"""Small, shared PostgreSQL gate for optional presentation generation.

No connection or transaction remains open while the provider is working. Quotas,
leases, and per-owner text-only caches are shared by all Gunicorn workers.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import uuid

from .presentation_ai import PresentationAIError, generate_content, get_ai_capabilities

AI_JOBS_SCHEMA = """
CREATE TABLE IF NOT EXISTS presentation_ai_jobs (
    id UUID PRIMARY KEY,
    owner_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    request_hash CHAR(64) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running','complete','failed')),
    result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    lease_until TIMESTAMPTZ NOT NULL DEFAULT now() + interval '6 minutes',
    finished_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS presentation_ai_jobs_owner_created
    ON presentation_ai_jobs(owner_id,created_at DESC);
CREATE INDEX IF NOT EXISTS presentation_ai_jobs_cache
    ON presentation_ai_jobs(owner_id,request_hash,created_at DESC) WHERE status='complete';
CREATE INDEX IF NOT EXISTS presentation_ai_jobs_running
    ON presentation_ai_jobs(lease_until) WHERE status='running';
CREATE INDEX IF NOT EXISTS presentation_ai_jobs_created
    ON presentation_ai_jobs(created_at);
"""

TEXT_FIELDS = (
    'title', 'section', 'body', 'body2', 'body3', 'formula', 'example',
    'image_prompt', 'image2_prompt', 'image_caption', 'image2_caption',
)


def _limit(name, default, maximum):
    try:
        value = int(os.getenv(name, str(default)))
    except (ValueError, TypeError):
        return default
    return max(1, min(maximum, value))


def cache_key(document, brief, slide_ids, model):
    """Only content sent to the text provider affects its reusable response.

    The owner scopes every cache SQL query separately; media stays in the
    incoming document and is never copied into the generated-text cache.
    """
    source = {
        'revision': 51, 'model': model, 'brief': brief, 'slide_ids': slide_ids,
        'title': document['title'], 'subject': document['subject'],
        'lesson_type': document['lesson_type'], 'audience': document.get('audience', ''),
        'design': {k: v for k, v in document.get('design', {}).items() if k != 'image'},
        'slides': [dict(id=s['id'], layout=s['layout'],
                       placements=s.get('placements', {}),
                       design={k: v for k, v in (s.get('design') or {}).items() if k != 'image'},
                       has_image=bool(s.get('image')), has_image2=bool(s.get('image2')),
                       **{k: s.get(k, '') for k in TEXT_FIELDS})
                   for s in document['slides']],
    }
    data = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def text_result(result, slide_ids):
    selected = set(slide_ids)
    return {
        'slides': [{'id': s['id'], **{k: s.get(k, '') for k in TEXT_FIELDS}}
                   for s in result['document']['slides'] if s['id'] in selected],
        'warnings': result.get('warnings', []),
    }


def restore_result(document, cached):
    if isinstance(cached, str):
        cached = json.loads(cached)
    out = copy.deepcopy(document)
    patches = {s['id']: s for s in cached['slides']}
    for slide in out['slides']:
        patch = patches.get(slide['id'])
        if patch is not None:
            slide.update({key: patch[key] for key in TEXT_FIELDS if key in patch})
    return {'document': out, 'generated_count': len(patches),
            'warnings': cached.get('warnings', []), 'cached': True}


class PresentationAIJobs:
    def __init__(self, db, require):
        self.db = db
        self.require = require

    @staticmethod
    def _busy(message, status=429):
        raise PresentationAIError(message, status_code=status, code='quota')

    def _reserve(self, uid, key):
        with self.db() as cur:
            self.require(cur, uid)
            # A short, transaction-scoped lock serializes reservations only.
            cur.execute('SELECT pg_advisory_xact_lock(49091302)')
            cur.execute("DELETE FROM presentation_ai_jobs WHERE created_at < now() - interval '7 days'")
            cur.execute("""UPDATE presentation_ai_jobs SET status='failed',finished_at=now()
                WHERE status='running' AND lease_until<=now()""")
            cur.execute("""SELECT result FROM presentation_ai_jobs WHERE owner_id=%s AND request_hash=%s
                AND status='complete' AND created_at>now()-interval '24 hours'
                ORDER BY created_at DESC LIMIT 1""", (uid, key))
            cached = cur.fetchone()
            if cached and cached['result'] is not None:
                return None, cached['result']
            cur.execute("""SELECT COUNT(*) AS total,
                COUNT(*) FILTER (WHERE owner_id=%s) AS own
                FROM presentation_ai_jobs WHERE status='running' AND lease_until>now()""", (uid,))
            running = cur.fetchone()
            if running['own']:
                self._busy('Oldingi taqdimotingiz hali tayyorlanmoqda. Tugashini kuting.')
            if running['total'] >= 2:
                self._busy('AI hozir boshqa taqdimotlarni tayyorlamoqda. Birozdan keyin qayta urinib ko‘ring.', 503)
            cur.execute("""SELECT COUNT(*) AS total,
                COUNT(*) FILTER (WHERE owner_id=%s) AS own
                FROM presentation_ai_jobs
                WHERE created_at >= (date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC')""", (uid,))
            counts = cur.fetchone()
            if counts['own'] >= _limit('PRESENTATION_AI_USER_DAILY', 5, 100):
                self._busy('Bugungi AI yaratish chegarangizga yetdingiz. Qo‘lda tahrirlashdan foydalanishingiz mumkin.')
            if counts['total'] >= _limit('PRESENTATION_AI_GLOBAL_DAILY', 20, 1000):
                self._busy('Bugungi umumiy AI yaratish chegarasiga yetildi. Qo‘lda tahrirlash ochiq.')
            # Prevent several short jobs in one minute from flooding the free API.
            cur.execute("SELECT COUNT(*) AS total FROM presentation_ai_jobs WHERE created_at>now()-interval '1 minute'")
            if cur.fetchone()['total'] >= 2:
                self._busy('AI navbati band. Bir daqiqadan keyin qayta urinib ko‘ring.')
            job_id = str(uuid.uuid4())
            cur.execute("""INSERT INTO presentation_ai_jobs(id,owner_id,request_hash,status)
                VALUES(%s,%s,%s,'running')""", (job_id, uid, key))
            return job_id, None

    def generate(self, uid, document, brief, slide_ids):
        capabilities = get_ai_capabilities()
        if not capabilities.get('available', capabilities['enabled']):
            self._busy(capabilities.get('reason') or 'AI hali ulanmagan. Qo‘lda tahrirlashingiz mumkin.', 503)
        key = cache_key(document, brief, slide_ids, capabilities['model'])
        job_id, cached = self._reserve(uid, key)
        if cached is not None:
            return restore_result(document, cached)
        try:
            result = generate_content(document, brief, slide_ids)
            # Validate before putting a response into the shared cache.
            from .presentations import validate_document
            result['document'] = validate_document(result['document'])
            stored = json.dumps(text_result(result, slide_ids), ensure_ascii=False, allow_nan=False)
            with self.db() as cur:
                cur.execute("""UPDATE presentation_ai_jobs SET status='complete',result=%s::jsonb,finished_at=now()
                    WHERE id=%s AND owner_id=%s AND status='running' AND lease_until>now()""", (stored, job_id, uid))
            return dict(result, cached=False)
        except Exception:
            # Retain the failed attempt for quota accounting, never its prompt,
            # provider payload, API key, or exception text.
            try:
                with self.db() as cur:
                    cur.execute("""UPDATE presentation_ai_jobs SET status='failed',finished_at=now()
                        WHERE id=%s AND owner_id=%s AND status='running'""", (job_id, uid))
            except Exception:
                pass  # The lease releases the slot if the database is offline.
            raise

"""REV47 self-paced courses, isolated from private institutional lessons.

Course authors own every lesson and answer key here. Student responses never
contain answer keys before an exercise submission or final quiz result. All
paid access is checked on the server. The manual payment ledger extends the
dedicated enrollment table only after the course owner confirms receipt;
there is no automatic bank verification or external paid service here.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import secrets
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from threading import Lock

from fastapi import Body, Header, HTTPException, Query


MAX_LESSONS = 500
MAX_CONTENT_BYTES = 262144
MAX_REQUEST_BYTES = 300000
SAFE_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
COURSE_FIELDS = {"title", "subject", "level", "description", "price_uzs"}
DIFFICULTIES = {"easy", "medium", "hard"}


def fail(message, status=422):
    raise HTTPException(status, message)


def integer(value, label, low=1, high=9223372036854775807):
    if type(value) is not int or not low <= value <= high:
        fail(f"{label}: {low}–{high} oralig‘ida butun son kiriting")
    return value


def text(value, label, maximum, required=False):
    if not isinstance(value, str):
        fail(f"{label}: matn kiriting")
    value = value.strip()
    if (required and not value) or len(value) > maximum or "\x00" in value:
        fail(f"{label}: {'1–' if required else '0–'}{maximum} belgi kiriting")
    return value


def boolean(value, label):
    if type(value) is not bool:
        fail(f"{label}: ha yoki yo‘q qiymatini tanlang")
    return value


def choice(value, label, options):
    if not isinstance(value, str) or value not in options:
        fail(f"{label} noto‘g‘ri")
    return value


def key(value, label="Identifikator"):
    if not isinstance(value, str) or not SAFE_KEY.fullmatch(value):
        fail(f"{label} noto‘g‘ri")
    return value


def payload(value, allowed, required=()):
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        fail("So‘rov maydonlari noto‘g‘ri yoki to‘liq emas")
    try:
        size = len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    except (TypeError, ValueError, RecursionError):
        fail("So‘rov JSON ma’lumoti noto‘g‘ri")
    if size > MAX_REQUEST_BYTES:
        fail("Bitta darsdagi matn juda katta. Uni bir nechta darsga ajrating", 413)
    return value


def list_field(value, label, maximum):
    if not isinstance(value, list) or len(value) > maximum:
        fail(f"{label}: ko‘pi bilan {maximum} ta bo‘lishi mumkin")
    return value


def ids(value, label, maximum=100):
    values = [integer(v, label) for v in list_field(value, label, maximum)]
    if len(set(values)) != len(values):
        fail(f"{label}: takrorlangan raqam bor")
    return values


def timestamp(value):
    return value.isoformat() if isinstance(value, datetime) else value


def utcnow():
    return datetime.now(timezone.utc)


def as_json(value):
    return json.loads(value) if isinstance(value, str) else value


def course_values(body):
    return {
        "title": text(body.get("title", ""), "Kurs nomi", 180, True),
        "subject": text(body.get("subject", ""), "Fan", 100, True),
        "level": text(body.get("level", ""), "Sinf yoki daraja", 100, True),
        "description": text(body.get("description", ""), "Kurs tavsifi", 6000),
        "price_uzs": integer(body.get("price_uzs", 0), "30 kunlik narx", 0, 100000000),
    }


def empty_content():
    return {"theory": "", "examples": [], "exercises": [], "questions": [],
            "video_id": None, "attachments": []}


def validate_content(raw):
    payload(raw, empty_content())
    out = empty_content()
    out["theory"] = text(raw.get("theory", ""), "Nazariya", 100000)
    for value in list_field(raw.get("examples", []), "Yechilgan misollar", 100):
        payload(value, {"prompt", "solution"}, {"prompt", "solution"})
        out["examples"].append({"prompt": text(value["prompt"], "Misol sharti", 6000, True),
                                "solution": text(value["solution"], "Misol yechimi", 12000, True)})
    used = set()
    for kind in ("exercises", "questions"):
        for value in list_field(raw.get(kind, []), kind, 100):
            fields = {"id", "prompt", "answer", "explanation"} if kind == "exercises" else {
                "id", "prompt", "options", "correct_index", "explanation", "difficulty"}
            payload(value, fields, {"prompt", "answer"} if kind == "exercises" else {
                "prompt", "options", "correct_index"})
            item_id = key(value.get("id") or uuid.uuid4().hex)
            if item_id in used:
                fail("Darsdagi mashq yoki test identifikatorlari takrorlangan")
            used.add(item_id)
            item = {"id": item_id, "prompt": text(value["prompt"], "Savol", 6000, True),
                    "explanation": text(value.get("explanation", ""), "Izoh", 10000)}
            if kind == "exercises":
                item["answer"] = text(value["answer"], "To‘g‘ri javob", 2000, True)
            else:
                options = list_field(value["options"], "Javob variantlari", 4)
                if len(options) != 4:
                    fail("Har bir testda 4 ta javob varianti bo‘lishi kerak")
                item["options"] = [text(v, "Javob varianti", 2000, True) for v in options]
                if len({normalise_answer(v) for v in item["options"]}) != 4:
                    fail("Test javob variantlari bir-biridan farq qilishi kerak")
                item["correct_index"] = integer(value["correct_index"], "To‘g‘ri javob raqami", 0, 3)
                item["difficulty"] = choice(value.get("difficulty", "medium"), "Test qiyinligi", DIFFICULTIES)
            out[kind].append(item)
    video = raw.get("video_id")
    out["video_id"] = None if video in (None, "") else key(video, "Video raqami")
    out["attachments"] = [key(v, "Fayl raqami") for v in list_field(raw.get("attachments", []), "Fayllar", 20)]
    if len(out["attachments"]) != len(set(out["attachments"])):
        fail("Bir fayl ikki marta biriktirilgan")
    if len(json.dumps(out, ensure_ascii=False).encode("utf-8")) > MAX_CONTENT_BYTES:
        fail("Dars matni juda katta. Uni kichikroq darslarga ajrating", 413)
    return out


def has_material(content):
    return any(content.get(k) for k in empty_content())


def normalise_answer(value):
    """Conservative text matching, NOT symbolic mathematical equivalence."""
    value = unicodedata.normalize("NFKC", str(value)).casefold()
    value = value.translate(str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "−": "-"}))
    return " ".join(value.split())


def numeric_answer(value):
    """Only bounded decimal/fraction literals; never evaluate user expressions."""
    value = normalise_answer(value).replace(" ", "")
    if len(value) > 70:
        return None
    number = r"[+-]?(?:\d{1,15}(?:[.,]\d{1,15})?|[.,]\d{1,15})"
    if not re.fullmatch(number + r"(?:/" + number + r")?", value, re.ASCII):
        return None
    try:
        parts = value.replace(",", ".").split("/")
        result = Fraction(Decimal(parts[0]))
        if len(parts) == 2:
            denominator = Fraction(Decimal(parts[1]))
            if denominator == 0:
                return None
            result /= denominator
        return result
    except (ValueError, InvalidOperation, ZeroDivisionError, OverflowError):
        return None


def check_answer(submitted, expected):
    left, right = numeric_answer(submitted), numeric_answer(expected)
    if left is not None and right is not None:
        return left == right, "numeric_equivalent"
    return normalise_answer(submitted) == normalise_answer(expected), "exact_text"


def student_content(raw):
    content = as_json(raw) or empty_content()
    return {
        "theory": content.get("theory", ""), "examples": content.get("examples", []),
        "exercises": [{"id": q["id"], "prompt": q["prompt"]} for q in content.get("exercises", [])],
        "question_count": len(content.get("questions", [])), "questions": [],
        "video_id": content.get("video_id"), "attachments": content.get("attachments", []),
    }


def publishing_rules(course, lessons):
    published = [l for l in lessons if l["status"] == "published"]
    if not published:
        fail("Kursda kamida bitta nashr qilingan dars bo‘lishi kerak")
    if course["price_uzs"] > 0:
        count = sum(bool(l["is_preview"]) for l in published)
        if not 2 <= count <= 3:
            fail("Pulli kursda 2 yoki 3 ta bepul sinov darsini belgilang")
        if len(published) <= count:
            fail("Pulli kursda kamida bitta obuna orqali ochiladigan dars bo‘lishi kerak")


def lesson_summary(row, access):
    content = as_json(row.get("content")) or {}
    return {k: row[k] for k in ("id", "title", "position", "is_preview", "status", "version")} | {
        "locked": not (access["owner"] or access["active"] or row["is_preview"]),
        "has_video": bool(row.get("has_video", content.get("video_id"))),
        "exercise_count": int(row.get("exercise_count", len(content.get("exercises", [])))),
        "question_count": int(row.get("question_count", len(content.get("questions", [])))),
    }


def progress_public(row):
    if not row:
        return None
    return {k: timestamp(row.get(k)) for k in (
        "course_id", "lesson_id", "position_seconds", "duration_seconds", "status", "updated_at")}


def quiz_answers(raw, snapshot):
    if not isinstance(raw, dict) or len(raw) > 100:
        fail("Test javoblari noto‘g‘ri")
    valid = {q["id"] for q in snapshot}
    if set(raw) - valid:
        fail("Javoblarda ushbu testga tegishli bo‘lmagan savol bor")
    return {qid: integer(value, "Javob varianti", 0, 3) for qid, value in raw.items()}


def score_quiz(snapshot, answers):
    correct = sum(answers.get(q["id"]) == q["correct_index"] for q in snapshot)
    return {"correct": correct, "total": len(snapshot),
            "percent": round(100 * correct / len(snapshot), 2) if snapshot else 0,
            "items": [{"id": q["id"], "lesson_id": q["lesson_id"], "prompt": q["prompt"],
                       "options": q["options"], "selected": answers.get(q["id"]),
                       "correct_index": q["correct_index"], "explanation": q.get("explanation", "")}
                      for q in snapshot]}


SCHEMA = """
CREATE TABLE IF NOT EXISTS academy_courses (
 id BIGSERIAL PRIMARY KEY, teacher_id BIGINT NOT NULL REFERENCES users(user_id),
 title TEXT NOT NULL, subject TEXT NOT NULL, level TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 price_uzs BIGINT NOT NULL DEFAULT 0 CHECK(price_uzs>=0),
 status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','published','archived')),
 version INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS academy_courses_catalog_idx ON academy_courses(status,id);
CREATE INDEX IF NOT EXISTS academy_courses_teacher_idx ON academy_courses(teacher_id,id);
CREATE TABLE IF NOT EXISTS academy_lessons (
 id BIGSERIAL PRIMARY KEY, course_id BIGINT NOT NULL REFERENCES academy_courses(id),
 title TEXT NOT NULL, position INTEGER NOT NULL CHECK(position>=0),
 is_preview BOOLEAN NOT NULL DEFAULT FALSE,
 status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','published')),
 content JSONB NOT NULL DEFAULT '{}', version INTEGER NOT NULL DEFAULT 1,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 UNIQUE(course_id,id)
);
CREATE INDEX IF NOT EXISTS academy_lessons_order_idx ON academy_lessons(course_id,position,id);
CREATE TABLE IF NOT EXISTS academy_enrollments (
 course_id BIGINT NOT NULL REFERENCES academy_courses(id), user_id BIGINT NOT NULL REFERENCES users(user_id),
 access_until TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), PRIMARY KEY(course_id,user_id)
);
CREATE INDEX IF NOT EXISTS academy_enrollments_user_idx ON academy_enrollments(user_id,course_id);
CREATE TABLE IF NOT EXISTS academy_progress (
 course_id BIGINT NOT NULL, lesson_id BIGINT NOT NULL, user_id BIGINT NOT NULL REFERENCES users(user_id),
 position_seconds DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK(position_seconds>=0),
 duration_seconds DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK(duration_seconds>=0),
 status TEXT NOT NULL DEFAULT 'studying' CHECK(status IN ('studying','completed')),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now(), PRIMARY KEY(course_id,lesson_id,user_id),
 FOREIGN KEY(course_id,lesson_id) REFERENCES academy_lessons(course_id,id)
);
CREATE INDEX IF NOT EXISTS academy_progress_user_idx ON academy_progress(user_id,course_id);
CREATE TABLE IF NOT EXISTS academy_exercise_results (
 lesson_id BIGINT NOT NULL REFERENCES academy_lessons(id), user_id BIGINT NOT NULL REFERENCES users(user_id),
 exercise_id TEXT NOT NULL, correct BOOLEAN NOT NULL, answer TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 1,
 lesson_version INTEGER NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(lesson_id,user_id,exercise_id)
);
CREATE TABLE IF NOT EXISTS academy_attempts (
 id TEXT PRIMARY KEY, course_id BIGINT NOT NULL REFERENCES academy_courses(id),
 user_id BIGINT NOT NULL REFERENCES users(user_id), request_key TEXT NOT NULL, fingerprint TEXT NOT NULL,
 snapshot JSONB NOT NULL, answers JSONB NOT NULL DEFAULT '{}', result JSONB,
 status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed')),
 available_count INTEGER NOT NULL, expires_at TIMESTAMPTZ NOT NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), completed_at TIMESTAMPTZ,
 UNIQUE(user_id,request_key)
);
CREATE INDEX IF NOT EXISTS academy_attempts_user_idx ON academy_attempts(user_id,created_at);
"""


class AcademyService:
    def __init__(self, platform):
        self.platform = platform
        self._ready = False
        self._lock = Lock()
        self.video_configured = lambda: False
        self.payments_configured = lambda: False

    @contextmanager
    def db(self):
        conn = self.platform._db()
        cur = None
        try:
            cur = conn.cursor()
            cur.execute("SET LOCAL statement_timeout = '8000ms'")
            cur.execute("SET LOCAL lock_timeout = '3000ms'")
            yield cur
            conn.commit()
        except Exception as exc:
            conn.rollback()
            if getattr(exc, "pgcode", None) in {"57014", "55P03", "40P01", "40001"}:
                raise HTTPException(503, "Kurs xizmati hozir band. Birozdan keyin qayta urinib ko‘ring") from None
            raise
        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def migrate(self):
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            with self.db() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(47091201)")
                cur.execute(SCHEMA)
            self._ready = True

    def actor(self, authorization, optional=False):
        if not authorization:
            if optional:
                return None
            fail("Davom etish uchun shaxsiy hisobingizga kiring", 401)
        if not isinstance(authorization, str) or len(authorization) > 8192:
            fail("Kirish ma’lumoti noto‘g‘ri", 401)
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token or " " in token:
            fail("Kirish ma’lumoti noto‘g‘ri", 401)
        uid = self.platform._jwt_tekshir(token)
        auth = getattr(self.platform, "_kabutar_auth_service", None)
        if auth is None:
            fail("Kirish xizmati hali tayyor emas", 503)
        if auth.claims(token).get("admin_korish"):
            fail("Ko‘rish rejimida shaxsiy kurs hisobidan foydalanib bo‘lmaydi", 403)
        uid = integer(uid, "Hisob raqami", -9223372036854775808)
        if uid == 0:
            fail("Hisob raqami noto‘g‘ri", 401)
        return uid

    def can_teach(self, cur, uid):
        if uid is None:
            return False
        cur.execute("""SELECT role, EXISTS(SELECT 1 FROM admin_akkaunt WHERE uid=%s) AS admin
                       FROM users WHERE user_id=%s""", (uid, uid))
        row = cur.fetchone()
        if not row:
            fail("Hisob topilmadi", 401)
        return bool(row["admin"] or row["role"] == "oqituvchi")

    def course(self, cur, course_id):
        course_id = integer(course_id, "Kurs raqami")
        cur.execute("SELECT * FROM academy_courses WHERE id=%s", (course_id,))
        row = cur.fetchone()
        if not row:
            fail("Kurs topilmadi", 404)
        return dict(row)

    def owner(self, cur, course_id, uid):
        course_id = integer(course_id, "Kurs raqami")
        cur.execute("SELECT * FROM academy_courses WHERE id=%s FOR UPDATE", (course_id,))
        row = cur.fetchone()
        if not row:
            fail("Kurs topilmadi", 404)
        if uid is None or int(row["teacher_id"]) != uid or not self.can_teach(cur, uid):
            fail("Bu kursni faqat uni yaratgan o‘qituvchi boshqaradi", 403)
        return dict(row)

    def access(self, cur, course, uid):
        owner = uid is not None and int(course["teacher_id"]) == uid and self.can_teach(cur, uid)
        out = {"active": bool(owner), "access_until": None, "owner": bool(owner)}
        if owner or uid is None or course["status"] != "published":
            return out
        cur.execute("""SELECT access_until,(access_until>now()) AS unexpired
                       FROM academy_enrollments WHERE course_id=%s AND user_id=%s""", (course["id"], uid))
        row = cur.fetchone()
        if row:
            out["access_until"] = timestamp(row["access_until"])
            out["active"] = bool(course["price_uzs"] == 0 or row["unexpired"])
        return out

    def lesson_access(self, cur, lesson_id, uid, for_write=False):
        lesson_id = integer(lesson_id, "Dars raqami")
        cur.execute("SELECT * FROM academy_lessons WHERE id=%s", (lesson_id,))
        lesson = cur.fetchone()
        if not lesson:
            fail("Dars topilmadi", 404)
        course = self.owner(cur, lesson["course_id"], uid) if for_write else self.course(cur, lesson["course_id"])
        access = self.access(cur, course, uid)
        if not access["owner"]:
            if course["status"] != "published" or lesson["status"] != "published":
                fail("Dars hozir ochiq emas", 404)
            if not (lesson["is_preview"] or access["active"]):
                fail("Bu dars uchun kurs obunasini faollashtiring", 402)
        return dict(lesson), course

    def _course_public(self, cur, course):
        return self._courses_public(cur, [course])[0]

    @staticmethod
    def _courses_public(cur, courses):
        if not courses:
            return []
        cur.execute("""SELECT c.id,u.full_name AS teacher_name,
          COUNT(l.id) FILTER(WHERE l.status='published') AS lesson_count,
          COUNT(l.id) FILTER(WHERE l.status='published' AND l.is_preview) AS preview_count
          FROM academy_courses c JOIN users u ON u.user_id=c.teacher_id
          LEFT JOIN academy_lessons l ON l.course_id=c.id WHERE c.id=ANY(%s)
          GROUP BY c.id,u.full_name""", ([r["id"] for r in courses],))
        infos = {r["id"]: r for r in cur.fetchall()}
        outputs = []
        for course in courses:
            info = infos.get(course["id"], {})
            outputs.append({k: course[k] for k in ("id", "title", "subject", "level", "description", "price_uzs", "status", "version")} | {
                "teacher_name": info.get("teacher_name") or "O‘qituvchi",
                "lesson_count": int(info.get("lesson_count") or 0), "preview_count": int(info.get("preview_count") or 0),
            })
        return outputs

    @staticmethod
    def _version(row, version):
        if integer(version, "Versiya", 1, 2147483647) != row["version"]:
            fail("Bu ma’lumot boshqa oynada yangilangan. Qayta ochib, o‘zgarishingizni saqlang", 409)

    @staticmethod
    def _bump(cur, course_id):
        cur.execute("UPDATE academy_courses SET version=version+1,updated_at=now() WHERE id=%s", (course_id,))

    def _assets(self, cur, course, content):
        asset_ids = content["attachments"] + ([content["video_id"]] if content["video_id"] else [])
        if not asset_ids:
            return
        cur.execute("SELECT id,course_id,owner_id,kind,status FROM academy_assets WHERE id=ANY(%s)", (asset_ids,))
        assets = {r["id"]: r for r in cur.fetchall()}
        for asset_id in asset_ids:
            asset = assets.get(asset_id)
            expected = "video" if asset_id == content["video_id"] else "file"
            if (not asset or asset["course_id"] != course["id"] or asset["owner_id"] != course["teacher_id"]
                    or asset["kind"] != expected or asset["status"] != "ready"):
                fail("Biriktirilgan fayl ushbu kursga tegishli emas yoki hali tayyor emas")

    def capabilities(self, uid):
        with self.db() as cur:
            allowed = self.can_teach(cur, uid)
        video = self.video_configured() if callable(self.video_configured) else self.video_configured
        payments = self.payments_configured() if callable(self.payments_configured) else self.payments_configured
        return {"can_teach": allowed, "video_configured": bool(video),
                "payments_configured": bool(payments), "payment_mode": "manual"}

    def catalog(self, q, subject, level, after_id, limit):
        q = text(q, "Qidiruv", 120)
        subject = text(subject, "Fan", 100)
        level = text(level, "Daraja", 100)
        after_id = integer(after_id, "Sahifa", 0)
        limit = integer(limit, "Sahifa hajmi", 1, 50)
        # Escape LIKE wildcard characters so user text is a literal search.
        pattern = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        with self.db() as cur:
            cur.execute("""SELECT c.* FROM academy_courses c JOIN users u ON u.user_id=c.teacher_id
                WHERE c.status='published' AND c.id>%s
                AND (%s='' OR c.title ILIKE %s OR c.subject ILIKE %s OR u.full_name ILIKE %s)
                AND (%s='' OR c.subject=%s) AND (%s='' OR c.level=%s)
                ORDER BY c.id LIMIT %s""", (after_id, q, pattern, pattern, pattern, subject, subject, level, level, limit+1))
            rows = cur.fetchall()
            return {"items": self._courses_public(cur, rows[:limit]),
                    "next_cursor": rows[limit-1]["id"] if len(rows) > limit else None}

    def mine(self, uid):
        with self.db() as cur:
            can_teach = self.can_teach(cur, uid)
            if can_teach:
                cur.execute("SELECT * FROM academy_courses WHERE teacher_id=%s ORDER BY id DESC LIMIT 100", (uid,))
                teaching = self._courses_public(cur, cur.fetchall())
            else:
                teaching = []
            cur.execute("""SELECT c.*,e.access_until,(e.access_until>now()) AS unexpired,
                (e.user_id IS NOT NULL) AS enrolled FROM academy_courses c
                LEFT JOIN academy_enrollments e ON e.course_id=c.id AND e.user_id=%s WHERE c.id IN
                (SELECT course_id FROM academy_enrollments WHERE user_id=%s
                 UNION SELECT course_id FROM academy_progress WHERE user_id=%s)
                AND c.status='published' ORDER BY c.id DESC LIMIT 100""", (uid, uid, uid))
            rows = cur.fetchall()
            learning = []
            for row, item in zip(rows, self._courses_public(cur, rows)):
                owner = bool(can_teach and row["teacher_id"] == uid)
                item["access"] = {"owner": owner, "access_until": timestamp(row["access_until"]),
                                  "active": bool(owner or row["enrolled"] and (row["price_uzs"] == 0 or row["unexpired"]))}
                learning.append(item)
            return {"teaching": teaching, "learning": learning}

    def detail(self, course_id, uid):
        with self.db() as cur:
            course = self.course(cur, course_id)
            access = self.access(cur, course, uid)
            if course["status"] != "published" and not access["owner"]:
                fail("Kurs hozir ochiq emas", 404)
            # Summary reads never load all lesson bodies/answer keys into RAM.
            cur.execute("""SELECT id,title,position,is_preview,status,version,
                           (NULLIF(content->>'video_id','') IS NOT NULL) AS has_video,
                           jsonb_array_length(COALESCE(content->'exercises','[]'::jsonb)) AS exercise_count,
                           jsonb_array_length(COALESCE(content->'questions','[]'::jsonb)) AS question_count
                           FROM academy_lessons WHERE course_id=%s
                           AND (%s OR status='published') ORDER BY position,id LIMIT 500""", (course_id, access["owner"]))
            lessons = [lesson_summary(row, access) for row in cur.fetchall()]
            progress = []
            if uid is not None:
                cur.execute("""SELECT p.* FROM academy_progress p JOIN academy_lessons l ON l.id=p.lesson_id
                    WHERE p.course_id=%s AND p.user_id=%s AND (%s OR l.status='published') LIMIT 500""", (course_id, uid, access["owner"]))
                progress = [progress_public(r) for r in cur.fetchall()]
            return {"course": self._course_public(cur, course), "lessons": lessons, "access": access, "progress": progress}

    def create(self, uid, body):
        payload(body, COURSE_FIELDS)
        values = course_values(body)
        with self.db() as cur:
            if not self.can_teach(cur, uid):
                fail("Kurs yaratish o‘qituvchi hisobida ochiladi", 403)
            # Serialize creation limits per author, including concurrent tabs.
            cur.execute("SELECT pg_advisory_xact_lock(47,%s)", (uid % 2147483647,))
            cur.execute("SELECT count(*) AS total FROM academy_courses WHERE teacher_id=%s", (uid,))
            if cur.fetchone()["total"] >= 100:
                fail("Bitta o‘qituvchi hisobida 100 tagacha kurs yaratiladi", 409)
            cur.execute("""INSERT INTO academy_courses(teacher_id,title,subject,level,description,price_uzs)
                VALUES(%s,%s,%s,%s,%s,%s) RETURNING *""", (uid, *values.values()))
            return {"course": self._course_public(cur, cur.fetchone())}

    def update(self, course_id, uid, body):
        payload(body, COURSE_FIELDS | {"version"}, {"version"})
        values = course_values(body)
        with self.db() as cur:
            course = self.owner(cur, course_id, uid)
            self._version(course, body["version"])
            if course["status"] == "published":
                cur.execute("SELECT status,is_preview FROM academy_lessons WHERE course_id=%s", (course_id,))
                publishing_rules(course | values, cur.fetchall())
            cur.execute("""UPDATE academy_courses SET title=%s,subject=%s,level=%s,description=%s,price_uzs=%s,
                 version=version+1,updated_at=now() WHERE id=%s RETURNING *""", (*values.values(), course_id))
            return {"course": self._course_public(cur, cur.fetchone())}

    def transition(self, course_id, uid, body, status):
        payload(body, {"version"}, {"version"})
        with self.db() as cur:
            course = self.owner(cur, course_id, uid)
            self._version(course, body["version"])
            if status == "published":
                cur.execute("SELECT * FROM academy_lessons WHERE course_id=%s ORDER BY position,id", (course_id,))
                lessons = cur.fetchall()
                publishing_rules(course, lessons)
                for lesson in lessons:
                    if lesson["status"] == "published":
                        content = as_json(lesson["content"])
                        if not has_material(content):
                            fail("Bo‘sh darsni nashr qilib bo‘lmaydi")
                        self._assets(cur, course, content)
            cur.execute("UPDATE academy_courses SET status=%s,version=version+1,updated_at=now() WHERE id=%s RETURNING *", (status, course_id))
            return {"course": self._course_public(cur, cur.fetchone())}

    def join(self, course_id, uid, body):
        payload(body, set())
        with self.db() as cur:
            cur.execute("SELECT * FROM academy_courses WHERE id=%s FOR SHARE", (integer(course_id, "Kurs raqami"),))
            course = cur.fetchone()
            if not course or course["status"] != "published":
                fail("Kurs hozir ochiq emas", 404)
            if course["price_uzs"] != 0:
                fail("Pulli kursga kirish uchun obunani to‘lang", 402)
            cur.execute("""INSERT INTO academy_enrollments(course_id,user_id) VALUES(%s,%s)
                ON CONFLICT(course_id,user_id) DO NOTHING""", (course_id, uid))
            return {"access": self.access(cur, course, uid)}

    def add_lessons(self, course_id, uid, body):
        payload(body, {"titles"}, {"titles"})
        titles = [text(t, "Dars nomi", 200, True) for t in list_field(body["titles"], "Darslar", 100)]
        if not titles:
            fail("Kamida bitta mavzu nomini kiriting")
        with self.db() as cur:
            course = self.owner(cur, course_id, uid)
            cur.execute("SELECT count(*) AS total,COALESCE(max(position),0) AS last FROM academy_lessons WHERE course_id=%s", (course_id,))
            counts = cur.fetchone()
            if counts["total"] + len(titles) > MAX_LESSONS:
                fail("Kursda ko‘pi bilan 500 ta dars bo‘lishi mumkin")
            rows = []
            for offset, title in enumerate(titles, 1):
                cur.execute("""INSERT INTO academy_lessons(course_id,title,position,content)
                    VALUES(%s,%s,%s,%s::jsonb) RETURNING *""", (course_id, title, counts["last"]+offset, json.dumps(empty_content())))
                rows.append(lesson_summary(cur.fetchone(), {"owner": True, "active": True}))
            self._bump(cur, course_id)
            return {"lessons": rows, "course": self._course_public(cur, course | {"version": course["version"]+1})}

    def reorder(self, course_id, uid, body):
        payload(body, {"lesson_ids", "version"}, {"lesson_ids", "version"})
        order = ids(body["lesson_ids"], "Darslar", MAX_LESSONS)
        with self.db() as cur:
            course = self.owner(cur, course_id, uid)
            self._version(course, body["version"])
            cur.execute("SELECT id FROM academy_lessons WHERE course_id=%s", (course_id,))
            if set(order) != {r["id"] for r in cur.fetchall()}:
                fail("Darslar ro‘yxati yangilangan. Qayta ochib tartiblang", 409)
            for position, lesson_id in enumerate(order, 1):
                cur.execute("UPDATE academy_lessons SET position=%s,version=version+1,updated_at=now() WHERE id=%s", (position, lesson_id))
            self._bump(cur, course_id)
            return {"course": self._course_public(cur, course | {"version": course["version"]+1})}

    def read_lesson(self, lesson_id, uid):
        with self.db() as cur:
            lesson, course = self.lesson_access(cur, lesson_id, uid)
            access = self.access(cur, course, uid)
            output = {k: lesson[k] for k in ("id", "course_id", "title", "position", "is_preview", "status", "version")}
            output["content"] = as_json(lesson["content"]) if access["owner"] else student_content(lesson["content"])
            progress = None
            if uid is not None:
                cur.execute("SELECT * FROM academy_progress WHERE lesson_id=%s AND user_id=%s", (lesson_id, uid))
                progress = progress_public(cur.fetchone())
            return {"lesson": output, "access": access, "progress": progress}

    def save_lesson(self, lesson_id, uid, body):
        payload(body, {"title", "is_preview", "status", "content", "version"}, {"title", "is_preview", "status", "content", "version"})
        title = text(body["title"], "Dars nomi", 200, True)
        preview = boolean(body["is_preview"], "Bepul dars")
        status = choice(body["status"], "Dars holati", {"draft", "published"})
        content = validate_content(body["content"])
        if status == "published" and not has_material(content):
            fail("Darsga nazariya, video, misol, mashq yoki test qo‘shing")
        with self.db() as cur:
            # Find parent first, then lock course before lesson, consistently.
            cur.execute("SELECT course_id FROM academy_lessons WHERE id=%s", (integer(lesson_id, "Dars raqami"),))
            parent = cur.fetchone()
            if not parent:
                fail("Dars topilmadi", 404)
            course = self.owner(cur, parent["course_id"], uid)
            cur.execute("SELECT * FROM academy_lessons WHERE id=%s FOR UPDATE", (lesson_id,))
            lesson = cur.fetchone()
            self._version(lesson, body["version"])
            self._assets(cur, course, content)
            if course["status"] == "published":
                cur.execute("SELECT id,status,is_preview FROM academy_lessons WHERE course_id=%s", (course["id"],))
                siblings = [dict(r) | ({"status": status, "is_preview": preview} if r["id"] == lesson_id else {}) for r in cur.fetchall()]
                publishing_rules(course, siblings)
            cur.execute("""UPDATE academy_lessons SET title=%s,is_preview=%s,status=%s,content=%s::jsonb,
                version=version+1,updated_at=now() WHERE id=%s RETURNING *""", (title, preview, status, json.dumps(content), lesson_id))
            updated = dict(cur.fetchone())
            self._bump(cur, course["id"])
            return {"lesson": {k: updated[k] for k in ("id", "course_id", "title", "position", "is_preview", "status", "version", "content")},
                    "course_version": course["version"]+1}

    def save_progress(self, lesson_id, uid, body):
        payload(body, {"position_seconds", "duration_seconds", "status"}, {"position_seconds", "duration_seconds", "status"})
        values = []
        for field in ("position_seconds", "duration_seconds"):
            v = body[field]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 86400:
                fail("Video vaqti noto‘g‘ri")
            values.append(float(v))
        position, duration = values
        if position > duration:
            fail("Ko‘rish vaqti video davomiyligidan oshmasligi kerak")
        choice(body["status"], "O‘qish holati", {"studying", "completed"})
        with self.db() as cur:
            lesson, course = self.lesson_access(cur, lesson_id, uid)
            cur.execute("""INSERT INTO academy_progress(course_id,lesson_id,user_id,position_seconds,duration_seconds,status)
                VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(course_id,lesson_id,user_id) DO UPDATE SET
                position_seconds=EXCLUDED.position_seconds,duration_seconds=EXCLUDED.duration_seconds,
                status=CASE WHEN academy_progress.status='completed' THEN 'completed' ELSE EXCLUDED.status END,
                updated_at=now() RETURNING *""", (course["id"], lesson_id, uid, position, duration, body["status"]))
            return {"progress": progress_public(cur.fetchone())}

    def exercise(self, lesson_id, exercise_id, uid, body):
        payload(body, {"answer"}, {"answer"})
        submitted = text(body["answer"], "Javob", 2000, True)
        exercise_id = key(exercise_id)
        with self.db() as cur:
            lesson, _ = self.lesson_access(cur, lesson_id, uid)
            match = next((e for e in as_json(lesson["content"]).get("exercises", []) if e["id"] == exercise_id), None)
            if match is None:
                fail("Mashq topilmadi", 404)
            correct, checking = check_answer(submitted, match["answer"])
            cur.execute("""INSERT INTO academy_exercise_results(lesson_id,user_id,exercise_id,correct,answer,lesson_version)
                VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT(lesson_id,user_id,exercise_id) DO UPDATE SET
                correct=EXCLUDED.correct,answer=EXCLUDED.answer,lesson_version=EXCLUDED.lesson_version,
                attempts=academy_exercise_results.attempts+1,updated_at=now()""", (lesson_id, uid, exercise_id, correct, submitted, lesson["version"]))
            return {"correct": correct, "explanation": match.get("explanation", ""), "expected_answer": match["answer"],
                    "checking": checking, "notice": "Qisqa javob ustoz kiritgan namuna bilan solishtirildi; yozma yechim avtomatik baholanmaydi."}

    def _attempt_access(self, cur, attempt, uid):
        if attempt["user_id"] != uid:
            fail("Test urinishi topilmadi", 404)
        course = self.course(cur, attempt["course_id"])
        access = self.access(cur, course, uid)
        if not access["owner"] and course["status"] != "published":
            fail("Kurs hozir ochiq emas", 404)
        required = {q["lesson_id"] for q in as_json(attempt["snapshot"])}
        cur.execute("SELECT id,status,is_preview FROM academy_lessons WHERE course_id=%s AND id=ANY(%s)", (course["id"], list(required)))
        rows = cur.fetchall()
        if len(rows) != len(required) or (not access["owner"] and any(r["status"] != "published" for r in rows)):
            fail("Testning ayrim darslari hozir ochiq emas", 404)
        if not access["owner"] and not access["active"] and any(not r["is_preview"] for r in rows):
            fail("Testni davom ettirish uchun obunani yangilang", 402)

    @staticmethod
    def _attempt_public(attempt):
        out = {"id": attempt["id"], "course_id": attempt["course_id"],
               "questions": [{k: q[k] for k in ("id", "lesson_id", "prompt", "options")}
                             for q in as_json(attempt["snapshot"])],
               "expires_at": timestamp(attempt["expires_at"]), "answers": as_json(attempt["answers"]),
               "status": attempt["status"]}
        if attempt["status"] == "completed":
            out["result"] = as_json(attempt["result"])
        return out

    @staticmethod
    def _finish(cur, attempt, incoming=None):
        if attempt["status"] == "completed":
            return attempt
        answers = dict(as_json(attempt["answers"]))
        if incoming is not None and utcnow() < attempt["expires_at"]:
            answers.update(incoming)
        result = score_quiz(as_json(attempt["snapshot"]), answers)
        cur.execute("""UPDATE academy_attempts SET answers=%s::jsonb,result=%s::jsonb,status='completed',completed_at=now()
            WHERE id=%s RETURNING *""", (json.dumps(answers), json.dumps(result), attempt["id"]))
        return dict(cur.fetchone())

    def _fetch_attempt(self, cur, attempt_id, uid):
        attempt_id = key(attempt_id, "Test urinishi")
        cur.execute("SELECT * FROM academy_attempts WHERE id=%s AND user_id=%s FOR UPDATE", (attempt_id, uid))
        attempt = cur.fetchone()
        if not attempt:
            fail("Test urinishi topilmadi", 404)
        self._attempt_access(cur, attempt, uid)
        return dict(attempt)

    def start_attempt(self, course_id, uid, body):
        payload(body, {"lesson_ids", "scope", "count", "difficulty", "minutes", "request_key"},
                {"lesson_ids", "scope", "count", "difficulty", "minutes", "request_key"})
        lesson_ids = ids(body["lesson_ids"], "Mavzular", 100)
        scope = choice(body["scope"], "Test mavzulari", {"selected", "completed"})
        if scope == "selected" and not lesson_ids:
            fail("Test uchun mavzularni tanlang")
        count = integer(body["count"], "Savollar soni", 1, 100)
        minutes = integer(body["minutes"], "Test vaqti", 1, 180)
        difficulty = choice(body["difficulty"], "Test qiyinligi", DIFFICULTIES | {"mixed"})
        request_key = key(body["request_key"], "So‘rov raqami")
        fingerprint = hashlib.sha256(json.dumps({**body, "course_id": course_id, "lesson_ids": sorted(lesson_ids)}, sort_keys=True).encode()).hexdigest()
        with self.db() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(48,%s)", (uid % 2147483647,))
            cur.execute("SELECT * FROM academy_attempts WHERE user_id=%s AND request_key=%s FOR UPDATE", (uid, request_key))
            old = cur.fetchone()
            if old:
                if old["fingerprint"] != fingerprint:
                    fail("Bu so‘rov raqami boshqa test uchun ishlatilgan", 409)
                self._attempt_access(cur, old, uid)
                if old["status"] == "active" and utcnow() >= old["expires_at"]:
                    old = self._finish(cur, old)
                return {"attempt": self._attempt_public(old), "available_count": old["available_count"]}
            course = self.course(cur, course_id)
            access = self.access(cur, course, uid)
            if not access["owner"] and course["status"] != "published":
                fail("Kurs hozir ochiq emas", 404)
            cur.execute("""SELECT count(*) AS total FROM academy_attempts
                WHERE user_id=%s AND created_at>now()-interval '1 hour'""", (uid,))
            if cur.fetchone()["total"] >= 30:
                fail("Bir soatda 30 tagacha yangi test tuzish mumkin. Mavjud testingizni davom ettiring", 429)
            if scope == "completed":
                cur.execute("""SELECT lesson_id FROM academy_progress WHERE course_id=%s AND user_id=%s
                    AND status='completed' ORDER BY lesson_id LIMIT 501""", (course_id, uid))
                completed = {r["lesson_id"] for r in cur.fetchall()}
                if lesson_ids and not set(lesson_ids) <= completed:
                    fail("Tanlangan mavzular orasida hali tugatilmagan dars bor")
                lesson_ids = lesson_ids if lesson_ids else sorted(completed)
                if len(lesson_ids) > 100:
                    fail("100 tadan ko‘p mavzu o‘qilgansiz. Test uchun 100 tagacha mavzuni tanlang")
            if not lesson_ids:
                fail("Test uchun tugatilgan mavzu topilmadi")
            cur.execute("SELECT * FROM academy_lessons WHERE course_id=%s AND id=ANY(%s) ORDER BY position,id", (course_id, lesson_ids))
            lessons = cur.fetchall()
            if len(lessons) != len(lesson_ids):
                fail("Tanlangan mavzulardan biri ushbu kursga tegishli emas", 404)
            pool = []
            for lesson in lessons:
                if not access["owner"]:
                    if lesson["status"] != "published":
                        fail("Tanlangan dars hali nashr qilinmagan", 404)
                    if not (access["active"] or lesson["is_preview"]):
                        fail("Bu mavzular uchun kurs obunasini faollashtiring", 402)
                for q in as_json(lesson["content"]).get("questions", []):
                    if difficulty == "mixed" or q["difficulty"] == difficulty:
                        pool.append(dict(q, id=f"{lesson['id']}:{q['id']}", lesson_id=lesson["id"]))
            if not pool:
                fail("Tanlangan mavzu va qiyinlikda test savollari hali kiritilmagan")
            selected = secrets.SystemRandom().sample(pool, min(count, len(pool)))
            attempt_id = uuid.uuid4().hex
            expires_at = utcnow() + timedelta(minutes=minutes)
            cur.execute("""INSERT INTO academy_attempts(id,course_id,user_id,request_key,fingerprint,snapshot,available_count,expires_at)
                VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,%s) RETURNING *""",
                (attempt_id, course_id, uid, request_key, fingerprint, json.dumps(selected), len(pool), expires_at))
            return {"attempt": self._attempt_public(cur.fetchone()), "available_count": len(pool),
                    "notice": f"Bazadagi mavjud {len(selected)} ta savol olindi." if len(selected) < count else ""}

    def read_attempt(self, attempt_id, uid):
        with self.db() as cur:
            attempt = self._fetch_attempt(cur, attempt_id, uid)
            if attempt["status"] == "active" and utcnow() >= attempt["expires_at"]:
                attempt = self._finish(cur, attempt)
            return {"attempt": self._attempt_public(attempt)}

    def answer_attempt(self, attempt_id, uid, body, submit=False):
        payload(body, {"answers"}, {"answers"})
        with self.db() as cur:
            attempt = self._fetch_attempt(cur, attempt_id, uid)
            answers = quiz_answers(body["answers"], as_json(attempt["snapshot"]))
            if attempt["status"] != "completed":
                if submit or utcnow() >= attempt["expires_at"]:
                    attempt = self._finish(cur, attempt, answers)
                else:
                    merged = dict(as_json(attempt["answers"])) | answers
                    cur.execute("UPDATE academy_attempts SET answers=%s::jsonb WHERE id=%s RETURNING *", (json.dumps(merged), attempt_id))
                    attempt = dict(cur.fetchone())
            return {"result": as_json(attempt["result"])} if submit else {"attempt": self._attempt_public(attempt)}


def register_courses(app, platform):
    service = AcademyService(platform)

    @app.get("/api/kurslar/catalog")
    def catalog(q: str = "", subject: str = "", level: str = "", after_id: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)):
        return service.catalog(q, subject, level, after_id, limit)

    @app.get("/api/kurslar/capabilities")
    def capabilities(authorization: str | None = Header(None)):
        return service.capabilities(service.actor(authorization, optional=True))

    @app.get("/api/kurslar/mine")
    def mine(authorization: str | None = Header(None)):
        return service.mine(service.actor(authorization))

    @app.get("/api/kurslar/courses/{course_id}")
    def detail(course_id: int, authorization: str | None = Header(None)):
        return service.detail(course_id, service.actor(authorization, optional=True))

    @app.post("/api/kurslar/courses")
    def create(body: dict = Body(...), authorization: str | None = Header(None)):
        return service.create(service.actor(authorization), body)

    @app.put("/api/kurslar/courses/{course_id}")
    def update(course_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.update(course_id, service.actor(authorization), body)

    @app.post("/api/kurslar/courses/{course_id}/publish")
    def publish(course_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.transition(course_id, service.actor(authorization), body, "published")

    @app.post("/api/kurslar/courses/{course_id}/archive")
    def archive(course_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.transition(course_id, service.actor(authorization), body, "archived")

    @app.post("/api/kurslar/courses/{course_id}/join")
    def join(course_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.join(course_id, service.actor(authorization), body)

    @app.post("/api/kurslar/courses/{course_id}/lessons")
    def add_lessons(course_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.add_lessons(course_id, service.actor(authorization), body)

    @app.post("/api/kurslar/courses/{course_id}/reorder")
    def reorder(course_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.reorder(course_id, service.actor(authorization), body)

    @app.get("/api/kurslar/lessons/{lesson_id}")
    def lesson(lesson_id: int, authorization: str | None = Header(None)):
        return service.read_lesson(lesson_id, service.actor(authorization, optional=True))

    @app.put("/api/kurslar/lessons/{lesson_id}")
    def save_lesson(lesson_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.save_lesson(lesson_id, service.actor(authorization), body)

    @app.post("/api/kurslar/lessons/{lesson_id}/progress")
    def progress(lesson_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.save_progress(lesson_id, service.actor(authorization), body)

    @app.post("/api/kurslar/lessons/{lesson_id}/exercises/{exercise_id}/answer")
    def exercise(lesson_id: int, exercise_id: str, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.exercise(lesson_id, exercise_id, service.actor(authorization), body)

    @app.post("/api/kurslar/courses/{course_id}/attempts")
    def attempt_start(course_id: int, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.start_attempt(course_id, service.actor(authorization), body)

    @app.get("/api/kurslar/attempts/{attempt_id}")
    def attempt_get(attempt_id: str, authorization: str | None = Header(None)):
        return service.read_attempt(attempt_id, service.actor(authorization))

    @app.post("/api/kurslar/attempts/{attempt_id}/answers")
    def attempt_answers(attempt_id: str, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.answer_attempt(attempt_id, service.actor(authorization), body)

    @app.post("/api/kurslar/attempts/{attempt_id}/submit")
    def attempt_submit(attempt_id: str, body: dict = Body(...), authorization: str | None = Header(None)):
        return service.answer_attempt(attempt_id, service.actor(authorization), body, submit=True)

    return service

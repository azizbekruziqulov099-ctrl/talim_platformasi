"""REV51 private presentation projects, optional AI, and editable import/export.

Only authenticated real accounts may enter this module. Eligibility is re-read
from server tables for every operation; neither the document nor JWT role-like
claims supply permissions. This module creates only its own two tables.
"""
from __future__ import annotations

import base64
import binascii
import io
import json
import re
import stat
import zipfile
import zlib
from contextlib import contextmanager
from datetime import datetime
from email import policy
from email.parser import BytesParser
from threading import BoundedSemaphore, Lock
from xml.etree import ElementTree as ET

from fastapi import Header, HTTPException, Query, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

PREFIX = "/api/taqdimotlar"
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_REQUEST_BYTES = MAX_DOCUMENT_BYTES + 4096
MAX_DOCX_BYTES = 2 * 1024 * 1024
MAX_DOCX_EXPANDED = 10 * 1024 * 1024
MAX_SLIDES = 40
MAX_PROJECTS = 50
DEFAULT_GRADES = [8, 9, 10, 11]
NO_STORE = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}
INVALID_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")
LEGACY_DESIGN_FIELDS = {"background", "color", "image", "overlay", "panel", "accent", "text", "font", "size", "radius"}
DESIGN_FIELDS = LEGACY_DESIGN_FIELDS | {"template", "transition"}
LEGACY_SLIDE_FIELDS = {"id", "title", "section", "body", "formula", "example", "image", "layout", "design"}
SLIDE_FIELDS = LEGACY_SLIDE_FIELDS | {"body2", "body3", "image2", "image_prompt", "image2_prompt", "image_caption", "image2_caption", "placements", "elements"}
TEMPLATES = {"glass", "ribbon", "split", "gallery", "steps", "pencil", "arc", "spiral", "bands"}
LAYOUTS = {"text", "formula", "image", "cover", "two_columns", "two_images", "three_cards", "steps"}
LEGACY_DOCUMENT_FIELDS = {"schema", "title", "subject", "lesson_type", "design", "slides"}
DOCUMENT_FIELDS = LEGACY_DOCUMENT_FIELDS | {"audience"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS presentation_settings (
    singleton SMALLINT PRIMARY KEY CHECK(singleton=1),
    grades JSONB NOT NULL DEFAULT '[8,9,10,11]'::jsonb,
    updated_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO presentation_settings(singleton) VALUES(1) ON CONFLICT(singleton) DO NOTHING;
CREATE TABLE IF NOT EXISTS presentation_projects (
    id BIGSERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT NOT NULL CHECK(char_length(title) BETWEEN 1 AND 160),
    subject TEXT NOT NULL CHECK(char_length(subject)<=100),
    slide_count SMALLINT NOT NULL CHECK(slide_count BETWEEN 1 AND 40),
    document JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1 CHECK(version>0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS presentation_projects_owner_updated
    ON presentation_projects(owner_id,updated_at DESC,id DESC);
"""


def fail(message, status=422):
    raise HTTPException(status_code=status, detail=message, headers=NO_STORE)


def integer(value, label, low=1, high=2147483647):
    if type(value) is not int or not low <= value <= high:
        fail(f"{label}: {low}–{high} oralig‘ida butun son kiriting")
    return value


def fields(value, allowed, required=None):
    required = allowed if required is None else required
    if not isinstance(value, dict) or set(value) - set(allowed) or set(required) - set(value):
        fail("So‘rov maydonlari noto‘g‘ri yoki to‘liq emas")
    return value


def string(value, label, maximum, required=False):
    if not isinstance(value, str) or INVALID_XML.search(value):
        fail(f"{label}: ruxsat etilgan matn kiriting")
    value = value.strip()
    if len(value) > maximum or (required and not value):
        fail(f"{label}: {'1–' if required else '0–'}{maximum} belgi kiriting")
    return value


def choice(value, label, options):
    if not isinstance(value, str) or value not in options:
        fail(f"{label} noto‘g‘ri")
    return value


def json_size(value):
    try:
        return len(json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8"))
    except (TypeError, ValueError, RecursionError, UnicodeError):
        fail("JSON ma’lumoti noto‘g‘ri")


def image_value(value):
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > ((MAX_IMAGE_BYTES + 2) // 3) * 4 + 24:
        fail("Rasm PNG yoki JPEG bo‘lsin, hajmi 2 MB dan oshmasin", 413)
    match = re.fullmatch(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/]*={0,2})", value)
    if not match:
        fail("Faqat PNG yoki JPEG data URL rasmlar qabul qilinadi")
    try:
        raw = base64.b64decode(match[2], validate=True)
    except (ValueError, binascii.Error):
        fail("Rasm kodi noto‘g‘ri")
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        fail("Rasm hajmi 2 MB dan oshmasin", 413)
    from PIL import Image, UnidentifiedImageError
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format != {"png": "PNG", "jpeg": "JPEG"}[match[1]]:
                fail("Rasm turi uning mazmuniga mos emas")
            if min(im.size) < 1 or max(im.size) > 4096 or im.width * im.height > 16000000:
                fail("Rasm o‘lchami 4096 × 4096 dan va 16 million pikseldan oshmasin")
            if getattr(im, "n_frames", 1) != 1:
                fail("Animatsiyali rasm o‘rniga oddiy PNG yoki JPEG tanlang")
            im.verify()
        with Image.open(io.BytesIO(raw)) as decoded:
            decoded.load()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, Image.DecompressionBombError):
        fail("Rasm buzilgan yoki xavfsiz o‘qib bo‘lmaydi")
    return value


def validate_design(raw):
    fields(raw, DESIGN_FIELDS, LEGACY_DESIGN_FIELDS)
    out = {
        "template": choice(raw.get("template", "glass"), "Shablon", TEMPLATES),
        "transition": choice(raw.get("transition", "fade"), "Slayd almashinuvi", {"none", "fade", "push", "wipe"}),
        "background": choice(raw["background"], "Orqa fon", {"aurora", "paper", "midnight", "solid", "image"}),
        "color": string(raw["color"], "Fon rangi", 7, True),
        "image": image_value(raw["image"]),
        "overlay": integer(raw["overlay"], "Fon xiraligi", 0, 90),
        "panel": choice(raw["panel"], "Slayd ko‘rinishi", {"glass", "solid", "none"}),
        "accent": choice(raw["accent"], "Urg‘u rangi", {"cyan", "blue", "violet", "green", "amber"}),
        "text": choice(raw["text"], "Matn rangi", {"auto", "light", "dark"}),
        "font": choice(raw["font"], "Shrift", {"sans", "serif"}),
        "size": choice(raw["size"], "Matn o‘lchami", {"normal", "large"}),
        "radius": choice(raw["radius"], "Burchak", {"round", "square"}),
    }
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", out["color"]):
        fail("Rang #17394b ko‘rinishida bo‘lsin")
    if out["background"] == "image" and not out["image"]:
        fail("Rasmli fon uchun PNG yoki JPEG rasm tanlang")
    return out


def validate_document(raw):
    fields(raw, DOCUMENT_FIELDS, LEGACY_DOCUMENT_FIELDS)
    if json_size(raw) > MAX_DOCUMENT_BYTES:
        fail("Taqdimotning jami hajmi 8 MB dan oshmasin", 413)
    integer(raw["schema"], "Hujjat formati", 1, 2)
    out = {
        "schema": 2,
        "title": string(raw["title"], "Taqdimot nomi", 160, True),
        "subject": string(raw["subject"], "Fan", 100),
        "audience": string(raw.get("audience", ""), "Kim uchun", 120),
        "lesson_type": choice(raw["lesson_type"], "Dars turi", {"lecture", "practice", "seminar", "lab", "project"}),
        "design": validate_design(raw["design"]), "slides": [],
    }
    if not isinstance(raw["slides"], list) or not 1 <= len(raw["slides"]) <= MAX_SLIDES:
        fail("Taqdimotda 1–40 ta slayd bo‘lishi kerak")
    seen = set()
    for item in raw["slides"]:
        fields(item, SLIDE_FIELDS, LEGACY_SLIDE_FIELDS)
        slide_id = string(item["id"], "Slayd raqami", 96, True)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}", slide_id) or slide_id in seen:
            fail("Slayd raqamlari to‘g‘ri va takrorlanmagan bo‘lishi kerak")
        seen.add(slide_id)
        slide = {"id": slide_id}
        for name, label, maximum in (("title", "Slayd nomi", 100), ("section", "Bo‘lim", 60),
                                      ("body", "Slayd matni", 600), ("formula", "Formula", 400),
                                      ("example", "Misol", 250)):
            slide[name] = string(item[name], label, maximum)
        for name, label, maximum in (("body2", "Ikkinchi matn", 400), ("body3", "Uchinchi matn", 400),
                                     ("image_prompt", "Birinchi rasm tavsifi", 240), ("image2_prompt", "Ikkinchi rasm tavsifi", 240),
                                     ("image_caption", "Birinchi rasm izohi", 100), ("image2_caption", "Ikkinchi rasm izohi", 100)):
            slide[name] = string(item.get(name, ""), label, maximum)
        slide["image"] = image_value(item["image"])
        slide["image2"] = image_value(item.get("image2"))
        slide["layout"] = choice(item["layout"], "Slayd turi", LAYOUTS)
        slide["design"] = None if item["design"] is None else validate_design(item["design"])
        from .presentation_layout_validation import validate_slide_geometry
        try:
            slide.update(validate_slide_geometry(item, image_validator=image_value))
        except ValueError as exc:
            fail(str(exc))
        out["slides"].append(slide)
    return out


def validate_grades(raw):
    if not isinstance(raw, list) or len(raw) > 11:
        fail("Ruxsat berilgan sinflar ro‘yxati noto‘g‘ri")
    grades = [integer(v, "Sinf", 1, 11) for v in raw]
    if len(set(grades)) != len(grades):
        fail("Sinf raqamlari takrorlanmasin")
    return sorted(grades)


def parse_grade(value):
    """Accept stored school grades (8, 8-A, 8-sinf); never infer from age."""
    if type(value) is int:
        return value if 1 <= value <= 11 else None
    if not isinstance(value, str) or len(value) > 30:
        return None
    match = re.fullmatch(r"\s*(1[01]|[1-9])(?:\s*[- ]\s*(?:sinf(?:\s*[- ]?\s*[A-Za-z])?|[A-Za-z]))?\s*", value, re.I)
    return int(match[1]) if match else None


def _docx_xml_text(xml):
    """One pass with explicit XML depth/node/text budgets, including whitespace."""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    parser = ET.XMLPullParser(events=("start", "end"))
    paragraphs, active = [], []
    depth = nodes = length = 0
    root_seen = False
    for offset in range(0, len(xml), 16384):
        parser.feed(xml[offset:offset + 16384])
        for event, node in parser.read_events():
            if event == "start":
                if not root_seen:
                    root_seen = True
                    if node.tag != ns + "document":
                        fail("DOCX hujjat tuzilishi noto‘g‘ri")
                depth += 1
                nodes += 1
                if depth > 128 or nodes > 100000:
                    fail("DOCX tuzilishi juda murakkab. Kerakli matnni alohida hujjatda yuklang", 413)
                if node.tag == ns + "p":
                    paragraph = []
                    paragraphs.append(paragraph)
                    active.append(paragraph)
                continue
            piece = None
            if node.tag == ns + "t":
                piece = node.text or ""
            elif node.tag == ns + "tab":
                piece = "\t"
            elif node.tag in {ns + "br", ns + "cr"}:
                piece = "\n"
            if piece is not None and active:
                length += len(piece)
                if length > 100000:
                    fail("DOCX matni 100 000 belgidan oshgan. Kerakli qismini alohida yuklang", 413)
                active[-1].append(piece)
            if node.tag == ns + "p":
                active.pop()
            depth -= 1
            node.clear()
    parser.close()
    text = "\n\n".join(part for pieces in paragraphs if (part := "".join(pieces).strip()))
    if not text:
        fail("DOCX ichida o‘qiladigan matn topilmadi; rasmdagi matn avtomatik o‘qilmaydi")
    if len(text) > 100000:
        fail("DOCX matni 100 000 belgidan oshgan. Kerakli qismini alohida yuklang", 413)
    return {"text": text}


def docx_text(raw):
    """Read only document paragraphs, without resolving links or embedded files."""
    if len(raw) > MAX_DOCX_BYTES:
        fail("DOCX fayli 2 MB dan oshmasin", 413)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > 200 or sum(i.file_size for i in infos) > MAX_DOCX_EXPANDED:
                fail("DOCX kengaytirilgan hajmi 10 MB yoki qismlari 200 tadan oshgan", 413)
            names = set()
            for info in infos:
                name = info.filename
                if (name in names or name.startswith(("/", "\\")) or "\\" in name or ".." in name.split("/")
                        or ":" in name or info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16)
                        or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}):
                    fail("DOCX ichidagi fayl tuzilishi ruxsat etilmagan")
                names.add(name)
                if name.casefold().endswith("vbaproject.bin"):
                    fail("Makrosli hujjat qabul qilinmaydi; oddiy DOCX fayl tanlang")
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                fail("Haqiqiy DOCX hujjatini tanlang")
            xml = archive.read("word/document.xml").decode("utf-8-sig")
            if re.search(r"<!\s*(?:DOCTYPE|ENTITY)", xml, re.I):
                fail("DOCX ichida ruxsat etilmagan XML mavjud")
            return _docx_xml_text(xml)
    except HTTPException:
        raise
    except (zipfile.BadZipFile, zlib.error, RuntimeError, OSError, ValueError, UnicodeError, ET.ParseError):
        fail("DOCX fayli buzilgan yoki o‘qib bo‘lmaydi")


class PresentationService:
    def __init__(self, platform):
        self.platform = platform
        self._ready = False
        self._lock = Lock()
        self._export_slots = BoundedSemaphore(2)

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
                fail("Taqdimot xizmati hozir band. Birozdan keyin qayta urinib ko‘ring", 503)
            raise
        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def migrate(self):
        if self._ready:
            return
        with self._lock:
            if not self._ready:
                with self.db() as cur:
                    cur.execute("SELECT pg_advisory_xact_lock(49091301)")
                    cur.execute(SCHEMA)
                    from .presentation_ai_jobs import AI_JOBS_SCHEMA
                    cur.execute(AI_JOBS_SCHEMA)
                self._ready = True

    def actor(self, authorization):
        if not isinstance(authorization, str) or not authorization or len(authorization) > 8192:
            fail("Davom etish uchun shaxsiy hisobingizga kiring", 401)
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token or any(c.isspace() for c in token):
            fail("Kirish ma’lumoti noto‘g‘ri", 401)
        uid = self.platform._jwt_tekshir(token)
        auth = getattr(self.platform, "_kabutar_auth_service", None)
        if auth is None:
            fail("Kirish xizmati hali tayyor emas", 503)
        if auth.claims(token).get("admin_korish"):
            fail("Ko‘rish rejimida shaxsiy taqdimotlardan foydalanib bo‘lmaydi", 403)
        if type(uid) is not int or uid == 0 or not -(2**63) <= uid < 2**63:
            fail("Hisob raqami noto‘g‘ri", 401)
        return uid

    @staticmethod
    def settings(cur):
        cur.execute("SELECT grades FROM presentation_settings WHERE singleton=1")
        row = cur.fetchone()
        if not row:
            fail("Taqdimot xizmati hali tayyor emas", 503)
        grades = row["grades"]
        if isinstance(grades, str):
            grades = json.loads(grades)
        return {"grades": validate_grades(grades)}

    @staticmethod
    def institute_member(cur, uid):
        # Institute schema is lazily installed elsewhere. Read existing source
        # tables; do not create them or trust profile.universitet_id/lavozim.
        cur.execute("""SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'
            AND tablename=ANY(%s)""", (["universitetlar", "universitet_xodim_rollari", "universitet_qabul_talabalari",
                                       "universitet_guruh_azolari", "universitet_guruhlari", "kafedralar", "fakultetlar",
                                       "universitet_workspace_map", "organization_trials", "learning_contexts",
                                       "talaba_profillari"],))
        tables = {r["tablename"] for r in cur.fetchall()}
        if "universitetlar" not in tables:
            return False
        candidates, params = [], []
        if "universitet_xodim_rollari" in tables:
            candidates.append("SELECT universitet_id FROM universitet_xodim_rollari WHERE user_id=%s AND faol=TRUE")
            params.append(uid)
        if "universitet_qabul_talabalari" in tables:
            candidates.append("SELECT universitet_id FROM universitet_qabul_talabalari WHERE user_id=%s")
            params.append(uid)
        if "talaba_profillari" in tables:  # parol bilan o'zi qo'shilgan talabalar
            candidates.append("SELECT universitet_id FROM talaba_profillari WHERE user_id=%s")
            params.append(uid)
        if {"universitet_guruh_azolari", "universitet_guruhlari", "kafedralar", "fakultetlar"} <= tables:
            candidates.append("""SELECT f.universitet_id FROM universitet_guruh_azolari a
                JOIN universitet_guruhlari g ON g.id=a.guruh_id JOIN kafedralar k ON k.id=g.kafedra_id
                JOIN fakultetlar f ON f.id=k.fakultet_id WHERE a.user_id=%s""")
            params.append(uid)
        if not candidates:
            return False
        source_check = ""
        if {"universitet_workspace_map", "organization_trials", "learning_contexts"} <= tables:
            source_check = """AND NOT EXISTS (
                SELECT 1 FROM universitet_workspace_map wm
                LEFT JOIN organization_trials o ON o.context_id=wm.context_id
                LEFT JOIN learning_contexts c ON c.id=wm.context_id
                WHERE wm.universitet_id=u.id AND NOT COALESCE(
                    o.organization_type='institute' AND c.context_type='university' AND c.active=TRUE
                    AND LOWER(COALESCE(o.lifecycle_status,'')) IN ('trial','read_only','active'),FALSE))"""
        cur.execute("SELECT EXISTS(SELECT 1 FROM universitetlar u JOIN (" + " UNION ".join(candidates) + ") membership"
                    " ON membership.universitet_id=u.id WHERE to_jsonb(u)->>'archived_at' IS NULL " + source_check + ") AS member", tuple(params))
        return bool(cur.fetchone()["member"])

    def _capabilities(self, cur, uid):
        settings = self.settings(cur)
        cur.execute("""SELECT u.role,u.class,EXISTS(SELECT 1 FROM admin_akkaunt a WHERE a.uid=u.user_id) AS admin
            FROM users u WHERE u.user_id=%s""", (uid,))
        row = cur.fetchone()
        if not row:
            fail("Hisob topilmadi", 401)
        admin = bool(row["admin"])
        allowed = admin or row["role"] == "oqituvchi"
        if not allowed:
            allowed = self.institute_member(cur, uid)
        if not allowed and row["role"] == "oquvchi":
            allowed = parse_grade(row["class"]) in settings["grades"]
        reason = "" if allowed else "Taqdimotlar o‘qituvchilar, institut a’zolari va ruxsat berilgan yuqori sinf o‘quvchilari uchun ochiq."
        return {"allowed": bool(allowed), "admin": admin, "reason": reason, "settings": settings, "max_slides": MAX_SLIDES}

    def capabilities(self, uid):
        with self.db() as cur:
            capabilities = self._capabilities(cur, uid)
        from .presentation_ai import get_ai_capabilities
        capabilities["ai"] = get_ai_capabilities()
        return capabilities

    def generate_ai(self, uid, body):
        # Eligibility comes from the authenticated real account, never a role
        # or an audience string sent by the browser.
        with self.db() as cur:
            self.require(cur, uid)
        fields(body, {"document", "brief", "slide_ids"}, {"document", "brief"})
        document = validate_document(body["document"])
        from .presentation_ai import PresentationAIError, validate_generation_request
        from .presentation_ai_jobs import PresentationAIJobs
        try:
            validated = validate_generation_request(document, body["brief"], body.get("slide_ids"))
            result = PresentationAIJobs(self.db, self.require).generate(
                uid, document, validated["brief"], validated["slide_ids"])
            result["document"] = validate_document(result["document"])
            return result
        except PresentationAIError as exc:
            fail(exc.message, exc.status_code)

    def require(self, cur, uid, admin=False):
        capabilities = self._capabilities(cur, uid)
        if not capabilities["admin" if admin else "allowed"]:
            fail("Sozlamalarni faqat administrator o‘zgartiradi" if admin else capabilities["reason"], 403)
        return capabilities

    def set_settings(self, uid, body):
        fields(body, {"grades"})
        grades = validate_grades(body["grades"])
        with self.db() as cur:
            self.require(cur, uid, admin=True)
            cur.execute("""UPDATE presentation_settings SET grades=%s::jsonb,updated_by=%s,updated_at=now()
                WHERE singleton=1""", (json.dumps(grades), uid))
        return {"grades": grades}

    @staticmethod
    def public(row):
        document = row["document"]
        if isinstance(document, str):
            document = json.loads(document)
        # Upgrade legacy stored projects on read without changing owner/version
        # or writing a migration back over a concurrent editor's document.
        document = validate_document(document)
        updated = row["updated_at"]
        return {"id": row["id"], "version": row["version"], "document": document,
                "updated_at": updated.isoformat() if isinstance(updated, datetime) else updated}

    @staticmethod
    def owner(cur, uid, project_id, lock=False):
        integer(project_id, "Taqdimot raqami", 1, 2**63 - 1)
        cur.execute("SELECT * FROM presentation_projects WHERE id=%s AND owner_id=%s" + (" FOR UPDATE" if lock else ""), (project_id, uid))
        row = cur.fetchone()
        if not row:
            fail("Taqdimot topilmadi", 404)
        return row

    def list_projects(self, uid):
        with self.db() as cur:
            self.require(cur, uid)
            cur.execute("""SELECT id,title,subject,slide_count,version,updated_at FROM presentation_projects
                WHERE owner_id=%s ORDER BY updated_at DESC,id DESC LIMIT 50""", (uid,))
            projects = []
            for raw in cur.fetchall():
                row = dict(raw)
                if isinstance(row["updated_at"], datetime):
                    row["updated_at"] = row["updated_at"].isoformat()
                projects.append(row)
        return {"projects": projects}

    def get_project(self, uid, project_id):
        with self.db() as cur:
            self.require(cur, uid)
            return {"project": self.public(self.owner(cur, uid, project_id))}

    def save_project(self, uid, body, project_id=None):
        fields(body, {"document"} if project_id is None else {"version", "document"})
        document = validate_document(body["document"])
        version = None if project_id is None else integer(body["version"], "Versiya")
        with self.db() as cur:
            self.require(cur, uid)
            if project_id is None:
                # Serializes this account's creates, making the project cap atomic.
                cur.execute("SELECT user_id FROM users WHERE user_id=%s FOR UPDATE", (uid,))
                if not cur.fetchone():
                    fail("Hisob topilmadi", 401)
                cur.execute("SELECT COUNT(*) AS count FROM presentation_projects WHERE owner_id=%s", (uid,))
                if cur.fetchone()["count"] >= MAX_PROJECTS:
                    fail("Hisobingizda 50 ta taqdimot bor. Yangisini saqlashdan oldin bittasini o‘chiring", 409)
                cur.execute("""INSERT INTO presentation_projects(owner_id,title,subject,slide_count,document)
                    VALUES(%s,%s,%s,%s,%s::jsonb) RETURNING *""",
                            (uid, document["title"], document["subject"], len(document["slides"]), json.dumps(document, ensure_ascii=False)))
            else:
                row = self.owner(cur, uid, project_id, lock=True)
                if row["version"] != version:
                    fail("Taqdimot boshqa oynada yangilangan. Qayta ochib, o‘zgarishingizni saqlang", 409)
                if version == 2147483647:
                    fail("Taqdimot versiyalari chegarasiga yetildi. Yangi nusxa yarating", 409)
                cur.execute("""UPDATE presentation_projects SET title=%s,subject=%s,slide_count=%s,
                    document=%s::jsonb,version=version+1,updated_at=now() WHERE id=%s AND owner_id=%s RETURNING *""",
                            (document["title"], document["subject"], len(document["slides"]), json.dumps(document, ensure_ascii=False), project_id, uid))
            return {"project": self.public(cur.fetchone())}

    def delete_project(self, uid, project_id, version):
        integer(version, "Versiya")
        with self.db() as cur:
            self.require(cur, uid)
            row = self.owner(cur, uid, project_id, lock=True)
            if row["version"] != version:
                fail("Taqdimot boshqa oynada yangilangan. O‘chirishdan oldin qayta oching", 409)
            cur.execute("DELETE FROM presentation_projects WHERE id=%s AND owner_id=%s", (project_id, uid))
        return {"deleted": True}

    def export(self, uid, body):
        with self.db() as cur:
            self.require(cur, uid)
        if not self._export_slots.acquire(blocking=False):
            fail("Taqdimot eksporti hozir band. Birozdan keyin qayta urinib ko‘ring", 503)
        try:
            fields(body, {"document"})
            document = validate_document(body["document"])
            from .presentation_export import export_pptx
            try:
                data = export_pptx(document)
            except ValueError as exc:
                fail(str(exc) or "Taqdimotni eksport qilish uchun mazmunni tekshiring")
            return Response(data, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            headers=NO_STORE | {"Content-Disposition": 'attachment; filename="taqdimot.pptx"'})
        finally:
            self._export_slots.release()

    def import_docx(self, uid, raw):
        with self.db() as cur:
            self.require(cur, uid)
        return docx_text(raw)

    def template_docx(self, uid, body):
        with self.db() as cur:
            self.require(cur, uid)
        if not self._export_slots.acquire(blocking=False):
            fail("Taqdimot eksporti hozir band. Birozdan keyin qayta urinib ko‘ring", 503)
        try:
            fields(body, {"document"})
            document = validate_document(body["document"])
            from .presentation_docx import build_template_docx
            try:
                data = build_template_docx(document)
            except ValueError as exc:
                fail(str(exc) or "Word shabloni uchun mazmunni tekshiring")
            return Response(data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            headers=NO_STORE | {"Content-Disposition": 'attachment; filename="taqdimot-shabloni.docx"'})
        finally:
            self._export_slots.release()


async def bounded_body(request, limit):
    if request.headers.get("content-encoding", "identity").lower() != "identity":
        fail("Siqilgan HTTP so‘rovi qabul qilinmaydi", 415)
    claimed = request.headers.get("content-length")
    if claimed is not None:
        if not re.fullmatch(r"[0-9]{1,20}", claimed):
            fail("So‘rov hajmi noto‘g‘ri", 400)
        if int(claimed) > limit:
            fail("So‘rov hajmi ruxsat etilgan chegaradan oshgan", 413)
    chunks, length = [], 0
    async for chunk in request.stream():
        length += len(chunk)
        if length > limit:
            fail("So‘rov hajmi ruxsat etilgan chegaradan oshgan", 413)
        chunks.append(chunk)
    return b"".join(chunks)


def json_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            fail("JSON maydoni takrorlangan")
        out[key] = value
    return out


async def json_body(request, limit=MAX_REQUEST_BYTES):
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        fail("So‘rov application/json formatida bo‘lsin", 415)
    raw = await bounded_body(request, limit)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=json_pairs,
                           parse_constant=lambda _: fail("JSON soni noto‘g‘ri"))
    except (ValueError, UnicodeError, RecursionError):
        fail("So‘rov JSON ma’lumoti noto‘g‘ri")
    if not isinstance(value, dict):
        fail("So‘rov JSON obyekti bo‘lsin")
    return value


def multipart_docx(content_type, raw):
    """A bounded single browser form part; parsing cannot write to disk."""
    if not content_type or len(content_type) > 256 or "\r" in content_type or "\n" in content_type:
        fail("Faylni multipart/form-data ko‘rinishida yuklang", 415)
    try:
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + content_type.encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n" + raw)
    except (ValueError, UnicodeError):
        fail("Fayl yuklash so‘rovi noto‘g‘ri")
    if message.get_content_type() != "multipart/form-data" or not message.is_multipart() or message.defects:
        fail("Faylni multipart/form-data ko‘rinishida yuklang", 415)
    parts = list(message.iter_parts())
    if len(parts) != 1:
        fail("Bir vaqtda bitta DOCX fayl yuklang")
    part = parts[0]
    if (part.is_multipart() or part.defects or part.get_content_disposition() != "form-data"
            or part.get_param("name", header="content-disposition") != "file"
            or not (part.get_filename() or "").lower().endswith(".docx")
            or part.get("Content-Transfer-Encoding", "binary").lower() not in {"binary", "8bit"}):
        fail("file maydonida bitta oddiy DOCX fayl yuklang")
    payload = part.get_payload(decode=True)
    if not isinstance(payload, bytes) or not payload:
        fail("DOCX fayli bo‘sh")
    if len(payload) > MAX_DOCX_BYTES:
        fail("DOCX fayli 2 MB dan oshmasin", 413)
    return payload


def register_presentations(app, platform):
    service = PresentationService(platform)

    @app.get(PREFIX + "/capabilities")
    def capabilities(response: Response, authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        return service.capabilities(service.actor(authorization))

    @app.put(PREFIX + "/settings")
    async def settings(request: Request, response: Response, authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        uid = await run_in_threadpool(service.actor, authorization)
        return await run_in_threadpool(service.set_settings, uid, await json_body(request, 1024))

    @app.get(PREFIX + "/projects")
    def projects(response: Response, authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        return service.list_projects(service.actor(authorization))

    @app.post(PREFIX + "/projects", status_code=201)
    async def create(request: Request, response: Response, authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        uid = await run_in_threadpool(service.actor, authorization)
        return await run_in_threadpool(service.save_project, uid, await json_body(request))

    @app.get(PREFIX + "/projects/{project_id}")
    def detail(project_id: int, response: Response, authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        return service.get_project(service.actor(authorization), project_id)

    @app.put(PREFIX + "/projects/{project_id}")
    async def save(project_id: int, request: Request, response: Response, authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        uid = await run_in_threadpool(service.actor, authorization)
        return await run_in_threadpool(service.save_project, uid, await json_body(request), project_id)

    @app.delete(PREFIX + "/projects/{project_id}")
    def delete(project_id: int, response: Response, version: int = Query(..., ge=1, le=2147483647), authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        return service.delete_project(service.actor(authorization), project_id, version)

    @app.post(PREFIX + "/export")
    async def export(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(service.actor, authorization)
        return await run_in_threadpool(service.export, uid, await json_body(request))

    @app.post(PREFIX + "/ai/generate")
    async def generate_content(request: Request, response: Response, authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        uid = await run_in_threadpool(service.actor, authorization)
        return await run_in_threadpool(service.generate_ai, uid, await json_body(request))

    @app.post(PREFIX + "/import-docx")
    async def import_file(request: Request, response: Response, authorization: str | None = Header(None)):
        response.headers.update(NO_STORE)
        uid = await run_in_threadpool(service.actor, authorization)
        raw = await bounded_body(request, MAX_DOCX_BYTES + 8192)
        data = await run_in_threadpool(multipart_docx, request.headers.get("content-type"), raw)
        return await run_in_threadpool(service.import_docx, uid, data)

    @app.post(PREFIX + "/template-docx")
    async def template_file(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(service.actor, authorization)
        return await run_in_threadpool(service.template_docx, uid, await json_body(request))

    return service

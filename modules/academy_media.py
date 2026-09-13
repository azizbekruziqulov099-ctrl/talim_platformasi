"""REV47 course media: YouTube embeds and lesson-authorized PDF/images.

There is no paid video provider, network upload, public asset download endpoint,
or claim that YouTube videos cannot be copied. File storage uses the existing
database with explicit limits. Course access controls the lesson, not YouTube.
"""
from io import BytesIO
import json
import re
import threading
import uuid
import warnings
from urllib.parse import parse_qs, quote, urlsplit

MAX_FILE_BYTES = 10 * 1024 * 1024
COURSE_FILE_BYTES = 100 * 1024 * 1024
OWNER_FILE_BYTES = 500 * 1024 * 1024
MAX_COURSE_ASSETS = 1000
_VALIDATION_SLOT = threading.BoundedSemaphore(1)
EXTERNAL_NOTICE = "YouTube havolasi orqali video boshqa joyda ham ko‘rilishi mumkin. Ekran yozuvini to‘liq bloklash imkoni yo‘q."
SCHEMA = """
CREATE TABLE IF NOT EXISTS academy_assets (
 id TEXT PRIMARY KEY,
 course_id BIGINT NOT NULL REFERENCES academy_courses(id),
 owner_id BIGINT NOT NULL REFERENCES users(user_id),
 kind TEXT NOT NULL CHECK(kind IN ('video','file')),
 status TEXT NOT NULL CHECK(status IN ('uploading','ready','failed')),
 provider_id TEXT,
 provider TEXT NOT NULL CHECK(provider IN ('youtube','database')),
 filename TEXT NOT NULL, mime TEXT NOT NULL,
 size_bytes BIGINT NOT NULL DEFAULT 0 CHECK(size_bytes>=0 AND size_bytes<=10485760),
 data BYTEA, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CHECK((kind='video' AND provider='youtube' AND data IS NULL) OR
       (kind='file' AND provider='database' AND data IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS academy_assets_course ON academy_assets(course_id,id);
CREATE INDEX IF NOT EXISTS academy_assets_owner ON academy_assets(owner_id);
"""


def fail(status, message):
    from fastapi import HTTPException
    raise HTTPException(status_code=status, detail=message)


def youtube_id(value):
    """Normalize only a known YouTube URL. Never fetch a caller's URL."""
    if not isinstance(value, str) or not 1 <= len(value) <= 2048:
        fail(422, "YouTube video havolasini kiriting.")
    value = value.strip()
    if re.search(r"[\x00-\x20\x7f\\]", value):
        fail(422, "Video havolasi noto‘g‘ri.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        fail(422, "Video havolasi noto‘g‘ri.")
    if parsed.scheme not in {"https", "http"} or parsed.username or parsed.password or port:
        fail(422, "YouTube saytidagi to‘liq video havolasini kiriting.")
    host = (parsed.hostname or "").lower()
    try:
        query = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=40)
    except ValueError:
        fail(422, "Video havolasi juda uzun yoki noto‘g‘ri.")
    parts = parsed.path.strip("/").split("/")
    candidate = None
    if host in {"youtu.be", "www.youtu.be"} and len(parts) == 1:
        candidate = parts[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch" and len(query.get("v", [])) == 1:
            candidate = query["v"][0]
        elif len(parts) == 2 and parts[0] in {"embed", "shorts", "live"}:
            candidate = parts[1]
    elif host in {"youtube-nocookie.com", "www.youtube-nocookie.com"} and len(parts) == 2 and parts[0] == "embed":
        candidate = parts[1]
    if not candidate or not re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        fail(422, "Bitta YouTube videosining havolasini kiriting; kanal yoki ro‘yxat havolasi mos emas.")
    return candidate


def clean_filename(filename, extension):
    if not isinstance(filename, str):
        filename = "Dars materiali"
    filename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    stem = filename.rsplit(".", 1)[0]
    stem = re.sub(r"[^\w .()\-]", "_", stem, flags=re.UNICODE).strip(" ._")[:110]
    return (stem or "Dars materiali") + extension


def _safe_pdf(data):
    """Reject active/embedded content, bound the graph, then rebuild the PDF."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import IndirectObject, DictionaryObject, ArrayObject
    reader = PdfReader(BytesIO(data), strict=True)
    if reader.is_encrypted:
        raise ValueError("encrypted")
    dangerous = {"/JS", "/JavaScript", "/OpenAction", "/AA", "/Launch", "/EmbeddedFiles",
                 "/EF", "/RichMedia", "/XFA", "/AcroForm", "/Movie", "/Sound", "/GoToR"}
    seen = set()
    pending = [reader.trailer]
    inspected = 0
    while pending:
        inspected += 1
        if inspected > 50000:
            raise ValueError("complex PDF")
        obj = pending.pop()
        if isinstance(obj, IndirectObject):
            key = (obj.idnum, obj.generation)
            if key in seen:
                continue
            seen.add(key)
            pending.append(obj.get_object())
        elif isinstance(obj, DictionaryObject):
            if dangerous.intersection(str(k) for k in obj) or str(obj.get("/S", "")) in dangerous:
                raise ValueError("active PDF")
            if len(obj) > 10000:
                raise ValueError("complex PDF")
            pending.extend(obj.values())
        elif isinstance(obj, ArrayObject):
            if len(obj) > 10000:
                raise ValueError("complex PDF")
            pending.extend(obj)
    if not 1 <= len(reader.pages) <= 300:
        raise ValueError("page count")
    writer = PdfWriter()
    for page in reader.pages:
        # A static teaching attachment has no need for PDF action annotations.
        writer.add_page(page, excluded_keys=["/Annots", "/AA"])
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def validate_file(data, filename):
    """Trust decoded bytes, never the multipart MIME or filename extension."""
    if not isinstance(data, bytes) or not data or len(data) > MAX_FILE_BYTES:
        fail(413, "Fayl 10 MB dan oshmasligi va bo‘sh bo‘lmasligi kerak.")
    if data.startswith(b"%PDF-"):
        try:
            cleaned = _safe_pdf(data)
        except Exception:
            fail(422, "PDF buzilgan, parollangan yoki faol qo‘shimchali. Oddiy PDF qilib qayta saqlang.")
        mime, extension = "application/pdf", ".pdf"
    else:
        from PIL import Image, ImageOps
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(data)) as picture:
                    if picture.format not in {"JPEG", "PNG", "WEBP"}:
                        raise ValueError("format")
                    if getattr(picture, "n_frames", 1) != 1:
                        raise ValueError("animated")
                    if picture.width * picture.height > 20_000_000 or max(picture.size) > 12000:
                        raise ValueError("dimensions")
                    picture.verify()
                with Image.open(BytesIO(data)) as picture:
                    picture = ImageOps.exif_transpose(picture)
                    has_alpha = "A" in picture.getbands() or "transparency" in picture.info
                    picture = picture.convert("RGBA" if has_alpha else "RGB")
                    # Pixel-only re-encoding strips EXIF, executable trailers and metadata.
                    clean = Image.new(picture.mode, picture.size)
                    clean.paste(picture)
                    output = BytesIO()
                    clean.save(output, format="PNG" if has_alpha else "JPEG", quality=90)
                    cleaned = output.getvalue()
                    mime, extension = ("image/png", ".png") if has_alpha else ("image/jpeg", ".jpg")
        except Exception:
            fail(422, "Faqat oddiy PDF, JPG, PNG yoki WebP rasm yuklang (rasm 20 megapikseldan oshmasin).")
    if len(cleaned) > MAX_FILE_BYTES:
        fail(413, "Tayyorlangan fayl 10 MB dan oshdi. Rasm yoki hujjat hajmini kichraytiring.")
    return cleaned, mime, clean_filename(filename, extension)


def summary(asset):
    return {key: asset[key] for key in ("id", "status", "filename", "kind")}


class AcademyFileUploadLimit:
    """Limit multipart bytes before Starlette finishes spooling an upload."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or scope.get("method") != "POST" or not re.fullmatch(r"/api/kurslar/courses/[0-9]+/files", scope.get("path", "")):
            return await self.app(scope, receive, send)
        limit = MAX_FILE_BYTES + 128 * 1024  # Multipart headers plus one 10 MB file.
        length = next((v for k, v in scope.get("headers", []) if k.lower() == b"content-length"), None)
        if length:
            try:
                too_large = int(length) > limit or int(length) < 0
            except (ValueError, TypeError):
                too_large = True
            if too_large:
                from starlette.responses import JSONResponse
                return await JSONResponse({"detail": "Fayl 10 MB dan oshmasligi kerak."}, status_code=413)(scope, receive, send)
        count = 0

        async def bounded_receive():
            nonlocal count
            message = await receive()
            count += len(message.get("body", b""))
            if count > limit:
                # This parser exception closes in-progress spool files as well.
                from starlette.formparsers import MultiPartException
                raise MultiPartException("Fayl 10 MB dan oshmasligi kerak.")
            return message

        return await self.app(scope, bounded_receive, send)


class MediaService:
    def __init__(self, service):
        self.service = service

    def configured(self):
        return True  # YouTube embedding needs no paid service or API key.

    def migrate(self):
        with self.service.db() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(47003)")
            cur.execute(SCHEMA)

    def _quota(self, cur, course_id, uid, size):
        # Owner-wide lock also protects the aggregate quota across courses/workers.
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (f"academy-media:{uid}",))
        cur.execute("""SELECT COUNT(*) FILTER (WHERE course_id=%s) AS course_count,
                     COALESCE(SUM(size_bytes) FILTER (WHERE course_id=%s),0) AS course_size,
                     COALESCE(SUM(size_bytes),0) AS owner_size
                     FROM academy_assets WHERE owner_id=%s""", (course_id, course_id, uid))
        quota = cur.fetchone()
        if int(quota["course_count"]) >= MAX_COURSE_ASSETS:
            fail(409, "Kurs materiallari chegarasiga yetildi. Administratorga murojaat qiling.")
        if int(quota["course_size"]) + size > COURSE_FILE_BYTES or int(quota["owner_size"]) + size > OWNER_FILE_BYTES:
            fail(413, "Materiallar uchun joy chegarasiga yetildi: kursga 100 MB, ustozga jami 500 MB.")

    def add_video(self, course_id, authorization, payload):
        uid = self.service.actor(authorization)
        if not isinstance(payload, dict) or set(payload) != {"url"}:
            fail(422, "YouTube havolasini kiriting.")
        provider_id = youtube_id(payload["url"])
        with self.service.db() as cur:
            self.service.owner(cur, course_id, uid)
            self._quota(cur, course_id, uid, 0)
            # Repeated saves of the same link reuse its course-owned asset.
            cur.execute("SELECT id,status,filename,kind FROM academy_assets WHERE course_id=%s AND owner_id=%s AND provider='youtube' AND provider_id=%s ORDER BY created_at LIMIT 1", (course_id, uid, provider_id))
            existing = cur.fetchone()
            if existing:
                return {"asset": summary(existing), "notice": EXTERNAL_NOTICE}
            asset_id = "av_" + uuid.uuid4().hex
            filename = "YouTube video · " + provider_id
            cur.execute("""INSERT INTO academy_assets(id,course_id,owner_id,kind,status,provider_id,provider,filename,mime,size_bytes)
                         VALUES(%s,%s,%s,'video','ready',%s,'youtube',%s,'text/uri-list',0)""", (asset_id, course_id, uid, provider_id, filename))
        return {"asset": {"id": asset_id, "status": "ready", "filename": filename, "kind": "video"}, "notice": EXTERNAL_NOTICE}

    def add_file(self, course_id, uid, data, filename):
        # Pre-read and final checks: an upload cannot outlive revoked ownership.
        with self.service.db() as cur:
            self.service.owner(cur, course_id, uid)
        if not _VALIDATION_SLOT.acquire(blocking=False):
            fail(429, "Boshqa fayl tayyorlanmoqda. Bir ozdan keyin qayta yuklang.")
        try:
            cleaned, mime, filename = validate_file(data, filename)
        finally:
            _VALIDATION_SLOT.release()
        with self.service.db() as cur:
            self.service.owner(cur, course_id, uid)
            self._quota(cur, course_id, uid, len(cleaned))
            asset_id = "af_" + uuid.uuid4().hex
            cur.execute("""INSERT INTO academy_assets(id,course_id,owner_id,kind,status,provider,filename,mime,size_bytes,data)
                         VALUES(%s,%s,%s,'file','ready','database',%s,%s,%s,%s)""", (asset_id, course_id, uid, filename, mime, len(cleaned), cleaned))
        return {"asset": {"id": asset_id, "status": "ready", "filename": filename, "kind": "file"}}

    def refresh(self, asset_id, authorization):
        uid = self.service.actor(authorization)
        with self.service.db() as cur:
            cur.execute("SELECT id,status,filename,kind,course_id,owner_id FROM academy_assets WHERE id=%s", (asset_id,))
            asset = cur.fetchone()
            if not asset or int(asset["owner_id"]) != uid:
                fail(404, "Material topilmadi.")
            self.service.owner(cur, asset["course_id"], uid)
            return {"asset": summary(asset)}

    def _lesson_asset(self, cur, lesson_id, uid, kind, asset_id=None):
        lesson, course = self.service.lesson_access(cur, lesson_id, uid)
        content = lesson["content"]
        if isinstance(content, str):
            content = json.loads(content)
        if kind == "video":
            asset_id = content.get("video_id")
        elif not asset_id or asset_id not in content.get("attachments", []):
            fail(404, "Dars materiali topilmadi.")
        if not isinstance(asset_id, str) or not re.fullmatch(r"a[vf]_[a-f0-9]{32}", asset_id):
            fail(404, "Dars materiali topilmadi.")
        columns = "id,course_id,owner_id,kind,status,provider_id,provider,filename,mime,size_bytes"
        if kind == "file":
            columns += ",data"
        cur.execute(f"SELECT {columns} FROM academy_assets WHERE id=%s AND course_id=%s AND owner_id=%s AND kind=%s AND status='ready'", (asset_id, course["id"], course["teacher_id"], kind))
        asset = cur.fetchone()
        if not asset:
            fail(404, "Dars materiali topilmadi.")
        return asset

    def playback(self, lesson_id, authorization):
        uid = self.service.actor(authorization, optional=True)
        with self.service.db() as cur:
            asset = self._lesson_asset(cur, lesson_id, uid, "video")
        if asset["provider"] != "youtube" or not re.fullmatch(r"[A-Za-z0-9_-]{11}", asset.get("provider_id") or ""):
            fail(404, "Video topilmadi.")
        return {"url": f"https://www.youtube-nocookie.com/embed/{asset['provider_id']}?rel=0&playsinline=1",
                "expires_at": None, "watermark": f"KB-{uid}" if uid else "Bepul dars",
                "protection": "external_link", "notice": EXTERNAL_NOTICE}

    def download(self, lesson_id, asset_id, authorization):
        uid = self.service.actor(authorization, optional=True)
        with self.service.db() as cur:
            asset = self._lesson_asset(cur, lesson_id, uid, "file", asset_id)
        if asset["provider"] != "database" or asset["mime"] not in {"application/pdf", "image/jpeg", "image/png"}:
            fail(404, "Fayl topilmadi.")
        data = bytes(asset["data"])
        if not data or len(data) > MAX_FILE_BYTES:
            fail(404, "Fayl topilmadi.")
        return data, asset["mime"], asset["filename"]


def register_media(app, service):
    from fastapi import APIRouter, Body, File, Header, Response, UploadFile
    media = MediaService(service)
    service.video_configured = media.configured
    router = APIRouter(prefix="/api/kurslar", tags=["Kurs materiallari"])

    def private(response):
        response.headers["Cache-Control"] = "private, no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"

    @router.post("/courses/{course_id}/videos/link")
    def video_link(course_id: int, response: Response, payload: dict = Body(...), authorization: str | None = Header(None)):
        private(response)
        return media.add_video(course_id, authorization, payload)

    @router.post("/courses/{course_id}/videos/upload")
    def video_upload(course_id: int, authorization: str | None = Header(None)):
        uid = service.actor(authorization)
        with service.db() as cur:
            service.owner(cur, course_id, uid)
        fail(503, "Hozir YouTube havolasi orqali video qo‘shiladi. Video faylini saytga yuklash yoqilmagan.")

    @router.post("/courses/{course_id}/files")
    def file_upload(course_id: int, response: Response, file: UploadFile = File(...), authorization: str | None = Header(None)):
        private(response)
        try:
            uid = service.actor(authorization)
            with service.db() as cur:
                service.owner(cur, course_id, uid)
            data = file.file.read(MAX_FILE_BYTES + 1)
            return media.add_file(course_id, uid, data, file.filename)
        finally:
            file.file.close()

    @router.post("/assets/{asset_id}/refresh")
    def asset_refresh(asset_id: str, response: Response, authorization: str | None = Header(None)):
        private(response)
        return media.refresh(asset_id, authorization)

    @router.get("/lessons/{lesson_id}/playback")
    def playback(lesson_id: int, response: Response, authorization: str | None = Header(None)):
        private(response)
        return media.playback(lesson_id, authorization)

    @router.get("/lessons/{lesson_id}/files/{asset_id}")
    def lesson_file(lesson_id: int, asset_id: str, authorization: str | None = Header(None)):
        data, mime, filename = media.download(lesson_id, asset_id, authorization)
        return Response(content=data, media_type=mime, headers={
            "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}",
            "Content-Security-Policy": "sandbox; default-src 'none'",
        })

    app.include_router(router)
    app.add_middleware(AcademyFileUploadLimit)
    return media

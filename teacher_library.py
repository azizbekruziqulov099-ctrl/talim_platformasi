"""REV96: «Kutubxonam» — har bir o'qituvchining shaxsiy elektron kutubxonasi.

Polka (hujjat turi: dars ishlanmalari, testlar, rejalar …) → qator (fan yoki sinf) → hujjat.
Yangi hujjat avtomatik to'g'ri polka/qatorga qo'yiladi (yoki o'qituvchi o'zi tanlaydi), bir xil fayl ikki marta
saqlanmaydi, qidiruv imlo xatolariga chidamli, yordamchi suhbat orqali «shu hujjatimni top» deyish mumkin.
Hujjat ichini o'qish — faqat o'qituvchi sozlamada ruxsat berganda; ruxsat olib tashlansa o'qilgan matn o'chiriladi.
Har bir o'qituvchi faqat o'z kutubxonasini ko'radi.
"""
import hashlib
import json
import os
import re
from typing import List, Optional
from urllib.parse import quote

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

try:
    from . import teacher_library_search as S
except ImportError:  # pragma: no cover — bitta papkali joylashtirish
    import teacher_library_search as S

MAX_FILE_BYTES = 25 * 1024 * 1024
QUOTA_BYTES = 500 * 1024 * 1024
ALLOWED_EXT = {".pdf", ".doc", ".docx", ".rtf", ".odt", ".xls", ".xlsx", ".csv", ".ods", ".ppt", ".pptx", ".odp",
               ".txt", ".md", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".zip", ".rar", ".mp3", ".m4a", ".mp4"}
SORTED_OUT = "Saralanmagan"


class ShelfIn(BaseModel):
    nomi: str
    rang: Optional[str] = None
    belgi: Optional[str] = None


class RowIn(BaseModel):
    nomi: str


class DocPatch(BaseModel):
    nomi: Optional[str] = None
    polka_id: Optional[int] = None
    qator_id: Optional[int] = None
    teglar: Optional[List[str]] = None
    izoh: Optional[str] = None
    tartibsiz: Optional[bool] = None   # true → polkadan olib «Saralanmagan»ga


class SettingsIn(BaseModel):
    matn_oqish: Optional[bool] = None
    avto_joylash: Optional[bool] = None


class AskIn(BaseModel):
    xabar: str


def _clean_name(value, limit=120):
    v = re.sub(r"\s+", " ", str(value or "")).strip()[:limit]
    if not v:
        raise HTTPException(400, "Nomini yozing")
    return v


def _groq_keys():
    raw = [os.getenv("GROQ_API_KEYS", ""), os.getenv("GROQ_API_KEY", "")]
    keys = []
    for chunk in raw:
        for k in re.split(r"[,\s;]+", chunk):
            if k and k not in keys:
                keys.append(k)
    return keys


def ai_keywords(message, shelves):
    """Imlo juda buzilgan bo'lsa — AI so'rovdan to'g'ri yozilgan kalit so'zlarni ajratadi (hujjat matni yuborilmaydi)."""
    for key in _groq_keys()[:2]:
        try:
            with httpx.Client(timeout=12) as client:
                r = client.post("https://api.groq.com/openai/v1/chat/completions",
                                headers={"Authorization": f"Bearer {key}"},
                                json={"model": "llama-3.3-70b-versatile", "temperature": 0, "max_tokens": 200,
                                      "response_format": {"type": "json_object"},
                                      "messages": [
                                          {"role": "system", "content": (
                                              "Sen o'qituvchining hujjat qidiruv yordamchisisan. Foydalanuvchi o'zbekcha (lotin/kirill, "
                                              "sheva, imlo xatolari bilan) yozadi. Qidirilayotgan hujjat uchun to'g'ri o'zbek lotin "
                                              "imlosida 1-6 ta kalit so'z qaytar (fan, sinf, hujjat turi, mavzu). Buyruq so'zlarini "
                                              "(top, ber, qani, hujjat) qo'shma. Faqat JSON: {\"sozlar\":[...],\"tur\":\"word|pdf|excel|slides|image|\"}")},
                                          {"role": "user", "content": json.dumps({"xabar": message[:400], "polkalar": shelves[:30]}, ensure_ascii=False)},
                                      ]})
            if r.status_code == 429:
                continue
            r.raise_for_status()
            data = json.loads(r.json()["choices"][0]["message"]["content"])
            words = [w for s in data.get("sozlar") or [] for w in S.tokens(s)][:10]
            if data.get("tur") in S.TYPE_WORDS:
                words.append(data["tur"])
            return words
        except Exception:
            continue
    return []


def create_teacher_library_router(check_token, db, ai=ai_keywords):
    router = APIRouter(prefix="/api/kutubxonam", tags=["teacher-library"])
    ready = {"ok": False}

    def ensure(cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS oqituvchi_kutubxona_polkalar(
              id BIGSERIAL PRIMARY KEY, user_id INTEGER NOT NULL, nomi VARCHAR(120) NOT NULL,
              belgi VARCHAR(16), rang VARCHAR(20), tartib INTEGER NOT NULL DEFAULT 0,
              avto BOOLEAN NOT NULL DEFAULT FALSE, yaratilgan TIMESTAMPTZ NOT NULL DEFAULT NOW());
            CREATE UNIQUE INDEX IF NOT EXISTS ux_okp_nom ON oqituvchi_kutubxona_polkalar(user_id, LOWER(nomi));
            CREATE TABLE IF NOT EXISTS oqituvchi_kutubxona_qatorlar(
              id BIGSERIAL PRIMARY KEY, polka_id BIGINT NOT NULL REFERENCES oqituvchi_kutubxona_polkalar(id) ON DELETE CASCADE,
              user_id INTEGER NOT NULL, nomi VARCHAR(120) NOT NULL, tartib INTEGER NOT NULL DEFAULT 0,
              yaratilgan TIMESTAMPTZ NOT NULL DEFAULT NOW());
            CREATE UNIQUE INDEX IF NOT EXISTS ux_okq_nom ON oqituvchi_kutubxona_qatorlar(polka_id, LOWER(nomi));
            CREATE TABLE IF NOT EXISTS oqituvchi_kutubxona_hujjatlar(
              id BIGSERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
              polka_id BIGINT REFERENCES oqituvchi_kutubxona_polkalar(id) ON DELETE SET NULL,
              qator_id BIGINT REFERENCES oqituvchi_kutubxona_qatorlar(id) ON DELETE SET NULL,
              nomi VARCHAR(240) NOT NULL, fayl_nomi VARCHAR(240) NOT NULL, mime VARCHAR(160),
              hajm BIGINT NOT NULL, sha256 VARCHAR(64) NOT NULL, tarkib BYTEA NOT NULL,
              matn TEXT, teglar TEXT[] NOT NULL DEFAULT '{}', izoh TEXT,
              yaratilgan TIMESTAMPTZ NOT NULL DEFAULT NOW(), ochilgan TIMESTAMPTZ);
            CREATE INDEX IF NOT EXISTS ix_okh_user ON oqituvchi_kutubxona_hujjatlar(user_id);
            CREATE UNIQUE INDEX IF NOT EXISTS ux_okh_sha ON oqituvchi_kutubxona_hujjatlar(user_id, sha256);
            CREATE TABLE IF NOT EXISTS oqituvchi_kutubxona_sozlama(
              user_id INTEGER PRIMARY KEY, matn_oqish BOOLEAN NOT NULL DEFAULT FALSE,
              avto_joylash BOOLEAN NOT NULL DEFAULT TRUE, yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW());
        """)

    def teacher(cur, token):
        uid = check_token(token)
        cur.execute("SELECT role FROM users WHERE user_id=%s", (uid,))
        row = cur.fetchone() or {}
        if row.get("role") in ("oqituvchi", "admin"):
            return uid
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
        if cur.fetchone():
            return uid
        raise HTTPException(403, "Kutubxonam — o‘qituvchilar uchun")

    def run(token, fn):
        conn = db()
        cur = conn.cursor()
        try:
            if not ready["ok"]:
                ensure(cur)
                conn.commit()   # jadvallar darhol saqlansin — keyingi xato ularni bekor qilmasin
                ready["ok"] = True
            uid = teacher(cur, token)
            out = fn(cur, uid)
            conn.commit()
            return out
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def settings(cur, uid):
        cur.execute("SELECT matn_oqish, avto_joylash FROM oqituvchi_kutubxona_sozlama WHERE user_id=%s", (uid,))
        row = cur.fetchone()
        return {"matn_oqish": bool(row["matn_oqish"]), "avto_joylash": bool(row["avto_joylash"])} if row else {"matn_oqish": False, "avto_joylash": True}

    def shelf_id(cur, uid, name, auto=True):
        cur.execute("SELECT id FROM oqituvchi_kutubxona_polkalar WHERE user_id=%s AND LOWER(nomi)=LOWER(%s)", (uid, name))
        row = cur.fetchone()
        if row:
            return row["id"]
        icon, color = S.shelf_style(name)
        cur.execute("""INSERT INTO oqituvchi_kutubxona_polkalar(user_id,nomi,belgi,rang,avto,tartib)
                       VALUES(%s,%s,%s,%s,%s,(SELECT COALESCE(MAX(tartib),0)+1 FROM oqituvchi_kutubxona_polkalar WHERE user_id=%s))
                       ON CONFLICT (user_id, LOWER(nomi)) DO UPDATE SET nomi=oqituvchi_kutubxona_polkalar.nomi RETURNING id""",
                    (uid, name, icon, color, auto, uid))
        return cur.fetchone()["id"]

    def row_id(cur, uid, shelf, name):
        cur.execute("SELECT id FROM oqituvchi_kutubxona_qatorlar WHERE polka_id=%s AND LOWER(nomi)=LOWER(%s)", (shelf, name))
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute("""INSERT INTO oqituvchi_kutubxona_qatorlar(polka_id,user_id,nomi,tartib)
                       VALUES(%s,%s,%s,(SELECT COALESCE(MAX(tartib),0)+1 FROM oqituvchi_kutubxona_qatorlar WHERE polka_id=%s))
                       ON CONFLICT (polka_id, LOWER(nomi)) DO UPDATE SET nomi=oqituvchi_kutubxona_qatorlar.nomi RETURNING id""",
                    (shelf, uid, name, shelf))
        return cur.fetchone()["id"]

    def own_shelf(cur, uid, sid):
        cur.execute("SELECT id,nomi FROM oqituvchi_kutubxona_polkalar WHERE id=%s AND user_id=%s", (sid, uid))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Polka topilmadi")
        return row

    def own_row(cur, uid, rid, sid=None):
        cur.execute("SELECT id,polka_id,nomi FROM oqituvchi_kutubxona_qatorlar WHERE id=%s AND user_id=%s", (rid, uid))
        row = cur.fetchone()
        if not row or (sid and row["polka_id"] != sid):
            raise HTTPException(404, "Qator topilmadi (yoki boshqa polkada)")
        return row

    def shelf_names(cur, uid):
        cur.execute("SELECT nomi FROM oqituvchi_kutubxona_polkalar WHERE user_id=%s ORDER BY tartib", (uid,))
        return [r["nomi"] for r in cur.fetchall()]

    DOC_COLS = """h.id,h.nomi,h.fayl_nomi,h.mime,h.hajm,h.teglar,h.izoh,h.polka_id,h.qator_id,
                  h.yaratilgan,h.ochilgan,p.nomi AS polka,q.nomi AS qator"""

    def doc_json(r):
        return {"id": r["id"], "nomi": r["nomi"], "fayl_nomi": r["fayl_nomi"], "mime": r.get("mime"), "hajm": r["hajm"],
                "teglar": list(r.get("teglar") or []), "izoh": r.get("izoh") or "", "polka_id": r.get("polka_id"),
                "qator_id": r.get("qator_id"), "polka": r.get("polka"), "qator": r.get("qator"),
                "turi": S.kind_of(r["fayl_nomi"]) or "boshqa", "matn_bor": bool(r.get("matn_bor")),
                "yaratilgan": r["yaratilgan"].isoformat() if r.get("yaratilgan") else None,
                "ochilgan": r["ochilgan"].isoformat() if r.get("ochilgan") else None,
                **({"ball": r["ball"], "topildi": r.get("topildi", []), "parcha": r.get("parcha", "")} if "ball" in r else {})}

    def all_docs(cur, uid, with_text=False):
        cur.execute(f"""SELECT {DOC_COLS}, (h.matn IS NOT NULL AND h.matn<>'') AS matn_bor
                        {', h.matn' if with_text else ''}
                        FROM oqituvchi_kutubxona_hujjatlar h
                        LEFT JOIN oqituvchi_kutubxona_polkalar p ON p.id=h.polka_id
                        LEFT JOIN oqituvchi_kutubxona_qatorlar q ON q.id=h.qator_id
                        WHERE h.user_id=%s ORDER BY h.yaratilgan DESC""", (uid,))
        return [dict(r) for r in cur.fetchall()]

    def place(cur, uid, file_name, text, sid=None, rid=None):
        """(polka_id, qator_id, avto) — o'qituvchi tanlagani ustun, qolgani avtomatik."""
        if rid and not sid:
            sid = own_row(cur, uid, rid)["polka_id"]
        if sid:
            own_shelf(cur, uid, sid)
            if rid:
                own_row(cur, uid, rid, sid)
                return sid, rid, False
            _s, row_name = S.classify(file_name, text, [])
            return sid, row_id(cur, uid, sid, row_name), True
        shelf_name, row_name = S.classify(file_name, text, shelf_names(cur, uid))
        sid = shelf_id(cur, uid, shelf_name)
        return sid, row_id(cur, uid, sid, row_name), True

    @router.get("")
    def overview(token: str):
        def fn(cur, uid):
            cur.execute("""SELECT p.id,p.nomi,p.belgi,p.rang,p.avto,p.tartib FROM oqituvchi_kutubxona_polkalar p
                           WHERE p.user_id=%s ORDER BY p.tartib, p.id""", (uid,))
            shelves = [dict(r) for r in cur.fetchall()]
            cur.execute("""SELECT q.id,q.polka_id,q.nomi FROM oqituvchi_kutubxona_qatorlar q WHERE q.user_id=%s
                           ORDER BY q.tartib, q.id""", (uid,))
            rows = [dict(r) for r in cur.fetchall()]
            docs = [doc_json(d) for d in all_docs(cur, uid)]
            for s in shelves:
                s["qatorlar"] = [dict(r, soni=sum(1 for d in docs if d["qator_id"] == r["id"])) for r in rows if r["polka_id"] == s["id"]]
                s["soni"] = sum(1 for d in docs if d["polka_id"] == s["id"])
            used = sum(d["hajm"] for d in docs)
            return {"polkalar": shelves, "hujjatlar": docs, "saralanmagan": sum(1 for d in docs if not d["polka_id"]),
                    "sozlama": settings(cur, uid), "hajm": {"ishlatilgan": used, "limit": QUOTA_BYTES, "fayl_limit": MAX_FILE_BYTES}}
        return run(token, fn)

    @router.post("/polka")
    def add_shelf(token: str, body: ShelfIn):
        name = _clean_name(body.nomi)

        def fn(cur, uid):
            cur.execute("SELECT id FROM oqituvchi_kutubxona_polkalar WHERE user_id=%s AND LOWER(nomi)=LOWER(%s)", (uid, name))
            if cur.fetchone():
                raise HTTPException(409, f"«{name}» nomli polka allaqachon bor")
            sid = shelf_id(cur, uid, name, auto=False)
            if body.rang or body.belgi:
                cur.execute("UPDATE oqituvchi_kutubxona_polkalar SET rang=COALESCE(%s,rang), belgi=COALESCE(%s,belgi) WHERE id=%s",
                            (body.rang, body.belgi, sid))
            return {"id": sid, "nomi": name}
        return run(token, fn)

    @router.patch("/polka/{sid}")
    def edit_shelf(sid: int, token: str, body: ShelfIn):
        name = _clean_name(body.nomi)

        def fn(cur, uid):
            own_shelf(cur, uid, sid)
            cur.execute("SELECT id FROM oqituvchi_kutubxona_polkalar WHERE user_id=%s AND LOWER(nomi)=LOWER(%s) AND id<>%s", (uid, name, sid))
            if cur.fetchone():
                raise HTTPException(409, f"«{name}» nomli polka allaqachon bor")
            cur.execute("UPDATE oqituvchi_kutubxona_polkalar SET nomi=%s, rang=COALESCE(%s,rang), belgi=COALESCE(%s,belgi), avto=FALSE WHERE id=%s",
                        (name, body.rang, body.belgi, sid))
            return {"ok": True}
        return run(token, fn)

    @router.delete("/polka/{sid}")
    def delete_shelf(sid: int, token: str):
        def fn(cur, uid):
            own_shelf(cur, uid, sid)
            cur.execute("UPDATE oqituvchi_kutubxona_hujjatlar SET polka_id=NULL, qator_id=NULL WHERE polka_id=%s AND user_id=%s", (sid, uid))
            moved = cur.rowcount
            cur.execute("DELETE FROM oqituvchi_kutubxona_polkalar WHERE id=%s AND user_id=%s", (sid, uid))
            return {"ok": True, "saralanmaganga": moved}
        return run(token, fn)

    @router.post("/polka/{sid}/qator")
    def add_row(sid: int, token: str, body: RowIn):
        name = _clean_name(body.nomi)

        def fn(cur, uid):
            own_shelf(cur, uid, sid)
            cur.execute("SELECT id FROM oqituvchi_kutubxona_qatorlar WHERE polka_id=%s AND LOWER(nomi)=LOWER(%s)", (sid, name))
            if cur.fetchone():
                raise HTTPException(409, f"Bu polkada «{name}» qatori allaqachon bor")
            return {"id": row_id(cur, uid, sid, name), "nomi": name}
        return run(token, fn)

    @router.patch("/qator/{rid}")
    def edit_row(rid: int, token: str, body: RowIn):
        name = _clean_name(body.nomi)

        def fn(cur, uid):
            r = own_row(cur, uid, rid)
            cur.execute("SELECT id FROM oqituvchi_kutubxona_qatorlar WHERE polka_id=%s AND LOWER(nomi)=LOWER(%s) AND id<>%s", (r["polka_id"], name, rid))
            if cur.fetchone():
                raise HTTPException(409, f"Bu polkada «{name}» qatori allaqachon bor")
            cur.execute("UPDATE oqituvchi_kutubxona_qatorlar SET nomi=%s WHERE id=%s", (name, rid))
            return {"ok": True}
        return run(token, fn)

    @router.delete("/qator/{rid}")
    def delete_row(rid: int, token: str):
        def fn(cur, uid):
            own_row(cur, uid, rid)
            cur.execute("UPDATE oqituvchi_kutubxona_hujjatlar SET qator_id=NULL WHERE qator_id=%s AND user_id=%s", (rid, uid))
            cur.execute("DELETE FROM oqituvchi_kutubxona_qatorlar WHERE id=%s AND user_id=%s", (rid, uid))
            return {"ok": True}
        return run(token, fn)

    @router.post("/hujjat")
    def upload(token: str = Form(...), fayl: UploadFile = File(...), polka_id: Optional[int] = Form(None),
                     qator_id: Optional[int] = Form(None), nomi: str = Form(""), teglar: str = Form("")):
        file_name = re.sub(r"[\\/\x00-\x1f]+", "_", (fayl.filename or "hujjat").strip())[-200:] or "hujjat"
        ext = S.ext_of(file_name)
        if ext not in ALLOWED_EXT:
            raise HTTPException(400, f"«{ext or 'nomaʼlum'}» turidagi faylni saqlab bo‘lmaydi. Word, PDF, Excel, taqdimot yoki rasm yuklang.")
        data = fayl.file.read(MAX_FILE_BYTES + 1)
        if not data:
            raise HTTPException(400, "Fayl bo‘sh")
        if len(data) > MAX_FILE_BYTES:
            raise HTTPException(413, f"Fayl juda katta — eng ko‘pi {MAX_FILE_BYTES // (1024 * 1024)} MB")
        digest = hashlib.sha256(data).hexdigest()
        title = _clean_name(nomi or re.sub(r"\.[A-Za-z0-9]{1,5}$", "", file_name).replace("_", " "), 240)
        tags = [t.strip()[:40] for t in re.split(r"[,;#]+", teglar or "") if t.strip()][:12]

        def fn(cur, uid):
            cur.execute(f"""SELECT {DOC_COLS} FROM oqituvchi_kutubxona_hujjatlar h
                            LEFT JOIN oqituvchi_kutubxona_polkalar p ON p.id=h.polka_id
                            LEFT JOIN oqituvchi_kutubxona_qatorlar q ON q.id=h.qator_id
                            WHERE h.user_id=%s AND h.sha256=%s""", (uid, digest))
            same = cur.fetchone()
            if same:
                d = doc_json(dict(same))
                return {"dublikat": True, "hujjat": d, "xabar": f"Bu fayl kutubxonangizda allaqachon bor: «{d['nomi']}» — {S._place(d)}."}
            cur.execute("SELECT COALESCE(SUM(hajm),0) AS s FROM oqituvchi_kutubxona_hujjatlar WHERE user_id=%s", (uid,))
            if int(cur.fetchone()["s"]) + len(data) > QUOTA_BYTES:
                raise HTTPException(413, f"Kutubxona to‘ldi ({QUOTA_BYTES // (1024 * 1024)} MB). Keraksiz hujjatlarni o‘chiring.")
            opts = settings(cur, uid)
            text = S.extract_text(file_name, data) if opts["matn_oqish"] else ""
            if polka_id or qator_id or opts["avto_joylash"]:
                sid, rid, auto = place(cur, uid, title + S.ext_of(file_name), text, polka_id, qator_id)
            else:
                sid, rid, auto = None, None, False
            mime = fayl.content_type or "application/octet-stream"
            cur.execute("""INSERT INTO oqituvchi_kutubxona_hujjatlar(user_id,polka_id,qator_id,nomi,fayl_nomi,mime,hajm,sha256,tarkib,matn,teglar)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (uid, sid, rid, title, file_name, mime[:160], len(data), digest, data, text or None, tags))
            new_id = cur.fetchone()["id"]
            cur.execute(f"""SELECT {DOC_COLS}, (h.matn IS NOT NULL AND h.matn<>'') AS matn_bor FROM oqituvchi_kutubxona_hujjatlar h
                            LEFT JOIN oqituvchi_kutubxona_polkalar p ON p.id=h.polka_id
                            LEFT JOIN oqituvchi_kutubxona_qatorlar q ON q.id=h.qator_id WHERE h.id=%s""", (new_id,))
            d = doc_json(dict(cur.fetchone()))
            how = "o‘zim joyladim" if auto else "siz tanlagan joyga qo‘ydim"
            msg = f"Saqlandi ✅ {S._place(d)} ({how})." if sid else "Saqlandi ✅ «Saralanmagan»da turibdi."
            return {"dublikat": False, "hujjat": d, "xabar": msg}
        return run(token, fn)

    @router.get("/hujjat/{did}/fayl")
    def download(did: int, token: str, yuklab: int = 0):
        def fn(cur, uid):
            cur.execute("SELECT fayl_nomi,mime,tarkib FROM oqituvchi_kutubxona_hujjatlar WHERE id=%s AND user_id=%s", (did, uid))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Hujjat topilmadi")
            cur.execute("UPDATE oqituvchi_kutubxona_hujjatlar SET ochilgan=NOW() WHERE id=%s", (did,))
            return row
        row = run(token, fn)
        name = row["fayl_nomi"]
        ascii_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name) or "hujjat"
        mode = "attachment" if yuklab or S.kind_of(name) not in ("pdf", "image") else "inline"
        return Response(bytes(row["tarkib"]), media_type=row["mime"] or "application/octet-stream",
                        headers={"Content-Disposition": f"{mode}; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name, safe='')}",
                                 "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})

    @router.patch("/hujjat/{did}")
    def edit_doc(did: int, token: str, body: DocPatch):
        def fn(cur, uid):
            cur.execute("SELECT id,polka_id FROM oqituvchi_kutubxona_hujjatlar WHERE id=%s AND user_id=%s", (did, uid))
            cur_row = cur.fetchone()
            if not cur_row:
                raise HTTPException(404, "Hujjat topilmadi")
            sets, vals = [], []
            if body.nomi is not None:
                sets.append("nomi=%s"); vals.append(_clean_name(body.nomi, 240))
            if body.izoh is not None:
                sets.append("izoh=%s"); vals.append(body.izoh.strip()[:1000] or None)
            if body.teglar is not None:
                sets.append("teglar=%s"); vals.append([t.strip()[:40] for t in body.teglar if t and t.strip()][:12])
            if body.tartibsiz:
                sets += ["polka_id=NULL", "qator_id=NULL"]
            elif body.polka_id is not None or body.qator_id is not None:
                sid = body.polka_id or cur_row["polka_id"]
                if body.qator_id:
                    r = own_row(cur, uid, body.qator_id)
                    sid = r["polka_id"] if not body.polka_id else sid
                    own_row(cur, uid, body.qator_id, sid)
                own_shelf(cur, uid, sid)
                sets += ["polka_id=%s", "qator_id=%s"]; vals += [sid, body.qator_id]
            if sets:
                cur.execute(f"UPDATE oqituvchi_kutubxona_hujjatlar SET {', '.join(sets)} WHERE id=%s AND user_id=%s", (*vals, did, uid))
            return {"ok": True}
        return run(token, fn)

    @router.delete("/hujjat/{did}")
    def delete_doc(did: int, token: str):
        def fn(cur, uid):
            cur.execute("DELETE FROM oqituvchi_kutubxona_hujjatlar WHERE id=%s AND user_id=%s", (did, uid))
            if not cur.rowcount:
                raise HTTPException(404, "Hujjat topilmadi")
            return {"ok": True}
        return run(token, fn)

    @router.put("/sozlama")
    def save_settings(token: str, body: SettingsIn):
        def fn(cur, uid):
            old = settings(cur, uid)
            new = {k: (getattr(body, k) if getattr(body, k) is not None else old[k]) for k in old}
            cur.execute("""INSERT INTO oqituvchi_kutubxona_sozlama(user_id,matn_oqish,avto_joylash) VALUES(%s,%s,%s)
                           ON CONFLICT (user_id) DO UPDATE SET matn_oqish=EXCLUDED.matn_oqish, avto_joylash=EXCLUDED.avto_joylash, yangilangan=NOW()""",
                        (uid, new["matn_oqish"], new["avto_joylash"]))
            read = 0
            if new["matn_oqish"] and not old["matn_oqish"]:
                cur.execute("SELECT id,fayl_nomi FROM oqituvchi_kutubxona_hujjatlar WHERE user_id=%s AND matn IS NULL ORDER BY id DESC LIMIT 80", (uid,))
                for r in cur.fetchall():
                    cur.execute("SELECT tarkib FROM oqituvchi_kutubxona_hujjatlar WHERE id=%s", (r["id"],))
                    text = S.extract_text(r["fayl_nomi"], bytes(cur.fetchone()["tarkib"]))
                    cur.execute("UPDATE oqituvchi_kutubxona_hujjatlar SET matn=%s WHERE id=%s", (text or "", r["id"]))
                    read += 1 if text else 0
            if not new["matn_oqish"] and old["matn_oqish"]:
                cur.execute("UPDATE oqituvchi_kutubxona_hujjatlar SET matn=NULL WHERE user_id=%s", (uid,))
            return {"sozlama": new, "oqildi": read}
        return run(token, fn)

    @router.post("/tartibla")
    def tidy(token: str):
        def fn(cur, uid):
            cur.execute("SELECT id,nomi,fayl_nomi,matn FROM oqituvchi_kutubxona_hujjatlar WHERE user_id=%s AND polka_id IS NULL", (uid,))
            moved = []
            for r in cur.fetchall():
                sid, rid, _a = place(cur, uid, r["nomi"] + S.ext_of(r["fayl_nomi"]), r.get("matn") or "")
                cur.execute("UPDATE oqituvchi_kutubxona_hujjatlar SET polka_id=%s, qator_id=%s WHERE id=%s", (sid, rid, r["id"]))
                moved.append(r["id"])
            cur.execute("""UPDATE oqituvchi_kutubxona_hujjatlar h SET qator_id=NULL
                           WHERE user_id=%s AND qator_id IS NOT NULL AND NOT EXISTS
                           (SELECT 1 FROM oqituvchi_kutubxona_qatorlar q WHERE q.id=h.qator_id AND q.polka_id=h.polka_id)""", (uid,))
            return {"joylandi": len(moved)}
        return run(token, fn)

    def found_docs(cur, uid, text):
        opts = settings(cur, uid)
        if opts["matn_oqish"]:   # ruxsatdan keyin hali o'qilmagan hujjatlar — har so'rovda ozgina
            cur.execute("SELECT id,fayl_nomi,tarkib FROM oqituvchi_kutubxona_hujjatlar WHERE user_id=%s AND matn IS NULL ORDER BY id DESC LIMIT 4", (uid,))
            for r in cur.fetchall():
                cur.execute("UPDATE oqituvchi_kutubxona_hujjatlar SET matn=%s WHERE id=%s",
                            (S.extract_text(r["fayl_nomi"], bytes(r["tarkib"])) or "", r["id"]))
        docs = all_docs(cur, uid, with_text=opts["matn_oqish"])
        for d in docs:
            d["teglar"] = list(d.get("teglar") or [])
            d["yaratilgan"] = d["yaratilgan"].isoformat() if d.get("yaratilgan") else ""
        return opts, docs

    def finish(result, _words=None):
        keep = ("id", "nomi", "fayl_nomi", "hajm", "polka_id", "qator_id", "polka", "qator", "teglar", "izoh", "yaratilgan")
        result["hujjatlar"] = [{**{k: d.get(k) for k in keep}, "turi": S.kind_of(d.get("fayl_nomi")) or "boshqa",
                                "ball": d.get("ball"), "topildi": d.get("topildi", []), "parcha": d.get("parcha", "")}
                               for d in result.get("hujjatlar") or []]
        return result

    @router.get("/qidiruv")
    def find(token: str, q: str = ""):
        def fn(cur, uid):
            _opts, docs = found_docs(cur, uid, q)
            parsed, res = S.search(q, docs, limit=30)
            return finish({"hujjatlar": res, "sorov": parsed}, parsed["sozlar"])
        return run(token, fn)

    @router.post("/yordamchi")
    def assistant(token: str, body: AskIn):
        message = str(body.xabar or "")[:500]

        def fn(cur, uid):
            opts, docs = found_docs(cur, uid, message)
            return opts, docs, shelf_names(cur, uid)
        opts, docs, shelves = run(token, fn)
        result = S.assistant_reply(message, docs, can_read_text=opts["matn_oqish"])
        used_ai = False
        if result["turi"] == "savol" and docs and S.parse_query(message)["sozlar"]:
            words = ai(message, shelves)
            if words:
                retry = S.assistant_reply(message, docs, can_read_text=opts["matn_oqish"], extra_words=words)
                if retry["hujjatlar"]:
                    result, used_ai = retry, True
        result["ai"] = used_ai
        return finish(result, S.parse_query(message)["sozlar"])

    return router

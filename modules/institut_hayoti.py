"""REV79: institut hayoti — admin uchun talabalar (kurs → guruh → talaba) va institut sahifasi
(muqova rasmi, tavsif, muhim sanalar); talaba uchun «Mening institutim / Mening guruhim».

Manba: talaba_profillari (talaba institutni tanlab, parol bilan qo'shilganda yoziladi).
Rasmlar bazada (BYTEA) saqlanadi — Railway diski doimiy emas.
"""
from datetime import date

import psycopg2
from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response

MAX_IMAGE = 5 * 1024 * 1024
IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
SANA_TURLARI = {
    "tadbir": "Tadbir",
    "imtihon": "Imtihon / sessiya",
    "tatil": "Ta'til",
    "yangilik": "Yangilik",
    "muhim": "Muhim sana",
}
MAX_TEXT = 4000


def _t(value, limit=None):
    text = str(value or "").strip()
    return text[:limit] if limit else text


def _date(value, required=False):
    text = _t(value)
    if not text:
        if required:
            raise HTTPException(422, "Sanani kiriting")
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        raise HTTPException(422, "Sana YYYY-MM-DD ko'rinishida bo'lsin")


def _kurs(value):
    text = _t(value)
    if not text or text in ("0", "hammasi", "all"):
        return None
    try:
        kurs = int(text)
    except ValueError:
        raise HTTPException(422, "Kurs 1–6 oralig'ida bo'lsin")
    if not 1 <= kurs <= 6:
        raise HTTPException(422, "Kurs 1–6 oralig'ida bo'lsin")
    return kurs


async def _image(upload):
    if upload is None or not getattr(upload, "filename", ""):
        return None, None
    data = await upload.read(MAX_IMAGE + 1)
    if len(data) > MAX_IMAGE:
        raise HTTPException(413, "Rasm 5 MB dan katta bo'lmasin")
    kind = (upload.content_type or "").lower()
    if kind == "image/jpg":
        kind = "image/jpeg"
    if kind not in IMAGE_TYPES:
        raise HTTPException(415, "Faqat PNG, JPG yoki WEBP rasm")
    return data, kind


def migrate(cur):
    cur.execute("ALTER TABLE universitetlar ADD COLUMN IF NOT EXISTS hayot_tavsif TEXT")
    cur.execute("ALTER TABLE universitetlar ADD COLUMN IF NOT EXISTS muqova_rasm BYTEA")
    cur.execute("ALTER TABLE universitetlar ADD COLUMN IF NOT EXISTS muqova_turi TEXT")
    cur.execute("ALTER TABLE universitetlar ADD COLUMN IF NOT EXISTS muqova_yangilangan TIMESTAMPTZ")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_muhim_sanalar(
        id BIGSERIAL PRIMARY KEY,
        universitet_id INTEGER NOT NULL REFERENCES universitetlar(id) ON DELETE CASCADE,
        sarlavha TEXT NOT NULL,
        matn TEXT NOT NULL DEFAULT '',
        sana DATE NOT NULL,
        tugash_sana DATE,
        turi TEXT NOT NULL DEFAULT 'muhim',
        kurs SMALLINT CHECK(kurs IS NULL OR kurs BETWEEN 1 AND 6),
        rasm BYTEA,
        rasm_turi TEXT,
        yaratgan_user_id BIGINT,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_universitet_muhim_sanalar ON universitet_muhim_sanalar(universitet_id, sana)")


def group_students(rows):
    """[{kurs, guruh, ...}] → kurslar: [{kurs, soni, guruhlar:[{guruh, soni, talabalar}]}] (1-kursdan boshlab)."""
    courses = {}
    for row in rows:
        kurs = int(row.get("kurs") or 0)
        guruh = _t(row.get("guruh")) or "Guruhsiz"
        course = courses.setdefault(kurs, {"kurs": kurs, "soni": 0, "guruhlar": {}})
        course["soni"] += 1
        group = course["guruhlar"].setdefault(guruh.upper(), {"guruh": guruh, "soni": 0, "talabalar": []})
        group["soni"] += 1
        group["talabalar"].append(row)
    result = []
    for kurs in sorted(courses):
        course = courses[kurs]
        groups = sorted(course["guruhlar"].values(), key=lambda g: (g["guruh"] == "Guruhsiz", g["guruh"].lower()))
        for group in groups:
            group["talabalar"].sort(key=lambda r: _t(r.get("full_name")).lower())
        result.append({"kurs": kurs, "soni": course["soni"], "guruhlar": groups})
    return result


def sort_dates(rows, today=None):
    """Yaqinlashayotganlar (bugundan keyin) oldin — sanasi bo'yicha; o'tganlar oxirida, yangisi oldin."""
    today = today or date.today()

    def end(row):
        return row.get("tugash_sana") or row.get("sana")

    upcoming = [r for r in rows if end(r) and end(r) >= today]
    past = [r for r in rows if not (end(r) and end(r) >= today)]
    upcoming.sort(key=lambda r: (r["sana"], r.get("id") or 0))
    past.sort(key=lambda r: (r.get("sana") or date.min), reverse=True)
    for row in upcoming:
        row["qolgan_kun"] = max(0, (row["sana"] - today).days)
        row["otgan"] = False
    for row in past:
        row["qolgan_kun"] = None
        row["otgan"] = True
    return upcoming + past


def _date_row(row):
    item = {k: row.get(k) for k in ("id", "universitet_id", "sarlavha", "matn", "sana", "tugash_sana", "turi", "kurs", "yangilangan_at")}
    item["turi_nomi"] = SANA_TURLARI.get(item["turi"], "Muhim sana")
    item["rasm_bor"] = bool(row.get("rasm_bor"))
    return item


def create_router(platform):
    router = APIRouter()

    def _uid(token, authorization):
        return platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization))

    def _conn():
        conn = platform._db()
        cur = conn.cursor()
        platform._universitet_jadvali(cur)
        migrate(cur)
        return conn, cur

    def _manager(cur, user_id, universitet_id):
        cur.execute("SELECT id, nomi, rektor_user_id FROM universitetlar WHERE id=%s", (universitet_id,))
        uni = cur.fetchone()
        if not uni:
            raise HTTPException(404, "Institut topilmadi")
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
        if cur.fetchone() or (uni.get("rektor_user_id") is not None and int(uni["rektor_user_id"]) == int(user_id)):
            return uni
        raise HTTPException(403, "Faqat admin yoki institut rahbari uchun")

    def _dates(cur, universitet_id, kurs=None, with_all=True):
        sql = """SELECT id, universitet_id, sarlavha, matn, sana, tugash_sana, turi, kurs, yangilangan_at,
                        (rasm IS NOT NULL) AS rasm_bor
                 FROM universitet_muhim_sanalar WHERE universitet_id=%s"""
        params = [universitet_id]
        if not with_all:
            sql += " AND (kurs IS NULL OR kurs=%s)"
            params.append(kurs)
        cur.execute(sql + " ORDER BY sana", params)
        return sort_dates([_date_row(r) for r in cur.fetchall()])

    # ── Admin: talabalar kurs → guruh → talaba ──
    @router.get("/api/institut_hayoti/admin/{universitet_id}/talabalar")
    def admin_students(universitet_id: int, token: str = None, authorization: str = Header(None)):
        user_id = _uid(token, authorization)
        conn, cur = _conn()
        try:
            uni = _manager(cur, user_id, universitet_id)
            cur.execute("""SELECT p.user_id, u.full_name, u.kabutar_id, p.kurs, p.guruh, p.yonalish_nomi,
                                  p.talim_bosqichi, p.talim_shakli, p.talim_tili, p.semestr, p.qoshilgan_at
                           FROM talaba_profillari p JOIN users u ON u.user_id=p.user_id
                           WHERE p.universitet_id=%s""", (universitet_id,))
            rows = cur.fetchall()
            conn.commit()
            return {"universitet": {"id": uni["id"], "nomi": uni["nomi"]}, "jami": len(rows),
                    "kurslar": group_students([dict(r) for r in rows])}
        finally:
            cur.close()
            conn.close()

    # ── Admin: institut sahifasi (muqova, tavsif, muhim sanalar) ──
    @router.get("/api/institut_hayoti/admin/{universitet_id}")
    def admin_page(universitet_id: int, token: str = None, authorization: str = Header(None)):
        user_id = _uid(token, authorization)
        conn, cur = _conn()
        try:
            uni = _manager(cur, user_id, universitet_id)
            cur.execute("""SELECT hayot_tavsif, (muqova_rasm IS NOT NULL) AS muqova_bor, muqova_yangilangan,
                                  (SELECT COUNT(*) FROM talaba_profillari tp WHERE tp.universitet_id=u.id) AS talaba_soni
                           FROM universitetlar u WHERE id=%s""", (universitet_id,))
            info = cur.fetchone() or {}
            sanalar = _dates(cur, universitet_id)
            conn.commit()
            return {"universitet": {"id": uni["id"], "nomi": uni["nomi"], "tavsif": info.get("hayot_tavsif") or "",
                                    "muqova_bor": bool(info.get("muqova_bor")), "muqova_yangilangan": info.get("muqova_yangilangan"),
                                    "talaba_soni": int(info.get("talaba_soni") or 0)},
                    "sanalar": sanalar, "turlar": SANA_TURLARI}
        finally:
            cur.close()
            conn.close()

    @router.post("/api/institut_hayoti/admin/{universitet_id}/sahifa")
    async def admin_page_save(universitet_id: int, token: str = Form(None), tavsif: str = Form(""),
                              rasm_ochir: bool = Form(False), rasm: UploadFile = File(None),
                              authorization: str = Header(None)):
        user_id = _uid(token, authorization)
        data, kind = await _image(rasm)
        conn, cur = _conn()
        try:
            _manager(cur, user_id, universitet_id)
            cur.execute("UPDATE universitetlar SET hayot_tavsif=%s WHERE id=%s", (_t(tavsif, MAX_TEXT), universitet_id))
            if data:
                cur.execute("UPDATE universitetlar SET muqova_rasm=%s, muqova_turi=%s, muqova_yangilangan=NOW() WHERE id=%s",
                            (psycopg2.Binary(data), kind, universitet_id))
            elif rasm_ochir:
                cur.execute("UPDATE universitetlar SET muqova_rasm=NULL, muqova_turi=NULL, muqova_yangilangan=NOW() WHERE id=%s", (universitet_id,))
            conn.commit()
            return {"ok": True}
        finally:
            cur.close()
            conn.close()

    @router.post("/api/institut_hayoti/admin/{universitet_id}/sana")
    async def admin_date_save(universitet_id: int, token: str = Form(None), sarlavha: str = Form(...),
                              sana: str = Form(...), matn: str = Form(""), tugash_sana: str = Form(""),
                              turi: str = Form("muhim"), kurs: str = Form(""), sana_id: str = Form(""),
                              rasm_ochir: bool = Form(False), rasm: UploadFile = File(None),
                              authorization: str = Header(None)):
        user_id = _uid(token, authorization)
        title = _t(sarlavha, 200)
        if not title:
            raise HTTPException(422, "Sarlavhani yozing")
        start, end = _date(sana, required=True), _date(tugash_sana)
        if end and end < start:
            raise HTTPException(422, "Tugash sanasi boshlanishdan oldin bo'lmasin")
        kind_key = turi if turi in SANA_TURLARI else "muhim"
        course = _kurs(kurs)
        data, kind = await _image(rasm)
        conn, cur = _conn()
        try:
            _manager(cur, user_id, universitet_id)
            if _t(sana_id):
                cur.execute("""UPDATE universitet_muhim_sanalar SET sarlavha=%s, matn=%s, sana=%s, tugash_sana=%s, turi=%s,
                               kurs=%s, yangilangan_at=NOW() WHERE id=%s AND universitet_id=%s RETURNING id""",
                            (title, _t(matn, MAX_TEXT), start, end, kind_key, course, int(sana_id), universitet_id))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(404, "Sana topilmadi")
                new_id = row["id"]
            else:
                cur.execute("""INSERT INTO universitet_muhim_sanalar(universitet_id,sarlavha,matn,sana,tugash_sana,turi,kurs,yaratgan_user_id)
                               VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                            (universitet_id, title, _t(matn, MAX_TEXT), start, end, kind_key, course, user_id))
                new_id = cur.fetchone()["id"]
            if data:
                cur.execute("UPDATE universitet_muhim_sanalar SET rasm=%s, rasm_turi=%s WHERE id=%s", (psycopg2.Binary(data), kind, new_id))
            elif rasm_ochir:
                cur.execute("UPDATE universitet_muhim_sanalar SET rasm=NULL, rasm_turi=NULL WHERE id=%s", (new_id,))
            conn.commit()
            return {"ok": True, "id": new_id}
        finally:
            cur.close()
            conn.close()

    @router.delete("/api/institut_hayoti/admin/sana/{sana_id}")
    def admin_date_delete(sana_id: int, token: str = None, authorization: str = Header(None)):
        user_id = _uid(token, authorization)
        conn, cur = _conn()
        try:
            cur.execute("SELECT universitet_id FROM universitet_muhim_sanalar WHERE id=%s", (sana_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Sana topilmadi")
            _manager(cur, user_id, row["universitet_id"])
            cur.execute("DELETE FROM universitet_muhim_sanalar WHERE id=%s", (sana_id,))
            conn.commit()
            return {"ok": True}
        finally:
            cur.close()
            conn.close()

    # ── Rasmlar (ism kabi ochiq ma'lumot; <img> token yubora olmaydi) ──
    @router.get("/api/institut_hayoti/rasm/sana/{sana_id}")
    def date_image(sana_id: int):
        conn, cur = _conn()
        try:
            cur.execute("SELECT rasm, rasm_turi FROM universitet_muhim_sanalar WHERE id=%s", (sana_id,))
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()
        if not row or not row["rasm"]:
            raise HTTPException(404, "Rasm topilmadi")
        return Response(bytes(row["rasm"]), media_type=row["rasm_turi"] or "image/jpeg", headers={"Cache-Control": "public, max-age=300"})

    @router.get("/api/institut_hayoti/rasm/muqova/{universitet_id}")
    def cover_image(universitet_id: int):
        conn, cur = _conn()
        try:
            cur.execute("SELECT muqova_rasm, muqova_turi FROM universitetlar WHERE id=%s", (universitet_id,))
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()
        if not row or not row["muqova_rasm"]:
            raise HTTPException(404, "Rasm topilmadi")
        return Response(bytes(row["muqova_rasm"]), media_type=row["muqova_turi"] or "image/jpeg", headers={"Cache-Control": "public, max-age=300"})

    # ── Talaba: Mening institutim / Mening guruhim ──
    @router.get("/api/institut_hayoti/mening")
    def my_institute(token: str = None, authorization: str = Header(None)):
        user_id = _uid(token, authorization)
        conn, cur = _conn()
        try:
            cur.execute("""SELECT p.*, u.nomi AS universitet_nomi, u.hayot_tavsif, (u.muqova_rasm IS NOT NULL) AS muqova_bor,
                                  u.muqova_yangilangan
                           FROM talaba_profillari p JOIN universitetlar u ON u.id=p.universitet_id WHERE p.user_id=%s""", (user_id,))
            me = cur.fetchone()
            if not me:
                conn.commit()
                return {"ulangan": False}
            uni_id, kurs, guruh = me["universitet_id"], me["kurs"], _t(me["guruh"])
            cur.execute("""SELECT p.user_id, u.full_name, (u.user_id=%s) AS menman
                           FROM talaba_profillari p JOIN users u ON u.user_id=p.user_id
                           WHERE p.universitet_id=%s AND p.kurs=%s AND UPPER(TRIM(p.guruh))=UPPER(%s)
                           ORDER BY LOWER(u.full_name)""", (user_id, uni_id, kurs, guruh))
            groupmates = [dict(r) for r in cur.fetchall()]
            cur.execute("""SELECT COUNT(*) AS kursdosh, COUNT(DISTINCT UPPER(TRIM(guruh))) AS guruh_soni
                           FROM talaba_profillari WHERE universitet_id=%s AND kurs=%s""", (uni_id, kurs))
            course = cur.fetchone() or {}
            cur.execute("SELECT COUNT(*) AS n FROM talaba_profillari WHERE universitet_id=%s", (uni_id,))
            total = (cur.fetchone() or {}).get("n") or 0
            sanalar = _dates(cur, uni_id, kurs, with_all=False)
            conn.commit()
            return {
                "ulangan": True,
                "universitet": {"id": uni_id, "nomi": me["universitet_nomi"], "tavsif": me.get("hayot_tavsif") or "",
                                "muqova_bor": bool(me.get("muqova_bor")), "muqova_yangilangan": me.get("muqova_yangilangan"),
                                "talaba_soni": int(total)},
                "men": {"kurs": kurs, "guruh": guruh, "yonalish_nomi": me.get("yonalish_nomi"),
                        "talim_bosqichi": me.get("talim_bosqichi"), "talim_shakli": me.get("talim_shakli"),
                        "semestr": me.get("semestr"), "qoshilgan_at": me.get("qoshilgan_at")},
                "guruhdoshlar": groupmates,
                "kurs": {"talaba_soni": int(course.get("kursdosh") or 0), "guruh_soni": int(course.get("guruh_soni") or 0)},
                "sanalar": sanalar,
            }
        finally:
            cur.close()
            conn.close()

    return router

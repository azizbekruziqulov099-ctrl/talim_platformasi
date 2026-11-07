"""REV364: bog'cha darslarini admin o'zi ko'rib tuzatadi.
1) O'yin sozlamasi — har o'yinga holat (✅ yoqilgan / 🛠 tuzatish kerak / ⛔ o'chirilgan) va izoh; o'chirilgan o'yin bolalarga chiqmaydi.
2) Dars muharriri — har darsning qadamlari (qaysi o'yin, ustoz gapi, doska yozuvi, test variantlari) ko'rinadi va tahrirlanadi;
   har o'zgarish jurnalga yoziladi va Excel'ga eksport qilinadi (boshqa tillarni shu asosda tuzatish uchun)."""
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional

# Tahrirlash mumkin bo'lgan maydonlar (Miya ustunlari bilan bir xil nomlar)
QADAM_MAYDON = {"sarlavha": "Sarlavha", "ovoz_matni": "Ustoz gapi", "doska_matni": "Doska", "oyin": "O'yin №", "variantlar": "Variantlar",
                "togri_javob": "To'g'ri javob", "oquvchi_savoli": "O'quvchiga savol", "kutilgan_javob": "Kutilgan javob"}
TOPSHIRIQ_MAYDON = {"savol": "Savol", "variant_a": "A", "variant_b": "B", "variant_c": "C", "variant_d": "D", "togri_javob": "To'g'ri javob", "izoh": "Izoh"}
HOLATLAR = ("ok", "tuzat", "yopiq")


_TAYYOR = {"ok": False}


def migrate(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS oyin_sozlama (oyin_id INT PRIMARY KEY, holat TEXT NOT NULL DEFAULT 'ok', izoh TEXT NOT NULL DEFAULT '',
        kim BIGINT, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS miya_tahrir_log (id BIGSERIAL PRIMARY KEY, unit_id BIGINT NOT NULL, topic_code TEXT NOT NULL, unit_code TEXT NOT NULL,
        maydon TEXT NOT NULL, eski TEXT, yangi TEXT, kim BIGINT, vaqt TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE INDEX IF NOT EXISTS miya_tahrir_log_topic ON miya_tahrir_log(topic_code, vaqt)")


def qadam_korinishi(r):
    p = r.get("payload") or {}
    if isinstance(p, str):
        p = json.loads(p or "{}")
    maydon = QADAM_MAYDON if r["unit_kind"] == "lesson_step" else TOPSHIRIQ_MAYDON
    return {"id": r["id"], "kod": r["unit_code"], "tur": r["unit_kind"], "qadam_turi": p.get("qadam_turi") or p.get("amaliy_turi") or ("test" if r["unit_kind"] == "task" else ""),
            "tartib": p.get("tartib") or 0, "maydonlar": {k: ("" if p.get(k) is None else str(p.get(k))) for k in maydon}}


def eksport_kitob(loglar, darslar):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    wb = Workbook(); ws = wb.active; ws.title = "O'ZGARISHLAR"
    bosh = ["Vaqt", "Sinf", "Fan", "Mavzu", "Qadam kodi", "Maydon", "Eski", "Yangi"]
    ws.append(bosh)
    for l in loglar:
        ws.append([str(l["vaqt"])[:16], l.get("sinf") or "", l.get("fan") or "", l.get("mavzu") or "", l["unit_code"], QADAM_MAYDON.get(l["maydon"]) or TOPSHIRIQ_MAYDON.get(l["maydon"]) or l["maydon"],
                   l.get("eski") or "", l.get("yangi") or ""])
    w2 = wb.create_sheet("DARSLAR")
    w2.append(["Mavzu", "Qadam kodi", "Turi", "Sarlavha", "Ustoz gapi", "Doska", "O'yin №", "Variantlar", "To'g'ri javob"])
    for d in darslar:
        for q in d["qadamlar"]:
            m = q["maydonlar"]
            w2.append([d["mavzu"], q["kod"], q["qadam_turi"], m.get("sarlavha", ""), m.get("ovoz_matni") or m.get("savol", ""), m.get("doska_matni", ""), m.get("oyin", ""),
                       m.get("variantlar") or " / ".join(x for x in (m.get("variant_a"), m.get("variant_b"), m.get("variant_c"), m.get("variant_d")) if x), m.get("togri_javob", "")])
    for w in (ws, w2):
        for c in w[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2B3452")
        for col, kenglik in zip("ABCDEFGHI", (16, 12, 14, 30, 22, 16, 40, 40, 14)):
            w.column_dimensions[col].width = kenglik
        for row in w.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


def create_router(platform):
    router = APIRouter()

    def db():
        conn = platform._db(); cur = conn.cursor()
        if not _TAYYOR["ok"]:   # REV414: bir marta
            migrate(cur); conn.commit(); _TAYYOR["ok"] = True
        return conn, cur

    # ── 1) o'yin sozlamasi ──
    @router.get("/api/oyin_sozlama")
    def oyin_sozlama():
        conn, cur = db()
        try:
            cur.execute("SELECT oyin_id, holat, izoh FROM oyin_sozlama")
            return {"oyinlar": {str(r["oyin_id"]): {"holat": r["holat"], "izoh": r["izoh"]} for r in cur.fetchall()}}
        finally:
            cur.close(); conn.close()

    class Sozlama(BaseModel):
        token: str
        oyin_id: int = Field(ge=1, le=400)
        holat: str = "ok"
        izoh: str = Field(default="", max_length=600)

    @router.post("/api/admin/oyin_sozlama")
    def oyin_sozlama_yoz(body: Sozlama):
        uid = platform._admin_tekshir(body.token)
        if body.holat not in HOLATLAR:
            raise HTTPException(400, "holat: ok | tuzat | yopiq")
        conn, cur = db()
        try:
            cur.execute("""INSERT INTO oyin_sozlama(oyin_id, holat, izoh, kim, yangilandi) VALUES(%s,%s,%s,%s,NOW())
                           ON CONFLICT (oyin_id) DO UPDATE SET holat=EXCLUDED.holat, izoh=EXCLUDED.izoh, kim=EXCLUDED.kim, yangilandi=NOW()""",
                        (body.oyin_id, body.holat, body.izoh.strip(), uid))
            conn.commit()
            return {"ok": True}
        finally:
            cur.close(); conn.close()

    # ── 2) dars muharriri ──
    @router.get("/api/admin/dars_tahrir/darslar")
    def darslar(token: str, sinf: str, fan: str):
        platform._admin_tekshir(token)
        conn, cur = db()
        try:
            cur.execute("""SELECT d.topic_code, COALESCE(d.mavzu_name, d.bolim_name, d.bob_name) AS mavzu,
                                  (SELECT COUNT(*) FROM ai_brain_units u WHERE u.topic_code=d.topic_code AND u.status='published') AS qadamlar,
                                  (SELECT COUNT(*) FROM miya_tahrir_log l WHERE l.topic_code=d.topic_code) AS tahrirlar
                           FROM dts_tree d WHERE d.is_deleted=FALSE AND TRIM(d.grade)=%s
                             AND UPPER(TRANSLATE(d.subject_name,'—–','--'))=UPPER(TRANSLATE(%s,'—–','--'))
                           ORDER BY d.topic_code""", (sinf.strip(), fan.strip()))
            return {"darslar": [dict(r) for r in cur.fetchall() if r["qadamlar"]]}
        finally:
            cur.close(); conn.close()

    def dars_ol(cur, topic_code):
        cur.execute("""SELECT id, unit_code, unit_kind, payload FROM ai_brain_units WHERE topic_code=%s AND status='published'
                       AND unit_kind IN ('lesson_step','task') ORDER BY unit_kind DESC, id""", (topic_code,))
        q = [qadam_korinishi(r) for r in cur.fetchall()]
        q.sort(key=lambda x: (x["tur"] != "lesson_step", int(x["tartib"] or 0) if str(x["tartib"]).isdigit() else 0, x["id"]))
        return q

    @router.get("/api/admin/dars_tahrir/dars")
    def dars(token: str, topic_code: str):
        platform._admin_tekshir(token)
        conn, cur = db()
        try:
            return {"topic_code": topic_code, "qadamlar": dars_ol(cur, topic_code)}
        finally:
            cur.close(); conn.close()

    class Saqla(BaseModel):
        token: str
        unit_id: int
        maydonlar: dict

    @router.post("/api/admin/dars_tahrir/saqla")
    def saqla(body: Saqla):
        uid = platform._admin_tekshir(body.token)
        conn, cur = db()
        try:
            cur.execute("SELECT id, unit_code, unit_kind, topic_code, payload FROM ai_brain_units WHERE id=%s FOR UPDATE", (body.unit_id,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Qadam topilmadi")
            ruxsat = QADAM_MAYDON if r["unit_kind"] == "lesson_step" else TOPSHIRIQ_MAYDON
            p = r["payload"] or {}
            if isinstance(p, str):
                p = json.loads(p or "{}")
            ozgardi = 0
            for k, v in (body.maydonlar or {}).items():
                if k not in ruxsat:
                    continue
                yangi = str(v if v is not None else "").strip()
                if k == "oyin":
                    if yangi and not yangi.isdigit():
                        raise HTTPException(400, "O'yin raqami — butun son (masalan 116)")
                    yangi_q = int(yangi) if yangi else None
                else:
                    yangi_q = yangi
                eski = "" if p.get(k) is None else str(p.get(k))
                if eski == ("" if yangi_q is None else str(yangi_q)):
                    continue
                p[k] = yangi_q
                cur.execute("""INSERT INTO miya_tahrir_log(unit_id, topic_code, unit_code, maydon, eski, yangi, kim) VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                            (r["id"], r["topic_code"], r["unit_code"], k, eski, "" if yangi_q is None else str(yangi_q), uid))
                ozgardi += 1
            if ozgardi:
                cur.execute("UPDATE ai_brain_units SET payload=%s::jsonb WHERE id=%s", (json.dumps(p, ensure_ascii=False), r["id"]))
            conn.commit()
            try:
                platform._dars_kesh_tozala(r["topic_code"])   # bo'lsa — darsning keshi darhol yangilanadi
            except Exception:
                pass
            return {"ok": True, "ozgardi": ozgardi}
        finally:
            cur.close(); conn.close()

    @router.get("/api/admin/dars_tahrir/eksport")
    def eksport(token: str, sinf: str = "", fan: str = ""):
        platform._admin_tekshir(token)
        conn, cur = db()
        try:
            cur.execute("""SELECT l.*, d.grade AS sinf, d.subject_name AS fan, COALESCE(d.mavzu_name, d.bolim_name) AS mavzu
                           FROM miya_tahrir_log l LEFT JOIN dts_tree d ON d.topic_code=l.topic_code
                           WHERE (%s='' OR TRIM(d.grade)=%s) AND (%s='' OR UPPER(TRANSLATE(d.subject_name,'—–','--'))=UPPER(TRANSLATE(%s,'—–','--')))
                           ORDER BY l.topic_code, l.vaqt""", (sinf.strip(), sinf.strip(), fan.strip(), fan.strip()))
            loglar = [dict(x) for x in cur.fetchall()]
            mavzular = list(dict.fromkeys(l["topic_code"] for l in loglar))
            darslar_ = []
            for t in mavzular[:200]:
                darslar_.append({"mavzu": next((l["mavzu"] for l in loglar if l["topic_code"] == t), t) or t, "qadamlar": dars_ol(cur, t)})
            data = eksport_kitob(loglar, darslar_)
            nom = f"Dars_tahrirlari_{(sinf or 'hammasi').replace(' ', '_')}_{(fan or 'hammasi').replace(' ', '_')}_{datetime.now(timezone.utc):%Y%m%d}.xlsx"
            from urllib.parse import quote
            return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nom)}"})
        finally:
            cur.close(); conn.close()

    return router

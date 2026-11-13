"""REV543: «Kabu loyiha» portfeli serverda + qo'lda yasash (F3).
  • Ekrandagi loyiha natijasi serverga yoziladi (eng yaxshi yulduz saqlanadi) — qurilma almashsa ham yo'qolmaydi.
  • Qo'lda yasash: bola yasagan narsasining rasmini yuklaydi (kichik JPEG, bulutli omborga) → ota-ona yoki o'qituvchi tasdiqlaydi.
  • Ota-ona o'z farzandlari, o'qituvchi o'z guruhidagi o'quvchilar portfelini ko'radi."""
import base64
import re
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

LOYIHALAR = {"osimlik", "koprik", "kod", "naqsh", "byudjet", "filtr", "richag", "parashyut", "qayiq", "soya", "qiya", "masshtab", "sorov", "rang", "kod2"}
RASM_MAX = 600_000


def jadval(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS loyiha_natija (user_id BIGINT NOT NULL, loyiha TEXT NOT NULL, yulduz INT NOT NULL DEFAULT 0, urinish INT NOT NULL DEFAULT 0,
        faraz BOOLEAN NOT NULL DEFAULT FALSE, xulosa BOOLEAN NOT NULL DEFAULT FALSE, maqsad BOOLEAN NOT NULL DEFAULT FALSE, soni INT NOT NULL DEFAULT 1,
        yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, loyiha))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS loyiha_qolda (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, loyiha TEXT NOT NULL, s3_kalit TEXT NOT NULL, izoh TEXT NOT NULL DEFAULT '',
        holat TEXT NOT NULL DEFAULT 'kutadi', tasdiqlagan BIGINT, izoh_tasdiq TEXT NOT NULL DEFAULT '', yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW(), hal_qilindi TIMESTAMPTZ)""")
    cur.execute("CREATE INDEX IF NOT EXISTS loyiha_qolda_u ON loyiha_qolda(user_id, yaratildi DESC)")


class Natija(BaseModel):
    token: Optional[str] = None
    loyiha: str
    yulduz: int = Field(ge=0, le=3)
    urinish: int = Field(default=0, ge=0, le=500)
    faraz: bool = False
    xulosa: bool = False
    maqsad: bool = False


class Qolda(BaseModel):
    token: Optional[str] = None
    loyiha: str
    rasm: str
    izoh: str = Field(default="", max_length=400)


class Tasdiq(BaseModel):
    token: Optional[str] = None
    qabul: bool
    izoh: str = Field(default="", max_length=300)


def create_router(platform):
    router = APIRouter(tags=["loyiha_portfel"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            jadval(cur); r = fn(cur); conn.commit(); return r
        finally:
            cur.close(); conn.close()

    def ota_mi(cur, ota, bola):
        try:
            from modules.bogcha_reja import ota_bolami
            return bool(ota_bolami(cur, ota, bola))
        except Exception:   # noqa: BLE001
            return False

    def oqituvchi_mi(cur, ustoz, bola):
        cur.execute("""SELECT 1 FROM kurs_guruh g JOIN kurs_guruh_azo a ON a.guruh_id=g.id WHERE g.egasi=%s AND a.user_id=%s AND g.faol LIMIT 1""", (ustoz, bola))
        return cur.fetchone() is not None

    def admin_mi(cur, u):
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (u,))
        return cur.fetchone() is not None

    def kim_koradi(cur, u, egasi):
        return u == egasi or ota_mi(cur, u, egasi) or oqituvchi_mi(cur, u, egasi) or admin_mi(cur, u)

    @router.post("/api/loyiha/natija")
    def natija_yoz(body: Natija, authorization: Optional[str] = Header(None)):
        """Ekrandagi loyiha tugadi. Eng yaxshi natija saqlanadi; urinishlar soni oshadi."""
        u = uid(body.token, authorization)
        if body.loyiha not in LOYIHALAR:
            raise HTTPException(400, "Noma'lum loyiha")
        def f(cur):
            cur.execute("""INSERT INTO loyiha_natija(user_id, loyiha, yulduz, urinish, faraz, xulosa, maqsad) VALUES(%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (user_id, loyiha) DO UPDATE SET soni = loyiha_natija.soni + 1, yangilandi = NOW(),
                             yulduz = GREATEST(loyiha_natija.yulduz, EXCLUDED.yulduz),
                             urinish = CASE WHEN EXCLUDED.yulduz > loyiha_natija.yulduz THEN EXCLUDED.urinish ELSE loyiha_natija.urinish END,
                             faraz = loyiha_natija.faraz OR EXCLUDED.faraz, xulosa = loyiha_natija.xulosa OR EXCLUDED.xulosa, maqsad = loyiha_natija.maqsad OR EXCLUDED.maqsad
                           RETURNING yulduz, soni""", (u, body.loyiha, body.yulduz, body.urinish, body.faraz, body.xulosa, body.maqsad))
            r = cur.fetchone()
            return {"ok": True, "yulduz": r["yulduz"], "soni": r["soni"]}
        return run(f)

    def portfel_ol(cur, egasi):
        cur.execute("SELECT loyiha, yulduz, urinish, faraz, xulosa, maqsad, soni, yangilandi FROM loyiha_natija WHERE user_id=%s", (egasi,))
        ekran = {r["loyiha"]: {"yulduz": r["yulduz"], "urinish": r["urinish"], "faraz": r["faraz"], "xulosa": r["xulosa"], "maqsad": r["maqsad"], "soni": r["soni"],
                               "vaqt": r["yangilandi"].isoformat() if r["yangilandi"] else None} for r in cur.fetchall()}
        cur.execute("SELECT id, loyiha, izoh, holat, izoh_tasdiq, yaratildi FROM loyiha_qolda WHERE user_id=%s ORDER BY id DESC LIMIT 60", (egasi,))
        qolda = [{"id": r["id"], "loyiha": r["loyiha"], "izoh": r["izoh"], "holat": r["holat"], "tasdiq_izoh": r["izoh_tasdiq"], "vaqt": r["yaratildi"].isoformat()} for r in cur.fetchall()]
        return {"ekran": ekran, "qolda": qolda, "yulduz": sum(x["yulduz"] for x in ekran.values()) + 2 * sum(1 for q in qolda if q["holat"] == "tasdiqlandi")}

    @router.get("/api/loyiha/portfel")
    def portfel(oquvchi_id: int = 0, token: str = "", authorization: Optional[str] = Header(None)):
        """O'quvchi o'z portfelini; ota-ona farzandini; o'qituvchi guruh a'zosini ko'radi."""
        u = uid(token, authorization)
        def f(cur):
            egasi = oquvchi_id or u
            if not kim_koradi(cur, u, egasi):
                raise HTTPException(403, "Bu portfelni ko'rish huquqingiz yo'q")
            return portfel_ol(cur, egasi)
        return run(f)

    @router.post("/api/loyiha/qolda")
    def qolda_yubor(body: Qolda, authorization: Optional[str] = Header(None)):
        """Bola qo'lda yasagan narsasining rasmini yuboradi (kichik JPEG). Ota-ona yoki o'qituvchi tasdiqlaydi."""
        from modules import ombor
        u = uid(body.token, authorization)
        if body.loyiha not in LOYIHALAR:
            raise HTTPException(400, "Noma'lum loyiha")
        if not ombor.yoqilgan():
            raise HTTPException(503, "Rasm ombori hozircha ishlamayapti")
        try:
            data = base64.b64decode(body.rasm.split(",", 1)[-1], validate=True)
        except Exception:   # noqa: BLE001
            raise HTTPException(400, "Rasm noto'g'ri")
        if len(data) > RASM_MAX or not data.startswith(b"\xff\xd8"):
            raise HTTPException(400, "Faqat JPEG rasm, 600 KB gacha")
        def f(cur):
            cur.execute("SELECT COUNT(*) AS n FROM loyiha_qolda WHERE user_id=%s AND yaratildi > NOW() - INTERVAL '1 day'", (u,))
            if int(cur.fetchone()["n"]) >= 8:
                raise HTTPException(429, "Bugun juda ko'p rasm yuborildi — ertaga davom eting")
            k = f"loyiha/{u}/{body.loyiha}/{int(time.time() * 1000)}.jpg"
            if not ombor.yukla_bayt(k, data, "image/jpeg"):
                raise HTTPException(502, "Rasm saqlanmadi — qayta urinib ko'ring")
            cur.execute("INSERT INTO loyiha_qolda(user_id, loyiha, s3_kalit, izoh) VALUES(%s,%s,%s,%s) RETURNING id", (u, body.loyiha, k, body.izoh.strip()))
            return {"ok": True, "id": cur.fetchone()["id"], "holat": "kutadi"}
        return run(f)

    @router.get("/api/loyiha/kutayotgan")
    def kutayotgan(token: str = "", authorization: Optional[str] = Header(None)):
        """Tasdiq kutayotgan rasmlar: ota-onaga — farzandlariniki, o'qituvchiga — guruh o'quvchilariniki."""
        u = uid(token, authorization)
        def f(cur):
            cur.execute("""SELECT q.id, q.user_id, q.loyiha, q.izoh, q.yaratildi FROM loyiha_qolda q WHERE q.holat='kutadi' ORDER BY q.id DESC LIMIT 200""")
            out = []
            for r in cur.fetchall():
                if r["user_id"] != u and (ota_mi(cur, u, r["user_id"]) or oqituvchi_mi(cur, u, r["user_id"])):
                    cur.execute("SELECT COALESCE(NULLIF(TRIM(full_name),''), 'O‘quvchi') AS ism FROM users WHERE user_id=%s", (r["user_id"],))
                    x = cur.fetchone() or {}
                    out.append({"id": r["id"], "oquvchi_id": r["user_id"], "ism": x.get("ism") or "O‘quvchi", "loyiha": r["loyiha"], "izoh": r["izoh"], "vaqt": r["yaratildi"].isoformat()})
            return {"royxat": out[:50]}
        return run(f)

    @router.get("/api/loyiha/rasm/{rid}")
    def rasm_havola(rid: int, token: str = "", authorization: Optional[str] = Header(None)):
        """Rasm uchun qisqa muddatli havola — faqat egasi, ota-onasi, o'qituvchisi va admin."""
        from modules import ombor
        u = uid(token, authorization)
        def f(cur):
            cur.execute("SELECT user_id, s3_kalit FROM loyiha_qolda WHERE id=%s", (rid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Rasm topilmadi")
            if not kim_koradi(cur, u, int(r["user_id"])):
                raise HTTPException(403, "Ruxsat yo'q")
            return {"url": ombor.havola(r["s3_kalit"], muddat=600)}
        return run(f)

    @router.post("/api/loyiha/qolda/{rid}/tasdiq")
    def tasdiqla(rid: int, body: Tasdiq, authorization: Optional[str] = Header(None)):
        """Ota-ona yoki o'qituvchi rasmni tasdiqlaydi yoki «qayta urinib ko'ring» deydi. O'quvchining o'zi tasdiqlay olmaydi."""
        u = uid(body.token, authorization)
        def f(cur):
            cur.execute("SELECT user_id, holat FROM loyiha_qolda WHERE id=%s", (rid,))
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, "Topilmadi")
            egasi = int(r["user_id"])
            if u == egasi or not (ota_mi(cur, u, egasi) or oqituvchi_mi(cur, u, egasi) or admin_mi(cur, u)):
                raise HTTPException(403, "Tasdiqlash faqat ota-ona yoki o'qituvchi uchun")
            if r["holat"] != "kutadi":
                return {"ok": True, "holat": r["holat"]}
            holat = "tasdiqlandi" if body.qabul else "qaytarildi"
            cur.execute("UPDATE loyiha_qolda SET holat=%s, tasdiqlagan=%s, izoh_tasdiq=%s, hal_qilindi=NOW() WHERE id=%s", (holat, u, body.izoh.strip(), rid))
            return {"ok": True, "holat": holat}
        return run(f)

    @router.get("/api/loyiha/sinf")
    def sinf_hisobot(token: str = "", authorization: Optional[str] = Header(None)):
        """O'qituvchi uchun: guruhlaridagi o'quvchilar — nechta loyiha, yulduz, tasdiq kutayotgan rasmlar."""
        u = uid(token, authorization)
        def f(cur):
            cur.execute("""SELECT g.id AS gid, g.nom, a.user_id FROM kurs_guruh g JOIN kurs_guruh_azo a ON a.guruh_id=g.id WHERE g.egasi=%s AND g.faol ORDER BY g.id""", (u,))
            qator = cur.fetchall(); idlar = sorted({r["user_id"] for r in qator})
            if not idlar:
                return {"guruhlar": []}
            cur.execute("SELECT user_id, COUNT(*) AS n, COALESCE(SUM(yulduz),0) AS y FROM loyiha_natija WHERE user_id=ANY(%s) GROUP BY user_id", (idlar,))
            nat = {r["user_id"]: (int(r["n"]), int(r["y"])) for r in cur.fetchall()}
            cur.execute("SELECT user_id, COUNT(*) FILTER (WHERE holat='kutadi') AS k, COUNT(*) FILTER (WHERE holat='tasdiqlandi') AS t FROM loyiha_qolda WHERE user_id=ANY(%s) GROUP BY user_id", (idlar,))
            qol = {r["user_id"]: (int(r["k"]), int(r["t"])) for r in cur.fetchall()}
            cur.execute("SELECT user_id, COALESCE(NULLIF(TRIM(full_name),''), 'O‘quvchi') AS ism FROM users WHERE user_id=ANY(%s)", (idlar,))
            ism = {r["user_id"]: r["ism"] for r in cur.fetchall()}
            gl = {}
            for r in qator:
                n, y = nat.get(r["user_id"], (0, 0)); k, t = qol.get(r["user_id"], (0, 0))
                g = gl.setdefault(r["gid"], {"id": r["gid"], "nom": r["nom"], "oquvchilar": []})
                g["oquvchilar"].append({"id": r["user_id"], "ism": ism.get(r["user_id"], "O‘quvchi"), "loyihalar": n, "yulduz": y + 2 * t, "kutadi": k, "qolda": t})
            for g in gl.values():
                g["oquvchilar"].sort(key=lambda x: (-x["yulduz"], x["ism"]))
            return {"guruhlar": list(gl.values())}
        return run(f)

    return router

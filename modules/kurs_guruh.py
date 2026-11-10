"""REV411: Kurs guruhi — o'qituvchi kursdan guruh ochadi, havola yuboradi, «Bugungi mashg'ulot»ni tanlaydi;
talaba havola bilan qo'shiladi va to'g'ri o'sha darsga tushadi; har javob va jonli holat yoziladi,
o'qituvchi kim nechta masala/test yechganini har 3 soniyada ko'radi.
"""
import re
import secrets
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

KOD_HARF = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def kod_yasa(n=6):
    return "".join(secrets.choice(KOD_HARF) for _ in range(n))


def kod_norm(k):
    return re.sub(r"[^A-Za-z0-9]", "", str(k or "")).upper()[:12]


def holat_of(oldin, holat, jami, yechgan):
    """Jonli holat: tugatdi / yechmoqda / chiqdi / boshlamagan (sof qoida — testlanadi)."""
    if oldin is None:
        return "boshlamagan"
    if jami and yechgan >= jami:
        return "tugatdi"
    if holat == "chiqdi" or oldin > 25:   # REV414: ilova har 10 s da xabar beradi
        return "chiqdi"
    return "yechmoqda"


def migrate(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_guruh (id BIGSERIAL PRIMARY KEY, egasi BIGINT NOT NULL, fan TEXT NOT NULL, grade TEXT NOT NULL DEFAULT '',
        kurs_nomi TEXT NOT NULL DEFAULT '', nom TEXT NOT NULL, kod TEXT NOT NULL UNIQUE, faol BOOLEAN NOT NULL DEFAULT TRUE,
        bugungi TEXT NOT NULL DEFAULT '', bugungi_nom TEXT NOT NULL DEFAULT '', bugungi_vaqt TIMESTAMPTZ, yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_guruh_azo (guruh_id BIGINT NOT NULL REFERENCES kurs_guruh(id) ON DELETE CASCADE, user_id BIGINT NOT NULL,
        qoshildi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (guruh_id, user_id))""")
    cur.execute("ALTER TABLE kurs_guruh ADD COLUMN IF NOT EXISTS kamera BOOLEAN NOT NULL DEFAULT FALSE")   # REV483: o'qituvchi barcha nazoratlarga kamera yoqadi
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_dars_javob (user_id BIGINT NOT NULL, topic_code TEXT NOT NULL, item TEXT NOT NULL, turi TEXT NOT NULL DEFAULT '',
        togri BOOLEAN NOT NULL DEFAULT FALSE, urinish INT NOT NULL DEFAULT 1, vaqt TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, topic_code, item))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_dars_jonli (user_id BIGINT NOT NULL, topic_code TEXT NOT NULL, holat TEXT NOT NULL DEFAULT 'faol',
        boshladi TIMESTAMPTZ NOT NULL DEFAULT NOW(), yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, topic_code))""")


class GuruhYarat(BaseModel):
    token: Optional[str] = None
    fan: str = Field(..., max_length=160)
    grade: str = Field(default="", max_length=40)
    kurs_nomi: str = Field(default="", max_length=200)
    nom: str = Field(..., max_length=80)


class Bugungi(BaseModel):
    token: Optional[str] = None
    topic_code: str = Field(default="", max_length=80)
    nom: str = Field(default="", max_length=200)


class Qoshil(BaseModel):
    token: Optional[str] = None
    kod: str = Field(..., max_length=12)


class Javob(BaseModel):
    token: Optional[str] = None
    topic_code: str = Field(..., max_length=80)
    item: str = Field(..., max_length=60)
    turi: str = Field(default="", max_length=12)
    togri: bool = False


class Jonli(BaseModel):
    token: Optional[str] = None
    topic_code: str = Field(..., max_length=80)
    holat: str = Field(default="faol", max_length=10)


_TAYYOR = {"ok": False}


def create_router(platform):
    router = APIRouter(tags=["kurs_guruh"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            if not _TAYYOR["ok"]:   # REV414: jadvallar har so'rovda emas, jarayon boshida bir marta tekshiriladi
                migrate(cur); conn.commit(); _TAYYOR["ok"] = True
            out = fn(cur); conn.commit(); return out
        except Exception:
            conn.rollback(); raise
        finally:
            cur.close(); conn.close()

    def ozi(cur, gid, user_id):
        cur.execute("SELECT * FROM kurs_guruh WHERE id=%s AND faol", (gid,))
        g = cur.fetchone()
        if not g:
            raise HTTPException(404, "Guruh topilmadi")
        if int(g["egasi"]) != int(user_id):
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
            if not cur.fetchone():
                raise HTTPException(403, "Bu guruh sizniki emas")
        return g

    def korinish(cur, g, egasi=False):
        cur.execute("SELECT COUNT(*) AS n FROM kurs_guruh_azo WHERE guruh_id=%s", (g["id"],))
        n = int(cur.fetchone()["n"])
        d = {"id": int(g["id"]), "nom": g["nom"], "fan": g["fan"], "grade": g["grade"], "kurs_nomi": g["kurs_nomi"], "azolar": n,
             "bugungi": g["bugungi"], "bugungi_nom": g["bugungi_nom"], "bugungi_vaqt": g["bugungi_vaqt"].isoformat() if g["bugungi_vaqt"] else None,
             "kamera": bool(g.get("kamera"))}
        if egasi:
            d["kod"] = g["kod"]
        return d

    @router.post("/api/kurs_guruh")
    def yarat(body: GuruhYarat, authorization: str = Header(None)):
        user_id = uid(body.token, authorization)
        nom = re.sub(r"\s+", " ", body.nom).strip()
        if not 2 <= len(nom) <= 80:
            raise HTTPException(400, "Guruh nomini yozing")

        def go(cur):
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
            admin = bool(cur.fetchone())
            cur.execute("SELECT role FROM users WHERE user_id=%s", (user_id,))
            r = cur.fetchone()
            if not admin and str((r or {}).get("role") or "") in ("oquvchi", ""):
                raise HTTPException(403, "Guruhni o‘qituvchi ochadi")
            for _ in range(10):
                kod = kod_yasa()
                cur.execute("SELECT 1 FROM kurs_guruh WHERE kod=%s", (kod,))
                if not cur.fetchone():
                    break
            cur.execute("""INSERT INTO kurs_guruh(egasi, fan, grade, kurs_nomi, nom, kod) VALUES (%s,%s,%s,%s,%s,%s) RETURNING *""",
                        (user_id, body.fan.strip(), body.grade.strip(), body.kurs_nomi.strip(), nom, kod))
            return {"ok": True, "guruh": korinish(cur, cur.fetchone(), True)}
        return run(go)

    @router.get("/api/kurs_guruh")
    def royxat(token: str = None, fan: str = Query("", max_length=160), grade: str = Query("", max_length=40), authorization: str = Header(None)):
        """Mening guruhlarim (o'qituvchi) va a'zo bo'lgan guruhlarim (talaba); fan berilsa — shu kurs bo'yicha."""
        user_id = uid(token, authorization)

        def go(cur):
            shart, par = ("AND g.fan=%s AND g.grade=%s", [fan, grade]) if fan else ("", [])
            cur.execute(f"SELECT g.* FROM kurs_guruh g WHERE g.egasi=%s AND g.faol {shart} ORDER BY g.id DESC", [user_id, *par])
            meniki = [korinish(cur, g, True) for g in cur.fetchall()]
            cur.execute(f"""SELECT g.* FROM kurs_guruh g JOIN kurs_guruh_azo a ON a.guruh_id=g.id WHERE a.user_id=%s AND g.faol {shart}
                            ORDER BY a.qoshildi DESC""", [user_id, *par])
            azolik = [korinish(cur, g) for g in cur.fetchall()]
            return {"meniki": meniki, "azolik": azolik}
        return run(go)

    @router.post("/api/kurs_guruh/qoshil")
    def qoshil(body: Qoshil, authorization: str = Header(None)):
        user_id = uid(body.token, authorization)

        def go(cur):
            cur.execute("SELECT * FROM kurs_guruh WHERE kod=%s AND faol", (kod_norm(body.kod),))
            g = cur.fetchone()
            if not g:
                raise HTTPException(404, "Guruh topilmadi — kodni tekshiring")
            if int(g["egasi"]) != int(user_id):
                cur.execute("INSERT INTO kurs_guruh_azo(guruh_id, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (g["id"], user_id))
            return {"ok": True, "guruh": korinish(cur, g, int(g["egasi"]) == int(user_id))}
        return run(go)

    @router.post("/api/kurs_guruh/{gid}/bugungi")
    def bugungi(gid: int, body: Bugungi, authorization: str = Header(None)):
        user_id = uid(body.token, authorization)

        def go(cur):
            ozi(cur, gid, user_id)
            cur.execute("UPDATE kurs_guruh SET bugungi=%s, bugungi_nom=%s, bugungi_vaqt=NOW() WHERE id=%s RETURNING *",
                        (body.topic_code.strip(), body.nom.strip()[:200], gid))
            return {"ok": True, "guruh": korinish(cur, cur.fetchone(), True)}
        return run(go)

    class Kamera(BaseModel):
        token: Optional[str] = None
        kamera: bool

    @router.post("/api/kurs_guruh/{gid}/kamera")
    def kamera(gid: int, body: Kamera, authorization: str = Header(None)):
        """REV483: o'qituvchi tanlaydi — guruh o'quvchilarining barcha nazoratlari kamera bilan."""
        user_id = uid(body.token, authorization)
        def go(cur):
            ozi(cur, gid, user_id)
            cur.execute("UPDATE kurs_guruh SET kamera=%s WHERE id=%s RETURNING *", (bool(body.kamera), gid))
            return {"ok": True, "guruh": korinish(cur, cur.fetchone(), True)}
        return run(go)

    @router.get("/api/kurs_guruh/{gid}/nazoratlar")
    def nazoratlar(gid: int, token: str = None, authorization: str = Header(None)):
        """REV483: guruh o'quvchilarining nazorat natijalari — halollik belgilari va kamera rasmlari (imzolangan havolalar)."""
        user_id = uid(token, authorization)
        def go(cur):
            g = ozi(cur, gid, user_id)
            from modules.kurslar import kurs_of
            kalit = kurs_of(g["fan"], g["grade"])[0]
            cur.execute("""SELECT n.user_id, COALESCE(NULLIF(us.full_name,''),'O‘quvchi') AS ism, n.kod, n.tur, n.togri, n.jami, n.otdi, n.urinishlar,
                                  n.oxirgi_urinish, n.halollik FROM kurs_nazorat n JOIN kurs_guruh_azo a ON a.user_id=n.user_id AND a.guruh_id=%s
                           JOIN users us ON us.user_id=n.user_id WHERE n.kalit=%s ORDER BY n.oxirgi_urinish DESC LIMIT 300""", (gid, kalit))
            qat = cur.fetchall()
            rasm = {}
            try:
                from modules import ombor
                cur.execute("SAVEPOINT kgr")
                cur.execute("""SELECT user_id, kod, s3_kalit, vaqt FROM kurs_nazorat_rasm WHERE kalit=%s AND user_id = ANY(%s) AND vaqt > NOW() - INTERVAL '30 days'
                               ORDER BY vaqt""", (kalit, [r["user_id"] for r in qat] or [0]))
                for r in cur.fetchall():
                    if ombor.yoqilgan():
                        rasm.setdefault((r["user_id"], r["kod"]), []).append(ombor.havola(r["s3_kalit"], 3600))
                cur.execute("RELEASE SAVEPOINT kgr")
            except Exception:   # noqa: BLE001
                cur.execute("ROLLBACK TO SAVEPOINT kgr")
            return {"natijalar": [{"ism": r["ism"], "kod": r["kod"], "tur": r["tur"], "togri": r["togri"], "jami": r["jami"], "otdi": r["otdi"],
                                   "urinishlar": r["urinishlar"], "vaqt": r["oxirgi_urinish"].isoformat(), "halollik": r["halollik"] or {},
                                   "rasmlar": rasm.get((r["user_id"], r["kod"]), [])[-12:]} for r in qat]}
        return run(go)

    @router.delete("/api/kurs_guruh/{gid}")
    def ochir(gid: int, token: str = None, authorization: str = Header(None)):
        user_id = uid(token, authorization)

        def go(cur):
            ozi(cur, gid, user_id)
            cur.execute("UPDATE kurs_guruh SET faol=FALSE WHERE id=%s", (gid,))
            return {"ok": True}
        return run(go)

    @router.post("/api/kurs_dars/javob")
    def javob(body: Javob, authorization: str = Header(None)):
        """Darsdagi har bir misol/masala/test javobi (birinchi to'g'ri javob saqlanadi, urinishlar sanaladi)."""
        user_id = uid(body.token, authorization)

        def go(cur):
            cur.execute("""INSERT INTO kurs_dars_javob(user_id, topic_code, item, turi, togri) VALUES (%s,%s,%s,%s,%s)
                           ON CONFLICT (user_id, topic_code, item) DO UPDATE SET togri = kurs_dars_javob.togri OR EXCLUDED.togri,
                           urinish = kurs_dars_javob.urinish + 1, vaqt = NOW()""",
                        (user_id, body.topic_code, body.item[:60], body.turi[:12], bool(body.togri)))
            cur.execute("""INSERT INTO kurs_dars_jonli(user_id, topic_code) VALUES (%s,%s)
                           ON CONFLICT (user_id, topic_code) DO UPDATE SET holat='faol', yangilandi=NOW()""", (user_id, body.topic_code))
            return {"ok": True}
        return run(go)

    @router.post("/api/kurs_dars/jonli")
    def jonli_yoz(body: Jonli, authorization: str = Header(None)):
        user_id = uid(body.token, authorization)
        holat = body.holat if body.holat in ("faol", "chiqdi") else "faol"

        def go(cur):
            cur.execute("""INSERT INTO kurs_dars_jonli(user_id, topic_code, holat) VALUES (%s,%s,%s)
                           ON CONFLICT (user_id, topic_code) DO UPDATE SET holat=EXCLUDED.holat, yangilandi=NOW()""", (user_id, body.topic_code, holat))
            return {"ok": True}
        return run(go)

    @router.get("/api/kurs_guruh/{gid}/jonli")
    def jonli(gid: int, token: str = None, topic_code: str = Query("", max_length=80), jami: int = Query(0, ge=0, le=500),
              authorization: str = Header(None)):
        """O'qituvchi: guruhning har bir a'zosi shu darsda — holat, yechgan, to'g'ri (masala/test alohida), oxirgi faollik."""
        user_id = uid(token, authorization)

        def go(cur):
            g = ozi(cur, gid, user_id)
            tc = topic_code or g["bugungi"]
            if not tc:
                return {"oquvchilar": [], "topic_code": "", "soni": {}}
            cur.execute("""SELECT u.user_id, COALESCE(u.full_name,'') AS ism,
                                  EXTRACT(EPOCH FROM (NOW()-j.yangilandi)) AS oldin, j.holat,
                                  COALESCE(SUM(CASE WHEN v.item IS NOT NULL THEN 1 ELSE 0 END),0) AS yechgan,
                                  COALESCE(SUM(CASE WHEN v.togri THEN 1 ELSE 0 END),0) AS togri,
                                  COALESCE(SUM(CASE WHEN v.turi='test' THEN 1 ELSE 0 END),0) AS test,
                                  COALESCE(SUM(CASE WHEN v.turi='test' AND v.togri THEN 1 ELSE 0 END),0) AS test_togri
                           FROM kurs_guruh_azo a JOIN users u ON u.user_id=a.user_id
                           LEFT JOIN kurs_dars_jonli j ON j.user_id=a.user_id AND j.topic_code=%s
                           LEFT JOIN kurs_dars_javob v ON v.user_id=a.user_id AND v.topic_code=%s
                           WHERE a.guruh_id=%s GROUP BY u.user_id, u.full_name, j.yangilandi, j.holat ORDER BY u.full_name""", (tc, tc, gid))
            out = []
            for r in cur.fetchall():
                oldin = float(r["oldin"]) if r["oldin"] is not None else None
                yech = int(r["yechgan"])
                out.append({"user_id": int(r["user_id"]), "ism": r["ism"], "holat": holat_of(oldin if (oldin is not None or yech) else None, r["holat"], jami, yech),
                            "yechgan": yech, "togri": int(r["togri"]), "test": int(r["test"]), "test_togri": int(r["test_togri"]),
                            "oldin": round(oldin) if oldin is not None else None})
            soni = {k: sum(1 for x in out if x["holat"] == k) for k in ("yechmoqda", "chiqdi", "tugatdi", "boshlamagan")}
            return {"oquvchilar": out, "topic_code": tc, "soni": soni}
        return run(go)

    return router

"""REV481: 🕵️ «Mister Nazoratchi» — o'yin xonasida.
1) Dars tugasa — o'yin: o'yin xonasi bugun kamida bitta dars tugatilgan bo'lsa ochiladi (darsga yozilmaganlar va admin — cheklovsiz).
2) O'yin o'rtasida Nazoratchi 1–3 dars oldingi darslardan 3 ta savol so'raydi (kuniga ko'pi bilan 3 marta).
3) 3 tadan 2 tasi xato — o'yin qulflanadi: 1 kun, 30 kun ichida qayta bo'lsa 2, 3, eng ko'pi 4 kun. Qaysi darslarni takrorlash kerakligi
   ko'rsatiladi; bola shu darslardan birini qayta o'tib tugatsa — qulf DARHOL ochiladi. Ota-onaga bildirishnoma boradi."""
import json
import random
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

KUNLIK_CHIQISH = 3
_TAYYOR = {"ok": False}


def jadval(cur):
    if _TAYYOR["ok"]:
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS nazoratchi_qulf (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, gacha DATE NOT NULL,
        kun INT NOT NULL, darslar JSONB NOT NULL DEFAULT '[]', ochildi BOOLEAN NOT NULL DEFAULT FALSE, yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE INDEX IF NOT EXISTS nazoratchi_qulf_u ON nazoratchi_qulf(user_id, yaratildi DESC)")
    cur.execute("""CREATE TABLE IF NOT EXISTS nazoratchi_sorov (user_id BIGINT NOT NULL, kun DATE NOT NULL, soni INT NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, kun))""")
    _TAYYOR["ok"] = True


def toshkent_bugun():
    return (datetime.now(timezone.utc) + timedelta(hours=5)).date()


def qulf_kunlari(oldingi_marta):
    """30 kun ichidagi oldingi qulflar soni → necha kun (1, 2, 3, ko'pi bilan 4)."""
    return min(4, 1 + max(0, int(oldingi_marta)))


def _tugatilganlar(cur, uid, soni=8):
    """Eng oxirgi tugatilgan darslar (bolalar va maktab kurslari) — [(kod, nom, vaqt)] yangisidan eskisiga."""
    out = []
    for sql in ("""SELECT dars_kod AS kod, mavzu AS nom, tugatilgan_at AS t FROM bola_dars_holat WHERE child_id=%s AND tugatilgan_at IS NOT NULL
                   ORDER BY tugatilgan_at DESC LIMIT %s""",
                """SELECT topic_code AS kod, '' AS nom, tugadi_at AS t FROM kurs_dars_holat WHERE user_id=%s AND topic_code NOT LIKE 'NZ:%%'
                   ORDER BY tugadi_at DESC LIMIT %s"""):
        try:
            cur.execute("SAVEPOINT nz_t"); cur.execute(sql, (uid, soni)); out += [(r["kod"], r["nom"], r["t"]) for r in cur.fetchall()]
            cur.execute("RELEASE SAVEPOINT nz_t")
        except Exception:   # noqa: BLE001 — jadval hali yo'q bo'lishi mumkin
            cur.execute("ROLLBACK TO SAVEPOINT nz_t")
    out.sort(key=lambda x: x[2], reverse=True)
    seen, res = set(), []
    for k, n, t in out:
        if k not in seen:
            seen.add(k); res.append((k, n, t))
    return res


def holat(cur, uid, admin=False):
    jadval(cur)
    bugun = toshkent_bugun()
    if admin:
        return {"ruxsat": True, "sabab": "", "admin": True, "nazoratchi": True}
    darslar = _tugatilganlar(cur, uid)
    cur.execute("SELECT * FROM nazoratchi_qulf WHERE user_id=%s AND NOT ochildi ORDER BY yaratildi DESC LIMIT 1", (uid,))
    q = cur.fetchone()
    if q and q["gacha"] > bugun:
        kerak = {d["kod"] for d in (q["darslar"] or [])}
        if any(k in kerak and t > q["yaratildi"] for k, _, t in darslar):   # darsni qayta o'tdi — darhol ochiladi
            cur.execute("UPDATE nazoratchi_qulf SET ochildi=TRUE WHERE id=%s", (q["id"],))
        else:
            return {"ruxsat": False, "sabab": "qulf", "gacha": q["gacha"].isoformat(), "kun": q["kun"], "darslar": q["darslar"] or []}
    if darslar and not any((t + timedelta(hours=5)).date() == bugun for _, _, t in darslar):
        return {"ruxsat": False, "sabab": "dars", "darslar": []}   # avval bugungi dars
    cur.execute("SELECT soni FROM nazoratchi_sorov WHERE user_id=%s AND kun=%s", (uid, bugun))
    r = cur.fetchone()
    return {"ruxsat": True, "sabab": "", "nazoratchi": len(darslar) >= 2 and (r["soni"] if r else 0) < KUNLIK_CHIQISH}


class Natija(BaseModel):
    token: str = ""
    togri: int
    jami: int
    darslar: list = []


def create_router(platform, yukla_ol=None):
    router = APIRouter(tags=["nazoratchi"])

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

    def admin_mi(cur, u):
        try:
            cur.execute("SAVEPOINT nz_a"); cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (u,)); a = cur.fetchone() is not None
            cur.execute("RELEASE SAVEPOINT nz_a"); return a
        except Exception:   # noqa: BLE001
            cur.execute("ROLLBACK TO SAVEPOINT nz_a"); return False

    @router.get("/api/nazoratchi/ruxsat")
    def ruxsat(token: str = "", authorization: str = Header(None)):
        u = uid(token, authorization)
        return run(lambda cur: holat(cur, u, admin_mi(cur, u)))

    @router.get("/api/nazoratchi/savollar")
    def savollar(token: str = "", til: str = "uz", authorization: str = Header(None)):
        """1, 2, 3-oldingi darslardan bittadan savol (bugun hozirgina tugatilgani emas). Chiqish soni hisoblanadi."""
        u = uid(token, authorization)
        from modules import dars_xonasi as _dx
        yukla = yukla_ol() if yukla_ol else _dx.TASHQI.get("yukla")
        def f(cur):
            darslar = _tugatilganlar(cur, u)
            tanlov = darslar[1:4] if len(darslar) >= 4 else darslar[-3:]
            rnd = random.Random(f"{u}:{datetime.now().isoformat(timespec='minutes')}")
            out = []
            for kod, nom, _ in tanlov:
                try:
                    les = yukla(kod, til) if yukla else {}
                except Exception:   # noqa: BLE001
                    les = {}
                qs = [q for q in (les.get("savollar") or []) if q.get("variantlar")]
                if qs:
                    q = rnd.choice(qs)
                    out.append({**{k: v for k, v in q.items() if not str(k).startswith("_")}, "dars": kod,
                                "dars_nomi": nom or (les.get("topic") or {}).get("mavzu", "")})
            bugun = toshkent_bugun()
            cur.execute("""INSERT INTO nazoratchi_sorov(user_id, kun, soni) VALUES(%s,%s,1)
                           ON CONFLICT (user_id, kun) DO UPDATE SET soni=nazoratchi_sorov.soni+1""", (u, bugun))
            return {"savollar": out}
        return run(f)

    @router.post("/api/nazoratchi/natija")
    def natija(body: Natija, authorization: str = Header(None)):
        u = uid(body.token, authorization)
        def f(cur):
            if body.jami < 2 or (body.jami - body.togri) * 3 < 2 * body.jami:   # 3 tadan 2 tasi xato bo'lsa — qulf
                return {"qulf": False}
            if admin_mi(cur, u):
                return {"qulf": False, "admin": True}
            cur.execute("SELECT COUNT(*) AS n FROM nazoratchi_qulf WHERE user_id=%s AND yaratildi > NOW() - INTERVAL '30 days'", (u,))
            kun = qulf_kunlari(cur.fetchone()["n"])
            gacha = toshkent_bugun() + timedelta(days=kun)
            darslar = [{"kod": str(d.get("kod", ""))[:80], "nomi": str(d.get("nomi", ""))[:160]} for d in body.darslar[:5] if isinstance(d, dict)]
            cur.execute("INSERT INTO nazoratchi_qulf(user_id, gacha, kun, darslar) VALUES(%s,%s,%s,%s::jsonb)", (u, gacha, kun, json.dumps(darslar, ensure_ascii=False)))
            try:   # ota-onaga xabar (bildirishnomalar jadvali bo'lsa)
                cur.execute("SAVEPOINT nz_b")
                cur.execute("SELECT DISTINCT parent_id FROM parent_child WHERE child_id=%s", (u,))
                nomlar = ", ".join(d["nomi"] for d in darslar if d["nomi"]) or "oldingi darslar"
                for p in cur.fetchall():
                    cur.execute("INSERT INTO bildirishnomalar(user_id, matn, turi) VALUES(%s,%s,'nazoratchi')",
                                (p["parent_id"], f"🕵️ Nazoratchi: farzandingiz {nomlar} mavzusini unutgan — o'yinlar {kun} kunga to'xtatildi. Darsni qayta o'tsa, darhol ochiladi."))
                cur.execute("RELEASE SAVEPOINT nz_b")
            except Exception:   # noqa: BLE001
                cur.execute("ROLLBACK TO SAVEPOINT nz_b")
            return {"qulf": True, "kun": kun, "gacha": gacha.isoformat(), "darslar": darslar}
        return run(f)

    return router

"""REV481: 🕵️ «Mister Nazoratchi» — o'yin xonasida.
1) Dars tugasa — o'yin: o'yin xonasi bugun kamida bitta dars tugatilgan bo'lsa ochiladi (darsga yozilmaganlar va admin — cheklovsiz).
2) O'yin o'rtasida Nazoratchi 1–3 dars oldingi darslardan 3 ta savol so'raydi (kuniga ko'pi bilan 3 marta).
3) 3 tadan 2 tasi xato — o'yin qulflanadi: 1 kun, 30 kun ichida qayta bo'lsa 2, 3, eng ko'pi 4 kun. Qaysi darslarni takrorlash kerakligi
   ko'rsatiladi; bola shu darslardan birini qayta o'tib tugatsa — qulf DARHOL ochiladi. Ota-onaga bildirishnoma boradi."""
import json
import random
import re
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
    # REV521: kunlik o'yin hisobi — nechta bosqich tugatildi (har 3 tadan keyin Nazoratchi) va nechta XIL o'yin (10 ta — kunlik chegara)
    cur.execute("""CREATE TABLE IF NOT EXISTS nazoratchi_oyin_kun (user_id BIGINT NOT NULL, kun DATE NOT NULL, soni INT NOT NULL DEFAULT 0,
        oyinlar JSONB NOT NULL DEFAULT '[]'::jsonb, PRIMARY KEY (user_id, kun))""")
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


KUNLIK_OYIN = 10      # REV521: kuniga 10 xil o'yin (har biri 10 talik bosqich) — keyin o'yinlar bugunga tugaydi
NAZORAT_HAR = 3       # har 3 ta tugatilgan o'yindan keyin Nazoratchi


def oyin_kun(cur, uid, bugun):
    cur.execute("SELECT soni, oyinlar FROM nazoratchi_oyin_kun WHERE user_id=%s AND kun=%s", (uid, bugun))
    r = cur.fetchone()
    return (int(r["soni"]), list(r["oyinlar"] or [])) if r else (0, [])


def holat(cur, uid, admin=False):
    jadval(cur)
    bugun = toshkent_bugun()
    if admin:
        return {"ruxsat": True, "sabab": "", "admin": True, "nazoratchi": True}
    soni_o, xil_o = oyin_kun(cur, uid, bugun)
    if len(xil_o) >= KUNLIK_OYIN:
        return {"ruxsat": False, "sabab": "chegara", "bugun_oyin": len(xil_o), "chegara": KUNLIK_OYIN}
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
    kichik = bolami(cur, uid)   # bolaga savollar yoshiga mos tuziladi — dars soni shart emas
    return {"ruxsat": True, "sabab": "", "nazoratchi": (kichik or len(darslar) >= 2) and (r["soni"] if r else 0) < KUNLIK_CHIQISH,
            "bugun_oyin": len(xil_o), "tugagan": soni_o, "chegara": KUNLIK_OYIN, "nazorat_har": NAZORAT_HAR}


class Natija(BaseModel):
    token: str = ""
    togri: int
    jami: int
    darslar: list = []


# ───── REV519: 2–7 yoshli bola uchun Nazoratchi savollari — darsning test bazasidan EMAS (u yerda kattalar savoli bo'lishi
# mumkin), balki shu yoshga mos, rasmli, o'qishsiz savollar: sanash, ko'p-kam, shakl, rang, keyingi son, rasmli qo'shish.
_NARSA = [("🍎", "olma"), ("🐟", "baliq"), ("⭐", "yulduz"), ("🎈", "shar"), ("🐥", "jo‘ja"), ("🌷", "gul"), ("🚗", "mashina"), ("🍓", "qulupnay")]
_SHAKL = [("⚪", "doira"), ("🔺", "uchburchak"), ("⬛", "kvadrat"), ("⭐", "yulduz")]
_RANG = [("🔴", "qizil"), ("🟢", "yashil"), ("🔵", "ko‘k"), ("🟡", "sariq")]


def bola_savollari(rnd, mavzu="", soni=3):
    m = str(mavzu or "").lower()
    def sanash():
        e, nom = rnd.choice(_NARSA); n = rnd.randint(2, 8); vs = sorted({n, n + 1, max(1, n - 1)}); rnd.shuffle(vs)
        return {"savol": f"{e * n} — nechta {nom}?", "variantlar": [str(v) for v in vs], "togri": vs.index(n), "tur": "sanash"}
    def kopi():
        (e1, _), (e2, _) = rnd.sample(_NARSA, 2); a, b = rnd.sample(range(2, 7), 2)
        vs = [e1 * a, e2 * b]
        return {"savol": "Qaysi biri ko‘p?", "variantlar": vs, "togri": 0 if a > b else 1, "tur": "kop"}
    def shakl():
        tog = rnd.choice(_SHAKL); vs = [x[0] for x in _SHAKL[:3]] if tog in _SHAKL[:3] else [x[0] for x in _SHAKL[1:]]
        rnd.shuffle(vs)
        return {"savol": f"Qaysi biri {tog[1]}?", "variantlar": vs, "togri": vs.index(tog[0]), "tur": "shakl"}
    def rang():
        tog = rnd.choice(_RANG); vs = [x[0] for x in _RANG]; rnd.shuffle(vs)
        return {"savol": f"Qaysi biri {tog[1]}?", "variantlar": vs, "togri": vs.index(tog[0]), "tur": "rang"}
    def keyingi():
        n = rnd.randint(1, 8); vs = [n + 1, n - 1 if n > 1 else n + 2, n + 2 if n > 1 else n + 3]; rnd.shuffle(vs)
        return {"savol": f"{n} dan keyin qaysi son?", "variantlar": [str(v) for v in vs], "togri": vs.index(n + 1), "tur": "keyingi"}
    def qoshish():
        e, nom = rnd.choice(_NARSA); a, b = rnd.randint(1, 4), rnd.randint(1, 3); n = a + b
        vs = sorted({n, n + 1, max(1, n - 1)}); rnd.shuffle(vs)
        return {"savol": f"{e * a} + {e * b} — hammasi nechta?", "variantlar": [str(v) for v in vs], "togri": vs.index(n), "tur": "qoshish"}
    tanlov = [sanash, kopi, keyingi, qoshish]
    if re.search(r"shakl|doira|uchburchak|kvadrat", m):
        tanlov = [shakl, shakl, sanash]
    elif re.search(r"rang", m):
        tanlov = [rang, rang, sanash]
    out, kor = [], set()
    for _ in range(soni * 4):
        q = rnd.choice(tanlov)()
        if q["savol"] + str(q["variantlar"]) not in kor:
            kor.add(q["savol"] + str(q["variantlar"])); out.append({**q, "dars_nomi": mavzu, "bola": True})
        if len(out) >= soni:
            break
    return out


def bolami(cur, u):
    """2–7 yosh: bog'cha darslari, bolalar kursi, bog'cha profili yoki sinfi «yosh»/«bog'cha» — bittasi yetarli."""
    for sql in ("SELECT 1 FROM bola_dars_holat WHERE child_id=%s LIMIT 1",
                "SELECT 1 FROM kurs_dars_holat WHERE user_id=%s AND kalit LIKE 'bolalar|%%' LIMIT 1",
                "SELECT 1 FROM users WHERE user_id=%s AND LOWER(COALESCE(class,'')) ~ '(yosh|bog|mtt|maktabgacha)'",
                "SELECT 1 FROM users WHERE user_id=%s AND COALESCE(kabutar_learning_profile->>'role','') = 'bogcha'",
                "SELECT 1 FROM users WHERE user_id=%s AND COALESCE(education_role,'') = 'bogcha'"):   # har biri alohida — ustun bo'lmasa qolganlari ishlaydi
        try:
            cur.execute("SAVEPOINT nz_bm"); cur.execute(sql, (u,)); r = cur.fetchone() is not None; cur.execute("RELEASE SAVEPOINT nz_bm")
            if r:
                return True
        except Exception:   # noqa: BLE001 — ustun yoki jadval bo'lmasa keyingisi
            cur.execute("ROLLBACK TO SAVEPOINT nz_bm")
    return False


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

    @router.post("/api/nazoratchi/oyin_tugadi")
    def oyin_tugadi(oyin_id: int, token: str = "", authorization: str = Header(None)):
        """Bola o'yin bosqichini (10 talik) tugatdi: kunlik hisobga yoziladi. Javobda — Nazoratchi hozir chiqsinmi va chegara."""
        u = uid(token, authorization)
        def f(cur):
            jadval(cur)
            if admin_mi(cur, u):
                return {**holat(cur, u, True), "nazoratchi_hozir": False}
            bugun = toshkent_bugun()
            cur.execute("""INSERT INTO nazoratchi_oyin_kun(user_id, kun, soni, oyinlar) VALUES(%s,%s,1,%s::jsonb)
                           ON CONFLICT (user_id, kun) DO UPDATE SET soni = nazoratchi_oyin_kun.soni + 1,
                             oyinlar = CASE WHEN nazoratchi_oyin_kun.oyinlar @> %s::jsonb THEN nazoratchi_oyin_kun.oyinlar
                                            ELSE nazoratchi_oyin_kun.oyinlar || %s::jsonb END
                           RETURNING soni""", (u, bugun, json.dumps([int(oyin_id)]), json.dumps([int(oyin_id)]), json.dumps([int(oyin_id)])))
            soni = int(cur.fetchone()["soni"])
            h = holat(cur, u)
            return {**h, "nazoratchi_hozir": bool(h.get("nazoratchi")) and soni % NAZORAT_HAR == 0}
        return run(f)

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
            if bolami(cur, u):   # REV519: 2–7 yosh — darslar test bazasidan EMAS, yoshga mos rasmli savollar
                out = bola_savollari(rnd, (tanlov[0][1] if tanlov else ""), 3)
            else:
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

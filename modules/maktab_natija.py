"""REV173: Maktab (1–11 sinf) til o'yinlari natijasi — ball, daraja (CEFR), o'tilgan bo'limlar va sinfdoshlar orasida o'rin.

  • POST /api/maktab/natija — o'quvchi qurilmasidagi jami natija (ball, javoblar, daraja). Server eng yaxshisini saqlaydi:
    ball/javoblar/o'tilgan bo'limlar kamaymaydi (boshqa qurilmadan kirsa ham), daraja pasaymaydi.
  • GET /api/maktab/reyting?til=en&sinf=7 — shu til va sinfdagi o'quvchilar orasida o'rin (ismlar ko'rsatilmaydi).
Keyingi bosqichda ota-ona sahifasi shu jadvaldan farzandining darajasini ko'radi.
"""
import threading
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from platform_core.ddl_guard import LazyMigration as _LazyMigration
except ImportError:   # pragma: no cover
    _LazyMigration = None

TILLAR = {"en", "ru", "de", "fr", "es", "ar", "tr", "zh", "ja", "ko"}
CEFR = ["", "Pre-A1", "A1", "A2", "B1"]   # REV174: dastur faqat B1 gacha — boshqa qiymat qabul qilinmaydi
KUNLIK_BAL = 10000      # bir kunda ko'pi bilan shuncha ball qo'shiladi (faol o'quvchi ~2–3 ming to'playdi)
KUNLIK_JAVOB = 3000     # bir kunda ko'pi bilan shuncha javob
KUNLIK_BOLIM = 12       # bir kunda ko'pi bilan shuncha bo'lim imtihoni
FAOL_KUN = 60          # reytingda — oxirgi 60 kunda faol bo'lganlar
REYTING_MIN = 3        # kamida shuncha o'quvchi bo'lsa o'rin ko'rsatiladi


class Natija(BaseModel):
    token: str = ""
    til: str = Field(min_length=2, max_length=5)
    sinf: int = Field(default=1, ge=1, le=11)
    bal: int = Field(default=0, ge=0, le=50_000_000)
    togri: int = Field(default=0, ge=0, le=5_000_000)
    jami: int = Field(default=0, ge=0, le=5_000_000)
    daraja: str = Field(default="", max_length=10)
    keyingi: str = Field(default="", max_length=10)
    foiz: int = Field(default=0, ge=0, le=100)
    otildi: int = Field(default=0, ge=0, le=200)


def daraja_raqami(kod):
    kod = str(kod or "")
    return CEFR.index(kod) if kod in CEFR else 0


def sinf_of(value, fallback):
    """users.class («7», «7-A», «7 sinf») → 7; topilmasa — o'quvchi yuborgan sinf."""
    digits = "".join(ch if ch.isdigit() else " " for ch in str(value or "")).split()
    for d in digits:
        n = int(d)
        if 1 <= n <= 11:
            return n
    return max(1, min(11, int(fallback or 1)))


def birlashtir(eski, yangi):
    """Saqlangan va yangi natijadan eng yaxshisi: sonlar kamaymaydi, daraja pasaymaydi (foiz — shu darajaga mos)."""
    eski = eski or {}
    out = {k: max(int(eski.get(k) or 0), int(yangi.get(k) or 0)) for k in ("bal", "togri", "jami", "otildi")}
    if out["togri"] > out["jami"]:
        out["togri"] = out["jami"]
    e, y = daraja_raqami(eski.get("daraja")), daraja_raqami(yangi.get("daraja"))
    if y > e or (y == e and int(yangi.get("foiz") or 0) >= int(eski.get("foiz") or 0)):
        out.update(daraja=CEFR[y], keyingi=str(yangi.get("keyingi") or "")[:10], foiz=int(yangi.get("foiz") or 0))
    else:
        out.update(daraja=CEFR[e], keyingi=str(eski.get("keyingi") or "")[:10], foiz=int(eski.get("foiz") or 0))
    return out


def kunlik_chegara(eski, r, today):
    """REV174: soxta so'rov bilan reytingni ko'tarib bo'lmasin — bir kunda o'sish chegaralangan (kun boshidagi qiymatdan).
    → (r — chegaralangan, kun_bosh — {kun, bal, jami, otildi})."""
    eski = eski or {}
    if eski.get("kun") == today:
        bosh = {"kun": today, "bal": int(eski.get("kun_bal") or 0), "jami": int(eski.get("kun_jami") or 0), "otildi": int(eski.get("kun_otildi") or 0)}
    else:
        bosh = {"kun": today, "bal": int(eski.get("bal") or 0), "jami": int(eski.get("jami") or 0), "otildi": int(eski.get("otildi") or 0)}
    out = dict(r)
    out["bal"] = min(out["bal"], bosh["bal"] + KUNLIK_BAL)
    out["jami"] = min(out["jami"], bosh["jami"] + KUNLIK_JAVOB)
    out["togri"] = min(out["togri"], out["jami"])
    out["otildi"] = min(out["otildi"], bosh["otildi"] + KUNLIK_BOLIM)
    return out, bosh


def orin(ballar, mening):
    """O'rin: mendan ko'p ball to'plaganlar soni + 1."""
    return 1 + sum(1 for b in ballar if b > mening)


def migrate(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maktab_til_natija (
            user_id BIGINT NOT NULL,
            til TEXT NOT NULL,
            sinf INT NOT NULL DEFAULT 1,
            bal BIGINT NOT NULL DEFAULT 0,
            togri INT NOT NULL DEFAULT 0,
            jami INT NOT NULL DEFAULT 0,
            daraja TEXT NOT NULL DEFAULT '',
            keyingi TEXT NOT NULL DEFAULT '',
            foiz INT NOT NULL DEFAULT 0,
            otildi INT NOT NULL DEFAULT 0,
            yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, til)
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS maktab_til_natija_reyting ON maktab_til_natija(til, sinf, bal DESC)")
    # REV174: kunlik o'sish chegarasi uchun kun boshidagi qiymatlar
    cur.execute("ALTER TABLE maktab_til_natija ADD COLUMN IF NOT EXISTS kun DATE")
    cur.execute("ALTER TABLE maktab_til_natija ADD COLUMN IF NOT EXISTS kun_bal BIGINT NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE maktab_til_natija ADD COLUMN IF NOT EXISTS kun_jami INT NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE maktab_til_natija ADD COLUMN IF NOT EXISTS kun_otildi INT NOT NULL DEFAULT 0")


def create_router(platform):
    router = APIRouter()
    ready = {"ok": False}
    lock = threading.Lock()
    lazy = _LazyMigration("maktab_natija") if _LazyMigration else None

    def uid_of(token, authorization):
        return int(platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization)))

    def run_db(fn):
        conn = platform._db()
        cur = conn.cursor()
        try:
            if not ready["ok"]:
                if lazy is not None:
                    lazy.run(conn, cur, migrate)
                    ready["ok"] = lazy.ok
                else:
                    with lock:
                        if not ready["ok"]:
                            migrate(cur)
                            conn.commit()
                            ready["ok"] = True
            return fn(conn, cur)
        finally:
            cur.close()
            conn.close()

    def user_class(cur, user_id):
        try:
            cur.execute("SAVEPOINT maktab_sinf")
            cur.execute("SELECT class FROM users WHERE user_id=%s", (user_id,))
            row = cur.fetchone() or {}
            cur.execute("RELEASE SAVEPOINT maktab_sinf")
            return row.get("class")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT maktab_sinf")
            return None

    @router.post("/api/maktab/natija")
    def save_result(body: Natija, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        til = body.til.lower()
        if til not in TILLAR:
            raise HTTPException(400, "Noma'lum til")

        def run(conn, cur):
            sinf = sinf_of(user_class(cur, user_id), body.sinf)
            cur.execute("""SELECT bal, togri, jami, otildi, daraja, keyingi, foiz, kun, kun_bal, kun_jami, kun_otildi
                           FROM maktab_til_natija WHERE user_id=%s AND til=%s FOR UPDATE""", (user_id, til))
            eski = cur.fetchone()
            eski = dict(eski) if eski else None
            yangi = body.model_dump() if hasattr(body, "model_dump") else body.dict()
            if str(yangi.get("daraja") or "") not in CEFR:
                yangi["daraja"], yangi["foiz"] = "", 0
            r, bosh = kunlik_chegara(eski, birlashtir(eski, yangi), datetime.now(timezone(timedelta(hours=5))).date())
            # bir vaqtda kelgan ikki so'rov ham bir-birini kamaytirmaydi (GREATEST)
            cur.execute("""INSERT INTO maktab_til_natija(user_id, til, sinf, bal, togri, jami, daraja, keyingi, foiz, otildi, yangilangan_at,
                                                         kun, kun_bal, kun_jami, kun_otildi)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s,%s,%s)
                           ON CONFLICT (user_id, til) DO UPDATE SET sinf=EXCLUDED.sinf,
                             bal=GREATEST(maktab_til_natija.bal, EXCLUDED.bal), togri=GREATEST(maktab_til_natija.togri, EXCLUDED.togri),
                             jami=GREATEST(maktab_til_natija.jami, EXCLUDED.jami), daraja=EXCLUDED.daraja, keyingi=EXCLUDED.keyingi,
                             foiz=EXCLUDED.foiz, otildi=GREATEST(maktab_til_natija.otildi, EXCLUDED.otildi), yangilangan_at=NOW(),
                             kun=EXCLUDED.kun, kun_bal=EXCLUDED.kun_bal, kun_jami=EXCLUDED.kun_jami, kun_otildi=EXCLUDED.kun_otildi""",
                        (user_id, til, sinf, r["bal"], r["togri"], r["jami"], r["daraja"], r["keyingi"], r["foiz"], r["otildi"],
                         bosh["kun"], bosh["bal"], bosh["jami"], bosh["otildi"]))
            conn.commit()
            return {"ok": True, "sinf": sinf, **r}
        return run_db(run)

    @router.get("/api/maktab/reyting")
    def ranking(til: str = Query("en", max_length=5), sinf: int = Query(1, ge=1, le=11),
                token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til.lower()
        if til not in TILLAR:
            raise HTTPException(400, "Noma'lum til")

        def run(conn, cur):
            cur.execute("SELECT bal, sinf FROM maktab_til_natija WHERE user_id=%s AND til=%s", (user_id, til))
            me = cur.fetchone()
            if not me:
                conn.commit()
                return {"orin": None, "jami": 0}
            s = int(me["sinf"] or sinf)
            cur.execute(f"""SELECT COUNT(*) AS jami, COUNT(*) FILTER (WHERE bal > %s) AS yuqori FROM maktab_til_natija
                            WHERE til=%s AND sinf=%s AND yangilangan_at > NOW() - INTERVAL '{FAOL_KUN} days'""", (me["bal"], til, s))
            row = cur.fetchone() or {}
            conn.commit()
            jami = int(row.get("jami") or 0)
            if jami < REYTING_MIN:
                return {"orin": None, "jami": jami}
            return {"orin": int(row.get("yuqori") or 0) + 1, "jami": jami, "sinf": s}
        return run_db(run)

    return router

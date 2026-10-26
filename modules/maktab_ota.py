"""REV174: Maktab (1–11 sinf) o'quvchisi va ota-onasi.

O'quvchi:
  • POST /api/maktab/faollik — dars (fan mavzusi), til o'yini, repetitor yoki topshiriq natijasi (bugun nima qildi).
  • GET  /api/maktab/topshiriqlar — ota-ona bergan mashqlar (so'zlar, necha marta yozish, izoh).
  • POST /api/maktab/topshiriq/bajardi — mashq bajarildi (natija ota-onaga boradi: sayt + Telegram).
Ota-ona (parent_child yoki oila profili egasi; administrator ham):
  • GET  /api/ota/maktab?bola_id= — bugun va shu hafta (har kun), tillar darajasi (CEFR), o'rgangan so'zlari, topshiriqlar, sinovlar.
  • POST /api/ota/maktab/topshiriq — «Mashq ber»: so'zlar ro'yxati, necha marta yozish, izoh, muddat.
  • POST /api/ota/maktab/topshiriq/bekor — topshiriqni bekor qilish.
  • POST /api/ota/maktab/sinov — «O'zim sinayman» natijasi (bildi / bilmadi).
REV177 — kun rejasi (bolalar bog'chasidagidek):
  • GET  /api/maktab/reja — o'quvchining rejasi (kuniga necha dars, dam olish kunlari, yakshanba) va bugun bajargani.
  • POST /api/ota/maktab/reja — ota-ona rejani o'zgartiradi (0 — sinfga qarab avtomatik: 1–2 sinf 3–4 dars …).
"""
import json
import re
import threading
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

try:
    from platform_core.ddl_guard import LazyMigration as _LazyMigration
except ImportError:   # pragma: no cover
    _LazyMigration = None
try:
    from . import bogcha_reja as reja_mod
except ImportError:   # pragma: no cover
    from modules import bogcha_reja as reja_mod

TASHKENT = timezone(timedelta(hours=5))
WEEKDAYS_UZ = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
TILLAR = {"en", "ru", "de", "fr", "es", "ar", "tr", "zh", "ja", "ko"}
TIL_NOMI = {"en": "Ingliz tili", "ru": "Rus tili", "de": "Nemis tili", "fr": "Fransuz tili", "es": "Ispan tili",
            "ar": "Arab tili", "tr": "Turk tili", "zh": "Xitoy tili", "ja": "Yapon tili", "ko": "Koreys tili"}
TURLAR = {"dars", "til", "repetitor", "topshiriq", "imtihon", "takror"}   # REV176: imtihon; REV177: takror — darsdan oldingi spiral takror
SOZ_ID = re.compile(r"^[a-z0-9_-]{1,48}$")
YOZISH = (0, 5, 10, 20, 30, 40, 50, 100)
MAX_SOZ = 30            # bitta topshiriqda
FAOL_TOPSHIRIQ = 10     # bir vaqtda ochiq topshiriqlar
SOZLAR_RO_YXAT = 150    # ota-onaga — so'nggi o'rgangan so'zlar


def tashkent_day(now_utc):
    return now_utc.astimezone(TASHKENT).date()


def soz_idlari(items, limit=60):
    """Faqat to'g'ri ko'rinishdagi so'z identifikatorlari, takrorsiz, tartib saqlanadi."""
    out, seen = [], set()
    for x in items or []:
        s = str(x or "").strip().lower()
        if SOZ_ID.match(s) and s not in seen:
            seen.add(s)
            out.append(s)
            if len(out) >= limit:
                break
    return out


def matn(value, limit):
    return " ".join(str(value or "").split())[:limit]


def yozish_soni(n):
    """Ota-ona tanlagan «necha marta yozish» — ruxsat etilgan qiymatlarning eng yaqini (0..100)."""
    n = max(0, min(100, int(n or 0)))
    return min(YOZISH, key=lambda v: (abs(v - n), v))


def sinf_of(value):
    for d in "".join(ch if ch.isdigit() else " " for ch in str(value or "")).split():
        n = int(d)
        if 1 <= n <= 11:
            return n
    return None


def maktab_oquvchimi(row):
    """Maktab o'quvchisi: role=oquvchi, bog'cha bolasi emas, sinfi 1–11."""
    lp = row.get("lp") or {}
    if isinstance(lp, str):
        try:
            lp = json.loads(lp)
        except ValueError:
            lp = {}
    if row.get("role") != "oquvchi" or (lp or {}).get("role") == "bogcha":
        return None
    return sinf_of(row.get("class"))


def hafta_jadvali(rows, today):
    """Oxirgi 7 kun: har kun — nechta faoliyat, to'g'ri/jami, daftarga yozilgan, daqiqa (bo'sh kunlar ham)."""
    by = {}
    for r in rows:
        d = r["sana"]
        x = by.setdefault(d, {"faoliyat": 0, "togri": 0, "jami": 0, "yozdi": 0, "soniya": 0, "fanlar": set()})
        x["faoliyat"] += 1
        x["togri"] += int(r.get("togri") or 0)
        x["jami"] += int(r.get("jami") or 0)
        x["yozdi"] += int(r.get("yozdi") or 0)
        x["soniya"] += int(r.get("soniya") or 0)
        if r.get("fan"):
            x["fanlar"].add(r["fan"])
    out = []
    for k in range(6, -1, -1):
        d = today - timedelta(days=k)
        x = by.get(d) or {"faoliyat": 0, "togri": 0, "jami": 0, "yozdi": 0, "soniya": 0, "fanlar": set()}
        out.append({"sana": d.isoformat(), "kun": WEEKDAYS_UZ[d.weekday()], "faoliyat": x["faoliyat"], "togri": x["togri"],
                    "jami": x["jami"], "yozdi": x["yozdi"], "daqiqa": round(x["soniya"] / 60), "fanlar": sorted(x["fanlar"])[:6]})
    return out


def bajarildi_matni(ism, t, natija):
    """Ota-onaga: «✅ Ali mashqni bajardi: 8 ta so'z, 8/10 to'g'ri, daftarga 160 marta yozdi»."""
    parts = [f"{len(t.get('sozlar') or [])} ta so'z"]
    if natija.get("jami"):
        parts.append(f"{natija.get('togri', 0)}/{natija['jami']} to'g'ri")
    if natija.get("yozdi"):
        parts.append(f"daftarga {natija['yozdi']} marta yozdi")
    til = TIL_NOMI.get(t.get("til"), "")
    return f"✅ {ism} siz bergan mashqni bajardi" + (f" ({til})" if til else "") + ": " + ", ".join(parts) + "."


class Faollik(BaseModel):
    token: str = ""
    turi: str = Field(min_length=3, max_length=12)
    kod: str = Field(min_length=1, max_length=120)
    fan: str = Field(default="", max_length=120)
    til: str = Field(default="", max_length=5)
    mavzu: str = Field(default="", max_length=200)
    togri: int = Field(default=0, ge=0, le=500)
    jami: int = Field(default=0, ge=0, le=500)
    yozdi: int = Field(default=0, ge=0, le=2000)
    soniya: int = Field(default=0, ge=0, le=4 * 3600)
    sozlar: list = Field(default_factory=list, max_length=60)


class Bajardi(BaseModel):
    token: str = ""
    id: int
    togri: int = Field(default=0, ge=0, le=500)
    jami: int = Field(default=0, ge=0, le=500)
    yozdi: int = Field(default=0, ge=0, le=5000)


class Topshiriq(BaseModel):
    token: str = ""
    bola_id: int
    til: str = Field(min_length=2, max_length=5)
    sozlar: list = Field(min_length=1, max_length=MAX_SOZ)
    yozish: int = Field(default=20, ge=0, le=100)
    izoh: str = Field(default="", max_length=300)
    muddat_kun: int = Field(default=3, ge=1, le=14)


class Bekor(BaseModel):
    token: str = ""
    bola_id: int
    id: int


class Reja(BaseModel):
    token: str = ""
    bola_id: int
    dars_soni: int = Field(default=0, ge=0, le=8)          # 0 — sinfga qarab avtomatik
    dam_kunlari: list = Field(default_factory=list, max_length=7)   # JS hafta kuni: 1 — dushanba … 6 — shanba (yakshanba — «yakshanba» maydoni)
    yakshanba: str = Field(default="takror", max_length=12)


YAKSHANBA = {"takror", "dam", "dars"}   # yakshanba: yengil takror (yangi dars yo'q) | to'liq dam | odatdagi dars kuni
REJA_STANDART = {"dars_soni": 0, "dam_kunlari": [], "yakshanba": "takror"}   # yakshanba alohida sozlanadi (dam_kunlari — faqat Du–Sh)


def fan_kaliti(fan):
    """«Nemis tili (izoh: rus)» va «Nemis tili» — bitta fan."""
    return re.sub(r"\s*\(izoh:[^)]*\)\s*", "", str(fan or ""), flags=re.I).strip().lower()


def reja_toza(dars_soni=0, dam_kunlari=None, yakshanba="takror"):
    """Ota-ona yuborgan rejani tozalash: dars soni 0–8, dam kunlari — dushanba–shanba (1–6, ko'pi bilan 3 kun);
    yakshanba alohida: takror | dam | dars."""
    try:
        n = max(0, min(8, int(dars_soni)))
    except (TypeError, ValueError):
        n = 0
    kunlar = []
    for k in dam_kunlari if isinstance(dam_kunlari, (list, tuple)) else []:
        if isinstance(k, bool):
            continue
        try:
            k = int(k)
        except (TypeError, ValueError):
            continue
        if 1 <= k <= 6 and k not in kunlar:
            kunlar.append(k)
    kunlar = sorted(kunlar)[:3]
    y = yakshanba if yakshanba in YAKSHANBA else "takror"
    return {"dars_soni": n, "dam_kunlari": kunlar, "yakshanba": y}


def reja_row_json(r):
    if not r:
        return dict(REJA_STANDART)
    kunlar = r.get("dam_kunlari")
    if isinstance(kunlar, str):
        kunlar = json.loads(kunlar or "[]")
    return {**reja_toza(r.get("dars_soni"), kunlar, r.get("yakshanba")), "ozgartirildi": True}


class Sinov(BaseModel):
    token: str = ""
    bola_id: int
    til: str = Field(min_length=2, max_length=5)
    natijalar: list = Field(min_length=1, max_length=60)


def migrate(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maktab_faollik (
            user_id BIGINT NOT NULL,
            sana DATE NOT NULL,
            turi TEXT NOT NULL,
            kod TEXT NOT NULL,
            fan TEXT NOT NULL DEFAULT '',
            til TEXT NOT NULL DEFAULT '',
            mavzu TEXT NOT NULL DEFAULT '',
            togri INT NOT NULL DEFAULT 0,
            jami INT NOT NULL DEFAULT 0,
            yozdi INT NOT NULL DEFAULT 0,
            soniya INT NOT NULL DEFAULT 0,
            sozlar JSONB NOT NULL DEFAULT '[]'::jsonb,
            boshlandi_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            yangilandi_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, sana, turi, kod)
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS maktab_faollik_kun ON maktab_faollik(user_id, sana)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maktab_topshiriq (
            id BIGSERIAL PRIMARY KEY,
            ota_id BIGINT NOT NULL,
            bola_id BIGINT NOT NULL,
            til TEXT NOT NULL,
            sozlar JSONB NOT NULL,
            yozish INT NOT NULL DEFAULT 20,
            izoh TEXT NOT NULL DEFAULT '',
            muddat DATE NOT NULL,
            holat TEXT NOT NULL DEFAULT 'yangi',
            natija JSONB,
            yaratildi_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            bajarildi_at TIMESTAMPTZ
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS maktab_topshiriq_bola ON maktab_topshiriq(bola_id, holat)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maktab_ota_sinov (
            id BIGSERIAL PRIMARY KEY,
            ota_id BIGINT NOT NULL,
            bola_id BIGINT NOT NULL,
            til TEXT NOT NULL,
            togri INT NOT NULL,
            jami INT NOT NULL,
            bilmadi JSONB NOT NULL DEFAULT '[]'::jsonb,
            yaratildi_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS maktab_ota_sinov_bola ON maktab_ota_sinov(bola_id, yaratildi_at DESC)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS maktab_reja (
            user_id BIGINT PRIMARY KEY,
            dars_soni INT NOT NULL DEFAULT 0,
            dam_kunlari JSONB NOT NULL DEFAULT '[]'::jsonb,
            yakshanba TEXT NOT NULL DEFAULT 'takror',
            ota_id BIGINT,
            yangilandi_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")


def topshiriq_json(r):
    return {"id": int(r["id"]), "til": r["til"], "sozlar": r["sozlar"] if isinstance(r["sozlar"], list) else json.loads(r["sozlar"] or "[]"),
            "yozish": int(r["yozish"]), "izoh": r["izoh"] or "", "muddat": r["muddat"].isoformat() if r.get("muddat") else None,
            "holat": r["holat"], "natija": r.get("natija") if not isinstance(r.get("natija"), str) else json.loads(r["natija"]),
            "yaratildi": r["yaratildi_at"].isoformat() if r.get("yaratildi_at") else None,
            "bajarildi": r["bajarildi_at"].isoformat() if r.get("bajarildi_at") else None}


def create_router(platform):
    router = APIRouter()
    ready = {"ok": False}
    lock = threading.Lock()
    lazy = _LazyMigration("maktab_ota") if _LazyMigration else None

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

    def user_row(cur, user_id):
        rows = reja_mod._savepoint_query(cur, "maktab_user", """SELECT full_name, role, class, kabutar_learning_profile AS lp
                                                              FROM users WHERE user_id=%s""", (user_id,))
        if rows is None:   # eski baza — ta'lim profili ustuni yo'q
            rows = reja_mod._savepoint_query(cur, "maktab_user2", "SELECT full_name, role, class FROM users WHERE user_id=%s", (user_id,))
        return dict(rows[0]) if rows else {}

    def ota_huquqi(cur, ota_id, bola_id):
        if reja_mod.ota_bolami(cur, ota_id, bola_id) or reja_mod.adminmi(cur, ota_id):
            return
        raise HTTPException(403, "Bu farzand sizga ulanmagan")

    def ota_onalar(cur, bola_id):
        ids = [int(r["parent_id"]) for r in (reja_mod._savepoint_query(cur, "maktab_ota_pc", "SELECT DISTINCT parent_id FROM parent_child WHERE child_id=%s", (bola_id,)) or [])]
        for r in reja_mod._savepoint_query(cur, "maktab_ota_fp", """SELECT owner_user_id FROM kabutar_family_profiles
                                                                  WHERE profile_user_id=%s AND removed_at IS NULL""", (bola_id,)) or []:
            if int(r["owner_user_id"]) not in ids:
                ids.append(int(r["owner_user_id"]))
        return ids

    def xabar(cur, user_ids, text, kind):
        """Sayt bildirishnomasi (shu tranzaksiyada) + Telegram (fon oqimida)."""
        for uid in user_ids:
            reja_mod._savepoint_query(cur, "maktab_xabar", "INSERT INTO bildirishnomalar(user_id, matn, turi) VALUES(%s,%s,%s) RETURNING 1",
                                      (uid, text, kind))
        try:
            telegram = list(reja_mod.telegram_idlari(cur, user_ids).values())
        except Exception:   # pragma: no cover
            telegram = []
        send = getattr(platform, "_telegram_orqali_yubor", None)
        if telegram and send:
            def push():
                for tid in telegram:
                    try:
                        send(tid, text)
                    except Exception as exc:   # pragma: no cover
                        print(f"[maktab_ota telegram] {exc}", flush=True)
            threading.Thread(target=push, daemon=True).start()

    # ── O'quvchi ──
    @router.post("/api/maktab/faollik")
    def save_activity(body: Faollik, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        turi = body.turi.lower()
        if turi not in TURLAR:
            raise HTTPException(400, "Noma'lum faoliyat turi")
        til = body.til.lower() if body.til.lower() in TILLAR else ""
        day = tashkent_day(datetime.now(timezone.utc))
        ids = soz_idlari(body.sozlar)

        def run(conn, cur):
            cur.execute("""INSERT INTO maktab_faollik(user_id, sana, turi, kod, fan, til, mavzu, togri, jami, yozdi, soniya, sozlar)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                           ON CONFLICT (user_id, sana, turi, kod) DO UPDATE SET
                             fan=COALESCE(NULLIF(EXCLUDED.fan,''), maktab_faollik.fan),
                             mavzu=COALESCE(NULLIF(EXCLUDED.mavzu,''), maktab_faollik.mavzu),
                             togri=CASE WHEN EXCLUDED.jami > 0 THEN EXCLUDED.togri ELSE maktab_faollik.togri END,
                             jami=CASE WHEN EXCLUDED.jami > 0 THEN EXCLUDED.jami ELSE maktab_faollik.jami END,
                             yozdi=LEAST(100000, maktab_faollik.yozdi + EXCLUDED.yozdi),
                             soniya=LEAST(86400, maktab_faollik.soniya + EXCLUDED.soniya),
                             sozlar=(SELECT COALESCE(jsonb_agg(DISTINCT x), '[]'::jsonb) FROM jsonb_array_elements(maktab_faollik.sozlar || EXCLUDED.sozlar) x),
                             yangilandi_at=NOW()""",
                        (user_id, day, turi, matn(body.kod, 120), matn(body.fan, 120), til, matn(body.mavzu, 200),
                         min(body.togri, body.jami), body.jami, body.yozdi, body.soniya, json.dumps(ids)))
            conn.commit()
            return {"ok": True}
        return run_db(run)

    def reja_ol(cur, user_id):
        cur.execute("SELECT dars_soni, dam_kunlari, yakshanba FROM maktab_reja WHERE user_id=%s", (user_id,))
        r = cur.fetchone()
        return reja_row_json(dict(r) if r else None)

    def bugun_bajardi(cur, user_id, day):
        cur.execute("""SELECT turi, COUNT(DISTINCT kod) AS n FROM maktab_faollik WHERE user_id=%s AND sana=%s GROUP BY turi""", (user_id, day))
        return {r["turi"]: int(r["n"]) for r in cur.fetchall()}

    @router.get("/api/maktab/reja")
    def my_plan(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        day = tashkent_day(datetime.now(timezone.utc))

        def run(conn, cur):
            reja = reja_ol(cur, user_id)
            bajardi = bugun_bajardi(cur, user_id, day)
            cur.execute("""SELECT DISTINCT fan FROM maktab_faollik WHERE user_id=%s AND sana=%s AND turi='dars' AND fan <> '' LIMIT 20""", (user_id, day))
            fanlar = [r["fan"] for r in cur.fetchall()]
            conn.commit()
            return {"reja": reja, "bugun": bajardi, "fanlar": fanlar, "sana": day.isoformat(), "hafta_kuni": (day.weekday() + 1) % 7}
        return run_db(run)

    @router.get("/api/maktab/kundalik")
    def my_diary(fan: str = Query("", max_length=160), kun: int = Query(60, ge=1, le=365), token: str = None, authorization: str = Header(None)):
        """REV180: o'quvchining o'z kundaligi — fan bo'yicha: dars, test, takror, mashq, repetitor, imtihon natijalari (har qurilmada bir xil)."""
        user_id = uid_of(token, authorization)
        day = tashkent_day(datetime.now(timezone.utc))
        fk = fan_kaliti(fan)

        def run(conn, cur):
            cur.execute("""SELECT sana, turi, kod, fan, til, mavzu, togri, jami, yozdi, soniya, boshlandi_at FROM maktab_faollik
                           WHERE user_id=%s AND sana > %s ORDER BY sana DESC, boshlandi_at DESC LIMIT 600""", (user_id, day - timedelta(days=kun)))
            rows = []
            for r in cur.fetchall():
                r = dict(r)
                if fk and fan_kaliti(r["fan"]) != fk:
                    continue
                rows.append({"sana": r["sana"].isoformat(), "turi": r["turi"], "kod": r["kod"], "fan": r["fan"], "til": r["til"], "mavzu": r["mavzu"],
                             "togri": int(r["togri"] or 0), "jami": int(r["jami"] or 0), "yozdi": int(r["yozdi"] or 0), "soniya": int(r["soniya"] or 0),
                             "vaqt": r["boshlandi_at"].astimezone(TASHKENT).strftime("%H:%M") if r.get("boshlandi_at") else ""})
            conn.commit()
            return {"kundalik": rows[:300]}
        return run_db(run)

    @router.get("/api/maktab/topshiriqlar")
    def my_tasks(til: str = Query("", max_length=5), token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til.lower()

        def run(conn, cur):
            cur.execute("""SELECT * FROM maktab_topshiriq WHERE bola_id=%s AND (%s='' OR til=%s)
                             AND (holat='yangi' OR bajarildi_at > NOW() - INTERVAL '3 days') AND holat <> 'bekor'
                           ORDER BY holat='yangi' DESC, yaratildi_at DESC LIMIT 20""", (user_id, til, til))
            rows = [topshiriq_json(dict(r)) for r in cur.fetchall()]
            conn.commit()
            return {"topshiriqlar": rows}
        return run_db(run)

    @router.post("/api/maktab/topshiriq/bajardi")
    def task_done(body: Bajardi, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        now = datetime.now(timezone.utc)

        def run(conn, cur):
            cur.execute("SELECT * FROM maktab_topshiriq WHERE id=%s AND bola_id=%s FOR UPDATE", (body.id, user_id))
            r = cur.fetchone()
            if not r or r["holat"] == "bekor":
                conn.rollback()
                raise HTTPException(404, "Topshiriq topilmadi")
            t = topshiriq_json(dict(r))
            natija = {"togri": min(body.togri, body.jami), "jami": body.jami, "yozdi": body.yozdi}
            if r["holat"] == "bajarildi":   # qayta bajarsa — eng yaxshi natija saqlanadi, xabar qayta yuborilmaydi
                eski = t["natija"] or {}
                natija = {"togri": max(natija["togri"], int(eski.get("togri") or 0)), "jami": max(natija["jami"], int(eski.get("jami") or 0)),
                          "yozdi": natija["yozdi"] + int(eski.get("yozdi") or 0)}
                cur.execute("UPDATE maktab_topshiriq SET natija=%s::jsonb WHERE id=%s", (json.dumps(natija), body.id))
                conn.commit()
                return {"ok": True, "qayta": True}
            cur.execute("UPDATE maktab_topshiriq SET holat='bajarildi', natija=%s::jsonb, bajarildi_at=%s WHERE id=%s",
                        (json.dumps(natija), now, body.id))
            ism = (user_row(cur, user_id).get("full_name") or "Farzandingiz").strip()[:60] or "Farzandingiz"
            xabar(cur, [int(r["ota_id"])] + [p for p in ota_onalar(cur, user_id) if p != int(r["ota_id"])],
                  bajarildi_matni(ism, t, natija), "maktab_topshiriq")
            conn.commit()
            return {"ok": True}
        return run_db(run)

    # ── Ota-ona ──
    @router.get("/api/ota/maktab")
    def parent_view(bola_id: int, token: str = None, authorization: str = Header(None)):
        ota_id = uid_of(token, authorization)
        day = tashkent_day(datetime.now(timezone.utc))

        def run(conn, cur):
            ota_huquqi(cur, ota_id, bola_id)
            row = user_row(cur, bola_id)
            sinf = maktab_oquvchimi(row)
            if not sinf:
                conn.commit()
                return {"maktab": False}
            cur.execute("""SELECT sana, turi, kod, fan, til, mavzu, togri, jami, yozdi, soniya, sozlar, boshlandi_at
                           FROM maktab_faollik WHERE user_id=%s AND sana > %s ORDER BY sana DESC, boshlandi_at DESC LIMIT 400""",
                        (bola_id, day - timedelta(days=7)))
            rows = [dict(r) for r in cur.fetchall()]
            bugun = [{"turi": r["turi"], "fan": r["fan"], "til": r["til"], "mavzu": r["mavzu"], "togri": r["togri"], "jami": r["jami"],
                      "yozdi": r["yozdi"], "daqiqa": round((r["soniya"] or 0) / 60), "sozlar": len(r["sozlar"] or []),
                      "vaqt": r["boshlandi_at"].astimezone(TASHKENT).strftime("%H:%M") if r.get("boshlandi_at") else ""}
                     for r in rows if r["sana"] == day]
            sozlar, seen = [], set()
            for r in rows:
                for sid in r["sozlar"] or []:
                    key = (r["til"], sid)
                    if r["til"] and key not in seen:
                        seen.add(key)
                        sozlar.append({"id": sid, "til": r["til"], "kim": "bugun" if r["sana"] == day else "hafta"})
            tillar = [dict(x) for x in (reja_mod._savepoint_query(cur, "maktab_ota_til", """SELECT til, bal, togri, jami, daraja, keyingi, foiz, otildi,
                                                                       yangilangan_at FROM maktab_til_natija WHERE user_id=%s ORDER BY bal DESC""", (bola_id,)) or [])]
            for x in tillar:
                x["nom"] = TIL_NOMI.get(x["til"], x["til"])
                x["yangilangan_at"] = x["yangilangan_at"].isoformat() if x.get("yangilangan_at") else None
            cur.execute("""SELECT * FROM maktab_topshiriq WHERE bola_id=%s AND holat <> 'bekor' ORDER BY yaratildi_at DESC LIMIT 15""", (bola_id,))
            topshiriqlar = [topshiriq_json(dict(r)) for r in cur.fetchall()]
            cur.execute("""SELECT til, togri, jami, bilmadi, yaratildi_at FROM maktab_ota_sinov WHERE bola_id=%s ORDER BY yaratildi_at DESC LIMIT 5""",
                        (bola_id,))
            sinovlar = [{"til": r["til"], "togri": r["togri"], "jami": r["jami"], "bilmadi": r["bilmadi"],
                         "sana": r["yaratildi_at"].astimezone(TASHKENT).strftime("%d.%m %H:%M")} for r in cur.fetchall()]
            reja = reja_ol(cur, bola_id)
            conn.commit()
            return {"maktab": True, "reja": reja, "bola": {"user_id": bola_id, "ism": (row.get("full_name") or "").strip()[:60], "sinf": sinf},
                    "sana": day.isoformat(), "bugun": bugun, "hafta": hafta_jadvali(rows, day), "tillar": tillar,
                    "sozlar": sozlar[:SOZLAR_RO_YXAT], "topshiriqlar": topshiriqlar, "sinovlar": sinovlar}
        return run_db(run)

    @router.post("/api/ota/maktab/topshiriq")
    def give_task(body: Topshiriq, authorization: str = Header(None)):
        ota_id = uid_of(body.token, authorization)
        til = body.til.lower()
        if til not in TILLAR:
            raise HTTPException(400, "Noma'lum til")
        ids = soz_idlari(body.sozlar, MAX_SOZ)
        if not ids:
            raise HTTPException(400, "Kamida bitta so'z tanlang")
        day = tashkent_day(datetime.now(timezone.utc))

        def run(conn, cur):
            ota_huquqi(cur, ota_id, body.bola_id)
            if not maktab_oquvchimi(user_row(cur, body.bola_id)):
                conn.rollback()
                raise HTTPException(400, "Bu bo'lim maktab o'quvchilari uchun")
            cur.execute("SELECT COUNT(*) AS n FROM maktab_topshiriq WHERE bola_id=%s AND holat='yangi'", (body.bola_id,))
            if int(cur.fetchone()["n"]) >= FAOL_TOPSHIRIQ:
                conn.rollback()
                raise HTTPException(409, f"Bir vaqtda {FAOL_TOPSHIRIQ} tadan ko'p topshiriq berib bo'lmaydi — avval bajarilsin yoki bekor qiling.")
            cur.execute("""INSERT INTO maktab_topshiriq(ota_id, bola_id, til, sozlar, yozish, izoh, muddat)
                           VALUES(%s,%s,%s,%s::jsonb,%s,%s,%s) RETURNING *""",
                        (ota_id, body.bola_id, til, json.dumps(ids), yozish_soni(body.yozish), matn(body.izoh, 300),
                         day + timedelta(days=body.muddat_kun)))
            t = topshiriq_json(dict(cur.fetchone()))
            xabar(cur, [body.bola_id], f"📬 Ota-onangiz mashq berdi ({TIL_NOMI[til]}): {len(ids)} ta so'z"
                  + (f", har birini {t['yozish']} marta yozing" if t["yozish"] else "") + ". Til o'yinlari → «Topshiriq».", "maktab_topshiriq")
            conn.commit()
            return {"ok": True, "topshiriq": t}
        return run_db(run)

    @router.post("/api/ota/maktab/topshiriq/bekor")
    def cancel_task(body: Bekor, authorization: str = Header(None)):
        ota_id = uid_of(body.token, authorization)

        def run(conn, cur):
            ota_huquqi(cur, ota_id, body.bola_id)
            cur.execute("UPDATE maktab_topshiriq SET holat='bekor' WHERE id=%s AND bola_id=%s AND holat='yangi' RETURNING id", (body.id, body.bola_id))
            ok = cur.fetchone() is not None
            conn.commit()
            if not ok:
                raise HTTPException(404, "Topshiriq topilmadi yoki allaqachon bajarilgan")
            return {"ok": True}
        return run_db(run)

    @router.post("/api/ota/maktab/reja")
    def set_plan(body: Reja, authorization: str = Header(None)):
        ota_id = uid_of(body.token, authorization)
        reja = reja_toza(body.dars_soni, body.dam_kunlari, body.yakshanba)

        def run(conn, cur):
            ota_huquqi(cur, ota_id, body.bola_id)
            cur.execute("""INSERT INTO maktab_reja(user_id, dars_soni, dam_kunlari, yakshanba, ota_id, yangilandi_at)
                           VALUES(%s,%s,%s::jsonb,%s,%s,NOW())
                           ON CONFLICT (user_id) DO UPDATE SET dars_soni=EXCLUDED.dars_soni, dam_kunlari=EXCLUDED.dam_kunlari,
                             yakshanba=EXCLUDED.yakshanba, ota_id=EXCLUDED.ota_id, yangilandi_at=NOW()""",
                        (body.bola_id, reja["dars_soni"], json.dumps(reja["dam_kunlari"]), reja["yakshanba"], ota_id))
            conn.commit()
            return {"ok": True, "reja": {**reja, "ozgartirildi": True}}
        return run_db(run)

    @router.post("/api/ota/maktab/sinov")
    def parent_quiz(body: Sinov, authorization: str = Header(None)):
        ota_id = uid_of(body.token, authorization)
        til = body.til.lower()
        if til not in TILLAR:
            raise HTTPException(400, "Noma'lum til")
        bildi, bilmadi = [], []
        for x in body.natijalar:
            if not isinstance(x, dict):
                continue
            ids = soz_idlari([x.get("id")])
            if ids and ids[0] not in bildi and ids[0] not in bilmadi:
                (bildi if x.get("bildi") is True else bilmadi).append(ids[0])
        jami = len(bildi) + len(bilmadi)
        if not jami:
            raise HTTPException(400, "Natija bo'sh")

        def run(conn, cur):
            ota_huquqi(cur, ota_id, body.bola_id)
            cur.execute("""INSERT INTO maktab_ota_sinov(ota_id, bola_id, til, togri, jami, bilmadi) VALUES(%s,%s,%s,%s,%s,%s::jsonb)""",
                        (ota_id, body.bola_id, til, len(bildi), jami, json.dumps(bilmadi)))
            conn.commit()
            return {"ok": True, "togri": len(bildi), "jami": jami, "bilmadi": bilmadi}
        return run_db(run)

    return router

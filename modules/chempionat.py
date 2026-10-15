"""REV143: Bolalar ligasi — «Chempionlar ligasi» uslubidagi chempionatlar (hozir 2–7 yosh; 1–11 sinf keyin ulanadi).

Tartib:
  • Admin chempionat e'lon qiladi: yosh guruhi, o'rganiladigan til, nima bilan bellashish (til so'zlari, harakat
    o'yinlari, bilim — sanash va «ortiqchasini top»), jamoa hajmi (1 — yakka, 5, 10, 15, 20), har tur necha kun.
  • Bolalar o'zi yoziladi. Admin «Jamoalarni tuzish»ni bosadi — qancha bola bo'lsa, shuncha jamoaga teng bo'linadi
    (hajmlar farqi ko'pi bilan 1). Admin bolani boshqa jamoaga o'tkazishi, jamoa nomini o'zgartirishi mumkin.
    Boshlanish vaqti kelib admin hali tuzmagan bo'lsa — jamoalar o'zi tuziladi va chempionat o'zi boshlanadi.
  • Guruh bosqichi (3–4 jamoalik guruhlar, har kim har kim bilan; g'alaba 3, durang 1) → pley-off (1/8, 1/4, 1/2)
    → final va 3-o'rin uchun o'yin. 2 jamoa — darhol final; 3–5 jamoa — bitta guruh, keyin final (+ 3-o'rin).
  • Har tur bir necha kun ochiq — har bola o'z vaqtida o'ynaydi. Savollar bola «O'ynash»ni bosganda serverda tuziladi:
    har bolaga alohida (bir-biridan ko'chirib bo'lmaydi), lekin tarkibi va qiyinligi yosh guruhi bo'yicha hammaga bir xil.
    Javob faqat serverda tekshiriladi, savolga vaqt server soati bo'yicha, qayta o'ynab bo'lmaydi.
  • Jamoa balli = a'zolar ballari o'rtachasi (o'ynamagan a'zo — 0). Raqib balli tur tugaguncha yashirin.
  • Kuboklar: 🏆 oltin (chempion jamoa), 🥈 kumush, 🥉 bronza, ⭐ eng yaxshi o'yinchi, 🎖️ har bir o'ynagan bolaga.
Holat mijoz so'raganda «dangasa» yangilanadi (chempionat qatori qulflanadi) — fon jarayoni kerak emas.
"""
import hashlib
import json
import os
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

P = "/api/chempionat"
KOD_ALIFBO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
DARAJALAR = ("2-3 yosh", "4-5 yosh", "6-7 yosh")
FANLAR = ("soz", "harakat", "bilim")
JAMOA_HAJMLARI = (1, 5, 10, 15, 20)
IZOH_TILLARI = ("uz", "ru", "en")
KECHIKISH = 3          # tarmoq kechikishi uchun savolga qo'shimcha soniya
MAX_ISHTIROKCHI = 2000
ADMIN_KUTADI = 30      # «admin o'zi boshlaydi» tanlansa — admin unutsa, shuncha kundan keyin o'zi boshlanadi

_POOL = None


def pool():
    global _POOL
    if _POOL is None:
        with open(os.path.join(os.path.dirname(__file__), "chempionat_pool.json"), encoding="utf-8") as f:
            _POOL = json.load(f)
    return _POOL


def now():
    return datetime.now(timezone.utc)


def ms(dt):
    return int(dt.timestamp() * 1000) if dt else None


# ───────────────────────────── yosh profili ─────────────────────────────

def profil(daraja):
    """Yosh guruhi → bir o'yindagi savollar soni, variantlar soni, savol vaqti, sanash chegarasi (hammaga bir xil)."""
    if daraja == "2-3 yosh":
        return {"savol": 6, "variant": 2, "vaqt": 25, "sana": 3}
    if daraja == "4-5 yosh":
        return {"savol": 8, "variant": 3, "vaqt": 20, "sana": 5}
    return {"savol": 10, "variant": 4, "vaqt": 15, "sana": 10}


# ───────────────────────────── matnlar (izoh tilida) ─────────────────────────────

SON = {
    "uz": ["", "bitta", "ikkita", "uchta", "to‘rtta", "beshta", "oltita", "yettita", "sakkizta", "to‘qqizta", "o‘nta"],
    "ru": ["", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять", "десять"],
    "en": ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
}
GAP = {
    "sana": {"uz": "Qayerda {n}?", "ru": "Покажи, где {n}!", "en": "Where are {n}?"},
    "sana1": {"uz": "Qayerda bitta?", "ru": "Покажи, где один!", "en": "Where is one?"},
    "ortiqcha": {"uz": "Qaysi biri ortiqcha?", "ru": "Что здесь лишнее?", "en": "Which one doesn’t belong?"},
    "harakat": {"uz": "Qaysi rasm?", "ru": "Какая картинка?", "en": "Which picture?"},
}


def izoh_ol(izoh):
    return izoh if izoh in IZOH_TILLARI else "uz"


def teg(text, til):
    """Ovoz uchun til tegi: o'zbekcha tegsiz, qolganlari [ru]…[/ru] kabi."""
    if not text:
        return ""
    return text if til == "uz" else f"[{til}]{text}[/{til}]"


# ───────────────────────────── savollar ─────────────────────────────

def _turlar_ketma(fanlar, n, rng):
    """Bir o'yindagi savol turlari: tarkib hammaga bir xil (navbat bilan), tartibi aralash."""
    tur = []
    for f in fanlar:
        tur += ["sana", "ortiqcha"] if f == "bilim" else [f]
    seq = [tur[i % len(tur)] for i in range(n)]
    rng.shuffle(seq)
    return seq


def _soz_ids(pl, til):
    return [i for i in pl["sozlar"] if (pl["sozlar"][i]["w"].get(til) or "").strip()]


def _turkumi(pl):
    out = {}
    for k, ids in pl["turkum"].items():
        for i in ids:
            out.setdefault(i, k)
    return out


def savol_soz(rng, pl, til, v):
    tk = _turkumi(pl)
    ids = _soz_ids(pl, til)
    togri = rng.choice(ids)
    em = {pl["sozlar"][togri]["e"]}
    variant = [togri]
    nomzod = [i for i in ids if tk.get(i) != tk.get(togri)]   # boshqa turkumdan — chalg'ituvchi adolatli va aniq
    rng.shuffle(nomzod)
    for i in nomzod:
        if len(variant) >= v:
            break
        if pl["sozlar"][i]["e"] not in em:
            variant.append(i)
            em.add(pl["sozlar"][i]["e"])
    rng.shuffle(variant)
    soz = pl["sozlar"][togri]["w"][til]
    gap = (pl["korsat"].get(til) or "{x}").replace("{x}", soz)
    return {"tur": "soz", "til": til, "soz": soz, "gap": gap,
            "variantlar": [{"k": i, "soz": i} for i in variant], "javob": togri}


def savol_harakat(rng, pl, til, v):
    juft = [tuple(x) for x in pl["juft"]]
    ids = [i for i, h in pl["harakat"].items() if (h["s"].get(til) or "").strip()]
    togri = rng.choice(ids)
    jf = {b for a, b in juft if a == togri} | {a for a, b in juft if b == togri}
    variant = [togri]
    nomzod = [i for i in ids if i != togri and i not in jf]
    rng.shuffle(nomzod)
    for i in nomzod:
        if len(variant) >= v:
            break
        # bir xil qisqa buyruqli ikki harakat bir savolda bo'lmasin
        if all(pl["harakat"][i]["s"][til] != pl["harakat"][x]["s"][til] for x in variant):
            variant.append(i)
    rng.shuffle(variant)
    return {"tur": "harakat", "til": til, "buyruq": pl["harakat"][togri]["s"][til],
            "variantlar": [{"k": i, "harakat": i} for i in variant], "javob": togri}


def savol_sana(rng, pl, v, chegara):
    ids = [i for i in pl["turkum"].get("meva", []) + pl["turkum"].get("oyinchoq", []) + pl["turkum"].get("hayvon", [])
           if i in pl["sozlar"]]
    narsa = rng.choice(ids)
    v = min(v, chegara)
    togri = rng.randint(1, chegara)
    # yaqin sonlar: chalg'ituvchilar to'g'ri javob atrofida (har yosh uchun bir xil qiyinlik)
    yaqin = sorted(range(1, chegara + 1), key=lambda n: (abs(n - togri), rng.random()))
    sonlar = sorted(yaqin[:v])
    rng.shuffle(sonlar)
    return {"tur": "sana", "n": togri, "namuna": narsa,
            "variantlar": [{"k": str(n), "soz": narsa, "n": n} for n in sonlar], "javob": str(togri)}


def savol_ortiqcha(rng, pl, v):
    v = max(3, v)
    turkum = [k for k, ids in pl["turkum"].items() if len({pl["sozlar"][i]["e"] for i in ids if i in pl["sozlar"]}) >= v - 1]
    asos = rng.choice(turkum)
    boshqa = rng.choice([k for k in pl["turkum"] if k != asos])
    tanlov, em = [], set()
    asos_ids = [i for i in pl["turkum"][asos] if i in pl["sozlar"]]
    rng.shuffle(asos_ids)
    for i in asos_ids:
        if len(tanlov) >= v - 1:
            break
        if pl["sozlar"][i]["e"] not in em:
            tanlov.append(i)
            em.add(pl["sozlar"][i]["e"])
    tashqi = [i for i in pl["turkum"][boshqa] if i in pl["sozlar"] and pl["sozlar"][i]["e"] not in em]
    togri = rng.choice(tashqi)
    variant = tanlov + [togri]
    rng.shuffle(variant)
    return {"tur": "ortiqcha", "variantlar": [{"k": i, "soz": i} for i in variant], "javob": togri}


def savollar_tuz(daraja, til, fanlar, rng=None, pl=None):
    """Bitta bolaning bitta uchrashuvdagi savollari. Har bolaga boshqa savol, tarkib va qiyinlik — bir xil."""
    rng = rng or random.Random(secrets.randbits(64))
    pl = pl or pool()
    pr = profil(daraja)
    fanlar = [f for f in FANLAR if f in (fanlar or [])] or ["soz"]
    out, avval = [], set()
    for tur in _turlar_ketma(fanlar, pr["savol"], rng):
        for _ in range(12):   # bir o'yinda bir xil to'g'ri javob takrorlanmasin
            if tur == "soz":
                q = savol_soz(rng, pl, til, pr["variant"])
            elif tur == "harakat":
                q = savol_harakat(rng, pl, til, pr["variant"])
            elif tur == "sana":
                q = savol_sana(rng, pl, pr["variant"], pr["sana"])
            else:
                q = savol_ortiqcha(rng, pl, pr["variant"])
            if (tur, q["javob"]) not in avval:
                break
        avval.add((tur, q["javob"]))
        q["vaqt"] = pr["vaqt"]
        out.append(q)
    return out


def savol_korinish(q, izoh, i, jami, pl=None):
    """Mijozga ketadigan ko'rinish — to'g'ri javobsiz. ovoz: tegli matn (ustoz aytadi), matn: ekranda."""
    pl = pl or pool()
    l = izoh_ol(izoh)
    out = {"i": i, "jami": jami, "tur": q["tur"], "vaqt": q["vaqt"], "variantlar": q["variantlar"]}
    if q["tur"] == "soz":
        out["ovoz"] = teg(q["gap"], q["til"])
        out["matn"] = q["soz"]
        out["til"] = q["til"]
    elif q["tur"] == "harakat":
        out["ovoz"] = f"{teg(GAP['harakat'][l], l)} {teg(q['buyruq'], q['til'])}"
        out["matn"] = q["buyruq"]
        out["til"] = q["til"]
    elif q["tur"] == "sana":
        g = GAP["sana1" if q["n"] == 1 else "sana"][l].replace("{n}", SON[l][q["n"]])
        out["ovoz"] = teg(g, l)
        out["matn"] = g
        out["namuna"] = q["namuna"]
    else:
        out["ovoz"] = teg(GAP["ortiqcha"][l], l)
        out["matn"] = GAP["ortiqcha"][l]
    return out


def javob_ball(togri, sarf_ms, vaqt_s):
    """To'g'ri — 100 + tezlik uchun 0–50. Xato yoki vaqt tugasa — 0."""
    if not togri:
        return 0
    lim = max(1, int(vaqt_s * 1000))
    return 100 + round(50 * max(0.0, 1.0 - min(sarf_ms, lim) / lim))


# ───────────────────────────── jamoalar va format ─────────────────────────────

JAMOA_NOMLARI = [
    ("sherlar", "🦁"), ("burgutlar", "🦅"), ("delfinlar", "🐬"), ("yolbarslar", "🐯"), ("ayiqlar", "🐻"),
    ("tulkilar", "🦊"), ("fillar", "🐘"), ("pandalar", "🐼"), ("pingvinlar", "🐧"), ("boyogli", "🦉"),
    ("asalarilar", "🐝"), ("kapalaklar", "🦋"), ("toshbaqalar", "🐢"), ("raketalar", "🚀"), ("yulduzlar", "⭐"),
    ("kamalaklar", "🌈"), ("chaqmoqlar", "⚡"), ("kungaboqar", "🌻"), ("jirafalar", "🦒"), ("delfin2", "🐳"),
]


def jamoalarga_bol(user_ids, hajm, rng):
    """Qancha bola bo'lsa — shuncha: jamoalar soni = max(2, n // hajm), hajmlar farqi ≤ 1. Kamida 2 bola kerak."""
    ids = list(user_ids)
    n = len(ids)
    if n < 2:
        return []
    if hajm <= 1:
        return [[u] for u in ids]
    k = max(2, n // hajm)
    rng.shuffle(ids)
    out = [[] for _ in range(k)]
    for i, u in enumerate(ids):
        out[i % k].append(u)
    return out


def guruhlarga_bol(jamoa_ids, rng):
    """6 va undan ko'p jamoa — 3–4 jamoalik guruhlar (A, B, C…); 3–5 jamoa — bitta guruh; 2 — guruhsiz."""
    t = list(jamoa_ids)
    if len(t) <= 2:
        return {}
    rng.shuffle(t)
    g = 1 if len(t) <= 5 else (len(t) + 3) // 4
    out = {chr(65 + i): [] for i in range(g)}
    for i, x in enumerate(t):
        out[chr(65 + (i % g))].append(x)
    return out


def doira(jamoalar):
    """Doira usuli: har kim har kim bilan bir marta. Qaytaradi: [[(a, b), …], …] — turlar; toq bo'lsa b=None (dam)."""
    t = list(jamoalar)
    if len(t) % 2:
        t.append(None)
    n = len(t)
    turlar = []
    for r in range(n - 1):
        juft = []
        for i in range(n // 2):
            a, b = t[i], t[n - 1 - i]
            if a is None:
                a, b = b, None
            elif b is not None and r % 2:
                a, b = b, a
            juft.append((a, b))
        turlar.append(juft)
        t = [t[0]] + [t[-1]] + t[1:-1]
    return turlar


def guruh_jadvali(jamoa_ids, uchrashuvlar):
    """G'alaba 3, durang 1. Teng bo'lsa: ballar farqi, jami ball, to'g'ri javoblar, keyin id."""
    row = {j: {"jamoa_id": j, "oyin": 0, "g": 0, "d": 0, "m": 0, "ochko": 0, "ball": 0, "farq": 0, "togri": 0} for j in jamoa_ids}
    for u in uchrashuvlar:
        if u.get("holat") != "tugadi" or u.get("b_id") is None:
            continue
        a, b = u["a_id"], u["b_id"]
        if a not in row or b not in row:
            continue
        for x, y, xb, yb, xt in ((a, b, u["a_ball"], u["b_ball"], u.get("a_togri") or 0), (b, a, u["b_ball"], u["a_ball"], u.get("b_togri") or 0)):
            r = row[x]
            r["oyin"] += 1
            r["ball"] += xb
            r["farq"] += xb - yb
            r["togri"] += xt
            if xb > yb:
                r["g"] += 1
                r["ochko"] += 3
            elif xb == yb:
                r["d"] += 1
                r["ochko"] += 1
            else:
                r["m"] += 1
    out = sorted(row.values(), key=lambda r: (-r["ochko"], -r["farq"], -r["ball"], -r["togri"], r["jamoa_id"]))
    for i, r in enumerate(out, 1):
        r["orin"] = i
    return out


def tanga(seed, a, b):
    """Hamma narsa teng bo'lsa — adolatli, lekin qayta hisoblanganda o'zgarmaydigan qur'a."""
    h = hashlib.sha256(f"{seed}:{min(a, b)}:{max(a, b)}".encode()).digest()
    return min(a, b) if h[0] % 2 else max(a, b)


def golib_aniqla(u, seed, pleyoff):
    """Uchrashuv g'olibi: ko'p ball; pley-offda teng bo'lsa — ko'p to'g'ri javob, keyin qur'a. Guruhda durang — None."""
    if u.get("b_id") is None:
        return u["a_id"]
    if u["a_ball"] != u["b_ball"]:
        return u["a_id"] if u["a_ball"] > u["b_ball"] else u["b_id"]
    if not pleyoff:
        return None
    if (u.get("a_togri") or 0) != (u.get("b_togri") or 0):
        return u["a_id"] if (u.get("a_togri") or 0) > (u.get("b_togri") or 0) else u["b_id"]
    return tanga(seed, u["a_id"], u["b_id"])


def bosqich_nomi(soni):
    return {2: "final", 4: "1/2", 8: "1/4", 16: "1/8", 32: "1/16", 64: "1/32"}.get(soni, f"1/{soni // 2}")


def pleyoff_juftlari(saralangan):
    """Saralangan jamoalar (1-o'rin eng kuchli) → birinchi pley-off turi juftlari. Soni 2 ning darajasigacha
    to'ldiriladi: ortiqcha joylar eng kuchlilarga «dam» (avtomatik o'tish) bo'ladi. 1–N, 2–(N−1), … tartibi."""
    n = len(saralangan)
    if n < 2:
        return []
    size = 1
    while size < n:
        size *= 2
    slot = list(saralangan) + [None] * (size - n)
    order = [1]
    while len(order) < size:   # an'anaviy to'r tartibi: 1 va 2 faqat finalda uchrashadi
        m = len(order) * 2 + 1
        order = [x for s in order for x in (s, m - s)]
    return [(slot[order[i] - 1], slot[order[i + 1] - 1]) for i in range(0, size, 2)]


def saralash(guruhlar_jadvali):
    """Guruhlardan pley-offga: har guruhning 1- va 2-o'rinlari. G'oliblar — avval (ochko va farq bo'yicha), keyin ikkinchilar."""
    birinchi = [g[0] for g in guruhlar_jadvali if len(g) >= 1]
    ikkinchi = [g[1] for g in guruhlar_jadvali if len(g) >= 2]
    k = lambda r: (-r["ochko"], -r["farq"], -r["ball"], r["jamoa_id"])
    return [r["jamoa_id"] for r in sorted(birinchi, key=k)] + [r["jamoa_id"] for r in sorted(ikkinchi, key=k)]


# ───────────────────────────── API ─────────────────────────────

class YangiChempionat(BaseModel):
    token: Optional[str] = None
    nomi: str = Field(min_length=3, max_length=80)
    izoh: str = Field(default="", max_length=300)
    daraja: str = "4-5 yosh"
    til: str = "en"
    fanlar: list[str] = Field(default_factory=lambda: ["soz", "harakat", "bilim"])
    jamoa_hajmi: int = 5
    tur_kun: int = Field(default=1, ge=1, le=7)
    boshlanish_kun: int = Field(default=3, ge=0, le=60)   # ro'yxatdan o'tish shuncha kun ochiq; 0 — admin o'zi boshlaydi


class Token(BaseModel):
    token: Optional[str] = None


class JamoaOzgar(BaseModel):
    token: Optional[str] = None
    nomi: Optional[str] = Field(default=None, max_length=40)
    user_id: Optional[int] = None          # shu bolani bu jamoaga o'tkazish


class Javob(BaseModel):
    token: Optional[str] = None
    i: int
    tanlov: str = Field(max_length=40)
    izoh: str = "uz"


class Oyna(BaseModel):
    token: Optional[str] = None
    izoh: str = "uz"


def migrate(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chempionatlar (
            id BIGSERIAL PRIMARY KEY,
            kod TEXT UNIQUE NOT NULL,
            nomi TEXT NOT NULL,
            izoh TEXT NOT NULL DEFAULT '',
            daraja TEXT NOT NULL,
            til TEXT NOT NULL,
            fanlar JSONB NOT NULL DEFAULT '[]'::jsonb,
            jamoa_hajmi INT NOT NULL DEFAULT 5,
            tur_kun INT NOT NULL DEFAULT 1,
            boshlanish TIMESTAMPTZ NOT NULL,
            holat TEXT NOT NULL DEFAULT 'royxat',      -- royxat | jamoa | davom | tugadi | bekor
            bosqich TEXT NOT NULL DEFAULT '',
            guruhlar JSONB NOT NULL DEFAULT '{}'::jsonb,
            seed TEXT NOT NULL,
            yaratuvchi_id BIGINT,
            versiya INT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chempionat_jamoalar (
            id BIGSERIAL PRIMARY KEY,
            chempionat_id BIGINT NOT NULL REFERENCES chempionatlar(id) ON DELETE CASCADE,
            kalit TEXT NOT NULL DEFAULT '',
            nomi TEXT,
            emoji TEXT NOT NULL DEFAULT '⭐',
            guruh TEXT,
            tartib INT NOT NULL DEFAULT 0
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS chempionat_jamoalar_c ON chempionat_jamoalar(chempionat_id)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chempionat_ishtirokchilar (
            chempionat_id BIGINT NOT NULL REFERENCES chempionatlar(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL,
            ism TEXT, jins TEXT,
            jamoa_id BIGINT,
            qoshilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (chempionat_id, user_id)
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS chempionat_ishtirokchilar_u ON chempionat_ishtirokchilar(user_id)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chempionat_uchrashuvlar (
            id BIGSERIAL PRIMARY KEY,
            chempionat_id BIGINT NOT NULL REFERENCES chempionatlar(id) ON DELETE CASCADE,
            bosqich TEXT NOT NULL,                     -- guruh | 1/8 | 1/4 | 1/2 | final | 3-orin
            tur INT NOT NULL,
            guruh TEXT,
            tartib INT NOT NULL DEFAULT 0,
            a_id BIGINT NOT NULL,
            b_id BIGINT,                               -- NULL: dam (avtomatik o'tish)
            boshlanish TIMESTAMPTZ NOT NULL,
            tugash TIMESTAMPTZ NOT NULL,
            holat TEXT NOT NULL DEFAULT 'davom',       -- davom | tugadi
            a_ball INT NOT NULL DEFAULT 0, b_ball INT NOT NULL DEFAULT 0,
            a_togri INT NOT NULL DEFAULT 0, b_togri INT NOT NULL DEFAULT 0,
            golib_id BIGINT
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS chempionat_uchrashuvlar_c ON chempionat_uchrashuvlar(chempionat_id, tur)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chempionat_urinishlar (
            uchrashuv_id BIGINT NOT NULL REFERENCES chempionat_uchrashuvlar(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL,
            jamoa_id BIGINT NOT NULL,
            savollar JSONB NOT NULL,
            javoblar JSONB NOT NULL DEFAULT '[]'::jsonb,
            i INT NOT NULL DEFAULT 0,
            ball INT NOT NULL DEFAULT 0,
            togri INT NOT NULL DEFAULT 0,
            savol_boshlangan TIMESTAMPTZ NOT NULL,
            tugagan TIMESTAMPTZ,
            PRIMARY KEY (uchrashuv_id, user_id)
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chempionat_kuboklar (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            chempionat_id BIGINT NOT NULL REFERENCES chempionatlar(id) ON DELETE CASCADE,
            kubok TEXT NOT NULL,                        -- oltin | kumush | bronza | yulduz | ishtirok
            jamoa TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (user_id, chempionat_id, kubok)
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS chempionat_kuboklar_u ON chempionat_kuboklar(user_id)")


def create_router(platform):
    router = APIRouter()
    try:
        from . import curriculum_scope as scope
    except ImportError:
        from modules import curriculum_scope as scope
    ready = {"ok": False}

    def uid_of(token, authorization):
        return platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization))

    def open_db():
        conn = platform._db()
        cur = conn.cursor()
        if not ready["ok"]:
            migrate(cur)
            conn.commit()
            ready["ok"] = True
        return conn, cur

    def begin(cur, conn, fn):
        try:
            return fn()
        finally:
            cur.close()
            conn.close()

    def is_admin(cur, user_id):
        try:
            cur.execute("SAVEPOINT chemp_admin")
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
            ok = bool(cur.fetchone())
            cur.execute("RELEASE SAVEPOINT chemp_admin")
            return ok
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT chemp_admin")
            return False

    def user_of(cur, user_id):
        cur.execute("SELECT to_jsonb(u) AS j FROM users u WHERE user_id=%s", (user_id,))
        row = (cur.fetchone() or {}).get("j") or {}
        ism = (str(row.get("full_name") or "Bola").strip()[:40] or "Bola")
        daraja = scope.preschool_learner(row) or ""
        return ism, row.get("jins"), daraja

    def admin_kerak(cur, user_id):
        if not is_admin(cur, user_id):
            raise HTTPException(403, "Buni faqat admin qiladi")

    def load(cur, kod, lock=False):
        cur.execute("SELECT * FROM chempionatlar WHERE kod=%s" + (" FOR UPDATE" if lock else ""), (str(kod or "").strip().upper()[:12],))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Chempionat topilmadi")
        return dict(row)

    def store(cur, c):
        c["versiya"] += 1
        cur.execute("""UPDATE chempionatlar SET holat=%s, bosqich=%s, guruhlar=%s::jsonb, boshlanish=%s, versiya=%s, updated_at=NOW()
                       WHERE id=%s""", (c["holat"], c["bosqich"], json.dumps(c["guruhlar"]), c["boshlanish"], c["versiya"], c["id"]))

    def jamoalar_of(cur, c):
        cur.execute("SELECT * FROM chempionat_jamoalar WHERE chempionat_id=%s ORDER BY tartib, id", (c["id"],))
        return [dict(r) for r in cur.fetchall()]

    def ishtirokchilar_of(cur, c):
        cur.execute("SELECT * FROM chempionat_ishtirokchilar WHERE chempionat_id=%s ORDER BY qoshilgan_at, user_id", (c["id"],))
        return [dict(r) for r in cur.fetchall()]

    def uchrashuvlar_of(cur, c):
        cur.execute("SELECT * FROM chempionat_uchrashuvlar WHERE chempionat_id=%s ORDER BY tur, tartib, id", (c["id"],))
        return [dict(r) for r in cur.fetchall()]

    # — jamoalar tuzish —
    def jamoa_tuz(cur, c):
        odam = ishtirokchilar_of(cur, c)
        rng = random.Random(f"{c['seed']}:jamoa:{c['versiya']}")
        guruh = jamoalarga_bol([p["user_id"] for p in odam], int(c["jamoa_hajmi"]), rng)
        cur.execute("UPDATE chempionat_ishtirokchilar SET jamoa_id=NULL WHERE chempionat_id=%s", (c["id"],))
        cur.execute("DELETE FROM chempionat_jamoalar WHERE chempionat_id=%s", (c["id"],))
        if not guruh:
            return 0
        nomlar = list(JAMOA_NOMLARI)
        rng.shuffle(nomlar)
        ism = {p["user_id"]: p["ism"] for p in odam}
        for t, aza in enumerate(guruh):
            kalit, emoji = nomlar[t % len(nomlar)]
            nomi = ism.get(aza[0]) if int(c["jamoa_hajmi"]) <= 1 else (None if t < len(nomlar) else f"{t + 1}")
            cur.execute("""INSERT INTO chempionat_jamoalar(chempionat_id,kalit,nomi,emoji,tartib) VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                        (c["id"], kalit, nomi, emoji, t))
            jid = cur.fetchone()["id"]
            cur.execute("UPDATE chempionat_ishtirokchilar SET jamoa_id=%s WHERE chempionat_id=%s AND user_id=ANY(%s)", (jid, c["id"], aza))
        return len(guruh)

    def uchrashuv_qosh(cur, c, bosqich, tur, juftlar, bosh, guruh=None):
        tug = bosh + timedelta(days=int(c["tur_kun"]))
        for k, (a, b) in enumerate(juftlar):
            if a is None and b is None:
                continue
            if a is None:
                a, b = b, None
            if b is None:   # dam — avtomatik o'tish (guruhda — o'yin yo'q)
                if bosqich == "guruh":
                    continue
                cur.execute("""INSERT INTO chempionat_uchrashuvlar(chempionat_id,bosqich,tur,guruh,tartib,a_id,b_id,boshlanish,tugash,holat,golib_id)
                               VALUES(%s,%s,%s,%s,%s,%s,NULL,%s,%s,'tugadi',%s)""", (c["id"], bosqich, tur, guruh, k, a, bosh, tug, a))
                continue
            cur.execute("""INSERT INTO chempionat_uchrashuvlar(chempionat_id,bosqich,tur,guruh,tartib,a_id,b_id,boshlanish,tugash)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (c["id"], bosqich, tur, guruh, k, a, b, bosh, tug))
        return tug

    def boshlash(cur, c, at):
        """Guruhlar va guruh bosqichi taqvimi (yoki 2 jamoa bo'lsa — darhol final)."""
        jam = jamoalar_of(cur, c)
        if len(jam) < 2:
            c["holat"] = "bekor"
            return
        rng = random.Random(f"{c['seed']}:guruh")
        ids = [j["id"] for j in jam]
        c["boshlanish"] = at
        D = timedelta(days=int(c["tur_kun"]))
        if len(ids) == 2:
            c["guruhlar"] = {}
            c["bosqich"] = "final"
            uchrashuv_qosh(cur, c, "final", 1, [(ids[0], ids[1])], at)
        else:
            g = guruhlarga_bol(ids, rng)
            c["guruhlar"] = g
            c["bosqich"] = "guruh"
            for nom, aza in g.items():
                cur.execute("UPDATE chempionat_jamoalar SET guruh=%s WHERE id=ANY(%s)", (nom, aza))
                for r, juft in enumerate(doira(aza)):
                    uchrashuv_qosh(cur, c, "guruh", r + 1, juft, at + D * r, guruh=nom)
        c["holat"] = "davom"

    def yakunla(cur, c, u):
        """Uchrashuv tugadi: jamoa balli — a'zolar o'rtachasi (o'ynamagan — 0)."""
        if u["b_id"] is None:
            return
        cur.execute("""SELECT i.jamoa_id, COUNT(*) AS soni,
                              COALESCE(SUM(r.ball),0)::int AS ball, COALESCE(SUM(r.togri),0)::int AS togri
                       FROM chempionat_ishtirokchilar i
                       LEFT JOIN chempionat_urinishlar r ON r.uchrashuv_id=%s AND r.user_id=i.user_id
                       WHERE i.chempionat_id=%s AND i.jamoa_id=ANY(%s) GROUP BY i.jamoa_id""",
                    (u["id"], c["id"], [u["a_id"], u["b_id"]]))
        by = {r["jamoa_id"]: r for r in cur.fetchall()}
        for side in ("a", "b"):
            r = by.get(u[f"{side}_id"]) or {"soni": 1, "ball": 0, "togri": 0}
            u[f"{side}_ball"] = round(r["ball"] / max(1, r["soni"]))
            u[f"{side}_togri"] = int(r["togri"])
        u["golib_id"] = golib_aniqla(u, c["seed"], u["bosqich"] != "guruh")
        u["holat"] = "tugadi"
        cur.execute("""UPDATE chempionat_uchrashuvlar SET holat='tugadi', a_ball=%s, b_ball=%s, a_togri=%s, b_togri=%s, golib_id=%s
                       WHERE id=%s""", (u["a_ball"], u["b_ball"], u["a_togri"], u["b_togri"], u["golib_id"], u["id"]))

    def guruh_jadvallari(c, jam, uch):
        out = []
        for nom, aza in sorted((c.get("guruhlar") or {}).items()):
            out.append((nom, guruh_jadvali(aza, [u for u in uch if u["bosqich"] == "guruh" and u.get("guruh") == nom])))
        return out

    def progress(cur, c, at):
        changed = False
        if c["holat"] in ("royxat", "jamoa") and at >= c["boshlanish"]:
            if c["holat"] == "royxat":
                jamoa_tuz(cur, c)
            boshlash(cur, c, at)
            changed = True
        if c["holat"] != "davom":
            return changed
        for _ in range(8):   # bir so'rovda bir necha bosqich o'tib ketgan bo'lishi mumkin
            uch = uchrashuvlar_of(cur, c)
            for u in uch:
                if u["holat"] != "tugadi" and u["tugash"] <= at:
                    yakunla(cur, c, u)
                    changed = True
            joriy = [u for u in uch if u["bosqich"] == c["bosqich"] or (c["bosqich"] == "final" and u["bosqich"] == "3-orin")]
            if not joriy or any(u["holat"] != "tugadi" for u in joriy):
                return changed
            if not keyingi_bosqich(cur, c, uch, at):
                return True
            changed = True
        return changed

    def keyingi_bosqich(cur, c, uch, at):
        """Joriy bosqich tugadi → keyingisini tuzadi. Final tugasa — kuboklar va «tugadi». Davom etsa True."""
        jam = jamoalar_of(cur, c)
        oxirgi_tugash = max((u["tugash"] for u in uch), default=at)
        bosh = max(oxirgi_tugash, at) if oxirgi_tugash > at else at
        tur = max((u["tur"] for u in uch), default=0) + 1
        if c["bosqich"] == "guruh":
            jad = [j for _, j in guruh_jadvallari(c, jam, uch)]
            if len(jad) == 1:   # 3–5 jamoa: 1–2 finalda, 3–4 uchinchi o'rin uchun
                t = jad[0]
                c["bosqich"] = "final"
                uchrashuv_qosh(cur, c, "final", tur, [(t[0]["jamoa_id"], t[1]["jamoa_id"])], bosh)
                if len(t) >= 4:
                    uchrashuv_qosh(cur, c, "3-orin", tur, [(t[2]["jamoa_id"], t[3]["jamoa_id"])], bosh)
                return True
            sar = saralash(jad)
            juft = pleyoff_juftlari(sar)
            c["bosqich"] = bosqich_nomi(len(juft) * 2)
            uchrashuv_qosh(cur, c, c["bosqich"], tur, juft, bosh)
            return True
        if c["bosqich"] == "final":
            kuboklar(cur, c, jam, uch)
            c["holat"] = "tugadi"
            return False
        joriy = sorted([u for u in uch if u["bosqich"] == c["bosqich"]], key=lambda u: u["tartib"])
        golib = [u["golib_id"] for u in joriy]
        if len(golib) == 2:   # yarim final tugadi → final va 3-o'rin
            yutqazgan = [u["a_id"] if u["golib_id"] == u["b_id"] else u["b_id"] for u in joriy]
            c["bosqich"] = "final"
            uchrashuv_qosh(cur, c, "final", tur, [(golib[0], golib[1])], bosh)
            if all(x is not None for x in yutqazgan):
                uchrashuv_qosh(cur, c, "3-orin", tur, [(yutqazgan[0], yutqazgan[1])], bosh)
            return True
        c["bosqich"] = bosqich_nomi(len(golib))
        uchrashuv_qosh(cur, c, c["bosqich"], tur, [(golib[i], golib[i + 1]) for i in range(0, len(golib), 2)], bosh)
        return True

    def kuboklar(cur, c, jam, uch):
        nom = {j["id"]: (j.get("nomi") or j["kalit"]) for j in jam}
        fin = next((u for u in uch if u["bosqich"] == "final"), None)
        berish = []
        if fin:
            g = fin["golib_id"]
            berish.append(("oltin", g))
            if fin["b_id"] is not None:
                berish.append(("kumush", fin["a_id"] if g == fin["b_id"] else fin["b_id"]))
        uchinchi = next((u for u in uch if u["bosqich"] == "3-orin"), None)
        if uchinchi:
            berish.append(("bronza", uchinchi["golib_id"]))
        elif len(jam) == 3 and c.get("guruhlar"):
            t = guruh_jadvallari(c, jam, uch)[0][1]
            berish.append(("bronza", t[2]["jamoa_id"]))
        for kubok, jid in berish:
            if jid is None:
                continue
            cur.execute("""INSERT INTO chempionat_kuboklar(user_id,chempionat_id,kubok,jamoa)
                           SELECT user_id, %s, %s, %s FROM chempionat_ishtirokchilar WHERE chempionat_id=%s AND jamoa_id=%s
                           ON CONFLICT DO NOTHING""", (c["id"], kubok, nom.get(jid), c["id"], jid))
        # ⭐ eng yaxshi o'yinchi (eng ko'p jami ball) va 🎖️ har bir o'ynagan bolaga
        cur.execute("""SELECT r.user_id, SUM(r.ball)::int AS ball FROM chempionat_urinishlar r
                       JOIN chempionat_uchrashuvlar u ON u.id=r.uchrashuv_id WHERE u.chempionat_id=%s GROUP BY r.user_id""", (c["id"],))
        ballar = [dict(r) for r in cur.fetchall()]
        eng = max((r["ball"] for r in ballar), default=0)
        for r in ballar:
            cur.execute("""INSERT INTO chempionat_kuboklar(user_id,chempionat_id,kubok) VALUES(%s,%s,'ishtirok') ON CONFLICT DO NOTHING""",
                        (r["user_id"], c["id"]))
            if eng > 0 and r["ball"] == eng:
                cur.execute("""INSERT INTO chempionat_kuboklar(user_id,chempionat_id,kubok) VALUES(%s,%s,'yulduz') ON CONFLICT DO NOTHING""",
                            (r["user_id"], c["id"]))

    # — ko'rinishlar —
    def karta(c, soni=None, men=False):
        return {"kod": c["kod"], "nomi": c["nomi"], "izoh": c["izoh"], "daraja": c["daraja"], "til": c["til"],
                "fanlar": c["fanlar"], "jamoa_hajmi": c["jamoa_hajmi"], "tur_kun": c["tur_kun"], "holat": c["holat"],
                "bosqich": c["bosqich"], "boshlanish": ms(c["boshlanish"]), "ishtirokchilar": soni, "qatnashaman": men}

    def jamoa_k(j):
        return {"id": j["id"], "kalit": j["kalit"], "nomi": j.get("nomi"), "emoji": j["emoji"], "guruh": j.get("guruh")}

    def tafsilot(cur, c, user_id, at, admin):
        odam = ishtirokchilar_of(cur, c)
        jam = jamoalar_of(cur, c)
        uch = uchrashuvlar_of(cur, c)
        me = next((p for p in odam if int(p["user_id"]) == user_id), None)
        out = karta(c, len(odam), bool(me))
        out.update({"server_now": ms(at), "versiya": c["versiya"], "admin": admin, "profil": profil(c["daraja"])})
        aza = {}
        for p in odam:
            aza.setdefault(p["jamoa_id"], []).append({"user_id": p["user_id"], "ism": p["ism"], "jins": p["jins"],
                                                      "men": int(p["user_id"]) == user_id})
        out["jamoalar"] = [jamoa_k(j) | {"azolar": aza.get(j["id"], [])} for j in jam]
        if admin:
            out["jamoasizlar"] = aza.get(None, [])
        out["mening_jamoam"] = me["jamoa_id"] if me else None
        out["guruhlar"] = [{"nomi": nom, "jadval": t} for nom, t in guruh_jadvallari(c, jam, uch)]

        cur.execute("""SELECT r.uchrashuv_id, r.user_id, r.tugagan IS NOT NULL AS tugadi, r.ball, r.togri
                       FROM chempionat_urinishlar r JOIN chempionat_uchrashuvlar u ON u.id=r.uchrashuv_id WHERE u.chempionat_id=%s""", (c["id"],))
        ur = [dict(r) for r in cur.fetchall()]
        jamoasi = {int(p["user_id"]): p["jamoa_id"] for p in odam}
        oynadi = {}
        for r in ur:
            if r["tugadi"]:
                key = (r["uchrashuv_id"], jamoasi.get(int(r["user_id"])))
                oynadi[key] = oynadi.get(key, 0) + 1

        def u_k(u):
            yopiq = u["holat"] != "tugadi"
            o = {"id": u["id"], "bosqich": u["bosqich"], "tur": u["tur"], "guruh": u.get("guruh"), "a": u["a_id"], "b": u["b_id"],
                 "boshlanish": ms(u["boshlanish"]), "tugash": ms(u["tugash"]), "holat": u["holat"],
                 "golib": u["golib_id"], "tartib": u["tartib"]}
            if yopiq:   # raqib natijasi tur tugaguncha yashirin — faqat nechta bola o'ynab bo'lgani
                o["oynadi"] = {str(s): oynadi.get((u["id"], s), 0) for s in (u["a_id"], u["b_id"]) if s is not None}
            else:
                o.update({"a_ball": u["a_ball"], "b_ball": u["b_ball"]})
            return o
        out["uchrashuvlar"] = [u_k(u) for u in uch]
        # mening joriy uchrashuvim
        joriy = None
        if me and me["jamoa_id"]:
            for u in uch:
                if u["holat"] != "tugadi" and me["jamoa_id"] in (u["a_id"], u["b_id"]) and u["boshlanish"] <= at:
                    joriy = u
                    break
        if joriy:
            mine = next((r for r in ur if r["uchrashuv_id"] == joriy["id"] and int(r["user_id"]) == user_id), None)
            out["mening_oyinim"] = {"uchrashuv": joriy["id"], "tugash": ms(joriy["tugash"]),
                                    "holat": "tugadi" if mine and mine["tugadi"] else ("davom" if mine else "yangi"),
                                    "ball": mine["ball"] if mine and mine["tugadi"] else None}
        else:
            keyin = next((u for u in uch if me and u["holat"] != "tugadi" and me["jamoa_id"] in (u["a_id"], u["b_id"])), None)
            out["mening_oyinim"] = None
            out["keyingi_oyin"] = ms(keyin["boshlanish"]) if keyin else None
        # mening shu chempionatdagi ballarim
        out["mening_ballarim"] = sum(int(r["ball"] or 0) for r in ur if int(r["user_id"]) == user_id and r["tugadi"])
        if c["holat"] == "tugadi":
            cur.execute("""SELECT k.kubok, k.jamoa, k.user_id, i.ism FROM chempionat_kuboklar k
                           LEFT JOIN chempionat_ishtirokchilar i ON i.chempionat_id=k.chempionat_id AND i.user_id=k.user_id
                           WHERE k.chempionat_id=%s AND k.kubok<>'ishtirok' ORDER BY k.kubok, i.ism""", (c["id"],))
            out["kuboklar"] = [dict(r) for r in cur.fetchall()]
        return out

    # — o'yin (urinish) —
    def joriy_uchrashuv(cur, c, user_id, at):
        cur.execute("SELECT jamoa_id FROM chempionat_ishtirokchilar WHERE chempionat_id=%s AND user_id=%s", (c["id"], user_id))
        me = cur.fetchone()
        if not me or not me["jamoa_id"]:
            raise HTTPException(409, "Siz bu chempionatda jamoaga kiritilmagansiz")
        cur.execute("""SELECT * FROM chempionat_uchrashuvlar WHERE chempionat_id=%s AND holat<>'tugadi' AND boshlanish<=%s AND tugash>%s
                       AND (a_id=%s OR b_id=%s) ORDER BY tur LIMIT 1""", (c["id"], at, at, me["jamoa_id"], me["jamoa_id"]))
        u = cur.fetchone()
        if not u:
            raise HTTPException(409, "Hozir jamoangizning o'yini yo'q. Keyingi tur boshlanishini kuting.")
        return dict(u), me["jamoa_id"]

    def urinish_holati(c, r, izoh, at, pl):
        """Vaqti o'tgan savollarni xato deb belgilaydi; joriy savol yoki yakunni qaytaradi. O'zgargan bo'lsa r['_ozg']."""
        sav = r["savollar"]
        while r["tugagan"] is None and r["i"] < len(sav):
            q = sav[r["i"]]
            if at - r["savol_boshlangan"] <= timedelta(seconds=q["vaqt"] + KECHIKISH):
                break
            r["javoblar"].append({"i": r["i"], "tanlov": None, "togri": False, "ball": 0})
            r["i"] += 1
            r["savol_boshlangan"] = at
            r["_ozg"] = True
        if r["tugagan"] is None and r["i"] >= len(sav):
            r["tugagan"] = at
            r["_ozg"] = True
        if r["tugagan"] is not None:
            return {"tugadi": True, "ball": r["ball"], "togri": r["togri"], "jami": len(sav)}
        q = sav[r["i"]]
        qolgan = q["vaqt"] - (at - r["savol_boshlangan"]).total_seconds()
        return {"tugadi": False, "savol": savol_korinish(q, izoh, r["i"], len(sav), pl), "qolgan": max(1, round(qolgan)),
                "ball": r["ball"], "togri": r["togri"]}

    def urinish_saqla(cur, r):
        cur.execute("""UPDATE chempionat_urinishlar SET javoblar=%s::jsonb, i=%s, ball=%s, togri=%s, savol_boshlangan=%s, tugagan=%s
                       WHERE uchrashuv_id=%s AND user_id=%s""",
                    (json.dumps(r["javoblar"]), r["i"], r["ball"], r["togri"], r["savol_boshlangan"], r["tugagan"], r["uchrashuv_id"], r["user_id"]))

    # ───── marshrutlar ─────
    @router.get(P)
    def royxat(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            cur.execute("""SELECT c.*, (SELECT COUNT(*) FROM chempionat_ishtirokchilar p WHERE p.chempionat_id=c.id) AS soni,
                                  EXISTS(SELECT 1 FROM chempionat_ishtirokchilar p WHERE p.chempionat_id=c.id AND p.user_id=%s) AS men
                           FROM chempionatlar c
                           WHERE c.holat IN ('royxat','jamoa','davom') OR c.updated_at > %s
                              OR EXISTS(SELECT 1 FROM chempionat_ishtirokchilar p WHERE p.chempionat_id=c.id AND p.user_id=%s)
                           ORDER BY CASE c.holat WHEN 'davom' THEN 0 WHEN 'jamoa' THEN 1 WHEN 'royxat' THEN 2 ELSE 3 END, c.boshlanish DESC
                           LIMIT 60""", (user_id, at - timedelta(days=14), user_id))
            rows = [dict(r) for r in cur.fetchall()]
            admin = is_admin(cur, user_id)
            _, _, daraja = user_of(cur, user_id)
            cur.execute("""SELECT k.kubok, k.jamoa, c.nomi, c.kod, c.daraja, k.created_at FROM chempionat_kuboklar k
                           JOIN chempionatlar c ON c.id=k.chempionat_id WHERE k.user_id=%s ORDER BY k.created_at DESC""", (user_id,))
            kub = [{**dict(r), "created_at": ms(r["created_at"])} for r in cur.fetchall()]
            conn.commit()
            return {"chempionatlar": [karta(r, int(r["soni"]), bool(r["men"])) for r in rows], "admin": admin, "daraja": daraja,
                    "kuboklar": kub, "server_now": ms(at), "darajalar": list(DARAJALAR), "hajmlar": list(JAMOA_HAJMLARI),
                    "tillar": pool()["tillar"]}
        return begin(cur, conn, run)

    @router.post(P)
    def yarat(body: YangiChempionat, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        if body.daraja not in DARAJALAR:
            raise HTTPException(422, "Yosh guruhini tanlang")
        if body.til not in pool()["tillar"]:
            raise HTTPException(422, "Tilni tanlang")
        if body.jamoa_hajmi not in JAMOA_HAJMLARI:
            raise HTTPException(422, "Jamoa hajmi: 1, 5, 10, 15 yoki 20")
        fanlar = [f for f in FANLAR if f in body.fanlar]
        if not fanlar:
            raise HTTPException(422, "Kamida bitta bellashuv turini tanlang")
        conn, cur = open_db()

        def run():
            admin_kerak(cur, user_id)
            for _ in range(10):
                kod = "C" + "".join(secrets.choice(KOD_ALIFBO) for _ in range(5))
                cur.execute("SELECT 1 FROM chempionatlar WHERE kod=%s", (kod,))
                if not cur.fetchone():
                    break
            cur.execute("""INSERT INTO chempionatlar(kod,nomi,izoh,daraja,til,fanlar,jamoa_hajmi,tur_kun,boshlanish,seed,yaratuvchi_id)
                           VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s)""",
                        (kod, body.nomi.strip(), body.izoh.strip(), body.daraja, body.til, json.dumps(fanlar), body.jamoa_hajmi,
                         body.tur_kun, at + timedelta(days=body.boshlanish_kun or ADMIN_KUTADI), secrets.token_hex(16), user_id))
            conn.commit()
            return {"kod": kod}
        return begin(cur, conn, run)

    @router.get(P + "/{kod}")
    def korish(kod: str, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            c = load(cur, kod, lock=True)
            if progress(cur, c, at):
                store(cur, c)
            out = tafsilot(cur, c, user_id, at, is_admin(cur, user_id))
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/yozil")
    def yozil(kod: str, body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            c = load(cur, kod, lock=True)
            admin = is_admin(cur, user_id)
            if c["holat"] != "royxat":
                raise HTTPException(409, "Ro'yxatdan o'tish yopilgan")
            ism, jins, daraja = user_of(cur, user_id)
            if not admin and daraja != c["daraja"]:
                raise HTTPException(409, f"Bu chempionat {c['daraja']} bolalar uchun")
            cur.execute("SELECT COUNT(*) AS n FROM chempionat_ishtirokchilar WHERE chempionat_id=%s", (c["id"],))
            if cur.fetchone()["n"] >= MAX_ISHTIROKCHI:
                raise HTTPException(409, "Joy qolmadi")
            cur.execute("""INSERT INTO chempionat_ishtirokchilar(chempionat_id,user_id,ism,jins) VALUES(%s,%s,%s,%s)
                           ON CONFLICT(chempionat_id,user_id) DO UPDATE SET ism=EXCLUDED.ism""", (c["id"], user_id, ism, jins))
            store(cur, c)
            out = tafsilot(cur, c, user_id, at, admin)
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/chiq")
    def chiq(kod: str, body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            c = load(cur, kod, lock=True)
            if c["holat"] != "royxat":
                raise HTTPException(409, "Jamoalar tuzilgan — endi chiqib bo'lmaydi. Admin bilan bog'laning.")
            cur.execute("DELETE FROM chempionat_ishtirokchilar WHERE chempionat_id=%s AND user_id=%s", (c["id"], user_id))
            store(cur, c)
            out = tafsilot(cur, c, user_id, at, is_admin(cur, user_id))
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/jamoalar")
    def jamoalar(kod: str, body: Token, authorization: str = Header(None)):
        """Admin: ro'yxatni yopib jamoalarni (qayta) tuzadi."""
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            admin_kerak(cur, user_id)
            c = load(cur, kod, lock=True)
            if c["holat"] not in ("royxat", "jamoa"):
                raise HTTPException(409, "Chempionat boshlangan")
            if jamoa_tuz(cur, c) < 2:
                raise HTTPException(409, "Jamoa tuzish uchun kamida 2 bola yozilishi kerak")
            c["holat"] = "jamoa"
            store(cur, c)
            out = tafsilot(cur, c, user_id, at, True)
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/royxat_och")
    def royxat_och(kod: str, body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            admin_kerak(cur, user_id)
            c = load(cur, kod, lock=True)
            if c["holat"] != "jamoa":
                raise HTTPException(409, "Ro'yxat allaqachon ochiq yoki chempionat boshlangan")
            cur.execute("UPDATE chempionat_ishtirokchilar SET jamoa_id=NULL WHERE chempionat_id=%s", (c["id"],))
            cur.execute("DELETE FROM chempionat_jamoalar WHERE chempionat_id=%s", (c["id"],))
            c["holat"] = "royxat"
            store(cur, c)
            out = tafsilot(cur, c, user_id, at, True)
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/jamoa/{jid}")
    def jamoa_ozgar(kod: str, jid: int, body: JamoaOzgar, authorization: str = Header(None)):
        """Admin: jamoa nomini o'zgartirish yoki bolani shu jamoaga o'tkazish (boshlanguncha)."""
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            admin_kerak(cur, user_id)
            c = load(cur, kod, lock=True)
            cur.execute("SELECT * FROM chempionat_jamoalar WHERE id=%s AND chempionat_id=%s", (jid, c["id"]))
            if not cur.fetchone():
                raise HTTPException(404, "Jamoa topilmadi")
            if body.nomi is not None:
                cur.execute("UPDATE chempionat_jamoalar SET nomi=%s WHERE id=%s", (body.nomi.strip()[:40] or None, jid))
            if body.user_id is not None:
                if c["holat"] != "jamoa":
                    raise HTTPException(409, "Bolalarni faqat chempionat boshlanguncha o'tkazish mumkin")
                cur.execute("UPDATE chempionat_ishtirokchilar SET jamoa_id=%s WHERE chempionat_id=%s AND user_id=%s",
                            (jid, c["id"], body.user_id))
                cur.execute("""DELETE FROM chempionat_jamoalar j WHERE j.chempionat_id=%s
                               AND NOT EXISTS(SELECT 1 FROM chempionat_ishtirokchilar i WHERE i.jamoa_id=j.id)""", (c["id"],))
            store(cur, c)
            out = tafsilot(cur, c, user_id, at, True)
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/boshla")
    def boshla(kod: str, body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            admin_kerak(cur, user_id)
            c = load(cur, kod, lock=True)
            if c["holat"] == "royxat":
                if jamoa_tuz(cur, c) < 2:
                    raise HTTPException(409, "Boshlash uchun kamida 2 bola kerak")
            elif c["holat"] != "jamoa":
                raise HTTPException(409, "Chempionat allaqachon boshlangan")
            boshlash(cur, c, at)
            store(cur, c)
            out = tafsilot(cur, c, user_id, at, True)
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/bekor")
    def bekor(kod: str, body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            admin_kerak(cur, user_id)
            c = load(cur, kod, lock=True)
            if c["holat"] == "tugadi":
                raise HTTPException(409, "Chempionat tugagan")
            c["holat"] = "bekor"
            store(cur, c)
            out = tafsilot(cur, c, user_id, at, True)
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/oyna")
    def oyna(kod: str, body: Oyna, authorization: str = Header(None)):
        """Joriy uchrashuvdagi o'yinni boshlash yoki davom ettirish. Savollar shu yerda (birinchi marta) tuziladi."""
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()
        pl = pool()

        def run():
            c = load(cur, kod, lock=True)
            if progress(cur, c, at):
                store(cur, c)
                conn.commit()
            if c["holat"] != "davom":
                raise HTTPException(409, "Chempionat hozir davom etmayapti")
            u, jamoa_id = joriy_uchrashuv(cur, c, user_id, at)
            cur.execute("SELECT * FROM chempionat_urinishlar WHERE uchrashuv_id=%s AND user_id=%s FOR UPDATE", (u["id"], user_id))
            r = cur.fetchone()
            if not r:
                sav = savollar_tuz(c["daraja"], c["til"], c["fanlar"], random.Random(secrets.randbits(64)), pl)
                cur.execute("""INSERT INTO chempionat_urinishlar(uchrashuv_id,user_id,jamoa_id,savollar,savol_boshlangan)
                               VALUES(%s,%s,%s,%s::jsonb,%s) RETURNING *""", (u["id"], user_id, jamoa_id, json.dumps(sav), at))
                r = cur.fetchone()
            r = dict(r)
            out = urinish_holati(c, r, body.izoh, at, pl)
            if r.get("_ozg"):
                urinish_saqla(cur, r)
            conn.commit()
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/javob")
    def javob(kod: str, body: Javob, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()
        pl = pool()

        def run():
            c = load(cur, kod)
            cur.execute("""SELECT r.* FROM chempionat_urinishlar r JOIN chempionat_uchrashuvlar u ON u.id=r.uchrashuv_id
                           WHERE u.chempionat_id=%s AND r.user_id=%s AND r.tugagan IS NULL AND u.holat<>'tugadi' AND u.tugash>%s
                           ORDER BY u.tur LIMIT 1 FOR UPDATE OF r""", (c["id"], user_id, at))
            r = cur.fetchone()
            if not r:
                raise HTTPException(409, "Faol o'yin topilmadi")
            r = dict(r)
            natija = None
            if body.i == r["i"] and r["i"] < len(r["savollar"]):
                q = r["savollar"][r["i"]]
                sarf = (at - r["savol_boshlangan"]).total_seconds()
                vaqtida = sarf <= q["vaqt"] + KECHIKISH
                togri = vaqtida and str(body.tanlov) == str(q["javob"])
                ball = javob_ball(togri, int(sarf * 1000), q["vaqt"])
                r["javoblar"].append({"i": r["i"], "tanlov": body.tanlov, "togri": togri, "ball": ball})
                r["ball"] += ball
                r["togri"] += int(togri)
                r["i"] += 1
                r["savol_boshlangan"] = at
                r["_ozg"] = True
                natija = {"togri": togri, "javob": q["javob"], "ball": ball, "vaqtida": vaqtida}
            out = urinish_holati(c, r, body.izoh, at, pl)
            if r.get("_ozg"):
                urinish_saqla(cur, r)
            conn.commit()
            out["natija"] = natija
            return out
        return begin(cur, conn, run)

    @router.get(P + "/kuboklar/mening")
    def kuboklarim(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        conn, cur = open_db()

        def run():
            cur.execute("""SELECT k.kubok, k.jamoa, c.nomi, c.kod, c.daraja, k.created_at FROM chempionat_kuboklar k
                           JOIN chempionatlar c ON c.id=k.chempionat_id WHERE k.user_id=%s ORDER BY k.created_at DESC""", (user_id,))
            out = [{**dict(r), "created_at": ms(r["created_at"])} for r in cur.fetchall()]
            conn.commit()
            return {"kuboklar": out}
        return begin(cur, conn, run)

    return router

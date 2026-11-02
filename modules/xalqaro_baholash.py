"""REV260: «Xalqaro baholash» — TIMSS/PISA darajasida o'qitish, mashq, takrorlash va haqiqiy imtihonlar.

Kontent (modules/xalqaro_data/*.json):
  * savollar.json — TIMSS 2011 ochiq savollariga PARALLEL (o'zimiz yozgan) savollar: har asl savolga 2 variant,
    soha, mavzu, fikrlash darajasi, asl savolning xalqaro statistikasi (davlatlar bo'yicha to'g'ri yechganlar foizi).
    Asl IEA savollari ko'chirilmagan — IEA ularni tijoriy maqsadda ishlatishni taqiqlaydi.
  * darslar.json  — har mavzuga Kabu darsi (doska satri + ovoz, [1], [2] belgilari bilan bir xil ketadi).
  * ramka.json    — to'plamlar (4/8-sinf, matematika/tabiiy fanlar), mavzular, maktab dasturi bilan bog'lanish.
  * natijalar.json— davlatlarning haqiqiy TIMSS/PISA/PIRLS ballari (manbalari bilan), O'zbekiston natijalari.

API (hammasi JWT bilan):
  GET  /api/xalqaro/katalog                — sinfga mos to'plamlar, mavzular, o'quvchining bilimi, ustoz gapi (motivatsiya/tanbeh)
  GET  /api/xalqaro/mavzu/{kalit}          — mavzu tafsiloti: dars kodi, statistikasi, strategiyalar, maktab darslari, reyting
  GET  /api/xalqaro/mavzu_oldi             — maktab mavzusidan oldin: mos xalqaro mavzu, namuna savollar, daraja, gap
  GET  /api/xalqaro/mashq                  — mashq savollari (javob va yechimi bilan)
  POST /api/xalqaro/javob                  — mashq javobi: server tekshiradi, bilim va takrorlash navbati yangilanadi
  GET  /api/xalqaro/takror                 — bugun takrorlanadigan savollar (Leitner qutilari)
  GET  /api/xalqaro/imtihonlar             — haftalik / oylik / choraklik / yillik imtihonlar holati
  POST /api/xalqaro/imtihon/boshla         — imtihon (javobsiz savollar, server vaqti)
  POST /api/xalqaro/imtihon/topshir        — server baholaydi: foiz, taxminiy TIMSS bali, darajasi, davlatlar bilan solishtirish
  GET  /api/xalqaro/imtihon/{id}           — topshirilgan imtihon tahlili (yechimlar bilan)
  GET  /api/xalqaro/reyting                — sinfdoshlar / maktab / platforma va davlatlar orasida o'rin
  GET  /api/xalqaro/natijalar              — davlatlar natijalari (yillar kesimida)
  GET  /api/xalqaro/sinf_natija            — o'qituvchi: o'z maktabidagi sinf o'quvchilari darajasi
  GET  /api/xalqaro/rasm/{savol}/{v}.svg   — savol rasmi
Dars xonasi «XB-…» kodli darslarni shu moduldagi dars_payload() orqali ochadi.
"""
import hashlib
import json
import math
import os
import random
import re
import threading
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

try:
    from platform_core.ddl_guard import LazyMigration as _LazyMigration
except ImportError:   # pragma: no cover
    _LazyMigration = None

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xalqaro_data")
TZ = timezone(timedelta(hours=5))
OPTION_LETTERS = "ABCD"
QUTI_KUN = [0, 1, 2, 4, 8, 16]          # Leitner: quti → necha kundan keyin qayta so'raladi
DARAJALAR = [(625, "ilgor", "Ilg‘or"), (550, "yuqori", "Yuqori"), (475, "orta", "O‘rta"), (400, "past", "Past")]
THETA_SD = 1.15                          # o'quvchilar qobiliyatining tarqalishi (logit) — 100 TIMSS baliga teng
REYTING_MIN = 3

# Imtihon turlari: savollar soni va vaqti (daqiqa) — 4-sinf va 8-sinf uchun alohida. TIMSS: 4-sinf qismi 36 daqiqa, 8-sinf — 45.
IMTIHON_TURLARI = {
    "haftalik": {"nom": "Haftalik nazorat", "4": (10, 15), "8": (12, 18)},
    "oylik": {"nom": "Oylik imtihon", "4": (18, 27), "8": (22, 33)},
    "choraklik": {"nom": "Choraklik imtihon (TIMSS 1-qism)", "4": (24, 36), "8": (30, 45)},
    "yillik": {"nom": "Yillik imtihon (to‘liq TIMSS daftari)", "4": (24, 36), "8": (30, 45)},   # har qism; 2 qism: matematika + tabiiy fanlar
}
# TIMSS 2011 ramkasi: mazmun sohalari va fikrlash darajalari ulushi (imtihon savollari shu nisbatda tanlanadi)
REJA = {
    "T11_G4_M": {"soha": {"son": 0.50, "geometriya": 0.35, "malumot": 0.15}, "fikrlash": {"bilish": 0.40, "qollash": 0.40, "mulohaza": 0.20}},
    "T11_G8_M": {"soha": {"son": 0.30, "algebra": 0.30, "geometriya": 0.20, "malumot": 0.20}, "fikrlash": {"bilish": 0.35, "qollash": 0.40, "mulohaza": 0.25}},
    "T11_G4_S": {"soha": {"hayot": 0.45, "fizika": 0.35, "yer": 0.20}, "fikrlash": {"bilish": 0.40, "qollash": 0.40, "mulohaza": 0.20}},
    "T11_G8_S": {"soha": {"biologiya": 0.35, "kimyo": 0.20, "fizika": 0.25, "yer": 0.20}, "fikrlash": {"bilish": 0.35, "qollash": 0.35, "mulohaza": 0.30}},
}
NATIJA_JADVAL = {"T11_G4_M": "M4", "T11_G8_M": "M8", "T11_G4_S": "S4", "T11_G8_S": "S8"}


# ───────────────────────── kontent ─────────────────────────
class Kontent:
    """JSON kontent bir marta o'qiladi (xotirada ~ bir necha MB)."""

    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = data_dir
        self._lock = threading.Lock()
        self._ok = False

    def _load(self, name, default):
        path = os.path.join(self.data_dir, name)
        if not os.path.exists(path):
            return default
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def ensure(self):
        if self._ok:
            return self
        with self._lock:
            if self._ok:
                return self
            self.ramka = self._load("ramka.json", {"toplamlar": {}, "mavzular": {}, "fikrlash": {}})
            self.natijalar = self._load("natijalar.json", {"jadvallar": {}, "nomlar": {}})
            self.savollar = self._load("savollar.json", [])
            self.darslar = self._load("darslar.json", [])
            self.by_id = {s["id"]: s for s in self.savollar}
            self.dars_by_kod = {d["kod"]: d for d in self.darslar}
            self.mavzu_by_kalit = {}
            for tk, tops in self.ramka.get("mavzular", {}).items():
                for t in tops:
                    self.mavzu_by_kalit[t["kalit"]] = dict(t, toplam=tk)
            self.by_mavzu = {}
            for s in self.savollar:
                self.by_mavzu.setdefault(s["mavzu"], []).append(s)
            self._ok = True
        return self


KONTENT = Kontent()


def _t(v):
    return str(v or "").strip()


def sinf_raqami(value, fallback=0):
    m = re.search(r"(\d{1,2})", str(value or ""))
    n = int(m.group(1)) if m else 0
    if "yosh" in str(value or "").lower() or "kurs" in str(value or "").lower():
        return 0
    return n if 1 <= n <= 11 else int(fallback or 0)


def tavsiya_toplamlar(sinf):
    """O'quvchi sinfiga mos to'plamlar: 1–5 sinf → TIMSS 4-sinf, 6–11 → TIMSS 8-sinf."""
    if not sinf:
        return ["T11_G4_M", "T11_G4_S", "T11_G8_M", "T11_G8_S"]
    return ["T11_G4_M", "T11_G4_S"] if sinf <= 5 else ["T11_G8_M", "T11_G8_S"]


def daraja_of(ball):
    for chegara, kalit, nom in DARAJALAR:
        if ball >= chegara:
            return {"kalit": kalit, "nom": nom, "chegara": chegara}
    return {"kalit": "boshlangich", "nom": "Past darajadan quyi", "chegara": 0}


# ───────────────────────── javobni tekshirish ─────────────────────────
def _norm(value):
    s = str(value or "").lower().strip()
    s = s.replace("’", "'").replace("‘", "'").replace("ʻ", "'").replace("`", "'").replace("ʼ", "'")
    s = re.sub(r"\$|\\,|\\;|\s+", "", s)
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", s)
    s = s.replace("{,}", ",").replace(",", ".")
    s = re.sub(r"(ta|dona|so'm|sum|sm|cm|m|kg|g|l|°c|°|%|daraja|gradus)$", "", s)
    s = s.rstrip(".")
    return s


def _as_number(s):
    try:
        if re.fullmatch(r"-?\d+/\d+", s):
            a, b = s.split("/")
            return int(a) / int(b) if int(b) else None
        if re.fullmatch(r"-?\d+(\.\d+)?", s):
            return float(s)
    except (ValueError, ZeroDivisionError):
        return None
    return None


def tekshir_ochiq(berilgan, kutilgan):
    """«ochiq» javob: matn bo'yicha (| bilan bir nechta to'g'ri yozilish) yoki son qiymati bo'yicha (3/4 = 0,75)."""
    a = _norm(berilgan)
    if not a:
        return False
    variants = [_norm(x) for x in str(kutilgan or "").split("|") if _norm(x)]
    if a in variants:
        return True
    av = _as_number(a)
    if av is None:
        return False
    for v in variants:
        vv = _as_number(v)
        if vv is not None and abs(vv - av) < 1e-9:
            return True
    return False


def harf_indeksi(value):
    """«B», «b)», «2» yoki variant matni → indeks (0–3). Topilmasa None."""
    s = _t(value).upper()
    if not s:
        return None
    if isinstance(value, int) and 0 <= value <= 3:
        return value
    m = re.match(r"^\(?([ABCD])\)?[\).]?$", s)
    if m:
        return OPTION_LETTERS.index(m.group(1))
    if re.fullmatch(r"[0-3]", s):
        return int(s)
    return None


def tekshir(variant, javob):
    if variant.get("turi") == "tanlov":
        i = harf_indeksi(javob) if not isinstance(javob, int) else javob
        return i is not None and i == variant.get("togri")
    return tekshir_ochiq(javob, variant.get("javob"))


# ───────────────────────── baholash (Rasch, EAP) ─────────────────────────
def qiyinlik(foiz):
    """Asl savolning xalqaro to'g'ri yechilish foizidan Rasch qiyinligi (logit). 50% → 0."""
    p = min(97.0, max(3.0, float(foiz if foiz is not None else 50))) / 100.0
    return -math.log(p / (1 - p))


def eap_theta(natijalar):
    """natijalar: [(qiyinlik, togri_mi)] → qobiliyat (EAP, N(0,1) apriori) va xatolik."""
    nuqtalar = [-4 + i * 0.1 for i in range(81)]
    w = []
    for th in nuqtalar:
        lp = -th * th / 2
        for b, ok in natijalar:
            p = 1 / (1 + math.exp(-(th - b)))
            lp += math.log(p if ok else 1 - p)
        w.append(lp)
    m = max(w)
    w = [math.exp(x - m) for x in w]
    s = sum(w)
    mean = sum(t * x for t, x in zip(nuqtalar, w)) / s
    var = sum((t - mean) ** 2 * x for t, x in zip(nuqtalar, w)) / s
    return mean, math.sqrt(var)


def timss_ball(natijalar):
    """Taxminiy TIMSS bali: xalqaro o'rtacha o'quvchi ≈ 500. Rasmiy natija emas."""
    if not natijalar:
        return None, None
    th, se = eap_theta(natijalar)
    ball = int(round(500 + 100 * th / THETA_SD))
    return max(250, min(750, ball)), int(round(100 * se / THETA_SD))


def davlatlar_bilan(ball, jadval):
    """Ball → shu jadvaldagi o'rin va yaqin davlatlar."""
    rows = sorted(jadval or [], key=lambda r: -r[1])
    if ball is None or not rows:
        return None
    yuqori = [r for r in rows if r[1] > ball]
    past = [r for r in rows if r[1] <= ball]
    return {"orin": len(yuqori) + 1, "jami": len(rows) + 1,
            "yuqorida": yuqori[-2:], "pastda": past[:2],
            "ozbekiston": next((r[1] for r in rows if r[0] == "O‘zbekiston"), None), "eng_yuqori": rows[0], "jadval": rows}


# ───────────────────────── davrlar ─────────────────────────
def bugun():
    return datetime.now(TZ).date()


def davr_kaliti(tur, kun=None):
    """Imtihon davri: hafta (ISO), oy, chorak (o'zbek maktabi: I sen–okt, II noy–dek, III yan–mar, IV apr–avg), o'quv yili."""
    kun = kun or bugun()
    if tur == "haftalik":
        y, w, _ = kun.isocalendar()
        return f"{y}-H{w:02d}"
    if tur == "oylik":
        return f"{kun.year}-{kun.month:02d}"
    oquv_yili = kun.year if kun.month >= 9 else kun.year - 1
    if tur == "choraklik":
        m = kun.month
        q = 1 if m in (9, 10) else 2 if m in (11, 12) else 3 if m in (1, 2, 3) else 4
        return f"{oquv_yili}-{oquv_yili + 1}-C{q}"
    return f"{oquv_yili}-{oquv_yili + 1}"


def davr_oxiri(tur, kun=None):
    kun = kun or bugun()
    if tur == "haftalik":
        return kun + timedelta(days=6 - kun.weekday())
    if tur == "oylik":
        nxt = date(kun.year + (kun.month == 12), kun.month % 12 + 1, 1)
        return nxt - timedelta(days=1)
    if tur == "choraklik":
        m, y = kun.month, kun.year
        end = {9: (10, 31), 10: (10, 31), 11: (12, 31), 12: (12, 31), 1: (3, 31), 2: (3, 31), 3: (3, 31)}.get(m, (8, 31))
        return date(y, end[0], end[1])
    return date(kun.year if kun.month < 9 else kun.year + 1, 8, 31)


# ───────────────────────── savol tanlash ─────────────────────────
def _variant_public(s, vi, javob_bilan=False):
    v = s["variantlar"][vi]
    out = {"savol_id": s["id"], "v": vi, "turi": v["turi"], "savol": v["savol"], "rasm": bool(v.get("rasm")),
           "javoblar": v.get("javoblar") or [], "javob_turi": v.get("javob_turi") or "",
           "mavzu": s["mavzu"], "soha": s["soha"], "fikrlash": s["fikrlash"], "ball": 1,
           "xalqaro_foiz": s.get("xalqaro_ortacha")}
    if v.get("rasm"):
        out["rasm_svg"] = v["rasm"]
    if javob_bilan:
        out.update(togri=v.get("togri"), javob=v.get("javob") or "", yechim=v.get("yechim") or [],
                   xatolar=v.get("xatolar") or {}, maslahat=v.get("maslahat") or "",
                   kunikma=s.get("kunikma") or "", usul=s.get("usul") or "")
    return out


def reja_boyicha_tanla(savollar, soni, reja, rng, chetla=()):
    """TIMSS ramkasi nisbatida savol tanlaydi: avval soha ulushlari, ichida fikrlash darajalari aralash.
    chetla — yaqinda berilgan savollar (iloji bo'lsa takrorlanmaydi)."""
    chetla = set(chetla)
    pool = [s for s in savollar if s["id"] not in chetla]
    if len(pool) < soni:
        pool = list(savollar)
    sohalar = reja.get("soha") or {}
    kvota = {k: int(round(v * soni)) for k, v in sohalar.items()}
    while sum(kvota.values()) > soni:
        k = max(kvota, key=kvota.get); kvota[k] -= 1
    while sum(kvota.values()) < soni and kvota:
        k = max(sohalar, key=sohalar.get); kvota[k] += 1
    tanlangan = []
    fik_reja = reja.get("fikrlash") or {}
    for soha, n in kvota.items():
        guruh = [s for s in pool if s["soha"] == soha]
        rng.shuffle(guruh)
        # fikrlash darajalari bo'yicha navbatma-navbat
        fik = sorted(fik_reja, key=lambda k: -fik_reja[k]) or ["bilish", "qollash", "mulohaza"]
        target = {f: max(0, int(round(fik_reja.get(f, 0.33) * n))) for f in fik}
        olindi = []
        for f in fik:
            olindi += [s for s in guruh if s["fikrlash"] == f and s not in olindi][:target[f]]
        olindi += [s for s in guruh if s not in olindi][: max(0, n - len(olindi))]
        tanlangan += olindi[:n]
    if len(tanlangan) < soni:
        qolgan = [s for s in pool if s not in tanlangan]
        rng.shuffle(qolgan)
        tanlangan += qolgan[: soni - len(tanlangan)]
    rng.shuffle(tanlangan)
    return tanlangan[:soni]


# ───────────────────────── dars xonasi uchun ─────────────────────────
def dars_payload(topic_code, kontent=None):
    """«XB-M8-KAS» → dars xonasi formatidagi dars (topic, steps, variants, savollar). Topilmasa None."""
    k = (kontent or KONTENT).ensure()
    d = k.dars_by_kod.get(_t(topic_code).upper())
    if not d:
        return None
    mv = k.mavzu_by_kalit.get(d["mavzu"], {})
    tm = k.ramka.get("toplamlar", {}).get(mv.get("toplam"), {})
    fan = _t(d.get("fan")) or tm.get("ustoz_fan") or tm.get("fan_nomi") or "Matematika"
    steps, variants = [], {}
    for i, q in enumerate(d.get("qadamlar") or []):
        sid = f"{d['kod']}-{i + 1:02d}"
        steps.append({"id": sid, "turi": q.get("turi") or "tushuntirish", "sahna": _t(q.get("sahna")) or sid,
                      "sarlavha": _t(q.get("sarlavha")), "doska": _t(q.get("doska")), "ovoz": _t(q.get("ovoz")) or _t(q.get("doska")),
                      "rasm": None, "savol": _t(q.get("savol")) if q.get("turi") == "birga" else "",
                      "javob": _t(q.get("javob")) if q.get("turi") == "birga" else "", "javob_izohi": _t(q.get("javob_izohi")), "sahifa": ""})
    first_of_scene = {}
    for s in steps:
        first_of_scene.setdefault(s["sahna"], s["id"])
    names = {"sodda": "Soddaroq", "hikoya": "Hikoya orqali", "boshqa_usul": "Boshqa usulda", "rasm": "Rasm bilan"}
    for sahna, vs in (d.get("tushunmadim") or {}).items():
        sid = first_of_scene.get(sahna)
        if not sid:
            continue
        variants[sid] = [{"id": f"{sid}-v{j + 1}", "turi": v.get("turi") or "sodda", "nom": names.get(v.get("turi"), "Boshqacha"),
                          "doska": _t(v.get("doska")), "ovoz": _t(v.get("ovoz")), "rasm": None, "takrorlash_topic_code": ""}
                         for j, v in enumerate(vs)]
    savollar = []
    rng = random.Random(hashlib.md5(d["kod"].encode()).hexdigest())
    pool = [s for s in k.by_mavzu.get(d["mavzu"], []) if s["variantlar"][0]["turi"] == "tanlov" and not s["variantlar"][0].get("rasm")]
    rng.shuffle(pool)
    for s in pool[:5]:
        v = s["variantlar"][0]
        savollar.append({"id": f"xb-{s['id']}", "savol": v["savol"], "variantlar": v["javoblar"], "togri": v["togri"],
                         "izoh": " ".join(x["doska"] for x in (v.get("yechim") or [])[-1:]), "kod": ""})
    return {
        "topic": {"topic_code": d["kod"], "mavzu": d.get("sarlavha") or mv.get("nom"), "fan": fan,
                  "sinf": f"{tm.get('sinf', '')}-sinf" if tm.get("sinf") else "", "maqsad": _t(d.get("maqsad")), "daraja": None},
        "auto": False, "steps": steps, "variants": variants, "savollar": savollar,
        "manba": {"kitob": "Xalqaro baholash (TIMSS) tayyorlov kursi"}, "xalqaro": True,
    }


# ───────────────────────── modellar ─────────────────────────
class JavobBody(BaseModel):
    token: str = ""
    savol_id: str = Field(max_length=20)
    v: int = Field(default=0, ge=0, le=5)
    javob: str = Field(default="", max_length=200)
    usul: str = Field(default="yozib", max_length=12)     # yozib | aytib
    takror: bool = False


class BoshlaBody(BaseModel):
    token: str = ""
    tur: str = Field(max_length=12)
    toplam: str = Field(default="", max_length=12)
    mashq: bool = False


class TopshirBody(BaseModel):
    token: str = ""
    sessiya: int
    javoblar: dict = Field(default_factory=dict)
    chiqishlar: int = Field(default=0, ge=0, le=1000)      # imtihon oynasidan chiqib ketishlar soni (halollik nazorati)
    qism: int = Field(default=0, ge=0, le=2)


def migrate(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_bilim (
        user_id BIGINT NOT NULL, savol_id TEXT NOT NULL, toplam TEXT NOT NULL DEFAULT '', mavzu TEXT NOT NULL DEFAULT '',
        urinish INT NOT NULL DEFAULT 0, togri INT NOT NULL DEFAULT 0, oxirgi_togri BOOLEAN NOT NULL DEFAULT FALSE,
        aytib INT NOT NULL DEFAULT 0, yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, savol_id))""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_bilim_user ON xb_bilim(user_id, toplam)")
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_takror (
        user_id BIGINT NOT NULL, savol_id TEXT NOT NULL, v INT NOT NULL DEFAULT 0, quti INT NOT NULL DEFAULT 1,
        keyingi DATE NOT NULL, PRIMARY KEY (user_id, savol_id))""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_takror_due ON xb_takror(user_id, keyingi)")
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_imtihon (
        id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, tur TEXT NOT NULL, toplam TEXT NOT NULL, davr TEXT NOT NULL,
        rasmiy BOOLEAN NOT NULL DEFAULT FALSE, sinf INT NOT NULL DEFAULT 0, maktab_id BIGINT, sinf_nomi TEXT NOT NULL DEFAULT '',
        savollar JSONB NOT NULL, javoblar JSONB NOT NULL DEFAULT '{}'::jsonb, qismlar INT NOT NULL DEFAULT 1, qism INT NOT NULL DEFAULT 1,
        boshlangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), tugash TIMESTAMPTZ NOT NULL, topshirilgan TIMESTAMPTZ,
        foiz INT, ball INT, xato_ball INT, natija JSONB NOT NULL DEFAULT '{}'::jsonb, chiqishlar INT NOT NULL DEFAULT 0)""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_imtihon_user ON xb_imtihon(user_id, tur, davr)")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_imtihon_reyting ON xb_imtihon(toplam, tur, davr, rasmiy, ball DESC)")


def create_router(platform, kontent=None):
    router = APIRouter()
    K = kontent or KONTENT
    ready = {"ok": False}
    lock = threading.Lock()
    lazy = _LazyMigration("xalqaro_baholash") if _LazyMigration else None

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

    def user_info(cur, user_id):
        info = {"user_id": user_id, "sinf": 0, "class": "", "harf": "", "maktab_id": None, "role": "", "ism": ""}
        try:
            cur.execute("SAVEPOINT xb_user")
            cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
            row = dict(cur.fetchone() or {})
            cur.execute("RELEASE SAVEPOINT xb_user")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT xb_user")
            row = {}
        info.update(sinf=sinf_raqami(row.get("class")), **{"class": _t(row.get("class")), "harf": _t(row.get("class_letter")),
                    "maktab_id": row.get("maktab_id"), "role": _t(row.get("role")), "ism": _t(row.get("full_name"))})
        return info

    def toplam_of(key, sinf):
        k = K.ensure()
        if key in k.ramka.get("toplamlar", {}):
            return key
        return tavsiya_toplamlar(sinf)[0]

    def bilim_xaritasi(cur, user_id):
        cur.execute("SELECT savol_id, urinish, togri, oxirgi_togri, yangilangan FROM xb_bilim WHERE user_id=%s", (user_id,))
        return {r["savol_id"]: dict(r) for r in cur.fetchall()}

    def mavzu_holati(bilim, savollar):
        """Mavzu bo'yicha o'zlashtirish: yechilgan savollar ulushi va aniqlik."""
        jami = len(savollar)
        urin = [bilim[s["id"]] for s in savollar if s["id"] in bilim]
        togri = sum(1 for b in urin if b["oxirgi_togri"])
        aniqlik = round(100 * sum(b["togri"] for b in urin) / max(1, sum(b["urinish"] for b in urin))) if urin else None
        ozlashtirish = round(100 * togri / max(1, jami))
        return {"jami": jami, "urinilgan": len(urin), "ozlashtirgan": togri, "foiz": ozlashtirish, "aniqlik": aniqlik}

    def ustoz_gapi(cur, user, bilim):
        """Kabu o'quvchiga nima deydi: maqtov, eslatma yoki tanbeh (faollik va natijaga qarab)."""
        now = datetime.now(TZ)
        oxirgi = max([b["yangilangan"] for b in bilim.values()], default=None)
        kun_oldin = (now - oxirgi).days if oxirgi else None
        hafta = sum(1 for b in bilim.values() if b["yangilangan"] and (now - b["yangilangan"]).days < 7)
        cur.execute("SELECT tur, davr, ball, foiz FROM xb_imtihon WHERE user_id=%s AND rasmiy AND topshirilgan IS NOT NULL ORDER BY id DESC LIMIT 20", (user["user_id"],))
        imt = [dict(r) for r in cur.fetchall()]
        haftalik_bor = any(r["tur"] == "haftalik" and r["davr"] == davr_kaliti("haftalik") for r in imt)
        ism = (user.get("ism") or "").split()[0] if user.get("ism") else ""
        murojaat = f"{ism}, " if ism else ""
        if not bilim and not imt:
            return {"tur": "salom", "matn": f"{murojaat}xalqaro baholashga xush kelibsiz! Bu yerda dunyodagi eng kuchli o‘quvchilar yechadigan savollarni o‘rganamiz. Avval birinchi mavzu darsini ko‘ring, keyin haftalik nazoratni topshiring."}
        if kun_oldin is not None and kun_oldin >= 7:
            return {"tur": "tanbeh", "matn": f"{murojaat}siz {kun_oldin} kundan beri mashq qilmadingiz. Bu yaxshi emas — bilim mashqsiz unutiladi. Bugun kamida 10 ta savol yeching va takrorlash navbatini tugating."}
        if imt and imt[0]["foiz"] is not None and imt[0]["foiz"] < 40:
            return {"tur": "tanbeh", "matn": f"{murojaat}oxirgi imtihonda natijangiz {imt[0]['foiz']}%. Bu xalqaro past darajadan ham quyi. Xato qilgan mavzularingiz darsini qayta ko‘ring — har kuni 15 daqiqa yetadi."}
        if not haftalik_bor and bugun().weekday() >= 3:
            return {"tur": "eslatma", "matn": f"{murojaat}bu haftaning nazorati hali topshirilmagan. Hafta yakshanba kuni tugaydi — vaqtni qo‘ldan boy bermang."}
        if hafta < 10:
            return {"tur": "eslatma", "matn": f"{murojaat}bu hafta atigi {hafta} ta savol yechdingiz. Xalqaro darajaga chiqish uchun haftasiga kamida 30 ta savol kerak."}
        if imt and imt[0]["ball"] and imt[0]["ball"] >= 550:
            return {"tur": "maqtov", "matn": f"{murojaat}barakalla! Oxirgi imtihoningiz taxminan {imt[0]['ball']} ball — bu xalqaro yuqori daraja. Endi mulohaza savollariga e’tibor bering, ilg‘or darajaga oz qoldi!"}
        return {"tur": "maqtov", "matn": f"{murojaat}yaxshi ketyapsiz! Bu hafta {hafta} ta savol yechdingiz. Davom eting — har bir mashq sizni Singapur o‘quvchilariga yaqinlashtiradi."}

    # ─────────── katalog ───────────
    @router.get("/api/xalqaro/katalog")
    def katalog(token: str = None, sinf: int = Query(0, ge=0, le=11), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        k = K.ensure()

        def run(conn, cur):
            user = user_info(cur, user_id)
            s = sinf or user["sinf"]
            bilim = bilim_xaritasi(cur, user_id)
            cur.execute("SELECT COUNT(*) AS n FROM xb_takror WHERE user_id=%s AND keyingi<=%s", (user_id, bugun()))
            takror = int((cur.fetchone() or {}).get("n") or 0)
            gap = ustoz_gapi(cur, user, bilim)
            conn.commit()
            toplamlar = []
            for tk, tm in k.ramka.get("toplamlar", {}).items():
                mavzular = []
                for t in k.ramka["mavzular"].get(tk, []):
                    sv = k.by_mavzu.get(t["kalit"], [])
                    foizlar = [x.get("xalqaro_ortacha") for x in sv if x.get("xalqaro_ortacha") is not None]
                    dars = k.dars_by_kod.get("XB-" + t["kalit"])
                    mavzular.append({"kalit": t["kalit"], "nom": t["nom"], "soha": t["soha"], "soha_nomi": t["soha_nomi"],
                                     "dars_kodi": dars["kod"] if dars else "", "savollar": len(sv),
                                     "xalqaro_foiz": round(sum(foizlar) / len(foizlar)) if foizlar else None,
                                     "holat": mavzu_holati(bilim, sv)})
                jad = NATIJA_JADVAL.get(tk)
                toplamlar.append({**tm, "kalit": tk, "mavzular": mavzular, "tavsiya": tk in tavsiya_toplamlar(s),
                                  "natija_kaliti": jad})
            return {"sinf": s, "toplamlar": toplamlar, "takror": takror, "ustoz": gap,
                    "fikrlash": k.ramka.get("fikrlash", {}), "ozbekiston": k.natijalar.get("ozbekiston", {}),
                    "manba": "Savollar TIMSS 2011 ochiq savollariga parallel holda o‘zbek tilida yozilgan; xalqaro statistika — IEA TIMSS 2011 User Guide."}
        return run_db(run)

    # ─────────── mavzu ───────────
    def mavzu_tafsilot(cur, user, kalit):
        k = K.ensure()
        t = k.mavzu_by_kalit.get(kalit)
        if not t:
            raise HTTPException(404, "Mavzu topilmadi")
        sv = k.by_mavzu.get(kalit, [])
        bilim = bilim_xaritasi(cur, user["user_id"])
        dars = k.dars_by_kod.get("XB-" + kalit) or {}
        foizlar = [x["xalqaro_ortacha"] for x in sv if x.get("xalqaro_ortacha") is not None]
        davlat = {}
        for x in sv:
            for nom, f in (x.get("davlatlar") or {}).items():
                davlat.setdefault(nom, []).append(f)
        davlat_ort = sorted(([n, round(sum(v) / len(v))] for n, v in davlat.items() if len(v) >= max(1, len(sv) // 2)), key=lambda r: -r[1])
        nomlar = k.natijalar.get("nomlar", {})
        fikrlash = {}
        for x in sv:
            f = fikrlash.setdefault(x["fikrlash"], {"jami": 0, "ozlashtirgan": 0})
            f["jami"] += 1
            if bilim.get(x["id"], {}).get("oxirgi_togri"):
                f["ozlashtirgan"] += 1
        # namuna savollar: har fikrlash darajasidan bittadan (javob va yechimi bilan)
        namuna = []
        for f in ("bilish", "qollash", "mulohaza"):
            cand = sorted([x for x in sv if x["fikrlash"] == f], key=lambda x: x.get("xalqaro_ortacha") or 50)
            if cand:
                x = cand[len(cand) // 2]
                namuna.append(_variant_public(x, 0, javob_bilan=True))
        return {
            "kalit": kalit, "nom": t["nom"], "soha_nomi": t["soha_nomi"], "toplam": t["toplam"],
            "toplam_nomi": k.ramka["toplamlar"].get(t["toplam"], {}), "dars_kodi": dars.get("kod", ""),
            "maqsad": dars.get("maqsad", ""), "strategiyalar": dars.get("strategiyalar", []), "tipik_xatolar": dars.get("tipik_xatolar", []),
            "maktab": t.get("maktab", []), "kalit_sozlar": dars.get("kalit_sozlar", []),
            "xalqaro_foiz": round(sum(foizlar) / len(foizlar)) if foizlar else None,
            "davlatlar": [[nomlar.get(n, n), f] for n, f in davlat_ort[:8]] + [[nomlar.get(n, n), f] for n, f in davlat_ort[8:] if n in ("Kazakhstan", "Russian Federation")],
            "holat": mavzu_holati(bilim, sv), "fikrlash": fikrlash, "namuna": namuna,
            "kunikmalar": [x.get("kunikma") for x in sv if x.get("kunikma")][:12],
        }

    @router.get("/api/xalqaro/mavzu/{kalit}")
    def mavzu(kalit: str, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)

        def run(conn, cur):
            user = user_info(cur, user_id)
            out = mavzu_tafsilot(cur, user, kalit[:20])
            out["maktab_darslari"] = maktab_darslari(cur, out["maktab"])
            out["reyting"] = mavzu_reytingi(cur, user, kalit[:20])
            conn.commit()
            return out
        return run_db(run)

    def maktab_darslari(cur, maktab):
        """Mavzuga bog'liq 1–11 sinf maktab darslari (dts_tree dan kalit so'zlar bo'yicha)."""
        out = []
        try:
            cur.execute("SAVEPOINT xb_dts")
            for m in maktab[:3]:
                sozlar = [s for s in m.get("sozlar", []) if len(s) >= 3][:6]
                if not sozlar:
                    continue
                like = " OR ".join(["LOWER(COALESCE(NULLIF(kichik_name,''),NULLIF(mavzu_name,''),bolim_name,bob_name)) LIKE %s"] * len(sozlar))
                cur.execute(f"""SELECT topic_code, COALESCE(NULLIF(kichik_name,''),NULLIF(mavzu_name,''),NULLIF(bolim_name,''),bob_name) AS nom,
                                       subject_name, grade FROM dts_tree
                                WHERE LOWER(subject_name) LIKE %s AND ({like}) LIMIT 40""",
                            [f"%{m['fan'].lower()[:6]}%"] + [f"%{s.lower()}%" for s in sozlar])
                for r in cur.fetchall():
                    g = sinf_raqami(r["grade"])
                    if g and g in m.get("sinflar", []) and len(out) < 12 and r["topic_code"] not in {x["topic_code"] for x in out}:
                        out.append({"topic_code": r["topic_code"], "nom": _t(r["nom"]), "fan": _t(r["subject_name"]), "sinf": g})
            cur.execute("RELEASE SAVEPOINT xb_dts")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT xb_dts")
        return sorted(out, key=lambda x: (x["sinf"], x["nom"]))

    def mavzu_reytingi(cur, user, kalit):
        """Shu mavzu bo'yicha sinfdoshlar orasida o'rin (o'zlashtirgan savollar soni)."""
        if not user.get("maktab_id") or not user.get("class"):
            return None
        try:
            cur.execute("SAVEPOINT xb_mr")
            cur.execute("""SELECT b.user_id, COUNT(*) FILTER (WHERE b.oxirgi_togri) AS n FROM xb_bilim b JOIN users u ON u.user_id=b.user_id
                           WHERE b.mavzu=%s AND u.maktab_id=%s AND u.class=%s GROUP BY b.user_id""", (kalit, user["maktab_id"], user["class"]))
            rows = cur.fetchall()
            cur.execute("RELEASE SAVEPOINT xb_mr")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT xb_mr")
            return None
        mening = next((int(r["n"]) for r in rows if int(r["user_id"]) == user["user_id"]), 0)
        if len(rows) < REYTING_MIN:
            return {"jami": len(rows), "orin": None, "mening": mening}
        return {"jami": len(rows), "orin": 1 + sum(1 for r in rows if int(r["n"]) > mening), "mening": mening,
                "eng_kop": max(int(r["n"]) for r in rows)}

    # ─────────── mavzu oldi ───────────
    @router.get("/api/xalqaro/mavzu_oldi")
    def mavzu_oldi(token: str = None, fan: str = Query("", max_length=80), sinf: str = Query("", max_length=20),
                   mavzu_nomi: str = Query("", max_length=200), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        k = K.ensure()
        s = sinf_raqami(sinf)
        nom = mavzu_nomi.lower()
        fan_l = fan.lower()
        best, best_score = None, 0
        for kalit, t in k.mavzu_by_kalit.items():
            score = 0
            for m in t.get("maktab", []):
                fan_mos = m["fan"].lower()[:5] in fan_l or (m["fan"] == "Matematika" and re.search(r"matem|algebra|geometr", fan_l)) \
                    or (m["fan"] == "Tabiiy fanlar" and re.search(r"tabiiy|tabiat|atrof|science", fan_l))
                if not fan_mos:
                    continue
                hits = sum(1 for w in m.get("sozlar", []) if w.lower() in nom)
                if hits:
                    score = max(score, hits * 10 + (5 if s in m.get("sinflar", []) else 0)
                                + (3 if s and abs(k.ramka["toplamlar"][t["toplam"]]["sinf"] - s) <= 2 else 0))
            if score > best_score:
                best, best_score = kalit, score
        if not best:
            return {"topildi": False}

        def run(conn, cur):
            user = user_info(cur, user_id)
            out = mavzu_tafsilot(cur, user, best)
            out["reyting"] = mavzu_reytingi(cur, user, best)
            bilim = bilim_xaritasi(cur, user_id)
            out["ustoz"] = ustoz_gapi(cur, user, bilim)
            conn.commit()
            out["topildi"] = True
            return out
        return run_db(run)

    # ─────────── mashq ───────────
    @router.get("/api/xalqaro/mashq")
    def mashq(token: str = None, mavzu: str = Query("", max_length=20), toplam: str = Query("", max_length=12),
              soni: int = Query(8, ge=1, le=30), fikrlash: str = Query("", max_length=10), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        k = K.ensure()

        def run(conn, cur):
            bilim = bilim_xaritasi(cur, user_id)
            conn.commit()
            if mavzu:
                pool = list(k.by_mavzu.get(mavzu, []))
            else:
                pool = [s for s in k.savollar if s["toplam"] == (toplam or "T11_G8_M")]
            if fikrlash:
                pool = [s for s in pool if s["fikrlash"] == fikrlash] or pool
            # avval yechilmagan / xato qilinganlar, keyin qolganlari; oson → qiyin
            rng = random.Random()
            rng.shuffle(pool)
            pool.sort(key=lambda s: (bool(bilim.get(s["id"], {}).get("oxirgi_togri")), -(s.get("xalqaro_ortacha") or 50) // 15))
            chosen = pool[:soni]
            out = []
            for s in chosen:
                b = bilim.get(s["id"])
                vi = (b["urinish"] if b else 0) % max(1, len(s["variantlar"]))
                out.append(_variant_public(s, vi, javob_bilan=True))
            return {"savollar": out}
        return run_db(run)

    @router.post("/api/xalqaro/javob")
    def javob(body: JavobBody, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        k = K.ensure()
        s = k.by_id.get(body.savol_id)
        if not s or body.v >= len(s["variantlar"]):
            raise HTTPException(404, "Savol topilmadi")
        v = s["variantlar"][body.v]
        ok = tekshir(v, body.javob)

        def run(conn, cur):
            cur.execute("""INSERT INTO xb_bilim(user_id, savol_id, toplam, mavzu, urinish, togri, oxirgi_togri, aytib, yangilangan)
                           VALUES(%s,%s,%s,%s,1,%s,%s,%s,NOW())
                           ON CONFLICT (user_id, savol_id) DO UPDATE SET urinish=xb_bilim.urinish+1, togri=xb_bilim.togri+EXCLUDED.togri,
                             oxirgi_togri=EXCLUDED.oxirgi_togri, aytib=xb_bilim.aytib+EXCLUDED.aytib, yangilangan=NOW()""",
                        (user_id, s["id"], s["toplam"], s["mavzu"], int(ok), ok, int(body.usul == "aytib")))
            cur.execute("SELECT quti FROM xb_takror WHERE user_id=%s AND savol_id=%s", (user_id, s["id"]))
            row = cur.fetchone()
            quti = None
            if not ok:
                quti = 1
                cur.execute("""INSERT INTO xb_takror(user_id, savol_id, v, quti, keyingi) VALUES(%s,%s,%s,1,%s)
                               ON CONFLICT (user_id, savol_id) DO UPDATE SET quti=1, v=EXCLUDED.v, keyingi=EXCLUDED.keyingi""",
                            (user_id, s["id"], (body.v + 1) % len(s["variantlar"]), bugun() + timedelta(days=1)))
            elif row:
                quti = min(5, int(row["quti"]) + 1)
                if quti >= 5 and body.takror:
                    cur.execute("DELETE FROM xb_takror WHERE user_id=%s AND savol_id=%s", (user_id, s["id"]))
                else:
                    cur.execute("UPDATE xb_takror SET quti=%s, v=%s, keyingi=%s WHERE user_id=%s AND savol_id=%s",
                                (quti, (body.v + 1) % len(s["variantlar"]), bugun() + timedelta(days=QUTI_KUN[quti]), user_id, s["id"]))
            conn.commit()
            return {"togri": ok, "togri_javob": v.get("togri") if v["turi"] == "tanlov" else v.get("javob", "").split("|")[0],
                    "quti": quti}
        return run_db(run)

    @router.get("/api/xalqaro/takror")
    def takror(token: str = None, soni: int = Query(15, ge=1, le=40), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        k = K.ensure()

        def run(conn, cur):
            cur.execute("SELECT savol_id, v, quti, keyingi FROM xb_takror WHERE user_id=%s AND keyingi<=%s ORDER BY keyingi, quti LIMIT %s",
                        (user_id, bugun(), soni))
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) AS n FROM xb_takror WHERE user_id=%s", (user_id,))
            jami = int((cur.fetchone() or {}).get("n") or 0)
            conn.commit()
            out = []
            for r in rows:
                s = k.by_id.get(r["savol_id"])
                if s:
                    item = _variant_public(s, int(r["v"]) % len(s["variantlar"]), javob_bilan=True)
                    item["quti"] = int(r["quti"])
                    out.append(item)
            return {"savollar": out, "navbatda": jami}
        return run_db(run)

    # ─────────── imtihonlar ───────────
    def bloklar(toplam_key, tur):
        """Imtihon qismlari: yillik — 2 qism (matematika + tabiiy fanlar), qolganlari — 1 qism."""
        k = K.ensure()
        tm = k.ramka["toplamlar"][toplam_key]
        if tur == "yillik":
            juft = toplam_key.replace("_M", "_S") if toplam_key.endswith("_M") else toplam_key.replace("_S", "_M")
            return [toplam_key, juft] if toplam_key.endswith("_M") else [juft, toplam_key]
        return [toplam_key] if tm else []

    @router.get("/api/xalqaro/imtihonlar")
    def imtihonlar(token: str = None, toplam: str = Query("", max_length=12), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)

        def run(conn, cur):
            user = user_info(cur, user_id)
            tk = toplam_of(toplam, user["sinf"])
            band = "4" if "_G4_" in tk else "8"
            cur.execute("""SELECT id, tur, toplam, davr, rasmiy, foiz, ball, topshirilgan, tugash, natija FROM xb_imtihon
                           WHERE user_id=%s ORDER BY id DESC LIMIT 60""", (user_id,))
            rows = [dict(r) for r in cur.fetchall()]
            conn.commit()
            out = []
            now = datetime.now(TZ)
            for tur, cfg in IMTIHON_TURLARI.items():
                soni, daqiqa = cfg[band]
                davr = davr_kaliti(tur)
                mos = [r for r in rows if r["tur"] == tur and r["davr"] == davr and (r["toplam"] == tk or tur == "yillik")]
                rasmiy = next((r for r in mos if r["rasmiy"] and r["topshirilgan"]), None)
                ochiq = next((r for r in mos if not r["topshirilgan"] and r["tugash"] and r["tugash"] > now), None)
                tarix = [{"id": r["id"], "davr": r["davr"], "ball": r["ball"], "foiz": r["foiz"]}
                         for r in rows if r["tur"] == tur and r["rasmiy"] and r["topshirilgan"]][:8]
                out.append({"tur": tur, "nom": cfg["nom"], "savollar": soni * (2 if tur == "yillik" else 1), "daqiqa": daqiqa * (2 if tur == "yillik" else 1),
                            "qismlar": 2 if tur == "yillik" else 1, "davr": davr, "davr_oxiri": davr_oxiri(tur).isoformat(),
                            "topshirildi": bool(rasmiy), "natija": {"id": rasmiy["id"], "ball": rasmiy["ball"], "foiz": rasmiy["foiz"]} if rasmiy else None,
                            "davom": {"id": ochiq["id"]} if ochiq else None, "tarix": list(reversed(tarix))})
            return {"toplam": tk, "imtihonlar": out}
        return run_db(run)

    def savollar_jsonb(tanlangan, rng):
        return [{"id": s["id"], "v": rng.randrange(len(s["variantlar"]))} for s in tanlangan]

    @router.post("/api/xalqaro/imtihon/boshla")
    def boshla(body: BoshlaBody, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        if body.tur not in IMTIHON_TURLARI:
            raise HTTPException(400, "Noma’lum imtihon turi")
        k = K.ensure()

        def run(conn, cur):
            user = user_info(cur, user_id)
            tk = toplam_of(body.toplam, user["sinf"])
            band = "4" if "_G4_" in tk else "8"
            soni, daqiqa = IMTIHON_TURLARI[body.tur][band]
            davr = davr_kaliti(body.tur)
            now = datetime.now(TZ)
            # tugallanmagan sessiya bo'lsa — o'shani davom ettiramiz (sahifani yangilash imtihonni qayta boshlamaydi)
            cur.execute("""SELECT * FROM xb_imtihon WHERE user_id=%s AND tur=%s AND davr=%s AND topshirilgan IS NULL AND tugash>%s
                           ORDER BY id DESC LIMIT 1""", (user_id, body.tur, davr, now))
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT 1 FROM xb_imtihon WHERE user_id=%s AND tur=%s AND davr=%s AND rasmiy AND topshirilgan IS NOT NULL LIMIT 1",
                            (user_id, body.tur, davr))
                rasmiy = not body.mashq and not cur.fetchone()
                cur.execute("SELECT savollar FROM xb_imtihon WHERE user_id=%s ORDER BY id DESC LIMIT 6", (user_id,))
                yaqin = [x["id"] for r in cur.fetchall() for x in (r["savollar"] or [])]
                rng = random.Random()
                qismlar = []
                for q in bloklar(tk, body.tur):
                    pool = [s for s in k.savollar if s["toplam"] == q]
                    tanlangan = reja_boyicha_tanla(pool, soni, REJA.get(q, {}), rng, yaqin)
                    qismlar.append({"toplam": q, "savollar": savollar_jsonb(tanlangan, rng)})
                tugash = now + timedelta(minutes=daqiqa)
                cur.execute("""INSERT INTO xb_imtihon(user_id, tur, toplam, davr, rasmiy, sinf, maktab_id, sinf_nomi, savollar, qismlar, qism, tugash)
                               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,1,%s) RETURNING *""",
                            (user_id, body.tur, tk, davr, rasmiy, user["sinf"], user["maktab_id"],
                             f"{user['class']}{user['harf']}", json.dumps([x for q in qismlar for x in q["savollar"]]), len(qismlar), tugash))
                row = cur.fetchone()
                cur.execute("UPDATE xb_imtihon SET natija=%s::jsonb WHERE id=%s",
                            (json.dumps({"qism_toplam": [q["toplam"] for q in qismlar], "qism_soni": [len(q["savollar"]) for q in qismlar]}), row["id"]))
                row = dict(row)
                row["natija"] = {"qism_toplam": [q["toplam"] for q in qismlar], "qism_soni": [len(q["savollar"]) for q in qismlar]}
            conn.commit()
            return sessiya_korinishi(dict(row), daqiqa)
        return run_db(run)

    def sessiya_korinishi(row, daqiqa):
        k = K.ensure()
        meta = row.get("natija") or {}
        sonlar = meta.get("qism_soni") or [len(row["savollar"])]
        qism = int(row.get("qism") or 1)
        bosh = sum(sonlar[: qism - 1])
        items = []
        for i, x in enumerate(row["savollar"][bosh: bosh + sonlar[qism - 1]]):
            s = k.by_id.get(x["id"])
            if s:
                p = _variant_public(s, x["v"] % len(s["variantlar"]))
                p["n"] = bosh + i
                items.append(p)
        toplamlar = meta.get("qism_toplam") or [row["toplam"]]
        return {"sessiya": row["id"], "tur": row["tur"], "nom": IMTIHON_TURLARI[row["tur"]]["nom"], "rasmiy": row["rasmiy"],
                "qism": qism, "qismlar": int(row.get("qismlar") or 1),
                "qism_fani": K.ensure().ramka["toplamlar"].get(toplamlar[qism - 1], {}).get("fan_nomi", ""),
                "tugash": row["tugash"].isoformat() if hasattr(row["tugash"], "isoformat") else row["tugash"],
                "server_vaqt": datetime.now(TZ).isoformat(), "daqiqa": daqiqa, "savollar": items,
                "javoblar": row.get("javoblar") or {}}

    @router.post("/api/xalqaro/imtihon/topshir")
    def topshir(body: TopshirBody, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        k = K.ensure()

        def run(conn, cur):
            cur.execute("SELECT * FROM xb_imtihon WHERE id=%s AND user_id=%s FOR UPDATE", (body.sessiya, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Imtihon topilmadi")
            row = dict(row)
            if row["topshirilgan"]:
                conn.commit()
                return {"id": row["id"], "tayyor": True}
            now = datetime.now(TZ)
            kech = now > row["tugash"] + timedelta(seconds=90)   # tarmoq kechikishi uchun 90 s
            javoblar = dict(row["javoblar"] or {})
            # vaqt tugagandan keyin yuborilgan javoblar qabul qilinmaydi (oldin saqlanganlari qoladi)
            if not kech:
                for kk, vv in (body.javoblar or {}).items():
                    if re.fullmatch(r"\d{1,3}", str(kk)):
                        javoblar[str(kk)] = str(vv)[:200]
            meta = dict(row.get("natija") or {})
            band = "4" if "_G4_" in row["toplam"] else "8"
            daqiqa = IMTIHON_TURLARI[row["tur"]][band][1]
            if int(row["qism"]) < int(row["qismlar"]) and not kech:
                # keyingi qism: tanaffusdan keyin yangi vaqt
                cur.execute("UPDATE xb_imtihon SET javoblar=%s::jsonb, qism=qism+1, tugash=%s, chiqishlar=chiqishlar+%s WHERE id=%s RETURNING *",
                            (json.dumps(javoblar), now + timedelta(minutes=daqiqa + 10), body.chiqishlar, row["id"]))
                nr = dict(cur.fetchone())
                conn.commit()
                out = sessiya_korinishi(nr, daqiqa)
                out["tanaffus"] = 10
                return out
            natija = bahola(row["savollar"], javoblar, meta)
            cur.execute("""UPDATE xb_imtihon SET javoblar=%s::jsonb, topshirilgan=NOW(), foiz=%s, ball=%s, xato_ball=%s,
                           natija=%s::jsonb, chiqishlar=chiqishlar+%s WHERE id=%s""",
                        (json.dumps(javoblar), natija["foiz"], natija["ball"], natija["xato"], json.dumps({**meta, **natija}),
                         body.chiqishlar, row["id"]))
            # imtihondagi xatolar takrorlash navbatiga tushadi
            for x, ok in zip(row["savollar"], natija["togri_list"]):
                if not ok:
                    s = k.by_id.get(x["id"])
                    if s:
                        cur.execute("""INSERT INTO xb_takror(user_id, savol_id, v, quti, keyingi) VALUES(%s,%s,%s,1,%s)
                                       ON CONFLICT (user_id, savol_id) DO UPDATE SET quti=1, keyingi=EXCLUDED.keyingi""",
                                    (user_id, x["id"], (x["v"] + 1) % len(s["variantlar"]), bugun() + timedelta(days=1)))
            conn.commit()
            return {"id": row["id"], "tayyor": True}
        return run_db(run)

    def bahola(savollar, javoblar, meta):
        k = K.ensure()
        rasch, togri_list, soha, fik = [], [], {}, {}
        qism_toplam = meta.get("qism_toplam") or []
        for i, x in enumerate(savollar):
            s = k.by_id.get(x["id"])
            if not s:
                togri_list.append(False)
                continue
            v = s["variantlar"][x["v"] % len(s["variantlar"])]
            ok = tekshir(v, javoblar.get(str(i), ""))
            togri_list.append(ok)
            rasch.append((qiyinlik(s.get("xalqaro_ortacha")), ok))
            for d, key in ((soha, f"{s['toplam']}|{s['soha']}"), (fik, s["fikrlash"])):
                e = d.setdefault(key, [0, 0])
                e[0] += int(ok)
                e[1] += 1
        ball, xato = timss_ball(rasch)
        foiz = round(100 * sum(togri_list) / max(1, len(togri_list)))
        # qismlar (yillik: matematika va tabiiy fanlar) bo'yicha alohida ball
        qism_ball = {}
        for q in qism_toplam:
            r = [(qiyinlik(k.by_id[x["id"]].get("xalqaro_ortacha")), ok) for x, ok in zip(savollar, togri_list)
                 if x["id"] in k.by_id and k.by_id[x["id"]]["toplam"] == q]
            if r:
                qism_ball[q] = timss_ball(r)[0]
        return {"foiz": foiz, "ball": ball, "xato": xato, "togri": sum(togri_list), "jami": len(togri_list),
                "togri_list": togri_list, "daraja": daraja_of(ball or 0), "soha": soha, "fikrlash": fik, "qism_ball": qism_ball}

    @router.get("/api/xalqaro/imtihon/{sessiya}")
    def imtihon_tahlil(sessiya: int, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        k = K.ensure()

        def run(conn, cur):
            cur.execute("SELECT * FROM xb_imtihon WHERE id=%s AND user_id=%s", (sessiya, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Imtihon topilmadi")
            row = dict(row)
            if not row["topshirilgan"]:
                band = "4" if "_G4_" in row["toplam"] else "8"
                conn.commit()
                return {"tayyor": False, **sessiya_korinishi(row, IMTIHON_TURLARI[row["tur"]][band][1])}
            reyt = imtihon_reytingi(cur, row)
            conn.commit()
            natija = row["natija"] or {}
            items = []
            for i, x in enumerate(row["savollar"]):
                s = k.by_id.get(x["id"])
                if not s:
                    continue
                p = _variant_public(s, x["v"] % len(s["variantlar"]), javob_bilan=True)
                p.update(n=i, berilgan=(row["javoblar"] or {}).get(str(i), ""), togri_mi=bool((natija.get("togri_list") or [])[i:i + 1] and natija["togri_list"][i]))
                items.append(p)
            sohalar = {}
            for key, (t, j) in (natija.get("soha") or {}).items():
                tk, soha = key.split("|")
                nom = next((m["soha_nomi"] for m in k.ramka["mavzular"].get(tk, []) if m["soha"] == soha), soha)
                sohalar[key] = {"nom": nom, "fan": k.ramka["toplamlar"].get(tk, {}).get("fan_nomi", ""), "togri": t, "jami": j}
            jadvallar = {}
            for q in (natija.get("qism_toplam") or [row["toplam"]]):
                kod = NATIJA_JADVAL.get(q)
                b = (natija.get("qism_ball") or {}).get(q, row["ball"])
                jadvallar[q] = {"fan": k.ramka["toplamlar"].get(q, {}).get("fan_nomi", ""), "ball": b,
                                "timss2023": davlatlar_bilan(b, k.natijalar["jadvallar"].get(f"TIMSS 2023 {kod}")),
                                "timss2019": davlatlar_bilan(b, k.natijalar["jadvallar"].get(f"TIMSS 2019 {kod}"))}
            return {"tayyor": True, "id": row["id"], "tur": row["tur"], "nom": IMTIHON_TURLARI[row["tur"]]["nom"], "rasmiy": row["rasmiy"],
                    "davr": row["davr"], "foiz": row["foiz"], "ball": row["ball"], "xato_ball": row["xato_ball"],
                    "daraja": daraja_of(row["ball"] or 0), "togri": natija.get("togri"), "jami": natija.get("jami"),
                    "sohalar": sohalar, "fikrlash": natija.get("fikrlash") or {}, "davlatlar": jadvallar, "reyting": reyt,
                    "chiqishlar": row["chiqishlar"], "savollar": items,
                    "izoh": "Taxminiy TIMSS bali savollarning xalqaro qiyinligi asosida hisoblangan (Rasch modeli) — rasmiy natija emas."}
        return run_db(run)

    def imtihon_reytingi(cur, row):
        """Shu davr va shu turdagi rasmiy imtihonlar orasida o'rin: sinfdoshlar, maktab, platforma (sinf bo'yicha)."""
        if not row["rasmiy"] or row["ball"] is None:
            return None
        out = {}
        sharts = {"sinf": ("maktab_id=%s AND sinf_nomi=%s", (row["maktab_id"], row["sinf_nomi"])) if row["maktab_id"] else None,
                  "maktab": ("maktab_id=%s AND sinf=%s", (row["maktab_id"], row["sinf"])) if row["maktab_id"] else None,
                  "platforma": ("sinf=%s", (row["sinf"],))}
        for nom, sh in sharts.items():
            if not sh:
                continue
            cur.execute(f"""SELECT COUNT(*) AS jami, COUNT(*) FILTER (WHERE ball > %s) AS yuqori, ROUND(AVG(ball)) AS ortacha
                            FROM xb_imtihon WHERE tur=%s AND toplam=%s AND davr=%s AND rasmiy AND topshirilgan IS NOT NULL AND {sh[0]}""",
                        (row["ball"], row["tur"], row["toplam"], row["davr"], *sh[1]))
            r = cur.fetchone() or {}
            jami = int(r.get("jami") or 0)
            out[nom] = {"jami": jami, "orin": int(r.get("yuqori") or 0) + 1 if jami >= REYTING_MIN else None,
                        "ortacha": int(r["ortacha"]) if r.get("ortacha") is not None else None}
        return out

    # ─────────── reyting va natijalar ───────────
    @router.get("/api/xalqaro/reyting")
    def reyting(token: str = None, toplam: str = Query("", max_length=12), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        k = K.ensure()

        def run(conn, cur):
            user = user_info(cur, user_id)
            tk = toplam_of(toplam, user["sinf"])
            cur.execute("""SELECT id, tur, davr, ball, foiz, maktab_id, sinf_nomi, sinf, toplam, rasmiy, topshirilgan FROM xb_imtihon
                           WHERE user_id=%s AND rasmiy AND topshirilgan IS NOT NULL AND (toplam=%s OR tur='yillik') ORDER BY id""", (user_id, tk))
            mine = [dict(r) for r in cur.fetchall()]
            oxirgi = mine[-1] if mine else None
            reyt = imtihon_reytingi(cur, {**oxirgi, "toplam": oxirgi["toplam"]}) if oxirgi else None
            # sinfdoshlar ro'yxati (ismsiz, faqat o'rin va ball) — eng yaxshi rasmiy natija shu oy
            sinfdosh = []
            if user.get("maktab_id") and user.get("class"):
                cur.execute("""SELECT user_id, MAX(ball) AS ball FROM xb_imtihon WHERE maktab_id=%s AND sinf_nomi=%s AND toplam=%s
                               AND rasmiy AND topshirilgan IS NOT NULL AND boshlangan > NOW() - INTERVAL '45 days' GROUP BY user_id ORDER BY 2 DESC LIMIT 40""",
                            (user["maktab_id"], f"{user['class']}{user['harf']}", tk))
                sinfdosh = [{"orin": i + 1, "ball": int(r["ball"] or 0), "men": int(r["user_id"]) == user_id} for i, r in enumerate(cur.fetchall())]
            conn.commit()
            kod = NATIJA_JADVAL.get(tk)
            b = oxirgi["ball"] if oxirgi else None
            return {"toplam": tk, "tarix": [{"tur": r["tur"], "davr": r["davr"], "ball": r["ball"], "foiz": r["foiz"]} for r in mine[-30:]],
                    "oxirgi": {"ball": b, "daraja": daraja_of(b or 0) if b else None}, "reyting": reyt,
                    "sinfdoshlar": sinfdosh if len(sinfdosh) >= REYTING_MIN else [],
                    "davlatlar": {"timss2023": davlatlar_bilan(b, k.natijalar["jadvallar"].get(f"TIMSS 2023 {kod}")),
                                  "timss2019": davlatlar_bilan(b, k.natijalar["jadvallar"].get(f"TIMSS 2019 {kod}"))}}
        return run_db(run)

    @router.get("/api/xalqaro/natijalar")
    def natijalar(token: str = None, authorization: str = Header(None)):
        uid_of(token, authorization)
        n = K.ensure().natijalar
        return {"jadvallar": n.get("jadvallar", {}), "ozbekiston": n.get("ozbekiston", {}), "manbalar": n.get("manbalar", {}),
                "darajalar": n.get("darajalar", {})}

    @router.get("/api/xalqaro/sinf_natija")
    def sinf_natija(token: str = None, sinf: str = Query("", max_length=10), authorization: str = Header(None)):
        """O'qituvchi o'z maktabidagi sinf o'quvchilarining xalqaro baholash natijasini ko'radi."""
        user_id = uid_of(token, authorization)

        def run(conn, cur):
            user = user_info(cur, user_id)
            if user["role"] not in ("oqituvchi", "admin", "direktor") or not user.get("maktab_id"):
                raise HTTPException(403, "Faqat maktab o‘qituvchisi uchun")
            cur.execute("""SELECT u.user_id, u.full_name, u.class, COALESCE(u.class_letter,'') AS harf,
                                  (SELECT COUNT(*) FROM xb_bilim b WHERE b.user_id=u.user_id) AS urinish,
                                  (SELECT COUNT(*) FROM xb_bilim b WHERE b.user_id=u.user_id AND b.oxirgi_togri) AS ozlashtirgan,
                                  (SELECT MAX(b.yangilangan) FROM xb_bilim b WHERE b.user_id=u.user_id) AS oxirgi,
                                  (SELECT i.ball FROM xb_imtihon i WHERE i.user_id=u.user_id AND i.rasmiy AND i.topshirilgan IS NOT NULL ORDER BY i.id DESC LIMIT 1) AS ball
                           FROM users u WHERE u.maktab_id=%s AND u.role IN ('oquvchi','o''quvchi','student') AND u.class LIKE %s
                           ORDER BY u.class, harf, u.full_name LIMIT 400""", (user["maktab_id"], f"{sinf}%" if sinf else "%"))
            rows = []
            now = datetime.now(TZ)
            for r in cur.fetchall():
                d = dict(r)
                d["kun_oldin"] = (now - d["oxirgi"]).days if d.get("oxirgi") else None
                d["daraja"] = daraja_of(d["ball"])["nom"] if d.get("ball") else None
                d.pop("oxirgi", None)
                rows.append(d)
            conn.commit()
            return {"oquvchilar": rows}
        return run_db(run)

    @router.get("/api/xalqaro/rasm/{savol_id}/{v}.svg")
    def rasm(savol_id: str, v: int, request: Request):
        k = K.ensure()
        s = k.by_id.get(savol_id[:20])
        if not s or v >= len(s["variantlar"]) or not s["variantlar"][v].get("rasm"):
            raise HTTPException(404, "Rasm yo‘q")
        svg = s["variantlar"][v]["rasm"].encode("utf-8")
        etag = '"' + hashlib.sha1(svg).hexdigest() + '"'
        headers = {"Cache-Control": "public, max-age=86400", "ETag": etag, "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"}
        if etag in (request.headers.get("if-none-match") or ""):
            return Response(status_code=304, headers=headers)
        return Response(content=svg, media_type="image/svg+xml", headers=headers)

    return router

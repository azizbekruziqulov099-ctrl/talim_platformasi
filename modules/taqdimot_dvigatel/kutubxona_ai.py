"""Tayyor mavzular kutubxonasini AI bilan to'ldirish.

1) Mavzular reestri (DB: taqdimot_mavzular) — 1–11-sinf, bakalavr, magistratura:
   • urug‘: malumot/mavzular_reja.json (rasmiy TRM darslari + umumiy dastur asosidagi mavzular);
   • infoedu.uz darslik mundarijalari (server o'zi yig'adi, sahifama-sahifa, sekin);
   • admin yuklagan fan dasturi (xlsx/csv/docx/pdf/txt) — mavzular qatordan yoki AI bilan ajratiladi.
2) Yozuvchi: mavzularni bittadan AI bilan miyaga aylantiradi (kunlik chegara, admin yoqadi/to'xtatadi,
   server qayta yonsa to'xtagan joyidan davom etadi). Bir nechta jarayon bo'lsa — ijara (lease) bilan bittasi ishlaydi.
3) Tayyor miyalar «Tayyor mavzular» oynasida sinf → fan → mavzu bo'yicha ochiladi; rasm kalitlari 2-qism buyurtma
   ro'yxatidan — rasm yuklanganda taqdimotda o'zi chiqadi.
"""
from __future__ import annotations

import html as _html
import io
import json
import os
import re
import threading
import time
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS taqdimot_mavzular (
    id BIGSERIAL PRIMARY KEY,
    daraja TEXT NOT NULL,
    sinf TEXT NOT NULL DEFAULT '',
    fan TEXT NOT NULL,
    yonalish TEXT NOT NULL DEFAULT '',
    bob TEXT NOT NULL DEFAULT '',
    raqam INT,
    mavzu TEXT NOT NULL,
    en TEXT NOT NULL DEFAULT '',
    manba TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    yozilsin BOOLEAN NOT NULL DEFAULT true,
    holat TEXT NOT NULL DEFAULT 'kutmoqda',
    miya JSONB,
    xato TEXT,
    urinish INT NOT NULL DEFAULT 0,
    yaratildi TIMESTAMPTZ NOT NULL DEFAULT now(),
    boshlandi TIMESTAMPTZ,
    yozildi TIMESTAMPTZ,
    UNIQUE (daraja, sinf, fan, mavzu)
);
CREATE INDEX IF NOT EXISTS taqdimot_mavzular_navbat ON taqdimot_mavzular(holat, daraja, sinf, fan);
-- bir mavzu — ikki mahsulot: taqdimot miyasi (miya) va ochiq dars miyasi (ochiq_dars, fan metodlari asosida keyin yoziladi)
ALTER TABLE taqdimot_mavzular ADD COLUMN IF NOT EXISTS ochiq_dars JSONB;
ALTER TABLE taqdimot_mavzular ADD COLUMN IF NOT EXISTS ochiq_holat TEXT NOT NULL DEFAULT 'kutmoqda';
-- dars masalliqlari (bayon, guruh topshiriqlari, loyiha, ekskursiya…) — eski tayyor mavzularga keyin to'ldiriladi
ALTER TABLE taqdimot_mavzular ADD COLUMN IF NOT EXISTS ochiq_vaqt TIMESTAMPTZ;
ALTER TABLE taqdimot_mavzular ADD COLUMN IF NOT EXISTS ochiq_urinish INT NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS taqdimot_kutubxona_sozlama (
    kalit TEXT PRIMARY KEY,
    qiymat JSONB NOT NULL,
    vaqt TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

MALUMOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "malumot")
URUG = os.path.join(MALUMOT, "mavzular_reja.json")
DARAJALAR = ("maktab", "bakalavr", "magistr")
HOLATLAR = ("kutmoqda", "yozilmoqda", "tayyor", "xato", "otkazildi")
STANDART = {"yoqilgan": False, "kunlik": 100, "tartib": "maktab", "daraja": [], "sinflar": [], "fanlar": [], "tun": False}
TUN_SOATLARI = (22, 7)   # «faqat kechasi» yoqilganda yozuvchi shu oraliqda ishlaydi (Toshkent vaqti)
# Asosiy fanlar birinchi yoziladi: matematika → ona tili → chet tili → tabiiy fanlar → qolganlari
ASOSIY_FANLAR = (("%matemat%", "%algebra%", "%geometr%"), ("ona tili%", "%qish savodxon%", "%alifbe%", "%adabiyot%"),
                 ("%ingliz%", "%rus tili%"), ("%fizika%",), ("%kimyo%",), ("%biolog%", "%tabiiy%"), ("%informat%",),
                 ("%tarix%",), ("%geograf%",))


def fan_tartibi_sql() -> str:
    qism = []
    for i, andozalar in enumerate(ASOSIY_FANLAR):
        shart = " OR ".join("lower(fan) LIKE '" + a.replace("%", "%%") + "'" for a in andozalar)
        qism.append(f"WHEN {shart} THEN {i}")
    return "CASE " + " ".join(qism) + f" ELSE {len(ASOSIY_FANLAR)} END"


def tun_vaqtimi(hozir=None) -> bool:
    import datetime as _dt
    soat = (hozir or _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=5)))).hour
    a, b = TUN_SOATLARI
    return soat >= a or soat < b
OTKAZ = re.compile(r"takrorla|masala(lar)? yech|nazorat ishi|mustahkam|^test\b|\bbsb\b|\bchsb\b|javoblar|foydalanilgan|bob yuzasidan|"
                   r"umumlashtir|mashqlarning javob|kirish$|mundarija", re.I)
IJARA_DAQ = 12        # yozuvchi ijarasi (bir nechta gunicorn jarayoni bo'lsa ham bitta yozadi)
ESKI_DAQ = 30         # shuncha daqiqa «yozilmoqda» turgan mavzu — qayta navbatga
URINISH_MAX = 3
# miyada darsning o'zi (bayon) bormi — SQL ifodasi
BAYON_BOR = ("COALESCE(CASE WHEN jsonb_typeof(miya #> '{masalliq,bayon}') = 'array' "
             "THEN jsonb_array_length(miya #> '{masalliq,bayon}') END, 0) > 0")


def bayon_bor(m) -> bool:
    return bool(((m or {}).get("masalliq") or {}).get("bayon"))
TANAFFUS = 15         # mavzular orasida (soniya)
INFOEDU = "https://infoedu.uz"

# infoedu.uz sahifa nomi → fan nomi (reestrdagi bilan bir xil bo'lsin)
FAN_SLUG = {
    "ona-tili": "Ona tili", "adabiyot": "Adabiyot", "oqish": "O‘qish savodxonligi", "oqish-savodxonligi": "O‘qish savodxonligi",
    "alifbe": "Alifbe", "matematika": "Matematika", "algebra": "Algebra", "geometriya": "Geometriya", "fizika": "Fizika", "kimyo": "Kimyo",
    "biologiya": "Biologiya", "zoologiya": "Biologiya", "botanika": "Biologiya", "odam-va-uning-salomatligi": "Biologiya",
    "geografiya": "Geografiya", "jahon-tarixi": "Jahon tarixi", "ozbekiston-tarixi": "O‘zbekiston tarixi", "tarix": "Tarix",
    "tarixdan-hikoyalar": "Tarix", "informatika": "Informatika", "informatika-va-at": "Informatika", "ingliz-tili": "Ingliz tili",
    "rus-tili": "Rus tili", "nemis-tili": "Nemis tili", "fransuz-tili": "Fransuz tili", "jismoniy-tarbiya": "Jismoniy tarbiya",
    "musiqa": "Musiqa", "tarbiya": "Tarbiya", "tasviriy-sanat": "Tasviriy san’at", "texnologiya": "Texnologiya",
    "milliy-istiqlol-goyasi": "Milliy istiqlol g‘oyasi", "huquq": "Huquq asoslari", "davlat-va-huquq-asoslari": "Huquq asoslari",
    "iqtisodiy-bilim-asoslari": "Iqtisodiy bilim asoslari", "iqtisod": "Iqtisodiy bilim asoslari", "astronomiya": "Astronomiya",
    "chqbt": "Chaqiruvga qadar boshlang‘ich tayyorgarlik", "tabiiy-fanlar": "Tabiiy fanlar", "atrofimizdagi-olam": "Tabiiy fanlar",
    "tabiatshunoslik": "Tabiiy fanlar", "chizmachilik": "Chizmachilik", "dinshunoslik": "Dinshunoslik",
}
# urug' reestrdagi umumiy nom → infoedu kelganda o'rniga keladigan fanlar (takror yozilmasin)
URNIGA = {"Tarix": ("Tarix", "Jahon tarixi", "O‘zbekiston tarixi"), "Ona tili va o‘qish savodxonligi": ("Ona tili", "O‘qish savodxonligi", "Alifbe"),
          "Matematika (algebra va analiz asoslari)": ("Algebra",), "Geometriya (stereometriya)": ("Geometriya",)}


# ------------------------------------------------------------------ yordamchilar
def _qator(r):
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(r).items()}


def sinf_tartib(s: str) -> int:
    m = re.search(r"\d+", s or "")
    return int(m.group(0)) if m else 99


def sinf_matni(daraja: str, sinf: str) -> str:
    if daraja == "maktab":
        return f"{sinf}-sinf" if sinf and "sinf" not in sinf else sinf
    if daraja == "magistr":
        return f"magistratura {sinf}" if sinf else "magistratura"
    return sinf or "bakalavr"


def html_matn(h: str) -> str:
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h or "")
    h = re.sub(r"(?i)<br\s*/?>|</(p|li|div|h[1-6]|tr|td|ul|ol|section|article)>", "\n", h)
    h = re.sub(r"<[^>]+>", " ", h)
    h = _html.unescape(h)
    return "\n".join(re.sub(r"[ \t ]+", " ", q).strip() for q in h.splitlines())


_MAVZU = re.compile(r"^\s*[•●▪·\-*–]?\s*(\d{1,3})\s*[-–]?\s*(?:mavzu|dars|§)\s*[.:)]?\s*(.{3,180}?)\s*$", re.I)
_PARAGRAF = re.compile(r"^\s*[•●▪·\-*–]?\s*§\s*(\d{1,3})\s*[.:)]?\s*(.{3,180}?)\s*$")
_BOB = re.compile(r"^\s*[•●▪·\-*–]?\s*(?:([IVXLC]{1,6})|(\d{1,2}))\s*[-–]?\s*(?:BOB|bob|Bob|BO[‘'ʻ`]?LIM|bo[‘'ʻ`]?lim|QISM|qism)\b\.?\s*[:.]?\s*(.*)$")
_KIRILL = re.compile(r"[А-Яа-яЁё]")


def mundarija(matn: str) -> list:
    """Darslik mundarijasi matnidan: [{raqam, mavzu, bob}] (o'zbekcha qatorlar, takrorsiz, tartib bilan)."""
    out, bob, korilgan = [], "", set()
    for q in (matn or "").splitlines():
        if not q or len(q) > 220:
            continue
        mb = _BOB.match(q)
        if mb:
            bob = re.sub(r"\s+", " ", f"{mb.group(1) or mb.group(2)}-bob. {mb.group(3)}").strip(" .")
            continue
        m = _MAVZU.match(q) or _PARAGRAF.match(q)
        if not m:
            continue
        nom = m.group(2).strip(" .;:")
        if len(_KIRILL.findall(nom)) > len(nom) / 3:   # ruscha nashr qatorlari
            continue
        k = re.sub(r"\W+", "", nom.lower())
        if not k or k in korilgan:
            continue
        korilgan.add(k)
        out.append({"raqam": int(m.group(1)), "mavzu": nom[:200], "bob": bob[:160]})
    return out


def dastur_qatorlari(matn: str) -> list:
    """Fan dasturi / syllabus matnidan mavzular: «1-mavzu. …», «Mavzu 1: …», «1. …» (raqamli qatorlar)."""
    out = mundarija(matn)
    if len(out) >= 4:
        return out
    out, korilgan = [], set()
    for q in (matn or "").splitlines():
        m = re.match(r"^\s*(?:mavzu\s*)?(\d{1,3})\s*[.):-]\s*(?:mavzu\s*[.:-]?\s*)?([A-Za-zʻ‘'O‘G‘].{4,180})$", q.strip(), re.I)
        if not m:
            continue
        nom = m.group(2).strip(" .;:")
        k = re.sub(r"\W+", "", nom.lower())
        if k in korilgan or len(nom.split()) < 2:
            continue
        korilgan.add(k)
        out.append({"raqam": int(m.group(1)), "mavzu": nom[:200], "bob": ""})
    return out


def fayl_matni(nom: str, data: bytes) -> tuple[str, list]:
    """Yuklangan fan dasturi → (matn, jadval qatorlari [(raqam, mavzu)])."""
    ext = (nom.rsplit(".", 1)[-1] if "." in nom else "").lower()
    if ext in ("xlsx", "xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        qatorlar = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
                if cells:
                    qatorlar.append(cells)
        jadval = []
        for cells in qatorlar:
            matnli = [c for c in cells if len(c) > 6 and not re.fullmatch(r"[\d.,\s]+", c)]
            if matnli:
                raqam = next((int(c) for c in cells if re.fullmatch(r"\d{1,3}", c)), None)
                jadval.append((raqam, max(matnli, key=len)))
        return "\n".join(" ".join(c) for c in qatorlar), jadval
    if ext == "csv":
        t = data.decode("utf-8-sig", "replace")
        return t, []
    if ext == "docx":
        import docx
        d = docx.Document(io.BytesIO(data))
        qism = [p.text for p in d.paragraphs]
        for tb in d.tables:
            for row in tb.rows:
                qism.append(" | ".join(c.text.strip() for c in row.cells))
        return "\n".join(qism), []
    if ext == "pdf":
        from pypdf import PdfReader
        r = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in r.pages[:80]), []
    return data.decode("utf-8", "replace"), []


def ai_mavzular(matn: str, fan: str, sinf: str) -> list:
    """Mundarija qatorlari topilmasa — AI matndan mavzularni ajratadi (faqat ro'yxat, izohsiz)."""
    from . import ai
    if not ai.mavjud():
        return []
    sistema = ("Sen metodistsan. Berilgan darslik yoki fan dasturi matnidan dars MAVZULARI ro‘yxatini ajrat. Faqat JSON: "
               "{\"mavzular\":[{\"raqam\":1,\"bob\":\"…\",\"mavzu\":\"…\"}]}. Mavzu nomlarini matndagidek (o‘zbek lotin) yoz, o‘ylab topma.")
    r = ai._bir_chaqiruv(sistema, f"FAN: {fan}\nSINF/KURS: {sinf}\nMATN:\n{matn[:24000]}", 90.0, time.monotonic())
    out = []
    for i, x in enumerate((r or {}).get("mavzular") or [], 1):
        if isinstance(x, dict) and isinstance(x.get("mavzu"), str) and len(x["mavzu"].strip()) > 3:
            out.append({"raqam": int(x.get("raqam") or i) if str(x.get("raqam") or "").isdigit() else i,
                        "mavzu": x["mavzu"].strip()[:200], "bob": str(x.get("bob") or "")[:160]})
    return out


# ------------------------------------------------------------------ xizmat
class Kutubxona:
    def __init__(self, D):
        self.D = D
        self.pid = f"{os.getpid()}-{uuid.uuid4().hex[:6]}"
        self._ip = None
        self._yigish = None
        self._tayyor = False
        self._lock = threading.Lock()

    @property
    def ps(self):
        return self.D.ps

    def migrate(self):
        if self._tayyor:
            return
        with self._lock:
            if self._tayyor:
                return
            with self.ps.db() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(49091378)")
                cur.execute(SCHEMA)
                cur.execute("SELECT count(*) AS n FROM taqdimot_mavzular")
                bosh = cur.fetchone()["n"] == 0
            if bosh:
                self.urug_qosh()
            self._tayyor = True

    def urug_qosh(self) -> int:
        try:
            with open(URUG, encoding="utf-8") as f:
                rows = json.load(f).get("mavzular") or []
        except (OSError, ValueError):
            return 0
        return self.qosh(rows)

    def qosh(self, rows, ustun: bool = False) -> int:
        """Reestrga qo'shadi. ustun=True — aniq manba (darslik mundarijasi, fan dasturi): bir xil nomli taxminiy
        («reja …») mavzu bo'lsa, o'shani yangilaydi (raqam, bob, manba) va navbatga qaytaradi."""
        n = 0
        yangilash = ("ON CONFLICT (daraja, sinf, fan, mavzu) DO UPDATE SET manba=EXCLUDED.manba, raqam=EXCLUDED.raqam, bob=EXCLUDED.bob, "
                     "url=EXCLUDED.url, yozilsin=EXCLUDED.yozilsin, holat=CASE WHEN taqdimot_mavzular.holat='otkazildi' AND EXCLUDED.yozilsin "
                     "THEN 'kutmoqda' ELSE taqdimot_mavzular.holat END WHERE taqdimot_mavzular.manba LIKE 'reja%%'") if ustun else \
            "ON CONFLICT (daraja, sinf, fan, mavzu) DO NOTHING"
        with self.ps.db() as cur:
            for r in rows:
                mav = re.sub(r"\s+", " ", str(r.get("mavzu") or "")).strip()[:200]
                if len(mav) < 3 or r.get("daraja") not in DARAJALAR or not r.get("fan"):
                    continue
                yoz = bool(r.get("yozilsin", True)) and not OTKAZ.search(mav)
                cur.execute(
                    "INSERT INTO taqdimot_mavzular(daraja, sinf, fan, yonalish, bob, raqam, mavzu, en, manba, url, yozilsin, holat) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) " + yangilash,
                    (r["daraja"], str(r.get("sinf") or "")[:20], str(r["fan"])[:120], str(r.get("yonalish") or "")[:120],
                     str(r.get("bob") or "")[:160], r.get("raqam") if isinstance(r.get("raqam"), int) else None, mav,
                     str(r.get("en") or "")[:300], str(r.get("manba") or "")[:120], str(r.get("url") or "")[:300], yoz,
                     "kutmoqda" if yoz else "otkazildi"))
                n += cur.rowcount
        return n

    # ---------------------------------------------------- sozlamalar
    def sozlama(self) -> dict:
        self.migrate()
        with self.ps.db() as cur:
            cur.execute("SELECT qiymat FROM taqdimot_kutubxona_sozlama WHERE kalit='yozuvchi'")
            r = cur.fetchone()
        z = dict(STANDART)
        if r:
            q = r["qiymat"] if isinstance(r["qiymat"], dict) else json.loads(r["qiymat"])
            z.update({k: q[k] for k in STANDART if k in q})
        return z

    def sozlama_saqla(self, body) -> dict:
        z = self.sozlama()
        if isinstance(body.get("yoqilgan"), bool):
            z["yoqilgan"] = body["yoqilgan"]
        if isinstance(body.get("tun"), bool):
            z["tun"] = body["tun"]
        if body.get("kunlik") is not None:
            try:
                z["kunlik"] = max(0, min(5000, int(body["kunlik"])))
            except (TypeError, ValueError):
                pass
        if body.get("tartib") in ("maktab", "otm", "sinf"):
            z["tartib"] = body["tartib"]
        for k, ok in (("daraja", lambda v: v in DARAJALAR), ("sinflar", lambda v: isinstance(v, str) and len(v) <= 20),
                      ("fanlar", lambda v: isinstance(v, str) and len(v) <= 120)):
            if isinstance(body.get(k), list):
                z[k] = [v for v in body[k] if ok(v)][:60]
        with self.ps.db() as cur:
            cur.execute("INSERT INTO taqdimot_kutubxona_sozlama(kalit, qiymat) VALUES('yozuvchi', %s) "
                        "ON CONFLICT (kalit) DO UPDATE SET qiymat=EXCLUDED.qiymat, vaqt=now()", (json.dumps(z, ensure_ascii=False),))
        if z["yoqilgan"]:
            self.ishga_tushir()
        return z

    def _holat_yoz(self, kalit, qiymat):
        with self.ps.db() as cur:
            cur.execute("INSERT INTO taqdimot_kutubxona_sozlama(kalit, qiymat) VALUES(%s, %s) "
                        "ON CONFLICT (kalit) DO UPDATE SET qiymat=EXCLUDED.qiymat, vaqt=now()", (kalit, json.dumps(qiymat, ensure_ascii=False)))

    def _holat_ol(self, kalit):
        with self.ps.db() as cur:
            cur.execute("SELECT qiymat, vaqt FROM taqdimot_kutubxona_sozlama WHERE kalit=%s", (kalit,))
            r = cur.fetchone()
        if not r:
            return None
        q = r["qiymat"] if isinstance(r["qiymat"], dict) else json.loads(r["qiymat"])
        q["vaqt"] = r["vaqt"].isoformat() if hasattr(r["vaqt"], "isoformat") else r["vaqt"]
        return q

    # ---------------------------------------------------- holat (admin)
    def holat(self) -> dict:
        self.migrate()
        with self.ps.db() as cur:
            cur.execute("SELECT daraja, sinf, fan, holat, count(*) AS n FROM taqdimot_mavzular GROUP BY daraja, sinf, fan, holat")
            rows = cur.fetchall()
            cur.execute("SELECT count(*) AS n FROM taqdimot_mavzular WHERE holat='tayyor' AND yozildi > now() - interval '1 day'")
            bugun = cur.fetchone()["n"]
            # kunlik chegaraga kiradiganlar (yozuvchi shu sonni tekshiradi): oxirgi 24 soatda boshlangan urinishlar
            cur.execute("SELECT count(*) AS n FROM taqdimot_mavzular WHERE boshlandi > now() - interval '1 day' AND holat IN ('tayyor','yozilmoqda','xato')")
            sarf = cur.fetchone()["n"]
            cur.execute("SELECT id, daraja, sinf, fan, mavzu, xato, urinish FROM taqdimot_mavzular WHERE holat='xato' ORDER BY boshlandi DESC NULLS LAST LIMIT 20")
            xatolar = [_qator(r) for r in cur.fetchall()]
            cur.execute("SELECT id, daraja, sinf, fan, mavzu, boshlandi FROM taqdimot_mavzular WHERE holat='yozilmoqda' ORDER BY boshlandi DESC LIMIT 3")
            hozir = [_qator(r) for r in cur.fetchall()]
            cur.execute("SELECT manba, count(*) AS n FROM taqdimot_mavzular GROUP BY manba ORDER BY n DESC")
            manbalar = [_qator(r) for r in cur.fetchall()]
            cur.execute("SELECT ochiq_holat, count(*) AS n FROM taqdimot_mavzular WHERE holat='tayyor' GROUP BY ochiq_holat")
            dars_mazmuni = {r["ochiq_holat"]: r["n"] for r in cur.fetchall()}
        jami = {h: 0 for h in HOLATLAR}
        guruh = {}
        for r in rows:
            jami[r["holat"]] = jami.get(r["holat"], 0) + r["n"]
            g = guruh.setdefault((r["daraja"], r["sinf"], r["fan"]), {h: 0 for h in HOLATLAR})
            g[r["holat"]] = g.get(r["holat"], 0) + r["n"]
        fanlar = [{"daraja": d, "sinf": s, "fan": f, **v} for (d, s, f), v in
                  sorted(guruh.items(), key=lambda kv: (DARAJALAR.index(kv[0][0]) if kv[0][0] in DARAJALAR else 9, sinf_tartib(kv[0][1]), kv[0][1], kv[0][2]))]
        from . import ai
        return {"jami": jami, "bugun": bugun, "sarf": sarf, "ai": ai.mavjud(), "kalitlar": ai.kalitlar_holati(), "tun_hozir": tun_vaqtimi(),
                "sozlama": self.sozlama(), "fanlar": fanlar, "xatolar": xatolar, "hozir": hozir,
                "manbalar": manbalar, "yigish": self._holat_ol("yigish"), "dars_mazmuni": dars_mazmuni}

    def navbat(self, body) -> int:
        """Tanlangan mavzularni qayta navbatga qo'yish yoki o'tkazib yuborish."""
        amal = body.get("amal")
        shart, args = ["true"], []
        for k, col in (("daraja", "daraja"), ("sinf", "sinf"), ("fan", "fan")):
            if isinstance(body.get(k), str) and body[k]:
                shart.append(f"{col}=%s")
                args.append(body[k])
        if isinstance(body.get("id"), int):
            shart.append("id=%s")
            args.append(body["id"])
        w = " AND ".join(shart)
        with self.ps.db() as cur:
            if amal == "qayta":       # xato yoki tayyorni qayta yozish
                cur.execute(f"UPDATE taqdimot_mavzular SET holat='kutmoqda', yozilsin=true, urinish=0, xato=NULL WHERE {w} AND holat IN ('xato','tayyor','otkazildi')", args)
            elif amal == "xatolarni":
                cur.execute(f"UPDATE taqdimot_mavzular SET holat='kutmoqda', urinish=0, xato=NULL WHERE {w} AND holat='xato'", args)
            elif amal == "otkaz":
                cur.execute(f"UPDATE taqdimot_mavzular SET holat='otkazildi', yozilsin=false WHERE {w} AND holat IN ('kutmoqda','xato')", args)
            elif amal == "yoq":       # o'tkazilganni qaytarish
                cur.execute(f"UPDATE taqdimot_mavzular SET holat='kutmoqda', yozilsin=true WHERE {w} AND holat='otkazildi'", args)
            else:
                return 0
            return cur.rowcount

    # ---------------------------------------------------- foydalanuvchi uchun ro'yxat
    def royxat(self, daraja="", sinf="", fan="", q="", faqat_tayyor=True, limit=400) -> dict:
        """daraxt: daraja–sinf–fan bo'yicha (tayyor/jami); mavzular: filtr bo'yicha (limit=0 — faqat daraxt)."""
        self.migrate()
        shart, args = ["yozilsin"], []
        if faqat_tayyor:
            shart.append("holat='tayyor'")
        for col, v in (("daraja", daraja), ("sinf", sinf), ("fan", fan)):
            if v:
                shart.append(f"{col}=%s")
                args.append(v)
        if q:
            shart.append("mavzu ILIKE %s")
            args.append(f"%{q[:60]}%")
        w = " AND ".join(shart)
        with self.ps.db() as cur:
            cur.execute("SELECT daraja, sinf, fan, count(*) FILTER (WHERE holat='tayyor') AS tayyor, count(*) AS jami "
                        "FROM taqdimot_mavzular WHERE yozilsin GROUP BY daraja, sinf, fan")
            daraxt = [_qator(r) for r in cur.fetchall()]
        mav = []
        if limit > 0:
            mav = self._mavzular(w, args, limit)
        daraxt.sort(key=lambda r: (DARAJALAR.index(r["daraja"]) if r["daraja"] in DARAJALAR else 9, sinf_tartib(r["sinf"]), r["sinf"], r["fan"]))
        return {"daraxt": daraxt, "mavzular": mav}

    def _mavzular(self, w, args, limit) -> list:
        with self.ps.db() as cur:
            cur.execute(f"SELECT id, daraja, sinf, fan, bob, raqam, mavzu, holat, manba, "
                        f"(SELECT COALESCE(sum(jsonb_array_length(b->'slaydlar')),0) FROM jsonb_array_elements("
                        f"CASE WHEN jsonb_typeof(miya->'bolimlar')='array' THEN miya->'bolimlar' ELSE '[]'::jsonb END) b "
                        f"WHERE jsonb_typeof(b->'slaydlar')='array') AS slaydlar, "
                        f"COALESCE(CASE WHEN jsonb_typeof(miya->'dars'->'bosqichlar')='array' THEN jsonb_array_length(miya->'dars'->'bosqichlar')>0 END, false) AS dars_rejasi "
                        f"FROM taqdimot_mavzular WHERE {w} ORDER BY daraja, sinf, fan, raqam NULLS LAST, id LIMIT %s", args + [max(1, min(limit, 2000))])
            return [_qator(r) for r in cur.fetchall()]

    def miya(self, i: int):
        self.migrate()
        with self.ps.db() as cur:
            cur.execute("SELECT miya FROM taqdimot_mavzular WHERE id=%s AND holat='tayyor'", (i,))
            r = cur.fetchone()
        if not r:
            return None
        return r["miya"] if isinstance(r["miya"], dict) else json.loads(r["miya"])

    # ---------------------------------------------------- infoedu.uz yig'ish
    def yigish_boshla(self, sinflar) -> dict:
        self.migrate()
        if self._yigish and self._yigish.is_alive():
            return {"holat": "ishlamoqda"}
        with self.ps.db() as cur:   # boshqa gunicorn worker yig'ayotgan bo'lsa (holat 10 daqiqa ichida yangilangan)
            cur.execute("SELECT 1 FROM taqdimot_kutubxona_sozlama WHERE kalit='yigish' AND qiymat->>'holat'='ishlamoqda' "
                        "AND vaqt > now() - interval '10 minutes'")
            if cur.fetchone():
                return {"holat": "ishlamoqda"}
        sinflar = [s for s in sinflar if isinstance(s, int) and 1 <= s <= 11] or list(range(1, 12))
        self._yigish = threading.Thread(target=self._yigish_ish, args=(sinflar,), daemon=True, name="taqdimot-yigish")
        self._yigish.start()
        return {"holat": "boshlandi", "sinflar": sinflar}

    def _ol(self, url) -> str:
        import httpx
        if not url.startswith(INFOEDU + "/"):
            raise ValueError("ruxsat etilmagan manba")
        r = httpx.get(url, timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (compatible; TalimKabutar/1.0; +https://talimkabutar.uz)"})
        r.raise_for_status()
        return r.text

    def _yigish_ish(self, sinflar):
        h = {"holat": "ishlamoqda", "sinflar": sinflar, "sahifalar": 0, "mavzular": 0, "qoshildi": 0, "bosh": [], "xatolar": []}
        try:
            for g in sinflar:
                h["joriy"] = f"{g}-sinf"
                self._holat_yoz("yigish", h)
                try:
                    bosh = self._ol(f"{INFOEDU}/darsliklar/{g}")
                except Exception as exc:
                    h["xatolar"].append(f"{g}-sinf ro‘yxati: {str(exc)[:120]}")
                    continue
                yollar = sorted(set(re.findall(rf'href="(?:https?://infoedu\.uz)?(/darsliklar/{g}/{g}-sinf-[a-z0-9\-]+)/?"', bosh)))
                for yol in yollar:
                    slug = yol.rsplit(f"{g}-sinf-", 1)[-1]
                    fan = FAN_SLUG.get(slug) or slug.replace("-", " ").capitalize()
                    url = INFOEDU + yol
                    time.sleep(2.5)
                    try:
                        matn = html_matn(self._ol(url))
                    except Exception as exc:
                        h["xatolar"].append(f"{g}-sinf {fan}: {str(exc)[:100]}")
                        continue
                    mav = mundarija(matn)
                    if len(mav) < 4:
                        try:
                            mav = ai_mavzular(matn, fan, f"{g}-sinf")
                        except Exception:
                            mav = []
                    h["sahifalar"] += 1
                    h["mavzular"] += len(mav)
                    if not mav:
                        h["bosh"].append(f"{g}-sinf {fan}")
                        continue
                    n = self.qosh([{"daraja": "maktab", "sinf": str(g), "fan": fan, "bob": x["bob"], "raqam": x["raqam"], "mavzu": x["mavzu"],
                                    "manba": "infoedu.uz darslik mundarijasi", "url": url} for x in mav], ustun=True)
                    h["qoshildi"] += n
                    self._urnini_bosish(str(g), fan)
                    self._holat_yoz("yigish", h)
            h["holat"] = "tugadi"
        except Exception as exc:
            h["holat"] = "xato"
            h["xatolar"].append(str(exc)[:200])
        h.pop("joriy", None)
        self._holat_yoz("yigish", h)

    def _urnini_bosish(self, sinf, fan):
        """Darslik mundarijasi kelgan sinf–fan uchun umumiy dastur asosidagi (taxminiy) mavzular navbatdan chiqadi."""
        nomlar = [fan] + [k for k, v in URNIGA.items() if fan in v]
        with self.ps.db() as cur:
            cur.execute("UPDATE taqdimot_mavzular SET holat='otkazildi', yozilsin=false WHERE daraja='maktab' AND fan = ANY(%s) "
                        "AND (sinf=%s OR CASE WHEN sinf ~ '^[0-9]+–[0-9]+$' THEN %s BETWEEN split_part(sinf,'–',1)::int "
                        "AND split_part(sinf,'–',2)::int ELSE false END) "
                        "AND manba LIKE 'reja%%' AND holat IN ('kutmoqda','xato')", (nomlar, sinf, int(sinf)))

    # ---------------------------------------------------- fan dasturi yuklash
    def dastur_yukla(self, nom, data, meta) -> dict:
        self.migrate()
        daraja = meta.get("daraja") if meta.get("daraja") in DARAJALAR else "bakalavr"
        fan = re.sub(r"\s+", " ", str(meta.get("fan") or "")).strip()[:120]
        if len(fan) < 2:
            raise ValueError("Fan nomini yozing")
        sinf = str(meta.get("sinf") or "").strip()[:20]
        matn, jadval = fayl_matni(nom, data)
        mav = [{"raqam": r or i, "mavzu": t, "bob": ""} for i, (r, t) in enumerate(jadval, 1)] if len(jadval) >= 4 else dastur_qatorlari(matn)
        usul = "jadval" if len(jadval) >= 4 else "qatorlar"
        if len(mav) < 4:
            mav = ai_mavzular(matn, fan, sinf)
            usul = "AI"
        n = self.qosh([{"daraja": daraja, "sinf": sinf, "fan": fan, "yonalish": str(meta.get("yonalish") or "")[:120], "bob": x["bob"],
                        "raqam": x["raqam"], "mavzu": x["mavzu"], "manba": f"fan dasturi: {nom[:80]}"} for x in mav], ustun=True)
        return {"topildi": len(mav), "qoshildi": n, "usul": usul, "namuna": [x["mavzu"] for x in mav[:8]]}

    # ---------------------------------------------------- yozuvchi
    def ishga_tushir(self):
        if self._ip and self._ip.is_alive():
            return
        self._ip = threading.Thread(target=self._sikl, daemon=True, name="taqdimot-kutubxona")
        self._ip.start()

    def _sikl(self):
        while True:
            dam = 60
            try:
                ishladi = self.qadam()
                dam = TANAFFUS if ishladi else 60
            except Exception:
                dam = 120
            time.sleep(dam)

    def _ijara(self) -> bool:
        with self.ps.db() as cur:
            cur.execute("SELECT qiymat, vaqt FROM taqdimot_kutubxona_sozlama WHERE kalit='ishchi' FOR UPDATE")
            r = cur.fetchone()
            q = (r["qiymat"] if isinstance(r["qiymat"], dict) else json.loads(r["qiymat"])) if r else {}
            if r and q.get("pid") != self.pid:
                cur.execute("SELECT %s::timestamptz > now() - make_interval(mins => %s) AS band", (r["vaqt"], IJARA_DAQ))
                if cur.fetchone()["band"]:
                    return False
            cur.execute("INSERT INTO taqdimot_kutubxona_sozlama(kalit, qiymat) VALUES('ishchi', %s) "
                        "ON CONFLICT (kalit) DO UPDATE SET qiymat=EXCLUDED.qiymat, vaqt=now()", (json.dumps({"pid": self.pid}),))
            return True

    def _foydalanuvchi_band(self) -> bool:
        """Hozir foydalanuvchi taqdimot yozdirayaptimi — yozuvchi navbat bermaydi (AI limiti avval odamlarga)."""
        try:
            with self.ps.db() as cur:
                cur.execute("SELECT count(*) AS n FROM taqdimot_dvigatel_ishlar WHERE holat IN ('navbatda','yozilmoqda') "
                            "AND yaratildi > now() - interval '6 minutes'")
                return cur.fetchone()["n"] > 0
        except Exception:
            return False

    def _tartib(self, z) -> str:
        manba = "CASE WHEN manba LIKE 'reja%%' THEN 1 ELSE 0 END"
        sinf = "COALESCE(NULLIF(substring(sinf from '\\d+'), '')::int, 99)"
        dr = {"maktab": "CASE daraja WHEN 'maktab' THEN 0 WHEN 'bakalavr' THEN 1 ELSE 2 END",
              "otm": "CASE daraja WHEN 'bakalavr' THEN 0 WHEN 'magistr' THEN 1 ELSE 2 END",
              "sinf": "0"}[z.get("tartib") if z.get("tartib") in ("maktab", "otm", "sinf") else "maktab"]
        fan = fan_tartibi_sql()
        if z.get("tartib") == "sinf":
            return f"{sinf}, {fan}, {manba}, fan, raqam NULLS LAST, id"
        return f"{dr}, {fan}, {manba}, {sinf}, fan, raqam NULLS LAST, id"

    def qadam(self) -> bool:
        """Bitta mavzuni yozadi (yoki hech narsa qilmaydi). Qaytaradi: yozishga urindimi."""
        self.migrate()
        z = self.sozlama()
        if not z["yoqilgan"]:
            return False
        from . import ai
        if not ai.mavjud():
            return False
        if z.get("tun") and not tun_vaqtimi():
            return False
        if ai.tugaganmi():          # kalitlar limitda — qolgan so'rovlar foydalanuvchilarga qolsin
            return False
        if self._foydalanuvchi_band():
            return False
        if not self._ijara():
            return False
        with self.ps.db() as cur:
            cur.execute("UPDATE taqdimot_mavzular SET holat='kutmoqda' WHERE holat='yozilmoqda' AND boshlandi < now() - make_interval(mins => %s)", (ESKI_DAQ,))
            cur.execute("SELECT (SELECT count(*) FROM taqdimot_mavzular WHERE boshlandi > now() - interval '1 day' "
                        "AND holat IN ('tayyor','yozilmoqda','xato')) + (SELECT count(*) FROM taqdimot_mavzular "
                        "WHERE ochiq_vaqt > now() - interval '1 day') AS n")
            if cur.fetchone()["n"] >= z["kunlik"]:
                return False
            shart, args = ["holat='kutmoqda'", "yozilsin"], []
            for k, col in (("daraja", "daraja"), ("sinflar", "sinf"), ("fanlar", "fan")):
                if z.get(k):
                    shart.append(f"{col} = ANY(%s)")
                    args.append(z[k])
            cur.execute(f"UPDATE taqdimot_mavzular SET holat='yozilmoqda', boshlandi=now(), urinish=urinish+1 WHERE id=("
                        f"SELECT id FROM taqdimot_mavzular WHERE {' AND '.join(shart)} ORDER BY {self._tartib(z)} "
                        f"FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING *", args)
            r = cur.fetchone()
        if not r:
            return self._masalliq_qadam(z)
        r = dict(r)
        try:
            m = self.yoz(r)
            with self.ps.db() as cur:
                cur.execute("UPDATE taqdimot_mavzular SET holat='tayyor', miya=%s, yozildi=now(), xato=NULL, ochiq_holat=%s WHERE id=%s",
                            (json.dumps(m, ensure_ascii=False), "tayyor" if bayon_bor(m) else "kutmoqda", r["id"]))
        except Exception as exc:
            from . import ai as _ai
            with self.ps.db() as cur:
                if isinstance(exc, _ai.AiTugadi):   # limit tugagan — mavzu aybdor emas: urinish hisobga olinmaydi
                    cur.execute("UPDATE taqdimot_mavzular SET holat='kutmoqda', urinish=GREATEST(urinish-1, 0), boshlandi=NULL WHERE id=%s", (r["id"],))
                    return False
                cur.execute("UPDATE taqdimot_mavzular SET holat=%s, xato=%s WHERE id=%s",
                            ("xato" if r["urinish"] >= URINISH_MAX else "kutmoqda", str(exc)[:300], r["id"]))
        return True

    def _masalliq_qadam(self, z) -> bool:
        """Yoziladigan mavzu qolmagan bo'lsa: tayyor mavzularga darsning o'zini (bayon, yechimli misollar, guruh topshiriqlari,
        loyiha, ekskursiya…) yozadi — miyaning mazmuniga tayanib, masalliq miya bilan mos bo'lsin."""
        from . import ai
        with self.ps.db() as cur:
            cur.execute(f"UPDATE taqdimot_mavzular SET ochiq_holat='tayyor' WHERE holat='tayyor' AND ochiq_holat <> 'tayyor' AND {BAYON_BOR}")
            cur.execute("UPDATE taqdimot_mavzular SET ochiq_holat='kutmoqda' WHERE ochiq_holat='yozilmoqda' "
                        "AND ochiq_vaqt < now() - make_interval(mins => %s)", (ESKI_DAQ,))
            shart, args = ["holat='tayyor'", "ochiq_holat='kutmoqda'", "ochiq_urinish < %s"], [URINISH_MAX]
            for k, col in (("daraja", "daraja"), ("sinflar", "sinf"), ("fanlar", "fan")):
                if z.get(k):
                    shart.append(f"{col} = ANY(%s)")
                    args.append(z[k])
            cur.execute(f"UPDATE taqdimot_mavzular SET ochiq_holat='yozilmoqda', ochiq_vaqt=now(), ochiq_urinish=ochiq_urinish+1 WHERE id=("
                        f"SELECT id FROM taqdimot_mavzular WHERE {' AND '.join(shart)} ORDER BY {self._tartib(z)} "
                        f"FOR UPDATE SKIP LOCKED LIMIT 1) RETURNING id, daraja, sinf, fan, mavzu, miya, ochiq_urinish", args)
            r = cur.fetchone()
        if not r:
            return False
        miya = r["miya"] if isinstance(r["miya"], dict) else json.loads(r["miya"] or "{}")
        try:
            yangi = ai.masalliq_yoz(r["mavzu"], r["fan"], r["daraja"], sinf_matni(r["daraja"], r.get("sinf") or ""), "",
                                    deadline=220.0, mazmun=ai.miya_mazmuni(miya))
            eski = miya.get("masalliq") or {}
            mas = {k: (v if v and not (isinstance(v, dict) and not any(v.values())) else eski.get(k, v)) for k, v in yangi.items()}
            ok = bool(mas.get("bayon"))
            with self.ps.db() as cur:
                cur.execute("UPDATE taqdimot_mavzular SET miya=jsonb_set(miya, '{masalliq}', %s::jsonb), ochiq_holat=%s WHERE id=%s",
                            (json.dumps(mas, ensure_ascii=False),
                             "tayyor" if ok else ("xato" if r["ochiq_urinish"] >= URINISH_MAX else "kutmoqda"), r["id"]))
        except Exception:
            with self.ps.db() as cur:
                cur.execute("UPDATE taqdimot_mavzular SET ochiq_holat=%s WHERE id=%s",
                            ("xato" if r["ochiq_urinish"] >= URINISH_MAX else "kutmoqda", r["id"]))
        return True

    def bittasini(self, mid: int, pool) -> dict:
        """Admin «sinab ko'rish»: tanlangan mavzuni navbatsiz yozadi (kunlik chegaraga kiradi)."""
        self.migrate()
        with self.ps.db() as cur:
            cur.execute("UPDATE taqdimot_mavzular SET holat='yozilmoqda', boshlandi=now(), urinish=urinish+1 "
                        "WHERE id=%s AND holat <> 'yozilmoqda' RETURNING *", (mid,))
            r = cur.fetchone()
        if not r:
            return {"holat": "topilmadi"}
        r = dict(r)

        def ish():
            try:
                m = self.yoz(r)
                with self.ps.db() as cur:
                    cur.execute("UPDATE taqdimot_mavzular SET holat='tayyor', yozilsin=true, miya=%s, yozildi=now(), xato=NULL, ochiq_holat=%s "
                                "WHERE id=%s", (json.dumps(m, ensure_ascii=False), "tayyor" if bayon_bor(m) else "kutmoqda", r["id"]))
            except Exception as exc:
                with self.ps.db() as cur:
                    cur.execute("UPDATE taqdimot_mavzular SET holat='xato', xato=%s WHERE id=%s", (str(exc)[:300], r["id"]))
        pool.submit(ish)
        return {"holat": "boshlandi", "id": mid, "mavzu": r["mavzu"]}

    def qoshnilar(self, r) -> tuple[list, list]:
        with self.ps.db() as cur:
            cur.execute("SELECT mavzu, raqam FROM taqdimot_mavzular WHERE daraja=%s AND sinf=%s AND fan=%s AND yozilsin AND id<>%s "
                        "ORDER BY raqam NULLS LAST, id", (r["daraja"], r["sinf"], r["fan"], r["id"]))
            rows = cur.fetchall()
        raqam = r.get("raqam") or 0
        oldin = [x["mavzu"] for x in rows if (x["raqam"] or 0) < raqam][-3:]
        keyin = [x["mavzu"] for x in rows if (x["raqam"] or 0) > raqam][:3]
        return oldin, keyin

    def yoz(self, r) -> dict:
        from . import ai
        oldin, keyin = self.qoshnilar(r)
        return ai.miya_yoz(*yozish_argumentlari(r, oldin, keyin), deadline=240.0, sozlama=yozish_sozlamasi(r), masalliq=True)


def yozish_sozlamasi(r) -> dict:
    s = sinf_tartib(r.get("sinf") or "")
    if r["daraja"] == "maktab":
        return {"slayd_soni": 8 if s <= 4 else 10 if s <= 9 else 12, "hajm": "orta" if s <= 4 else "batafsil", "til": "uz"}
    return {"slayd_soni": 14, "hajm": "toliq", "til": "uz"}


def yozish_argumentlari(r, oldin, keyin) -> tuple:
    """ai.miya_yoz uchun: (mavzu, fan, daraja, sinf, tur, qoshimcha, manba)."""
    tur = "dars" if r["daraja"] == "maktab" else "ma’ruza"
    q = [f"Bu mavzu «{r['fan']}» fanining o‘quv dasturidagi mavzu" + (f" ({r['raqam']}-mavzu)" if r.get("raqam") else "") + "."]
    if r.get("bob"):
        q.append(f"Bob / bo‘lim: {r['bob']}.")
    if r.get("yonalish"):
        q.append(f"Yo‘nalish: {r['yonalish']}.")
    if oldin:
        q.append("Oldingi mavzular: " + "; ".join(oldin) + ".")
    if keyin:
        q.append("Keyingi mavzular: " + "; ".join(keyin) + " — ularni bu taqdimotda o‘tma, faqat shu mavzuni to‘liq yorit.")
    q.append("Rasmlar ro‘yxatidagi «(rejada)» belgili kalitlar ham ishlatilsin: ular keyinroq chiziladi va taqdimotga o‘zi qo‘shiladi.")
    manba = f"Mavzu tavsifi (ingliz tilida, rasm uchun): {r['en']}" if r.get("en") else ""
    return (r["mavzu"], r["fan"], r["daraja"], sinf_matni(r["daraja"], r.get("sinf") or ""), tur, " ".join(q), manba)

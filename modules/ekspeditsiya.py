"""REV456: «🧭 Matematik ekspeditsiya» — maktab matematikasi bo'yicha 20 bosqichli xarita, har bosqichda 15 topshiriq.
Spiral: 8 ta joriy mavzu + 4 ta yaqin takror (1–3 bosqich oldin) + 3 ta uzoq takror (5, 10, 15 bosqich oldin).
Xato qilingan mavzu turi (Leitner): keyingi bosqichda va 3 bosqichdan keyin boshqa sonlar bilan qaytadi, 2 marta to'g'ri yechilsa chiqadi.
Har 5-bosqich — «Sinov darvozasi»: oldingi hamma mavzudan aralash 15 ta, o'tish uchun 12 ta to'g'ri."""
import hashlib, json, os, random
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from modules import ekspeditsiya_gen as G

_DASTUR = json.load(open(os.path.join(os.path.dirname(__file__), "ekspeditsiya_dastur.json"), encoding="utf8"))
KURS = {k["kalit"]: k for k in _DASTUR}
_TAYYOR = {"ok": False}
from modules import ekspeditsiya_xalqaro as XB   # REV463: PISA uslubidagi hayotiy masalalar
GEN = {"12": G.gen12, "34": G.gen34, "56": G.gen56, "711": G.gen711, "xb": XB.gen_xb}


def _yulduz(togri, darvoza):
    if darvoza:
        return 3 if togri >= 14 else 2 if togri >= 13 else 1 if togri >= 12 else 0
    return 3 if togri >= 14 else 2 if togri >= 12 else 1 if togri >= 9 else 0


def _topshiriq(kurs, tur, rng, tag):
    fn = GEN[kurs["gen"]]
    for _ in range(6):
        try:
            q, j, y, xs = fn(tur, rng)
        except Exception:   # noqa: BLE001 — bitta generator xatosi bosqichni to'xtatmasin
            continue
        js = str(j)
        var = []
        for x in xs:
            x = str(x)
            if x != js and x not in var:
                var.append(x)
        if not var:
            continue
        var = var[:3]
        hamma = [js] + var
        rng.shuffle(hamma)
        import re as _re
        q = _re.sub(r"(?<![\d,.])1(x)", r"\1", q)   # «1x^2» → «x^2»
        out = {"tur": tur, "tag": tag, "savol": q, "variantlar": hamma, "togri": hamma.index(js), "yechim": y if "Javob" in y else f"{y}\nJavob: {js}"}
        if kurs.get("gen") == "xb":   # REV463: kontekst rasmi (Azizjon yuborgan xalqaro sahnalar)
            out["sahna"] = XB.SAHNA.get(tur.split(":")[0], "")
        return out
    return None


TUR_NOMI = {"ajrat": "Ko‘paytuvchilarga ajratish", "algebra": "O‘xshash hadlar", "alomat": "Bo‘linish alomatlari", "arifprog": "Arifmetik progressiya hadi", "arifyig": "Arifmetik progressiya yig‘indisi", "ayir": "Ko‘p xonali sonlarni ayirish", "aylana": "Aylana uzunligi", "bol": "Bir xonali songa bo‘lish", "bol2": "Ikki xonali songa bo‘lish", "burchak": "Burchak turlari", "burchak_chiziq": "To‘g‘ri chiziqdagi burchaklar", "burchak_nuqta": "Nuqta atrofidagi burchaklar", "chegirma": "Chegirma va QQS", "cheksiz": "Cheksiz geometrik progressiya", "chiziqli": "Chiziqli tenglama", "daraja": "Daraja xossalari", "diagramma": "Doiraviy diagramma", "diskriminant": "Diskriminant", "doira": "Doira yuzi", "ehtimol": "Ehtimollik", "ekstremum": "Funksiya ekstremumi", "fazovektor": "Fazoviy vektor", "foiz": "Foiz", "funksiya": "Chiziqli funksiya qiymati", "geomprog": "Geometrik progressiya", "hajm": "Hajm", "harakat": "Harakat: S = v·t", "hosila": "Hosila", "ifoda": "Ifoda qiymati, amallar tartibi", "ildiz": "Kvadrat ildiz", "integral": "Aniq integral", "jism": "Fazoviy jismlar", "karrali": "Bo‘luvchilar va karralilar", "kasr_n_bol": "Kasrni natural songa bo‘lish", "kasr_n_kop": "Kasrni natural songa ko‘paytirish", "kasrbol": "Kasrlarni bo‘lish", "kasrkop": "Kasrlarni ko‘paytirish", "kasrnat": "Kasrni songa ko‘paytirish", "kasrqisq": "Algebraik kasr", "kasrqosh": "Bir xil maxrajli kasrlar", "kasrqosh2": "Turli maxrajli kasrlar", "kasrtaq": "Kasrlarni taqqoslash", "kombinatorika": "Kombinatorika", "konus": "Konus hajmi", "koordinata": "Koordinata nuri", "kop1": "Bir xonali songa ko‘paytirish", "kop10": "10, 100, 1000 ga ko‘paytirish", "kop2": "Ikki xonali songa ko‘paytirish", "kophad": "Ko‘phadlar ko‘paytmasi", "korsatkich": "Ko‘rsatkichli tenglama", "korxona": "Ko‘p xonali sonlar", "kosinus": "Kosinuslar teoremasi", "kubqirra": "Kub qirrasi", "kvayirma": "Kvadratlar ayirmasi", "kvtenglama": "Kvadrat tenglama", "logarifm": "Logarifm", "logtenglama": "Logarifmik tenglama", "masofa": "Nuqtalar orasidagi masofa", "massa": "Massa birliklari", "meyor": "Me’yor (birlik narxi)", "muntazam": "Muntazam ko‘pburchak", "n_kasr_bol": "Sonni kasrga bo‘lish", "nisbat": "Nisbat", "onli": "O‘nli kasr", "onli10": "O‘nli kasrni 10, 100 ga ko‘paytirish", "ortacha": "O‘rta arifmetik", "ortacha_tezlik": "O‘rtacha tezlik", "osish": "Foiz o‘sishi", "oxshash": "O‘xshash shakllar", "parabola": "Parabola uchi", "parallel": "Parallel chiziqlar burchaklari", "perimetr": "Perimetr", "pifagor": "Pifagor teoremasi", "piramida": "Piramida hajmi", "prizma": "Prizma hajmi", "qarama": "Qarama-qarshi harakat", "qisqa": "Qisqa ko‘paytirish formulalari", "qiymat": "Narx · miqdor = qiymat", "qoldiq": "Qoldiqli bo‘lish", "qolgan": "Qolgan qismning qismi", "qosh": "Ko‘p xonali sonlarni qo‘shish", "qoshni": "Qo‘shni burchaklar", "quvlama": "Quvlama harakat", "radian": "Radian", "sektor": "Sektor yuzi", "shar": "Shar va sfera", "silindr": "Silindr hajmi", "sistema": "Tenglamalar sistemasi", "statistika": "Statistika (mediana)", "taqqos": "Sonlarni taqqoslash", "tenglama": "Tenglama", "tengsizlik": "Tengsizlik", "tengyonli": "Teng yonli uchburchak", "toplam": "To‘plamlar (Venn)", "tortburchak": "Parallelogramm burchaklari", "tortburchak_burchak": "To‘rtburchak burchaklari", "trapetsiya": "Trapetsiya o‘rta chizig‘i", "trapyuz": "Trapetsiya yuzi", "trig": "Trigonometrik qiymatlar", "trigtenglama": "Trigonometrik tenglama", "uchburchak": "Uchburchak burchaklari", "uchburchak_burchak": "Uchburchak burchaklari", "uchburchak_yuz": "Uchburchak yuzi", "ulush": "Sonning ulushi", "unum": "Unumdorlik", "urinma": "Urinma", "uzunlik": "Uzunlik birliklari", "vaqt": "Vaqt birliklari", "vektor": "Vektor uzunligi", "viyet": "Viyet teoremasi", "yaxlit": "Yaxlitlash", "yuz": "Yuz", "yuzbirlik": "Yuz birliklari", "naqsh": "Naqsh (ketma-ketlik)"}


TUR_NOMI.update({f"{k}:{d}": f"{v} ({d}-daraja)" for k, v in XB.NOMI.items() for d in range(1, 7)})   # REV463


ISMLAR = ["Ali", "Malika", "Bekzod", "Dilnoza", "Sardor", "Zarina", "Jasur", "Nilufar"]


def _sonmi(x):
    try:
        return float(str(x).replace(",", ".").replace("−", "-"))
    except ValueError:
        return None


def _qayta_shakl(t, rng, kurs):
    """REV457: topshiriqni boshqa ko'rinishga aylantiradi — xatoni top, chamalash, to'g'ri/noto'g'ri. Mos kelmasa — o'zgarmaydi."""
    q = t["savol"].rstrip(" ?").replace("= \\;?", "").replace("= \\; ?", "").strip()
    js = t["variantlar"][t["togri"]]
    xatolar = [v for k, v in enumerate(t["variantlar"]) if k != t["togri"]]
    tur = "togri_notogri" if kurs.get("gen") == "12" else rng.choice(["xato_top", "togri_notogri", "chamalash"])   # REV461: 1–2-sinfga faqat «to'g'rimi?»
    if tur == "chamalash":
        v = _sonmi(js)
        if v is None or abs(v) < 200 or v != int(v):
            tur = "togri_notogri"
        else:
            v = int(v); k = 10 ** (len(str(abs(v))) - 1)
            if (abs(v) % k) * 2 == k:   # aniq o'rtada (250 — 200 ham, 300 ham) — chamalash noaniq, boshqa ko'rinish
                return _qayta_shakl({**t}, random.Random(rng.random()), {**kurs, "_cham_yoq": True}) if not kurs.get("_cham_yoq") else t
            yaqin = round(v / k) * k
            var = list(dict.fromkeys([yaqin, yaqin * 10, max(k, yaqin // 10), yaqin + 3 * k if yaqin + 3 * k != yaqin else yaqin + k]))[:4]
            if len(var) < 3:
                tur = "togri_notogri"
            else:
                var = [str(x) for x in var]; togri = str(yaqin); rng.shuffle(var)
                return {**t, "korinish": "chamalash", "savol": f"Hisoblamasdan chamalang: {t['savol'].rstrip(' ?')} — javob qaysi songa eng yaqin?",
                        "variantlar": var, "togri": var.index(togri), "yechim": f"Aniq javob: {js}. Eng yaqin yaxlit son — {togri}.\nChamalash: sonlarni yaxlitlab, xonalar sonini bahoalaymiz."}
    ism = rng.choice(ISMLAR)
    if tur == "xato_top" and xatolar:
        ali_haq = rng.random() < 0.3
        javobi = js if ali_haq else rng.choice(xatolar)
        var = [f"{ism} to‘g‘ri topgan"] + [f"To‘g‘ri javob: {x}" for x in [js] + xatolar if x != javobi][:3]
        togri = var[0] if ali_haq else f"To‘g‘ri javob: {js}"
        rng.shuffle(var)
        return {**t, "korinish": "xato_top", "savol": f"{ism} shu topshiriqqa «{javobi}» deb javob berdi:\n{t['savol']}\nUning javobini tekshiring.",
                "variantlar": var, "togri": var.index(togri), "yechim": t["yechim"]}
    # to'g'ri / noto'g'ri — nega
    haq = rng.random() < 0.5 or not xatolar
    aytilgan = js if haq else rng.choice(xatolar)
    var = ["To‘g‘ri", "Noto‘g‘ri"]
    return {**t, "korinish": "togri_notogri", "savol": f"Tasdiq: {t['savol'].rstrip(' ?')} — javobi «{aytilgan}». Shu to‘g‘rimi?",
            "variantlar": var, "togri": 0 if haq else 1, "yechim": t["yechim"]}


def _naqsh(rng, kurs):
    """REV457: naqsh — ketma-ketlikni davom ettirish (sinfga mos)."""
    g = int("".join(c for c in kurs["kalit"] if c.isdigit()) or 5)
    r = rng.randint
    tur = rng.choice(["arif", "geom", "kvadrat", "almash"] if g >= 7 else ["arif", "almash"] if g <= 2 else ["arif", "geom", "almash"])
    if tur == "arif":
        a, d = (r(1, 10), r(1, 3)) if g <= 2 else (r(1, 30), rng.choice([r(2, 9), r(11, 25)] if g >= 5 else [r(2, 9)]))
        q = [a + i * d for i in range(5)]; j = a + 5 * d; izoh = f"Har safar {d} ga oshadi"
    elif tur == "geom":
        a, k = r(1, 5), rng.choice([2, 3])
        q = [a * k ** i for i in range(5)]; j = a * k ** 5; izoh = f"Har safar {k} marta oshadi"
    elif tur == "kvadrat":
        s0 = r(1, 6); q = [(s0 + i) ** 2 for i in range(5)]; j = (s0 + 5) ** 2; izoh = "Ketma-ket sonlarning kvadratlari"
    else:
        a, b = (r(2, 4), r(1, 2)) if g <= 2 else (r(2, 9), r(2, 9))
        q = [r(3, 10) if g <= 2 else r(10, 30)]
        for i in range(4):
            q.append(q[-1] + (a if i % 2 == 0 else -b))
        j = q[-1] + a; izoh = f"Navbat bilan +{a} va −{b}"
    xs = list(dict.fromkeys([j + 1, j - 1, j + (q[-1] - q[-2]), j * 2]))
    xs = [x for x in xs if x != j][:3]
    var = [str(j)] + [str(x) for x in xs]; rng.shuffle(var)
    return {"tur": "naqsh", "tag": "yangi", "korinish": "naqsh", "savol": f"Ketma-ketlikni davom ettiring: {', '.join(map(str, q))}, …?",
            "variantlar": var, "togri": var.index(str(j)), "yechim": f"{izoh}.\nJavob: {j}"}


def bosqich_yasa(kurs, n, holat, urinish=0, uid=0):
    """15 ta topshiriq (spiral). holat — o'quvchining xatolar navbati uchun."""
    B = kurs["bosqichlar"]
    seed = int(hashlib.sha1(f"{uid}:{kurs['kalit']}:{n}:{urinish}".encode()).hexdigest()[:12], 16)
    rng = random.Random(seed)
    darvoza = n % 5 == 0
    reja = []
    if darvoza:
        hammasi = [t for b in B[:n] for t in b["turlar"]]
        reja = [(rng.choice(hammasi), "darvoza") for _ in range(15)]
    else:
        joriy = B[n - 1]["turlar"] or B[max(0, n - 2)]["turlar"]
        reja += [(joriy[i % len(joriy)], "yangi") for i in range(8)]
        yaqin = [t for b in B[max(0, n - 4):n - 1] for t in b["turlar"]] or joriy
        reja += [(rng.choice(yaqin), "takror") for _ in range(4)]
        uzoq_b = [B[k - 1] for k in (n - 5, n - 10, n - 15) if k >= 1]
        uzoq = [t for b in uzoq_b for t in b["turlar"]] or yaqin
        reja += [(rng.choice(uzoq), "uzoq") for _ in range(3)]
        # xatolar navbati — muddati kelganlari oxirgi o'rinlarni egallaydi (ko'pi bilan 4 ta)
        kelgan = [x for x in (holat.get("xato") or []) if x.get("qaytadi", 99) <= n][:4]
        for i, x in enumerate(kelgan):
            reja[14 - i] = (x["tur"], "xato")
    out = []
    for tur, tag in reja:
        t = _topshiriq(kurs, tur, rng, tag)
        if t:
            out.append(t)
    # REV457: ko'rinishlar aralashmasi — 15 tadan ~4 tasi boshqa shaklda (xatoni top, chamalash, to'g'ri/noto'g'ri), 1 ta naqsh
    if out:
        joylar = rng.sample(range(len(out)), min(2 if kurs.get("gen") == "12" else 4, len(out)))
        for k in joylar:
            out[k] = _qayta_shakl(out[k], rng, kurs)
        if not darvoza and len(out) >= 10:
            out[rng.randrange(1, 8)] = {**_naqsh(rng, kurs), "tag": "yangi"}
    for t in out:
        t.setdefault("korinish", "oddiy")
    rng.shuffle(out) if darvoza else None
    return out


class Natija(BaseModel):
    togri: int
    togri_turlar: List[str] = []
    xato_turlar: List[str] = []
    vaqt: int = 0                     # REV459: bosqichga ketgan soniyalar (tezkor nishoni uchun)
    korinish_togri: dict = {}         # REV459: {"xato_top": 2, "chamalash": 1, "naqsh": 1}


NISHONLAR = {   # REV459: kalit → (nomi, sharti matnda)
    "birinchi_qadam": "Birinchi bosqich", "xatosiz": "Xatosiz bosqich (15/15)", "tezkor": "Tezkor (5 daqiqadan tez, 12+ to‘g‘ri)", "darvoza_zabti": "Darvozani o‘tdi",
    "ketma_ket_7": "7 kun ketma-ket", "ketma_ket_30": "30 kun ketma-ket", "kasr_ustasi": "Kasrlar ustasi", "geometr": "Geometr", "algebraist": "Algebraist",
    "hisobchi": "Tez hisobchi", "mantiqchi": "Mantiqchi", "masalachi": "Masala yechuvchi", "xatoni_topuvchi": "Xato topuvchi", "chamalovchi": "Aniq chamalovchi",
    "qaytgan": "Unutilgan mavzuni tikladi", "100_masala": "100 ta masala", "1000_masala": "1000 ta masala",
}
_HISOB = {"qosh", "ayir", "kop1", "kop2", "kop10", "bol", "bol2", "qoldiq"}
_MASALA = {"harakat", "qarama", "quvlama", "qiymat", "unum", "nisbat", "meyor", "chegirma", "osish", "foiz", "ortacha_tezlik", "qolgan", "toplam"}


def _yangi_nishonlar(d, kurs, n, body, s, chiqdi):
    bor = set((d.get("nishonlar") or {}).keys()); yangi = []
    st = d.get("tur_stat") or {}; kt = d.get("korinish_stat") or {}
    def togri_soni(turlar): return sum(v[0] for t, v in st.items() if t in turlar)
    shart = {
        "birinchi_qadam": s >= 1, "xatosiz": body.togri >= 15, "tezkor": 0 < body.vaqt < 300 and body.togri >= 12, "darvoza_zabti": n % 5 == 0 and s >= 1,
        "ketma_ket_7": d.get("streak", 0) >= 7, "ketma_ket_30": d.get("streak", 0) >= 30,
        "kasr_ustasi": (lambda a, j: j >= 30 and a / j >= 0.9)(*[sum(v[i] for t, v in st.items() if t.startswith("kasr") or "kasr" in t) for i in (0, 1)]),
        "geometr": kurs["kalit"].startswith("geo") and sum(1 for v in (d.get("yulduz") or {}).values() if int(v) >= 1) >= 10,
        "algebraist": kurs["kalit"].startswith("alg") and sum(1 for v in (d.get("yulduz") or {}).values() if int(v) >= 1) >= 10,
        "hisobchi": togri_soni(_HISOB) >= 50, "masalachi": togri_soni(_MASALA) >= 50, "mantiqchi": int(kt.get("naqsh", 0)) >= 20,
        "xatoni_topuvchi": int(kt.get("xato_top", 0)) >= 20, "chamalovchi": int(kt.get("chamalash", 0)) >= 15,
        "qaytgan": chiqdi > 0, "100_masala": d.get("jami", 0) >= 100, "1000_masala": d.get("jami", 0) >= 1000,
    }
    for k, ok in shart.items():
        if ok and k not in bor:
            yangi.append(k)
    return yangi


def create_router(platform):
    router = APIRouter(tags=["ekspeditsiya"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            if not _TAYYOR["ok"]:
                cur.execute("""CREATE TABLE IF NOT EXISTS ekspeditsiya_holat(user_id BIGINT NOT NULL, kurs TEXT NOT NULL, data JSONB NOT NULL DEFAULT '{}'::jsonb,
                               updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(user_id, kurs))""")
                cur.execute("""CREATE TABLE IF NOT EXISTS ekspeditsiya_profil(user_id BIGINT PRIMARY KEY, avatar TEXT NOT NULL DEFAULT '',
                               updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")   # REV464: tanlangan avatar
                conn.commit(); _TAYYOR["ok"] = True
            r = fn(cur); conn.commit(); return r
        finally:
            cur.close(); conn.close()

    def admin_mi(cur, u):
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (u,))
        return cur.fetchone() is not None

    def ol(cur, u, kurs):
        cur.execute("SELECT data FROM ekspeditsiya_holat WHERE user_id=%s AND kurs=%s", (u, kurs))
        r = cur.fetchone()
        return (r["data"] if isinstance(r, dict) else r[0]) if r else {}

    def yoz(cur, u, kurs, d):
        cur.execute("""INSERT INTO ekspeditsiya_holat(user_id, kurs, data) VALUES(%s,%s,%s::jsonb)
                       ON CONFLICT(user_id, kurs) DO UPDATE SET data=EXCLUDED.data, updated_at=NOW()""", (u, kurs, json.dumps(d, ensure_ascii=False)))

    def kurs_ol(k):
        if k not in KURS:
            raise HTTPException(404, "Bunday ekspeditsiya yo'q")
        return KURS[k]

    def xarita(d, kurs, adm):
        yul = d.get("yulduz") or {}
        out = []
        for i, b in enumerate(kurs["bosqichlar"], 1):
            s = int(yul.get(str(i), 0))
            ochiq = adm or i == 1 or int(yul.get(str(i - 1), 0)) >= 1
            out.append({"n": i, "mavzu": b["mavzu"], "yulduz": s, "holat": "otdi" if s else "ochiq" if ochiq else "yopiq", "darvoza": i % 5 == 0})
        return out

    class Profil(BaseModel):
        avatar: str

    @router.get("/api/ekspeditsiya/profil")
    def profil(token: str = "", authorization: Optional[str] = Header(None)):
        """REV464: o'quvchining avatari (avatar_01 … avatar_12)."""
        u = uid(token, authorization)
        def f(cur):
            cur.execute("SELECT avatar FROM ekspeditsiya_profil WHERE user_id=%s", (u,))
            r = cur.fetchone()
            return {"avatar": (r["avatar"] if isinstance(r, dict) else r[0]) if r else ""}
        return run(f)

    @router.post("/api/ekspeditsiya/profil")
    def profil_yoz(body: Profil, token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        a = str(body.avatar or "")
        if a and not (a.startswith("avatar_") and a[7:].isdigit() and 1 <= int(a[7:]) <= 12):
            raise HTTPException(400, "Bunday avatar yo'q")
        def f(cur):
            cur.execute("""INSERT INTO ekspeditsiya_profil(user_id, avatar) VALUES(%s,%s)
                           ON CONFLICT(user_id) DO UPDATE SET avatar=EXCLUDED.avatar, updated_at=NOW()""", (u, a))
            return {"avatar": a}
        return run(f)

    @router.get("/api/ekspeditsiya/{kurs}/reyting")
    def reyting(kurs: str, token: str = "", authorization: Optional[str] = Header(None)):
        """REV464: guruhdoshlar reytingi (o'quvchi a'zo bo'lgan kurs guruhlari bo'yicha) — ism va familiya bosh harfi, avatar, yulduzlar."""
        u = uid(token, authorization); kurs_ol(kurs)
        def f(cur):
            try:
                cur.execute("""SELECT DISTINCT a2.user_id FROM kurs_guruh_azo a1 JOIN kurs_guruh_azo a2 ON a2.guruh_id=a1.guruh_id WHERE a1.user_id=%s""", (u,))
                ids = [(r["user_id"] if isinstance(r, dict) else r[0]) for r in cur.fetchall()]
            except Exception:
                ids = []
            if not ids:
                return {"reyting": [], "guruhsiz": True}
            cur.execute("""SELECT us.user_id, COALESCE(us.full_name,'') AS ism, e.data, p.avatar FROM users us
                           LEFT JOIN ekspeditsiya_holat e ON e.user_id=us.user_id AND e.kurs=%s
                           LEFT JOIN ekspeditsiya_profil p ON p.user_id=us.user_id WHERE us.user_id = ANY(%s)""", (kurs, ids))
            out = []
            for r in cur.fetchall():
                d = r["data"] or {}
                yul = d.get("yulduz") or {}
                q = str(r["ism"] or "").split()
                ism = (q[0] + (f" {q[1][0]}." if len(q) > 1 and q[1] else "")) if q else "O‘quvchi"
                out.append({"ism": ism, "avatar": r["avatar"] or "", "yulduz": sum(int(v) for v in yul.values()),
                            "bosqich": max([int(n) for n, v in yul.items() if int(v) >= 1] or [0]), "men": r["user_id"] == u})
            out.sort(key=lambda x: (-x["yulduz"], -x["bosqich"]))
            for i, x in enumerate(out, 1):
                x["orin"] = i
            return {"reyting": out[:20] + [x for x in out[20:] if x["men"]], "guruhsiz": False}
        return run(f)

    @router.get("/api/ekspeditsiya/kurslar")
    def kurslar():
        return {"kurslar": [{"kalit": k["kalit"], "nom": k["nom"]} for k in _DASTUR]}

    @router.get("/api/ekspeditsiya/{kurs}")
    def holat(kurs: str, token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization); k = kurs_ol(kurs)
        def f(cur):
            d = ol(cur, u, kurs); adm = admin_mi(cur, u)
            return {"kalit": kurs, "nom": k["nom"], "bosqichlar": xarita(d, k, adm), "streak": d.get("streak", 0), "jami": d.get("jami", 0),
                    "xato_navbat": len(d.get("xato") or []), "admin": adm,
                    "nishonlar": [{"kalit": k_, "nom": v, "olindi": (d.get("nishonlar") or {}).get(k_)} for k_, v in NISHONLAR.items()]}
        return run(f)

    @router.post("/api/ekspeditsiya/{kurs}/{n}/boshlash")
    def boshlash(kurs: str, n: int, token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization); k = kurs_ol(kurs)
        if not 1 <= n <= 20:
            raise HTTPException(400, "Bosqich 1–20")
        def f(cur):
            d = ol(cur, u, kurs); adm = admin_mi(cur, u)
            if xarita(d, k, adm)[n - 1]["holat"] == "yopiq":
                raise HTTPException(403, "Avval oldingi bosqichni o'ting")
            ur = (d.get("urinish") or {}); ur[str(n)] = int(ur.get(str(n), 0)) + 1; d["urinish"] = ur
            yoz(cur, u, kurs, d)
            return {"n": n, "darvoza": n % 5 == 0, "mavzu": k["bosqichlar"][n - 1]["mavzu"], "topshiriqlar": bosqich_yasa(k, n, d, ur[str(n)], u)}
        return run(f)

    @router.post("/api/ekspeditsiya/{kurs}/{n}/natija")
    def natija(kurs: str, n: int, body: Natija, token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization); kurs_ol(kurs)
        def f(cur):
            d = ol(cur, u, kurs)
            s = _yulduz(max(0, min(15, body.togri)), n % 5 == 0)
            yul = d.get("yulduz") or {}
            yul[str(n)] = max(int(yul.get(str(n), 0)), s); d["yulduz"] = yul
            d["jami"] = int(d.get("jami", 0)) + max(0, min(15, body.togri))
            # Leitner: xatolar navbati
            nav = {x["tur"]: x for x in (d.get("xato") or [])}
            chiqdi = 0
            for t in body.xato_turlar[:15]:
                nav[t] = {"tur": t, "qaytadi": n + 1, "marta": 0}
            for t in body.togri_turlar[:15]:
                if t in nav and nav[t].get("qaytadi", 99) <= n:
                    nav[t]["marta"] = int(nav[t].get("marta", 0)) + 1
                    if nav[t]["marta"] >= 2:
                        nav.pop(t); chiqdi += 1
                    else:
                        nav[t]["qaytadi"] = n + 3
            d["xato"] = list(nav.values())[:40]
            st = d.get("tur_stat") or {}   # REV458: mavzu bo'yicha [to'g'ri, jami] — o'qituvchi hisoboti uchun
            for t in body.togri_turlar[:15]:
                a = st.get(t, [0, 0]); st[t] = [a[0] + 1, a[1] + 1]
            for t in body.xato_turlar[:15]:
                a = st.get(t, [0, 0]); st[t] = [a[0], a[1] + 1]
            d["tur_stat"] = st
            try:   # REV480: ko'nikmalar xaritasiga ham
                from modules import konikma as _kn
                _kn.yoz(cur, u, [{"tur": t, "togri": True} for t in body.togri_turlar[:15]] + [{"tur": t, "togri": False} for t in body.xato_turlar[:15]])
            except Exception:   # noqa: BLE001
                pass
            bugun = date.today().isoformat()
            if d.get("kun") != bugun:
                d["streak"] = int(d.get("streak", 0)) + 1 if d.get("kun") == (date.today() - timedelta(days=1)).isoformat() else 1
                d["kun"] = bugun
            kt = d.get("korinish_stat") or {}
            for kk, v in (body.korinish_togri or {}).items():
                if kk in ("xato_top", "chamalash", "naqsh", "togri_notogri"):
                    kt[kk] = int(kt.get(kk, 0)) + max(0, min(15, int(v or 0)))
            d["korinish_stat"] = kt
            yangi = _yangi_nishonlar(d, KURS[kurs], n, body, s, chiqdi)
            nsh = d.get("nishonlar") or {}
            for k_ in yangi:
                nsh[k_] = bugun
            d["nishonlar"] = nsh
            yoz(cur, u, kurs, d)
            return {"yulduz": s, "otdi": s >= 1, "streak": d["streak"], "jami": d["jami"], "xato_navbat": len(d["xato"]),
                    "yangi_nishonlar": [{"kalit": k_, "nom": NISHONLAR[k_]} for k_ in yangi]}
        return run(f)

    @router.get("/api/ekspeditsiya/oqituvchi/guruhlar")
    def guruhlar(token: str = "", authorization: Optional[str] = Header(None)):
        """REV458: o'qituvchining kurs guruhlari (o'quvchilari shu guruhlarga qo'shilgan)."""
        u = uid(token, authorization)
        def f(cur):
            try:
                cur.execute("""SELECT g.id, g.nom, g.fan, g.grade, (SELECT COUNT(*) FROM kurs_guruh_azo a WHERE a.guruh_id=g.id) AS soni
                               FROM kurs_guruh g WHERE g.egasi=%s AND g.faol ORDER BY g.yaratildi DESC""", (u,))
                return {"guruhlar": [dict(r) for r in cur.fetchall()]}
            except Exception:
                return {"guruhlar": []}
        return run(f)

    @router.get("/api/ekspeditsiya/oqituvchi/hisobot")
    def hisobot(guruh: int, kurs: str, token: str = "", authorization: Optional[str] = Header(None)):
        """REV458: guruh bo'yicha ekspeditsiya hisoboti — kim qayerda, aniqlik, zaif mavzular (sinf va har o'quvchi)."""
        u = uid(token, authorization); k = kurs_ol(kurs)
        def f(cur):
            cur.execute("SELECT egasi, nom FROM kurs_guruh WHERE id=%s", (guruh,))
            g = cur.fetchone()
            if not g or (g["egasi"] != u and not admin_mi(cur, u)):
                raise HTTPException(403, "Bu guruh sizniki emas")
            cur.execute("""SELECT a.user_id, COALESCE(NULLIF(us.full_name,''), 'O‘quvchi') AS ism, e.data, p.avatar
                           FROM kurs_guruh_azo a JOIN users us ON us.user_id=a.user_id
                           LEFT JOIN ekspeditsiya_profil p ON p.user_id=a.user_id
                           LEFT JOIN ekspeditsiya_holat e ON e.user_id=a.user_id AND e.kurs=%s WHERE a.guruh_id=%s""", (kurs, guruh))
            qatorlar, sinf = [], {}
            for r in cur.fetchall():
                d = r["data"] or {}
                yul = d.get("yulduz") or {}
                otgan = max([int(n) for n, v in yul.items() if int(v) >= 1] or [0])
                st = d.get("tur_stat") or {}
                tg = sum(v[0] for v in st.values()); jm = sum(v[1] for v in st.values())
                zaif = sorted([(t, v[0] / v[1]) for t, v in st.items() if v[1] >= 3 and v[0] / v[1] < 0.6], key=lambda x: x[1])[:3]
                for t, v in st.items():
                    a = sinf.get(t, [0, 0, 0]); sinf[t] = [a[0] + v[0], a[1] + v[1], a[2] + (1 if v[1] >= 3 and v[0] / v[1] < 0.6 else 0)]
                qatorlar.append({"ism": r["ism"], "avatar": r.get("avatar") or "", "bosqich": otgan, "yulduz": sum(int(v) for v in yul.values()), "aniqlik": round(100 * tg / jm) if jm else None,
                                 "streak": d.get("streak", 0), "oxirgi_kun": d.get("kun", ""), "zaif": [{"tur": t, "nom": TUR_NOMI.get(t, t), "foiz": round(100 * p)} for t, p in zaif]})
            n = len(qatorlar) or 1
            sinf_zaif = sorted([{"tur": t, "nom": TUR_NOMI.get(t, t), "aniqlik": round(100 * v[0] / v[1]), "qiynalganlar": v[2], "ulush": round(100 * v[2] / n)}
                                for t, v in sinf.items() if v[1] >= 5], key=lambda x: (x["aniqlik"], -x["qiynalganlar"]))[:8]
            qatorlar.sort(key=lambda x: (-x["bosqich"], -(x["aniqlik"] or 0)))
            return {"guruh": g["nom"], "kurs": k["nom"], "oquvchilar": qatorlar, "sinf_zaif": sinf_zaif,
                    "boshlamagan": sum(1 for q in qatorlar if q["aniqlik"] is None)}
        return run(f)

    return router

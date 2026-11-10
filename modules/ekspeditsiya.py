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
GEN = {"34": G.gen34, "56": G.gen56, "711": G.gen711}


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
        return {"tur": tur, "tag": tag, "savol": q, "variantlar": hamma, "togri": hamma.index(js), "yechim": y if "Javob" in y else f"{y}\nJavob: {js}"}
    return None


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
    tur = rng.choice(["xato_top", "togri_notogri", "chamalash"])
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
    tur = rng.choice(["arif", "geom", "kvadrat", "almash"] if g >= 7 else ["arif", "geom", "almash"])
    if tur == "arif":
        a, d = r(1, 30), rng.choice([r(2, 9), r(11, 25)] if g >= 5 else [r(2, 9)])
        q = [a + i * d for i in range(5)]; j = a + 5 * d; izoh = f"Har safar {d} ga oshadi"
    elif tur == "geom":
        a, k = r(1, 5), rng.choice([2, 3])
        q = [a * k ** i for i in range(5)]; j = a * k ** 5; izoh = f"Har safar {k} marta oshadi"
    elif tur == "kvadrat":
        s0 = r(1, 6); q = [(s0 + i) ** 2 for i in range(5)]; j = (s0 + 5) ** 2; izoh = "Ketma-ket sonlarning kvadratlari"
    else:
        a, b = r(2, 9), r(2, 9)
        q = [r(10, 30)]
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
        joylar = rng.sample(range(len(out)), min(4, len(out)))
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

    @router.get("/api/ekspeditsiya/kurslar")
    def kurslar():
        return {"kurslar": [{"kalit": k["kalit"], "nom": k["nom"]} for k in _DASTUR]}

    @router.get("/api/ekspeditsiya/{kurs}")
    def holat(kurs: str, token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization); k = kurs_ol(kurs)
        def f(cur):
            d = ol(cur, u, kurs); adm = admin_mi(cur, u)
            return {"kalit": kurs, "nom": k["nom"], "bosqichlar": xarita(d, k, adm), "streak": d.get("streak", 0), "jami": d.get("jami", 0),
                    "xato_navbat": len(d.get("xato") or []), "admin": adm}
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
            for t in body.xato_turlar[:15]:
                nav[t] = {"tur": t, "qaytadi": n + 1, "marta": 0}
            for t in body.togri_turlar[:15]:
                if t in nav and nav[t].get("qaytadi", 99) <= n:
                    nav[t]["marta"] = int(nav[t].get("marta", 0)) + 1
                    if nav[t]["marta"] >= 2:
                        nav.pop(t)
                    else:
                        nav[t]["qaytadi"] = n + 3
            d["xato"] = list(nav.values())[:40]
            bugun = date.today().isoformat()
            if d.get("kun") != bugun:
                d["streak"] = int(d.get("streak", 0)) + 1 if d.get("kun") == (date.today() - timedelta(days=1)).isoformat() else 1
                d["kun"] = bugun
            yoz(cur, u, kurs, d)
            return {"yulduz": s, "otdi": s >= 1, "streak": d["streak"], "jami": d["jami"], "xato_navbat": len(d["xato"])}
        return run(f)

    return router

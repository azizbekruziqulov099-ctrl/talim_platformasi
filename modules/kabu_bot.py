"""REV561: Kabu-bot — AI'SIZ, qoidalarga asoslangan yordamchi (ikki «miya»: o'quvchi va o'qituvchi).

Nega AI emas: javoblar o'quvchi pasportidagi (modules/pasport.py) HAQIQIY raqamlardan quriladi — o'ylab topilgan gap bo'lmaydi, pullik emas,
kunlik chegara kerak emas. Tushunmagan savolga bot bilmasligini aytadi va nima so'ray olishini ko'rsatadi.

O'quvchi miyasi:  natijam / nimani o'rganay / takrorlash / test tuz / formula / mavzu haqida / guruhim / eslatma yoq-o'chir.
  Matematik masala berilsa — bot YECHMAYDI: mavzusini topib, shu mavzu bo'yicha test tuzishni taklif qiladi (to'g'ri javoblar test oxirida).
O'qituvchi miyasi: «22-o'quvchi qayerda?», ism bo'yicha, kim eng zaif, kim faol emas, kirish testini kim topshirmagan, qaysi mavzu ko'p xato, sinf holati.
Yozuv: o'zbek lotin va kirill, apostrofsiz va «ş ç ö ğ» kabi imlo ham tushuniladi.

  POST /api/bot/yoz            — {matn, sinf?, formulalar?: [id…]} → {rol, niyat, javob:[blok], amallar:[…], takliflar:[…]}
  GET  /api/bot/boshlash       — salom + (eslatma yoqilgan bo'lsa) bugungi takrorlash: formula va mavzular
  POST /api/bot/formula_natija — {id, togri}: formula mashqi natijasi (takrorlash navbati uchun)
"""
import math
import os
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from modules import pasport as PS

TZ = timezone.utc
MATN_ENG_UZUN = 400

# ───────────────────────── yozuvni tekislash ─────────────────────────
_KIRILL = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
           "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "s", "ч": "ch", "ш": "sh", "ъ": "", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o", "ғ": "g", "қ": "q", "ҳ": "h"}
_IMLO = {"ö": "o", "ğ": "g", "ş": "sh", "ç": "ch", "ü": "u", "ı": "i", "ä": "a", "ё": "yo"}


def normallash(matn):
    """Kichik harf, kirill → lotin, «ş ç ö ğ» → sh ch o g, apostroflar tashlanadi (o'quvchi → oquvchi), bo'shliqlar bitta."""
    s = str(matn or "").lower()
    s = "".join(_KIRILL.get(c, c) for c in s)
    s = "".join(_IMLO.get(c, c) for c in s)
    s = re.sub(r"[ʻʼ‘’`´'’]", "", s)
    s = re.sub(r"[^\w\s%√∫+\-*/=^<>().,:;?!#]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _bor(s, *kalitlar):
    return any(k in s for k in kalitlar)


def _soz(s, *sozlar):
    t = set(re.findall(r"[a-z0-9]+", s))
    return any(z in t for z in sozlar)


# ───────────────────────── mavzuni topish ─────────────────────────
# so'z (tekislangan) → mavzu nomida qidiriladigan kalit; ba'zi so'zlar nomda boshqacha yoziladi
SINONIM = {"foiz": "prosent", "protsent": "prosent", "tezlik": "harakat", "masofa": "harakat", "poyezd": "harakat", "ish": "ishga", "kasrlar": "kasr", "integral": "integral",
           "sin": "trigonometr", "cos": "trigonometr", "tg": "trigonometr", "ctg": "trigonometr", "sinus": "trigonometr", "kosinus": "trigonometr", "tangens": "trigonometr",
           "log": "logarifm", "lg": "logarifm", "ln": "logarifm", "sistema": "sistem", "ildiz": "ildiz", "modul": "modul", "daraja": "daraja", "uchburchak": "uchburchak",
           "yuza": "yuz", "hajm": "hajm", "burchak": "burchak", "kombinatorika": "kombinator", "ehtimol": "ehtimol", "ekub": "ekub", "ekuk": "ekuk", "qoldiq": "qoldiq"}
UMUMIY = {"tenglama", "tenglamani", "tengsizlik", "tengsizlikni", "masala", "misol", "funksiya", "formula", "formulalar", "mavzu", "haqida", "nima", "qanday", "toping", "yeching", "hisoblang",
          "boladi", "bolsa", "uchun", "yechib", "ber", "bering", "menga", "ning", "ni", "va", "bilan", "test", "savol", "mashq", "tuz", "boshla", "teng", "nechaga", "nechiga", "necha", "qancha",
          "qanchaga", "hisobla", "hisoblash", "topish", "yech", "yechim", "yechimini", "javob", "javobini", "ifoda", "ifodani", "qiymati", "qiymatini", "nechta", "ekan", "bor", "kerak", "tushuntir"}


def tuzilma_mavzusi(s, mavzular):
    """So'z bo'lmasa, ifoda TUZILMASIdan mavzu: x²+…=0 → kvadrat tenglama, 2x+3=11 → chiziqli tenglama, tengsizlik belgisi, √, %, kasr, sin/cos."""
    h = lambda *r: [x for x in r if x in mavzular]
    if re.search(r"[a-z]\s*(?:\^\s*2|2\b|²)", s) and "=" in s:
        return h(20)
    if re.search(r"[<>]", s) and re.search(r"\b[a-z]\b", s):
        return h(31) if re.search(r"[a-z]\s*\^\s*2|\)\s*\(", s) else h(29)
    if "=" in s and re.search(r"\d\s*[a-z]\b|\b[a-z]\s*[+\-=]|[+\-]\s*[a-z]\b", s):
        return h(19)
    if "√" in s:
        return h(15)
    if "%" in s:
        return h(43)
    if re.search(r"\b(?:sin|cos|tg|ctg)\b", s):
        return h(60)
    if re.search(r"\blog\d*", s):
        return h(56)
    if "∫" in s:
        return h(84)
    if re.search(r"\d\s*/\s*\d", s):
        return h(7)
    return []


def mavzu_topish(matn, mavzular, eng_kop=3):
    """matn → [mavzu raqamlari] (eng mosi birinchi). mavzular: {raqam: {nom, kitob}}. Aniq «N-mavzu» ustun; keyin so'zlar mavzu nomiga moslanadi."""
    s = normallash(matn)
    m = re.search(r"(?<![\d.])(\d{1,3})\s*-?\s*(?:chi|inchi)?\s*mavzu|mavzu\s*(?:raqami\s*)?(?:№|n)?\s*(\d{1,3})", s)
    if m:
        n = int(m.group(1) or m.group(2))
        return [n] if n in mavzular else []
    nomlar = {r: normallash(v["nom"]) for r, v in mavzular.items()}
    ball, tugri = {}, {}          # tugri — so'zning O'ZI mos kelgan (sinonim orqali emas): tenglikda ustunlik
    for t in re.findall(r"[a-z]{2,}", s):
        if t in UMUMIY:
            continue
        for kalit in {SINONIM.get(t, t), t}:          # sinonim ham, so'zning o'zi ham («sinus» → trigonometriya VA «sinuslar teoremasi»)
            if len(kalit) < 3:
                continue
            for r, nom in nomlar.items():
                soz = re.findall(r"[a-z]+", nom)
                if any(w == kalit or (len(kalit) >= 4 and (w.startswith(kalit) or kalit.startswith(w[:max(4, len(w) - 2)]) and len(w) >= 4))
                       or (len(w) >= 6 and len(kalit) >= 6 and len(os.path.commonprefix([w, kalit])) >= 6) for w in soz):      # teoremasi ≈ teoremalari
                    ball[r] = ball.get(r, 0) + (2 if len(kalit) >= 5 else 1)
                    if kalit == t:
                        tugri[r] = tugri.get(r, 0) + 1
    # raqam va amallardan: faqat sonlar bilan hisoblash → «Hisoblashga oid misollar»
    qolgan = [t for t in re.findall(r"[a-z]{2,}", s) if t not in UMUMIY]
    if not ball:
        t = tuzilma_mavzusi(s, mavzular)          # so'z yo'q — ifoda tuzilmasidan
        if t:
            return t
    if not ball and re.search(r"\d", s) and re.search(r"[+\-*/:()]", s) and not qolgan:
        return [r for r in (1, 16) if r in mavzular][:1]
    if not ball:
        return []
    top = sorted(ball.items(), key=lambda kv: (-kv[1], -tugri.get(kv[0], 0), kv[0]))
    eng = top[0][1]
    return [r for r, b in top if b >= max(1, eng - 1)][:eng_kop]


# ───────────────────────── masala (yechib bermaymiz) ─────────────────────────
def masala_mi(matn):
    """Matematik masala/misol berilganmi (yechish so'ralganmi)? Bot masalani YECHMAYDI, test taklif qiladi."""
    s = normallash(matn)
    if _bor(s, "natijam", "holatim", "darajam", "pasport", "reyting", "guruhim", "eslatma", "takror"):
        return False
    yech = _bor(s, "yech", "hisobla", "toping", "topin", "nechaga teng", "nechiga teng", "soddalashtir", "isbotla", "javobini", "yechimini", "yechib", "yechim", "qanday topiladi", "nechi bola")
    ifoda = bool(re.search(r"\d\s*[+\-*/:^×÷]\s*\(?\d|[a-z]\s*[=<>]\s*[\d(a-z-]|\d\s*[a-z]\s*[+\-=]|[=]\s*\d|√|∫|\b(?:sin|cos|tg|ctg|ln|lg)\s*[(\d]|\b(?:sin|cos|tg|ctg)\s*[a-z]\b|\blog\d*\s*[(\d]|\bx\s*\^?\d?\s*[+\-=]", s))
    nom_soz = _bor(s, "integral", "hosila", "limit", "tenglama", "tengsizlik", "kasr", "ildiz", "logarifm", "progressiya", "vektor", "uchburchak", "aylana", "ifodani")
    sozli = bool(re.search(r"\d", s)) and bool(re.search(r"nechta|necha|qancha|qanchaga|yig.?indi|ayirma|ko.?paytma|bo.?linma|tezlik|masofa|foiz|prosent", s))
    return (yech and (ifoda or sozli or nom_soz or bool(re.search(r"\d", s)))) or (ifoda and not _bor(s, "formula nima", "nima degani")) or sozli


# ───────────────────────── niyat (o'quvchi) ─────────────────────────
def eslatma_buyrugi(s):
    """«eslatma» so'zi bor: yoqish (True), o'chirish (False) yoki haqida so'ralgan (None)."""
    if "eslatma" not in s and "eslat" not in s:
        return None
    if _bor(s, "ochir", "ochiril", "yoqma", "toxtat", "kerakmas", "kerak emas", "bezor", "bas qil"):
        return False
    if _bor(s, "yoq", "yoqing", "yoqib", "boshla", "ulang", "kerak", "ha "):
        return True
    return None


def niyat_oquvchi(matn, mavzular):
    s = normallash(matn)
    if not s:
        return "bosh"
    if eslatma_buyrugi(s) is not None or (_bor(s, "eslatma") and _bor(s, "nima", "qanday")):
        return "eslatma"
    if _bor(s, "natijam", "natijalarim", "holatim", "qanday ketyap", "bilimim", "darajam", "qayerdaman", "qaysi darajada", "pasport", "statistika", "qanday oqiyap", "yutuqlarim", "nechta savol yech"):
        return "pasport"
    if _bor(s, "zaif", "nozik", "nimani organ", "qiyin mavzu", "qiynal", "xatolarim", "qayerda xato", "nimani takrorla", "nima yomon", "qaysi mavzu"):
        return "nozik"
    if _bor(s, "takror", "unutdim", "unutyap", "esimdan", "esdan", "eslab qol"):
        return "takror"
    if _bor(s, "guruhim", "reyting", "ustozim", "oqituvchim", "xalqaro", "pisa", "timss", "kirish test") and not _bor(s, "formula"):
        return "guruh"
    if _soz(s, "test", "mashq") or _bor(s, "savol ber", "savollar ber", "sinab kor", "sinov", "test tuz", "meni sina"):
        return "test"
    if _bor(s, "formula"):
        return "formula"
    if masala_mi(matn):
        return "masala"
    if mavzu_topish(matn, mavzular) and _bor(s, "haqida", "nima", "tushuntir", "qoida", "organ", "mavzu", "royxat", "qanday"):
        return "mavzu"
    if _bor(s, "rahmat", "tashakkur", "raxmat", "sagbol", "zor"):
        return "rahmat"
    if _bor(s, "xayr", "korishguncha", "hayr"):
        return "xayr"
    if _bor(s, "yordam", "nima qila ol", "nimalar qila", "qanday ishlat", "imkoniyat", "nima qilasan", "kimsan", "nima bu", "menyu"):
        return "yordam"
    if _bor(s, "salom", "assalom", "hayrli", "qalay", "nima gap", "hello", "privet") or _soz(s, "hi"):
        return "salom"
    if mavzu_topish(matn, mavzular):
        return "mavzu"
    return "nomalum"


# ───────────────────────── formula navbati (takrorlash) ─────────────────────────
def formula_navbat(idlar, tarix, hozir, eng_kop=3):
    """idlar: mavjud formulalar; tarix: {id: (urinish, togri, oxirgi_togri, yangilangan)}. → ketma-ketlik: xato qilinganlar, ko'rilmaganlar, keyin saqlanishi eng past bo'lganlar.
    Saqlanishi MUSTAHKAM (≥0,6) bo'lganlar navbatga kirmaydi."""
    nom = []
    for i in idlar:
        h = tarix.get(i)
        if not h or not h[0]:
            nom.append((1, 0.0, i)); continue
        if not h[2]:
            nom.append((0, 0.0, i)); continue
        r = PS.saqlanish(h[1], PS._kun(hozir, h[3]))
        if r < PS.MUSTAHKAM:
            nom.append((2, r, i))
    nom.sort()
    return [i for _, _, i in nom[:eng_kop]]


# ───────────────────────── javob bloklari ─────────────────────────
M = lambda s: {"t": "matn", "s": s}
R = lambda items: {"t": "royxat", "items": items}
TEST = lambda mavzu, yozuv: {"tur": "test", "mavzu": mavzu, "yozuv": yozuv}
TAKLIF_BOSH = ["Natijam qanday?", "Nimani o‘rganay?", "Test tuz", "Formula so‘ra", "Eslatmani yoq"]


class Ctx:
    """Bitta so'rov uchun ma'lumotlar: pasport (kerak bo'lganda yuklanadi), mavzular, xotira, vaqt."""

    def __init__(self, mavzular, pasport_fn=None, xotira=None, formulalar=None, hozir=None):
        self.mavzular = mavzular
        self._pf, self._p = pasport_fn, None
        self.xotira = xotira or {}
        self.formulalar = formulalar or []
        self.hozir = hozir or datetime.now(TZ)

    @property
    def pasport(self):
        if self._p is None and self._pf:
            self._p = self._pf()
        return self._p


def _mavzu_nomi(ctx, r):
    return f"{r}. {ctx.mavzular[r]['nom']}" if r in ctx.mavzular else str(r)


def oquvchi_javobi(matn, ctx):
    """→ {niyat, javob, amallar, takliflar, xotira?} (xotira — saqlanadigan o'zgarishlar)."""
    niyat = niyat_oquvchi(matn, ctx.mavzular)
    s = normallash(matn)
    out = {"niyat": niyat, "javob": [], "amallar": [], "takliflar": list(TAKLIF_BOSH)}
    j, a = out["javob"], out["amallar"]
    p = ctx.pasport
    mat = p["matematika"] if p else None
    if niyat == "bosh":
        j.append(M("Savolingizni yozing yoki pastdagi tugmalardan birini tanlang."))
    elif niyat == "salom":
        j.append(M("Salom! Men Kabu-botman. Natijangiz, zaif mavzularingiz haqida aytib beraman, test tuzaman va formulalarni takrorlatib turaman."))
    elif niyat == "yordam":
        j.append(M("Men quyidagilarni qila olaman:"))
        j.append(R(["«Natijam qanday?»: matematika va xalqaro natijalaringiz", "«Nimani o‘rganay?»: nozik mavzular va takrorlash vaqti kelganlar", "«Test tuz»: mavzu bo‘yicha test (masalan «7-mavzuda test»)", "«Formula so‘ra»: formulani yozib tekshirasiz", "«Eslatmani yoq»: har kuni takrorlash eslatmasi", "«Kasr haqida»: mavzu va natijangiz"]))
        j.append(M("Masalani yechib bermayman: o‘zingiz yechganingizda bilim mustahkam bo‘ladi. Shu mavzu bo‘yicha test tuzib beraman."))
    elif niyat == "rahmat":
        j.append(M("Marhamat! Yana yordam kerak bo‘lsa, yozing."))
    elif niyat == "xayr":
        j.append(M("Xayr! Omad tilayman. Ertaga ham bir oz mashq qilishni unutmang."))
    elif niyat == "masala":
        top = mavzu_topish(matn, ctx.mavzular)
        j.append(M("Bu masalani men yechib bermayman: o‘zingiz yechsangiz bilim mustahkam bo‘ladi, yechib berilgan javob esa tezda unutiladi."))
        if top:
            j.append(M("Bu masala quyidagi mavzuga o‘xshaydi:"))
            j.append(R([_mavzu_nomi(ctx, r) for r in top]))
            a.append(TEST(top, f"{_mavzu_nomi(ctx, top[0])}: test"))
            a.append({"tur": "mavzu", "mavzu": top[0], "yozuv": "Qoidani o‘qish"})
            j.append(M("Shu mavzu bo‘yicha test tuzib beraymi? To‘g‘ri javoblar test oxirida ko‘rsatiladi, yechimi bor savollarda esa yechim ham."))
        else:
            j.append(M("Mavzusini aniq topa olmadim. Aralash test tuzib beraymi, yoki mavzu nomini yozing (masalan «kvadrat tenglama»)?"))
            a.append(TEST([], "Aralash test"))
        out["xotira"] = {"oxirgi_mavzu": top[0] if top else None}
    elif niyat == "test":
        top = mavzu_topish(matn, ctx.mavzular)
        if not top and ctx.xotira.get("oxirgi_mavzu") and _bor(s, "shu", "yana", "oshan", "uni"):
            top = [int(ctx.xotira["oxirgi_mavzu"])]
        if top:
            j.append(M(f"Mayli, {_mavzu_nomi(ctx, top[0])} mavzusi bo‘yicha test tuzaman. Avval ko‘rmagan savollaringiz, keyin xato qilganlaringiz beriladi."))
            a.append(TEST(top[:1], f"{_mavzu_nomi(ctx, top[0])}: test"))
        elif mat and mat["nozik"]:
            r = mat["nozik"][0]
            j.append(M(f"Sizga eng kerakli mavzu: {r['raqam']}. {r['nom']} ({r['hozirgi']}% to‘g‘ri). Shu mavzuda test tuzaymi?"))
            a.append(TEST([r["raqam"]], f"{r['raqam']}. {r['nom']}: test")); a.append(TEST([], "Aralash test"))
        else:
            j.append(M("Aralash test tuzaman: hamma mavzudan, avval ko‘rmaganlaringiz. Mavzuni aytsangiz (masalan «7-mavzuda test»), shu mavzudan tuzaman."))
            a.append(TEST([], "Aralash test"))
        out["xotira"] = {"oxirgi_mavzu": top[0] if top else ctx.xotira.get("oxirgi_mavzu")}
    elif niyat == "mavzu":
        top = mavzu_topish(matn, ctx.mavzular)
        r = top[0]; m = ctx.mavzular[r]
        j.append(M(f"{_mavzu_nomi(ctx, r)}" + (f" (kitob bo‘limi {m['kitob']})" if m.get("kitob") else "") + f". Bankda {m.get('jami', 0)} ta test bor."))
        x = next((t for t in (mat or {}).get("mavzular", []) if t["raqam"] == r), None)
        j.append(M(f"Siz bu mavzuda {x['ko_rilgan']} ta savol ko‘rgansiz, hozirgi holatda {x['hozirgi']}% to‘g‘ri." if x else "Siz bu mavzuda hali savol yechmagansiz."))
        if len(top) > 1:
            j.append(M("Yaqin mavzular: " + "; ".join(_mavzu_nomi(ctx, t) for t in top[1:]) + "."))
        a.append({"tur": "mavzu", "mavzu": r, "yozuv": "Qoida va misollar"}); a.append(TEST([r], "Shu mavzuda test"))
        out["xotira"] = {"oxirgi_mavzu": r}
    elif niyat == "formula":
        navbat = formula_navbat(ctx.formulalar, ctx.xotira.get("_formula_tarix", {}), ctx.hozir, 1) if ctx.formulalar else []
        j.append(M("Mayli, formula so‘rayman. Belgilar klaviaturasida yozing, men ma’nosini tekshiraman (yozilish tartibi muhim emas: S = a·a va S = a² bir xil)."))
        a.append({"tur": "formula", "id": navbat[0] if navbat else None, "yozuv": "Formula mashqi"})
    elif niyat == "eslatma":
        yoq = eslatma_buyrugi(s)
        if yoq is True:
            j.append(M("Eslatma yoqildi. Botni ochganingizda takrorlash vaqti kelgan formula va mavzularni aytib turaman. Xohlasangiz «eslatmani o‘chir» deb yozing."))
            out["xotira"] = {"eslatma": True}
        elif yoq is False:
            j.append(M("Eslatma o‘chirildi. Kerak bo‘lsa, «eslatmani yoq» deb yozing.")); out["xotira"] = {"eslatma": False}
        else:
            holat = "yoqilgan" if ctx.xotira.get("eslatma") else "o‘chiq"
            j.append(M(f"Eslatma hozir {holat}. Yoqsangiz, botni ochganingizda takrorlash vaqti kelgan formulalar va mavzularni so‘rab turaman."))
    elif niyat == "pasport":
        if not mat or not (mat["ko_rilgan"] or p["xalqaro"]["sinflar"] or p["xalqaro"]["imtihonlar"]):
            j.append(M("Hozircha sizda natija yo‘q: matematika bankida savol yechilmagan. Bir nechta savol yechsangiz, natijangizni ko‘rsataman."))
            a.append(TEST([], "Aralash test"))
        else:
            j.append(M("Natijangiz:")); j.append(R(p["xulosa"]))
            a.append({"tur": "pasport", "yozuv": "To‘liq pasportni ochish"})
    elif niyat == "nozik":
        if not mat or not mat["ko_rilgan"]:
            j.append(M("Hali zaif joyingizni aniqlash uchun savol yetarli emas. Avval aralash test yeching.")); a.append(TEST([], "Aralash test"))
        else:
            if mat["nozik"]:
                j.append(M("Nozik mavzularingiz (kamida 6 savol yechilgan, to‘g‘ri javob 50% dan past):"))
                j.append(R([f"{t['raqam']}. {t['nom']}: {t['hozirgi']}% ({t['ko_rilgan']} savol)" for t in mat["nozik"]]))
                for t in mat["nozik"][:2]:
                    a.append(TEST([t["raqam"]], f"{t['raqam']}. {t['nom']}: test"))
            else:
                j.append(M("Aniq nozik mavzu topilmadi: hech bir mavzuda 6 ta va undan ko‘p savol bo‘yicha natijangiz 50% dan past emas."))
            if mat["takrorlash"]:
                j.append(M("Takrorlash vaqti kelgan mavzular (taxminiy hisob):")); j.append(R([f"{t['raqam']}. {t['nom']}: {t['holatlar']['takror'] + t['holatlar']['unutilgan']} ta savol" for t in mat["takrorlash"]]))
                if not a:
                    a.append(TEST([mat["takrorlash"][0]["raqam"]], f"{mat['takrorlash'][0]['raqam']}. {mat['takrorlash'][0]['nom']}: test"))
            elif not mat["nozik"]:
                j.append(M("Takrorlash vaqti kelgan savol ham yo‘q. Davom eting!"))
    elif niyat == "takror":
        h = mat["holatlar"] if mat else None
        if not mat or not mat["ko_rilgan"]:
            j.append(M("Hali yechilgan savol yo‘q, takrorlanadigan narsa ham yo‘q. Avval test yeching."))
            a.append(TEST([], "Aralash test"))
        else:
            n = h["takror"] + h["unutilgan"]
            j.append(M(f"Taxminiy hisobda {h['takror']} ta savolni takrorlash vaqti keldi, {h['unutilgan']} tasi unutilgan bo‘lishi mumkin; oxirgi urinishda xato qilingan: {h['xato']} ta. (Bu o‘lchov emas, taxmin.)"))
            if mat["takrorlash"]:
                t = mat["takrorlash"][0]
                j.append(M(f"Birinchi navbatda: {t['raqam']}. {t['nom']}.")); a.append(TEST([t["raqam"]], f"{t['raqam']}. {t['nom']}: test"))
            elif not n:
                j.append(M("Hozir takrorlash shart emas, hammasi mustahkam."))
    elif niyat == "guruh":
        xs = p["xalqaro"]["sinflar"] if p else []
        if not xs:
            j.append(M("Siz xalqaro (PISA/TIMSS) sinfiga qo‘shilmagansiz. O‘qituvchingizdan taklif kodi so‘rang."))
        else:
            for sn in xs:
                j.append(M(f"«{sn['nom']}» sinfi, o‘qituvchi: {sn['oqituvchi'] or '—'}. " + (f"Guruhingiz: {sn['guruh']} ({sn['guruhlar_soni']} ta guruhdan), reyting {sn['reyting']}." if sn["guruh"] else "Siz hali guruhga tushmagansiz: kirish testini topshirishingiz kerak.")))
    else:   # nomalum
        j.append(M("Bu savolni tushunmadim. Men faqat natijangiz, zaif mavzularingiz, testlar va formulalar haqida gaplasha olaman. Quyidagilardan birini tanlang yoki «yordam» deb yozing."))
    if niyat in ("pasport", "nozik", "takror") and p:
        out["takliflar"] = ["Test tuz", "Formula so‘ra", "Guruhim qanday?", "Eslatmani yoq"]
    return out


# ───────────────────────── o'qituvchi miyasi ─────────────────────────
NOFAOL_KUN = 7
ZAIF_CHEGARA = 65       # shu foizdan past — «zaif»; hamma undan yuqori bo'lsa, bot «zaif yo'q» deydi
ZAIF_ENG_KAM = 10      # o'qituvchi uchun «zaif» deyish uchun kamida shuncha savol yechilgan bo'lishi kerak (pasportdagi 15 dan yumshoqroq: erta signal)
UZUN_RO_YXAT = 15

NIYAT_USTOZ = [
    ("kirish", ("kirish test",)),
    ("tekshiruv", ("shubhali", "tekshiruvda", "gpt", "kochir", "aldov", "chatgpt")),
    ("nofaol", ("faol emas", "nofaol", "kirmagan", "kirmayap", "qatnashmay", "ishlamay", "sust", "passiv", "yoq bolgan", "faolsiz")),
    ("zaif", ("zaif", "qiynalayot", "past natija", "orqada", "eng yomon", "yordam kerak bolgan", "kim qiynal")),
    ("mavzu_xato", ("qaysi mavzu", "ko p xato", "kop xato", "umumiy xato", "qaysi mavzuda xato")),
    ("sinf", ("sinf holati", "sinfim", "guruhlar", "umumiy", "holat", "nechta oquvchi", "statistika", "hisobot", "xulosa")),
]


def oquvchi_ref(matn):
    """«22-o'quvchi», «22 chi oquvchi», «#1234» → ("raqam", 22) | ("id", 1234) | None."""
    s = normallash(matn)
    m = re.search(r"#\s*(\d{3,})", s)
    if m:
        return ("id", int(m.group(1)))
    m = re.search(r"(?<![\d.])(\d{1,3})\s*-?\s*(?:chi|inchi|nchi)?\s*(?:oquvchi|talaba|bola)", s) or re.search(r"(?:oquvchi|talaba)\s*(?:raqami\s*)?(?:№|n)?\s*(\d{1,3})\b", s)
    return ("raqam", int(m.group(1))) if m else None


def niyat_ustoz(matn):
    s = normallash(matn)
    if not s:
        return "bosh"
    if oquvchi_ref(matn):
        return "oquvchi"
    for nom, kalitlar in NIYAT_USTOZ:
        if _bor(s, *kalitlar):
            return nom
    if _bor(s, "rahmat", "tashakkur", "raxmat"):
        return "rahmat"
    if _bor(s, "yordam", "nima qila ol", "nimalar qila", "qanday ishlat", "kimsan", "menyu"):
        return "yordam"
    if _bor(s, "salom", "assalom", "hayrli") or _soz(s, "hi"):
        return "salom"
    return "nomalum"


def _ism_sozlari(ism):
    return re.findall(r"[a-z]+", normallash(ism))


def oquvchi_topish(matn, qatorlar, sinf_nomi=""):
    """matn ichidan o'quvchini topadi. qatorlar — ism bo'yicha tartiblangan sinf jurnali. → ([qator…], raqam | None).
    «N-o'quvchi» — jurnaldagi N-o'rin (ism bo'yicha); aks holda ism so'zlari (kamida 3 harf)."""
    ref = oquvchi_ref(matn)
    if ref and ref[0] == "id":
        return [q for q in qatorlar if q["user_id"] == ref[1]], None
    if ref and ref[0] == "raqam":
        n = ref[1]
        return ([qatorlar[n - 1]] if 1 <= n <= len(qatorlar) else []), n
    s = normallash(matn)
    sinf_sozlari = set(re.findall(r"[a-z0-9]+", normallash(sinf_nomi)))
    tok = [t for t in re.findall(r"[a-z]{3,}", s) if t not in UMUMIY and t not in sinf_sozlari and t not in {"oquvchi", "haqida", "qayerda", "qanday", "natijasi", "holati", "kim", "bola"}]
    topilgan = []
    for q in qatorlar:
        sozlar = _ism_sozlari(q["ism"])
        if tok and any(any(w.startswith(t) for w in sozlar) for t in tok):
            topilgan.append(q)
    return topilgan, None


def _sana(t):
    return t.astimezone(TZ).strftime("%d.%m.%Y") if t else None


def _kun_oldin(t, hozir):
    return int((hozir - t).total_seconds() // 86400) if t else None


class TCtx:
    """O'qituvchi so'rovi uchun ma'lumot manbalari (bazasiz sinash mumkin: funksiyalar beriladi)."""

    def __init__(self, mavzular, sinflar, yukla, pasport, mavzu_stat, tanlangan=None, hozir=None):
        self.mavzular, self.sinflar, self._yukla, self._pasport, self._mavzu_stat = mavzular, sinflar, yukla, pasport, mavzu_stat
        self.tanlangan, self.hozir = tanlangan, hozir or datetime.now(TZ)
        self._kesh = {}

    def azolar(self, kalit):
        if kalit not in self._kesh:
            self._kesh[kalit] = sorted(self._yukla(kalit), key=lambda q: normallash(q["ism"]))
        return self._kesh[kalit]


def sinf_tanlash(matn, ctx):
    """→ (sinf | None, savol_matni | None). Bitta sinf bo'lsa — o'sha; nomi aytilsa — o'sha; aks holda so'raladi."""
    if not ctx.sinflar:
        return None, None
    if ctx.tanlangan:
        for s in ctx.sinflar:
            if s["kalit"] == ctx.tanlangan:
                return s, None
    if len(ctx.sinflar) == 1:
        return ctx.sinflar[0], None
    t = set(re.findall(r"[a-z0-9]{2,}", normallash(matn)))
    mos = [s for s in ctx.sinflar if any(w in t for w in re.findall(r"[a-z0-9]{3,}", normallash(s["nom"])))]
    if len(mos) == 1:
        return mos[0], None
    return None, "Qaysi sinf haqida so‘rayapsiz?"


def _qator_matni(q, n, hozir):
    kun = _kun_oldin(q["oxirgi"], hozir)
    faol = "hali hech narsa yechmagan" if q["oxirgi"] is None else ("bugun faol" if kun == 0 else f"{kun} kun oldin faol")
    mat = f"{q['mat_tg']}/{q['mat_ko']} to‘g‘ri" if q["mat_ko"] else "matematika bankida savol yo‘q"
    return f"{n}. {q['ism']}: {faol}; {mat}" + (f"; guruh {q['guruh']}, reyting {q['reyting']}" if q.get("guruh") else "")


def ustoz_javobi(matn, ctx):
    niyat = niyat_ustoz(matn)
    s = normallash(matn)
    out = {"niyat": niyat, "javob": [], "amallar": [], "takliflar": ["Kim eng zaif?", "Kim faol emas?", "Sinf holati", "Qaysi mavzuda ko‘p xato?", "Kirish testini kim topshirmagan?"]}
    j, a = out["javob"], out["amallar"]
    if niyat == "bosh":
        j.append(M("Savolingizni yozing, masalan «22-o‘quvchi qayerda?» yoki «kim eng zaif?».")); return out
    if niyat == "salom":
        j.append(M("Salom! Men Kabu-botman. Sinfingiz haqida so‘rang: o‘quvchining holati, kim zaif, kim faol emas, qaysi mavzuda xato ko‘p.")); return out
    if niyat == "rahmat":
        j.append(M("Marhamat!")); return out
    if niyat == "yordam":
        j.append(M("Men quyidagilarni bilaman:"))
        j.append(R(["«22-o‘quvchi qayerda?» yoki ism bilan: o‘quvchining pasporti (jurnaldagi tartib raqami, ism bo‘yicha)", "«Kim eng zaif?»: matematika bankidagi natija bo‘yicha", "«Kim faol emas?» yoki «5 kundan beri kirmaganlar»", "«Kirish testini kim topshirmagan?»", "«Qaysi mavzuda xato ko‘p?»", "«Sinf holati»: umumiy raqamlar"]))
        j.append(M("Natijalar tizimdagi haqiqiy ma’lumotdan olinadi; yetarli ma’lumot bo‘lmasa, shuni ochiq aytaman.")); return out
    if not ctx.sinflar:
        j.append(M("Sizda faol sinf yoki guruh topilmadi. Avval Xalqaro baholash bo‘limida sinf oching yoki o‘quvchilarni qo‘shing.")); return out
    sinf, savol = sinf_tanlash(matn, ctx)
    if sinf is None and niyat == "nomalum":
        j.append(M("Bu savolni tushunmadim. Quyidagi savollardan birini tanlang yoki «yordam» deb yozing. Bir nechta sinfingiz bo‘lsa, savolga sinf nomini ham yozing.")); return out
    if sinf is None:
        j.append(M(savol)); out["takliflar"] = [f"{x['nom']}: {matn.strip()}"[:120] for x in ctx.sinflar[:6]]
        out["tanlov"] = [{"kalit": x["kalit"], "nom": x["nom"]} for x in ctx.sinflar[:6]]; return out
    qator = ctx.azolar(sinf["kalit"]); hozir = ctx.hozir
    out["sinf"] = {"kalit": sinf["kalit"], "nom": sinf["nom"]}
    if niyat == "nomalum" and qator and oquvchi_topish(matn, qator, sinf["nom"])[0]:
        niyat = out["niyat"] = "oquvchi"            # faqat ism yozilgan («sardor qanday») — jurnaldagi o'quvchi
    if niyat == "nomalum":
        j.append(M("Bu savolni tushunmadim. Quyidagi savollardan birini tanlang yoki «yordam» deb yozing.")); return out
    if not qator:
        j.append(M(f"«{sinf['nom']}» sinfida hali o‘quvchi yo‘q.")); return out
    if niyat == "oquvchi":
        topilgan, n = oquvchi_topish(matn, qator, sinf["nom"])
        if not topilgan:
            j.append(M(f"«{sinf['nom']}» jurnalida {n}-o‘quvchi yo‘q (jami {len(qator)} ta o‘quvchi)." if n else "Bunday o‘quvchini topa olmadim. Ismini yoki jurnaldagi tartib raqamini yozing."))
            return out
        if len(topilgan) > 1:
            j.append(M("Bir nechta mos o‘quvchi topildi, qaysi biri?")); j.append(R([f"{qator.index(q) + 1}. {q['ism']}" for q in topilgan[:8]]))
            out["takliflar"] = [f"{qator.index(q) + 1}-o‘quvchi qayerda?" for q in topilgan[:6]]; return out
        q = topilgan[0]; raqam = qator.index(q) + 1
        p = ctx._pasport(q["user_id"])
        j.append(M(f"{raqam}. {q['ism']} («{sinf['nom']}» jurnali, ism bo‘yicha tartib):")); j.append(R(p["xulosa"]))
        a.append({"tur": "pasport", "user_id": q["user_id"], "yozuv": f"{q['ism']}: to‘liq pasport"})
        out["takliflar"] = [f"{raqam + 1}-o‘quvchi qayerda?"] + out["takliflar"][:3] if raqam < len(qator) else out["takliflar"]
    elif niyat == "zaif":
        yetarli = [q for q in qator if q["mat_ko"] >= ZAIF_ENG_KAM]
        kam = len(qator) - len(yetarli)
        if not yetarli:
            j.append(M(f"Hozircha hukm chiqarish uchun ma’lumot yetarli emas: {len(qator)} o‘quvchining hech birida matematika bankida {ZAIF_ENG_KAM} tadan ko‘p savol yechilmagan."))
        else:
            tartib = sorted(yetarli, key=lambda q: (q["mat_tg"] / q["mat_ko"], -q["mat_ko"]))
            pastlar = [q for q in tartib if 100 * q["mat_tg"] / q["mat_ko"] < ZAIF_CHEGARA][:5]
            if pastlar:
                j.append(M(f"Matematika bankida natijasi {ZAIF_CHEGARA}% dan past o‘quvchilar (kamida {ZAIF_ENG_KAM} savol yechganlar orasidan, eng pasti birinchi):"))
            else:
                pastlar = tartib[:3]
                j.append(M(f"Zaif o‘quvchi aniqlanmadi: kamida {ZAIF_ENG_KAM} savol yechgan hech kimning natijasi {ZAIF_CHEGARA}% dan past emas. Eng past natijalar:"))
            j.append(R([f"{qator.index(q) + 1}. {q['ism']}: {round(100 * q['mat_tg'] / q['mat_ko'])}% ({q['mat_ko']} savol)" for q in pastlar]))
            a.extend({"tur": "pasport", "user_id": q["user_id"], "yozuv": f"{q['ism']}: pasport"} for q in pastlar[:3])
        if kam:
            j.append(M(f"{kam} o‘quvchi bo‘yicha ma’lumot kam (hukm chiqarilmadi)."))
        reyt = sorted([q for q in qator if q.get("reyting")], key=lambda q: q["reyting"])[:5]
        if reyt and len(qator) > 1:
            j.append(M("Xalqaro reytingi eng past o‘quvchilar:")); j.append(R([f"{qator.index(q) + 1}. {q['ism']}: reyting {q['reyting']}, {q['guruh']}-guruh" for q in reyt]))
    elif niyat == "nofaol":
        m = re.search(r"(\d{1,3})\s*kun", s); kun = int(m.group(1)) if m else NOFAOL_KUN
        nofaol = [q for q in qator if q["oxirgi"] is None or _kun_oldin(q["oxirgi"], hozir) >= kun]
        hech = [q for q in nofaol if q["oxirgi"] is None]
        if not nofaol:
            j.append(M(f"Hamma o‘quvchi oxirgi {kun} kun ichida faol bo‘lgan."))
        else:
            j.append(M(f"Oxirgi {kun} kunda faol bo‘lmagan o‘quvchilar: {len(nofaol)} ta (shundan {len(hech)} tasi hali hech narsa yechmagan)."))
            nofaol.sort(key=lambda q: (q["oxirgi"] is not None, q["oxirgi"] or hozir))
            j.append(R([f"{qator.index(q) + 1}. {q['ism']}: " + ("hali hech narsa yechmagan" if q["oxirgi"] is None else f"oxirgi faolligi {_sana(q['oxirgi'])} ({_kun_oldin(q['oxirgi'], hozir)} kun oldin)") for q in nofaol[:UZUN_RO_YXAT]]))
            if len(nofaol) > UZUN_RO_YXAT:
                j.append(M(f"Ro‘yxat qisqartirildi: yana {len(nofaol) - UZUN_RO_YXAT} ta."))
    elif niyat == "kirish":
        if sinf["tur"] != "xb":
            j.append(M("Kirish testi faqat xalqaro (PISA/TIMSS) sinflarida bor."))
        else:
            yoq = [q for q in qator if not q.get("kirish_bor")]
            j.append(M(f"Kirish testini topshirmaganlar: {len(yoq)} ta (jami {len(qator)} tadan)." if yoq else "Hamma o‘quvchi kirish testini topshirgan."))
            if yoq:
                j.append(R([f"{qator.index(q) + 1}. {q['ism']}" for q in yoq[:UZUN_RO_YXAT]]))
            a.append({"tur": "guruhlar", "sinf": sinf["id"], "yozuv": "Guruhlar bo‘limi"})
    elif niyat == "tekshiruv":
        j.append(M("Shubhali natijalar (juda tez yechilgan, ilovadan chiqilgan, keskin sakragan) sabablari bilan «Guruhlar» bo‘limida ko‘rinadi. U yerda har bir o‘quvchining belgisi ham bor."))
        if sinf["tur"] == "xb":
            a.append({"tur": "guruhlar", "sinf": sinf["id"], "yozuv": "Guruhlarni ochish"})
    elif niyat == "mavzu_xato":
        st = [x for x in ctx._mavzu_stat([q["user_id"] for q in qator]) if x["ko"] >= 20]
        if not st:
            j.append(M("Mavzular bo‘yicha xulosa uchun savol yetarli emas (har mavzuda kamida 20 ta javob kerak)."))
        else:
            ps = sorted(st, key=lambda x: x["tg"] / x["ko"])[:5]
            j.append(M("Sinf bo‘yicha eng ko‘p xato qilingan mavzular (kamida 20 ta javob):"))
            j.append(R([f"{x['mavzu']}. {ctx.mavzular.get(x['mavzu'], {}).get('nom', '')}: {round(100 * x['tg'] / x['ko'])}% to‘g‘ri ({x['ko']} javob)" for x in ps]))
    elif niyat == "sinf":
        faol = [q for q in qator if q["oxirgi"] is not None and _kun_oldin(q["oxirgi"], hozir) < 7]
        yechgan = [q for q in qator if q["mat_ko"]]
        j.append(M(f"«{sinf['nom']}»: {len(qator)} ta o‘quvchi."))
        sat = [f"Oxirgi 7 kunda faol: {len(faol)} ta", f"Matematika bankida savol yechgan: {len(yechgan)} ta"]
        etarli = [q for q in qator if q["mat_ko"] >= ZAIF_ENG_KAM]
        if etarli:
            sat.append(f"O‘rtacha to‘g‘ri javob ulushi ({len(etarli)} o‘quvchi bo‘yicha): {round(sum(100 * q['mat_tg'] / q['mat_ko'] for q in etarli) / len(etarli))}%")
        if sinf["tur"] == "xb":
            gr = {q["guruh"] for q in qator if q.get("guruh")}
            sat.append(f"Guruhlarda: {sum(1 for q in qator if q.get('guruh'))} ta ({len(gr)} ta guruh); kirish testini topshirmagan: {sum(1 for q in qator if not q.get('kirish_bor'))} ta")
        j.append(R(sat))
    return out


# ───────────────────────── baza va endpointlar ─────────────────────────
class Yoz(BaseModel):
    token: Optional[str] = None
    matn: str = Field("", max_length=MATN_ENG_UZUN)
    sinf: Optional[str] = Field(None, max_length=20)
    rol: Optional[str] = Field(None, max_length=12)
    formulalar: list = Field(default_factory=list, max_length=80)


class FormulaNatija(BaseModel):
    token: Optional[str] = None
    id: str = Field(..., min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_\-]+$")
    togri: bool


def create_router(platform):
    router = APIRouter(tags=["kabu_bot"])
    holat = {"tayyor": False}

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def jadval(cur):
        if holat["tayyor"]:
            return
        cur.execute("""CREATE TABLE IF NOT EXISTS kabu_bot_xotira (user_id BIGINT NOT NULL, kalit TEXT NOT NULL, qiymat JSONB NOT NULL DEFAULT 'null'::jsonb,
                       yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, kalit))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS kabu_bot_formula (user_id BIGINT NOT NULL, formula_id TEXT NOT NULL, urinish INT NOT NULL DEFAULT 0, togri INT NOT NULL DEFAULT 0,
                       oxirgi_togri BOOLEAN NOT NULL DEFAULT FALSE, yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, formula_id))""")
        holat["tayyor"] = True

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            jadval(cur); r = fn(cur); conn.commit(); return r
        finally:
            cur.close(); conn.close()

    # ── o'qituvchi ma'lumotlari ──
    def admin_mi(cur, u):
        return bool(PS._q(cur, "kb_adm", "SELECT 1 FROM admin_akkaunt WHERE uid=%s", (u,)))

    def sinflarim(cur, u):
        out = []
        for r in PS._q(cur, "kb_xs", "SELECT s.id, s.nom, (SELECT COUNT(*) FROM xb_sinf_azo a WHERE a.sinf_id=s.id) AS soni FROM xb_sinf s WHERE s.egasi=%s AND s.faol ORDER BY s.id", (u,)):
            out.append({"kalit": f"xb:{r['id']}", "id": int(r["id"]), "nom": r["nom"], "tur": "xb", "soni": int(r["soni"])})
        for r in PS._q(cur, "kb_ks", "SELECT g.id, g.nom, (SELECT COUNT(*) FROM kurs_guruh_azo a WHERE a.guruh_id=g.id) AS soni FROM kurs_guruh g WHERE g.egasi=%s AND g.faol ORDER BY g.id", (u,)):
            out.append({"kalit": f"kurs:{r['id']}", "id": int(r["id"]), "nom": r["nom"], "tur": "kurs", "soni": int(r["soni"])})
        return out

    def azolar_yukla(cur, u, kalit, sinflar):
        s = next((x for x in sinflar if x["kalit"] == kalit), None)
        if not s:
            raise HTTPException(403, "Bu sinf sizniki emas")
        if s["tur"] == "xb":
            ids = [int(r["user_id"]) for r in PS._q(cur, "kb_a1", "SELECT user_id FROM xb_sinf_azo WHERE sinf_id=%s", (s["id"],))]
            guruh = {int(r["user_id"]): r for r in PS._q(cur, "kb_g", "SELECT user_id, guruh, reyting FROM xb_guruh_azo WHERE sinf_id=%s", (s["id"],))}
        else:
            ids = [int(r["user_id"]) for r in PS._q(cur, "kb_a2", "SELECT user_id FROM kurs_guruh_azo WHERE guruh_id=%s", (s["id"],))]
            guruh = {}
        if not ids:
            return []
        nom = {int(r["user_id"]): r["full_name"] for r in PS._q(cur, "kb_n", "SELECT user_id, full_name FROM users WHERE user_id = ANY(%s)", (ids,))}
        mat = {int(r["user_id"]): r for r in PS._q(cur, "kb_m", "SELECT user_id, COUNT(*) AS ko, COALESCE(SUM(oxirgi_togri::int),0) AS tg, MAX(yangilangan) AS oxirgi FROM mat_bank_javob WHERE user_id = ANY(%s) GROUP BY user_id", (ids,))}
        xbv = {int(r["user_id"]): r["oxirgi"] for r in PS._q(cur, "kb_v", "SELECT user_id, MAX(yangilangan) AS oxirgi FROM xb_bilim WHERE user_id = ANY(%s) GROUP BY user_id", (ids,))}
        xbi = {int(r["user_id"]): r for r in PS._q(cur, "kb_i", """SELECT user_id, MAX(topshirilgan) AS oxirgi, BOOL_OR(tur='kirish' AND rasmiy) AS kirish FROM xb_imtihon
                                                                WHERE user_id = ANY(%s) AND topshirilgan IS NOT NULL GROUP BY user_id""", (ids,))}
        out = []
        for i in ids:
            vaqt = [t for t in (mat.get(i, {}).get("oxirgi"), xbv.get(i), xbi.get(i, {}).get("oxirgi")) if t]
            g = guruh.get(i, {})
            out.append({"user_id": i, "ism": nom.get(i) or f"#{i}", "oxirgi": max(vaqt) if vaqt else None, "mat_ko": int(mat.get(i, {}).get("ko") or 0), "mat_tg": int(mat.get(i, {}).get("tg") or 0),
                        "guruh": g.get("guruh"), "reyting": g.get("reyting"), "kirish_bor": bool(xbi.get(i, {}).get("kirish")) or bool(g)})
        return out

    def mavzu_stat(cur, ids):
        if not ids:
            return []
        return [{"mavzu": int(r["mavzu"]), "ko": int(r["ko"]), "tg": int(r["tg"])} for r in PS._q(cur, "kb_ms", """SELECT mavzu, COUNT(*) AS ko, COALESCE(SUM(oxirgi_togri::int),0) AS tg
                                                                                                  FROM mat_bank_javob WHERE user_id = ANY(%s) GROUP BY mavzu""", (ids,))]

    def xotira_ol(cur, u):
        return {r["kalit"]: r["qiymat"] for r in PS._q(cur, "kb_x", "SELECT kalit, qiymat FROM kabu_bot_xotira WHERE user_id=%s", (u,))}

    def xotira_yoz(cur, u, d):
        for k, v in (d or {}).items():
            import json as _j
            cur.execute("""INSERT INTO kabu_bot_xotira(user_id, kalit, qiymat) VALUES(%s,%s,%s::jsonb) ON CONFLICT (user_id, kalit) DO UPDATE SET qiymat=EXCLUDED.qiymat, yangilangan=NOW()""", (u, k, _j.dumps(v)))

    def formula_tarix(cur, u, idlar):
        idlar = [str(i)[:40] for i in idlar if re.fullmatch(r"[A-Za-z0-9_\-]{1,40}", str(i))]
        if not idlar:
            return {}
        return {r["formula_id"]: (int(r["urinish"]), int(r["togri"]), bool(r["oxirgi_togri"]), r["yangilangan"])
                for r in PS._q(cur, "kb_f", "SELECT formula_id, urinish, togri, oxirgi_togri, yangilangan FROM kabu_bot_formula WHERE user_id=%s AND formula_id = ANY(%s)", (u, idlar))}

    def rol_aniqla(cur, u, so_ralgan):
        sl = sinflarim(cur, u)
        ustoz_mi = bool(sl) or admin_mi(cur, u)
        if so_ralgan == "oquvchi":
            return "oquvchi", sl
        if so_ralgan == "oqituvchi":
            if not ustoz_mi:
                raise HTTPException(403, "Siz o‘qituvchi emassiz")
            return "oqituvchi", sl
        return ("oqituvchi" if sl else "oquvchi"), sl

    def mavzular_lugat():
        from modules.mat_bank import bank_ol
        b = bank_ol()
        return b, {r: {"nom": m["nom"], "kitob": m["kitob"], "jami": len(m["testlar"])} for r, m in b.mavzular.items()}

    @router.post("/api/bot/yoz")
    def yoz(body: Yoz, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization)
        matn = (body.matn or "").strip()
        if not matn:
            raise HTTPException(400, "Savolni yozing")
        bank, mav = mavzular_lugat()

        def f(cur):
            rol, sl = rol_aniqla(cur, u, body.rol)
            if rol == "oqituvchi":
                ctx = TCtx(mav, sl, lambda kalit: azolar_yukla(cur, u, kalit, sl), lambda bola: PS.pasport_yig(cur, bola, bank), lambda ids: mavzu_stat(cur, ids), body.sinf)
                r = ustoz_javobi(matn, ctx)
            else:
                x = xotira_ol(cur, u)
                x["_formula_tarix"] = formula_tarix(cur, u, body.formulalar)
                r = oquvchi_javobi(matn, Ctx(mav, lambda: PS.pasport_yig(cur, u, bank), x, [str(i) for i in body.formulalar]))
                xotira_yoz(cur, u, {k: v for k, v in (r.pop("xotira", None) or {}).items() if v is not None})
            r["rol"] = rol
            return r
        return run(f)

    @router.get("/api/bot/boshlash")
    def boshlash(token: str = None, rol: str = None, formulalar: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        bank, mav = mavzular_lugat()
        ids = [i for i in re.split(r"[,\s]+", formulalar or "") if i][:80]

        def f(cur):
            r_, sl = rol_aniqla(cur, u, rol)
            ism = ((PS._q(cur, "kb_u", "SELECT full_name FROM users WHERE user_id=%s", (u,)) or [{}])[0].get("full_name") or "").split(" ")
            if r_ == "oqituvchi":
                nom = ", ".join(x["nom"] for x in sl[:3]) or "sinf yo‘q"
                return {"rol": r_, "javob": [M("Salom! Men Kabu-botman." + (f" Sinflaringiz: {nom}." if sl else " Sizda hali faol sinf yo‘q.")), M("«22-o‘quvchi qayerda?», «kim eng zaif?», «kim faol emas?» kabi savollar bering.")],
                        "amallar": [], "eslatmalar": [], "takliflar": ["Sinf holati", "Kim eng zaif?", "Kim faol emas?", "Kirish testini kim topshirmagan?", "Qaysi mavzuda ko‘p xato?"]}
            x = xotira_ol(cur, u)
            yoq = bool(x.get("eslatma"))
            j, a, esl = [M("Salom! Men Kabu-botman." + (f" {ism[-1]}," if False else ""))], [], []
            if yoq:
                p = PS.pasport_yig(cur, u, bank)
                navbat = formula_navbat(ids, formula_tarix(cur, u, ids), datetime.now(TZ), 1) if ids else []
                if navbat:
                    esl.append("formula"); j.append(M("Bugungi takrorlash: bitta formulani yozib ko‘ring.")); a.append({"tur": "formula", "id": navbat[0], "yozuv": "Formulani yozish"})
                m = p["matematika"]
                if m["takrorlash"]:
                    t = m["takrorlash"][0]; esl.append("mavzu")
                    j.append(M(f"Takrorlash vaqti kelgan mavzu: {t['raqam']}. {t['nom']} ({t['holatlar']['takror'] + t['holatlar']['unutilgan']} ta savol).")); a.append(TEST([t["raqam"]], f"{t['raqam']}. {t['nom']}: test"))
                f_ = p["faollik"]
                if f_["oxirgi"] and f_["kun_7"] == 0:
                    esl.append("faollik"); j.append(M("Oxirgi 7 kunda mashq qilmadingiz. Bugun bir nechta savol yechib ko‘ring."))
                if not esl:
                    j.append(M("Bugun takrorlash shart emas, hammasi joyida."))
            else:
                j.append(M("Eslatmani yoqsangiz, takrorlash vaqti kelgan formula va mavzularni aytib turaman."))
            return {"rol": r_, "javob": j, "amallar": a, "eslatmalar": esl, "eslatma_yoqilgan": yoq, "takliflar": list(TAKLIF_BOSH)}
        return run(f)

    @router.post("/api/bot/formula_natija")
    def formula_natija(body: FormulaNatija, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization)

        def f(cur):
            cur.execute("""INSERT INTO kabu_bot_formula(user_id, formula_id, urinish, togri, oxirgi_togri) VALUES(%s,%s,1,%s,%s)
                           ON CONFLICT (user_id, formula_id) DO UPDATE SET urinish=kabu_bot_formula.urinish+1, togri=kabu_bot_formula.togri+EXCLUDED.togri,
                             oxirgi_togri=EXCLUDED.oxirgi_togri, yangilangan=NOW()""", (u, body.id, int(body.togri), body.togri))
            return {"ok": True}
        return run(f)

    return router

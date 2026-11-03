"""REV270: xalqaro kontentni tarjima qilish vositasi (uz → ru, en).

  python3 -I tools/tarjima.py extract            # content/*.json → tr/src/<nom>.json  (tarjima qilinadigan satrlar ro'yxati)
  python3 -I tools/tarjima.py check ru [nom]     # tr/ru/<nom>.json ni tekshiradi (to'liqlik, [n] belgilar, formulalar)
  python3 -I tools/tarjima.py merge ru           # content/*.json + tr/ru/*.json → content_ru/*.json (tuzilma aynan bir xil)

Tarjimon faqat tr/<til>/<nom>.json yozadi: {"s0001": "tarjima", ...}. Kalitlar tr/src dagidek.
Asl kontent o'zgarmaydi; tuzilma, javob kalitlari, id lar, rasmlar geometriyasi saqlanadi.
"""
import glob
import json
import os
import re
import sys

S = os.path.dirname(os.path.abspath(__file__))   # tools/xalqaro
CONTENT = os.environ.get("XB_CONTENT", f"{S}/content")
TR = os.environ.get("XB_TR", f"{S}/tr")

SKIP = {"turi", "sahna", "id", "mavzu", "asl_id", "jarayon", "kontekst", "fikrlash", "birlik", "asl", "toplam", "kod",
        "javob_turi", "taxminiy", "qiyinlik_ball", "oecd_foiz", "togri", "soha", "manba"}
SVG_TEXT = re.compile(r"(<(text|tspan|title)\b[^>]*>)([^<]+)(</\2>)")
LETTER = re.compile(r"[A-Za-zА-Яа-яЁёʻʼ‘’]{2,}|[A-Za-zА-Яа-я]")


RAMKA = [f"{S}/ramka.json", f"{S}/ramka_pisa.json"]
RAMKA_SKIP = {"maktab", "ustoz_fan", "fan", "dastur", "kalit", "natija", "en", "yil", "soha", "soha_en", "sinflar"}


def fayllar():
    out = sorted(glob.glob(f"{CONTENT}/*.json")) + sorted(glob.glob(f"{CONTENT}/pisa/*.json"))
    rows = [(os.path.relpath(f, CONTENT).replace("/", "__").removesuffix(".json"), f) for f in out]
    return rows + [("ramka__" + os.path.basename(f).removesuffix(".json"), f) for f in RAMKA if os.path.exists(f)]


def _skip(nom):
    return RAMKA_SKIP if nom.startswith("ramka__") else SKIP


def tarjimabop(s):
    """Faqat harf bo'lgan (raqam/formula emas) satrlar tarjima qilinadi. Bitta lotin harfi (A, B, x) — tarjima qilinmaydi."""
    if not isinstance(s, str) or not s.strip():
        return False
    t = re.sub(r"\$[^$]*\$", " ", s)                          # formulalar
    return bool(re.search(r"[A-Za-zА-Яа-яʻʼ‘’]{2,}", t)) or bool(re.search(r"\\text\{[^}]{2,}\}", s))


def satrlar(obj, key=None, skip=SKIP):
    """(yo'l, matn, turi) — turi: 'matn' yoki 'svg' (svg ichidagi <text> tugunlari)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in skip:
                continue
            yield from satrlar(v, k, skip)
    elif isinstance(obj, list):
        for v in obj:
            yield from satrlar(v, key, skip)
    elif isinstance(obj, str):
        if obj.lstrip().startswith("<svg"):
            for m in SVG_TEXT.finditer(obj):
                if tarjimabop(m.group(3)):
                    yield (key, m.group(3), "svg")
        elif tarjimabop(obj):
            yield (key, obj, "matn")


def extract():
    os.makedirs(f"{TR}/src", exist_ok=True)
    jami = 0
    for nom, f in fayllar():
        data = json.load(open(f))
        seen, rows = {}, []
        for item in (data if isinstance(data, list) else [data]):
            for key, text, tur in satrlar(item, skip=_skip(nom)):
                if text in seen:
                    continue
                sid = f"s{len(rows) + 1:04d}"
                seen[text] = sid
                rows.append({"k": sid, "maydon": key, "tur": tur, "uz": text})
        json.dump(rows, open(f"{TR}/src/{nom}.json", "w"), ensure_ascii=False, indent=0)
        jami += sum(len(r["uz"]) for r in rows)
        print(f"{nom}: {len(rows)} satr, {sum(len(r['uz']) for r in rows)} belgi")
    print("jami belgi:", jami)


MATH = re.compile(r"\$[^$]*\$")
CMD = re.compile(r"\\[A-Za-z]+")
UZ_IZ = re.compile(r"[oOgG][‘ʻ’']|\b\w+(lar|ning|dagi|gacha|ni|ga)\b")


def _norm_math(m, til):
    m = re.sub(r"\\text\{[^}]*\}", "", m).replace(" ", "")
    m = m.replace("{,}", ",").replace("{.}", ".")
    if til == "en":
        m = re.sub(r"(\d),(\d)", r"\1.\2", m)
    return m


def tekshir_satr(src, tr, til, tur):
    xato = []
    if not isinstance(tr, str) or not tr.strip():
        return ["bo'sh"]
    if re.findall(r"\[\d{1,2}\]", src) != re.findall(r"\[\d{1,2}\]", tr):
        xato.append("[n] belgilar mos emas")
    if src.count("$") != tr.count("$"):
        xato.append("$ soni mos emas")
    else:
        a = [_norm_math(m, til) for m in MATH.findall(src)]
        b = [_norm_math(m, til) for m in MATH.findall(tr)]
        if sorted(a) != sorted(b):
            if til == "en":
                a = [re.sub(r"(\d),(\d)", r"\1.\2", x) for x in a]
            if sorted(a) != sorted(b):
                xato.append(f"formula o'zgargan: {set(a) - set(b) or ''} → {set(b) - set(a) or ''}")
    if src.count("\n") != tr.count("\n"):
        xato.append("satrlar soni (\\n) mos emas")
    if til in ("ru", "en") and UZ_IZ.search(MATH.sub("", tr)) and tur != "svg":
        m = UZ_IZ.search(MATH.sub("", tr))
        if til == "ru" or re.search(r"[‘ʻ]", m.group(0)):
            xato.append(f"o'zbekcha qolgan: «{m.group(0)}»")
    if til == "ru" and tur == "matn" and not re.search(r"[А-Яа-яЁё]", tr) and re.search(r"[A-Za-z]{4,}", MATH.sub("", src)):
        xato.append("ruscha harf yo'q")
    if "|" in src and src.count("|") != tr.count("|") and tur == "matn" and len(src) < 60:
        pass   # javob muqobillari soni farq qilishi mumkin
    return xato


def check(til, faqat=None):
    yomon = 0
    for nom, _f in fayllar():
        if faqat and nom != faqat:
            continue
        src = json.load(open(f"{TR}/src/{nom}.json"))
        p = f"{TR}/{til}/{nom}.json"
        if not os.path.exists(p):
            print(f"{nom}: YO'Q")
            yomon += 1
            continue
        tr = json.load(open(p))
        xatolar = []
        for r in src:
            if r["k"] not in tr:
                xatolar.append(f"{r['k']}: tarjima yo'q")
                continue
            for x in tekshir_satr(r["uz"], tr[r["k"]], til, r["tur"]):
                xatolar.append(f"{r['k']} ({r['maydon']}): {x}")
        ortiqcha = set(tr) - {r["k"] for r in src}
        if ortiqcha:
            xatolar.append(f"ortiqcha kalitlar: {sorted(ortiqcha)[:5]}")
        print(f"{nom}: {'OK' if not xatolar else str(len(xatolar)) + ' xato'}")
        for x in xatolar[:40]:
            print("   ", x)
        yomon += bool(xatolar)
    return yomon


def _en_son(t):
    """Inglizcha: o'nli vergul → nuqta (tarjima qilinmagan sof son/formula satrlari va rasm yozuvlari uchun)."""
    return re.sub(r"(\d),(\d)", r"\1.\2", t.replace("{,}", "."))


RU_BIRLIK = {"kg": "кг", "km": "км", "mm": "мм", "sm": "см", "cm": "см", "m": "м", "g": "г", "l": "л", "s": "с", "ml": "мл", "kVt": "кВт", "Vt": "Вт", "V": "В", "A": "А"}


def _ru_birlik(t):
    """Ruscha: tarjima qilinmagan (faqat son+birlik) satrlarda lotin birliklari → kirill (formula ichiga tegilmaydi).
    Birlik faqat sondan keyin («10 g») yoki formuladan keyin («$5$ m») bo'lsa almashtiriladi."""
    qism = re.split(r"(\$[^$]*\$)", t)
    son = re.compile(r"(?<=\d)(\s?)(kVt|Vt|kg|km|mm|ml|sm|cm|m|g|l|s)(?![A-Za-z])")
    bosh = re.compile(r"^(\s)(kVt|Vt|kg|km|mm|ml|sm|cm|m|g|l|s)(?![A-Za-z])")
    out = []
    for i, q in enumerate(qism):
        if q.startswith("$"):
            out.append(q)
            continue
        q = son.sub(lambda m: m.group(1) + RU_BIRLIK[m.group(2)], q)
        if i and qism[i - 1].startswith("$"):
            q = bosh.sub(lambda m: m.group(1) + RU_BIRLIK[m.group(2)], q)
        out.append(q)
    return "".join(out)


def _apply(obj, lug, key=None, skip=SKIP, til=""):
    if isinstance(obj, dict):
        return {k: (v if k in skip else _apply(v, lug, k, skip, til)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_apply(v, lug, key, skip, til) for v in obj]
    if isinstance(obj, str):
        if obj.lstrip().startswith("<svg"):
            def node(m):
                t = m.group(3)
                return m.group(1) + (_xml(lug[t]) if t in lug else (_en_son(t) if til == "en" else _ru_birlik(t) if til == "ru" else t)) + m.group(4)
            return SVG_TEXT.sub(node, obj)
        if obj in lug:
            return lug[obj]
        if til == "en" and key not in ("id",):
            return _en_son(obj)
        if til == "ru" and key not in ("id",):
            return _ru_birlik(obj)
        return obj
    return obj


def _xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if not re.search(r"&\w+;", s) else s


def merge(til):
    out_dir = f"{S}/content_{til}"
    n = 0
    for nom, f in fayllar():
        p = f"{TR}/{til}/{nom}.json"
        if not os.path.exists(p):
            continue
        src = json.load(open(f"{TR}/src/{nom}.json"))
        tr = json.load(open(p))
        lug = {r["uz"]: tr[r["k"]] for r in src if r["k"] in tr}
        data = _apply(json.load(open(f)), lug, skip=_skip(nom), til=til)
        dst = os.path.join(out_dir, os.path.basename(f)) if nom.startswith("ramka__") else os.path.join(out_dir, os.path.relpath(f, CONTENT))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        json.dump(data, open(dst, "w"), ensure_ascii=False, indent=1)
        n += 1
    print(f"content_{til}: {n} fayl")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "extract":
        extract()
    elif cmd == "check":
        sys.exit(1 if check(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None) else 0)
    elif cmd == "merge":
        merge(sys.argv[2])

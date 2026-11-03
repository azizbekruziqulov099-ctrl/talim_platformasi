"""PISA parallel birliklar faylini tekshiradi: python3 -I tools/tekshir_pisa.py content/pisa/X.json"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAMKA = json.load(open(os.path.join(HERE, "ramka_pisa.json")))
BAD_SVG = re.compile(r"<\s*(script|image|foreignObject|iframe|use)\b|on[a-z]+\s*=|href\s*=|url\s*\(", re.I)


def svg_ok(r, q, errs):
    if not r:
        return
    r = str(r)
    if not r.lstrip().startswith("<svg") or "</svg>" not in r: errs.append(f"{q}: rasm SVG emas")
    if BAD_SVG.search(r): errs.append(f"{q}: SVG da taqiqlangan element")
    if len(r.encode()) > 15000: errs.append(f"{q}: SVG juda katta ({len(r.encode())})")


def check(path):
    errs = []
    data = json.load(open(path))
    if not isinstance(data, list) or not data:
        return ["Fayl bo‘sh bo‘lmagan JSON massiv bo‘lishi kerak"]
    seen = set()
    for u in data:
        b = u.get("birlik", "?")
        if not re.fullmatch(r"P-[A-Z0-9]+-[A-Z]\d{2,3}", str(b)): errs.append(f"{b}: birlik kodi P-TT-M07 ko‘rinishida bo‘lsin")
        tk = u.get("toplam")
        if tk not in RAMKA["toplamlar"]: errs.append(f"{b}: toplam noto‘g‘ri"); continue
        mavzular = {m["kalit"] for m in RAMKA["mavzular"][tk]}
        jarayon = set(RAMKA["jarayonlar"][tk])
        for f in ("asl", "nom"):
            if not str(u.get(f) or "").strip(): errs.append(f"{b}: {f} bo‘sh")
        if len(str(u.get("stimul") or "").strip()) < 40 and not u.get("stimul_rasm"): errs.append(f"{b}: stimul juda qisqa")
        svg_ok(u.get("stimul_rasm"), b, errs)
        qs = u.get("savollar") or []
        if not qs: errs.append(f"{b}: savol yo‘q")
        for n, v in enumerate(qs, 1):
            q = v.get("id", f"{b}#{n}")
            if v.get("id") != f"{b}-{n}": errs.append(f"{q}: id {b}-{n} bo‘lsin")
            if q in seen: errs.append(f"{q}: takror id")
            seen.add(q)
            if v.get("mavzu") not in mavzular: errs.append(f"{q}: mavzu {v.get('mavzu')} — {sorted(mavzular)} dan biri")
            if v.get("jarayon") not in jarayon: errs.append(f"{q}: jarayon {v.get('jarayon')} — {sorted(jarayon)} dan biri")
            if v.get("kontekst") not in RAMKA["kontekstlar"]: errs.append(f"{q}: kontekst noto‘g‘ri")
            if v.get("fikrlash") not in ("bilish", "qollash", "mulohaza"): errs.append(f"{q}: fikrlash noto‘g‘ri")
            qb = v.get("qiyinlik_ball")
            if not isinstance(qb, (int, float)) or not (200 <= qb <= 850): errs.append(f"{q}: qiyinlik_ball 200–850 son bo‘lsin")
            if not isinstance(v.get("taxminiy"), bool): errs.append(f"{q}: taxminiy true/false")
            of = v.get("oecd_foiz")
            if of is not None and not (isinstance(of, (int, float)) and 0 <= of <= 100): errs.append(f"{q}: oecd_foiz 0–100 yoki null")
            for k in ("kunikma", "usul", "savol", "maslahat"):
                if not str(v.get(k) or "").strip(): errs.append(f"{q}: {k} bo‘sh")
            t = v.get("turi")
            if t == "tanlov":
                js = v.get("javoblar")
                if not isinstance(js, list) or len(js) != 4 or not all(str(x).strip() for x in js) or len(set(map(str, js))) != 4:
                    errs.append(f"{q}: 4 ta turli javob kerak")
                if v.get("togri") not in (0, 1, 2, 3): errs.append(f"{q}: togri 0–3")
                x = v.get("xatolar") or {}
                if not all(str(x.get(str(i)) or "").strip() for i in range(4) if i != v.get("togri")): errs.append(f"{q}: har noto‘g‘ri variantga xato izohi")
                last = " ".join(s.get("doska", "") for s in (v.get("yechim") or [])[-2:])
                m = re.search(r"Javob\s*:?\s*\(?([ABCD])\b", last)
                if not m: errs.append(f"{q}: oxirgi qadamda «Javob: X)» yo‘q")
                elif v.get("togri") in (0, 1, 2, 3) and "ABCD".index(m.group(1)) != v["togri"]: errs.append(f"{q}: yechimdagi javob harfi togri ga mos emas")
            elif t == "ochiq":
                if not str(v.get("javob") or "").strip(): errs.append(f"{q}: ochiq javob bo‘sh")
                if v.get("javob_turi") not in ("son", "kasr", "soz"): errs.append(f"{q}: javob_turi son|kasr|soz")
                if not str((v.get("xatolar") or {}).get("umumiy") or "").strip(): errs.append(f"{q}: xatolar.umumiy kerak")
            else:
                errs.append(f"{q}: turi tanlov|ochiq")
            ys = v.get("yechim")
            if not isinstance(ys, list) or not (2 <= len(ys) <= 8) or not all(isinstance(s, dict) and str(s.get("doska") or "").strip() and str(s.get("ovoz") or "").strip() for s in ys):
                errs.append(f"{q}: yechim 3–6 qadam, doska+ovoz")
            svg_ok(v.get("rasm"), q, errs)
            txt = json.dumps(v, ensure_ascii=False)
            if txt.count("$") % 2: errs.append(f"{q}: $ juft emas")
        if re.search(r"[oOgG]'", json.dumps(u, ensure_ascii=False)): errs.append(f"{b}: o‘/g‘ da ' emas ‘ (U+2018)")
    return errs


if __name__ == "__main__":
    e = check(sys.argv[1])
    print("OK" if not e else "\n".join(e[:80]))
    sys.exit(1 if e else 0)

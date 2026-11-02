"""Dars faylini tekshiradi: python3 -I tools/tekshir_dars.py content/dars_X.json"""
import json, re, sys

TURLAR = {"kirish", "tushuntirish", "qoida", "misol", "birga", "mashq", "xulosa"}


def check(path):
    errs = []
    data = json.load(open(path))
    if not isinstance(data, list) or not data:
        return ["Fayl bo‘sh bo‘lmagan JSON massiv bo‘lishi kerak"]
    for d in data:
        k = d.get("kod", "?")
        if not re.fullmatch(r"XB-[A-Z0-9]+-[A-Z]{3}", str(k)): errs.append(f"{k}: kod XB-M8-KAS ko‘rinishida")
        if d.get("kod") != "XB-" + str(d.get("mavzu")): errs.append(f"{k}: kod = XB- + mavzu")
        for f in ("sarlavha", "maqsad"):
            if not str(d.get(f) or "").strip(): errs.append(f"{k}: {f} bo‘sh")
        qs = d.get("qadamlar") or []
        if not (10 <= len(qs) <= 24): errs.append(f"{k}: qadamlar soni {len(qs)} (12–20 kerak)")
        birga = 0
        misol_sahna = set()
        for i, q in enumerate(qs):
            p = f"{k}#{i}"
            if q.get("turi") not in TURLAR: errs.append(f"{p}: turi {q.get('turi')}")
            if not str(q.get("sahna") or "").strip(): errs.append(f"{p}: sahna bo‘sh")
            lines = [l for l in str(q.get("doska") or "").split("\n") if l.strip()]
            if not lines: errs.append(f"{p}: doska bo‘sh")
            ov = str(q.get("ovoz") or "")
            marks = [int(m) for m in re.findall(r"\[(\d{1,2})\]", ov)]
            if len(lines) > 1 and marks != list(range(1, len(lines) + 1)):
                errs.append(f"{p}: doskada {len(lines)} satr, ovozda belgilar {marks} — [1]..[{len(lines)}] kerak")
            if len(lines) == 1 and marks and marks != [1]: errs.append(f"{p}: bitta satr — faqat [1]")
            if len(re.sub(r"\[\d+\]", "", ov).strip()) < 15: errs.append(f"{p}: ovoz juda qisqa")
            for l in lines:
                if len(re.sub(r"\$[^$]*\$", "xxxxxx", l)) > 80: errs.append(f"{p}: doska satri juda uzun: {l[:40]}…")
            if q.get("turi") == "birga":
                birga += 1
                if not str(q.get("javob") or "").strip(): errs.append(f"{p}: birga — javob kerak")
            if q.get("turi") == "misol": misol_sahna.add(q.get("sahna"))
            if ov.count("$") % 2 or str(q.get("doska")).count("$") % 2: errs.append(f"{p}: $ juft emas")
        if birga < 2: errs.append(f"{k}: kamida 2 ta birga kerak")
        if len(misol_sahna) < 2: errs.append(f"{k}: kamida 2 ta misol sahnasi kerak")
        tm = d.get("tushunmadim") or {}
        sahnalar = {q.get("sahna") for q in qs}
        for s, vs in tm.items():
            if s not in sahnalar: errs.append(f"{k}: tushunmadim kaliti '{s}' sahnalarda yo‘q")
            for v in vs:
                if v.get("turi") not in ("sodda", "hikoya", "boshqa_usul", "rasm"): errs.append(f"{k}/{s}: variant turi")
                if not str(v.get("ovoz") or "").strip() or not str(v.get("doska") or "").strip(): errs.append(f"{k}/{s}: variant bo‘sh")
        if len(tm) < 2: errs.append(f"{k}: kamida 2 sahnaga tushunmadim kerak")
        for f in ("tipik_xatolar", "strategiyalar", "kalit_sozlar"):
            if not isinstance(d.get(f), list) or not d.get(f): errs.append(f"{k}: {f} ro‘yxat bo‘lsin")
        if re.search(r"[oOgG]'", json.dumps(d, ensure_ascii=False)): errs.append(f"{k}: o‘/g‘ da ' emas ‘ (U+2018) ishlating")
    return errs


if __name__ == "__main__":
    e = check(sys.argv[1])
    print("OK" if not e else "\n".join(e[:80]))
    sys.exit(1 if e else 0)

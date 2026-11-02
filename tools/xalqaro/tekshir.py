"""Parallel savollar faylini tekshiradi: python3 -I tools/tekshir.py content/X.json jobs/X.json"""
import json, re, sys

BAD_SVG = re.compile(r"<\s*(script|image|foreignObject|iframe|use)\b|on[a-z]+\s*=|href\s*=|url\s*\(", re.I)


def check(path, job_path=None):
    errs = []
    data = json.load(open(path))
    if not isinstance(data, list):
        return ["Fayl JSON massiv bo‘lishi kerak"]
    ids = [d.get("id") for d in data]
    if job_path:
        job = [j["id"] for j in json.load(open(job_path))]
        miss = [i for i in job if i not in ids]
        extra = [i for i in ids if i not in job]
        if miss: errs.append(f"Yetishmayapti: {miss}")
        if extra: errs.append(f"Ortiqcha: {extra}")
    for d in data:
        p = d.get("id", "?")
        for k in ("kunikma", "usul"):
            if not str(d.get(k) or "").strip(): errs.append(f"{p}: '{k}' bo‘sh")
        vs = d.get("variantlar")
        if not isinstance(vs, list) or len(vs) != 2:
            errs.append(f"{p}: aynan 2 ta variant kerak"); continue
        for n, v in enumerate(vs, 1):
            q = f"{p}/V{n}"
            t = v.get("turi")
            if t not in ("tanlov", "ochiq"): errs.append(f"{q}: turi noto‘g‘ri"); continue
            if len(str(v.get("savol") or "").strip()) < 10: errs.append(f"{q}: savol juda qisqa")
            if t == "tanlov":
                js = v.get("javoblar")
                if not isinstance(js, list) or len(js) != 4 or not all(str(x).strip() for x in js): errs.append(f"{q}: 4 ta javob kerak")
                elif len(set(map(str, js))) != 4: errs.append(f"{q}: javoblar takrorlangan")
                if v.get("togri") not in (0, 1, 2, 3): errs.append(f"{q}: togri 0–3 bo‘lishi kerak")
                x = v.get("xatolar") or {}
                wrong = [str(i) for i in range(4) if i != v.get("togri")]
                if not isinstance(x, dict) or not all(str(x.get(w) or "").strip() for w in wrong): errs.append(f"{q}: har noto‘g‘ri variant uchun xatolar kerak")
            else:
                if not str(v.get("javob") or "").strip(): errs.append(f"{q}: ochiq javob bo‘sh")
                if v.get("javob_turi") not in ("son", "kasr", "soz"): errs.append(f"{q}: javob_turi son|kasr|soz")
            ys = v.get("yechim")
            if not isinstance(ys, list) or not (2 <= len(ys) <= 9): errs.append(f"{q}: yechim 3–7 qadam bo‘lsin")
            else:
                for s in ys:
                    if not isinstance(s, dict) or not str(s.get("doska") or "").strip() or not str(s.get("ovoz") or "").strip():
                        errs.append(f"{q}: yechim qadamida doska/ovoz bo‘sh"); break
            if not str(v.get("maslahat") or "").strip(): errs.append(f"{q}: maslahat bo‘sh")
            r = v.get("rasm")
            if r:
                r = str(r)
                if not r.lstrip().startswith("<svg") or "</svg>" not in r: errs.append(f"{q}: rasm SVG emas")
                if BAD_SVG.search(r): errs.append(f"{q}: SVG da taqiqlangan element")
                if len(r.encode()) > 12000: errs.append(f"{q}: SVG juda katta ({len(r.encode())} bayt)")
            txt = json.dumps(v, ensure_ascii=False)
            if txt.count("$") % 2: errs.append(f"{q}: $ belgilari juft emas (formula yopilmagan)")
            if re.search(r"o'|g'|O'|G'", str(v.get("savol"))): errs.append(f"{q}: o‘/g‘ uchun ‘ (U+2018) ishlating")
    return errs


if __name__ == "__main__":
    e = check(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print("OK" if not e else "\n".join(e[:80]))
    sys.exit(1 if e else 0)

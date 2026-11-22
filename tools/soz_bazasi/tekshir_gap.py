"""REV696: gap bazasi qismini tekshirish — 11 til, token soni, yozuv turi, takror token yo'q."""
import json, re, sys
from tekshir import TILLAR, YOZUV, LOTIN


def tekshir(yol):
    xato, d, kalit = [], json.load(open(yol, encoding="utf-8")), set()
    for i, x in enumerate(d):
        joy = f"{yol}[{i}] {x.get('kalit', '?')}"
        if x.get("kalit") in kalit:
            xato.append(f"{joy}: kalit takror")
        kalit.add(x.get("kalit"))
        g = x.get("g") or {}
        for t in TILLAR:
            tok = g.get(t)
            if not isinstance(tok, list) or not (2 <= len(tok) <= 7):
                xato.append(f"{joy}: {t} — token soni 2–7 emas"); continue
            if any(not str(s).strip() or re.search(r"[.!?。！？،؟]$", str(s)) for s in tok):
                xato.append(f"{joy}: {t} — bo'sh token yoki tinish belgisi")
            if len({str(s).lower() for s in tok}) != len(tok):
                xato.append(f"{joy}: {t} — takror token")
            s = " ".join(map(str, tok))
            if t in YOZUV and not re.search(YOZUV[t], s, re.I):
                xato.append(f"{joy}: {t} «{s}» — yozuv turi noto'g'ri")
            if t in LOTIN and re.search(r"[а-яё؀-ۿ぀-ヿ一-鿿가-힯]", s, re.I):
                xato.append(f"{joy}: {t} «{s}» — lotin emas")
            if t == "ja" and re.search(r"[一-鿿]", s):
                xato.append(f"{joy}: ja «{s}» — kanji bor")
            if t == "ar" and re.search(r"[ً-ْ]", s):
                xato.append(f"{joy}: ar «{s}» — harakat belgilari bor")
            if t in LOTIN | {"ru"} and tok[0][:1] != tok[0][:1].upper():
                xato.append(f"{joy}: {t} — birinchi token bosh harf bilan emas")
    return d, xato


if __name__ == "__main__":
    jami = 0
    for yol in sys.argv[1:]:
        d, xato = tekshir(yol)
        for e in xato[:40]:
            print("XATO", e)
        print(f"{yol}: {len(d)} gap, {len(xato)} xato"); jami += len(xato)
    sys.exit(1 if jami else 0)

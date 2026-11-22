"""REV695: so'z bazasi qismini tekshirish — 11 til to'liq, yozuv turi to'g'ri, kalit/id takrorlanmaydi."""
import json, re, sys

TILLAR = ["uz", "ru", "en", "de", "fr", "es", "ar", "tr", "zh", "ja", "ko"]
TURKUM = {"odam", "hayvon", "meva", "sabzavot", "ovqat", "ichimlik", "kiyim", "oyinchoq", "transport", "maktab", "uy", "tabiat", "tana", "joy", "kasb", "harakat", "buyum", "osimlik", "boshqa"}
YOZUV = {"ru": r"[а-яё]", "ar": r"[؀-ۿ]", "zh": r"[一-鿿]", "ja": r"[぀-ヿ]", "ko": r"[가-힯]"}
LOTIN = {"uz", "en", "de", "fr", "es", "tr"}


def tekshir(yol, maktab=False):
    xato = []
    d = json.load(open(yol, encoding="utf-8"))
    kalit, idlar = set(), set()
    for i, x in enumerate(d):
        joy = f"{yol}[{i}] {x.get('kalit', '?')}"
        for k in ("id", "fayl", "kalit", "turkum", "daraja", "w"):
            if k not in x:
                xato.append(f"{joy}: «{k}» yo'q")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", str(x.get("kalit", ""))):
            xato.append(f"{joy}: kalit snake_case emas")
        if x.get("kalit") in kalit:
            xato.append(f"{joy}: kalit takror")
        if x.get("id") in idlar:
            xato.append(f"{joy}: id takror")
        kalit.add(x.get("kalit")); idlar.add(x.get("id"))
        if x.get("turkum") not in TURKUM:
            xato.append(f"{joy}: turkum noma'lum «{x.get('turkum')}»")
        if x.get("daraja") not in (1, 2, 3):
            xato.append(f"{joy}: daraja 1–3 emas")
        w = x.get("w") or {}
        for t in TILLAR:
            s = str(w.get(t) or "").strip()
            if not s:
                xato.append(f"{joy}: {t} bo'sh"); continue
            if len(s.split()) > 4 or re.search(r"[/()\[\]|;]", s):
                xato.append(f"{joy}: {t} «{s}» — uzun yoki variantli")
            if t in YOZUV and not re.search(YOZUV[t], s, re.I):
                xato.append(f"{joy}: {t} «{s}» — yozuv turi noto'g'ri")
            if t in LOTIN and re.search(r"[а-яё؀-ۿ぀-ヿ一-鿿가-힯]", s, re.I):
                xato.append(f"{joy}: {t} «{s}» — lotin emas")
            if t == "ja" and re.search(r"[一-鿿]", s):
                xato.append(f"{joy}: ja «{s}» — kanji bor")
            if t == "ar" and re.search(r"[ً-ْ]", s):
                xato.append(f"{joy}: ar «{s}» — harakat belgilari bor")
        if maktab and x.get("soz_turi") not in ("ot", "fel", "sifat", "ravish", "ibora", "son"):
            xato.append(f"{joy}: soz_turi noma'lum")
        # "artiklsiz": true — oy, hafta kuni, fan nomi kabi artiklsiz aytiladigan otlar (de/fr/es/ar tekshirilmaydi)
        if x.get("artiklsiz"):
            continue
        if (x.get("soz_turi") == "ot") if maktab else (x.get("turkum") != "harakat"):
            # arabcha izofa («رائد الفضاء») — ikkinchi so'zi «ال» bilan: qabul qilinadi
            for t, rx in (("de", r"^(der|die|das) "), ("fr", r"^(le |la |les |l[’'])"), ("es", r"^(el|la|los|las) "), ("ar", r"^ال|\sال")):
                s = str(w.get(t) or "")
                if s and not re.search(rx, s):
                    xato.append(f"{joy}: {t} «{s}» — artikl yo'q")
    return d, xato


if __name__ == "__main__":
    jami = 0
    maktab = "--maktab" in sys.argv
    for yol in [a for a in sys.argv[1:] if a != "--maktab"]:
        d, xato = tekshir(yol, maktab)
        for e in xato[:40]:
            print("XATO", e)
        print(f"{yol}: {len(d)} so'z, {len(xato)} xato")
        jami += len(xato)
    sys.exit(1 if jami else 0)

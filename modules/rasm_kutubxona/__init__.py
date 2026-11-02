"""REV259: umumiy rasm kutubxonasi — saytdagi barcha chizilgan rasmlar (dars rasmlari, xona rasmlari, javob variantlari,
bog'cha rasmlari) backend uchun ham: Kabutar TV, maktab (1–11-sinf), sertifikat guruhlari, taqdimot (PPT) yasash va
rasm topish funksiyalari shu yerdan oladi. Qidirish — so'z (istalgan tilda) yoki emoji bo'yicha, saytdagi qoidalar bilan:
javob uchun ataylab chizilgan rasm (d_v-…) ustun; bog'cha rasmlari («past») bor so'zni noaniq qilmaydi."""
import json
import os
import re
import unicodedata
from functools import lru_cache

PAPKA = os.path.dirname(os.path.abspath(__file__))
RASM_PAPKA = os.path.join(PAPKA, "rasm")
_ARTIKL = re.compile(r"^(the|a|an|der|die|das|le|la|les|l'|el|los|las|un|une)\s+", re.I)


def norm(matn):
    t = unicodedata.normalize("NFKD", str(matn or "")).lower()
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.replace("‘", "'").replace("’", "'").replace("ʻ", "'").replace("`", "'")
    t = re.sub(r"\[/?[a-z]{2}\]", "", t)
    t = re.sub(r"[!?.,;:«»\"()…]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


@lru_cache(maxsize=1)
def katalog():
    with open(os.path.join(PAPKA, "katalog.json"), encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _xarita():
    m, em = {}, {}
    def qosh(t, i):
        for k in {norm(t), _ARTIKL.sub("", norm(t))}:
            if len(k) < 2:
                continue
            old = m.get(k, "yoq")
            if old != "yoq" and old and old.startswith("d_v-"):
                continue
            if i.startswith("d_v-"):
                m[k] = i
            elif old == "yoq":
                m[k] = i
            elif old != i and not (old and old.startswith("d_") and not i.startswith("d_")):
                m[k] = None
    for r in katalog():
        if not r.get("past"):
            for w in r.get("sozlar") or []:
                qosh(w, r["id"])
    for r in katalog():
        if r.get("past"):
            for w in r.get("sozlar") or []:
                k = norm(w)
                if k and k not in m:
                    m[k] = r["id"]
        e = (r.get("emoji") or "").replace("\ufe0f", "")
        if e:
            em.setdefault(e, []).append(r["id"])
    return m, em


def _yozuv(i):
    return next((r for r in katalog() if r["id"] == i), None)


def rasm_top(soz="", emoji=""):
    """So'z (istalgan tilda) yoki emoji bo'yicha rasm: {"id", "fayl", "yol"} yoki None. Noaniq bo'lsa — None."""
    m, em = _xarita()
    i = m.get(norm(soz)) if soz else None
    if not i and emoji:
        ids = em.get(str(emoji).replace("\ufe0f", ""), [])
        i = ids[0] if len(ids) == 1 else None
    if not i:
        return None
    r = _yozuv(i)
    return {"id": i, "fayl": r["fayl"], "yol": os.path.join(RASM_PAPKA, r["fayl"])} if r else None


def qidir(soz, n=12):
    """Qisman moslik bilan qidirish (admin, taqdimot yasash, rasm tanlash uchun)."""
    q = norm(soz)
    if not q:
        return []
    out = []
    for r in katalog():
        if any(q in norm(w) for w in r.get("sozlar") or []):
            out.append({"id": r["id"], "fayl": r["fayl"], "sozlar": (r.get("sozlar") or [])[:4]})
            if len(out) >= n:
                break
    return out

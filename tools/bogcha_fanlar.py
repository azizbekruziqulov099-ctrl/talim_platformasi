"""REV121: bog'cha fanlari (Atrof-muhit, Matematika) — yangi yosh guruhlariga: 2-3, 4-5, 6-7 yosh.

Til kitoblari kabi (bogcha_yosh_rev99.py) eski 5 ta kitob (2-3, 3-4, 4-5, 5-6, 6-7) uchta yoshga yig'iladi:
  2-3 yosh = 2-3 kitobi + 3-4 kitobining 1-4 bo'limlari (eng sodda mavzular)
  4-5 yosh = 3-4 kitobining 5-8 bo'limlari + 4-5 kitobi
  6-7 yosh = 5-6 kitobi + 6-7 kitobi
Takror nomli darslar (bir xil «name») chiqarib tashlanadi. O'zbekcha gaplar «sen» va robot Kabu uslubiga o'tadi
(warm). Mantiq kitoblari alohida — tools/bogcha_mantiq.py.

Ishlatish: python tools/bogcha_fanlar.py → tools/bogcha_content/am_23y.json, am_45y.json, am_67y.json, mt_…
"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.bogcha_spiral import _clean, validate  # noqa: E402
from tools.bogcha_yosh_rev99 import sen as _sen  # noqa: E402

ROOT = Path(__file__).resolve().parent / "bogcha_content"
FANLAR = ("am", "mt")
PLAN = {
    "23y": ((("23", None), ("34", (0, 1, 2, 3))), "2-3 yosh", "2–3 yosh"),
    "45y": ((("34", (4, 5, 6, 7)), ("45", None)), "4-5 yosh", "4–5 yosh"),
    "67y": ((("56", None), ("67", None)), "6-7 yosh", "6–7 yosh"),
}


OLDIN = {"topib keling": "topib kel", "olib keling": "olib kel", "Topib keling": "Topib kel", "Olib keling": "Olib kel"}
KEYIN = {"Men ko'k osmonda uchishni yaxshi ko'raman, gu-gu!": "Men ko'k osmonga qarashni yaxshi ko'raman, bip-bip!",
         "Mening qanotlarim va panjalarim bor. Senda-chi?": "Mening temir qo'llarim va oyoqlarim bor. Senda-chi?",
         "Men ham qushman! Qushlarning": "Qushlarning",
         "Bu — kabutar, xuddi men kabi! Kabu «gu-gu» deydi.": "Bu — kabutar. U «gu-gu» deydi.",
         "Men uchayotganimda qanotlarimni bir narsa ko'tarib yuradi.": "Qushlar uchganda qanotlarini bir narsa ko'tarib yuradi.",
         "Ko'zguga qarasam, u yerda boshqa bir kabutar turibdi! O'ng qanotimni ko'tarsam, u chapini ko'taradi.":
             "Ko'zguga qarasam, u yerda boshqa bir robot turibdi! O'ng qo'limni ko'tarsam, u chapini ko'taradi.",
         "» deng": "» de", "Kabu «gu-gu» deydi": "Kabutar «gu-gu» deydi", "Qanotim og'rib": "Qo'lim og'rib",
         "ustasisiz": "ustasisan", "do'stisiz": "do'stisan", "oxirgisiz": "oxirgisan", "sizniki": "seniki", "ingizdek": "ingdek",
         "eshitdingiz": "eshitding"}


def sen(text):
    if not text:
        return text
    for a, b in OLDIN.items():
        text = text.replace(a, b)
    text = _sen(text)
    for a, b in KEYIN.items():
        text = text.replace(a, b)
    text = re.sub(r"ingizdagi", "ingdagi", text)
    text = re.sub(r"(?<!«)\bgu-gu\b(?!»| — kabutar)", "bip-bip", text)   # robot Kabu endi «gu-gu» demaydi (kabutardan tashqari)
    # «sen — suv qo'riqchisisiz!» → «…qo'riqchisisan!» (gapdagi «sen» ga mos kesim)
    text = re.sub(r"(\bsen\b(?:\s*—)?(?:\s+[\w'’]+){0,3}?\s+[\w'’]+?)siz(?=[!.,])", r"\1san", text, flags=re.I)
    return text


def warm_fan(book):
    """Fan kitobi: hamma o'zbekcha matn (tushuntirish ham) «sen» va robot Kabu uslubida."""
    for unit in book["units"]:
        for les in unit["lessons"]:
            les["intro"] = sen(les.get("intro"))
            for it in les.get("items") or []:
                for k in ("action", "explain"):
                    if it.get(k):
                        it[k] = sen(it[k])
            for row in les.get("extra") or []:
                for k in ("sarlavha", "matn", "sodda", "boshqa_usul"):
                    if row.get(k):
                        row[k] = sen(row[k])
            for row in les.get("extra") or []:
                if "Assalomu" in (row.get("doska") or ""):
                    row["doska"] = row["doska"].replace("🕊️", "🤖")
            for t in les.get("tests") or []:
                t["q"] = sen(t["q"])
                if "Kabu" in t["q"]:    # robot Kabu haqidagi savol — kabutar emas, robot rasmi
                    t["options"] = [o.replace("🕊️", "🤖") for o in t["options"]]
                if t.get("why"):
                    t["why"] = sen(t["why"])
    return book


def compose(fan, key):
    parts, age, label = PLAN[key]
    book = None
    seen = set()
    for src, idx in parts:
        other = json.loads((ROOT / f"{fan}_{src}.json").read_text(encoding="utf-8"))
        if book is None:
            book = {k: v for k, v in other.items() if k != "units"}
            book["units"] = []
        units = other["units"] if idx is None else [other["units"][i] for i in idx]
        for unit in units:
            unit = copy.deepcopy(unit)
            unit["lessons"] = [les for les in unit["lessons"] if _clean(les["name"]).lower() not in seen]
            seen.update(_clean(les["name"]).lower() for les in unit["lessons"])
            if unit["lessons"]:
                book["units"].append(unit)
    book["age"] = age
    book["book_title"] = re.sub(r"\d\s*[–-]\s*\d\s*yosh$", label, book.get("book_title", "")).strip()
    warm_fan(book)
    if age == "4-5 yosh":   # 4-5 yoshga 2 ta variant yetadi (3-4 kitobidan kelganlari allaqachon 2 ta)
        for unit in book["units"]:
            for les in unit["lessons"]:
                for q in les.get("tests") or []:
                    if len(q["options"]) > 2:
                        right = q["options"][q["answer"]]
                        other = next(o for i, o in enumerate(q["options"]) if i != q["answer"])
                        q["options"] = [right, other] if q["answer"] % 2 == 0 else [other, right]
                        q["answer"] = q["options"].index(right)
    validate(book)
    (ROOT / f"{fan}_{key}.json").write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return book


if __name__ == "__main__":
    for fan in FANLAR:
        for key in PLAN:
            b = compose(fan, key)
            print(fan, key, b["subject"], b["age"], len(b["units"]), "bo'lim",
                  sum(len(u["lessons"]) for u in b["units"]), "dars")

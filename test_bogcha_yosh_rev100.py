"""REV100: 4-5 va 6-7 yosh kitoblari (10 til) — yosh, «sen» uslubi, robot Kabu, jonli SVG rasmlar."""
import json
import re
from pathlib import Path

from tools.bogcha_yosh_rev99 import SPLIT, sen

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "tools" / "bogcha_content"
SVG = ROOT / "tools" / "bogcha_rasmlar" / "svg"
LANGS = ("en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh")
# REV110: yangi darslar rasmlari hali chizilmoqda (Gemini) — kelguncha emoji ko'rinadi.
_PLAN = json.loads((CONTENT / "reja_rasmli.json").read_text(encoding="utf-8"))
PENDING = {it["image"] for units in _PLAN.values() for u in units for l in u["lessons"] for it in l["items"]}


def _uz(text):
    return " ".join(part for n, part in enumerate(SPLIT.split(str(text or ""))) if n % 2 == 0)


def test_sen_converter_keeps_foreign_and_robot():
    assert sen("Ayting! [en]Say it![/en]") == "Ayt! [en]Say it![/en]"
    assert sen("Kabutar qushchaman. Gu-gu!") == "robot Kabuman. Bip-bip!"
    assert sen("Men uya qurdim") == "Mening temir uycham bor"
    assert sen("dengiz") == "dengiz" and sen("Rang-barang") == "Rang-barang"


def test_4_5_and_6_7_books():
    for lang in LANGS:
        for key, age, maxopt in (("45y", "4-5 yosh", 2), ("67y", "6-7 yosh", 4)):
            book = json.loads((CONTENT / f"{lang}_{key}.json").read_text(encoding="utf-8"))
            assert book["age"] == age and age in book["book_title"].replace("–", "-")
            assert len(book["units"]) >= 10
            for unit in book["units"]:
                for les in unit["lessons"]:
                    uz = _uz(les.get("intro"))
                    assert not re.search(r"\b(siz|Siz|sizga|keling|Keling)\b", uz), (lang, key, uz)
                    assert not re.search(r"Kabutar qushcha|Gu-gu|patlarim|qanotlarim|uya qurdim", uz)
                    for it in les.get("items") or []:
                        if it.get("image") and it["image"] not in PENDING:
                            assert (SVG / (Path(it["image"]).stem + ".svg")).is_file(), it["image"]
                    for t in les.get("tests") or []:
                        assert len(t["options"]) <= maxopt

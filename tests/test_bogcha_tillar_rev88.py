"""REV88: 9 ta chet tili kitobi (ingliz tili andozasidan) — to'liqlik, teglar, o'qilish, ovoz bo'laklari."""
import json
import re
from pathlib import Path

import pytest

from modules.speech_language import split_speech_text
from modules.speech_pronunciation import prepare_speech
from tools.bogcha_kitob import build_books
from tools.bogcha_tillar import LANGS, ROMANIZED, check

ROOT = Path(__file__).resolve().parents[1] / "tools" / "bogcha_content"


@pytest.mark.parametrize("lang", sorted(LANGS))
def test_translation_complete(lang):
    assert check(lang) == []


@pytest.mark.parametrize("lang", sorted(LANGS))
def test_language_books_build_like_english(lang):
    books = build_books([ROOT / f"{lang}_{a}.json" for a in ("34", "45", "56", "67")])
    assert [b["immersion"] for b in books] == [1, 2, 3, 4]
    for book in books:
        text = json.dumps(book, ensure_ascii=False)
        assert "[en]" not in text and f"[{lang}]" in text
        assert not re.search(r"\bingliz|\bIngliz|Angliya", text)
        scenes = [t for t in book["topics"] if t.get("image_scene")]
        assert len(scenes) == 8
        for topic in book["topics"]:
            for row in topic["rows"]:
                if row["turi"] == "test":
                    opts = [o[3:] for o in row["variantlar"].split("\n")]
                    assert len(set(opts)) == len(opts)
    cur = json.loads((ROOT / f"{lang}_56.json").read_text(encoding="utf-8"))
    items = [it for u in cur["units"] for les in u["lessons"] for it in les["items"]]
    assert all(it.get("image") for it in items)              # rasmlar ingliz kitobi bilan umumiy
    if lang in ROMANIZED:
        assert all(it.get("rom") for it in items)
    assert all(re.findall(r"\{[a-z]+\}", cur["class"]["which"]) == ["{w}"] for _ in [0])


def test_speech_reads_every_language_tag():
    parts = split_speech_text("Qarang: [de]Hallo![/de] [ja]こんにちは[/ja] [ar]مرحبا[/ar] [zh]你好[/zh] [ko]안녕[/ko]")
    assert [p[0] for p in parts if p[1].strip()] == ["uz", "de", "ja", "ar", "zh", "ko"]
    assert prepare_speech("Hallo, 5 Freunde!", "de") == "Hallo, 5 Freunde!"
    assert prepare_speech("[lat]x+y[/lat]", "ru") == "икс плюс игрек"

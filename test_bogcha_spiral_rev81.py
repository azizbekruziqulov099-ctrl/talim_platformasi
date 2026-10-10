import json
from pathlib import Path

import pytest

from tools.bogcha_spiral import BookError, build_book

ROOT = Path(__file__).resolve().parents[1] / "tools" / "bogcha_content"
CURRICULA = sorted(p for p in ROOT.glob("*_*.json") if p.stem[:2] in ("en", "ru", "mt", "am") and len(p.stem) == 5)


def _cur():
    return {"subject": "Ingliz tili", "lang": "en", "age": "3-4 yosh", "prefix": "EN", "units": [
        {"name": "Salom", "emoji": "👋", "lessons": [
            {"name": "Hello", "items": [{"say": "Hello!", "uz": "salom", "emoji": "👋"}, {"say": "Bye!", "uz": "xayr", "emoji": "🙋"}]},
            {"name": "Boy", "items": [{"say": "boy", "uz": "o'g'il bola", "emoji": "👦"}, {"say": "girl", "uz": "qiz", "emoji": "👧"}]}]},
        {"name": "Ranglar", "emoji": "🌈", "lessons": [
            {"name": "Red", "items": [{"say": "red", "uz": "qizil", "emoji": "🔴"}, {"say": "blue", "uz": "ko'k", "emoji": "🔵"}]}]}]}


def test_spiral_adds_reviews_old_questions_and_final_lesson():
    book = build_book(_cur())
    names = [t["name"] for t in book["topics"]]
    assert names == ["Hello", "Boy", "1-bo'lim takrori: Salom", "Red", "2-bo'lim takrori: Ranglar", "Katta bayram: hammasini takrorlaymiz"]
    red = book["topics"][3]["rows"]
    assert any(r["sarlavha"].startswith("🔁 Eslaymiz") for r in red)
    assert any(r["turi"] == "test" and r["sarlavha"] == "🔁 Eski savol" for r in red)
    for topic in book["topics"]:
        for row in topic["rows"]:
            if row["turi"] == "test":
                assert len(row["variantlar"].splitlines()) == 2  # 3-4 yosh: 2 ta rasm
                assert row["javob"] in "AB"


def test_validation_rejects_duplicates_and_missing_tests():
    cur = _cur()
    cur["units"][1]["lessons"][0]["name"] = "Hello"
    with pytest.raises(BookError):
        build_book(cur)
    cur = _cur() | {"lang": None, "subject": "Matematika"}
    with pytest.raises(BookError):
        build_book(cur)  # matematikada explain va testlar majburiy


@pytest.mark.parametrize("path", CURRICULA, ids=lambda p: p.stem)
def test_shipped_curricula_build(path):
    book = build_book(json.loads(path.read_text(encoding="utf-8")))
    lessons = [t for t in book["topics"] if "takror" not in t["name"] and not t["name"].startswith("Katta bayram")]
    assert len(lessons) >= 24
    assert book["topics"][-1]["name"].startswith("Katta bayram")

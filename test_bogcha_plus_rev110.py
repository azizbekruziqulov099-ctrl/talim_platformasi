"""REV110: yangi darslar — platformada 2–3 yoshda 50, 4–5 da 80, 6–7 da 100 dars (10 tilda)."""
import json
from pathlib import Path

from tools.bogcha_spiral import build_book, stats

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "tools" / "bogcha_content"
LANGS = ("en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh")
WANT = (("23y", 50), ("45y", 80), ("67y", 100))


def test_lesson_counts_all_languages():
    for lang in LANGS:
        prev = None
        for key, want in WANT:
            book = json.loads((CONTENT / f"{lang}_{key}.json").read_text(encoding="utf-8"))
            got = stats(build_book(book, None, prev))["darslar"]
            assert got == want, (lang, key, got)
            prev = book


def test_plus_lessons_speak_and_use_tags():
    for key in ("23p", "45p", "67p"):
        book = json.loads((CONTENT / f"en_{key}.json").read_text(encoding="utf-8"))
        for unit in book["units"]:
            for les in unit["lessons"]:
                matn = les["extra"][0]["matn"]
                assert "[en]" in matn, les["name"]
                assert len(les["tests"]) >= 2, les["name"]

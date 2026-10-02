import json
import re
from pathlib import Path

from modules.dars_xonasi import emoji_key, emoji_pictures

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "tools" / "bogcha_content"


def test_emoji_key_and_pictures():
    assert emoji_key("🐱 cat\nmushuk") == "🐱"
    assert emoji_key("5️⃣ five") == "5⃣"
    assert emoji_key("cat") == "" and emoji_key("") == ""
    pics = emoji_pictures([{"payload": {"doska_matni": "🐱 cat", "media_id": "a.svg"}},
                           {"payload": {"doska_matni": "🐱 kot", "media_id": "b.svg"}}], lambda m: "/m/" + m)
    assert pics == {"🐱": "/m/a.svg"}


def test_2_3_books_are_warm_simple_and_keep_translations():
    for lang in ("en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh"):
        book = json.loads((CONTENT / f"{lang}_23.json").read_text(encoding="utf-8"))
        assert book["age"] == "2-3 yosh"
        text = json.dumps(book, ensure_ascii=False)
        assert "Kabutar qushcha" not in text and "Gu-gu" not in text
        for unit in book["units"]:
            assert not unit.get("scenarios")
            for les in unit["lessons"]:
                assert len(les["intro"]) <= 220
                assert not re.search(r"\b(ayting|qiling|ko'rsating|Siz|sizga)\b", les["intro"] + " ".join(i.get("action", "") for i in les["items"]))
                for it in les["items"]:
                    assert (ROOT / "tools" / "bogcha_rasmlar" / "svg" / (Path(it["image"]).stem + ".svg")).is_file(), it["image"]

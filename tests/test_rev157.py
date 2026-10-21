"""REV157: bog'cha 4–7 yosh — dars to'liq o'rganilayotgan tilda; xulosaga o'zbekcha «Esda tut:» qo'shilmaydi;
ovoz keshi umumiy (CDN/brauzer) va 304 qaytaradi."""
import json
import re
from pathlib import Path

from tools.bogcha_spiral import build_book

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "tools" / "bogcha_content"


def _load(name):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def _tashqi(text):
    return re.sub(r"\[(\w\w)\][\s\S]*?\[/\1\]", "", str(text or "")).strip()


def test_45_lesson_in_target_language_with_one_time_translation():
    book = build_book(_load("de_45y.json"), None, _load("de_23y.json"))
    rows = [r for t in book["topics"][1:6] for r in t["rows"] if r["turi"] in ("kirish", "tushuncha", "topshiriq")]
    assert rows
    for r in rows:
        # tegdan tashqarida faqat yangi so'zning bir martalik tarjimasi («— isming nima?»)
        assert len(_tashqi(r["matn"]).split()) <= 5, r["matn"]
        assert "  " not in r["matn"] and "?." not in r["matn"] and " ." not in r["matn"], r["matn"]


def test_67_lesson_has_no_uzbek():
    book = build_book(_load("de_67y.json"), None, _load("de_45y.json"))
    rows = [r for t in book["topics"][1:6] for r in t["rows"] if r["turi"] in ("tushuncha", "topshiriq")]
    assert rows and all(_tashqi(r["matn"]) == "" for r in rows)


def test_xulosa_fully_tagged_gets_no_uzbek_prefix():
    src = (ROOT / "modules" / "ai_miya_varoq.py").read_text(encoding="utf-8")
    assert "toliq_teg" in src and '(text if toliq_teg else "Esda tut: " + text)' in src


def test_voice_cache_is_public_and_supports_304():
    src = (ROOT / "samtm_platform.py").read_text(encoding="utf-8")
    assert '"Cache-Control": "public, max-age=31536000, immutable"' in src
    assert "status_code=304" in src
    assert '"public, max-age=600"' in src   # yangi (chala bo'lishi mumkin) oqim — qisqa muddat

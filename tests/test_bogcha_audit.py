"""REV324: bog'cha til kitoblari yoshga mos — barcha JSON'lar tools/bogcha_audit.py qoidalaridan o'tadi."""
import copy
import json
from pathlib import Path

import pytest

from tools.bogcha_audit import (RULES, REPO, audit_all, audit_book, book_files, sentences, summarize, words,
                                write_report)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def result():
    return audit_all()


def _fmt(result, limit=25):
    rows = [f"{f}: [{c}] {w} — {d}" for f, issues in sorted(result["files"].items()) for c, w, d in issues]
    return "\n".join(rows[:limit]) + (f"\n… yana {len(rows) - limit}" if len(rows) > limit else "")


def test_all_three_locations_are_scanned(result):
    files = [str(p.relative_to(ROOT)) for p in book_files()]
    assert any(f.startswith("bogcha_content/") for f in files)
    assert any(f.startswith("tools/bogcha_content/") for f in files)
    assert any("/" not in f for f in files)          # repo ildizidagi nusxalar
    assert result["stats"]["fayl"] == len(files) >= 66
    langs = {Path(f).name[:2] for f in files}
    assert langs == {"en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh"}


def test_every_book_passes_age_rules(result):
    summ = summarize(result)
    assert summ["jami"] == 0, "qoidaga zid joylar:\n" + _fmt(result)


def test_root_copies_match_bogcha_content():
    for p in sorted((ROOT / "bogcha_content").glob("*.json")):
        twin = ROOT / p.name
        if twin.is_file():
            assert json.loads(p.read_text(encoding="utf-8")) == json.loads(twin.read_text(encoding="utf-8")), p.name


def test_item_counts_follow_age_groups(result):
    """Har yosh guruhida darsdagi element soni qoidada (alohida, aniq xabar bilan)."""
    for p in book_files():
        lang, age = p.name[:2], p.name[3:5]
        group = {"23": "2-3", "34": "2-3", "45": "4-5", "56": "4-5", "67": "6-7"}[age]
        lo, hi = RULES[group]["items"]
        book = json.loads(p.read_text(encoding="utf-8"))
        for unit in book["units"]:
            for les in unit["lessons"]:
                assert lo <= len(les["items"]) <= hi, (str(p.relative_to(ROOT)), les["name"], len(les["items"]))


def test_fixes_are_already_applied():
    """Tuzatishlar qo'llangan: qayta ishga tushirilsa hech narsa o'zgarmaydi."""
    from tools.bogcha_tuzatish_rev324 import Fixer
    fx = Fixer()
    changed = fx.run(write=False)
    assert changed == [] and fx.log == [], fx.log[:5]


# ── audit qoidalarining o'zi to'g'ri ishlashi ──
def _book(**lesson):
    les = {"name": "Dars", "goal": "Maqsad", "intro": "Salom! Bugun o'ynaymiz.",
           "items": [{"say": "cat", "uz": "mushuk", "emoji": "🐱", "image": "a.png"},
                     {"say": "dog", "uz": "kuchuk", "emoji": "🐶", "image": "b.png"}]}
    les.update(lesson)
    return {"units": [{"name": "Bo'lim", "lessons": [les]}]}


def _codes(book, lang="en", group="2-3"):
    return {c for c, _, _ in audit_book(book, lang, group)}


def test_clean_book_has_no_issues():
    assert _codes(_book()) == set()


def test_detects_counts_and_lengths():
    base = _book()
    assert "items_soni" in _codes(base, group="6-7")                       # 6-7 yoshda kamida 4 ta
    many = _book(items=[{"say": w, "uz": w, "emoji": "⭐", "image": f"{w}.png"} for w in ("a1", "b2", "c3", "d4")])
    assert "items_soni" in _codes(many, group="2-3")                       # 2-3 yoshda ko'pi bilan 3 ta
    assert "intro_gap" in _codes(_book(intro="Bir. Ikki. Uch."))
    assert "intro_soz" in _codes(_book(intro=" ".join(["so'z"] * 21) + "."))
    long_say = copy.deepcopy(base)
    long_say["units"][0]["lessons"][0]["items"][0]["say"] = "Wash your hands now!"
    assert "say_uzun" in _codes(long_say)


def test_detects_empty_duplicate_and_unsafe():
    b = _book()
    it = b["units"][0]["lessons"][0]["items"]
    it[1]["say"] = "Cat!"                                                  # takror (katta harf, belgi farqi hisobga olinmaydi)
    it[0]["action"] = ""
    codes = _codes(b)
    assert {"takror_element", "bosh_maydon"} <= codes
    b = _book()
    b["units"][0]["lessons"][0]["items"][0]["action"] = "Pichoqni ol!"
    assert "xavfli" in _codes(b)
    b["units"][0]["lessons"][0]["items"][0]["action"] = "Shamni puflaganday qil!"   # o'xshatib — xavfsiz
    assert "xavfli" not in _codes(b)


def test_detects_letters_rom_and_spelling():
    b = _book()
    b["units"][0]["lessons"][0]["items"][0]["say"] = "A"
    assert "harf_oqish" in _codes(b, group="2-3")
    assert "harf_oqish" not in _codes(b, group="6-7")                      # 6-7 yoshda harfga kirish mumkin
    ru = _book()
    ru["units"][0]["lessons"][0]["items"][0].update(say="кот", rom="кот")
    ru["units"][0]["lessons"][0]["items"][1].update(say="собака")         # rom yo'q
    assert "rom" in _codes(ru, lang="ru")
    b = _book()
    b["units"][0]["lessons"][0]["items"][0]["uz"] = "o‘rdak"               # noto'g'ri tutuq belgisi
    assert "imlo" in _codes(b)


def test_sentence_counter():
    assert len(sentences("Salom, do'stim! Uzoq yurt bolalari qanday salomlashadi?")) == 2
    assert len(sentences("Bugun inglizcha «qila olasanmi?» deb so'rashni o'rganamiz.")) == 1
    assert len(sentences("[en]Thank you![/en] — rahmat, esingdami? Bugun yana.")) == 2
    assert len(sentences("ピピッ！「どうぶつえんは どこ？」と きいているよ。")) == 2
    assert len(words("[en]Good morning![/en] Salom!")) == 3


def test_report_is_written(tmp_path, result):
    out = write_report(result, tmp_path / "r.md")
    text = out.read_text(encoding="utf-8")
    for part in ("## Qoidalar", "## Natija", "## Qolgan xatolar", "## O'zgarishlar jurnali", "## Mazmun tekshiruvi"):
        assert part in text
    shipped = (REPO / "docs" / "BOGCHA_AUDIT_REV324.md").read_text(encoding="utf-8")
    assert "Yo'q — hamma fayl qoidalardan o'tdi" in shipped

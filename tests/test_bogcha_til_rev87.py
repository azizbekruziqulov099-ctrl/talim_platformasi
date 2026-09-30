"""REV87: ingliz tili bog'cha kitoblari — immersiya pog'onalari, hayotiy vaziyatlar, yoshlararo takror, rasmlar."""
import json
import re
from pathlib import Path

import pytest

from tools.bogcha_spiral import BookError, build_book, merge_enrich

ROOT = Path(__file__).resolve().parents[1] / "tools" / "bogcha_content"
AGES = ["34", "45", "56", "67"]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def books():
    out, prev = {}, None
    for a in AGES:
        cur = load(f"en_{a}.json")
        out[a] = build_book(cur, load(f"en_{a}_enrich.json"), prev)
        prev = cur
    return out


def outside_tags(text):
    return re.sub(r"\[en\].*?\[/en\]", "", text, flags=re.S).strip()


def test_enrich_files_cover_every_lesson_and_unit():
    for a in ("56", "67"):
        base, enr = load(f"en_{a}.json"), load(f"en_{a}_enrich.json")
        for unit in base["units"]:
            for les in unit["lessons"]:
                e = enr["lessons"][les["name"]]
                assert e["intro_en"]
                assert all(e["items"][it["say"]]["sentence"] for it in les["items"])
    for a in AGES:
        assert sorted(s["unit"] for s in load(f"en_{a}_enrich.json")["scenarios"]) == list(range(1, 9))


def test_immersion_levels_grow_with_age(books):
    assert [books[a]["immersion"] for a in AGES] == [1, 2, 3, 4]
    # 3–4 yosh: tushuntirish o'zbekcha
    first = next(t for t in books["34"]["topics"] if t["name"] not in ("O'tgan yilni eslaymiz",))
    concept = next(r for r in first["rows"] if r["turi"] == "tushuncha")
    assert outside_tags(concept["matn"])
    # 6–7 yosh, 2-bo'limdan boshlab: yangi so'z tushuntirishi TO'LIQ inglizcha, o'zbekcha faqat «Tushunmadim»da
    unit2 = [t for t in books["67"]["topics"][6:20] if "takror" not in t["name"] and not t.get("image_scene")]
    rows = [r for t in unit2 for r in t["rows"] if r["turi"] == "tushuncha" and not r["sarlavha"].startswith("🔁")]
    assert rows and all(outside_tags(r["matn"]) == "" for r in rows)
    assert all(r["sodda"] for r in rows)  # o'zbekcha yordam «Tushunmadim» tugmasida
    # 4–5 yosh: o'zbekcha ichida inglizcha sinf buyruqlari
    concepts45 = [r["matn"] for t in books["45"]["topics"] for r in t["rows"] if r["turi"] == "tushuncha"]
    assert any("[en]Look![/en]" in m or "[en]Listen" in m for m in concepts45)


def test_scenarios_previous_year_and_images(books):
    for a in AGES:
        topics = books[a]["topics"]
        scenes = [t for t in topics if t.get("image_scene")]
        assert len(scenes) == 8
        for t in scenes:
            assert any(r["turi"] == "topshiriq" and "🎭" in r["sarlavha"] for r in t["rows"])
            assert sum(r["turi"] == "test" for r in t["rows"]) >= 2
        assert sum(1 for t in topics for r in t["rows"] if r.get("rasm")) > 100
    assert books["34"]["topics"][0]["name"] != "O'tgan yilni eslaymiz"
    for a in AGES[1:]:
        assert books[a]["topics"][0]["name"] == "O'tgan yilni eslaymiz"


def test_validation_rejects_bad_scenario():
    cur = load("en_34.json")
    enr = load("en_34_enrich.json")
    enr["scenarios"][0]["dialog"][0]["who"] = 5
    with pytest.raises(BookError):
        build_book(cur, enr)
    merged = merge_enrich(load("en_56.json"), load("en_56_enrich.json"))
    it = merged["units"][0]["lessons"][0]["items"][0]
    assert it.get("sentence")

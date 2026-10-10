from pathlib import Path

from modules.curriculum_scope import canonical_grade, normalize_scope, preschool_group, preschool_learner
from modules.dars_xonasi import filled_options

ROOT = Path(__file__).resolve().parents[1]


def test_preschool_groups_are_recognized_without_touching_school_grades():
    # REV97: faqat 2-3, 4-5, 6-7 yosh; eski 3-4/5-6 import qilinmaydi, eski profil esa yangisiga o'qiladi.
    assert preschool_group("4-5") == "4-5 yosh"
    assert preschool_group("2–3 yosh") == "2-3 yosh"
    assert preschool_group("3-4 yosh") == ""
    assert preschool_group("3-4 yosh", legacy=True) == "2-3 yosh"
    assert preschool_group("bogcha-6-7") == "6-7 yosh"
    assert preschool_group("4-6 yosh") == ""
    assert canonical_grade("5-6 yosh") == "5-6 yosh"
    assert canonical_grade("5-6") == "5-6"  # maktab qiymati o'zgarmaydi
    assert canonical_grade("2 kurs") == "2 kurs"
    assert preschool_learner({"kabutar_learning_profile": {"role": "bogcha", "age_group": "3-4 yosh"}}) == "2-3 yosh"
    assert preschool_learner({"kabutar_learning_profile": {"role": "bogcha", "age_group": "6-7 yosh"}}) == "6-7 yosh"
    assert preschool_learner({"kabutar_learning_profile": {"role": "oquvchi"}, "class": "3-4 yosh"}) == ""


def test_common_kindergarten_scope():
    s = normalize_scope({"institution_type": "bogcha", "institution_id": 0})
    assert s["scope_key"] == "kindergarten-common"
    try:
        normalize_scope({"institution_type": "markaz", "institution_id": 0})
    except ValueError:
        pass
    else:
        raise AssertionError("markaz uchun umumiy katalog yo'q")
    sql = (ROOT / "migrations/20260929_preschool.sql").read_text(encoding="utf-8")
    assert "kindergarten-common" in sql and "institution_type IN ('universitet','bogcha')" in sql


def test_two_or_three_option_tests_are_kept():
    assert filled_options(["🐱 cat", "🐶 dog", "", ""]) == ["🐱 cat", "🐶 dog"]
    assert filled_options(["a", "", "c", ""]) == []
    assert filled_options(["a", "", "", ""]) == []


def test_ai_miya_accepts_two_option_tests():
    from modules import ai_miya_varoq as v
    src = (ROOT / "modules/ai_miya_varoq.py").read_text(encoding="utf-8")
    assert "2 <= len(options) <= 4" in src
    assert v.parse_options("A) 🐱 cat\nB) 🐶 dog") == ["🐱 cat", "🐶 dog"]


def test_quick_start_and_education_know_bogcha():
    src = (ROOT / "kabutar_auth.py").read_text(encoding="utf-8")
    assert "'bogcha': 'Bog‘cha bolasi'" in src
    assert "Bolaning yosh guruhini tanlang" in src

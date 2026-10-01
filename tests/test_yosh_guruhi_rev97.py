from datetime import date

from modules.curriculum_scope import preschool_group_for_age
from modules.miya_tarkibi import legacy_of, new_group, subject_key


def test_old_groups_move_to_new_ones():
    assert legacy_of("3-4 yosh") == "3-4 yosh" and legacy_of("5–6 yosh") == "5-6 yosh"
    assert legacy_of("4-5 yosh") == "" and legacy_of("3-4 yosh-01-01") == "3-4 yosh"
    assert new_group("3-4 yosh") == "2-3 yosh"
    assert new_group("5-6 yosh") == "4-5 yosh"
    today = date(2026, 10, 1)
    assert new_group("3-4 yosh", date(2022, 5, 1), today) == "4-5 yosh"   # 4 yosh
    assert new_group("5-6 yosh", date(2020, 3, 1), today) == "6-7 yosh"   # 6 yosh
    assert new_group("3-4 yosh", date(2023, 9, 1), today) == "2-3 yosh"   # 3 yosh


def test_age_buckets_and_subject_key():
    assert [preschool_group_for_age(a) for a in (2, 3, 4, 5, 6, 7, 1, 10, None)] == \
        ["2-3 yosh", "2-3 yosh", "4-5 yosh", "4-5 yosh", "6-7 yosh", "6-7 yosh", "", "", ""]
    assert subject_key("ATROF-MUHIT") == subject_key("Atrof-muhit")
    assert subject_key("O‘qish  savodxonligi") == subject_key("o'qish savodxonligi")

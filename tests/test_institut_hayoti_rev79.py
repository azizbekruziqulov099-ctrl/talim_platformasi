from datetime import date
from pathlib import Path

from modules.institut_hayoti import group_students, sort_dates


def test_students_grouped_by_course_then_group_case_insensitively():
    rows = [
        {"user_id": 1, "full_name": "Karimova Dilnoza", "kurs": 1, "guruh": "101-bt"},
        {"user_id": 2, "full_name": "Aliyev Sardor", "kurs": 1, "guruh": "101-BT"},
        {"user_id": 3, "full_name": "Tursunova Madina", "kurs": 2, "guruh": "201-M"},
        {"user_id": 4, "full_name": "Bekov Ali", "kurs": 1, "guruh": ""},
    ]
    courses = group_students(rows)
    assert [c["kurs"] for c in courses] == [1, 2]
    first = courses[0]
    assert first["soni"] == 3
    assert [g["guruh"] for g in first["guruhlar"]] == ["101-bt", "Guruhsiz"]
    assert [t["full_name"] for t in first["guruhlar"][0]["talabalar"]] == ["Aliyev Sardor", "Karimova Dilnoza"]


def test_upcoming_dates_first_then_past_newest_first():
    today = date(2026, 9, 28)
    rows = [
        {"id": 1, "sana": date(2026, 9, 1), "tugash_sana": None},
        {"id": 2, "sana": date(2026, 12, 25), "tugash_sana": date(2027, 1, 15)},
        {"id": 3, "sana": date(2026, 10, 5), "tugash_sana": None},
        {"id": 4, "sana": date(2026, 9, 20), "tugash_sana": date(2026, 9, 30)},
        {"id": 5, "sana": date(2026, 8, 1), "tugash_sana": None},
    ]
    result = sort_dates(rows, today)
    assert [r["id"] for r in result] == [4, 3, 2, 1, 5]
    assert result[0]["qolgan_kun"] == 0 and not result[0]["otgan"]
    assert result[1]["qolgan_kun"] == 7
    assert result[-1]["otgan"] and result[-1]["qolgan_kun"] is None


def test_quick_start_is_rate_limited_role_checked_and_registered():
    source = Path(__file__).resolve().parents[1].joinpath("kabutar_auth.py").read_text(encoding="utf-8")
    block = source[source.index("def quick_start"):source.index("@app.post('/auth/telegram/code/issue')")]
    assert "service.rate('quick-ip'" in block
    assert "QUICK_ROLE_NAMES" in block and "'admin'" not in block
    assert "_issue_cur(cur,new_id,'quick')" in block
    main = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")
    assert "create_institut_hayoti_router" in main

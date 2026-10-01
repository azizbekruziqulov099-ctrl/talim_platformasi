import pytest
from fastapi import HTTPException

from modules.togarak_jurnal import month_bounds, parse_day, parse_month, summary


def test_summary_counts_partial_and_unpaid():
    rows = [{"tolov_summa": 300000}, {"tolov_summa": 100000}, {"tolov_summa": None}]
    s = summary(rows, 300000)
    assert s == {"azolar": 3, "tolaganlar": 1, "qisman": 1, "qarzdorlar": 2, "kutilgan": 900000, "yigilgan": 400000, "qarz": 500000}
    assert summary([{"tolov_summa": 0}], 0)["tolaganlar"] == 1


def test_month_and_day_parsing():
    assert parse_month("2026-12") == "2026-12"
    first, nxt = month_bounds("2026-12")
    assert (first.isoformat(), nxt.isoformat()) == ("2026-12-01", "2027-01-01")
    assert parse_day("2026-10-01").isoformat() == "2026-10-01"
    for bad in ("2026-13", "26-01", "abc"):
        with pytest.raises(HTTPException):
            parse_month(bad)
    with pytest.raises(HTTPException):
        parse_day("01.10.2026")

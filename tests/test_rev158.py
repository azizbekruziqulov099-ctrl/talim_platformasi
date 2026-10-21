"""REV158: kitob qayta yuklanganda eski nashrning ortiqcha qadamlari yangi dars bilan aralashmaydi;
bog'cha Mavzular fayli o'zi Bog'cha katalogiga yoziladi."""
import datetime as dt
from pathlib import Path

from modules.dars_xonasi import eng_yangi_kitob

ROOT = Path(__file__).resolve().parents[1]


def test_only_latest_book_units_of_topic_remain():
    t0, t1 = dt.datetime(2026, 10, 1), dt.datetime(2026, 10, 21)
    units = [{"unit_code": f"T1#S{i}", "source_code": "OLD", "published_at": t0} for i in range(8, 13)]
    units += [{"unit_code": f"T1#S{i}", "source_code": "NEW", "published_at": t1} for i in range(1, 8)]
    units += [{"unit_code": "T1#V3", "source_code": "OLD", "published_at": t0}, {"unit_code": "boshqa-1", "source_code": "X", "published_at": t0}]
    out = eng_yangi_kitob(units, "T1")
    assert sorted(u["unit_code"] for u in out if u["unit_code"].startswith("T1#")) == [f"T1#S{i}" for i in range(1, 8)]
    assert any(u["unit_code"] == "boshqa-1" for u in out)


def test_publish_archives_old_book_units_of_same_topics_and_paket_cleans_on_skip():
    src = (ROOT / "samtm_platform.py").read_text(encoding="utf-8")
    assert "u.unit_code LIKE u.topic_code || '#%%'" in src
    assert "tozalandi = _ai_brain_eski_nashrni_arxivla(cur, oldin)" in src
    assert "scope_id = _paket_bogcha_scope(content, scope_id)" in src
    assert "ai_brain_unit_code=ANY(%s)" in (ROOT / "modules" / "dars_xonasi.py").read_text(encoding="utf-8")

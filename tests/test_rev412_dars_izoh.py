from datetime import datetime
from modules import dars_izoh as di

def _x(**k):
    d = {"id": 1, "topic_code": "", "dars_nomi": "", "fan": "", "qadam": None, "qadam_turi": "", "qadam_matn": "", "soniya": None, "matn": "", "holat": "yangi", "yaratildi": ""}
    d.update(k); return d

def test_eksport():
    md = di.eksport_matn([_x(matn="Ustoz sekinroq gapirsin"), _x(id=2, topic_code="ENS-001", dars_nomi="1-ma’ruza", qadam=7, qadam_turi="tushuncha", soniya=134, matn="Formula xato", qadam_matn="$P=m/n$")])
    assert "Umumiy izohlar" in md and "Kod: `ENS-001`" in md and "7-qadam (tushuncha) · 02:14: Formula xato" in md and "Doskada" in md
    assert di.vaqt_matn(61) == "01:01"

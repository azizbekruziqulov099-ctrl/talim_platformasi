from io import BytesIO
from pptx import Presentation
from modules.dars_pptx import lesson_pptx

def test_ochiq_dars_pptx():
    lesson = {"topic": {"mavzu": "O‘rin almashtirish", "fan": "Matematika", "sinf": "2 kurs", "topic_code": "T1"},
              "steps": [{"turi": "kirish", "sarlavha": "Kirish", "doska": "Reja", "ovoz": "Salom", "sahna": 1},
                        {"turi": "tushuntirish", "sarlavha": "Uchta narsa", "doska": "ORIN_ALMASH: 3\nQOIDA: $P_n = n!$", "ovoz": "[1] Uchta narsa", "sahna": 2},
                        {"turi": "birga", "sarlavha": "Savol", "doska": "3! = ?", "variantlar": ["6", "3", "9"], "javob": "6", "sahna": 2},
                        {"turi": "amaliy", "sarlavha": "1-namuna", "doska": "5 ta kitob", "javob": "120", "yechim": [{"doska": "$5! = 120$"}], "sahna": 3}],
              "savollar": [{"savol": "$0!$ = ?", "variantlar": ["0", "1"], "togri": 1, "izoh": ""}], "variants": {}}
    prs = Presentation(BytesIO(lesson_pptx(lesson, {})))
    assert len(prs.slides) >= 8
    xml = prs.slides[4]._element.xml   # «Uchta narsa» — doska animatsiyasi bor
    assert "p:timing" in xml and "clickEffect" in xml
    assert any("Uchta narsa" in (s.notes_slide.notes_text_frame.text if s.has_notes_slide else "") for s in prs.slides)

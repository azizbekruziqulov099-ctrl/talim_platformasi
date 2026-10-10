import io
import zipfile

from modules import teacher_library_search as S

DOCS = [
    dict(id=1, nomi="5-sinf matematika nazorat ishi", fayl_nomi="a.docx", polka="Test va nazorat ishlari", qator="Matematika", yaratilgan="2026-01-01"),
    dict(id=2, nomi="Ona tili dars ishlanmasi 7-sinf", fayl_nomi="b.pdf", polka="Dars ishlanmalari", qator="Ona tili va adabiyot", yaratilgan="2026-02-01"),
    dict(id=3, nomi="Yillik hisobot 2025", fayl_nomi="c.pdf", polka="Hisobot va tahlillar", qator="Umumiy", yaratilgan="2026-03-01",
         matn="Fizika fanidan natijalar 87 foiz"),
    dict(id=4, nomi="Buyruq 45", fayl_nomi="d.docx", polka="Rasmiy hujjatlar", qator="Umumiy", yaratilgan="2026-03-02"),
]


def ids(r):
    return [d["id"] for d in r["hujjatlar"]]


def test_typo_tolerant_search_finds_single_doc():
    r = S.assistant_reply("matmatika nazaratni topib ber", DOCS)
    assert r["turi"] == "topildi" and ids(r) == [1]
    assert "Test va nazorat" in r["javob"] and "Matematika" in r["javob"]
    assert ids(S.assistant_reply("ona tli ishlanmasi qani", DOCS)) == [2]
    assert ids(S.assistant_reply("buyrugini top", DOCS)) == [4]
    assert ids(S.assistant_reply("хисобот", DOCS)) == [3]   # kirillcha + x/h


def test_vague_request_asks_to_clarify():
    assert S.assistant_reply("shu hujjatimni top", DOCS)["turi"] == "savol"
    r = S.assistant_reply("pdf", DOCS)
    assert r["turi"] == "tanlash" and set(ids(r)) == {2, 3}


def test_type_filter_and_content_snippet():
    q, res = S.search("fizika word", DOCS)
    assert res == []
    q, res = S.search("fizika natijalari", DOCS)
    assert res[0]["id"] == 3 and "Fizika" in res[0]["parcha"]


def test_not_found_offers_spelling_fix():
    r = S.assistant_reply("zoologiya", DOCS)
    assert r["turi"] == "savol" and not r["hujjatlar"]
    assert "ruxsat" in r["javob"]


def test_classify_shelf_and_row():
    assert S.classify("5-sinf Matematika BSB.docx") == ("Test va nazorat ishlari", "Matematika")
    assert S.classify("Buyruq 45.pdf", "Maktab direktori") == ("Rasmiy hujjatlar", "Umumiy")
    assert S.classify("Algebra 8 sinf dars ishlanmasi.docx") == ("Dars ishlanmalari", "Matematika")
    assert S.classify("IMG_1.jpg")[0] == "Rasmlar"
    assert S.classify("x.pptx", "Present simple english") == ("Taqdimotlar", "Ingliz tili")
    assert S.classify("hujjat.docx", "", ["Olimpiada"])[0] == "Boshqa hujjatlar"
    assert S.classify("Olimpiada 2026 savollari.docx", "", ["Olimpiada"])[0] == "Olimpiada"
    assert S.classify("Ro'yxat 9 sinf.docx") == ("Boshqa hujjatlar", "9-sinf")


def test_extract_docx_text():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:body><w:p><w:r><w:t>Kasrlar &amp; ulushlar</w:t></w:r></w:p></w:body></w:document>")
    assert "Kasrlar & ulushlar" in S.extract_text("a.docx", buf.getvalue())
    assert S.extract_text("a.docx", b"not zip") == ""

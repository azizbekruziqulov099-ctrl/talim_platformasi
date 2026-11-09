import os, shutil, pytest
os.environ.setdefault("JWT_MAXFIY_KALIT", "x" * 40)
from modules import hujjat_aylantir as H

@pytest.mark.skipif(not shutil.which("soffice"), reason="LibreOffice yo'q")
def test_docx_pdf_ga():
    from docx import Document
    import io
    d = Document(); d.add_paragraph("Salom, Kabutar!"); b = io.BytesIO(); d.save(b)
    pdf = H.aylantir_pdf(b.getvalue(), "docx")
    assert pdf[:4] == b"%PDF" and len(pdf) > 500

def test_limit():
    H._IP.clear()
    for _ in range(30): H._limit("1.2.3.4")
    with pytest.raises(Exception): H._limit("1.2.3.4")

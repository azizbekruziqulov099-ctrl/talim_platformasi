import os
os.environ.setdefault("JWT_MAXFIY_KALIT", "x" * 40)
import io, zipfile
import samtm_platform as S

def test_rasmli_miya_zip_turi():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("kitob_2_ai_miya.xlsx", b"PK\x03\x04" + b"0" * 100)
        z.writestr("k1_r001.webp", b"RIFF0000WEBP")
    buf.seek(0)
    assert S._paket_zip_fayllar(buf) is None          # bitta Excel + rasmlar — eski usul
    buf.seek(0)
    assert S._paket_turi(buf.read(), "1-kitob_2_miya.zip") == "miya"

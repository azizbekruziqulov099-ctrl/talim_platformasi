import os, datetime as dt, tempfile
from modules import ombor


def test_imzo_aws_bilan_mos():
    # botocore bilan solishtirib tekshirilgan qiymat (sandboxda, sobit vaqt bilan)
    env = dict(S3_ENDPOINT="https://storage.railway.app", S3_BUCKET="kabutar-media-abc", S3_ACCESS_KEY_ID="AKIDEXAMPLE",
               S3_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY", S3_REGION="auto")
    eski = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        t = dt.datetime(2026, 11, 10, 9, 30, tzinfo=dt.timezone.utc)
        u = ombor.havola("kabutar_tv/2026-11-10/uz 5-sinf.mp4", 3600, vaqt=t)
        assert u.startswith("https://storage.railway.app/kabutar-media-abc/kabutar_tv/2026-11-10/uz%205-sinf.mp4?")
        assert "X-Amz-Signature=" in u and "X-Amz-Expires=3600" in u
    finally:
        for k, v in eski.items():
            os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)


def test_sozlanmagan_bolsa_disk():
    for k in ("S3_ENDPOINT", "S3_BUCKET", "S3_ACCESS_KEY_ID", "S3_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        os.environ.pop(k, None)
    assert not ombor.yoqilgan()
    from modules.kabutar_tv import kanal
    with tempfile.TemporaryDirectory() as d:
        os.environ["KABUTAR_TV_DIR"] = d
        p = os.path.join(d, "2026-11-10", "uz_5-sinf.mp4"); os.makedirs(os.path.dirname(p))
        open(p, "wb").write(b"0123456789")
        r = kanal.fayl_javob(p, "bytes=2-5")
        assert r.status_code == 206
        assert kanal.ombor_kaliti(p) == "kabutar_tv/2026-11-10/uz_5-sinf.mp4"

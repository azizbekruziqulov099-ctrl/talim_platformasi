"""REV468: bulutli ombor (S3 bilan mos: Railway Bucket, Cloudflare R2, AWS S3) — qo'shimcha kutubxonasiz (AWS Signature V4).
Sozlama (Railway Variables): S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_REGION (ixtiyoriy, «auto»).
Sozlanmagan bo'lsa yoqilgan() → False va kod eski usulda (server diskida) ishlayveradi.
Nega kerak: server diskidagi fayllar backend'ni bir nechta nusxada (replika) ishga tushirishga to'sqinlik qiladi."""
import datetime as _dt
import hashlib
import hmac
import os
from urllib.parse import quote, urlsplit

import httpx


def _s(nom, *zaxira):
    for k in (nom, *zaxira):
        v = (os.environ.get(k) or "").strip()
        if v:
            return v
    return ""


def sozlama():
    return {
        "endpoint": _s("S3_ENDPOINT", "AWS_ENDPOINT_URL", "BUCKET_ENDPOINT").rstrip("/"),
        "bucket": _s("S3_BUCKET", "AWS_S3_BUCKET_NAME", "BUCKET_NAME"),
        "key": _s("S3_ACCESS_KEY_ID", "AWS_ACCESS_KEY_ID"),
        "secret": _s("S3_SECRET_ACCESS_KEY", "AWS_SECRET_ACCESS_KEY"),
        "region": _s("S3_REGION", "AWS_DEFAULT_REGION", "AWS_REGION") or "auto",
        "virtual": _s("S3_URL_STYLE").lower() == "virtual",
    }


def yoqilgan():
    c = sozlama()
    return bool(c["endpoint"] and c["bucket"] and c["key"] and c["secret"])


def _hmac(k, m):
    return hmac.new(k, m.encode("utf-8"), hashlib.sha256).digest()


def _url_qism(c, kalit):
    """→ (host, kanonik yo'l, to'liq URL asosi)"""
    u = urlsplit(c["endpoint"])
    kalit_q = quote(kalit.lstrip("/"), safe="/-_.~")
    if c["virtual"]:
        host = f'{c["bucket"]}.{u.netloc}'
        yol = f"/{kalit_q}"
    else:
        host = u.netloc
        yol = f'/{quote(c["bucket"], safe="-_.~")}/{kalit_q}'
    return host, yol, f"{u.scheme}://{host}{yol}"


def _imzo_kaliti(secret, sana, region):
    k = _hmac(("AWS4" + secret).encode("utf-8"), sana)
    k = _hmac(k, region)
    k = _hmac(k, "s3")
    return _hmac(k, "aws4_request")


def _sarlavhali(usul, kalit, body_hash, qoshimcha=None, vaqt=None):
    """Sarlavhalar bilan imzolangan so'rov (PUT/HEAD/DELETE)."""
    c = sozlama()
    vaqt = vaqt or _dt.datetime.now(_dt.timezone.utc)
    amz = vaqt.strftime("%Y%m%dT%H%M%SZ"); sana = vaqt.strftime("%Y%m%d")
    host, yol, url = _url_qism(c, kalit)
    sarl = {"host": host, "x-amz-content-sha256": body_hash, "x-amz-date": amz, **{k.lower(): v for k, v in (qoshimcha or {}).items()}}
    imzolanganlar = ";".join(sorted(sarl))
    kanonik = "\n".join([usul, yol, "", "".join(f"{k}:{str(sarl[k]).strip()}\n" for k in sorted(sarl)), imzolanganlar, body_hash])
    doira = f'{sana}/{c["region"]}/s3/aws4_request'
    sts = "\n".join(["AWS4-HMAC-SHA256", amz, doira, hashlib.sha256(kanonik.encode()).hexdigest()])
    imzo = hmac.new(_imzo_kaliti(c["secret"], sana, c["region"]), sts.encode(), hashlib.sha256).hexdigest()
    sarl["authorization"] = f'AWS4-HMAC-SHA256 Credential={c["key"]}/{doira}, SignedHeaders={imzolanganlar}, Signature={imzo}'
    sarl.pop("host")
    return url, sarl


def yukla(kalit, fayl_yoli, content_type="application/octet-stream", timeout=600):
    """Faylni omborga yuklaydi (katta video ham — oqim bilan). True/False."""
    h = hashlib.sha256()
    with open(fayl_yoli, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    url, sarl = _sarlavhali("PUT", kalit, h.hexdigest(), {"content-type": content_type})
    sarl["content-length"] = str(os.path.getsize(fayl_yoli))
    with open(fayl_yoli, "rb") as f:
        r = httpx.put(url, headers=sarl, content=f, timeout=timeout)
    return r.status_code in (200, 201)


def bormi(kalit, timeout=15):
    url, sarl = _sarlavhali("HEAD", kalit, hashlib.sha256(b"").hexdigest())
    try:
        return httpx.head(url, headers=sarl, timeout=timeout).status_code == 200
    except httpx.HTTPError:
        return False


def ochir(kalit, timeout=15):
    url, sarl = _sarlavhali("DELETE", kalit, hashlib.sha256(b"").hexdigest())
    return httpx.delete(url, headers=sarl, timeout=timeout).status_code in (200, 204)


def havola(kalit, muddat=3600, vaqt=None, qoshimcha_sorov=None):
    """Imzolangan vaqtinchalik GET havola (video to'g'ridan-to'g'ri ombordan yuklanadi, Range so'rovlari bilan)."""
    c = sozlama()
    vaqt = vaqt or _dt.datetime.now(_dt.timezone.utc)
    amz = vaqt.strftime("%Y%m%dT%H%M%SZ"); sana = vaqt.strftime("%Y%m%d")
    host, yol, url = _url_qism(c, kalit)
    doira = f'{sana}/{c["region"]}/s3/aws4_request'
    q = {"X-Amz-Algorithm": "AWS4-HMAC-SHA256", "X-Amz-Credential": f'{c["key"]}/{doira}', "X-Amz-Date": amz,
         "X-Amz-Expires": str(int(muddat)), "X-Amz-SignedHeaders": "host", **(qoshimcha_sorov or {})}
    kanonik_q = "&".join(f"{quote(k, safe='-_.~')}={quote(str(v), safe='-_.~')}" for k, v in sorted(q.items()))
    kanonik = "\n".join(["GET", yol, kanonik_q, f"host:{host}\n", "host", "UNSIGNED-PAYLOAD"])
    sts = "\n".join(["AWS4-HMAC-SHA256", amz, doira, hashlib.sha256(kanonik.encode()).hexdigest()])
    imzo = hmac.new(_imzo_kaliti(c["secret"], sana, c["region"]), sts.encode(), hashlib.sha256).hexdigest()
    return f"{url}?{kanonik_q}&X-Amz-Signature={imzo}"

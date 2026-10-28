"""REV184: LUG'AT MIYASI — bola darsda tushunmagan so'zni bosganda izoh ustozi tushuntiradi.

Manba:
  1) modules/lugat_miyasi_data/<til>.json — barcha AI miyalardan yig'ilgan lug'at (so'z, tarjima uz/ru/en, so'z turkumi,
     3 tagacha misol gap tarjimasi bilan) va har so'z uchun misol gaplar indeksi;
  2) admin yuklagan «Lug'at miyasi» Excel fayli (lugat_miyasi_qoshimcha jadvali) — JSON'dagidan ustun turadi.

Endpointlar:
  GET  /api/lugat/soz?til=en&iz=uz&soz=weather     — bitta so'z
  POST /api/lugat/yukla?token=…  (multipart: fayl)  — admin: Excel'dan qo'shish/yangilash
"""
import io
import json
import os
import re
import threading
from functools import lru_cache

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

DATA = os.path.join(os.path.dirname(__file__), "lugat_miyasi_data")
TILLAR = {"en", "de", "fr", "es", "ru", "ar", "tr", "ko", "ja", "zh"}
IZLAR = {"uz", "ru", "en"}
TURKUMLAR = {"ot", "fe'l", "sifat", "ravish", "son", "olmosh", "predlog", "bog'lovchi", "undov", "ibora", "yuklama"}
ART = {"en": r"(a|an|the)", "de": r"(der|die|das|ein|eine|einen|dem|den)", "fr": r"(le|la|les|un|une|des|l')",
       "es": r"(el|la|los|las|un|una)"}
_lock = threading.Lock()
_qoshimcha = {}   # (til, kalit) -> yozuv (DB'dan, admin yuklagan)
_qoshimcha_tayyor = {"ok": False, "t": 0.0}


def norm(s):
    s = re.sub(r"\[/?[a-z]{2}\]", "", str(s or ""))
    s = re.sub(r"[’`ʻ]", "'", s).strip().lower()
    return re.sub(r"^[^\w]+|[^\w]+$", "", s, flags=re.U)


@lru_cache(maxsize=12)
def yukla(til):
    path = os.path.join(DATA, f"{til}.json")
    if til not in TILLAR or not os.path.exists(path):
        return {"sozlar": {}, "gaplar": [], "indeks": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def variantlar(til, k):
    """Qidiriladigan shakllar: o'zi, artiklsiz, oddiy qo'shimchalarsiz (cats → cat, played → play)."""
    out = [k]
    a = ART.get(til)
    if a:
        m = re.match(r"^" + a + r"\s+|^l'", k)
        if m:
            out.append(k[m.end():])
    if til == "en":
        for suf, rep in (("ies", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e"), ("'s", "")):
            if k.endswith(suf) and len(k) - len(suf) >= 3:
                out.append(k[: -len(suf)] + rep)
    elif til == "de":
        for suf in ("en", "e", "n", "s", "er", "es", "t", "st"):
            if k.endswith(suf) and len(k) - len(suf) >= 3:
                out.append(k[: -len(suf)])
    elif til in ("fr", "es"):
        for suf in ("es", "s", "x", "e"):
            if k.endswith(suf) and len(k) - len(suf) >= 3:
                out.append(k[: -len(suf)])
    elif til == "ru":
        for suf in ("ами", "ями", "ого", "его", "ому", "ему", "ой", "ей", "ую", "юю", "ая", "яя", "ые", "ие", "ов", "ев", "ам", "ям",
                    "ах", "ях", "ы", "и", "а", "я", "у", "ю", "е", "ом", "ем"):
            if k.endswith(suf) and len(k) - len(suf) >= 3:
                out.append(k[: -len(suf)])
                out.append(k[: -len(suf)] + "а")
                out.append(k[: -len(suf)] + "ь")
    seen, res = set(), []
    for x in out:
        if x and x not in seen:
            seen.add(x)
            res.append(x)
    return res


def _gap(d, i, iz):
    g = d["gaplar"][i] if 0 <= i < len(d["gaplar"]) else None
    if not g:
        return None
    return {"gap": g[0], "tarjima": (g[1] or {}).get(iz, "")}


def topish(til, iz, soz, qoshimcha=None):
    qoshimcha = qoshimcha if qoshimcha is not None else _qoshimcha
    k = norm(soz)
    if not k or til not in TILLAR:
        return {"topildi": False, "soz": soz}
    iz = iz if iz in IZLAR else "uz"
    d = yukla(til)
    for v in variantlar(til, k):
        q = qoshimcha.get((til, v))
        if q:
            return {"topildi": True, "soz": q["soz"], "tarjima": q["tarjima"].get(iz) or next(iter(q["tarjima"].values()), ""),
                    "turkum": q.get("turkum", ""), "emoji": q.get("emoji", ""), "daraja": q.get("daraja", ""),
                    "misollar": [{"gap": m.get("gap", ""), "tarjima": (m.get("tarjima") or {}).get(iz, "")} for m in q.get("misollar", [])][:4]}
        e = d["sozlar"].get(v)
        if e and "r" in e:
            e = d["sozlar"].get(e["r"])
        if e:
            tr = e.get("t", {})
            return {"topildi": True, "soz": e.get("s", soz), "tarjima": tr.get(iz) or tr.get("uz") or tr.get("en") or "",
                    "turkum": e.get("k", ""), "emoji": e.get("e", ""), "daraja": e.get("d", ""),
                    "misollar": [g for g in (_gap(d, i, iz) for i in e.get("m", [])) if g][:4]}
    # lug'atda yo'q — hech bo'lmasa shu so'z ishlatilgan gaplar (bola ma'noni kontekstdan tushunadi)
    for v in variantlar(til, k):
        ids = d["indeks"].get(v)
        if ids:
            return {"topildi": False, "soz": soz, "tarjima": "", "turkum": "", "emoji": "",
                    "misollar": [g for g in (_gap(d, i, iz) for i in ids) if g][:3]}
    return {"topildi": False, "soz": soz, "tarjima": "", "turkum": "", "misollar": []}


# ───────────── Excel (admin) ─────────────
USTUNLAR = ["til", "soz", "turkum", "tarjima_uz", "tarjima_ru", "tarjima_en",
            "misol1", "misol1_uz", "misol1_ru", "misol1_en", "misol2", "misol2_uz", "misol2_ru", "misol2_en",
            "misol3", "misol3_uz", "misol3_ru", "misol3_en", "daraja", "emoji"]


def excel_oqi(data):
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    ws = wb["LUGAT"] if "LUGAT" in wb.sheetnames else wb.worksheets[0]
    out, xato = [], []
    for n, r in enumerate(ws.iter_rows(min_row=3, values_only=True), start=3):
        r = list(r) + [None] * len(USTUNLAR)
        row = {k: str(r[i]).strip() if r[i] is not None else "" for i, k in enumerate(USTUNLAR)}
        if not row["soz"]:
            continue
        til = row["til"].lower()
        if til not in TILLAR:
            xato.append(f"{n}-qator: til noto'g'ri ({row['til']})")
            continue
        tarjima = {iz: row[f"tarjima_{iz}"] for iz in IZLAR if row[f"tarjima_{iz}"]}
        if not tarjima:
            xato.append(f"{n}-qator: tarjima yo'q")
            continue
        turkum = row["turkum"].lower().replace("’", "'")
        misollar = []
        for j in (1, 2, 3):
            if row[f"misol{j}"]:
                misollar.append({"gap": row[f"misol{j}"], "tarjima": {iz: row[f"misol{j}_{iz}"] for iz in IZLAR if row[f"misol{j}_{iz}"]}})
        out.append({"til": til, "kalit": norm(row["soz"]), "soz": row["soz"], "turkum": turkum if turkum in TURKUMLAR else "",
                    "tarjima": tarjima, "misollar": misollar, "daraja": row["daraja"], "emoji": row["emoji"]})
    return out, xato


def saqla(cur, qatorlar):
    """Excel'dan o'qilgan so'zlarni bazaga yozadi va shu jarayon xotirasini yangilaydi (boshqa workerlar — keyingi so'rovda)."""
    cur.execute("""CREATE TABLE IF NOT EXISTS lugat_miyasi_qoshimcha(
        til VARCHAR(4) NOT NULL, kalit VARCHAR(120) NOT NULL, yozuv JSONB NOT NULL,
        yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(til, kalit))""")
    for q in qatorlar:
        cur.execute("""INSERT INTO lugat_miyasi_qoshimcha(til,kalit,yozuv) VALUES(%s,%s,%s::jsonb)
                       ON CONFLICT(til,kalit) DO UPDATE SET yozuv=EXCLUDED.yozuv, yangilangan=NOW()""",
                    (q["til"], q["kalit"][:120], json.dumps(q, ensure_ascii=False)))
    with _lock:
        for q in qatorlar:
            _qoshimcha[(q["til"], q["kalit"])] = q
    _qoshimcha_tayyor["ok"] = False   # keyingi so'rovda bazadan qayta o'qiladi


def create_lugat_router(check_admin, db):
    router = APIRouter(prefix="/api/lugat", tags=["lugat-miyasi"])

    def jadval(cur):
        cur.execute("""CREATE TABLE IF NOT EXISTS lugat_miyasi_qoshimcha(
            til VARCHAR(4) NOT NULL, kalit VARCHAR(120) NOT NULL, yozuv JSONB NOT NULL,
            yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(til, kalit))""")

    def qoshimcha_yukla():
        import time as _t
        if _qoshimcha_tayyor["ok"] and _t.time() - _qoshimcha_tayyor["t"] < 600:   # 10 daqiqada bir yangilanadi (boshqa workerlar ham)
            return
        with _lock:
            if _qoshimcha_tayyor["ok"] and _t.time() - _qoshimcha_tayyor["t"] < 600:
                return
            try:
                conn = db()
                cur = conn.cursor()
                try:
                    jadval(cur)
                    conn.commit()
                    cur.execute("SELECT til, kalit, yozuv FROM lugat_miyasi_qoshimcha")
                    for row in cur.fetchall():
                        y = row["yozuv"] if isinstance(row["yozuv"], dict) else json.loads(row["yozuv"])
                        _qoshimcha[(row["til"], row["kalit"])] = y
                finally:
                    cur.close()
                    conn.close()
            except Exception:
                return   # baza band bo'lsa — JSON lug'at bilan ishlaymiz, keyingi so'rovda qayta urinamiz
            _qoshimcha_tayyor["ok"] = True
            _qoshimcha_tayyor["t"] = _t.time()

    @router.get("/soz")
    def soz(til: str = Query(..., max_length=4), iz: str = Query("uz", max_length=4), soz: str = Query(..., max_length=80)):
        qoshimcha_yukla()
        natija = topish(til.lower(), iz.lower(), soz)
        return JSONResponse(natija, headers={"Cache-Control": "public, max-age=86400"})

    @router.post("/yukla")
    async def yukla_excel(token: str = Query(...), fayl: UploadFile = File(...)):
        check_admin(token)
        data = await fayl.read()
        if len(data) > 15 * 1024 * 1024:
            raise HTTPException(413, "Fayl juda katta (15 MB gacha)")
        try:
            qatorlar, xato = excel_oqi(data)
        except Exception as e:
            raise HTTPException(422, f"Excel o'qilmadi: {e}")
        conn = db()
        cur = conn.cursor()
        try:
            saqla(cur, qatorlar)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()
        return {"qoshildi": len(qatorlar), "xatolar": xato[:50]}

    return router

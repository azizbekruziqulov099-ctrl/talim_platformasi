"""REV473: Kabutar chat fayllari bazada (BYTEA) emas, bulutli omborda. Baza shishmaydi, fayllar to'g'ridan-to'g'ri
ombordan beriladi (backend band bo'lmaydi). Xavfsizlik avvalgidek: fayl turi ICHIDAN aniqlanadi (xavfsiz_fayl);
HTML va boshqa xavfli turlar brauzerda OCHILMAYDI — imzolangan havola «yuklab olish» sarlavhasi bilan beriladi.
Bazada: fayl_yol = 's3:chat/<id>/<nom>', fayl_meta = {"ct": tur, "inline": bool}."""
import json
import re
import threading
import time
from urllib.parse import quote

from modules import ombor


def xavfsiz_sarlavha(data, nom, saqlangan_tur):
    """xavfsiz_fayl.chat_javob bilan bir xil qaror: (content_type, inline)."""
    from platform_core import xavfsiz_fayl as X
    ct = (saqlangan_tur or "").split(";")[0].strip().lower()
    if ct in X._MEDIA and X._media_sehr(data):
        return ct, True
    tur = X._sehrli_tur(data)
    if tur in X.INLINE and tur == X.tur_nomdan(nom):
        return X.MIME.get(tur, "application/octet-stream"), True
    return "application/octet-stream", False


def kalit(xid, nom):
    toza = re.sub(r"[^A-Za-z0-9._-]+", "_", str(nom or "fayl"))[:80] or "fayl"
    return f"chat/{int(xid)}/{toza}"


def saqla(cur, xid, data, nom, saqlangan_tur):
    """Baytlarni omborga yuklab, qatorni yangilaydi. Muvaffaqiyatli bo'lsa True (fayl_malumot tozalanadi)."""
    if not ombor.yoqilgan() or not data:
        return False
    ct, inline = xavfsiz_sarlavha(bytes(data), nom, saqlangan_tur)
    k = kalit(xid, nom)
    if not ombor.yukla_bayt(k, data, ct):
        return False
    cur.execute("UPDATE chat_xabarlari SET fayl_yol=%s, fayl_meta=%s::jsonb, fayl_malumot=NULL WHERE id=%s",
                (f"s3:{k}", json.dumps({"ct": ct, "inline": inline}), xid))
    return True


def havola(fayl_yol, meta, nom, muddat=3600):
    m = meta if isinstance(meta, dict) else (json.loads(meta) if meta else {})
    ct = m.get("ct") or "application/octet-stream"
    rejim = "inline" if m.get("inline") else "attachment"
    ascii_nom = re.sub(r"[^A-Za-z0-9._-]+", "_", nom or "fayl") or "fayl"
    return ombor.havola(fayl_yol[3:], muddat, qoshimcha_sorov={
        "response-content-type": ct,
        "response-content-disposition": f"{rejim}; filename=\"{ascii_nom}\"; filename*=UTF-8''{quote(nom or 'fayl', safe='')}",
        "response-cache-control": "private, max-age=3000"})


def ustunlar(cur):
    cur.execute("SET lock_timeout = '5s'")
    cur.execute("ALTER TABLE chat_xabarlari ADD COLUMN IF NOT EXISTS fayl_yol TEXT")
    cur.execute("ALTER TABLE chat_xabarlari ADD COLUMN IF NOT EXISTS fayl_meta JSONB")


def kochir(db_url, log=print):
    """Bazadagi eski fayllarni omborga ko'chiradi (fonda, 20 tadan; bir nechta nusxada — faqat bittasi)."""
    if not ombor.yoqilgan():
        return
    import psycopg2
    from psycopg2.extras import RealDictCursor
    time.sleep(90)   # server ishga tushib olsin
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor, application_name="samtm-chat-ombor")
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT pg_try_advisory_lock(473473473) AS ok")
        if not cur.fetchone()["ok"]:
            conn.close(); return
        ustunlar(cur)
        cur.execute("RESET lock_timeout")
    except Exception as exc:   # noqa: BLE001
        log(f"[chat-ombor] boshlanmadi: {exc}"); return
    jami = xato = 0
    while True:
        try:
            cur.execute("""SELECT id, fayl_malumot, fayl_nomi, fayl_content_turi FROM chat_xabarlari
                           WHERE fayl_malumot IS NOT NULL AND COALESCE(ochirilgan,FALSE)=FALSE ORDER BY id LIMIT 20""")
            qatorlar = cur.fetchall()
            if not qatorlar:
                break
            for r in qatorlar:
                if saqla(cur, r["id"], bytes(r["fayl_malumot"]), r["fayl_nomi"] or "fayl", r["fayl_content_turi"]):
                    jami += 1
                else:
                    xato += 1
                    cur.execute("UPDATE chat_xabarlari SET fayl_meta=COALESCE(fayl_meta,'{}'::jsonb) WHERE id=%s", (r["id"],))
            if xato > 50:
                log("[chat-ombor] juda ko'p xato — to'xtatildi"); break
            if jami and jami % 200 == 0:
                log(f"[chat-ombor] {jami} ta fayl ko'chdi")
            time.sleep(0.3)   # bazaga yuk tushmasin
        except Exception as exc:   # noqa: BLE001
            log(f"[chat-ombor] xato: {exc}"); time.sleep(30); xato += 1
            if xato > 50:
                break
    log(f"[chat-ombor] tugadi: {jami} ta fayl omborga ko'chdi, xato {xato}")
    try:
        conn.close()
    except Exception:   # noqa: BLE001
        pass


def fonda_boshla(db_url):
    threading.Thread(target=kochir, args=(db_url,), name="chat-ombor", daemon=True).start()

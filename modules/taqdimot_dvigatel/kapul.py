"""KAPUL — platformaning ichki hisob birligi (o'qituvchi hamyoni).

1 kapul = 1000 so'm. Yangi hamyon ochilganda 10 kapul sovg'a beriladi.
Narxlar: PPT — 10 slayd = 1 kapul (yuqoriga yaxlitlanadi); ochiq dars (AI) — 1 kapul.

Hamma amal bitta tranzaksiyada (kursor orqali) bajariladi:
  yech()   — balans yetarli bo'lsagina ayiradi (UPDATE ... WHERE balans >= n), jurnalga yozadi;
  qaytar() — xato bo'lsa yechilganni bir marta qaytaradi (jurnal `ref` bo'yicha takrorlanmaydi);
  qosh()   — to'lov/sovg'a qo'shadi (ref bo'yicha takror qo'shilmaydi).
Jurnal (kapul_jurnal) hech qachon o'chirilmaydi: har tiyinga hisob bor.
"""
from __future__ import annotations

from fastapi import HTTPException

SOM = 1000                 # 1 kapul = 1000 so'm
SOVGA = 10                 # yangi hamyonga beriladigan kapul
SLAYD_KAPULGA = 10        # 1 kapul = 10 slayd (yuqoriga yaxlitlanadi)
NARX = {"ppt_10_slayd": 1, "ochiq_dars": 1}


def ppt_narx(slayd_soni):
    n = max(1, int(slayd_soni or 0))
    return -(-n // SLAYD_KAPULGA) * NARX["ppt_10_slayd"]

NO_STORE = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS kapul_hamyon (
    owner_id BIGINT PRIMARY KEY,
    balans INT NOT NULL DEFAULT 0 CHECK (balans >= 0),
    yaratildi TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS kapul_jurnal (
    id BIGSERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    delta INT NOT NULL,
    sabab TEXT NOT NULL,
    ref TEXT,
    balans_keyin INT NOT NULL,
    vaqt TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS kapul_jurnal_ref ON kapul_jurnal(owner_id, ref, sabab) WHERE ref IS NOT NULL;
CREATE INDEX IF NOT EXISTS kapul_jurnal_owner ON kapul_jurnal(owner_id, id DESC);
"""


def _yoz(cur, uid, delta, sabab, ref, balans):
    cur.execute("INSERT INTO kapul_jurnal(owner_id, delta, sabab, ref, balans_keyin) VALUES(%s,%s,%s,%s,%s)",
                (uid, delta, sabab, ref, balans))


def hamyon(cur, uid):
    """Hamyonni qaytaradi (balans); yo'q bo'lsa 50 kapul sovg'a bilan ochadi."""
    cur.execute("SELECT balans FROM kapul_hamyon WHERE owner_id=%s", (uid,))
    r = cur.fetchone()
    if r:
        return int(r["balans"])
    cur.execute("INSERT INTO kapul_hamyon(owner_id, balans) VALUES(%s,%s) ON CONFLICT (owner_id) DO NOTHING RETURNING balans",
                (uid, SOVGA))
    r = cur.fetchone()
    if r:
        _yoz(cur, uid, SOVGA, "sovga", "start", SOVGA)
        return int(r["balans"])
    cur.execute("SELECT balans FROM kapul_hamyon WHERE owner_id=%s", (uid,))
    return int(cur.fetchone()["balans"])


def yech(cur, uid, n, sabab, ref):
    """n kapul ayiradi. Yetmasa — 402. Qaytadi: yangi balans."""
    n = int(n)
    if n <= 0:
        return hamyon(cur, uid)
    bor = hamyon(cur, uid)
    cur.execute("UPDATE kapul_hamyon SET balans = balans - %s WHERE owner_id=%s AND balans >= %s RETURNING balans", (n, uid, n))
    r = cur.fetchone()
    if not r:
        raise HTTPException(status_code=402, headers=NO_STORE,
                            detail=f"Kapul yetarli emas: kerak {n}, hisobingizda {bor}. 1 kapul = {SOM} so'm.")
    _yoz(cur, uid, -n, sabab, ref, int(r["balans"]))
    return int(r["balans"])


def qaytar(cur, uid, n, sabab, ref):
    """Xato bo'lgan ish uchun yechilgan kapulni bir marta qaytaradi."""
    n = int(n)
    if n <= 0:
        return
    cur.execute("SELECT 1 FROM kapul_jurnal WHERE owner_id=%s AND ref=%s AND sabab=%s", (uid, ref, "qaytarildi:" + sabab))
    if cur.fetchone():
        return
    cur.execute("SELECT 1 FROM kapul_jurnal WHERE owner_id=%s AND ref=%s AND sabab=%s", (uid, ref, sabab))
    if not cur.fetchone():
        return          # yechilmagan — qaytarish ham yo'q
    cur.execute("UPDATE kapul_hamyon SET balans = balans + %s WHERE owner_id=%s RETURNING balans", (n, uid))
    r = cur.fetchone()
    if r:
        _yoz(cur, uid, n, "qaytarildi:" + sabab, ref, int(r["balans"]))


def qosh(cur, uid, n, sabab, ref):
    """n kapul qo'shadi (to'lov, sovg'a). Bir xil ref ikki marta qo'shilmaydi."""
    n = int(n)
    if n <= 0:
        return hamyon(cur, uid)
    hamyon(cur, uid)
    if ref:
        cur.execute("SELECT 1 FROM kapul_jurnal WHERE owner_id=%s AND ref=%s AND sabab=%s", (uid, ref, sabab))
        if cur.fetchone():
            return hamyon(cur, uid)
    cur.execute("UPDATE kapul_hamyon SET balans = balans + %s WHERE owner_id=%s RETURNING balans", (n, uid))
    b = int(cur.fetchone()["balans"])
    _yoz(cur, uid, n, sabab, ref, b)
    return b


def holat(cur, uid, jurnal=20):
    b = hamyon(cur, uid)
    cur.execute("SELECT delta, sabab, balans_keyin, vaqt FROM kapul_jurnal WHERE owner_id=%s ORDER BY id DESC LIMIT %s",
                (uid, max(1, min(100, int(jurnal)))))
    rows = [{"delta": int(r["delta"]), "sabab": r["sabab"], "balans": int(r["balans_keyin"]),
             "vaqt": r["vaqt"].isoformat() if r["vaqt"] else None} for r in cur.fetchall()]
    return {"balans": b, "som": b * SOM, "kapul_som": SOM, "narx": NARX, "jurnal": rows}

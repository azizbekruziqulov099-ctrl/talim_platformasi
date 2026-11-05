"""REV339: bolaning stiker albomi serverda — boshqa qurilmadan kirsa ham yo'qolmaydi, ota-ona ham ko'radi.
Qoidalar frontend (src/kid/stikerAlbom.js) bilan bir xil: har tugagan dars — stiker (6 xil navbat bilan), har 5-da medal,
10-da kubok, 20-da toj; bir dars bir kunda bir marta; haftalik orol — shu haftadagi darslar (5 qism)."""
import json
from datetime import date, timedelta

STIKERLAR = ["stiker_quyon", "stiker_fil", "stiker_dinozavr", "stiker_kaptar", "stiker_raketa", "stiker_gul"]
MUKOFOTLAR = [("toj", 20), ("kubok", 10), ("medal_oltin", 5)]
OROL_QISMLARI = 5


def bosh():
    return {"jami": 0, "sanoq": {}, "berildi": {}, "oxirgi": [], "orollar": 0, "orolHafta": ""}


def hafta_boshi(d: date) -> str:
    return (d - timedelta(days=d.weekday())).isoformat()


def orol_soni(a, d: date) -> int:
    b = hafta_boshi(d); o = (date.fromisoformat(b) + timedelta(days=7)).isoformat()
    return min(OROL_QISMLARI, sum(1 for k in a.get("berildi", {}) if b <= (k.split("|")[1] if "|" in k else "") < o))


def stiker_ber(a, dars_kod: str, d: date):
    """a — albom (dict), o'zgaradi. Qaytaradi: {stiker, mukofot, jami} yoki None (bugun berilgan)."""
    a = {**bosh(), **(a or {})}
    k = f"{dars_kod}|{d.isoformat()}"
    if not dars_kod or k in a["berildi"]:
        return a, None
    a["jami"] += 1
    stiker = STIKERLAR[(a["jami"] - 1) % len(STIKERLAR)]
    mukofot = next((m for m, n in MUKOFOTLAR if a["jami"] % n == 0), None)
    for i in filter(None, [stiker, mukofot]):
        a["sanoq"][i] = int(a["sanoq"].get(i, 0)) + 1
    a["berildi"][k] = 1
    chegara = (d - timedelta(days=60)).isoformat()
    a["berildi"] = {x: 1 for x in a["berildi"] if (x.split("|")[1] if "|" in x else "") >= chegara}
    a["oxirgi"] = ([{"id": stiker, "mukofot": mukofot, "sana": d.isoformat()}] + list(a.get("oxirgi", [])))[:30]
    if orol_soni(a, d) == OROL_QISMLARI and a.get("orolHafta") != hafta_boshi(d):
        a["orollar"] = int(a.get("orollar", 0)) + 1
        a["orolHafta"] = hafta_boshi(d)
    return a, {"stiker": stiker, "mukofot": mukofot, "jami": a["jami"]}


def migrate(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS bola_albom (child_id BIGINT PRIMARY KEY, albom JSON NOT NULL, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")


def ol(cur, child_id):
    cur.execute("SELECT albom FROM bola_albom WHERE child_id=%s", (child_id,))
    r = cur.fetchone()
    v = (r["albom"] if isinstance(r, dict) else r[0]) if r else None
    return {**bosh(), **(json.loads(v) if isinstance(v, str) else (v or {}))}


def saqla(cur, child_id, a):
    cur.execute("""INSERT INTO bola_albom(child_id, albom, yangilandi) VALUES(%s,%s,NOW())
                   ON CONFLICT (child_id) DO UPDATE SET albom=EXCLUDED.albom, yangilandi=NOW()""", (child_id, json.dumps(a, ensure_ascii=False)))

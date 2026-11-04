"""REV329: bola miyasi xaritasi — har o'yin bir yoki bir necha qobiliyatni rivojlantiradi va tekshiradi.
O'yin natijalari (to'g'ri/xato, vaqt) yig'iladi va ota-onaga qobiliyatlar bo'yicha foiz ko'rsatiladi.
Sof qismlar (QOBILIYATLAR, OYIN_QOBILIYAT, hisobla) bazasiz sinaladi."""
from datetime import timedelta

QOBILIYATLAR = [
    ("xotira", "🧠", "Xotira"), ("diqqat", "🎯", "Diqqat"), ("mantiq", "🧩", "Mantiqiy fikrlash"),
    ("fazoviy", "📐", "Fazoviy tasavvur"), ("sanash", "🔢", "Son va sanash"), ("nutq", "🗣️", "Nutq va til"),
    ("eshitish", "👂", "Eshitib idrok qilish"), ("tezlik", "⚡", "Fikrlash tezligi"),
]
QOB_KALIT = [q[0] for q in QOBILIYATLAR]
# o'yin raqami → {qobiliyat: ulush} (ulushlar yig'indisi 1)
OYIN_QOBILIYAT = {
    116: {"eshitish": .6, "nutq": .4}, 117: {"nutq": 1.0}, 83: {"diqqat": .6, "fazoviy": .4},
    89: {"xotira": .8, "diqqat": .2}, 88: {"xotira": .7, "diqqat": .3}, 86: {"mantiq": .8, "diqqat": .2},
    90: {"xotira": .6, "diqqat": .4}, 91: {"mantiq": .7, "nutq": .3}, 32: {"sanash": 1.0}, 31: {"sanash": 1.0},
    35: {"sanash": .6, "mantiq": .4}, 38: {"sanash": .6, "mantiq": .4}, 55: {"mantiq": .6, "diqqat": .4},
    97: {"mantiq": .6, "eshitish": .4}, 33: {"sanash": .6, "xotira": .4},
}
KUTILGAN_SONIYA = {116: 50, 117: 56, 83: 54, 89: 60, 88: 48, 86: 45, 90: 60, 91: 60, 32: 54, 31: 56, 35: 50, 38: 50, 55: 48, 97: 49, 33: 52}
MIN_OYIN = 3   # bir qobiliyat bo'yicha xulosa uchun kamida shuncha o'yin


def hisobla(natijalar):
    """natijalar — [{oyin_id, togri, xato, soniya}]. Qaytaradi: {qobiliyat: {foiz|None, oyin, belgi, nom}} + umumiy."""
    yig = {k: [0.0, 0.0, 0] for k in QOB_KALIT}   # [ball*ulush, ulush, o'yinlar soni]
    tez = [0.0, 0]
    for r in natijalar or []:
        oid = int(r.get("oyin_id") or 0)
        q = OYIN_QOBILIYAT.get(oid)
        if not q:
            continue
        togri, xato = max(0, int(r.get("togri") or 0)), max(0, int(r.get("xato") or 0))
        if togri + xato == 0:
            continue
        ball = togri / (togri + xato)
        for k, u in q.items():
            yig[k][0] += ball * u; yig[k][1] += u; yig[k][2] += 1
        s = int(r.get("soniya") or 0)
        if s > 0 and oid in KUTILGAN_SONIYA:
            tez[0] += max(0.0, min(1.0, KUTILGAN_SONIYA[oid] / s * 0.8)) ; tez[1] += 1
    out = {}
    for k, belgi, nom in QOBILIYATLAR:
        if k == "tezlik":
            n = tez[1]
            out[k] = {"foiz": round(100 * tez[0] / n) if n >= MIN_OYIN else None, "oyin": n, "belgi": belgi, "nom": nom}
            continue
        b, u, n = yig[k]
        out[k] = {"foiz": round(100 * b / u) if n >= MIN_OYIN and u > 0 else None, "oyin": n, "belgi": belgi, "nom": nom}
    bor = [(k, v["foiz"]) for k, v in out.items() if v["foiz"] is not None]
    kuchli = max(bor, key=lambda x: x[1])[0] if bor else ""
    zaif = min(bor, key=lambda x: x[1])[0] if len(bor) > 1 else ""
    return {"qobiliyatlar": out, "jami_oyin": len(natijalar or []), "kuchli": kuchli, "zaif": zaif if zaif != kuchli else ""}


MASLAHAT = {
    "xotira": "Kechqurun bugun nima qilganini 3 ta rasm bilan aytib berishini so'rang.",
    "diqqat": "Ikki rasm orasidagi farqni topish o'yinini birga o'ynang.",
    "mantiq": "«Nima uchun?» savolini ko'proq bering — sababini o'zi topsin.",
    "fazoviy": "Kubiklardan namunaga qarab minora qurdiring.",
    "sanash": "Ovqat paytida qoshiq, non, olmalarni birga sanang.",
    "nutq": "Kitob o'qib, rasm haqida 2–3 gap aytishini so'rang.",
    "eshitish": "Ko'zini yumib, qaysi ovoz eshitilganini toptiring.",
    "tezlik": "Shoshiltirmang — avval to'g'ri, keyin tez. Oddiy o'yinlarni takrorlang.",
}


def migrate(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS bola_oyin_natija (
        id BIGSERIAL PRIMARY KEY, child_id BIGINT NOT NULL, sana DATE NOT NULL, dars_kod TEXT NOT NULL DEFAULT '',
        oyin_id INT NOT NULL, togri INT NOT NULL DEFAULT 0, xato INT NOT NULL DEFAULT 0, soniya INT NOT NULL DEFAULT 0,
        yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE INDEX IF NOT EXISTS bola_oyin_natija_bola ON bola_oyin_natija(child_id, sana)")


def yoz(cur, child_id, day, dars_kod, oyin_id, togri, xato, soniya):
    if int(oyin_id) not in OYIN_QOBILIYAT:
        return False
    cur.execute("""INSERT INTO bola_oyin_natija(child_id, sana, dars_kod, oyin_id, togri, xato, soniya) VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (child_id, day, str(dars_kod or "")[:120], int(oyin_id), max(0, min(50, int(togri))), max(0, min(50, int(xato))),
                 max(0, min(1800, int(soniya)))))
    return True


def xarita(cur, child_id, day, kun=30):
    cur.execute("""SELECT oyin_id, togri, xato, soniya FROM bola_oyin_natija WHERE child_id=%s AND sana > %s""",
                (child_id, day - timedelta(days=kun)))
    out = hisobla([dict(r) for r in cur.fetchall()])
    out["kun"] = kun
    out["maslahat"] = MASLAHAT.get(out["zaif"], "")
    return out

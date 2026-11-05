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
    # REV335: fazoviy tasavvur o'yinlari
    68: {"fazoviy": .6, "diqqat": .4}, 76: {"fazoviy": .7, "nutq": .3}, 103: {"fazoviy": .6, "diqqat": .4},
    93: {"fazoviy": .7, "diqqat": .3}, 106: {"mantiq": .6, "fazoviy": .4}, 114: {"nutq": .5, "mantiq": .5},   # REV336
    61: {"diqqat": .6, "eshitish": .4}, 62: {"mantiq": .5, "diqqat": .5}, 63: {"diqqat": .6, "xotira": .4}, 64: {"mantiq": .7, "xotira": .3},   # REV337
    49: {"sanash": .6, "mantiq": .4}, 57: {"sanash": .7, "fazoviy": .3}, 43: {"sanash": .6, "mantiq": .4}, 59: {"sanash": .5, "eshitish": .3, "mantiq": .2},   # REV338
    149: {"mantiq": .6, "diqqat": .4}, 154: {"mantiq": .6, "diqqat": .4}, 161: {"mantiq": .6, "diqqat": .4}, 162: {"mantiq": .6, "diqqat": .4}, 168: {"mantiq": .6, "diqqat": .4}, 150: {"mantiq": .6, "diqqat": .4}, 96: {"mantiq": .6, "diqqat": .4}, 14: {"mantiq": .6, "diqqat": .4}, 18: {"mantiq": .5, "xotira": .5}, 148: {"mantiq": .6, "xotira": .4}, 94: {"mantiq": .6, "xotira": .4}, 158: {"mantiq": .6, "xotira": .4}, 147: {"mantiq": .6, "xotira": .4}, 95: {"mantiq": .6, "xotira": .4}, 165: {"mantiq": .7, "nutq": .3}, 152: {"mantiq": .6, "xotira": .4}, 146: {"mantiq": .6, "xotira": .4}, 29: {"mantiq": .6, "xotira": .4}, 157: {"mantiq": .6, "xotira": .4}, 153: {"mantiq": .6, "xotira": .4}, 15: {"mantiq": .6, "xotira": .4}, 156: {"mantiq": .6, "xotira": .4}, 166: {"mantiq": .6, "xotira": .4}, 121: {"eshitish": .8, "xotira": .2}, 123: {"eshitish": .8, "xotira": .2}, 142: {"eshitish": .5, "mantiq": .5}, 118: {"nutq": .7, "diqqat": .3}, 120: {"nutq": .6, "eshitish": .4},   # REV348: saralash va ulash; REV349: tartib; REV351: eshitish
}
KUTILGAN_SONIYA = {116: 50, 117: 56, 83: 54, 89: 60, 88: 48, 86: 45, 90: 60, 91: 60, 32: 54, 31: 56, 35: 50, 38: 50, 55: 48, 97: 49, 33: 52, 68: 50, 76: 50, 103: 60, 93: 56, 106: 47, 114: 55, 61: 48, 62: 54, 63: 54, 64: 55, 49: 57, 57: 60, 43: 55, 59: 60, **{i: 54 for i in (149, 154, 161, 162, 168, 150, 96, 14, 18, 148, 94, 158, 147, 95, 165)}, **{i: 50 for i in (152, 146, 29, 157, 153, 15, 156, 166)}, 121: 48, 123: 48, 142: 60, 118: 60, 120: 60}
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


_TAYYOR = False   # REV343: jadval bir marta tekshiriladi (har so'rovda CREATE … IF NOT EXISTS — ko'p odamda katalog qulfi)


def migrate(cur):
    global _TAYYOR
    if _TAYYOR:
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS bola_oyin_natija (
        id BIGSERIAL PRIMARY KEY, child_id BIGINT NOT NULL, sana DATE NOT NULL, dars_kod TEXT NOT NULL DEFAULT '',
        oyin_id INT NOT NULL, togri INT NOT NULL DEFAULT 0, xato INT NOT NULL DEFAULT 0, soniya INT NOT NULL DEFAULT 0,
        yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE INDEX IF NOT EXISTS bola_oyin_natija_bola ON bola_oyin_natija(child_id, sana)")
    try:
        cur.connection.commit()   # jadval darhol saqlansin — keyingi xato uni bekor qilmasin
    except Exception:
        return
    _TAYYOR = True

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

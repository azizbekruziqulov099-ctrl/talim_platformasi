"""REV371: «O‘yinlar xonasi» — bolaning bosqichlari serverda (boshqa qurilmada ham saqlanadi, ota-ona ko‘radi).
Qoida frontend (src/kid/oyinXona/xonaRules.js) bilan bir xil: 1-bosqich doim ochiq; keyingisi oldingisi o‘tilgan va
o‘tilgan kundan keyin yangi kun kelganda ochiladi, hamda faqat obunachilarga. Har bosqich bir marta yoziladi
(qayta o‘ynasa — eng yaxshi yulduz saqlanadi)."""
import json

XONA_OYINLAR = set(range(1, 500))   # REV379: rivojlantiruvchi o'yinlar — katalogdagi hamma o'yinlar (57 xil)
MAX_BOSQICH = 20
_TAYYOR = False


def migrate(cur):
    global _TAYYOR
    if _TAYYOR:
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS bola_oyin_xona (child_id BIGINT PRIMARY KEY, holat JSON NOT NULL, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    try:
        cur.connection.commit()
    except Exception:
        return
    _TAYYOR = True


def ol(cur, child_id):
    cur.execute("SELECT holat FROM bola_oyin_xona WHERE child_id=%s", (child_id,))
    r = cur.fetchone()
    v = (r["holat"] if isinstance(r, dict) else r[0]) if r else None
    return json.loads(v) if isinstance(v, str) else (v or {})


def saqla(cur, child_id, h):
    cur.execute("""INSERT INTO bola_oyin_xona(child_id, holat, yangilandi) VALUES(%s,%s,NOW())
                   ON CONFLICT (child_id) DO UPDATE SET holat=EXCLUDED.holat, yangilandi=NOW()""", (child_id, json.dumps(h, ensure_ascii=False)))


def bosqich_holati(prog, i, obuna, bugun):
    p = prog or {}
    if str(i) in p:
        return "otdi"
    if i == 1:
        return "ochiq"
    old = p.get(str(i - 1))
    if not old:
        return "qulf"
    if not obuna:
        return "obuna"
    return "ochiq" if str(old.get("sana", "")) < bugun else "ertaga"


def otdi(h, oyin, bosqich, yulduz, obuna, bugun, admin=False):
    """h o'zgaradi. Qaytaradi (h, xato) — xato bo'lsa h o'zgarmaydi. REV450: admin — hamma bosqich ochiq (kutish va obunasiz)."""
    oyin, bosqich, yulduz = int(oyin), int(bosqich), max(0, min(3, int(yulduz)))
    if oyin not in XONA_OYINLAR or not 1 <= bosqich <= MAX_BOSQICH:
        return h, "nomalum"
    if yulduz < 1:
        return h, "otmadi"
    prog = dict(h.get(str(oyin)) or {})
    holat = "ochiq" if admin else bosqich_holati(prog, bosqich, obuna, bugun)
    if holat not in ("ochiq", "otdi"):
        return h, holat
    eski = prog.get(str(bosqich))
    if eski:
        eski = {**eski, "yulduz": max(int(eski.get("yulduz", 0)), yulduz)}
        prog[str(bosqich)] = eski
    else:
        prog[str(bosqich)] = {"sana": bugun, "yulduz": yulduz}
    return {**h, str(oyin): prog}, None

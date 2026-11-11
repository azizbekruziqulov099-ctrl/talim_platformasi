"""REV487: «🏠 Bugun» — har rol uchun bosh ekran ma'lumoti (bitta yengil so'rov).
o'quvchi/talaba: davom etayotgan kurslar (oxirgi o'tilgan dars, bugun o'tildimi), ekspeditsiya seriyasi, ko'nikmalar (kuchli/zaif);
o'qituvchi: guruhlari (a'zolar, bugungi dars, bugun dars o'tganlar, ⚠️ nazorat belgilari);
ota-ona: farzandlari (bugun nechta dars, haftada nechta, o'yin qulfi)."""
from typing import Optional

from fastapi import APIRouter, Header, HTTPException


def _sp(cur, sql, args=()):
    try:
        cur.execute("SAVEPOINT bg"); cur.execute(sql, args); r = cur.fetchall(); cur.execute("RELEASE SAVEPOINT bg"); return r
    except Exception:   # noqa: BLE001 — jadval hali bo'lmasa ham ekran ochilsin
        cur.execute("ROLLBACK TO SAVEPOINT bg"); return []


BUGUN = "(NOW() AT TIME ZONE 'Asia/Tashkent')::date"


def oquvchi(cur, uid):
    kurslar = _sp(cur, f"""SELECT kalit, COUNT(*) FILTER (WHERE topic_code NOT LIKE 'NZ:%%') AS otilgan,
                              MAX(tugadi_at) AS oxirgi, BOOL_OR((tugadi_at AT TIME ZONE 'Asia/Tashkent')::date = {BUGUN}) AS bugun
                           FROM kurs_dars_holat WHERE user_id=%s GROUP BY kalit ORDER BY MAX(tugadi_at) DESC LIMIT 6""", (uid,))
    nz = _sp(cur, """SELECT kalit, kod, tur, togri, jami, otdi FROM kurs_nazorat WHERE user_id=%s ORDER BY oxirgi_urinish DESC LIMIT 3""", (uid,))
    eks = _sp(cur, "SELECT kurs, data FROM ekspeditsiya_holat WHERE user_id=%s ORDER BY updated_at DESC LIMIT 1", (uid,))
    kn = _sp(cur, "SELECT konikma, togri, jami FROM konikma_holat WHERE user_id=%s", (uid,))
    try:
        from modules.konikma import korinish
        konikmalar = [k for k in korinish(kn) if k["jami"] >= 5]
    except Exception:   # noqa: BLE001
        konikmalar = []
    konikmalar.sort(key=lambda k: k["foiz"])
    e = eks[0] if eks else None
    seriya = int(((e or {}).get("data") or {}).get("streak") or 0) if e else 0
    return {"rol": "oquvchi",
            "kurslar": [{"kalit": r["kalit"], "otilgan": int(r["otilgan"] or 0), "bugun": bool(r["bugun"]),
                         "oxirgi": r["oxirgi"].isoformat() if r["oxirgi"] else None} for r in kurslar],
            "nazoratlar": [{"kalit": r["kalit"], "kod": r["kod"], "tur": r["tur"], "togri": r["togri"], "jami": r["jami"], "otdi": r["otdi"]} for r in nz],
            "ekspeditsiya": {"kurs": e["kurs"], "seriya": seriya} if e else None,
            "kuchli": konikmalar[-1] if konikmalar else None, "zaif": konikmalar[0] if len(konikmalar) > 1 else None}


def oqituvchi(cur, uid):
    gr = _sp(cur, f"""SELECT g.id, g.nom, g.fan, g.grade, g.bugungi_nom, g.kamera,
                             (SELECT COUNT(*) FROM kurs_guruh_azo a WHERE a.guruh_id=g.id) AS azolar,
                             (SELECT COUNT(DISTINCT h.user_id) FROM kurs_dars_holat h JOIN kurs_guruh_azo a ON a.user_id=h.user_id AND a.guruh_id=g.id
                                WHERE (h.tugadi_at AT TIME ZONE 'Asia/Tashkent')::date = {BUGUN}) AS bugun_otgan,
                             (SELECT COUNT(*) FROM kurs_nazorat n JOIN kurs_guruh_azo a ON a.user_id=n.user_id AND a.guruh_id=g.id
                                WHERE n.oxirgi_urinish > NOW() - INTERVAL '7 days' AND (COALESCE((n.halollik->>'yashirildi')::int,0) > 0
                                  OR COALESCE((n.halollik->>'nusxa')::int,0) > 0 OR n.halollik->>'kamera' = 'rad')) AS diqqat
                      FROM kurs_guruh g WHERE g.egasi=%s AND g.faol ORDER BY g.id DESC LIMIT 12""", (uid,))
    return {"rol": "oqituvchi", "guruhlar": [{"id": r["id"], "nom": r["nom"], "fan": r["fan"], "sinf": r["grade"], "bugungi": r["bugungi_nom"],
                                              "azolar": int(r["azolar"] or 0), "bugun_otgan": int(r["bugun_otgan"] or 0), "diqqat": int(r["diqqat"] or 0)} for r in gr]}


def ota(cur, uid):
    bolalar = _sp(cur, f"""SELECT pc.child_id, COALESCE(NULLIF(u.full_name,''),'Farzand') AS ism,
                                  (SELECT COUNT(*) FROM bola_dars_holat b WHERE b.child_id=pc.child_id AND (b.tugatilgan_at AT TIME ZONE 'Asia/Tashkent')::date = {BUGUN}) AS bugun,
                                  (SELECT COUNT(*) FROM bola_dars_holat b WHERE b.child_id=pc.child_id AND b.tugatilgan_at > NOW() - INTERVAL '7 days') AS hafta
                           FROM parent_child pc JOIN users u ON u.user_id=pc.child_id WHERE pc.parent_id=%s ORDER BY 2""", (uid,))
    out = []
    for b in bolalar:
        ql = _sp(cur, "SELECT gacha FROM nazoratchi_qulf WHERE user_id=%s AND NOT ochildi AND gacha > CURRENT_DATE ORDER BY yaratildi DESC LIMIT 1", (b["child_id"],))
        out.append({"id": b["child_id"], "ism": b["ism"], "bugun": int(b["bugun"] or 0), "hafta": int(b["hafta"] or 0),
                    "qulf": ql[0]["gacha"].isoformat() if ql else None})
    return {"rol": "ota-ona", "bolalar": out}


def create_router(platform):
    router = APIRouter(tags=["bugun"])

    @router.get("/api/bugun")
    def bugun(rol: str = "", token: str = "", authorization: Optional[str] = Header(None)):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        uid = int(platform._jwt_tekshir(t))
        conn = platform._db(); cur = conn.cursor()
        try:
            if rol == "oqituvchi":
                return oqituvchi(cur, uid)
            if rol == "ota-ona":
                return ota(cur, uid)
            return oquvchi(cur, uid)
        finally:
            conn.rollback(); cur.close(); conn.close()

    return router

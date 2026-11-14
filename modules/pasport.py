"""REV560: O'quvchi pasporti — bitta o'quvchi haqida HAQIQIY ma'lumotdan yig'ilgan sahifa (AI kerak emas; Kabu-bot keyin shuni o'qiydi).

Manbalar: mat_bank_javob (matematika banki tarixi), xb_bilim / xb_imtihon / xb_guruh_azo / xb_sinf (xalqaro PISA·TIMSS), users.
Nima ko'rsatiladi: kim, faollik, matematika bo'yicha qamrov va aniqlik, elementar matematika darajasi, mavzular kesimi, NOZIK joylar,
ESDAN CHIQARISH (taxminiy model), xalqaro daraja va guruh, soha va fikrlash ko'nikmalari, qisqa xulosa.
Halollik qoidalari: yetarli ma'lumot bo'lmasa (kam savol) daraja aytilmaydi — «aniqlanmagan»; esdan chiqarish o'lchov emas, TAXMIN ekani yoziladi.

  GET /api/pasport/mening       — o'quvchining o'zi
  GET /api/pasport/{user_id}    — o'zi, ota-onasi, o'qituvchisi (kurs guruhi yoki xalqaro sinf egasi) yoki admin
"""
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

TZ = timezone.utc
# Esdan chiqarish: har to'g'ri javobdan keyin saqlanish barqarorligi kengayadi. S = 1,5 · 2^min(to'g'ri, 6) kun; saqlanish = e^(−kun/S).
BARQAROR_BOSHI = 1.5
MUSTAHKAM = 0.6      # saqlanish shundan yuqori — «mustahkam»
UNUTILGAN = 0.3      # shundan past — «unutilgan»; oralig'i — «takrorlash vaqti»
ISHONCH_ENG_KAM = 15  # daraja aytish uchun kamida shuncha savol ko'rilgan bo'lishi kerak
NOZIK_ENG_KAM = 6     # mavzu «nozik» deyilishi uchun kamida shuncha savol ko'rilgan
NOZIK_CHEGARA = 50    # shu foizdan past (hozirgi holat) — nozik
ELEMENTAR_KITOB = ("1.1", "1.2")   # natural, butun sonlar va kasrlar (1–10-mavzular)


def saqlanish(togri, kun):
    """Taxminiy saqlanish (0…1): oxirgi marta to'g'ri javob berilganiga `kun` kun bo'lgan, jami `togri` marta to'g'ri yechilgan."""
    s = BARQAROR_BOSHI * 2 ** min(max(int(togri or 1), 1), 6)
    return math.exp(-max(float(kun), 0.0) / s)


def savol_holati(oxirgi_togri, togri, kun):
    if not oxirgi_togri:
        return "xato"
    r = saqlanish(togri, kun)
    return "mustahkam" if r >= MUSTAHKAM else ("takror" if r >= UNUTILGAN else "unutilgan")


def daraja_nomi(foiz, n):
    """Hozirgi holat foizi → daraja. Baho (Milliy sertifikat shkalasi) bilan bir xil chegaralar: A+/A — yuqori, B+/B — yaxshi, C+/C — o'rta, C ga yetmasa — past.
    Ma'lumot kam bo'lsa — None (aytilmaydi)."""
    if n < ISHONCH_ENG_KAM:
        return None
    from modules.mat_bank import baho_harfi
    h = baho_harfi(float(foiz))
    return "yuqori" if h in ("A+", "A") else ("yaxshi" if h in ("B+", "B") else ("o‘rta" if h in ("C+", "C") else "past"))


def _kun(hozir, t):
    return max(0.0, (hozir - t).total_seconds() / 86400.0) if t else 9999.0


def mavzu_statistikasi(qatorlar, mavzular, hozir):
    """qatorlar: [{savol_id, mavzu, urinish, togri, oxirgi_togri, yangilangan}], mavzular: {raqam: {nom, kitob, jami}}.
    → [{raqam, nom, kitob, jami, ko_rilgan, hozirgi, aniqlik, holatlar:{…}, nozik}] (faqat ko'rilganlar, raqam bo'yicha)."""
    guruh = {}
    for q in qatorlar:
        guruh.setdefault(int(q["mavzu"]), []).append(q)
    out = []
    for raqam, q in sorted(guruh.items()):
        m = mavzular.get(raqam, {})
        h = {"mustahkam": 0, "takror": 0, "unutilgan": 0, "xato": 0}
        for x in q:
            h[savol_holati(bool(x["oxirgi_togri"]), int(x["togri"]), _kun(hozir, x["yangilangan"]))] += 1
        ko = len(q); hozirgi = round(100 * sum(1 for x in q if x["oxirgi_togri"]) / ko)
        ur = sum(int(x["urinish"]) for x in q); tg = sum(int(x["togri"]) for x in q)
        out.append({"raqam": raqam, "nom": m.get("nom", ""), "kitob": m.get("kitob"), "jami": m.get("jami", 0), "ko_rilgan": ko, "hozirgi": hozirgi,
                    "aniqlik": round(100 * tg / ur) if ur else 0, "holatlar": h, "nozik": ko >= NOZIK_ENG_KAM and hozirgi < NOZIK_CHEGARA})
    return out


def taxminiy_baho(foiz, daraja):
    """Taxminiy baho harfi (Milliy sertifikat shkalasi, foizdan): faqat daraja aytilgan (savol yetarli) bo'lsa; aks holda None."""
    if daraja is None:
        return None
    from modules.mat_bank import baho_harfi
    return baho_harfi(float(foiz))


def matematika_bolimi(qatorlar, mavzular, hozir):
    ms = mavzu_statistikasi(qatorlar, mavzular, hozir)
    ko = len(qatorlar); jami = sum(m.get("jami", 0) for m in mavzular.values())
    h = {"mustahkam": 0, "takror": 0, "unutilgan": 0, "xato": 0}
    for m in ms:
        for k, v in m["holatlar"].items():
            h[k] += v
    hozirgi = round(100 * sum(1 for q in qatorlar if q["oxirgi_togri"]) / ko) if ko else 0
    el = [m for m in ms if m["kitob"] and str(m["kitob"]).startswith(ELEMENTAR_KITOB)]
    el_ko = sum(m["ko_rilgan"] for m in el)
    el_hozirgi = round(sum(m["hozirgi"] * m["ko_rilgan"] for m in el) / el_ko) if el_ko else 0
    nozik = sorted([m for m in ms if m["nozik"]], key=lambda m: (m["hozirgi"], -m["ko_rilgan"]))[:5]
    takror = sorted([m for m in ms if m["holatlar"]["takror"] + m["holatlar"]["unutilgan"] > 0], key=lambda m: -(m["holatlar"]["takror"] + m["holatlar"]["unutilgan"]))[:5]
    return {"ko_rilgan": ko, "jami_savol": jami, "qamrov": round(100 * ko / jami) if jami else 0, "hozirgi": hozirgi, "urinish": sum(int(q["urinish"]) for q in qatorlar),
            "holatlar": h, "daraja": daraja_nomi(hozirgi, ko), "baho": taxminiy_baho(hozirgi, daraja_nomi(hozirgi, ko)),
            "elementar": {"ko_rilgan": el_ko, "jami": sum(m["jami"] for m in el), "hozirgi": el_hozirgi, "daraja": daraja_nomi(el_hozirgi, el_ko), "baho": taxminiy_baho(el_hozirgi, daraja_nomi(el_hozirgi, el_ko)), "ishonchli": el_ko >= ISHONCH_ENG_KAM},
            "mavzular": ms, "nozik": nozik, "takrorlash": takror}


def faollik_bolimi(vaqtlar, hozir):
    """vaqtlar — o'quvchi biror ish qilgan lahzalar (matematika banki, xalqaro mashq va imtihonlar)."""
    kunlar = {t.astimezone(TZ).date() for t in vaqtlar if t}
    bugun = hozir.astimezone(TZ).date()
    return {"oxirgi": max(vaqtlar).isoformat() if vaqtlar else None, "kun_7": sum(1 for k in kunlar if (bugun - k).days < 7),
            "kun_30": sum(1 for k in kunlar if (bugun - k).days < 30), "jami_harakat": len(vaqtlar)}


def xulosa_yoz(p):
    """Pasport ma'lumotidan qisqa, tekshiriladigan gaplar (har gap raqamga tayanadi). Bot buni ohangiga qarab so'zlaydi."""
    g = []
    f = p["faollik"]; m = p["matematika"]; x = p["xalqaro"]
    if f["oxirgi"] is None:
        g.append("Hali hech qanday mashq yoki test bajarilmagan.")
    else:
        g.append(f"Oxirgi 7 kunda {f['kun_7']} kun, oxirgi 30 kunda {f['kun_30']} kun faol bo‘lgan.")
    if m["ko_rilgan"]:
        g.append(f"Matematika bankida {m['ko_rilgan']} ta savol ko‘rilgan (bankning {m['qamrov']}%); hozirgi holatda {m['hozirgi']}% savol to‘g‘ri.")
        el = m["elementar"]
        g.append(f"Elementar matematika (natural sonlar va kasrlar): {el['daraja']} daraja ({el['hozirgi']}%, {el['ko_rilgan']} savol)." if el["daraja"]
                 else (f"Elementar matematika bo‘yicha daraja hali aniqlanmaydi: faqat {el['ko_rilgan']} savol yechilgan (kamida {ISHONCH_ENG_KAM} ta kerak)." if el["ko_rilgan"] else "Elementar matematika mavzulari (1–10) hali yechilmagan."))
        if m["nozik"]:
            g.append("Nozik mavzular: " + "; ".join(f"{t['raqam']}. {t['nom']} ({t['hozirgi']}%)" for t in m["nozik"][:3]) + ".")
        h = m["holatlar"]
        if h["takror"] + h["unutilgan"]:
            g.append(f"Taxminiy hisobda {h['takror']} ta savolni takrorlash vaqti keldi, {h['unutilgan']} tasi unutilgan bo‘lishi mumkin.")
        if h["xato"]:
            g.append(f"Oxirgi urinishda xato qilingan savollar: {h['xato']} ta.")
    if x["sinflar"]:
        s = x["sinflar"][0]
        g.append(f"Xalqaro sinfda: «{s['nom']}», " + (f"{s['guruh']}-guruh ({s['guruhlar_soni']} ta guruhdan), reyting {s['reyting']}." if s["guruh"] else "hali guruhga tushmagan (kirish testi kerak)."))
    if x["sohalar"]:
        z = [a for a in x["sohalar"] if a["jami"] >= 4][:2]
        if z:
            g.append("Xalqaro testlarda eng zaif sohalar: " + ", ".join(f"{a['nom']} ({a['foiz']}%)" for a in z) + ".")
    return g


def _q(cur, nom, sql, par=()):
    """Jadval bo'lmasa yoki so'rov xato bersa — bo'sh ro'yxat (pasport boshqa bo'limlarga bog'liq bo'lib qolmasin)."""
    try:
        cur.execute(f"SAVEPOINT p_{nom}")
        cur.execute(sql, par)
        r = [dict(x) for x in cur.fetchall()]
        cur.execute(f"RELEASE SAVEPOINT p_{nom}")
        return r
    except Exception:   # noqa: BLE001
        cur.execute(f"ROLLBACK TO SAVEPOINT p_{nom}")
        return []


def _xb_nomlari():
    try:
        from modules.xalqaro_baholash import KONTENT
        return KONTENT.ensure().mavzu_by_kalit
    except Exception:   # noqa: BLE001
        return {}


def _soha_nomlari():
    """{(to'plam, soha_kaliti): ko'rsatiladigan nom} — xalqaro bankning o'z nomlari («geometriya» → «Geometriya va o'lchov»)."""
    try:
        from modules.xalqaro_baholash import KONTENT
        return {(tk, t["soha"]): t["soha_nomi"] for tk, tops in KONTENT.ensure().ramka.get("mavzular", {}).items() for t in tops if t.get("soha_nomi")}
    except Exception:   # noqa: BLE001
        return {}


FIKRLASH_NOMI = {"bilish": "Bilish", "qollash": "Qo‘llash", "mulohaza": "Mulohaza"}


def pasport_yig(cur, uid, bank, hozir=None):
    hozir = hozir or datetime.now(TZ)
    u = (_q(cur, "u", "SELECT full_name, role, class FROM users WHERE user_id=%s", (uid,)) or [{}])[0]
    mavzular = {r: {"nom": m["nom"], "kitob": m["kitob"], "jami": bank.soni(r)} for r, m in bank.mavzular.items()}
    mat = _q(cur, "mat", "SELECT savol_id, mavzu, urinish, togri, oxirgi_togri, yangilangan FROM mat_bank_javob WHERE user_id=%s", (uid,))
    vaqt = [r["yangilangan"] for r in mat] + [r["yangilangan"] for r in _q(cur, "xbv", "SELECT yangilangan FROM xb_bilim WHERE user_id=%s", (uid,))] \
        + [r["topshirilgan"] for r in _q(cur, "xbi", "SELECT topshirilgan FROM xb_imtihon WHERE user_id=%s AND topshirilgan IS NOT NULL", (uid,))]
    # xalqaro: sinf, guruh, reyting
    sinflar = []
    for s in _q(cur, "xs", """SELECT s.id, s.nom, s.toplam, COALESCE(o.full_name,'') AS ustoz, g.guruh, g.reyting,
                                     (SELECT COUNT(DISTINCT guruh) FROM xb_guruh_azo WHERE sinf_id=s.id) AS guruhlar
                              FROM xb_sinf_azo a JOIN xb_sinf s ON s.id=a.sinf_id AND s.faol LEFT JOIN users o ON o.user_id=s.egasi
                              LEFT JOIN xb_guruh_azo g ON g.sinf_id=s.id AND g.user_id=a.user_id WHERE a.user_id=%s ORDER BY a.qoshildi DESC""", (uid,)):
        sinflar.append({"nom": s["nom"], "toplam": s["toplam"], "oqituvchi": s["ustoz"], "guruh": s["guruh"], "guruhlar_soni": int(s["guruhlar"] or 0), "reyting": s["reyting"]})
    imt = _q(cur, "xi", """SELECT tur, toplam, ball, foiz, topshirilgan, natija FROM xb_imtihon WHERE user_id=%s AND rasmiy AND topshirilgan IS NOT NULL AND ball IS NOT NULL
                           ORDER BY topshirilgan DESC LIMIT 8""", (uid,))
    soha, fik = {}, {}
    for r in imt:
        n = r.get("natija") or {}
        for d, man in ((soha, n.get("soha") or {}), (fik, n.get("fikrlash") or {})):
            for k, (ok, jami) in man.items():
                e = d.setdefault(k, [0, 0]); e[0] += int(ok); e[1] += int(jami)
    nomlar = _xb_nomlari()
    sn = _soha_nomlari()

    def soha_nomi(k):
        tk, _, kalit = k.partition("|")
        return sn.get((tk, kalit)) or (kalit or tk).replace("_", " ").capitalize()
    sohalar = sorted([{"nom": soha_nomi(k), "togri": v[0], "jami": v[1], "foiz": round(100 * v[0] / v[1])} for k, v in soha.items() if v[1]], key=lambda a: a["foiz"])
    fikrlash = [{"nom": FIKRLASH_NOMI.get(k, k), "togri": v[0], "jami": v[1], "foiz": round(100 * v[0] / v[1])} for k, v in fik.items() if v[1]]
    zaif = []
    for r in _q(cur, "xz", """SELECT mavzu, SUM(urinish) AS ur, SUM(togri) AS tg FROM xb_bilim WHERE user_id=%s AND mavzu<>'' GROUP BY mavzu HAVING SUM(urinish)>=5""", (uid,)):
        f = round(100 * int(r["tg"]) / int(r["ur"]))
        if f < 60:
            zaif.append({"mavzu": r["mavzu"], "nom": (nomlar.get(r["mavzu"]) or {}).get("nom", r["mavzu"]), "foiz": f, "urinish": int(r["ur"])})
    p = {"kim": {"user_id": uid, "ism": u.get("full_name") or "", "sinf": u.get("class") or "", "rol": u.get("role") or ""},
         "faollik": faollik_bolimi(vaqt, hozir), "matematika": matematika_bolimi(mat, mavzular, hozir),
         "xalqaro": {"sinflar": sinflar, "imtihonlar": [{"tur": r["tur"], "toplam": r["toplam"], "ball": r["ball"], "foiz": r["foiz"], "sana": r["topshirilgan"].isoformat()} for r in imt],
                     "sohalar": sohalar, "fikrlash": fikrlash, "zaif_mavzular": sorted(zaif, key=lambda a: a["foiz"])[:5]},
         "eslatma": "Esdan chiqarish — o‘lchov emas, taxminiy model (har to‘g‘ri javobdan keyin eslab qolish muddati uzayadi). Daraja faqat yetarli savol yechilganda aytiladi."}
    p["xulosa"] = xulosa_yoz(p)
    return p


def kim_koradi(cur, ko, bola):
    """O'zi, admin, ota-onasi, o'qituvchisi (kurs guruhi yoki xalqaro sinf egasi) ko'ra oladi."""
    if ko == bola:
        return True
    if _q(cur, "adm", "SELECT 1 FROM admin_akkaunt WHERE uid=%s", (ko,)):
        return True
    try:
        from modules.bogcha_reja import ota_bolami
        if ota_bolami(cur, ko, bola):
            return True
    except Exception:   # noqa: BLE001
        pass
    return bool(_q(cur, "ust1", "SELECT 1 FROM kurs_guruh g JOIN kurs_guruh_azo a ON a.guruh_id=g.id WHERE g.egasi=%s AND a.user_id=%s AND g.faol LIMIT 1", (ko, bola))
                or _q(cur, "ust2", "SELECT 1 FROM xb_sinf s JOIN xb_sinf_azo a ON a.sinf_id=s.id WHERE s.egasi=%s AND a.user_id=%s AND s.faol LIMIT 1", (ko, bola)))


def create_router(platform):
    router = APIRouter(tags=["pasport"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def yig(ko, bola):
        from modules.mat_bank import bank_ol
        conn = platform._db(); cur = conn.cursor()
        try:
            if not kim_koradi(cur, ko, bola):
                raise HTTPException(403, "Bu o‘quvchining pasportini ko‘rish huquqingiz yo‘q")
            r = pasport_yig(cur, bola, bank_ol())
            conn.commit()
            return r
        finally:
            cur.close(); conn.close()

    @router.get("/api/pasport/mening")
    def mening(token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        return yig(u, u)

    @router.get("/api/pasport/{user_id}")
    def oquvchi(user_id: int, token: str = None, authorization: Optional[str] = Header(None)):
        return yig(uid(token, authorization), user_id)

    return router

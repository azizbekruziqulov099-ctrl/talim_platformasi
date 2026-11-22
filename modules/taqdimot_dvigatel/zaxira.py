"""AI javob bermaganda (limit tugagan, kalit yo'q, server band) taqdimot o'z bazamizdan beriladi — ish to'xtab qolmaydi.

Manbalar (shu tartibda):
  1) qo'lda yozilgan darslar (malumot/darslar) — mavzu aynan mos kelsa;
  2) AI kutubxonasi (taqdimot_mavzular jadvali, holat='tayyor') — 1–11-sinf, bakalavr, magistratura;
  3) tayyor to'plamlar (kutubxona/<toplam>) — OTM kurslari.

Mavzu aynan topilmasa, shu fandan eng yaqin mavzu beriladi (nomlari haqiqatan o'xshash bo'lsa). O'xshashi ham bo'lmasa
hech narsa berilmaydi: boshqa mavzuni «shu mavzu» deb ko'rsatmaymiz, faqat shu fandan tayyor mavzular tavsiya qilinadi.
"""
from __future__ import annotations

import re
import threading
import time

from . import darslar, kutubxona, sxema
from .rasm_tanla import tokenlar

ANIQ, YAQIN = 0.80, 0.45
_KESH = {"vaqt": 0.0, "qatorlar": ()}
_QULF = threading.Lock()
KESH_SON = 90.0


def _n(s) -> str:
    return darslar._n(s)


def _guruh(daraja: str) -> str:
    d = _n(daraja)
    return "otm" if d.startswith(("bak", "mag", "otm", "oliy")) else "maktab"


def fan_yaqin(a: str, b: str, daraja: str = "maktab", sinf="") -> int:
    """2 — aynan shu fan; 1 — shu fan oilasi (Matematika ~ Algebra); 0 — boshqa fan."""
    na, nb = _n(a), _n(b)
    if not na or not nb:
        return 1
    if na == nb:
        return 2
    ta, tb = tokenlar(a), tokenlar(b)
    if ta and tb and len(ta & tb) * 2 >= min(len(ta), len(tb)) + 1:
        return 1
    if _guruh(daraja) == "maktab":
        try:
            return 1 if darslar._fan_mos(a, b, str(sinf or "5"), "maktab") else 0
        except Exception:
            return 0
    return 0


def oxshashlik(sorov: str, nomzod: str) -> float:
    """0…1: so'ralgan mavzu bilan bazadagi mavzu nomi qanchalik bir xil (so'z o'zaklari bo'yicha)."""
    if _n(sorov) == _n(nomzod):
        return 1.0
    q, c = tokenlar(sorov), tokenlar(nomzod)
    if not q or not c:
        return 0.0
    um = q & c
    if not um or max(len(x) for x in um) < 4:
        return 0.0
    return round(0.65 * len(um) / len(q) + 0.35 * len(um) / len(c), 3)


def _sinf_masofa(sorov, nomzod) -> int:
    s = darslar._sinf_n(sorov)[0]
    a, b = darslar._sinf_n(nomzod)
    if not s or (a, b) == (0, 99):
        return 0
    return 0 if a <= s <= b else min(abs(s - a), abs(s - b))


def _db_qatorlari(D) -> tuple:
    """AI kutubxonasidagi tayyor mavzular ro'yxati (miyasiz) — qisqa muddat xotirada turadi."""
    with _QULF:
        if _KESH["qatorlar"] and time.monotonic() - _KESH["vaqt"] < KESH_SON:
            return _KESH["qatorlar"]
    try:
        D.kutub.migrate()
        with D.ps.db() as cur:
            cur.execute("SELECT id, daraja, sinf, fan, mavzu FROM taqdimot_mavzular WHERE holat='tayyor' AND yozilsin AND miya IS NOT NULL")
            rows = tuple({"manba": "kutubxona", "id": r["id"], "daraja": r["daraja"], "sinf": r["sinf"] or "", "fan": r["fan"], "mavzu": r["mavzu"]}
                         for r in cur.fetchall())
    except Exception:
        rows = ()
    with _QULF:
        _KESH.update(vaqt=time.monotonic(), qatorlar=rows)
    return rows


def keshni_tozala():
    with _QULF:
        _KESH.update(vaqt=0.0, qatorlar=())


def _toplam_qatorlari() -> list:
    out = []
    for t in kutubxona.toplamlar():
        r = kutubxona.reestr(t["kod"]) or {}
        fan = re.split(r"\s*[(,]", r.get("nom") or "")[0]
        kurs = re.search(r"(\d)-kurs", r.get("nom") or "")
        for m in r.get("mavzular") or []:
            if m.get("tur") in (None, "maruza", "amaliy") and m.get("nom") and m.get("kod"):
                out.append({"manba": "toplam", "toplam": t["kod"], "kod": m["kod"], "daraja": r.get("daraja") or "bakalavr",
                            "sinf": f"{kurs.group(1)}-kurs" if kurs else "", "fan": r.get("fan") or fan, "mavzu": m["nom"]})
    return out


def nomzodlar(D, daraja: str, sinf, fan: str, mavzu: str) -> list:
    """Bazadagi mos mavzular — eng mosi birinchi. Har biri: {..., ball, fan_mos, aniq}."""
    g = _guruh(daraja)
    out = []
    for x in list(_db_qatorlari(D)) + _toplam_qatorlari():
        if _guruh(x["daraja"]) != g:
            continue
        fm = fan_yaqin(fan, x["fan"], daraja, sinf) if fan else 1
        if not fm:
            continue
        o = oxshashlik(mavzu, x["mavzu"])
        if o < YAQIN:
            continue
        if not fan and o < 0.6:    # fan aytilmagan bo'lsa faqat ishonchli moslik
            continue
        ms = _sinf_masofa(sinf, x["sinf"])
        dm = 0 if _n(x["daraja"])[:3] == _n(daraja or "maktab")[:3] else 1
        out.append({**x, "oxshash": o, "fan_mos": fm, "sinf_masofa": ms, "aniq": o >= ANIQ,
                    "ball": o + 0.04 * fm - 0.03 * min(ms, 5) - 0.05 * dm})
    out.sort(key=lambda x: -x["ball"])
    return out


def tavsiyalar(D, daraja: str, sinf, fan: str, n: int = 3) -> list:
    """Mavzu topilmaganda: shu fan va sinfdan tayyor mavzular nomlari."""
    if not fan:
        return []
    g = _guruh(daraja)
    v = [(_sinf_masofa(sinf, x["sinf"]), x["mavzu"]) for x in list(_db_qatorlari(D)) + _toplam_qatorlari()
         if _guruh(x["daraja"]) == g and fan_yaqin(fan, x["fan"], daraja, sinf)]
    v.sort(key=lambda t: t[0])
    return [m for _, m in v[:n]]


def _miya_ol(D, x):
    if x["manba"] == "kutubxona":
        return D.kutub.miya(x["id"])
    return kutubxona.miya(x["toplam"], x["kod"])


# ---------------------------------------------------------------- qo'lda yozilgan dars → taqdimot miyasi
def darsdan_miya(x: dict) -> dict:
    """Qo'lda yozilgan dars (masalliq: bayon, misollar, mashqlar, atamalar, savollar) → taqdimot miyasi. AI ishlatilmaydi."""
    ms = x.get("masalliq") or {}
    t = sxema.t
    bolimlar = []
    bayon = [b for b in ms.get("bayon") or [] if isinstance(b, dict) and t(b.get("matn"))]
    if bayon:
        sl = []
        for b in bayon[:6]:
            el = [{"tur": "matn", "matn": t(b.get("matn"), 900), **({"rasm": b["rasm"]} if b.get("rasm") else {})}]
            if t(b.get("misol")):
                el.append({"tur": "hayotiy", "sarlavha": "Misol", "matn": t(b.get("misol"), 400)})
            if t(b.get("savol")):
                el.append({"tur": "savol", "matn": t(b.get("savol"), 300), "izoh": t(b.get("javob"), 200)})
            sl.append({"sarlavha": t(b.get("sarlavha"), 110) or x["mavzu"], "elementlar": el[:3],
                       "izoh": t(b.get("javob"), 300) and f"Savol javobi: {t(b.get('javob'), 200)}"})
        if t(ms.get("asosiy_qoida")):
            sl.append({"sarlavha": "Asosiy qoida", "elementlar": [{"tur": "qoida", "matn": t(ms["asosiy_qoida"], 600)}]})
        bolimlar.append({"nom": "Yangi mavzu", "slaydlar": sl})
    misollar = [m for m in ms.get("misollar") or [] if isinstance(m, dict) and t(m.get("shart"))]
    if misollar:
        bolimlar.append({"nom": "Yechimli misollar", "slaydlar": [
            {"sarlavha": f"{i}-misol", "elementlar": [{"tur": "misol", "shart": t(m["shart"], 600), "qadamlar": sxema.ls(m.get("yechim"), 8, 260),
                                                       "javob": t(m.get("javob"), 200)}]} for i, m in enumerate(misollar[:4], 1)]})
    must = []
    mashq = [m for m in ms.get("mashqlar") or [] if isinstance(m, dict) and t(m.get("shart"))]
    if mashq:
        must.append({"sarlavha": "Mashqlar", "elementlar": [{"tur": "matn", "bandlar": [t(m["shart"], 300) for m in mashq[:8]]}],
                     "izoh": "Javoblar: " + "; ".join(t(m.get("javob"), 60) for m in mashq[:8])})
    guruh = [g for g in ms.get("guruh_topshiriqlari") or [] if isinstance(g, dict) and t(g.get("topshiriq"))]
    for gq in guruh[:2]:
        must.append({"sarlavha": t(gq.get("nom"), 110) or "Guruh topshirig‘i", "elementlar": [{"tur": "masala", "shart": t(gq["topshiriq"], 600)}],
                     "izoh": t(gq.get("yechim"), 300)})
    bay = [b for b in ms.get("bayonotlar") or [] if isinstance(b, dict) and t(b.get("matn"))]
    if len(bay) >= 2:
        must.append({"sarlavha": "To‘g‘ri yoki noto‘g‘ri?", "elementlar": [{"tur": "togri_notogri", "fikrlar": [
            {"matn": t(b["matn"], 200), "togri": bool(b.get("togri")), "izoh": t(b.get("izoh"), 200)} for b in bay[:6]]}]})
    atama = [a for a in ms.get("atamalar") or [] if isinstance(a, dict) and t(a.get("atama"))]
    if atama:
        must.append({"sarlavha": "Atamalar", "elementlar": [{"tur": "xossalar", "bandlar": [
            {"nom": t(a["atama"], 80), "matn": t(a.get("tarif"), 300)} for a in atama[:6]]}]})
    if must:
        bolimlar.append({"nom": "Mustahkamlash", "slaydlar": must})
    sav = [s for s in ms.get("savollar") or [] if isinstance(s, dict) and t(s.get("savol"))]
    m = {"meta": {"mavzu": x["mavzu"], "fan": x["fan"], "sinf": str(x["sinf"]), "daraja": x["daraja"], "tur": "dars",
                  "tayanch": [t(a["atama"], 60) for a in atama[:5]]},
         "bolimlar": bolimlar,
         "takrorlash": {"mavzu": x["mavzu"], "savollar": [{"savol": t(s["savol"], 200), "javob": t(s.get("javob"), 160)} for s in sav[:6]]},
         "xulosa": [t(ms.get("asosiy_qoida"), 300)] if t(ms.get("asosiy_qoida")) else []}
    if t(ms.get("muammoli_savol")):
        m["muammo"] = {"masalalar": [{"sarlavha": "Muammoli savol", "matn": t(ms["muammoli_savol"], 300)}]}
    return sxema.normallashtir(m)


# ---------------------------------------------------------------- asosiy kirish
def top(D, sorov: dict, sabab: str = "") -> dict | None:
    """So'rov (mavzu, fan, daraja, sinf) uchun bazadan tayyor miya yoki None. Miyaga `_zaxira` belgisi qo'yiladi."""
    mavzu, fan = sorov.get("mavzu") or "", sorov.get("fan") or ""
    daraja, sinf = sorov.get("daraja") or "maktab", sorov.get("sinf") or ""
    topildi, miya = None, None
    try:
        x = darslar.top(daraja, sinf, fan, mavzu)
        if x and (x.get("masalliq") or {}).get("bayon"):
            miya = darsdan_miya(x)
            if sum(len(b["slaydlar"]) for b in miya.get("bolimlar") or []) >= 4:
                topildi = {"manba": "dars", "mavzu": x["mavzu"], "fan": x["fan"], "sinf": str(x["sinf"]), "aniq": True}
    except Exception:
        topildi = None
    if not topildi:
        for x in nomzodlar(D, daraja, sinf, fan, mavzu)[:4]:
            try:
                miya = _miya_ol(D, x)
            except Exception:
                miya = None
            if isinstance(miya, dict) and miya.get("bolimlar"):
                topildi = {"manba": x["manba"], "mavzu": x["mavzu"], "fan": x["fan"], "sinf": x["sinf"], "aniq": bool(x["aniq"])}
                break
    if not topildi:
        return None
    from .kutubxona_ai import sinf_matni
    try:
        sm = sinf_matni(_guruh(daraja) == "maktab" and "maktab" or "bakalavr", topildi["sinf"]) if topildi["sinf"] else ""
    except Exception:
        sm = topildi["sinf"]
    joy = ", ".join(v for v in (topildi["fan"], sm) if v)
    if topildi["aniq"]:
        xabar = f"AI hozir band — taqdimot tayyor mavzular bazasidan berildi: «{topildi['mavzu']}»" + (f" ({joy})" if joy else "") + "."
    else:
        xabar = (f"AI hozir band va aynan «{mavzu}» mavzusi bazada yo‘q — eng yaqin tayyor mavzu berildi: «{topildi['mavzu']}»"
                 + (f" ({joy})" if joy else "") + ". Keyinroq AI bilan qayta yozdirishingiz mumkin.")
    miya = dict(miya)
    miya["_zaxira"] = {**topildi, "sabab": sxema.t(sabab, 160), "xabar": xabar}
    return miya


def rejaga(miya: dict) -> dict:
    """Tayyor miyadan reja (faqat tuzilma) — «avval reja» rejimida AI ishlamasa."""
    bol = []
    for b in miya.get("bolimlar") or []:
        sl = [{"sarlavha": s.get("sarlavha") or "", "maqsad": "", "tur": ((s.get("elementlar") or [{}])[0] or {}).get("tur") or ""}
              for s in b.get("slaydlar") or [] if s.get("sarlavha")]
        if sl:
            bol.append({"nom": b.get("nom") or "Bo‘lim", "izoh": b.get("izoh") or "", "slaydlar": sl})
    meta = miya.get("meta") or {}
    return {"meta": {"mavzu": meta.get("mavzu"), "qisqa": meta.get("qisqa"), "maqsad": meta.get("maqsad"), "tayanch": meta.get("tayanch")},
            "bolimlar": bol}


def topilmadi_xabari(D, sorov: dict, sabab: str) -> str:
    tv = tavsiyalar(D, sorov.get("daraja") or "maktab", sorov.get("sinf") or "", sorov.get("fan") or "")
    bosh = "AI hozir band (limit tugagan yoki javob bermayapti) va bu mavzu tayyor mavzular bazasida hali yo‘q."
    if tv:
        return bosh + " Shu fandan tayyorlari: " + "; ".join(f"«{m}»" for m in tv) + " — «Tayyor mavzular»dan oching yoki keyinroq urinib ko‘ring."
    return bosh + " Birozdan keyin qayta urinib ko‘ring."

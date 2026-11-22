"""REV693: ota-ona statistikasi — til o'zlashtirish foizi va fanlar bo'yicha o'sish.

Sof hisob (bazasiz): bola_dars_faollik qatorlaridan.
«Mustahkam» so'z — kamida 3 marta uchragan va kamida 2 xil kunda (bir kunda uch marta ko'rish hali eslab qolish emas).
Bosqich: 1 — tinglab tushunadi; 2 — so'zlarni aytadi; 3 — gap tuzadi.
"""
MUSTAHKAM_MARTA = 3
MUSTAHKAM_KUN = 2
BOSQICH_NOMI = {1: "Tinglab tushunadi", 2: "So'zlarni aytadi", 3: "Gap tuzadi"}


def _foiz(a, b):
    return round(a * 100 / b) if b else 0


def ozlashtirish(rows, kurs_of):
    """rows: [{"fan", "sana", "sozlar": [{"soz","aytdi"}], "togri", "jami", "tugadi"}]; kurs_of(fan) → (kalit, {"nom","turi","emoji"}).

    Qaytaradi: {"tillar": [...], "fanlar": [...]} — tillar so'z bo'yicha, fanlar test javoblari bo'yicha."""
    kurslar = {}
    for r in rows or []:
        kalit, kurs = kurs_of(r.get("fan") or "")
        if not kalit:
            continue
        k = kurslar.setdefault(kalit, {"kalit": kalit, "nom": kurs.get("nom") or r.get("fan") or kalit, "emoji": kurs.get("emoji") or "",
                                       "turi": kurs.get("turi") or "fan", "soz": {}, "darslar": 0, "togri": 0, "jami": 0, "kunlar": set()})
        if r.get("tugadi"):
            k["darslar"] += 1
        k["kunlar"].add(r.get("sana"))
        if r.get("jami"):
            k["togri"] += int(r.get("togri") or 0)
            k["jami"] += int(r.get("jami") or 0)
        for w in r.get("sozlar") or []:
            soz = " ".join(str((w or {}).get("soz") or "").split()).lower()
            if not soz:
                continue
            s = k["soz"].setdefault(soz, {"marta": 0, "kunlar": set(), "aytdi": False})
            s["marta"] += 1
            s["kunlar"].add(r.get("sana"))
            if w.get("aytdi") is True:
                s["aytdi"] = True
    tillar, fanlar = [], []
    for k in kurslar.values():
        if k["turi"] == "til":
            jami = len(k["soz"])
            mustahkam = sum(1 for s in k["soz"].values() if s["marta"] >= MUSTAHKAM_MARTA and len(s["kunlar"]) >= MUSTAHKAM_KUN)
            aytdi = sum(1 for s in k["soz"].values() if s["aytdi"])
            gap = sum(1 for soz, s in k["soz"].items() if s["aytdi"] and " " in soz)
            bosqich = 3 if gap >= 5 else 2 if aytdi >= 5 and aytdi * 100 >= jami * 30 else 1
            tillar.append({"kalit": k["kalit"], "nom": k["nom"], "emoji": k["emoji"], "sozlar": jami, "mustahkam": mustahkam,
                           "foiz": _foiz(mustahkam, jami), "aytdi": aytdi, "darslar": k["darslar"], "kunlar": len(k["kunlar"]),
                           "bosqich": bosqich, "bosqich_nomi": BOSQICH_NOMI[bosqich]})
        else:
            fanlar.append({"kalit": k["kalit"], "nom": k["nom"], "emoji": k["emoji"], "darslar": k["darslar"], "kunlar": len(k["kunlar"]),
                           "togri": k["togri"], "jami": k["jami"], "foiz": _foiz(k["togri"], k["jami"])})
    tillar.sort(key=lambda x: (-x["sozlar"], x["nom"]))
    fanlar.sort(key=lambda x: (-x["darslar"], x["nom"]))
    return {"tillar": tillar, "fanlar": fanlar}

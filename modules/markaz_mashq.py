"""REV275: 4 ko'nikma mashqlari (markaz): tinglab tushunish, diktant, gapirish (talaffuz). Kontent — o'zimiz yozgan kurs darslari."""
import random
from modules.markaz_kontent.en_a1 import DARSLAR as EN_A1
from modules.markaz_kontent.en_a1_2 import DARSLAR2 as EN_A1_2

KURSLAR = {("en", "A1"): list(EN_A1) + list(EN_A1_2)}   # REV277: 18 ta hayotiy dars (1–2-qism)


def mashqlar(til, daraja, dars, iz="uz", seed=None):
    darslar = KURSLAR.get((til, daraja))
    if not darslar or not (1 <= int(dars) <= len(darslar)):
        return None
    d = darslar[int(dars) - 1]
    I = 0 if iz == "uz" else 1
    rnd = random.Random(seed if seed is not None else f"{til}{daraja}{dars}{iz}")
    tarjimalar = [x[2 + I] for x in d["dialog"]]
    tinglash = []
    for k, (kim, gap, uz, ru) in enumerate(d["dialog"]):
        togri = (uz, ru)[I]
        boshqa = [t for t in tarjimalar if t != togri]
        rnd.shuffle(boshqa)
        var = [togri] + boshqa[:2]
        rnd.shuffle(var)
        tinglash.append({"kim": kim, "gap": gap, "variantlar": var, "javob": var.index(togri)})
    diktant = [{"gap": ex, "soz": w, "mano": (uz, ru)[I], "emoji": e} for e, w, uz, ru, ex in d["sozlar"]]
    gapirish = [{"gap": g} for _, g, *_ in d["dialog"]] + [{"gap": x} for x in d["ibora"][3]]
    return {"nom": d["nom"][I], "hook": d["hook"][0], "tinglash": tinglash, "diktant": diktant, "gapirish": gapirish,
            "rol": {"topshiriq": d["rol"][0], "izoh": d["rol"][1 + I], "namuna": d["rol"][3]}, "darslar_soni": len(darslar),
            "dialog": [{"kim": kim, "gap": gap} for kim, gap, *_ in d["dialog"]]}

"""REV283: o'quv markazi mashqlari — KONTENT MIYA'DAN (yuklangan «… — Erkin til» kitobidan), koddagi nusxa yo'q.
Dars xonasi darsidan (load_lesson) mashq ma'lumoti olinadi:
  • suhbat qadami (doska qatorlari «[en]Kim: gap[/en]») → tinglash (qaysi gap eshitildi), gapirish;
  • so'z qadamlari (sarlavha «🍎 [en]apple[/en] — olma», doska: belgi+so'z / ma'no / misol gap) → diktant (rasm bilan);
  • ibora qadami (doskada [en] misollar) → gapirish;
  • «Your turn!» qadami (doska: topshiriq / namuna) → jonli suhbat va yozish topshirig'i."""
import random
import re

TEG = re.compile(r"\[(en|ru|de|fr|es|ar|tr|ko|ja|zh)\]([\s\S]*?)\[/\1\]")


def _teg(t, til):
    return [m.group(2).strip() for m in TEG.finditer(str(t or "")) if m.group(1) == til and m.group(2).strip()]


def _izoh(t, til="en"):
    """Izoh matni: o'rganilayotgan tildagi topshiriq olib tashlanadi, qolgan teglar (izoh tili) ochiladi."""
    t = re.sub(r"\[" + til + r"\][\s\S]*?\[/" + til + r"\]", " ", str(t or ""), count=1)
    t = re.sub(r"\[/?[a-z]{2}\]", "", t)
    return re.sub(r"\s+", " ", t).strip(" —-")


# REV289: qadam belgilari kurs tilida («Listen to the conversation» / «Послушайте разговор» …)
BELGI = {"suhbat": ("listen to the conversation", "послушайте разговор"), "rol": ("your turn", "ваша очередь"), "yakun": ("today we learned", "сегодня мы выучили")}


def _bormi(matn, tur):
    t = (matn or "").lower()
    return any(t.startswith(b) for b in BELGI[tur])


def mashq_darsdan(lesson, til="en", seed=""):
    steps = (lesson or {}).get("steps") or []
    nom = ((lesson or {}).get("topic") or {}).get("mavzu") or ((lesson or {}).get("mavzu") or {}).get("nomi") or ""
    dialog, sozlar, ibora, rol = [], [], [], None
    for st in steps:
        sar, doska, ovoz = st.get("sarlavha") or "", st.get("doska") or "", st.get("ovoz") or ""
        sar_en = _teg(sar, til)
        if sar_en and _bormi(sar_en[0], "suhbat"):
            for g in _teg(doska, til):
                m = re.match(r"^([^:]{1,30}):\s*(.+)$", g)
                dialog.append({"kim": m.group(1).strip() if m else "", "gap": (m.group(2) if m else g).strip()})
        elif sar_en and _bormi(sar_en[0], "rol"):
            d = _teg(doska, til)
            rol = {"topshiriq": d[0] if d else "", "namuna": d[1] if len(d) > 1 else "", "izoh": _izoh(ovoz, til)}
        elif re.match(r"^\s*\S+\s*\[" + til + r"\][^\[]+\[/" + til + r"\]\s*[—-]\s*\S", sar):
            emoji = sar.strip().split()[0]
            w = _teg(sar, til)[0]
            mano = re.sub(r"^.*?\[/" + til + r"\]\s*[—-]\s*", "", sar).strip()
            misol = (_teg(doska, til) or [w])[-1]
            sozlar.append({"emoji": emoji, "soz": w, "mano": mano, "gap": misol})
        elif st.get("turi") == "tushuncha" and len(_teg(doska, til)) >= 2 and not (sar_en and _bormi(sar_en[0], "yakun")):
            ibora += _teg(doska, til)
    rnd = random.Random(f"{nom}{seed}")
    tinglash = []
    for k, d in enumerate(dialog):
        boshqa = [x["gap"] for x in dialog if x["gap"] != d["gap"]]
        rnd.shuffle(boshqa)
        var = [d["gap"]] + boshqa[:2]
        rnd.shuffle(var)
        tinglash.append({"kim": d["kim"], "gap": d["gap"], "variantlar": var, "javob": var.index(d["gap"])})
    gapirish = [{"gap": d["gap"]} for d in dialog] + [{"gap": x} for x in ibora[:3] if x not in {d["gap"] for d in dialog}]
    return {"nom": nom, "dialog": dialog, "tinglash": tinglash, "diktant": sozlar, "gapirish": gapirish,
            "rol": rol or {"topshiriq": "", "namuna": "", "izoh": ""}, "rol_kim": dialog[0]["kim"] if dialog else "Partner"}

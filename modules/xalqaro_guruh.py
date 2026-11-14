"""REV553: Xalqaro baholash (PISA / TIMSS) sinfi — o'quvchilarni REYTING bo'yicha guruhlarga bo'lish.

Sof funksiyalar (bazasiz, testlanadi). Qoidalar (Azizjon bergan):
  1. O'quvchilar reyting bo'yicha tartiblanadi; har guruhda 30 ta: 1-guruh — eng yuqori reytinglilar, 2-guruh — keyingilari …
  2. Guruhda 20 tadan kam o'quvchi qolmasligi kerak. Oxirgi guruh 20 dan kam chiqsa:
       • qoldiq 1–9 ta bo'lsa — oldingi guruhga qo'shiladi (30 atrofida: 31–39 ta);
       • qoldiq 10–19 ta bo'lsa — oxirgi ikki guruh teng bo'linadi (har biri 20–25 ta).
     Shunda har guruh 20–39 ta bo'ladi. Jami o'quvchi 20 dan kam bo'lsa — bitta guruh (boshqa iloj yo'q).
  3. Reytingi hali yo'q (kirish testini topshirmagan) o'quvchi guruhga kiritilmaydi — «kutayotganlar» ro'yxatida turadi.
  4. Qayta guruhlashda guruhi o'zgargan o'quvchilar alohida qaytariladi — ularga «Siz reytingingizga mos yangi guruhga
     o'tdingiz» degan xabar ko'rsatiladi.
"""
from __future__ import annotations

GURUH_HAJMI = 30
GURUH_ENG_KAM = 20


def guruh_hajmlari(n: int, hajm: int = GURUH_HAJMI, eng_kam: int = GURUH_ENG_KAM) -> list[int]:
    """n ta o'quvchi uchun guruh hajmlari ro'yxati (yuqori reytingdan pastga). Masalan 68 → [30, 38]; 75 → [30, 23, 22]."""
    n = int(n)
    if n <= 0:
        return []
    toliq, qoldiq = divmod(n, hajm)
    if toliq == 0:
        return [n]                      # jami 30 dan kam — bitta guruh
    hajmlar = [hajm] * toliq
    if qoldiq == 0:
        return hajmlar
    if qoldiq >= eng_kam:
        return hajmlar + [qoldiq]       # qoldiq o'zi to'laqonli guruh (20–29)
    if qoldiq < eng_kam - hajm // 3:    # 1–9: oxirgi guruhga qo'shiladi (31–39 — «30 atrofida»)
        hajmlar[-1] += qoldiq
        return hajmlar
    jami = hajm + qoldiq                # 10–19: oxirgi ikki guruh teng bo'linadi (40–49 → 20–25 dan)
    return hajmlar[:-1] + [(jami + 1) // 2, jami // 2]


def guruhlarga_bol(oquvchilar: list[dict], hajm: int = GURUH_HAJMI, eng_kam: int = GURUH_ENG_KAM) -> dict:
    """oquvchilar: [{"user_id": int, "reyting": float | None, "qoshildi": saralash uchun ixtiyoriy}].
    → {"guruhlar": [{"raqam": 1, "azolar": [user_id…], "eng_yuqori": r, "eng_past": r, "ortacha": r}], "kutayotgan": [user_id…]}.
    Teng reytingda avval qo'shilgan o'quvchi yuqoriroq (natija har safar bir xil bo'lishi uchun), so'ng user_id bo'yicha."""
    borlar = [o for o in oquvchilar if o.get("reyting") is not None]
    kutayotgan = [int(o["user_id"]) for o in oquvchilar if o.get("reyting") is None]
    borlar.sort(key=lambda o: (-float(o["reyting"]), str(o.get("qoshildi") or ""), int(o["user_id"])))
    guruhlar, boshi = [], 0
    for raqam, soni in enumerate(guruh_hajmlari(len(borlar), hajm, eng_kam), 1):
        bolak = borlar[boshi:boshi + soni]
        boshi += soni
        r = [float(o["reyting"]) for o in bolak]
        guruhlar.append({"raqam": raqam, "azolar": [int(o["user_id"]) for o in bolak],
                         "eng_yuqori": max(r), "eng_past": min(r), "ortacha": round(sum(r) / len(r), 1)})
    return {"guruhlar": guruhlar, "kutayotgan": kutayotgan}


def guruh_ozgarishlari(eski: dict[int, int], yangi_bolinish: dict) -> list[dict]:
    """eski: {user_id: guruh raqami}. → guruhi o'zgargan yoki birinchi marta guruh olgan o'quvchilar:
    [{"user_id", "eski": raqam | None, "yangi": raqam, "tur": "yangi" | "yuqoriga" | "pastga"}]. Raqam kichik — reyting yuqori."""
    out = []
    for g in yangi_bolinish.get("guruhlar", []):
        for uid in g["azolar"]:
            oldingi = eski.get(uid)
            if oldingi == g["raqam"]:
                continue
            tur = "yangi" if oldingi is None else ("yuqoriga" if g["raqam"] < oldingi else "pastga")
            out.append({"user_id": uid, "eski": oldingi, "yangi": g["raqam"], "tur": tur})
    return out

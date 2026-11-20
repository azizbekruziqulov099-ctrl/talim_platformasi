"""Fan profili va yoshga moslash.

Dvigatel barcha fanlarga taqdimot yasaydi; profil AI (va ChatGPT ko'rsatmasi) ga shu fan va yoshda qaysi slayd
turlari eng foydali ekanini aytadi. Kalitlar uslub.fan_kaliti bilan bir xil.
"""
from __future__ import annotations

import re

from .uslub import fan_kaliti

PROFIL = {
    "matematika": ("tarif, qoida, formula, misol (qadamlar bilan), masala (hayotiy, rasmli), chizma, jadval",
                   "Har mavzuda kamida 2 ta chizma (son o‘qi, ulush, shakl) va 1 ta hayotiy masala."),
    "xorijiy_til": ("lugat (har darsda 1–2 slayd), dialog, bosh_joy (grammatika), moslash (so‘z ↔ tarjima), rasmda_nima, qoida + misol",
                    "Slayd matni o‘rganilayotgan tilda, \"tarjima\" maydonida o‘zbekcha. Lug‘at so‘zi uchun kutubxonadan rasm."),
    "ona_tili": ("qoida + misol (gaplar), bosh_joy, guruhlash (so‘z turkumlari, unli/undosh), parcha, moslash, togri_notogri",
                 "Misol gaplar hayotiy va qisqa; qoidaga 2–3 misol."),
    "adabiyot": ("parcha (asardan yoki xalq og‘zaki ijodidan), vaqt_chizigi (adib hayoti), galereya, savol, togri_notogri",
                 "Faqat xalq og‘zaki ijodi yoki mualliflik muddati o‘tgan asarlardan parcha; uzun iqtibos emas."),
    "tarix": ("vaqt_chizigi (har mavzuda), xarita, galereya (obidalar, shaxslar), taqqoslash, rasmda_nima, togri_notogri",
              "Sanalar aniq; xaritada voqea joylari belgilanadi."),
    "geografiya": ("xarita (har mavzuda), jarayon (aylana: suv aylanishi va h.k.), jadval, galereya, guruhlash",
                   "Xaritada \"belgilash\" — viloyat yoki davlat nomlari, \"joylar\" — shaharlar."),
    "biologiya": ("jarayon (aylana / zanjir: oziq zanjiri, hayot sikli), galereya, guruhlash, tajriba, rasm, togri_notogri",
                  "Tuzilish va jarayonlar rasm bilan; har bo‘limda bitta o‘yin."),
    "tabiiy": ("jarayon, tajriba, galereya, guruhlash, rasmda_nima, togri_notogri, hayotiy",
               "1–4-sinf: kuzatish va tajriba, ko‘p rasm."),
    "fizika": ("tajriba, formula, misol, jarayon, chizma, xossalar, hayotiy", "Har qonun uchun tajriba yoki hayotiy misol."),
    "kimyo": ("tajriba (xavfsizlik bilan), formula, jadval, guruhlash, xossalar", "Tajribada \"xavfsizlik\" maydoni majburiy."),
    "informatika": ("jarayon (zanjir: algoritm qadamlari), guruhlash (kiritish/chiqarish qurilmalari), galereya, jadval, bosh_joy",
                    "Qurilmalar uchun kutubxona rasmlari."),
    "musiqa": ("galereya (cholg‘ular), guruhlash (torli, urma, puflama), vaqt_chizigi (bastakorlar), rasmda_nima, parcha (xalq qo‘shig‘i)",
               "Faqat xalq qo‘shiqlari yoki mualliflik muddati o‘tgan matnlar."),
    "tasviriy": ("galereya, jarayon (qadam: chizish bosqichlari), rasmda_nima, guruhlash", "Har ish bosqichi alohida qadam."),
    "texnologiya": ("jarayon (qadam), galereya (asboblar), tajriba, eslatma (xavfsizlik)", "Asbob bilan ishlashda xavfsizlik eslatmasi."),
    "jismoniy": ("jarayon (qadam: mashq bosqichlari, rasmli), galereya, togri_notogri (xavfsizlik), guruhlash",
                 "Har mashq: nechta marta, qancha vaqt."),
    "tarbiya": ("hayotiy, togri_notogri, guruhlash (yaxshi va yomon odat), rasmda_nima, savol, dialog",
                "Hayotiy vaziyat va muhokama savoli."),
    "pedagogika": ("tarif, taqqoslash, jadval, vaqt_chizigi (olimlar), parcha (iqtibos), jarayon, xossalar",
                   "Nazariya + boshlang‘ich sinfda qo‘llash metodikasi."),
    "umumiy": ("tarif, matn, misol, jadval, galereya, jarayon, togri_notogri", ""),
}


def yosh_bandi(sinf: str, daraja: str = "") -> str:
    d = (daraja or "").lower()
    s = (sinf or "").lower()
    if "bog" in d or "bog" in s or "yosh" in s:
        return "bogcha"
    if "magistr" in d or "magistr" in s:
        return "magistr"
    if any(x in d for x in ("bakalavr", "oliy")) or "kurs" in s:
        return "oliy"
    m = re.search(r"\d+", s)
    if m:
        n = int(m.group())
        return "1-4" if n <= 4 else "5-9" if n <= 9 else "10-11"
    return "5-9"


YOSH = {
    "bogcha": "BOG‘CHA: har slaydda rasm; matn 3–6 so‘z; ko‘p o‘yin (moslash, rasmda_nima, togri_notogri); lug‘at kartalari; test 4 ta, variantlar 2–3 so‘z.",
    "1-4": "1–4-SINF: har slaydda rasm yoki chizma; matn ko‘pi bilan 12 so‘z; har bo‘limda bitta o‘yin (moslash, bosh_joy, rasmda_nima, togri_notogri); test 5–6 ta, qisqa variantlar.",
    "5-9": "5–9-SINF: qoida + misol; 2–3 o‘yin slaydi; jadval va taqqoslash; test 6 ta.",
    "10-11": "10–11-SINF: tahlil, sabab-natija, taqqoslash; manbalar; test 6 ta.",
    "oliy": ("OLIY TA’LIM (bakalavr): har bo‘limda ilmiy ta’rif (muallif va yili bilan, masalan: «L.S. Vygotskiy (1934) bo‘yicha…»), "
             "nazariya yoki yondashuvlarni taqqoslash (taqqoslash/jadval), iqtibos (parcha + muallif), amaliyotda qo‘llash "
             "(boshlang‘ich sinf yoki ish joyida misol), munozara savoli. Oxirida: 6–8 nazorat savoli, 3–4 mustaqil ish, "
             "seminar savollari (\"metodika\" ichida). ADABIYOTLAR: faqat haqiqatda mavjud kitob va maqolalar — muallif, nomi, yili, "
             "nashriyot; aniq bilmasang yozma (to‘qima manba qat’iyan taqiqlanadi). Ilmiy atama birinchi marta qalin."),
    "magistr": ("MAGISTRATURA: bakalavrdagidek ilmiy chuqurlik, qo‘shimcha: zamonaviy tadqiqotlar va yo‘nalishlar, ilmiy muammo va "
                "gipoteza, tadqiqot metodlari (kuzatish, eksperiment, so‘rovnoma, statistik tahlil), xalqaro tajriba (PISA, PIRLS, TIMSS "
                "kabi — mavzuga aloqador bo‘lsa), munozarali masalalar. Adabiyotlar: haqiqiy monografiya va maqolalar, aniq "
                "bilmasang yozma."),
}


def profil_matni(fan: str, sinf: str = "", daraja: str = "") -> str:
    k = fan_kaliti(fan)
    turlar, izoh = PROFIL.get(k, PROFIL["umumiy"])
    return (f"FAN PROFILI ({k}): eng foydali element turlari — {turlar}. {izoh}\n"
            f"YOSH: {YOSH[yosh_bandi(sinf, daraja)]}")

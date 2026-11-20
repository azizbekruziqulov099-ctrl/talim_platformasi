"""Xalqaro baholash kurs tuzilmasi: dastur → BO'LIMLAR (10–15) → MAVZULAR (har birida dars + 30 mashq + 30 test).
Kodda berilgan bo'limlar (BOLIMLAR) ustun; berilmagan dasturlar uchun eski «bolim» maydoni bo'yicha avtomatik guruhlanadi."""

ETIKET = {"PIRLS_4": "PIRLS 4", "P_M": "PISA mat", "P_S": "PISA fan", "P_R": "PISA o‘qish", "P_F": "PISA moliya", "T11_G4_M": "TIMSS 4 mat",
          "T11_G8_M": "TIMSS 8 mat", "T11_G4_S": "TIMSS 4 fan", "T11_G8_S": "TIMSS 8 fan"}   # Miya Excel mavzu nomi: «<nom> (<etiket>)»


def miya_nomi(nom, toplam):
    return f"{nom} ({ETIKET[toplam]})" if toplam in ETIKET else nom


BOLIMLAR = {
    "T11_G8_M": [
        {"kalit": "T8-1", "nom": "Natural sonlar va daraja", "belgi": "🔢", "izoh": "Amallar, daraja, kvadrat ildiz", "mavzular": ["M8-NAT", "t8_daraja"]},
        {"kalit": "T8-2", "nom": "Bo‘linish, EKUB va EKUK", "belgi": "🔗", "izoh": "Bo‘linish belgilari, umumiy bo‘luvchi va karrali", "mavzular": ["t8_bolinish"]},
        {"kalit": "T8-3", "nom": "Kasrlar va o‘nli kasrlar", "belgi": "🍕", "izoh": "Kasrlar bilan amallar", "mavzular": ["M8-KAS"]},
        {"kalit": "T8-4", "nom": "Butun sonlar", "belgi": "🌡️", "izoh": "Manfiy sonlar, amallar tartibi", "mavzular": ["M8-BUT", "t8_butun"]},
        {"kalit": "T8-5", "nom": "Nisbat, proporsiya va foiz", "belgi": "💯", "izoh": "Foiz, chegirma, proporsionallik, masshtab", "mavzular": ["M8-NIS", "t8_foiz", "t8_prop"]},
        {"kalit": "T8-6", "nom": "Qonuniyatlar va ketma-ketliklar", "belgi": "🔁", "izoh": "n-had formulasi", "mavzular": ["M8-QON", "t8_progressiya"]},
        {"kalit": "T8-7", "nom": "Algebraik ifodalar", "belgi": "🔤", "izoh": "Ixchamlash, qavslarni ochish", "mavzular": ["M8-IFO", "t8_ifoda"]},
        {"kalit": "T8-8", "nom": "Tenglamalar va funksiyalar", "belgi": "📈", "izoh": "Chiziqli tenglama, y = kx + b", "mavzular": ["M8-TEN", "t8_tenglama", "t8_funk"]},
        {"kalit": "T8-9", "nom": "Geometrik shakllar", "belgi": "🔺", "izoh": "Burchaklar, uchburchak, Pifagor", "mavzular": ["M8-SHA", "t8_uchburchak"]},
        {"kalit": "T8-10", "nom": "Geometrik o‘lchash", "belgi": "⭕", "izoh": "Perimetr, yuza, aylana va doira", "mavzular": ["M8-OLC", "t8_aylana"]},
        {"kalit": "T8-11", "nom": "Koordinatalar", "belgi": "🧭", "izoh": "Koordinatalar tekisligi, almashtirishlar", "mavzular": ["M8-JOY", "t8_koord"]},
        {"kalit": "T8-12", "nom": "Ma’lumotlar", "belgi": "📊", "izoh": "Tartiblash, o‘rtacha, mediana, moda", "mavzular": ["M8-TAS", "M8-TAH", "t8_stat"]},
        {"kalit": "T8-13", "nom": "Ehtimollik", "belgi": "🎲", "izoh": "Oddiy hodisa ehtimoli", "mavzular": ["M8-EHT", "t8_ehtimol"]},
    ],
    "T11_G4_M": [
        {"kalit": "T4-1", "nom": "Sonlar va xonalar", "belgi": "🔢", "izoh": "Ko‘p xonali sonlar, taqqoslash", "mavzular": ["M4-NAT", "t4_xona"]},
        {"kalit": "T4-2", "nom": "Qo‘shish va ayirish", "belgi": "➕", "izoh": "Ustun usuli, tekshirish", "mavzular": ["t4_ustun"]},
        {"kalit": "T4-3", "nom": "Ko‘paytirish va bo‘lish", "belgi": "✖️", "izoh": "Jadval, qoldiqli bo‘lish", "mavzular": ["t4_kopay", "t4_bolish"]},
        {"kalit": "T4-4", "nom": "Matnli masalalar", "belgi": "📖", "izoh": "Tenglik, noma’lum son, ikki amalli masala", "mavzular": ["M4-TEN", "t4_masala"]},
        {"kalit": "T4-5", "nom": "Kasrlar", "belgi": "🍕", "izoh": "Kasr tushunchasi, taqqoslash, qo‘shish", "mavzular": ["M4-KAS", "t4_kasr"]},
        {"kalit": "T4-6", "nom": "O‘nli kasrlar va pul", "belgi": "💲", "izoh": "O‘ndan va yuzdan bir, pul, uzunlik", "mavzular": ["t4_onli"]},
        {"kalit": "T4-7", "nom": "Qonuniyatlar", "belgi": "🔁", "izoh": "Ketma-ketlik qoidasi", "mavzular": ["M4-QON", "t4_qonun"]},
        {"kalit": "T4-8", "nom": "Chiziq, burchak va shakllar", "belgi": "📐", "izoh": "Burchak turlari, tekis va fazoviy shakllar", "mavzular": ["M4-NUQ", "t4_burchak", "M4-SHA"]},
        {"kalit": "T4-9", "nom": "O‘lchash: perimetr, yuza, vaqt", "belgi": "📏", "izoh": "To‘rtburchak, vaqt va birliklar", "mavzular": ["t4_perim", "t4_vaqt"]},
        {"kalit": "T4-10", "nom": "Ma’lumotlar", "belgi": "📊", "izoh": "Jadval, diagramma, tartiblash", "mavzular": ["M4-OQI", "t4_jadval", "M4-TAS"]},
    ],
    "P_M": [
        {"kalit": "PM-1", "nom": "Sonlar va hisoblash", "belgi": "🔢", "izoh": "Manfiy sonlar, kasrlar, daraja, yaxlitlash",
         "mavzular": ["pm_butun", "pm_kasr", "pm_daraja", "pm_taxmin"]},
        {"kalit": "PM-2", "nom": "Foiz va ulush", "belgi": "💯", "izoh": "Chegirma, soliq, foiz o‘zgarishi, doira diagrammasi",
         "mavzular": ["pisa_foiz", "pm_ulush", "pm_foizqayta"]},
        {"kalit": "PM-3", "nom": "Nisbat va proporsiya", "belgi": "⚖️", "izoh": "Masshtab, proporsionallik, aralashma",
         "mavzular": ["pisa_nisbat", "pm_proporsiya", "pm_aralashma"]},
        {"kalit": "PM-4", "nom": "Birliklar va vaqt", "belgi": "📏", "izoh": "Uzunlik, massa, hajm birliklari; vaqt va jadval",
         "mavzular": ["pm_birlik", "pm_vaqt"]},
        {"kalit": "PM-5", "nom": "Algebra: ifoda, tenglama, tengsizlik", "belgi": "🔤", "izoh": "Formulalar, tenglama tuzish, chegara masalalari",
         "mavzular": ["pm_ifoda", "pm_tenglama", "pm_tengsizlik"]},
        {"kalit": "PM-6", "nom": "Chiziqli bog‘lanish va tezlik", "belgi": "📈", "izoh": "Tarif, yo‘l, grafik, tarifni taqqoslash",
         "mavzular": ["pisa_chiziqli", "pisa_tezlik", "pm_tarif"]},
        {"kalit": "PM-7", "nom": "Qonuniyat va modellar", "belgi": "🦠", "izoh": "Ketma-ketlik, parabola, tez o‘sish va kamayish",
         "mavzular": ["pisa_ketma", "pm_kvadrat", "pm_eksp"]},
        {"kalit": "PM-8", "nom": "Yuza, perimetr va qoplash", "belgi": "🧱", "izoh": "To‘siq, plitka, bo‘yoq, murakkab shakllar",
         "mavzular": ["pm_perimetr", "pisa_yuza", "pm_yuza2", "pm_qoplash"]},
        {"kalit": "PM-9", "nom": "Hajm va sirt", "belgi": "📦", "izoh": "Quti, silindr, hovuz, qadoq",
         "mavzular": ["pm_hajm", "pm_sirt"]},
        {"kalit": "PM-10", "nom": "Geometriya: Pifagor, burchak, trigonometriya", "belgi": "📐", "izoh": "O‘xshashlik, Pifagor, burchaklar, sinus-kosinus",
         "mavzular": ["pisa_geometriya", "pm_burchak", "pm_pifagor", "pm_trig"]},
        {"kalit": "PM-11", "nom": "Ma’lumotlar va statistika", "belgi": "📊", "izoh": "Diagramma, jadval, o‘rtacha, mediana",
         "mavzular": ["pisa_malumot", "pisa_diagramma", "pm_ortacha"]},
        {"kalit": "PM-12", "nom": "Ehtimollik va sanash", "belgi": "🎲", "izoh": "Ehtimol, variantlar soni, xavf va qaror",
         "mavzular": ["pm_ehtimol", "pm_sanash", "pm_tavakkal"]},
        {"kalit": "PM-13", "nom": "Moliya va hayotiy qarorlar", "belgi": "🏦", "izoh": "Byudjet, xarid, kredit, jamg‘arma",
         "mavzular": ["pisa_pul", "pm_byudjet2", "pm_kredit"]},
    ],
}


def tuzilma(toplam, MAVZULAR, SH):
    """[{kalit, nom, belgi, izoh, mavzular:[{kod, nom, belgi, maqsad}]}] — faqat generatori bor mavzular."""
    out = []
    if toplam in BOLIMLAR:
        for b in BOLIMLAR[toplam]:
            ms = [k for k in b["mavzular"] if k in MAVZULAR and k in SH]
            if ms:
                out.append({**{x: b[x] for x in ("kalit", "nom", "belgi", "izoh")}, "mavzular": ms})
    else:
        gr = {}
        for k, m in MAVZULAR.items():
            if m.get("toplam") == toplam and k in SH:
                gr.setdefault(m.get("bolim") or k, []).append(k)
        for kal, ms in gr.items():
            m0 = MAVZULAR[ms[0]]
            out.append({"kalit": kal, "nom": m0["nom"] if len(ms) == 1 else m0.get("soha", kal), "belgi": m0.get("belgi", "📘"), "izoh": m0.get("maqsad", ""), "mavzular": ms})
    return out

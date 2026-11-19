"""Xalqaro baholash kurs tuzilmasi: dastur → BO'LIMLAR (10–15) → MAVZULAR (har birida dars + 30 mashq + 30 test).
Kodda berilgan bo'limlar (BOLIMLAR) ustun; berilmagan dasturlar uchun eski «bolim» maydoni bo'yicha avtomatik guruhlanadi."""

BOLIMLAR = {
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

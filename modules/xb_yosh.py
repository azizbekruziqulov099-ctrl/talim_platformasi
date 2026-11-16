"""Xalqaro baholash: o'quvchi yoshiga mos yo'nalishlar (hech qachon noto'g'ri yoshga chiqmaydi).

TIMSS 4-sinf ≈ 10 yosh, TIMSS 8-sinf ≈ 14 yosh, PISA — 15 yosh. Shunga ko'ra (yoshi to'lgan yil bilan):
  7–11  → TIMSS 4-sinf (matematika, tabiiy fan)
  12–14 → TIMSS 8-sinf (matematika, tabiiy fan)
  15+   → PISA (matematika, tabiiy fan, o'qish, moliya)
7 yoshdan kichik — yo'nalish yo'q. PISA 15 yoshgacha, 4-sinf TIMSS 12 yoshdan keyin ko'rsatilmaydi.
Test tartibi: avval matematika, keyin tabiiy fan, keyin o'qish, keyin moliya (chalg'itmaslik uchun ketma-ket)."""
from datetime import date

TIMSS4 = ("T11_G4_M", "T11_G4_S")
TIMSS8 = ("T11_G8_M", "T11_G8_S")
PISA = ("P_M", "P_S", "P_R", "P_F")
HAMMASI = TIMSS4 + TIMSS8 + PISA
NOMI = {"T11_G4_M": "TIMSS 4-sinf · Matematika", "T11_G4_S": "TIMSS 4-sinf · Tabiiy fan",
        "T11_G8_M": "TIMSS 8-sinf · Matematika", "T11_G8_S": "TIMSS 8-sinf · Tabiiy fan",
        "P_M": "PISA · Matematik savodxonlik", "P_S": "PISA · Tabiiy fan savodxonligi",
        "P_R": "PISA · O‘qish savodxonligi", "P_F": "PISA · Moliyaviy savodxonlik"}
SINF_RAQAMI = {"T11_G4_M": 4, "T11_G4_S": 4, "T11_G8_M": 8, "T11_G8_S": 8, "P_M": 9, "P_S": 9, "P_R": 9, "P_F": 9}
ENG_KICHIK_YOSH = 7


def yosh_hisobla(tugilgan, bugun=None):
    """To'lgan yosh. tugilgan — date yoki 'YYYY-MM-DD'; noto'g'ri bo'lsa None."""
    try:
        t = tugilgan if isinstance(tugilgan, date) else date.fromisoformat(str(tugilgan)[:10])
    except (TypeError, ValueError):
        return None
    b = bugun or date.today()
    if t > b:
        return None
    return b.year - t.year - ((b.month, b.day) < (t.month, t.day))


def yonalishlar(yosh):
    """Yoshga mos yo'nalishlar (tartib bilan). Yosh noma'lum yoki juda kichik — bo'sh ro'yxat."""
    if yosh is None or yosh < ENG_KICHIK_YOSH or yosh > 120:
        return []
    if yosh <= 11:
        return list(TIMSS4)
    if yosh <= 14:
        return list(TIMSS8)
    return list(PISA)


def ruxsat_etilgan(yosh, tanlangan):
    """Tanlangan yo'nalishlardan faqat yoshiga mosi, tartibi bilan; qolgani tashlanadi."""
    mos = yonalishlar(yosh)
    return [t for t in mos if t in set(tanlangan or [])]

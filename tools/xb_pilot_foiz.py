"""Namuna (pilot): PISA matematika «Foiz va chegirma» — yangi usulda: muammo -> kashfiyot -> chizma -> usullar -> xato tahlili -> mustaqil ish.
Ishlatish: python tools/xb_pilot_foiz.py CHIQISH_PAPKA"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.ai_miya_varoq import template_workbook, parse_sheets
from tools import miya_xb_eksport as E

DARS = [
 {"turi": "kirish", "sarlavha": "Qaysi chegirma yaxshi?",
  "matn": "[1] Tasavvur qiling... do‘konda ikkita e’lon bor. [2] Birinchisida: «Hamma narsaga 20 foiz chegirma, ustiga yana 10 foiz». [3] Ikkinchisida: «30 foiz chegirma». Qaysi biri foydali? ... Hali hisoblamang! Avval o‘ylab, taxmin qiling. [4] Dars oxirida taxminingiz to‘g‘ri chiqdimi — o‘zingiz tekshirasiz.",
  "doska": "BELGILA: 20% + yana 10% | aylana\nBELGILA: 30% | ramka\nSavol: qaysi biri arzonroq?\nTaxmin qiling ✋"},
 {"turi": "tushuncha", "sarlavha": "Foiz — yuzdan bir bo‘lak",
  "matn": "[1] «Foiz» so‘zi — «yuzga» degani. [2] Butun narsani yuzta teng bo‘lakka bo‘lamiz. [3] Bitta bo‘lak — bir foiz. [4] Yigirma besh bo‘lak — yigirma besh foiz. [5] Qarang: bu butunning aynan to‘rtdan biri! [6] Demak, yigirma besh foiz va bir bo‘lak to‘rtdan bir — ikkalasi bitta narsa.",
  "doska": "QOIDA: 1% = 1/100 butun\nDOIRA_KASR: 1/4\n25% = 25/100 = 1/4\nBELGILA: 50% = 1/2 | tag\n10% = 1/10",
  "sodda": "Foiz — butunni 100 ga bo‘lib, kerakli bo‘lagini olish.", "boshqa_usul": "Foizni kasr yoki o‘nli kasr deb o‘qing: 25% = 1/4 = 0,25.",
  "tekshiruv": "50% butunning nechadan bir qismi? => 1/2|2da 1"},
 {"turi": "tushuncha", "sarlavha": "Hisoblashning uchta oson yo‘li",
  "matn": "[1] Kalkulyator yo‘q deylik. Foizni boshda hisoblash mumkin. [2] Birinchi yo‘l: o‘n foiz — o‘nga bo‘lamiz. Ikki yuz so‘mning o‘n foizi — yigirma. [3] Ikkinchi yo‘l: ellik foiz — ikkiga bo‘lamiz. [4] Uchinchi yo‘l: boshqa foizlarni bo‘laklab yig‘amiz. Yigirma besh foiz — ikki marta o‘n foiz va yarim o‘n foiz. [5] Qarang, hammasi bir xil mantiq: kichik bo‘lakni topamiz, keyin ko‘paytiramiz.",
  "doska": "QOIDA: 10% → 10 ga bo‘l\nBOLISH: 200:10\n50% → 2 ga bo‘l\nKETMA: 25% | 10%+10%+5% | 20+20+10 | 50\nBELGILA: kichik bo‘lak → keyin ko‘paytir | ramka",
  "tekshiruv": "400 ning 10% i nechiga teng? => 40"},
 {"turi": "tushuncha", "sarlavha": "Chegirma — kamayish, ustiga qo‘shilmaydi",
  "matn": "[1] Ko‘ylak 80 ming so‘m. Chegirma — 25 foiz. [2] Avval chegirma qancha ekanini topamiz: seksonning to‘rtdan biri. [3] Bu yigirma ming. [4] Endi narxdan ayiramiz: sakson minus yigirma. [5] To‘lanadigan narx — oltmish ming. [6] Yoki tezroq: 25 foiz arzon bo‘lsa, 75 foizini to‘laymiz!",
  "doska": "Narx: 80 000\nChegirma 25% = 80 000 : 4 = 20 000\nUSTUN: 80000-20000\nQOIDA: To‘lov = 100% − chegirma% = 75%\n80 000 · 0,75 = 60 000",
  "tekshiruv": "Narx 200, chegirma 10%. Necha to‘laymiz? => 180"},
 {"turi": "tushuncha", "sarlavha": "Xato tuzog‘i: 20% + 10% ≠ 30%",
  "matn": "[1] Endi boshlang‘ich savolga qaytamiz. Narx yuz ming so‘m deylik. [2] Birinchi chegirma — yigirma foiz. Yigirma ming arzonlashdi, qoldi sakson ming. [3] Ikkinchi chegirma — o‘n foiz. Lekin nimaning o‘n foizi? Yangi narxning! Sakson mingning o‘n foizi — sakkiz ming. [4] Qoldi — yetmish ikki ming. [5] Ikkinchi e’londa esa o‘ttiz foiz — yetmish ming. [6] Ko‘rdingizmi? Ikkinchi e’lon foydaliroq. Chunki ikkinchi foiz kichraygan narxdan olinadi.",
  "doska": "Boshlang‘ich narx: 100 000\n−20% → 100 000 · 0,8 = 80 000\n−10% → 80 000 · 0,9 = 72 000\n30% chegirma → 100 000 · 0,7 = 70 000\nBELGILA: 72 000 ≠ 70 000 | aylana\nQOIDA: Foizlar qo‘shilmaydi — ko‘paytiriladi: 0,8 · 0,9 = 0,72",
  "tekshiruv": "100 ga 10% oshirsak, keyin 10% kamaytirsak necha bo‘ladi? => 99"},
 {"turi": "xulosa", "sarlavha": "Esda tut",
  "matn": "Birinchi: foiz — yuzdan bo‘lak. Ikkinchi: o‘n foizdan boshlang — qolganini bo‘laklab yig‘ing. Uchinchi: chegirmada to‘lov — yuz foizdan chegirma foizini ayirib topiladi. To‘rtinchi: ketma-ket foizlar qo‘shilmaydi, ko‘paytiriladi. Endi mashqda sinab ko‘ring!",
  "doska": "1. 1% = 1/100\n2. 10% → 10 ga bo‘l\n3. To‘lov = (100 − chegirma)%\n4. Ketma-ket foiz → ko‘paytir"},
]

def main(out):
    os.makedirs(out, exist_ok=True)
    k = "pisa_foiz"
    rows = [dict(r) for r in DARS]
    rows += E.savol_qatorlari(k, "mashq", "", "S") + E.savol_qatorlari(k, "test", "", "S")
    book = {"kitob_nomi": "Xalqaro baholash — namuna (Foiz)", "fan": "Matematika", "sinf": "PISA", "kitob_kodi": "XB-PILOT", "til": "uz", "kod_prefiksi": "XPM", "mualliflar": "Kabutar Ta’lim"}
    wb = template_workbook(prefill=[{"mavzu_kodi": "", "mavzu_nomi": "Foiz va chegirma (PISA mat)", "mavzu_raqami": "1", "rows": rows}], book=book)
    p = os.path.join(out, "miya_pilot_foiz.xlsx"); wb.save(p)
    import openpyxl
    r = parse_sheets(openpyxl.load_workbook(p)); print(r.get("errors") or "xato yo'q", len(rows), "qator"); return p

if __name__ == "__main__":
    main(sys.argv[1])

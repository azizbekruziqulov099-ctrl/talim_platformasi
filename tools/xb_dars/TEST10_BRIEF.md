# Har darsda 10 ta test (Xalqaro baholash darslari)
Foydalanuvchi talabi: HAR DARS oxirida 10 ta test (TEKSH). Hozir ko'p darsda 4–6 ta. Sening vazifang: berilgan .txt fayllardagi HAR dars (## kod) uchun jami TEKSH sonini kamida 10 ga yetkaz.
Format (loader.py ni o'qi): `TEKSH: savol => to'g'ri | xato | xato` (birinchi variant TO'G'RI; 3–4 variant). TEKSH qatorlari @tushuncha / @xulosa qadamlariga qo'yiladi (qadam boshiga 1–3 ta).
Sifat qoidalari:
- Yangi savollar dars mazmunini qamrasin: tushunish, qo'llash, xatoni topish, hayotiy masala; qiyinlik ketma-ket oshsin (oson→o'rta→qiyin); TIMSS/PISA/PIRLS uslubiga mos.
- Savol darsda ishlangan misolning AYNAN o'zi bo'lmasin (loader.tekshir buni tutadi); sonlarni o'zgartir.
- Har savolda yagona to'g'ri javob; xato variantlar ishonarli (tipik xatolar: ishora, o'rin almashtirish...). Hisob-kitoblarni o'zing python bilan tekshir.
- O'zbekcha, alifbo: o', g', sh, ch oddiy (mavjud fayllar uslubida). Mavjud TEKSH, OVOZ, DOSKA qatorlarini BUZMA.
Tekshiruv: `cd /home/claude/talim_platformasi && python3 -c "import sys;sys.path.insert(0,'.');from tools.xb_dars import loader;r=loader.oqi(open('tools/xb_dars/FAYL.txt',encoding='utf-8').read());[print(k,e) for k,q in r.items() for e in loader.tekshir(k,q)]"` — hech narsa chiqmasin (0 xato). Commit QILMA. Hisobot: nechta TEKSH qo'shilgani, shubha.

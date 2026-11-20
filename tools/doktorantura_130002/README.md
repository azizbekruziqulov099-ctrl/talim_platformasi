# 13.00.02 — tayanch doktorantura (Kabu darslari va testlari)

Imtihonning 328 savoli (7 bo'lim) bo'yicha qisqa darslar va Kabu testlari shu yerdan yasaladi.

- `data/s1.txt … s7.txt` — sxema: `raqam | savol | KOD | mag'iz (**bosh harflar**) | bog'liq savollar`
- `darslar/s<n>.txt` — dars matnlari (format `build_miya.py` boshida yozilgan). Bitta savol 1–3 ta qisqa darsga
  bo'linadi: `### 1.1-a | Sarlavha`, bo'linmagani `### 1.2`. Har darsda 2–5 qadam, 5–6 test (oson → qiyin).
- `python3 build_miya.py` → `out/13_00_02_doktorantura_paket.zip` (Admin → «Paketni birdan o'rnatish»).
  Faqat yozilgan darslar mavzular ro'yxatiga kiradi; tekshiruv xatolari konsolga chiqadi.
- `python3 build.py` — qog'ozga yodlash sxemasi (HTML → PDF).

Saytda: Kurslar → Oliy ta'lim kurslari → «13.00.02 … · Doktorantura». Dars testidan 70% olinmaguncha keyingi dars
yopiq; har 5 darsda mini-test, bo'lim oxirida 30 savollik bo'lim testi, oxirida yakuniy imtihon (modules/kurslar.py, REV470).

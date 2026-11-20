# 13.00.02 — tayanch doktorantura (Kabu darslari va testlari)

Imtihonning 328 savoli (7 bo'lim). **Bir bo'lim = bitta dars**: darsda bo'limning barcha savollari savol tartibida
(kod → mag'iz → qisqa tushuntirish), har 10 savoldan keyin «Esda tut», oxirida bo'limning barcha testlari (100–150 ta).

- `data/s1.txt … s7.txt` — sxema: `raqam | savol | KOD | mag'iz (**bosh harflar**) | bog'liq savollar`
- `darslar_mavzu/s<n>*.txt` — savollar matni va testlari (format `build_dars.py` boshida).
- `python3 build_dars.py [1 2 …]` → `out/13_00_02_doktorantura_paket.zip` (Admin → «Paketni birdan o'rnatish»).
- `python3 build.py` — qog'ozga yodlash sxemasi (HTML → PDF).

Saytda: Kurslar → Oliy ta'lim kurslari → «13.00.02 … · Doktorantura». Dars testidan 70% olinmaguncha keyingi bo'lim
yopiq; har bo'limdan keyin 30 savollik bo'lim testi, oxirida yakuniy imtihon (modules/kurslar.py, dars_xonasi.py REV470).

"""REV515: mantiqsiz kirish/tushuncha qatorlarini tuzatish («12 olma va undan 4 ta ko‘p nok: jami 28 meva. Avval nima topiladi?»).
Kirish — shu darsning birinchi namunaviy misoli bilan (mavzuga mos), tushuncha — to'g'ri tuzilgan ikki bosqichli masala bilan."""
import re, sys
from openpyxl import load_workbook

YOMON = "28 meva"
TUSH_E = ("Ikki bosqichli masalada savolga darhol javob topilmaydi — avval yordamchi miqdor topiladi. [1] Masalan: Alida 12 ta olma bor, "
          "nok esa olmadan 4 ta ko‘p. Ikkalasi jami nechta meva? Avval nok sonini topamiz: 12 + 4 = 16, keyin jami: 12 + 16 = 28.")
TUSH_F = "Ikki amalli masalalar\nOlma: 12\nNok: 12 + 4 = 16\nJami: 12 + 16 = 28"
TUSH_N = "Alida 12 olma bor, nok olmadan 4 ta ko‘p. Jami nechta mevani bilish uchun avval nimani topamiz? => Nok sonini: 12 + 4 = 16"


def tuzat(manba, chiqish):
    wb = load_workbook(manba); n = 0
    for ws in wb.worksheets[2:]:
        nom = ws.cell(2, 7).value
        misol = None
        for r in range(7, ws.max_row + 1):
            if ws.cell(r, 2).value == "misol":
                y = str(ws.cell(r, 10).value or ""); m = re.search(r"Javob:\s*(.+)$", y)
                misol = (ws.cell(r, 5).value, (m.group(1).strip("$ ") if m else "")); break
        for r in range(7, ws.max_row + 1):
            matn = " ".join(str(ws.cell(r, c).value or "") for c in range(1, 15))
            if YOMON not in matn and "Avval nima topiladi" not in matn:
                continue
            tur = ws.cell(r, 2).value
            if tur == "kirish" and misol:
                ws.cell(r, 5).value = f"Bugungi mavzu: {nom}. [1] Keling, bitta savoldan boshlaymiz: {misol[0]}"
                ws.cell(r, 6).value = misol[0]
                ws.cell(r, 14).value = f"{misol[0]} => {misol[1]}" if misol[1] else None
            else:
                ws.cell(r, 5).value = TUSH_E; ws.cell(r, 6).value = TUSH_F; ws.cell(r, 14).value = TUSH_N
            n += 1
    wb.save(chiqish)
    return n

if __name__ == "__main__":
    print(tuzat(sys.argv[1], sys.argv[2]), "qator tuzatildi")

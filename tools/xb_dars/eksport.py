"""Ishlatish: python -m tools.xb_dars.eksport DASTUR fayl1.txt [fayl2.txt ...] CHIQISH_PAPKA
Faqat DARS (mashq va test darsda chiqmaydi — kursda alohida, dars ko'rilgach)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules import pisa_mat as P, xb_kurs as XK
from modules.ai_miya_varoq import template_workbook, parse_sheets
from tools import miya_xb_eksport as E
from tools.xb_dars import loader


def main(dastur, fayllar, out):
    mav = loader.oqi("\n".join(open(f, encoding="utf-8").read() for f in fayllar))
    fan, sinf = E.FAN.get(dastur, (dastur, "kurs"))
    tz = XK.BOLIMLAR.get(dastur)
    tartib = [m for b in tz for m in b["mavzular"]] if tz else []
    pre, xato = [], 0
    for k in tartib:
        if k not in mav: continue
        for e in loader.tekshir(k, mav[k]): print("XATO", k, e); xato += 1
        nom = P.MAVZULAR[k]["nom"] if k in P.MAVZULAR else k
        pre.append({"mavzu_kodi": "", "mavzu_nomi": f"{nom} ({E.ETIKET.get(dastur, dastur)})", "mavzu_raqami": str(len(pre) + 1), "rows": loader.qatorlar(mav[k])})
    book = {"kitob_nomi": f"Xalqaro baholash — {fan}, {sinf} (darslar)", "fan": fan, "sinf": sinf, "kitob_kodi": f"XB-{dastur}", "til": "uz",
            "kod_prefiksi": E.PREF[dastur], "mualliflar": "Kabutar Ta’lim"}
    wb = template_workbook(prefill=pre, book=book)
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, f"miya_{dastur}_darslar.xlsx"); wb.save(p)
    import openpyxl
    r = parse_sheets(openpyxl.load_workbook(p))
    print(dastur, len(pre), "mavzu", "| sifat xatolari:", xato, "| Miya xatolari:", [e for e in r.get("errors", [])][:3])
    return p


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:-1], sys.argv[-1])

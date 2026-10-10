"""REV121: ommaviy paket — fayl turini ichidan aniqlash, tartib (avval mavzular), aniq belgi."""
import ast
import io
import os
import re
import zipfile
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
NAMES = {"_paket_belgi", "_paket_turi", "_paket_tartib", "_paket_zip_fayllar", "_ai_brain_xlsx_mi"}
CONSTS = {"PAKET_ZIP_MAX", "PAKET_FAYL_MAX", "PAKET_SONI_MAX", "PAKET_TURI_TARTIB", "PAKET_IZOH_NOMI", "AI_MEDIA_EXTENSIONS"}


class _HTTP(Exception):
    def __init__(self, status_code=0, detail=""):
        super().__init__(detail)
        self.status_code, self.detail = status_code, detail


def _funcs():
    """samtm_platform.py ni import qilmasdan (baza, fastapi kerak emas) kerakli funksiyalarni olamiz."""
    from modules import curriculum_scope
    g = {"io": io, "os": os, "re": re, "HTTPException": _HTTP, "_curriculum": curriculum_scope}
    tree = ast.parse((ROOT / "samtm_platform.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign) and any(getattr(t, "id", "") in CONSTS for t in node.targets)) or \
                (isinstance(node, ast.FunctionDef) and node.name in NAMES):
            exec(compile(ast.Module([node], []), "samtm_platform.py", "exec"), g)
    return g


def _xlsx(fill):
    wb = openpyxl.Workbook()
    fill(wb)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_turi_ichidan_aniqlanadi_va_tartib():
    g = _funcs()
    mavzu = _xlsx(lambda wb: wb.active.append(["Sinf", "Fan", "Chorak", "Bob", "Bo'lim", "Mavzu", "Kichik mavzu"]))
    miya = _xlsx(lambda wb: setattr(wb.active, "title", "KITOB"))
    assert g["_paket_turi"](mavzu, "x.xlsx") == "mavzu"
    assert g["_paket_turi"](miya, "y.xlsx") == "miya"
    assert g["_paket_turi"](mavzu, "fan_rasmlar_royxati.xlsx") == "royxat"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("paket/mantiq/mantiq_2-3_yosh_2_ai_miya.xlsx", miya)
        z.writestr("paket/mantiq/mantiq_2-3_yosh_1_mavzular.xlsx", mavzu)
        z.writestr("paket/mantiq/mantiq_rasmlar_royxati.xlsx", mavzu)
        z.writestr("__MACOSX/._x.xlsx", b"junk")
    buf.seek(0)
    items = [{"nomi": n, "yol": d, "turi": g["_paket_turi"](b, n)} for n, d, b in g["_paket_zip_fayllar"](buf)]
    items.sort(key=g["_paket_tartib"])
    assert [i["turi"] for i in items] == ["mavzu", "miya", "royxat"]


def test_belgi():
    g = _funcs()
    assert g["_paket_belgi"]("ingliz_tili_izoh_ru_4-5_yosh_2_ai_miya.xlsx") == "Ingliz tili · izoh rus · 4-5 yosh · miya"
    assert g["_paket_belgi"]("atrof-muhit_2-3_yosh_1_mavzular.xlsx") == "Atrof-muhit · 2-3 yosh · mavzular"

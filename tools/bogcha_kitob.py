"""REV80: bog'cha kitobi (JSON) → platformaga yuklanadigan fayllar.

Chiqadi (har yosh guruhi uchun):
  1) <fan>_<yosh>_mavzular.xlsx — Mavzular importi (Admin → Mavzular → Import, dastur: «Bog'cha — umumiy katalog»)
  2) <fan>_<yosh>_ai_miya.xlsx  — AI miya kitobi (Admin → Shablon → Kitob darslari)
Hamma yosh uchun bitta:
  3) <fan>_rasmlar_royxati.xlsx — kerakli rasmlar: fayl nomi + GPT uchun tayyor buyruq

Ishlatish:  python tools/bogcha_kitob.py <chiqish_papka> <fan nomi> <prefiks> kitob1.json kitob2.json ...
Masalan:    python tools/bogcha_kitob.py out "Ingliz tili" EN en_34.json en_45.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.ai_miya_varoq import template_workbook  # noqa: E402

STYLE = "cute cartoon, soft flat colors, white background, no text, square 1024x1024"


def age_short(age):
    return "".join(ch for ch in age if ch.isdigit())[:2]


def topics_workbook(book, fan):
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mavzular"
    ws.append(["Sinf", "Fan", "Chorak", "Bob", "Bo'lim", "Mavzu", "Kichik mavzu"])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="173B57")
    for topic in book["topics"]:
        ws.append([book["age"], fan, 1, book.get("book_title", fan), "", topic["name"], ""])
    for col, width in zip("ABCDEFG", (12, 16, 8, 30, 10, 36, 14)):
        ws.column_dimensions[col].width = width
    return wb


def ai_workbook(book, fan, prefix):
    prefill = []
    for topic in book["topics"]:
        rows = []
        for row in topic["rows"]:
            rows.append({
                "turi": row.get("turi", ""), "sarlavha": row.get("sarlavha", ""), "matn": row.get("matn", ""),
                "doska": row.get("doska", ""), "variantlar": row.get("variantlar", ""), "javob": row.get("javob", ""),
                "yechim": row.get("yechim") or ("Barakalla! Juda yaxshi bajardingiz! 🌟" if row.get("turi") == "topshiriq" else ""),
                "sodda": row.get("sodda", ""), "boshqa_usul": row.get("boshqa_usul", ""),
            })
        prefill.append({"mavzu_kodi": "", "mavzu_nomi": topic["name"], "mavzu_raqami": topic["no"], "daraja": 1, "rows": rows})
    meta = {"kitob_nomi": book.get("book_title") or f"{fan} {book['age']}", "fan": fan, "sinf": book["age"],
            "til": "uz", "kod_prefiksi": f"{prefix}{age_short(book['age'])}", "mualliflar": "Kabutar Ta'lim"}
    return template_workbook(prefill, meta, blank_topics=0)


def images_workbook(books, fan):
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Rasmlar"
    ws.append(["Yosh", "Mavzu", "Fayl nomi", "Nima", "Emoji (hozircha)", "GPT uchun buyruq (inglizcha)", "Tayyor?"])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="173B57")
    seen = set()
    for book in books:
        for topic in book["topics"]:
            if topic.get("image_scene"):
                ws.append([book["age"], topic["name"], topic["image_scene"], "Mavzu sahnasi", "",
                           topic.get("image_scene_prompt") or f"A cheerful scene for the lesson '{topic['name']}', {STYLE}", ""])
            for word in topic.get("words", []):
                if not word.get("image") or word["image"] in seen:
                    continue  # takror darslaridagi so'zlar ikkinchi marta yozilmaydi
                seen.add(word["image"])
                prompt = word.get("image_prompt") or f"{word.get('en')}, {STYLE}"
                ws.append([book["age"], topic["name"], word.get("image", ""), f"{word.get('en', '')} — {word.get('uz', '')}",
                           word.get("emoji", ""), prompt, ""])
    for col, width in zip("ABCDEFG", (10, 26, 30, 26, 10, 90, 9)):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        row[5].alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    return wb


def main(out, *args):
    """main(out, "Ingliz tili", "EN", a.json, ...) yoki main(out, a.json, b.json, ...) — fan va prefiks kitobdan."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fan = prefix = None
    if args and not str(args[0]).endswith(".json"):
        fan, prefix, args = args[0], args[1], args[2:]
    books = [json.loads(Path(f).read_text(encoding="utf-8")) for f in args]
    groups = {}
    for book in books:
        subject = fan or book.get("subject") or "Fan"
        groups.setdefault(subject, []).append(book)
    for subject, items in groups.items():
        slug = subject.lower().replace(" ", "_").replace("'", "").replace("‘", "")
        folder = out / slug
        folder.mkdir(parents=True, exist_ok=True)
        for book in items:
            a = age_short(book["age"])
            topics_workbook(book, subject).save(folder / f"{slug}_{a[0]}-{a[1]}_yosh_1_mavzular.xlsx")
            ai_workbook(book, subject, prefix or book.get("prefix") or "BK").save(folder / f"{slug}_{a[0]}-{a[1]}_yosh_2_ai_miya.xlsx")
        images_workbook(items, subject).save(folder / f"{slug}_rasmlar_royxati.xlsx")
    print("tayyor:", sorted(str(p.relative_to(out)) for p in out.rglob("*.xlsx")))


if __name__ == "__main__":
    main(*sys.argv[1:])

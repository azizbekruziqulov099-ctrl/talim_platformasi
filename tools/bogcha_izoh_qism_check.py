"""REV110: izoh tarjimasi qismini tekshirish. Ishlatish: python tools/bogcha_izoh_qism_check.py <ru|en> <A|B|C>"""
import json, re, sys
from pathlib import Path
D = Path(__file__).resolve().parent / "bogcha_content" / "izoh"
izoh, part = sys.argv[1], sys.argv[2]
src = json.loads((D / f"kerak_{part}.json").read_text(encoding="utf-8"))
path = D / f"qism_{izoh}_{part}.json"
t = json.loads(path.read_text(encoding="utf-8")).get("t", {}) if path.is_file() else {}
bad = []
for k, v in src.items():
    tr = t.get(k)
    if not tr or not str(tr).strip():
        bad.append(f"yo'q: {k} «{v['uz'][:50]}»"); continue
    if set(re.findall(r"\{[a-z_]+\}", v["uz"])) != set(re.findall(r"\{[a-z_]+\}", tr)):
        bad.append(f"{{…}} mos emas: {k} «{v['uz'][:40]}» → «{tr[:40]}»")
    if re.search(r"\[/?[a-z]{2}\]", tr):
        bad.append(f"teg bor: {k}")
    if izoh == "ru" and v["kind"] != "shablon" and re.search(r"\b(va|bilan|uchun|qani|barakalla|degani|ayt)\b", tr, re.I):
        bad.append(f"o'zbekcha qolgan?: {k} «{tr[:50]}»")
extra = [k for k in t if k not in src]
print(f"{izoh}/{part}: {len(src)} ta, muammo {len(bad)}, ortiqcha {len(extra)}")
print("\n".join(bad[:40]))

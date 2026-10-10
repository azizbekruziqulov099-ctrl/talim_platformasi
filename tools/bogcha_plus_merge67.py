"""REV110: 6-7 yosh plus faylining ikki qismini (A: 1-4 bo'lim, B: 5-7 bo'lim) birlashtiradi."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent / "bogcha_content"
parts = [p for p in ("A", "B") if (ROOT / f"en_67p_{p}.json").is_file()]
book, enr = None, {"lessons": {}, "scenarios": []}
for p in parts:
    b = json.loads((ROOT / f"en_67p_{p}.json").read_text(encoding="utf-8"))
    if book is None:
        book = b
    else:
        book["units"] += b["units"]
    e_path = ROOT / f"en_67p_{p}_enrich.json"
    if e_path.is_file():
        e = json.loads(e_path.read_text(encoding="utf-8"))
        enr["lessons"].update(e.get("lessons") or {})
        enr["scenarios"] += e.get("scenarios") or []
if book:
    (ROOT / "en_67p.json").write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "en_67p_enrich.json").write_text(json.dumps(enr, ensure_ascii=False, indent=1), encoding="utf-8")
print("qismlar:", parts)

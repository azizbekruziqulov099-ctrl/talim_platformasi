"""REV110: yangi tarjimalarni (tarjima/yangi_<til>.json) asosiy lug'atga (tarjima/<til>.json) qo'shadi va tekshiradi.

Ishlatish: python tools/bogcha_tarjima_merge.py <til>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.bogcha_tillar import TR_DIR, check  # noqa: E402

lang = sys.argv[1]
main_path, new_path = TR_DIR / f"{lang}.json", TR_DIR / f"yangi_{lang}.json"
data = json.loads(main_path.read_text(encoding="utf-8"))
new = json.loads(new_path.read_text(encoding="utf-8"))
src = json.loads((TR_DIR / "manba.json").read_text(encoding="utf-8"))["matnlar"]
added = 0
for part in ("t", "rom"):
    data.setdefault(part, {})
    for k, v in (new.get(part) or {}).items():
        if k in src and str(v).strip():
            added += k not in data[part]
            data[part][k] = v
main_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
probs = check(lang)
print(f"{lang}: qo'shildi {added}; muammo {len(probs)}")
print("\n".join(probs[:40]))

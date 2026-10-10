"""REV110: yangi «plus» darslarni tekshirish (en_23p, en_45p, en_67p + boyitish).

Ishlatish: python tools/bogcha_plus_check.py [reja_rasmli.json]
"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.bogcha_spiral import build_book, merge_enrich, validate  # noqa: E402

ROOT = Path(__file__).resolve().parent / "bogcha_content"
PLUS = {"23p": ("23", "2-3 yosh", 200, 2), "45p": ("45y", "4-5 yosh", 280, 2), "67p": ("67y", "6-7 yosh", 380, 3)}
PLAN_AGE = {"23p": "2-3", "45p": "4-5", "67p": "6-7"}
TAG = re.compile(r"\[en\]([\s\S]*?)\[/en\]")
BAD_UZ = re.compile(r"\b(siz|Siz|sizga|keling|Keling|Kabutar|Gu-gu)\b")
DIALOG_LEN = {"45p": (4, 5), "67p": (6, 8)}


def uz_parts(text):
    return TAG.sub(" ", str(text or ""))


def check_text(where, text, limit, errors):
    if not text:
        return
    if text.count("[en]") != text.count("[/en]"):
        errors.append(f"{where}: [en] teglari juft emas")
    if len(text) > limit:
        errors.append(f"{where}: {len(text)} belgi (chegara {limit})")
    if BAD_UZ.search(uz_parts(text)):
        errors.append(f"{where}: «siz/keling/Kabutar» ishlatilgan — «sen» va robot Kabu bo'lsin")
    if re.search(r"\b(the|and|you|is|are|my|I'm|Let's)\b", uz_parts(text)):
        errors.append(f"{where}: tegsiz inglizcha so'z bor — «{uz_parts(text)[:60]}»")


def check(key, plan):
    base_key, age, limit, nopt = PLUS[key]
    errors = []
    path = ROOT / f"en_{key}.json"
    if not path.is_file():
        return [f"{path.name} yo'q"]
    cur = json.loads(path.read_text(encoding="utf-8"))
    if cur.get("age") != age or cur.get("lang") != "en":
        errors.append(f"{key}: age/lang noto'g'ri")
    units = cur.get("units") or []
    want = plan[PLAN_AGE[key]]
    if [u["name"] for u in units] != [u["name"] for u in want]:
        errors.append(f"{key}: bo'limlar rejadagidek emas")
    base = json.loads((ROOT / f"en_{base_key}.json").read_text(encoding="utf-8"))
    base_names = {l["name"].lower() for u in base["units"] for l in u["lessons"] + (u.get("scenarios") or [])}
    for u, wu in zip(units, want):
        for les, wl in zip(u["lessons"], wu["lessons"]):
            w = f"{key} «{les.get('name')}»"
            if les.get("name") != wl["name"]:
                errors.append(f"{w}: nom rejada «{wl['name']}»")
            if les["name"].lower() in base_names:
                errors.append(f"{w}: asosiy kitobda shu nom bor")
            got = [(i.get("say"), i.get("image")) for i in les.get("items") or []]
            exp = [(i["say"], i["image"]) for i in wl["items"]]
            if got != exp:
                errors.append(f"{w}: items rejadagidek emas: {got} ≠ {exp}")
            for i in les.get("items") or []:
                if "[en]" in str(i.get("say")):
                    errors.append(f"{w}: say ichida teg bo'lmasin")
                if not i.get("image_prompt"):
                    errors.append(f"{w}: «{i.get('say')}» image_prompt yo'q")
                if key == "23p" and not i.get("action"):
                    errors.append(f"{w}: 2-3 yoshda har so'zga action kerak")
            check_text(w + " intro", les.get("intro"), limit, errors)
            if len(les.get("extra") or []) < 1:
                errors.append(f"{w}: extra qatori yo'q")
            for r in les.get("extra") or []:
                for k in ("matn", "sodda", "boshqa_usul"):
                    check_text(f"{w} extra.{k}", r.get(k), limit, errors)
                if not r.get("doska"):
                    errors.append(f"{w}: extra.doska yo'q")
            tests = les.get("tests") or []
            if len(tests) < 2:
                errors.append(f"{w}: kamida 2 ta test")
            for t in tests:
                check_text(f"{w} test", t.get("q"), limit, errors)
                check_text(f"{w} test.why", t.get("why"), limit, errors)
                if len(t.get("options") or []) != nopt:
                    errors.append(f"{w}: testda {nopt} ta variant bo'lsin")
    enr_path = ROOT / f"en_{key}_enrich.json"
    if key in ("45p", "67p"):
        if not enr_path.is_file():
            errors.append(f"{enr_path.name} yo'q")
        else:
            enr = json.loads(enr_path.read_text(encoding="utf-8"))
            sc = enr.get("scenarios") or []
            if sorted(s.get("unit") for s in sc) != list(range(1, len(units) + 1)):
                errors.append(f"{key}: har bo'limga bittadan vaziyat kerak (unit 1..{len(units)})")
            lo, hi = DIALOG_LEN[key]
            for s in sc:
                w = f"{key} vaziyat «{s.get('name')}»"
                if not lo <= len(s.get("dialog") or []) <= hi:
                    errors.append(f"{w}: dialog {lo}–{hi} qator")
                if not any(d.get("who") == 1 for d in s.get("dialog") or []):
                    errors.append(f"{w}: bolaning (who: 1) qatori yo'q")
                if s.get("name", "").lower() in base_names:
                    errors.append(f"{w}: asosiy kitobda shu nom bor")
                check_text(w + " intro", s.get("intro"), limit, errors)
                for q in s.get("questions") or []:
                    check_text(w + " q", q.get("q"), limit, errors)
                    if len(q.get("options") or []) != nopt:
                        errors.append(f"{w}: savolda {nopt} ta variant")
                img = (s.get("scene") or {}).get("image", "")
                if not re.fullmatch(r"en(45|67)-s\d+-[a-z0-9-]+\.png", img):
                    errors.append(f"{w}: scene.image nomi noto'g'ri")
            if key == "67p":
                names = {l["name"] for u in units for l in u["lessons"]}
                for name in names:
                    e = (enr.get("lessons") or {}).get(name)
                    if not e:
                        errors.append(f"{key} «{name}»: boyitish yo'q")
                        continue
                    if not e.get("intro_en"):
                        errors.append(f"{key} «{name}»: intro_en yo'q")
                    les = next(l for u in units for l in u["lessons"] if l["name"] == name)
                    for i in les["items"]:
                        if not (e.get("items") or {}).get(i["say"], {}).get("sentence"):
                            errors.append(f"{key} «{name}»: «{i['say']}» sentence yo'q")
                    if len(e.get("tests_en") or []) != len(les.get("tests") or []):
                        errors.append(f"{key} «{name}»: tests_en soni testlar soniga teng bo'lsin")
            try:
                merged = merge_enrich(copy.deepcopy(cur), enr)
                validate(merged)
                build_book(merged)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{key}: dvigatel xatosi — {exc}")
    else:
        try:
            validate(cur)
            build_book(copy.deepcopy(cur))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{key}: dvigatel xatosi — {exc}")
    return errors


if __name__ == "__main__":
    plan = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "reja_rasmli.json").read_text(encoding="utf-8"))
    total = 0
    for key in PLUS:
        errs = check(key, plan)
        total += len(errs)
        print(f"== {key}: {'ok' if not errs else str(len(errs)) + ' xato'}")
        for e in errs[:80]:
            print("  -", e)
    sys.exit(1 if total else 0)

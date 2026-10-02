"""REV88: bog'cha til kitoblari — ingliz tili kitobi andozasidan 9 ta boshqa til.

Ingliz tili kitoblari (en_34 … en_67 + boyitish fayllari) — ANDOZA: mavzular, rasmlar, hayotiy vaziyatlar,
immersiya pog'onalari, takror tizimi bir xil. Har til uchun faqat TARJIMA lug'ati kerak:
  tools/bogcha_content/tarjima/manba.json  — tarjima qilinadigan hamma ingliz matnlari (id → matn, turi)
  tools/bogcha_content/tarjima/<til>.json  — {"t": {id: tarjima}, "rom": {id: lotincha o'qilishi}}
Rasmlar ingliz kitobi bilan UMUMIY (fayl nomlari bir xil) — qayta chizish shart emas.

Ishlatish:
  python tools/bogcha_tillar.py extract          # manba.json ni yangilaydi
  python tools/bogcha_tillar.py check ru         # tarjima to'liqligini tekshiradi
  python tools/bogcha_tillar.py build ru         # tools/bogcha_content/ru_34.json … ru_67.json
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.bogcha_spiral import CLASS, merge_enrich  # noqa: E402

ROOT = Path(__file__).resolve().parent / "bogcha_content"
TR_DIR = ROOT / "tarjima"
AGES = ("23", "34", "45", "56", "67")   # REV99: 2–3 yosh (en_23 — tools/bogcha_23.py)
AGE_LABEL = {"23": "2–3 yosh", "34": "3–4 yosh", "45": "4–5 yosh", "56": "5–6 yosh", "67": "6–7 yosh"}
# til: (o'zbekcha o'zak, fan nomi, kitob kodi prefiksi, til nomi inglizcha — tarjimonga)
LANGS = {
    "ru": ("rus", "Rus tili", "RU", "Russian"),
    "ar": ("arab", "Arab tili", "AR", "Arabic (Modern Standard, fully vowelled for children where helpful)"),
    "tr": ("turk", "Turk tili", "TR", "Turkish"),
    "de": ("nemis", "Nemis tili", "DE", "German"),
    "fr": ("fransuz", "Fransuz tili", "FR", "French"),
    "es": ("ispan", "Ispan tili", "ES", "Spanish"),
    "ko": ("koreys", "Koreys tili", "KO", "Korean"),
    "ja": ("yapon", "Yapon tili", "JA", "Japanese (kana/simple kanji suitable for children)"),
    "zh": ("xitoy", "Xitoy tili", "ZH", "Mandarin Chinese (Simplified)"),
}
ROMANIZED = {"ru", "ar", "ko", "ja", "zh"}    # bola/ota-ona uchun lotincha o'qilishi ko'rsatiladi
TAG_EN = re.compile(r"\[en\](.*?)\[/en\]", re.S)
BOOK_TITLE_EN = "Hello, friend!"


def sid(text):
    return "s" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def english_books():
    out = {}
    for a in AGES:
        cur = json.loads((ROOT / f"en_{a}.json").read_text(encoding="utf-8"))
        enrich_path = ROOT / f"en_{a}_enrich.json"
        enrich = json.loads(enrich_path.read_text(encoding="utf-8")) if enrich_path.is_file() else None
        out[a] = merge_enrich(cur, enrich)
    return out


# ── Kitobni aylanib chiqish: har matn maydoniga funksiya qo'llanadi ──
def walk(cur, f):
    """f(kind, value, ctx) → yangi qiymat. kind: say|en|seg|option|board|uzname|class."""
    def seg(value, ctx):
        return TAG_EN.sub(lambda m: "\x00" + f("seg", m.group(1).strip(), ctx) + "\x01", value) if value else value

    for ui, unit in enumerate(cur["units"], 1):
        ctx = f"bo'lim {ui}: {unit['name']}"
        unit["name"] = f("uzname", unit["name"], ctx)
        for les in unit["lessons"]:
            c = f"{ctx} / dars «{les['name']}»"
            les["name"] = f("uzname", les["name"], c)
            if les.get("goal"):
                les["goal"] = f("uzname", les["goal"], c)
            les["intro"] = seg(les.get("intro"), c)
            if les.get("intro_en"):
                les["intro_en"] = f("en", les["intro_en"], c)
            for it in les["items"]:
                it["say"] = f("say", it["say"], c + f" (uz: {it.get('uz', '')})")
                for k in ("sentence", "action_en"):
                    if it.get(k):
                        it[k] = f("en", it[k], c)
            for row in les.get("extra") or []:
                row["sarlavha"] = f("uzname", row.get("sarlavha", ""), c)
                for k in ("matn", "sodda", "boshqa_usul"):
                    row[k] = seg(row.get(k), c)
                if row.get("doska"):
                    row["doska"] = f("board", row["doska"], c)
                for k in ("matn_en", "sarlavha_en"):
                    if row.get(k):
                        row[k] = f("en", row[k], c)
            for t in les.get("tests") or []:
                t["q"] = seg(t["q"], c)
                t["why"] = seg(t.get("why"), c)
                t["options"] = [f("option", o, c) for o in t["options"]]
                if t.get("q_en"):
                    t["q_en"] = f("en", t["q_en"], c)
        for sc in unit.get("scenarios") or []:
            c = f"{ctx} / hayotiy vaziyat «{sc['name']}»"
            sc["name"] = f("uzname", sc["name"], c)
            if sc.get("goal"):
                sc["goal"] = f("uzname", sc["goal"], c)
            sc["intro"] = seg(sc.get("intro"), c)
            for k in ("name_en", "intro_en"):
                if sc.get(k):
                    sc[k] = f("en", sc[k], c)
            sc["roles_en"] = [f("en", r, c + " (rol nomi)") for r in sc.get("roles_en") or []]
            for d in sc["dialog"]:
                d["say"] = f("say", d["say"], c + f" (uz: {d.get('uz', '')})")
            for q in sc.get("questions") or []:
                q["q"] = seg(q["q"], c)
                q["why"] = seg(q.get("why"), c)
                q["options"] = [f("option", o, c) for o in q["options"]]
                for k in ("q_en", "why_en"):
                    if q.get(k):
                        q[k] = f("en", q[k], c)
    return cur


def extract():
    items = {}

    def add(kind, value, ctx):
        value = str(value or "")
        if value.strip():
            entry = items.setdefault(sid(value), {"en": value, "kind": kind, "ctx": ctx})
            if kind == "say" and entry["kind"] != "say":   # o'rganiladigan ibora bo'lsa — lotincha o'qilishi ham kerak
                entry.update(kind="say", ctx=ctx)
        return value

    for a, cur in english_books().items():
        walk(copy.deepcopy(cur), lambda k, v, c: add(k, v, f"{AGE_LABEL[a]} · {c}"))
    for key, value in CLASS["en"].items():
        for v in (value if isinstance(value, list) else [value]):
            add("class", v, f"sinf iborasi «{key}» — {{...}} belgilarini o'zgarishsiz qoldiring")
    add("en", BOOK_TITLE_EN, "kitob nomi")
    TR_DIR.mkdir(parents=True, exist_ok=True)
    data = {"izoh": "Tarjima manbasi. Turlar: say — o'rganiladigan so'z/ibora; en — inglizcha gap; seg — o'zbekcha matn ichidagi "
                    "inglizcha bo'lak; option — test varianti (emoji saqlanadi; o'zbekcha bo'lsa o'zgarmaydi); board — doska "
                    "(faqat inglizcha qismlari tarjima qilinadi); uzname — o'zbekcha nom (faqat ichidagi inglizcha so'zlar "
                    "tarjima qilinadi); class — sinf iborasi ({...} saqlanadi).",
            "matnlar": dict(sorted(items.items()))}
    (TR_DIR / "manba.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def load_translation(lang):
    data = json.loads((TR_DIR / f"{lang}.json").read_text(encoding="utf-8"))
    return data.get("t") or {}, data.get("rom") or {}


def check(lang):
    src = json.loads((TR_DIR / "manba.json").read_text(encoding="utf-8"))["matnlar"]
    t, rom = load_translation(lang)
    problems = []
    for key, item in src.items():
        value = t.get(key)
        if not value or not str(value).strip():
            problems.append(f"yo'q: {key} «{item['en'][:50]}»")
            continue
        want = set(re.findall(r"\{[a-z]+\}", item["en"]))
        if want != set(re.findall(r"\{[a-z]+\}", value)):
            problems.append(f"{{…}} belgisi mos emas: {key} «{item['en'][:40]}» → «{value[:40]}»")
        if "[" in value and "]" in value and re.search(r"\[/?[a-z]{2}\]", value):
            problems.append(f"teg bo'lmasligi kerak: {key}")
        if lang in ROMANIZED and item["kind"] == "say" and not rom.get(key):
            problems.append(f"lotincha o'qilishi yo'q: {key} «{item['en'][:40]}»")
    return problems


COUNTRY = {"ru": "Rossiya", "ar": "Arab mamlakatlari", "tr": "Turkiya", "de": "Germaniya", "fr": "Fransiya", "es": "Ispaniya",
           "ko": "Koreya", "ja": "Yaponiya", "zh": "Xitoy"}


def uz_language_words(text, lang):
    """O'zbekcha matndagi «inglizcha», «ingliz bolalari», «Angliyadan» → shu tilga mos."""
    stem = LANGS[lang][0]
    text = re.sub(r"\bingliz(\w*)", lambda m: stem + m.group(1), text)
    text = re.sub(r"\bIngliz(\w*)", lambda m: stem.capitalize() + m.group(1), text)
    country = COUNTRY[lang]
    text = re.sub(r"\bAngliya(\w*)", lambda m: country + m.group(1), text)
    return text


def drop_english_only(cur):
    """Faqat ingliz tiliga xos qatorlar (masalan «teen» qo'shimchasi sirlari) boshqa tillarda olib tashlanadi."""
    for unit in cur["units"]:
        for les in unit["lessons"]:
            les["extra"] = [r for r in les.get("extra") or [] if "teen" not in (r.get("sarlavha") or "")]
    return cur


def build(lang, write=True):
    stem, subject, prefix, _ = LANGS[lang]
    t, rom = load_translation(lang)
    books = {}

    def tr(value):
        key = sid(value)
        if key not in t:
            raise KeyError(f"{lang}: tarjima yo'q — «{value[:60]}»")
        return str(t[key]).strip()

    for a, cur in english_books().items():
        cur = drop_english_only(copy.deepcopy(cur))
        romanize = {}

        def f(kind, value, ctx):
            if kind == "say" and lang in ROMANIZED and rom.get(sid(value)):
                romanize[tr(value)] = rom[sid(value)]
            out = tr(value)
            return uz_language_words(out, lang) if kind in ("uzname",) else out

        walk(cur, f)
        text = json.dumps(cur, ensure_ascii=False)
        cur = json.loads(text.replace("\\u0000", f"[{lang}]").replace("\\u0001", f"[/{lang}]"))
        # o'zbekcha matnlardagi «inglizcha» → «ruscha» va h.k.
        for unit in cur["units"]:
            for les in unit["lessons"] + (unit.get("scenarios") or []):
                for k in ("intro", "goal"):
                    if les.get(k):
                        les[k] = uz_language_words(les[k], lang)
                for row in les.get("extra") or []:
                    for k in ("matn", "sodda", "boshqa_usul"):
                        if row.get(k):
                            row[k] = uz_language_words(row[k], lang)
                for q in (les.get("tests") or []) + (les.get("questions") or []):
                    q["q"] = uz_language_words(q["q"], lang)
                    if q.get("why"):
                        q["why"] = uz_language_words(q["why"], lang)
                for it in les.get("items") or []:
                    if it["say"] in romanize:
                        it["rom"] = romanize[it["say"]]
                for d in les.get("dialog") or []:
                    if d["say"] in romanize:
                        d["rom"] = romanize[d["say"]]
        # nomlar kitob ichida takrorlanmasin (tarjimada ikki nom bir xil bo'lib qolishi mumkin)
        seen = set()
        for unit in cur["units"]:
            for les in unit["lessons"] + (unit.get("scenarios") or []):
                name, n = les["name"], 2
                while name.lower() in seen:
                    name, n = f"{les['name']} ({n})", n + 1
                les["name"] = name
                seen.add(name.lower())
        cur.update(subject=subject, lang=lang, prefix=prefix,
                   book_title=f"{tr(BOOK_TITLE_EN)} {AGE_LABEL[a]}",
                   **{"class": {k: ([tr(x) for x in v] if isinstance(v, list) else tr(v)) for k, v in CLASS["en"].items()}})
        books[a] = cur
        if write:
            (ROOT / f"{lang}_{a}.json").write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    return books


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        d = extract()
        print("matnlar:", len(d["matnlar"]))
    elif cmd == "check":
        probs = check(sys.argv[2])
        print("\n".join(probs[:60]) or "ok", f"\n{len(probs)} muammo")
    elif cmd == "build":
        for lang in sys.argv[2:]:
            build(lang)
            print(lang, "tayyor")
    else:
        print(__doc__)

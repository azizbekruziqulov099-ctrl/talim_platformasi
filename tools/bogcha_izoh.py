"""REV111: bog'cha til kitoblari — IZOH tili (kurs qaysi tilda TUSHUNTIRILADI).

O'qitiladigan til (ingliz, rus, arab, …) o'zgarmaydi — u faqat [xx]…[/xx] teglari ichida. Tushuntirish (o'qituvchi
ovozi, nomlar, ma'nolar, dvigatel shablonlari) asli o'zbekcha; bu yerda uni rus yoki ingliz tiliga o'giramiz:
  ingliz tili kursi + izoh ru  → bola inglizchani ruscha tushuntirish bilan o'rganadi;
  rus tili kursi + izoh ru     → to'liq ruscha;   ingliz tili kursi + izoh en → to'liq inglizcha.

Lug'at:
  tools/bogcha_content/izoh/manba.json — tarjima qilinadigan hamma o'zbekcha matnlar {sid: {uz, kind, ctx}}
  tools/bogcha_content/izoh/<ru|en>.json — {"t": {sid: tarjima}}   (sid = "s" + sha1(o'zbekcha matn)[:10])
Turlar: shablon (dvigatel shabloni, {…} belgilari bilan), nom (dars/bo'lim nomlari, maqsadlar, rollar, sarlavhalar),
ovoz (o'qituvchi ovozi matni bo'laklari), uz (qisqa ma'nolar, o'zbekcha test variantlari), doska (doskadagi ma'no).

Ishlatish:
  python tools/bogcha_izoh.py extract                       # manba.json ni yangilaydi
  python tools/bogcha_izoh.py check ru                      # tarjima to'liqligi / {…} / [xx] teglari
  python tools/bogcha_izoh.py build ru [en ru …] [--out PAPKA] [--rasmlar PAPKA] [--qoralama]
        → PAPKA/ingliz_tili_izoh_ru/ingliz_tili_izoh_ru_4-5_yosh_2_ai_miya.xlsx …
        (--qoralama: lug'atda yo'q matn o'zbekcha qoladi — faqat sinov uchun)
"""
import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import bogcha_spiral as sp  # noqa: E402
from tools.bogcha_spiral import TITLE_AGE, _clean, _split_picture, sid, uz_chunks  # noqa: E402

ROOT = Path(__file__).resolve().parent / "bogcha_content"
IZOH_DIR = ROOT / "izoh"
LANGS = ("en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh")
KEYS = ("23y", "45y", "67y")
KIND_ORDER = ("shablon", "nom", "ovoz", "uz", "doska")

# Kitobdagi chet tilidagi / texnik maydonlar — tarjima qilinmaydi
SKIP = {"say", "image", "image_prompt", "sentence", "action_en", "intro_en", "matn_en", "sarlavha_en", "q_en", "why_en",
        "name_en", "roles_en", "rom", "emoji", "subject", "lang", "prefix", "age", "class", "turi", "rasm", "image_scene",
        "who", "answer", "immersion", "izoh"}
# Butun maydon bitta kalit (Builder.UZ) — qolgan matnlar teglar bo'yicha bo'laklanadi (Builder.TX)
WHOLE = {"name": "nom", "goal": "nom", "roles": "nom", "uz": "uz", "action": "ovoz", "explain": "ovoz"}
SEGMENTED = {"sarlavha": "nom", "intro": "ovoz", "matn": "ovoz", "sodda": "ovoz", "boshqa_usul": "ovoz", "q": "ovoz",
             "why": "ovoz"}

INSTRUCTIONS = (
    "Bog'cha (2–7 yosh) til kitoblari uchun TUSHUNTIRISH tili tarjimasi. Har 'uz' matnini izoh tiliga (ru — rus, en — ingliz) "
    "o'giring va <izoh>.json ga {\"t\": {id: tarjima}} ko'rinishida yozing. Bu o'qituvchining (robot Kabu) bolaga "
    "gapiradigan ovozi: sodda, iliq, «sen» (ты / you) bilan, qisqa gaplar; emoji va tinish belgilari saqlanadi. "
    "O'qitiladigan chet tili bu matnlarda YO'Q (u [xx]…[/xx] teglari ichida va tarjimaga kirmaydi) — tarjimaga hech qachon "
    "[en], [ru] kabi teg qo'shmang. Turlar: shablon — dvigatel shabloni: {w}, {uz}, {name}, {lines} kabi belgilarni "
    "AYNAN o'zgarishsiz qoldiring (o'rnini gapga moslab surish mumkin); {w}/{wp} — o'rganilayotgan so'z (chet tilida), "
    "{uz}/{uz_cap} — uning ma'nosi izoh tilida, {name} — dars/bo'lim/vaziyat nomi, {role}/{a}/{b} — rol nomi, "
    "{lines}/{names}/{emojis} — tayyor qatorlar ro'yxati, {act} — harakat gapi (bo'sh bo'lishi mumkin; oldida bo'shliq bor), "
    "{look}/{listen}/{again}/{your_turn}/{repeat}/{good} — chet tilidagi sinf iboralari, {voice} — chet tilidagi ovoz, "
    "{ex} — misol gapi (bo'sh bo'lishi mumkin), {explain} — tushuntirish, {sentence} — chet tilidagi gap, {emoji}, {n} — son. "
    "«O'zbekcha» so'zi — «izoh tilida» degani: ru → «По-русски», en → «In English» deb o'giring. "
    "nom — dars, bo'lim, vaziyat nomlari, maqsadlar, rollar, sarlavhalar; ovoz — ovoz matni bo'lagi (ba'zan ikki chet "
    "so'zi orasidagi bo'lak — ctx dagi to'liq matnga qarang); uz — so'z/ibora ma'nosi (kichik harf bilan boshlangan bo'lsa, "
    "kichik harf bilan); doska — doskada chet so'zi yonida turadigan ma'no. Ismlar (Ali, Laylo), joy nomlari (Toshkent) va "
    "milliy taomlar (palov) o'zgarmaydi yoki transliteratsiya qilinadi."
)


# ── dvigatel shablonlari: bogcha_spiral.py dagi hamma U("…") chaqiriqlari (statik) ──
def engine_templates():
    tree = ast.parse(Path(sp.__file__).read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args:
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            arg = node.args[0]
            if name == "U" and isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                found.append((node.lineno, arg.value))
    out = [t for _, t in sorted(found)]
    out += list(sp.PRAISE) + [sp.YECHIM_DEFAULT]       # U(self.rng.choice(PRAISE)), U(YECHIM_DEFAULT)
    return list(dict.fromkeys(out))


def placeholders(text):
    return set(re.findall(r"\{[^{}]*\}", text))


def book_paths(lang):
    return [ROOT / f"{lang}_{k}.json" for k in KEYS]


def load_books():
    return {(lang, k): json.loads((ROOT / f"{lang}_{k}.json").read_text(encoding="utf-8")) for lang in LANGS for k in KEYS}


# ── kitob maydonlarini aylanib chiqish ──
def _walk(node, path, out):
    if isinstance(node, dict):
        for k, v in node.items():
            _walk(v, path + (k,), out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk(v, path + (i,), out)
    elif isinstance(node, str):
        out.append((path, node))


def _field(path):
    """Yo'ldagi oxirgi nomli kalit (ro'yxat indekslari tashlanadi)."""
    for p in reversed(path):
        if isinstance(p, str):
            return p
    return ""


def walk_chunks(books):
    """→ ([(kind, text, ctx)], noma'lum maydonlar, uz_aniq) — kitoblardagi o'zbekcha bo'laklar (Builder qanday kalit
    olsa, xuddi shunday). Test varianti va doskaning « — » dan o'ng tomoni faqat ingliz VA rus kitobida shu joyda aynan
    bir xil bo'lsa o'zbekcha hisoblanadi (chet tilidagisi tillarda farq qiladi)."""
    out, unknown = [], set()
    uz_variant, uz_doska = set(), set()
    by_path = {}
    for (lang, k), cur in books.items():
        strings = []
        _walk(cur, (), strings)
        by_path[(lang, k)] = dict(strings)
    for (lang, k), strings in by_path.items():
        for path, text in strings.items():
            field = _field(path)
            if field in SKIP or "class" in path or "scene" in path:
                continue
            ctx = f"{lang}_{k}: " + "/".join(map(str, path[:-1] if path and isinstance(path[-1], int) else path))
            if field == "book_title":
                m = TITLE_AGE.match(text)
                if m:
                    out.append(("nom", m.group(2), f"kitob nomining yosh qismi: {text}"))
                continue
            if field == "options":
                if not by_path[("en", k)].get(path) == by_path[("ru", k)].get(path) == text:
                    continue
                uz_variant.add(_clean(text))
                parts = uz_chunks(text) if "[" in text else uz_chunks(_split_picture(text)[1])
                out += [("uz", p, ctx + f" | variant: {text}") for p in parts]
                continue
            if field == "doska":
                en_l = str(by_path[("en", k)].get(path) or "").split("\n")
                ru_l = str(by_path[("ru", k)].get(path) or "").split("\n")
                for i, line in enumerate(text.split("\n")):
                    if " — " not in line:
                        continue
                    right = line.split(" — ", 1)[1]
                    same = [ls[i].split(" — ", 1)[1] if i < len(ls) and " — " in ls[i] else None for ls in (en_l, ru_l)]
                    if same[0] == same[1] == right:
                        uz_doska.add(right)
                        out += [("doska", p, ctx + f" | doska: {text[:160]}") for p in uz_chunks(right)]
                continue
            if field in WHOLE:
                if any(ch.isalpha() for ch in text):
                    out.append((WHOLE[field], text, ctx))
                continue
            if field not in SEGMENTED:
                unknown.add(field)
            kind = SEGMENTED.get(field, "ovoz")
            out += [(kind, p, ctx + f" | matn: {text[:160]}") for p in uz_chunks(text)]
    return out, unknown, {"variant": sorted(uz_variant), "doska": sorted(uz_doska)}


def record_run():
    """Hamma 30 kitobni (izoh=uz) yozib oluvchi U/UZ bilan quradi → ishlatilgan har shablon va bo'lak."""
    from tools.bogcha_kitob import build_books
    rec = []
    sp.IZOH_RECORDER = lambda kind, text, ctx: rec.append((kind, text, ctx))
    try:
        for lang in LANGS:
            build_books(book_paths(lang))
    finally:
        sp.IZOH_RECORDER = None
    return rec


def extract():
    templates = engine_templates()
    tset = set(templates)
    rec = record_run()
    used_t = {t for k, t, _ in rec if k == "shablon"}
    extra = used_t - tset
    if extra:
        raise SystemExit(f"Statik ro'yxatda yo'q shablonlar: {sorted(extra)[:5]}")
    walked, unknown, uz_aniq = walk_chunks(load_books())
    items = {}

    def add(kind, text, ctx):
        if not isinstance(text, str) or not any(ch.isalpha() for ch in text):
            return
        key = sid(text)
        if key in items:
            if kind == "shablon" and items[key]["kind"] != "shablon":
                items[key].update(kind=kind, ctx=ctx)
            return
        items[key] = {"uz": text, "kind": kind, "ctx": ctx}

    for t in templates:
        ph = sorted(placeholders(t))
        add("shablon", t, "dvigatel shabloni" + (f"; {', '.join(ph)} belgilarini o'zgarishsiz qoldiring" if ph else ""))
    for kind, text, ctx in rec:
        if kind != "shablon":
            add(kind, text, ctx)
    for kind, text, ctx in walked:
        add(kind, text, ctx)
    order = {k: i for i, k in enumerate(KIND_ORDER)}
    matnlar = dict(sorted(items.items(), key=lambda kv: order.get(kv[1]["kind"], 9)))
    IZOH_DIR.mkdir(parents=True, exist_ok=True)
    data = {"izoh": INSTRUCTIONS, "matnlar": matnlar, "uz_aniq": uz_aniq}
    (IZOH_DIR / "manba.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    counts = {k: sum(1 for v in matnlar.values() if v["kind"] == k) for k in KIND_ORDER}
    rec_keys = {sid(t) for k, t, _ in rec if any(ch.isalpha() for ch in t)}
    print(f"manba.json: {len(matnlar)} matn — " + ", ".join(f"{k} {n}" for k, n in counts.items()))
    print(f"  dvigatel ishlatgan: {len(rec_keys)} (shablonlar {len(used_t)}/{len(templates)}), "
          f"faqat aylanib chiqishda: {len(set(matnlar) - rec_keys)}")
    if unknown:
        print("  noma'lum maydonlar (ovoz deb olindi):", ", ".join(sorted(unknown)))
    return data


def check(code):
    manba = json.loads((IZOH_DIR / "manba.json").read_text(encoding="utf-8"))["matnlar"]
    path = IZOH_DIR / f"{code}.json"
    t = (json.loads(path.read_text(encoding="utf-8")).get("t") or {}) if path.is_file() else {}
    probs = []
    for key, entry in manba.items():
        tr = t.get(key)
        if not isinstance(tr, str) or not tr.strip():
            probs.append(f"yo'q {key} [{entry['kind']}] {entry['uz'][:70]}")
            continue
        if placeholders(tr) != placeholders(entry["uz"]):
            probs.append(f"belgi {key}: {sorted(placeholders(entry['uz']))} ≠ {sorted(placeholders(tr))} — {tr[:70]}")
        if re.search(r"\[/?[a-z]{2}\]", tr):
            probs.append(f"teg {key}: tarjimada [xx] tegi — {tr[:70]}")
        if entry["kind"] == "shablon":
            try:
                tr.format(**{p[1:-1]: "" for p in placeholders(entry["uz"])})
            except (KeyError, IndexError, ValueError) as e:
                probs.append(f"format {key}: {e!r} — {tr[:70]}")
    stale = set(t) - set(manba)
    if stale:
        probs.append(f"eskirgan (manbada yo'q) id: {len(stale)} ta")
    return probs


def build(izoh, langs=None, out="bogcha_izoh_chiqish", image_dir=None, draft=False):
    from tools.bogcha_kitob import build_books, write_groups
    langs = langs or LANGS
    sp.IZOH_ALLOW_MISSING = draft
    report = []
    for lang in langs:
        books = build_books(book_paths(lang), izoh=izoh)
        groups = {books[0]["subject"]: books}
        report += write_groups(Path(out), groups, None, image_dir, izoh)
    print("\n".join(report))
    return report


def main(argv):
    cmd = argv[0] if argv else ""
    if cmd == "extract":
        extract()
    elif cmd == "check":
        probs = check(argv[1])
        print("\n".join(probs[:80]) or "ok", f"\n{len(probs)} muammo")
        return 1 if probs else 0
    elif cmd == "build":
        args = list(argv[1:])
        opts = {}
        for flag in ("--out", "--rasmlar"):
            if flag in args:
                i = args.index(flag)
                opts[flag] = args[i + 1]
                del args[i:i + 2]
        draft = "--qoralama" in args
        args = [a for a in args if a != "--qoralama"]
        if not args or args[0] not in sp.IZOH_LANGS:
            print(__doc__)
            return 2
        build(args[0], args[1:] or None, opts.get("--out", "bogcha_izoh_chiqish"), opts.get("--rasmlar"), draft)
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

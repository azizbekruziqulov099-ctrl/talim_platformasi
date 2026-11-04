"""REV324: bog'cha til kitoblari — yoshga moslik auditi (o'lchanadigan qoidalar).

Tekshiriladigan fayllar (uch joyda, bir xil nomli nusxalar ham):
  bogcha_content/<til>_<yosh>.json, repo ildizidagi <til>_<yosh>.json, tools/bogcha_content/<til>_<yosh>.json
  til: en ru ar tr de fr es ko ja zh;  yosh: 23 34 45 56 67 (+ «y» yangi variant, «p» qo'shimcha darslar,
  «_A»/«_B» — 67p bo'laklari). 3-4 yosh → 2-3 qoidasi, 5-6 yosh → 4-5 qoidasi (kichigiga tenglanadi).

Qoidalar (RULES): darsdagi element soni, kirish (intro/intro_en) gaplar va so'zlar soni, o'rganiladigan ibora
uzunligi, bo'sh maydonlar, bir darsda takrorlangan element/rasm, 2-3 yoshda harf va o'qish yo'qligi, xavfli
harakat/so'zlar, lotincha o'qilish (rom), emoji, o'zbekcha imlo belgilari (tutuq belgisi faqat «'»), nusxalar bir xilligi.

Ishlatish:
  python tools/bogcha_audit.py             # tekshiradi va docs/BOGCHA_AUDIT_REV324.md hisobotini yozadi
  python tools/bogcha_audit.py --check     # faqat tekshiradi: xato bo'lsa chiqish kodi 1
  python tools/bogcha_audit.py --baseline  # joriy holatni «boshlang'ich» deb saqlaydi (hisobotda «oldin» ustuni)
"""
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOCATIONS = ("bogcha_content", ".", "tools/bogcha_content")
LANGS = ("en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh")
ROMANIZED = {"ru", "ar", "ko", "ja", "zh"}          # tools/bogcha_tillar.py bilan bir xil
FILE_RE = re.compile(r"^(?P<lang>en|ru|ar|tr|de|fr|es|ko|ja|zh)_(?P<age>23|34|45|56|67)(?P<var>[yp]?)(?P<part>_[AB])?\.json$")
AGE_GROUP = {"23": "2-3", "34": "2-3", "45": "4-5", "56": "4-5", "67": "6-7"}

# Yosh qoidalari. say_words — o'rganiladigan ibora (say) so'zlari; ja/zh da bo'sh joy yo'q — belgilar sanaladi.
RULES = {
    "2-3": {"items": (2, 3), "intro_sent": 2, "intro_words": 20, "say_words": 3, "say_chars": {"ja": 6, "zh": 4}, "letters": False},
    "4-5": {"items": (3, 4), "intro_sent": 3, "intro_words": 30, "say_words": 6, "say_chars": {"ja": 12, "zh": 8}, "letters": False},
    "6-7": {"items": (4, 6), "intro_sent": 4, "intro_words": 40, "say_words": 8, "say_chars": {"ja": 16, "zh": 10}, "letters": True},
}

REPORT = REPO / "docs" / "BOGCHA_AUDIT_REV324.md"
BASELINE = REPO / "docs" / "bogcha_audit_rev324_boshlangich.json"
CHANGES = REPO / "docs" / "bogcha_audit_rev324_ozgarishlar.json"

CODES = {
    "items_soni": "darsdagi element soni yoshga mos emas",
    "intro_gap": "kirishda gap ko'p",
    "intro_soz": "kirishda so'z ko'p",
    "say_uzun": "o'rganiladigan ibora yoshga nisbatan uzun",
    "bosh_maydon": "bo'sh maydon",
    "takror_element": "bir darsda element takrorlangan",
    "takror_rasm": "bir darsda bitta rasm ikki marta",
    "harf_oqish": "2-3 yoshda harf/o'qish",
    "xavfli": "xavfli harakat yoki yoshga mos bo'lmagan so'z",
    "rom": "lotincha o'qilishi (rom) noto'g'ri",
    "emoji": "emoji emas",
    "imlo": "o'zbekcha imlo belgisi",
    "nusxa": "nusxalar bir xil emas",
    "json": "JSON o'qilmadi yoki tuzilma buzuq",
}

TAG_SEG = re.compile(r"\[(?P<t>[a-z]{2,3})\](?P<body>.*?)\[/(?P=t)\]", re.S)
ANY_TAG = re.compile(r"\[/?[a-z]{2,3}\]")
SENT_END = ".!?…。！？؟"
WORD = re.compile(r"[^\W_](?:[\w'’ʻ‘-]*[^\W_])?")
LATIN_CYR_LETTER = re.compile(r"^[A-Za-z\u00C0-\u024F\u0400-\u04FF]$")
NON_LATIN = re.compile(r"[\u0400-\u04FF\u0600-\u06FF\u0750-\u077F\u3040-\u30FF\u3400-\u9FFF\uAC00-\uD7AF\u1100-\u11FF]")
BAD_APOS = re.compile(r"[`‘’ʻʼ´]")
CYRILLIC = re.compile(r"[\u0400-\u04FF]")

# Xavfli narsa/harakat — «action» va topshiriqlarda bolaga tavsiya qilinmasin.
DANGER_ACTION = re.compile(
    r"(olov|gugurt|zajigalka|pichoq|qaychi|\bdori|tabletka|rozetka|\btok\b|gaz plita|plita|dazmol|qaynoq|"
    r"derazadan|derazaga chiq|balkon|narvon|daraxtga chiq|tomga chiq|stol(ga|ning ustiga) chiq|"
    r"qozon|choynak|\bsham\w*|"
    r"\bur\b|\burib|\btep\b|tepib|mushtla|tishla|o'ldir|qurol)", re.I)
# «…ganday qil» — o'xshatib (haqiqiy narsasiz) bajariladi: xavfsiz
PRETEND = re.compile(r"(ganday|gandek|go'yo|o'yinchoq|plastilin)", re.I)
# Hamma matnda: zo'ravonlik, qo'rqinchli va kattalar mavzusi.
DANGER_TEXT = re.compile(
    r"(o'ldir|\bqon(?:ga|i|ni|li)?\b|qurol|to'pponcha|miltiq|urush|\bjang\b|arvoh|dahshat|qo'rqinchli|\bo'lim\b|\bo'lik|"
    r"sigaret|chekish|aroq|\bvino\b|\bpivo\b|spirtli|\bichkilik)", re.I)
# 2-3 yosh: harf o'rgatilmaydi, o'qish/yozish topshirilmaydi.
LETTER_TEXT = re.compile(r"(\bharf|\bo'qi(?:ymiz|ysan|ysiz|ng|sh|b\b|gin)|\byoz(?:amiz|asan|ing|ish|ib\b|gin))", re.I)


# ── matn o'lchovlari ──
def _tokens(text):
    """Bo'sh joy bilan ajratilgan so'zlar (arabcha harakatlar, ʼ va «-» so'zni bo'lmaydi)."""
    return [w for w in re.split(r"\s+", str(text or "")) if any(ch.isalnum() for ch in w)]


def _seg_words(body):
    return max(1, len(_tokens(body)))


CLOSERS = "\"»”'’)]」』"
CJK_END = "。！？"


def sentences(text):
    """Gaplar. [xx]…[/xx] bo'lagi bitta so'z o'rnida (ichidagi «!» gapni bo'lmaydi).
    Tinish belgisidan keyin kichik harf bilan davom etsa («qila olasanmi?» deb, Sss… jim) yoki
    qo'shtirnoq yopilib gap davom etsa (「どこ？」と) — bu bitta gap."""
    t = ANY_TAG.sub("", TAG_SEG.sub(" § ", str(text or "")))
    cuts, i, n = [0], 0, len(t)
    for m in re.finditer("[" + re.escape(SENT_END) + "]+", t):
        k = m.end()
        while k < n and t[k] in CLOSERS:
            k += 1
        closed = k > m.end()
        rest = t[k:]
        if not rest.strip():
            continue
        if rest[0].isspace():
            nxt = rest.lstrip()[0]
            if nxt.islower():
                continue
        elif closed or m.group(0)[-1] not in CJK_END:
            continue
        cuts.append(k)
    cuts.append(n)
    parts = [t[a:b] for a, b in zip(cuts, cuts[1:])]
    return [p.strip() for p in parts if re.search(r"[^\W_]|§", p)]


def words(text):
    t = TAG_SEG.sub(lambda m: " " + " ".join(["§"] * _seg_words(m.group("body"))) + " ", str(text or ""))
    t = ANY_TAG.sub("", t)
    return [w for w in re.split(r"\s+", t) if w == "§" or any(ch.isalnum() for ch in w)]


def say_size(say, lang):
    s = str(say or "")
    if lang in ("ja", "zh"):
        return len([ch for ch in s if ch.isalnum()])
    return len(_tokens(s))


def norm(text):
    return re.sub(r"[\W_]+", "", str(text or "").lower())


def is_emoji(text):
    for ch in str(text or ""):
        cp = ord(ch)
        if cp >= 0x1F000 or cp == 0x20E3 or unicodedata.category(ch) == "So" or 0x2600 <= cp <= 0x27BF or 0x2B00 <= cp <= 0x2BFF:
            return True
    return False


def outside_tags(text):
    return TAG_SEG.sub(" ", str(text or ""))


# ── fayllar ──
def book_files(repo=REPO):
    out = []
    for loc in LOCATIONS:
        folder = repo / loc
        for p in sorted(folder.glob("*.json")):
            m = FILE_RE.match(p.name)
            if m:
                out.append(p)
    return out


def file_info(path):
    m = FILE_RE.match(Path(path).name)
    return m.group("lang"), m.group("age"), AGE_GROUP[m.group("age")]


def rel(path, repo=REPO):
    return str(Path(path).resolve().relative_to(repo))


def iter_lessons(book):
    for ui, unit in enumerate(book.get("units") or [], 1):
        for li, les in enumerate(unit.get("lessons") or [], 1):
            yield ui, li, unit, les


# ── bitta kitob ──
def audit_book(book, lang, group):
    """→ [(kod, joy, tafsilot)]. joy: «2.3 «Dars nomi»» ko'rinishida."""
    rule = RULES[group]
    issues = []

    def add(code, where, detail):
        issues.append((code, where, detail))

    if not isinstance(book, dict) or not isinstance(book.get("units"), list) or not book["units"]:
        return [("json", "kitob", "units yo'q")]
    for ui, unit in enumerate(book["units"], 1):
        if not str(unit.get("name") or "").strip():
            add("bosh_maydon", f"{ui}-bo'lim", "bo'lim nomi bo'sh")
        if not unit.get("lessons"):
            add("bosh_maydon", f"{ui}-bo'lim", "darslar yo'q")
    for ui, li, unit, les in iter_lessons(book):
        where = f"{ui}.{li} «{les.get('name', '')}»"
        for k in ("name", "goal", "intro"):
            if not str(les.get(k) or "").strip():
                add("bosh_maydon", where, f"{k} bo'sh")
        items = les.get("items") or []
        lo, hi = rule["items"]
        if not lo <= len(items) <= hi:
            add("items_soni", where, f"{len(items)} ta element (kerak: {lo}–{hi})")
        for key in ("intro", "intro_en"):
            text = les.get(key)
            if not text:
                continue
            ns, nw = len(sentences(text)), len(words(text))
            if ns > rule["intro_sent"]:
                add("intro_gap", where, f"{key}: {ns} gap (ko'pi bilan {rule['intro_sent']})")
            if nw > rule["intro_words"]:
                add("intro_soz", where, f"{key}: {nw} so'z (ko'pi bilan {rule['intro_words']})")
        seen_say, seen_img = {}, {}
        for n, it in enumerate(items, 1):
            iw = f"{where} #{n} «{it.get('say', '')}»"
            for k in ("say", "uz", "emoji", "image"):
                if not str(it.get(k) or "").strip():
                    add("bosh_maydon", iw, f"{k} bo'sh")
            if "action" in it and not str(it.get("action") or "").strip():
                add("bosh_maydon", iw, "action bo'sh (to'ldiring yoki olib tashlang)")
            limit = rule["say_chars"].get(lang, rule["say_words"])
            size = say_size(it.get("say"), lang)
            if size > limit:
                unit_name = "belgi" if lang in ("ja", "zh") else "so'z"
                add("say_uzun", iw, f"{size} {unit_name} (ko'pi bilan {limit})")
            key = norm(it.get("say"))
            if key and key in seen_say:
                add("takror_element", iw, f"#{seen_say[key]} bilan bir xil")
            seen_say.setdefault(key, n)
            img = str(it.get("image") or "")
            if img and img in seen_img:
                add("takror_rasm", iw, f"{img} — #{seen_img[img]} da ham")
            seen_img.setdefault(img, n)
            rom = str(it.get("rom") or "")
            if lang in ROMANIZED:
                if not rom.strip():
                    add("rom", iw, "rom bo'sh")
                elif NON_LATIN.search(rom):
                    add("rom", iw, f"rom lotincha emas: {rom}")
                elif rom.strip() == str(it.get("say") or "").strip():
                    add("rom", iw, "rom say bilan bir xil")
            elif rom and NON_LATIN.search(rom):
                add("rom", iw, f"rom lotincha emas: {rom}")
            if it.get("emoji") and not is_emoji(it["emoji"]):
                add("emoji", iw, f"emoji emas: {it['emoji']}")
            action = str(it.get("action") or "")
            if action and DANGER_ACTION.search(action) and not PRETEND.search(action):
                add("xavfli", iw, f"action: {action}")
            for k in ("uz", "action"):
                v = str(it.get(k) or "")
                if BAD_APOS.search(v):
                    add("imlo", iw, f"{k}: tutuq belgisi «'» bo'lsin — {v}")
                if CYRILLIC.search(v):
                    add("imlo", iw, f"{k}: o'zbek lotin yozuvida kirill harfi — {v}")
                if "  " in v:
                    add("imlo", iw, f"{k}: ikki bo'sh joy — {v}")
            if not rule["letters"]:
                core = re.sub(r"[\W_]+", "", str(it.get("say") or ""))
                if LATIN_CYR_LETTER.match(core):
                    add("harf_oqish", iw, f"harf o'rgatilyapti: {it.get('say')}")
        # o'zbekcha matnlar: imlo, xavfli so'zlar, 2-3 yoshda harf/o'qish
        uz_texts = [("goal", les.get("goal")), ("intro", outside_tags(les.get("intro")))]
        uz_texts += [(f"#{n} uz", it.get("uz")) for n, it in enumerate(items, 1)]
        uz_texts += [(f"#{n} action", it.get("action")) for n, it in enumerate(items, 1)]
        for r in les.get("extra") or []:
            uz_texts += [("extra", outside_tags(r.get("sarlavha"))), ("extra", outside_tags(r.get("matn")))]
        for t in les.get("tests") or []:
            uz_texts += [("test", outside_tags(t.get("q"))), ("test", outside_tags(t.get("why")))]
        for k, v in uz_texts:
            v = str(v or "")
            if not v:
                continue
            if k in ("goal", "intro") and BAD_APOS.search(v):
                add("imlo", where, f"{k}: tutuq belgisi «'» bo'lsin — {v[:80]}")
            m = DANGER_TEXT.search(v)
            if m:
                add("xavfli", where, f"{k}: «{m.group(0)}» — {v[:80]}")
            if not rule["letters"]:
                m = LETTER_TEXT.search(v)
                if m:
                    add("harf_oqish", where, f"{k}: «{m.group(0)}» — {v[:80]}")
        for r in les.get("extra") or []:
            task = outside_tags(r.get("matn"))
            if r.get("turi") == "topshiriq" and DANGER_ACTION.search(task) and not PRETEND.search(task):
                add("xavfli", where, f"topshiriq: {task[:80]}")
    return issues


def warnings_book(book, lang, group):
    """Xato emas — ko'rib chiqish uchun: bir darsda bir xil ma'no (sinonim) va h.k."""
    out = []
    for ui, li, unit, les in iter_lessons(book):
        where = f"{ui}.{li} «{les.get('name', '')}»"
        cnt = collections.Counter(str(it.get("uz") or "").strip().lower() for it in les.get("items") or [])
        for uz, c in cnt.items():
            if uz and c > 1:
                out.append(("bir_xil_manosi", where, f"«{uz}» {c} marta (sinonimlar — testda chalkashmasin)"))
    return out


# ── hammasi ──
def audit_all(repo=REPO):
    """→ {"files": {rel: [issues]}, "warnings": {rel: [...]}, "stats": {...}}"""
    res, warn = {}, {}
    stats = collections.Counter()
    texts = {}
    for p in book_files(repo):
        r = rel(p, repo)
        lang, age, group = file_info(p)
        try:
            raw = p.read_text(encoding="utf-8")
            book = json.loads(raw)
        except Exception as e:  # noqa: BLE001
            res[r] = [("json", "fayl", str(e)[:120])]
            continue
        texts[r] = raw
        res[r] = audit_book(book, lang, group)
        warn[r] = warnings_book(book, lang, group)
        stats["fayl"] += 1
        for _, _, _, les in iter_lessons(book):
            stats["dars"] += 1
            stats["element"] += len(les.get("items") or [])
    # nusxalar: bogcha_content/X va ildizdagi X bir xil bo'lsin
    for p in sorted((repo / "bogcha_content").glob("*.json")):
        if not FILE_RE.match(p.name):
            continue
        root = repo / p.name
        if root.is_file():
            a, b = rel(p, repo), rel(root, repo)
            if texts.get(a) is not None and texts.get(b) is not None and json.loads(texts[a]) != json.loads(texts[b]):
                res.setdefault(a, []).append(("nusxa", "fayl", f"{b} bilan bir xil emas"))
    return {"files": res, "warnings": warn, "stats": dict(stats)}


def summarize(result):
    by_code = collections.Counter()
    by_loc = collections.Counter()
    for f, issues in result["files"].items():
        loc = f.rsplit("/", 1)[0] if "/" in f else "."
        for code, _, _ in issues:
            by_code[code] += 1
            by_loc[loc] += 1
    return {"jami": sum(by_code.values()), "kod": dict(by_code), "joy": dict(by_loc), "stats": result["stats"]}


# ── hisobot ──
def _md(text):
    return str(text).replace("|", "\\|").replace("\n", " ⏎ ")


def _rules_table():
    rows = ["| Yosh guruhi | Fayllar | Element | Kirish (gap / so'z) | Ibora (so'z; ja/zh — belgi) | Harf |",
            "|---|---|---|---|---|---|"]
    files = {"2-3": "_23, _23y, _23p, _34", "4-5": "_45, _45y, _45p, _56", "6-7": "_67, _67y, _67p (_A/_B)"}
    for g, r in RULES.items():
        rows.append(f"| {g} yosh | {files[g]} | {r['items'][0]}–{r['items'][1]} | ≤ {r['intro_sent']} / ≤ {r['intro_words']} | "
                    f"≤ {r['say_words']} (ja ≤ {r['say_chars']['ja']}, zh ≤ {r['say_chars']['zh']}) | {'mumkin' if r['letters'] else 'yo‘q'} |".replace("‘", "'"))
    return "\n".join(rows)


def _changes_section():
    if not CHANGES.is_file():
        return ["_O'zgarishlar jurnali hali yo'q._"]
    data = json.loads(CHANGES.read_text(encoding="utf-8"))
    groups = data.get("guruhlar") or []
    out = [f"Jami: **{data.get('jami_fayl_ozgarish', 0)}** ta fayl-darajasidagi o'zgarish, **{len(groups)}** ta noyob tuzatish "
           f"(bir xil tuzatish hamma tillar va nusxalarda takrorlangani bitta qatorda). To'liq ro'yxat (har fayl, har dars): "
           f"[`{CHANGES.name}`]({CHANGES.name}).", ""]
    by_kind = collections.OrderedDict()
    for g in groups:
        by_kind.setdefault(g["tur"], []).append(g)
    for kind, rows in by_kind.items():
        out += [f"#### {kind} — {len(rows)} ta", "", "| # | Fayllar | Dars | Maydon | Eski | Yangi | Sababi |", "|---|---|---|---|---|---|---|"]
        for n, g in enumerate(rows, 1):
            out.append(f"| {n} | {_md(g['fayllar'])} | {_md(g['dars'])} | {_md(g['maydon'])} | {_md(g['eski'])} | {_md(g['yangi'])} | {_md(g['sabab'])} |")
        out.append("")
    return out


def write_report(result, path=REPORT):
    now = summarize(result)
    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.is_file() else None
    st = now["stats"]
    lines = ["# REV324: bog'cha darslari auditi", "",
             "Avtomatik hisobot: `python tools/bogcha_audit.py` (tekshiruv: `pytest -q tests/test_bogcha_audit.py`).", "",
             "## Qamrov", "",
             f"- Joylar: `bogcha_content/`, repo ildizi (bir xil nomli nusxalar), `tools/bogcha_content/` — {st.get('fayl', 0)} ta kitob fayli, "
             f"{st.get('dars', 0)} ta dars, {st.get('element', 0)} ta element.",
             "- Tillar: en, ru, ar, tr, de, fr, es, ko, ja, zh. Yoshlar: 23, 34, 45, 56, 67 va «y» (yangi), «p» (qo'shimcha), 67p_A/_B.",
             "- 3-4 yosh (_34) 2-3 qoidasi bilan, 5-6 yosh (_56) 4-5 qoidasi bilan tekshirildi (kichigiga tenglandi).", "",
             "## Qoidalar", "", _rules_table(), "",
             "Barcha yoshda: bo'sh maydon yo'q (name, goal, intro; element: say, uz, emoji, image; rom — ru/ar/ko/ja/zh), "
             "bir darsda element (say) va rasm takrorlanmaydi, «action» bo'sh emas va xavfsiz (olov, pichoq, dori, rozetka, "
             "balandga chiqish va h.k. yo'q), matnda zo'ravonlik/qo'rqinchli/kattalar so'zlari yo'q, rom — faqat lotin yozuvi, "
             "emoji — haqiqiy emoji, o'zbekcha matnda tutuq belgisi faqat «'» (‘ ’ ʻ ` emas), kirill harfi yo'q; "
             "`bogcha_content/X` va ildizdagi `X` bir xil. Gap oxiri: «.», «!», «?», «…» (va 。！？؟); belgidan keyin kichik harf "
             "bilan davom etsa («qila olasanmi?» deb) yoki qo'shtirnoq yopilib gap davom etsa — bitta gap. `[xx]…[/xx]` bo'lagi "
             "gapni bo'lmaydi, ichidagi so'zlar so'z sifatida sanaladi.", "",
             "## Mazmun tekshiruvi", "",
             "O'lchab bo'lmaydigan xatolar har tilda qo'lda ko'rib chiqildi (462 ta noyob element × 10 til, misol gaplar, "
             "o'zbekcha ma'no va harakatlar): say ↔ uz mosligi (masalan, «Olma, banan, apelsin» darsida 9 tilda «apelsin» o'rniga "
             "rang so'zi turgan edi), imlo («to'gra» → «to'g'ra», «qo'l soat» → «qo'l soati», «qorbobo, qor odam» → «qor odam»), "
             "rom (arabcha i'rob, yaponcha ismlar, pinyin), emoji (🙆 → 🦶), bir darsda takror (ru «Привет!» ×2, ja «あし» ×2, "
             "ko «배» ×2, ru «Пожалуйста» ×2), yoshdan murakkab ibora (fr, de, ja, zh), noto'g'ri fikr o'rgatadigan misol gap "
             "(«Men ham ucha olaman!» → «Men ucha olmayman!», hamma tilda), xavfli harakat (haqiqiy qozon, yonib turgan sham → "
             "o'xshatib bajariladigan shakl). Har bir tuzatish quyidagi jurnalda.", "",
             "## Natija", "",
             "| Xato turi | Oldin | Hozir |", "|---|---|---|"]
    codes = list(CODES)
    for c in codes:
        b = (base or {}).get("kod", {}).get(c, 0) if base else "—"
        lines.append(f"| {CODES[c]} (`{c}`) | {b} | {now['kod'].get(c, 0)} |")
    lines.append(f"| **Jami** | **{base['jami'] if base else '—'}** | **{now['jami']}** |")
    lines += ["", "Joylar bo'yicha (hozir): " + (", ".join(f"`{k}` — {v}" for k, v in sorted(now["joy"].items())) or "xato yo'q") + ".", ""]
    left = {f: i for f, i in result["files"].items() if i}
    lines += ["## Qolgan xatolar", ""]
    if not left:
        lines += ["Yo'q — hamma fayl qoidalardan o'tdi. ✅", ""]
    else:
        for f, issues in sorted(left.items()):
            lines += [f"### `{f}` — {len(issues)}", "", "| Kod | Joy | Tafsilot |", "|---|---|---|"]
            lines += [f"| {c} | {_md(w)} | {_md(d)} |" for c, w, d in issues[:200]]
            if len(issues) > 200:
                lines.append(f"| … | … | yana {len(issues) - 200} ta |")
            lines.append("")
    lines += ["## O'zgarishlar jurnali", ""] + _changes_section()
    warn = collections.Counter()
    examples = {}
    for f, ws in result["warnings"].items():
        for code, w, d in ws:
            warn[(code, d)] += 1
            examples.setdefault((code, d), f"{f} {w}")
    lines += ["## Ogohlantirishlar (xato emas)", ""]
    if warn:
        lines += ["| Tur | Tafsilot | Necha faylda | Misol |", "|---|---|---|---|"]
        lines += [f"| {c} | {_md(d)} | {n} | {_md(examples[(c, d)])} |" for (c, d), n in sorted(warn.items())]
    else:
        lines.append("Yo'q.")
    lines += ["", "## Tuzatilmagan, qaror kerak bo'lgan joylar", "",
              "- ja: «かのじょ / かれ / かれら» (u — qiz, u — o'g'il, ular) olmoshlari bolalar nutqida g'ayritabiiy; yaponchada odatda "
              "olmosh tushiriladi yoki ism aytiladi. «He/She/They» darsi shu olmoshlarni o'rgatgani uchun o'zgartirilmadi.",
              "- es: «Este es mi…» (bu mening…) — «abuela» bilan «Esta es mi…» kerak; ibora qolip sifatida qoldirildi.",
              "- Eski kitoblar (_34, _45, _56, _67) hali «Kabutar qushcha» va «siz» uslubida (y-kitoblar — robot Kabu, «sen»); "
              "uslub almashtirilmadi, faqat qoidaga zid joylar tuzatildi.",
              "- Matematika, atrof-muhit va mantiq kitoblari (`mt_*`, `am_*`, `mn_*`) bu auditga kirmadi.", "",
              "## Eslatma", "",
              "- Tarjima kitoblari `tools/bogcha_tillar.py build <til>` bilan ingliz kitobidan qayta yasalsa yoki "
              "`tools/bogcha_yosh_rev99.py` qayta ishga tushirilsa, bu tuzatishlar ustidan yoziladi. Shunday bo'lsa — "
              "`python tools/bogcha_tuzatish_rev324.py` tuzatishlarni qayta qo'llaydi, so'ng `python tools/bogcha_audit.py`.",
              "- `bogcha_content/` va ildizdagi y-fayllar (`*_45y`, `*_67y`) `tools/bogcha_content/` dagining eski, qisqa nusxasi "
              "(kamroq bo'lim) — ular ham tekshirildi va tuzatildi, lekin yangi nusxaga almashtirilmadi.",
              "- Kam elementli darslarga qo'shilgan elementlar mavjud rasmlardan foydalanadi (yangi rasm chizish shart emas). "
              "Sanoq va hafta kunlari darslarida oldingi darsdagi so'z takror sifatida qo'shildi; shu sababli "
              "`tools/bogcha_spiral.py` da takror element test variantlari pulga ikkinchi marta kirmaydigan qilindi.",
              "- Ingliz manbasi (`en_*`, `en_*_enrich.json`) ham tuzatildi, lekin `tools/bogcha_content/tarjima/` lug'atlari "
              "yangilanmadi — tarjimalar faqat kitob fayllarida.", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv):
    result = audit_all()
    summ = summarize(result)
    if "--baseline" in argv:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
        print("boshlang'ich holat saqlandi:", rel(BASELINE))
    if "--check" not in argv:
        print("hisobot:", rel(write_report(result)))
    print(f"fayllar: {summ['stats'].get('fayl', 0)}, darslar: {summ['stats'].get('dars', 0)}, xatolar: {summ['jami']}")
    for c, n in sorted(summ["kod"].items()):
        print(f"  {c}: {n}")
    return 1 if summ["jami"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

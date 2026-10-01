"""REV96: o'qituvchining shaxsiy kutubxonasi — «aqlli» qism (bazasiz, sof funksiyalar).

* Imlo xatolariga chidamli qidiruv: kirill→lotin, tutuq belgisiz (o'/o‘/o`/o), q↔k, h↔x, e↔i, o↔u
  chalkashliklari, qo'shimchalar (-imni, -lar, -dagi …) olib tashlanadi, o'xshashlik darajasi hisoblanadi.
* Yangi hujjat qaysi polka va qatorga tushishini taklif qiladi (turi va fani bo'yicha).
* Yordamchi suhbat: topdi / bir nechta o'xshash (aniqlashtirishni so'raydi) / topolmadi (imloni taklif qiladi).
"""
import io
import re
import zipfile
from difflib import SequenceMatcher

_CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "ғ": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "қ": "q", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ў": "o", "ф": "f", "х": "x", "ҳ": "h", "ц": "ts", "ч": "ch", "ш": "sh",
    "щ": "sh", "ъ": "", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ы": "i",
}
_APOS = re.compile(r"[ʻʼ’‘`´'ʹ]")

SUFFIXES = sorted([
    "larimizni", "laringizni", "larimizdagi", "larimiz", "laringiz", "larining", "larini", "larimni",
    "larimdagi", "larimda", "larim", "laridagi", "lari", "larda", "lardan", "larga", "lar",
    "imizni", "ingizni", "imizdagi", "imdagi", "imni", "imga", "imda", "imdan", "ning", "imiz", "ingiz",
    "dagi", "dan", "ga", "da", "ni", "im", "ing", "si", "mi", "chi", "ini",
], key=len, reverse=True)

STOPWORDS = {
    "top", "topib", "topip", "topgin", "toping", "topchi", "topasanmi", "topasizmi", "ber", "bering", "bergin",
    "qani", "qayerda", "qaerda", "qayda", "qayerga", "qaerga", "qayerdan", "hujjat", "hujjatim", "hujat",
    "hujjatni", "hujjatlar", "hujjatlarim", "fayl", "faylim", "fayllarim", "shu", "shuni", "mening", "menga",
    "meni", "men", "kerak", "keraksiz", "saqlagan", "saqladim", "saqlaganman", "saqlab", "edim", "edi", "bor",
    "bormi", "och", "ochib", "oching", "ochgin", "korsat", "korsating", "kursat", "iltimos", "va", "bilan",
    "uchun", "haqida", "haqidagi", "qilib", "bu", "osha", "usha", "anu", "yuklagan", "yuklaganman", "qoygan",
    "qoyganman", "qaysi", "qani", "ham", "yoki", "bir", "bitta", "anavi", "manavi", "hozir", "tez", "yordam",
    "ber", "chiqar", "chiqarib", "izla", "izlab", "qidir", "qidirib", "kutubxona", "kutubxonam", "kutubxonamda",
    "polka", "polkada", "qator", "qatorda", "yoz", "yozgan", "yozganman", "ekan", "edi", "deb", "nomli", "nomi",
    "nomidagi", "ichida", "salom", "assalomu", "alaykum", "rahmat", "kim", "nima", "qanday", "degan",
}
RECENT_WORDS = {"oxirgi", "songgi", "yangi", "bugungi", "kechagi", "yaqinda"}

TYPE_WORDS = {
    "word": {"word", "vord", "ворд", "docx", "doc", "vordda", "wordda", "wordli"},
    "pdf": {"pdf", "pdfda", "pdfli", "pedeef"},
    "excel": {"excel", "eksel", "exel", "xlsx", "xls", "exceldagi", "jadval", "jadvalda"},
    "slides": {"taqdimot", "prezentatsiya", "prezentasiya", "slayd", "slaydlar", "pptx", "ppt", "powerpoint"},
    "image": {"rasm", "surat", "foto", "jpg", "jpeg", "png", "skrinshot", "rasmi"},
}
TYPE_EXT = {
    "word": {".doc", ".docx", ".rtf", ".odt"}, "pdf": {".pdf"}, "excel": {".xls", ".xlsx", ".csv", ".ods"},
    "slides": {".ppt", ".pptx", ".odp"}, "image": {".jpg", ".jpeg", ".png", ".webp", ".gif"},
}
TYPE_NAME = {"word": "Word", "pdf": "PDF", "excel": "Excel", "slides": "taqdimot", "image": "rasm"}

# Polkalar (hujjat turi bo'yicha) — kalit so'zlar normallashtirilgan ko'rinishda.
SHELVES = [
    ("Dars ishlanmalari", "📘", "#1B4B7A", ["ishlanma", "ishlanmasi", "konspekt", "dars reja", "darsreja", "lesson plan", "dars ishlanma", "texnologik xarita"]),
    ("Test va nazorat ishlari", "📝", "#8B5FBF", ["test", "nazorat", "imtihon", "savol", "savollar", "quiz", "variant", "diktant", "bsb", "chsb", "olimpiada"]),
    ("Rejalar", "🗓️", "#28735A", ["taqvim", "tematik", "yillik reja", "reja", "kalendar", "ish reja", "ishreja", "jadval"]),
    ("Hisobot va tahlillar", "📊", "#C0762B", ["hisobot", "malumotnoma", "tahlil", "monitoring", "natija", "reyting", "statistika"]),
    ("Rasmiy hujjatlar", "🏛️", "#6B5B45", ["buyruq", "ariza", "bayonnoma", "nizom", "shartnoma", "yoriqnoma", "dalolatnoma", "xat", "farmoyish", "tavsifnoma", "obyektivka", "malumotnoma"]),
    ("Taqdimotlar", "🖥️", "#2F7D95", ["taqdimot", "prezentatsiya", "slayd"]),
    ("Metodik materiallar", "📚", "#7A4B1B", ["metodik", "qollanma", "darslik", "kitob", "maqola", "tavsiya", "uslubiy", "risola"]),
    ("Rasmlar", "🖼️", "#A34A6B", []),
]
OTHER_SHELF = ("Boshqa hujjatlar", "🗂️", "#8A8578")

SUBJECTS = [
    ("Matematika", ["matematika", "algebra", "geometriya", "arifmetika", "math"]),
    ("Fizika", ["fizika", "physics", "astronomiya"]),
    ("Kimyo", ["kimyo", "chemistry"]),
    ("Biologiya", ["biologiya", "botanika", "zoologiya", "anatomiya", "biology"]),
    ("Ona tili va adabiyot", ["ona tili", "onatili", "adabiyot", "oqish", "savod"]),
    ("Ingliz tili", ["ingliz", "english"]),
    ("Rus tili", ["rus tili", "rustili", "russkiy", "russian"]),
    ("Nemis / fransuz tili", ["nemis", "fransuz", "deutsch", "french"]),
    ("Tarix", ["tarix", "history"]),
    ("Geografiya", ["geografiya", "geography"]),
    ("Informatika", ["informatika", "axborot", "dasturlash", "kompyuter"]),
    ("Huquq va tarbiya", ["huquq", "tarbiya", "odobnoma", "davlat"]),
    ("Musiqa va tasviriy san'at", ["musiqa", "tasviriy", "chizmachilik", "rasm chizish"]),
    ("Jismoniy tarbiya", ["jismoniy", "sport"]),
    ("Texnologiya", ["texnologiya", "mehnat"]),
    ("Boshlang'ich ta'lim", ["boshlangich", "alifbo", "bogcha", "maktabgacha"]),
]
GENERAL_ROW = "Umumiy"


def translit(text):
    return "".join(_CYR.get(ch, ch) for ch in str(text or "").lower())


def norm(text):
    """Kichik harf, lotin, tutuqsiz, faqat harf-raqam va bo'shliq."""
    t = _APOS.sub("", translit(text))
    t = re.sub(r"[^0-9a-z]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def stem(tok):
    for suf in SUFFIXES:
        if tok.endswith(suf) and len(tok) - len(suf) >= 3:
            base = tok[: -len(suf)]
            # buyrug'ini → buyrug → buyruq (q/k oxirida g' ga aylanadi)
            return base[:-1] + "q" if base.endswith("g") and len(base) >= 4 and suf[0] in "aiu" else base
    for suf in ("gimni", "gini", "ging", "gim", "gi"):   # buyrug'i → buyruq, tilagi → tilaq≈tilak
        if tok.endswith(suf) and len(tok) - len(suf) >= 4:
            return tok[: -len(suf)] + "q"
    return tok


def skeleton(tok):
    """Tez-tez uchraydigan imlo chalkashliklarini bir xil ko'rinishga keltiradi."""
    s = tok.replace("q", "k").replace("h", "x").replace("ts", "s").replace("e", "i").replace("o", "u").replace("w", "v")
    return re.sub(r"(.)\1+", r"\1", s)


def tokens(text):
    return [t for t in norm(text).split() if t]


def token_score(q, d):
    """Bitta so'rov so'zi va hujjat so'zi qanchalik mos: 0..1."""
    if q == d:
        return 1.0
    qs, ds = stem(q), stem(d)
    if qs == ds:
        return 0.97
    if len(qs) >= 3 and (d.startswith(qs) or ds.startswith(qs)):
        return 0.9
    if q.isdigit() or d.isdigit():
        return 0.0
    qk, dk = skeleton(qs), skeleton(ds)
    if qk == dk:
        return 0.9
    if len(qk) >= 4 and len(dk) >= 4:
        r = SequenceMatcher(None, qk, dk).ratio()
        if r >= 0.8:
            return round(r * 0.88, 3)
        if len(dk) > len(qk) + 1 and dk.startswith(qk[:-1]):
            return 0.75
    return 0.0


def is_stopword(tok):
    if tok in STOPWORDS or stem(tok) in STOPWORDS:
        return True
    if len(tok) >= 5:
        sk = skeleton(stem(tok))
        for w in STOPWORDS:
            if len(w) >= 5 and SequenceMatcher(None, sk, skeleton(w)).ratio() >= 0.88:
                return True
    return False


def parse_query(text):
    """So'rov → {sozlar, turlar, yangi}: kerakli so'zlar, fayl turi filtrlari, «oxirgi» ishorasi."""
    words, kinds, recent = [], set(), False
    for tok in tokens(text):
        kind = next((k for k, vals in TYPE_WORDS.items() if tok in vals or stem(tok) in vals), None)
        if kind:
            kinds.add(kind)
            continue
        if tok in RECENT_WORDS:
            recent = True
            continue
        if is_stopword(tok):
            continue
        if len(tok) == 1 and not tok.isdigit():
            continue
        words.append(tok)
    return {"sozlar": words, "turlar": sorted(kinds), "yangi": recent}


def ext_of(name):
    m = re.search(r"(\.[A-Za-z0-9]{1,5})$", str(name or ""))
    return m.group(1).lower() if m else ""


def kind_of(name):
    e = ext_of(name)
    return next((k for k, exts in TYPE_EXT.items() if e in exts), "")


FIELD_WEIGHTS = (("nomi", 1.0), ("fayl_nomi", 0.95), ("teglar", 0.9), ("izoh", 0.8), ("qator", 0.72), ("polka", 0.7), ("matn", 0.62))


def doc_fields(doc):
    out = {}
    for field, _w in FIELD_WEIGHTS:
        val = doc.get(field) or ""
        if isinstance(val, (list, tuple)):
            val = " ".join(str(v) for v in val)
        if field == "matn":
            val = str(val)[:60000]
        out[field] = set(tokens(val))
    return out


def score_doc(query, doc, fields=None):
    """0..1 — hujjat so'rovga qanchalik mos. Fayl turi mos kelmasa 0."""
    if query["turlar"] and kind_of(doc.get("fayl_nomi")) not in query["turlar"]:
        return 0.0, []
    words = query["sozlar"]
    if not words:
        return (0.5 if query["turlar"] or query["yangi"] else 0.0), []
    fields = fields or doc_fields(doc)
    total, hits = 0.0, []
    for q in words:
        best, where = 0.0, ""
        for field, weight in FIELD_WEIGHTS:
            toks = fields.get(field) or ()
            if not toks:
                continue
            if q in toks:
                s = weight
            else:
                s = max((token_score(q, d) for d in toks), default=0.0) * weight
            if s > best:
                best, where = s, field
            if best >= weight >= 0.95:
                break
        total += best
        if best > 0:
            hits.append(where)
    return round(total / len(words), 3), hits


def search(query_text, docs, limit=8):
    q = parse_query(query_text) if isinstance(query_text, str) else query_text
    scored = []
    for doc in docs:
        s, hits = score_doc(q, doc)
        if s >= 0.45:
            scored.append((s, str(doc.get("yaratilgan") or ""), doc, hits))
    scored.sort(key=lambda x: (x[0], x[1]) if not q["yangi"] else (x[1], x[0]), reverse=True)
    return q, [dict(d, ball=s, topildi=sorted(set(h)),
                    parcha=snippet(d.get("matn"), q["sozlar"]) if "matn" in h else "") for s, _t, d, h in scored[:limit]]


def vocabulary(docs):
    vocab = set()
    for doc in docs:
        for field in ("nomi", "teglar", "polka", "qator"):
            val = doc.get(field) or ""
            if isinstance(val, (list, tuple)):
                val = " ".join(val)
            vocab.update(t for t in tokens(val) if len(t) >= 4 and not t.isdigit())
    return vocab


def suggest_spelling(words, docs):
    """Topilmagan so'zlar uchun — kutubxonadagi eng yaqin so'z («… demoqchimisiz?»)."""
    vocab = vocabulary(docs)
    out = {}
    for w in words:
        if len(w) < 4 or w in vocab:
            continue
        best, bw = 0.0, ""
        for v in vocab:
            r = SequenceMatcher(None, skeleton(w), skeleton(v)).ratio()
            if r > best:
                best, bw = r, v
        if best >= 0.6:
            out[w] = bw
    return out


def _has(text_norm, keyword):
    kw = norm(keyword)
    if " " in kw:
        return kw in text_norm or kw.replace(" ", "") in text_norm.replace(" ", "")
    toks = text_norm.split()
    return any(t == kw or stem(t) == kw or (len(kw) >= 5 and t.startswith(kw)) or
               (len(kw) >= 6 and token_score(kw, t) >= 0.8) for t in toks)


def classify(file_name, text="", shelves=None):
    """Yangi hujjat uchun (polka, qator) taklifi. shelves — o'qituvchining mavjud polka nomlari."""
    head = norm(file_name.rsplit(".", 1)[0] if "." in str(file_name) else file_name)
    body = norm(str(text or "")[:4000])
    kind = kind_of(file_name)
    # 1) O'qituvchining o'z polkasi nomi fayl nomida bo'lsa — o'sha.
    for name in shelves or ():
        n = norm(name)
        if n and len(n) >= 4 and n not in {norm(s[0]) for s in SHELVES} and _has(head, n):
            shelf = name
            break
    else:
        shelf = None
    if not shelf:
        if kind == "image":
            shelf = "Rasmlar"
        else:
            def pick(src):
                for name, _i, _c, kws in SHELVES:
                    if any(_has(src, k) for k in kws):
                        return name
                return None
            shelf = pick(head) or ("Taqdimotlar" if kind == "slides" else None) or pick(body[:1500]) or OTHER_SHELF[0]
    row = None
    for src in (head, body):
        for name, kws in SUBJECTS:
            if any(_has(src, k) for k in kws):
                row = name
                break
        if row:
            break
    if not row:
        m = re.search(r"\b(\d{1,2})\s*(?:sinf|sinfi|sinflar|class|grade)\b", head + " " + body[:800])
        row = f"{int(m.group(1))}-sinf" if m and 1 <= int(m.group(1)) <= 11 else GENERAL_ROW
    return shelf, row


def shelf_style(name):
    for n, icon, color, _k in SHELVES + [OTHER_SHELF + ([],)]:
        if n == name:
            return icon, color
    return "📁", "#1B4B7A"


# ─── Hujjat ichidagi matnni o'qish (faqat o'qituvchi ruxsat bergan bo'lsa) ─────────────────────────
def _xml_text(xml, para_tag):
    xml = re.sub(rf"</{para_tag}>", "\n", xml)
    xml = re.sub(r"<[^>]+>", " ", xml)
    for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'")):
        xml = xml.replace(a, b)
    return re.sub(r"[ \t]+", " ", xml)


def extract_text(file_name, data, limit=200000):
    ext = ext_of(file_name)
    try:
        if ext in (".docx", ".pptx", ".xlsx"):
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                names = z.namelist()
                if ext == ".docx":
                    parts = [n for n in names if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n)]
                    tag = "w:p"
                elif ext == ".pptx":
                    parts = sorted((n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                                   key=lambda n: int(re.findall(r"\d+", n)[-1]))
                    tag = "a:p"
                else:
                    parts = [n for n in names if n == "xl/sharedStrings.xml"]
                    tag = "si"
                out = []
                for n in parts:
                    out.append(_xml_text(z.read(n).decode("utf-8", "ignore"), tag))
                    if sum(len(x) for x in out) > limit:
                        break
                return "\n".join(out)[:limit]
        if ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            out = []
            for page in reader.pages[:40]:
                out.append(page.extract_text() or "")
                if sum(len(x) for x in out) > limit:
                    break
            return "\n".join(out)[:limit]
        if ext in (".txt", ".csv", ".md"):
            for enc in ("utf-8", "cp1251", "latin-1"):
                try:
                    return data.decode(enc)[:limit]
                except UnicodeDecodeError:
                    continue
        if ext == ".rtf":
            t = data.decode("latin-1", "ignore")
            t = re.sub(r"\\'[0-9a-f]{2}|\\[a-z]+-?\d* ?|[{}]", " ", t)
            return re.sub(r"\s+", " ", t)[:limit]
    except Exception:
        return ""
    return ""


def snippet(text, words, width=90):
    """Hujjat ichidan topilgan joy atrofidagi qisqa parcha."""
    if not text or not words:
        return ""
    low = translit(text)
    low = _APOS.sub("", low)
    for w in words:
        for cand in {w, stem(w)}:
            i = low.find(cand)
            if i >= 0 and len(cand) >= 3:
                a, b = max(0, i - width // 2), min(len(text), i + len(cand) + width // 2)
                return ("…" if a else "") + re.sub(r"\s+", " ", text[a:b]).strip() + ("…" if b < len(text) else "")
    return ""


# ─── Yordamchi suhbat ─────────────────────────────────────────────────────────────────────────────
def _place(doc):
    shelf = doc.get("polka") or "Saralanmagan"
    row = doc.get("qator")
    return f"📚 «{shelf}» polkasi" + (f", «{row}» qatori" if row else "")


def assistant_reply(message, docs, can_read_text=False, extra_words=None):
    """Deterministik yordamchi: har doim tushunarli javob; kerak bo'lsa aniqlashtiruvchi savol beradi."""
    text = str(message or "").strip()
    q = parse_query(text)
    if extra_words:   # AI to'g'rilagan kalit so'zlar — buzilgan so'zlar o'rniga
        q2 = parse_query(" ".join(extra_words))
        q["sozlar"] = q2["sozlar"] or q["sozlar"]
        q["turlar"] = sorted(set(q["turlar"]) | set(q2["turlar"]))
    nt = norm(text)
    if not docs:
        return {"turi": "bosh", "javob": "Kutubxonangiz hozircha bo‘sh. «➕ Hujjat qo‘shish» tugmasi bilan Word, PDF, Excel yoki taqdimot yuklang — men ularni o‘zim polka va qatorlarga tartiblab qo‘yaman.", "hujjatlar": []}
    if re.search(r"\b(tartibla|tartibga|sarala|saralab|joylashtir|taxla)", nt):
        loose = [d for d in docs if not d.get("polka")]
        if loose:
            return {"turi": "tartib", "javob": f"{len(loose)} ta hujjat hali polkaga qo‘yilmagan. «Tartibla» tugmasini bossangiz, ularni turiga va faniga qarab polka-qatorlarga o‘zim joylayman.", "hujjatlar": loose[:6], "amal": "tartibla"}
        return {"turi": "tartib", "javob": "Hamma hujjatlaringiz joy-joyida — saralanmagan hujjat yo‘q ✅", "hujjatlar": []}
    if not q["sozlar"] and not q["turlar"] and not q["yangi"]:
        if re.search(r"\b(salom|assalom)", nt):
            return {"turi": "savol", "javob": "Assalomu alaykum! Qaysi hujjatni topay? Nomidan yoki ichidagi 1–2 so‘zni yozing, masalan: «5-sinf matematika nazorat ishi» yoki «oxirgi PDF».", "hujjatlar": []}
        return {"turi": "savol", "javob": "Aniqroq yozing: qaysi hujjat kerak? Nomidagi yoki ichidagi so‘zlardan, fanidan, sinfidan yoki turidan (Word/PDF) yozsangiz, darhol topaman.", "hujjatlar": []}
    q, found = search(q, docs)
    if found and q["sozlar"]:
        best = found[0]["ball"]
        strong = [d for d in found if d["ball"] >= best - 0.12]
        if best < 0.6:   # faqat qisman mos — taxmin sifatida ko'rsatib, aniqlashtirishni so'raymiz
            return {"turi": "taklif", "javob": "Aynan mos hujjat topilmadi, lekin shular o‘xshaydi. Shulardan birimi? Bo‘lmasa, nomidan yana bir so‘z yozing.",
                    "hujjatlar": found[:6]}
    else:
        strong = found[:6]
    kinds = ", ".join(TYPE_NAME[k] for k in q["turlar"])
    if not found:
        fixes = suggest_spelling(q["sozlar"], docs)
        if fixes:
            fixed = [fixes.get(w, w) for w in q["sozlar"]]
            _q2, again = search({"sozlar": fixed, "turlar": q["turlar"], "yangi": q["yangi"]}, docs)
            tips = ", ".join(f"«{a}» o‘rniga «{b}»" for a, b in fixes.items())
            if again:
                return {"turi": "taklif", "javob": f"Aynan shunday yozilgani yo‘q, lekin {tips} demoqchi bo‘lsangiz — mana topganlarim. To‘g‘rimi?",
                        "hujjatlar": again[:6], "tuzatish": fixes}
            return {"turi": "savol", "javob": f"Topolmadim. {tips} demoqchimisiz? Aniqroq yozing — fan, sinf yoki hujjat turi (Word/PDF).", "hujjatlar": [], "tuzatish": fixes}
        hint = "" if can_read_text else " Hujjatlar ichini o‘qishga ruxsat bersangiz (⚙️ sozlamada), ichidagi so‘z bo‘yicha ham qidiraman."
        what = f" ({kinds})" if kinds else ""
        return {"turi": "savol", "javob": f"«{' '.join(q['sozlar']) or kinds}»{what} bo‘yicha hech narsa topilmadi. Boshqacha yozib ko‘ring: hujjat nomidagi so‘z, fan yoki sinf.{hint}", "hujjatlar": []}
    if len(strong) == 1 or (q["yangi"] and found):
        d = strong[0] if strong else found[0]
        where = _place(d)
        extra = f"\n🔎 Ichida: {d['parcha']}" if d.get("parcha") else ""
        return {"turi": "topildi", "javob": f"Topdim ✅ «{d.get('nomi')}» — {where}.{extra}\nOchasizmi yoki yuklab olasizmi?", "hujjatlar": [d]}
    shelves = sorted({d.get("polka") or "Saralanmagan" for d in strong})
    ask = "Qaysi biri kerak? "
    if len(shelves) > 1:
        ask += "Turli polkalarda turibdi (" + ", ".join(shelves[:4]) + "). "
    if not q["turlar"]:
        ask += "Word yoki PDF ekanini, sinf yoki yilini yozsangiz, bittasini aniq topaman."
    else:
        ask += "Sinf, fan yoki yilini qo‘shib yozing."
    return {"turi": "tanlash", "javob": f"{len(strong)} ta o‘xshash hujjat topdim. {ask}", "hujjatlar": strong[:6]}

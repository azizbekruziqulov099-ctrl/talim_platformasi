"""REV111: miyadagi til teglarini tuzatish — har bir chet so'z/gap o'z tilining ovozida, o'zbekcha (yoki izoh tili) o'z ovozida
o'qilsin. Avval test va bellashuvlarda ba'zi chet iboralar tegsiz qolib o'zbekcha o'qilardi, ba'zi o'zbekcha variantlar esa
chet til tegiga tushib qolardi.

1) Test variantlari: o'zbekcha ekani aniq bo'lsa (manba «uz_aniq.variant») — tegsiz; aks holda — chet til tegi.
2) Ovoz matni: tegsiz qolgan chet til bo'laklari teglanadi — lotin bo'lmagan tillarda shu yozuvdagi hamma bo'lak,
   lotin yozuvli tillarda kitobdagi ma'lum ibora va gaplar (2+ so'z yoki o'zbekchada uchramaydigan so'z).
3) izoh != uz bo'lsa: qolgan tegsiz matn izoh tili tegiga olinadi ([ru]…[/ru] yoki [en]…[/en]) — aks holda o'zbekcha o'qiladi.
"""
import json
import re
from collections import Counter
from pathlib import Path

LANGS = ("en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh")
TAG = re.compile(r"\[(en|ru|de|fr|es|ar|tr|zh|ja|ko|uz)\]([\s\S]*?)\[/\1\]")
VOICE = ("matn", "yechim", "sodda", "boshqa_usul")
SCRIPT = {
    "ru": r"Ѐ-ӿ", "ar": r"؀-ۿݐ-ݿ", "ko": r"가-힯ᄀ-ᇿ㄰-㆏",
    "ja": r"぀-ヿ一-鿿　-〿！-｠", "zh": r"一-鿿　-〿！-｠",
}
EMOJI = re.compile(r"^((?:[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿️‍⃣#*0-9]|\s)+)")
_UZ = {}
IZOH_DIR = Path(__file__).resolve().parent / "bogcha_content" / "izoh"


def uz_variants(izoh="uz"):
    """O'zbekcha ekani aniq test variantlari (izoh tilida — ularning tarjimasi)."""
    if izoh not in _UZ:
        import hashlib
        p = IZOH_DIR / "manba.json"
        data = json.loads(p.read_text(encoding="utf-8")).get("uz_aniq") if p.is_file() else {}
        src = (data or {}).get("variant", [])
        out = {_norm(x) for x in src}
        if izoh not in (None, "uz") and (IZOH_DIR / f"{izoh}.json").is_file():
            t = json.loads((IZOH_DIR / f"{izoh}.json").read_text(encoding="utf-8")).get("t", {})
            sid = lambda x: "s" + hashlib.sha1(x.encode("utf-8")).hexdigest()[:10]  # noqa: E731
            for x in src:
                em = EMOJI.match(x)
                pic = em.group(1).strip() if em else ""
                word = x[em.end():].strip() if em else x
                for cand in (t.get(sid(x)), t.get(sid(word)) and (pic + " " + t[sid(word)]).strip()):
                    if cand:
                        out.add(_norm(cand))
        _UZ[izoh] = out
    return _UZ[izoh]


def _norm(text):
    return re.sub(r"\s+", " ", TAG.sub(lambda m: m.group(2), str(text or ""))).strip().lower()


def book_lang(book):
    c = Counter(m.group(1) for t in book.get("topics", []) for r in t.get("rows", []) for m in TAG.finditer(str(r.get("matn") or "")))
    return c.most_common(1)[0][0] if c else None


def _segments(text):
    """[(tag|None, body)]"""
    out, pos = [], 0
    for m in TAG.finditer(text):
        if m.start() > pos:
            out.append((None, text[pos:m.start()]))
        out.append((m.group(1), m.group(2)))
        pos = m.end()
    if pos < len(text):
        out.append((None, text[pos:]))
    return out


def _join(segs):
    return "".join(body if tag is None else f"[{tag}]{body}[/{tag}]" for tag, body in segs)


def fix_option(line, lang, izoh="uz"):
    m = re.match(r"^(\s*[A-D]\)\s*)(.*)$", line)
    if not m or not lang:
        return line
    head, body = m.groups()
    plain = TAG.sub(lambda x: x.group(2), body).strip()
    em = EMOJI.match(plain)
    pic = em.group(1).strip() if em else ""
    word = plain[em.end():].strip() if em else plain
    if not word:
        return line
    if _norm(plain) in uz_variants(izoh):
        return f"{head}{plain}"
    return f"{head}{pic + ' ' if pic else ''}[{lang}]{word}[/{lang}]"


def fix_voice(text, lang, phrases):
    if not text or not lang:
        return text
    segs = _segments(str(text))
    out = []
    for tag, body in segs:
        if tag is not None:
            out.append((tag, body))
            continue
        if lang in SCRIPT:
            rx = re.compile(rf"([{SCRIPT[lang]}][{SCRIPT[lang]}\s\d,.!?…:;«»\"'\-—–]*[{SCRIPT[lang]}!?.…。！？])|([{SCRIPT[lang]}])")
        else:
            rx = phrases
        pos = 0
        for m in rx.finditer(body) if rx is not None else []:
            if m.start() > pos:
                out.append((None, body[pos:m.start()]))
            out.append((lang, m.group(0)))
            pos = m.end()
        out.append((None, body[pos:]))
    return _join([s for s in out if s[1]])


def wrap_izoh(text, izoh):
    if not text or izoh in (None, "uz"):
        return text
    out = []
    for tag, body in _segments(str(text)):
        if tag is None and re.search(r"[^\W\d_]", body):
            lead = re.match(r"^\s*", body).group(0)
            trail = re.search(r"\s*$", body).group(0)
            core = body[len(lead):len(body) - len(trail)] if trail else body[len(lead):]
            out.append((None, lead))
            out.append((izoh, core))
            out.append((None, trail))
        else:
            out.append((tag, body))
    return _join([s for s in out if s[1]])


def _phrase_rx(book):
    """Lotin yozuvli tillar: kitobdagi ma'lum ibora va gaplar (2+ so'z) — tegsiz uchrasa teglanadi."""
    items = set()
    for t in book.get("topics", []):
        for w in t.get("words", []):
            for k in ("say", "en", "sentence"):
                v = re.sub(r"[.!?…]+$", "", str(w.get(k) or "")).strip()
                if len(v.split()) >= 2:
                    items.add(v)
        for r in t.get("rows", []):
            for k in VOICE:
                for m in TAG.finditer(str(r.get(k) or "")):
                    v = re.sub(r"[.!?…]+$", "", m.group(2)).strip()
                    if len(v.split()) >= 2 and len(v) <= 80:
                        items.add(v)
    if not items:
        return None
    alts = sorted((re.escape(x) for x in items), key=len, reverse=True)
    return re.compile(r"(?<![\w'])(?:" + "|".join(alts) + r")[.!?…]?(?![\w'])", re.I)


def fix_book(book, izoh="uz", lang=None):
    """Kitobni joyida tuzatadi; o'zgargan maydonlar sonini qaytaradi."""
    lang = lang or book_lang(book)
    rx = None if lang in SCRIPT else _phrase_rx(book)
    n = 0
    for t in book.get("topics", []):
        for r in t.get("rows", []):
            if r.get("variantlar"):
                new = "\n".join(fix_option(x, lang, izoh) for x in str(r["variantlar"]).split("\n"))
                new = new if izoh in (None, "uz") else "\n".join(_opt_izoh(x, izoh) for x in new.split("\n"))
                n += new != r["variantlar"]
                r["variantlar"] = new
            for k in VOICE:
                if r.get(k):
                    new = wrap_izoh(fix_voice(r[k], lang, rx), izoh)
                    n += new != r[k]
                    r[k] = new
    return n


def _opt_izoh(line, izoh):
    m = re.match(r"^(\s*[A-D]\)\s*)(.*)$", line)
    if not m or TAG.search(m.group(2)):
        return line
    head, body = m.groups()
    em = EMOJI.match(body)
    pic = em.group(1) if em else ""
    word = body[len(pic):].strip()
    return f"{head}{pic}[{izoh}]{word}[/{izoh}]" if word else line

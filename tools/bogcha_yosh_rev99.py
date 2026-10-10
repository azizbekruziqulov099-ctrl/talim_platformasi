"""REV99: bog'cha til kitoblari yangi yosh guruhlariga: 2-3, 4-5, 6-7 yosh (10 til).

  2-3 yosh = 3-4 kitobi, soddalashtirilgan (tools/bogcha_23.py → <til>_23.json)
  4-5 yosh = 4-5 kitobi + 5-6 kitobidan: «Ovqat va ichimliklar», «Uyim va xonalar», «Ob-havo va fasllar»
  6-7 yosh = 6-7 kitobi + 5-6 kitobidan: «Menga yoqadi, yoqmaydi», «Menda bor, qila olaman»
5-6 kitobining qolgan bo'limlari (salom, oila, kiyim) 4-5 kitobida bor — takrorlanmaydi.

O'zbekcha gaplar robot Kabu tilida: bolaga «sen» deb murojaat, «Kabutar qushcha, Gu-gu» → «robot Kabu, Bip-bip».
[xx]…[/xx] ichidagi chet tili matniga tegilmaydi (tarjimalar o'zgarmaydi).

Ishlatish: python tools/bogcha_yosh_rev99.py   → tools/bogcha_content/<til>_45y.json, <til>_67y.json
"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.bogcha_spiral import merge_enrich, validate  # noqa: E402

ROOT = Path(__file__).resolve().parent / "bogcha_content"
LANGS = ("en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh")
ALL = None   # plus faylning hamma bo'limlari
PLAN = {
    "23y": ("23", (), "2-3 yosh", "2–3 yosh"),
    "45y": ("45", (("56", (3, 4, 5)),), "4-5 yosh", "4–5 yosh"),
    "67y": ("67", (("56", (6, 7)),), "6-7 yosh", "6–7 yosh"),
}
# REV110: yangi darslar — platformada 2–3 yoshda 50, 4–5 da 80, 6–7 da 100 dars. Ular allaqachon «sen» va robot Kabu
# uslubida yozilgan, shuning uchun warm() dan keyin qo'shiladi.
PLUS = {"23y": "23p", "45y": "45p", "67y": "67p"}
SPLIT = re.compile(r"(\[[a-z]{2}\][\s\S]*?\[/[a-z]{2}\])")

# «siz» → «sen»: aniq so'zlar (birinchi) va qo'shimcha qoidalari (keyin). Faqat o'zbekcha bo'laklarga qo'llanadi.
WORDS = {
    "siz": "sen", "Siz": "Sen", "sizga": "senga", "Sizga": "Senga", "sizni": "seni", "Sizni": "Seni",
    "sizning": "sening", "Sizning": "Sening", "sizda": "senda", "Sizda": "Senda", "sizdan": "sendan",
    "sizlar": "sizlar", "Keling": "Qani", "keling": "qani", "Kelinglar": "Qani", "kelinglar": "qani",
    "Tayyormisiz": "Tayyormisan", "tayyormisiz": "tayyormisan", "Esingizdami": "Esingdami", "esingizdami": "esingdami",
    "Topdingizmi": "Topdingmi", "topdingizmi": "topdingmi", "Chanqadingizmi": "Chanqadingmi", "eshityapsizmi": "eshityapsanmi",
    "Eshityapsizmi": "Eshityapsanmi", "hidlayapsizmi": "hidlayapsanmi", "Hidlayapsizmi": "Hidlayapsanmi",
}
NOT_IMPERATIVE = {"bilan", "ning", "qiling", "yaxshilik", "o'ring", "ming", "ring", "king", "sing", "tong", "kuzning",
                  "qishning", "yozning", "bahorning", "ertaning", "uyning", "kunning", "shoving", "ning"}


def _english_vocab():
    try:
        src = json.loads((ROOT / "tarjima" / "manba.json").read_text(encoding="utf-8"))["matnlar"]
    except Exception:
        return set()
    return {w.lower() for item in src.values() for w in re.findall(r"[A-Za-z']+", item.get("en", ""))}


ENGLISH = _english_vocab()
# Qushga xos gaplar → robot Kabuga mos (faqat o'zbekcha bo'laklar).
ROBOT = {
    "Men donni yaxshi ko'raman": "Men batareykamni yaxshi ko'raman",
    "Men uya qurdim": "Mening temir uycham bor",
    "qishda esa patlarimni hurpaytiraman": "qishda esa antennamni isitaman",
    "Men katta donni ko'tarolmayapman": "Men katta qutini ko'tarolmayapman",
    "qanotlarim bilan qalam ushlab bo'lmaydi": "temir qo'llarim bilan qalam sirpanib ketadi",
    "patlarim ho'l bo'ladi": "zang bosib qolaman",
    "Birga donni ko'taramiz": "Birga qutini ko'taramiz",
}
KEEP_NG = {"barang", "rang", "jigarrang", "kulrang", "tong", "keng", "teng", "ming", "bodring", "ring", "zang", "jang"}


def _word_sen(w, nxt=""):
    """nxt — so'zdan keyingi belgilar (buyruqni egalikdan ajratish uchun)."""
    if w in WORDS:
        return WORDS[w]
    if w.startswith("Kabutar"):
        return "Kabu" + w[len("Kabutar"):]
    w2 = re.sub(r"(moqchimi|moqchi|chi|paz|chi?)siz$", lambda m: m.group(1) + "san", w)
    if w2 != w and len(w) > 7:
        return w2
    low = w.lower()
    if low in ENGLISH or low.startswith(("dengiz", "tugmangiz")):
        return w
    # egalik: -ingiz / -ngiz (+ kelishik) → -ing / -ng
    w2 = re.sub(r"(i?n)giz(ni|ga|da|dan|ning|dagi|cha)?$", lambda m: m.group(1) + "g" + (m.group(2) or ""), w)
    if w2 != w and len(w) > 6:
        return w2
    # o'tgan zamon / shart: -dingiz, -sangiz (+mi) → -ding, -sang
    w2 = re.sub(r"([dt]i|sa)ngiz(mi)?$", lambda m: m.group(1) + "ng" + (m.group(2) or ""), w)
    if w2 != w:
        return w2
    # hozirgi-kelasi: -asiz/-ysiz/-yapsiz/-misiz (+mi) → -asan/-ysan/-yapsan
    w2 = re.sub(r"(a|y|yap|ya|qchi)siz(mi)?$", lambda m: m.group(1) + "san" + (m.group(2) or ""), w)
    if w2 != w and len(w) > 5:
        return w2
    # buyruq: faqat gap ichida buyruq o'rnida turganda (keyin «!», «,», «:», «.», «va», «—»)
    if not re.match(r"\s*(?:[!,:.—–]|va\b|$)", nxt) or low.endswith("ning") or low in KEEP_NG or len(w) <= 4:
        return w
    m = re.fullmatch(r"(.+?[^aeiou'‘’ʻʼ])ing", w)
    if m:
        return m.group(1)
    m = re.fullmatch(r"(.+?[aeiou])ng", w)
    if m:
        return m.group(1)
    return w


def sen(text):
    """Faqat o'zbekcha qismlarda «siz» → «sen», robot Kabu. [xx]…[/xx] bo'laklarga tegilmaydi."""
    if not text:
        return text
    out = []
    for n, chunk in enumerate(SPLIT.split(str(text))):
        if n % 2:   # chet tili bo'lagi
            out.append(chunk)
            continue
        for old, new in ROBOT.items():
            chunk = chunk.replace(old, new)
        chunk = re.sub(r"Kabutar qushcha(man)?", lambda m: "robot Kabu" + ("man" if m.group(1) else ""), chunk)
        chunk = re.sub(r"\bGu-gu(-gu)*\b!?", "Bip-bip!", chunk)
        chunk = re.sub(r"[A-Za-zʻ’‘'ʼ]+(?=(.{0,4}))", lambda m: _word_sen(m.group(0), m.group(1)), chunk, flags=re.S)
        out.append(chunk)
    return "".join(out)


def warm(book):
    for unit in book["units"]:
        for les in unit["lessons"] + (unit.get("scenarios") or []):
            for k in ("intro",):
                les[k] = sen(les.get(k))
            for it in les.get("items") or []:
                if it.get("action"):
                    it["action"] = sen(it["action"])
            for row in les.get("extra") or []:
                for k in ("matn", "sodda", "boshqa_usul"):
                    if row.get(k):
                        row[k] = sen(row[k])
            for t in (les.get("tests") or []) + (les.get("questions") or []):
                t["q"] = sen(t["q"])
                if t.get("why"):
                    t["why"] = sen(t["why"])
    return book


def load(lang, age):
    cur = json.loads((ROOT / f"{lang}_{age}.json").read_text(encoding="utf-8"))
    enrich = ROOT / f"{lang}_{age}_enrich.json"
    return merge_enrich(cur, json.loads(enrich.read_text(encoding="utf-8"))) if enrich.is_file() else cur


def compose(lang, key):
    base, extras, age, label = PLAN[key]
    book = copy.deepcopy(load(lang, base))
    for src, idx in extras:
        other = load(lang, src)
        book["units"] += [copy.deepcopy(other["units"][i]) for i in idx]
    book["age"] = age
    if key == "45y":   # REV121: 4–5 yosh — bola ko'p tushunsin: gaplar chet tilida, ma'nosi qavsda (3-pog'ona)
        book["immersion"] = 3
    book["book_title"] = re.sub(r"\d\s*[–-]\s*\d\s*yosh$", label, book.get("book_title", "")).strip()
    for unit in book["units"]:
        for sc in unit.get("scenarios") or []:
            sc.pop("unit", None)
    if key != "23y":   # 2–3 kitobi (bogcha_23.py) allaqachon «sen» uslubida — qayta o'girilsa buziladi
        warm(book)
    if (ROOT / f"{lang}_{PLUS[key]}.json").is_file():
        plus = load(lang, PLUS[key])
        for unit in plus["units"]:
            for sc in unit.get("scenarios") or []:
                sc.pop("unit", None)
        book["units"] += copy.deepcopy(plus["units"])
    if age == "4-5 yosh":   # 5-6 kitobidan kelgan savollarda 3 variant — 4-5 yoshga 2 tasi yetadi
        for unit in book["units"]:
            for q in [q for les in unit["lessons"] for q in les.get("tests") or []] + \
                     [q for sc in unit.get("scenarios") or [] for q in sc.get("questions") or []]:
                if len(q["options"]) > 2:
                    right = q["options"][q["answer"]]
                    other = next(o for i, o in enumerate(q["options"]) if i != q["answer"])
                    q["options"] = [right, other] if q["answer"] == 0 else [other, right]
                    q["answer"] = q["options"].index(right)
    validate(book)
    (ROOT / f"{lang}_{key}.json").write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return book


if __name__ == "__main__":
    for lang in LANGS:
        for key in PLAN:
            b = compose(lang, key)
            print(lang, key, b["age"], len(b["units"]), "bo'lim", sum(len(u["lessons"]) for u in b["units"]), "dars")

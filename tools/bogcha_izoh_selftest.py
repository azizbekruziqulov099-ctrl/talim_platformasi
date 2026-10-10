"""REV111: izoh tili o'z-o'zini tekshirish — o'zbekcha matn izoh != uz kitobga «sizib» o'tmaganini tekshiradi.

Soxta lug'at: manba.json dagi har o'zbekcha matn → «matn». Kitob izoh=ru bilan quriladi; har qator matnida
[xx]…[/xx] teglari va «…» bo'laklari olib tashlangach qolgan har so'z chet tilidagi lug'atda (kitobning chet tilidagi
maydonlari) yoki ismlar ro'yxatida bo'lishi shart — aks holda o'sha so'z U()/UZ()/TX() dan o'tmagan (sizib chiqqan).

Ishlatish: python tools/bogcha_izoh_selftest.py [til ...]     (standart: en ru; avval `bogcha_izoh.py extract`)
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import bogcha_spiral as sp  # noqa: E402
from tools.bogcha_izoh import IZOH_DIR, KEYS, ROOT, SKIP, book_paths  # noqa: E402
from tools.bogcha_kitob import build_books  # noqa: E402

PROPER = {"ali", "laylo", "toshkent", "palov", "kabu", "miyov", "vov"}   # ismlar, joy/taom nomlari, tovush so'zlari
WORD = re.compile(r"[^\W\d_]+(?:['ʻ‘’][^\W\d_]+)*")
TAGGED = re.compile(r"\[([a-z]{2})\].*?\[/\1\]", re.S)
WRAPPED = re.compile(r"«[^«»]*»")
FIELDS = ("sarlavha", "matn", "doska", "sodda", "boshqa_usul", "yechim", "variantlar")


def words(text):
    return {w.lower() for w in WORD.findall(text or "")}


def foreign_vocab(lang, uz_aniq):
    """Kitobdagi chet tilidagi hamma so'zlar: say, sentence, *_en, rom, sinf iboralari, teg ichidagilar, chet variantlar,
    doskaning o'zbekcha bo'lmagan qismlari."""
    vocab = set()
    uz_variants, uz_doska = set(uz_aniq["variant"]), set(uz_aniq["doska"])

    def walk(node, key="", foreign=False):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, k, foreign or k == "class")
        elif isinstance(node, list):
            for v in node:
                walk(v, key, foreign)
        elif isinstance(node, str):
            for m in TAGGED.finditer(node):
                vocab.update(words(m.group(0)))
            if foreign or key in SKIP:
                vocab.update(words(node))
            elif key == "options" and sp._clean(node) not in uz_variants:
                vocab.update(words(node))
            elif key == "doska":
                for line in node.split("\n"):
                    left, _, right = line.partition(" — ")
                    vocab.update(words(left))
                    if right not in uz_doska:
                        vocab.update(words(right))

    for k in KEYS:
        walk(json.loads((ROOT / f"{lang}_{k}.json").read_text(encoding="utf-8")))
    walk(sp.CLASS, foreign=True)
    return vocab


def leftover(text):
    text = TAGGED.sub(" ", text or "")
    prev = None
    while prev != text:
        prev, text = text, WRAPPED.sub(" ", text)
    return text


def run(langs=("en", "ru")):
    manba = json.loads((IZOH_DIR / "manba.json").read_text(encoding="utf-8"))
    fake = {key: "«" + e["uz"] + "»" for key, e in manba["matnlar"].items()}
    sp.IZOH_DICTS["ru"] = fake
    sp.IZOH_UZ_SETS = manba["uz_aniq"]
    sp.IZOH_ALLOW_MISSING = False      # qat'iy: manbada yo'q matn → KeyError
    total_fields = leaks = 0
    report = {}
    for lang in langs:
        vocab = foreign_vocab(lang, manba["uz_aniq"]) | PROPER | set("abcd")   # «A) B) C) D)» variant harflari
        books = build_books(book_paths(lang), izoh="ru")
        bad = {}
        for key, book in zip(KEYS, books):
            assert book.get("izoh") == "ru"
            texts = [("book_title", book["book_title"])]
            for t in book["topics"]:
                texts += [("topic.name", t["name"]), ("topic.goal", t["goal"])]
                texts += [("words.uz", w["uz"]) for w in t["words"]]
                for row in t["rows"]:
                    texts += [(f, row.get(f) or "") for f in FIELDS]
                    if row.get("turi") == "topshiriq":
                        assert row.get("yechim"), "topshiriq yechimi bo'sh (kitob o'zbekcha standartni qo'yadi)"
            for where, text in texts:
                total_fields += 1
                left = words(leftover(text)) - vocab
                if left:
                    leaks += 1
                    for w in left:
                        bad.setdefault(w, f"{key} {where}: {text[:140]}")
        report[lang] = bad
    return total_fields, leaks, report


if __name__ == "__main__":
    langs = sys.argv[1:] or ["en", "ru"]
    total, leaks, report = run(langs)
    for lang, bad in report.items():
        print(f"{lang}: sizib chiqqan so'zlar {len(bad)}")
        for w, ex in list(bad.items())[:25]:
            print(f"   {w!r:22} ← {ex}")
    print(f"tekshirilgan maydonlar: {total}, sizib chiqqan maydonlar: {leaks}")
    print("OK" if not leaks else "XATO")
    sys.exit(1 if leaks else 0)

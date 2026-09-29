"""REV81: bog'cha kitobi dvigateli — muallif yozgan o'quv dasturidan (CURRICULUM_SPEC.md) to'liq kitob.

Takror tizimi (spiral):
  • har dars «🔁 Eslaymiz» bilan boshlanadi — 1 va 3 dars oldingi bilimlar qayta aytiladi;
  • test: yangi savollar + eski savollar (1, 3, 7 dars oldingi) aralash;
  • har bo'lim oxirida TAKRORLASH darsi — bo'limning hamma bilimi, aralash test;
  • kitob oxirida KATTA BAYRAM — butun kitob bo'yicha yakuniy takror.
Natija: tools/bogcha_kitob.py qabul qiladigan kitob JSON (SPEC.md formati).

Ishlatish: python tools/bogcha_spiral.py dastur.json kitob.json   (tekshiradi va kitob yasaydi)
"""
import json
import random
import re
import sys
from pathlib import Path

TAG = {"en": ("[en]", "[/en]"), "ru": ("[ru]", "[/ru]")}
MAX_OPTIONS = {"2-3 yosh": 2, "3-4 yosh": 2, "4-5 yosh": 2, "5-6 yosh": 3, "6-7 yosh": 4}
TEXT_LIMIT = {"2-3 yosh": 220, "3-4 yosh": 220, "4-5 yosh": 300, "5-6 yosh": 400, "6-7 yosh": 400}
PRAISE = ["Barakalla!", "Zo'r!", "Ofarin!", "Qoyil!", "Ajoyib!", "Juda yaxshi!"]


class BookError(ValueError):
    pass


def _tag(lang, text):
    if not lang or not text:
        return text
    a, b = TAG[lang]
    return f"{a}{text}{b}"


def _clean(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _tagp(lang, text):
    """Teglangan so'z + gap oxiri belgisi (ovoz to'xtab oladi)."""
    text = _clean(text)
    return _tag(lang, text) + ("" if re.search(r"[.!?…]$", text) else ".")


def _sentence(text):
    text = _clean(text)
    return text if not text or re.search(r"[.!?…]$", text) else text + "."


def _name(lang, item):
    """Ovozda bilim nomi: tilda — teglangan so'z, boshqa fanda — tushuncha nomi."""
    return _tag(lang, _clean(item["say"])) if lang else _clean(item["say"])


def _word(item):
    """Test varianti uchun: tilda — so'zning o'zi, boshqa fanda — o'zbekcha nomi."""
    return _clean(item.get("say") or item.get("uz"))


def validate(cur):
    errors = []
    age = cur.get("age")
    if age not in MAX_OPTIONS:
        errors.append(f"age noto'g'ri: {age}")
    lang = cur.get("lang")
    if lang not in (None, "en", "ru"):
        errors.append("lang faqat en, ru yoki null")
    names = set()
    units = cur.get("units") or []
    if not units:
        errors.append("units bo'sh")
    for ui, unit in enumerate(units, 1):
        if not unit.get("lessons"):
            errors.append(f"{ui}-bo'lim: darslar yo'q")
        for li, lesson in enumerate(unit.get("lessons") or [], 1):
            where = f"{ui}.{li} «{lesson.get('name')}»"
            key = _clean(lesson.get("name")).lower()
            if not key:
                errors.append(f"{where}: nom yo'q")
            if key in names:
                errors.append(f"{where}: nom takrorlangan")
            names.add(key)
            items = lesson.get("items") or []
            if not items:
                errors.append(f"{where}: items bo'sh")
            for item in items:
                if not item.get("say") or not item.get("emoji"):
                    errors.append(f"{where}: item say/emoji yo'q")
                if not lang and not item.get("explain"):
                    errors.append(f"{where}: «{item.get('say')}» — explain majburiy")
            if not lang and len(lesson.get("tests") or []) < 3:
                errors.append(f"{where}: kamida 3 ta test kerak")
            for t in lesson.get("tests") or []:
                opts = t.get("options") or []
                if not 2 <= len(opts) <= 4 or not isinstance(t.get("answer"), int) or not 0 <= t["answer"] < len(opts):
                    errors.append(f"{where}: test noto'g'ri — {t.get('q', '')[:40]}")
    if errors:
        raise BookError("\n".join(errors[:40]))


class Builder:
    def __init__(self, cur):
        self.cur = cur
        self.lang = cur.get("lang")
        self.age = cur["age"]
        self.n_opts = MAX_OPTIONS[self.age]
        self.limit = TEXT_LIMIT[self.age]
        self.rng = random.Random(f"{cur.get('subject')}|{self.age}")
        self.pool = []          # o'tilgan barcha bilimlar (tartib bilan)
        self.lesson_items = []  # har dars bo'yicha bilimlar ro'yxati
        self.lesson_tests = []  # har dars bo'yicha test savollari (tayyor qator)
        self.topics = []

    # ── matnlar ──
    def t(self, text):
        return _clean(text)

    def item_voice(self, it, n):
        w = _tagp(self.lang, it["say"])
        act = f" {it['action']}" if it.get("action") else ""
        if not self.lang:
            return self.t(it["explain"] + act)
        if it.get("explain"):
            return self.t(f"{it['explain']} Men bilan takrorla: {w} Yana bir marta: {w}{act}")
        patterns = [
            f"Qarang, bu — {w} O'zbekcha — {it['uz']}. Men bilan takrorla: {w} Yana bir marta: {w}{act} Barakalla!",
            f"Yangi so'z: {w} Bu — {it['uz']} degani. Qani, baland ovozda ayting: {w} Endi sekin, shivirlab: {w}{act}",
            f"Diqqat bilan tinglang: {w} Bu — {it['uz']}. Men aytaman, siz takrorlaysiz: {w} Yana: {w}{act} Zo'r!",
        ]
        return self.t(patterns[n % len(patterns)])

    def item_simple(self, it):
        w = _tagp(self.lang, it["say"])
        if not self.lang:
            return self.t(f"Keling, sekinroq: {it['emoji']} bu — {it['uz'] or it['say']}. {it['explain'].split('.')[0]}.")
        return self.t(f"{it['uz'].capitalize()} — {w} Sekin ayting: {w}")

    def item_other(self, it):
        w = _tagp(self.lang, it["say"])
        if not self.lang:
            return self.t(f"Atrofingizga qarang: {it['uz'] or it['say']} qayerda bor? Barmog'ingiz bilan ko'rsating va ayting!")
        return self.t(f"Keling, o'yin! Men {it['uz']} desam, siz {w} deysiz. {it['uz'].capitalize()}! … {w} Barakalla!")

    def board(self, it):
        return f"{it['emoji']} {it['say']}" + (f"\n{it['uz']}" if self.lang and it.get("uz") else "")

    # ── testlar ──
    def q_pick(self, it):
        w = _tag(self.lang, it["say"]) if self.lang else it.get("uz") or it["say"]
        forms = [f"Qaysi rasm {w}?", f"Qani, toping: {w} qayerda?", f"{w} — qaysi biri?"]
        return self.rng.choice(forms)

    def make_test(self, question, correct, distractors, why, kind="auto"):
        opts = [correct] + distractors[: self.n_opts - 1]
        if len(opts) < 2:
            return None
        self.rng.shuffle(opts)
        letters = "ABCD"
        return {"turi": "test", "sarlavha": "O'ynaymiz!", "matn": self.t(question),
                "variantlar": "\n".join(f"{letters[i]}) {o}" for i, o in enumerate(opts)),
                "javob": letters[opts.index(correct)], "yechim": self.t(why), "_kind": kind}

    def auto_test(self, it):
        others = [x for x in self.pool if x is not it and x["emoji"] != it["emoji"] and _word(x) != _word(it)]
        self.rng.shuffle(others)
        # yaqinlari (shu bo'limdan) avval — bola farqlashni o'rgansin
        same = [x for x in others if x.get("_unit") == it.get("_unit")]
        pool = same + [x for x in others if x not in same]
        distract = [f"{x['emoji']} {_word(x)}" for x in pool[:3]]
        w = _tag(self.lang, it["say"]) if self.lang else it["say"]
        return self.make_test(self.q_pick(it), f"{it['emoji']} {_word(it)}", distract,
                              f"{self.rng.choice(PRAISE)} {it['emoji']} {w} — {it['uz']}." if self.lang else f"{self.rng.choice(PRAISE)} Bu — {it['uz'] or it['say']}.")

    def author_test(self, t):
        opts = list(t["options"])
        correct = opts[t["answer"]]
        others = [o for i, o in enumerate(opts) if i != t["answer"]]
        return self.make_test(t["q"], correct, others, t.get("why") or self.rng.choice(PRAISE), kind="author")

    def reverse_test(self, it):
        """5–7 yosh tilda: so'zni eshitib, o'zbekcha ma'nosini topish."""
        others = [x for x in self.pool if x is not it and x.get("uz") and x["uz"] != it["uz"]]
        self.rng.shuffle(others)
        return self.make_test(f"{_tag(self.lang, it['say'])} — o'zbekchasi nima?", f"{it['emoji']} {it['uz']}",
                              [f"{x['emoji']} {x['uz']}" for x in others[:3]], f"To'g'ri! {_tag(self.lang, it['say'])} — {it['uz']}.")

    # ── darslar ──
    def review_rows(self, index):
        rows = []
        for back in (1, 3):
            if index - back >= 0 and self.lesson_items[index - back]:
                it = self.rng.choice(self.lesson_items[index - back])
                if self.lang:
                    text = f"Esingizdami? {it['emoji']} Bu — {_tag(self.lang, it['say'])}, ya'ni {_sentence(it['uz'])} Qani, birga ayting!"
                else:
                    uz = _clean(it.get("uz"))
                    text = f"Esingizdami? {it['emoji']} {_sentence(it['say'])} {_sentence(uz[:1].upper() + uz[1:])} Qani, birga ayting!"
                rows.append({"turi": "tushuncha", "sarlavha": f"🔁 Eslaymiz: {it['emoji']} {it['say']}",
                             "matn": self.t(text),
                             "doska": self.board(it), "sodda": self.item_simple(it), "boshqa_usul": self.item_other(it)})
        return rows

    def lesson(self, unit_no, unit, lesson):
        index = len(self.lesson_items)
        items = [dict(it, _unit=unit_no) for it in lesson["items"]]
        rows = [{"turi": "kirish", "sarlavha": f"{unit.get('emoji', '🕊️')} {lesson['name']}",
                 "matn": self.t(lesson.get("intro") or f"Salom, do'stim! Men — Kabutar qushcha. Gu-gu! Bugun «{lesson['name']}» mavzusini o'rganamiz."),
                 "doska": f"🕊️ {lesson['name']}"}]
        rows += self.review_rows(index)
        for n, it in enumerate(items):
            rows.append({"turi": "tushuncha", "sarlavha": f"{it['emoji']} {it['say']}" + (f" — {it['uz']}" if self.lang and it.get("uz") else ""),
                         "matn": self.item_voice(it, n + index), "doska": self.board(it),
                         "sodda": self.item_simple(it), "boshqa_usul": self.item_other(it)})
        for row in lesson.get("extra") or []:
            rows.append({k: row.get(k, "") for k in ("turi", "sarlavha", "matn", "doska", "sodda", "boshqa_usul")})
        # O'yin: yangi so'zlar + bitta eski — «top-chi»
        game_items = items + ([self.rng.choice(self.pool)] if self.pool else [])
        names = ", ".join(_name(self.lang, x) for x in game_items)
        rows.append({"turi": "topshiriq", "sarlavha": "🎲 Top-chi o'yini",
                     "matn": self.t(f"O'yin vaqti! Men aytaman, siz ekrandagi rasmni barmog'ingiz bilan ko'rsatasiz: {names}. Tayyor bo'lsangiz — qarsak chaling!"),
                     "doska": "  ".join(x["emoji"] for x in game_items), "yechim": "Barakalla! Hammasini topdingiz! 🌟"})
        self.pool.extend(items)
        self.lesson_items.append(items)
        # Testlar: yangi (muallif + avto) va eski takror
        new_tests = [self.author_test(t) for t in lesson.get("tests") or []]
        if self.lang or not new_tests:
            new_tests += [self.auto_test(it) for it in items]
        if self.lang and self.age in ("5-6 yosh", "6-7 yosh") and items:
            new_tests.append(self.reverse_test(self.rng.choice(items)))
        new_tests = [t for t in new_tests if t]
        want_new = 3 if self.age in ("2-3 yosh", "3-4 yosh", "4-5 yosh") else 4
        tests = new_tests[:want_new]
        for back in (1, 3, 7):
            if index - back >= 0 and self.lesson_tests[index - back]:
                old = dict(self.rng.choice(self.lesson_tests[index - back]))
                old["sarlavha"] = "🔁 Eski savol"
                tests.append(old)
        self.lesson_tests.append(new_tests)
        rows += [{k: v for k, v in t.items() if not k.startswith("_")} for t in tests]
        rows.append({"turi": "xulosa", "sarlavha": "🌟 Bugun o'rgandik",
                     "matn": self.t(f"{self.rng.choice(PRAISE)} Bugun biz " + ", ".join(_name(self.lang, x) for x in items) + " ni o'rgandik. Ertaga yana uchrashamiz — yangi sir bor!"),
                     "doska": "  ".join(f"{x['emoji']} {x['say']}" for x in items)})
        self.topics.append(self.topic(lesson["name"], lesson.get("goal", ""), rows, items))

    def unit_review(self, unit_no, unit, start):
        items = [it for its in self.lesson_items[start:] for it in its]
        if not items:
            return
        rows = [{"turi": "kirish", "sarlavha": f"🔁 {unit['name']}: takrorlaymiz",
                 "matn": self.t(f"Gu-gu! Bugun katta takrorlash kuni! «{unit['name']}» bo'limida o'rgangan hamma narsani eslaymiz. Har to'g'ri javob — bitta yulduzcha!"),
                 "doska": "🔁 " + "  ".join(x["emoji"] for x in items)}]
        for i in range(0, len(items), 3):
            chunk = items[i:i + 3]
            voice = " ".join(f"{x['emoji']} {_name(self.lang, x)} — {_sentence(x.get('uz'))}" for x in chunk)
            rows.append({"turi": "tushuncha", "sarlavha": "Eslaymiz: " + " ".join(x["emoji"] for x in chunk),
                         "matn": self.t(f"{voice} Men bilan birga takrorla!"),
                         "doska": "\n".join(self.board(x).replace("\n", " — ") for x in chunk),
                         "sodda": self.t("Sekin-sekin: " + voice), "boshqa_usul": self.t("Har birini ko'rsatib, qarsak chalib ayting: " + voice)})
        rows.append({"turi": "topshiriq", "sarlavha": "🏃 Harakatli o'yin",
                     "matn": self.t("Men so'z aytaman: agar rasm ekranda bo'lsa — sakrang, bo'lmasa — o'tiring! Tayyormisiz? Boshladik!"),
                     "doska": "  ".join(x["emoji"] for x in items), "yechim": "Ofarin! Siz zo'r o'ynadingiz! 🌟"})
        pool_tests = [t for ts in self.lesson_tests[start:] for t in ts]
        self.rng.shuffle(pool_tests)
        count = 5 if self.age in ("2-3 yosh", "3-4 yosh", "4-5 yosh") else 7
        rows += [dict({k: v for k, v in t.items() if not k.startswith("_")}, sarlavha="⭐ Takror savoli") for t in pool_tests[:count]]
        rows.append({"turi": "xulosa", "sarlavha": "🏅 Bo'lim tugadi!",
                     "matn": self.t(f"Qoyil! «{unit['name']}» bo'limini tugatdingiz. Endi yangi sarguzashtga o'tamiz!"),
                     "doska": f"🏅 {unit['name']}"})
        self.topics.append(self.topic(f"{unit_no}-bo'lim takrori: {unit['name']}", f"«{unit['name']}» bo'limini mustahkamlash", rows, items[:6]))

    def final_review(self):
        rows = [{"turi": "kirish", "sarlavha": "🎉 Katta bayram!",
                 "matn": self.t("Gu-gu! Bugun katta bayram! Butun kitobni tugatdingiz. Keling, eng qiziq so'zlarni eslaymiz va o'yinda yulduzcha yig'amiz!"),
                 "doska": "🎉 Katta bayram"}]
        sample = self.pool[:]
        self.rng.shuffle(sample)
        for i in range(0, min(len(sample), 12), 4):
            chunk = sample[i:i + 4]
            voice = " ".join(f"{x['emoji']} {_sentence(_name(self.lang, x))}" for x in chunk)
            rows.append({"turi": "tushuncha", "sarlavha": "Eslaymiz: " + " ".join(x["emoji"] for x in chunk),
                         "matn": self.t(voice + " Ajoyib, hammasini bilasiz!"), "doska": "\n".join(self.board(x).replace("\n", " — ") for x in chunk)})
        all_tests = [t for ts in self.lesson_tests for t in ts]
        self.rng.shuffle(all_tests)
        rows += [dict({k: v for k, v in t.items() if not k.startswith("_")}, sarlavha="🎉 Bayram savoli") for t in all_tests[:10]]
        rows.append({"turi": "xulosa", "sarlavha": "🏆 Siz chempionsiz!",
                     "matn": self.t("Siz chempionsiz! Endi hammasini bilasiz. Istalgan darsni qayta ochib, takrorlab o'ynashingiz mumkin."),
                     "doska": "🏆"})
        self.topics.append(self.topic("Katta bayram: hammasini takrorlaymiz", "Butun kitobni mustahkamlash", rows, sample[:6]))

    def topic(self, name, goal, rows, items):
        return {"no": len(self.topics) + 1, "name": name, "goal": goal, "rows": rows,
                "words": [{k: it.get(k, "") for k in ("say", "uz", "emoji", "image", "image_prompt")} | {"en": it["say"]} for it in items]}

    def build(self):
        for unit_no, unit in enumerate(self.cur["units"], 1):
            start = len(self.lesson_items)
            for lesson in unit["lessons"]:
                self.lesson(unit_no, unit, lesson)
            self.unit_review(unit_no, unit, start)
        self.final_review()
        for topic in self.topics:
            for row in topic["rows"]:
                for key in ("matn", "sodda", "boshqa_usul", "yechim"):
                    if len(row.get(key) or "") > 1400:
                        row[key] = row[key][:1400]
        return {"age": self.age, "book_title": self.cur.get("book_title") or f"{self.cur['subject']} {self.age}",
                "subject": self.cur["subject"], "prefix": self.cur.get("prefix") or "BK", "topics": self.topics}


def build_book(cur):
    validate(cur)
    return Builder(cur).build()


def stats(book):
    tests = sum(1 for t in book["topics"] for r in t["rows"] if r["turi"] == "test")
    words = sum(len(t["words"]) for t in book["topics"] if "takror" not in t["name"].lower() and "bayram" not in t["name"].lower())
    return {"darslar": len(book["topics"]), "testlar": tests, "yangi_bilim": words}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    book = build_book(json.loads(Path(src).read_text(encoding="utf-8")))
    Path(dst).write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats(book), ensure_ascii=False))

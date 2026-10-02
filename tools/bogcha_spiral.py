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

LANGS = ("en", "ru", "ar", "tr", "de", "fr", "es", "ko", "ja", "zh")
TAG = {code: (f"[{code}]", f"[/{code}]") for code in LANGS}
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
    return _tag(lang, text) + ("" if re.search(r"[.!?…。！？؟]$", text) else ".")


def _sentence(text):
    text = _clean(text)
    return text if not text or re.search(r"[.!?…。！？؟]$", text) else text + "."


def _name(lang, item):
    """Ovozda bilim nomi: tilda — teglangan so'z, boshqa fanda — tushuncha nomi."""
    return _tag(lang, _clean(item["say"])) if lang else _clean(item["say"])


def _key(text):
    return re.sub(r"[^\w\s]", "", _clean(text).lower()).strip()


def _split_picture(text):
    """«🙏 Thank you!» → («🙏 », «Thank you!»): birinchi harfgacha — rasm (emoji)."""
    text = _clean(text)
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i], text[i:]
    return text, ""


def _word(item):
    """Test varianti uchun: tilda — so'zning o'zi, boshqa fanda — o'zbekcha nomi."""
    return _clean(item.get("say") or item.get("uz"))


def validate(cur):
    errors = []
    age = cur.get("age")
    if age not in MAX_OPTIONS:
        errors.append(f"age noto'g'ri: {age}")
    lang = cur.get("lang")
    if lang not in (None,) + LANGS:
        errors.append(f"lang faqat {', '.join(LANGS)} yoki null")
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
    for ui, unit in enumerate(units, 1):
        for sc in unit.get("scenarios") or []:
            where = f"{ui}-bo'lim vaziyati «{sc.get('name')}»"
            key = _clean(sc.get("name")).lower()
            if not key or key in names:
                errors.append(f"{where}: nom yo'q yoki takrorlangan")
            names.add(key)
            roles = sc.get("roles") or []
            if len(roles) < 2 or len(sc.get("roles_en") or roles) != len(roles):
                errors.append(f"{where}: roles/roles_en noto'g'ri")
            dialog = sc.get("dialog") or []
            if len(dialog) < 3:
                errors.append(f"{where}: dialog kamida 3 qator")
            for d in dialog:
                if not d.get("say") or not d.get("uz") or not isinstance(d.get("who"), int) or not 0 <= d["who"] < len(roles):
                    errors.append(f"{where}: dialog qatori noto'g'ri — {d}")
            for q in sc.get("questions") or []:
                opts = q.get("options") or []
                if not 2 <= len(opts) <= max(2, MAX_OPTIONS.get(age, 4)) or not isinstance(q.get("answer"), int) or not 0 <= q["answer"] < len(opts):
                    errors.append(f"{where}: savol noto'g'ri — {q.get('q', '')[:40]}")
    if errors:
        raise BookError("\n".join(errors[:40]))


IMMERSION = {"2-3 yosh": 1, "3-4 yosh": 1, "4-5 yosh": 2, "5-6 yosh": 3, "6-7 yosh": 4}
# Sinf tili (classroom language) — immersiya pog'onalarida ishlatiladi. Boshqa tillar keyin qo'shiladi.
CLASS = {
    "en": {
        "look": "Look!", "listen": "Listen and repeat:", "again": "Again!", "good": ["Good job!", "Well done!", "Great!", "Super!", "Excellent!"],
        "remember": "Do you remember?", "together": "Say it together!", "your_turn": "Your turn!", "game": "Game time!",
        "ready": "Ready? Go!", "found": "Great job! You found them all!", "today": "Today we learned:", "bye": "See you tomorrow!",
        "which": "Which one is: {w}?", "find": "Find the picture: {w}", "where": "Where is it: {w}?",
        "what": "Look at the picture. What is it?", "yes": "Yes! {w}", "old": "🔁 Old question", "play": "Let's play!",
        "roleplay": "Let's act it out!", "says": "{r} says:", "now_you": "Now you say it:",
        "hello_friends": "Hello, friends!", "listen_short": "Listen:", "listen_bang": "Listen!", "repeat_me": "Repeat after me:",
        "now_you_short": "Now you:", "say": "Say:", "one_more": "One more time:", "look_listen": "Look and listen:",
        "point_game": "I say it, you point to the picture: {names}.", "t_point": "🎲 Point to it!", "t_today": "🌟 Today we learned",
        "t_remember": "Remember:", "t_last_year": "Last year", "welcome_back": "Hello, friends! Welcome back! Let's remember the words we learned last year.",
        "t_review": "review", "review_intro": "Review day! Let's remember everything from this unit. Every right answer is a star!",
        "say_with_me": "Say it with me!", "t_jump": "Jump or sit!", "jump": "I say a word. If you see the picture — jump! If not — sit down! Ready? Go!",
        "played_great": "Well done! You played great!", "t_review_q": "Review question", "t_unit_done": "Unit complete!",
        "unit_done": "Fantastic! You finished this unit. Let's start a new adventure!", "t_party": "Big party!", "party": "Big party",
        "party_intro": "Hooray! It's a big party today! You finished the whole book. Let's remember our favourite words and win stars!",
        "know_all": "You know them all!", "t_party_q": "Party question", "t_champion": "You are a champion!",
        "champion": "You are a champion! Now you know it all. Open any lesson again and play!", "t_roleplay": "Role play",
        "roles_line": "I am the {a}, you are the {b}.", "change_roles": "Now we change roles!", "great_role": "You are a great {r}!",
        "t_well_done": "🌟 Well done!", "scenario_done": "Now you can do it: {name}! Play it again at home with your family.",
    },
}


class Builder:
    def __init__(self, cur, previous=None):
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
        self.previous = previous
        self.base_level = int(cur.get("immersion") or IMMERSION.get(self.age, 1)) if self.lang else 0
        self.level = self.base_level
        # Sinf tili iboralari: kitobning o'z tarjimasi (cur["class"]) → til lug'ati → ingliz tili.
        self.C = {**CLASS["en"], **CLASS.get(self.lang or "", {}), **(cur.get("class") or {})}
        self.images = {}        # say → rasm (dialog qatorlari mavjud so'z rasmini qayta ishlatadi)
        self.says, self.uzs = set(), set()   # test variantining tilini aniqlash uchun (tinglash testi)
        for unit in cur.get("units") or []:
            for les in (unit.get("lessons") or []) + (unit.get("scenarios") or []):
                for it in (les.get("items") or []) + (les.get("dialog") or []):
                    self.says.add(_key(it.get("say")))
                    self.uzs.add(_key(it.get("uz")))
        for unit in cur.get("units") or []:
            for les in unit.get("lessons") or []:
                for it in les.get("items") or []:
                    if it.get("image"):
                        self.images.setdefault(_clean(it["say"]).lower(), it["image"])

    # ── yordamchilar ──
    def t(self, text):
        return _clean(text)

    def E(self, text):
        """Tildagi matn (ovoz shu tilda o'qiladi)."""
        return _tag(self.lang, _clean(text)) if text else ""

    def good(self):
        return self.rng.choice(self.C["good"])

    def mix(self, uz, en):
        """Pog'onaga qarab: 1 — o'zbekcha, 2 — o'zbekcha + qisqa inglizcha, 3–4 — inglizcha."""
        if self.level <= 1 or not en:
            return self.t(uz)
        if self.level == 2:
            return self.t(f"{uz} {self.E(en)}")
        return self.E(en)

    @staticmethod
    def bare(text):
        return re.sub(r"[.!?…。！？؟]+$", "", _clean(text))

    # ── matnlar ──
    def item_voice(self, it, n):
        w = _tagp(self.lang, it["say"])
        act = f" {it['action']}" if it.get("action") else ""
        if not self.lang:
            return self.t(it["explain"] + act)
        C = self.C
        say = _sentence(it["say"])
        sent = _sentence(it.get("sentence") or "")
        act_en = _sentence(it.get("action_en") or "")
        if self.level >= 4:
            forms = [f"{C['look']} {say} {sent} {C['your_turn']} {C['say']} {say} {C['one_more']} {say} {act_en}",
                     f"{C['listen_short']} {say} {sent} {C['now_you_short']} {say} {C['again']} {say} {act_en}",
                     f"{C['look_listen']} {say} {sent} {C['repeat_me']} {say} {act_en} {self.good()}"]
            return self.E(forms[n % len(forms)])
        if self.level == 3:
            forms = [f"{C['look']} {say} {sent} {C['listen']} {say} {C['again']} {say} {act_en}",
                     f"{C['listen_short']} {say} {sent} {C['repeat_me']} {say} {act_en} {self.good()}"]
            return self.t(f"{self.E(forms[n % len(forms)])} O'zbekcha — {it['uz']}.{act if not act_en else ''}")
        if self.level == 2:
            forms = [f"{self.E(C['look'])} Qara, bu — {w} O'zbekcha — {it['uz']}. {self.E(C['listen'])} {w} {self.E(C['again'])} {w}{act} {self.E(self.good())}",
                     f"Yangi so'z: {w} Bu — {it['uz']} degani. {self.E(C['your_turn'])} Baland ovozda ayt: {w} {self.E(C['again'])} {w}{act}",
                     f"{self.E(C['listen_bang'])} {w} Bu — {it['uz']}. {self.E(C['repeat_me'])} {w}{act} {self.E(self.good())}"]
            return self.t(forms[n % len(forms)])
        if it.get("explain"):
            return self.t(f"{it['explain']} Men bilan takrorla: {w} Yana bir marta: {w}{act}")
        patterns = [
            f"Qara, bu — {w} O'zbekcha — {it['uz']}. Men bilan ayt: {w} Yana bir marta: {w}{act} Barakalla!",
            f"Yangi so'z: {w} Bu — {it['uz']} degani. Qani, baland ovozda ayt: {w} Endi shivirlab: {w}{act} Zo'r!",
            f"Qulog'ingni ding qil: {w} Bu — {it['uz']}. Men aytaman, sen qaytar: {w} Yana: {w}{act} Ofarin!",
        ]
        return self.t(patterns[n % len(patterns)])

    def item_simple(self, it):
        w = _tagp(self.lang, it["say"])
        if not self.lang:
            return self.t(f"Keling, sekinroq: {it['emoji']} bu — {it['uz'] or it['say']}. {it['explain'].split('.')[0]}.")
        if self.level >= 3:
            ex = f" Misol: {self.E(it['sentence'])}" if it.get("sentence") else ""
            return self.t(f"O'zbekcha tushuntiraman: {it['emoji']} {w} — bu «{it['uz']}» degani.{ex} Sekin ayt: {w}")
        return self.t(f"{it['uz'].capitalize()} — {w} Sekin ayt: {w}")

    def item_other(self, it):
        w = _tagp(self.lang, it["say"])
        if not self.lang:
            return self.t(f"Atrofingga qara: {it['uz'] or it['say']} qayerda bor? Barmog'ing bilan ko'rsat va ayt!")
        return self.t(f"Qani, o'yin! Men {it['uz']} desam, sen {w} deysan. {it['uz'].capitalize()}! … {w} Barakalla!")

    def board(self, it):
        show_uz = self.lang and it.get("uz") and self.level <= 3
        rom = f"\n{it['rom']}" if it.get("rom") else ""   # lotin yozuvida o'qilishi (arab, xitoy, yapon, koreys, rus)
        return f"{it['emoji']} {it['say']}{rom}" + (f"\n{it['uz']}" if show_uz else "")

    # ── testlar ──
    def q_pick(self, it):
        if self.lang and self.level >= 3:
            single = " " not in self.bare(it["say"])
            form = self.rng.choice([self.C["which"], self.C["find"]] + ([self.C["where"]] if single else []))
            return self.E(form.format(w=self.bare(it["say"])))
        w = _tag(self.lang, it["say"]) if self.lang else it.get("uz") or it["say"]
        forms = [f"Qaysi rasm {w}?", f"Qani, toping: {w} qayerda?", f"{w} — qaysi biri?"]
        return self.rng.choice(forms)

    def make_test(self, question, correct, distractors, why, kind="auto"):
        opts = [correct] + distractors[: self.n_opts - 1]
        if len(opts) < 2:
            return None
        self.rng.shuffle(opts)
        letters = "ABCD"
        return {"turi": "test", "sarlavha": self.C["play"] if self.lang and self.level >= 3 else "O'ynaymiz!", "matn": self.t(question),
                "variantlar": "\n".join(f"{letters[i]}) {o}" for i, o in enumerate(opts)),
                "javob": letters[opts.index(correct)], "yechim": self.t(why), "_kind": kind}

    def auto_test(self, it):
        others = [x for x in self.pool if x is not it and x["emoji"] != it["emoji"] and _word(x) != _word(it)]
        self.rng.shuffle(others)
        # yaqinlari (shu bo'limdan) avval — bola farqlashni o'rgansin
        same = [x for x in others if x.get("_unit") == it.get("_unit")]
        pool = same + [x for x in others if x not in same]
        distract = [self.opt(x["emoji"], _word(x)) for x in pool[:3]]
        w = _tag(self.lang, it["say"]) if self.lang else it["say"]
        if self.lang and self.level >= 4:
            why = self.E(self.C["yes"].format(w=_sentence(it["say"])))
        elif self.lang and self.level == 3:
            why = f"{self.E(self.C['yes'].format(w=_sentence(it['say'])))} — {it['uz']}."
        elif self.lang:
            why = f"{self.rng.choice(PRAISE)} {it['emoji']} {w} — {it['uz']}."
        else:
            why = f"{self.rng.choice(PRAISE)} Bu — {it['uz'] or it['say']}."
        return self.make_test(self.q_pick(it), self.opt(it["emoji"], _word(it)), distract, why)

    def opt(self, emoji, word, foreign=True):
        """Test varianti. Til kitobida so'z teglanadi — bola uni ekranda o'qimaydi, ESHITADI (🔊)."""
        word = _clean(word)
        return f"{emoji} {self.E(word)}".strip() if foreign and self.lang else f"{emoji} {word}".strip()

    def tag_option(self, text):
        """Muallif varianti: «🙏 Thank you!» → «🙏 [en]Thank you![/en]»; o'zbekcha variant o'zgarmaydi."""
        if not self.lang or "[" in str(text):
            return text
        pic, word = _split_picture(text)
        key = _key(word)
        if not key:
            return text
        foreign = key in self.says or (key not in self.uzs and not re.search(r"[oOgG][ʻ'‘’]", word))
        return f"{pic}{self.E(word)}".strip() if foreign else text

    def author_test(self, t):
        opts = [self.tag_option(o) for o in t["options"]]
        correct = opts[t["answer"]]
        others = [o for i, o in enumerate(opts) if i != t["answer"]]
        q = t["q"]
        why = t.get("why") or self.rng.choice(PRAISE)
        if self.lang and self.level >= 3 and t.get("q_en"):
            plain_uz = re.sub(r"\[/?[a-z]{2}\]", "", t["q"])
            q = self.E(t["q_en"]) if self.level >= 4 else f"{self.E(t['q_en'])} ({plain_uz})"
            if t.get("why_en"):
                why = self.E(t["why_en"])
            elif self.level >= 4:
                answer = re.sub(r"^[^A-Za-z]+", "", _clean(correct))
                if answer and re.fullmatch(r"[A-Za-z0-9 ,.'!?’-]+", answer):
                    why = self.E(self.C["yes"].format(w=_sentence(answer)))
        return self.make_test(q, correct, others, why, kind="author")

    def reverse_test(self, it):
        """5–6 yosh: so'zni eshitib, o'zbekcha ma'nosini topish. 6–7 yosh: rasmni ko'rib, so'zni topish (to'liq inglizcha)."""
        if self.level >= 4:
            others = [x for x in self.pool if x is not it and _word(x) != _word(it)]
            self.rng.shuffle(others)
            return self.make_test(self.E(f"{self.C['what']}") + f" {it['emoji']}", self.E(_word(it)), [self.E(_word(x)) for x in others[:3]],
                                  self.E(self.C["yes"].format(w=_sentence(it["say"]))))
        others = [x for x in self.pool if x is not it and x.get("uz") and x["uz"] != it["uz"]]
        self.rng.shuffle(others)
        return self.make_test(f"{_tag(self.lang, it['say'])} — o'zbekchasi nima?", f"{it['emoji']} {it['uz']}",
                              [f"{x['emoji']} {x['uz']}" for x in others[:3]], f"To'g'ri! {_tag(self.lang, it['say'])} — {it['uz']}.")

    def old_title(self):
        return self.C["old"] if self.lang and self.level >= 3 else "🔁 Eski savol"

    # ── darslar ──
    def review_rows(self, index):
        rows = []
        for back in (1, 3):
            if index - back >= 0 and self.lesson_items[index - back]:
                it = self.rng.choice(self.lesson_items[index - back])
                if self.lang and self.level >= 3:
                    sent = f" {_sentence(it['sentence'])}" if it.get("sentence") else ""
                    text = self.E(f"{self.C['remember']} {it['emoji']} {_sentence(it['say'])}{sent} {self.C['together']}")
                    if self.level == 3:
                        text += f" ({it['uz']})"
                    title = f"🔁 {self.C['t_remember']} {it['emoji']} {it['say']}"
                elif self.lang:
                    pre = f"{self.E(self.C['remember'])} " if self.level == 2 else "Esingdami? "
                    text = f"{pre}{it['emoji']} Bu — {_tag(self.lang, it['say'])}, ya'ni {_sentence(it['uz'])} Qani, birga aytamiz!"
                    title = f"🔁 Eslaymiz: {it['emoji']} {it['say']}"
                else:
                    uz = _clean(it.get("uz"))
                    text = f"Esingdami? {it['emoji']} {_sentence(it['say'])} {_sentence(uz[:1].upper() + uz[1:])} Qani, birga aytamiz!"
                    title = f"🔁 Eslaymiz: {it['emoji']} {it['say']}"
                rows.append({"turi": "tushuncha", "sarlavha": title, "matn": self.t(text), "rasm": it.get("image", ""),
                             "doska": self.board(it), "sodda": self.item_simple(it), "boshqa_usul": self.item_other(it)})
        return rows

    def intro_text(self, lesson, default_uz):
        if self.lang and self.level >= 3 and lesson.get("intro_en"):
            return self.E(lesson["intro_en"])
        if self.lang and self.level == 2 and lesson.get("intro"):
            return self.t(f"{self.E(self.C['hello_friends'])} {lesson['intro']}")
        return self.t(lesson.get("intro") or default_uz)

    def game_row(self, game_items):
        if self.lang and self.level >= 3:
            names = ", ".join(self.bare(x["say"]) for x in game_items)
            return {"turi": "topshiriq", "sarlavha": self.C["t_point"],
                    "matn": self.E(f"{self.C['game']} {self.C['point_game'].format(names=names)} {self.C['ready']}"),
                    "doska": "  ".join(x["emoji"] for x in game_items), "yechim": self.E(self.C["found"]) + " 🌟"}
        names = ", ".join(_name(self.lang, x) for x in game_items)
        pre = f"{self.E(self.C['game'])} " if self.lang and self.level == 2 else "O'yin vaqti! "
        return {"turi": "topshiriq", "sarlavha": "🎲 Top-chi o'yini",
                "matn": self.t(f"{pre}Men aytaman, sen rasmni barmog'ing bilan bos: {names}. Topsang — qarsak chal!"),
                "doska": "  ".join(x["emoji"] for x in game_items), "yechim": "Barakalla! Hammasini topding! 🌟"}

    def summary_row(self, items):
        if self.lang and self.level >= 3:
            names = ", ".join(self.bare(x["say"]) for x in items)
            text = self.E(f"{self.good()} {self.C['today']} {names}. {self.C['bye']}")
            if self.level == 3:
                text += " Barakalla!"
            return {"turi": "xulosa", "sarlavha": self.C["t_today"], "matn": self.t(text),
                    "doska": "  ".join(f"{x['emoji']} {x['say']}" for x in items)}
        pre = f"{self.E(self.good())} " if self.lang and self.level == 2 else f"{self.rng.choice(PRAISE)} "
        return {"turi": "xulosa", "sarlavha": "🌟 Bugun o'rgandik",
                "matn": self.t(f"{pre}Bugun biz " + ", ".join(_name(self.lang, x) for x in items) + " ni o'rgandik. Ertaga yana uchrashamiz — yangi sir bor!"),
                "doska": "  ".join(f"{x['emoji']} {x['say']}" for x in items)}

    def spiral_tests(self, index, new_tests):
        want_new = 3 if self.age in ("2-3 yosh", "3-4 yosh", "4-5 yosh") else 4
        tests = new_tests[:want_new]
        for back in (1, 3, 7):
            if index - back >= 0 and self.lesson_tests[index - back]:
                old = dict(self.rng.choice(self.lesson_tests[index - back]))
                old["sarlavha"] = self.old_title()
                tests.append(old)
        return tests

    def lesson(self, unit_no, unit, lesson):
        index = len(self.lesson_items)
        items = [dict(it, _unit=unit_no) for it in lesson["items"]]
        rows = [{"turi": "kirish", "sarlavha": f"{unit.get('emoji', '🕊️')} {lesson['name']}",
                 "matn": self.intro_text(lesson, f"Salom, do'stim! Men — robot Kabu. Bip-bip! Bugun «{lesson['name']}» mavzusini o'rganamiz."),
                 "doska": f"🕊️ {lesson['name']}", "rasm": lesson.get("image_scene", "")}]
        rows += self.review_rows(index)
        for n, it in enumerate(items):
            show_uz = self.lang and it.get("uz") and self.level <= 3
            rows.append({"turi": "tushuncha", "sarlavha": f"{it['emoji']} {it['say']}" + (f" — {it['uz']}" if show_uz else ""),
                         "matn": self.item_voice(it, n + index), "doska": self.board(it), "rasm": it.get("image", ""),
                         "sodda": self.item_simple(it), "boshqa_usul": self.item_other(it)})
        for row in lesson.get("extra") or []:
            out = {k: row.get(k, "") for k in ("turi", "sarlavha", "matn", "doska", "sodda", "boshqa_usul", "rasm")}
            if self.lang and self.level >= 3 and row.get("matn_en"):
                # Inglizcha variant — asosiy ovoz; o'zbekchasi «Tushunmadim» tugmasiga o'tadi.
                out["sodda"] = out["sodda"] or out["matn"]
                out["matn"] = self.E(row["matn_en"])
                out["sarlavha"] = row.get("sarlavha_en") or out["sarlavha"]
            rows.append(out)
        # O'yin: yangi so'zlar + bitta eski — «top-chi»
        game_items = items + ([self.rng.choice(self.pool)] if self.pool else [])
        rows.append(self.game_row(game_items))
        self.pool.extend(items)
        self.lesson_items.append(items)
        # Testlar: yangi (muallif + avto) va eski takror
        new_tests = [self.author_test(t) for t in lesson.get("tests") or []]
        if self.lang or not new_tests:
            new_tests += [self.auto_test(it) for it in items]
        if self.lang and self.age in ("5-6 yosh", "6-7 yosh") and items:
            new_tests.append(self.reverse_test(self.rng.choice(items)))
        new_tests = [t for t in new_tests if t]
        tests = self.spiral_tests(index, new_tests)
        self.lesson_tests.append(new_tests)
        rows += [{k: v for k, v in t.items() if not k.startswith("_")} for t in tests]
        rows.append(self.summary_row(items))
        self.topics.append(self.topic(lesson["name"], lesson.get("goal", ""), rows, items))

    # ── hayotiy vaziyat (dialog, rol o'yini) ──
    def scenario(self, unit_no, unit, sc):
        index = len(self.lesson_items)
        roles, roles_en = sc.get("roles") or ["", ""], sc.get("roles_en") or sc.get("roles") or ["", ""]
        lines = []
        for d in sc["dialog"]:
            key = _clean(d["say"]).lower()
            lines.append(dict(d, _unit=unit_no, image=d.get("image") or self.images.get(key, "")))
        scene = sc.get("scene") or {}
        title_place = sc.get("name_en") if self.level >= 3 else sc["name"]
        rows = [{"turi": "kirish", "sarlavha": f"🎭 {title_place}", "rasm": scene.get("image", ""),
                 "matn": self.intro_text({"intro": sc.get("intro"), "intro_en": sc.get("intro_en")},
                                         f"Bip-bip! Bugun hayotiy vaziyat: {sc['name']}. Qani, tinglaymiz va o'ynaymiz!"),
                 "doska": f"{sc.get('emoji', '🎭')} {sc.get('name_en') or sc['name']}"}]
        for n, d in enumerate(lines):
            role, role_en = roles[d["who"]], roles_en[d["who"]]
            say = _sentence(d["say"])
            if self.level >= 4:
                voice = self.E(f"{self.C['says'].format(r=role_en)} {say} {self.C['now_you']} {say}")
            elif self.level == 3:
                voice = f"{self.E(self.C['says'].format(r=role_en) + ' ' + say + ' ' + self.C['listen'] + ' ' + say)} ({d['uz']})"
            else:
                voice = f"{role} aytadi: {_tagp(self.lang, d['say'])} Bu — «{d['uz']}» degani. Takrorlang: {_tagp(self.lang, d['say'])}"
            rows.append({"turi": "tushuncha", "sarlavha": f"{d.get('emoji', '💬')} {role_en if self.level >= 3 else role}: {d['say']}",
                         "matn": self.t(voice), "rasm": d.get("image", ""),
                         "doska": f"{d.get('emoji', '')} {d['say']}" + (f"\n{d['rom']}" if d.get("rom") else "") + (f"\n{d['uz']}" if self.level <= 3 else ""),
                         "sodda": self.t(f"{role} aytadi: {_tagp(self.lang, d['say'])} O'zbekcha: {d['uz']}."),
                         "boshqa_usul": self.t(f"Oyna oldida {role.lower()} bo'lib ayt: {_tagp(self.lang, d['say'])}")})
        script = "\n".join(f"— {roles_en[d['who']] if self.level >= 3 else roles[d['who']]}: {d['say']}" for d in lines)
        me = roles_en[-1] if self.level >= 3 else roles[-1]
        if self.level >= 3:
            play = self.E(f"{self.C['roleplay']} {self.C['roles_line'].format(a=roles_en[0].lower(), b=roles_en[-1].lower())} " + " ".join(_sentence(d["say"]) for d in lines)
                          + f" {self.C['change_roles']}")
        else:
            play = self.t(f"Keling, rol o'ynaymiz! Men — {roles[0].lower()}, sen — {roles[-1].lower()}. "
                          + " ".join(_tagp(self.lang, d["say"]) for d in lines) + " Endi rollarni almashamiz!")
        rows.append({"turi": "topshiriq", "sarlavha": "🎭 " + (self.C["t_roleplay"] if self.level >= 3 else "Rol o'ynaymiz"),
                     "matn": play, "doska": script,
                     "yechim": self.E(f"{self.good()} {self.C['great_role'].format(r=me.lower())}") if self.level >= 3 else "Ofarin! Sen zo'r o'ynading! 🌟"})
        new_tests = [self.author_test(q | {"q": q["q"], "q_en": q.get("q_en"), "why_en": q.get("why_en")}) for q in sc.get("questions") or []]
        new_tests = [t for t in new_tests if t]
        tests = self.spiral_tests(index, new_tests)
        rows += [{k: v for k, v in t.items() if not k.startswith("_")} for t in tests]
        if self.level >= 3:
            rows.append({"turi": "xulosa", "sarlavha": self.C["t_well_done"],
                         "matn": self.E(f"{self.good()} {self.C['scenario_done'].format(name=self.bare(sc.get('name_en') or ''))} {self.C['bye']}"),
                         "doska": f"{sc.get('emoji', '🎭')} {sc.get('name_en') or sc['name']} ✅"})
        else:
            pre = f"{self.E(self.good())} " if self.level == 2 else f"{self.rng.choice(PRAISE)} "
            rows.append({"turi": "xulosa", "sarlavha": "🌟 Bugun o'ynadik",
                         "matn": self.t(f"{pre}Bugun «{sc['name']}» vaziyatini o'ynadik. Endi buni hayotda ham ayta olasan! Uyda oilang bilan yana o'yna."),
                         "doska": f"{sc.get('emoji', '🎭')} {sc['name']} ✅"})
        self.pool.extend(lines)
        self.lesson_items.append(lines)
        self.lesson_tests.append(new_tests)
        topic = self.topic(sc["name"], sc.get("goal", ""), rows, lines)
        topic["image_scene"] = scene.get("image")
        topic["image_scene_prompt"] = scene.get("image_prompt")
        self.topics.append(topic)

    def previous_year(self):
        """Kitob boshida: o'tgan yilgi kitobdan eng muhim so'zlarni eslash (yoshlar orasidagi spiral)."""
        prev = self.previous
        items = [dict(it, _unit=0) for u in prev["units"] for les in u["lessons"] for it in les["items"]]
        rng = random.Random(f"prev|{self.age}")
        rng.shuffle(items)
        items = items[:8]
        if not items:
            return
        rows = [{"turi": "kirish", "sarlavha": "🔁 " + (self.C["t_last_year"] if self.level >= 3 else "O'tgan yilni eslaymiz"),
                 "matn": self.mix("Bip-bip! Salom, do'stim! Yangi kitobni boshlashdan oldin o'tgan yili o'rgangan so'zlarimizni eslaymiz.",
                                  self.C["welcome_back"]),
                 "doska": "🔁 " + "  ".join(x["emoji"] for x in items)}]
        for i in range(0, len(items), 2):
            chunk = items[i:i + 2]
            if self.level >= 3:
                voice = self.E(" ".join(f"{self.C['remember']} {_sentence(x['say'])}" for x in chunk) + f" {self.C['together']}")
            else:
                voice = self.t(" ".join(f"{x['emoji']} {_tagp(self.lang, x['say'])} — {_sentence(x['uz'])}" for x in chunk) + " Qani, birga aytamiz!")
            rows.append({"turi": "tushuncha", "sarlavha": "🔁 " + " ".join(f"{x['emoji']} {x['say']}" for x in chunk),
                         "matn": voice, "rasm": chunk[0].get("image", ""), "doska": "\n".join(self.board(x) for x in chunk),
                         "sodda": self.t("O'zbekcha: " + "; ".join(f"{_tag(self.lang, x['say'])} — {x['uz']}" for x in chunk)),
                         "boshqa_usul": self.item_other(chunk[0])})
        self.pool.extend(items)
        tests = [t for t in (self.auto_test(it) for it in items[:5]) if t]
        rows += [{k: v for k, v in t.items() if not k.startswith("_")} for t in tests]
        rows.append(self.summary_row(items[:5]))
        self.lesson_items.append(items)
        self.lesson_tests.append(tests)
        self.topics.append(self.topic("O'tgan yilni eslaymiz", "O'tgan yilgi kitobdagi asosiy so'zlarni takrorlash", rows, items))

    def unit_review(self, unit_no, unit, start):
        items = [it for its in self.lesson_items[start:] for it in its]
        if not items:
            return
        en = self.lang and self.level >= 3
        rows = [{"turi": "kirish", "sarlavha": f"🔁 {unit['name']}: " + (self.C["t_review"] if en else "takrorlaymiz"),
                 "matn": self.mix(f"Bip-bip! Bugun katta takrorlash kuni! «{unit['name']}» bo'limida o'rgangan hamma narsani eslaymiz. Har to'g'ri javob — bitta yulduzcha!",
                                  self.C["review_intro"]),
                 "doska": "🔁 " + "  ".join(x["emoji"] for x in items[:12])}]
        for i in range(0, len(items), 3):
            chunk = items[i:i + 3]
            if en:
                voice = self.E(" ".join(f"{_sentence(x['say'])}" for x in chunk) + f" {self.C['say_with_me']}")
                if self.level == 3:
                    voice += " (" + "; ".join(x.get("uz", "") for x in chunk) + ")"
            else:
                voice = self.t(" ".join(f"{x['emoji']} {_name(self.lang, x)} — {_sentence(x.get('uz'))}" for x in chunk) + " Men bilan birga takrorla!")
            plain = " ".join(f"{x['emoji']} {_name(self.lang, x)} — {_sentence(x.get('uz'))}" for x in chunk)
            rows.append({"turi": "tushuncha", "sarlavha": (f"{self.C['t_remember']} " if en else "Eslaymiz: ") + " ".join(x["emoji"] for x in chunk),
                         "matn": voice, "rasm": chunk[0].get("image", ""),
                         "doska": "\n".join(self.board(x).replace("\n", " — ") for x in chunk),
                         "sodda": self.t("Sekin-sekin: " + plain), "boshqa_usul": self.t("Har birini ko'rsatib, qarsak chalib ayt: " + plain)})
        rows.append({"turi": "topshiriq", "sarlavha": "🏃 " + (self.C["t_jump"] if en else "Harakatli o'yin"),
                     "matn": self.mix("Men so'z aytaman: rasm ekranda bo'lsa — sakra, bo'lmasa — o'tir! Tayyormisan? Boshladik!",
                                      self.C["jump"]),
                     "doska": "  ".join(x["emoji"] for x in items[:12]), "yechim": self.E(self.C["played_great"]) + " 🌟" if en else "Ofarin! Sen zo'r o'ynading! 🌟"})
        pool_tests = [t for ts in self.lesson_tests[start:] for t in ts]
        self.rng.shuffle(pool_tests)
        count = 5 if self.age in ("2-3 yosh", "3-4 yosh", "4-5 yosh") else 7
        rows += [dict({k: v for k, v in t.items() if not k.startswith("_")}, sarlavha="⭐ " + (self.C["t_review_q"] if en else "Takror savoli")) for t in pool_tests[:count]]
        rows.append({"turi": "xulosa", "sarlavha": "🏅 " + (self.C["t_unit_done"] if en else "Bo'lim tugadi!"),
                     "matn": self.mix(f"Qoyil! «{unit['name']}» bo'limini tugatding. Endi yangi sarguzashtga o'tamiz!",
                                      self.C["unit_done"]),
                     "doska": f"🏅 {unit['name']}"})
        self.topics.append(self.topic(f"{unit_no}-bo'lim takrori: {unit['name']}", f"«{unit['name']}» bo'limini mustahkamlash", rows, items[:6]))

    def final_review(self):
        en = self.lang and self.level >= 3
        rows = [{"turi": "kirish", "sarlavha": "🎉 " + (self.C["t_party"] if en else "Katta bayram!"),
                 "matn": self.mix("Bip-bip! Bugun katta bayram! Butun kitobni tugatding. Keling, eng qiziq so'zlarni eslaymiz va o'yinda yulduzcha yig'amiz!",
                                  self.C["party_intro"]),
                 "doska": "🎉 " + (self.C["party"] if en else "Katta bayram")}]
        sample = self.pool[:]
        self.rng.shuffle(sample)
        for i in range(0, min(len(sample), 16), 4):
            chunk = sample[i:i + 4]
            voice = self.E(" ".join(_sentence(x["say"]) for x in chunk) + f" {self.C['know_all']}") if en else \
                self.t(" ".join(f"{x['emoji']} {_sentence(_name(self.lang, x))}" for x in chunk) + " Ajoyib, hammasini bilasan!")
            rows.append({"turi": "tushuncha", "sarlavha": (f"{self.C['t_remember']} " if en else "Eslaymiz: ") + " ".join(x["emoji"] for x in chunk),
                         "matn": voice, "rasm": chunk[0].get("image", ""), "doska": "\n".join(self.board(x).replace("\n", " — ") for x in chunk)})
        all_tests = [t for ts in self.lesson_tests for t in ts]
        self.rng.shuffle(all_tests)
        rows += [dict({k: v for k, v in t.items() if not k.startswith("_")}, sarlavha="🎉 " + (self.C["t_party_q"] if en else "Bayram savoli")) for t in all_tests[:12]]
        rows.append({"turi": "xulosa", "sarlavha": "🏆 " + (self.C["t_champion"] if en else "Sen chempionsan!"),
                     "matn": self.mix("Sen chempionsan! Endi hammasini bilasan. Istalgan darsni qayta ochib, yana o'ynashing mumkin.",
                                      self.C["champion"]),
                     "doska": "🏆"})
        self.topics.append(self.topic("Katta bayram: hammasini takrorlaymiz", "Butun kitobni mustahkamlash", rows, sample[:6]))

    def topic(self, name, goal, rows, items):
        return {"no": len(self.topics) + 1, "name": name, "goal": goal, "rows": rows,
                "words": [{k: it.get(k, "") for k in ("say", "uz", "emoji", "image", "image_prompt")} | {"en": it["say"]} for it in items]}

    def build(self):
        if self.previous and self.lang:
            self.level = max(1, self.base_level - 1)
            self.previous_year()
        for unit_no, unit in enumerate(self.cur["units"], 1):
            # birinchi bo'lim — o'tish davri: bir pog'ona yengilroq (bola asta-sekin inglizchaga o'tadi)
            self.level = max(1, self.base_level - 1) if unit_no == 1 and self.base_level >= 3 else self.base_level
            start = len(self.lesson_items)
            for lesson in unit["lessons"]:
                self.lesson(unit_no, unit, lesson)
            for sc in unit.get("scenarios") or []:
                self.scenario(unit_no, unit, sc)
            self.unit_review(unit_no, unit, start)
        self.level = self.base_level
        self.final_review()
        for topic in self.topics:
            for row in topic["rows"]:
                for key in ("matn", "sodda", "boshqa_usul", "yechim"):
                    if len(row.get(key) or "") > 1400:
                        row[key] = row[key][:1400]
        return {"age": self.age, "book_title": self.cur.get("book_title") or f"{self.cur['subject']} {self.age}",
                "subject": self.cur["subject"], "prefix": self.cur.get("prefix") or "BK", "topics": self.topics,
                "immersion": self.base_level}


def merge_enrich(cur, enrich):
    """Asosiy dastur + boyitish fayli (inglizcha misol gaplar, kirishlar, hayotiy vaziyatlar) → bitta dastur."""
    import copy
    cur = copy.deepcopy(cur)
    lessons = (enrich or {}).get("lessons") or {}
    for unit in cur["units"]:
        for les in unit["lessons"]:
            extra = lessons.get(les["name"]) or {}
            if extra.get("intro_en"):
                les["intro_en"] = extra["intro_en"]
            for it in les["items"]:
                it.update({k: v for k, v in ((extra.get("items") or {}).get(it["say"]) or {}).items() if v})
            for row, en in zip(les.get("extra") or [], extra.get("extras_en") or []):
                if en.get("matn_en"):
                    row["matn_en"], row["sarlavha_en"] = en["matn_en"], en.get("sarlavha_en") or row.get("sarlavha")
            for t, q in zip(les.get("tests") or [], extra.get("tests_en") or []):
                if q:
                    t["q_en"] = q
    for sc in (enrich or {}).get("scenarios") or []:
        unit = cur["units"][int(sc["unit"]) - 1]
        unit.setdefault("scenarios", []).append(sc)
    return cur


def build_book(cur, enrich=None, previous=None):
    if enrich:
        cur = merge_enrich(cur, enrich)
    validate(cur)
    return Builder(cur, previous=previous).build()


def stats(book):
    tests = sum(1 for t in book["topics"] for r in t["rows"] if r["turi"] == "test")
    words = sum(len(t["words"]) for t in book["topics"] if "takror" not in t["name"].lower() and "bayram" not in t["name"].lower())
    return {"darslar": len(book["topics"]), "testlar": tests, "yangi_bilim": words}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    book = build_book(json.loads(Path(src).read_text(encoding="utf-8")))
    Path(dst).write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats(book), ensure_ascii=False))

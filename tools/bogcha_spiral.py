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


# ── REV111: izoh tili — kursni qaysi tilda TUSHUNTIRISH (o'qitiladigan til o'zgarmaydi) ──
# cur["izoh"]: "uz" (asl, o'zgarmaydi) | "ru" | "en". Lug'at: bogcha_content/izoh/<izoh>.json → {"t": {sid: tarjima}}.
# Kalit — sid(o'zbekcha matn): dvigatel shablonlari (U) va kitob bo'laklari (UZ/TX) bitta "t" bo'limida.
IZOH_DIR = Path(__file__).resolve().parent / "bogcha_content" / "izoh"
IZOH_LANGS = ("uz", "ru", "en")
IZOH_DICTS = {}             # izoh → {sid: tarjima}; bir marta yuklanadi (selftest o'z lug'atini shu yerga qo'yadi)
IZOH_ALLOW_MISSING = False  # True — lug'atda yo'q matn o'zbekcha qoladi (extract / qoralama yig'ish uchun)
IZOH_RECORDER = None        # callable(kind, text, ctx) — extract: ishlatilgan har shablon va bo'lak yoziladi
YECHIM_DEFAULT = "Barakalla! Juda yaxshi bajarding! 🌟"   # bogcha_kitob.ai_workbook dagi topshiriq yechimi
TAG_ANY = re.compile(r"(\[([a-z]{2})\].*?\[/\2\])", re.S)


def sid(text):
    import hashlib
    return "s" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


IZOH_UZ_SETS = None         # {"variant": [...], "doska": [...]} — manba.json «uz_aniq»: chet so'zidek ko'rinadigan, lekin
                            # boshqa til kitoblarida ham aynan bir xil (demak o'zbekcha) test variantlari va doska bo'laklari


def izoh_uz_sets():
    global IZOH_UZ_SETS
    if IZOH_UZ_SETS is None:
        path = IZOH_DIR / "manba.json"
        data = json.loads(path.read_text(encoding="utf-8")).get("uz_aniq") if path.is_file() else None
        IZOH_UZ_SETS = data or {}
    return IZOH_UZ_SETS


def izoh_dict(izoh):
    if izoh not in IZOH_DICTS:
        path = IZOH_DIR / f"{izoh}.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        IZOH_DICTS[izoh] = data.get("t") or {}
    return IZOH_DICTS[izoh]


def _has_letters(text):
    return any(ch.isalpha() for ch in str(text or ""))


def tagged_pieces(text):
    """Matn → [(tegmi, bo'lak)]: [xx]…[/xx] — o'qitiladigan til (tegmi=True), qolgani — izoh tili."""
    out, pos = [], 0
    for m in TAG_ANY.finditer(text):
        if m.start() > pos:
            out.append((False, text[pos:m.start()]))
        out.append((True, m.group(1)))
        pos = m.end()
    if pos < len(text):
        out.append((False, text[pos:]))
    return out


def _core(piece):
    """« Uni kutib ol: » → (« », «Uni kutib ol:», « ») — tarjima kaliti o'zak (chetdagi bo'shliqsiz)."""
    core = piece.strip()
    if not core:
        return piece, "", ""
    i = piece.index(core)
    return piece[:i], core, piece[i + len(core):]


def uz_chunks(text):
    """Teglardan tashqaridagi, harfi bor o'zbekcha bo'laklar (tarjima kalitlari)."""
    if not isinstance(text, str) or not text:
        return []
    return [_core(p)[1] for tag, p in tagged_pieces(text) if not tag and _has_letters(p)]


def doska_chunks(text):
    """Doska: har qatorda « — » dan o'ng tomoni o'zbekcha (chap tomoni — o'qitiladigan til)."""
    out = []
    for line in str(text or "").split("\n"):
        if " — " in line:
            out += uz_chunks(line.split(" — ", 1)[1])
    return out


TITLE_AGE = re.compile(r"^(.*?\S)\s+(\d[–-]\d yosh)$")


class Builder:
    def __init__(self, cur, previous=None):
        self.cur = cur
        self.lang = cur.get("lang")
        self.izoh = cur.get("izoh") or "uz"
        if self.izoh not in IZOH_LANGS:
            raise BookError(f"izoh faqat {', '.join(IZOH_LANGS)}: {self.izoh}")
        self.izoh_t = izoh_dict(self.izoh) if self.izoh != "uz" else {}
        sets = izoh_uz_sets() if self.izoh != "uz" else {}
        self.uz_variant, self.uz_doska = set(sets.get("variant") or ()), set(sets.get("doska") or ())
        self.where = ""         # extract uchun kontekst (hozirgi dars)
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

    # ── izoh tili ──
    def _record(self, kind, text, ctx=None):
        if IZOH_RECORDER:
            IZOH_RECORDER(kind, text, ctx or f"{self.lang} {self.age} | {self.where}")

    def _lookup(self, text):
        out = self.izoh_t.get(sid(text))
        if out is None:
            if IZOH_ALLOW_MISSING:
                return text
            raise KeyError(f"izoh={self.izoh}: tarjima yo'q {sid(text)} «{text[:80]}»")
        return out

    def U(self, uz_template, **kw):
        """Dvigatel shabloni (o'zbekcha) → izoh tilida, keyin .format(**kw)."""
        self._record("shablon", uz_template, "shablon: " + ", ".join("{%s}" % k for k in kw) if kw else "shablon")
        if self.izoh == "uz":
            return uz_template.format(**kw)
        return self._lookup(uz_template).format(**kw)

    def UZ(self, text, kind="uz"):
        """Kitobdagi butun o'zbekcha matn (ma'no, nom, rol) → izoh tilida."""
        if not isinstance(text, str) or not _has_letters(text):
            return text
        self._record(kind, text)
        return text if self.izoh == "uz" else self._lookup(text)

    def TX(self, text, kind="ovoz"):
        """Teglangan matn: [xx]…[/xx] o'zgarmaydi, oradagi o'zbekcha bo'laklar tarjima qilinadi."""
        if not isinstance(text, str) or not text:
            return text
        out = []
        for tag, piece in tagged_pieces(text):
            if tag or not _has_letters(piece):
                out.append(piece)
                continue
            lead, core, trail = _core(piece)
            self._record(kind, core, f"{self.lang} {self.age} | {self.where} | matn: {text[:160]}")
            out.append(lead + (core if self.izoh == "uz" else self._lookup(core)) + trail)
        return "".join(out)

    def DOSKA(self, text):
        """Muallif doskasi: qatordagi « — » dan o'ng tomoni o'zbekcha bo'lsa (manba «uz_aniq.doska») o'giriladi."""
        if self.izoh == "uz" or not isinstance(text, str) or " — " not in text:
            return text
        lines = []
        for line in text.split("\n"):
            if " — " in line:
                left, right = line.split(" — ", 1)
                if right in self.uz_doska:
                    line = f"{left} — {self.TX(right, 'doska')}"
            lines.append(line)
        return "\n".join(lines)

    def title(self):
        title = self.cur.get("book_title") or f"{self.cur['subject']} {self.age}"
        m = TITLE_AGE.match(title)
        return title[:m.start(2)] + self.UZ(m.group(2), "nom") if m else title

    def praise(self):
        return self.U(self.rng.choice(PRAISE))

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
        U = self.U
        w = _tagp(self.lang, it["say"])
        act = f" {self.UZ(it['action'], 'ovoz')}" if it.get("action") else ""
        if not self.lang:
            return self.t(self.UZ(it["explain"], "ovoz") + act)
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
            return self.t(U("{voice} O'zbekcha — {uz}.{act}", voice=self.E(forms[n % len(forms)]), uz=self.UZ(it["uz"]),
                            act=act if not act_en else ""))
        uz = self.UZ(it.get("uz"))
        if self.level == 2:
            forms = [U("{look} Qara, bu — {w} O'zbekcha — {uz}. {listen} {w} {again} {w}{act} {good}",
                       look=self.E(C["look"]), w=w, uz=uz, listen=self.E(C["listen"]), again=self.E(C["again"]), act=act,
                       good=self.E(self.good())),
                     U("Yangi so'z: {w} Bu — {uz} degani. {your_turn} Baland ovozda ayt: {w} {again} {w}{act}",
                       w=w, uz=uz, your_turn=self.E(C["your_turn"]), again=self.E(C["again"]), act=act),
                     U("{listen} {w} Bu — {uz}. {repeat} {w}{act} {good}",
                       listen=self.E(C["listen_bang"]), w=w, uz=uz, repeat=self.E(C["repeat_me"]), act=act,
                       good=self.E(self.good()))]
            return self.t(forms[n % len(forms)])
        if it.get("explain"):
            return self.t(U("{explain} Men bilan takrorla: {w} Yana bir marta: {w}{act}",
                            explain=self.UZ(it["explain"], "ovoz"), w=w, act=act))
        patterns = [
            U("Qara, bu — {w} O'zbekcha — {uz}. Men bilan ayt: {w} Yana bir marta: {w}{act} Barakalla!", w=w, uz=uz, act=act),
            U("Yangi so'z: {w} Bu — {uz} degani. Qani, baland ovozda ayt: {w} Endi shivirlab: {w}{act} Zo'r!", w=w, uz=uz, act=act),
            U("Qulog'ingni ding qil: {w} Bu — {uz}. Men aytaman, sen qaytar: {w} Yana: {w}{act} Ofarin!", w=w, uz=uz, act=act),
        ]
        return self.t(patterns[n % len(patterns)])

    def item_simple(self, it):
        w = _tagp(self.lang, it["say"])
        if not self.lang:
            return self.t(self.U("Keling, sekinroq: {emoji} bu — {uz}. {explain}.", emoji=it["emoji"],
                                 uz=self.UZ(it["uz"] or it["say"]), explain=self.UZ(it["explain"], "ovoz").split(".")[0]))
        if self.level >= 3:
            ex = " " + self.U("Misol: {sentence}", sentence=self.E(it["sentence"])) if it.get("sentence") else ""
            return self.t(self.U("O'zbekcha tushuntiraman: {emoji} {w} — bu «{uz}» degani.{ex} Sekin ayt: {w}",
                                 emoji=it["emoji"], w=w, uz=self.UZ(it["uz"]), ex=ex))
        return self.t(self.U("{uz} — {w} Sekin ayt: {w}", uz=self.UZ(it["uz"]).capitalize(), w=w))

    def item_other(self, it):
        w = _tagp(self.lang, it["say"])
        if not self.lang:
            return self.t(self.U("Atrofingga qara: {uz} qayerda bor? Barmog'ing bilan ko'rsat va ayt!",
                                 uz=self.UZ(it["uz"] or it["say"])))
        uz = self.UZ(it["uz"])
        return self.t(self.U("Qani, o'yin! Men {uz} desam, sen {w} deysan. {uz_cap}! … {w} Barakalla!",
                             uz=uz, w=w, uz_cap=uz.capitalize()))

    def board(self, it):
        show_uz = self.lang and it.get("uz") and self.level <= 3
        rom = f"\n{it['rom']}" if it.get("rom") else ""   # lotin yozuvida o'qilishi (arab, xitoy, yapon, koreys, rus)
        return f"{it['emoji']} {it['say']}{rom}" + (f"\n{self.UZ(it['uz'])}" if show_uz else "")

    # ── testlar ──
    def q_pick(self, it):
        if self.lang and self.level >= 3:
            single = " " not in self.bare(it["say"])
            form = self.rng.choice([self.C["which"], self.C["find"]] + ([self.C["where"]] if single else []))
            return self.E(form.format(w=self.bare(it["say"])))
        w = _tag(self.lang, it["say"]) if self.lang else self.UZ(it.get("uz") or it["say"])
        forms = [self.U("Qaysi rasm {w}?", w=w), self.U("Qani, toping: {w} qayerda?", w=w), self.U("{w} — qaysi biri?", w=w)]
        return self.rng.choice(forms)

    def make_test(self, question, correct, distractors, why, kind="auto"):
        opts = [correct] + distractors[: self.n_opts - 1]
        if len(opts) < 2:
            return None
        self.rng.shuffle(opts)
        letters = "ABCD"
        return {"turi": "test", "sarlavha": self.C["play"] if self.lang and self.level >= 3 else self.U("O'ynaymiz!"),
                "matn": self.t(question),
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
            why = f"{self.E(self.C['yes'].format(w=_sentence(it['say'])))} — {self.UZ(it['uz'])}."
        elif self.lang:
            why = f"{self.praise()} {it['emoji']} {w} — {self.UZ(it['uz'])}."
        else:
            why = self.praise() + " " + self.U("Bu — {uz}.", uz=self.UZ(it["uz"] or it["say"]))
        return self.make_test(self.q_pick(it), self.opt(it["emoji"], _word(it)), distract, why)

    def opt(self, emoji, word, foreign=True):
        """Test varianti. Til kitobida so'z teglanadi — bola uni ekranda o'qimaydi, ESHITADI (🔊)."""
        word = _clean(word)
        return f"{emoji} {self.E(word)}".strip() if foreign and self.lang else f"{emoji} {word}".strip()

    def tag_option(self, text):
        """Muallif varianti: «🙏 Thank you!» → «🙏 [en]Thank you![/en]»; o'zbekcha variant izoh tiliga o'giriladi."""
        if not self.lang:
            return self.TX(text, "uz")
        if "[" in str(text):
            return self.TX(text, "uz")
        pic, word = _split_picture(text)
        key = _key(word)
        if not key:
            return text
        foreign = key in self.says or (key not in self.uzs and not re.search(r"[oOgG][ʻ'‘’]", word))
        if foreign and _clean(text) in self.uz_variant:
            foreign = False         # izoh != uz: boshqa til kitoblarida ham aynan shunday — o'zbekcha variant
        if foreign:
            return f"{pic}{self.E(word)}".strip()
        word = self.TX(word, "uz")
        return text if self.izoh == "uz" else pic + word

    def author_test(self, t):
        opts = [self.tag_option(o) for o in t["options"]]
        correct = opts[t["answer"]]
        others = [o for i, o in enumerate(opts) if i != t["answer"]]
        q = self.TX(t["q"])
        why = self.TX(t["why"]) if t.get("why") else self.praise()
        if self.lang and self.level >= 3 and t.get("q_en"):
            plain_uz = re.sub(r"\[/?[a-z]{2}\]", "", q)
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
        w = _tag(self.lang, it["say"])
        return self.make_test(self.U("{w} — o'zbekchasi nima?", w=w), f"{it['emoji']} {self.UZ(it['uz'])}",
                              [f"{x['emoji']} {self.UZ(x['uz'])}" for x in others[:3]],
                              self.U("To'g'ri! {w} — {uz}.", w=w, uz=self.UZ(it["uz"])))

    def old_title(self):
        return self.C["old"] if self.lang and self.level >= 3 else self.U("🔁 Eski savol")

    # ── darslar ──
    def review_rows(self, index):
        """REV102: oldingi darslardan 2 tadan bilim (1 va 3 dars oldingi) — bitta qadamda ikkita rasm, har so'zdan
        keyin «Men bilan ayt» / «Say:» (dars xonasi shu joyda bolaga qaytarish uchun pauza qiladi)."""
        rows = []
        for back in (1, 3):
            if index - back < 0 or not self.lesson_items[index - back]:
                continue
            pool = list(self.lesson_items[index - back])
            picks = self.rng.sample(pool, min(2, len(pool)))
            names = " ".join(f"{it['emoji']} {it['say']}" for it in picks)
            if self.lang and self.level >= 3:
                parts = []
                for it in picks:
                    sent = f" {_sentence(it['sentence'])}" if it.get("sentence") else ""
                    parts.append(f"{it['emoji']} {_sentence(it['say'])}{sent} {self.C['say']} {_sentence(it['say'])}")
                text = self.E(f"{self.C['remember']} " + " ".join(parts))
                if self.level == 3:
                    text += " (" + "; ".join(self.UZ(it["uz"]) for it in picks) + ")"
                title = f"🔁 {self.C['t_remember']} {names}"
            elif self.lang:
                pre = f"{self.E(self.C['remember'])} " if self.level == 2 else self.U("Esingdami?") + " "
                text = pre + " ".join(self.U("{emoji} Bu — {w}, ya'ni {uz} Men bilan ayt: {wp}", emoji=it["emoji"],
                                             w=_tag(self.lang, it["say"]), uz=_sentence(self.UZ(it["uz"])),
                                             wp=_tagp(self.lang, it["say"])) for it in picks)
                title = self.U("🔁 Eslaymiz: {names}", names=names)
            else:
                said = []
                for it in picks:
                    uz = _clean(self.UZ(it.get("uz")))
                    said.append(f"{it['emoji']} {_sentence(it['say'])}" + (f" {_sentence(uz[:1].upper() + uz[1:])}" if uz else ""))
                text = self.U("Esingdami? {lines} Qani, birga aytamiz!", lines=" ".join(said))
                title = self.U("🔁 Eslaymiz: {names}", names=names)
            rows.append({"turi": "tushuncha", "sarlavha": title, "matn": self.t(text), "rasm": picks[0].get("image", ""),
                         "doska": "\n".join(self.board(it) for it in picks), "sodda": self.item_simple(picks[0]),
                         "boshqa_usul": self.item_other(picks[0])})
        return rows

    def intro_text(self, lesson, default_uz):
        intro = self.TX(lesson.get("intro"))
        if self.lang and self.level >= 3 and lesson.get("intro_en"):
            return self.E(lesson["intro_en"])
        if self.lang and self.level == 2 and intro:
            return self.t(f"{self.E(self.C['hello_friends'])} {intro}")
        return self.t(intro or default_uz)

    def game_row(self, game_items):
        if self.lang and self.level >= 3:
            names = ", ".join(self.bare(x["say"]) for x in game_items)
            return {"turi": "topshiriq", "sarlavha": self.C["t_point"],
                    "matn": self.E(f"{self.C['game']} {self.C['point_game'].format(names=names)} {self.C['ready']}"),
                    "doska": "  ".join(x["emoji"] for x in game_items), "yechim": self.E(self.C["found"]) + " 🌟"}
        names = ", ".join(_name(self.lang, x) for x in game_items)
        pre = f"{self.E(self.C['game'])} " if self.lang and self.level == 2 else self.U("O'yin vaqti!") + " "
        return {"turi": "topshiriq", "sarlavha": self.U("🎲 Top-chi o'yini"),
                "matn": self.t(pre + self.U("Men aytaman, sen rasmni barmog'ing bilan bos: {names}. Topsang — qarsak chal!", names=names)),
                "doska": "  ".join(x["emoji"] for x in game_items), "yechim": self.U("Barakalla! Hammasini topding! 🌟")}

    def summary_row(self, items):
        if self.lang and self.level >= 3:
            names = ", ".join(self.bare(x["say"]) for x in items)
            text = self.E(f"{self.good()} {self.C['today']} {names}. {self.C['bye']}")
            if self.level == 3:
                text += " " + self.U("Barakalla!")
            return {"turi": "xulosa", "sarlavha": self.C["t_today"], "matn": self.t(text),
                    "doska": "  ".join(f"{x['emoji']} {x['say']}" for x in items)}
        pre = f"{self.E(self.good())} " if self.lang and self.level == 2 else f"{self.praise()} "
        return {"turi": "xulosa", "sarlavha": self.U("🌟 Bugun o'rgandik"),
                "matn": self.t(pre + self.U("Bugun biz {names} ni o'rgandik. Ertaga yana uchrashamiz — yangi sir bor!",
                                            names=", ".join(_name(self.lang, x) for x in items))),
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

    def extra_row(self, row):
        """Muallifning qo'shimcha qatori: o'zbekcha qismlari izoh tiliga o'giriladi."""
        out = {k: row.get(k, "") for k in ("turi", "sarlavha", "matn", "doska", "sodda", "boshqa_usul", "rasm")}
        out["sarlavha"] = self.TX(out["sarlavha"], "nom")
        for k in ("matn", "sodda", "boshqa_usul"):
            out[k] = self.TX(out[k])
        out["doska"] = self.DOSKA(out["doska"])
        return out

    def lesson(self, unit_no, unit, lesson):
        self.where = f"bo'lim {unit_no} «{unit['name']}» / dars «{lesson['name']}»"
        index = len(self.lesson_items)
        items = [dict(it, _unit=unit_no) for it in lesson["items"]]
        name = self.UZ(lesson["name"], "nom")
        rows = [{"turi": "kirish", "sarlavha": f"{unit.get('emoji', '🕊️')} {name}",
                 "matn": self.intro_text(lesson, self.U("Salom, do'stim! Men — robot Kabu. Bip-bip! Bugun «{name}» mavzusini o'rganamiz.", name=name)),
                 "doska": f"🕊️ {name}", "rasm": lesson.get("image_scene", "")}]
        rows += self.review_rows(index)
        for n, it in enumerate(items):
            show_uz = self.lang and it.get("uz") and self.level <= 3
            rows.append({"turi": "tushuncha", "sarlavha": f"{it['emoji']} {it['say']}" + (f" — {self.UZ(it['uz'])}" if show_uz else ""),
                         "matn": self.item_voice(it, n + index), "doska": self.board(it), "rasm": it.get("image", ""),
                         "sodda": self.item_simple(it), "boshqa_usul": self.item_other(it)})
        for row in lesson.get("extra") or []:
            out = self.extra_row(row)
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
        self.topics.append(self.topic(name, self.UZ(lesson.get("goal", ""), "nom"), rows, items))

    # ── hayotiy vaziyat (dialog, rol o'yini) ──
    def scenario(self, unit_no, unit, sc):
        self.where = f"bo'lim {unit_no} «{unit['name']}» / hayotiy vaziyat «{sc['name']}»"
        U = self.U
        index = len(self.lesson_items)
        roles = [self.UZ(r, "nom") for r in (sc.get("roles") or ["", ""])]
        roles_en = sc.get("roles_en") or roles
        lines = []
        for d in sc["dialog"]:
            key = _clean(d["say"]).lower()
            lines.append(dict(d, _unit=unit_no, image=d.get("image") or self.images.get(key, "")))
        scene = sc.get("scene") or {}
        sc_name = self.UZ(sc["name"], "nom")
        title_place = sc.get("name_en") if self.level >= 3 else sc_name
        rows = [{"turi": "kirish", "sarlavha": f"🎭 {title_place}", "rasm": scene.get("image", ""),
                 "matn": self.intro_text({"intro": sc.get("intro"), "intro_en": sc.get("intro_en")},
                                         U("Bip-bip! Bugun hayotiy vaziyat: {name}. Qani, tinglaymiz va o'ynaymiz!", name=sc_name)),
                 "doska": f"{sc.get('emoji', '🎭')} {sc.get('name_en') or sc_name}"}]
        for n, d in enumerate(lines):
            role, role_en = roles[d["who"]], roles_en[d["who"]]
            say = _sentence(d["say"])
            d_uz = self.UZ(d["uz"])
            if self.level >= 4:
                voice = self.E(f"{self.C['says'].format(r=role_en)} {say} {self.C['now_you']} {say}")
            elif self.level == 3:
                voice = f"{self.E(self.C['says'].format(r=role_en) + ' ' + say + ' ' + self.C['listen'] + ' ' + say)} ({d_uz})"
            else:
                voice = U("{role} aytadi: {w} Bu — «{uz}» degani. Takrorlang: {w}", role=role, w=_tagp(self.lang, d["say"]), uz=d_uz)
            rows.append({"turi": "tushuncha", "sarlavha": f"{d.get('emoji', '💬')} {role_en if self.level >= 3 else role}: {d['say']}",
                         "matn": self.t(voice), "rasm": d.get("image", ""),
                         "doska": f"{d.get('emoji', '')} {d['say']}" + (f"\n{d['rom']}" if d.get("rom") else "") + (f"\n{d_uz}" if self.level <= 3 else ""),
                         "sodda": self.t(U("{role} aytadi: {w} O'zbekcha: {uz}.", role=role, w=_tagp(self.lang, d["say"]), uz=d_uz)),
                         "boshqa_usul": self.t(U("Oyna oldida {role} bo'lib ayt: {w}", role=role.lower(), w=_tagp(self.lang, d["say"])))})
        script = "\n".join(f"— {roles_en[d['who']] if self.level >= 3 else roles[d['who']]}: {d['say']}" for d in lines)
        me = roles_en[-1] if self.level >= 3 else roles[-1]
        if self.level >= 3:
            play = self.E(f"{self.C['roleplay']} {self.C['roles_line'].format(a=roles_en[0].lower(), b=roles_en[-1].lower())} " + " ".join(_sentence(d["say"]) for d in lines)
                          + f" {self.C['change_roles']}")
        else:
            play = self.t(U("Keling, rol o'ynaymiz! Men — {a}, sen — {b}. {lines} Endi rollarni almashamiz!",
                            a=roles[0].lower(), b=roles[-1].lower(), lines=" ".join(_tagp(self.lang, d["say"]) for d in lines)))
        rows.append({"turi": "topshiriq", "sarlavha": "🎭 " + (self.C["t_roleplay"] if self.level >= 3 else U("Rol o'ynaymiz")),
                     "matn": play, "doska": script,
                     "yechim": self.E(f"{self.good()} {self.C['great_role'].format(r=me.lower())}") if self.level >= 3 else U("Ofarin! Sen zo'r o'ynading! 🌟")})
        new_tests = [self.author_test(q | {"q": q["q"], "q_en": q.get("q_en"), "why_en": q.get("why_en")}) for q in sc.get("questions") or []]
        new_tests = [t for t in new_tests if t]
        tests = self.spiral_tests(index, new_tests)
        rows += [{k: v for k, v in t.items() if not k.startswith("_")} for t in tests]
        if self.level >= 3:
            rows.append({"turi": "xulosa", "sarlavha": self.C["t_well_done"],
                         "matn": self.E(f"{self.good()} {self.C['scenario_done'].format(name=self.bare(sc.get('name_en') or ''))} {self.C['bye']}"),
                         "doska": f"{sc.get('emoji', '🎭')} {sc.get('name_en') or sc_name} ✅"})
        else:
            pre = f"{self.E(self.good())} " if self.level == 2 else f"{self.praise()} "
            rows.append({"turi": "xulosa", "sarlavha": U("🌟 Bugun o'ynadik"),
                         "matn": self.t(pre + U("Bugun «{name}» vaziyatini o'ynadik. Endi buni hayotda ham ayta olasan! Uyda oilang bilan yana o'yna.", name=sc_name)),
                         "doska": f"{sc.get('emoji', '🎭')} {sc_name} ✅"})
        self.pool.extend(lines)
        self.lesson_items.append(lines)
        self.lesson_tests.append(new_tests)
        topic = self.topic(sc_name, self.UZ(sc.get("goal", ""), "nom"), rows, lines)
        topic["image_scene"] = scene.get("image")
        topic["image_scene_prompt"] = scene.get("image_prompt")
        self.topics.append(topic)

    def previous_year(self):
        """Kitob boshida: o'tgan yilgi kitobdan eng muhim so'zlarni eslash (yoshlar orasidagi spiral)."""
        self.where = "o'tgan yilni eslash"
        U = self.U
        prev = self.previous
        items = [dict(it, _unit=0) for u in prev["units"] for les in u["lessons"] for it in les["items"]]
        rng = random.Random(f"prev|{self.age}")
        rng.shuffle(items)
        items = items[:8]
        if not items:
            return
        rows = [{"turi": "kirish", "sarlavha": "🔁 " + (self.C["t_last_year"] if self.level >= 3 else U("O'tgan yilni eslaymiz")),
                 "matn": self.mix(U("Bip-bip! Salom, do'stim! Yangi kitobni boshlashdan oldin o'tgan yili o'rgangan so'zlarimizni eslaymiz."),
                                  self.C["welcome_back"]),
                 "doska": "🔁 " + "  ".join(x["emoji"] for x in items)}]
        for i in range(0, len(items), 2):
            chunk = items[i:i + 2]
            if self.level >= 3:
                voice = self.E(" ".join(f"{self.C['remember']} {_sentence(x['say'])}" for x in chunk) + f" {self.C['together']}")
            else:
                voice = self.t(U("{lines} Qani, birga aytamiz!",
                                 lines=" ".join(f"{x['emoji']} {_tagp(self.lang, x['say'])} — {_sentence(self.UZ(x['uz']))}" for x in chunk)))
            rows.append({"turi": "tushuncha", "sarlavha": "🔁 " + " ".join(f"{x['emoji']} {x['say']}" for x in chunk),
                         "matn": voice, "rasm": chunk[0].get("image", ""), "doska": "\n".join(self.board(x) for x in chunk),
                         "sodda": self.t(U("O'zbekcha: {lines}", lines="; ".join(f"{_tag(self.lang, x['say'])} — {self.UZ(x['uz'])}" for x in chunk))),
                         "boshqa_usul": self.item_other(chunk[0])})
        self.pool.extend(items)
        tests = [t for t in (self.auto_test(it) for it in items[:5]) if t]
        rows += [{k: v for k, v in t.items() if not k.startswith("_")} for t in tests]
        rows.append(self.summary_row(items[:5]))
        self.lesson_items.append(items)
        self.lesson_tests.append(tests)
        self.topics.append(self.topic(U("O'tgan yilni eslaymiz"), U("O'tgan yilgi kitobdagi asosiy so'zlarni takrorlash"), rows, items))

    def unit_review(self, unit_no, unit, start):
        self.where = f"bo'lim {unit_no} «{unit['name']}» / takrorlash"
        U = self.U
        items = [it for its in self.lesson_items[start:] for it in its]
        if not items:
            return
        en = self.lang and self.level >= 3
        uname = self.UZ(unit["name"], "nom")
        rows = [{"turi": "kirish", "sarlavha": f"🔁 {uname}: " + (self.C["t_review"] if en else U("takrorlaymiz")),
                 "matn": self.mix(U("Bip-bip! Bugun katta takrorlash kuni! «{name}» bo'limida o'rgangan hamma narsani eslaymiz. Har to'g'ri javob — bitta yulduzcha!", name=uname),
                                  self.C["review_intro"]),
                 "doska": "🔁 " + "  ".join(x["emoji"] for x in items[:12])}]
        for i in range(0, len(items), 3):
            chunk = items[i:i + 3]
            if en:
                voice = self.E(" ".join(f"{_sentence(x['say'])}" for x in chunk) + f" {self.C['say_with_me']}")
                if self.level == 3:
                    voice += " (" + "; ".join(self.UZ(x.get("uz", "")) for x in chunk) + ")"
            plain = " ".join(f"{x['emoji']} {_name(self.lang, x)} — {_sentence(self.UZ(x.get('uz')))}" for x in chunk)
            if not en:
                voice = self.t(U("{lines} Men bilan birga takrorla!", lines=plain))
            emojis = " ".join(x["emoji"] for x in chunk)
            rows.append({"turi": "tushuncha", "sarlavha": f"{self.C['t_remember']} {emojis}" if en else U("Eslaymiz: {emojis}", emojis=emojis),
                         "matn": voice, "rasm": chunk[0].get("image", ""),
                         "doska": "\n".join(self.board(x).replace("\n", " — ") for x in chunk),
                         "sodda": self.t(U("Sekin-sekin: {lines}", lines=plain)),
                         "boshqa_usul": self.t(U("Har birini ko'rsatib, qarsak chalib ayt: {lines}", lines=plain))})
        rows.append({"turi": "topshiriq", "sarlavha": "🏃 " + (self.C["t_jump"] if en else U("Harakatli o'yin")),
                     "matn": self.mix(U("Men so'z aytaman: rasm ekranda bo'lsa — sakra, bo'lmasa — o'tir! Tayyormisan? Boshladik!"),
                                      self.C["jump"]),
                     "doska": "  ".join(x["emoji"] for x in items[:12]), "yechim": self.E(self.C["played_great"]) + " 🌟" if en else U("Ofarin! Sen zo'r o'ynading! 🌟")})
        pool_tests = [t for ts in self.lesson_tests[start:] for t in ts]
        self.rng.shuffle(pool_tests)
        count = 5 if self.age in ("2-3 yosh", "3-4 yosh", "4-5 yosh") else 7
        rows += [dict({k: v for k, v in t.items() if not k.startswith("_")}, sarlavha="⭐ " + (self.C["t_review_q"] if en else U("Takror savoli"))) for t in pool_tests[:count]]
        rows.append({"turi": "xulosa", "sarlavha": "🏅 " + (self.C["t_unit_done"] if en else U("Bo'lim tugadi!")),
                     "matn": self.mix(U("Qoyil! «{name}» bo'limini tugatding. Endi yangi sarguzashtga o'tamiz!", name=uname),
                                      self.C["unit_done"]),
                     "doska": f"🏅 {uname}"})
        self.topics.append(self.topic(U("{n}-bo'lim takrori: {name}", n=unit_no, name=uname),
                                      U("«{name}» bo'limini mustahkamlash", name=uname), rows, items[:6]))

    def final_review(self):
        self.where = "kitob oxiri: katta bayram"
        U = self.U
        en = self.lang and self.level >= 3
        rows = [{"turi": "kirish", "sarlavha": "🎉 " + (self.C["t_party"] if en else U("Katta bayram!")),
                 "matn": self.mix(U("Bip-bip! Bugun katta bayram! Butun kitobni tugatding. Keling, eng qiziq so'zlarni eslaymiz va o'yinda yulduzcha yig'amiz!"),
                                  self.C["party_intro"]),
                 "doska": "🎉 " + (self.C["party"] if en else U("Katta bayram"))}]
        sample = self.pool[:]
        self.rng.shuffle(sample)
        for i in range(0, min(len(sample), 16), 4):
            chunk = sample[i:i + 4]
            voice = self.E(" ".join(_sentence(x["say"]) for x in chunk) + f" {self.C['know_all']}") if en else \
                self.t(U("{lines} Ajoyib, hammasini bilasan!", lines=" ".join(f"{x['emoji']} {_sentence(_name(self.lang, x))}" for x in chunk)))
            emojis = " ".join(x["emoji"] for x in chunk)
            rows.append({"turi": "tushuncha", "sarlavha": f"{self.C['t_remember']} {emojis}" if en else U("Eslaymiz: {emojis}", emojis=emojis),
                         "matn": voice, "rasm": chunk[0].get("image", ""), "doska": "\n".join(self.board(x).replace("\n", " — ") for x in chunk)})
        all_tests = [t for ts in self.lesson_tests for t in ts]
        self.rng.shuffle(all_tests)
        rows += [dict({k: v for k, v in t.items() if not k.startswith("_")}, sarlavha="🎉 " + (self.C["t_party_q"] if en else U("Bayram savoli"))) for t in all_tests[:12]]
        rows.append({"turi": "xulosa", "sarlavha": "🏆 " + (self.C["t_champion"] if en else U("Sen chempionsan!")),
                     "matn": self.mix(U("Sen chempionsan! Endi hammasini bilasan. Istalgan darsni qayta ochib, yana o'ynashing mumkin."),
                                      self.C["champion"]),
                     "doska": "🏆"})
        self.topics.append(self.topic(U("Katta bayram: hammasini takrorlaymiz"), U("Butun kitobni mustahkamlash"), rows, sample[:6]))

    def topic(self, name, goal, rows, items):
        words = []
        for it in items:
            w = {k: it.get(k, "") for k in ("say", "uz", "emoji", "image", "image_prompt")} | {"en": it["say"]}
            w["uz"] = self.UZ(w["uz"])
            words.append(w)
        return {"no": len(self.topics) + 1, "name": name, "goal": goal, "rows": rows, "words": words}

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
        self.where = "kitob"
        yechim = self.U(YECHIM_DEFAULT)
        for topic in self.topics:
            for row in topic["rows"]:
                if self.izoh != "uz" and row.get("turi") == "topshiriq" and not row.get("yechim"):
                    row["yechim"] = yechim    # aks holda bogcha_kitob o'zbekcha standart yechimni qo'yardi
                for key in ("matn", "sodda", "boshqa_usul", "yechim"):
                    if len(row.get(key) or "") > 1400:
                        row[key] = row[key][:1400]
        book = {"age": self.age, "book_title": self.title(),
                "subject": self.cur["subject"], "prefix": self.cur.get("prefix") or "BK", "topics": self.topics,
                "immersion": self.base_level}
        if self.izoh != "uz":
            book["izoh"] = self.izoh
        return book


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

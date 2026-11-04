"""REV324: bog'cha til kitoblari tuzatishlarini qo'llaydi (audit: tools/bogcha_audit.py).

Tuzatishlar ma'lumoti — tools/bogcha_tuzatish_rev324.json (aynan «eski → yangi» matnlar):
  intro       — o'zbekcha kirishlar qisqartirildi (ingliz kitobidagi matn kaliti; boshqa tillarda [xx]…[/xx]
                bo'laklari va «inglizcha → ruscha» almashinuvi saqlanib, xuddi shu qisqa matn yasaladi)
  intro_en    — o'rganilayotgan tildagi kirish: ortiqcha gap(lar) olib tashlanadi (hamma tilda bir xil o'rindagi gap)
  item_fix    — til bo'yicha say / rom / sentence tuzatishlari (say o'zgarsa, shu darsdagi matnlarda ham)
  uz_fix, action_fix, emoji_fix, empty_action — hamma tilda umumiy o'zbekcha maydonlar
  text_fix    — darsdagi aniq matn bo'laklari (qo'shiq, doska, test)
  add_items   — elementi kam darslarga (4-5 yosh: 3–4, 6-7 yosh: 4–6) element qo'shish (darslar o'chirilmaydi)

Uch joydagi fayllarga bir xil qo'llanadi: bogcha_content/, repo ildizi, tools/bogcha_content/.
Qayta ishga tushirish xavfsiz: allaqachon tuzatilgan joy topilmaydi, o'zgarish bo'lmaydi.
O'zgarishlar jurnali — docs/bogcha_audit_rev324_ozgarishlar.json (hisobotga tools/bogcha_audit.py qo'shadi).

Ishlatish:  python tools/bogcha_tuzatish_rev324.py [--dry]
"""
import collections
import copy
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.bogcha_audit import (AGE_GROUP, CHANGES, FILE_RE, REPO, TAG_SEG, book_files, file_info,  # noqa: E402
                                iter_lessons, rel)
from tools.bogcha_tillar import uz_language_words  # noqa: E402

DATA = Path(__file__).resolve().parent / "bogcha_tuzatish_rev324.json"
TOOLS = REPO / "tools" / "bogcha_content"
SENT_RE = re.compile(r".*?(?:[.!?…。！？؟]+[\"»”')\]]*\s*|$)", re.S)


# ── fayl formati saqlanadi (indent va oxirgi qator) ──
def load(path):
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    fmt = (1, "")
    for ind in (1, 2):
        s = json.dumps(data, ensure_ascii=False, indent=ind)
        if raw in (s, s + "\n"):
            fmt = (ind, raw[len(s):])
            break
    return data, fmt


def dump(data, fmt):
    return json.dumps(data, ensure_ascii=False, indent=fmt[0]) + fmt[1]


def strip_marks(text):
    return "".join(ch for ch in str(text or "") if not unicodedata.category(ch).startswith("M"))


def split_sentences(text):
    """Gaplarni oraliq bo'sh joylari bilan birga qaytaradi ("".join(...) == text)."""
    out = [m.group(0) for m in SENT_RE.finditer(str(text or "")) if m.group(0)]
    return out


class Fixer:
    def __init__(self, repo=REPO):
        self.repo = repo
        self.data = json.loads(DATA.read_text(encoding="utf-8"))
        self.books = {}   # path → [book, fmt, original_text]
        for p in book_files(repo):
            book, fmt = load(p)
            self.books[p] = [book, fmt, p.read_text(encoding="utf-8")]
        self.log = []
        self.source = {}
        self.unused = collections.Counter()
        self.enrich_renames = []

    # ── jurnal ──
    def rec(self, path, where, field, old, new, reason, kind, source=None):
        """source — bir xil tuzatishning tillar bo'yicha guruhi (ingliz matni yoki qoida kaliti)."""
        if old == new:
            return
        r = {"fayl": rel(path, self.repo), "dars": where, "maydon": field, "eski": old, "yangi": new, "sabab": reason, "tur": kind}
        if source:
            r["manba"] = source
        self.log.append(r)

    @staticmethod
    def lesson_label(ui, li, les):
        return f"{ui}.{li} «{les.get('name', '')}»"

    def lessons(self, langs=None, groups=None):
        for p, (book, _, _) in self.books.items():
            lang, age, group = file_info(p)
            if langs and lang not in langs:
                continue
            if groups and group not in groups:
                continue
            for ui, li, unit, les in iter_lessons(book):
                yield p, lang, group, book, ui, li, les

    # ── darsdagi barcha matn maydonlari: (konteyner, kalit) ──
    @staticmethod
    def text_slots(les, with_items=False):
        slots = [(les, "name")]
        for r in les.get("extra") or []:
            for k in ("sarlavha", "matn", "doska", "sodda", "boshqa_usul", "matn_en", "sarlavha_en"):
                if isinstance(r.get(k), str):
                    slots.append((r, k))
        for t in les.get("tests") or []:
            for k in ("q", "why", "q_en"):
                if isinstance(t.get(k), str):
                    slots.append((t, k))
            opts = t.get("options") or []
            for i in range(len(opts)):
                slots.append((opts, i))
        if with_items:
            for it in les.get("items") or []:
                if isinstance(it.get("sentence"), str):
                    slots.append((it, "sentence"))
        return slots

    def replace_in_lesson(self, p, label, les, old, new, reason, kind, word=False):
        if file_info(p)[0] in ("ja", "zh", "ko"):
            word = False   # bo'sh joysiz yozuv — so'z chegarasi yo'q
        marks_only = strip_marks(old) == strip_marks(new)   # faqat harakat qo'shildi (arabcha)
        n = 0
        for cont, key in self.text_slots(les):
            if marks_only and isinstance(key, str) and (key == "name" or key.endswith("_en")):
                continue   # nom va to'liq gaplar harakatsiz yoziladi
            val = cont[key]
            if not isinstance(val, str) or old not in val:
                continue
            if word:
                pat = re.compile(r"(?<![^\W\d_])" + re.escape(old) + r"(?![^\W\d_])")
                nv = pat.sub(new, val)
            else:
                nv = val.replace(old, new)
            if nv != val:
                cont[key] = nv
                n += 1
                self.rec(p, label, f"matn ({key})", val, nv, reason, kind)
        return n

    # ── 1) element tuzatishlari ──
    def item_fixes(self):
        for fx in self.data["item_fix"]:
            hit = 0
            for p, lang, group, book, ui, li, les in self.lessons(langs={fx["lang"]}):
                label = self.lesson_label(ui, li, les)
                for it in les.get("items") or []:
                    if fx.get("uz") and it.get("uz") != fx["uz"]:
                        continue
                    if fx.get("image") and it.get("image") != fx["image"]:
                        continue
                    field = fx["field"]
                    if it.get(field) != fx["old"]:
                        continue
                    hit += 1
                    it[field] = fx["new"]
                    self.rec(p, label, field, fx["old"], fx["new"], fx["reason"], f"Element: {field}")
                    if field == "say" and fx.get("new_rom") and "rom" in it:
                        old_rom = it["rom"]
                        it["rom"] = fx["new_rom"]
                        self.rec(p, label, "rom", old_rom, fx["new_rom"], "say o'zgargani uchun o'qilishi ham", "Element: rom")
                    if field == "say" and fx.get("propagate"):
                        self.replace_in_lesson(p, label, les, fx["old"], fx["new"],
                                               "say o'zgargani uchun darsdagi matnda ham", "Dars matni", word=True)
            if not hit:
                self.unused[f"item_fix {fx['lang']} {fx['field']} «{fx['old']}»"] += 1
            if hit and fx["lang"] == "en" and fx["field"] == "say":
                self.enrich_renames.append((fx["old"], fx["new"], fx["reason"]))

    def rename_enrich(self):
        """Ingliz kitobi say'i o'zgarsa — *_enrich.json dagi kalit va matnlar ham (testlar kalit bo'yicha qidiradi)."""
        for old, new, reason in self.enrich_renames:
            pat = re.compile(r"(?<![^\W\d_])" + re.escape(old) + r"(?![^\W\d_])")
            for path in sorted(TOOLS.glob("en_*_enrich.json")):
                data, fmt = load(path)
                changed = False
                for name, les in (data.get("lessons") or {}).items():
                    items = les.get("items") or {}
                    if old in items and new not in items:
                        les["items"] = {(new if k == old else k): v for k, v in items.items()}
                        changed = True
                        self.log.append({"fayl": rel(path, self.repo), "dars": f"«{name}»", "maydon": "items (kalit)",
                                         "eski": old, "yangi": new, "sabab": reason, "tur": "Element: say"})
                    text = json.dumps(les, ensure_ascii=False)
                    if pat.search(text):
                        les2 = json.loads(pat.sub(new.replace("\\", "\\\\"), text))
                        les.clear(); les.update(les2)
                        changed = True
                        self.log.append({"fayl": rel(path, self.repo), "dars": f"«{name}»", "maydon": "matn",
                                         "eski": old, "yangi": new, "sabab": "say o'zgargani uchun boyitish matnlarida ham",
                                         "tur": "Dars matni"})
                if changed:
                    path.write_text(dump(data, fmt), encoding="utf-8")

    # ── 2) umumiy o'zbekcha maydonlar ──
    def shared_fixes(self):
        for kind, key, items in (("O'zbekcha ma'no (uz)", "uz", self.data["uz_fix"]),
                                 ("Harakat (action)", "action", self.data["action_fix"])):
            for fx in items:
                hit = 0
                for p, lang, group, book, ui, li, les in self.lessons():
                    for it in les.get("items") or []:
                        if it.get(key) == fx["old"]:
                            it[key] = fx["new"]
                            hit += 1
                            self.rec(p, self.lesson_label(ui, li, les), key, fx["old"], fx["new"], fx["reason"], kind)
                if not hit:
                    self.unused[f"{key} «{fx['old']}»"] += 1
        for fx in self.data["emoji_fix"]:
            hit = 0
            for p, lang, group, book, ui, li, les in self.lessons():
                label = self.lesson_label(ui, li, les)
                for it in les.get("items") or []:
                    if it.get("uz") == fx["uz"] and it.get("emoji") == fx["old"]:
                        it["emoji"] = fx["new"]
                        hit += 1
                        self.rec(p, label, "emoji", fx["old"], fx["new"], fx["reason"], "Emoji")
                        self.replace_in_lesson(p, label, les, fx["old"], fx["new"], "emoji o'zgargani uchun test/doskada ham", "Dars matni")
            if not hit:
                self.unused[f"emoji {fx['uz']}"] += 1
        for fx in self.data["empty_action"]:
            hit = 0
            for p, lang, group, book, ui, li, les in self.lessons():
                for it in les.get("items") or []:
                    if it.get("uz") == fx["uz"] and "action" in it and not str(it["action"]).strip():
                        old = it["action"]
                        it["action"] = fx["new"]
                        hit += 1
                        self.rec(p, self.lesson_label(ui, li, les), "action", old, fx["new"],
                                 "bo'sh «action» — bola o'zi bajaradigan xavfsiz harakat yozildi", "Harakat (action)")
            if not hit:
                self.unused[f"empty_action {fx['uz']}"] += 1

    # ── 3) darsdagi aniq matnlar ──
    def text_fixes(self):
        for fx in self.data["text_fix"]:
            hit = 0
            for p, lang, group, book, ui, li, les in self.lessons(langs=None if fx["lang"] == "*" else {fx["lang"]}):
                if fx.get("anchor_image") and not any(it.get("image") == fx["anchor_image"] for it in les.get("items") or []):
                    continue
                hit += self.replace_in_lesson(p, self.lesson_label(ui, li, les), les, fx["old"], fx["new"], fx["reason"], "Dars matni")
            if not hit:
                self.unused[f"text_fix {fx['lang']} «{fx['old'][:40]}»"] += 1

    # ── 4) kirishlar ──
    def _aligned(self):
        """tools/ dagi har til kitobi ingliz kitobi bilan dars-dars mos: (lang, en_les, les)."""
        for p in sorted(TOOLS.glob("*.json")):
            m = FILE_RE.match(p.name)
            if not m or m.group("lang") == "en":
                continue
            en_path = TOOLS / ("en_" + p.name[3:])
            if not en_path.is_file() or p not in self.books or en_path not in self.books:
                continue
            a = [les for *_, les in iter_lessons(self.books[en_path][0])]
            b = [les for *_, les in iter_lessons(self.books[p][0])]
            if len(a) != len(b):
                continue
            for x, y in zip(a, b):
                if [i.get("image") for i in x.get("items") or []] == [i.get("image") for i in y.get("items") or []]:
                    yield m.group("lang"), x, y

    def intro_maps(self):
        """Til → {eski kirish: yangi kirish}. Faqat o'zgartirishdan OLDIN chaqiriladi."""
        en_map = {d["old"]: d["new"] for d in self.data["intro"]}
        maps = {"en": dict(en_map)}
        skipped = collections.Counter()
        for lang, en_les, les in self._aligned():
            old_en, old = en_les.get("intro"), les.get("intro")
            if old_en not in en_map or not old:
                continue
            segs_en = [m.group("body") for m in TAG_SEG.finditer(old_en)]
            segs = [m.group("body") for m in TAG_SEG.finditer(old)]
            skel_en = uz_language_words(TAG_SEG.sub("§", old_en), lang)
            if len(segs_en) != len(segs) or skel_en != TAG_SEG.sub("§", old):
                skipped[lang] += 1
                continue

            def sub(m):
                body = m.group("body")
                j = segs_en.index(body)
                return f"[{lang}]{segs[j]}[/{lang}]"
            new = uz_language_words(TAG_SEG.sub(sub, en_map[old_en]), lang)
            prev = maps.setdefault(lang, {}).get(old)
            if prev and prev != new:
                skipped[lang + " (ziddiyat)"] += 1
                continue
            maps[lang][old] = new
            self.source.setdefault(("intro", lang, old), old_en)
        for k in en_map:
            self.source.setdefault(("intro", "en", k), k)
        self.intro_skipped = skipped
        return maps

    def _enrich(self, stem):
        path = TOOLS / f"{stem}_enrich.json"
        if not hasattr(self, "_enrich_cache"):
            self._enrich_cache = {}
        if stem not in self._enrich_cache:
            self._enrich_cache[stem] = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        return self._enrich_cache[stem]

    def _en_intro_en(self, en_stem, en_les):
        """Ingliz kitobida intro_en bo'lmasa (56, 67, 67p) — u *_enrich.json da."""
        return en_les.get("intro_en") or ((self._enrich(en_stem).get("lessons") or {}).get(en_les.get("name")) or {}).get("intro_en")

    def intro_en_maps(self):
        specs = {d["en_old"]: d for d in self.data["intro_en"]}
        maps = {"en": {}}
        for k, d in specs.items():
            if (d.get("manual") or {}).get("en"):
                maps["en"][k] = d["manual"]["en"]
            elif d.get("drop") is not None:
                parts = split_sentences(k)
                maps["en"][k] = "".join(s for i, s in enumerate(parts) if i not in d["drop"]).strip()
        bad = collections.Counter()
        for p in sorted(TOOLS.glob("*.json")):
            m = FILE_RE.match(p.name)
            if not m or m.group("lang") == "en" or p not in self.books:
                continue
            lang, en_path = m.group("lang"), TOOLS / ("en_" + p.name[3:])
            if en_path not in self.books:
                continue
            a = [les for *_, les in iter_lessons(self.books[en_path][0])]
            b = [les for *_, les in iter_lessons(self.books[p][0])]
            if len(a) != len(b):
                continue
            for en_les, les in zip(a, b):
                d = specs.get(self._en_intro_en(en_path.stem, en_les))
                if not d or not les.get("intro_en"):
                    continue
                old = les["intro_en"]
                if lang in (d.get("manual") or {}):
                    new = d["manual"][lang]
                elif d.get("drop") is None:
                    continue
                else:
                    parts = split_sentences(old)
                    if len(parts) != len(split_sentences(d["en_old"])):
                        bad[lang] += 1
                        continue
                    new = "".join(s for i, s in enumerate(parts) if i not in d["drop"]).strip()
                maps.setdefault(lang, {})[old] = new
                self.source.setdefault(("intro_en", lang, old), d["en_old"])
        for k in maps["en"]:
            self.source.setdefault(("intro_en", "en", k), k)
        self.intro_en_bad = bad
        self.intro_en_en = maps["en"]
        return maps

    def update_enrich_intro_en(self):
        """Ingliz boyitish fayllaridagi intro_en ham xuddi shunday qisqartiriladi (manba bir xil bo'lsin)."""
        for path in sorted(TOOLS.glob("en_*_enrich.json")):
            data, fmt = load(path)
            changed = False
            for name, les in (data.get("lessons") or {}).items():
                old = les.get("intro_en")
                if old in self.intro_en_en:
                    les["intro_en"] = self.intro_en_en[old]
                    changed = True
                    self.log.append({"fayl": rel(path, self.repo), "dars": f"«{name}»", "maydon": "intro_en", "eski": old,
                                     "yangi": les["intro_en"], "sabab": "o'rganilayotgan tildagi kirishda gap ko'p — ortiqcha gap olib tashlandi",
                                     "tur": "Kirish (intro_en)", "manba": "intro_en:" + old})
            if changed:
                path.write_text(dump(data, fmt), encoding="utf-8")

    def apply_intros(self, imap, emap):
        for p, lang, group, book, ui, li, les in self.lessons():
            label = self.lesson_label(ui, li, les)
            old = les.get("intro")
            if old in imap.get(lang, {}):
                les["intro"] = imap[lang][old]
                self.rec(p, label, "intro", old, les["intro"], "kirish yoshga nisbatan uzun — ma'nosi saqlanib qisqartirildi", "Kirish (intro)",
                         source="intro:" + self.source.get(("intro", lang, old), old))
            old = les.get("intro_en")
            if old in emap.get(lang, {}):
                les["intro_en"] = emap[lang][old]
                self.rec(p, label, "intro_en", old, les["intro_en"], "o'rganilayotgan tildagi kirishda gap ko'p — ortiqcha gap olib tashlandi", "Kirish (intro_en)",
                         source="intro_en:" + self.source.get(("intro_en", lang, old), old))

    # ── 5) element qo'shish ──
    def _find_item(self, path, image):
        book = self.books.get(path, [None])[0]
        if not book:
            return None
        for *_, les in iter_lessons(book):
            for it in les.get("items") or []:
                if it.get("image") == image:
                    return it
        return None

    def _image_prompt(self, image):
        for book, _, _ in self.books.values():
            for *_, les in iter_lessons(book):
                for it in les.get("items") or []:
                    if it.get("image") == image and it.get("image_prompt"):
                        return it["image_prompt"]
        return None

    def _en_sentence(self, image, say):
        """Misol gapi kitobda emas, *_enrich.json da bo'lgan ingliz kitoblari uchun — boshqa ingliz kitobidan olinadi."""
        for p, (book, _, _) in self.books.items():
            if p.parent != TOOLS or not p.name.startswith("en_"):
                continue
            for *_, les in iter_lessons(book):
                for it in les.get("items") or []:
                    if it.get("image") == image and it.get("say") == say and it.get("sentence"):
                        return it["sentence"]
        return None

    def add_items(self):
        self.enrich_new = []   # (book key, lesson name, say, sentence)
        for spec in self.data["add_items"]:
            hit = 0
            for p, lang, group, book, ui, li, les in self.lessons(groups={spec["group"]}):
                items = les.get("items") or []
                if [i.get("image") for i in items] != spec["anchor"]:
                    continue
                has_sentence = any(i.get("sentence") for i in items)   # shu darsda misol gaplar bormi
                if spec["kind"] == "copy_same_book":
                    src = None
                    for *_, l2 in iter_lessons(book):
                        for it in l2.get("items") or []:
                            if it.get("image") == spec["src_image"]:
                                src = it
                    new = copy.deepcopy(src) if src else None
                elif spec["kind"] == "copy":
                    src = self._find_item(TOOLS / f"{lang}_{spec['src_book']}.json", spec["src_image"])
                    new = copy.deepcopy(src) if src else None
                    if new is not None:
                        for k in spec.get("drop") or []:
                            new.pop(k, None)
                        if spec.get("uz"):
                            new["uz"] = spec["uz"]
                else:
                    base, per = spec["item"], spec["item"]["langs"].get(lang)
                    new = None
                    if per:
                        new = {"say": per["say"], "uz": base["uz"], "emoji": base["emoji"], "image": base["image"],
                               "image_prompt": self._image_prompt(base["image"]) or ""}
                        if base.get("action"):
                            new["action"] = base["action"]
                        if per.get("sentence"):
                            new["sentence"] = per["sentence"]
                        if per.get("rom"):
                            new["rom"] = per["rom"]
                if new is None:
                    self.unused[f"add_items {lang} {spec['anchor'][0]}"] += 1
                    continue
                sentence = new.get("sentence")
                if not has_sentence:
                    new.pop("sentence", None)
                    new.pop("action_en", None)
                elif not new.get("sentence"):
                    self.unused[f"add_items: misol gap yo'q {lang} {new['say']}"] += 1
                if any(i.get("say") == new["say"] for i in items):
                    continue   # allaqachon qo'shilgan
                pos = len(items) if spec["pos"] == "end" else spec["pos"]
                items.insert(pos, new)
                hit += 1
                self.rec(p, self.lesson_label(ui, li, les), "items", f"{len(items) - 1} ta element",
                         f"+ «{new['say']}» ({new['uz']}) → {len(items)} ta", spec["reason"], "Element qo'shildi",
                         source="add:" + "|".join(spec["anchor"]))
                if lang == "en" and not has_sentence and p.parent == TOOLS:
                    sentence = sentence or self._en_sentence(new.get("image"), new["say"])
                    if sentence:
                        self.enrich_new.append((p.stem, les["name"], new["say"], sentence, spec["reason"]))
            if not hit:
                self.unused[f"add_items {spec['anchor'][0]}"] += 1

    def update_enrich(self):
        """en_67 / en_67p kitoblarining misol gaplari alohida *_enrich.json da (testlar shuni talab qiladi)."""
        for stem, name, say, sentence, reason in self.enrich_new:
            path = TOOLS / f"{stem}_enrich.json"
            if not path.is_file():
                continue
            data, fmt = load(path)
            les = (data.get("lessons") or {}).get(name)
            if les is None:
                continue
            items = les.setdefault("items", {})
            if say in items:
                continue
            items[say] = {"sentence": sentence}
            path.write_text(dump(data, fmt), encoding="utf-8")
            self.log.append({"fayl": rel(path, self.repo), "dars": f"«{name}»", "maydon": "items", "eski": "—",
                             "yangi": f"+ «{say}»: {sentence}", "sabab": reason + " (ingliz kitobining misol gapi)",
                             "tur": "Element qo'shildi"})

    # ── hammasi ──
    def run(self, write=True):
        imap = self.intro_maps()
        emap = self.intro_en_maps()
        self.item_fixes()
        self.shared_fixes()
        self.text_fixes()
        self.apply_intros(imap, emap)
        self.add_items()
        changed = []
        for p, (book, fmt, original) in self.books.items():
            text = dump(book, fmt)
            if text != original:
                changed.append(p)
                if write:
                    p.write_text(text, encoding="utf-8")
        if write:
            self.update_enrich()
            self.rename_enrich()
            self.update_enrich_intro_en()
            if self.log:
                write_changes(self.log, self.repo)
        return changed


def _files_label(files):
    names = sorted({f.rsplit("/", 1)[-1] for f in files})
    locs = sorted({(f.rsplit("/", 1)[0] if "/" in f else ".") for f in files})
    shown = ", ".join(n[:-5] for n in names[:8]) + (f" +{len(names) - 8}" if len(names) > 8 else "")
    return f"{shown} ({len(files)} fayl, {len(locs)} joy)"


def write_changes(log, repo=REPO):
    """Guruhlab yozadi: bir xil tuzatish (hamma til va nusxada) — bitta guruh; har fayl yozuvi guruh raqamiga ishora qiladi.
    Kirish va qo'shilgan elementlar tillar bo'yicha bitta guruhga yig'iladi (ingliz kitobidagi ko'rinishi ko'rsatiladi)."""
    groups = collections.OrderedDict()
    for r in log:
        key = r.get("manba") or (r["tur"], r["maydon"], r["eski"], r["yangi"], r["sabab"])
        g = groups.setdefault(key, {"tur": r["tur"], "maydon": r["maydon"], "eski": r["eski"], "yangi": r["yangi"],
                                    "sabab": r["sabab"], "_f": [], "_d": [], "_en": False})
        is_en = r["fayl"].rsplit("/", 1)[-1].startswith("en_")
        if is_en and not g["_en"]:   # ko'rsatish uchun ingliz kitobidagi ko'rinishi
            g.update(eski=r["eski"], yangi=r["yangi"], _en=True)
        g["_f"].append(r["fayl"])
        if is_en and r["dars"] not in g["_d"]:
            g["_d"].insert(0, r["dars"])
        elif r["dars"] not in g["_d"]:
            g["_d"].append(r["dars"])
    order = ["Kirish (intro)", "Kirish (intro_en)", "Element qo'shildi", "Element: say", "Element: rom", "Element: sentence",
             "O'zbekcha ma'no (uz)", "Emoji", "Harakat (action)", "Dars matni"]
    keys = sorted(groups, key=lambda k: order.index(groups[k]["tur"]) if groups[k]["tur"] in order else 99)
    index = {k: i for i, k in enumerate(keys)}
    out = []
    for k in keys:
        g = groups[k]
        d = g["_d"]
        langs = sorted({f.rsplit("/", 1)[-1][:2] for f in g["_f"]})
        out.append({"tur": g["tur"], "maydon": g["maydon"], "eski": g["eski"], "yangi": g["yangi"], "sabab": g["sabab"],
                    "tillar": langs, "fayllar": _files_label(g["_f"]),
                    "dars": "; ".join(d[:2]) + (f" (+{len(d) - 2})" if len(d) > 2 else "")})
    rows = [{"fayl": r["fayl"], "dars": r["dars"], "maydon": r["maydon"], "guruh": index[r.get("manba") or
             (r["tur"], r["maydon"], r["eski"], r["yangi"], r["sabab"])]} for r in log]
    data = {"izoh": "guruhlar — noyob tuzatishlar (hisobotdagi jadval); hammasi — har fayl/dars yozuvi, «guruh» — guruhlar ro'yxatidagi o'rni",
            "jami_fayl_ozgarish": len(log), "guruhlar": out, "hammasi": rows}
    CHANGES.parent.mkdir(parents=True, exist_ok=True)
    CHANGES.write_text(json.dumps(data, ensure_ascii=False, indent=0), encoding="utf-8")


def main(argv):
    fx = Fixer()
    changed = fx.run(write="--dry" not in argv)
    kinds = collections.Counter(r["tur"] for r in fx.log)
    print(f"o'zgargan fayllar: {len(changed)}, o'zgarishlar: {len(fx.log)}")
    for k, n in kinds.most_common():
        print(f"  {k}: {n}")
    if fx.intro_skipped:
        print("kirish mos kelmadi (qo'lda):", dict(fx.intro_skipped))
    if fx.intro_en_bad:
        print("intro_en gap soni mos emas:", dict(fx.intro_en_bad))
    if fx.unused and fx.log:
        print("qo'llanmagan tuzatishlar:")
        for k, n in fx.unused.items():
            print("  -", k)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

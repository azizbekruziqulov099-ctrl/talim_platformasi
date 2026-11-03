"""REV298: mavzu testini Miya darsining O'Z mazmunidan to'ldirish — har mavzuga (har tilda) kamida 20 ta savol.
Savollar to'g'riligi tuzilishidan kafolatlanadi (javob darsdagi so'z/rasmning o'zi, chalg'ituvchilar — boshqa so'zlar):
  • rasm → so'z («🍎 — bu nima?»), so'z → rasm («Qaysi rasm: olma?»),
  • ma'no → so'z va so'z → ma'no (darsda «🍎 [en]apple[/en] — olma» ko'rinishi bo'lsa),
  • sanash («Nechta 🍎?» — doskadagi takrorlangan rasmlardan, bog'cha matematikasi).
Savol matni o'quvchi tilida (uz/ru/en); o'rganilayotgan til so'zi o'z tegida qoladi (ovoz shu tilda o'qiydi)."""
import random
import re

EMO = r"(?:[\U0001F300-\U0001FAFF\u2600-\u27BF]\uFE0F?(?:\u200D[\U0001F300-\U0001FAFF\u2600-\u27BF]\uFE0F?)*)"
TEG = r"\[(?P<t>en|ru|de|fr|es|ar|tr|ko|ja|zh)\](?P<w>[^\[\]]{1,40}?)\[/(?P=t)\]"
YOQ = set("❓🔁🎲🧩🎤👏✅❌➡⬅🌟⭐✨💡🔊🔗🔎👆👉✋🕊🗣🎵🎶🙂😊🤔👀")
SUZ = {
    "uz": {"bosh": "Bo‘sh joyga mos so‘zni tanlang:", "nima": "{e} — bu nima?", "qaysi": "Qaysi rasm: {w}?", "tarjima": "«{m}» qanday aytiladi?", "mano": "{w} — nima degani?", "nechta": "Nechta {e}? {k}"},
    "ru": {"bosh": "Выберите слово для пропуска:", "nima": "{e} — что это?", "qaysi": "Какая картинка: {w}?", "tarjima": "Как сказать «{m}»?", "mano": "{w} — что это значит?", "nechta": "Сколько {e}? {k}"},
    "en": {"bosh": "Choose the word for the gap:", "nima": "{e} — what is this?", "qaysi": "Which picture is {w}?", "tarjima": "How do you say «{m}»?", "mano": "What does {w} mean?", "nechta": "How many {e}? {k}"},
}


# «New word: circus.», «Repeat: …» — har qanday so'z mos keladi, bo'sh joy savoli bo'lmaydi
META = re.compile(r"^\s*(new word|new words|remember|repeat|listen|say|look|again|word|новое слово|повтори|слушай|скажи|запомни|neues wort|nouveau mot|nueva palabra|yeni kelime)\b|:\s", re.I)


BOSH_JOY = False


def _toza(e):
    return e.replace("\uFE0F", "")


def lugat(lesson, til=""):
    """Darsdagi (rasm, so'z, teg, ma'no) to'plami — tartib saqlanadi, takrorsiz.
    Faqat darsda KAMIDA IKKI MARTA (sarlavha, doska, ovozda) birga kelgan rasm+so'z olinadi — tasodifiy «🟣 Rolli o'yin»
    kabi belgi-ro'yxat qatorlari so'z bo'lib qolmasin. O'quvchi tilidagi teg (izoh qatori) — o'rganiladigan so'z emas."""
    import collections
    topildi, tartib = collections.Counter(), {}
    def ol(e, t, w, mano):
        w = w.strip(" .!?…"); mano = (mano or "").strip(" .")
        if _toza(e) in YOQ or not w or len(w.split()) > 4 or ":" in w or re.search(r"\d", w):
            return
        k = (_toza(e), t, w.lower())
        topildi[k] += 1
        if k not in tartib or (mano and not tartib[k]["m"]):
            tartib[k] = {"e": e, "w": w, "t": t, "m": mano if ":" not in mano else ""}
    for st in (lesson or {}).get("steps") or []:
        for maydon in ("sarlavha", "doska", "ovoz"):
            matn = str(st.get(maydon) or "")
            for m in re.finditer(rf"(?P<e>{EMO})\s*{TEG}\s*(?:[—–-]\s*(?P<m>[^\n\[\]]{{2,40}}))?", matn):
                ol(m.group("e"), m.group("t"), m.group("w"), m.group("m"))
            for line in matn.split("\n"):
                m = re.fullmatch(rf"\s*({EMO})\s+([^\d\[\]\n→←=+:]{{2,30}}?)\s*", line)
                if m and len(m.group(2).split()) <= 2:
                    ol(m.group(1), "", m.group(2), "")
    out = [tartib[k] for k in tartib if topildi[k] >= 2]
    if til and any(x["t"] and x["t"] != til for x in out):
        out = [x for x in out if x["t"] != til]
    # bir rasm — bir so'z, bir so'z — bir rasm (aks holda savolda ikki to'g'ri javob chiqadi)
    re_e, re_w, natija = set(), set(), []
    for x in out:
        if _toza(x["e"]) not in re_e and (x["t"], x["w"].lower()) not in re_w:
            re_e.add(_toza(x["e"])); re_w.add((x["t"], x["w"].lower())); natija.append(x)
    return natija


def _w(x):
    return f"[{x['t']}]{x['w']}[/{x['t']}]" if x["t"] else x["w"]


def _sanoq(lesson):
    """Doskadagi takrorlangan rasm qatorlari: «🍎🍎🍎» → (🍎, 3)."""
    out, seen = [], set()
    for st in (lesson or {}).get("steps") or []:
        for m in re.finditer(rf"(({EMO}))(?:\2){{1,9}}", str(st.get("doska") or "")):
            e = m.group(2); k = len(re.findall(re.escape(_toza(e)), _toza(m.group(0))))
            if _toza(e) not in YOQ and 1 <= k <= 10 and (_toza(e), k) not in seen:
                seen.add((_toza(e), k)); out.append((e, k))
    return out


def yasash(lesson, til="uz", soni=20, boshqa_lugat=(), seed=""):
    """Darsning o'z mazmunidan savollar (variantlar soni 3, to'g'ri javob tasodifiy joyda)."""
    S = SUZ.get(til if til in SUZ else "uz")
    L = lugat(lesson, til)
    pool = L + [x for x in boshqa_lugat if _toza(x["e"]) not in {_toza(y["e"]) for y in L}]
    rnd = random.Random(f"{seed}|{til}")
    savollar = []
    def var(tog, chalg):
        chalg = [c for c in dict.fromkeys(chalg) if c != tog]
        rnd.shuffle(chalg)
        v = [tog] + chalg[:2]
        if len(v) < 3:
            return None
        rnd.shuffle(v)
        return v, v.index(tog)
    for x in L:
        boshqalar = [y for y in pool if y is not x]
        # rasm → so'z
        r = var(_w(x), [_w(y) for y in boshqalar if y["w"].lower() != x["w"].lower()])
        if r: savollar.append({"savol": S["nima"].format(e=x["e"]), "variantlar": r[0], "togri": r[1]})
        # so'z → rasm
        r = var(x["e"], [y["e"] for y in boshqalar])
        if r: savollar.append({"savol": S["qaysi"].format(w=_w(x)), "variantlar": r[0], "togri": r[1]})
        if x["m"]:
            r = var(_w(x), [_w(y) for y in boshqalar if y["w"].lower() != x["w"].lower()])
            if r: savollar.append({"savol": S["tarjima"].format(m=x["m"]), "variantlar": r[0], "togri": r[1]})
            r = var(x["m"], [y["m"] for y in boshqalar if y["m"] and y["m"].lower() != x["m"].lower()])
            if r: savollar.append({"savol": S["mano"].format(w=_w(x)), "variantlar": r[0], "togri": r[1]})
    # bo'sh joy: darsdagi misol gapda so'z o'rniga «___» («[en]We were at the ___ on Saturday.[/en]»)
    gaplar = []
    for st in (lesson or {}).get("steps") or []:
        for maydon in ("doska", "ovoz"):
            for m in re.finditer(TEG, str(st.get(maydon) or "")):
                if len(m.group("w").split()) >= 3 or len(m.group("w")) > 25:
                    gaplar.append((m.group("t"), m.group("w")))
    for t, g in re.findall(rf"\[(en|ru|de|fr|es|ar|tr|ko|ja|zh)\]([^\[\]]{{12,160}}?)\[/\1\]", " ".join(str(st.get("doska") or "") + " " + str(st.get("ovoz") or "") for st in (lesson or {}).get("steps") or [])):
        gaplar.append((t, g))
    ishlatilgan = set()
    # Bo'sh joy savoli o'chirilgan: kontekst ko'pincha bir nechta javobga to'g'ri keladi («Abre las manos como ___»)
    # — xato savoldan ko'ra savolsiz yaxshi. Faqat tuzilishidan to'g'riligi kafolatlangan savollar qoladi.
    for x in (L if BOSH_JOY else []):
        if not x["t"] or len(x["w"]) < 2:
            continue
        rx = re.compile(rf"(?<![\w’']){re.escape(x['w'])}(?![\w’'])", re.I)
        for t, g in gaplar:
            # faqat to'liq gap (nuqta/undov/so'roq bilan tugaydi), kamida 6 so'z, rasm belgisiz — kontekst javobni aniq belgilasin
            g = g.strip()
            if META.search(g) or len(g.split()) < 6 or not re.search(r"[.!?]$", g) or re.search(EMO, g):
                continue
            if t == x["t"] and rx.search(g) and g not in ishlatilgan and len(rx.findall(g)) == 1 and g.strip().lower() != x["w"].lower():
                ishlatilgan.add(g)
                r = var(_w(x), [_w(y) for y in pool if y is not x and y["t"] == x["t"] and y["w"].lower() != x["w"].lower()])
                if r:
                    savollar.append({"savol": f"{S['bosh']} [{t}]{rx.sub('___', g, count=1)}[/{t}]", "variantlar": r[0], "togri": r[1]})
                break
    sanoq = _sanoq(lesson)
    if sanoq:
        # sanash darsi — darsdagi rasmlar bilan, darsdagi eng katta songacha (kamida 5) turli sonlar
        eng = max(5, max(k for _, k in sanoq))
        rasmlar = list(dict.fromkeys(e for e, _ in sanoq))   # faqat darsda sanalgan rasmlar (mavzuga mos)
        juft = list(dict.fromkeys(sanoq + [(e, k) for e in rasmlar for k in range(1, eng + 1)]))
        for e, k in juft:
            chalg = [str(n) for n in (k - 1, k + 1, k + 2) if 1 <= n <= eng + 2]
            r = var(str(k), chalg)
            if r: savollar.append({"savol": S["nechta"].format(e=e, k=e * k), "variantlar": r[0], "togri": r[1], "_sanoq": (e, k) in sanoq})
    rnd.shuffle(savollar)
    savollar.sort(key=lambda q: not q.pop("_sanoq", True))   # darsdagi aniq sanoqlar oldinda
    for i, q in enumerate(savollar):
        q["id"] = f"auto-{seed}-{i}"; q["izoh"] = ""; q["xatolar"] = {}; q["avto"] = True
    return savollar[:soni]

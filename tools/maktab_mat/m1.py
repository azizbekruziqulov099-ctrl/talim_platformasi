"""1-sinf matematika (yangi) — darslik mundarijasi + metodik modellar → Kabutar Miya.
Har dars: hayotiy vaziyat → tushuncha (model) + chizma → o'yin (bola o'zi bajaradi) → tabiiy savollar →
namunaviy misol (qadamma-qadam) → mashqlar → test. Sonlar dars o'rniga mos (10 gacha / 20 gacha / 100 gacha)."""
import json, random, re, sys
sys.path.insert(0, "/tmp/mm1")
import bob1   # avval yozilgan 7 ta «sonlargacha» darsi (xossalar, joylashish, shakllar, vaqt, guruhlar)

D = json.load(open("/tmp/m1/data.json", encoding="utf8"))
M = D["M"]
CASES = {c["id"]: c for c in D["C"]}

TUZAT = {"Q o‘shish hadlari": "Qo‘shish hadlari", "M uqaddim a": "Muqaddima", "Q avslar": "Qavslar", "Sonlarni a yirish": "Sonlarni ayirish",
         "Yaxlit s o n la r": "Yaxlit sonlar", "8 soni va raqam i": "8 soni va raqami", "Qavsli tarkibli ifod alar": "Qavsli tarkibli ifodalar"}


def toza(t):
    t = str(t or "").strip()
    t = TUZAT.get(t, t)
    t = re.sub(r"^\d\s?\d?\s?\.\s*", "", t)                       # «1 9 .1 dan 5 gacha» → «1 dan 5 gacha»
    t = re.sub(r"\bq o ?'?‘?sh ?ish\b", "qo‘shish", t, flags=re.I)
    t = t.replace("y o z ilis h i", "yozilishi").replace("qo‘s h is h", "qo‘shish").replace("q o 'sh ish", "qo‘shish")
    t = t.replace("'", "‘").replace("’", "’")
    t = re.sub(r"\s+", " ", t).strip()
    return t[:1].upper() + t[1:]


def model_savol(mid):
    """«Savol? Javob.» → (savol, javob)"""
    s = str(M[mid]["savol"] or "")
    i = s.rfind("?")
    return (s[: i + 1].strip(), s[i + 1:].strip().rstrip(".")) if i > 0 else (s, "")


def model_qatorlari(mid, oyin=None, sarl=None):
    m = M[mid]
    harakat = [re.sub(r"^\d+\.\s*", "", x).strip() for x in str(m["harakat"] or "").split("\n") if x.strip()]
    q, j = model_savol(mid)
    rows = [("tushuncha", "", sarl or m["tushuncha"], f"{m['nazariya']} [1] Masalan: {m['misol']}", f"{m['tushuncha']}\n{m['misol']}", "", "", "", "", "", "", "", "", "", "")]
    if oyin:
        rows.append(("tushuncha", "", "🎮 O‘zing bajar", "Endi o‘zing bajarib ko‘r. [1] Tugmalarni bos va nima bo‘lishini kuzat.", oyin, "", "", "", "", "", "", "", "", "", ""))
    if harakat:
        rows.append(("tushuncha", "", "Qadamma-qadam", " ".join(f"[{k + 1}] {h}." for k, h in enumerate(harakat[:4])), "\n".join(harakat[:4]), "", "", "", "", "", "",
                     "", "", "", ""))
    return rows


def rows_test(rng, savol, togri, xatolar, kod, sarl="Test"):
    xs = []
    for x in xatolar:
        if str(x) != str(togri) and str(x) not in xs:
            xs.append(str(x))
    k = 1
    while len(xs) < 3:
        c = str(int(togri) + k) if str(togri).lstrip("-").isdigit() else f"{togri}{k}"
        if c != str(togri) and c not in xs and not c.startswith("-"):
            xs.append(c)
        k = -k if k > 0 else -k + 1
    opts = [str(togri)] + xs[:3]
    rng.shuffle(opts)
    return ("test", kod, sarl, savol, "", "", "\n".join(f"{'ABCD'[i]}) {o}" for i, o in enumerate(opts)), "ABCD"[opts.index(str(togri))], "", "", "", "", "", "oson", "")


NARSALAR = [("olma", "🍎"), ("qalam", "✏️"), ("shar", "🎈"), ("konfet", "🍬"), ("kitob", "📘"), ("baliq", "🐟"), ("gul", "🌷"), ("yulduz", "⭐")]


def qoshish_mashq(rng, cap, n=8, ayir=False):
    out = []
    for _ in range(n):
        if ayir:
            a = rng.randint(2, cap); b = rng.randint(1, a - 1) if a > 1 else 0
            out.append((f"${a} - {b} = \\;?$", a - b, [a + b, a - b + 1, b]))
        else:
            a = rng.randint(1, cap - 1); b = rng.randint(1, cap - a)
            out.append((f"${a} + {b} = \\;?$", a + b, [a - b if a > b else a + b + 1, a + b - 1, a * b if a * b != a + b else a + b + 2]))
    return out


def masala_qatorlari(rng, cap, turi):
    """Hayotiy masalalar: butun/qism, orttirish/kamaytirish, taqqoslash."""
    R = []
    ism = ["Ali", "Malika", "Bekzod", "Dilnoza", "Sardor", "Gulnora"]
    for k in range(6):
        nom, bel = rng.choice(NARSALAR); i1, i2 = rng.sample(ism, 2)
        a = rng.randint(2, max(3, cap // 2)); b = rng.randint(1, max(2, cap // 2))
        if turi == "butun":
            matn, j, yech = f"{i1}da {a} ta {nom}, {i2}da {b} ta {nom} bor. Ikkalasida jami nechta {nom} bor?", a + b, f"Jami — qo‘shish: ${a} + {b} = {a + b}$"
        elif turi == "qism":
            matn, j, yech = f"Savatda {a + b} ta {nom} bor edi. {b} tasi olindi. Nechta qoldi?", a, f"Qism — ayirish: ${a + b} - {b} = {a}$"
        elif turi == "orttir":
            matn, j, yech = f"{i1}da {a} ta {nom} bor. {i2}da undan {b} ta ko‘p. {i2}da nechta {nom} bor?", a + b, f"«ta ko‘p» — qo‘shamiz: ${a} + {b} = {a + b}$"
        else:
            matn, j, yech = f"{i1}da {a + b} ta, {i2}da {a} ta {nom} bor. {i1}da nechta ko‘p?", b, f"Taqqoslash — ayiramiz: ${a + b} - {a} = {b}$"
        R.append(("masala", f"M{k + 1:02d}", f"Masala {k + 1}", f"{bel} {matn}", "", "", "", str(j), yech + f"\nJavob: {j}", "", "", "", "", "oson" if k < 3 else "o‘rta",
                  "Avval nima berilganini va nima so‘ralganini ayt. Keyin amalni tanla."))
    return R


def dars_yasa(i, nom, rng, cap):
    n = nom.lower()
    R = []
    mos = None
    # 1) avval yozilgan «sonlargacha» darslari
    for bn, _, rows in bob1.BOB:
        bnl = bn.split(". ", 1)[-1].lower()
        if bnl.split()[0] in n and any(w in n for w in bnl.split()[1:2] or [bnl]):
            mos = rows
            break
    if mos:
        out = []
        for r in mos:
            turi, kod, sarl, matn, doska, var, javob, yechim, sodda, boshqa, tek, mas, xato, qiy = r
            out.append((turi, kod, sarl, matn, doska, "", var, javob, yechim, sodda, boshqa, tek, xato, qiy, mas))
        if "taqqoslash" in n or "guruh" in n:
            out.insert(2, ("tushuncha", "", "🎮 O‘zing juftla", "Piyola va qoshiqlarni juftlab ko‘r. [1] Qaysi biri ko‘p?", "OYIN: juftla 5 3", "", "", "", "", "", "", "Piyolalar ko‘pmi yoki qoshiqlar? => piyolalar | qoshiqlar | teng", "", "", ""))
        if "sanog" in n:
            out.insert(2, ("tushuncha", "", "🎮 Sanab chiq", "Olmalarni bittadan bosib sana. [1] Oxirgi aytgan soning — jami.", "OYIN: sana 6 olma", "", "", "", "", "", "", "Olmalar nechta ekan? => 6 | 5 | 7", "", "", ""))
        return out
    # 2) «N soni va raqami», «10 soni»
    m = re.match(r"^(\d{1,2})\s+soni", nom)
    if m:
        N = int(m.group(1)); nomi, bel = NARSALAR[N % len(NARSALAR)]
        R.append(("kirish", "", f"🎯 {N} soni", f"Kabu bugun {N} ta {nomi} olib keldi. Keling, birga sanaymiz va {N} raqamini yozishni o‘rganamiz.", f"{bel * max(N, 0)}" if N else "∅ — bo‘sh savat", "", "", "", "", "", "",
                  f"Kabu nechta {nomi} olib keldi? => {N} | {N + 1} | {max(0, N - 1) if N > 1 else N + 2}", "", "", ""))
        if N == 0:
            R += model_qatorlari("N008", "OYIN: nur 3 -3 10")
        else:
            R += model_qatorlari("N001", f"OYIN: sana {N} {nomi}")
            if N >= 2:
                a = rng.randint(1, N - 1)
                R.append(("tushuncha", "", f"{N} ning tarkibi", f"{N} ni ikki qismga turlicha ajratish mumkin. [1] Masalan, {a} va {N - a}. Qismlar qo‘shilsa, yana {N} bo‘ladi.",
                          f"${N} = {a} + {N - a}$", "", "", "", "", "", "", f"{N} ning bir qismi {a} bo‘lsa, ikkinchisi nechta? => {N - a} | {N - a + 1} | {a}", "", "", ""))
        R.append(("tushuncha", "", "Son qatorida", f"Son qatorida {N} dan oldin {N - 1 if N else '—'} turadi, keyin {N + 1} keladi. [1] Keyingi son bittaga katta.",
                  f"OYIN: nur {max(0, N - 1)} 1 10", "", "", "", "", "", "", f"{N} dan keyin qaysi son keladi? => {N + 1} | {N - 1 if N else N + 2} | {N}", "", "", ""))
        for k in range(6):
            q = rng.randint(1, 10)
            R.append(("masala", f"M{k + 1:02d}", f"Sanash {k + 1}", f"{bel * q} — nechta?", "", "", "", str(q), f"Bittadan sanaymiz: {', '.join(map(str, range(1, q + 1)))}.\nJavob: {q}", "", "", "", "", "oson", "Har biriga bir marta tegib sana."))
        R.append(rows_test(rng, f"{N} dan keyin qaysi son keladi?", N + 1, [N - 1 if N else N + 2, N, N + 2], "T01"))
        R.append(rows_test(rng, f"Qaysi son {N} dan oldin keladi?", N - 1 if N else 1, [N + 1, N, N + 2], "T02"))
        R.append(rows_test(rng, f"{bel * N if N else '∅'} — nechta?", N, [N + 1, abs(N - 1), N + 2], "T03"))
        return R
    # 3) mavzu bo'yicha model va o'yin
    TUR = [
        (("sanog",), "N001", "OYIN: sana 7 olma", "sanoq"),
        (("o‘nlikdan o‘tib qo‘shish",), "N011", "OYIN: ramka 8 5", "qosh"),
        (("bo‘laklab ayirish", "o‘nlikdan ayirish", "o‘nlikdan o‘tib ayirish"), "N012", "OYIN: nur 13 -5 20", "ayir"),
        (("noma’lum", "tenglama"), "N030" if cap > 10 else "N013", "OYIN: tarozi 1 3 7", "tenglama"),
        (("ikki xonali sonlarni qo‘shish", "ko‘p komponentli"), "N020", "OYIN: nur 20 8 40", "qosh"),
        (("ikki xonali sonlarni ayirish",), "N021", "OYIN: nur 30 -8 40", "ayir"),
        (("guruhlash xossasi", "o‘rin almashtirish xossasi", "amallarning xossalari"), "N022", "OYIN: massiv 2 5", "qosh"),
        (("bog‘liqlik", "bog‘lanish"), "N009", "OYIN: nur 4 2 10", "qosh"),
        (("qo‘shish",), "N006", "OYIN: nur 3 2 10", "qosh"),
        (("ayirish",), "N007", "OYIN: nur 7 -3 10", "ayir"),
        (("ikki xonali sonlarni taqqoslash", "21 dan 100", "yaxlit", "11 dan 20", "sonlari", "o‘nlikda"), "N019" if cap > 20 else "N010", "OYIN: nur 10 5 20", "son"),
        (("taqqoslash", "natural", "1 dan", "tengsizlik", "tenglik"), "N004", "OYIN: juftla 6 4", "taqqos"),
        (("juft va toq",), "N002", "OYIN: juftla 4 4", "juft"),
        (("qavs", "ifoda"), "N029", "OYIN: tarozi 2 1 9", "ifoda"),
        (("butunni topish",), "N018", "OYIN: sana 7 olma", "butun"),
        (("qismlarni topish",), "N007", "OYIN: nur 9 -4 10", "qism"),
        (("orttirish", "kamaytirish"), "N036", "OYIN: nur 5 3 10", "orttir"),
        (("taqqoslashga doir",), "N002", "OYIN: juftla 7 4", "taqqosM"),
        (("masala",), "N018", "OYIN: juftla 5 2", "butun"),
        (("santimetr", "uzunlik", "kesmalarni o‘lchash", "detsimetr", "berilgan uzunlikda"), "N016" if "detsimetr" not in n else "N031", "OYIN: nur 0 6 10", "olchov"),
        (("perimetr", "siniq chiziqning uzunligi"), "N032", None, "perimetr"),
        (("to‘rtburchak", "kvadrat", "burchak"), "N033", None, "shakl"),
        (("nuqta", "chiziq", "kesma"), "N014", None, "shakl"),
        (("ko‘pburchak", "shakl", "simmetriya", "soha"), "N015", None, "shakl"),
        (("massa", "hajm", "kattalik"), "N031", None, "olchov"),
        (("rim",), None, None, "rim"),
        (("takrorlash", "misol va masalalar"), "N018", "OYIN: ramka 7 6", "aralash"),
    ]
    tanlov = next(((mid, oyin, tur) for kalit, mid, oyin, tur in TUR if any(k in n for k in kalit)), ("N018", None, "aralash"))
    mid, oyin, tur = tanlov
    kq, kj = model_savol(mid) if mid else ("", "")
    R.append(("kirish", "", f"🎯 {nom}", f"Bugungi mavzu: {nom}. Kabu avval sizga bitta savol beradi — o‘ylab javob bering, keyin birga tekshiramiz. [1] {M[mid]['misol'] if mid else ''}",
              M[mid]["misol"] if mid else "I, V, X", "", "", "", "", "", "", f"{kq} => {kj}" if kq and kj and tur not in ("juft",) else "", "", "", ""))
    if tur == "rim":
        R += [("tushuncha", "", "Rim raqamlari", "Qadimgi Rimda sonlar harflar bilan yozilgan. [1] I — bir, V — besh, X — o‘n. [2] Kichik raqam kattasidan keyin kelsa qo‘shiladi, oldin kelsa ayiriladi: VI — olti, IV — to‘rt.",
               "I = 1, V = 5, X = 10\nVI = 5 + 1 = 6, IV = 5 − 1 = 4", "", "", "", "", "", "", "IX qaysi son? => 9 | 11 | 10", "", "", "")]
        mas = [("VII", 7), ("III", 3), ("XI", 11), ("IV", 4), ("VIII", 8), ("XII", 12)]
        R += [("masala", f"M{k + 1:02d}", f"Rim raqami {k + 1}", f"{r} qaysi son?", "", "", "", str(v), f"Javob: {v}", "", "", "", "", "oson", "") for k, (r, v) in enumerate(mas)]
        R += [rows_test(rng, f"{r} qaysi son?", v, [v + 1, v - 1, v + 2], f"T{k + 1:02d}") for k, (r, v) in enumerate(mas[:5])]
        return R
    if tur == "juft":
        R += [("tushuncha", "", "Juft va toq", "Narsalarni ikkitadan juftlaymiz. [1] Hammasining jufti bo‘lsa — son juft: 2, 4, 6, 8, 10. [2] Bittasi jufti yo‘q qolsa — son toq: 1, 3, 5, 7, 9.",
               "Juft: 2, 4, 6, 8, 10\nToq: 1, 3, 5, 7, 9", "", "", "", "", "", "", "5 ta qalamni ikkitadan juftlasak, nechtasi ortib qoladi? => 1 | 0 | 2", "", "", ""),
              ("tushuncha", "", "🎮 O‘zing juftla", "Piyola va qoshiqlarni juftlab ko‘r. [1] Hammasining jufti bormi?", "OYIN: juftla 4 4", "", "", "", "", "", "", "4 juftmi? => ha | yo‘q", "", "", "")]
    elif tur == "sanoq":
        R += model_qatorlari(mid, oyin, nom)
    else:
        R += model_qatorlari(mid, oyin, nom)
    # namunaviy misol — darslikdagi yechim (bor bo'lsa)
    yid = None
    for c in D["C"]:
        if c["grade"] == 1 and c.get("steps") and len(c["problem"]) > 30 and tur in ("butun", "qism", "orttir", "taqqosM"):
            yid = c["id"]
            break
    if yid:
        c = CASES[yid]
        R.append(("misol", "N01", "Darslikdagi masala", c["problem"], "", "", "", "", "\n".join(c["steps"]), "", "", "", "", "o‘rta", ""))
    # mashqlar
    if tur in ("butun", "qism", "orttir", "taqqosM"):
        R += masala_qatorlari(rng, cap, {"butun": "butun", "qism": "qism", "orttir": "orttir", "taqqosM": "taqqos"}[tur])
        tests = qoshish_mashq(rng, cap, 6, ayir=tur in ("qism", "taqqosM"))
    elif tur == "tenglama":
        tests = []
        for k in range(8):
            a = rng.randint(1, cap - 2); x = rng.randint(1, cap - a)
            if k % 2:
                R.append(("masala", f"M{k + 1:02d}", f"Tenglama {k + 1}", f"$x + {a} = {x + a}$. $x$ nechaga teng?", "", "", "", str(x), f"Noma’lum qo‘shiluvchi = yig‘indi − ma’lum qo‘shiluvchi: ${x + a} - {a} = {x}$\nJavob: {x}", "", "", "", "", "o‘rta", "Tarozini esla: ikkala tomondan bir xil olib tashla."))
            else:
                R.append(("masala", f"M{k + 1:02d}", f"Tenglama {k + 1}", f"$x - {a} = {x}$. $x$ nechaga teng?", "", "", "", str(x + a), f"Noma’lum kamayuvchi = ayirma + ayriluvchi: ${x} + {a} = {x + a}$\nJavob: {x + a}", "", "", "", "", "o‘rta", ""))
            tests.append((f"$x + {a} = {x + a}$ bo‘lsa, $x$ = ?", x, [x + a, x + 1, a]))
    elif tur in ("son", "taqqos", "juft"):
        tests = []
        juftlar = rng.sample(range(1, min(cap, 20) + 1), 8)
        for k in range(8):
            a, b = rng.sample(range(1, cap + 1), 2)
            if tur == "juft":
                a = juftlar[k]
                R.append(("masala", f"M{k + 1:02d}", f"Juftmi? {k + 1}", f"{a} soni juftmi? (ha / yo‘q)", "", "", "", "ha" if a % 2 == 0 else "yo‘q", f"{a} ta narsani ikkitadan juftlasak, {'hammasining jufti bor' if a % 2 == 0 else 'bittasi ortib qoladi'}.\nJavob: {'ha' if a % 2 == 0 else 'yo‘q'}", "", "", "", "", "oson", "Ikkitadan juftlab ko‘r."))
                tests.append((f"Qaysi son juft?", 2 * rng.randint(1, cap // 2), [2 * rng.randint(0, cap // 2) + 1 for _ in range(3)]))
            else:
                katta = max(a, b)
                R.append(("masala", f"M{k + 1:02d}", f"Taqqosla {k + 1}", f"{a} va {b} — qaysi biri katta?", "", "", "", str(katta), f"Son qatorida {katta} o‘ngroqda turadi.\nJavob: {katta}", "", "", "", "", "oson", "Son qatorida qaysi biri o‘ngroqda?"))
                tests.append((f"Qaysi son katta: {a} yoki {b}?", katta, [min(a, b), a + b, abs(a - b)]))
    elif tur in ("perimetr", "shakl", "olchov"):
        tests = []
        for k in range(6):
            if tur == "perimetr":
                a, b = rng.randint(2, 9), rng.randint(2, 9)
                R.append(("masala", f"M{k + 1:02d}", f"Perimetr {k + 1}", f"To‘g‘ri to‘rtburchakning tomonlari {a} sm va {b} sm. Perimetri necha sm?", "", "", "", str(2 * (a + b)), f"Hamma tomonlar: ${a} + {b} + {a} + {b} = {2 * (a + b)}$ sm\nJavob: {2 * (a + b)}", "", "", "", "", "o‘rta", "To‘rtta tomonning hammasini qo‘sh."))
                tests.append((f"Tomonlari {a} sm va {b} sm bo‘lgan to‘g‘ri to‘rtburchak perimetri?", 2 * (a + b), [a + b, a * b, 2 * a + b]))
            elif tur == "olchov":
                d, s = rng.randint(1, 5), rng.randint(0, 9)
                R.append(("masala", f"M{k + 1:02d}", f"O‘lchov {k + 1}", f"{d} dm {s} sm — necha santimetr?", "", "", "", str(10 * d + s), f"1 dm = 10 sm: ${d} \\cdot 10 + {s} = {10 * d + s}$ sm\nJavob: {10 * d + s}", "", "", "", "", "o‘rta", "1 dm = 10 sm"))
                tests.append((f"{d} dm necha sm?", 10 * d, [d, d + 10, 100 * d]))
            else:
                shakl = rng.choice([("uchburchak", 3), ("to‘rtburchak", 4), ("beshburchak", 5), ("oltiburchak", 6)])
                R.append(("masala", f"M{k + 1:02d}", f"Shakl {k + 1}", f"{shakl[0].capitalize()}ning nechta burchagi bor?", "", "", "", str(shakl[1]), f"Nomida aytilgan: {shakl[1]} ta.\nJavob: {shakl[1]}", "", "", "", "", "oson", "Burchaklarini sanab chiq."))
                tests.append((f"{shakl[0].capitalize()}ning nechta tomoni bor?", shakl[1], [shakl[1] + 1, shakl[1] - 1, shakl[1] + 2]))
    elif tur == "sanoq":
        tests = []
        for k in range(8):
            nomi, bel = rng.choice(NARSALAR); q = rng.randint(2, cap if cap <= 10 else 10)
            R.append(("masala", f"M{k + 1:02d}", f"Sanash {k + 1}", f"{bel * q} — nechta {nomi}?", "", "", "", str(q), f"Bittadan sanaymiz: {', '.join(map(str, range(1, q + 1)))}.\nJavob: {q}", "", "", "", "", "oson", "Har biriga bir marta tegib sana."))
            tests.append((f"{bel * q} — nechta?", q, [q + 1, q - 1, q + 2]))
    else:   # qo'shish, ayirish, ifoda, aralash
        ayir = tur == "ayir"
        mashq = qoshish_mashq(rng, cap, 4) + qoshish_mashq(rng, cap, 4, ayir=True) if tur == "aralash" else qoshish_mashq(rng, cap, 8, ayir=ayir)
        for k, (q, j, xs) in enumerate(mashq):
            R.append(("masala", f"M{k + 1:02d}", f"Misol {k + 1}", q, "", "", "", str(j), f"Javob: {j}", "", "", "", "", "oson" if k < 4 else "o‘rta", "Son nurida yurib ko‘r yoki barmoq bilan sana."))
        tests = qoshish_mashq(rng, cap, 6, ayir=ayir)
    for k, (q, j, xs) in enumerate(tests[:6]):
        R.append(rows_test(rng, q, j, xs, f"T{k + 1:02d}"))
    R.append(("xulosa", "", "🌟 Bugun nimani o‘rgandik", f"{M[mid]['nazariya']}" if mid else "", M[mid]["tushuncha"] if mid else nom, "", "", "", "", "", "", "", "", "", ""))
    return R


def darslar():
    L = [x for x in D["L"] if x["sinf"] == "1"]
    out, sanoq = [], {}
    for i, x in enumerate(L):
        nom = toza(x["nom"])
        if nom.lower() == "muqaddima":
            continue
        sanoq[nom] = sanoq.get(nom, 0) + 1
        cap = 10 if i <= 40 else 20 if i <= 58 else 100
        out.append((nom if sanoq[nom] == 1 else f"{nom} ({sanoq[nom]}-dars)", nom, cap, x))
    return out

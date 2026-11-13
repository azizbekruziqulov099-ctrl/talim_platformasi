"""REV538: «⚡ Tez bellashuv» — yosh va mavzu tanlanadi, savollar shu zahoti tuziladi (bazada test bo'lishi shart emas).
Har savol: (matn, [4 variant], to'g'ri indeks, izoh). Matn oddiy (formulasiz) — bellashuv ekranida to'g'ri ko'rinadi."""
import random

BANDLAR = [("bogcha", "Bog‘cha (4–7 yosh)"), ("1-4", "1–4-sinf"), ("5-8", "5–8-sinf"), ("9-11", "9–11-sinf")]
MAVZULAR = {
    "bogcha": [("sanash", "🔢 Sanash"), ("qoshish", "➕ Rasmli qo‘shish"), ("keyingi", "➡️ Keyingi son"), ("rang_shakl", "🎨 Rang va shakl")],
    "1-4": [("hisob", "➕ Tez hisob"), ("jadval", "✖️ Ko‘paytirish jadvali"), ("ketma", "🔗 Ketma-ketlik"), ("imlo", "✍️ Imlo"), ("poytaxt", "🌍 Poytaxtlar")],
    "5-8": [("hisob", "🧮 Tez hisob"), ("tenglama", "⚖️ Tenglama"), ("foiz", "％ Foiz va kasr"), ("ketma", "🔗 Ketma-ketlik"), ("imlo", "✍️ Imlo"), ("poytaxt", "🌍 Poytaxtlar"), ("davriy", "🧪 Kimyoviy elementlar")],
    "9-11": [("daraja", "√ Daraja va ildiz"), ("tenglama", "⚖️ Tenglamalar"), ("ketma", "🔗 Ketma-ketlik"), ("imlo", "✍️ Imlo"), ("poytaxt", "🌍 Poytaxtlar"), ("davriy", "🧪 Kimyoviy elementlar")],
}
for _b in MAVZULAR:
    MAVZULAR[_b].append(("aralash", "🎲 Aralash"))

NARSA = [("🍎", "olma"), ("⭐", "yulduz"), ("🐟", "baliq"), ("🎈", "shar"), ("🌷", "gul"), ("🚗", "mashina")]
RANG = [("🔴", "qizil"), ("🟢", "yashil"), ("🔵", "ko‘k"), ("🟡", "sariq"), ("🟠", "to‘q sariq"), ("🟣", "binafsha")]
SHAKL = [("⚪", "doira"), ("🔺", "uchburchak"), ("⬛", "kvadrat"), ("⭐", "yulduz"), ("❤️", "yurak")]
POYTAXT = [("O‘zbekiston", "Toshkent", 0), ("Qozog‘iston", "Ostona", 0), ("Qirg‘iziston", "Bishkek", 0), ("Tojikiston", "Dushanbe", 0), ("Turkmaniston", "Ashxobod", 0), ("Rossiya", "Moskva", 0),
           ("Xitoy", "Pekin", 0), ("Turkiya", "Anqara", 0), ("AQSH", "Vashington", 0), ("Buyuk Britaniya", "London", 0), ("Fransiya", "Parij", 0), ("Germaniya", "Berlin", 0), ("Yaponiya", "Tokio", 0),
           ("Hindiston", "Nyu-Dehli", 0), ("Italiya", "Rim", 0), ("Misr", "Qohira", 0), ("Afg‘oniston", "Kobul", 1), ("Eron", "Tehron", 1), ("Pokiston", "Islomobod", 1), ("Ozarbayjon", "Boku", 1),
           ("Ispaniya", "Madrid", 1), ("Janubiy Koreya", "Seul", 1), ("Kanada", "Ottava", 1), ("Avstraliya", "Kanberra", 1), ("Braziliya", "Braziliya", 1), ("Gretsiya", "Afina", 1), ("Polsha", "Varshava", 1),
           ("Shveytsariya", "Bern", 2), ("Niderlandiya", "Amsterdam", 2), ("Shvetsiya", "Stokgolm", 2), ("Norvegiya", "Oslo", 2), ("Portugaliya", "Lissabon", 2), ("Avstriya", "Vena", 2),
           ("Argentina", "Buenos-Ayres", 2), ("Tailand", "Bangkok", 2), ("Vyetnam", "Xanoy", 2), ("Yangi Zelandiya", "Vellington", 2), ("Keniya", "Nayrobi", 2)]
ELEMENT = [("H", "Vodorod"), ("He", "Geliy"), ("Li", "Litiy"), ("Be", "Berilliy"), ("B", "Bor"), ("C", "Uglerod"), ("N", "Azot"), ("O", "Kislorod"), ("F", "Ftor"), ("Ne", "Neon"), ("Na", "Natriy"), ("Mg", "Magniy"),
           ("Al", "Alyuminiy"), ("Si", "Kremniy"), ("P", "Fosfor"), ("S", "Oltingugurt"), ("Cl", "Xlor"), ("Ar", "Argon"), ("K", "Kaliy"), ("Ca", "Kalsiy"), ("Fe", "Temir"), ("Cu", "Mis"), ("Zn", "Rux"), ("Ag", "Kumush"),
           ("Au", "Oltin"), ("Hg", "Simob"), ("Pb", "Qo‘rg‘oshin"), ("Sn", "Qalay")]
IMLO = [[("havo", "xavo"), ("shahar", "shaxar"), ("hafta", "xafta"), ("xona", "hona"), ("xat", "hat"), ("hamma", "xamma"), ("bahor", "baxor"), ("kitob", "kitop"), ("maktab", "maktap"), ("daraxt", "daraxd"), ("tog‘", "tog"), ("o‘quvchi", "oquvchi")],
        [("ma’no", "mano"), ("san’at", "sanat"), ("e’tibor", "etibor"), ("a’lo", "alo"), ("ta’lim", "talim"), ("tashakkur", "tashakur"), ("muvaffaqiyat", "muvafaqiyat"), ("tabassum", "tabasum"), ("rahmat", "raxmat"), ("mehmon", "mexmon"), ("xursand", "hursand"), ("muhabbat", "muxabbat")],
        [("mas’uliyat", "ma’suliyat"), ("mutaxassis", "mutahassis"), ("taraqqiyot", "taraqiyot"), ("tafakkur", "tafakur"), ("tashabbus", "tashabus"), ("mustahkam", "mustaxkam"), ("axborot", "ahborot"), ("ixtiro", "ihtiro"), ("an’ana", "anana"), ("murakkab", "murakab"), ("mahorat", "maxorat"), ("ehtirom", "extirom")]]


def _var(r, togri, xatolar):
    """To'g'ri javob + 3 ta har xil xato → aralashtirilgan 4 variant va to'g'ri indeks."""
    vs = [str(togri)]
    for x in xatolar:
        if str(x) not in vs:
            vs.append(str(x))
        if len(vs) == 4:
            break
    k = 1
    while len(vs) < 4:   # yetmasa — yaqin sonlar bilan to'ldiramiz
        try:
            n = int(str(togri).replace(" ", "")) + k
        except ValueError:
            n = f"{togri} {k}"
        if str(n) not in vs:
            vs.append(str(n))
        k = -k if k > 0 else -k + 1
    r.shuffle(vs)
    return vs, vs.index(str(togri))


def _sonli(r, matn, javob, izoh="", yaqin=False):
    # yaqin=True (bog'cha): faqat qo'shni sonlar — «14» kabi uzoq variant kichkintoyni chalg'itadi
    xato = [javob + 1, javob - 1, javob + 2, javob - 2, javob + 3] if yaqin else [javob + 1, javob - 1, javob + 10, javob - 10, javob + 2, javob * 2]
    r.shuffle(xato)
    vs, i = _var(r, javob, [x for x in xato if x != javob and (javob < 0 or x >= 0)])
    return matn, vs, i, izoh


def g_sanash(r, b):
    e, nom = r.choice(NARSA); n = r.randint(2, 9)
    return _sonli(r, f"{e * n}  Nechta {nom}?", n, yaqin=True)


def g_qoshish(r, b):
    e, nom = r.choice(NARSA); a, c = r.randint(1, 5), r.randint(1, 4)
    return _sonli(r, f"{e * a}  +  {e * c}  Hammasi nechta?", a + c, yaqin=True)


def g_keyingi(r, b):
    n = r.randint(1, 18); oldingi = r.random() < 0.3 and n > 1
    return _sonli(r, f"{n} dan {'oldin' if oldingi else 'keyin'} qaysi son keladi?", n - 1 if oldingi else n + 1, yaqin=True)


def g_rang_shakl(r, b):
    royxat = r.choice([RANG, SHAKL]); t = r.choice(royxat); bosh = r.sample([x for x in royxat if x != t], 3)
    vs, i = _var(r, t[0], [x[0] for x in bosh])
    return f"Qaysi biri {t[1]}?", vs, i, f"{t[0]} — {t[1]}"


def g_hisob(r, b):
    if b == "1-4":
        tur = r.choice("+-")
        a, c = (r.randint(11, 79), r.randint(4, 19))
        return _sonli(r, f"{a} {tur} {c} = ?", a + c if tur == "+" else a - c)
    if b == "5-8":
        tur = r.choice(["+", "-", "*", "manfiy"])
        if tur == "*":
            a, c = r.randint(11, 25), r.randint(3, 9); return _sonli(r, f"{a} · {c} = ?", a * c)
        if tur == "manfiy":
            a, c = r.randint(-20, -2), r.randint(3, 30); return _sonli(r, f"{a} + {c} = ?", a + c)
        a, c = r.randint(120, 890), r.randint(25, 110); return _sonli(r, f"{a} {tur} {c} = ?", a + c if tur == "+" else a - c)
    a, c = r.randint(12, 35), r.randint(11, 19)
    return _sonli(r, f"{a} · {c} = ?", a * c)


def g_jadval(r, b):
    a, c = r.randint(2, 9), r.randint(2, 9)
    if r.random() < 0.35:
        return _sonli(r, f"{a * c} : {a} = ?", c, f"{a} · {c} = {a * c}")
    return _sonli(r, f"{a} · {c} = ?", a * c)


def g_ketma(r, b):
    a, d = r.randint(1, 9), r.randint(2, 7 if b != "1-4" else 5)
    tur = r.choice(["ar", "ar", "geo"] if b == "1-4" else ["ar", "geo", "kv", "fib", "osh"])
    if tur == "ar":
        h = [a + i * d for i in range(5)]; izoh = f"Har safar {d} qo‘shiladi"
    elif tur == "geo":
        q = 2 if b == "1-4" else r.choice([2, 3]); h = [a * q ** i for i in range(5)]; izoh = f"Har safar {q} ga ko‘paytiriladi"
    elif tur == "kv":
        h = [(a + i) ** 2 for i in range(5)]; izoh = "Ketma-ket sonlarning kvadratlari"
    elif tur == "fib":
        h = [a, a + d]
        while len(h) < 5:
            h.append(h[-1] + h[-2])
        izoh = "Har had oldingi ikkitasining yig‘indisi"
    else:
        h = [a]
        for i in range(1, 5):
            h.append(h[-1] + i)
        izoh = "Qo‘shiladigan son har safar 1 ga oshadi"
    m, vs, i, _ = _sonli(r, ", ".join(map(str, h[:4])) + ", ?", h[4])
    return m, vs, i, izoh


def g_tenglama(r, b):
    x = r.randint(2, 12) if b == "5-8" else r.randint(-6, 9) or 3
    a, c = r.randint(2, 7), r.randint(1, 15)
    if b == "9-11" and r.random() < 0.5:
        p, q = sorted([r.randint(1, 7), r.randint(2, 9)])
        if p == q:
            q += 1
        return _sonli(r, f"x² − {p + q}x + {p * q} = 0. Katta ildiz?", q, f"Ildizlar: {p} va {q}")
    return _sonli(r, f"{a}x + {c} = {a * x + c}.  x = ?", x)


def g_foiz(r, b):
    if r.random() < 0.5:
        p, n = r.choice([10, 20, 25, 50, 75]), r.choice([40, 80, 120, 200, 240, 360])
        return _sonli(r, f"{n} ning {p}% i nechaga teng?", n * p // 100)
    m = r.choice([2, 4, 5, 10]); s = r.randint(1, m - 1); n = m * r.randint(3, 12)
    return _sonli(r, f"{n} ning {s}/{m} qismi nechaga teng?", n // m * s)


def g_daraja(r, b):
    tur = r.choice(["kv", "ildiz", "dar", "log"])
    if tur == "kv":
        n = r.randint(11, 25); return _sonli(r, f"{n}² = ?", n * n)
    if tur == "ildiz":
        n = r.randint(11, 30); return _sonli(r, f"√{n * n} = ?", n)
    if tur == "dar":
        a, n = r.choice([2, 3, 5]), r.randint(3, 6); return _sonli(r, f"{a} ning {n}-darajasi = ?", a ** n)
    a, n = r.choice([2, 3, 5]), r.randint(2, 5)
    return _sonli(r, f"log asosi {a} bo‘yicha {a ** n} = ?", n, f"{a} ning {n}-darajasi {a ** n}")


def g_imlo(r, b):
    d = {"1-4": 0, "5-8": 1, "9-11": 2}.get(b, 0); t, x = r.choice(IMLO[d])
    boshqa = [p[1] for p in r.sample([p for p in IMLO[d] if p[0] != t], 2)]
    vs, i = _var(r, t, [x] + boshqa)
    return "Qaysi so‘z TO‘G‘RI yozilgan?", vs, i, f"To‘g‘risi: {t}"


def g_poytaxt(r, b):
    d = {"1-4": 0, "5-8": 1, "9-11": 2}.get(b, 0); hovuz = [p for p in POYTAXT if p[2] <= d]
    t = r.choice([p for p in hovuz if p[2] == d] or hovuz); teskari = r.random() < 0.4
    bosh = r.sample([p for p in hovuz if p != t], 3)
    vs, i = _var(r, t[0] if teskari else t[1], [p[0] if teskari else p[1] for p in bosh])
    return (f"{t[1]} — qaysi davlat poytaxti?" if teskari else f"{t[0]} poytaxti qaysi shahar?"), vs, i, f"{t[0]} — {t[1]}"


def g_davriy(r, b):
    hovuz = ELEMENT[:20] if b == "5-8" else ELEMENT; t = r.choice(hovuz); teskari = r.random() < 0.5
    bosh = r.sample([e for e in hovuz if e != t], 3)
    vs, i = _var(r, t[0] if teskari else t[1], [e[0] if teskari else e[1] for e in bosh])
    return (f"{t[1]} elementining kimyoviy belgisi?" if teskari else f"«{t[0]}» — qaysi element belgisi?"), vs, i, f"{t[0]} — {t[1]}"


GEN = {"sanash": g_sanash, "qoshish": g_qoshish, "keyingi": g_keyingi, "rang_shakl": g_rang_shakl, "hisob": g_hisob, "jadval": g_jadval, "ketma": g_ketma, "tenglama": g_tenglama,
       "foiz": g_foiz, "daraja": g_daraja, "imlo": g_imlo, "poytaxt": g_poytaxt, "davriy": g_davriy}


def band_aniqla(sinf: str = "", bola: bool = False) -> str:
    import re
    if bola or re.search(r"yosh|bog|mtt", str(sinf or "").lower()):
        return "bogcha"
    m = re.search(r"\d{1,2}", str(sinf or "")); n = int(m.group(0)) if m else 0
    return "1-4" if 1 <= n <= 4 else "9-11" if n >= 9 else "5-8"


def savollar(band: str, mavzu: str, soni: int, urug=None):
    """→ generated_tests qatoriga o'xshash lug'atlar ro'yxati (id — manfiy tartib raqami). Takror savol bo'lmaydi."""
    r = random.Random(urug); band = band if band in MAVZULAR else "5-8"
    kalitlar = [k for k, _ in MAVZULAR[band] if k != "aralash"]
    if mavzu not in kalitlar and mavzu != "aralash":
        mavzu = kalitlar[0]
    out, kor, urin = [], set(), 0
    while len(out) < soni and urin < soni * 30:
        urin += 1
        k = r.choice(kalitlar) if mavzu == "aralash" else mavzu
        matn, vs, i, izoh = GEN[k](r, band)
        kal = f"{matn}|{vs[i]}"   # bir xil matnli savollar (imlo) javobi bilan farqlanadi
        if kal in kor or len(set(vs)) != 4:
            continue
        kor.add(kal)
        out.append({"id": -(len(out) + 1), "question": matn, "option_a": vs[0], "option_b": vs[1], "option_c": vs[2], "option_d": vs[3], "correct_answer": "ABCD"[i], "explanation": izoh})
    return out

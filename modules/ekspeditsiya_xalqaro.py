"""REV463: «🌍 Xalqaro ekspeditsiya» — PISA uslubidagi hayotiy masalalar. Tur nomi «kontekst:daraja» (daraja 1–6).
Daraja oshgan sari: qadamlar soni ko'payadi, ma'lumot jadvaldan o'qiladi, yaxlitlash/taqqoslash/asoslash kerak bo'ladi.
Har kontekstning rasmi bor (Azizjon yuborgan xalqaro_* va sahna_* rasmlari)."""
import math

SAHNA = {"chipta": "xalqaro_chipta", "masshtab": "xalqaro_xarita_masshtab", "harorat": "xalqaro_grafik_harorat", "retsept": "xalqaro_retsept",
         "quyosh": "xalqaro_quyosh_paneli", "suv": "xalqaro_tomchi", "velosiped": "xalqaro_velosiped_ijara", "piramida": "xalqaro_piramida",
         "aholi": "xalqaro_aholi", "tarif": "sahna_telefon_tarif", "poyezd": "sahna_poyezd", "omonat": "sahna_bank", "xalta": "sahna_lotereya",
         "sport": "sahna_sport", "plitka": "sahna_qurilish", "chegirma": "sahna_dokon", "hovuz": "sahna_suv_hovuz", "ob_havo": "sahna_ob_havo"}
NOMI = {"chipta": "Chipta yoki abonement", "masshtab": "Xarita masshtabi", "harorat": "Harorat jadvali", "retsept": "Retsept va porsiya", "quyosh": "Quyosh paneli",
        "suv": "Tomayotgan jo‘mrak", "velosiped": "Velosiped ijarasi", "piramida": "Qutilar piramidasi", "aholi": "Aholi va foiz", "tarif": "Mobil tarif",
        "poyezd": "Poyezd jadvali", "omonat": "Bank omonati", "xalta": "Xaltadagi sharlar", "sport": "Yugurish tezligi", "plitka": "Plitka yotqizish",
        "chegirma": "Qaysi aksiya foydali", "hovuz": "Hovuzni to‘ldirish", "ob_havo": "Ob-havo ehtimoli"}


def _f(x):
    x = round(x, 2)
    return str(int(x)) if x == int(x) else str(x).replace(".", ",")


def gen_xb(tur, rng):
    """→ (savol, javob, yechim, xato_variantlar)"""
    kontekst, _, d = str(tur).partition(":")
    L = int(d or 1)
    r = rng.randint
    if kontekst == "chipta":
        bir, oy = rng.choice([1400, 1500, 1700, 2000]), rng.choice([60000, 70000, 80000])
        if L <= 2:
            n = r(5, 15)
            return (f"Bir martalik avtobus chiptasi {bir} so‘m. Ali bir haftada {n} marta yuradi. U chiptalarga qancha to‘laydi?", bir * n,
                    f"${bir} \\cdot {n} = {bir * n}$ so‘m", [bir + n, bir * (n - 1), bir * n * 2])
        chegara = math.floor(oy / bir) + 1
        return (f"Bir martalik chipta {bir} so‘m, oylik abonement {oy} so‘m (cheksiz yurish). Oyiga kamida necha marta yurganda abonement arzonroq bo‘ladi?",
                chegara, f"${oy} : {bir} \\approx {_f(oy / bir)}$. Ko‘pi bilan {chegara - 1} marta yursa chipta arzon yoki teng, {chegara} martadan boshlab abonement arzon.\nJavob: {chegara}",
                [chegara - 1, round(oy / bir), chegara + 5])
    if kontekst == "masshtab":
        m = rng.choice([10000, 25000, 50000, 100000]); sm = r(2, 12) + (rng.choice([0, 0.5]) if L >= 3 else 0)
        km = sm * m / 100000
        if L >= 4:
            v = rng.choice([4, 5]); t = km / v * 60
            return (f"Xarita masshtabi 1:{m}. Xaritada maktab bilan bog‘ orasi {_f(sm)} sm. Soatiga {v} km tezlikda yursangiz, necha daqiqada yetib borasiz?",
                    _f(t), f"Haqiqiy masofa: ${_f(sm)} \\cdot {m} = {_f(sm * m)}$ sm $= {_f(km)}$ km. Vaqt: ${_f(km)} : {v} \\cdot 60 = {_f(t)}$ daqiqa",
                    [_f(km * 60), _f(t / 60), _f(t * 2)])
        return (f"Xarita masshtabi 1:{m}. Xaritada ikki shahar orasi {_f(sm)} sm. Haqiqiy masofa necha km?", _f(km),
                f"${_f(sm)}$ sm $\\cdot {m} = {_f(sm * m)}$ sm $= {_f(km)}$ km (1 km = 100 000 sm)", [_f(km * 10), _f(km / 10), _f(sm * m / 1000)])
    if kontekst in ("harorat", "ob_havo"):
        kunlar = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]
        t = [r(-6, 12) for _ in range(7)]
        jadval = " · ".join(f"{k}: {x}°" for k, x in zip(kunlar, t))
        if L <= 2:
            return (f"Bir haftalik harorat: {jadval}. Eng iliq va eng sovuq kun orasidagi farq necha gradus?", max(t) - min(t),
                    f"${max(t)} - ({min(t)}) = {max(t) - min(t)}$°", [max(t) + min(t), max(t), abs(max(t)) - abs(min(t))])
        while sum(t) % 7:
            t[0] += 1
        jadval = " · ".join(f"{k}: {x}°" for k, x in zip(kunlar, t))
        if L >= 4:
            past = sum(1 for x in t if x < sum(t) // 7)
            return (f"Harorat: {jadval}. Haftaning o‘rtacha haroratidan sovuqroq bo‘lgan kunlar nechta?", past,
                    f"O‘rtacha: ${sum(t)} : 7 = {sum(t) // 7}$°. Undan past kunlar: {past} ta", [7 - past, past + 1, sum(t) // 7])
        return (f"Harorat: {jadval}. Haftaning o‘rtacha harorati necha gradus?", sum(t) // 7,
                f"Yig‘indi: ${sum(t)}$, kunlar: 7; ${sum(t)} : 7 = {sum(t) // 7}$°", [sum(t), (max(t) + min(t)) // 2 if (max(t) + min(t)) // 2 != sum(t) // 7 else sum(t) // 7 + 1, sum(t) // 7 + 2])
    if kontekst == "retsept":
        kishi, un = 4, rng.choice([200, 300, 400, 600])
        yangi = rng.choice([6, 10, 2]) if L >= 3 else rng.choice([8, 12])
        j = un * yangi / kishi
        if L >= 5:
            bor = int(j * rng.choice([0.6, 0.75]))
            k = math.floor(bor * kishi / un)
            return (f"Bulochka retsepti {kishi} kishiga {un} g un talab qiladi. Uyda {bor} g un bor. Ko‘pi bilan necha kishiga yetadi?", k,
                    f"1 kishiga ${un} : {kishi} = {_f(un / kishi)}$ g. ${bor} : {_f(un / kishi)} \\approx {_f(bor / (un / kishi))}$ → butun kishilar: {k}", [k + 1, round(bor / (un / kishi)) + 1, kishi])
        return (f"Retsept {kishi} kishilik: {un} g un. {yangi} kishiga necha gramm un kerak?", _f(j), f"${un} : {kishi} \\cdot {yangi} = {_f(j)}$ g",
                [_f(un + yangi), _f(un * yangi), _f(un / yangi * kishi)])
    if kontekst == "quyosh":
        kun = rng.choice([4, 5, 6, 8]); oy = kun * 30 * (rng.choice([1.25, 1.6, 2, 2.5]) if L >= 4 else 1)   # ehtiyoj ishlab chiqarishdan katta — foiz 100 dan kichik
        if L >= 4:
            foiz = round(kun * 30 / oy * 100)
            return (f"Quyosh paneli kuniga {kun} kVt·soat elektr beradi. Oila oyiga {_f(oy)} kVt·soat ishlatadi. Panel oilaning ehtiyojini necha foiz qoplaydi? (30 kun)",
                    foiz, f"Oyiga: ${kun} \\cdot 30 = {kun * 30}$. ${kun * 30} : {_f(oy)} \\cdot 100\\% = {foiz}\\%$",
                    [round(oy / (kun * 30) * 100), kun * 30, foiz + 10])
        return (f"Quyosh paneli kuniga {kun} kVt·soat beradi. 30 kunda qancha beradi?", kun * 30, f"${kun} \\cdot 30 = {kun * 30}$ kVt·soat", [kun + 30, kun * 7, kun * 300])
    if kontekst == "suv":
        tomchi_s = rng.choice([1, 2]); ml20 = 20
        litr = 86400 / tomchi_s / ml20 / 1000
        return (f"Jo‘mrakdan {'har soniyada' if tomchi_s == 1 else 'har 2 soniyada'} bir tomchi oqadi; 20 tomchi = 1 ml. Bir kunda (86 400 soniya) necha litr suv isrof bo‘ladi?",
                _f(litr), f"Tomchilar: ${86400 // tomchi_s}$; ml: ${86400 // tomchi_s} : 20 = {86400 // tomchi_s // 20}$; litr: ${_f(litr)}$",
                [_f(litr * 1000), _f(litr * 20), _f(86400 / tomchi_s / 1000)])
    if kontekst == "velosiped":
        a0, a1 = rng.choice([(5000, 4000), (8000, 3000), (0, 6000)]); b1 = a1 + rng.choice([1000, 2000])
        if L >= 4 and a0:
            t = math.ceil(a0 / (b1 - a1))
            return (f"«Tez» ijarasi: {a0} so‘m kirish + soatiga {a1} so‘m. «Oson» ijarasi: kirish yo‘q, soatiga {b1} so‘m. Necha soatdan boshlab «Tez» arzonroq bo‘ladi?",
                    t + (1 if a0 % (b1 - a1) == 0 else 0), f"Har soatda «Tez» {b1 - a1} so‘m arzon; kirish puli ${a0} : {b1 - a1} = {_f(a0 / (b1 - a1))}$ soatda qoplanadi.\nJavob: {t + (1 if a0 % (b1 - a1) == 0 else 0)}",
                    [t - 1 if t > 1 else t + 2, round(a0 / a1), t + 3])
        h = r(2, 6)
        return (f"Velosiped ijarasi: {a0} so‘m kirish va soatiga {a1} so‘m. {h} soatga necha so‘m?", a0 + a1 * h, f"${a0} + {a1} \\cdot {h} = {a0 + a1 * h}$", [(a0 + a1) * h, a1 * h, a0 + a1 * (h + 1)])
    if kontekst == "piramida":
        n = r(4, 9) if L <= 3 else r(10, 20)
        return (f"Qutilar piramida qilib taxlanadi: eng yuqorida 1 ta, keyingi qatorda 2 ta, keyin 3 ta… {n} qatorli piramidada nechta quti bor?", n * (n + 1) // 2,
                f"$1 + 2 + … + {n} = \\frac{{{n} \\cdot {n + 1}}}{{2}} = {n * (n + 1) // 2}$", [n * n, n * (n - 1) // 2, n * (n + 1)])
    if kontekst == "aholi":
        jami = rng.choice([120000, 250000, 480000, 600000]); f1, f2 = rng.choice([(25, 40), (20, 35), (30, 45)])
        if L >= 3:
            return (f"Shaharda {jami} kishi yashaydi: {f1}% i bolalar, {f2}% i ishlaydiganlar, qolganlari nafaqaxo‘rlar. Nafaqaxo‘rlar nechta?", jami * (100 - f1 - f2) // 100,
                    f"$100 - {f1} - {f2} = {100 - f1 - f2}\\%$; ${jami} \\cdot {100 - f1 - f2} : 100 = {jami * (100 - f1 - f2) // 100}$", [jami * f1 // 100, jami * f2 // 100, jami * (f1 + f2) // 100])
        return (f"Shaharda {jami} kishi yashaydi, {f1}% i bolalar. Bolalar nechta?", jami * f1 // 100, f"${jami} \\cdot {f1} : 100 = {jami * f1 // 100}$", [jami // f1, jami * f1 // 10, jami * (100 - f1) // 100])
    if kontekst == "tarif":
        a, ga, b, gb, kerak = 30000, 10, 45000, 20, rng.choice([8, 12, 15, 18])
        qoshim = 4000
        na = a + max(0, kerak - ga) * qoshim; nb = b + max(0, kerak - gb) * qoshim
        return (f"«A» tarif: {a} so‘m, {ga} GB; «B» tarif: {b} so‘m, {gb} GB. Ortiqcha har 1 GB — {qoshim} so‘m. Oyiga {kerak} GB ishlatadigan odamga qaysi tarif arzon? (A yoki B)",
                "A" if na < nb else "B" if nb < na else "teng", f"A: ${a} + {max(0, kerak - ga)} \\cdot {qoshim} = {na}$; B: ${nb}$.\nJavob: {'A' if na < nb else 'B' if nb < na else 'teng'}", ["B" if na < nb else "A", "teng"])
    if kontekst == "poyezd":
        s, m = r(6, 20), rng.choice([0, 15, 30, 45]); dur = r(70, 320)
        es, em = divmod(s * 60 + m + dur, 60)
        return (f"Poyezd {s:02d}:{m:02d} da jo‘naydi va yo‘lda {dur // 60} soat {dur % 60} daqiqa yuradi. Qachon yetib keladi?", f"{es % 24:02d}:{em:02d}",
                f"${s}:{m:02d} + {dur // 60}$ soat ${dur % 60}$ daqiqa $= {es % 24:02d}:{em:02d}$", [f"{(es + 1) % 24:02d}:{em:02d}", f"{(s + dur // 60) % 24:02d}:{(m + dur) % 60:02d}", f"{es % 24:02d}:{(em + 10) % 60:02d}"])
    if kontekst == "omonat":
        p, f, y = rng.choice([1000000, 2000000, 5000000]), rng.choice([10, 12, 20]), r(1, 3) if L <= 3 else r(2, 3)
        if L >= 5:
            j = round(p * (1 + f / 100) ** y)
            return (f"Bankka {p} so‘m qo‘yildi, yillik {f}% (foiz har yili omonatga qo‘shiladi). {y} yildan keyin omonat necha so‘m bo‘ladi?", j,
                    f"$${p} \\cdot (1 + {f / 100:g})^{{{y}}} = {j}$$", [p + p * f * y // 100, round(p * (1 + f / 100) ** (y - 1)), p * f * y // 100])
        return (f"Bankka {p} so‘m yillik {f}% bilan qo‘yildi (oddiy foiz). {y} yilda qancha foyda keladi?", p * f * y // 100, f"${p} \\cdot {f}\\% \\cdot {y} = {p * f * y // 100}$",
                [p * f // 100, p + p * f * y // 100, p * f * y // 10])
    if kontekst == "xalta":
        q, k, s = r(2, 8), r(2, 8), r(1, 6); n = q + k + s
        from fractions import Fraction
        if L >= 4:
            v = Fraction(q, n) * Fraction(q - 1, n - 1)
            return (f"Xaltada {q} ta qizil, {k} ta ko‘k va {s} ta sariq shar bor. Ketma-ket 2 ta shar olinadi (qaytarilmaydi). Ikkalasi qizil bo‘lish ehtimoli?", f"{v.numerator}/{v.denominator}",
                    f"$\\frac{{{q}}}{{{n}}} \\cdot \\frac{{{q - 1}}}{{{n - 1}}} = {v.numerator}/{v.denominator}$", [f"{(Fraction(q, n) ** 2).numerator}/{(Fraction(q, n) ** 2).denominator}", f"{q}/{n}", f"{2 * q}/{n}"])
        v = Fraction(q, n)
        return (f"Xaltada {q} ta qizil, {k} ta ko‘k va {s} ta sariq shar bor. Qarab o‘tirmay olingan shar qizil bo‘lish ehtimoli?", f"{v.numerator}/{v.denominator}",
                f"$\\frac{{{q}}}{{{n}}}$ — qisqartirilgan: {v.numerator}/{v.denominator}", [f"{q}/{k + s}", f"1/{n}", f"{k}/{n}"])
    if kontekst == "sport":
        m, mins = rng.choice([400, 800, 1500, 3000]), r(2, 15)
        v = m / mins / 1000 * 60
        return (f"Sportchi {m} m ni {mins} daqiqada yugurdi. Uning o‘rtacha tezligi soatiga necha km? (0,1 gacha)", f"{round(v, 1):g}".replace(".", ","),
                f"${m}$ m $= {m / 1000:g}$ km, ${mins}$ daqiqa $= {_f(mins / 60)}$ soat; tezlik ${m / 1000:g} : {_f(mins / 60)} \\approx {round(v, 1):g}$",
                [f"{round(m / mins, 1):g}".replace(".", ","), f"{round(v * 10, 1):g}".replace(".", ","), f"{round(v / 2, 1):g}".replace(".", ",")])
    if kontekst == "plitka":
        a, b, p = r(3, 6), r(2, 5), rng.choice([0.3, 0.4, 0.5])
        soni = math.ceil(a / p) * math.ceil(b / p)
        if L >= 4:
            quti = rng.choice([10, 12, 20]); q = math.ceil(soni / quti)
            return (f"Xona {a} m × {b} m. Plitka {int(p * 100)}×{int(p * 100)} sm, qutida {quti} tadan. Kamida necha quti kerak?", q,
                    f"Bir tomonga ${math.ceil(a / p)}$, ikkinchisiga ${math.ceil(b / p)}$ ta: jami ${soni}$ plitka; ${soni} : {quti} \\approx {_f(soni / quti)}$ → yuqoriga yaxlitlaymiz: {q}",
                    [round(soni / quti) if round(soni / quti) != q else q - 1, soni, q + 1])
        return (f"Xona {a} m × {b} m. Plitka {int(p * 100)}×{int(p * 100)} sm. Nechta plitka kerak? (bo‘laklar ham butun plitka hisoblanadi)", soni,
                f"${a} : {p:g}$ → {math.ceil(a / p)} ta, ${b} : {p:g}$ → {math.ceil(b / p)} ta; ${math.ceil(a / p)} \\cdot {math.ceil(b / p)} = {soni}$", [int(a * b / (p * p)), soni + math.ceil(a / p), a * b])
    if kontekst == "chegirma":
        narx = rng.choice([30000, 45000, 60000]); ch = rng.choice([20, 30, 40])
        aksiya = rng.choice(["bepul", "yarim"])
        a = narx * 3 * (100 - ch) // 100
        b = narx * 2 if aksiya == "bepul" else narx * 2 + narx // 2
        matn = "«3 ta olsang — 3-chisi bepul»" if aksiya == "bepul" else "«3-chisi yarim narxda»"
        j = "1" if a < b else "2" if b < a else "farqi yo‘q"
        return (f"Bitta futbolka {narx} so‘m. 1-do‘kon: hammasiga {ch}% chegirma. 2-do‘kon: {matn}. 3 ta futbolka qaysi do‘konda arzon? (1, 2 yoki farqi yo‘q)",
                j, f"1-do‘kon: ${narx * 3} \\cdot {(100 - ch) / 100:g} = {a}$; 2-do‘kon: ${b}$.\nJavob: {j}", [x for x in ("1", "2", "farqi yo‘q") if x != j])
    if kontekst == "hovuz":
        u, e, ch = r(6, 25), r(3, 10), rng.choice([1.2, 1.5, 2])
        hajm = u * e * ch; v = rng.choice([10, 20, 30])
        soat = hajm / v
        return (f"Hovuz {u} m × {e} m, chuqurligi {ch:g} m. Nasos soatiga {v} m³ suv quyadi. Hovuz necha soatda to‘ladi? (0,1 gacha)", f"{round(soat, 1):g}".replace(".", ","),
                f"Hajm: ${u} \\cdot {e} \\cdot {ch:g} = {_f(hajm)}$ m³; ${_f(hajm)} : {v} \\approx {round(soat, 1):g}$ soat",
                [f"{round(hajm, 1):g}".replace(".", ","), f"{round(u * e / v, 1):g}".replace(".", ","), f"{round(soat * 60, 1):g}".replace(".", ",")])
    return gen_xb("chipta:1", rng)


KONTEKSTLAR = list(SAHNA.keys())

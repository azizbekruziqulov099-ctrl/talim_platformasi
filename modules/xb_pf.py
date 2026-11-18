"""PISA moliyaviy savodxonlik: PF-PUL, PF-REJ, PF-XAV, PF-MUH."""
from fractions import Fraction

from modules.pisa_mat_g import reg, num, _y, _o, _yopiq, fig_stolbik

TOP = "P_F"


def _tema(kod, nom, soha, belgi, maqsad, dars):
    return {"nom": nom, "soha": soha, "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": TOP, "dars": dars}


def _d(sar, doska, ovoz):
    return {"sarlavha": sar, "doska": doska, "ovoz": ovoz}


# PF-PUL: pul va tranzaksiyalar
@reg("PF-PUL", "yopiq")
def pul_qaytim(rng):
    n = rng.choice([12, 18, 24, 35, 47]); k = rng.choice([2, 3, 4]); b = n * k; to = (b // 50000 + 1) * 50000 if b >= 1000 else 100
    n *= 1000; b = n * k; to = (b // 50000 + 1) * 50000
    return _y(rng, f"Do‘konda {k} ta daftar sotib olindi, har biri {n} so‘m. To‘lov {to} so‘m berildi. Qaytim necha so‘m?", to - b, [f"Narx: {k}·{n} = {b}.", f"Qaytim: {to} − {b} = {to - b}."], noto=[to - n, b, to + b])


@reg("PF-PUL", "yopiq")
def pul_valyuta(rng):
    kurs = rng.choice([12000, 12500, 12800, 13000]); d = rng.choice([20, 50, 80, 120])
    return _y(rng, f"1 dollar = {kurs} so‘m. {d} dollar necha so‘m bo‘ladi?", d * kurs, [f"{d} · {kurs} = {d * kurs}."], noto=[d * kurs // 10, kurs // d, d + kurs])


@reg("PF-PUL", "yopiq")
def pul_komissiya(rng):
    s = rng.choice([500, 800, 1000, 2000]) * 1000; p = rng.choice([1, 2, 3])
    return _y(rng, f"Kartadan {s} so‘m o‘tkazishda {p}% komissiya olinadi. Komissiya necha so‘m?", s * p // 100, [f"{s}·{p}/100 = {s * p // 100}."], noto=[s * p // 10, s + s * p // 100, p * 1000])


@reg("PF-PUL", "ochiq")
def pul_chek(rng):
    a = rng.choice([8, 12, 15]) * 1000; b = rng.choice([4, 6, 9]) * 1000; k = rng.choice([2, 3])
    return _o(f"Chekda: non {k} dona × {a} so‘m; sut 1 dona × {b} so‘m.", [("a) Jami necha so‘m?", k * a + b), ("b) 100 000 so‘m berilsa, qaytim?", 100000 - k * a - b)], [f"a) {k}·{a} + {b} = {k * a + b}.", f"b) 100000 − {k * a + b} = {100000 - k * a - b}."])


@reg("PF-PUL", "ochiq")
def pul_chegirma(rng):
    P = rng.choice([200, 400, 600, 800]) * 1000; d = rng.choice([10, 15, 20, 25])
    return _o(f"Telefon narxi {P} so‘m, chegirma {d}%.", [("a) Chegirma summasi?", P * d // 100), ("b) To‘lanadigan summa?", P - P * d // 100)], [f"a) {P}·{d}/100 = {P * d // 100}.", f"b) {P} − {P * d // 100} = {P - P * d // 100}."])


@reg("PF-PUL", "ochiq")
def pul_ayirboshlash(rng):
    kurs = rng.choice([12000, 12500, 13000]); s = kurs * rng.choice([3, 5, 8])
    return _o(f"Valyuta ayirboshlash punktida 1 dollar = {kurs} so‘m. Sizda {s} so‘m bor.", [("a) Necha dollar olasiz?", s // kurs), (f"b) {s // kurs} dollarni qaytarib sotsangiz va kurs {kurs - 200} bo‘lsa, necha so‘m olasiz?", (s // kurs) * (kurs - 200))], [f"a) {s} ÷ {kurs} = {s // kurs}.", f"b) {s // kurs}·{kurs - 200} = {(s // kurs) * (kurs - 200)}."])


# PF-REJ: byudjet va rejalashtirish
@reg("PF-REJ", "yopiq")
def rej_jamg(rng):
    d = rng.choice([2000, 3000, 4000]) * 1000; x = rng.choice([40, 50, 60, 70]); 
    return _y(rng, f"Oylik daromad {d} so‘m, xarajatlar daromadning {x}%. Qolgan (jamg‘arma) necha so‘m?", d - d * x // 100, [f"Xarajat: {d}·{x}/100 = {d * x // 100}.", f"Qolgan: {d} − {d * x // 100} = {d - d * x // 100}."], noto=[d * x // 100, d - x * 1000, d // x])


@reg("PF-REJ", "yopiq")
def rej_oy(rng):
    t = rng.choice([3000, 4800, 6000, 9000]) * 1000; m = rng.choice([500, 600, 800, 1000]) * 1000
    while t % m: m = rng.choice([500, 600, 800, 1000]) * 1000; t = m * rng.randint(4, 12)
    return _y(rng, f"Mobil telefon uchun {t} so‘m kerak. Har oy {m} so‘mdan jamg‘arilsa, necha oy kerak?", t // m, [f"{t} ÷ {m} = {t // m} oy."], noto=[t // m + 1, t // m - 1, t // m * 2])


@reg("PF-REJ", "ochiq")
def rej_byudjet(rng):
    d = rng.choice([4000, 5000, 6000]) * 1000; a, b = rng.choice([(50, 30), (40, 40), (60, 25)]); 
    q = _o(f"Oilaning oylik daromadi {d} so‘m. Oziq-ovqatga {a}%, kommunal to‘lovlarga {b}% sarflanadi.", [("a) Oziq-ovqatga necha so‘m?", d * a // 100), ("b) Qolgan summa necha so‘m?", d * (100 - a - b) // 100)], [f"a) {d}·{a}/100 = {d * a // 100}.", f"b) Qolgan {100 - a - b}% = {d * (100 - a - b) // 100}."])
    return q


@reg("PF-REJ", "ochiq")
def rej_grafik(rng):
    n = ["Oziq", "Yo‘l", "Kommunal", "Boshqa"]; v = [rng.choice([800, 1000, 1200, 1500]) * 1000 // 1000 for _ in range(4)]
    q = _o("Diagrammada oylik xarajatlar (ming so‘mda) ko‘rsatilgan.", [("a) Jami xarajat (ming so‘m)?", sum(v)), ("b) Eng katta xarajat (ming so‘m)?", max(v))], [f"a) {' + '.join(map(str, v))} = {sum(v)}.", f"b) Eng katta: {max(v)}."])
    q["rasm"] = fig_stolbik(n, v, "Xarajatlar"); return q


@reg("PF-REJ", "yopiq")
def rej_tejash(rng):
    a = rng.choice([300, 450, 600]) * 1000; h = rng.choice([4, 6, 12])
    return _y(rng, f"Har oy {a} so‘m tejalsa, {h} oyda necha so‘m yig‘iladi?", a * h, [f"{a}·{h} = {a * h}."], noto=[a + h, a * h // 2, a * (h + 1)])


@reg("PF-REJ", "yopiq")
def rej_taqqos(rng):
    a = rng.choice([90, 120, 150]); b = a - rng.choice([10, 15, 20]); 
    return _yopiq(rng, f"Internet tarifi A: oyiga {a} ming so‘m. B: {b} ming so‘m, lekin tezligi past. Faqat narx bo‘yicha qaysi arzon?", "B", [f"{b} < {a}."], noto=["A", "Ikkalasi bir xil", "Aniqlab bo‘lmaydi"], tartib=False)


# PF-XAV: xavf va foyda
@reg("PF-XAV", "yopiq")
def xav_foiz(rng):
    s = rng.choice([1000, 2000, 5000]) * 1000; p = rng.choice([5, 8, 10]); 
    return _y(rng, f"Bankka {s} so‘m yillik {p}% bilan qo‘yildi. 1 yildan keyin foyda necha so‘m?", s * p // 100, [f"{s}·{p}/100 = {s * p // 100}."], noto=[s + s * p // 100, s * p // 10, p * 1000])


@reg("PF-XAV", "yopiq")
def xav_murakkab(rng):
    s = rng.choice([100, 200, 500]) * 1000; p = rng.choice([10, 20])
    r = s * (100 + p) * (100 + p) // 10000
    return _y(rng, f"{s} so‘m yiliga {p}% dan 2 yil davomida o‘sadi (har yil oxirida foiz asosiy summaga qo‘shiladi). 2 yildan keyin summa necha so‘m?", r, [f"1-yil: {s}·{(100 + p) / 100:g} = {s * (100 + p) // 100}.", f"2-yil: {s * (100 + p) // 100}·{(100 + p) / 100:g} = {r}."], noto=[s + 2 * s * p // 100, s * (100 + 2 * p) // 100 + 1000, r + s // 10])


@reg("PF-XAV", "ochiq")
def xav_sugurta(rng):
    b = rng.choice([200, 400, 800]) * 1000; s = rng.choice([8, 10, 12]) 
    return _o(f"Telefon sug‘urtasi yiliga narxning {s}% ni tashkil etadi. Telefon narxi {b} so‘m.", [("a) Sug‘urta narxi?", b * s // 100), ("b) Telefon sinsa va ta’mirlash {0} so‘m tursa, sug‘urta bilan tejaladigan summa?".format(b // 2), b // 2 - b * s // 100)], [f"a) {b}·{s}/100 = {b * s // 100}.", f"b) {b // 2} − {b * s // 100} = {b // 2 - b * s // 100}."])


@reg("PF-XAV", "ochiq")
def xav_kredit(rng):
    k = rng.choice([1200, 2400, 3600]) * 1000; m = rng.choice([6, 12]); p = rng.choice([10, 20])
    return _o(f"{k} so‘mlik texnika {m} oyga, qo‘shimcha {p}% bilan bo‘lib to‘lashga olindi.", [("a) Jami to‘lanadigan summa?", k * (100 + p) // 100), ("b) Oylik to‘lov?", Fraction(k * (100 + p), 100 * m))], [f"a) {k}·{100 + p}/100 = {k * (100 + p) // 100}.", f"b) {k * (100 + p) // 100} ÷ {m} = {num(Fraction(k * (100 + p), 100 * m))}."])


@reg("PF-XAV", "yopiq")
def xav_ehtimol(rng):
    n = rng.choice([4, 5, 10]); 
    return _yopiq(rng, f"Lotereyada {n * 100} ta biletdan faqat {n} tasi yutuqli. Bitta bilet yutish ehtimoli?", "1/100", [f"{n}/{n * 100} = 1/100."], noto=["1/10", "1/50", "1/1000"], tartib=False)


@reg("PF-XAV", "yopiq")
def xav_soliq(rng):
    d = rng.choice([3, 5, 8]) * 1000000; 
    return _y(rng, f"Daromaddan 12% soliq olinadi. {d} so‘mlik daromadda soliq necha so‘m?", d * 12 // 100, [f"{d}·12/100 = {d * 12 // 100}."], noto=[d * 12 // 10, d - d * 12 // 100, 12000])


# PF-MUH: moliyaviy muhit
@reg("PF-MUH", "yopiq")
def muh_infl(rng):
    p = rng.choice([100, 200, 500]) * 1000; i = rng.choice([5, 10, 20])
    return _y(rng, f"Mahsulot narxi {p} so‘m edi. Inflyatsiya tufayli narx {i}% ga oshdi. Yangi narx?", p * (100 + i) // 100, [f"{p}·{100 + i}/100 = {p * (100 + i) // 100}."], noto=[p + i, p * (100 - i) // 100, p + i * 1000])


@reg("PF-MUH", "yopiq")
def muh_arzon(rng):
    a = rng.choice([2, 3, 4]); pa = rng.choice([12, 18, 24]) * 1000; b = rng.choice([5, 6]); pb = pa * b // a - rng.choice([1000, 2000])
    return _yopiq(rng, f"Do‘konda {a} dona mahsulot {pa} so‘m, boshqasida {b} dona {pb} so‘m. 1 donasi qaysi do‘konda arzon?", "Ikkinchi", [f"Birinchi: {pa}/{a} = {pa // a}.", f"Ikkinchi: {pb}/{b} ≈ {pb // b}; kichikroq."], noto=["Birinchi", "Teng", "Aniqlab bo‘lmaydi"], tartib=False) if pb / b < pa / a else _y(rng, f"Mahsulot {a} donasi {pa} so‘m. 1 donasi necha so‘m?", pa // a, [f"{pa} ÷ {a} = {pa // a}."], noto=[pa * a, pa // a + 1000, pa - a])


@reg("PF-MUH", "ochiq")
def muh_ish(rng):
    s = rng.choice([30, 40, 60]) * 1000; h = rng.choice([20, 22, 25]); 
    return _o(f"Talaba soatiga {s} so‘m ishlaydi, oyiga {h} kun, kuniga 4 soat.", [("a) Oylik daromad?", s * h * 4), ("b) Soliq 12% bo‘lsa, qo‘lga tegadigan summa?", s * h * 4 * 88 // 100)], [f"a) {s}·{h}·4 = {s * h * 4}.", f"b) {s * h * 4}·88/100 = {s * h * 4 * 88 // 100}."])


@reg("PF-MUH", "ochiq")
def muh_tarif(rng):
    a = rng.choice([30, 50]); b = rng.choice([200, 300]); m = rng.choice([100, 150, 400])
    return _o(f"Tarif: oyiga {a} ming so‘m, shundan 200 daqiqa bepul, undan keyin daqiqasi {b} so‘m.", [(f"a) {m} daqiqa gaplashilsa, qo‘shimcha to‘lov (so‘m)?", max(0, m - 200) * b), ("b) Jami to‘lov (so‘m)?", a * 1000 + max(0, m - 200) * b)], [f"a) max(0, {m} − 200)·{b} = {max(0, m - 200) * b}.", f"b) {a * 1000} + {max(0, m - 200) * b} = {a * 1000 + max(0, m - 200) * b}."])


@reg("PF-MUH", "yopiq")
def muh_firib(rng):
    return _yopiq(rng, rng.choice(["«Faqat bugun! Hammasi 50% arzon!» e’lonini ko‘rganda eng to‘g‘ri harakat qaysi?", "Notanish saytda «tez boyish» va'dasi uchrasa, eng to‘g‘ri harakat qaysi?"]), "Ishonchli manbada tekshirish", ["Va’daga darhol ishonma: manbani va shartlarni tekshir."], noto=["Darhol to‘lash", "Karta ma’lumotini yuborish", "Do‘stlarga tarqatish"], tartib=False)


@reg("PF-MUH", "yopiq")
def muh_parol(rng):
    return _yopiq(rng, "Bank kartasining PIN-kodi bilan nima qilish kerak?", "Hech kimga aytmaslik", ["PIN-kod maxfiy: bank xodimiga ham aytilmaydi."], noto=["Do‘stga aytish", "Karta ustiga yozish", "Telefon raqamiga yuborish"], tartib=False)


TEMA = {
    "PF-PUL": _tema("PF-PUL", "Pul va tranzaksiyalar", "Moliya", "💵", "Qaytim, valyuta, komissiya, chek va chegirma", [
        _d("Pul hisobi", "Qaytim = berilgan − narx\nValyuta: dollar · kurs\nKomissiya = summa · p%", "Qaytim berilgan pul minus narx. Valyutada dollar sonini kursga ko‘paytiramiz. Komissiya summaning foizi."),
        _d("Chek va chegirma", "Chek: har qator = soni × narx\nChegirma = narx · p/100\nTo‘lov = narx − chegirma", "Chekni o‘qiyotganda har qatordagi son va narxni ko‘paytirib, hammasini qo‘shamiz. Chegirma narxning foizi, to‘lov esa narx minus chegirma.")]),
    "PF-REJ": _tema("PF-REJ", "Byudjet va rejalashtirish", "Moliya", "🗓️", "Daromad, xarajat, jamg‘arma maqsadi", [
        _d("Byudjet", "Jamg‘arma = daromad − xarajat\nXarajat = daromad · p%\nMaqsad / oylik jamg‘arma = oylar", "Byudjet — daromad va xarajatlar rejasi. Qolgan summa jamg‘arma. Maqsadni oylik jamg‘armaga bo‘lsak, kerakli oylar chiqadi.")]),
    "PF-XAV": _tema("PF-XAV", "Xavf va foyda", "Moliya", "⚖️", "Foiz, murakkab foiz, kredit, sug‘urta, ehtimol", [
        _d("Foiz va kredit", "Oddiy foyda = summa · p%\n2 yil: summa · (1 + p/100)²\nKredit: jami = summa · (1 + p/100)", "Bankdagi foyda — summaning foizi. Murakkab foizda har yil oxiridagi foiz asosiy summaga qo‘shiladi. Kreditda qo‘shimcha foiz ham to‘lanadi."),
        _d("Xavf", "Sug‘urta — xavfdan himoya\nEhtimol = qulay / barcha\nBaland foyda — baland xavf", "Sug‘urta kutilmagan zarardan himoyalaydi. Katta foyda va'da qilinsa, odatda xavf ham katta bo‘ladi.")]),
    "PF-MUH": _tema("PF-MUH", "Moliyaviy muhit", "Moliya", "🛡️", "Inflyatsiya, soliq, tarif, firibgarlikdan saqlanish", [
        _d("Narx va soliq", "Inflyatsiya: narx · (100 + i)/100\nSoliq = daromad · p%\n1 dona narxi = jami / soni", "Inflyatsiyada narxlar oshadi, pulning xarid qobiliyati kamayadi. Soliq daromadning foizi. Arzonini topish uchun bir dona narxini solishtiramiz."),
        _d("Xavfsizlik", "PIN-kod — maxfiy\nSMS-kodni aytma\nVa’dani tekshir", "Karta PIN-kodi va SMS kodlarini hech kimga aytmang. Haddan tashqari yaxshi va’dalar ko‘pincha firibgarlik belgisi.")]),
}

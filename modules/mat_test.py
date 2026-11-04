"""REV299: matematika mavzusiga mos savollarni dastur bilan yasash — javobni dastur HISOBLAYDI (xato bo'lmaydi).
Mavzu nomi (uz/ru/en) bo'yicha tur aniqlanadi; sonlar sinfga mos oraliqda. Variantlar: to'g'ri javob + 3 ta
yaqin, lekin har xil xato javob. Savol matni o'quvchi tilida. Mos tur topilmasa — [] (kitob testlari ishlatiladi)."""
import math
import random
import re
from fractions import Fraction

# (tur, uz, ru, en) — mavzu nomidagi kalit so'zlar
TURLAR = [
    ("uchburchak_yuza", r"uchburchak(ning)? yuzini topish|uchburchak yuzi", "", ""),
    ("kasr_onli", r"oddiy kasrni o.nli kasrga", "", ""),
    ("onli_bolish", r"o.nli kasrni o.n, yuz va mingga bo.lish", "", ""),
    ("kasr_bolish", r"kasrlarni bo.lish|kasrga bo.lish|kasrni natural songa bo.lish", "", ""),
    ("qoldiq", r"qoldiqli", r"с остатком", r"remainder"),
    ("tenglama_x", r"noma.lum (qo.shiluvchi|kamayuvchi|ayriluvchi)|tenglamalar(ni)? yechish|tenglamani yechish|^tenglamalar$|sodda chiziqli tenglama|chiziqli tenglama",
     r"неизвестн(ого|ое) (слагаем|уменьшаем|вычитаем)|решение уравнени|^уравнения$|линейн\w* уравнени", r"unknown (addend|minuend|subtrahend)|solving equations|^equations$|linear equation"),
    ("kvadrat_tenglama", r"kvadrat tenglama|diskriminant|viyet", r"квадратн\w* уравнени|дискриминант|виет", r"quadratic (equation|formula)|discriminant|vieta"),
    ("progressiya_a", r"arifmetik progressiya", r"арифметическ\w* прогресси", r"arithmetic progression"),
    ("progressiya_g", r"geometrik progressiya", r"геометрическ\w* прогресси", r"geometric progression"),
    ("logarifm", r"logarifm", r"логарифм", r"logarithm"),
    ("daraja", r"daraja(si|lar)? va uning xossa|ratsional ko.rsatkichli daraja|^daraja", r"степен\w* с рациональн|свойства степен", r"rational exponent|powers"),
    ("ildiz", r"kvadrat (va kub )?ildiz|arifmetik ildiz", r"квадратн\w* (и кубическ\w* )?кор|арифметическ\w* кор", r"square root|arithmetic root"),
    ("kombinatorika", r"o.rinlashtirish|o.rin almashtirish|guruhlash|kombinator", r"размещени|перестановк|сочетани|комбинатор", r"arrangement|permutation|combination|combinator|counting principle"),
    ("ehtimol", r"ehtimol", r"вероятност", r"probabilit"),
    ("pifagor", r"pifagor", r"пифагор", r"pythagor"),
    ("masofa", r"ikki nuqta orasidagi masofa", r"расстояние между двумя точками", r"distance between two points"),
    ("ekub", r"ekub|eng katta umumiy bo.luvchi", r"нод|наибольший общий делитель", r"gcd|greatest common divisor"),
    ("ekuk", r"ekuk|eng kichik umumiy karrali", r"нок|наименьшее общее кратное", r"lcm|least common multiple"),
    ("bolinish_belgi", r"bo.linish belgi", r"признак\w* делимост", r"divisibility"),
    ("butun_son", r"butun sonlar|manfiy son", r"целых чисел|отрицательн", r"integers|negative numbers"),
    ("foiz", r"foiz|qqs|chegirma|ustama", r"процент|ндс|скидк|наценк", r"percent|vat|discount|markup"),
    ("onli_kasr", r"o.nli kasr", r"десятичн", r"decimal"),
    ("aralash_son", r"aralash son", r"смешанн\w* чис", r"mixed number"),
    ("kasr_qoshish", r"maxrajli kasrlarni qo.shish|kasrlarni qo.shish va ayirish", r"сложение и вычитание дробей", r"adding and subtracting fractions"),
    ("kasr_kopaytirish", r"kasrlarni ko.paytirish|kasrni natural songa ko.paytirish|kasrni .* bo.lish|kasrga bo.lish", r"умножение дроб|делени\w* .*дроб", r"multiplying (a )?fraction|dividing .*fraction"),
    ("kasr_qism", r"sonning (kasr|ulush)|kasriga ko.ra|ulushini topish|qismini topish", r"дроби от числа|числа по его дроби|доли числа", r"fraction of a number|number from its fraction"),
    ("kasr_taqqos", r"kasrlarni taqqoslash", r"сравнение дробей", r"comparing fractions"),
    ("nisbat", r"nisbat", r"отношени", r"ratio"),
    ("tezlik", r"tezlik|harakatga doir|harakat", r"скорост|движени", r"speed|motion"),
    ("ortacha", r"o.rta arifmetik|o.rtacha qiymat|o.rtacha", r"среднее арифметическ|среднее значение", r"arithmetic mean|average|mean"),
    ("perimetr", r"perimetr", r"периметр", r"perimeter"),
    ("yuza", r"yuza(si)?(?! birlik)|yuzini", r"площад", r"area"),
    ("hajm", r"hajm", r"объ[её]м", r"volume"),
    ("aylana", r"aylana(ning)? uzunligi|doira(ning)? yuzi", r"длина окружности|площадь круга", r"circumference|area of a circle"),
    ("birlik", r"(?<![a-z‘’'])(santi|detsi|milli|kilo)?metr(?![a-z])|massa birlik|uzunlik birlik|^massa|soat va minut|soat, minut|vaqt birlik|o.lchov birliklarini", r"единиц|сантиметр|дециметр|миллиметр|метр|километр|масс|час и минут", r"units|centimetre|decimetre|millimetre|metre|kilometre|mass|hour and minute"),
    ("tartib", r"amallar tartibi|qavs|murakkab ifoda|ikki amalli", r"порядок (выполнения )?действий|скобк|составные выражения|в два действия", r"order of operations|brackets|compound expressions|two-operation"),
    ("kopaytirish", r"ko.paytirish|ko.paytirish jadvali|karra|o.nga va yuzga", r"умножени|таблица умножения", r"multiplication|multiplying|multiply"),
    ("bolish", r"bo.lish", r"делени", r"division|dividing"),
    ("ayirish", r"ayirish", r"вычитани", r"subtract"),
    ("qoshish", r"qo.shish", r"сложени", r"addition|adding"),
    ("taqqoslash", r"taqqoslash|solishtirish", r"сравнени", r"compar"),
    ("sonlar", r"sonlar|raqam|sanash|xonali", r"числа|цифр|счёт|счет|значн", r"numbers|digits|counting"),
]

M = {
    "uz": {"son": "Hisoblang: {e}", "x": "Tenglamani yeching: {e}. x = ?", "qoldiq": "{a} ni {b} ga bo‘lganda qoldiq nechaga teng?", "kop": "{a} va {b} dan qaysi biri katta?",
           "kat": "Eng katta sonni toping:", "foiz": "{a} ning {p}% i nechaga teng?", "per": "Tomonlari {a} va {b} bo‘lgan to‘g‘ri to‘rtburchakning perimetri nechaga teng?",
           "yuz": "Tomonlari {a} va {b} bo‘lgan to‘g‘ri to‘rtburchakning yuzi nechaga teng?", "hajm": "O‘lchamlari {a}, {b} va {c} bo‘lgan to‘g‘ri burchakli parallelepipedning hajmi nechaga teng?",
           "tez": "Tezligi {v} km/soat bo‘lgan mashina {t} soatda necha km yo‘l yuradi?", "ort": "{q} sonlarining o‘rta arifmetigi nechaga teng?",
           "ekub": "EKUB({a}; {b}) = ?", "ekuk": "EKUK({a}; {b}) = ?", "bol": "Qaysi son {d} ga qoldiqsiz bo‘linadi?", "pif": "To‘g‘ri burchakli uchburchakning katetlari {a} va {b}. Gipotenuzasi nechaga teng?",
           "mas": "A({x1}; {y1}) va B({x2}; {y2}) nuqtalar orasidagi masofa nechaga teng?", "kv": "x² − {s}x + {p} = 0 tenglamaning ildizlari yig‘indisi va ko‘paytmasi: x₁ + x₂ = ?",
           "kvi": "x² − {s}x + {p} = 0 tenglamaning kichik ildizi nechaga teng?", "ap": "Arifmetik progressiyada a₁ = {a}, d = {d}. a{n} = ?", "gp": "Geometrik progressiyada b₁ = {a}, q = {q}. b{n} = ?",
           "log": "log{b}({x}) = ?", "dar": "Hisoblang: {e}", "ild": "Hisoblang: √{x}", "fakt": "{n} ta har xil kitobni javonga necha xil usulda terish mumkin?",
           "komb": "{n} ta o‘quvchidan {k} tasini necha xil usulda tanlash mumkin?", "ehti": "Qutida {a} ta oq va {b} ta qora shar bor. Tavakkaliga olingan shar oq bo‘lish ehtimoli qancha?",
           "kasrq": "{n} ning {p}/{q} qismi nechaga teng?", "nis": "{a} : {b} nisbatni soddalashtiring.", "bir": "{a} {u1} necha {u2} bo‘ladi?",
           "aylana": "Radiusi {r} bo‘lgan aylananing uzunligi nechaga teng? (π ≈ 3,14)", "kasrk": "{p}/{q} va {r}/{s} kasrlardan qaysi biri katta?"},
    "ru": {"son": "Вычислите: {e}", "x": "Решите уравнение: {e}. x = ?", "qoldiq": "Какой остаток при делении {a} на {b}?", "kop": "Какое число больше: {a} или {b}?",
           "kat": "Найдите наибольшее число:", "foiz": "Чему равны {p}% от {a}?", "per": "Чему равен периметр прямоугольника со сторонами {a} и {b}?",
           "yuz": "Чему равна площадь прямоугольника со сторонами {a} и {b}?", "hajm": "Чему равен объём прямоугольного параллелепипеда с измерениями {a}, {b} и {c}?",
           "tez": "Машина едет со скоростью {v} км/ч. Сколько километров она проедет за {t} ч?", "ort": "Чему равно среднее арифметическое чисел {q}?",
           "ekub": "НОД({a}; {b}) = ?", "ekuk": "НОК({a}; {b}) = ?", "bol": "Какое число делится на {d} без остатка?", "pif": "Катеты прямоугольного треугольника равны {a} и {b}. Чему равна гипотенуза?",
           "mas": "Чему равно расстояние между точками A({x1}; {y1}) и B({x2}; {y2})?", "kv": "Для уравнения x² − {s}x + {p} = 0 найдите x₁ + x₂.",
           "kvi": "Чему равен меньший корень уравнения x² − {s}x + {p} = 0?", "ap": "В арифметической прогрессии a₁ = {a}, d = {d}. a{n} = ?", "gp": "В геометрической прогрессии b₁ = {a}, q = {q}. b{n} = ?",
           "log": "log{b}({x}) = ?", "dar": "Вычислите: {e}", "ild": "Вычислите: √{x}", "fakt": "Сколькими способами можно расставить на полке {n} разных книг?",
           "komb": "Сколькими способами можно выбрать {k} учеников из {n}?", "ehti": "В коробке {a} белых и {b} чёрных шаров. Какова вероятность вынуть белый шар?",
           "kasrq": "Чему равны {p}/{q} от {n}?", "nis": "Упростите отношение {a} : {b}.", "bir": "Сколько {u2} в {a} {u1}?",
           "aylana": "Чему равна длина окружности радиуса {r}? (π ≈ 3,14)", "kasrk": "Какая дробь больше: {p}/{q} или {r}/{s}?"},
    "en": {"son": "Calculate: {e}", "x": "Solve the equation: {e}. x = ?", "qoldiq": "What is the remainder when {a} is divided by {b}?", "kop": "Which number is greater: {a} or {b}?",
           "kat": "Find the greatest number:", "foiz": "What is {p}% of {a}?", "per": "What is the perimeter of a rectangle with sides {a} and {b}?",
           "yuz": "What is the area of a rectangle with sides {a} and {b}?", "hajm": "What is the volume of a cuboid measuring {a}, {b} and {c}?",
           "tez": "A car travels at {v} km/h. How far does it travel in {t} h?", "ort": "What is the mean of the numbers {q}?",
           "ekub": "GCD({a}; {b}) = ?", "ekuk": "LCM({a}; {b}) = ?", "bol": "Which number is divisible by {d}?", "pif": "The legs of a right triangle are {a} and {b}. What is the hypotenuse?",
           "mas": "What is the distance between A({x1}; {y1}) and B({x2}; {y2})?", "kv": "For x² − {s}x + {p} = 0, find x₁ + x₂.",
           "kvi": "What is the smaller root of x² − {s}x + {p} = 0?", "ap": "In an arithmetic progression a₁ = {a}, d = {d}. a{n} = ?", "gp": "In a geometric progression b₁ = {a}, q = {q}. b{n} = ?",
           "log": "log{b}({x}) = ?", "dar": "Calculate: {e}", "ild": "Calculate: √{x}", "fakt": "In how many ways can {n} different books be arranged on a shelf?",
           "komb": "In how many ways can {k} pupils be chosen from {n}?", "ehti": "A box has {a} white and {b} black balls. What is the probability of drawing a white ball?",
           "kasrq": "What is {p}/{q} of {n}?", "nis": "Simplify the ratio {a} : {b}.", "bir": "How many {u2} are there in {a} {u1}?",
           "aylana": "What is the circumference of a circle with radius {r}? (π ≈ 3.14)", "kasrk": "Which fraction is greater: {p}/{q} or {r}/{s}?"},
}
BIRLIK = {"uz": [("m", "sm", 100), ("dm", "sm", 10), ("sm", "mm", 10), ("km", "m", 1000), ("kg", "g", 1000), ("t", "kg", 1000), ("soat", "minut", 60), ("minut", "sekund", 60)],
          "ru": [("м", "см", 100), ("дм", "см", 10), ("см", "мм", 10), ("км", "м", 1000), ("кг", "г", 1000), ("т", "кг", 1000), ("ч", "мин", 60), ("мин", "с", 60)],
          "en": [("m", "cm", 100), ("dm", "cm", 10), ("cm", "mm", 10), ("km", "m", 1000), ("kg", "g", 1000), ("t", "kg", 1000), ("h", "min", 60), ("min", "s", 60)]}


import json as _json
import os as _os
try:
    _NOM = _json.load(open(_os.path.join(_os.path.dirname(__file__), "mat_nomlar.json"), encoding="utf8"))   # ru/en → uz
except OSError:
    _NOM = {}


ISTISNO = {
    "uchburchak_yuza": r"sinus", "onli_kasr": r"aylantirish|bo.lish|munosabat",
    "birlik": r"trigonometr|geometri|stereometr|planimetr|radian|hajm|yuza", "tenglama_x": r"trigonometr|kasr-chiziqli|grafik",
    "daraja": r"hosila", "logarifm": r"hosila", "kombinatorika": r"xossa", "ortacha": r"dispersiya|tezlik", "kasr_qoshish": r"algebraik",
    "kasr_kopaytirish": r"algebraik|aralash", "kopaytirish": r"tengsizlik|vektor|aralash|kasr|o.nli", "qoshish": r"formula|vektor|kasr|aralash|tengsizlik",
    "ayirish": r"vektor|kasr|aralash", "sonlar": r"yaxlit|tub son|ratsional|haqiqiy|juft|amal", "tezlik": r"parallel ko.chirish|birlik",
    "nisbat": r"nisbatan|o.zgaruvchan|proporsiya", "yuza": r"sinus|uchburchak|murakkab|doira", "perimetr": r"doira|murakkab", "bolish": r"bo.laklarga|kasr|qoldiq|o.nli|aralash",
    "tartib": r"chiziqli ifoda", "aralash_son": r"ko.paytirish|bo.lish",
    "foiz": r"o.sish|qismiga ko.ra|ustama|munosabat|o.zgarish", "hajm": r"aylanish|prizma|silindr|piramida|konus|shar|yassi|hajmli shakl|suyuqlik|murakkab",
}


def tur_top(nom):
    """Mavzu turi FAQAT o'zbekcha nom bo'yicha (ruscha/inglizcha nom tarjima jadvalidan o'zbekchaga) — uch tilda bir xil tur."""
    n = re.sub(r"^\d+\.\s*", "", str(nom or "")).strip()
    n = _NOM.get(n, n).lower()
    if re.match(r"^(takrorlash|повторение|review)\b", n):
        return None
    for tur, uz, *_ in TURLAR:
        if re.search(uz, n) and not (tur in ISTISNO and re.search(ISTISNO[tur], n)):
            return tur
    return None


def _sinf(g):
    m = re.search(r"\d+", str(g or ""))
    return int(m.group()) if m else 5


def _fmt(v, til):
    if isinstance(v, Fraction):
        return f"{v.numerator}/{v.denominator}" if v.denominator != 1 else str(v.numerator)
    if isinstance(v, float):
        s = f"{round(v, 6):.6f}".rstrip("0").rstrip(".")   # REV299: yaxlitlanmaydi (332,8 : 100 = 3,328, «3,33» emas)
        return s.replace(".", ",") if til != "en" else s
    return f"{v:,}".replace(",", " ") if isinstance(v, int) and abs(v) >= 10000 else str(v)


def _variant(rnd, tog, chalg, til):
    seen, out = {_fmt(tog, til)}, []
    for c in chalg:
        f = _fmt(c, til)
        if f not in seen and (not isinstance(c, (int, float)) or c == c):
            seen.add(f); out.append(f)
        if len(out) == 3:
            break
    if len(out) < 3:
        return None
    v = [_fmt(tog, til)] + out
    rnd.shuffle(v)
    return v, v.index(_fmt(tog, til))


def _yaqin(rnd, x, qadam=1):
    return [x + qadam, x - qadam, x + 2 * qadam, x - 2 * qadam, x + 10 * qadam, x * 2 if x else 3]


def bitta(tur, sinf, til, rnd):
    S = M[til]
    hi = {1: 20, 2: 100, 3: 1000, 4: 10000}.get(sinf, 100000)
    R = lambda a, b: rnd.randint(a, b)
    if tur == "qoshish":
        a, b = R(1, hi // 2), R(1, hi // 2); return S["son"].format(e=f"{a} + {b}"), a + b, _yaqin(rnd, a + b, 1 if sinf < 3 else 10)
    if tur == "sonlar":
        a = R(1, hi - 2)
        if rnd.random() < .5:
            return {"uz": f"{a} dan keyin qaysi son keladi?", "ru": f"Какое число идёт после {a}?", "en": f"Which number comes after {a}?"}[til], a + 1, [a - 1, a + 2, a + 10, a]
        return {"uz": f"{a + 1} dan oldin qaysi son keladi?", "ru": f"Какое число идёт перед {a + 1}?", "en": f"Which number comes before {a + 1}?"}[til], a, [a + 2, a + 1, a - 1 if a > 1 else a + 3, a + 10]
    if tur == "taqqoslash":
        a, b = rnd.sample(range(1, hi), 2); c = rnd.sample([x for x in range(1, hi) if x not in (a, b)], 2)
        return S["kat"] + " " + ", ".join(map(str, [a, b] + c)), max([a, b] + c), [a, b] + c
    if tur == "ayirish":
        a = R(2, hi); b = R(1, a - 1); return S["son"].format(e=f"{a} − {b}"), a - b, _yaqin(rnd, a - b, 1 if sinf < 3 else 10)
    if tur == "kopaytirish":
        if sinf <= 3: a, b = R(2, 9), R(2, 9)
        else: a, b = R(11, 99 if sinf == 4 else 999), R(2, 99)
        return S["son"].format(e=f"{a} × {b}"), a * b, [a * (b + 1), a * (b - 1), (a + 1) * b, a * b + 10, a * b - 10]
    if tur == "bolish":
        b = R(2, 9 if sinf <= 3 else 99); q = R(2, 9 if sinf <= 3 else 999); a = b * q
        return S["son"].format(e=f"{a} : {b}"), q, _yaqin(rnd, q)
    if tur == "qoldiq":
        b = R(3, 9 if sinf <= 4 else 30); q = R(2, 20); r = R(1, b - 1); a = b * q + r
        return S["qoldiq"].format(a=a, b=b), r, [x for x in range(0, b + 2) if x != r]
    if tur == "tartib":
        a, b, c = R(2, 20), R(2, 9), R(2, 9)
        if rnd.random() < .5: return S["son"].format(e=f"{a} + {b} × {c}"), a + b * c, [(a + b) * c, a + b + c, a * b + c, a + b * c + 1]
        return S["son"].format(e=f"({a} + {b}) × {c}"), (a + b) * c, [a + b * c, a + b + c, (a + b) * c + c, (a + b) * c - 1]
    if tur == "tenglama_x":
        if sinf <= 4:
            a, x = R(2, hi // 4), R(1, hi // 4)
            if rnd.random() < .5: return S["x"].format(e=f"x + {a} = {a + x}"), x, _yaqin(rnd, x) + [a + x + a]
            return S["x"].format(e=f"x − {a} = {x}"), x + a, [x, x - a if x > a else x + 2 * a, x + a + 1, x + a - 1]
        k, x, b = R(2, 9), R(-10, 15), R(-20, 20)
        bs = f"+ {b}" if b >= 0 else f"− {-b}"
        return S["x"].format(e=f"{k}x {bs} = {k * x + b}"), x, [x + 1, x - 1, -x if x else 2, (k * x + b + b) // k if k else 5, x + 2]
    if tur == "butun_son":
        a, b = R(-30, 30), R(-30, 30)
        op = rnd.choice(["+", "−", "×"])
        v = a + b if op == "+" else a - b if op == "−" else a * b
        bstr = f"({b})" if b < 0 else str(b)
        return S["son"].format(e=f"{a} {op} {bstr}"), v, [-v, v + 1, v - 1, v + 2 if v else 5, abs(a) + abs(b)]
    if tur == "foiz":
        p = rnd.choice([5, 10, 20, 25, 30, 40, 50, 60, 75]); a = rnd.choice([40, 60, 80, 100, 120, 200, 240, 300, 400, 500, 800, 1000])
        v = a * p // 100
        if a * p % 100: return None
        return S["foiz"].format(a=a, p=p), v, [v + 10, v - 5 if v > 5 else v + 5, a - v, v * 2, p]
    if tur == "perimetr":
        a, b = R(2, 30), R(2, 30); return S["per"].format(a=a, b=b), 2 * (a + b), [a + b, a * b, 2 * a + b, 2 * (a + b) + 2]
    if tur == "yuza":
        a, b = R(2, 30), R(2, 30); return S["yuz"].format(a=a, b=b), a * b, [2 * (a + b), a + b, a * b + a, a * (b + 1)]
    if tur == "hajm":
        a, b, c = R(2, 12), R(2, 12), R(2, 12); return S["hajm"].format(a=a, b=b, c=c), a * b * c, [a * b + c, 2 * (a * b + b * c + a * c), a * b * c + a, (a + b) * c]
    if tur == "aylana":
        r = R(1, 20); v = round(2 * 3.14 * r, 2); return S["aylana"].format(r=r), v, [round(3.14 * r, 2), round(3.14 * r * r, 2), round(2 * 3.14 * r + 1, 2), round(4 * 3.14 * r, 2)]
    if tur == "tezlik":
        v, t = rnd.choice([40, 50, 60, 70, 80, 90]), R(2, 6); return S["tez"].format(v=v, t=t), v * t, [v + t, v * (t + 1), v * (t - 1), v * t + 10]
    if tur == "ortacha":
        n = rnd.choice([3, 4, 5]); m = R(5, 40); q = [m + R(-5, 5) for _ in range(n - 1)]; q.append(m * n - sum(q))
        if min(q) <= 0: return None
        return S["ort"].format(q=", ".join(map(str, q))), m, [m + 1, m - 1, sum(q), m + 2]
    if tur in ("ekub", "ekuk"):
        g = R(2, 12); a, b = g * R(2, 9), g * R(2, 9)
        if a == b: return None
        v = math.gcd(a, b) if tur == "ekub" else a * b // math.gcd(a, b)
        return S[tur].format(a=a, b=b), v, [a * b, math.gcd(a, b) * 2, a * b // math.gcd(a, b) * 2, abs(a - b), min(a, b), max(a, b)]
    if tur == "bolinish_belgi":
        d = rnd.choice([2, 3, 4, 5, 9, 10]); tog = d * R(12, 999)
        chalg = [tog + k for k in (1, 2, 3, 4, 5, 6, 7) if (tog + k) % d]
        return S["bol"].format(d=d), tog, chalg
    if tur == "pifagor":
        a, b, c = rnd.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17), (12, 16, 20), (7, 24, 25)])
        return S["pif"].format(a=a, b=b), c, [a + b, c + 1, c - 1, b + 1]
    if tur == "masofa":
        x1, y1 = R(-5, 5), R(-5, 5); dx, dy = rnd.choice([(3, 4), (6, 8), (5, 12), (4, 3), (8, 6)])
        return S["mas"].format(x1=x1, y1=y1, x2=x1 + dx, y2=y1 + dy), int(math.hypot(dx, dy)), [dx + dy, int(math.hypot(dx, dy)) + 1, abs(dx - dy), dx * dy]
    if tur == "kvadrat_tenglama":
        x1, x2 = sorted(rnd.sample(range(1, 12), 2)); s, p = x1 + x2, x1 * x2
        if rnd.random() < .5: return S["kv"].format(s=s, p=p), s, [p, -s, s + 1, x2 - x1]
        return S["kvi"].format(s=s, p=p), x1, [x2, -x1, s, p]
    if tur == "progressiya_a":
        a, d, n = R(-10, 20), R(2, 9), R(5, 15); return S["ap"].format(a=a, d=d, n=n), a + (n - 1) * d, [a + n * d, a + (n - 2) * d, a * n, a + (n - 1) * d + 1]
    if tur == "progressiya_g":
        a, q, n = R(1, 5), rnd.choice([2, 3]), R(3, 7); return S["gp"].format(a=a, q=q, n=n), a * q ** (n - 1), [a * q ** n, a * q ** (n - 2), a * q * n, a + q * (n - 1)]
    if tur == "logarifm":
        b = rnd.choice([2, 3, 5, 10]); k = R(1, 6 if b < 5 else 4); return S["log"].format(b=b, x=b ** k), k, [k + 1, k - 1 if k > 1 else k + 2, b * k, b ** k // b]
    if tur == "daraja":
        a, k = R(2, 9), R(2, 4); return S["dar"].format(e=f"{a}^{k}".replace("^2", "²").replace("^3", "³").replace("^4", "⁴")), a ** k, [a * k, a ** (k - 1), a ** k + a, (a + 1) ** k]
    if tur == "ildiz":
        a = R(2, 30); return S["ild"].format(x=a * a), a, [a + 1, a - 1, a * 2, a * a // 2]
    if tur == "kombinatorika":
        if rnd.random() < .5:
            n = R(3, 7); return S["fakt"].format(n=n), math.factorial(n), [n * n, math.factorial(n - 1), n * (n - 1), math.factorial(n) // 2]
        n, k = R(4, 10), R(2, 3); return S["komb"].format(n=n, k=k), math.comb(n, k), [math.perm(n, k), n * k, math.comb(n, k) + n, math.comb(n, k - 1)]
    if tur == "ehtimol":
        a, b = R(1, 9), R(1, 9); v = Fraction(a, a + b); return S["ehti"].format(a=a, b=b), v, [Fraction(b, a + b), Fraction(a, b) if b else Fraction(1, 2), Fraction(1, a + b), Fraction(a, a + b + 1)]
    if tur in ("kasr_qism", "kasr_kopaytirish"):
        q = rnd.choice([2, 3, 4, 5, 6, 8, 10]); p = R(1, q - 1); n = q * R(2, 20)
        return S["kasrq"].format(n=n, p=p, q=q), n * p // q, [n // q, n * q // p if p else 1, n - n * p // q, n * p // q + p]
    if tur in ("kasr_qoshish", "aralash_son"):
        q = rnd.choice([3, 4, 5, 6, 7, 8, 9, 10, 12]); a, b = R(1, q - 1), R(1, q - 1)
        v = Fraction(a + b, q); return S["son"].format(e=f"{a}/{q} + {b}/{q}"), v, [Fraction(a + b, 2 * q), Fraction(a * b, q), Fraction(a + b + 1, q), Fraction(abs(a - b) or 1, q)]
    if tur == "kasr_taqqos":
        q1, q2 = rnd.sample([3, 4, 5, 6, 7, 8, 9], 2); p1, p2 = R(1, q1 - 1), R(1, q2 - 1)
        if Fraction(p1, q1) == Fraction(p2, q2): return None
        v = max(Fraction(p1, q1), Fraction(p2, q2))
        return S["kasrk"].format(p=p1, q=q1, r=p2, s=q2), f"{v.numerator * (q1 if v == Fraction(p1, q1) and False else 1)}", None
    if tur == "onli_kasr":
        a = R(11, 999) / 10; k = rnd.choice([10, 100]); return S["son"].format(e=f"{_fmt(a, til)} × {k}"), round(a * k, 2), [round(a * k / 10, 2), round(a * k * 10, 2), round(a + k, 2), round(a * k + 1, 2)]
    if tur == "nisbat":
        g = R(2, 9); a, b = R(1, 9), R(1, 9)
        if math.gcd(a, b) != 1 or a == b: return None
        return S["nis"].format(a=a * g, b=b * g), f"{a} : {b}", [f"{b} : {a}", f"{a * 2} : {b}", f"{a} : {b * 2}", f"{a + 1} : {b}"]
    if tur == "uchburchak_yuza":
        a, h = R(2, 20) * 2, R(2, 20); return {"uz": f"Asosi {a}, balandligi {h} bo‘lgan uchburchakning yuzi nechaga teng?", "ru": f"Чему равна площадь треугольника с основанием {a} и высотой {h}?",
            "en": f"What is the area of a triangle with base {a} and height {h}?"}[til], a * h // 2, [a * h, a + h, a * h // 2 + a, (a + h) * 2]
    if tur == "kasr_onli":
        p, q = rnd.choice([(1, 2), (1, 4), (3, 4), (1, 5), (2, 5), (3, 5), (4, 5), (1, 10), (3, 10), (7, 10), (1, 20), (3, 20), (1, 25), (7, 25)])
        v = p / q; return S["son"].format(e=f"{p}/{q} = ?"), v, [p / 10, q / 10, round(v * 10, 2), round(v + 0.1, 2)]
    if tur == "onli_bolish":
        a = R(11, 9999) / 10; k = rnd.choice([10, 100])
        return S["son"].format(e=f"{_fmt(a, til)} : {k}"), round(a / k, 4), [round(a * k, 2), round(a / k * 10, 4), round(a / k / 10, 5), round(a - k, 2) if a > k else round(a + k, 2)]
    if tur == "kasr_bolish":
        q = rnd.choice([2, 3, 4, 5, 6, 8]); p = R(1, q - 1); n = R(2, 9)
        if rnd.random() < .5:   # natural son : kasr
            v = Fraction(n * q, p); return S["son"].format(e=f"{n} : {p}/{q}"), v, [Fraction(n * p, q), Fraction(n, q), v + 1, Fraction(q, n * p)]
        v = Fraction(p, q * n); return S["son"].format(e=f"{p}/{q} : {n}"), v, [Fraction(p * n, q), Fraction(p, q + n), Fraction(q * n, p), Fraction(p, n)]
    if tur == "birlik":
        u1, u2, k = rnd.choice(BIRLIK[til]); a = R(2, 12); return S["bir"].format(a=a, u1=u1, u2=u2), a * k, [a * k // 10 or 1, a * k * 10, a + k, a * k + k]
    return None


def yasash(nom, sinf, til="uz", soni=20, seed=""):
    tur = tur_top(nom)
    if not tur:
        return []
    til = til if til in M else "uz"
    g = _sinf(sinf); rnd = random.Random(f"{seed}|{nom}|{til}")
    out, seen, urinish = [], set(), 0
    while len(out) < soni and urinish < soni * 15:
        urinish += 1
        r = bitta(tur, g, til, rnd)
        if not r:
            continue
        savol, tog, chalg = r
        if tur == "kasr_taqqos":   # alohida: ikki kasrdan biri
            m = re.findall(r"(\d+)/(\d+)", savol); f1, f2 = Fraction(int(m[0][0]), int(m[0][1])), Fraction(int(m[1][0]), int(m[1][1]))
            v = [f"{m[0][0]}/{m[0][1]}", f"{m[1][0]}/{m[1][1]}"]; tog_s = v[0] if f1 > f2 else v[1]
            v2 = list(v); rnd.shuffle(v2)
            if savol not in seen:
                seen.add(savol); out.append({"savol": savol, "variantlar": v2, "togri": v2.index(tog_s)})
            continue
        if isinstance(tog, str):
            vv = [tog] + [c for c in dict.fromkeys(chalg) if c != tog][:3]
            if len(vv) < 4: continue
            rnd.shuffle(vv); var = (vv, vv.index(tog))
        else:
            chalg = [c for c in chalg if not (isinstance(c, (int, float)) and isinstance(tog, (int, float)) and tog >= 0 and c < 0 and tur not in ("butun_son", "tenglama_x"))]
            var = _variant(rnd, tog, chalg, til)
        if not var or savol in seen:
            continue
        seen.add(savol)
        out.append({"savol": savol, "variantlar": var[0], "togri": var[1]})
    for i, q in enumerate(out):
        q.update({"id": f"mat-{seed}-{i}", "izoh": "", "xatolar": {}, "avto": True})
    return out

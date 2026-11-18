"""Kirish imtihonining birinchi 10 ta savoli uchun: juda SODDA, bir qadamli, bir-biriga o'xshamagan savollar banki (500 ta).
Har shablon — alohida kichik bilim (bir qadam). Bank deterministik: bir xil id har doim bir xil savol."""
import math
import random
from fractions import Fraction

from modules.mock_lib import M, fx, yopiq

SH = []   # (nom, funksiya)


def sh(nom):
    def d(f):
        SH.append((nom, f)); return f
    return d


def R(rng, a, b): return rng.randint(a, b)


@sh("qo'shish")
def _(g): a, b = R(g, 12, 89), R(g, 11, 59); return yopiq(g, f"${a}+{b}$ ni hisoblang.", a + b, [f"Qo‘shish: ${a}+{b}={a + b}$."])
@sh("ayirish")
def _(g): a, b = R(g, 40, 99), R(g, 11, 39); return yopiq(g, f"${a}-{b}$ ni hisoblang.", a - b, [f"Ayirish: ${a}-{b}={a - b}$."])
@sh("ko'paytirish")
def _(g): a, b = R(g, 3, 12), R(g, 3, 12); return yopiq(g, f"${a}\\cdot {b}$ ni hisoblang.", a * b, [f"Ko‘paytirish jadvali: ${a}\\cdot {b}={a * b}$."])
@sh("bo'lish")
def _(g): b, c = R(g, 3, 12), R(g, 3, 12); return yopiq(g, f"${b * c}:{b}$ ni hisoblang.", c, [f"${b}\\cdot {c}={b * c}$ bo‘lgani uchun ${b * c}:{b}={c}$."])
@sh("kasr qo'shish")
def _(g): d = R(g, 3, 9); a, b = R(g, 1, d - 2), R(g, 1, 2); return yopiq(g, f"$\\frac{{{a}}}{{{d}}}+\\frac{{{b}}}{{{d}}}$ ni hisoblang.", Fraction(a + b, d), ["Maxrajlar teng bo‘lsa, suratlar qo‘shiladi, maxraj o‘zgarmaydi: $\\frac{a}{c}+\\frac{b}{c}=\\frac{a+b}{c}$.", f"$\\frac{{{a}+{b}}}{{{d}}}={fx(Fraction(a + b, d))}$."])
@sh("kasr qisqartirish")
def _(g): k, a, b = R(g, 2, 7), R(g, 1, 5), R(g, 6, 9); return yopiq(g, f"$\\frac{{{a * k}}}{{{b * k}}}$ kasrni qisqartiring (qiymatini toping).", Fraction(a, b), [f"Surat va maxrajni ${k}$ ga bo‘lamiz: $\\frac{{{a * k}:{k}}}{{{b * k}:{k}}}={fx(Fraction(a, b))}$."])
@sh("foiz")
def _(g): p = g.choice([10, 20, 25, 50]); n = g.choice([40, 60, 80, 120, 200]); return yopiq(g, f"{n} ning {p}% i nechaga teng?", n * p // 100, ["Foiz: son $\\cdot \\frac{p}{100}$.", f"${n}\\cdot \\frac{{{p}}}{{100}}={n * p // 100}$."])
@sh("tenglama x+a")
def _(g): x, a = R(g, 3, 30), R(g, 2, 25); return yopiq(g, f"$x+{a}={x + a}$ tenglamani yeching.", x, [f"Noma’lum qo‘shiluvchi: $x={x + a}-{a}={x}$."])
@sh("tenglama ax")
def _(g): x, a = R(g, 2, 15), R(g, 2, 9); return yopiq(g, f"${a}x={a * x}$ tenglamani yeching.", x, [f"Ikki tomonni ${a}$ ga bo‘lamiz: $x=\\frac{{{a * x}}}{{{a}}}={x}$."])
@sh("kvadrat")
def _(g): a = R(g, 3, 15); return yopiq(g, f"${a}^2$ ni hisoblang.", a * a, [f"$a^2=a\\cdot a$: ${a}\\cdot {a}={a * a}$."])
@sh("kvadrat ildiz")
def _(g): a = R(g, 3, 15); return yopiq(g, f"$\\sqrt{{{a * a}}}$ ni hisoblang.", a, [f"${a}^2={a * a}$ bo‘lgani uchun $\\sqrt{{{a * a}}}={a}$."])
@sh("daraja")
def _(g): a, n = g.choice([2, 3, 5]), R(g, 2, 4); return yopiq(g, f"${a}^{n}$ ni hisoblang.", a ** n, [f"${a}^{n}$ — ${a}$ ni ${n}$ marta o‘ziga ko‘paytirish: ${a ** n}$."])
@sh("o'rta arifmetik")
def _(g): a = R(g, 4, 40); d = R(g, 1, 10) * 2; return yopiq(g, f"{a} va {a + d} sonlarining o‘rta arifmetigi nechaga teng?", a + d // 2, [f"$\\frac{{{a}+{a + d}}}{{2}}={a + d // 2}$."])
@sh("kvadrat perimetri")
def _(g): a = R(g, 3, 20); return yopiq(g, f"Kvadratning tomoni {a} sm. Perimetri necha sm?", 4 * a, [f"$P=4a=4\\cdot {a}={4 * a}$."])
@sh("to'g'ri to'rtburchak yuzi")
def _(g): a, b = R(g, 3, 15), R(g, 3, 15); return yopiq(g, f"To‘g‘ri to‘rtburchakning tomonlari {a} sm va {b} sm. Yuzi necha sm²?", a * b, [f"$S=a\\cdot b={a}\\cdot {b}={a * b}$."])
@sh("kvadrat yuzi")
def _(g): a = R(g, 3, 16); return yopiq(g, f"Kvadratning tomoni {a}. Yuzini toping.", a * a, [f"$S=a^2={a}^2={a * a}$."])
@sh("uchburchak burchagi")
def _(g): a, b = R(g, 30, 80), R(g, 30, 70); return yopiq(g, f"Uchburchakning ikki burchagi {a}° va {b}°. Uchinchi burchagi necha gradus?", 180 - a - b, [f"Uchburchak burchaklari yig‘indisi $180^\\circ$: $180-{a}-{b}={180 - a - b}$."])
@sh("to'ldiruvchi burchak")
def _(g): a = R(g, 15, 80); return yopiq(g, f"Burchak {a}° bo‘lsa, uni $90^\\circ$ gacha to‘ldiruvchi burchak necha gradus?", 90 - a, [f"$90-{a}={90 - a}$."])
@sh("qo'shni burchak")
def _(g): a = R(g, 30, 150); return yopiq(g, f"Burchak {a}° bo‘lsa, unga qo‘shni burchak necha gradus?", 180 - a, [f"Qo‘shni burchaklar yig‘indisi $180^\\circ$: $180-{a}={180 - a}$."])
@sh("to'g'ri to'rtburchak perimetri")
def _(g): a, b = R(g, 3, 15), R(g, 3, 15); return yopiq(g, f"To‘g‘ri to‘rtburchakning tomonlari {a} va {b}. Perimetrini toping.", 2 * (a + b), [f"$P=2(a+b)=2({a}+{b})={2 * (a + b)}$."])
@sh("EKUK")
def _(g): a, b = g.choice([(4, 6), (6, 9), (4, 10), (6, 8), (3, 5), (8, 12), (5, 10), (9, 12)]); return yopiq(g, f"{a} va {b} sonlarining EKUK i nechaga teng?", a * b // math.gcd(a, b), [f"Ikkalasiga bo‘linadigan eng kichik son: ${a * b // math.gcd(a, b)}$."])
@sh("EKUB")
def _(g): a, b = g.choice([(12, 18), (8, 12), (15, 20), (14, 21), (16, 24), (18, 27), (20, 30)]); return yopiq(g, f"{a} va {b} sonlarining EKUB i nechaga teng?", math.gcd(a, b), [f"Ikkalasini bo‘ladigan eng katta son: ${math.gcd(a, b)}$."])
@sh("manfiy sonlar")
def _(g): a, b = R(g, 2, 12), R(g, 13, 25); return yopiq(g, f"${-a}+{b}$ ni hisoblang.", b - a, [f"${-a}+{b}={b}-{a}={b - a}$."], tartib=True)
@sh("manfiy ko'paytirish")
def _(g): a, b = R(g, 2, 9), R(g, 2, 9); return yopiq(g, f"$(-{a})\\cdot {b}$ ni hisoblang.", -a * b, ["Manfiy son musbatga ko‘paytirilsa — natija manfiy.", f"$-{a}\\cdot {b}={-a * b}$."])
@sh("amallar tartibi")
def _(g): a, b, c = R(g, 2, 9), R(g, 2, 9), R(g, 2, 9); return yopiq(g, f"${a}+{b}\\cdot {c}$ ni hisoblang.", a + b * c, ["Avval ko‘paytirish, keyin qo‘shish.", f"${b}\\cdot {c}={b * c}$, ${a}+{b * c}={a + b * c}$."])
@sh("o'nli kasr qo'shish")
def _(g): a, b = R(g, 11, 49) / 10, R(g, 11, 39) / 10; s = Fraction(round(a * 10) + round(b * 10), 10); return yopiq(g, f"${a:g}+{b:g}$ ni hisoblang.".replace(".", ","), f"{float(s):g}".replace(".", ","), [f"${a:g}+{b:g}={float(s):g}$.".replace(".", ",")]) if False else yopiq(g, f"${str(a).replace('.', ',')}+{str(b).replace('.', ',')}$ ni hisoblang.", s, [f"Verguldan keyingi raqamlar tagma-tag: ${float(s):g}$.".replace(".", ",")])
@sh("10 ga ko'paytirish")
def _(g): a = R(g, 12, 99); return yopiq(g, f"${a}\\cdot 100$ ni hisoblang.", a * 100, ["100 ga ko‘paytirganda songa ikkita nol qo‘shiladi.", f"${a}\\cdot 100={a * 100}$."])
@sh("uzunlik birligi")
def _(g): a = R(g, 2, 9); return yopiq(g, f"{a} m necha sm?", a * 100, ["1 m = 100 sm.", f"${a}\\cdot 100={a * 100}$."])
@sh("massa birligi")
def _(g): a = R(g, 2, 9); return yopiq(g, f"{a} kg necha gramm?", a * 1000, ["1 kg = 1000 g.", f"${a}\\cdot 1000={a * 1000}$."])
@sh("vaqt birligi")
def _(g): a = R(g, 2, 9); return yopiq(g, f"{a} daqiqa necha sekund?", a * 60, ["1 daqiqa = 60 sekund.", f"${a}\\cdot 60={a * 60}$."])
@sh("masofa")
def _(g): v, t = R(g, 20, 80), R(g, 2, 6); return yopiq(g, f"Avtomobil {v} km/soat tezlik bilan {t} soat yurdi. Necha km yo‘l bosdi?", v * t, ["Yo‘l $S=v\\cdot t$.", f"${v}\\cdot {t}={v * t}$."])
@sh("tezlik")
def _(g): v, t = R(g, 20, 70), R(g, 2, 6); return yopiq(g, f"{v * t} km yo‘lni {t} soatda bosib o‘tgan velosipedchining tezligi (km/soat) qancha?", v, ["Tezlik $v=\\frac{S}{t}$.", f"$\\frac{{{v * t}}}{{{t}}}={v}$."])
@sh("nisbat")
def _(g): k, a, b = R(g, 2, 8), g.choice([1, 2, 3]), g.choice([4, 5, 7]); return yopiq(g, f"{a * k} : {b * k} nisbatni eng sodda ko‘rinishda yozing (birinchi son nechaga teng?).", a, [f"Ikkalasini ${k}$ ga bo‘lamiz: ${a}:{b}$. Birinchi son ${a}$."]) if False else yopiq(g, f"$\\frac{{{a * k}}}{{{b * k}}}$ nisbat $a:b$ ko‘rinishida eng sodda yozilganda $a+b$ necha bo‘ladi?", a + b, [f"Ikkalasini ${k}$ ga bo‘lamiz: ${a}:{b}$.", f"${a}+{b}={a + b}$."])
@sh("proporsiya")
def _(g): a, b, k = R(g, 2, 6), R(g, 2, 6), R(g, 2, 5); return yopiq(g, f"$\\frac{{{a}}}{{{b}}}=\\frac{{x}}{{{b * k}}}$ proporsiyada $x$ ni toping.", a * k, [f"Chetki hadlar ko‘paytmasi = o‘rtalar ko‘paytmasi: $x={a}\\cdot {b * k}:{b}={a * k}$."])
@sh("ifoda qiymati")
def _(g): a, x, b = R(g, 2, 6), R(g, 2, 9), R(g, 1, 9); return yopiq(g, f"$x={x}$ bo‘lsa, ${a}x+{b}$ ning qiymati nechaga teng?", a * x + b, [f"$x$ o‘rniga ${x}$ ni qo‘yamiz: ${a}\\cdot {x}+{b}={a * x + b}$."])
@sh("qavsni ochish")
def _(g): a, b, c = R(g, 2, 7), R(g, 2, 9), R(g, 2, 9); return yopiq(g, f"${a}({b}+{c})$ ni hisoblang.", a * (b + c), [f"${a}({b}+{c})={a}\\cdot {b + c}={a * (b + c)}$."])
@sh("funksiya qiymati")
def _(g): k, b, x = R(g, 2, 5), R(g, 1, 9), R(g, 2, 6); return yopiq(g, f"$f(x)={k}x+{b}$ bo‘lsa, $f({x})$ ni toping.", k * x + b, [f"$f({x})={k}\\cdot {x}+{b}={k * x + b}$."])
@sh("medianа")
def _(g): a = sorted(g.sample(range(2, 30), 3)); return yopiq(g, f"{a[2]}, {a[0]}, {a[1]} sonlarining medianasi (o‘rtadagi qiymati) nechaga teng?", a[1], ["Sonlarni o‘sish tartibida yozamiz va o‘rtadagisini olamiz.", f"${a[0]},\\ {a[1]},\\ {a[2]}$ → ${a[1]}$."])
@sh("aylana diametri")
def _(g): r = R(g, 2, 15); return yopiq(g, f"Aylana radiusi {r} bo‘lsa, diametri nechaga teng?", 2 * r, [f"$d=2r=2\\cdot {r}={2 * r}$."])
@sh("gipotenuza")
def _(g): a, b, c = g.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13)]); return yopiq(g, f"To‘g‘ri burchakli uchburchakning katetlari {a} va {b}. Gipotenuzasini toping.", c, [f"Pifagor teoremasi: $c^2=a^2+b^2={a * a}+{b * b}={c * c}$, $c={c}$."])
@sh("foizga oshirish")
def _(g): n, p = g.choice([100, 200, 50, 400]), g.choice([10, 20, 50]); return yopiq(g, f"{n} soni {p}% ga oshirilsa, necha bo‘ladi?", n + n * p // 100, [f"{p}% = ${n * p // 100}$. ${n}+{n * p // 100}={n + n * p // 100}$."])
@sh("chegirma")
def _(g): n, p = g.choice([100, 200, 400, 500, 1000]), g.choice([10, 20, 25, 50]); return yopiq(g, f"Narxi {n} so‘m bo‘lgan mahsulotga {p}% chegirma berildi. Yangi narxi necha so‘m?", n - n * p // 100, [f"Chegirma: ${n * p // 100}$. ${n}-{n * p // 100}={n - n * p // 100}$."])
@sh("modul")
def _(g): a = R(g, 2, 30); return yopiq(g, f"$|{-a}|$ ning qiymatini toping.", a, ["Modul — sonning noldan masofasi, u manfiy bo‘lmaydi."])
@sh("tenglama x/a")
def _(g): a, x = R(g, 2, 9), R(g, 2, 12); return yopiq(g, f"$\\frac{{x}}{{{a}}}={x}$ — bu tenglama noto‘g‘ri; $\\frac{{x}}{{{a}}}={x}$ emas.".replace("— bu tenglama noto‘g‘ri; $\\frac{x}{" + str(a) + "}=" + str(x) + "$ emas.", ""), a * x, [f"Ikki tomonni ${a}$ ga ko‘paytiramiz: $x={x}\\cdot {a}={a * x}$."]) if False else yopiq(g, f"$\\frac{{x}}{{{a}}}={x}$ tenglamani yeching.", a * x, [f"Ikki tomonni ${a}$ ga ko‘paytiramiz: $x={x}\\cdot {a}={a * x}$."])
@sh("nol daraja")
def _(g): a = R(g, 2, 20); return yopiq(g, f"${a}^0$ ni hisoblang.", 1, ["Noldan farqli sonning 0-darajasi 1 ga teng."], noto=[0, a, 2])
@sh("daraja ko'paytma")
def _(g): m, n = R(g, 2, 6), R(g, 2, 6); return yopiq(g, f"$2^{m}\\cdot 2^{n}=2^x$ bo‘lsa, $x$ nechaga teng?", m + n, ["Asoslari teng darajalar ko‘paytirilsa, ko‘rsatkichlar qo‘shiladi: $a^m\\cdot a^n=a^{m+n}$.", f"${m}+{n}={m + n}$."])
@sh("logarifm")
def _(g): a, n = g.choice([2, 3, 5, 10]), R(g, 2, 4); return yopiq(g, f"$\\log_{{{a}}}{a ** n}$ ni hisoblang.", n, [f"${a}^{n}={a ** n}$ bo‘lgani uchun $\\log_{{{a}}}{a ** n}={n}$."])
@sh("trigonometriya")
def _(g): f, v = g.choice([("\\sin30^\\circ", Fraction(1, 2)), ("\\cos60^\\circ", Fraction(1, 2)), ("\\operatorname{tg}45^\\circ", 1), ("\\sin90^\\circ", 1), ("\\cos0^\\circ", 1), ("\\sin0^\\circ", 0)]); return yopiq(g, f"${f}$ ning qiymatini toping.", v, ["Jadval qiymati: yodlab olinadigan bir qadamli qiymat."], noto=[Fraction(1, 2), 1, 0, 2, Fraction(1, 3)])
@sh("hosila")
def _(g): n, x = R(g, 2, 4), R(g, 1, 3); return yopiq(g, f"$f(x)=x^{n}$ bo‘lsa, $f'({x})$ ni toping.", n * x ** (n - 1), [f"$(x^n)'=nx^{{n-1}}$, shuning uchun $f'(x)={n}x^{{{n - 1}}}$.", f"$f'({x})={n * x ** (n - 1)}$."])
@sh("integral")
def _(g): k = R(g, 1, 6); return yopiq(g, f"$\\int_0^1 {2 * k}x\\,dx$ ni hisoblang.", k, [f"$\\int {2 * k}x\\,dx={k}x^2$, $x=1$ da ${k}$, $x=0$ da $0$.", f"${k}-0={k}$."])
@sh("arifmetik progressiya")
def _(g): a, d = R(g, 1, 9), R(g, 2, 6); return yopiq(g, f"Arifmetik progressiyada $a_1={a}$, $d={d}$. $a_2$ ni toping.", a + d, [f"$a_2=a_1+d={a}+{d}={a + d}$."])
@sh("geometrik progressiya")
def _(g): b, q = R(g, 1, 5), R(g, 2, 4); return yopiq(g, f"Geometrik progressiyada $b_1={b}$, $q={q}$. $b_2$ ni toping.", b * q, [f"$b_2=b_1\\cdot q={b}\\cdot {q}={b * q}$."])
@sh("faktorial")
def _(g): n = R(g, 3, 6); return yopiq(g, f"${n}!$ ni hisoblang.", math.factorial(n), [f"${n}!=" + "\\cdot ".join(str(i) for i in range(1, n + 1)) + f"={math.factorial(n)}$."])
@sh("kombinatsiya")
def _(g): n, k = R(g, 4, 7), 2; return yopiq(g, f"${n}$ ta elementdan 2 tadan nechta kombinatsiya tuzish mumkin ($C_{{{n}}}^2$)?", math.comb(n, 2), [f"$C_n^2=\\frac{{n(n-1)}}{{2}}=\\frac{{{n}\\cdot {n - 1}}}{{2}}={math.comb(n, 2)}$."])
@sh("ehtimol tanga")
def _(g): return yopiq(g, "Tanga tashlandi. Gerb tushish ehtimoli nechaga teng?", Fraction(1, 2), ["Ikki teng imkoniyat (gerb yoki raqam), qulayi 1 ta: $\\frac{1}{2}$."], noto=[Fraction(1, 3), 1, Fraction(1, 4)])
@sh("ehtimol kub")
def _(g): k = R(g, 1, 5); return yopiq(g, f"O‘yin kubigi tashlandi. {k} dan kichik son tushish ehtimoli nechaga teng?", Fraction(k - 1, 6), [f"Barcha natijalar 6 ta; qulayi: ${k - 1}$ ta. $P=\\frac{{{k - 1}}}{{6}}={fx(Fraction(k - 1, 6))}$."], noto=[Fraction(k, 6), Fraction(k + 1, 6), Fraction(1, 2) if k != 4 else Fraction(1, 3)]) if k > 1 else yopiq(g, "O‘yin kubigi tashlandi. Juft son tushish ehtimoli nechaga teng?", Fraction(1, 2), ["Juft sonlar 2, 4, 6 — 3 ta; jami 6 ta: $\\frac{3}{6}=\\frac{1}{2}$."])
@sh("o'xshash to'plamlar")
def _(g): a, b = R(g, 5, 20), R(g, 5, 20); return yopiq(g, f"Ikki to‘plam kesishmaydi: birinchisida {a} ta, ikkinchisida {b} ta element. Birlashmada nechta element bor?", a + b, [f"Kesishmasa, elementlar soni qo‘shiladi: ${a}+{b}={a + b}$."])
@sh("qoldiq")
def _(g): d = R(g, 3, 9); q = R(g, 3, 9); r = R(g, 1, d - 1); return yopiq(g, f"${d * q + r}$ ni ${d}$ ga bo‘lganda qoldiq nechaga teng?", r, [f"${d * q + r}={d}\\cdot {q}+{r}$, demak qoldiq ${r}$."], noto=[0, d - 1 if d - 1 != r else d - 2, r + 1])
@sh("raqamlar yig'indisi")
def _(g): a = R(g, 100, 999); return yopiq(g, f"{a} sonining raqamlari yig‘indisi nechaga teng?", sum(map(int, str(a))), [" + ".join(str(a)) + f" = {sum(map(int, str(a)))}"])
@sh("yaxlitlash")
def _(g): a = R(g, 21, 99) + g.choice([.3, .4, .6, .7]); return yopiq(g, f"${str(a).replace('.', ',')}$ sonini butun songacha yaxlitlang.", round(a), ["Verguldan keyingi raqam 5 dan kichik bo‘lsa — pastga, katta bo‘lsa — yuqoriga yaxlitlanadi."])
@sh("tub son")
def _(g): n = g.choice([11, 13, 17, 19, 23, 29, 31, 37, 41, 43]); return yopiq(g, "Quyidagi sonlardan qaysi biri tub?", n, ["Tub son faqat 1 ga va o‘ziga bo‘linadi; qolganlari boshqa songa ham bo‘linadi."], noto=g.sample([9, 15, 21, 25, 27, 33, 35, 39, 45, 49, 51, 55], 3))
@sh("juft sonlar")
def _(g): a = R(g, 3, 9); return yopiq(g, f"1 dan {2 * a} gacha (shu jumladan) nechta juft natural son bor?", a, [f"Juft sonlar: 2, 4, …, {2 * a}. Ularning soni ${2 * a}:2={a}$."])
@sh("kub hajmi")
def _(g): a = R(g, 2, 8); return yopiq(g, f"Qirrasi {a} bo‘lgan kubning hajmi nechaga teng?", a ** 3, [f"$V=a^3={a}^3={a ** 3}$."])
@sh("parallelepiped")
def _(g): a, b, c = R(g, 2, 8), R(g, 2, 8), R(g, 2, 6); return yopiq(g, f"To‘g‘ri burchakli parallelepipedning o‘lchamlari {a}, {b}, {c}. Hajmini toping.", a * b * c, [f"$V=abc={a}\\cdot {b}\\cdot {c}={a * b * c}$."])
@sh("uchburchak yuzi")
def _(g): a, h = R(g, 4, 20) * 2, R(g, 3, 12); return yopiq(g, f"Uchburchakning asosi {a}, balandligi {h}. Yuzini toping.", a * h // 2, [f"$S=\\frac{{1}}{{2}}ah=\\frac{{1}}{{2}}\\cdot {a}\\cdot {h}={a * h // 2}$."])
@sh("to'rtburchak burchaklari")
def _(g): a, b, c = R(g, 60, 110), R(g, 70, 100), R(g, 60, 100); return yopiq(g, f"Qavariq to‘rtburchakning uch burchagi {a}°, {b}°, {c}°. To‘rtinchi burchagi necha gradus?", 360 - a - b - c, [f"To‘rtburchak burchaklari yig‘indisi $360^\\circ$: $360-{a}-{b}-{c}={360 - a - b - c}$."]) if 360 - a - b - c > 0 else yopiq(g, "Qavariq to‘rtburchak burchaklari yig‘indisi necha gradus?", 360, ["Uni ikki uchburchakka ajratamiz: $2\\cdot 180^\\circ=360^\\circ$."], noto=[180, 270, 540])
@sh("vertikal burchaklar")
def _(g): a = R(g, 20, 80); return yopiq(g, f"Ikki to‘g‘ri chiziq kesishganda hosil bo‘lgan vertikal burchaklardan biri {a}°. Unga vertikal bo‘lgan burchak necha gradus?", a, ["Vertikal burchaklar o‘zaro teng."])


def _tuz():
    """500 ta savol: shablonlarni aylanma tartibda, har biridan ~8 xil parametr bilan."""
    out, korildi = [], set()
    per = {}
    tur = 0
    while len(out) < 500 and tur < 4000:
        nom, f = SH[tur % len(SH)]
        k = per.get(nom, 0); per[nom] = k + 1
        tur += 1
        try:
            q = f(random.Random(f"oddiy:{nom}:{k}"))
        except Exception:   # noqa: BLE001
            continue
        kal = q["savol"] + "|".join(q["variantlar"])
        if kal in korildi:
            continue
        korildi.add(kal)
        out.append(dict(q, mavzu=None, nom=nom, id=f"S{len(out) + 1:03d}"))
    return out


_B = {"l": None, "d": None}


def bank():
    if _B["l"] is None:
        _B["l"] = _tuz()
        _B["d"] = {q["id"]: q for q in _B["l"]}
    return _B["l"]


def ol(sid):
    bank()
    return _B["d"].get(sid)


def oddiy_10(rng):
    """10 ta savol: 10 xil shablondan (bir-biriga o'xshamaydi)."""
    b = bank()
    shuf = b[:]
    rng.shuffle(shuf)
    out, nomlar = [], set()
    for q in shuf:
        if q["nom"] in nomlar:
            continue
        nomlar.add(q["nom"]); out.append(q)
        if len(out) == 10:
            break
    return out

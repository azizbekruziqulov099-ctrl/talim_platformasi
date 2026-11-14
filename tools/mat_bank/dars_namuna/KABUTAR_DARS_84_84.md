# DARS: 84 | ANIQ INTEGRAL

## MAQSAD
Bu darsdan keyin siz aniq integralning geometrik ma'nosini (egri chiziq ostidagi yuza) tushunasiz, Nyuton–Leybnits formulasi bilan integralni hisoblaysiz, modulli va trigonometrik funksiyalarning integrallarini topasiz.

## OLDIN BIL
- Boshlang'ich funksiya: $F'(x) = f(x)$ (82-mavzu).
- Asosiy boshlang'ich funksiyalar: $x^{n}$ uchun $\frac{x^{n+1}}{n+1}$, $\sin x$ uchun $-\cos x$, $\cos x$ uchun $\sin x$ (83-mavzu).
- Qavsni ochish: $(a + b)^{2} = a^{2} + 2ab + b^{2}$.

## TUSHUNCHA
### 1. Aniq integralning geometrik ma'nosi
Agar $[a;b]$ kesmada $f(x) \geq 0$ bo'lsa, $\int_{a}^{b} f(x)\, dx$ — $y = f(x)$ grafigi, $Ox$ o'qi va $x = a$, $x = b$ to'g'ri chiziqlari bilan chegaralangan shaklning yuziga teng. Quyidagi doskada o'zingiz sinab ko'ring: funksiyani va chegaralarni o'zgartiring, yuza va uning qiymati darhol o'zgaradi.

[[INTEGRAL: x^2 | 0..2 | -1..3 | -1..5]]

### 2. Nyuton–Leybnits formulasi
$f(x)$ funksiya $[a;b]$ kesmada uzluksiz va $F'(x) = f(x)$ bo'lsa:

$$\int_{a}^{b} f(x)\, dx = F(b) - F(a).$$

Bu yerda $F$ — $f$ ning ixtiyoriy boshlang'ich funksiyasi; doimiy $C$ ayirishda yo'qoladi, shuning uchun uni yozish shart emas.

### 3. Asosiy xossalar
1. $\int_{a}^{a} f(x)\, dx = 0$.
2. $\int_{a}^{b} f(x)\, dx = - \int_{b}^{a} f(x)\, dx$.
3. $\int_{a}^{b} f(x)\, dx = \int_{a}^{c} f(x)\, dx + \int_{c}^{b} f(x)\, dx$.
4. Chiziqlilik: $\int_{a}^{b} \left( \alpha f(x) + \beta g(x) \right) dx = \alpha \int_{a}^{b} f(x)\, dx + \beta \int_{a}^{b} g(x)\, dx$. Ya'ni doimiy ko'paytuvchi integral belgisidan chiqadi, yig'indining integrali integrallar yig'indisiga teng.
5. Agar $[a;b]$ kesmada $f(x) \geq 0$ bo'lsa, $\int_{a}^{b} f(x)\, dx \geq 0$.

### 4. Ko'p ishlatiladigan formulalar
1. $\int_{a}^{b} x^{n}\, dx = \frac{b^{n+1} - a^{n+1}}{n + 1}$ ($n \neq -1$).
2. $\int_{a}^{b} \sin x\, dx = \cos a - \cos b$ va $\int_{a}^{b} \cos x\, dx = \sin b - \sin a$.
3. $\int_{a}^{b} \frac{dx}{x} = \ln \left| \frac{b}{a} \right|$ ($a$ va $b$ bir xil ishorali).
4. $k \neq 0$ bo'lganda:

$$\int_{a}^{b} \sin kx\, dx = \left[ -\frac{\cos kx}{k} \right]_{a}^{b}, \quad \int_{a}^{b} \cos kx\, dx = \left[ \frac{\sin kx}{k} \right]_{a}^{b}.$$

$$\int_{a}^{b} \frac{dx}{\cos^{2} kx} = \left[ \frac{\operatorname{tg} kx}{k} \right]_{a}^{b}, \quad \int_{a}^{b} \frac{dx}{\sin^{2} kx} = \left[ -\frac{\operatorname{ctg} kx}{k} \right]_{a}^{b}.$$

Misol uchun $\sin x$ ning $0$ dan $\pi$ gacha bo'lgan yuzi aynan $2$ ga teng:

[[INTEGRAL: sin(x) | 0..3.1416 | -1..7 | -2..2]]

### 5. Modulli integral
$|f(x)|$ qatnashsa, modul ichidagi ifoda ishorasini o'zgartiradigan nuqtalarda oraliqni bo'lamiz: $f(x) \geq 0$ bo'lgan joyda $|f(x)| = f(x)$, $f(x) < 0$ bo'lgan joyda $|f(x)| = - f(x)$. Grafikda modul pastdagi qismni yuqoriga "buklaydi":

[[GRAFIK: abs(x-a) | a=2 | -1..5 | -1..4]]

### 6. Yuqori chegarasi o'zgaruvchi integral
Integralning yuqori chegarasi $x$ bo'lsa, u $x$ ning funksiyasi bo'ladi va uning hosilasi integral ostidagi funksiyaga teng:

$$\frac{d}{dx} \left( \int_{a}^{x} f(t)\, dt \right) = f(x).$$

### 7. Fizik ma'nosi: bosib o'tilgan yo'l
Nuqta $v(t)$ tezlik bilan harakat qilsa, $[t_{1}; t_{2}]$ vaqt oralig'ida bosib o'tilgan yo'l $S = \int_{t_{1}}^{t_{2}} |v(t)|\, dt$. Agar $v(t) \geq 0$ bo'lsa, modul belgisi kerak emas.

## MISOL TAHLILI
### Misol 1 | (97-3-31)
G'OYA: Qavsni ochib, har bir haddan boshlang'ich funksiya topamiz, keyin Nyuton–Leybnits formulasini qo'llaymiz.

1-qadam. $(3x - 1)^{2} = 9x^{2} - 6x + 1$.

2-qadam. Boshlang'ich funksiya: $F(x) = 3x^{3} - 3x^{2} + x$.

3-qadam. $F(1) - F(0) = (3 - 3 + 1) - 0 = 1$.

JAVOB: B

### Misol 2 | (96-9-82)
G'OYA: $\sin kx$ ning boshlang'ich funksiyasi $-\frac{\cos kx}{k}$ ekanini ishlatamiz.

1-qadam. $F(x) = -\frac{1}{2} \cos 2x$.

2-qadam. $F\left( \frac{\pi}{4} \right) = -\frac{1}{2} \cos\frac{\pi}{2} = 0$ va $F(0) = -\frac{1}{2} \cos 0 = -\frac{1}{2}$.

3-qadam. $F\left( \frac{\pi}{4} \right) - F(0) = 0 - \left( -\frac{1}{2} \right) = \frac{1}{2}$.

JAVOB: A

### Misol 3 | (97-1-62)
G'OYA: Avval berilgan oraliqda modul ichidagi ifodaning ishorasini aniqlaymiz.

1-qadam. $-1 \leq x \leq 2$ da $2 - x \geq 0$, shuning uchun $|2 - x| = 2 - x$.

2-qadam. Boshlang'ich funksiya: $F(x) = 2x - \frac{x^{2}}{2}$.

3-qadam. $F(2) = 4 - 2 = 2$ va $F(-1) = -2 - \frac{1}{2} = -2,5$.

4-qadam. $\int_{-1}^{2} |2 - x|\, dx = 2 - (-2,5) = 4,5$.

JAVOB: E

### Misol 4 | (96-1-31)
G'OYA: $\sin x$ ning boshlang'ich funksiyasi $-\cos x$.

1-qadam. $F(x) = -\cos x$.

2-qadam. $F\left( \frac{\pi}{2} \right) = -\cos\frac{\pi}{2} = 0$ va $F\left( \frac{\pi}{3} \right) = -\cos\frac{\pi}{3} = -\frac{1}{2}$.

3-qadam. $F\left( \frac{\pi}{2} \right) - F\left( \frac{\pi}{3} \right) = 0 - \left( -\frac{1}{2} \right) = \frac{1}{2}$.

JAVOB: C

### Misol 5 | (97-2-49)
G'OYA: $1 + \operatorname{tg}^{2} x = \frac{1}{\cos^{2} x}$ va $(\operatorname{tg} x)' = \frac{1}{\cos^{2} x}$, ya'ni integral ostidagi ifodaning boshlang'ich funksiyasi $\operatorname{tg} x$.

1-qadam. $F(x) = \operatorname{tg} x$.

2-qadam. $F\left( \frac{\pi}{4} \right) - F(0) = 1 - 0 = 1$.

JAVOB: B

## KO'P UCHRAYDIGAN XATOLAR
1. $x^{2}$ ning boshlang'ich funksiyasini $\frac{x^{2}}{2}$ yoki $2x$ deb olish. To'g'risi $\frac{x^{3}}{3}$: daraja bittaga oshadi va yangi daraja ko'rsatkichiga bo'linadi.
2. Chegaralarni teskari qo'yish: $F(a) - F(b)$ ishorani teskari qiladi. Doim $F(\text{yuqori}) - F(\text{quyi})$.
3. Modul ostidagi ifoda ishorasini tekshirmasdan integrallash: $|2 - x| = 2 - x$ faqat $x \leq 2$ bo'lgan oraliqda to'g'ri.
4. $\sin kx$ ni integrallashda $\frac{1}{k}$ ni unutish: $\int \sin 2x\, dx = -\frac{1}{2} \cos 2x$, $-\cos 2x$ emas.

## ESDA TUT
- $\int_{a}^{b} f(x)\, dx = F(b) - F(a)$, bunda $F' = f$.
- $\int x^{n}\, dx \to \frac{x^{n+1}}{n+1}$, $\int \sin x\, dx \to -\cos x$, $\int \cos x\, dx \to \sin x$.
- $\int \sin kx\, dx \to -\frac{\cos kx}{k}$, $\int \cos kx\, dx \to \frac{\sin kx}{k}$.
- Modul bo'lsa: ishora o'zgaradigan nuqtada oraliqni bo'ling.

## MATEMATIKA TARIXI
Egri chiziqli shakllarning yuzini hisoblash masalasi qadimdan ma'lum: qadimgi yunon olimi Arximed (miloddan avvalgi III asr) parabola kesmasining yuzini «tugatish usuli» bilan topgan. XVII asrda Isaak Nyuton (1643–1727) va Gotfrid Vilgelm Leybnits (1646–1716) bir-biridan mustaqil ravishda hosila va integral hisobini yaratib, ularning o'zaro bog'liqligini ko'rsatdilar: bu bog'lanish bugungi Nyuton–Leybnits formulasidir. Integral belgisi $\int$ ni Leybnits kiritgan: u lotincha «summa» so'zining cho'zilgan «S» harfidan olingan. «Integral» atamasini esa Yakob Bernulli (1690-yil) qo'llagan.

## O'ZINI TEKSHIR
(97-7-31) (97-10-31) (97-6-63) (96-10-33)

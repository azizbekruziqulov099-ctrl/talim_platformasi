"""REV121: «Mantiq» fani — bog'cha uchun aqlli o'yinlar kitobi (2-3, 4-5, 6-7 yosh), uch tilda birdaniga.

Har yoshda 5 xil mantiqiy o'yin (bo'lim), har biri bir nechta darsdan:
  2-3 yosh: bir xilini top · nima bilan nima · katta-kichik / og'ir-yengil · AB naqsh · 3 tadan ortiqchasi
  4-5 yosh: AB/ABB/AAB/ABC naqsh · 4 tadan ortiqchasi (belgisi bo'yicha) · bog'liqlik (uy, kasb, mahsulot)
            · avval-keyin (ketma-ketlik) · diqqat: nima yo'qoldi?
  6-7 yosh: murakkab va sonli naqshlar · ortiqchasi va sababi · o'xshatish (analogiya) · sabab-natija, 3 qadamli
            ketma-ketlik · mantiqiy savollar, tarozi, topishmoqlar
Savolda rasmlar (emoji) bor — bola ularni ko'rib o'ylaydi; variant — «emoji so'z».

Kitob o'zbekcha yoziladi (bogcha_content/mn_<yosh>.json, til kitoblari kabi), rus va ingliz izohi uchun har matnning
tarjimasi shu yerning o'zida (T(uz, ru, en)) — izoh/ru.json, izoh/en.json ga qo'shiladi (kalit = sid(o'zbekcha)).

Ishlatish: python tools/bogcha_mantiq.py
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.bogcha_spiral import sid, validate  # noqa: E402

ROOT = Path(__file__).resolve().parent / "bogcha_content"
IZOH = ROOT / "izoh"
TR = {}     # o'zbekcha → (ru, en)


class T:
    """Uch tildagi matn. str(T) — o'zbekchasi (kitobga), tarjimasi TR ga yoziladi."""
    __slots__ = ("uz", "ru", "en")

    def __init__(self, uz, ru, en):
        self.uz, self.ru, self.en = uz, ru, en

    def f(self, **kw):
        return T(self.uz.format(**{k: (v.uz if isinstance(v, T) else v) for k, v in kw.items()}),
                 self.ru.format(**{k: (v.ru if isinstance(v, T) else v) for k, v in kw.items()}),
                 self.en.format(**{k: (v.en if isinstance(v, T) else v) for k, v in kw.items()}))

    def __add__(self, other):
        other = other if isinstance(other, T) else T(other, other, other)
        return T(self.uz + other.uz, self.ru + other.ru, self.en + other.en)

    def cap(self):
        c = lambda s: s[:1].upper() + s[1:]
        return T(c(self.uz), c(self.ru), c(self.en))

    def capuz(self):
        """Gap boshidagi nom: o'zbekcha va ruschada bosh harf, inglizchada «The {w}» shablonida kichik qoladi."""
        c = lambda s: s[:1].upper() + s[1:]
        return T(c(self.uz), c(self.ru), self.en)

    def put(self, strip=True):
        """Kitobga yoziladigan o'zbekcha matn; tarjima lug'atga tushadi."""
        key = self.uz.strip() if strip else self.uz
        old = TR.get(key)
        new = (self.ru.strip() if strip else self.ru, self.en.strip() if strip else self.en)
        if old and old != new:
            raise ValueError(f"Bir xil o'zbekcha matn — har xil tarjima: {key!r}: {old} / {new}")
        TR[key] = new
        return self.uz


# ── lug'at: kalit → emoji + uch tilda nomi ──
_V = """
mushuk 🐱 mushuk|кошка|cat
kuchuk 🐶 kuchuk|собачка|puppy
quyon 🐰 quyon|зайчик|bunny
ayiq 🐻 ayiq|медведь|bear
fil 🐘 fil|слон|elephant
sichqon 🐭 sichqon|мышка|mouse
baliq 🐟 baliq|рыбка|fish
qush 🐦 qushcha|птичка|bird
sigir 🐄 sigir|корова|cow
tovuq 🐔 tovuq|курица|hen
joja 🐥 jo'ja|цыплёнок|chick
ari 🐝 ari|пчела|bee
kapalak 🦋 kapalak|бабочка|butterfly
maymun 🐒 maymun|обезьянка|monkey
jirafa 🦒 jirafa|жираф|giraffe
qoy 🐑 qo'y|овечка|sheep
toshbaqa 🐢 toshbaqa|черепаха|turtle
ordak 🦆 o'rdak|утка|duck
pingvin 🐧 pingvin|пингвин|penguin
sher 🦁 sher|лев|lion
delfin 🐬 delfin|дельфин|dolphin
sakkizoyoq 🐙 sakkizoyoq|осьминог|octopus
boyqush 🦉 boyqush|сова|owl
tuya 🐫 tuya|верблюд|camel
qurt 🐛 qurtcha|гусеница|caterpillar
it 🐕 it|собака|dog
ot 🐴 ot|лошадь|horse
qurbaqa 🐸 qurbaqa|лягушка|frog
olma 🍎 olma|яблоко|apple
banan 🍌 banan|банан|banana
nok 🍐 nok|груша|pear
uzum 🍇 uzum|виноград|grapes
qulupnay 🍓 qulupnay|клубника|strawberry
tarvuz 🍉 tarvuz|арбуз|watermelon
gilos 🍒 gilos|вишня|cherry
sabzi 🥕 sabzi|морковка|carrot
bodring 🥒 bodring|огурец|cucumber
pomidor 🍅 pomidor|помидор|tomato
non 🍞 non|хлеб|bread
pishloq 🧀 pishloq|сыр|cheese
sut 🥛 sut|молоко|milk
tuxum 🥚 tuxum|яйцо|egg
asal 🍯 asal|мёд|honey
suyak 🦴 suyak|косточка|bone
yung 🧶 jun|шерсть|wool
mashina 🚗 mashina|машина|car
avtobus 🚌 avtobus|автобус|bus
poyezd 🚂 poyezd|поезд|train
samolyot ✈️ samolyot|самолёт|plane
velosiped 🚲 velosiped|велосипед|bike
qayiq ⛵ qayiq|лодка|boat
traktor 🚜 traktor|трактор|tractor
top ⚽ to'p|мяч|ball
ayiqcha 🧸 ayiqcha|мишка|teddy bear
shar 🎈 shar|шарик|balloon
koylak 👕 ko'ylak|футболка|T-shirt
shim 👖 shim|брюки|trousers
paypoq 🧦 paypoq|носок|sock
krossovka 👟 krossovka|кроссовка|sneaker
kepka 🧢 kepka|кепка|cap
qolqop 🧤 qo'lqop|варежка|mitten
sharf 🧣 sharf|шарф|scarf
kurtka 🧥 kurtka|куртка|jacket
shortik 🩳 shortik|шорты|shorts
kozoynak 🕶️ ko'zoynak|очки от солнца|sunglasses
qoshiq 🥄 qoshiq|ложка|spoon
likopcha 🍽️ likopcha|тарелка|plate
kosa 🥣 kosa|миска|bowl
kalit 🔑 kalit|ключ|key
qulf 🔒 qulf|замок|lock
qalam ✏️ qalam|карандаш|pencil
daftar 📒 daftar|тетрадь|notebook
chotka 🪥 tish cho'tkasi|зубная щётка|toothbrush
tish 🦷 tish|зуб|tooth
qaychi ✂️ qaychi|ножницы|scissors
qogoz 📄 qog'oz|бумага|paper
soyabon ☂️ soyabon|зонтик|umbrella
yomgir 🌧️ yomg'ir|дождь|rain
quyosh ☀️ quyosh|солнце|sun
oy 🌙 oy|луна|moon
yulduz ⭐ yulduz|звезда|star
qor ❄️ qor|снег|snow
gul 🌸 gul|цветок|flower
daraxt 🌳 daraxt|дерево|tree
nihol 🌱 nihol|росток|sprout
urug 🌰 urug'|семечко|seed
barg 🍃 barg|листок|leaf
uya 🪺 uya|гнездо|nest
dengiz 🌊 dengiz|море|sea
orm 🌲 o'rmon|лес|forest
chol 🏜️ cho'l|пустыня|desert
muz 🧊 muz|лёд|ice
suv 💧 suv|вода|water
olov 🔥 olov|огонь|fire
uy 🏠 uy|дом|house
eshik 🚪 eshik|дверь|door
gildirak 🛞 g'ildirak|колесо|wheel
tosh 🪨 tosh|камень|stone
pat 🪶 pat|пёрышко|feather
qizil 🔴 qizil doira|красный круг|red circle
kok 🔵 ko'k doira|синий круг|blue circle
sariq 🟡 sariq doira|жёлтый круг|yellow circle
yashil 🟢 yashil doira|зелёный круг|green circle
kvadrat 🟥 qizil kvadrat|красный квадрат|red square
kokkv 🟦 ko'k kvadrat|синий квадрат|blue square
uchburchak 🔺 uchburchak|треугольник|triangle
yurak ❤️ yurakcha|сердечко|heart
chapak 👏 chapak|хлопок|clap
dupur 🦶 dupur|топот|stomp
oshpaz 🧑‍🍳 oshpaz|повар|cook
tova 🍳 tova|сковорода|frying pan
otochir 🧑‍🚒 o't o'chiruvchi|пожарный|firefighter
otochirgich 🧯 o't o'chirgich|огнетушитель|fire extinguisher
dehqon 🧑‍🌾 dehqon|фермер|farmer
shifokor 🧑‍⚕️ shifokor|врач|doctor
stetoskop 🩺 stetoskop|стетоскоп|stethoscope
rassom 🧑‍🎨 rassom|художник|artist
moyqalam 🖌️ mo'yqalam|кисточка|paintbrush
qoshiqchi 🎤 mikrofon|микрофон|microphone
kitob 📚 kitob|книги|books
karavot 🛏️ karavot|кровать|bed
divan 🛋️ divan|диван|sofa
stul 🪑 stul|стул|chair
qaldirgoch 🐣 tuxumdan chiqqan jo'ja|вылупившийся цыплёнок|hatching chick
bugdoy 🌾 bug'doy|пшеница|wheat
lola 🌷 lola|тюльпан|tulip
kamalak 🌈 kamalak|радуга|rainbow
kolmak 💦 ko'lmak|лужа|puddle
soligan 🥀 so'lgan gul|увядший цветок|wilted flower
tong 🌅 tong|утро|morning
olma_gul 🌼 olma guli|цветок яблони|apple blossom
yashil_olma 🍏 xom olma|зелёное яблоко|green apple
sumka 🎒 sumka|рюкзак|backpack
quti 📦 quti|коробка|box
savat 🧺 savat|корзина|basket
bulut ☁️ bulut|облако|cloud
ha ✅ ha|да|yes
yoq ❌ yo'q|нет|no
tarozi ⚖️ tarozi|весы|scales
"""
V = {}
for line in _V.strip().splitlines():
    key, emoji, rest = line.split(" ", 2)
    uz, ru, en = rest.split("|")
    V[key] = (emoji, T(uz, ru, en))
NUM = {n: (e, T(uz, ru, en)) for n, e, uz, ru, en in [
    (1, "1️⃣", "bitta", "один", "one"), (2, "2️⃣", "ikkita", "два", "two"), (3, "3️⃣", "uchta", "три", "three"),
    (4, "4️⃣", "to'rtta", "четыре", "four"), (5, "5️⃣", "beshta", "пять", "five"), (6, "6️⃣", "oltita", "шесть", "six"),
    (7, "7️⃣", "yettita", "семь", "seven"), (8, "8️⃣", "sakkizta", "восемь", "eight"), (9, "9️⃣", "to'qqizta", "девять", "nine"),
    (10, "🔟", "o'nta", "десять", "ten")]}


def E(k):
    return V[k][0]


def W(k):
    return V[k][1]


def opt(k):
    """Test varianti: «🐱 mushuk». Tayyor T bo'lsa — o'zi."""
    if isinstance(k, T):
        return k
    e, w = V[k] if k in V else NUM[k]
    return T(f"{e} ", f"{e} ", f"{e} ") + w


def seq(keys):
    return "".join(E(k) for k in keys)


PRAISE = [T("Barakalla!", "Молодец!", "Well done!"), T("Ofarin!", "Умница!", "Great job!"),
          T("Qoyil!", "Здорово!", "Awesome!"), T("Zo'r!", "Супер!", "Super!"), T("To'g'ri!", "Верно!", "Right!")]


# ── kitob yig'uvchi ──
class Kitob:
    def __init__(self, age, label):
        self.age, self.label = age, label
        self.units = []
        self.rng = random.Random(f"mantiq|{age}")

    def unit(self, name, emoji):
        self.units.append({"name": name.put(), "emoji": emoji, "lessons": []})

    def lesson(self, name, goal, intro, items, tests, extra=()):
        les = {"name": name.put(), "goal": goal.put(), "intro": intro.put(), "items": [], "tests": [], "extra": []}
        for it in items:
            row = {"say": it["say"].put(False), "uz": it["uz"].put(False), "emoji": it["emoji"],
                   "explain": it["explain"].put(False)}
            if it.get("action"):
                row["action"] = it["action"].put(False)
            les["items"].append(row)
        for i, t in enumerate(tests):
            opts = [o.put() for o in t["options"]]
            right = opts[t["answer"]]
            # to'g'ri javob o'rni aralashtiriladi (bola doim birinchisini bosib o'rganib qolmasin)
            self.rng.shuffle(opts)
            les["tests"].append({"q": t["q"].put(), "options": opts, "answer": opts.index(right),
                                 "why": t["why"].put()})
        for r in extra:
            les["extra"].append({"turi": "topshiriq",   # harakatli o'yin ham topshiriq (yechim avtomatik)
                                  "sarlavha": r["sarlavha"].put(),
                                 "matn": r["matn"].put(),
                                 "doska": "\n".join(line.put() if isinstance(line, T) else line for line in r["doska"])})
        self.units[-1]["lessons"].append(les)

    def praise(self):
        return self.rng.choice(PRAISE)

    def book(self, n):
        return {"subject": "Mantiq", "lang": None, "age": self.age, "prefix": "MN",
                "book_title": T("Aqlli o'yinlar", "Умные игры", "Smart games").put() + " " + self.label,
                "units": self.units}


def item(say, uz, emoji, explain, action=None):
    return {"say": say, "uz": uz, "emoji": emoji, "explain": explain, "action": action}


def test(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


def row(sarlavha, matn, doska, turi="topshiriq"):
    return {"sarlavha": sarlavha, "matn": matn, "doska": doska, "turi": turi}


# ═════════════════════════════ 2–3 yosh ═════════════════════════════
def yosh23():
    k = Kitob("2-3 yosh", "2–3 yosh")
    T("2–3 yosh", "2–3 года", "2–3 years").put()

    # 1. Bir xilini top
    k.unit(T("Bir xilini top", "Найди такую же", "Find the same"), "🔍")
    sets = [
        (T("Bir xil hayvonchalar", "Одинаковые зверята", "Same little animals"), ["mushuk", "kuchuk", "quyon", "ayiq"]),
        (T("Bir xil mevalar", "Одинаковые фрукты", "Same fruits"), ["olma", "banan", "nok", "uzum"]),
        (T("Bir xil o'yinchoqlar", "Одинаковые игрушки", "Same toys"), ["top", "ayiqcha", "shar", "mashina"]),
        (T("Bir xil shakllar", "Одинаковые фигуры", "Same shapes"), ["qizil", "kokkv", "uchburchak", "yulduz"]),
    ]
    homes = [
        T("O'yin! Uyda ikkita bir xil narsa top: ikki qoshiq yoki ikki paypoq. Topsang — onangga ko'rsat!",
          "Игра! Найди дома две одинаковые вещи: две ложки или два носка. Нашёл — покажи маме!",
          "Game! Find two things at home that are the same: two spoons or two socks. Show them to your mom!"),
        T("O'yin! Kiyimingga qara: ikki yengi bir xilmi? Ikki oyog'ingdagi paypoq bir xilmi? Barmog'ing bilan ko'rsat!",
          "Игра! Посмотри на свою одежду: два рукава одинаковые? А носочки на ножках одинаковые? Покажи пальчиком!",
          "Game! Look at your clothes: are the two sleeves the same? Are your two socks the same? Point with your finger!"),
        T("O'yin! O'yinchoqlaringni yig'ib, bir xillarini yonma-yon qo'y. Qaysilarining jufti bor ekan?",
          "Игра! Собери свои игрушки и поставь одинаковые рядом. У каких игрушек есть пара?",
          "Game! Gather your toys and put the same ones side by side. Which toys have a pair?"),
        T("O'yin! Qo'llaringni ko'tar — ikkalasi bir xil! Endi oyoqlaringga qara — ular ham bir xil!",
          "Игра! Подними ручки — они одинаковые! А теперь посмотри на ножки — они тоже одинаковые!",
          "Game! Lift your hands — they are the same! Now look at your feet — they are the same too!"),
    ]
    for (name, keys), home in zip(sets, homes):
        a, b, c, d = keys
        k.lesson(name,
                 T("Bola bir xil rasmlarni topadi, «bir xil» va «har xil» so'zlarini tushunadi",
                   "Ребёнок находит одинаковые картинки, понимает слова «одинаковые» и «разные»",
                   "The child finds matching pictures and understands “the same” and “different”"),
                 T("Bip-bip! Bugun ko'zlarimiz sehrli! Qara: {s}. Ba'zi rasmlar egizakdek bir xil. Qani, ularni topamiz!",
                   "Бип-бип! Сегодня у нас волшебные глазки! Смотри: {s}. Некоторые картинки одинаковые, как близнецы. Давай их найдём!",
                   "Beep-beep! Today our eyes are magic! Look: {s}. Some pictures are the same, like twins. Let's find them!").f(s=E(a) + E(b) + E(a) + E(c)),
                 [item(T("Bir xil", "Одинаковые", "The same"), T("egizakdek o'xshash", "похожи, как близнецы", "alike, like twins"),
                       E(a) + E(a),
                       T("Qara: {e} {w} va yana {e} {w}. Ikkalasi bir xil — rangi ham, shakli ham bir xil! Bir xil narsalar xuddi egizaklardek.",
                         "Смотри: {e} {w} и ещё {e} {w}. Они одинаковые — и цвет, и форма одинаковые! Одинаковые вещи — как близнецы.",
                         "Look: {e} a {w} and another {e} {w}. They are the same — the same color and the same shape! Things that are the same are like twins.").f(e=E(a), w=W(a)),
                       T("Ikki kaftingni birlashtir — ular ham bir xil!", "Сложи ладошки вместе — они тоже одинаковые!",
                         "Put your palms together — they are the same too!")),
                  item(T("Har xil", "Разные", "Different"), T("bir-biriga o'xshamaydi", "не похожи друг на друга", "not alike"),
                       E(a) + E(b),
                       T("Endi qara: {ea} {wa} va {eb} {wb}. Ular har xil! Biri boshqasiga o'xshamaydi.",
                         "А теперь смотри: {ea} {wa} и {eb} {wb}. Они разные! Совсем не похожи друг на друга.",
                         "Now look: {ea} {wa} and {eb} {wb}. They are different! They don't look alike.").f(ea=E(a), wa=W(a), eb=E(b), wb=W(b)),
                       T("Boshingni chayqa: «Yo'q, bir xil emas!»", "Покачай головой: «Нет, не одинаковые!»",
                         "Shake your head: “No, not the same!”"))],
                 [test(T("{e} Xuddi shunday rasmni top!", "{e} Найди такую же картинку!", "{e} Find the same picture!").f(e=E(t)),
                       [opt(t), opt(o)], 0,
                       k.praise() + T(" {e} va {e} — bir xil.", " {e} и {e} — одинаковые.", " {e} and {e} are the same.").f(e=E(t)))
                  for t, o in ((a, b), (b, c), (c, d))],
                 [row(T("🧩 Egizaklarni top", "🧩 Найди близнецов", "🧩 Find the twins"), home,
                      [E(a) + E(b) + E(a) + E(c)])])

    # 2. Nima bilan nima?
    k.unit(T("Nima bilan nima?", "Что к чему?", "What goes together?"), "🧦")
    groups = [
        (T("Kim nima yeydi?", "Кто что ест?", "Who eats what?"), [
            ("quyon", "sabzi", "ayiqcha", T("quyon sabzi yeydi", "зайчик ест морковку", "the bunny eats a carrot"),
             T("Quyon sabzini juda yaxshi ko'radi: qirs-qirs! Shuning uchun quyon va sabzi — juftlik.",
               "Зайчик очень любит морковку: хрум-хрум! Поэтому зайчик и морковка — пара.",
               "The bunny loves carrots: crunch-crunch! So the bunny and the carrot go together.")),
            ("kuchuk", "suyak", "shar", T("kuchuk suyak g'ajiydi", "собачка грызёт косточку", "the puppy chews a bone"),
             T("Kuchukcha suyakni g'ajishni yaxshi ko'radi. Kuchuk va suyak — juftlik!",
               "Собачка любит грызть косточку. Собачка и косточка — пара!",
               "The puppy loves to chew a bone. The puppy and the bone go together!")),
            ("maymun", "banan", "top", T("maymun banan yeydi", "обезьянка ест банан", "the monkey eats a banana"),
             T("Maymuncha bananni archib, mazza qilib yeydi. Maymun va banan — juftlik!",
               "Обезьянка чистит банан и с удовольствием его ест. Обезьянка и банан — пара!",
               "The monkey peels a banana and eats it happily. The monkey and the banana go together!"))]),
        (T("Narsalar jufti", "Пары вещей", "Pairs of things"), [
            ("paypoq", "krossovka", "olma", T("paypoqdan keyin krossovka kiyamiz", "после носка надеваем кроссовку", "we put on a sneaker after a sock"),
             T("Avval paypoq kiyamiz, keyin krossovka. Ular doim birga — juftlik!",
               "Сначала надеваем носок, потом кроссовку. Они всегда вместе — пара!",
               "First we put on a sock, then a sneaker. They are always together — a pair!")),
            ("qoshiq", "likopcha", "mashina", T("qoshiq bilan likopchadan yeymiz", "ложкой едим из тарелки", "we eat from a plate with a spoon"),
             T("Likopchada osh bor, qoshiq bilan yeymiz. Qoshiq va likopcha — juftlik!",
               "В тарелке каша, мы едим её ложкой. Ложка и тарелка — пара!",
               "There is food on the plate, and we eat it with a spoon. The spoon and the plate go together!")),
            ("kalit", "qulf", "banan", T("kalit qulfni ochadi", "ключ открывает замок", "a key opens a lock"),
             T("Kalitni qulfga solib buraymiz — chiq! Qulf ochildi. Kalit va qulf — juftlik!",
               "Вставляем ключ в замок и поворачиваем — щёлк! Замок открылся. Ключ и замок — пара!",
               "We put the key in the lock and turn it — click! The lock opens. The key and the lock go together!"))]),
        (T("Kim qayerda yashaydi?", "Кто где живёт?", "Who lives where?"), [
            ("baliq", "dengiz", "uy", T("baliq suvda suzadi", "рыбка плавает в воде", "the fish swims in water"),
             T("Baliqcha suvda yashaydi va suzadi. Suvsiz baliq yashay olmaydi. Baliq va dengiz — juftlik!",
               "Рыбка живёт в воде и плавает. Без воды рыбка жить не может. Рыбка и море — пара!",
               "The fish lives in the water and swims. A fish can't live without water. The fish and the sea go together!")),
            ("qush", "uya", "dengiz", T("qushcha uyada yashaydi", "птичка живёт в гнезде", "the bird lives in a nest"),
             T("Qushcha daraxtda uya quradi va unda yashaydi. Qush va uya — juftlik!",
               "Птичка строит гнездо на дереве и живёт в нём. Птичка и гнездо — пара!",
               "The bird builds a nest in a tree and lives in it. The bird and the nest go together!")),
            ("ari", "gul", "muz", T("ari guldan shira oladi", "пчела собирает нектар с цветка", "the bee takes nectar from a flower"),
             T("Ari guldan gulga uchadi va shirin shira yig'adi. Ari va gul — juftlik!",
               "Пчела летает с цветка на цветок и собирает сладкий нектар. Пчела и цветок — пара!",
               "The bee flies from flower to flower and collects sweet nectar. The bee and the flower go together!"))]),
        (T("Nima bilan nima qilamiz?", "Чем что делаем?", "What do we use?"), [
            ("qalam", "daftar", "tarvuz", T("qalam bilan daftarga chizamiz", "карандашом рисуем в тетради", "we draw in a notebook with a pencil"),
             T("Qalamni olib, daftarga chiroyli rasm chizamiz. Qalam va daftar — juftlik!",
               "Берём карандаш и рисуем в тетради красивую картинку. Карандаш и тетрадь — пара!",
               "We take a pencil and draw a nice picture in a notebook. The pencil and the notebook go together!")),
            ("chotka", "tish", "shar", T("cho'tka bilan tish yuvamiz", "щёткой чистим зубы", "we brush teeth with a toothbrush"),
             T("Ertalab va kechqurun tish cho'tkasi bilan tishlarimizni yuvamiz. Cho'tka va tish — juftlik!",
               "Утром и вечером мы чистим зубы зубной щёткой. Щётка и зубы — пара!",
               "In the morning and at night we brush our teeth with a toothbrush. The toothbrush and teeth go together!")),
            ("soyabon", "yomgir", "olov", T("yomg'irda soyabon ochamiz", "в дождь открываем зонтик", "we open an umbrella in the rain"),
             T("Yomg'ir yog'sa, soyabonni ochamiz va quruq qolamiz. Soyabon va yomg'ir — juftlik!",
               "Если идёт дождь, мы открываем зонтик и остаёмся сухими. Зонтик и дождь — пара!",
               "When it rains, we open an umbrella and stay dry. The umbrella and the rain go together!"))]),
    ]
    for name, pairs in groups:
        (a1, b1, _, m1, x1), (a2, b2, _, m2, x2), _p3 = pairs
        k.lesson(name,
                 T("Bola bir-biriga mos narsalarni topadi va nima uchun mosligini aytadi",
                   "Ребёнок находит подходящие друг к другу предметы и говорит, почему они подходят",
                   "The child finds things that go together and says why"),
                 T("Bip-bip! Har narsaning o'z do'sti bor. {a} kimni qidiryapti ekan? Qani, juftini topamiz!",
                   "Бип-бип! У каждой вещи есть свой друг. Кого ищет {a}? Давай найдём ему пару!",
                   "Beep-beep! Everything has its own friend. Who is {a} looking for? Let's find its pair!").f(a=E(a1)),
                 [item(W(a1).cap() + T(" va ", " и ", " and ") + W(b1), m1, E(a1) + E(b1), x1),
                  item(W(a2).cap() + T(" va ", " и ", " and ") + W(b2), m2, E(a2) + E(b2), x2)],
                 [test(T("{a} + ❓ Nima mos keladi?", "{a} + ❓ Что подходит?", "{a} + ❓ What goes with it?").f(a=E(a)),
                       [opt(b), opt(d)], 0, k.praise() + T(" ", " ", " ") + m.cap() + T(".", ".", "."))
                  for a, b, d, m, _x in pairs],
                 [row(T("🧩 Juftini top", "🧩 Найди пару", "🧩 Find the pair"),
                      T("O'yin! Men bir narsani aytaman, sen uning juftini ko'rsat: {a} — ? {b} — ? Topding! Qarsak chal!",
                        "Игра! Я называю вещь, а ты покажи её пару: {a} — ? {b} — ? Нашёл! Хлопни в ладоши!",
                        "Game! I name a thing, and you show its pair: {a} — ? {b} — ? You found it! Clap your hands!").f(a=E(a1), b=E(a2)),
                      [f"{E(a1)} ➡️ {E(b1)}", f"{E(a2)} ➡️ {E(b2)}"])])

    # 3. Katta-kichik, og'ir-yengil
    k.unit(T("Kattami, kichikmi?", "Большой или маленький?", "Big or small?"), "🐘")
    cmp_lessons = [
        (T("Kim katta?", "Кто большой?", "Who is big?"), "katta",
         [("fil", "sichqon"), ("ayiq", "quyon"), ("jirafa", "joja")]),
        (T("Kim kichik?", "Кто маленький?", "Who is small?"), "kichik",
         [("sichqon", "fil"), ("joja", "tovuq"), ("gilos", "tarvuz")]),
        (T("Og'ir va yengil", "Тяжёлый и лёгкий", "Heavy and light"), "ogir",
         [("tarvuz", "pat"), ("tosh", "shar"), ("fil", "kapalak")]),
        (T("Katta-kichik oila", "Большие и маленькие", "Big and little family"), "katta",
         [("tovuq", "joja"), ("daraxt", "nihol"), ("avtobus", "velosiped")]),
    ]
    Q = {"katta": T("{a} {b} Qaysi biri katta?", "{a} {b} Кто больше?", "{a} {b} Which one is bigger?"),
         "kichik": T("{a} {b} Qaysi biri kichik?", "{a} {b} Кто меньше?", "{a} {b} Which one is smaller?"),
         "ogir": T("{a} {b} Qaysi biri og'ir?", "{a} {b} Что тяжелее?", "{a} {b} Which one is heavier?")}
    WHY = {"katta": T(" {w} — katta!", " {w} — больше!", " The {w} is bigger!"),
           "kichik": T(" {w} — kichkina!", " {w} — меньше!", " The {w} is smaller!"),
           "ogir": T(" {w} — og'ir!", " {w} — тяжелее!", " The {w} is heavier!")}
    for name, kind, pairs in cmp_lessons:
        (a1, b1), (a2, b2), (a3, b3) = pairs
        big, small = (a1, b1) if kind != "kichik" else (b1, a1)
        if kind == "ogir":
            items = [item(T("Og'ir", "Тяжёлый", "Heavy"), T("ko'tarish qiyin", "трудно поднять", "hard to lift"), E(a1),
                          T("{e} {w} — og'ir. Uni ko'tarish qiyin: uh-uh! Ikki qo'l bilan zo'rg'a ko'taramiz.",
                            "{e} {w}. Это — тяжёлое! Поднять трудно: ух-ух! Еле поднимаем двумя руками.",
                            "{e} The {w} is heavy. It is hard to lift: oof! We can barely lift it with two hands.").f(e=E(a1), w=W(a1)),
                          T("Og'ir narsani ko'targandek qil: uh!", "Покажи, будто поднимаешь тяжёлое: ух!", "Pretend to lift something heavy: oof!")),
                     item(T("Yengil", "Лёгкий", "Light"), T("bir barmoq bilan ko'tarsa bo'ladi", "можно поднять одним пальцем", "you can lift it with one finger"), E(b1),
                          T("{e} {w} — yengil. Uni bir barmoq bilan ko'tarsa bo'ladi, puflasang — uchib ketadi!",
                            "{e} {w}. Это — лёгкое! Можно поднять одним пальчиком, а если подуть — улетит!",
                            "{e} The {w} is light. You can lift it with one finger, and if you blow, it flies away!").f(e=E(b1), w=W(b1)),
                          T("Puflab ko'r: puf-f!", "Подуй: фу-у!", "Blow: whoo!"))]
        else:
            items = [item(T("Katta", "Большой", "Big"), T("ko'p joy egallaydi", "занимает много места", "takes up a lot of space"), E(big),
                          T("{e} {w} — katta! Qo'llaringni keng och: mana shunday kat-ta!",
                            "{e} {w}. Это — большое! Разведи ручки широко: во-от такое большое!",
                            "{e} The {w} is big! Spread your arms wide: this big!").f(e=E(big), w=W(big)),
                          T("Qo'llaringni keng ochib ko'rsat: kat-ta!", "Покажи руками: бо-ольшой!", "Show with your arms: big!")),
                     item(T("Kichik", "Маленький", "Small"), T("kaftga sig'adi", "помещается в ладошке", "fits in your palm"), E(small),
                          T("{e} {w} — kichkina. Kaftingga sig'adigan darajada kichkina!",
                            "{e} {w}. Это — маленькое! Такое маленькое, что поместится в ладошке!",
                            "{e} The {w} is small. So small it can fit in your palm!").f(e=E(small), w=W(small)),
                          T("Barmoqlaring bilan ko'rsat: mitti!", "Покажи пальчиками: малюсенький!", "Show with your fingers: tiny!"))]
        tests = []
        for a, b in pairs:
            tests.append(test(Q[kind].f(a=E(a), b=E(b)), [opt(a), opt(b)], 0,
                              k.praise() + WHY[kind].f(w=W(a).capuz())))
        k.lesson(name,
                 T("Bola narsalarni katta-kichik va og'ir-yengil bo'yicha solishtiradi",
                   "Ребёнок сравнивает предметы: большой — маленький, тяжёлый — лёгкий",
                   "The child compares things: big and small, heavy and light"),
                 T("Bip-bip! Qara: {a} va {b}. Ular bir xil emas! Qani, solishtiramiz!",
                   "Бип-бип! Смотри: {a} и {b}. Они не одинаковые! Давай сравним!",
                   "Beep-beep! Look: {a} and {b}. They are not the same! Let's compare!").f(a=E(a1), b=E(b1)),
                 items, tests,
                 [row(T("🏃 Katta-kichik o'yini", "🏃 Игра «Большой — маленький»", "🏃 Big and small game"),
                      T("O'yin! Men «katta» desam — qo'llaringni yuqoriga ko'tarib, katta bo'l. «Kichik» desam — cho'kkalab, kichkina bo'l! Katta! Kichik! Katta!",
                        "Игра! Я говорю «большой» — подними ручки и стань большим. Говорю «маленький» — присядь и стань маленьким! Большой! Маленький! Большой!",
                        "Game! When I say “big”, raise your arms and be big. When I say “small”, crouch down and be small! Big! Small! Big!"),
                      [f"{E(a1)} ⬆️", f"{E(b1)} ⬇️"], turi="amaliy")])

    # 4. Naqshni davom ettir (AB)
    k.unit(T("Naqshni davom ettir", "Продолжи узор", "Continue the pattern"), "🔴")
    pats = [(T("Qizil va ko'k naqsh", "Красно-синий узор", "Red and blue pattern"), "qizil", "kok"),
            (T("Mevali naqsh", "Фруктовый узор", "Fruit pattern"), "olma", "banan"),
            (T("Hayvonli naqsh", "Узор из зверят", "Animal pattern"), "mushuk", "kuchuk"),
            (T("Kun va tun naqshi", "Узор «день и ночь»", "Day and night pattern"), "quyosh", "oy")]
    for name, a, b in pats:
        k.lesson(name,
                 T("Bola ikki rasm navbatlashadigan naqshni ko'radi va keyingisini topadi",
                   "Ребёнок видит узор из двух чередующихся картинок и находит следующую",
                   "The child sees a pattern of two pictures taking turns and finds the next one"),
                 T("Bip-bip! Qara, qanday chiroyli qator: {s}. Rasmlar navbat bilan turibdi. Keyingisi kim ekan?",
                   "Бип-бип! Смотри, какой красивый ряд: {s}. Картинки стоят по очереди. Кто же следующий?",
                   "Beep-beep! Look at this pretty row: {s}. The pictures take turns. Who comes next?").f(s=seq([a, b, a, b])),
                 [item(T("Naqsh", "Узор", "Pattern"), T("takrorlanib turadigan qator", "ряд, который повторяется", "a row that repeats"),
                       seq([a, b, a, b]),
                       T("Qara: {wa}, {wb}, {wa}, {wb}. Bu — naqsh! Naqshda rasmlar navbat bilan takrorlanadi.",
                         "Смотри: {wa}, {wb}, {wa}, {wb}. Это — узор! В узоре картинки повторяются по очереди.",
                         "Look: {wa}, {wb}, {wa}, {wb}. This is a pattern! In a pattern, the pictures repeat in turns.").f(wa=W(a), wb=W(b)),
                       T("Men bilan ayt: {wa}, {wb}, {wa}, {wb}!", "Скажи со мной: {wa}, {wb}, {wa}, {wb}!",
                         "Say it with me: {wa}, {wb}, {wa}, {wb}!").f(wa=W(a), wb=W(b))),
                  item(T("Navbat", "По очереди", "Taking turns"), T("biri, keyin boshqasi", "сначала один, потом другой", "one, then the other"),
                       E(a) + "➡️" + E(b),
                       T("{wa}dan keyin doim {wb} keladi. {wb}dan keyin esa — yana {wa}. Ular navbat bilan turadi!",
                         "После «{wa}» всегда идёт «{wb}». А после «{wb}» — снова «{wa}». Они стоят по очереди!",
                         "After the {wa} always comes the {wb}. After the {wb} — the {wa} again. They take turns!").f(wa=W(a), wb=W(b)),
                       T("Qarsak, dupur, qarsak, dupur — sen ham navbat bilan qil!", "Хлоп, топ, хлоп, топ — сделай по очереди!",
                         "Clap, stomp, clap, stomp — take turns too!"))],
                 [test(T("{s}❓ Keyingisi qaysi?", "{s}❓ Что дальше?", "{s}❓ What comes next?").f(s=seq(s)),
                       [opt(ans), opt(other)], 0,
                       k.praise() + T(" Keyingisi — {w}.", " Дальше — {w}.", " Next is the {w}.").f(w=W(ans)))
                  for s, ans, other in (([a, b, a, b], a, b), ([b, a, b, a], b, a), ([a, b, a], b, a))],
                 [row(T("👏 Qarsak naqshi", "👏 Узор из хлопков", "👏 Clapping pattern"),
                      T("O'yin! Qarsak, dupur, qarsak, dupur! Endi sen davom ettir: qarsak... nima? Dupur! Barakalla!",
                        "Игра! Хлоп, топ, хлоп, топ! Теперь продолжай ты: хлоп... что дальше? Топ! Молодец!",
                        "Game! Clap, stomp, clap, stomp! Now you continue: clap... what's next? Stomp! Well done!"),
                      ["👏🦶👏🦶❓"], turi="amaliy")])

    # 5. Ortiqchasini top (3 tadan)
    k.unit(T("Ortiqchasini top", "Найди лишнее", "Find the odd one"), "🙅")
    odd = [
        (T("Mevalar va bitta begona", "Фрукты и один чужой", "Fruits and one stranger"), T("meva", "фрукты", "fruit"),
         [("olma", "nok", "mashina"), ("banan", "uzum", "top"), ("gilos", "olma", "kuchuk")]),
        (T("Hayvonlar va bitta begona", "Зверята и один чужой", "Animals and one stranger"), T("hayvon", "животные", "animals"),
         [("mushuk", "kuchuk", "shar"), ("quyon", "ayiq", "olma"), ("fil", "sichqon", "avtobus")]),
        (T("Transport va bitta begona", "Транспорт и один чужой", "Vehicles and one stranger"), T("transport", "транспорт", "vehicles"),
         [("mashina", "avtobus", "banan"), ("poyezd", "samolyot", "mushuk"), ("velosiped", "qayiq", "ayiqcha")]),
        (T("Kiyimlar va bitta begona", "Одежда и один чужой", "Clothes and one stranger"), T("kiyim", "одежда", "clothes"),
         [("koylak", "shim", "baliq"), ("paypoq", "kepka", "olma"), ("kurtka", "sharf", "mashina")]),
    ]
    for name, cat, triples in odd:
        a, b, o = triples[0]
        k.lesson(name,
                 T("Bola uchta rasm ichidan boshqalarga o'xshamaydiganini topadi",
                   "Ребёнок находит среди трёх картинок ту, что не похожа на другие",
                   "The child finds the one picture out of three that doesn't belong"),
                 T("Bip-bip! Qara: {s}. Bittasi adashib qolibdi! Qaysi biri boshqalarga o'xshamaydi?",
                   "Бип-бип! Смотри: {s}. Кто-то здесь потерялся! Кто не похож на других?",
                   "Beep-beep! Look: {s}. Someone got lost here! Which one is not like the others?").f(s=seq([a, b, o])),
                 [item(T("Guruh", "Группа", "Group"), T("bir turdagi narsalar", "вещи одного вида", "things of one kind"),
                       seq([a, b]),
                       T("{wa} va {wb} — ikkalasi ham {cat}. Ular bitta guruh, bitta oila!",
                         "{wa} и {wb} — это {cat}. Они одна группа, одна семья!",
                         "The {wa} and the {wb} are both {cat}. They are one group, one family!").f(wa=W(a).capuz(), wb=W(b), cat=cat),
                       T("Qo'llaringni bir-biriga qo'shib, «oila» de!", "Сложи ручки вместе и скажи: «Семья!»",
                         "Hold your hands together and say “family!”")),
                  item(T("Ortiqcha", "Лишний", "The odd one"), T("guruhga kirmaydi", "не входит в группу", "doesn't belong to the group"),
                       E(o),
                       T("{e} {w} esa {cat} emas. U bu guruhga kirmaydi. Demak, {w} — ortiqcha!",
                         "А {e} {w} — это не {cat}. Это из другой группы. Значит, это лишнее!",
                         "But the {e} {w} is not {cat}. It doesn't belong to this group. So the {w} is the odd one!").f(e=E(o), w=W(o), cat=cat),
                       T("Barmog'ingni silkit: «Sen bizdan emassan!»", "Погрози пальчиком: «Ты не из нашей группы!»",
                         "Wag your finger: “You're not one of us!”"))],
                 [test(T("{s} Qaysi biri ortiqcha?", "{s} Что лишнее?", "{s} Which one is the odd one?").f(s=seq([x, o_, y])),
                       [opt(o_), opt(x)], 0,
                       k.praise() + T(" {w} — {cat} emas.", " {w} — это не {cat}.", " The {w} is not {cat}.").f(w=W(o_).capuz(), cat=cat))
                  for x, y, o_ in triples],
                 [row(T("🧺 Savatga yig'amiz", "🧺 Собираем в корзинку", "🧺 Fill the basket"),
                      T("O'yin! Savatga faqat {cat} solamiz. Men aytaman, sen «ha» yoki «yo'q» de: {a} — ha! {o} — yo'q! {b} — ha!",
                        "Игра! В корзинку кладём только {cat}. Я называю, а ты говоришь «да» или «нет»: {a} — да! {o} — нет! {b} — да!",
                        "Game! We put only {cat} in the basket. I name things, you say “yes” or “no”: {a} — yes! {o} — no! {b} — yes!").f(cat=cat, a=E(a), o=E(o), b=E(b)),
                      [f"🧺 {E(a)}{E(b)}", f"🙅 {E(o)}"])])
    return k


# ═════════════════════════════ 4–5 yosh ═════════════════════════════
def pattern_lesson(k, name, kind_say, kind_uz, unit, rule, goal, cut_points, extra):
    """unit — naqsh birligi (kalitlar ro'yxati). cut_points — savollar: qator uzunligi (keyingisi so'raladi)."""
    full = unit * 4
    tests = []
    for n in cut_points:
        shown, ans = full[:n], full[n]
        other = next(x for x in unit if x != ans)
        tests.append(test(T("{s}❓ Keyingisi qaysi?", "{s}❓ Что дальше?", "{s}❓ What comes next?").f(s=seq(shown)),
                          [opt(ans), opt(other)], 0,
                          k.praise() + T(" Keyingisi — {w}.", " Дальше — {w}.", " Next is the {w}.").f(w=W(ans))))
    names = T(", ", ", ", ", ")
    words = W(unit[0])
    for x in unit[1:]:
        words = words + names + W(x)
    k.lesson(name, goal,
             T("Bip-bip! Naqsh — bu sirli qator. Qara: {s}. Sirini topsang, keyingisini ham bilasan!",
               "Бип-бип! Узор — это ряд с секретом. Смотри: {s}. Разгадаешь секрет — узнаешь, что дальше!",
               "Beep-beep! A pattern is a row with a secret. Look: {s}. Find the secret and you'll know what comes next!").f(s=seq(unit * 2)),
             [item(kind_say, kind_uz, seq(unit * 2),
                   rule + T(" Qara: {s}. Bo'lak: {w} — keyin yana boshidan!", " Смотри: {s}. Кусочек: {w} — и снова сначала!",
                            " Look: {s}. The part is: {w} — and then again from the start!").f(s=seq(unit * 2), w=words),
                   T("Naqshni men bilan ayt: {w}... yana: {w}!", "Скажи узор со мной: {w}... ещё раз: {w}!",
                     "Say the pattern with me: {w}... again: {w}!").f(w=words)),
              item(T("Naqsh bo'lagi", "Звено узора", "Pattern part"), T("takrorlanadigan qism", "часть, которая повторяется", "the part that repeats"),
                   seq(unit) + "🔁",
                   T("Naqshning sirli bo'lagi — {s}. U qayta-qayta takrorlanadi. Bo'lakni topsang — naqshni davom ettira olasan!",
                     "Секретная часть узора — {s}. Она повторяется снова и снова. Найдёшь эту часть — сможешь продолжить узор!",
                     "The secret part of the pattern is {s}. It repeats again and again. Find the part and you can continue the pattern!").f(s=seq(unit)),
                   None)],
             tests, extra)


def yosh45():
    k = Kitob("4-5 yosh", "4–5 yosh")
    T("4–5 yosh", "4–5 лет", "4–5 years").put()
    goal_p = T("Bola naqshning takrorlanadigan bo'lagini topadi va naqshni davom ettiradi",
               "Ребёнок находит повторяющуюся часть узора и продолжает узор",
               "The child finds the repeating part of a pattern and continues it")

    # 1. Naqshlar
    k.unit(T("Naqshlar", "Узоры", "Patterns"), "🎨")
    move = [row(T("👏 Harakatli naqsh", "👏 Узор движениями", "👏 Movement pattern"),
                T("O'yin! Qarsak, qarsak, dupur! Qarsak, qarsak, dupur! Endi sen davom ettir! Keyin o'zing yangi naqsh o'ylab top.",
                  "Игра! Хлоп, хлоп, топ! Хлоп, хлоп, топ! Теперь продолжай ты! А потом придумай свой узор.",
                  "Game! Clap, clap, stomp! Clap, clap, stomp! Now you continue! Then make up your own pattern."),
                ["👏👏🦶 👏👏🦶 ❓"], turi="amaliy")]
    pattern_lesson(k, T("Ikki rasmli naqsh", "Узор из двух картинок", "Two-picture pattern"),
                   T("AB naqsh", "Узор АБ", "AB pattern"), T("biri, keyin boshqasi", "сначала один, потом другой", "one, then the other"),
                   ["olma", "banan"], T("Bu naqshda ikki rasm navbatlashadi.", "В этом узоре чередуются две картинки.",
                                        "In this pattern, two pictures take turns."), goal_p, (4, 5, 7), move)
    pattern_lesson(k, T("Bitta va ikkita naqsh", "Узор «один и два»", "One-and-two pattern"),
                   T("ABB naqsh", "Узор АББ", "ABB pattern"), T("bitta, keyin ikkita", "одно, потом два", "one, then two"),
                   ["qizil", "kok", "kok"], T("Bu naqshda bitta qizil, keyin ikkita ko'k keladi.",
                                              "В этом узоре один красный круг, потом два синих.",
                                              "In this pattern there is one red circle, then two blue ones."), goal_p, (3, 4, 5), move)
    pattern_lesson(k, T("Ikkita va bitta naqsh", "Узор «два и один»", "Two-and-one pattern"),
                   T("AAB naqsh", "Узор ААБ", "AAB pattern"), T("ikkita, keyin bitta", "два, потом одно", "two, then one"),
                   ["yulduz", "yulduz", "oy"], T("Bu naqshda ikkita yulduz, keyin bitta oy keladi.",
                                                 "В этом узоре две звезды, потом одна луна.",
                                                 "In this pattern there are two stars, then one moon."), goal_p, (2, 5, 6), move)
    pattern_lesson(k, T("Uch rasmli naqsh", "Узор из трёх картинок", "Three-picture pattern"),
                   T("ABC naqsh", "Узор АБВ", "ABC pattern"), T("uchtasi navbat bilan", "три по очереди", "three in turn"),
                   ["mushuk", "kuchuk", "quyon"], T("Bu naqshda uchta hayvoncha navbat bilan turadi.",
                                                    "В этом узоре три зверька стоят по очереди.",
                                                    "In this pattern, three animals stand in turn."), goal_p, (3, 4, 5), move)
    pattern_lesson(k, T("Rangli shakllar naqshi", "Узор из цветных фигур", "Colorful shapes pattern"),
                   T("Shakl naqshi", "Узор из фигур", "Shape pattern"), T("shakllar navbatlashadi", "фигуры чередуются", "shapes take turns"),
                   ["uchburchak", "sariq", "kokkv"], T("Bu naqshda uchburchak, doira va kvadrat navbatlashadi.",
                                                       "В этом узоре чередуются треугольник, круг и квадрат.",
                                                       "In this pattern, a triangle, a circle and a square take turns."), goal_p, (3, 4, 7), move)

    # 2. Ortiqchasi qaysi? (4 tadan, belgisi bo'yicha)
    k.unit(T("Ortiqchasi qaysi?", "Что лишнее?", "Which one doesn't belong?"), "🙅")
    odd4 = [
        (T("Meva va sabzavot", "Фрукты и овощи", "Fruits and vegetables"),
         T("{a} — sabzavot, qolganlari — meva", "{a} — это овощ, а остальные — фрукты", "the {a} is a vegetable, the others are fruits"),
         T("Mevalar shirin, daraxtda o'sadi. Sabzavotlar esa ko'pincha yerda, polizda o'sadi.",
           "Фрукты сладкие, растут на деревьях. А овощи чаще растут на грядке, в земле.",
           "Fruits are sweet and grow on trees. Vegetables often grow in the ground, in a garden bed."),
         [("olma", "banan", "uzum", "sabzi"), ("nok", "gilos", "qulupnay", "bodring"), ("tarvuz", "olma", "banan", "pomidor")]),
        (T("Uchadi — uchmaydi", "Летает — не летает", "Flies or not"),
         T("{a} ucha olmaydi, qolganlari uchadi", "{a} не умеет летать, а остальные летают", "the {a} can't fly, the others can"),
         T("Qanoti borlar uchadi: qush, kapalak, ari. Qanoti yo'qlar — uchmaydi.",
           "Кто с крыльями — летает: птичка, бабочка, пчела. У кого крыльев нет — не летает.",
           "Things with wings can fly: a bird, a butterfly, a bee. Things without wings can't fly."),
         [("qush", "kapalak", "ari", "baliq"), ("samolyot", "qush", "boyqush", "mashina"), ("ari", "ordak", "kapalak", "fil")]),
        (T("Suvda yashaydi", "Живёт в воде", "Lives in water"),
         T("{a} suvda yashamaydi, qolganlari suvda yashaydi", "{a} не живёт в воде, а остальные живут", "the {a} doesn't live in water, the others do"),
         T("Baliq, delfin, sakkizoyoq suvda yashaydi. Mushuk, ot, quyon esa quruqlikda yashaydi.",
           "Рыбка, дельфин, осьминог живут в воде. А кошка, лошадь, зайчик живут на суше.",
           "Fish, dolphins and octopuses live in water. Cats, horses and bunnies live on land."),
         [("baliq", "delfin", "sakkizoyoq", "mushuk"), ("delfin", "baliq", "toshbaqa", "ot"), ("sakkizoyoq", "baliq", "delfin", "quyon")]),
        (T("Yeyiladi — yeyilmaydi", "Съедобное — несъедобное", "Can we eat it?"),
         T("{a}ni yeb bo'lmaydi, qolganlarini yeymiz", "{a} нельзя есть, а остальное можно", "you can't eat the {a}, but you can eat the others"),
         T("Non, pishloq, olmani yeymiz — ular ovqat. O'yinchoq va qalam esa ovqat emas!",
           "Хлеб, сыр, яблоко мы едим — это еда. А игрушки и карандаши — не еда!",
           "We eat bread, cheese and apples — they are food. Toys and pencils are not food!"),
         [("non", "pishloq", "olma", "ayiqcha"), ("sut", "banan", "non", "qalam"), ("tuxum", "asal", "uzum", "top")]),
        (T("Shakli boshqa", "Другая форма", "A different shape"),
         T("{a} — doira emas, qolganlari doira", "{a} — не круг, а остальные — круги", "the {a} is not a circle, the others are circles"),
         T("Doiraning burchagi yo'q, u yumaloq. Kvadrat va uchburchakning esa burchaklari bor.",
           "У круга нет углов, он круглый. А у квадрата и треугольника есть углы.",
           "A circle has no corners, it is round. A square and a triangle have corners."),
         [("qizil", "sariq", "yashil", "kvadrat"), ("kok", "qizil", "sariq", "uchburchak"), ("yashil", "kok", "qizil", "kokkv")]),
    ]
    for name, reason, explain, quads in odd4:
        a, b, c, o = quads[0]
        k.lesson(name,
                 T("Bola to'rtta rasm ichidan belgisi boshqacha bo'lganini topadi va sababini aytadi",
                   "Ребёнок находит среди четырёх картинок лишнюю по признаку и объясняет почему",
                   "The child finds the one out of four that differs and explains why"),
                 T("Bip-bip! Men to'rtta rasm qo'ydim: {s}. Bittasi boshqacha. Kim ekan? Diqqat bilan o'ylab ko'r!",
                   "Бип-бип! Я положил четыре картинки: {s}. Одна из них другая. Кто же? Подумай внимательно!",
                   "Beep-beep! I put out four pictures: {s}. One of them is different. Which one? Think carefully!").f(s=seq([a, b, o, c])),
                 [item(T("Umumiy belgi", "Общий признак", "What they share"), T("hammasida bor narsa", "то, что есть у всех", "something all of them have"),
                       seq([a, b, c]), explain,
                       T("Barmog'ing bilan hammasini sanab chiq: bir, ikki, uch!", "Посчитай их пальчиком: раз, два, три!",
                         "Count them with your finger: one, two, three!")),
                  item(T("Ortiqcha", "Лишний", "The odd one"), T("belgisi boshqacha", "признак другой", "it's different"),
                       E(o), T("{e} — ortiqcha, chunki ", "{e} — лишний, потому что ", "{e} is the odd one, because ").f(e=E(o)) + reason.f(a=W(o)) + T(".", ".", "."),
                       None)],
                 [test(T("{s} Qaysi biri ortiqcha?", "{s} Что лишнее?", "{s} Which one doesn't belong?").f(s=seq([x, y, o_, z])),
                       [opt(o_), opt(x)], 0, k.praise() + T(" ", " ", " ") + reason.f(a=W(o_)).cap() + T(".", ".", "."))
                  for x, y, z, o_ in quads],
                 [row(T("🔎 Uydan top", "🔎 Найди дома", "🔎 Find at home"),
                      T("O'yin! Uydan uchta bir xil turdagi narsa va bitta boshqacha narsani yig'. Kattalarga «Qaysi biri ortiqcha?» deb topishmoq qil!",
                        "Игра! Собери дома три вещи одного вида и одну другую. Загадай взрослым: «Что здесь лишнее?»",
                        "Game! Find three things of one kind at home and one different thing. Ask a grown-up: “Which one doesn't belong?”"),
                      [seq([a, b, c]) + " + " + E(o)])])

    # 3. Nima bilan nima? (bog'liqlik)
    k.unit(T("Nima bilan bog'liq?", "Что с чем связано?", "What goes with what?"), "🔗")
    links = [
        (T("Kim qayerda yashaydi?", "Кто где живёт?", "Who lives where?"),
         [("baliq", "dengiz", "chol", T("baliq dengizda yashaydi", "рыбка живёт в море", "the fish lives in the sea")),
          ("tuya", "chol", "dengiz", T("tuya cho'lda yashaydi", "верблюд живёт в пустыне", "the camel lives in the desert")),
          ("ayiq", "orm", "muz", T("ayiq o'rmonda yashaydi", "медведь живёт в лесу", "the bear lives in the forest")),
          ("pingvin", "muz", "chol", T("pingvin muzliklarda yashaydi", "пингвин живёт среди льдов", "the penguin lives on the ice"))]),
        (T("Kasb va asbob", "Профессия и инструмент", "Jobs and tools"),
         [("oshpaz", "tova", "stetoskop", T("oshpaz tovada ovqat pishiradi", "повар готовит на сковороде", "a cook cooks with a frying pan")),
          ("shifokor", "stetoskop", "tova", T("shifokor stetoskop bilan yurakni eshitadi", "врач слушает сердце стетоскопом", "a doctor listens to the heart with a stethoscope")),
          ("otochir", "otochirgich", "moyqalam", T("o't o'chiruvchi olovni o'chiradi", "пожарный тушит огонь", "a firefighter puts out fires")),
          ("rassom", "moyqalam", "traktor", T("rassom mo'yqalam bilan rasm chizadi", "художник рисует кисточкой", "an artist paints with a paintbrush"))]),
        (T("Hayvon nima beradi?", "Что дают животные?", "What do animals give us?"),
         [("sigir", "sut", "asal", T("sigir sut beradi", "корова даёт молоко", "a cow gives milk")),
          ("tovuq", "tuxum", "sut", T("tovuq tuxum qo'yadi", "курица несёт яйца", "a hen lays eggs")),
          ("ari", "asal", "yung", T("ari asal yig'adi", "пчела собирает мёд", "a bee makes honey")),
          ("qoy", "yung", "tuxum", T("qo'ydan jun olinadi", "у овечки берут шерсть", "we get wool from sheep"))]),
        (T("Ob-havo va kiyim", "Погода и одежда", "Weather and clothes"),
         [("quyosh", "shortik", "qolqop", T("issiq kunda shortik kiyamiz", "в жару надеваем шорты", "we wear shorts on a hot day")),
          ("qor", "qolqop", "shortik", T("qorli kunda qo'lqop kiyamiz", "в снег надеваем варежки", "we wear mittens when it snows")),
          ("yomgir", "soyabon", "kozoynak", T("yomg'irda soyabon olamiz", "в дождь берём зонтик", "we take an umbrella when it rains")),
          ("qor", "sharf", "kozoynak", T("sovuqda sharf o'raymiz", "в холод надеваем шарф", "we wear a scarf when it's cold"))]),
        (T("Narsa va uning ishi", "Вещь и её дело", "Things and their jobs"),
         [("kalit", "eshik", "kosa", T("kalit eshikni ochadi", "ключ открывает дверь", "a key opens a door")),
          ("qaychi", "qogoz", "sut", T("qaychi qog'ozni qirqadi", "ножницы режут бумагу", "scissors cut paper")),
          ("chotka", "tish", "eshik", T("cho'tka tishni tozalaydi", "щётка чистит зубы", "a toothbrush cleans teeth")),
          ("qoshiq", "kosa", "qogoz", T("qoshiq bilan kosadan sho'rva ichamiz", "ложкой едим суп из миски", "we eat soup from a bowl with a spoon"))]),
    ]
    for name, pairs in links:
        (a1, b1, _, m1), (a2, b2, _, m2) = pairs[:2]
        k.lesson(name,
                 T("Bola narsalar orasidagi bog'liqlikni topadi va tushuntiradi",
                   "Ребёнок находит связь между предметами и объясняет её",
                   "The child finds how things are connected and explains it"),
                 T("Bip-bip! Dunyoda hamma narsa bir-biri bilan bog'liq. {a} va {b} — nega birga? Qani, o'ylaymiz!",
                   "Бип-бип! В мире всё связано друг с другом. {a} и {b} — почему они вместе? Давай подумаем!",
                   "Beep-beep! Everything in the world is connected. {a} and {b} — why are they together? Let's think!").f(a=E(a1), b=E(b1)),
                 [item(W(a1).cap() + T(" va ", " и ", " and ") + W(b1), m1, E(a1) + E(b1),
                       T("Qara: {ea} va {eb}. ", "Смотри: {ea} и {eb}. ", "Look: {ea} and {eb}. ").f(ea=E(a1), eb=E(b1)) + m1.cap()
                       + T(". Shuning uchun ular birga!", ". Поэтому они вместе!", ". That's why they go together!")),
                  item(W(a2).cap() + T(" va ", " и ", " and ") + W(b2), m2, E(a2) + E(b2),
                       T("Endi qara: {ea} va {eb}. ", "А теперь: {ea} и {eb}. ", "Now look: {ea} and {eb}. ").f(ea=E(a2), eb=E(b2)) + m2.cap()
                       + T(". Ular ham bog'liq!", ". Они тоже связаны!", ". They are connected too!"))],
                 [test(T("{a} ➡️ ❓ Nima mos keladi?", "{a} ➡️ ❓ Что подходит?", "{a} ➡️ ❓ What goes with it?").f(a=E(a)),
                       [opt(b), opt(d)], 0, k.praise() + T(" ", " ", " ") + m.cap() + T(".", ".", "."))
                  for a, b, d, m in pairs[1:]],
                 [row(T("🎤 Gapni davom ettir", "🎤 Продолжи фразу", "🎤 Finish the sentence"),
                      T("O'yin! Men gapni boshlayman, sen tugat: {a} ... ? To'g'ri! Endi o'zing yangi juftlik o'ylab top va kattalarga ayt!",
                        "Игра! Я начинаю, а ты заканчиваешь: {a} ... ? Верно! А теперь придумай свою пару и расскажи взрослым!",
                        "Game! I start, you finish: {a} ... ? Right! Now think of your own pair and tell a grown-up!").f(a=E(a1)),
                      [f"{E(a)} ➡️ {E(b)}" for a, b, _d, _m in pairs])])

    # 4. Avval, keyin
    k.unit(T("Avval nima, keyin nima?", "Что сначала, что потом?", "What comes first?"), "⏳")
    chains = [
        (T("Tuxumdan jo'ja", "Из яйца — цыплёнок", "From egg to chick"), ["tuxum", "qaldirgoch", "joja"],
         T("Avval tuxum bo'ladi. Keyin jo'ja tuxumni cho'qib chiqadi. Oxirida u momiq jo'jaga aylanadi.",
           "Сначала — яйцо. Потом цыплёнок проклёвывает скорлупку. И вот он уже пушистый цыплёнок!",
           "First there is an egg. Then the chick pecks its way out. At last it becomes a fluffy chick.")),
        (T("Urug'dan gul", "Из семечка — цветок", "From seed to flower"), ["urug", "nihol", "lola"],
         T("Avval urug'ni yerga ekamiz. Keyin undan nihol chiqadi. Oxirida chiroyli gul ochiladi.",
           "Сначала сажаем семечко в землю. Потом из него появляется росток. А в конце распускается красивый цветок.",
           "First we plant a seed in the ground. Then a sprout comes up. At last a beautiful flower blooms.")),
        (T("Ertalabdan kechgacha", "С утра до вечера", "From morning to night"), ["tong", "quyosh", "oy"],
         T("Avval tong otadi. Keyin kun bo'ladi, quyosh charaqlaydi. Oxirida tun keladi, oy chiqadi.",
           "Сначала наступает утро. Потом день, светит солнышко. А в конце приходит ночь, и выходит луна.",
           "First the morning comes. Then it is day and the sun shines. At last night comes and the moon comes out.")),
        (T("Qurtchadan kapalak", "Из гусеницы — бабочка", "From caterpillar to butterfly"), ["tuxum", "qurt", "kapalak"],
         T("Avval bargda kichkina tuxum bo'ladi. Undan qurtcha chiqadi. Qurtcha ko'p yeydi, keyin chiroyli kapalakka aylanadi!",
           "Сначала на листике маленькое яичко. Из него появляется гусеница. Она много ест, а потом превращается в красивую бабочку!",
           "First there is a tiny egg on a leaf. A caterpillar comes out of it. It eats a lot and then turns into a beautiful butterfly!")),
        (T("Kiyinamiz", "Одеваемся", "Getting dressed"), ["paypoq", "krossovka", "kepka"],
         T("Avval paypoq kiyamiz. Keyin krossovka. Tashqariga chiqishdan oldin esa — kepka!",
           "Сначала надеваем носки. Потом кроссовки. А перед выходом на улицу — кепку!",
           "First we put on socks. Then sneakers. And before going outside — a cap!")),
    ]
    for name, (a, b, c), story in chains:
        k.lesson(name,
                 T("Bola voqealar ketma-ketligini tushunadi: avval, keyin, oxirida",
                   "Ребёнок понимает порядок событий: сначала, потом, в конце",
                   "The child understands the order of events: first, then, last"),
                 T("Bip-bip! Har narsaning o'z navbati bor. {s} — qaysi biri birinchi? Qani, tartibga solamiz!",
                   "Бип-бип! У всего есть свой порядок. {s} — что первое? Давай разложим по порядку!",
                   "Beep-beep! Everything has its order. {s} — which comes first? Let's put them in order!").f(s=seq([c, a, b])),
                 [item(T("Avval", "Сначала", "First"), T("eng birinchi", "самое первое", "the very first"), E(a),
                       story, T("Bitta barmog'ingni ko'rsat: «avval!»", "Покажи один пальчик: «сначала!»", "Show one finger: “first!”")),
                  item(T("Keyin", "Потом", "Then"), T("undan keyin", "после этого", "after that"), E(a) + "➡️" + E(b) + "➡️" + E(c),
                       T("{a} ➡️ {b} ➡️ {c}. Avval — {wa}, keyin — {wb}, oxirida — {wc}.",
                         "{a} ➡️ {b} ➡️ {c}. Сначала — {wa}, потом — {wb}, в конце — {wc}.",
                         "{a} ➡️ {b} ➡️ {c}. First the {wa}, then the {wb}, and last the {wc}.").f(a=E(a), b=E(b), c=E(c), wa=W(a), wb=W(b), wc=W(c)),
                       T("Barmoqlaringda sana: avval, keyin, oxirida!", "Посчитай на пальчиках: сначала, потом, в конце!",
                         "Count on your fingers: first, then, last!"))],
                 [test(T("{a} ➡️ ❓ Keyin nima bo'ladi?", "{a} ➡️ ❓ Что будет потом?", "{a} ➡️ ❓ What happens next?").f(a=E(a)),
                       [opt(b), opt(c)], 0, k.praise() + T(" Avval {wa}, keyin {wb}.", " Сначала {wa}, потом {wb}.", " First the {wa}, then the {wb}.").f(wa=W(a), wb=W(b))),
                  test(T("❓ ➡️ {b} ➡️ {c} Eng birinchi nima?", "❓ ➡️ {b} ➡️ {c} Что самое первое?", "❓ ➡️ {b} ➡️ {c} What comes first?").f(b=E(b), c=E(c)),
                       [opt(a), opt(c)], 0, k.praise() + T(" Eng birinchi — {w}.", " Самое первое — {w}.", " First comes the {w}.").f(w=W(a))),
                  test(T("{a} ➡️ {b} ➡️ ❓ Oxirida nima?", "{a} ➡️ {b} ➡️ ❓ Что в конце?", "{a} ➡️ {b} ➡️ ❓ What comes last?").f(a=E(a), b=E(b)),
                       [opt(c), opt(a)], 0, k.praise() + T(" Oxirida — {w}.", " В конце — {w}.", " Last comes the {w}.").f(w=W(c)))],
                 [row(T("🎭 Ko'rsatib ber", "🎭 Покажи", "🎭 Act it out"),
                      T("O'yin! Bu hikoyani harakat bilan ko'rsat: avval {a}, keyin {b}, oxirida {c}. Endi teskarisini ko'rsatib ko'r — kulgili bo'ladi!",
                        "Игра! Покажи эту историю движениями: сначала {a}, потом {b}, в конце {c}. А теперь покажи наоборот — будет смешно!",
                        "Game! Act out the story: first {a}, then {b}, last {c}. Now try it backwards — it's funny!").f(a=E(a), b=E(b), c=E(c)),
                      [f"1 {E(a)}  2 {E(b)}  3 {E(c)}"], turi="amaliy")])

    # 5. Diqqat: nima yo'qoldi?
    k.unit(T("Diqqat o'yini", "Игра на внимание", "Attention game"), "👀")
    gone = [
        (T("Qaysi meva yo'qoldi?", "Какой фрукт пропал?", "Which fruit is missing?"), ["olma", "banan", "uzum", "nok", "gilos"]),
        (T("Qaysi hayvon yashirindi?", "Какой зверёк спрятался?", "Which animal is hiding?"), ["mushuk", "kuchuk", "quyon", "ayiq", "fil"]),
        (T("Qaysi o'yinchoq yo'q?", "Какой игрушки нет?", "Which toy is missing?"), ["top", "ayiqcha", "shar", "mashina", "velosiped"]),
        (T("Qaysi transport ketdi?", "Какой транспорт уехал?", "Which vehicle left?"), ["mashina", "avtobus", "poyezd", "samolyot", "qayiq"]),
        (T("Qaysi shakl yo'qoldi?", "Какая фигура пропала?", "Which shape is missing?"), ["qizil", "kokkv", "uchburchak", "yulduz", "yurak"]),
    ]
    for name, (a, b, c, d, e) in gone:
        k.lesson(name,
                 T("Bola rasmlarni eslab qoladi va qaysi biri yo'qolganini topadi (diqqat va xotira)",
                   "Ребёнок запоминает картинки и находит, какая пропала (внимание и память)",
                   "The child remembers pictures and finds which one is missing (attention and memory)"),
                 T("Bip-bip! Ko'zlaringni katta och va eslab qol: {s}. Endi bittasi yashirinadi. Qaysi biri ekan?",
                   "Бип-бип! Открой глазки пошире и запомни: {s}. Сейчас одна картинка спрячется. Какая же?",
                   "Beep-beep! Open your eyes wide and remember: {s}. Now one picture will hide. Which one?").f(s=seq([a, b, c])),
                 [item(T("Eslab qol", "Запомни", "Remember"), T("diqqat bilan qarab, yodda saqla", "посмотри внимательно и запомни", "look carefully and keep it in mind"),
                       seq([a, b, c]),
                       T("Qara va eslab qol: {s}. {wa}, {wb}, {wc}. Ko'zingni yumib, ichingda takrorla!",
                         "Смотри и запоминай: {s}. {wa}, {wb}, {wc}. Закрой глазки и повтори про себя!",
                         "Look and remember: {s}. The {wa}, the {wb}, the {wc}. Close your eyes and say them to yourself!").f(s=seq([a, b, c]), wa=W(a).capuz(), wb=W(b), wc=W(c)),
                       T("Ko'zingni yum va ayt: nima bor edi?", "Закрой глаза и скажи: что там было?", "Close your eyes and say: what was there?")),
                  item(T("Yo'qoldi", "Пропал", "Missing"), T("oldin bor edi, endi yo'q", "раньше был, а теперь нет", "it was there, now it's gone"),
                       seq([a, c]) + "❓",
                       T("Endi qara: {s}. {wb} qayerda? U yashirindi! Biz uni esladik — demak, diqqatimiz kuchli!",
                         "А теперь смотри: {s}. Где {wb}? Спрятался! Мы его вспомнили — значит, мы очень внимательные!",
                         "Now look: {s}. Where is the {wb}? It's hiding! We remembered it — so we pay great attention!").f(s=seq([a, c]), wb=W(b)),
                       None)],
                 [test(T("{s1} ➡️ {s2} Nima yo'qoldi?", "{s1} ➡️ {s2} Что пропало?", "{s1} ➡️ {s2} What is missing?").f(s1=seq(full), s2=seq([x for x in full if x != miss])),
                       [opt(miss), opt(other)], 0, k.praise() + T(" {w} yo'qoldi.", " Пропала картинка: {w}.", " The {w} is missing.").f(w=W(miss).capuz()))
                  for full, miss, other in (([a, b, c], b, a), ([a, c, d], d, c), ([b, d, e, a], e, b))],
                 [row(T("🙈 Yashirinmachoq", "🙈 Прятки", "🙈 Hide and seek"),
                      T("O'yin! Kattalar stolga 4 ta o'yinchoq qo'ysin. Sen ko'zingni yum — ular bittasini yashiradi. Ko'zingni och: qaysi biri yo'q?",
                        "Игра! Пусть взрослые положат на стол 4 игрушки. Ты закрываешь глаза — они прячут одну. Открывай: какой нет?",
                        "Game! Ask a grown-up to put 4 toys on the table. You close your eyes — they hide one. Open your eyes: which one is missing?"),
                      ["🧸⚽🎈🚗 ➡️ 🙈 ➡️ ❓"], turi="amaliy")])
    return k


# ═════════════════════════════ 6–7 yosh ═════════════════════════════
def yosh67():
    k = Kitob("6-7 yosh", "6–7 yosh")
    T("6–7 yosh", "6–7 лет", "6–7 years").put()

    def q3(qt, right, wrongs, why):
        return test(qt, [right] + wrongs, 0, k.praise() + T(" ", " ", " ") + why)

    # 1. Murakkab va sonli naqshlar
    k.unit(T("Murakkab naqshlar", "Сложные узоры", "Tricky patterns"), "🧩")
    goal_p = T("Bola murakkab va sonli naqshlarning qoidasini topadi va davom ettiradi",
               "Ребёнок находит правило сложных и числовых узоров и продолжает их",
               "The child finds the rule of tricky and number patterns and continues them")
    move = [row(T("🤸 Naqsh mashqi", "🤸 Зарядка-узор", "🤸 Pattern exercise"),
                T("Mashq! Qarsak, qarsak, sakra, sakra! Qarsak, qarsak, sakra, sakra! Endi o'zing naqsh o'ylab top va do'stingga o'rgat!",
                  "Зарядка! Хлоп, хлоп, прыг, прыг! Хлоп, хлоп, прыг, прыг! А теперь придумай свой узор и научи друга!",
                  "Exercise! Clap, clap, jump, jump! Clap, clap, jump, jump! Now invent your own pattern and teach a friend!"),
                ["👏👏🤸🤸 👏👏🤸🤸"], turi="amaliy")]
    for name, unit_, rule, cuts in [
        (T("Juft-juft naqsh", "Узор парами", "Pairs pattern"), ["qizil", "qizil", "kok", "kok"],
         T("Bu naqshda har rasm ikkitadan keladi: ikkita qizil, ikkita ko'k.", "В этом узоре каждая картинка идёт парой: два красных, два синих.",
           "In this pattern, each picture comes in twos: two red, two blue."), (4, 6, 7)),
        (T("Uchta mevali naqsh", "Узор из трёх фруктов", "Three-fruit pattern"), ["olma", "banan", "uzum"],
         T("Bu naqshda uchta meva navbat bilan keladi.", "В этом узоре три фрукта идут по очереди.",
           "In this pattern, three fruits come in turn."), (4, 5, 6)),
        (T("Ikkita yulduz, oy, quyosh", "Две звезды, луна, солнце", "Two stars, moon, sun"), ["yulduz", "yulduz", "oy", "quyosh"],
         T("Bu naqshda ikkita yulduz, keyin oy, keyin quyosh keladi.", "В этом узоре две звезды, потом луна, потом солнце.",
           "In this pattern: two stars, then the moon, then the sun."), (4, 6, 7)),
    ]:
        full = unit_ * 4
        tests = []
        for n in cuts:
            ans = full[n]
            wrong = [x for x in dict.fromkeys(unit_) if x != ans][:2]
            tests.append(q3(T("{s}❓ Keyingisi qaysi?", "{s}❓ Что дальше?", "{s}❓ What comes next?").f(s=seq(full[:n])),
                            opt(ans), [opt(x) for x in wrong], T("Keyingisi — {w}.", "Дальше — {w}.", "Next is the {w}.").f(w=W(ans))))
        k.lesson(name, goal_p,
                 T("Bip-bip! Bugungi naqsh — qiyinroq, lekin sen endi katta bolasan! Qara: {s}. Qoidasini top!",
                   "Бип-бип! Сегодняшний узор посложнее, но ты уже большой! Смотри: {s}. Найди правило!",
                   "Beep-beep! Today's pattern is harder, but you're big now! Look: {s}. Find the rule!").f(s=seq(unit_ * 2)),
                 [item(T("Naqsh qoidasi", "Правило узора", "Pattern rule"), T("naqsh qanday takrorlanadi", "как повторяется узор", "how the pattern repeats"),
                       seq(unit_ * 2), rule + T(" Bo'lak: {s} — keyin yana boshidan.", " Звено: {s} — и снова сначала.", " The part: {s} — then again from the start.").f(s=seq(unit_)),
                       T("Naqshni qarsak bilan chal!", "Прохлопай узор в ладоши!", "Clap out the pattern!")),
                  item(T("Bo'lakni top", "Найди звено", "Find the part"), T("takrorlanadigan qism", "часть, которая повторяется", "the part that repeats"),
                       seq(unit_) + "🔁",
                       T("Naqshni bo'laklarga ajrat: {s} | {s} | {s}. Bo'lak topildi — endi naqshni xohlagancha davom ettira olasan!",
                         "Раздели узор на звенья: {s} | {s} | {s}. Звено найдено — теперь ты можешь продолжать узор сколько хочешь!",
                         "Split the pattern into parts: {s} | {s} | {s}. Found the part — now you can continue the pattern as long as you like!").f(s=seq(unit_)),
                       None)],
                 tests, move)
    numpats = [
        (T("O'sib boradigan naqsh", "Растущий узор", "Growing pattern"),
         T("Har safar bittadan ko'payadi", "Каждый раз на один больше", "One more each time"),
         T("Qara: ⭐, ⭐⭐, ⭐⭐⭐. Har safar bitta yulduz qo'shiladi! Bir, ikki, uch... keyin — to'rt!",
           "Смотри: ⭐, ⭐⭐, ⭐⭐⭐. Каждый раз добавляется одна звёздочка! Один, два, три... потом — четыре!",
           "Look: ⭐, ⭐⭐, ⭐⭐⭐. Each time one more star is added! One, two, three... then four!"), "⭐ ⭐⭐ ⭐⭐⭐",
         [(T("⭐ | ⭐⭐ | ⭐⭐⭐ | ❓ Keyingisida nechta yulduz?", "⭐ | ⭐⭐ | ⭐⭐⭐ | ❓ Сколько звёзд дальше?", "⭐ | ⭐⭐ | ⭐⭐⭐ | ❓ How many stars next?"), 4, [3, 5]),
          (T("🍎 | 🍎🍎 | ❓ Keyingisida nechta olma?", "🍎 | 🍎🍎 | ❓ Сколько яблок дальше?", "🍎 | 🍎🍎 | ❓ How many apples next?"), 3, [2, 4]),
          (T("🐥🐥 | 🐥🐥🐥 | 🐥🐥🐥🐥 | ❓ Keyingisida nechta jo'ja?", "🐥🐥 | 🐥🐥🐥 | 🐥🐥🐥🐥 | ❓ Сколько цыплят дальше?", "🐥🐥 | 🐥🐥🐥 | 🐥🐥🐥🐥 | ❓ How many chicks next?"), 5, [4, 6])]),
        (T("Ikkitalab sanaymiz", "Считаем двойками", "Counting by twos"),
         T("Har safar ikkitaga ko'payadi", "Каждый раз на два больше", "Two more each time"),
         T("Qara: 2, 4, 6. Har safar ikkitadan qo'shiladi! Ikki, to'rt, olti... keyin — sakkiz!",
           "Смотри: 2, 4, 6. Каждый раз прибавляем два! Два, четыре, шесть... потом — восемь!",
           "Look: 2, 4, 6. Each time we add two! Two, four, six... then eight!"), "2 ➡️ 4 ➡️ 6 ➡️ ❓",
         [(T("2, 4, 6, ❓ Keyingi son qaysi?", "2, 4, 6, ❓ Какое число дальше?", "2, 4, 6, ❓ What number comes next?"), 8, [7, 10]),
          (T("4, 6, 8, ❓ Keyingi son qaysi?", "4, 6, 8, ❓ Какое число дальше?", "4, 6, 8, ❓ What number comes next?"), 10, [9, 6]),
          (T("1, 3, 5, ❓ Keyingi son qaysi?", "1, 3, 5, ❓ Какое число дальше?", "1, 3, 5, ❓ What number comes next?"), 7, [6, 8])]),
        (T("Orqaga sanaymiz", "Считаем назад", "Counting backwards"),
         T("Har safar bittaga kamayadi", "Каждый раз на один меньше", "One less each time"),
         T("Qara: 5, 4, 3. Har safar bittaga kamayadi! Raketa uchishidan oldin shunday sanaladi: besh, to'rt, uch, ikki, bir — uchdik!",
           "Смотри: 5, 4, 3. Каждый раз на один меньше! Так считают перед взлётом ракеты: пять, четыре, три, два, один — пуск!",
           "Look: 5, 4, 3. One less each time! That's how we count before a rocket launch: five, four, three, two, one — liftoff!"), "5 ➡️ 4 ➡️ 3 ➡️ ❓",
         [(T("5, 4, 3, ❓ Keyingi son qaysi?", "5, 4, 3, ❓ Какое число дальше?", "5, 4, 3, ❓ What number comes next?"), 2, [4, 1]),
          (T("10, 9, 8, ❓ Keyingi son qaysi?", "10, 9, 8, ❓ Какое число дальше?", "10, 9, 8, ❓ What number comes next?"), 7, [9, 6]),
          (T("8, 6, 4, ❓ Keyingi son qaysi?", "8, 6, 4, ❓ Какое число дальше?", "8, 6, 4, ❓ What number comes next?"), 2, [3, 1])]),
    ]
    for name, rule_say, explain, board, qs in numpats:
        k.lesson(name, goal_p,
                 T("Bip-bip! Sonlar ham naqsh hosil qiladi! Sirini topsang — keyingi sonni aytib bera olasan.",
                   "Бип-бип! Числа тоже складываются в узоры! Разгадаешь секрет — назовёшь следующее число.",
                   "Beep-beep! Numbers make patterns too! Find the secret and you can say the next number."),
                 [item(rule_say, T("sonli naqsh qoidasi", "правило числового узора", "the number pattern rule"), board, explain,
                       T("Barmoqlaringda sanab ko'r!", "Посчитай на пальчиках!", "Count on your fingers!")),
                  item(T("Qoidani tekshir", "Проверь правило", "Check the rule"), T("har qadamda bir xil o'zgaradi", "на каждом шаге меняется одинаково", "it changes the same way each step"),
                       "🔍", T("Har ikki qo'shni sonni solishtir: qancha ko'paydi yoki kamaydi? Har safar bir xil bo'lsa — qoidani topding!",
                               "Сравни соседние числа: на сколько стало больше или меньше? Если каждый раз одинаково — правило найдено!",
                               "Compare each two neighbor numbers: how much bigger or smaller? If it's the same every time — you found the rule!"),
                       None)],
                 [q3(qt, opt(ans), [opt(x) for x in wr], T("Javob — {w}.", "Ответ — {w}.", "The answer is {w}.").f(w=NUM[ans][1])) for qt, ans, wr in qs],
                 [row(T("🚀 Raketa sanog'i", "🚀 Ракетный счёт", "🚀 Rocket countdown"),
                      T("O'yin! Cho'kkalab o'tir. O'ndan birgacha orqaga sana va «Uchdik!» deb baland sakra! Keyin ikkitalab sana: 2, 4, 6, 8, 10!",
                        "Игра! Присядь. Посчитай назад от десяти до одного и с криком «Пуск!» высоко подпрыгни! А потом считай двойками: 2, 4, 6, 8, 10!",
                        "Game! Crouch down. Count backwards from ten to one and jump high shouting “Liftoff!” Then count by twos: 2, 4, 6, 8, 10!"),
                      ["🔟 9 8 7 6 5 4 3 2 1 🚀"], turi="amaliy")])

    # 2. Ortiqcha va sababi
    k.unit(T("Ortiqchasini top va sababini ayt", "Найди лишнее и объясни", "Find the odd one and explain"), "🕵️")
    odd = [
        (T("Qushmi yoki yo'q?", "Птица или нет?", "A bird or not?"),
         T("{a} — qush emas, hasharot; qolganlari qush", "{a} — не птица, а насекомое; остальные — птицы", "the {a} is not a bird, it's an insect; the others are birds"),
         T("Qushlarning pati va tumshug'i bor. Kapalak ham uchadi, lekin u — hasharot: pati yo'q, oltita oyog'i bor.",
           "У птиц есть перья и клюв. Бабочка тоже летает, но она — насекомое: перьев нет, а ножек шесть.",
           "Birds have feathers and a beak. A butterfly flies too, but it's an insect: no feathers and six legs."),
         [("qush", "boyqush", "ordak", "kapalak"), ("ordak", "tovuq", "qush", "ari"), ("boyqush", "pingvin", "tovuq", "kapalak")]),
        (T("Tirik va jonsiz", "Живое и неживое", "Living and non-living"),
         T("{a} — jonsiz, qolganlari tirik", "{a} — неживое, остальные — живые", "the {a} is non-living, the others are alive"),
         T("Tirik narsalar nafas oladi, oziqlanadi va o'sadi: hayvon, o'simlik, odam. Tosh, mashina esa o'smaydi — ular jonsiz.",
           "Живое дышит, питается и растёт: животные, растения, люди. А камень и машина не растут — они неживые.",
           "Living things breathe, eat and grow: animals, plants, people. A stone or a car doesn't grow — they are non-living."),
         [("mushuk", "daraxt", "baliq", "tosh"), ("gul", "qush", "ot", "mashina"), ("nihol", "ari", "it", "ayiqcha")]),
        (T("Yoz va qish narsalari", "Вещи для лета и зимы", "Summer and winter things"),
         T("{a} — qish uchun, qolganlari yoz uchun", "{a} — для зимы, а остальное — для лета", "the {a} is for winter, the others are for summer"),
         T("Yozda issiq: shortik, ko'zoynak, tarvuz. Qishda sovuq: sharf, qo'lqop, kurtka kerak bo'ladi.",
           "Летом жарко: шорты, очки от солнца, арбуз. Зимой холодно: нужны шарф, варежки, куртка.",
           "Summer is hot: shorts, sunglasses, watermelon. Winter is cold: we need a scarf, mittens and a jacket."),
         [("shortik", "kozoynak", "tarvuz", "sharf"), ("tarvuz", "shortik", "quyosh", "qolqop"), ("kozoynak", "quyosh", "shortik", "kurtka")]),
        (T("Oyoqlarini sana", "Посчитай ножки", "Count the legs"),
         T("{a}ning ikki oyog'i bor, qolganlarining to'rttadan", "{a} ходит на двух ногах, а остальные — на четырёх", "the {a} has two legs, the others have four"),
         T("It, mushuk, sigirning to'rttadan oyog'i bor. Qushlarning esa ikkita oyog'i va ikkita qanoti bor.",
           "У собаки, кошки, коровы по четыре ноги. А у птиц — две ноги и два крыла.",
           "Dogs, cats and cows have four legs each. Birds have two legs and two wings."),
         [("it", "mushuk", "sigir", "tovuq"), ("ot", "qoy", "it", "ordak"), ("fil", "sher", "mushuk", "pingvin")]),
        (T("Rangi boshqa", "Другой цвет", "A different color"),
         T("{a} — qizil emas, qolganlari qizil", "{a} — не красный, а остальные — красные", "the {a} is not red, the others are red"),
         T("Ba'zan narsalarni shakli bo'yicha emas, rangi bo'yicha guruhlaymiz. Olma, yurakcha, qizil kvadrat — hammasi qizil!",
           "Иногда мы делим вещи не по форме, а по цвету. Яблоко, сердечко, красный квадрат — все красные!",
           "Sometimes we group things not by shape but by color. An apple, a heart, a red square — all of them are red!"),
         [("olma", "yurak", "kvadrat", "kok"), ("qizil", "pomidor", "gilos", "yashil"), ("qulupnay", "kvadrat", "olma", "banan")]),
        (T("Uy jihozlari", "Мебель", "Furniture"),
         T("{a} — jihoz emas, qolganlari xonadagi jihozlar", "{a} — не мебель, а остальное — мебель", "the {a} is not furniture, the others are furniture"),
         T("Xonada jihozlar turadi: karavot, divan, stul. Ularda o'tiramiz va yotamiz. Velosiped esa — transport!",
           "В комнате стоит мебель: кровать, диван, стул. На них сидят и лежат. А велосипед — это транспорт!",
           "Furniture stands in a room: a bed, a sofa, a chair. We sit and lie on them. A bike is a vehicle!"),
         [("karavot", "divan", "stul", "velosiped"), ("stul", "karavot", "divan", "traktor"), ("divan", "stul", "karavot", "samolyot")]),
    ]
    for name, reason, explain, quads in odd:
        a, b, c, o = quads[0]
        k.lesson(name,
                 T("Bola ortiqcha narsani topadi va sababini o'z so'zi bilan tushuntiradi",
                   "Ребёнок находит лишнее и объясняет причину своими словами",
                   "The child finds the odd one out and explains the reason in their own words"),
                 T("Bip-bip! Endi biz kichik detektivmiz! {s} — bittasi begona. Lekin faqat topish yetmaydi — nega begonaligini ham aytamiz!",
                   "Бип-бип! Сегодня мы маленькие сыщики! {s} — один здесь чужой. Но мало его найти — надо ещё сказать, почему!",
                   "Beep-beep! Today we are little detectives! {s} — one of them doesn't belong. Finding it isn't enough — we'll also say why!").f(s=seq([a, o, b, c])),
                 [item(T("Belgi", "Признак", "Feature"), T("narsalarni guruhlaydigan xususiyat", "свойство, по которому делим вещи", "what we use to group things"),
                       seq([a, b, c]), explain, T("Belgini ayt: ular nimasi bilan o'xshash?", "Назови признак: чем они похожи?", "Say the feature: how are they alike?")),
                  item(T("Sabab", "Причина", "Reason"), T("«chunki» deb tushuntiramiz", "объясняем словом «потому что»", "we explain with “because”"),
                       E(o) + "❓",
                       T("{e} — ortiqcha. Nega? Chunki ", "{e} — лишний. Почему? Потому что ", "{e} is the odd one. Why? Because ").f(e=E(o)) + reason.f(a=W(o)) + T(".", ".", "."),
                       T("Sen ham «chunki» so'zi bilan tushuntir!", "Объясни и ты, используя слово «потому что»!", "Explain it yourself using the word “because”!"))],
                 [test(T("{s} Qaysi biri ortiqcha?", "{s} Что лишнее?", "{s} Which one doesn't belong?").f(s=seq([x, o_, y, z])),
                       [opt(o_), opt(x), opt(y)], 0, k.praise() + T(" ", " ", " ") + reason.f(a=W(o_)).cap() + T(".", ".", "."))
                  for x, y, z, o_ in quads],
                 [row(T("🕵️ Detektiv topishmog'i", "🕵️ Загадка сыщика", "🕵️ Detective riddle"),
                      T("O'yin! Uchta o'xshash va bitta boshqacha narsa o'yla. Oilangga topishmoq qil: «Qaysi biri ortiqcha va nima uchun?»",
                        "Игра! Придумай три похожие вещи и одну другую. Загадай семье: «Что лишнее и почему?»",
                        "Game! Think of three similar things and one different thing. Ask your family: “Which one doesn't belong, and why?”"),
                      [seq([a, b, c]) + " + " + E(o) + " ❓"])])

    # 3. O'xshatish (analogiya)
    k.unit(T("O'xshatish", "Аналогии", "Analogies"), "🔁")
    analog = [
        (T("Hayvon va uyi", "Животное и его дом", "Animals and homes"),
         [("qush", "uya", "baliq", "dengiz", ["orm", "uy"]), ("ayiq", "orm", "tuya", "chol", ["dengiz", "muz"]),
          ("pingvin", "muz", "qush", "uya", ["chol", "dengiz"])]),
        (T("Hayvon va ovqati", "Животное и его еда", "Animals and food"),
         [("quyon", "sabzi", "maymun", "banan", ["suyak", "asal"]), ("kuchuk", "suyak", "ari", "gul", ["banan", "sut"]),
          ("maymun", "banan", "mushuk", "sut", ["sabzi", "suyak"])]),
        (T("Nima nima uchun?", "Что для чего?", "What is it for?"),
         [("qolqop", "qor", "soyabon", "yomgir", ["quyosh", "olov"]), ("kalit", "qulf", "qaychi", "qogoz", ["eshik", "suv"]),
          ("chotka", "tish", "qoshiq", "kosa", ["qogoz", "tish"])]),
        (T("Kasb va asbob", "Профессия и инструмент", "Jobs and tools"),
         [("oshpaz", "tova", "rassom", "moyqalam", ["stetoskop", "otochirgich"]), ("shifokor", "stetoskop", "otochir", "otochirgich", ["tova", "moyqalam"]),
          ("dehqon", "traktor", "oshpaz", "tova", ["stetoskop", "samolyot"])]),
        (T("Qarama-qarshi", "Противоположности", "Opposites"),
         [("olov", "muz", "quyosh", "oy", ["yulduz", "olov"]), ("fil", "sichqon", "tarvuz", "gilos", ["olma", "tarvuz"]),
          ("tosh", "pat", "fil", "kapalak", ["sigir", "ayiq"])]),
        (T("Butun va bo'lagi", "Целое и часть", "Whole and part"),
         [("daraxt", "barg", "mashina", "gildirak", ["eshik", "qulf"]), ("uy", "eshik", "velosiped", "gildirak", ["kalit", "barg"]),
          ("gul", "barg", "uy", "eshik", ["gildirak", "nihol"])]),
    ]
    for name, rows in analog:
        a, b, c, d, wr = rows[0]
        k.lesson(name,
                 T("Bola ikki juftlik orasidagi o'xshashlikni topadi: «A — B ga, C — nimaga?»",
                   "Ребёнок находит сходство двух пар: «А относится к Б, как В — к чему?»",
                   "The child finds what two pairs share: “A goes with B, as C goes with what?”"),
                 T("Bip-bip! Bugun eng aqlli o'yin — o'xshatish! {a} ➡️ {b}. {c} ➡️ ❓ Birinchi juftlikning sirini topsang, ikkinchisini ham topasan!",
                   "Бип-бип! Сегодня самая умная игра — аналогии! {a} ➡️ {b}. {c} ➡️ ❓ Разгадаешь секрет первой пары — найдёшь и вторую!",
                   "Beep-beep! Today's smartest game is analogies! {a} ➡️ {b}. {c} ➡️ ❓ Solve the secret of the first pair and you'll find the second!").f(a=E(a), b=E(b), c=E(c)),
                 [item(T("Juftlik siri", "Секрет пары", "The pair's secret"), T("ikki narsa qanday bog'langan", "как связаны две вещи", "how two things are connected"),
                       E(a) + "➡️" + E(b),
                       T("Qara: {ea} {wa} va {eb} {wb}. Ular qanday bog'langan? Avval shuni o'ylaymiz — bu juftlikning siri.",
                         "Смотри: {ea} {wa} и {eb} {wb}. Как они связаны? Сначала думаем об этом — это секрет пары.",
                         "Look: {ea} the {wa} and {eb} the {wb}. How are they connected? First we think about that — it's the pair's secret.").f(ea=E(a), wa=W(a), eb=E(b), wb=W(b)),
                       None),
                  item(T("O'xshatish qoidasi", "Правило аналогии", "Analogy rule"), T("xuddi shu sirni boshqa juftlikka qo'llash", "тот же секрет для другой пары", "using the same secret for another pair"),
                       E(c) + "➡️" + E(d),
                       T("Endi xuddi shu sirni {ec} {wc} uchun qo'llaymiz: {ea} ➡️ {eb}, demak {ec} ➡️ {ed}! Javob — {wd}.",
                         "Теперь применим тот же секрет: {ea} ➡️ {eb}, значит {ec} ➡️ {ed}! Ответ — {wd}.",
                         "Now use the same secret for {ec} the {wc}: {ea} ➡️ {eb}, so {ec} ➡️ {ed}! The answer is the {wd}.").f(ea=E(a), eb=E(b), ec=E(c), ed=E(d), wc=W(c), wd=W(d)),
                       T("Ayt: «{a} va {b} — juftlik, {c} va {d} — ham juftlik!»", "Скажи: «{a} и {b} — пара, {c} и {d} — тоже пара!»",
                         "Say: “{a} and {b} are a pair, {c} and {d} are a pair too!”").f(a=W(a), b=W(b), c=W(c), d=W(d)))],
                 [test(T("{a} ➡️ {b}, {c} ➡️ ❓", "{a} ➡️ {b}, {c} ➡️ ❓", "{a} ➡️ {b}, {c} ➡️ ❓").f(a=E(x1), b=E(y1), c=E(x2)),
                       [opt(y2)] + [opt(w) for w in wrongs], 0,
                       k.praise() + T(" {a} — {b}, {c} — {d}.", " {a} — {b}, {c} — {d}.", " {a} goes with {b}, {c} goes with {d}.").f(a=E(x1), b=E(y1), c=E(x2), d=E(y2)))
                  for x1, y1, x2, y2, wrongs in rows],
                 [row(T("🎲 O'zing o'xshatish o'yla", "🎲 Придумай аналогию", "🎲 Make your own analogy"),
                      T("O'yin! O'zing o'xshatish o'ylab top va kattalardan so'ra. Masalan: «Qo'l — qo'lqopga, oyoq — nimaga?» (paypoqqa!)",
                        "Игра! Придумай свою аналогию и спроси взрослых. Например: «Рука — варежка, нога — что?» (носок!)",
                        "Game! Make up your own analogy and ask a grown-up. For example: “Hand goes with mitten, foot goes with what?” (sock!)"),
                      ["🖐️ ➡️ 🧤", "🦶 ➡️ ❓"])])

    # 4. Sabab va natija, 3 qadamli ketma-ketlik
    k.unit(T("Sabab va natija", "Причина и следствие", "Cause and effect"), "⛓️")
    cause = [
        (T("Muz va olov", "Лёд и огонь", "Ice and fire"),
         T("Agar muzni issiq joyga qo'ysak, u eriydi va suvga aylanadi. Agar suvni qattiq sovuqda qoldirsak — muz bo'ladi.",
           "Если положить лёд в тёплое место, он растает и станет водой. А если оставить воду на сильном морозе — она станет льдом.",
           "If we put ice in a warm place, it melts and turns into water. If we leave water out in the freezing cold, it turns into ice."),
         [(T("🧊 + ☀️ ➡️ ❓ Muz quyoshda nima bo'ladi?", "🧊 + ☀️ ➡️ ❓ Что будет со льдом на солнце?", "🧊 + ☀️ ➡️ ❓ What happens to ice in the sun?"),
           "suv", ["tosh", "qor"], T("Muz eriydi va suvga aylanadi.", "Лёд растает и станет водой.", "The ice melts into water.")),
          (T("💧 + ❄️ ➡️ ❓ Suv qattiq sovuqda nima bo'ladi?", "💧 + ❄️ ➡️ ❓ Что будет с водой на морозе?", "💧 + ❄️ ➡️ ❓ What happens to water in the freezing cold?"),
           "muz", ["olov", "gul"], T("Suv muzlaydi.", "Вода замёрзнет.", "The water freezes.")),
          (T("❄️ + ☀️ ➡️ ❓ Qor bahorda nima bo'ladi?", "❄️ + ☀️ ➡️ ❓ Что будет со снегом весной?", "❄️ + ☀️ ➡️ ❓ What happens to snow in spring?"),
           "kolmak", ["muz", "tosh"], T("Qor erib, ko'lmakka aylanadi.", "Снег растает и превратится в лужу.", "The snow melts into a puddle."))]),
        (T("Yomg'irdan keyin", "После дождя", "After the rain"),
         T("Yomg'ir yog'sa — yerda ko'lmak paydo bo'ladi, o'simliklar suv ichadi. Yomg'ir va quyosh birga bo'lsa — osmonda kamalak chiqadi!",
           "Если идёт дождь — на земле появляются лужи, а растения пьют воду. Если дождь и солнце вместе — на небе появляется радуга!",
           "When it rains, puddles appear and plants drink water. When there is rain and sun together, a rainbow appears in the sky!"),
         [(T("🌧️ + ☀️ ➡️ ❓ Osmonda nima chiqadi?", "🌧️ + ☀️ ➡️ ❓ Что появится на небе?", "🌧️ + ☀️ ➡️ ❓ What appears in the sky?"),
           "kamalak", ["oy", "qor"], T("Kamalak chiqadi!", "Появится радуга!", "A rainbow appears!")),
          (T("🌧️ ➡️ ❓ Yomg'irdan keyin yo'lda nima bo'ladi?", "🌧️ ➡️ ❓ Что будет на дороге после дождя?", "🌧️ ➡️ ❓ What is on the road after rain?"),
           "kolmak", ["olov", "qor"], T("Ko'lmaklar paydo bo'ladi.", "Появятся лужи.", "Puddles appear.")),
          (T("🌷 + 🚫💧 ➡️ ❓ Gulga suv bermasak nima bo'ladi?", "🌷 + 🚫💧 ➡️ ❓ Что будет, если не поливать цветок?", "🌷 + 🚫💧 ➡️ ❓ What happens if we don't water a flower?"),
           "soligan", ["lola", "daraxt"], T("Gul so'lib qoladi.", "Цветок завянет.", "The flower wilts."))]),
        (T("Olma qanday pishadi?", "Как созревает яблоко?", "How does an apple grow?"),
         T("Bahorda daraxtda gul ochiladi. Gul o'rnida kichkina xom olma paydo bo'ladi. Yoz bo'yi quyoshda pishib, qizil olmaga aylanadi.",
           "Весной на дереве распускаются цветы. На месте цветка появляется маленькое зелёное яблочко. За лето оно зреет на солнце и становится красным.",
           "In spring the tree blossoms. Where the flower was, a little green apple appears. All summer it ripens in the sun and turns red."),
         [(T("🌼 ➡️ 🍏 ➡️ ❓ Oxirida nima bo'ladi?", "🌼 ➡️ 🍏 ➡️ ❓ Что будет в конце?", "🌼 ➡️ 🍏 ➡️ ❓ What happens at the end?"),
           "olma", ["urug", "barg"], T("Pishgan qizil olma!", "Спелое красное яблоко!", "A ripe red apple!")),
          (T("❓ ➡️ 🍏 ➡️ 🍎 Eng avval nima bo'ladi?", "❓ ➡️ 🍏 ➡️ 🍎 Что бывает сначала?", "❓ ➡️ 🍏 ➡️ 🍎 What comes first?"),
           "olma_gul", ["olma", "nihol"], T("Avval olma guli ochiladi.", "Сначала распускается цветок яблони.", "First the apple blossom opens.")),
          (T("🌰 ➡️ ❓ ➡️ 🌳 O'rtada nima bo'ladi?", "🌰 ➡️ ❓ ➡️ 🌳 Что посередине?", "🌰 ➡️ ❓ ➡️ 🌳 What is in the middle?"),
           "nihol", ["olma", "barg"], T("Urug'dan avval nihol chiqadi.", "Из семечка сначала появляется росток.", "First a sprout comes out of the seed."))]),
        (T("Kunimiz tartibi", "Порядок дня", "Our daily routine"),
         T("Ertalab uyg'onamiz, tish yuvamiz, nonushta qilamiz, keyin bog'chaga boramiz. Kechqurun cho'milib, uxlaymiz. Har ishning o'z vaqti bor!",
           "Утром мы просыпаемся, чистим зубы, завтракаем, потом идём в садик. Вечером купаемся и ложимся спать. Всему своё время!",
           "In the morning we wake up, brush our teeth, have breakfast and go to kindergarten. In the evening we take a bath and go to sleep. Everything has its time!"),
         [(T("🛏️ ➡️ 🪥 ➡️ ❓ Tish yuvgandan keyin nima?", "🛏️ ➡️ 🪥 ➡️ ❓ Что после чистки зубов?", "🛏️ ➡️ 🪥 ➡️ ❓ What comes after brushing teeth?"),
           T("🍳 nonushta", "🍳 завтрак", "🍳 breakfast"), [T("🛏️ yana uxlash", "🛏️ снова спать", "🛏️ back to sleep"), T("🌙 tun", "🌙 ночь", "🌙 night")],
           T("Nonushta qilamiz!", "Завтракаем!", "We have breakfast!")),
          (T("🍳 ➡️ ❓ Nonushtadan keyin qayerga boramiz?", "🍳 ➡️ ❓ Куда идём после завтрака?", "🍳 ➡️ ❓ Where do we go after breakfast?"),
           T("🎒 bog'chaga", "🎒 в садик", "🎒 to kindergarten"), [T("🛏️ karavotga", "🛏️ в кровать", "🛏️ to bed"), T("🌙 oyga", "🌙 на луну", "🌙 to the moon")],
           T("Sumkani olib, bog'chaga boramiz.", "Берём рюкзак и идём в садик.", "We take our backpack and go to kindergarten.")),
          (T("🌙 ➡️ ❓ Kechasi nima qilamiz?", "🌙 ➡️ ❓ Что делаем ночью?", "🌙 ➡️ ❓ What do we do at night?"),
           T("🛏️ uxlaymiz", "🛏️ спим", "🛏️ we sleep"), [T("🎒 bog'chaga boramiz", "🎒 идём в садик", "🎒 go to kindergarten"), T("⚽ futbol o'ynaymiz", "⚽ играем в футбол", "⚽ play football")],
           T("Kechasi uxlaymiz.", "Ночью мы спим.", "At night we sleep."))]),
        (T("Agar..., unda...", "Если..., то...", "If..., then..."),
         T("«Agar» va «unda» — sehrli so'zlar. Agar to'pni tepsak — u dumalaydi. Agar sharni puflasak — u kattalashadi. Agar ko'p yugursak — charchaymiz.",
           "«Если» и «то» — волшебные слова. Если пнуть мяч — он покатится. Если надувать шарик — он станет большим. Если долго бегать — устанем.",
           "“If” and “then” are magic words. If we kick a ball, then it rolls. If we blow into a balloon, then it gets big. If we run a lot, then we get tired."),
         [(T("Agar sharni puflasak, unda u... ❓", "Если надувать шарик, то он... ❓", "If we blow into a balloon, then it... ❓"),
           T("🎈 kattalashadi", "🎈 становится больше", "🎈 gets bigger"),
           [T("🪨 toshga aylanadi", "🪨 станет камнем", "🪨 turns into a stone"), T("🪶 yo'qolib qoladi", "🪶 исчезнет", "🪶 disappears")],
           T("Shar kattalashadi.", "Шарик станет большим.", "The balloon gets bigger.")),
          (T("Agar qorong'i tushsa, unda osmonda... ❓", "Если стемнеет, то на небе... ❓", "If it gets dark, then in the sky... ❓"),
           "oy", ["quyosh", "kamalak"], T("Oy va yulduzlar chiqadi.", "Появятся луна и звёзды.", "The moon and stars come out.")),
          (T("Agar tovuq tuxumni bossa, unda... ❓", "Если курица высидит яйцо, то... ❓", "If a hen sits on an egg, then... ❓"),
           "joja", ["olma", "baliq"], T("Jo'ja chiqadi.", "Вылупится цыплёнок.", "A chick hatches."))]),
        (T("Kapalakning hayoti", "Жизнь бабочки", "A butterfly's life"),
         T("Kapalak avval kichkina tuxum bo'ladi. Tuxumdan qurtcha chiqadi va ko'p barg yeydi. Keyin u pillaga o'ralib uxlaydi va kapalak bo'lib uchib chiqadi!",
           "Сначала бабочка — маленькое яичко. Из яичка появляется гусеница и ест много листьев. Потом она заворачивается в кокон, спит и вылетает бабочкой!",
           "A butterfly starts as a tiny egg. A caterpillar comes out and eats lots of leaves. Then it wraps itself in a cocoon, sleeps and flies out as a butterfly!"),
         [(T("🥚 ➡️ 🐛 ➡️ ❓ Oxirida kim bo'ladi?", "🥚 ➡️ 🐛 ➡️ ❓ Кем станет в конце?", "🥚 ➡️ 🐛 ➡️ ❓ What does it become at the end?"),
           "kapalak", ["qush", "ari"], T("Kapalak bo'ladi!", "Станет бабочкой!", "It becomes a butterfly!")),
          (T("❓ ➡️ 🐛 ➡️ 🦋 Eng avval nima?", "❓ ➡️ 🐛 ➡️ 🦋 Что самое первое?", "❓ ➡️ 🐛 ➡️ 🦋 What comes first?"),
           "tuxum", ["barg", "gul"], T("Eng avval kichkina tuxum.", "Сначала маленькое яичко.", "First a tiny egg.")),
          (T("🐛 Qurtcha nima yeydi?", "🐛 Что ест гусеница?", "🐛 What does the caterpillar eat?"),
           "barg", ["sut", "suyak"], T("Qurtcha barg yeydi.", "Гусеница ест листья.", "The caterpillar eats leaves."))]),
    ]
    for name, explain, qs in cause:
        first = qs[0]
        k.lesson(name,
                 T("Bola sabab va natijani bog'laydi, voqealar tartibini tushuntiradi",
                   "Ребёнок связывает причину и следствие, объясняет порядок событий",
                   "The child connects cause and effect and explains the order of events"),
                 T("Bip-bip! Hamma narsaning sababi bor! Nima bo'lsa — keyin nima bo'ladi? Qani, olimlar kabi o'ylaymiz!",
                   "Бип-бип! У всего есть причина! Что случится — и что будет потом? Давай думать, как учёные!",
                   "Beep-beep! Everything has a cause! If something happens — what happens next? Let's think like scientists!"),
                 [item(T("Sababi", "Почему?", "The cause"), T("nima uchun bo'ldi", "почему это случилось", "why it happened"), "❓➡️", explain,
                       T("Ayt: «Agar..., unda...»", "Скажи: «Если..., то...»", "Say: “If..., then...”")),
                  item(T("Natijasi", "Что потом?", "The effect"), T("keyin nima bo'ldi", "что случилось потом", "what happened next"), "➡️" + (E(first[1]) if isinstance(first[1], str) else first[1].uz.split()[0]),
                       first[3] + T(" Bu — natija: sabab bo'lgani uchun shunday bo'ldi.", " Это — следствие: так случилось из-за причины.",
                                    " This is the effect: it happened because of the cause."),
                       None)],
                 [q3(qt, opt(ans), [opt(x) for x in wr], why) for qt, ans, wr, why in qs],
                 [row(T("🔬 Kichik tajriba", "🔬 Маленький опыт", "🔬 A little experiment"),
                      T("Tajriba kattalar bilan! Likopchaga bitta muz bo'lagini qo'y va derazaga qo'y. Har 10 daqiqada qara: nima bo'lyapti? Nega?",
                        "Опыт со взрослыми! Положи кусочек льда на тарелку и поставь на подоконник. Каждые 10 минут смотри: что происходит? Почему?",
                        "An experiment with a grown-up! Put an ice cube on a plate by the window. Check every 10 minutes: what is happening? Why?"),
                      ["🧊 + ☀️ ➡️ 💧"], turi="amaliy")])

    # 5. Mantiqiy savollar
    k.unit(T("Mantiqiy savollar", "Логические задачки", "Logic puzzles"), "🧠")
    names3 = T("Ali, Vali, Sara", "Али, Вали, Сара", "Ali, Vali, Sara")
    ali, vali, sara = (T("🧒 Ali", "🧒 Али", "🧒 Ali"), T("👦 Vali", "👦 Вали", "👦 Vali"), T("👧 Sara", "👧 Сара", "👧 Sara"))
    logic = [
        (T("Kim baland?", "Кто выше?", "Who is taller?"),
         T("Solishtirish zanjiri: agar Ali Validan baland, Vali esa Saradan baland bo'lsa — Ali hammadan baland! Bosqichma-bosqich o'ylaymiz.",
           "Цепочка сравнений: если Али выше Вали, а Вали выше Сары, — значит, Али выше всех! Думаем шаг за шагом.",
           "A chain of comparisons: if Ali is taller than Vali, and Vali is taller than Sara, then Ali is the tallest! We think step by step."),
         [(T("Ali Validan baland. Vali Saradan baland. Kim eng baland?", "Али выше Вали. Вали выше Сары. Кто самый высокий?",
             "Ali is taller than Vali. Vali is taller than Sara. Who is the tallest?"), ali, [vali, sara], T("Ali eng baland.", "Али самый высокий.", "Ali is the tallest.")),
          (T("Sara Alidan past. Ali Validan past. Kim eng past?", "Сара ниже Али. Али ниже Вали. Кто самый низкий?",
             "Sara is shorter than Ali. Ali is shorter than Vali. Who is the shortest?"), sara, [ali, vali], T("Sara eng past.", "Сара самая низкая.", "Sara is the shortest.")),
          (T("🐘 otdan katta. 🐴 ayiqdan katta. Kim katta: fil yoki ayiq?", "🐘 больше лошади. 🐴 больше медведя. Кто больше: слон или медведь?",
             "🐘 is bigger than a horse. 🐴 is bigger than a bear. Who is bigger: the elephant or the bear?"),
           opt("fil"), [opt("ayiq"), opt("ot")], T("Fil katta.", "Слон больше.", "The elephant is bigger."))]),
        (T("Qayerda yashirindi?", "Где спрятался?", "Where is it hiding?"),
         T("Bu o'yinda «yo'q» joylarni chiqarib tashlaymiz. Qaysi joy qolsa — javob o'sha!",
           "В этой игре мы убираем места, где «нет». Какое место осталось — там и ответ!",
           "In this game we cross out the places where it's “not”. The place that's left is the answer!"),
         [(T("Mushuk qutida emas. Savatda ham emas. Mushuk qayerda?", "Кошки нет в коробке. И в корзине нет. Где кошка?",
             "The cat is not in the box. It's not in the basket either. Where is the cat?"),
           T("🛏️ karavot ostida", "🛏️ под кроватью", "🛏️ under the bed"), [T("📦 qutida", "📦 в коробке", "📦 in the box"), T("🧺 savatda", "🧺 в корзине", "🧺 in the basket")],
           T("Qolgan joy — karavot ostida!", "Осталось одно место — под кроватью!", "The only place left is under the bed!")),
          (T("To'p stulda emas. Karavotda emas. To'p qayerda?", "Мяча нет на стуле. И на кровати нет. Где мяч?",
             "The ball is not on the chair. It's not on the bed. Where is the ball?"),
           T("📦 qutida", "📦 в коробке", "📦 in the box"), [T("🪑 stulda", "🪑 на стуле", "🪑 on the chair"), T("🛏️ karavotda", "🛏️ на кровати", "🛏️ on the bed")],
           T("To'p qutida!", "Мяч в коробке!", "The ball is in the box!")),
          (T("Quyon daraxt ortida emas. Uyda ham emas. Quyon qayerda?", "Зайчика нет за деревом. И в домике нет. Где зайчик?",
             "The bunny is not behind the tree. It's not in the house. Where is the bunny?"),
           T("🌸 gullar orasida", "🌸 среди цветов", "🌸 among the flowers"), [T("🌳 daraxt ortida", "🌳 за деревом", "🌳 behind the tree"), T("🏠 uyda", "🏠 в домике", "🏠 in the house")],
           T("Quyon gullar orasida!", "Зайчик среди цветов!", "The bunny is among the flowers!"))]),
        (T("Ha yoki yo'q?", "Да или нет?", "Yes or no?"),
         T("Agar «hamma qushlarning qanoti bor» desak va chumchuq qush bo'lsa — demak, chumchuqning ham qanoti bor. Bu — mantiq!",
           "Если «у всех птиц есть крылья», а воробей — птица, значит, у воробья тоже есть крылья. Это — логика!",
           "If “all birds have wings” and a sparrow is a bird, then a sparrow has wings too. That's logic!"),
         [(T("Hamma qushlarning qanoti bor. Boyqush — qush. Boyqushning qanoti bormi?", "У всех птиц есть крылья. Сова — птица. Есть ли у совы крылья?",
             "All birds have wings. An owl is a bird. Does an owl have wings?"), opt("ha"), [opt("yoq")], T("Ha, boyqushning qanoti bor.", "Да, у совы есть крылья.", "Yes, an owl has wings.")),
          (T("Hamma baliqlar suvda yashaydi. Mushuk — baliq emas. Mushuk suvda yashaydimi?", "Все рыбы живут в воде. Кошка — не рыба. Живёт ли кошка в воде?",
             "All fish live in water. A cat is not a fish. Does a cat live in water?"), opt("yoq"), [opt("ha")], T("Yo'q, mushuk quruqlikda yashaydi.", "Нет, кошка живёт на суше.", "No, a cat lives on land.")),
          (T("Hamma mevalar daraxtda yoki butada o'sadi. Olma — meva. Olma o'sadimi?", "Все фрукты растут на деревьях или кустах. Яблоко — фрукт. Растёт ли яблоко?",
             "All fruits grow on trees or bushes. An apple is a fruit. Does an apple grow?"), opt("ha"), [opt("yoq")], T("Ha, olma daraxtda o'sadi.", "Да, яблоко растёт на дереве.", "Yes, an apple grows on a tree."))]),
        (T("Nechta bo'ladi?", "Сколько получится?", "How many?"),
         T("Mantiqiy sanoq: bitta qushning ikki oyog'i bor. Ikkita qush — ikki marta ko'p: to'rtta oyoq! Rasmini xayolda chizib, sanaymiz.",
           "Логический счёт: у одной птицы две ноги. Две птицы — вдвое больше: четыре ноги! Рисуем в уме и считаем.",
           "Logical counting: one bird has two legs. Two birds have twice as many: four legs! We picture it in our head and count."),
         [(T("🐦🐦 Ikkita qushning nechta oyog'i bor?", "🐦🐦 Сколько ног у двух птичек?", "🐦🐦 How many legs do two birds have?"), opt(4), [opt(2), opt(6)],
           T("2 + 2 = 4 oyoq.", "2 + 2 = 4 ноги.", "2 + 2 = 4 legs.")),
          (T("🐱🐱 Ikkita mushukning nechta qulog'i bor?", "🐱🐱 Сколько ушей у двух кошек?", "🐱🐱 How many ears do two cats have?"), opt(4), [opt(2), opt(8)],
           T("Har birida ikkitadan: 4 ta quloq.", "У каждой по два: 4 уха.", "Two each: 4 ears.")),
          (T("🖐️🖐️ Ikki qo'lda nechta barmoq bor?", "🖐️🖐️ Сколько пальцев на двух руках?", "🖐️🖐️ How many fingers on two hands?"), opt(10), [opt(5), opt(8)],
           T("5 + 5 = 10 barmoq.", "5 + 5 = 10 пальцев.", "5 + 5 = 10 fingers."))]),
        (T("Tarozi", "Весы", "The scales"),
         T("Tarozining og'ir tomoni pastga tushadi, yengil tomoni tepaga ko'tariladi. Qaysi tomon pastda bo'lsa — o'sha og'ir!",
           "Тяжёлая сторона весов опускается вниз, а лёгкая поднимается вверх. Какая сторона внизу — та и тяжелее!",
           "The heavy side of the scales goes down and the light side goes up. Whichever side is lower is heavier!"),
         [(T("⚖️ 🍉 pastda, 🍒 tepada. Qaysi biri og'ir?", "⚖️ 🍉 внизу, 🍒 вверху. Что тяжелее?", "⚖️ 🍉 is down, 🍒 is up. Which is heavier?"),
           opt("tarvuz"), [opt("gilos")], T("Tarvuz og'ir — u pastga tushdi.", "Арбуз тяжелее — он опустился вниз.", "The watermelon is heavier — it went down.")),
          (T("⚖️ 🪶 tepada, 🪨 pastda. Qaysi biri yengil?", "⚖️ 🪶 вверху, 🪨 внизу. Что легче?", "⚖️ 🪶 is up, 🪨 is down. Which is lighter?"),
           opt("pat"), [opt("tosh")], T("Pat yengil — u tepaga ko'tarildi.", "Пёрышко легче — оно поднялось вверх.", "The feather is lighter — it went up.")),
          (T("⚖️ 🍎 va 🍎 teng turibdi. Ular qanday?", "⚖️ 🍎 и 🍎 стоят ровно. Какие они?", "⚖️ 🍎 and 🍎 are level. What does that mean?"),
           T("🟰 bir xil og'ir", "🟰 одинаково тяжёлые", "🟰 equally heavy"), [T("⬇️ biri og'ir", "⬇️ одно тяжелее", "⬇️ one is heavier")],
           T("Tarozi teng — ular bir xil og'ir.", "Весы ровно — они одинаково тяжёлые.", "The scales are level — they weigh the same."))]),
        (T("Topishmoqlar", "Загадки", "Riddles"),
         T("Topishmoqda narsaning belgilari aytiladi. Har belgini eshitib, mos kelmaganlarini chiqarib tashlaymiz. Oxirida bitta javob qoladi!",
           "В загадке называют признаки предмета. Слушаем каждый признак и убираем то, что не подходит. В конце остаётся один ответ!",
           "A riddle tells you the features of something. We listen to each feature and cross out what doesn't fit. At the end one answer is left!"),
         [(T("Quloqlari uzun, sakrab yuradi, sabzi yeydi. Bu kim?", "Уши длинные, прыгает, ест морковку. Кто это?",
             "Long ears, it hops, it eats carrots. Who is it?"), opt("quyon"), [opt("ayiq"), opt("baliq")], T("Bu — quyon!", "Это — зайчик!", "It's a bunny!")),
          (T("Kunduzi osmonda, issiq va yorug'. Bu nima?", "Днём на небе, тёплое и светлое. Что это?",
             "In the sky by day, warm and bright. What is it?"), opt("quyosh"), [opt("oy"), opt("bulut")],
           T("Bu — quyosh!", "Это — солнце!", "It's the sun!")),
          (T("Bo'yni juda uzun, daraxt barglarini yeydi. Bu kim?", "Шея очень длинная, ест листья с деревьев. Кто это?",
             "A very long neck, it eats leaves from trees. Who is it?"), opt("jirafa"), [opt("fil"), opt("ot")], T("Bu — jirafa!", "Это — жираф!", "It's a giraffe!"))]),
    ]
    for name, explain, qs in logic:
        k.lesson(name,
                 T("Bola sodda mantiqiy masalalarni bosqichma-bosqich o'ylab yechadi",
                   "Ребёнок шаг за шагом решает простые логические задачки",
                   "The child solves simple logic puzzles step by step"),
                 T("Bip-bip! Bugun miyamizni mashq qildiramiz! Shoshilmaymiz, har gapni diqqat bilan tinglaymiz va o'ylaymiz.",
                   "Бип-бип! Сегодня тренируем мозг! Не торопимся, внимательно слушаем каждое слово и думаем.",
                   "Beep-beep! Today we exercise our brain! No rushing — we listen carefully to every word and think."),
                 [item(T("Mantiq", "Логика", "Logic"), T("to'g'ri o'ylash", "правильно рассуждать", "thinking it through"), "🧠", explain,
                       T("Barmog'ingni chakkangga qo'yib, «O'ylayapman!» de.", "Приложи пальчик к виску и скажи: «Я думаю!»",
                         "Put your finger on your temple and say “I'm thinking!”")),
                  item(T("Bosqichma-bosqich", "Шаг за шагом", "Step by step"), T("bitta-bittadan o'ylaymiz", "думаем по шагу", "we think one step at a time"),
                       "1️⃣➡️2️⃣➡️3️⃣",
                       T("Qiyin savolni bo'laklarga bo'lamiz: avval birinchi gapni o'ylaymiz, keyin ikkinchisini. Oxirida javob o'zi ochiladi!",
                         "Трудный вопрос делим на части: сначала думаем о первой фразе, потом о второй. В конце ответ откроется сам!",
                         "We split a hard question into parts: first we think about the first sentence, then the second. At the end the answer appears by itself!"),
                       None)],
                 [q3(qt, right, wr, why) for qt, right, wr, why in qs],
                 [row(T("🧠 Oilaviy topishmoq", "🧠 Семейная загадка", "🧠 Family riddle"),
                      T("O'yin! Bir narsa o'yla va uning uchta belgisini ayt. Oilang topsin! Keyin ular senga topishmoq aytsin.",
                        "Игра! Задумай предмет и назови три его признака. Пусть семья отгадает! А потом пусть загадают тебе.",
                        "Game! Think of something and say three things about it. Let your family guess! Then they give you a riddle."),
                      ["❓ 1️⃣ 2️⃣ 3️⃣ ➡️ 💡"], turi="amaliy")])
    return k


def yoz():
    TR.clear()
    out = {}
    for key, fn in (("23y", yosh23), ("45y", yosh45), ("67y", yosh67)):
        book = fn().book(key)
        validate(book)
        (ROOT / f"mn_{key}.json").write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
        out[key] = book
    # tarjimalar → izoh lug'atlari
    for i, code in ((0, "ru"), (1, "en")):
        path = IZOH / f"{code}.json"
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"t": {}}
        for uz, tr in TR.items():
            data["t"].setdefault(sid(uz), tr[i])   # til kitoblarida bor matn — o'sha tarjimasi qoladi
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    for key, b in yoz().items():
        print("mn", key, b["age"], len(b["units"]), "bo'lim", sum(len(u["lessons"]) for u in b["units"]), "dars")
    print("tarjima:", len(TR), "matn")

"""REV187: KABUTAR TV — kontent banki (ssenariychi shu yerdan tanlaydi).

Mavzular: kun iborasi (hayotiy so'z birikmalari), bayram va madaniyat (sana bo'yicha), ob-havo (internetdan — Open-Meteo,
kalitsiz), kundalik hayot (dars matnlaridan kalit so'z bo'yicha). Siyosat, jinoyat, qo'rqinchli mavzular yo'q — faqat
yoshga mos, ta'limga oid, hayotiy narsalar. Daraja: k — 2–7 yosh va 1–4-sinf, o — 5–8-sinf, y — 9–11-sinf.
"""
import datetime as dt
import json
import urllib.request

# ── Kun iborasi: (ibora, o'zbekcha ma'nosi, misol gap, daraja) ──
IBORALAR = {
    "en": [
        ("Good morning!", "Xayrli tong!", "Good morning, Mum!", "k"), ("Thank you very much!", "Katta rahmat!", "Thank you very much for the gift!", "k"),
        ("Excuse me.", "Kechirasiz.", "Excuse me, where is the library?", "k"), ("Well done!", "Barakalla!", "Well done, you got it right!", "k"),
        ("Let's go!", "Ketdik!", "Let's go to the park!", "k"), ("I'm hungry.", "Qornim ochdi.", "I'm hungry. Can I have an apple?", "k"),
        ("See you later!", "Keyinroq ko'rishamiz!", "See you later, Ali!", "k"), ("My bad!", "Mening xatoim!", "Oops, my bad! I took your pen.", "o"),
        ("No worries.", "Hechqisi yo'q.", "No worries, I can help you.", "o"), ("I can't wait!", "Sabrim chidamayapti!", "The holidays start tomorrow. I can't wait!", "o"),
        ("Give it a try!", "Bir urinib ko'r!", "It's not difficult. Give it a try!", "o"), ("Take your time.", "Shoshilmang.", "Take your time and read the question.", "o"),
        ("It's up to you.", "O'zingiz hal qiling.", "Tea or juice? It's up to you.", "y"), ("Break a leg!", "Omad tilayman! (sahnaga chiqayotganga)", "Your concert is today? Break a leg!", "y"),
        ("Piece of cake.", "Juda oson.", "This test was a piece of cake.", "y"), ("Better late than never.", "Kech bo'lsa ham, yo'qdan yaxshi.", "You finished the project! Better late than never.", "y"),
    ],
    "de": [
        ("Guten Morgen!", "Xayrli tong!", "Guten Morgen, Mama!", "k"), ("Danke schön!", "Katta rahmat!", "Danke schön für das Geschenk!", "k"),
        ("Entschuldigung.", "Kechirasiz.", "Entschuldigung, wo ist die Schule?", "k"), ("Super gemacht!", "Barakalla!", "Super gemacht, das ist richtig!", "k"),
        ("Los geht's!", "Ketdik!", "Los geht's in den Park!", "k"), ("Ich habe Hunger.", "Qornim ochdi.", "Ich habe Hunger. Darf ich einen Apfel?", "k"),
        ("Bis später!", "Keyinroq ko'rishamiz!", "Bis später, Ali!", "k"), ("Mein Fehler!", "Mening xatoim!", "Oh, mein Fehler! Das ist dein Stift.", "o"),
        ("Kein Problem.", "Hechqisi yo'q.", "Kein Problem, ich helfe dir.", "o"), ("Ich freue mich!", "Juda xursandman!", "Morgen sind Ferien. Ich freue mich!", "o"),
        ("Probier es mal!", "Bir urinib ko'r!", "Es ist nicht schwer. Probier es mal!", "o"), ("Lass dir Zeit.", "Shoshilma.", "Lass dir Zeit und lies die Frage.", "o"),
        ("Das ist mir egal.", "Menga farqi yo'q.", "Tee oder Saft? Das ist mir egal.", "y"), ("Toi, toi, toi!", "Omad tilayman!", "Heute ist dein Konzert? Toi, toi, toi!", "y"),
        ("Kinderleicht!", "Juda oson!", "Der Test war kinderleicht.", "y"), ("Übung macht den Meister.", "Mashq ustoz qiladi.", "Jeden Tag lesen — Übung macht den Meister.", "y"),
    ],
    "fr": [
        ("Bonjour !", "Salom! / Xayrli kun!", "Bonjour, maman !", "k"), ("Merci beaucoup !", "Katta rahmat!", "Merci beaucoup pour le cadeau !", "k"),
        ("Excusez-moi.", "Kechirasiz.", "Excusez-moi, où est l'école ?", "k"), ("Bravo !", "Barakalla!", "Bravo, c'est juste !", "k"),
        ("On y va !", "Ketdik!", "On y va au parc !", "k"), ("J'ai faim.", "Qornim ochdi.", "J'ai faim. Je peux avoir une pomme ?", "k"),
        ("À plus tard !", "Keyinroq ko'rishamiz!", "À plus tard, Ali !", "k"), ("C'est ma faute !", "Mening xatoim!", "Oh, c'est ma faute ! C'est ton stylo.", "o"),
        ("Pas de souci.", "Hechqisi yo'q.", "Pas de souci, je t'aide.", "o"), ("J'ai hâte !", "Sabrim chidamayapti!", "Les vacances commencent demain. J'ai hâte !", "o"),
        ("Essaie !", "Urinib ko'r!", "Ce n'est pas difficile. Essaie !", "o"), ("Prends ton temps.", "Shoshilma.", "Prends ton temps et lis la question.", "o"),
        ("Comme tu veux.", "O'zing bilasan.", "Du thé ou du jus ? Comme tu veux.", "y"), ("Bonne chance !", "Omad!", "Ton concert est aujourd'hui ? Bonne chance !", "y"),
        ("C'est du gâteau.", "Juda oson.", "Ce test, c'est du gâteau.", "y"), ("Petit à petit, l'oiseau fait son nid.", "Tomchi-tomchi ko'l bo'lur.", "Un mot par jour : petit à petit, l'oiseau fait son nid.", "y"),
    ],
    "es": [
        ("¡Buenos días!", "Xayrli tong!", "¡Buenos días, mamá!", "k"), ("¡Muchas gracias!", "Katta rahmat!", "¡Muchas gracias por el regalo!", "k"),
        ("Perdón.", "Kechirasiz.", "Perdón, ¿dónde está la escuela?", "k"), ("¡Muy bien!", "Barakalla!", "¡Muy bien, es correcto!", "k"),
        ("¡Vamos!", "Ketdik!", "¡Vamos al parque!", "k"), ("Tengo hambre.", "Qornim ochdi.", "Tengo hambre. ¿Puedo comer una manzana?", "k"),
        ("¡Hasta luego!", "Keyinroq ko'rishamiz!", "¡Hasta luego, Ali!", "k"), ("¡Culpa mía!", "Mening xatoim!", "¡Uy, culpa mía! Es tu lápiz.", "o"),
        ("No pasa nada.", "Hechqisi yo'q.", "No pasa nada, te ayudo.", "o"), ("¡Qué ganas!", "Sabrim chidamayapti!", "Mañana empiezan las vacaciones. ¡Qué ganas!", "o"),
        ("¡Inténtalo!", "Urinib ko'r!", "No es difícil. ¡Inténtalo!", "o"), ("Tranquilo.", "Shoshilma, xotirjam bo'l.", "Tranquilo, lee la pregunta.", "o"),
        ("Como quieras.", "O'zing bilasan.", "¿Té o zumo? Como quieras.", "y"), ("¡Mucha suerte!", "Omad tilayman!", "¿Tu concierto es hoy? ¡Mucha suerte!", "y"),
        ("Es pan comido.", "Juda oson.", "El examen fue pan comido.", "y"), ("Poco a poco se va lejos.", "Sekin-sekin uzoqqa boriladi.", "Una palabra al día: poco a poco se va lejos.", "y"),
    ],
    "ru": [
        ("Доброе утро!", "Xayrli tong!", "Доброе утро, мама!", "k"), ("Большое спасибо!", "Katta rahmat!", "Большое спасибо за подарок!", "k"),
        ("Извините.", "Kechirasiz.", "Извините, где школа?", "k"), ("Молодец!", "Barakalla!", "Молодец, правильно!", "k"),
        ("Пойдём!", "Ketdik!", "Пойдём в парк!", "k"), ("Я хочу есть.", "Qornim ochdi.", "Я хочу есть. Можно яблоко?", "k"),
        ("До встречи!", "Ko'rishguncha!", "До встречи, Али!", "k"), ("Моя ошибка!", "Mening xatoim!", "Ой, моя ошибка! Это твоя ручка.", "o"),
        ("Ничего страшного.", "Hechqisi yo'q.", "Ничего страшного, я помогу.", "o"), ("Жду не дождусь!", "Sabrim chidamayapti!", "Завтра каникулы. Жду не дождусь!", "o"),
        ("Попробуй!", "Urinib ko'r!", "Это не трудно. Попробуй!", "o"), ("Не торопись.", "Shoshilma.", "Не торопись и прочитай вопрос.", "o"),
        ("Как хочешь.", "O'zing bilasan.", "Чай или сок? Как хочешь.", "y"), ("Ни пуха ни пера!", "Omad! (imtihon oldidan)", "Завтра экзамен? Ни пуха ни пера!", "y"),
        ("Проще простого.", "Juda oson.", "Этот тест — проще простого.", "y"), ("Повторение — мать учения.", "Takrorlash — bilim onasi.", "Каждый день повторяй: повторение — мать учения.", "y"),
    ],
}

# ── Bayram va madaniyat: (oy, kun, o'zbekcha matn (Nilufar opa), {til: tabrik}, faqat shu tillarda (bo'sh — hammasi)) ──
BAYRAMLAR = [
    (1, 1, "Bugun Yangi yil! Hammaga yangi yilda yangi bilim tilaymiz.",
     {"en": "Happy New Year!", "de": "Frohes neues Jahr!", "fr": "Bonne année !", "es": "¡Feliz Año Nuevo!", "ru": "С Новым годом!"}, ()),
    (1, 14, "Bugun Vatan himoyachilari kuni. Askarlarimizga rahmat aytamiz.",
     {"en": "Thank you, defenders!", "de": "Danke, liebe Verteidiger!", "fr": "Merci aux défenseurs !", "es": "¡Gracias, defensores!", "ru": "Спасибо защитникам!"}, ()),
    (3, 8, "Bugun 8-mart — onalar, opa-singillar va ustozlar bayrami. Onangizni bir quchoqlab qo'ying!",
     {"en": "Happy Mother's Day, Mum!", "de": "Alles Gute zum Frauentag!", "fr": "Bonne fête des femmes !", "es": "¡Feliz Día de la Mujer!", "ru": "С 8 Марта, мама!"}, ()),
    (3, 21, "Bugun Navro'z — bahor va yangi kun bayrami. Sumalak pishadi, hamma bir-birini tabriklaydi.",
     {"en": "Happy Navruz! Spring is here!", "de": "Frohes Navruz! Der Frühling ist da!", "fr": "Joyeux Navruz ! Le printemps est là !", "es": "¡Feliz Navruz! ¡Llegó la primavera!", "ru": "С Навруз! Пришла весна!"}, ()),
    (5, 9, "Bugun Xotira va qadrlash kuni. Bobo va buvilarimizni yod etamiz, ularga hurmat ko'rsatamiz.",
     {"en": "We remember and we respect.", "de": "Wir erinnern uns und danken.", "fr": "Nous nous souvenons.", "es": "Recordamos y respetamos.", "ru": "Мы помним и ценим."}, ()),
    (6, 1, "Bugun Xalqaro bolalar kuni! Bayramingiz bilan, bolajonlar!",
     {"en": "Happy Children's Day!", "de": "Alles Gute zum Kindertag!", "fr": "Bonne journée des enfants !", "es": "¡Feliz Día del Niño!", "ru": "С Днём защиты детей!"}, ()),
    (9, 1, "Bugun Mustaqillik kuni! Vatanimiz bayrami muborak.",
     {"en": "Happy Independence Day, Uzbekistan!", "de": "Alles Gute zum Unabhängigkeitstag!", "fr": "Bonne fête de l'Indépendance !", "es": "¡Feliz Día de la Independencia!", "ru": "С Днём независимости!"}, ()),
    (9, 2, "Bugun yangi o'quv yili boshlandi! Maktabga xush kelibsiz.",
     {"en": "Welcome back to school!", "de": "Willkommen zurück in der Schule!", "fr": "Bonne rentrée !", "es": "¡Bienvenidos a la escuela!", "ru": "С Днём знаний!"}, ()),
    (10, 1, "Bugun O'qituvchi va murabbiylar kuni. Ustozlaringizga rahmat ayting!",
     {"en": "Happy Teachers' Day! Thank you, teacher!", "de": "Danke, liebe Lehrerin!", "fr": "Merci, maîtresse !", "es": "¡Gracias, maestra!", "ru": "С Днём учителя!"}, ()),
    (10, 21, "Bugun O'zbek tili bayrami. Ona tilimizni sevamiz — boshqa tillarni ham shu sevgi bilan o'rganamiz.",
     {"en": "Every language is a treasure.", "de": "Jede Sprache ist ein Schatz.", "fr": "Chaque langue est un trésor.", "es": "Cada idioma es un tesoro.", "ru": "Каждый язык — сокровище."}, ()),
    (12, 8, "Bugun Konstitutsiya kuni. Konstitutsiya — hammamiz uchun asosiy qoidalar kitobi.",
     {"en": "Rules help us live together.", "de": "Regeln helfen uns zusammen.", "fr": "Les règles nous aident à vivre ensemble.", "es": "Las reglas nos ayudan a convivir.", "ru": "Правила помогают нам жить вместе."}, ()),
    (12, 25, "Bugun ko'p mamlakatlarda Rojdestvo nishonlanadi: archa bezatiladi, oilalar yig'iladi.",
     {"en": "Merry Christmas!", "de": "Frohe Weihnachten!", "fr": "Joyeux Noël !", "es": "¡Feliz Navidad!", "ru": "Счастливого Рождества!"}, ("en", "de", "fr", "es")),
    (7, 14, "Bugun Fransiyada milliy bayram: osmonda salyut, ko'chalarda musiqa.",
     {"fr": "Bonne fête nationale !"}, ("fr",)),
    (10, 3, "Bugun Germaniyada Birlik kuni — butun mamlakat bayrami.",
     {"de": "Schönen Tag der Deutschen Einheit!"}, ("de",)),
    (10, 12, "Bugun Ispaniyada milliy bayram — Ispan tili kuni ham deyiladi.",
     {"es": "¡Feliz Día de la Hispanidad!"}, ("es",)),
    (6, 6, "Bugun Rus tili kuni — buyuk shoir Pushkin tug'ilgan kun.",
     {"ru": "С Днём русского языка!"}, ("ru",)),
    (4, 23, "Bugun Ingliz tili kuni — yozuvchi Shekspir tug'ilgan kun.",
     {"en": "Happy English Language Day!"}, ("en",)),
]

# ── Kundalik hayot: hafta kuniga qarab mavzu va dars matnlaridan izlanadigan kalit so'zlar ──
HAYOT = [
    ("Ertalab nima qilamiz?", {"en": ["morning", "wake up", "breakfast", "brush"], "de": ["Morgen", "Frühstück", "aufstehen", "Zähne"],
                               "fr": ["matin", "petit-déjeuner", "réveille", "dents"], "es": ["mañana", "desayuno", "despierto", "dientes"],
                               "ru": ["утро", "завтрак", "встаю", "зубы"]}),
    ("Maktabda", {"en": ["school", "lesson", "teacher", "classroom"], "de": ["Schule", "Unterricht", "Lehrer", "Klasse"],
                  "fr": ["école", "classe", "maîtresse", "cours"], "es": ["escuela", "clase", "maestra", "profesor"],
                  "ru": ["школа", "урок", "учитель", "класс"]}),
    ("Ovqat va dasturxon", {"en": ["lunch", "dinner", "eat", "apple", "bread"], "de": ["Mittagessen", "essen", "Apfel", "Brot"],
                            "fr": ["déjeuner", "dîner", "mange", "pomme", "pain"], "es": ["almuerzo", "cena", "como", "manzana", "pan"],
                            "ru": ["обед", "ужин", "ем", "яблоко", "хлеб"]}),
    ("Sport va o'yin", {"en": ["play", "football", "run", "sport"], "de": ["spielen", "Fußball", "laufen", "Sport"],
                        "fr": ["joue", "football", "cours", "sport"], "es": ["juego", "fútbol", "correr", "deporte"],
                        "ru": ["играю", "футбол", "бегаю", "спорт"]}),
    ("Oila", {"en": ["mother", "father", "family", "sister", "brother"], "de": ["Mutter", "Vater", "Familie", "Schwester", "Bruder"],
              "fr": ["mère", "père", "famille", "sœur", "frère"], "es": ["madre", "padre", "familia", "hermana", "hermano"],
              "ru": ["мама", "папа", "семья", "сестра", "брат"]}),
    ("Kechqurun", {"en": ["evening", "homework", "read", "sleep"], "de": ["Abend", "Hausaufgaben", "lese", "schlafe"],
                   "fr": ["soir", "devoirs", "lis", "dors"], "es": ["noche", "deberes", "leo", "duermo"],
                   "ru": ["вечер", "домашнее", "читаю", "сплю"]}),
    ("Dam olish kuni", {"en": ["weekend", "park", "visit", "Sunday"], "de": ["Wochenende", "Park", "besuchen", "Sonntag"],
                        "fr": ["week-end", "parc", "visite", "dimanche"], "es": ["fin de semana", "parque", "visitar", "domingo"],
                        "ru": ["выходные", "парк", "в гости", "воскресенье"]}),
]

# ── Ob-havo ──
OB_HAVO_SHAHAR = {"nom": "Samarqand", "lat": 39.65, "lon": 66.96}
HAVO_SOZ = {
    "quyosh": {"uz": "quyoshli", "en": "sunny", "de": "sonnig", "fr": "ensoleillé", "es": "soleado", "ru": "солнечно"},
    "bulut": {"uz": "bulutli", "en": "cloudy", "de": "bewölkt", "fr": "nuageux", "es": "nublado", "ru": "облачно"},
    "yomgir": {"uz": "yomg'irli", "en": "rainy", "de": "regnerisch", "fr": "pluvieux", "es": "lluvioso", "ru": "дождливо"},
    "qor": {"uz": "qorli", "en": "snowy", "de": "verschneit", "fr": "neigeux", "es": "nevado", "ru": "снежно"},
    "tuman": {"uz": "tumanli", "en": "foggy", "de": "neblig", "fr": "brumeux", "es": "con niebla", "ru": "туманно"},
}
HAVO_GAP = {
    "en": ("Today in Samarkand it is {h}.", "It is {t} degrees."), "de": ("Heute ist es in Samarkand {h}.", "Es sind {t} Grad."),
    "fr": ("Aujourd'hui, à Samarcande, le temps est {h}.", "Il fait {t} degrés."), "es": ("Hoy en Samarcanda está {h}.", "Hace {t} grados."),
    "ru": ("Сегодня в Самарканде {h}.", "Сейчас {t} градусов."),
}
HAVO_EMOJI = {"quyosh": "☀️", "bulut": "☁️", "yomgir": "🌧️", "qor": "❄️", "tuman": "🌫️"}


def ob_havo(sana, timeout=6):
    """Open-Meteo (kalitsiz, bepul). Internet bo'lmasa — None (bo'lim tushib qoladi, ko'rsatuv baribir chiqadi)."""
    url = ("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max"
           "&timezone=Asia%2FTashkent&start_date={d}&end_date={d}").format(lat=OB_HAVO_SHAHAR["lat"], lon=OB_HAVO_SHAHAR["lon"], d=sana.isoformat())
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            d = json.loads(r.read().decode())
        kod = int(d["daily"]["weathercode"][0])
        t = round(float(d["daily"]["temperature_2m_max"][0]))
    except Exception:
        return None
    turi = ("quyosh" if kod <= 1 else "bulut" if kod <= 3 else "tuman" if kod in (45, 48)
            else "qor" if kod in (71, 73, 75, 77, 85, 86) else "yomgir")
    return {"turi": turi, "harorat": t, "emoji": HAVO_EMOJI[turi]}


def bugungi_bayram(sana, til):
    for oy, kun, uz, tabrik, faqat in BAYRAMLAR:
        if (oy, kun) == (sana.month, sana.day) and (not faqat or til in faqat) and til in tabrik:
            return {"uz": uz, "tabrik": tabrik[til]}
    return None


def ibora_tanla(til, daraja_harf, urug):
    """Shu darajadagi iboralardan bittasi; sana va auditoriyaga qarab aylanadi (har guruhda boshqa, takrorlanmaydi)."""
    royxat = [x for x in IBORALAR.get(til, []) if x[3] == daraja_harf] or IBORALAR.get(til, [])
    return royxat[urug % len(royxat)] if royxat else None

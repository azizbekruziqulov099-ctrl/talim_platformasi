"""REV187: Kabutar TV rukn (bo'lim) matnlari — ob-havo, taqvim, qiziqarli fakt, qo'shiq. 5 til + o'zbekcha.
Matnlar oldindan yozilgan (internetdan faqat ob-havo raqamlari olinadi) — bolalar uchun xavfsiz."""

HAFTA = {
    "uz": ["dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba", "yakshanba"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
    "ru": ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"],
}
OY = {
    "uz": ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
}
SANA = {  # bugungi sana gapi
    "uz": "Bugun {kun}-{oy}, {hafta}.", "en": "Today is {hafta}, the {kun} of {oy}.", "de": "Heute ist {hafta}, der {kun}. {oy}.",
    "fr": "Aujourd'hui, c'est {hafta} {kun} {oy}.", "es": "Hoy es {hafta}, {kun} de {oy}.", "ru": "Сегодня {hafta}, {kun} {oy}.",
}

# Ob-havo: holat kodi → (emoji, so'z har tilda)
HOLAT = {
    "quyosh": ("☀️", {"uz": "quyoshli", "en": "sunny", "de": "sonnig", "fr": "ensoleillé", "es": "soleado", "ru": "солнечно"}),
    "bulut": ("⛅", {"uz": "bulutli", "en": "cloudy", "de": "bewölkt", "fr": "nuageux", "es": "nublado", "ru": "облачно"}),
    "tuman": ("🌫️", {"uz": "tumanli", "en": "foggy", "de": "neblig", "fr": "brumeux", "es": "con niebla", "ru": "туманно"}),
    "yomgir": ("🌧️", {"uz": "yomg'irli", "en": "rainy", "de": "regnerisch", "fr": "pluvieux", "es": "lluvioso", "ru": "дождливо"}),
    "qor": ("❄️", {"uz": "qorli", "en": "snowy", "de": "verschneit", "fr": "neigeux", "es": "nevado", "ru": "снежно"}),
    "momaqaldiroq": ("⛈️", {"uz": "momaqaldiroqli", "en": "stormy", "de": "stürmisch", "fr": "orageux", "es": "tormentoso", "ru": "гроза"}),
}
OBHAVO = {   # {shahar} {holat} {max} {min} — kichik / katta
    "kichik": {
        "en": "Look at the sky! It is {holat} today.", "de": "Schau in den Himmel! Heute ist es {holat}.",
        "fr": "Regarde le ciel ! Aujourd'hui, il fait {holat}.", "es": "¡Mira el cielo! Hoy está {holat}.", "ru": "Посмотри на небо! Сегодня {holat}.",
        "uz": "Osmonga qarang! Bugun havo {holat}.",
    },
    "katta": {
        "en": "Weather in {shahar}: it is {holat}, up to {max} degrees, at night {min} degrees.",
        "de": "Das Wetter in {shahar}: es ist {holat}, bis zu {max} Grad, in der Nacht {min} Grad.",
        "fr": "La météo à {shahar} : il fait {holat}, jusqu'à {max} degrés, la nuit {min} degrés.",
        "es": "El tiempo en {shahar}: está {holat}, hasta {max} grados, por la noche {min} grados.",
        "ru": "Погода в городе {shahar}: {holat}, днём до {max} градусов, ночью {min}.",
        "uz": "{shahar}da ob-havo: {holat}, kunduzi {max} daraja, kechasi {min} daraja.",
    },
}
MASLAHAT = {   # holat → maslahat (katta yosh)
    "yomgir": {"en": "Take an umbrella!", "de": "Nimm einen Regenschirm mit!", "fr": "Prends un parapluie !", "es": "¡Lleva un paraguas!", "ru": "Возьми зонтик!", "uz": "Soyabon oling!"},
    "qor": {"en": "Put on a warm hat!", "de": "Zieh eine warme Mütze an!", "fr": "Mets un bonnet chaud !", "es": "¡Ponte un gorro caliente!", "ru": "Надень тёплую шапку!", "uz": "Issiq qalpoq kiying!"},
    "quyosh": {"en": "Drink water and play outside!", "de": "Trink Wasser und spiel draußen!", "fr": "Bois de l'eau et joue dehors !", "es": "¡Bebe agua y juega fuera!", "ru": "Пей воду и играй на улице!", "uz": "Suv iching va tashqarida o'ynang!"},
    "bulut": {"en": "Maybe take a jacket.", "de": "Nimm vielleicht eine Jacke mit.", "fr": "Prends peut-être une veste.", "es": "Quizás lleva una chaqueta.", "ru": "Возьми куртку.", "uz": "Kurtka olib oling."},
    "tuman": {"en": "Be careful on the road!", "de": "Sei vorsichtig auf der Straße!", "fr": "Fais attention sur la route !", "es": "¡Ten cuidado en la calle!", "ru": "Будь осторожен на дороге!", "uz": "Yo'lda ehtiyot bo'ling!"},
    "momaqaldiroq": {"en": "Stay at home today!", "de": "Bleib heute zu Hause!", "fr": "Reste à la maison aujourd'hui !", "es": "¡Quédate en casa hoy!", "ru": "Сегодня лучше остаться дома!", "uz": "Bugun uyda qoling!"},
}
SHAHAR = {"uz": "Samarqand", "en": "Samarkand", "de": "Samarkand", "fr": "Samarcande", "es": "Samarcanda", "ru": "Самарканд"}

# Taqvim: (oy, kun) → bayram nomi
BAYRAM = {
    (1, 1): {"uz": "Yangi yil", "en": "New Year's Day", "de": "Neujahr", "fr": "le Jour de l'An", "es": "Año Nuevo", "ru": "Новый год", "e": "🎆"},
    (1, 14): {"uz": "Vatan himoyachilari kuni", "en": "Defenders of the Motherland Day", "de": "Tag der Vaterlandsverteidiger", "fr": "la Journée des défenseurs de la patrie", "es": "el Día de los Defensores de la Patria", "ru": "День защитников Родины", "e": "🎖️"},
    (2, 21): {"uz": "Xalqaro ona tili kuni", "en": "International Mother Language Day", "de": "der Internationale Tag der Muttersprache", "fr": "la Journée internationale de la langue maternelle", "es": "el Día Internacional de la Lengua Materna", "ru": "Международный день родного языка", "e": "🗣️"},
    (3, 8): {"uz": "Xalqaro xotin-qizlar kuni", "en": "International Women's Day", "de": "der Internationale Frauentag", "fr": "la Journée internationale des femmes", "es": "el Día Internacional de la Mujer", "ru": "Международный женский день", "e": "💐"},
    (3, 21): {"uz": "Navro'z", "en": "Navruz, the spring holiday", "de": "Nouruz, das Frühlingsfest", "fr": "Navrouz, la fête du printemps", "es": "Navruz, la fiesta de la primavera", "ru": "Навруз — праздник весны", "e": "🌷"},
    (4, 22): {"uz": "Yer kuni", "en": "Earth Day", "de": "der Tag der Erde", "fr": "le Jour de la Terre", "es": "el Día de la Tierra", "ru": "День Земли", "e": "🌍"},
    (5, 9): {"uz": "Xotira va qadrlash kuni", "en": "the Day of Remembrance", "de": "der Tag der Erinnerung", "fr": "la Journée du souvenir", "es": "el Día del Recuerdo", "ru": "День памяти и почестей", "e": "🕊️"},
    (6, 1): {"uz": "Xalqaro bolalarni himoya qilish kuni", "en": "International Children's Day", "de": "der Internationale Kindertag", "fr": "la Journée internationale des enfants", "es": "el Día Internacional del Niño", "ru": "Международный день защиты детей", "e": "🎈"},
    (9, 1): {"uz": "Mustaqillik kuni", "en": "Independence Day of Uzbekistan", "de": "der Unabhängigkeitstag Usbekistans", "fr": "la fête de l'Indépendance de l'Ouzbékistan", "es": "el Día de la Independencia de Uzbekistán", "ru": "День независимости Узбекистана", "e": "🇺🇿"},
    (9, 2): {"uz": "Bilimlar kuni", "en": "the first school day", "de": "der erste Schultag", "fr": "la rentrée des classes", "es": "el primer día de clase", "ru": "День знаний", "e": "🎒"},
    (10, 1): {"uz": "O'qituvchi va murabbiylar kuni", "en": "Teachers' Day", "de": "der Tag der Lehrer", "fr": "la Journée des enseignants", "es": "el Día del Maestro", "ru": "День учителя", "e": "🍎"},
    (10, 21): {"uz": "O'zbek tili bayrami kuni", "en": "Uzbek Language Day", "de": "der Tag der usbekischen Sprache", "fr": "la Journée de la langue ouzbèke", "es": "el Día de la Lengua Uzbeka", "ru": "День узбекского языка", "e": "📖"},
    (12, 8): {"uz": "Konstitutsiya kuni", "en": "Constitution Day", "de": "der Tag der Verfassung", "fr": "la Journée de la Constitution", "es": "el Día de la Constitución", "ru": "День Конституции", "e": "📜"},
    (12, 31): {"uz": "Yangi yil arafasi", "en": "New Year's Eve", "de": "Silvester", "fr": "la Saint-Sylvestre", "es": "Nochevieja", "ru": "канун Нового года", "e": "🎄"},
}
BAYRAM_GAP = {"uz": "Bugun — {nom}! Tabriklaymiz!", "en": "Today is {nom}! Happy holiday!", "de": "Heute ist {nom}! Alles Gute!",
              "fr": "Aujourd'hui, c'est {nom} ! Bonne fête !", "es": "¡Hoy es {nom}! ¡Feliz día!", "ru": "Сегодня — {nom}! Поздравляем!"}
FASL = {  # oy → fasl (bayram bo'lmagan kunlar uchun)
    "qish": ({12, 1, 2}, "☃️", {"uz": "Hozir qish.", "en": "It is winter now.", "de": "Jetzt ist Winter.", "fr": "C'est l'hiver.", "es": "Ahora es invierno.", "ru": "Сейчас зима."}),
    "bahor": ({3, 4, 5}, "🌸", {"uz": "Hozir bahor.", "en": "It is spring now.", "de": "Jetzt ist Frühling.", "fr": "C'est le printemps.", "es": "Ahora es primavera.", "ru": "Сейчас весна."}),
    "yoz": ({6, 7, 8}, "🌞", {"uz": "Hozir yoz.", "en": "It is summer now.", "de": "Jetzt ist Sommer.", "fr": "C'est l'été.", "es": "Ahora es verano.", "ru": "Сейчас лето."}),
    "kuz": ({9, 10, 11}, "🍂", {"uz": "Hozir kuz.", "en": "It is autumn now.", "de": "Jetzt ist Herbst.", "fr": "C'est l'automne.", "es": "Ahora es otoño.", "ru": "Сейчас осень."}),
}

# Qiziqarli faktlar — kichik (2-7 yosh, 1-4 sinf) va katta (5-11 sinf). Har ko'rsatuvda takrorlanmas tartibda.
FAKT_KICHIK = [
    ("🐘", {"uz": "Fil — eng katta quruqlik hayvoni.", "en": "The elephant is the biggest land animal.", "de": "Der Elefant ist das größte Landtier.", "fr": "L'éléphant est le plus grand animal terrestre.", "es": "El elefante es el animal terrestre más grande.", "ru": "Слон — самое большое сухопутное животное."}),
    ("🐝", {"uz": "Asalarilar asal qiladi.", "en": "Bees make honey.", "de": "Bienen machen Honig.", "fr": "Les abeilles font du miel.", "es": "Las abejas hacen miel.", "ru": "Пчёлы делают мёд."}),
    ("🦒", {"uz": "Jirafaning bo'yni juda uzun.", "en": "A giraffe has a very long neck.", "de": "Die Giraffe hat einen sehr langen Hals.", "fr": "La girafe a un très long cou.", "es": "La jirafa tiene un cuello muy largo.", "ru": "У жирафа очень длинная шея."}),
    ("🐙", {"uz": "Sakkizoyoqning sakkizta oyog'i bor.", "en": "An octopus has eight arms.", "de": "Ein Oktopus hat acht Arme.", "fr": "La pieuvre a huit bras.", "es": "El pulpo tiene ocho brazos.", "ru": "У осьминога восемь щупалец."}),
    ("🌈", {"uz": "Kamalakda yettita rang bor.", "en": "A rainbow has seven colours.", "de": "Ein Regenbogen hat sieben Farben.", "fr": "L'arc-en-ciel a sept couleurs.", "es": "El arcoíris tiene siete colores.", "ru": "В радуге семь цветов."}),
    ("🐧", {"uz": "Pingvinlar ucha olmaydi, lekin yaxshi suzadi.", "en": "Penguins cannot fly, but they swim very well.", "de": "Pinguine können nicht fliegen, aber sie schwimmen sehr gut.", "fr": "Les pingouins ne volent pas, mais ils nagent très bien.", "es": "Los pingüinos no vuelan, pero nadan muy bien.", "ru": "Пингвины не летают, но отлично плавают."}),
    ("🌙", {"uz": "Oy kechasi osmonda ko'rinadi.", "en": "We can see the Moon at night.", "de": "Nachts sehen wir den Mond.", "fr": "La nuit, on voit la Lune.", "es": "Por la noche vemos la Luna.", "ru": "Ночью мы видим Луну."}),
    ("🐢", {"uz": "Toshbaqa juda sekin yuradi.", "en": "A turtle walks very slowly.", "de": "Eine Schildkröte geht sehr langsam.", "fr": "La tortue marche très lentement.", "es": "La tortuga camina muy despacio.", "ru": "Черепаха ходит очень медленно."}),
    ("🦋", {"uz": "Kapalak avval qurt bo'ladi.", "en": "A butterfly was a caterpillar first.", "de": "Ein Schmetterling war zuerst eine Raupe.", "fr": "Le papillon était d'abord une chenille.", "es": "La mariposa primero fue una oruga.", "ru": "Бабочка сначала была гусеницей."}),
    ("🐳", {"uz": "Kit — eng katta hayvon.", "en": "The blue whale is the biggest animal.", "de": "Der Blauwal ist das größte Tier.", "fr": "La baleine bleue est le plus grand animal.", "es": "La ballena azul es el animal más grande.", "ru": "Синий кит — самое большое животное."}),
    ("🍎", {"uz": "Olma shirin va foydali.", "en": "Apples are sweet and healthy.", "de": "Äpfel sind süß und gesund.", "fr": "Les pommes sont sucrées et bonnes pour la santé.", "es": "Las manzanas son dulces y sanas.", "ru": "Яблоки сладкие и полезные."}),
    ("🦉", {"uz": "Boyqush kechasi uyg'oq bo'ladi.", "en": "Owls are awake at night.", "de": "Eulen sind nachts wach.", "fr": "Les hiboux sont éveillés la nuit.", "es": "Los búhos están despiertos de noche.", "ru": "Совы не спят ночью."}),
    ("🐪", {"uz": "Tuya ko'p kun suv ichmasdan yura oladi.", "en": "A camel can walk for days without water.", "de": "Ein Kamel kann tagelang ohne Wasser laufen.", "fr": "Le chameau peut marcher des jours sans eau.", "es": "El camello puede caminar días sin agua.", "ru": "Верблюд может идти много дней без воды."}),
    ("☀️", {"uz": "Quyosh — bu katta yulduz.", "en": "The Sun is a big star.", "de": "Die Sonne ist ein großer Stern.", "fr": "Le Soleil est une grande étoile.", "es": "El Sol es una estrella grande.", "ru": "Солнце — большая звезда."}),
    ("🐸", {"uz": "Qurbaqa uzoqqa sakraydi.", "en": "A frog can jump very far.", "de": "Ein Frosch kann sehr weit springen.", "fr": "La grenouille saute très loin.", "es": "La rana salta muy lejos.", "ru": "Лягушка прыгает очень далеко."}),
    ("🌻", {"uz": "Kungaboqar quyoshga qarab o'giriladi.", "en": "A sunflower turns to the Sun.", "de": "Die Sonnenblume dreht sich zur Sonne.", "fr": "Le tournesol se tourne vers le Soleil.", "es": "El girasol gira hacia el Sol.", "ru": "Подсолнух поворачивается к Солнцу."}),
    ("🐬", {"uz": "Delfinlar bir-biri bilan gaplashadi.", "en": "Dolphins talk to each other.", "de": "Delfine sprechen miteinander.", "fr": "Les dauphins se parlent.", "es": "Los delfines hablan entre ellos.", "ru": "Дельфины разговаривают друг с другом."}),
    ("🦷", {"uz": "Tishlarni kuniga ikki marta yuvamiz.", "en": "We brush our teeth two times a day.", "de": "Wir putzen zweimal am Tag die Zähne.", "fr": "On se brosse les dents deux fois par jour.", "es": "Nos lavamos los dientes dos veces al día.", "ru": "Мы чистим зубы два раза в день."}),
    ("🐿️", {"uz": "Olmaxon qish uchun yong'oq yig'adi.", "en": "A squirrel saves nuts for winter.", "de": "Ein Eichhörnchen sammelt Nüsse für den Winter.", "fr": "L'écureuil garde des noix pour l'hiver.", "es": "La ardilla guarda nueces para el invierno.", "ru": "Белка запасает орехи на зиму."}),
    ("💧", {"uz": "Suv muzlasa — muzga aylanadi.", "en": "When water freezes, it becomes ice.", "de": "Wenn Wasser friert, wird es zu Eis.", "fr": "Quand l'eau gèle, elle devient de la glace.", "es": "Cuando el agua se congela, se vuelve hielo.", "ru": "Когда вода замерзает, она становится льдом."}),
    ("🐄", {"uz": "Sigir bizga sut beradi.", "en": "A cow gives us milk.", "de": "Die Kuh gibt uns Milch.", "fr": "La vache nous donne du lait.", "es": "La vaca nos da leche.", "ru": "Корова даёт нам молоко."}),
    ("🦁", {"uz": "Sherni hayvonlar shohi deyishadi.", "en": "People call the lion the king of animals.", "de": "Der Löwe heißt König der Tiere.", "fr": "On appelle le lion le roi des animaux.", "es": "Al león lo llaman el rey de los animales.", "ru": "Льва называют царём зверей."}),
    ("🌳", {"uz": "Daraxtlar bizga toza havo beradi.", "en": "Trees give us clean air.", "de": "Bäume geben uns saubere Luft.", "fr": "Les arbres nous donnent de l'air pur.", "es": "Los árboles nos dan aire limpio.", "ru": "Деревья дают нам чистый воздух."}),
    ("🐌", {"uz": "Shilliqqurt uyini orqasida olib yuradi.", "en": "A snail carries its house on its back.", "de": "Die Schnecke trägt ihr Haus auf dem Rücken.", "fr": "L'escargot porte sa maison sur le dos.", "es": "El caracol lleva su casa en la espalda.", "ru": "Улитка носит домик на спине."}),
    ("⭐", {"uz": "Osmonda juda ko'p yulduz bor.", "en": "There are many, many stars in the sky.", "de": "Am Himmel gibt es sehr viele Sterne.", "fr": "Il y a beaucoup d'étoiles dans le ciel.", "es": "Hay muchísimas estrellas en el cielo.", "ru": "На небе очень много звёзд."}),
    ("🐓", {"uz": "Xo'roz ertalab qichqiradi.", "en": "The rooster sings in the morning.", "de": "Der Hahn kräht am Morgen.", "fr": "Le coq chante le matin.", "es": "El gallo canta por la mañana.", "ru": "Петух поёт утром."}),
    ("🥕", {"uz": "Sabzi ko'zlarga foydali.", "en": "Carrots are good for your eyes.", "de": "Karotten sind gut für die Augen.", "fr": "Les carottes sont bonnes pour les yeux.", "es": "Las zanahorias son buenas para los ojos.", "ru": "Морковь полезна для глаз."}),
    ("🦜", {"uz": "To'tiqush gapni takrorlay oladi.", "en": "A parrot can repeat words.", "de": "Ein Papagei kann Wörter nachsprechen.", "fr": "Un perroquet peut répéter des mots.", "es": "Un loro puede repetir palabras.", "ru": "Попугай умеет повторять слова."}),
    ("🍉", {"uz": "Tarvuzning ko'p qismi — suv.", "en": "A watermelon is mostly water.", "de": "Eine Wassermelone besteht fast nur aus Wasser.", "fr": "La pastèque, c'est surtout de l'eau.", "es": "La sandía es casi toda agua.", "ru": "Арбуз почти весь из воды."}),
    ("🐻", {"uz": "Ayiq qishda uxlaydi.", "en": "Bears sleep in winter.", "de": "Bären schlafen im Winter.", "fr": "Les ours dorment en hiver.", "es": "Los osos duermen en invierno.", "ru": "Медведи спят зимой."}),
]
FAKT_KATTA = [
    ("🪐", {"uz": "Saturn shunchalik yengilki, katta okeanda suzib yurgan bo'lardi.", "en": "Saturn is so light that it could float in a giant ocean.", "de": "Saturn ist so leicht, dass er in einem riesigen Ozean schwimmen könnte.", "fr": "Saturne est si légère qu'elle pourrait flotter dans un océan géant.", "es": "Saturno es tan ligero que podría flotar en un océano gigante.", "ru": "Сатурн такой лёгкий, что мог бы плавать в гигантском океане."}),
    ("🧠", {"uz": "Inson miyasi tanadagi energiyaning taxminan beshdan birini sarflaydi.", "en": "The human brain uses about one fifth of the body's energy.", "de": "Das menschliche Gehirn verbraucht etwa ein Fünftel der Energie des Körpers.", "fr": "Le cerveau humain utilise environ un cinquième de l'énergie du corps.", "es": "El cerebro humano usa casi una quinta parte de la energía del cuerpo.", "ru": "Мозг человека тратит около пятой части энергии тела."}),
    ("🏔️", {"uz": "Everest — dunyodagi eng baland tog', balandligi 8849 metr.", "en": "Everest is the highest mountain in the world: 8,849 metres.", "de": "Der Everest ist der höchste Berg der Welt: 8849 Meter.", "fr": "L'Everest est la plus haute montagne du monde : 8 849 mètres.", "es": "El Everest es la montaña más alta del mundo: 8849 metros.", "ru": "Эверест — самая высокая гора в мире: 8849 метров."}),
    ("🔭", {"uz": "Mirzo Ulug'bek Samarqandda 1018 ta yulduzni o'lchagan.", "en": "Ulugh Beg measured more than a thousand stars in Samarkand.", "de": "Ulugh Beg hat in Samarkand über tausend Sterne vermessen.", "fr": "Ulugh Beg a mesuré plus de mille étoiles à Samarcande.", "es": "Ulugh Beg midió más de mil estrellas en Samarcanda.", "ru": "Улугбек измерил в Самарканде больше тысячи звёзд."}),
    ("🧮", {"uz": "«Algoritm» so'zi Al-Xorazmiy nomidan kelib chiqqan.", "en": "The word 'algorithm' comes from the name of al-Khwarizmi.", "de": "Das Wort Algorithmus kommt vom Namen al-Chwarizmi.", "fr": "Le mot « algorithme » vient du nom d'al-Khwarizmi.", "es": "La palabra «algoritmo» viene del nombre de al-Juarismi.", "ru": "Слово «алгоритм» происходит от имени аль-Хорезми."}),
    ("💡", {"uz": "Yorug'lik Quyoshdan Yergacha taxminan 8 daqiqada yetib keladi.", "en": "Light from the Sun reaches the Earth in about eight minutes.", "de": "Das Licht der Sonne braucht etwa acht Minuten bis zur Erde.", "fr": "La lumière du Soleil arrive sur Terre en huit minutes environ.", "es": "La luz del Sol llega a la Tierra en unos ocho minutos.", "ru": "Свет от Солнца доходит до Земли примерно за восемь минут."}),
    ("🐙", {"uz": "Sakkizoyoqning uchta yuragi bor.", "en": "An octopus has three hearts.", "de": "Ein Oktopus hat drei Herzen.", "fr": "La pieuvre a trois cœurs.", "es": "El pulpo tiene tres corazones.", "ru": "У осьминога три сердца."}),
    ("🌊", {"uz": "Yer yuzasining taxminan 71 foizi suv bilan qoplangan.", "en": "About 71 percent of the Earth's surface is water.", "de": "Etwa 71 Prozent der Erdoberfläche sind Wasser.", "fr": "Environ 71 % de la surface de la Terre est de l'eau.", "es": "Cerca del 71 por ciento de la superficie de la Tierra es agua.", "ru": "Около 71 процента поверхности Земли покрыто водой."}),
    ("🦴", {"uz": "Katta odamda 206 ta suyak bor.", "en": "An adult has 206 bones.", "de": "Ein Erwachsener hat 206 Knochen.", "fr": "Un adulte a 206 os.", "es": "Un adulto tiene 206 huesos.", "ru": "У взрослого человека 206 костей."}),
    ("📚", {"uz": "Ibn Sinoning «Tib qonunlari» kitobi 600 yil davomida darslik bo'lgan.", "en": "Avicenna's Canon of Medicine was used as a textbook for about 600 years.", "de": "Avicennas Kanon der Medizin war etwa 600 Jahre lang ein Lehrbuch.", "fr": "Le Canon de la médecine d'Avicenne a servi de manuel pendant environ 600 ans.", "es": "El Canon de medicina de Avicena fue libro de texto durante unos 600 años.", "ru": "«Канон врачебной науки» Ибн Сины был учебником около 600 лет."}),
    ("🐝", {"uz": "Asalari bir qoshiq asal uchun minglab gulga qo'nadi.", "en": "Bees visit thousands of flowers to make one spoon of honey.", "de": "Bienen besuchen tausende Blüten für einen Löffel Honig.", "fr": "Les abeilles visitent des milliers de fleurs pour une cuillère de miel.", "es": "Las abejas visitan miles de flores para hacer una cuchara de miel.", "ru": "Пчёлы облетают тысячи цветов ради одной ложки мёда."}),
    ("⚡", {"uz": "Chaqmoq Quyosh yuzasidan ham issiqroq bo'ladi.", "en": "Lightning is hotter than the surface of the Sun.", "de": "Ein Blitz ist heißer als die Oberfläche der Sonne.", "fr": "La foudre est plus chaude que la surface du Soleil.", "es": "Un rayo es más caliente que la superficie del Sol.", "ru": "Молния горячее поверхности Солнца."}),
    ("🌍", {"uz": "Yer Quyosh atrofini 365 kunda bir marta aylanadi.", "en": "The Earth goes around the Sun once in 365 days.", "de": "Die Erde umkreist die Sonne einmal in 365 Tagen.", "fr": "La Terre fait le tour du Soleil en 365 jours.", "es": "La Tierra da la vuelta al Sol en 365 días.", "ru": "Земля обходит Солнце за 365 дней."}),
    ("🐘", {"uz": "Fillar bir-birini ovozi orqali kilometrlab uzoqdan taniydi.", "en": "Elephants can recognise each other's voices from kilometres away.", "de": "Elefanten erkennen ihre Stimmen über Kilometer hinweg.", "fr": "Les éléphants reconnaissent leurs voix à des kilomètres.", "es": "Los elefantes reconocen sus voces a kilómetros de distancia.", "ru": "Слоны узнают голоса друг друга за километры."}),
    ("🧊", {"uz": "Antarktida — Yerdagi eng sovuq va eng shamolli joy.", "en": "Antarctica is the coldest and windiest place on Earth.", "de": "Die Antarktis ist der kälteste und windigste Ort der Erde.", "fr": "L'Antarctique est l'endroit le plus froid et le plus venteux de la Terre.", "es": "La Antártida es el lugar más frío y ventoso de la Tierra.", "ru": "Антарктида — самое холодное и ветреное место на Земле."}),
    ("🛰️", {"uz": "Xalqaro kosmik stansiya Yerni 90 daqiqada bir marta aylanib chiqadi.", "en": "The International Space Station circles the Earth every 90 minutes.", "de": "Die Internationale Raumstation umkreist die Erde alle 90 Minuten.", "fr": "La Station spatiale internationale fait le tour de la Terre en 90 minutes.", "es": "La Estación Espacial Internacional da la vuelta a la Tierra cada 90 minutos.", "ru": "Международная космическая станция облетает Землю за 90 минут."}),
    ("🗣️", {"uz": "Dunyoda 7000 dan ortiq til bor.", "en": "There are more than 7,000 languages in the world.", "de": "Auf der Welt gibt es mehr als 7000 Sprachen.", "fr": "Il existe plus de 7 000 langues dans le monde.", "es": "En el mundo hay más de 7000 idiomas.", "ru": "В мире больше 7000 языков."}),
    ("🧬", {"uz": "Har bir hujayramizda DNK bor — bu tananing «ko'rsatma kitobi».", "en": "Every cell has DNA — the body's instruction book.", "de": "Jede Zelle hat DNA — das Bauanleitungsbuch des Körpers.", "fr": "Chaque cellule contient de l'ADN, le mode d'emploi du corps.", "es": "Cada célula tiene ADN, el libro de instrucciones del cuerpo.", "ru": "В каждой клетке есть ДНК — инструкция для организма."}),
    ("🏛️", {"uz": "Samarqand 2700 yildan ortiq tarixga ega.", "en": "Samarkand is more than 2,700 years old.", "de": "Samarkand ist mehr als 2700 Jahre alt.", "fr": "Samarcande a plus de 2 700 ans.", "es": "Samarcanda tiene más de 2700 años.", "ru": "Самарканду больше 2700 лет."}),
    ("🐟", {"uz": "Ba'zi baliqlar okean tubida o'zi nur sochadi.", "en": "Some deep-sea fish make their own light.", "de": "Manche Tiefseefische erzeugen ihr eigenes Licht.", "fr": "Certains poissons des profondeurs produisent leur propre lumière.", "es": "Algunos peces de las profundidades producen su propia luz.", "ru": "Некоторые глубоководные рыбы сами светятся."}),
    ("🌵", {"uz": "Kaktus suvni tanasida yig'ib saqlaydi.", "en": "A cactus stores water inside its stem.", "de": "Ein Kaktus speichert Wasser in seinem Stamm.", "fr": "Le cactus garde l'eau dans sa tige.", "es": "El cactus guarda agua en su tallo.", "ru": "Кактус запасает воду в стебле."}),
    ("🎵", {"uz": "Musiqa tinglash xotirani kuchaytirishi mumkin.", "en": "Listening to music can help your memory.", "de": "Musikhören kann dem Gedächtnis helfen.", "fr": "Écouter de la musique peut aider la mémoire.", "es": "Escuchar música puede ayudar a la memoria.", "ru": "Музыка может помогать памяти."}),
    ("🚀", {"uz": "Oyda shamol yo'q, shuning uchun astronavtlarning izi yo'qolmaydi.", "en": "There is no wind on the Moon, so astronauts' footprints stay there.", "de": "Auf dem Mond gibt es keinen Wind, darum bleiben die Fußspuren der Astronauten.", "fr": "Il n'y a pas de vent sur la Lune, donc les traces des astronautes restent.", "es": "En la Luna no hay viento, por eso las huellas de los astronautas siguen allí.", "ru": "На Луне нет ветра, поэтому следы астронавтов остаются."}),
    ("🦅", {"uz": "Burgut odamdan bir necha barobar uzoqni ko'radi.", "en": "An eagle can see several times farther than a person.", "de": "Ein Adler sieht mehrmals weiter als ein Mensch.", "fr": "Un aigle voit plusieurs fois plus loin qu'un humain.", "es": "Un águila ve varias veces más lejos que una persona.", "ru": "Орёл видит в несколько раз дальше человека."}),
    ("🕰️", {"uz": "Bir kunda 86400 soniya bor.", "en": "There are 86,400 seconds in one day.", "de": "Ein Tag hat 86 400 Sekunden.", "fr": "Une journée compte 86 400 secondes.", "es": "Un día tiene 86 400 segundos.", "ru": "В сутках 86 400 секунд."}),
    ("🌋", {"uz": "Yer ostida eritilgan tosh — magma bor.", "en": "Under the ground there is melted rock called magma.", "de": "Unter der Erde gibt es geschmolzenes Gestein: Magma.", "fr": "Sous la terre, il y a de la roche fondue : le magma.", "es": "Bajo la tierra hay roca fundida: el magma.", "ru": "Под землёй есть расплавленная порода — магма."}),
    ("📱", {"uz": "Birinchi mobil telefon 1973-yilda qo'ng'iroq qilgan.", "en": "The first mobile phone call was made in 1973.", "de": "Der erste Handyanruf war im Jahr 1973.", "fr": "Le premier appel avec un téléphone portable date de 1973.", "es": "La primera llamada con un móvil fue en 1973.", "ru": "Первый звонок по мобильному телефону сделали в 1973 году."}),
    ("🦈", {"uz": "Akulalar dinozavrlardan ham oldin paydo bo'lgan.", "en": "Sharks appeared even before the dinosaurs.", "de": "Haie gab es schon vor den Dinosauriern.", "fr": "Les requins sont apparus avant les dinosaures.", "es": "Los tiburones aparecieron antes que los dinosaurios.", "ru": "Акулы появились ещё до динозавров."}),
    ("🍯", {"uz": "Asal hech qachon buzilmaydi — ming yillik asal ham yeyishga yaroqli.", "en": "Honey never goes bad — even very old honey can be eaten.", "de": "Honig wird nie schlecht — selbst sehr alter Honig ist essbar.", "fr": "Le miel ne se gâte jamais, même très vieux.", "es": "La miel nunca se estropea, ni siquiera la muy antigua.", "ru": "Мёд не портится — даже очень старый мёд можно есть."}),
    ("🧲", {"uz": "Yer — ulkan magnit, shuning uchun kompas shimolni ko'rsatadi.", "en": "The Earth is a giant magnet, so a compass points north.", "de": "Die Erde ist ein riesiger Magnet, darum zeigt der Kompass nach Norden.", "fr": "La Terre est un aimant géant, donc la boussole indique le nord.", "es": "La Tierra es un imán gigante, por eso la brújula señala el norte.", "ru": "Земля — огромный магнит, поэтому компас показывает на север."}),
]
FAKT_BOSH = {"uz": "Qiziqarli fakt!", "en": "Fun fact!", "de": "Wusstest du das?", "fr": "Le savais-tu ?", "es": "¿Sabías que…?", "ru": "Интересный факт!"}
OBHAVO_BOSH = {"uz": "Ob-havo", "en": "Weather report", "de": "Der Wetterbericht", "fr": "La météo", "es": "El tiempo", "ru": "Прогноз погоды"}
TAQVIM_BOSH = {"uz": "Kun taqvimi", "en": "Today's calendar", "de": "Der Kalender", "fr": "Le calendrier", "es": "El calendario", "ru": "Календарь дня"}
QOSHIQ_BOSH = {"uz": "Qo'shiq vaqti!", "en": "Song time!", "de": "Wir singen!", "fr": "On chante !", "es": "¡A cantar!", "ru": "Поём вместе!"}
SAVOL = {  # katta yosh — fikr savoli (fikr bildirish vaqti)
    "en": "What do you think? Say your answer out loud!", "de": "Was meinst du? Sag deine Antwort laut!", "fr": "Qu'en penses-tu ? Dis ta réponse à voix haute !",
    "es": "¿Qué piensas? ¡Di tu respuesta en voz alta!", "ru": "А как думаешь ты? Скажи ответ вслух!", "uz": "Siz nima deb o'ylaysiz? Javobni ovoz chiqarib ayting!",
}
QOSHIQ = {  # {a} {b} — bugungi so'zlar
    "en": "{a}, {a}, clap, clap, clap! {b}, {b}, tap, tap, tap!", "de": "{a}, {a}, klatsch, klatsch, klatsch! {b}, {b}, tipp, tipp, tipp!",
    "fr": "{a}, {a}, tape, tape, tape ! {b}, {b}, saute, saute, saute !", "es": "¡{a}, {a}, palmas, palmas! ¡{b}, {b}, salta, salta!",
    "ru": "{a}, {a}, хлоп, хлоп, хлоп! {b}, {b}, топ, топ, топ!",
}


# ───────── REV194: «Kabu sayohatda» — o'rganilayotgan til mamlakati an'analari va tarixi + bizning meros ─────────
# (emoji, kichiklarga gap, kattalarga gap, o'zbekcha izoh, «bizda-chi?» taqqoslash)
SAYOHAT = {
    "en": [
        ("🫖", "In Britain, people love tea.", "In Britain, people drink tea every day, often with milk at five o'clock.",
         "Britaniyada choyni juda yaxshi ko'rishadi, ko'pincha sut bilan ichishadi.", "Bizda ham choy — mehmonning birinchi hurmati!"),
        ("🕰️", "This is Big Ben in London.", "Big Ben is the famous bell in the clock tower in London; it is more than 160 years old.",
         "Big Ben — Londondagi mashhur soat minorasining qo'ng'irog'i.", "Bizda esa Registon — Samarqandning yuragi!"),
        ("🎃", "In autumn, children make pumpkin lanterns.", "In October, many families carve pumpkins and make lanterns.",
         "Kuzda bolalar qovoqdan chiroq yasashadi.", "Bizda kuzda qovoqdan somsa pishiriladi!"),
        ("🏈", "In America, people love football and baseball.", "In the USA, American football and baseball are very popular sports.",
         "Amerikada amerikacha futbol va beysbol juda mashhur.", "Bizda esa kurash va futbol!"),
        ("🦃", "In America, families eat turkey in November.", "On Thanksgiving Day in November, American families say thank you and share a big dinner.",
         "Amerikada noyabrda oilalar yig'ilib, bir-biriga rahmat aytishadi.", "Bizda ham dasturxon atrofida oila yig'ilishi — eng katta baxt!"),
    ],
    "de": [
        ("🥨", "In Deutschland isst man gern Brezeln.", "Die Brezel ist ein typisches deutsches Gebäck mit einer besonderen Form.",
         "Germaniyada brezel degan o'ziga xos non bor.", "Bizda esa tandir non — dunyodagi eng mazali non!"),
        ("🏰", "In Deutschland gibt es viele Burgen.", "In Deutschland gibt es über zwanzigtausend Burgen und Schlösser.",
         "Germaniyada qadimiy qasrlar juda ko'p.", "Bizda ham qadimiy qal'alar bor — Xiva Ichan qal'asi!"),
        ("🎄", "Im Dezember gibt es Weihnachtsmärkte.", "Im Winter besuchen Familien die Weihnachtsmärkte mit Lichtern und Lebkuchen.",
         "Qishda Germaniyada chiroqli bayram bozorlari bo'ladi.", "Bizda Navro'zda sayllar bo'ladi!"),
        ("🚲", "Viele Kinder fahren mit dem Fahrrad zur Schule.", "In vielen deutschen Städten fahren Kinder mit dem Fahrrad zur Schule.",
         "Germaniyada ko'p bolalar maktabga velosipedda borishadi.", "Velosiped — sog'liq uchun ham foydali!"),
        ("🎵", "Beethoven war ein großer deutscher Komponist.", "Beethoven komponierte wunderbare Musik, obwohl er später nicht mehr hören konnte.",
         "Betxoven — buyuk nemis bastakori, eshitmay qolsa ham musiqa yozgan.", "Bizda ham buyuk musiqa bor — Shashmaqom!"),
    ],
    "fr": [
        ("🥐", "En France, on mange des croissants.", "Le matin, beaucoup de Français mangent un croissant au petit-déjeuner.",
         "Fransiyada ertalab kruassan yeyishadi.", "Bizda nonushtaga non, qaymoq va choy!"),
        ("🗼", "Voici la tour Eiffel à Paris.", "La tour Eiffel a été construite en 1889 et mesure plus de trois cents mètres.",
         "Eyfel minorasi Parijda, 1889-yilda qurilgan.", "Bizda esa Kalon minorasi — Buxoroda, 900 yoshdan oshgan!"),
        ("🧀", "En France, il y a beaucoup de fromages.", "La France produit plus de mille sortes de fromages.",
         "Fransiyada pishloqning mingdan ortiq turi bor.", "Bizda esa qurt — mazali va foydali!"),
        ("🎨", "Le Louvre est un grand musée.", "Le Louvre à Paris est le musée le plus visité du monde.",
         "Luvr — Parijdagi dunyoning eng mashhur muzeyi.", "Bizda Samarqand va Toshkentda ajoyib muzeylar bor!"),
        ("🚴", "Le Tour de France est une course de vélo.", "Chaque été, des cyclistes traversent la France pendant trois semaines.",
         "Har yozda Fransiyada mashhur velopoyga bo'ladi.", "Sport — sog'lom tana va kuchli iroda!"),
    ],
    "es": [
        ("💃", "En España, la gente baila flamenco.", "El flamenco es un baile español con música de guitarra y palmas.",
         "Ispaniyada flamenko degan raqs bor.", "Bizda esa Lazgi va Andijon polkasi!"),
        ("🥘", "La paella es un plato español.", "La paella es un plato de arroz típico de Valencia.",
         "Paelya — Ispaniyaning guruchli taomi.", "Bizda esa palov — guruchli taomlarning podshosi!"),
        ("🍇", "En Año Nuevo, comen doce uvas.", "En Nochevieja, los españoles comen doce uvas, una con cada campanada.",
         "Ispaniyada Yangi yilda 12 ta uzum yeyishadi.", "Bizda Yangi yilda oila bilan dasturxon!"),
        ("⚽", "En España, el fútbol es muy popular.", "En España hay equipos de fútbol muy famosos en todo el mundo.",
         "Ispaniyada futbol juda mashhur.", "Bizda ham futbolni yaxshi ko'rishadi!"),
        ("🏛️", "La Alhambra es un palacio antiguo.", "La Alhambra de Granada es un palacio con jardines y azulejos preciosos.",
         "Alhambra — Ispaniyadagi chiroyli qadimiy saroy.", "Bizda ham koshinli saroylar bor — Shahrisabz Oqsaroy!"),
    ],
    "ru": [
        ("🪆", "Это матрёшка.", "Матрёшка — деревянная кукла, внутри которой есть другие куклы.",
         "Matryoshka — ichida boshqa qo'g'irchoqlar bor yog'och qo'g'irchoq.", "Bizda esa chiroyli sopol o'yinchoqlar — Rishton!"),
        ("🥞", "Весной пекут блины.", "На праздник Масленица в России пекут блины и провожают зиму.",
         "Rossiyada bahorda quymoq pishirib, qishni kuzatishadi.", "Bizda bahorda sumalak pishiriladi!"),
        ("🚂", "Это самая длинная железная дорога.", "Транссибирская магистраль — самая длинная железная дорога в мире.",
         "Rossiyada dunyodagi eng uzun temir yo'l bor.", "Bizda «Afrosiyob» poyezdi juda tez yuradi!"),
        ("📚", "Пушкин — великий поэт.", "Александр Пушкин — великий русский поэт, его сказки знают все дети.",
         "Pushkin — buyuk rus shoiri, ertaklarini hamma biladi.", "Bizda esa Alisher Navoiy — buyuk shoirimiz!"),
        ("❄️", "Зимой в России много снега.", "Зимой в России бывает очень холодно и много снега.",
         "Rossiyada qishda qor juda ko'p.", "Bizda qish yumshoqroq, lekin qorbo'ron o'ynash zo'r!"),
    ],
}
SAYOHAT_BOSH = {"en": "Kabu is travelling! Where are we today?", "de": "Kabu reist! Wo sind wir heute?", "fr": "Kabu voyage ! Où sommes-nous aujourd'hui ?",
                "es": "¡Kabu viaja! ¿Dónde estamos hoy?", "ru": "Кабу путешествует! Где мы сегодня?"}


# ───────── REV195: «Mashhur inson» — shu tilda gapiradigan mashhur odamlar (kichiklarga sodda, kattalarga batafsil) ─────────
MASHHUR = {
    "en": [("🎭", "William Shakespeare", "Shakespeare wrote plays and poems.", "Shakespeare wrote 39 plays; people still watch Romeo and Juliet today.",
            "Shekspir — buyuk ingliz yozuvchisi, «Romeo va Julyetta»ni yozgan."),
           ("🍎", "Isaac Newton", "Newton watched an apple fall.", "Isaac Newton explained gravity: why things fall down to the Earth.",
            "Nyuton — olma tushganini ko'rib, tortishish kuchini kashf qilgan olim."),
           ("🧚", "Beatrix Potter", "She wrote stories about a little rabbit.", "Beatrix Potter wrote and drew the stories of Peter Rabbit.",
            "Beatris Potter — quyoncha Piter haqida ertaklar yozgan va chizgan."),
           ("✈️", "The Wright brothers", "Two brothers made the first plane.", "In 1903, the Wright brothers flew the first airplane in America.",
            "Rayt aka-ukalar 1903-yilda birinchi samolyotni uchirishgan.")],
    "de": [("🎹", "Ludwig van Beethoven", "Beethoven spielte Klavier.", "Beethoven schrieb neun Sinfonien, auch als er nicht mehr hören konnte.",
            "Betxoven — buyuk bastakor, eshitmay qolsa ham musiqa yozgan."),
           ("💡", "Albert Einstein", "Einstein war ein großer Wissenschaftler.", "Albert Einstein erklärte, wie Zeit und Licht zusammenhängen.",
            "Eynshteyn — vaqt va yorug'lik sirlarini ochgan olim."),
           ("📖", "Die Brüder Grimm", "Die Brüder Grimm schrieben Märchen.", "Die Brüder Grimm sammelten Märchen wie Rotkäppchen und Schneewittchen.",
            "Aka-uka Grimmlar «Qizil qalpoqcha» kabi ertaklarni to'plashgan."),
           ("🚗", "Carl Benz", "Carl Benz baute das erste Auto.", "1886 baute Carl Benz das erste Auto mit Motor.",
            "Karl Bens 1886-yilda birinchi dvigatelli avtomobilni yasagan.")],
    "fr": [("🚀", "Jules Verne", "Jules Verne écrivait des aventures.", "Jules Verne a imaginé des voyages sur la Lune et sous la mer.",
            "Jyul Vern — Oyga va dengiz tubiga sayohat haqida yozgan."),
           ("⚗️", "Marie Curie", "Marie Curie était une grande savante.", "Marie Curie a reçu deux prix Nobel pour ses découvertes.",
            "Mariya Kyuri — ikki marta Nobel mukofotini olgan olima."),
           ("🤴", "Antoine de Saint-Exupéry", "Il a écrit Le Petit Prince.", "Saint-Exupéry était pilote et il a écrit Le Petit Prince.",
            "Sent-Ekzyuperi — uchuvchi, «Kichkina shahzoda»ni yozgan."),
           ("🦠", "Louis Pasteur", "Pasteur aidait les gens à être en bonne santé.", "Louis Pasteur a créé des vaccins qui ont sauvé beaucoup de vies.",
            "Lui Paster — ko'p hayotni saqlab qolgan vaksinalar yaratgan.")],
    "es": [("🐴", "Miguel de Cervantes", "Cervantes escribió Don Quijote.", "Cervantes escribió Don Quijote, una de las novelas más famosas del mundo.",
            "Servantes — «Don Kixot»ni yozgan buyuk ispan yozuvchisi."),
           ("🎨", "Pablo Picasso", "Picasso pintaba cuadros.", "Pablo Picasso pintó cuadros con formas y colores muy nuevos.",
            "Pablo Pikasso — mashhur ispan rassomi."),
           ("🎸", "Andrés Segovia", "Segovia tocaba la guitarra.", "Andrés Segovia llevó la guitarra española a las grandes salas de concierto.",
            "Andres Segoviya — ispan gitarasini butun dunyoga tanitgan."),
           ("🏛️", "Antoni Gaudí", "Gaudí hizo casas muy bonitas.", "Antoni Gaudí construyó la Sagrada Familia en Barcelona.",
            "Antoni Gaudi — Barselonadagi ajoyib binolar me'mori.")],
    "ru": [("🚀", "Юрий Гагарин", "Гагарин полетел в космос.", "В 1961 году Юрий Гагарин первым полетел в космос.",
            "Yuriy Gagarin 1961-yilda koinotga birinchi bo'lib uchgan."),
           ("📚", "Лев Толстой", "Толстой писал книги.", "Лев Толстой написал большой роман «Война и мир» и сказки для детей.",
            "Lev Tolstoy — «Urush va tinchlik» va bolalar uchun ertaklar yozgan."),
           ("🧪", "Дмитрий Менделеев", "Менделеев был учёным.", "Менделеев создал таблицу химических элементов.",
            "Mendeleyev kimyoviy elementlar jadvalini yaratgan."),
           ("🎼", "Пётр Чайковский", "Чайковский писал музыку.", "Чайковский написал музыку к балету «Щелкунчик».",
            "Chaykovskiy — «Shelkunchik» baleti musiqasini yozgan.")],
}
MASHHUR_BOSH = {"en": "Famous people!", "de": "Berühmte Menschen!", "fr": "Des gens célèbres !", "es": "¡Gente famosa!", "ru": "Знаменитые люди!"}

# ───────── REV195: Vaziyat (sahnacha) — dialog bo'lmagan mavzular uchun xavfsiz qoliplar (grammatika buzilmasin) ─────────
# {x}, {y} — bugungi va o'tgan dars so'zlari (bosh kelishikda qoladigan qurilmalar)
VAZIYAT = {
    "en": [("Kabu, where is the {x}?", "Hmm… here it is!", "Yes! The {x}! Well done!", "And what is this?", "It's the {y}!", "Great! The {x} and the {y}!")],
    "de": [("Kabu, wo ist {x}?", "Hmm… hier ist {x}!", "Ja, richtig! Super!", "Und was ist das?", "Das ist {y}!", "Toll! {x} und {y}!")],
    "fr": [("Kabu, où est {x} ?", "Hmm… voilà {x} !", "Oui, bravo !", "Et ça, qu'est-ce que c'est ?", "C'est {y} !", "Super ! {x} et {y} !")],
    "es": [("Kabu, ¿dónde está {x}?", "Mmm… ¡aquí está {x}!", "¡Sí! ¡Muy bien!", "¿Y qué es esto?", "¡Es {y}!", "¡Genial! ¡{x} y {y}!")],
    "ru": [("Кабу, где {x}?", "Хм… вот {x}!", "Да! Молодец!", "А что это?", "Это {y}!", "Отлично! {x} и {y}!")],
}
SAHNA_BOSH = {"en": "Scene time!", "de": "Unsere kleine Szene!", "fr": "Notre petite scène !", "es": "¡Nuestra pequeña escena!", "ru": "Маленькая сценка!"}
KIM_AYTDI = {"en": "Who said: “{g}”?", "de": "Wer hat gesagt: „{g}“?", "fr": "Qui a dit : « {g} » ?", "es": "¿Quién dijo: «{g}»?", "ru": "Кто сказал: «{g}»?"}

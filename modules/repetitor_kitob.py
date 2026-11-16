"""Repetitor kitobi (Matematikadan repetitorlik, 1–148 dars): AI miya orqali «Matematika · 11» ostida
« (Repetitor)» qo'shimchali mavzular sifatida yuklangan. Kurslar katalogida ular alohida kurs bo'lib chiqadi
(sinfga qaramasdan), tartibi — shu ro'yxat bo'yicha."""
KALIT = "repetitor|Matematikadan repetitorlik|148"
NOMI = "Matematikadan repetitorlik · 148 dars"
FAN = "Matematika"
SINF = "Repetitor"          # kurs ichidagi belgi (katalogda sinf o'rnida)
ASL_SINF = "11"             # darslar dts_tree da shu sinfda turadi
QOSHIMCHA = " (Repetitor)"
NOMLAR = [
"Natural sonlar va to'rt amal",
"Qulay hisoblash",
"Bo'linish belgilari",
"Tub ko'paytuvchilarga ajratish",
"EKUB va EKUK",
"Qoldiqli bo'lish",
"Oxirgi raqam",
"Butun sonlar",
"Oddiy kasrlar: asosiy xossa",
"Oddiy kasrlar ustida amallar",
"Aralash sonlar",
"O'nli kasrlar",
"Oddiy va o'nli kasrlar aralash",
"Cheksiz davriy o'nli kasrlar",
"Daraja va uning xossalari",
"Birhad va ko'phad",
"Ko'phadlar ustida amallar",
"Qisqa ko'paytirish: kvadratlar",
"Qisqa ko'paytirish: kublar",
"Ko'paytuvchilarga ajratish: qavsdan chiqarish va guruhlash",
"Ko'paytuvchilarga ajratish: formulalar bilan",
"Algebraik kasrlar",
"Ifodalarni soddalashtirish va ayniyatlar",
"Arifmetik kvadrat ildiz",
"Ildizli ifodalarni soddalashtirish",
"Ikki qavatli ildizlar",
"n-darajali ildiz va ratsional ko'rsatkich",
"Sonning standart shakli",
"Chiziqli tenglama",
"Proporsiya",
"Chala kvadrat tenglamalar",
"Kvadrat tenglama va diskriminant",
"Viyet teoremasi",
"Kvadrat tenglamaga keltiriladigan tenglamalar",
"Ratsional tenglamalar",
"Parametrli chiziqli tenglamalar",
"Parametrli kvadrat tenglamalar",
"Chiziqli tenglamalar sistemasi",
"Chiziqli va ikkinchi darajali tenglamalar sistemasi",
"Ikkinchi va yuqori darajali sistemalar",
"Parametrli sistemalar",
"Sonli tengsizliklar va isbotlash",
"Chiziqli tengsizliklar",
"Chiziqli tengsizliklar sistemasi",
"Kvadrat tengsizliklar",
"Oraliqlar usuli",
"Parametrli tengsizliklar",
"Sonning moduli",
"Modulli tenglamalar",
"Modulli tengsizliklar",
"Modulli tenglama va tengsizliklar sistemasi",
"Irratsional tenglamalar",
"Irratsional tengsizliklar",
"Arifmetik progressiya",
"Arifmetik progressiya yig'indisi",
"Geometrik progressiya",
"Geometrik progressiya yig'indisi",
"Cheksiz kamayuvchi geometrik progressiya",
"Sonlarga oid masalalar: tenglama tuzish",
"Sonlarga oid masalalar: o'rta qiymat va qismlar",
"Prosent",
"Prosentga oid masalalar: o'sish va kamayish",
"Harakatga oid masalalar: tekis harakat",
"Harakatga oid masalalar: oqim va aylana",
"Ishga oid masalalar",
"Aralashmaga oid masalalar",
"Nuqta, to'g'ri chiziq, burchak",
"Parallel to'g'ri chiziqlar",
"Uchburchak va uning chiziqlari",
"Uchburchak burchaklari",
"To'g'ri burchakli uchburchak va Pifagor teoremasi",
"Funksiya tushunchasi",
"Funksiya xossalari",
"Chiziqli funksiya",
"Kvadrat funksiya",
"Grafikni almashtirish",
"Teskari funksiya",
"Ko'rsatkichli funksiya",
"Ko'rsatkichli tenglamalar",
"Ko'rsatkichli tengsizliklar",
"Logarifm va uning xossalari",
"Logarifmik funksiya",
"Logarifmik ifodalarni shakl almashtirish",
"Logarifmik tenglamalar",
"Logarifmik tengsizliklar",
"Burchakning radian o'lchovi",
"Sinus, kosinus, tangens, kotangens",
"Trigonometrik funksiyalar ishoralari",
"Asosiy trigonometrik ayniyatlar",
"Juft-toqlik va keltirish formulalari",
"Trigonometrik funksiyalarning xossalari va grafiklari",
"Qo'shish formulalari",
"Ikkilangan va yarim burchak formulalari",
"Yig'indi va ko'paytma formulalari",
"Teskari trigonometrik funksiyalar",
"Eng sodda trigonometrik tenglamalar",
"Trigonometrik tenglamalarni yechish usullari",
"Tenglama yechimlarini oraliqdan tanlash",
"Trigonometrik tengsizliklar",
"Kosinuslar va sinuslar teoremasi",
"Balandlik va mediana xossalari",
"Bissektrisa xossalari",
"Uchburchakning yuzi",
"Uchburchaklarning o'xshashligi",
"To'rtburchak, to'g'ri to'rtburchak, kvadrat",
"Parallelogramm",
"Romb",
"Trapetsiya",
"Ko'pburchaklar",
"Aylana: urinma, vatar, radius",
"Markaziy va ichki chizilgan burchaklar",
"Aylana uzunligi, yoyi va doira yuzi",
"Aylanada kesishuvchi kesmalar",
"Hosila tushunchasi va darajali funksiya hosilasi",
"Ko'paytma va bo'linma hosilasi",
"Elementar funksiyalar hosilalari",
"Murakkab funksiyaning hosilasi",
"Hosilaning fizik ma'nosi",
"Urinmaning burchak koeffitsiyenti",
"Urinma tenglamasi",
"O'sish va kamayish oraliqlari",
"Ekstremumlar",
"Eng katta va eng kichik qiymat",
"Hosila yordamida grafik yasash",
"Boshlang'ich funksiya",
"Boshlang'ich funksiyani topish qoidalari",
"Aniq integral",
"Egri chiziqli trapetsiyaning yuzi",
"Vektor va uning uzunligi",
"Vektorlar ustida amallar",
"Vektorlarning skalyar ko'paytmasi",
"Ikki vektor orasidagi burchak",
"Vektorlarning kollinearligi",
"Fazoda to'g'ri chiziqlar va tekisliklar",
"Kub va parallelepiped",
"Prizma",
"Piramida va uning hajmi",
"Ko'pyoqlarning sirt yuzi",
"Kesik piramida",
"Silindr",
"Konus: yon va to'la sirt",
"Konusning hajmi va kesik konus",
"Shar va sfera",
"Ko'pyoqlar va shar",
"Aylanish jismlari va shar",
"Baholash usuli",
"Funksiyaning monotonligi bilan yechish",
"Almashtirish va simmetriya"
]


def nom_sql(a="d"):
    """dts_tree qatori Repetitor kitobiga tegishlimi — SQL sharti."""
    return "(" + " OR ".join(f"{a}.{c} LIKE '%%{QOSHIMCHA}'" for c in ("kichik_name", "mavzu_name", "bolim_name", "bob_name")) + ")"


def tartib_raqam(nom):
    """Dars nomidan (qo'shimchali yoki qo'shimchasiz) 1..148 raqam; topilmasa 0."""
    s = str(nom or "").strip()
    if s.endswith(QOSHIMCHA):
        s = s[: -len(QOSHIMCHA)].strip()
    try:
        return NOMLAR.index(s) + 1
    except ValueError:
        return 0


def korinadigan_nom(nom):
    n = tartib_raqam(nom)
    s = str(nom or "").strip()
    if s.endswith(QOSHIMCHA):
        s = s[: -len(QOSHIMCHA)].strip()
    return f"{n}-dars. {s}" if n else s

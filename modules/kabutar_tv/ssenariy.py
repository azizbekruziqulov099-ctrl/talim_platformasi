"""REV185: KABUTAR TV — SSENARIYCHI.

Har kuni har til va har daraja (2-3 yosh … 11-sinf) uchun ko'rsatuv ssenariysini tuzadi:
bugungi mavzu + kechagi va o'tgan haftalar takrori. Ishtirokchilar:
  T  — o'rganilayotgan til ustozi (Emily, Lukas, Camille, Carlos, Anna)
  I  — izoh ustozi Nilufar (o'zbekcha)
  K1 — til Kabusi (o'rganilayotgan tilda)
  K2 — o'zbek Kabu
Immersiya saytdagi darslar bilan bir xil: 1–4-sinfda o'zbekcha ko'p, yil oxiriga ~50 %; 5–6-sinf faqat yangi so'z
izohi; 7–11-sinf to'liq o'rganilayotgan tilda (Nilufar va o'zbek Kabu chiqmaydi).
"""
import datetime as dt
import json
import os
import random
import re
from functools import lru_cache

from . import rukn_matn as RM

DATA = os.path.join(os.path.dirname(__file__), "data")
DARAJALAR = ["2-3 yosh", "4-5 yosh", "6-7 yosh"] + [f"{i}-sinf" for i in range(1, 12)]
TILLAR = {"en": "Ingliz tili", "de": "Nemis tili", "fr": "Fransuz tili", "es": "Ispan tili", "ru": "Rus tili"}
USTOZ = {"en": ("emily", "Emili opa", "Miss Emily", False), "de": ("lukas", "Lukas aka", "Herr Lukas", True),
         "fr": ("camille", "Kamilla opa", "Madame Camille", False), "es": ("carlos", "Karlos aka", "Señor Carlos", True),
         "ru": ("anna", "Anna opa", "Анна", False)}
DAVOMIYLIK = {"2-3 yosh": 300, "4-5 yosh": 420, "6-7 yosh": 480}   # soniya; sinflar — pastda
# REV188: efir guruhlari (Telegram/Instagram va Kabutar kanallari uchun). 2–7 yosh va 1–11-sinf aralashmaydi.
AUDITORIYALAR = ["2-3 yosh", "4-5 yosh", "6-7 yosh", "1-4-sinf", "5-6-sinf", "7-sinf", "8-sinf", "9-sinf", "10-11-sinf"]
AUD_DAVOM = {"2-3 yosh": 300, "4-5 yosh": 420, "6-7 yosh": 480, "1-4-sinf": 600, "5-6-sinf": 660, "7-sinf": 720,
             "8-sinf": 720, "9-sinf": 840, "10-11-sinf": 900}


def aud_darajalari(aud):
    """Auditoriya qaysi sinf/yosh kanallariga tegishli: «1-4-sinf» → 1-, 2-, 3-, 4-sinf."""
    m = re.fullmatch(r"(\d+)-(\d+)-sinf", aud)
    if m:
        return [f"{i}-sinf" for i in range(int(m.group(1)), int(m.group(2)) + 1)]
    return [aud]


def aud_manba(aud, tartib):
    """Guruhli auditoriyada dars manbasi navbat bilan almashadi (1-4-sinf: bugun 1-sinf so'zlari, ertaga 2-sinf…) — zerikmaydi."""
    d = aud_darajalari(aud)
    return d[tartib % len(d)]

# o'rganilayotgan tildagi tayyor gaplar
G = {
    "en": dict(salom="Hello, children! I'm {ism}.", kabu_salom="Hi! I'm Kabu!", takrorla="Say it with me!", bu_nima="What is it?",
               ha="Yes! Well done!", sozlar="Today's words!", oyin="Let's play! What is it?", gap="Let's make a sentence!",
               dialog="Listen to the dialogue.", takror="Do you remember?", xayr="Goodbye, children! See you tomorrow!", kabu_xayr="Bye-bye!",
               tingla="Listen!", yana="One more time!", mavzu="Today's topic is: {nom}."),
    "de": dict(salom="Hallo, Kinder! Ich bin {ism}.", kabu_salom="Hallo! Ich bin Kabu!", takrorla="Sag es mit mir!", bu_nima="Was ist das?",
               ha="Ja! Super!", sozlar="Die Wörter von heute!", oyin="Wir spielen! Was ist das?", gap="Wir bauen einen Satz!",
               dialog="Hör dir den Dialog an.", takror="Erinnerst du dich?", xayr="Tschüss, Kinder! Bis morgen!", kabu_xayr="Tschüss!",
               tingla="Hör zu!", yana="Noch einmal!", mavzu="Unser Thema heute: {nom}."),
    "fr": dict(salom="Bonjour, les enfants ! Je suis {ism}.", kabu_salom="Salut ! Je suis Kabu !", takrorla="Répète avec moi !", bu_nima="Qu'est-ce que c'est ?",
               ha="Oui ! Bravo !", sozlar="Les mots du jour !", oyin="On joue ! Qu'est-ce que c'est ?", gap="Faisons une phrase !",
               dialog="Écoute le dialogue.", takror="Tu te souviens ?", xayr="Au revoir, les enfants ! À demain !", kabu_xayr="Salut !",
               tingla="Écoute !", yana="Encore une fois !", mavzu="Le thème d'aujourd'hui : {nom}."),
    "es": dict(salom="¡Hola, niños! Soy {ism}.", kabu_salom="¡Hola! ¡Soy Kabu!", takrorla="¡Repite conmigo!", bu_nima="¿Qué es?",
               ha="¡Sí! ¡Muy bien!", sozlar="¡Las palabras de hoy!", oyin="¡Vamos a jugar! ¿Qué es?", gap="¡Hagamos una frase!",
               dialog="Escucha el diálogo.", takror="¿Te acuerdas?", xayr="¡Adiós, niños! ¡Hasta mañana!", kabu_xayr="¡Chao!",
               tingla="¡Escucha!", yana="¡Otra vez!", mavzu="El tema de hoy: {nom}."),
    "ru": dict(salom="Здравствуйте, ребята! Я — {ism}.", kabu_salom="Привет! Я — Кабу!", takrorla="Повторяй за мной!", bu_nima="Что это?",
               ha="Да! Молодец!", sozlar="Слова дня!", oyin="Играем! Что это?", gap="Составим предложение!",
               dialog="Послушай диалог.", takror="Ты помнишь?", xayr="До свидания, ребята! До завтра!", kabu_xayr="Пока-пока!",
               tingla="Слушай!", yana="Ещё раз!", mavzu="Тема дня: {nom}."),
}
UZ = dict(salom="Assalomu alaykum, bolajonlar! Men Nilufar opangizman. Bugun {u} bilan {til}dan dars takrorlaymiz.",
          kabu_salom="Salom! Men o'zbek Kabuman!", dedi="", qisqa="",
          soz="Bu — «{t}».", soz_q="«{t}».", takrorla="Siz ham takrorlang!",
          oyin="Endi o'yin! Rasmga qarang. Bu nima? O'ylang!", gap="Endi gap tuzamiz. So'zlarni to'g'ri tartibda qo'yamiz.",
          dialog="Endi kichik suhbatni tinglaymiz.", takror="Endi o'tgan darslarni eslaymiz.", oylang="Uch, ikki, bir!",
          xayr="Barakalla, bolajonlar! Ertaga yana uchrashamiz!", kabu_xayr="Xayr!", mavzu="Bugungi mavzu — «{nom}».")


# REV188: Nilufar opa tarjima qilmaydi — o'zi gapiradi (har safar boshqacha, tabiiy)
SOZ_UZ = ["Bu — «{t}».", "O'zbekchasi — «{t}».", "«{t}» — eslab qoling!", "Ma'nosi — «{t}».", "Ha, «{t}»!"]


# REV205: boshlovchilarning o'tish gaplari — ko'rsatuv bo'limlari bir-biriga tabiiy ulanadi (ustozlar bir-biriga gapiradi)
OTISH = {
    "teatr": {"en": "Now let's watch a little scene with the Kabus!", "de": "Jetzt schauen wir eine kleine Szene mit den Kabus!",
              "fr": "Regardons maintenant une petite scène avec les Kabus !", "es": "¡Ahora veamos una pequeña escena con los Kabus!",
              "ru": "А теперь посмотрим сценку с Кабу!", "uz": "Kabular bizga kichik sahna tayyorlashibdi. Diqqat bilan tinglang!"},
    "oyin": {"en": "Are you ready to play? Let's go to Kabu's games!", "de": "Seid ihr bereit? Auf zu Kabus Spielen!",
             "fr": "Vous êtes prêts ? Allons jouer avec Kabu !", "es": "¿Listos? ¡Vamos a los juegos de Kabu!",
             "ru": "Готовы? Идём играть с Кабу!", "uz": "O'yin vaqti! Javoblarni baland ovozda ayting!"},
    "maqtov": {"en": "Great job, children! You are so clever!", "de": "Super gemacht, Kinder! Ihr seid so klug!",
               "fr": "Bravo, les enfants ! Vous êtes très forts !", "es": "¡Muy bien, niños! ¡Sois muy listos!",
               "ru": "Молодцы, ребята! Вы такие умные!", "uz": "Barakalla, bolajonlar! {ism} ham sizdan juda xursand!"},
    "sayohat": {"en": "Where will Kabu fly today? Let's see!", "de": "Wohin fliegt Kabu heute? Mal sehen!",
                "fr": "Où va voler Kabu aujourd'hui ? Voyons !", "es": "¿Adónde volará Kabu hoy? ¡Veamos!",
                "ru": "Куда сегодня полетит Кабу? Посмотрим!", "uz": "Qani, Kabu bugun qayerga uchar ekan?"},
    "yakun": {"en": "Thank you, Kabus! That was fun!", "de": "Danke, Kabus! Das war toll!", "fr": "Merci, les Kabus ! C'était super !",
              "es": "¡Gracias, Kabus! ¡Fue genial!", "ru": "Спасибо, Кабу! Было здорово!", "uz": "Rahmat, Kabular! Bugun juda qiziqarli bo'ldi."},
}


# REV193: Kabu o'yinlari iboralari va sonlar
OYIN = {
    "en": {"bosh": "It's Kabu game time! Let's play!", "qayerda": "Where is {s}?", "sanaymiz": "Let's count!", "yakun": "Today we learned:"},
    "de": {"bosh": "Zeit für Kabus Spiele! Los geht's!", "qayerda": "Wo ist {s}?", "sanaymiz": "Wir zählen!", "yakun": "Heute haben wir gelernt:"},
    "fr": {"bosh": "C'est l'heure des jeux de Kabu ! On joue !", "qayerda": "Où est {s} ?", "sanaymiz": "On compte !", "yakun": "Aujourd'hui, on a appris :"},
    "es": {"bosh": "¡Hora de los juegos de Kabu! ¡A jugar!", "qayerda": "¿Dónde está {s}?", "sanaymiz": "¡Vamos a contar!", "yakun": "Hoy aprendimos:"},
    "ru": {"bosh": "Время игр с Кабу! Играем!", "qayerda": "Где {s}?", "sanaymiz": "Считаем!", "yakun": "Сегодня мы выучили:"},
}
SONLAR = {
    "en": "one two three four five six seven eight nine ten".split(),
    "de": "eins zwei drei vier fünf sechs sieben acht neun zehn".split(),
    "fr": "un deux trois quatre cinq six sept huit neuf dix".split(),
    "es": "uno dos tres cuatro cinco seis siete ocho nueve diez".split(),
    "ru": "один два три четыре пять шесть семь восемь девять десять".split(),
}


@lru_cache(maxsize=16)
def lugat_sozlari(til, darajalar):
    """REV193: mavzuda so'z bo'lmasa (4-5, 6-7 yosh) — lug'at miyasidan shu yoshga mos rasmli so'zlar."""
    p = os.path.join(os.path.dirname(DATA), "..", "lugat_miyasi_data", f"{til}.json")
    try:
        with open(os.path.normpath(p), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return []
    out = []
    for v in d.get("sozlar", {}).values():
        if "s" in v and v.get("e") and v.get("d") in darajalar and (v.get("t") or {}).get("uz") and len(v["s"]) <= 18:
            out.append({"s": v["s"], "t": v["t"]["uz"], "e": v["e"]})
    out.sort(key=lambda x: x["s"].lower())
    return out


@lru_cache(maxsize=8)
def _turkumlar(til):
    p = os.path.normpath(os.path.join(os.path.dirname(DATA), "..", "lugat_miyasi_data", f"{til}.json"))
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)["sozlar"]
    except Exception:
        return {}
    return {k: v.get("k", "") for k, v in d.items() if "s" in v}


@lru_cache(maxsize=8)
def _tarjimalar(til):
    """REV195: gap → o'zbekcha tarjima (lug'at miyasidagi juft gaplardan) — sahnachada kichiklarga tarjima uchun."""
    p = os.path.normpath(os.path.join(os.path.dirname(DATA), "..", "lugat_miyasi_data", f"{til}.json"))
    try:
        with open(p, encoding="utf-8") as f:
            g = json.load(f).get("gaplar", [])
    except Exception:
        return {}
    norm = lambda x: re.sub(r"[^\w]+", " ", x.lower()).strip()
    return {norm(a): (b or {}).get("uz", "") for a, b in g if (b or {}).get("uz")}


def tarjima_top(til, gap):
    return _tarjimalar(til).get(re.sub(r"[^\w]+", " ", str(gap).lower()).strip(), "")


def rasmga_mos(til, soz):
    """REV194: «Rasmni top» o'yiniga faqat rasmda ko'rinadigan so'zlar (ot, son, rang) — fe'l va ravish emas."""
    k = _turkumlar(til).get(str(soz).lower().strip(" .!?"), "")
    return k not in ("fe'l", "ravish", "olmosh", "predlog", "bog'lovchi", "yuklama", "ibora", "undov") and len(str(soz).split()) <= 3


@lru_cache(maxsize=8)
def manba(til):
    with open(os.path.join(DATA, "manba", f"{til}.json"), encoding="utf-8") as f:
        return json.load(f)


def sinf_yosh(daraja):
    m = re.match(r"(\d+)-sinf", daraja)
    if m:
        return int(m.group(1)), 0
    return 0, int(daraja[0])


def ulush(daraja, raqam, jami):
    """Saytdagi immersiya (src/til/immersiya.js) bilan bir xil: 0..1 — o'rganilayotgan til ulushi."""
    sinf, yosh = sinf_yosh(daraja)
    p = min(1.0, max(0.0, (raqam - 1) / max(1, jami - 1)))
    lerp = lambda a, b: a + (b - a) * p
    if yosh:
        return lerp(0.15, 0.35) if yosh <= 3 else lerp(0.35, 0.6) if yosh <= 5 else lerp(0.6, 0.85)
    return {1: lerp(0, .15), 2: lerp(.15, .3), 3: lerp(.3, .45), 4: lerp(.45, .6), 5: lerp(.8, .85), 6: lerp(.85, .9)}.get(sinf, 1.0)


def davomiylik(daraja):
    sinf, _ = sinf_yosh(daraja)
    if not sinf:
        return DAVOMIYLIK[daraja]
    return 600 if sinf <= 4 else 720 if sinf <= 8 else 900


def oquv_kuni(sana):
    """O'quv yili 2-sentabr — 25-may. Yoz oylarida — takrorlash (yil oxirgi qismi)."""
    yil = sana.year if sana.month >= 9 else sana.year - 1
    bosh, ox = dt.date(yil, 9, 2), dt.date(yil + 1, 5, 25)
    jami = (ox - bosh).days
    return min(1.0, max(0.0, (sana - bosh).days / jami))


def bugungi_raqam(daraja, til, sana):
    mavzular = manba(til).get(daraja) or []
    if not mavzular:
        return 0, 0
    jami = len(mavzular)
    return min(jami, 1 + int(oquv_kuni(sana) * (jami - 1))), jami


def _ttaxmin(matn):
    return len(matn) / 13.0 + 0.5


def ob_havo_ol(sana=None, timeout=10):
    """REV187: Samarqand ob-havosi (open-meteo, kalitsiz). Qaytaradi: {holat, max, min} yoki None."""
    import json as _json
    import urllib.request
    url = ("https://api.open-meteo.com/v1/forecast?latitude=39.65&longitude=66.96&daily=weathercode,temperature_2m_max,"
           "temperature_2m_min&timezone=Asia%2FTashkent&forecast_days=2")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            d = _json.loads(r.read().decode())["daily"]
        i = 0
        if sana is not None and sana.isoformat() in d.get("time", []):
            i = d["time"].index(sana.isoformat())
        return {"holat": ob_holat(int(d["weathercode"][i])), "max": round(d["temperature_2m_max"][i]), "min": round(d["temperature_2m_min"][i])}
    except Exception:
        return None


def ob_holat(kod):
    if kod in (0, 1):
        return "quyosh"
    if kod in (2, 3):
        return "bulut"
    if kod in (45, 48):
        return "tuman"
    if 71 <= kod <= 77 or kod in (85, 86):
        return "qor"
    if kod >= 95:
        return "momaqaldiroq"
    return "yomgir"


def fasl_ob_havo(sana):
    """Internet bo'lmasa — fasl bo'yicha taxminiy (Samarqand o'rtacha)."""
    jadval = {1: ("bulut", 8, -2), 2: ("bulut", 11, 0), 3: ("yomgir", 17, 5), 4: ("quyosh", 23, 9), 5: ("quyosh", 28, 13), 6: ("quyosh", 34, 17),
              7: ("quyosh", 36, 19), 8: ("quyosh", 34, 17), 9: ("quyosh", 29, 12), 10: ("quyosh", 22, 7), 11: ("bulut", 15, 3), 12: ("qor", 9, -1)}
    h, mx, mn = jadval[sana.month]
    return {"holat": h, "max": mx, "min": mn, "taxminiy": True}


class Ssenariy:
    def __init__(self, til, daraja, sana, ob_havo=None, tartib=None):
        # REV188: daraja — auditoriya bo'lishi mumkin («1-4-sinf»): dars manbasi navbat bilan bitta sinfdan olinadi
        self.auditoriya = daraja
        if daraja not in DARAJALAR:
            t0 = tartib if tartib is not None else max(0, (sana - dt.date(sana.year if sana.month >= 9 else sana.year - 1, 9, 2)).days)
            daraja = aud_manba(daraja, t0)
        self.til, self.daraja, self.sana = til, daraja, sana
        self.ob = ob_havo or fasl_ob_havo(sana)
        # shu til uchun nechanchi ko'rsatuv (yil boshidan) — rukn va faktlar takrorlanmasligi uchun
        self.tartib = tartib if tartib is not None else max(0, (sana - dt.date(sana.year if sana.month >= 9 else sana.year - 1, 9, 2)).days)
        self.raqam, self.jami = bugungi_raqam(daraja, til, sana)
        self.u = ulush(daraja, self.raqam or 1, self.jami or 1)
        k, uz_ism, ism, erkak = USTOZ[til]
        self.ustoz, self.uz_ism, self.ism, self.erkak = k, uz_ism, ism, erkak
        self.sahnalar, self.vaqt = [], 0.0
        self.rnd = random.Random(f"{til}|{daraja}|{sana.isoformat()}")
        self.uzbek = self.u < 0.999          # Nilufar va o'zbek Kabu chiqadimi
        self.fon = "fon_bogcha_toza" if "yosh" in daraja else "fon_maktab_toza"

    # ── yordamchilar ──
    def sahna(self, nom, karta=None, **rej):
        """rej (REV193, rejissorga): joy="oyin" (Kabu o'yin studiyasi), kamera="yaqin", bayram=True (konfetti), pop=False."""
        self.sahnalar.append({"nom": nom, "karta": karta, "qatorlar": [], **rej})
        return self.sahnalar[-1]

    def ayt(self, kim, matn, til=None, pauza=0.25, sanoq=0):
        matn = re.sub(r"\s+", " ", re.sub("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u20E3]+", "", matn or "")).strip()
        if not matn:
            return
        # REV196: studiyada faqat ikki ustoz — Kabu gaplari studiyada bo'lsa, ustozlarga o'tadi (Kabular o'z lavhasida)
        if self.sahnalar and self.sahnalar[-1].get("joy") != "oyin" and kim in ("K1", "K2"):
            if re.search(r"\bKabu|Кабу", matn):   # «Men Kabuman» kabi gapni ustoz aytmaydi — Kabular o'z lavhasida tanishadi
                return
            kim = "T" if kim == "K1" else ("I" if self.uzbek else "T")
            if kim == "T" and til == "uz":
                til = None
        til = til or (self.til if kim in ("T", "K1") else "uz")
        self.sahnalar[-1]["qatorlar"].append({"kim": kim, "matn": matn, "til": til, "pauza": pauza, "sanoq": sanoq})
        self.vaqt += _ttaxmin(matn) + pauza + sanoq

    def izoh_kerak(self, yangi=True):
        """Shu gapga o'zbekcha izoh beriladimi (immersiya bo'yicha)."""
        if not self.uzbek:
            return False
        if self.u < 0.3:
            return True
        if self.u < 0.8:
            return yangi or self.rnd.random() > self.u
        return yangi and self.rnd.random() > 0.5

    def uz_gap(self, kalit, **kw):
        return UZ[kalit].format(u=self.uz_ism, **kw)

    # ── bo'limlar ──
    def salomlashish(self, mavzu):
        g = G[self.til]
        self.sahna("salom", {"sarlavha": TILLAR[self.til], "pastki": mavzu.get("nom", "")})
        self.ayt("T", g["salom"].format(ism=self.ism))
        self.sahna("salom_yaqin", None, kamera="yaqin")   # REV193: boshlovchilar yaqin planda
        if self.uzbek:
            self.ayt("I", self.uz_gap("salom", til=TILLAR[self.til].lower()))
        self.ayt("K1", g["kabu_salom"])
        if self.uzbek and self.u < 0.6:
            self.ayt("K2", UZ["kabu_salom"])
        if mavzu.get("nom") and self.uzbek:
            self.ayt("I", UZ["mavzu"].format(nom=mavzu["nom"]))

    def bugungi_sozlar(self, mavzu, chegara):
        g = G[self.til]
        sozlar = mavzu.get("sozlar") or []
        if not sozlar:
            return
        self.sahna("sozlar_bosh", {"sarlavha": g["sozlar"]})
        self.ayt("T", g["sozlar"])
        gaplar = mavzu.get("gaplar") or []
        for s in sozlar:
            if self.vaqt > chegara:
                break
            self.sahna("soz", {"emoji": s.get("e", ""), "soz": s["s"], "tarjima": s["t"] if self.uzbek and self.u < 0.9 else ""})
            self.ayt("T", f"{s['s']}. {s['s']}!", pauza=0.4)
            if self.izoh_kerak(True):
                self.ayt("I", SOZ_UZ[len(self.sahnalar) % len(SOZ_UZ)].format(t=s["t"]))
            misol = next((x for x in gaplar if x["g"].lower().strip(" .!?") != s["s"].lower().strip(" .!?") and re.search(r"(?<!\w)" + re.escape(s["s"].split()[-1]) + r"(?!\w)", x["g"], re.I)), None)
            if misol:
                self.ayt("T", misol["g"], pauza=0.4)
                if misol.get("t") and self.izoh_kerak(False):
                    self.ayt("I", misol["t"])
            self.ayt("K1", g["takrorla"], pauza=0.2)
            self.ayt("T", s["s"], pauza=2.0)   # bola takrorlaydi

    def kabu_oyini(self, sozlar):
        g = G[self.til]
        if len([s for s in sozlar if s.get("e")]) < 2:
            return
        self.sahna("oyin_bosh", {"sarlavha": "🎲 " + g["oyin"].split("!")[0] + "!"})
        self.ayt("K1", g["oyin"])
        if self.uzbek and self.u < 0.6:
            self.ayt("K2", UZ["oyin"])
        tanlov = [s for s in sozlar if s.get("e")]
        self.rnd.shuffle(tanlov)
        for s in tanlov[:4]:
            self.sahna("topishmoq", {"emoji": s["e"], "soz": "?", "tarjima": ""})
            self.ayt("K1", g["bu_nima"], pauza=0.2, sanoq=3)
            self.sahna("javob", {"emoji": s["e"], "soz": s["s"], "tarjima": s["t"] if self.uzbek and self.u < 0.8 else ""})
            self.ayt("T", f"{s['s']}!")
            self.ayt("K1", g["ha"])
            if self.uzbek and self.u < 0.5:
                self.ayt("K2", f"To'g'ri! «{s['t']}»!")

    # ───────── REV193: KABU O'YINLARI — alohida o'yin studiyasi, faqat Kabular ─────────
    def kabu_oyinlari(self, sozlar, boshqa=(), qism=1):
        g, T = G[self.til], OYIN[self.til]
        rasmli = [x for x in sozlar if x.get("e") and rasmga_mos(self.til, x["s"])]
        hovuz = list({x["e"]: x for x in list(sozlar) + list(boshqa) if x.get("e")}.values())
        if len(rasmli) < 1 or len(hovuz) < 3:
            return
        self.sahna("oyin_bosh", {"sarlavha": "🎮 KABU O'YINLARI" if qism == 1 else "🎮 YANA O'YIN!"}, joy="oyin", bayram=True)
        self.ayt("K1", T["bosh"])
        if self.uzbek and self.u < 0.7:
            self.ayt("K2", "Kabu o'yinlari boshlandi! Ekranga qarang va javobni baland ayting!" if qism == 1 else "Yana o'ynaymiz!")
        self.rnd.shuffle(rasmli)
        # 1) Rasmni top
        for x in rasmli[:3]:
            boshqalar = [y["e"] for y in hovuz if y["e"] != x["e"]]
            self.rnd.shuffle(boshqalar)
            var = boshqalar[:2] + [x["e"]]
            self.rnd.shuffle(var)
            togri = var.index(x["e"])
            self.sahna("rasm_savol", {"variantlar": var, "togri": togri, "savol": T["qayerda"].format(s=x["s"])}, joy="oyin")
            self.ayt("K1", T["qayerda"].format(s=x["s"]), pauza=0.2, sanoq=3)
            self.sahna("rasm_javob", {"variantlar": var, "togri": togri, "ochildi": True, "savol": f"{'ABC'[togri]} — {x['s']}"},
                       joy="oyin", bayram=True, pop=False)
            self.ayt("K1", f"{'ABC'[togri]}! {x['s']}! {g['ha']}")
            if self.uzbek and self.u < 0.6:
                self.ayt("K2", f"Barakalla! «{x['t']}»!")
        # 2) Sanaymiz
        x = rasmli[-1]
        sinf, yosh = sinf_yosh(self.daraja)
        n = self.rnd.randint(3, 5) if (yosh or sinf <= 2) else self.rnd.randint(5, 8)
        self.sahna("sanash_bosh", {"sanash": x["e"], "k": 0, "n": n}, joy="oyin")
        self.ayt("K1", T["sanaymiz"])
        if self.uzbek and self.u < 0.5:
            self.ayt("K2", "Keling, birga sanaymiz!")
        for k in range(1, n + 1):
            self.sahna("sanash", {"sanash": x["e"], "k": k, "n": n}, joy="oyin", pop=False, bayram=(k == n))
            self.ayt("K1", SONLAR[self.til][k - 1] + "!", pauza=0.15)
        if self.uzbek and self.u < 0.6:
            self.ayt("K2", f"{n} ta! Zo'r!")
        # 3) Tez ayt — rasm chiqadi, bola nomini aytadi
        for x in rasmli[3:5] or rasmli[:1]:
            self.sahna("tez_savol", {"emoji": x["e"], "soz": "?"}, joy="oyin")
            self.ayt("K1", g["bu_nima"], pauza=0.1, sanoq=2)
            self.sahna("tez_javob", {"emoji": x["e"], "soz": x["s"], "tarjima": x["t"] if self.uzbek and self.u < 0.7 else ""}, joy="oyin", bayram=True, pop=False)
            self.ayt("K1", f"{x['s']}!")

    def yakun(self, sozlar):
        """REV193: «Bugun nimalarni o'rgandik?» — Kabular rasm va so'zlar bilan qisqa xulosa qiladi."""
        tanlov = [x for x in sozlar if x.get("e")][:6] or sozlar[:6]
        if not tanlov:
            return
        T = OYIN[self.til]
        self.sahna("yakun", {"sarlavha": T["yakun"], "panjara": [(x.get("e", ""), x["s"]) for x in tanlov]}, joy="oyin", bayram=True)
        if self.uzbek and self.u < 0.7:
            self.ayt("K2", "Bugun nimalarni o'rgandik? Keling, eslaymiz!")
        self.ayt("K1", T["yakun"] + " " + ", ".join(x["s"] for x in tanlov) + "!")
        self.ayt("K1", G[self.til]["takrorla"], pauza=0.2)
        for x in tanlov[:3]:
            self.ayt("K1", x["s"] + "!", pauza=1.2)
        if self.uzbek:
            self.ayt("K2", "Barakalla! Ertaga yangi o'yinlar bilan kutamiz!")

    def gap_tuzish(self, mavzu):
        g = G[self.til]
        qisqa = [x for x in (mavzu.get("qisqa") or []) if 2 <= len(re.findall(r"[^\W\d_][\w'’-]*", x["g"])) <= 3]
        if not qisqa:
            return
        self.sahna("gap_bosh", {"sarlavha": "🧩 " + g["gap"]}, joy="oyin")
        self.ayt("K1", g["gap"])
        if self.uzbek and self.u < 0.8:
            self.ayt("K2", UZ["gap"])
        for x in qisqa[:3]:
            sozlar = x["g"].rstrip(".!?").split()
            aralash = sozlar[:]
            for _ in range(5):
                self.rnd.shuffle(aralash)
                if aralash != sozlar or len(sozlar) < 2:
                    break
            self.sahna("gap_aralash", {"kartalar": aralash}, joy="oyin")
            self.ayt("K1", g["tingla"], pauza=0.2, sanoq=3)
            self.sahna("gap_tayyor", {"kartalar": sozlar, "tayyor": True, "tarjima": x.get("t", "") if self.uzbek and self.u < 0.8 else ""}, joy="oyin", bayram=True, pop=False)
            self.ayt("K1", x["g"], pauza=0.3)
            if x.get("t") and self.izoh_kerak(False):
                self.ayt("K2", x["t"])
            self.ayt("K1", g["ha"])

    def dialog(self, mavzu):
        g = G[self.til]
        d = mavzu.get("dialog") or []
        if len(d) < 2:
            return
        self.sahna("dialog", {"sarlavha": "💬 " + g["dialog"]})
        self.ayt("T", g["dialog"])
        if self.uzbek and self.u < 0.6:
            self.ayt("I", UZ["dialog"])
        ismlar = list(dict.fromkeys(x["kim"] for x in d))
        for x in d[:6]:
            kim = "T" if x["kim"] == ismlar[0] else "K1"
            self.sahnalar[-1]["qatorlar"].append({"kim": kim, "matn": x["g"], "til": self.til, "pauza": 0.3, "sanoq": 0, "rol": x["kim"]})
            self.vaqt += _ttaxmin(x["g"]) + 0.3

    def takror(self, chegara):
        g = G[self.til]
        mavzular = manba(self.til).get(self.daraja) or []
        if self.raqam <= 1:
            return
        # kecha va 1–2 mavzu oldin ko'proq, o'tgan haftalar — kamroq (oraliqli takror)
        yaqin = mavzular[max(0, self.raqam - 4):self.raqam - 1]
        eski = mavzular[max(0, self.raqam - 14):max(0, self.raqam - 4)]
        sozlar = [s for t in yaqin for s in t["sozlar"]]
        eski_s = [s for t in eski for s in t["sozlar"]]
        self.rnd.shuffle(sozlar)
        self.rnd.shuffle(eski_s)
        tanlov = sozlar[:6] + eski_s[:4]
        if not tanlov:
            return
        self.sahna("takror_bosh", {"sarlavha": "🔁 " + g["takror"]})
        self.ayt("T", g["takror"])
        if self.uzbek and self.u < 0.6:
            self.ayt("I", UZ["takror"])
        for s in tanlov:
            if self.vaqt > chegara:
                break
            if s.get("e"):   # rasm bor — topishmoq: avval «?», bola o'zi aytadi
                self.sahna("takror", {"emoji": s["e"], "soz": "?", "tarjima": ""})
                self.ayt("K1", g["bu_nima"], pauza=0.1, sanoq=2)
            self.sahna("takror_javob", {"emoji": s.get("e", ""), "soz": s["s"], "tarjima": s["t"] if self.uzbek and self.u < 0.6 else ""})
            self.ayt("T", s["s"] + "!")
            if self.izoh_kerak(False) and self.u < 0.5:
                self.ayt("K2", f"«{s['t']}»")

    def tingla_takrorla(self, mavzu, nechta=4):
        g = G[self.til]
        gaplar = [x for x in (mavzu.get("gaplar") or []) if 3 <= len(x["g"].split()) <= 12]
        self.rnd.shuffle(gaplar)
        if not gaplar:
            return False
        self.sahna("tingla_bosh", {"sarlavha": "👂 " + g["tingla"] + " " + g["takrorla"]})
        self.ayt("T", g["tingla"])
        if self.uzbek and self.u < 0.5:
            self.ayt("I", "Tinglang va takrorlang!")
        for x in gaplar[:nechta]:
            self.sahna("tingla", {"gap": x["g"], "tarjima": x.get("t", "") if self.uzbek and self.u < 0.6 else ""})
            self.ayt("T", x["g"], pauza=0.5)
            if x.get("t") and self.izoh_kerak(False):
                self.ayt("I", x["t"])
            self.ayt("T", x["g"], pauza=2.5)   # bola takrorlaydi
        return True

    # ── REV187: TV/radio ruknlari — taqvim, ob-havo, qiziqarli fakt, qo'shiq, fikr savoli (yoshga mos) ──
    def _juft(self, lugat, **kw):
        """Bir xil gap: til ustozida o'rganilayotgan tilda, kerak bo'lsa Nilufar opada o'zbekcha."""
        self.ayt("T", lugat[self.til].format(**{k: (v[self.til] if isinstance(v, dict) else v) for k, v in kw.items()}))
        if self.izoh_kerak(False) and "uz" in lugat:
            self.ayt("I", lugat["uz"].format(**{k: (v["uz"] if isinstance(v, dict) else v) for k, v in kw.items()}))

    def kichikmi(self):
        sinf, yosh = sinf_yosh(self.daraja)
        return bool(yosh) or sinf <= 4

    def taqvim(self):
        b = RM.BAYRAM.get((self.sana.month, self.sana.day))
        fasl = next(v for v in RM.FASL.values() if self.sana.month in v[0])
        hafta = {k: v[self.sana.weekday()] for k, v in RM.HAFTA.items()}
        oy = {k: v[self.sana.month - 1] for k, v in RM.OY.items()}
        self.sahna("taqvim", {"emoji": b["e"] if b else fasl[1], "soz": f"{self.sana.day} {RM.OY[self.til][self.sana.month - 1]}",
                              "tarjima": hafta[self.til].capitalize()})
        self.ayt("K1", RM.TAQVIM_BOSH[self.til] + "!")
        d = self.sana.day
        en_kun = f"{d}{'th' if 10 <= d % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')}"
        self._juft(RM.SANA, kun={**{k: str(d) for k in RM.SANA}, "en": en_kun}, oy=oy, hafta=hafta)
        if b:
            self._juft(RM.BAYRAM_GAP, nom={k: b[k] for k in RM.SANA})
        else:
            self._juft(fasl[2])

    def ob_havo(self):
        h = self.ob["holat"]
        emoji, soz = RM.HOLAT[h]
        katta = not self.kichikmi()
        self.sahna("ob_havo", {"emoji": emoji, "soz": soz[self.til], "tarjima": (f"{self.ob['max']}° / {self.ob['min']}°" if katta else
                                                                                   (soz["uz"] if self.uzbek and self.u < 0.6 else ""))})
        self.ayt("K1", RM.OBHAVO_BOSH[self.til] + "!")
        lug = RM.OBHAVO["katta" if katta else "kichik"]
        self._juft(lug, holat=soz, shahar=RM.SHAHAR, max=str(self.ob["max"]), min=str(self.ob["min"]))
        if katta:
            self._juft(RM.MASLAHAT[h])
        else:
            self.ayt("K1", G[self.til]["takrorla"])
            self.ayt("T", soz[self.til] + "!", pauza=2.0)

    def fakt(self):
        bank = RM.FAKT_KICHIK if self.kichikmi() else RM.FAKT_KATTA
        sinf, yosh = sinf_yosh(self.daraja)
        # har darajaga o'z siljishi — bir kunda turli sinflar boshqa-boshqa fakt eshitadi; ketma-ket ko'rsatuvlarda takrorlanmaydi
        i = (self.tartib // 2 * 7 + (sinf or yosh) * 3) % len(bank)
        emoji, m = bank[i]
        self.sahna("fakt", {"emoji": emoji, "gap": m[self.til], "tarjima": m["uz"] if self.uzbek and self.u < 0.8 else ""})
        self.ayt("K1", RM.FAKT_BOSH[self.til])
        self.ayt("T", m[self.til], pauza=0.5)
        if self.izoh_kerak(True):
            self.ayt("I", m["uz"])
        if sinf >= 9:
            self._juft(RM.SAVOL)
            self.sahnalar[-1]["qatorlar"][-1]["sanoq"] = 3

    # ───────── REV195: 🎭 VAZIYAT — sahnacha: bugungi (yoki o'tgan dars) so'zlari bilan 5–6 gapli jonli suhbat ─────────
    def _dialog(self, m):
        sinf, yosh = sinf_yosh(self.daraja)
        satrlar = [x for x in (m.get("dialog") or [])
                   if x.get("kim") not in ("Say", "Sag", "Dis", "Di", "Скажи") and not re.search(r"…|\.\.\.|___", x.get("g", ""))
                   and 1 <= len(x["g"].split()) <= (8 if (yosh or sinf <= 4) else 16)
                   and not (x["g"].count(",") >= 2 and len(x["g"].split()) <= 6)]   # «sogar, gerade, …» — so'z ro'yxati, gap emas
        from collections import Counter as _C
        sanoq = _C(x["kim"] for x in satrlar)
        satrlar = [x for x in satrlar if sanoq[x["kim"]] >= 2]   # haqiqiy qahramon kamida 2 marta gapiradi («Schule:», «Rate:» — sarlavha)
        rollar = list(dict.fromkeys(x["kim"] for x in satrlar))
        if m.get("nom") in getattr(self, "_ishlatilgan", set()):
            return [], []
        return (satrlar, rollar) if len(satrlar) >= 4 and len(rollar) >= 2 else ([], [])

    def vaziyat(self, mavzu, eski_sozlar=(), qism=1, zaxira=()):
        g = G[self.til]
        sinf, yosh = sinf_yosh(self.daraja)
        satrlar, rollar = self._dialog(mavzu)
        if not satrlar:   # bu mavzuda dialog yo'q — eng yaqin mavzuning haqiqiy dialogi (o'sha so'zlar, yangi vaziyat)
            for m in zaxira:
                satrlar, rollar = self._dialog(m)
                if satrlar:
                    mavzu = {**m, "sozlar": mavzu.get("sozlar") or m.get("sozlar")}
                    break
        if satrlar:
            self._ishlatilgan = getattr(self, "_ishlatilgan", set()) | {mavzu.get("nom")}   # bitta sahnacha bir ko'rsatuvda bir marta
            satrlar = satrlar[:6]
            rol = {r: ("K1" if i % 2 == 0 else "K2") for i, r in enumerate(rollar)}   # REV196: Kabu teatri — ikki Kabu rol o'ynaydi
        else:
            # dialog yo'q — qolip: bugungi va o'tgan so'zlar bilan «Topib ber» sahnachasi
            sozlar = [x for x in (mavzu.get("sozlar") or []) if rasmga_mos(self.til, x["s"])] + [x for x in eski_sozlar if rasmga_mos(self.til, x["s"])]
            if len(sozlar) < 2:
                return
            return self._rasmli_sahna(sozlar[0], sozlar[1])
        nom = mavzu.get("nom", "")
        T = dict(joy="oyin", teatr=True)
        self.sahna("vaziyat_bosh", {"sarlavha": "🎭 KABU TEATRI", "pastki": nom}, **T, bayram=True)
        if self.uzbek and self.u < 0.6:
            self.ayt("K2", f"Kabu teatri! Bugun biz {rollar[0]} va {rollar[1]} bo'lamiz. Diqqat bilan tinglang!", til="uz")
        else:
            self.ayt("K1", RM.SAHNA_BOSH[self.til])
        for x in satrlar:
            k = rol.get(x["kim"], "K1")
            self.sahna("vaziyat", {"sarlavha": "🎭 " + x["kim"], "pastki": nom}, **T, pop=False)
            self.sahnalar[-1]["qatorlar"].append({"kim": k, "matn": x["g"], "til": self.til, "pauza": 0.35, "sanoq": 0, "rol": x["kim"]})
            self.vaqt += _ttaxmin(x["g"]) + 0.35
            if self.uzbek and self.u < 0.5:
                t = tarjima_top(self.til, x["g"])
                if t:
                    self.sahnalar[-1]["qatorlar"].append({"kim": "K2" if k == "K1" else "K1", "matn": t, "til": "uz", "pauza": 0.25, "sanoq": 0})
                    self.vaqt += _ttaxmin(t) + 0.25
        # tushundingmi? — kim aytdi (tanlov)
        savol_q = next((x for x in satrlar[1:] if len(x["g"].split()) >= 2), satrlar[0])
        tanlov = rollar[:3]
        togri = tanlov.index(savol_q["kim"]) if savol_q["kim"] in tanlov else 0
        savol = RM.KIM_AYTDI[self.til].format(g=savol_q["g"])
        self.sahna("vaziyat_savol", {"matn_variant": tanlov, "togri": togri, "savol": savol}, **T)
        if self.uzbek and self.u < 0.5:
            self.ayt("K2", f"Savol! Kim aytdi: «{savol_q['g']}»?", sanoq=3)
        else:
            self.ayt("K1", savol, sanoq=3)
        self.sahna("vaziyat_javob", {"matn_variant": tanlov, "togri": togri, "ochildi": True, "savol": savol}, **T, bayram=True, pop=False)
        self.ayt("K1", f"{savol_q['kim']}! {g['ha']}")
        # endi siz ayting — bugungi so'z bor gap
        bugun = [x["s"].lower() for x in (mavzu.get("sozlar") or [])]
        ayt = next((x for x in satrlar if any(w in x["g"].lower() for w in bugun)), satrlar[0])
        self.sahna("vaziyat_takror", {"gap": ayt["g"], "tarjima": tarjima_top(self.til, ayt["g"]) if self.uzbek and self.u < 0.7 else ""}, **T)
        self.ayt("K1", g["takrorla"], pauza=0.2)
        self.ayt("K1", ayt["g"], pauza=2.5)

    def _rasmli_sahna(self, a, b):
        """2–3 yosh (dialog yo'q): rasmli sahnacha — ustoz rasmni ko'rsatadi, Kabu topadi, birga quvonishadi."""
        R = {"en": ("Kabu, look! What's this?", "It's the {x}!", "Yes! Very good!", "And this? What's this?", "It's the {y}!", "The {x} and the {y}! Hooray!"),
             "de": ("Kabu, schau! Was ist das?", "Das ist {x}!", "Ja! Sehr gut!", "Und das? Was ist das?", "Das ist {y}!", "{x} und {y}! Hurra!"),
             "fr": ("Kabu, regarde ! Qu'est-ce que c'est ?", "C'est {x} !", "Oui ! Très bien !", "Et ça ?", "C'est {y} !", "{x} et {y} ! Hourra !"),
             "es": ("Kabu, ¡mira! ¿Qué es esto?", "¡Es {x}!", "¡Sí! ¡Muy bien!", "¿Y esto?", "¡Es {y}!", "¡{x} y {y}! ¡Hurra!"),
             "ru": ("Кабу, смотри! Что это?", "Это {x}!", "Да! Молодец!", "А это что?", "Это {y}!", "{x} и {y}! Ура!")}[self.til]
        self.sahna("vaziyat_bosh", {"sarlavha": "🎭 KABU TEATRI"}, joy="oyin", teatr=True, bayram=True)
        if self.uzbek:
            self.ayt("K2", "Kabu teatri! Rasmga qarang va biz bilan birga ayting!", til="uz")
        kartalar = [a, a, a, b, b, b]
        for i, t in enumerate(R):
            x = kartalar[i]
            kim = "K1" if i % 2 == 0 else "K2"
            self.sahna("vaziyat_rasm", {"emoji": x.get("e", ""), "soz": x["s"] if i % 3 else "?", "tarjima": x["t"] if i % 3 and self.uzbek else ""},
                       joy="oyin", teatr=True, pop=(i % 3 == 0), bayram=(i == 5))
            self.ayt(kim, t.format(x=a["s"], y=b["s"]), til=self.til, pauza=0.4)
            if i in (1, 4):
                self.ayt("K1", x["s"], pauza=2.0)   # bola takrorlaydi

    def otish(self, turi):
        """REV205: bo'limlar orasida boshlovchilar bir-biriga gapiradi (studiya, ikkalasi ham kadrda)."""
        b = OTISH.get(turi)
        if not b:
            return
        self.sahna("otish_" + turi, None)
        self.ayt("T", b[self.til])
        if self.uzbek and self.u < 0.7:
            self.ayt("I", b["uz"].format(ism=self.uz_ism))

    def mashhur(self):
        """REV195: shu tilda gapiradigan mashhur inson — kichiklarga bir sodda gap, kattalarga batafsil."""
        bank = RM.MASHHUR.get(self.til) or []
        if not bank:
            return
        i = (self.tartib // 2 + (AUDITORIYALAR.index(self.auditoriya) if self.auditoriya in AUDITORIYALAR else 0)) % len(bank)
        emoji, ism, kichik, katta, uz = bank[i]
        gap = kichik if self.kichikmi() else katta
        self.sahna("mashhur", {"emoji": emoji, "soz": ism, "tarjima": ""})
        self.ayt("K1", RM.MASHHUR_BOSH[self.til])
        self.ayt("T", f"{ism}. {gap}", pauza=0.5)
        if self.uzbek:
            self.ayt("I", uz)

    def sayohat(self):
        """REV194: «Kabu sayohatda» — til mamlakati an'anasi yoki tarixi, oxirida «Bizda-chi?» — o'zimizning meros."""
        bank = RM.SAYOHAT.get(self.til) or []
        if not bank:
            return
        sinf, yosh = sinf_yosh(self.daraja)
        i = (self.tartib + (AUDITORIYALAR.index(self.auditoriya) if self.auditoriya in AUDITORIYALAR else 0)) % len(bank)
        emoji, kichik, katta, uz, bizda = bank[i]
        gap = kichik if self.kichikmi() else katta
        self.sahna("sayohat_bosh", {"sarlavha": "✈️ " + RM.SAYOHAT_BOSH[self.til].split("!")[0] + "!"}, joy="oyin", bayram=True)
        self.ayt("K1", RM.SAYOHAT_BOSH[self.til])
        self.sahna("sayohat", {"emoji": emoji, "gap": gap, "tarjima": uz if self.uzbek and self.u < 0.85 else ""})
        self.ayt("T", gap, pauza=0.5)
        if self.uzbek:
            self.ayt("I", uz)
            self.sahna("sayohat_bizda", None, kamera="yaqin")
            self.ayt("K2", "Bizda-chi?")
            self.ayt("I", bizda)

    def qoshiq(self, mavzu):
        sozlar = [x["s"] for x in (mavzu.get("sozlar") or []) if len(x["s"].split()) <= 2]
        if len(sozlar) < 2 or self.til not in RM.QOSHIQ:
            return
        a, b = sozlar[0], sozlar[1]
        self.sahna("qoshiq", {"sarlavha": "🎵 " + RM.QOSHIQ_BOSH[self.til]})
        self.ayt("K1", RM.QOSHIQ_BOSH[self.til])
        if self.uzbek and self.u < 0.5:
            self.ayt("K2", "Birga kuylaymiz va qarsak chalamiz!")
        matn = RM.QOSHIQ[self.til].format(a=a, b=b)
        self.ayt("T", matn, pauza=0.5)
        self.ayt("K1", matn, pauza=1.0)

    def kun_iborasi(self):
        """REV188: hayotiy ibora («My bad!» — «Mening xatoim!») — yoshga mos, har guruhda boshqa, takrorlanmaydi."""
        from .kontent import ibora_tanla
        sinf, yosh = sinf_yosh(self.daraja)
        harf = "k" if (yosh or sinf <= 4) else "o" if sinf <= 8 else "y"
        x = ibora_tanla(self.til, harf, self.tartib * 3 + (sinf or yosh) * 5 + AUDITORIYALAR.index(self.auditoriya) if self.auditoriya in AUDITORIYALAR else self.tartib)
        if not x:
            return
        ibora, uz, misol, _ = x
        g = G[self.til]
        self.sahna("ibora", {"emoji": "💬", "soz": ibora, "tarjima": uz if self.uzbek else ""})
        self.ayt("K1", {"en": "Phrase of the day!", "de": "Satz des Tages!", "fr": "L'expression du jour !", "es": "¡La frase del día!",
                        "ru": "Фраза дня!"}[self.til])
        self.ayt("T", ibora, pauza=0.4)
        if self.uzbek:
            self.ayt("I", f"Bu ibora — «{uz}». Hayotda juda ko'p ishlatiladi.")
        self.sahna("ibora_misol", {"gap": misol, "tarjima": ""})
        self.ayt("T", misol, pauza=0.4)
        self.ayt("K1", g["takrorla"], pauza=0.2)
        self.ayt("T", ibora, pauza=2.0)

    def hayotdan(self):
        """REV188: kundalik hayot — hafta kuniga qarab mavzu (ertalab, maktab, ovqat, sport, oila…), dars matnlaridan gaplar."""
        from .kontent import HAYOT
        nom, kalitlar = HAYOT[(self.tartib + self.sana.weekday()) % len(HAYOT)]
        kal = [k.lower() for k in kalitlar.get(self.til, [])]
        bor = []
        for lv in manba(self.til).values():
            for t in lv:
                for gp in t.get("gaplar") or []:
                    low = gp["g"].lower()
                    if gp.get("t") and 3 <= len(gp["g"].split()) <= 10 and any(k in low for k in kal):
                        bor.append(gp)
        if len(bor) < 2:
            return
        sinf, yosh = sinf_yosh(self.daraja)
        bor.sort(key=lambda x: len(x["g"]))   # kichiklarga qisqa gaplar
        boshi = 0 if (yosh or sinf <= 4) else len(bor) // 3
        hovuz = bor[boshi:boshi + 24] or bor   # REV191: hovuz kichik bo'lsa ham xato bermasin
        tanlov = random.Random(f"{self.til}|{self.auditoriya}|{self.sana}").sample(hovuz, k=min(3, len(hovuz)))
        self.sahna("hayot_bosh", {"sarlavha": "🏡 " + nom})
        if self.uzbek:
            self.ayt("I", f"Endi hayotdan: «{nom}». Tinglang va takrorlang!")
        for gp in tanlov:
            self.sahna("hayot", {"gap": gp["g"], "tarjima": gp["t"] if self.uzbek and self.u < 0.7 else ""})
            self.ayt("T", gp["g"], pauza=0.4)
            if self.izoh_kerak(False):
                self.ayt("I", gp["t"])
            self.ayt("T", gp["g"], pauza=2.0)

    def ruknlar(self, mavzu):
        """Kun ruknlari: taqvim, ob-havo va kun iborasi har kuni; navbat bilan — fakt, hayotdan yoki qo'shiq (zerikmasin)."""
        self.taqvim()
        self.ob_havo()
        self.kun_iborasi()
        if self.kichikmi() and self.tartib % 2:   # REV195: fakt va hayot — ko'rsatuvning o'z joyida; kichiklarga qo'shiq
            self.qoshiq(mavzu)

    def xayrlashuv(self):
        g = G[self.til]
        self.sahna("xayr", None, kamera="yaqin")
        self.ayt("T", g["xayr"])
        if self.uzbek:
            self.ayt("I", UZ["xayr"])
        self.ayt("K1", g["kabu_xayr"])
        if self.uzbek and self.u < 0.6:
            self.ayt("K2", UZ["kabu_xayr"])

    def tuz(self):
        mavzular = manba(self.til).get(self.daraja) or []
        if not mavzular:
            return None
        mavzu = mavzular[self.raqam - 1]
        maqsad = AUD_DAVOM.get(self.auditoriya, davomiylik(self.daraja)) - 20   # kirish/chiqish videosi
        # REV193: KO'RSATUV tartibi (dars emas): salom → kun ruknlari → kun so'zlari (3–4 ta) → 🎮 Kabu o'yinlari →
        # yana bitta rukn → 🎮 o'tganlar bo'yicha o'yin → «Bugun nimani o'rgandik?» → xayr.
        sozlar = mavzu.get("sozlar") or []
        oldingi = [mavzular[i] for i in range(self.raqam - 2, max(-1, self.raqam - 12), -1)]
        eski = [x for m in oldingi for x in (m.get("sozlar") or [])]
        if len(sozlar) < 3:   # REV193: bog'cha 4-7 yosh — mavzuda so'z yo'q, lug'atdan yoshga mos rasmli so'zlar
            _, yosh = sinf_yosh(self.daraja)
            pool = list(lugat_sozlari(self.til, ("2-3 yosh", "4-5 yosh", "1-sinf") if yosh >= 4 else ("2-3 yosh",)))
            if pool:
                i = (self.raqam * 4) % len(pool)
                sozlar = (sozlar + pool[i:i + 4] + pool[:max(0, i + 4 - len(pool))])[:4]
                eski = eski or [pool[(i - k * 3) % len(pool)] for k in range(1, 7)]
                mavzu = {**mavzu, "sozlar": sozlar}
        self.salomlashish(mavzu)
        self.ruknlar(mavzu)
        self.bugungi_sozlar({**mavzu, "sozlar": sozlar[:4]}, 10 ** 6)
        # REV195: ko'rsatuvning yuragi — 🎭 sahnacha (bugungi so'zlar bilan jonli suhbat, savol, takror)
        self.otish("teatr")
        self.vaziyat({**mavzu, "sozlar": sozlar}, eski, 1, zaxira=oldingi)
        self.otish("oyin")
        self.kabu_oyinlari(sozlar, eski, 1)
        self.otish("maqtov")
        if self.vaqt < maqsad * 0.8:
            if self.tartib % 2 == 0:
                self.otish("sayohat")
                self.sayohat()
            else:
                self.mashhur()
        # o'tgan dars sahnachasi — o'sha so'zlar yangi vaziyatda (quruq takror emas)
        if oldingi and self.vaqt < maqsad * 0.85:
            self.vaziyat(oldingi[0], sozlar, 2, zaxira=oldingi[1:])
        if self.vaqt < maqsad * 0.85:
            self.hayotdan() if self.tartib % 2 else self.fakt()
        if self.vaqt < maqsad * 0.9:
            self.gap_tuzish(mavzu)
        sinf, _ = sinf_yosh(self.daraja)
        if eski and self.vaqt < maqsad - 40:
            self.rnd.shuffle(eski)
            self.kabu_oyinlari(eski[:5], sozlar, 2)
        self.yakun(sozlar + eski[:2])
        self.otish("yakun")
        self.xayrlashuv()
        return {"til": self.til, "daraja": self.auditoriya, "manba_daraja": self.daraja, "sana": self.sana.isoformat(), "mavzu": mavzu.get("nom", ""),
                "raqam": self.raqam, "jami": self.jami, "ulush": round(self.u, 2), "ustoz": self.ustoz, "ustoz_ism": self.ism,
                "uzbek": self.uzbek, "erkak": self.erkak, "fon": self.fon, "taxminiy_soniya": round(self.vaqt), "sahnalar": self.sahnalar}


def ssenariy(til, daraja, sana, ob_havo=None, tartib=None):
    return Ssenariy(til, daraja, sana, ob_havo, tartib).tuz()


# ───────────── REV188: HAFTALIK KO'RSATUV (yakshanba) ─────────────
def haftalik(auditoriya, sana, jad, reyting=None, musobaqa=None):
    """Hafta yakuni: bu hafta nimalarni o'rgandik (har til bo'yicha mavzular va so'zlar), reyting (kim nechanchi o'rinda),
    musobaqa natijalari (bo'lsa) va kelasi hafta mavzulari. Boshlovchi — Nilufar opa, Kabular yordam beradi."""
    from collections import Counter
    hafta_kunlari = [sana - dt.timedelta(days=i) for i in range(6, 0, -1)]   # dushanba–shanba
    tillar = Counter(t for d in hafta_kunlari for t in jad.get(d.weekday(), []))
    if not tillar:
        return None
    asosiy = tillar.most_common(1)[0][0]
    s = Ssenariy(asosiy, auditoriya, sana)
    s.uzbek, s.u = True, 0.0   # haftalik — o'zbekcha boshlovchi bilan (hamma tushunsin)
    s.sahna("salom", {"sarlavha": "📅 Hafta yakuni", "pastki": auditoriya})
    s.ayt("I", "Assalomu alaykum! Bugun yakshanba — hafta yakunlari. Bu hafta nimalarni o'rgandik, kim eng faol bo'ldi — hozir bilib olamiz!")
    s.ayt("K2", "Salom! Men ham tayyorman!")
    for til, _ in tillar.most_common():
        mavzular = manba(til).get(s.daraja) or []
        if not mavzular:
            continue
        kunlar = [d for d in hafta_kunlari if til in jad.get(d.weekday(), [])]
        raqamlar = sorted({bugungi_raqam(s.daraja, til, d)[0] for d in kunlar} - {0})
        nomlar = [mavzular[r - 1]["nom"] for r in raqamlar if mavzular[r - 1].get("nom")]
        sozlar = [x for r in raqamlar for x in (mavzular[r - 1].get("sozlar") or [])][:4]
        s.sahna("hafta_til", {"sarlavha": TILLAR[til], "royxat": [f"• {n}" for n in nomlar[:4]] or ["• Takrorlash"]})
        s.ayt("I", f"{TILLAR[til]}dan bu hafta: " + ", ".join(f"«{n}»" for n in nomlar[:3]) + "." if nomlar else f"{TILLAR[til]}dan takrorladik.")
        for x in sozlar:
            s.sahna("hafta_soz", {"emoji": x.get("e", ""), "soz": x["s"], "tarjima": x["t"]})
            s.ayt("T", x["s"], til=til, pauza=0.3)
            s.ayt("I", f"«{x['t']}».")
    if reyting:
        s.sahna("reyting", {"sarlavha": "🏆 Haftaning eng faollari", "royxat": [f"{i}. {r['ism']} — {r['ball']} ball" for i, r in enumerate(reyting[:5], 1)]})
        s.ayt("K2", "Endi eng qiziq joyi — reyting!")
        for i, r in enumerate(reyting[:3], 1):
            s.ayt("I", f"{i}-o'rin — {r['ism']}, {r['ball']} ball. Tabriklaymiz!", pauza=0.4)
        s.ayt("I", "Siz ham har kuni darslarni o'tsangiz, kelasi hafta reytingda bo'lasiz!")
    if musobaqa:
        s.sahna("musobaqa", {"sarlavha": "🥇 Musobaqa natijalari", "royxat": musobaqa[:5]})
        s.ayt("I", "Musobaqa natijalari: " + "; ".join(musobaqa[:3]) + ". G'oliblarni tabriklaymiz!")
    kelasi = []
    for til, _ in tillar.most_common():
        mavzular = manba(til).get(s.daraja) or []
        d = sana + dt.timedelta(days=1)
        r = bugungi_raqam(s.daraja, til, d)[0]
        if mavzular and r:
            kelasi.append(f"{TILLAR[til]}: «{mavzular[min(len(mavzular), r) - 1]['nom']}»")
    if kelasi:
        s.sahna("kelasi", {"sarlavha": "🔜 Kelasi hafta", "royxat": kelasi[:4]})
        s.ayt("I", "Kelasi hafta: " + "; ".join(kelasi[:3]) + ". Kutib qolamiz!")
    s.sahna("xayr", {"sarlavha": "👋"})
    s.ayt("I", "Dam olish kuningiz maroqli o'tsin! Dushanba kuni yangi darslarda ko'rishamiz!")
    s.ayt("K1", G[asosiy]["kabu_xayr"])
    s.ayt("K2", UZ["kabu_xayr"])
    return {"til": asosiy, "daraja": auditoriya, "manba_daraja": s.daraja, "sana": sana.isoformat(), "mavzu": "Hafta yakuni",
            "raqam": 0, "jami": 0, "ulush": 0, "ustoz": s.ustoz, "ustoz_ism": s.ism, "uzbek": True, "erkak": s.erkak,
            "fon": s.fon, "taxminiy_soniya": round(s.vaqt), "sahnalar": s.sahnalar, "haftalik": True}

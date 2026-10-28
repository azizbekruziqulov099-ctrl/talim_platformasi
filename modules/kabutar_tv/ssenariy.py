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
    def sahna(self, nom, karta=None):
        self.sahnalar.append({"nom": nom, "karta": karta, "qatorlar": []})
        return self.sahnalar[-1]

    def ayt(self, kim, matn, til=None, pauza=0.25, sanoq=0):
        matn = re.sub(r"\s+", " ", re.sub("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u20E3]+", "", matn or "")).strip()
        if not matn:
            return
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

    def gap_tuzish(self, mavzu):
        g = G[self.til]
        qisqa = [x for x in (mavzu.get("qisqa") or []) if 2 <= len(re.findall(r"[^\W\d_][\w'’-]*", x["g"])) <= 3]
        if not qisqa:
            return
        self.sahna("gap_bosh", {"sarlavha": "🧩 " + g["gap"]})
        self.ayt("T", g["gap"])
        if self.uzbek and self.u < 0.8:
            self.ayt("K2" if self.u < 0.6 else "I", UZ["gap"])
        for x in qisqa[:3]:
            sozlar = x["g"].rstrip(".!?").split()
            aralash = sozlar[:]
            for _ in range(5):
                self.rnd.shuffle(aralash)
                if aralash != sozlar or len(sozlar) < 2:
                    break
            self.sahna("gap_aralash", {"kartalar": aralash})
            self.ayt("K1", g["tingla"], pauza=0.2, sanoq=3)
            self.sahna("gap_tayyor", {"kartalar": sozlar, "tayyor": True, "tarjima": x.get("t", "") if self.uzbek and self.u < 0.8 else ""})
            self.ayt("T", x["g"], pauza=0.3)
            if x.get("t") and self.izoh_kerak(False):
                self.ayt("I", x["t"])
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
        tanlov = random.Random(f"{self.til}|{self.auditoriya}|{self.sana}").sample(bor[boshi:boshi + 24] or bor, k=min(3, len(bor)))
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
        navbat = (self.tartib + (AUDITORIYALAR.index(self.auditoriya) if self.auditoriya in AUDITORIYALAR else 0)) % 3
        if navbat == 0:
            self.fakt()
        elif navbat == 1:
            self.hayotdan()
        elif self.kichikmi():
            self.qoshiq(mavzu)
        else:
            self.fakt()

    def xayrlashuv(self):
        g = G[self.til]
        self.sahna("xayr", {"sarlavha": "👋"})
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
        self.salomlashish(mavzu)
        self.ruknlar(mavzu)
        self.bugungi_sozlar(mavzu, maqsad * 0.45)
        self.kabu_oyini(mavzu.get("sozlar") or [])
        self.gap_tuzish(mavzu)
        if self.vaqt < maqsad * 0.75:
            self.dialog(mavzu)
        self.takror(maqsad - 25)
        # vaqt qolsa — bugungi gaplar, kechagi va o'tgan mavzular bilan qo'shimcha bloklar (yoshga mos davomiylikka yetguncha)
        oldingi = [mavzular[i] for i in range(self.raqam - 2, max(-1, self.raqam - 12), -1)]
        bloklar = [lambda: self.tingla_takrorla(mavzu)]
        for m in oldingi:
            bloklar += [lambda m=m: self.kabu_oyini(m.get("sozlar") or []), lambda m=m: self.tingla_takrorla(m, 3), lambda m=m: self.gap_tuzish(m)]
        for blok in bloklar:
            if self.vaqt >= maqsad - 25:
                break
            blok()
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

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

DATA = os.path.join(os.path.dirname(__file__), "data")
DARAJALAR = ["2-3 yosh", "4-5 yosh", "6-7 yosh"] + [f"{i}-sinf" for i in range(1, 12)]
TILLAR = {"en": "Ingliz tili", "de": "Nemis tili", "fr": "Fransuz tili", "es": "Ispan tili", "ru": "Rus tili"}
USTOZ = {"en": ("emily", "Emili opa", "Miss Emily", False), "de": ("lukas", "Lukas aka", "Herr Lukas", True),
         "fr": ("camille", "Kamilla opa", "Madame Camille", False), "es": ("carlos", "Karlos aka", "Señor Carlos", True),
         "ru": ("anna", "Anna opa", "Анна", False)}
DAVOMIYLIK = {"2-3 yosh": 300, "4-5 yosh": 420, "6-7 yosh": 480}   # soniya; sinflar — pastda

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
          kabu_salom="Salom! Men o'zbek Kabuman!", dedi="{u} shunday dedi. O'zbekchada bunday tushunamiz:", qisqa="Ya'ni:",
          soz="{u} aytgan so'z — «{t}» degani.", soz_q="«{t}» degani.", takrorla="Siz ham takrorlang!",
          oyin="Endi o'yin! Rasmga qarang. Bu nima? O'ylang!", gap="Endi gap tuzamiz. So'zlarni to'g'ri tartibda qo'yamiz.",
          dialog="Endi kichik suhbatni tinglaymiz.", takror="Endi o'tgan darslarni eslaymiz.", oylang="Uch, ikki, bir!",
          xayr="Barakalla, bolajonlar! Ertaga yana uchrashamiz!", kabu_xayr="Xayr!", mavzu="Bugungi mavzu — «{nom}».")


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


class Ssenariy:
    def __init__(self, til, daraja, sana):
        self.til, self.daraja, self.sana = til, daraja, sana
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
                self.ayt("I", self.uz_gap("soz", s=s["s"], t=s["t"]) if self.u < 0.3 else UZ["soz_q"].format(t=s["t"]))
            misol = next((x for x in gaplar if x["g"].lower().strip(" .!?") != s["s"].lower().strip(" .!?") and re.search(r"(?<!\w)" + re.escape(s["s"].split()[-1]) + r"(?!\w)", x["g"], re.I)), None)
            if misol:
                self.ayt("T", misol["g"], pauza=0.4)
                if misol.get("t") and self.izoh_kerak(False):
                    self.ayt("I", (UZ["qisqa"] + " " if self.u >= 0.3 else "") + misol["t"])
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
        maqsad = davomiylik(self.daraja) - 20   # kirish/chiqish videosi
        self.salomlashish(mavzu)
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
        return {"til": self.til, "daraja": self.daraja, "sana": self.sana.isoformat(), "mavzu": mavzu.get("nom", ""),
                "raqam": self.raqam, "jami": self.jami, "ulush": round(self.u, 2), "ustoz": self.ustoz, "ustoz_ism": self.ism,
                "uzbek": self.uzbek, "erkak": self.erkak, "fon": self.fon, "taxminiy_soniya": round(self.vaqt), "sahnalar": self.sahnalar}


def ssenariy(til, daraja, sana):
    return Ssenariy(til, daraja, sana).tuz()

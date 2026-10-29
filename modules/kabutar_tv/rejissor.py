"""REV185: KABUTAR TV — REJISSOR.

Ssenariydan video yig'adi: har qatorga ovoz (edge-tts, saytdagi ovozlar), studiya foni, ustozlar (og'zi ochiq/yopiq),
ikki Kabu, markazda karta (emoji + so'z + tarjima, gap kartalari, sanoq 3-2-1) va pastda karaoke yozuv — aytilayotgan
so'z yonadi, har ishtirokchi o'z rangida. Boshiga kirish, oxiriga chiqish videosi qo'yiladi. 1280×720, 15 kadr/s.
"""
import asyncio
import hashlib
import io
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import wave
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont, ImageOps

DATA = os.path.join(os.path.dirname(__file__), "data")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H, FPS, SR = 1280, 720, 15, 24000
OVOZ = {"uz": {"qiz": "uz-UZ-MadinaNeural", "ogil": "uz-UZ-SardorNeural"},
        "en": {"qiz": "en-US-JennyNeural", "ogil": "en-US-GuyNeural"}, "ru": {"qiz": "ru-RU-SvetlanaNeural", "ogil": "ru-RU-DmitryNeural"},
        "de": {"qiz": "de-DE-KatjaNeural", "ogil": "de-DE-ConradNeural"}, "fr": {"qiz": "fr-FR-DeniseNeural", "ogil": "fr-FR-HenriNeural"},
        "es": {"qiz": "es-ES-ElviraNeural", "ogil": "es-ES-AlvaroNeural"}}
RANG = {"T": (29, 111, 216), "I": (15, 138, 95), "K1": (124, 77, 255), "K2": (232, 120, 20)}
BAYROQ = {"en": "EN", "de": "DE", "fr": "FR", "es": "ES", "ru": "RU", "uz": "UZ"}
TIL_NOMI = {"en": "Ingliz tili", "de": "Nemis tili", "fr": "Fransuz tili", "es": "Ispan tili", "ru": "Rus tili"}


def _font(size, bold=True):
    for p in (os.path.join(ROOT, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


F = {k: _font(v) for k, v in {"katta": 64, "orta": 40, "kichik": 28, "yozuv": 30, "ism": 22, "sanoq": 84, "sarlavha": 46}.items()}
F["tarjima"] = _font(36, bold=False)


@lru_cache(maxsize=64)
def rasm(nom):
    return Image.open(os.path.join(DATA, "rasm", nom)).convert("RGBA")


@lru_cache(maxsize=512)
def emoji_rasm(e, size=170):
    nom = "-".join(f"{ord(c):x}" for c in e if ord(c) != 0xFE0F)
    p = os.path.join(DATA, "rasm", "emoji", nom + ".webp")
    if not os.path.exists(p):
        p = os.path.join(DATA, "rasm", "emoji", "-".join(f"{ord(c):x}" for c in e) + ".webp")
        if not os.path.exists(p):
            return None
    im = Image.open(p).convert("RGBA")
    k = size / max(im.size)
    return im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)


# ───────────── OVOZ ─────────────
def ovoz_tanla(kim, til, ssen):
    if kim == "T":
        return OVOZ[til]["ogil" if ssen["erkak"] else "qiz"], "+0%", "+0Hz"
    if kim == "I":
        return OVOZ["uz"]["qiz"], "+0%", "+0Hz"
    if kim == "K1":
        return OVOZ.get(til, OVOZ["en"])["ogil"], "+6%", "+28Hz"
    if til != "uz" and til in OVOZ:   # REV196: Kabu teatrida ikkinchi Kabu ham o'rganilayotgan tilda (boshqa ovoz)
        return OVOZ[til]["qiz"], "+6%", "+22Hz"
    return OVOZ["uz"]["ogil"], "+6%", "+28Hz"


async def _edge(matn, voice, rate, pitch):
    import edge_tts
    audio, chegaralar = bytearray(), []
    com = edge_tts.Communicate(matn, voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    async for ch in com.stream():
        if ch["type"] == "audio":
            audio.extend(ch["data"])
        elif ch["type"] == "WordBoundary":
            chegaralar.append((ch["offset"] / 1e7, ch["text"]))
    return bytes(audio), chegaralar


_ZAXIRA_OVOZ = {   # REV211: asosiy ovoz javob bermasa — shu tildagi boshqa ovoz
    "ru-RU": ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"], "en-US": ["en-US-JennyNeural", "en-US-GuyNeural"],
    "en-GB": ["en-GB-SoniaNeural", "en-US-JennyNeural"], "de-DE": ["de-DE-KatjaNeural", "de-DE-ConradNeural"],
    "fr-FR": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural"], "es-ES": ["es-ES-ElviraNeural", "es-ES-AlvaroNeural"],
    "uz-UZ": ["uz-UZ-MadinaNeural", "uz-UZ-SardorNeural"],
}


def _jimlik(matn):
    """Ovoz umuman olinmasa — gap uzunligiga mos sukunat (subtitr ko'rinadi, ko'rsatuv to'xtamaydi)."""
    son = max(0.6, min(6.0, len(matn) / 13.0))
    return bytes(int(SR * son) * 2), []


def edge_tts_ovoz(matn, voice, rate, pitch, kesh):
    """→ (pcm s16 mono 24 kHz bytes, [(soniya, so'z)]). Kesh — bir xil gap qayta so'ralmaydi.
    REV211: bo'sh/belgili gap — sukunat; xizmat band bo'lsa — kutib qayta urinadi, keyin boshqa ovoz, oxiri — sukunat
    (bitta gap tufayli butun ko'rsatuv «Ovoz olinmadi» bo'lib yiqilmaydi)."""
    import time as _t
    toza = re.sub(r"[«»\"'“”„…\.\s]+", " ", matn or "").strip()
    if not re.search(r"\w", toza):
        return _jimlik(matn or " ")
    kalit = hashlib.sha1(f"{voice}|{rate}|{pitch}|{matn}".encode()).hexdigest()
    p = os.path.join(kesh, kalit)
    if os.path.exists(p + ".pcm"):
        import json
        return open(p + ".pcm", "rb").read(), [tuple(x) for x in json.load(open(p + ".json"))]
    mp3, cheg = None, []
    locale = "-".join(voice.split("-")[:2])
    urinishlar = [(voice, rate, pitch, 0), (voice, rate, pitch, 1.5), (voice, rate, pitch, 4), (voice, "+0%", "+0Hz", 2)]
    urinishlar += [(v, rate, "+0Hz", 1) for v in _ZAXIRA_OVOZ.get(locale, []) if v != voice]
    for v, r, pt, kut in urinishlar:
        if kut:
            _t.sleep(kut)
        try:
            mp3, cheg = asyncio.run(_edge(matn, v, r, pt))
            if mp3:
                break
        except Exception:
            mp3 = None
    if not mp3:
        print(f"[kabutar_tv] ovoz olinmadi (sukunat qo'yildi): {matn[:40]}", flush=True)
        return _jimlik(matn)
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                         input=mp3, capture_output=True, check=True).stdout
    import json
    open(p + ".pcm", "wb").write(pcm)
    json.dump(cheg, open(p + ".json", "w"))
    return pcm, cheg


# ───────────── KADR ─────────────
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u20E3]+")


def _matn_ol(d, xy, text, font, fill, anchor="mm", stroke=0):
    text = EMOJI_RE.sub("", str(text)).strip()
    d.text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(255, 255, 255))


def _qatorla(text, font, kenglik, d):
    sozlar, qatorlar, joriy = text.split(), [], ""
    for s in sozlar:
        sinov = (joriy + " " + s).strip()
        if d.textlength(sinov, font=font) <= kenglik or not joriy:
            joriy = sinov
        else:
            qatorlar.append(joriy)
            joriy = s
    if joriy:
        qatorlar.append(joriy)
    return qatorlar


class Sahna:
    def __init__(self, ssen):
        self.s = ssen
        self.fon = Image.open(os.path.join(DATA, "rasm", "fon", ssen["fon"] + ".jpg")).convert("RGBA")
        self.ustoz = {o: rasm(f"ustoz/{ssen['ustoz']}_{o}.png") for o in ("yopiq", "ochiq")}
        self.nilufar = {o: rasm(f"ustoz/nilufar_{o}.png") for o in ("yopiq", "ochiq")}
        self.kabu = {k: rasm(f"kabu_{k}.png") for k in ("gapiradi", "tingla", "salom", "hurra")}
        self.logo = rasm("logo.png")
        self._kesh = {}

    def _kabu(self, kim, gapir, faza, sahna_nom):
        holat = "gapiradi" if gapir else ("hurra" if sahna_nom in ("javob", "gap_tayyor") else "salom" if sahna_nom in ("salom", "xayr") else "tingla")
        im = self.kabu[holat]
        if kim == "K2":
            im = ImageOps.mirror(im)
        im = im.copy()
        d = ImageDraw.Draw(im)
        til = self.s["til"] if kim == "K1" else "uz"
        cx, cy, r = im.width - 34 if kim == "K1" else 34, 30, 24
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=RANG[kim], outline=(255, 255, 255), width=3)
        _matn_ol(d, (cx, cy), BAYROQ[til], _font(18), (255, 255, 255))
        return im, (-6 if gapir and faza else 0)

    @staticmethod
    @lru_cache(maxsize=2)
    def oyin_fon():
        """REV193: Kabu o'yinlari uchun alohida yorqin «o'yin studiyasi» foni (rasm kerak emas — chiziladi)."""
        im = Image.new("RGBA", (W, H), (60, 30, 120, 255))
        d = ImageDraw.Draw(im)
        for i in range(0, H, 4):   # binafsha → moviy gradient
            t = i / H
            d.rectangle((0, i, W, i + 4), fill=(int(88 - 50 * t), int(40 + 60 * t), int(170 + 40 * t), 255))
        import random as _r
        rr = _r.Random(7)
        for _ in range(70):   # yulduzchalar
            x, y, r = rr.randint(0, W), rr.randint(0, 560), rr.choice((2, 3, 4))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, rr.randint(90, 200)))
        nur = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # shaffof qatlam — chiroq nurlari va pol
        dn = ImageDraw.Draw(nur)
        for i, rang in enumerate(((255, 210, 77), (255, 120, 170), (90, 220, 200))):   # sahna chiroqlari
            cx = 200 + i * 440
            dn.polygon([(cx - 30, 0), (cx + 30, 0), (cx + 170, 600), (cx - 170, 600)], fill=(*rang, 34))
        dn.ellipse((120, 520, 1160, 700), fill=(255, 255, 255, 38))   # sahna poli
        im.alpha_composite(nur)
        return im

    def karta_qatlam(self, sahna):
        """Karta alohida qatlam — paydo bo'lish (pop) animatsiyasi uchun."""
        kal = ("karta", id(sahna))
        if kal not in self._kesh:
            q = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            self._karta(q, sahna.get("karta") or {}, oyin=sahna.get("joy") == "oyin")
            self._kesh[kal] = q
        return self._kesh[kal]

    def asos(self, sahna, gapiruvchi, faza, karta=True):
        """Fon + personajlar. gapiruvchi: T/I/K1/K2/None; faza: og'iz ochiq (1) yoki yopiq (0)."""
        kalit = (id(sahna), gapiruvchi, faza, karta)
        if kalit in self._kesh:
            return self._kesh[kalit].copy()
        if sahna.get("joy") == "oyin":   # REV193: Kabular alohida — o'yin studiyasida, katta, ustozlarsiz
            im = self.oyin_fon().copy()
            for kim, x in (("K1", 180), ("K2", 1100)):
                if kim == "K2" and not self.s["uzbek"]:
                    continue
                k, dy = self._kabu(kim, gapiruvchi == kim, faza, sahna["nom"])
                k = k.resize((round(k.width * 1.5), round(k.height * 1.5)), Image.LANCZOS)
                im.alpha_composite(k, (x - k.width // 2, 600 - k.height + dy * 2))
            if karta:
                im.alpha_composite(self.karta_qatlam(sahna))
            im.alpha_composite(self.logo, (W - self.logo.width - 18, 12))
            if len(self._kesh) > 400:
                self._kesh.clear()
            self._kesh[kalit] = im.copy()
            return im
        im = self.fon.copy()
        oyoq = 690
        # ustoz (chapda)
        u = self.ustoz["ochiq" if gapiruvchi == "T" and faza else "yopiq"]
        im.alpha_composite(u, (250 - u.width // 2, oyoq - u.height))
        if self.s["uzbek"]:
            n = self.nilufar["ochiq" if gapiruvchi == "I" and faza else "yopiq"]
            im.alpha_composite(n, (1030 - n.width // 2, oyoq - n.height))
        k1, dy = self._kabu("K1", gapiruvchi == "K1", faza, sahna["nom"])
        im.alpha_composite(k1, (460 - k1.width // 2, 602 - k1.height + dy))
        if self.s["uzbek"]:
            k2, dy = self._kabu("K2", gapiruvchi == "K2", faza, sahna["nom"])
            im.alpha_composite(k2, (820 - k2.width // 2, 602 - k2.height + dy))
        if karta:
            im.alpha_composite(self.karta_qatlam(sahna))
        im.alpha_composite(self.logo, (W - self.logo.width - 18, 12))
        d = ImageDraw.Draw(im)
        sar = f"KABUTAR TV · {'Hafta yakuni' if self.s.get('haftalik') else TIL_NOMI[self.s['til']]} · {self.s['daraja']}"
        d.rounded_rectangle((16, 14, 30 + d.textlength(sar, font=F["ism"]), 50), 12, fill=(255, 255, 255, 220))
        _matn_ol(d, (24, 32), sar, F["ism"], (29, 60, 120), anchor="lm")
        if len(self._kesh) > 400:
            self._kesh.clear()
        self._kesh[kalit] = im.copy()
        return im

    def _karta(self, im, k, oyin=False):
        if not k:
            return
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = (355, 60, 925, 420) if oyin else (330, 66, 950, 380)
        if k.get("variantlar"):   # REV193: «Rasmni top» — 3 ta rasm, to'g'risi ochiladi
            d.rounded_rectangle((x0, y0, x1, y1), 32, fill=(255, 255, 255, 240), outline=(255, 200, 60), width=6)
            if k.get("savol"):
                _matn_ol(d, ((x0 + x1) // 2, y0 + 42), k["savol"], F["orta"], (90, 40, 160))
            for i, e in enumerate(k["variantlar"]):
                cx = x0 + 105 + i * 180
                ok = k.get("ochildi") and i == k.get("togri")
                xira = k.get("ochildi") and i != k.get("togri")
                d.rounded_rectangle((cx - 82, y0 + 90, cx + 82, y0 + 290), 26, fill=(220, 255, 230, 255) if ok else (246, 243, 255, 255),
                                    outline=(30, 170, 90) if ok else (180, 170, 230), width=8 if ok else 3)
                er = emoji_rasm(e, 120)
                if er:
                    if xira:
                        er = er.copy()
                        er.putalpha(er.getchannel("A").point(lambda a: a // 3))
                    im.alpha_composite(er, (cx - er.width // 2, y0 + 125))
                _matn_ol(d, (cx, y0 + 318), "ABC"[i], F["orta"], (90, 40, 160))
            return
        if k.get("matn_variant"):   # REV195: «Kim aytdi?» — matnli tanlov, to'g'risi ochiladi
            d.rounded_rectangle((x0, y0, x1, y1), 32, fill=(255, 255, 255, 240), outline=(255, 200, 60), width=6)
            for i, q in enumerate(_qatorla(k.get("savol", ""), F["kichik"], x1 - x0 - 50, d)[:3]):
                _matn_ol(d, ((x0 + x1) // 2, y0 + 38 + i * 36), q, F["kichik"], (90, 40, 160))
            var = k["matn_variant"][:3]
            for i, v in enumerate(var):
                yy = y0 + 150 + i * 62
                ok = k.get("ochildi") and i == k.get("togri")
                xira = k.get("ochildi") and i != k.get("togri")
                d.rounded_rectangle((x0 + 60, yy - 26, x1 - 60, yy + 26), 18, fill=(220, 255, 230) if ok else (246, 243, 255),
                                    outline=(30, 170, 90) if ok else (180, 170, 230), width=6 if ok else 2)
                _matn_ol(d, ((x0 + x1) // 2, yy), f"{'ABC'[i]}) {v}", F["orta"], (160, 160, 175) if xira else (29, 60, 120))
            return
        if k.get("sanash"):   # REV193: sanash o'yini — rasm birma-bir paydo bo'ladi
            d.rounded_rectangle((x0, y0, x1, y1), 32, fill=(255, 255, 255, 240), outline=(90, 220, 200), width=6)
            n = int(k.get("k") or 0)
            er = emoji_rasm(k["sanash"], 96 if k.get("n", 5) <= 5 else 78)
            if er:
                qator = min(5, max(1, k.get("n", 5)))
                for i in range(n):
                    r, c = divmod(i, qator)
                    cx = (x0 + x1) // 2 - (qator - 1) * 55 + c * 110
                    im.alpha_composite(er, (cx - er.width // 2, y0 + 50 + r * 110))
            _matn_ol(d, ((x0 + x1) // 2, y1 - 55), str(n) if n else "?", _font(86), (90, 40, 160))
            return
        if k.get("panjara"):   # REV193: bugun o'rganganlarimiz — rasm + so'z panjarasi
            d.rounded_rectangle((x0, y0, x1, y1), 32, fill=(255, 255, 255, 240), outline=(255, 200, 60), width=6)
            if k.get("sarlavha"):
                _matn_ol(d, ((x0 + x1) // 2, y0 + 40), k["sarlavha"], F["orta"], (90, 40, 160))
            for i, (e, w) in enumerate(k["panjara"][:6]):
                r, c = divmod(i, 3)
                cx, cy = x0 + 100 + c * 185, y0 + 135 + r * 140
                er = emoji_rasm(e, 76) if e else None
                if er:
                    im.alpha_composite(er, (cx - er.width // 2, cy - 50))
                _matn_ol(d, (cx, cy + 48), w, F["kichik"], (29, 111, 216))
            return
        if k.get("kartalar"):
            y1 = 330
        d.rounded_rectangle((x0, y0, x1, y1), 28, fill=(255, 255, 255, 236), outline=(29, 111, 216), width=4)
        cx = (x0 + x1) // 2
        if k.get("royxat"):   # REV188: ro'yxat (haftalik: mavzular, reyting, kelasi hafta)
            if k.get("sarlavha"):
                _matn_ol(d, (cx, y0 + 40), k["sarlavha"], F["orta"], (29, 111, 216))
            y = y0 + 95
            for q in k["royxat"][:5]:
                for qq in _qatorla(q, F["kichik"], x1 - x0 - 60, d)[:1]:
                    _matn_ol(d, (x0 + 30, y), qq, F["kichik"], (30, 40, 60), anchor="lm")
                y += 44
            return
        if k.get("kartalar"):
            chiplar = k["kartalar"]
            kenglik = [d.textlength(c, font=F["orta"]) + 40 for c in chiplar]
            jami = sum(kenglik) + 16 * (len(chiplar) - 1)
            x = cx - jami / 2
            rang = (15, 138, 95) if k.get("tayyor") else (124, 77, 255)
            for c, w in zip(chiplar, kenglik):
                d.rounded_rectangle((x, 150, x + w, 220), 16, fill=rang)
                _matn_ol(d, (x + w / 2, 185), c, F["orta"], (255, 255, 255))
                x += w + 16
            if k.get("tarjima"):
                _matn_ol(d, (cx, 275), k["tarjima"], F["tarjima"], (15, 138, 95))
            return
        if k.get("gap"):
            qatorlar = _qatorla(k["gap"], F["orta"], x1 - x0 - 60, d)[:4]
            y = 215 - 26 * len(qatorlar)
            for q in qatorlar:
                _matn_ol(d, (cx, y), q, F["orta"], (29, 111, 216))
                y += 54
            if k.get("tarjima"):
                for q in _qatorla(k["tarjima"], F["tarjima"], x1 - x0 - 60, d)[:2]:
                    _matn_ol(d, (cx, y + 10), q, F["tarjima"], (15, 138, 95))
                    y += 44
            return
        if k.get("emoji") or k.get("soz"):
            e = emoji_rasm(k["emoji"], 140) if k.get("emoji") else None
            y = 84
            if e:
                im.alpha_composite(e, (cx - e.width // 2, y))
                y += e.height + 10
            else:
                y = 160
            soz = k.get("soz", "")
            f = F["katta"] if d.textlength(soz, font=F["katta"]) < x1 - x0 - 60 else F["orta"]
            _matn_ol(d, (cx, y + 36), soz, f, (29, 111, 216) if soz != "?" else (232, 120, 20))
            if k.get("tarjima"):
                _matn_ol(d, (cx, y + 92), k["tarjima"], F["tarjima"], (15, 138, 95))
            return
        if k.get("sarlavha"):
            m = re.match(r"^\s*([^\w\s«\"'(]+)\s*", k["sarlavha"])   # REV193: sarlavhadagi emoji — rasm bo'lib chiqadi
            em = emoji_rasm(m.group(1).strip(), 96) if m else None
            y0s = 150
            if em:
                im.alpha_composite(em, (cx - em.width // 2, y0 + 20))
                y0s = y0 + 20 + em.height + 40
            for i, q in enumerate(_qatorla(k["sarlavha"], F["sarlavha"], x1 - x0 - 60, d)[:3]):
                _matn_ol(d, (cx, y0s + 20 + i * 60), q, F["sarlavha"], (29, 111, 216) if not oyin else (90, 40, 160))
            if k.get("pastki"):
                _matn_ol(d, (cx, 330), k["pastki"], F["tarjima"], (15, 138, 95))

    def yozuv(self, im, q, faol_soz, ism):
        """Pastki karaoke yozuv: gapiruvchi ismi + gap, aytilayotgan so'z sariq fonda."""
        d = ImageDraw.Draw(im)
        d.rectangle((0, 600, W, H), fill=(13, 20, 36, 205))
        rang = RANG[q["kim"]]
        d.rounded_rectangle((20, 612, 40 + d.textlength(ism, font=F["ism"]), 644), 10, fill=rang)
        _matn_ol(d, (30, 628), ism, F["ism"], (255, 255, 255), anchor="lm")
        sozlar = EMOJI_RE.sub("", q["matn"]).split()
        qatorlar, joriy, kenglik = [], [], 0
        bosh = 20
        for i, s in enumerate(sozlar):
            w = d.textlength(s + " ", font=F["yozuv"])
            if kenglik + w > W - 40 and joriy:
                qatorlar.append(joriy)
                joriy, kenglik = [], 0
            joriy.append((i, s, w))
            kenglik += w
        if joriy:
            qatorlar.append(joriy)
        # faol so'z qaysi qatorda — shu qator va keyingisi ko'rinadi
        ix = next((n for n, qq in enumerate(qatorlar) if any(i == faol_soz for i, _, _ in qq)), 0)
        for n, qq in enumerate(qatorlar[ix:ix + 2]):
            x, y = bosh, 668 + n * 36 - (0 if len(qatorlar[ix:ix + 2]) == 1 else 12)
            for i, s, w in qq:
                if i == faol_soz:
                    d.rounded_rectangle((x - 4, y - 18, x + w - 6, y + 18), 8, fill=(255, 216, 77))
                    _matn_ol(d, (x, y), s, F["yozuv"], (20, 24, 40), anchor="lm")
                else:
                    _matn_ol(d, (x, y), s, F["yozuv"], (255, 255, 255) if i > faol_soz else (190, 205, 230), anchor="lm")
                x += w
        return im


KAMERA_X = {"T": 250, "I": 1030, "K1": 460, "K2": 820}


def yaqin(im, kim):
    """REV193: kamera — gapirayotgan personajga yaqinlashadi (o'rta plan)."""
    cx = KAMERA_X.get(kim, W // 2)
    w, h = 880, 495
    x = max(0, min(W - w, cx - w // 2))
    y = 150
    return im.crop((x, y, x + w, y + h)).resize((W, H), Image.BILINEAR)


def konfetti(im, t):
    """REV193: to'g'ri javobda konfetti (t — soniya, 0..1.2)."""
    import random as _r
    rr = _r.Random(11)
    d = ImageDraw.Draw(im)
    for _ in range(90):
        x0, v, rang = rr.randint(0, W), rr.uniform(250, 520), rr.choice(((255, 90, 90), (255, 210, 60), (80, 200, 120), (80, 160, 255), (200, 110, 255)))
        y = -20 + v * t + rr.randint(-80, 0)
        if 0 <= y <= 600:
            x = x0 + 30 * __import__("math").sin(t * 6 + x0)
            d.rectangle((x, y, x + 9, y + 14), fill=(*rang, 255))
    return im


def _ton(chastota, sek, kuch=5000):
    import math
    n = int(SR * sek)
    return b"".join(struct.pack("<h", int(kuch * math.sin(2 * math.pi * chastota * i / SR) * (1 - i / n))) for i in range(n))


TIK = None
DING = None


def tovush(nom):
    """REV193: oddiy ovoz effektlari (sanoq «tik», to'g'ri javob «ding»)."""
    global TIK, DING
    if nom == "tik":
        TIK = TIK or (_ton(1200, 0.06, 3500) + b"\x00\x00" * int(SR * 0.94))
        return TIK
    DING = DING or (_ton(880, 0.15) + _ton(1320, 0.35))
    return DING


def _soz_vaqtlari(q, cheg, dav):
    """Har so'zning boshlanish vaqti. edge-tts chegaralari bo'lsa — ulardan, bo'lmasa harf soniga qarab."""
    sozlar = q["matn"].split()
    if not sozlar:
        return []
    if cheg:
        vaqt, j = [], 0
        for s in sozlar:
            toza = re.sub(r"[^\w]", "", s.lower())
            while j < len(cheg) and toza and re.sub(r"[^\w]", "", str(cheg[j][1]).lower()) not in toza and toza not in re.sub(r"[^\w]", "", str(cheg[j][1]).lower()):
                j += 1
            if j < len(cheg):
                vaqt.append(cheg[j][0])
                j += 1
            else:
                vaqt.append(vaqt[-1] + 0.3 if vaqt else 0)
        return vaqt
    uz = [len(s) + 2 for s in sozlar]
    jami = sum(uz)
    t, out = 0.0, []
    for u in uz:
        out.append(t)
        t += dav * u / jami
    return out


def yasash(ssen, chiqish, tts=None, ish_papka=None, kesh=None, kirish_chiqish=True, log=print):
    """Ssenariy → mp4. tts(matn, voice, rate, pitch, kesh) → (pcm, chegaralar). Qaytaradi: davomiylik (soniya)."""
    tts = tts or edge_tts_ovoz
    ish = ish_papka or tempfile.mkdtemp(prefix="kabutar_tv_")
    kesh = kesh or os.path.join(tempfile.gettempdir(), "kabutar_tv_ovoz")
    os.makedirs(kesh, exist_ok=True)
    os.makedirs(os.path.join(ish, "k"), exist_ok=True)
    try:
        asosiy = _jonli_yasash(ssen, chiqish, tts, kesh, kirish_chiqish, ish, log)   # REV194: jonli rejissor
        os.makedirs(os.path.dirname(chiqish) or ".", exist_ok=True)
        if kirish_chiqish:
            och = OCHILISH_YOSH.get(ssen.get("daraja"))   # REV208: bog'cha yoshlariga — o'z ochilish/yopilishi
            k1 = os.path.join(STD, "ochilish", f"{och}_ochilish.mp4") if och else ""
            k2 = os.path.join(STD, "ochilish", f"{och}_yopilish.mp4") if och else ""
            qismlar = [k1 if k1 and os.path.exists(k1) else os.path.join(DATA, "video", "kirish_12s.mp4"), asosiy,
                       k2 if k2 and os.path.exists(k2) else os.path.join(DATA, "video", "chiqish_8s.mp4")]
            ro2 = os.path.join(ish, "qism.txt")
            with open(ro2, "w") as f:
                for p in qismlar:
                    f.write(f"file '{p}'\n")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", ro2,
                            "-vf", f"fps={FPS},scale={W}:{H},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "26", "-c:a", "aac", "-b:a", "80k", "-ar", str(SR), "-ac", "1", "-movflags", "+faststart", chiqish], check=True)
        else:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", asosiy, "-c", "copy", "-movflags", "+faststart", chiqish], check=True)
        dav = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", chiqish],
                                   capture_output=True, text=True).stdout.strip() or 0)
        return dav
    finally:
        if not ish_papka:
            shutil.rmtree(ish, ignore_errors=True)


# ═════════════ REV194: JONLI REJISSOR — har kadr chiziladi (15 kadr/s) ═════════════
# Ustozlar: og'zi OVOZGA mos ochiladi (har kadrdagi ovoz balandligi bo'yicha), sekin «nafas oladi» (yengil tebranish),
# Nilufar opa ko'z qisadi (boshqa ustozlarga ko'z yumuq rasm qo'shilsa — ular ham). Kabular — saytdagi jonli robot:
# uchib turadi, qanot qoqadi, gapirganda og'zi ovozga mos sakraydi. Kadrlar diskka yozilmaydi — to'g'ridan ffmpeg'ga.
import math as _m

from . import kabu_jonli
from . import rig
from . import yuz as yuzmod
from . import labsinx

_Q = {"X": 0, "A": 0, "B": 1, "C": 1, "G": 1, "H": 1, "D": 2, "E": 2, "F": 2}

# ───────── REV208: STUDIYA PAKETI — 4 studiya × 4 rakurs, ekranga karta, o'tishlar, musiqa, ovoz effektlari ─────────
STD = os.path.join(DATA, "studiya")
STUDIYA_YOSH = {"2-3 yosh": "bog", "4-5 yosh": "ijod", "6-7 yosh": "orbita"}   # maktab guruhlari — «efir»
OTISH_YOSH = {"bog": ["05_bulut", "01_qanot"], "ijod": ["04_rang_kataklari", "06_shakllar"], "orbita": ["03_orbita", "01_qanot"],
              "efir": ["01_qanot", "07_parda", "02_kitob"], "oyin": ["08_kabutar"]}
OCHILISH_YOSH = {"2-3 yosh": "01_kichkintoy_2_3", "4-5 yosh": "02_kashfiyot_4_5", "6-7 yosh": "03_sarguzasht_6_7"}
MUSIQA_YOSH = {"bog": "01_kichkintoy_2_3_suhbat_foni", "ijod": "02_kashfiyot_4_5_suhbat_foni", "orbita": "03_sarguzasht_6_7_suhbat_foni",
               "efir": "04_tinch_mashq_suhbat_foni"}


def studiya_nomi(ssen):
    nom = STUDIYA_YOSH.get(ssen.get("daraja"), "efir")
    return nom if os.path.exists(os.path.join(STD, f"{nom}_old.jpg")) else None


@lru_cache(maxsize=1)
def ekranlar():
    try:
        with open(os.path.join(STD, "ekranlar.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@lru_cache(maxsize=16)
def otish_kadrlari(nom):
    p = os.path.join(STD, "otish", nom)
    if not os.path.isdir(p):
        return []
    return [Image.open(os.path.join(p, f)).convert("RGBA") for f in sorted(os.listdir(p)) if f.endswith(".png")]


@lru_cache(maxsize=16)
def audio_pcm(yol):
    """mp3/wav → mono s16 PCM (SR) — ovoz effekti va fon musiqasi uchun."""
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-i", yol, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True)
        return r.stdout
    except Exception:
        return b""


def sfx(nom):
    return audio_pcm(os.path.join(STD, "sfx", nom + ".mp3"))


def musiqa_qosh(pcm, nom, kuch=0.16):
    """Butun ko'rsatuv ostiga past ovozli fon musiqasi (takrorlanadi). Ovoz baland joyda musiqa yana pasayadi."""
    m = audio_pcm(os.path.join(STD, "musiqa", nom + ".mp3"))
    if not m or not pcm:
        return pcm
    import numpy as np
    a = np.frombuffer(bytes(pcm), dtype=np.int16).astype(np.float32)
    b = np.frombuffer(m, dtype=np.int16).astype(np.float32)
    b = np.tile(b, int(np.ceil(len(a) / max(1, len(b)))) + 1)[:len(a)]
    # ovoz bor joyda musiqani yana 50 % pasaytirish (yumshoq «ducking»)
    oyna = int(SR * 0.3)
    en = np.abs(a)
    if len(en) > oyna:
        en = np.convolve(en, np.ones(oyna) / oyna, mode="same")
    duck = 1.0 - 0.5 * np.clip(en / 2500.0, 0, 1)
    out = np.clip(a + b * kuch * duck, -32768, 32767).astype(np.int16)
    return bytearray(out.tobytes())


_OXIRGI = {}


def _yuz_kadr(kalit, poza, gapir, daraja, vis, koz, bal, aniq):
    """Variant rasmlar bo'lsa — rassom chizgan og'iz/ko'z; bo'lmasa — dastur chizadi (aniq: og'iz shakli Rhubarb'dan).
    Og'iz shakli almashganda bitta oraliq kadr — ikki shaklning yarmi (sakrash sezilmaydi)."""
    if yuzmod.variant_bormi(kalit, poza):
        sh = vis if gapir else "X"
        kal = (kalit, poza, bal)
        old = _OXIRGI.get(kal)
        _OXIRGI[kal] = sh
        yangi = yuzmod.holat_v(kalit, poza, sh, koz, bal)
        if old and old != sh and yuzmod.OGIZ_VARIANT.get(old) != yuzmod.OGIZ_VARIANT.get(sh):
            eski = yuzmod.holat_v(kalit, poza, old, koz, bal)
            if eski is not None and eski.size == yangi.size:
                return Image.blend(eski, yangi, 0.5)
        return yangi
    q = (_Q.get(vis, 1) if aniq else yuzmod.og_iz_daraja(daraja)) if gapir else 0
    return yuzmod.holat(kalit, poza, q, koz, bal)


def _kabu(h, t, holat, daraja, faza, oyna):
    """Jonli Kabu; serverda cairo bo'lmasa — oldingi rasmli Kabu (video baribir chiqadi)."""
    try:
        return kabu_jonli.kadr(h, t, holat, daraja, faza, oyna)
    except Exception:
        nom = {"gapir": "gapiradi", "salom": "salom", "hurra": "hurra"}.get(holat, "tingla")
        im = rasm(f"kabu_{nom}.png")
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        return ImageOps.mirror(im) if oyna else im


def _darajalar(pcm, n):
    """Har kadr uchun ovoz balandligi 0..1 (RMS), gap bo'yicha normallangan."""
    if not pcm or n <= 0:
        return [0.0] * max(0, n)
    a = memoryview(pcm).cast("h")
    q = max(1, len(a) // n)
    out = []
    for i in range(n):
        bo = a[i * q:(i + 1) * q:4]
        out.append((sum(x * x for x in bo) / max(1, len(bo))) ** 0.5 if len(bo) else 0.0)
    mx = max(out) or 1.0
    return [min(1.0, v / mx) for v in out]


@lru_cache(maxsize=64)
def _ustoz_rasm(kalit, h):
    p = os.path.join(DATA, "rasm", "ustoz", kalit + ".png")
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    return im if im.height == h else im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


@lru_cache(maxsize=48)
def _ustoz_aralash(ustoz, h, q):
    """Og'iz: q=0 yopiq, 1 yarim (ikki rasm aralashmasi), 2 ochiq."""
    a, b = _ustoz_rasm(f"{ustoz}_yopiq", h), _ustoz_rasm(f"{ustoz}_ochiq", h)
    if q == 0 or b is None:
        return a
    if q == 2:
        return b
    yarim = _ustoz_rasm(f"{ustoz}_yarim", h)
    return yarim if yarim is not None else Image.blend(a, b, 0.5)


def _koz(t, faza):
    f = ((t + faza) % 4.7)
    return f < 0.13


class Jonli:
    def __init__(self, ssen):
        self.s = ssen
        self.eski = Sahna(ssen)   # karta, yozuv, o'yin foni — oldingi qism
        self.fon = Image.open(os.path.join(DATA, "rasm", "fon", ssen["fon"] + ".jpg")).convert("RGBA")
        d = ImageDraw.Draw(self.fon)
        sar = f"KABUTAR TV · {'Hafta yakuni' if ssen.get('haftalik') else TIL_NOMI[ssen['til']]} · {ssen['daraja']}"
        d.rounded_rectangle((16, 14, 30 + d.textlength(sar, font=F["ism"]), 50), 12, fill=(255, 255, 255, 220))
        _matn_ol(d, (24, 32), sar, F["ism"], (29, 60, 120), anchor="lm")
        self.fon.alpha_composite(rasm("logo.png"), (W - rasm("logo.png").width - 18, 12))
        self.oyin = Sahna.oyin_fon().copy()
        self.oyin.alpha_composite(rasm("logo.png"), (W - rasm("logo.png").width - 18, 12))
        hd = os.path.join(DATA, "rasm", "fon", ssen["fon"] + "_hd.jpg")
        self.fon_hd = Image.open(hd).convert("RGBA") if os.path.exists(hd) else None   # REV196: yaqin plan uchun tiniq fon
        # REV208: studiya paketi (bo'lsa) — rakurslar: old, chap, ong, yaqin
        self.studiya = studiya_nomi(ssen)
        self.plita = {}
        if self.studiya:
            for v in ("old", "chap", "ong", "yaqin"):
                im = Image.open(os.path.join(STD, f"{self.studiya}_{v}.jpg")).convert("RGBA")
                if v != "yaqin":
                    d = ImageDraw.Draw(im)
                    d.rounded_rectangle((16, 14, 30 + d.textlength(sar, font=F["ism"]), 50), 12, fill=(255, 255, 255, 220))
                    _matn_ol(d, (24, 32), sar, F["ism"], (29, 60, 120), anchor="lm")
                im.alpha_composite(rasm("logo.png"), (W - rasm("logo.png").width - 18, 12))
                self.plita[v] = im
        self.karta_alfa = 1.0

    def _sprite(self, kalit, kim, gapir, daraja, t, h):
        """REV201: rassomning butun rasmi + jonli yuz. Poza (tik/salom/korsat) imo-ishoraga qarab, almashganda yumshoq o'tadi."""
        ctx = getattr(self, "ctx", {}) or {}
        imo, _ = ctx.get("imo", {}).get(kim, (None, 0.0))
        poza = "salom" if imo == "salom" else "korsat" if imo == "korsat" else "tik"
        # REV205: sherigi gapirayotganda — unga burilib tinglaydi (rassomning yon tomonga qaragan rasmi)
        sherik = ctx.get("gapiruvchi")
        if poza == "tik" and not gapir and sherik in ("T", "I") and sherik != kim and ctx.get("uzun_gap"):
            poza = "qara"
        if not yuzmod.bormi(kalit, poza):
            poza = "tik"
        holatlar = self.__dict__.setdefault("_poza", {})
        eski = holatlar.get(kalit)
        if not eski or eski[0] != poza:
            holatlar[kalit] = (poza, t, eski[0] if eski else poza)
        poza, t0, oldingi = holatlar[kalit]
        m = yuzmod.meta(kalit)
        tik = m["tik"]
        k_tik = h / tik["olcham"][1]
        koz = yuzmod.koz_holati(t, 0.0 if kim == "T" else 2.1) if poza != "qara" else 0
        vis, aniq = ctx.get("vis", "X"), bool(ctx.get("aniq"))

        def tayyor(pz):
            mp = m[pz]
            # bo'yi: ko'zdan oyoqqacha masofa barcha pozalarda bir xil bo'lsin (qo'l ko'tarilsa ham personaj kichraymaydi)
            ey = (mp["lm"][36][1] + mp["lm"][45][1]) / 2
            ey_t = (tik["lm"][36][1] + tik["lm"][45][1]) / 2
            k = k_tik * (tik["olcham"][1] - ey_t) / max(1.0, (mp["olcham"][1] - ey))
            bal = max(1, round(mp["olcham"][1] * k))
            img = _yuz_kadr(kalit, pz, gapir, daraja, vis, koz, bal, aniq)
            fx = mp["lm"][27][0] * k                      # yuz markazi (burun ko'prigi) — joylash nuqtasi
            fx_t = tik["lm"][27][0] * k_tik - tik["olcham"][0] * k_tik / 2
            return img, fx - fx_t
        img, ox = tayyor(poza)
        o = min(1.0, (t - t0) / 0.2)
        if o < 1.0 and oldingi != poza:
            img0, ox0 = tayyor(oldingi)
            return [(img0, ox0, 1 - o), (img, ox, o)]
        return [(img, ox, 1.0)]

    def _ustoz(self, im, kalit, cx, oyoq, h, gapir, daraja, t, faza):
        # REV201: butun rasm + jonli yuz (rassom chizgani buzilmaydi) — birinchi o'rinda
        if yuzmod.bormi(kalit):
            kim = "T" if kalit == self.s["ustoz"] else "I"
            bob = 1.5 * _m.sin((t + faza) * 2 * _m.pi / 3.8)
            sway = 1.2 * _m.sin((t + faza) * 2 * _m.pi / 6.1)
            for img, ox, alfa in self._sprite(kalit, kim, gapir, daraja, t, h):
                if alfa < 0.999:
                    img = img.copy()
                    img.putalpha(img.getchannel("A").point(lambda a, al=alfa: int(a * al)))
                im.alpha_composite(img, (round(cx - ox + sway), round(oyoq - img.height + bob)))
            return
        # REV197: skeletli (rig) personaj bo'lsa — jonli: imo-ishora, nigoh, mimika, tovushga mos og'iz
        if rig.rig_bormi(kalit):
            kim = "T" if kalit == self.s["ustoz"] else "I"
            ctx = getattr(self, "ctx", {}) or {}
            imo, imo_t = ctx.get("imo", {}).get(kim, (None, 0.0))
            tomon = "chap" if kim == "T" else "ong"            # karta ustozlar o'rtasida
            qara = 0.0
            if ctx.get("gapiruvchi") in ("T", "I") and ctx.get("gapiruvchi") != kim:
                qara = 1.0 if kim == "T" else -1.0             # sherigiga qaraydi
            p = rig.poza(t, gapir=gapir, daraja=daraja, ogiz=ctx.get("vis", "X"), imo=imo, imo_t=imo_t, qara=qara, faza=faza, tomon=tomon)
            u, ux, uy = rig.joyla(kalit, h, p)
            im.alpha_composite(u, (round(cx - ux), round(oyoq - uy)))
            return
        q = 0 if not gapir else (2 if daraja > 0.55 else 1 if daraja > 0.22 else 0)
        if kalit == "nilufar":
            nom = "nilufar_yumuq" if (not gapir and _koz(t, faza)) else ("nilufar_" + ("yopiq", "yarim", "ochiq")[q])
            u = _ustoz_rasm(nom, h)
        else:
            u = _ustoz_aralash(kalit, h, q)
            if _koz(t, faza):
                y = _ustoz_rasm(f"{kalit}_yumuq", h)   # ixtiyoriy: ko'z yumuq rasm bo'lsa — ko'z qisadi
                u = y if (y is not None and not gapir) else u
        bob = 2.5 * _m.sin((t + faza) * 2 * _m.pi / 3.6)          # nafas
        sway = 2.0 * _m.sin((t + faza) * 2 * _m.pi / 5.3)
        im.alpha_composite(u, (round(cx - u.width / 2 + sway), round(oyoq - u.height + bob)))

    def belgi(self, im, kim, x, y, r, teatr=False):
        """Kabu tepasida til belgisi (EN / UZ) — bolalar qaysi Kabu qaysi tilda gapirishini bilsin."""
        til = self.s["til"] if (kim == "K1" or teatr) else "uz"
        d = ImageDraw.Draw(im)
        d.ellipse((x - r, y - r, x + r, y + r), fill=RANG[kim], outline=(255, 255, 255), width=3)
        _matn_ol(d, (x, y), BAYROQ[til], _font(round(r * 0.75)), (255, 255, 255))

    def kadr(self, sh, kim, daraja, t, tsahna):
        oyin = sh.get("joy") == "oyin"
        holat_k = lambda k: ("gapir" if kim == k else "hurra" if sh.get("bayram") and tsahna < 2.5
                             else "salom" if sh["nom"] in ("salom", "salom_yaqin", "xayr", "oyin_bosh") else "tingla")
        if oyin:
            im = self.oyin.copy()
            for k, x, oyna in (("K1", 180, False), ("K2", 1100, True)):
                if k == "K2" and not self.s["uzbek"]:
                    continue
                kb = _kabu(330, t, holat_k(k), daraja if kim == k else 0, 0.0 if k == "K1" else 1.3, oyna)
                im.alpha_composite(kb, (round(x - kb.width / 2), 610 - kb.height))
                self.belgi(im, k, x + (95 if k == "K1" else -95), 610 - kb.height + 60, 26, teatr=bool(sh.get("teatr")))
        else:
            # REV196: studiyada faqat ikki ustoz — Kabularning o'z lavhalari bor (aralashmaydi)
            if self.studiya:
                return self.studiya_kadr(sh, kim, daraja, t, tsahna)
            # kamera rejasi: yaqin sahna — doim; kartali sahnada uzun izoh (4+ so'z) karta ko'rilgach — gapiruvchiga «kesadi»
            kesish = (sh.get("kamera") == "yaqin" or (sh.get("karta") and getattr(self, "uzun", False) and tsahna > 2.5))
            if kesish and self.fon_hd is not None and kim in ("T", "I"):
                return self.yaqin_kadr(kim, daraja, t, tsahna)
            im = self.fon.copy()
            self._ustoz(im, self.s["ustoz"], 270, 700, 470, kim == "T", daraja, t, 0.0)
            if self.s["uzbek"]:
                self._ustoz(im, "nilufar", 1010, 700, 470, kim == "I", daraja, t, 2.1)
        if sh.get("karta"):
            im.alpha_composite(self.eski.karta_qatlam(sh))
        # REV196: kamera — umumiy planda sekin yaqinlashadi (sahna «tirik»), to'g'ri javobda «zarb» bilan kattalashadi
        z = 1.0 + 0.045 * min(1.0, tsahna / 7.0)
        if sh.get("bayram") and tsahna < 0.4:
            z += 0.05 * (1 - tsahna / 0.4)
        if z > 1.002:
            w, h = W / z, H / z
            x0, y0 = (W - w) / 2, (H - h) * 0.4
            im = im.crop((round(x0), round(y0), round(x0 + w), round(y0 + h))).resize((W, H), Image.BILINEAR)
        return im

    def ekranga(self, im, sh, view):
        """Karta studiya ekrani ichida (ekran oq — karta oq foni bilan qo'shilib ketadi)."""
        bb = ekranlar().get(f"{self.studiya}_{view}")
        if not bb or not sh.get("karta"):
            return
        q = self.eski.karta_qatlam(sh).crop((330, 66, 950, 380))
        x0, y0, x1, y1 = bb
        mw, mh = (x1 - x0) * 0.94, (y1 - y0) * 0.92
        k = min(mw / q.width, mh / q.height)
        q = q.resize((max(1, round(q.width * k)), max(1, round(q.height * k))), Image.LANCZOS)
        if self.karta_alfa < 0.999:
            q.putalpha(q.getchannel("A").point(lambda a: int(a * self.karta_alfa)))
        im.alpha_composite(q, (round((x0 + x1 - q.width) / 2), round((y0 + y1 - q.height) / 2)))

    def studiya_kadr(self, sh, kim, daraja, t, tsahna):
        """REV208: rakursni rejissor tanlaydi: karta — old (ikki ustoz, karta ekranda); uzun izoh — gapiruvchiga
        yaqin rakurs (chap/o'ng); yaqin sahna — yaqin rakurs (ustoz ko'krakdan yuqori, ekran yonida)."""
        uzun = getattr(self, "uzun", False)
        if sh.get("kamera") == "yaqin" and kim in ("T", "I"):
            view = "yaqin"
        elif kim in ("T", "I") and uzun and (not sh.get("karta") or tsahna > 2.5):
            view = "chap" if kim == "T" else "ong"
        else:
            view = "old"
        im = self.plita[view].copy()
        if view == "yaqin":
            self.ekranga(im, sh, view)
            kalit = self.s["ustoz"] if kim == "T" else "nilufar"
            if yuzmod.bormi(kalit, "yaqin"):
                m = yuzmod.meta(kalit)["yaqin"]
                bal = 620
                ctx = getattr(self, "ctx", {}) or {}
                koz = yuzmod.koz_holati(t, 0.0 if kim == "T" else 2.1)
                img = _yuz_kadr(kalit, "yaqin", True, daraja, ctx.get("vis", "X"), koz, bal, bool(ctx.get("aniq")))
                fx = m["lm"][27][0] * bal / m["olcham"][1]
                bob = 1.2 * _m.sin(t * 2 * _m.pi / 3.8)
                im.alpha_composite(img, (round(330 - fx), round(H - img.height + 8 + bob)))
            else:
                self._ustoz(im, kalit, 330, 740, 640, True, daraja, t, 0.0 if kim == "T" else 2.1)
            return im
        if view == "old":
            self.ekranga(im, sh, view)
            # ustozlar ekranni to'smasin: ekran o'ngda bo'lsa — ikkalasi ekranning chap tomonida turadi
            ek = ekranlar().get(f"{self.studiya}_old") or (520, 0, 1140, 0)
            if self.s["uzbek"]:
                xt, xi = (165, max(380, ek[0] - 120)) if ek[0] > 540 else (250, min(1190, ek[2] + 90))
            else:
                xt, xi = (max(200, ek[0] - 230), None)
            self._ustoz(im, self.s["ustoz"], xt, 706, 480, kim == "T", daraja, t, 0.0)
            if xi is not None:
                self._ustoz(im, "nilufar", xi, 706, 480, kim == "I", daraja, t, 2.1)
            return im
        # chap / o'ng: gapiruvchi kattaroq, kadrning bir tomonida; ekranda karta (bo'lsa)
        self.ekranga(im, sh, view)
        kalit = self.s["ustoz"] if kim == "T" else "nilufar"
        x = 300 if view == "chap" else 470
        self._ustoz(im, kalit, x, 760, 600, True, daraja, t, 0.0 if kim == "T" else 2.1)
        return im

    def yaqin_kadr(self, kim, daraja, t, tsahna):
        """REV196: haqiqiy yaqin plan — tiniq fon va katta ustoz (1,7×), kamera sekin suriladi."""
        z = self.fon_hd.width / W
        cx = (270 if kim == "T" else 1010) * z + 18 * _m.sin(t * 2 * _m.pi / 9)
        wx = max(0, min(self.fon_hd.width - W, round(cx - W / 2)))
        wy = round(300 + 12 * min(1.0, tsahna / 3))
        im = self.fon_hd.crop((wx, wy, wx + W, wy + H))
        kalit = self.s["ustoz"] if kim == "T" else "nilufar"
        if yuzmod.bormi(kalit, "yaqin"):   # REV201: yaqin plan — rassomning alohida yaqin rasmi (tiniq)
            m = yuzmod.meta(kalit)["yaqin"]
            bal = 640
            koz = yuzmod.koz_holati(t, 0.0 if kim == "T" else 2.1)
            ctx = getattr(self, "ctx", {}) or {}
            img = _yuz_kadr(kalit, "yaqin", True, daraja, ctx.get("vis", "X"), koz, bal, bool(ctx.get("aniq")))
            k = bal / m["olcham"][1]
            fx = m["lm"][27][0] * k
            bob = 1.2 * _m.sin(t * 2 * _m.pi / 3.8)
            im.alpha_composite(img, (round(W / 2 - fx + 8 * _m.sin(t * 2 * _m.pi / 9)), round(H - img.height + 6 + bob)))
            return im
        self._ustoz(im, kalit, cx - wx, 700 * z - wy, round(470 * z), True, daraja, t, 0.0 if kim == "T" else 2.1)
        return im


def _imo(sh, q, tsahna, tqator):
    """REV197: rejissor imo-ishorasi: salom/xayr — qo'l silkitish; so'z kartasida — kartaga ko'rsatish;
    to'g'ri javob/bayram — kulish; savol — hayron; uzun gapda — bosh irg'ash. {kim: (imo, imo_t)}."""
    kim = q["kim"]
    out = {}
    nom = sh.get("nom", "")
    if nom in ("salom", "salom_yaqin", "xayr") and tsahna < 2.6:
        out["T"] = ("salom", tsahna)
        out["I"] = ("salom", tsahna)
    elif sh.get("bayram") and tsahna < 3.0:
        out["T"] = ("kul", tsahna)
        out["I"] = ("kul", tsahna)
    elif sh.get("karta") and kim in ("T", "I") and tqator < 2.2 and len(q["matn"].split()) <= 4:
        out[kim] = ("korsat", tqator)
    elif kim in ("T", "I") and q["matn"].rstrip().endswith("?"):
        out[kim] = ("hayron", tqator)
    elif kim in ("T", "I") and len(q["matn"].split()) >= 8 and 0.5 < tqator < 1.7:
        out[kim] = ("irgash", tqator - 0.5)
    return out


def _jonli_yasash(ssen, chiqish, tts, kesh, kirish_chiqish, ish, log):
    j = Jonli(ssen)
    ismlar = {"T": ssen["ustoz_ism"], "I": "Nilufar opa", "K1": "Kabu", "K2": "Kabu (UZ)"}
    os.makedirs(os.path.dirname(chiqish) or ".", exist_ok=True)
    wav = os.path.join(ish, "ovoz.wav")
    asosiy = os.path.join(ish, "asosiy.mp4")
    pcm = bytearray()
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p", os.path.join(ish, "video.mp4")],
                          stdin=subprocess.PIPE)
    n = [0]
    t_global = [0.0]

    def yoz(im):
        j.oxirgi = im
        ff.stdin.write(im.convert("RGB").tobytes())
        n[0] += 1
        t_global[0] = n[0] / FPS

    def ovoz_tekisla():   # ovoz uzunligi kadrlar soniga aniq teng bo'lsin
        kerak = round(n[0] * SR / FPS) * 2
        if len(pcm) < kerak:
            pcm.extend(b"\x00" * (kerak - len(pcm)))
        elif len(pcm) > kerak:
            del pcm[kerak:]

    try:
        for sh in ssen["sahnalar"]:
            if not sh["qatorlar"]:
                continue
            ts0 = t_global[0]
            if sh.get("bayram"):
                pcm.extend(sfx("03_togri_javob") or tovush("ding"))
            # REV208: bo'lim boshida — studiya paketining o'tish animatsiyasi (oldingi kadr → yangi sahna)
            if j.studiya and (sh["nom"].startswith(("otish_", "oyin_bosh", "vaziyat_bosh", "sayohat_bosh", "yakun", "xayr"))) and n[0] > 0:
                tur = "oyin" if sh.get("joy") == "oyin" else j.studiya
                royxat = OTISH_YOSH.get(tur) or ["01_qanot"]
                kadrlar = otish_kadrlari(royxat[(len(pcm) // 9973) % len(royxat)])
                if kadrlar:
                    pcm.extend(sfx("08_yumshoq_otish"))
                    oldingi = getattr(j, "oxirgi", None)
                    yangi = j.kadr(sh, None, 0, t_global[0], 0.0)
                    for i, ok in enumerate(kadrlar):
                        asos = (oldingi if (i < len(kadrlar) // 2 and oldingi is not None) else yangi).copy()
                        asos.alpha_composite(ok)
                        yoz(asos)
                    ovoz_tekisla()
                    ts0 = t_global[0]
            if j.studiya and sh.get("karta") and not sh.get("kamera") and sh.get("pop", True) and sh.get("joy") != "oyin":
                pcm.extend(sfx("02_kichik_pop"))
                for a in (0.25, 0.5, 0.75, 1.0):   # karta ekranda paydo bo'ladi (yumshoq)
                    j.karta_alfa = a
                    yoz(j.kadr(sh, None, 0, t_global[0], t_global[0] - ts0))
                ovoz_tekisla()
            elif sh.get("karta") and not sh.get("kamera") and sh.get("pop", True):
                for ko in (0.55, 0.75, 0.9, 1.03, 1.0):
                    im = j.kadr({**sh, "karta": None}, None, 0, t_global[0], t_global[0] - ts0)
                    m = j.eski.karta_qatlam(sh).resize((round(W * ko), round(H * ko)), Image.BILINEAR)
                    im.alpha_composite(m, (round(640 - 640 * ko), round(230 - 230 * ko)))
                    yoz(im)
                ovoz_tekisla()
            for q in sh["qatorlar"]:
                voice, rate, pitch = ovoz_tanla(q["kim"], q["til"], ssen)
                p, cheg = tts(q["matn"], voice, rate, pitch, kesh)
                dav = len(p) / 2 / SR
                nk = max(1, round(dav * FPS))
                lv = _darajalar(p, nk)
                vaqtlar = _soz_vaqtlari(q, cheg, dav)
                ism = (q.get("rol") + " · " if q.get("rol") else "") + ismlar[q["kim"]]
                j.uzun = len(q["matn"].split()) >= 4 and q["kim"] in ("T", "I")
                pcm.extend(p)
                sozlar_q = q["matn"].split()
                silliq = rig.Silliq()
                # REV202: ustozlar uchun og'iz shakllari — Rhubarb (ovozni tinglab, millisoniyagacha aniq)
                cues = labsinx.belgilar(p, SR, q["matn"], q["til"], kesh) if q["kim"] in ("T", "I") else None
                for f in range(nk):
                    tt = f / FPS
                    faol = max(0, sum(1 for v in vaqtlar if v <= tt + 0.02) - 1)
                    # REV197: rejissor konteksti — kim gapiryapti, og'iz shakli, imo-ishora
                    if sozlar_q and lv[f] > 0.12:
                        bosh_v = vaqtlar[faol] if faol < len(vaqtlar) else 0
                        keyin_v = vaqtlar[faol + 1] if faol + 1 < len(vaqtlar) else dav
                        ul = (tt - bosh_v) / max(0.05, keyin_v - bosh_v)
                        vis = rig.visema(sozlar_q[min(faol, len(sozlar_q) - 1)], max(0.0, min(0.999, ul)))
                    else:
                        vis = "X"
                    vis = silliq(vis, lv[f])
                    if cues:
                        vis = labsinx.shakl(cues, tt)
                        if vis in ("D", "E", "F") and lv[f] < 0.7:    # REV204: keng og'iz faqat eng baland unlida — tabiiy, sezilmas
                            vis = "B"
                    j.ctx = {"gapiruvchi": q["kim"], "vis": vis, "aniq": bool(cues), "imo": _imo(sh, q, t_global[0] - ts0, tt),
                             "uzun_gap": len(sozlar_q) >= 4 and tt > 0.4}
                    im = j.kadr(sh, q["kim"], lv[f], t_global[0], t_global[0] - ts0)
                    if sh.get("bayram") and t_global[0] - ts0 < 1.6:
                        im = konfetti(im, 0.2 + (t_global[0] - ts0))
                    j.eski.yozuv(im, q, faol, ism)
                    yoz(im)
                ovoz_tekisla()
                for f in range(round(q.get("pauza", 0.25) * FPS)):
                    im = j.kadr(sh, q["kim"] if sh.get("kamera") == "yaqin" else None, 0, t_global[0], t_global[0] - ts0)
                    j.eski.yozuv(im, q, len(q["matn"].split()), ism)
                    yoz(im)
                ovoz_tekisla()
                sanoq_n = int(q.get("sanoq") or 0)
                if sanoq_n and sfx("18_uch_ikki_bir"):
                    pcm.extend(sfx("18_uch_ikki_bir")[: int(SR * min(2.4, sanoq_n)) * 2])
                for sn in range(sanoq_n, 0, -1):
                    if not sfx("18_uch_ikki_bir"):
                        pcm.extend(tovush("tik"))
                    for f in range(FPS):
                        im = j.kadr(sh, None, 0, t_global[0], t_global[0] - ts0)
                        j.eski.yozuv(im, q, len(q["matn"].split()), ism)
                        d = ImageDraw.Draw(im)
                        pul = 1 + 0.12 * _m.sin(f / FPS * _m.pi)   # raqam «yuradi»
                        r = 60 * pul
                        d.ellipse((1020 - r, 130 - r, 1020 + r, 130 + r), fill=(232, 120, 20, 245), outline=(255, 255, 255), width=6)
                        _matn_ol(d, (1020, 130), str(sn), F["sanoq"], (255, 255, 255))
                        yoz(im)
                    ovoz_tekisla()
        ff.stdin.close()
        ff.wait()
        if ff.returncode:
            raise RuntimeError("ffmpeg video yozolmadi")
        if j.studiya and os.environ.get("KABUTAR_TV_MUSIQA", "1") != "0":   # REV208: past ovozli fon musiqasi
            pcm[:] = musiqa_qosh(pcm, MUSIQA_YOSH.get(j.studiya, "04_tinch_mashq_suhbat_foni"))
        with wave.open(wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(bytes(pcm))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(ish, "video.mp4"), "-i", wav, "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "80k", "-ar", str(SR), "-ac", "1", "-shortest", asosiy], check=True)
    finally:
        try:
            ff.stdin.close()
        except Exception:
            pass
    return asosiy

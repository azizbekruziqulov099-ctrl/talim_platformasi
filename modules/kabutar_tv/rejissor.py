"""REV185: KABUTAR TV — REJISSOR.

Ssenariydan video yig'adi: har qatorga ovoz (edge-tts, saytdagi ovozlar), studiya foni, ustozlar (og'zi ochiq/yopiq),
ikki Kabu, markazda karta (emoji + so'z + tarjima, gap kartalari, sanoq 3-2-1) va pastda karaoke yozuv — aytilayotgan
so'z yonadi, har ishtirokchi o'z rangida. Boshiga kirish, oxiriga chiqish videosi qo'yiladi. 1280×720, 15 kadr/s.
"""
import asyncio
import hashlib
import io
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


def edge_tts_ovoz(matn, voice, rate, pitch, kesh):
    """→ (pcm s16 mono 24 kHz bytes, [(soniya, so'z)]). Kesh — bir xil gap qayta so'ralmaydi."""
    kalit = hashlib.sha1(f"{voice}|{rate}|{pitch}|{matn}".encode()).hexdigest()
    p = os.path.join(kesh, kalit)
    if os.path.exists(p + ".pcm"):
        import json
        return open(p + ".pcm", "rb").read(), [tuple(x) for x in json.load(open(p + ".json"))]
    mp3, cheg = None, []
    for _ in range(3):
        try:
            mp3, cheg = asyncio.run(_edge(matn, voice, rate, pitch))
            if mp3:
                break
        except Exception:
            mp3 = None
    if not mp3:
        raise RuntimeError(f"Ovoz olinmadi: {matn[:40]}")
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

    def asos(self, sahna, gapiruvchi, faza):
        """Fon + personajlar. gapiruvchi: T/I/K1/K2/None; faza: og'iz ochiq (1) yoki yopiq (0)."""
        kalit = (id(sahna), gapiruvchi, faza)
        if kalit in self._kesh:
            return self._kesh[kalit].copy()
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
        self._karta(im, sahna.get("karta") or {})
        im.alpha_composite(self.logo, (W - self.logo.width - 18, 12))
        d = ImageDraw.Draw(im)
        sar = f"KABUTAR TV · {'Hafta yakuni' if self.s.get('haftalik') else TIL_NOMI[self.s['til']]} · {self.s['daraja']}"
        d.rounded_rectangle((16, 14, 30 + d.textlength(sar, font=F["ism"]), 50), 12, fill=(255, 255, 255, 220))
        _matn_ol(d, (24, 32), sar, F["ism"], (29, 60, 120), anchor="lm")
        if len(self._kesh) > 400:
            self._kesh.clear()
        self._kesh[kalit] = im.copy()
        return im

    def _karta(self, im, k):
        if not k:
            return
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = 330, 66, 950, 380
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
            for i, q in enumerate(_qatorla(k["sarlavha"], F["sarlavha"], x1 - x0 - 60, d)[:3]):
                _matn_ol(d, (cx, 170 + i * 60), q, F["sarlavha"], (29, 111, 216))
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
        sahna = Sahna(ssen)
        ismlar = {"T": ssen["ustoz_ism"], "I": "Nilufar opa", "K1": "Kabu", "K2": "Kabu (UZ)"}
        pcm_hammasi = bytearray()
        kadrlar = []   # (fayl, soniya)
        kadr_n = [0]

        def kadr(img, sek):
            if sek <= 0.001:
                return
            if kadrlar and kadrlar[-1][2] == id(img):
                kadrlar[-1] = (kadrlar[-1][0], kadrlar[-1][1] + sek, id(img))
                return
            p = os.path.join(ish, "k", f"{kadr_n[0]:06d}.jpg")
            img.convert("RGB").save(p, quality=82)
            kadr_n[0] += 1
            kadrlar.append((p, sek, id(img)))

        def jim(sek):
            pcm_hammasi.extend(b"\x00\x00" * int(SR * sek))

        for sh in ssen["sahnalar"]:
            if not sh["qatorlar"]:
                continue
            for q in sh["qatorlar"]:
                voice, rate, pitch = ovoz_tanla(q["kim"], q["til"], ssen)
                pcm, cheg = tts(q["matn"], voice, rate, pitch, kesh)
                dav = len(pcm) / 2 / SR
                vaqtlar = _soz_vaqtlari(q, cheg, dav)
                ism = (q.get("rol") + " · " if q.get("rol") else "") + ismlar[q["kim"]]
                # og'iz har 0.13 s da almashadi; so'z o'zgarsa — yangi kadr
                t, qadam, faza = 0.0, 0.13, 1
                while t < dav - 0.01:
                    sek = min(qadam, dav - t)
                    faol = max(0, sum(1 for v in vaqtlar if v <= t + 0.02) - 1)
                    im = sahna.asos(sh, q["kim"], faza)
                    sahna.yozuv(im, q, faol, ism)
                    kadr(im, sek)
                    t += sek
                    faza = 1 - faza
                pcm_hammasi.extend(pcm)
                tin = sahna.asos(sh, None, 0)
                sahna.yozuv(tin, q, len(q["matn"].split()), ism)
                kadr(tin, q.get("pauza", 0.25))
                jim(q.get("pauza", 0.25))
                for n in range(int(q.get("sanoq") or 0), 0, -1):
                    im = sahna.asos(sh, None, 0)
                    sahna.yozuv(im, q, len(q["matn"].split()), ism)
                    d = ImageDraw.Draw(im)
                    d.ellipse((960, 70, 1080, 190), fill=(232, 120, 20, 240), outline=(255, 255, 255), width=6)
                    _matn_ol(d, (1020, 130), str(n), F["sanoq"], (255, 255, 255))
                    kadr(im, 1.0)
                    jim(1.0)
        # oxirgi kadr concat uchun takrorlanadi
        ro = os.path.join(ish, "royxat.txt")
        with open(ro, "w") as f:
            for p, sek, _ in kadrlar:
                f.write(f"file '{p}'\nduration {sek:.3f}\n")
            if kadrlar:
                f.write(f"file '{kadrlar[-1][0]}'\n")
        wav = os.path.join(ish, "ovoz.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(bytes(pcm_hammasi))
        asosiy = os.path.join(ish, "asosiy.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", ro, "-i", wav,
                        "-vf", f"fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "27",
                        "-c:a", "aac", "-b:a", "80k", "-ar", str(SR), "-ac", "1", "-shortest", asosiy], check=True)
        os.makedirs(os.path.dirname(chiqish) or ".", exist_ok=True)
        if kirish_chiqish:
            qismlar = [os.path.join(DATA, "video", "kirish_12s.mp4"), asosiy, os.path.join(DATA, "video", "chiqish_8s.mp4")]
            ro2 = os.path.join(ish, "qism.txt")
            with open(ro2, "w") as f:
                for p in qismlar:
                    f.write(f"file '{p}'\n")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", ro2,
                            "-vf", f"fps={FPS},scale={W}:{H},format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
                            "-crf", "27", "-c:a", "aac", "-b:a", "80k", "-ar", str(SR), "-ac", "1", "-movflags", "+faststart", chiqish], check=True)
        else:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", asosiy, "-c", "copy", "-movflags", "+faststart", chiqish], check=True)
        dav = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", chiqish],
                                   capture_output=True, text=True).stdout.strip() or 0)
        return dav
    finally:
        if not ish_papka:
            shutil.rmtree(ish, ignore_errors=True)

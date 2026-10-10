"""REV102: ovoz rejasi — matn → edge-tts bo'laklari (til bo'yicha) + bolaga qaytarish uchun pauzalar.

Muammo (videoda ko'rindi): har bir [en]…[/en] bo'lagi va har o'zbekcha gap alohida edge-tts so'rovi edi.
«Bugun biz [en]Green[/en], [en]Clap[/en], [en]Ears[/en] ni o'rgandik» — 7–9 ta so'rov ketma-ket; bittasi uzilsa,
qolgani eshitilmasdi («faqat bitta so'zni aytadi»). Endi:
  * faqat tinish belgisidan iborat bo'laklar tashlanadi, yonma-yon bir tildagi qisqa bo'laklar qo'shiladi;
  * «Men bilan ayt: [en]Green[/en]», «Say: Green.» kabi joyda so'zdan keyin bola qaytarib aytishi uchun
    1–3 soniya jimlik (so'z uzunligiga qarab) — faqat takror=True (bog'cha darsining tushuntirish qadami);
  * matndagi «⏸» belgisi — aniq pauza (doim).
Jimlik MP3 kadrlari audio bilan bir xil formatda yasaladi — brauzer bitta fayl sifatida uzluksiz o'ynaydi.
"""
from __future__ import annotations

import re

from modules.speech_audio import mp3_frames

PAUSE_MARK = "⏸"
MERGE_LIMIT = 220          # qo'shilgan bo'lak uzunligi (belgi) — juda uzun bo'lsa birinchi ovoz kechikadi
MIN_PAUSE, MAX_PAUSE = 1.5, 3.0

# O'zbekcha «qaytar» buyruqlari: «Men bilan ayt:», «Yana bir marta:», «Endi shivirlab:», «Qani, birga aytamiz!»
_PROMPT_UZ = re.compile(
    r"(?:\bayt\w*|\btakrorla\w*|\bqaytar\w*|\byana(?:\s+bir\s+marta)?|\bshivirla\w*|\bovozda|\bbirga)\s*[:!.,…]?\s*$",
    re.I,
)
_SENTENCE = re.compile(r"(?<=[.!?:;。！？：；؟])\s+")
_WORD = re.compile(r"\w+", re.U)


def _words(text):
    return _WORD.findall(str(text or ""))


def speakable(text) -> bool:
    """Ovozga chiqadigan harf yoki raqam bormi (faqat «, — !» bo'lsa — yo'q)."""
    return bool(_words(text))


def pause_for(phrase) -> float:
    """Qaytarish uchun vaqt: so'z ko'p va uzun bo'lsa ko'proq. «Green» → 1.5 s, «How are you?» → 2.7 s, uzun → 3 s."""
    words = _words(phrase)
    if not words:
        return MIN_PAUSE
    letters = sum(len(w) for w in words)
    seconds = 1.3 + 0.5 * (len(words) - 1) + 0.04 * letters
    return round(min(MAX_PAUSE, max(MIN_PAUSE, seconds)), 2)


def _is_prompt_sentence(sentence) -> bool:
    """Chet tilidagi qisqa buyruq: «Say:», «Again!», «Your turn!», «One more time:», «Повтори:»."""
    s = sentence.strip()
    return bool(s) and s[-1] in ":!：！" and len(_words(s)) <= 4


def _is_target(sentence, limit) -> bool:
    """Bola qaytaradigan so'z/ibora: qisqa, o'zi buyruq emas («Say:» emas)."""
    s = sentence.strip()
    return speakable(s) and s[-1:] not in (":", "：") and len(_words(s)) <= limit


def _split_foreign(text, first_target=False):
    """Chet til bo'lagi → [(matn, pauza)]: buyruqdan keyingi qisqa so'zdan so'ng bolaga vaqt.

    first_target — bo'lakdan oldin o'zbekcha buyruq bor («Men bilan ayt:»): birinchi gap — qaytariladigan so'z."""
    sentences = [s for s in _SENTENCE.split(str(text).strip()) if s.strip()]
    out, current = [], []
    for i, sentence in enumerate(sentences):
        current.append(sentence)
        if (i == 0 and first_target and _is_target(sentence, 4)) or \
                (i > 0 and _is_prompt_sentence(sentences[i - 1]) and _is_target(sentence, 3)):
            out.append((" ".join(current), pause_for(sentence)))
            current = []
    if current:
        out.append((" ".join(current), 0.0))
    return out


def reja(text, takror=False):
    """Matn → [{"til", "matn", "pauza"}]. pauza — shu bo'lakdan keyingi jimlik (soniya)."""
    from modules.speech_language import split_speech_text

    items = []
    pieces = str(text or "").split(PAUSE_MARK)
    for n, piece in enumerate(pieces):
        for til, matn in split_speech_text(piece):
            items.append({"til": til, "matn": matn, "pauza": 0.0, "belgi": False})
        if n < len(pieces) - 1 and items:
            items[-1]["belgi"] = True          # «⏸» — aniq pauza (uzunligi pastda hisoblanadi)

    # 1) Tinish belgisidan iborat bo'laklar tashlanadi (pauza belgisi oldingisiga o'tadi)
    cleaned = []
    for it in items:
        if speakable(it["matn"]):
            cleaned.append(dict(it, matn=re.sub(r"\s+", " ", it["matn"]).strip()))
        elif cleaned and it["belgi"]:
            cleaned[-1]["belgi"] = True
    # 2) Yonma-yon bir tildagi qisqa bo'laklar — bitta so'rov
    merged = []
    for it in cleaned:
        last = merged[-1] if merged else None
        if (last and last["til"] == it["til"] and not last["belgi"]
                and len(last["matn"]) + len(it["matn"]) + 1 <= MERGE_LIMIT):
            joiner = " " if re.search(r"[.!?,;:…。！？،]$", last["matn"]) else ", "
            last["matn"] = f"{last['matn']}{joiner}{it['matn']}"
            last["belgi"] = it["belgi"]
        else:
            merged.append(dict(it))
    # 3) Takrorlash pauzalari (bog'cha tushuntirish qadami)
    out = []
    for i, it in enumerate(merged):
        if takror and it["til"] != "uz":
            prompt = i > 0 and merged[i - 1]["til"] == "uz" and bool(_PROMPT_UZ.search(merged[i - 1]["matn"]))
            parts = _split_foreign(it["matn"], first_target=prompt)
            for k, (part, pause) in enumerate(parts):
                out.append({"til": it["til"], "matn": part, "pauza": pause,
                            "belgi": it["belgi"] and k == len(parts) - 1})
        else:
            out.append(dict(it))
    # 4) «⏸» uzunligi — oldingi chet tilidagi ibora bo'yicha
    for i, it in enumerate(out):
        if it.pop("belgi", False):
            foreign = next((x["matn"] for x in reversed(out[:i + 1]) if x["til"] != "uz"), "")
            last_sentence = [s for s in _SENTENCE.split(foreign) if s.strip()][-1:] if foreign else []
            it["pauza"] = max(it["pauza"], pause_for(last_sentence[0]) if last_sentence else 1.5)
    return out


def jimlik(namuna, soniya) -> bytes:
    """`namuna` MP3 bilan bir xil formatdagi jimlik (`soniya` uzunlikda). Tanib bo'lmasa — b""."""
    if not namuna or not soniya or soniya <= 0:
        return b""
    frames = mp3_frames(namuna)
    if not frames:
        return b""
    start, _, duration = frames[0]
    head = bytearray(namuna[start:start + 4])
    head[1] |= 0x01            # CRC yo'q
    head[2] &= 0xFD            # padding yo'q
    version = (head[1] >> 3) & 0x03
    mpeg1 = version == 3
    bitrates = ([0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0] if mpeg1
                else [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0])
    rates = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}[version]
    bitrate = bitrates[(head[2] >> 4) & 0x0F] * 1000
    rate = rates[(head[2] >> 2) & 0x03]
    length = (144 if mpeg1 else 72) * bitrate // rate
    if length <= 4 or duration <= 0:
        return b""
    frame = bytes(head) + bytes(length - 4)   # yon ma'lumot va asosiy qism nol — dekoder jimlik chiqaradi
    return frame * max(1, round(soniya / duration))

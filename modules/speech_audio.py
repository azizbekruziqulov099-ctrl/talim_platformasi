"""REV93: aralash tilli ovozda bo'laklar orasidagi «uzilish»ni kamaytirish.

Har til bo'lagi (o'zbekcha → [en]…[/en] → o'zbekcha) alohida o'qiladi. Har MP3 bo'lagining boshida va oxirida
jimlik bor — ular ketma-ket qo'shilganda gap o'rtasida yarim soniyalik tanaffuslar paydo bo'ladi va ovoz
«robotdek» bo'lib qoladi. Bu yerda so'zlar qayerda boshlanib-tugashi (edge-tts boundary hodisalari) bo'yicha
bo'lakning ortiqcha jimligi MP3 kadrlari chegarasida kesiladi. Tahlil qila olmasak — bo'lak o'zgarmaydi.
"""

_BITRATES = {  # (mpeg1?, layer3) → kbps jadvali
    True: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0],
    False: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0],
}
_RATES = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}   # versiya biti → Hz

LEAD_KEEP = 0.04    # birinchi so'zdan oldin qoldiriladigan jimlik (soniya)
TAIL_KEEP = 0.14    # oxirgi so'zdan keyin — nafas olgandek tabiiy tanaffus


def mp3_frames(data):
    """MP3 (Layer III) kadrlari: [(boshlanish_bayt, uzunlik, davomiylik_soniya)]. Tanib bo'lmasa — None."""
    frames, i, n = [], 0, len(data)
    if data[:3] == b"ID3" and n > 10:
        size = (data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14 | (data[8] & 0x7F) << 7 | (data[9] & 0x7F)
        i = 10 + size
    while i + 4 <= n:
        b1, b2, b3 = data[i + 1], data[i + 2], data[i + 3]
        if data[i] != 0xFF or (b1 & 0xE0) != 0xE0:
            return None
        version = (b1 >> 3) & 0x03          # 3=MPEG1, 2=MPEG2, 0=MPEG2.5
        layer = (b1 >> 1) & 0x03            # 1 = Layer III
        if version == 1 or layer != 1:
            return None
        rate_i, bit_i = (b2 >> 2) & 0x03, (b2 >> 4) & 0x0F
        if rate_i == 3 or bit_i in (0, 15):
            return None
        mpeg1 = version == 3
        bitrate = _BITRATES[mpeg1][bit_i] * 1000
        rate = _RATES[version][rate_i]
        padding = (b2 >> 1) & 0x01
        samples = 1152 if mpeg1 else 576
        length = (144 if mpeg1 else 72) * bitrate // rate + padding
        if length <= 4 or i + length > n:
            if i + length > n and frames:   # oxirgi chala kadr — tashlaymiz
                break
            return None
        frames.append((i, length, samples / rate))
        i += length
    return frames or None


def trim_segment(data, speech_start, speech_end):
    """Nutq [speech_start, speech_end] soniyalar oralig'ida — undan tashqaridagi jimlik kesiladi."""
    if not data or speech_start is None or speech_end is None or speech_end <= speech_start:
        return data
    frames = mp3_frames(data)
    if not frames:
        return data
    total = sum(f[2] for f in frames)
    if speech_start < 0 or speech_end > total + 0.3:
        return data   # vaqtlar audio bilan mos emas — xavf qilmaymiz, kesmaymiz
    keep_from, keep_to = max(0.0, speech_start - LEAD_KEEP), speech_end + TAIL_KEEP
    out, t = bytearray(), 0.0
    for start, length, dur in frames:
        if t + dur > keep_from and t < keep_to:
            out.extend(data[start:start + length])
        t += dur
    return bytes(out) if len(out) >= 4 else data


def speech_window(events):
    """edge-tts Word/SentenceBoundary hodisalari (offset/duration — 100 ns birlikda) → (boshlanish, tugash) soniyada."""
    spans = [(e["offset"], e["offset"] + e.get("duration", 0)) for e in events
             if isinstance(e, dict) and isinstance(e.get("offset"), (int, float))]
    if not spans:
        return None, None
    return min(s for s, _ in spans) / 1e7, max(e for _, e in spans) / 1e7

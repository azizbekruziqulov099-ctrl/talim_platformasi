"""Text language detection shared with the browser reading rules (uz/en/ru)."""
import json
import re
from pathlib import Path
from modules.speech_math import protect_math

WORDS = json.loads(Path(__file__).with_name('speech_words.json').read_text(encoding='utf-8'))
ENGLISH = set(WORDS['en'])
UZBEK = set(WORDS['uz'])
SPEAKERS = {
    'uz': {'qiz': 'uz-UZ-MadinaNeural', 'ogil': 'uz-UZ-SardorNeural'},
    'en': {'qiz': 'en-US-JennyNeural', 'ogil': 'en-US-GuyNeural'},
    'ru': {'qiz': 'ru-RU-SvetlanaNeural', 'ogil': 'ru-RU-DmitryNeural'},
    # REV88: bog'cha til kitoblari — 10 til ([de]…[/de] kabi teglar)
    'de': {'qiz': 'de-DE-KatjaNeural', 'ogil': 'de-DE-ConradNeural'},
    'fr': {'qiz': 'fr-FR-DeniseNeural', 'ogil': 'fr-FR-HenriNeural'},
    'es': {'qiz': 'es-ES-ElviraNeural', 'ogil': 'es-ES-AlvaroNeural'},
    'ar': {'qiz': 'ar-EG-SalmaNeural', 'ogil': 'ar-EG-ShakirNeural'},
    'tr': {'qiz': 'tr-TR-EmelNeural', 'ogil': 'tr-TR-AhmetNeural'},
    'zh': {'qiz': 'zh-CN-XiaoxiaoNeural', 'ogil': 'zh-CN-YunxiNeural'},
    'ja': {'qiz': 'ja-JP-NanamiNeural', 'ogil': 'ja-JP-KeitaNeural'},
    'ko': {'qiz': 'ko-KR-SunHiNeural', 'ogil': 'ko-KR-InJoonNeural'},
}
TAG_LANGS = 'uz|en|ru|de|fr|es|ar|tr|zh|ja|ko'

def detect_language(value, fallback='uz'):
    text = re.sub(r'\[lat\].*?\[/lat\]|\$[^$]*\$|<[^>]*>', ' ', str(value or '').lower(), flags=re.S | re.I)
    text = re.sub(r"[‘’ʻʼ`']", '', text)
    if re.search('[ўқғҳ]', text): return 'uz'
    if re.search('[а-яё]', text):
        return 'uz' if re.search('салом|бугун|мактаб|билан|учун|эмас', text) else 'ru'
    en = uz = 0
    for word in re.findall('[a-z]+', text):
        if word in ENGLISH: en += 2
        if word in UZBEK: uz += 2
        if len(word) > 5 and re.search(r'(?:larni|ning|ingiz|uvchi|lardan)$', word): uz += 2
    if uz > en: return 'uz'
    if en > uz: return 'en'
    return fallback if fallback in SPEAKERS else 'uz'

def split_speech_text(value, language='auto'):
    text = str(value or '')
    result = []
    def untagged(part):
        if language in SPEAKERS:
            if part.strip():result.append((language,part))
            return
        current = 'uz'
        protected, restore = protect_math(part)
        for sentence in re.split(r'(?<=[.!?;\n])\s+', protected):
            if sentence.strip():
                result.append((current, restore(sentence)))
    previous = 0
    for match in re.finditer(r'\[(' + TAG_LANGS + r')\](.*?)\[/\1\]', text, re.S | re.I):
        untagged(text[previous:match.start()])
        if match[2].strip(): result.append((match[1].lower(), match[2]))
        previous = match.end()
    untagged(text[previous:])
    return result

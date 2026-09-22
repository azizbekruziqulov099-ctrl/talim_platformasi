"""Text language detection shared with the browser reading rules (uz/en/ru)."""
import json
import re
from pathlib import Path

WORDS = json.loads(Path(__file__).with_name('speech_words.json').read_text(encoding='utf-8'))
ENGLISH = set(WORDS['en'])
UZBEK = set(WORDS['uz'])
SPEAKERS = {
    'uz': {'qiz': 'uz-UZ-MadinaNeural', 'ogil': 'uz-UZ-SardorNeural'},
    'en': {'qiz': 'en-US-JennyNeural', 'ogil': 'en-US-GuyNeural'},
    'ru': {'qiz': 'ru-RU-SvetlanaNeural', 'ogil': 'ru-RU-DmitryNeural'},
}

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

def split_speech_text(value):
    text = str(value or '')
    result = []
    def untagged(part):
        language = detect_language(part)
        for sentence in re.split(r'(?<=[.!?;\n])\s+', part):
            if sentence.strip():
                language = detect_language(sentence, language)
                result.append((language, sentence))
    previous = 0
    for match in re.finditer(r'\[(uz|en|ru)\](.*?)\[/\1\]', text, re.S | re.I):
        untagged(text[previous:match.start()])
        if match[2].strip(): result.append((match[1].lower(), match[2]))
        previous = match.end()
    untagged(text[previous:])
    return result

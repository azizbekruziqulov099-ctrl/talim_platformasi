"""Prepare speech without changing saved/displayed text or using an AI service."""
import re
from modules.speech_math import MATH_SPANS, number_words, integer_words, speak_math_tags, speak_formula, WORDS, SYMBOLS, protect_math

APOSTROPHES = "'‘’ʻʼ`´′ʹ＇"
ORDINAL_NOUNS = 'maktab|sinf|kurs|dars|mashq|savol|misol|bob|bet|mavzu|qism|topshiriq|chorak|semestr|o‘rin|oʻrin|qavat|sahifa|yil|kun|son'

def normalize_uzbek(value):
    # U+02BB is a LETTER, not removable quotation punctuation.
    return re.sub(r'([oOgG])['+re.escape(APOSTROPHES)+r']+',r'\1ʻ',str(value or ''))

def ordinal_uzbek(value):
    word=integer_words(int(value),'uz')
    return word+('nchi' if word.endswith(('a','i','o','u')) else 'inchi')

def tag_raw_math(value):
    """Keep legacy untagged TeX atoms readable, including nested arguments."""
    source,restore=protect_math(value);parts=[];previous=0
    args={'frac':2,'dfrac':2,'tfrac':2,'cfrac':2,'binom':2,'sqrt':1,'text':1,'mathrm':1,'mathbf':1,'vec':1,'overline':1,'bar':1,'dot':1}
    def group(pos,opening='{',closing='}'):
        while pos<len(source) and source[pos].isspace():pos+=1
        if pos>=len(source) or source[pos]!=opening:return pos
        depth=1;pos+=1
        while pos<len(source) and depth:
            if source[pos]==opening:depth+=1
            elif source[pos]==closing:depth-=1
            pos+=1
        return pos
    for match in re.finditer(r'\\([A-Za-z]+)',source):
        if match.start()<previous:continue
        start=match.start();end=match.end()
        if match[1] in ('frac','dfrac','tfrac','cfrac'):
            whole=re.search(r'(?<![\w.,])\d+\s*$',source[previous:start])
            if whole:start=previous+whole.start()
        if match[1]=='sqrt' and end<len(source) and source[end]=='[':end=group(end,'[',']')
        for _ in range(args.get(match[1],0)):end=group(end)
        while end<len(source) and source[end] in '_^':
            end+=1;end=group(end) if end<len(source) and source[end]=='{' else min(end+1,len(source))
        parts.extend((source[previous:start],'[lat]'+source[start:end]+'[/lat]'));previous=end
    parts.append(source[previous:]);return restore(''.join(parts))

def _prose(value,language):
    text=str(value)
    text=re.sub(r'<(?:/?[A-Za-z][^>]*|!--[\s\S]*?--)>',' ',text)
    text=re.sub(r'\[/?(?:uz|ru|en)\]','',text,flags=re.I)
    text=re.sub(r'https?://\S+|www\.\S+',' ',text)
    text=re.sub(r'(?<!\w)(?:[A-Za-z]|\d+)\s*\^\s*(?:\{[A-Za-z0-9+ -]+\}|[A-Za-z]|\d+)',lambda m:speak_formula(m[0],language),text)
    if language=='uz':
        text=normalize_uzbek(text)
        text=re.sub(r'°\s*C\b',' daraja Selsiy ',text)
        # Before math minus: 1-maktab is an ordinal, 1-2 stays subtraction.
        text=re.sub(r'(?<![\w.,])([0-9]{1,9})\s*[-‑–]\s*('+ORDINAL_NOUNS+r')(?=[^\W\d_]*\b)',
                    lambda m:ordinal_uzbek(m[1])+' '+m[2],text,flags=re.I)
        text=re.sub(r'(?<![\wʻʼ])c(?![\wʻʼ])','si',text,flags=re.I)
        units={'km/soat':'kilometr soatiga','sm²':'kvadrat santimetr','sm2':'kvadrat santimetr',
               'm²':'kvadrat metr','m2':'kvadrat metr','sm³':'kub santimetr','sm3':'kub santimetr',
               'm³':'kub metr','m3':'kub metr','kg':'kilogramm','gr':'gramm','mm':'millimetr',
               'sm':'santimetr','km':'kilometr','ml':'millilitr','l':'litr','m':'metr'}
        for unit,spoken in units.items():
            text=re.sub(r'(?<![^\W\d_])'+re.escape(unit)+r'(?!\w)',lambda _:' '+spoken+' ',text)
    w=WORDS[language]
    for symbol,key in SYMBOLS.items():
        if symbol=='-':
            # Preserve word hyphens such as ko‘p-qavatli and hyphenated English.
            text=re.sub(r'(?<![^\W\d_])-|-(?![^\W\d_])',' '+w[key]+' ',text)
        else:text=text.replace(symbol,' '+w[key]+' ')
    # Work on digit strings: 0,0001 must never become 0.1 by rounding/cleanup.
    text=re.sub(r'(?<!\w)(?<!\d[.,])\d+(?:[.,]\d+)?(?!\d|[.,]\d)',lambda m:number_words(m[0],language),text)
    text=re.sub(r'_{2,}',{'uz':' bo‘sh joy ','ru':' пропуск ','en':' blank '}[language],text)
    return text

def prepare_speech(value,language='uz'):
    language=language if language in WORDS else 'uz'
    value=tag_raw_math(str(value or ''))
    # Expand formulas separately so mathematical minus/cases cannot be mistaken
    # for an ordinal, and formula letter names are not rewritten as prose.
    parts=[];previous=0
    for match in MATH_SPANS.finditer(str(value or '')):
        parts.append(_prose(str(value)[previous:match.start()],language))
        parts.append(speak_math_tags(match[0],language));previous=match.end()
    parts.append(_prose(str(value or '')[previous:],language))
    text=''.join(parts)
    if language=='uz':text=normalize_uzbek(text)
    return re.sub(r'\s+([,.;:!?])',r'\1',re.sub(r'\s+',' ',text)).strip()

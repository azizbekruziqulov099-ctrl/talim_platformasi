"""Display-only translation: bounded input and protected formula/code fragments."""
import re
from collections import Counter
TARGETS={'uz','uz-Cyrl','ru','en','tr','kk'}
MARKER=re.compile(r'ZXQKB\d+QXZ')
PROTECTED=re.compile(r'```[\s\S]*?```|`[^`\n]+`|\[lat\][\s\S]*?\[/lat\]|\$\$[\s\S]*?\$\$|\$[^$\n]+\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]|\\[a-zA-Z]+(?:\{(?:[^{}]|\{[^{}]*\})*\})*(?:[_^](?:\{[^{}]*\}|\w))*|https?://[^\s<>]+|\{(?:v\d+|[A-Za-z][A-Za-z0-9_]*)\}')
def normalize_source(value):return re.sub(r'\s+',' ',re.sub('[‘’ʻʼ`]',"'",value)).strip()
def validate_payload(body,registered=None):
    if not isinstance(body,dict):raise ValueError('Invalid translation request')
    target,texts=body.get('target'),body.get('texts')
    if not isinstance(target,str) or target not in TARGETS:raise ValueError('Unsupported language')
    if not isinstance(texts,list) or not 1<=len(texts)<=50:raise ValueError('Invalid text count')
    if any(not isinstance(t,str) or not t.strip() or len(t)>12000 or '\x00' in t or MARKER.search(t) for t in texts):raise ValueError('Invalid text')
    if sum(map(len,texts))>20000:raise ValueError('Text limit exceeded')
    if registered is not None:
        if any(normalize_source(t) not in registered for t in texts):raise ValueError('Unregistered interface text')
        texts=[normalize_source(t) for t in texts]
    return target,texts

def mask_text(text):
    if MARKER.search(text):raise ValueError('Reserved translation marker')
    saved={}
    def replace(match):
        key=f'ZXQKB{len(saved)}QXZ';saved[key]=match.group(0);return key
    return PROTECTED.sub(replace,text),saved

_MAP=dict(zip('abdefghijklmnopqrstuvxyz','абдефгҳижклмнопқрстувхйз'))
_MAP.update({"o'":'ў',"g'":'ғ','sh':'ш','ch':'ч',"yo'":'йў','ye':'е','yo':'ё','yu':'ю','ya':'я',"'":'ъ'})
def uzbek_cyrillic(text):
    def convert(match):
        token=match.group(0);lower=token.lower();translated=_MAP.get(lower,token)
        if lower=='e' and (match.start()==0 or not re.match("[a-z']",match.string[match.start()-1],re.I)):translated='э'
        if not token[0].isupper():return translated
        return translated.upper() if token.isupper() else translated[:1].upper()+translated[1:]
    return re.sub(r"yo'|o'|g'|sh|ch|ye|yo|yu|ya|[a-z']",convert,re.sub('[‘’ʻʼ`]',"'",text),flags=re.I)

def restore_text(text,saved,cyrillic=False):
    if not isinstance(text,str) or Counter(MARKER.findall(text))!=Counter(saved.keys()):raise ValueError('Translation changed protected text')
    pieces=MARKER.split(text);keys=MARKER.findall(text);out=[]
    for i,piece in enumerate(pieces):
        out.append(uzbek_cyrillic(piece) if cyrillic else piece)
        if i<len(keys):out.append(saved[keys[i]])
    return ''.join(out)

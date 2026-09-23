"""Deterministic spoken mathematics. Never evaluate a formula or call an AI API."""
import re

MATH_SPANS = re.compile(r'\[lat\][\s\S]*?\[/lat\]|\$\$[\s\S]*?\$\$|\$[^$\n]+\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]', re.I)
SMALL = {
    'uz': 'nol bir ikki uch to‘rt besh olti yetti sakkiz to‘qqiz'.split(),
    'en': 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(),
    'ru': 'ноль один два три четыре пять шесть семь восемь девять десять одиннадцать двенадцать тринадцать четырнадцать пятнадцать шестнадцать семнадцать восемнадцать девятнадцать'.split(),
}
TENS = {
    'uz': ['', 'o‘n', 'yigirma', 'o‘ttiz', 'qirq', 'ellik', 'oltmish', 'yetmish', 'sakson', 'to‘qson'],
    'en': ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'],
    'ru': ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто'],
}
HUNDREDS_RU = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']

def _plural(n, forms):
    return forms[2] if 11 <= n % 100 <= 14 else forms[0] if n % 10 == 1 else forms[1] if 2 <= n % 10 <= 4 else forms[2]

def _feminine(words):
    return re.sub(r'\bодин$', 'одна', re.sub(r'\bдва$', 'две', words))

def _russian_genitive(words):
    forms=dict(zip(
        'ноль один одна два две три четыре пять шесть семь восемь девять десять одиннадцать двенадцать тринадцать четырнадцать пятнадцать шестнадцать семнадцать восемнадцать девятнадцать двадцать тридцать сорок пятьдесят шестьдесят семьдесят восемьдесят девяносто сто двести триста четыреста пятьсот шестьсот семьсот восемьсот девятьсот тысяча тысячи миллион миллиона миллиард миллиарда'.split(),
        'нуля одного одной двух двух трёх четырёх пяти шести семи восьми девяти десяти одиннадцати двенадцати тринадцати четырнадцати пятнадцати шестнадцати семнадцати восемнадцати девятнадцати двадцати тридцати сорока пятидесяти шестидесяти семидесяти восьмидесяти девяноста ста двухсот трёхсот четырёхсот пятисот шестисот семисот восьмисот девятисот тысячи тысяч миллиона миллионов миллиарда миллиардов'.split()))
    return ' '.join(forms.get(word,word) for word in words.split())

def integer_words(n, language):
    if n < 0:return {'uz':'minus ', 'en':'minus ', 'ru':'минус '}[language] + integer_words(-n, language)
    if n < len(SMALL[language]):return SMALL[language][n]
    if n >= 10**12:return str(n)  # Let the selected TTS voice pronounce very large numbers.
    parts = []
    for scale, uz, en, ru in [(10**9,'milliard','billion',('миллиард','миллиарда','миллиардов')),
                              (10**6,'million','million',('миллион','миллиона','миллионов')),
                              (1000,'ming','thousand',('тысяча','тысячи','тысяч'))]:
        if n >= scale:
            count, n = divmod(n, scale)
            words = integer_words(count, language)
            if language == 'ru':words = (_feminine(words) if scale == 1000 else words) + ' ' + _plural(count, ru)
            elif language == 'uz':words = ('' if count == 1 and scale == 1000 else words + ' ') + uz
            else:words += ' ' + en
            parts.append(words)
    if n >= 100:
        count, n = divmod(n, 100)
        parts.append(HUNDREDS_RU[count] if language == 'ru' else
                     ('' if count == 1 else SMALL['uz'][count] + ' ') + 'yuz' if language == 'uz' else SMALL['en'][count] + ' hundred')
    if 0 < n < len(SMALL[language]):parts.append(SMALL[language][n])
    elif n:
        count, n = divmod(n, 10);parts.append(TENS[language][count])
        if n:parts.append(SMALL[language][n])
    return ' '.join(parts)

def number_words(value, language):
    pieces = re.split(r'[.,]', value, maxsplit=1)
    whole = integer_words(int(pieces[0]), language)
    if len(pieces) == 1:return whole
    fraction = pieces[1]
    if language == 'uz' and len(fraction) <= 6:
        return f'{whole} butun {integer_words(10**len(fraction), language)}dan {integer_words(int(fraction), language)}'
    separator = ' point ' if language == 'en' else ' запятая ' if language == 'ru' else ' vergul '
    return whole + separator + ' '.join(SMALL[language][int(digit)] for digit in fraction)

WORDS = {
 'uz': dict(plus='plyus', minus='minus', times='ko‘paytirilgan', divide='bo‘lingan', equals='teng',
  less='kichik', greater='katta', le='kichik yoki teng', ge='katta yoki teng', ne='teng emas', approx='taxminan teng',
  pm='plyus yoki minus', percent='foiz', infinity='cheksizlik', degree='gradus',
  fraction='surati {a}, maxraji {b} bo‘lgan kasr', root='kvadrat ildiz ostida {x}', cube_root='kub ildiz ostida {x}', nth_root='{n} darajali ildiz ostida {x}',
  squared='{x}ning kvadrati', cubed='{x}ning kubi', power='{x}ning {n} darajasi',
  group='qavs ochiladi, {x}, qavs yopiladi', quantity='qavsdagi {x} ifoda', index='{x}, indeks {n}', factorial='{x} faktorial',
  absolute='{x}ning moduli', binomial='{n} tadan {k} tadan tanlashlar soni',
  sum='yig‘indi', prod='ko‘paytma', integral='integral', limit='limit', lower='{x} dan', upper='{x} gacha', tends='intiladi',
  sin='sinus', cos='kosinus', tan='tangens', cot='kotangens', ln='natural logarifm', log='logarifm',
  arcsin='arksinus', arccos='arkkosinus', arctan='arktangens', in_='tegishli', notin='tegishli emas', union='birlashma', intersection='kesishma',
  forall='har qanday', exists='mavjud', implies='bundan kelib chiqadi', iff='faqat va faqat', empty='bo‘sh to‘plam', partial='xususiy hosila',
  vector='{x} vektori', overline='{x} ustida chiziq', dot='{x}ning vaqt bo‘yicha hosilasi', row='keyingi qator'),
 'en': dict(plus='plus', minus='minus', times='times', divide='divided by', equals='equals',
  less='less than', greater='greater than', le='less than or equal to', ge='greater than or equal to', ne='not equal to', approx='approximately equals',
  pm='plus or minus', percent='percent', infinity='infinity', degree='degrees',
  fraction='the fraction with numerator {a} and denominator {b}', root='square root of {x}', cube_root='cube root of {x}', nth_root='root of order {n} of {x}',
  squared='{x} squared', cubed='{x} cubed', power='{x} to the power of {n}',
  group='open parenthesis, {x}, close parenthesis', quantity='the quantity {x}', index='{x} sub {n}', factorial='{x} factorial',
  absolute='absolute value of {x}', binomial='{n} choose {k}',
  sum='sum', prod='product', integral='integral', limit='limit', lower='from {x}', upper='to {x}', tends='tends to',
  sin='sine', cos='cosine', tan='tangent', cot='cotangent', ln='natural logarithm', log='logarithm',
  arcsin='arcsine', arccos='arccosine', arctan='arctangent', in_='belongs to', notin='does not belong to', union='union', intersection='intersection',
  forall='for every', exists='there exists', implies='implies', iff='if and only if', empty='empty set', partial='partial derivative',
  vector='vector {x}', overline='{x} with an overline', dot='time derivative of {x}', row='next row'),
 'ru': dict(plus='плюс', minus='минус', times='умножить на', divide='разделить на', equals='равно',
  less='меньше', greater='больше', le='меньше или равно', ge='больше или равно', ne='не равно', approx='приблизительно равно',
  pm='плюс или минус', percent='процентов', infinity='бесконечность', degree='градусов',
  fraction='дробь: в числителе {a}, в знаменателе {b}', root='квадратный корень из {x}', cube_root='кубический корень из {x}', nth_root='корень степени {n} из {x}',
  squared='{x} в квадрате', cubed='{x} в кубе', power='{x} в степени {n}',
  group='скобка открывается, {x}, скобка закрывается', quantity='выражение {x} в скобках', index='{x} с индексом {n}', factorial='{x} факториал',
  absolute='модуль {x}', binomial='число сочетаний из {n} по {k}',
  sum='сумма', prod='произведение', integral='интеграл', limit='предел', lower='от {x}', upper='до {x}', tends='стремится к',
  sin='синус', cos='косинус', tan='тангенс', cot='котангенс', ln='натуральный логарифм', log='логарифм',
  arcsin='арксинус', arccos='арккосинус', arctan='арктангенс', in_='принадлежит', notin='не принадлежит', union='объединение', intersection='пересечение',
  forall='для любого', exists='существует', implies='следовательно', iff='тогда и только тогда', empty='пустое множество', partial='частная производная',
  vector='вектор {x}', overline='{x} с чертой', dot='производная {x} по времени', row='следующая строка'),
}
SYMBOLS = dict(zip(['+','-','*','×','·','/','÷','=','<','>','≤','≥','≠','≈','±','%','∞','°','→','∈','∉','∪','∩','∀','∃'],
 ['plus','minus','times','times','times','divide','divide','equals','less','greater','le','ge','ne','approx','pm','percent','infinity','degree','tends','in_','notin','union','intersection','forall','exists']))
COMMANDS = dict(times='times', cdot='times', div='divide', le='le', leq='le', ge='ge', geq='ge', neq='ne', ne='ne',
 approx='approx', sim='approx', pm='pm', infty='infinity', to='tends', rightarrow='tends', in_='in_', notin='notin', cup='union', cap='intersection',
 forall='forall', exists='exists', implies='implies', Rightarrow='implies', iff='iff', Leftrightarrow='iff', emptyset='empty', varnothing='empty', partial='partial', circ='degree')
COMMANDS['in'] = 'in_'
GREEK = {
 'alpha':('alfa','alpha','альфа'), 'beta':('beta','beta','бета'), 'gamma':('gamma','gamma','гамма'),
 'delta':('delta','delta','дельта'), 'epsilon':('epsilon','epsilon','эпсилон'), 'theta':('teta','theta','тета'),
 'lambda':('lambda','lambda','лямбда'), 'mu':('myu','mu','мю'), 'nu':('nyu','nu','ню'), 'pi':('pi','pi','пи'),
 'rho':('ro','rho','ро'), 'sigma':('sigma','sigma','сигма'), 'tau':('tau','tau','тау'), 'phi':('fi','phi','фи'),
 'chi':('xi','chi','хи'), 'psi':('psi','psi','пси'), 'omega':('omega','omega','омега'),
}
GREEK_SYMBOLS = dict(zip('αβγδεθλμνπρστφχψω', GREEK))
LETTERS = {
 'uz': 'a be se de e ef ge ash i jot ka el em en o pe ku er es te u ve dubl ve iks igrik zet'.split(),
 'ru': ['а','бэ','цэ','дэ','е','эф','гэ','аш','и','йот','ка','эль','эм','эн','о','пэ','ку','эр','эс','тэ','у','вэ','дубль вэ','икс','игрек','зет'],
 'en': ['ay','bee','see','dee','ee','eff','gee','aitch','eye','jay','kay','el','em','en','oh','pee','cue','are','ess','tee','you','vee','double you','x','why','zee'],
}
# Keep multiword letter names in one slot.
LETTERS['uz'] = ['a','be','se','de','e','ef','ge','ash','i','jot','ka','el','em','en','o','pe','ku','er','es','te','u','ve','dubl ve','iks','igrik','zet']
TOKENS = re.compile(r'\\[A-Za-z]+|\\.|\d+(?:[.,]\d+)?|[A-Za-z]+|[А-Яа-яЁё]+|[^\s]')

class MathReader:
    def __init__(self, value, language):
        value = value.replace('−','-').replace('²','^{2}').replace('³','^{3}')
        value = re.sub(r'\\(?:left|right|displaystyle|textstyle|scriptstyle|limits)\b', '', value)
        self.tokens = TOKENS.findall(value);self.pos = 0;self.language = language;self.words = WORDS[language]

    def peek(self):return self.tokens[self.pos] if self.pos < len(self.tokens) else ''
    def take(self):
        token = self.peek()
        if token:self.pos += 1
        return token

    def sequence(self, close='', depth=0):
        if depth > 40:raise ValueError('Formula juda chuqur ichma-ich yozilgan.')
        parts = []
        while self.peek() and self.peek() != close:
            if self.peek() == '/' and parts:
                self.take();parts.append(('fraction', parts.pop(), self.atom(depth+1)));continue
            node=self.atom(depth+1)
            if parts and parts[-1][0]=='number' and node[0]=='fraction' and self.simple_number(node[1]) is not None and self.simple_number(node[2]) is not None:
                parts.append(('mixed',parts.pop(),node))
            else:parts.append(node)
        if close and self.peek() == close:self.take()
        return ('seq', parts)

    def argument(self, depth):
        if self.peek() == '{':self.take();return self.sequence('}', depth+1)
        return self.primary(depth+1)

    def primary(self, depth):
        if depth > 40:raise ValueError('Formula juda chuqur ichma-ich yozilgan.')
        token = self.take()
        if not token:return ('text','')
        if token in ('{','(','['):
            body = self.sequence({'{':'}','(':')','[':']'}[token], depth+1)
            return body if token == '{' else ('group', body)
        if token == '|':return ('absolute', self.sequence('|', depth+1))
        command = token[1:] if token.startswith('\\') else token
        if command in ('frac','dfrac','tfrac','cfrac'):return ('fraction', self.argument(depth), self.argument(depth))
        if command == 'binom':return ('binomial', self.argument(depth), self.argument(depth))
        if command in ('sqrt','√'):
            degree = None
            if self.peek() == '[':self.take();degree = self.sequence(']', depth+1)
            return ('root', self.argument(depth), degree)
        if command in ('sum','prod','int','lim'):
            lower = upper = None
            while self.peek() in ('_','^'):
                marker = self.take();value = self.argument(depth)
                if marker == '_':lower = value
                else:upper = value
            return ('big', {'int':'integral','lim':'limit'}.get(command,command), lower, upper)
        if command in ('vec','overline','bar','dot'):return ({'vec':'vector','bar':'overline'}.get(command,command), self.argument(depth))
        if command in ('mathrm','mathbf','mathit','mathbb','mathcal','operatorname'):return self.argument(depth)
        if command in ('text','textrm','mbox') and self.peek() == '{':
            self.take();text=[];nested=1
            while self.peek() and nested:
                part=self.take()
                if part=='{':nested+=1
                elif part=='}':nested-=1
                if nested:text.append(part)
            return ('text',' '.join(text))
        if re.fullmatch(r'\d+(?:[.,]\d+)?', token):return ('number',token)
        return ('symbol', command)

    def atom(self, depth):
        node = self.primary(depth)
        while self.peek() in ('^','_','!'):
            marker = self.take()
            node = ('factorial',node) if marker == '!' else ('power' if marker == '^' else 'index',node,self.argument(depth))
        return node

    def simple_number(self, node):
        if node[0] == 'seq' and len(node[1]) == 1:return self.simple_number(node[1][0])
        return int(node[1]) if node[0] == 'number' and node[1].isdigit() else None

    def render(self, node):
        kind = node[0];w = self.words;lang = self.language
        if kind == 'seq':return ' '.join(filter(None,(self.render(child) for child in node[1])))
        if kind == 'text':return node[1]
        if kind == 'number':return number_words(node[1],lang)
        if kind == 'symbol':
            value=node[1]
            if value in (',',';',':'):return ','
            if value in ('!','quad','qquad','enspace','thinspace',' ') :return ''
            if value == '\\':return w['row']
            if value in SYMBOLS:return w[SYMBOLS[value]]
            if value in COMMANDS:return w[COMMANDS[value]]
            if value in w:return w[value]
            greek = GREEK_SYMBOLS.get(value, value.lower().removeprefix('var'))
            if greek in GREEK:return GREEK[greek][{'uz':0,'en':1,'ru':2}[lang]]
            if re.fullmatch('[A-Za-z]+',value):return ' '.join(LETTERS[lang][ord(c.lower())-97] for c in value)
            return value
        if kind == 'fraction':
            a,b=self.simple_number(node[1]),self.simple_number(node[2])
            if a is not None and b is not None:
                if lang=='uz':return f'{integer_words(b,lang)}dan {integer_words(a,lang)}'
                if lang=='en':
                    forms={2:('half','halves'),3:('third','thirds'),4:('quarter','quarters'),5:('fifth','fifths'),6:('sixth','sixths'),7:('seventh','sevenths'),8:('eighth','eighths'),9:('ninth','ninths'),10:('tenth','tenths')}
                    if b in forms:return integer_words(a,lang)+' '+forms[b][0 if a==1 else 1]
                    return integer_words(a,lang)+' over '+integer_words(b,lang)
                forms={2:('вторая','вторых'),3:('третья','третьих'),4:('четвёртая','четвёртых'),5:('пятая','пятых'),6:('шестая','шестых'),7:('седьмая','седьмых'),8:('восьмая','восьмых'),9:('девятая','девятых'),10:('десятая','десятых')}
                if b in forms:return _feminine(integer_words(a,lang))+' '+forms[b][0 if a%10==1 and a%100!=11 else 1]
            return w['fraction'].format(a=self.render(node[1]),b=self.render(node[2]))
        if kind == 'mixed':
            whole=self.render(node[1]);fraction=self.render(node[2])
            if lang=='ru':return _feminine(whole)+' целых '+fraction
            return whole+(' butun ' if lang=='uz' else ' and ')+fraction
        if kind == 'root':
            degree=self.simple_number(node[2]) if node[2] else 2
            key='root' if degree==2 else 'cube_root' if degree==3 else 'nth_root'
            value=self.render(node[1]);order=self.render(node[2]) if node[2] else ''
            if lang=='ru' and self.simple_number(node[1]) is not None:value=_russian_genitive(value)
            if key=='nth_root' and degree is not None:
                if lang=='uz':order += 'nchi' if order.endswith(('a','i','o','u')) else 'inchi'
                if lang=='en' and degree in (4,5,6,7,8,9,10):
                    return {4:'fourth',5:'fifth',6:'sixth',7:'seventh',8:'eighth',9:'ninth',10:'tenth'}[degree]+' root of '+value
                if lang=='ru' and degree in (4,5,6,7,8,9,10):
                    return 'корень '+{4:'четвёртой',5:'пятой',6:'шестой',7:'седьмой',8:'восьмой',9:'девятой',10:'десятой'}[degree]+' степени из '+value
            return w[key].format(x=value,n=order)
        if kind in ('power','index'):
            base=node[1];value=self.render(base)
            if base[0]=='group':value=w['quantity'].format(x=self.render(base[1]))
            number=self.simple_number(node[2]);key='squared' if kind=='power' and number==2 else 'cubed' if kind=='power' and number==3 else kind
            exponent=self.render(node[2])
            if kind=='power' and exponent==w['degree']:return value+' '+exponent
            if lang=='uz' and kind=='power' and number is not None and number not in (2,3):
                exponent += 'nchi' if exponent.endswith(('a','i','o','u')) else 'inchi'
            return w[key].format(x=value,n=exponent)
        if kind == 'big':
            parts=[w[node[1]]]
            if node[1]=='limit' and node[2]:
                return parts[0]+{'uz':', ','en':' as ','ru':', при условии '}[lang]+self.render(node[2])
            if node[2]:parts.append(w['lower'].format(x=self.render(node[2])))
            if node[3]:parts.append(w['upper'].format(x=self.render(node[3])))
            return ' '.join(parts)
        if kind == 'binomial':return w[kind].format(n=self.render(node[1]),k=self.render(node[2]))
        return w[kind].format(x=self.render(node[1]))

def speak_formula(value, language='uz'):
    language = language if language in WORDS else 'uz'
    reader = MathReader(str(value),language)
    text = reader.render(reader.sequence())
    return re.sub(r'\s+([,.;:])',r'\1',re.sub(r'\s+',' ',text)).strip()

def speak_math_tags(value, language='uz'):
    def replace(match):
        raw=match.group(0)
        formula=raw[5:-6] if raw.lower().startswith('[lat]') else raw[2:-2] if raw.startswith(('$$','\\(','\\[')) else raw[1:-1]
        return ' '+speak_formula(formula,language)+' '
    return MATH_SPANS.sub(replace,str(value or ''))

def protect_math(value):
    formulas=[]
    def mask(match):
        formulas.append(match.group(0));return f'\ue000{len(formulas)-1}\ue001'
    text=MATH_SPANS.sub(mask,value)
    def restore(part):return re.sub(r'\ue000(\d+)\ue001',lambda m:formulas[int(m[1])],part)
    return text,restore

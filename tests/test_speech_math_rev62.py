"""Check exact words before TTS, without a live voice or paid service."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from modules.speech_math import speak_formula, speak_math_tags, number_words
from modules.speech_language import split_speech_text, SPEAKERS

class MathSpeechTests(unittest.TestCase):
    def test_same_formula_uses_three_native_mathematics_vocabularies(self):
        expected={'uz':'iksning kvadrati plyus ikkidan bir teng kvadrat ildiz ostida to‘rt',
                  'ru':'икс в квадрате плюс одна вторая равно квадратный корень из четырёх',
                  'en':'x squared plus one half equals square root of four'}
        for language,words in expected.items():
            with self.subTest(language=language):
                self.assertEqual(speak_formula(r'x^2+\frac{1}{2}=\sqrt{4}',language),words)

    def test_nested_fraction_and_root_keep_numerator_denominator_and_order(self):
        value=r'\frac{x+1}{\sqrt{\frac{2}{3}}}'
        for language,terms in [('uz',['surati','iks','maxraji','kvadrat ildiz','uchdan ikki']),
                               ('ru',['числителе','икс','знаменателе','квадратный корень','две третьих']),
                               ('en',['numerator','x','denominator','square root','two thirds'])]:
            words=speak_formula(value,language)
            for term in terms:self.assertIn(term,words)
            self.assertNotRegex(words,r'[\\{}]')

    def test_fraction_power_factorial_bounds_and_greek(self):
        self.assertIn('cubed',speak_formula('(x+1)^3','en'))
        self.assertIn('cube root',speak_formula(r'\sqrt[3]{8}','en'))
        self.assertEqual(speak_formula(r'\sqrt[4]{16}','ru'),'корень четвёртой степени из шестнадцати')
        self.assertIn('икс с индексом один',speak_formula('x_1','ru'))
        self.assertEqual(speak_formula('5!','uz'),'besh faktorial')
        self.assertEqual(speak_formula(r'90^\circ','uz'),'to‘qson gradus')
        self.assertEqual(speak_formula(r'\alpha+\pi','ru'),'альфа плюс пи')
        self.assertIn('from eye equals one to en',speak_formula(r'\sum_{i=1}^{n}i^2','en'))
        self.assertEqual(speak_formula(r'2\frac{1}{2}','uz'),'ikki butun ikkidan bir')

    def test_plain_prose_is_preserved_and_only_math_markup_is_spoken(self):
        self.assertEqual(speak_math_tags('Hello, world!', 'en'),'Hello, world!')
        text=speak_math_tags('Вычислите [lat]2+3=5[/lat].','ru')
        self.assertIn('Вычислите',text);self.assertIn('два плюс три равно пять',text)
        self.assertNotIn('[lat]',text)

    def test_decimal_digits_and_large_numbers_are_not_changed(self):
        self.assertEqual(number_words('2.05','uz'),'ikki butun yuzdan besh')
        self.assertEqual(number_words('2.05','en'),'two point zero five')
        self.assertEqual(number_words('2.05','ru'),'два запятая ноль пять')
        self.assertEqual(number_words('21000','ru'),'двадцать одна тысяча')

    def test_language_tags_win_over_selected_language_and_multiline_formula_is_atomic(self):
        text=r'[ru]Формула [lat]\frac{1}{2}[/lat].[/ru] [en][lat]x^2[/lat][/en]'
        pieces=split_speech_text(text,'uz')
        self.assertEqual([p[0] for p in pieces],['ru','en'])
        self.assertIn('одна вторая',speak_math_tags(pieces[0][1],pieces[0][0]))
        self.assertIn('x squared',speak_math_tags(pieces[1][1],pieces[1][0]))
        formula='[lat]x^2\n+1[/lat]'
        self.assertEqual(split_speech_text('Найдите значение. '+formula)[-1],('uz',formula))

    def test_real_synthesize_function_passes_spoken_math_to_the_matching_voice(self):
        source=Path(__file__).resolve().parents[1]/'modules/admin_speech.py'
        node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and n.name=='synthesize')
        namespace={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
        calls=[]
        class Communicate:
            def __init__(self,text,voice,rate):calls.append((text,voice,rate))
            async def stream(self):yield {'type':'audio','data':b'mp3'}
        with patch.dict('sys.modules',{'edge_tts':SimpleNamespace(Communicate=Communicate)}):
            result=asyncio.run(namespace['synthesize']('[ru][lat]x^2[/lat][/ru] [en][lat]2+3[/lat][/en]','ogil','+0%','uz'))
        self.assertEqual(result,b'mp3mp3')
        self.assertIn('икс в квадрате',calls[0][0]);self.assertEqual(calls[0][1],SPEAKERS['ru']['ogil'])
        self.assertIn('two plus three',calls[1][0]);self.assertEqual(calls[1][1],SPEAKERS['en']['ogil'])

    def test_deep_formula_has_bounded_recovery(self):
        with self.assertRaisesRegex(ValueError,'chuqur'):
            speak_formula(r'\sqrt{'*70+'2'+'}'*70,'uz')

if __name__=='__main__':unittest.main()

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from modules.speech_pronunciation import prepare_speech
from modules.speech_language import split_speech_text

ROOT=Path(__file__).resolve().parents[1]

class PronunciationTests(unittest.TestCase):
    def test_uzbek_letters_are_letters_not_discarded_quotes(self):
        for mark in "'‘’ʻʼ`´′ʹ＇":
            self.assertEqual(prepare_speech(f"G{mark}isht o{mark}quvchi"),'Gʻisht oʻquvchi')
        self.assertEqual(prepare_speech('c C ch Ch celsius abc'),'si si ch Ch celsius abc')

    def test_decimal_precision_and_ordinals_survive_replay(self):
        text='1-maktab, 2-sinf, 6-kurs; 0,0001. -0.0001.'
        expected='birinchi maktab, ikkinchi sinf, oltinchi kurs; nol butun oʻn mingdan bir. minus nol butun oʻn mingdan bir.'
        for _ in range(3):self.assertEqual(prepare_speech(text),expected)
        self.assertEqual(prepare_speech('1-2=-1'),'bir minus ikki teng minus bir')

    def test_formulas_use_outer_language_only_and_preserve_literal_text(self):
        text='Hello. Привет. [ru][lat]x+y[/lat][/ru] [en][lat]x+y[/lat][/en] [lat]x+y+c=0{,}0001[/lat]'
        pieces=split_speech_text(text)
        self.assertEqual([lang for lang,_ in pieces],['uz','uz','ru','en','uz'])
        self.assertEqual(prepare_speech(pieces[2][1],pieces[2][0]),'икс плюс игрек')
        self.assertEqual(prepare_speech(pieces[3][1],pieces[3][0]),'x plus why')
        self.assertEqual(prepare_speech(pieces[4][1],pieces[4][0]),'iks plyus igrik plyus si teng nol butun oʻn mingdan bir')
        self.assertEqual(prepare_speech(r'[lat]\text{g‘isht, o‘quvchi}[/lat]'),'gʻisht, oʻquvchi')
        self.assertEqual(prepare_speech(r'2\frac{1}{2}; x^2'),'ikki butun ikkidan bir; iksning kvadrati')

    def test_actual_admin_and_public_entrypoints_use_the_same_prepared_words(self):
        module=ROOT/'modules/admin_speech.py'
        node=next(n for n in ast.parse(module.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and n.name=='synthesize')
        ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(module),'exec'),ns)
        calls=[]
        class Communicate:
            def __init__(self,text,voice,rate):calls.append((text,voice))
            async def stream(self):yield {'type':'audio','data':b'mp3'}
        text="1-maktab, g'isht, 0,0001. [lat]x+y[/lat]"
        with patch.dict('sys.modules',{'edge_tts':SimpleNamespace(Communicate=Communicate)}):
            asyncio.run(ns['synthesize'](text,'qiz','+0%'))
        self.assertTrue(all(voice=='uz-UZ-MadinaNeural' for _,voice in calls))
        self.assertEqual(' '.join(value for value,_ in calls),prepare_speech(text))
        public=ROOT/'samtm_platform.py'
        node=next(n for n in ast.parse(public.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_ovoz_uchun_tayyorla_til')
        ns={'_ovoz_tilini_tuzat':lambda value:value};exec(compile(ast.Module(body=[node],type_ignores=[]),str(public),'exec'),ns)
        self.assertEqual(ns['_ovoz_uchun_tayyorla_til'](text,'uz'),prepare_speech(text))

if __name__=='__main__':unittest.main()

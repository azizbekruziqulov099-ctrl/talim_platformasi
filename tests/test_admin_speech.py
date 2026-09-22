"""Validate real admin speech handlers without sending text to an external service."""
import ast,asyncio,hashlib,importlib.util,math,re,unittest
from pathlib import Path
from types import SimpleNamespace
from test_curriculum_catalog import Router
from test_curriculum_scope import HTTPException

class SpeechTests(unittest.TestCase):
 def setUp(self):
  path=Path(__file__).resolve().parents[1]/'modules/admin_speech.py'
  nodes=[n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
  self.ns={'asyncio':asyncio,'hashlib':hashlib,'math':math,'re':re,'importlib':importlib,'APIRouter':Router,'HTTPException':HTTPException,'Request':object,'Response':lambda **kwargs:SimpleNamespace(**kwargs)}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),self.ns)
  self.calls=[];self.cache={}
  async def synth(*args):self.calls.append(args);return b'mp3'
  self.ns['synthesize']=synth
  def admin(token):
   if token!='admin':raise HTTPException(403,'Faqat admin')
  platform=SimpleNamespace(_admin_tekshir=admin,_ovoz_keshdan_ol=self.cache.get,_ovoz_keshga_qoy=lambda k,v:self.cache.update({k:v}))
  self.routes=self.ns['create_router'](platform).routes
  self.platform=platform
 def read(self,payload,token='admin'):return asyncio.run(self.routes['/read'](payload,token))
 def test_read_preserves_uzbek_punctuation_and_paragraphs(self):
  text='Salom, dunyo!\n\nBugun o‘zbekcha dars.'
  response=self.read({'text':text,'voice':'ogil','rate':0.75})
  self.assertEqual(self.calls,[(text,'ogil','-25%')]);self.assertEqual(response.content,b'mp3')
  self.assertEqual(response.headers['Cache-Control'],'private, no-store')
 def test_server_checks_admin_for_status_and_read(self):
  for token in ('student','teacher',''):
   with self.assertRaises(HTTPException) as error:self.read({'text':'Matn'},token)
   self.assertEqual(error.exception.status_code,403)
   with self.assertRaises(HTTPException):self.routes['/status'](token)
  self.assertEqual(self.calls,[])
 def test_oversized_or_blank_text_is_rejected_instead_of_truncated(self):
  for text in ('','   ','a'*1501,123,None):
   with self.subTest(text_type=type(text)),self.assertRaises(HTTPException) as error:self.read({'text':text})
   self.assertEqual(error.exception.status_code,400)
  self.assertEqual(self.calls,[])
 def test_voice_and_rate_are_validated(self):
  for options in ({'voice':'invalid'},{'rate':0.1},{'rate':3},{'rate':'nan'},{'rate':'abc'}):
   with self.assertRaises(HTTPException):self.read({'text':'Matn',**options})
  self.assertEqual(self.calls,[])
 def test_cache_separates_voice_and_rate(self):
  self.read({'text':'Matn'});self.read({'text':'Matn'});self.read({'text':'Matn','voice':'ogil'});self.read({'text':'Matn','rate':2})
  self.assertEqual(len(self.calls),3)
 def test_upstream_failure_returns_readable_error(self):
  async def fail(*args):raise RuntimeError('upstream')
  self.ns['synthesize']=fail
  with self.assertRaises(HTTPException) as error:self.read({'text':'Matn'})
  self.assertEqual(error.exception.status_code,503);self.assertEqual(self.cache,{})

if __name__=='__main__':unittest.main()

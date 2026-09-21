"""Real translation core/service/router with HTTP/response adapters; no network or DB."""
import ast,asyncio,hashlib,html,json,os,time,unittest
from pathlib import Path
from collections import OrderedDict
from threading import Lock
from types import SimpleNamespace
from unittest.mock import patch
from modules.translation_core import validate_payload,mask_text,restore_text,normalize_source
ROOT=Path(__file__).resolve().parents[1]
class HTTPException(Exception):
 def __init__(self,status_code,detail,headers=None):super().__init__(detail);self.status_code=status_code;self.detail=detail;self.headers=headers or {}
class Response:
 def __init__(self,content,headers=None):self.content=content;self.headers=headers or {}
class Router:
 def __init__(self,**kwargs):self.routes={}
 def route(self,path):
  def register(fn):self.routes[path]=fn;return fn
  return register
 get=post=route
class Request:
 def __init__(self,body):self.body=json.dumps(body).encode();self.client=SimpleNamespace(host='test')
 async def stream(self):yield self.body
async def thread(fn,*args):return fn(*args)
class CoreTests(unittest.TestCase):
 def test_all_six_languages(self):
  for target in ('uz','uz-Cyrl','ru','en','tr','kk'):self.assertEqual(validate_payload({'target':target,'texts':['Salom']})[0],target)
 def test_strict_body_target_and_array(self):
  for body in (None,[],{'target':[],'texts':['a']},{'target':'xx','texts':['a']},{'target':'en','texts':'a'},{'target':'en','texts':[]}):
   with self.subTest(body=body),self.assertRaises(ValueError):validate_payload(body)
 def test_limits_empty_markers_and_nul(self):
  for texts in ([' '],['a\0b'],['ZXQKB0QXZ'],['x'*12001],['a']*51,['x'*11000]*2):
   with self.subTest(length=len(texts)),self.assertRaises(ValueError):validate_payload({'target':'en','texts':texts})
 def test_public_ui_whitelist_normalizes_but_rejects_private_text(self):
  allow={normalize_source('O‘quvchi')};self.assertEqual(validate_payload({'target':'en','texts':[" O'quvchi "]},allow)[1],["O'quvchi"])
  with self.assertRaises(ValueError):validate_payload({'target':'en','texts':['Private student message']},allow)
 def test_formulas_code_urls_and_placeholders_survive(self):
  text='Salom $x^2$ $$a+b$$ \\(y=2\\) [lat]z_1[/lat] `answer=A` ```x=1``` https://example.test/path {v0} {name}'
  masked,saved=mask_text(text);self.assertNotIn('x^2',masked);self.assertEqual(restore_text(masked,saved),text)
 def test_missing_duplicated_and_unknown_markers_fail_closed(self):
  masked,saved=mask_text('Value $x$')
  for text in ('Value',masked+masked,masked+' ZXQKB99QXZ'):
   with self.assertRaises(ValueError):restore_text(text,saved)
 def test_cyrillic_changes_prose_only(self):
  masked,saved=mask_text('Salom $x$ {v0} `uz`');self.assertEqual(restore_text(masked,saved,True),'Салом $x$ {v0} `uz`')
class ServiceTests(unittest.IsolatedAsyncioTestCase):
 @classmethod
 def setUpClass(cls):
  path=ROOT/'modules/translation_api.py';tree=ast.parse(path.read_text());tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
  cls.namespace=dict(asyncio=asyncio,hashlib=hashlib,html=html,json=json,os=os,time=time,OrderedDict=OrderedDict,Path=Path,Lock=Lock,validate_payload=validate_payload,mask_text=mask_text,restore_text=restore_text,HTTPException=HTTPException,APIRouter=Router,Request=Request,Header=lambda **k:'',JSONResponse=Response,run_in_threadpool=thread,__file__=str(path))
  exec(compile(tree,str(path),'exec'),cls.namespace)
 def setUp(self):
  self.calls=[];owner=self
  class Client:
   def __init__(self,**kwargs):pass
   async def __aenter__(self):return self
   async def __aexit__(self,*args):pass
   async def post(self,url,params,json):
    owner.calls.append((url,params,json));await asyncio.sleep(0)
    if hasattr(owner,'provider_error'):raise owner.provider_error
    rows=getattr(owner,'provider_rows',[{'translatedText':'EN '+value} for value in json['q']])
    return SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'data':{'translations':rows}})
  self.namespace['httpx']=SimpleNamespace(AsyncClient=Client)
  with patch.dict(os.environ,{},clear=True):self.service=self.namespace['TranslationService'](key='secret-key')
  self.auth_calls=[]
  def auth(token):
   self.auth_calls.append(token)
   if token!='valid':raise HTTPException(401,'Invalid token')
   return 7
  self.routes=self.namespace['create_router'](SimpleNamespace(_jwt_tekshir=auth),self.service).routes
 async def test_provider_uses_server_key_text_format_and_restores_formula(self):
  result=await self.service.google('en',['Question $x^2$ {v0}']);self.assertEqual(result,['EN Question $x^2$ {v0}'])
  url,params,body=self.calls[0];self.assertEqual(url,'https://translation.googleapis.com/language/translate/v2');self.assertEqual(params,{'key':'secret-key'});self.assertEqual(body['format'],'text');self.assertNotIn('x^2',body['q'][0])
 async def test_missing_key_503_without_provider_call(self):
  self.service.key=''
  with self.assertRaises(HTTPException) as e:await self.service.google('en',['Salom'])
  self.assertEqual(e.exception.status_code,503);self.assertEqual(self.calls,[])
 async def test_public_cache_deduplicates_requests(self):
  a,b=await asyncio.gather(self.service.interface('en',['Salom','Salom']),self.service.interface('en',['Salom','Salom']))
  self.assertEqual(a,b);self.assertEqual(len(self.calls),1);await self.service.interface('en',['Salom']);self.assertEqual(len(self.calls),1)
 async def test_provider_failure_redacts_details(self):
  self.provider_error=ValueError('secret-key with private student text')
  with self.assertRaises(HTTPException) as e:await self.service.google('en',['Private'])
  self.assertEqual(e.exception.status_code,503);self.assertNotIn('secret',e.exception.detail);self.assertNotIn('Private',e.exception.detail)
 async def test_invalid_response_and_formula_loss_fail_closed(self):
  for rows in ([],[{'translatedText':None}],[{'translatedText':'Lost formula'}]):
   self.provider_rows=rows
   with self.assertRaises(HTTPException):await self.service.google('en',['Formula $x$'])
 async def test_daily_budget_and_request_rate_limits(self):
  self.service.consume('test',1,1,60)
  with self.assertRaises(HTTPException) as e:self.service.consume('test',1,1,60)
  self.assertEqual(e.exception.status_code,429);self.assertIn('Retry-After',e.exception.headers)
  self.service.daily_limit=1
  with self.assertRaises(HTTPException):await self.service.google('en',['Too long'])
  self.assertEqual(self.calls,[])
 async def test_redis_limit_failure_is_closed(self):
  def failed(*args):raise ConnectionError('redis unavailable')
  self.service.redis=SimpleNamespace(eval=failed)
  with self.assertRaises(HTTPException) as e:self.service.consume('test',1,10,60)
  self.assertEqual(e.exception.status_code,503)
 async def test_ui_route_rejects_unregistered_private_text(self):
  with self.assertRaises(HTTPException) as e:await self.routes['/interface'](Request({'target':'en','texts':['Private never registered 8472']}))
  self.assertEqual(e.exception.status_code,400);self.assertEqual(self.calls,[])
 async def test_ui_route_works_without_user_login(self):
  result=await self.routes['/interface'](Request({'target':'en','texts':['Saqlash']}))
  self.assertEqual(result.content['translations'],['EN Saqlash']);self.assertEqual(self.auth_calls,[])
 async def test_content_requires_login_and_explicit_consent(self):
  for authorization,consent,code in [('',True,401),('Bearer invalid',True,401),('Bearer valid',False,400),('Bearer valid','true',400)]:
   with self.subTest(authorization=authorization,consent=consent),self.assertRaises(HTTPException) as e:await self.routes['/content'](Request({'target':'en','texts':['Source'],'consent':consent}),authorization)
   self.assertEqual(e.exception.status_code,code)
  self.assertEqual(self.calls,[])
 async def test_private_content_never_enters_shared_cache(self):
  body={'target':'en','texts':['Private topic'],'consent':True}
  for _ in range(2):
   result=await self.routes['/content'](Request(body),'Bearer valid');self.assertEqual(result.content['translations'],['EN Private topic']);self.assertEqual(result.headers['Cache-Control'],'private, no-store')
  self.assertEqual(len(self.calls),2);self.assertFalse(self.service.cache)
 async def test_body_size_limit_precedes_provider(self):
  request=Request({});request.body=b' '*100001
  with self.assertRaises(HTTPException) as e:await self.routes['/interface'](request)
  self.assertEqual(e.exception.status_code,413);self.assertEqual(self.calls,[])
 async def test_status_exposes_configuration_only(self):
  result=self.routes['/status']();self.assertTrue(result.content['configured']);self.assertNotIn('secret-key',json.dumps(result.content));self.assertEqual(self.calls,[])
if __name__=='__main__':unittest.main()

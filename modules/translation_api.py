"""Google Cloud Translation bridge. No database content is read or changed."""
import asyncio,hashlib,html,json,os,time
from collections import OrderedDict
from pathlib import Path
from threading import Lock
import httpx
from fastapi import APIRouter,Header,HTTPException,Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from .translation_core import validate_payload,mask_text,restore_text
NO_STORE={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}
GOOGLE_URL='https://translation.googleapis.com/language/translate/v2'

class TranslationService:
    def __init__(self,key=None,transport=None):
        self.key=key if key is not None else os.getenv('GOOGLE_TRANSLATE_API_KEY','').strip()
        self.registered=frozenset(json.loads(Path(__file__).with_name('interface_sources.json').read_text()))
        self.cache=OrderedDict();self.limits=OrderedDict();self.lock=Lock();self.flights={};self.semaphore=asyncio.Semaphore(4);self.transport=transport
        self.daily_limit=max(20000,int(os.getenv('TRANSLATION_DAILY_CHARACTER_LIMIT','1000000')));self.redis=None
        if os.getenv('REDIS_URL'):
            import redis
            self.redis=redis.Redis.from_url(os.environ['REDIS_URL'],socket_connect_timeout=1,socket_timeout=1,decode_responses=True)
    def consume(self,identity,cost,ceiling,window):
        now=int(time.time());key=f'kb:translation:v4:limit:{window}:{now//window}:{hashlib.sha256(identity.encode()).hexdigest()}'
        if self.redis is not None:
            try:used=self.redis.eval("local n=redis.call('INCRBY',KEYS[1],ARGV[1]); if n==tonumber(ARGV[1]) then redis.call('EXPIRE',KEYS[1],ARGV[2]); end; return n",1,key,cost,window+1)
            except Exception as exc:raise HTTPException(503,'Translation temporarily unavailable',headers=NO_STORE) from exc
        else:
            with self.lock:
                self.limits[key]=self.limits.get(key,0)+cost;used=self.limits[key]
                while len(self.limits)>10000:self.limits.popitem(last=False)
        if used>ceiling:raise HTTPException(429,'Translation rate limit reached',headers={**NO_STORE,'Retry-After':str(window-now%window)})
    def cache_key(self,target,text):return 'kb:translation:v4:ui:'+hashlib.sha256(f'{target}\0{text}'.encode()).hexdigest()
    def cached(self,target,text):
        key=self.cache_key(target,text)
        if key in self.cache:self.cache.move_to_end(key);return self.cache[key]
        if self.redis is not None:
            try:return self.redis.get(key)
            except Exception:return None
        return None
    def remember(self,target,text,value):
        key=self.cache_key(target,text);self.cache[key]=value
        while len(self.cache)>30000:self.cache.popitem(last=False)
        if self.redis is not None:
            try:self.redis.setex(key,30*86400,value)
            except Exception:pass
    async def google(self,target,texts):
        if not self.key:raise HTTPException(503,'Translation is not configured',headers=NO_STORE)
        try:masked=[mask_text(text) for text in texts]
        except ValueError as exc:raise HTTPException(400,'Invalid translation text',headers=NO_STORE) from exc
        self.consume('provider-daily',sum(map(len,texts)),self.daily_limit,86400)
        payload={'q':[m[0] for m in masked],'target':'uz' if target=='uz-Cyrl' else target,'format':'text'}
        try:
            async with self.semaphore:
                async with httpx.AsyncClient(timeout=15,transport=self.transport) as client:
                    response=await client.post(GOOGLE_URL,params={'key':self.key},json=payload)
            response.raise_for_status();rows=response.json()['data']['translations']
            if not isinstance(rows,list) or len(rows)!=len(texts):raise ValueError('Invalid translation count')
            output=[]
            for row,(_,saved) in zip(rows,masked):
                value=row.get('translatedText')
                if not isinstance(value,str) or not value.strip() or len(value)>60000:raise ValueError('Invalid translation')
                output.append(restore_text(html.unescape(value),saved,target=='uz-Cyrl'))
            return output
        except HTTPException:raise
        except Exception as exc:raise HTTPException(503,'Translation temporarily unavailable',headers=NO_STORE) from exc
    async def interface(self,target,texts):
        if target=='uz':return texts
        missing=list(dict.fromkeys(t for t in texts if self.cached(target,t) is None))
        if missing:
            fingerprint=hashlib.sha256(json.dumps([target,missing]).encode()).hexdigest();task=self.flights.get(fingerprint)
            if task is None:
                async def run():
                    result=await self.google(target,missing)
                    for source,value in zip(missing,result):self.remember(target,source,value)
                task=asyncio.create_task(run());self.flights[fingerprint]=task
                def finished(done):
                    self.flights.pop(fingerprint,None)
                    if not done.cancelled():done.exception()  # retrieve errors even if the requesting client disconnects
                task.add_done_callback(finished)
            await asyncio.shield(task)
        return [self.cached(target,t) for t in texts]

def create_router(platform,service=None):
    router=APIRouter(prefix='/api/translation',tags=['translation']);service=service or TranslationService()
    async def payload(request):
        raw=bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw)>100000:raise HTTPException(413,'Translation request too large',headers=NO_STORE)
        try:return json.loads(raw)
        except (ValueError,UnicodeError) as exc:raise HTTPException(400,'Invalid translation request',headers=NO_STORE) from exc
    @router.get('/status')
    def status():return JSONResponse({'configured':bool(service.key),'provider':'google_cloud','content_requires_login':True},headers=NO_STORE)
    @router.post('/interface')
    async def interface(request:Request):
        try:target,texts=validate_payload(await payload(request),service.registered)
        except ValueError as exc:raise HTTPException(400,str(exc),headers=NO_STORE) from exc
        service.consume('ui:'+(request.client.host if request.client else 'unknown'),1,240,60)
        result=await service.interface(target,texts)
        return JSONResponse({'translations':result,'provider':'google_cloud'},headers=NO_STORE)
    @router.post('/content')
    async def content(request:Request,authorization:str=Header(default='')):
        if not authorization.startswith('Bearer '):raise HTTPException(401,'Sign in to translate content',headers=NO_STORE)
        uid=await run_in_threadpool(platform._jwt_tekshir,authorization[7:]);body=await payload(request)
        if not isinstance(body,dict) or body.get('consent') is not True:raise HTTPException(400,'Content translation must be enabled',headers=NO_STORE)
        try:target,texts=validate_payload(body)
        except ValueError as exc:raise HTTPException(400,str(exc),headers=NO_STORE) from exc
        service.consume('content:'+str(uid),sum(map(len,texts)),100000,3600)
        return JSONResponse({'translations':await service.google(target,texts),'provider':'google_cloud'},headers=NO_STORE)
    return router

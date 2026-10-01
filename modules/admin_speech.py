"""Admin reading and dictation, keeping the original language."""
import asyncio
import hashlib
import importlib.util
import math
import re
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

def speech_input(payload):
    text=payload.get('text')
    if not isinstance(text,str) or not text.strip():raise ValueError('O‘qish uchun matn kiriting')
    if len(text)>1500:raise ValueError('Bitta ovoz bo‘lagi 1500 belgidan oshmasligi kerak')
    text=re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',text.replace('\r\n','\n')).strip()
    voice=payload.get('voice','qiz')
    if voice not in ('qiz','ogil'):raise ValueError('Ovoz turini tanlang')
    try:rate=float(payload.get('rate',1))
    except (ValueError,TypeError):raise ValueError('O‘qish tezligi noto‘g‘ri')
    if not math.isfinite(rate) or not 0.5<=rate<=2:raise ValueError('Tezlik 0.5–2 oralig‘ida bo‘lishi kerak')
    return text,voice,f'{round((rate-1)*100):+d}%'

def selected_language(value='auto'):
    if value not in ('auto','uz','ru','en'):
        raise ValueError('Tilni avtomatik, o‘zbekcha, ruscha yoki inglizcha tanlang')
    return value

async def synthesize(text,voice,rate,language='auto'):
    import edge_tts
    from modules.speech_language import split_speech_text, SPEAKERS
    from modules.speech_pronunciation import prepare_speech
    audio=bytearray()
    for part_language,part in split_speech_text(text,language):
        spoken=prepare_speech(part,part_language)
        async for chunk in edge_tts.Communicate(spoken,SPEAKERS[part_language][voice],rate=rate).stream():
            if chunk['type']=='audio':audio.extend(chunk['data'])
    if not audio:raise RuntimeError('Empty speech response')
    return bytes(audio)

def stt_keys(platform=None):
    """Kalitlar har chaqiruvda o'qiladi: Railway'da kalit qo'shilsa qayta deploy shart emas."""
    import os
    attr=getattr(platform,'GROQ_API_KALIT',None)
    groq=str(attr if attr is not None else os.getenv('GROQ_API_KEY','') or '').strip()
    return {'groq':groq,'openai':str(os.getenv('OPENAI_API_KEY','') or '').strip(),
            'gemini':str(os.getenv('GEMINI_API_KEY','') or os.getenv('GOOGLE_AI_API_KEY','') or '').strip()}


def stt_key_list(name, first):
    """REV96: bir xizmatga bir nechta kalit — GROQ_API_KEYS=k1,k2 (yoki GROQ_API_KEY ichida vergul bilan).
    Bepul limit tugasa keyingi kalitga o'tiladi; kunlik limit shu bilan ko'payadi."""
    import os
    raw=','.join([first or '',os.getenv(f'{name.upper()}_API_KEYS','') or ''])
    out=[]
    for key in raw.split(','):
        key=key.strip()
        if key and key not in out:out.append(key)
    return out


def stt_providers(platform=None):
    """Kaliti bor xizmatlar tartibi. STT_PROVIDERS=openai,gemini,groq bilan o'zgartirish mumkin.
    Limiti tugagan / kaliti qabul qilinmagan xizmat bir muddat oxiriga suriladi (qayta-qayta urilmaydi)."""
    import os
    keys=stt_keys(platform)
    order=[x.strip().lower() for x in (os.getenv('STT_PROVIDERS') or 'groq,openai,gemini').split(',') if x.strip()]
    order+=[x for x in ('groq','openai','gemini') if x not in order]
    result=[(name,key) for name in order if name in keys for key in stt_key_list(name,keys[name])]
    cooling=stt_cooldowns()
    import time
    now=time.time()
    ready=[p for p in result if cooling.get(stt_slot(*p),{}).get('until',0)<=now]
    resting=sorted([p for p in result if p not in ready],key=lambda p:cooling[stt_slot(*p)]['until'])
    return ready+resting


def stt_cooldowns(_store={}):
    """Jarayon ichidagi holat: {slot: {'until': vaqt, 'reason': matn, 'at': vaqt}}."""
    return _store


def stt_slot(name, key):
    return f'{name}:{hashlib.sha256(str(key).encode()).hexdigest()[:10]}'


def stt_rest(name, key, exc):
    """Xato turiga qarab xizmatni dam oldirish: limit — 2 daq (yoki Retry-After), kalit xatosi — 30 daq."""
    import time
    response=getattr(exc,'response',None)
    status=getattr(response,'status_code',None)
    seconds={429:120,401:1800,403:1800,404:900}.get(status,0)
    if status==429:
        try:seconds=max(20,min(3600,int(float((response.headers or {}).get('retry-after') or 120))))
        except (TypeError,ValueError,AttributeError):seconds=120
    reason={429:'limit',401:'kalit',403:'ruxsat',404:'model'}.get(status,type(exc).__name__)
    entry={'until':time.time()+seconds,'reason':reason,'at':time.time()}
    stt_cooldowns()[stt_slot(name,key)]=entry
    return entry


def stt_health(platform=None):
    """Adminga: qaysi xizmat ishlayapti, qaysi biri dam olmoqda va nega."""
    import time
    now=time.time()
    out=[]
    for name,key in stt_providers(platform):
        c=stt_cooldowns().get(stt_slot(name,key)) or {}
        out.append({'xizmat':name,'kalit':'…'+str(key)[-4:],'holat':'dam' if c.get('until',0)>now else 'tayyor',
                    'sabab':c.get('reason',''),'qolgan_soniya':max(0,int(c.get('until',0)-now))})
    return out


async def _whisper_compatible(url, model, audio, content_type, extension, api_key, language, verbose):
    import httpx
    fields={'model':model,'response_format':'verbose_json' if verbose else 'json','temperature':'0'}
    if language!='auto':fields['language']=language
    async with httpx.AsyncClient(timeout=60) as client:
        response=await client.post(url,headers={'Authorization':f'Bearer {api_key}'},
            files={'file':(f'dictation.{extension}',audio,content_type)},data=fields)
        response.raise_for_status()
        data=response.json()
    if not isinstance(data,dict) or not isinstance(data.get('text'),str):
        raise ValueError('stt_invalid_response')
    return {'text':data['text'].strip(),'language':str(data.get('language') or (language if language!='auto' else ''))}


async def _gemini(audio, content_type, api_key, language):
    import base64
    import os
    import httpx
    model=os.getenv('GEMINI_STT_MODEL','gemini-2.5-flash')
    # Gemini webm/mp4 ni ham qabul qiladi; mime aniq yuboriladi.
    mime={'video/webm':'audio/webm','video/mp4':'audio/mp4','audio/x-wav':'audio/wav','audio/mp3':'audio/mpeg',
          'audio/x-m4a':'audio/mp4','audio/m4a':'audio/mp4','audio/x-flac':'audio/flac'}.get(content_type,content_type)
    prompt=("Transcribe this audio exactly as spoken, in the original language (Uzbek Latin script for Uzbek). "
            "Do not translate, do not summarise, do not add anything. Return only the spoken text.")
    hint={'uz':' The speech is in Uzbek.','ru':' The speech is in Russian.','en':' The speech is in English.'}.get(language,'')
    body={'contents':[{'parts':[{'text':prompt+hint},{'inline_data':{'mime_type':mime,'data':base64.b64encode(audio).decode()}}]}],
          'generationConfig':{'temperature':0}}
    async with httpx.AsyncClient(timeout=60) as client:
        response=await client.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
            headers={'x-goog-api-key':api_key},json=body)
        response.raise_for_status()
        data=response.json()
    try:
        text=''.join(p.get('text','') for p in data['candidates'][0]['content']['parts'])
    except (KeyError,IndexError,TypeError) as exc:
        raise ValueError('stt_invalid_response') from exc
    return {'text':text.strip(),'language':language if language!='auto' else ''}


async def transcribe_audio(audio, content_type, extension, api_key, language='auto', provider='groq', model=None):
    import os
    if provider=='openai':
        return await _whisper_compatible('https://api.openai.com/v1/audio/transcriptions',
            os.getenv('OPENAI_STT_MODEL','whisper-1'),audio,content_type,extension,api_key,language,
            os.getenv('OPENAI_STT_MODEL','whisper-1')=='whisper-1')
    if provider=='gemini':
        return await _gemini(audio,content_type,api_key,language)
    return await _whisper_compatible('https://api.groq.com/openai/v1/audio/transcriptions',
        model or os.getenv('GROQ_STT_MODEL','whisper-large-v3'),audio,content_type,extension,api_key,language,True)


async def transcribe_any(audio, content_type, extension, providers, language='auto'):
    """Birinchi ishlagan xizmat natijasi. Kalit/limit/ulanish xatosida keyingisiga o'tiladi."""
    last=None
    for name,key in providers:
        try:
            result=await transcribe_audio(audio,content_type,extension,key,language,name)
            result['provider']=name
            stt_cooldowns().pop(stt_slot(name,key),None)
            return result
        except Exception as exc:
            last=exc
            status=getattr(getattr(exc,'response',None),'status_code',None)
            if name=='groq' and status==429:
                # REV96: Groq'da har modelning limiti alohida — «turbo» model bilan shu kalitda yana urinamiz.
                try:
                    result=await transcribe_audio(audio,content_type,extension,key,language,name,model='whisper-large-v3-turbo')
                    result['provider']='groq-turbo'
                    return result
                except Exception as exc2:
                    if getattr(exc2,'response',None) is not None:last=exc2   # aks holda asl limit xatosi aytiladi
            try:stt_rest(name,key,last)
            except Exception:pass
            continue
    raise last or RuntimeError('no_provider')


def transcription_error(exc):
    """Return an actionable error without exposing provider bodies or credentials."""
    status=getattr(getattr(exc,'response',None),'status_code',None)
    if status==401:return HTTPException(503,'STT_PROVIDER_KEY: Ovoz tanish kaliti qabul qilinmadi. Backenddagi OPENAI_API_KEY / GEMINI_API_KEY / GROQ_API_KEY qiymatini tekshiring.')
    if status==403:return HTTPException(503,'STT_PROVIDER_ACCESS: Ovoz tanish xizmati bu kalitga ruxsat bermadi. Kalit ruxsatlarini tekshiring.')
    if status==429:return HTTPException(429,'STT_LIMIT: Ovoz tanish xizmati limiti tugadi. Birozdan so‘ng shu yozuvni qayta yuboring.')
    if status==413:return HTTPException(413,'STT_TOO_LARGE: Ovoz yozuvi xizmat uchun juda katta. Qisqaroq yozuv yuboring.')
    if status in (400,415,422):return HTTPException(422,'STT_AUDIO_REJECTED: Ovoz xizmati yozuvni qabul qilmadi. Yozuvni tinglab tekshiring yoki MP3, WAV, M4A faylini yuboring.')
    if status==404:return HTTPException(503,'STT_MODEL: Ovoz tanish modeli yoki xizmat manzili topilmadi.')
    if isinstance(exc,TimeoutError) or 'timeout' in type(exc).__name__.lower():
        return HTTPException(504,'STT_TIMEOUT: Ovoz tanish xizmati vaqtida javob bermadi. Shu yozuvni qayta yuboring.')
    if isinstance(exc,ValueError):return HTTPException(502,'STT_RESPONSE: Ovoz xizmati matnli javob qaytarmadi. Shu yozuvni qayta yuboring.')
    return HTTPException(503,'STT_CONNECTION: Backend ovoz tanish xizmatidan javob ololmadi. Ulanishni tekshirib, shu yozuvni qayta yuboring.')

def create_router(platform):
    return speech_router(platform,'/api/admin/speech',platform._admin_tekshir)


def teacher_check(platform):
    """REV96: o'qituvchi (va admin) uchun ham — matnni ovozga, ovozni matnga."""
    def check(token):
        uid=platform._jwt_tekshir(token)
        conn=platform._db();cur=conn.cursor()
        try:
            cur.execute('SELECT role FROM users WHERE user_id=%s',(uid,))
            row=cur.fetchone() or {}
            if row.get('role') in ('oqituvchi','admin'):return uid
            cur.execute('SELECT 1 FROM admin_akkaunt WHERE uid=%s',(uid,))
            if cur.fetchone():return uid
        finally:
            cur.close();conn.close()
        raise HTTPException(403,'Ovozli matn faqat o‘qituvchilar uchun')
    return check


def create_teacher_router(platform):
    return speech_router(platform,'/api/speech',teacher_check(platform),'oqituvchi')


def speech_router(platform, prefix, check, rol='admin'):
    router=APIRouter(prefix=prefix,tags=['speech'])

    @router.get('/status')
    def status(token:str):
        check(token)
        providers=stt_providers(platform)
        return {'admin':True,'allowed':True,'reading_available':importlib.util.find_spec('edge_tts') is not None,
                'language':'uz','languages':['uz','ru','en'],'revision':96,
                'dictation_available':bool(providers),
                'providers':list(dict.fromkeys(name for name,_ in providers)),
                'rol':rol,'holat':stt_health(platform) if rol=='admin' else []}

    @router.post('/read')
    async def read(payload:dict,token:str):
        check(token)
        try:
            text,voice,rate=speech_input(payload)
            language=selected_language(payload.get('language','auto'))
        except ValueError as exc:raise HTTPException(400,str(exc)) from exc
        key=hashlib.sha256(f'admin-speech-v64\0{language}\0{voice}\0{rate}\0{text}'.encode()).hexdigest()
        audio=platform._ovoz_keshdan_ol(key)
        if audio is None:
            try:
                args=(text,voice,rate) if language=='auto' else (text,voice,rate,language)
                audio=await asyncio.wait_for(synthesize(*args),timeout=45)
            except ValueError as exc:raise HTTPException(400,str(exc)) from exc
            except ImportError as exc:raise HTTPException(503,'Serverda ovoz xizmati o‘rnatilmagan') from exc
            except Exception as exc:raise HTTPException(503,'Ovoz xizmati javob bermadi. Qayta urinib ko‘ring.') from exc
            platform._ovoz_keshga_qoy(key,audio)
        return Response(content=audio,media_type='audio/mpeg',headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @router.post('/dictate')
    async def dictate(request:Request,token:str,language:str='auto'):
        check(token)
        try:language=selected_language(language)
        except ValueError as exc:raise HTTPException(400,str(exc)) from exc
        providers=stt_providers(platform)
        if not providers:raise HTTPException(503,'STT_NOT_CONFIGURED: Ovoz tanish xizmati ulanmagan. Backendda OPENAI_API_KEY, GEMINI_API_KEY yoki GROQ_API_KEY dan kamida bittasini qo‘shing.')
        content_type=request.headers.get('content-type','').split(';',1)[0].strip().lower()
        extensions={'audio/webm':'webm','video/webm':'webm','audio/ogg':'ogg','audio/mp4':'mp4','video/mp4':'mp4',
                    'audio/wav':'wav','audio/x-wav':'wav','audio/mpeg':'mp3','audio/mp3':'mp3',
                    'audio/m4a':'m4a','audio/x-m4a':'m4a','audio/flac':'flac','audio/x-flac':'flac'}
        if content_type not in extensions:raise HTTPException(415,'Bu ovoz fayli turi qo‘llanmaydi')
        audio=bytearray()
        async for chunk in request.stream():
            if len(audio)+len(chunk)>8*1024*1024:raise HTTPException(413,'Ovoz yozuvi 8 MB dan oshmasligi kerak')
            audio.extend(chunk)
        if not audio:raise HTTPException(400,'Ovoz yozuvi bo‘sh')
        try:
            result=await transcribe_any(bytes(audio),content_type,extensions[content_type],providers,language)
        except Exception as exc:raise transcription_error(exc) from exc
        if not isinstance(result,dict) or not isinstance(result.get('text'),str):
            raise HTTPException(502,'STT_RESPONSE: Ovoz xizmati noto‘g‘ri javob qaytardi. Shu yozuvni qayta yuboring.')
        if not result['text'].strip():raise HTTPException(422,'STT_NO_SPEECH: Yozuvda nutq topilmadi. Saqlangan yozuvni tinglab tekshiring.')
        return result

    return router

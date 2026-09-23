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
    from modules.speech_math import speak_math_tags
    audio=bytearray()
    for part_language,part in split_speech_text(text,language):
        spoken=speak_math_tags(part,part_language)
        async for chunk in edge_tts.Communicate(spoken,SPEAKERS[part_language][voice],rate=rate).stream():
            if chunk['type']=='audio':audio.extend(chunk['data'])
    if not audio:raise RuntimeError('Empty speech response')
    return bytes(audio)

async def transcribe_audio(audio, content_type, extension, api_key, language='auto'):
    import httpx
    fields={'model':'whisper-large-v3','response_format':'verbose_json','temperature':'0'}
    if language != 'auto':fields['language']=language
    async with httpx.AsyncClient(timeout=60) as client:
        response=await client.post('https://api.groq.com/openai/v1/audio/transcriptions',
            headers={'Authorization':f'Bearer {api_key}'},
            files={'file':(f'dictation.{extension}',audio,content_type)},
            # A chosen language is authoritative; auto omits the hint. Never translate.
            data=fields)
        response.raise_for_status()
        data=response.json()
    if not isinstance(data,dict) or not isinstance(data.get('text'),str):
        raise ValueError('stt_invalid_response')
    return {'text':data['text'].strip(),'language':str(data.get('language') or '')}

def transcription_error(exc):
    """Return an actionable error without exposing provider bodies or credentials."""
    status=getattr(getattr(exc,'response',None),'status_code',None)
    if status==401:return HTTPException(503,'STT_PROVIDER_KEY: Groq kaliti qabul qilinmadi. Backenddagi GROQ_API_KEY qiymatini yangilang.')
    if status==403:return HTTPException(503,'STT_PROVIDER_ACCESS: Groq ovoz modeliga ruxsat bermadi. Groq loyihasidagi model ruxsatlarini tekshiring.')
    if status==429:return HTTPException(429,'STT_LIMIT: Ovoz tanish xizmati limiti tugadi. Birozdan so‘ng shu yozuvni qayta yuboring yoki Groq limitingizni tekshiring.')
    if status==413:return HTTPException(413,'STT_TOO_LARGE: Ovoz yozuvi xizmat uchun juda katta. Qisqaroq yozuv yuboring.')
    if status in (400,415,422):return HTTPException(422,'STT_AUDIO_REJECTED: Ovoz xizmati yozuvni qabul qilmadi. Yozuvni tinglab tekshiring yoki MP3, WAV, M4A faylini yuboring.')
    if status==404:return HTTPException(503,'STT_MODEL: Ovoz tanish modeli yoki xizmat manzili topilmadi.')
    if isinstance(exc,TimeoutError) or 'timeout' in type(exc).__name__.lower():
        return HTTPException(504,'STT_TIMEOUT: Ovoz tanish xizmati vaqtida javob bermadi. Shu yozuvni qayta yuboring.')
    if isinstance(exc,ValueError):return HTTPException(502,'STT_RESPONSE: Ovoz xizmati matnli javob qaytarmadi. Shu yozuvni qayta yuboring.')
    return HTTPException(503,'STT_CONNECTION: Backend ovoz tanish xizmatidan javob ololmadi. Ulanishni tekshirib, shu yozuvni qayta yuboring.')

def create_router(platform):
    router=APIRouter(prefix='/api/admin/speech',tags=['admin-speech'])

    @router.get('/status')
    def status(token:str):
        platform._admin_tekshir(token)
        return {'admin':True,'reading_available':importlib.util.find_spec('edge_tts') is not None,
                'language':'auto','languages':['uz','ru','en'],'revision':57,
                'dictation_available':bool(str(getattr(platform,'GROQ_API_KALIT','') or '').strip())}

    @router.post('/read')
    async def read(payload:dict,token:str):
        platform._admin_tekshir(token)
        try:
            text,voice,rate=speech_input(payload)
            language=selected_language(payload.get('language','auto'))
        except ValueError as exc:raise HTTPException(400,str(exc)) from exc
        key=hashlib.sha256(f'admin-speech-v62\0{language}\0{voice}\0{rate}\0{text}'.encode()).hexdigest()
        audio=platform._ovoz_keshdan_ol(key)
        if audio is None:
            try:
                args=(text,voice,rate) if language=='auto' else (text,voice,rate,language)
                audio=await asyncio.wait_for(synthesize(*args),timeout=45)
            except ImportError as exc:raise HTTPException(503,'Serverda ovoz xizmati o‘rnatilmagan') from exc
            except Exception as exc:raise HTTPException(503,'Ovoz xizmati javob bermadi. Qayta urinib ko‘ring.') from exc
            platform._ovoz_keshga_qoy(key,audio)
        return Response(content=audio,media_type='audio/mpeg',headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @router.post('/dictate')
    async def dictate(request:Request,token:str,language:str='auto'):
        platform._admin_tekshir(token)
        try:language=selected_language(language)
        except ValueError as exc:raise HTTPException(400,str(exc)) from exc
        api_key=str(getattr(platform,'GROQ_API_KALIT','') or '').strip()
        if not api_key:raise HTTPException(503,'STT_NOT_CONFIGURED: Ovoz tanish xizmati ulanmagan. Backendda GROQ_API_KEY sozlanishi kerak.')
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
            args=(bytes(audio),content_type,extensions[content_type],api_key)
            result=await transcribe_audio(*args) if language=='auto' else await transcribe_audio(*args,language)
        except Exception as exc:raise transcription_error(exc) from exc
        if not isinstance(result,dict) or not isinstance(result.get('text'),str):
            raise HTTPException(502,'STT_RESPONSE: Ovoz xizmati noto‘g‘ri javob qaytardi. Shu yozuvni qayta yuboring.')
        if not result['text'].strip():raise HTTPException(422,'STT_NO_SPEECH: Yozuvda nutq topilmadi. Saqlangan yozuvni tinglab tekshiring.')
        return result

    return router

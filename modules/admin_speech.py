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

async def synthesize(text,voice,rate):
    import edge_tts
    from modules.speech_language import split_speech_text, SPEAKERS
    audio=bytearray()
    for language,part in split_speech_text(text):
        async for chunk in edge_tts.Communicate(part,SPEAKERS[language][voice],rate=rate).stream():
            if chunk['type']=='audio':audio.extend(chunk['data'])
    if not audio:raise RuntimeError('Empty speech response')
    return bytes(audio)

async def transcribe_audio(audio, content_type, extension, api_key):
    import httpx
    async with httpx.AsyncClient(timeout=60) as client:
        response=await client.post('https://api.groq.com/openai/v1/audio/transcriptions',
            headers={'Authorization':f'Bearer {api_key}'},
            files={'file':(f'dictation.{extension}',audio,content_type)},
            # Omit language so multilingual Whisper detects it. Never translate to English.
            data={'model':'whisper-large-v3','response_format':'verbose_json','temperature':'0'})
        response.raise_for_status()
        data=response.json()
    return {'text':str(data.get('text') or '').strip(),'language':str(data.get('language') or '')}

def create_router(platform):
    router=APIRouter(prefix='/api/admin/speech',tags=['admin-speech'])

    @router.get('/status')
    def status(token:str):
        platform._admin_tekshir(token)
        return {'admin':True,'reading_available':importlib.util.find_spec('edge_tts') is not None,
                'language':'auto','dictation_available':bool(getattr(platform,'GROQ_API_KALIT',''))}

    @router.post('/read')
    async def read(payload:dict,token:str):
        platform._admin_tekshir(token)
        try:text,voice,rate=speech_input(payload)
        except ValueError as exc:raise HTTPException(400,str(exc)) from exc
        key=hashlib.sha256(f'admin-speech-v54\0{voice}\0{rate}\0{text}'.encode()).hexdigest()
        audio=platform._ovoz_keshdan_ol(key)
        if audio is None:
            try:audio=await asyncio.wait_for(synthesize(text,voice,rate),timeout=45)
            except ImportError as exc:raise HTTPException(503,'Serverda ovoz xizmati o‘rnatilmagan') from exc
            except Exception as exc:raise HTTPException(503,'Ovoz xizmati javob bermadi. Qayta urinib ko‘ring.') from exc
            platform._ovoz_keshga_qoy(key,audio)
        return Response(content=audio,media_type='audio/mpeg',headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    @router.post('/dictate')
    async def dictate(request:Request,token:str):
        platform._admin_tekshir(token)
        api_key=getattr(platform,'GROQ_API_KALIT','')
        if not api_key:raise HTTPException(503,'Avtomatik ovoz tanish xizmati ulanmagan')
        content_type=request.headers.get('content-type','').split(';',1)[0].strip().lower()
        extensions={'audio/webm':'webm','audio/ogg':'ogg','audio/mp4':'mp4','audio/wav':'wav','audio/mpeg':'mp3','audio/x-m4a':'m4a'}
        if content_type not in extensions:raise HTTPException(415,'Bu ovoz fayli turi qo‘llanmaydi')
        audio=bytearray()
        async for chunk in request.stream():
            if len(audio)+len(chunk)>8*1024*1024:raise HTTPException(413,'Ovoz yozuvi 8 MB dan oshmasligi kerak')
            audio.extend(chunk)
        if not audio:raise HTTPException(400,'Ovoz yozuvi bo‘sh')
        try:result=await transcribe_audio(bytes(audio),content_type,extensions[content_type],api_key)
        except Exception as exc:raise HTTPException(503,'Ovozni matnga aylantirib bo‘lmadi. Qayta urinib ko‘ring.') from exc
        if not result['text']:raise HTTPException(422,'Yozuvda nutq topilmadi. Qayta gapirib ko‘ring.')
        return result

    return router

"""Admin-only Uzbek reading, preserving punctuation and paragraph boundaries."""
import asyncio
import hashlib
import importlib.util
import math
import re
from fastapi import APIRouter, HTTPException
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
    audio=bytearray()
    speaker='uz-UZ-MadinaNeural' if voice=='qiz' else 'uz-UZ-SardorNeural'
    async for chunk in edge_tts.Communicate(text,speaker,rate=rate).stream():
        if chunk['type']=='audio':audio.extend(chunk['data'])
    if not audio:raise RuntimeError('Empty speech response')
    return bytes(audio)

def create_router(platform):
    router=APIRouter(prefix='/api/admin/speech',tags=['admin-speech'])

    @router.get('/status')
    def status(token:str):
        platform._admin_tekshir(token)
        return {'admin':True,'reading_available':importlib.util.find_spec('edge_tts') is not None,'language':'uz-UZ'}

    @router.post('/read')
    async def read(payload:dict,token:str):
        platform._admin_tekshir(token)
        try:text,voice,rate=speech_input(payload)
        except ValueError as exc:raise HTTPException(400,str(exc)) from exc
        key=hashlib.sha256(f'admin-speech-v1\0{voice}\0{rate}\0{text}'.encode()).hexdigest()
        audio=platform._ovoz_keshdan_ol(key)
        if audio is None:
            try:audio=await asyncio.wait_for(synthesize(text,voice,rate),timeout=45)
            except ImportError as exc:raise HTTPException(503,'Serverda ovoz xizmati o‘rnatilmagan') from exc
            except Exception as exc:raise HTTPException(503,'Ovoz xizmati javob bermadi. Qayta urinib ko‘ring.') from exc
            platform._ovoz_keshga_qoy(key,audio)
        return Response(content=audio,media_type='audio/mpeg',headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})

    return router

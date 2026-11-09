"""REV443: hujjatni «asl ko'rinishda» ochish — Word/PowerPoint/Excel (va eski .doc/.ppt/.xls) LibreOffice bilan PDF ga.
Fayl faqat aylantirish uchun vaqtinchalik papkada turadi va darhol o'chiriladi (saqlanmaydi).
Bir vaqtda bitta aylantirish (xotira tejaladi), 90 soniya chegarasi, bir IP dan soatiga 30 tagacha."""
import os, shutil, subprocess, tempfile, threading, time
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import Response

router = APIRouter()
RUXSAT = {"docx", "doc", "pptx", "ppt", "xlsx", "xls", "odt", "ods", "odp", "rtf", "csv", "pps", "ppsx"}
MAX = 25 * 1024 * 1024
_QULF = threading.Semaphore(1)
_IP = {}


def _soffice():
    return shutil.which("soffice") or shutil.which("libreoffice")


def _limit(ip):
    now = time.time()
    q = [t for t in _IP.get(ip, []) if now - t < 3600]
    if len(q) >= 30:
        raise HTTPException(status_code=429, detail="Juda ko'p so'rov — bir oz kutib qayta urinib ko'ring")
    q.append(now); _IP[ip] = q


def aylantir_pdf(data: bytes, ext: str, timeout: int = 90) -> bytes:
    exe = _soffice()
    if not exe:
        raise HTTPException(status_code=503, detail="Asl ko'rinish hali sozlanmagan (serverda LibreOffice yo'q)")
    with tempfile.TemporaryDirectory(prefix="kb_ayl_") as d:
        kirish = os.path.join(d, f"hujjat.{ext}")
        with open(kirish, "wb") as f:
            f.write(data)
        profil = f"file://{d}/profil"
        if not _QULF.acquire(timeout=60):
            raise HTTPException(status_code=503, detail="Server band — bir daqiqadan keyin qayta urinib ko'ring")
        try:
            p = subprocess.run([exe, f"-env:UserInstallation={profil}", "--headless", "--norestore", "--nologo", "--nodefault",
                                "--convert-to", "pdf", "--outdir", d, kirish], capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Fayl juda katta yoki murakkab — aylantirish vaqti tugadi")
        finally:
            _QULF.release()
        chiqish = os.path.join(d, "hujjat.pdf")
        if p.returncode != 0 or not os.path.exists(chiqish):
            raise HTTPException(status_code=422, detail="Faylni aylantirib bo'lmadi (buzilgan yoki parolli bo'lishi mumkin)")
        with open(chiqish, "rb") as f:
            return f.read()


@router.post("/api/hujjat/aylantir")
async def hujjat_aylantir(request: Request, fayl: UploadFile = File(...)):
    nom = str(fayl.filename or "hujjat").lower()
    ext = nom.rsplit(".", 1)[-1] if "." in nom else ""
    if ext not in RUXSAT:
        raise HTTPException(status_code=400, detail="Bu fayl turini aylantirib bo'lmaydi")
    data = await fayl.read(MAX + 1)
    if len(data) > MAX:
        raise HTTPException(status_code=413, detail="Fayl 25 MB dan katta")
    ip = (request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "").split(",")[0] or (request.client.host if request.client else "")).strip()
    _limit(ip)
    from starlette.concurrency import run_in_threadpool
    pdf = await run_in_threadpool(aylantir_pdf, data, ext)
    return Response(pdf, media_type="application/pdf", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})

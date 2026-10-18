"""REV152: yuklanadigan fayllarni QATTIQ tekshirish va xavfsiz qaytarish.

Qoidalar (kutubxonalar uchun): faqat Word (.docx), Excel (.xlsx), PDF va rasm (.png, .jpg, .jpeg, .webp).
- Fayl turi kengaytmaga EMAS, ichidagi haqiqiy belgilarga (magic bytes) qarab aniqlanadi; brauzer yuborgan
  Content-Type hech qachon ishlatilmaydi — saqlanadigan tur serverda belgilanadi.
- Word/Excel: haqiqiy Office tuzilmasi bo'lishi shart; makros (vbaProject), ActiveX, ichiga joylangan
  dasturlar (OLE embeddings), shifrlangan arxiv, «zip-bomba» (juda ko'p yoki juda katta ochiladigan qismlar),
  yo'l chiqib ketishi (../) va XML DTD/ENTITY (XXE) — rad etiladi.
- PDF: haqiqiy PDF bo'lishi, parol bilan shifrlanmagan bo'lishi, ichida JavaScript, ishga tushirish (Launch),
  ichiga joylangan fayl, XFA/RichMedia bo'lmasligi shart.
- Rasm: Pillow bilan to'liq tekshiriladi; o'lcham chegarasi (dekompressiya bombasi), tur kengaytmaga mos.
- ClamAV ulangan bo'lsa (CLAMD_HOST yoki CLAMD_SOCKET) — antivirus bilan ham tekshiriladi.

Qaytarishda: tur serverda belgilangan, `nosniff`, faqat PDF va rasm brauzerda ochiladi (inline), qolgani
yuklab olinadi; Word/Excel uchun `sandbox` CSP.
"""
from __future__ import annotations

import io
import os
import re
import zipfile
from dataclasses import dataclass
from urllib.parse import quote

from fastapi import HTTPException
from fastapi.responses import Response

MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "png": "image/png",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}
EXT_TUR = {".pdf": "pdf", ".docx": "docx", ".xlsx": "xlsx", ".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}
KUTUBXONA = frozenset(MIME)            # Word, Excel, PDF, rasmlar
RASMLAR = frozenset({"png", "jpeg", "webp"})
INLINE = frozenset({"pdf", "png", "jpeg", "webp"})

MAX_ZIP_QISM = 3000                    # Office arxivdagi qismlar soni
MAX_OCHILGAN = 250 * 1024 * 1024       # ochilgandagi jami hajm
MAX_NISBAT = 200                       # bitta qismning siqilish nisbati (zip-bomba)
MAX_PIKSEL = 60_000_000                # rasm (8000×7500)
MAX_TOMON = 12000

_PDF_XAVF = re.compile(rb"/(JavaScript|Launch|EmbeddedFiles?|RichMedia|XFA|SubmitForm|ImportData)(?![A-Za-z0-9])")


@dataclass
class Fayl:
    tur: str            # pdf | docx | xlsx | png | jpeg | webp
    mime: str
    nom: str            # tozalangan fayl nomi (kengaytmasi tur bilan mos)
    hajm: int


class FaylXato(HTTPException):
    def __init__(self, xabar: str, status: int = 400):
        super().__init__(status_code=status, detail=xabar)


def toza_nom(nom: str, default: str = "hujjat") -> str:
    nom = (nom or default).replace("\\", "/").split("/")[-1]
    nom = re.sub(r"[\x00-\x1f\x7f<>:\"|?*]+", "_", nom).strip(" .")
    return (nom or default)[-200:]


def _ext(nom: str) -> str:
    return ("." + nom.rsplit(".", 1)[-1].lower()) if "." in nom else ""


def _sehrli_tur(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if b"%PDF-" in data[:1024]:
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        return "zip"
    if data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return "ole"   # eski .doc/.xls yoki shifrlangan Office
    return ""


def _office(data: bytes, tur: str) -> None:
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        infos = z.infolist()
    except (zipfile.BadZipFile, ValueError, OSError) as exc:
        raise FaylXato("Fayl buzilgan yoki haqiqiy Word/Excel emas") from exc
    if len(infos) > MAX_ZIP_QISM:
        raise FaylXato("Fayl tuzilishi shubhali (juda ko‘p qism)")
    jami = 0
    nomlar = set()
    for i in infos:
        n = i.filename
        if i.flag_bits & 0x1:
            raise FaylXato("Parol bilan shifrlangan fayl qabul qilinmaydi")
        if n.startswith(("/", "\\")) or ".." in n.replace("\\", "/").split("/") or ":" in n:
            raise FaylXato("Fayl tuzilishi shubhali")
        jami += i.file_size
        if jami > MAX_OCHILGAN:
            raise FaylXato("Fayl ochilganda juda katta (zip-bomba bo‘lishi mumkin)")
        if i.compress_size and i.file_size > 1_000_000 and i.file_size / max(1, i.compress_size) > MAX_NISBAT:
            raise FaylXato("Fayl ochilganda juda katta (zip-bomba bo‘lishi mumkin)")
        nomlar.add(n.lower())
    asosiy = "word/document.xml" if tur == "docx" else "xl/workbook.xml"
    if "[content_types].xml" not in nomlar or asosiy not in nomlar:
        raise FaylXato("Bu haqiqiy " + ("Word (.docx)" if tur == "docx" else "Excel (.xlsx)") + " fayli emas")
    for n in nomlar:
        if "vbaproject" in n or "vbadata" in n:
            raise FaylXato("Ichida makros bor — bunday fayl qabul qilinmaydi")
        if "/activex/" in n:
            raise FaylXato("Ichida ActiveX boshqaruvi bor — bunday fayl qabul qilinmaydi")
        # diagramma uchun joylangan Excel/Word va rasmlar — mumkin; .bin (OLE), .exe va makrosli fayllar — yo'q
        if "/embeddings/" in n and not n.endswith((".xlsx", ".docx", ".png", ".jpg", ".jpeg", ".emf", ".wmf")):
            raise FaylXato("Ichiga boshqa dastur yoki obyekt joylangan — bunday fayl qabul qilinmaydi")
    try:
        ct = z.read("[Content_Types].xml")[:200_000]
    except KeyError:
        ct = b""
    if b"macroEnabled" in ct or b"vbaProject" in ct:
        raise FaylXato("Ichida makros bor — bunday fayl qabul qilinmaydi")
    for n in ("[Content_Types].xml", asosiy):
        try:
            with z.open(n) as f:
                bosh = f.read(4096)
        except KeyError:
            continue
        if b"<!DOCTYPE" in bosh or b"<!ENTITY" in bosh:
            raise FaylXato("Fayl tuzilishi shubhali (DTD)")


def _pdf(data: bytes) -> None:
    if _PDF_XAVF.search(data):
        raise FaylXato("PDF ichida skript yoki ishga tushiriladigan narsa bor — qabul qilinmaydi")
    try:
        from pypdf import PdfReader
        r = PdfReader(io.BytesIO(data), strict=False)
        if r.is_encrypted:
            raise FaylXato("Parol bilan himoyalangan PDF qabul qilinmaydi")
        root = r.trailer.get("/Root") or {}
        root = root.get_object() if hasattr(root, "get_object") else root
        for k in ("/OpenAction", "/AA"):
            v = root.get(k) if hasattr(root, "get") else None
            if v is not None:
                v = v.get_object() if hasattr(v, "get_object") else v
                if isinstance(v, dict) and str(v.get("/S", "")) in ("/JavaScript", "/Launch", "/SubmitForm", "/ImportData"):
                    raise FaylXato("PDF ochilganda avtomatik amal bajaradi — qabul qilinmaydi")
        names = root.get("/Names") if hasattr(root, "get") else None
        names = names.get_object() if hasattr(names, "get_object") else names
        if isinstance(names, dict) and ("/JavaScript" in names or "/EmbeddedFiles" in names):
            raise FaylXato("PDF ichida skript yoki biriktirilgan fayl bor — qabul qilinmaydi")
        if len(r.pages) < 1:
            raise FaylXato("PDF bo‘sh")
        # sahifa va havolalardagi amallar (siqilgan obyektlar ichida ham — pypdf ochib beradi)
        for page in list(r.pages)[:500]:
            if page.get("/AA") is not None:
                raise FaylXato("PDF sahifasi ochilganda amal bajaradi — qabul qilinmaydi")
            for a in (page.get("/Annots") or []):
                a = a.get_object() if hasattr(a, "get_object") else a
                act = a.get("/A") if hasattr(a, "get") else None
                act = act.get_object() if hasattr(act, "get_object") else act
                if isinstance(act, dict) and str(act.get("/S", "")) in ("/JavaScript", "/Launch", "/SubmitForm", "/ImportData"):
                    raise FaylXato("PDF ichida skriptli havola bor — qabul qilinmaydi")
    except FaylXato:
        raise
    except ImportError:
        pass   # pypdf yo'q bo'lsa — yuqoridagi bayt tekshiruvi yetadi
    except Exception as exc:
        raise FaylXato("PDF buzilgan yoki o‘qib bo‘lmaydi") from exc


def _rasm(data: bytes, tur: str) -> None:
    try:
        from PIL import Image
    except ImportError:
        return
    Image.MAX_IMAGE_PIXELS = MAX_PIKSEL
    try:
        with Image.open(io.BytesIO(data)) as im:
            fmt = (im.format or "").lower()
            w, h = im.size
            im.verify()
    except Exception as exc:
        raise FaylXato("Rasm buzilgan yoki o‘qib bo‘lmaydi") from exc
    if {"jpeg": "jpeg", "png": "png", "webp": "webp"}.get(fmt) != tur:
        raise FaylXato("Rasm turi fayl nomiga mos emas")
    if w > MAX_TOMON or h > MAX_TOMON or w * h > MAX_PIKSEL:
        raise FaylXato("Rasm o‘lchami juda katta")


def _antivirus(data: bytes) -> None:
    host, sock = os.getenv("CLAMD_HOST", "").strip(), os.getenv("CLAMD_SOCKET", "").strip()
    if not host and not sock:
        return
    try:
        import clamd
        cd = clamd.ClamdUnixSocket(sock) if sock else clamd.ClamdNetworkSocket(host, int(os.getenv("CLAMD_PORT", "3310")), timeout=20)
        natija = cd.instream(io.BytesIO(data)) or {}
        holat = (natija.get("stream") or ("OK", ""))[0]
    except Exception:
        if os.getenv("CLAMD_MAJBURIY", "") == "1":
            raise FaylXato("Antivirus tekshiruvi hozir ishlamayapti. Keyinroq urinib ko‘ring.", 503)
        return
    if holat == "FOUND":
        raise FaylXato("Faylda zararli dastur topildi — qabul qilinmadi")


def tekshir(data: bytes, nom: str, ruxsat=KUTUBXONA, max_bayt: int = 30 * 1024 * 1024) -> Fayl:
    """Faylni to'liq tekshiradi. Yaroqsiz bo'lsa — FaylXato (400/413), aniq sabab bilan."""
    nom = toza_nom(nom)
    if not data:
        raise FaylXato("Fayl bo‘sh")
    if len(data) > max_bayt:
        raise FaylXato(f"Fayl juda katta — eng ko‘pi {max_bayt // (1024 * 1024)} MB", 413)
    ext = _ext(nom)
    tur = EXT_TUR.get(ext)
    if not tur or tur not in ruxsat:
        ruxsat_nomi = []
        if "docx" in ruxsat: ruxsat_nomi.append("Word (.docx)")
        if "xlsx" in ruxsat: ruxsat_nomi.append("Excel (.xlsx)")
        if "pdf" in ruxsat: ruxsat_nomi.append("PDF")
        if ruxsat & RASMLAR: ruxsat_nomi.append("rasm (.jpg, .png, .webp)")
        if ext in (".doc", ".xls"):
            raise FaylXato("Eski formatdagi fayl. Uni Word/Excel’da ochib, «.docx» yoki «.xlsx» qilib saqlang va qayta yuklang.")
        raise FaylXato("Faqat " + ", ".join(ruxsat_nomi) + " yuklash mumkin")
    sehr = _sehrli_tur(data)
    kutilgan = "zip" if tur in ("docx", "xlsx") else tur
    if sehr != kutilgan:
        if sehr == "ole" and tur in ("docx", "xlsx"):
            raise FaylXato("Fayl parol bilan shifrlangan yoki eski formatda. Parolsiz «.docx/.xlsx» qilib saqlang.")
        raise FaylXato("Fayl ichidagi tur nomiga mos emas (masalan, nomi o‘zgartirilgan). Asl faylni yuklang.")
    if tur in ("docx", "xlsx"):
        _office(data, tur)
    elif tur == "pdf":
        _pdf(data)
    else:
        _rasm(data, tur)
    _antivirus(data)
    return Fayl(tur=tur, mime=MIME[tur], nom=nom, hajm=len(data))


def tur_nomdan(nom: str) -> str:
    """Saqlangan eski fayl uchun — tur faqat kengaytmadan (brauzer yuborgan turga ishonilmaydi)."""
    return EXT_TUR.get(_ext(nom or ""), "")


def javob(data: bytes, nom: str, yuklab: bool = False, tur: str = "") -> Response:
    """Faylni xavfsiz qaytaradi: tur serverda, nosniff; faqat PDF/rasm brauzerda ochiladi, qolgani yuklanadi."""
    tur = tur or tur_nomdan(nom)
    mime = MIME.get(tur, "application/octet-stream")
    rejim = "inline" if (tur in INLINE and not yuklab) else "attachment"
    ascii_nom = re.sub(r"[^A-Za-z0-9._-]+", "_", nom or "fayl") or "fayl"
    sarlavha = {
        "Content-Disposition": f"{rejim}; filename=\"{ascii_nom}\"; filename*=UTF-8''{quote(nom or 'fayl', safe='')}",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store",
        "Referrer-Policy": "no-referrer",
        "Cross-Origin-Resource-Policy": "cross-origin",
    }
    if tur != "pdf":   # Chrome PDF ko'ruvchisi sandbox bilan ishlamaydi; PDF tekshirilgan va turi qat'iy
        sarlavha["Content-Security-Policy"] = "sandbox; default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'"
    return Response(content=bytes(data), media_type=mime, headers=sarlavha)


# ── chat: ovozli/video xabarlar va oddiy hujjatlar ──
_MEDIA = {
    "audio/webm": "webm", "video/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "mp4", "video/mp4": "mp4",
    "audio/x-m4a": "mp4", "audio/m4a": "mp4", "video/quicktime": "mp4", "audio/aac": "aac",
    "audio/mpeg": "mp3", "audio/mp3": "mp3", "audio/wav": "wav", "audio/x-wav": "wav", "audio/wave": "wav",
}


def _media_sehr(data: bytes) -> str:
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    if data[:4] == b"OggS":
        return "ogg"
    if data[4:8] == b"ftyp":
        return "mp4"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3" if data[:3] == b"ID3" or (data[1] & 0x06) else "aac"
    return ""


def media_turi(data: bytes, content_type: str) -> str:
    """Ovozli/video xabar: brauzer aytgan tur ruxsat etilganlardan bo'lishi VA fayl ichi unga mos bo'lishi shart.
    Qaytaradi: saqlanadigan tur (masalan 'audio/webm'). Mos bo'lmasa — FaylXato."""
    ct = (content_type or "").split(";")[0].strip().lower()
    kut = _MEDIA.get(ct)
    sehr = _media_sehr(data)
    if not kut or not sehr or (kut != sehr and not {kut, sehr} <= {"mp3", "aac"}):
        raise FaylXato("Bu ovoz/video yozuvi emas")
    return ct


def hujjat_turi(nom: str) -> str:
    """Chatdagi oddiy hujjat: saqlanadigan tur faqat kengaytmadan (rasm/PDF — o'z turi, qolgani — yuklab olinadigan)."""
    tur = tur_nomdan(nom)
    return MIME.get(tur, "application/octet-stream")


def chat_javob(data: bytes, nom: str, saqlangan_tur: str) -> Response:
    """Chat faylini qaytarish: audio/video va rasm/PDF — brauzerda; qolgani — faqat yuklab olish, sandbox bilan."""
    ct = (saqlangan_tur or "").split(";")[0].strip().lower()
    if ct in _MEDIA and _media_sehr(data):
        return Response(content=bytes(data), media_type=ct, headers={
            "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox; default-src 'none'",
            "Cache-Control": "private, max-age=3600", "Accept-Ranges": "none"})
    tur = _sehrli_tur(data)
    if tur in INLINE and tur == tur_nomdan(nom):
        return javob(data, nom, yuklab=False, tur=tur)
    return javob(data, nom, yuklab=True, tur="")

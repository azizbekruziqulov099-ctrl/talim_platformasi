"""Taqdimot dvigateli API (/api/taqdimot-dvigatel).

Faqat o'zining 2 ta jadvalini yaratadi: taqdimot_dvigatel_ishlar (AI navbati) va taqdimot_rasmlar (yuklangan rasmlar).
Boshqa modullarga tegmaydi.
"""
from __future__ import annotations

import io
import json
import re
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore

from fastapi import Header, HTTPException, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from . import ai, excel, kutubxona, rasmlar, sxema, uslub, yasash

PREFIX = "/api/taqdimot-dvigatel"
NO_STORE = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}
MAX_JSON = 1024 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_ZIP = 120 * 1024 * 1024
AI_KUNLIK = 15
SCHEMA = """
CREATE TABLE IF NOT EXISTS taqdimot_dvigatel_ishlar (
    id TEXT PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    holat TEXT NOT NULL DEFAULT 'navbatda',
    sorov JSONB,
    natija JSONB,
    xato TEXT,
    yaratildi TIMESTAMPTZ NOT NULL DEFAULT now(),
    tugadi TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS taqdimot_dvigatel_ishlar_owner ON taqdimot_dvigatel_ishlar(owner_id, yaratildi DESC);
CREATE TABLE IF NOT EXISTS taqdimot_rasmlar (
    kalit TEXT PRIMARY KEY,
    mime TEXT NOT NULL,
    data BYTEA NOT NULL,
    w INT, h INT,
    tavsif TEXT,
    yukladi BIGINT,
    vaqt TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""
UVKOD = re.compile(r"^[a-z_]{2,20}\.[a-z_]{2,20}\.[0-2]$")


def fail(msg, status=422):
    raise HTTPException(status_code=status, detail=msg, headers=NO_STORE)


class Dvigatel:
    def __init__(self, platform):
        from ..presentations import PresentationService  # mavjud kirish tekshiruvi va DB ulanishi
        self.ps = PresentationService(platform)
        self._ready = False
        self._lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="taqdimot-ai")
        self.eksport = BoundedSemaphore(3)
        self._kalitlar = set()
        self._kalit_vaqt = 0.0
        rasmlar.TASHQI = self.rasm_db
        rasmlar.TASHQI_BOR = self.rasm_bormi

    # ------------------------------------------------------------ umumiy
    def migrate(self):
        if self._ready:
            return
        with self._lock:
            if not self._ready:
                with self.ps.db() as cur:
                    cur.execute("SELECT pg_advisory_xact_lock(49091377)")
                    cur.execute(SCHEMA)
                self._ready = True

    def actor(self, auth):
        uid = self.ps.actor(auth)
        self.migrate()
        return uid

    def admin(self, uid):
        with self.ps.db() as cur:
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
            return cur.fetchone() is not None

    # ------------------------------------------------------------ rasmlar (DB)
    def rasm_bormi(self, key):
        if time.time() - self._kalit_vaqt > 60:
            try:
                self.migrate()
                with self.ps.db() as cur:
                    cur.execute("SELECT kalit FROM taqdimot_rasmlar")
                    self._kalitlar = {r["kalit"] for r in cur.fetchall()}
                self._kalit_vaqt = time.time()
            except Exception:
                self._kalit_vaqt = time.time()
        return key in self._kalitlar

    def rasm_db(self, key):
        if not self.rasm_bormi(key):
            return None
        with self.ps.db() as cur:
            cur.execute("SELECT data, mime FROM taqdimot_rasmlar WHERE kalit=%s", (key,))
            r = cur.fetchone()
        return (bytes(r["data"]), r["mime"]) if r else None

    def rasm_saqla(self, uid, kalit, data, tavsif=""):
        from PIL import Image
        kalit = rasmlar.kalit_toza(kalit)
        if not rasmlar.KALIT.match(kalit):
            return None
        try:
            with Image.open(io.BytesIO(data)) as im:
                im.load()
                if im.width * im.height > 25_000_000:
                    return None
                im = im.convert("RGBA")
                if max(im.size) > 1024:
                    k = 1024 / max(im.size)
                    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, "WEBP", quality=88, method=5)
                w, h = im.size
        except Exception:
            return None
        with self.ps.db() as cur:
            cur.execute("""INSERT INTO taqdimot_rasmlar(kalit, mime, data, w, h, tavsif, yukladi) VALUES(%s,'image/webp',%s,%s,%s,%s,%s)
                           ON CONFLICT(kalit) DO UPDATE SET data=EXCLUDED.data, w=EXCLUDED.w, h=EXCLUDED.h, mime=EXCLUDED.mime,
                           tavsif=COALESCE(NULLIF(EXCLUDED.tavsif,''), taqdimot_rasmlar.tavsif), yukladi=EXCLUDED.yukladi, vaqt=now()""",
                        (kalit, buf.getvalue(), w, h, tavsif[:300], uid))
        self._kalitlar.add(kalit)
        rasmlar.yol.cache_clear()
        return kalit

    # ------------------------------------------------------------ yasash
    @staticmethod
    def parametrlar(body):
        if not isinstance(body, dict) or not isinstance(body.get("miya"), dict):
            fail("Miya (mazmun) yuborilmadi")
        seed = body.get("seed")
        if seed is not None and (type(seed) is not int or not 0 < seed < 2 ** 31):
            fail("Urug‘ (seed) noto‘g‘ri")
        kod = body.get("uslub")
        if kod is not None and (not isinstance(kod, str) or not UVKOD.match(kod)):
            fail("Uslub kodi noto‘g‘ri")
        anim = body.get("anim") if body.get("anim") in uslub.ANIMATSIYALAR else None
        oila = body.get("oila") if body.get("oila") in uslub.OILALAR else None
        pal = body.get("palitra") if isinstance(body.get("palitra"), str) else None
        bt = body.get("bolim_titul") if isinstance(body.get("bolim_titul"), bool) else None
        ra = body.get("rasm_avto") if isinstance(body.get("rasm_avto"), bool) else True
        return dict(seed=seed, uslub_kod=kod, anim=anim, oila=oila, palitra=pal, bolim_titul=bt, rasm_avto=ra)

    def yasa(self, body):
        p = self.parametrlar(body)
        try:
            return yasash.yasa(body["miya"], **p)
        except ValueError as exc:
            fail(str(exc))

    def pptx(self, body):
        if not self.eksport.acquire(timeout=20):
            fail("Server band, birozdan keyin qayta urinib ko‘ring", 503)
        try:
            sah = self.yasa(body)
            data = yasash.pptx(sah)
            nom = re.sub(r"[^\w\-]+", "_", (sah["meta"].get("qisqa") or sah["meta"]["mavzu"]))[:60] or "taqdimot"
            return data, nom
        finally:
            self.eksport.release()

    # ------------------------------------------------------------ AI navbati
    def ai_boshla(self, uid, body):
        if not ai.mavjud():
            fail("AI kaliti serverda sozlanmagan. Hozircha miyani Excel yoki JSON orqali yuklang.", 503)
        if not isinstance(body, dict):
            fail("So‘rov noto‘g‘ri")
        mavzu = sxema.t(body.get("mavzu"), 200)
        if len(mavzu) < 3:
            fail("Mavzuni yozing")
        sorov = {k: sxema.t(body.get(k), 200) for k in ("fan", "daraja", "sinf", "tur")}
        sorov["mavzu"] = mavzu
        sorov["qoshimcha"] = sxema.t(body.get("qoshimcha"), 1500)
        sorov["manba"] = sxema.t(body.get("manba"), 12000)
        admin = self.admin(uid)
        with self.ps.db() as cur:
            if not admin:
                cur.execute("SELECT count(*) AS n FROM taqdimot_dvigatel_ishlar WHERE owner_id=%s AND yaratildi > now() - interval '1 day'", (uid,))
                if cur.fetchone()["n"] >= AI_KUNLIK:
                    fail(f"Bugungi AI limiti tugadi ({AI_KUNLIK} ta). Ertaga yoki Excel shablon orqali davom eting.", 429)
            ish = uuid.uuid4().hex
            cur.execute("INSERT INTO taqdimot_dvigatel_ishlar(id, owner_id, sorov) VALUES(%s,%s,%s)", (ish, uid, json.dumps(sorov, ensure_ascii=False)))
        self.pool.submit(self._ai_ish, ish, sorov)
        return {"ish": ish, "holat": "navbatda"}

    def _ai_ish(self, ish, sorov):
        try:
            with self.ps.db() as cur:
                cur.execute("UPDATE taqdimot_dvigatel_ishlar SET holat='yozilmoqda' WHERE id=%s", (ish,))
            m = ai.miya_yoz(sorov["mavzu"], sorov.get("fan", ""), sorov.get("daraja") or "maktab", sorov.get("sinf", ""), sorov.get("tur") or "dars",
                            sorov.get("qoshimcha", ""), sorov.get("manba", ""))
            # AI rasm (yoqilgan bo'lsa): yo'q kalitlar uchun 4 tagacha
            for r in (m.get("rasmlar") or [])[:4]:
                k = rasmlar.kalit_toza(r["kalit"])
                if k and not rasmlar.bor(k) and r.get("prompt"):
                    try:
                        png = ai.rasm_chiz(r["prompt"])
                        if png:
                            self.rasm_saqla(0, k, png, r.get("tavsif", ""))
                    except Exception:
                        pass
            with self.ps.db() as cur:
                cur.execute("UPDATE taqdimot_dvigatel_ishlar SET holat='tayyor', natija=%s, tugadi=now() WHERE id=%s", (json.dumps(m, ensure_ascii=False), ish))
        except Exception as exc:  # xato foydalanuvchiga qisqa ko'rinadi
            try:
                with self.ps.db() as cur:
                    cur.execute("UPDATE taqdimot_dvigatel_ishlar SET holat='xato', xato=%s, tugadi=now() WHERE id=%s", (str(exc)[:300], ish))
            except Exception:
                pass

    def ai_holat(self, uid, ish):
        if not re.fullmatch(r"[0-9a-f]{32}", ish or ""):
            fail("Ish raqami noto‘g‘ri", 404)
        with self.ps.db() as cur:
            cur.execute("SELECT holat, natija, xato, owner_id, yaratildi FROM taqdimot_dvigatel_ishlar WHERE id=%s", (ish,))
            r = cur.fetchone()
        if not r or r["owner_id"] != uid:
            fail("Ish topilmadi", 404)
        out = {"holat": r["holat"]}
        if r["holat"] == "tayyor":
            out["miya"] = r["natija"] if isinstance(r["natija"], dict) else json.loads(r["natija"])
        elif r["holat"] == "xato":
            out["xato"] = r["xato"]
        return out

    # ------------------------------------------------------------ import
    @staticmethod
    def importla(nom, data):
        nom = (nom or "").lower()
        if nom.endswith(".xlsx") or data[:2] == b"PK" and not nom.endswith(".zip"):
            try:
                return excel.oqi(data)
            except ValueError as exc:
                fail(str(exc))
            except Exception:
                fail("Excel faylni o‘qib bo‘lmadi. Shablondan foydalaning.")
        try:
            obj = ai.json_ajrat(data.decode("utf-8-sig"))
        except Exception:
            fail("JSON faylni o‘qib bo‘lmadi")
        items = obj if isinstance(obj, list) else [obj]
        out = []
        for it in items[:20]:
            try:
                out.append(sxema.normallashtir(it))
            except ValueError as exc:
                fail(str(exc))
        return out


async def _body(request: Request, limit: int) -> bytes:
    n = int(request.headers.get("content-length") or 0)
    if n > limit:
        fail("Fayl juda katta", 413)
    buf = bytearray()
    async for chunk in request.stream():
        buf += chunk
        if len(buf) > limit:
            fail("Fayl juda katta", 413)
    return bytes(buf)


async def _json(request: Request, limit=MAX_JSON):
    raw = await _body(request, limit)
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        fail("JSON noto‘g‘ri")


def register_taqdimot_dvigatel(app, platform):
    D = Dvigatel(platform)

    @app.get(PREFIX + "/uslublar")
    def uslublar(authorization: str | None = Header(None)):
        D.actor(authorization)
        oilalar = []
        for o, od in uslub.OILALAR.items():
            pals = []
            for p in uslub.mos_palitralar(o):
                u = uslub.Uslub(f"{o}.{p}.0")
                pals.append({"kod": p, "nom": (uslub.YORUG.get(p) or uslub.QORONGI.get(p) or uslub.DOSKA.get(p))["nom"], "acc": u.acc, "qorongi": u.qorongi})
            oilalar.append({"kod": o, "nom": od["nom"], "turi": od["turi"], "palitralar": pals})
        return Response(json.dumps({"oilalar": oilalar, "animatsiyalar": [{"kod": k, "nom": v["nom"]} for k, v in uslub.ANIMATSIYALAR.items()],
                                    "jami": uslub.uslublar_soni(), "ai": ai.mavjud()}, ensure_ascii=False),
                        media_type="application/json", headers=NO_STORE)

    @app.get(PREFIX + "/fon/{kod}.jpg")
    def fon(kod: str):
        asos, _, motif = kod.partition("~")
        if not UVKOD.match(asos) or (motif and not re.match(r"^[a-z0-9_]{2,40}$", motif)):
            fail("Topilmadi", 404)
        return Response(uslub.fon_rasm(kod), media_type="image/jpeg", headers={"Cache-Control": "public, max-age=604800, immutable"})

    @app.get(PREFIX + "/rasm/{kalit}")
    def rasm(kalit: str):
        k = rasmlar.kalit_toza(kalit)
        data, mime = rasmlar.web_bytes(k)
        if not data:
            fail("Rasm topilmadi", 404)
        return Response(data, media_type=mime, headers={"Cache-Control": "public, max-age=86400"})

    @app.get(PREFIX + "/namuna")
    def namuna(authorization: str | None = Header(None)):
        D.actor(authorization)
        return Response(rasmlar.namuna_json(), media_type="application/json", headers=NO_STORE)

    @app.get(PREFIX + "/korsatma")
    def korsatma(authorization: str | None = Header(None)):
        D.actor(authorization)
        return Response(ai.korsatma(katalog=True), media_type="text/plain; charset=utf-8", headers=NO_STORE)

    @app.get(PREFIX + "/shablon.xlsx")
    def shablon(namuna: int = 0, authorization: str | None = Header(None)):
        D.actor(authorization)
        m = json.loads(rasmlar.namuna_json()) if namuna else None
        data = excel.shablon(m, ai.korsatma())
        nom = "Taqdimot_miya_namuna.xlsx" if namuna else "Taqdimot_miya_shablon.xlsx"
        return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={**NO_STORE, "Content-Disposition": f'attachment; filename="{nom}"'})

    @app.post(PREFIX + "/yasash")
    async def yasa(request: Request, authorization: str | None = Header(None)):
        await run_in_threadpool(D.actor, authorization)
        body = await _json(request)
        sah = await run_in_threadpool(D.yasa, body)
        return Response(json.dumps(sah, ensure_ascii=False, separators=(",", ":")), media_type="application/json", headers=NO_STORE)

    @app.post(PREFIX + "/pptx")
    async def pptx(request: Request, authorization: str | None = Header(None)):
        await run_in_threadpool(D.actor, authorization)
        body = await _json(request)
        data, nom = await run_in_threadpool(D.pptx, body)
        return Response(data, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        headers={**NO_STORE, "Content-Disposition": f'attachment; filename="{nom}.pptx"'})

    @app.post(PREFIX + "/import")
    async def importla(request: Request, authorization: str | None = Header(None)):
        await run_in_threadpool(D.actor, authorization)
        data = await _body(request, MAX_FILE)
        out = await run_in_threadpool(D.importla, request.headers.get("x-fayl-nomi", ""), data)
        return Response(json.dumps({"miyalar": out}, ensure_ascii=False), media_type="application/json", headers=NO_STORE)

    @app.post(PREFIX + "/ai")
    async def ai_boshla(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(D.actor, authorization)
        body = await _json(request, 64 * 1024)
        return await run_in_threadpool(D.ai_boshla, uid, body)

    @app.get(PREFIX + "/ai/{ish}")
    def ai_holat(ish: str, authorization: str | None = Header(None)):
        uid = D.actor(authorization)
        return Response(json.dumps(D.ai_holat(uid, ish), ensure_ascii=False), media_type="application/json", headers=NO_STORE)

    @app.post(PREFIX + "/rasm-yuklash")
    async def rasm_yuklash(request: Request, authorization: str | None = Header(None)):
        """Faqat admin: bitta rasm (X-Kalit) yoki ZIP (fayl nomi = kalit)."""
        uid = await run_in_threadpool(D.actor, authorization)
        if not await run_in_threadpool(D.admin, uid):
            fail("Rasm yuklash faqat administrator uchun", 403)
        data = await _body(request, MAX_ZIP)

        def ish():
            saqlandi, xato = [], []
            if data[:2] == b"PK":
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for info in z.infolist()[:3000]:
                        if info.is_dir() or info.file_size > 8 * 1024 * 1024:
                            continue
                        nom = info.filename.rsplit("/", 1)[-1]
                        base, _, ext = nom.rpartition(".")
                        if ext.lower() not in ("png", "webp", "jpg", "jpeg") or nom.startswith("."):
                            continue
                        k = D.rasm_saqla(uid, base, z.read(info))
                        (saqlandi if k else xato).append(k or nom)
            else:
                k = D.rasm_saqla(uid, request.headers.get("x-kalit", ""), data, request.headers.get("x-tavsif", ""))
                (saqlandi if k else xato).append(k or "rasm")
            return {"saqlandi": len(saqlandi), "kalitlar": saqlandi[:200], "xato": xato[:50]}
        return await run_in_threadpool(ish)

    @app.get(PREFIX + "/rasmlar")
    def rasm_royxat(q: str = "", authorization: str | None = Header(None)):
        D.actor(authorization)
        q = rasmlar.kalit_toza(q)
        with D.ps.db() as cur:
            cur.execute("SELECT kalit, tavsif FROM taqdimot_rasmlar WHERE kalit LIKE %s ORDER BY vaqt DESC LIMIT 60", (f"%{q}%",))
            rows = [{"kalit": r["kalit"], "tavsif": r["tavsif"], "tur": "yuklangan"} for r in cur.fetchall()]
        bor = {r["kalit"] for r in rows}
        rows += [r for r in rasmlar.papkadan_qidir(q, 120 - len(rows)) if r["kalit"] not in bor]
        return {"rasmlar": rows}

    # --- Tayyor mavzular kutubxonasi ---
    @app.get(PREFIX + "/kutubxona")
    def kutubxona_royxat(authorization: str | None = Header(None)):
        D.actor(authorization)
        return Response(json.dumps({"toplamlar": [kutubxona.mavzular(t["kod"]) for t in kutubxona.toplamlar()]}, ensure_ascii=False),
                        media_type="application/json", headers=NO_STORE)

    @app.get(PREFIX + "/kutubxona/{toplam}/{kod}")
    def kutubxona_miya(toplam: str, kod: str, authorization: str | None = Header(None)):
        D.actor(authorization)
        m = kutubxona.miya(toplam, kod)
        if not m:
            fail("Mavzu topilmadi", 404)
        return Response(json.dumps(m, ensure_ascii=False), media_type="application/json", headers=NO_STORE)

    @app.get(PREFIX + "/kutubxona/{toplam}/{kod}/{tur}")
    def kutubxona_hujjat(toplam: str, kod: str, tur: str, authorization: str | None = Header(None)):
        uid = D.actor(authorization)
        if tur not in ("oqituvchi", "topshiriq", "reja", "javoblar"):
            fail("Topilmadi", 404)
        if tur == "javoblar" and not D.admin(uid):
            fail("Javoblar faqat administrator uchun", 403)
        h = kutubxona.hujjat(toplam, kod, tur)
        if not h:
            fail("Hujjat topilmadi", 404)
        nom, data, mime = h
        return Response(data, media_type=mime, headers={**NO_STORE, "Content-Disposition": f'attachment; filename="{nom}"'})

    return D

"""Taqdimot dvigateli API (/api/taqdimot-dvigatel).

Faqat o'zining 2 ta jadvalini yaratadi: taqdimot_dvigatel_ishlar (AI navbati) va taqdimot_rasmlar (yuklangan rasmlar).
Boshqa modullarga tegmaydi.
"""
from __future__ import annotations

import io
import json
import os
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

from . import ai, excel, kutubxona, rasmlar, sozlamalar, sxema, uslub, yasash

PREFIX = "/api/taqdimot-dvigatel"
NO_STORE = {"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"}
MAX_JSON = 1024 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_ZIP = 120 * 1024 * 1024
AI_KUNLIK = 15
SAQLASH_MAX = 300   # bitta foydalanuvchining saqlangan taqdimotlari (o'chirilmaganlari)
UZILDI_DAQ = 20     # shuncha daqiqadan beri «yozilmoqda» turgan ish — server qayta ishga tushganda uzilgan
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
-- «Mening taqdimotlarim»: tanlangan dizayn, nom, o'chirilgan belgisi (qatorlar o'chmaydi — AI limiti hisobi to'g'ri qolsin)
ALTER TABLE taqdimot_dvigatel_ishlar ADD COLUMN IF NOT EXISTS korinish JSONB;
ALTER TABLE taqdimot_dvigatel_ishlar ADD COLUMN IF NOT EXISTS nom TEXT;
ALTER TABLE taqdimot_dvigatel_ishlar ADD COLUMN IF NOT EXISTS ochirildi BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE taqdimot_dvigatel_ishlar ADD COLUMN IF NOT EXISTS yangilandi TIMESTAMPTZ;
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
        self._til_vaqt = {}
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
        rasmlar.TASHQI_KALITLAR = self.rasm_kalitlari
        from .kutubxona_ai import Kutubxona
        self.kutub = Kutubxona(self)
        self._yozuvchi_tekshirildi = False

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
        if not self._yozuvchi_tekshirildi:   # kutubxona yozuvchisi: DB ishlayotgani aniq bo'lgach (yoqilmagan bo'lsa — kutib turadi)
            self._yozuvchi_tekshirildi = True
            if os.getenv("TAQDIMOT_KUTUBXONA_YOZUVCHI", "1") != "0" and not os.getenv("PYTEST_CURRENT_TEST"):
                try:
                    self.kutub.ishga_tushir()
                except Exception:
                    pass
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

    def rasm_kalitlari(self):
        self.rasm_bormi("")
        return self._kalitlar

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
        a2 = body.get("anim2")
        a2 = a2 if a2 == "" or a2 in uslub.ANIMATSIYALAR else None
        dz = body.get("dizayn") if isinstance(body.get("dizayn"), dict) else None
        if dz:
            dz = {k: v for k, v in dz.items() if k in ("sarlavha", "kart", "titul", "bolim") and isinstance(v, (str, int)) and len(str(v)) <= 12}
        return dict(seed=seed, uslub_kod=kod, anim=anim, oila=oila, palitra=pal, bolim_titul=bt, rasm_avto=ra, anim2=a2, dizayn=dz or None,
                    sozlama=sozlamalar.toza(body.get("sozlama")) or None)

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
        sorov["sozlama"] = ai.sozlama_toza(body.get("sozlama"))
        sorov["faqat_reja"] = bool(body.get("faqat_reja"))
        if isinstance(body.get("reja"), dict):
            try:
                sorov["reja"] = ai.reja_toza(body["reja"], mavzu)
            except RuntimeError as exc:
                fail(str(exc))
        admin = self.admin(uid)
        with self.ps.db() as cur:
            if not admin and not sorov["faqat_reja"]:  # reja tuzish limitga kirmaydi
                cur.execute("SELECT count(*) AS n FROM taqdimot_dvigatel_ishlar WHERE owner_id=%s AND yaratildi > now() - interval '1 day' "
                            "AND COALESCE(sorov->>'faqat_reja', 'false') <> 'true' AND COALESCE(sorov->>'qolda', 'false') <> 'true'", (uid,))
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
            args = (sorov["mavzu"], sorov.get("fan", ""), sorov.get("daraja") or "maktab", sorov.get("sinf", ""), sorov.get("tur") or "dars",
                    sorov.get("qoshimcha", ""), sorov.get("manba", ""))
            if sorov.get("faqat_reja"):
                r = ai.reja_yoz(*args, sozlama=sorov.get("sozlama"))
                with self.ps.db() as cur:
                    cur.execute("UPDATE taqdimot_dvigatel_ishlar SET holat='tayyor', natija=%s, tugadi=now() WHERE id=%s", (json.dumps(r, ensure_ascii=False), ish))
                return
            m = ai.miya_yoz(*args, sozlama=sorov.get("sozlama"), reja=sorov.get("reja"))
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

    # ------------------------------------------------------------ «Mening taqdimotlarim»
    @staticmethod
    def _iso(v):
        return v.isoformat() if v else None

    def royxat(self, uid, limit=80):
        """AI yozgan (va qo'lda saqlangan) taqdimotlar — eng yangisi birinchi."""
        limit = max(1, min(int(limit or 80), 200))
        with self.ps.db() as cur:
            cur.execute(
                "SELECT id, holat, sorov, nom, xato, yaratildi, tugadi, yangilandi, natija->'meta' AS meta, "
                "(SELECT COALESCE(sum(CASE WHEN jsonb_typeof(b->'slaydlar')='array' THEN jsonb_array_length(b->'slaydlar') ELSE 0 END),0) "
                "   FROM jsonb_array_elements(CASE WHEN jsonb_typeof(natija->'bolimlar')='array' THEN natija->'bolimlar' ELSE '[]'::jsonb END) b) AS slaydlar, "
                "(korinish IS NOT NULL) AS dizaynli, (yaratildi < now() - make_interval(mins => %s)) AS eski "
                "FROM taqdimot_dvigatel_ishlar WHERE owner_id=%s AND NOT ochirildi ORDER BY COALESCE(yangilandi, yaratildi) DESC LIMIT %s",
                (UZILDI_DAQ, uid, limit))
            rows = cur.fetchall()
        out = []
        for r in rows:
            so = r["sorov"] if isinstance(r["sorov"], dict) else json.loads(r["sorov"] or "{}")
            meta = r["meta"] if isinstance(r["meta"], dict) else json.loads(r["meta"] or "{}") if r["meta"] else {}
            holat = r["holat"]
            if holat in ("navbatda", "yozilmoqda") and r["eski"]:
                holat = "uzildi"
            tur = "reja" if so.get("faqat_reja") else "saqlangan" if so.get("qolda") else "ai"
            out.append({"id": r["id"], "holat": holat, "tur": tur, "nom": r["nom"] or meta.get("mavzu") or so.get("mavzu") or "Taqdimot",
                        "fan": meta.get("fan") or so.get("fan") or "", "sinf": meta.get("sinf") or so.get("sinf") or "",
                        "daraja": so.get("daraja") or meta.get("daraja") or "", "slaydlar": int(r["slaydlar"] or 0),
                        "yaratildi": self._iso(r["yaratildi"]), "yangilandi": self._iso(r["yangilandi"] or r["tugadi"]),
                        "xato": (r["xato"] or "")[:160] if holat == "xato" else ("Server qayta ishga tushganda to‘xtab qoldi — qayta yozdiring"
                                                                               if holat == "uzildi" else "")})
        return out

    def ochish(self, uid, ish):
        if not re.fullmatch(r"[0-9a-f]{32}", ish or ""):
            fail("Taqdimot topilmadi", 404)
        with self.ps.db() as cur:
            cur.execute("SELECT holat, sorov, natija, korinish, nom, xato, owner_id, ochirildi FROM taqdimot_dvigatel_ishlar WHERE id=%s", (ish,))
            r = cur.fetchone()
        if not r or r["owner_id"] != uid or r["ochirildi"]:
            fail("Taqdimot topilmadi", 404)
        so = r["sorov"] if isinstance(r["sorov"], dict) else json.loads(r["sorov"] or "{}")
        out = {"id": ish, "holat": r["holat"], "tur": "reja" if so.get("faqat_reja") else "saqlangan" if so.get("qolda") else "ai",
               "nom": r["nom"] or "", "xato": r["xato"] or "",
               "sorov": {k: so.get(k) for k in ("mavzu", "fan", "daraja", "sinf", "tur", "qoshimcha", "sozlama") if so.get(k) is not None},
               "korinish": r["korinish"] if isinstance(r["korinish"], dict) else json.loads(r["korinish"]) if r["korinish"] else None}
        if r["holat"] == "tayyor":
            n = r["natija"] if isinstance(r["natija"], dict) else json.loads(r["natija"] or "{}")
            out["reja" if out["tur"] == "reja" else "miya"] = n
        return out

    @staticmethod
    def _korinish_toza(k):
        if not isinstance(k, dict):
            return None
        out = {}
        if isinstance(k.get("seed"), int):
            out["seed"] = max(1, min(int(k["seed"]), 2_147_483_647))
        for x in ("oila", "palitra", "anim"):
            v = k.get(x)
            if isinstance(v, str) and re.fullmatch(r"[a-z_]{0,20}", v):
                out[x] = v
        if "bolim_titul" in k and k["bolim_titul"] in (True, False, None):
            out["bolim_titul"] = k["bolim_titul"]
        if isinstance(k.get("rasm_avto"), bool):
            out["rasm_avto"] = k["rasm_avto"]
        if isinstance(k.get("dizayn"), dict):
            out["dizayn"] = {a: v for a, v in k["dizayn"].items() if a in ("sarlavha", "kart", "titul", "bolim")
                             and isinstance(v, (str, int)) and len(str(v)) <= 12}
        z = sozlamalar.toza(k.get("sozlama"))
        if z:
            out["sozlama"] = z
        return out

    def korinish_saqla(self, uid, ish, body):
        if not re.fullmatch(r"[0-9a-f]{32}", ish or "") or not isinstance(body, dict):
            fail("Taqdimot topilmadi", 404)
        k = self._korinish_toza(body.get("korinish"))
        nom = sxema.t(body.get("nom"), 160) if body.get("nom") is not None else None
        with self.ps.db() as cur:
            cur.execute("UPDATE taqdimot_dvigatel_ishlar SET korinish=COALESCE(%s::jsonb, korinish), nom=COALESCE(%s, nom), yangilandi=now() "
                        "WHERE id=%s AND owner_id=%s AND NOT ochirildi",
                        (json.dumps(k, ensure_ascii=False) if k is not None else None, nom or None, ish, uid))
            if cur.rowcount == 0:
                fail("Taqdimot topilmadi", 404)
        return {"ok": True}

    def saqla(self, uid, body):
        """Tayyor mavzu, Excel/JSON yoki namuna — «Mening taqdimotlarim»ga (AI limitiga kirmaydi)."""
        if not isinstance(body, dict) or not isinstance(body.get("miya"), dict):
            fail("Saqlanadigan taqdimot yo‘q")
        try:
            m = sxema.normallashtir(body["miya"])
        except ValueError as exc:
            fail(str(exc))
        k = self._korinish_toza(body.get("korinish"))
        ish = uuid.uuid4().hex
        with self.ps.db() as cur:
            cur.execute("SELECT count(*) AS n FROM taqdimot_dvigatel_ishlar WHERE owner_id=%s AND NOT ochirildi", (uid,))
            if cur.fetchone()["n"] >= SAQLASH_MAX:
                fail(f"Saqlangan taqdimotlar {SAQLASH_MAX} taga yetdi — keraksizlarini o‘chiring.", 429)
            cur.execute("INSERT INTO taqdimot_dvigatel_ishlar(id, owner_id, holat, sorov, natija, korinish, nom, tugadi, yangilandi) "
                        "VALUES(%s,%s,'tayyor',%s,%s,%s,%s,now(),now())",
                        (ish, uid, json.dumps({"mavzu": m["meta"]["mavzu"], "fan": m["meta"].get("fan", ""), "qolda": True}, ensure_ascii=False),
                         json.dumps(m, ensure_ascii=False), json.dumps(k, ensure_ascii=False) if k else None, m["meta"]["mavzu"]))
        return {"id": ish}

    def ochir(self, uid, ish):
        if not re.fullmatch(r"[0-9a-f]{32}", ish or ""):
            fail("Taqdimot topilmadi", 404)
        with self.ps.db() as cur:
            cur.execute("UPDATE taqdimot_dvigatel_ishlar SET ochirildi=true, yangilandi=now() WHERE id=%s AND owner_id=%s", (ish, uid))
            if cur.rowcount == 0:
                fail("Taqdimot topilmadi", 404)
        return {"ok": True}

    # ------------------------------------------------------------ tilni to'g'rilash
    def til_togrila(self, uid, body):
        """Taqdimotda tanlangan tildan boshqa tilda qolgan matnlarni AI bilan tarjima qiladi (saqlangan bo'lsa — bazada ham)."""
        if not ai.mavjud():
            fail("AI kaliti serverda sozlanmagan", 503)
        if not isinstance(body, dict) or not isinstance(body.get("miya"), dict):
            fail("Taqdimot yo‘q")
        til = body.get("til") or (body["miya"].get("meta") or {}).get("til") or "uz"
        if til not in ("uz", "ru", "en"):
            fail("Til noto‘g‘ri")
        oxirgi = self._til_vaqt.get(uid, 0)
        if time.time() - oxirgi < 20:
            fail("Biroz kuting — oldingi tarjima endi tugadi", 429)
        self._til_vaqt[uid] = time.time()
        try:
            m = sxema.normallashtir(body["miya"])
        except ValueError as exc:
            fail(str(exc))
        m["meta"]["til"] = til
        try:
            soni = ai.til_tekshir(m, til, deadline=120.0)
        except Exception as exc:
            fail(f"Tarjima bo‘lmadi: {str(exc)[:120]}", 502)
        ish = body.get("ish")
        if soni and isinstance(ish, str) and re.fullmatch(r"[0-9a-f]{32}", ish):
            with self.ps.db() as cur:
                cur.execute("UPDATE taqdimot_dvigatel_ishlar SET natija=%s, yangilandi=now() WHERE id=%s AND owner_id=%s AND NOT ochirildi "
                            "AND holat='tayyor' AND COALESCE(sorov->>'faqat_reja','false') <> 'true'",
                            (json.dumps(m, ensure_ascii=False), ish, uid))
        return {"miya": m, "soni": soni}

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


def _biriktirma(nom: str) -> str:
    """Content-Disposition: HTTP sarlavhasi faqat latin-1 bo'ladi. Oʻzbekcha «ʻ», kirill harflari bilan nom
    sarlavhani buzib, yuklab olishni 500 xatoga olib kelardi — ASCII nom va filename* (UTF-8) birga beriladi."""
    import unicodedata
    from urllib.parse import quote
    nom = nom or "fayl"
    stem, ext = (nom.rsplit(".", 1) + [""])[:2] if "." in nom else (nom, "")
    asc = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    asc = re.sub(r"[^A-Za-z0-9_\-]+", "_", asc).strip("_") or "taqdimot"
    if ext:
        asc += "." + re.sub(r"[^A-Za-z0-9]+", "", ext)
    return f"attachment; filename=\"{asc}\"; filename*=UTF-8''{quote(nom, safe='')}"


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
        uid = D.actor(authorization)
        oilalar = []
        for o, od in uslub.OILALAR.items():
            pals = []
            for p in uslub.mos_palitralar(o):
                u = uslub.Uslub(f"{o}.{p}.0")
                pals.append({"kod": p, "nom": (uslub.YORUG.get(p) or uslub.QORONGI.get(p) or uslub.DOSKA.get(p))["nom"], "acc": u.acc, "qorongi": u.qorongi})
            oilalar.append({"kod": o, "nom": od["nom"], "turi": od["turi"], "palitralar": pals})
        from . import bloklar_joy
        return Response(json.dumps({"oilalar": oilalar, "animatsiyalar": [{"kod": k, "nom": v["nom"]} for k, v in uslub.ANIMATSIYALAR.items()],
                                    "dizaynlar": bloklar_joy.dizayn_royxati(), "sozlamalar": sozlamalar.KATALOG,
                                    "jami": uslub.uslublar_soni(), "ai": ai.mavjud(), "admin": D.admin(uid)}, ensure_ascii=False),
                        media_type="application/json", headers=NO_STORE)

    @app.get(PREFIX + "/fon/{kod}.jpg")
    def fon(kod: str):
        asos, _, motif = kod.partition("~")
        asos, *qism = asos.split("!")
        if not UVKOD.match(asos) or len(qism) > 2 or any(not re.fullmatch(r"[a-z]{3,10}|r[0-9a-f]{6}", q) for q in qism) \
                or (motif and not re.match(r"^[a-z0-9_]{2,40}$", motif)):
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
                        headers={**NO_STORE, "Content-Disposition": _biriktirma(nom)})

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
                        headers={**NO_STORE, "Content-Disposition": _biriktirma(f"{nom}.pptx")})

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

    @app.get(PREFIX + "/saqlangan")
    def saqlanganlar(limit: int = 80, authorization: str | None = Header(None)):
        uid = D.actor(authorization)
        return Response(json.dumps({"taqdimotlar": D.royxat(uid, limit)}, ensure_ascii=False), media_type="application/json", headers=NO_STORE)

    @app.get(PREFIX + "/saqlangan/{ish}")
    def saqlangan_och(ish: str, authorization: str | None = Header(None)):
        uid = D.actor(authorization)
        return Response(json.dumps(D.ochish(uid, ish), ensure_ascii=False), media_type="application/json", headers=NO_STORE)

    @app.post(PREFIX + "/saqlangan")
    async def saqlangan_yangi(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(D.actor, authorization)
        body = await _json(request)
        return await run_in_threadpool(D.saqla, uid, body)

    @app.post(PREFIX + "/saqlangan/{ish}/korinish")
    async def saqlangan_korinish(ish: str, request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(D.actor, authorization)
        body = await _json(request, 16 * 1024)
        return await run_in_threadpool(D.korinish_saqla, uid, ish, body)

    @app.delete(PREFIX + "/saqlangan/{ish}")
    def saqlangan_ochir(ish: str, authorization: str | None = Header(None)):
        uid = D.actor(authorization)
        return D.ochir(uid, ish)

    @app.post(PREFIX + "/til-togrila")
    async def til_togrila(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(D.actor, authorization)
        body = await _json(request)
        out = await run_in_threadpool(D.til_togrila, uid, body)
        return Response(json.dumps(out, ensure_ascii=False), media_type="application/json", headers=NO_STORE)

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

    # --- AI kutubxonasi: 1–11-sinf, bakalavr, magistratura mavzulari ---
    @app.get(PREFIX + "/kutubxona-ai")
    def kutubxona_ai_royxat(daraja: str = "", sinf: str = "", fan: str = "", q: str = "", hammasi: int = 0, limit: int = 400,
                            authorization: str | None = Header(None)):
        uid = D.actor(authorization)
        barchasi = bool(hammasi) and D.admin(uid)   # admin: yozilmaganlari ham (sinab ko'rish, navbat boshqaruvi)
        out = D.kutub.royxat(daraja[:20], sinf[:20], fan[:120], q[:60], faqat_tayyor=not barchasi, limit=max(0, min(limit, 2000)))
        return Response(json.dumps(out, ensure_ascii=False), media_type="application/json", headers=NO_STORE)

    @app.get(PREFIX + "/kutubxona-ai/{mid}")
    def kutubxona_ai_miya(mid: int, authorization: str | None = Header(None)):
        D.actor(authorization)
        m = D.kutub.miya(mid)
        if not m:
            fail("Mavzu hali yozilmagan", 404)
        return Response(json.dumps(m, ensure_ascii=False), media_type="application/json", headers=NO_STORE)

    def _admin(authorization):
        uid = D.actor(authorization)
        if not D.admin(uid):
            fail("Faqat administrator uchun", 403)
        return uid

    @app.get(PREFIX + "/admin/kutubxona")
    def kutubxona_admin_holat(authorization: str | None = Header(None)):
        _admin(authorization)
        return Response(json.dumps(D.kutub.holat(), ensure_ascii=False), media_type="application/json", headers=NO_STORE)

    @app.post(PREFIX + "/admin/kutubxona/sozlama")
    async def kutubxona_admin_sozlama(request: Request, authorization: str | None = Header(None)):
        await run_in_threadpool(_admin, authorization)
        body = json.loads(await _body(request, MAX_JSON) or b"{}")
        return await run_in_threadpool(D.kutub.sozlama_saqla, body if isinstance(body, dict) else {})

    @app.post(PREFIX + "/admin/kutubxona/yigish")
    async def kutubxona_admin_yigish(request: Request, authorization: str | None = Header(None)):
        await run_in_threadpool(_admin, authorization)
        body = json.loads(await _body(request, MAX_JSON) or b"{}")
        return await run_in_threadpool(D.kutub.yigish_boshla, (body or {}).get("sinflar") or [])

    @app.post(PREFIX + "/admin/kutubxona/navbat")
    async def kutubxona_admin_navbat(request: Request, authorization: str | None = Header(None)):
        await run_in_threadpool(_admin, authorization)
        body = json.loads(await _body(request, MAX_JSON) or b"{}")
        return {"ozgardi": await run_in_threadpool(D.kutub.navbat, body if isinstance(body, dict) else {})}

    @app.post(PREFIX + "/admin/kutubxona/sinov")
    async def kutubxona_admin_sinov(request: Request, authorization: str | None = Header(None)):
        """Bitta mavzuni hozir yozib ko'rish (sifatni tekshirish uchun; yozuvchi yoqilmagan bo'lsa ham)."""
        await run_in_threadpool(_admin, authorization)
        body = json.loads(await _body(request, MAX_JSON) or b"{}")
        mid = (body or {}).get("id")
        if not isinstance(mid, int):
            fail("Mavzu tanlanmagan")
        if not ai.mavjud():
            fail("AI kaliti serverda sozlanmagan", 503)
        return await run_in_threadpool(D.kutub.bittasini, mid, D.pool)

    @app.post(PREFIX + "/admin/kutubxona/dastur")
    async def kutubxona_admin_dastur(request: Request, authorization: str | None = Header(None)):
        """Fan dasturi (xlsx, docx, pdf, csv, txt) → mavzular reestriga."""
        await run_in_threadpool(_admin, authorization)
        data = await _body(request, MAX_FILE * 3)
        from urllib.parse import unquote
        meta = {k: unquote(request.headers.get(f"x-{k}", "")) for k in ("daraja", "sinf", "fan", "yonalish")}
        nom = unquote(request.headers.get("x-fayl-nomi", "dastur.txt"))
        try:
            return await run_in_threadpool(D.kutub.dastur_yukla, nom, data, meta)
        except ValueError as exc:
            fail(str(exc))

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
        return Response(data, media_type=mime, headers={**NO_STORE, "Content-Disposition": _biriktirma(nom)})

    return D

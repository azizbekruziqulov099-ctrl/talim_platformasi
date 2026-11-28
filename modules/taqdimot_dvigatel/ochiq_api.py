"""Ochiq dars API (/api/taqdimot-dvigatel/ochiq-dars/...): katalog, qo'lda/tezkor tuzish, «AI yozsin» navbati,
Word ishlanma va PPTX. Taqdimot dvigatelining jadvallaridan foydalanadi (AI ishlari — taqdimot_dvigatel_ishlar, sorov.ochiq_dars=true)."""
from __future__ import annotations

import json
import re
import uuid

from fastapi import Header, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool

from . import ai, ishlanma, ochiq_ai, ochiq_dars as od, sxema

DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
SOROV_KALIT = ("daraja", "sinf", "fan", "mavzu", "format", "andoza", "oquvchilar", "guruhlar", "rejim", "tanlov", "guruhlash",
               "birlashtirish", "urug", "metodik_maqsad", "istak")


class OchiqDars:
    def __init__(self, D, fail):
        self.D = D
        self.fail = fail

    # ---------------------------------------------------------------- yordamchilar
    def sorov(self, body) -> dict:
        s = body.get("sorov") if isinstance(body, dict) and isinstance(body.get("sorov"), dict) else {}
        out = {}
        for k in SOROV_KALIT:
            v = s.get(k)
            if v is None:
                continue
            if k == "tanlov":
                if isinstance(v, dict):
                    out[k] = {str(a)[:3]: str(b)[:40] for a, b in list(v.items())[:20]}
            elif k in ("oquvchilar", "guruhlar", "urug"):
                try:
                    out[k] = int(v)
                except (TypeError, ValueError):
                    pass
            else:
                out[k] = sxema.t(v, 600 if k == "istak" else 300)
        return out

    def miya(self, uid, body):
        """Mavzu materiali: kutubxona (id), «Mening taqdimotlarim» (ish) yoki to'g'ridan-to'g'ri miya. Yo'q bo'lsa — None."""
        manba = body.get("manba") if isinstance(body.get("manba"), dict) else {}
        m = None
        if manba.get("kutubxona") is not None:
            try:
                m = self.D.kutub.miya(int(manba["kutubxona"]))
            except (TypeError, ValueError):
                m = None
            if not m:
                self.fail("Mavzu kutubxonada topilmadi", 404)
        elif isinstance(manba.get("ish"), str):
            m = self.D.ochish(uid, manba["ish"]).get("miya")
        elif isinstance(body.get("miya"), dict):
            m = body["miya"]
        if not m:
            return None
        try:
            return sxema.normallashtir(m)
        except ValueError as exc:
            self.fail(str(exc))

    @staticmethod
    def _toldir(sorov, miya):
        meta = (miya or {}).get("meta") or {}
        for k in ("fan", "mavzu", "daraja", "sinf"):
            if not sorov.get(k) and meta.get(k):
                sorov[k] = meta[k]
        return sorov

    def _dars_ol(self, body):
        d = body.get("dars") if isinstance(body, dict) else None
        if not isinstance(d, dict) or d.get("sxema") != od.SXEMA or not isinstance(d.get("bosqichlar"), list):
            self.fail("Dars rejasi yuborilmadi")
        return d

    # ---------------------------------------------------------------- tuzish
    def tuz(self, uid, body):
        if not isinstance(body, dict):
            self.fail("So‘rov noto‘g‘ri")
        miya = self.miya(uid, body)
        s = self._toldir(self.sorov(body), miya)
        if s.get("rejim") == "ai":
            s["rejim"] = "tezkor"
        if not s.get("mavzu"):
            self.fail("Mavzuni tanlang yoki yozing")
        # «AI yozsin» rejasida metod almashtirilganda AI yozgan masalliq saqlanib qolsin
        mas = sxema.masalliq_toza(body["masalliq"]) if isinstance(body.get("masalliq"), dict) else None
        try:
            dars = od.tuz(s, miya, mas=mas)
        except ValueError as exc:
            self.fail(str(exc))
        if mas:
            dars["meta"]["masalliq_bor"] = True
        return dars

    def ai_boshla(self, uid, body):
        if not ai.mavjud():
            self.fail("AI kaliti serverda sozlanmagan — «Tezkor» yoki «O‘zim tanlayman» rejimidan foydalaning.", 503)
        if not isinstance(body, dict):
            self.fail("So‘rov noto‘g‘ri")
        miya = self.miya(uid, body)
        s = self._toldir(self.sorov(body), miya)
        if not s.get("mavzu"):
            self.fail("Mavzuni tanlang yoki yozing")
        try:
            od.yosh_kodi(s.get("daraja") or "maktab", s.get("sinf"))
        except ValueError as exc:
            self.fail(str(exc))
        s["rejim"] = "ai"
        manba = body.get("manba") if isinstance(body.get("manba"), dict) else {}
        yozuv = {**s, "ochiq_dars": True, "manba": {k: manba[k] for k in ("kutubxona", "ish") if k in manba}}
        admin = self.D.admin(uid)
        with self.D.ps.db() as cur:
            if not admin:
                from .api import AI_KUNLIK
                cur.execute("SELECT count(*) AS n FROM taqdimot_dvigatel_ishlar WHERE owner_id=%s AND yaratildi > now() - interval '1 day' "
                            "AND COALESCE(sorov->>'faqat_reja', 'false') <> 'true' AND COALESCE(sorov->>'qolda', 'false') <> 'true'", (uid,))
                if cur.fetchone()["n"] >= AI_KUNLIK:
                    self.fail(f"Bugungi AI limiti tugadi ({AI_KUNLIK} ta). «Tezkor» rejimdan foydalaning.", 429)
            ish = uuid.uuid4().hex
            if not admin:                      # ochiq dars (AI) = 10 kapul
                from . import kapul
                yozuv["kapul"] = kapul.NARX["ochiq_dars"]
                kapul.yech(cur, uid, yozuv["kapul"], "ochiq_dars", ish)
            cur.execute("INSERT INTO taqdimot_dvigatel_ishlar(id, owner_id, sorov, ochirildi) VALUES(%s,%s,%s,true)",
                        (ish, uid, json.dumps(yozuv, ensure_ascii=False)))
        self.D.pool.submit(self._ai_ish, ish, s, miya)
        return {"ish": ish, "holat": "navbatda"}

    def _ai_ish(self, ish, s, miya):
        try:
            with self.D.ps.db() as cur:
                cur.execute("UPDATE taqdimot_dvigatel_ishlar SET holat='yozilmoqda' WHERE id=%s", (ish,))
            try:
                dars = ochiq_ai.tuz(s, miya)
            except Exception as exc:   # AI ishlamasa — tezkor reja, sababi bilan
                dars = od.tuz({**s, "rejim": "tezkor"}, miya)
                dars["meta"]["ogohlantirish"] = f"AI javob bermadi ({str(exc)[:80]}) — reja tezkor rejimda tuzildi."
            with self.D.ps.db() as cur:
                cur.execute("UPDATE taqdimot_dvigatel_ishlar SET holat='tayyor', natija=%s, tugadi=now() WHERE id=%s",
                            (json.dumps(dars, ensure_ascii=False), ish))
        except Exception as exc:
            try:
                with self.D.ps.db() as cur:
                    cur.execute("UPDATE taqdimot_dvigatel_ishlar SET holat='xato', xato=%s, tugadi=now() WHERE id=%s "
                                "RETURNING owner_id, COALESCE((sorov->>'kapul')::int, 0) AS kapul", (str(exc)[:300], ish))
                    r = cur.fetchone()
                    if r and r["kapul"]:
                        from . import kapul
                        kapul.qaytar(cur, r["owner_id"], r["kapul"], "ochiq_dars", ish)
            except Exception:
                pass

    def ai_holat(self, uid, ish):
        if not re.fullmatch(r"[0-9a-f]{32}", ish or ""):
            self.fail("Ish raqami noto‘g‘ri", 404)
        with self.D.ps.db() as cur:
            cur.execute("SELECT holat, natija, xato, owner_id, sorov FROM taqdimot_dvigatel_ishlar WHERE id=%s", (ish,))
            r = cur.fetchone()
        so = (r["sorov"] if isinstance(r["sorov"], dict) else json.loads(r["sorov"] or "{}")) if r else {}
        if not r or r["owner_id"] != uid or not so.get("ochiq_dars"):
            self.fail("Ish topilmadi", 404)
        out = {"holat": r["holat"]}
        if r["holat"] == "tayyor":
            out["dars"] = r["natija"] if isinstance(r["natija"], dict) else json.loads(r["natija"])
        elif r["holat"] == "xato":
            out["xato"] = r["xato"]
        return out

    # ---------------------------------------------------------------- eksport
    def docx(self, uid, body):
        dars = self._dars_ol(body)
        miya = self.miya(uid, body)
        if not self.D.eksport.acquire(timeout=20):
            self.fail("Server band, birozdan keyin qayta urinib ko‘ring", 503)
        try:
            data = ishlanma.docx_yoz(dars, miya)
        except (KeyError, TypeError, IndexError, AttributeError, ValueError):
            self.fail("Dars rejasi buzilgan — qayta tuzing")
        finally:
            self.D.eksport.release()
        return data, self._nom(dars)

    def pptx(self, uid, body):
        dars = self._dars_ol(body)
        miya = self.miya(uid, body)
        try:
            m = od.ochiq_miya(dars, miya)
        except (KeyError, TypeError, IndexError, AttributeError, ValueError):
            self.fail("Dars rejasi buzilgan — qayta tuzing")
        uslub = {k: body[k] for k in ("seed", "uslub", "anim", "oila", "palitra", "bolim_titul", "rasm_avto", "anim2", "dizayn", "sozlama") if k in body}
        data, _nom = self.D.pptx({**uslub, "miya": m})
        return data, self._nom(dars)

    @staticmethod
    def _nom(dars):
        mt = dars.get("meta") or {}
        return "Ochiq_dars_" + (re.sub(r"[^\w\-]+", "_", str(mt.get("mavzu") or "dars"))[:60] or "dars")


def register(app, D, prefix, fail, json_ol, biriktirma, no_store):
    O = OchiqDars(D, fail)
    p = prefix + "/ochiq-dars"

    def _j(obj):
        return Response(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), media_type="application/json", headers=no_store)

    @app.get(p + "/katalog")
    def ochiq_katalog(authorization: str | None = Header(None)):
        D.actor(authorization)
        from . import darslar
        return _j({**od.katalog(), "ai": ai.mavjud(), "darslar": darslar.royxat()})

    @app.get(p + "/rasmlar")
    def ochiq_rasmlar(q: str = "", fan: str = "", authorization: str | None = Header(None)):
        """Rasm almashtirish uchun nomzodlar: so'rovga (o'zbekcha, ruscha, inglizcha) eng mos rasmlar, keyin fanning universal rasmlari."""
        D.actor(authorization)
        from . import rasm_tanla, rasmlar
        q = (q or "").strip()[:160]
        fan = (fan or "").strip()[:120]
        out, bor = [], set()

        def qosh(kalit, nom):
            if kalit and kalit not in bor and rasmlar.bor(kalit) and (rasmlar.malumot(kalit).get("tur") or "rasm") == "rasm":
                bor.add(kalit)
                out.append({"kalit": kalit, "nom": re.sub(r"\s*\[[^\]]*\]$", "", nom or "")})

        if q:
            for kalit in (rasm_tanla.titul_rasmi(q, fan), rasm_tanla.buyum_rasmi(q)):
                if kalit:
                    r = rasmlar.malumot(kalit)
                    qosh(kalit, r.get("nom") or "")
            for kalit, nom in rasm_tanla.katalog(q, fan, 40):
                if "rejada)" not in nom:
                    qosh(kalit, nom)
        if len(out) < 36:
            for kalit in rasm_tanla.universal_hovuz(fan)[:60]:
                qosh(kalit, rasmlar.malumot(kalit).get("nom") or "")
                if len(out) >= 36:
                    break
        return _j({"rasmlar": out[:36]})

    @app.post(p + "/tuz")
    async def ochiq_tuz(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(D.actor, authorization)
        body = await json_ol(request)
        return _j(await run_in_threadpool(O.tuz, uid, body))

    @app.post(p + "/ai")
    async def ochiq_ai_boshla(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(D.actor, authorization)
        body = await json_ol(request)
        return await run_in_threadpool(O.ai_boshla, uid, body)

    @app.get(p + "/ai/{ish}")
    def ochiq_ai_holat(ish: str, authorization: str | None = Header(None)):
        uid = D.actor(authorization)
        return _j(O.ai_holat(uid, ish))

    @app.post(p + "/docx")
    async def ochiq_docx(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(D.actor, authorization)
        body = await json_ol(request)
        data, nom = await run_in_threadpool(O.docx, uid, body)
        return Response(data, media_type=DOCX, headers={**no_store, "Content-Disposition": biriktirma(f"{nom}.docx")})

    @app.post(p + "/pptx")
    async def ochiq_pptx(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(D.actor, authorization)
        body = await json_ol(request)
        data, nom = await run_in_threadpool(O.pptx, uid, body)
        return Response(data, media_type=PPTX, headers={**no_store, "Content-Disposition": biriktirma(f"{nom}.pptx")})

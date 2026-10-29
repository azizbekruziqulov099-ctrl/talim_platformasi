"""REV209: SERTIFIKATGA TAYYORLOV GURUHLARI (exam_prep).

Oqim:
  1. O'quvchi (saytda) yoki ota-ona (Telegram botda) imtihonni tanlab ARIZA beradi — avtomatik a'zo bo'lmaydi.
  2. Administrator arizalarni ko'radi, istasa daraja testi ballini kiritadi.
  3. «Guruhlash» — bir imtihon bo'yicha kutayotgan arizalar ballga qarab tartiblanib, 30 tadan guruhlarga bo'linadi
     (kuchlilar bilan boshlovchilar alohida). Har guruhga Kabutar'da alohida guruh-chat ochiladi.
  4. «Qayta guruhlash» — imtihon/test natijalari kiritilgach, shu imtihonning barcha o'quvchilari yana darajasiga qarab
     30 tadan qayta bo'linadi (bir-biriga yaqin darajadagilar birga).
  5. Haftalik reyting — har guruh ichida so'nggi 7 kun natijalari bo'yicha.
Sinf bo'yicha tavsiya cheklov emas (katalog siyosati): boshqa imtihon ham tanlanadi, faqat eslatma chiqadi.
Rasmiy sertifikat berilmaydi — bu tayyorlov.
"""
import json
import os
from functools import lru_cache

from fastapi import APIRouter, Body, Header, HTTPException

KATALOG = os.path.join(os.path.dirname(__file__), "sertifikat_data", "katalog.json")
SIGIM = 30


@lru_cache(maxsize=1)
def katalog():
    with open(KATALOG, encoding="utf-8") as f:
        return json.load(f)


def imtihon(iid):
    return next((e for e in katalog()["exams"] if e["id"] == iid), None)


def jadvallar(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS sertifikat_arizalar(
        id BIGSERIAL PRIMARY KEY, user_id BIGINT, imtihon_id TEXT NOT NULL, ism TEXT, telefon TEXT, sinf INT,
        manba TEXT NOT NULL DEFAULT 'sayt', telegram_id BIGINT, holat TEXT NOT NULL DEFAULT 'yangi',
        daraja_ball NUMERIC, guruh_id BIGINT, izoh TEXT, yaratilgan TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE INDEX IF NOT EXISTS sert_ariza_imtihon ON sertifikat_arizalar(imtihon_id, holat)")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS sert_ariza_bir_marta ON sertifikat_arizalar(user_id, imtihon_id)
                   WHERE user_id IS NOT NULL AND holat <> 'rad'""")
    cur.execute("""CREATE TABLE IF NOT EXISTS sertifikat_guruhlari(
        id BIGSERIAL PRIMARY KEY, imtihon_id TEXT NOT NULL, nomi TEXT NOT NULL, tartib INT NOT NULL DEFAULT 1,
        sinf_dan INT, sinf_gacha INT, daraja TEXT, sigim INT NOT NULL DEFAULT 30, teacher_id BIGINT,
        chat_guruh_id BIGINT, holat TEXT NOT NULL DEFAULT 'faol', yaratilgan TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS sertifikat_natijalar(
        id BIGSERIAL PRIMARY KEY, ariza_id BIGINT NOT NULL, ball NUMERIC NOT NULL, turi TEXT NOT NULL DEFAULT 'mashq',
        sana TIMESTAMPTZ NOT NULL DEFAULT NOW())""")


def _chat_guruh(cur, nomi, gid):
    try:
        cur.execute("SAVEPOINT sert_chat")
        cur.execute("SELECT id FROM chat_guruhlari WHERE manba_turi='sertifikat' AND manba_id=%s", (gid,))
        r = cur.fetchone()
        if r:
            cur.execute("UPDATE chat_guruhlari SET nomi=%s WHERE id=%s", (nomi, r["id"]))
            cid = r["id"]
        else:
            cur.execute("INSERT INTO chat_guruhlari(nomi,turi,manba_turi,manba_id) VALUES(%s,'guruh','sertifikat',%s) RETURNING id", (nomi, gid))
            cid = cur.fetchone()["id"]
        cur.execute("RELEASE SAVEPOINT sert_chat")
        return cid
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT sert_chat")
        return None


def _chat_azolar(cur, cid, user_ids, teacher_id=None):
    if not cid:
        return
    try:
        cur.execute("SAVEPOINT sert_az")
        cur.execute("DELETE FROM chat_azolari WHERE guruh_id=%s AND NOT (user_id = ANY(%s))", (cid, list(user_ids) + ([teacher_id] if teacher_id else []) or [0]))
        for u in list(user_ids) + ([teacher_id] if teacher_id else []):
            cur.execute("INSERT INTO chat_azolari(guruh_id,user_id) VALUES(%s,%s) ON CONFLICT DO NOTHING", (cid, u))
        cur.execute("RELEASE SAVEPOINT sert_az")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT sert_az")


def _ball(cur, ariza):
    """Darajani bildiruvchi ball: oxirgi imtihon/test natijasi, bo'lmasa — daraja testi, bo'lmasa — 0."""
    cur.execute("SELECT ball FROM sertifikat_natijalar WHERE ariza_id=%s AND turi IN ('imtihon','daraja') ORDER BY sana DESC LIMIT 1", (ariza["id"],))
    r = cur.fetchone()
    if r:
        return float(r["ball"])
    return float(ariza.get("daraja_ball") or 0)


def guruhla(cur, imtihon_id, qayta=False):
    """Kutayotganlarni (qayta=True bo'lsa — hammasini) ballga qarab 30 tadan guruhlaydi."""
    e = imtihon(imtihon_id)
    if not e:
        raise HTTPException(status_code=400, detail="Imtihon topilmadi")
    holatlar = ("yangi", "qabul", "guruhda") if qayta else ("yangi", "qabul")
    cur.execute("SELECT * FROM sertifikat_arizalar WHERE imtihon_id=%s AND holat = ANY(%s) ORDER BY id", (imtihon_id, list(holatlar)))
    arizalar = [dict(r) for r in cur.fetchall()]
    if not arizalar:
        return {"guruhlar": 0, "oquvchilar": 0}
    for a in arizalar:
        a["_ball"] = _ball(cur, a)
    arizalar.sort(key=lambda a: (-a["_ball"], a["id"]))
    if qayta:   # eski guruhlarni yopamiz — yangi tarkib bilan qayta ochiladi
        cur.execute("UPDATE sertifikat_guruhlari SET holat='yopiq' WHERE imtihon_id=%s AND holat='faol'", (imtihon_id,))
        bor = 0
    else:
        cur.execute("SELECT COALESCE(MAX(tartib),0) AS m FROM sertifikat_guruhlari WHERE imtihon_id=%s", (imtihon_id,))
        bor = cur.fetchone()["m"]
    n = (len(arizalar) + SIGIM - 1) // SIGIM
    hajm = (len(arizalar) + n - 1) // n   # teng bo'lak: 31 kishi → 16 + 15, bitta 1 kishilik guruh emas
    natija = []
    for i in range(n):
        bolak = arizalar[i * hajm:(i + 1) * hajm]
        if not bolak:
            continue
        tartib = bor + i + 1
        sinflar = [a["sinf"] for a in bolak if a.get("sinf")]
        daraja = "kuchli" if i == 0 and n > 1 else "boshlovchi" if i == n - 1 and n > 1 else "o'rta" if n > 2 else ""
        nomi = f"🎓 {e['shortTitle']} · {tartib}-guruh" + (f" ({daraja})" if daraja else "")
        cur.execute("""INSERT INTO sertifikat_guruhlari(imtihon_id,nomi,tartib,sinf_dan,sinf_gacha,daraja,sigim)
                       VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (imtihon_id, nomi, tartib, min(sinflar) if sinflar else None, max(sinflar) if sinflar else None, daraja, SIGIM))
        gid = cur.fetchone()["id"]
        cid = _chat_guruh(cur, nomi, gid)
        cur.execute("UPDATE sertifikat_guruhlari SET chat_guruh_id=%s WHERE id=%s", (cid, gid))
        for a in bolak:
            cur.execute("UPDATE sertifikat_arizalar SET holat='guruhda', guruh_id=%s, yangilangan=NOW() WHERE id=%s", (gid, a["id"]))
        _chat_azolar(cur, cid, [a["user_id"] for a in bolak if a.get("user_id")])
        natija.append({"id": gid, "nomi": nomi, "soni": len(bolak)})
    return {"guruhlar": len(natija), "oquvchilar": len(arizalar), "royxat": natija}


def reyting(cur, guruh_id, kun=7, limit=10):
    cur.execute("""SELECT a.id, COALESCE(u.full_name, a.ism, '') AS ism, COALESCE(SUM(n.ball),0) AS ball
                   FROM sertifikat_arizalar a LEFT JOIN users u ON u.user_id=a.user_id
                   LEFT JOIN sertifikat_natijalar n ON n.ariza_id=a.id AND n.sana > NOW() - (%s || ' days')::interval
                   WHERE a.guruh_id=%s GROUP BY a.id, u.full_name, a.ism ORDER BY ball DESC, a.id LIMIT %s""", (str(kun), guruh_id, limit))
    out = []
    for i, r in enumerate(cur.fetchall(), 1):
        q = str(r["ism"] or "").split()
        out.append({"orin": i, "ism": (q[0] + (f" {q[1][0]}." if len(q) > 1 else "")) if q else f"{i}-o'rin", "ball": float(r["ball"])})
    return out


def create_router(check_admin, db, user_from_token):
    router = APIRouter(prefix="/api/sertifikat", tags=["sertifikat"])
    admin = APIRouter(prefix="/api/admin/sertifikat", tags=["sertifikat-admin"])

    def ish(fn):
        conn = db()
        cur = conn.cursor()
        try:
            jadvallar(cur)
            r = fn(cur)
            conn.commit()
            return r
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.get("/katalog")
    def kat():
        k = katalog()
        return {"imtihonlar": k["exams"], "darajalar": k["cefrLevels"], "siyosat": k["policy"]}

    @router.get("/mening")
    def mening(token: str):
        uid = user_from_token(token)

        def f(cur):
            cur.execute("""SELECT a.id, a.imtihon_id, a.holat, a.yaratilgan, g.nomi AS guruh, g.chat_guruh_id
                           FROM sertifikat_arizalar a LEFT JOIN sertifikat_guruhlari g ON g.id=a.guruh_id
                           WHERE a.user_id=%s ORDER BY a.id DESC""", (uid,))
            return {"arizalar": [dict(r) for r in cur.fetchall()]}
        return ish(f)

    @router.post("/ariza")
    def ariza(token: str, body: dict = Body(...)):
        uid = user_from_token(token)
        iid = str(body.get("imtihon_id") or "")
        if not imtihon(iid):
            raise HTTPException(status_code=400, detail="Imtihon tanlanmagan")

        def f(cur):
            cur.execute("SELECT to_jsonb(u) AS j FROM users u WHERE u.user_id=%s", (uid,))
            r = cur.fetchone()
            j = (r or {}).get("j") or {}
            u = {"full_name": j.get("full_name") or j.get("ism"), "class": j.get("class"), "phone": j.get("phone") or j.get("telefon")}
            import re as _re
            m = _re.search(r"\d+", str(u.get("class") or ""))
            try:
                cur.execute("""INSERT INTO sertifikat_arizalar(user_id,imtihon_id,ism,telefon,sinf,manba)
                               VALUES(%s,%s,%s,%s,%s,'sayt') RETURNING id""",
                            (uid, iid, u.get("full_name"), u.get("phone"), int(m.group()) if m else None))
            except Exception:
                raise HTTPException(status_code=409, detail="Bu imtihonga arizangiz allaqachon bor")
            return {"ok": True, "id": cur.fetchone()["id"]}
        return ish(f)

    @router.post("/ariza_bot")
    def ariza_bot(body: dict = Body(...), x_bot_token: str = Header(default="")):
        """Telegram bot arizasi (bot va sayt bir xil BOT_TOKEN'ni biladi)."""
        if not x_bot_token or x_bot_token != os.environ.get("BOT_TOKEN", ""):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        iid = str(body.get("imtihon_id") or "")
        if not imtihon(iid):
            raise HTTPException(status_code=400, detail="Imtihon topilmadi")

        def f(cur):
            uid = None   # bot arizasi — administrator keyin saytdagi hisobga bog'laydi (telefon bo'yicha)
            cur.execute("""INSERT INTO sertifikat_arizalar(user_id,imtihon_id,ism,telefon,sinf,manba,telegram_id)
                           VALUES(%s,%s,%s,%s,%s,'bot',%s) RETURNING id""",
                        (uid, iid, str(body.get("ism") or "")[:120], str(body.get("telefon") or "")[:40],
                         int(body["sinf"]) if str(body.get("sinf") or "").isdigit() else None, body.get("telegram_id")))
            return {"ok": True, "id": cur.fetchone()["id"]}
        return ish(f)

    # ───── admin ─────
    @admin.get("/arizalar")
    def arizalar(token: str, imtihon_id: str = "", holat: str = ""):
        check_admin(token)

        def f(cur):
            sql = """SELECT a.*, g.nomi AS guruh FROM sertifikat_arizalar a LEFT JOIN sertifikat_guruhlari g ON g.id=a.guruh_id WHERE TRUE"""
            p = []
            if imtihon_id:
                sql += " AND a.imtihon_id=%s"
                p.append(imtihon_id)
            if holat:
                sql += " AND a.holat=%s"
                p.append(holat)
            cur.execute(sql + " ORDER BY a.id DESC LIMIT 2000", p)
            rows = [dict(r) for r in cur.fetchall()]
            cur.execute("SELECT imtihon_id, holat, COUNT(*) AS n FROM sertifikat_arizalar GROUP BY 1,2")
            stat = {}
            for r in cur.fetchall():
                stat.setdefault(r["imtihon_id"], {})[r["holat"]] = r["n"]
            return {"arizalar": rows, "statistika": stat}
        return ish(f)

    @admin.put("/ariza/{aid}")
    def ariza_yangila(aid: int, token: str, body: dict = Body(...)):
        check_admin(token)

        def f(cur):
            if "daraja_ball" in body:
                cur.execute("UPDATE sertifikat_arizalar SET daraja_ball=%s, holat=CASE WHEN holat='yangi' THEN 'qabul' ELSE holat END WHERE id=%s",
                            (float(body["daraja_ball"]), aid))
                cur.execute("INSERT INTO sertifikat_natijalar(ariza_id,ball,turi) VALUES(%s,%s,'daraja')", (aid, float(body["daraja_ball"])))
            if body.get("holat") in ("yangi", "qabul", "rad"):
                cur.execute("UPDATE sertifikat_arizalar SET holat=%s WHERE id=%s", (body["holat"], aid))
            return {"ok": True}
        return ish(f)

    @admin.post("/natija")
    def natija(token: str, body: dict = Body(...)):
        """Imtihon yoki haftalik mashq natijasi: {ariza_id, ball, turi: 'imtihon'|'mashq'}."""
        check_admin(token)

        def f(cur):
            cur.execute("INSERT INTO sertifikat_natijalar(ariza_id,ball,turi) VALUES(%s,%s,%s)",
                        (int(body["ariza_id"]), float(body["ball"]), body.get("turi") if body.get("turi") in ("imtihon", "mashq", "daraja") else "mashq"))
            return {"ok": True}
        return ish(f)

    @admin.post("/guruhla")
    def guruhla_api(token: str, imtihon_id: str, qayta: bool = False):
        check_admin(token)
        return ish(lambda cur: guruhla(cur, imtihon_id, qayta))

    @admin.get("/guruhlar")
    def guruhlar(token: str, imtihon_id: str = ""):
        check_admin(token)

        def f(cur):
            cur.execute("""SELECT g.*, (SELECT COUNT(*) FROM sertifikat_arizalar a WHERE a.guruh_id=g.id) AS soni
                           FROM sertifikat_guruhlari g WHERE g.holat='faol' AND (%s='' OR g.imtihon_id=%s) ORDER BY g.imtihon_id, g.tartib""",
                        (imtihon_id, imtihon_id))
            out = [dict(r) for r in cur.fetchall()]
            for g in out:
                g["reyting"] = reyting(cur, g["id"], limit=5)
            return {"guruhlar": out}
        return ish(f)

    return [router, admin]

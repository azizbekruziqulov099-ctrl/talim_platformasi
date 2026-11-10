"""REV484: yakuniy baho va ota-onaga haftalik hisobot.
Yakuniy baho = uyda o'zi 30% + kurs (guruh mashg'ulotlari va o'qituvchi baholari) 40% + onlayn imtihon (oylik/maksimum) 10%
+ o'qituvchi imtihoni 20%. Qaysidir qism bo'lmasa — qolganlari ulushiga qarab qayta taqsimlanadi; o'qituvchi qismi bo'lmasa
baho «tasdiqlanmagan». 5 ballik: 86–100 → 5, 71–85 → 4, 56–70 → 3, undan past → 2."""
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

ULUSH = {"uy": 30, "kurs": 40, "onlayn": 10, "imtihon": 20}
NOMI = {"uy": "🏠 Uyda o‘zi", "kurs": "👩‍🏫 Kurs / repetitor", "onlayn": "💻 Onlayn imtihon", "imtihon": "✍️ O‘qituvchi imtihoni"}


def besh_ball(foiz):
    if foiz is None:
        return None
    return 5 if foiz >= 86 else 4 if foiz >= 71 else 3 if foiz >= 56 else 2


def yigindi(qismlar):
    """qismlar: {kalit: foiz|None} → {"foiz", "ball", "tasdiqlangan", "qismlar":[...]}"""
    bor = {k: v for k, v in qismlar.items() if v is not None}
    jami_ulush = sum(ULUSH[k] for k in bor)
    foiz = round(sum(ULUSH[k] * v for k, v in bor.items()) / jami_ulush) if jami_ulush else None
    return {"foiz": foiz, "ball": besh_ball(foiz), "tasdiqlangan": qismlar.get("imtihon") is not None or qismlar.get("kurs") is not None,
            "qismlar": [{"kalit": k, "nom": NOMI[k], "ulush": ULUSH[k], "foiz": qismlar.get(k)} for k in ULUSH]}


def _sp(cur, sql, args):
    """Jadval hali bo'lmasa ham yiqilmasin."""
    try:
        cur.execute("SAVEPOINT yk"); cur.execute(sql, args); r = cur.fetchall(); cur.execute("RELEASE SAVEPOINT yk"); return r
    except Exception:   # noqa: BLE001
        cur.execute("ROLLBACK TO SAVEPOINT yk"); return []


def _ort(rows, t="togri", j="jami"):
    rr = [r for r in rows if (r.get(j) or 0) > 0]
    return round(100 * sum(r[t] for r in rr) / sum(r[j] for r in rr)) if rr else None


def hisobla(cur, uid, kalit, guruh_ids=()):
    uy = _ort(_sp(cur, "SELECT togri, jami FROM kurs_dars_holat WHERE user_id=%s AND kalit=%s AND topic_code NOT LIKE 'NZ:%%'", (uid, kalit))
              + _sp(cur, "SELECT togri, jami FROM kurs_nazorat WHERE user_id=%s AND kalit=%s AND tur IN ('mini','oraliq')", (uid, kalit)))
    onlayn = _ort(_sp(cur, "SELECT togri, jami FROM kurs_nazorat WHERE user_id=%s AND kalit=%s AND tur IN ('oylik','maksimum')", (uid, kalit)))
    kurs = imtihon = None
    if guruh_ids:
        bah = _sp(cur, "SELECT turi, ball FROM kurs_baho WHERE user_id=%s AND guruh_id = ANY(%s)", (uid, list(guruh_ids)))
        kb = [b["ball"] for b in bah if b["turi"] == "kurs"]; ib = [b["ball"] for b in bah if b["turi"] == "imtihon"]
        jav = _sp(cur, """SELECT COUNT(*) FILTER (WHERE togri) AS togri, COUNT(*) AS jami FROM kurs_dars_javob WHERE user_id=%s""", (uid,))
        mashgulot = _ort(jav) if jav and jav[0]["jami"] else None
        parts = [x for x in [mashgulot, round(sum(kb) / len(kb)) if kb else None] if x is not None]
        kurs = round(sum(parts) / len(parts)) if parts else None
        imtihon = round(sum(ib) / len(ib)) if ib else None
    return yigindi({"uy": uy, "kurs": kurs, "onlayn": onlayn, "imtihon": imtihon})


def jadval(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_baho (id BIGSERIAL PRIMARY KEY, guruh_id BIGINT NOT NULL, user_id BIGINT NOT NULL, turi TEXT NOT NULL,
        ball INT NOT NULL, izoh TEXT NOT NULL DEFAULT '', qoydi BIGINT NOT NULL, vaqt TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE INDEX IF NOT EXISTS kurs_baho_u ON kurs_baho(user_id, guruh_id)")
    cur.execute("CREATE TABLE IF NOT EXISTS haftalik_hisobot (parent_id BIGINT NOT NULL, child_id BIGINT NOT NULL, hafta DATE NOT NULL, PRIMARY KEY (parent_id, child_id, hafta))")


def haftalik(cur, bola_id):
    """Oxirgi 7 kun: darslar, nazoratlar, ko'nikmalar, o'yin qulflari."""
    darslar = _sp(cur, """SELECT mavzu AS nom, yulduz FROM bola_dars_holat WHERE child_id=%s AND tugatilgan_at > NOW() - INTERVAL '7 days'
                          ORDER BY tugatilgan_at""", (bola_id,))
    kurs_d = _sp(cur, """SELECT topic_code, togri, jami FROM kurs_dars_holat WHERE user_id=%s AND tugadi_at > NOW() - INTERVAL '7 days'
                         AND topic_code NOT LIKE 'NZ:%%'""", (bola_id,))
    nz = _sp(cur, """SELECT kod, tur, togri, jami, otdi, halollik FROM kurs_nazorat WHERE user_id=%s AND oxirgi_urinish > NOW() - INTERVAL '7 days'""", (bola_id,))
    kn = _sp(cur, "SELECT konikma, togri, jami FROM konikma_holat WHERE user_id=%s", (bola_id,))
    ql = _sp(cur, "SELECT kun, gacha, darslar FROM nazoratchi_qulf WHERE user_id=%s AND yaratildi > NOW() - INTERVAL '7 days'", (bola_id,))
    vaqt = _sp(cur, "SELECT COALESCE(SUM(faol_soniya),0) AS s FROM bola_dars_faollik WHERE child_id=%s AND sana > CURRENT_DATE - 7", (bola_id,))
    try:
        from modules.konikma import korinish
        konikmalar = korinish(kn)
    except Exception:   # noqa: BLE001
        konikmalar = []
    return {"darslar": len(darslar) + len(kurs_d), "dars_nomlari": [d["nom"] for d in darslar if d.get("nom")][:12],
            "test_foiz": _ort(kurs_d), "daqiqa": round(int((vaqt[0]["s"] if vaqt else 0) or 0) / 60),
            "nazoratlar": [{"kod": r["kod"], "tur": r["tur"], "togri": r["togri"], "jami": r["jami"], "otdi": r["otdi"],
                            "diqqat": bool((r["halollik"] or {}).get("yashirildi") or (r["halollik"] or {}).get("nusxa") or (r["halollik"] or {}).get("kamera") == "rad")} for r in nz],
            "konikmalar": konikmalar, "qulflar": [{"kun": r["kun"], "gacha": r["gacha"].isoformat(), "darslar": r["darslar"]} for r in ql]}


def hisobot_matni(ism, h):
    q = [f"📅 {ism} — haftalik hisobot", f"📚 O‘tilgan darslar: {h['darslar']}" + (f" (testlar: {h['test_foiz']}%)" if h["test_foiz"] is not None else ""),
         f"⏱ Darsda: {h['daqiqa']} daqiqa"]
    if h["nazoratlar"]:
        q.append("📝 Nazoratlar: " + ", ".join(f"{n['togri']}/{n['jami']} {'✅' if n['otdi'] else '❌'}{' ⚠️' if n['diqqat'] else ''}" for n in h["nazoratlar"]))
    kuchli = sorted([k for k in h["konikmalar"] if k["jami"] >= 5], key=lambda k: k["foiz"])
    if kuchli:
        q.append(f"💪 Kuchli: {kuchli[-1]['nom']} {kuchli[-1]['foiz']}% · 🎯 Mashq kerak: {kuchli[0]['nom']} {kuchli[0]['foiz']}%")
    if h["qulflar"]:
        q.append(f"🕵️ Nazoratchi: o‘yinlar {len(h['qulflar'])} marta to‘xtatildi — eski darslarni takrorlash kerak")
    return "\n".join(q)


def create_router(platform):
    router = APIRouter(tags=["yakuniy"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            jadval(cur); r = fn(cur); conn.commit(); return r
        finally:
            cur.close(); conn.close()

    def guruh_egasi(cur, gid, u):
        cur.execute("SELECT * FROM kurs_guruh WHERE id=%s AND faol", (gid,))
        g = cur.fetchone()
        if not g:
            raise HTTPException(404, "Guruh topilmadi")
        if int(g["egasi"]) != u:
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (u,))
            if not cur.fetchone():
                raise HTTPException(403, "Bu guruh sizniki emas")
        return g

    @router.get("/api/yakuniy")
    def meniki(fan: str, grade: str = "", token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        from modules.kurslar import kurs_of
        def f(cur):
            kalit = kurs_of(fan, grade)[0]
            gid = [r["guruh_id"] for r in _sp(cur, """SELECT a.guruh_id FROM kurs_guruh_azo a JOIN kurs_guruh g ON g.id=a.guruh_id
                                                     WHERE a.user_id=%s AND g.fan=%s AND g.faol""", (u, fan))]
            return hisobla(cur, u, kalit, gid)
        return run(f)

    @router.get("/api/kurs_guruh/{gid}/yakuniy")
    def guruh(gid: int, token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        from modules.kurslar import kurs_of
        def f(cur):
            g = guruh_egasi(cur, gid, u)
            kalit = kurs_of(g["fan"], g["grade"])[0]
            cur.execute("""SELECT a.user_id, COALESCE(NULLIF(us.full_name,''),'O‘quvchi') AS ism FROM kurs_guruh_azo a JOIN users us ON us.user_id=a.user_id
                           WHERE a.guruh_id=%s ORDER BY 2""", (gid,))
            return {"oquvchilar": [{"user_id": r["user_id"], "ism": r["ism"], **hisobla(cur, r["user_id"], kalit, [gid])} for r in cur.fetchall()]}
        return run(f)

    class Baho(BaseModel):
        token: str = ""
        user_id: int
        turi: str = Field(..., pattern="^(kurs|imtihon)$")
        ball: int = Field(..., ge=0, le=100)
        izoh: str = Field(default="", max_length=300)

    @router.post("/api/kurs_guruh/{gid}/baho")
    def baho(gid: int, body: Baho, authorization: Optional[str] = Header(None)):
        """O'qituvchi bahosi: «kurs» (mashg'ulot, uy vazifasi) yoki «imtihon» (o'z imtihoni) — 0–100 foiz."""
        u = uid(body.token, authorization)
        def f(cur):
            guruh_egasi(cur, gid, u)
            cur.execute("SELECT 1 FROM kurs_guruh_azo WHERE guruh_id=%s AND user_id=%s", (gid, body.user_id))
            if not cur.fetchone():
                raise HTTPException(404, "O‘quvchi bu guruhda emas")
            cur.execute("INSERT INTO kurs_baho(guruh_id, user_id, turi, ball, izoh, qoydi) VALUES(%s,%s,%s,%s,%s,%s)",
                        (gid, body.user_id, body.turi, body.ball, body.izoh.strip(), u))
            return {"ok": True}
        return run(f)

    @router.get("/api/ota/haftalik")
    def ota_haftalik(bola_id: int, token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        from modules import bogcha_reja as reja
        def f(cur):
            if not (reja.ota_bolami(cur, u, bola_id) or reja.adminmi(cur, u)):
                raise HTTPException(403, "Bu farzand sizga ulanmagan")
            h = haftalik(cur, bola_id)
            cur.execute("SELECT COALESCE(NULLIF(full_name,''),'Farzand') AS ism FROM users WHERE user_id=%s", (bola_id,))
            r = cur.fetchone(); h["matn"] = hisobot_matni(r["ism"] if r else "Farzand", h)
            return h
        return run(f)

    def yakshanba_ishi():
        """Har yakshanba kechqurun (Toshkent 19:00 dan keyin) ota-onalarga haftalik hisobot — bildirishnoma (bitta nusxa bajaradi)."""
        time.sleep(180)
        while True:
            try:
                now = datetime.now(timezone.utc) + timedelta(hours=5)
                if now.weekday() == 6 and now.hour >= 19:
                    conn = platform._db(); conn.autocommit = True; cur = conn.cursor()
                    try:
                        cur.execute("SELECT pg_try_advisory_lock(484484484) AS ok")
                        if cur.fetchone()["ok"]:
                            jadval(cur)
                            hafta = now.date()
                            for pc in _sp(cur, "SELECT DISTINCT parent_id, child_id FROM parent_child", ()):
                                cur.execute("INSERT INTO haftalik_hisobot(parent_id, child_id, hafta) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING RETURNING parent_id", (pc["parent_id"], pc["child_id"], hafta))
                                if not cur.fetchone():
                                    continue
                                h = haftalik(cur, pc["child_id"])
                                if not h["darslar"] and not h["nazoratlar"]:
                                    continue
                                cur.execute("SELECT COALESCE(NULLIF(full_name,''),'Farzand') AS ism FROM users WHERE user_id=%s", (pc["child_id"],))
                                r = cur.fetchone()
                                cur.execute("INSERT INTO bildirishnomalar(user_id, matn, turi) VALUES(%s,%s,'haftalik')", (pc["parent_id"], hisobot_matni(r["ism"] if r else "Farzand", h)))
                            cur.execute("SELECT pg_advisory_unlock(484484484)")
                    finally:
                        cur.close(); conn.close()
            except Exception as exc:   # noqa: BLE001
                print("[haftalik]", exc, flush=True)
            time.sleep(1800)

    @router.on_event("startup")
    def boshla():
        import sys as _s
        if "pytest" not in _s.modules:
            threading.Thread(target=yakshanba_ishi, name="haftalik-hisobot", daemon=True).start()

    return router

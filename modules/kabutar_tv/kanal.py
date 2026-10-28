"""REV185: KABUTAR TV — Kabutar ichidagi yoshga mos kanallar.

Har kuni tunda (Toshkent vaqti bilan 2:00–6:00) haftalik jadval bo'yicha (masalan dushanba —
ingliz va nemis tili) har daraja uchun ko'rsatuv tayyorlanadi va «📺 Kabutar TV — 3-sinf» kabi kanalga o'zi joylanadi.
Kanallar avtomatik: o'quvchi o'z sinfi/yoshidagi kanalga, ota-ona — farzandlari kanallariga qo'shiladi. Kanalga faqat
tizim yozadi, a'zolar ko'radi.

Muhit sozlamalari:
  KABUTAR_TV_YOQILGAN=1        — 0 bo'lsa, tungi tayyorlash ishlamaydi
  KABUTAR_TV_SOAT=2            — tayyorlash boshlanadigan soat (Toshkent); KABUTAR_TV_OXIRGI_SOAT=6 — shundan keyin yangi kun boshlanmaydi
  KABUTAR_TV_DIR=/data/kabutar_tv — videolar papkasi (Railway Volume ulang, aks holda qayta deployda o'chadi)
  KABUTAR_TV_SAQLASH_KUN=30    — videolar necha kun saqlanadi
  KABUTAR_TV_USER_ID=          — kanalga yozuvchi foydalanuvchi (bo'sh bo'lsa — birinchi admin)
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import threading
import time

from fastapi import APIRouter, Body, HTTPException, Query

from .ssenariy import DARAJALAR, TILLAR

TASHKENT = dt.timezone(dt.timedelta(hours=5))
STANDART_JADVAL = {0: ["en", "de"], 1: ["ru", "fr"], 2: ["en", "es"], 3: ["de", "ru"], 4: ["en", "fr"], 5: ["es", "en"], 6: []}
HAFTA = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
OYLAR = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


def papka():
    return os.environ.get("KABUTAR_TV_DIR") or os.path.join(os.getcwd(), "kabutar_tv_data")


def daraja_kodi(daraja):
    m = re.match(r"(\d+)-sinf", daraja)
    return int(m.group(1)) if m else 100 + int(daraja[0])


def kod_daraja(kod):
    kod = int(kod)
    return f"{kod}-sinf" if kod <= 11 else {102: "2-3 yosh", 104: "4-5 yosh", 106: "6-7 yosh"}.get(kod)


def sinfdan_daraja(sinf):
    s = str(sinf or "").strip().lower()
    if not s:
        return None
    if "yosh" in s or "bog" in s or "лет" in s:
        m = re.search(r"(\d)", s)
        if not m:
            return None
        n = int(m.group(1))
        return "2-3 yosh" if n <= 3 else "4-5 yosh" if n <= 5 else "6-7 yosh"
    m = re.search(r"(\d{1,2})", s)
    if m and 1 <= int(m.group(1)) <= 11:
        return f"{int(m.group(1))}-sinf"
    return None


def jadvallar(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS kabutar_tv_korsatuvlar(
        sana DATE NOT NULL, til VARCHAR(4) NOT NULL, daraja VARCHAR(12) NOT NULL,
        holat TEXT NOT NULL DEFAULT 'kutmoqda', mavzu TEXT, fayl_yol TEXT, xabar_id INTEGER, soniya INTEGER,
        xato TEXT, yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(sana, til, daraja))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kabutar_tv_kun(
        sana DATE PRIMARY KEY, boshlandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), tugadi TIMESTAMPTZ)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kabutar_tv_jadval(hafta_kuni INTEGER PRIMARY KEY, tillar TEXT NOT NULL)""")
    cur.execute("ALTER TABLE chat_xabarlari ADD COLUMN IF NOT EXISTS fayl_yol TEXT")


def jadval_ol(cur):
    jadvallar(cur)
    cur.execute("SELECT hafta_kuni, tillar FROM kabutar_tv_jadval")
    j = {k: list(v) for k, v in STANDART_JADVAL.items()}
    for r in cur.fetchall():
        j[int(r["hafta_kuni"])] = [t for t in json.loads(r["tillar"]) if t in TILLAR]
    return j


# ───────────── a'zolik ─────────────
def foydalanuvchi_darajalari(cur, user_id):
    cur.execute("SELECT role, class FROM users WHERE user_id=%s", (user_id,))
    r = cur.fetchone()
    if not r:
        return set()
    if str(r.get("role") or "").lower() in ("admin", "superadmin", "super_admin"):
        return set(DARAJALAR)
    out = set()
    d = sinfdan_daraja(r.get("class"))
    if d:
        out.add(d)
    try:
        cur.execute("SAVEPOINT kabutar_tv_fp")
        cur.execute("""SELECT u.class FROM kabutar_family_profiles f JOIN users u ON u.user_id=f.profile_user_id
                       WHERE f.owner_user_id=%s AND f.removed_at IS NULL""", (user_id,))
        for x in cur.fetchall():
            d = sinfdan_daraja(x.get("class"))
            if d:
                out.add(d)
        cur.execute("RELEASE SAVEPOINT kabutar_tv_fp")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT kabutar_tv_fp")
    return out


def guruh(cur, daraja, topish_yarat):
    return topish_yarat(cur, "kanal", "kabutar_tv", daraja_kodi(daraja), f"📺 Kabutar TV — {daraja}")


def azolikni_sinxronla(cur, user_id, topish_yarat, azo_qosh):
    """Foydalanuvchini o'z sinfi/yoshi (va farzandlari) kanallariga qo'shadi, boshqa TV kanallaridan chiqaradi."""
    darajalar = foydalanuvchi_darajalari(cur, user_id)
    kerak = set()
    for d in darajalar:
        gid = guruh(cur, d, topish_yarat)
        azo_qosh(cur, gid, user_id)
        kerak.add(gid)
    cur.execute("""DELETE FROM chat_azolari a USING chat_guruhlari g
                   WHERE a.guruh_id=g.id AND g.manba_turi='kabutar_tv' AND a.user_id=%s AND NOT (g.id = ANY(%s))""",
                (user_id, list(kerak) or [0]))


def yozuvchi(cur):
    env = os.environ.get("KABUTAR_TV_USER_ID")
    if env and env.isdigit():
        return int(env)
    cur.execute("SELECT user_id FROM users WHERE LOWER(role) IN ('admin','superadmin','super_admin') ORDER BY user_id LIMIT 1")
    r = cur.fetchone()
    if not r:
        raise RuntimeError("Kanalga yozish uchun admin topilmadi (KABUTAR_TV_USER_ID ni bering)")
    return int(r["user_id"])


def topish_yarat_oddiy(cur, turi, manba_turi, manba_id, nomi):
    cur.execute("SELECT id FROM chat_guruhlari WHERE turi=%s AND manba_turi=%s AND manba_id=%s", (turi, manba_turi, manba_id))
    r = cur.fetchone()
    if r:
        return r["id"]
    cur.execute("INSERT INTO chat_guruhlari(nomi,turi,manba_turi,manba_id) VALUES(%s,%s,%s,%s) RETURNING id", (nomi, turi, manba_turi, manba_id))
    return cur.fetchone()["id"]


def joyla(cur, sana, til, daraja, fayl, mavzu, soniya):
    gid = topish_yarat_oddiy(cur, "kanal", "kabutar_tv", daraja_kodi(daraja), f"📺 Kabutar TV — {daraja}")
    sarlavha = (f"📺 Kabutar TV · {TILLAR[til]} · {daraja}\n{HAFTA[sana.weekday()]}, {sana.day}-{OYLAR[sana.month - 1]}"
                f"{' — «' + mavzu + '»' if mavzu else ''}\n"
                f"Bugungi mavzu va o'tgan haftalar takrori · {max(1, round(soniya / 60))} daqiqa. Ekran oldida birga takrorlang! 🕊")
    hajm = os.path.getsize(fayl) // 1024
    cur.execute("""INSERT INTO chat_xabarlari(guruh_id, yuboruvchi_user_id, matn, fayl_turi, fayl_nomi, fayl_content_turi, fayl_hajmi_kb, fayl_yol)
                   VALUES(%s,%s,%s,'video',%s,'video/mp4',%s,%s) RETURNING id""",
                (gid, yozuvchi(cur), sarlavha, os.path.basename(fayl), hajm, fayl))
    return cur.fetchone()["id"]


# ───────────── fayl uzatish (videoni oldinga-orqaga surish uchun Range bilan) ─────────────
def fayl_javob(path, range_header=None, nom="video.mp4"):
    from fastapi.responses import Response, StreamingResponse
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video muddati tugagan yoki topilmadi")
    hajm = os.path.getsize(path)
    bosh, ox = 0, hajm - 1
    m = re.match(r"bytes=(\d*)-(\d*)", range_header or "")
    if m and (m.group(1) or m.group(2)):
        if m.group(1):
            bosh = int(m.group(1))
            ox = int(m.group(2)) if m.group(2) else hajm - 1
        else:
            bosh = max(0, hajm - int(m.group(2)))
        ox = min(ox, hajm - 1)
        if bosh > ox:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{hajm}"})

    def oqi():
        with open(path, "rb") as f:
            f.seek(bosh)
            qoldi = ox - bosh + 1
            while qoldi > 0:
                b = f.read(min(256 * 1024, qoldi))
                if not b:
                    break
                qoldi -= len(b)
                yield b
    sarlavha = {"Accept-Ranges": "bytes", "Content-Length": str(ox - bosh + 1), "Cache-Control": "private, max-age=86400",
                "Content-Disposition": f'inline; filename="{nom}"'}
    if m and (m.group(1) or m.group(2)):
        sarlavha["Content-Range"] = f"bytes {bosh}-{ox}/{hajm}"
        return StreamingResponse(oqi(), status_code=206, media_type="video/mp4", headers=sarlavha)
    return StreamingResponse(oqi(), media_type="video/mp4", headers=sarlavha)


# ───────────── tungi ish ─────────────
def ulanish():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    return psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)


def kun_ishi(sana, tillar=None, darajalar=None, majburiy=False, log=print):
    """Bir kunlik barcha ko'rsatuvlar: ssenariy → video → kanal. Tayyorlarini qayta qilmaydi."""
    from .rejissor import yasash
    from .ssenariy import ssenariy
    conn = ulanish()
    cur = conn.cursor()
    try:
        jadvallar(cur)
        conn.commit()
        tillar = tillar or jadval_ol(cur)[sana.weekday()]
        darajalar = darajalar or DARAJALAR
        kesh = os.path.join(papka(), "_ovoz_kesh")
        for til in tillar:
            for daraja in darajalar:
                cur.execute("SELECT holat FROM kabutar_tv_korsatuvlar WHERE sana=%s AND til=%s AND daraja=%s", (sana, til, daraja))
                r = cur.fetchone()
                if r and r["holat"] == "joylandi" and not majburiy:
                    continue
                cur.execute("""INSERT INTO kabutar_tv_korsatuvlar(sana,til,daraja,holat) VALUES(%s,%s,%s,'tayyorlanmoqda')
                               ON CONFLICT(sana,til,daraja) DO UPDATE SET holat='tayyorlanmoqda', xato=NULL, yangilangan=NOW()""",
                            (sana, til, daraja))
                conn.commit()
                try:
                    s = ssenariy(til, daraja, sana)
                    if not s:
                        raise RuntimeError("Bu daraja uchun manba yo'q")
                    fayl = os.path.join(papka(), sana.isoformat(), f"{til}_{daraja.replace(' ', '_')}.mp4")
                    t0 = time.time()
                    soniya = yasash(s, fayl, kesh=kesh)
                    xid = joyla(cur, sana, til, daraja, fayl, s["mavzu"], soniya)
                    cur.execute("""UPDATE kabutar_tv_korsatuvlar SET holat='joylandi', mavzu=%s, fayl_yol=%s, xabar_id=%s, soniya=%s,
                                   yangilangan=NOW() WHERE sana=%s AND til=%s AND daraja=%s""",
                                (s["mavzu"], fayl, xid, round(soniya), sana, til, daraja))
                    conn.commit()
                    log(f"[kabutar_tv] {sana} {til} {daraja}: {round(soniya)} s, {round(time.time() - t0)} s da tayyor")
                except Exception as exc:
                    conn.rollback()
                    cur.execute("UPDATE kabutar_tv_korsatuvlar SET holat='xato', xato=%s, yangilangan=NOW() WHERE sana=%s AND til=%s AND daraja=%s",
                                (str(exc)[:500], sana, til, daraja))
                    conn.commit()
                    log(f"[kabutar_tv] XATO {sana} {til} {daraja}: {exc}")
        cur.execute("UPDATE kabutar_tv_kun SET tugadi=NOW() WHERE sana=%s", (sana,))
        tozala(cur)
        conn.commit()
    finally:
        cur.close()
        conn.close()


def tozala(cur):
    """Muddati o'tgan videolar diskdan o'chadi, xabar «o'chirilgan» bo'ladi."""
    kun = int(os.environ.get("KABUTAR_TV_SAQLASH_KUN", "30"))
    chegara = dt.date.today() - dt.timedelta(days=kun)
    cur.execute("SELECT sana, fayl_yol, xabar_id FROM kabutar_tv_korsatuvlar WHERE sana < %s AND fayl_yol IS NOT NULL", (chegara,))
    for r in cur.fetchall():
        try:
            os.remove(r["fayl_yol"])
        except OSError:
            pass
        if r["xabar_id"]:
            cur.execute("UPDATE chat_xabarlari SET ochirilgan=TRUE WHERE id=%s", (r["xabar_id"],))
    cur.execute("UPDATE kabutar_tv_korsatuvlar SET fayl_yol=NULL, holat='arxiv' WHERE sana < %s AND fayl_yol IS NOT NULL", (chegara,))


def ishni_boshla(sana, tillar=None, darajalar=None, majburiy=False):
    """Alohida jarayon: veb-serverni sekinlashtirmaydi."""
    cmd = [sys.executable, "-m", "modules.kabutar_tv.ish", "--sana", sana.isoformat()]
    if tillar:
        cmd += ["--tillar", ",".join(tillar)]
    if darajalar:
        cmd += ["--darajalar", ",".join(darajalar)]
    if majburiy:
        cmd += ["--majburiy"]
    try:
        cmd = ["nice", "-n", "10"] + cmd
        return subprocess.Popen(cmd, cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    except FileNotFoundError:
        return subprocess.Popen(cmd[3:], cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def create_kabutar_tv_router(check_admin, db):
    router = APIRouter(prefix="/api/kabutar_tv", tags=["kabutar-tv"])
    holat = {"ishga": False}

    def kuzatuvchi():
        time.sleep(60)
        while True:
            try:
                if os.environ.get("KABUTAR_TV_YOQILGAN", "1") != "0":
                    hozir = dt.datetime.now(TASHKENT)
                    # REV186: faqat tunda (standart 2:00–6:00) — kunduzi admin yuklashlari bilan serverni band qilmasin
                    bosh = int(os.environ.get("KABUTAR_TV_SOAT", "2"))
                    if bosh <= hozir.hour < max(bosh + 1, int(os.environ.get("KABUTAR_TV_OXIRGI_SOAT", "6"))):
                        conn = db()
                        cur = conn.cursor()
                        try:
                            jadvallar(cur)
                            # bir kunda bir marta (bir nechta worker bo'lsa ham) — kim birinchi yozsa, o'sha boshlaydi;
                            # 6 soatda tugamagan bo'lsa (server qayta ishga tushgan) — qayta boshlanadi, tayyorlari qayta qilinmaydi
                            cur.execute("""INSERT INTO kabutar_tv_kun(sana) VALUES(%s) ON CONFLICT(sana) DO UPDATE SET boshlandi=NOW()
                                           WHERE kabutar_tv_kun.tugadi IS NULL AND kabutar_tv_kun.boshlandi < NOW() - INTERVAL '6 hours'
                                           RETURNING sana""", (hozir.date(),))
                            yutdi = cur.fetchone()
                            conn.commit()
                        finally:
                            cur.close()
                            conn.close()
                        if yutdi:
                            ishni_boshla(hozir.date())
            except Exception as exc:   # pragma: no cover
                print(f"[kabutar_tv kuzatuvchi] {exc}", flush=True)
            time.sleep(600)

    @router.on_event("startup")
    def boshla():
        if not holat["ishga"]:
            holat["ishga"] = True
            threading.Thread(target=kuzatuvchi, name="kabutar-tv", daemon=True).start()

    @router.get("/holat")
    def tv_holat(token: str, sana: str = None):
        check_admin(token)
        s = dt.date.fromisoformat(sana) if sana else dt.datetime.now(TASHKENT).date()
        conn = db()
        cur = conn.cursor()
        try:
            jadvallar(cur)
            conn.commit()
            cur.execute("SELECT til,daraja,holat,mavzu,soniya,xato,yangilangan FROM kabutar_tv_korsatuvlar WHERE sana=%s ORDER BY til,daraja", (s,))
            rows = cur.fetchall()
            return {"sana": s.isoformat(), "tillar": jadval_ol(cur)[s.weekday()], "korsatuvlar": rows}
        finally:
            cur.close()
            conn.close()

    @router.post("/ishga_tushir")
    def tv_ishga(token: str, sana: str = None, tillar: str = None, darajalar: str = None, majburiy: bool = False):
        check_admin(token)
        s = dt.date.fromisoformat(sana) if sana else dt.datetime.now(TASHKENT).date()
        t = [x for x in (tillar or "").split(",") if x in TILLAR] or None
        d = [x for x in (darajalar or "").split(",") if x in DARAJALAR] or None
        ishni_boshla(s, t, d, majburiy)
        return {"ok": True, "sana": s.isoformat(), "tillar": t, "darajalar": d}

    @router.get("/jadval")
    def tv_jadval(token: str):
        check_admin(token)
        conn = db()
        cur = conn.cursor()
        try:
            j = jadval_ol(cur)
            conn.commit()
            return {"jadval": [{"kun": HAFTA[k], "hafta_kuni": k, "tillar": j[k]} for k in range(7)], "mumkin": TILLAR}
        finally:
            cur.close()
            conn.close()

    @router.put("/jadval")
    def tv_jadval_yoz(token: str, body: dict = Body(...)):
        check_admin(token)
        conn = db()
        cur = conn.cursor()
        try:
            jadvallar(cur)
            for x in body.get("jadval", []):
                k = int(x.get("hafta_kuni", -1))
                if 0 <= k <= 6:
                    tl = [t for t in x.get("tillar", []) if t in TILLAR][:4]
                    cur.execute("""INSERT INTO kabutar_tv_jadval(hafta_kuni,tillar) VALUES(%s,%s)
                                   ON CONFLICT(hafta_kuni) DO UPDATE SET tillar=EXCLUDED.tillar""", (k, json.dumps(tl)))
            conn.commit()
            return {"jadval": jadval_ol(cur)}
        finally:
            cur.close()
            conn.close()

    return router

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

from fastapi import APIRouter, Body, Header, HTTPException, Query

from .ssenariy import AUDITORIYALAR, DARAJALAR, TILLAR, aud_darajalari

TASHKENT = dt.timezone(dt.timedelta(hours=5))
STANDART_JADVAL = {0: ["en", "de"], 1: ["ru", "fr"], 2: ["en", "es"], 3: ["de", "ru"], 4: ["en", "fr"], 5: ["es", "en"], 6: []}
HAFTA = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
OYLAR = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


def papka():
    return os.environ.get("KABUTAR_TV_DIR") or os.path.join(os.getcwd(), "kabutar_tv_data")


def volume_bormi():
    """Videolar papkasi alohida diskda (Railway Volume) turibdimi — aks holda deployda o'chadi."""
    p = os.path.abspath(papka())
    while p and p != "/":
        if os.path.ismount(p):
            return True
        p = os.path.dirname(p)
    return False


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


_JADVAL_TAYYOR = {"ok": False}


def jadvallar(cur):
    if _JADVAL_TAYYOR["ok"]:   # jarayonda bir marta (ALTER har safar jadvalni qisqa qulflamasin)
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS kabutar_tv_korsatuvlar(
        sana DATE NOT NULL, til VARCHAR(4) NOT NULL, daraja VARCHAR(12) NOT NULL,
        holat TEXT NOT NULL DEFAULT 'kutmoqda', mavzu TEXT, fayl_yol TEXT, xabar_id INTEGER, soniya INTEGER,
        xato TEXT, yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(sana, til, daraja))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kabutar_tv_kun(
        sana DATE PRIMARY KEY, boshlandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), tugadi TIMESTAMPTZ)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kabutar_tv_jadval(hafta_kuni INTEGER PRIMARY KEY, tillar TEXT NOT NULL)""")
    cur.execute("ALTER TABLE chat_xabarlari ADD COLUMN IF NOT EXISTS fayl_yol TEXT")
    cur.execute("CREATE TABLE IF NOT EXISTS kabutar_tv_sozlama(kalit TEXT PRIMARY KEY, qiymat TEXT NOT NULL)")
    cur.execute("ALTER TABLE kabutar_tv_korsatuvlar ADD COLUMN IF NOT EXISTS admin_xabar_id INTEGER")
    cur.execute("ALTER TABLE kabutar_tv_korsatuvlar ADD COLUMN IF NOT EXISTS xabarlar TEXT")      # REV188: bir nechta sinf kanali
    cur.execute("ALTER TABLE kabutar_tv_korsatuvlar ADD COLUMN IF NOT EXISTS tg_holat TEXT")      # REV188: Telegramga yuborildimi
    _JADVAL_TAYYOR["ok"] = True


ADMIN_KANAL = 999
STANDART_SOZLAMA = {"yoqilgan": True, "soat": 2, "oxirgi_soat": 6, "saqlash_kun": 30,
                    # REV188: tayyor video Telegram botdan adminga birma-bir yuboriladi (TG guruh va Instagram uchun)
                    "tg_yuborish": True, "tg_chat": "", "haftalik": True, "reyting_ism": True}
HAFTALIK = "hf"   # haftalik ko'rsatuv qatorining «til» belgisi


def sozlama_ol(cur):
    """REV187: admin paneldan o'zgartiriladigan sozlamalar (bazada); bo'lmasa — muhit o'zgaruvchilari / standart."""
    jadvallar(cur)
    s = dict(STANDART_SOZLAMA)
    env = {"yoqilgan": os.environ.get("KABUTAR_TV_YOQILGAN"), "soat": os.environ.get("KABUTAR_TV_SOAT"),
           "oxirgi_soat": os.environ.get("KABUTAR_TV_OXIRGI_SOAT"), "saqlash_kun": os.environ.get("KABUTAR_TV_SAQLASH_KUN")}
    for k, v in env.items():
        if v not in (None, ""):
            s[k] = v != "0" if k == "yoqilgan" else int(v)
    cur.execute("SELECT kalit, qiymat FROM kabutar_tv_sozlama")
    for r in cur.fetchall():
        try:
            s[r["kalit"]] = json.loads(r["qiymat"])
        except Exception:
            pass
    return s


def jadval_ol(cur):
    jadvallar(cur)
    cur.execute("SELECT hafta_kuni, tillar FROM kabutar_tv_jadval")
    j = {k: list(v) for k, v in STANDART_JADVAL.items()}
    for r in cur.fetchall():
        j[int(r["hafta_kuni"])] = [t for t in json.loads(r["tillar"]) if t in TILLAR]
    return j


# ───────────── a'zolik ─────────────
def adminmi(cur, user_id):
    cur.execute("SELECT role FROM users WHERE user_id=%s", (user_id,))
    r = cur.fetchone()
    return bool(r) and str(r.get("role") or "").lower() in ("admin", "superadmin", "super_admin")


def foydalanuvchi_darajalari(cur, user_id):
    cur.execute("SELECT role, class FROM users WHERE user_id=%s", (user_id,))
    r = cur.fetchone()
    if not r:
        return set()
    if str(r.get("role") or "").lower() in ("admin", "superadmin", "super_admin"):
        return set(DARAJALAR) | {"__admin__"}
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
    if daraja == "__admin__":   # REV187: adminning katta kanali — barcha ko'rsatuvlar bir joyda
        return topish_yarat(cur, "kanal", "kabutar_tv", ADMIN_KANAL, "📺 Kabutar TV — barcha ko'rsatuvlar (admin)")
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


def sarlavha_yoz(sana, til, daraja, mavzu, soniya):
    if til == HAFTALIK:
        return (f"📅 Kabutar TV · Hafta yakuni · {daraja}\n{HAFTA[sana.weekday()]}, {sana.day}-{OYLAR[sana.month - 1]}\n"
                f"Bu hafta nimalarni o'rgandik, eng faollar reytingi va kelasi hafta mavzulari · {max(1, round(soniya / 60))} daqiqa 🏆")
    return (f"📺 Kabutar TV · {TILLAR[til]} · {daraja}\n{HAFTA[sana.weekday()]}, {sana.day}-{OYLAR[sana.month - 1]}"
            f"{' — «' + mavzu + '»' if mavzu else ''}\n"
            f"Kun taqvimi, ob-havo, kun iborasi, yangi so'zlar va o'yin · {max(1, round(soniya / 60))} daqiqa. Ekran oldida birga takrorlang! 🕊")


def joyla(cur, sana, til, daraja, fayl, mavzu, soniya, kanal=None):
    gid = kanal or topish_yarat_oddiy(cur, "kanal", "kabutar_tv", daraja_kodi(daraja), f"📺 Kabutar TV — {daraja}")
    sarlavha = sarlavha_yoz(sana, til, daraja, mavzu, soniya)
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


def tg_yubor(fayl, sarlavha, chat, log=print):
    """REV188: tayyor videoni Telegram bot orqali adminga yuborish (BOT_TOKEN — Railway'da bor). 50 MB gacha."""
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token or not chat:
        return "sozlanmagan"
    if os.path.getsize(fayl) > 49 * 1024 * 1024:
        return "katta (50 MB dan ortiq)"
    try:
        import requests
        with open(fayl, "rb") as f:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendVideo",
                              data={"chat_id": chat, "caption": sarlavha[:1000], "supports_streaming": "true"},
                              files={"video": (os.path.basename(fayl), f, "video/mp4")}, timeout=180)
        ok = r.ok and r.json().get("ok")
        return "yuborildi" if ok else f"xato: {r.text[:200]}"
    except Exception as exc:
        log(f"[kabutar_tv] TG: {exc}")
        return f"xato: {exc}"


def reyting(cur, auditoriya, ism_korsat=True, limit=5):
    """REV188: haftaning eng faollari — maktab tillari natijasi (maktab_til_natija) shu auditoriya sinflari bo'yicha.
    Ism — faqat ism va familiya bosh harfi (reklama ochiq bo'lgani uchun)."""
    try:
        cur.execute("SAVEPOINT tv_reyting")
        darajalar = aud_darajalari(auditoriya)
        sinflar = [int(d.split("-")[0]) for d in darajalar if d.endswith("-sinf")]
        if sinflar:
            cur.execute("""SELECT u.full_name, u.class, SUM(n.bal) AS ball FROM maktab_til_natija n JOIN users u ON u.user_id=n.user_id
                           WHERE n.sinf = ANY(%s) AND n.yangilangan_at > NOW() - INTERVAL '7 days'
                           GROUP BY u.user_id, u.full_name, u.class ORDER BY ball DESC LIMIT %s""", (sinflar, limit))
        else:
            cur.execute("""SELECT u.full_name, u.class, SUM(n.bal) AS ball FROM maktab_til_natija n JOIN users u ON u.user_id=n.user_id
                           WHERE u.class ILIKE %s AND n.yangilangan_at > NOW() - INTERVAL '7 days'
                           GROUP BY u.user_id, u.full_name, u.class ORDER BY ball DESC LIMIT %s""", (auditoriya[:3] + "%", limit))
        rows = cur.fetchall()
        cur.execute("RELEASE SAVEPOINT tv_reyting")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT tv_reyting")
        return []
    out = []
    for i, r in enumerate(rows, 1):
        qism = str(r.get("full_name") or "").split()
        ism = (qism[0] + (f" {qism[1][0]}." if len(qism) > 1 else "")) if (ism_korsat and qism) else f"{i}-o'rin, {r.get('class') or auditoriya}"
        out.append({"ism": ism, "ball": int(r.get("ball") or 0)})
    return out


def _bitta(cur, conn, sana, til, daraja, yasash_fn, kesh, admin_kanal, soz, majburiy, log):
    """Bitta ko'rsatuv: ssenariy → video → Kabutar kanallari (+ admin kanali) → Telegram."""
    from .rejissor import yasash
    cur.execute("SELECT holat FROM kabutar_tv_korsatuvlar WHERE sana=%s AND til=%s AND daraja=%s", (sana, til, daraja))
    r = cur.fetchone()
    if r and r["holat"] == "joylandi" and not majburiy:
        return
    cur.execute("""INSERT INTO kabutar_tv_korsatuvlar(sana,til,daraja,holat) VALUES(%s,%s,%s,'tayyorlanmoqda')
                   ON CONFLICT(sana,til,daraja) DO UPDATE SET holat='tayyorlanmoqda', xato=NULL, yangilangan=NOW()""", (sana, til, daraja))
    conn.commit()
    try:
        s = yasash_fn()
        if not s:
            raise RuntimeError("Bu guruh uchun manba yo'q")
        fayl = os.path.join(papka(), sana.isoformat(), f"{til}_{daraja.replace(' ', '_')}.mp4")
        t0 = time.time()
        soniya = yasash(s, fayl, kesh=kesh)
        cur.execute("SELECT xabar_id, admin_xabar_id, xabarlar FROM kabutar_tv_korsatuvlar WHERE sana=%s AND til=%s AND daraja=%s", (sana, til, daraja))
        eski = cur.fetchone() or {}
        eskilar = [eski.get("xabar_id"), eski.get("admin_xabar_id")] + (json.loads(eski["xabarlar"]) if eski.get("xabarlar") else [])
        for x in {x for x in eskilar if x}:   # qayta tayyorlansa — eski xabarlar o'chadi
            cur.execute("UPDATE chat_xabarlari SET ochirilgan=TRUE WHERE id=%s", (x,))
        ids = [joyla(cur, sana, til, d, fayl, s["mavzu"], soniya) for d in aud_darajalari(daraja)]
        axid = joyla(cur, sana, til, daraja, fayl, s["mavzu"], soniya, kanal=admin_kanal)
        cur.execute("""UPDATE kabutar_tv_korsatuvlar SET holat='joylandi', mavzu=%s, fayl_yol=%s, xabar_id=%s, admin_xabar_id=%s, xabarlar=%s,
                       soniya=%s, yangilangan=NOW() WHERE sana=%s AND til=%s AND daraja=%s""",
                    (s["mavzu"], fayl, ids[0] if ids else None, axid, json.dumps(ids), round(soniya), sana, til, daraja))
        conn.commit()
        log(f"[kabutar_tv] {sana} {til} {daraja}: {round(soniya)} s, {round(time.time() - t0)} s da tayyor")
        if soz.get("tg_yuborish") and soz.get("tg_chat"):
            tg = tg_yubor(fayl, sarlavha_yoz(sana, til, daraja, s["mavzu"], soniya) + "\n#KabutarTalim #KabutarTV", str(soz["tg_chat"]), log)
            cur.execute("UPDATE kabutar_tv_korsatuvlar SET tg_holat=%s WHERE sana=%s AND til=%s AND daraja=%s", (tg, sana, til, daraja))
            conn.commit()
    except Exception as exc:
        conn.rollback()
        cur.execute("UPDATE kabutar_tv_korsatuvlar SET holat='xato', xato=%s, yangilangan=NOW() WHERE sana=%s AND til=%s AND daraja=%s",
                    (str(exc)[:500], sana, til, daraja))
        conn.commit()
        log(f"[kabutar_tv] XATO {sana} {til} {daraja}: {exc}")


def kun_ishi(sana, tillar=None, darajalar=None, majburiy=False, log=print):
    """Bir kunlik barcha ko'rsatuvlar (har til × 9 efir guruhi); yakshanba — har guruhga haftalik ko'rsatuv. Tayyorlarini qayta qilmaydi."""
    from .ssenariy import haftalik, ob_havo_ol, ssenariy
    conn = ulanish()
    cur = conn.cursor()
    try:
        jadvallar(cur)
        conn.commit()
        jad = jadval_ol(cur)
        soz = sozlama_ol(cur)
        conn.commit()
        haftalik_kuni = sana.weekday() == 6 and soz.get("haftalik", True)
        tillar = tillar if tillar is not None else jad[sana.weekday()]
        darajalar = darajalar or AUDITORIYALAR
        kesh = os.path.join(papka(), "_ovoz_kesh")
        ob = ob_havo_ol(sana)   # bir marta — barcha ko'rsatuvlar uchun (internet bo'lmasa — fasl bo'yicha)
        admin_kanal = topish_yarat_oddiy(cur, "kanal", "kabutar_tv", ADMIN_KANAL, "📺 Kabutar TV — barcha ko'rsatuvlar (admin)")
        conn.commit()
        for til in tillar:
            if til == HAFTALIK:
                continue
            for daraja in darajalar:
                _bitta(cur, conn, sana, til, daraja, lambda til=til, daraja=daraja: ssenariy(til, daraja, sana, ob, tartib_hisobla(jad, til, sana)),
                       kesh, admin_kanal, soz, majburiy, log)
        if (haftalik_kuni and tillar == jad[sana.weekday()]) or HAFTALIK in (tillar or []):
            for daraja in darajalar:
                rey = reyting(cur, daraja, soz.get("reyting_ism", True))
                _bitta(cur, conn, sana, HAFTALIK, daraja, lambda daraja=daraja, rey=rey: haftalik(daraja, sana, jad, rey),
                       kesh, admin_kanal, soz, majburiy, log)
        cur.execute("UPDATE kabutar_tv_kun SET tugadi=NOW() WHERE sana=%s", (sana,))
        tozala(cur)
        conn.commit()
    finally:
        cur.close()
        conn.close()


def tartib_hisobla(jad, til, sana):
    """O'quv yili boshidan shu kungacha bu til necha marta efirga chiqqan (rukn va faktlar navbati uchun)."""
    bosh = dt.date(sana.year if sana.month >= 9 else sana.year - 1, 9, 2)
    n, d = 0, bosh
    while d < sana:
        if til in jad.get(d.weekday(), []):
            n += 1
        d += dt.timedelta(days=1)
    return n


def tozala(cur):
    """Muddati o'tgan videolar diskdan o'chadi, xabar «o'chirilgan» bo'ladi."""
    kun = int(sozlama_ol(cur).get("saqlash_kun") or 30)
    chegara = dt.date.today() - dt.timedelta(days=kun)
    cur.execute("SELECT sana, fayl_yol, xabar_id FROM kabutar_tv_korsatuvlar WHERE sana < %s AND fayl_yol IS NOT NULL", (chegara,))
    for r in cur.fetchall():
        try:
            os.remove(r["fayl_yol"])
        except OSError:
            pass
        if r["xabar_id"]:
            cur.execute("UPDATE chat_xabarlari SET ochirilgan=TRUE WHERE id=%s", (r["xabar_id"],))
        cur.execute("SELECT admin_xabar_id FROM kabutar_tv_korsatuvlar WHERE sana=%s AND xabar_id IS NOT DISTINCT FROM %s", (r["sana"], r["xabar_id"]))
        a = cur.fetchone()
        if a and a.get("admin_xabar_id"):
            cur.execute("UPDATE chat_xabarlari SET ochirilgan=TRUE WHERE id=%s", (a["admin_xabar_id"],))
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
                conn0 = db()
                cur0 = conn0.cursor()
                try:
                    soz = sozlama_ol(cur0)
                    conn0.commit()
                finally:
                    cur0.close()
                    conn0.close()
                if soz.get("yoqilgan"):
                    hozir = dt.datetime.now(TASHKENT)
                    # REV186/187: faqat tunda (standart 2:00–6:00) — kunduzi admin yuklashlari bilan serverni band qilmasin
                    bosh = int(soz.get("soat", 2))
                    if bosh <= hozir.hour < max(bosh + 1, int(soz.get("oxirgi_soat", 6))):
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
            cur.execute("""SELECT til,daraja,holat,mavzu,soniya,xato,xabar_id,admin_xabar_id,tg_holat,yangilangan FROM kabutar_tv_korsatuvlar
                           WHERE sana=%s ORDER BY til,daraja""", (s,))
            rows = cur.fetchall()
            cur.execute("""SELECT COUNT(*) AS n FROM kabutar_tv_korsatuvlar WHERE holat='tayyorlanmoqda' AND yangilangan > NOW() - INTERVAL '20 minutes'""")
            band = cur.fetchone()["n"] > 0
            cur.execute("SELECT sana, COUNT(*) FILTER (WHERE holat='joylandi') AS joylandi, COUNT(*) FILTER (WHERE holat='xato') AS xato "
                        "FROM kabutar_tv_korsatuvlar WHERE sana >= %s GROUP BY sana ORDER BY sana DESC", (s - dt.timedelta(days=14),))
            tarix = cur.fetchall()
            return {"sana": s.isoformat(), "tillar": jadval_ol(cur)[s.weekday()], "korsatuvlar": rows, "band": band,
                    "darajalar": AUDITORIYALAR, "mumkin_tillar": {**TILLAR, HAFTALIK: "📅 Hafta yakuni"}, "sozlama": sozlama_ol(cur), "tarix": tarix,
                    "bot_bor": bool(os.environ.get("BOT_TOKEN", "").strip()),
                    "tv_papka": papka(), "volume": volume_bormi()}
        finally:
            cur.close()
            conn.close()

    @router.post("/ishga_tushir")
    def tv_ishga(token: str, sana: str = None, tillar: str = None, darajalar: str = None, majburiy: bool = False):
        check_admin(token)
        s = dt.date.fromisoformat(sana) if sana else dt.datetime.now(TASHKENT).date()
        t = [x for x in (tillar or "").split(",") if x in TILLAR or x == HAFTALIK] or None
        d = [x for x in (darajalar or "").split(",") if x in AUDITORIYALAR] or None
        conn = db()
        cur = conn.cursor()
        try:
            jadvallar(cur)
            cur.execute("""SELECT COUNT(*) AS n FROM kabutar_tv_korsatuvlar WHERE holat='tayyorlanmoqda' AND yangilangan > NOW() - INTERVAL '20 minutes'""")
            if cur.fetchone()["n"] > 0:
                raise HTTPException(status_code=409, detail="Hozir boshqa ko'rsatuv tayyorlanmoqda — tugashini kuting (sahifa o'zi yangilanadi)")
            if not t and not jadval_ol(cur)[s.weekday()] and s.weekday() != 6:
                raise HTTPException(status_code=400, detail="Bu kunga jadvalda til yo'q — tilni tanlang")
            # tanlanganlar darhol «kutmoqda» bo'lib ko'rinsin
            for til in (t or jadval_ol(cur)[s.weekday()] + ([HAFTALIK] if s.weekday() == 6 else [])):
                for daraja in (d or AUDITORIYALAR):
                    cur.execute("""INSERT INTO kabutar_tv_korsatuvlar(sana,til,daraja,holat) VALUES(%s,%s,%s,'kutmoqda')
                                   ON CONFLICT(sana,til,daraja) DO UPDATE SET holat=CASE WHEN kabutar_tv_korsatuvlar.holat='joylandi' AND NOT %s
                                   THEN 'joylandi' ELSE 'kutmoqda' END, yangilangan=NOW()""", (s, til, daraja, majburiy))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        ishni_boshla(s, t, d, majburiy)
        return {"ok": True, "sana": s.isoformat(), "tillar": t, "darajalar": d}

    @router.get("/video")
    def tv_video(token: str, til: str, daraja: str, sana: str, range_header: str = Header(None, alias="Range")):
        """Admin panelda videoni ko'rish (Kabutar'ga kirmasdan)."""
        check_admin(token)
        conn = db()
        cur = conn.cursor()
        try:
            jadvallar(cur)
            cur.execute("SELECT fayl_yol FROM kabutar_tv_korsatuvlar WHERE sana=%s AND til=%s AND daraja=%s", (dt.date.fromisoformat(sana), til, daraja))
            r = cur.fetchone()
            conn.commit()
        finally:
            cur.close()
            conn.close()
        return fayl_javob((r or {}).get("fayl_yol"), range_header, f"{til}_{daraja}.mp4")

    @router.get("/ssenariy")
    def tv_ssenariy(token: str, til: str, daraja: str, sana: str = None):
        """Ko'rsatuv ssenariysini video tayyorlamasdan ko'rish (qaysi mavzu, ruknlar, gaplar, kim aytadi)."""
        check_admin(token)
        from .ssenariy import ssenariy, fasl_ob_havo
        s = dt.date.fromisoformat(sana) if sana else dt.datetime.now(TASHKENT).date()
        if (til not in TILLAR and til != HAFTALIK) or daraja not in AUDITORIYALAR:
            raise HTTPException(status_code=400, detail="Til yoki guruh noto'g'ri")
        conn = db()
        cur = conn.cursor()
        try:
            jad = jadval_ol(cur)
            conn.commit()
        finally:
            cur.close()
            conn.close()
        if til == HAFTALIK:
            from .ssenariy import haftalik
            conn = db()
            cur = conn.cursor()
            try:
                rey = reyting(cur, daraja, True)
                conn.commit()
            finally:
                cur.close()
                conn.close()
            sc = haftalik(daraja, s, jad, rey)
        else:
            sc = ssenariy(til, daraja, s, fasl_ob_havo(s), tartib_hisobla(jad, til, s))
        if not sc:
            raise HTTPException(status_code=404, detail="Bu daraja uchun manba yo'q")
        return sc

    @router.get("/sozlama")
    def tv_sozlama(token: str):
        check_admin(token)
        conn = db()
        cur = conn.cursor()
        try:
            r = sozlama_ol(cur)
            conn.commit()
            return r
        finally:
            cur.close()
            conn.close()

    @router.put("/sozlama")
    def tv_sozlama_yoz(token: str, body: dict = Body(...)):
        check_admin(token)
        toza = {}
        if "yoqilgan" in body:
            toza["yoqilgan"] = bool(body["yoqilgan"])
        for k, lo, hi in (("soat", 0, 23), ("oxirgi_soat", 1, 24), ("saqlash_kun", 3, 365)):
            if k in body:
                toza[k] = max(lo, min(hi, int(body[k])))
        for k in ("tg_yuborish", "haftalik", "reyting_ism"):
            if k in body:
                toza[k] = bool(body[k])
        if "tg_chat" in body:
            toza["tg_chat"] = str(body["tg_chat"] or "").strip()[:64]
        conn = db()
        cur = conn.cursor()
        try:
            jadvallar(cur)
            for k, v in toza.items():
                cur.execute("""INSERT INTO kabutar_tv_sozlama(kalit,qiymat) VALUES(%s,%s)
                               ON CONFLICT(kalit) DO UPDATE SET qiymat=EXCLUDED.qiymat""", (k, json.dumps(v)))
            conn.commit()
            return sozlama_ol(cur)
        finally:
            cur.close()
            conn.close()

    @router.post("/tg_sinov")
    def tv_tg_sinov(token: str):
        """Telegram sozlamasini tekshirish: botdan adminga sinov xabari."""
        check_admin(token)
        conn = db()
        cur = conn.cursor()
        try:
            soz = sozlama_ol(cur)
            conn.commit()
        finally:
            cur.close()
            conn.close()
        bot = os.environ.get("BOT_TOKEN", "").strip()
        if not bot:
            raise HTTPException(status_code=400, detail="Serverda BOT_TOKEN yo'q")
        if not soz.get("tg_chat"):
            raise HTTPException(status_code=400, detail="Telegram chat ID kiritilmagan")
        import requests
        r = requests.post(f"https://api.telegram.org/bot{bot}/sendMessage",
                          data={"chat_id": soz["tg_chat"], "text": "📺 Kabutar TV: sinov xabari. Videolar shu yerga keladi."}, timeout=20)
        if not (r.ok and r.json().get("ok")):
            raise HTTPException(status_code=400, detail=f"Telegram: {r.text[:200]} — botga avval /start yozing va chat ID'ni tekshiring")
        return {"ok": True}

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

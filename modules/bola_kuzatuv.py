"""REV91: bog'cha bolasi — kunlik dars rejasi va ota-onaga jonli hisobot.

Kunlik reja (faqat bog'cha bolasi uchun, har FAN alohida — bir fan boshqasiga ta'sir qilmaydi):
  • ish kunlari har fandan 2 ta YANGI dars, dam olish kunlari (shanba, yakshanba) — 3 ta;
  • o'tilgan darsni qayta ko'rish, o'yin (test) va takror — cheklanmaydi;
  • kun Toshkent vaqti bilan (UTC+5) almashadi.

Ota-onaga (parent_child orqali ulangan bo'lsa) xabar boradi — sayt bildirishnomasi va Telegram:
  • 🟢 bola darsni boshladi;  ✅ darsni tugatdi (natija, yulduzlar);  🎉 bugungi darslar tugadi;
  • ⏸ 5 daqiqadan beri mashq qilmayapti — ilovadan chiqib ketgan (boshqa ilova, ekran o'chgan) yoki dars
    to'xtab turibdi. Brauzer bola qaysi ilovaga o'tganini bilolmaydi (telefon maxfiyligi) — faqat bizning
    ilovadan chiqqani va qancha vaqt yo'qligini biladi.
Bola ilovasi har 30 soniyada «signal» yuboradi (ko'rinib turibdimi, dars ketyaptimi). Kuzatuvchi har daqiqada
bir marta ishlaydi; bir nechta server nusxasida ham xabar bir marta ketadi (SKIP LOCKED).
"""
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

TASHKENT = timezone(timedelta(hours=5))
WEEKDAY_LIMIT = 2
WEEKEND_LIMIT = 3
IDLE_MINUTES = 5
MAX_IDLE_ALERTS = 2           # bitta dars uchun ko'pi bilan 2 marta «mashq qilmayapti»
SIGNAL_CAP_SECONDS = 45       # ikki signal orasidagi faol vaqt shundan oshmaydi
WATCH_EVERY_SECONDS = 60
WEEKDAYS_UZ = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]


# ── Sof mantiq (DB'siz sinaladi) ─────────────────────────────────
def tashkent_day(now_utc):
    return now_utc.astimezone(TASHKENT).date()


def daily_limit(day):
    return WEEKEND_LIMIT if day.weekday() >= 5 else WEEKDAY_LIMIT


def stars_for(togri, jami):
    """Dars natijasi: testsiz dars — 1 yulduz; 70%+ — 3; bittasi ham to'g'ri — 2; aks holda 1."""
    togri, jami = max(0, int(togri or 0)), max(0, int(jami or 0))
    if not jami:
        return 1
    if togri / jami >= 0.7:
        return 3
    return 2 if togri else 1


def active_seconds(prev_signal, now, was_visible, was_active):
    """Oxirgi signaldan beri faol vaqt: ko'rinib turgan va dars ketayotgan bo'lsa, ko'pi bilan SIGNAL_CAP."""
    if not prev_signal or not was_visible or not was_active:
        return 0
    return max(0, min(SIGNAL_CAP_SECONDS, int((now - prev_signal).total_seconds())))


def live_status(row, now):
    """Ota-ona uchun jonli holat: darsda | toxtagan | chiqib_ketgan | tugatgan | yoq."""
    if not row:
        return {"holat": "yoq"}
    if row.get("tugadi_at"):
        return {"holat": "tugatgan", "daqiqa": minutes_between(row["tugadi_at"], now)}
    last = row.get("oxirgi_signal_at") or row.get("boshlandi_at")
    gone = minutes_between(last, now)
    if not row.get("korinadi"):
        since = row.get("yashirildi_at") or last
        return {"holat": "chiqib_ketgan", "daqiqa": minutes_between(since, now)}
    if gone >= 2:
        return {"holat": "chiqib_ketgan", "daqiqa": gone}
    if row.get("bosh_since"):
        return {"holat": "toxtagan", "daqiqa": minutes_between(row["bosh_since"], now)}
    return {"holat": "darsda", "daqiqa": minutes_between(row.get("boshlandi_at"), now)}


def minutes_between(a, b):
    if not a or not b:
        return 0
    return max(0, int((b - a).total_seconds() // 60))


def idle_reason(row, now):
    """Ogohlantirish kerakmi? Qaytaradi: None | 'chiqib_ketgan' | 'toxtagan'.
    Bitta «yo'qlik» uchun bir marta; bola qaytib, yana yo'qolsa — yana (dars boshiga ko'pi bilan MAX_IDLE_ALERTS)."""
    if row.get("tugadi_at") or (row.get("ogohlantirish_soni") or 0) >= MAX_IDLE_ALERTS:
        return None
    limit = now - timedelta(minutes=IDLE_MINUTES)
    last = row.get("oxirgi_signal_at") or row.get("boshlandi_at")
    warned = row.get("ogohlantirildi_at")
    if not row.get("korinadi"):
        start = row.get("yashirildi_at") or last
        kind = "chiqib_ketgan"
    elif last and last <= limit:
        start, kind = last, "chiqib_ketgan"      # signal kelmay qoldi — ilova yopilgan / internet yo'q
    elif row.get("bosh_since"):
        start, kind = row["bosh_since"], "toxtagan"
    else:
        return None
    if not start or start > limit:
        return None
    if warned and start <= warned:
        return None                               # shu yo'qlik haqida allaqachon aytilgan
    return kind


def stars_text(n):
    n = max(0, min(3, int(n or 0)))
    return "⭐" * n + "☆" * (3 - n)


class StartLesson(BaseModel):
    token: Optional[str] = None
    dars_kod: str = Field(min_length=1, max_length=120)
    fan: str = Field(default="", max_length=120)
    mavzu: str = Field(default="", max_length=200)
    jami_qadam: int = Field(default=0, ge=0, le=500)


class FinishLesson(BaseModel):
    token: Optional[str] = None
    dars_kod: str = Field(min_length=1, max_length=120)
    togri: int = Field(default=0, ge=0, le=500)
    jami: int = Field(default=0, ge=0, le=500)


def migrate(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bola_dars_holat (
            child_id BIGINT NOT NULL,
            dars_kod TEXT NOT NULL,
            fan TEXT NOT NULL DEFAULT '',
            mavzu TEXT NOT NULL DEFAULT '',
            ochilgan_sana DATE NOT NULL,
            yulduz INT NOT NULL DEFAULT 0,
            tugatilgan_at TIMESTAMPTZ,
            PRIMARY KEY (child_id, dars_kod)
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS bola_dars_holat_kun ON bola_dars_holat(child_id, ochilgan_sana, fan)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bola_dars_faollik (
            id BIGSERIAL PRIMARY KEY,
            child_id BIGINT NOT NULL,
            dars_kod TEXT NOT NULL,
            fan TEXT NOT NULL DEFAULT '',
            mavzu TEXT NOT NULL DEFAULT '',
            sana DATE NOT NULL,
            boshlandi_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            oxirgi_signal_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            korinadi BOOLEAN NOT NULL DEFAULT TRUE,
            faol BOOLEAN NOT NULL DEFAULT TRUE,
            yashirildi_at TIMESTAMPTZ,
            bosh_since TIMESTAMPTZ,
            faol_soniya INT NOT NULL DEFAULT 0,
            chalgish_soni INT NOT NULL DEFAULT 0,
            qadam INT NOT NULL DEFAULT 0,
            jami_qadam INT NOT NULL DEFAULT 0,
            tugadi_at TIMESTAMPTZ,
            togri INT, jami INT, yulduz INT,
            ogohlantirish_soni INT NOT NULL DEFAULT 0,
            ogohlantirildi_at TIMESTAMPTZ,
            UNIQUE (child_id, dars_kod, sana)
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS bola_dars_faollik_kun ON bola_dars_faollik(child_id, sana)")
    cur.execute("""CREATE INDEX IF NOT EXISTS bola_dars_faollik_ochiq ON bola_dars_faollik(oxirgi_signal_at)
                   WHERE tugadi_at IS NULL""")
    # Sayt bildirishnomalari (to'lov modulidagi jadval bilan bir xil tuzilish).
    cur.execute("""CREATE TABLE IF NOT EXISTS bildirishnomalar(
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(user_id),
        matn TEXT NOT NULL,
        turi TEXT DEFAULT 'umumiy',
        oqildimi BOOLEAN DEFAULT FALSE,
        yaratildi TIMESTAMP DEFAULT NOW()
    )""")


def create_router(platform):
    router = APIRouter()
    ready = {"ok": False}
    lock = threading.Lock()

    def uid_of(token, authorization):
        return int(platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization)))

    def open_db():
        conn = platform._db()
        cur = conn.cursor()
        if not ready["ok"]:
            with lock:
                if not ready["ok"]:
                    migrate(cur)
                    conn.commit()
                    ready["ok"] = True
        return conn, cur

    def run_db(fn):
        conn, cur = open_db()
        try:
            return fn(conn, cur)
        finally:
            cur.close()
            conn.close()

    def child_card(cur, user_id):
        cur.execute("""SELECT full_name, role, to_jsonb(u)->'kabutar_learning_profile'->>'role' AS lrole
                       FROM users u WHERE user_id=%s""", (user_id,))
        row = cur.fetchone() or {}
        name = (str(row.get("full_name") or "Farzandingiz").strip() or "Farzandingiz")[:60]
        return name, row.get("role") == "oquvchi" and row.get("lrole") == "bogcha"

    def parents_of(cur, child_id):
        try:
            cur.execute("SAVEPOINT bola_ota")
            cur.execute("SELECT DISTINCT parent_id FROM parent_child WHERE child_id=%s", (child_id,))
            ids = [int(r["parent_id"]) for r in cur.fetchall()]
            cur.execute("RELEASE SAVEPOINT bola_ota")
            return ids
        except Exception:   # parent_child hali yaratilmagan muhit
            cur.execute("ROLLBACK TO SAVEPOINT bola_ota")
            return []

    def notify(cur, child_id, text, kind):
        """Ota-onalarga: sayt bildirishnomasi (shu tranzaksiyada) + Telegram (fon oqimida, javobni ushlamaydi)."""
        parents = parents_of(cur, child_id)
        for pid in parents:
            cur.execute("INSERT INTO bildirishnomalar(user_id, matn, turi) VALUES(%s,%s,%s)", (pid, text, kind))
        telegram = [pid for pid in parents if pid > 0]
        send = getattr(platform, "_telegram_orqali_yubor", None)
        if telegram and send:
            def push():
                for pid in telegram:
                    try:
                        send(pid, text)
                    except Exception as exc:   # pragma: no cover — tarmoq xatosi darsga ta'sir qilmaydi
                        print(f"[bola_kuzatuv telegram] {exc}", flush=True)
            threading.Thread(target=push, daemon=True).start()
        return len(parents)

    def plan(cur, child_id, now):
        day = tashkent_day(now)
        limit = daily_limit(day)
        cur.execute("""SELECT dars_kod, fan, ochilgan_sana, yulduz, tugatilgan_at FROM bola_dars_holat WHERE child_id=%s""", (child_id,))
        rows = cur.fetchall()
        fans = {}
        lessons = {}
        for r in rows:
            lessons[r["dars_kod"]] = {"yulduz": r["yulduz"], "tugadi": r["tugatilgan_at"] is not None,
                                      "bugun": r["ochilgan_sana"] == day}
            if r["ochilgan_sana"] == day:
                f = fans.setdefault(r["fan"], {"ochildi": 0, "tugadi": 0})
                f["ochildi"] += 1
                f["tugadi"] += r["tugatilgan_at"] is not None
        for f in fans.values():
            f["qoldi"] = max(0, limit - f["ochildi"])
        return {"sana": day.isoformat(), "kun": WEEKDAYS_UZ[day.weekday()], "dam_olish": day.weekday() >= 5,
                "limit": limit, "fanlar": fans, "darslar": lessons}

    # ── Bola ──
    @router.get("/api/bola/kun_rejasi")
    def day_plan(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        now = datetime.now(timezone.utc)

        def run(conn, cur):
            _, kid = child_card(cur, user_id)
            out = plan(cur, user_id, now)
            conn.commit()
            return {**out, "bogcha": kid}
        return run_db(run)

    @router.post("/api/bola/dars/boshla")
    def start_lesson(body: StartLesson, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        now = datetime.now(timezone.utc)
        day = tashkent_day(now)

        def run(conn, cur):
            name, kid = child_card(cur, user_id)
            if not kid:
                conn.commit()
                return {"ok": True, "kuzatilmaydi": True}
            cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"bola-reja:{user_id}",))
            cur.execute("SELECT ochilgan_sana FROM bola_dars_holat WHERE child_id=%s AND dars_kod=%s", (user_id, body.dars_kod))
            known = cur.fetchone()
            limit = daily_limit(day)
            if not known:
                cur.execute("SELECT COUNT(*) AS n FROM bola_dars_holat WHERE child_id=%s AND ochilgan_sana=%s AND fan=%s",
                            (user_id, day, body.fan))
                if cur.fetchone()["n"] >= limit:
                    conn.rollback()
                    raise HTTPException(409, {"kod": "limit", "limit": limit,
                                              "xabar": f"Bugungi {limit} ta yangi dars o'tildi. Yangi dars ertaga ochiladi — o'tilgan darslarni takrorlash va o'yinlar ochiq."})
                cur.execute("""INSERT INTO bola_dars_holat(child_id, dars_kod, fan, mavzu, ochilgan_sana) VALUES(%s,%s,%s,%s,%s)""",
                            (user_id, body.dars_kod, body.fan, body.mavzu, day))
            cur.execute("""INSERT INTO bola_dars_faollik(child_id, dars_kod, fan, mavzu, sana, jami_qadam)
                           VALUES(%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (child_id, dars_kod, sana) DO UPDATE SET oxirgi_signal_at=NOW(), korinadi=TRUE, faol=TRUE,
                             yashirildi_at=NULL, bosh_since=NULL, jami_qadam=GREATEST(bola_dars_faollik.jami_qadam, EXCLUDED.jami_qadam)
                           RETURNING (xmax = 0) AS yangi""",
                        (user_id, body.dars_kod, body.fan, body.mavzu, day, body.jami_qadam))
            first_today = cur.fetchone()["yangi"]
            # Boshqa darsga o'tdi — oldingi tugallanmagan darslar haqida «mashq qilmayapti» deyilmaydi.
            cur.execute("""UPDATE bola_dars_faollik SET ogohlantirish_soni=%s WHERE child_id=%s AND sana=%s AND dars_kod<>%s
                             AND tugadi_at IS NULL AND ogohlantirish_soni < %s""",
                        (MAX_IDLE_ALERTS, user_id, day, body.dars_kod, MAX_IDLE_ALERTS))
            if first_today:
                title = body.mavzu or "yangi"
                notify(cur, user_id, f"🟢 {name} «{title}» darsini boshladi" + (f" ({body.fan})" if body.fan else "") + ".", "bola_dars")
            out = plan(cur, user_id, now)
            conn.commit()
            return {"ok": True, "reja": out}
        return run_db(run)

    @router.post("/api/bola/dars/signal")
    async def lesson_signal(request: Request, authorization: str = Header(None)):
        """Har 30 soniyada va ilova yashirilganda/qaytganda. Brauzer chiqib ketayotganda ham yuborishi uchun
        text/plain JSON ham qabul qilinadi (keepalive, CORS oldindan so'rovisiz)."""
        try:
            data = json.loads((await request.body() or b"{}").decode("utf-8") or "{}")
        except Exception:
            raise HTTPException(400, "Noto'g'ri signal")
        token = data.get("token")
        kod = str(data.get("dars_kod") or "")[:120]
        visible = bool(data.get("korinadi", True))
        active = bool(data.get("faol", True))
        step = max(0, min(500, int(data.get("qadam") or 0)))
        if not kod:
            raise HTTPException(400, "dars_kod kerak")
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(_signal, token, authorization, kod, visible, active, step)

    def _signal(token, authorization, kod, visible, active, step):
        user_id = uid_of(token, authorization)
        now = datetime.now(timezone.utc)
        day = tashkent_day(now)

        def run(conn, cur):
            cur.execute("""SELECT id, oxirgi_signal_at, korinadi, faol, bosh_since, tugadi_at FROM bola_dars_faollik
                           WHERE child_id=%s AND dars_kod=%s AND sana=%s FOR UPDATE""", (user_id, kod, day))
            row = cur.fetchone()
            if not row or row["tugadi_at"]:
                conn.commit()
                return {"ok": True}
            add = active_seconds(row["oxirgi_signal_at"], now, row["korinadi"], row["faol"])
            went_away = row["korinadi"] and not visible
            cur.execute("""UPDATE bola_dars_faollik SET oxirgi_signal_at=%s, korinadi=%s, faol=%s,
                             faol_soniya=faol_soniya+%s, chalgish_soni=chalgish_soni+%s,
                             yashirildi_at=CASE WHEN %s THEN COALESCE(yashirildi_at, %s) ELSE NULL END,
                             bosh_since=CASE WHEN %s AND NOT %s THEN COALESCE(bosh_since, %s) ELSE NULL END,
                             qadam=GREATEST(qadam, %s)
                           WHERE id=%s""",
                        (now, visible, active, add, 1 if went_away else 0, not visible, now, visible, active, now, step, row["id"]))
            conn.commit()
            return {"ok": True}
        return run_db(run)

    @router.post("/api/bola/dars/tugat")
    def finish_lesson(body: FinishLesson, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        now = datetime.now(timezone.utc)
        day = tashkent_day(now)

        def run(conn, cur):
            name, kid = child_card(cur, user_id)
            if not kid:
                conn.commit()
                return {"ok": True, "kuzatilmaydi": True, "yulduz": stars_for(body.togri, body.jami)}
            stars = stars_for(body.togri, body.jami)
            cur.execute("""UPDATE bola_dars_holat SET yulduz=GREATEST(yulduz,%s), tugatilgan_at=COALESCE(tugatilgan_at, %s)
                           WHERE child_id=%s AND dars_kod=%s RETURNING fan, mavzu""", (stars, now, user_id, body.dars_kod))
            lesson = cur.fetchone()
            cur.execute("""UPDATE bola_dars_faollik SET tugadi_at=%s, togri=%s, jami=%s, yulduz=%s,
                             faol_soniya=faol_soniya + CASE WHEN korinadi AND faol THEN LEAST(%s, GREATEST(0, EXTRACT(EPOCH FROM (%s - oxirgi_signal_at))::int)) ELSE 0 END
                           WHERE child_id=%s AND dars_kod=%s AND sana=%s AND tugadi_at IS NULL
                           RETURNING faol_soniya, mavzu, fan""",
                        (now, body.togri, body.jami, stars, SIGNAL_CAP_SECONDS, now, user_id, body.dars_kod, day))
            done = cur.fetchone()
            out = plan(cur, user_id, now)
            fan = (lesson or done or {}).get("fan") or ""
            state = out["fanlar"].get(fan, {"ochildi": 0, "tugadi": 0, "qoldi": out["limit"]})
            all_done = state["tugadi"] >= out["limit"]
            if done:   # bugun birinchi marta tugatildi — ota-onaga natija
                title = done["mavzu"] or (lesson or {}).get("mavzu") or "dars"
                minutes = max(1, round((done["faol_soniya"] or 0) / 60))
                result = f"{body.togri}/{body.jami} to'g'ri, " if body.jami else ""
                text = f"✅ {name} «{title}» darsini tugatdi: {result}{stars_text(stars)}, {minutes} daqiqa."
                if all_done:
                    text += f"\n🎉 Bugungi {fan + ' ' if fan else ''}darslari tugadi ({state['tugadi']}/{out['limit']}). Yangi darslar ertaga ochiladi."
                notify(cur, user_id, text, "bola_dars")
            conn.commit()
            return {"ok": True, "yulduz": stars, "bugun_tugadi": all_done, "qoldi": state["qoldi"], "reja": out}
        return run_db(run)

    # ── Ota-ona ──
    @router.get("/api/ota/bola_faollik")
    def child_activity(bola_id: int, token: str = None, authorization: str = Header(None)):
        parent_id = uid_of(token, authorization)
        now = datetime.now(timezone.utc)
        day = tashkent_day(now)

        def run(conn, cur):
            cur.execute("SELECT 1 FROM parent_child WHERE parent_id=%s AND child_id=%s LIMIT 1", (parent_id, bola_id))
            if not cur.fetchone():
                raise HTTPException(403, "Bu farzand sizga ulanmagan")
            name, kid = child_card(cur, bola_id)
            cur.execute("""SELECT * FROM bola_dars_faollik WHERE child_id=%s AND sana=%s ORDER BY boshlandi_at""", (bola_id, day))
            today = [dict(r) for r in cur.fetchall()]
            live_row = next((r for r in reversed(today) if not r["tugadi_at"]), None) or (today[-1] if today else None)
            cur.execute("""SELECT sana, COUNT(*) AS darslar, COUNT(tugadi_at) AS tugatilgan, COALESCE(SUM(faol_soniya),0) AS soniya,
                                  COALESCE(SUM(chalgish_soni),0) AS chalgish
                           FROM bola_dars_faollik WHERE child_id=%s AND sana > %s GROUP BY sana ORDER BY sana DESC""",
                        (bola_id, day - timedelta(days=7)))
            week = [{"sana": r["sana"].isoformat(), "kun": WEEKDAYS_UZ[r["sana"].weekday()], "darslar": r["darslar"],
                     "tugatilgan": r["tugatilgan"], "daqiqa": round(r["soniya"] / 60), "chalgish": r["chalgish"]} for r in cur.fetchall()]
            out_plan = plan(cur, bola_id, now)
            conn.commit()
            status = live_status(live_row, now)
            if live_row:
                status.update(mavzu=live_row["mavzu"], fan=live_row["fan"], qadam=live_row["qadam"], jami_qadam=live_row["jami_qadam"])
            return {
                "bola": {"user_id": bola_id, "ism": name, "bogcha": kid},
                "jonli": status,
                "bugun": [{"mavzu": r["mavzu"], "fan": r["fan"], "boshlandi": r["boshlandi_at"].astimezone(TASHKENT).strftime("%H:%M"),
                           "tugadi": r["tugadi_at"].astimezone(TASHKENT).strftime("%H:%M") if r["tugadi_at"] else None,
                           "daqiqa": round((r["faol_soniya"] or 0) / 60), "togri": r["togri"], "jami": r["jami"], "yulduz": r["yulduz"],
                           "chalgish": r["chalgish_soni"], "qadam": r["qadam"], "jami_qadam": r["jami_qadam"]} for r in today],
                "hafta": week,
                "reja": {k: out_plan[k] for k in ("sana", "kun", "dam_olish", "limit", "fanlar")},
            }
        return run_db(run)

    # ── Kuzatuvchi: 5 daqiqa mashq qilmasa — ota-onaga bir marta ──
    def check_idle(now=None):
        now = now or datetime.now(timezone.utc)
        sent = 0

        def run(conn, cur):
            nonlocal sent
            cur.execute("SELECT pg_try_advisory_xact_lock(%s) AS ok", (91009100,))
            if not cur.fetchone()["ok"]:
                conn.rollback()
                return 0
            limit = now - timedelta(minutes=IDLE_MINUTES)
            cur.execute("""SELECT * FROM bola_dars_faollik
                           WHERE tugadi_at IS NULL AND ogohlantirish_soni < %s AND oxirgi_signal_at > %s
                             AND (oxirgi_signal_at <= %s OR (NOT korinadi AND yashirildi_at <= %s) OR bosh_since <= %s)
                           ORDER BY id LIMIT 300 FOR UPDATE SKIP LOCKED""",
                        (MAX_IDLE_ALERTS, now - timedelta(hours=3), limit, limit, limit))
            for row in [dict(r) for r in cur.fetchall()]:
                reason = idle_reason(row, now)
                if not reason:
                    continue
                name, _ = child_card(cur, row["child_id"])
                title = row["mavzu"] or "dars"
                step = f" ({row['qadam']}/{row['jami_qadam']}-qadamda)" if row["jami_qadam"] else ""
                if reason == "chiqib_ketgan":
                    text = (f"⏸ {name} {IDLE_MINUTES} daqiqadan beri mashq qilmayapti — «{title}» darsi yarim qoldi{step}. "
                            "Ilovadan chiqib ketgan: boshqa ilovaga o'tgan yoki telefon ekrani o'chgan bo'lishi mumkin.")
                else:
                    text = (f"⏸ {name} {IDLE_MINUTES} daqiqadan beri mashq qilmayapti — «{title}» darsi to'xtab turibdi{step}. "
                            "Yonida bo'lib, davom ettirishga yordam bering.")
                cur.execute("UPDATE bola_dars_faollik SET ogohlantirish_soni=ogohlantirish_soni+1, ogohlantirildi_at=%s WHERE id=%s",
                            (now, row["id"]))
                notify(cur, row["child_id"], text, "bola_dars")
                sent += 1
            conn.commit()
            return sent
        return run_db(run)

    def watcher():
        time.sleep(15)
        while True:
            try:
                check_idle()
            except Exception as exc:   # pragma: no cover — kuzatuvchi hech qachon to'xtamaydi
                print(f"[bola_kuzatuv watcher] {exc}", flush=True)
            time.sleep(WATCH_EVERY_SECONDS)

    started = {"ok": False}

    @router.on_event("startup")
    def start_watcher():
        if not started["ok"]:
            started["ok"] = True
            threading.Thread(target=watcher, name="bola-kuzatuv", daemon=True).start()

    router.check_idle = check_idle   # sinov uchun
    return router

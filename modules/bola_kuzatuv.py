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

REV103 — kunlik vaqt (faqat bog'cha bolasi):
  • 2-3 va 4-5 yosh: 1 soat dars + 1 soat erkin (o'yin) = 2 soat; 6-7 yosh: 2 soat dars + 1 soat erkin = 3 soat;
  • dars vaqti tugasa — darslar yopiladi (o'yin ochiq), o'yin vaqti tugasa — o'yinlar yopiladi, ikkalasi tugasa —
    «Bugun vaqting tugadi, ertaga uchrashamiz»; o'yinlar har kuni ochiq, faqat bolaning vaqtiga qarab;
  • butun platformada 5 daqiqa yo'q bo'lsa (boshqa ilova, ekran o'chgan) — ota-onaga «Bilasizmi?» xabari;
  • ota-ona: bugun nima qildi, qancha (dars / o'yin nomlari bilan) va o'rganish ko'rsatkichlari + reyting.
"""
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

try:
    from .curriculum_scope import preschool_learner
except ImportError:   # pragma: no cover — modules/ bevosita yo'lda
    from modules.curriculum_scope import preschool_learner

TASHKENT = timezone(timedelta(hours=5))
WEEKDAY_LIMIT = 2
WEEKEND_LIMIT = 3
IDLE_MINUTES = 5
MAX_IDLE_ALERTS = 2           # bitta dars uchun ko'pi bilan 2 marta «mashq qilmayapti»
SIGNAL_CAP_SECONDS = 45       # ikki signal orasidagi faol vaqt shundan oshmaydi
INFO_CACHE_SECONDS = 300      # REV103: bola ismi/guruhi keshi (vaqt signali tez-tez keladi)
WATCH_EVERY_SECONDS = 60
WEEKDAYS_UZ = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]


# ── Sof mantiq (DB'siz sinaladi) ─────────────────────────────────
def tashkent_day(now_utc):
    return now_utc.astimezone(TASHKENT).date()


def daily_limit(day):
    return WEEKEND_LIMIT if day.weekday() >= 5 else WEEKDAY_LIMIT


def stars_for(togri, jami):
    """Dars natijasi (test + «Top-chi» o'yini): testsiz dars — 1 yulduz; 80%+ — 3; 50%+ — 2; bittasi to'g'ri — 1;
    REV121: hech biri to'g'ri bo'lmasa — 0 (bosmasa yoki xato bossa yulduz berilmaydi)."""
    togri, jami = max(0, int(togri or 0)), max(0, int(jami or 0))
    if not jami:
        return 1
    if not togri:
        return 0
    r = min(1.0, togri / jami)
    return 3 if r >= 0.8 else 2 if r >= 0.5 else 1


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


# ── REV103: kunlik vaqt (sof mantiq) ─────────────────────────────
TIME_LIMITS = {"2-3 yosh": (60, 60), "4-5 yosh": (60, 60), "6-7 yosh": (120, 60)}   # (dars, erkin) daqiqa
DEFAULT_TIME_LIMIT = (60, 60)
WARN_LEFT_MINUTES = 5
SESSION_IDLE_ALERTS_PER_DAY = 3
GAME_NAMES = {"oyinlar": "O'yinlar", "shaxmat": "Shaxmat", "shashka": "Shashka", "bellashuv": "Bellashuv", "mavzular": "Darslar",
              "ai_ustoz": "Dars", "test": "Test"}


def time_category(turi):
    """dars (dars, test, mavzular) yoki oyin (erkin vaqt: o'yinlar va qolgan hamma ekran)."""
    return "dars" if str(turi or "") == "dars" else "oyin"


def time_status(used, group=""):
    """used — {"dars": soniya, "oyin": soniya}. Qaytaradi: daqiqalar, limitlar, qolgan vaqt va nimasi tugagani."""
    dars_limit, oyin_limit = TIME_LIMITS.get(group, DEFAULT_TIME_LIMIT)
    dars = int(used.get("dars") or 0) // 60
    oyin = int(used.get("oyin") or 0) // 60
    total_limit = dars_limit + oyin_limit
    out = {
        "guruh": group or "",
        "dars": {"daqiqa": dars, "limit": dars_limit, "qoldi": max(0, dars_limit - dars)},
        "oyin": {"daqiqa": oyin, "limit": oyin_limit, "qoldi": max(0, oyin_limit - oyin)},
        "jami": {"daqiqa": dars + oyin, "limit": total_limit, "qoldi": max(0, total_limit - dars - oyin)},
    }
    out["tugadi"] = {"dars": dars >= dars_limit, "oyin": oyin >= oyin_limit}
    out["tugadi"]["jami"] = out["tugadi"]["dars"] and out["tugadi"]["oyin"]
    return out


def hours_text(minutes):
    h, m = divmod(int(minutes or 0), 60)
    return f"{h} soat" + (f" {m} daqiqa" if m else "") if h else f"{m} daqiqa"


def time_message(status, turi):
    """Bolaga (robot ovozida) aytiladigan gap: nimasi tugagan bo'lsa yoki 5 daqiqa qolgan bo'lsa."""
    cat = time_category(turi)
    done = status["tugadi"]
    if done["jami"]:
        return {"kod": "jami", "matn": f"Bugun vaqting tugadi! Bugun {hours_text(status['jami']['limit'])} o'qib-o'ynading. "
                                        "Ko'zlaring dam olsin. Ertaga uchrashamiz!"}
    if done[cat]:
        if cat == "dars":
            return {"kod": "dars", "matn": "Bugungi dars vaqti tugadi. Barakalla! Endi biroz o'ynasang bo'ladi."}
        return {"kod": "oyin", "matn": "O'yin vaqti tugadi. Endi dars qilamiz!"}
    left = status[cat]["qoldi"]
    if 0 < left <= WARN_LEFT_MINUTES:
        return {"kod": "oz_qoldi", "matn": f"{'Dars' if cat == 'dars' else 'O`yin'} vaqtidan {left} daqiqa qoldi.".replace("`", "'")}
    return None


def _level(score):
    """0..1 → 1..5 yulduzli daraja."""
    return max(1, min(5, int(round(1 + 4 * max(0.0, min(1.0, score))))))


def _percentile(value, values, higher_is_better=True):
    """Tengdoshlarning (bolaning o'zidan tashqari) qanchasidan yaxshiroq: 0..1. Taqqoslash uchun kamida 3 bola kerak."""
    vals = [v for v in values if v is not None]
    if value is None or len(vals) < 3:
        return None
    better = sum(1 for v in vals if (v < value if higher_is_better else v > value))
    return better / len(vals)


def _peer_text(pct, better_word, worse_word):
    """«— tengdoshlarining 85 foizidan tezroq» (taqqoslash uchun yetarli bola bo'lmasa — bo'sh)."""
    if pct is None:
        return ""
    if pct >= 0.995:
        return f" — shu yoshdagi tengdoshlarining hammasidan {better_word}"
    if pct <= 0.005:
        return f" — hozircha tengdoshlaridan {worse_word}"
    return f" — tengdoshlarining {round(pct * 100)} foizidan {better_word}"


def insights(child_id, lessons, answers, reaction_ms, days_active, peers):
    """Ota-ona uchun o'rganish ko'rsatkichlari (tibbiy/psixologik tashxis EMAS — faqat platformadagi natijalar).

    lessons — [{faol_soniya, chalgish_soni, togri, jami, yulduz, tugadi, javob_ms}] (oxirgi 14 kun),
    answers — [bool] test javoblari, reaction_ms — reaksiya o'yini o'rtachasi yoki None, days_active — oxirgi 7 kundagi faol
    kunlar, peers — {child_id: {"yulduz": n, "javob_ms": ms|None, "aniqlik": 0..1|None}} (shu yosh guruhi, 7 kun)."""
    done = [l for l in lessons if l.get("tugadi")]
    right = sum(int(l.get("togri") or 0) for l in done) + sum(1 for a in answers if a)
    total = sum(int(l.get("jami") or 0) for l in done) + len(answers)
    accuracy = right / total if total else None
    times = [int(l["javob_ms"]) for l in done if l.get("javob_ms")]
    answer_ms = round(sum(times) / len(times)) if times else None
    focus_min = round(sum(int(l.get("faol_soniya") or 0) for l in done) / 60 / len(done), 1) if done else None
    distract = round(sum(int(l.get("chalgish_soni") or 0) for l in lessons) / len(lessons), 1) if lessons else None
    stars = round(sum(int(l.get("yulduz") or 0) for l in done) / len(done), 1) if done else None
    finish_rate = len(done) / len(lessons) if lessons else None
    peer_ms = [p.get("javob_ms") for k, p in peers.items() if k != child_id]
    peer_acc = [p.get("aniqlik") for k, p in peers.items() if k != child_id]
    # tengdoshlar bilan bir xil davr (7 kun) va bir xil o'lchov bo'yicha taqqoslanadi
    own = peers.get(child_id) or {}
    own_ms = own.get("javob_ms") or answer_ms
    own_acc = own.get("aniqlik") if own.get("aniqlik") is not None else accuracy
    items = []

    speed_pct = _percentile(own_ms, peer_ms, higher_is_better=False)
    if answer_ms:
        text = f"Savolga o'rtacha {answer_ms / 1000:.1f} soniyada javob beradi"
        text += _peer_text(speed_pct, "tezroq", "sekinroq")
        if reaction_ms:
            text += f". Reaksiya o'yinida o'rtacha {int(reaction_ms)} ms"
        items.append({"kalit": "tezlik", "nom": "Tezlik", "emoji": "⚡", "daraja": _level(speed_pct if speed_pct is not None else 0.6),
                      "matn": text + "."})
    elif reaction_ms:
        items.append({"kalit": "tezlik", "nom": "Tezlik", "emoji": "⚡", "daraja": _level(max(0.0, min(1.0, (900 - reaction_ms) / 600))),
                      "matn": f"Reaksiya o'yinida o'rtacha {int(reaction_ms)} ms."})
    if accuracy is not None:
        pct = _percentile(own_acc, peer_acc)
        text = f"Savollarning {round(accuracy * 100)} foiziga to'g'ri javob berdi (o'tgan darslardan takror savollar ham shu ichida)"
        text += _peer_text(pct, "yaxshiroq", "pastroq")
        items.append({"kalit": "xotira", "nom": "Eslab qolish", "emoji": "🧠", "daraja": _level(accuracy), "matn": text + "."})
    if focus_min is not None:
        text = f"Bir darsda o'rtacha {focus_min:g} daqiqa diqqat bilan o'tiradi"
        if distract:
            text += f", darsdan o'rtacha {distract:g} marta chalg'iydi"
        items.append({"kalit": "diqqat", "nom": "Diqqat", "emoji": "🎯",
                      "daraja": _level(max(0.0, min(1.0, (finish_rate or 0) - 0.15 * (distract or 0) + 0.1))), "matn": text + "."})
    items.append({"kalit": "muntazam", "nom": "Muntazamlik", "emoji": "📅", "daraja": _level(days_active / 7),
                  "matn": f"Oxirgi 7 kunda {days_active} kun shug'ullandi."})
    if stars is not None:
        items.append({"kalit": "natija", "nom": "Natija", "emoji": "⭐", "daraja": _level((stars - 1) / 2),
                      "matn": f"Tugatgan darslarida o'rtacha {stars:g} yulduz oldi."})

    ranking = None
    if child_id in peers and len(peers) >= 2:
        mine = int(peers[child_id].get("yulduz") or 0)
        place = 1 + sum(1 for p in peers.values() if int(p.get("yulduz") or 0) > mine)   # teng yulduz — bir xil o'rin
        ranking = {"orin": place, "jami": len(peers), "yulduz": mine}
    best = sorted([i for i in items if i["daraja"] >= 4], key=lambda i: -i["daraja"])
    summary = ("Kuchli tomoni: " + ", ".join(i["nom"].lower() for i in best[:2]) + ".") if best else \
        ("Hali ma'lumot kam — bir necha kun dars qilgach ko'rsatkichlar aniqlashadi." if not done else "Muntazam dars qilsa, ko'rsatkichlar tez o'sadi.")
    return {"korsatkichlar": items, "reyting": ranking, "xulosa": summary,
            "izoh": "Bu tibbiy yoki psixologik tashxis emas — faqat platformadagi dars va o'yin natijalari."}


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
    ortacha_ms: int = Field(default=0, ge=0, le=120000)   # REV103: savolga o'rtacha javob vaqti (tezlik ko'rsatkichi)
    ovoz_togri: int = Field(default=0, ge=0, le=50)       # REV105: dars oxiridagi ovozli tekshiruv — to'g'ri aytilgan iboralar
    ovoz_jami: int = Field(default=0, ge=0, le=50)


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
    cur.execute("ALTER TABLE bola_dars_faollik ADD COLUMN IF NOT EXISTS javob_ms INT")
    cur.execute("ALTER TABLE bola_dars_faollik ADD COLUMN IF NOT EXISTS ovoz_togri INT")   # REV105
    cur.execute("ALTER TABLE bola_dars_faollik ADD COLUMN IF NOT EXISTS ovoz_jami INT")
    # REV103: kunlik vaqt — nima qildi va qancha (dars / o'yin nomi bilan) hamda butun platformadagi seans
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bola_vaqt (
            child_id BIGINT NOT NULL,
            sana DATE NOT NULL,
            turi TEXT NOT NULL,
            nom TEXT NOT NULL DEFAULT '',
            soniya INT NOT NULL DEFAULT 0,
            oxirgi_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (child_id, sana, turi, nom)
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bola_sessiya (
            child_id BIGINT PRIMARY KEY,
            sana DATE NOT NULL,
            oxirgi_signal_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            korinadi BOOLEAN NOT NULL DEFAULT TRUE,
            yashirildi_at TIMESTAMPTZ,
            turi TEXT NOT NULL DEFAULT 'oyin',
            nom TEXT NOT NULL DEFAULT '',
            ogohlantirildi_at TIMESTAMPTZ,
            ogohlantirish_soni INT NOT NULL DEFAULT 0,
            tugadi_xabar_sana DATE
        )""")
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

    # REV103: bola ma'lumoti (ism, bog'cha bolasimi, yosh guruhi) — vaqt signali har 30 soniyada keladi, shuning uchun
    # qisqa keshda saqlanadi va users qatori to'liq JSON qilinmaydi (unda profil rasmi bor).
    info_cache = {}

    def child_info(cur, user_id):
        now = time.monotonic()
        hit = info_cache.get(user_id)
        if hit and hit[0] > now:
            return hit[1]
        try:
            cur.execute("SAVEPOINT bola_info")
            cur.execute("SELECT full_name, role, class, kabutar_learning_profile AS lp FROM users WHERE user_id=%s", (user_id,))
            row = dict(cur.fetchone() or {})
            cur.execute("RELEASE SAVEPOINT bola_info")
        except Exception:   # eski baza: ta'lim profili ustuni hali yo'q
            cur.execute("ROLLBACK TO SAVEPOINT bola_info")
            cur.execute("SELECT full_name, role, class FROM users WHERE user_id=%s", (user_id,))
            row = dict(cur.fetchone() or {})
        lp = row.get("lp") or {}
        if isinstance(lp, str):
            try:
                lp = json.loads(lp)
            except ValueError:
                lp = {}
        name = (str(row.get("full_name") or "Farzandingiz").strip() or "Farzandingiz")[:60]
        kid = row.get("role") == "oquvchi" and lp.get("role") == "bogcha"
        group = preschool_learner({"kabutar_learning_profile": lp, "class": row.get("class")}) or ""
        out = (name, kid, group)
        if len(info_cache) > 20000:
            info_cache.clear()
        info_cache[user_id] = (now + INFO_CACHE_SECONDS, out)
        return out

    def child_card(cur, user_id):
        name, kid, _ = child_info(cur, user_id)
        return name, kid

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

    # ── REV103: kunlik vaqt ──
    def child_group(cur, user_id):
        return child_info(cur, user_id)[2]

    def today_usage(cur, child_id, day):
        cur.execute("SELECT turi, COALESCE(SUM(soniya),0) AS s FROM bola_vaqt WHERE child_id=%s AND sana=%s GROUP BY turi",
                    (child_id, day))
        used = {"dars": 0, "oyin": 0}
        for r in cur.fetchall():
            used[time_category(r["turi"])] += int(r["s"] or 0)
        return used

    def time_state(cur, child_id, day):
        return time_status(today_usage(cur, child_id, day), child_group(cur, child_id))

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
            vaqt = time_state(cur, user_id, day)
            if vaqt["tugadi"]["dars"]:   # REV103: bugungi dars vaqti tugagan — dars ochilmaydi (o'yin vaqti bo'lsa, o'yin ochiq)
                conn.rollback()
                msg = time_message(vaqt, "dars")
                raise HTTPException(409, {"kod": "vaqt", "xabar": msg["matn"] if msg else "Bugungi dars vaqti tugadi."})
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
            cur.execute("""UPDATE bola_dars_faollik SET tugadi_at=%s, togri=%s, jami=%s, yulduz=%s, javob_ms=NULLIF(%s, 0),
                             ovoz_togri=%s, ovoz_jami=%s,
                             faol_soniya=faol_soniya + CASE WHEN korinadi AND faol THEN LEAST(%s, GREATEST(0, EXTRACT(EPOCH FROM (%s - oxirgi_signal_at))::int)) ELSE 0 END
                           WHERE child_id=%s AND dars_kod=%s AND sana=%s AND tugadi_at IS NULL
                           RETURNING faol_soniya, mavzu, fan""",
                        (now, body.togri, body.jami, stars, body.ortacha_ms, (min(body.ovoz_togri, body.ovoz_jami) if body.ovoz_jami else None), (body.ovoz_jami or None), SIGNAL_CAP_SECONDS, now, user_id, body.dars_kod, day))
            done = cur.fetchone()
            out = plan(cur, user_id, now)
            fan = (lesson or done or {}).get("fan") or ""
            state = out["fanlar"].get(fan, {"ochildi": 0, "tugadi": 0, "qoldi": out["limit"]})
            all_done = state["tugadi"] >= out["limit"]
            if done:   # bugun birinchi marta tugatildi — ota-onaga natija
                title = done["mavzu"] or (lesson or {}).get("mavzu") or "dars"
                minutes = max(1, round((done["faol_soniya"] or 0) / 60))
                result = f"{body.togri}/{body.jami} to'g'ri, " if body.jami else ""
                if body.ovoz_jami:
                    result += f"🎤 ovozli takror {min(body.ovoz_togri, body.ovoz_jami)}/{body.ovoz_jami}, "
                text = f"✅ {name} «{title}» darsini tugatdi: {result}{stars_text(stars)}, {minutes} daqiqa."
                if all_done:
                    text += f"\n🎉 Bugungi {fan + ' ' if fan else ''}darslari tugadi ({state['tugadi']}/{out['limit']}). Yangi darslar ertaga ochiladi."
                notify(cur, user_id, text, "bola_dars")
            conn.commit()
            return {"ok": True, "yulduz": stars, "bugun_tugadi": all_done, "qoldi": state["qoldi"], "reja": out}
        return run_db(run)

    @router.get("/api/bola/vaqt")
    def time_now(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        day = tashkent_day(datetime.now(timezone.utc))

        def run(conn, cur):
            _, kid = child_card(cur, user_id)
            if not kid:
                conn.commit()
                return {"kuzatilmaydi": True}
            out = time_state(cur, user_id, day)
            conn.commit()
            return {**out, "xabar": time_message(out, "oyin") if out["tugadi"]["jami"] else None}
        return run_db(run)

    @router.post("/api/bola/vaqt/signal")
    async def time_signal(request: Request, authorization: str = Header(None)):
        """REV103: har 30 soniyada, ilova yashirilganda va qaytganda. turi: dars | oyin; nom — dars mavzusi yoki o'yin nomi.
        Oldingi signaldan beri o'tgan faol vaqt (ko'pi bilan 45 s) oldingi ekran hisobiga yoziladi."""
        try:
            data = json.loads((await request.body() or b"{}").decode("utf-8") or "{}")
        except Exception:
            raise HTTPException(400, "Noto'g'ri signal")
        turi = "dars" if data.get("turi") == "dars" else "oyin"
        nom = str(data.get("nom") or "").strip()[:120]
        visible = bool(data.get("korinadi", True))
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(_time_signal, data.get("token"), authorization, turi, nom, visible)

    def _time_signal(token, authorization, turi, nom, visible):
        user_id = uid_of(token, authorization)
        now = datetime.now(timezone.utc)
        day = tashkent_day(now)

        def run(conn, cur):
            name, kid = child_card(cur, user_id)
            if not kid:
                conn.commit()
                return {"kuzatilmaydi": True}
            group = child_group(cur, user_id)
            cur.execute("SELECT * FROM bola_sessiya WHERE child_id=%s FOR UPDATE", (user_id,))
            prev = cur.fetchone()
            used = today_usage(cur, user_id, day)
            status = time_status(used, group)
            if prev and prev["sana"] == day:
                add = active_seconds(prev["oxirgi_signal_at"], now, prev["korinadi"], True)
                cat = time_category(prev["turi"])
                if add and not status["tugadi"][cat]:   # tugagan vaqt hisobiga yozilmaydi (bola u yerda bloklangan)
                    cur.execute("""INSERT INTO bola_vaqt(child_id, sana, turi, nom, soniya, oxirgi_at) VALUES(%s,%s,%s,%s,%s,%s)
                                   ON CONFLICT (child_id, sana, turi, nom) DO UPDATE SET soniya=bola_vaqt.soniya+EXCLUDED.soniya,
                                     oxirgi_at=EXCLUDED.oxirgi_at""",
                                (user_id, day, cat, prev["nom"] or GAME_NAMES.get(cat, ""), add, now))
                    used[cat] += add
                    status = time_status(used, group)
            new_day = not prev or prev["sana"] != day
            cur.execute("""INSERT INTO bola_sessiya(child_id, sana, oxirgi_signal_at, korinadi, yashirildi_at, turi, nom, ogohlantirish_soni)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,0)
                           ON CONFLICT (child_id) DO UPDATE SET sana=EXCLUDED.sana, oxirgi_signal_at=EXCLUDED.oxirgi_signal_at,
                             korinadi=EXCLUDED.korinadi, turi=EXCLUDED.turi, nom=EXCLUDED.nom,
                             yashirildi_at=CASE WHEN EXCLUDED.korinadi THEN NULL ELSE COALESCE(bola_sessiya.yashirildi_at, EXCLUDED.oxirgi_signal_at) END,
                             ogohlantirish_soni=CASE WHEN %s THEN 0 ELSE bola_sessiya.ogohlantirish_soni END""",
                        (user_id, day, now, visible, None if visible else now, turi, nom, new_day))
            if status["tugadi"]["jami"] and (not prev or prev.get("tugadi_xabar_sana") != day):
                cur.execute("UPDATE bola_sessiya SET tugadi_xabar_sana=%s WHERE child_id=%s", (day, user_id))
                notify(cur, user_id, f"🌙 {name} bugungi vaqtini to'liq ishlatdi: dars {status['dars']['daqiqa']} daqiqa, "
                                     f"o'yin {status['oyin']['daqiqa']} daqiqa. Platforma ertagacha yopildi.", "bola_vaqt")
            conn.commit()
            return {**status, "xabar": time_message(status, turi)}
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
            vaqt = time_state(cur, bola_id, day) if kid else None
            cur.execute("""SELECT turi, nom, soniya FROM bola_vaqt WHERE child_id=%s AND sana=%s ORDER BY soniya DESC LIMIT 20""",
                        (bola_id, day))
            nima = [{"turi": r["turi"], "nom": r["nom"], "daqiqa": max(1, round((r["soniya"] or 0) / 60))} for r in cur.fetchall() if r["soniya"]]
            cur.execute("""SELECT sana, turi, COALESCE(SUM(soniya),0) AS s FROM bola_vaqt WHERE child_id=%s AND sana > %s
                           GROUP BY sana, turi ORDER BY sana""", (bola_id, day - timedelta(days=7)))
            kunlar = {}
            for r in cur.fetchall():
                d = kunlar.setdefault(r["sana"].isoformat(), {"sana": r["sana"].isoformat(), "kun": WEEKDAYS_UZ[r["sana"].weekday()], "dars": 0, "oyin": 0})
                d[time_category(r["turi"])] += round(int(r["s"] or 0) / 60)
            cur.execute("SELECT * FROM bola_sessiya WHERE child_id=%s", (bola_id,))
            sess = cur.fetchone()
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
                # REV103: bugun qancha va nima (dars / o'yin) — hamda platformada hozir bormi
                "vaqt": {**(vaqt or {}), "nima": nima, "hafta": list(kunlar.values()),
                         "hozir": ({"nom": sess["nom"], "turi": sess["turi"],
                                    "platformada": bool(sess["korinadi"]) and minutes_between(sess["oxirgi_signal_at"], now) < 2,
                                    "daqiqa": minutes_between(sess["yashirildi_at"] or sess["oxirgi_signal_at"], now)}
                                   if sess and sess["sana"] == day else None)} if kid else None,
            }
        return run_db(run)

    @router.get("/api/ota/bola_tahlil")
    def child_insights(bola_id: int, token: str = None, authorization: str = Header(None)):
        """REV103: o'rganish ko'rsatkichlari (tezlik, eslab qolish, diqqat, muntazamlik, natija) va yosh guruhi reytingi."""
        parent_id = uid_of(token, authorization)
        now = datetime.now(timezone.utc)
        day = tashkent_day(now)

        def run(conn, cur):
            cur.execute("SELECT 1 FROM parent_child WHERE parent_id=%s AND child_id=%s LIMIT 1", (parent_id, bola_id))
            if not cur.fetchone():
                raise HTTPException(403, "Bu farzand sizga ulanmagan")
            group = child_group(cur, bola_id)
            cur.execute("""SELECT faol_soniya, chalgish_soni, togri, jami, yulduz, (tugadi_at IS NOT NULL) AS tugadi, javob_ms
                           FROM bola_dars_faollik WHERE child_id=%s AND sana > %s""", (bola_id, day - timedelta(days=14)))
            lessons = [dict(r) for r in cur.fetchall()]
            answers, reaction = [], None
            for sql, key in (("SELECT togri_mi FROM savol_javob_tarixi WHERE user_id=%s AND yaratilgan_at > NOW() - INTERVAL '14 days'", "a"),
                             ("SELECT AVG(millisekund) AS m FROM reaksiya_natijalari WHERE user_id=%s AND yaratilgan_at > NOW() - INTERVAL '14 days'", "r")):
                try:
                    cur.execute("SAVEPOINT bola_tahlil")
                    cur.execute(sql, (bola_id,))
                    if key == "a":
                        answers = [bool(r["togri_mi"]) for r in cur.fetchall()]
                    else:
                        reaction = (cur.fetchone() or {}).get("m")
                    cur.execute("RELEASE SAVEPOINT bola_tahlil")
                except Exception:   # jadval hali yo'q
                    cur.execute("ROLLBACK TO SAVEPOINT bola_tahlil")
            cur.execute("""SELECT COUNT(DISTINCT sana) AS n FROM (
                             SELECT sana FROM bola_dars_faollik WHERE child_id=%s AND sana > %s
                             UNION SELECT sana FROM bola_vaqt WHERE child_id=%s AND sana > %s) x""",
                        (bola_id, day - timedelta(days=7), bola_id, day - timedelta(days=7)))
            days_active = int((cur.fetchone() or {}).get("n") or 0)
            # Tengdoshlar: shu yosh guruhidagi bog'cha bolalari, oxirgi 7 kun (ismsiz — faqat o'rin)
            peer_sql = """SELECT f.child_id, MAX(u.class) AS class, {lp} AS lp,
                                  COALESCE(SUM(f.yulduz),0) AS yulduz,
                                  AVG(f.javob_ms) FILTER (WHERE f.javob_ms IS NOT NULL) AS javob_ms,
                                  SUM(f.togri) FILTER (WHERE f.tugadi_at IS NOT NULL) AS togri,
                                  SUM(f.jami) FILTER (WHERE f.tugadi_at IS NOT NULL) AS jami
                           FROM bola_dars_faollik f JOIN users u ON u.user_id=f.child_id
                           WHERE f.sana > %s GROUP BY f.child_id LIMIT 5000"""
            try:
                cur.execute("SAVEPOINT bola_tengdosh")
                cur.execute(peer_sql.format(lp="(ARRAY_AGG(u.kabutar_learning_profile))[1]"), (day - timedelta(days=7),))
                peer_rows = cur.fetchall()
                cur.execute("RELEASE SAVEPOINT bola_tengdosh")
            except Exception:   # eski baza: ta'lim profili ustuni yo'q — guruhsiz taqqoslanadi
                cur.execute("ROLLBACK TO SAVEPOINT bola_tengdosh")
                cur.execute(peer_sql.format(lp="NULL::jsonb"), (day - timedelta(days=7),))
                peer_rows, group = cur.fetchall(), ""
            peers = {}
            for r in peer_rows:
                lp = r["lp"] if isinstance(r["lp"], dict) else {}
                if group and preschool_learner({"kabutar_learning_profile": lp, "class": r["class"]}) != group:
                    continue
                peers[int(r["child_id"])] = {"yulduz": int(r["yulduz"] or 0),
                                             "javob_ms": float(r["javob_ms"]) if r["javob_ms"] is not None else None,
                                             "aniqlik": (int(r["togri"] or 0) / int(r["jami"])) if r["jami"] else None}
            conn.commit()
            name, _ = child_card(cur, bola_id)
            return {"bola": {"user_id": bola_id, "ism": name, "guruh": group},
                    **insights(bola_id, lessons, answers, float(reaction) if reaction else None, days_active, peers)}
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
                if time_state(cur, row["child_id"], row["sana"])["tugadi"]["dars"]:
                    # REV103: dars vaqti tugagani uchun to'xtadi — bu «mashq qilmayapti» emas, ota-onaga yozilmaydi
                    cur.execute("UPDATE bola_dars_faollik SET ogohlantirish_soni=%s WHERE id=%s", (MAX_IDLE_ALERTS, row["id"]))
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

    # ── REV103: butun platformada 5 daqiqa yo'q (boshqa ilova, ekran o'chgan) — ota-onaga «Bilasizmi?» ──
    def check_session_idle(now=None):
        now = now or datetime.now(timezone.utc)
        day = tashkent_day(now)
        sent = 0

        def run(conn, cur):
            nonlocal sent
            cur.execute("SELECT pg_try_advisory_xact_lock(%s) AS ok", (91039103,))
            if not cur.fetchone()["ok"]:
                conn.rollback()
                return 0
            limit = now - timedelta(minutes=IDLE_MINUTES)
            # shu yo'qlik haqida aytilganlar SQL'da chiqarib tashlanadi — ko'p bola bo'lsa ham hech kim navbatda qolib ketmaydi
            cur.execute("""SELECT * FROM bola_sessiya
                           WHERE sana=%s AND ogohlantirish_soni < %s AND oxirgi_signal_at > %s
                             AND ((NOT korinadi AND yashirildi_at <= %s) OR oxirgi_signal_at <= %s)
                             AND (ogohlantirildi_at IS NULL OR ogohlantirildi_at <
                                  CASE WHEN NOT korinadi AND yashirildi_at IS NOT NULL THEN yashirildi_at ELSE oxirgi_signal_at END)
                           ORDER BY oxirgi_signal_at LIMIT 300 FOR UPDATE SKIP LOCKED""",
                        (day, SESSION_IDLE_ALERTS_PER_DAY, now - timedelta(hours=3), limit, limit))
            for row in [dict(r) for r in cur.fetchall()]:
                state = time_state(cur, row["child_id"], day)
                if state["tugadi"]["jami"]:   # bugungi vaqti tugagan — chiqib ketishi kutilgan, bugun boshqa tekshirilmaydi
                    cur.execute("UPDATE bola_sessiya SET ogohlantirish_soni=%s WHERE child_id=%s", (SESSION_IDLE_ALERTS_PER_DAY, row["child_id"]))
                    continue
                cur.execute("""SELECT * FROM bola_dars_faollik WHERE child_id=%s AND sana=%s AND tugadi_at IS NULL
                                 AND ogohlantirish_soni < %s AND oxirgi_signal_at > %s""",
                            (row["child_id"], day, MAX_IDLE_ALERTS, now - timedelta(hours=3)))
                lessons = [dict(r) for r in cur.fetchall()]
                start = row["yashirildi_at"] if not row["korinadi"] and row["yashirildi_at"] else row["oxirgi_signal_at"]
                if any(l.get("ogohlantirildi_at") and l["ogohlantirildi_at"] >= start for l in lessons):
                    # shu yo'qlik haqida «darsi yarim qoldi» xabari ketgan — ikkinchi marta yozilmaydi
                    cur.execute("UPDATE bola_sessiya SET ogohlantirildi_at=%s WHERE child_id=%s", (now, row["child_id"]))
                    continue
                if not state["tugadi"]["dars"] and any(idle_reason(l, now) for l in lessons):
                    continue   # yarim qolgan dars haqida dars kuzatuvchisi aytadi
                name, kid = child_card(cur, row["child_id"])
                if not kid:
                    continue
                where = f" Oxirgi marta: «{row['nom']}»." if row.get("nom") else ""
                notify(cur, row["child_id"],
                       f"⏸ Bilasizmi? {name} {IDLE_MINUTES} daqiqadan beri platformada emas — boshqa ilovaga o'tgan, "
                       f"telefon ekrani o'chgan yoki boshqa ish bilan band bo'lishi mumkin.{where}", "bola_vaqt")
                cur.execute("UPDATE bola_sessiya SET ogohlantirildi_at=%s, ogohlantirish_soni=ogohlantirish_soni+1 WHERE child_id=%s",
                            (now, row["child_id"]))
                sent += 1
            conn.commit()
            return sent
        return run_db(run)

    def watcher():
        time.sleep(15)
        while True:
            for job in (check_idle, check_session_idle):
                try:
                    job()
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
    router.check_session_idle = check_session_idle
    return router

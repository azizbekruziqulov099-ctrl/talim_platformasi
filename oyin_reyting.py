"""REV84: O'yinlar uchun umumiy poydevor — Elo reyting, vaqt nazorati (soat) va reyting jadvali.

Shashka, shaxmat va keyingi o'yinlar shu modulni ishlatadi:
  • reyting har o'yin turi uchun alohida (oyin = 'shashka' | 'shaxmat' | ...), boshlang'ich 1200;
  • faqat odam–odam o'yinlari hisoblanadi (bot, bekor qilingan o'yin — yo'q);
  • yangi o'yinchi (dastlabki 20 o'yin) tezroq o'z darajasiga chiqadi: K=40, keyin K=24, 2000 dan yuqori K=16;
  • vaqt nazorati «daqiqa+qo'shimcha soniya»: 3+2, 5+0, 10+0, 15+10 yoki cheksiz.
"""
from datetime import timedelta

START_RATING = 1200
FLOOR = 100
TIME_CONTROLS = {
    "3+2": (180, 2, "⚡ Tezkor 3+2"),
    "5+0": (300, 0, "⚡ Tezkor 5 daqiqa"),
    "10+0": (600, 0, "⏱ Oddiy 10 daqiqa"),
    "15+10": (900, 10, "🐢 Sokin 15+10"),
    "cheksiz": (None, 0, "♾ Vaqtsiz"),
}
DEFAULT_CONTROL = "10+0"
FIRST_MOVE_SECONDS = 30   # birinchi yurishni shuncha vaqtda qilmasa — o'yin bekor (reytingga ta'sirsiz)


def control_of(key):
    key = key if key in TIME_CONTROLS else DEFAULT_CONTROL
    base, inc, label = TIME_CONTROLS[key]
    return key, base, inc, label


def expected(ra, rb):
    return 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))


def k_factor(rating, games):
    if games < 20:
        return 40
    return 16 if rating >= 2000 else 24


def elo_delta(ra, rb, score, games_a):
    """score: 1 g'alaba, 0.5 durang, 0 mag'lubiyat. A uchun reyting o'zgarishi (butun son)."""
    return round(k_factor(ra, games_a) * (score - expected(ra, rb)))


def bot_level_for(rating):
    """Onlayn izlashda raqib topilmasa — o'yinchi reytingiga mos bot darajasi."""
    if rating < 1050:
        return 1
    if rating < 1300:
        return 2
    if rating < 1550:
        return 3
    return 4


def search_window(waited_seconds):
    """Raqib izlash oynasi: avval yaqin reytingli, kutgan sari kengayadi."""
    return 150 + int(max(0, waited_seconds)) * 40


# ── Soat (vaqt nazorati) ─────────────────────────────────────────
def clock_after_move(clock_ms, mover, elapsed_ms, increment_s):
    """Yurgan tomon vaqtidan sarflangan vaqt ayiriladi va qo'shimcha soniya qo'shiladi."""
    left = dict(clock_ms)
    left[mover] = max(0, left[mover] - int(elapsed_ms)) + int(increment_s) * 1000
    return left


def remaining_now(clock_ms, side_to_move, last_move_at, at):
    """Hozirgi paytdagi soat (yurish navbatidagi tomonning vaqti oqmoqda)."""
    left = dict(clock_ms)
    if last_move_at is not None:
        spent = int((at - last_move_at).total_seconds() * 1000)
        left[side_to_move] = max(0, left[side_to_move] - spent)
    return left


def flag_deadline(clock_ms, side_to_move, last_move_at):
    return last_move_at + timedelta(milliseconds=clock_ms[side_to_move])


# ── DB ───────────────────────────────────────────────────────────
def migrate(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS oyin_reyting (
            user_id BIGINT NOT NULL,
            oyin TEXT NOT NULL,
            reyting INT NOT NULL DEFAULT 1200,
            eng_yuqori INT NOT NULL DEFAULT 1200,
            oyinlar INT NOT NULL DEFAULT 0,
            galaba INT NOT NULL DEFAULT 0,
            maglubiyat INT NOT NULL DEFAULT 0,
            durang INT NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, oyin)
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS oyin_reyting_top ON oyin_reyting(oyin, reyting DESC)")


def get_rating(cur, user_id, oyin):
    cur.execute("SELECT reyting, oyinlar, galaba, maglubiyat, durang, eng_yuqori FROM oyin_reyting WHERE user_id=%s AND oyin=%s",
                (user_id, oyin))
    row = cur.fetchone()
    if not row:
        return {"reyting": START_RATING, "oyinlar": 0, "galaba": 0, "maglubiyat": 0, "durang": 0, "eng_yuqori": START_RATING}
    return dict(row)


def apply_result(cur, oyin, white_id, black_id, winner):
    """winner: 'w' | 'b' | 'durang'. Ikkala o'yinchining reytingini yangilaydi; {'w': delta, 'b': delta} qaytaradi."""
    if not white_id or not black_id or int(white_id) == int(black_id):
        return None
    ids = sorted({int(white_id), int(black_id)})
    for uid in ids:   # qulflash tartibi bir xil — deadlock bo'lmaydi
        cur.execute("""INSERT INTO oyin_reyting(user_id, oyin) VALUES(%s,%s) ON CONFLICT DO NOTHING""", (uid, oyin))
        cur.execute("SELECT 1 FROM oyin_reyting WHERE user_id=%s AND oyin=%s FOR UPDATE", (uid, oyin))
    w, b = get_rating(cur, white_id, oyin), get_rating(cur, black_id, oyin)
    score_w = 1.0 if winner == "w" else 0.0 if winner == "b" else 0.5
    dw = elo_delta(w["reyting"], b["reyting"], score_w, w["oyinlar"])
    db = elo_delta(b["reyting"], w["reyting"], 1 - score_w, b["oyinlar"])
    for uid, delta, score in ((white_id, dw, score_w), (black_id, db, 1 - score_w)):
        cur.execute("""UPDATE oyin_reyting SET reyting=GREATEST(%s, reyting+%s), eng_yuqori=GREATEST(eng_yuqori, reyting+%s),
                         oyinlar=oyinlar+1, galaba=galaba+%s, maglubiyat=maglubiyat+%s, durang=durang+%s, updated_at=NOW()
                       WHERE user_id=%s AND oyin=%s""",
                    (FLOOR, delta, delta, int(score == 1), int(score == 0), int(score == 0.5), uid, oyin))
    return {"w": dw, "b": db}


def leaderboard(cur, oyin, user_id=None, limit=20):
    cur.execute("""SELECT r.user_id, r.reyting, r.oyinlar, r.galaba, u.full_name, to_jsonb(u)->>'jins' AS jins
                   FROM oyin_reyting r JOIN users u ON u.user_id=r.user_id
                   WHERE r.oyin=%s AND r.oyinlar>0 ORDER BY r.reyting DESC, r.galaba DESC, r.user_id LIMIT %s""", (oyin, limit))
    top = [{"orin": i + 1, "user_id": int(r["user_id"]), "ism": (r["full_name"] or "O'yinchi")[:40], "jins": r["jins"],
            "reyting": r["reyting"], "oyinlar": r["oyinlar"], "galaba": r["galaba"]} for i, r in enumerate(cur.fetchall())]
    me = None
    if user_id:
        mine = get_rating(cur, user_id, oyin)
        # Jadvaldagi tartib bilan bir xil: reyting, keyin g'alabalar, keyin user_id.
        cur.execute("""SELECT COUNT(*)+1 AS o FROM oyin_reyting WHERE oyin=%s AND oyinlar>0 AND (reyting>%s
                         OR (reyting=%s AND galaba>%s) OR (reyting=%s AND galaba=%s AND user_id<%s))""",
                    (oyin, mine["reyting"], mine["reyting"], mine["galaba"], mine["reyting"], mine["galaba"], user_id))
        me = {**mine, "user_id": int(user_id), "orin": int(cur.fetchone()["o"]) if mine["oyinlar"] else None}
    return {"top": top, "men": me}

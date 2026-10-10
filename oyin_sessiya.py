"""REV84: Taxta o'yinlari uchun umumiy o'yin xizmati (shashka, shaxmat va keyingilari).

Har bir o'yin faqat «adapter» beradi (qoidalar, bot, baho); qolgan hamma narsa shu yerda bir xil:
  • rejimlar: bot bilan (4 daraja) · onlayn raqib (reyting bo'yicha juftlash) · do'st bilan (kod/havola);
  • vaqt nazorati (3+2, 5+0, 10+0, 15+10, vaqtsiz) — soat serverda hisoblanadi;
  • birinchi yurishni 30 soniyada qilmagan o'yin bekor bo'ladi (reytingga ta'sirsiz);
  • Elo reyting — faqat onlayn odam–odam o'yinlarida;
  • onlayn izlashda raqib topilmasa — reytingga mos bot; o'yin tugagach «mashq boti edi» deb aytiladi
    va reytingga hisoblanmaydi;
  • durang taklifi, taslim bo'lish, qayta o'ynash (revansh).
Holat mijoz so'raganda «dangasa» yangilanadi (bot yurishi, soat tugashi) — qator qulfi bilan, bir
nechta server nusxasida ham to'g'ri ishlaydi.
"""
import json
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from . import oyin_reyting as rt
    from . import oyin_turnir as tn
except ImportError:  # pragma: no cover
    from modules import oyin_reyting as rt
    from modules import oyin_turnir as tn

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SEARCH_BOT_AFTER = (14, 24)   # shuncha soniyada odam topilmasa — bot
QUEUE_ALIVE = 6
FRIEND_TTL = timedelta(minutes=30)
BOT_NAMES = [
    ("Jasur", "ogil"), ("Sardor", "ogil"), ("Bekzod", "ogil"), ("Otabek", "ogil"), ("Shahzod", "ogil"),
    ("Doniyor", "ogil"), ("Javohir", "ogil"), ("Abdulloh", "ogil"), ("Muhammadali", "ogil"), ("Asadbek", "ogil"),
    ("Madina", "qiz"), ("Dilnoza", "qiz"), ("Sevinch", "qiz"), ("Mohinur", "qiz"), ("Zarina", "qiz"),
    ("Shahzoda", "qiz"), ("Malika", "qiz"), ("Oysha", "qiz"), ("Robiya", "qiz"), ("Nilufar", "qiz"),
]
LEVEL_NAMES = {1: "Oson", 2: "O'rta", 3: "Qiyin", 4: "Usta"}


def now():
    return datetime.now(timezone.utc)


def ms(dt):
    return int(dt.timestamp() * 1000) if dt else None


def other(side):
    return "b" if side == "w" else "w"


def result_for(winner, me):
    if winner == "durang":
        return "durang"
    return "galaba" if winner == me else "maglubiyat"


def human_bot_name(rng=random):
    name, jins = rng.choice(BOT_NAMES)
    return f"{name} {rng.choice('ARSTMNKHODBQ')}.", jins


def bot_delay(hidden, legal_count, rng=random):
    """Bot o'ylash vaqti. Oddiy bot tez; yashirin bot odamdek — goh tez, goh uzoq o'ylaydi."""
    if not hidden:
        return rng.uniform(0.45, 0.9)
    if legal_count <= 1:
        return rng.uniform(0.8, 1.8)
    base = rng.uniform(1.3, 3.4) + min(legal_count, 14) * rng.uniform(0.04, 0.18)
    if rng.random() < 0.15:
        base += rng.uniform(2, 5)
    return min(base, 9.0)


class BotGame(BaseModel):
    token: Optional[str] = None
    daraja: int = Field(default=2, ge=1, le=4)
    rang: str = Field(default="w", pattern="^(w|b|random)$")


class Token(BaseModel):
    token: Optional[str] = None


class Search(BaseModel):
    token: Optional[str] = None
    nazorat: str = Field(default=rt.DEFAULT_CONTROL, max_length=10)


class FriendGame(BaseModel):
    token: Optional[str] = None
    rang: str = Field(default="random", pattern="^(w|b|random)$")
    nazorat: str = Field(default="cheksiz", max_length=10)


class Join(BaseModel):
    token: Optional[str] = None
    kod: str = Field(min_length=4, max_length=12)


class Move(BaseModel):
    token: Optional[str] = None
    path: List[str] = Field(min_length=2, max_length=20)
    versiya: Optional[int] = None


def migrate(cur):
    rt.migrate(cur)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS oyin_partiyalar (
            id BIGSERIAL PRIMARY KEY,
            oyin TEXT NOT NULL,
            kod TEXT UNIQUE NOT NULL,
            turi TEXT NOT NULL,                  -- bot | onlayn | dost
            oq_id BIGINT, qora_id BIGINT,
            oq_ism TEXT, qora_ism TEXT, oq_jins TEXT, qora_jins TEXT,
            oq_reyting INT, qora_reyting INT,
            bot_rang TEXT, bot_daraja INT, yashirin BOOLEAN NOT NULL DEFAULT FALSE,
            pozitsiya TEXT NOT NULL,
            navbat TEXT NOT NULL DEFAULT 'w',
            meta JSONB NOT NULL DEFAULT '{}'::jsonb,
            yurishlar JSONB NOT NULL DEFAULT '[]'::jsonb,
            holat TEXT NOT NULL DEFAULT 'davom',   -- kutish | davom | tugadi
            golib TEXT, sabab TEXT,
            nazorat TEXT NOT NULL DEFAULT 'cheksiz', qoshimcha INT NOT NULL DEFAULT 0,
            oq_ms INT, qora_ms INT,
            bot_vaqti TIMESTAMPTZ, oxirgi_yurish_at TIMESTAMPTZ,
            reyting_hisob BOOLEAN NOT NULL DEFAULT FALSE, reyting_qollandi BOOLEAN NOT NULL DEFAULT FALSE,
            oq_delta INT, qora_delta INT,
            durang_taklif TEXT, yana_taklif TEXT, keyingi_kod TEXT,
            versiya INT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS oyin_partiyalar_oq ON oyin_partiyalar(oyin, oq_id, holat)")
    cur.execute("CREATE INDEX IF NOT EXISTS oyin_partiyalar_qora ON oyin_partiyalar(oyin, qora_id, holat)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS oyin_navbat (
            oyin TEXT NOT NULL,
            user_id BIGINT NOT NULL,
            nazorat TEXT NOT NULL,
            reyting INT NOT NULL,
            ism TEXT, jins TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            bot_at TIMESTAMPTZ NOT NULL,
            topilgan_kod TEXT,
            PRIMARY KEY (oyin, user_id)
        )""")
    tn.migrate(cur)   # REV90: turnirlar


# ── Sof holat mantig'i (DB'siz sinaladi) ─────────────────────────
def start_clock(game, base_s, at):
    game["oq_ms"] = game["qora_ms"] = base_s * 1000 if base_s else None
    game["oxirgi_yurish_at"] = at


def clock_running(game):
    return game["oq_ms"] is not None and len(game["yurishlar"] or []) >= 2 and game["holat"] == "davom"


def clocks_now(game, at):
    if game["oq_ms"] is None:
        return None
    clock = {"w": game["oq_ms"], "b": game["qora_ms"]}
    if clock_running(game):
        clock = rt.remaining_now(clock, game["navbat"], game["oxirgi_yurish_at"], at)
    return clock


def first_move_deadline(game):
    """Onlayn/do'st o'yinida ikkala tomon birinchi yurishini 30 soniyada qilishi kerak."""
    if game["holat"] != "davom" or game["turi"] == "bot" or game["oq_ms"] is None:
        return None
    if len(game["yurishlar"] or []) >= 2 or game["bot_rang"] == game["navbat"]:
        return None
    return game["oxirgi_yurish_at"] + timedelta(seconds=rt.FIRST_MOVE_SECONDS)


def finish(game, winner, reason):
    game.update(holat="tugadi", golib=winner, sabab=reason, bot_vaqti=None, durang_taklif=None)


def create_game_router(platform, adapter):
    """adapter: key, prefix, initial(), legal(pos, side), find(pos, side, path), apply(pos, move),
    names(move), caps(move), update_meta(pos, move, meta), outcome(pos, side, meta, plies),
    choose(pos, side, level, time_limit), evaluate(pos, side), counts(pos), side_to_move(pos)|None."""
    router = APIRouter()
    ready = {"ok": False}
    P = adapter.prefix
    OYIN = adapter.key

    def uid_of(token, authorization):
        return int(platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization)))

    def open_db():
        conn = platform._db()
        cur = conn.cursor()
        if not ready["ok"]:
            migrate(cur)
            conn.commit()
            ready["ok"] = True
        return conn, cur

    def user_card(cur, user_id):
        cur.execute("SELECT full_name, to_jsonb(u)->>'jins' AS jins FROM users u WHERE user_id=%s", (user_id,))
        row = cur.fetchone() or {}
        return (str(row.get("full_name") or "O'yinchi").strip()[:40] or "O'yinchi"), row.get("jins")

    def unique_code(cur):
        for _ in range(10):
            kod = "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))
            cur.execute("SELECT 1 FROM oyin_partiyalar WHERE kod=%s", (kod,))
            if not cur.fetchone():
                return kod
        raise HTTPException(503, "Kod yaratib bo'lmadi, qayta urinib ko'ring")

    def insert_game(cur, turi, white, black, *, bot_rang=None, bot_daraja=None, hidden=False, holat="davom",
                    nazorat="cheksiz", rated=False):
        """white/black: (user_id|None, ism, jins, reyting|None)."""
        kod = unique_code(cur)
        at = now()
        control, base, inc, _ = rt.control_of(nazorat)
        pos = adapter.initial()
        bot_time = None
        if bot_rang == "w" and holat == "davom":
            bot_time = at + timedelta(seconds=bot_delay(hidden, len(adapter.legal(pos, "w"))) + (1.0 if hidden else 0.3))
        cur.execute("""INSERT INTO oyin_partiyalar(oyin,kod,turi,oq_id,qora_id,oq_ism,qora_ism,oq_jins,qora_jins,oq_reyting,qora_reyting,
                         bot_rang,bot_daraja,yashirin,pozitsiya,holat,nazorat,qoshimcha,oq_ms,qora_ms,bot_vaqti,oxirgi_yurish_at,reyting_hisob)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (OYIN, kod, turi, white[0], black[0], white[1], black[1], white[2], black[2], white[3], black[3],
                     bot_rang, bot_daraja, hidden, pos, holat, control, inc,
                     base * 1000 if base else None, base * 1000 if base else None, bot_time, at if holat == "davom" else None, rated))
        return kod

    def game_by_code(cur, kod, lock=False):
        cur.execute("SELECT * FROM oyin_partiyalar WHERE oyin=%s AND kod=%s" + (" FOR UPDATE" if lock else ""),
                    (OYIN, str(kod or "").strip().upper()[:12]))
        game = cur.fetchone()
        if not game:
            raise HTTPException(404, "O'yin topilmadi. Kodni tekshiring.")
        game = dict(game)
        game["meta"] = game.get("meta") or {}
        game["yurishlar"] = game.get("yurishlar") or []
        return game

    def game_by_id(cur, gid):
        cur.execute("SELECT * FROM oyin_partiyalar WHERE id=%s FOR UPDATE", (gid,))
        game = dict(cur.fetchone())
        game["meta"] = game.get("meta") or {}
        game["yurishlar"] = game.get("yurishlar") or []
        return game

    def my_side(game, user_id):
        if game["oq_id"] is not None and int(game["oq_id"]) == user_id:
            return "w"
        if game["qora_id"] is not None and int(game["qora_id"]) == user_id:
            return "b"
        return None

    def schedule_bot(game, at):
        if game["holat"] == "davom" and game["bot_rang"] == game["navbat"]:
            legal = len(adapter.legal(game["pozitsiya"], game["navbat"]))
            delay = bot_delay(game["yashirin"], legal)
            clock = clocks_now(game, at)
            if clock:   # soat bilan o'ynayotgan bot vaqtini tugatib qo'ymaydi
                delay = min(delay, max(0.3, clock[game["navbat"]] / 1000 / 12))
            game["bot_vaqti"] = at + timedelta(seconds=delay)
        else:
            game["bot_vaqti"] = None

    def play(game, move, at):
        mover = game["navbat"]
        plies_before = len(game["yurishlar"])
        if game["oq_ms"] is not None:
            clock = {"w": game["oq_ms"], "b": game["qora_ms"]}
            elapsed = int((at - game["oxirgi_yurish_at"]).total_seconds() * 1000) if plies_before >= 2 else 0
            clock = rt.clock_after_move(clock, mover, elapsed, game["qoshimcha"] if plies_before >= 2 else 0)
            game["oq_ms"], game["qora_ms"] = clock["w"], clock["b"]
        before = game["pozitsiya"]
        game["meta"] = adapter.update_meta(before, move, dict(game["meta"]))
        game["pozitsiya"] = adapter.apply(before, move)
        moves = list(game["yurishlar"])
        moves.append({"p": adapter.names(move), "c": adapter.caps(move), "s": mover, "t": ms(at),
                      **({"n": adapter.notation(before, move)} if hasattr(adapter, "notation") else {})})
        game["yurishlar"] = moves
        game["navbat"] = other(mover)
        game["oxirgi_yurish_at"] = at
        game["versiya"] += 1
        if game["durang_taklif"] and game["durang_taklif"] != mover:
            game["durang_taklif"] = None   # taklif qilinganiga yurish bilan javob — rad
        done, winner, reason = adapter.outcome(game["pozitsiya"], game["navbat"], game["meta"], len(moves))
        if done:
            finish(game, winner or "durang", reason)
        schedule_bot(game, at)

    def advance(game, at):
        """Soat tugashi, birinchi yurish muddati va bot yurishi. O'zgarsa True."""
        if game["holat"] != "davom":
            return False
        clock = clocks_now(game, at)
        if clock and clock_running(game) and clock[game["navbat"]] <= 0:
            finish(game, other(game["navbat"]), "vaqt")
            return True
        deadline = first_move_deadline(game)
        if deadline and at > deadline:
            if game["turi"] == "turnir":   # turnirda kelmagan o'yinchi texnik mag'lubiyat oladi
                finish(game, other(game["navbat"]), "kelmadi")
            else:
                finish(game, "durang", "bekor")
            return True
        if game["bot_rang"] == game["navbat"] and game["bot_vaqti"] and at >= game["bot_vaqti"]:
            limit = 1.0 if not clock else max(0.2, min(1.0, clock[game["navbat"]] / 1000 / 20))
            move = adapter.choose(game["pozitsiya"], game["navbat"], game["bot_daraja"] or 2, limit, game["meta"])
            if move is None:
                done, winner, reason = adapter.outcome(game["pozitsiya"], game["navbat"], game["meta"], len(game["yurishlar"]))
                finish(game, winner or "durang", reason or "yurish_yoq")
            else:
                play(game, move, at)
            return True
        return False

    def save(cur, game):
        if game["holat"] == "tugadi" and game["reyting_hisob"] and not game["reyting_qollandi"]:
            game["reyting_qollandi"] = True
            if game["sabab"] not in ("bekor", "kelmadi"):
                deltas = rt.apply_result(cur, OYIN, game["oq_id"], game["qora_id"], game["golib"])
                if deltas:
                    game["oq_delta"], game["qora_delta"] = deltas["w"], deltas["b"]
        cur.execute("""UPDATE oyin_partiyalar SET pozitsiya=%s, navbat=%s, meta=%s::jsonb, yurishlar=%s::jsonb, holat=%s, golib=%s,
                         sabab=%s, oq_ms=%s, qora_ms=%s, bot_vaqti=%s, oxirgi_yurish_at=%s, reyting_qollandi=%s, oq_delta=%s,
                         qora_delta=%s, durang_taklif=%s, yana_taklif=%s, keyingi_kod=%s, oq_id=%s, qora_id=%s, oq_ism=%s,
                         qora_ism=%s, oq_jins=%s, qora_jins=%s, oq_reyting=%s, qora_reyting=%s, versiya=%s, updated_at=NOW()
                       WHERE id=%s""",
                    (game["pozitsiya"], game["navbat"], json.dumps(game["meta"]), json.dumps(game["yurishlar"]), game["holat"],
                     game["golib"], game["sabab"], game["oq_ms"], game["qora_ms"], game["bot_vaqti"], game["oxirgi_yurish_at"],
                     game["reyting_qollandi"], game["oq_delta"], game["qora_delta"], game["durang_taklif"], game["yana_taklif"],
                     game["keyingi_kod"], game["oq_id"], game["qora_id"], game["oq_ism"], game["qora_ism"], game["oq_jins"],
                     game["qora_jins"], game["oq_reyting"], game["qora_reyting"], game["versiya"], game["id"]))

    def view(game, user_id, at):
        me = my_side(game, user_id)
        over = game["holat"] == "tugadi"

        def player(side):
            p = "oq" if side == "w" else "qora"
            is_bot = game["bot_rang"] == side
            visible_bot = is_bot and (not game["yashirin"] or over)
            name = game[f"{p}_ism"]
            if is_bot and not game["yashirin"]:
                name = f"Bot · {LEVEL_NAMES.get(game['bot_daraja'] or 2, '')}"
            return {"ism": name, "jins": game[f"{p}_jins"], "bot": bool(visible_bot),
                    "bor": bool(is_bot or game[f"{p}_id"] is not None),
                    "reyting": game[f"{p}_reyting"] if (not is_bot or game["yashirin"]) else None,
                    "delta": game[f"{p}_delta"]}

        moves = game["yurishlar"]
        _, _, _, label = rt.control_of(game["nazorat"])
        out = {
            "oyin": OYIN, "kod": game["kod"], "turi": game["turi"], "holat": game["holat"], "pozitsiya": game["pozitsiya"],
            "navbat": game["navbat"], "men": me, "oq": player("w"), "qora": player("b"),
            "yurishlar_soni": len(moves), "oxirgi": moves[-1] if moves else None,
            "tarix": [m.get("n") or "-".join(m["p"]) for m in moves][-400:],
            "versiya": game["versiya"], "server_now": ms(at), "donalar": adapter.counts(game["pozitsiya"]),
            "nazorat": game["nazorat"], "nazorat_nomi": label, "qoshimcha": game["qoshimcha"],
            "soat": clocks_now(game, at), "soat_yurmoqda": clock_running(game),
            # yashirin bot o'yini tugaguncha oddiy onlayn o'yindek ko'rinadi; tugagach «hisoblanmadi» deb aytiladi
            "reytingli": bool(game["reyting_hisob"] or (game["yashirin"] and not over)), "durang_taklif": game["durang_taklif"],
            "yana_taklif": game["yana_taklif"], "keyingi_kod": game["keyingi_kod"],
        }
        deadline = first_move_deadline(game)
        if deadline:
            out["birinchi_yurish_tugaydi"] = ms(deadline)
        if game["turi"] == "bot":
            out["bot_daraja"] = game["bot_daraja"]
        if game.get("turnir_kod"):
            out.update(turnir_kod=game["turnir_kod"], tur=game.get("tur"))
        if hasattr(adapter, "status"):
            out.update(adapter.status(game["pozitsiya"]))
        if game["holat"] == "davom" and me and me == game["navbat"]:
            legal = adapter.legal(game["pozitsiya"], me)
            out["mumkin"] = [adapter.names(m) for m in legal]
            if hasattr(adapter, "hint"):
                out.update(adapter.hint(game["pozitsiya"], me, legal))
        if over:
            out.update(golib=game["golib"], sabab=game["sabab"], natija=result_for(game["golib"], me) if me else None,
                       raqib_bot=bool(game["bot_rang"]))
        return out

    def begin(cur, conn, fn):
        try:
            return fn()
        finally:
            cur.close()
            conn.close()

    # ── Bot bilan ──
    @router.post(f"{P}/bot")
    def start_bot(body: BotGame, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        conn, cur = open_db()

        def run():
            name, jins = user_card(cur, user_id)
            side = body.rang if body.rang in ("w", "b") else random.choice("wb")
            me, bot = (user_id, name, jins, None), (None, "Bot", None, None)
            white, black = (me, bot) if side == "w" else (bot, me)
            kod = insert_game(cur, "bot", white, black, bot_rang=other(side), bot_daraja=body.daraja)
            conn.commit()
            return {"kod": kod}
        return begin(cur, conn, run)

    # ── Onlayn raqib izlash (reyting va vaqt nazorati bo'yicha) ──
    def try_match(cur, user_id, at):
        cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"oyin-navbat:{OYIN}",))
        cur.execute("SELECT * FROM oyin_navbat WHERE oyin=%s AND user_id=%s", (OYIN, user_id))
        mine = cur.fetchone()
        if not mine:
            return None
        if mine["topilgan_kod"]:
            cur.execute("DELETE FROM oyin_navbat WHERE oyin=%s AND user_id=%s", (OYIN, user_id))
            return mine["topilgan_kod"]
        cur.execute("UPDATE oyin_navbat SET last_seen=%s WHERE oyin=%s AND user_id=%s", (at, OYIN, user_id))
        waited = (at - mine["created_at"]).total_seconds()
        window = rt.search_window(waited)
        cur.execute("""SELECT * FROM oyin_navbat WHERE oyin=%s AND user_id<>%s AND topilgan_kod IS NULL AND nazorat=%s
                         AND last_seen > %s AND ABS(reyting-%s) <= GREATEST(%s, 150 + EXTRACT(EPOCH FROM (%s - created_at))::int*40)
                       ORDER BY ABS(reyting-%s), created_at LIMIT 1""",
                    (OYIN, user_id, mine["nazorat"], at - timedelta(seconds=QUEUE_ALIVE), mine["reyting"], window, at, mine["reyting"]))
        other_row = cur.fetchone()
        me = (user_id, mine["ism"], mine["jins"], mine["reyting"])
        if other_row:
            them = (int(other_row["user_id"]), other_row["ism"], other_row["jins"], other_row["reyting"])
            white, black = (me, them) if random.random() < 0.5 else (them, me)
            kod = insert_game(cur, "onlayn", white, black, nazorat=mine["nazorat"], rated=True)
            cur.execute("UPDATE oyin_navbat SET topilgan_kod=%s WHERE oyin=%s AND user_id=%s", (kod, OYIN, them[0]))
            cur.execute("DELETE FROM oyin_navbat WHERE oyin=%s AND user_id=%s", (OYIN, user_id))
            return kod
        if at >= mine["bot_at"]:
            bot_name, bot_jins = human_bot_name()
            bot_rating = max(rt.FLOOR, mine["reyting"] + random.randint(-60, 60))
            bot = (None, bot_name, bot_jins, bot_rating)
            side = random.choice("wb")
            white, black = (me, bot) if side == "w" else (bot, me)
            kod = insert_game(cur, "onlayn", white, black, bot_rang=other(side), bot_daraja=rt.bot_level_for(mine["reyting"]),
                              hidden=True, nazorat=mine["nazorat"], rated=False)
            cur.execute("DELETE FROM oyin_navbat WHERE oyin=%s AND user_id=%s", (OYIN, user_id))
            return kod
        return None

    @router.post(f"{P}/izla")
    def search(body: Search, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            control, base, _, _ = rt.control_of(body.nazorat)
            if not base:
                control = rt.DEFAULT_CONTROL   # onlayn o'yin doim soat bilan
            name, jins = user_card(cur, user_id)
            rating = rt.get_rating(cur, user_id, OYIN)["reyting"]
            cur.execute("""INSERT INTO oyin_navbat(oyin,user_id,nazorat,reyting,ism,jins,created_at,last_seen,bot_at)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT(oyin,user_id) DO UPDATE SET nazorat=EXCLUDED.nazorat, reyting=EXCLUDED.reyting, ism=EXCLUDED.ism,
                             jins=EXCLUDED.jins, created_at=EXCLUDED.created_at, last_seen=EXCLUDED.last_seen, bot_at=EXCLUDED.bot_at,
                             topilgan_kod=NULL""",
                        (OYIN, user_id, control, rating, name, jins, at, at, at + timedelta(seconds=random.uniform(*SEARCH_BOT_AFTER))))
            kod = try_match(cur, user_id, at)
            conn.commit()
            return {"kod": kod} if kod else {"kutish": True, "soniya": 0, "nazorat": control, "reyting": rating}
        return begin(cur, conn, run)

    @router.get(f"{P}/izla")
    def search_poll(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            kod = try_match(cur, user_id, at)
            cur.execute("SELECT created_at, nazorat, reyting FROM oyin_navbat WHERE oyin=%s AND user_id=%s", (OYIN, user_id))
            row = cur.fetchone()
            conn.commit()
            if kod:
                return {"kod": kod}
            if not row:
                return {"kutish": False}
            return {"kutish": True, "soniya": int((at - row["created_at"]).total_seconds()), "nazorat": row["nazorat"], "reyting": row["reyting"]}
        return begin(cur, conn, run)

    @router.post(f"{P}/izla/bekor")
    def search_cancel(body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        conn, cur = open_db()

        def run():
            cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"oyin-navbat:{OYIN}",))
            cur.execute("DELETE FROM oyin_navbat WHERE oyin=%s AND user_id=%s RETURNING topilgan_kod", (OYIN, user_id))
            row = cur.fetchone()
            conn.commit()
            return {"ok": True, "kod": row["topilgan_kod"] if row else None}
        return begin(cur, conn, run)

    # ── Do'st bilan ──
    @router.post(f"{P}/dost")
    def friend_create(body: FriendGame, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        conn, cur = open_db()

        def run():
            name, jins = user_card(cur, user_id)
            rating = rt.get_rating(cur, user_id, OYIN)["reyting"]
            side = body.rang if body.rang in ("w", "b") else random.choice("wb")
            me, empty = (user_id, name, jins, rating), (None, None, None, None)
            white, black = (me, empty) if side == "w" else (empty, me)
            kod = insert_game(cur, "dost", white, black, holat="kutish", nazorat=body.nazorat)
            conn.commit()
            return {"kod": kod}
        return begin(cur, conn, run)

    @router.post(f"{P}/qoshil")
    def friend_join(body: Join, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        conn, cur = open_db()

        def run():
            game = game_by_code(cur, body.kod, lock=True)
            if my_side(game, user_id):
                return {"kod": game["kod"]}
            if game["turi"] != "dost" or game["holat"] != "kutish":
                raise HTTPException(409, "Bu o'yinda joy yo'q — u allaqachon boshlangan.")
            if game["created_at"] < now() - FRIEND_TTL:
                raise HTTPException(410, "Taklif vaqti o'tib ketgan. Do'stingizdan yangi kod so'rang.")
            name, jins = user_card(cur, user_id)
            slot = "oq" if game["oq_id"] is None else "qora"
            game.update({f"{slot}_id": user_id, f"{slot}_ism": name, f"{slot}_jins": jins,
                         f"{slot}_reyting": rt.get_rating(cur, user_id, OYIN)["reyting"]})
            game["holat"] = "davom"
            game["oxirgi_yurish_at"] = now()
            game["versiya"] += 1
            save(cur, game)
            conn.commit()
            return {"kod": game["kod"]}
        return begin(cur, conn, run)

    # ── Reyting jadvali va umumiy ma'lumot (/{kod} dan oldin) ──
    @router.get(f"{P}/reyting")
    def rating_table(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        conn, cur = open_db()

        def run():
            data = rt.leaderboard(cur, OYIN, user_id)
            conn.commit()
            return data
        return begin(cur, conn, run)

    # ── Turnirlar (/{kod} dan oldin ulanadi) ──
    from types import SimpleNamespace
    tn.attach(router, SimpleNamespace(P=P, OYIN=OYIN, rt=rt, now=now, ms=ms, uid_of=uid_of, open_db=open_db, begin=begin,
                                      user_card=user_card, insert_game=insert_game, advance=advance, save=save, game_by_id=game_by_id))

    @router.get(P)
    def summary(token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        conn, cur = open_db()

        def run():
            cur.execute("""SELECT kod, turi, holat, sabab, golib, CASE WHEN oq_id=%s THEN 'w' ELSE 'b' END AS men, updated_at
                           FROM oyin_partiyalar WHERE oyin=%s AND (oq_id=%s OR qora_id=%s) ORDER BY updated_at DESC LIMIT 300""",
                        (user_id, OYIN, user_id, user_id))
            rows = [dict(r) for r in cur.fetchall()]
            rating = rt.get_rating(cur, user_id, OYIN)
            conn.commit()
            stats = {"galaba": 0, "maglubiyat": 0, "durang": 0}
            active = None
            for r in rows:
                if r["holat"] == "tugadi" and r["golib"] and r["sabab"] != "bekor":
                    stats[result_for(r["golib"], r["men"])] += 1
                elif r["holat"] == "davom" and active is None and r["updated_at"] > now() - timedelta(hours=6):
                    active = {"kod": r["kod"], "turi": r["turi"]}
            return {"statistika": stats, "davom": active, "reyting": rating,
                    "nazoratlar": [{"kod": k, "nomi": v[2]} for k, v in rt.TIME_CONTROLS.items()]}
        return begin(cur, conn, run)

    # ── O'yin ──
    def locked_game(cur, kod, user_id, need_player=True):
        game = game_by_code(cur, kod, lock=True)
        side = my_side(game, user_id)
        if need_player and not side:
            raise HTTPException(403, "Siz bu o'yinda ishtirok etmaysiz")
        return game, side

    @router.get(P + "/{kod}")
    def state(kod: str, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            game, side = locked_game(cur, kod, user_id, need_player=False)
            if not side and game["holat"] != "kutish":
                raise HTTPException(403, "Siz bu o'yinda ishtirok etmaysiz")
            if advance(game, at):
                save(cur, game)
            conn.commit()
            return view(game, user_id, at)
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/yur")
    def make_move(kod: str, body: Move, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            game, side = locked_game(cur, kod, user_id)
            if advance(game, at):
                save(cur, game)
                conn.commit()
            if game["holat"] != "davom":
                raise HTTPException(409, "O'yin tugagan")
            if game["navbat"] != side:
                raise HTTPException(409, "Hozir raqibning navbati")
            move = adapter.find(game["pozitsiya"], side, body.path)
            if not move:
                raise HTTPException(400, adapter.illegal_message(game["pozitsiya"], side) if hasattr(adapter, "illegal_message")
                                    else "Bu yurish qoidaga to'g'ri kelmaydi")
            play(game, move, at)
            save(cur, game)
            conn.commit()
            return view(game, user_id, at)
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/taslim")
    def resign(kod: str, body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            game, side = locked_game(cur, kod, user_id)
            if game["holat"] == "kutish" or (game["holat"] == "davom" and len(game["yurishlar"]) < 2 and game["turi"] not in ("bot", "turnir")):
                finish(game, "durang", "bekor")   # o'yin boshlanmay turib chiqish — bekor
            elif game["holat"] == "davom":
                finish(game, other(side), "taslim")
            game["versiya"] += 1
            save(cur, game)
            conn.commit()
            return view(game, user_id, at)
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/durang")
    def offer_draw(kod: str, body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            game, side = locked_game(cur, kod, user_id)
            if game["holat"] != "davom":
                raise HTTPException(409, "O'yin tugagan")
            out = {}
            if game["bot_rang"]:
                bot = game["bot_rang"]
                score = adapter.evaluate(game["pozitsiya"], bot)
                if score <= -150 or (len(game["yurishlar"]) >= 60 and abs(score) < 60):
                    finish(game, "durang", "kelishuv")
                else:
                    out["rad"] = True
            elif game["durang_taklif"] == other(side):
                finish(game, "durang", "kelishuv")
            else:
                game["durang_taklif"] = side
            game["versiya"] += 1
            save(cur, game)
            conn.commit()
            return {**view(game, user_id, at), **out}
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/durang/rad")
    def decline_draw(kod: str, body: Token, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            game, side = locked_game(cur, kod, user_id)
            if game["durang_taklif"] == other(side):
                game["durang_taklif"] = None
                game["versiya"] += 1
                save(cur, game)
                conn.commit()
            return view(game, user_id, at)
        return begin(cur, conn, run)

    def replay(game, keep):
        """Dastlabki pozitsiyadan birinchi `keep` ta yurishni qayta o'ynab, holatni tiklaydi."""
        pos, meta, side = adapter.initial(), {}, "w"
        kept = game["yurishlar"][:keep]
        for rec in kept:
            move = adapter.find(pos, side, rec["p"])
            if move is None:
                raise HTTPException(409, "Yurishlar tarixini tiklab bo'lmadi")
            meta = adapter.update_meta(pos, move, meta)
            pos = adapter.apply(pos, move)
            side = other(side)
        game.update(pozitsiya=pos, meta=meta, yurishlar=kept, navbat=side, holat="davom", golib=None, sabab=None,
                    durang_taklif=None, yana_taklif=None, keyingi_kod=None)
        game["versiya"] += 1

    @router.post(P + "/{kod}/qaytar")
    def take_back(kod: str, body: Token, authorization: str = Header(None)):
        """Bot bilan mashqda oxirgi yurishni qaytarish (o'rganish uchun). Reytingli o'yinda yo'q."""
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()

        def run():
            game, side = locked_game(cur, kod, user_id)
            if game["turi"] != "bot":
                raise HTTPException(400, "Yurishni faqat bot bilan mashqda qaytarish mumkin")
            if game["holat"] == "tugadi" and game["sabab"] in ("taslim", "kelishuv"):
                raise HTTPException(409, "O'yin tugagan")
            mine = [i for i, m in enumerate(game["yurishlar"]) if m.get("s") == side]
            if not mine:
                raise HTTPException(409, "Qaytariladigan yurish yo'q")
            replay(game, mine[-1])
            schedule_bot(game, at)
            save(cur, game)
            conn.commit()
            return view(game, user_id, at)
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/maslahat")
    def advice(kod: str, body: Token, authorization: str = Header(None)):
        """Bot bilan mashqda «qaysi yurish yaxshi?» — kuchli bot tavsiyasi."""
        user_id = uid_of(body.token, authorization)
        conn, cur = open_db()

        def run():
            game, side = locked_game(cur, kod, user_id)
            conn.commit()
            if game["turi"] != "bot":
                raise HTTPException(400, "Maslahat faqat bot bilan mashqda beriladi")
            if game["holat"] != "davom" or game["navbat"] != side:
                raise HTTPException(409, "Hozir sizning navbatingiz emas")
            move = adapter.choose(game["pozitsiya"], side, 3, 0.8)
            if move is None:
                raise HTTPException(409, "Yurish yo'q")
            out = {"yurish": adapter.names(move)}
            if hasattr(adapter, "notation"):
                out["yozuv"] = adapter.notation(game["pozitsiya"], move)
            if hasattr(adapter, "explain"):
                out["izoh"] = adapter.explain(game["pozitsiya"], move)
            return out
        return begin(cur, conn, run)

    @router.post(P + "/{kod}/yana")
    def rematch(kod: str, body: Token, authorization: str = Header(None)):
        """Revansh: ranglar almashadi, vaqt nazorati o'sha. Odam–odam o'yinda ikkala tomon rozi bo'lishi kerak."""
        user_id = uid_of(body.token, authorization)
        conn, cur = open_db()

        def run():
            game, side = locked_game(cur, kod, user_id)
            if game["holat"] != "tugadi":
                raise HTTPException(409, "O'yin hali tugamagan")
            if game["keyingi_kod"]:
                return {"kod": game["keyingi_kod"]}
            if game["turi"] == "turnir":
                raise HTTPException(400, "Turnirda keyingi raqibni turnir o'zi tanlaydi")
            if game["bot_rang"] and game["yashirin"]:
                raise HTTPException(400, "Yangi raqib izlang")
            if game["turi"] == "bot":
                name, jins = user_card(cur, user_id)
                me, bot = (user_id, name, jins, None), (None, "Bot", None, None)
                new_side = other(side)
                white, black = (me, bot) if new_side == "w" else (bot, me)
                new = insert_game(cur, "bot", white, black, bot_rang=other(new_side), bot_daraja=game["bot_daraja"])
            else:
                if game["yana_taklif"] != other(side):
                    game["yana_taklif"] = side
                    game["versiya"] += 1
                    save(cur, game)
                    conn.commit()
                    return {"kutish": True}
                def card(p):
                    uid = game[f"{p}_id"]
                    return (uid, game[f"{p}_ism"], game[f"{p}_jins"], rt.get_rating(cur, uid, OYIN)["reyting"])
                new = insert_game(cur, game["turi"], card("qora"), card("oq"), nazorat=game["nazorat"], rated=game["reyting_hisob"])
            game["keyingi_kod"] = new
            game["versiya"] += 1
            save(cur, game)
            conn.commit()
            return {"kod": new}
        return begin(cur, conn, run)

    return router

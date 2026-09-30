"""REV90: Turnir va chempionatlar (shashka, shaxmat va keyingi taxta o'yinlari) — Shveytsariya tizimi.

  • Turnirni istalgan o'yinchi yoki ustoz yaratadi (kod bilan yopiq turnir — sinf, to'garak, maktab uchun);
    hammaga ochiq CHEMPIONAT/olimpiadani faqat admin e'lon qiladi (ro'yxatda hamma ko'radi).
  • Belgilangan vaqtda (yoki yaratuvchi «Boshlash»ni bossa) 1-tur juftlanadi. Tur tugashi bilan keyingisi o'zi
    juftlanadi: bir xil ochkolilar bir-biri bilan, ikki marta bir raqib bilan o'ynatilmaydi, ranglar navbatlanadi.
  • Toq sonli bo'lsa — eng pastdagi (hali «dam» olmagan) o'yinchi shu turda dam oladi va 1 ochko oladi.
  • G'alaba 1, durang ½. Teng ochkoda: Buxgolts (raqiblar ochkolari yig'indisi), g'alabalar soni, reyting.
  • Turnir o'yini soat bilan va reytingli (odam–odam). Birinchi yurishni 30 soniyada qilmagan o'yinchi
    texnik mag'lubiyat oladi (bu reytingga ta'sir qilmaydi).
Holat mijoz so'raganda «dangasa» yangilanadi (turnir qatori qulflanadi) — alohida fon jarayoni kerak emas.
"""
import json
import secrets
from datetime import timedelta
from typing import Optional

from fastapi import Header, HTTPException
from pydantic import BaseModel, Field

POINT = 2            # ochkolar yarimlarda saqlanadi: g'alaba 2, durang 1
MAX_SEARCH = 20000   # juftlash qidiruvi chegarasi (katta turnirda ham tez)
TOURNAMENT_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class NewTournament(BaseModel):
    token: Optional[str] = None
    nomi: str = Field(min_length=3, max_length=60)
    nazorat: str = Field(default="5+0", max_length=10)
    turlar: int = Field(default=5, ge=2, le=11)
    boshlanish_daqiqa: int = Field(default=10, ge=1, le=60 * 24 * 14)
    ochiq: bool = False
    max_ishtirokchi: int = Field(default=64, ge=2, le=256)
    izoh: str = Field(default="", max_length=240)
    qatnashaman: bool = True


class TournamentToken(BaseModel):
    token: Optional[str] = None


# ── Sof mantiq (DB'siz sinaladi) ─────────────────────────────────
def game_points(winner, side):
    """Bitta o'yindan `side` tomon oladigan ochko (yarimlarda)."""
    if winner == "durang":
        return 1
    return POINT if winner == side else 0


def standings(players, games, byes=None):
    """players: [{user_id, ism, jins, reyting, chiqdi}], games: [{tur, oq_id, qora_id, holat, golib}],
    byes: {user_id: [tur, ...]}. Qaytaradi: tartiblangan jadval (orin bilan)."""
    byes = byes or {}
    rows = {}
    for p in players:
        uid = int(p["user_id"])
        rows[uid] = {"user_id": uid, "ism": p.get("ism") or "O'yinchi", "jins": p.get("jins"),
                     "reyting": int(p.get("reyting") or 0), "chiqdi": bool(p.get("chiqdi")),
                     "ochko2": POINT * len(byes.get(uid, [])), "galaba": 0, "raqiblar": [], "ranglar": "",
                     "dam": len(byes.get(uid, [])), "natijalar": {}}
    for uid, rounds in byes.items():
        for tur in rounds:
            if int(uid) in rows:
                rows[int(uid)]["natijalar"][tur] = "dam"
    for g in sorted(games, key=lambda x: (x.get("tur") or 0)):
        w, b = g.get("oq_id"), g.get("qora_id")
        if w is None or b is None:
            continue
        w, b = int(w), int(b)
        for uid, side, opp in ((w, "w", b), (b, "b", w)):
            if uid not in rows:
                continue
            row = rows[uid]
            row["raqiblar"].append(opp)
            row["ranglar"] += side
            if g.get("holat") == "tugadi" and g.get("golib"):
                pts = game_points(g["golib"], side)
                row["ochko2"] += pts
                row["galaba"] += pts == POINT
                row["natijalar"][g.get("tur")] = {POINT: "1", 1: "½", 0: "0"}[pts]
            else:
                row["natijalar"][g.get("tur")] = "…"
    for row in rows.values():
        row["buxgolts2"] = sum(rows[o]["ochko2"] for o in row["raqiblar"] if o in rows)
    ordered = sorted(rows.values(), key=lambda r: (-r["ochko2"], -r["buxgolts2"], -r["galaba"], -r["reyting"], r["ism"], r["user_id"]))
    for i, row in enumerate(ordered):
        row["orin"] = i + 1
        row["ochko"] = row["ochko2"] / POINT
        row["buxgolts"] = row["buxgolts2"] / POINT
    return ordered


def _color_pair(a, b, rnd):
    """(oq, qora): kim ko'proq oq bilan o'ynagan bo'lsa — qora oladi; teng bo'lsa oxirgi rang almashadi."""
    da = a["ranglar"].count("w") - a["ranglar"].count("b")
    db = b["ranglar"].count("w") - b["ranglar"].count("b")
    if da != db:
        return (b, a) if da > db else (a, b)
    la, lb = a["ranglar"][-1:], b["ranglar"][-1:]
    if la != lb:
        return (b, a) if la == "w" else (a, b)
    return (a, b) if rnd % 2 else (b, a)


def pair_round(table, rnd):
    """table: standings() natijasi (tartiblangan). Qaytaradi: ([(oq_id, qora_id), ...], dam_oluvchi_id|None)."""
    active = [r for r in table if not r["chiqdi"]]
    if len(active) < 2:
        return [], (active[0]["user_id"] if active else None)
    bye = None
    if len(active) % 2:
        pool = sorted(active, key=lambda r: (r["dam"], r["ochko2"], r["reyting"], -r["orin"]))
        bye = pool[0]
        active = [r for r in active if r is not bye]
    if rnd == 1:
        seeded = sorted(active, key=lambda r: (-r["reyting"], r["ism"], r["user_id"]))
        half = len(seeded) // 2
        pairs = []
        for i in range(half):
            top, low = seeded[i], seeded[i + half]
            pairs.append((top["user_id"], low["user_id"]) if i % 2 == 0 else (low["user_id"], top["user_id"]))
        return pairs, bye["user_id"] if bye else None
    played = {frozenset((r["user_id"], o)) for r in active for o in r["raqiblar"]}
    steps = [0]

    def solve(pool):
        if not pool:
            return []
        steps[0] += 1
        if steps[0] > MAX_SEARCH:
            return None
        first, rest = pool[0], pool[1:]
        for i, cand in enumerate(rest):
            if frozenset((first["user_id"], cand["user_id"])) in played:
                continue
            tail = solve(rest[:i] + rest[i + 1:])
            if tail is not None:
                return [(first, cand)] + tail
        return None

    matched = solve(active)
    if matched is None:   # hamma bilan o'ynab bo'lingan — ketma-ket juftlanadi (takror uchrashuv)
        matched = [(active[i], active[i + 1]) for i in range(0, len(active) - 1, 2)]
    pairs = []
    for a, b in matched:
        w, bl = _color_pair(a, b, rnd)
        pairs.append((w["user_id"], bl["user_id"]))
    return pairs, bye["user_id"] if bye else None


def result_mark(game):
    if game.get("holat") != "tugadi" or not game.get("golib"):
        return "…"
    return {"w": "1–0", "b": "0–1"}.get(game["golib"], "½–½")


# ── Marshrutlar (create_game_router ichidan ulanadi) ─────────────
def migrate(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS oyin_turnirlar (
            id BIGSERIAL PRIMARY KEY,
            oyin TEXT NOT NULL,
            kod TEXT UNIQUE NOT NULL,
            nomi TEXT NOT NULL,
            izoh TEXT NOT NULL DEFAULT '',
            yaratuvchi_id BIGINT,
            ochiq BOOLEAN NOT NULL DEFAULT FALSE,
            nazorat TEXT NOT NULL,
            turlar INT NOT NULL,
            max_ishtirokchi INT NOT NULL DEFAULT 64,
            boshlanish TIMESTAMPTZ NOT NULL,
            holat TEXT NOT NULL DEFAULT 'royxat',      -- royxat | davom | tugadi | bekor
            joriy_tur INT NOT NULL DEFAULT 0,
            versiya INT NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS oyin_turnirlar_royxat ON oyin_turnirlar(oyin, ochiq, holat)")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS oyin_turnir_oyinchilar (
            turnir_id BIGINT NOT NULL REFERENCES oyin_turnirlar(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL,
            ism TEXT, jins TEXT, reyting INT NOT NULL DEFAULT 0,
            chiqdi BOOLEAN NOT NULL DEFAULT FALSE,
            dam_turlar JSONB NOT NULL DEFAULT '[]'::jsonb,
            qoshilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (turnir_id, user_id)
        )""")
    cur.execute("CREATE INDEX IF NOT EXISTS oyin_turnir_oyinchilar_user ON oyin_turnir_oyinchilar(user_id)")
    cur.execute("ALTER TABLE oyin_partiyalar ADD COLUMN IF NOT EXISTS turnir_id BIGINT")
    cur.execute("ALTER TABLE oyin_partiyalar ADD COLUMN IF NOT EXISTS turnir_kod TEXT")
    cur.execute("ALTER TABLE oyin_partiyalar ADD COLUMN IF NOT EXISTS tur INT")
    cur.execute("CREATE INDEX IF NOT EXISTS oyin_partiyalar_turnir ON oyin_partiyalar(turnir_id, tur)")


def attach(router, h):
    """h — create_game_router yordamchilari: OYIN, P, rt, now, ms, uid_of, open_db, begin, user_card, insert_game,
    advance, save, game_by_id."""
    P, OYIN, rt = h.P, h.OYIN, h.rt
    TP = f"{P}/turnir"

    def is_admin(cur, user_id):
        try:
            cur.execute("SAVEPOINT turnir_admin")
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
            ok = bool(cur.fetchone())
            cur.execute("RELEASE SAVEPOINT turnir_admin")
            return ok
        except Exception:   # jadval yo'q muhit (sinov)
            cur.execute("ROLLBACK TO SAVEPOINT turnir_admin")
            return False

    def unique_code(cur):
        for _ in range(10):
            kod = "T" + "".join(secrets.choice(TOURNAMENT_ALPHABET) for _ in range(5))
            cur.execute("SELECT 1 FROM oyin_turnirlar WHERE kod=%s", (kod,))
            if not cur.fetchone():
                return kod
        raise HTTPException(503, "Kod yaratib bo'lmadi, qayta urinib ko'ring")

    def load(cur, kod, lock=False):
        cur.execute("SELECT * FROM oyin_turnirlar WHERE oyin=%s AND kod=%s" + (" FOR UPDATE" if lock else ""),
                    (OYIN, str(kod or "").strip().upper()[:12]))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Turnir topilmadi. Kodni tekshiring.")
        return dict(row)

    def players_of(cur, t):
        cur.execute("SELECT * FROM oyin_turnir_oyinchilar WHERE turnir_id=%s ORDER BY qoshilgan_at, user_id", (t["id"],))
        return [dict(r) for r in cur.fetchall()]

    def games_of(cur, t):
        cur.execute("""SELECT id, kod, tur, oq_id, qora_id, oq_ism, qora_ism, holat, golib, sabab FROM oyin_partiyalar
                       WHERE oyin=%s AND turnir_id=%s ORDER BY tur, id""", (OYIN, t["id"]))
        return [dict(r) for r in cur.fetchall()]

    def table_of(players, games):
        byes = {int(p["user_id"]): list(p.get("dam_turlar") or []) for p in players}
        return standings(players, games, byes)

    def start_round(cur, t, players, games, rnd):
        table = table_of(players, games)
        pairs, bye = pair_round(table, rnd)
        if not pairs:
            return False
        by_id = {int(p["user_id"]): p for p in players}
        for w, b in pairs:
            cards = []
            for uid in (w, b):
                p = by_id[uid]
                cards.append((uid, p["ism"], p["jins"], rt.get_rating(cur, uid, OYIN)["reyting"]))
            kod = h.insert_game(cur, "turnir", cards[0], cards[1], nazorat=t["nazorat"], rated=True)
            cur.execute("UPDATE oyin_partiyalar SET turnir_id=%s, turnir_kod=%s, tur=%s WHERE kod=%s",
                        (t["id"], t["kod"], rnd, kod))
        if bye is not None:
            rounds = list(by_id[bye].get("dam_turlar") or []) + [rnd]
            cur.execute("UPDATE oyin_turnir_oyinchilar SET dam_turlar=%s::jsonb WHERE turnir_id=%s AND user_id=%s",
                        (json.dumps(rounds), t["id"], bye))
        t["joriy_tur"] = rnd
        return True

    def progress(cur, t, at):
        """Boshlanish vaqti, tur o'yinlarining soati va keyingi tur. O'zgarsa True."""
        changed = False
        if t["holat"] == "royxat" and at >= t["boshlanish"]:
            players = [p for p in players_of(cur, t) if not p["chiqdi"]]
            if len(players) < 2:
                t["holat"] = "bekor"
            else:
                t["holat"] = "davom"
                start_round(cur, t, players, [], 1)
            changed = True
        if t["holat"] != "davom":
            return changed
        cur.execute("SELECT id FROM oyin_partiyalar WHERE turnir_id=%s AND tur=%s AND holat='davom' ORDER BY id",
                    (t["id"], t["joriy_tur"]))
        for row in cur.fetchall():
            game = h.game_by_id(cur, row["id"])
            if h.advance(game, at):
                h.save(cur, game)
        cur.execute("SELECT COUNT(*) AS n FROM oyin_partiyalar WHERE turnir_id=%s AND tur=%s AND holat<>'tugadi'",
                    (t["id"], t["joriy_tur"]))
        if cur.fetchone()["n"]:
            return changed
        players = players_of(cur, t)
        active = [p for p in players if not p["chiqdi"]]
        if t["joriy_tur"] < t["turlar"] and len(active) >= 2 and start_round(cur, t, players, games_of(cur, t), t["joriy_tur"] + 1):
            return True
        t["holat"] = "tugadi"
        return True

    def store(cur, t):
        t["versiya"] += 1
        cur.execute("UPDATE oyin_turnirlar SET holat=%s, joriy_tur=%s, versiya=%s, updated_at=NOW() WHERE id=%s",
                    (t["holat"], t["joriy_tur"], t["versiya"], t["id"]))

    def card(t, user_id, count=None, joined=False):
        _, _, _, label = rt.control_of(t["nazorat"])
        return {"kod": t["kod"], "nomi": t["nomi"], "izoh": t["izoh"], "ochiq": t["ochiq"], "holat": t["holat"],
                "nazorat": t["nazorat"], "nazorat_nomi": label, "turlar": t["turlar"], "joriy_tur": t["joriy_tur"],
                "boshlanish": h.ms(t["boshlanish"]), "ishtirokchilar": count, "max_ishtirokchi": t["max_ishtirokchi"],
                "qatnashaman": joined, "yaratuvchi": t["yaratuvchi_id"] is not None and int(t["yaratuvchi_id"]) == user_id}

    def detail(cur, t, user_id, at):
        players = players_of(cur, t)
        games = games_of(cur, t)
        table = table_of(players, games)
        me = next((p for p in players if int(p["user_id"]) == user_id), None)
        out = card(t, user_id, len([p for p in players if not p["chiqdi"]]), bool(me and not me["chiqdi"]))
        out["server_now"] = h.ms(at)
        out["versiya"] = t["versiya"]
        out["jadval"] = [{k: r[k] for k in ("orin", "user_id", "ism", "jins", "reyting", "ochko", "buxgolts", "galaba", "chiqdi")}
                         | {"men": r["user_id"] == user_id, "natijalar": {str(k): v for k, v in r["natijalar"].items()}}
                         for r in table]
        rnd = t["joriy_tur"]
        out["juftlar"] = [{"kod": g["kod"], "oq": g["oq_ism"], "qora": g["qora_ism"], "natija": result_mark(g),
                           "men": user_id in (g["oq_id"], g["qora_id"])} for g in games if g["tur"] == rnd]
        mine = next((g for g in games if g["tur"] == rnd and user_id in (g["oq_id"], g["qora_id"])), None)
        out["mening_oyinim"] = mine["kod"] if mine and mine["holat"] == "davom" else None
        out["dam_olaman"] = bool(me and rnd in (me.get("dam_turlar") or []))
        if t["holat"] == "tugadi":
            out["golib"] = [{"orin": r["orin"], "ism": r["ism"], "ochko": r["ochko"]} for r in table[:3]]
        return out

    @router.get(TP)
    def tournaments(token: str = None, authorization: str = Header(None)):
        user_id = h.uid_of(token, authorization)
        at = h.now()
        conn, cur = h.open_db()

        def run():
            cur.execute("""SELECT t.*, (SELECT COUNT(*) FROM oyin_turnir_oyinchilar p WHERE p.turnir_id=t.id AND NOT p.chiqdi) AS soni,
                                  EXISTS(SELECT 1 FROM oyin_turnir_oyinchilar p WHERE p.turnir_id=t.id AND p.user_id=%s AND NOT p.chiqdi) AS men
                           FROM oyin_turnirlar t
                           WHERE t.oyin=%s AND (
                             (t.ochiq AND (t.holat IN ('royxat','davom') OR t.updated_at > %s))
                             OR t.yaratuvchi_id=%s
                             OR EXISTS(SELECT 1 FROM oyin_turnir_oyinchilar p WHERE p.turnir_id=t.id AND p.user_id=%s))
                           ORDER BY CASE t.holat WHEN 'davom' THEN 0 WHEN 'royxat' THEN 1 ELSE 2 END, t.boshlanish DESC LIMIT 40""",
                        (user_id, OYIN, at - timedelta(days=3), user_id, user_id))
            rows = [dict(r) for r in cur.fetchall()]
            admin = is_admin(cur, user_id)
            conn.commit()
            items = [card(r, user_id, int(r["soni"]), bool(r["men"])) for r in rows]
            return {"ochiq": [i for i in items if i["ochiq"]], "meniki": [i for i in items if not i["ochiq"]],
                    "admin": admin, "server_now": h.ms(at),
                    "nazoratlar": [{"kod": k, "nomi": v[2]} for k, v in rt.TIME_CONTROLS.items() if v[0]]}
        return h.begin(cur, conn, run)

    @router.post(TP)
    def create(body: NewTournament, authorization: str = Header(None)):
        user_id = h.uid_of(body.token, authorization)
        at = h.now()
        conn, cur = h.open_db()

        def run():
            control, base, _, _ = rt.control_of(body.nazorat)
            if not base:
                control = "5+0"   # turnir doim soat bilan — aks holda tur tugamay qolishi mumkin
            if body.ochiq and not is_admin(cur, user_id):
                raise HTTPException(403, "Hammaga ochiq chempionatni faqat admin e'lon qiladi. Sinf yoki to'garak uchun yopiq turnir yarating.")
            cur.execute("""SELECT COUNT(*) AS n FROM oyin_turnirlar WHERE oyin=%s AND yaratuvchi_id=%s AND holat IN ('royxat','davom')""",
                        (OYIN, user_id))
            if cur.fetchone()["n"] >= 5:
                raise HTTPException(429, "Sizda 5 ta faol turnir bor. Avval ulardan biri tugasin.")
            kod = unique_code(cur)
            cur.execute("""INSERT INTO oyin_turnirlar(oyin,kod,nomi,izoh,yaratuvchi_id,ochiq,nazorat,turlar,max_ishtirokchi,boshlanish)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (OYIN, kod, body.nomi.strip(), body.izoh.strip(), user_id, body.ochiq, control, body.turlar,
                         body.max_ishtirokchi, at + timedelta(minutes=body.boshlanish_daqiqa)))
            tid = cur.fetchone()["id"]
            if body.qatnashaman:
                name, jins = h.user_card(cur, user_id)
                cur.execute("INSERT INTO oyin_turnir_oyinchilar(turnir_id,user_id,ism,jins,reyting) VALUES(%s,%s,%s,%s,%s)",
                            (tid, user_id, name, jins, rt.get_rating(cur, user_id, OYIN)["reyting"]))
            conn.commit()
            return {"kod": kod}
        return h.begin(cur, conn, run)

    @router.get(TP + "/{tkod}")
    def tournament(tkod: str, token: str = None, authorization: str = Header(None)):
        user_id = h.uid_of(token, authorization)
        at = h.now()
        conn, cur = h.open_db()

        def run():
            t = load(cur, tkod, lock=True)
            if progress(cur, t, at):
                store(cur, t)
            out = detail(cur, t, user_id, at)
            conn.commit()
            return out
        return h.begin(cur, conn, run)

    @router.post(TP + "/{tkod}/qoshil")
    def join(tkod: str, body: TournamentToken, authorization: str = Header(None)):
        user_id = h.uid_of(body.token, authorization)
        at = h.now()
        conn, cur = h.open_db()

        def run():
            t = load(cur, tkod, lock=True)
            if t["holat"] != "royxat":
                raise HTTPException(409, "Ro'yxatdan o'tish yopilgan — turnir boshlanib bo'lgan.")
            cur.execute("SELECT chiqdi FROM oyin_turnir_oyinchilar WHERE turnir_id=%s AND user_id=%s", (t["id"], user_id))
            mine = cur.fetchone()
            if not (mine and not mine["chiqdi"]):
                cur.execute("SELECT COUNT(*) AS n FROM oyin_turnir_oyinchilar WHERE turnir_id=%s AND NOT chiqdi", (t["id"],))
                if cur.fetchone()["n"] >= t["max_ishtirokchi"]:
                    raise HTTPException(409, "Turnirda joy qolmadi.")
                name, jins = h.user_card(cur, user_id)
                cur.execute("""INSERT INTO oyin_turnir_oyinchilar(turnir_id,user_id,ism,jins,reyting) VALUES(%s,%s,%s,%s,%s)
                               ON CONFLICT(turnir_id,user_id) DO UPDATE SET chiqdi=FALSE, ism=EXCLUDED.ism, reyting=EXCLUDED.reyting""",
                            (t["id"], user_id, name, jins, rt.get_rating(cur, user_id, OYIN)["reyting"]))
                store(cur, t)
            out = detail(cur, t, user_id, at)
            conn.commit()
            return out
        return h.begin(cur, conn, run)

    @router.post(TP + "/{tkod}/chiq")
    def leave(tkod: str, body: TournamentToken, authorization: str = Header(None)):
        """Ro'yxatdan chiqish. Turnir davomida chiqsa — keyingi turlarga juftlanmaydi (joriy o'yini davom etadi)."""
        user_id = h.uid_of(body.token, authorization)
        at = h.now()
        conn, cur = h.open_db()

        def run():
            t = load(cur, tkod, lock=True)
            if t["holat"] in ("tugadi", "bekor"):
                raise HTTPException(409, "Turnir tugagan")
            if t["holat"] == "royxat":
                cur.execute("DELETE FROM oyin_turnir_oyinchilar WHERE turnir_id=%s AND user_id=%s", (t["id"], user_id))
            else:
                cur.execute("UPDATE oyin_turnir_oyinchilar SET chiqdi=TRUE WHERE turnir_id=%s AND user_id=%s", (t["id"], user_id))
            store(cur, t)
            out = detail(cur, t, user_id, at)
            conn.commit()
            return out
        return h.begin(cur, conn, run)

    @router.post(TP + "/{tkod}/boshla")
    def start_now(tkod: str, body: TournamentToken, authorization: str = Header(None)):
        user_id = h.uid_of(body.token, authorization)
        at = h.now()
        conn, cur = h.open_db()

        def run():
            t = load(cur, tkod, lock=True)
            if t["yaratuvchi_id"] is None or int(t["yaratuvchi_id"]) != user_id:
                raise HTTPException(403, "Turnirni faqat uni yaratgan kishi boshlaydi")
            if t["holat"] != "royxat":
                raise HTTPException(409, "Turnir allaqachon boshlangan")
            cur.execute("SELECT COUNT(*) AS n FROM oyin_turnir_oyinchilar WHERE turnir_id=%s AND NOT chiqdi", (t["id"],))
            if cur.fetchone()["n"] < 2:
                raise HTTPException(409, "Boshlash uchun kamida 2 ishtirokchi kerak")
            t["boshlanish"] = at
            cur.execute("UPDATE oyin_turnirlar SET boshlanish=%s WHERE id=%s", (at, t["id"]))
            progress(cur, t, at)
            store(cur, t)
            out = detail(cur, t, user_id, at)
            conn.commit()
            return out
        return h.begin(cur, conn, run)

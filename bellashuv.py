"""REV82: onlayn bellashuv — o'quvchi va talabalar o'zaro test bellashuvi («kim birinchi to'g'ri topadi»).

Xona ochiladi (mavzu → savollar), do'stlar 6 belgili kod yoki havola bilan qo'shiladi, boshlovchi
«Boshlash»ni bosadi. Hamma bir xil savolni bir vaqtda ko'radi: vaqt server soati bo'yicha
(har savol T soniya, keyin R soniya natija). Mijoz har soniyada holatni so'raydi (polling) —
bir nechta server jarayonida ham to'g'ri ishlaydi, WebSocket shart emas.

Ochko: to'g'ri javob 500 + tezlik uchun 0–500; birinchi to'g'ri topgan +200; ketma-ket to'g'ri +50.
"""
import random
import re
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException
from typing import Optional

from pydantic import BaseModel, Field

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
MAX_PLAYERS = 40
COUNTDOWN = 4          # boshlashdan oldin 3-2-1
REVEAL = 5             # natija ko'rsatiladigan soniyalar
ROOM_TTL = timedelta(hours=3)
QUESTION_TIMES = (10, 15, 20, 30)


def now():
    return datetime.now(timezone.utc)


def ms(dt):
    return int(dt.timestamp() * 1000)


def new_code():
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))


def norm_code(value):
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())[:6]


def options_of(row):
    opts = [str(row.get(f"option_{x}") or "").strip() for x in "abcd"]
    count = sum(1 for o in opts if o)
    if count < 2 or any(not o for o in opts[:count]):
        return []
    return opts[:count]


def phase_at(room, at, total):
    """Server soati bo'yicha: (phase, index, phase_ends_at). phase: lobby|countdown|question|reveal|finished."""
    if room["status"] == "lobby" or not room.get("started_at"):
        return "lobby", -1, None
    start = room["started_at"]
    if at < start:
        return "countdown", -1, start
    step = timedelta(seconds=room["savol_vaqti"] + REVEAL)
    elapsed = at - start
    index = int(elapsed / step)
    if index >= total:
        return "finished", total, None
    q_start = start + step * index
    q_end = q_start + timedelta(seconds=room["savol_vaqti"])
    if at < q_end:
        return "question", index, q_end
    return "reveal", index, q_start + step


def score_answer(correct, elapsed_ms, limit_s, first_correct, streak):
    if not correct:
        return 0
    limit_ms = max(1, int(limit_s * 1000))
    speed = max(0.0, 1.0 - min(elapsed_ms, limit_ms) / limit_ms)
    return 500 + round(500 * speed) + (200 if first_correct else 0) + (50 if streak >= 2 else 0)


def podium(players):
    """Reyting: ochko ko'p, teng bo'lsa — to'g'ri javob ko'p, keyin tezroq umumiy vaqt."""
    ordered = sorted(players, key=lambda p: (-int(p.get("ochko") or 0), -int(p.get("togri") or 0), int(p.get("vaqt_ms") or 0), str(p.get("ism") or "")))
    place, last = 0, None
    for i, p in enumerate(ordered, 1):
        key = (p.get("ochko"), p.get("togri"))
        if key != last:
            place, last = i, key
        p["orin"] = place
    return ordered


class CreateRoom(BaseModel):
    token: Optional[str] = None
    topic_codes: list[str] = Field(min_length=1, max_length=60)
    savol_soni: int = Field(default=10, ge=3, le=30)
    savol_vaqti: int = Field(default=20)
    nomi: Optional[str] = Field(default=None, max_length=120)


class JoinRoom(BaseModel):
    token: Optional[str] = None
    kod: str = Field(min_length=4, max_length=12)


class Answer(BaseModel):
    token: Optional[str] = None
    index: int = Field(ge=0, le=60)
    tanlangan: str = Field(min_length=1, max_length=1)


def migrate(cur):
    cur.execute("SELECT pg_advisory_xact_lock(hashtext('bellashuv-schema'))")
    cur.execute("""CREATE TABLE IF NOT EXISTS bellashuv_xonalar(
        id BIGSERIAL PRIMARY KEY,
        kod TEXT NOT NULL UNIQUE,
        host_user_id BIGINT NOT NULL,
        nomi TEXT NOT NULL DEFAULT '',
        topic_codes TEXT[] NOT NULL,
        savol_ids INTEGER[] NOT NULL,
        savol_vaqti SMALLINT NOT NULL DEFAULT 20,
        status TEXT NOT NULL DEFAULT 'lobby' CHECK(status IN ('lobby','running','finished')),
        started_at TIMESTAMPTZ,
        keyingi_kod TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '3 hours'
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bellashuv_ishtirokchilar(
        xona_id BIGINT NOT NULL REFERENCES bellashuv_xonalar(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL,
        ism TEXT NOT NULL,
        jins TEXT,
        qoshilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY(xona_id, user_id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bellashuv_javoblar(
        xona_id BIGINT NOT NULL REFERENCES bellashuv_xonalar(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL,
        savol_index SMALLINT NOT NULL,
        tanlangan TEXT NOT NULL,
        togri BOOLEAN NOT NULL,
        vaqt_ms INTEGER NOT NULL,
        ochko INTEGER NOT NULL DEFAULT 0,
        javob_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY(xona_id, user_id, savol_index)
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_bellashuv_javob_xona ON bellashuv_javoblar(xona_id, savol_index, javob_at)")


def create_router(platform):
    router = APIRouter()
    try:
        from . import curriculum_scope as scope
    except ImportError:
        from modules import curriculum_scope as scope
    ready = {"ok": False}

    def uid_of(token, authorization):
        return platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization))

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

    def room_by_code(cur, kod, lock=False):
        cur.execute("SELECT * FROM bellashuv_xonalar WHERE kod=%s" + (" FOR UPDATE" if lock else ""), (norm_code(kod),))
        room = cur.fetchone()
        if not room or room["expires_at"] < now():
            raise HTTPException(404, "Bellashuv topilmadi yoki vaqti tugagan. Kodni tekshiring.")
        return dict(room)

    def questions(cur, room):
        cur.execute("""SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, explanation
                       FROM generated_tests WHERE id=ANY(%s)""", (room["savol_ids"],))
        by_id = {r["id"]: dict(r) for r in cur.fetchall()}
        return [by_id[i] for i in room["savol_ids"] if i in by_id]

    def standings(cur, room, total, index, phase):
        cur.execute("""SELECT p.user_id, p.ism, p.jins,
                              COALESCE(SUM(j.ochko),0)::int AS ochko,
                              COUNT(j.*) FILTER (WHERE j.togri)::int AS togri,
                              COALESCE(SUM(j.vaqt_ms) FILTER (WHERE j.togri),0)::int AS vaqt_ms,
                              EXISTS(SELECT 1 FROM bellashuv_javoblar jj WHERE jj.xona_id=p.xona_id
                                     AND jj.user_id=p.user_id AND jj.savol_index=%s) AS javob_berdi
                       FROM bellashuv_ishtirokchilar p
                       LEFT JOIN bellashuv_javoblar j ON j.xona_id=p.xona_id AND j.user_id=p.user_id
                            AND (j.savol_index < %s OR %s)
                       WHERE p.xona_id=%s GROUP BY p.xona_id, p.user_id, p.ism, p.jins""",
                    (index, index, phase in ("reveal", "finished"), room["id"]))
        return podium([dict(r, javob_berdi=bool(r["javob_berdi"])) for r in cur.fetchall()])

    def finish_if_done(cur, room, phase):
        if phase == "finished" and room["status"] != "finished":
            cur.execute("UPDATE bellashuv_xonalar SET status='finished' WHERE id=%s AND status<>'finished'", (room["id"],))

    @router.post("/api/bellashuv/xona")
    def create_room(body: CreateRoom, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        codes = list(dict.fromkeys(str(c).strip() for c in body.topic_codes if str(c).strip()))
        limit = body.savol_vaqti if body.savol_vaqti in QUESTION_TIMES else 20
        conn, cur = open_db()
        try:
            try:
                codes = scope.authorized_codes(cur, user_id, codes)
            except PermissionError as exc:
                raise HTTPException(403, str(exc))
            cur.execute("""SELECT id, option_a, option_b, option_c, option_d, correct_answer FROM generated_tests
                           WHERE topic_code=ANY(%s) AND COALESCE(question_type,'single_choice')='single_choice'""", (codes,))
            pool = [r["id"] for r in cur.fetchall()
                    if options_of(r) and str(r.get("correct_answer") or "").strip().upper()[:1] in "ABCD"[:len(options_of(r))]
                    and str(r.get("correct_answer") or "").strip()]
            if len(pool) < 3:
                raise HTTPException(400, "Bu mavzuda bellashuv uchun savol yetarli emas (kamida 3 ta test kerak).")
            random.shuffle(pool)
            ids = pool[: body.savol_soni]
            name, _ = user_card(cur, user_id)
            for _ in range(8):
                kod = new_code()
                cur.execute("SELECT 1 FROM bellashuv_xonalar WHERE kod=%s", (kod,))
                if not cur.fetchone():
                    break
            cur.execute("""INSERT INTO bellashuv_xonalar(kod,host_user_id,nomi,topic_codes,savol_ids,savol_vaqti,expires_at)
                           VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (kod, user_id, (body.nomi or "").strip()[:120], codes, ids, limit, now() + ROOM_TTL))
            room_id = cur.fetchone()["id"]
            _, jins = user_card(cur, user_id)
            cur.execute("INSERT INTO bellashuv_ishtirokchilar(xona_id,user_id,ism,jins) VALUES(%s,%s,%s,%s)", (room_id, user_id, name, jins))
            conn.commit()
            return {"kod": kod, "savollar": len(ids), "savol_vaqti": limit}
        finally:
            cur.close()
            conn.close()

    @router.post("/api/bellashuv/qoshil")
    def join_room(body: JoinRoom, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        conn, cur = open_db()
        try:
            room = room_by_code(cur, body.kod, lock=True)
            cur.execute("SELECT 1 FROM bellashuv_ishtirokchilar WHERE xona_id=%s AND user_id=%s", (room["id"], user_id))
            if not cur.fetchone():
                if room["status"] != "lobby":
                    raise HTTPException(409, "Bellashuv allaqachon boshlangan. Keyingisiga qo'shiling!")
                cur.execute("SELECT COUNT(*) AS n FROM bellashuv_ishtirokchilar WHERE xona_id=%s", (room["id"],))
                if cur.fetchone()["n"] >= MAX_PLAYERS:
                    raise HTTPException(409, "Xona to'lgan")
                name, jins = user_card(cur, user_id)
                cur.execute("INSERT INTO bellashuv_ishtirokchilar(xona_id,user_id,ism,jins) VALUES(%s,%s,%s,%s)", (room["id"], user_id, name, jins))
            conn.commit()
            return {"kod": room["kod"]}
        finally:
            cur.close()
            conn.close()

    @router.post("/api/bellashuv/{kod}/boshlash")
    def start_room(kod: str, body: Optional[JoinRoom] = None, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token or (body.token if body else None), authorization)
        conn, cur = open_db()
        try:
            room = room_by_code(cur, kod, lock=True)
            if int(room["host_user_id"]) != int(user_id):
                raise HTTPException(403, "Faqat xonani ochgan boshlaydi")
            if room["status"] != "lobby":
                return {"ok": True}
            cur.execute("UPDATE bellashuv_xonalar SET status='running', started_at=%s WHERE id=%s",
                        (now() + timedelta(seconds=COUNTDOWN), room["id"]))
            conn.commit()
            return {"ok": True}
        finally:
            cur.close()
            conn.close()

    @router.post("/api/bellashuv/{kod}/javob")
    def answer(kod: str, body: Answer, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        at = now()
        conn, cur = open_db()
        try:
            room = room_by_code(cur, kod)
            qs = questions(cur, room)
            phase, index, _ = phase_at(room, at, len(qs))
            if phase != "question" or index != body.index:
                raise HTTPException(409, "Bu savolning vaqti tugadi")
            cur.execute("SELECT 1 FROM bellashuv_ishtirokchilar WHERE xona_id=%s AND user_id=%s", (room["id"], user_id))
            if not cur.fetchone():
                raise HTTPException(403, "Siz bu bellashuvda emassiz")
            q = qs[index]
            letter = body.tanlangan.upper()
            correct_letter = str(q["correct_answer"] or "").strip().upper()[:1]
            correct = letter == correct_letter
            q_start = room["started_at"] + timedelta(seconds=(room["savol_vaqti"] + REVEAL) * index)
            elapsed = max(0, ms(at) - ms(q_start))
            cur.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (f"bellashuv:{room['id']}:{index}",))
            cur.execute("SELECT 1 FROM bellashuv_javoblar WHERE xona_id=%s AND savol_index=%s AND togri", (room["id"], index))
            first = correct and not cur.fetchone()
            cur.execute("""SELECT savol_index, togri FROM bellashuv_javoblar WHERE xona_id=%s AND user_id=%s
                           ORDER BY savol_index DESC""", (room["id"], user_id))
            streak = 1 if correct else 0
            expected = index - 1
            for r in cur.fetchall():
                if not correct or r["savol_index"] != expected or not r["togri"]:
                    break
                streak += 1
                expected -= 1
            points = score_answer(correct, elapsed, room["savol_vaqti"], first, streak)
            cur.execute("""INSERT INTO bellashuv_javoblar(xona_id,user_id,savol_index,tanlangan,togri,vaqt_ms,ochko)
                           VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING ochko""",
                        (room["id"], user_id, index, letter, correct, elapsed, points))
            saved = cur.fetchone()
            conn.commit()
            if not saved:
                raise HTTPException(409, "Bu savolga javob berib bo'lgansiz")
            # To'g'ri/noto'g'ri darhol aytiladi (bolalarga muhim), to'g'ri harf esa natija vaqtida ochiladi.
            return {"togri": correct, "ochko": points, "birinchi": first, "ketma_ket": streak}
        finally:
            cur.close()
            conn.close()

    @router.get("/api/bellashuv/{kod}")
    def state(kod: str, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        at = now()
        conn, cur = open_db()
        try:
            room = room_by_code(cur, kod)
            qs = questions(cur, room)
            phase, index, ends = phase_at(room, at, len(qs))
            finish_if_done(cur, room, phase)
            players = standings(cur, room, len(qs), index, phase)
            me = next((p for p in players if int(p["user_id"]) == int(user_id)), None)
            out = {
                "kod": room["kod"], "nomi": room["nomi"], "phase": phase, "index": index, "total": len(qs),
                "savol_vaqti": room["savol_vaqti"], "server_now": ms(at), "phase_ends_at": ms(ends) if ends else None,
                "host": int(room["host_user_id"]) == int(user_id), "men": me, "ishtirokchi": me is not None,
                "players": [{k: p[k] for k in ("user_id", "ism", "jins", "ochko", "togri", "orin", "javob_berdi")} for p in players],
                "keyingi_kod": room.get("keyingi_kod"), "topic_codes": room["topic_codes"],
            }
            if phase in ("question", "reveal") and 0 <= index < len(qs):
                q = qs[index]
                out["savol"] = {"matn": q["question"], "variantlar": options_of(q)}
                cur.execute("SELECT tanlangan, togri, ochko FROM bellashuv_javoblar WHERE xona_id=%s AND user_id=%s AND savol_index=%s",
                            (room["id"], user_id, index))
                mine = cur.fetchone()
                out["mening_javobim"] = dict(mine) if mine else None
                cur.execute("SELECT COUNT(*) AS n FROM bellashuv_javoblar WHERE xona_id=%s AND savol_index=%s", (room["id"], index))
                out["javob_berganlar"] = int(cur.fetchone()["n"])
                if phase == "reveal":
                    cur.execute("""SELECT j.vaqt_ms, p.ism FROM bellashuv_javoblar j JOIN bellashuv_ishtirokchilar p
                                   ON p.xona_id=j.xona_id AND p.user_id=j.user_id
                                   WHERE j.xona_id=%s AND j.savol_index=%s AND j.togri ORDER BY j.javob_at LIMIT 1""", (room["id"], index))
                    fastest = cur.fetchone()
                    out["natija"] = {"togri": str(q["correct_answer"] or "").strip().upper()[:1], "izoh": q.get("explanation") or "",
                                     "birinchi": {"ism": fastest["ism"], "soniya": round(fastest["vaqt_ms"] / 1000, 1)} if fastest else None}
            conn.commit()
            return out
        finally:
            cur.close()
            conn.close()

    @router.post("/api/bellashuv/{kod}/yana")
    def rematch(kod: str, body: Optional[JoinRoom] = None, token: str = None, authorization: str = Header(None)):
        """Boshlovchi «Yana o'ynaymiz» — shu mavzulardan yangi xona; qolganlar holatda keyingi_kod ni ko'radi."""
        user_id = uid_of(token or (body.token if body else None), authorization)
        conn, cur = open_db()
        try:
            room = room_by_code(cur, kod, lock=True)
            if int(room["host_user_id"]) != int(user_id):
                raise HTTPException(403, "Faqat xonani ochgan yangi o'yin boshlaydi")
            if room.get("keyingi_kod"):
                return {"kod": room["keyingi_kod"]}
        finally:
            cur.close()
            conn.close()
        created = create_room(CreateRoom(token=token or (body.token if body else None), topic_codes=room["topic_codes"],
                                         savol_soni=len(room["savol_ids"]) or 10, savol_vaqti=room["savol_vaqti"], nomi=room["nomi"]),
                              authorization)
        conn, cur = open_db()
        try:
            cur.execute("UPDATE bellashuv_xonalar SET keyingi_kod=%s WHERE id=%s", (created["kod"], room["id"]))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        return created

    return router

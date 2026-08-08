"""O'yinlashtirilgan testlar V18.

Savolning to'g'ri javobi, urinishlar, yordamlar va ochko server tomonidan
boshqariladi. Frontend faqat sessiya kaliti va foydalanuvchi javobini yuboradi.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import secrets
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Callable, Optional

import psycopg2.extras
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


GAME_MODES = {"bridge", "millionaire", "space", "detective", "city"}
GAME_QUESTION_COUNTS = {5, 10, 15, 20, 25}
MAX_TOPIC_CODES = 50
TASHKENT_TODAY_SQL = "(NOW() AT TIME ZONE 'Asia/Tashkent')::date"
MIN_GAME_TIME_SECONDS = 20
MAX_GAME_TIME_SECONDS = 180
DIFFICULTY_TIME_DEFAULTS = {
    "oson": 60,
    "o'rta": 75,
    "orta": 75,
    "qiyin": 90,
    "murakkab": 120,
}


def grade_band_for_value(value: object) -> str:
    """DTS sinfi yoki maxsus guruh nomini to'rtta yosh bosqichiga ajratadi."""
    text = str(value or "").strip().lower().replace("-sinf", "")
    match = re.search(r"(?:^|\D)(\d{1,2})(?:\D|$)", text)
    if not match:
        return "applicant"
    grade = int(match.group(1))
    if 1 <= grade <= 4:
        return "grade_1_4"
    if 5 <= grade <= 9:
        return "grade_5_9"
    if 10 <= grade <= 11:
        return "grade_10_11"
    return "applicant"


def is_applicant_value(value: object) -> bool:
    text = str(value or "").strip().casefold()
    return any(marker in text for marker in ("abitur", "applicant"))


def boss_attempt_limit(grade_band: str) -> int:
    return 3 if normalize_grade_band(grade_band) in {"grade_1_4", "grade_5_9"} else 2


def normalize_grade_band(grade_band: object) -> str:
    """016 dan oldingi yosh kalitlarini yangi 1–4/5–9 kalitlariga moslaydi."""
    value = str(grade_band or "").strip()
    return {
        "grade_1_5": "grade_1_4",
        "grade_6_9": "grade_5_9",
    }.get(value, value if value in {"grade_1_4", "grade_5_9", "grade_10_11"} else "applicant")


def initial_lives_for_band(grade_band: str) -> int:
    """1–9-sinflarga uchta, katta sinf va abituriyentga ikkita jon."""
    return 3 if normalize_grade_band(grade_band) in {"grade_1_4", "grade_5_9"} else 2


def bounded_question_time_limit(source_time: object, difficulty: object, is_boss: bool = False) -> int:
    """Savol bankidagi vaqtni ishonchli oraliqqa qisadi, yo'q bo'lsa darajadan oladi."""
    parsed = None
    if not isinstance(source_time, bool):
        try:
            if isinstance(source_time, str) and not re.fullmatch(
                r"[0-9]+(?:[.][0-9]+)?", source_time.strip()
            ):
                raise InvalidOperation
            candidate = Decimal(str(source_time).strip())
            if candidate.is_finite() and candidate > 0:
                parsed = (
                    MAX_GAME_TIME_SECONDS
                    if candidate >= MAX_GAME_TIME_SECONDS
                    else int(candidate.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                )
        except (InvalidOperation, TypeError, ValueError):
            parsed = None
    if parsed is None:
        key = str(difficulty or "").strip().casefold().replace("’", "'").replace("`", "'")
        parsed = DIFFICULTY_TIME_DEFAULTS.get(key, DIFFICULTY_TIME_DEFAULTS["o'rta"])
        if is_boss:
            parsed += 30
    return max(MIN_GAME_TIME_SECONDS, min(MAX_GAME_TIME_SECONDS, int(parsed)))


def timeout_transition(
    *,
    is_boss: bool,
    attempts_used: int,
    max_attempts: int,
    lives_remaining: int,
) -> dict:
    """DB yozuvidan oldingi sof timeout qoidasi; client vaqti bu yerga kirmaydi."""
    next_attempt = max(0, int(attempts_used)) + 1
    if is_boss:
        if next_attempt < max(1, int(max_attempts)):
            return {
                "outcome": "boss_retry",
                "attempts_used": next_attempt,
                "attempts_left": int(max_attempts) - next_attempt,
                "lives_remaining": max(0, int(lives_remaining)),
            }
        return {
            "outcome": "game_over_boss",
            "attempts_used": next_attempt,
            "attempts_left": 0,
            "lives_remaining": max(0, int(lives_remaining)),
        }
    lives_after = max(0, int(lives_remaining) - 1)
    return {
        "outcome": "game_over_lives" if lives_after == 0 else "advance",
        "attempts_used": 1,
        "attempts_left": 0,
        "lives_remaining": lives_after,
    }


def is_terminal_boss_failure(
    *, is_boss: bool, correct: bool, attempts_used: int, max_attempts: int
) -> bool:
    return bool(
        is_boss
        and not correct
        and int(attempts_used) >= max(1, int(max_attempts))
    )


def score_game_rows(rows: list[dict], completed: bool, lifelines_used: int = 0) -> dict:
    """Har qanday raund sonini 0..1000 yagona natijaga normallashtiradi."""
    total = len(rows)
    rounds = max(1, total // 5)
    regular = [row for row in rows if not row.get("is_boss")]
    bosses = [row for row in rows if row.get("is_boss")]
    regular_correct = sum(1 for row in regular if row.get("correct") is True)

    regular_points = round(500 * regular_correct / max(1, len(regular)))
    boss_value = 0.0
    for row in bosses:
        if row.get("correct") is not True:
            continue
        attempts = max(1, int(row.get("attempts_used") or 1))
        boss_value += 1.0 if attempts == 1 else (2 / 3 if attempts == 2 else 1 / 3)
    boss_points = round(300 * boss_value / max(1, len(bosses)))

    finalized = sum(1 for row in rows if row.get("answered_at") is not None)
    completion_points = 100 if completed and finalized == total else 0
    perfect = bool(
        completed
        and total > 0
        and all(row.get("correct") is True for row in rows)
        and all(int(row.get("attempts_used") or 0) == 1 for row in rows)
        and lifelines_used == 0
    )
    mastery_bonus = 100 if perfect else 0
    score = min(1000, regular_points + boss_points + completion_points + mastery_bonus)
    correct_count = sum(1 for row in rows if row.get("correct") is True)
    return {
        "score_1000": score,
        "percent": round(correct_count * 100 / total) if total else 0,
        "correct_count": correct_count,
        "total": total,
        "regular_points": regular_points,
        "boss_points": boss_points,
        "completion_points": completion_points,
        "mastery_bonus": mastery_bonus,
        "perfect": perfect,
        "rounds": rounds,
    }


def _content_key(mode: str, topic_codes: list[str], question_count: int) -> str:
    canonical = f"{mode}|{question_count}|{'|'.join(sorted(set(topic_codes)))}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _clean_topic_codes(values: list[object]) -> list[str]:
    result = []
    seen = set()
    for value in values or []:
        code = str(value or "").strip()
        if len(code) > 200:
            raise HTTPException(status_code=400, detail="Mavzu kodi juda uzun")
        if code and code not in seen:
            seen.add(code)
            result.append(code)
    if not result:
        raise HTTPException(status_code=400, detail="Kamida bitta mavzu tanlang")
    if len(result) > MAX_TOPIC_CODES:
        raise HTTPException(status_code=400, detail="Bir o'yinda ko'pi bilan 50 ta mavzu tanlanadi")
    return result


def _game_tables_ready(cur) -> bool:
    cur.execute("SELECT to_regclass('public.game_profiles') AS table_name")
    row = cur.fetchone()
    return bool(row and row["table_name"])


def _require_game_tables(cur) -> None:
    if not _game_tables_ready(cur):
        raise HTTPException(
            status_code=503,
            detail="O'yinli testlar bazasi o'rnatilmagan. Avval 015 migratsiyasini bajaring.",
        )
    cur.execute(
        """SELECT EXISTS(
               SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name='game_sessions'
                 AND column_name='lives_remaining'
             ) AS timer_ready"""
    )
    if not cur.fetchone()["timer_ready"]:
        raise HTTPException(
            status_code=503,
            detail="Server taymeri bazasi o'rnatilmagan. Avval 016 migratsiyasini bajaring.",
        )


def _ensure_profile(cur, user_id: int) -> None:
    cur.execute(
        "INSERT INTO game_profiles(user_id) VALUES(%s) ON CONFLICT (user_id) DO NOTHING",
        (user_id,),
    )


def _profile_payload(cur, user_id: int) -> dict:
    _ensure_profile(cur, user_id)
    cur.execute(
        """SELECT total_points,current_streak,longest_streak,games_completed,
                  last_login_date,last_play_date
           FROM game_profiles WHERE user_id=%s""",
        (user_id,),
    )
    row = cur.fetchone()
    total_points = int(row["total_points"] or 0)
    level = total_points // 250 + 1
    return {
        "total_points": total_points,
        "level": level,
        "level_progress": total_points % 250,
        "level_target": 250,
        "current_streak": int(row["current_streak"] or 0),
        "longest_streak": int(row["longest_streak"] or 0),
        "games_completed": int(row["games_completed"] or 0),
        "last_login_date": row["last_login_date"],
        "last_play_date": row["last_play_date"],
    }


def _ledger_award(
    cur,
    user_id: int,
    amount: int,
    reason: str,
    reference_key: str,
    metadata: Optional[dict] = None,
) -> int:
    if amount <= 0:
        return 0
    _ensure_profile(cur, user_id)
    cur.execute(
        """INSERT INTO game_point_ledger(user_id,amount,reason,reference_key,metadata)
           VALUES(%s,%s,%s,%s,%s::jsonb)
           ON CONFLICT (user_id,reference_key) DO NOTHING
           RETURNING amount""",
        (user_id, amount, reason, reference_key, json.dumps(metadata or {}, ensure_ascii=False)),
    )
    inserted = cur.fetchone()
    if not inserted:
        return 0
    awarded = int(inserted["amount"])
    cur.execute(
        "UPDATE game_profiles SET total_points=total_points+%s,updated_at=NOW() WHERE user_id=%s",
        (awarded, user_id),
    )
    return awarded


def _first_test_today_award(cur, user_id: int, source: str) -> int:
    cur.execute(f"SELECT {TASHKENT_TODAY_SQL} AS today")
    today = cur.fetchone()["today"]
    return _ledger_award(
        cur,
        user_id,
        20,
        "first_test_daily",
        f"first-test:{today.isoformat()}",
        {"source": source, "date": today.isoformat()},
    )


def _best_score_award(
    cur,
    *,
    user_id: int,
    mode: str,
    content_key: str,
    score_1000: int,
    percent: int,
    reference_key: str,
) -> int:
    # Birinchi natijada SELECT ... FOR UPDATE hali mavjud bo'lmagan qatorni
    # qulflay olmaydi. Avval 0-lik qatorni atomar yaratib, keyin aynan shu
    # qatorni qulflaymiz — parallel yakunlar faqat yaxshilangan farqni oladi.
    cur.execute(
        """INSERT INTO game_best_scores(
               user_id,mode,content_key,best_score_1000,best_percent,updated_at
             ) VALUES(%s,%s,%s,0,0,NOW())
             ON CONFLICT (user_id,mode,content_key) DO NOTHING""",
        (user_id, mode, content_key),
    )
    cur.execute(
        """SELECT best_score_1000 FROM game_best_scores
           WHERE user_id=%s AND mode=%s AND content_key=%s FOR UPDATE""",
        (user_id, mode, content_key),
    )
    previous = cur.fetchone()
    previous_score = int(previous["best_score_1000"] or 0)
    if score_1000 > previous_score:
        cur.execute(
            """UPDATE game_best_scores
               SET best_score_1000=%s,best_percent=%s,updated_at=NOW()
               WHERE user_id=%s AND mode=%s AND content_key=%s
                 AND best_score_1000 < %s""",
            (score_1000, percent, user_id, mode, content_key, score_1000),
        )
    improvement_xp = max(0, round(score_1000 / 10) - round(previous_score / 10))
    return _ledger_award(
        cur,
        user_id,
        improvement_xp,
        "best_improvement",
        reference_key,
        {
            "mode": mode,
            "previous_score_1000": previous_score,
            "new_score_1000": score_1000,
        },
    )


def award_standard_test_points(
    cur,
    *,
    user_id: int,
    topic_codes: list[str],
    question_count: int,
    answered_count: int,
    percent: int,
    attempt_id: Optional[str],
    server_content_key: Optional[str] = None,
) -> dict:
    """Server bergan oddiy test urinishiga V18 ochkosini beradi."""
    if not _game_tables_ready(cur):
        return {"awarded_points": 0, "profile": None}
    _ensure_profile(cur, user_id)
    completed = question_count > 0 and answered_count >= question_count
    score_1000 = min(1000, round(max(0, min(100, percent)) * 9) + (100 if completed else 0))
    if not server_content_key or not attempt_id:
        return {
            "score_1000": score_1000,
            "awarded_points": 0,
            "best_improvement_points": 0,
            "daily_first_test_points": 0,
            "profile": _profile_payload(cur, user_id),
        }
    awarded = _best_score_award(
        cur,
        user_id=user_id,
        mode="standard",
        content_key=server_content_key,
        score_1000=score_1000,
        percent=percent,
        reference_key=f"standard-best:{attempt_id}",
    )
    daily = 0
    if completed:
        daily = _first_test_today_award(cur, user_id, "standard")
        cur.execute(
            f"""UPDATE game_profiles SET games_completed=games_completed+1,
                       last_play_date={TASHKENT_TODAY_SQL},updated_at=NOW()
                WHERE user_id=%s""",
            (user_id,),
        )
    return {
        "score_1000": score_1000,
        "awarded_points": awarded + daily,
        "best_improvement_points": awarded,
        "daily_first_test_points": daily,
        "profile": _profile_payload(cur, user_id),
    }


class DailyLoginRequest(BaseModel):
    token: str


class GameStartRequest(BaseModel):
    token: str
    topic_codes: list[str] = Field(default_factory=list)
    question_count: int = 10
    game_mode: str = "bridge"


class GameAvailabilityRequest(BaseModel):
    token: str
    topic_codes: list[str] = Field(default_factory=list)


class GameAnswerRequest(BaseModel):
    token: str
    session_id: str = Field(min_length=8, max_length=128)
    question_key: str = Field(min_length=8, max_length=128)
    action_id: str = Field(min_length=8, max_length=128)
    answer: str = ""


class GameLifelineRequest(BaseModel):
    token: str
    session_id: str = Field(min_length=8, max_length=128)
    question_key: str = Field(min_length=8, max_length=128)
    action_id: str = Field(min_length=8, max_length=128)
    lifeline: str


class GameReadyRequest(BaseModel):
    token: str
    session_id: str = Field(min_length=8, max_length=128)
    question_key: str = Field(min_length=8, max_length=128)
    action_id: str = Field(min_length=8, max_length=128)


class GameTimeoutRequest(BaseModel):
    token: str
    session_id: str = Field(min_length=8, max_length=128)
    question_key: str = Field(min_length=8, max_length=128)
    action_id: str = Field(min_length=8, max_length=128)


class GameFinishRequest(BaseModel):
    token: str
    session_id: str = Field(min_length=8, max_length=128)


def create_test_games_router(
    jwt_verify: Callable[[str], int],
    db_factory: Callable,
    written_answer_checker: Callable[[str, str], bool],
    correct_letter_resolver: Callable,
    text_cleaner: Callable[[str], str],
) -> APIRouter:
    router = APIRouter(prefix="/api/oyin", tags=["O'yinli test V18"])

    def get_session_for_update(cur, session_id: str, user_id: int):
        cur.execute(
            "SELECT * FROM game_sessions WHERE session_id=%s AND user_id=%s FOR UPDATE",
            (session_id, user_id),
        )
        session = cur.fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="O'yin sessiyasi topilmadi")
        return session

    def get_current_row(cur, session: dict, for_update: bool = False):
        if int(session["current_position"]) > int(session["total_questions"]):
            return None
        lock = " FOR UPDATE" if for_update else ""
        cur.execute(
            f"""SELECT sq.*
                FROM game_session_questions sq
                WHERE sq.session_id=%s AND sq.position=%s{lock}""",
            (session["session_id"], session["current_position"]),
        )
        return cur.fetchone()

    def snapshot(row: dict) -> dict:
        value = row.get("question_snapshot") or {}
        return json.loads(value) if isinstance(value, str) else value

    def timer_limit_for_row(row: dict) -> int:
        data = snapshot(row)
        stored = row.get("time_limit_seconds")
        return bounded_question_time_limit(
            stored if stored is not None else data.get("time_limit"),
            data.get("difficulty"),
            bool(row.get("is_boss")),
        )

    def question_timer_payload(cur, row: dict) -> dict:
        """DB soatini qaytaradi; deadline yo'q bo'lsa uni yashirincha boshlamaydi."""
        seconds = timer_limit_for_row(row)
        cur.execute(
            """WITH updated AS (
                 UPDATE game_session_questions
                 SET time_limit_seconds=%s
                 WHERE session_id=%s AND position=%s
                 RETURNING time_limit_seconds,timer_started_at,deadline_at
               ), timed AS (
                 SELECT updated.*,clock_timestamp() AS server_now FROM updated
               )
               SELECT time_limit_seconds,timer_started_at,deadline_at,server_now,
                      CASE
                        WHEN deadline_at IS NULL THEN time_limit_seconds
                        ELSE GREATEST(
                          0,CEIL(EXTRACT(EPOCH FROM (deadline_at-server_now)))
                        )::INTEGER
                      END AS remaining_seconds,
                      CASE
                        WHEN deadline_at IS NULL THEN 'waiting'
                        WHEN deadline_at <= server_now THEN 'expired'
                        ELSE 'active'
                      END AS timer_status
               FROM timed""",
            (seconds, row["session_id"], row["position"]),
        )
        timer = cur.fetchone()
        row["time_limit_seconds"] = timer["time_limit_seconds"]
        row["timer_started_at"] = timer["timer_started_at"]
        row["deadline_at"] = timer["deadline_at"]
        api_started_at = (
            timer["timer_started_at"].isoformat()
            if timer["timer_started_at"] is not None
            else None
        )
        api_deadline_at = (
            timer["deadline_at"].isoformat()
            if timer["deadline_at"] is not None
            else None
        )
        api_server_now = timer["server_now"].isoformat()
        return {
            "time_limit_seconds": int(timer["time_limit_seconds"]),
            "timer_status": timer["timer_status"],
            "timer_started_at": api_started_at,
            "deadline_at": api_deadline_at,
            "server_now": api_server_now,
            "remaining_seconds": int(timer["remaining_seconds"]),
        }

    def activate_question_timer(cur, row: dict) -> dict:
        """Faqat waiting savolni boshlaydi; boshqa ready action deadline'ni uzaytirmaydi."""
        seconds = timer_limit_for_row(row)
        cur.execute(
            """UPDATE game_session_questions
               SET time_limit_seconds=%s,
                   timer_started_at=COALESCE(timer_started_at,clock_timestamp()),
                   deadline_at=COALESCE(
                     deadline_at,clock_timestamp() + (%s * INTERVAL '1 second')
                   )
               WHERE session_id=%s AND position=%s
               RETURNING *""",
            (seconds, seconds, row["session_id"], row["position"]),
        )
        activated = cur.fetchone()
        row.update(activated)
        return question_timer_payload(cur, row)

    def reset_question_timer(cur, row: dict) -> None:
        """Bossning yangi urinishini UI ko'rsatmaguncha waiting holatida qoldiradi."""
        cur.execute(
            """UPDATE game_session_questions
               SET timer_started_at=NULL,deadline_at=NULL
               WHERE session_id=%s AND position=%s""",
            (row["session_id"], row["position"]),
        )
        row["timer_started_at"] = None
        row["deadline_at"] = None

    def require_active_timer(cur, row: dict) -> dict:
        timer = question_timer_payload(cur, row)
        if timer["timer_status"] == "waiting":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "QUESTION_NOT_READY",
                    "message": "Savol taymeri hali boshlanmagan",
                    **timer,
                },
            )
        if timer["timer_status"] == "expired":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "QUESTION_TIME_EXPIRED",
                    "message": "Savol vaqti tugagan",
                    **timer,
                },
            )
        return timer

    def action_replay(cur, *, session_id: str, user_id: int, action_id: str, action_type: str, payload: dict):
        if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", action_id or ""):
            raise HTTPException(status_code=400, detail="Harakat identifikatori noto'g'ri")
        request_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        cur.execute(
            """SELECT action_type,request_hash,response FROM game_actions
               WHERE session_id=%s AND action_id=%s AND user_id=%s""",
            (session_id, action_id, user_id),
        )
        previous = cur.fetchone()
        if not previous:
            return None, request_hash
        if previous["action_type"] != action_type or previous["request_hash"] != request_hash:
            raise HTTPException(status_code=409, detail="Harakat identifikatori boshqa so'rovda ishlatilgan")
        return previous["response"], request_hash

    def save_action(cur, *, session_id: str, user_id: int, action_id: str, action_type: str, request_hash: str, response: dict):
        cur.execute(
            """INSERT INTO game_actions(
                 session_id,user_id,action_id,action_type,request_hash,response
               ) VALUES(%s,%s,%s,%s,%s,%s::jsonb)""",
            (
                session_id,
                user_id,
                action_id,
                action_type,
                request_hash,
                json.dumps(response, ensure_ascii=False, default=str),
            ),
        )

    def display_correct_letter(row: dict) -> Optional[str]:
        data = snapshot(row)
        original = correct_letter_resolver(
            data.get("option_a"), data.get("option_b"), data.get("option_c"), data.get("option_d"), data.get("correct_answer")
        )
        option_map = row.get("option_map") or {}
        for display, source in option_map.items():
            if source == original:
                return display
        return None

    def correct_text(row: dict) -> str:
        data = snapshot(row)
        if row["display_type"] == "boss_converted":
            original = correct_letter_resolver(
                data.get("option_a"), data.get("option_b"), data.get("option_c"), data.get("option_d"), data.get("correct_answer")
            )
            value = data.get(f"option_{str(original or '').lower()}") if original else data.get("correct_answer")
            return text_cleaner(value or "")
        return text_cleaner(data.get("correct_answer") or "")

    def question_payload(cur, session: dict, row: Optional[dict] = None) -> Optional[dict]:
        row = row or get_current_row(cur, session)
        if not row:
            return None
        data = snapshot(row)
        hidden = set(row.get("hidden_options") or [])
        options = []
        if row["display_type"] == "choice":
            option_map = row.get("option_map") or {}
            for display in ("A", "B", "C", "D"):
                source = option_map.get(display)
                if not source:
                    continue
                options.append({
                    "key": display,
                    "text": data.get(f"option_{source.lower()}") or "",
                    "hidden": display in hidden,
                })
        position = int(row["position"])
        max_attempts = int(row["max_attempts"] or 1)
        attempts_used = int(row["attempts_used"] or 0)
        timer = question_timer_payload(cur, row)
        return {
            "question_key": row["question_key"],
            "position": position,
            "total": int(session["total_questions"]),
            "round": (position - 1) // 5 + 1,
            "round_step": (position - 1) % 5 + 1,
            "is_boss": bool(row["is_boss"]),
            "question_type": "write_answer" if row["is_boss"] else "single_choice",
            "question": data.get("question") or "",
            "options": options,
            "is_latex": bool(data.get("is_latex")),
            "rasm_id": data.get("rasm_id"),
            "difficulty": data.get("difficulty"),
            # time_limit eski frontend bilan moslik uchun saqlanadi, lekin u
            # ham endi server chegaralagan authoritative qiymatdir.
            "time_limit": timer["time_limit_seconds"],
            **timer,
            "max_attempts": max_attempts,
            "attempts_used": attempts_used,
            "attempts_left": max(0, max_attempts - attempts_used),
            "lifeline_used": row.get("lifeline_used"),
            "can_use_lifeline": session["game_mode"] == "millionaire" and not bool(row["is_boss"]),
        }

    def session_summary(cur, session: dict) -> dict:
        used = list(session.get("lifelines_used") or [])
        grade_band = normalize_grade_band(session["grade_band"])
        initial_lives = int(session.get("initial_lives") or initial_lives_for_band(grade_band))
        lives_remaining = int(
            session.get("lives_remaining")
            if session.get("lives_remaining") is not None
            else initial_lives
        )
        return {
            "session_id": session["session_id"],
            "game_mode": session["game_mode"],
            "grade_band": grade_band,
            "status": session["status"],
            "current_position": int(session["current_position"]),
            "total_questions": int(session["total_questions"]),
            "correct_count": int(session["correct_count"] or 0),
            "initial_lives": initial_lives,
            "lives_remaining": lives_remaining,
            "lifelines": {
                "fifty_fifty": "fifty_fifty" not in used,
                "remove_one": "remove_one" not in used,
            },
            "question": question_payload(cur, session) if session["status"] == "active" else None,
            "result": session.get("result"),
        }

    def sync_learning(cur, user_id: int, session_id: str, update_mastery: bool, hints_used: int = 0) -> None:
        cur.execute(
            """SELECT sq.question_id,sq.topic_code,sq.correct,sq.is_boss,
                      sq.question_snapshot
               FROM game_session_questions sq
               WHERE sq.session_id=%s AND sq.answered_at IS NOT NULL""",
            (session_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return
        for row in rows:
            data = snapshot(row)
            row["difficulty"] = data.get("difficulty")
            row["question_type"] = "write_answer" if row["is_boss"] else "single_choice"
        grouped = defaultdict(lambda: {"correct": 0, "total": 0})
        for row in rows:
            grouped[row["topic_code"]]["total"] += 1
            if row["correct"]:
                grouped[row["topic_code"]]["correct"] += 1
        analytics_ready = False
        platform_context_id = None
        if update_mastery:
            cur.execute("SELECT to_regclass('public.learning_events') AS table_name")
            analytics_ready = bool(cur.fetchone()["table_name"])
            if analytics_ready:
                cur.execute("SELECT set_config('app.analytics_direct_write','on',TRUE)")
                cur.execute(
                    """SELECT id FROM learning_contexts
                       WHERE external_type='platform' AND external_id=1 AND active=TRUE
                       LIMIT 1"""
                )
                context_row = cur.fetchone()
                platform_context_id = context_row["id"] if context_row else None
                if platform_context_id:
                    cur.execute(
                        """INSERT INTO context_memberships(
                             context_id,user_id,member_role,status,source
                           ) VALUES(%s,%s,'student','active','game_test_v18')
                           ON CONFLICT DO NOTHING""",
                        (platform_context_id, user_id),
                    )
            for topic_code, item in grouped.items():
                percent = round(item["correct"] * 100 / item["total"])
                cur.execute(
                    """INSERT INTO learned_topics(user_id,topic_code,score,repeat_count,learned_at,next_repeat)
                       VALUES(%s,%s,%s,1,NOW(),CURRENT_DATE+INTERVAL '7 days')
                       ON CONFLICT (user_id,topic_code) DO UPDATE SET
                         score=EXCLUDED.score,
                         repeat_count=learned_topics.repeat_count+1,
                         learned_at=NOW(),next_repeat=CURRENT_DATE+INTERVAL '7 days'""",
                    (user_id, topic_code, percent),
                )
                if analytics_ready and platform_context_id:
                    cur.execute(
                        """INSERT INTO learning_events(
                             user_id,actor_user_id,context_id,event_type,source_type,
                             channel,evidence_source,topic_code,score_percent,
                             correct_count,total_count,hints_used,status,affects_mastery,
                             idempotency_key,payload
                           ) VALUES(
                             %s,%s,%s,'test_attempt','independent','web','self',%s,%s,
                             %s,%s,%s,%s,TRUE,%s,%s::jsonb
                           ) ON CONFLICT DO NOTHING""",
                        (
                            user_id,
                            user_id,
                            platform_context_id,
                            topic_code,
                            percent,
                            item["correct"],
                            item["total"],
                            max(0, hints_used),
                            "passed" if percent >= 60 else "failed",
                            f"game:{session_id}:{topic_code}",
                            json.dumps(
                                {
                                    "delivery_mode": "game",
                                    "session_id": session_id,
                                    "ruleset_version": "v18",
                                },
                                ensure_ascii=False,
                            ),
                        ),
                    )
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO savol_javob_tarixi
                 (user_id,savol_id,topic_code,difficulty,question_type,togri_mi)
               VALUES %s""",
            [
                (
                    user_id,
                    row["question_id"],
                    row["topic_code"],
                    row["difficulty"],
                    row["question_type"],
                    bool(row["correct"]),
                )
                for row in rows
            ],
        )

    def finish_locked(
        cur,
        session: dict,
        completed: bool,
        *,
        terminal_status: Optional[str] = None,
        terminal_reason: Optional[str] = None,
    ) -> dict:
        if session["status"] in {"completed", "abandoned", "game_over"} and session.get("result"):
            return session["result"]
        cur.execute(
            """SELECT is_boss,correct,attempts_used,answered_at
               FROM game_session_questions WHERE session_id=%s ORDER BY position""",
            (session["session_id"],),
        )
        rows = cur.fetchall()
        used_count = len(session.get("lifelines_used") or [])
        score = score_game_rows(rows, completed=completed, lifelines_used=used_count)
        awarded_best = 0
        daily_first = 0
        if completed:
            awarded_best = _best_score_award(
                cur,
                user_id=session["user_id"],
                mode=session["game_mode"],
                content_key=session["content_key"],
                score_1000=score["score_1000"],
                percent=score["percent"],
                reference_key=f"game-best:{session['session_id']}",
            )
            daily_first = _first_test_today_award(cur, session["user_id"], "game")
            cur.execute(
                f"""UPDATE game_profiles SET games_completed=games_completed+1,
                          last_play_date={TASHKENT_TODAY_SQL},updated_at=NOW()
                   WHERE user_id=%s""",
                (session["user_id"],),
            )
        sync_learning(
            cur,
            session["user_id"],
            session["session_id"],
            update_mastery=completed,
            hints_used=used_count,
        )
        result = {
            **score,
            "completed": completed,
            "mastery_updated": completed,
            "game_mode": session["game_mode"],
            "status": "completed" if completed else (terminal_status or "abandoned"),
            "terminal_reason": terminal_reason,
            "initial_lives": int(
                session.get("initial_lives") or initial_lives_for_band(session["grade_band"])
            ),
            "lives_remaining": int(
                session.get("lives_remaining")
                if session.get("lives_remaining") is not None
                else initial_lives_for_band(session["grade_band"])
            ),
            "awarded_points": awarded_best + daily_first,
            "best_improvement_points": awarded_best,
            "daily_first_test_points": daily_first,
            "profile": _profile_payload(cur, session["user_id"]),
        }
        cur.execute(
            """UPDATE game_sessions SET status=%s,finished_at=NOW(),score_1000=%s,
                      awarded_points=%s,result=%s::jsonb,updated_at=NOW()
               WHERE session_id=%s""",
            (
                "completed" if completed else (terminal_status or "abandoned"),
                score["score_1000"],
                result["awarded_points"],
                json.dumps(result, ensure_ascii=False, default=str),
                session["session_id"],
            ),
        )
        return result

    @router.get("/profil")
    def game_profile(token: str):
        user_id = jwt_verify(token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            profile = _profile_payload(cur, user_id)
            conn.commit()
            return {"profile": profile}
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.post("/kunlik-kirish")
    def daily_login(request: DailyLoginRequest):
        user_id = jwt_verify(request.token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            _ensure_profile(cur, user_id)
            cur.execute(
                f"""SELECT total_points,current_streak,longest_streak,last_login_date,
                           {TASHKENT_TODAY_SQL} AS today
                    FROM game_profiles WHERE user_id=%s FOR UPDATE""",
                (user_id,),
            )
            row = cur.fetchone()
            today = row["today"]
            awarded = 0
            new_day = row["last_login_date"] != today
            if new_day:
                consecutive = bool(row["last_login_date"] and (today - row["last_login_date"]).days == 1)
                streak = int(row["current_streak"] or 0) + 1 if consecutive else 1
                cur.execute(
                    """UPDATE game_profiles SET current_streak=%s,
                              longest_streak=GREATEST(longest_streak,%s),
                              last_login_date=%s,updated_at=NOW()
                       WHERE user_id=%s""",
                    (streak, streak, today, user_id),
                )
                awarded += _ledger_award(
                    cur, user_id, 10, "daily_login", f"daily-login:{today.isoformat()}",
                    {"date": today.isoformat(), "streak": streak},
                )
                if streak % 7 == 0:
                    awarded += _ledger_award(
                        cur, user_id, 25, "streak_bonus", f"streak-bonus:{today.isoformat()}",
                        {"date": today.isoformat(), "streak": streak},
                    )
            profile = _profile_payload(cur, user_id)
            conn.commit()
            return {"awarded_points": awarded, "new_day": new_day, "profile": profile}
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.post("/mavjudligi")
    def game_availability(request: GameAvailabilityRequest):
        user_id = jwt_verify(request.token)
        topic_codes = _clean_topic_codes(request.topic_codes)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            cur.execute(
                """SELECT topic_code,grade,subject_code FROM dts_tree
                   WHERE topic_code=ANY(%s) AND is_deleted=FALSE""",
                (topic_codes,),
            )
            dts_rows = cur.fetchall()
            found = {row["topic_code"] for row in dts_rows}
            if any(code not in found for code in topic_codes):
                raise HTTPException(status_code=400, detail="Tanlangan mavzu kodlaridan biri DTS bazasida yo'q")
            canonical_subjects = set()
            bands = set()
            for row in dts_rows:
                parts = str(row["topic_code"] or "").split("-")
                subject_code = row["subject_code"] or (parts[1] if len(parts) > 1 else "")
                canonical_subjects.add(f"{row['grade']}|{subject_code}")
                bands.add(grade_band_for_value(row["grade"]))
            if len(canonical_subjects) != 1 or len(bands) != 1:
                raise HTTPException(status_code=400, detail="O'yin uchun bitta sinf va bitta fan mavzularini tanlang")
            cur.execute(
                """SELECT question,option_a,option_b,option_c,option_d,
                          correct_answer,question_type
                   FROM generated_tests WHERE topic_code=ANY(%s)""",
                (topic_codes,),
            )
            choice_count = 0
            write_count = 0
            for candidate in cur.fetchall():
                if not text_cleaner(candidate["question"] or "").strip():
                    continue
                if candidate["question_type"] == "write_answer":
                    if text_cleaner(candidate["correct_answer"] or "").strip():
                        write_count += 1
                    continue
                option_values = [candidate[f"option_{letter}"] for letter in ("a", "b", "c", "d")]
                normalized = [text_cleaner(value or "").strip().casefold() for value in option_values]
                correct_letter = correct_letter_resolver(*option_values, candidate["correct_answer"])
                if all(normalized) and len(set(normalized)) == 4 and correct_letter in {"A", "B", "C", "D"}:
                    choice_count += 1
            available_rounds = 0
            for possible in range(1, 6):
                natural_writes = min(possible, write_count)
                if choice_count >= possible * 4 + (possible - natural_writes):
                    available_rounds = possible
            availability_band = next(iter(bands))
            cur.execute('SELECT class FROM users WHERE user_id=%s', (user_id,))
            user_row = cur.fetchone()
            if user_row and is_applicant_value(user_row.get("class")):
                availability_band = "applicant"
            conn.commit()
            return {
                "available_count": available_rounds * 5,
                "options": [count for count in (5, 10, 15, 20, 25) if count <= available_rounds * 5],
                "choice_count": choice_count,
                "write_count": write_count,
                "grade_band": availability_band,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.post("/boshlash")
    def start_game(request: GameStartRequest):
        user_id = jwt_verify(request.token)
        if request.game_mode not in GAME_MODES:
            raise HTTPException(status_code=400, detail="O'yin turi noto'g'ri")
        if request.question_count not in GAME_QUESTION_COUNTS:
            raise HTTPException(status_code=400, detail="O'yin savollari 5, 10, 15, 20 yoki 25 ta bo'ladi")
        topic_codes = _clean_topic_codes(request.topic_codes)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            _ensure_profile(cur, user_id)
            cur.execute(
                """SELECT topic_code,grade,subject_code FROM dts_tree
                   WHERE topic_code=ANY(%s) AND is_deleted=FALSE""",
                (topic_codes,),
            )
            dts_rows = cur.fetchall()
            dts_by_code = {row["topic_code"]: row for row in dts_rows}
            missing_codes = [code for code in topic_codes if code not in dts_by_code]
            if missing_codes:
                raise HTTPException(status_code=400, detail="Tanlangan mavzu kodlaridan biri DTS bazasida yo'q")
            bands = {grade_band_for_value(row["grade"]) for row in dts_rows}
            if len(bands) > 1:
                raise HTTPException(status_code=400, detail="Bitta o'yinda bir yosh bosqichidagi mavzularni tanlang")
            grade_band = next(iter(bands))
            cur.execute('SELECT class FROM users WHERE user_id=%s', (user_id,))
            user_row = cur.fetchone()
            if user_row and is_applicant_value(user_row.get("class")):
                grade_band = "applicant"

            # Ochko kaliti foydalanuvchi yuborgan ixtiyoriy kombinatsiyadan
            # emas, DTS'dagi haqiqiy sinf+fan identifikatoridan tuziladi.
            canonical_subjects = set()
            for row in dts_rows:
                code_parts = str(row["topic_code"] or "").split("-")
                subject_code = row["subject_code"] or (code_parts[1] if len(code_parts) > 1 else "")
                canonical_subjects.add(f"{row['grade']}|{subject_code}")
            if len(canonical_subjects) != 1:
                raise HTTPException(status_code=400, detail="Bitta o'yinda faqat bitta sinf va bitta fan mavzularini tanlang")
            canonical_subject = next(iter(canonical_subjects))

            cur.execute(
                """SELECT id,topic_code,question,option_a,option_b,option_c,option_d,
                          correct_answer,explanation,question_type,is_latex,time_limit,difficulty,
                          CASE WHEN rasm_malumot IS NOT NULL
                                 THEN '/api/test_rasmi/' || id::text
                               ELSE COALESCE(NULLIF(image_url,''),NULLIF(image_file_id,''))
                          END AS rasm_id
                   FROM generated_tests WHERE topic_code=ANY(%s)
                   ORDER BY RANDOM()""",
                (topic_codes,),
            )
            candidates = list(cur.fetchall())
            choices = []
            writes = []
            for candidate in candidates:
                question_text = text_cleaner(candidate["question"] or "").strip()
                if not question_text:
                    continue
                if candidate["question_type"] == "write_answer":
                    if text_cleaner(candidate["correct_answer"] or "").strip():
                        writes.append(candidate)
                    continue
                option_values = [candidate[f"option_{letter}"] for letter in ("a", "b", "c", "d")]
                normalized_options = [text_cleaner(value or "").strip().casefold() for value in option_values]
                correct_letter = correct_letter_resolver(*option_values, candidate["correct_answer"])
                if all(normalized_options) and len(set(normalized_options)) == 4 and correct_letter in {"A", "B", "C", "D"}:
                    choices.append(candidate)

            random.shuffle(choices)
            random.shuffle(writes)
            rounds = request.question_count // 5
            natural_boss_count = min(rounds, len(writes))
            choice_needed = rounds * 4 + (rounds - natural_boss_count)
            if len(choices) < choice_needed:
                available_rounds = 0
                for possible in range(1, 6):
                    available_writes = min(possible, len(writes))
                    if len(choices) >= possible * 4 + (possible - available_writes):
                        available_rounds = possible
                available_count = min(25, available_rounds * 5)
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "O'yin uchun yetarli sifatli savol yo'q: har raundga 4 ta tugmali va 1 ta Boss kerak. "
                        f"Hozir ko'pi bilan {available_count} ta o'ynash mumkin."
                    ),
                )
            choices = choices[:choice_needed]
            writes = writes[:natural_boss_count]

            # Har foydalanuvchida bitta faol o'yin: yangi o'yin aniq
            # boshlanganida eski tashlab ketilgan sessiyalar ochiq qolmaydi.
            cur.execute(
                """UPDATE game_sessions SET status='abandoned',finished_at=NOW(),updated_at=NOW()
                   WHERE user_id=%s AND status='active'""",
                (user_id,),
            )
            session_id = secrets.token_urlsafe(24)
            actual_count = request.question_count
            content_key = _content_key("canonical_subject", [canonical_subject], 0)
            initial_lives = initial_lives_for_band(grade_band)
            cur.execute(
                """INSERT INTO game_sessions
                     (session_id,user_id,game_mode,grade_band,topic_codes,content_key,
                      requested_questions,total_questions,current_position,status,
                      initial_lives,lives_remaining)
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,1,'active',%s,%s)""",
                (
                    session_id, user_id, request.game_mode, grade_band, topic_codes,
                    content_key, request.question_count, actual_count,
                    initial_lives, initial_lives,
                ),
            )

            records = []
            choice_index = 0
            write_index = 0
            position = 1
            for round_index in range(rounds):
                for _ in range(4):
                    question = choices[choice_index]
                    choice_index += 1
                    source_keys = ["A", "B", "C", "D"]
                    random.shuffle(source_keys)
                    option_map = dict(zip(("A", "B", "C", "D"), source_keys))
                    records.append((
                        session_id, position, secrets.token_urlsafe(18), question["id"],
                        question["topic_code"], "choice", False, 1,
                        bounded_question_time_limit(
                            question.get("time_limit"), question.get("difficulty"), False
                        ),
                        json.dumps(option_map),
                        json.dumps(
                            {
                                key: question.get(key)
                                for key in (
                                    "question", "option_a", "option_b", "option_c", "option_d",
                                    "correct_answer", "explanation", "question_type", "is_latex",
                                    "time_limit", "difficulty", "rasm_id",
                                )
                            },
                            ensure_ascii=False,
                            default=str,
                        ),
                        [],
                    ))
                    position += 1
                if write_index < len(writes):
                    boss = writes[write_index]
                    write_index += 1
                    display_type = "boss_write"
                else:
                    boss = choices[choice_index]
                    choice_index += 1
                    display_type = "boss_converted"
                records.append((
                    session_id, position, secrets.token_urlsafe(18), boss["id"],
                    boss["topic_code"], display_type, True, boss_attempt_limit(grade_band),
                    bounded_question_time_limit(
                        boss.get("time_limit"), boss.get("difficulty"), True
                    ),
                    json.dumps({}),
                    json.dumps(
                        {
                            key: boss.get(key)
                            for key in (
                                "question", "option_a", "option_b", "option_c", "option_d",
                                "correct_answer", "explanation", "question_type", "is_latex",
                                "time_limit", "difficulty", "rasm_id",
                            )
                        },
                        ensure_ascii=False,
                        default=str,
                    ),
                    [],
                ))
                position += 1

            psycopg2.extras.execute_values(
                cur,
                """INSERT INTO game_session_questions
                     (session_id,position,question_key,question_id,topic_code,display_type,
                      is_boss,max_attempts,time_limit_seconds,option_map,
                      question_snapshot,hidden_options)
                   VALUES %s""",
                records,
            )
            cur.execute("SELECT * FROM game_sessions WHERE session_id=%s", (session_id,))
            session = cur.fetchone()
            response = session_summary(cur, session)
            response["profile"] = _profile_payload(cur, user_id)
            response["requested_questions"] = request.question_count
            response["actual_questions"] = actual_count
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.post("/tayyor")
    def ready_game_question(request: GameReadyRequest):
        """Savol ekranda ko'ringandan keyingina authoritative deadline boshlanadi."""
        user_id = jwt_verify(request.token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            session = get_session_for_update(cur, request.session_id, user_id)
            replay, request_hash = action_replay(
                cur,
                session_id=session["session_id"],
                user_id=user_id,
                action_id=request.action_id,
                action_type="ready",
                payload={"question_key": request.question_key},
            )
            if replay is not None:
                current = get_current_row(cur, session, for_update=True) if session["status"] == "active" else None
                if current and current["question_key"] == request.question_key:
                    # Effect replay qilinadi, ammo vaqtga bog'liq maydonlar
                    # eski cached remaining_seconds emas, hozirgi DB soatidan.
                    refreshed = {"ready": True, "replayed": True, **session_summary(cur, session)}
                    conn.commit()
                    return refreshed
                conn.commit()
                return replay
            if session["status"] != "active":
                raise HTTPException(status_code=409, detail="Bu o'yin endi faol emas")
            row = get_current_row(cur, session, for_update=True)
            if not row or row["question_key"] != request.question_key:
                raise HTTPException(status_code=409, detail="Bu savol endi faol emas")
            if row["answered_at"] is not None:
                raise HTTPException(status_code=409, detail="Bu savol allaqachon yakunlangan")

            activate_question_timer(cur, row)
            response = {"ready": True, **session_summary(cur, session)}
            save_action(
                cur,
                session_id=session["session_id"],
                user_id=user_id,
                action_id=request.action_id,
                action_type="ready",
                request_hash=request_hash,
                response=response,
            )
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.post("/javob")
    def answer_game(request: GameAnswerRequest):
        user_id = jwt_verify(request.token)
        answer = (request.answer or "").strip()
        if not answer:
            raise HTTPException(status_code=400, detail="Javobni kiriting")
        if len(answer) > 1000:
            raise HTTPException(status_code=400, detail="Javob juda uzun")
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            session = get_session_for_update(cur, request.session_id, user_id)
            replay, request_hash = action_replay(
                cur,
                session_id=session["session_id"],
                user_id=user_id,
                action_id=request.action_id,
                action_type="answer",
                payload={"question_key": request.question_key, "answer": answer},
            )
            if replay is not None:
                conn.commit()
                return replay
            if session["status"] != "active":
                result = session.get("result") or {}
                conn.commit()
                return {"status": session["status"], "result": result, "profile": _profile_payload(cur, user_id)}
            row = get_current_row(cur, session, for_update=True)
            if not row or row["question_key"] != request.question_key:
                raise HTTPException(status_code=409, detail="Bu savol endi faol emas")
            if row["answered_at"] is not None:
                raise HTTPException(status_code=409, detail="Bu savolga javob allaqachon yakunlangan")
            # Client yuborgan elapsed qiymati umuman qabul qilinmaydi. Javob
            # faqat DB deadline hali o'tmagan bo'lsa baholanadi.
            require_active_timer(cur, row)

            attempts_used = int(row["attempts_used"] or 0) + 1
            if row["display_type"] == "choice":
                selected = answer.upper()
                if selected not in {"A", "B", "C", "D"} or selected in set(row.get("hidden_options") or []):
                    raise HTTPException(status_code=400, detail="Ko'rinib turgan javoblardan birini tanlang")
                correct = selected == display_correct_letter(row)
            else:
                correct = written_answer_checker(answer, correct_text(row))

            retry = bool(row["is_boss"] and not correct and attempts_used < int(row["max_attempts"]))
            if retry:
                cur.execute(
                    """UPDATE game_session_questions SET attempts_used=%s,answer_text=%s
                       WHERE session_id=%s AND position=%s""",
                    (attempts_used, answer, session["session_id"], row["position"]),
                )
                row["attempts_used"] = attempts_used
                reset_question_timer(cur, row)
                response = {
                    "status": "retry",
                    "correct": False,
                    "attempts_used": attempts_used,
                    "attempts_left": int(row["max_attempts"]) - attempts_used,
                    "hint": "Javobning asosiy so'zi yoki hisob qadamini yana bir marta tekshiring.",
                    "question": question_payload(cur, session, row),
                    "initial_lives": int(session["initial_lives"]),
                    "lives_remaining": int(session["lives_remaining"]),
                }
                save_action(
                    cur,
                    session_id=session["session_id"],
                    user_id=user_id,
                    action_id=request.action_id,
                    action_type="answer",
                    request_hash=request_hash,
                    response=response,
                )
                conn.commit()
                return response

            if is_terminal_boss_failure(
                is_boss=bool(row["is_boss"]),
                correct=bool(correct),
                attempts_used=attempts_used,
                max_attempts=int(row["max_attempts"]),
            ):
                explanation = text_cleaner(snapshot(row).get("explanation") or "")
                revealed_answer = correct_text(row)
                cur.execute(
                    """UPDATE game_session_questions
                       SET attempts_used=%s,answer_text=%s,correct=FALSE,answered_at=NOW()
                       WHERE session_id=%s AND position=%s""",
                    (attempts_used, answer, session["session_id"], row["position"]),
                )
                cur.execute(
                    "SELECT * FROM game_sessions WHERE session_id=%s FOR UPDATE",
                    (session["session_id"],),
                )
                updated = cur.fetchone()
                result = finish_locked(
                    cur,
                    updated,
                    completed=False,
                    terminal_status="game_over",
                    terminal_reason="boss_attempts_exhausted",
                )
                response = {
                    "status": "game_over",
                    "correct": False,
                    "correct_answer": revealed_answer,
                    "explanation": explanation,
                    "lives_remaining": int(updated["lives_remaining"]),
                    "result": result,
                }
                save_action(
                    cur,
                    session_id=session["session_id"],
                    user_id=user_id,
                    action_id=request.action_id,
                    action_type="answer",
                    request_hash=request_hash,
                    response=response,
                )
                conn.commit()
                return response

            cur.execute(
                """UPDATE game_session_questions SET attempts_used=%s,answer_text=%s,
                          correct=%s,answered_at=NOW()
                   WHERE session_id=%s AND position=%s""",
                (attempts_used, answer, correct, session["session_id"], row["position"]),
            )
            next_position = int(session["current_position"]) + 1
            cur.execute(
                """UPDATE game_sessions SET current_position=%s,
                          correct_count=correct_count+%s,updated_at=NOW()
                   WHERE session_id=%s""",
                (next_position, 1 if correct else 0, session["session_id"]),
            )
            explanation = text_cleaner(snapshot(row).get("explanation") or "")
            revealed_answer = display_correct_letter(row) if row["display_type"] == "choice" else correct_text(row)

            cur.execute("SELECT * FROM game_sessions WHERE session_id=%s FOR UPDATE", (session["session_id"],))
            updated = cur.fetchone()
            if next_position > int(updated["total_questions"]):
                result = finish_locked(cur, updated, completed=True)
                response = {
                    "status": "finished",
                    "correct": bool(correct),
                    "correct_answer": revealed_answer,
                    "explanation": explanation,
                    "result": result,
                }
                save_action(
                    cur,
                    session_id=session["session_id"],
                    user_id=user_id,
                    action_id=request.action_id,
                    action_type="answer",
                    request_hash=request_hash,
                    response=response,
                )
                conn.commit()
                return response
            payload = session_summary(cur, updated)
            response = {
                **payload,
                "status": "next",
                "correct": bool(correct),
                "correct_answer": revealed_answer,
                "explanation": explanation,
            }
            save_action(
                cur,
                session_id=session["session_id"],
                user_id=user_id,
                action_id=request.action_id,
                action_type="answer",
                request_hash=request_hash,
                response=response,
            )
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.post("/vaqt-tugadi")
    def timeout_game_question(request: GameTimeoutRequest):
        """Faqat DB deadline tugagach, timeout'ni bir marta qo'llaydi."""
        user_id = jwt_verify(request.token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            session = get_session_for_update(cur, request.session_id, user_id)
            replay, request_hash = action_replay(
                cur,
                session_id=session["session_id"],
                user_id=user_id,
                action_id=request.action_id,
                action_type="timeout",
                payload={"question_key": request.question_key},
            )
            if replay is not None:
                conn.commit()
                return replay
            if session["status"] != "active":
                raise HTTPException(status_code=409, detail="Bu o'yin endi faol emas")
            row = get_current_row(cur, session, for_update=True)
            if not row or row["question_key"] != request.question_key:
                raise HTTPException(status_code=409, detail="Bu savol endi faol emas")
            if row["answered_at"] is not None:
                raise HTTPException(status_code=409, detail="Bu savol allaqachon yakunlangan")

            timer = question_timer_payload(cur, row)
            if timer["timer_status"] == "waiting":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "QUESTION_NOT_READY",
                        "message": "Ko'rinmagan savol uchun timeout yuborib bo'lmaydi",
                        **timer,
                    },
                )
            if timer["timer_status"] != "expired":
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "TIMER_STILL_ACTIVE",
                        "message": "Server bo'yicha savol vaqti hali tugamagan",
                        **timer,
                    },
                )

            transition = timeout_transition(
                is_boss=bool(row["is_boss"]),
                attempts_used=int(row["attempts_used"] or 0),
                max_attempts=int(row["max_attempts"]),
                lives_remaining=int(session["lives_remaining"]),
            )
            attempts_used = transition["attempts_used"]
            explanation = text_cleaner(snapshot(row).get("explanation") or "")
            revealed_answer = (
                display_correct_letter(row)
                if row["display_type"] == "choice"
                else correct_text(row)
            )

            if transition["outcome"] == "boss_retry":
                cur.execute(
                    """UPDATE game_session_questions
                       SET attempts_used=%s,answer_text='[timeout]',timed_out=TRUE,
                           timer_started_at=NULL,deadline_at=NULL
                       WHERE session_id=%s AND position=%s""",
                    (attempts_used, session["session_id"], row["position"]),
                )
                row["attempts_used"] = attempts_used
                row["timed_out"] = True
                row["timer_started_at"] = None
                row["deadline_at"] = None
                response = {
                    "status": "retry",
                    "timed_out": True,
                    "correct": False,
                    "attempts_used": attempts_used,
                    "attempts_left": transition["attempts_left"],
                    "hint": "Boss vaqti tugadi. Yangi urinishni tayyor bo'lganda boshlang.",
                    "question": question_payload(cur, session, row),
                    "initial_lives": int(session["initial_lives"]),
                    "lives_remaining": int(session["lives_remaining"]),
                }
            elif transition["outcome"] == "game_over_boss":
                cur.execute(
                    """UPDATE game_session_questions
                       SET attempts_used=%s,answer_text='[timeout]',timed_out=TRUE,
                           correct=FALSE,answered_at=NOW()
                       WHERE session_id=%s AND position=%s""",
                    (attempts_used, session["session_id"], row["position"]),
                )
                cur.execute(
                    "SELECT * FROM game_sessions WHERE session_id=%s FOR UPDATE",
                    (session["session_id"],),
                )
                updated = cur.fetchone()
                result = finish_locked(
                    cur,
                    updated,
                    completed=False,
                    terminal_status="game_over",
                    terminal_reason="boss_attempts_exhausted",
                )
                response = {
                    "status": "game_over",
                    "timed_out": True,
                    "correct": False,
                    "correct_answer": revealed_answer,
                    "explanation": explanation,
                    "lives_remaining": int(updated["lives_remaining"]),
                    "result": result,
                }
            else:
                cur.execute(
                    """UPDATE game_session_questions
                       SET attempts_used=1,answer_text='[timeout]',timed_out=TRUE,
                           correct=FALSE,answered_at=NOW()
                       WHERE session_id=%s AND position=%s""",
                    (session["session_id"], row["position"]),
                )
                cur.execute(
                    """UPDATE game_sessions
                       SET lives_remaining=%s,updated_at=NOW()
                       WHERE session_id=%s RETURNING *""",
                    (transition["lives_remaining"], session["session_id"]),
                )
                updated = cur.fetchone()
                lives_remaining = int(updated["lives_remaining"])
                if lives_remaining == 0:
                    result = finish_locked(
                        cur,
                        updated,
                        completed=False,
                        terminal_status="game_over",
                        terminal_reason="lives_exhausted",
                    )
                    response = {
                        "status": "game_over",
                        "timed_out": True,
                        "correct": False,
                        "correct_answer": revealed_answer,
                        "explanation": explanation,
                        "lives_lost": 1,
                        "lives_remaining": 0,
                        "result": result,
                    }
                else:
                    next_position = int(updated["current_position"]) + 1
                    cur.execute(
                        """UPDATE game_sessions SET current_position=%s,updated_at=NOW()
                           WHERE session_id=%s RETURNING *""",
                        (next_position, session["session_id"]),
                    )
                    updated = cur.fetchone()
                    if next_position > int(updated["total_questions"]):
                        result = finish_locked(cur, updated, completed=True)
                        response = {
                            "status": "finished",
                            "timed_out": True,
                            "correct": False,
                            "correct_answer": revealed_answer,
                            "explanation": explanation,
                            "lives_lost": 1,
                            "lives_remaining": lives_remaining,
                            "result": result,
                        }
                    else:
                        payload = session_summary(cur, updated)
                        response = {
                            **payload,
                            "status": "next",
                            "timed_out": True,
                            "correct": False,
                            "correct_answer": revealed_answer,
                            "explanation": explanation,
                            "lives_lost": 1,
                            "lives_remaining": lives_remaining,
                        }

            save_action(
                cur,
                session_id=session["session_id"],
                user_id=user_id,
                action_id=request.action_id,
                action_type="timeout",
                request_hash=request_hash,
                response=response,
            )
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.post("/yordam")
    def use_lifeline(request: GameLifelineRequest):
        user_id = jwt_verify(request.token)
        if request.lifeline not in {"fifty_fifty", "remove_one"}:
            raise HTTPException(status_code=400, detail="Yordam turi noto'g'ri")
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            session = get_session_for_update(cur, request.session_id, user_id)
            replay, request_hash = action_replay(
                cur,
                session_id=session["session_id"],
                user_id=user_id,
                action_id=request.action_id,
                action_type="lifeline",
                payload={"question_key": request.question_key, "lifeline": request.lifeline},
            )
            if replay is not None:
                conn.commit()
                return replay
            if session["status"] != "active" or session["game_mode"] != "millionaire":
                raise HTTPException(status_code=409, detail="Bu yordam faqat faol Millioner o'yinida ishlaydi")
            used = list(session.get("lifelines_used") or [])
            if request.lifeline in used:
                raise HTTPException(status_code=409, detail="Bu yordam avval ishlatilgan")
            row = get_current_row(cur, session, for_update=True)
            if not row or row["question_key"] != request.question_key or row["is_boss"]:
                raise HTTPException(status_code=409, detail="Bu savolda yordam ishlatib bo'lmaydi")
            if row.get("lifeline_used"):
                raise HTTPException(status_code=409, detail="Bir savolda faqat bitta yordam ishlatiladi")
            require_active_timer(cur, row)
            correct_display = display_correct_letter(row)
            hidden_now = set(row.get("hidden_options") or [])
            wrong = [key for key in ("A", "B", "C", "D") if key != correct_display and key not in hidden_now]
            random.shuffle(wrong)
            remove_count = 2 if request.lifeline == "fifty_fifty" else 1
            removed = wrong[:remove_count]
            hidden = sorted(hidden_now.union(removed))
            cur.execute(
                """UPDATE game_session_questions SET hidden_options=%s,lifeline_used=%s
                   WHERE session_id=%s AND position=%s""",
                (hidden, request.lifeline, session["session_id"], row["position"]),
            )
            cur.execute(
                """UPDATE game_sessions SET lifelines_used=array_append(lifelines_used,%s),updated_at=NOW()
                   WHERE session_id=%s""",
                (request.lifeline, session["session_id"]),
            )
            cur.execute("SELECT * FROM game_sessions WHERE session_id=%s", (session["session_id"],))
            updated = cur.fetchone()
            payload = session_summary(cur, updated)
            response = {"removed_options": removed, **payload}
            save_action(
                cur,
                session_id=session["session_id"],
                user_id=user_id,
                action_id=request.action_id,
                action_type="lifeline",
                request_hash=request_hash,
                response=response,
            )
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.post("/yakunlash")
    def finish_game(request: GameFinishRequest):
        user_id = jwt_verify(request.token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            session = get_session_for_update(cur, request.session_id, user_id)
            already_completed = session["status"] == "completed"
            result = finish_locked(cur, session, completed=already_completed)
            conn.commit()
            final_status = session["status"] if session["status"] != "active" else "abandoned"
            return {"status": final_status, "result": result}
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.get("/sessiya/{session_id}")
    def resume_game(session_id: str, token: str):
        user_id = jwt_verify(token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _require_game_tables(cur)
            session = get_session_for_update(cur, session_id, user_id)
            response = session_summary(cur, session)
            response["profile"] = _profile_payload(cur, user_id)
            conn.commit()
            return response
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    return router

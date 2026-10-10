"""REV82: onlayn bellashuv — vaqt fazalari, ochko, reyting va variantlar (DB'siz)."""
from datetime import datetime, timedelta, timezone

from modules import bellashuv as b

T0 = datetime(2026, 9, 29, 10, 0, 0, tzinfo=timezone.utc)
ROOM = {"status": "started", "started_at": T0, "savol_vaqti": 20}


def test_phases_follow_server_clock():
    assert b.phase_at({"status": "lobby", "started_at": None}, T0, 5) == ("lobby", -1, None)
    assert b.phase_at(ROOM, T0 - timedelta(seconds=2), 5) == ("countdown", -1, T0)
    assert b.phase_at(ROOM, T0 + timedelta(seconds=3), 5) == ("question", 0, T0 + timedelta(seconds=20))
    assert b.phase_at(ROOM, T0 + timedelta(seconds=22), 5) == ("reveal", 0, T0 + timedelta(seconds=25))
    assert b.phase_at(ROOM, T0 + timedelta(seconds=25), 5)[:2] == ("question", 1)
    assert b.phase_at(ROOM, T0 + timedelta(seconds=25 * 5), 5) == ("finished", 5, None)


def test_score_rewards_speed_first_and_streak():
    assert b.score_answer(False, 100, 20, True, 5) == 0
    assert b.score_answer(True, 0, 20, False, 1) == 1000
    assert b.score_answer(True, 20_000, 20, False, 1) == 500
    assert b.score_answer(True, 99_000, 20, False, 1) == 500
    assert b.score_answer(True, 10_000, 20, True, 2) == 500 + 250 + 200 + 50


def test_podium_ties_share_place_and_break_by_time():
    players = [
        {"ism": "A", "ochko": 900, "togri": 1, "vaqt_ms": 4000},
        {"ism": "B", "ochko": 1500, "togri": 2, "vaqt_ms": 9000},
        {"ism": "C", "ochko": 900, "togri": 1, "vaqt_ms": 3000},
        {"ism": "D", "ochko": 0, "togri": 0, "vaqt_ms": 0},
    ]
    ordered = b.podium(players)
    assert [p["ism"] for p in ordered] == ["B", "C", "A", "D"]
    assert [p["orin"] for p in ordered] == [1, 2, 2, 4]


def test_options_must_be_contiguous_2_to_4():
    assert b.options_of({"option_a": "x", "option_b": "y"}) == ["x", "y"]
    assert b.options_of({"option_a": "x", "option_b": "y", "option_c": "z", "option_d": "w"}) == ["x", "y", "z", "w"]
    assert b.options_of({"option_a": "x"}) == []
    assert b.options_of({"option_a": "x", "option_b": "", "option_c": "z"}) == []


def test_codes_are_unambiguous():
    for _ in range(50):
        code = b.new_code()
        assert len(code) == 6 and not set(code) & set("01IO")
    assert b.norm_code(" ab-c12 3 ") == "ABC123"

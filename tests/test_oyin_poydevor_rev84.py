"""REV84: o'yinlar poydevori — Elo, vaqt nazorati, soat, juftlash oynasi, birinchi yurish muddati."""
from datetime import datetime, timedelta, timezone

from modules import oyin_reyting as rt
from modules import oyin_sessiya as s
from modules.shashka import ShashkaAdapter

T0 = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


def test_elo_equal_players_and_upsets():
    assert rt.elo_delta(1200, 1200, 1, 0) == 20          # yangi o'yinchi K=40
    assert rt.elo_delta(1200, 1200, 0.5, 0) == 0
    assert rt.elo_delta(1200, 1200, 1, 30) == 12         # tajribali K=24
    assert rt.elo_delta(1000, 1400, 1, 30) > rt.elo_delta(1400, 1000, 1, 30)   # kuchliroqni yutish qimmatroq
    assert rt.elo_delta(2100, 2100, 1, 50) == 8          # K=16
    assert abs(rt.expected(1500, 1100) + rt.expected(1100, 1500) - 1) < 1e-9


def test_time_controls_and_bot_levels():
    assert rt.control_of("3+2")[:3] == ("3+2", 180, 2)
    assert rt.control_of("cheksiz")[1] is None
    assert rt.control_of("99+9")[0] == rt.DEFAULT_CONTROL
    assert [rt.bot_level_for(r) for r in (900, 1200, 1400, 1700)] == [1, 2, 3, 4]
    assert rt.search_window(0) == 150 and rt.search_window(10) == 550


def test_clock_math():
    clock = rt.clock_after_move({"w": 60000, "b": 60000}, "w", 4500, 2)
    assert clock == {"w": 57500, "b": 60000}
    assert rt.clock_after_move({"w": 1000, "b": 1}, "w", 5000, 0)["w"] == 0
    left = rt.remaining_now({"w": 10000, "b": 9000}, "b", T0, T0 + timedelta(seconds=3))
    assert left == {"w": 10000, "b": 6000}


def game(**kw):
    g = {"holat": "davom", "turi": "onlayn", "oq_ms": 180000, "qora_ms": 180000, "yurishlar": [], "navbat": "w",
         "oxirgi_yurish_at": T0, "bot_rang": None}
    g.update(kw)
    return g


def test_clock_starts_after_both_first_moves_and_first_move_deadline():
    g = game()
    assert not s.clock_running(g)
    assert s.clocks_now(g, T0 + timedelta(seconds=20)) == {"w": 180000, "b": 180000}
    assert s.first_move_deadline(g) == T0 + timedelta(seconds=30)
    g2 = game(yurishlar=[{}, {}])
    assert s.clock_running(g2) and s.first_move_deadline(g2) is None
    assert s.clocks_now(g2, T0 + timedelta(seconds=20))["w"] == 160000
    assert s.first_move_deadline(game(turi="bot")) is None
    assert s.first_move_deadline(game(oq_ms=None)) is None          # vaqtsiz do'st o'yini
    assert s.first_move_deadline(game(bot_rang="w")) is None        # bot yuradi


def test_results_and_hidden_bot_delay():
    assert s.result_for("w", "w") == "galaba" and s.result_for("w", "b") == "maglubiyat" and s.result_for("durang", "w") == "durang"
    import random
    rng = random.Random(3)
    fast = [s.bot_delay(False, 7, rng) for _ in range(30)]
    human = [s.bot_delay(True, 7, rng) for _ in range(30)]
    assert max(fast) < 1 and min(human) > 1 and max(human) <= 9
    name, jins = s.human_bot_name(rng)
    assert name.endswith(".") and jins in ("qiz", "ogil")


def test_shashka_adapter_tracks_quiet_king_moves():
    a = ShashkaAdapter()
    pos = "." * 64
    pos = pos[:0] + "W" + pos[1:]
    move = {"path": [0, 9], "caps": []}
    assert a.update_meta(pos, move, {"tinch": 4})["tinch"] == 5
    assert a.update_meta(pos, {"path": [0, 18], "caps": [9]}, {"tinch": 4})["tinch"] == 0
    assert a.outcome(a.initial(), "w", {}, 0)[0] is False

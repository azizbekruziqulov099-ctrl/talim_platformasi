"""REV690: 10 savolli o'yinda 4 ta boss (3, 5, 8, 10-savol); ball hisobi boss soniga bog'liq emas."""
from modules.test_games import GAME_LEVEL_SIZE, is_boss_step, score_game_rows


def test_10_savolda_4_boss():
    bosslar = [r * GAME_LEVEL_SIZE + s + 1 for r in range(2) for s in range(GAME_LEVEL_SIZE) if is_boss_step(s)]
    assert bosslar == [3, 5, 8, 10]


def test_raund_oxirgi_savoli_doim_boss():
    assert is_boss_step(GAME_LEVEL_SIZE - 1) and not is_boss_step(0)


def test_ball_4_boss_bilan_ham_1000_dan_oshmaydi():
    rows = [{"is_boss": is_boss_step(i % GAME_LEVEL_SIZE), "correct": True, "attempts_used": 1, "answered_at": "now"} for i in range(10)]
    r = score_game_rows(rows, completed=True)
    assert r["score_1000"] == 1000 and r["boss_points"] == 300 and r["regular_points"] == 500
    rows[2]["correct"] = False          # bitta boss xato
    r = score_game_rows(rows, completed=True)
    assert r["boss_points"] == 225 and r["regular_points"] == 500

"""REV83: shashka qoidalari (rus shashkasi) va bot darajalari."""
import random

from modules import shashka_engine as e


def board(**pieces):
    cells = ["."] * 64
    for ch, squares in pieces.items():
        for sq in squares.split():
            cells[e.sq_index(sq)] = ch
    return "".join(cells)


def names(moves):
    return sorted(e.notation(m) for m in moves)


def test_start_position_and_first_moves():
    b = e.initial_board()
    assert e.counts(b) == {"w": 12, "b": 12, "W": 0, "B": 0}
    assert b[e.sq_index("a1")] == "w" and b[e.sq_index("h8")] == "b"
    assert names(e.legal_moves(b, "w")) == sorted(["a3-b4", "c3-b4", "c3-d4", "e3-d4", "e3-f4", "g3-f4", "g3-h4"])


def test_capture_is_mandatory_and_man_captures_backwards():
    b = board(w="e5 a1", b="d4")
    # a1-b2 oddiy yurish bor, lekin urish majburiy: e5 dona d4 ni orqaga urib c3 ga tushadi
    assert names(e.legal_moves(b, "w")) == ["e5:c3"]


def test_multi_jump_and_choice_of_path():
    b = board(w="c1", b="d2 f4 d6")
    assert names(e.legal_moves(b, "w")) == ["c1:e3:g5"]
    b2 = board(w="c1", b="d2 f4 d4")
    assert names(e.legal_moves(b2, "w")) == ["c1:e3:c5", "c1:e3:g5"]


def test_promotion_during_capture_continues_as_king():
    # f6:d8 — damka bo'ladi va endi uchib (c7 bo'sh) b6 ni urib a5 ga tushadi; oddiy dona buni qila olmasdi
    b = board(w="f6", b="e7 b6")
    assert names(e.legal_moves(b, "w")) == ["f6:d8:a5"]
    assert e.apply_move(b, e.legal_moves(b, "w")[0])[e.sq_index("a5")] == "W"


def test_flying_king_moves_and_captures_from_distance():
    b = board(W="a1", b="e5")
    got = names(e.legal_moves(b, "w"))
    assert got == ["a1:f6", "a1:g7", "a1:h8"]
    quiet = board(W="d4")
    assert len(e.legal_moves(quiet, "w")) == 13


def test_king_must_land_where_capture_continues():
    # Damka a1 dan c3 ni uradi; d4/e5/f6... tushish mumkin, lekin faqat e5 dan f6? — g7 ... davom etadi.
    b = board(W="a1", b="c3 f6")
    got = names(e.legal_moves(b, "w"))
    # c3 urilgandan so'ng d4 dan d4-e5 bo'ylab f6 bir diagonalda — e5 ga tushsa ham, d4 ga tushsa ham f6 ni urish mumkin
    assert all(m.count(":") == 2 for m in got), got
    b = board(W="a1", b="c3 f2")
    got = names(e.legal_moves(b, "w"))
    assert got == ["a1:d4:g1"], got   # faqat d4 dan f2 ga yo'l bor


def test_piece_cannot_be_jumped_twice_and_blocks():
    b = board(W="a1", b="c3 e5")
    # c3 va e5 bir diagonalda ketma-ket: c3 urilgach d4 ga tushadi, e5 orqasi f6 bo'sh — ikkita donani bir sakrashda urib bo'lmaydi
    got = names(e.legal_moves(b, "w"))
    assert got == ["a1:d4:f6", "a1:d4:g7", "a1:d4:h8"], got


def test_apply_move_removes_captured_and_promotes():
    b = board(w="c7", b="a1")
    m = e.find_move(b, "w", ["c7", "d8"])
    after = e.apply_move(b, m)
    assert after[e.sq_index("d8")] == "W"
    assert e.find_move(b, "w", ["c7", "c8"]) is None


def test_outcome_no_moves_loses_and_draw_rules():
    b = board(w="a1", b="b2 c3")
    assert e.outcome(b, "w") == (True, "b", "yurish_yoq")
    assert e.outcome(board(W="a1", B="h8"), "w", quiet_king_plies=30) == (True, None, "damkalar_durang")
    assert e.outcome(e.initial_board(), "w")[0] is False


def _play(white, black, seed):
    rng = random.Random(seed)
    b, side, quiet = e.initial_board(), "w", 0
    lv = {"w": white, "b": black}
    for ply in range(200):
        done, win, _ = e.outcome(b, side, quiet, ply)
        if done:
            return win
        m = e.choose_move(b, side, lv[side], rng, 0.2)
        quiet = quiet + 1 if not m["caps"] and b[m["path"][0]].isupper() else 0
        b, side = e.apply_move(b, m), e.other(side)
    return None


def test_stronger_bot_beats_weaker():
    assert [_play(3, 1, s) for s in range(3)].count("w") >= 2
    assert [_play(1, 3, s) for s in range(3)].count("b") >= 2

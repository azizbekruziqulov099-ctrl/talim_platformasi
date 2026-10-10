"""REV86: Shaxmat maktabi — har bir mashq tekshiriladi: FEN, yulduzlarga yetish, mat, yechim, shax usuli."""
import pytest

from modules import shaxmat_engine as e
from modules import shaxmat_maktab as mk

ALL = [(les["kod"], i, ex) for les in mk.LESSONS for i, ex in enumerate(les["mashqlar"])]


def test_curriculum_shape():
    codes = [les["kod"] for les in mk.LESSONS]
    assert len(codes) == len(set(codes)) >= 14
    assert all(les["matn"] and les["mashqlar"] for les in mk.LESSONS)
    assert [les["tartib"] for les in mk.LESSONS] == list(range(len(codes)))


@pytest.mark.parametrize("code,i,ex", ALL, ids=[f"{c}-{i}" for c, i, _ in ALL])
def test_every_exercise_is_valid(code, i, ex):
    b = e.Board(ex["fen"])
    assert b.fen().split()[0] == ex["fen"].split()[0]
    if ex["tur"] == "katak":
        assert ex["javob"] and all(e.sq_index(s) >= 0 for s in ex["javob"])
    elif ex["tur"] == "yulduz":
        par = mk.par_of(code, i)
        assert par is not None and 1 <= par <= 8, par
    elif ex["tur"] == "mat":
        assert mk.forced_mate(b, ex["n"])
        if ex["n"] > 1:
            assert not mk.forced_mate(b, ex["n"] - 1)   # oson yo'l yo'q
    elif ex["tur"] == "yechim":
        fen = ex["fen"]
        for step in ex["yechim"]:
            m = e.find_move(fen, e.side_to_move(fen), [step[:2], step[2:4]] + ([step[4]] if len(step) > 4 else []))
            assert m, (code, step)
            fen = e.apply_move(fen, m)
    elif ex["tur"] == "shax":
        assert b.in_check()
        methods = {mk.method_of(b, m) for m in b.legal()}
        assert ex["usul"] in methods


def test_star_exercise_flow_and_par():
    fen = mk.BY_CODE["ruh"]["mashqlar"][0]["fen"]
    r = mk.check_move("ruh", 0, fen, ["a1", "a5"])
    assert r["togri"] and r["yigildi"] == ["a5"] and not r["tugadi"] and r["fen"].split()[1] == "w"
    r = mk.check_move("ruh", 0, r["fen"], ["a5", "e5"], r["yigildi"])
    assert r["tugadi"]
    assert mk.check_move("ruh", 0, fen, ["a1", "b2"])["togri"] is False
    assert mk.par_of("ot", 2) == 6            # a1 dan h8 ga ot 6 sakrashda
    assert mk.stars_for(0, 2, 2) == 3 and mk.stars_for(0, 4, 2) == 2 and mk.stars_for(3) == 1


def test_mate_exercises_accept_any_mate_and_defend():
    fen = mk.BY_CODE["mat1"]["mashqlar"][0]["fen"]
    assert mk.check_move("mat1", 0, fen, ["a1", "a8"])["tugadi"]
    assert mk.check_move("mat1", 0, fen, ["a1", "a7"])["togri"] is False
    fen2 = mk.BY_CODE["mat2"]["mashqlar"][0]["fen"]
    r = mk.check_move("mat2", 0, fen2, ["b2", "b7"])
    assert r["togri"] and not r["tugadi"] and r["javob"]
    mates = [m for m in r["mumkin"] if mk.check_move("mat2", 0, r["fen"], m, step=1).get("tugadi")]
    assert mates
    assert mk.check_move("mat2", 0, fen2, ["h1", "g2"])["togri"] is False


def test_solution_and_check_exercises():
    ex = mk.BY_CODE["vilka"]["mashqlar"][0]
    r = mk.check_move("vilka", 0, ex["fen"], ["b5", "c7"])
    assert r["togri"] and r["javob"] == ["e8", "d7"]
    assert mk.check_move("vilka", 0, r["fen"], ["c7", "a8"], step=1)["tugadi"]
    assert mk.check_move("vilka", 0, ex["fen"], ["b5", "d6"])["togri"] is False
    tos = mk.BY_CODE["shax"]["mashqlar"][1]["fen"]
    assert mk.check_move("shax", 1, tos, ["e1", "e2"])["togri"] is False
    assert mk.check_move("shax", 1, tos, ["d2", "c1"])["tugadi"]
    ep = mk.BY_CODE["otib_urish"]["mashqlar"][0]["fen"]
    assert mk.check_move("otib_urish", 0, ep, ["e5", "d6"])["tugadi"]

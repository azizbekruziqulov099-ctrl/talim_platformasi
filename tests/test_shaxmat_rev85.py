"""REV85: shaxmat qoidalari — perft (yurish generatori), maxsus yurishlar, natijalar, SAN va bot."""
import random

import pytest

from modules import shaxmat_engine as e
from modules.shaxmat import ShaxmatAdapter, explain

PERFT = [
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", [20, 400, 8902]),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", [48, 2039]),       # «Kiwipete»
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [14, 191, 2812]),                           # o'tib urish, bog'lanish
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [6, 264, 9467]),      # aylanish, rokirovka
    ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", [44, 1486]),
]


@pytest.mark.parametrize("fen,expected", PERFT)
def test_perft_matches_reference(fen, expected):
    b = e.Board(fen)
    assert [e.perft(b, d + 1) for d in range(len(expected))] == expected
    assert b.fen() == e.Board(fen).fen()   # make/unmake holatni to'liq tiklaydi


def names(fen):
    return sorted("".join(e.move_names(m)) for m in e.legal_moves(fen))


def test_castling_rules():
    fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
    assert {"e1g1", "e1c1"} <= set(names(fen))
    after = e.apply_move(fen, e.find_move(fen, "w", ["e1", "g1"]))
    assert after.startswith("r3k2r/8/8/8/8/8/8/R4RK1 b kq")
    # f1 hujum ostida — qisqa rokirovka yo'q; shax ostida umuman yo'q
    assert "e1g1" not in names("5r2/8/8/8/8/8/8/R3K2R w KQ - 0 1")
    assert not {"e1g1", "e1c1"} & set(names("4r3/8/8/8/8/8/8/R3K2R w KQ - 0 1"))
    # ruh yurgach huquq yo'qoladi
    moved = e.apply_move(fen, e.find_move(fen, "w", ["h1", "h2"]))
    assert moved.split()[2] == "Qkq"


def test_en_passant_and_promotion():
    fen = "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"
    m = e.find_move(fen, "w", ["e5", "d6"])
    assert m and e.captured_square(fen, m) == "d5"
    assert e.apply_move(fen, m).startswith("4k3/8/3P4/8/")
    promo = "8/4P3/8/8/8/8/k7/4K3 w - - 0 1"
    assert {"e7e8q", "e7e8r", "e7e8b", "e7e8n"} <= set(names(promo))
    assert e.find_move(promo, "w", ["e7", "e8"]) is None          # aylanish figurasi shart
    assert e.apply_move(promo, e.find_move(promo, "w", ["e7", "e8", "n"])).startswith("4N3/")


def test_results_mate_stalemate_material_fifty_repetition():
    assert e.outcome("R5k1/5ppp/8/8/8/8/8/6K1 b - - 0 1") == (True, "w", "mat")
    assert e.outcome("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1") == (True, None, "pat")
    assert e.outcome("8/8/4k3/8/8/3NK3/8/8 w - - 0 1")[2] == "kuch_yetmaydi"
    assert e.outcome("8/8/4k3/8/8/3RK3/8/8 w - - 0 1")[0] is False
    assert e.outcome("8/8/4k3/8/8/3RK3/8/8 w - - 100 80")[2] == "ellik_yurish"
    fen = e.START_FEN
    meta = {}
    a = ShaxmatAdapter()
    for step in [["g1", "f3"], ["g8", "f6"], ["f3", "g1"], ["f6", "g8"]] * 2:
        m = a.find(fen, e.side_to_move(fen), step)
        meta = a.update_meta(fen, m, meta)
        fen = a.apply(fen, m)
    assert a.outcome(fen, "w", meta, 8) == (True, None, "takror")


def test_san_notation():
    fen = e.START_FEN
    assert e.san(fen, e.find_move(fen, "w", ["g1", "f3"])) == "Nf3"
    assert e.san(fen, e.find_move(fen, "w", ["e2", "e4"])) == "e4"
    rooks = "4k3/8/8/8/8/8/8/R4RK1 w - - 0 1"
    assert e.san(rooks, e.find_move(rooks, "w", ["a1", "d1"])) == "Rad1"
    mate = "6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1"
    assert e.san(mate, e.find_move(mate, "w", ["a1", "a8"])) == "Ra8#"
    castle = "4k3/8/8/8/8/8/8/R3K3 w Q - 0 1"
    assert e.san(castle, e.find_move(castle, "w", ["e1", "c1"])) == "O-O-O"


def test_bot_finds_mate_in_one_and_wins_material():
    mate = "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1"
    for level in (2, 3, 4):
        m = e.choose_move(mate, "w", level, random.Random(1), 0.5)
        assert e.san(mate, m) == "Rd8#"
    hang = "4k3/8/8/3q4/8/8/8/3RK3 w - - 0 1"   # himoyasiz farzin
    assert e.move_names(e.choose_move(hang, "w", 3, random.Random(2))) == ["d1", "d5"]
    assert "MAT" in explain(mate, e.find_move(mate, "w", ["d1", "d8"]))
    assert "farzinini uradi" in explain(hang, e.find_move(hang, "w", ["d1", "d5"]))


def test_status_and_counts():
    st = e.status(e.START_FEN)
    assert set(st) == {"shax", "shax_katak", "ustunlik"}
    check = e.status("4k3/8/8/8/8/8/8/4R1K1 b - - 0 1")
    assert check["shax"] is True and check["shax_katak"] == "e8" and check["ustunlik"] == 5
    assert e.counts(e.START_FEN) == {"w": 16, "b": 16}


def test_winning_bot_avoids_repetition():
    fen = "7k/8/8/8/8/8/1Q6/K7 w - - 0 1"
    b = e.Board(fen)
    scored = [(500, m) for m in b.legal()]
    first = scored[0][1]
    u = b.make(first)
    history = {b.key(): 2}
    b.unmake(u)
    adjusted = dict((m, v) for v, m in e._repetition_adjust(b, scored, history))
    assert adjusted[first] == 0 and max(adjusted.values()) == 500

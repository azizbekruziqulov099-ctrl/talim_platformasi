"""REV90: turnir — Shveytsariya juftlash, ochkolar va Buxgolts (DB'siz)."""
import random
import unittest

from modules.oyin_turnir import pair_round, result_mark, standings


def players(n):
    return [{"user_id": i, "ism": f"O'yinchi {i}", "reyting": 1500 - i * 10} for i in range(1, n + 1)]


def play_round(games, pairs, rnd, rng):
    for w, b in pairs:
        games.append({"tur": rnd, "oq_id": w, "qora_id": b, "holat": "tugadi", "golib": rng.choice(["w", "b", "durang"])})


class SwissTests(unittest.TestCase):
    def test_first_round_top_half_meets_bottom_half_with_alternating_colours(self):
        pairs, bye = pair_round(standings(players(8), []), 1)
        self.assertIsNone(bye)
        self.assertEqual(pairs, [(1, 5), (6, 2), (3, 7), (8, 4)])

    def test_odd_field_gives_lowest_player_a_bye_once(self):
        ps, games, byes, rng = players(7), [], {}, random.Random(3)
        seen = []
        for rnd in range(1, 6):
            table = standings(ps, games, byes)
            pairs, bye = pair_round(table, rnd)
            self.assertIsNotNone(bye)
            self.assertNotIn(bye, seen)          # hech kim ikki marta dam olmaydi
            seen.append(bye)
            byes.setdefault(bye, []).append(rnd)
            self.assertEqual(len(pairs), 3)
            self.assertNotIn(bye, {u for p in pairs for u in p})
            play_round(games, pairs, rnd, rng)
        row = next(r for r in standings(ps, games, byes) if r["user_id"] == seen[0])
        self.assertGreaterEqual(row["ochko"], 1)

    def test_no_rematch_and_colours_balanced_over_many_rounds(self):
        ps, games, rng = players(10), [], random.Random(7)
        for rnd in range(1, 8):
            pairs, _ = pair_round(standings(ps, games), rnd)
            self.assertEqual(len(pairs), 5)
            play_round(games, pairs, rnd, rng)
        met = [frozenset((g["oq_id"], g["qora_id"])) for g in games]
        self.assertEqual(len(met), len(set(met)))
        for row in standings(ps, games):
            self.assertLessEqual(abs(row["ranglar"].count("w") - row["ranglar"].count("b")), 2)

    def test_points_buchholz_and_order(self):
        ps = players(4)
        games = [{"tur": 1, "oq_id": 1, "qora_id": 3, "holat": "tugadi", "golib": "w"},
                 {"tur": 1, "oq_id": 4, "qora_id": 2, "holat": "tugadi", "golib": "durang"},
                 {"tur": 2, "oq_id": 2, "qora_id": 1, "holat": "tugadi", "golib": "b"},
                 {"tur": 2, "oq_id": 3, "qora_id": 4, "holat": "davom", "golib": None}]
        table = standings(ps, games)
        self.assertEqual([r["user_id"] for r in table][:1], [1])
        top = table[0]
        self.assertEqual((top["ochko"], top["galaba"], top["natijalar"]), (2.0, 2, {1: "1", 2: "1"}))
        self.assertEqual(top["buxgolts"], 0.5)   # raqiblar: 3 (0) va 2 (½)
        self.assertEqual(next(r for r in table if r["user_id"] == 3)["natijalar"][2], "…")
        self.assertEqual(result_mark(games[1]), "½–½")
        self.assertEqual(result_mark(games[3]), "…")

    def test_withdrawn_player_is_not_paired(self):
        ps = players(5)
        ps[0]["chiqdi"] = True
        pairs, bye = pair_round(standings(ps, []), 1)
        ids = {u for p in pairs for u in p}
        self.assertNotIn(1, ids)
        self.assertEqual(len(pairs), 2)
        self.assertIsNone(bye)


if __name__ == "__main__":
    unittest.main()

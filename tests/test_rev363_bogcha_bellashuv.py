"""REV363: bog'cha bellashuvi — savollar faqat hamma o'tgan darslardan (kesishma)."""
import random
from modules.bellashuv import bogcha_savollar


class Cur:
    def __init__(self, holat, testlar):
        self.holat, self.testlar, self.q = holat, testlar, None
    def execute(self, sql, args=()):
        self.q = (sql, args)
    def fetchall(self):
        sql, args = self.q
        if "bola_dars_holat" in sql:
            return [{"child_id": c, "dars_kod": k} for c, k in self.holat if c in args[0]]
        return [t for t in self.testlar if t["topic_code"] in args[0]]


def t(i, k, fan):
    return {"id": i, "topic_code": k, "option_a": "🐈 mushuk", "option_b": "🐕 it", "option_c": None, "option_d": None, "correct_answer": "A", "subject_name": fan}


def test_kesishma_va_aralash():
    holat = [(1, "A1"), (1, "A2"), (1, "M1"), (2, "A1"), (2, "M1")]
    testlar = [t(i, k, f) for i, (k, f) in enumerate([("A1", "Atrof")] * 3 + [("A2", "Atrof")] * 3 + [("M1", "Mantiq")] * 3)]
    ids, umumiy = bogcha_savollar(Cur(holat, testlar), [1, 2], 4, random.Random(2))
    assert umumiy == ["A1", "M1"] and len(ids) == 4
    assert all(testlar[i]["topic_code"] in ("A1", "M1") for i in ids)
    assert bogcha_savollar(Cur(holat, testlar), [1, 3], 4) == ([], [])

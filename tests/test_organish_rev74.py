import unittest

from modules import curriculum_scope as scope
from modules.dars_xonasi import placement_label


def row(code, name, lesson=None, tests=0):
    return {'testli_kodlar': [code] if tests else None, 'barcha_kodlar': [code], 'darsli_kodlar': lesson,
            'curriculum_scope_id': 1, 'grade': '5', 'subject_name': 'Matematika', 'subject_code': 'MAT',
            'dars_turi': None, 'nomi': name, 'savol_soni': tests, 'institution_type': 'maktab', 'kurs': None}


class OrganishTests(unittest.TestCase):
    def test_catalog_marks_topics_with_book_lessons_and_merges_codes(self):
        subjects = scope.group_catalog_rows([row('A1', 'Kasr', None, 3), row('A2', 'Kasr', ['A2']), row('B1', 'Nisbat')], False)
        topics = subjects[0]['sinflar'][0]['mavzular']
        kasr = next(t for t in topics if t['nomi'] == 'Kasr')
        self.assertTrue(kasr['dars_bor'])
        self.assertEqual(kasr['darsli_kodlar'], ['A2'])
        self.assertEqual(kasr['savol_soni'], 3)
        self.assertFalse(next(t for t in topics if t['nomi'] == 'Nisbat')['dars_bor'])

    def test_placement_says_who_will_see_the_lesson(self):
        self.assertEqual(placement_label({'institution_type': 'maktab', 'grade': '5', 'subject_name': 'Matematika'}), 'Maktab · 5-sinf · Matematika')
        self.assertIn('2-kurs', placement_label({'institution_type': 'universitet', 'institution_name': 'SamDPI', 'yonalish_nomi': "Boshlang'ich ta'lim", 'kurs': 2, 'semestr': 3, 'subject_name': 'BMKN'}))
        self.assertIn("ko'rmaydi", placement_label({'institution_type': None}))


if __name__ == '__main__':
    unittest.main()

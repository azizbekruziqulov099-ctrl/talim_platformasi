"""Admin lookup uses real catalog SQL; read filters never widen learner access."""
import unittest
import test_curriculum_catalog as fixtures


class AdminCatalogTests(unittest.TestCase):
    setUp = fixtures.CatalogTests.setUp
    topic = fixtures.CatalogTests.topic
    codes = fixtures.CatalogTests.codes

    def filtered(self, **changes):
        filters = dict(token='admin', institution_type='universitet', institution_id=11,
                       yonalish_id=7, talim_bosqichi='bakalavr', talim_shakli='kechki', talim_tili='uz', kurs=1)
        return self.catalog(**{**filters, **changes})

    def test_course_opens_both_semesters_all_lessons_and_groups(self):
        self.db.admin = True
        expected = set()
        for lesson in ('maruza', 'amaliy', 'seminar', 'laboratoriya'):
            for semester in (1, 2):
                for group in ('', '101'):
                    expected.add(self.topic(len(expected)+1, dars_turi=lesson, semestr=semester, guruh=group))
        self.assertEqual(self.codes(self.filtered()), expected)
        self.assertEqual(len(self.filtered()['fanlar']), 8)  # each lesson/group stays separate
        for subject in self.filtered()['fanlar']:
            self.assertEqual(subject['semestrlar'], [1, 2])

    def test_every_selected_dimension_excludes_other_catalogs(self):
        self.db.admin = True
        own = self.topic(1)
        differences = [dict(institution_id=12), dict(yonalish_id=8), dict(talim_bosqichi='magistr'),
                       dict(talim_shakli='kunduzgi'), dict(talim_tili='tj'), dict(kurs=2, semestr=3)]
        for index, changes in enumerate(differences, 2):
            self.topic(index, **changes)
        self.assertEqual(self.codes(self.filtered()), {own})

    def test_general_browse_keeps_institutes_and_courses_separate(self):
        self.db.admin = True
        a = self.topic(1)
        b = self.topic(2, institution_id=12)
        c = self.topic(3, kurs=2, semestr=3, grade='2 kurs')
        self.topic(4, institution_type='maktab', institution_id=0, grade='7')
        result = self.catalog(token='admin', institution_type='universitet')
        self.assertEqual(self.codes(result), {a, b, c})
        self.assertEqual(len({subject['kalit'] for subject in result['fanlar']}), 3)
        self.assertEqual({group['sinf'] for s in result['fanlar'] for group in s['sinflar']}, {'1 kurs', '2 kurs'})
        self.assertEqual({s['institution_id'] for s in result['fanlar']}, {11, 12})

    def test_manual_major_and_zero_institute_are_exact_not_wildcards(self):
        self.db.admin = True
        common = self.topic(1, institution_id=0, yonalish_id=0, yonalish_nomi='Mustaqil', guruh='')
        self.topic(2, institution_id=0, yonalish_id=0, yonalish_nomi='Boshqa', guruh='')
        self.topic(3, institution_id=11, yonalish_id=0, yonalish_nomi='Mustaqil')
        self.assertEqual(self.codes(self.filtered(institution_id=0, yonalish_id=0, yonalish_key='MUSTAQIL')), {common})

    def test_tajik_and_master_options_return_their_own_tests(self):
        self.db.admin = True
        self.topic(1)
        tajik = self.topic(2, talim_tili='tj')
        master = self.topic(3, talim_bosqichi='magistr', grade='1 kurs magistr')
        self.assertEqual(self.codes(self.filtered(talim_tili='tj')), {tajik})
        self.assertEqual(self.codes(self.filtered(talim_bosqichi='magistr')), {master})
        subject = self.filtered(talim_tili='tj')['fanlar'][0]
        self.assertEqual(subject['talim_tili'], 'tj')
        self.assertEqual(subject['yonalish_nomi'], 'Boshlang‘ich ta’lim')
        self.assertEqual(subject['talim_shakli'], 'kechki')

    def test_missing_or_deleted_tests_do_not_create_empty_course_cards(self):
        self.db.admin = True
        own = self.topic(1)
        self.db.add_scope(2, kurs=2, semestr=3)
        self.db.add_topic(2, grade='2 kurs')
        deleted = self.topic(3, kurs=3, semestr=5, grade='3 kurs')
        self.db.sql.execute('UPDATE dts_tree SET is_deleted=TRUE WHERE topic_code=?', (deleted,))
        self.assertEqual(self.codes(self.catalog(token='admin', institution_type='universitet')), {own})

    def test_general_or_forged_filters_never_expand_student_access(self):
        own = self.topic(1)
        self.topic(2, institution_id=12)
        self.topic(3, talim_tili='ru')
        self.assertEqual(self.codes(self.catalog(token='student', institution_type='universitet')), {own})
        for changes in ({'institution_id': 12}, {'talim_tili': 'ru'}, {'yonalish_id': 99}):
            self.assertEqual(self.codes(self.filtered(token='student', **changes)), set())

    def test_invalid_filters_fail_and_manual_name_is_parameterized(self):
        self.db.admin = True
        self.topic(1)
        for changes in ({'kurs': 0}, {'kurs': 7}, {'institution_id': -1}, {'talim_tili': 'xx'}, {'talim_shakli': 'invalid'}):
            with self.subTest(changes=changes), self.assertRaises(fixtures.HTTPException) as error:
                self.filtered(**changes)
            self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(self.codes(self.filtered(yonalish_id=0, yonalish_key="x' OR 1=1 --")), set())
        self.assertEqual(self.db.sql.execute('SELECT COUNT(*) FROM dts_tree').fetchone()[0], 1)

    def test_school_common_institution_filter_still_shows_tests(self):
        self.db.admin = True
        own = self.topic(1, institution_type='maktab', institution_id=0, grade='7')
        self.topic(2, institution_type='maktab', institution_id=11, grade='7')
        result = self.catalog(token='admin', institution_type='maktab', institution_id=0)
        self.assertEqual(self.codes(result), {own})


if __name__ == '__main__':
    unittest.main()

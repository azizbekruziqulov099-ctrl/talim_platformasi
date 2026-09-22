"""Language tags change reading, not the subject/topic identity during import."""
import sqlite3
import unittest
from modules.test_template_import import (
    authoritative_topic_scope, canonical_subject_name, comparison_text,
    exact_topic_matches_workbook_metadata, resolve_topic_code_for_scope,
    subject_matches,
)
import test_curriculum_roundtrip as fixtures
from test_curriculum_scope import HTTPException

SUBJECT = 'ТЕОРИЯ ВЕРОЯТНОСТЕЙ И МАТЕМАТИЧЕСКАЯ СТАТИСТИКА.'

class TaggedMetadataTests(unittest.TestCase):
    def test_subject_reading_tags_do_not_change_identity(self):
        for tag in ('ru','RU','uz','en'):
            tagged=f'[{tag}]{SUBJECT}[/{tag}]'
            self.assertEqual(canonical_subject_name(tagged),canonical_subject_name(SUBJECT))
            self.assertTrue(subject_matches(SUBJECT,tagged))
        self.assertFalse(subject_matches(SUBJECT,'[ru]ФИЗИКА[/ru]'))
        self.assertEqual(comparison_text('[ru]RUSTILI[/ru]'),'RUSTILI')
        self.assertEqual(comparison_text('[lat]x+y[/lat]'),'[lat]x+y[/lat]')

    def test_tagged_metadata_is_accepted_without_changing_stored_source(self):
        code='4 kurs-01-07-01-01-01-001'
        info={'grade':'4 kurs','subject_name':f'[ru]{SUBJECT}[/ru]','mavzu_name':'[ru]Множества[/ru]'}
        selected,errors=authoritative_topic_scope({code:info},'4 kurs',SUBJECT)
        self.assertEqual(errors,[]);self.assertEqual(set(selected),{code})
        self.assertEqual(selected[code]['subject_name'],info['subject_name'])
        self.assertEqual(selected[code]['mavzu_name'],info['mavzu_name'])

    def test_mixed_tagged_and_plain_subject_labels_are_one_subject_not_two(self):
        meta={f'4 kurs-01-07-01-01-{i:02d}-001':{'grade':'4 kurs','subject_name':name}
              for i,name in enumerate([SUBJECT,f'[ru]{SUBJECT}[/ru]'],1)}
        selected,errors=authoritative_topic_scope(meta,'4 kurs')
        self.assertEqual(errors,[]);self.assertEqual(len(selected),2)
        meta['4 kurs-01-07-01-01-03-001']={'grade':'4 kurs','subject_name':'[ru]ФИЗИКА[/ru]'}
        self.assertTrue(authoritative_topic_scope(meta,'4 kurs')[1])

    def test_remapping_uses_tag_free_topic_names_and_still_requires_one_match(self):
        raw='4 kurs-01-07-01-01-01-001'
        db=[{'topic_code':'new-code','grade':'4 kurs','subject_name':SUBJECT,'mavzu_name':'Множества','quarter':'07'}]
        metadata={raw:{'grade':'4 kurs','subject_name':f'[ru]{SUBJECT}[/ru]','mavzu_name':'[ru]Множества[/ru]','quarter':'07'}}
        self.assertEqual(resolve_topic_code_for_scope(raw,'4 kurs',SUBJECT,db,metadata),'new-code')
        self.assertTrue(exact_topic_matches_workbook_metadata(db[0],metadata[raw],'4 kurs',SUBJECT))
        db.append({**db[0],'topic_code':'another-code'})
        self.assertIsNone(resolve_topic_code_for_scope(raw,'4 kurs',SUBJECT,db,metadata))

class TaggedReplacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixtures.WorkbookRoundTripTests.setUpClass()
    def setUp(self):
        self.engine=fixtures.WorkbookRoundTripTests()
        self.engine.setUp();self.addCleanup(self.engine.doCleanups)
        scope=self.engine.scope(talim_tili='ru',kurs=4,semestr=7,dars_turi='amaliy')
        topics=self.engine.topic_template(scope,grade='4 kurs',subject=SUBJECT,topics='7 / Множества\n7 / Числа')
        self.engine.import_topics(topics)
        self.codes=[row[0] for row in self.engine.db.sql.execute('SELECT topic_code FROM dts_tree ORDER BY topic_code')]
        self.workbook=self.engine.fill(self.engine.build_test_template(self.codes))
        self.engine.import_tests(self.workbook,grade='4 kurs',subject=SUBJECT)
        for row in self.workbook['MALUMOT'].iter_rows(min_row=2):
            for cell in row[3:9]:
                if isinstance(cell.value,str) and cell.value:cell.value=f'[ru]{cell.value}[/ru]'
        self.workbook['VARAQ_XARITA'].cell(2,2,f'[ru]{SUBJECT}[/ru]')
        for row in self.workbook['TESTLAR'].iter_rows(min_row=2):
            for column in range(3,10):
                row[column].value=f'[ru]{row[column].value if row[column].value is not None else "Объяснение."}[/ru]'

    def test_reimport_replaces_old_untagged_tests_without_duplicates_and_preserves_tags(self):
        for run in range(2):
            result=self.engine.import_tests(self.workbook,grade='4 kurs',subject=SUBJECT)
            self.assertEqual(result['saved'],2);self.assertEqual(result['duplicates'],0)
            self.assertEqual(result['almashtirishda_ochirilgan_eski_test_soni'],2)
            rows=self.engine.rows();self.assertEqual(len(rows),2)
            for row in rows:
                for field in ('question','option_a','option_b','option_c','option_d','correct_answer','explanation'):
                    self.assertTrue(row[field].startswith('[ru]'));self.assertTrue(row[field].endswith('[/ru]'))
        subjects={row[0] for row in self.engine.db.sql.execute('SELECT subject_name FROM dts_tree')}
        self.assertEqual(subjects,{SUBJECT})

    def test_all_subjects_mode_accepts_tagged_map(self):
        result=self.engine.import_tests(self.workbook,grade='4 kurs')
        self.assertEqual(result['saved'],2);self.assertEqual(len(self.engine.rows()),2)

    def test_other_program_is_still_rejected_without_replacing_anything(self):
        self.engine.scope(2,talim_tili='ru',kurs=4,semestr=7,dars_turi='seminar')
        before=self.engine.rows()
        with self.assertRaises(HTTPException):self.engine.import_tests(self.workbook,grade='4 kurs',subject=SUBJECT,id=2)
        self.assertEqual(self.engine.rows(),before)

    def test_write_failure_after_deletion_rolls_back_old_questions(self):
        before=self.engine.rows()
        self.engine.db.sql.execute("CREATE TRIGGER reject_new BEFORE INSERT ON generated_tests WHEN NEW.question LIKE '[ru]%' BEGIN SELECT RAISE(ABORT,'write failure'); END")
        self.engine.db.commit()
        with self.assertRaisesRegex(sqlite3.IntegrityError,'write failure'):
            self.engine.import_tests(self.workbook,grade='4 kurs',subject=SUBJECT)
        self.assertEqual(self.engine.rows(),before)

if __name__=='__main__':unittest.main()

-- Additive, repeatable migration. No test or topic codes are deleted/renamed.
BEGIN;
SELECT pg_advisory_xact_lock(20260920, 71);
CREATE TABLE IF NOT EXISTS curriculum_scopes (
 id BIGSERIAL PRIMARY KEY,
 scope_key TEXT NOT NULL UNIQUE,
 institution_type TEXT NOT NULL CHECK (institution_type IN ('maktab','universitet','bogcha','markaz')),
 institution_id BIGINT NOT NULL CHECK (institution_id >= 0),
 institution_name TEXT NOT NULL DEFAULT '',
 talim_bosqichi TEXT NOT NULL DEFAULT '',
 yonalish_id BIGINT NOT NULL DEFAULT 0 CHECK (yonalish_id >= 0),
 yonalish_nomi TEXT NOT NULL DEFAULT '',
 yonalish_key TEXT NOT NULL DEFAULT '',
 talim_shakli TEXT NOT NULL DEFAULT '',
 talim_tili TEXT NOT NULL DEFAULT '',
 kurs SMALLINT NOT NULL DEFAULT 0,
 semestr SMALLINT NOT NULL DEFAULT 0,
 guruh TEXT NOT NULL DEFAULT '',
 dars_turi TEXT NOT NULL DEFAULT '',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CHECK (institution_id > 0 OR institution_type='maktab'),
 CHECK (institution_type <> 'universitet' OR (
   institution_id > 0 AND talim_bosqichi IN ('bakalavr','magistr')
   AND yonalish_key <> '' AND talim_shakli IN ('kunduzgi','kechki','sirtqi','masofaviy','umumiy')
   AND talim_tili IN ('uz','ru','tj','en','kk','kz')
   AND kurs BETWEEN 1 AND CASE WHEN talim_bosqichi='magistr' THEN 2 ELSE 6 END
   AND semestr IN (kurs*2-1,kurs*2)
   AND dars_turi IN ('maruza','amaliy','seminar','laboratoriya'))),
 CHECK (institution_type = 'universitet' OR (talim_bosqichi='' AND kurs=0 AND semestr=0 AND dars_turi=''))
);
INSERT INTO curriculum_scopes(scope_key,institution_type,institution_id,institution_name)
VALUES('school-common','maktab',0,'Maktab — umumiy katalog') ON CONFLICT(scope_key) DO NOTHING;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS subject_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS bob_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS bolim_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS mavzu_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS kichik_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS dars_turi TEXT;
ALTER TABLE dts_tree ALTER COLUMN dars_turi DROP NOT NULL;
ALTER TABLE dts_tree ALTER COLUMN dars_turi DROP DEFAULT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS curriculum_scope_id BIGINT REFERENCES curriculum_scopes(id);
CREATE TABLE IF NOT EXISTS curriculum_legacy_backup (
 topic_code TEXT PRIMARY KEY, old_row JSONB NOT NULL, saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Only unambiguously numbered SCHOOL grades are migrated automatically.
INSERT INTO curriculum_legacy_backup(topic_code,old_row)
SELECT topic_code,to_jsonb(d) FROM dts_tree d
WHERE curriculum_scope_id IS NULL AND grade ~ '^(1[01]|[1-9])$' AND COALESCE(to_jsonb(d)->>'institution_type','maktab') IN ('maktab','school') AND topic_code IS NOT NULL
ON CONFLICT(topic_code) DO NOTHING;
UPDATE dts_tree d SET curriculum_scope_id=(SELECT id FROM curriculum_scopes WHERE scope_key='school-common'),dars_turi=NULL
WHERE curriculum_scope_id IS NULL AND grade ~ '^(1[01]|[1-9])$' AND COALESCE(to_jsonb(d)->>'institution_type','maktab') IN ('maktab','school');
-- Legacy institute/club rows remain unassigned; an admin explicitly maps them.
CREATE INDEX IF NOT EXISTS ix_dts_curriculum_scope ON dts_tree(curriculum_scope_id,grade,subject_name,dars_turi) WHERE is_deleted=FALSE;
CREATE INDEX IF NOT EXISTS ix_curriculum_profile ON curriculum_scopes(institution_type,institution_id,talim_bosqichi,kurs,semestr,talim_shakli,talim_tili);
CREATE TABLE IF NOT EXISTS talaba_profillari(
 user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
 universitet_id INTEGER NOT NULL REFERENCES universitetlar(id) ON DELETE CASCADE,
 yonalish_id BIGINT, yonalish_nomi TEXT NOT NULL,
 talim_bosqichi TEXT NOT NULL CHECK(talim_bosqichi IN ('bakalavr','magistr')),
 kurs SMALLINT NOT NULL CHECK(kurs BETWEEN 1 AND 6), guruh TEXT NOT NULL,
 talim_shakli TEXT NOT NULL,talim_tili TEXT NOT NULL,semestr SMALLINT,
 qoshilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
DO $$ BEGIN
 IF to_regclass('public.talaba_profillari') IS NOT NULL THEN
  ALTER TABLE talaba_profillari ADD COLUMN IF NOT EXISTS semestr SMALLINT;
 END IF;
END $$;
-- For legacy SCHOOL writers only: preserve the common school catalog. A blank
-- institute/center scope never falls back to a school or an all-institutions scope.
CREATE OR REPLACE FUNCTION curriculum_dts_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE s curriculum_scopes%ROWTYPE; expected_grade TEXT;
BEGIN
 IF NEW.curriculum_scope_id IS NULL AND NEW.grade ~ '^(1[01]|[1-9])$' AND COALESCE(to_jsonb(NEW)->>'institution_type','maktab') IN ('maktab','school') THEN
  SELECT id INTO NEW.curriculum_scope_id FROM curriculum_scopes WHERE scope_key='school-common';
 END IF;
 IF NEW.curriculum_scope_id IS NULL THEN RETURN NEW; END IF;
 SELECT * INTO s FROM curriculum_scopes WHERE id=NEW.curriculum_scope_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Curriculum scope not found'; END IF;
 IF s.institution_type='universitet' THEN
  expected_grade := s.kurs::text || ' kurs' || CASE WHEN s.talim_bosqichi='magistr' THEN ' magistr' ELSE '' END;
  IF NEW.grade <> expected_grade THEN RAISE EXCEPTION 'Course and curriculum scope do not match'; END IF;
  IF COALESCE(NEW.dars_turi,'') <> s.dars_turi THEN RAISE EXCEPTION 'Lesson type and curriculum scope do not match'; END IF;
 ELSE
  IF s.institution_type='maktab' AND NEW.grade !~ '^(1[01]|[1-9])$' THEN
   RAISE EXCEPTION 'School curriculum requires a school grade';
  END IF;
  NEW.dars_turi := NULL;
 END IF;
 RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS curriculum_dts_scope_guard ON dts_tree;
CREATE TRIGGER curriculum_dts_scope_guard BEFORE INSERT OR UPDATE ON dts_tree FOR EACH ROW EXECUTE FUNCTION curriculum_dts_guard();
CREATE TABLE IF NOT EXISTS curriculum_explanations (
 curriculum_scope_id BIGINT NOT NULL REFERENCES curriculum_scopes(id),
 sinf TEXT NOT NULL, fan TEXT NOT NULL, mavzu_nomi TEXT NOT NULL,
 tushuntirish TEXT NOT NULL, yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 PRIMARY KEY(curriculum_scope_id,sinf,fan,mavzu_nomi)
);
DO $$ BEGIN
 IF to_regclass('public.mavzu_tushuntirishlari') IS NOT NULL THEN
  INSERT INTO curriculum_explanations(curriculum_scope_id,sinf,fan,mavzu_nomi,tushuntirish)
  SELECT s.id,m.sinf,m.fan,m.mavzu_nomi,m.tushuntirish FROM mavzu_tushuntirishlari m
  CROSS JOIN curriculum_scopes s WHERE s.scope_key='school-common' AND m.sinf ~ '^(1[01]|[1-9])$'
  ON CONFLICT DO NOTHING;
 END IF;
END $$;
COMMIT;

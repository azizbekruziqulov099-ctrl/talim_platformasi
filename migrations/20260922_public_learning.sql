-- Repeatable, additive support for independent learners. Existing institution
-- curricula, membership records, topic codes and tests are not reassigned.
BEGIN;
SELECT pg_advisory_xact_lock(20260922, 53);
ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_learning_profile JSONB NOT NULL DEFAULT '{}'::jsonb;
DO $$ DECLARE item RECORD; BEGIN
  FOR item IN SELECT conname FROM pg_constraint
    WHERE conrelid='curriculum_scopes'::regclass AND contype='c'
      AND pg_get_constraintdef(oid) LIKE '%institution_id > 0%'
      AND conname NOT IN ('curriculum_public_institution','curriculum_public_university')
  LOOP EXECUTE format('ALTER TABLE curriculum_scopes DROP CONSTRAINT %I', item.conname); END LOOP;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='curriculum_scopes'::regclass AND conname='curriculum_public_institution') THEN
    ALTER TABLE curriculum_scopes ADD CONSTRAINT curriculum_public_institution
      CHECK (institution_id > 0 OR institution_type='maktab' OR (institution_type='universitet' AND guruh=''));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='curriculum_scopes'::regclass AND conname='curriculum_public_university') THEN
    ALTER TABLE curriculum_scopes ADD CONSTRAINT curriculum_public_university CHECK (institution_type <> 'universitet' OR (
      institution_id >= 0 AND talim_bosqichi IN ('bakalavr','magistr') AND yonalish_key <> ''
      AND talim_shakli IN ('kunduzgi','kechki','sirtqi','masofaviy','umumiy')
      AND talim_tili IN ('uz','ru','tj','en','kk','kz')
      AND kurs BETWEEN 1 AND CASE WHEN talim_bosqichi='magistr' THEN 2 ELSE 6 END
      AND semestr IN (kurs*2-1,kurs*2) AND dars_turi IN ('maruza','amaliy','seminar','laboratoriya')
      AND (institution_id > 0 OR (guruh='' AND yonalish_id=0))));
  END IF;
END $$;
COMMIT;

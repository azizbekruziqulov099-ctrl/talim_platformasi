-- REV80: umumiy bog'cha katalogi (2–7 yosh). Qo'shimcha, qayta ishga tushirish xavfsiz.
BEGIN;
SELECT pg_advisory_xact_lock(20260929, 17);
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='curriculum_scopes'::regclass AND conname='curriculum_public_institution'
             AND pg_get_constraintdef(oid) NOT LIKE '%bogcha%') THEN
    ALTER TABLE curriculum_scopes DROP CONSTRAINT curriculum_public_institution;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='curriculum_scopes'::regclass AND conname='curriculum_public_institution') THEN
    ALTER TABLE curriculum_scopes ADD CONSTRAINT curriculum_public_institution
      CHECK (institution_id > 0 OR institution_type='maktab' OR (institution_type IN ('universitet','bogcha') AND guruh=''));
  END IF;
END $$;
INSERT INTO curriculum_scopes(scope_key,institution_type,institution_id,institution_name)
VALUES('kindergarten-common','bogcha',0,'Bog‘cha — umumiy katalog (2–7 yosh)') ON CONFLICT(scope_key) DO NOTHING;
COMMIT;

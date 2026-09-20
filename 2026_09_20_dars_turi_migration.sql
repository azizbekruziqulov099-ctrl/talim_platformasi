-- Eski PostgreSQL bazasi uchun bir martalik xavfsiz migratsiya.
-- Backend ham buni avtomatik bajaradi; bu fayl qo'lda ishlatish uchun zaxira.
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS subject_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS bob_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS bolim_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS mavzu_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS kichik_code TEXT;
ALTER TABLE dts_tree ADD COLUMN IF NOT EXISTS dars_turi TEXT NOT NULL DEFAULT '';

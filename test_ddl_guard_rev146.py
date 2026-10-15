"""REV146: deploy paytida allaqachon bor ustun/indeks uchun DDL qulf so'ramaydi (kirish osilib qolmaydi)."""
import unittest

from platform_core.ddl_guard import redundant, split_clauses, split_sql

COLS = {("users", "kabutar_id"), ("users", "name"), ("public.users", "kabutar_id")}
IDX = {"uq_users_x"}
col = lambda t, c: (t, c) in COLS
idx = lambda n: n in IDX


class DdlGuardTests(unittest.TestCase):
    def test_split_respects_quotes_dollars_comments(self):
        sql = "CREATE TABLE a(x text default 'a;b');\nALTER TABLE a ADD COLUMN IF NOT EXISTS y INT; DO $$ BEGIN PERFORM 1; END $$; -- izoh; bu\nSELECT 1"
        parts = split_sql(sql)
        self.assertEqual(len(parts), 4)
        self.assertIn("'a;b'", parts[0])
        self.assertIn("PERFORM 1; END", parts[2])

    def test_existing_column_is_skipped_new_is_kept(self):
        self.assertTrue(redundant("ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_id TEXT", col, idx))
        self.assertTrue(redundant('ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "name" TEXT DEFAULT \'a,b\'', col, idx))
        self.assertTrue(redundant("ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_id TEXT, ADD COLUMN IF NOT EXISTS name TEXT", col, idx))
        self.assertFalse(redundant("ALTER TABLE users ADD COLUMN IF NOT EXISTS yangi TEXT", col, idx))
        self.assertFalse(redundant("ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_id TEXT, ADD COLUMN IF NOT EXISTS yangi INT", col, idx))
        # boshqa turdagi o'zgartirish — har doim bajariladi
        self.assertFalse(redundant("ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_id TEXT, ALTER COLUMN name SET NOT NULL", col, idx))
        self.assertFalse(redundant("ALTER TABLE users DROP COLUMN IF EXISTS eski", col, idx))
        self.assertFalse(redundant("UPDATE users SET name='x'", col, idx))

    def test_index(self):
        self.assertTrue(redundant("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_x ON users(maktab_id) WHERE x IS NOT NULL", col, idx))
        self.assertFalse(redundant("CREATE INDEX IF NOT EXISTS yangi_idx ON users(x)", col, idx))
        self.assertFalse(redundant("CREATE INDEX yangi_idx ON users(x)", col, idx))

    def test_clauses(self):
        self.assertEqual(len(split_clauses("ADD COLUMN IF NOT EXISTS a NUMERIC(5,2), ADD COLUMN IF NOT EXISTS b TEXT DEFAULT 'x,y'")), 2)


if __name__ == "__main__":
    unittest.main()

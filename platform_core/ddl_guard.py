"""REV146: server qayta ishga tushganda bazani bloklamaydigan kursor.

Muammo: har deployda o'nlab modul ishga tushishda ``ALTER TABLE users ADD COLUMN IF NOT EXISTS ...`` va
``CREATE INDEX IF NOT EXISTS ...`` buyruqlarini qayta bajaradi. PostgreSQL ``ALTER TABLE`` uchun ustun allaqachon
bor bo'lsa ham AVVAL jadvalga eng kuchli qulf (ACCESS EXCLUSIVE) so'raydi. Ishlab turgan eski server jadvalni
band qilib tursa, bu qulf kutadi — kutayotgan paytda ``users`` jadvaliga keladigan BARCHA so'rovlar (kirish,
/auth/men, ro'yxatdan o'tish) uning orqasida navbatda qoladi: sayt kirishda «osilib» qoladi, yangi server esa
``lock_timeout`` bilan yiqilib, healthcheck'dan o'tolmaydi.

Yechim: bunday buyruqdan oldin katalogdan (qulfsiz) tekshiramiz — ustun/indeks allaqachon bor bo'lsa, buyruq
umuman yuborilmaydi. Yangi ustun haqiqatan kerak bo'lgandagina ALTER bajariladi (bir marta).
"""
from __future__ import annotations

import re
import threading
import time

import psycopg2.extras

# Haqiqatan yangi ustun/indeks qo'shilganda qulf ko'pi bilan shuncha kutiladi (jonli so'rovlar navbatda qolmasin).
DDL_LOCK_TIMEOUT = "3s"

_ADD_COL = re.compile(r'ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+"?([A-Za-z_][A-Za-z0-9_]*)"?', re.I)
_ALTER_HEAD = re.compile(r'^\s*ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?((?:"?[A-Za-z_][A-Za-z0-9_]*"?\.)?"?[A-Za-z_][A-Za-z0-9_]*"?)\s+(.*)$', re.I | re.S)
_INDEX = re.compile(r'^\s*CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?IF\s+NOT\s+EXISTS\s+"?([A-Za-z_][A-Za-z0-9_]*)"?\s+ON\s', re.I)


def split_sql(text: str) -> list[str]:
    """SQL matnini «;» bo'yicha bo'ladi — qo'shtirnoq, $$…$$ va -- izohlar ichidagi «;» hisobga olinmaydi."""
    out, buf, i, n = [], [], 0, len(text)
    quote = None          # "'" | '"' | "$tag$"
    while i < n:
        ch = text[i]
        if quote:
            if quote in ("'", '"'):
                buf.append(ch)
                if ch == quote:
                    if i + 1 < n and text[i + 1] == quote:   # '' — qochirilgan qo'shtirnoq
                        buf.append(text[i + 1]); i += 2; continue
                    quote = None
                i += 1; continue
            if text.startswith(quote, i):
                buf.append(quote); i += len(quote); quote = None; continue
            buf.append(ch); i += 1; continue
        if ch in ("'", '"'):
            quote = ch; buf.append(ch); i += 1; continue
        if ch == "$":
            m = re.match(r"\$[A-Za-z_]*\$", text[i:])
            if m:
                quote = m.group(0); buf.append(quote); i += len(quote); continue
        if ch == "-" and text.startswith("--", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            buf.append(text[i:j]); i = j; continue
        if ch == ";":
            out.append("".join(buf)); buf = []; i += 1; continue
        buf.append(ch); i += 1
    out.append("".join(buf))
    return [s for s in out if s.strip()]


def _strip_comments(stmt: str) -> str:
    return re.sub(r"--[^\n]*", "", stmt).strip()


def redundant(stmt: str, column_exists, index_exists) -> bool:
    """Buyruq hech narsa o'zgartirmaydimi (hamma ustun / indeks allaqachon bor)."""
    s = _strip_comments(stmt)
    m = _INDEX.match(s)
    if m:
        return bool(index_exists(m.group(1)))
    m = _ALTER_HEAD.match(s)
    if not m:
        return False
    table, rest = m.group(1).replace('"', ""), m.group(2)
    # faqat «ADD COLUMN IF NOT EXISTS …» bandlaridan iborat bo'lsa (boshqa o'zgartirish bo'lsa — tegmaymiz)
    clauses = [c.strip() for c in split_clauses(rest)]
    if not clauses or not all(_ADD_COL.match(c) for c in clauses):
        return False
    return all(column_exists(table, _ADD_COL.match(c).group(1)) for c in clauses)


def split_clauses(rest: str) -> list[str]:
    """«ADD COLUMN a INT, ADD COLUMN b TEXT DEFAULT 'x,y'» → bandlar (qavs va qo'shtirnoq ichidagi vergul emas)."""
    out, buf, depth, quote = [], [], 0, None
    for ch in rest:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append("".join(buf)); buf = []; continue
        buf.append(ch)
    out.append("".join(buf))
    return [c for c in out if c.strip()]


class XavfsizCursor(psycopg2.extras.RealDictCursor):
    """RealDictCursor + keraksiz (allaqachon bajarilgan) DDL qulf so'ramasdan o'tkazib yuboriladi."""

    def _column_exists(self, table, column):
        super().execute("SELECT 1 AS ok FROM pg_attribute WHERE attrelid = to_regclass(%s) AND attname = %s "
                        "AND attnum > 0 AND NOT attisdropped", (table, column))
        return super().fetchone() is not None

    def _index_exists(self, name):
        super().execute("SELECT to_regclass(%s) IS NOT NULL AS ok", (name,))
        row = super().fetchone()
        return bool(row and row["ok"])

    def execute(self, query, vars=None):
        if vars is None and isinstance(query, str) and ("ALTER" in query.upper() or "INDEX" in query.upper()):
            try:
                parts = split_sql(query)
                keep = [p for p in parts if not redundant(p, self._column_exists, self._index_exists)]
            except psycopg2.Error:
                raise
            except Exception:   # tahlil qila olmasak — asl buyruq o'zgarishsiz
                keep = None
            if keep is not None and len(keep) != len(parts):
                if not keep:
                    return None
                query = ";\n".join(keep)
            if keep and any(_INDEX.match(_strip_comments(p)) or _ALTER_HEAD.match(_strip_comments(p)) for p in keep):
                # yangi ustun/indeks: qulf uzoq kutilmaydi — band bo'lsa tez xato beradi va keyinroq qayta uriniladi
                super().execute(f"SET LOCAL lock_timeout = '{DDL_LOCK_TIMEOUT}'")
        return super().execute(query, vars)


class LazyMigration:
    """Modul jadvallari birinchi so'rovda yaratiladi. REV146: muvaffaqiyatsiz bo'lsa — har so'rovda qayta urinib
    serverni qotirmaydi (60 soniya kutadi), so'rov esa davom etadi (jadvallar odatda allaqachon bor)."""

    def __init__(self, name: str, backoff: float = 60.0):
        self.name, self.backoff = name, backoff
        self.ok = False
        self._next = 0.0
        self._lock = threading.Lock()

    def run(self, conn, cur, fn) -> None:
        if self.ok or time.monotonic() < self._next:
            return
        if not self._lock.acquire(blocking=False):   # boshqa so'rov hozir migratsiya qilyapti — kutmaymiz
            return
        try:
            if self.ok:
                return
            fn(cur)
            conn.commit()
            self.ok = True
        except Exception as exc:   # qulf band / vaqtincha xato — keyinroq
            try:
                conn.rollback()
            except Exception:
                pass
            self._next = time.monotonic() + self.backoff
            print(f"[MIGRATSIYA-KEYINROQ] {self.name}: {type(exc).__name__}: {str(exc)[:160]}", flush=True)
        finally:
            self._lock.release()

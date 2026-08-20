"""SamTM V18.24 — adminning muassasa arxivi va o'chirish paroli.

Eski ``MUASSASA_OCHIRISH_PAROLI`` Railway qiymati birinchi sozlama
yangilanguncha ishlashda davom etadi. Yangi qiymat ochiq matnda emas,
PBKDF2-HMAC-SHA256 xeshi sifatida bazada saqlanadi.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from psycopg2 import sql


ARCHIVE_RETENTION_DAYS = 365
PASSWORD_ITERATIONS = 260_000
PASSWORD_ENV_NAME = "MUASSASA_OCHIRISH_PAROLI"

INSTITUTION_TABLES = {
    "maktab": "maktablar",
    "bogcha": "bogchalar",
    "markaz": "oquv_markazlari",
    "universitet": "universitetlar",
}

INSTITUTION_LABELS = {
    "maktab": "Maktab",
    "bogcha": "Bog'cha",
    "markaz": "O'quv markazi",
    "universitet": "Universitet",
}


def _normalize_legacy_password(value: Optional[str]) -> str:
    """Railway'da tasodifan `'1234'` yoki `"1234"` yozilsa ham tanish."""
    normalized = (value or "").strip()
    if (
        len(normalized) >= 2
        and normalized[0] == normalized[-1]
        and normalized[0] in ("'", '"')
    ):
        normalized = normalized[1:-1].strip()
    return normalized


def _validate_new_password(password: str) -> str:
    normalized = _normalize_legacy_password(password)
    if len(normalized) != 4 or not normalized.isdigit():
        raise HTTPException(
            status_code=400,
            detail="O'chirish paroli aynan 4 ta raqamdan iborat bo'lishi kerak",
        )
    return normalized


def _hash_password(password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return salt.hex(), digest.hex()


def _password_matches(password: str, salt_hex: str, expected_hash: str) -> bool:
    _, actual_hash = _hash_password(password, salt_hex)
    return hmac.compare_digest(actual_hash, expected_hash)


def _institution_table(institution_type: str) -> str:
    table = INSTITUTION_TABLES.get((institution_type or "").strip().lower())
    if not table:
        raise HTTPException(status_code=400, detail="Noto'g'ri muassasa turi")
    return table


def ensure_institution_archive_columns(cur, table_name: str) -> None:
    """Legacy jadval keyinroq yaratilgan bo'lsa ham arxiv ustunlarini qo'shadi."""
    if table_name not in INSTITUTION_TABLES.values():
        raise ValueError("Muassasa jadvali ruxsat etilmagan")
    cur.execute("SELECT to_regclass(%s) AS table_name", (f"public.{table_name}",))
    row = cur.fetchone()
    if not row or not row["table_name"]:
        return
    cur.execute(
        sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ").format(
            sql.Identifier(table_name)
        )
    )
    cur.execute(
        sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS archive_purge_at TIMESTAMPTZ").format(
            sql.Identifier(table_name)
        )
    )
    cur.execute(
        sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS archived_by_admin_id BIGINT").format(
            sql.Identifier(table_name)
        )
    )
    cur.execute(
        sql.SQL("ALTER TABLE {} ADD COLUMN IF NOT EXISTS archive_record_id BIGINT").format(
            sql.Identifier(table_name)
        )
    )


def institution_is_archived(cur, institution_type: str, institution_id: int) -> bool:
    table_name = _institution_table(institution_type)
    cur.execute("SELECT to_regclass(%s) AS table_name", (f"public.{table_name}",))
    table_row = cur.fetchone()
    if not table_row or not table_row["table_name"]:
        return False
    ensure_institution_archive_columns(cur, table_name)
    cur.execute(
        sql.SQL("SELECT archived_at IS NOT NULL AS archived FROM {} WHERE id=%s").format(
            sql.Identifier(table_name)
        ),
        (institution_id,),
    )
    row = cur.fetchone()
    return bool(row and row["archived"])


def _ensure_schema(cur) -> None:
    cur.execute(
        """CREATE TABLE IF NOT EXISTS admin_institution_security(
            singleton_id SMALLINT PRIMARY KEY DEFAULT 1 CHECK(singleton_id=1),
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            password_version INTEGER NOT NULL DEFAULT 1,
            updated_by_admin_id BIGINT,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS admin_destructive_action_attempts(
            admin_user_id BIGINT PRIMARY KEY,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TIMESTAMPTZ,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS institution_archives(
            id BIGSERIAL PRIMARY KEY,
            institution_type TEXT NOT NULL CHECK(
                institution_type IN ('maktab','bogcha','markaz','universitet')
            ),
            institution_id INTEGER NOT NULL,
            institution_name TEXT NOT NULL,
            archived_by_admin_id BIGINT NOT NULL,
            archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            purge_after TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '365 days'),
            archive_reason TEXT,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            restored_at TIMESTAMPTZ,
            restored_by_admin_id BIGINT,
            purged_at TIMESTAMPTZ,
            purge_error TEXT
        )"""
    )
    cur.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS ux_institution_archives_active
           ON institution_archives(institution_type,institution_id)
           WHERE restored_at IS NULL AND purged_at IS NULL"""
    )
    cur.execute(
        """CREATE INDEX IF NOT EXISTS ix_institution_archives_retention
           ON institution_archives(purge_after)
           WHERE restored_at IS NULL AND purged_at IS NULL"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS institution_security_audit(
            id BIGSERIAL PRIMARY KEY,
            admin_user_id BIGINT NOT NULL,
            action TEXT NOT NULL,
            institution_type TEXT,
            institution_id INTEGER,
            archive_id BIGINT,
            details JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )"""
    )
    for table_name in INSTITUTION_TABLES.values():
        ensure_institution_archive_columns(cur, table_name)


def _security_status(cur) -> dict:
    cur.execute(
        """SELECT password_version,updated_at,updated_by_admin_id
           FROM admin_institution_security WHERE singleton_id=1"""
    )
    row = cur.fetchone()
    legacy_configured = bool(
        _normalize_legacy_password(os.getenv(PASSWORD_ENV_NAME, ""))
    )
    if row:
        return {
            "configured": True,
            "source": "settings",
            "password_version": int(row["password_version"]),
            "updated_at": row["updated_at"],
            "updated_by_admin_id": row["updated_by_admin_id"],
            "legacy_password_available": legacy_configured,
        }
    return {
        "configured": legacy_configured,
        "source": "railway" if legacy_configured else "not_configured",
        "password_version": 0,
        "updated_at": None,
        "updated_by_admin_id": None,
        "legacy_password_available": legacy_configured,
    }


def _check_rate_limit(cur, admin_user_id: int) -> None:
    cur.execute(
        """SELECT failed_attempts,locked_until
           FROM admin_destructive_action_attempts
           WHERE admin_user_id=%s FOR UPDATE""",
        (admin_user_id,),
    )
    row = cur.fetchone()
    now = datetime.now(timezone.utc)
    if row and row["locked_until"] and row["locked_until"] > now:
        seconds = max(1, int((row["locked_until"] - now).total_seconds()))
        raise HTTPException(
            status_code=429,
            detail=f"Ko'p marta noto'g'ri parol kiritildi. {seconds} soniyadan keyin qayta urinib ko'ring",
        )


def _record_wrong_password(conn, cur, admin_user_id: int) -> None:
    cur.execute(
        """INSERT INTO admin_destructive_action_attempts(
               admin_user_id,failed_attempts,locked_until,updated_at
           ) VALUES(%s,1,NULL,NOW())
           ON CONFLICT(admin_user_id) DO UPDATE SET
             failed_attempts=admin_destructive_action_attempts.failed_attempts+1,
             locked_until=CASE
               WHEN admin_destructive_action_attempts.failed_attempts+1 >= 5
               THEN NOW()+INTERVAL '15 minutes'
               ELSE admin_destructive_action_attempts.locked_until
             END,
             updated_at=NOW()""",
        (admin_user_id,),
    )
    conn.commit()


def _reset_wrong_passwords(cur, admin_user_id: int) -> None:
    cur.execute(
        """INSERT INTO admin_destructive_action_attempts(
               admin_user_id,failed_attempts,locked_until,updated_at
           ) VALUES(%s,0,NULL,NOW())
           ON CONFLICT(admin_user_id) DO UPDATE SET
             failed_attempts=0,locked_until=NULL,updated_at=NOW()""",
        (admin_user_id,),
    )


def _verify_deletion_password(conn, cur, admin_user_id: int, password: str) -> None:
    _check_rate_limit(cur, admin_user_id)
    normalized = _normalize_legacy_password(password)
    cur.execute(
        """SELECT password_salt,password_hash
           FROM admin_institution_security WHERE singleton_id=1"""
    )
    row = cur.fetchone()
    if row:
        correct = _password_matches(
            normalized,
            row["password_salt"],
            row["password_hash"],
        )
    else:
        legacy = _normalize_legacy_password(os.getenv(PASSWORD_ENV_NAME, ""))
        if not legacy:
            raise HTTPException(
                status_code=409,
                detail="Avval Profil va sozlamalarda muassasa o'chirish parolini belgilang",
            )
        correct = hmac.compare_digest(normalized, legacy)
    if not correct:
        _record_wrong_password(conn, cur, admin_user_id)
        raise HTTPException(
            status_code=403,
            detail="O'chirish paroli noto'g'ri. Profil va sozlamalardan parolni yangilashingiz mumkin",
        )
    _reset_wrong_passwords(cur, admin_user_id)


def _audit(
    cur,
    admin_user_id: int,
    action: str,
    institution_type: Optional[str] = None,
    institution_id: Optional[int] = None,
    archive_id: Optional[int] = None,
    details: Optional[dict] = None,
) -> None:
    cur.execute(
        """INSERT INTO institution_security_audit(
               admin_user_id,action,institution_type,institution_id,archive_id,details
           ) VALUES(%s,%s,%s,%s,%s,%s::jsonb)""",
        (
            admin_user_id,
            action,
            institution_type,
            institution_id,
            archive_id,
            json.dumps(details or {}, ensure_ascii=False),
        ),
    )


def _context_states(cur, institution_type: str, institution_id: int) -> list[dict]:
    cur.execute("SELECT to_regclass('public.learning_contexts') AS table_name")
    row = cur.fetchone()
    if not row or not row["table_name"]:
        return []
    cur.execute(
        """SELECT id,active FROM learning_contexts
           WHERE external_type=%s AND external_id=%s""",
        (institution_type, institution_id),
    )
    return [
        {"context_id": int(item["id"]), "active": bool(item["active"])}
        for item in cur.fetchall()
    ]


def _archive_contexts(cur, institution_type: str, institution_id: int) -> None:
    cur.execute("SELECT to_regclass('public.learning_contexts') AS table_name")
    row = cur.fetchone()
    if not row or not row["table_name"]:
        return
    cur.execute(
        """UPDATE learning_contexts
           SET active=FALSE,
               metadata=COALESCE(metadata,'{}'::jsonb) ||
                 jsonb_build_object('institution_archived',TRUE,'institution_archived_at',NOW())
           WHERE external_type=%s AND external_id=%s""",
        (institution_type, institution_id),
    )


def _restore_contexts(cur, context_states: list[dict]) -> None:
    if not context_states:
        return
    cur.execute("SELECT to_regclass('public.learning_contexts') AS table_name")
    row = cur.fetchone()
    if not row or not row["table_name"]:
        return
    for state in context_states:
        cur.execute(
            """UPDATE learning_contexts
               SET active=%s,
                   metadata=(COALESCE(metadata,'{}'::jsonb)
                     - 'institution_archived'
                     - 'institution_archived_at')
               WHERE id=%s""",
            (bool(state.get("active")), int(state["context_id"])),
        )


def _single_column_foreign_keys(cur, parent_table: str) -> list[dict]:
    cur.execute(
        """SELECT child.relname AS child_table,
                  child_col.attname AS child_column,
                  parent_col.attname AS parent_column
           FROM pg_constraint constraint_row
           JOIN pg_class parent ON parent.oid=constraint_row.confrelid
           JOIN pg_namespace parent_ns ON parent_ns.oid=parent.relnamespace
           JOIN pg_class child ON child.oid=constraint_row.conrelid
           JOIN pg_namespace child_ns ON child_ns.oid=child.relnamespace
           JOIN pg_attribute child_col
             ON child_col.attrelid=child.oid
            AND child_col.attnum=constraint_row.conkey[1]
           JOIN pg_attribute parent_col
             ON parent_col.attrelid=parent.oid
            AND parent_col.attnum=constraint_row.confkey[1]
           WHERE constraint_row.contype='f'
             AND parent_ns.nspname='public'
             AND child_ns.nspname='public'
             AND parent.relname=%s
             AND array_length(constraint_row.conkey,1)=1
             AND array_length(constraint_row.confkey,1)=1""",
        (parent_table,),
    )
    return list(cur.fetchall())


def _delete_rows_recursively(
    cur,
    table_name: str,
    filter_column: str,
    filter_values: list,
    trail: Optional[set[tuple[str, str]]] = None,
) -> None:
    """FK daraxtidagi aynan muassasaga tegishli qatorlarni pastdan o'chiradi."""
    values = [value for value in filter_values if value is not None]
    if not values:
        return
    trail = set(trail or set())
    marker = (table_name, filter_column)
    if marker in trail:
        raise RuntimeError(f"Aylanma foreign key topildi: {table_name}.{filter_column}")
    trail.add(marker)

    for foreign_key in _single_column_foreign_keys(cur, table_name):
        cur.execute(
            sql.SQL(
                "SELECT DISTINCT {parent_column} AS value FROM {parent_table} "
                "WHERE {filter_column}=ANY(%s) AND {parent_column} IS NOT NULL"
            ).format(
                parent_column=sql.Identifier(foreign_key["parent_column"]),
                parent_table=sql.Identifier(table_name),
                filter_column=sql.Identifier(filter_column),
            ),
            (values,),
        )
        referenced_values = [row["value"] for row in cur.fetchall()]
        _delete_rows_recursively(
            cur,
            foreign_key["child_table"],
            foreign_key["child_column"],
            referenced_values,
            trail,
        )

    cur.execute(
        sql.SQL("DELETE FROM {} WHERE {}=ANY(%s)").format(
            sql.Identifier(table_name),
            sql.Identifier(filter_column),
        ),
        (values,),
    )


def _purge_one(cur, archive: dict) -> None:
    institution_type = archive["institution_type"]
    institution_id = int(archive["institution_id"])
    table_name = _institution_table(institution_type)

    # Generic, foreign-keysiz eski bog'lanishlar avval uziladi.
    cur.execute("SELECT to_regclass('public.foydalanuvchi_muassasalari') AS table_name")
    row = cur.fetchone()
    if row and row["table_name"]:
        cur.execute(
            """DELETE FROM foydalanuvchi_muassasalari
               WHERE muassasa_turi=%s AND muassasa_id=%s""",
            (institution_type, institution_id),
        )

    user_column = {
        "maktab": "maktab_id",
        "bogcha": "bogcha_id",
        "markaz": "markaz_id",
        "universitet": "universitet_id",
    }[institution_type]
    cur.execute(
        sql.SQL("UPDATE users SET {}=NULL WHERE {}=%s").format(
            sql.Identifier(user_column), sql.Identifier(user_column)
        ),
        (institution_id,),
    )

    cur.execute("SELECT to_regclass('public.learning_contexts') AS table_name")
    row = cur.fetchone()
    if row and row["table_name"]:
        cur.execute(
            """SELECT id FROM learning_contexts
               WHERE external_type=%s AND external_id=%s""",
            (institution_type, institution_id),
        )
        context_ids = [item["id"] for item in cur.fetchall()]
        _delete_rows_recursively(cur, "learning_contexts", "id", context_ids)

    _delete_rows_recursively(cur, table_name, "id", [institution_id])
    cur.execute(
        """UPDATE institution_archives
           SET purged_at=NOW(),purge_error=NULL,
               metadata=metadata || '{"permanently_deleted":true}'::jsonb
           WHERE id=%s""",
        (archive["id"],),
    )


def _purge_expired_institutions(db_factory: Callable, limit: int = 20) -> int:
    conn = db_factory()
    cur = conn.cursor()
    try:
        _ensure_schema(cur)
        cur.execute("SELECT pg_try_advisory_lock(74125,20260820) AS locked")
        if not cur.fetchone()["locked"]:
            conn.rollback()
            return 0
        cur.execute(
            """SELECT * FROM institution_archives
               WHERE restored_at IS NULL AND purged_at IS NULL
                 AND purge_after<=NOW()
               ORDER BY purge_after,id LIMIT %s FOR UPDATE SKIP LOCKED""",
            (max(1, min(int(limit), 100)),),
        )
        archives = list(cur.fetchall())
        purged = 0
        for archive in archives:
            cur.execute("SAVEPOINT institution_purge_item")
            try:
                _purge_one(cur, archive)
                cur.execute("RELEASE SAVEPOINT institution_purge_item")
                purged += 1
            except Exception as error:  # keyingi kun yana urinadi; boshqa arxivlar to'xtamaydi
                cur.execute("ROLLBACK TO SAVEPOINT institution_purge_item")
                cur.execute("RELEASE SAVEPOINT institution_purge_item")
                cur.execute(
                    "UPDATE institution_archives SET purge_error=%s WHERE id=%s",
                    (str(error)[:1000], archive["id"]),
                )
        conn.commit()
        return purged
    finally:
        try:
            cur.execute("SELECT pg_advisory_unlock(74125,20260820)")
            conn.commit()
        except Exception:
            conn.rollback()
        cur.close()
        conn.close()


class PasswordUpdateRequest(BaseModel):
    token: str
    joriy_parol: Optional[str] = None
    yangi_parol: str
    yangi_parol_takror: str


class ArchiveRequest(BaseModel):
    token: str
    muassasa_turi: str
    muassasa_id: int
    ochirish_paroli: str
    sabab: Optional[str] = None


class RestoreRequest(BaseModel):
    token: str
    archive_id: int
    ochirish_paroli: str


def create_institution_archive_router(
    admin_checker: Callable[[str], int],
    db_factory: Callable,
) -> APIRouter:
    router = APIRouter(prefix="/api/admin/muassasa-xavfsizligi")
    purge_task: Optional[asyncio.Task] = None

    @router.get("/holat")
    def security_status(token: str):
        admin_user_id = admin_checker(token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _ensure_schema(cur)
            status = _security_status(cur)
            cur.execute(
                """SELECT COUNT(*) AS count FROM institution_archives
                   WHERE restored_at IS NULL AND purged_at IS NULL"""
            )
            status["archive_count"] = int(cur.fetchone()["count"] or 0)
            status["retention_days"] = ARCHIVE_RETENTION_DAYS
            status["admin_user_id"] = admin_user_id
            conn.commit()
            return status
        finally:
            cur.close()
            conn.close()

    @router.put("/parol")
    def update_password(request: PasswordUpdateRequest):
        admin_user_id = admin_checker(request.token)
        new_password = _validate_new_password(request.yangi_parol)
        repeated = _validate_new_password(request.yangi_parol_takror)
        if new_password != repeated:
            raise HTTPException(status_code=400, detail="Yangi parollar bir xil emas")

        conn = db_factory()
        cur = conn.cursor()
        try:
            _ensure_schema(cur)
            # Admin akkaunti allaqachon token bilan tasdiqlangan. Shu sabab
            # Railway'dagi eski qiymat noto'g'ri yozilgan yoki esdan chiqqan
            # bo'lsa ham admin Sozlamadan yangi 4 raqamni belgilay oladi.
            # Eski parol yangi qiymat saqlanguncha arxiv amallari uchun qoladi.
            salt_hex, password_hash = _hash_password(new_password)
            cur.execute(
                """INSERT INTO admin_institution_security(
                       singleton_id,password_salt,password_hash,password_version,
                       updated_by_admin_id,updated_at
                   ) VALUES(1,%s,%s,1,%s,NOW())
                   ON CONFLICT(singleton_id) DO UPDATE SET
                     password_salt=EXCLUDED.password_salt,
                     password_hash=EXCLUDED.password_hash,
                     password_version=admin_institution_security.password_version+1,
                     updated_by_admin_id=EXCLUDED.updated_by_admin_id,
                     updated_at=NOW()
                   RETURNING password_version,updated_at""",
                (salt_hex, password_hash, admin_user_id),
            )
            updated = cur.fetchone()
            _audit(cur, admin_user_id, "deletion_password_changed")
            conn.commit()
            return {
                "status": "updated",
                "password_version": int(updated["password_version"]),
                "updated_at": updated["updated_at"],
            }
        except HTTPException:
            if not conn.closed:
                conn.rollback()
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.get("/faol")
    def active_institutions(token: str):
        admin_checker(token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _ensure_schema(cur)
            result = []
            for institution_type, table_name in INSTITUTION_TABLES.items():
                cur.execute("SELECT to_regclass(%s) AS table_name", (f"public.{table_name}",))
                row = cur.fetchone()
                if not row or not row["table_name"]:
                    continue
                cur.execute(
                    sql.SQL(
                        "SELECT id,nomi FROM {} WHERE archived_at IS NULL ORDER BY nomi,id"
                    ).format(sql.Identifier(table_name))
                )
                result.extend(
                    {
                        "muassasa_turi": institution_type,
                        "turi_nomi": INSTITUTION_LABELS[institution_type],
                        "muassasa_id": int(item["id"]),
                        "nomi": item["nomi"],
                    }
                    for item in cur.fetchall()
                )
            conn.commit()
            return {"muassasalar": result}
        finally:
            cur.close()
            conn.close()

    @router.post("/arxivlash")
    def archive_institution(request: ArchiveRequest):
        admin_user_id = admin_checker(request.token)
        table_name = _institution_table(request.muassasa_turi)
        if request.muassasa_id < 1:
            raise HTTPException(status_code=400, detail="Muassasa ID noto'g'ri")
        conn = db_factory()
        cur = conn.cursor()
        try:
            _ensure_schema(cur)
            _verify_deletion_password(
                conn,
                cur,
                admin_user_id,
                request.ochirish_paroli,
            )
            cur.execute(
                sql.SQL(
                    "SELECT id,nomi,archived_at FROM {} WHERE id=%s FOR UPDATE"
                ).format(sql.Identifier(table_name)),
                (request.muassasa_id,),
            )
            institution = cur.fetchone()
            if not institution:
                raise HTTPException(status_code=404, detail="Muassasa topilmadi")
            if institution["archived_at"]:
                raise HTTPException(status_code=409, detail="Muassasa allaqachon arxivda")

            states = _context_states(
                cur,
                request.muassasa_turi,
                request.muassasa_id,
            )
            metadata = {
                "context_states": states,
                "retention_days": ARCHIVE_RETENTION_DAYS,
            }
            cur.execute(
                """INSERT INTO institution_archives(
                       institution_type,institution_id,institution_name,
                       archived_by_admin_id,purge_after,archive_reason,metadata
                   ) VALUES(%s,%s,%s,%s,NOW()+INTERVAL '365 days',%s,%s::jsonb)
                   RETURNING id,archived_at,purge_after""",
                (
                    request.muassasa_turi,
                    request.muassasa_id,
                    institution["nomi"],
                    admin_user_id,
                    (request.sabab or "").strip()[:500] or None,
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )
            archive = cur.fetchone()
            cur.execute(
                sql.SQL(
                    "UPDATE {} SET archived_at=%s,archive_purge_at=%s,"
                    "archived_by_admin_id=%s,archive_record_id=%s WHERE id=%s"
                ).format(sql.Identifier(table_name)),
                (
                    archive["archived_at"],
                    archive["purge_after"],
                    admin_user_id,
                    archive["id"],
                    request.muassasa_id,
                ),
            )
            _archive_contexts(cur, request.muassasa_turi, request.muassasa_id)
            _audit(
                cur,
                admin_user_id,
                "institution_archived",
                request.muassasa_turi,
                request.muassasa_id,
                archive["id"],
                {"purge_after": archive["purge_after"].isoformat()},
            )
            conn.commit()
            return {
                "status": "archived",
                "archive_id": int(archive["id"]),
                "archived_at": archive["archived_at"],
                "purge_after": archive["purge_after"],
                "retention_days": ARCHIVE_RETENTION_DAYS,
            }
        except HTTPException:
            if not conn.closed:
                conn.rollback()
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.get("/arxiv")
    def archived_institutions(token: str):
        admin_checker(token)
        _purge_expired_institutions(db_factory, limit=20)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _ensure_schema(cur)
            cur.execute(
                """SELECT id,institution_type,institution_id,institution_name,
                          archived_by_admin_id,archived_at,purge_after,archive_reason,
                          GREATEST(0,CEIL(EXTRACT(EPOCH FROM (purge_after-NOW()))/86400.0))::INTEGER
                            AS days_remaining
                   FROM institution_archives
                   WHERE restored_at IS NULL AND purged_at IS NULL
                   ORDER BY archived_at DESC,id DESC"""
            )
            archives = [
                {
                    "archive_id": int(row["id"]),
                    "muassasa_turi": row["institution_type"],
                    "turi_nomi": INSTITUTION_LABELS[row["institution_type"]],
                    "muassasa_id": int(row["institution_id"]),
                    "nomi": row["institution_name"],
                    "archived_by_admin_id": int(row["archived_by_admin_id"]),
                    "archived_at": row["archived_at"],
                    "purge_after": row["purge_after"],
                    "days_remaining": int(row["days_remaining"] or 0),
                    "sababi": row["archive_reason"],
                }
                for row in cur.fetchall()
            ]
            conn.commit()
            return {
                "arxiv": archives,
                "retention_days": ARCHIVE_RETENTION_DAYS,
            }
        finally:
            cur.close()
            conn.close()

    @router.post("/tiklash")
    def restore_institution(request: RestoreRequest):
        admin_user_id = admin_checker(request.token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            _ensure_schema(cur)
            _verify_deletion_password(
                conn,
                cur,
                admin_user_id,
                request.ochirish_paroli,
            )
            cur.execute(
                """SELECT * FROM institution_archives
                   WHERE id=%s AND restored_at IS NULL AND purged_at IS NULL
                   FOR UPDATE""",
                (request.archive_id,),
            )
            archive = cur.fetchone()
            if not archive:
                raise HTTPException(status_code=404, detail="Arxiv yozuvi topilmadi")
            if archive["purge_after"] <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=410,
                    detail="1 yillik saqlash muddati tugagan; bu muassasani tiklab bo'lmaydi",
                )
            table_name = _institution_table(archive["institution_type"])
            cur.execute(
                sql.SQL(
                    "UPDATE {} SET archived_at=NULL,archive_purge_at=NULL,"
                    "archived_by_admin_id=NULL,archive_record_id=NULL WHERE id=%s"
                ).format(sql.Identifier(table_name)),
                (archive["institution_id"],),
            )
            if cur.rowcount != 1:
                raise HTTPException(status_code=410, detail="Muassasa allaqachon butunlay o'chirilgan")
            metadata = archive["metadata"] or {}
            _restore_contexts(cur, metadata.get("context_states") or [])
            cur.execute(
                """UPDATE institution_archives
                   SET restored_at=NOW(),restored_by_admin_id=%s
                   WHERE id=%s""",
                (admin_user_id, request.archive_id),
            )
            _audit(
                cur,
                admin_user_id,
                "institution_restored",
                archive["institution_type"],
                archive["institution_id"],
                archive["id"],
            )
            conn.commit()
            return {"status": "restored"}
        except HTTPException:
            if not conn.closed:
                conn.rollback()
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    async def purge_loop() -> None:
        await asyncio.sleep(20)
        while True:
            try:
                await asyncio.to_thread(_purge_expired_institutions, db_factory, 50)
            except Exception:
                # So'rovlar ishlashda davom etadi; keyingi sikl qayta urinadi.
                pass
            await asyncio.sleep(6 * 60 * 60)

    @router.on_event("startup")
    async def start_purge_loop() -> None:
        nonlocal purge_task
        if purge_task is None or purge_task.done():
            purge_task = asyncio.create_task(purge_loop())

    @router.on_event("shutdown")
    async def stop_purge_loop() -> None:
        nonlocal purge_task
        if purge_task and not purge_task.done():
            purge_task.cancel()
            try:
                await purge_task
            except asyncio.CancelledError:
                pass
        purge_task = None

    return router

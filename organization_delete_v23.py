"""V18.23 — barcha legacy muassasalar uchun yagona yumshoq o'chirish."""

from typing import Any, Callable, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .school_import_rules import normalize_text, pin_matches


ORGANIZATION_TABLES = {
    "school": ("maktablar", "maktab"),
    "learning_center": ("oquv_markazlari", "markaz"),
    "kindergarten": ("bogchalar", "bogcha"),
    "institute": ("universitetlar", "universitet"),
}


class OrganizationDeleteRequest(BaseModel):
    token: str
    confirmation_name: str
    pin: Optional[str] = None
    reason: Optional[str] = Field(default=None, max_length=240)


def create_organization_delete_v23_router(
    verify_token: Callable[[str], int], db_factory: Callable[[], Any]
) -> APIRouter:
    router = APIRouter(prefix="/api/muassasa-v23", tags=["organization-delete-v23"])

    @router.delete("/{organization_type}/{organization_id}")
    def delete_organization(
        organization_type: str,
        organization_id: int,
        payload: OrganizationDeleteRequest,
    ):
        if organization_type not in ORGANIZATION_TABLES:
            raise HTTPException(status_code=400, detail="Muassasa turi noto'g'ri")
        user_id = verify_token(payload.token)
        table, external_type = ORGANIZATION_TABLES[organization_type]
        conn = db_factory()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=403, detail="Faqat admin uchun")
            cur.execute(
                f"SELECT nomi,creator_user_id,deletion_pin_hash,deleted_at FROM {table} WHERE id=%s FOR UPDATE",
                (organization_id,),
            )
            organization = cur.fetchone()
            if not organization or organization["deleted_at"] is not None:
                raise HTTPException(status_code=404, detail="Muassasa topilmadi")
            if normalize_text(payload.confirmation_name) != normalize_text(organization["nomi"]):
                raise HTTPException(status_code=400, detail="Tasdiqlash uchun muassasa nomini aynan kiriting")
            own_creation = organization["creator_user_id"] == user_id
            subject = f"organization-delete:{organization_type}:{organization_id}:{user_id}"
            if not own_creation:
                cur.execute("SELECT locked_until FROM school_delete_attempts WHERE subject=%s", (subject,))
                attempt = cur.fetchone()
                if attempt and attempt["locked_until"] is not None:
                    cur.execute("SELECT (%s::timestamptz>NOW()) AS locked", (attempt["locked_until"],))
                    if cur.fetchone()["locked"]:
                        raise HTTPException(status_code=429, detail="Ko'p xato urinish. 30 daqiqadan keyin qayta urinib ko'ring")
                if not pin_matches(payload.pin or "", organization["deletion_pin_hash"]):
                    cur.execute(
                        """INSERT INTO school_delete_attempts(subject,attempts,window_started,locked_until,updated_at)
                           VALUES(%s,1,NOW(),NULL,NOW())
                           ON CONFLICT(subject) DO UPDATE SET
                             attempts=CASE WHEN school_delete_attempts.window_started<NOW()-INTERVAL '15 minutes' THEN 1 ELSE school_delete_attempts.attempts+1 END,
                             window_started=CASE WHEN school_delete_attempts.window_started<NOW()-INTERVAL '15 minutes' THEN NOW() ELSE school_delete_attempts.window_started END,
                             locked_until=CASE WHEN school_delete_attempts.attempts+1>=10 THEN NOW()+INTERVAL '30 minutes' ELSE school_delete_attempts.locked_until END,
                             updated_at=NOW()""",
                        (subject,),
                    )
                    conn.commit()
                    raise HTTPException(status_code=400, detail="4 xonali o'chirish paroli noto'g'ri")
                cur.execute("DELETE FROM school_delete_attempts WHERE subject=%s", (subject,))
            cur.execute(
                f"""UPDATE {table}
                       SET deleted_at=NOW(),deleted_by_user_id=%s,delete_reason=%s,updated_at=NOW()
                     WHERE id=%s""",
                (user_id, (payload.reason or "").strip() or None, organization_id),
            )
            cur.execute(
                "UPDATE learning_contexts SET active=FALSE,updated_at=NOW() WHERE external_type=%s AND external_id=%s",
                (external_type, organization_id),
            )
            conn.commit()
            return {"status": "archived", "organization_type": organization_type, "organization_id": organization_id, "password_required": not own_creation}
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    return router

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel


class PrivacyPreferences(BaseModel):
    privacy_accepted: bool = False
    terms_accepted: bool = False
    parental_consent_confirmed: bool = False
    analytics_allowed: bool = False
    marketing_allowed: bool = False


class DeletionRequest(BaseModel):
    reason: Optional[str] = None
    confirm: bool = False


def create_legal_privacy_router(jwt_verify, db):
    router = APIRouter(prefix="/api/legal", tags=["legal-privacy"])

    def ensure_tables(cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_privacy_preferences_v1 (
                user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                privacy_accepted BOOLEAN NOT NULL DEFAULT FALSE,
                terms_accepted BOOLEAN NOT NULL DEFAULT FALSE,
                parental_consent_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
                analytics_allowed BOOLEAN NOT NULL DEFAULT FALSE,
                marketing_allowed BOOLEAN NOT NULL DEFAULT FALSE,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS account_deletion_requests_v1 (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                reason TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                resolved_at TIMESTAMPTZ
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_deletion_user_status ON account_deletion_requests_v1(user_id,status)")

    @router.get("/preferences")
    def get_preferences(token: str = Query(...)):
        user_id = jwt_verify(token)
        conn = db(); cur = conn.cursor()
        try:
            ensure_tables(cur)
            cur.execute("SELECT * FROM user_privacy_preferences_v1 WHERE user_id=%s", (user_id,))
            row = cur.fetchone()
            cur.execute("SELECT status,requested_at FROM account_deletion_requests_v1 WHERE user_id=%s ORDER BY id DESC LIMIT 1", (user_id,))
            deletion = cur.fetchone()
            conn.commit()
            return {"preferences": row or {}, "deletion_request": deletion}
        finally:
            cur.close(); conn.close()

    @router.put("/preferences")
    def save_preferences(payload: PrivacyPreferences, token: str = Query(...)):
        user_id = jwt_verify(token)
        if not payload.privacy_accepted or not payload.terms_accepted:
            raise HTTPException(status_code=422, detail="Maxfiylik siyosati va foydalanish shartlarini qabul qilish majburiy")
        conn = db(); cur = conn.cursor()
        try:
            ensure_tables(cur)
            cur.execute("""
                INSERT INTO user_privacy_preferences_v1
                    (user_id,privacy_accepted,terms_accepted,parental_consent_confirmed,analytics_allowed,marketing_allowed,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,NOW())
                ON CONFLICT(user_id) DO UPDATE SET
                    privacy_accepted=EXCLUDED.privacy_accepted,
                    terms_accepted=EXCLUDED.terms_accepted,
                    parental_consent_confirmed=EXCLUDED.parental_consent_confirmed,
                    analytics_allowed=EXCLUDED.analytics_allowed,
                    marketing_allowed=EXCLUDED.marketing_allowed,
                    updated_at=NOW()
            """, (user_id, payload.privacy_accepted, payload.terms_accepted,
                  payload.parental_consent_confirmed, payload.analytics_allowed,
                  payload.marketing_allowed))
            conn.commit()
            return {"ok": True}
        except Exception:
            conn.rollback(); raise
        finally:
            cur.close(); conn.close()

    @router.post("/account-deletion-request")
    def request_deletion(payload: DeletionRequest, token: str = Query(...)):
        user_id = jwt_verify(token)
        if not payload.confirm:
            raise HTTPException(status_code=422, detail="Hisobni o'chirish so'rovini tasdiqlang")
        conn = db(); cur = conn.cursor()
        try:
            ensure_tables(cur)
            cur.execute("SELECT id FROM account_deletion_requests_v1 WHERE user_id=%s AND status='pending'", (user_id,))
            if cur.fetchone():
                return {"ok": True, "status": "pending", "message": "So'rov avval yuborilgan"}
            cur.execute("INSERT INTO account_deletion_requests_v1(user_id,reason) VALUES(%s,%s) RETURNING id", (user_id, (payload.reason or "")[:1000]))
            request_id = cur.fetchone()["id"]
            conn.commit()
            return {"ok": True, "status": "pending", "request_id": request_id}
        except Exception:
            conn.rollback(); raise
        finally:
            cur.close(); conn.close()

    return router

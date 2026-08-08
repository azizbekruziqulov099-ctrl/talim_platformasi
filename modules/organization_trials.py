"""V17 private-organisation trial and one-time activation API.

Self-service creation is deliberately separate from the four full onboarding
routers: only a private organisation can be created here.  Public/state
institutions still use the administrator verification workflow.  Trial dates
and prices are server-owned; a wallet debit is possible only after an explicit
human confirmation and is written to an immutable ledger in the same DB
transaction as activation.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Literal

import psycopg2
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from platform_core.database import DatabaseBusyError, db_session


ACTIVATION_PRICE_UZS = 200_000
TRIAL_DAYS = 30
ORGANIZATION_TYPES = {"kindergarten", "school", "learning_center", "institute"}
SELF_SERVICE_ROLES = {
    "oqituvchi", "teacher", "bogcha_opa", "tarbiyachi", "educator",
    "owner", "founder", "direktor", "director", "rektor", "rector",
    "admin", "administrator",
}


class TrialStart(BaseModel):
    organization_type: Literal[
        "kindergarten", "school", "learning_center", "institute"
    ]
    name: str = Field(min_length=3, max_length=180)
    ownership_type: Literal["private", "public", "state"] = "private"
    confirm_start: bool = False
    idempotency_key: str = Field(min_length=8, max_length=128)
    region: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    institution_type: Literal[
        "institute", "university", "academy", "branch"
    ] = "institute"
    operator_model: Literal["center", "independent_tutor"] = "center"


class ActivationConfirm(BaseModel):
    confirm_charge: bool = False
    idempotency_key: str = Field(min_length=8, max_length=128)


class AdminWalletCredit(BaseModel):
    user_id: int = Field(ge=1)
    amount_uzs: int = Field(ge=1, le=100_000_000)
    confirm_credit: bool = False
    idempotency_key: str = Field(min_length=8, max_length=128)
    reference: str = Field(min_length=3, max_length=160)
    note: str | None = Field(default=None, max_length=1000)


def _fingerprint(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def create_organization_trial_router(
    jwt_check: Callable[[str], int],
) -> APIRouter:
    router = APIRouter(prefix="/api/muassasa-v17", tags=["Muassasa V17"])

    def authenticated_user(
        authorization: str | None = Header(default=None),
    ) -> int:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=401, detail="Bearer sessiya tokeni topilmadi"
            )
        token = authorization[7:].strip()
        if not token:
            raise HTTPException(status_code=401, detail="Sessiya tokeni bo'sh")
        return int(jwt_check(token))

    @contextmanager
    def database(*, readonly: bool = False) -> Iterator[tuple[Any, Any]]:
        try:
            with db_session(readonly=readonly) as result:
                yield result
        except DatabaseBusyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except psycopg2.errors.UndefinedTable as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "V17 bazasi o'rnatilmagan. Avval 001--013, keyin "
                    "database/014_organization_trials_wallet.sql ni bajaring."
                ),
            ) from exc

    def ensure_schema(cur: Any) -> None:
        cur.execute(
            """SELECT 1 FROM app_schema_migrations
               WHERE version='014_organization_trials_wallet'"""
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=503,
                detail="database/014_organization_trials_wallet.sql bajarilmagan",
            )

    def system_admin(cur: Any, user_id: int) -> bool:
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
        return cur.fetchone() is not None

    def lock_request_key(
        cur: Any, actor_user_id: int, operation_key: str, idempotency_key: str,
    ) -> None:
        """Serialize even the first concurrent use of an idempotency key.

        A plain SELECT ... FOR UPDATE cannot lock a row that does not exist yet;
        the transaction-scoped advisory lock closes that absent-row race.
        """
        cur.execute(
            """SELECT pg_advisory_xact_lock(
                 74131,hashtext(%s)
               )""",
            (f"{actor_user_id}:{operation_key}:{idempotency_key}",),
        )

    def refresh_expired(cur: Any, *, user_id: int | None = None) -> None:
        params: list[Any] = []
        scope = ""
        if user_id is not None:
            scope = " AND creator_user_id=%s"
            params.append(user_id)
        cur.execute(
            f"""UPDATE organization_trials
                   SET lifecycle_status='read_only',
                       read_only_at=COALESCE(read_only_at,NOW()),updated_at=NOW()
                 WHERE lifecycle_status='trial' AND trial_ends_at<=NOW(){scope}""",
            params,
        )

    def wallet_row(cur: Any, user_id: int, *, lock: bool = False) -> dict[str, Any]:
        cur.execute(
            """INSERT INTO organization_wallets(user_id,balance_uzs)
               VALUES(%s,0) ON CONFLICT(user_id) DO NOTHING""",
            (user_id,),
        )
        cur.execute(
            f"""SELECT user_id,balance_uzs,updated_at
                FROM organization_wallets WHERE user_id=%s
                {'FOR UPDATE' if lock else ''}""",
            (user_id,),
        )
        return dict(cur.fetchone())

    def organization_item(
        cur: Any, organization_id: int, user_id: int,
    ) -> dict[str, Any]:
        cur.execute(
            """SELECT o.id,o.context_id,o.organization_type,o.display_name name,
                      o.ownership_type,o.lifecycle_status,
                      CASE WHEN o.lifecycle_status='active' THEN 'write'
                           WHEN o.lifecycle_status='trial' AND o.trial_ends_at>NOW()
                             THEN 'write'
                           ELSE 'read_only' END access_mode,
                      o.trial_started_at,o.trial_ends_at,
                      GREATEST(
                        0,CEIL(EXTRACT(EPOCH FROM (o.trial_ends_at-NOW()))/86400.0)
                      )::INTEGER days_remaining,
                      o.activated_at,o.activation_price_uzs,
                      (o.lifecycle_status<>'active') can_activate,
                      (COALESCE(w.balance_uzs,0)>=o.activation_price_uzs)
                        wallet_balance_sufficient
                 FROM organization_trials o
                 LEFT JOIN organization_wallets w
                   ON w.user_id=o.creator_user_id
                WHERE o.id=%s AND o.creator_user_id=%s""",
            (organization_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Muassasa topilmadi")
        return dict(row)

    def add_membership(
        cur: Any, context_id: int, user_id: int, member_role: str,
        organization_type: str,
    ) -> None:
        cur.execute(
            """INSERT INTO context_memberships(
                 context_id,user_id,member_role,status,source,
                 approved_by_user_id,metadata
               ) VALUES(%s,%s,%s,'active','organization_v17',%s,%s::jsonb)
               ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,member_role)
               DO UPDATE SET status='active',ended_at=NULL,updated_at=NOW(),
                 approved_by_user_id=EXCLUDED.approved_by_user_id,
                 metadata=EXCLUDED.metadata""",
            (
                context_id, user_id, member_role, user_id,
                json.dumps(
                    {"organization_type": organization_type, "source": "trial_v17"},
                    ensure_ascii=False,
                ),
            ),
        )

    def create_bound_context(
        cur: Any, request: TrialStart, user_id: int,
    ) -> int:
        name = request.name.strip()
        context_type = (
            "university" if request.organization_type == "institute"
            else request.organization_type
        )
        cur.execute(
            """INSERT INTO learning_contexts(
                 context_type,name,owner_user_id,region,district,active,metadata
               ) VALUES(%s,%s,%s,%s,%s,TRUE,%s::jsonb) RETURNING id""",
            (
                context_type, name, user_id,
                (request.region or "").strip() or None,
                (request.district or "").strip() or None,
                json.dumps(
                    {
                        "source": "organization_trial_v17",
                        "provisional_setup": True,
                        "private_self_service": True,
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        context_id = int(cur.fetchone()["id"])

        if request.organization_type == "kindergarten":
            cur.execute(
                """INSERT INTO bogchalar(
                     nomi,turi,viloyat,tuman,direktor_user_id,oylik_tolov
                   ) VALUES(%s,'xususiy',%s,%s,%s,NULL) RETURNING id""",
                (name, request.region, request.district, user_id),
            )
            legacy_id = int(cur.fetchone()["id"])
            cur.execute(
                """UPDATE learning_contexts SET external_type='bogcha',external_id=%s
                   WHERE id=%s""",
                (legacy_id, context_id),
            )
            cur.execute(
                """INSERT INTO kindergarten_profiles(
                     context_id,legacy_bogcha_id,ownership_type,
                     onboarding_status,verification_status,work_start,work_end,
                     work_days,capacity,language,payment_enabled,monthly_fee
                   ) VALUES(
                     %s,%s,'private','active','unverified','08:00','18:00',
                     %s,100,'uz',FALSE,NULL
                   )""",
                (context_id, legacy_id, [1, 2, 3, 4, 5, 6]),
            )
            for role_key in ("owner", "director"):
                cur.execute(
                    """INSERT INTO kindergarten_role_assignments(
                         context_id,user_id,role_key,status,approved_by_user_id,permissions
                       ) VALUES(%s,%s,%s,'active',%s,%s::jsonb)""",
                    (
                        context_id, user_id, role_key, user_id,
                        json.dumps({"source": "organization_v17"}),
                    ),
                )
            add_membership(cur, context_id, user_id, "manager", "kindergarten")
            cur.execute(
                """INSERT INTO foydalanuvchi_muassasalari(
                     user_id,muassasa_turi,muassasa_id,lavozim
                   ) VALUES(%s,'bogcha',%s,'bogcha_direktor')
                   ON CONFLICT(user_id,muassasa_turi,muassasa_id)
                   DO UPDATE SET lavozim=EXCLUDED.lavozim""",
                (user_id, legacy_id),
            )

        elif request.organization_type == "school":
            cur.execute(
                """INSERT INTO school_profiles(
                     context_id,ownership_type,onboarding_status,verification_status,
                     shift_count,academic_year,lesson_minutes,work_days,
                     billing_enabled,settings
                   ) VALUES(
                     %s,'private','active','unverified',1,'2026-2027',45,%s,
                     FALSE,%s::jsonb
                   )""",
                (
                    context_id, [1, 2, 3, 4, 5, 6],
                    json.dumps({"source": "organization_v17", "provisional_setup": True}),
                ),
            )
            cur.execute(
                """INSERT INTO school_role_assignments(
                     context_id,user_id,role_key,status,approved_by_user_id,permissions
                   ) VALUES(%s,%s,'owner','active',%s,%s::jsonb)""",
                (
                    context_id, user_id, user_id,
                    json.dumps({"source": "organization_v17"}),
                ),
            )
            add_membership(cur, context_id, user_id, "manager", "school")

        elif request.organization_type == "learning_center":
            cur.execute(
                """INSERT INTO center_profiles(
                     context_id,ownership_type,operator_model,onboarding_status,
                     verification_status,timezone,settings
                   ) VALUES(
                     %s,'private',%s,'active','unverified','Asia/Tashkent',%s::jsonb
                   )""",
                (
                    context_id, request.operator_model,
                    json.dumps({"source": "organization_v17", "provisional_setup": True}),
                ),
            )
            cur.execute(
                """INSERT INTO center_role_assignments(
                     context_id,user_id,role_key,status,approved_by_user_id,permissions
                   ) VALUES(%s,%s,'owner','active',%s,%s::jsonb)""",
                (
                    context_id, user_id, user_id,
                    json.dumps({"source": "organization_v17"}),
                ),
            )
            add_membership(cur, context_id, user_id, "manager", "learning_center")

        else:
            cur.execute(
                """INSERT INTO institute_profiles(
                     context_id,ownership_type,institution_type,onboarding_status,
                     verification_status,grading_system,default_currency,
                     academic_policy,settings
                   ) VALUES(
                     %s,'private',%s,'pending_verification','pending',
                     'credit_modular','UZS',
                     %s::jsonb,%s::jsonb
                   )""",
                (
                    context_id, request.institution_type,
                    json.dumps({"auto_exclusion": False}),
                    json.dumps({"source": "organization_v17", "provisional_setup": True}),
                ),
            )
            cur.execute(
                """INSERT INTO institute_role_assignments(
                     context_id,user_id,role_key,status,approved_by_user_id,permissions
                   ) VALUES(%s,%s,'owner','active',%s,%s::jsonb)""",
                (
                    context_id, user_id, user_id,
                    json.dumps({"source": "organization_v17"}),
                ),
            )
            add_membership(cur, context_id, user_id, "manager", "institute")

        return context_id

    @router.get("/meniki")
    def my_organizations(
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            refresh_expired(cur, user_id=user_id)
            wallet = wallet_row(cur, user_id)
            cur.execute(
                """SELECT id FROM organization_trials
                   WHERE creator_user_id=%s ORDER BY id DESC""",
                (user_id,),
            )
            ids = [int(row["id"]) for row in cur.fetchall()]
            organizations = [organization_item(cur, item_id, user_id) for item_id in ids]
        return {
            "activation_price_uzs": ACTIVATION_PRICE_UZS,
            "trial_days": TRIAL_DAYS,
            "wallet": {"balance_uzs": int(wallet["balance_uzs"])},
            "organizations": organizations,
        }

    @router.post("/sinov-boshlash")
    def start_trial(
        request: TrialStart,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.confirm_start is not True:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "TRIAL_CONFIRMATION_REQUIRED",
                    "message": "30 kunlik sinovni boshlash uchun inson tasdig'i kerak",
                },
            )
        if request.ownership_type != "private":
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PUBLIC_OR_STATE_REQUIRES_VERIFICATION",
                    "message": (
                        "Davlat/ommaviy muassasa faqat Administrator markazi "
                        "va hujjat tekshiruvi orqali ochiladi"
                    ),
                },
            )
        normalized_name = request.name.strip()
        request_key = request.idempotency_key.strip()
        fingerprint = _fingerprint(
            {
                "organization_type": request.organization_type,
                "name": normalized_name,
                "ownership_type": request.ownership_type,
                "region": (request.region or "").strip(),
                "district": (request.district or "").strip(),
                "institution_type": request.institution_type,
                "operator_model": request.operator_model,
            }
        )
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                "SELECT user_id,role FROM users WHERE user_id=%s FOR UPDATE",
                (user_id,),
            )
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
            admin = system_admin(cur, user_id)
            if not admin and str(user["role"] or "").casefold() not in SELF_SERVICE_ROLES:
                raise HTTPException(
                    status_code=403,
                    detail="Muassasa sinovini o'qituvchi yoki vakolatli egasi ochadi",
                )
            lock_request_key(cur, user_id, "trial_start", request_key)
            cur.execute(
                """SELECT request_fingerprint,organization_id
                   FROM organization_request_keys
                   WHERE actor_user_id=%s AND operation_key='trial_start'
                     AND idempotency_key=%s FOR UPDATE""",
                (user_id, request_key),
            )
            replay = cur.fetchone()
            if replay:
                if replay["request_fingerprint"] != fingerprint:
                    raise HTTPException(
                        status_code=409,
                        detail={"code": "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST"},
                    )
                item = organization_item(cur, int(replay["organization_id"]), user_id)
                return {**item, "reused": True}

            refresh_expired(cur, user_id=user_id)
            cur.execute(
                """SELECT id,lifecycle_status FROM organization_trials
                   WHERE creator_user_id=%s
                     AND lifecycle_status IN ('trial','read_only')
                   ORDER BY id LIMIT 1 FOR UPDATE""",
                (user_id,),
            )
            unpaid = cur.fetchone()
            if unpaid:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "UNPAID_ORGANIZATION_EXISTS",
                        "organization_id": int(unpaid["id"]),
                        "lifecycle_status": unpaid["lifecycle_status"],
                        "message": (
                            "Avval mavjud sinov muassasasini 200 000 UZS ga "
                            "faollashtiring; undan keyin yangi sinov ochiladi"
                        ),
                    },
                )

            context_id = create_bound_context(cur, request, user_id)
            cur.execute(
                """INSERT INTO organization_trials(
                     context_id,creator_user_id,organization_type,ownership_type,
                     display_name,lifecycle_status,trial_started_at,trial_ends_at,
                     activation_price_uzs,start_request_key,
                     start_request_fingerprint,metadata
                   ) VALUES(
                     %s,%s,%s,'private',%s,'trial',NOW(),
                     NOW()+INTERVAL '30 days',200000,%s,%s,%s::jsonb
                   ) RETURNING id""",
                (
                    context_id, user_id, request.organization_type, normalized_name,
                    request_key, fingerprint,
                    json.dumps({"server_trial_days": TRIAL_DAYS}),
                ),
            )
            organization_id = int(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO organization_request_keys(
                     actor_user_id,operation_key,idempotency_key,
                     request_fingerprint,organization_id
                   ) VALUES(%s,'trial_start',%s,%s,%s)""",
                (user_id, request_key, fingerprint, organization_id),
            )
            item = organization_item(cur, organization_id, user_id)
        return {**item, "reused": False}

    @router.post("/{organization_id}/faollashtirish")
    def activate(
        organization_id: int,
        request: ActivationConfirm,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.confirm_charge is not True:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "EXPLICIT_CHARGE_CONFIRMATION_REQUIRED",
                    "message": "200 000 UZS yechishga aniq rozilik kerak",
                },
            )
        request_key = request.idempotency_key.strip()
        fingerprint = _fingerprint(
            {"organization_id": organization_id, "amount_uzs": ACTIVATION_PRICE_UZS}
        )
        with database() as (_, cur):
            ensure_schema(cur)
            refresh_expired(cur, user_id=user_id)
            lock_request_key(cur, user_id, "activation", request_key)
            cur.execute(
                """SELECT request_fingerprint,organization_id,ledger_entry_id
                   FROM organization_request_keys
                   WHERE actor_user_id=%s AND operation_key='activation'
                     AND idempotency_key=%s FOR UPDATE""",
                (user_id, request_key),
            )
            replay = cur.fetchone()
            if replay:
                if replay["request_fingerprint"] != fingerprint:
                    raise HTTPException(
                        status_code=409,
                        detail={"code": "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST"},
                    )
                item = organization_item(cur, int(replay["organization_id"]), user_id)
                wallet = wallet_row(cur, user_id)
                return {
                    "organization": item,
                    "charged_uzs": (
                        ACTIVATION_PRICE_UZS
                        if replay["ledger_entry_id"] is not None else 0
                    ),
                    "wallet": {"balance_uzs": int(wallet["balance_uzs"])},
                    "reused": True,
                }

            cur.execute(
                """SELECT * FROM organization_trials
                   WHERE id=%s AND creator_user_id=%s FOR UPDATE""",
                (organization_id, user_id),
            )
            organization = cur.fetchone()
            if not organization:
                raise HTTPException(status_code=404, detail="Muassasa topilmadi")
            wallet = wallet_row(cur, user_id, lock=True)
            if organization["lifecycle_status"] == "active":
                cur.execute(
                    """INSERT INTO organization_request_keys(
                         actor_user_id,operation_key,idempotency_key,
                         request_fingerprint,organization_id
                       ) VALUES(%s,'activation',%s,%s,%s)""",
                    (user_id, request_key, fingerprint, organization_id),
                )
                item = organization_item(cur, organization_id, user_id)
                return {
                    "organization": item,
                    "charged_uzs": 0,
                    "wallet": {"balance_uzs": int(wallet["balance_uzs"])},
                    "reused": True,
                }

            price = int(organization["activation_price_uzs"])
            balance = int(wallet["balance_uzs"])
            if balance < price:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "code": "INSUFFICIENT_WALLET_BALANCE",
                        "required_uzs": price,
                        "balance_uzs": balance,
                        "message": "Hisobda faollashtirish uchun mablag' yetarli emas",
                    },
                )
            new_balance = balance - price
            cur.execute(
                """UPDATE organization_wallets
                   SET balance_uzs=%s,updated_at=NOW() WHERE user_id=%s""",
                (new_balance, user_id),
            )
            cur.execute(
                """INSERT INTO organization_wallet_ledger(
                     wallet_user_id,organization_id,entry_type,amount_uzs,
                     direction,balance_after_uzs,actor_user_id,idempotency_key,
                     request_fingerprint,note,metadata
                   ) VALUES(
                     %s,%s,'activation_debit',%s,'debit',%s,%s,%s,%s,
                     'Muassasani bir martalik faollashtirish',%s::jsonb
                   ) RETURNING id""",
                (
                    user_id, organization_id, price, new_balance, user_id,
                    request_key, fingerprint,
                    json.dumps({"explicit_confirm_charge": True}),
                ),
            )
            ledger_id = int(cur.fetchone()["id"])
            cur.execute(
                """UPDATE organization_trials
                   SET lifecycle_status='active',activated_at=NOW(),
                       read_only_at=NULL,updated_at=NOW()
                   WHERE id=%s""",
                (organization_id,),
            )
            cur.execute(
                """INSERT INTO organization_request_keys(
                     actor_user_id,operation_key,idempotency_key,
                     request_fingerprint,organization_id,ledger_entry_id
                   ) VALUES(%s,'activation',%s,%s,%s,%s)""",
                (user_id, request_key, fingerprint, organization_id, ledger_id),
            )
            item = organization_item(cur, organization_id, user_id)
        return {
            "organization": item,
            "charged_uzs": price,
            "wallet": {"balance_uzs": new_balance},
            "reused": False,
        }

    @router.post("/admin/hamyon-toldirish")
    def admin_credit(
        request: AdminWalletCredit,
        admin_user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.confirm_credit is not True:
            raise HTTPException(
                status_code=409,
                detail={"code": "ADMIN_CREDIT_CONFIRMATION_REQUIRED"},
            )
        request_key = request.idempotency_key.strip()
        fingerprint = _fingerprint(
            {
                "user_id": request.user_id,
                "amount_uzs": request.amount_uzs,
                "reference": request.reference.strip(),
                "note": (request.note or "").strip(),
            }
        )
        with database() as (_, cur):
            ensure_schema(cur)
            if not system_admin(cur, admin_user_id):
                raise HTTPException(status_code=403, detail="Faqat administrator uchun")
            lock_request_key(
                cur, admin_user_id, "admin_wallet_credit", request_key
            )
            cur.execute(
                "SELECT 1 FROM users WHERE user_id=%s FOR UPDATE",
                (request.user_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
            cur.execute(
                """SELECT request_fingerprint,ledger_entry_id
                   FROM organization_request_keys
                   WHERE actor_user_id=%s AND operation_key='admin_wallet_credit'
                     AND idempotency_key=%s FOR UPDATE""",
                (admin_user_id, request_key),
            )
            replay = cur.fetchone()
            if replay:
                if replay["request_fingerprint"] != fingerprint:
                    raise HTTPException(
                        status_code=409,
                        detail={"code": "IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST"},
                    )
                wallet = wallet_row(cur, request.user_id)
                return {
                    "wallet": {
                        "user_id": request.user_id,
                        "balance_uzs": int(wallet["balance_uzs"]),
                    },
                    "credited_uzs": request.amount_uzs,
                    "ledger_entry_id": int(replay["ledger_entry_id"]),
                    "reused": True,
                }
            wallet = wallet_row(cur, request.user_id, lock=True)
            new_balance = int(wallet["balance_uzs"]) + request.amount_uzs
            cur.execute(
                """UPDATE organization_wallets
                   SET balance_uzs=%s,updated_at=NOW() WHERE user_id=%s""",
                (new_balance, request.user_id),
            )
            cur.execute(
                """INSERT INTO organization_wallet_ledger(
                     wallet_user_id,entry_type,amount_uzs,direction,
                     balance_after_uzs,actor_user_id,idempotency_key,
                     request_fingerprint,note,metadata
                   ) VALUES(
                     %s,'admin_verified_credit',%s,'credit',%s,%s,%s,%s,%s,%s::jsonb
                   ) RETURNING id""",
                (
                    request.user_id, request.amount_uzs, new_balance,
                    admin_user_id, request_key, fingerprint, request.note,
                    json.dumps(
                        {"reference": request.reference.strip(), "verified_by_admin": True},
                        ensure_ascii=False,
                    ),
                ),
            )
            ledger_id = int(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO organization_request_keys(
                     actor_user_id,operation_key,idempotency_key,
                     request_fingerprint,ledger_entry_id
                   ) VALUES(%s,'admin_wallet_credit',%s,%s,%s)""",
                (admin_user_id, request_key, fingerprint, ledger_id),
            )
        return {
            "wallet": {"user_id": request.user_id, "balance_uzs": new_balance},
            "credited_uzs": request.amount_uzs,
            "ledger_entry_id": ledger_id,
            "reused": False,
        }

    return router

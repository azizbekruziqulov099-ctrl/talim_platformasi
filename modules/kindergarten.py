"""Modular kindergarten API and deterministic assistant workflow.

The assistant never performs a privileged final action by itself. It can
explain, focus a semantic UI field, prepare a draft, move between reversible
steps and keep an audit trail. Organisation activation, roles, calendar
publishing and payments still require an authenticated human confirmation.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import string
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterator, Literal

import psycopg2
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from platform_core.database import DatabaseBusyError, db_session


MANAGER_ROLES = {
    "owner",
    "founder",
    "director",
    "deputy_director",
    "administrator",
}
STAFF_ROLES = MANAGER_ROLES | {
    "methodist",
    "educator",
    "assistant_educator",
    "nurse",
    "psychologist",
    "accountant",
    "cook",
    "security",
}
EDIT_CHILD_ROLES = MANAGER_ROLES | {"methodist", "educator", "assistant_educator"}
CHILD_VIEW_ROLES = EDIT_CHILD_ROLES | {"nurse", "psychologist"}
GROUP_VIEW_ROLES = CHILD_VIEW_ROLES
ATTENDANCE_EDIT_ROLES = EDIT_CHILD_ROLES | {"nurse"}
DAILY_REPORT_ROLES = EDIT_CHILD_ROLES | {"nurse"}
PAYMENT_ROLES = MANAGER_ROLES | {"accountant"}
PRIVILEGED_ROLES = {"director", "deputy_director", "administrator"}
ROLE_LABELS = {
    "owner": "Mulkdor",
    "founder": "Ta'sischi",
    "director": "Direktor",
    "deputy_director": "Direktor o'rinbosari",
    "methodist": "Metodist",
    "educator": "Tarbiyachi",
    "assistant_educator": "Tarbiyachi yordamchisi",
    "nurse": "Hamshira",
    "psychologist": "Psixolog",
    "accountant": "Hisobchi",
    "administrator": "Administrator",
    "cook": "Oshpaz",
    "security": "Qo'riqlash xodimi",
}
ROLE_TO_LEGACY = {
    "owner": "bogcha_direktor",
    "founder": "bogcha_direktor",
    "director": "bogcha_direktor",
    "deputy_director": "bogcha_zam",
    "administrator": "bogcha_zam",
    "methodist": "bogcha_zam",
    "educator": "bogcha_opa",
    "assistant_educator": "bogcha_opa",
    "nurse": "bogcha_opa",
    "psychologist": "bogcha_opa",
    "accountant": "bogcha_zam",
    "cook": "bogcha_opa",
    "security": "bogcha_opa",
}
ALLOWED_STEPS = {
    "relationship",
    "method",
    "basics",
    "schedule",
    "groups",
    "team",
    "preview",
}
ASSISTANT_ACTIONS = {
    "SHOW_MENU",
    "FOCUS_FIELD",
    "SET_DRAFT_VALUE",
    "NEXT_STEP",
    "PREVIOUS_STEP",
    "PAUSE",
    "RESUME",
    "UNDO",
    "MINIMIZE",
    "RESTORE",
    "SPEAK",
    "COMPLETE_TOUR",
}
REVERSIBLE_ACTIONS = {
    "FOCUS_FIELD",
    "SET_DRAFT_VALUE",
    "NEXT_STEP",
    "PREVIOUS_STEP",
    "MINIMIZE",
    "RESTORE",
}


class DraftStart(BaseModel):
    token: str
    relationship: Literal["owner", "director", "administrator", "educator"]
    ownership_type: Literal["public", "private"]
    setup_mode: Literal["manual", "guided", "assistant"] = "guided"
    avatar_enabled: bool = True
    speech_enabled: bool = True
    avatar_variant: Literal["female", "male", "neutral"] = "female"


class DraftUpdate(BaseModel):
    token: str
    step: str
    payload: dict[str, Any] = Field(default_factory=dict)
    expected_version: int


class DraftConfirm(BaseModel):
    token: str
    expected_version: int
    confirmation: bool


class JoinRequestCreate(BaseModel):
    token: str
    context_id: int
    requested_role: str
    note: str | None = None


class JoinDecision(BaseModel):
    token: str
    request_id: int
    approve: bool


class InviteCreate(BaseModel):
    token: str
    context_id: int
    role_key: str
    group_id: int | None = None
    invited_name: str | None = None
    invited_contact: str | None = None


class InviteAccept(BaseModel):
    token: str
    invite_code: str


class GroupCreate(BaseModel):
    token: str
    context_id: int
    name: str
    age_min_months: int | None = Field(default=None, ge=0, le=120)
    age_max_months: int | None = Field(default=None, ge=0, le=120)
    capacity: int | None = Field(default=None, ge=1, le=100)
    room_name: str | None = None
    work_start: str | None = None
    work_end: str | None = None


class ChildCreate(BaseModel):
    token: str
    context_id: int
    group_id: int | None = None
    full_name: str
    birth_date: date | None = None
    gender: Literal["female", "male", "unspecified"] | None = None
    allergies: str | None = None
    medical_notes: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None
    guardian_relationship: str | None = None


class AttendanceMark(BaseModel):
    token: str
    context_id: int
    group_id: int
    child_id: int
    attendance_date: date
    status: Literal["present", "absent", "late", "excused", "sick"]
    arrival_at: datetime | None = None
    departure_at: datetime | None = None
    note: str | None = None


class DailyReportUpsert(BaseModel):
    token: str
    context_id: int
    group_id: int
    child_id: int
    report_date: date
    meals: dict[str, Any] = Field(default_factory=dict)
    sleep: dict[str, Any] = Field(default_factory=dict)
    mood: str | None = None
    activities: str | None = None
    educator_note: str | None = None


class CalendarEventCreate(BaseModel):
    token: str
    context_id: int
    group_id: int | None = None
    event_type: Literal[
        "lesson",
        "activity",
        "holiday",
        "meeting",
        "meal",
        "sleep",
        "medical",
        "payment_due",
        "other",
    ]
    title: str
    description: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: Literal["draft", "published"] = "published"
    confirmation: bool = False


class SettingsUpdate(BaseModel):
    token: str
    context_id: int
    work_start: str | None = None
    work_end: str | None = None
    work_days: list[int] | None = None
    capacity: int | None = Field(default=None, ge=1)
    language: str | None = None
    payment_enabled: bool | None = None
    monthly_fee: Decimal | None = Field(default=None, ge=0)


class BillingPlanCreate(BaseModel):
    token: str
    context_id: int
    name: str
    amount: Decimal = Field(gt=0)
    billing_day: int = Field(default=5, ge=1, le=28)


class InvoiceGenerate(BaseModel):
    token: str
    context_id: int
    plan_id: int
    group_id: int | None = None
    period_month: date
    due_date: date
    confirmation: bool = False


class PaymentCreate(BaseModel):
    token: str
    amount: Decimal = Field(gt=0)
    payment_method: Literal["cash", "card", "bank_transfer", "online", "other"] = (
        "cash"
    )
    reference: str | None = None
    note: str | None = None
    idempotency_key: str = Field(min_length=16, max_length=100)
    confirmation: bool = False


class AssistantStart(BaseModel):
    token: str
    workflow_key: str = "kindergarten_onboarding"
    context_id: int | None = None
    draft_id: int | None = None
    avatar_enabled: bool = True
    speech_enabled: bool = True
    avatar_variant: Literal["female", "male", "neutral"] = "female"


class AssistantAction(BaseModel):
    token: str
    action_id: str
    ui_anchor: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


def create_kindergarten_router(jwt_check: Callable[[str], int]) -> APIRouter:
    router = APIRouter(prefix="/api/bogcha-v2", tags=["Bog'cha v2"])

    def current_user(token: str) -> int:
        return int(jwt_check(token))

    def authenticated_user(
        token: str | None = Query(default=None, include_in_schema=False),
        authorization: str | None = Header(default=None),
    ) -> int:
        bearer = ""
        if authorization and authorization.lower().startswith("bearer "):
            bearer = authorization[7:].strip()
        candidate = bearer or (token or "").strip()
        if not candidate:
            raise HTTPException(status_code=401, detail="Sessiya tokeni topilmadi")
        return current_user(candidate)

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
                    "Bog'cha bazasi hali o'rnatilmagan. "
                    "Avval 001_learning_analytics.sql, keyin "
                    "003_kindergarten_platform.sql ni bajaring."
                ),
            ) from exc

    def ensure_schema(cur: Any) -> None:
        cur.execute(
            "SELECT 1 FROM app_schema_migrations WHERE version=%s",
            ("004_kindergarten_hardening",),
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Bog'cha v2 migratsiyasi to'liq emas: "
                    "003 dan keyin database/004_kindergarten_hardening.sql "
                    "faylini ham bajaring."
                ),
            )

    def is_system_admin(cur: Any, user_id: int) -> bool:
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
        return cur.fetchone() is not None

    def active_roles(cur: Any, context_id: int, user_id: int) -> set[str]:
        cur.execute(
            """SELECT c.active,p.onboarding_status,p.verification_status
               FROM learning_contexts c
               JOIN kindergarten_profiles p ON p.context_id=c.id
               WHERE c.id=%s""",
            (context_id,),
        )
        state = cur.fetchone()
        if (
            not state
            or not state["active"]
            or state["onboarding_status"] != "active"
            or state["verification_status"] == "rejected"
        ):
            raise HTTPException(
                status_code=403,
                detail="Bu bog'cha hozir faol emas yoki tasdiqlanmagan.",
            )
        cur.execute(
            """SELECT role_key,group_id
               FROM kindergarten_role_assignments
               WHERE context_id=%s AND user_id=%s AND status='active'
                 AND starts_at<=NOW()
                 AND (ends_at IS NULL OR ends_at>NOW())""",
            (context_id, user_id),
        )
        return {
            row["role_key"]
            for row in cur.fetchall()
            if row["group_id"] is None or row["role_key"] not in MANAGER_ROLES
        }

    def allowed_group_scope(
        cur: Any,
        context_id: int,
        user_id: int,
        allowed: set[str],
    ) -> tuple[set[str], set[int] | None]:
        if is_system_admin(cur, user_id):
            return {"system_admin"}, None
        roles = active_roles(cur, context_id, user_id)
        if not roles.intersection(allowed):
            raise HTTPException(
                status_code=403,
                detail="Bu amal uchun shu bog'chadagi vakolatingiz yetarli emas.",
            )
        cur.execute(
            """SELECT role_key,group_id
               FROM kindergarten_role_assignments
               WHERE context_id=%s AND user_id=%s AND status='active'
                 AND role_key=ANY(%s)
                 AND starts_at<=NOW()
                 AND (ends_at IS NULL OR ends_at>NOW())""",
            (context_id, user_id, list(allowed)),
        )
        assignments = cur.fetchall()
        if any(row["group_id"] is None for row in assignments):
            return roles, None
        return roles, {int(row["group_id"]) for row in assignments}

    def require_group(
        cur: Any,
        context_id: int,
        user_id: int,
        allowed: set[str],
        group_id: int,
    ) -> set[str]:
        roles, group_scope = allowed_group_scope(
            cur, context_id, user_id, allowed
        )
        if group_scope is not None and group_id not in group_scope:
            raise HTTPException(
                status_code=403,
                detail="Siz faqat biriktirilgan guruh ma'lumotini ko'ra olasiz.",
            )
        return roles

    def require_roles(
        cur: Any, context_id: int, user_id: int, allowed: set[str]
    ) -> set[str]:
        if is_system_admin(cur, user_id):
            return {"system_admin"}
        roles = active_roles(cur, context_id, user_id)
        cur.execute(
            """SELECT role_key
               FROM kindergarten_role_assignments
               WHERE context_id=%s AND user_id=%s AND status='active'
                 AND group_id IS NULL AND role_key=ANY(%s)
                 AND starts_at<=NOW()
                 AND (ends_at IS NULL OR ends_at>NOW())""",
            (context_id, user_id, list(allowed)),
        )
        context_roles = {row["role_key"] for row in cur.fetchall()}
        if not context_roles:
            raise HTTPException(
                status_code=403,
                detail="Bu amal uchun shu bog'chadagi vakolatingiz yetarli emas.",
            )
        return roles

    def validate_role(role_key: str, *, joinable_only: bool = False) -> str:
        allowed = STAFF_ROLES - ({"owner", "founder"} if joinable_only else set())
        if role_key not in allowed:
            raise HTTPException(status_code=400, detail="Noto'g'ri lavozim tanlandi")
        return role_key

    def fetch_draft(cur: Any, draft_id: int, user_id: int, *, lock: bool = False):
        cur.execute(
            f"""SELECT *
                FROM kindergarten_setup_drafts
                WHERE id=%s AND creator_user_id=%s
                {"FOR UPDATE" if lock else ""}""",
            (draft_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Sozlash qoralamasi topilmadi")
        if row["status"] != "draft":
            raise HTTPException(
                status_code=409,
                detail="Bu qoralama allaqachon yakunlangan yoki bekor qilingan",
            )
        if row["expires_at"] <= datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Qoralama muddati tugagan")
        return row

    def parse_time(value: Any, field_name: str) -> str | None:
        if value in (None, ""):
            return None
        text = str(value).strip()
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", text):
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} HH:MM ko'rinishida bo'lishi kerak",
            )
        return text

    def like_literal(value: str) -> str:
        return (
            value.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )

    def aware_utc(value: datetime | None, field_name: str) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} vaqt zonasi bilan yuborilishi kerak",
            )
        return value.astimezone(timezone.utc)

    def draft_validation(draft: Any) -> tuple[dict[str, Any], list[str]]:
        payload = dict(draft["payload"] or {})
        basic = dict(payload.get("basic") or {})
        groups = payload.get("groups") or []
        errors: list[str] = []
        warnings: list[str] = []

        name = str(basic.get("name") or "").strip()
        if len(name) < 3:
            errors.append("Bog'cha nomi kamida 3 ta belgidan iborat bo'lsin")
        if len(name) > 180:
            errors.append("Bog'cha nomi 180 belgidan oshmasin")

        work_start = parse_time(basic.get("work_start"), "Ish boshlanish vaqti")
        work_end = parse_time(basic.get("work_end"), "Ish tugash vaqti")
        if work_start and work_end and work_end <= work_start:
            errors.append("Ish tugash vaqti boshlanish vaqtidan keyin bo'lishi kerak")

        work_days = basic.get("work_days")
        if work_days is None:
            work_days = [1, 2, 3, 4, 5]
        valid_work_days = (
            isinstance(work_days, list)
            and bool(work_days)
            and all(
                isinstance(day, int) and 1 <= day <= 7
                for day in work_days
            )
        )
        if (
            not valid_work_days
        ):
            errors.append("Ish kunlarini 1–7 oralig'ida tanlang")
            work_days = [1, 2, 3, 4, 5]

        capacity = basic.get("capacity")
        if capacity not in (None, ""):
            try:
                capacity = int(capacity)
                if capacity < 1 or capacity > 10000:
                    errors.append("Umumiy sig'im 1–10000 oralig'ida bo'lsin")
            except (TypeError, ValueError):
                errors.append("Umumiy sig'im son bilan yozilsin")

        payment_enabled = bool(basic.get("payment_enabled", False))
        monthly_fee = basic.get("monthly_fee")
        if draft["ownership_type"] == "public" and payment_enabled:
            warnings.append(
                "Davlat bog'chasida to'lov faqat vakolatli tasdiqdan keyin yoqiladi"
            )
        if payment_enabled:
            try:
                monthly_fee = Decimal(str(monthly_fee))
                if monthly_fee < 0:
                    errors.append("Oylik to'lov manfiy bo'lmaydi")
            except (InvalidOperation, TypeError, ValueError):
                errors.append("To'lov yoqilgan bo'lsa, oylik summani kiriting")

        clean_groups: list[dict[str, Any]] = []
        if not isinstance(groups, list):
            errors.append("Guruhlar ro'yxati noto'g'ri")
            groups = []
        for index, group in enumerate(groups[:100], start=1):
            if not isinstance(group, dict):
                errors.append(f"{index}-guruh ma'lumoti noto'g'ri")
                continue
            group_name = str(group.get("name") or "").strip()
            if len(group_name) < 2:
                errors.append(f"{index}-guruh nomini kiriting")
                continue
            age_min = group.get("age_min_months")
            age_max = group.get("age_max_months")
            group_capacity = group.get("capacity")
            try:
                age_min = int(age_min) if age_min not in (None, "") else None
                age_max = int(age_max) if age_max not in (None, "") else None
                group_capacity = (
                    int(group_capacity)
                    if group_capacity not in (None, "")
                    else None
                )
            except (TypeError, ValueError):
                errors.append(f"{group_name}: yosh yoki sig'im son bilan yozilsin")
                continue
            if age_min is not None and not 0 <= age_min <= 120:
                errors.append(f"{group_name}: eng kichik yosh 0–120 oy bo'lsin")
            if age_max is not None and not 0 <= age_max <= 120:
                errors.append(f"{group_name}: eng katta yosh 0–120 oy bo'lsin")
            if age_min is not None and age_max is not None and age_max < age_min:
                errors.append(f"{group_name}: yosh oralig'i teskari kiritilgan")
            if group_capacity is not None and not 1 <= group_capacity <= 100:
                errors.append(f"{group_name}: sig'im 1–100 oralig'ida bo'lsin")
            clean_groups.append(
                {
                    "name": group_name,
                    "age_min_months": age_min,
                    "age_max_months": age_max,
                    "capacity": group_capacity,
                    "room_name": str(group.get("room_name") or "").strip() or None,
                }
            )
        if len(groups) > 100:
            errors.append("Bir sozlashda 100 tadan ko'p guruh kiritmang")
        if not clean_groups:
            warnings.append("Guruhni hozir yoki bog'cha ochilgandan keyin yaratishingiz mumkin")

        if draft["ownership_type"] == "public" and draft["relationship"] == "owner":
            errors.append("Davlat bog'chasida mulkdor roli bo'lmaydi")
        if draft["relationship"] == "educator":
            errors.append(
                "Tarbiyachi yangi bog'cha ochmaydi; mavjud bog'chaga qo'shilish so'rovini yuboradi"
            )

        summary = {
            "name": name,
            "ownership_type": draft["ownership_type"],
            "relationship": draft["relationship"],
            "setup_mode": draft["setup_mode"],
            "region": str(basic.get("region") or "").strip() or None,
            "district": str(basic.get("district") or "").strip() or None,
            "address": str(basic.get("address") or "").strip() or None,
            "phone": str(basic.get("phone") or "").strip() or None,
            "work_start": work_start,
            "work_end": work_end,
            "work_days": sorted(set(work_days)),
            "capacity": capacity,
            "language": str(basic.get("language") or "uz").strip() or "uz",
            "payment_enabled": payment_enabled,
            "monthly_fee": monthly_fee if payment_enabled else None,
            "groups": clean_groups,
            "group_count": len(clean_groups),
        }
        if errors:
            raise HTTPException(
                status_code=422,
                detail={"message": "Qoralamada tuzatish kerak", "errors": errors},
            )
        return summary, warnings

    def legacy_membership(
        cur: Any,
        *,
        user_id: int,
        legacy_bogcha_id: int,
        role_key: str,
    ) -> None:
        legacy_role = ROLE_TO_LEGACY.get(role_key, "bogcha_opa")
        cur.execute(
            """INSERT INTO foydalanuvchi_muassasalari(
                   user_id, muassasa_turi, muassasa_id, lavozim
               )
               VALUES(%s,'bogcha',%s,%s)
               ON CONFLICT (user_id, muassasa_turi, muassasa_id)
               DO UPDATE SET lavozim=EXCLUDED.lavozim""",
            (user_id, legacy_bogcha_id, legacy_role),
        )
        cur.execute(
            """UPDATE users
               SET bogcha_id=%s,lavozim=%s
               WHERE user_id=%s
                 AND maktab_id IS NULL
                 AND markaz_id IS NULL
                 AND bogcha_id IS NULL
                 AND universitet_id IS NULL""",
            (legacy_bogcha_id, legacy_role, user_id),
        )

    def add_role(
        cur: Any,
        *,
        context_id: int,
        user_id: int,
        role_key: str,
        status: str,
        approved_by: int | None,
        group_id: int | None = None,
    ) -> None:
        cur.execute(
            """INSERT INTO kindergarten_role_assignments(
                   context_id,group_id,user_id,role_key,status,
                   approved_by_user_id,permissions
               )
               VALUES(
                   %s,%s,%s,%s,%s,%s,
                   '{"source":"kindergarten_v2"}'::jsonb
               )
               ON CONFLICT(
                   context_id,(COALESCE(group_id,0)),user_id,role_key
               ) DO UPDATE SET
                   status=EXCLUDED.status,
                   approved_by_user_id=EXCLUDED.approved_by_user_id,
                   permissions=kindergarten_role_assignments.permissions
                               || EXCLUDED.permissions,
                   starts_at=NOW(),ends_at=NULL,updated_at=NOW()""",
            (context_id, group_id, user_id, role_key, status, approved_by),
        )
        generic_role = "manager" if role_key in MANAGER_ROLES else "teacher"
        cur.execute(
            """INSERT INTO context_memberships(
                   context_id,group_id,user_id,member_role,status,source,
                   approved_by_user_id,metadata
               )
               VALUES(%s,%s,%s,%s,%s,'kindergarten_v2',%s,%s::jsonb)
               ON CONFLICT(
                   context_id,(COALESCE(group_id,0)),user_id,member_role
               ) DO UPDATE SET
                   status=EXCLUDED.status,
                   source=EXCLUDED.source,
                   approved_by_user_id=EXCLUDED.approved_by_user_id,
                   ended_at=NULL,updated_at=NOW(),
                   metadata=EXCLUDED.metadata""",
            (
                context_id,
                group_id,
                user_id,
                generic_role,
                status,
                approved_by,
                json.dumps({"kindergarten_role": role_key}, ensure_ascii=False),
            ),
        )

    def create_group_records(
        cur: Any,
        *,
        context_id: int,
        legacy_bogcha_id: int,
        group: dict[str, Any],
        teacher_user_id: int | None = None,
    ) -> int:
        cur.execute(
            """INSERT INTO bogcha_guruhlari(
                   bogcha_id,nomi,opa_user_id,qoshilish_paroli
               )
               VALUES(%s,%s,%s,NULL) RETURNING id""",
            (legacy_bogcha_id, group["name"], teacher_user_id),
        )
        legacy_group_id = cur.fetchone()["id"]
        cur.execute(
            """INSERT INTO course_groups(
                   context_id,group_type,delivery_mode,name,teacher_user_id,
                   external_type,external_id,metadata
               )
               VALUES(%s,'kindergarten_group','offline',%s,%s,
                      'bogcha_guruh',%s,%s::jsonb)
               RETURNING id""",
            (
                context_id,
                group["name"],
                teacher_user_id,
                legacy_group_id,
                json.dumps(
                    {
                        "age_min_months": group.get("age_min_months"),
                        "age_max_months": group.get("age_max_months"),
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        group_id = cur.fetchone()["id"]
        cur.execute(
            """INSERT INTO kindergarten_group_profiles(
                   group_id,context_id,legacy_group_id,age_min_months,
                   age_max_months,capacity,room_name,work_start,work_end
               )
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                group_id,
                context_id,
                legacy_group_id,
                group.get("age_min_months"),
                group.get("age_max_months"),
                group.get("capacity"),
                group.get("room_name"),
                group.get("work_start"),
                group.get("work_end"),
            ),
        )
        return group_id

    @router.get("/health")
    def health() -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            cur.execute("SELECT NOW() AS database_time")
            row = cur.fetchone()
        return {
            "status": "ready",
            "module": "kindergarten-v2",
            "schema": "004_kindergarten_hardening",
            "database_time": row["database_time"],
        }

    @router.get("/onboarding/options")
    def onboarding_options(
        _user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        return {
            "institution_types": [
                {"value": "private", "label": "Xususiy bog'cha"},
                {"value": "public", "label": "Davlat bog'chasi"},
            ],
            "relationships": [
                {
                    "value": "owner",
                    "label": "Mulkdor / ta'sischi",
                    "allowed_for": ["private"],
                    "flow": "create",
                },
                {
                    "value": "director",
                    "label": "Direktor",
                    "allowed_for": ["private", "public"],
                    "flow": "create_or_join",
                },
                {
                    "value": "administrator",
                    "label": "Administrator",
                    "allowed_for": ["private", "public"],
                    "flow": "create_or_join",
                },
                {
                    "value": "educator",
                    "label": "Tarbiyachi / xodim",
                    "allowed_for": ["private", "public"],
                    "flow": "join",
                },
            ],
            "setup_modes": [
                {"value": "guided", "label": "Bosqichma-bosqich"},
                {"value": "assistant", "label": "AI avatar bilan"},
                {"value": "manual", "label": "O'zim to'ldiraman"},
            ],
            "steps": [
                "relationship",
                "method",
                "basics",
                "schedule",
                "groups",
                "team",
                "preview",
            ],
            "notice": (
                "Bu platformadagi raqamli profil. Davlat ro'yxatidan o'tkazish "
                "yoki litsenziya berish amali emas."
            ),
        }

    @router.post("/onboarding/start")
    def onboarding_start(request: DraftStart) -> dict[str, Any]:
        user_id = current_user(request.token)
        if request.ownership_type == "public" and request.relationship == "owner":
            raise HTTPException(
                status_code=400,
                detail="Davlat bog'chasida mulkdor rolini tanlab bo'lmaydi",
            )
        if request.relationship == "educator":
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Tarbiyachi mavjud bog'chaga qo'shiladi",
                    "next": "search_and_join",
                },
            )
        initial_payload = {
            "avatar": {
                "enabled": request.avatar_enabled,
                "speech_enabled": request.speech_enabled,
                "variant": request.avatar_variant,
            }
        }
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """INSERT INTO kindergarten_setup_drafts(
                       creator_user_id,relationship,ownership_type,setup_mode,
                       current_step,payload
                   )
                   VALUES(%s,%s,%s,%s,'basics',%s::jsonb)
                   RETURNING id,version,current_step,expires_at""",
                (
                    user_id,
                    request.relationship,
                    request.ownership_type,
                    request.setup_mode,
                    json.dumps(initial_payload, ensure_ascii=False),
                ),
            )
            draft = cur.fetchone()
        return {
            "draft": draft,
            "message": "Qoralama yaratildi. Yakuniy tasdiqqacha bog'cha ochilmaydi.",
        }

    @router.get("/onboarding/drafts")
    def onboarding_drafts(
        user_id: int = Depends(authenticated_user),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT id,relationship,ownership_type,setup_mode,current_step,
                          status,payload,version,created_at,updated_at,expires_at,
                          confirmed_context_id
                   FROM kindergarten_setup_drafts
                   WHERE creator_user_id=%s
                   ORDER BY updated_at DESC LIMIT %s""",
                (user_id, limit),
            )
            rows = cur.fetchall()
        return {"drafts": rows}

    @router.get("/onboarding/{draft_id}")
    def onboarding_draft(
        draft_id: int,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            draft = fetch_draft(cur, draft_id, user_id)
        return {"draft": draft}

    @router.put("/onboarding/{draft_id}/step")
    def onboarding_update(draft_id: int, request: DraftUpdate) -> dict[str, Any]:
        user_id = current_user(request.token)
        if request.step not in ALLOWED_STEPS:
            raise HTTPException(status_code=400, detail="Noto'g'ri sozlash bosqichi")
        encoded = json.dumps(request.payload, ensure_ascii=False)
        if len(encoded.encode("utf-8")) > 120_000:
            raise HTTPException(status_code=413, detail="Qoralama ma'lumoti juda katta")
        with database() as (_, cur):
            ensure_schema(cur)
            draft = fetch_draft(cur, draft_id, user_id, lock=True)
            if draft["version"] != request.expected_version:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Qoralama boshqa oynada yangilangan",
                        "current_version": draft["version"],
                    },
                )
            cur.execute(
                """UPDATE kindergarten_setup_drafts
                   SET payload=payload || %s::jsonb,
                       current_step=%s,version=version+1,updated_at=NOW()
                   WHERE id=%s
                   RETURNING id,payload,current_step,version,updated_at""",
                (encoded, request.step, draft_id),
            )
            updated = cur.fetchone()
        return {"draft": updated}

    @router.post("/onboarding/{draft_id}/preview")
    def onboarding_preview(
        draft_id: int,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            draft = fetch_draft(cur, draft_id, user_id)
            summary, warnings = draft_validation(draft)
            cur.execute(
                """SELECT 1 FROM learning_contexts
                   WHERE context_type='kindergarten'
                     AND lower(name)=lower(%s)
                     AND COALESCE(region,'')=COALESCE(%s,'')
                     AND active=TRUE LIMIT 1""",
                (summary["name"], summary["region"]),
            )
            if cur.fetchone():
                warnings.append(
                    "Shu nom va hududga o'xshash bog'cha mavjud; takror emasligini tekshiring"
                )
        return {
            "summary": summary,
            "warnings": warnings,
            "requires_human_confirmation": True,
            "legal_notice": (
                "Tasdiqlash platformada raqamli ish maydonini yaratadi; "
                "yuridik ro'yxatdan o'tkazmaydi."
            ),
        }

    @router.post("/onboarding/{draft_id}/confirm")
    def onboarding_confirm(draft_id: int, request: DraftConfirm) -> dict[str, Any]:
        user_id = current_user(request.token)
        if not request.confirmation:
            raise HTTPException(
                status_code=400,
                detail="Bog'chani yaratish uchun foydalanuvchi tasdig'i shart",
            )
        with database() as (_, cur):
            ensure_schema(cur)
            draft = fetch_draft(cur, draft_id, user_id, lock=True)
            if draft["version"] != request.expected_version:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Qoralama yangilangan; qayta ko'rib tasdiqlang",
                        "current_version": draft["version"],
                    },
                )
            summary, warnings = draft_validation(draft)
            is_public = draft["ownership_type"] == "public"
            profile_status = "pending_verification" if is_public else "active"
            verification = "pending" if is_public else "unverified"
            role_status = "pending" if is_public else "active"
            director_id = (
                user_id if draft["relationship"] in {"owner", "director"} else None
            )
            legacy_type = "davlat" if is_public else "xususiy"

            cur.execute(
                """INSERT INTO bogchalar(
                       nomi,turi,viloyat,tuman,direktor_user_id,oylik_tolov
                   )
                   VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    summary["name"],
                    legacy_type,
                    summary["region"],
                    summary["district"],
                    director_id,
                    summary["monthly_fee"],
                ),
            )
            legacy_bogcha_id = cur.fetchone()["id"]
            cur.execute(
                """INSERT INTO learning_contexts(
                       context_type,name,owner_user_id,region,district,
                       external_type,external_id,active,metadata
                   )
                   VALUES(
                       'kindergarten',%s,%s,%s,%s,'bogcha',%s,%s,%s::jsonb
                   )
                   RETURNING id""",
                (
                    summary["name"],
                    user_id if not is_public else None,
                    summary["region"],
                    summary["district"],
                    legacy_bogcha_id,
                    not is_public,
                    json.dumps(
                        {
                            "address": summary["address"],
                            "phone": summary["phone"],
                            "created_via": "kindergarten_v2",
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
            context_id = cur.fetchone()["id"]
            cur.execute(
                """INSERT INTO kindergarten_profiles(
                       context_id,legacy_bogcha_id,ownership_type,
                       onboarding_status,verification_status,work_start,work_end,
                       work_days,capacity,language,payment_enabled,monthly_fee
                   )
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    context_id,
                    legacy_bogcha_id,
                    draft["ownership_type"],
                    profile_status,
                    verification,
                    summary["work_start"],
                    summary["work_end"],
                    summary["work_days"],
                    summary["capacity"],
                    summary["language"],
                    summary["payment_enabled"] and not is_public,
                    summary["monthly_fee"] if not is_public else None,
                ),
            )

            selected_roles = [draft["relationship"]]
            if draft["relationship"] == "owner":
                selected_roles.append("director")
            for role_key in selected_roles:
                add_role(
                    cur,
                    context_id=context_id,
                    user_id=user_id,
                    role_key=role_key,
                    status=role_status,
                    approved_by=None if is_public else user_id,
                )

            created_group_ids = []
            for group in summary["groups"]:
                created_group_ids.append(
                    create_group_records(
                        cur,
                        context_id=context_id,
                        legacy_bogcha_id=legacy_bogcha_id,
                        group=group,
                        teacher_user_id=None,
                    )
                )

            if not is_public:
                legacy_membership(
                    cur,
                    user_id=user_id,
                    legacy_bogcha_id=legacy_bogcha_id,
                    role_key=draft["relationship"],
                )
            cur.execute(
                """UPDATE kindergarten_setup_drafts
                   SET status='confirmed',confirmed_context_id=%s,
                       current_step='preview',version=version+1,updated_at=NOW()
                   WHERE id=%s""",
                (context_id, draft_id),
            )

        return {
            "status": profile_status,
            "context_id": context_id,
            "legacy_bogcha_id": legacy_bogcha_id,
            "group_ids": created_group_ids,
            "warnings": warnings,
            "next": (
                "admin_verification"
                if is_public
                else "kindergarten_dashboard"
            ),
            "message": (
                "Davlat bog'chasi profili tekshiruvga yuborildi"
                if is_public
                else "Bog'cha ish maydoni yaratildi"
            ),
        }

    @router.get("/workspaces")
    def workspaces(
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT c.id AS context_id,c.name,c.region,c.district,c.active,
                          p.ownership_type,p.onboarding_status,
                          p.verification_status,p.legacy_bogcha_id,
                          r.role_key,r.status AS role_status
                   FROM kindergarten_role_assignments r
                   JOIN learning_contexts c ON c.id=r.context_id
                   JOIN kindergarten_profiles p ON p.context_id=c.id
                   WHERE r.user_id=%s AND r.status IN ('active','pending')
                   ORDER BY c.name,r.role_key""",
                (user_id,),
            )
            rows = cur.fetchall()
            cur.execute(
                """SELECT j.id,j.context_id,c.name,j.requested_role,j.status,
                          j.created_at
                   FROM kindergarten_join_requests j
                   JOIN learning_contexts c ON c.id=j.context_id
                   WHERE j.user_id=%s AND j.status='pending'
                   ORDER BY j.created_at DESC""",
                (user_id,),
            )
            requests = cur.fetchall()

        grouped: dict[int, dict[str, Any]] = {}
        for row in rows:
            context_id = row["context_id"]
            item = grouped.setdefault(
                context_id,
                {
                    "context_id": context_id,
                    "name": row["name"],
                    "region": row["region"],
                    "district": row["district"],
                    "active": row["active"],
                    "ownership_type": row["ownership_type"],
                    "onboarding_status": row["onboarding_status"],
                    "verification_status": row["verification_status"],
                    "legacy_bogcha_id": row["legacy_bogcha_id"],
                    "roles": [],
                    "role_status": row["role_status"],
                },
            )
            item["roles"].append(row["role_key"])
            if row["role_status"] == "active":
                item["role_status"] = "active"
        return {"workspaces": list(grouped.values()), "pending_requests": requests}

    @router.get("/search")
    def search_kindergartens(
        q: str = Query(min_length=2, max_length=100),
        _user_id: int = Depends(authenticated_user),
        region: str | None = None,
        limit: int = Query(default=20, ge=1, le=50),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT c.id AS context_id,c.name,c.region,c.district,
                          p.ownership_type,p.verification_status
                   FROM learning_contexts c
                   JOIN kindergarten_profiles p ON p.context_id=c.id
                   WHERE c.context_type='kindergarten'
                     AND c.active=TRUE
                     AND c.name ILIKE %s ESCAPE '\'
                     AND (%s IS NULL OR c.region=%s)
                   ORDER BY
                     CASE WHEN lower(c.name)=lower(%s) THEN 0 ELSE 1 END,
                     c.name
                   LIMIT %s""",
                (
                    f"%{like_literal(q.strip())}%",
                    region,
                    region,
                    q.strip(),
                    limit,
                ),
            )
            rows = cur.fetchall()
        return {"results": rows}

    @router.post("/join-requests")
    def create_join_request(request: JoinRequestCreate) -> dict[str, Any]:
        user_id = current_user(request.token)
        role_key = validate_role(request.requested_role, joinable_only=True)
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT c.id,p.onboarding_status
                   FROM learning_contexts c
                   JOIN kindergarten_profiles p ON p.context_id=c.id
                   WHERE c.id=%s AND c.context_type='kindergarten'
                     AND c.active=TRUE""",
                (request.context_id,),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail="Faol bog'cha topilmadi yoki hali tasdiqlanmagan",
                )
            if active_roles(cur, request.context_id, user_id):
                raise HTTPException(
                    status_code=409,
                    detail="Siz bu bog'chaga allaqachon ulangansiz",
                )
            cur.execute(
                """INSERT INTO kindergarten_join_requests(
                       context_id,user_id,requested_role,note
                   )
                   VALUES(%s,%s,%s,%s)
                   ON CONFLICT DO NOTHING
                   RETURNING id,status,created_at""",
                (
                    request.context_id,
                    user_id,
                    role_key,
                    (request.note or "").strip()[:500] or None,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=409,
                    detail="Bu lavozim uchun so'rov avval yuborilgan",
                )
        return {"request": row, "message": "So'rov bog'cha rahbariyatiga yuborildi"}

    @router.get("/join-requests")
    def list_join_requests(
        context_id: int,
        user_id: int = Depends(authenticated_user),
        after_id: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, MANAGER_ROLES)
            cur.execute(
                """SELECT j.id,j.user_id,u.full_name,j.requested_role,j.note,
                          j.status,j.created_at
                   FROM kindergarten_join_requests j
                   JOIN users u ON u.user_id=j.user_id
                   WHERE j.context_id=%s AND j.status='pending' AND j.id>%s
                   ORDER BY j.id LIMIT %s""",
                (context_id, after_id, limit + 1),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
            "has_more": len(rows) > limit,
        }

    @router.post("/join-requests/decision")
    def decide_join_request(request: JoinDecision) -> dict[str, Any]:
        reviewer_id = current_user(request.token)
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM kindergarten_join_requests
                   WHERE id=%s FOR UPDATE""",
                (request.request_id,),
            )
            join_request = cur.fetchone()
            if not join_request:
                raise HTTPException(status_code=404, detail="So'rov topilmadi")
            reviewer_roles = require_roles(
                cur, join_request["context_id"], reviewer_id, MANAGER_ROLES
            )
            if (
                join_request["requested_role"] in PRIVILEGED_ROLES
                and not reviewer_roles.intersection(
                    {"system_admin", "owner", "founder", "director"}
                )
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Yuqori rahbarlik rolini faqat mulkdor yoki direktor tasdiqlaydi",
                )
            if join_request["status"] != "pending":
                raise HTTPException(status_code=409, detail="So'rov allaqachon ko'rilgan")
            status = "approved" if request.approve else "rejected"
            cur.execute(
                """UPDATE kindergarten_join_requests
                   SET status=%s,reviewed_by_user_id=%s,reviewed_at=NOW(),
                       updated_at=NOW()
                   WHERE id=%s""",
                (status, reviewer_id, request.request_id),
            )
            if request.approve:
                add_role(
                    cur,
                    context_id=join_request["context_id"],
                    user_id=join_request["user_id"],
                    role_key=join_request["requested_role"],
                    status="active",
                    approved_by=reviewer_id,
                )
                cur.execute(
                    """SELECT legacy_bogcha_id
                       FROM kindergarten_profiles WHERE context_id=%s""",
                    (join_request["context_id"],),
                )
                profile = cur.fetchone()
                if profile and profile["legacy_bogcha_id"]:
                    legacy_membership(
                        cur,
                        user_id=join_request["user_id"],
                        legacy_bogcha_id=profile["legacy_bogcha_id"],
                        role_key=join_request["requested_role"],
                    )
        return {"status": status}

    @router.post("/staff/invite")
    def invite_staff(request: InviteCreate) -> dict[str, Any]:
        creator_id = current_user(request.token)
        role_key = validate_role(request.role_key, joinable_only=True)
        with database() as (_, cur):
            ensure_schema(cur)
            creator_roles = require_roles(
                cur, request.context_id, creator_id, MANAGER_ROLES
            )
            if (
                role_key in PRIVILEGED_ROLES
                and not creator_roles.intersection(
                    {"system_admin", "owner", "founder", "director"}
                )
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Yuqori rahbarlik roliga taklifni faqat mulkdor yoki direktor yaratadi",
                )
            if role_key in MANAGER_ROLES and request.group_id is not None:
                raise HTTPException(
                    status_code=400,
                    detail="Rahbarlik roli alohida guruhga emas, bog'chaga beriladi",
                )
            if request.group_id is not None:
                cur.execute(
                    "SELECT 1 FROM course_groups WHERE id=%s AND context_id=%s AND active=TRUE",
                    (request.group_id, request.context_id),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=400, detail="Guruh topilmadi")
            alphabet = string.ascii_uppercase + string.digits
            code = "-".join(
                "".join(secrets.choice(alphabet) for _ in range(4))
                for _ in range(2)
            )
            code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
            cur.execute(
                """INSERT INTO kindergarten_staff_invitations(
                       context_id,group_id,role_key,invite_code_hash,
                       invited_name,invited_contact,created_by_user_id
                   )
                   VALUES(%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id,expires_at""",
                (
                    request.context_id,
                    request.group_id,
                    role_key,
                    code_hash,
                    (request.invited_name or "").strip()[:160] or None,
                    (request.invited_contact or "").strip()[:160] or None,
                    creator_id,
                ),
            )
            invitation = cur.fetchone()
        return {
            "invitation_id": invitation["id"],
            "invite_code": code,
            "expires_at": invitation["expires_at"],
            "warning": "Kod faqat hozir ko'rsatiladi; uni kerakli xodimga yuboring.",
        }

    @router.post("/staff/accept-invite")
    def accept_invite(request: InviteAccept) -> dict[str, Any]:
        user_id = current_user(request.token)
        normalized = request.invite_code.strip().upper()
        code_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM kindergarten_staff_invitations
                   WHERE invite_code_hash=%s FOR UPDATE""",
                (code_hash,),
            )
            invitation = cur.fetchone()
            if not invitation:
                raise HTTPException(status_code=400, detail="Taklif kodi noto'g'ri")
            if invitation["status"] != "pending":
                raise HTTPException(status_code=409, detail="Taklif kodi ishlatilgan")
            if invitation["expires_at"] <= datetime.now(timezone.utc):
                cur.execute(
                    """UPDATE kindergarten_staff_invitations
                       SET status='expired' WHERE id=%s""",
                    (invitation["id"],),
                )
                raise HTTPException(status_code=410, detail="Taklif muddati tugagan")
            role_key = validate_role(
                invitation["role_key"],
                joinable_only=True,
            )
            cur.execute(
                """SELECT c.active,p.onboarding_status,p.verification_status
                   FROM learning_contexts c
                   JOIN kindergarten_profiles p ON p.context_id=c.id
                   WHERE c.id=%s""",
                (invitation["context_id"],),
            )
            context_state = cur.fetchone()
            if (
                not context_state
                or not context_state["active"]
                or context_state["onboarding_status"] != "active"
                or context_state["verification_status"] == "rejected"
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Bu bog'cha faol emas; taklifni qabul qilib bo'lmaydi.",
                )
            creator_roles = require_roles(
                cur,
                invitation["context_id"],
                invitation["created_by_user_id"],
                MANAGER_ROLES,
            )
            if (
                role_key in PRIVILEGED_ROLES
                and not creator_roles.intersection(
                    {"system_admin", "owner", "founder", "director"}
                )
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Bu rahbarlik taklifi vakolatli shaxs tomonidan yaratilmagan.",
                )
            if role_key in MANAGER_ROLES and invitation["group_id"] is not None:
                raise HTTPException(
                    status_code=400,
                    detail="Rahbarlik taklifi alohida guruhga biriktirilmaydi.",
                )
            if invitation["group_id"] is not None:
                cur.execute(
                    """SELECT 1 FROM course_groups
                       WHERE id=%s AND context_id=%s AND active=TRUE""",
                    (invitation["group_id"], invitation["context_id"]),
                )
                if not cur.fetchone():
                    raise HTTPException(
                        status_code=400,
                        detail="Taklifdagi guruh faol emas yoki topilmadi.",
                    )
            add_role(
                cur,
                context_id=invitation["context_id"],
                group_id=invitation["group_id"],
                user_id=user_id,
                role_key=role_key,
                status="active",
                approved_by=invitation["created_by_user_id"],
            )
            if (
                invitation["group_id"] is not None
                and role_key == "educator"
            ):
                cur.execute(
                    """UPDATE course_groups
                       SET teacher_user_id=%s,updated_at=NOW()
                       WHERE id=%s AND context_id=%s""",
                    (
                        user_id,
                        invitation["group_id"],
                        invitation["context_id"],
                    ),
                )
                cur.execute(
                    """UPDATE bogcha_guruhlari bg
                       SET opa_user_id=%s
                       FROM kindergarten_group_profiles gp
                       WHERE gp.group_id=%s
                         AND bg.id=gp.legacy_group_id""",
                    (user_id, invitation["group_id"]),
                )
            cur.execute(
                """UPDATE kindergarten_staff_invitations
                   SET status='accepted',accepted_by_user_id=%s,accepted_at=NOW()
                   WHERE id=%s""",
                (user_id, invitation["id"]),
            )
            cur.execute(
                "SELECT legacy_bogcha_id FROM kindergarten_profiles WHERE context_id=%s",
                (invitation["context_id"],),
            )
            profile = cur.fetchone()
            if profile and profile["legacy_bogcha_id"]:
                legacy_membership(
                    cur,
                    user_id=user_id,
                    legacy_bogcha_id=profile["legacy_bogcha_id"],
                    role_key=role_key,
                )
        return {
            "status": "accepted",
            "context_id": invitation["context_id"],
            "role": role_key,
        }

    @router.get("/dashboard")
    def dashboard(
        context_id: int,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            roles, group_scope = allowed_group_scope(
                cur, context_id, user_id, STAFF_ROLES
            )
            cur.execute(
                """SELECT c.id,c.name,c.region,c.district,c.active,
                          p.ownership_type,p.onboarding_status,
                          p.verification_status,p.work_start,p.work_end,
                          p.work_days,p.capacity,p.language,p.payment_enabled,
                          p.monthly_fee,p.legacy_bogcha_id,p.timezone
                   FROM learning_contexts c
                   JOIN kindergarten_profiles p ON p.context_id=c.id
                   WHERE c.id=%s""",
                (context_id,),
            )
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="Bog'cha topilmadi")
            scope_all = group_scope is None
            scoped_groups = list(group_scope or [])
            cur.execute(
                """SELECT
                     (SELECT COUNT(*) FROM course_groups
                      WHERE context_id=%s AND group_type='kindergarten_group'
                        AND active=TRUE
                        AND (%s OR id=ANY(%s))) AS groups,
                     (SELECT COUNT(DISTINCT user_id)
                      FROM kindergarten_role_assignments
                      WHERE context_id=%s AND status='active'
                        AND role_key NOT IN ('parent','child')) AS staff,
                     (SELECT COUNT(*) FROM kindergarten_children
                      WHERE context_id=%s AND enrollment_status='active'
                        AND (%s OR group_id=ANY(%s))) AS children,
                     (SELECT COUNT(*) FROM kindergarten_attendance
                      WHERE context_id=%s
                        AND attendance_date=(
                          NOW() AT TIME ZONE %s
                        )::date
                        AND (%s OR group_id=ANY(%s))
                        AND status IN ('present','late')) AS present_today,
                     (SELECT COUNT(*) FROM kindergarten_calendar_events
                      WHERE context_id=%s AND status='published'
                        AND starts_at>=date_trunc(
                          'day', NOW() AT TIME ZONE %s
                        ) AT TIME ZONE %s
                        AND starts_at<(
                          date_trunc('day', NOW() AT TIME ZONE %s)
                          + INTERVAL '7 days'
                        ) AT TIME ZONE %s
                        AND (
                          %s OR group_id IS NULL OR group_id=ANY(%s)
                        )) AS events_week,
                     (SELECT COUNT(*) FROM kindergarten_invoices
                      WHERE context_id=%s AND status IN ('unpaid','partial')
                        AND due_date<(
                          NOW() AT TIME ZONE %s
                        )::date) AS overdue_invoices""",
                (
                    context_id,
                    scope_all,
                    scoped_groups,
                    context_id,
                    context_id,
                    scope_all,
                    scoped_groups,
                    context_id,
                    profile["timezone"],
                    scope_all,
                    scoped_groups,
                    context_id,
                    profile["timezone"],
                    profile["timezone"],
                    profile["timezone"],
                    profile["timezone"],
                    scope_all,
                    scoped_groups,
                    context_id,
                    profile["timezone"],
                ),
            )
            metrics = cur.fetchone()

        checklist = [
            {
                "key": "settings",
                "label": "Bog'cha asosiy ma'lumotlari",
                "done": bool(profile["name"] and profile["work_start"] and profile["work_end"]),
            },
            {
                "key": "groups",
                "label": "Kamida bitta guruh",
                "done": metrics["groups"] > 0,
            },
            {
                "key": "staff",
                "label": "Xodimlar va rollar",
                "done": metrics["staff"] > 1,
            },
            {
                "key": "children",
                "label": "Bolalar ro'yxati",
                "done": metrics["children"] > 0,
            },
            {
                "key": "calendar",
                "label": "Haftalik kalendar",
                "done": metrics["events_week"] > 0,
            },
        ]
        is_manager = bool(
            roles.intersection(MANAGER_ROLES | {"system_admin"})
        )
        can_view_groups = bool(
            roles.intersection(GROUP_VIEW_ROLES | {"system_admin"})
        )
        can_view_children = bool(
            roles.intersection(CHILD_VIEW_ROLES | {"system_admin"})
        )
        can_edit_attendance = bool(
            roles.intersection(ATTENDANCE_EDIT_ROLES | {"system_admin"})
        )
        can_write_daily_report = bool(
            roles.intersection(DAILY_REPORT_ROLES | {"system_admin"})
        )
        can_manage_payments = bool(
            roles.intersection(PAYMENT_ROLES | {"system_admin"})
        )
        role_menu = [
            {"key": "overview", "label": "Bosh sahifa", "all": True},
            {"key": "groups", "label": "Guruhlar", "all": can_view_groups},
            {"key": "children", "label": "Bolalar", "all": can_view_children},
            {"key": "attendance", "label": "Davomat", "all": can_edit_attendance},
            {
                "key": "daily_reports",
                "label": "Kunlik hisobot",
                "all": can_write_daily_report,
            },
            {"key": "calendar", "label": "Kalendar", "all": True},
            {
                "key": "staff",
                "label": "Xodimlar",
                "all": is_manager,
            },
            {
                "key": "payments",
                "label": "To'lovlar",
                "all": bool(
                    can_manage_payments and profile["ownership_type"] == "private"
                ),
            },
            {
                "key": "settings",
                "label": "Sozlamalar",
                "all": is_manager,
            },
        ]
        if not can_view_groups:
            metrics["groups"] = None
        if not can_view_children:
            metrics["children"] = None
        if not can_edit_attendance:
            metrics["present_today"] = None
        if not is_manager:
            metrics["staff"] = None
        if not can_manage_payments:
            metrics["overdue_invoices"] = None
        if not is_manager:
            checklist = []
        return {
            "profile": profile,
            "roles": sorted(roles),
            "role_labels": [ROLE_LABELS.get(role, role) for role in sorted(roles)],
            "metrics": metrics,
            "menu": [item for item in role_menu if item["all"]],
            "checklist": checklist,
        }

    @router.get("/groups")
    def groups(
        context_id: int,
        user_id: int = Depends(authenticated_user),
        after_id: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, group_scope = allowed_group_scope(
                cur, context_id, user_id, GROUP_VIEW_ROLES
            )
            cur.execute(
                """SELECT cg.id,cg.name,cg.teacher_user_id,u.full_name AS teacher_name,
                          gp.age_min_months,gp.age_max_months,gp.capacity,
                          gp.room_name,gp.work_start,gp.work_end,
                          (SELECT COUNT(*) FROM kindergarten_children ch
                           WHERE ch.group_id=cg.id
                             AND ch.enrollment_status='active') AS child_count
                   FROM course_groups cg
                   LEFT JOIN kindergarten_group_profiles gp ON gp.group_id=cg.id
                   LEFT JOIN users u ON u.user_id=cg.teacher_user_id
                   WHERE cg.context_id=%s
                     AND cg.group_type='kindergarten_group'
                     AND cg.active=TRUE AND cg.id>%s
                     AND (%s OR cg.id=ANY(%s))
                   ORDER BY cg.id LIMIT %s""",
                (
                    context_id,
                    after_id,
                    group_scope is None,
                    list(group_scope or []),
                    limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
            "has_more": len(rows) > limit,
        }

    @router.post("/groups")
    def create_group(request: GroupCreate) -> dict[str, Any]:
        user_id = current_user(request.token)
        name = request.name.strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Guruh nomini kiriting")
        if (
            request.age_min_months is not None
            and request.age_max_months is not None
            and request.age_max_months < request.age_min_months
        ):
            raise HTTPException(status_code=400, detail="Yosh oralig'i teskari")
        work_start = parse_time(request.work_start, "Boshlanish vaqti")
        work_end = parse_time(request.work_end, "Tugash vaqti")
        if work_start and work_end and work_end <= work_start:
            raise HTTPException(status_code=400, detail="Tugash vaqti noto'g'ri")
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, MANAGER_ROLES)
            cur.execute(
                "SELECT legacy_bogcha_id FROM kindergarten_profiles WHERE context_id=%s",
                (request.context_id,),
            )
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="Bog'cha topilmadi")
            cur.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (7_410_000_000_000 + request.context_id,),
            )
            cur.execute(
                """SELECT 1 FROM course_groups
                   WHERE context_id=%s AND lower(name)=lower(%s) AND active=TRUE""",
                (request.context_id, name),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="Bu nomdagi guruh mavjud")
            group_id = create_group_records(
                cur,
                context_id=request.context_id,
                legacy_bogcha_id=profile["legacy_bogcha_id"],
                group={
                    "name": name,
                    "age_min_months": request.age_min_months,
                    "age_max_months": request.age_max_months,
                    "capacity": request.capacity,
                    "room_name": (request.room_name or "").strip() or None,
                    "work_start": work_start,
                    "work_end": work_end,
                },
            )
        return {"status": "created", "group_id": group_id}

    @router.get("/staff")
    def staff(
        context_id: int,
        user_id: int = Depends(authenticated_user),
        after_id: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, MANAGER_ROLES)
            cur.execute(
                """SELECT r.id,r.user_id,u.full_name,r.role_key,r.status,
                          r.group_id,cg.name AS group_name,r.starts_at
                   FROM kindergarten_role_assignments r
                   JOIN users u ON u.user_id=r.user_id
                   LEFT JOIN course_groups cg ON cg.id=r.group_id
                   WHERE r.context_id=%s AND r.status IN ('active','pending')
                     AND r.role_key NOT IN ('parent','child') AND r.id>%s
                   ORDER BY r.id LIMIT %s""",
                (context_id, after_id, limit + 1),
            )
            rows = cur.fetchall()
        for row in rows:
            row["role_label"] = ROLE_LABELS.get(row["role_key"], row["role_key"])
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
            "has_more": len(rows) > limit,
        }

    @router.get("/children")
    def children(
        context_id: int,
        user_id: int = Depends(authenticated_user),
        group_id: int | None = None,
        q: str | None = Query(default=None, max_length=100),
        after_id: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, group_scope = allowed_group_scope(
                cur, context_id, user_id, CHILD_VIEW_ROLES
            )
            if (
                group_id is not None
                and group_scope is not None
                and group_id not in group_scope
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Siz faqat biriktirilgan guruh bolalarini ko'ra olasiz.",
                )
            cur.execute(
                """SELECT ch.id,ch.full_name,ch.birth_date,ch.gender,
                          ch.enrollment_status,ch.group_id,cg.name AS group_name,
                          ch.allergies,
                          g.full_name AS guardian_name,g.phone AS guardian_phone
                   FROM kindergarten_children ch
                   LEFT JOIN course_groups cg ON cg.id=ch.group_id
                   LEFT JOIN LATERAL (
                     SELECT full_name,phone FROM kindergarten_guardians
                     WHERE child_id=ch.id
                     ORDER BY is_primary DESC,id LIMIT 1
                   ) g ON TRUE
                   WHERE ch.context_id=%s AND ch.id>%s
                     AND ch.enrollment_status IN ('active','pending','paused')
                     AND (%s IS NULL OR ch.group_id=%s)
                     AND (%s OR ch.group_id=ANY(%s))
                     AND (%s IS NULL OR ch.full_name ILIKE %s)
                   ORDER BY ch.id LIMIT %s""",
                (
                    context_id,
                    after_id,
                    group_id,
                    group_id,
                    group_scope is None,
                    list(group_scope or []),
                    q,
                    f"%{q.strip()}%" if q else None,
                    limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
            "has_more": len(rows) > limit,
        }

    @router.post("/children")
    def create_child(request: ChildCreate) -> dict[str, Any]:
        user_id = current_user(request.token)
        full_name = request.full_name.strip()
        if len(full_name) < 3:
            raise HTTPException(status_code=400, detail="Bola F.I.Sh.ini kiriting")
        with database() as (_, cur):
            ensure_schema(cur)
            _, group_scope = allowed_group_scope(
                cur, request.context_id, user_id, EDIT_CHILD_ROLES
            )
            legacy_group_id = None
            if request.group_id is not None:
                if (
                    group_scope is not None
                    and request.group_id not in group_scope
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Siz faqat biriktirilgan guruhga bola qo'sha olasiz.",
                    )
                cur.execute(
                    """SELECT gp.legacy_group_id
                       FROM course_groups cg
                       LEFT JOIN kindergarten_group_profiles gp
                         ON gp.group_id=cg.id
                       WHERE cg.id=%s AND cg.context_id=%s
                         AND cg.group_type='kindergarten_group'
                         AND cg.active=TRUE""",
                    (request.group_id, request.context_id),
                )
                group_row = cur.fetchone()
                if not group_row:
                    raise HTTPException(status_code=400, detail="Guruh topilmadi")
                legacy_group_id = group_row["legacy_group_id"]
            elif group_scope is not None:
                raise HTTPException(
                    status_code=400,
                    detail="Biriktirilgan guruhingizni tanlang",
                )
            cur.execute(
                """INSERT INTO kindergarten_children(
                       context_id,group_id,full_name,birth_date,gender,
                       allergies,medical_notes,created_by_user_id
                   )
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    request.context_id,
                    request.group_id,
                    full_name,
                    request.birth_date,
                    request.gender,
                    (request.allergies or "").strip() or None,
                    (request.medical_notes or "").strip() or None,
                    user_id,
                ),
            )
            child_id = cur.fetchone()["id"]
            legacy_user_id = -8_000_000_000_000_000_000 + child_id
            cur.execute(
                """UPDATE kindergarten_children
                   SET external_reference=%s,updated_at=NOW()
                   WHERE id=%s""",
                (f"legacy_user:{legacy_user_id}", child_id),
            )
            cur.execute(
                """INSERT INTO users(user_id,full_name,role)
                   VALUES(%s,%s,'oquvchi')
                   ON CONFLICT(user_id) DO NOTHING""",
                (legacy_user_id, full_name),
            )
            if legacy_group_id is not None:
                cur.execute(
                    """INSERT INTO bogcha_guruh_bolalari(guruh_id,bola_user_id)
                       VALUES(%s,%s)
                       ON CONFLICT(guruh_id,bola_user_id) DO NOTHING""",
                    (legacy_group_id, legacy_user_id),
                )
                cur.execute(
                    """INSERT INTO context_memberships(
                           context_id,group_id,user_id,member_role,status,source
                       )
                       VALUES(%s,%s,%s,'student','active','kindergarten_v2')
                       ON CONFLICT(
                           context_id,(COALESCE(group_id,0)),user_id,member_role
                       ) DO UPDATE SET
                           status='active',ended_at=NULL,updated_at=NOW()""",
                    (
                        request.context_id,
                        request.group_id,
                        legacy_user_id,
                    ),
                )
            if request.guardian_name and request.guardian_name.strip():
                cur.execute(
                    """INSERT INTO kindergarten_guardians(
                           child_id,full_name,relationship,phone,is_primary
                       )
                       VALUES(%s,%s,%s,%s,TRUE)""",
                    (
                        child_id,
                        request.guardian_name.strip(),
                        (request.guardian_relationship or "").strip() or None,
                        (request.guardian_phone or "").strip() or None,
                    ),
                )
        return {"status": "created", "child_id": child_id}

    @router.post("/attendance")
    def mark_attendance(request: AttendanceMark) -> dict[str, Any]:
        user_id = current_user(request.token)
        arrival_at = aware_utc(request.arrival_at, "Kelish vaqti")
        departure_at = aware_utc(request.departure_at, "Ketish vaqti")
        if (
            arrival_at
            and departure_at
            and departure_at < arrival_at
        ):
            raise HTTPException(status_code=400, detail="Ketish vaqti noto'g'ri")
        with database() as (_, cur):
            ensure_schema(cur)
            require_group(
                cur,
                request.context_id,
                user_id,
                ATTENDANCE_EDIT_ROLES,
                request.group_id,
            )
            cur.execute(
                """SELECT 1 FROM kindergarten_children
                   WHERE id=%s AND context_id=%s
                     AND group_id=%s""",
                (request.child_id, request.context_id, request.group_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Bola topilmadi")
            cur.execute(
                """INSERT INTO kindergarten_attendance(
                       context_id,group_id,child_id,attendance_date,status,
                       arrival_at,departure_at,note,marked_by_user_id
                   )
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(child_id,attendance_date) DO UPDATE SET
                     group_id=EXCLUDED.group_id,
                     status=EXCLUDED.status,
                     arrival_at=EXCLUDED.arrival_at,
                     departure_at=EXCLUDED.departure_at,
                     note=EXCLUDED.note,
                     marked_by_user_id=EXCLUDED.marked_by_user_id,
                     updated_at=NOW()
                   RETURNING id,updated_at""",
                (
                    request.context_id,
                    request.group_id,
                    request.child_id,
                    request.attendance_date,
                    request.status,
                    arrival_at,
                    departure_at,
                    (request.note or "").strip() or None,
                    user_id,
                ),
            )
            row = cur.fetchone()
        return {"status": "saved", "attendance": row}

    @router.get("/attendance")
    def attendance(
        context_id: int,
        group_id: int,
        attendance_date: date,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_group(
                cur, context_id, user_id, ATTENDANCE_EDIT_ROLES, group_id
            )
            cur.execute(
                """SELECT ch.id AS child_id,ch.full_name,
                          a.id AS attendance_id,a.status,a.arrival_at,
                          a.departure_at,a.note
                   FROM kindergarten_children ch
                   LEFT JOIN kindergarten_attendance a
                     ON a.child_id=ch.id
                    AND a.context_id=ch.context_id
                    AND a.group_id=ch.group_id
                    AND a.attendance_date=%s
                   WHERE ch.context_id=%s AND ch.group_id=%s
                     AND ch.enrollment_status='active'
                   ORDER BY ch.full_name""",
                (attendance_date, context_id, group_id),
            )
            rows = cur.fetchall()
        return {"date": attendance_date, "items": rows}

    @router.get("/daily-reports")
    def daily_reports(
        context_id: int,
        group_id: int,
        report_date: date,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_group(
                cur, context_id, user_id, DAILY_REPORT_ROLES, group_id
            )
            cur.execute(
                """SELECT ch.id AS child_id,ch.full_name,
                          r.id AS report_id,r.meals,r.sleep,r.mood,
                          r.activities,r.educator_note,r.updated_at
                   FROM kindergarten_children ch
                   LEFT JOIN kindergarten_daily_reports r
                     ON r.child_id=ch.id
                    AND r.context_id=ch.context_id
                    AND r.group_id=ch.group_id
                    AND r.report_date=%s
                   WHERE ch.context_id=%s AND ch.group_id=%s
                     AND ch.enrollment_status='active'
                   ORDER BY ch.full_name""",
                (report_date, context_id, group_id),
            )
            rows = cur.fetchall()
        return {"date": report_date, "items": rows}

    @router.post("/daily-reports")
    def save_daily_report(request: DailyReportUpsert) -> dict[str, Any]:
        user_id = current_user(request.token)
        if len(json.dumps(request.meals, ensure_ascii=False)) > 10_000:
            raise HTTPException(status_code=413, detail="Ovqat hisoboti juda katta")
        if len(json.dumps(request.sleep, ensure_ascii=False)) > 10_000:
            raise HTTPException(status_code=413, detail="Uyqu hisoboti juda katta")
        with database() as (_, cur):
            ensure_schema(cur)
            require_group(
                cur,
                request.context_id,
                user_id,
                DAILY_REPORT_ROLES,
                request.group_id,
            )
            cur.execute(
                """SELECT 1 FROM kindergarten_children
                   WHERE id=%s AND context_id=%s AND group_id=%s
                     AND enrollment_status='active'""",
                (request.child_id, request.context_id, request.group_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Bola yoki guruh topilmadi")
            cur.execute(
                """INSERT INTO kindergarten_daily_reports(
                       context_id,group_id,child_id,report_date,meals,sleep,
                       mood,activities,educator_note,created_by_user_id
                   )
                   VALUES(%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s)
                   ON CONFLICT(child_id,report_date) DO UPDATE SET
                     group_id=EXCLUDED.group_id,
                     meals=EXCLUDED.meals,
                     sleep=EXCLUDED.sleep,
                     mood=EXCLUDED.mood,
                     activities=EXCLUDED.activities,
                     educator_note=EXCLUDED.educator_note,
                     created_by_user_id=EXCLUDED.created_by_user_id,
                     updated_at=NOW()
                   RETURNING id,updated_at""",
                (
                    request.context_id,
                    request.group_id,
                    request.child_id,
                    request.report_date,
                    json.dumps(request.meals, ensure_ascii=False),
                    json.dumps(request.sleep, ensure_ascii=False),
                    (request.mood or "").strip()[:80] or None,
                    (request.activities or "").strip()[:2000] or None,
                    (request.educator_note or "").strip()[:2000] or None,
                    user_id,
                ),
            )
            row = cur.fetchone()
        return {"status": "saved", "report": row}

    @router.get("/calendar")
    def calendar(
        context_id: int,
        date_from: date,
        date_to: date,
        user_id: int = Depends(authenticated_user),
        group_id: int | None = None,
        after_start: datetime | None = None,
        after_id: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=500),
    ) -> dict[str, Any]:
        if date_to < date_from or (date_to - date_from).days > 366:
            raise HTTPException(
                status_code=400,
                detail="Kalendar oralig'i 0–366 kun bo'lishi kerak",
            )
        if (after_start is None and after_id) or (
            after_start is not None and after_id == 0
        ):
            raise HTTPException(
                status_code=400,
                detail="Kalendar cursor va ID birga yuborilishi kerak.",
            )
        cursor_start = aware_utc(after_start, "Kalendar cursor vaqti")
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            roles, group_scope = allowed_group_scope(
                cur, context_id, user_id, STAFF_ROLES
            )
            if (
                group_id is not None
                and group_scope is not None
                and group_id not in group_scope
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Siz faqat biriktirilgan guruh kalendarini ko'ra olasiz.",
                )
            can_view_drafts = bool(
                roles.intersection(MANAGER_ROLES | {"system_admin"})
            )
            cur.execute(
                """SELECT e.id,e.group_id,cg.name AS group_name,e.event_type,
                          e.title,e.description,e.starts_at,e.ends_at,e.status
                   FROM kindergarten_calendar_events e
                   LEFT JOIN course_groups cg ON cg.id=e.group_id
                   WHERE e.context_id=%s
                     AND e.starts_at < (%s::date + INTERVAL '1 day')
                     AND e.ends_at >= %s::date
                     AND (%s IS NULL OR e.group_id=%s)
                     AND (%s OR e.group_id IS NULL OR e.group_id=ANY(%s))
                     AND (
                       e.status='published'
                       OR (%s AND e.status='draft')
                       OR (e.created_by_user_id=%s AND e.status='draft')
                     )
                     AND (
                       %s
                       OR e.starts_at>%s
                       OR (e.starts_at=%s AND e.id>%s)
                     )
                   ORDER BY e.starts_at,e.id LIMIT %s""",
                (
                    context_id,
                    date_to,
                    date_from,
                    group_id,
                    group_id,
                    group_scope is None,
                    list(group_scope or []),
                    can_view_drafts,
                    user_id,
                    cursor_start is None,
                    cursor_start,
                    cursor_start,
                    after_id,
                    limit + 1,
                ),
            )
            rows = cur.fetchall()
        has_more = len(rows) > limit
        items = rows[:limit]
        next_cursor = None
        if has_more and items:
            next_cursor = {
                "starts_at": items[-1]["starts_at"],
                "id": items[-1]["id"],
            }
        return {
            "items": items,
            "has_more": has_more,
            "next_cursor": next_cursor,
        }

    @router.post("/calendar")
    def create_calendar_event(request: CalendarEventCreate) -> dict[str, Any]:
        user_id = current_user(request.token)
        if not request.confirmation:
            raise HTTPException(
                status_code=400,
                detail="Kalendar voqeasini chiqarishdan oldin tasdiqlang",
            )
        title = request.title.strip()
        starts_at = aware_utc(request.starts_at, "Boshlanish vaqti")
        ends_at = aware_utc(request.ends_at, "Tugash vaqti")
        if len(title) < 2:
            raise HTTPException(status_code=400, detail="Voqea nomini kiriting")
        if ends_at <= starts_at:
            raise HTTPException(status_code=400, detail="Vaqt oralig'i noto'g'ri")
        with database() as (_, cur):
            ensure_schema(cur)
            allowed = MANAGER_ROLES | {"methodist", "educator"}
            if request.group_id is not None:
                require_group(
                    cur,
                    request.context_id,
                    user_id,
                    allowed,
                    request.group_id,
                )
                cur.execute(
                    "SELECT 1 FROM course_groups WHERE id=%s AND context_id=%s AND active=TRUE",
                    (request.group_id, request.context_id),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=400, detail="Guruh topilmadi")
            else:
                require_roles(cur, request.context_id, user_id, allowed)
            cur.execute(
                """INSERT INTO kindergarten_calendar_events(
                       context_id,group_id,event_type,title,description,
                       starts_at,ends_at,status,created_by_user_id
                   )
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id,created_at""",
                (
                    request.context_id,
                    request.group_id,
                    request.event_type,
                    title,
                    (request.description or "").strip() or None,
                    starts_at,
                    ends_at,
                    request.status,
                    user_id,
                ),
            )
            row = cur.fetchone()
        return {"status": "created", "event": row}

    @router.put("/settings")
    def update_settings(request: SettingsUpdate) -> dict[str, Any]:
        user_id = current_user(request.token)
        work_start = parse_time(request.work_start, "Boshlanish vaqti")
        work_end = parse_time(request.work_end, "Tugash vaqti")
        if work_start and work_end and work_end <= work_start:
            raise HTTPException(status_code=400, detail="Ish vaqti noto'g'ri")
        if request.work_days is not None and (
            not request.work_days
            or any(day < 1 or day > 7 for day in request.work_days)
        ):
            raise HTTPException(status_code=400, detail="Ish kunlari noto'g'ri")
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, MANAGER_ROLES)
            cur.execute(
                """SELECT ownership_type FROM kindergarten_profiles
                   WHERE context_id=%s FOR UPDATE""",
                (request.context_id,),
            )
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="Bog'cha topilmadi")
            if (
                profile["ownership_type"] == "public"
                and request.payment_enabled is True
                and not is_system_admin(cur, user_id)
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Davlat bog'chasida to'lovni faqat tizim administratori tasdiqlaydi",
                )
            cur.execute(
                """UPDATE kindergarten_profiles SET
                     work_start=COALESCE(%s,work_start),
                     work_end=COALESCE(%s,work_end),
                     work_days=COALESCE(%s,work_days),
                     capacity=COALESCE(%s,capacity),
                     language=COALESCE(%s,language),
                     payment_enabled=COALESCE(%s,payment_enabled),
                     monthly_fee=CASE
                       WHEN %s IS NOT NULL THEN %s ELSE monthly_fee END,
                     updated_at=NOW()
                   WHERE context_id=%s
                   RETURNING *""",
                (
                    work_start,
                    work_end,
                    sorted(set(request.work_days)) if request.work_days else None,
                    request.capacity,
                    (request.language or "").strip() or None,
                    request.payment_enabled,
                    request.monthly_fee,
                    request.monthly_fee,
                    request.context_id,
                ),
            )
            updated = cur.fetchone()
        return {"profile": updated}

    @router.get("/billing/plans")
    def billing_plans(
        context_id: int,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, PAYMENT_ROLES)
            cur.execute(
                """SELECT id,name,amount,billing_day,active,created_at
                   FROM kindergarten_billing_plans
                   WHERE context_id=%s AND active=TRUE
                   ORDER BY id""",
                (context_id,),
            )
            rows = cur.fetchall()
        return {"items": rows}

    @router.post("/billing/plans")
    def create_billing_plan(request: BillingPlanCreate) -> dict[str, Any]:
        user_id = current_user(request.token)
        name = request.name.strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="To'lov rejasi nomini kiriting")
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, PAYMENT_ROLES)
            cur.execute(
                """SELECT ownership_type,payment_enabled
                   FROM kindergarten_profiles WHERE context_id=%s""",
                (request.context_id,),
            )
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="Bog'cha topilmadi")
            if profile["ownership_type"] != "private":
                raise HTTPException(
                    status_code=403,
                    detail="Davlat bog'chasi uchun to'lov rejasi bu bo'limda yaratilmaydi",
                )
            cur.execute(
                """INSERT INTO kindergarten_billing_plans(
                       context_id,name,amount,billing_day,created_by_user_id
                   )
                   VALUES(%s,%s,%s,%s,%s)
                   RETURNING id,name,amount,billing_day,active""",
                (
                    request.context_id,
                    name,
                    request.amount,
                    request.billing_day,
                    user_id,
                ),
            )
            row = cur.fetchone()
            if not profile["payment_enabled"]:
                cur.execute(
                    """UPDATE kindergarten_profiles
                       SET payment_enabled=TRUE,monthly_fee=COALESCE(monthly_fee,%s),
                           updated_at=NOW()
                       WHERE context_id=%s""",
                    (request.amount, request.context_id),
                )
        return {"plan": row}

    @router.get("/billing/invoices")
    def billing_invoices(
        context_id: int,
        user_id: int = Depends(authenticated_user),
        status: str | None = None,
        after_id: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
    ) -> dict[str, Any]:
        allowed_statuses = {"unpaid", "partial", "paid", "waived", "cancelled"}
        if status is not None and status not in allowed_statuses:
            raise HTTPException(status_code=400, detail="Noto'g'ri hisob holati")
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, PAYMENT_ROLES)
            cur.execute(
                """SELECT i.id,i.child_id,ch.full_name,p.name AS plan_name,
                          i.period_month,i.amount_due,i.amount_paid,
                          (i.amount_due-i.amount_paid) AS remaining,
                          i.due_date,i.status,i.updated_at
                   FROM kindergarten_invoices i
                   JOIN kindergarten_children ch
                     ON ch.id=i.child_id AND ch.context_id=i.context_id
                   LEFT JOIN kindergarten_billing_plans p
                     ON p.id=i.plan_id AND p.context_id=i.context_id
                   WHERE i.context_id=%s AND i.id>%s
                     AND (%s IS NULL OR i.status=%s)
                   ORDER BY i.id LIMIT %s""",
                (context_id, after_id, status, status, limit + 1),
            )
            rows = cur.fetchall()
            cur.execute(
                """SELECT
                     COALESCE(SUM(amount_paid),0) AS paid_total,
                     COALESCE(SUM(
                       CASE WHEN status IN ('unpaid','partial')
                         THEN amount_due-amount_paid ELSE 0 END
                     ),0) AS outstanding_total,
                     COUNT(*) AS invoice_count
                   FROM kindergarten_invoices
                   WHERE context_id=%s
                     AND (%s IS NULL OR status=%s)""",
                (context_id, status, status),
            )
            summary = cur.fetchone()
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
            "has_more": len(rows) > limit,
            "summary": summary,
        }

    @router.post("/billing/invoices/generate")
    def generate_invoices(request: InvoiceGenerate) -> dict[str, Any]:
        user_id = current_user(request.token)
        if not request.confirmation:
            raise HTTPException(
                status_code=400,
                detail="Hisoblarni yaratishdan oldin foydalanuvchi tasdig'i shart",
            )
        period_month = request.period_month.replace(day=1)
        if request.due_date < period_month or (
            request.due_date - period_month
        ).days > 62:
            raise HTTPException(
                status_code=400,
                detail="To'lov muddati tanlangan oyga yaqin bo'lishi kerak",
            )
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, PAYMENT_ROLES)
            cur.execute(
                """SELECT id,amount FROM kindergarten_billing_plans
                   WHERE id=%s AND context_id=%s AND active=TRUE""",
                (request.plan_id, request.context_id),
            )
            plan = cur.fetchone()
            if not plan:
                raise HTTPException(status_code=404, detail="To'lov rejasi topilmadi")
            if request.group_id is not None:
                cur.execute(
                    """SELECT 1 FROM course_groups
                       WHERE id=%s AND context_id=%s
                         AND group_type='kindergarten_group' AND active=TRUE""",
                    (request.group_id, request.context_id),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Guruh topilmadi")
            cur.execute(
                """INSERT INTO kindergarten_invoices(
                       context_id,child_id,plan_id,period_month,amount_due,due_date
                   )
                   SELECT %s,ch.id,%s,%s,%s,%s
                   FROM kindergarten_children ch
                   WHERE ch.context_id=%s AND ch.enrollment_status='active'
                     AND (%s IS NULL OR ch.group_id=%s)
                   ON CONFLICT(child_id,plan_id,period_month) DO NOTHING""",
                (
                    request.context_id,
                    request.plan_id,
                    period_month,
                    plan["amount"],
                    request.due_date,
                    request.context_id,
                    request.group_id,
                    request.group_id,
                ),
            )
            created_count = cur.rowcount
        return {
            "status": "generated",
            "created_count": created_count,
            "period_month": period_month,
        }

    @router.post("/billing/invoices/{invoice_id}/payments")
    def record_payment(invoice_id: int, request: PaymentCreate) -> dict[str, Any]:
        user_id = current_user(request.token)
        if not request.confirmation:
            raise HTTPException(
                status_code=400,
                detail="To'lovni yozishdan oldin foydalanuvchi tasdig'i shart",
            )
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM kindergarten_invoices
                   WHERE id=%s FOR UPDATE""",
                (invoice_id,),
            )
            invoice = cur.fetchone()
            if not invoice:
                raise HTTPException(status_code=404, detail="Hisob topilmadi")
            require_roles(
                cur, invoice["context_id"], user_id, PAYMENT_ROLES
            )
            cur.execute(
                """SELECT id,invoice_id,amount,payment_method,reference,paid_at
                   FROM kindergarten_payments
                   WHERE context_id=%s AND idempotency_key=%s""",
                (invoice["context_id"], request.idempotency_key),
            )
            existing_payment = cur.fetchone()
            if existing_payment:
                if existing_payment["invoice_id"] != invoice_id:
                    raise HTTPException(
                        status_code=409,
                        detail="Bu takrorlanmas amal kaliti boshqa hisobda ishlatilgan",
                    )
                return {
                    "payment": existing_payment,
                    "invoice": {
                        "amount_due": invoice["amount_due"],
                        "amount_paid": invoice["amount_paid"],
                        "status": invoice["status"],
                    },
                    "idempotent_replay": True,
                }
            remaining = invoice["amount_due"] - invoice["amount_paid"]
            if invoice["status"] in {"paid", "waived", "cancelled"}:
                raise HTTPException(status_code=409, detail="Bu hisob yopilgan")
            if request.amount > remaining:
                raise HTTPException(
                    status_code=400,
                    detail=f"To'lov qoldiqdan oshmasin: {remaining:f}",
                )
            cur.execute(
                """INSERT INTO kindergarten_payments(
                       context_id,invoice_id,amount,payment_method,reference,
                       note,recorded_by_user_id,idempotency_key
                   )
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id,paid_at""",
                (
                    invoice["context_id"],
                    invoice_id,
                    request.amount,
                    request.payment_method,
                    (request.reference or "").strip()[:200] or None,
                    (request.note or "").strip()[:500] or None,
                    user_id,
                    request.idempotency_key,
                ),
            )
            payment = cur.fetchone()
            cur.execute(
                """UPDATE kindergarten_invoices
                   SET amount_paid=amount_paid+%s,
                       status=CASE
                         WHEN amount_paid+%s>=amount_due THEN 'paid'
                         ELSE 'partial'
                       END,
                       updated_at=NOW()
                   WHERE id=%s
                   RETURNING amount_due,amount_paid,status""",
                (request.amount, request.amount, invoice_id),
            )
            updated = cur.fetchone()
        return {"payment": payment, "invoice": updated}

    @router.post("/admin/verification")
    def verify_public_kindergarten(
        context_id: int,
        approve: bool,
        admin_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            if not is_system_admin(cur, admin_id):
                raise HTTPException(status_code=403, detail="Faqat tizim administratori")
            cur.execute(
                """SELECT p.*,c.name
                   FROM kindergarten_profiles p
                   JOIN learning_contexts c ON c.id=p.context_id
                   WHERE p.context_id=%s FOR UPDATE""",
                (context_id,),
            )
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="Bog'cha topilmadi")
            if profile["ownership_type"] != "public":
                raise HTTPException(status_code=400, detail="Bu davlat bog'chasi emas")
            if (
                approve
                and profile["onboarding_status"] == "active"
                and profile["verification_status"] == "verified"
            ):
                raise HTTPException(status_code=409, detail="Bog'cha allaqachon tasdiqlangan")
            if (
                not approve
                and profile["onboarding_status"] == "suspended"
                and profile["verification_status"] == "rejected"
            ):
                raise HTTPException(status_code=409, detail="Bog'cha allaqachon rad etilgan")
            status = "active" if approve else "suspended"
            verification = "verified" if approve else "rejected"
            cur.execute(
                """UPDATE kindergarten_profiles
                   SET onboarding_status=%s,verification_status=%s,updated_at=NOW()
                   WHERE context_id=%s""",
                (status, verification, context_id),
            )
            cur.execute(
                "UPDATE learning_contexts SET active=%s,updated_at=NOW() WHERE id=%s",
                (approve, context_id),
            )
            if approve:
                cur.execute(
                    """UPDATE kindergarten_role_assignments
                       SET status='active',approved_by_user_id=%s,
                           starts_at=NOW(),ends_at=NULL,
                           permissions=permissions-'verification_hold',
                           updated_at=NOW()
                       WHERE context_id=%s
                         AND (
                           status='pending'
                           OR permissions ? 'verification_hold'
                         )""",
                    (admin_id, context_id),
                )
                cur.execute(
                    """UPDATE context_memberships
                       SET status='active',approved_by_user_id=%s,
                           ended_at=NULL,
                           metadata=metadata-'verification_hold',
                           updated_at=NOW()
                       WHERE context_id=%s
                         AND (
                           status='pending'
                           OR metadata ? 'verification_hold'
                         )""",
                    (admin_id, context_id),
                )
                cur.execute(
                    """SELECT user_id,role_key FROM kindergarten_role_assignments
                       WHERE context_id=%s AND status='active'""",
                    (context_id,),
                )
                for role in cur.fetchall():
                    legacy_membership(
                        cur,
                        user_id=role["user_id"],
                        legacy_bogcha_id=profile["legacy_bogcha_id"],
                        role_key=role["role_key"],
                    )
            else:
                cur.execute(
                    "SELECT to_regclass('public.xodim_kod') AS table_name"
                )
                if cur.fetchone()["table_name"]:
                    cur.execute(
                        """UPDATE xodim_kod code
                           SET ishlatildi=TRUE
                           FROM users legacy_user
                           WHERE code.user_id=legacy_user.user_id
                             AND legacy_user.bogcha_id=%s
                             AND code.ishlatildi=FALSE""",
                        (profile["legacy_bogcha_id"],),
                    )
                cur.execute(
                    """UPDATE kindergarten_role_assignments
                       SET status=CASE
                         WHEN status='pending' THEN 'rejected'
                         ELSE 'suspended'
                       END,
                       permissions=permissions || jsonb_build_object(
                         'verification_hold',status
                       ),
                       approved_by_user_id=%s,ends_at=NOW(),updated_at=NOW()
                       WHERE context_id=%s AND status IN ('pending','active')""",
                    (admin_id, context_id),
                )
                cur.execute(
                    """UPDATE context_memberships
                       SET status=CASE
                         WHEN status='pending' THEN 'rejected'
                         ELSE 'suspended'
                       END,
                       metadata=metadata || jsonb_build_object(
                         'verification_hold',status
                       ),
                       approved_by_user_id=%s,ended_at=NOW(),updated_at=NOW()
                       WHERE context_id=%s AND status IN ('pending','active')""",
                    (admin_id, context_id),
                )
                cur.execute(
                    """DELETE FROM foydalanuvchi_muassasalari
                       WHERE muassasa_turi='bogcha' AND muassasa_id=%s""",
                    (profile["legacy_bogcha_id"],),
                )
                cur.execute(
                    """UPDATE users
                       SET bogcha_id=NULL,
                           lavozim=CASE
                             WHEN maktab_id IS NULL
                              AND markaz_id IS NULL
                              AND universitet_id IS NULL
                             THEN NULL
                             ELSE lavozim
                           END
                       WHERE bogcha_id=%s""",
                    (profile["legacy_bogcha_id"],),
                )
        return {"status": status, "verification_status": verification}

    @router.post("/assistant/sessions")
    def start_assistant(request: AssistantStart) -> dict[str, Any]:
        user_id = current_user(request.token)
        allowed_workflows = {
            "kindergarten_onboarding": "relationship",
            "kindergarten_director_tour": "overview",
            "kindergarten_educator_tour": "groups",
            "kindergarten_accountant_tour": "payments",
            "kindergarten_nurse_tour": "children",
            "kindergarten_staff_tour": "overview",
        }
        if request.workflow_key not in allowed_workflows:
            raise HTTPException(status_code=400, detail="Noma'lum yordamchi yo'nalishi")
        with database() as (_, cur):
            ensure_schema(cur)
            if request.context_id is not None:
                allowed_group_scope(
                    cur, request.context_id, user_id, STAFF_ROLES
                )
            if request.draft_id is not None:
                fetch_draft(cur, request.draft_id, user_id)
            first_step = allowed_workflows[request.workflow_key]
            cur.execute(
                """SELECT id,current_step,state,created_at
                   FROM assistant_sessions
                   WHERE user_id=%s
                     AND context_id IS NOT DISTINCT FROM %s
                     AND draft_id IS NOT DISTINCT FROM %s
                     AND workflow_key=%s
                     AND state IN ('active','paused','minimized')
                   ORDER BY updated_at DESC LIMIT 1 FOR UPDATE""",
                (
                    user_id,
                    request.context_id,
                    request.draft_id,
                    request.workflow_key,
                ),
            )
            session = cur.fetchone()
            if session:
                cur.execute(
                    """UPDATE assistant_sessions
                       SET state='active',avatar_enabled=%s,speech_enabled=%s,
                           avatar_variant=%s,updated_at=NOW()
                       WHERE id=%s
                       RETURNING id,current_step,state,created_at""",
                    (
                        request.avatar_enabled,
                        request.speech_enabled,
                        request.avatar_variant,
                        session["id"],
                    ),
                )
                session = cur.fetchone()
                return {
                    "session": session,
                    "resumed": True,
                    "capabilities": {
                        "can_explain": True,
                        "can_focus_fields": True,
                        "can_prepare_drafts": False,
                        "can_confirm_privileged_actions": False,
                        "can_bypass_permissions": False,
                    },
                }
            cur.execute(
                """INSERT INTO assistant_sessions(
                       user_id,context_id,draft_id,workflow_key,current_step,
                       avatar_enabled,speech_enabled,avatar_variant
                   )
                   VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id,current_step,state,created_at""",
                (
                    user_id,
                    request.context_id,
                    request.draft_id,
                    request.workflow_key,
                    first_step,
                    request.avatar_enabled,
                    request.speech_enabled,
                    request.avatar_variant,
                ),
            )
            session = cur.fetchone()
        return {
            "session": session,
            "capabilities": {
                "can_explain": True,
                "can_focus_fields": True,
                "can_prepare_drafts": False,
                "can_confirm_privileged_actions": False,
                "can_bypass_permissions": False,
            },
        }

    @router.post("/assistant/sessions/{session_id}/actions")
    def assistant_action(
        session_id: int, request: AssistantAction
    ) -> dict[str, Any]:
        user_id = current_user(request.token)
        action_id = request.action_id.strip().upper()
        if action_id not in ASSISTANT_ACTIONS:
            raise HTTPException(status_code=400, detail="Noma'lum avatar amali")
        encoded = json.dumps(request.payload, ensure_ascii=False)
        if len(encoded.encode("utf-8")) > 20_000:
            raise HTTPException(status_code=413, detail="Avatar amali juda katta")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM assistant_sessions
                   WHERE id=%s AND user_id=%s FOR UPDATE""",
                (session_id, user_id),
            )
            session = cur.fetchone()
            if not session:
                raise HTTPException(status_code=404, detail="Avatar sessiyasi topilmadi")
            if session["state"] in {"completed", "cancelled"}:
                raise HTTPException(status_code=409, detail="Avatar sessiyasi yakunlangan")

            result: dict[str, Any] = {}
            state = session["state"]
            current_step = session["current_step"]

            if action_id == "PAUSE":
                state = "paused"
            elif action_id == "RESUME":
                state = "active"
            elif action_id == "MINIMIZE":
                state = "minimized"
            elif action_id == "RESTORE":
                state = "active"
            elif action_id == "COMPLETE_TOUR":
                state = "completed"
            elif action_id == "NEXT_STEP":
                current_step = str(
                    request.payload.get("next_step") or current_step
                )[:80]
            elif action_id == "PREVIOUS_STEP":
                current_step = str(
                    request.payload.get("previous_step") or current_step
                )[:80]
            elif action_id == "UNDO":
                cur.execute(
                    """SELECT id,action_id,input_payload
                       FROM assistant_action_events
                       WHERE session_id=%s AND reversible=TRUE
                         AND action_status='completed'
                       ORDER BY sequence_no DESC LIMIT 1 FOR UPDATE""",
                    (session_id,),
                )
                previous = cur.fetchone()
                if previous:
                    cur.execute(
                        """UPDATE assistant_action_events
                           SET action_status='undone',undone_at=NOW()
                           WHERE id=%s""",
                        (previous["id"],),
                    )
                    result["undone_action"] = previous["action_id"]
                    result["restore"] = previous["input_payload"]
                else:
                    result["undone_action"] = None

            cur.execute(
                """SELECT COALESCE(MAX(sequence_no),0)+1 AS next_sequence
                   FROM assistant_action_events WHERE session_id=%s""",
                (session_id,),
            )
            sequence = cur.fetchone()["next_sequence"]
            cur.execute(
                """INSERT INTO assistant_action_events(
                       session_id,sequence_no,action_id,ui_anchor,
                       action_status,reversible,input_payload,result_payload
                   )
                   VALUES(%s,%s,%s,%s,'completed',%s,%s::jsonb,%s::jsonb)
                   RETURNING id,sequence_no,created_at""",
                (
                    session_id,
                    sequence,
                    action_id,
                    (request.ui_anchor or "")[:120] or None,
                    action_id in REVERSIBLE_ACTIONS,
                    encoded,
                    json.dumps(result, ensure_ascii=False),
                ),
            )
            event = cur.fetchone()
            cur.execute(
                """UPDATE assistant_sessions
                   SET state=%s,current_step=%s,
                       state_payload=state_payload || %s::jsonb,
                       updated_at=NOW(),
                       completed_at=CASE WHEN %s='completed' THEN NOW()
                                         ELSE completed_at END
                   WHERE id=%s""",
                (
                    state,
                    current_step,
                    json.dumps(
                        {
                            "last_action": action_id,
                            "last_anchor": request.ui_anchor,
                        },
                        ensure_ascii=False,
                    ),
                    state,
                    session_id,
                ),
            )
        return {
            "event": event,
            "state": state,
            "current_step": current_step,
            "result": result,
            "requires_confirmation": action_id in {
                "SET_DRAFT_VALUE",
            },
        }

    return router

"""Modular, tenant-safe school API.

The guided assistant may explain, focus fields and prepare drafts, but it can
never publish a timetable/calendar, assign a privileged role, take payment or
activate a school without an explicit authenticated human confirmation.
"""

from __future__ import annotations

import json
import hashlib
import re
import secrets
import string
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Callable, Iterator, Literal

import psycopg2
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from platform_core.database import DatabaseBusyError, db_session
from modules.school_scheduler import (
    Assignment as SchedulerAssignment,
    CalendarDayLabel,
    CalendarLesson,
    Cancellation,
    ClassHourPolicy,
    ClassHourRule,
    LessonDemand,
    MakeupRequest,
    Room as SchedulerRoom,
    SchoolClass,
    Shift,
    Slot,
    SubjectPreference,
    Teacher,
    TimetableRequest,
    audit_assignments,
    generate_timetable as run_school_scheduler,
    plan_calendar_makeups,
)


MANAGER_ROLES = {
    "owner", "founder", "director", "academic_deputy",
    "spiritual_deputy", "administrator",
}
ACADEMIC_ROLES = MANAGER_ROLES | {"methodist"}
TEACHING_ROLES = ACADEMIC_ROLES | {"teacher", "homeroom_teacher"}
ATTENDANCE_ROLES = TEACHING_ROLES | {"psychologist", "social_pedagogue", "nurse"}
FINANCE_ROLES = MANAGER_ROLES | {"accountant"}
VIEW_ROLES = {
    *MANAGER_ROLES, "methodist", "teacher", "homeroom_teacher",
    "psychologist", "social_pedagogue", "nurse", "accountant", "librarian",
    "it_admin", "laboratory_assistant", "security", "student", "parent",
}
STAFF_ROLES = VIEW_ROLES - {"student", "parent"}
PRIVILEGED_ASSIGNABLE = {
    "owner", "founder", "director", "academic_deputy",
    "spiritual_deputy", "administrator",
}
ROLE_LABELS = {
    "owner": "Mulkdor", "founder": "Ta'sischi", "director": "Direktor",
    "academic_deputy": "O'quv ishlari bo'yicha direktor o'rinbosari",
    "spiritual_deputy": "Ma'naviy-ma'rifiy ishlar bo'yicha direktor o'rinbosari",
    "administrator": "Administrator", "methodist": "Metodist",
    "teacher": "Fan o'qituvchisi", "homeroom_teacher": "Sinf rahbari",
    "psychologist": "Psixolog", "social_pedagogue": "Ijtimoiy pedagog",
    "nurse": "Hamshira", "accountant": "Hisobchi", "librarian": "Kutubxonachi",
    "it_admin": "IT administrator", "laboratory_assistant": "Laborant",
    "security": "Qo'riqlash xodimi", "student": "O'quvchi", "parent": "Ota-ona",
}
ASSISTANT_ACTIONS = {
    "SHOW_MENU", "FOCUS_FIELD", "SET_DRAFT_VALUE", "NEXT_STEP",
    "PREVIOUS_STEP", "PAUSE", "RESUME", "UNDO", "MINIMIZE",
    "RESTORE", "SPEAK", "COMPLETE_TOUR",
}
REVERSIBLE_ACTIONS = {
    "FOCUS_FIELD", "NEXT_STEP", "PREVIOUS_STEP",
    "MINIMIZE", "RESTORE",
}

# Fixed-date, nationwide non-working holidays from the Uzbekistan Labour Code.
# Lunar Eid dates intentionally are not guessed offline; administrators can add
# their officially announced dates to the calendar for each academic year.
UZ_FIXED_PUBLIC_HOLIDAYS_V1 = (
    (1, 1, "Yangi yil"),
    (3, 8, "Xotin-qizlar kuni"),
    (3, 21, "Navro‘z bayrami"),
    (5, 9, "Xotira va qadrlash kuni"),
    (9, 1, "Mustaqillik kuni"),
    (10, 1, "O‘qituvchi va murabbiylar kuni"),
    (12, 8, "Konstitutsiya kuni"),
)


class DraftStart(BaseModel):
    relationship: Literal["owner", "founder", "director", "administrator"]
    ownership_type: Literal["public", "private"]
    setup_mode: Literal["manual", "guided", "assistant"] = "guided"


class DraftPatch(BaseModel):
    step: str = Field(min_length=1, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
    expected_version: int = Field(ge=1)


class HumanConfirm(BaseModel):
    expected_version: int | None = Field(default=None, ge=1)
    confirmation: bool


class RoomDraft(BaseModel):
    room_number: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    room_type: Literal[
        "classroom", "laboratory", "computer", "library", "gym", "assembly",
        "canteen", "medical", "office", "workshop", "other",
    ] = "classroom"
    capacity: int | None = Field(default=None, ge=1, le=5000)
    position: Literal["left", "center", "right"] = "center"


class FloorDraft(BaseModel):
    floor_number: int = Field(ge=-3, le=30)
    name: str | None = Field(default=None, max_length=100)
    rooms: list[RoomDraft] = Field(default_factory=list, max_length=300)


class BuildingCreate(BaseModel):
    context_id: int
    name: str = Field(min_length=2, max_length=150)
    building_order: int = Field(ge=1, le=100)
    entrance_side: Literal["left", "center", "right"] = "center"
    floors: list[FloorDraft] = Field(default_factory=list, max_length=40)


class SectionCreate(BaseModel):
    context_id: int
    grade_no: int = Field(ge=1, le=11)
    section_name: str = Field(min_length=1, max_length=10)
    shift_no: Literal[1, 2] = 1
    homeroom_teacher_user_id: int | None = None
    default_room_id: int | None = None
    capacity: int | None = Field(default=None, ge=1, le=100)


class SubjectCreate(BaseModel):
    context_id: int
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=150)
    grade_from: int = Field(default=1, ge=1, le=11)
    grade_to: int = Field(default=11, ge=1, le=11)
    weekly_hours: Decimal | None = Field(default=None, ge=0, le=80)
    preferred_period_max: int | None = Field(default=None, ge=1, le=20)


class StaffAssign(BaseModel):
    context_id: int
    user_id: int
    role_key: str
    group_id: int | None = None
    subject_ids: list[int] = Field(default_factory=list, max_length=100)
    grade_from: int = Field(default=1, ge=1, le=11)
    grade_to: int = Field(default=11, ge=1, le=11)
    confirmation: bool = False


class StaffInviteCreate(BaseModel):
    context_id: int
    role_key: str
    group_id: int | None = None
    full_name: str | None = Field(default=None, max_length=180)
    phone: str | None = Field(default=None, max_length=80)
    method_day: int | None = Field(default=None, ge=1, le=7)
    available_shift: Literal["1", "2", "both"] = "both"
    max_daily_lessons: int = Field(default=6, ge=1, le=7)
    confirmation: bool = False


class JoinSchoolRequest(BaseModel):
    context_id: int | None = None
    invite_code: str | None = Field(default=None, min_length=6, max_length=40)
    requested_role: str = "teacher"


class JoinRequestDecision(BaseModel):
    approve: bool
    confirmation: bool


class VerificationDecision(BaseModel):
    approve: bool
    confirmation: bool
    note: str | None = Field(default=None, max_length=1000)


class AvailabilityRow(BaseModel):
    weekday: int = Field(ge=1, le=7)
    shift_no: Literal[1, 2]
    period_from: int = Field(ge=1, le=20)
    period_to: int = Field(ge=1, le=20)
    availability: Literal["available", "unavailable", "preferred"]
    note: str | None = Field(default=None, max_length=300)


class TeacherAvailabilityPut(BaseModel):
    context_id: int
    method_day: int | None = Field(default=None, ge=1, le=7)
    max_daily_periods: int | None = Field(default=None, ge=1, le=7)
    max_weekly_periods: int | None = Field(default=None, ge=1, le=72)
    preferred_shift: Literal[1, 2] | None = None
    avoid_first_period: bool | None = None
    rows: list[AvailabilityRow] = Field(default_factory=list, max_length=200)


class WorkloadCreate(BaseModel):
    context_id: int
    section_id: int
    subject_id: int
    teacher_user_id: int
    weekly_hours: int = Field(ge=1, le=30)
    preferred_room_id: int | None = None
    preferred_band: Literal["early", "late", "any"] = "any"
    max_per_day: int = Field(default=1, ge=1, le=4)


class CalendarCreate(BaseModel):
    context_id: int
    group_id: int | None = None
    event_type: Literal[
        "academic", "holiday", "lesson", "exam", "meeting", "club",
        "substitution", "other",
    ]
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    starts_at: datetime
    ends_at: datetime
    status: Literal["draft", "published"] = "draft"
    confirmation: bool = False


class MakeupCancellation(BaseModel):
    slot_id: int
    lesson_date: date
    reason: str = Field(min_length=2, max_length=500)


class CalendarMakeupRequest(BaseModel):
    context_id: int
    cancellations: list[MakeupCancellation] = Field(min_length=1, max_length=100)
    candidate_dates: list[date] = Field(min_length=1, max_length=120)
    allow_topic_compression: bool = False
    max_extra_lessons_per_class_per_day: int = Field(default=1, ge=1, le=4)
    confirmation: bool = False


class TimetableGenerate(BaseModel):
    context_id: int
    academic_year: str = Field(min_length=4, max_length=20)
    term_no: int | None = Field(default=None, ge=1, le=4)
    section_ids: list[int] = Field(default_factory=list, max_length=500)
    max_periods_per_shift: int = Field(default=6, ge=1, le=12)
    first_shift_start: str = "08:00"
    second_shift_start: str = "13:10"
    short_break_minutes: int = Field(default=5, ge=0, le=60)
    long_break_after: int = Field(default=3, ge=1, le=12)
    long_break_minutes: int = Field(default=10, ge=0, le=90)


class TimetableConfirm(BaseModel):
    expected_version: int = Field(ge=1)
    confirmation: bool


class SubstitutionCreate(BaseModel):
    context_id: int
    slot_id: int
    lesson_date: date
    new_teacher_user_id: int
    reason: str = Field(min_length=2, max_length=500)
    idempotency_key: str = Field(min_length=16, max_length=100)
    confirmation: bool


class TimetableExceptionRevoke(BaseModel):
    context_id: int
    reason: str = Field(min_length=2, max_length=500)
    idempotency_key: str = Field(min_length=16, max_length=100)
    confirmation: bool


class AttendanceMark(BaseModel):
    context_id: int
    section_id: int
    student_user_id: int
    attendance_date: date
    period_no: int | None = Field(default=None, ge=1, le=20)
    status: Literal["present", "absent", "late", "excused", "sick"]
    note: str | None = Field(default=None, max_length=500)


class StudentAssign(BaseModel):
    context_id: int
    section_id: int
    user_id: int
    confirmation: bool = False


class ParentStudentLink(BaseModel):
    context_id: int
    parent_user_id: int
    student_user_id: int
    confirmation: bool = False


class GradeCreate(BaseModel):
    context_id: int
    section_id: int
    subject_id: int
    student_user_id: int
    grade_type: Literal["daily", "homework", "quiz", "exam", "quarter", "annual"]
    score: Decimal = Field(ge=0)
    max_score: Decimal = Field(gt=0)
    graded_at: datetime | None = None
    note: str | None = Field(default=None, max_length=1000)
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=100)


class BillingPlanCreate(BaseModel):
    context_id: int
    name: str = Field(min_length=2, max_length=150)
    amount: Decimal = Field(gt=0)
    billing_day: int = Field(default=5, ge=1, le=28)
    confirmation: bool = False


class InvoiceCreate(BaseModel):
    context_id: int
    plan_id: int
    student_user_id: int
    period_month: date
    due_date: date
    confirmation: bool = False


class PaymentCreate(BaseModel):
    context_id: int
    invoice_id: int
    amount: Decimal = Field(gt=0)
    payment_method: Literal["cash", "card", "bank_transfer", "online", "other"] = "cash"
    idempotency_key: str = Field(min_length=16, max_length=100)
    reference: str | None = Field(default=None, max_length=300)
    confirmation: bool = False


class AssistantStart(BaseModel):
    workflow_key: str = Field(default="school_onboarding", max_length=100)
    context_id: int | None = None
    draft_id: int | None = None
    avatar_enabled: bool = True
    speech_enabled: bool = True
    avatar_variant: Literal["female", "male", "neutral"] = "female"


class AssistantAction(BaseModel):
    action_id: str = Field(min_length=1, max_length=60)
    ui_anchor: str | None = Field(default=None, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


def create_school_router(jwt_check: Callable[[str], int]) -> APIRouter:
    router = APIRouter(prefix="/api/maktab-v2", tags=["Maktab v2"])

    def authenticated_user(authorization: str | None = Header(default=None)) -> int:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Bearer sessiya tokeni topilmadi")
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
                detail="Maktab bazasi o'rnatilmagan: avval 001, keyin 005 SQL ni bajaring.",
            ) from exc

    def ensure_schema(cur: Any) -> None:
        cur.execute(
            "SELECT 1 FROM app_schema_migrations WHERE version='005_school_platform'"
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=503,
                detail="database/005_school_platform.sql hali bajarilmagan.",
            )

    def ensure_exception_schema(cur: Any) -> None:
        cur.execute(
            """SELECT 1 FROM app_schema_migrations
               WHERE version='006_school_timetable_exceptions'"""
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Sanaga xos jadval uchun "
                    "database/006_school_timetable_exceptions.sql ni bajaring."
                ),
            )

    def system_admin(cur: Any, user_id: int) -> bool:
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
        return cur.fetchone() is not None

    def audit(
        cur: Any, context_id: int | None, actor: int, action: str,
        target_type: str | None = None, target_id: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        cur.execute(
            """INSERT INTO school_audit_log(
                 context_id,actor_user_id,action_key,target_type,target_id,payload
               ) VALUES(%s,%s,%s,%s,%s,%s::jsonb)""",
            (context_id, actor, action, target_type, target_id,
             json.dumps(payload or {}, ensure_ascii=False, default=str)),
        )

    def active_roles(cur: Any, context_id: int, user_id: int) -> set[str]:
        cur.execute(
            """SELECT c.active,p.onboarding_status,p.verification_status
               FROM learning_contexts c JOIN school_profiles p ON p.context_id=c.id
               WHERE c.id=%s AND c.context_type='school'""",
            (context_id,),
        )
        state = cur.fetchone()
        if (
            not state or not state["active"] or state["onboarding_status"] != "active"
            or state["verification_status"] == "rejected"
        ):
            raise HTTPException(status_code=403, detail="Bu maktab hozir faol emas.")
        cur.execute(
            """SELECT role_key FROM school_role_assignments
               WHERE context_id=%s AND user_id=%s AND status='active'
                 AND starts_at<=NOW() AND (ends_at IS NULL OR ends_at>NOW())""",
            (context_id, user_id),
        )
        return {row["role_key"] for row in cur.fetchall()}

    def require_roles(
        cur: Any, context_id: int, user_id: int, allowed: set[str],
        *, group_id: int | None = None,
    ) -> set[str]:
        if system_admin(cur, user_id):
            return {"system_admin"}
        roles = active_roles(cur, context_id, user_id)
        cur.execute(
            """SELECT role_key,group_id FROM school_role_assignments
               WHERE context_id=%s AND user_id=%s AND status='active'
                 AND role_key=ANY(%s) AND starts_at<=NOW()
                 AND (ends_at IS NULL OR ends_at>NOW())""",
            (context_id, user_id, list(allowed)),
        )
        assignments = cur.fetchall()
        if not assignments:
            raise HTTPException(
                status_code=403,
                detail="Bu amal uchun shu maktabdagi vakolatingiz yetarli emas.",
            )
        if group_id is not None and not any(
            row["group_id"] is None or int(row["group_id"]) == group_id
            for row in assignments
        ):
            raise HTTPException(
                status_code=403, detail="Siz faqat biriktirilgan sinf bilan ishlaysiz."
            )
        return roles

    def teacher_can_access_section(
        cur: Any, context_id: int, user_id: int, section_id: int
    ) -> bool:
        if system_admin(cur, user_id):
            return True
        roles = active_roles(cur, context_id, user_id)
        if roles & MANAGER_ROLES:
            return True
        cur.execute(
            """SELECT group_id FROM school_sections
               WHERE id=%s AND context_id=%s AND active=TRUE""",
            (section_id, context_id),
        )
        section = cur.fetchone()
        if not section:
            return False
        cur.execute(
            """SELECT 1
               WHERE EXISTS(
                 SELECT 1 FROM school_workloads
                 WHERE context_id=%s AND section_id=%s
                   AND teacher_user_id=%s AND active=TRUE
               ) OR EXISTS(
                 SELECT 1 FROM school_role_assignments
                 WHERE context_id=%s AND group_id=%s AND user_id=%s
                   AND role_key='homeroom_teacher' AND status='active'
               )""",
            (
                context_id, section_id, user_id,
                context_id, section["group_id"], user_id,
            ),
        )
        return cur.fetchone() is not None

    def require_human(confirmation: bool, message: str) -> None:
        if confirmation is not True:
            raise HTTPException(status_code=409, detail=message)

    def valid_time(text: str, field: str) -> time:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", text.strip()):
            raise HTTPException(status_code=422, detail=f"{field} HH:MM shaklida bo'lsin")
        return time.fromisoformat(text.strip())

    def bounded_int(
        value: Any, field: str, minimum: int, maximum: int,
        *, default: int | None = None,
    ) -> int:
        if value in (None, "") and default is not None:
            return default
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=422, detail=f"{field} butun son bo'lishi kerak"
            ) from exc
        if not minimum <= parsed <= maximum:
            raise HTTPException(
                status_code=422,
                detail=f"{field} {minimum}–{maximum} oralig'ida bo'lsin",
            )
        return parsed

    def academic_year_bounds(value: str) -> tuple[date, date]:
        match = re.fullmatch(r"\s*(\d{4})\s*[-/]\s*(\d{4})\s*", value)
        if not match or int(match.group(2)) != int(match.group(1)) + 1:
            raise HTTPException(
                status_code=422,
                detail="O'quv yili 2026-2027 ko'rinishida bo'lsin.",
            )
        first, second = int(match.group(1)), int(match.group(2))
        return date(first, 9, 1), date(second, 8, 31)

    def official_holidays_for_academic_year(
        academic_year: str,
    ) -> list[tuple[date, str]]:
        starts_on, ends_on = academic_year_bounds(academic_year)
        result = []
        for year in range(starts_on.year, ends_on.year + 1):
            for month, day, title in UZ_FIXED_PUBLIC_HOLIDAYS_V1:
                holiday_date = date(year, month, day)
                if starts_on <= holiday_date <= ends_on:
                    result.append((holiday_date, title))
        return sorted(result)

    def school_calendar_bounds(
        cur: Any, context_id: int
    ) -> tuple[date, date]:
        cur.execute(
            """SELECT academic_year,settings FROM school_profiles
               WHERE context_id=%s""",
            (context_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Maktab profili topilmadi")
        fallback_start, fallback_end = academic_year_bounds(
            str(row["academic_year"])
        )
        calendar_settings = dict(
            dict(row["settings"] or {}).get("calendar") or {}
        )
        try:
            starts_on = (
                date.fromisoformat(str(calendar_settings["starts_on"]))
                if calendar_settings.get("starts_on") else fallback_start
            )
            ends_on = (
                date.fromisoformat(str(calendar_settings["ends_on"]))
                if calendar_settings.get("ends_on") else fallback_end
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=409,
                detail="Maktab kalendarining starts_on/ends_on sanasi noto'g'ri.",
            ) from exc
        if ends_on < starts_on:
            raise HTTPException(
                status_code=409,
                detail="Maktab kalendarining tugash sanasi boshlanishdan oldin.",
            )
        return starts_on, ends_on

    def require_calendar_dates(
        cur: Any, context_id: int, values: list[date] | set[date]
    ) -> tuple[date, date]:
        starts_on, ends_on = school_calendar_bounds(cur, context_id)
        outside = sorted(
            value for value in set(values)
            if value < starts_on or value > ends_on
        )
        if outside:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": (
                        "Dars sanasi maktabning joriy akademik kalendari "
                        "chegarasidan tashqarida."
                    ),
                    "starts_on": starts_on.isoformat(),
                    "ends_on": ends_on.isoformat(),
                    "invalid_dates": [
                        value.isoformat() for value in outside[:20]
                    ],
                },
            )
        return starts_on, ends_on

    def lock_context_dates(
        cur: Any, context_id: int, values: list[date] | set[date]
    ) -> None:
        # Sorted transaction-scoped locks serialize every effective occurrence
        # mutation without holding a broad school/profile row lock.
        for lesson_date in sorted(set(values)):
            cur.execute(
                "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))",
                (f"school-effective:{context_id}:{lesson_date.isoformat()}",),
            )

    def teacher_slot_preferences(
        all_slots: set[Slot], rows: list[Any], user_id: int
    ) -> tuple[frozenset[Slot], frozenset[Slot]]:
        explicit_available: set[Slot] = set()
        unavailable: set[Slot] = set()
        preferred: set[Slot] = set()
        for row in rows:
            if int(row["user_id"]) != user_id:
                continue
            target = (
                unavailable
                if row["availability"] == "unavailable"
                else preferred
                if row["availability"] == "preferred"
                else explicit_available
            )
            for period in range(
                int(row["period_from"]), int(row["period_to"]) + 1
            ):
                slot = Slot(
                    str(row["weekday"]), str(row["shift_no"]), period
                )
                if slot in all_slots:
                    target.add(slot)
        allowed = (
            explicit_available.copy()
            if explicit_available
            else all_slots.copy()
        )
        allowed.difference_update(unavailable)
        preferred.intersection_update(allowed)
        return frozenset(allowed), frozenset(preferred)

    def aware(value: datetime, field: str) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise HTTPException(status_code=422, detail=f"{field} vaqt zonasi bilan yuborilsin")
        return value.astimezone(timezone.utc)

    def ensure_group(cur: Any, context_id: int, group_id: int) -> None:
        cur.execute(
            "SELECT 1 FROM course_groups WHERE id=%s AND context_id=%s AND active=TRUE",
            (group_id, context_id),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Sinf bu maktabda topilmadi")

    def upsert_school_role(
        cur: Any, *, context_id: int, user_id: int, role_key: str,
        status: str, approved_by: int | None, group_id: int | None = None,
    ) -> int:
        cur.execute(
            """INSERT INTO school_role_assignments(
                 context_id,group_id,user_id,role_key,status,approved_by_user_id,
                 permissions
               ) VALUES(%s,%s,%s,%s,%s,%s,'{"source":"school_v2"}')
               ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,role_key)
               DO UPDATE SET status=EXCLUDED.status,
                 approved_by_user_id=EXCLUDED.approved_by_user_id,
                 starts_at=NOW(),ends_at=NULL,updated_at=NOW()
               RETURNING id""",
            (context_id, group_id, user_id, role_key, status, approved_by),
        )
        assignment_id = int(cur.fetchone()["id"])
        generic = (
            "student" if role_key == "student"
            else "parent_observer" if role_key == "parent"
            else "director" if role_key == "director"
            else "manager" if role_key in MANAGER_ROLES
            else "teacher"
        )
        cur.execute(
            """INSERT INTO context_memberships(
                 context_id,group_id,user_id,member_role,status,source,
                 approved_by_user_id,metadata
               ) VALUES(%s,%s,%s,%s,%s,'school_v2',%s,%s::jsonb)
               ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,member_role)
               DO UPDATE SET status=EXCLUDED.status,
                 approved_by_user_id=EXCLUDED.approved_by_user_id,
                 ended_at=NULL,updated_at=NOW(),metadata=EXCLUDED.metadata""",
            (
                context_id, group_id, user_id, generic, status, approved_by,
                json.dumps({"school_role": role_key}, ensure_ascii=False),
            ),
        )
        return assignment_id

    def sync_homeroom_teacher(
        cur: Any, *, context_id: int, group_id: int, teacher_user_id: int
    ) -> None:
        cur.execute(
            """SELECT id FROM school_sections
               WHERE context_id=%s AND group_id=%s AND active=TRUE""",
            (context_id, group_id),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Sinf topilmadi")
        cur.execute(
            """UPDATE school_role_assignments
               SET status='ended',ends_at=NOW(),updated_at=NOW()
               WHERE context_id=%s AND group_id=%s
                 AND role_key='homeroom_teacher' AND status='active'
                 AND user_id<>%s""",
            (context_id, group_id, teacher_user_id),
        )
        cur.execute(
            """UPDATE context_memberships
               SET status='withdrawn',ended_at=NOW(),updated_at=NOW()
               WHERE context_id=%s AND group_id=%s AND status='active'
                 AND metadata->>'school_role'='homeroom_teacher'
                 AND user_id<>%s""",
            (context_id, group_id, teacher_user_id),
        )
        cur.execute(
            """UPDATE school_sections
               SET homeroom_teacher_user_id=%s,updated_at=NOW()
               WHERE context_id=%s AND group_id=%s""",
            (teacher_user_id, context_id, group_id),
        )
        cur.execute(
            """UPDATE course_groups
               SET teacher_user_id=%s,updated_at=NOW()
               WHERE context_id=%s AND id=%s""",
            (teacher_user_id, context_id, group_id),
        )

    def ensure_private_billing(cur: Any, context_id: int) -> None:
        cur.execute(
            """SELECT ownership_type,billing_enabled FROM school_profiles
               WHERE context_id=%s""",
            (context_id,),
        )
        profile = cur.fetchone()
        if not profile or profile["ownership_type"] != "private":
            raise HTTPException(status_code=403, detail="To'lov faqat xususiy maktab uchun.")
        if not profile["billing_enabled"]:
            raise HTTPException(status_code=409, detail="Maktabda to'lov moduli yoqilmagan.")

    @router.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ready",
            "module": "school",
            "version": "school-platform-v1",
            "schema": "005_school_platform+006_school_timetable_exceptions",
        }

    @router.get("/meta")
    def meta(_: int = Depends(authenticated_user)) -> dict[str, Any]:
        return {
            "roles": [{"key": key, "label": value} for key, value in ROLE_LABELS.items()],
            "ownership_types": ["public", "private"],
            "shift_counts": [1, 2],
            "assistant_limits": {
                "can_confirm_privileged_actions": False,
                "can_bypass_permissions": False,
            },
        }

    @router.get("/join/search")
    def join_search(
        q: str = Query(min_length=3, max_length=100),
        limit: int = Query(default=20, ge=1, le=50),
        _: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        literal = (
            q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT c.id context_id,c.name,c.region,c.district,
                          p.ownership_type,p.shift_count
                   FROM learning_contexts c JOIN school_profiles p ON p.context_id=c.id
                   WHERE c.active=TRUE AND p.onboarding_status='active'
                     AND p.verification_status<>'rejected'
                     AND c.name ILIKE %s ESCAPE '\\'
                   ORDER BY c.name,c.id LIMIT %s""",
                (f"%{literal}%", limit),
            )
            rows = cur.fetchall()
        return {"items": rows}

    @router.get("/users/search")
    def search_enrollment_users(
        context_id: int = Query(ge=1),
        q: str = Query(min_length=3, max_length=100),
        limit: int = Query(default=20, ge=1, le=50),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        literal = (
            q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, MANAGER_ROLES)
            cur.execute(
                """SELECT u.user_id,u.full_name,
                          EXISTS(
                            SELECT 1 FROM school_role_assignments r
                            WHERE r.context_id=%s AND r.user_id=u.user_id
                              AND r.status='active'
                          ) already_in_school
                   FROM users u
                   WHERE u.full_name ILIKE %s ESCAPE '\\'
                   ORDER BY u.full_name,u.user_id LIMIT %s""",
                (context_id, f"%{literal}%", limit),
            )
            rows = cur.fetchall()
        return {"items": rows}

    @router.post("/join/requests")
    def join_request(
        request: JoinSchoolRequest, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        if bool(request.context_id) == bool(request.invite_code):
            raise HTTPException(
                status_code=422,
                detail="Maktab ID yoki taklif kodidan aynan bittasini yuboring.",
            )
        with database() as (_, cur):
            ensure_schema(cur)
            if request.invite_code:
                normalized = re.sub(r"[^A-Z0-9]", "", request.invite_code.upper())
                digest = hashlib.sha256(normalized.encode()).hexdigest()
                cur.execute(
                    """SELECT * FROM school_invitations
                       WHERE code_hash=%s FOR UPDATE""",
                    (digest,),
                )
                invitation = cur.fetchone()
                if (
                    not invitation or invitation["status"] != "pending"
                    or invitation["expires_at"] <= datetime.now(timezone.utc)
                ):
                    raise HTTPException(status_code=404, detail="Taklif kodi yaroqsiz yoki eskirgan")
                assignment_id = upsert_school_role(
                    cur, context_id=int(invitation["context_id"]),
                    group_id=invitation["group_id"], user_id=user_id,
                    role_key=invitation["role_key"], status="active",
                    approved_by=int(invitation["created_by_user_id"]),
                )
                if (
                    invitation["role_key"] == "homeroom_teacher"
                    and invitation["group_id"] is not None
                ):
                    sync_homeroom_teacher(
                        cur, context_id=int(invitation["context_id"]),
                        group_id=int(invitation["group_id"]),
                        teacher_user_id=user_id,
                    )
                invite_meta = dict(invitation["metadata"] or {})
                if invitation["role_key"] in {"teacher", "homeroom_teacher"}:
                    allowed_shifts = invite_meta.get("allowed_shifts") or [1, 2]
                    cur.execute(
                        """INSERT INTO school_teacher_settings(
                             context_id,user_id,method_day,max_daily_periods,
                             preferences
                           ) VALUES(%s,%s,%s,%s,%s::jsonb)
                           ON CONFLICT(context_id,user_id) DO UPDATE SET
                             method_day=EXCLUDED.method_day,
                             max_daily_periods=EXCLUDED.max_daily_periods,
                             preferences=school_teacher_settings.preferences
                               ||EXCLUDED.preferences,
                             updated_at=NOW()""",
                        (
                            invitation["context_id"], user_id,
                            invite_meta.get("method_day"),
                            min(int(invite_meta.get("max_daily_lessons") or 6), 7),
                            json.dumps({"allowed_shifts": allowed_shifts}),
                        ),
                    )
                cur.execute(
                    """UPDATE school_invitations
                       SET status='accepted',accepted_by_user_id=%s,accepted_at=NOW()
                       WHERE id=%s""",
                    (user_id, invitation["id"]),
                )
                audit(
                    cur, invitation["context_id"], user_id, "invitation.accept",
                    "invitation", invitation["id"],
                )
                return {
                    "context_id": invitation["context_id"],
                    "assignment_id": assignment_id,
                    "status": "active",
                }
            role = request.requested_role.strip()
            if role not in STAFF_ROLES - PRIVILEGED_ASSIGNABLE:
                role = "teacher"
            cur.execute(
                """SELECT 1 FROM school_profiles
                   WHERE context_id=%s AND onboarding_status='active'
                     AND verification_status<>'rejected'""",
                (request.context_id,),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Faol maktab topilmadi")
            assignment_id = upsert_school_role(
                cur, context_id=int(request.context_id), user_id=user_id,
                role_key=role, status="pending", approved_by=None,
            )
        return {
            "context_id": request.context_id,
            "assignment_id": assignment_id,
            "status": "pending",
        }

    @router.get("/join/requests")
    def list_join_requests(
        context_id: int = Query(ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, MANAGER_ROLES)
            cur.execute(
                """SELECT r.id,r.user_id,u.full_name,r.role_key,r.group_id,
                          r.status,r.created_at
                   FROM school_role_assignments r
                   JOIN users u ON u.user_id=r.user_id
                   WHERE r.context_id=%s AND r.status='pending' AND r.id>%s
                   ORDER BY r.id LIMIT %s""",
                (context_id, after_id or 0, limit + 1),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
        }

    @router.post("/join/requests/{assignment_id}/decision")
    def decide_join_request(
        assignment_id: int, request: JoinRequestDecision,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "Qo'shilish so'rovi qarori uchun inson tasdig'i kerak.",
        )
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM school_role_assignments
                   WHERE id=%s FOR UPDATE""",
                (assignment_id,),
            )
            assignment = cur.fetchone()
            if not assignment or assignment["status"] != "pending":
                raise HTTPException(
                    status_code=404, detail="Faol qo'shilish so'rovi topilmadi"
                )
            require_roles(
                cur, assignment["context_id"], user_id, MANAGER_ROLES
            )
            if assignment["role_key"] in PRIVILEGED_ASSIGNABLE:
                raise HTTPException(
                    status_code=409,
                    detail="Rahbarlik roli oddiy qo'shilish so'rovi bilan berilmaydi",
                )
            new_status = "active" if request.approve else "rejected"
            cur.execute(
                """UPDATE school_role_assignments
                   SET status=%s,approved_by_user_id=%s,
                     starts_at=CASE WHEN %s='active' THEN NOW() ELSE starts_at END,
                     updated_at=NOW()
                   WHERE id=%s""",
                (new_status, user_id, new_status, assignment_id),
            )
            cur.execute(
                """UPDATE context_memberships
                   SET status=%s,approved_by_user_id=%s,updated_at=NOW()
                   WHERE context_id=%s AND user_id=%s
                     AND COALESCE(group_id,0)=COALESCE(%s,0)
                     AND metadata->>'school_role'=%s""",
                (
                    new_status, user_id, assignment["context_id"],
                    assignment["user_id"], assignment["group_id"],
                    assignment["role_key"],
                ),
            )
            audit(
                cur, assignment["context_id"], user_id, "join.decide",
                "role_assignment", assignment_id,
                {"approved": request.approve},
            )
        return {"assignment_id": assignment_id, "status": new_status}

    @router.post("/admin/contexts/{context_id}/verification")
    def verify_public_school(
        context_id: int, request: VerificationDecision,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Tekshiruv qarori uchun inson tasdig'i kerak.")
        with database() as (_, cur):
            ensure_schema(cur)
            if not system_admin(cur, user_id):
                raise HTTPException(status_code=403, detail="Faqat tizim administratori uchun")
            cur.execute(
                """UPDATE school_profiles SET
                     onboarding_status=%s,verification_status=%s,
                     settings=settings||%s::jsonb,updated_at=NOW()
                   WHERE context_id=%s AND ownership_type='public'
                   RETURNING context_id,onboarding_status,verification_status""",
                (
                    "active" if request.approve else "suspended",
                    "verified" if request.approve else "rejected",
                    json.dumps(
                        {"verification_note": request.note, "verified_by": user_id},
                        ensure_ascii=False,
                    ),
                    context_id,
                ),
            )
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="Davlat maktabi topilmadi")
            audit(cur, context_id, user_id, "school.verify", "school", context_id,
                  {"approved": request.approve})
        return {"profile": profile}

    @router.post("/onboarding/drafts")
    def start_draft(
        request: DraftStart, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        if request.ownership_type == "public" and request.relationship in {"owner", "founder"}:
            raise HTTPException(status_code=422, detail="Davlat maktabida mulkdor roli bo'lmaydi.")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """INSERT INTO school_setup_drafts(
                     creator_user_id,relationship,ownership_type,setup_mode
                   ) VALUES(%s,%s,%s,%s)
                   RETURNING id,current_step,status,version,expires_at""",
                (user_id, request.relationship, request.ownership_type, request.setup_mode),
            )
            draft = cur.fetchone()
        return {"draft": draft, "next_step": "basics"}

    @router.patch("/onboarding/drafts/{draft_id}")
    def patch_draft(
        draft_id: int, request: DraftPatch,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        encoded = json.dumps(request.payload, ensure_ascii=False)
        if len(encoded.encode()) > 100_000:
            raise HTTPException(status_code=413, detail="Sozlash ma'lumoti juda katta")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """UPDATE school_setup_drafts
                   SET payload=payload||%s::jsonb,current_step=%s,version=version+1,
                       updated_at=NOW()
                   WHERE id=%s AND creator_user_id=%s AND status='draft'
                     AND expires_at>NOW() AND version=%s
                   RETURNING id,current_step,payload,version,updated_at""",
                (encoded, request.step, draft_id, user_id, request.expected_version),
            )
            draft = cur.fetchone()
            if not draft:
                raise HTTPException(
                    status_code=409,
                    detail="Qoralama o'zgargan, topilmagan yoki muddati tugagan.",
                )
        return {"draft": draft}

    @router.get("/onboarding/drafts/{draft_id}/preview")
    def preview_draft(
        draft_id: int, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT id,relationship,ownership_type,setup_mode,current_step,
                          payload,version,expires_at
                   FROM school_setup_drafts
                   WHERE id=%s AND creator_user_id=%s AND status='draft'""",
                (draft_id, user_id),
            )
            draft = cur.fetchone()
            if not draft:
                raise HTTPException(status_code=404, detail="Qoralama topilmadi")
        payload = dict(draft["payload"] or {})
        basic = {
            **dict(payload.get("identity") or {}),
            **dict(payload.get("basic") or {}),
        }
        errors = []
        name = str(basic.get("name") or "").strip()
        if len(name) < 3:
            errors.append("Maktab nomini kamida 3 belgi bilan kiriting")
        shifts = payload.get("shift_count", basic.get("shift_count", 1))
        if shifts not in (1, 2):
            errors.append("Smena soni 1 yoki 2 bo'lishi kerak")
        return {
            "draft": draft,
            "summary": {
                "name": name,
                "ownership_type": draft["ownership_type"],
                "shift_count": shifts,
                "region": basic.get("region"),
                "district": basic.get("district"),
                "academic_year": basic.get("academic_year", "2026-2027"),
            },
            "errors": errors,
            "ready": not errors,
        }

    @router.post("/onboarding/drafts/{draft_id}/commit")
    def commit_draft(
        draft_id: int, request: HumanConfirm,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "Maktabni ochishdan oldin yakuniy inson tasdig'i kerak.",
        )
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM school_setup_drafts
                   WHERE id=%s AND creator_user_id=%s FOR UPDATE""",
                (draft_id, user_id),
            )
            draft = cur.fetchone()
            if draft and draft["status"] == "confirmed" and draft["confirmed_context_id"]:
                cur.execute(
                    """SELECT onboarding_status,verification_status
                       FROM school_profiles WHERE context_id=%s""",
                    (draft["confirmed_context_id"],),
                )
                existing = cur.fetchone()
                if existing:
                    return {
                        "context_id": draft["confirmed_context_id"],
                        "status": existing["onboarding_status"],
                        "verification_status": existing["verification_status"],
                        "idempotent_replay": True,
                    }
            if not draft or draft["status"] != "draft" or draft["expires_at"] <= datetime.now(timezone.utc):
                raise HTTPException(status_code=409, detail="Qoralama faol emas")
            if request.expected_version is not None and draft["version"] != request.expected_version:
                raise HTTPException(status_code=409, detail="Qoralama versiyasi o'zgargan")
            payload = dict(draft["payload"] or {})
            basic = {
                **dict(payload.get("identity") or {}),
                **dict(payload.get("basic") or {}),
            }
            name = str(basic.get("name") or "").strip()
            if len(name) < 3 or len(name) > 180:
                raise HTTPException(status_code=422, detail="Maktab nomi 3–180 belgi bo'lsin")
            shift_count = bounded_int(
                payload.get("shift_count", basic.get("shift_count")),
                "Smena soni", 1, 2, default=1,
            )
            bell_schedule = dict(payload.get("bell_schedule") or {})
            lesson_minutes = bounded_int(
                bell_schedule.get("lesson_minutes", basic.get("lesson_minutes")),
                "Dars davomiyligi", 20, 120, default=45,
            )
            raw_shift_rows = bell_schedule.get("shifts") or []
            if not isinstance(raw_shift_rows, list):
                raise HTTPException(
                    status_code=422,
                    detail="Smena qo'ng'iroq jadvali ro'yxat bo'lishi kerak",
                )

            legacy_max_lessons = bounded_int(
                bell_schedule.get("max_periods_per_shift"),
                "Smenadagi darslar soni", 1, 12, default=6,
            )

            def onboarding_shift(
                index: int, fallback: str
            ) -> tuple[str, int]:
                if index >= len(raw_shift_rows):
                    value = fallback
                    max_lessons = legacy_max_lessons
                else:
                    row = raw_shift_rows[index]
                    if not isinstance(row, dict):
                        raise HTTPException(
                            status_code=422,
                            detail=f"{index + 1}-smena ma'lumoti noto'g'ri",
                        )
                    value = str(row.get("starts_at") or fallback).strip()
                    max_lessons = bounded_int(
                        row.get("max_lessons"),
                        f"{index + 1}-smenadagi darslar soni",
                        1, 12, default=legacy_max_lessons,
                    )
                valid_time(value, f"{index + 1}-smena boshlanishi")
                return value, max_lessons

            first_shift_start, first_shift_max = onboarding_shift(0, "08:00")
            second_shift_start, second_shift_max = onboarding_shift(1, "13:10")
            short_break_minutes = bounded_int(
                bell_schedule.get("short_break_minutes"),
                "Qisqa tanaffus", 0, 60, default=5,
            )
            long_break_after = bounded_int(
                bell_schedule.get("long_break_after"),
                "Uzun tanaffusdan oldingi dars", 1, 12, default=3,
            )
            long_break_minutes = bounded_int(
                bell_schedule.get("long_break_minutes"),
                "Uzun tanaffus", 0, 90, default=10,
            )
            if shift_count == 2:
                first = valid_time(first_shift_start, "1-smena boshlanishi")
                second = valid_time(second_shift_start, "2-smena boshlanishi")
                first_minute = first.hour * 60 + first.minute
                second_minute = second.hour * 60 + second.minute
                first_end = (
                    first_minute
                    + (first_shift_max - 1)
                    * (lesson_minutes + short_break_minutes)
                    + (
                        max(0, long_break_minutes - short_break_minutes)
                        if first_shift_max > long_break_after else 0
                    )
                    + lesson_minutes
                )
                if first_end > second_minute:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"1-smenaning {first_shift_max} ta darsi "
                            "2-smena boshlanishiga "
                            "ustma-ust tushmoqda. Smena vaqtlarini tuzating."
                        ),
                    )
            billing_enabled = bool(basic.get("billing_enabled", False))
            if draft["ownership_type"] == "public" and billing_enabled:
                raise HTTPException(status_code=422, detail="Davlat maktabida xususiy to'lov yoqilmaydi")
            buildings = list(payload.get("buildings") or [])
            if len(buildings) > 30:
                raise HTTPException(status_code=422, detail="Bir sozlashda 30 tadan ko'p bino bo'lmaydi")
            normalized_buildings = []
            total_rooms = 0
            for item in buildings:
                if not isinstance(item, dict):
                    raise HTTPException(status_code=422, detail="Bino ma'lumoti noto'g'ri")
                building_name = str(item.get("name") or "").strip()
                if len(building_name) < 2:
                    raise HTTPException(status_code=422, detail="Bino nomini to'liq kiriting")
                floor_count = bounded_int(
                    item.get("floors"), f"{building_name} qavatlari", 1, 30
                )
                rooms_per_floor = bounded_int(
                    item.get("rooms_per_floor"),
                    f"{building_name} qavatidagi xonalar", 1, 100,
                )
                total_rooms += floor_count * rooms_per_floor
                normalized_buildings.append(
                    (item, building_name, floor_count, rooms_per_floor)
                )
            if total_rooms > 1000:
                raise HTTPException(
                    status_code=422,
                    detail="Bir sozlashda jami xonalar soni 1000 dan oshmasin",
                )
            classes = dict(payload.get("classes") or {})
            grades = sorted({
                int(value) for value in classes.get("grades", [])
                if str(value).isdigit() and 1 <= int(value) <= 11
            })
            raw_letters = classes.get("section_letters") or []
            if isinstance(raw_letters, str):
                raw_letters = raw_letters.split(",")
            letters: list[str] = []
            for value in raw_letters:
                letter = str(value).strip().upper()[:4]
                if letter and letter not in letters:
                    letters.append(letter)
            if len(grades) * len(letters) > 500:
                raise HTTPException(
                    status_code=422,
                    detail="Bir sozlashda sinflar soni 500 dan oshmaydi",
                )
            default_shift = bounded_int(
                classes.get("default_shift"), "Standart smena", 1, shift_count,
                default=1,
            )
            capacity = bounded_int(
                classes.get("capacity"), "Sinf sig'imi", 1, 100, default=30
            )
            academic_year = str(
                basic.get("academic_year") or "2026-2027"
            )[:20]
            academic_year_bounds(academic_year)
            cur.execute(
                """INSERT INTO learning_contexts(
                     context_type,name,owner_user_id,region,district,active,metadata
                   ) VALUES('school',%s,%s,%s,%s,TRUE,%s::jsonb) RETURNING id""",
                (
                    name, user_id, str(basic.get("region") or "").strip() or None,
                    str(basic.get("district") or "").strip() or None,
                    json.dumps({"address": basic.get("address"), "source": "school_v2"},
                               ensure_ascii=False),
                ),
            )
            context_id = int(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO school_profiles(
                     context_id,ownership_type,onboarding_status,verification_status,
                     shift_count,academic_year,lesson_minutes,work_days,billing_enabled,settings
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                (
                    context_id, draft["ownership_type"],
                    (
                        "pending_verification"
                        if draft["ownership_type"] == "public" else "active"
                    ),
                    "pending" if draft["ownership_type"] == "public" else "unverified",
                    shift_count, academic_year,
                    lesson_minutes, basic.get("work_days") or [1, 2, 3, 4, 5, 6],
                    billing_enabled,
                    json.dumps({
                        "first_shift_start": (
                            first_shift_start
                        ),
                        "second_shift_start": (
                            second_shift_start
                        ),
                        "short_break_minutes": short_break_minutes,
                        "long_break_after": long_break_after,
                        "long_break_minutes": long_break_minutes,
                        "max_periods_per_shift": max(
                            first_shift_max,
                            second_shift_max if shift_count == 2 else 0,
                        ),
                        "max_periods_by_shift": {
                            "1": first_shift_max,
                            **(
                                {"2": second_shift_max}
                                if shift_count == 2 else {}
                            ),
                        },
                        "calendar": payload.get("calendar") or {},
                        "staff_plan": payload.get("staff_plan") or {},
                        "workload_preferences": payload.get("workload") or {},
                        "school_type": basic.get("school_type", "public_general"),
                    }),
                ),
            )
            calendar_settings = dict(payload.get("calendar") or {})
            include_official_holidays = bool(
                calendar_settings.get("use_uzbekistan_holidays")
                or calendar_settings.get("include_official_holidays")
                or calendar_settings.get("official_uzbekistan_holidays")
            )
            if include_official_holidays:
                tashkent_tz = timezone(timedelta(hours=5))
                for holiday_date, holiday_title in (
                    official_holidays_for_academic_year(academic_year)
                ):
                    starts_at = datetime.combine(
                        holiday_date, time.min, tzinfo=tashkent_tz
                    )
                    ends_at = starts_at + timedelta(days=1)
                    cur.execute(
                        """INSERT INTO school_calendar_events(
                             context_id,event_type,title,description,starts_at,
                             ends_at,status,created_by_user_id,metadata
                           ) VALUES(
                             %s,'holiday',%s,%s,%s,%s,'published',%s,%s::jsonb
                           )""",
                        (
                            context_id, holiday_title,
                            (
                                "UZ_FIXED_PUBLIC_HOLIDAYS_V1. Hayit sanalari "
                                "rasmiy e'londan keyin administrator tomonidan "
                                "qo'shiladi."
                            ),
                            starts_at, ends_at, user_id,
                            json.dumps(
                                {
                                    "builtin": "UZ_FIXED_PUBLIC_HOLIDAYS_V1",
                                    "holiday_date": holiday_date.isoformat(),
                                },
                                ensure_ascii=False,
                            ),
                        ),
                    )
            created_room_ids: list[int] = []
            for building_index, normalized in enumerate(
                normalized_buildings, start=1
            ):
                item, building_name, floor_count, rooms_per_floor = normalized
                cur.execute(
                    """INSERT INTO school_buildings(
                         context_id,name,building_order,metadata
                       ) VALUES(%s,%s,%s,%s::jsonb) RETURNING id""",
                    (
                        context_id, building_name, building_index,
                        json.dumps(
                            {
                                "entrance_side": (
                                    item.get("entrance_side")
                                    if item.get("entrance_side")
                                    in {"left", "center", "right"}
                                    else "center"
                                )
                            }
                        ),
                    ),
                )
                building_id = cur.fetchone()["id"]
                for floor_number in range(1, floor_count + 1):
                    cur.execute(
                        """INSERT INTO school_floors(
                             context_id,building_id,floor_number,name
                           ) VALUES(%s,%s,%s,%s) RETURNING id""",
                        (
                            context_id, building_id, floor_number,
                            f"{floor_number}-qavat",
                        ),
                    )
                    floor_id = cur.fetchone()["id"]
                    for room_index in range(1, rooms_per_floor + 1):
                        room_number = (
                            f"{item.get('room_prefix') or ''}"
                            f"{floor_number}{room_index:02d}"
                        )
                        cur.execute(
                            """INSERT INTO school_rooms(
                                 context_id,floor_id,room_number,name,position
                               ) VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                            (
                                context_id, floor_id, room_number,
                                f"{room_number}-xona",
                                item.get("entrance_side")
                                if item.get("entrance_side") in {"left", "center", "right"}
                                else "center",
                            ),
                        )
                        created_room_ids.append(int(cur.fetchone()["id"]))

            grade_shifts = dict(classes.get("grade_shifts") or {})
            room_cursor = 0
            for grade_no in grades:
                section_shift = bounded_int(
                    grade_shifts.get(str(grade_no)),
                    f"{grade_no}-sinf smenasi", 1, shift_count,
                    default=default_shift,
                )
                for letter in letters:
                    room_id = (
                        created_room_ids[room_cursor % len(created_room_ids)]
                        if created_room_ids else None
                    )
                    room_cursor += 1
                    class_name = f"{grade_no}-{letter}"
                    cur.execute(
                        """INSERT INTO course_groups(
                             context_id,group_type,delivery_mode,name,grade,metadata
                           ) VALUES(%s,'school_section','offline',%s,%s,%s::jsonb)
                           RETURNING id""",
                        (
                            context_id, class_name, str(grade_no),
                            json.dumps({"shift_no": section_shift}),
                        ),
                    )
                    group_id = cur.fetchone()["id"]
                    cur.execute(
                        """INSERT INTO school_sections(
                             context_id,group_id,grade_no,section_name,shift_no,
                             default_room_id,capacity
                           ) VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            context_id, group_id, grade_no, letter, section_shift,
                            room_id, max(1, min(capacity, 100)),
                        ),
                    )
            workload = dict(payload.get("workload") or {})
            subject_names = workload.get("subjects") or []
            if workload.get("use_standard_subjects") and isinstance(subject_names, list):
                for index, subject_name in enumerate(subject_names[:100], start=1):
                    name_value = str(subject_name).strip()
                    if not name_value:
                        continue
                    code = re.sub(r"[^a-z0-9]+", "_", name_value.lower()).strip("_")
                    if not code:
                        code = f"subject_{index}"
                    cur.execute(
                        """INSERT INTO school_subjects(context_id,code,name)
                           VALUES(%s,%s,%s)
                           ON CONFLICT(context_id,code) DO NOTHING""",
                        (context_id, code[:40], name_value[:150]),
                    )
            role = draft["relationship"]
            cur.execute(
                """INSERT INTO school_role_assignments(
                     context_id,user_id,role_key,status,approved_by_user_id,permissions
                   ) VALUES(%s,%s,%s,'active',%s,'{"source":"school_v2"}')""",
                (context_id, user_id, role, user_id),
            )
            cur.execute(
                """INSERT INTO context_memberships(
                     context_id,user_id,member_role,status,source,approved_by_user_id,metadata
                   ) VALUES(%s,%s,%s,'active','school_v2',%s,%s::jsonb)
                   ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,member_role)
                   DO UPDATE SET status='active',ended_at=NULL,updated_at=NOW()""",
                (
                    context_id, user_id,
                    "director" if role == "director" else "manager", user_id,
                    json.dumps({"school_role": role}, ensure_ascii=False),
                ),
            )
            cur.execute(
                """UPDATE school_setup_drafts
                   SET status='confirmed',confirmed_context_id=%s,updated_at=NOW()
                   WHERE id=%s""",
                (context_id, draft_id),
            )
            audit(cur, context_id, user_id, "school.confirm", "school", context_id)
        return {
            "context_id": context_id,
            "status": (
                "pending_verification"
                if draft["ownership_type"] == "public" else "active"
            ),
            "verification_status": (
                "pending" if draft["ownership_type"] == "public" else "unverified"
            ),
        }

    @router.get("/workspaces")
    def workspaces(
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=30, ge=1, le=100),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            if system_admin(cur, user_id):
                cur.execute(
                    """SELECT c.id context_id,c.name,c.region,c.district,p.ownership_type,
                              p.shift_count,p.onboarding_status,p.verification_status,
                              p.onboarding_status status,
                              COALESCE(p.settings->>'school_type','public_general') school_type,
                              ARRAY['system_admin']::TEXT[] roles
                       FROM learning_contexts c JOIN school_profiles p ON p.context_id=c.id
                       WHERE c.id>%s ORDER BY c.id LIMIT %s""",
                    (after_id or 0, limit + 1),
                )
            else:
                cur.execute(
                    """SELECT c.id context_id,c.name,c.region,c.district,p.ownership_type,
                              p.shift_count,p.onboarding_status,p.verification_status,
                              p.onboarding_status status,
                              COALESCE(p.settings->>'school_type','public_general') school_type,
                              array_agg(DISTINCT r.role_key) roles
                       FROM school_role_assignments r
                       JOIN learning_contexts c ON c.id=r.context_id
                       JOIN school_profiles p ON p.context_id=c.id
                       WHERE r.user_id=%s AND r.status='active' AND c.active=TRUE
                         AND c.id>%s
                       GROUP BY c.id,c.name,c.region,c.district,p.ownership_type,
                                p.shift_count,p.onboarding_status,p.verification_status,
                                p.settings
                       ORDER BY c.id LIMIT %s""",
                    (user_id, after_id or 0, limit + 1),
                )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": (
                rows[limit - 1]["context_id"] if len(rows) > limit else None
            ),
        }

    @router.get("/dashboard")
    def dashboard(
        context_id: int = Query(ge=1),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            roles = require_roles(cur, context_id, user_id, VIEW_ROLES)
            cur.execute(
                """SELECT c.id context_id,c.name,c.region,c.district,p.ownership_type,
                          p.shift_count,p.academic_year,p.lesson_minutes,
                          p.work_days,
                          p.verification_status,p.onboarding_status,p.billing_enabled,
                          COALESCE(p.settings->>'school_type','public_general') school_type,
                          p.settings
                   FROM learning_contexts c JOIN school_profiles p ON p.context_id=c.id
                   WHERE c.id=%s""",
                (context_id,),
            )
            school = cur.fetchone()
            school = dict(school)
            settings = dict(school.pop("settings") or {})
            max_by_shift = dict(
                settings.get("max_periods_by_shift") or {}
            )
            fallback_max = settings.get("max_periods_per_shift", 6)
            school["bell_schedule"] = {
                "lesson_minutes": school["lesson_minutes"],
                "first_shift_start": settings.get("first_shift_start", "08:00"),
                "second_shift_start": settings.get("second_shift_start", "13:10"),
                "short_break_minutes": settings.get("short_break_minutes", 5),
                "long_break_after": settings.get("long_break_after", 3),
                "long_break_minutes": settings.get("long_break_minutes", 10),
                "max_periods_per_shift": settings.get(
                    "max_periods_per_shift", 6
                ),
                "shifts": [
                    {
                        "shift_no": shift_no,
                        "starts_at": (
                            settings.get("first_shift_start", "08:00")
                            if shift_no == 1
                            else settings.get("second_shift_start", "13:10")
                        ),
                        "max_lessons": max_by_shift.get(
                            str(shift_no), fallback_max
                        ),
                    }
                    for shift_no in range(1, int(school["shift_count"]) + 1)
                ],
            }
            cur.execute(
                """SELECT
                    (SELECT count(*) FROM school_sections WHERE context_id=%s AND active) sections,
                    (SELECT count(*) FROM school_rooms WHERE context_id=%s AND active) rooms,
                    (SELECT count(DISTINCT user_id) FROM school_role_assignments
                     WHERE context_id=%s AND status='active' AND role_key=ANY(%s)) staff,
                    (SELECT count(DISTINCT user_id) FROM school_role_assignments
                     WHERE context_id=%s AND status='active' AND role_key='student') students,
                    (SELECT count(*) FROM school_calendar_events
                     WHERE context_id=%s AND status='published'
                       AND starts_at>=CURRENT_DATE AND starts_at<CURRENT_DATE+INTERVAL '7 days') week_events""",
                (context_id, context_id, context_id, list(STAFF_ROLES),
                 context_id, context_id),
            )
            counts = cur.fetchone()
        role_set = set(roles)
        menus = ["overview"]
        if role_set & TEACHING_ROLES or "system_admin" in role_set:
            menus += ["timetable", "attendance", "grades", "calendar"]
        if role_set & MANAGER_ROLES or "system_admin" in role_set:
            menus += ["campus", "sections", "subjects", "staff", "schedule_builder"]
        if role_set & FINANCE_ROLES and school["ownership_type"] == "private":
            menus += ["billing"]
        return {"school": school, "roles": sorted(role_set), "menus": menus, "counts": counts}

    @router.post("/buildings")
    def create_building(
        request: BuildingCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, MANAGER_ROLES)
            cur.execute(
                """INSERT INTO school_buildings(
                     context_id,name,building_order,metadata
                   ) VALUES(%s,%s,%s,%s::jsonb)
                   RETURNING id,name,building_order,metadata""",
                (
                    request.context_id, request.name.strip(),
                    request.building_order,
                    json.dumps({"entrance_side": request.entrance_side}),
                ),
            )
            building = cur.fetchone()
            room_count = 0
            for floor in request.floors:
                cur.execute(
                    """INSERT INTO school_floors(context_id,building_id,floor_number,name)
                       VALUES(%s,%s,%s,%s) RETURNING id""",
                    (request.context_id, building["id"], floor.floor_number, floor.name),
                )
                floor_id = cur.fetchone()["id"]
                for room in floor.rooms:
                    cur.execute(
                        """INSERT INTO school_rooms(
                             context_id,floor_id,room_number,name,room_type,capacity,position
                           ) VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                        (
                            request.context_id, floor_id, room.room_number.strip(),
                            room.name.strip(), room.room_type, room.capacity, room.position,
                        ),
                    )
                    room_count += 1
            audit(cur, request.context_id, user_id, "building.create",
                  "building", building["id"], {"rooms": room_count})
        return {"building": building, "room_count": room_count}

    @router.get("/buildings")
    def list_buildings(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=20, ge=1, le=100),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, VIEW_ROLES)
            cur.execute(
                """SELECT id,name,building_order,metadata FROM school_buildings
                   WHERE context_id=%s AND active=TRUE AND id>%s
                   ORDER BY id LIMIT %s""",
                (context_id, after_id or 0, limit + 1),
            )
            rows = cur.fetchall()
            ids = [r["id"] for r in rows[:limit]]
            floors: list[Any] = []
            rooms: list[Any] = []
            if ids:
                cur.execute(
                    """SELECT id,building_id,floor_number,name FROM school_floors
                       WHERE context_id=%s AND building_id=ANY(%s)
                       ORDER BY building_id,floor_number,id""",
                    (context_id, ids),
                )
                floors = cur.fetchall()
                floor_ids = [r["id"] for r in floors]
                if floor_ids:
                    cur.execute(
                        """SELECT id,floor_id,room_number,name,room_type,capacity,position
                           FROM school_rooms
                           WHERE context_id=%s AND floor_id=ANY(%s) AND active=TRUE
                           ORDER BY floor_id,position,room_number,id""",
                        (context_id, floor_ids),
                    )
                    rooms = cur.fetchall()
        room_map: dict[int, list[Any]] = defaultdict(list)
        for room in rooms:
            room_map[int(room["floor_id"])].append(room)
        floor_map: dict[int, list[Any]] = defaultdict(list)
        for floor in floors:
            floor = dict(floor)
            floor["rooms"] = room_map[int(floor["id"])]
            floor_map[int(floor["building_id"])].append(floor)
        items = []
        for row in rows[:limit]:
            row = dict(row)
            row["floors"] = floor_map[int(row["id"])]
            items.append(row)
        return {
            "items": items,
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
        }

    @router.post("/grades")
    def create_grade_section(
        request: SectionCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, MANAGER_ROLES)
            cur.execute("SELECT shift_count FROM school_profiles WHERE context_id=%s",
                        (request.context_id,))
            profile = cur.fetchone()
            if not profile or request.shift_no > profile["shift_count"]:
                raise HTTPException(status_code=422, detail="Tanlangan smena maktabda yo'q")
            if request.default_room_id is not None:
                cur.execute(
                    "SELECT 1 FROM school_rooms WHERE id=%s AND context_id=%s AND active=TRUE",
                    (request.default_room_id, request.context_id),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Xona topilmadi")
            name = f"{request.grade_no}-{request.section_name.strip().upper()}"
            cur.execute(
                """INSERT INTO course_groups(
                     context_id,group_type,delivery_mode,name,grade,teacher_user_id,metadata
                   ) VALUES(%s,'school_section','offline',%s,%s,%s,%s::jsonb)
                   RETURNING id""",
                (
                    request.context_id, name, str(request.grade_no),
                    request.homeroom_teacher_user_id,
                    json.dumps({"shift_no": request.shift_no}),
                ),
            )
            group_id = cur.fetchone()["id"]
            cur.execute(
                """INSERT INTO school_sections(
                     context_id,group_id,grade_no,section_name,shift_no,
                     homeroom_teacher_user_id,default_room_id,capacity
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id,group_id,grade_no,section_name,shift_no""",
                (
                    request.context_id, group_id, request.grade_no,
                    request.section_name.strip().upper(), request.shift_no,
                    request.homeroom_teacher_user_id, request.default_room_id,
                    request.capacity,
                ),
            )
            section = cur.fetchone()
            if request.homeroom_teacher_user_id:
                cur.execute(
                    """INSERT INTO school_role_assignments(
                         context_id,group_id,user_id,role_key,status,
                         approved_by_user_id,permissions
                       ) VALUES(%s,%s,%s,'homeroom_teacher','active',%s,
                                '{"source":"school_v2"}')
                       ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,role_key)
                       DO UPDATE SET status='active',ends_at=NULL,updated_at=NOW()""",
                    (
                        request.context_id, group_id,
                        request.homeroom_teacher_user_id, user_id,
                    ),
                )
            audit(cur, request.context_id, user_id, "section.create",
                  "section", section["id"])
        return {"section": section}

    @router.get("/grades")
    def list_grade_sections(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, VIEW_ROLES)
            cur.execute(
                """SELECT s.id,s.group_id,s.grade_no,s.section_name,s.shift_no,
                          s.homeroom_teacher_user_id,s.default_room_id,s.capacity,
                          u.full_name homeroom_teacher_name,r.name room_name
                   FROM school_sections s
                   LEFT JOIN users u ON u.user_id=s.homeroom_teacher_user_id
                   LEFT JOIN school_rooms r ON r.id=s.default_room_id AND r.context_id=s.context_id
                   WHERE s.context_id=%s AND s.active=TRUE AND s.id>%s
                   ORDER BY s.id LIMIT %s""",
                (context_id, after_id or 0, limit + 1),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
        }

    @router.post("/subjects")
    def create_subject(
        request: SubjectCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        if request.grade_to < request.grade_from:
            raise HTTPException(status_code=422, detail="Sinf oralig'i teskari")
        code = re.sub(r"[^a-z0-9_-]+", "_", request.code.lower().strip())
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, ACADEMIC_ROLES)
            cur.execute(
                """INSERT INTO school_subjects(
                     context_id,code,name,grade_from,grade_to,weekly_hours,preferred_period_max
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(context_id,code) DO UPDATE SET
                     name=EXCLUDED.name,grade_from=EXCLUDED.grade_from,
                     grade_to=EXCLUDED.grade_to,weekly_hours=EXCLUDED.weekly_hours,
                     preferred_period_max=EXCLUDED.preferred_period_max,
                     active=TRUE,updated_at=NOW()
                   RETURNING id,code,name,grade_from,grade_to,weekly_hours,preferred_period_max""",
                (
                    request.context_id, code, request.name.strip(),
                    request.grade_from, request.grade_to, request.weekly_hours,
                    request.preferred_period_max,
                ),
            )
            subject = cur.fetchone()
        return {"subject": subject}

    @router.get("/subjects")
    def list_subjects(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=100, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, VIEW_ROLES)
            cur.execute(
                """SELECT id,code,name,grade_from,grade_to,weekly_hours,preferred_period_max
                   FROM school_subjects WHERE context_id=%s AND active=TRUE AND id>%s
                   ORDER BY id LIMIT %s""",
                (context_id, after_id or 0, limit + 1),
            )
            rows = cur.fetchall()
        return {"items": rows[:limit],
                "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/workloads")
    def create_workload(
        request: WorkloadCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, ACADEMIC_ROLES)
            cur.execute(
                """SELECT s.id,s.grade_no FROM school_sections s
                   WHERE s.id=%s AND s.context_id=%s AND s.active=TRUE""",
                (request.section_id, request.context_id),
            )
            section = cur.fetchone()
            if not section:
                raise HTTPException(status_code=404, detail="Sinf topilmadi")
            cur.execute(
                """SELECT code,name,preferred_period_max FROM school_subjects
                   WHERE id=%s AND context_id=%s AND active=TRUE
                     AND %s BETWEEN grade_from AND grade_to""",
                (request.subject_id, request.context_id, section["grade_no"]),
            )
            subject = cur.fetchone()
            if not subject:
                raise HTTPException(
                    status_code=422, detail="Fan bu sinf bosqichiga mos emas"
                )
            cur.execute(
                """SELECT 1 FROM school_role_assignments
                   WHERE context_id=%s AND user_id=%s AND status='active'
                     AND role_key=ANY(%s)""",
                (
                    request.context_id, request.teacher_user_id,
                    ["teacher", "homeroom_teacher"],
                ),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=422,
                    detail="O'qituvchi shu maktabda faol emas",
                )
            cur.execute(
                """INSERT INTO school_teacher_subjects(
                     context_id,user_id,subject_id,grade_from,grade_to
                   ) VALUES(%s,%s,%s,%s,%s)
                   ON CONFLICT(context_id,user_id,subject_id) DO UPDATE SET
                     grade_from=LEAST(
                       school_teacher_subjects.grade_from,EXCLUDED.grade_from
                     ),
                     grade_to=GREATEST(
                       school_teacher_subjects.grade_to,EXCLUDED.grade_to
                     )""",
                (
                    request.context_id, request.teacher_user_id,
                    request.subject_id, section["grade_no"], section["grade_no"],
                ),
            )
            cur.execute(
                """SELECT COALESCE(max_weekly_periods,36) max_weekly
                   FROM school_teacher_settings
                   WHERE context_id=%s AND user_id=%s""",
                (request.context_id, request.teacher_user_id),
            )
            setting = cur.fetchone()
            max_weekly = int(setting["max_weekly"]) if setting else 36
            cur.execute(
                """SELECT COALESCE(sum(weekly_hours),0) assigned_hours
                   FROM school_workloads
                   WHERE context_id=%s AND teacher_user_id=%s AND active=TRUE
                     AND NOT(section_id=%s AND subject_id=%s)""",
                (
                    request.context_id, request.teacher_user_id,
                    request.section_id, request.subject_id,
                ),
            )
            assigned_hours = int(cur.fetchone()["assigned_hours"])
            cur.execute(
                """SELECT count(*) class_hours FROM school_sections
                   WHERE context_id=%s AND active=TRUE
                     AND homeroom_teacher_user_id=%s""",
                (request.context_id, request.teacher_user_id),
            )
            class_hours = int(cur.fetchone()["class_hours"])
            if assigned_hours + class_hours + request.weekly_hours > max_weekly:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"O'qituvchi haftalik limiti {max_weekly} soat. "
                        f"Hozir {assigned_hours + class_hours} soat biriktirilgan."
                    ),
                )
            if request.preferred_room_id is not None:
                cur.execute(
                    """SELECT 1 FROM school_rooms
                       WHERE id=%s AND context_id=%s AND active=TRUE""",
                    (request.preferred_room_id, request.context_id),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Xona topilmadi")
            preferred_band = request.preferred_band
            if preferred_band == "any":
                cur.execute(
                    "SELECT settings FROM school_profiles WHERE context_id=%s",
                    (request.context_id,),
                )
                profile_settings = dict((cur.fetchone() or {}).get("settings") or {})
                preferences = dict(
                    profile_settings.get("workload_preferences") or {}
                )
                subject_text = f"{subject['code']} {subject['name']}".lower()
                exact_keywords = (
                    "matemat", "algebra", "geometri", "fizika", "kimyo"
                )
                physical_keywords = ("jismoniy", "sport")
                if (
                    subject["preferred_period_max"]
                    and int(subject["preferred_period_max"]) <= 3
                ) or (
                    preferences.get("avoid_math_last_periods")
                    and any(word in subject_text for word in exact_keywords)
                ) or (
                    preferences.get("prefer_physical_first_three")
                    and any(word in subject_text for word in physical_keywords)
                ):
                    preferred_band = "early"
            cur.execute(
                """INSERT INTO school_workloads(
                     context_id,section_id,subject_id,teacher_user_id,weekly_hours,
                     preferred_room_id,preferred_band,max_per_day
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(context_id,section_id,subject_id) DO UPDATE SET
                     teacher_user_id=EXCLUDED.teacher_user_id,
                     weekly_hours=EXCLUDED.weekly_hours,
                     preferred_room_id=EXCLUDED.preferred_room_id,
                     preferred_band=EXCLUDED.preferred_band,
                     max_per_day=EXCLUDED.max_per_day,
                     active=TRUE,updated_at=NOW()
                   RETURNING id,section_id,subject_id,teacher_user_id,weekly_hours,
                             preferred_room_id,preferred_band,max_per_day""",
                (
                    request.context_id, request.section_id, request.subject_id,
                    request.teacher_user_id, request.weekly_hours,
                    request.preferred_room_id, preferred_band,
                    request.max_per_day,
                ),
            )
            workload = cur.fetchone()
            audit(
                cur, request.context_id, user_id, "workload.upsert",
                "workload", workload["id"],
            )
        return {"workload": workload}

    @router.get("/workloads")
    def list_workloads(
        context_id: int = Query(ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=100, ge=1, le=300),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, VIEW_ROLES)
            cur.execute(
                """SELECT w.id,w.section_id,w.subject_id,w.teacher_user_id,
                          w.weekly_hours,w.preferred_room_id,w.preferred_band,
                          w.max_per_day,s.grade_no,s.section_name,
                          sub.name subject_name,u.full_name teacher_name
                   FROM school_workloads w
                   JOIN school_sections s ON s.id=w.section_id
                    AND s.context_id=w.context_id
                   JOIN school_subjects sub ON sub.id=w.subject_id
                    AND sub.context_id=w.context_id
                   JOIN users u ON u.user_id=w.teacher_user_id
                   WHERE w.context_id=%s AND w.active=TRUE AND w.id>%s
                   ORDER BY w.id LIMIT %s""",
                (context_id, after_id or 0, limit + 1),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
        }

    @router.post("/staff")
    def assign_staff(
        request: StaffAssign, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "Xodim vakolatini berishdan oldin inson tasdig'i kerak.",
        )
        if request.role_key not in STAFF_ROLES:
            raise HTTPException(status_code=422, detail="Noto'g'ri xodim roli")
        if request.grade_to < request.grade_from:
            raise HTTPException(status_code=422, detail="Sinf oralig'i teskari")
        with database() as (_, cur):
            ensure_schema(cur)
            caller_roles = require_roles(cur, request.context_id, user_id, MANAGER_ROLES)
            cur.execute("SELECT ownership_type FROM school_profiles WHERE context_id=%s",
                        (request.context_id,))
            profile = cur.fetchone()
            if request.role_key in {"owner", "founder"} and profile["ownership_type"] != "private":
                raise HTTPException(status_code=422, detail="Davlat maktabida mulkdor roli yo'q")
            if (
                request.role_key in {"owner", "founder"}
                and not (caller_roles & {"owner", "founder", "system_admin"})
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Mulkdor/ta'sischi rolini direktor bera olmaydi.",
                )
            if (
                request.role_key in PRIVILEGED_ASSIGNABLE - {"owner", "founder"}
                and not (caller_roles & {"owner", "founder", "director", "system_admin"})
            ):
                raise HTTPException(status_code=403, detail="Rahbarlik rolini faqat direktor/mulkdor beradi")
            if request.group_id is not None:
                ensure_group(cur, request.context_id, request.group_id)
            cur.execute("SELECT 1 FROM users WHERE user_id=%s", (request.user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
            cur.execute(
                """INSERT INTO school_role_assignments(
                     context_id,group_id,user_id,role_key,status,approved_by_user_id,permissions
                   ) VALUES(%s,%s,%s,%s,'active',%s,'{"source":"school_v2"}')
                   ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,role_key)
                   DO UPDATE SET status='active',approved_by_user_id=EXCLUDED.approved_by_user_id,
                     starts_at=NOW(),ends_at=NULL,updated_at=NOW()
                   RETURNING id""",
                (
                    request.context_id, request.group_id, request.user_id,
                    request.role_key, user_id,
                ),
            )
            assignment_id = cur.fetchone()["id"]
            if (
                request.role_key == "homeroom_teacher"
                and request.group_id is not None
            ):
                sync_homeroom_teacher(
                    cur, context_id=request.context_id,
                    group_id=request.group_id,
                    teacher_user_id=request.user_id,
                )
            generic = (
                "director" if request.role_key == "director"
                else "manager" if request.role_key in MANAGER_ROLES
                else "teacher"
            )
            cur.execute(
                """INSERT INTO context_memberships(
                     context_id,group_id,user_id,member_role,status,source,
                     approved_by_user_id,metadata
                   ) VALUES(%s,%s,%s,%s,'active','school_v2',%s,%s::jsonb)
                   ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,member_role)
                   DO UPDATE SET status='active',approved_by_user_id=EXCLUDED.approved_by_user_id,
                     ended_at=NULL,updated_at=NOW(),metadata=EXCLUDED.metadata""",
                (
                    request.context_id, request.group_id, request.user_id, generic,
                    user_id, json.dumps({"school_role": request.role_key}),
                ),
            )
            if request.subject_ids:
                cur.execute(
                    """SELECT id FROM school_subjects
                       WHERE context_id=%s AND id=ANY(%s) AND active=TRUE""",
                    (request.context_id, request.subject_ids),
                )
                found = {int(row["id"]) for row in cur.fetchall()}
                if found != set(request.subject_ids):
                    raise HTTPException(status_code=422, detail="Fanlardan biri boshqa maktabniki")
                for subject_id in found:
                    cur.execute(
                        """INSERT INTO school_teacher_subjects(
                             context_id,user_id,subject_id,grade_from,grade_to
                           ) VALUES(%s,%s,%s,%s,%s)
                           ON CONFLICT(context_id,user_id,subject_id) DO UPDATE SET
                             grade_from=EXCLUDED.grade_from,grade_to=EXCLUDED.grade_to""",
                        (
                            request.context_id, request.user_id, subject_id,
                            request.grade_from, request.grade_to,
                        ),
                    )
            audit(cur, request.context_id, user_id, "staff.assign",
                  "role_assignment", assignment_id,
                  {"user_id": request.user_id, "role": request.role_key})
        return {"assignment_id": assignment_id, "status": "active"}

    @router.post("/staff/invites")
    def create_staff_invite(
        request: StaffInviteCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "Xodim taklif kodini yaratish uchun inson tasdig'i kerak.",
        )
        if request.role_key not in STAFF_ROLES:
            raise HTTPException(status_code=422, detail="Noto'g'ri xodim roli")
        with database() as (_, cur):
            ensure_schema(cur)
            caller_roles = require_roles(
                cur, request.context_id, user_id, MANAGER_ROLES
            )
            cur.execute(
                "SELECT ownership_type FROM school_profiles WHERE context_id=%s",
                (request.context_id,),
            )
            ownership = cur.fetchone()
            if (
                request.role_key in {"owner", "founder"}
                and ownership["ownership_type"] != "private"
            ):
                raise HTTPException(
                    status_code=422, detail="Davlat maktabida mulkdor roli yo'q"
                )
            if (
                request.role_key in {"owner", "founder"}
                and not (caller_roles & {"owner", "founder", "system_admin"})
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Mulkdor/ta'sischi taklifini direktor bera olmaydi.",
                )
            if (
                request.role_key in PRIVILEGED_ASSIGNABLE - {"owner", "founder"}
                and not (
                    caller_roles
                    & {"owner", "founder", "director", "system_admin"}
                )
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Rahbarlik rolini faqat direktor/mulkdor taklif qiladi.",
                )
            if request.group_id is not None:
                ensure_group(cur, request.context_id, request.group_id)
            alphabet = string.ascii_uppercase + string.digits
            raw = "".join(secrets.choice(alphabet) for _ in range(12))
            code = f"SCH-{raw[:4]}-{raw[4:8]}-{raw[8:]}"
            digest = hashlib.sha256(re.sub(r"[^A-Z0-9]", "", code).encode()).hexdigest()
            metadata = {
                "method_day": request.method_day,
                "allowed_shifts": (
                    [int(request.available_shift)]
                    if request.available_shift in {"1", "2"} else [1, 2]
                ),
                "max_daily_lessons": request.max_daily_lessons,
            }
            cur.execute(
                """INSERT INTO school_invitations(
                     context_id,group_id,role_key,invited_name,invited_contact,
                     code_hash,created_by_user_id,metadata
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                   RETURNING id,role_key,status,expires_at""",
                (
                    request.context_id, request.group_id, request.role_key,
                    request.full_name, request.phone, digest, user_id,
                    json.dumps(metadata),
                ),
            )
            invitation = cur.fetchone()
            audit(
                cur, request.context_id, user_id, "invitation.create",
                "invitation", invitation["id"],
                {"role": request.role_key, "group_id": request.group_id},
            )
        return {"invitation": invitation, "invite_code": code}

    @router.get("/staff")
    def list_staff(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            roles = require_roles(cur, context_id, user_id, STAFF_ROLES)
            can_view_pending = bool(
                roles & MANAGER_ROLES or "system_admin" in roles
            )
            cur.execute(
                """SELECT r.id,r.user_id,u.full_name,r.role_key,r.group_id,
                          r.status,r.starts_at,r.ends_at
                   FROM school_role_assignments r JOIN users u ON u.user_id=r.user_id
                   WHERE r.context_id=%s AND r.role_key=ANY(%s) AND r.id>%s
                     AND (%s OR r.status='active')
                   ORDER BY r.id LIMIT %s""",
                (
                    context_id, list(STAFF_ROLES), after_id or 0,
                    can_view_pending, limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {"items": rows[:limit],
                "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.put("/staff/{teacher_user_id}/availability")
    def put_availability(
        teacher_user_id: int, request: TeacherAvailabilityPut,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            roles = active_roles(cur, request.context_id, user_id)
            manager = bool(roles & ACADEMIC_ROLES) or system_admin(cur, user_id)
            if teacher_user_id != user_id and not manager:
                raise HTTPException(status_code=403, detail="Boshqa o'qituvchi vaqtini o'zgartira olmaysiz")
            cur.execute(
                """SELECT 1 FROM school_role_assignments
                   WHERE context_id=%s AND user_id=%s AND status='active'
                     AND role_key=ANY(%s)""",
                (request.context_id, teacher_user_id, ["teacher", "homeroom_teacher"]),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="O'qituvchi bu maktabda topilmadi")
            supplied_fields = request.model_fields_set
            if not manager and supplied_fields & {
                "max_daily_periods", "max_weekly_periods", "method_day"
            }:
                raise HTTPException(status_code=403, detail="Yuklama va metod kunini rahbar belgilaydi")
            if (
                "max_daily_periods" in supplied_fields
                and request.max_daily_periods is None
            ) or (
                "max_weekly_periods" in supplied_fields
                and request.max_weekly_periods is None
            ):
                raise HTTPException(
                    status_code=422,
                    detail="Kunlik/haftalik limit bo'sh bo'lishi mumkin emas.",
                )
            cur.execute(
                """SELECT method_day,max_daily_periods,max_weekly_periods,
                          preferred_shift,avoid_first_period
                   FROM school_teacher_settings
                   WHERE context_id=%s AND user_id=%s""",
                (request.context_id, teacher_user_id),
            )
            current = cur.fetchone() or {
                "method_day": None,
                "max_daily_periods": 6,
                "max_weekly_periods": 36,
                "preferred_shift": None,
                "avoid_first_period": False,
            }
            method_day = (
                request.method_day
                if "method_day" in supplied_fields else current["method_day"]
            )
            max_daily = (
                request.max_daily_periods
                if "max_daily_periods" in supplied_fields
                else current["max_daily_periods"]
            )
            max_weekly = (
                request.max_weekly_periods
                if "max_weekly_periods" in supplied_fields
                else current["max_weekly_periods"]
            )
            preferred_shift = (
                request.preferred_shift
                if "preferred_shift" in supplied_fields
                else current["preferred_shift"]
            )
            avoid_first = (
                request.avoid_first_period
                if "avoid_first_period" in supplied_fields
                else current["avoid_first_period"]
            )
            cur.execute(
                """INSERT INTO school_teacher_settings(
                     context_id,user_id,method_day,max_daily_periods,max_weekly_periods,
                     preferred_shift,avoid_first_period
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(context_id,user_id) DO UPDATE SET
                     method_day=EXCLUDED.method_day,
                     max_daily_periods=EXCLUDED.max_daily_periods,
                     max_weekly_periods=EXCLUDED.max_weekly_periods,
                     preferred_shift=EXCLUDED.preferred_shift,
                     avoid_first_period=EXCLUDED.avoid_first_period,
                     updated_at=NOW()""",
                (
                    request.context_id, teacher_user_id, method_day,
                    max_daily, max_weekly, preferred_shift, avoid_first,
                ),
            )
            cur.execute(
                "DELETE FROM school_teacher_availability WHERE context_id=%s AND user_id=%s",
                (request.context_id, teacher_user_id),
            )
            for row in request.rows:
                if row.period_to < row.period_from:
                    raise HTTPException(status_code=422, detail="Vaqt oralig'i teskari")
                cur.execute(
                    """INSERT INTO school_teacher_availability(
                         context_id,user_id,weekday,shift_no,period_from,period_to,
                         availability,note
                       ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        request.context_id, teacher_user_id, row.weekday, row.shift_no,
                        row.period_from, row.period_to, row.availability, row.note,
                    ),
                )
        return {"status": "saved", "rows": len(request.rows)}

    @router.get("/staff/{teacher_user_id}/availability")
    def get_availability(
        teacher_user_id: int, context_id: int = Query(ge=1),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            if teacher_user_id == user_id:
                require_roles(
                    cur, context_id, user_id,
                    {"teacher", "homeroom_teacher", *ACADEMIC_ROLES},
                )
            else:
                require_roles(cur, context_id, user_id, ACADEMIC_ROLES)
            cur.execute(
                "SELECT * FROM school_teacher_settings WHERE context_id=%s AND user_id=%s",
                (context_id, teacher_user_id),
            )
            settings = cur.fetchone()
            cur.execute(
                """SELECT id,weekday,shift_no,period_from,period_to,availability,note
                   FROM school_teacher_availability
                   WHERE context_id=%s AND user_id=%s ORDER BY weekday,shift_no,period_from,id""",
                (context_id, teacher_user_id),
            )
            rows = cur.fetchall()
        return {"settings": settings, "rows": rows}

    @router.post("/calendar")
    def create_calendar_event(
        request: CalendarCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        if request.status == "published":
            require_human(request.confirmation, "Kalendarni e'lon qilish uchun inson tasdig'i kerak.")
        starts_at = aware(request.starts_at, "Boshlanish")
        ends_at = aware(request.ends_at, "Tugash")
        if ends_at <= starts_at:
            raise HTTPException(status_code=422, detail="Tugash boshlanishdan keyin bo'lsin")
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, ACADEMIC_ROLES,
                          group_id=request.group_id)
            if request.group_id:
                ensure_group(cur, request.context_id, request.group_id)
            cur.execute(
                """INSERT INTO school_calendar_events(
                     context_id,group_id,event_type,title,description,starts_at,ends_at,
                     status,created_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id,status,starts_at,ends_at""",
                (
                    request.context_id, request.group_id, request.event_type,
                    request.title.strip(), request.description, starts_at, ends_at,
                    request.status, user_id,
                ),
            )
            event = cur.fetchone()
            if request.status == "published":
                audit(cur, request.context_id, user_id, "calendar.publish",
                      "calendar_event", event["id"])
        return {"event": event}

    @router.get("/calendar")
    def list_calendar(
        context_id: int = Query(ge=1), after_start: datetime | None = None,
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if (after_start is None) != (after_id is None):
            raise HTTPException(status_code=422, detail="Kalendar cursor va ID birga yuborilsin")
        cursor_start = aware(after_start, "Cursor") if after_start else datetime(1970, 1, 1, tzinfo=timezone.utc)
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            roles = require_roles(cur, context_id, user_id, VIEW_ROLES)
            can_view_drafts = bool(
                roles & ACADEMIC_ROLES or "system_admin" in roles
            )
            can_view_all_groups = bool(
                roles & MANAGER_ROLES or "system_admin" in roles
            )
            cur.execute(
                """SELECT e.id,e.group_id,e.event_type,e.title,e.description,
                          e.starts_at,e.ends_at,e.status
                   FROM school_calendar_events e
                   WHERE e.context_id=%s AND (e.starts_at,e.id)>(%s,%s)
                     AND (%s OR e.status='published')
                     AND (
                       %s OR e.group_id IS NULL
                       OR EXISTS(
                         SELECT 1 FROM school_role_assignments r
                         WHERE r.context_id=e.context_id AND r.user_id=%s
                           AND r.group_id=e.group_id AND r.status='active'
                       )
                       OR EXISTS(
                         SELECT 1 FROM school_sections sec
                         JOIN school_workloads w
                           ON w.context_id=sec.context_id
                          AND w.section_id=sec.id AND w.active=TRUE
                         WHERE sec.context_id=e.context_id
                           AND sec.group_id=e.group_id
                           AND w.teacher_user_id=%s AND sec.active=TRUE
                       )
                       OR EXISTS(
                         SELECT 1 FROM school_parent_students ps
                         JOIN school_role_assignments sr
                           ON sr.context_id=ps.context_id
                          AND sr.user_id=ps.student_user_id
                          AND sr.role_key='student' AND sr.status='active'
                         WHERE ps.context_id=e.context_id
                           AND ps.parent_user_id=%s AND ps.status='active'
                           AND sr.group_id=e.group_id
                       )
                     )
                   ORDER BY e.starts_at,e.id LIMIT %s""",
                (
                    context_id, cursor_start, after_id or 0,
                    can_view_drafts, can_view_all_groups,
                    user_id, user_id, user_id, limit + 1,
                ),
            )
            rows = cur.fetchall()
        cursor = None
        if len(rows) > limit:
            last = rows[limit - 1]
            cursor = {"after_start": last["starts_at"], "after_id": last["id"]}
        return {"items": rows[:limit], "next_cursor": cursor}

    def effective_timetable_rows_for_dates(
        cur: Any, context_id: int, lesson_dates: list[date] | set[date]
    ) -> list[dict[str, Any]]:
        dates = sorted(set(lesson_dates))
        if not dates:
            return []
        require_calendar_dates(cur, context_id, dates)
        cur.execute(
            """WITH requested_dates AS (
                 SELECT unnest(%s::DATE[]) lesson_date
               )
               SELECT d.lesson_date,t.id slot_id,t.section_id,t.subject_id,
                      t.teacher_user_id original_teacher_user_id,
                      COALESCE(
                        CASE WHEN x.exception_kind='substitution'
                          THEN x.replacement_teacher_user_id END,
                        t.teacher_user_id
                      ) teacher_user_id,
                      t.room_id,t.weekday,t.shift_no,t.period_no,
                      t.starts_at,t.ends_at,sec.group_id,sec.grade_no,
                      sec.section_name,sub.name subject_name,
                      u.full_name teacher_name,r.name room_name,
                      x.id exception_id,x.exception_kind,x.reason exception_reason,
                      NULL::BIGINT makeup_event_id,
                      CASE WHEN x.exception_kind='substitution'
                        THEN 'substitution' ELSE 'recurring' END source_type
               FROM requested_dates d
               JOIN school_timetable_slots t
                 ON t.context_id=%s AND t.status='published'
                AND t.weekday=EXTRACT(ISODOW FROM d.lesson_date)
               JOIN school_sections sec
                 ON sec.id=t.section_id AND sec.context_id=t.context_id
               JOIN school_subjects sub
                 ON sub.id=t.subject_id AND sub.context_id=t.context_id
               LEFT JOIN school_timetable_exceptions x
                 ON x.context_id=t.context_id AND x.slot_id=t.id
                AND x.lesson_date=d.lesson_date AND x.status='active'
               JOIN users u ON u.user_id=COALESCE(
                 CASE WHEN x.exception_kind='substitution'
                   THEN x.replacement_teacher_user_id END,
                 t.teacher_user_id
               )
               LEFT JOIN school_rooms r
                 ON r.id=t.room_id AND r.context_id=t.context_id
               WHERE x.id IS NULL OR x.exception_kind='substitution'""",
            (dates, context_id),
        )
        rows = [dict(row) for row in cur.fetchall()]
        cur.execute(
            """SELECT x.target_date lesson_date,x.slot_id,x.id exception_id,
                      x.exception_kind,x.reason exception_reason,
                      x.makeup_event_id,t.section_id,t.subject_id,
                      x.original_teacher_user_id,
                      x.original_teacher_user_id teacher_user_id,
                      CASE
                        WHEN e.metadata->>'room_id' ~ '^[0-9]+$'
                          THEN (e.metadata->>'room_id')::BIGINT
                        ELSE t.room_id
                      END room_id,
                      EXTRACT(ISODOW FROM x.target_date)::INT weekday,
                      x.target_shift_no shift_no,
                      x.target_period_no period_no,
                      COALESCE(
                        (e.starts_at AT TIME ZONE 'Asia/Tashkent')::TIME,
                        clock.starts_at
                      ) starts_at,
                      COALESCE(
                        (e.ends_at AT TIME ZONE 'Asia/Tashkent')::TIME,
                        clock.ends_at
                      ) ends_at,
                      sec.group_id,sec.grade_no,sec.section_name,
                      sub.name subject_name,u.full_name teacher_name,
                      r.name room_name,'makeup_extra'::TEXT source_type
               FROM school_timetable_exceptions x
               JOIN school_timetable_slots t
                 ON t.id=x.slot_id AND t.context_id=x.context_id
               JOIN school_sections sec
                 ON sec.id=t.section_id AND sec.context_id=t.context_id
               JOIN school_subjects sub
                 ON sub.id=t.subject_id AND sub.context_id=t.context_id
               JOIN users u ON u.user_id=x.original_teacher_user_id
               LEFT JOIN school_calendar_events e
                 ON e.id=x.makeup_event_id AND e.context_id=x.context_id
               LEFT JOIN LATERAL (
                 SELECT c.starts_at,c.ends_at
                 FROM school_timetable_slots c
                 WHERE c.context_id=x.context_id AND c.status='published'
                   AND c.shift_no=x.target_shift_no
                   AND c.period_no=x.target_period_no
                 ORDER BY c.id LIMIT 1
               ) clock ON TRUE
               LEFT JOIN school_rooms r
                 ON r.id=CASE
                   WHEN e.metadata->>'room_id' ~ '^[0-9]+$'
                     THEN (e.metadata->>'room_id')::BIGINT
                   ELSE t.room_id
                 END AND r.context_id=x.context_id
               WHERE x.context_id=%s AND x.status='active'
                 AND x.exception_kind='makeup_extra'
                 AND x.target_date=ANY(%s::DATE[])""",
            (context_id, dates),
        )
        rows.extend(dict(row) for row in cur.fetchall())
        cur.execute(
            """SELECT
                 (e.starts_at AT TIME ZONE 'Asia/Tashkent')::DATE lesson_date,
                 t.id slot_id,NULL::BIGINT exception_id,
                 'makeup_extra'::TEXT exception_kind,
                 NULL::TEXT exception_reason,e.id makeup_event_id,
                 t.section_id,t.subject_id,t.teacher_user_id
                   original_teacher_user_id,
                 CASE WHEN e.metadata->>'teacher_user_id' ~ '^[0-9]+$'
                   THEN (e.metadata->>'teacher_user_id')::BIGINT
                   ELSE t.teacher_user_id END teacher_user_id,
                 CASE WHEN e.metadata->>'room_id' ~ '^[0-9]+$'
                   THEN (e.metadata->>'room_id')::BIGINT
                   ELSE t.room_id END room_id,
                 EXTRACT(
                   ISODOW FROM e.starts_at AT TIME ZONE 'Asia/Tashkent'
                 )::INT weekday,
                 COALESCE(
                   CASE WHEN e.metadata->>'shift_id' ~ '^[12]$'
                     THEN (e.metadata->>'shift_id')::SMALLINT END,
                   t.shift_no
                 ) shift_no,
                 CASE WHEN e.metadata->>'period_no' ~ '^[0-9]+$'
                   THEN (e.metadata->>'period_no')::SMALLINT
                   ELSE t.period_no END period_no,
                 (e.starts_at AT TIME ZONE 'Asia/Tashkent')::TIME starts_at,
                 (e.ends_at AT TIME ZONE 'Asia/Tashkent')::TIME ends_at,
                 sec.group_id,sec.grade_no,sec.section_name,
                 sub.name subject_name,u.full_name teacher_name,
                 r.name room_name,'published_makeup_event'::TEXT source_type
               FROM school_calendar_events e
               JOIN school_timetable_slots t
                 ON t.context_id=e.context_id
                AND t.id=CASE
                  WHEN e.metadata->>'original_lesson_id'
                    ~ '^[0-9]+:[0-9]{4}-[0-9]{2}-[0-9]{2}$'
                  THEN split_part(
                    e.metadata->>'original_lesson_id',':',1
                  )::BIGINT
                END
               JOIN school_sections sec
                 ON sec.id=t.section_id AND sec.context_id=t.context_id
               JOIN school_subjects sub
                 ON sub.id=t.subject_id AND sub.context_id=t.context_id
               JOIN users u ON u.user_id=CASE
                 WHEN e.metadata->>'teacher_user_id' ~ '^[0-9]+$'
                   THEN (e.metadata->>'teacher_user_id')::BIGINT
                 ELSE t.teacher_user_id END
               LEFT JOIN school_rooms r
                 ON r.id=CASE WHEN e.metadata->>'room_id' ~ '^[0-9]+$'
                   THEN (e.metadata->>'room_id')::BIGINT
                   ELSE t.room_id END
                AND r.context_id=e.context_id
               WHERE e.context_id=%s AND e.status='published'
                 AND e.event_type='lesson'
                 AND e.metadata ? 'makeup_key'
                 AND (e.starts_at AT TIME ZONE 'Asia/Tashkent')::DATE
                     =ANY(%s::DATE[])
                 AND NOT EXISTS(
                   SELECT 1 FROM school_timetable_exceptions x
                   WHERE x.context_id=e.context_id
                     AND x.makeup_event_id=e.id AND x.status='active'
                 )""",
            (context_id, dates),
        )
        rows.extend(dict(row) for row in cur.fetchall())
        for row in rows:
            row["effective_key"] = (
                f"{row['source_type']}:{row.get('exception_id') or row.get('makeup_event_id') or row['slot_id']}:"
                f"{row['lesson_date'].isoformat()}"
            )
        return sorted(
            rows,
            key=lambda row: (
                row["lesson_date"],
                row["starts_at"] or time.max,
                int(row["section_id"]),
                row["effective_key"],
            ),
        )

    def effective_timetable_rows(
        cur: Any, context_id: int, lesson_date: date
    ) -> list[dict[str, Any]]:
        return effective_timetable_rows_for_dates(
            cur, context_id, [lesson_date]
        )

    def build_makeup_plan(
        cur: Any, request: CalendarMakeupRequest
    ) -> tuple[Any, dict[tuple[str, int], tuple[time, time]]]:
        if request.allow_topic_compression:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Mavzu ID va ketma-ketliklari barqaror bog'lanmaguncha "
                    "avtomatik tig'izlashtirish o'chirilgan."
                ),
            )
        require_calendar_dates(
            cur,
            request.context_id,
            {
                *request.candidate_dates,
                *(item.lesson_date for item in request.cancellations),
            },
        )
        cur.execute(
            """SELECT work_days FROM school_profiles WHERE context_id=%s""",
            (request.context_id,),
        )
        profile = cur.fetchone()
        if not profile:
            raise HTTPException(status_code=404, detail="Maktab profili topilmadi")
        work_days = {int(value) for value in (profile["work_days"] or [])}
        cur.execute(
            """SELECT d holiday_date
               FROM unnest(%s::DATE[]) d
               WHERE EXISTS(
                 SELECT 1 FROM school_calendar_events e
                 WHERE e.context_id=%s AND e.event_type='holiday'
                   AND e.status='published'
                   AND (e.starts_at AT TIME ZONE 'Asia/Tashkent')::date<=d
                   AND (e.ends_at AT TIME ZONE 'Asia/Tashkent')::date>d
               )""",
            (
                request.candidate_dates,
                request.context_id,
            ),
        )
        holiday_dates = {row["holiday_date"] for row in cur.fetchall()}
        eligible_candidate_dates = sorted(
            {
                value for value in request.candidate_dates
                if value.isoweekday() in work_days
                and value not in holiday_dates
            }
        )
        if not eligible_candidate_dates:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Qoplov uchun ish kuni topilmadi; dam olish va bayram "
                    "sanalarini almashtiring."
                ),
            )
        slot_ids = sorted({item.slot_id for item in request.cancellations})
        cur.execute(
            """SELECT slot_id,lesson_date,exception_kind
               FROM school_timetable_exceptions
               WHERE context_id=%s AND status='active' AND slot_id=ANY(%s)""",
            (request.context_id, slot_ids),
        )
        requested_occurrences = {
            (item.slot_id, item.lesson_date)
            for item in request.cancellations
        }
        blocked_occurrences = [
            row for row in cur.fetchall()
            if (int(row["slot_id"]), row["lesson_date"])
            in requested_occurrences
        ]
        if blocked_occurrences:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Bekor qilinayotgan dars sanasida faol almashtirish "
                        "yoki qoplov allaqachon mavjud."
                    ),
                    "exceptions": blocked_occurrences,
                },
            )
        cur.execute(
            """SELECT t.id,t.section_id,t.teacher_user_id,t.room_id,t.weekday,
                      t.shift_no,t.period_no,t.starts_at,t.ends_at,
                      sec.group_id,s.name subject_name
               FROM school_timetable_slots t
               JOIN school_subjects s ON s.id=t.subject_id AND s.context_id=t.context_id
               JOIN school_sections sec
                 ON sec.id=t.section_id AND sec.context_id=t.context_id
               WHERE t.context_id=%s AND t.status='published'""",
            (request.context_id,),
        )
        slot_rows = [dict(row) for row in cur.fetchall()]
        row_by_id = {int(row["id"]): row for row in slot_rows}
        if not slot_ids or any(slot_id not in row_by_id for slot_id in slot_ids):
            raise HTTPException(
                status_code=422,
                detail="Bekor qilingan darslardan biri faol jadvalda topilmadi.",
            )
        all_dates = sorted(
            set(eligible_candidate_dates)
            | {item.lesson_date for item in request.cancellations}
        )
        effective_rows = effective_timetable_rows_for_dates(
            cur, request.context_id, all_dates
        )
        lessons = [
            CalendarLesson(
                id=(
                    f"{row['slot_id']}:{row['lesson_date'].isoformat()}"
                    if row["source_type"] in {"recurring", "substitution"}
                    else row["effective_key"]
                ),
                lesson_date=row["lesson_date"],
                shift_id=str(row["shift_no"]),
                period=int(row["period_no"]),
                class_id=str(row["section_id"]),
                subject=row["subject_name"],
                teacher_id=str(row["teacher_user_id"]),
                room_id=(
                    str(row["room_id"])
                    if row.get("room_id") is not None else None
                ),
            )
            for row in effective_rows
            if row.get("starts_at") is not None
            and row.get("ends_at") is not None
        ]
        cancellations = tuple(
            Cancellation(
                lesson_id=f"{item.slot_id}:{item.lesson_date.isoformat()}",
                reason=item.reason,
            )
            for item in request.cancellations
        )
        shift_periods: dict[str, dict[int, tuple[int, int]]] = defaultdict(dict)
        clock_map: dict[tuple[str, int], tuple[time, time]] = {}
        for row in slot_rows:
            key = (str(row["shift_no"]), int(row["period_no"]))
            start_value = row["starts_at"]
            end_value = row["ends_at"]
            clock_map[key] = (start_value, end_value)
            shift_periods[key[0]][key[1]] = (
                start_value.hour * 60 + start_value.minute,
                end_value.hour * 60 + end_value.minute,
            )
        shifts = tuple(
            Shift(
                shift_id, tuple(sorted(periods)),
                period_times=dict(periods),
            )
            for shift_id, periods in sorted(shift_periods.items())
        )
        teacher_ids = sorted(
            {int(row["teacher_user_id"]) for row in effective_rows}
            | {int(row["teacher_user_id"]) for row in slot_rows}
        )
        cur.execute(
            """SELECT x.user_id,COALESCE(s.method_day,0) method_day,
                      LEAST(COALESCE(s.max_daily_periods,6),7) max_daily,
                      s.preferred_shift,
                      COALESCE(s.avoid_first_period,FALSE) avoid_first,
                      COALESCE(s.preferences,'{}'::jsonb) preferences
               FROM unnest(%s::BIGINT[]) x(user_id)
               LEFT JOIN school_teacher_settings s ON s.context_id=%s
                AND s.user_id=x.user_id""",
            (teacher_ids, request.context_id),
        )
        teacher_rows = cur.fetchall()
        cur.execute(
            """SELECT user_id,weekday,shift_no,period_from,period_to,availability
               FROM school_teacher_availability
               WHERE context_id=%s AND user_id=ANY(%s)""",
            (request.context_id, teacher_ids),
        )
        availability_rows = cur.fetchall()
        weekly_slots = {
            Slot(str(day), shift.id, period)
            for day in work_days
            for shift in shifts
            for period in shift.periods
        }
        teacher_models = []
        for row in teacher_rows:
            teacher_id = int(row["user_id"])
            allowed, preferred = teacher_slot_preferences(
                weekly_slots, availability_rows, teacher_id
            )
            allowed_shifts = {
                str(value)
                for value in dict(row["preferences"] or {}).get(
                    "allowed_shifts", [1, 2]
                )
                if str(value) in {"1", "2"}
            }
            allowed = frozenset(
                slot for slot in allowed if slot.shift_id in allowed_shifts
            )
            preferred = frozenset(
                slot for slot in preferred if slot.shift_id in allowed_shifts
            )
            teacher_models.append(
                Teacher(
                    id=str(teacher_id),
                    method_days=(
                        frozenset({str(row["method_day"])})
                        if row["method_day"] else frozenset()
                    ),
                    available_slots=allowed,
                    preferred_slots=preferred,
                    preferred_shift=(
                        str(row["preferred_shift"])
                        if row["preferred_shift"] else None
                    ),
                    avoid_first_period=bool(row["avoid_first"]),
                    max_daily_lessons=int(row["max_daily"]),
                )
            )
        teachers = tuple(teacher_models)
        room_ids = sorted(
            {
                int(row["room_id"]) for row in [*slot_rows, *effective_rows]
                if row.get("room_id") is not None
            }
        )
        makeup_request = MakeupRequest(
            lessons=tuple(lessons),
            cancellations=cancellations,
            candidate_dates=tuple(eligible_candidate_dates),
            shifts=shifts,
            teachers=teachers,
            rooms=tuple(SchedulerRoom(str(room_id)) for room_id in room_ids),
            day_labels=tuple(
                CalendarDayLabel(value, str(value.isoweekday()))
                for value in all_dates
            ),
            max_extra_lessons_per_class_per_day=(
                request.max_extra_lessons_per_class_per_day
            ),
            allow_topic_compression=False,
        )
        return plan_calendar_makeups(makeup_request), clock_map

    @router.post("/calendar/makeup/preview")
    def preview_calendar_makeup(
        request: CalendarMakeupRequest,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            ensure_exception_schema(cur)
            require_roles(cur, request.context_id, user_id, ACADEMIC_ROLES)
            result, _ = build_makeup_plan(cur, request)
        return {
            "placements": [asdict(item) for item in result.placements],
            "hard_conflicts": [asdict(item) for item in result.hard_conflicts],
            "warnings": [asdict(item) for item in result.quality_warnings],
            "requires_human_approval": True,
            "ready_to_publish": bool(result.placements) and not result.hard_conflicts,
        }

    @router.post("/calendar/makeup/confirm")
    def confirm_calendar_makeup(
        request: CalendarMakeupRequest,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "Qoplov/tig'izlashtirish rejasini e'lon qilish uchun inson tasdig'i kerak.",
        )
        request_key_data = request.model_dump(mode="json")
        request_key_data.pop("confirmation", None)
        request_key = hashlib.sha256(
            json.dumps(
                request_key_data, sort_keys=True, ensure_ascii=False
            ).encode()
        ).hexdigest()
        with database() as (_, cur):
            ensure_schema(cur)
            ensure_exception_schema(cur)
            require_roles(cur, request.context_id, user_id, ACADEMIC_ROLES)
            request_dates = {
                *request.candidate_dates,
                *(item.lesson_date for item in request.cancellations),
            }
            require_calendar_dates(
                cur, request.context_id, request_dates
            )
            lock_context_dates(
                cur, request.context_id, request_dates
            )
            cur.execute(
                """SELECT id,status,makeup_event_id
                   FROM school_timetable_exceptions
                   WHERE context_id=%s
                     AND idempotency_key LIKE %s
                   ORDER BY id""",
                (request.context_id, f"{request_key}:%"),
            )
            prior_exceptions = cur.fetchall()
            if prior_exceptions:
                if all(row["status"] == "active" for row in prior_exceptions):
                    return {
                        "status": "published",
                        "idempotent_replay": True,
                        "makeup_key": request_key,
                        "exception_ids": [
                            int(row["id"]) for row in prior_exceptions
                        ],
                        "event_ids": [
                            int(row["makeup_event_id"])
                            for row in prior_exceptions
                            if row["makeup_event_id"] is not None
                        ],
                    }
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Bu qoplov talabi avval bajarilib, keyin bekor "
                        "qilingan. Yangi reja tuzing."
                    ),
                )
            cur.execute(
                """SELECT id FROM school_calendar_events
                   WHERE context_id=%s AND status='published'
                     AND metadata->>'makeup_key'=%s LIMIT 1""",
                (request.context_id, request_key),
            )
            existing = cur.fetchone()
            if existing:
                return {
                    "status": "published",
                    "idempotent_replay": True,
                    "makeup_key": request_key,
                }
            result, clock_map = build_makeup_plan(cur, request)
            if result.hard_conflicts or not result.placements:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Qoplov rejasida majburiy ziddiyat bor.",
                        "hard_conflicts": [
                            asdict(item) for item in result.hard_conflicts
                        ],
                    },
                )
            created_ids = []
            cancellation_event_ids = []
            exception_ids = []
            tashkent_tz = timezone(timedelta(hours=5))
            cancellation_reasons = {
                (item.slot_id, item.lesson_date): item.reason
                for item in request.cancellations
            }
            planned_lessons = {
                item.id: item for item in result.original_lessons
            }
            for sequence_no, placement in enumerate(result.placements, start=1):
                original_slot_id = int(
                    str(placement.original_lesson_id).split(":", 1)[0]
                )
                cur.execute(
                    """SELECT t.teacher_user_id,t.section_id,t.subject_id,
                              sec.group_id,sub.name subject_name
                       FROM school_timetable_slots t
                       JOIN school_sections sec
                         ON sec.id=t.section_id AND sec.context_id=t.context_id
                       JOIN school_subjects sub
                         ON sub.id=t.subject_id AND sub.context_id=t.context_id
                       WHERE t.context_id=%s AND t.id=%s
                         AND t.status='published'""",
                    (request.context_id, original_slot_id),
                )
                original = cur.fetchone()
                if not original:
                    raise HTTPException(
                        status_code=409,
                        detail="Qoplovning asl darsi endi faol emas.",
                    )
                reason = cancellation_reasons.get(
                    (original_slot_id, placement.original_date)
                )
                if not reason:
                    raise HTTPException(
                        status_code=409,
                        detail="Bekor qilish sababi qoplov natijasiga mos emas.",
                    )
                clock = clock_map.get((placement.shift_id, placement.period))
                if not clock:
                    raise HTTPException(
                        status_code=409,
                        detail="Qoplov uchun qo'ng'iroq vaqti topilmadi.",
                    )
                starts_at = datetime.combine(
                    placement.target_date, clock[0], tzinfo=tashkent_tz
                )
                ends_at = datetime.combine(
                    placement.target_date, clock[1], tzinfo=tashkent_tz
                )
                source_lesson = planned_lessons.get(
                    placement.original_lesson_id
                )
                original_clock = (
                    clock_map.get(
                        (
                            source_lesson.shift_id,
                            source_lesson.period,
                        )
                    )
                    if source_lesson else None
                )
                if not original_clock:
                    raise HTTPException(
                        status_code=409,
                        detail="Asl darsning qo'ng'iroq vaqti topilmadi.",
                    )
                original_starts_at = datetime.combine(
                    placement.original_date,
                    original_clock[0],
                    tzinfo=tashkent_tz,
                )
                original_ends_at = datetime.combine(
                    placement.original_date,
                    original_clock[1],
                    tzinfo=tashkent_tz,
                )
                cur.execute(
                    """INSERT INTO school_calendar_events(
                         context_id,group_id,event_type,title,description,
                         starts_at,ends_at,status,created_by_user_id,metadata
                       ) VALUES(
                         %s,%s,'lesson',%s,%s,%s,%s,'cancelled',%s,%s::jsonb
                       ) RETURNING id""",
                    (
                        request.context_id, original["group_id"],
                        f"Bekor qilingan dars: {original['subject_name']}",
                        reason, original_starts_at, original_ends_at, user_id,
                        json.dumps(
                            {
                                "makeup_key": request_key,
                                "slot_id": original_slot_id,
                                "lesson_date": (
                                    placement.original_date.isoformat()
                                ),
                                "sequence_no": sequence_no,
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
                cancellation_event_id = int(cur.fetchone()["id"])
                cancellation_event_ids.append(cancellation_event_id)
                metadata = {
                    "makeup_key": request_key,
                    "original_lesson_id": placement.original_lesson_id,
                    "original_date": placement.original_date.isoformat(),
                    "mode": placement.mode,
                    "target_lesson_id": placement.target_lesson_id,
                    "teacher_user_id": int(placement.teacher_id),
                    "room_id": int(placement.room_id) if placement.room_id else None,
                    "section_id": int(original["section_id"]),
                    "subject_id": int(original["subject_id"]),
                    "group_id": int(original["group_id"]),
                    "shift_id": int(placement.shift_id),
                    "period_no": placement.period,
                    "approved_by": user_id,
                    "cancellation_event_id": cancellation_event_id,
                    "sequence_no": sequence_no,
                }
                cur.execute(
                    """INSERT INTO school_calendar_events(
                         context_id,group_id,event_type,title,description,
                         starts_at,ends_at,
                         status,created_by_user_id,metadata
                       ) VALUES(
                         %s,%s,'lesson',%s,%s,%s,%s,'published',%s,%s::jsonb
                       )
                       RETURNING id""",
                    (
                        request.context_id, original["group_id"],
                        (
                            f"Qoplov darsi: {placement.subject}"
                        ),
                        (
                            "Asl bekor qilish tarixi saqlandi; "
                            "tasdiqlangan qoplov darsi."
                        ),
                        starts_at, ends_at, user_id,
                        json.dumps(metadata, ensure_ascii=False),
                    ),
                )
                makeup_event_id = int(cur.fetchone()["id"])
                created_ids.append(makeup_event_id)
                cur.execute(
                    """INSERT INTO school_timetable_exceptions(
                         context_id,slot_id,lesson_date,exception_kind,
                         original_teacher_user_id,target_date,target_shift_no,
                         target_period_no,makeup_event_id,sequence_no,reason,
                         idempotency_key,created_by_user_id,metadata
                       ) VALUES(
                         %s,%s,%s,'makeup_extra',%s,%s,%s,%s,%s,%s,%s,%s,%s,
                         %s::jsonb
                       )
                       ON CONFLICT(context_id,slot_id,lesson_date)
                         WHERE status='active' DO NOTHING
                       RETURNING id""",
                    (
                        request.context_id, original_slot_id,
                        placement.original_date,
                        original["teacher_user_id"], placement.target_date,
                        int(placement.shift_id), placement.period,
                        makeup_event_id, sequence_no, reason,
                        f"{request_key}:{sequence_no}", user_id,
                        json.dumps(
                            {
                                "cancellation_event_id": cancellation_event_id,
                                "section_id": original["section_id"],
                                "subject_id": original["subject_id"],
                            },
                            ensure_ascii=False,
                        ),
                    ),
                )
                exception = cur.fetchone()
                if not exception:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Asl dars sanasida boshqa faol jadval istisnosi "
                            "mavjud."
                        ),
                    )
                exception_ids.append(int(exception["id"]))
            audit(
                cur, request.context_id, user_id, "calendar.makeup.publish",
                "calendar_makeup", None,
                {
                    "makeup_key": request_key,
                    "events": created_ids,
                    "cancellations": cancellation_event_ids,
                    "exceptions": exception_ids,
                },
            )
        return {
            "status": "published",
            "idempotent_replay": False,
            "event_ids": created_ids,
            "cancellation_event_ids": cancellation_event_ids,
            "exception_ids": exception_ids,
            "warnings": [asdict(item) for item in result.quality_warnings],
        }

    def period_clock(
        start_text: str, lesson_minutes: int, period_no: int,
        short_break: int, long_after: int, long_break: int,
    ) -> tuple[str, str]:
        start = valid_time(start_text, "Smena boshlanishi")
        total = start.hour * 60 + start.minute
        total += (period_no - 1) * (lesson_minutes + short_break)
        if period_no > long_after:
            total += max(0, long_break - short_break)
        end_total = total + lesson_minutes
        if total < 0 or end_total >= 24 * 60:
            raise HTTPException(
                status_code=422,
                detail="Dars qo'ng'irog'i bir sutka chegarasidan chiqib ketdi.",
            )
        begin = time(total // 60, total % 60)
        end = time(end_total // 60, end_total % 60)
        return begin.strftime("%H:%M"), end.strftime("%H:%M")

    def scheduler_request_from_db(
        cur: Any, request: TimetableGenerate
    ) -> tuple[TimetableRequest, dict[str, Any], dict[str, Any]]:
        cur.execute(
            """SELECT shift_count,lesson_minutes,work_days,settings FROM school_profiles
               WHERE context_id=%s""",
            (request.context_id,),
        )
        profile = dict(cur.fetchone() or {})
        if not profile:
            raise HTTPException(status_code=404, detail="Maktab profili topilmadi")
        profile_settings = dict(profile.get("settings") or {})
        profile["effective_first_shift_start"] = str(
            profile_settings.get("first_shift_start") or "08:00"
        )
        profile["effective_second_shift_start"] = str(
            profile_settings.get("second_shift_start") or "13:10"
        )
        profile["effective_max_periods_per_shift"] = bounded_int(
            profile_settings.get("max_periods_per_shift"),
            "Saqlangan smenadagi darslar soni", 1, 12, default=6,
        )
        raw_max_by_shift = dict(
            profile_settings.get("max_periods_by_shift") or {}
        )
        profile["effective_max_periods_by_shift"] = {
            str(shift_no): bounded_int(
                raw_max_by_shift.get(
                    str(shift_no),
                    profile["effective_max_periods_per_shift"],
                ),
                f"Saqlangan {shift_no}-smenadagi darslar soni",
                1, 12,
            )
            for shift_no in range(1, int(profile["shift_count"]) + 1)
        }
        profile["effective_short_break_minutes"] = bounded_int(
            profile_settings.get("short_break_minutes"),
            "Saqlangan qisqa tanaffus", 0, 60, default=5,
        )
        profile["effective_long_break_after"] = bounded_int(
            profile_settings.get("long_break_after"),
            "Saqlangan uzun tanaffus joyi", 1, 12, default=3,
        )
        profile["effective_long_break_minutes"] = bounded_int(
            profile_settings.get("long_break_minutes"),
            "Saqlangan uzun tanaffus", 0, 90, default=10,
        )
        valid_time(
            profile["effective_first_shift_start"], "Saqlangan 1-smena boshlanishi"
        )
        valid_time(
            profile["effective_second_shift_start"], "Saqlangan 2-smena boshlanishi"
        )
        cur.execute(
            """SELECT id,grade_no,shift_no,default_room_id,
                      homeroom_teacher_user_id
               FROM school_sections
               WHERE context_id=%s AND active=TRUE
                 AND (%s::BIGINT[]='{}' OR id=ANY(%s))
               ORDER BY shift_no,grade_no,section_name,id""",
            (request.context_id, request.section_ids, request.section_ids),
        )
        section_rows = cur.fetchall()
        if not section_rows:
            raise HTTPException(status_code=422, detail="Jadval uchun sinf topilmadi")
        section_ids = [int(row["id"]) for row in section_rows]
        cur.execute(
            """SELECT w.id,w.section_id,w.subject_id,w.teacher_user_id,
                      w.weekly_hours,w.preferred_room_id,w.preferred_band,
                      w.max_per_day,sub.name subject_name
               FROM school_workloads w
               JOIN school_subjects sub ON sub.id=w.subject_id
                AND sub.context_id=w.context_id AND sub.active=TRUE
               WHERE w.context_id=%s AND w.active=TRUE
                 AND w.section_id=ANY(%s)
               ORDER BY w.id""",
            (request.context_id, section_ids),
        )
        workload_rows = cur.fetchall()
        if not workload_rows:
            raise HTTPException(
                status_code=422,
                detail="Avval sinf+fan+o'qituvchi haftalik yuklamalarini kiriting.",
            )
        teacher_ids = sorted(
            {int(row["teacher_user_id"]) for row in workload_rows}
            | {
                int(row["homeroom_teacher_user_id"])
                for row in section_rows
                if row["homeroom_teacher_user_id"] is not None
            }
        )
        cur.execute(
            """SELECT x.user_id,COALESCE(s.method_day,0) method_day,
                      LEAST(COALESCE(s.max_daily_periods,6),7) max_daily,
                      COALESCE(s.max_weekly_periods,36) max_weekly,
                      s.preferred_shift,COALESCE(s.avoid_first_period,FALSE) avoid_first,
                      COALESCE(s.preferences,'{}'::jsonb) preferences
               FROM unnest(%s::BIGINT[]) x(user_id)
               LEFT JOIN school_teacher_settings s ON s.context_id=%s
                AND s.user_id=x.user_id""",
            (teacher_ids, request.context_id),
        )
        teacher_rows = cur.fetchall()
        cur.execute(
            """SELECT teacher_user_id,sum(weekly_hours)::INT weekly_hours
               FROM school_workloads
               WHERE context_id=%s AND active=TRUE
                 AND teacher_user_id=ANY(%s)
               GROUP BY teacher_user_id""",
            (request.context_id, teacher_ids),
        )
        weekly_totals = {
            int(row["teacher_user_id"]): int(row["weekly_hours"])
            for row in cur.fetchall()
        }
        cur.execute(
            """SELECT homeroom_teacher_user_id user_id,count(*)::INT class_hours
               FROM school_sections
               WHERE context_id=%s AND active=TRUE
                 AND homeroom_teacher_user_id=ANY(%s)
               GROUP BY homeroom_teacher_user_id""",
            (request.context_id, teacher_ids),
        )
        for row in cur.fetchall():
            teacher_id = int(row["user_id"])
            weekly_totals[teacher_id] = (
                weekly_totals.get(teacher_id, 0) + int(row["class_hours"])
            )
        for row in teacher_rows:
            assigned = weekly_totals.get(int(row["user_id"]), 0)
            if assigned > int(row["max_weekly"]):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"{row['user_id']} o'qituvchining {assigned} soat "
                        f"yuklamasi {row['max_weekly']} soat limitdan oshgan."
                    ),
                )
        cur.execute(
            """SELECT user_id,weekday,shift_no,period_from,period_to,availability
               FROM school_teacher_availability
               WHERE context_id=%s AND user_id=ANY(%s)""",
            (request.context_id, teacher_ids),
        )
        availability_rows = cur.fetchall()
        room_ids = {
            int(room_id)
            for row in section_rows
            for room_id in [row["default_room_id"]]
            if room_id is not None
        } | {
            int(room_id)
            for row in workload_rows
            for room_id in [row["preferred_room_id"]]
            if room_id is not None
        }
        room_rows: list[Any] = []
        if room_ids:
            cur.execute(
                """SELECT id FROM school_rooms
                   WHERE context_id=%s AND active=TRUE AND id=ANY(%s)""",
                (request.context_id, sorted(room_ids)),
            )
            room_rows = cur.fetchall()
            if {int(row["id"]) for row in room_rows} != room_ids:
                raise HTTPException(
                    status_code=422, detail="Yuklamadagi xonalardan biri faol emas"
                )

        days = tuple(str(int(day)) for day in profile["work_days"])
        shifts_list = []
        for number in range(1, int(profile["shift_count"]) + 1):
            periods = tuple(
                range(
                    1,
                    int(
                        profile["effective_max_periods_by_shift"][str(number)]
                    )
                    + 1,
                )
            )
            start_text = (
                profile["effective_first_shift_start"] if number == 1
                else profile["effective_second_shift_start"]
            )
            period_times: dict[int, tuple[int, int]] = {}
            for period_no in periods:
                begins, ends = period_clock(
                    start_text, int(profile["lesson_minutes"]), period_no,
                    int(profile["effective_short_break_minutes"]),
                    int(profile["effective_long_break_after"]),
                    int(profile["effective_long_break_minutes"]),
                )
                period_times[period_no] = (
                    int(begins[:2]) * 60 + int(begins[3:]),
                    int(ends[:2]) * 60 + int(ends[3:]),
                )
            shifts_list.append(
                Shift(str(number), periods, period_times=period_times)
            )
        shifts = tuple(shifts_list)
        all_slots = {
            Slot(day, shift.id, period)
            for day in days for shift in shifts for period in shift.periods
        }
        teachers = []
        for row in teacher_rows:
            teacher_id = int(row["user_id"])
            allowed, preferred = teacher_slot_preferences(
                all_slots, availability_rows, teacher_id
            )
            stored_preferences = dict(row["preferences"] or {})
            allowed_shifts = {
                str(value)
                for value in stored_preferences.get(
                    "allowed_shifts",
                    range(1, int(profile["shift_count"]) + 1),
                )
                if str(value) in {"1", "2"}
            }
            allowed = frozenset(
                slot for slot in allowed if slot.shift_id in allowed_shifts
            )
            preferred = frozenset(
                slot for slot in preferred if slot.shift_id in allowed_shifts
            )
            teachers.append(
                Teacher(
                    id=str(teacher_id),
                    method_days=(
                        frozenset({str(row["method_day"])})
                        if row["method_day"] else frozenset()
                    ),
                    available_slots=allowed,
                    preferred_slots=preferred,
                    preferred_shift=(
                        str(row["preferred_shift"])
                        if row["preferred_shift"] else None
                    ),
                    avoid_first_period=bool(row["avoid_first"]),
                    max_daily_lessons=min(int(row["max_daily"]), 7),
                )
            )
        classes = tuple(
            SchoolClass(
                id=str(row["id"]),
                shift_id=str(row["shift_no"]),
                home_room_id=(
                    str(row["default_room_id"])
                    if row["default_room_id"] is not None else None
                ),
                class_teacher_id=(
                    str(row["homeroom_teacher_user_id"])
                    if row["homeroom_teacher_user_id"] is not None else None
                ),
                class_hour=(
                    ClassHourRule(
                        day="5", period=1,
                        teacher_id=str(row["homeroom_teacher_user_id"]),
                        room_id=(
                            str(row["default_room_id"])
                            if row["default_room_id"] is not None else None
                        ),
                    )
                    if row["homeroom_teacher_user_id"] is not None else None
                ),
            )
            for row in section_rows
        )
        workload_map = {f"w:{row['id']}": dict(row) for row in workload_rows}
        cur.execute(
            """INSERT INTO school_subjects(
                 context_id,code,name,grade_from,grade_to,preferred_period_max
               ) VALUES(%s,'sinf_soati','Sinf soati',1,11,1)
               ON CONFLICT(context_id,code) DO UPDATE SET active=TRUE,updated_at=NOW()
               RETURNING id""",
            (request.context_id,),
        )
        workload_map["__class_hour__"] = {
            "subject_id": int(cur.fetchone()["id"])
        }
        demands = tuple(
            LessonDemand(
                id=f"w:{row['id']}",
                class_id=str(row["section_id"]),
                subject=row["subject_name"],
                teacher_id=str(row["teacher_user_id"]),
                weekly_hours=int(row["weekly_hours"]),
                room_ids=(
                    (str(row["preferred_room_id"]),)
                    if row["preferred_room_id"] is not None
                    else ()
                ),
                preferred_band=row["preferred_band"],
                max_per_day=int(row["max_per_day"]),
            )
            for row in workload_rows
        )
        preferences = tuple(
            SubjectPreference(row["subject_name"], row["preferred_band"])
            for row in workload_rows if row["preferred_band"] != "any"
        )
        schedule_request = TimetableRequest(
            days=days,
            shifts=shifts,
            classes=classes,
            teachers=tuple(teachers),
            rooms=tuple(SchedulerRoom(str(row["id"])) for row in room_rows),
            demands=demands,
            subject_preferences=preferences,
            class_hour_policy=ClassHourPolicy(
                day="5", period=1, required_for_all_classes=False
            ),
        )
        return schedule_request, workload_map, dict(profile)

    def bell_clock_map(
        request: TimetableGenerate, profile: dict[str, Any]
    ) -> dict[tuple[int, int], tuple[str, str]]:
        result: dict[tuple[int, int], tuple[str, str]] = {}
        intervals: list[tuple[int, int, int, int]] = []
        for shift_no in range(1, int(profile["shift_count"]) + 1):
            start_text = (
                profile["effective_first_shift_start"] if shift_no == 1
                else profile["effective_second_shift_start"]
            )
            for period_no in range(
                1,
                int(
                    profile["effective_max_periods_by_shift"][str(shift_no)]
                )
                + 1,
            ):
                starts_at, ends_at = period_clock(
                    start_text, int(profile["lesson_minutes"]), period_no,
                    int(profile["effective_short_break_minutes"]),
                    int(profile["effective_long_break_after"]),
                    int(profile["effective_long_break_minutes"]),
                )
                start_minute = int(starts_at[:2]) * 60 + int(starts_at[3:])
                end_minute = int(ends_at[:2]) * 60 + int(ends_at[3:])
                intervals.append((shift_no, period_no, start_minute, end_minute))
                result[(shift_no, period_no)] = (starts_at, ends_at)
        if int(profile["shift_count"]) == 2:
            first_end = max(end for shift, _, _, end in intervals if shift == 1)
            second_start = min(start for shift, _, start, _ in intervals if shift == 2)
            if first_end > second_start:
                raise HTTPException(
                    status_code=422,
                    detail="1- va 2-smena haqiqiy vaqtda ustma-ust tushmoqda.",
                )
        return result

    def scheduler_slots(
        assignments: tuple[SchedulerAssignment, ...],
        workload_map: dict[str, Any],
        clock_map: dict[tuple[int, int], tuple[str, str]],
    ) -> list[dict[str, Any]]:
        slots: list[dict[str, Any]] = []
        for item in assignments:
            workload = (
                workload_map.get("__class_hour__")
                if item.source == "class_hour"
                else workload_map.get(str(item.demand_id))
            )
            if not workload:
                raise HTTPException(
                    status_code=409, detail="Generator noma'lum yuklama qaytardi"
                )
            shift_no = int(item.shift_id)
            weekday = int(item.day)
            starts_at, ends_at = clock_map[(shift_no, int(item.period))]
            slots.append(
                {
                    "section_id": int(item.class_id),
                    "subject_id": int(workload["subject_id"]),
                    "subject_name": item.subject,
                    "teacher_user_id": int(item.teacher_id),
                    "room_id": int(item.room_id) if item.room_id else None,
                    "weekday": weekday,
                    "shift_no": shift_no,
                    "period_no": int(item.period),
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                    "demand_id": (
                        f"class-hour:{item.class_id}"
                        if item.source == "class_hour" else item.demand_id
                    ),
                    "occurrence_index": item.occurrence_index,
                    "source": item.source,
                }
            )
        return slots

    def enrich_scheduler_slots(
        cur: Any, context_id: int, slots: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not slots:
            return slots
        section_ids = sorted({int(item["section_id"]) for item in slots})
        teacher_ids = sorted(
            {int(item["teacher_user_id"]) for item in slots}
        )
        room_ids = sorted(
            {
                int(item["room_id"]) for item in slots
                if item.get("room_id") is not None
            }
        )
        cur.execute(
            """SELECT id,grade_no,section_name FROM school_sections
               WHERE context_id=%s AND id=ANY(%s)""",
            (context_id, section_ids),
        )
        sections = {
            int(row["id"]): dict(row) for row in cur.fetchall()
        }
        cur.execute(
            """SELECT user_id,full_name FROM users WHERE user_id=ANY(%s)""",
            (teacher_ids,),
        )
        teachers = {
            int(row["user_id"]): row["full_name"] for row in cur.fetchall()
        }
        rooms: dict[int, str] = {}
        if room_ids:
            cur.execute(
                """SELECT id,name FROM school_rooms
                   WHERE context_id=%s AND id=ANY(%s)""",
                (context_id, room_ids),
            )
            rooms = {
                int(row["id"]): row["name"] for row in cur.fetchall()
            }
        for item in slots:
            section = sections.get(int(item["section_id"]), {})
            item["grade_no"] = section.get("grade_no")
            item["section_name"] = section.get("section_name")
            item["teacher_name"] = teachers.get(
                int(item["teacher_user_id"])
            )
            item["room_name"] = (
                rooms.get(int(item["room_id"]))
                if item.get("room_id") is not None else None
            )
        return slots

    @router.post("/timetable/generate")
    def generate_timetable(
        request: TimetableGenerate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, ACADEMIC_ROLES)
            schedule_request, workload_map, profile = scheduler_request_from_db(cur, request)
            clock_map = bell_clock_map(request, profile)
            result = run_school_scheduler(schedule_request)
            slots = enrich_scheduler_slots(
                cur, request.context_id,
                scheduler_slots(result.assignments, workload_map, clock_map),
            )
            conflicts = [asdict(item) for item in result.hard_conflicts]
            warnings = [asdict(item) for item in result.quality_warnings]
            constraints = request.model_dump(mode="json")
            constraints["first_shift_start"] = profile["effective_first_shift_start"]
            constraints["second_shift_start"] = profile["effective_second_shift_start"]
            constraints["max_periods_per_shift"] = profile[
                "effective_max_periods_per_shift"
            ]
            constraints["max_periods_by_shift"] = profile[
                "effective_max_periods_by_shift"
            ]
            constraints["short_break_minutes"] = profile[
                "effective_short_break_minutes"
            ]
            constraints["long_break_after"] = profile[
                "effective_long_break_after"
            ]
            constraints["long_break_minutes"] = profile[
                "effective_long_break_minutes"
            ]
            cur.execute(
                """INSERT INTO school_timetable_generations(
                     context_id,created_by_user_id,academic_year,term_no,
                     constraints,candidate_slots,conflicts
                   ) VALUES(%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb)
                   RETURNING id,status,version,created_at""",
                (
                    request.context_id, user_id, request.academic_year, request.term_no,
                    json.dumps(constraints, ensure_ascii=False),
                    json.dumps(slots, ensure_ascii=False),
                    json.dumps(conflicts, ensure_ascii=False, default=str),
                ),
            )
            generation = cur.fetchone()
        return {
            "generation": generation,
            "slots": slots,
            "conflicts": conflicts,
            "quality_warnings": warnings,
            "search_nodes": result.search_nodes,
            "ready_to_confirm": bool(slots) and not conflicts,
        }

    @router.get("/timetable/generations")
    def list_timetable_generations(
        context_id: int = Query(ge=1),
        status: Literal["draft", "confirmed", "rejected"] | None = None,
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=30, ge=1, le=100),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, ACADEMIC_ROLES)
            cur.execute(
                """SELECT id,status,academic_year,term_no,constraints,
                          candidate_slots,conflicts,
                          version,created_at,confirmed_at,
                          jsonb_array_length(candidate_slots) slot_count
                   FROM school_timetable_generations
                   WHERE context_id=%s AND (%s IS NULL OR id<%s)
                     AND (%s IS NULL OR status=%s)
                   ORDER BY id DESC LIMIT %s""",
                (
                    context_id, after_id, after_id,
                    status, status, limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None,
        }

    @router.post("/timetable/generations/{generation_id}/confirm")
    def confirm_timetable(
        generation_id: int, request: TimetableConfirm,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "Haftalik jadvalni e'lon qilish uchun inson tasdig'i kerak.",
        )
        with database() as (_, cur):
            ensure_schema(cur)
            ensure_exception_schema(cur)
            cur.execute(
                """SELECT * FROM school_timetable_generations
                   WHERE id=%s FOR UPDATE""",
                (generation_id,),
            )
            generation = cur.fetchone()
            if not generation:
                raise HTTPException(status_code=404, detail="Jadval qoralamasi topilmadi")
            require_roles(cur, generation["context_id"], user_id, ACADEMIC_ROLES)
            if generation["status"] != "draft" or generation["version"] != request.expected_version:
                raise HTTPException(status_code=409, detail="Jadval qoralamasi o'zgargan/yakunlangan")
            if generation["conflicts"]:
                raise HTTPException(status_code=409, detail="Avval jadval ziddiyatlarini tuzating")
            try:
                generation_options = TimetableGenerate.model_validate(
                    {
                        **dict(generation["constraints"] or {}),
                        "context_id": int(generation["context_id"]),
                    }
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=409,
                    detail="Jadval qoralamasi sozlamasi yaroqsiz; qayta yarating.",
                ) from exc
            schedule_request, workload_map, profile = scheduler_request_from_db(
                cur, generation_options
            )
            clock_map = bell_clock_map(generation_options, profile)
            fresh_result = run_school_scheduler(schedule_request)
            publication_audit = audit_assignments(
                schedule_request, fresh_result.assignments
            )
            if fresh_result.hard_conflicts or publication_audit:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Manbalar o'zgargan yoki jadvalda majburiy ziddiyat bor.",
                        "hard_conflicts": [
                            asdict(item) for item in fresh_result.hard_conflicts
                        ],
                        "audit_conflicts": [
                            asdict(item) for item in publication_audit
                        ],
                    },
                )
            slots = enrich_scheduler_slots(
                cur, int(generation["context_id"]),
                scheduler_slots(
                    fresh_result.assignments, workload_map, clock_map
                ),
            )
            stored_slots = list(generation["candidate_slots"] or [])

            def signature(slot: dict[str, Any]) -> tuple[Any, ...]:
                return (
                    int(slot["section_id"]), int(slot["subject_id"]),
                    int(slot["teacher_user_id"]), int(slot["room_id"])
                    if slot.get("room_id") is not None else None,
                    int(slot["weekday"]), int(slot["shift_no"]),
                    int(slot["period_no"]), str(slot["starts_at"]),
                    str(slot["ends_at"]), str(slot.get("demand_id") or ""),
                    int(slot.get("occurrence_index") or 0),
                )

            if sorted(map(signature, slots)) != sorted(map(signature, stored_slots)):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Sinf, yuklama, o'qituvchi, xona yoki qo'ng'iroq vaqti "
                        "o'zgargan. Jadval qoralamasini qayta yarating."
                    ),
                )
            if not slots:
                raise HTTPException(status_code=422, detail="Bo'sh jadval e'lon qilinmaydi")
            target_section_ids = sorted(
                {int(slot["section_id"]) for slot in slots}
            )
            cur.execute(
                """SELECT x.id,x.slot_id,x.lesson_date
                   FROM school_timetable_exceptions x
                   JOIN school_timetable_slots t
                     ON t.id=x.slot_id AND t.context_id=x.context_id
                   WHERE x.context_id=%s AND x.status='active'
                     AND x.lesson_date>=CURRENT_DATE
                     AND t.status='published'
                     AND t.section_id=ANY(%s)
                   ORDER BY x.lesson_date,x.id LIMIT 20""",
                (generation["context_id"], target_section_ids),
            )
            future_exceptions = cur.fetchall()
            if future_exceptions:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": (
                            "Tanlangan sinflarning kelajakdagi almashtirish/"
                            "qoplovlari bor. Ularni yakunlang yoki bekor qiling."
                        ),
                        "exceptions": future_exceptions,
                    },
                )
            cur.execute(
                """SELECT section_id,teacher_user_id,room_id,weekday,
                          starts_at,ends_at
                   FROM school_timetable_slots
                   WHERE context_id=%s AND status='published'
                     AND NOT(section_id=ANY(%s))""",
                (generation["context_id"], target_section_ids),
            )
            preserved_slots = cur.fetchall()
            merge_conflicts = []
            for slot in slots:
                for existing_slot in preserved_slots:
                    if int(existing_slot["weekday"]) != int(slot["weekday"]):
                        continue
                    if not (
                        str(existing_slot["starts_at"]) < str(slot["ends_at"])
                        and str(existing_slot["ends_at"]) > str(slot["starts_at"])
                    ):
                        continue
                    same_teacher = int(existing_slot["teacher_user_id"]) == int(
                        slot["teacher_user_id"]
                    )
                    same_room = (
                        existing_slot["room_id"] is not None
                        and slot.get("room_id") is not None
                        and int(existing_slot["room_id"])
                        == int(slot["room_id"])
                    )
                    if same_teacher or same_room:
                        merge_conflicts.append(
                            {
                                "section_id": slot["section_id"],
                                "weekday": slot["weekday"],
                                "period_no": slot["period_no"],
                                "teacher_collision": same_teacher,
                                "room_collision": same_room,
                            }
                        )
                        if len(merge_conflicts) >= 20:
                            break
                if len(merge_conflicts) >= 20:
                    break
            if merge_conflicts:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": (
                            "Qisman yaratilgan jadval saqlanayotgan boshqa "
                            "sinflar jadvali bilan to'qnashdi."
                        ),
                        "conflicts": merge_conflicts,
                    },
                )
            combined_daily: dict[tuple[int, int], int] = defaultdict(int)
            for slot in slots:
                combined_daily[
                    (int(slot["teacher_user_id"]), int(slot["weekday"]))
                ] += 1
            for existing_slot in preserved_slots:
                combined_daily[
                    (
                        int(existing_slot["teacher_user_id"]),
                        int(existing_slot["weekday"]),
                    )
                ] += 1
            teacher_ids = sorted({key[0] for key in combined_daily})
            cur.execute(
                """SELECT x.user_id,
                          LEAST(COALESCE(s.max_daily_periods,6),7) max_daily
                   FROM unnest(%s::BIGINT[]) x(user_id)
                   LEFT JOIN school_teacher_settings s
                     ON s.context_id=%s AND s.user_id=x.user_id""",
                (teacher_ids, generation["context_id"]),
            )
            daily_limits = {
                int(row["user_id"]): int(row["max_daily"])
                for row in cur.fetchall()
            }
            over_daily = [
                {
                    "teacher_user_id": teacher_id,
                    "weekday": weekday,
                    "lesson_count": lesson_count,
                    "max_daily": daily_limits.get(teacher_id, 6),
                }
                for (teacher_id, weekday), lesson_count
                in sorted(combined_daily.items())
                if lesson_count > daily_limits.get(teacher_id, 6)
            ]
            if over_daily:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "Qisman jadval birlashganda kunlik limit oshdi.",
                        "teachers": over_daily[:20],
                    },
                )
            cur.execute(
                """UPDATE school_timetable_slots SET status='cancelled'
                   WHERE context_id=%s AND status='published'
                     AND section_id=ANY(%s)""",
                (generation["context_id"], target_section_ids),
            )
            for slot in slots:
                cur.execute(
                    """INSERT INTO school_timetable_slots(
                         context_id,generation_id,section_id,subject_id,
                         teacher_user_id,room_id,weekday,shift_no,period_no,
                         starts_at,ends_at,status
                       ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'published')""",
                    (
                        generation["context_id"], generation_id, slot["section_id"],
                        slot["subject_id"], slot["teacher_user_id"], slot.get("room_id"),
                        slot["weekday"], slot["shift_no"], slot["period_no"],
                        slot["starts_at"], slot["ends_at"],
                    ),
                )
            cur.execute(
                """UPDATE school_timetable_generations
                   SET status='confirmed',confirmed_at=NOW(),version=version+1
                   WHERE id=%s""",
                (generation_id,),
            )
            audit(cur, generation["context_id"], user_id, "timetable.publish",
                  "timetable_generation", generation_id, {"slots": len(slots)})
        return {"status": "published", "slot_count": len(slots)}

    @router.get("/timetable")
    def list_timetable(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=100, ge=1, le=500),
        section_id: int | None = Query(default=None, ge=1),
        teacher_user_id: int | None = Query(default=None, ge=1),
        lesson_date: date | None = Query(default=None),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            ensure_exception_schema(cur)
            require_roles(cur, context_id, user_id, VIEW_ROLES, group_id=None)
            if lesson_date is not None:
                dated_rows = effective_timetable_rows(
                    cur, context_id, lesson_date
                )
                rows = [
                    row for row in dated_rows
                    if int(row["slot_id"]) > (after_id or 0)
                    and (
                        section_id is None
                        or int(row["section_id"]) == section_id
                    )
                    and (
                        teacher_user_id is None
                        or int(row["teacher_user_id"]) == teacher_user_id
                    )
                ]
                page = rows[:limit]
                return {
                    "items": page,
                    "lesson_date": lesson_date,
                    "effective": True,
                    "next_cursor": (
                        int(page[-1]["slot_id"])
                        if len(rows) > limit and page else None
                    ),
                    "truncated": len(rows) > limit,
                }
            cur.execute(
                """SELECT t.id,t.section_id,t.subject_id,t.teacher_user_id,
                          t.teacher_user_id original_teacher_user_id,t.room_id,
                          t.weekday,t.shift_no,t.period_no,t.starts_at,t.ends_at,
                          s.grade_no,s.section_name,sub.name subject_name,
                          u.full_name teacher_name,r.name room_name,
                          NULL::DATE lesson_date,NULL::BIGINT exception_id,
                          NULL::TEXT exception_kind,
                          NULL::TEXT exception_reason,
                          'recurring_template'::TEXT source_type
                   FROM school_timetable_slots t
                   JOIN school_sections s ON s.id=t.section_id AND s.context_id=t.context_id
                   JOIN school_subjects sub ON sub.id=t.subject_id AND sub.context_id=t.context_id
                   JOIN users u ON u.user_id=t.teacher_user_id
                   LEFT JOIN school_rooms r ON r.id=t.room_id AND r.context_id=t.context_id
                   WHERE t.context_id=%s AND t.status='published' AND t.id>%s
                     AND (%s IS NULL OR t.section_id=%s)
                     AND (%s IS NULL OR t.teacher_user_id=%s)
                   ORDER BY t.id LIMIT %s""",
                (
                    context_id, after_id or 0,
                    section_id, section_id,
                    teacher_user_id, teacher_user_id, limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {"items": rows[:limit],
                "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.get("/timetable/effective")
    def get_effective_timetable(
        context_id: int = Query(ge=1),
        lesson_date: date = Query(),
        section_id: int | None = Query(default=None, ge=1),
        teacher_user_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=500, ge=1, le=2000),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            ensure_exception_schema(cur)
            require_roles(cur, context_id, user_id, VIEW_ROLES)
            starts_on, ends_on = school_calendar_bounds(cur, context_id)
            rows = effective_timetable_rows(cur, context_id, lesson_date)
            rows = [
                row for row in rows
                if (
                    section_id is None
                    or int(row["section_id"]) == section_id
                )
                and (
                    teacher_user_id is None
                    or int(row["teacher_user_id"]) == teacher_user_id
                )
            ]
        return {
            "lesson_date": lesson_date,
            "calendar": {
                "starts_on": starts_on,
                "ends_on": ends_on,
            },
            "items": rows[:limit],
            "count": len(rows),
            "truncated": len(rows) > limit,
        }

    @router.post("/timetable/substitutions")
    def substitute_teacher(
        request: SubstitutionCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        require_human(request.confirmation, "O'qituvchini almashtirish uchun inson tasdig'i kerak.")
        with database() as (_, cur):
            ensure_schema(cur)
            ensure_exception_schema(cur)
            require_roles(cur, request.context_id, user_id, ACADEMIC_ROLES)
            require_calendar_dates(
                cur, request.context_id, [request.lesson_date]
            )
            lock_context_dates(
                cur, request.context_id, [request.lesson_date]
            )
            cur.execute(
                """SELECT * FROM school_timetable_exceptions
                   WHERE context_id=%s AND idempotency_key=%s""",
                (request.context_id, request.idempotency_key),
            )
            replay = cur.fetchone()
            if replay:
                if (
                    int(replay["slot_id"]) != request.slot_id
                    or replay["lesson_date"] != request.lesson_date
                    or int(replay["replacement_teacher_user_id"] or 0)
                    != request.new_teacher_user_id
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency kaliti boshqa almashtirishda ishlatilgan.",
                    )
                return {
                    "substitution": replay,
                    "idempotent_replay": True,
                }
            cur.execute(
                """SELECT t.*,sec.grade_no,sec.group_id
                   FROM school_timetable_slots t
                   JOIN school_sections sec
                     ON sec.id=t.section_id AND sec.context_id=t.context_id
                   WHERE t.id=%s AND t.context_id=%s
                     AND t.status='published' FOR UPDATE""",
                (request.slot_id, request.context_id),
            )
            slot = cur.fetchone()
            if not slot:
                raise HTTPException(status_code=404, detail="Dars jadvali topilmadi")
            if request.lesson_date.isoweekday() != int(slot["weekday"]):
                raise HTTPException(
                    status_code=422,
                    detail="Almashtirish sanasi darsning hafta kuniga mos emas.",
                )
            if int(slot["teacher_user_id"]) == request.new_teacher_user_id:
                raise HTTPException(
                    status_code=422,
                    detail="Yangi o'qituvchi asl o'qituvchidan farq qilsin.",
                )
            cur.execute(
                """SELECT work_days FROM school_profiles WHERE context_id=%s""",
                (request.context_id,),
            )
            profile = cur.fetchone()
            if (
                not profile
                or request.lesson_date.isoweekday()
                not in set(profile["work_days"] or [])
            ):
                raise HTTPException(
                    status_code=409, detail="Bu sana maktabning ish kuni emas."
                )
            cur.execute(
                """SELECT 1 FROM school_calendar_events
                   WHERE context_id=%s AND event_type='holiday'
                     AND status='published'
                     AND (starts_at AT TIME ZONE 'Asia/Tashkent')::date<=%s
                     AND (ends_at AT TIME ZONE 'Asia/Tashkent')::date>%s
                   LIMIT 1""",
                (
                    request.context_id,
                    request.lesson_date,
                    request.lesson_date,
                ),
            )
            if cur.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="Bayram yoki dam olish kuniga almashtirish qo'yilmaydi.",
                )
            cur.execute(
                """SELECT 1 FROM school_role_assignments
                   WHERE context_id=%s AND user_id=%s AND status='active'
                     AND role_key=ANY(%s)""",
                (request.context_id, request.new_teacher_user_id,
                 ["teacher", "homeroom_teacher"]),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=422, detail="Yangi o'qituvchi shu maktabda faol emas")
            cur.execute(
                """SELECT 1 FROM school_teacher_subjects ts
                   JOIN school_sections sec ON sec.id=%s
                    AND sec.context_id=ts.context_id
                   WHERE ts.context_id=%s AND ts.user_id=%s
                     AND ts.subject_id=%s
                     AND sec.grade_no BETWEEN ts.grade_from AND ts.grade_to""",
                (
                    slot["section_id"], request.context_id,
                    request.new_teacher_user_id, slot["subject_id"],
                ),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=422, detail="Yangi o'qituvchi bu fanga biriktirilmagan"
                )
            cur.execute(
                """SELECT COALESCE(method_day,0) method_day,
                          LEAST(COALESCE(max_daily_periods,6),7) max_daily,
                          COALESCE(preferences,'{}'::jsonb) preferences
                   FROM school_teacher_settings
                   WHERE context_id=%s AND user_id=%s""",
                (request.context_id, request.new_teacher_user_id),
            )
            teacher_settings = cur.fetchone() or {
                "method_day": 0, "max_daily": 6, "preferences": {}
            }
            if teacher_settings["method_day"] == slot["weekday"]:
                raise HTTPException(status_code=409, detail="Bu kun o'qituvchining metod kuni")
            allowed_shifts = {
                int(value)
                for value in dict(
                    teacher_settings["preferences"] or {}
                ).get("allowed_shifts", [1, 2])
                if str(value) in {"1", "2"}
            }
            if int(slot["shift_no"]) not in allowed_shifts:
                raise HTTPException(
                    status_code=409,
                    detail="O'qituvchi bu smenada ishlashga biriktirilmagan.",
                )
            cur.execute(
                """SELECT
                     count(*) FILTER(WHERE availability='available') available_rows,
                     bool_or(
                       availability='available'
                       AND weekday=%s AND shift_no=%s
                       AND %s BETWEEN period_from AND period_to
                     ) explicitly_available,
                     bool_or(
                       availability='unavailable'
                       AND weekday=%s AND shift_no=%s
                       AND %s BETWEEN period_from AND period_to
                     ) explicitly_unavailable
                   FROM school_teacher_availability
                   WHERE context_id=%s AND user_id=%s""",
                (
                    slot["weekday"], slot["shift_no"], slot["period_no"],
                    slot["weekday"], slot["shift_no"], slot["period_no"],
                    request.context_id, request.new_teacher_user_id,
                ),
            )
            availability = cur.fetchone()
            if availability and (
                availability["explicitly_unavailable"]
                or (
                    int(availability["available_rows"] or 0) > 0
                    and not availability["explicitly_available"]
                )
            ):
                raise HTTPException(status_code=409, detail="O'qituvchi bu vaqtda mavjud emas")
            effective_rows = effective_timetable_rows(
                cur, request.context_id, request.lesson_date
            )
            new_teacher_lessons = [
                row for row in effective_rows
                if int(row["teacher_user_id"])
                == request.new_teacher_user_id
                and not (
                    int(row["slot_id"]) == request.slot_id
                    and row["source_type"] in {"recurring", "substitution"}
                )
            ]
            if len(new_teacher_lessons) >= teacher_settings["max_daily"]:
                raise HTTPException(status_code=409, detail="O'qituvchining kunlik limiti to'lgan")
            if any(
                row.get("starts_at") is not None
                and row.get("ends_at") is not None
                and row["starts_at"] < slot["ends_at"]
                and row["ends_at"] > slot["starts_at"]
                for row in new_teacher_lessons
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Yangi o'qituvchida shu haqiqiy vaqtda boshqa dars bor",
                )
            cur.execute(
                """INSERT INTO school_timetable_exceptions(
                     context_id,slot_id,lesson_date,exception_kind,
                     original_teacher_user_id,replacement_teacher_user_id,
                     reason,idempotency_key,created_by_user_id,metadata
                   ) VALUES(
                     %s,%s,%s,'substitution',%s,%s,%s,%s,%s,%s::jsonb
                   )
                   ON CONFLICT(context_id,slot_id,lesson_date)
                     WHERE status='active' DO NOTHING
                   RETURNING *""",
                (
                    request.context_id, request.slot_id, request.lesson_date,
                    slot["teacher_user_id"], request.new_teacher_user_id,
                    request.reason, request.idempotency_key, user_id,
                    json.dumps(
                        {
                            "section_id": slot["section_id"],
                            "subject_id": slot["subject_id"],
                            "group_id": slot["group_id"],
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
            changed = cur.fetchone()
            if not changed:
                raise HTTPException(
                    status_code=409,
                    detail="Bu dars sanasi uchun faol istisno allaqachon bor.",
                )
            audit(cur, request.context_id, user_id, "timetable.substitute",
                  "timetable_exception", changed["id"],
                  {
                      "slot_id": request.slot_id,
                      "lesson_date": request.lesson_date,
                      "new_teacher_user_id": request.new_teacher_user_id,
                  })
        return {"substitution": changed, "idempotent_replay": False}

    @router.get("/timetable/exceptions")
    def list_timetable_exceptions(
        context_id: int = Query(ge=1),
        lesson_date: date | None = Query(default=None),
        status: Literal["active", "revoked"] | None = None,
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=100, ge=1, le=500),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            ensure_exception_schema(cur)
            require_roles(cur, context_id, user_id, ACADEMIC_ROLES)
            cur.execute(
                """SELECT x.id,x.context_id,x.slot_id,x.lesson_date,
                          x.exception_kind,x.original_teacher_user_id,
                          x.replacement_teacher_user_id,x.reason,x.target_date,
                          x.target_slot_id,x.target_shift_no,x.target_period_no,
                          x.makeup_event_id,x.sequence_no,x.status,
                          x.created_by_user_id,x.revoked_by_user_id,
                          x.created_at,x.updated_at,x.revoked_at,
                          sec.group_id,sec.grade_no,sec.section_name,
                          sub.name subject_name,
                          ou.full_name original_teacher_name,
                          ru.full_name replacement_teacher_name
                   FROM school_timetable_exceptions x
                   JOIN school_timetable_slots t
                     ON t.id=x.slot_id AND t.context_id=x.context_id
                   JOIN school_sections sec
                     ON sec.id=t.section_id AND sec.context_id=t.context_id
                   JOIN school_subjects sub
                     ON sub.id=t.subject_id AND sub.context_id=t.context_id
                   JOIN users ou ON ou.user_id=x.original_teacher_user_id
                   LEFT JOIN users ru
                     ON ru.user_id=x.replacement_teacher_user_id
                   WHERE x.context_id=%s AND x.id>%s
                     AND (%s IS NULL OR x.lesson_date=%s)
                     AND (%s IS NULL OR x.status=%s)
                   ORDER BY x.id LIMIT %s""",
                (
                    context_id, after_id or 0,
                    lesson_date, lesson_date, status, status, limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": (
                rows[limit - 1]["id"] if len(rows) > limit else None
            ),
        }

    @router.post("/timetable/exceptions/{exception_id}/revoke")
    def revoke_timetable_exception(
        exception_id: int,
        request: TimetableExceptionRevoke,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "Jadval istisnosini bekor qilish uchun inson tasdig'i kerak.",
        )
        with database() as (_, cur):
            ensure_schema(cur)
            ensure_exception_schema(cur)
            require_roles(cur, request.context_id, user_id, ACADEMIC_ROLES)
            cur.execute(
                """SELECT lesson_date FROM school_timetable_exceptions
                   WHERE id=%s AND context_id=%s""",
                (exception_id, request.context_id),
            )
            occurrence = cur.fetchone()
            if not occurrence:
                raise HTTPException(
                    status_code=404, detail="Jadval istisnosi topilmadi."
                )
            lock_context_dates(
                cur, request.context_id, [occurrence["lesson_date"]]
            )
            cur.execute(
                """SELECT id FROM school_timetable_exceptions
                   WHERE context_id=%s AND revocation_idempotency_key=%s""",
                (request.context_id, request.idempotency_key),
            )
            reused_key = cur.fetchone()
            if reused_key and int(reused_key["id"]) != exception_id:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Revocation idempotency kaliti boshqa istisnoda "
                        "ishlatilgan."
                    ),
                )
            cur.execute(
                """SELECT * FROM school_timetable_exceptions
                   WHERE id=%s AND context_id=%s FOR UPDATE""",
                (exception_id, request.context_id),
            )
            exception = cur.fetchone()
            metadata = dict(exception["metadata"] or {})
            if exception["status"] == "revoked":
                if (
                    exception["revocation_idempotency_key"]
                    == request.idempotency_key
                ):
                    return {
                        "exception": exception,
                        "idempotent_replay": True,
                    }
                raise HTTPException(
                    status_code=409,
                    detail="Jadval istisnosi avval boshqa amal bilan bekor qilingan.",
                )
            metadata.update(
                {
                    "revocation_reason": request.reason,
                }
            )
            cur.execute(
                """UPDATE school_timetable_exceptions
                   SET status='revoked',revoked_by_user_id=%s,
                       revoked_at=NOW(),updated_at=NOW(),
                       revocation_idempotency_key=%s,metadata=%s::jsonb
                   WHERE id=%s AND context_id=%s AND status='active'
                   RETURNING *""",
                (
                    user_id, request.idempotency_key,
                    json.dumps(metadata, ensure_ascii=False),
                    exception_id, request.context_id,
                ),
            )
            revoked = cur.fetchone()
            if not revoked:
                raise HTTPException(
                    status_code=409, detail="Jadval istisnosi o'zgargan."
                )
            if revoked["makeup_event_id"] is not None:
                cur.execute(
                    """UPDATE school_calendar_events
                       SET status='cancelled',updated_at=NOW(),
                           metadata=metadata||%s::jsonb
                       WHERE id=%s AND context_id=%s AND status='published'""",
                    (
                        json.dumps(
                            {
                                "exception_revoked": True,
                                "revoked_by": user_id,
                                "revocation_reason": request.reason,
                            },
                            ensure_ascii=False,
                        ),
                        revoked["makeup_event_id"], request.context_id,
                    ),
                )
            audit(
                cur, request.context_id, user_id,
                "timetable.exception.revoke", "timetable_exception",
                exception_id,
                {
                    "lesson_date": revoked["lesson_date"],
                    "exception_kind": revoked["exception_kind"],
                    "reason": request.reason,
                },
            )
        return {"exception": revoked, "idempotent_replay": False}

    @router.post("/students")
    def assign_student(
        request: StudentAssign, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "O'quvchini sinfga biriktirish uchun inson tasdig'i kerak.",
        )
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, MANAGER_ROLES)
            cur.execute(
                """SELECT group_id FROM school_sections
                   WHERE id=%s AND context_id=%s AND active=TRUE""",
                (request.section_id, request.context_id),
            )
            section = cur.fetchone()
            if not section:
                raise HTTPException(status_code=404, detail="Sinf topilmadi")
            cur.execute("SELECT 1 FROM users WHERE user_id=%s", (request.user_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="O'quvchi hisobi topilmadi")
            cur.execute(
                """UPDATE school_role_assignments SET status='ended',ends_at=NOW(),
                     updated_at=NOW()
                   WHERE context_id=%s AND user_id=%s AND role_key='student'
                     AND status='active' AND group_id<>%s""",
                (request.context_id, request.user_id, section["group_id"]),
            )
            assignment_id = upsert_school_role(
                cur, context_id=request.context_id, group_id=section["group_id"],
                user_id=request.user_id, role_key="student", status="active",
                approved_by=user_id,
            )
            audit(
                cur, request.context_id, user_id, "student.assign",
                "role_assignment", assignment_id,
                {"student_user_id": request.user_id, "section_id": request.section_id},
            )
        return {"assignment_id": assignment_id, "status": "active"}

    @router.post("/students/parent-links")
    def link_parent_student(
        request: ParentStudentLink, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        require_human(
            request.confirmation,
            "Ota-ona va o'quvchini bog'lash uchun inson tasdig'i kerak.",
        )
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, MANAGER_ROLES)
            cur.execute(
                """SELECT 1 FROM school_role_assignments
                   WHERE context_id=%s AND user_id=%s AND role_key='student'
                     AND status='active'""",
                (request.context_id, request.student_user_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=422, detail="O'quvchi maktabda faol emas")
            cur.execute(
                """SELECT 1 FROM school_role_assignments
                   WHERE context_id=%s AND user_id=%s AND role_key='parent'
                     AND status='active'""",
                (request.context_id, request.parent_user_id),
            )
            if not cur.fetchone():
                upsert_school_role(
                    cur, context_id=request.context_id,
                    user_id=request.parent_user_id, role_key="parent",
                    status="active", approved_by=user_id,
                )
            cur.execute(
                """INSERT INTO school_parent_students(
                     context_id,parent_user_id,student_user_id,status,approved_by_user_id
                   ) VALUES(%s,%s,%s,'active',%s)
                   ON CONFLICT(context_id,parent_user_id,student_user_id)
                   DO UPDATE SET status='active',approved_by_user_id=EXCLUDED.approved_by_user_id,
                     updated_at=NOW()""",
                (
                    request.context_id, request.parent_user_id,
                    request.student_user_id, user_id,
                ),
            )
        return {"status": "active"}

    @router.get("/students")
    def list_students(
        context_id: int = Query(ge=1),
        section_id: int | None = Query(default=None, ge=1),
        attendance_date: date | None = None,
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=100, ge=1, le=300),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            admin = system_admin(cur, user_id)
            roles = {"system_admin"} if admin else active_roles(cur, context_id, user_id)
            manager = bool(roles & MANAGER_ROLES) or admin
            teacher = bool(roles & TEACHING_ROLES)
            parent = "parent" in roles
            student = "student" in roles
            teacher_scope = False
            if not (manager or teacher or parent or student):
                raise HTTPException(status_code=403, detail="O'quvchilar ro'yxatiga ruxsat yo'q")
            group_id = None
            if section_id:
                cur.execute(
                    "SELECT group_id FROM school_sections WHERE id=%s AND context_id=%s",
                    (section_id, context_id),
                )
                section = cur.fetchone()
                if not section:
                    raise HTTPException(status_code=404, detail="Sinf topilmadi")
                group_id = section["group_id"]
                if teacher and not manager:
                    require_roles(
                        cur, context_id, user_id, TEACHING_ROLES,
                        group_id=group_id,
                    )
                    teacher_scope = teacher_can_access_section(
                        cur, context_id, user_id, section_id
                    )
                    if not teacher_scope and not (parent or student):
                        raise HTTPException(
                            status_code=403,
                            detail="Siz bu sinfga biriktirilmagansiz",
                        )
            if not section_id and not manager and not parent and not student:
                raise HTTPException(status_code=403, detail="O'qituvchi sinfni tanlashi kerak")
            cur.execute(
                """SELECT r.id role_assignment_id,r.user_id id,u.full_name,
                          s.id section_id,s.grade_no,s.section_name,s.shift_no,
                          a.status attendance_status
                   FROM school_role_assignments r
                   JOIN users u ON u.user_id=r.user_id
                   JOIN school_sections s ON s.group_id=r.group_id
                    AND s.context_id=r.context_id AND s.active=TRUE
                   LEFT JOIN school_attendance a ON a.context_id=r.context_id
                    AND a.section_id=s.id AND a.student_user_id=r.user_id
                    AND a.attendance_date=%s AND a.period_no IS NULL
                   WHERE r.context_id=%s AND r.role_key='student' AND r.status='active'
                     AND r.id>%s AND (%s IS NULL OR s.id=%s)
                     AND (
                       %s OR
                       (%s AND EXISTS(
                         SELECT 1 FROM school_parent_students ps
                         WHERE ps.context_id=r.context_id
                           AND ps.parent_user_id=%s AND ps.student_user_id=r.user_id
                           AND ps.status='active'
                       )) OR
                       (%s AND r.user_id=%s) OR
                       %s
                     )
                   ORDER BY r.id LIMIT %s""",
                (
                    attendance_date, context_id, after_id or 0,
                    section_id, section_id, manager, parent, user_id,
                    student, user_id, teacher_scope, limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {
            "items": rows[:limit],
            "next_cursor": (
                rows[limit - 1]["role_assignment_id"] if len(rows) > limit else None
            ),
        }

    @router.post("/attendance")
    def mark_attendance(
        request: AttendanceMark, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                "SELECT group_id FROM school_sections WHERE id=%s AND context_id=%s AND active=TRUE",
                (request.section_id, request.context_id),
            )
            section = cur.fetchone()
            if not section:
                raise HTTPException(status_code=404, detail="Sinf topilmadi")
            roles = require_roles(
                cur, request.context_id, user_id, ATTENDANCE_ROLES,
                group_id=section["group_id"],
            )
            if (
                roles & {"teacher", "homeroom_teacher"}
                and not roles & MANAGER_ROLES
                and not teacher_can_access_section(
                    cur, request.context_id, user_id, request.section_id
                )
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Siz bu sinfga fan yoki sinf rahbari sifatida biriktirilmagansiz",
                )
            cur.execute(
                """SELECT 1 FROM school_role_assignments
                   WHERE context_id=%s AND group_id=%s AND user_id=%s
                     AND role_key='student' AND status='active'""",
                (request.context_id, section["group_id"], request.student_user_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=422, detail="O'quvchi bu sinfga biriktirilmagan")
            cur.execute(
                """INSERT INTO school_attendance(
                     context_id,section_id,student_user_id,attendance_date,
                     period_no,status,note,marked_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(
                     context_id,section_id,student_user_id,attendance_date,
                     (COALESCE(period_no,0))
                   ) DO UPDATE SET status=EXCLUDED.status,note=EXCLUDED.note,
                     marked_by_user_id=EXCLUDED.marked_by_user_id,updated_at=NOW()
                   RETURNING id,status,updated_at""",
                (
                    request.context_id, request.section_id, request.student_user_id,
                    request.attendance_date, request.period_no, request.status,
                    request.note, user_id,
                ),
            )
            row = cur.fetchone()
        return {"attendance": row}

    @router.get("/attendance")
    def list_attendance(
        context_id: int = Query(ge=1), section_id: int | None = Query(default=None, ge=1),
        student_user_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=100, ge=1, le=500),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            admin = system_admin(cur, user_id)
            roles = {"system_admin"} if admin else active_roles(cur, context_id, user_id)
            manager = admin or bool(roles & MANAGER_ROLES)
            if "student" in roles and not manager:
                if student_user_id not in (None, user_id):
                    raise HTTPException(status_code=403, detail="Faqat o'z davomatingiz ko'rinadi")
                student_user_id = user_id
            elif "parent" in roles and not manager:
                if student_user_id is None:
                    raise HTTPException(status_code=422, detail="Bog'langan farzandni tanlang")
                cur.execute(
                    """SELECT 1 FROM school_parent_students
                       WHERE context_id=%s AND parent_user_id=%s
                         AND student_user_id=%s AND status='active'""",
                    (context_id, user_id, student_user_id),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=403, detail="Bu o'quvchi sizga bog'lanmagan")
            elif not manager:
                if not roles.intersection(ATTENDANCE_ROLES) or section_id is None:
                    raise HTTPException(
                        status_code=403,
                        detail="Xodim faqat biriktirilgan sinf davomatini ko'radi",
                    )
                cur.execute(
                    "SELECT group_id FROM school_sections WHERE id=%s AND context_id=%s",
                    (section_id, context_id),
                )
                section = cur.fetchone()
                if not section:
                    raise HTTPException(status_code=404, detail="Sinf topilmadi")
                require_roles(
                    cur, context_id, user_id, ATTENDANCE_ROLES,
                    group_id=section["group_id"],
                )
                if (
                    roles & {"teacher", "homeroom_teacher"}
                    and not teacher_can_access_section(
                        cur, context_id, user_id, section_id
                    )
                ):
                    raise HTTPException(
                        status_code=403,
                        detail="Siz bu sinfga biriktirilmagansiz",
                    )
            cur.execute(
                """SELECT a.id,a.section_id,a.student_user_id,u.full_name,
                          a.attendance_date,a.period_no,a.status,a.note,a.updated_at
                   FROM school_attendance a JOIN users u ON u.user_id=a.student_user_id
                   WHERE a.context_id=%s AND a.id>%s
                     AND (%s IS NULL OR a.section_id=%s)
                     AND (%s IS NULL OR a.student_user_id=%s)
                   ORDER BY a.id LIMIT %s""",
                (
                    context_id, after_id or 0, section_id, section_id,
                    student_user_id, student_user_id, limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {"items": rows[:limit],
                "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/grade-entries")
    def create_grade_entry(
        request: GradeCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        if request.score > request.max_score:
            raise HTTPException(status_code=422, detail="Baho maksimal balldan oshmaydi")
        graded_at = request.graded_at or datetime.now(timezone.utc)
        if graded_at.tzinfo is None:
            raise HTTPException(status_code=422, detail="Baho vaqti vaqt zonasi bilan yuborilsin")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                "SELECT group_id FROM school_sections WHERE id=%s AND context_id=%s",
                (request.section_id, request.context_id),
            )
            section = cur.fetchone()
            if not section:
                raise HTTPException(status_code=404, detail="Sinf topilmadi")
            require_roles(cur, request.context_id, user_id, TEACHING_ROLES,
                          group_id=section["group_id"])
            cur.execute(
                "SELECT 1 FROM school_subjects WHERE id=%s AND context_id=%s AND active=TRUE",
                (request.subject_id, request.context_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Fan topilmadi")
            cur.execute(
                """SELECT 1 FROM school_role_assignments
                   WHERE context_id=%s AND group_id=%s AND user_id=%s
                     AND role_key='student' AND status='active'""",
                (
                    request.context_id, section["group_id"],
                    request.student_user_id,
                ),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=422, detail="O'quvchi bu sinfda faol emas"
                )
            if not system_admin(cur, user_id):
                cur.execute(
                    """SELECT 1 FROM school_workloads
                       WHERE context_id=%s AND section_id=%s AND subject_id=%s
                         AND teacher_user_id=%s AND active=TRUE""",
                    (
                        request.context_id, request.section_id,
                        request.subject_id, user_id,
                    ),
                )
                if not cur.fetchone():
                    raise HTTPException(
                        status_code=403,
                        detail="Bu fan va sinf bahosini faqat biriktirilgan o'qituvchi yozadi",
                    )
            cur.execute(
                """INSERT INTO school_grade_entries(
                     context_id,section_id,subject_id,student_user_id,teacher_user_id,
                     grade_type,score,max_score,graded_at,note,idempotency_key
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(context_id,idempotency_key)
                     WHERE idempotency_key IS NOT NULL DO NOTHING
                   RETURNING id,score,max_score,graded_at""",
                (
                    request.context_id, request.section_id, request.subject_id,
                    request.student_user_id, user_id, request.grade_type,
                    request.score, request.max_score, graded_at, request.note,
                    request.idempotency_key,
                ),
            )
            grade = cur.fetchone()
            if grade is None and request.idempotency_key:
                cur.execute(
                    """SELECT id,section_id,subject_id,student_user_id,teacher_user_id,
                              grade_type,score,max_score,graded_at
                       FROM school_grade_entries
                       WHERE context_id=%s AND idempotency_key=%s""",
                    (request.context_id, request.idempotency_key),
                )
                grade = cur.fetchone()
                if (
                    not grade
                    or int(grade["section_id"]) != request.section_id
                    or int(grade["subject_id"]) != request.subject_id
                    or int(grade["student_user_id"]) != request.student_user_id
                    or int(grade["teacher_user_id"]) != user_id
                    or grade["grade_type"] != request.grade_type
                    or grade["score"] != request.score
                    or grade["max_score"] != request.max_score
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency kaliti boshqa baho so'rovida ishlatilgan",
                    )
        return {"grade": grade}

    @router.get("/grade-entries")
    def list_grade_entries(
        context_id: int = Query(ge=1), student_user_id: int | None = Query(default=None, ge=1),
        section_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=100, ge=1, le=500),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            admin = system_admin(cur, user_id)
            roles = {"system_admin"} if admin else active_roles(cur, context_id, user_id)
            manager = admin or bool(roles & MANAGER_ROLES)
            teacher_only = bool(roles & TEACHING_ROLES) and not manager
            if "student" in roles and not manager:
                if student_user_id not in (None, user_id):
                    raise HTTPException(status_code=403, detail="Faqat o'z baholaringiz ko'rinadi")
                student_user_id = user_id
                teacher_only = False
            elif "parent" in roles and not manager:
                teacher_only = False
                if student_user_id is None:
                    raise HTTPException(status_code=422, detail="Bog'langan farzandni tanlang")
                cur.execute(
                    """SELECT 1 FROM school_parent_students
                       WHERE context_id=%s AND parent_user_id=%s
                         AND student_user_id=%s AND status='active'""",
                    (context_id, user_id, student_user_id),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=403, detail="Bu o'quvchi sizga bog'lanmagan")
            elif not manager and not teacher_only:
                raise HTTPException(status_code=403, detail="Baholarni ko'rish vakolati yo'q")
            cur.execute(
                """SELECT g.id,g.section_id,g.subject_id,g.student_user_id,g.teacher_user_id,
                          g.grade_type,g.score,g.max_score,g.graded_at,g.note,
                          s.name subject_name,u.full_name student_name
                   FROM school_grade_entries g
                   JOIN school_subjects s ON s.id=g.subject_id AND s.context_id=g.context_id
                   JOIN users u ON u.user_id=g.student_user_id
                   WHERE g.context_id=%s AND g.id>%s
                     AND (%s IS NULL OR g.student_user_id=%s)
                     AND (%s IS NULL OR g.section_id=%s)
                     AND (NOT %s OR g.teacher_user_id=%s)
                   ORDER BY g.id LIMIT %s""",
                (
                    context_id, after_id or 0, student_user_id,
                    student_user_id, section_id, section_id,
                    teacher_only, user_id, limit + 1,
                ),
            )
            rows = cur.fetchall()
        return {"items": rows[:limit],
                "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/billing/plans")
    def create_billing_plan(
        request: BillingPlanCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        require_human(request.confirmation, "To'lov rejasini yaratish uchun inson tasdig'i kerak.")
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, FINANCE_ROLES)
            ensure_private_billing(cur, request.context_id)
            cur.execute(
                """INSERT INTO school_billing_plans(
                     context_id,name,amount,billing_day,created_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s)
                   RETURNING id,name,amount,billing_day,active""",
                (
                    request.context_id, request.name.strip(), request.amount,
                    request.billing_day, user_id,
                ),
            )
            plan = cur.fetchone()
            audit(cur, request.context_id, user_id, "billing.plan.create",
                  "billing_plan", plan["id"])
        return {"plan": plan}

    @router.get("/billing/plans")
    def list_billing_plans(
        context_id: int = Query(ge=1), user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, FINANCE_ROLES)
            ensure_private_billing(cur, context_id)
            cur.execute(
                """SELECT id,name,amount,billing_day,active FROM school_billing_plans
                   WHERE context_id=%s ORDER BY id""",
                (context_id,),
            )
            rows = cur.fetchall()
        return {"items": rows}

    @router.post("/billing/invoices")
    def create_invoice(
        request: InvoiceCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Hisob yaratish uchun inson tasdig'i kerak.")
        period_month = request.period_month.replace(day=1)
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, FINANCE_ROLES)
            ensure_private_billing(cur, request.context_id)
            cur.execute(
                """SELECT amount FROM school_billing_plans
                   WHERE id=%s AND context_id=%s AND active=TRUE""",
                (request.plan_id, request.context_id),
            )
            plan = cur.fetchone()
            if not plan:
                raise HTTPException(status_code=404, detail="To'lov rejasi topilmadi")
            cur.execute(
                """SELECT 1 FROM school_role_assignments
                   WHERE context_id=%s AND user_id=%s AND role_key='student'
                     AND status='active'""",
                (request.context_id, request.student_user_id),
            )
            if not cur.fetchone():
                raise HTTPException(
                    status_code=422, detail="O'quvchi bu maktabda faol emas"
                )
            cur.execute(
                """INSERT INTO school_invoices(
                     context_id,plan_id,student_user_id,period_month,due_date,amount
                   ) VALUES(%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(context_id,plan_id,student_user_id,period_month)
                   DO UPDATE SET due_date=EXCLUDED.due_date
                   RETURNING id,amount,paid_amount,status,due_date""",
                (
                    request.context_id, request.plan_id, request.student_user_id,
                    period_month, request.due_date, plan["amount"],
                ),
            )
            invoice = cur.fetchone()
        return {"invoice": invoice}

    @router.get("/billing/invoices")
    def list_invoices(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=100, ge=1, le=300),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            require_roles(cur, context_id, user_id, FINANCE_ROLES)
            ensure_private_billing(cur, context_id)
            cur.execute(
                """SELECT i.id,i.plan_id,i.student_user_id,u.full_name,i.period_month,
                          i.due_date,i.amount,i.paid_amount,i.status
                   FROM school_invoices i JOIN users u ON u.user_id=i.student_user_id
                   WHERE i.context_id=%s AND i.id>%s ORDER BY i.id LIMIT %s""",
                (context_id, after_id or 0, limit + 1),
            )
            rows = cur.fetchall()
        return {"items": rows[:limit],
                "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/billing/payments")
    def create_payment(
        request: PaymentCreate, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        require_human(request.confirmation, "To'lovni qabul qilish uchun inson tasdig'i kerak.")
        with database() as (_, cur):
            ensure_schema(cur)
            require_roles(cur, request.context_id, user_id, FINANCE_ROLES)
            ensure_private_billing(cur, request.context_id)
            cur.execute(
                """SELECT * FROM school_invoices
                   WHERE id=%s AND context_id=%s FOR UPDATE""",
                (request.invoice_id, request.context_id),
            )
            invoice = cur.fetchone()
            if not invoice or invoice["status"] == "cancelled":
                raise HTTPException(status_code=404, detail="Faol hisob topilmadi")
            cur.execute(
                """SELECT id,invoice_id,amount,payment_method,reference,paid_at
                   FROM school_payments
                   WHERE context_id=%s AND idempotency_key=%s""",
                (request.context_id, request.idempotency_key),
            )
            existing_payment = cur.fetchone()
            if existing_payment:
                if (
                    int(existing_payment["invoice_id"]) != request.invoice_id
                    or existing_payment["amount"] != request.amount
                    or existing_payment["payment_method"] != request.payment_method
                    or (existing_payment["reference"] or None)
                    != (request.reference or None)
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency kaliti boshqa to'lov so'rovida ishlatilgan",
                    )
                return {
                    "payment": existing_payment,
                    "idempotent_replay": True,
                }
            remaining = invoice["amount"] - invoice["paid_amount"]
            if request.amount > remaining:
                raise HTTPException(status_code=422, detail="To'lov qolgan summadan oshmaydi")
            cur.execute(
                """INSERT INTO school_payments(
                     context_id,invoice_id,amount,payment_method,idempotency_key,
                     received_by_user_id,reference
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(context_id,idempotency_key) DO NOTHING
                   RETURNING id,amount,paid_at""",
                (
                    request.context_id, request.invoice_id, request.amount,
                    request.payment_method, request.idempotency_key, user_id,
                    request.reference,
                ),
            )
            payment = cur.fetchone()
            if payment is None:
                cur.execute(
                    """SELECT id,invoice_id,amount,payment_method,reference,paid_at
                       FROM school_payments
                       WHERE context_id=%s AND idempotency_key=%s""",
                    (request.context_id, request.idempotency_key),
                )
                payment = cur.fetchone()
                if (
                    not payment
                    or int(payment["invoice_id"]) != request.invoice_id
                    or payment["amount"] != request.amount
                    or payment["payment_method"] != request.payment_method
                    or (payment["reference"] or None) != (request.reference or None)
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency kaliti boshqa to'lov so'rovida ishlatilgan",
                    )
                return {"payment": payment, "idempotent_replay": True}
            new_paid = invoice["paid_amount"] + request.amount
            cur.execute(
                """UPDATE school_invoices SET paid_amount=%s,
                     status=CASE WHEN %s>=amount THEN 'paid' ELSE 'partial' END
                   WHERE id=%s""",
                (new_paid, new_paid, request.invoice_id),
            )
            audit(cur, request.context_id, user_id, "billing.payment.receive",
                  "payment", payment["id"], {"invoice_id": request.invoice_id})
        return {"payment": payment, "idempotent_replay": False}

    @router.post("/assistant/sessions")
    def start_assistant(
        request: AssistantStart, user_id: int = Depends(authenticated_user)
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            if request.context_id is not None:
                require_roles(cur, request.context_id, user_id, VIEW_ROLES)
            if request.draft_id is not None:
                cur.execute(
                    """SELECT 1 FROM school_setup_drafts
                       WHERE id=%s AND creator_user_id=%s AND status='draft'""",
                    (request.draft_id, user_id),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Avatar qoralamasi topilmadi")
            cur.execute(
                """INSERT INTO school_assistant_sessions(
                     user_id,context_id,draft_id,workflow_key,current_step,
                     avatar_enabled,speech_enabled,avatar_variant
                   ) VALUES(%s,%s,%s,%s,'welcome',%s,%s,%s)
                   RETURNING id,current_step,state,created_at""",
                (
                    user_id, request.context_id, request.draft_id,
                    request.workflow_key, request.avatar_enabled,
                    request.speech_enabled, request.avatar_variant,
                ),
            )
            session = cur.fetchone()
        return {
            "session": session,
            "capabilities": {
                "can_explain": True, "can_focus_fields": True,
                "can_prepare_drafts": True,
                "can_confirm_privileged_actions": False,
                "can_bypass_permissions": False,
            },
        }

    @router.post("/assistant/sessions/{session_id}/actions")
    def assistant_action(
        session_id: int, request: AssistantAction,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        action_id = request.action_id.strip().upper()
        if action_id not in ASSISTANT_ACTIONS:
            raise HTTPException(status_code=422, detail="Noma'lum avatar amali")
        encoded = json.dumps(request.payload, ensure_ascii=False)
        if len(encoded.encode()) > 20_000:
            raise HTTPException(status_code=413, detail="Avatar amali juda katta")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM school_assistant_sessions
                   WHERE id=%s AND user_id=%s FOR UPDATE""",
                (session_id, user_id),
            )
            session = cur.fetchone()
            if not session:
                raise HTTPException(status_code=404, detail="Avatar sessiyasi topilmadi")
            if session["state"] in {"completed", "cancelled"}:
                raise HTTPException(status_code=409, detail="Avatar sessiyasi yakunlangan")
            state = session["state"]
            step = session["current_step"]
            result: dict[str, Any] = {}
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
                step = str(request.payload.get("next_step") or step)[:80]
            elif action_id == "PREVIOUS_STEP":
                step = str(request.payload.get("previous_step") or step)[:80]
            elif action_id == "SET_DRAFT_VALUE":
                if session["draft_id"] is None:
                    raise HTTPException(
                        status_code=422,
                        detail="Bu avatar sessiyasi onboarding qoralamasiga bog'lanmagan.",
                    )
                draft_step = str(request.payload.get("step") or "").strip()
                expected_version = request.payload.get("expected_version")
                allowed_fields: dict[str, set[str]] = {
                    "identity": {
                        "name", "region", "district", "address",
                        "academic_year", "school_type",
                    },
                    "basic": {
                        "name", "region", "district", "address",
                        "academic_year", "school_type", "billing_enabled",
                        "work_days", "lesson_minutes", "shift_count",
                    },
                    "bell_schedule": {
                        "lesson_minutes", "short_break_minutes",
                        "long_break_after", "long_break_minutes",
                        "max_periods_per_shift", "shifts",
                    },
                    "classes": {
                        "grades", "section_letters", "default_shift",
                        "capacity",
                    },
                    "calendar": {
                        "use_uzbekistan_holidays", "terms",
                        "custom_holidays", "starts_on", "ends_on",
                    },
                    "staff_plan": {
                        "roles", "teacher_count", "notes",
                    },
                    "workload": {
                        "avoid_math_last_periods",
                        "prefer_physical_first_three",
                    },
                }
                if draft_step not in allowed_fields:
                    raise HTTPException(
                        status_code=422,
                        detail="Avatar bu onboarding bo'limini o'zgartira olmaydi.",
                    )
                if (
                    isinstance(expected_version, bool)
                    or not isinstance(expected_version, int)
                    or expected_version < 1
                ):
                    raise HTTPException(
                        status_code=422,
                        detail="Qoralama expected_version raqami kerak.",
                    )
                values = request.payload.get("values")
                if values is None and "field" in request.payload:
                    values = {
                        str(request.payload["field"]): request.payload.get("value")
                    }
                if not isinstance(values, dict) or not values:
                    raise HTTPException(
                        status_code=422,
                        detail="Avatar uchun values obyektini yuboring.",
                    )
                unknown = set(values) - allowed_fields[draft_step]
                if unknown:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "message": "Avatar ruxsat etilmagan maydonni o'zgartirmaydi.",
                            "fields": sorted(unknown),
                        },
                    )
                cur.execute(
                    """SELECT id,payload,version FROM school_setup_drafts
                       WHERE id=%s AND creator_user_id=%s AND status='draft'
                         AND expires_at>NOW() FOR UPDATE""",
                    (session["draft_id"], user_id),
                )
                draft = cur.fetchone()
                if not draft:
                    raise HTTPException(
                        status_code=404, detail="Avatar qoralamasi faol emas."
                    )
                if int(draft["version"]) != expected_version:
                    raise HTTPException(
                        status_code=409,
                        detail="Qoralama versiyasi o'zgargan; qayta yuklang.",
                    )
                draft_payload = dict(draft["payload"] or {})
                current_values = dict(draft_payload.get(draft_step) or {})
                current_values.update(values)
                draft_payload[draft_step] = current_values
                if draft_step == "basic" and "shift_count" in values:
                    draft_payload["shift_count"] = values["shift_count"]
                cur.execute(
                    """UPDATE school_setup_drafts
                       SET payload=%s::jsonb,current_step=%s,version=version+1,
                           updated_at=NOW()
                       WHERE id=%s
                       RETURNING id,current_step,version,updated_at""",
                    (
                        json.dumps(draft_payload, ensure_ascii=False),
                        draft_step, draft["id"],
                    ),
                )
                updated_draft = cur.fetchone()
                step = draft_step
                result = {
                    "applied": True,
                    "draft": updated_draft,
                    "applied_fields": sorted(values),
                }
            elif action_id == "UNDO":
                cur.execute(
                    """SELECT id,action_id,input_payload FROM school_assistant_actions
                       WHERE session_id=%s AND reversible=TRUE
                         AND action_status='completed'
                       ORDER BY sequence_no DESC LIMIT 1 FOR UPDATE""",
                    (session_id,),
                )
                previous = cur.fetchone()
                if previous:
                    cur.execute(
                        """UPDATE school_assistant_actions
                           SET action_status='undone',undone_at=NOW() WHERE id=%s""",
                        (previous["id"],),
                    )
                    result = {
                        "undone_action": previous["action_id"],
                        "restore": previous["input_payload"],
                    }
            cur.execute(
                """SELECT COALESCE(MAX(sequence_no),0)+1 next_sequence
                   FROM school_assistant_actions WHERE session_id=%s""",
                (session_id,),
            )
            sequence = cur.fetchone()["next_sequence"]
            cur.execute(
                """INSERT INTO school_assistant_actions(
                     session_id,sequence_no,action_id,ui_anchor,reversible,
                     input_payload,result_payload
                   ) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb)
                   RETURNING id,sequence_no,created_at""",
                (
                    session_id, sequence, action_id, request.ui_anchor,
                    action_id in REVERSIBLE_ACTIONS, encoded,
                    json.dumps(result, ensure_ascii=False),
                ),
            )
            event = cur.fetchone()
            cur.execute(
                """UPDATE school_assistant_sessions
                   SET state=%s,current_step=%s,
                     state_payload=state_payload||%s::jsonb,updated_at=NOW(),
                     completed_at=CASE WHEN %s='completed' THEN NOW() ELSE completed_at END
                   WHERE id=%s""",
                (
                    state, step,
                    json.dumps({"last_action": action_id, "last_anchor": request.ui_anchor}),
                    state, session_id,
                ),
            )
        return {
            "event": event, "state": state, "current_step": step, "result": result,
            "requires_human_confirmation": False,
            "can_confirm_privileged_actions": False,
            "can_bypass_permissions": False,
        }

    return router

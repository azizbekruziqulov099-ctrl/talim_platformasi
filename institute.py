"""Tenant-safe institute/university credit-module API.

The guided avatar is intentionally limited to navigation and reversible draft
actions.  It never publishes a curriculum, changes student legal status,
finalizes a grade, issues a transcript, records money, or closes a term.
"""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from contextlib import contextmanager
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Callable, Iterator, Literal

import psycopg2
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from modules.institute_grades import (
    CreditResult,
    GradeBand,
    WeightedMark,
    calculate_gpa,
    select_grade_band,
    select_transcript_attempts,
    weighted_percent,
)
from platform_core.database import DatabaseBusyError, db_session


ROLE_LABELS = {
    "owner": "Mulkdor",
    "founder": "Ta'sischi",
    "rector": "Rektor",
    "vice_rector_academic": "O'quv ishlari bo'yicha prorektor",
    "administrator": "Administrator",
    "registrar": "Registrator",
    "dean": "Dekan",
    "deputy_dean": "Dekan o'rinbosari",
    "department_head": "Kafedra mudiri",
    "finance_manager": "Moliya rahbari",
    "accountant": "Hisobchi",
    "hr_manager": "Kadrlar bo'limi",
    "methodist": "Metodist",
    "lecturer": "O'qituvchi",
    "advisor": "Tyutor",
    "student": "Talaba",
}
VIEW_ROLES = set(ROLE_LABELS)
GLOBAL_MANAGER_ROLES = {
    "owner", "founder", "rector", "vice_rector_academic", "administrator",
}
ACADEMIC_MANAGER_ROLES = GLOBAL_MANAGER_ROLES | {
    "registrar", "dean", "deputy_dean", "department_head", "methodist",
}
FINANCE_ROLES = {"owner", "founder", "rector", "finance_manager", "accountant"}

ALL_PERMISSIONS = {
    "institute.view", "structure.manage", "staff.manage", "academics.manage",
    "terms.manage", "enrollments.manage", "schedule.manage",
    "attendance.write", "grades.write", "grades.finalize",
    "transcripts.issue", "finance.view", "finance.manage",
    "workload.manage", "analytics.view", "assistant.use",
}
ROLE_PERMISSIONS = {
    "owner": ALL_PERMISSIONS,
    "founder": ALL_PERMISSIONS,
    "rector": ALL_PERMISSIONS,
    "vice_rector_academic": ALL_PERMISSIONS - {"finance.manage"},
    "administrator": {
        "institute.view", "structure.manage", "staff.manage",
        "academics.manage", "terms.manage", "enrollments.manage",
        "schedule.manage", "attendance.write", "analytics.view",
        "assistant.use",
    },
    "registrar": {
        "institute.view", "academics.manage", "terms.manage",
        "enrollments.manage", "schedule.manage", "attendance.write",
        "grades.write", "grades.finalize", "transcripts.issue",
        "analytics.view", "assistant.use",
    },
    "dean": {
        "institute.view", "staff.manage", "academics.manage",
        "enrollments.manage", "schedule.manage", "attendance.write",
        "grades.write", "analytics.view", "workload.manage", "assistant.use",
    },
    "deputy_dean": {
        "institute.view", "academics.manage", "enrollments.manage",
        "schedule.manage", "attendance.write", "grades.write",
        "analytics.view", "assistant.use",
    },
    "department_head": {
        "institute.view", "staff.manage", "academics.manage",
        "schedule.manage", "attendance.write", "grades.write",
        "workload.manage", "analytics.view", "assistant.use",
    },
    "finance_manager": {
        "institute.view", "finance.view", "finance.manage",
        "analytics.view", "assistant.use",
    },
    "accountant": {
        "institute.view", "finance.view", "finance.manage", "assistant.use",
    },
    "hr_manager": {
        "institute.view", "staff.manage", "workload.manage", "assistant.use",
    },
    "methodist": {
        "institute.view", "academics.manage", "schedule.manage",
        "attendance.write", "grades.write", "analytics.view", "assistant.use",
    },
    "lecturer": {
        "institute.view", "schedule.manage", "attendance.write",
        "grades.write", "analytics.view", "assistant.use",
    },
    "advisor": {"institute.view", "analytics.view", "assistant.use"},
    "student": {"institute.view", "finance.view", "assistant.use"},
}
ROLE_GRANT_MATRIX = {
    "owner": VIEW_ROLES - {"owner"},
    "founder": VIEW_ROLES - {"owner", "founder"},
    "rector": VIEW_ROLES - {"owner", "founder", "rector"},
    "vice_rector_academic": {
        "administrator", "registrar", "dean", "deputy_dean",
        "department_head", "hr_manager", "methodist", "lecturer", "advisor",
    },
    "administrator": {"hr_manager", "methodist", "lecturer", "advisor"},
    "dean": {"deputy_dean", "department_head", "methodist", "lecturer", "advisor"},
    "department_head": {"methodist", "lecturer", "advisor"},
    "hr_manager": {"methodist", "lecturer", "advisor"},
}


def dashboard_menu_keys(roles: set[str], permissions: set[str]) -> list[str]:
    """Return only canonical frontend menu keys the current user can use.

    Read-only student panels are role-gated because viewing one's own grades,
    assessments and transcript intentionally does not grant the corresponding
    staff write/issue permissions.
    """
    menus = ["overview"]
    if "structure.manage" in permissions:
        menus.append("structure")
    academic_reader = bool(
        roles
        & (ACADEMIC_MANAGER_ROLES | {"lecturer", "advisor", "student", "system_admin"})
    )
    if academic_reader:
        menus.extend(("curriculum", "schedule", "attendance"))
    if "student" in roles or permissions & {"grades.write", "grades.finalize"}:
        menus.extend(("gradebook", "exams"))
    if "enrollments.manage" in permissions:
        menus.append("students")
    if "student" in roles or "transcripts.issue" in permissions:
        menus.append("transcripts")
    if "finance.view" in permissions:
        menus.append("finance")
    if "analytics.view" in permissions:
        menus.append("analytics")
    if "staff.manage" in permissions:
        menus.append("staff")
    if permissions & {"structure.manage", "terms.manage"}:
        menus.append("settings")
    return menus


ASSISTANT_ACTIONS = {
    "SHOW_MENU", "FOCUS_FIELD", "SET_DRAFT_VALUE", "NEXT_STEP",
    "PREVIOUS_STEP", "PAUSE", "RESUME", "UNDO", "MINIMIZE",
    "RESTORE", "SPEAK", "COMPLETE_TOUR",
}
REVERSIBLE_ACTIONS = {
    "FOCUS_FIELD", "SET_DRAFT_VALUE", "NEXT_STEP", "PREVIOUS_STEP",
    "MINIMIZE", "RESTORE", "UNDO",
}


class DraftStart(BaseModel):
    relationship: Literal["owner", "founder", "rector", "administrator"]
    ownership_type: Literal["public", "private"]
    institution_type: Literal["institute", "university", "academy", "branch"]
    setup_mode: Literal["manual", "guided", "assistant"] = "guided"
    grading_system: Literal["credit_modular", "five_point", "custom"] = "credit_modular"


class DraftPatch(BaseModel):
    step: str = Field(min_length=1, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
    expected_version: int = Field(ge=1)


class HumanConfirm(BaseModel):
    context_id: int | None = Field(default=None, ge=1)
    expected_version: int | None = Field(default=None, ge=1)
    confirmation: bool


class StaffEnd(HumanConfirm):
    reason: str = Field(min_length=3, max_length=1000)


class VerificationDecision(BaseModel):
    decision: Literal["verified", "rejected"]
    note: str | None = Field(default=None, max_length=2000)
    confirmation: bool


class CampusCreate(BaseModel):
    context_id: int
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=180)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=80)


class RoomCreate(BaseModel):
    context_id: int
    campus_id: int
    building_id: int | None = None
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=180)
    room_type: Literal[
        "classroom", "lecture_hall", "laboratory", "computer", "language",
        "online", "other",
    ] = "classroom"
    capacity: int | None = Field(default=None, ge=1, le=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FacultyCreate(BaseModel):
    context_id: int
    campus_id: int
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=180)
    dean_user_id: int | None = None


class DepartmentCreate(BaseModel):
    context_id: int
    faculty_id: int
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=180)
    head_user_id: int | None = None


class ProgramCreate(BaseModel):
    context_id: int
    department_id: int
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=240)
    degree_level: Literal[
        "foundation", "bachelor", "master", "doctoral", "professional", "custom",
    ]
    study_form: Literal[
        "full_time", "part_time", "evening", "distance", "dual", "custom",
    ] = "full_time"
    language: str = Field(default="uz", min_length=2, max_length=20)
    duration_terms: int = Field(ge=1, le=24)
    target_credits: Decimal = Field(gt=0, le=1000)
    policy_overrides: dict[str, Any] = Field(default_factory=dict)


class AcademicYearCreate(BaseModel):
    context_id: int
    code: str = Field(min_length=3, max_length=40)
    starts_on: date
    ends_on: date


class TermCreate(BaseModel):
    context_id: int
    academic_year_id: int
    term_no: int = Field(ge=1, le=12)
    term_type: Literal["semester", "trimester", "quarter", "summer", "custom"] = "semester"
    name: str = Field(min_length=2, max_length=120)
    starts_on: date
    ends_on: date
    registration_opens_at: datetime | None = None
    registration_closes_at: datetime | None = None
    change_deadline: datetime | None = None


class TermStatus(BaseModel):
    context_id: int
    status: Literal["planned", "registration", "active", "grade_entry", "closed", "archived"]
    confirmation: bool


class StaffAssign(BaseModel):
    context_id: int
    user_id: int
    role_key: str
    campus_id: int | None = None
    faculty_id: int | None = None
    department_id: int | None = None
    confirmation: bool = False


class CourseCreate(BaseModel):
    context_id: int
    department_id: int
    code: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=2, max_length=240)
    credit_value: Decimal = Field(gt=0, le=120)
    lecture_hours: Decimal = Field(default=0, ge=0)
    practice_hours: Decimal = Field(default=0, ge=0)
    laboratory_hours: Decimal = Field(default=0, ge=0)
    independent_hours: Decimal = Field(default=0, ge=0)
    supports_latex: bool = False
    description: str | None = Field(default=None, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CurriculumCreate(BaseModel):
    context_id: int
    program_id: int
    admission_year: int = Field(ge=1900, le=2200)
    version: int = Field(default=1, ge=1)
    name: str = Field(min_length=2, max_length=240)


class CurriculumCourseCreate(BaseModel):
    context_id: int
    course_id: int
    recommended_term: int = Field(ge=1, le=24)
    requirement_type: Literal["required", "elective", "optional"]
    elective_block: str | None = Field(default=None, max_length=80)
    credits_override: Decimal | None = Field(default=None, gt=0)
    hours_override: dict[str, Any] = Field(default_factory=dict)
    prerequisite_course_ids: list[int] = Field(default_factory=list, max_length=50)


class CohortCreate(BaseModel):
    context_id: int
    program_id: int
    curriculum_id: int
    code: str = Field(min_length=1, max_length=80)
    admission_year: int = Field(ge=1900, le=2200)
    current_level: int = Field(default=1, ge=1, le=12)
    study_language: str = Field(default="uz", min_length=2, max_length=20)
    advisor_user_id: int | None = None


class SectionCreate(BaseModel):
    context_id: int
    term_id: int
    course_id: int
    curriculum_course_id: int | None = None
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=2, max_length=180)
    primary_lecturer_user_id: int | None = None
    delivery_mode: Literal["offline", "online_live", "hybrid", "self_paced"] = "offline"
    section_type: Literal["regular", "retake", "summer", "independent"] = "regular"
    capacity: int = Field(default=30, ge=1, le=10000)
    cohort_ids: list[int] = Field(default_factory=list, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EnrollmentCreate(BaseModel):
    context_id: int
    section_id: int
    cohort_id: int | None = Field(default=None, ge=1)
    student_user_id: int
    student_number: str = Field(min_length=2, max_length=80)
    enrollment_type: Literal["regular", "retake", "audit", "summer"] = "regular"
    status: Literal["pending", "waitlisted", "enrolled"] = "pending"
    note: str | None = Field(default=None, max_length=2000)
    confirmation: bool = False


class EnrollmentDecision(BaseModel):
    context_id: int
    status: Literal["enrolled", "waitlisted", "completed", "withdrawn", "rejected"]
    confirmation: bool


class ScheduleCreate(BaseModel):
    context_id: int
    section_id: int
    teacher_user_id: int
    room_id: int | None = None
    schedule_kind: Literal["weekly", "dated"]
    weekday: int | None = Field(default=None, ge=1, le=7)
    lesson_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    starts_at: str
    ends_at: str
    lesson_kind: Literal["lecture", "practice", "laboratory", "seminar", "consultation", "exam", "other"] = "lecture"
    topic: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "published"] = "draft"
    confirmation: bool = False


class AttendanceMark(BaseModel):
    context_id: int
    section_id: int
    student_user_id: int
    schedule_slot_id: int | None = None
    lesson_date: date
    scheduled_minutes: int = Field(default=80, ge=1, le=1440)
    absent_minutes: int = Field(default=0, ge=0, le=1440)
    status: Literal["present", "absent", "late", "excused", "sick"]
    note: str | None = Field(default=None, max_length=1000)


class AssessmentCreate(BaseModel):
    context_id: int
    section_id: int
    assessment_type: Literal["attendance", "assignment", "quiz", "project", "midterm", "final", "other"]
    title: str = Field(min_length=2, max_length=240)
    max_score: Decimal = Field(gt=0)
    weight_percent: Decimal = Field(gt=0, le=100)
    due_at: datetime | None = None
    settings: dict[str, Any] = Field(default_factory=dict)


class GradeCreate(BaseModel):
    context_id: int
    assessment_id: int
    enrollment_id: int
    score: Decimal = Field(ge=0)
    feedback: str | None = Field(default=None, max_length=10000)
    idempotency_key: str | None = Field(default=None, min_length=12, max_length=120)


class FinalizeResult(BaseModel):
    context_id: int
    idempotency_key: str = Field(min_length=12, max_length=120)
    confirmation: bool


class TranscriptIssue(HumanConfirm):
    idempotency_key: str = Field(min_length=12, max_length=120)


class ContractCreate(BaseModel):
    context_id: int
    student_user_id: int
    program_id: int
    academic_year_id: int
    contract_no: str = Field(min_length=2, max_length=100)
    contract_type: Literal["paid", "grant", "scholarship", "sponsored", "other"] = "paid"
    total_amount: Decimal = Field(ge=0)
    scholarship_amount: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="UZS", min_length=3, max_length=8)
    payer_user_id: int | None = None
    starts_on: date
    ends_on: date
    confirmation: bool


class InstallmentItem(BaseModel):
    installment_no: int = Field(ge=1, le=100)
    due_date: date
    amount: Decimal = Field(gt=0)


class InstallmentsCreate(BaseModel):
    context_id: int
    items: list[InstallmentItem] = Field(min_length=1, max_length=100)
    confirmation: bool


class PaymentCreate(BaseModel):
    context_id: int
    contract_id: int
    installment_id: int
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="UZS", min_length=3, max_length=8)
    payment_method: Literal["cash", "card", "bank_transfer", "online", "other"]
    reference: str | None = Field(default=None, max_length=300)
    idempotency_key: str = Field(min_length=12, max_length=120)
    paid_at: datetime | None = None
    confirmation: bool


class WorkloadCreate(BaseModel):
    context_id: int
    term_id: int
    section_id: int
    staff_user_id: int
    workload_type: Literal["lecture", "practice", "laboratory", "supervision", "consultation", "assessment", "other"]
    planned_hours: Decimal = Field(gt=0, le=10000)
    confirmation: bool = False


class AssistantStart(BaseModel):
    workflow_key: str = Field(default="institute_onboarding", max_length=100)
    context_id: int | None = None
    avatar_enabled: bool = True
    speech_enabled: bool = True
    avatar_variant: Literal["female", "male", "neutral"] = "female"


class AssistantAction(BaseModel):
    action_id: str = Field(min_length=1, max_length=60)
    ui_anchor: str | None = Field(default=None, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


def create_institute_router(jwt_check: Callable[[str], int]) -> APIRouter:
    router = APIRouter(prefix="/api/institut-v1", tags=["Institut v1"])

    def authenticated_user(
        authorization: str | None = Header(default=None),
    ) -> int:
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
                detail="Institut bazasi o'rnatilmagan: 001, 009, 010, 011 va 012 SQL ni bajaring.",
            ) from exc
        except psycopg2.errors.UniqueViolation as exc:
            raise HTTPException(status_code=409, detail="Bu ma'lumot avval saqlangan.") from exc
        except psycopg2.errors.ForeignKeyViolation as exc:
            raise HTTPException(status_code=422, detail="Bog'langan institut resursi topilmadi.") from exc
        except psycopg2.errors.CheckViolation as exc:
            detail = (
                "O'qituvchi, oqim yoki xona vaqti to'qnashdi."
                if "schedule_conflict" in str(exc)
                else "Ma'lumot institut qoidalariga mos emas."
            )
            raise HTTPException(status_code=409, detail=detail) from exc
        except (
            psycopg2.errors.InvalidTextRepresentation,
            psycopg2.errors.NotNullViolation,
            psycopg2.DataError,
        ) as exc:
            raise HTTPException(status_code=422, detail="Yuborilgan ma'lumot formati noto'g'ri.") from exc

    def ensure_schema(cur: Any) -> None:
        cur.execute(
            """SELECT version FROM app_schema_migrations
               WHERE version=ANY(%s)""",
            ([
                "009_institute_core", "010_institute_curriculum",
                "011_institute_teaching", "012_institute_finance_assistant",
            ],),
        )
        if len(cur.fetchall()) != 4:
            raise HTTPException(status_code=503, detail="Institut 009–012 migratsiyalari to'liq bajarilmagan.")

    def system_admin(cur: Any, user_id: int) -> bool:
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
        return cur.fetchone() is not None

    def require_creation_admin(cur: Any, user_id: int) -> None:
        if not system_admin(cur, user_id):
            raise HTTPException(
                status_code=403,
                detail="Yangi institutni faqat Administrator markazi ochadi",
            )

    def require_human(value: bool, message: str) -> None:
        if value is not True:
            raise HTTPException(status_code=409, detail=message)

    def require_json_size(value: Any, maximum: int, label: str) -> None:
        size = len(json.dumps(value, ensure_ascii=False, default=str).encode("utf-8"))
        if size > maximum:
            raise HTTPException(status_code=413, detail=f"{label} {maximum} baytdan oshmasin")

    def parse_clock(value: str, label: str) -> time:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value.strip()):
            raise HTTPException(status_code=422, detail=f"{label} HH:MM shaklida bo'lsin")
        return time.fromisoformat(value.strip())

    def payload_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
        value = payload.get(key)
        return dict(value) if isinstance(value, dict) else {}

    def required_payload_text(
        value: Any, label: str, *, maximum: int,
    ) -> str:
        text = str(value or "").strip()
        if not text or len(text) > maximum:
            raise HTTPException(
                status_code=422,
                detail=f"{label} bo'sh bo'lmasin va {maximum} belgidan oshmasin",
            )
        return text

    def parse_payload_date(value: Any, label: str) -> date:
        try:
            return date.fromisoformat(str(value))
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=422, detail=f"{label} YYYY-MM-DD shaklida bo'lsin",
            ) from exc

    def parse_payload_datetime(value: Any, label: str) -> datetime | None:
        if value in (None, ""):
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=422, detail=f"{label} sana-vaqt shaklida bo'lsin",
            ) from exc

    def onboarding_missing(payload: dict[str, Any]) -> list[str]:
        identity = payload_object(payload, "identity")
        structure = payload_object(payload, "structure")
        campus = payload_object(payload, "campus")
        program = payload_object(payload, "program")
        calendar = payload_object(payload, "calendar")
        checks = {
            "identity.name": identity.get("name"),
            "campus.code": campus.get("code"),
            "campus.name": campus.get("name"),
            "structure.faculty_code": structure.get("faculty_code"),
            "structure.faculty_name": structure.get("faculty_name"),
            "structure.department_code": structure.get("department_code"),
            "structure.department_name": structure.get("department_name"),
            "program.code": program.get("code"),
            "program.name": program.get("name"),
            "program.degree_level": program.get("degree_level"),
            "program.study_form": program.get("study_form"),
            "program.duration_terms": program.get("duration_terms"),
            "program.target_credits": program.get("target_credits"),
            "calendar.academic_year_code": calendar.get("academic_year_code"),
            "calendar.starts_on": calendar.get("starts_on"),
            "calendar.ends_on": calendar.get("ends_on"),
            "calendar.first_term_name": calendar.get("first_term_name"),
            "calendar.first_term_starts_on": calendar.get("first_term_starts_on"),
            "calendar.first_term_ends_on": calendar.get("first_term_ends_on"),
        }
        return [key for key, value in checks.items() if value in (None, "")]

    def permissions_for(roles: set[str]) -> set[str]:
        if "system_admin" in roles:
            return set(ALL_PERMISSIONS)
        result: set[str] = set()
        for role in roles:
            result.update(ROLE_PERMISSIONS.get(role, set()))
        return result

    def roles_for_permission(permission: str) -> set[str]:
        return {role for role, values in ROLE_PERMISSIONS.items() if permission in values}

    def active_assignments(cur: Any, context_id: int, user_id: int) -> list[dict[str, Any]]:
        cur.execute(
            """SELECT c.active,p.onboarding_status,p.verification_status
               FROM learning_contexts c JOIN institute_profiles p ON p.context_id=c.id
               WHERE c.id=%s AND c.context_type='university'""",
            (context_id,),
        )
        state = cur.fetchone()
        if (
            not state or not state["active"]
            or state["onboarding_status"] in {"suspended", "archived"}
            or state["verification_status"] == "rejected"
        ):
            raise HTTPException(status_code=403, detail="Institut faol emas")
        cur.execute(
            """SELECT role_key,campus_id,faculty_id,department_id
               FROM institute_role_assignments
               WHERE context_id=%s AND user_id=%s AND status='active'
                 AND starts_at<=NOW() AND (ends_at IS NULL OR ends_at>NOW())""",
            (context_id, user_id),
        )
        return [dict(row) for row in cur.fetchall()]

    def assignment_matches(
        row: dict[str, Any], campus_id: int | None,
        faculty_id: int | None, department_id: int | None,
    ) -> bool:
        if row["campus_id"] is not None and int(row["campus_id"]) != int(campus_id or 0):
            return False
        if row["faculty_id"] is not None and int(row["faculty_id"]) != int(faculty_id or 0):
            return False
        if row["department_id"] is not None and int(row["department_id"]) != int(department_id or 0):
            return False
        return True

    def require_roles(
        cur: Any, context_id: int, user_id: int, allowed: set[str],
        *, campus_id: int | None = None, faculty_id: int | None = None,
        department_id: int | None = None, require_global: bool = False,
    ) -> set[str]:
        if system_admin(cur, user_id):
            return {"system_admin"}
        assignments = active_assignments(cur, context_id, user_id)
        matches = [
            row for row in assignments
            if row["role_key"] in allowed
            and assignment_matches(row, campus_id, faculty_id, department_id)
        ]
        if require_global:
            matches = [
                row for row in matches
                if row["campus_id"] is None and row["faculty_id"] is None
                and row["department_id"] is None
            ]
        if not matches:
            raise HTTPException(status_code=403, detail="Institutdagi vakolatingiz yetarli emas")
        return {str(row["role_key"]) for row in matches}

    def require_permission(
        cur: Any, context_id: int, user_id: int, permission: str, **scope: Any,
    ) -> set[str]:
        return require_roles(
            cur, context_id, user_id, roles_for_permission(permission), **scope
        )

    def scope_sets(
        cur: Any, context_id: int, user_id: int, allowed: set[str] = VIEW_ROLES,
    ) -> tuple[set[str], bool, list[int], list[int], list[int]]:
        if system_admin(cur, user_id):
            return {"system_admin"}, True, [], [], []
        rows = [
            row for row in active_assignments(cur, context_id, user_id)
            if row["role_key"] in allowed
        ]
        if not rows:
            raise HTTPException(status_code=403, detail="Institut vakolati topilmadi")
        roles = {str(row["role_key"]) for row in rows}
        global_scope = any(
            row["campus_id"] is None and row["faculty_id"] is None
            and row["department_id"] is None for row in rows
        )
        campuses = sorted({
            int(row["campus_id"]) for row in rows
            if row["campus_id"] is not None and row["faculty_id"] is None
        })
        faculties = sorted({
            int(row["faculty_id"]) for row in rows
            if row["faculty_id"] is not None and row["department_id"] is None
        })
        departments = sorted({int(row["department_id"]) for row in rows if row["department_id"] is not None})
        return roles, global_scope, campuses, faculties, departments

    def department_scope(cur: Any, context_id: int, department_id: int) -> dict[str, int]:
        cur.execute(
            """SELECT campus_id,faculty_id,id department_id
               FROM institute_departments WHERE context_id=%s AND id=%s AND active""",
            (context_id, department_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Kafedra topilmadi")
        return {key: int(row[key]) for key in ("campus_id", "faculty_id", "department_id")}

    def program_scope(cur: Any, context_id: int, program_id: int) -> dict[str, int]:
        cur.execute(
            """SELECT campus_id,faculty_id,department_id
               FROM institute_programs WHERE context_id=%s AND id=%s AND active""",
            (context_id, program_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ta'lim dasturi topilmadi")
        return {key: int(row[key]) for key in ("campus_id", "faculty_id", "department_id")}

    def finance_policy(cur: Any, context_id: int) -> tuple[str, bool]:
        cur.execute(
            """SELECT default_currency,
                      settings#>'{onboarding,finance,contracts_enabled}' enabled
               FROM institute_profiles WHERE context_id=%s""",
            (context_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Institut profili topilmadi")
        enabled = True if row["enabled"] is None else row["enabled"] is True
        return str(row["default_currency"]).upper(), enabled

    def section_resource(
        cur: Any, context_id: int, section_id: int, *, lock: bool = False,
    ) -> dict[str, Any]:
        cur.execute(
            f"""SELECT * FROM institute_course_sections
                WHERE context_id=%s AND id=%s {'FOR UPDATE' if lock else ''}""",
            (context_id, section_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Fan oqimi topilmadi")
        return dict(row)

    def section_access(
        cur: Any, context_id: int, section_id: int, user_id: int,
        *, write_permission: str | None = None,
    ) -> dict[str, Any]:
        section = section_resource(cur, context_id, section_id)
        if system_admin(cur, user_id):
            return section
        assignments = active_assignments(cur, context_id, user_id)
        if write_permission:
            allowed = roles_for_permission(write_permission)
            privileged_match = any(
                row["role_key"] in allowed
                and row["role_key"] != "lecturer"
                and assignment_matches(
                    row, section["campus_id"], section["faculty_id"],
                    section["department_id"],
                )
                for row in assignments
            )
            if privileged_match:
                return section
            lecturer_match = any(
                row["role_key"] == "lecturer"
                and "lecturer" in allowed
                and assignment_matches(
                    row, section["campus_id"], section["faculty_id"],
                    section["department_id"],
                )
                for row in assignments
            )
            if lecturer_match:
                cur.execute(
                    """SELECT 1 FROM institute_section_instructors
                       WHERE context_id=%s AND section_id=%s
                         AND instructor_user_id=%s AND active""",
                    (context_id, section_id, user_id),
                )
                if cur.fetchone() or int(section.get("primary_lecturer_user_id") or 0) == user_id:
                    return section
        else:
            if any(
                row["role_key"] in ACADEMIC_MANAGER_ROLES
                and assignment_matches(
                    row, section["campus_id"], section["faculty_id"],
                    section["department_id"],
                )
                for row in assignments
            ):
                return section
            lecturer_match = any(
                row["role_key"] == "lecturer"
                and assignment_matches(
                    row, section["campus_id"], section["faculty_id"],
                    section["department_id"],
                )
                for row in assignments
            )
            if lecturer_match:
                cur.execute(
                    """SELECT 1 FROM institute_section_instructors
                       WHERE context_id=%s AND section_id=%s
                         AND instructor_user_id=%s AND active
                       UNION ALL SELECT 1 WHERE %s=%s LIMIT 1""",
                    (
                        context_id, section_id, user_id, user_id,
                        section.get("primary_lecturer_user_id"),
                    ),
                )
                if cur.fetchone():
                    return section
            advisor_match = any(
                row["role_key"] == "advisor"
                and assignment_matches(
                    row, section["campus_id"], section["faculty_id"],
                    section["department_id"],
                )
                for row in assignments
            )
            if advisor_match:
                cur.execute(
                    """SELECT 1 FROM institute_section_cohorts sc
                       JOIN institute_cohorts co
                         ON co.context_id=sc.context_id AND co.id=sc.cohort_id
                       WHERE sc.context_id=%s AND sc.section_id=%s
                         AND co.advisor_user_id=%s AND co.active LIMIT 1""",
                    (context_id, section_id, user_id),
                )
                if cur.fetchone():
                    return section
            cur.execute(
                """SELECT 1 FROM institute_enrollments
                   WHERE context_id=%s AND section_id=%s AND student_user_id=%s
                     AND status IN ('enrolled','completed')""",
                (context_id, section_id, user_id),
            )
            if cur.fetchone():
                return section
        raise HTTPException(status_code=403, detail="Bu fan oqimiga ruxsat yo'q")

    def audit(
        cur: Any, context_id: int | None, actor: int, action: str,
        target_type: str, target_id: int | None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        cur.execute(
            """INSERT INTO institute_audit_log(
                 context_id,actor_user_id,action_key,target_type,target_id,payload
               ) VALUES(%s,%s,%s,%s,%s,%s::jsonb)""",
            (
                context_id, actor, action, target_type, target_id,
                json.dumps(payload or {}, ensure_ascii=False, default=str),
            ),
        )

    def claim_request(
        cur: Any, context_id: int, key: str, actor: int, action: str,
        fingerprint: str,
    ) -> int | None:
        cur.execute(
            """INSERT INTO institute_request_keys(
                 context_id,request_key,actor_user_id,action_key,request_fingerprint
               ) VALUES(%s,%s,%s,%s,%s)
               ON CONFLICT DO NOTHING RETURNING request_key""",
            (context_id, key, actor, action, fingerprint),
        )
        if cur.fetchone():
            return None
        cur.execute(
            """SELECT actor_user_id,action_key,target_id,request_fingerprint
               FROM institute_request_keys WHERE context_id=%s AND request_key=%s""",
            (context_id, key),
        )
        row = cur.fetchone()
        if (
            not row or int(row["actor_user_id"]) != actor
            or row["action_key"] != action
            or row["request_fingerprint"] != fingerprint
        ):
            raise HTTPException(
                status_code=409,
                detail="Idempotency kaliti boshqa amal yoki payload uchun ishlatilgan",
            )
        return int(row["target_id"] or 0)

    def request_fingerprint(action: str, payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            {"action": action, "payload": payload},
            ensure_ascii=False, default=str, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def finish_request(cur: Any, context_id: int, key: str, target_id: int) -> None:
        cur.execute(
            "UPDATE institute_request_keys SET target_id=%s WHERE context_id=%s AND request_key=%s",
            (target_id, context_id, key),
        )

    def generic_role(role_key: str) -> str:
        if role_key == "student":
            return "student"
        if role_key in {"rector"}:
            return "director"
        if role_key in GLOBAL_MANAGER_ROLES | {"registrar", "dean", "deputy_dean", "department_head"}:
            return "manager"
        if role_key in {"lecturer", "methodist"}:
            return "teacher"
        if role_key == "advisor":
            return "counselor"
        return "assistant"

    def upsert_role(
        cur: Any, *, context_id: int, user_id: int, role_key: str,
        campus_id: int | None, faculty_id: int | None,
        department_id: int | None, approved_by: int | None,
    ) -> int:
        cur.execute(
            """INSERT INTO institute_role_assignments(
                 context_id,campus_id,faculty_id,department_id,user_id,role_key,
                 status,approved_by_user_id,permissions
               ) VALUES(%s,%s,%s,%s,%s,%s,'active',%s,'{"source":"institute_v1"}')
               ON CONFLICT(
                 context_id,(COALESCE(campus_id,0)),(COALESCE(faculty_id,0)),
                 (COALESCE(department_id,0)),user_id,role_key
               ) DO UPDATE SET status='active',approved_by_user_id=EXCLUDED.approved_by_user_id,
                 ends_at=NULL,updated_at=NOW() RETURNING id""",
            (
                context_id, campus_id, faculty_id, department_id, user_id,
                role_key, approved_by,
            ),
        )
        assignment_id = int(cur.fetchone()["id"])
        if campus_id is None and faculty_id is None and department_id is None:
            mapped = generic_role(role_key)
            cur.execute(
                """INSERT INTO context_memberships(
                     context_id,user_id,member_role,status,source,
                     approved_by_user_id,metadata
                   ) VALUES(%s,%s,%s,'active','institute_v1',%s,%s::jsonb)
                   ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,member_role)
                   DO UPDATE SET status='active',ended_at=NULL,updated_at=NOW(),
                     approved_by_user_id=EXCLUDED.approved_by_user_id,
                     metadata=EXCLUDED.metadata""",
                (
                    context_id, user_id, mapped, approved_by,
                    json.dumps({"institute_role": role_key}, ensure_ascii=False),
                ),
            )
        return assignment_id

    @router.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ready",
            "module": "institute",
            "version": "institute-v1-secure-v15",
            "schema": "009+010+011+012",
        }

    @router.get("/meta")
    def meta(_: int = Depends(authenticated_user)) -> dict[str, Any]:
        return {
            "roles": [{"key": key, "label": value} for key, value in ROLE_LABELS.items()],
            "permissions": sorted(ALL_PERMISSIONS),
            "ownership_types": ["public", "private"],
            "institution_types": ["institute", "university", "academy", "branch"],
            "degree_levels": [
                "foundation", "bachelor", "master", "doctoral",
                "professional", "custom",
            ],
            "study_forms": [
                "full_time", "part_time", "evening", "distance", "dual", "custom",
            ],
            "student_statuses": [
                "active", "academic_leave", "retained", "transferred",
                "expelled", "reinstated", "graduated",
            ],
            "grading_systems": ["credit_modular", "five_point", "custom"],
            "official_integrations": {
                "hemis": "placeholder_not_connected",
                "contract": "placeholder_not_connected",
                "billing": "placeholder_not_connected",
            },
        }

    @router.post("/onboarding/drafts")
    def start_draft(
        request: DraftStart,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            require_creation_admin(cur, user_id)
            cur.execute(
                """INSERT INTO institute_setup_drafts(
                     creator_user_id,relationship,ownership_type,institution_type,
                     setup_mode,payload
                   ) VALUES(%s,%s,%s,%s,%s,%s::jsonb)
                   RETURNING id,version,current_step,status,expires_at""",
                (
                    user_id, request.relationship, request.ownership_type,
                    request.institution_type, request.setup_mode,
                    json.dumps(
                        {"grading_system": request.grading_system},
                        ensure_ascii=False,
                    ),
                ),
            )
            row = dict(cur.fetchone())
        return {"item": row}

    @router.patch("/onboarding/drafts/{draft_id}")
    def patch_draft(
        draft_id: int,
        request: DraftPatch,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_json_size(request.payload, 100_000, "Qoralama")
        with database() as (_, cur):
            ensure_schema(cur)
            require_creation_admin(cur, user_id)
            cur.execute(
                """UPDATE institute_setup_drafts
                   SET current_step=%s,payload=payload||%s::jsonb,version=version+1
                   WHERE id=%s AND creator_user_id=%s AND status='draft'
                     AND version=%s AND expires_at>NOW()
                   RETURNING id,version,current_step,status,payload,expires_at""",
                (
                    request.step,
                    json.dumps(request.payload, ensure_ascii=False, default=str),
                    draft_id, user_id, request.expected_version,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=409, detail="Qoralama o'zgargan yoki muddati tugagan")
        return {"item": dict(row)}

    @router.get("/onboarding/drafts/{draft_id}/preview")
    def preview_draft(
        draft_id: int,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT id,relationship,ownership_type,institution_type,setup_mode,
                          current_step,status,payload,version,expires_at
                   FROM institute_setup_drafts
                   WHERE id=%s AND creator_user_id=%s""",
                (draft_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Qoralama topilmadi")
        payload = dict(row["payload"] or {})
        missing = onboarding_missing(payload)
        return {"item": dict(row), "valid": not missing, "missing": missing}

    @router.post("/onboarding/drafts/{draft_id}/commit")
    def commit_draft(
        draft_id: int,
        request: HumanConfirm,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Institut ochilishini inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            require_creation_admin(cur, user_id)
            cur.execute(
                """SELECT * FROM institute_setup_drafts
                   WHERE id=%s AND creator_user_id=%s FOR UPDATE""",
                (draft_id, user_id),
            )
            draft = cur.fetchone()
            if not draft:
                raise HTTPException(status_code=404, detail="Qoralama topilmadi")
            if draft["status"] == "confirmed":
                return {"context_id": int(draft["confirmed_context_id"]), "reused": True}
            if draft["status"] != "draft" or draft["expires_at"] <= datetime.now(timezone.utc):
                raise HTTPException(status_code=409, detail="Qoralama faol emas")
            if request.expected_version and int(draft["version"]) != request.expected_version:
                raise HTTPException(status_code=409, detail="Qoralama versiyasi o'zgargan")
            payload = dict(draft["payload"] or {})
            missing = onboarding_missing(payload)
            if missing:
                raise HTTPException(
                    status_code=422,
                    detail={"message": "Onboarding ma'lumotlari to'liq emas", "missing": missing},
                )
            identity = payload_object(payload, "identity")
            structure = payload_object(payload, "structure")
            campus = payload_object(payload, "campus")
            program = payload_object(payload, "program")
            calendar = payload_object(payload, "calendar")
            team = payload_object(payload, "team")
            finance = payload_object(payload, "finance")
            policy = payload_object(payload, "academic_policy")
            name = required_payload_text(identity.get("name"), "Institut nomi", maximum=240)
            campus_code = required_payload_text(campus.get("code"), "Kampus kodi", maximum=40)
            campus_name = required_payload_text(campus.get("name"), "Kampus nomi", maximum=180)
            faculty_code = required_payload_text(structure.get("faculty_code"), "Fakultet kodi", maximum=40)
            faculty_name = required_payload_text(structure.get("faculty_name"), "Fakultet nomi", maximum=180)
            department_code = required_payload_text(structure.get("department_code"), "Kafedra kodi", maximum=40)
            department_name = required_payload_text(structure.get("department_name"), "Kafedra nomi", maximum=180)
            program_code = required_payload_text(program.get("code"), "Dastur kodi", maximum=40)
            program_name = required_payload_text(program.get("name"), "Dastur nomi", maximum=240)
            degree_level = str(program.get("degree_level"))
            study_form = str(program.get("study_form"))
            if degree_level not in {"foundation", "bachelor", "master", "doctoral", "professional", "custom"}:
                raise HTTPException(status_code=422, detail="Dastur darajasi noto'g'ri")
            if study_form not in {"full_time", "part_time", "evening", "distance", "dual", "custom"}:
                raise HTTPException(status_code=422, detail="Ta'lim shakli noto'g'ri")
            try:
                duration_terms = int(program.get("duration_terms"))
                target_credits = Decimal(str(program.get("target_credits")))
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=422, detail="Dastur davri yoki krediti noto'g'ri") from exc
            if not 1 <= duration_terms <= 24 or not Decimal("0") < target_credits <= Decimal("1000"):
                raise HTTPException(status_code=422, detail="Dastur davri yoki krediti chegaradan tashqarida")
            year_code = required_payload_text(calendar.get("academic_year_code"), "O'quv yili kodi", maximum=40)
            year_start = parse_payload_date(calendar.get("starts_on"), "O'quv yili boshlanishi")
            year_end = parse_payload_date(calendar.get("ends_on"), "O'quv yili tugashi")
            term_name = required_payload_text(calendar.get("first_term_name"), "Birinchi davr nomi", maximum=120)
            term_start = parse_payload_date(calendar.get("first_term_starts_on"), "Davr boshlanishi")
            term_end = parse_payload_date(calendar.get("first_term_ends_on"), "Davr tugashi")
            if year_end <= year_start or term_end <= term_start:
                raise HTTPException(status_code=422, detail="O'quv yili yoki davr sanalari noto'g'ri")
            if term_start < year_start or term_end > year_end:
                raise HTTPException(status_code=422, detail="Birinchi davr o'quv yili ichida bo'lishi kerak")
            registration_opens = parse_payload_datetime(calendar.get("registration_opens_at"), "Ro'yxatdan o'tish boshlanishi")
            registration_closes = parse_payload_datetime(calendar.get("registration_closes_at"), "Ro'yxatdan o'tish tugashi")
            change_deadline = parse_payload_datetime(calendar.get("change_deadline"), "Tanlovni o'zgartirish muddati")
            if registration_opens and registration_closes and registration_closes <= registration_opens:
                raise HTTPException(status_code=422, detail="Ro'yxatdan o'tish oynasi sanalari noto'g'ri")
            term_type = str(policy.get("term_system") or "semester")
            if term_type not in {"semester", "trimester", "quarter", "summer", "custom"}:
                term_type = "semester"
            planned_roles = team.get("planned_roles") or []
            if not isinstance(planned_roles, list) or len(planned_roles) > len(ROLE_LABELS):
                raise HTTPException(status_code=422, detail="Rejalashtirilgan rollar noto'g'ri")
            planned_roles = sorted({str(role) for role in planned_roles})
            if any(role not in ROLE_LABELS for role in planned_roles):
                raise HTTPException(status_code=422, detail="Noma'lum institut roli yuborilgan")
            default_currency = str(finance.get("default_currency") or "UZS").upper()
            if not re.fullmatch(r"[A-Z]{3,8}", default_currency):
                raise HTTPException(status_code=422, detail="Valyuta kodi noto'g'ri")
            contracts_enabled = finance.get("contracts_enabled", False) is True
            try:
                installment_count = int(finance.get("installment_count") or 1)
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=422, detail="Bo'lib to'lash soni noto'g'ri") from exc
            if contracts_enabled and not 1 <= installment_count <= 24:
                raise HTTPException(status_code=422, detail="Bo'lib to'lash soni 1–24 bo'lsin")
            onboarding_settings = {
                "onboarding": {
                    "team": {"planned_roles": planned_roles},
                    "finance": {
                        "contracts_enabled": contracts_enabled,
                        "default_currency": default_currency,
                        "installment_count": installment_count,
                        "external_integration": str(finance.get("external_integration") or "none"),
                    },
                },
            }
            require_json_size(onboarding_settings, 30_000, "Onboarding sozlamalari")
            cur.execute(
                """INSERT INTO learning_contexts(
                     context_type,name,owner_user_id,region,district,
                     external_type,external_id,active,metadata
                   ) VALUES('university',%s,%s,%s,%s,'institute_v1',%s,FALSE,%s::jsonb)
                   RETURNING id""",
                (
                    name, user_id, identity.get("region"), identity.get("district"),
                    draft_id,
                    json.dumps({"source": "institute_v1"}, ensure_ascii=False),
                ),
            )
            context_id = int(cur.fetchone()["id"])
            grading_system = str(payload.get("grading_system") or "credit_modular")
            require_json_size(policy, 30_000, "Akademik siyosat")
            effective_policy = {
                "credits_per_year": 60,
                "credits_per_term": 30,
                "hours_per_credit": 25,
                "promotion_gpa": 2.5,
                "unexcused_course_warning_percent": 25,
                "semester_absence_warning_hours": 74,
                "auto_exclusion": False,
                "retake_enabled": True,
                "summer_term_enabled": True,
                "transcript_attempt_policy": "latest",
                **policy,
            }
            effective_policy["auto_exclusion"] = False
            cur.execute(
                """INSERT INTO institute_profiles(
                     context_id,ownership_type,institution_type,onboarding_status,
                     verification_status,grading_system,default_currency,
                     academic_policy,settings
                   ) VALUES(%s,%s,%s,'pending_verification','pending',%s,
                     %s,%s::jsonb,%s::jsonb)""",
                (
                    context_id, draft["ownership_type"], draft["institution_type"],
                    grading_system, default_currency,
                    json.dumps(effective_policy, ensure_ascii=False, default=str),
                    json.dumps(onboarding_settings, ensure_ascii=False, default=str),
                ),
            )
            cur.execute(
                """INSERT INTO institute_campuses(context_id,code,name,address,phone)
                   VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                (
                    context_id, campus_code, campus_name,
                    campus.get("address"), campus.get("phone"),
                ),
            )
            campus_id = int(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO institute_faculties(context_id,campus_id,code,name)
                   VALUES(%s,%s,%s,%s) RETURNING id""",
                (context_id, campus_id, faculty_code, faculty_name),
            )
            faculty_id = int(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO institute_departments(
                     context_id,campus_id,faculty_id,code,name
                   ) VALUES(%s,%s,%s,%s,%s) RETURNING id""",
                (context_id, campus_id, faculty_id, department_code, department_name),
            )
            department_id = int(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO institute_programs(
                     context_id,campus_id,faculty_id,department_id,code,name,
                     degree_level,study_form,language,duration_terms,target_credits
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    context_id, campus_id, faculty_id, department_id,
                    program_code, program_name, degree_level, study_form,
                    str(program.get("language") or "uz")[:20], duration_terms,
                    target_credits,
                ),
            )
            program_id = int(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO institute_academic_years(
                     context_id,code,starts_on,ends_on
                   ) VALUES(%s,%s,%s,%s) RETURNING id""",
                (context_id, year_code, year_start, year_end),
            )
            academic_year_id = int(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO institute_terms(
                     context_id,academic_year_id,term_no,term_type,name,starts_on,
                     ends_on,registration_opens_at,registration_closes_at,change_deadline
                   ) VALUES(%s,%s,1,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    context_id, academic_year_id, term_type, term_name,
                    term_start, term_end, registration_opens,
                    registration_closes, change_deadline,
                ),
            )
            term_id = int(cur.fetchone()["id"])
            role_key = "administrator" if draft["relationship"] == "administrator" else str(draft["relationship"])
            upsert_role(
                cur, context_id=context_id, user_id=user_id, role_key=role_key,
                campus_id=None, faculty_id=None, department_id=None,
                approved_by=user_id,
            )
            bands = (
                [(86, 100, "5", 4, True), (71, 85.99, "4", 3, True),
                 (60, 70.99, "3", 2, True), (0, 59.99, "2", 0, False)]
                if grading_system == "five_point"
                else [(86, 100, "A", 4, True), (71, 85.99, "B", 3, True),
                      (60, 70.99, "C", 2, True), (0, 59.99, "F", 0, False)]
            )
            if grading_system != "custom":
                cur.executemany(
                    """INSERT INTO institute_grade_scale_bands(
                         context_id,scale_version,minimum_percent,maximum_percent,
                         letter_grade,grade_point,passed
                       ) VALUES(%s,1,%s,%s,%s,%s,%s)""",
                    [(context_id, *band) for band in bands],
                )
            cur.execute(
                """UPDATE institute_setup_drafts
                   SET status='confirmed',confirmed_context_id=%s,version=version+1
                   WHERE id=%s""",
                (context_id, draft_id),
            )
            audit(cur, context_id, user_id, "institute.onboarding.commit", "institute", context_id)
        return {
            "context_id": context_id,
            "status": "pending_verification",
            "reused": False,
            "created": {
                "campus_id": campus_id,
                "faculty_id": faculty_id,
                "department_id": department_id,
                "program_id": program_id,
                "academic_year_id": academic_year_id,
                "term_id": term_id,
            },
        }

    @router.get("/admin/verifications")
    def admin_verifications(
        status: str = Query(default="pending", pattern="^(pending|verified|rejected)$"),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=100),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            if not system_admin(cur, user_id):
                raise HTTPException(status_code=403, detail="Platforma administratori kerak")
            cur.execute(
                """SELECT c.id context_id,c.name,c.region,c.district,
                          p.ownership_type,p.institution_type,p.verification_status,
                          c.owner_user_id,u.full_name owner_name
                   FROM institute_profiles p JOIN learning_contexts c ON c.id=p.context_id
                   LEFT JOIN users u ON u.user_id=c.owner_user_id
                   WHERE p.verification_status=%s AND c.id>%s
                   ORDER BY c.id LIMIT %s""",
                (status, after_id or 0, limit + 1),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["context_id"] if len(rows) > limit else None}

    @router.post("/admin/verifications/{context_id}/decision")
    def decide_verification(
        context_id: int,
        request: VerificationDecision,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Tekshiruv qarorini inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            if not system_admin(cur, user_id):
                raise HTTPException(status_code=403, detail="Platforma administratori kerak")
            approved = request.decision == "verified"
            cur.execute(
                """UPDATE institute_profiles
                   SET verification_status=%s,onboarding_status=%s
                   WHERE context_id=%s AND verification_status='pending'
                   RETURNING *""",
                (request.decision, "active" if approved else "suspended", context_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=409, detail="Ariza avval ko'rib chiqilgan")
            cur.execute("UPDATE learning_contexts SET active=%s WHERE id=%s", (approved, context_id))
            audit(
                cur, context_id, user_id, "institute.verification.decision",
                "institute", context_id,
                {"decision": request.decision, "note": request.note},
            )
        return {"item": dict(row), "active": approved}

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
                    """SELECT c.id context_id,c.name,c.region,c.district,
                              p.ownership_type,p.institution_type,p.onboarding_status,
                              p.verification_status,ARRAY['system_admin']::TEXT[] roles
                       FROM learning_contexts c JOIN institute_profiles p ON p.context_id=c.id
                       WHERE c.id>%s ORDER BY c.id LIMIT %s""",
                    (after_id or 0, limit + 1),
                )
            else:
                cur.execute(
                    """SELECT c.id context_id,c.name,c.region,c.district,
                              p.ownership_type,p.institution_type,p.onboarding_status,
                              p.verification_status,array_agg(DISTINCT r.role_key) roles
                       FROM institute_role_assignments r
                       JOIN learning_contexts c ON c.id=r.context_id
                       JOIN institute_profiles p ON p.context_id=c.id
                       WHERE r.user_id=%s AND r.status='active'
                         AND r.starts_at<=NOW() AND (r.ends_at IS NULL OR r.ends_at>NOW())
                         AND c.id>%s
                       GROUP BY c.id,p.context_id ORDER BY c.id LIMIT %s""",
                    (user_id, after_id or 0, limit + 1),
                )
            rows = [dict(row) for row in cur.fetchall()]
        for row in rows:
            row["permissions"] = sorted(permissions_for(set(row["roles"])))
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["context_id"] if len(rows) > limit else None}

    @router.get("/dashboard")
    def dashboard(
        context_id: int = Query(ge=1),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            roles, global_scope, campus_ids, faculty_ids, department_ids = scope_sets(cur, context_id, user_id)
            permission_set = permissions_for(roles)
            student_only = roles == {"student"}
            cur.execute(
                """SELECT c.id context_id,c.name,c.region,c.district,
                          p.ownership_type,p.institution_type,p.onboarding_status,
                          p.verification_status,p.grading_system,p.policy_version,
                          p.default_currency,p.academic_policy,
                          COALESCE(
                            p.settings#>'{onboarding,finance,contracts_enabled}',
                            'true'::jsonb
                          )='true'::jsonb contracts_enabled,
                          COALESCE((p.integration_settings#>>'{hemis,enabled}')::BOOLEAN,FALSE) hemis_enabled,
                          COALESCE((p.integration_settings#>>'{contract,enabled}')::BOOLEAN,FALSE) contract_integration_enabled,
                          COALESCE((p.integration_settings#>>'{billing,enabled}')::BOOLEAN,FALSE) billing_enabled
                   FROM learning_contexts c JOIN institute_profiles p ON p.context_id=c.id
                   WHERE c.id=%s""",
                (context_id,),
            )
            institute = dict(cur.fetchone())
            if student_only:
                cur.execute(
                    """SELECT 1::BIGINT faculties,1::BIGINT departments,
                              1::BIGINT programs,1::BIGINT students,
                              COUNT(*) FILTER(WHERE s.status='active') active_sections
                       FROM institute_enrollments e
                       JOIN institute_course_sections s
                         ON s.context_id=e.context_id AND s.id=e.section_id
                       WHERE e.context_id=%s AND e.student_user_id=%s
                         AND e.status IN ('enrolled','completed')""",
                    (context_id, user_id),
                )
            elif global_scope:
                cur.execute(
                    """SELECT
                       (SELECT COUNT(*) FROM institute_faculties WHERE context_id=%s AND active) faculties,
                       (SELECT COUNT(*) FROM institute_departments WHERE context_id=%s AND active) departments,
                       (SELECT COUNT(*) FROM institute_programs WHERE context_id=%s AND active) programs,
                       (SELECT COUNT(*) FROM institute_students WHERE context_id=%s AND status='active') students,
                       (SELECT COUNT(*) FROM institute_course_sections WHERE context_id=%s AND status='active') active_sections""",
                    (context_id,) * 5,
                )
            else:
                cur.execute(
                    """SELECT
                       (SELECT COUNT(*) FROM institute_faculties f WHERE f.context_id=%s AND f.active
                         AND (f.campus_id=ANY(%s) OR f.id=ANY(%s)
                              OR EXISTS(SELECT 1 FROM institute_departments d WHERE d.id=ANY(%s) AND d.faculty_id=f.id))) faculties,
                       (SELECT COUNT(*) FROM institute_departments d WHERE d.context_id=%s AND d.active
                         AND (d.campus_id=ANY(%s) OR d.faculty_id=ANY(%s) OR d.id=ANY(%s))) departments,
                       (SELECT COUNT(*) FROM institute_programs p WHERE p.context_id=%s AND p.active
                         AND (p.campus_id=ANY(%s) OR p.faculty_id=ANY(%s) OR p.department_id=ANY(%s))) programs,
                       (SELECT COUNT(*) FROM institute_students s JOIN institute_programs p ON p.id=s.program_id
                         WHERE s.context_id=%s AND s.status='active'
                           AND (p.campus_id=ANY(%s) OR p.faculty_id=ANY(%s) OR p.department_id=ANY(%s))) students,
                       (SELECT COUNT(*) FROM institute_course_sections s WHERE s.context_id=%s AND s.status='active'
                         AND (s.campus_id=ANY(%s) OR s.faculty_id=ANY(%s) OR s.department_id=ANY(%s))) active_sections,
                       0::INTEGER placeholder""",
                    (
                        context_id, campus_ids, faculty_ids, department_ids,
                        context_id, campus_ids, faculty_ids, department_ids,
                        context_id, campus_ids, faculty_ids, department_ids,
                        context_id, campus_ids, faculty_ids, department_ids,
                        context_id, campus_ids, faculty_ids, department_ids,
                    ),
                )
            counts = dict(cur.fetchone())
            counts.pop("placeholder", None)
            counts["sections"] = counts["active_sections"]
            counts["overdue_contracts"] = 0
            counts["debt_amount"] = Decimal("0")
            counts["debt"] = Decimal("0")
            if "finance.view" in permission_set and institute["contracts_enabled"]:
                if student_only:
                    cur.execute(
                        """SELECT COUNT(DISTINCT c.id) FILTER(
                                    WHERE i.due_date<CURRENT_DATE
                                  ) overdue_contracts,
                                  COALESCE(SUM(i.amount-i.paid_amount),0) debt_amount
                           FROM institute_contract_installments i
                           JOIN institute_student_contracts c ON c.id=i.contract_id
                           WHERE i.context_id=%s AND i.status IN ('unpaid','partial')
                             AND c.student_user_id=%s AND c.currency=%s""",
                        (context_id, user_id, institute["default_currency"]),
                    )
                else:
                    cur.execute(
                        """SELECT COUNT(DISTINCT c.id) FILTER(
                                WHERE i.due_date<CURRENT_DATE
                              ) overdue_contracts,
                              COALESCE(SUM(i.amount-i.paid_amount),0) debt_amount
                       FROM institute_contract_installments i
                       JOIN institute_student_contracts c ON c.id=i.contract_id
                       JOIN institute_programs p ON p.id=c.program_id
                       WHERE i.context_id=%s AND i.status IN ('unpaid','partial')
                         AND c.currency=%s
                             AND (%s OR p.campus_id=ANY(%s)
                                  OR p.faculty_id=ANY(%s)
                                  OR p.department_id=ANY(%s))""",
                        (
                            context_id, institute["default_currency"], global_scope,
                            campus_ids, faculty_ids, department_ids,
                        ),
                    )
                finance_counts = cur.fetchone()
                counts["overdue_contracts"] = int(finance_counts["overdue_contracts"] or 0)
                counts["debt_amount"] = finance_counts["debt_amount"]
                counts["debt"] = finance_counts["debt_amount"]
        menus = dashboard_menu_keys(roles, permission_set)
        if not institute["contracts_enabled"]:
            menus = [key for key in menus if key != "finance"]
        return {
            "institute": institute,
            "current_user_id": user_id,
            "roles": sorted(roles),
            "permissions": sorted(permission_set),
            "menus": menus,
            "counts": counts,
            "capabilities": {
                "scope": {
                    "global": global_scope,
                    "campus_ids": campus_ids,
                    "faculty_ids": faculty_ids,
                    "department_ids": department_ids,
                },
                "attendance_policy": {
                    "warning_only": True,
                    "automatic_exclusion": False,
                },
            },
        }

    @router.get("/users/search")
    def search_users(
        context_id: int = Query(ge=1),
        q: str = Query(min_length=3, max_length=100),
        limit: int = Query(default=20, ge=1, le=50),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        literal = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        account_id = int(q.strip()) if q.strip().isdigit() else None
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(
                cur, context_id, user_id, roles_for_permission("staff.manage"),
            )
            cur.execute(
                """SELECT user_id,full_name,'#'||user_id::TEXT account_identifier
                   FROM users u WHERE (
                       u.full_name ILIKE %s ESCAPE '\\'
                       OR (%s IS NOT NULL AND u.user_id=%s)
                     ) AND (
                       %s OR EXISTS(
                         SELECT 1 FROM institute_role_assignments r
                         WHERE r.context_id=%s AND r.user_id=u.user_id
                           AND r.status='active'
                           AND (r.ends_at IS NULL OR r.ends_at>NOW())
                           AND (r.campus_id=ANY(%s) OR r.faculty_id=ANY(%s)
                                OR r.department_id=ANY(%s))
                       )
                     )
                   ORDER BY full_name,user_id LIMIT %s""",
                (
                    f"%{literal}%", account_id, account_id, global_scope,
                    context_id, campuses, faculties, departments, limit,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows, "next_cursor": None, "phone_or_email_available": False}

    @router.get("/campuses")
    def list_campuses(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT id,code,name,address,phone,active
                   FROM institute_campuses c WHERE c.context_id=%s AND c.id>%s
                     AND (%s OR c.id=ANY(%s)
                       OR EXISTS(SELECT 1 FROM institute_faculties f
                                 WHERE f.context_id=c.context_id AND f.campus_id=c.id AND f.id=ANY(%s))
                       OR EXISTS(SELECT 1 FROM institute_departments d
                                 WHERE d.context_id=c.context_id AND d.campus_id=c.id AND d.id=ANY(%s)))
                   ORDER BY c.id LIMIT %s""",
                (context_id, after_id or 0, global_scope, campuses, faculties, departments, limit + 1),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/campuses")
    def create_campus(
        request: CampusCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            require_permission(cur, request.context_id, user_id, "structure.manage", require_global=True)
            cur.execute(
                """INSERT INTO institute_campuses(context_id,code,name,address,phone)
                   VALUES(%s,%s,%s,%s,%s) RETURNING *""",
                (request.context_id, request.code.strip(), request.name.strip(), request.address, request.phone),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "campus.create", "campus", row["id"])
        return {"item": row}

    @router.get("/rooms")
    def list_rooms(
        context_id: int = Query(ge=1), campus_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT r.id,r.campus_id,r.building_id,r.code,r.name,r.room_type,
                          r.capacity,r.active,c.name campus_name
                   FROM institute_rooms r JOIN institute_campuses c ON c.id=r.campus_id
                   WHERE r.context_id=%s AND r.id>%s
                     AND (%s IS NULL OR r.campus_id=%s)
                     AND (%s OR r.campus_id=ANY(%s)
                       OR EXISTS(SELECT 1 FROM institute_faculties f
                                 WHERE f.context_id=r.context_id AND f.campus_id=r.campus_id AND f.id=ANY(%s))
                       OR EXISTS(SELECT 1 FROM institute_departments d
                                 WHERE d.context_id=r.context_id AND d.campus_id=r.campus_id AND d.id=ANY(%s)))
                   ORDER BY r.id LIMIT %s""",
                (
                    context_id, after_id or 0, campus_id, campus_id,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/rooms")
    def create_room(
        request: RoomCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_json_size(request.metadata, 20_000, "Xona metadata")
        with database() as (_, cur):
            ensure_schema(cur)
            require_permission(
                cur, request.context_id, user_id, "structure.manage",
                campus_id=request.campus_id,
            )
            cur.execute(
                """INSERT INTO institute_rooms(
                     context_id,campus_id,building_id,code,name,room_type,capacity,metadata
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING *""",
                (
                    request.context_id, request.campus_id, request.building_id,
                    request.code.strip(), request.name.strip(), request.room_type,
                    request.capacity,
                    json.dumps(request.metadata, ensure_ascii=False, default=str),
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "room.create", "room", row["id"])
        return {"item": row}

    @router.get("/faculties")
    def list_faculties(
        context_id: int = Query(ge=1), campus_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT f.id,f.campus_id,f.code,f.name,f.dean_user_id,f.active,
                          c.name campus_name,u.full_name dean_name
                   FROM institute_faculties f JOIN institute_campuses c ON c.id=f.campus_id
                   LEFT JOIN users u ON u.user_id=f.dean_user_id
                   WHERE f.context_id=%s AND f.id>%s
                     AND (%s IS NULL OR f.campus_id=%s)
                     AND (%s OR f.campus_id=ANY(%s) OR f.id=ANY(%s)
                       OR EXISTS(SELECT 1 FROM institute_departments d
                                 WHERE d.context_id=f.context_id AND d.faculty_id=f.id AND d.id=ANY(%s)))
                   ORDER BY f.id LIMIT %s""",
                (
                    context_id, after_id or 0, campus_id, campus_id,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/faculties")
    def create_faculty(
        request: FacultyCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            require_permission(
                cur, request.context_id, user_id, "structure.manage",
                campus_id=request.campus_id,
            )
            cur.execute(
                """INSERT INTO institute_faculties(
                     context_id,campus_id,code,name,dean_user_id
                   ) VALUES(%s,%s,%s,%s,%s) RETURNING *""",
                (
                    request.context_id, request.campus_id, request.code.strip(),
                    request.name.strip(), request.dean_user_id,
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "faculty.create", "faculty", row["id"])
        return {"item": row}

    @router.get("/departments")
    def list_departments(
        context_id: int = Query(ge=1), faculty_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT d.id,d.campus_id,d.faculty_id,d.code,d.name,d.head_user_id,
                          d.active,f.name faculty_name,u.full_name head_name
                   FROM institute_departments d JOIN institute_faculties f ON f.id=d.faculty_id
                   LEFT JOIN users u ON u.user_id=d.head_user_id
                   WHERE d.context_id=%s AND d.id>%s
                     AND (%s IS NULL OR d.faculty_id=%s)
                     AND (%s OR d.campus_id=ANY(%s) OR d.faculty_id=ANY(%s)
                           OR d.id=ANY(%s))
                   ORDER BY d.id LIMIT %s""",
                (
                    context_id, after_id or 0, faculty_id, faculty_id,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/departments")
    def create_department(
        request: DepartmentCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                "SELECT campus_id FROM institute_faculties WHERE context_id=%s AND id=%s AND active",
                (request.context_id, request.faculty_id),
            )
            faculty = cur.fetchone()
            if not faculty:
                raise HTTPException(status_code=404, detail="Fakultet topilmadi")
            require_permission(
                cur, request.context_id, user_id, "structure.manage",
                campus_id=int(faculty["campus_id"]), faculty_id=request.faculty_id,
            )
            cur.execute(
                """INSERT INTO institute_departments(
                     context_id,campus_id,faculty_id,code,name,head_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s) RETURNING *""",
                (
                    request.context_id, faculty["campus_id"], request.faculty_id,
                    request.code.strip(), request.name.strip(), request.head_user_id,
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "department.create", "department", row["id"])
        return {"item": row}

    @router.get("/programs")
    def list_programs(
        context_id: int = Query(ge=1), department_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT p.*,d.name department_name,f.name faculty_name
                   FROM institute_programs p
                   JOIN institute_departments d ON d.id=p.department_id
                   JOIN institute_faculties f ON f.id=p.faculty_id
                   WHERE p.context_id=%s AND p.id>%s
                     AND (%s IS NULL OR p.department_id=%s)
                     AND (%s OR p.campus_id=ANY(%s) OR p.faculty_id=ANY(%s)
                           OR p.department_id=ANY(%s))
                   ORDER BY p.id LIMIT %s""",
                (
                    context_id, after_id or 0, department_id, department_id,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/programs")
    def create_program(
        request: ProgramCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_json_size(request.policy_overrides, 30_000, "Dastur siyosati")
        with database() as (_, cur):
            ensure_schema(cur)
            scope = department_scope(cur, request.context_id, request.department_id)
            require_permission(cur, request.context_id, user_id, "structure.manage", **scope)
            cur.execute(
                """INSERT INTO institute_programs(
                     context_id,campus_id,faculty_id,department_id,code,name,
                     degree_level,study_form,language,duration_terms,target_credits,
                     policy_overrides
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                   RETURNING *""",
                (
                    request.context_id, scope["campus_id"], scope["faculty_id"],
                    request.department_id, request.code.strip(), request.name.strip(),
                    request.degree_level, request.study_form, request.language,
                    request.duration_terms, request.target_credits,
                    json.dumps(request.policy_overrides, ensure_ascii=False, default=str),
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "program.create", "program", row["id"])
        return {"item": row}

    @router.get("/academic-years")
    def list_academic_years(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=30, ge=1, le=100),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT * FROM institute_academic_years
                   WHERE context_id=%s AND id>%s ORDER BY id LIMIT %s""",
                (context_id, after_id or 0, limit + 1),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/academic-years")
    def create_academic_year(
        request: AcademicYearCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.ends_on <= request.starts_on:
            raise HTTPException(status_code=422, detail="O'quv yili tugashi boshlanishidan keyin bo'lsin")
        with database() as (_, cur):
            ensure_schema(cur)
            require_permission(cur, request.context_id, user_id, "terms.manage", require_global=True)
            cur.execute(
                """INSERT INTO institute_academic_years(context_id,code,starts_on,ends_on)
                   VALUES(%s,%s,%s,%s) RETURNING *""",
                (request.context_id, request.code.strip(), request.starts_on, request.ends_on),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "academic_year.create", "academic_year", row["id"])
        return {"item": row}

    @router.get("/terms")
    def list_terms(
        context_id: int = Query(ge=1), academic_year_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=30, ge=1, le=100),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT t.*,y.code academic_year_code
                   FROM institute_terms t JOIN institute_academic_years y ON y.id=t.academic_year_id
                   WHERE t.context_id=%s AND t.id>%s
                     AND (%s IS NULL OR t.academic_year_id=%s)
                   ORDER BY t.id LIMIT %s""",
                (context_id, after_id or 0, academic_year_id, academic_year_id, limit + 1),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/terms")
    def create_term(
        request: TermCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.ends_on <= request.starts_on:
            raise HTTPException(status_code=422, detail="Semestr tugashi boshlanishidan keyin bo'lsin")
        with database() as (_, cur):
            ensure_schema(cur)
            require_permission(cur, request.context_id, user_id, "terms.manage", require_global=True)
            cur.execute(
                """INSERT INTO institute_terms(
                     context_id,academic_year_id,term_no,term_type,name,starts_on,
                     ends_on,registration_opens_at,registration_closes_at,change_deadline
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                (
                    request.context_id, request.academic_year_id, request.term_no,
                    request.term_type, request.name.strip(), request.starts_on,
                    request.ends_on, request.registration_opens_at,
                    request.registration_closes_at, request.change_deadline,
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "term.create", "term", row["id"])
        return {"item": row}

    @router.post("/terms/{term_id}/status")
    def change_term_status(
        term_id: int,
        request: TermStatus,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Semestr holatini inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            require_permission(cur, request.context_id, user_id, "terms.manage", require_global=True)
            cur.execute(
                """SELECT * FROM institute_terms
                   WHERE context_id=%s AND id=%s FOR UPDATE""",
                (request.context_id, term_id),
            )
            current = cur.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Semestr topilmadi")
            transitions = {
                "planned": {"registration", "active", "archived"},
                "registration": {"planned", "active"},
                "active": {"grade_entry"},
                "grade_entry": {"closed"},
                "closed": {"archived"},
                "archived": set(),
            }
            if request.status not in transitions[current["status"]]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Semestr {current['status']} dan {request.status} ga o'tmaydi",
                )
            cur.execute(
                """UPDATE institute_terms SET status=%s
                   WHERE context_id=%s AND id=%s RETURNING *""",
                (request.status, request.context_id, term_id),
            )
            row = cur.fetchone()
            audit(cur, request.context_id, user_id, "term.status", "term", term_id, {"status": request.status})
        return {"item": dict(row)}

    @router.get("/staff")
    def list_staff(
        context_id: int = Query(ge=1), after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(
                cur, context_id, user_id, roles_for_permission("staff.manage"),
            )
            cur.execute(
                """SELECT r.id,r.user_id,u.full_name,r.role_key,r.status,
                          r.campus_id,r.faculty_id,r.department_id,r.starts_at,r.ends_at
                   FROM institute_role_assignments r JOIN users u ON u.user_id=r.user_id
                   WHERE r.context_id=%s AND r.id>%s AND r.role_key<>'student'
                     AND (%s OR r.campus_id=ANY(%s) OR r.faculty_id=ANY(%s)
                           OR r.department_id=ANY(%s))
                   ORDER BY r.id LIMIT %s""",
                (context_id, after_id or 0, global_scope, campuses, faculties, departments, limit + 1),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/staff")
    def assign_staff(
        request: StaffAssign,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Vakolat berishni inson tasdiqlashi kerak")
        if request.role_key not in ROLE_LABELS or request.role_key == "student":
            raise HTTPException(status_code=422, detail="Xodim roli noto'g'ri")
        if request.user_id == user_id:
            raise HTTPException(status_code=403, detail="O'zingizga rol bera olmaysiz")
        with database() as (_, cur):
            ensure_schema(cur)
            roles = require_permission(
                cur, request.context_id, user_id, "staff.manage",
                campus_id=request.campus_id, faculty_id=request.faculty_id,
                department_id=request.department_id,
                require_global=(request.campus_id is None),
            )
            if "system_admin" not in roles:
                permitted: set[str] = set()
                for role in roles:
                    permitted.update(ROLE_GRANT_MATRIX.get(role, set()))
                if request.role_key not in permitted:
                    raise HTTPException(status_code=403, detail="Bu darajadagi rolni bera olmaysiz")
            assignment_id = upsert_role(
                cur, context_id=request.context_id, user_id=request.user_id,
                role_key=request.role_key, campus_id=request.campus_id,
                faculty_id=request.faculty_id, department_id=request.department_id,
                approved_by=user_id,
            )
            audit(
                cur, request.context_id, user_id, "staff.assign", "role_assignment",
                assignment_id, {"target_user_id": request.user_id, "role": request.role_key},
            )
            cur.execute("SELECT * FROM institute_role_assignments WHERE id=%s", (assignment_id,))
            row = dict(cur.fetchone())
        return {"item": row}

    @router.post("/staff/{assignment_id}/end")
    def end_staff_assignment(
        assignment_id: int,
        request: StaffEnd,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.context_id is None:
            raise HTTPException(status_code=422, detail="context_id kerak")
        require_human(request.confirmation, "Xodim vakolatini tugatishni inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM institute_role_assignments
                   WHERE context_id=%s AND id=%s FOR UPDATE""",
                (request.context_id, assignment_id),
            )
            assignment = cur.fetchone()
            if not assignment:
                raise HTTPException(status_code=404, detail="Xodim vakolati topilmadi")
            if int(assignment["user_id"]) == user_id:
                raise HTTPException(status_code=403, detail="O'zingizning vakolatingizni tugata olmaysiz")
            actor_roles = require_permission(
                cur, request.context_id, user_id, "staff.manage",
                campus_id=assignment["campus_id"],
                faculty_id=assignment["faculty_id"],
                department_id=assignment["department_id"],
                require_global=(assignment["campus_id"] is None),
            )
            if assignment["role_key"] == "owner":
                raise HTTPException(
                    status_code=409,
                    detail="Mulkdor vakolati faqat mulkdorlikni rasmiy o'tkazish oqimida o'zgaradi",
                )
            if "system_admin" not in actor_roles:
                permitted: set[str] = set()
                for role in actor_roles:
                    permitted.update(ROLE_GRANT_MATRIX.get(role, set()))
                if assignment["role_key"] not in permitted:
                    raise HTTPException(status_code=403, detail="Bu darajadagi rolni tugata olmaysiz")
            if assignment["status"] == "ended":
                return {"item": dict(assignment), "reused": True}
            if assignment["status"] != "active":
                raise HTTPException(status_code=409, detail="Faqat faol vakolat tugatiladi")
            cur.execute(
                """UPDATE institute_role_assignments
                   SET status='ended',ends_at=NOW(),updated_at=NOW()
                   WHERE context_id=%s AND id=%s AND status='active'
                   RETURNING *""",
                (request.context_id, assignment_id),
            )
            row = dict(cur.fetchone())
            if (
                assignment["campus_id"] is None
                and assignment["faculty_id"] is None
                and assignment["department_id"] is None
            ):
                mapped = generic_role(str(assignment["role_key"]))
                cur.execute(
                    """SELECT role_key FROM institute_role_assignments
                       WHERE context_id=%s AND user_id=%s AND status='active'
                         AND campus_id IS NULL AND faculty_id IS NULL
                         AND department_id IS NULL""",
                    (request.context_id, assignment["user_id"]),
                )
                if not any(generic_role(str(item["role_key"])) == mapped for item in cur.fetchall()):
                    cur.execute(
                        """UPDATE context_memberships
                           SET status='withdrawn',ended_at=NOW(),updated_at=NOW()
                           WHERE context_id=%s AND group_id IS NULL AND user_id=%s
                             AND member_role=%s AND source='institute_v1'
                             AND status='active'""",
                        (request.context_id, assignment["user_id"], mapped),
                    )
            audit(
                cur, request.context_id, user_id, "staff.assignment.end",
                "role_assignment", assignment_id,
                {"target_user_id": assignment["user_id"], "reason": request.reason},
            )
        return {"item": row, "reused": False}

    @router.get("/course-catalog")
    def list_courses(
        context_id: int = Query(ge=1), department_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT c.*,d.name department_name
                   FROM institute_course_catalog c
                   LEFT JOIN institute_departments d ON d.id=c.department_id
                   WHERE c.context_id=%s AND c.id>%s
                     AND (%s IS NULL OR c.department_id=%s)
                     AND (%s OR c.department_id IS NULL OR c.campus_id=ANY(%s)
                           OR c.faculty_id=ANY(%s) OR c.department_id=ANY(%s))
                   ORDER BY c.id LIMIT %s""",
                (
                    context_id, after_id or 0, department_id, department_id,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/course-catalog")
    def create_course(
        request: CourseCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_json_size(request.metadata, 20_000, "Fan metadata")
        with database() as (_, cur):
            ensure_schema(cur)
            scope = department_scope(cur, request.context_id, request.department_id)
            require_permission(cur, request.context_id, user_id, "academics.manage", **scope)
            cur.execute(
                """INSERT INTO institute_course_catalog(
                     context_id,campus_id,faculty_id,department_id,code,title,
                     credit_value,lecture_hours,practice_hours,laboratory_hours,
                     independent_hours,supports_latex,description,metadata
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                   RETURNING *""",
                (
                    request.context_id, scope["campus_id"], scope["faculty_id"],
                    request.department_id, request.code.strip(), request.title.strip(),
                    request.credit_value, request.lecture_hours, request.practice_hours,
                    request.laboratory_hours, request.independent_hours,
                    request.supports_latex, request.description,
                    json.dumps(request.metadata, ensure_ascii=False, default=str),
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "course.create", "course", row["id"])
        return {"item": row}

    @router.get("/curricula")
    def list_curricula(
        context_id: int = Query(ge=1), program_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT c.*,p.name program_name,p.code program_code,
                          COALESCE(SUM(COALESCE(cc.credits_override,cat.credit_value)),0) total_credits
                   FROM institute_curricula c JOIN institute_programs p ON p.id=c.program_id
                   LEFT JOIN institute_curriculum_courses cc ON cc.curriculum_id=c.id
                   LEFT JOIN institute_course_catalog cat ON cat.id=cc.course_id
                   WHERE c.context_id=%s AND c.id>%s
                     AND (%s IS NULL OR c.program_id=%s)
                     AND (%s OR p.campus_id=ANY(%s) OR p.faculty_id=ANY(%s)
                           OR p.department_id=ANY(%s))
                   GROUP BY c.id,p.id ORDER BY c.id LIMIT %s""",
                (
                    context_id, after_id or 0, program_id, program_id,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/curricula")
    def create_curriculum(
        request: CurriculumCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            scope = program_scope(cur, request.context_id, request.program_id)
            require_permission(cur, request.context_id, user_id, "academics.manage", **scope)
            cur.execute(
                """INSERT INTO institute_curricula(
                     context_id,program_id,admission_year,version,name
                   ) VALUES(%s,%s,%s,%s,%s) RETURNING *""",
                (
                    request.context_id, request.program_id, request.admission_year,
                    request.version, request.name.strip(),
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "curriculum.create", "curriculum", row["id"])
        return {"item": row}

    @router.post("/curricula/{curriculum_id}/courses")
    def add_curriculum_course(
        curriculum_id: int,
        request: CurriculumCourseCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_json_size(request.hours_override, 10_000, "Soat sozlamalari")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT c.*,p.campus_id,p.faculty_id,p.department_id
                   FROM institute_curricula c JOIN institute_programs p ON p.id=c.program_id
                   WHERE c.context_id=%s AND c.id=%s FOR UPDATE""",
                (request.context_id, curriculum_id),
            )
            curriculum = cur.fetchone()
            if not curriculum:
                raise HTTPException(status_code=404, detail="O'quv reja topilmadi")
            if curriculum["status"] != "draft":
                raise HTTPException(status_code=409, detail="Nashr qilingan rejani tahrirlab bo'lmaydi; yangi versiya oching")
            require_permission(
                cur, request.context_id, user_id, "academics.manage",
                campus_id=int(curriculum["campus_id"]),
                faculty_id=int(curriculum["faculty_id"]),
                department_id=int(curriculum["department_id"]),
            )
            cur.execute(
                "SELECT 1 FROM institute_course_catalog WHERE context_id=%s AND id=%s AND active",
                (request.context_id, request.course_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Fan topilmadi")
            cur.execute(
                """INSERT INTO institute_curriculum_courses(
                     context_id,curriculum_id,course_id,recommended_term,
                     requirement_type,elective_block,credits_override,hours_override
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING *""",
                (
                    request.context_id, curriculum_id, request.course_id,
                    request.recommended_term, request.requirement_type,
                    request.elective_block, request.credits_override,
                    json.dumps(request.hours_override, ensure_ascii=False, default=str),
                ),
            )
            row = dict(cur.fetchone())
            for prerequisite_id in sorted(set(request.prerequisite_course_ids)):
                if prerequisite_id == request.course_id:
                    raise HTTPException(status_code=422, detail="Fan o'ziga prerequisite bo'la olmaydi")
                cur.execute(
                    """INSERT INTO institute_course_prerequisites(
                         context_id,curriculum_course_id,prerequisite_course_id
                       ) SELECT %s,%s,id FROM institute_course_catalog
                         WHERE context_id=%s AND id=%s AND active""",
                    (request.context_id, row["id"], request.context_id, prerequisite_id),
                )
                if cur.rowcount != 1:
                    raise HTTPException(status_code=404, detail="Prerequisite fan topilmadi")
            audit(cur, request.context_id, user_id, "curriculum.course.add", "curriculum_course", row["id"])
        return {"item": row}

    @router.post("/curricula/{curriculum_id}/publish")
    def publish_curriculum(
        curriculum_id: int,
        request: HumanConfirm,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.context_id is None:
            raise HTTPException(status_code=422, detail="context_id kerak")
        require_human(request.confirmation, "O'quv rejani nashr qilishni inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT c.*,p.campus_id,p.faculty_id,p.department_id,p.target_credits,
                          pr.academic_policy
                   FROM institute_curricula c JOIN institute_programs p ON p.id=c.program_id
                   JOIN institute_profiles pr ON pr.context_id=c.context_id
                   WHERE c.context_id=%s AND c.id=%s FOR UPDATE""",
                (request.context_id, curriculum_id),
            )
            curriculum = cur.fetchone()
            if not curriculum:
                raise HTTPException(status_code=404, detail="O'quv reja topilmadi")
            require_permission(
                cur, request.context_id, user_id, "academics.manage",
                campus_id=int(curriculum["campus_id"]), faculty_id=int(curriculum["faculty_id"]),
                department_id=int(curriculum["department_id"]),
            )
            cur.execute(
                """SELECT COUNT(*) item_count,
                          COALESCE(SUM(COALESCE(cc.credits_override,c.credit_value)),0) credits
                   FROM institute_curriculum_courses cc
                   JOIN institute_course_catalog c ON c.id=cc.course_id
                   WHERE cc.context_id=%s AND cc.curriculum_id=%s""",
                (request.context_id, curriculum_id),
            )
            totals = cur.fetchone()
            if int(totals["item_count"]) == 0:
                raise HTTPException(status_code=409, detail="O'quv reja bo'sh")
            if Decimal(totals["credits"]) > Decimal(curriculum["target_credits"]):
                raise HTTPException(status_code=409, detail="Reja krediti dastur limitidan oshdi")
            snapshot = dict(curriculum["academic_policy"] or {})
            cur.execute(
                """UPDATE institute_curricula
                   SET status='published',published_at=NOW(),published_by_user_id=%s,
                       policy_snapshot=%s::jsonb
                   WHERE context_id=%s AND id=%s AND status='draft' RETURNING *""",
                (
                    user_id, json.dumps(snapshot, ensure_ascii=False, default=str),
                    request.context_id, curriculum_id,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=409, detail="Reja allaqachon nashr qilingan")
            audit(cur, request.context_id, user_id, "curriculum.publish", "curriculum", curriculum_id)
        return {"item": dict(row)}

    @router.get("/cohorts")
    def list_cohorts(
        context_id: int = Query(ge=1), program_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
            cur.execute(
                """SELECT c.*,p.name program_name,u.full_name advisor_name
                   FROM institute_cohorts c JOIN institute_programs p ON p.id=c.program_id
                   LEFT JOIN users u ON u.user_id=c.advisor_user_id
                   WHERE c.context_id=%s AND c.id>%s
                     AND (%s IS NULL OR c.program_id=%s)
                     AND (%s OR p.campus_id=ANY(%s) OR p.faculty_id=ANY(%s)
                           OR p.department_id=ANY(%s))
                   ORDER BY c.id LIMIT %s""",
                (
                    context_id, after_id or 0, program_id, program_id,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/cohorts")
    def create_cohort(
        request: CohortCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            scope = program_scope(cur, request.context_id, request.program_id)
            require_permission(cur, request.context_id, user_id, "academics.manage", **scope)
            cur.execute(
                """SELECT 1 FROM institute_curricula
                   WHERE context_id=%s AND id=%s AND program_id=%s AND status='published'""",
                (request.context_id, request.curriculum_id, request.program_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=409, detail="Shu dasturga tegishli nashr qilingan reja kerak")
            cur.execute(
                """INSERT INTO course_groups(
                     context_id,group_type,delivery_mode,name,grade,external_type,
                     external_id,metadata
                   ) VALUES(%s,'institute_cohort','offline',%s,%s,'institute_cohort',
                     nextval(pg_get_serial_sequence('institute_cohorts','id')),
                     %s::jsonb) RETURNING id,external_id""",
                (
                    request.context_id, request.code.strip(), str(request.current_level),
                    json.dumps({"program_id": request.program_id}, ensure_ascii=False),
                ),
            )
            group = cur.fetchone()
            cohort_id = int(group["external_id"])
            cur.execute(
                """INSERT INTO institute_cohorts(
                     id,context_id,program_id,curriculum_id,group_id,code,
                     admission_year,current_level,study_language,advisor_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                (
                    cohort_id, request.context_id, request.program_id,
                    request.curriculum_id, group["id"], request.code.strip(),
                    request.admission_year, request.current_level,
                    request.study_language, request.advisor_user_id,
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "cohort.create", "cohort", row["id"])
        return {"item": row}

    @router.get("/sections")
    def list_sections(
        context_id: int = Query(ge=1), term_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            assignments = [] if system_admin(cur, user_id) else active_assignments(cur, context_id, user_id)
            is_student_only = bool(assignments) and all(row["role_key"] == "student" for row in assignments)
            if is_student_only:
                cur.execute(
                    """SELECT s.*,c.title course_title,c.code course_code,t.name term_name,
                              u.full_name lecturer_name
                       FROM institute_course_sections s
                       JOIN institute_enrollments e ON e.section_id=s.id AND e.context_id=s.context_id
                       JOIN institute_course_catalog c ON c.id=s.course_id
                       JOIN institute_terms t ON t.id=s.term_id
                       LEFT JOIN users u ON u.user_id=s.primary_lecturer_user_id
                       WHERE s.context_id=%s AND e.student_user_id=%s
                         AND e.status IN ('enrolled','completed') AND s.id>%s
                         AND (%s IS NULL OR s.term_id=%s)
                       ORDER BY s.id LIMIT %s""",
                    (context_id, user_id, after_id or 0, term_id, term_id, limit + 1),
                )
            else:
                _, global_scope, campuses, faculties, departments = scope_sets(cur, context_id, user_id)
                cur.execute(
                    """SELECT s.*,c.title course_title,c.code course_code,t.name term_name,
                              u.full_name lecturer_name
                       FROM institute_course_sections s
                       JOIN institute_course_catalog c ON c.id=s.course_id
                       JOIN institute_terms t ON t.id=s.term_id
                       LEFT JOIN users u ON u.user_id=s.primary_lecturer_user_id
                       WHERE s.context_id=%s AND s.id>%s
                         AND (%s IS NULL OR s.term_id=%s)
                         AND (%s OR s.campus_id=ANY(%s) OR s.faculty_id=ANY(%s)
                               OR s.department_id=ANY(%s))
                       ORDER BY s.id LIMIT %s""",
                    (
                        context_id, after_id or 0, term_id, term_id,
                        global_scope, campuses, faculties, departments, limit + 1,
                    ),
                )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/sections")
    def create_section(
        request: SectionCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_json_size(request.metadata, 20_000, "Oqim metadata")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT campus_id,faculty_id,department_id,title
                   FROM institute_course_catalog
                   WHERE context_id=%s AND id=%s AND active""",
                (request.context_id, request.course_id),
            )
            course = cur.fetchone()
            if not course or course["department_id"] is None:
                raise HTTPException(status_code=404, detail="Kafedraga biriktirilgan fan topilmadi")
            scope = {key: int(course[key]) for key in ("campus_id", "faculty_id", "department_id")}
            require_permission(cur, request.context_id, user_id, "academics.manage", **scope)
            if request.primary_lecturer_user_id is not None:
                lecturer_assignments = active_assignments(
                    cur, request.context_id, request.primary_lecturer_user_id,
                )
                if not any(
                    row["role_key"] == "lecturer"
                    and assignment_matches(
                        row, scope["campus_id"], scope["faculty_id"],
                        scope["department_id"],
                    )
                    for row in lecturer_assignments
                ):
                    raise HTTPException(
                        status_code=422,
                        detail="Asosiy o'qituvchi shu institut va kafedrada faol lecturer emas",
                    )
            cur.execute(
                "SELECT 1 FROM institute_terms WHERE context_id=%s AND id=%s AND status<>'archived'",
                (request.context_id, request.term_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Semestr topilmadi")
            if request.curriculum_course_id is not None:
                cur.execute(
                    """SELECT cc.curriculum_id,cu.program_id,p.campus_id,
                              p.faculty_id,p.department_id
                       FROM institute_curriculum_courses cc
                       JOIN institute_curricula cu ON cu.id=cc.curriculum_id
                       JOIN institute_programs p ON p.id=cu.program_id
                       WHERE cc.context_id=%s AND cc.id=%s AND cc.course_id=%s
                         AND cu.status='published'""",
                    (
                        request.context_id, request.curriculum_course_id,
                        request.course_id,
                    ),
                )
                curriculum_course = cur.fetchone()
                if not curriculum_course:
                    raise HTTPException(
                        status_code=422,
                        detail="O'quv reja fani oqim faniga mos emas",
                    )
                require_permission(
                    cur, request.context_id, user_id, "academics.manage",
                    campus_id=curriculum_course["campus_id"],
                    faculty_id=curriculum_course["faculty_id"],
                    department_id=curriculum_course["department_id"],
                )
            else:
                curriculum_course = None

            cohort_ids = sorted(set(request.cohort_ids))
            cohort_rows: list[dict[str, Any]] = []
            if cohort_ids:
                cur.execute(
                    """SELECT co.id,co.curriculum_id,co.program_id,
                              p.campus_id,p.faculty_id,p.department_id,
                              EXISTS(
                                SELECT 1 FROM institute_curriculum_courses cc
                                JOIN institute_curricula cu ON cu.id=cc.curriculum_id
                                WHERE cc.context_id=co.context_id
                                  AND cc.curriculum_id=co.curriculum_id
                                  AND cc.course_id=%s AND cu.status='published'
                                  AND (%s IS NULL OR cc.id=%s)
                              ) course_allowed
                       FROM institute_cohorts co
                       JOIN institute_programs p ON p.id=co.program_id
                       WHERE co.context_id=%s AND co.id=ANY(%s) AND co.active
                       ORDER BY co.id""",
                    (
                        request.course_id, request.curriculum_course_id,
                        request.curriculum_course_id, request.context_id,
                        cohort_ids,
                    ),
                )
                cohort_rows = [dict(item) for item in cur.fetchall()]
                if len(cohort_rows) != len(cohort_ids):
                    raise HTTPException(status_code=404, detail="Akademik guruh topilmadi")
                for cohort in cohort_rows:
                    if not cohort["course_allowed"]:
                        raise HTTPException(
                            status_code=422,
                            detail="Akademik guruh o'quv rejasida bu fan yo'q",
                        )
                    if (
                        curriculum_course is not None
                        and int(cohort["curriculum_id"])
                        != int(curriculum_course["curriculum_id"])
                    ):
                        raise HTTPException(
                            status_code=422,
                            detail="Akademik guruh va tanlangan o'quv reja fani mos emas",
                        )
                    require_permission(
                        cur, request.context_id, user_id, "academics.manage",
                        campus_id=cohort["campus_id"],
                        faculty_id=cohort["faculty_id"],
                        department_id=cohort["department_id"],
                    )
            cur.execute(
                """INSERT INTO course_groups(
                     context_id,group_type,delivery_mode,name,subject,teacher_user_id,
                     external_type,external_id,metadata
                   ) VALUES(%s,'institute_section',%s,%s,%s,%s,'institute_section',
                     nextval(pg_get_serial_sequence('institute_course_sections','id')),
                     %s::jsonb) RETURNING id,external_id""",
                (
                    request.context_id, request.delivery_mode, request.name.strip(),
                    course["title"], request.primary_lecturer_user_id,
                    json.dumps({"term_id": request.term_id}, ensure_ascii=False),
                ),
            )
            group = cur.fetchone()
            section_id = int(group["external_id"])
            cur.execute(
                """INSERT INTO institute_course_sections(
                     id,context_id,campus_id,faculty_id,department_id,term_id,
                     course_id,curriculum_course_id,group_id,code,name,
                     primary_lecturer_user_id,delivery_mode,section_type,capacity,metadata
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                   RETURNING *""",
                (
                    section_id, request.context_id, scope["campus_id"],
                    scope["faculty_id"], scope["department_id"], request.term_id,
                    request.course_id, request.curriculum_course_id, group["id"],
                    request.code.strip(), request.name.strip(),
                    request.primary_lecturer_user_id, request.delivery_mode,
                    request.section_type, request.capacity,
                    json.dumps(request.metadata, ensure_ascii=False, default=str),
                ),
            )
            row = dict(cur.fetchone())
            if request.primary_lecturer_user_id:
                cur.execute(
                    """INSERT INTO institute_section_instructors(
                         context_id,section_id,instructor_user_id,instructor_role
                       ) VALUES(%s,%s,%s,'lecturer') ON CONFLICT DO NOTHING""",
                    (request.context_id, section_id, request.primary_lecturer_user_id),
                )
            for cohort in cohort_rows:
                cur.execute(
                    """INSERT INTO institute_section_cohorts(
                         context_id,section_id,cohort_id
                       ) VALUES(%s,%s,%s)""",
                    (request.context_id, section_id, cohort["id"]),
                )
            audit(cur, request.context_id, user_id, "section.create", "section", section_id)
        return {"item": row}

    @router.post("/sections/{section_id}/activate")
    def activate_section(
        section_id: int,
        request: HumanConfirm,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.context_id is None:
            raise HTTPException(status_code=422, detail="context_id kerak")
        require_human(request.confirmation, "Oqimni faollashtirishni inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            section = section_resource(cur, request.context_id, section_id, lock=True)
            require_permission(
                cur, request.context_id, user_id, "academics.manage",
                campus_id=section["campus_id"], faculty_id=section["faculty_id"],
                department_id=section["department_id"],
            )
            if not section["primary_lecturer_user_id"]:
                raise HTTPException(status_code=409, detail="Asosiy o'qituvchini biriktiring")
            cur.execute(
                """UPDATE institute_course_sections SET status='active'
                   WHERE context_id=%s AND id=%s AND status='draft' RETURNING *""",
                (request.context_id, section_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=409, detail="Oqim draft holatida emas")
            audit(cur, request.context_id, user_id, "section.activate", "section", section_id)
        return {"item": dict(row)}

    @router.get("/enrollments")
    def list_enrollments(
        context_id: int = Query(ge=1), section_id: int | None = Query(default=None, ge=1),
        status: str | None = Query(default=None, max_length=30),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            is_system_admin = system_admin(cur, user_id)
            assignments = [] if is_system_admin else active_assignments(cur, context_id, user_id)
            student_only = bool(assignments) and all(row["role_key"] == "student" for row in assignments)
            if student_only:
                cur.execute(
                    """SELECT e.*,u.full_name student_name,s.name section_name,
                              c.title course_title
                       FROM institute_enrollments e
                       JOIN users u ON u.user_id=e.student_user_id
                       JOIN institute_course_sections s ON s.id=e.section_id
                       JOIN institute_course_catalog c ON c.id=s.course_id
                       WHERE e.context_id=%s AND e.student_user_id=%s AND e.id>%s
                         AND (%s IS NULL OR e.section_id=%s)
                         AND (%s IS NULL OR e.status=%s)
                       ORDER BY e.id LIMIT %s""",
                    (
                        context_id, user_id, after_id or 0, section_id, section_id,
                        status, status, limit + 1,
                    ),
                )
            else:
                visible_roles, global_scope, campuses, faculties, departments = scope_sets(
                    cur, context_id, user_id, ACADEMIC_MANAGER_ROLES | {"lecturer", "advisor"}
                )
                unrestricted = is_system_admin or bool(
                    visible_roles & ACADEMIC_MANAGER_ROLES
                )
                lecturer_visible = "lecturer" in visible_roles
                advisor_visible = "advisor" in visible_roles
                cur.execute(
                    """SELECT e.*,u.full_name student_name,s.name section_name,
                              c.title course_title
                       FROM institute_enrollments e
                       JOIN users u ON u.user_id=e.student_user_id
                       JOIN institute_course_sections s ON s.id=e.section_id
                       JOIN institute_course_catalog c ON c.id=s.course_id
                       WHERE e.context_id=%s AND e.id>%s
                         AND (%s IS NULL OR e.section_id=%s)
                         AND (%s IS NULL OR e.status=%s)
                         AND (%s OR s.campus_id=ANY(%s) OR s.faculty_id=ANY(%s)
                               OR s.department_id=ANY(%s))
                         AND (
                           %s
                           OR (%s AND (s.primary_lecturer_user_id=%s
                             OR EXISTS(SELECT 1 FROM institute_section_instructors si
                               WHERE si.context_id=s.context_id AND si.section_id=s.id
                                 AND si.instructor_user_id=%s AND si.active)))
                           OR (%s AND EXISTS(
                             SELECT 1 FROM institute_section_cohorts sc
                             JOIN institute_cohorts co
                               ON co.context_id=sc.context_id AND co.id=sc.cohort_id
                             WHERE sc.context_id=s.context_id AND sc.section_id=s.id
                               AND co.advisor_user_id=%s AND co.active))
                         )
                       ORDER BY e.id LIMIT %s""",
                    (
                        context_id, after_id or 0, section_id, section_id, status, status,
                        global_scope, campuses, faculties, departments,
                        unrestricted, lecturer_visible, user_id, user_id,
                        advisor_visible, user_id, limit + 1,
                    ),
                )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/enrollments")
    def create_enrollment(
        request: EnrollmentCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.status == "enrolled":
            require_human(request.confirmation, "Talabani oqimga yozishni inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                "SELECT pg_advisory_xact_lock(74131,hashtext(%s))",
                (f"institute-section-{request.context_id}-{request.section_id}",),
            )
            section = section_resource(cur, request.context_id, request.section_id, lock=True)
            require_permission(
                cur, request.context_id, user_id, "enrollments.manage",
                campus_id=section["campus_id"], faculty_id=section["faculty_id"],
                department_id=section["department_id"],
            )
            cur.execute(
                """SELECT sc.cohort_id,co.program_id,co.curriculum_id
                   FROM institute_section_cohorts sc
                   JOIN institute_cohorts co ON co.id=sc.cohort_id
                   WHERE sc.context_id=%s AND sc.section_id=%s
                   ORDER BY sc.cohort_id""",
                (request.context_id, request.section_id),
            )
            cohort_options = [dict(item) for item in cur.fetchall()]
            academic: dict[str, Any] | None = None
            if cohort_options:
                if request.cohort_id is None and len(cohort_options) > 1:
                    raise HTTPException(
                        status_code=422,
                        detail="Oqim bir nechta akademik guruhga ulangan; cohort_id ni tanlang",
                    )
                selected_cohort_id = request.cohort_id or cohort_options[0]["cohort_id"]
                academic = next(
                    (
                        item for item in cohort_options
                        if int(item["cohort_id"]) == int(selected_cohort_id)
                    ),
                    None,
                )
                if academic is None:
                    raise HTTPException(
                        status_code=422,
                        detail="Tanlangan akademik guruh bu oqimga biriktirilmagan",
                    )
            elif request.cohort_id is not None:
                raise HTTPException(
                    status_code=422,
                    detail="Bu oqimga akademik guruh biriktirilmagan",
                )
            elif section["curriculum_course_id"]:
                cur.execute(
                    """SELECT NULL::BIGINT cohort_id,c.program_id,c.id curriculum_id
                       FROM institute_curriculum_courses cc
                       JOIN institute_curricula c ON c.id=cc.curriculum_id
                       WHERE cc.context_id=%s AND cc.id=%s""",
                    (request.context_id, section["curriculum_course_id"]),
                )
                row = cur.fetchone()
                academic = dict(row) if row else None
            if not academic:
                raise HTTPException(status_code=409, detail="Oqimga o'quv reja yoki akademik guruh biriktirilmagan")
            cur.execute(
                """SELECT id,status,program_id,cohort_id,student_number
                   FROM institute_students
                   WHERE context_id=%s AND student_user_id=%s FOR UPDATE""",
                (request.context_id, request.student_user_id),
            )
            student_record = cur.fetchone()
            if student_record:
                program_mismatch = int(student_record["program_id"]) != int(academic["program_id"])
                cohort_mismatch = (
                    academic["cohort_id"] is not None
                    and int(student_record["cohort_id"] or 0) != int(academic["cohort_id"])
                )
                if program_mismatch or cohort_mismatch:
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "Talabaning dasturi yoki akademik guruhi boshqa; "
                            "avval rasmiy ko'chirish buyrug'ini kiriting"
                        ),
                    )
            else:
                cur.execute(
                    """INSERT INTO institute_students(
                         context_id,student_user_id,program_id,cohort_id,
                         student_number,status
                       ) VALUES(%s,%s,%s,%s,%s,'active')
                       RETURNING id,status,program_id,cohort_id,student_number""",
                    (
                        request.context_id, request.student_user_id,
                        academic["program_id"], academic["cohort_id"],
                        request.student_number.strip(),
                    ),
                )
                student_record = cur.fetchone()
            if student_record["status"] != "active":
                raise HTTPException(
                    status_code=409,
                    detail="Talabaning huquqiy holati faol emas; buyruq asosida tiklang",
                )
            student_record_id = int(student_record["id"])
            requested_status = request.status
            if requested_status == "enrolled":
                cur.execute(
                    """SELECT COUNT(*) occupied FROM institute_enrollments
                       WHERE context_id=%s AND section_id=%s AND status='enrolled'""",
                    (request.context_id, request.section_id),
                )
                if int(cur.fetchone()["occupied"]) >= int(section["capacity"]):
                    requested_status = "waitlisted"
            waitlist_position = None
            if requested_status == "waitlisted":
                cur.execute(
                    """SELECT COALESCE(MAX(waitlist_position),0)+1 position
                       FROM institute_enrollments
                       WHERE context_id=%s AND section_id=%s AND status='waitlisted'""",
                    (request.context_id, request.section_id),
                )
                waitlist_position = int(cur.fetchone()["position"])
            cur.execute(
                """INSERT INTO institute_enrollments(
                     context_id,section_id,student_record_id,student_user_id,
                     enrollment_type,status,waitlist_position,approved_by_user_id,
                     enrolled_at,note
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,
                     CASE WHEN %s='enrolled' THEN NOW() ELSE NULL END,%s)
                   RETURNING *""",
                (
                    request.context_id, request.section_id, student_record_id,
                    request.student_user_id, request.enrollment_type,
                    requested_status, waitlist_position,
                    user_id if requested_status == "enrolled" else None,
                    requested_status, request.note,
                ),
            )
            row = dict(cur.fetchone())
            upsert_role(
                cur, context_id=request.context_id, user_id=request.student_user_id,
                role_key="student", campus_id=section["campus_id"],
                faculty_id=section["faculty_id"], department_id=section["department_id"],
                approved_by=user_id,
            )
            cur.execute(
                """INSERT INTO context_memberships(
                     context_id,group_id,user_id,member_role,status,source,
                     approved_by_user_id,metadata
                   ) VALUES(%s,%s,%s,'student',%s,'institute_v1',%s,%s::jsonb)
                   ON CONFLICT(context_id,(COALESCE(group_id,0)),user_id,member_role)
                   DO UPDATE SET status=EXCLUDED.status,ended_at=NULL,updated_at=NOW()""",
                (
                    request.context_id, section["group_id"], request.student_user_id,
                    "active" if requested_status == "enrolled" else "pending", user_id,
                    json.dumps({"enrollment_id": row["id"]}, ensure_ascii=False),
                ),
            )
            audit(cur, request.context_id, user_id, "enrollment.create", "enrollment", row["id"])
        return {"item": row, "capacity_adjusted": requested_status != request.status}

    @router.post("/enrollments/{enrollment_id}/decision")
    def decide_enrollment(
        enrollment_id: int,
        request: EnrollmentDecision,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Qabul qarorini inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT e.*,s.campus_id,s.faculty_id,s.department_id,s.capacity,s.group_id
                   FROM institute_enrollments e
                   JOIN institute_course_sections s ON s.id=e.section_id
                   WHERE e.context_id=%s AND e.id=%s FOR UPDATE""",
                (request.context_id, enrollment_id),
            )
            enrollment = cur.fetchone()
            if not enrollment:
                raise HTTPException(status_code=404, detail="Qabul yozuvi topilmadi")
            require_permission(
                cur, request.context_id, user_id, "enrollments.manage",
                campus_id=enrollment["campus_id"], faculty_id=enrollment["faculty_id"],
                department_id=enrollment["department_id"],
            )
            allowed_transitions = {
                "pending": {"enrolled", "waitlisted", "rejected"},
                "waitlisted": {"enrolled", "withdrawn", "rejected"},
                "enrolled": {"completed", "withdrawn"},
                "completed": set(),
                "withdrawn": set(),
                "rejected": set(),
            }
            if request.status not in allowed_transitions.get(enrollment["status"], set()):
                raise HTTPException(
                    status_code=409,
                    detail=f"Qabul holati {enrollment['status']} dan {request.status} ga o'tmaydi",
                )
            cur.execute(
                "SELECT pg_advisory_xact_lock(74131,hashtext(%s))",
                (f"institute-section-{request.context_id}-{enrollment['section_id']}",),
            )
            waitlist_position = None
            if request.status == "enrolled":
                cur.execute(
                    """SELECT COUNT(*) occupied FROM institute_enrollments
                       WHERE context_id=%s AND section_id=%s AND status='enrolled' AND id<>%s""",
                    (request.context_id, enrollment["section_id"], enrollment_id),
                )
                if int(cur.fetchone()["occupied"]) >= int(enrollment["capacity"]):
                    raise HTTPException(status_code=409, detail="Oqim sig'imi to'lgan")
            elif request.status == "waitlisted":
                cur.execute(
                    """SELECT COALESCE(MAX(waitlist_position),0)+1 position
                       FROM institute_enrollments
                       WHERE context_id=%s AND section_id=%s AND status='waitlisted'""",
                    (request.context_id, enrollment["section_id"]),
                )
                waitlist_position = int(cur.fetchone()["position"])
            cur.execute(
                """UPDATE institute_enrollments SET status=%s,waitlist_position=%s,
                     approved_by_user_id=%s,
                     enrolled_at=CASE WHEN %s='enrolled' THEN COALESCE(enrolled_at,NOW()) ELSE enrolled_at END,
                     ended_at=CASE WHEN %s IN ('completed','withdrawn','rejected') THEN NOW() ELSE NULL END
                   WHERE context_id=%s AND id=%s RETURNING *""",
                (
                    request.status, waitlist_position, user_id, request.status,
                    request.status, request.context_id, enrollment_id,
                ),
            )
            row = dict(cur.fetchone())
            cur.execute(
                """UPDATE context_memberships SET status=%s,
                     ended_at=CASE WHEN %s='active' THEN NULL ELSE NOW() END,updated_at=NOW()
                   WHERE context_id=%s AND group_id=%s AND user_id=%s
                     AND member_role='student' AND source='institute_v1'""",
                (
                    (
                        "active" if request.status == "enrolled"
                        else "completed" if request.status == "completed"
                        else "pending" if request.status == "waitlisted"
                        else "rejected" if request.status == "rejected"
                        else "withdrawn"
                    ),
                    "active" if request.status == "enrolled" else "inactive",
                    request.context_id, enrollment["group_id"], enrollment["student_user_id"],
                ),
            )
            if request.status in {"rejected", "withdrawn"}:
                cur.execute(
                    """SELECT 1 FROM institute_enrollments e
                       JOIN institute_course_sections s ON s.id=e.section_id
                       WHERE e.context_id=%s AND e.student_user_id=%s
                         AND e.status IN ('pending','waitlisted','enrolled','completed')
                         AND s.campus_id=%s AND s.faculty_id=%s
                         AND s.department_id=%s LIMIT 1""",
                    (
                        request.context_id, enrollment["student_user_id"],
                        enrollment["campus_id"], enrollment["faculty_id"],
                        enrollment["department_id"],
                    ),
                )
                if not cur.fetchone():
                    cur.execute(
                        """UPDATE institute_role_assignments
                           SET status='ended',ends_at=NOW(),updated_at=NOW()
                           WHERE context_id=%s AND user_id=%s AND role_key='student'
                             AND campus_id=%s AND faculty_id=%s AND department_id=%s
                             AND status='active'""",
                        (
                            request.context_id, enrollment["student_user_id"],
                            enrollment["campus_id"], enrollment["faculty_id"],
                            enrollment["department_id"],
                        ),
                    )
            audit(cur, request.context_id, user_id, "enrollment.decision", "enrollment", enrollment_id, {"status": request.status})
        return {"item": row}

    @router.get("/schedule")
    def list_schedule(
        context_id: int = Query(ge=1), section_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            is_system_admin = system_admin(cur, user_id)
            assignments = [] if is_system_admin else active_assignments(cur, context_id, user_id)
            academic_rows = [
                row for row in assignments
                if row["role_key"] in ACADEMIC_MANAGER_ROLES
            ]
            is_lecturer = any(row["role_key"] == "lecturer" for row in assignments)
            is_student = any(row["role_key"] == "student" for row in assignments)
            is_advisor = any(row["role_key"] == "advisor" for row in assignments)
            if not (is_system_admin or academic_rows or is_lecturer or is_student or is_advisor):
                raise HTTPException(status_code=403, detail="Jadvalni ko'rishga akademik vakolat kerak")
            academic_global = any(
                row["campus_id"] is None and row["faculty_id"] is None
                and row["department_id"] is None for row in academic_rows
            )
            campuses = sorted({
                int(row["campus_id"]) for row in academic_rows
                if row["campus_id"] is not None and row["faculty_id"] is None
            })
            faculties = sorted({
                int(row["faculty_id"]) for row in academic_rows
                if row["faculty_id"] is not None and row["department_id"] is None
            })
            departments = sorted({
                int(row["department_id"]) for row in academic_rows
                if row["department_id"] is not None
            })
            cur.execute(
                """SELECT sl.*,s.name section_name,c.title course_title,
                          u.full_name teacher_name,r.name room_name
                   FROM institute_schedule_slots sl
                   JOIN institute_course_sections s ON s.id=sl.section_id
                   JOIN institute_course_catalog c ON c.id=s.course_id
                   JOIN users u ON u.user_id=sl.teacher_user_id
                   LEFT JOIN institute_rooms r ON r.id=sl.room_id
                   WHERE sl.context_id=%s AND sl.id>%s
                     AND (%s IS NULL OR sl.section_id=%s)
                     AND (
                       %s
                       OR (%s AND (%s OR s.campus_id=ANY(%s)
                            OR s.faculty_id=ANY(%s) OR s.department_id=ANY(%s)))
                       OR (%s AND (
                            s.primary_lecturer_user_id=%s OR EXISTS(
                              SELECT 1 FROM institute_section_instructors si
                              WHERE si.context_id=s.context_id AND si.section_id=s.id
                                AND si.instructor_user_id=%s AND si.active)))
                       OR (%s AND sl.status='published' AND EXISTS(
                            SELECT 1 FROM institute_enrollments e
                            WHERE e.context_id=s.context_id AND e.section_id=s.id
                              AND e.student_user_id=%s
                              AND e.status IN ('enrolled','completed')))
                       OR (%s AND sl.status='published' AND EXISTS(
                            SELECT 1 FROM institute_section_cohorts sc
                            JOIN institute_cohorts co
                              ON co.context_id=sc.context_id AND co.id=sc.cohort_id
                            WHERE sc.context_id=s.context_id AND sc.section_id=s.id
                              AND co.advisor_user_id=%s AND co.active))
                     )
                   ORDER BY sl.id LIMIT %s""",
                (
                    context_id, after_id or 0, section_id, section_id,
                    is_system_admin,
                    bool(academic_rows), academic_global, campuses, faculties,
                    departments, is_lecturer, user_id, user_id,
                    is_student, user_id, is_advisor, user_id, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/schedule")
    def create_schedule(
        request: ScheduleCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        starts_at = parse_clock(request.starts_at, "starts_at")
        ends_at = parse_clock(request.ends_at, "ends_at")
        if ends_at <= starts_at:
            raise HTTPException(status_code=422, detail="Dars tugashi boshlanishidan keyin bo'lsin")
        if request.schedule_kind == "weekly" and request.weekday is None:
            raise HTTPException(status_code=422, detail="Haftalik jadvalga weekday kerak")
        if request.schedule_kind == "dated" and request.lesson_date is None:
            raise HTTPException(status_code=422, detail="Sanali jadvalga lesson_date kerak")
        if request.status == "published":
            require_human(request.confirmation, "Jadvalni nashr qilishni inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            if request.status == "published":
                cur.execute(
                    "SELECT pg_advisory_xact_lock(74134,hashtext(%s))",
                    (f"institute-schedule-{request.context_id}",),
                )
            section = section_access(
                cur, request.context_id, request.section_id, user_id,
                write_permission="schedule.manage",
            )
            cur.execute(
                """SELECT 1 FROM institute_section_instructors
                   WHERE context_id=%s AND section_id=%s
                     AND instructor_user_id=%s AND active
                   UNION ALL SELECT 1 WHERE %s=%s LIMIT 1""",
                (
                    request.context_id, request.section_id, request.teacher_user_id,
                    request.teacher_user_id, section["primary_lecturer_user_id"],
                ),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=409, detail="O'qituvchi bu oqimga biriktirilmagan")
            if request.room_id:
                cur.execute(
                    "SELECT 1 FROM institute_rooms WHERE context_id=%s AND id=%s AND campus_id=%s AND active",
                    (request.context_id, request.room_id, section["campus_id"]),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=422, detail="Xona shu kampusga tegishli emas")
            cur.execute(
                """INSERT INTO institute_schedule_slots(
                     context_id,section_id,teacher_user_id,room_id,schedule_kind,
                     weekday,lesson_date,effective_from,effective_to,starts_at,
                     ends_at,lesson_kind,topic,status,created_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING *""",
                (
                    request.context_id, request.section_id, request.teacher_user_id,
                    request.room_id, request.schedule_kind, request.weekday,
                    request.lesson_date, request.effective_from, request.effective_to,
                    starts_at, ends_at, request.lesson_kind, request.topic,
                    request.status, user_id,
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "schedule.create", "schedule_slot", row["id"])
        return {"item": row, "cross_module_conflicts_checked": False}

    @router.post("/schedule/{slot_id}/publish")
    def publish_schedule(
        slot_id: int,
        request: HumanConfirm,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.context_id is None:
            raise HTTPException(status_code=422, detail="context_id kerak")
        require_human(request.confirmation, "Jadvalni nashr qilishni inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                "SELECT pg_advisory_xact_lock(74134,hashtext(%s))",
                (f"institute-schedule-{request.context_id}",),
            )
            cur.execute(
                "SELECT section_id FROM institute_schedule_slots WHERE context_id=%s AND id=%s",
                (request.context_id, slot_id),
            )
            item = cur.fetchone()
            if not item:
                raise HTTPException(status_code=404, detail="Jadval qatori topilmadi")
            section_access(
                cur, request.context_id, int(item["section_id"]), user_id,
                write_permission="schedule.manage",
            )
            cur.execute(
                """UPDATE institute_schedule_slots SET status='published'
                   WHERE context_id=%s AND id=%s AND status='draft' RETURNING *""",
                (request.context_id, slot_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=409, detail="Jadval draft holatida emas")
            audit(cur, request.context_id, user_id, "schedule.publish", "schedule_slot", slot_id)
        return {"item": dict(row), "cross_module_conflicts_checked": False}

    @router.get("/attendance")
    def list_attendance(
        context_id: int = Query(ge=1), section_id: int = Query(ge=1),
        student_user_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            section_access(cur, context_id, section_id, user_id)
            roles = {row["role_key"] for row in ([] if system_admin(cur, user_id) else active_assignments(cur, context_id, user_id))}
            target_student = student_user_id
            if roles == {"student"}:
                target_student = user_id
            cur.execute(
                """SELECT a.*,u.full_name student_name
                   FROM institute_attendance a JOIN users u ON u.user_id=a.student_user_id
                   WHERE a.context_id=%s AND a.section_id=%s AND a.id>%s
                     AND (%s IS NULL OR a.student_user_id=%s)
                   ORDER BY a.id LIMIT %s""",
                (context_id, section_id, after_id or 0, target_student, target_student, limit + 1),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/attendance")
    def mark_attendance(
        request: AttendanceMark,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.absent_minutes > request.scheduled_minutes:
            raise HTTPException(status_code=422, detail="Absent daqiqa dars vaqtidan oshmasin")
        with database() as (_, cur):
            ensure_schema(cur)
            section_access(
                cur, request.context_id, request.section_id, user_id,
                write_permission="attendance.write",
            )
            cur.execute(
                """SELECT id FROM institute_enrollments
                   WHERE context_id=%s AND section_id=%s AND student_user_id=%s
                     AND status='enrolled'""",
                (request.context_id, request.section_id, request.student_user_id),
            )
            enrollment = cur.fetchone()
            if not enrollment:
                raise HTTPException(status_code=409, detail="Talaba oqimga faol yozilmagan")
            if request.schedule_slot_id is not None:
                cur.execute(
                    """SELECT schedule_kind,weekday,lesson_date,effective_from,effective_to
                       FROM institute_schedule_slots
                       WHERE id=%s AND context_id=%s AND section_id=%s
                         AND status='published'""",
                    (
                        request.schedule_slot_id, request.context_id,
                        request.section_id,
                    ),
                )
                slot = cur.fetchone()
                if not slot:
                    raise HTTPException(
                        status_code=422,
                        detail="Jadval darsi shu oqimga tegishli yoki nashr qilingan emas",
                    )
                slot_matches = (
                    slot["schedule_kind"] == "dated"
                    and slot["lesson_date"] == request.lesson_date
                ) or (
                    slot["schedule_kind"] == "weekly"
                    and int(slot["weekday"]) == request.lesson_date.isoweekday()
                    and (
                        slot["effective_from"] is None
                        or slot["effective_from"] <= request.lesson_date
                    )
                    and (
                        slot["effective_to"] is None
                        or request.lesson_date <= slot["effective_to"]
                    )
                )
                if not slot_matches:
                    raise HTTPException(
                        status_code=422,
                        detail="Davomat sanasi jadval darsiga mos emas",
                    )
                cur.execute(
                    """INSERT INTO institute_attendance(
                         context_id,section_id,enrollment_id,student_user_id,
                         schedule_slot_id,lesson_date,scheduled_minutes,absent_minutes,
                         status,note,marked_by_user_id
                       ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT(
                         context_id,schedule_slot_id,student_user_id,lesson_date
                       ) WHERE schedule_slot_id IS NOT NULL
                       DO UPDATE SET enrollment_id=EXCLUDED.enrollment_id,
                         scheduled_minutes=EXCLUDED.scheduled_minutes,
                         absent_minutes=EXCLUDED.absent_minutes,status=EXCLUDED.status,
                         note=EXCLUDED.note,marked_by_user_id=EXCLUDED.marked_by_user_id,
                         updated_at=NOW() RETURNING *""",
                    (
                        request.context_id, request.section_id, enrollment["id"],
                        request.student_user_id, request.schedule_slot_id,
                        request.lesson_date, request.scheduled_minutes,
                        request.absent_minutes, request.status, request.note, user_id,
                    ),
                )
            else:
                cur.execute(
                    """INSERT INTO institute_attendance(
                         context_id,section_id,enrollment_id,student_user_id,
                         schedule_slot_id,lesson_date,scheduled_minutes,absent_minutes,
                         status,note,marked_by_user_id
                       ) VALUES(%s,%s,%s,%s,NULL,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT(
                         context_id,section_id,student_user_id,lesson_date
                       ) WHERE schedule_slot_id IS NULL
                       DO UPDATE SET enrollment_id=EXCLUDED.enrollment_id,
                         scheduled_minutes=EXCLUDED.scheduled_minutes,
                         absent_minutes=EXCLUDED.absent_minutes,status=EXCLUDED.status,
                         note=EXCLUDED.note,marked_by_user_id=EXCLUDED.marked_by_user_id,
                         updated_at=NOW() RETURNING *""",
                    (
                        request.context_id, request.section_id, enrollment["id"],
                        request.student_user_id, request.lesson_date,
                        request.scheduled_minutes, request.absent_minutes,
                        request.status, request.note, user_id,
                    ),
                )
            row = dict(cur.fetchone())
            cur.execute(
                """SELECT COALESCE(SUM(scheduled_minutes),0) scheduled,
                          COALESCE(SUM(absent_minutes) FILTER(
                            WHERE status NOT IN ('excused','sick')),0) unexcused
                   FROM institute_attendance
                   WHERE context_id=%s AND section_id=%s AND student_user_id=%s""",
                (request.context_id, request.section_id, request.student_user_id),
            )
            totals = cur.fetchone()
            course_percent = (
                Decimal(totals["unexcused"]) * 100 / Decimal(totals["scheduled"])
                if int(totals["scheduled"]) else Decimal("0")
            )
            cur.execute(
                """SELECT p.academic_policy,s.term_id FROM institute_profiles p
                   JOIN institute_course_sections s ON s.context_id=p.context_id
                   WHERE p.context_id=%s AND s.id=%s""",
                (request.context_id, request.section_id),
            )
            policy_row = cur.fetchone()
            policy = dict(policy_row["academic_policy"] or {})
            cur.execute(
                """SELECT COALESCE(SUM(a.absent_minutes) FILTER(
                            WHERE a.status NOT IN ('excused','sick')),0) minutes
                   FROM institute_attendance a
                   JOIN institute_course_sections s ON s.id=a.section_id
                   WHERE a.context_id=%s AND a.student_user_id=%s AND s.term_id=%s""",
                (request.context_id, request.student_user_id, policy_row["term_id"]),
            )
            term_minutes = int(cur.fetchone()["minutes"])
            course_limit = Decimal(str(policy.get("unexcused_course_warning_percent", 25)))
            term_limit = Decimal(str(policy.get("semester_absence_warning_hours", 74))) * 60
            warnings: list[str] = []
            if course_percent >= course_limit:
                warnings.append("course_unexcused_threshold")
            if Decimal(term_minutes) >= term_limit:
                warnings.append("semester_absence_hours_threshold")
            audit(
                cur, request.context_id, user_id, "attendance.mark", "attendance",
                row["id"], {"warnings": warnings},
            )
        return {
            "item": row,
            "warnings": warnings,
            "automatic_status_change": False,
            "human_order_required": True,
        }

    @router.get("/assessments")
    def list_assessments(
        context_id: int = Query(ge=1), section_id: int = Query(ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            section_access(cur, context_id, section_id, user_id)
            cur.execute(
                """SELECT * FROM institute_assessments
                   WHERE context_id=%s AND section_id=%s AND id>%s
                     AND (status<>'draft' OR created_by_user_id=%s)
                   ORDER BY id LIMIT %s""",
                (context_id, section_id, after_id or 0, user_id, limit + 1),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/assessments")
    def create_assessment(
        request: AssessmentCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_json_size(request.settings, 30_000, "Baholash sozlamalari")
        with database() as (_, cur):
            ensure_schema(cur)
            section_access(
                cur, request.context_id, request.section_id, user_id,
                write_permission="grades.write",
            )
            cur.execute(
                "SELECT pg_advisory_xact_lock(74135,hashtext(%s))",
                (f"institute-assessment-{request.context_id}-{request.section_id}",),
            )
            cur.execute(
                """SELECT COALESCE(SUM(weight_percent),0) total
                   FROM institute_assessments
                   WHERE context_id=%s AND section_id=%s
                     AND status IN ('draft','published')""",
                (request.context_id, request.section_id),
            )
            if Decimal(cur.fetchone()["total"]) + request.weight_percent > 100:
                raise HTTPException(status_code=409, detail="Baholash og'irliklari 100 foizdan oshdi")
            cur.execute(
                """INSERT INTO institute_assessments(
                     context_id,section_id,assessment_type,title,max_score,
                     weight_percent,due_at,settings,created_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING *""",
                (
                    request.context_id, request.section_id, request.assessment_type,
                    request.title.strip(), request.max_score, request.weight_percent,
                    request.due_at,
                    json.dumps(request.settings, ensure_ascii=False, default=str),
                    user_id,
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "assessment.create", "assessment", row["id"])
        return {"item": row}

    @router.post("/assessments/{assessment_id}/publish")
    def publish_assessment(
        assessment_id: int,
        request: HumanConfirm,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.context_id is None:
            raise HTTPException(status_code=422, detail="context_id kerak")
        require_human(request.confirmation, "Baholashni nashr qilishni inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                "SELECT section_id FROM institute_assessments WHERE context_id=%s AND id=%s",
                (request.context_id, assessment_id),
            )
            assessment = cur.fetchone()
            if not assessment:
                raise HTTPException(status_code=404, detail="Baholash topilmadi")
            section_access(
                cur, request.context_id, int(assessment["section_id"]), user_id,
                write_permission="grades.write",
            )
            cur.execute(
                """UPDATE institute_assessments SET status='published',published_at=NOW()
                   WHERE context_id=%s AND id=%s AND status='draft' RETURNING *""",
                (request.context_id, assessment_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=409, detail="Baholash draft holatida emas")
            audit(cur, request.context_id, user_id, "assessment.publish", "assessment", assessment_id)
        return {"item": dict(row)}

    @router.get("/grades")
    def list_grades(
        context_id: int = Query(ge=1), section_id: int = Query(ge=1),
        student_user_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            section_access(cur, context_id, section_id, user_id)
            assignments = [] if system_admin(cur, user_id) else active_assignments(cur, context_id, user_id)
            if assignments and all(row["role_key"] == "student" for row in assignments):
                student_user_id = user_id
            cur.execute(
                """SELECT g.*,a.title assessment_title,a.weight_percent,u.full_name student_name
                   FROM institute_grade_entries g
                   JOIN institute_assessments a ON a.id=g.assessment_id
                   JOIN users u ON u.user_id=g.student_user_id
                   WHERE g.context_id=%s AND g.section_id=%s AND g.id>%s
                     AND (%s IS NULL OR g.student_user_id=%s)
                   ORDER BY g.id LIMIT %s""",
                (
                    context_id, section_id, after_id or 0,
                    student_user_id, student_user_id, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/grades")
    def create_grade(
        request: GradeCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT a.*,e.student_user_id,e.section_id enrollment_section
                   FROM institute_assessments a
                   JOIN institute_enrollments e ON e.id=%s AND e.context_id=a.context_id
                   WHERE a.context_id=%s AND a.id=%s AND a.status='published'
                     AND e.status='enrolled'""",
                (request.enrollment_id, request.context_id, request.assessment_id),
            )
            item = cur.fetchone()
            if not item or int(item["section_id"]) != int(item["enrollment_section"]):
                raise HTTPException(status_code=404, detail="Baholash yoki talaba yozuvi mos emas")
            if request.score > Decimal(item["max_score"]):
                raise HTTPException(status_code=422, detail="Ball maksimal balldan oshmasin")
            section_access(
                cur, request.context_id, int(item["section_id"]), user_id,
                write_permission="grades.write",
            )
            reused = None
            if request.idempotency_key:
                fingerprint = request_fingerprint(
                    "grade.write",
                    {
                        "assessment_id": request.assessment_id,
                        "enrollment_id": request.enrollment_id,
                        "score": str(request.score),
                        "feedback": request.feedback,
                    },
                )
                reused = claim_request(
                    cur, request.context_id, request.idempotency_key,
                    user_id, "grade.write", fingerprint,
                )
                if reused:
                    cur.execute("SELECT * FROM institute_grade_entries WHERE context_id=%s AND id=%s", (request.context_id, reused))
                    return {"item": dict(cur.fetchone()), "reused": True}
            cur.execute(
                """INSERT INTO institute_grade_entries(
                     context_id,assessment_id,section_id,enrollment_id,
                     student_user_id,score,max_score,feedback,idempotency_key,
                     graded_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT(context_id,assessment_id,enrollment_id)
                   DO UPDATE SET score=EXCLUDED.score,max_score=EXCLUDED.max_score,
                     feedback=EXCLUDED.feedback,graded_by_user_id=EXCLUDED.graded_by_user_id,
                     graded_at=NOW(),updated_at=NOW() RETURNING *""",
                (
                    request.context_id, request.assessment_id, item["section_id"],
                    request.enrollment_id, item["student_user_id"], request.score,
                    item["max_score"], request.feedback, request.idempotency_key,
                    user_id,
                ),
            )
            row = dict(cur.fetchone())
            if request.idempotency_key:
                finish_request(cur, request.context_id, request.idempotency_key, int(row["id"]))
            audit(cur, request.context_id, user_id, "grade.write", "grade", row["id"])
        return {"item": row, "reused": False}

    @router.post("/course-results/{enrollment_id}/finalize")
    def finalize_result(
        enrollment_id: int,
        request: FinalizeResult,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Yakuniy bahoni inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT e.*,s.course_id,s.campus_id,s.faculty_id,s.department_id,
                          c.credit_value,p.policy_version
                   FROM institute_enrollments e
                   JOIN institute_course_sections s ON s.id=e.section_id
                   JOIN institute_course_catalog c ON c.id=s.course_id
                   JOIN institute_profiles p ON p.context_id=e.context_id
                   WHERE e.context_id=%s AND e.id=%s FOR UPDATE""",
                (request.context_id, enrollment_id),
            )
            enrollment = cur.fetchone()
            if not enrollment:
                raise HTTPException(status_code=404, detail="Talaba oqim yozuvi topilmadi")
            require_permission(
                cur, request.context_id, user_id, "grades.finalize",
                campus_id=enrollment["campus_id"], faculty_id=enrollment["faculty_id"],
                department_id=enrollment["department_id"],
            )
            fingerprint = request_fingerprint(
                "course_result.finalize", {"enrollment_id": enrollment_id},
            )
            reused = claim_request(
                cur, request.context_id, request.idempotency_key,
                user_id, "course_result.finalize", fingerprint,
            )
            if reused:
                cur.execute(
                    "SELECT * FROM institute_course_results WHERE context_id=%s AND id=%s",
                    (request.context_id, reused),
                )
                return {"item": dict(cur.fetchone()), "reused": True}
            if enrollment["status"] != "enrolled":
                raise HTTPException(
                    status_code=409,
                    detail="Faqat faol yozilgan talabaning natijasi yakunlanadi",
                )
            cur.execute(
                """SELECT a.id,a.max_score,a.weight_percent,g.score
                   FROM institute_assessments a
                   LEFT JOIN institute_grade_entries g
                     ON g.assessment_id=a.id AND g.enrollment_id=%s
                   WHERE a.context_id=%s AND a.section_id=%s AND a.status='published'
                   ORDER BY a.id""",
                (enrollment_id, request.context_id, enrollment["section_id"]),
            )
            grades = cur.fetchall()
            if not grades or any(row["score"] is None for row in grades):
                raise HTTPException(status_code=409, detail="Barcha e'lon qilingan baholashlar kiritilmagan")
            try:
                final_percent = weighted_percent(
                    WeightedMark(
                        Decimal(row["score"]), Decimal(row["max_score"]),
                        Decimal(row["weight_percent"]),
                    )
                    for row in grades
                )
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            cur.execute(
                """SELECT minimum_percent,maximum_percent,letter_grade,grade_point,passed
                   FROM institute_grade_scale_bands
                   WHERE context_id=%s AND scale_version=%s AND active
                   ORDER BY minimum_percent""",
                (request.context_id, enrollment["policy_version"]),
            )
            bands = [
                GradeBand(
                    Decimal(row["minimum_percent"]), Decimal(row["maximum_percent"]),
                    str(row["letter_grade"]), Decimal(row["grade_point"]), bool(row["passed"]),
                )
                for row in cur.fetchall()
            ]
            if not bands:
                raise HTTPException(status_code=409, detail="Baholash shkalasi sozlanmagan")
            try:
                band = select_grade_band(final_percent, bands)
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            cur.execute(
                "SELECT COALESCE(MAX(attempt_no),0)+1 attempt FROM institute_course_results WHERE context_id=%s AND enrollment_id=%s",
                (request.context_id, enrollment_id),
            )
            attempt_no = int(cur.fetchone()["attempt"])
            cur.execute(
                """UPDATE institute_course_results SET status='superseded'
                   WHERE context_id=%s AND enrollment_id=%s AND status='finalized'""",
                (request.context_id, enrollment_id),
            )
            cur.execute(
                """INSERT INTO institute_course_results(
                     context_id,section_id,enrollment_id,student_user_id,credits,
                     final_percent,letter_grade,grade_point,passed,attempt_no,
                     finalized_by_user_id,idempotency_key
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                (
                    request.context_id, enrollment["section_id"], enrollment_id,
                    enrollment["student_user_id"], enrollment["credit_value"],
                    final_percent, band.letter_grade, band.grade_point, band.passed,
                    attempt_no, user_id, request.idempotency_key,
                ),
            )
            row = dict(cur.fetchone())
            cur.execute(
                "UPDATE institute_enrollments SET status='completed',ended_at=NOW() WHERE context_id=%s AND id=%s",
                (request.context_id, enrollment_id),
            )
            finish_request(cur, request.context_id, request.idempotency_key, int(row["id"]))
            audit(cur, request.context_id, user_id, "course_result.finalize", "course_result", row["id"])
        return {"item": row, "reused": False}

    @router.get("/course-results")
    def list_course_results(
        context_id: int = Query(ge=1), student_user_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            is_system_admin = system_admin(cur, user_id)
            assignments = [] if is_system_admin else active_assignments(cur, context_id, user_id)
            student_only = bool(assignments) and all(
                row["role_key"] == "student" for row in assignments
            )
            if student_only:
                student_user_id = user_id
                global_scope, campuses, faculties, departments = False, [], [], []
                lecturer_only = False
            else:
                roles, global_scope, campuses, faculties, departments = scope_sets(
                    cur, context_id, user_id, roles_for_permission("grades.write"),
                )
                lecturer_only = roles == {"lecturer"}
            cur.execute(
                """SELECT r.*,s.name section_name,c.code course_code,
                          c.title course_title,t.name term_name,u.full_name student_name,
                          st.student_number
                   FROM institute_course_results r
                   JOIN institute_course_sections s ON s.id=r.section_id
                   JOIN institute_course_catalog c ON c.id=s.course_id
                   JOIN institute_terms t ON t.id=s.term_id
                   JOIN users u ON u.user_id=r.student_user_id
                   JOIN institute_students st
                     ON st.context_id=r.context_id
                    AND st.student_user_id=r.student_user_id
                   WHERE r.context_id=%s AND r.id>%s
                     AND (%s IS NULL OR r.student_user_id=%s)
                     AND (
                       (%s AND r.student_user_id=%s)
                       OR (NOT %s
                         AND (%s OR s.campus_id=ANY(%s)
                              OR s.faculty_id=ANY(%s)
                              OR s.department_id=ANY(%s))
                         AND (NOT %s OR s.primary_lecturer_user_id=%s
                              OR EXISTS(
                                SELECT 1 FROM institute_section_instructors si
                                WHERE si.context_id=s.context_id
                                  AND si.section_id=s.id
                                  AND si.instructor_user_id=%s AND si.active)))
                     )
                   ORDER BY r.id LIMIT %s""",
                (
                    context_id, after_id or 0, student_user_id,
                    student_user_id, student_only, user_id, student_only,
                    global_scope, campuses, faculties, departments,
                    lecturer_only, user_id, user_id, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.get("/transcripts")
    def list_transcripts(
        context_id: int = Query(ge=1), student_user_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=30, ge=1, le=100),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            is_system_admin = system_admin(cur, user_id)
            assignments = [] if is_system_admin else active_assignments(cur, context_id, user_id)
            student_only = bool(assignments) and all(
                row["role_key"] == "student" for row in assignments
            )
            if student_only:
                student_user_id = user_id
                global_scope, campuses, faculties, departments = False, [], [], []
            else:
                _, global_scope, campuses, faculties, departments = scope_sets(
                    cur, context_id, user_id,
                    roles_for_permission("transcripts.issue"),
                )
            cur.execute(
                """SELECT tr.id,tr.student_user_id,tr.transcript_no,
                          tr.verification_code,tr.cumulative_gpa,
                          tr.cumulative_gpa gpa,tr.attempted_credits,
                          tr.earned_credits,tr.earned_credits total_credits,
                          tr.issued_by_user_id,tr.issued_at,tr.revoked_at,
                          st.student_number,u.full_name student_name
                   FROM institute_transcript_snapshots tr
                   JOIN institute_students st
                     ON st.context_id=tr.context_id
                    AND st.student_user_id=tr.student_user_id
                   JOIN institute_programs p ON p.id=st.program_id
                   JOIN users u ON u.user_id=tr.student_user_id
                   WHERE tr.context_id=%s AND tr.id>%s
                     AND (%s IS NULL OR tr.student_user_id=%s)
                     AND (
                       (%s AND tr.student_user_id=%s)
                       OR (NOT %s AND (%s OR p.campus_id=ANY(%s)
                           OR p.faculty_id=ANY(%s) OR p.department_id=ANY(%s)))
                     )
                   ORDER BY tr.id LIMIT %s""",
                (
                    context_id, after_id or 0, student_user_id,
                    student_user_id, student_only, user_id, student_only,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/transcripts/{student_id}/issue")
    def issue_transcript(
        student_id: int,
        request: TranscriptIssue,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.context_id is None:
            raise HTTPException(status_code=422, detail="context_id kerak")
        require_human(request.confirmation, "Transkriptni registrator tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT s.id student_record_id,s.student_user_id,s.student_number,
                          s.status,p.name program_name,p.campus_id,p.faculty_id,
                          p.department_id,u.full_name,pr.academic_policy
                   FROM institute_students s JOIN institute_programs p ON p.id=s.program_id
                   JOIN users u ON u.user_id=s.student_user_id
                   JOIN institute_profiles pr ON pr.context_id=s.context_id
                   WHERE s.context_id=%s AND s.id=%s""",
                (request.context_id, student_id),
            )
            student = cur.fetchone()
            if not student:
                raise HTTPException(status_code=404, detail="Talaba topilmadi")
            require_permission(
                cur, request.context_id, user_id, "transcripts.issue",
                campus_id=student["campus_id"], faculty_id=student["faculty_id"],
                department_id=student["department_id"],
            )
            fingerprint = request_fingerprint(
                "transcript.issue", {"student_record_id": student_id},
            )
            reused = claim_request(
                cur, request.context_id, request.idempotency_key,
                user_id, "transcript.issue", fingerprint,
            )
            if reused:
                cur.execute(
                    "SELECT * FROM institute_transcript_snapshots WHERE context_id=%s AND id=%s",
                    (request.context_id, reused),
                )
                reused_row = dict(cur.fetchone())
                reused_row.update({
                    "gpa": reused_row["cumulative_gpa"],
                    "total_credits": reused_row["earned_credits"],
                    "student_name": student["full_name"],
                    "student_number": student["student_number"],
                })
                return {
                    "item": reused_row, "reused": True,
                    "official_e_signature": False, "hemis_synced": False,
                }
            cur.execute(
                """SELECT r.id,r.credits,r.final_percent,r.letter_grade,
                          r.grade_point,r.passed,r.finalized_at,c.id course_id,
                          c.code course_code,c.title course_title,t.name term_name,
                          t.starts_on term_start
                   FROM institute_course_results r
                   JOIN institute_course_sections s ON s.id=r.section_id
                   JOIN institute_course_catalog c ON c.id=s.course_id
                   JOIN institute_terms t ON t.id=s.term_id
                   WHERE r.context_id=%s AND r.student_user_id=%s
                     AND r.status='finalized'
                   ORDER BY t.starts_on,c.code,r.id""",
                (request.context_id, student["student_user_id"]),
            )
            all_results = [dict(row) for row in cur.fetchall()]
            if not all_results:
                raise HTTPException(status_code=409, detail="Yakunlangan fan natijalari yo'q")
            attempt_policy = str(
                dict(student["academic_policy"] or {}).get(
                    "transcript_attempt_policy", "latest",
                )
            )
            if attempt_policy not in {"latest", "best", "all"}:
                attempt_policy = "latest"
            results = select_transcript_attempts(all_results, attempt_policy)
            gpa = calculate_gpa(
                CreditResult(Decimal(row["credits"]), Decimal(row["grade_point"]), bool(row["passed"]))
                for row in results
            )
            attempted = sum((Decimal(row["credits"]) for row in results), Decimal("0"))
            earned = sum((Decimal(row["credits"]) for row in results if row["passed"]), Decimal("0"))
            snapshot = {
                "student": {
                    "user_id": int(student["student_user_id"]),
                    "student_number": student["student_number"],
                    "full_name": student["full_name"],
                    "program": student["program_name"],
                    "status": student["status"],
                },
                "results": results,
                "gpa": str(gpa),
                "attempted_credits": str(attempted),
                "earned_credits": str(earned),
                "attempt_policy": attempt_policy,
                "issued_at": datetime.now(timezone.utc).isoformat(),
            }
            encoded = json.dumps(snapshot, ensure_ascii=False, default=str, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(encoded).hexdigest()
            verification_code = secrets.token_urlsafe(24)
            transcript_no = f"TR-{request.context_id}-{student_id}-{datetime.now(timezone.utc):%Y%m%d%H%M%S%f}"
            cur.execute(
                """INSERT INTO institute_transcript_snapshots(
                     context_id,student_user_id,transcript_no,verification_code,
                     cumulative_gpa,attempted_credits,earned_credits,snapshot,
                     snapshot_hash,issued_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s) RETURNING *""",
                (
                    request.context_id, student["student_user_id"], transcript_no,
                    verification_code, gpa, attempted, earned,
                    json.dumps(snapshot, ensure_ascii=False, default=str), digest, user_id,
                ),
            )
            row = dict(cur.fetchone())
            finish_request(
                cur, request.context_id, request.idempotency_key, int(row["id"]),
            )
            audit(cur, request.context_id, user_id, "transcript.issue", "transcript", row["id"])
        row.update({
            "gpa": row["cumulative_gpa"],
            "total_credits": row["earned_credits"],
            "student_name": student["full_name"],
            "student_number": student["student_number"],
        })
        return {
            "item": row, "reused": False,
            "official_e_signature": False, "hemis_synced": False,
        }

    @router.get("/contracts")
    def list_contracts(
        context_id: int = Query(ge=1), student_user_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            is_system_admin = system_admin(cur, user_id)
            assignments = [] if is_system_admin else active_assignments(cur, context_id, user_id)
            student_only = bool(assignments) and all(
                row["role_key"] == "student" for row in assignments
            )
            if student_only:
                student_user_id = user_id
                global_scope, campuses, faculties, departments = False, [], [], []
            else:
                _, global_scope, campuses, faculties, departments = scope_sets(
                    cur, context_id, user_id, roles_for_permission("finance.view"),
                )
            cur.execute(
                """SELECT c.*,u.full_name student_name,p.name program_name,y.code academic_year_code
                   FROM institute_student_contracts c
                   JOIN users u ON u.user_id=c.student_user_id
                   JOIN institute_programs p ON p.id=c.program_id
                   JOIN institute_academic_years y ON y.id=c.academic_year_id
                   WHERE c.context_id=%s AND c.id>%s
                     AND (%s IS NULL OR c.student_user_id=%s)
                     AND (
                       (%s AND c.student_user_id=%s)
                       OR (NOT %s AND (%s OR p.campus_id=ANY(%s)
                           OR p.faculty_id=ANY(%s) OR p.department_id=ANY(%s)))
                     )
                   ORDER BY c.id LIMIT %s""",
                (
                    context_id, after_id or 0, student_user_id,
                    student_user_id, student_only, user_id, student_only,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/contracts")
    def create_contract(
        request: ContractCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "Shartnomani inson tasdiqlashi kerak")
        if request.ends_on < request.starts_on or request.scholarship_amount > request.total_amount:
            raise HTTPException(status_code=422, detail="Shartnoma summa yoki sanasi noto'g'ri")
        with database() as (_, cur):
            ensure_schema(cur)
            scope = program_scope(cur, request.context_id, request.program_id)
            require_permission(cur, request.context_id, user_id, "finance.manage", **scope)
            default_currency, contracts_enabled = finance_policy(cur, request.context_id)
            if not contracts_enabled:
                raise HTTPException(status_code=409, detail="Institutda kontrakt moduli o'chirilgan")
            if request.currency.upper() != default_currency:
                raise HTTPException(
                    status_code=422,
                    detail=f"Shartnoma valutasi institutning {default_currency} valutasiga mos bo'lsin",
                )
            cur.execute(
                """SELECT id FROM institute_students
                   WHERE context_id=%s AND student_user_id=%s AND program_id=%s""",
                (request.context_id, request.student_user_id, request.program_id),
            )
            student = cur.fetchone()
            if not student:
                raise HTTPException(status_code=404, detail="Talaba shu dasturda topilmadi")
            cur.execute(
                """INSERT INTO institute_student_contracts(
                     context_id,student_record_id,student_user_id,program_id,
                     academic_year_id,contract_no,contract_type,total_amount,
                     scholarship_amount,currency,payer_user_id,starts_on,ends_on,
                     status,created_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active',%s)
                   RETURNING *""",
                (
                    request.context_id, student["id"], request.student_user_id,
                    request.program_id, request.academic_year_id,
                    request.contract_no.strip(), request.contract_type,
                    request.total_amount, request.scholarship_amount,
                    request.currency.upper(), request.payer_user_id,
                    request.starts_on, request.ends_on, user_id,
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "contract.create", "contract", row["id"])
        return {"item": row, "external_contract_synced": False}

    @router.post("/contracts/{contract_id}/installments")
    def create_installments(
        contract_id: int,
        request: InstallmentsCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "To'lov rejasini inson tasdiqlashi kerak")
        if len({item.installment_no for item in request.items}) != len(request.items):
            raise HTTPException(status_code=422, detail="To'lov bosqich raqamlari takrorlanmasin")
        with database() as (_, cur):
            ensure_schema(cur)
            _, contracts_enabled = finance_policy(cur, request.context_id)
            if not contracts_enabled:
                raise HTTPException(status_code=409, detail="Institutda kontrakt moduli o'chirilgan")
            cur.execute(
                """SELECT c.*,p.campus_id,p.faculty_id,p.department_id
                   FROM institute_student_contracts c
                   JOIN institute_programs p ON p.id=c.program_id
                   WHERE c.context_id=%s AND c.id=%s FOR UPDATE""",
                (request.context_id, contract_id),
            )
            contract = cur.fetchone()
            if not contract:
                raise HTTPException(status_code=404, detail="Shartnoma topilmadi")
            require_permission(
                cur, request.context_id, user_id, "finance.manage",
                campus_id=contract["campus_id"], faculty_id=contract["faculty_id"],
                department_id=contract["department_id"],
            )
            cur.execute(
                "SELECT COALESCE(SUM(amount),0) amount FROM institute_contract_installments WHERE context_id=%s AND contract_id=%s AND status<>'cancelled'",
                (request.context_id, contract_id),
            )
            existing = Decimal(cur.fetchone()["amount"])
            requested = sum((item.amount for item in request.items), Decimal("0"))
            payable = Decimal(contract["total_amount"]) - Decimal(contract["scholarship_amount"])
            if existing + requested > payable:
                raise HTTPException(status_code=409, detail="To'lov rejasi shartnoma summasidan oshdi")
            rows: list[dict[str, Any]] = []
            for item in request.items:
                cur.execute(
                    """INSERT INTO institute_contract_installments(
                         context_id,contract_id,installment_no,due_date,amount
                       ) VALUES(%s,%s,%s,%s,%s) RETURNING *""",
                    (
                        request.context_id, contract_id, item.installment_no,
                        item.due_date, item.amount,
                    ),
                )
                rows.append(dict(cur.fetchone()))
            audit(cur, request.context_id, user_id, "installments.create", "contract", contract_id, {"count": len(rows)})
        return {"items": rows}

    @router.post("/payments")
    def create_payment(
        request: PaymentCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        require_human(request.confirmation, "To'lovni kassir inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            default_currency, contracts_enabled = finance_policy(cur, request.context_id)
            if not contracts_enabled:
                raise HTTPException(status_code=409, detail="Institutda kontrakt moduli o'chirilgan")
            cur.execute(
                """SELECT i.*,c.currency contract_currency,p.campus_id,p.faculty_id,p.department_id
                   FROM institute_contract_installments i
                   JOIN institute_student_contracts c ON c.id=i.contract_id
                   JOIN institute_programs p ON p.id=c.program_id
                   WHERE i.context_id=%s AND i.id=%s AND i.contract_id=%s FOR UPDATE""",
                (request.context_id, request.installment_id, request.contract_id),
            )
            installment = cur.fetchone()
            if not installment:
                raise HTTPException(status_code=404, detail="To'lov bosqichi topilmadi")
            require_permission(
                cur, request.context_id, user_id, "finance.manage",
                campus_id=installment["campus_id"], faculty_id=installment["faculty_id"],
                department_id=installment["department_id"],
            )
            if request.currency.upper() != default_currency:
                raise HTTPException(
                    status_code=422,
                    detail=f"To'lov valutasi institutning {default_currency} valutasiga mos bo'lsin",
                )
            if request.currency.upper() != str(installment["contract_currency"]).upper():
                raise HTTPException(status_code=422, detail="To'lov valutasi shartnomaga mos emas")
            fingerprint = request_fingerprint(
                "payment.create",
                {
                    "contract_id": request.contract_id,
                    "installment_id": request.installment_id,
                    "amount": str(request.amount),
                    "currency": request.currency.upper(),
                    "payment_method": request.payment_method,
                    "reference": request.reference,
                    "paid_at": request.paid_at,
                },
            )
            reused = claim_request(
                cur, request.context_id, request.idempotency_key,
                user_id, "payment.create", fingerprint,
            )
            if reused:
                cur.execute(
                    "SELECT * FROM institute_payments WHERE context_id=%s AND id=%s",
                    (request.context_id, reused),
                )
                return {"item": dict(cur.fetchone()), "reused": True}
            remaining = Decimal(installment["amount"]) - Decimal(installment["paid_amount"])
            if request.amount > remaining:
                raise HTTPException(status_code=409, detail="To'lov qolgan summadan oshdi")
            cur.execute(
                """INSERT INTO institute_payments(
                     context_id,contract_id,installment_id,amount,currency,
                     payment_method,reference,idempotency_key,received_by_user_id,paid_at
                   ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,COALESCE(%s,NOW()))
                   RETURNING *""",
                (
                    request.context_id, request.contract_id, request.installment_id,
                    request.amount, request.currency.upper(), request.payment_method,
                    request.reference, request.idempotency_key, user_id, request.paid_at,
                ),
            )
            row = dict(cur.fetchone())
            new_paid = Decimal(installment["paid_amount"]) + request.amount
            cur.execute(
                """UPDATE institute_contract_installments
                   SET paid_amount=%s,status=CASE WHEN %s=amount THEN 'paid' ELSE 'partial' END
                   WHERE context_id=%s AND id=%s""",
                (new_paid, new_paid, request.context_id, request.installment_id),
            )
            finish_request(cur, request.context_id, request.idempotency_key, int(row["id"]))
            audit(cur, request.context_id, user_id, "payment.create", "payment", row["id"], {"amount": str(request.amount)})
        return {"item": row, "reused": False, "gateway_processed": False}

    @router.get("/debts")
    def list_debts(
        context_id: int = Query(ge=1), student_user_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            is_system_admin = system_admin(cur, user_id)
            assignments = [] if is_system_admin else active_assignments(cur, context_id, user_id)
            student_only = bool(assignments) and all(
                row["role_key"] == "student" for row in assignments
            )
            if student_only:
                student_user_id = user_id
                global_scope, campuses, faculties, departments = False, [], [], []
            else:
                _, global_scope, campuses, faculties, departments = scope_sets(
                    cur, context_id, user_id, roles_for_permission("finance.view"),
                )
            cur.execute(
                """SELECT i.id installment_id,i.contract_id,c.contract_no,c.student_user_id,
                          u.full_name student_name,i.installment_no,i.due_date,i.amount,
                          i.paid_amount,(i.amount-i.paid_amount) debt,
                          (i.amount-i.paid_amount) remaining_amount,c.currency,i.status
                   FROM institute_contract_installments i
                   JOIN institute_student_contracts c ON c.id=i.contract_id
                   JOIN institute_programs p ON p.id=c.program_id
                   JOIN users u ON u.user_id=c.student_user_id
                   WHERE i.context_id=%s AND i.id>%s AND i.status IN ('unpaid','partial')
                     AND (%s IS NULL OR c.student_user_id=%s)
                     AND (
                       (%s AND c.student_user_id=%s)
                       OR (NOT %s AND (%s OR p.campus_id=ANY(%s)
                           OR p.faculty_id=ANY(%s) OR p.department_id=ANY(%s)))
                     )
                   ORDER BY i.id LIMIT %s""",
                (
                    context_id, after_id or 0, student_user_id,
                    student_user_id, student_only, user_id, student_only,
                    global_scope, campuses, faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["installment_id"] if len(rows) > limit else None}

    @router.get("/workloads")
    def list_workloads(
        context_id: int = Query(ge=1), term_id: int | None = Query(default=None, ge=1),
        staff_user_id: int | None = Query(default=None, ge=1),
        after_id: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            is_system_admin = system_admin(cur, user_id)
            assignments = [] if is_system_admin else active_assignments(cur, context_id, user_id)
            assignment_roles = {row["role_key"] for row in assignments}
            lecturer_only = (
                "lecturer" in assignment_roles
                and "workload.manage" not in permissions_for(assignment_roles)
            )
            if lecturer_only:
                staff_user_id = user_id
                global_scope, campuses, faculties, departments = True, [], [], []
            else:
                _, global_scope, campuses, faculties, departments = scope_sets(
                    cur, context_id, user_id,
                    roles_for_permission("workload.manage"),
                )
            cur.execute(
                """SELECT w.*,u.full_name staff_name,s.name section_name,t.name term_name
                   FROM institute_staff_workloads w JOIN users u ON u.user_id=w.staff_user_id
                   JOIN institute_course_sections s ON s.id=w.section_id
                   JOIN institute_terms t ON t.id=w.term_id
                   WHERE w.context_id=%s AND w.id>%s
                     AND (%s IS NULL OR w.term_id=%s)
                     AND (%s IS NULL OR w.staff_user_id=%s)
                     AND (%s OR s.campus_id=ANY(%s)
                          OR s.faculty_id=ANY(%s) OR s.department_id=ANY(%s))
                   ORDER BY w.id LIMIT %s""",
                (
                    context_id, after_id or 0, term_id, term_id,
                    staff_user_id, staff_user_id, global_scope, campuses,
                    faculties, departments, limit + 1,
                ),
            )
            rows = [dict(row) for row in cur.fetchall()]
        return {"items": rows[:limit], "next_cursor": rows[limit - 1]["id"] if len(rows) > limit else None}

    @router.post("/workloads")
    def create_workload(
        request: WorkloadCreate,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.confirmation is False:
            raise HTTPException(status_code=409, detail="Yuklamani inson tasdiqlashi kerak")
        with database() as (_, cur):
            ensure_schema(cur)
            section = section_resource(cur, request.context_id, request.section_id)
            if int(section["term_id"]) != request.term_id:
                raise HTTPException(status_code=422, detail="Semestr va oqim mos emas")
            require_permission(
                cur, request.context_id, user_id, "workload.manage",
                campus_id=section["campus_id"], faculty_id=section["faculty_id"],
                department_id=section["department_id"],
            )
            cur.execute(
                """INSERT INTO institute_staff_workloads(
                     context_id,term_id,section_id,staff_user_id,workload_type,
                     planned_hours,status,approved_by_user_id
                   ) VALUES(%s,%s,%s,%s,%s,%s,'active',%s) RETURNING *""",
                (
                    request.context_id, request.term_id, request.section_id,
                    request.staff_user_id, request.workload_type,
                    request.planned_hours, user_id,
                ),
            )
            row = dict(cur.fetchone())
            audit(cur, request.context_id, user_id, "workload.create", "workload", row["id"])
        return {"item": row}

    @router.get("/analytics/summary")
    def analytics_summary(
        context_id: int = Query(ge=1), term_id: int | None = Query(default=None, ge=1),
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database(readonly=True) as (_, cur):
            ensure_schema(cur)
            is_system_admin = system_admin(cur, user_id)
            assignments = [] if is_system_admin else active_assignments(cur, context_id, user_id)
            assignment_roles = {row["role_key"] for row in assignments}
            student_only = bool(assignments) and assignment_roles == {"student"}
            default_currency, _ = finance_policy(cur, context_id)
            if student_only:
                cur.execute(
                    """SELECT
                       (SELECT COUNT(*) FROM institute_enrollments WHERE context_id=%s AND student_user_id=%s AND status='enrolled') active_sections,
                       (SELECT COALESCE(AVG(final_percent),0) FROM institute_course_results WHERE context_id=%s AND student_user_id=%s AND status='finalized') average_percent,
                       (SELECT COALESCE(AVG(grade_point),0) FROM institute_course_results WHERE context_id=%s AND student_user_id=%s AND status='finalized') average_gpa,
                       (SELECT COALESCE(
                          100-(SUM(absent_minutes) FILTER(WHERE status NOT IN ('excused','sick'))*100.0
                            / NULLIF(SUM(scheduled_minutes),0)),100)
                        FROM institute_attendance WHERE context_id=%s AND student_user_id=%s) attendance_percent,
                       (SELECT COALESCE(SUM(i.amount-i.paid_amount),0)
                        FROM institute_contract_installments i JOIN institute_student_contracts c ON c.id=i.contract_id
                        WHERE i.context_id=%s AND c.student_user_id=%s AND c.currency=%s
                          AND i.status IN ('unpaid','partial')) debt_amount,
                       (SELECT COALESCE(SUM(p.amount),0)
                        FROM institute_payments p JOIN institute_student_contracts c ON c.id=p.contract_id
                        WHERE p.context_id=%s AND c.student_user_id=%s AND p.currency=%s) paid_amount""",
                    (
                        context_id, user_id, context_id, user_id,
                        context_id, user_id, context_id, user_id,
                        context_id, user_id, default_currency,
                        context_id, user_id, default_currency,
                    ),
                )
            else:
                roles, global_scope, campuses, faculties, departments = scope_sets(
                    cur, context_id, user_id,
                    roles_for_permission("analytics.view"),
                )
                permission_set = permissions_for(roles)
                lecturer_only = roles == {"lecturer"}
                advisor_only = roles == {"advisor"}
                cur.execute(
                    """WITH visible_sections AS (
                         SELECT s.id FROM institute_course_sections s
                         WHERE s.context_id=%s
                           AND (%s IS NULL OR s.term_id=%s)
                           AND (%s OR s.campus_id=ANY(%s)
                                OR s.faculty_id=ANY(%s)
                                OR s.department_id=ANY(%s))
                           AND (NOT %s OR s.primary_lecturer_user_id=%s
                                OR EXISTS(SELECT 1 FROM institute_section_instructors si
                                  WHERE si.context_id=s.context_id AND si.section_id=s.id
                                    AND si.instructor_user_id=%s AND si.active))
                           AND (NOT %s OR EXISTS(
                                SELECT 1 FROM institute_section_cohorts sc
                                JOIN institute_cohorts co
                                  ON co.context_id=sc.context_id AND co.id=sc.cohort_id
                                WHERE sc.context_id=s.context_id AND sc.section_id=s.id
                                  AND co.advisor_user_id=%s AND co.active))
                       ) SELECT
                         (SELECT COUNT(*) FROM visible_sections) active_sections,
                         (SELECT COUNT(DISTINCT e.student_user_id)
                          FROM institute_enrollments e JOIN visible_sections v ON v.id=e.section_id
                          WHERE e.status IN ('enrolled','completed')) active_students,
                         (SELECT COALESCE(AVG(r.final_percent),0)
                          FROM institute_course_results r JOIN visible_sections v ON v.id=r.section_id
                          WHERE r.status='finalized') average_percent,
                         (SELECT COALESCE(AVG(r.grade_point),0)
                          FROM institute_course_results r JOIN visible_sections v ON v.id=r.section_id
                          WHERE r.status='finalized') average_gpa,
                         (SELECT COALESCE(
                            100-(SUM(a.absent_minutes) FILTER(WHERE a.status NOT IN ('excused','sick'))*100.0
                              / NULLIF(SUM(a.scheduled_minutes),0)),100)
                          FROM institute_attendance a JOIN visible_sections v ON v.id=a.section_id) attendance_percent""",
                    (
                        context_id, term_id, term_id, global_scope, campuses,
                        faculties, departments, lecturer_only, user_id, user_id,
                        advisor_only, user_id,
                    ),
                )
                summary = dict(cur.fetchone())
                summary["debt_amount"] = Decimal("0")
                summary["paid_amount"] = Decimal("0")
                if "finance.view" in permission_set:
                    cur.execute(
                        """SELECT
                           COALESCE(SUM(i.amount-i.paid_amount),0) debt_amount,
                           COALESCE((SELECT SUM(pay.amount) FROM institute_payments pay
                             JOIN institute_student_contracts pc ON pc.id=pay.contract_id
                             JOIN institute_programs pp ON pp.id=pc.program_id
                             WHERE pay.context_id=%s AND pay.currency=%s
                               AND (%s OR pp.campus_id=ANY(%s)
                                    OR pp.faculty_id=ANY(%s)
                                    OR pp.department_id=ANY(%s))),0) paid_amount
                           FROM institute_contract_installments i
                           JOIN institute_student_contracts c ON c.id=i.contract_id
                           JOIN institute_programs p ON p.id=c.program_id
                           WHERE i.context_id=%s AND c.currency=%s
                             AND i.status IN ('unpaid','partial')
                             AND (%s OR p.campus_id=ANY(%s)
                                  OR p.faculty_id=ANY(%s)
                                  OR p.department_id=ANY(%s))""",
                        (
                            context_id, default_currency, global_scope, campuses,
                            faculties, departments, context_id, default_currency,
                            global_scope, campuses, faculties, departments,
                        ),
                    )
                    money = cur.fetchone()
                    summary["debt_amount"] = money["debt_amount"]
                    summary["paid_amount"] = money["paid_amount"]
            if student_only:
                summary = dict(cur.fetchone())
                summary["active_students"] = 1
            summary["sections"] = summary["active_sections"]
            summary["debt"] = summary["debt_amount"]
            summary["currency"] = default_currency
        return {"summary": summary, "term_id": term_id}

    @router.post("/assistant/sessions")
    def start_assistant_session(
        request: AssistantStart,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        with database() as (_, cur):
            ensure_schema(cur)
            if request.context_id is not None:
                scope_sets(
                    cur, request.context_id, user_id,
                    roles_for_permission("assistant.use"),
                )
            cur.execute(
                """INSERT INTO institute_assistant_sessions(
                     context_id,user_id,workflow_key,avatar_variant,
                     avatar_enabled,speech_enabled
                   ) VALUES(%s,%s,%s,%s,%s,%s) RETURNING *""",
                (
                    request.context_id, user_id, request.workflow_key,
                    request.avatar_variant, request.avatar_enabled,
                    request.speech_enabled,
                ),
            )
            row = dict(cur.fetchone())
        return {
            "item": row,
            "safety": {
                "navigation_and_drafts_only": True,
                "can_publish_or_grade_or_pay": False,
            },
        }

    @router.post("/assistant/sessions/{session_id}/actions")
    def assistant_action(
        session_id: int,
        request: AssistantAction,
        user_id: int = Depends(authenticated_user),
    ) -> dict[str, Any]:
        if request.action_id not in ASSISTANT_ACTIONS:
            raise HTTPException(status_code=422, detail="Avatar amali ruxsat etilmagan")
        require_json_size(request.payload, 20_000, "Avatar amali")
        forbidden_keys = {
            "role_key", "grade", "score", "payment", "amount", "publish",
            "status_order", "transcript", "term_close", "enrollment_decision",
        }
        if any(key in request.payload for key in forbidden_keys):
            raise HTTPException(status_code=403, detail="Avatar imtiyozli amalni bajara olmaydi")
        with database() as (_, cur):
            ensure_schema(cur)
            cur.execute(
                """SELECT * FROM institute_assistant_sessions
                   WHERE id=%s AND user_id=%s AND status IN ('active','paused')
                   FOR UPDATE""",
                (session_id, user_id),
            )
            session = cur.fetchone()
            if not session:
                raise HTTPException(status_code=404, detail="Avatar sessiyasi topilmadi")
            if session["context_id"] is not None:
                scope_sets(
                    cur, int(session["context_id"]), user_id,
                    roles_for_permission("assistant.use"),
                )
            reversible = request.action_id in REVERSIBLE_ACTIONS
            cur.execute(
                """INSERT INTO institute_assistant_actions(
                     session_id,context_id,user_id,action_id,ui_anchor,payload,reversible
                   ) VALUES(%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING *""",
                (
                    session_id, session["context_id"], user_id, request.action_id,
                    request.ui_anchor,
                    json.dumps(request.payload, ensure_ascii=False, default=str),
                    reversible,
                ),
            )
            action = dict(cur.fetchone())
            new_status = (
                "paused" if request.action_id == "PAUSE"
                else "active" if request.action_id == "RESUME"
                else "completed" if request.action_id == "COMPLETE_TOUR"
                else session["status"]
            )
            cur.execute(
                """UPDATE institute_assistant_sessions SET status=%s,
                     current_step=COALESCE(%s,current_step),
                     ended_at=CASE WHEN %s='completed' THEN NOW() ELSE ended_at END
                   WHERE id=%s RETURNING *""",
                (new_status, request.ui_anchor, new_status, session_id),
            )
            updated = dict(cur.fetchone())
        return {"item": action, "session": updated, "server_mutation": False}

    return router

"""Exact, feasibility-first timetable solver for SamTM.

This module deliberately has no dependency on FastAPI, PostgreSQL, or the
large ``samtm_school`` monolith.  The production endpoint can therefore build
its normal ``jobs`` and ``context`` objects and hand them to
``solve_exact_timetable``.  Returned placements use the existing shape::

    {"job": job, "day": 1, "period": 2,
     "teachers": [101], "room_keys": ["room:7"]}

Google OR-Tools is optional at import time.  If it is absent, importing this
file is safe and the public solver returns ``MODEL_INVALID`` with the stable
``ORTOOLS_NOT_INSTALLED`` diagnostic.  Deployment must install OR-Tools before
the exact path is enabled.

Adapter contract
----------------
``DefaultTimetableAdapter`` understands the current V19/V20 SamTM job/context
schema, including A/B week rotations.  A caller with additional static rules
may pass ``context["exact_candidate_filter"]`` with this signature::

    filter(job, day, period, teachers, room_keys, context) -> iterable[str]

Any returned reason removes that candidate.  Alternatively,
``candidate_builder(job, context)`` may return dictionaries containing at
least ``day``, ``period``, ``teachers`` and ``room_keys``.  Optional canonical
fields are ``interval``, ``class_phases``, ``teacher_phases``,
``room_phases``, ``subject_phases``, and ``teacher_phase_loads``.  Phase values
are ``har_hafta``, ``toq`` or ``juft``.

The strict model never weakens BAND/red time or method days for ordinary
lessons.  The only unconditional compatibility exception is an administrator-
fixed class hour when the caller enables that exact-slot flag.  After a proven
strict failure, a caller may explicitly enable one bounded fallback: at most
two identified method-day slots for primary classes on non-Saturday days.
BAND/red time remains impossible and every applied exception is returned.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product
import math
import re
import threading
import time
import unicodedata
from typing import Any, Callable, Iterable, Mapping, Optional

# Deployda fayl haqiqatan yangilangani bir qarashda ko'rinadigan belgi.
EXACT_SOLVER_RELEASE = "SAMTM-EXACT-SOLVER-V22.47-WORST-FIRST-COMPACT"

_ORTOOLS_IMPORT_ERROR: Optional[BaseException] = None
try:  # pragma: no cover - exercised in an OR-Tools-enabled deployment.
    from ortools.sat.python import cp_model  # type: ignore
except Exception as error:  # pragma: no cover - default test image has none.
    cp_model = None
    _ORTOOLS_IMPORT_ERROR = error


OPTIMAL = "OPTIMAL"
FEASIBLE = "FEASIBLE"
INFEASIBLE = "INFEASIBLE"
UNKNOWN = "UNKNOWN"
MODEL_INVALID = "MODEL_INVALID"
EXACT_STATUSES = frozenset({OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN, MODEL_INVALID})
ORTOOLS_AVAILABLE = cp_model is not None

_ACTUAL_PHASES = ("toq", "juft")
_WEEKDAY_NAMES = {
    1: "Dushanba", 2: "Seshanba", 3: "Chorshanba",
    4: "Payshanba", 5: "Juma", 6: "Shanba", 7: "Yakshanba",
}


def ortools_available() -> bool:
    """Return whether CP-SAT can be used in this Python environment."""

    return bool(ORTOOLS_AVAILABLE)


def normalize_phase(value: Any) -> str:
    """Normalize a SamTM week phase, rejecting unsafe unknown values."""

    text = str(value or "har_hafta").strip().casefold().replace("-", "_")
    aliases = {
        "har_hafta": "har_hafta", "har hafta": "har_hafta", "all": "har_hafta",
        "toq": "toq", "odd": "toq", "juft": "juft", "even": "juft",
    }
    if text not in aliases:
        raise ValueError(f"Noma'lum hafta fazasi: {value!r}")
    return aliases[text]


def expand_phases(values: Any) -> frozenset[str]:
    """Expand one/many configured phases to the two real week phases."""

    if values is None or isinstance(values, (str, bytes)):
        raw = [values]
    else:
        raw = list(values)
    result: set[str] = set()
    for value in raw or [None]:
        phase = normalize_phase(value)
        if phase == "har_hafta":
            result.update(_ACTUAL_PHASES)
        else:
            result.add(phase)
    return frozenset(result)


def phases_overlap(first: Any, second: Any) -> bool:
    """Pure helper used by tests and external validators."""

    return bool(expand_phases(first).intersection(expand_phases(second)))


def intervals_overlap(first: Any, second: Any) -> bool:
    """Return true for half-open clock intervals that overlap."""

    try:
        return int(first[0]) < int(second[1]) and int(second[0]) < int(first[1])
    except (TypeError, ValueError, IndexError):
        return False


def canonical_job_id(job: Mapping[str, Any], fallback: Any = None) -> str:
    """Stable identifier; object identity is intentionally never used."""

    if job.get("job_id") not in (None, ""):
        return str(job["job_id"])
    pieces = (
        job.get("load_id"), job.get("sinf_id"), job.get("fan"),
        job.get("occurrence"), fallback,
    )
    return "legacy:" + ":".join("" if item is None else str(item) for item in pieces)


def _clock_minutes(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()[:5]
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if not match:
        return None
    hour, minute = int(match.group(1)), int(match.group(2))
    if hour not in range(24) or minute not in range(60):
        return None
    return hour * 60 + minute


def _format_interval(interval: tuple[int, int]) -> str:
    def one(value: int) -> str:
        return f"{value // 60:02d}:{value % 60:02d}"
    return f"{one(int(interval[0]))}–{one(int(interval[1]))}"


def _subject_key(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    for old in ("‘", "’", "`", "ʼ", "ʻ", "'", '"'):
        text = text.replace(old, "")
    text = re.sub(r"[^a-z0-9а-яёқғҳў]+", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def _contains(key: str, *phrases: str) -> bool:
    return any(_subject_key(item) in key for item in phrases)


def _finalize_subject_profile(
    job: Mapping[str, Any], profile: Mapping[str, Any]
) -> dict[str, Any]:
    result = dict(profile)
    result["practical"] = bool(
        result.get("practical")
        or result.get("physical")
        or result.get("technology")
    )
    if job.get("is_class_hour"):
        # Administrator fan nomini erkin yozadi. Masalan, "Texnologik
        # kelajak soati" matndan amaliy fan deb topilib, qat'iy 1-dars
        # domenidan yo'qolmasligi kerak. Job turi matndan ustun turadi.
        result.update({
            "physical": False,
            "technology": False,
            "practical": False,
            "light": True,
            "primary_light": True,
            "primary_core": False,
            "heavy": False,
            "written_heavy": False,
            "core_priority": False,
            "academic": False,
            "class_hour": True,
            "difficulty": 2,
        })
    return result


def subject_profile(job: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    """Small pure profile compatible with the monolith's V18.74 flags."""

    stored = job.get("v1874_profile")
    if isinstance(stored, Mapping):
        return _finalize_subject_profile(job, stored)
    key = _subject_key(job.get("fan"))
    is_math = _contains(key, "matematika", "algebra", "geometriya")
    is_native = _contains(key, "ona tili", "ozbek tili")
    is_literature = _contains(key, "adabiyot", "oqish savodxonligi", "oqish")
    is_science = _contains(key, "fizika", "kimyo", "biologiya", "tabiiy fan", "tabiat")
    physical = _contains(key, "jismoniy tarbiya", "jismoniy madaniyat")
    technology = _contains(key, "texnologiya", "mehnat") and not _contains(
        key, "axborot texnologiyalari"
    )
    light = bool(
        physical or technology or _contains(
            key, "tasviriy sanat", "chizmachilik", "musiqa", "tarbiya",
            "sinf soati", "kelajak soati", "chaqiruvga qadar",
        )
    )
    difficulty = int(job.get("weight") or (2 if light else 7))
    heavy = bool(not light and (difficulty >= 3 or is_math or is_native or is_science))
    return _finalize_subject_profile(job, {
        "key": key,
        "physical": physical,
        "technology": technology,
        "practical": bool(physical or technology),
        "light": light,
        "heavy": heavy,
        "written_heavy": bool(heavy and not physical and not technology),
        "core_priority": bool(is_math or is_native or is_literature or is_science),
        "academic": not bool(job.get("is_class_hour")),
        "primary_light": light,
        "difficulty": difficulty,
    })


def _subject_daily_limits(job: Mapping[str, Any]) -> dict[str, int]:
    sources = list(job.get("rotation_members") or []) or [job]
    result: dict[str, int] = {}
    for source in sources:
        key = _subject_key(source.get("fan") or job.get("fan"))
        value = max(1, int(source.get("daily_max") or 1))
        result[key] = min(result.get(key, value), value)
    return result


def _grade(job: Mapping[str, Any], context: Mapping[str, Any]) -> int:
    try:
        explicit = int(job.get("v1874_grade") or 0)
    except (TypeError, ValueError):
        explicit = 0
    if explicit:
        return explicit
    row = (context.get("classes") or {}).get(job.get("sinf_id"), {})
    match = re.search(r"\d+", str((row or {}).get("sinf") or ""))
    return int(match.group()) if match else 0


def _blocked(hard: Iterable[Any], teacher: int, day: int, shift: int, period: int) -> bool:
    # Candidate validation calls this tens of thousands of times. Production
    # already supplies a set/frozenset; copying it on every call caused a long
    # silent pre-solver pause before the visible CP-SAT timer even started.
    values = hard if isinstance(hard, (set, frozenset)) else set(hard or ())
    return any(key in values for key in (
        (teacher, day, 0, 0), (teacher, day, shift, 0),
        (teacher, day, 0, period), (teacher, day, shift, period),
    ))


def _fixed_class_hour_availability_exception(
    job: Mapping[str, Any], teacher: int, day: int, shift: int, period: int,
    context: Mapping[str, Any],
) -> bool:
    """Explicit legacy exception for an administrator-fixed class hour.

    This opens only the configured method day for this exact class-hour slot.
    Hard red/BAND is checked separately and is never bypassed.  Class,
    teacher and room collisions also remain model constraints.
    """

    return bool(
        (
            context.get("allow_fixed_class_hour_method_exception")
            or context.get("allow_fixed_class_hour_availability_exception")
        )
        and job.get("is_class_hour")
        and int(job.get("fixed_day") or 0) == int(day)
        and int(job.get("fixed_period") or 0) == int(period)
        and int(job.get("smena") or 1) == int(shift)
        and teacher is not None
    )


def _class_day_blocked(job: Mapping[str, Any], day: int, context: Mapping[str, Any]) -> bool:
    rules = context.get("class_day_blocks") or {}
    class_id = int(job.get("sinf_id") or 0)
    grade = _grade(job, context)
    if isinstance(rules, Mapping):
        if (class_id, int(day)) in set(rules.get("exact") or ()):
            return True
        if (grade, int(day)) in set(rules.get("grades") or ()):
            return True
    return False


def _slot_interval(context: Mapping[str, Any], shift: int, period: int) -> tuple[int, int]:
    explicit = context.get("shift_intervals") or context.get("slot_intervals") or {}
    value = explicit.get((int(shift), int(period))) if isinstance(explicit, Mapping) else None
    if value and len(value) >= 2:
        return int(value[0]), int(value[1])
    shift_row = (context.get("shifts") or {}).get(int(shift), {})
    for slot in (shift_row or {}).get("slotlar") or []:
        if int(slot.get("dars_raqami") or 0) != int(period):
            continue
        start = _clock_minutes(slot.get("boshlanish"))
        end = _clock_minutes(slot.get("tugash"))
        if start is not None and end is not None and end > start:
            return start, end
    # Safe deterministic fallback. Different shifts must not accidentally use
    # the same clock when their configuration is absent.
    base = 8 * 60 if int(shift) == 1 else 13 * 60 + 30 + max(0, int(shift) - 2) * 420
    start = base + (int(period) - 1) * 50
    return start, start + 45


def _job_class_phases(job: Mapping[str, Any]) -> frozenset[str]:
    members = job.get("rotation_members") or []
    if members:
        return expand_phases([member.get("hafta_turi") for member in members])
    return expand_phases(job.get("hafta_turi"))


def _home_room_key(job: Mapping[str, Any], context: Mapping[str, Any]) -> Optional[str]:
    row = (context.get("classes") or {}).get(job.get("sinf_id"), {}) or {}
    if "_home_room_key" in row:
        value = row.get("_home_room_key")
        return str(value) if value else None
    if row.get("_home_room_invalid"):
        return None
    room_id = row.get("xona_id") or job.get("room_id")
    return f"room:{int(room_id)}" if room_id not in (None, "") else None


def _member_teacher_choices(member: Mapping[str, Any]) -> list[tuple[int, ...]]:
    groups = member.get("groups") or []
    if groups:
        teachers = tuple(
            int(group["teacher"]) for group in groups if group.get("teacher") is not None
        )
        return [teachers] if len(teachers) == len(groups) and len(set(teachers)) == len(teachers) else []
    options = [int(item) for item in member.get("teacher_options") or [] if item is not None]
    # Existing SamTM contract: a fixed KELAJAK/SINF SOATI may be shown with
    # teacher=NULL until the class leader is assigned.  Ordinary subjects
    # remain infeasible without a teacher.
    if not options and bool(member.get("is_class_hour")):
        return [tuple()]
    return [(item,) for item in sorted(set(options))]


def _member_room_keys(member: Mapping[str, Any], context: Mapping[str, Any]) -> tuple[Optional[str], ...]:
    groups = member.get("groups") or []
    home = _home_room_key(member, context)
    if groups:
        result = []
        for index, group in enumerate(groups):
            room = group.get("xona_id")
            result.append(f"room:{int(room)}" if room else (home if index == 0 else None))
        return tuple(result)
    if member.get("room_id"):
        return (f"room:{int(member['room_id'])}",)
    return (home,)


class DefaultTimetableAdapter:
    """Adapter for the current SamTM dictionary schema."""

    supports_method_relaxation = True

    def build_candidates(
        self,
        job: Mapping[str, Any],
        context: Mapping[str, Any],
        *,
        ignored_method: Optional[set[tuple[int, int]]] = None,
        mark_method_exceptions: bool = False,
    ) -> list[dict[str, Any]]:
        ignored_method = set(ignored_method or ())
        shift = int(job.get("smena") or 1)
        shift_row = (context.get("shifts") or {}).get(shift)
        if not shift_row:
            return []
        weekdays = int(context.get("weekdays") or 6)
        fixed_day = int(job.get("fixed_day") or 0)
        fixed_period = int(job.get("fixed_period") or 0)
        days = [fixed_day] if fixed_day else list(range(1, weekdays + 1))
        periods = [
            int(slot.get("dars_raqami") or 0)
            for slot in (shift_row.get("slotlar") or [])
            if int(slot.get("dars_raqami") or 0) > 0
        ]
        if fixed_period:
            periods = [period for period in periods if period == fixed_period]
        members = list(job.get("rotation_members") or [])
        sources = members or [job]
        member_choices = [_member_teacher_choices(member) for member in sources]
        if any(not choices for choices in member_choices):
            return []
        profile = subject_profile(job, context)
        grade = _grade(job, context)
        max_period = int(
            (context.get("class_daily_caps") or {}).get(job.get("sinf_id"), 5 if 1 <= grade <= 4 else 6)
        )
        practical_min = int(context.get("practical_min_period") or 2)
        hard = set(context.get("hard") or ())
        method_hard = set(context.get("method_hard") or ())
        rules_map = context.get("rules") or {}
        default_rules = context.get("default_rules") or {
            "kunlik_max": 6, "eng_erta_dars": 1, "eng_kech_dars": 12,
            "afzal_smena": 0, "okno_max": 1,
        }
        result: list[dict[str, Any]] = []
        for day in days:
            if day not in range(1, weekdays + 1) or _class_day_blocked(job, day, context):
                continue
            if 1 <= grade <= 4 and int(day) == 6:
                continue
            for period in periods:
                if period > max_period:
                    continue
                if profile.get("practical") and period < practical_min:
                    continue
                for selected_by_member in product(*member_choices):
                    teacher_phases: dict[int, set[str]] = defaultdict(set)
                    teacher_phase_loads: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
                    room_phases: dict[str, set[str]] = defaultdict(set)
                    subject_phases: dict[str, set[str]] = defaultdict(set)
                    placement_teachers: list[int] = []
                    placement_rooms: list[str] = []
                    invalid = False
                    for member, selected in zip(sources, selected_by_member):
                        member_phases = expand_phases(member.get("hafta_turi") if members else job.get("hafta_turi"))
                        # One-phase TOQ/JUFT lesson is 0.5 contractual hour;
                        # a regular lesson active in both phases is 1.0 hour.
                        load_units = 1 if len(member_phases) == 1 else 2
                        for teacher in selected:
                            if teacher not in placement_teachers:
                                placement_teachers.append(teacher)
                            teacher_phases[teacher].update(member_phases)
                            for phase in member_phases:
                                teacher_phase_loads[teacher][phase] += load_units
                        keys = _member_room_keys(member, context)
                        non_null = [key for key in keys if key]
                        if len(non_null) != len(set(non_null)):
                            invalid = True
                            break
                        for key in non_null:
                            if key not in placement_rooms:
                                placement_rooms.append(key)
                            room_phases[key].update(member_phases)
                        subject_phases[_subject_key(member.get("fan") or job.get("fan"))].update(member_phases)
                    if invalid:
                        continue
                    method_exceptions: set[tuple[int, int, int, int]] = set()
                    for teacher in placement_teachers:
                        teacher_rules = rules_map.get(teacher, default_rules)
                        if period < int(teacher_rules.get("eng_erta_dars") or 1) or period > int(
                            teacher_rules.get("eng_kech_dars") or 12
                        ):
                            invalid = True
                            break
                        fixed_method_exception = _fixed_class_hour_availability_exception(
                            job, teacher, day, shift, period, context
                        )
                        if _blocked(hard, teacher, day, shift, period):
                            invalid = True
                            break
                        if (teacher, day) in method_hard:
                            if fixed_method_exception:
                                pass
                            elif (teacher, day) not in ignored_method:
                                invalid = True
                                break
                            else:
                                if bool(context.get("method_exception_primary_only")) and (
                                    not 1 <= int(grade) <= 4 or int(day) == 6
                                ):
                                    invalid = True
                                    break
                                method_exceptions.add((teacher, int(day), shift, int(period)))
                    if invalid:
                        continue
                    room_keys_for_filter: list[Optional[str]] = list(placement_rooms) or [None]
                    candidate_filter = context.get("exact_candidate_filter")
                    if callable(candidate_filter):
                        filter_context: Mapping[str, Any] = context
                        if ignored_method:
                            # The production filter delegates to the monolith's
                            # final candidate-reasons function.  During this
                            # separate diagnostic model only, hide precisely
                            # the method-day pairs being tested; hard BAND/red
                            # remains untouched.  Never mutate the live context.
                            relaxed_context = dict(context)
                            relaxed_context["method_hard"] = set(method_hard).difference(
                                ignored_method
                            )
                            relaxed_context["_exact_method_relaxation_analysis"] = True
                            filter_context = relaxed_context
                        reasons = candidate_filter(
                            job, int(day), int(period), list(placement_teachers),
                            room_keys_for_filter, filter_context,
                        )
                        if reasons:
                            continue
                    result.append({
                        "day": int(day), "period": int(period), "shift": shift,
                        "class_id": int(job.get("sinf_id") or 0),
                        "teachers": tuple(placement_teachers),
                        "room_keys": tuple(room_keys_for_filter),
                        "interval": _slot_interval(context, shift, period),
                        "class_phases": _job_class_phases(job),
                        "teacher_phases": {key: frozenset(value) for key, value in teacher_phases.items()},
                        "teacher_phase_loads": {
                            key: dict(value) for key, value in teacher_phase_loads.items()
                        },
                        "room_phases": {key: frozenset(value) for key, value in room_phases.items()},
                        "subject_phases": {key: frozenset(value) for key, value in subject_phases.items()},
                        "subject_profiles": {
                            _subject_key(member.get("fan") or job.get("fan")): subject_profile(member, context)
                            for member in sources
                        },
                        "subject_daily_limits": _subject_daily_limits(job),
                        "method_exceptions": frozenset(method_exceptions) if mark_method_exceptions else frozenset(),
                    })
        return result


class CallableCandidateAdapter:
    """Normalize a lightweight ``candidate_builder(job, context)`` callback."""

    supports_method_relaxation = False

    def __init__(self, builder: Callable[[Mapping[str, Any], Mapping[str, Any]], Iterable[Mapping[str, Any]]]):
        self.builder = builder

    def build_candidates(self, job: Mapping[str, Any], context: Mapping[str, Any], **_: Any) -> list[dict[str, Any]]:
        return [dict(row) for row in self.builder(job, context)]


def _normalize_candidate(
    raw: Mapping[str, Any], job: Mapping[str, Any], context: Mapping[str, Any]
) -> dict[str, Any]:
    day = int(raw.get("day") or 0)
    period = int(raw.get("period") or 0)
    shift = int(raw.get("shift") or job.get("smena") or 1)
    expected_class_id = int(job.get("sinf_id") or 0)
    raw_class_id = raw.get("class_id")
    if raw_class_id not in (None, "") and int(raw_class_id) != expected_class_id:
        raise ValueError(
            "Candidate class_id manba job.sinf_id qiymatiga mos emas"
        )
    class_id = expected_class_id
    if day <= 0 or period <= 0 or class_id <= 0:
        raise ValueError("Candidate day/period/class_id musbat bo'lishi kerak")
    interval = raw.get("interval") or _slot_interval(context, shift, period)
    interval = (int(interval[0]), int(interval[1]))
    if interval[1] <= interval[0]:
        raise ValueError("Candidate vaqt oralig'i noto'g'ri")
    teachers = tuple(int(item) for item in raw.get("teachers") or [] if item is not None)
    room_keys = tuple(item if item is None else str(item) for item in raw.get("room_keys") or [None])
    class_phases = expand_phases(raw.get("class_phases") or _job_class_phases(job))

    def normalize_resource_phases(
        value: Any, keys: Iterable[Any], default: frozenset[str],
        key_converter: Callable[[Any], Any],
    ) -> dict[Any, frozenset[str]]:
        mapping: dict[Any, Any] = {}
        if isinstance(value, Mapping):
            for raw_key, raw_value in value.items():
                try:
                    mapping[key_converter(raw_key)] = raw_value
                except (TypeError, ValueError):
                    continue
        return {
            key: expand_phases(mapping.get(key) if key in mapping else default)
            for key in keys
        }

    teacher_phases = normalize_resource_phases(
        raw.get("teacher_phases"), teachers, class_phases, int
    )
    room_non_null = tuple(key for key in room_keys if key)
    room_phases = normalize_resource_phases(
        raw.get("room_phases"), room_non_null, class_phases, str
    )
    subject_raw = raw.get("subject_phases")
    if isinstance(subject_raw, Mapping):
        subject_phases = {
            _subject_key(key): expand_phases(value) for key, value in subject_raw.items()
        }
    else:
        subject_phases = {_subject_key(job.get("fan")): class_phases}
    profiles_raw = raw.get("subject_profiles")
    if isinstance(profiles_raw, Mapping):
        subject_profiles = {
            _subject_key(key): dict(value) if isinstance(value, Mapping) else {}
            for key, value in profiles_raw.items()
        }
    else:
        subject_profiles = {
            subject: subject_profile(job, context) for subject in subject_phases
        }
    loads_raw: dict[int, Any] = {}
    if isinstance(raw.get("teacher_phase_loads"), Mapping):
        for raw_teacher, raw_load in raw["teacher_phase_loads"].items():
            try:
                loads_raw[int(raw_teacher)] = raw_load
            except (TypeError, ValueError):
                continue
    teacher_phase_loads: dict[int, dict[str, int]] = {}
    for teacher in teachers:
        phase_load = loads_raw.get(teacher, {})
        if not isinstance(phase_load, Mapping):
            phase_load = {}
        teacher_phase_loads[teacher] = {
            phase: max(1, int((phase_load or {}).get(
                phase,
                1 if len(teacher_phases.get(teacher, class_phases)) == 1 else 2,
            )))
            for phase in teacher_phases.get(teacher, class_phases)
        }
    daily_limits_raw = raw.get("subject_daily_limits")
    subject_daily_limits = _subject_daily_limits(job)
    if isinstance(daily_limits_raw, Mapping):
        for subject, value in daily_limits_raw.items():
            subject_key = _subject_key(subject)
            requested_limit = max(1, int(value or 1))
            # A custom adapter may narrow a source rule, but it cannot make
            # ``daily_max`` looser.  The same contract applies to every grade:
            # an administrator's explicit ``2`` is a legal fallback, not a
            # request to repeat the subject and not something the solver may
            # silently overwrite with ``1``.
            source_limit = subject_daily_limits.get(subject_key)
            subject_daily_limits[subject_key] = (
                min(int(source_limit), requested_limit)
                if source_limit is not None else requested_limit
            )
    exceptions = frozenset(
        (int(item[0]), int(item[1]), int(item[2]), int(item[3]))
        for item in raw.get("method_exceptions") or ()
    )
    return {
        **dict(raw),
        "day": day, "period": period, "shift": shift, "class_id": class_id,
        "teachers": teachers, "room_keys": room_keys, "interval": interval,
        "class_phases": class_phases, "teacher_phases": teacher_phases,
        "teacher_phase_loads": teacher_phase_loads,
        "room_phases": room_phases, "subject_phases": subject_phases,
        "subject_profiles": subject_profiles,
        "subject_daily_limits": subject_daily_limits,
        "method_exceptions": exceptions,
    }


def candidate_hard_violations(
    candidate: Mapping[str, Any], job: Mapping[str, Any],
    context: Mapping[str, Any], *, allow_method_exceptions: bool = False,
) -> list[str]:
    """Validate the static hard domain independently of every adapter.

    This guard is especially important for a custom ``candidate_builder``:
    callbacks may narrow domains, but they cannot smuggle a red/method slot or
    a different shift back into the exact model.
    """

    errors: list[str] = []
    day = int(candidate.get("day") or 0)
    period = int(candidate.get("period") or 0)
    shift = int(candidate.get("shift") or 0)
    expected_shift = int(job.get("smena") or 1)
    weekdays = int(context.get("weekdays") or 6)
    if shift != expected_shift:
        errors.append("smena mos emas")
    if day not in range(1, weekdays + 1):
        errors.append("o'qish haftasidan tashqari")
    fixed_day = int(job.get("fixed_day") or 0)
    fixed_period = int(job.get("fixed_period") or 0)
    if fixed_day and day != fixed_day:
        errors.append("qat'iy kun buzilgan")
    if fixed_period and period != fixed_period:
        errors.append("qat'iy dars raqami buzilgan")
    if _class_day_blocked(job, day, context):
        errors.append("sinfning qattiq kun bloki")
    grade = _grade(job, context)
    if 1 <= grade <= 4 and day == 6:
        errors.append("1–4-sinf Shanba kuni bloklangan")
    max_period = int(
        (context.get("class_daily_caps") or {}).get(
            job.get("sinf_id"), 5 if 1 <= grade <= 4 else 6
        )
    )
    if period <= 0 or period > max_period:
        errors.append("sinfning kunlik dars chegarasidan tashqari")
    if subject_profile(job, context).get("practical") and period < int(
        context.get("practical_min_period") or 2
    ):
        errors.append("amaliy fan 1-darsga qo'yilmaydi")
    teachers = tuple(candidate.get("teachers") or ())
    if not teachers and not bool(job.get("is_class_hour")):
        errors.append("o'qituvchi biriktirilmagan")
    if len(teachers) != len(set(teachers)):
        errors.append("bitta o'qituvchi parallel guruhlarda takrorlangan")
    # Custom adapter manba jobdagi rahbar/o'qituvchini tashlab yuborishi yoki
    # boshqa user bilan almashtirishi mumkin emas. Aks holda haqiqiy ustozning
    # qizil/BAND qoidasi validatorga umuman yetib kelmay qolardi.
    groups = list(job.get("groups") or [])
    rotation_members = list(job.get("rotation_members") or [])
    if not rotation_members and groups:
        expected_group_teachers = tuple(
            int(group["teacher"])
            for group in groups if group.get("teacher") is not None
        )
        if (
            len(expected_group_teachers) != len(groups)
            or set(teachers) != set(expected_group_teachers)
        ):
            errors.append("candidate guruh o'qituvchilari manbaga mos emas")
    elif not rotation_members and "teacher_options" in job:
        allowed_teachers = {
            int(value) for value in job.get("teacher_options") or []
            if value is not None
        }
        if bool(job.get("is_class_hour")):
            if set(teachers) != allowed_teachers:
                errors.append("candidate sinf rahbari manbaga mos emas")
        elif len(teachers) != 1 or int(teachers[0]) not in allowed_teachers:
            errors.append("candidate o'qituvchisi manbaga mos emas")
    non_null_rooms = [str(value) for value in candidate.get("room_keys") or () if value]
    if len(non_null_rooms) != len(set(non_null_rooms)):
        errors.append("parallel guruhlar bir xil xonaga biriktirilgan")
    room_by_phase: dict[tuple[str, str], int] = defaultdict(int)
    for room, phases in (candidate.get("room_phases") or {}).items():
        for phase in phases:
            room_by_phase[(str(room), str(phase))] += 1
    if any(count > 1 for count in room_by_phase.values()):
        errors.append("parallel guruhlar bir xil xonaga biriktirilgan")
    hard = context.get("hard") or ()
    raw_method_hard = context.get("method_hard") or ()
    method_hard = (
        raw_method_hard
        if isinstance(raw_method_hard, (set, frozenset))
        else set(raw_method_hard)
    )
    rules = context.get("rules") or {}
    defaults = context.get("default_rules") or {
        "eng_erta_dars": 1, "eng_kech_dars": 12,
    }
    exception_tokens = set(candidate.get("method_exceptions") or ())
    for teacher in teachers:
        teacher = int(teacher)
        teacher_rules = rules.get(teacher, defaults) or defaults
        if period < int(teacher_rules.get("eng_erta_dars") or 1) or period > int(
            teacher_rules.get("eng_kech_dars") or 12
        ):
            errors.append(f"o'qituvchi {teacher} ruxsat etgan dars oralig'idan tashqari")
        fixed_method_exception = _fixed_class_hour_availability_exception(
            job, teacher, day, shift, period, context
        )
        if _blocked(hard, teacher, day, shift, period):
            errors.append(f"o'qituvchi {teacher} qizil/BAND vaqtda")
        if (teacher, day) in method_hard:
            token = (teacher, day, shift, period)
            if fixed_method_exception:
                pass
            elif not allow_method_exceptions or token not in exception_tokens:
                errors.append(f"o'qituvchi {teacher} metod kunida")
    return list(dict.fromkeys(errors))


def _adapter_for(candidate_builder: Any = None, adapter: Any = None) -> Any:
    if candidate_builder is not None and adapter is not None:
        raise ValueError("candidate_builder va adapter birga berilmaydi")
    if adapter is not None:
        if not callable(getattr(adapter, "build_candidates", None)):
            raise TypeError("adapter.build_candidates callable bo'lishi kerak")
        return adapter
    if candidate_builder is not None:
        if not callable(candidate_builder):
            raise TypeError("candidate_builder callable bo'lishi kerak")
        return CallableCandidateAdapter(candidate_builder)
    return DefaultTimetableAdapter()


@dataclass
class _ModelBundle:
    model: Any
    jobs: list[Mapping[str, Any]]
    candidates: list[dict[str, Any]]
    variables: list[Any]
    by_job: dict[int, list[int]]
    objective_terms: list[Any]
    exception_variables: dict[tuple[int, int, int, int], Any]
    teacher_exception_variables: dict[int, Any]
    has_objective: bool = True
    symmetry_breakers: int = 0


def _freeze_symmetry_value(value: Any) -> Any:
    """Turn a normalized candidate value into a stable comparable value.

    Feasibility models may order genuinely interchangeable weekly
    occurrences.  We compare the complete normalized candidate (except its
    job/index bookkeeping), so the ordering can never merge two lessons that
    participate in different hard constraints.
    """

    if isinstance(value, Mapping):
        return tuple(sorted(
            (str(key), _freeze_symmetry_value(item))
            for key, item in value.items()
        ))
    if isinstance(value, (set, frozenset)):
        return tuple(sorted(
            (_freeze_symmetry_value(item) for item in value), key=repr
        ))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_symmetry_value(item) for item in value)
    return value


def _candidate_hard_signature(candidate: Mapping[str, Any]) -> Any:
    """Return the full non-bookkeeping signature used for safe symmetry."""

    return _freeze_symmetry_value({
        key: value for key, value in candidate.items()
        if key not in {"candidate_index", "job_index", "job", "score"}
    })


def _enumerate_candidates(
    jobs: list[Mapping[str, Any]], context: Mapping[str, Any], adapter: Any,
    *, relax_method: bool = False,
) -> tuple[list[dict[str, Any]], dict[int, list[int]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    by_job: dict[int, list[int]] = defaultdict(list)
    empty: list[dict[str, Any]] = []
    ignored = set(context.get("method_hard") or ()) if relax_method else set()
    for job_index, job in enumerate(jobs):
        rows = adapter.build_candidates(
            job, context,
            ignored_method=ignored,
            mark_method_exceptions=relax_method,
        )
        for raw in rows:
            candidate = _normalize_candidate(raw, job, context)
            if candidate_hard_violations(
                candidate, job, context,
                allow_method_exceptions=bool(relax_method),
            ):
                continue
            candidate["job_index"] = job_index
            candidate["job"] = job
            candidate["candidate_index"] = len(candidates)
            candidates.append(candidate)
            by_job[job_index].append(candidate["candidate_index"])
        if not by_job[job_index]:
            teacher_ids = sorted({
                int(teacher)
                for source in (list(job.get("rotation_members") or []) or [job])
                for teacher in (
                    [group.get("teacher") for group in source.get("groups") or []]
                    if source.get("groups")
                    else list(source.get("teacher_options") or [])
                )
                if teacher is not None
            })
            empty.append({
                "job_index": int(job_index),
                "job_id": canonical_job_id(job, job_index),
                "sinf_id": job.get("sinf_id"), "fan": job.get("fan"),
                "smena": int(job.get("smena") or 1),
                "takror_raqami": int(job.get("occurrence") or 1),
                "teacher_ids": teacher_ids,
                "fixed_day": job.get("fixed_day"), "fixed_period": job.get("fixed_period"),
                "reason": "Qattiq qoidalar ichida bitta ham legal katak yo'q",
            })
    return candidates, dict(by_job), empty


def _model_status_name(status: Any) -> str:
    if cp_model is None:
        return MODEL_INVALID
    mapping = {
        cp_model.OPTIMAL: OPTIMAL,
        cp_model.FEASIBLE: FEASIBLE,
        cp_model.INFEASIBLE: INFEASIBLE,
        cp_model.MODEL_INVALID: MODEL_INVALID,
        cp_model.UNKNOWN: UNKNOWN,
    }
    return mapping.get(status, UNKNOWN)


def _build_model(
    jobs: list[Mapping[str, Any]], context: Mapping[str, Any], adapter: Any,
    *, relax_method: bool = False, feasibility_only: bool = False,
) -> tuple[Optional[_ModelBundle], list[dict[str, Any]]]:
    if cp_model is None:
        return None, []
    candidates, by_job, empty = _enumerate_candidates(
        jobs, context, adapter, relax_method=relax_method
    )
    if empty:
        return None, empty
    model = cp_model.CpModel()
    variables = [
        model.NewBoolVar(f"x_j{row['job_index']}_c{index}")
        for index, row in enumerate(candidates)
    ]
    for job_index in range(len(jobs)):
        model.AddExactlyOne([variables[index] for index in by_job[job_index]])

    # Weekly occurrences of the same lesson often have exactly the same hard
    # candidate universe.  Without an ordering, k occurrences introduce k!
    # meaningless permutations (six occurrences already mean 720 equivalent
    # branches).  The full candidate signature makes this breaker safe: only
    # truly interchangeable hard domains are ordered.
    symmetry_breakers = 0
    if feasibility_only and not relax_method:
        equivalent_domains: dict[Any, list[int]] = defaultdict(list)
        for job_index in range(len(jobs)):
            signature = tuple(
                _candidate_hard_signature(candidates[index])
                for index in by_job[job_index]
            )
            equivalent_domains[signature].append(job_index)
        for job_indices in equivalent_domains.values():
            if len(job_indices) < 2:
                continue
            for left_job, right_job in zip(job_indices, job_indices[1:]):
                left = by_job[left_job]
                right = by_job[right_job]
                if len(left) != len(right):
                    continue
                model.Add(
                    sum(rank * variables[index] for rank, index in enumerate(left))
                    <= sum(rank * variables[index] for rank, index in enumerate(right))
                )
                symmetry_breakers += 1

    # Convert overlapping real clock intervals into disjoint atomic segments.
    endpoints_by_day: dict[int, set[int]] = defaultdict(set)
    for row in candidates:
        endpoints_by_day[row["day"]].update(row["interval"])
    resource_buckets: dict[tuple[Any, ...], set[int]] = defaultdict(set)
    for index, row in enumerate(candidates):
        day = row["day"]
        start, end = row["interval"]
        endpoints = sorted(endpoints_by_day[day])
        segments = [
            segment for segment, (left, right) in enumerate(zip(endpoints, endpoints[1:]))
            if start < right and left < end
        ]
        for phase in row["class_phases"]:
            for segment in segments:
                resource_buckets[("class", row["class_id"], day, phase, segment)].add(index)
        for teacher, phases in row["teacher_phases"].items():
            for phase in phases:
                for segment in segments:
                    resource_buckets[("teacher", teacher, day, phase, segment)].add(index)
        for room, phases in row["room_phases"].items():
            for phase in phases:
                for segment in segments:
                    resource_buckets[("room", room, day, phase, segment)].add(index)
    seen_resource_domains: set[frozenset[int]] = set()
    for indices in resource_buckets.values():
        if len(indices) > 1:
            domain = frozenset(indices)
            if domain in seen_resource_domains:
                continue
            seen_resource_domains.add(domain)
            model.AddAtMostOne([variables[index] for index in sorted(domain)])

    weekdays = int(context.get("weekdays") or 6)
    # Class occupancy and prefix constraints: a used day is 1..N, never 2..N.
    class_period_vars: dict[tuple[int, int, str, int], list[int]] = defaultdict(list)
    class_day_vars: dict[tuple[int, int, str], list[int]] = defaultdict(list)
    for index, row in enumerate(candidates):
        for phase in row["class_phases"]:
            class_period_vars[(row["class_id"], row["day"], phase, row["period"])].append(index)
            class_day_vars[(row["class_id"], row["day"], phase)].append(index)
    class_ids = sorted({int(job.get("sinf_id") or 0) for job in jobs})
    quality_enabled = bool(not feasibility_only and not relax_method)
    balance_terms: list[Any] = []
    for class_id in class_ids:
        for phase in _ACTUAL_PHASES:
            phase_job_count = sum(
                1 for job in jobs if int(job.get("sinf_id") or 0) == class_id
                and phase in _job_class_phases(job)
            )
            for day in range(1, weekdays + 1):
                periods = sorted({
                    key[3] for key in class_period_vars
                    if key[:3] == (class_id, day, phase)
                })
                used_by_period: dict[int, Any] = {}
                if periods:
                    for period in range(1, max(periods) + 1):
                        used = model.NewBoolVar(f"class_used_{class_id}_{day}_{phase}_{period}")
                        indices = class_period_vars.get((class_id, day, phase, period), [])
                        if indices:
                            model.Add(sum(variables[index] for index in indices) == used)
                        else:
                            model.Add(used == 0)
                        used_by_period[period] = used
                    for period in range(1, max(periods)):
                        model.Add(used_by_period[period] >= used_by_period[period + 1])
                if quality_enabled and phase_job_count:
                    indices = sorted(set(class_day_vars.get((class_id, day, phase), [])))
                    count = model.NewIntVar(
                        0, min(phase_job_count, max(0, len(indices))),
                        f"class_count_{class_id}_{day}_{phase}",
                    )
                    model.Add(count == sum(variables[index] for index in indices))
                    deviation = model.NewIntVar(0, phase_job_count * weekdays, f"balance_{class_id}_{day}_{phase}")
                    model.AddAbsEquality(deviation, count * weekdays - phase_job_count)
                    balance_terms.append(deviation)

    # Subject repetitions and controlled repeat-day fallback.
    subject_groups: dict[tuple[int, str, int, str], list[int]] = defaultdict(list)
    subject_job_sets: dict[tuple[int, str, str], set[int]] = defaultdict(set)
    subject_daily_limits: dict[tuple[int, str], int] = {}
    subject_is_practical: dict[tuple[int, str], bool] = {}
    for index, row in enumerate(candidates):
        for subject, phases in row["subject_phases"].items():
            # Backend preflight/final validator bilan yagona kontrakt:
            # har bir fan kuniga ko'pi bilan 2, 3 esa qat'iy taqiqlangan.
            normal_limit = 2
            subject_daily_limits[(row["class_id"], subject)] = min(
                subject_daily_limits.get((row["class_id"], subject), normal_limit), normal_limit
            )
            profile = (row.get("subject_profiles") or {}).get(subject, {})
            subject_is_practical[(row["class_id"], subject)] = bool(
                subject_is_practical.get((row["class_id"], subject))
                or profile.get("practical") or profile.get("physical")
                or profile.get("technology")
            )
            for phase in phases:
                subject_groups[(row["class_id"], subject, row["day"], phase)].append(index)
                subject_job_sets[(row["class_id"], subject, phase)].add(
                    int(row["job_index"])
                )
    repeat_day_limit = max(0, int(context.get("max_subject_repeat_days") or 0))
    practical_repeat_day_limit = max(
        0, int(context.get("practical_repeat_day_limit", 1))
    )
    repeat_bools: dict[tuple[int, str, str], list[Any]] = defaultdict(list)
    repeat_group_limits: dict[tuple[int, str, str], int] = {}
    repeat_terms: list[tuple[Any, int]] = []
    practical_repeat_terms: list[tuple[Any, int]] = []
    for (class_id, subject, day, phase), indices in subject_groups.items():
        indices = sorted(set(indices))
        normal_limit = subject_daily_limits[(class_id, subject)]
        practical = bool(subject_is_practical.get((class_id, subject)))
        count = sum(variables[index] for index in indices)
        # ``daily_max`` is always hard.  A value of 1 can never be relaxed by
        # an internal mode; an explicit value >=2 permits a repeat only on a
        # bounded number of days.  This is the exact version of the user's
        # Algebra/Geometry rule: spread first, use a double only if required.
        per_day_limit = 2
        model.Add(count <= per_day_limit)
        if normal_limit <= 1:
            continue

        # Juft kunlar objective'da jazolanadi: bir juft yetarli bo'lsa
        # ikkinchisi tanlanmaydi. Ammo 5 soat/3 legal kun holatida 2+2+1
        # yechimini qattiq bloklamaymiz.
        allowed_repeat_days = (
            practical_repeat_day_limit if practical else repeat_day_limit
        )
        repeat = model.NewBoolVar(
            f"repeat_{class_id}_{abs(hash(subject))}_{day}_{phase}"
        )
        model.Add(count <= 1 + (per_day_limit - 1) * repeat)
        model.Add(count >= 2 * repeat)
        repeat_bools[(class_id, subject, phase)].append(repeat)
        repeat_group_limits[(class_id, subject, phase)] = int(
            allowed_repeat_days
        )
        weekly_occurrences = len(subject_job_sets.get(
            (class_id, subject, phase), set()
        ))
        # V22.47: 4–5 soatli fan uchun 2+2(+1) legal va foydali bo'lishi
        # mumkin. Shuning uchun bunday juft kunni deyarli taqiqlovchi 5000
        # ball bilan bosmaymiz. Sinf-kun balansi baribir 20000 ball bilan
        # ustun, daily_max=2 va repeat-day limiti esa qattiq qoladi.
        repeat_weight = 250 if weekly_occurrences in {4, 5} else 5_000
        practical_weight = 1_500
        (practical_repeat_terms if practical else repeat_terms).append(
            (repeat, practical_weight if practical else repeat_weight)
        )
        if practical:
            # If the practical fan occurs twice on this day, the two selected
            # occurrence candidates must be adjacent.  Pairwise forbidding is
            # small here (normally 2–3 weekly jobs × six periods) and exact.
            for left_pos, left_index in enumerate(indices):
                for right_index in indices[left_pos + 1:]:
                    left = candidates[left_index]
                    right = candidates[right_index]
                    if left["job_index"] == right["job_index"]:
                        continue
                    if abs(int(left["period"]) - int(right["period"])) != 1:
                        model.Add(variables[left_index] + variables[right_index] <= 1)
    for (class_id, subject, phase), booleans in repeat_bools.items():
        limit = int(repeat_group_limits.get(
            (class_id, subject, phase),
            practical_repeat_day_limit
            if subject_is_practical.get((class_id, subject))
            else repeat_day_limit,
        ))
        model.Add(sum(booleans) <= limit)

    # Daily limit is a real-day limit: an A/B-only lesson is still one full
    # occupied lesson on the phase in which it occurs.  Weekly contractual
    # load keeps half-hour units (2 = regular, 1 = one A/B-week occurrence).
    teacher_daily: dict[tuple[int, int, str], list[int]] = defaultdict(list)
    teacher_week: dict[tuple[int, str], list[tuple[int, int]]] = defaultdict(list)
    for index, row in enumerate(candidates):
        for teacher, phase_loads in row["teacher_phase_loads"].items():
            for phase, units in phase_loads.items():
                teacher_daily[(teacher, row["day"], phase)].append(index)
                teacher_week[(teacher, phase)].append((index, int(units)))
    rules = context.get("rules") or {}
    defaults = context.get("default_rules") or {"kunlik_max": 6}
    for (teacher, day, phase), indices in teacher_daily.items():
        limit = float((rules.get(teacher, defaults) or defaults).get("kunlik_max") or 6)
        model.Add(
            sum(variables[index] for index in sorted(set(indices)))
            <= int(math.floor(limit + 1e-9))
        )
    for (teacher, phase), terms in teacher_week.items():
        cap = (context.get("teacher_caps") or {}).get(teacher)
        if cap is not None:
            model.Add(sum(variables[index] * units for index, units in terms) <= int(math.floor(float(cap) * 2 + 1e-9)))

    # Compact teacher work on one real clock, not on two independent shift
    # counters.  This is soft: hard availability/collisions above are never
    # weakened, yet a needless 4–5 hour wait between shift 1 and shift 2 is
    # far more expensive than an ordinary short school break.
    teacher_real_day: dict[tuple[int, int, str], list[int]] = defaultdict(list)
    for index, row in enumerate(candidates):
        for teacher, phases in row["teacher_phases"].items():
            for phase in phases:
                teacher_real_day[(teacher, row["day"], phase)].append(index)
    teacher_real_idle_terms: list[Any] = []
    teacher_used_day_terms: list[Any] = []
    ordinary_break_minutes = max(
        0, int(context.get("teacher_normal_break_minutes") or 25)
    )
    for (teacher, day, phase), raw_indices in teacher_real_day.items():
        if not quality_enabled:
            continue
        indices = sorted(set(raw_indices))
        if not indices:
            continue
        starts = [int(candidates[index]["interval"][0]) for index in indices]
        ends = [int(candidates[index]["interval"][1]) for index in indices]
        horizon_start = min(starts)
        horizon_end = max(ends)
        label = f"{teacher}_{day}_{phase}"
        used_day = model.NewBoolVar(f"teacher_day_used_{label}")
        model.AddMaxEquality(used_day, [variables[index] for index in indices])
        teacher_used_day_terms.append(used_day)

        lesson_count = model.NewIntVar(0, len(indices), f"teacher_count_{label}")
        model.Add(lesson_count == sum(variables[index] for index in indices))
        first_start = model.NewIntVar(
            horizon_start, horizon_end, f"teacher_first_{label}"
        )
        model.AddMinEquality(first_start, [
            int(candidates[index]["interval"][0]) * variables[index]
            + horizon_end * (1 - variables[index])
            for index in indices
        ])
        last_end = model.NewIntVar(0, horizon_end, f"teacher_last_{label}")
        model.AddMaxEquality(last_end, [
            int(candidates[index]["interval"][1]) * variables[index]
            for index in indices
        ])
        span = model.NewIntVar(
            0, max(0, horizon_end - horizon_start), f"teacher_span_{label}"
        )
        model.Add(span == last_end - first_start).OnlyEnforceIf(used_day)
        model.Add(span == 0).OnlyEnforceIf(used_day.Not())
        occupied_minutes = sum(
            (
                int(candidates[index]["interval"][1])
                - int(candidates[index]["interval"][0])
            ) * variables[index]
            for index in indices
        )
        raw_idle = model.NewIntVar(
            0, max(0, horizon_end - horizon_start), f"teacher_idle_{label}"
        )
        model.Add(raw_idle == span - occupied_minutes).OnlyEnforceIf(used_day)
        model.Add(raw_idle == 0).OnlyEnforceIf(used_day.Not())
        break_count = model.NewIntVar(0, len(indices), f"teacher_breaks_{label}")
        model.AddMaxEquality(break_count, [lesson_count - 1, 0])
        excess_idle = model.NewIntVar(
            0, max(0, horizon_end - horizon_start),
            f"teacher_excess_idle_{label}",
        )
        model.AddMaxEquality(
            excess_idle,
            [raw_idle - ordinary_break_minutes * break_count, 0],
        )
        teacher_real_idle_terms.append(excess_idle)

    # A core subject may use period 6 on at most two class-days per phase.
    core_limit = max(0, int(context.get("core_period6_day_limit", 2)))
    core_by_class_day: dict[tuple[int, int, str], list[int]] = defaultdict(list)
    for index, row in enumerate(candidates):
        if row["period"] != 6:
            continue
        for subject, phases in row["subject_phases"].items():
            profile = (row.get("subject_profiles") or {}).get(subject, {})
            if not profile.get("core_priority"):
                continue
            for phase in phases:
                core_by_class_day[(row["class_id"], row["day"], phase)].append(index)
    core_days: dict[tuple[int, str], list[Any]] = defaultdict(list)
    for (class_id, day, phase), indices in core_by_class_day.items():
        used = model.NewBoolVar(f"core6_{class_id}_{day}_{phase}")
        unique = sorted(set(indices))
        model.Add(sum(variables[index] for index in unique) >= used)
        model.Add(sum(variables[index] for index in unique) <= len(unique) * used)
        core_days[(class_id, phase)].append(used)
    for values in core_days.values():
        model.Add(sum(values) <= core_limit)

    # Teacher internal windows are soft.  Real-time collisions above remain hard.
    teacher_periods: dict[tuple[int, int, int, str, int], list[int]] = defaultdict(list)
    for index, row in enumerate(candidates):
        for teacher, phases in row["teacher_phases"].items():
            for phase in phases:
                teacher_periods[(teacher, row["day"], row["shift"], phase, row["period"])].append(index)
    gap_terms: list[Any] = []
    grouped_teacher_periods: dict[tuple[int, int, int, str], dict[int, list[int]]] = defaultdict(dict)
    for (teacher, day, shift, phase, period), indices in teacher_periods.items():
        grouped_teacher_periods[(teacher, day, shift, phase)][period] = sorted(set(indices))
    for key, period_map in grouped_teacher_periods.items():
        if not quality_enabled:
            continue
        if len(period_map) < 3:
            continue
        max_period = max(period_map)
        used: dict[int, Any] = {}
        for period in range(1, max_period + 1):
            value = model.NewBoolVar(f"tused_{'_'.join(map(str, key))}_{period}")
            indices = period_map.get(period, [])
            if indices:
                model.Add(sum(variables[index] for index in indices) == value)
            else:
                model.Add(value == 0)
            used[period] = value
        for period in range(2, max_period):
            before = model.NewBoolVar(f"tbefore_{'_'.join(map(str, key))}_{period}")
            after = model.NewBoolVar(f"tafter_{'_'.join(map(str, key))}_{period}")
            model.AddMaxEquality(before, [used[item] for item in range(1, period)])
            model.AddMaxEquality(after, [used[item] for item in range(period + 1, max_period + 1)])
            gap = model.NewBoolVar(f"tgap_{'_'.join(map(str, key))}_{period}")
            model.Add(gap <= before)
            model.Add(gap <= after)
            model.Add(gap + used[period] <= 1)
            model.Add(gap >= before + after - used[period] - 1)
            gap_terms.append(gap)

    exception_variables: dict[tuple[int, int, int, int], Any] = {}
    teacher_exception_variables: dict[int, Any] = {}
    if relax_method:
        exception_to_candidates: dict[tuple[int, int, int, int], list[int]] = defaultdict(list)
        for index, row in enumerate(candidates):
            for token in row.get("method_exceptions") or ():
                exception_to_candidates[token].append(index)
        for token, indices in exception_to_candidates.items():
            flag = model.NewBoolVar(f"method_exception_{'_'.join(map(str, token))}")
            for index in sorted(set(indices)):
                model.Add(variables[index] <= flag)
            model.Add(flag <= sum(variables[index] for index in sorted(set(indices))))
            exception_variables[token] = flag
            teacher = token[0]
            teacher_flag = teacher_exception_variables.get(teacher)
            if teacher_flag is None:
                teacher_flag = model.NewBoolVar(f"method_teacher_{teacher}")
                teacher_exception_variables[teacher] = teacher_flag
            model.Add(flag <= teacher_flag)
        for teacher, teacher_flag in teacher_exception_variables.items():
            teacher_flags = [
                flag for token, flag in exception_variables.items() if token[0] == teacher
            ]
            model.Add(teacher_flag <= sum(teacher_flags))
        model.Add(sum(exception_variables.values()) <= 2)
        model.Add(sum(teacher_exception_variables.values()) <= 2)
        if not exception_variables:
            return None, [{"reason": "Metod kunida legal, qizil/BAND bo'lmagan katak topilmadi"}]

    objective_terms: list[Any] = []
    # Candidate-local pedagogical costs.  They cannot sacrifice feasibility.
    for index, row in enumerate(candidates):
        if not quality_enabled:
            break
        job = row["job"]
        profile = subject_profile(job, context)
        period = row["period"]
        cost = 0
        if profile.get("practical"):
            cost += {2: 120, 3: 35, 4: 5, 5: 0, 6: 0}.get(period, 50)
        elif profile.get("core_priority"):
            cost += {1: 8, 2: 0, 3: 0, 4: 3, 5: 35, 6: 240}.get(period, 300)
        elif profile.get("heavy"):
            cost += {1: 8, 2: 0, 3: 0, 4: 5, 5: 25, 6: 90}.get(period, 120)
        elif profile.get("light"):
            cost += {1: 35, 2: 20, 3: 8, 4: 2, 5: 0, 6: 0}.get(period, 10)
        preferred_last = int(job.get("preferred_last") or 6)
        cost += max(0, period - preferred_last) * max(2, int(job.get("weight") or 1) * 4)
        for teacher in row["teachers"]:
            teacher_rules = (rules.get(teacher, defaults) or defaults)
            preferred_shift = int(teacher_rules.get("afzal_smena") or 0)
            if preferred_shift and preferred_shift != row["shift"]:
                cost += 15
            if (teacher, row["day"]) in set(context.get("method_soft") or ()):
                cost += 120
            if _blocked(context.get("soft") or (), teacher, row["day"], row["shift"], period):
                cost += 40
        if cost:
            objective_terms.append(variables[index] * int(cost))
    objective_terms.extend(term * 50 for term in gap_terms)
    # One extra real idle minute costs more than small period preferences;
    # using an additional work day is also discouraged. Daily/weekly caps and
    # all red/method rules remain hard constraints, so these are safe tie-breaks.
    objective_terms.extend(term * 20 for term in teacher_real_idle_terms)
    # V22.47: kam/yengil yuklamali ustozni 2–4 kunga yig'ish uchun bir ortiqcha
    # faol kun sezilarli xarajat. Bu hard kunlik maksimumni hech qachon buzmaydi.
    objective_terms.extend(term * 300 for term in teacher_used_day_terms)
    # 4–5 soatli fan 2+2(+1) bo'lishi mumkin; boshqa fanlarda repeat hanuz
    # juda qimmat. Og'irlik yuqorida haftalik occurrence soniga qarab berildi.
    objective_terms.extend(term * weight for term, weight in repeat_terms)
    objective_terms.extend(term * weight for term, weight in practical_repeat_terms)
    # Sinf kunlari 1/6 yoki 2/6 bo'lib qolmasin. Bu mezon o'qituvchini kam
    # kunga yig'ish va mayda fan-vaqt afzalliklaridan oldin turadi. Masalan
    # 30 soat/6 kun uchun 5+5+5+5+5+5, 29 soat uchun 4+5+5+5+5+5 afzal.
    objective_terms.extend(term * 20_000 for term in balance_terms)
    quality = sum(objective_terms) if objective_terms else 0
    has_objective = False
    if relax_method:
        # This is a diagnostic model, never a saved timetable.  Minimize only
        # the number of explicit method-day exceptions; building the entire
        # comfort objective here made a timeout look like a recommendation.
        model.Minimize(sum(exception_variables.values()))
        has_objective = True
    elif quality_enabled:
        model.Minimize(quality)
        has_objective = True
    return _ModelBundle(
        model=model, jobs=jobs, candidates=candidates, variables=variables,
        by_job=by_job, objective_terms=objective_terms,
        exception_variables=exception_variables,
        teacher_exception_variables=teacher_exception_variables,
        has_objective=has_objective,
        symmetry_breakers=symmetry_breakers,
    ), []


def _class_label(class_id: int, context: Mapping[str, Any]) -> str:
    row = (context.get("classes") or {}).get(int(class_id), {}) or {}
    grade = str(row.get("sinf") or "").strip()
    letter = str(row.get("harf") or "").strip()
    return f"{grade}-{letter}".strip("-") or str(class_id)


def _teacher_label(teacher_id: int, context: Mapping[str, Any]) -> str:
    row = (context.get("teachers") or {}).get(int(teacher_id), {}) or {}
    return str(
        row.get("full_name") or row.get("fish") or row.get("fio")
        or teacher_id
    )


def _capacity_conflicts(
    bundle: _ModelBundle, context: Mapping[str, Any], *, limit: int = 24,
) -> list[dict[str, Any]]:
    """Return proven, user-facing lower-bound conflicts for an UNSAT model.

    CP-SAT can prove that the whole model is infeasible, but a normal solve
    does not automatically explain *which* entity caused it.  These checks do
    not guess from a partial draft.  They compare mandatory job lower bounds
    with the union of legal candidate slots, so every returned shortage is a
    genuine contradiction.  The list may be empty even when the global model
    is infeasible (for example, a longer alternating-resource cycle).
    """

    conflicts: list[dict[str, Any]] = []
    candidates = bundle.candidates
    by_job = bundle.by_job

    # A class has no teacher choice that can change its number of sessions.
    # If even the union of all legal slots is smaller than the required job
    # count, no global reordering can make that class fit.
    class_required: dict[tuple[int, str], int] = defaultdict(int)
    class_slots: dict[tuple[int, str], set[tuple[int, tuple[int, int]]]] = defaultdict(set)
    for job in bundle.jobs:
        class_id = int(job.get("sinf_id") or 0)
        for phase in _job_class_phases(job):
            class_required[(class_id, phase)] += 1
    for row in candidates:
        token = (int(row["day"]), tuple(row["interval"]))
        for phase in row["class_phases"]:
            class_slots[(int(row["class_id"]), str(phase))].add(token)
    for key, required in sorted(class_required.items()):
        available = len(class_slots.get(key, set()))
        if required <= available:
            continue
        class_id, phase = key
        shortage = required - available
        label = _class_label(class_id, context)
        conflicts.append({
            "kind": "class_capacity",
            "class_id": class_id,
            "class_name": label,
            "phase": phase,
            "required_lessons": required,
            "available_lessons": available,
            "shortage": shortage,
            "message": (
                f"{label} sinfning {phase.upper()} haftasida {required} ta dars "
                f"bor, ammo qattiq kun/smena chegaralarida ko'pi bilan "
                f"{available} ta turli legal vaqt katagi qolgan."
            ),
            "solution": (
                "Shu sinfning qat'iy yopilgan kunini yoki oldindan qotirilgan "
                "dars vaqtini tekshiring; qizil/BAND vaqtni taxminan ochmang."
            ),
        })

    # Count only jobs for which a teacher is unavoidable in every candidate.
    # Optional whole-class teacher choices are deliberately not blamed.
    teacher_required: dict[tuple[int, str], int] = defaultdict(int)
    teacher_required_units: dict[tuple[int, str], int] = defaultdict(int)
    for job_index in range(len(bundle.jobs)):
        rows = [candidates[index] for index in by_job.get(job_index, [])]
        if not rows:
            continue
        all_tokens: Optional[set[tuple[int, str]]] = None
        for row in rows:
            row_tokens = {
                (int(teacher), str(phase))
                for teacher, phases in row["teacher_phases"].items()
                for phase in phases
            }
            all_tokens = row_tokens if all_tokens is None else all_tokens.intersection(row_tokens)
        for teacher, phase in sorted(all_tokens or set()):
            teacher_required[(teacher, phase)] += 1
            unit_values = [
                int(row["teacher_phase_loads"][teacher][phase])
                for row in rows
                if teacher in row["teacher_phase_loads"]
                and phase in row["teacher_phase_loads"][teacher]
            ]
            teacher_required_units[(teacher, phase)] += min(unit_values or [2])

    teacher_slots: dict[tuple[int, str, int], set[tuple[int, int]]] = defaultdict(set)
    for row in candidates:
        interval = tuple(row["interval"])
        for teacher, phases in row["teacher_phases"].items():
            for phase in phases:
                teacher_slots[(int(teacher), str(phase), int(row["day"]))].add(interval)
    rules = context.get("rules") or {}
    defaults = context.get("default_rules") or {"kunlik_max": 6}
    method_hard = set(context.get("method_hard") or ())
    for key, required in sorted(teacher_required.items()):
        teacher, phase = key
        daily_limit = int(math.floor(float(
            (rules.get(teacher, defaults) or defaults).get("kunlik_max") or 6
        ) + 1e-9))
        days = sorted({
            day for candidate_teacher, candidate_phase, day in teacher_slots
            if candidate_teacher == teacher and candidate_phase == phase
        })
        available = sum(min(
            daily_limit,
            len(teacher_slots.get((teacher, phase, day), set())),
        ) for day in days)
        cap = (context.get("teacher_caps") or {}).get(teacher)
        cap_lessons = None if cap is None else int(math.floor(float(cap) + 1e-9))
        if cap_lessons is not None:
            available = min(available, cap_lessons)
        required_units = teacher_required_units.get(key, required * 2)
        cap_units = None if cap is None else int(math.floor(float(cap) * 2 + 1e-9))
        unit_shortage = cap_units is not None and required_units > cap_units
        if required <= available and not unit_shortage:
            continue
        label = _teacher_label(teacher, context)
        effective_cap_units = (
            required_units if cap_units is None else cap_units
        )
        shortage = max(required - available, int(math.ceil(
            max(0, required_units - effective_cap_units) / 2
        )))
        method_days = sorted(
            int(day) for candidate_teacher, day in method_hard
            if int(candidate_teacher) == int(teacher)
        )
        method_text = (
            " Metod kuni: " + ", ".join(
                _WEEKDAY_NAMES.get(day, str(day)) for day in method_days
            ) + "."
            if method_days else ""
        )
        conflicts.append({
            "kind": "teacher_capacity",
            "teacher_id": teacher,
            "teacher_name": label,
            "phase": phase,
            "required_lessons": required,
            "available_lessons": available,
            "shortage": max(1, shortage),
            "method_days": method_days,
            "message": (
                f"{label}ning {phase.upper()} haftasida kamida {required} ta "
                f"majburiy darsi bor, ammo qizil/BAND, metod kuni, dars "
                f"oralig'i va kunlik limitdan keyin ko'pi bilan {available} ta "
                f"legal dars sig'adi.{method_text}"
            ),
            "solution": (
                "Pastdagi isbotlangan metod-kuni tavsiyasi chiqsa, faqat o'sha "
                "1–2 katakni administrator qo'lda ochishi mumkin. Aks holda "
                "o'qituvchining yuklamasi yoki qat'iy BAND vaqtini tekshiring."
            ),
        })

    # Singleton domains expose exact fixed collisions directly.
    forced = [
        candidates[indices[0]]
        for indices in by_job.values() if len(indices) == 1
    ]
    for left_index, left in enumerate(forced):
        for right in forced[left_index + 1:]:
            if int(left["day"]) != int(right["day"]):
                continue
            if not intervals_overlap(left["interval"], right["interval"]):
                continue
            shared_phases = set(left["class_phases"]).intersection(right["class_phases"])
            if not shared_phases:
                continue
            resource = None
            if int(left["class_id"]) == int(right["class_id"]):
                resource = f"{_class_label(int(left['class_id']), context)} sinf"
            else:
                shared_teachers = {
                    teacher
                    for teacher in set(left["teachers"]).intersection(right["teachers"])
                    if set(left["teacher_phases"].get(teacher, ())).intersection(
                        right["teacher_phases"].get(teacher, ())
                    )
                }
                if shared_teachers:
                    teacher = sorted(shared_teachers)[0]
                    resource = _teacher_label(int(teacher), context)
                else:
                    shared_rooms = {
                        value for value in left["room_keys"] if value
                    }.intersection(value for value in right["room_keys"] if value)
                    shared_rooms = {
                        room for room in shared_rooms
                        if set(left["room_phases"].get(room, ())).intersection(
                            right["room_phases"].get(room, ())
                        )
                    }
                    if shared_rooms:
                        resource = f"xona {sorted(shared_rooms)[0]}"
            if not resource:
                continue
            left_job = left["job"]
            right_job = right["job"]
            conflicts.append({
                "kind": "fixed_collision",
                "class_id": int(left["class_id"]),
                "class_name": _class_label(int(left["class_id"]), context),
                "resource": resource,
                "day": int(left["day"]),
                "period": int(left["period"]),
                "message": (
                    f"{resource} uchun {_WEEKDAY_NAMES.get(int(left['day']), left['day'])} "
                    f"kuni bir xil real vaqtda ikkita yagona qat'iy variant "
                    f"to'qnashgan: {left_job.get('fan')} va {right_job.get('fan')}."
                ),
                "solution": (
                    "Shu ikki darsdan birining oldindan qotirilgan kun-soatini "
                    "o'zgartiring; qizil/BAND vaqt avtomatik ochilmaydi."
                ),
            })
            if len(conflicts) >= max(1, int(limit)):
                return conflicts[:limit]
    return conflicts[:max(1, int(limit))]


def _new_solver(seed: int, max_seconds: float, context: Mapping[str, Any]) -> Any:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(0.05, float(max_seconds))
    solver.parameters.random_seed = int(seed) & 0x7FFFFFFF
    # One worker is deterministic for a fixed seed/source.  Production may
    # opt into parallel portfolio search explicitly via exact_num_workers.
    solver.parameters.num_search_workers = max(1, min(32, int(context.get("exact_num_workers") or 1)))
    solver.parameters.log_search_progress = bool(context.get("exact_log_search"))
    solver.parameters.stop_after_first_solution = bool(
        context.get("exact_stop_after_first_solution")
    )
    return solver


def _solve_with_user_cancel(solver: Any, model: Any, context: Mapping[str, Any]) -> Any:
    """CP-SATni DBdagi foydalanuvchi signali bilan xavfsiz to‘xtatadi."""
    cancel_requested = context.get("exact_cancel_requested")
    if not callable(cancel_requested):
        return solver.Solve(model)
    watcher_done = threading.Event()

    def watch_cancel() -> None:
        while not watcher_done.wait(0.75):
            try:
                if cancel_requested():
                    solver.StopSearch()
                    return
            except Exception:
                continue

    watcher = threading.Thread(target=watch_cancel, daemon=True)
    watcher.start()
    try:
        return solver.Solve(model)
    finally:
        watcher_done.set()


def _extract_placements(bundle: _ModelBundle, solver: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    placements: list[dict[str, Any]] = []
    chosen: list[dict[str, Any]] = []
    for job_index in range(len(bundle.jobs)):
        selected = [
            index for index in bundle.by_job[job_index]
            if solver.BooleanValue(bundle.variables[index])
        ]
        if len(selected) != 1:
            raise ValueError(
                f"{canonical_job_id(bundle.jobs[job_index], job_index)} uchun "
                f"{len(selected)} ta candidate tanlandi"
            )
        row = bundle.candidates[selected[0]]
        chosen.append(row)
        placements.append({
            "job": bundle.jobs[job_index],
            "day": int(row["day"]), "period": int(row["period"]),
            "teachers": list(row["teachers"]),
            "room_keys": list(row["room_keys"]),
            "method_exceptions": [
                tuple(int(value) for value in token)
                for token in sorted(row.get("method_exceptions") or ())
            ],
        })
    return placements, chosen


def validate_candidate_selection(
    jobs: Iterable[Mapping[str, Any]], selected: Iterable[Mapping[str, Any]],
    context: Mapping[str, Any], *, allow_method_exceptions: bool = False,
) -> list[str]:
    """Independent pure hard-safety validator for selected canonical candidates."""

    jobs = list(jobs)
    selected = [dict(row) for row in selected]
    errors: list[str] = []
    if len(selected) != len(jobs):
        errors.append(f"{len(jobs)} ish uchun {len(selected)} placement qaytdi")
        return errors
    seen_jobs: set[int] = set()
    resource_rows: list[tuple[str, Any, int, str, tuple[int, int], int]] = []
    by_class_day: dict[tuple[int, int, str], set[int]] = defaultdict(set)
    teacher_daily_lessons: dict[tuple[int, int, str], int] = defaultdict(int)
    teacher_week_units: dict[tuple[int, str], int] = defaultdict(int)
    subject_counts: dict[tuple[int, str, int, str], int] = defaultdict(int)
    subject_limits: dict[tuple[int, str], int] = {}
    subject_practical: dict[tuple[int, str], bool] = {}
    subject_periods: dict[tuple[int, str, int, str], list[int]] = defaultdict(list)
    core_days: dict[tuple[int, str], set[int]] = defaultdict(set)
    for row in selected:
        job_index = int(row.get("job_index", -1))
        if job_index not in range(len(jobs)) or job_index in seen_jobs:
            errors.append(f"Takror yoki noto'g'ri job_index: {job_index}")
            continue
        seen_jobs.add(job_index)
        errors.extend(
            f"{canonical_job_id(jobs[job_index], job_index)}: {reason}"
            for reason in candidate_hard_violations(
                row, jobs[job_index], context,
                allow_method_exceptions=allow_method_exceptions,
            )
        )
        interval = tuple(row["interval"])
        for phase in row["class_phases"]:
            resource_rows.append(("sinf", row["class_id"], row["day"], phase, interval, job_index))
            by_class_day[(row["class_id"], row["day"], phase)].add(row["period"])
        for teacher, phases in row["teacher_phases"].items():
            for phase in phases:
                resource_rows.append(("o'qituvchi", teacher, row["day"], phase, interval, job_index))
                units = int(row["teacher_phase_loads"][teacher][phase])
                teacher_daily_lessons[(teacher, row["day"], phase)] += 1
                teacher_week_units[(teacher, phase)] += units
        for room, phases in row["room_phases"].items():
            for phase in phases:
                resource_rows.append(("xona", room, row["day"], phase, interval, job_index))
        for subject, phases in row["subject_phases"].items():
            row_daily_limit = max(1, int(
                (row.get("subject_daily_limits") or {}).get(
                    subject, jobs[job_index].get("daily_max") or 1
                )
            ))
            subject_limits[(row["class_id"], subject)] = min(
                subject_limits.get(
                    (row["class_id"], subject),
                    row_daily_limit,
                ),
                row_daily_limit,
            )
            profile = (row.get("subject_profiles") or {}).get(subject, {})
            subject_practical[(row["class_id"], subject)] = bool(
                subject_practical.get((row["class_id"], subject))
                or profile.get("practical") or profile.get("physical")
                or profile.get("technology")
            )
            for phase in phases:
                subject_counts[(row["class_id"], subject, row["day"], phase)] += 1
                subject_periods[(row["class_id"], subject, row["day"], phase)].append(
                    int(row["period"])
                )
                if (
                    int(row["period"]) == 6
                    and profile.get("core_priority")
                ):
                    core_days[(row["class_id"], phase)].add(row["day"])
    for index, first in enumerate(resource_rows):
        for second in resource_rows[index + 1:]:
            if (
                first[0] == second[0] and first[1] == second[1]
                and first[2] == second[2] and first[3] == second[3]
                and first[5] != second[5] and intervals_overlap(first[4], second[4])
            ):
                errors.append(
                    f"{first[0]} {first[1]}: {first[2]}-kun {first[3]} fazada real-vaqt kolliziyasi"
                )
    for (class_id, day, phase), periods in by_class_day.items():
        if periods and periods != set(range(1, max(periods) + 1)):
            errors.append(f"Sinf {class_id}: {day}-kun {phase} fazada okno bor: {sorted(periods)}")
    rules = context.get("rules") or {}
    defaults = context.get("default_rules") or {"kunlik_max": 6}
    for (teacher, day, phase), lessons in teacher_daily_lessons.items():
        limit = float((rules.get(teacher, defaults) or defaults).get("kunlik_max") or 6)
        if lessons > int(limit + 1e-9):
            errors.append(f"O'qituvchi {teacher}: {day}-kun {phase} kunlik limit oshgan")
    for (teacher, phase), units in teacher_week_units.items():
        cap = (context.get("teacher_caps") or {}).get(teacher)
        if cap is not None and units > int(float(cap) * 2 + 1e-9):
            errors.append(f"O'qituvchi {teacher}: {phase} haftalik limit oshgan")
    repeat_days: dict[tuple[int, str, str], int] = defaultdict(int)
    repeat_limit = max(0, int(context.get("max_subject_repeat_days") or 0))
    practical_repeat_limit = max(
        0, int(context.get("practical_repeat_day_limit", 1))
    )
    effective_repeat_limits: dict[tuple[int, str], int] = {}
    for (class_id, subject, day, phase), count in subject_counts.items():
        daily_max = int(subject_limits.get((class_id, subject), 1))
        practical = bool(subject_practical.get((class_id, subject)))
        allowed_repeat_days = practical_repeat_limit if practical else repeat_limit
        effective_repeat_limits[(class_id, subject)] = int(allowed_repeat_days)
        allowed = min(2, daily_max) if practical else daily_max
        if count > allowed:
            errors.append(f"Sinf {class_id} {subject}: {day}-kun {phase} takror limiti oshgan")
        if count >= 2:
            repeat_days[(class_id, subject, phase)] += 1
        if practical and count == 2:
            periods = sorted(subject_periods[(class_id, subject, day, phase)])
            if len(periods) != 2 or periods[1] - periods[0] != 1:
                errors.append(
                    f"Sinf {class_id} {subject}: {day}-kun {phase} amaliy juft dars yonma-yon emas"
                )
    for key, count in repeat_days.items():
        limit = int(effective_repeat_limits.get(
            key[:2],
            practical_repeat_limit if subject_practical.get(key[:2]) else repeat_limit,
        ))
        if count > limit:
            errors.append(f"Sinf/fan {key}: takror kunlari {count}>{limit}")
    core_limit = max(0, int(context.get("core_period6_day_limit", 2)))
    for key, days in core_days.items():
        if len(days) > core_limit:
            errors.append(f"Sinf/faza {key}: asosiy fan 6-dars kunlari {len(days)}>{core_limit}")
    return list(dict.fromkeys(errors))


def validate_timetable_placements(
    jobs: Iterable[Mapping[str, Any]],
    placements: Iterable[Mapping[str, Any]],
    context: Mapping[str, Any],
    *,
    adapter: Any = None,
    allow_method_exceptions: bool = False,
) -> list[str]:
    """Rebuild canonical candidates and validate a post-processed schedule.

    The school layer may improve class balance or teacher windows after CP-SAT
    returns.  This boundary converts those placements back to the exact
    candidate universe and reruns every hard rule.  A convenience optimizer
    therefore cannot silently invalidate a red/BAND, method, collision or
    capacity rule.
    """

    job_list = [dict(job) for job in jobs]
    placement_list = [dict(row) for row in placements]
    selected_adapter = _adapter_for(adapter=adapter)
    approved_method_tokens = {
        tuple(int(value) for value in token)
        for row in placement_list
        for token in row.get("method_exceptions") or ()
        if len(tuple(token)) == 4
    } if allow_method_exceptions else set()
    ignored_method_days = {
        (teacher, day)
        for teacher, day, _shift, _period in approved_method_tokens
    }
    by_identifier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(placement_list):
        placement_job = row.get("job") or {}
        by_identifier[canonical_job_id(placement_job, index)].append(row)
    selected: list[dict[str, Any]] = []
    errors: list[str] = []
    for job_index, job in enumerate(job_list):
        identifier = canonical_job_id(job, job_index)
        rows = by_identifier.get(identifier) or []
        if len(rows) != 1:
            errors.append(
                f"{identifier}: yakuniy jadvalda {len(rows)} ta placement bor"
            )
            continue
        placement = rows[0]
        expected_teachers = tuple(sorted(
            int(value) for value in placement.get("teachers") or ()
        ))
        expected_rooms = tuple(placement.get("room_keys") or ())
        matches: list[dict[str, Any]] = []
        for raw in selected_adapter.build_candidates(
            job,
            context,
            ignored_method=ignored_method_days,
            mark_method_exceptions=allow_method_exceptions,
        ):
            candidate = _normalize_candidate(raw, job, context)
            if (
                int(candidate["day"]) != int(placement.get("day") or 0)
                or int(candidate["period"]) != int(placement.get("period") or 0)
                or tuple(sorted(int(value) for value in candidate["teachers"]))
                != expected_teachers
            ):
                continue
            if expected_rooms and tuple(candidate.get("room_keys") or ()) != expected_rooms:
                continue
            candidate["job_index"] = job_index
            candidate["job"] = job
            matches.append(candidate)
        if len(matches) != 1:
            errors.append(
                f"{identifier}: yakuniy kun/soat/o'qituvchi exact domenida "
                f"{len(matches)} marta topildi"
            )
            continue
        selected.append(matches[0])
    if errors:
        return list(dict.fromkeys(errors))
    return validate_candidate_selection(
        job_list,
        selected,
        context,
        allow_method_exceptions=allow_method_exceptions,
    )


def _empty_result(status: str, diagnostics: Mapping[str, Any], wall: float = 0.0) -> dict[str, Any]:
    normalized_diagnostics = dict(diagnostics)
    normalized_diagnostics.setdefault("proof_complete", status == INFEASIBLE)
    return {
        "status": status, "complete": False,
        "proof_complete": status == INFEASIBLE,
        "placements": [], "state": None,
        "recommendations": [], "metod_kuni_istisno_tavsiyalari": [],
        "diagnostics": normalized_diagnostics, "objective_value": None,
        "best_bound": None, "wall_time_seconds": round(float(wall), 6),
    }


def _teacher_gap_count_for_rows(rows: Iterable[Mapping[str, Any]], teacher: int, day: int) -> int:
    by_shift_phase: dict[tuple[int, str], set[int]] = defaultdict(set)
    for row in rows:
        phases = (row.get("teacher_phases") or {}).get(teacher, ())
        if int(row.get("day") or 0) != int(day) or not phases:
            continue
        for phase in phases:
            by_shift_phase[(int(row.get("shift") or 1), str(phase))].add(int(row.get("period") or 0))
    return sum(
        max(periods) - min(periods) + 1 - len(periods)
        for periods in by_shift_phase.values() if len(periods) >= 2
    )


def _recommendations_from_relaxed(
    bundle: _ModelBundle, solver: Any, chosen: list[dict[str, Any]],
    context: Mapping[str, Any], *, limit_teachers: int, limit_slots: int,
) -> list[dict[str, Any]]:
    used_tokens = [
        token for token, variable in bundle.exception_variables.items()
        if solver.BooleanValue(variable)
    ]
    teachers_info = context.get("teachers") or {}
    rows: list[dict[str, Any]] = []
    seen_teachers: set[int] = set()
    for token in sorted(used_tokens, key=lambda item: (item[1], item[2], item[3], item[0])):
        teacher, day, shift, period = token
        if teacher not in seen_teachers and len(seen_teachers) >= max(1, int(limit_teachers)):
            continue
        assigned = [
            row for row in chosen
            if token in set(row.get("method_exceptions") or ())
        ]
        if not assigned:
            continue
        before_gap = _teacher_gap_count_for_rows(
            [row for row in chosen if row not in assigned], teacher, day
        )
        after_gap = _teacher_gap_count_for_rows(chosen, teacher, day)
        teacher_row = teachers_info.get(teacher, {}) if isinstance(teachers_info, Mapping) else {}
        teacher_name = (
            (teacher_row or {}).get("full_name")
            or (teacher_row or {}).get("fish")
            or str(teacher)
        )
        interval = _slot_interval(context, shift, period)
        lesson_names = [
            f"{row['job'].get('fan','Dars')} ({row['job'].get('sinf_id','?')}-sinf)"
            for row in assigned
        ]
        seen_teachers.add(teacher)
        rows.append({
            "raqam": len(rows) + 1,
            "oqituvchi_id": int(teacher), "oqituvchi": str(teacher_name),
            "kun": int(day), "kun_nomi": _WEEKDAY_NAMES.get(int(day), str(day)),
            "smena": int(shift), "dars": int(period),
            "vaqt": _format_interval(interval),
            "turi": "metod_kuni", "isbotlangan": True,
            "sabab": (
                "Alohida diagnostik exact model shu metod-kuni katagini ochsa "
                "barcha dars qat'iy qoidalar ichida joylashishini topdi."
            ),
            "joylashadigan_darslar": lesson_names,
            "kamayadigan_oynalar": max(0, before_gap - after_gap),
            "qizil_buzilmaydi": True,
            "avtomatik_qollanmagan": True,
            "amal": (
                f"{teacher_name} uchun {_WEEKDAY_NAMES.get(int(day), day)} kuni "
                f"faqat {period}-darsni metod-kuni istisnosi sifatida administrator tasdiqlashi mumkin."
            ),
        })
        if len(rows) >= max(1, int(limit_slots)):
            break
    return rows


def _analyze_method_day_relaxations_detailed(
    jobs: Iterable[Mapping[str, Any]], context: Mapping[str, Any],
    candidate_builder: Any = None, *, adapter: Any = None,
    seed: int = 0, max_seconds: float = 2.0,
    limit_teachers: int = 2, limit_slots: int = 2,
) -> dict[str, Any]:
    """Run a bounded CP model with at most two method exceptions.

    BAND/red slots remain absent from candidate domains.  A recommendation is
    returned only when this relaxed model itself finds a *complete* schedule.
    Placements are kept inside the detailed private result so an explicitly
    enabled production fallback can save the same independently validated
    solution instead of solving a third model.
    """

    started = time.monotonic()

    def finish(status: str, message: str, recommendations=None, **extra):
        return {
            "status": str(status),
            "message": str(message),
            "recommendations": list(recommendations or []),
            "wall_time_seconds": round(time.monotonic() - started, 6),
            **extra,
        }

    if cp_model is None:
        return finish("NOT_AVAILABLE", "OR-Tools mavjud emas.")
    if not jobs:
        return finish("NOT_NEEDED", "Jadvalda dars yo'q.")
    if not (context.get("method_hard") or ()):
        return finish("NOT_NEEDED", "Qattiq metod kuni belgilanmagan.")
    try:
        selected_adapter = _adapter_for(candidate_builder, adapter)
        if not bool(getattr(selected_adapter, "supports_method_relaxation", False)):
            return finish(
                "UNSUPPORTED",
                "Tanlangan candidate adapter metod-kuni diagnostikasini qo'llamaydi.",
            )
        job_list = [dict(job) for job in jobs]
        bundle, empty = _build_model(
            job_list,
            context,
            selected_adapter,
            relax_method=True,
            feasibility_only=True,
        )
        if bundle is None or empty:
            return finish(
                "INFEASIBLE",
                "Ko'pi bilan ikki metod katagini ochganda ham ayrim darsda legal domen qolmadi.",
                empty_domains=empty,
            )
        solver = _new_solver(seed ^ 0x4D455448, max_seconds, context)
        raw_status = _solve_with_user_cancel(solver, bundle.model, context)
        status = _model_status_name(raw_status)
        if status not in {FEASIBLE, OPTIMAL}:
            return finish(
                status,
                (
                    "Ikki metod katagigacha bo'lgan diagnostik model ham yechimsiz."
                    if status == INFEASIBLE else
                    "Metod-kuni diagnostikasi vaqt ichida yakuniy xulosa bermadi."
                ),
                conflicts=int(solver.NumConflicts()),
                branches=int(solver.NumBranches()),
            )
        placements, chosen = _extract_placements(bundle, solver)
        validation_errors = validate_candidate_selection(
            job_list, chosen, context, allow_method_exceptions=True
        )
        if validation_errors:
            # The pure validator sees method slots as candidates but never
            # treats them as BAND.  Any other hard error suppresses advice.
            return finish(
                "MODEL_INVALID",
                "Metod-kuni diagnostik natijasi mustaqil hard-validator tekshiruvidan o'tmadi.",
                validation_errors=validation_errors,
            )
        recommendations = _recommendations_from_relaxed(
            bundle, solver, chosen, context,
            limit_teachers=limit_teachers, limit_slots=limit_slots,
        )
        return finish(
            status,
            (
                "Quyidagi aniq metod kataklari bilan to'liq jadval topildi."
                if recommendations else
                "Relaxed model to'liq bo'ldi, ammo ishlatilgan metod istisnosi topilmadi."
            ),
            recommendations,
            placements=placements,
            method_exceptions=sorted({
                tuple(int(value) for value in token)
                for row in chosen
                for token in row.get("method_exceptions") or ()
            }),
            conflicts=int(solver.NumConflicts()),
            branches=int(solver.NumBranches()),
        )
    except Exception as error:
        # Advice is optional and must never turn a strict solve into a crash.
        return finish(
            "ERROR",
            f"Metod-kuni diagnostikasida {type(error).__name__}: {error}",
        )


def analyze_method_day_relaxations(
    jobs: Iterable[Mapping[str, Any]], context: Mapping[str, Any],
    candidate_builder: Any = None, *, adapter: Any = None,
    seed: int = 0, max_seconds: float = 2.0,
    limit_teachers: int = 2, limit_slots: int = 2,
) -> list[dict[str, Any]]:
    """Backward-compatible list API for the detailed method-day analysis."""

    detail = _analyze_method_day_relaxations_detailed(
        jobs, context, candidate_builder, adapter=adapter,
        seed=seed, max_seconds=max_seconds,
        limit_teachers=limit_teachers, limit_slots=limit_slots,
    )
    return list(detail.get("recommendations") or [])


def solve_exact_timetable(
    jobs: Iterable[Mapping[str, Any]], context: Mapping[str, Any],
    candidate_builder: Any = None, *, adapter: Any = None,
    state_builder: Optional[Callable[[list[dict[str, Any]], Mapping[str, Any]], Any]] = None,
    seed: int = 0, max_seconds: float = 20.0,
) -> dict[str, Any]:
    """Solve one complete timetable or return a precise CP-SAT status.

    ``FEASIBLE`` and ``OPTIMAL`` always contain exactly one placement for every
    input job and pass an independent hard-safety validator.  No partial draft
    is returned for ``UNKNOWN`` or ``INFEASIBLE``.
    """

    started = time.monotonic()
    if cp_model is None:
        missing = bool(
            isinstance(_ORTOOLS_IMPORT_ERROR, ModuleNotFoundError)
            and str(getattr(_ORTOOLS_IMPORT_ERROR, "name", "")).split(".")[0]
            == "ortools"
        )
        return _empty_result(MODEL_INVALID, {
            "code": "ORTOOLS_NOT_INSTALLED" if missing else "ORTOOLS_IMPORT_FAILED",
            "message": (
                "Exact jadval uchun google-ortools paketi o'rnatilmagan."
                if missing else
                "Google OR-Tools import qilindi, lekin uning Python/binary bog'liqligi yuklanmadi."
            ),
            "import_error": (
                None if _ORTOOLS_IMPORT_ERROR is None else
                f"{type(_ORTOOLS_IMPORT_ERROR).__name__}: {_ORTOOLS_IMPORT_ERROR}"
            ),
            "metod_kuni_istisno_tavsiyalari": [],
        }, time.monotonic() - started)
    try:
        numeric_max_seconds = float(max_seconds)
    except (TypeError, ValueError):
        return _empty_result(MODEL_INVALID, {
            "code": "INVALID_TIME_BUDGET",
            "message": "max_seconds son bo'lishi kerak.",
        }, time.monotonic() - started)
    if numeric_max_seconds <= 0:
        return _empty_result(UNKNOWN, {
            "code": "ZERO_TIME_BUDGET",
            "message": "Exact qidiruv uchun musbat vaqt ajratilmadi; imkonsizlik isbotlanmadi.",
            "metod_kuni_istisno_tavsiyalari": [],
        }, time.monotonic() - started)
    try:
        job_list = [dict(job) for job in jobs]
        identifiers = [canonical_job_id(job, index) for index, job in enumerate(job_list)]
        duplicates = sorted({value for value in identifiers if identifiers.count(value) > 1})
        if duplicates:
            return _empty_result(MODEL_INVALID, {
                "code": "DUPLICATE_JOB_ID", "duplicate_job_ids": duplicates,
                "message": "Har bir dars ishining job_id qiymati yagona bo'lishi kerak.",
            }, time.monotonic() - started)
        if not job_list:
            state = state_builder([], context) if callable(state_builder) else {"placements": []}
            return {
                "status": OPTIMAL, "complete": True, "proof_complete": True,
                "placements": [], "state": state,
                "recommendations": [], "metod_kuni_istisno_tavsiyalari": [],
                "diagnostics": {
                    "code": "EMPTY_TIMETABLE", "jobs": 0,
                    "proof_complete": True, "validator_passed": True,
                },
                "objective_value": 0.0, "best_bound": 0.0,
                "wall_time_seconds": round(time.monotonic() - started, 6),
            }
        selected_adapter = _adapter_for(candidate_builder, adapter)
        feasibility_only = bool(context.get("exact_feasibility_only"))

        def remaining_method_analysis_seconds() -> float:
            """Keep strict + bounded fallback inside the one exact budget."""

            try:
                requested = max(
                    0.0,
                    float(context.get("exact_relaxation_seconds") or min(
                        4.0, max(0.1, numeric_max_seconds * 0.2)
                    )),
                )
            except (TypeError, ValueError):
                requested = min(4.0, max(0.1, numeric_max_seconds * 0.2))
            remaining = max(
                0.05,
                numeric_max_seconds - (time.monotonic() - started) - 0.10,
            )
            return min(requested, remaining)

        def bounded_method_fallback_result(
            method_analysis: Mapping[str, Any],
            strict_status: str,
            strict_diagnostics: Mapping[str, Any],
        ) -> Optional[dict[str, Any]]:
            """Return the proven max-two-slot method fallback when enabled."""

            if not bool(context.get("exact_apply_bounded_method_fallback")):
                return None
            if str(strict_status).upper() != INFEASIBLE:
                return None
            if str(method_analysis.get("status") or "").upper() not in {
                FEASIBLE,
                OPTIMAL,
            }:
                return None
            relaxed_placements = [
                dict(row) for row in method_analysis.get("placements") or []
            ]
            used_exceptions = sorted({
                tuple(int(value) for value in token)
                for row in relaxed_placements
                for token in row.get("method_exceptions") or ()
            })
            if len(relaxed_placements) != len(job_list) or not used_exceptions:
                return None
            if len(used_exceptions) > 2:
                return None
            relaxed_errors = validate_timetable_placements(
                job_list,
                relaxed_placements,
                context,
                adapter=selected_adapter,
                allow_method_exceptions=True,
            )
            if relaxed_errors:
                return None
            recommendations = []
            for raw_recommendation in method_analysis.get("recommendations") or []:
                recommendation = dict(raw_recommendation)
                recommendation["avtomatik_qollanmagan"] = False
                recommendation["avtomatik_qollanildi"] = True
                recommendations.append(recommendation)
            relaxed_state = (
                state_builder(relaxed_placements, context)
                if callable(state_builder)
                else {"placements": relaxed_placements}
            )
            diagnostics = dict(strict_diagnostics)
            diagnostics.update({
                "code": "EXACT_BOUNDED_METHOD_FALLBACK",
                "message": (
                    "Strict model yechimsiz edi; qizil/BAND vaqtini ochmasdan "
                    "boshlang'ich sinf o'qituvchilarining ko'pi bilan ikki "
                    "aniq metod-kuni katagi bilan barcha dars joylashtirildi."
                ),
                "strict_solver_status": INFEASIBLE,
                "strict_proof_complete": True,
                "method_exception_applied": True,
                "applied_method_exceptions": [
                    list(token) for token in used_exceptions
                ],
                "metod_kuni_istisno_tavsiyalari": recommendations,
                "metod_kuni_tahlili": dict(method_analysis),
                "validator_passed": True,
                "proof_complete": True,
            })
            # The private analysis carries placements only for this handoff;
            # do not duplicate the whole schedule inside public diagnostics.
            diagnostics["metod_kuni_tahlili"].pop("placements", None)
            return {
                "status": FEASIBLE,
                "complete": True,
                "proof_complete": True,
                "placements": relaxed_placements,
                "state": relaxed_state,
                "recommendations": recommendations,
                "metod_kuni_istisno_tavsiyalari": recommendations,
                "method_exception_applied": True,
                "applied_method_exceptions": [
                    list(token) for token in used_exceptions
                ],
                "diagnostics": diagnostics,
                "objective_value": 0.0,
                "best_bound": 0.0,
                "wall_time_seconds": round(time.monotonic() - started, 6),
            }

        bundle, empty = _build_model(
            job_list,
            context,
            selected_adapter,
            relax_method=False,
            feasibility_only=feasibility_only,
        )
        if bundle is None:
            method_analysis = (
                _analyze_method_day_relaxations_detailed(
                    job_list, context, candidate_builder,
                    adapter=adapter, seed=seed,
                    max_seconds=remaining_method_analysis_seconds(),
                )
                if empty and bool(context.get("exact_analyze_method_relaxation", True))
                else {"status": "NOT_RUN", "recommendations": []}
            )
            recommendations = list(method_analysis.get("recommendations") or [])
            fallback = bounded_method_fallback_result(
                method_analysis,
                INFEASIBLE if empty else MODEL_INVALID,
                {
                    "code": "EMPTY_CANDIDATE_DOMAIN" if empty else "MODEL_BUILD_FAILED",
                    "empty_domains": empty,
                    "metod_kuni_tahlili": method_analysis,
                },
            )
            if fallback is not None:
                return fallback
            result = _empty_result(INFEASIBLE if empty else MODEL_INVALID, {
                "code": "EMPTY_CANDIDATE_DOMAIN" if empty else "MODEL_BUILD_FAILED",
                "empty_domains": empty,
                "message": "Kamida bitta dars uchun qat'iy qoidalar ichida legal katak yo'q.",
                "metod_kuni_istisno_tavsiyalari": recommendations,
                "metod_kuni_tahlili": method_analysis,
            }, time.monotonic() - started)
            result["recommendations"] = recommendations
            result["metod_kuni_istisno_tavsiyalari"] = recommendations
            return result
        solver = _new_solver(seed, numeric_max_seconds, context)
        raw_status = _solve_with_user_cancel(solver, bundle.model, context)
        status = _model_status_name(raw_status)
        diagnostics: dict[str, Any] = {
            "code": "EXACT_CP_SAT", "jobs": len(job_list),
            "candidates": len(bundle.candidates),
            "model_variables": len(bundle.model.Proto().variables),
            "model_constraints": len(bundle.model.Proto().constraints),
            "solve_stage": (
                "hard_feasibility" if feasibility_only else "quality"
            ),
            "quality_optimized": bool(bundle.has_objective),
            "symmetry_breakers": int(bundle.symmetry_breakers),
            "conflicts": int(solver.NumConflicts()),
            "branches": int(solver.NumBranches()),
            "solver_wall_time_seconds": float(solver.WallTime()),
            "metod_kuni_istisno_tavsiyalari": [],
            "proof_complete": status == INFEASIBLE,
        }
        if status not in {FEASIBLE, OPTIMAL}:
            recommendations = []
            method_analysis = {"status": "NOT_RUN", "recommendations": []}
            if (
                status == INFEASIBLE
                or (
                    status == UNKNOWN
                    and bool(context.get("exact_analyze_method_on_unknown"))
                )
            ) and bool(context.get("exact_analyze_method_relaxation", True)):
                method_analysis = _analyze_method_day_relaxations_detailed(
                    job_list, context, candidate_builder, adapter=adapter, seed=seed,
                    max_seconds=remaining_method_analysis_seconds(),
                )
                recommendations = list(method_analysis.get("recommendations") or [])
            diagnostics["metod_kuni_istisno_tavsiyalari"] = recommendations
            diagnostics["metod_kuni_tahlili"] = method_analysis
            fallback = bounded_method_fallback_result(
                method_analysis,
                status,
                diagnostics,
            )
            if fallback is not None:
                return fallback
            if status == INFEASIBLE:
                hard_conflicts = _capacity_conflicts(bundle, context)
                if not hard_conflicts:
                    hard_conflicts = [{
                        "kind": "global_resource_cycle",
                        "message": (
                            "Har bir darsning alohida legal katagi bor, ammo "
                            "ularni sinf, o'qituvchi va xona real-vaqt "
                            "to'qnashuvlarisiz bir vaqtda tanlab bo'lmadi."
                        ),
                        "solution": (
                            "Pastdagi metod-kuni tavsiyasi bo'lsa faqat o'sha "
                            "aniq katakni ko'rib chiqing. Tavsiya bo'lmasa "
                            "o'qituvchilarning qat'iy BAND va eng erta–eng "
                            "kech dars oralig'ini tekshiring."
                        ),
                    }]
                diagnostics["hard_conflicts"] = hard_conflicts
            diagnostics["message"] = {
                INFEASIBLE: "Qattiq qoidalar ichida to'liq jadval matematik jihatdan mavjud emas.",
                UNKNOWN: "Ajratilgan vaqtda to'liq yechim ham, imkonsizlik isboti ham topilmadi.",
                MODEL_INVALID: "CP-SAT modeli yaroqsiz deb topildi.",
            }.get(status, "Exact solver yakuniy yechim qaytarmadi.")
            result = _empty_result(status, diagnostics, time.monotonic() - started)
            result["recommendations"] = recommendations
            result["metod_kuni_istisno_tavsiyalari"] = recommendations
            if bundle.has_objective:
                try:
                    result["best_bound"] = float(solver.BestObjectiveBound())
                except Exception:
                    pass
            return result
        placements, chosen = _extract_placements(bundle, solver)
        validation_errors = validate_candidate_selection(job_list, chosen, context)
        if validation_errors:
            return _empty_result(MODEL_INVALID, {
                **diagnostics,
                "code": "POST_SOLVE_VALIDATION_FAILED",
                "message": "Exact natija mustaqil hard-validator tekshiruvidan o'tmadi.",
                "validation_errors": validation_errors,
            }, time.monotonic() - started)

        progress_callback = context.get("exact_progress_callback")
        if callable(progress_callback):
            try:
                progress_callback("hard_feasible", {
                    "placed": len(placements),
                    "total": len(job_list),
                    "status": status,
                })
            except Exception:
                pass

        objective_value = (
            float(solver.ObjectiveValue()) if bundle.has_objective else 0.0
        )
        best_bound = (
            float(solver.BestObjectiveBound()) if bundle.has_objective else 0.0
        )
        # Feasibility is never sacrificed for comfort. Once the first full
        # hard-safe timetable exists, a short second CP-SAT pass receives that
        # exact timetable as a complete hint and may globally rearrange all
        # classes. This is what lets Algebra+Algebra trade with the same
        # teacher's Geometry lesson even when it belongs to another class.
        if feasibility_only and bool(context.get("exact_quality_after_feasible")):
            try:
                requested_quality_seconds = max(
                    0.0, float(context.get("exact_quality_seconds") or 2.0)
                )
            except (TypeError, ValueError):
                requested_quality_seconds = 2.0
            remaining_before_build = (
                numeric_max_seconds - (time.monotonic() - started)
            )
            if requested_quality_seconds > 0 and remaining_before_build >= 0.75:
                quality_bundle, quality_empty = _build_model(
                    job_list,
                    context,
                    selected_adapter,
                    relax_method=False,
                    feasibility_only=False,
                )
                remaining_after_build = (
                    numeric_max_seconds - (time.monotonic() - started)
                )
                quality_seconds = min(
                    requested_quality_seconds,
                    max(0.0, remaining_after_build - 0.15),
                )
                if (
                    quality_bundle is not None
                    and quality_bundle.has_objective
                    and not quality_empty
                    and quality_seconds >= 0.20
                ):
                    hinted_indices: set[int] = set()
                    complete_hint = True
                    for job_index, incumbent in enumerate(chosen):
                        incumbent_signature = _candidate_hard_signature(incumbent)
                        matches = [
                            index for index in quality_bundle.by_job[job_index]
                            if _candidate_hard_signature(
                                quality_bundle.candidates[index]
                            ) == incumbent_signature
                        ]
                        if len(matches) != 1:
                            complete_hint = False
                            break
                        hinted_indices.add(matches[0])
                    if complete_hint:
                        for index, variable in enumerate(quality_bundle.variables):
                            quality_bundle.model.AddHint(
                                variable, 1 if index in hinted_indices else 0
                            )
                        quality_context = dict(context)
                        quality_context["exact_stop_after_first_solution"] = False
                        quality_solver = _new_solver(
                            seed ^ 0x21_09_51,
                            quality_seconds,
                            quality_context,
                        )
                        quality_raw_status = _solve_with_user_cancel(
                            quality_solver, quality_bundle.model, quality_context
                        )
                        quality_status = _model_status_name(quality_raw_status)
                        diagnostics["quality_refinement"] = {
                            "status": quality_status,
                            "seconds": round(float(quality_solver.WallTime()), 6),
                            "incumbent_hint_complete": True,
                        }
                        if quality_status in {FEASIBLE, OPTIMAL}:
                            refined_placements, refined_chosen = _extract_placements(
                                quality_bundle, quality_solver
                            )
                            refined_errors = validate_candidate_selection(
                                job_list, refined_chosen, context
                            )
                            if not refined_errors:
                                placements, chosen = (
                                    refined_placements, refined_chosen
                                )
                                objective_value = float(
                                    quality_solver.ObjectiveValue()
                                )
                                best_bound = float(
                                    quality_solver.BestObjectiveBound()
                                )
                                diagnostics["quality_optimized"] = True
                                diagnostics["quality_refinement"][
                                    "validator_passed"
                                ] = True
                                if callable(progress_callback):
                                    try:
                                        progress_callback("quality_accepted", {
                                            "placed": len(placements),
                                            "total": len(job_list),
                                            "status": quality_status,
                                        })
                                    except Exception:
                                        pass
                            else:
                                diagnostics["quality_refinement"][
                                    "validation_errors"
                                ] = refined_errors[:20]
                    else:
                        diagnostics["quality_refinement"] = {
                            "status": "SKIPPED",
                            "reason": "incumbent candidate hint yagona emas",
                            "incumbent_hint_complete": False,
                        }
        state = state_builder(placements, context) if callable(state_builder) else {"placements": placements}
        diagnostics["message"] = "Barcha dars aynan bir marta joylashtirildi va hard-validator tasdiqladi."
        diagnostics["validator_passed"] = True
        return {
            "status": status, "complete": True, "proof_complete": True,
            "placements": placements, "state": state,
            "recommendations": [], "metod_kuni_istisno_tavsiyalari": [],
            "diagnostics": diagnostics,
            "objective_value": objective_value,
            "best_bound": best_bound,
            "wall_time_seconds": round(time.monotonic() - started, 6),
        }
    except (TypeError, ValueError, KeyError) as error:
        return _empty_result(MODEL_INVALID, {
            "code": "MODEL_INPUT_INVALID", "message": str(error),
        }, time.monotonic() - started)
    except Exception as error:  # Production boundary: never crash the worker.
        return _empty_result(MODEL_INVALID, {
            "code": "MODEL_BUILD_EXCEPTION",
            "message": f"{type(error).__name__}: {error}",
        }, time.monotonic() - started)


__all__ = [
    "OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN", "MODEL_INVALID",
    "EXACT_STATUSES", "ORTOOLS_AVAILABLE", "ortools_available",
    "normalize_phase", "expand_phases", "phases_overlap", "intervals_overlap",
    "canonical_job_id", "subject_profile", "DefaultTimetableAdapter",
    "CallableCandidateAdapter", "candidate_hard_violations",
    "validate_candidate_selection", "validate_timetable_placements",
    "analyze_method_day_relaxations", "solve_exact_timetable",
]

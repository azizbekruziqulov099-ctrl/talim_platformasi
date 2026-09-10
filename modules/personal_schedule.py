"""Private weekly plans, grounded in the active admin curriculum and DTS.

No changes to official school timetables. All records are scoped to an authenticated
owner, grade, language and Monday; old v1 personal plans remain untouched.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from psycopg2.extras import Json

DAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]
ACTIVITIES = {"lesson", "review", "control", "problem", "project", "oral"}
LANGUAGES = {"uz", "ru", "en"}


def fail(message, status=422):
    raise HTTPException(status_code=status, detail=message)


def as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        fail("Sana YYYY-MM-DD shaklida bo'lishi kerak")


def monday(value=None):
    day = as_date(value) if value else datetime.now(ZoneInfo("Asia/Tashkent")).date()
    return day - timedelta(days=day.weekday())


def subject_key(value):
    return re.sub(r"[^\w]+", "", str(value or "").casefold().replace("ё", "е"))


def fixed_subject(value):
    return subject_key(value) in {"kelajaksoati", "sinfsoati"}


def grade_number(value):
    found = re.fullmatch(r"\s*(1[01]|[1-9])(?:\s*[-–]?\s*(?:sinf|[a-zа-я]))?\s*", str(value or ""), re.I)
    return int(found.group(1)) if found else None


def quarter_number(value):
    text = str(value or "").strip().casefold()
    match = re.fullmatch(r"(?:chorak\s*)?([1-4])(?:\s*[-.]?\s*(?:chorak|quarter))?", text)
    if match:
        return int(match.group(1))
    roman = re.fullmatch(r"(i|ii|iii|iv)(?:\s*[-.]?\s*chorak)?", text)
    return {"i": 1, "ii": 2, "iii": 3, "iv": 4}[roman.group(1)] if roman else None


def curriculum_rows(rows, week):
    """A .5 hour alternates; no rounding away subjects or adding unapproved ones."""
    result = []
    seen = set()
    half_index = 0
    parity = (monday(week) - date(2020, 1, 6)).days // 7 % 2
    for row in rows:
        name = str(row.get("subject") or row.get("fan_nomi") or "").strip()
        key = subject_key(name)
        if not key or key in seen:
            fail("Admin o'quv rejasida fan nomi bo'sh yoki takrorlangan; andozani tekshiring")
        seen.add(key)
        try:
            hours = Decimal(str(row.get("weekly_hours", row.get("haftalik_soat", 0))))
        except InvalidOperation:
            fail(f"{name}: haftalik soat noto'g'ri")
        if not hours.is_finite() or hours < 0 or hours > 20 or hours * 2 != int(hours * 2):
            fail(f"{name}: haftalik soat 0–20 oralig'ida, 0.5 qadamda bo'lishi kerak")
        if not hours:
            continue
        count = int(hours)
        half = hours != count
        if half:
            count += int(parity == half_index % 2)
            half_index += 1
        limit = int(row.get("kunlik_max") or 1)
        method = row.get("metod_kuni")
        if limit not in range(1, 5) or (method is not None and int(method) not in range(1, 8)):
            fail(f"{name}: admin kunlik cheklovi noto'g'ri")
        result.append({"subject": name, "weekly_hours": float(hours), "week_hours": count,
                       "metod_kuni": int(method) if method is not None else None,
                       "kunlik_max": limit, "alternating": half})
    if not result:
        fail("Bu sinf va ta'lim tili uchun faol admin o'quv rejasi topilmadi. Maktab tasdig'i shart emas; markaziy andozaga fan-soatlar kiritilishi kerak.")
    return result


def _add_edge(graph, source, target, capacity, cost):
    forward = [target, len(graph[target]), capacity, cost]
    reverse = [source, len(graph[source]), 0, -cost]
    graph[source].append(forward)
    graph[target].append(reverse)
    return forward


def distribute(curriculum, study_days=5, max_lessons=8, seed=0):
    """Bounded integral min-cost flow: exact hours, hard day limits, balanced loads.

    A convex cost for each extra daily lesson dominates small deterministic mixing
    costs. Residual edges repair greedy dead ends; no random retry loops.
    """
    if study_days not in (5, 6) or not 1 <= max_lessons <= 12:
        fail("O'quv kunlari yoki kunlik dars chegarasi noto'g'ri")
    placed = [[] for _ in range(study_days)]
    counts = [r["week_hours"] for r in curriculum]
    reserved = next((i for i, row in enumerate(curriculum) if fixed_subject(row["subject"]) and counts[i]), None)
    if reserved is not None:
        if curriculum[reserved]["metod_kuni"] == 1:
            fail("Kelajak soati dushanba 1-darsga qo'yiladi, lekin admin andozasida dushanba metod kuni qilib belgilangan")
        placed[0].append(curriculum[reserved]["subject"])
        counts[reserved] -= 1
    total = sum(counts)
    if total + int(reserved is not None) > study_days * max_lessons:
        fail("O'quv rejasidagi soatlar belgilangan kunlar va dars vaqtlariga sig'maydi")
    n = len(curriculum)
    source, day_base, sink = 0, n + 1, n + study_days + 1
    graph = [[] for _ in range(sink + 1)]
    links = []
    for index, row in enumerate(curriculum):
        node = index + 1
        _add_edge(graph, source, node, counts[index], 0)
        for day in range(study_days):
            cap = row["kunlik_max"] - (1 if day == 0 and reserved == index else 0)
            if row["metod_kuni"] == day + 1 or cap <= 0:
                continue
            mix = int(hashlib.sha256(f"{subject_key(row['subject'])}:{day}:{seed}".encode()).hexdigest()[:4], 16) % 13
            edge = _add_edge(graph, node, day_base + day, cap, mix)
            links.append((index, day, cap, edge))
    # Tuesday/Thursday extra lessons provide a gentler 4,5,4,5,4 pattern when feasible.
    preference = [2, 0, 3, 1, 5, 4]
    for day in range(study_days):
        for load in range(len(placed[day]), max_lessons):
            _add_edge(graph, day_base + day, sink, 1, load * 1000 + preference[day] * 20)
    sent = 0
    while sent < total:
        distance = [float("inf")] * len(graph)
        previous = [None] * len(graph)
        distance[source] = 0
        for _ in range(len(graph) - 1):
            changed = False
            for node, edges in enumerate(graph):
                if distance[node] == float("inf"):
                    continue
                for ei, edge in enumerate(edges):
                    target, _, cap, cost = edge
                    if cap and distance[target] > distance[node] + cost:
                        distance[target] = distance[node] + cost
                        previous[target] = (node, ei)
                        changed = True
            if not changed:
                break
        if previous[sink] is None:
            fail("Fan soatlari metod kunlari va kunlik maksimumga sig'maydi. Admin andozasidagi cheklovlarni tekshiring; soatlar yashirin kamaytirilmaydi.")
        node = sink
        while node != source:
            parent, ei = previous[node]
            edge = graph[parent][ei]
            edge[2] -= 1
            graph[node][edge[1]][2] += 1
            node = parent
        sent += 1
    for index, day, capacity, edge in links:
        placed[day].extend([curriculum[index]["subject"]] * (capacity - edge[2]))
    # Rotate order by day/week while keeping the one requested fixed lesson first.
    for day, items in enumerate(placed):
        fixed = items[:1] if day == 0 and reserved is not None else []
        rest = items[len(fixed):]
        rest.sort(key=lambda s: hashlib.sha256(f"{s}:{day}:{seed}:order".encode()).hexdigest())
        # Spread a repeated subject within a day whenever another subject remains.
        ordered = []
        while rest:
            index = next((i for i, name in enumerate(rest) if not ordered or name != ordered[-1]), 0)
            ordered.append(rest.pop(index))
        placed[day] = fixed + ordered
    return placed


def lesson_times(shift=1, settings=None):
    settings = settings or {}
    start_text = str(settings.get("boshlanish_vaqti") or ("13:30" if shift == 2 else "08:00"))
    start_parts = start_text.split(":")
    current = int(start_parts[0]) * 60 + int(start_parts[1])
    duration = int(settings.get("dars_daqiqa") or 45)
    pause = int(settings.get("tanaffus_daqiqa", 5))
    max_count = int(settings.get("dars_soni") or 8)
    result = []
    for order in range(1, max_count + 1):
        end = current + duration
        if end >= 24 * 60:
            fail("Smena vaqtlari bir kun chegarasidan oshmoqda")
        result.append(f"{current // 60:02d}:{current % 60:02d}–{end // 60:02d}:{end % 60:02d}")
        current = end + (int(settings.get("katta_tanaffus_daqiqa", 15))
                         if settings.get("katta_tanaffus_darsdan_keyin") == order else pause)
    return result


def calendar_day(day, calendar):
    quarter = next((q["quarter"] for q in calendar["quarters"] if q["start"] <= day <= q["end"]), None)
    special = calendar.get("special", {}).get(day)
    if special:
        return special["turi"] in {"oqish", "qoshimcha_oqish"}, special.get("nomi") or special["turi"], quarter
    if calendar.get("holidays") and any(a <= day <= b for a, b in calendar["holidays"]):
        return False, "Ta'til / dam olish", quarter
    if calendar["quarters"] and quarter is None:
        return False, "Chorakdan tashqari", None
    return day.isoweekday() <= calendar["study_days"], "", quarter


def make_week(curriculum, week, calendar, times, seed=0):
    arrangement = distribute(curriculum, calendar["study_days"], len(times), seed)
    days = []
    for index, subjects in enumerate(arrangement):
        current = monday(week) + timedelta(days=index)
        active, reason, quarter = calendar_day(current, calendar)
        days.append({"day": DAYS[index], "date": current.isoformat(), "is_study_day": active,
                     "reason": reason, "quarter": quarter,
                     "lessons": [{"id": f"{current.isoformat()}-{order + 1}", "order": order + 1,
                                  "time": times[order], "subject": subject, "topic": "", "topic_code": "",
                                  "quarter": quarter, "activity_type": "lesson", "topic_source": "unassigned",
                                  "locked_position": index == 0 and order == 0 and fixed_subject(subject)}
                                 for order, subject in enumerate(subjects)]})
    return days


def assign_topics(schedule, raw_curriculum, calendar, catalog, times, seed=0):
    """Position DTS topics on real term slots. Extra slots become explicit review.

    A suggested control/review slot is a personal plan, never an official exam.
    Unknown calendar or missing DTS stays visibly unassigned.
    """
    if not calendar["quarters"]:
        return []
    warnings = []
    wanted_dates = {d["date"] for d in schedule}
    lookup = {(day["date"], l["order"]): l for day in schedule for l in day["lessons"]}
    for quarter in calendar["quarters"]:
        if not any(quarter["start"].isoformat() <= day <= quarter["end"].isoformat() for day in wanted_dates):
            continue
        by_subject = defaultdict(list)
        cursor = monday(quarter["start"])
        while cursor <= quarter["end"]:
            weekly = curriculum_rows(raw_curriculum, cursor)
            generated = make_week(weekly, cursor, calendar, times, seed)
            for day in generated:
                if day["is_study_day"] and day["quarter"] == quarter["quarter"]:
                    for lesson in day["lessons"]:
                        by_subject[subject_key(lesson["subject"])].append((day["date"], lesson["order"]))
            cursor += timedelta(days=7)
        for key, slots in by_subject.items():
            topics = [t for t in catalog.get(key, []) if t["chorak"] == quarter["quarter"]]
            if not topics:
                name = next((r["fan_nomi"] for r in raw_curriculum if subject_key(r["fan_nomi"]) == key), key)
                warnings.append(f"{name}: {quarter['quarter']}-chorak DTS mavzulari topilmadi; mavzu taxmin qilib yozilmadi.")
                continue
            if len(topics) > len(slots):
                warnings.append(f"{topics[0].get('subject', key)}: DTS mavzulari chorakdagi darslardan ko'p; qolganlari mavzu tanlash ro'yxatida saqlanadi.")
            for index, slot in enumerate(slots):
                if slot not in lookup:
                    continue
                lesson = lookup[slot]
                # Course topics occupy earliest slots in database order; extra time
                # is a spaced repeat of the same real topics, ending with a control.
                topic = topics[index] if index < len(topics) else topics[(index - len(topics)) % len(topics)]
                activity = "lesson" if index < len(topics) else ("control" if index == len(slots) - 1 else "review")
                lesson.update(topic=topic["nomi"], topic_code=topic["topic_code"],
                              topic_codes=topic.get("topic_codes") or [topic["topic_code"]],
                              quarter=quarter["quarter"], activity_type=activity,
                              topic_source="dts" if activity == "lesson" else "personal_suggestion")
    return list(dict.fromkeys(warnings))


def validate_schedule(schedule, expected, curriculum, allowed_topics, times):
    if not isinstance(schedule, list) or len(schedule) != len(expected):
        fail("Jadvaldagi kunlar soni o'quv haftasiga mos emas")
    expected_counts = Counter(l["subject"] for d in expected for l in d["lessons"])
    current_counts = Counter()
    specs = {r["subject"]: r for r in curriculum}
    cleaned = []
    for index, (raw, reference) in enumerate(zip(schedule, expected)):
        if not isinstance(raw, dict) or raw.get("day") != reference["day"] or raw.get("date", reference["date"]) != reference["date"]:
            fail("Kunlar yoki sanalar tartibi noto'g'ri")
        lessons = raw.get("lessons")
        if not isinstance(lessons, list) or len(lessons) > len(times):
            fail("Kunlik darslar smena vaqtlariga sig'maydi")
        daily = Counter()
        items = []
        for order, item in enumerate(lessons):
            if not isinstance(item, dict):
                fail("Dars ma'lumoti noto'g'ri")
            name = str(item.get("subject") or "").strip()
            if name not in specs:
                fail("Fan adminning shu sinf o'quv rejasida yo'q")
            spec = specs[name]
            daily[name] += 1
            current_counts[name] += 1
            if daily[name] > spec["kunlik_max"] or spec["metod_kuni"] == index + 1:
                fail(f"{name}: metod kuni yoki kunlik maksimum buzildi")
            code = str(item.get("topic_code") or "").strip()
            activity = item.get("activity_type") or "lesson"
            if activity not in ACTIVITIES:
                fail("Mashg'ulot turi noto'g'ri")
            topic = allowed_topics.get((subject_key(name), code)) if code else None
            if code and topic is None:
                fail("Tanlangan DTS mavzusi bu sinf yoki fanga tegishli emas")
            if topic and reference.get("quarter") and topic["chorak"] not in (None, reference["quarter"]):
                fail("Tanlangan mavzu bu sana choragiga tegishli emas; o'z choragingizdagi mavzuni tanlang")
            if not code and str(item.get("topic") or "").strip():
                fail("Mavzuni DTS ro'yxatidan tanlang; tekshirilmagan nom saqlanmaydi")
            items.append({"id": f"{reference['date']}-{order + 1}", "order": order + 1,
                          "time": times[order], "subject": name,
                          "topic": topic["nomi"] if topic else "", "topic_code": code,
                          "topic_codes": (topic.get("topic_codes") or [code]) if topic else [],
                          "quarter": reference.get("quarter"), "activity_type": activity,
                          "locked_position": index == 0 and order == 0 and fixed_subject(name),
                          "topic_source": "personal" if topic else "unassigned"})
        cleaned.append({**reference, "lessons": items})
    if current_counts != expected_counts:
        fail("Har bir fanning shu haftadagi soati saqlanishi kerak; fanlarni kunlar orasida almashtiring")
    fixed = next((r["subject"] for r in curriculum if fixed_subject(r["subject"]) and r["week_hours"]), None)
    if fixed and (not cleaned[0]["lessons"] or cleaned[0]["lessons"][0]["subject"] != fixed):
        fail("Kelajak soati dushanba kuni 1-dars bo'lib qolishi kerak")
    return cleaned


def _exists(cur, table):
    cur.execute("SELECT to_regclass(%s) AS name", ("public." + table,))
    return bool((cur.fetchone() or {}).get("name"))


def resolve_owner(cur, actor_id, child_id=None, requested_grade=None, language=None, mode=None,
                  school_id=None, staff_check=None):
    owner_id = int(child_id or actor_id)
    if owner_id != int(actor_id):
        if not _exists(cur, "parent_child"):
            fail("Bu o'quvchining shaxsiy jadvaliga ruxsat yo'q", 403)
        cur.execute("SELECT 1 AS allowed FROM parent_child WHERE parent_id=%s AND child_id=%s LIMIT 1", (actor_id, owner_id))
        if not cur.fetchone():
            fail("Bu o'quvchining shaxsiy jadvaliga ruxsat yo'q", 403)
    cur.execute("""SELECT user_id,class,class_letter,maktab_id,role,
                   to_jsonb(u)->>'lavozim' AS lavozim,
                   to_jsonb(u)->>'asosiy_til' AS language
                   FROM users u WHERE user_id=%s""", (owner_id,))
    user = cur.fetchone()
    if not user:
        fail("Foydalanuvchi topilmadi", 404)
    user = dict(user)
    teacher = user.get("role") in {"oqituvchi", "teacher", "admin", "super_admin"}
    if mode == "teacher" and (not teacher or owner_id != int(actor_id)):
        fail("O'qituvchi rejasi faqat o'z hisobingizda ochiladi", 403)
    is_teacher = teacher and (mode == "teacher" or requested_grade is not None) and owner_id == int(actor_id)
    actual_grade = grade_number(user.get("class"))
    class_language = None
    class_shift = None
    if not is_teacher and _exists(cur, "maktab_sinf_azolari") and _exists(cur, "maktab_sinflari"):
        cur.execute("""SELECT s.sinf,s.maktab_id,to_jsonb(s)->>'talim_tili' AS language,
                       to_jsonb(s)->>'smena' AS shift FROM maktab_sinf_azolari a
                       JOIN maktab_sinflari s ON s.id=a.sinf_id
                       WHERE a.user_id=%s AND (s.maktab_id=%s OR %s IS NULL)
                       ORDER BY a.id DESC LIMIT 1""", (owner_id, user.get("maktab_id"), user.get("maktab_id")))
        school_class = cur.fetchone()
        if school_class:
            actual_grade = grade_number(school_class["sinf"]) or actual_grade
            class_language = school_class.get("language")
            class_shift = school_class.get("shift")
            user["maktab_id"] = school_class["maktab_id"]
    if school_id is not None:
        if school_id <= 0:
            fail("Maktab identifikatori noto'g'ri")
        if is_teacher:
            if not staff_check or not staff_check(cur, actor_id, school_id):
                fail("Bu maktab uchun shaxsiy o'qituvchi rejasiga ruxsat yo'q", 403)
            user["maktab_id"] = school_id
        elif int(user.get("maktab_id") or 0) != school_id:
            fail("O'quvchi jadvali o'z maktabiga tegishli bo'lishi kerak", 403)
    if is_teacher:
        actual_grade = requested_grade or actual_grade
    elif requested_grade is not None and requested_grade != actual_grade:
        fail("O'quvchi jadvali profilidagi sinfga mos bo'lishi kerak", 403)
    if actual_grade not in range(1, 12):
        fail("Profilingizda 1–11 oralig'idagi sinfni tanlang; jadval uchun sinf taxmin qilinmaydi")
    selected_language = class_language or user.get("language") or "uz"
    aliases = {"uzbek": "uz", "o'zbek": "uz", "russian": "ru", "english": "en"}
    selected_language = aliases.get(str(selected_language).casefold(), str(selected_language).casefold())
    if language:
        if language not in LANGUAGES:
            fail("Ta'lim tili uz, ru yoki en bo'lishi kerak")
        if class_language and language != class_language and not is_teacher:
            fail("Ta'lim tili maktab sinfi tiliga mos bo'lishi kerak", 403)
        selected_language = language
    if selected_language not in LANGUAGES:
        fail("Profilingizdagi ta'lim tilini tekshiring")
    return {"owner_id": owner_id, "actor_id": int(actor_id), "grade": actual_grade,
            "language": selected_language, "is_teacher": is_teacher,
            "school_id": user.get("maktab_id"), "shift": int(class_shift) if class_shift in (1, 2, "1", "2") else 1}


def load_curriculum(cur, context):
    if not _exists(cur, "admin_maktab_andoza_fanlari_v20_1"):
        fail("Admin maktab o'quv rejasi hali kiritilmagan")
    cur.execute("""SELECT f.fan_nomi,f.haftalik_soat,f.metod_kuni,f.kunlik_max,f.tartib
                   FROM admin_maktab_andoza_fanlari_v20_1 f
                   JOIN admin_maktab_andoza_versiyalari_v20_1 v ON v.id=f.versiya_id
                   WHERE v.faol=TRUE AND f.faol=TRUE AND f.talim_tili=%s
                     AND f.sinf_darajasi=%s AND f.haftalik_soat>0
                   ORDER BY f.tartib,f.id""", (context["language"], context["grade"]))
    return [dict(row) for row in cur.fetchall()]


def load_calendar(cur, context, week, personal_days=5):
    result = {"source": "missing", "name": "Admin kalendari kiritilmagan",
              "study_days": personal_days, "quarters": [], "special": {}, "holidays": [], "warnings": []}
    school_id = context.get("school_id")
    if school_id and _exists(cur, "aqlli_oquv_yillari_v2"):
        cur.execute("""SELECT id,nomi,hafta_kunlari FROM aqlli_oquv_yillari_v2
                       WHERE maktab_id=%s AND faol=TRUE AND boshlanish<=%s AND tugash>=%s
                       ORDER BY boshlanish DESC LIMIT 1""", (school_id, week + timedelta(days=5), week))
        year = cur.fetchone()
        if year and _exists(cur, "aqlli_choraklar_v2"):
            cur.execute("SELECT chorak,boshlanish,tugash,holat FROM aqlli_choraklar_v2 WHERE oquv_yili_id=%s ORDER BY chorak", (year["id"],))
            quarters = [dict(row) for row in cur.fetchall()]
            # Draft dates are displayed as provisional, never claimed approved.
            result.update(source="school", name=year["nomi"], study_days=int(year["hafta_kunlari"]),
                          quarters=[{"quarter": int(q["chorak"]), "start": as_date(q["boshlanish"]),
                                     "end": as_date(q["tugash"]), "status": q["holat"]} for q in quarters])
            if any(q["holat"] != "tasdiqlangan" for q in quarters):
                result["warnings"].append("Admin kalendaridagi ayrim chorak sanalari hali taxminiy deb belgilangan.")
        if year and _exists(cur, "aqlli_kalendar_kunlari_v2"):
            cur.execute("SELECT sana,turi,nomi FROM aqlli_kalendar_kunlari_v2 WHERE maktab_id=%s", (school_id,))
            result["special"] = {as_date(row["sana"]): dict(row) for row in cur.fetchall()}
    if not result["quarters"] and _exists(cur, "learning_path_calendars"):
        context_id = None
        if school_id and _exists(cur, "learning_contexts"):
            cur.execute("""SELECT id FROM learning_contexts WHERE active=TRUE
                           AND external_type='maktab' AND external_id=%s ORDER BY id LIMIT 1""", (school_id,))
            context_row = cur.fetchone()
            context_id = context_row["id"] if context_row else None
        academic_start = week.year if week.month >= 9 else week.year - 1
        academic_year = f"{academic_start}-{academic_start + 1}"
        cur.execute("""SELECT name,calendar_level,terms,holidays FROM learning_path_calendars
                       WHERE active=TRUE AND academic_year=%s AND (grade=%s OR grade IS NULL)
                       AND (context_id=%s OR context_id IS NULL)
                       ORDER BY (context_id IS NOT NULL) DESC,(grade IS NOT NULL) DESC,updated_at DESC LIMIT 1""",
                    (academic_year, str(context["grade"]), context_id))
        row = cur.fetchone()
        if row:
            quarters = []
            for item in row["terms"] or []:
                start, end = as_date(item["start"]), as_date(item["end"])
                term = quarter_number(item["term"])
                if start > end or term not in range(1, 5):
                    fail("Admin kalendaridagi chorak sanasi noto'g'ri")
                quarters.append({"quarter": term, "start": start, "end": end, "status": "admin"})
            for holiday in row["holidays"] or []:
                if isinstance(holiday, dict):
                    first = as_date(holiday.get("start") or holiday.get("date"))
                    last = as_date(holiday.get("end") or holiday.get("date") or first)
                else:
                    first = last = as_date(holiday)
                if last < first:
                    fail("Admin kalendaridagi ta'til sanalari noto'g'ri")
                result["holidays"].append((first, last))
            result.update(source=row["calendar_level"], name=row["name"], quarters=quarters)
    if not result["quarters"]:
        result["warnings"].append("Admin chorak kalendari topilmadi. Fan-soatlar bo'yicha haftalik andoza tayyor; sanali DTS mavzularini avtomatik joylash uchun kalendar kerak.")
    if result["source"] != "school":
        result["warnings"].append(f"Haftadagi {result['study_days']} o'quv kuni shaxsiy sozlama; maktab kalendari kiritilganda undagi kunlar olinadi.")
    if any((q["end"] - q["start"]).days > 160 for q in result["quarters"]):
        fail("Admin kalendaridagi chorak 160 kundan oshib ketgan; sanalarni tekshiring")
    return result


def load_times(cur, context, shift):
    settings = None
    if context.get("school_id") and _exists(cur, "aqlli_smena_sozlamalari_v2"):
        cur.execute("SELECT * FROM aqlli_smena_sozlamalari_v2 WHERE maktab_id=%s AND smena=%s", (context["school_id"], shift))
        settings = cur.fetchone()
    return lesson_times(shift, dict(settings) if settings else None), "school" if settings else "personal_default"


def topic_identity(value, canonical=None):
    content_language = {"русскийязык": "rustili", "englishlanguage": "ingliztili", "узбекскийязык": "onatili"}
    if subject_key(value) in content_language:
        return content_language[subject_key(value)]
    key = subject_key(canonical(value) if canonical else value)
    equivalents = {
        "tabiiyfanscience": "tabiiyfan", "science": "tabiiyfan",
        "informatikavaaxborottexnologiyalari": "informatika",
    }
    return equivalents.get(key, key)


def load_topics(cur, grade, subjects, mappings=None, canonical=None, options_out=None, aliases=None, diagnostics=None):
    catalog = {subject_key(s): [] for s in subjects}
    if not _exists(cur, "dts_tree"):
        return catalog
    cur.execute("""SELECT topic_code,quarter,subject_name,bob_name,
                   COALESCE(NULLIF(mavzu_name,''),NULLIF(kichik_name,''),NULLIF(bolim_name,''),bob_name) AS nomi
                   FROM dts_tree WHERE is_deleted=FALSE AND grade::text=%s
                   ORDER BY quarter,topic_code LIMIT 6000""", (str(grade),))
    rows = [dict(row) for row in cur.fetchall()]
    names = sorted({row["subject_name"] for row in rows if row["subject_name"]})
    mappings = mappings or {}
    if not isinstance(mappings, dict) or len(mappings) > 40:
        fail("DTS fan moslamalari noto'g'ri")
    invalid_keys = [key for key, value in mappings.items() if key not in subjects or not isinstance(value, str) or len(value) > 200]
    if invalid_keys:
        if diagnostics is None:
            fail("DTS moslamalari faqat shu sinf o'quv rejasidagi fanlar uchun saqlanadi")
        for key in invalid_keys:
            mappings.pop(key, None)
        diagnostics.append("Admin fanlar ro'yxati o'zgargan; DTS fan moslamalarini tekshiring. Saqlangan jadval o'chirilmadi.")
    match_keys = {}
    for subject in subjects:
        identity = topic_identity(subject, canonical)
        permitted_keys = {identity}
        if aliases and subject_key(subject) not in {"русскийязык", "englishlanguage", "узбекскийязык"}:
            permitted_keys |= {topic_identity(key, canonical) for key in aliases(subject)}
        # A generic foreign-language course needs an explicit personal choice.
        choices = [name for name in names if topic_identity(name, canonical) in
                   {"ingliztili", "nemistili", "fransuztili", "ispantili", "xitoytili", "arabtili", "rustili"}]
        choices = choices if identity == "chettili" else []
        if options_out is not None and choices:
            options_out[subject] = choices
        selected = mappings.get(subject)
        if selected and selected not in choices:
            if diagnostics is None:
                fail(f"{subject}: DTS fani taklif qilingan sinf fanlaridan tanlanishi kerak")
            diagnostics.append(f"{subject}: oldingi DTS fani bazada topilmadi; fan moslamasini qayta tanlang.")
            mappings.pop(subject, None)
            selected = None
        match_keys[subject] = ({topic_identity(selected, canonical)} if selected else
                               {identity} if identity == "chettili" else permitted_keys)
    for row in rows:
        if not row["nomi"]:
            continue
        quarter = quarter_number(row.get("quarter"))
        identity = topic_identity(row["subject_name"], canonical)
        for subject, keys in match_keys.items():
            if identity in keys:
                catalog[subject_key(subject)].append({"topic_code": str(row["topic_code"]), "nomi": row["nomi"],
                    "chorak": quarter, "bob_nomi": row["bob_name"], "subject": row["subject_name"]})
    for key, topics in catalog.items():
        grouped = {}
        for topic in topics:
            group_key = (topic["subject"], topic["chorak"], topic["bob_nomi"], topic["nomi"])
            if group_key not in grouped:
                grouped[group_key] = {**topic, "topic_codes": []}
            if topic["topic_code"] not in grouped[group_key]["topic_codes"]:
                grouped[group_key]["topic_codes"].append(topic["topic_code"])
        catalog[key] = list(grouped.values())
    return catalog


class PersonalScheduleBody(BaseModel):
    week_start: str
    grade: Optional[int] = None
    language: Optional[str] = None
    bola_id: Optional[int] = None
    mode: Optional[str] = None
    shift: int = 1
    study_days: int = 5
    schedule: list
    extracurriculars: list = Field(default_factory=list)
    version: int = 0
    curriculum_signature: Optional[str] = None
    subject_mappings: dict = Field(default_factory=dict)
    school_id: Optional[int] = None


def register_personal_schedule(app, platform, school=None):
    router = APIRouter(tags=["Shaxsiy jadval"])
    schema_ready = False
    canonical = getattr(school, "_v242_canonical_subject_name", None)
    staff_check = getattr(school, "_v1852_staff", None)
    aliases = getattr(school, "_v2266_dts_subject_keys", None)

    def ensure_schema(cur):
        nonlocal schema_ready
        if schema_ready:
            return
        cur.execute("SELECT pg_advisory_xact_lock(hashtext('kabutar_personal_schedule_v42'))")
        cur.execute("""CREATE TABLE IF NOT EXISTS kabutar_personal_schedule_v42(
            owner_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            school_scope BIGINT NOT NULL DEFAULT 0,
            grade SMALLINT NOT NULL CHECK(grade BETWEEN 1 AND 11),
            language TEXT NOT NULL CHECK(language IN ('uz','ru','en')),
            week_start DATE NOT NULL,shift SMALLINT NOT NULL CHECK(shift IN (1,2)),
            study_days SMALLINT NOT NULL CHECK(study_days IN (5,6)),
            schedule JSONB NOT NULL,extracurriculars JSONB NOT NULL DEFAULT '[]'::jsonb,
            subject_mappings JSONB NOT NULL DEFAULT '{}'::jsonb,
            version INTEGER NOT NULL DEFAULT 1,curriculum_signature TEXT NOT NULL,
            updated_by BIGINT NOT NULL,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(owner_user_id,school_scope,grade,language,week_start)
        )""")

    def fetch_context(cur, actor_id, week, bola_id, grade, language, mode, study_days, shift, school_id=None):
        if study_days not in (5, 6) or shift not in (None, 1, 2):
            fail("Smena 1/2 va o'quv haftasi 5/6 kun bo'lishi kerak")
        context = resolve_owner(cur, actor_id, bola_id, grade, language, mode, school_id, staff_check)
        raw = load_curriculum(cur, context)
        curriculum = curriculum_rows(raw, week)
        calendar = load_calendar(cur, context, week, study_days)
        shift = shift or context["shift"]
        times, time_source = load_times(cur, context, shift)
        signature = hashlib.sha256(json.dumps(raw, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()
        return context, raw, curriculum, calendar, shift, times, time_source, signature

    @router.get("/api/shaxsiy-jadval")
    def get_schedule(token: str, week: Optional[str] = None, bola_id: Optional[int] = None,
                     grade: Optional[int] = None, language: Optional[str] = None,
                     mode: Optional[str] = None, study_days: int = 5,
                     shift: Optional[int] = None, regenerate: bool = False,
                     subject_mappings: Optional[str] = None, school_id: Optional[int] = None):
        nonlocal schema_ready
        actor_id = platform._jwt_tekshir(token)
        start = monday(week)
        conn = platform._db()
        cur = conn.cursor()
        try:
            ensure_schema(cur)
            context, raw, curriculum, calendar, selected_shift, times, time_source, signature = fetch_context(
                cur, actor_id, start, bola_id, grade, language, mode, study_days, shift, school_id)
            key = (context["owner_id"], int(context.get("school_id") or 0), context["grade"], context["language"], start)
            cur.execute("SELECT * FROM kabutar_personal_schedule_v42 WHERE owner_user_id=%s AND school_scope=%s AND grade=%s AND language=%s AND week_start=%s", key)
            saved = cur.fetchone()
            if saved and not regenerate and calendar["source"] != "school":
                calendar = load_calendar(cur, context, start, int(saved["study_days"]))
            mappings = dict((saved or {}).get("subject_mappings") or {})
            if subject_mappings:
                if len(subject_mappings) > 8000:
                    fail("DTS moslamalari hajmi juda katta")
                try:
                    mappings = json.loads(subject_mappings)
                except (ValueError, TypeError):
                    fail("DTS moslamalari JSON shaklida bo'lishi kerak")
            subject_options = {}
            mapping_warnings = []
            catalog = load_topics(cur, context["grade"], [r["subject"] for r in curriculum], mappings, canonical,
                                 subject_options, aliases, diagnostics=mapping_warnings if not subject_mappings else None)
            legacy = None
            if _exists(cur, "oquvchi_shaxsiy_jadval_v1"):
                cur.execute("""SELECT shift,schedule,to_jsonb(t)->'extracurriculars' AS extracurriculars
                               FROM oquvchi_shaxsiy_jadval_v1 t WHERE bola_user_id=%s""", (context["owner_id"],))
                legacy = cur.fetchone()
            warnings = list(calendar["warnings"]) + mapping_warnings
            source = "central_curriculum"
            if saved and not regenerate:
                selected_shift = int(saved["shift"])
                times, time_source = load_times(cur, context, selected_shift)
                schedule = deepcopy(saved["schedule"])
                source = "saved"
                if saved["curriculum_signature"] != signature:
                    warnings.append("Admin o'quv rejasi o'zgargan. Saqlangan shaxsiy jadval saqlandi; yangi fan-soatlarga moslash uchun 'Qayta tuzish'ni bosing.")
                if len(schedule) != calendar["study_days"]:
                    warnings.append("Kalendar o'quv kunlari saqlangan jadvaldan farq qiladi. Shaxsiy nusxa saqlandi; 'Qayta tuzish' yangi kunlarga moslaydi.")
                # Recalculate date/holiday status on reads without overwriting personal topics.
                for index, day in enumerate(schedule):
                    current = start + timedelta(days=index)
                    active, reason, quarter = calendar_day(current, calendar)
                    day.update(date=current.isoformat(), is_study_day=active, reason=reason, quarter=quarter)
                    for lesson in day.get("lessons", []):
                        if lesson.get("topic_code") and lesson.get("quarter") != quarter:
                            warnings.append("Admin kalendari o'zgargan: saqlangan mavzuning choragi bilan sana choragini tekshiring yoki qayta tuzing.")
                        lesson["quarter"] = quarter
            else:
                schedule = make_week(curriculum, start, calendar, times)
                warnings.extend(assign_topics(schedule, raw, calendar, catalog, times))
            if saved:
                extracurriculars = saved.get("extracurriculars") or []
            else:
                cur.execute("""SELECT extracurriculars FROM kabutar_personal_schedule_v42
                               WHERE owner_user_id=%s AND school_scope=%s AND grade=%s AND language=%s
                               ORDER BY updated_at DESC LIMIT 1""", key[:4])
                recent_preferences = cur.fetchone()
                extracurriculars = (recent_preferences or legacy or {}).get("extracurriculars") or []
            if legacy and not saved:
                warnings.append("Oldingi shaxsiy jadvalingiz zaxirada saqlangan. Bu haftalik reja yangi o'quv rejasidan tuzildi; saqlash eski nusxani o'chirmaydi.")
            if time_source != "school":
                warnings.append("Dars vaqtlari shaxsiy boshlang'ich andoza (45 daqiqa, 5 daqiqa tanaffus). Maktab smena vaqtlari kiritilganda ular olinadi.")
            payload = {"bola_id": context["owner_id"], "grade": context["grade"], "language": context["language"],
                       "is_teacher": context["is_teacher"], "can_edit": int(actor_id) == context["owner_id"],
                       "available_grades": list(range(1, 12)) if context["is_teacher"] else [context["grade"]],
                       "week_start": start.isoformat(), "week_end": (start + timedelta(days=6)).isoformat(),
                       "shift": selected_shift, "study_days": len(schedule), "schedule": schedule,
                       "extracurriculars": extracurriculars, "curriculum": curriculum,
                       "weekly_hours": sum(len(d["lessons"]) for d in schedule),
                       "scheduled_hours": sum(len(d["lessons"]) for d in schedule if d.get("is_study_day")),
                       "expected_weekly_hours": sum(r["week_hours"] for r in curriculum),
                       "nominal_weekly_hours": sum(r["weekly_hours"] for r in curriculum),
                       "day_loads": [len(d["lessons"]) for d in schedule], "lesson_times": times,
                       "source": source, "calendar": {"source": calendar["source"], "name": calendar["name"],
                            "quarters": [{**q, "start": q["start"].isoformat(), "end": q["end"].isoformat()} for q in calendar["quarters"]]},
                       "warnings": list(dict.fromkeys(warnings)), "version": int(saved["version"]) if saved else 0,
                       "curriculum_signature": signature, "legacy_available": bool(legacy), "personal_only": True}
            payload.update(subject_mappings=mappings, subject_options=subject_options, school_id=context.get("school_id"))
            conn.commit()
            schema_ready = True
            return payload
        finally:
            cur.close()
            conn.close()

    @router.get("/api/shaxsiy-jadval/mavzular")
    def get_topics(token: str, fan: str, grade: Optional[int] = None,
                   language: Optional[str] = None, bola_id: Optional[int] = None,
                   quarter: Optional[int] = None, mode: Optional[str] = None,
                   dts_subject: Optional[str] = None, school_id: Optional[int] = None):
        actor_id = platform._jwt_tekshir(token)
        conn = platform._db()
        cur = conn.cursor()
        try:
            context = resolve_owner(cur, actor_id, bola_id, grade, language, mode, school_id, staff_check)
            raw = load_curriculum(cur, context)
            if fan not in {row["fan_nomi"] for row in raw}:
                fail("Bu fan sinf o'quv rejasida yo'q")
            if quarter is not None and quarter not in range(1, 5):
                fail("Chorak 1–4 oralig'ida bo'lishi kerak")
            topics = load_topics(cur, context["grade"], [fan], {fan: dts_subject} if dts_subject else None, canonical, aliases=aliases)[subject_key(fan)]
            if quarter:
                topics = [topic for topic in topics if topic["chorak"] == quarter]
            return {"grade": context["grade"], "fan": fan, "mavzular": topics}
        finally:
            cur.close()
            conn.close()

    @router.put("/api/shaxsiy-jadval")
    def save_schedule(payload: PersonalScheduleBody, token: str):
        nonlocal schema_ready
        actor_id = platform._jwt_tekshir(token)
        if payload.bola_id is not None and int(payload.bola_id) != int(actor_id):
            fail("Ota-ona farzandining jadvalini ko'rishi mumkin; shaxsiy jadvalni egasi o'zgartiradi", 403)
        start = monday(payload.week_start)
        if start.isoformat() != payload.week_start:
            fail("Saqlanadigan hafta sanasi dushanba bo'lishi kerak")
        conn = platform._db()
        cur = conn.cursor()
        try:
            ensure_schema(cur)
            context, raw, curriculum, calendar, shift, times, _, signature = fetch_context(
                cur, actor_id, start, payload.bola_id, payload.grade, payload.language,
                payload.mode, payload.study_days, payload.shift, payload.school_id)
            if payload.curriculum_signature and payload.curriculum_signature != signature:
                fail("Admin o'quv rejasi yangilandi. Jadvalni qayta ochib moslang.", 409)
            expected = make_week(curriculum, start, calendar, times)
            catalog = load_topics(cur, context["grade"], [row["subject"] for row in curriculum], payload.subject_mappings, canonical, aliases=aliases)
            allowed = {(key, topic["topic_code"]): topic for key, rows in catalog.items() for topic in rows}
            schedule = validate_schedule(payload.schedule, expected, curriculum, allowed, times)
            extracurriculars = platform._qoshimcha_mashgulotlarni_tekshir(payload.extracurriculars)
            key = (context["owner_id"], int(context.get("school_id") or 0), context["grade"], context["language"], start)
            if payload.version == 0:
                cur.execute("""INSERT INTO kabutar_personal_schedule_v42(
                    owner_user_id,school_scope,grade,language,week_start,shift,study_days,schedule,extracurriculars,
                    curriculum_signature,updated_by,subject_mappings) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(owner_user_id,school_scope,grade,language,week_start) DO NOTHING RETURNING version""",
                            (*key, shift, calendar["study_days"], Json(schedule), Json(extracurriculars), signature, actor_id, Json(payload.subject_mappings)))
            else:
                cur.execute("""UPDATE kabutar_personal_schedule_v42 SET shift=%s,study_days=%s,
                    schedule=%s,extracurriculars=%s,curriculum_signature=%s,updated_by=%s,
                    updated_at=NOW(),version=version+1,subject_mappings=%s WHERE owner_user_id=%s AND school_scope=%s AND grade=%s
                    AND language=%s AND week_start=%s AND version=%s RETURNING version""",
                            (shift, calendar["study_days"], Json(schedule), Json(extracurriculars), signature, actor_id, Json(payload.subject_mappings), *key, payload.version))
            updated = cur.fetchone()
            if not updated:
                conn.rollback()
                fail("Jadval boshqa oynada yangilangan. Sahifani qayta oching; o'zgarishlar ustidan yozilmadi.", 409)
            conn.commit()
            schema_ready = True
            return {"ok": True, "version": int(updated["version"]), "week_start": start.isoformat(),
                    "schedule": schedule, "shift": shift, "extracurriculars": extracurriculars,
                    "curriculum_signature": signature, "subject_mappings": payload.subject_mappings, "personal_only": True}
        finally:
            cur.close()
            conn.close()

    app.include_router(router)
    return router

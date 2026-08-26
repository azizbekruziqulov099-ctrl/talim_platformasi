"""SamTM Institute V20.

Institut -> fakultet -> kafedra -> ta'lim yo'nalishi ierarxiyasi,
lavozimga asoslangan ruxsatlar va HEMISgacha bo'lgan qabul kontingenti.

Muhim tamoyillar:
- import avval preview qilinadi, keyin bitta tranzaksiyada commit bo'ladi;
- talabaning maxfiy ma'lumoti faqat vakolatli rolga beriladi;
- xodim/talaba uchun doim bir martalik, 7 kunlik kirish kodi beriladi;
- qabulda dublikat universitet + JSHSHIR bo'yicha bloklanadi/upsert qilinadi.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import re
import secrets
import string
import unicodedata
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, File, Header, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field


SAMTM_INSTITUTE_RELEASE = "institute-foundation-v20-rev54"
router = APIRouter(prefix="/api/institut/v20", tags=["Institut V20"])
PLATFORM = None
_SCHEMA_READY = False

TA_LIM_SHAKLLARI = ["Kunduzgi", "Kechki", "Sirtqi", "Masofaviy", "Dual ta'lim"]
TA_LIM_TILLARI = ["O‘zbekcha", "Ruscha", "Tojikcha", "Qoraqalpoqcha", "Inglizcha"]
DARAJALAR = ["Bakalavriat", "Magistratura", "Doktorantura"]

ROLE_LABELS = {
    "owner": "Institut egasi",
    "rektor": "Rektor",
    "prorektor": "Prorektor",
    "institut_admin": "Institut administratori",
    "dekan": "Dekan",
    "zam_dekan": "Dekan o‘rinbosari",
    "manaviyatchi": "Ma’naviy-ma’rifiy ishlar mas’uli",
    "fakultet_admin": "Fakultet administratori",
    "kafedra_mudiri": "Kafedra mudiri",
    "professor_oqituvchi": "Professor-o‘qituvchi",
    "tyutor": "Tyutor",
    "talaba": "Talaba",
}

INSTITUTE_WIDE = {"owner", "rektor", "prorektor", "institut_admin"}
FACULTY_WIDE = {"dekan", "zam_dekan", "manaviyatchi", "fakultet_admin"}
DEPARTMENT_WIDE = {"kafedra_mudiri"}
PRIVATE_ROLES = INSTITUTE_WIDE | FACULTY_WIDE | DEPARTMENT_WIDE | {"tyutor"}
MANAGE_STRUCTURE_ROLES = INSTITUTE_WIDE
MANAGE_STAFF_ROLES = INSTITUTE_WIDE | {"dekan", "fakultet_admin"}
MARK_DOCUMENT_ROLES = INSTITUTE_WIDE | FACULTY_WIDE | DEPARTMENT_WIDE


def register_institute(app, platform):
    global PLATFORM
    PLATFORM = platform
    app.include_router(router)

    @app.on_event("startup")
    def migrate_institute_v20():
        global _SCHEMA_READY
        conn = platform._db(); cur = conn.cursor()
        try:
            cur.execute("SELECT pg_advisory_lock(%s)", (20005400,))
            _institut_v20_jadvallari(cur)
            conn.commit(); _SCHEMA_READY = True
        finally:
            try:
                cur.execute("SELECT pg_advisory_unlock(%s)", (20005400,)); conn.commit()
            except Exception:
                conn.rollback()
            cur.close(); conn.close()


def _p():
    if PLATFORM is None:
        raise RuntimeError("samtm_institute.register_institute chaqirilmagan")
    return PLATFORM


def _token(token: Optional[str], authorization: Optional[str]) -> str:
    return _p()._jwt_header_yoki_query(token, authorization)


def _uid(token: Optional[str], authorization: Optional[str]) -> int:
    return _p()._jwt_tekshir(_token(token, authorization))


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    text = text.replace("ʻ", "'").replace("’", "'").replace("‘", "'").replace("`", "'")
    return re.sub(r"\s+", " ", text).strip()


def _key(value: Any) -> str:
    text = _norm(value).casefold()
    text = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9а-яё]+", "", text)


def _digits(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"\D", "", str(value or ""))


def _text_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return _norm(value)


def _float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _iso_date(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _norm(value)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _telefon(value: Any) -> Optional[str]:
    d = _digits(value)
    if len(d) == 9:
        return "+998" + d
    if len(d) == 12 and d.startswith("998"):
        return "+" + d
    return None


def _mask_phone(value: Optional[str]) -> Optional[str]:
    d = _digits(value)
    if len(d) < 7:
        return None
    return f"+{d[:3]} ** *** {d[-2:]}"


def _mask_pin(value: Optional[str]) -> Optional[str]:
    d = _digits(value)
    if len(d) < 6:
        return None
    return d[:2] + "**********" + d[-2:]


def _canonical_choice(value: Any, choices: list[str]) -> Optional[str]:
    k = _key(value)
    aliases = {
        "kunduzgi": "Kunduzgi", "kechki": "Kechki", "sirtqi": "Sirtqi",
        "masofaviy": "Masofaviy", "dualtalim": "Dual ta'lim", "dual": "Dual ta'lim",
        "ozbekcha": "O‘zbekcha", "uzbekcha": "O‘zbekcha", "uzbek": "O‘zbekcha",
        "ruscha": "Ruscha", "russian": "Ruscha", "tojikcha": "Tojikcha",
        "qoraqalpoqcha": "Qoraqalpoqcha", "inglizcha": "Inglizcha",
        "bakalavriat": "Bakalavriat", "magistratura": "Magistratura", "doktorantura": "Doktorantura",
    }
    result = aliases.get(k)
    return result if result in choices else None


def _header_map(row: list[Any]) -> dict[str, int]:
    return {_key(value): i for i, value in enumerate(row) if _norm(value)}


def _find_header_row(rows: list[list[Any]], required: list[str], sheet_name: str) -> tuple[int, dict[str, int]]:
    """Bezak/sarlavha qatorlari bo'lsa ham haqiqiy ustun qatorini topadi."""
    wanted = {_key(value) for value in required}
    for index, row in enumerate(rows[:25]):
        headers = _header_map(row)
        if wanted.issubset(headers):
            return index, headers
    raise HTTPException(
        status_code=400,
        detail=f"{sheet_name} varag'ida ustunlar topilmadi: " + ", ".join(required),
    )


def _cell(row: list[Any], headers: dict[str, int], *names: str) -> Any:
    for name in names:
        idx = headers.get(_key(name))
        if idx is not None and idx < len(row):
            return row[idx]
    return None


def _workbook_rows(content: bytes, filename: str) -> dict[str, list[list[Any]]]:
    """XLS va XLSX ni formulalarsiz, ixcham 2D qatorlarga o'qiydi."""
    lower = (filename or "").lower()
    if lower.endswith(".xls") and not lower.endswith(".xlsx"):
        try:
            import xlrd
        except ImportError as exc:
            raise HTTPException(status_code=500, detail=".xls o'qish uchun xlrd o'rnatilmagan") from exc
        try:
            book = xlrd.open_workbook(file_contents=content)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"XLS fayl ochilmadi: {exc}") from exc
        result = {}
        for sheet in book.sheets():
            rows = []
            for r in range(sheet.nrows):
                values = []
                for c in range(sheet.ncols):
                    cell = sheet.cell(r, c)
                    value = cell.value
                    if cell.ctype == xlrd.XL_CELL_DATE:
                        try:
                            value = datetime(*xlrd.xldate_as_tuple(value, book.datemode))
                        except Exception:
                            pass
                    values.append(value)
                rows.append(values)
            result[sheet.name] = rows
        return result
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"XLSX fayl ochilmadi: {exc}") from exc
    result = {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}
    wb.close()
    return result


def _active_rows(sheets: dict[str, list[list[Any]]], preferred: tuple[str, ...] = ()) -> list[list[Any]]:
    for wanted in preferred:
        for name, rows in sheets.items():
            if _key(name) == _key(wanted):
                return rows
    return next(iter(sheets.values()), [])


def _named_rows(sheets: dict[str, list[list[Any]]], wanted: str) -> list[list[Any]]:
    for name, rows in sheets.items():
        if _key(name) == _key(wanted):
            return rows
    return []


def _institut_v20_jadvallari(cur):
    """V20 sxemasi. Runtime startupda bir marta bajaradi."""
    if PLATFORM is not None:
        PLATFORM._universitet_jadvali(cur)
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_yonalishlari(
        id BIGSERIAL PRIMARY KEY,
        universitet_id INTEGER NOT NULL REFERENCES universitetlar(id) ON DELETE CASCADE,
        fakultet_id INTEGER NOT NULL REFERENCES fakultetlar(id) ON DELETE CASCADE,
        kafedra_id INTEGER NOT NULL REFERENCES kafedralar(id) ON DELETE CASCADE,
        kodi TEXT, nomi TEXT NOT NULL, daraja TEXT NOT NULL DEFAULT 'Bakalavriat',
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(universitet_id,kafedra_id,nomi,daraja)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_yonalish_variantlari(
        id BIGSERIAL PRIMARY KEY,
        yonalish_id BIGINT NOT NULL REFERENCES universitet_yonalishlari(id) ON DELETE CASCADE,
        talim_shakli TEXT NOT NULL, talim_tili TEXT NOT NULL,
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        UNIQUE(yonalish_id,talim_shakli,talim_tili)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_xodim_rollari(
        id BIGSERIAL PRIMARY KEY,
        universitet_id INTEGER NOT NULL REFERENCES universitetlar(id) ON DELETE CASCADE,
        fakultet_id INTEGER REFERENCES fakultetlar(id) ON DELETE CASCADE,
        kafedra_id INTEGER REFERENCES kafedralar(id) ON DELETE CASCADE,
        yonalish_id BIGINT REFERENCES universitet_yonalishlari(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        rol TEXT NOT NULL,
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        yaratilgan_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(universitet_id,user_id,rol,fakultet_id,kafedra_id,yonalish_id)
    )""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_uni_fakultet_dekan
        ON universitet_xodim_rollari(fakultet_id)
        WHERE faol=TRUE AND rol='dekan'""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_uni_fakultet_manaviy
        ON universitet_xodim_rollari(fakultet_id)
        WHERE faol=TRUE AND rol='manaviyatchi'""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_uni_kafedra_mudir
        ON universitet_xodim_rollari(kafedra_id)
        WHERE faol=TRUE AND rol='kafedra_mudiri'""")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_tyutor_yonalishlari(
        id BIGSERIAL PRIMARY KEY,
        universitet_id INTEGER NOT NULL REFERENCES universitetlar(id) ON DELETE CASCADE,
        tyutor_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        yonalish_id BIGINT NOT NULL REFERENCES universitet_yonalishlari(id) ON DELETE CASCADE,
        talim_shakli TEXT, talim_tili TEXT, faol BOOLEAN NOT NULL DEFAULT TRUE,
        yaratilgan_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(tyutor_user_id,yonalish_id,talim_shakli,talim_tili)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_qabul_talabalari(
        id BIGSERIAL PRIMARY KEY,
        universitet_id INTEGER NOT NULL REFERENCES universitetlar(id) ON DELETE CASCADE,
        yonalish_id BIGINT NOT NULL REFERENCES universitet_yonalishlari(id) ON DELETE RESTRICT,
        guruh_id INTEGER REFERENCES universitet_guruhlari(id) ON DELETE SET NULL,
        user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
        abitur_id TEXT NOT NULL, jshshir TEXT NOT NULL, jshshir_hash CHAR(64) NOT NULL,
        familiya TEXT NOT NULL, ism TEXT NOT NULL, ota_ism TEXT,
        tugilgan_sana DATE, pasport_seriya TEXT, pasport_raqam TEXT,
        tavsiya_turi TEXT, talim_shakli TEXT NOT NULL, talim_tili TEXT NOT NULL,
        telefon TEXT, telegram_username TEXT, max_username TEXT,
        ball NUMERIC(7,2), doimiy_region TEXT, doimiy_tuman TEXT,
        maktab_region TEXT, maktab_tuman TEXT, maktab_turi TEXT, maktab_nomi TEXT,
        tugatgan_yili INTEGER, attestat TEXT, otm_nomi TEXT,
        qabul_bosqichi SMALLINT NOT NULL DEFAULT 1 CHECK(qabul_bosqichi BETWEEN 1 AND 3),
        hujjat_topshirgan_at TIMESTAMPTZ, saytga_kiritilgan_at TIMESTAMPTZ,
        import_batch_id BIGINT, yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(universitet_id,jshshir_hash), UNIQUE(universitet_id,abitur_id)
    )""")
    cur.execute("""CREATE INDEX IF NOT EXISTS ix_uni_qabul_filter
        ON universitet_qabul_talabalari(universitet_id,yonalish_id,qabul_bosqichi,talim_shakli,talim_tili,ball DESC)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_import_batchlar(
        id BIGSERIAL PRIMARY KEY,
        universitet_id INTEGER REFERENCES universitetlar(id) ON DELETE CASCADE,
        import_turi TEXT NOT NULL, fayl_nomi TEXT NOT NULL, fayl_sha256 CHAR(64) NOT NULL,
        payload JSONB NOT NULL, xulosa JSONB NOT NULL,
        yaratilgan_by BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        holat TEXT NOT NULL DEFAULT 'preview',
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), commit_at TIMESTAMPTZ
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_taklif_kodlari(
        id BIGSERIAL PRIMARY KEY,
        universitet_id INTEGER NOT NULL REFERENCES universitetlar(id) ON DELETE CASCADE,
        xodim_rol_id BIGINT REFERENCES universitet_xodim_rollari(id) ON DELETE CASCADE,
        qabul_talaba_id BIGINT REFERENCES universitet_qabul_talabalari(id) ON DELETE CASCADE,
        placeholder_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        kod_hash TEXT NOT NULL UNIQUE, turi TEXT NOT NULL,
        yaratilgan_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), ishlatildi_at TIMESTAMPTZ
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_workspace_map(
        context_id BIGINT PRIMARY KEY,
        universitet_id INTEGER NOT NULL UNIQUE REFERENCES universitetlar(id) ON DELETE CASCADE,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS universitet_audit_log(
        id BIGSERIAL PRIMARY KEY, universitet_id INTEGER NOT NULL,
        actor_user_id BIGINT NOT NULL, amal TEXT NOT NULL,
        obyekt_turi TEXT, obyekt_id BIGINT, tafsilot JSONB,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")


def _ensure_schema(cur):
    if not _SCHEMA_READY:
        _institut_v20_jadvallari(cur)


def _is_global_admin(cur, user_id: int) -> bool:
    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    return cur.fetchone() is not None


def _resolve_university(cur, user_id: int, workspace_id: Optional[int], create: bool = True) -> int:
    """V17 context id ni legacy universitet id ga xavfsiz xaritalaydi."""
    if not workspace_id:
        cur.execute("SELECT universitet_id FROM users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        if row and row["universitet_id"]:
            return int(row["universitet_id"])
        raise HTTPException(status_code=404, detail="Institut ish maydoni topilmadi")
    cur.execute("SELECT universitet_id FROM universitet_workspace_map WHERE context_id=%s", (workspace_id,))
    mapped = cur.fetchone()
    if mapped:
        return int(mapped["universitet_id"])
    if not create:
        raise HTTPException(status_code=404, detail="Institut xaritasi topilmadi")
    cur.execute("""SELECT o.display_name
        FROM organization_trials o JOIN learning_contexts c ON c.id=o.context_id
        WHERE o.context_id=%s AND o.organization_type='institute'
          AND (o.creator_user_id=%s OR EXISTS(
              SELECT 1 FROM context_memberships cm WHERE cm.context_id=o.context_id
              AND cm.user_id=%s AND cm.status='active'))""", (workspace_id, user_id, user_id))
    org = cur.fetchone()
    if not org:
        raise HTTPException(status_code=403, detail="Bu institut ish maydoniga ruxsat yo'q")
    cur.execute("INSERT INTO universitetlar(nomi) VALUES(%s) RETURNING id", (org["display_name"],))
    university_id = int(cur.fetchone()["id"])
    cur.execute("INSERT INTO universitet_workspace_map(context_id,universitet_id) VALUES(%s,%s)", (workspace_id, university_id))
    _assign_role(cur, university_id, user_id, "owner", created_by=user_id)
    cur.execute("UPDATE users SET universitet_id=COALESCE(universitet_id,%s),lavozim=COALESCE(lavozim,'owner') WHERE user_id=%s", (university_id, user_id))
    return university_id


def _roles(cur, user_id: int, university_id: int) -> list[dict[str, Any]]:
    roles = []
    if _is_global_admin(cur, user_id):
        roles.append({"rol": "institut_admin", "fakultet_id": None, "kafedra_id": None, "yonalish_id": None, "global_admin": True})
    cur.execute("""SELECT rol,fakultet_id,kafedra_id,yonalish_id
        FROM universitet_xodim_rollari
        WHERE universitet_id=%s AND user_id=%s AND faol=TRUE""", (university_id, user_id))
    roles.extend(dict(r) for r in cur.fetchall())
    cur.execute("SELECT id,yonalish_id FROM universitet_qabul_talabalari WHERE universitet_id=%s AND user_id=%s", (university_id, user_id))
    student = cur.fetchone()
    if student:
        roles.append({"rol": "talaba", "fakultet_id": None, "kafedra_id": None, "yonalish_id": student["yonalish_id"], "qabul_id": student["id"]})
    return roles


def _require_member(cur, user_id: int, university_id: int) -> list[dict[str, Any]]:
    roles = _roles(cur, user_id, university_id)
    if not roles:
        raise HTTPException(status_code=403, detail="Siz bu institutga biriktirilmagansiz")
    return roles


def _role_names(roles: list[dict[str, Any]]) -> set[str]:
    return {r["rol"] for r in roles}


def _scope_program_ids(cur, university_id: int, roles: list[dict[str, Any]]) -> Optional[set[int]]:
    names = _role_names(roles)
    if names & INSTITUTE_WIDE:
        return None
    ids: set[int] = set()
    faculties = {int(r["fakultet_id"]) for r in roles if r.get("fakultet_id") and r["rol"] in FACULTY_WIDE}
    departments = {int(r["kafedra_id"]) for r in roles if r.get("kafedra_id") and r["rol"] in DEPARTMENT_WIDE}
    direct = {int(r["yonalish_id"]) for r in roles if r.get("yonalish_id")}
    ids |= direct
    if faculties:
        cur.execute("SELECT id FROM universitet_yonalishlari WHERE universitet_id=%s AND fakultet_id=ANY(%s) AND faol=TRUE", (university_id, list(faculties)))
        ids |= {int(r["id"]) for r in cur.fetchall()}
    if departments:
        cur.execute("SELECT id FROM universitet_yonalishlari WHERE universitet_id=%s AND kafedra_id=ANY(%s) AND faol=TRUE", (university_id, list(departments)))
        ids |= {int(r["id"]) for r in cur.fetchall()}
    tutors = [r for r in roles if r["rol"] == "tyutor"]
    if tutors:
        user_ids = []
        # roles current userga tegishli, caller user_id tashqarida; assignmentdan topamiz.
        # Bu yerda rol yozuvlari user_id bermaydi, shuning uchun keyingi helper caller bilan ishlaydi.
    return ids


def _scope_program_ids_for_user(cur, university_id: int, user_id: int, roles: list[dict[str, Any]]) -> Optional[set[int]]:
    ids = _scope_program_ids(cur, university_id, roles)
    if ids is None:
        return None
    if "tyutor" in _role_names(roles):
        cur.execute("SELECT yonalish_id FROM universitet_tyutor_yonalishlari WHERE universitet_id=%s AND tyutor_user_id=%s AND faol=TRUE", (university_id, user_id))
        ids |= {int(r["yonalish_id"]) for r in cur.fetchall()}
    return ids


def _has_any(roles: list[dict[str, Any]], allowed: set[str]) -> bool:
    return bool(_role_names(roles) & allowed)


def _validate_assignment_scope(cur, university_id: int, roles: list[dict[str, Any]],
                               faculty_id: Optional[int], department_id: Optional[int],
                               program_id: Optional[int]) -> Optional[int]:
    """Tanlangan fakultet/kafedra/yo'nalish bir institut va bir zanjirda ekanini tekshiradi."""
    candidates: list[int] = []
    if faculty_id:
        cur.execute("SELECT id FROM fakultetlar WHERE id=%s AND universitet_id=%s", (faculty_id, university_id))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=400, detail="Fakultet bu institutga tegishli emas")
        candidates.append(int(row["id"]))
    if department_id:
        cur.execute("""SELECT f.id FROM kafedralar k JOIN fakultetlar f ON f.id=k.fakultet_id
            WHERE k.id=%s AND f.universitet_id=%s""", (department_id, university_id))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=400, detail="Kafedra bu institutga tegishli emas")
        candidates.append(int(row["id"]))
    if program_id:
        cur.execute("SELECT fakultet_id FROM universitet_yonalishlari WHERE id=%s AND universitet_id=%s AND faol=TRUE", (program_id, university_id))
        row = cur.fetchone()
        if not row: raise HTTPException(status_code=400, detail="Yo'nalish bu institutga tegishli emas")
        candidates.append(int(row["fakultet_id"]))
    if len(set(candidates)) > 1:
        raise HTTPException(status_code=400, detail="Fakultet, kafedra va yo'nalish bir-biriga mos emas")
    target_faculty = candidates[0] if candidates else None
    if not (_role_names(roles) & INSTITUTE_WIDE):
        allowed = {int(r["fakultet_id"]) for r in roles if r.get("fakultet_id") and r["rol"] in FACULTY_WIDE}
        if target_faculty is None or target_faculty not in allowed:
            raise HTTPException(status_code=403, detail="Faqat o'zingizga biriktirilgan fakultet doirasida ishlashingiz mumkin")
    return target_faculty


def _audit(cur, university_id: int, user_id: int, action: str, object_type: str = "", object_id: Optional[int] = None, detail: Optional[dict] = None):
    cur.execute("""INSERT INTO universitet_audit_log(universitet_id,actor_user_id,amal,obyekt_turi,obyekt_id,tafsilot)
        VALUES(%s,%s,%s,%s,%s,%s::jsonb)""", (university_id, user_id, action, object_type or None, object_id, json.dumps(detail or {}, ensure_ascii=False)))


def _assign_role(cur, university_id: int, user_id: int, role: str, faculty_id: Optional[int] = None, department_id: Optional[int] = None, program_id: Optional[int] = None, created_by: Optional[int] = None) -> int:
    if role not in ROLE_LABELS or role == "talaba":
        raise HTTPException(status_code=400, detail=f"Noto'g'ri lavozim: {role}")
    if role in FACULTY_WIDE and not faculty_id:
        raise HTTPException(status_code=400, detail="Bu lavozim uchun fakultet tanlanishi shart")
    if role in DEPARTMENT_WIDE and not department_id:
        raise HTTPException(status_code=400, detail="Kafedra mudiri uchun kafedra tanlanishi shart")
    cur.execute("""SELECT id FROM universitet_xodim_rollari
        WHERE universitet_id=%s AND user_id=%s AND rol=%s
          AND fakultet_id IS NOT DISTINCT FROM %s
          AND kafedra_id IS NOT DISTINCT FROM %s
          AND yonalish_id IS NOT DISTINCT FROM %s
        LIMIT 1""", (university_id, user_id, role, faculty_id, department_id, program_id))
    existing = cur.fetchone()
    if existing:
        cur.execute("UPDATE universitet_xodim_rollari SET faol=TRUE WHERE id=%s", (existing["id"],))
        return int(existing["id"])
    if role == "zam_dekan":
        cur.execute("SELECT COUNT(*) AS n FROM universitet_xodim_rollari WHERE fakultet_id=%s AND rol='zam_dekan' AND faol=TRUE", (faculty_id,))
        if int(cur.fetchone()["n"]) >= 2:
            raise HTTPException(status_code=409, detail="Bu fakultetda 2 ta dekan o'rinbosari allaqachon bor")
    cur.execute("""INSERT INTO universitet_xodim_rollari(
        universitet_id,fakultet_id,kafedra_id,yonalish_id,user_id,rol,yaratilgan_by)
        VALUES(%s,%s,%s,%s,%s,%s,%s)
        RETURNING id""",
        (university_id, faculty_id, department_id, program_id, user_id, role, created_by))
    return int(cur.fetchone()["id"])


def _new_placeholder(cur, full_name: str, university_id: int, role: str, phone: Optional[str], created_by: int, faculty_id: Optional[int] = None, department_id: Optional[int] = None, program_id: Optional[int] = None) -> tuple[int, int, str]:
    p = _p()
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (20005401,))
    cur.execute("SELECT MIN(user_id) AS min_id FROM users WHERE user_id<0")
    row = cur.fetchone()
    user_id = int(row["min_id"] - 1) if row and row["min_id"] is not None else -1
    cur.execute("INSERT INTO users(user_id,full_name,role,universitet_id,lavozim) VALUES(%s,%s,'oqituvchi',%s,%s)", (user_id, full_name, university_id, role))
    if phone:
        p._telefon_jadvallari(cur)
        cur.execute("INSERT INTO telefon_hisob(telefon,user_id) VALUES(%s,%s) ON CONFLICT(telefon) DO NOTHING", (phone, user_id))
    role_id = _assign_role(cur, university_id, user_id, role, faculty_id, department_id, program_id, created_by)
    p._xodim_kod_jadvali(cur)
    while True:
        plain, stored = p._xodim_kod_yarat()
        cur.execute("SELECT 1 FROM xodim_kod WHERE kod=%s", (stored,))
        if not cur.fetchone():
            break
    cur.execute("INSERT INTO xodim_kod(kod,user_id) VALUES(%s,%s)", (stored, user_id))
    cur.execute("""INSERT INTO universitet_taklif_kodlari(
        universitet_id,xodim_rol_id,placeholder_user_id,kod_hash,turi,yaratilgan_by)
        VALUES(%s,%s,%s,%s,'xodim',%s)""", (university_id, role_id, user_id, stored, created_by))
    return user_id, role_id, plain


def _create_student_invite(cur, row: dict[str, Any], actor_id: int) -> str:
    p = _p()
    current_user_id = int(row["user_id"]) if row.get("user_id") is not None else None
    if current_user_id is not None and current_user_id >= 0:
        raise HTTPException(status_code=409, detail="Talaba sayt akkauntiga allaqachon ulangan")
    if current_user_id is not None:
        user_id = current_user_id
        cur.execute("""UPDATE xodim_kod SET ishlatildi=TRUE WHERE kod IN (
            SELECT kod_hash FROM universitet_taklif_kodlari WHERE qabul_talaba_id=%s
        ) AND ishlatildi=FALSE""", (row["id"],))
    else:
        cur.execute("SELECT pg_advisory_xact_lock(%s)", (20005401,))
        cur.execute("SELECT MIN(user_id) AS min_id FROM users WHERE user_id<0")
        r = cur.fetchone()
        user_id = int(r["min_id"] - 1) if r and r["min_id"] is not None else -1
        full_name = " ".join(x for x in [row["familiya"], row["ism"], row.get("ota_ism")] if x)
        cur.execute("INSERT INTO users(user_id,full_name,role,universitet_id,lavozim) VALUES(%s,%s,'oquvchi',%s,'talaba')", (user_id, full_name, row["universitet_id"]))
        if row.get("telefon"):
            p._telefon_jadvallari(cur)
            cur.execute("INSERT INTO telefon_hisob(telefon,user_id) VALUES(%s,%s) ON CONFLICT(telefon) DO NOTHING", (row["telefon"], user_id))
    p._xodim_kod_jadvali(cur)
    while True:
        plain, stored = p._xodim_kod_yarat()
        cur.execute("SELECT 1 FROM xodim_kod WHERE kod=%s", (stored,))
        if not cur.fetchone():
            break
    cur.execute("INSERT INTO xodim_kod(kod,user_id) VALUES(%s,%s)", (stored, user_id))
    cur.execute("""INSERT INTO universitet_taklif_kodlari(
        universitet_id,qabul_talaba_id,placeholder_user_id,kod_hash,turi,yaratilgan_by)
        VALUES(%s,%s,%s,%s,'talaba',%s)""", (row["universitet_id"], row["id"], user_id, stored, actor_id))
    # Taklif yuborish hali "saytga kirgan" degani emas. 3-bosqich faqat kod
    # haqiqiy akkaunt tomonidan qabul qilinganda redeem_code ichida belgilanadi.
    cur.execute("UPDATE universitet_qabul_talabalari SET user_id=%s,yangilangan_at=NOW() WHERE id=%s", (user_id, row["id"]))
    return plain


def _parse_admission(content: bytes, filename: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sheets = _workbook_rows(content, filename)
    rows = _active_rows(sheets, ("QABUL", "Лист1", "Sheet1"))
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="Qabul faylida ma'lumot qatorlari yo'q")
    headers = _header_map(rows[0])
    required = ["AbiturID", "JSHSHIR", "Familya", "Ism", "Ta'lim shakli", "Ta'lim Tili", "OTM", "Yo'nalish", "Telefon", "Ball"]
    missing = [h for h in required if _key(h) not in headers]
    if missing:
        raise HTTPException(status_code=400, detail="Majburiy ustunlar yetishmaydi: " + ", ".join(missing))
    parsed, errors, warnings = [], [], []
    seen_pin, seen_abitur = set(), set()
    for excel_row, values in enumerate(rows[1:], 2):
        if not any(_norm(v) for v in values):
            continue
        abitur = _text_number(_cell(values, headers, "AbiturID"))
        pin = _digits(_cell(values, headers, "JSHSHIR"))
        family = _norm(_cell(values, headers, "Familya", "Familiya"))
        name = _norm(_cell(values, headers, "Ism"))
        form = _canonical_choice(_cell(values, headers, "Ta'lim shakli"), TA_LIM_SHAKLLARI)
        language = _canonical_choice(_cell(values, headers, "Ta'lim Tili", "Ta'lim tili"), TA_LIM_TILLARI)
        direction = _norm(_cell(values, headers, "Yo'nalish", "Ta'lim yo'nalishi"))
        phone = _telefon(_cell(values, headers, "Telefon"))
        score = _float(_cell(values, headers, "Ball", "Kirish bali"))
        row_errors = []
        if not abitur: row_errors.append("AbiturID bo'sh")
        if len(pin) != 14: row_errors.append("JSHSHIR 14 xonali emas")
        if not family or not name: row_errors.append("F.I.Sh. to'liq emas")
        if not form: row_errors.append("Ta'lim shakli tanilmagan")
        if not language: row_errors.append("Ta'lim tili tanilmagan")
        if not direction: row_errors.append("Yo'nalish bo'sh")
        if not phone: row_errors.append("Telefon noto'g'ri")
        if score is None: row_errors.append("Ball son emas")
        if pin in seen_pin: row_errors.append("Fayl ichida JSHSHIR takror")
        if abitur in seen_abitur: row_errors.append("Fayl ichida AbiturID takror")
        if row_errors:
            errors.append({"qator": excel_row, "xatolar": row_errors})
            continue
        seen_pin.add(pin); seen_abitur.add(abitur)
        birth = _iso_date(_cell(values, headers, "Tug'ilgan sana"))
        if not birth:
            warnings.append({"qator": excel_row, "ogohlantirish": "Tug'ilgan sana aniqlanmadi"})
        parsed.append({
            "excel_row": excel_row, "abitur_id": abitur, "jshshir": pin,
            "jshshir_hash": hashlib.sha256(pin.encode()).hexdigest(),
            "familiya": family, "ism": name, "ota_ism": _norm(_cell(values, headers, "Ota ism")) or None,
            "tugilgan_sana": birth, "pasport_seriya": _norm(_cell(values, headers, "Pasport seriya")) or None,
            "pasport_raqam": _text_number(_cell(values, headers, "Pasport raqam")) or None,
            "tavsiya_turi": _norm(_cell(values, headers, "Tavsiya turi")) or None,
            "talim_shakli": form, "talim_tili": language,
            "otm_nomi": _norm(_cell(values, headers, "OTM")), "yonalish_nomi": direction,
            "telefon": phone, "ball": score,
            "doimiy_region": _norm(_cell(values, headers, "D y region", "Doimiy region")) or None,
            "doimiy_tuman": _norm(_cell(values, headers, "D y tuman", "Doimiy tuman")) or None,
            "maktab_region": _norm(_cell(values, headers, "Maktab region")) or None,
            "maktab_tuman": _norm(_cell(values, headers, "Maktab tuman")) or None,
            "maktab_turi": _norm(_cell(values, headers, "Maktab turi")) or None,
            "maktab_nomi": _norm(_cell(values, headers, "Maktab nomi")) or None,
            "tugatgan_yili": int(_float(_cell(values, headers, "Tugatgan yili")) or 0) or None,
            "attestat": _norm(_cell(values, headers, "Serya va raqam", "Seriya va raqam")) or None,
        })
    counts = lambda key: {v: sum(1 for r in parsed if r[key] == v) for v in sorted({r[key] for r in parsed})}
    summary = {
        "jami_qator": len(rows) - 1, "yaroqli": len(parsed), "xato_soni": len(errors),
        "ogohlantirish_soni": len(warnings), "xatolar": errors[:100], "ogohlantirishlar": warnings[:100],
        "yonalishlar": counts("yonalish_nomi"), "talim_shakllari": counts("talim_shakli"),
        "talim_tillari": counts("talim_tili"),
    }
    return parsed, summary


def _role_key(value: Any) -> Optional[str]:
    k = _key(value)
    aliases = {
        "institutegasi": "owner", "rektor": "rektor", "prorektor": "prorektor",
        "institutadministratori": "institut_admin", "institutadmin": "institut_admin",
        "dekan": "dekan", "dekano'rinbosari": "zam_dekan", "dekanorinbosari": "zam_dekan",
        "zamdekan": "zam_dekan", "manaviyatchi": "manaviyatchi",
        "manaviyma'rifiyishlarmas'uli": "manaviyatchi", "manaviymarifiyishlarmasuli": "manaviyatchi",
        "fakultetadministratori": "fakultet_admin", "fakultetadmin": "fakultet_admin",
        "kafedramudiri": "kafedra_mudiri", "professoro'qituvchi": "professor_oqituvchi",
        "professoroqituvchi": "professor_oqituvchi", "tyutor": "tyutor",
    }
    if k in ROLE_LABELS:
        return k
    return aliases.get(k)


def _parse_structure(content: bytes, filename: str) -> tuple[dict[str, Any], dict[str, Any]]:
    sheets = _workbook_rows(content, filename)
    institute_rows = _named_rows(sheets, "INSTITUT")
    structure_rows = _named_rows(sheets, "TUZILMA")
    staff_rows = _named_rows(sheets, "XODIMLAR")
    if not institute_rows or not structure_rows or not staff_rows:
        raise HTTPException(status_code=400, detail="Shablonda INSTITUT, TUZILMA va XODIMLAR varaqlari bo'lishi shart")

    institute = {}
    for row in institute_rows:
        if len(row) >= 2 and _norm(row[0]):
            institute[_key(row[0])] = _norm(row[1])
    name = institute.get(_key("Institut nomi")) or institute.get("institutnomi")
    if not name:
        raise HTTPException(status_code=400, detail="INSTITUT varag'ida 'Institut nomi' to'ldirilmagan")

    required = ["Fakultet", "Kafedra", "Yo'nalish nomi", "Daraja", "Ta'lim shakli", "Ta'lim tili"]
    structure_header_index, sh = _find_header_row(structure_rows, required, "TUZILMA")
    structures, errors, warnings = [], [], []
    seen_variants = set()
    for row_no, row in enumerate(structure_rows[structure_header_index + 1:], structure_header_index + 2):
        if not any(_norm(v) for v in row):
            continue
        faculty = _norm(_cell(row, sh, "Fakultet"))
        department = _norm(_cell(row, sh, "Kafedra"))
        program = _norm(_cell(row, sh, "Yo'nalish nomi"))
        code = _norm(_cell(row, sh, "Yo'nalish kodi")) or None
        degree = _canonical_choice(_cell(row, sh, "Daraja"), DARAJALAR)
        form = _canonical_choice(_cell(row, sh, "Ta'lim shakli"), TA_LIM_SHAKLLARI)
        language = _canonical_choice(_cell(row, sh, "Ta'lim tili"), TA_LIM_TILLARI)
        row_errors = []
        if not faculty: row_errors.append("Fakultet bo'sh")
        if not department: row_errors.append("Kafedra bo'sh")
        if not program: row_errors.append("Yo'nalish bo'sh")
        if not degree: row_errors.append("Daraja noto'g'ri")
        if not form: row_errors.append("Ta'lim shakli noto'g'ri")
        if not language: row_errors.append("Ta'lim tili noto'g'ri")
        variant_key = (_key(faculty), _key(department), _key(program), degree, form, language)
        if variant_key in seen_variants: row_errors.append("Aynan shu yo'nalish/shakl/til takrorlangan")
        if row_errors:
            errors.append({"varaq": "TUZILMA", "qator": row_no, "xatolar": row_errors}); continue
        seen_variants.add(variant_key)
        structures.append({"fakultet": faculty, "kafedra": department, "yonalish": program,
                           "yonalish_kodi": code, "daraja": degree, "talim_shakli": form, "talim_tili": language})

    staff_required = ["F.I.Sh.", "Lavozim"]
    staff_header_index, xh = _find_header_row(staff_rows, staff_required, "XODIMLAR")
    staff, seen_people = [], set()
    for row_no, row in enumerate(staff_rows[staff_header_index + 1:], staff_header_index + 2):
        if not any(_norm(v) for v in row):
            continue
        fish = _norm(_cell(row, xh, "F.I.Sh.", "FISH"))
        role = _role_key(_cell(row, xh, "Lavozim"))
        phone_raw = _cell(row, xh, "Telefon")
        phone = _telefon(phone_raw) if phone_raw not in (None, "") else None
        faculty = _norm(_cell(row, xh, "Fakultet")) or None
        department = _norm(_cell(row, xh, "Kafedra")) or None
        program = _norm(_cell(row, xh, "Yo'nalish")) or None
        row_errors = []
        if not fish: row_errors.append("F.I.Sh. bo'sh")
        if not role: row_errors.append("Lavozim tanilmadi")
        if phone_raw not in (None, "") and not phone: row_errors.append("Telefon noto'g'ri")
        if role in FACULTY_WIDE and not faculty: row_errors.append("Bu lavozim uchun fakultet shart")
        if role in DEPARTMENT_WIDE and not department: row_errors.append("Kafedra mudiri uchun kafedra shart")
        person_key = (_key(fish), role, _key(faculty), _key(department), _key(program))
        if person_key in seen_people: row_errors.append("Xodim qatori takrorlangan")
        if row_errors:
            errors.append({"varaq": "XODIMLAR", "qator": row_no, "xatolar": row_errors}); continue
        seen_people.add(person_key)
        staff.append({"fish": fish, "telefon": phone, "rol": role, "fakultet": faculty,
                      "kafedra": department, "yonalish": program, "excel_row": row_no})

    faculty_names = sorted({x["fakultet"] for x in structures})
    department_pairs = {(x["fakultet"], x["kafedra"]) for x in structures}
    for item in staff:
        if item["fakultet"] and item["fakultet"] not in faculty_names:
            errors.append({"varaq": "XODIMLAR", "qator": item["excel_row"], "xatolar": ["Fakultet TUZILMA varag'ida yo'q"]})
        if item["kafedra"] and (item["fakultet"], item["kafedra"]) not in department_pairs:
            errors.append({"varaq": "XODIMLAR", "qator": item["excel_row"], "xatolar": ["Kafedra va fakultet mos emas"]})
    completeness = {}
    for faculty in faculty_names:
        members = [x for x in staff if x["fakultet"] == faculty]
        counts = {r: sum(1 for x in members if x["rol"] == r) for r in ("dekan", "zam_dekan", "manaviyatchi", "fakultet_admin")}
        completeness[faculty] = counts
        if counts["dekan"] != 1:
            errors.append({"varaq": "XODIMLAR", "qator": None, "xatolar": [f"{faculty}: aynan 1 ta dekan bo'lishi kerak"]})
        if counts["zam_dekan"] != 2:
            errors.append({"varaq": "XODIMLAR", "qator": None, "xatolar": [f"{faculty}: aynan 2 ta dekan o'rinbosari bo'lishi kerak"]})
        if counts["manaviyatchi"] != 1:
            errors.append({"varaq": "XODIMLAR", "qator": None, "xatolar": [f"{faculty}: aynan 1 ta ma'naviyatchi bo'lishi kerak"]})
        if counts["fakultet_admin"] == 0:
            warnings.append(f"{faculty}: alohida admin kiritilmagan; importni bajargan admin avtomatik biriktiriladi")

    payload = {"institut": {"nomi": name, "viloyat": institute.get(_key("Viloyat")) or None,
                             "tuman": institute.get(_key("Tuman")) or None},
               "tuzilma": structures, "xodimlar": staff}
    summary = {"institut_nomi": name, "fakultet_soni": len(faculty_names),
               "kafedra_soni": len(department_pairs), "yonalish_variant_soni": len(structures),
               "xodim_soni": len(staff), "fakultet_toldirilishi": completeness,
               "xato_soni": len(errors), "xatolar": errors[:150], "ogohlantirishlar": warnings}
    return payload, summary


def _store_batch(cur, university_id: Optional[int], kind: str, filename: str, content: bytes, payload: Any, summary: dict, user_id: int) -> int:
    cur.execute("""INSERT INTO universitet_import_batchlar(
        universitet_id,import_turi,fayl_nomi,fayl_sha256,payload,xulosa,yaratilgan_by)
        VALUES(%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s) RETURNING id""",
        (university_id, kind, filename, hashlib.sha256(content).hexdigest(), json.dumps(payload, ensure_ascii=False), json.dumps(summary, ensure_ascii=False), user_id))
    return int(cur.fetchone()["id"])


class InstituteCreate(BaseModel):
    token: str
    nomi: str
    viloyat: Optional[str] = None
    tuman: Optional[str] = None


class DepartmentInput(BaseModel):
    nomi: str
    yonalishlar: list[str] = Field(default_factory=list)


class FacultyInput(BaseModel):
    nomi: str
    kafedralar: list[DepartmentInput] = Field(default_factory=list)


class StructureManual(BaseModel):
    token: str
    universitet_id: int
    fakultetlar: list[FacultyInput]


class StaffCreate(BaseModel):
    token: str
    universitet_id: int
    fish: str
    telefon: Optional[str] = None
    rol: str
    fakultet_id: Optional[int] = None
    kafedra_id: Optional[int] = None
    yonalish_id: Optional[int] = None


class TutorAssign(BaseModel):
    token: str
    universitet_id: int
    tyutor_user_id: int
    yonalish_id: int
    talim_shakli: Optional[str] = None
    talim_tili: Optional[str] = None


class BatchCommit(BaseModel):
    token: str
    batch_id: int
    default_kafedra_id: Optional[int] = None
    auto_create_yonalishlar: bool = False


class StageUpdate(BaseModel):
    token: str
    bosqich: int


class InviteSend(BaseModel):
    token: str
    kanal: str = "copy"  # copy | sms


class RedeemCode(BaseModel):
    token: str
    kirish_kodi: str


@router.post("/institut_yarat")
def create_institute(req: InstituteCreate):
    p = _p(); user_id = p._admin_tekshir(req.token)
    if not _norm(req.nomi):
        raise HTTPException(status_code=400, detail="Institut nomini kiriting")
    conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur)
        cur.execute("INSERT INTO universitetlar(nomi,viloyat,tuman) VALUES(%s,%s,%s) RETURNING id", (_norm(req.nomi), _norm(req.viloyat) or None, _norm(req.tuman) or None))
        university_id = int(cur.fetchone()["id"])
        _assign_role(cur, university_id, user_id, "institut_admin", created_by=user_id)
        cur.execute("UPDATE users SET universitet_id=COALESCE(universitet_id,%s),lavozim=COALESCE(lavozim,'institut_admin') WHERE user_id=%s", (university_id, user_id))
        _audit(cur, university_id, user_id, "institut_yaratildi", "universitet", university_id)
        conn.commit()
        return {"holat": "yaratildi", "universitet_id": university_id}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.get("/bootstrap")
def bootstrap(workspace_id: Optional[int] = None, universitet_id: Optional[int] = None, token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p(); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur)
        uid = int(universitet_id) if universitet_id else _resolve_university(cur, user_id, workspace_id, create=True)
        roles = _require_member(cur, user_id, uid)
        cur.execute("SELECT id,nomi,viloyat,tuman FROM universitetlar WHERE id=%s", (uid,))
        university = cur.fetchone()
        cur.execute("SELECT COUNT(*) n FROM fakultetlar WHERE universitet_id=%s", (uid,)); faculties = int(cur.fetchone()["n"])
        cur.execute("SELECT COUNT(*) n FROM universitet_yonalishlari WHERE universitet_id=%s AND faol=TRUE", (uid,)); programs = int(cur.fetchone()["n"])
        cur.execute("SELECT COUNT(*) n FROM universitet_qabul_talabalari WHERE universitet_id=%s", (uid,)); students = int(cur.fetchone()["n"])
        names = _role_names(roles)
        permissions = {
            "tuzilma_boshqarish": bool(names & MANAGE_STRUCTURE_ROLES),
            "xodim_boshqarish": bool(names & MANAGE_STAFF_ROLES),
            "qabul_korish": bool(names & PRIVATE_ROLES),
            "hujjat_belgilash": bool(names & MARK_DOCUMENT_ROLES),
            "saytga_kiritish": bool(names & (MARK_DOCUMENT_ROLES | {"tyutor"})),
            "maxfiy_malumot": bool(names & PRIVATE_ROLES),
        }
        conn.commit()
        return {"release": SAMTM_INSTITUTE_RELEASE, "universitet": university, "rollar": roles,
                "asosiy_rol": roles[0]["rol"], "ruxsatlar": permissions,
                "sonlar": {"fakultet": faculties, "yonalish": programs, "talaba": students}}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.get("/tuzilma")
def structure(universitet_id: int, token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p(); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); _require_member(cur, user_id, universitet_id)
        cur.execute("""SELECT f.id,f.nomi,
            (SELECT COUNT(*) FROM kafedralar k WHERE k.fakultet_id=f.id) kafedra_soni,
            (SELECT COUNT(*) FROM universitet_yonalishlari y WHERE y.fakultet_id=f.id AND y.faol=TRUE) yonalish_soni
            FROM fakultetlar f WHERE f.universitet_id=%s ORDER BY f.nomi""", (universitet_id,))
        faculties = [dict(r) for r in cur.fetchall()]
        for f in faculties:
            cur.execute("SELECT id,nomi FROM kafedralar WHERE fakultet_id=%s ORDER BY nomi", (f["id"],))
            f["kafedralar"] = [dict(r) for r in cur.fetchall()]
            for d in f["kafedralar"]:
                cur.execute("SELECT id,kodi,nomi,daraja FROM universitet_yonalishlari WHERE kafedra_id=%s AND faol=TRUE ORDER BY nomi", (d["id"],))
                d["yonalishlar"] = cur.fetchall()
            cur.execute("""SELECT xr.id,xr.user_id,xr.rol,u.full_name
                FROM universitet_xodim_rollari xr JOIN users u ON u.user_id=xr.user_id
                WHERE xr.fakultet_id=%s AND xr.faol=TRUE ORDER BY xr.rol,u.full_name""", (f["id"],))
            f["rahbariyat"] = cur.fetchall()
            counts = {role: sum(1 for x in f["rahbariyat"] if x["rol"] == role) for role in ("dekan", "zam_dekan", "manaviyatchi", "fakultet_admin")}
            f["toldirilish"] = {"dekan": counts["dekan"], "zam_dekan": counts["zam_dekan"], "manaviyatchi": counts["manaviyatchi"], "admin": counts["fakultet_admin"],
                                "tayyor": counts["dekan"] == 1 and counts["zam_dekan"] == 2 and counts["manaviyatchi"] == 1 and counts["fakultet_admin"] >= 1}
        return {"fakultetlar": faculties, "talim_shakllari": TA_LIM_SHAKLLARI, "talim_tillari": TA_LIM_TILLARI, "darajalar": DARAJALAR}
    finally:
        cur.close(); conn.close()


@router.post("/tuzilma/manual")
def manual_structure(req: StructureManual):
    p = _p(); user_id = p._jwt_tekshir(req.token); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); roles = _require_member(cur, user_id, req.universitet_id)
        if not _has_any(roles, MANAGE_STRUCTURE_ROLES): raise HTTPException(status_code=403, detail="Tuzilmani boshqarish huquqi yo'q")
        if not req.fakultetlar: raise HTTPException(status_code=400, detail="Kamida 1 ta fakultet kiriting")
        created = {"fakultet": 0, "kafedra": 0, "yonalish": 0}
        for f in req.fakultetlar:
            fname = _norm(f.nomi)
            if not fname: raise HTTPException(status_code=400, detail="Fakultet nomi bo'sh")
            cur.execute("SELECT id FROM fakultetlar WHERE universitet_id=%s AND LOWER(nomi)=LOWER(%s)", (req.universitet_id, fname)); fr = cur.fetchone()
            if fr: faculty_id = int(fr["id"])
            else:
                cur.execute("INSERT INTO fakultetlar(universitet_id,nomi) VALUES(%s,%s) RETURNING id", (req.universitet_id, fname)); faculty_id = int(cur.fetchone()["id"]); created["fakultet"] += 1
                _assign_role(cur, req.universitet_id, user_id, "fakultet_admin", faculty_id=faculty_id, created_by=user_id)
            for d in f.kafedralar:
                dname = _norm(d.nomi)
                if not dname: raise HTTPException(status_code=400, detail=f"{fname}: kafedra nomi bo'sh")
                cur.execute("SELECT id FROM kafedralar WHERE fakultet_id=%s AND LOWER(nomi)=LOWER(%s)", (faculty_id, dname)); dr = cur.fetchone()
                if dr: department_id = int(dr["id"])
                else:
                    cur.execute("INSERT INTO kafedralar(fakultet_id,nomi) VALUES(%s,%s) RETURNING id", (faculty_id, dname)); department_id = int(cur.fetchone()["id"]); created["kafedra"] += 1
                for program in d.yonalishlar:
                    pname = _norm(program)
                    if not pname: continue
                    cur.execute("""INSERT INTO universitet_yonalishlari(universitet_id,fakultet_id,kafedra_id,nomi)
                        VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id""", (req.universitet_id, faculty_id, department_id, pname))
                    if cur.fetchone(): created["yonalish"] += 1
        _audit(cur, req.universitet_id, user_id, "tuzilma_qolda_saqlandi", detail=created)
        conn.commit(); return {"holat": "saqlandi", **created}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.post("/xodim/manual")
def manual_staff(req: StaffCreate):
    p = _p(); user_id = p._jwt_tekshir(req.token); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); roles = _require_member(cur, user_id, req.universitet_id)
        if not _has_any(roles, MANAGE_STAFF_ROLES): raise HTTPException(status_code=403, detail="Xodim biriktirish huquqi yo'q")
        if not (_role_names(roles) & INSTITUTE_WIDE) and req.rol in INSTITUTE_WIDE:
            raise HTTPException(status_code=403, detail="Institut rahbari yoki adminini faqat institut administratori qo'shadi")
        _validate_assignment_scope(cur, req.universitet_id, roles, req.fakultet_id, req.kafedra_id, req.yonalish_id)
        fish = _norm(req.fish); phone = _telefon(req.telefon) if req.telefon else None
        if not fish: raise HTTPException(status_code=400, detail="F.I.Sh. kiriting")
        if req.telefon and not phone: raise HTTPException(status_code=400, detail="Telefon +998 bilan to'g'ri yozilsin")
        placeholder, role_id, code = _new_placeholder(cur, fish, req.universitet_id, req.rol, phone, user_id, req.fakultet_id, req.kafedra_id, req.yonalish_id)
        _audit(cur, req.universitet_id, user_id, "xodim_qoshildi", "xodim_rol", role_id, {"rol": req.rol})
        conn.commit()
        return {"holat": "yaratildi", "user_id": placeholder, "rol_id": role_id, "fish": fish,
                "lavozim": ROLE_LABELS[req.rol], "kirish_kodi": code, "kod_muddati": "7 kun"}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.post("/tuzilma/import_preview")
async def structure_preview(universitet_id: int, fayl: UploadFile = File(...), token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p()
    content = await fayl.read()
    if len(content) > 15 * 1024 * 1024: raise HTTPException(status_code=413, detail="Tuzilma fayli 15 MB dan katta")
    if not (fayl.filename or "").lower().endswith(".xlsx"): raise HTTPException(status_code=400, detail="Institut tuzilmasi uchun .xlsx shablondan foydalaning")
    payload, summary = _parse_structure(content, fayl.filename or "institut_tuzilma.xlsx")
    conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); roles = _require_member(cur, user_id, universitet_id)
        if not _has_any(roles, MANAGE_STRUCTURE_ROLES): raise HTTPException(status_code=403, detail="Tuzilma importiga ruxsat yo'q")
        cur.execute("SELECT nomi FROM universitetlar WHERE id=%s", (universitet_id,)); university = cur.fetchone()
        if not university: raise HTTPException(status_code=404, detail="Institut topilmadi")
        summary["nom_mosligi"] = _key(university["nomi"]) == _key(payload["institut"]["nomi"])
        if not summary["nom_mosligi"]:
            summary["xatolar"].append({"varaq": "INSTITUT", "qator": 2, "xatolar": [f"Institut nomi mos emas: saytda '{university['nomi']}'"]})
            summary["xato_soni"] += 1
        batch_id = _store_batch(cur, universitet_id, "tuzilma", fayl.filename or "institut_tuzilma.xlsx", content, payload, summary, user_id)
        conn.commit(); return {"batch_id": batch_id, "xulosa": summary, "commit_mumkin": summary["xato_soni"] == 0}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.post("/tuzilma/import_commit")
def structure_commit(req: BatchCommit):
    p = _p(); actor = p._jwt_tekshir(req.token); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur)
        cur.execute("SELECT * FROM universitet_import_batchlar WHERE id=%s FOR UPDATE", (req.batch_id,)); batch = cur.fetchone()
        if not batch or batch["import_turi"] != "tuzilma": raise HTTPException(status_code=404, detail="Tuzilma preview topilmadi")
        if batch["holat"] != "preview": raise HTTPException(status_code=409, detail="Bu preview avval ishlatilgan")
        if batch["yaratilgan_by"] != actor and not _is_global_admin(cur, actor): raise HTTPException(status_code=403, detail="Bu preview boshqa foydalanuvchiga tegishli")
        roles = _require_member(cur, actor, batch["universitet_id"])
        if not _has_any(roles, MANAGE_STRUCTURE_ROLES): raise HTTPException(status_code=403, detail="Tuzilma importiga ruxsat yo'q")
        summary = batch["xulosa"] if isinstance(batch["xulosa"], dict) else json.loads(batch["xulosa"])
        if summary.get("xato_soni"): raise HTTPException(status_code=400, detail="Xatoli shablon commit qilinmaydi")
        payload = batch["payload"] if isinstance(batch["payload"], dict) else json.loads(batch["payload"])
        university_id = int(batch["universitet_id"])
        cur.execute("UPDATE universitetlar SET viloyat=COALESCE(%s,viloyat),tuman=COALESCE(%s,tuman) WHERE id=%s",
                    (payload["institut"].get("viloyat"), payload["institut"].get("tuman"), university_id))
        faculty_map, department_map, program_map = {}, {}, {}
        counts = {"fakultet": 0, "kafedra": 0, "yonalish": 0, "variant": 0, "xodim": 0}
        for item in payload["tuzilma"]:
            fk = _key(item["fakultet"])
            if fk not in faculty_map:
                cur.execute("SELECT id FROM fakultetlar WHERE universitet_id=%s AND LOWER(nomi)=LOWER(%s)", (university_id, item["fakultet"])); row = cur.fetchone()
                if row: faculty_id = int(row["id"])
                else:
                    cur.execute("INSERT INTO fakultetlar(universitet_id,nomi) VALUES(%s,%s) RETURNING id", (university_id, item["fakultet"])); faculty_id = int(cur.fetchone()["id"]); counts["fakultet"] += 1
                faculty_map[fk] = faculty_id
                # Shablonda admin bo'lmasa importchi shu fakultetga avtomatik admin.
                _assign_role(cur, university_id, actor, "fakultet_admin", faculty_id=faculty_id, created_by=actor)
            faculty_id = faculty_map[fk]
            dk = (fk, _key(item["kafedra"]))
            if dk not in department_map:
                cur.execute("SELECT id FROM kafedralar WHERE fakultet_id=%s AND LOWER(nomi)=LOWER(%s)", (faculty_id, item["kafedra"])); row = cur.fetchone()
                if row: department_id = int(row["id"])
                else:
                    cur.execute("INSERT INTO kafedralar(fakultet_id,nomi) VALUES(%s,%s) RETURNING id", (faculty_id, item["kafedra"])); department_id = int(cur.fetchone()["id"]); counts["kafedra"] += 1
                department_map[dk] = department_id
            department_id = department_map[dk]
            pk = (dk, _key(item["yonalish"]), item["daraja"])
            if pk not in program_map:
                cur.execute("""SELECT id FROM universitet_yonalishlari WHERE universitet_id=%s AND kafedra_id=%s AND LOWER(nomi)=LOWER(%s) AND daraja=%s""",
                            (university_id, department_id, item["yonalish"], item["daraja"])); row = cur.fetchone()
                if row: program_id = int(row["id"])
                else:
                    cur.execute("""INSERT INTO universitet_yonalishlari(universitet_id,fakultet_id,kafedra_id,kodi,nomi,daraja)
                        VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""", (university_id, faculty_id, department_id, item.get("yonalish_kodi"), item["yonalish"], item["daraja"])); program_id = int(cur.fetchone()["id"]); counts["yonalish"] += 1
                program_map[pk] = program_id
            program_id = program_map[pk]
            cur.execute("""INSERT INTO universitet_yonalish_variantlari(yonalish_id,talim_shakli,talim_tili)
                VALUES(%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id""", (program_id, item["talim_shakli"], item["talim_tili"]))
            if cur.fetchone(): counts["variant"] += 1

        credentials = []
        for person in payload["xodimlar"]:
            role = person["rol"]
            faculty_id = faculty_map.get(_key(person.get("fakultet"))) if person.get("fakultet") else None
            department_id = department_map.get((_key(person.get("fakultet")), _key(person.get("kafedra")))) if person.get("kafedra") else None
            program_id = None
            if person.get("yonalish"):
                candidates = [pid for key, pid in program_map.items() if key[0][0] == _key(person.get("fakultet")) and key[1] == _key(person["yonalish"])]
                if len(candidates) == 1: program_id = candidates[0]
            placeholder, role_id, code = _new_placeholder(cur, person["fish"], university_id, role, person.get("telefon"), actor, faculty_id, department_id, program_id)
            counts["xodim"] += 1
            credentials.append({"fish": person["fish"], "lavozim": ROLE_LABELS[role], "kirish_kodi": code, "kod_muddati": "7 kun"})
        cur.execute("UPDATE universitet_import_batchlar SET holat='committed',commit_at=NOW() WHERE id=%s", (req.batch_id,))
        _audit(cur, university_id, actor, "tuzilma_import_commit", "import_batch", req.batch_id, counts)
        conn.commit(); return {"holat": "import_qilindi", "sonlar": counts, "kirish_kodlari": credentials,
                               "eslatma": "Kirish kodlari faqat shu javobda bir marta ko'rsatiladi"}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.get("/xodimlar")
def staff_list(universitet_id: int, token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p(); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); _require_member(cur, user_id, universitet_id)
        cur.execute("""SELECT xr.id,xr.user_id,xr.rol,u.full_name,f.nomi fakultet_nomi,k.nomi kafedra_nomi,y.nomi yonalish_nomi,
            CASE WHEN tk.id IS NULL THEN NULL WHEN xk.ishlatildi THEN 'ulangan' ELSE 'taklif_yuborilgan' END kirish_holati
            FROM universitet_xodim_rollari xr JOIN users u ON u.user_id=xr.user_id
            LEFT JOIN fakultetlar f ON f.id=xr.fakultet_id LEFT JOIN kafedralar k ON k.id=xr.kafedra_id
            LEFT JOIN universitet_yonalishlari y ON y.id=xr.yonalish_id
            LEFT JOIN LATERAL (SELECT * FROM universitet_taklif_kodlari t WHERE t.xodim_rol_id=xr.id ORDER BY t.id DESC LIMIT 1) tk ON TRUE
            LEFT JOIN xodim_kod xk ON xk.kod=tk.kod_hash
            WHERE xr.universitet_id=%s AND xr.faol=TRUE ORDER BY f.nomi NULLS FIRST,xr.rol,u.full_name""", (universitet_id,))
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows: r["lavozim_nomi"] = ROLE_LABELS.get(r["rol"], r["rol"])
        return {"xodimlar": rows, "lavozimlar": ROLE_LABELS}
    finally:
        cur.close(); conn.close()


@router.post("/tyutor/biriktir")
def assign_tutor(req: TutorAssign):
    p = _p(); actor = p._jwt_tekshir(req.token); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); roles = _require_member(cur, actor, req.universitet_id)
        if not _has_any(roles, MANAGE_STAFF_ROLES): raise HTTPException(status_code=403, detail="Tyutor biriktirish huquqi yo'q")
        scope = _scope_program_ids_for_user(cur, req.universitet_id, actor, roles)
        if scope is not None and req.yonalish_id not in scope:
            raise HTTPException(status_code=403, detail="Bu yo'nalish sizning fakultetingizga tegishli emas")
        cur.execute("SELECT 1 FROM universitet_yonalishlari WHERE id=%s AND universitet_id=%s AND faol=TRUE", (req.yonalish_id, req.universitet_id))
        if not cur.fetchone(): raise HTTPException(status_code=400, detail="Yo'nalish bu institutga tegishli emas")
        form = _canonical_choice(req.talim_shakli, TA_LIM_SHAKLLARI) if req.talim_shakli else None
        language = _canonical_choice(req.talim_tili, TA_LIM_TILLARI) if req.talim_tili else None
        cur.execute("SELECT 1 FROM universitet_xodim_rollari WHERE universitet_id=%s AND user_id=%s AND rol='tyutor' AND faol=TRUE", (req.universitet_id, req.tyutor_user_id))
        if not cur.fetchone(): raise HTTPException(status_code=400, detail="Tanlangan xodim tyutor emas")
        cur.execute("""INSERT INTO universitet_tyutor_yonalishlari(
            universitet_id,tyutor_user_id,yonalish_id,talim_shakli,talim_tili,yaratilgan_by)
            VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id""",
            (req.universitet_id, req.tyutor_user_id, req.yonalish_id, form, language, actor))
        new = cur.fetchone(); conn.commit()
        return {"holat": "biriktirildi" if new else "avval_biriktirilgan"}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.post("/qabul/import_preview")
async def admission_preview(universitet_id: int, fayl: UploadFile = File(...), token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p()
    content = await fayl.read()
    if len(content) > 25 * 1024 * 1024: raise HTTPException(status_code=413, detail="Qabul fayli 25 MB dan katta")
    if not (fayl.filename or "").lower().endswith((".xls", ".xlsx")): raise HTTPException(status_code=400, detail="Faqat .xls yoki .xlsx fayl qabul qilinadi")
    parsed, summary = _parse_admission(content, fayl.filename or "qabul.xls")
    conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); roles = _require_member(cur, user_id, universitet_id)
        if not _has_any(roles, MARK_DOCUMENT_ROLES): raise HTTPException(status_code=403, detail="Qabul importiga ruxsat yo'q")
        cur.execute("SELECT id,nomi FROM universitet_yonalishlari WHERE universitet_id=%s AND faol=TRUE", (universitet_id,))
        known_rows: dict[str, list[dict[str, Any]]] = {}
        for row in cur.fetchall():
            known_rows.setdefault(_key(row["nomi"]), []).append(dict(row))
        known = {key: values[0] for key, values in known_rows.items() if len(values) == 1}
        ambiguous = {name: len(known_rows[_key(name)]) for name in summary["yonalishlar"] if len(known_rows.get(_key(name), [])) > 1}
        unknown = {name: count for name, count in summary["yonalishlar"].items() if _key(name) not in known}
        for name in ambiguous:
            unknown.pop(name, None)
        summary["noma_lum_yonalishlar"] = unknown
        summary["noaniq_yonalishlar"] = ambiguous
        summary["mos_yonalishlar"] = {name: known[_key(name)]["id"] for name in summary["yonalishlar"] if _key(name) in known}
        cur.execute("SELECT nomi FROM universitetlar WHERE id=%s", (universitet_id,)); university = cur.fetchone()
        foreign_names = sorted({r["otm_nomi"] for r in parsed if r["otm_nomi"] and _key(r["otm_nomi"]) != _key(university["nomi"])})
        summary["otm_nomi_farqi"] = foreign_names
        batch_id = _store_batch(cur, universitet_id, "qabul", fayl.filename or "qabul.xls", content, parsed, summary, user_id)
        conn.commit(); return {"batch_id": batch_id, "xulosa": summary,
                               "commit_mumkin": summary["xato_soni"] == 0 and not foreign_names and not ambiguous}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.post("/qabul/import_commit")
def admission_commit(req: BatchCommit):
    p = _p(); actor = p._jwt_tekshir(req.token); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur)
        cur.execute("SELECT * FROM universitet_import_batchlar WHERE id=%s FOR UPDATE", (req.batch_id,)); batch = cur.fetchone()
        if not batch or batch["import_turi"] != "qabul": raise HTTPException(status_code=404, detail="Qabul preview topilmadi")
        if batch["yaratilgan_by"] != actor and not _is_global_admin(cur, actor): raise HTTPException(status_code=403, detail="Bu preview boshqa foydalanuvchiga tegishli")
        if batch["holat"] != "preview": raise HTTPException(status_code=409, detail="Bu preview avval ishlatilgan")
        roles = _require_member(cur, actor, batch["universitet_id"])
        if not _has_any(roles, MARK_DOCUMENT_ROLES): raise HTTPException(status_code=403, detail="Qabul importiga ruxsat yo'q")
        payload = batch["payload"] if isinstance(batch["payload"], list) else json.loads(batch["payload"])
        summary = batch["xulosa"] if isinstance(batch["xulosa"], dict) else json.loads(batch["xulosa"])
        if summary.get("xato_soni"): raise HTTPException(status_code=400, detail="Xatoli fayl commit qilinmaydi; preview xatolarini tuzating")
        if summary.get("otm_nomi_farqi"): raise HTTPException(status_code=400, detail="Fayldagi OTM nomi tanlangan institutga mos emas")
        cur.execute("SELECT id,nomi,fakultet_id,kafedra_id FROM universitet_yonalishlari WHERE universitet_id=%s AND faol=TRUE", (batch["universitet_id"],))
        program_rows: dict[str, list[dict[str, Any]]] = {}
        for row in cur.fetchall():
            program_rows.setdefault(_key(row["nomi"]), []).append(dict(row))
        ambiguous_names = sorted({r["yonalish_nomi"] for r in payload if len(program_rows.get(_key(r["yonalish_nomi"]), [])) > 1})
        if ambiguous_names:
            raise HTTPException(status_code=400, detail="Bir xil nomli yo'nalishlar bir nechta kafedrada bor; yo'nalish nomlarini aniqlashtiring: " + ", ".join(ambiguous_names))
        programs = {key: values[0] for key, values in program_rows.items() if len(values) == 1}
        unknown_names = sorted({r["yonalish_nomi"] for r in payload if _key(r["yonalish_nomi"]) not in programs})
        if unknown_names:
            if not req.auto_create_yonalishlar or not req.default_kafedra_id:
                raise HTTPException(status_code=400, detail="Noma'lum yo'nalishlar uchun kafedra tanlang: " + ", ".join(unknown_names))
            cur.execute("SELECT k.id,k.fakultet_id FROM kafedralar k JOIN fakultetlar f ON f.id=k.fakultet_id WHERE k.id=%s AND f.universitet_id=%s", (req.default_kafedra_id, batch["universitet_id"])); dep = cur.fetchone()
            if not dep: raise HTTPException(status_code=400, detail="Tanlangan kafedra bu institutga tegishli emas")
            for name in unknown_names:
                cur.execute("""INSERT INTO universitet_yonalishlari(universitet_id,fakultet_id,kafedra_id,nomi)
                    VALUES(%s,%s,%s,%s) RETURNING id""", (batch["universitet_id"], dep["fakultet_id"], dep["id"], name))
                programs[_key(name)] = {"id": int(cur.fetchone()["id"]), "nomi": name}
        for variant in {(r["yonalish_nomi"], r["talim_shakli"], r["talim_tili"]) for r in payload}:
            program_id = programs[_key(variant[0])]["id"]
            cur.execute("""INSERT INTO universitet_yonalish_variantlari(yonalish_id,talim_shakli,talim_tili)
                VALUES(%s,%s,%s) ON CONFLICT DO NOTHING""", (program_id, variant[1], variant[2]))
        inserted = updated = 0
        sql = """INSERT INTO universitet_qabul_talabalari(
            universitet_id,yonalish_id,abitur_id,jshshir,jshshir_hash,familiya,ism,ota_ism,tugilgan_sana,
            pasport_seriya,pasport_raqam,tavsiya_turi,talim_shakli,talim_tili,telefon,ball,doimiy_region,
            doimiy_tuman,maktab_region,maktab_tuman,maktab_turi,maktab_nomi,tugatgan_yili,attestat,otm_nomi,import_batch_id)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(universitet_id,jshshir_hash) DO UPDATE SET
              yonalish_id=EXCLUDED.yonalish_id,abitur_id=EXCLUDED.abitur_id,familiya=EXCLUDED.familiya,
              ism=EXCLUDED.ism,ota_ism=EXCLUDED.ota_ism,tugilgan_sana=EXCLUDED.tugilgan_sana,
              pasport_seriya=EXCLUDED.pasport_seriya,pasport_raqam=EXCLUDED.pasport_raqam,
              tavsiya_turi=EXCLUDED.tavsiya_turi,talim_shakli=EXCLUDED.talim_shakli,talim_tili=EXCLUDED.talim_tili,
              telefon=EXCLUDED.telefon,ball=EXCLUDED.ball,doimiy_region=EXCLUDED.doimiy_region,
              doimiy_tuman=EXCLUDED.doimiy_tuman,import_batch_id=EXCLUDED.import_batch_id,yangilangan_at=NOW()
            RETURNING (xmax=0) AS inserted"""
        for r in payload:
            program_id = programs[_key(r["yonalish_nomi"])]["id"]
            cur.execute(sql, (batch["universitet_id"], program_id, r["abitur_id"], r["jshshir"], r["jshshir_hash"],
                r["familiya"], r["ism"], r.get("ota_ism"), r.get("tugilgan_sana"), r.get("pasport_seriya"), r.get("pasport_raqam"),
                r.get("tavsiya_turi"), r["talim_shakli"], r["talim_tili"], r.get("telefon"), r.get("ball"),
                r.get("doimiy_region"), r.get("doimiy_tuman"), r.get("maktab_region"), r.get("maktab_tuman"),
                r.get("maktab_turi"), r.get("maktab_nomi"), r.get("tugatgan_yili"), r.get("attestat"), r.get("otm_nomi"), req.batch_id))
            if cur.fetchone()["inserted"]: inserted += 1
            else: updated += 1
        cur.execute("UPDATE universitet_import_batchlar SET holat='committed',commit_at=NOW() WHERE id=%s", (req.batch_id,))
        _audit(cur, batch["universitet_id"], actor, "qabul_import_commit", "import_batch", req.batch_id, {"yangi": inserted, "yangilangan": updated})
        conn.commit(); return {"holat": "import_qilindi", "yangi": inserted, "yangilangan": updated, "jami": inserted + updated}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.get("/qabul/talabalar")
def admission_students(universitet_id: int, q: str = "", yonalish_id: Optional[int] = None, bosqich_min: int = 1,
                       talim_shakli: Optional[str] = None, talim_tili: Optional[str] = None,
                       region: Optional[str] = None, qabul_turi: Optional[str] = None,
                       sort: str = "ball_desc", page: int = 1, page_size: int = 50,
                       token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p(); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); roles = _require_member(cur, user_id, universitet_id)
        if not _has_any(roles, PRIVATE_ROLES): raise HTTPException(status_code=403, detail="Qabul ro'yxatini ko'rish huquqi yo'q")
        scope = _scope_program_ids_for_user(cur, universitet_id, user_id, roles)
        where = ["qt.universitet_id=%s", "qt.qabul_bosqichi>=%s"]; params: list[Any] = [universitet_id, max(1, min(3, bosqich_min))]
        if scope is not None:
            if not scope: return {"talabalar": [], "jami": 0, "sahifa": 1, "sahifa_soni": 0, "hisoblar": {}}
            where.append("qt.yonalish_id=ANY(%s)"); params.append(list(scope))
        if yonalish_id: where.append("qt.yonalish_id=%s"); params.append(yonalish_id)
        if talim_shakli: where.append("qt.talim_shakli=%s"); params.append(talim_shakli)
        if talim_tili: where.append("qt.talim_tili=%s"); params.append(talim_tili)
        if region: where.append("qt.doimiy_region=%s"); params.append(region)
        if qabul_turi == "grant": where.append("qt.tavsiya_turi ILIKE %s"); params.append("%grant%")
        if qabul_turi == "kontrakt": where.append("qt.tavsiya_turi ILIKE %s"); params.append("%kontrakt%")
        if _norm(q): where.append("(qt.familiya ILIKE %s OR qt.ism ILIKE %s OR qt.abitur_id ILIKE %s)"); term = "%" + _norm(q) + "%"; params += [term, term, term]
        order = {"ball_desc": "qt.ball DESC NULLS LAST,qt.familiya", "ball_asc": "qt.ball ASC NULLS LAST,qt.familiya", "name": "qt.familiya,qt.ism", "newest": "qt.id DESC"}.get(sort, "qt.ball DESC NULLS LAST")
        clause = " AND ".join(where)
        cur.execute(f"SELECT COUNT(*) n FROM universitet_qabul_talabalari qt WHERE {clause}", params); total = int(cur.fetchone()["n"])
        page_size = max(10, min(100, page_size)); page = max(1, page); offset = (page - 1) * page_size
        cur.execute(f"""SELECT qt.id,qt.familiya,qt.ism,qt.ota_ism,qt.ball,qt.talim_shakli,qt.talim_tili,qt.tavsiya_turi,
            qt.doimiy_region,qt.doimiy_tuman,qt.qabul_bosqichi,qt.telefon,y.id yonalish_id,y.nomi yonalish_nomi,
            CASE WHEN qt.user_id IS NULL THEN 'yaratilmagan' WHEN xk.ishlatildi THEN 'ulangan' ELSE 'taklif_yuborilgan' END sayt_holati
            FROM universitet_qabul_talabalari qt JOIN universitet_yonalishlari y ON y.id=qt.yonalish_id
            LEFT JOIN LATERAL (SELECT tk.kod_hash FROM universitet_taklif_kodlari tk WHERE tk.qabul_talaba_id=qt.id ORDER BY tk.id DESC LIMIT 1) tk ON TRUE
            LEFT JOIN xodim_kod xk ON xk.kod=tk.kod_hash
            WHERE {clause} ORDER BY {order} LIMIT %s OFFSET %s""", params + [page_size, offset])
        rows = []
        for r in cur.fetchall():
            item = dict(r); item["fish"] = " ".join(x for x in [r["familiya"], r["ism"], r["ota_ism"]] if x); item["telefon_mask"] = _mask_phone(r["telefon"]); item.pop("telefon", None); rows.append(item)
        scope_where = ["universitet_id=%s"]; scope_params: list[Any] = [universitet_id]
        if scope is not None: scope_where.append("yonalish_id=ANY(%s)"); scope_params.append(list(scope))
        sw = " AND ".join(scope_where)
        cur.execute(f"SELECT COUNT(*) jami,COUNT(*) FILTER(WHERE qabul_bosqichi>=2) hujjat,COUNT(*) FILTER(WHERE qabul_bosqichi>=3) sayt FROM universitet_qabul_talabalari WHERE {sw}", scope_params)
        counts = cur.fetchone()
        cur.execute(f"""SELECT
            ARRAY_REMOVE(ARRAY_AGG(DISTINCT talim_shakli ORDER BY talim_shakli),NULL) shakllar,
            ARRAY_REMOVE(ARRAY_AGG(DISTINCT talim_tili ORDER BY talim_tili),NULL) tillar,
            ARRAY_REMOVE(ARRAY_AGG(DISTINCT doimiy_region ORDER BY doimiy_region),NULL) hududlar
            FROM universitet_qabul_talabalari WHERE {sw}""", scope_params)
        filter_options = cur.fetchone()
        return {"talabalar": rows, "jami": total, "sahifa": page, "sahifa_soni": math.ceil(total/page_size) if total else 0,
                "hisoblar": counts, "filtrlar": filter_options}
    finally:
        cur.close(); conn.close()


@router.get("/qabul/talaba/{student_id}")
def admission_detail(student_id: int, universitet_id: int, token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p(); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); roles = _require_member(cur, user_id, universitet_id)
        if not _has_any(roles, PRIVATE_ROLES): raise HTTPException(status_code=403, detail="Shaxsiy ma'lumotni ko'rish huquqi yo'q")
        scope = _scope_program_ids_for_user(cur, universitet_id, user_id, roles)
        cur.execute("""SELECT qt.*,y.nomi yonalish_nomi,f.nomi fakultet_nomi,k.nomi kafedra_nomi
            FROM universitet_qabul_talabalari qt JOIN universitet_yonalishlari y ON y.id=qt.yonalish_id
            JOIN fakultetlar f ON f.id=y.fakultet_id JOIN kafedralar k ON k.id=y.kafedra_id
            WHERE qt.id=%s AND qt.universitet_id=%s""", (student_id, universitet_id)); row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Talaba topilmadi")
        if scope is not None and int(row["yonalish_id"]) not in scope: raise HTTPException(status_code=403, detail="Bu talaba sizning yo'nalishingizga tegishli emas")
        _audit(cur, universitet_id, user_id, "talaba_maxfiy_malumoti_korildi", "qabul_talaba", student_id)
        conn.commit(); result = dict(row); result["fish"] = " ".join(x for x in [row["familiya"],row["ism"],row["ota_ism"]] if x)
        return result
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.patch("/qabul/talaba/{student_id}/bosqich")
def update_stage(student_id: int, req: StageUpdate):
    if req.bosqich not in (1,2,3): raise HTTPException(status_code=400, detail="Bosqich 1, 2 yoki 3 bo'lishi kerak")
    p = _p(); actor = p._jwt_tekshir(req.token); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); cur.execute("SELECT * FROM universitet_qabul_talabalari WHERE id=%s FOR UPDATE", (student_id,)); row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Talaba topilmadi")
        roles = _require_member(cur, actor, row["universitet_id"]); names = _role_names(roles)
        scope = _scope_program_ids_for_user(cur, row["universitet_id"], actor, roles)
        if scope is not None and int(row["yonalish_id"]) not in scope: raise HTTPException(status_code=403, detail="Bu talaba sizga biriktirilmagan")
        if "tyutor" in names and not (names & MARK_DOCUMENT_ROLES):
            if req.bosqich != 3: raise HTTPException(status_code=403, detail="Tyutor faqat o'z yo'nalishidagi talabaning saytga kirishini belgilaydi")
            if int(row["qabul_bosqichi"]) < 2: raise HTTPException(status_code=409, detail="Avval admin hujjat topshirilganini tasdiqlashi kerak")
        elif not (names & MARK_DOCUMENT_ROLES): raise HTTPException(status_code=403, detail="Bosqichni o'zgartirish huquqi yo'q")
        code = None
        if req.bosqich == 3:
            if row["user_id"] is None or int(row["user_id"]) < 0:
                raise HTTPException(status_code=409, detail="Talaba hali sayt akkauntiga ulanmagan. Avval SMS taklif yuboring; kod qabul qilinganda 3-bosqich avtomatik belgilanadi")
            cur.execute("UPDATE universitet_qabul_talabalari SET qabul_bosqichi=3,saytga_kiritilgan_at=COALESCE(saytga_kiritilgan_at,NOW()),yangilangan_at=NOW() WHERE id=%s", (student_id,))
        else:
            cur.execute("""UPDATE universitet_qabul_talabalari SET qabul_bosqichi=%s,
                hujjat_topshirgan_at=CASE WHEN %s>=2 THEN COALESCE(hujjat_topshirgan_at,NOW()) ELSE NULL END,
                yangilangan_at=NOW() WHERE id=%s""", (req.bosqich, req.bosqich, student_id))
        _audit(cur, row["universitet_id"], actor, "qabul_bosqichi", "qabul_talaba", student_id, {"bosqich": req.bosqich})
        conn.commit(); return {"holat": "yangilandi", "bosqich": req.bosqich, "kirish_kodi": code, "kod_muddati": "7 kun" if code else None}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.post("/qabul/talaba/{student_id}/taklif")
def invite_student(student_id: int, req: InviteSend):
    p = _p(); actor = p._jwt_tekshir(req.token); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); cur.execute("SELECT * FROM universitet_qabul_talabalari WHERE id=%s FOR UPDATE", (student_id,)); row = cur.fetchone()
        if not row: raise HTTPException(status_code=404, detail="Talaba topilmadi")
        roles = _require_member(cur, actor, row["universitet_id"]); scope = _scope_program_ids_for_user(cur, row["universitet_id"], actor, roles)
        if not _has_any(roles, MARK_DOCUMENT_ROLES | {"tyutor"}) or (scope is not None and int(row["yonalish_id"]) not in scope):
            raise HTTPException(status_code=403, detail="Taklif yuborish huquqi yo'q")
        if int(row["qabul_bosqichi"]) < 2: raise HTTPException(status_code=409, detail="Hujjat topshirilgani tasdiqlanmagan")
        code = _create_student_invite(cur, dict(row), actor)
        base = getattr(p, "FRONTEND_URL", "").rstrip("/")
        link = f"{base}/?kirish_kodi={code}"
        text = f"Institut ta'lim platformasiga kirish kodi: {code}. Kod 7 kun amal qiladi. Kirish: {link}"
        sent = False
        if req.kanal == "sms":
            if not row["telefon"]: raise HTTPException(status_code=400, detail="Talabada telefon raqami yo'q")
            sent = bool(p._sms_yubor(row["telefon"], text))
        _audit(cur, row["universitet_id"], actor, "talaba_taklif_yaratildi", "qabul_talaba", student_id, {"kanal": req.kanal, "sent": sent})
        conn.commit(); return {"holat": "yuborildi" if sent else "tayyor", "kirish_kodi": code, "havola": link, "sms_matni": text, "sms_yuborildi": sent}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.post("/kirish_kodi_qabul")
def redeem_code(req: RedeemCode):
    p = _p(); user_id = p._jwt_tekshir(req.token); plain, stored = p._xodim_kod_variantlari(req.kirish_kodi)
    conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); p._xodim_kod_jadvali(cur)
        cur.execute("""SELECT tk.*,xk.ishlatildi,(xk.yaratildi>NOW()-INTERVAL '7 days') hali_yangi
            FROM universitet_taklif_kodlari tk JOIN xodim_kod xk ON xk.kod=tk.kod_hash
            WHERE tk.kod_hash IN (%s,%s) FOR UPDATE""", (stored, plain)); invite = cur.fetchone()
        if not invite: raise HTTPException(status_code=400, detail="Kirish kodi noto'g'ri")
        if invite["ishlatildi"]: raise HTTPException(status_code=409, detail="Kirish kodi ishlatilgan")
        if not invite["hali_yangi"]: raise HTTPException(status_code=410, detail="Kirish kodi muddati tugagan")
        placeholder = invite["placeholder_user_id"]
        cur.execute("SELECT universitet_id FROM users WHERE user_id=%s FOR UPDATE", (user_id,))
        account = cur.fetchone()
        if not account: raise HTTPException(status_code=404, detail="Foydalanuvchi akkaunti topilmadi")
        if account["universitet_id"] is not None and int(account["universitet_id"]) != int(invite["universitet_id"]):
            raise HTTPException(status_code=409, detail="Bu akkaunt boshqa institutga biriktirilgan")
        if invite["xodim_rol_id"]:
            cur.execute("UPDATE universitet_xodim_rollari SET user_id=%s WHERE id=%s", (user_id, invite["xodim_rol_id"]))
        if invite["qabul_talaba_id"]:
            cur.execute("UPDATE universitet_qabul_talabalari SET user_id=%s,saytga_kiritilgan_at=NOW(),qabul_bosqichi=3 WHERE id=%s", (user_id, invite["qabul_talaba_id"]))
        p._telefon_jadvallari(cur)
        cur.execute("UPDATE telefon_hisob SET user_id=%s WHERE user_id=%s", (user_id, placeholder))
        cur.execute("UPDATE users SET universitet_id=%s,lavozim=COALESCE(lavozim,%s) WHERE user_id=%s", (invite["universitet_id"], "talaba" if invite["turi"] == "talaba" else "institut_xodimi", user_id))
        cur.execute("UPDATE xodim_kod SET ishlatildi=TRUE WHERE kod=%s", (invite["kod_hash"],))
        cur.execute("UPDATE universitet_taklif_kodlari SET ishlatildi_at=NOW() WHERE id=%s", (invite["id"],))
        _audit(cur, invite["universitet_id"], user_id, "kirish_kodi_qabul", invite["turi"], invite["qabul_talaba_id"] or invite["xodim_rol_id"])
        conn.commit(); return {"holat": "ulandi", "universitet_id": invite["universitet_id"], "turi": invite["turi"]}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@router.get("/talaba/yonalish_katalogi")
def student_directory(universitet_id: int, token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p(); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); roles = _require_member(cur, user_id, universitet_id)
        student_role = next((r for r in roles if r["rol"] == "talaba"), None)
        if not student_role: raise HTTPException(status_code=403, detail="Bu bo'lim talaba uchun")
        program_id = int(student_role["yonalish_id"])
        cur.execute("""SELECT y.id,y.nomi,y.daraja,f.id fakultet_id,f.nomi fakultet_nomi,k.nomi kafedra_nomi
            FROM universitet_yonalishlari y JOIN fakultetlar f ON f.id=y.fakultet_id JOIN kafedralar k ON k.id=y.kafedra_id WHERE y.id=%s""", (program_id,)); program = cur.fetchone()
        cur.execute("""SELECT qt.id,qt.familiya,qt.ism,qt.ota_ism FROM universitet_qabul_talabalari qt
            WHERE qt.universitet_id=%s AND qt.yonalish_id=%s AND qt.qabul_bosqichi>=3 ORDER BY qt.familiya,qt.ism""", (universitet_id, program_id))
        students = [{"id": r["id"], "fish": " ".join(x for x in [r["familiya"],r["ism"],r["ota_ism"]] if x)} for r in cur.fetchall()]
        cur.execute("""SELECT DISTINCT xr.rol,u.full_name FROM universitet_xodim_rollari xr JOIN users u ON u.user_id=xr.user_id
            WHERE xr.universitet_id=%s AND xr.faol=TRUE AND (
              xr.rol IN ('rektor','prorektor','institut_admin') OR xr.fakultet_id=%s OR
              (xr.rol='tyutor' AND EXISTS(SELECT 1 FROM universitet_tyutor_yonalishlari ty WHERE ty.tyutor_user_id=xr.user_id AND ty.yonalish_id=%s AND ty.faol=TRUE)))
            ORDER BY xr.rol,u.full_name""", (universitet_id, program["fakultet_id"], program_id))
        staff = [{"rol": r["rol"], "lavozim_nomi": ROLE_LABELS.get(r["rol"],r["rol"]), "fish": r["full_name"]} for r in cur.fetchall()]
        return {"yonalish": program, "talabalar": students, "masullar": staff}
    finally:
        cur.close(); conn.close()


@router.get("/tyutor/yetarlilik")
def tutor_capacity(universitet_id: int, token: Optional[str] = Query(None, include_in_schema=False), authorization: Optional[str] = Header(None)):
    user_id = _uid(token, authorization); p = _p(); conn = p._db(); cur = conn.cursor()
    try:
        _ensure_schema(cur); _require_member(cur, user_id, universitet_id)
        cur.execute("""SELECT y.id,y.nomi,COUNT(qt.id) FILTER(WHERE qt.talim_shakli='Kunduzgi') kunduzgi_1kurs,
            COUNT(DISTINCT ty.tyutor_user_id) FILTER(WHERE ty.faol=TRUE) tyutor_soni
            FROM universitet_yonalishlari y
            LEFT JOIN universitet_qabul_talabalari qt ON qt.yonalish_id=y.id
            LEFT JOIN universitet_tyutor_yonalishlari ty ON ty.yonalish_id=y.id
            WHERE y.universitet_id=%s AND y.faol=TRUE GROUP BY y.id,y.nomi ORDER BY y.nomi""", (universitet_id,))
        rows=[]
        for r in cur.fetchall():
            needed = math.ceil(int(r["kunduzgi_1kurs"] or 0)/150) if r["kunduzgi_1kurs"] else 0
            item=dict(r); item["tavsiya_etilgan_minimum"] = needed; item["yetarli"] = int(r["tyutor_soni"] or 0) >= needed; rows.append(item)
        return {"yonalishlar": rows, "mezon": "Kunduzgi 1–3-kursning har 120–150 talabasi uchun 1 tyutor"}
    finally:
        cur.close(); conn.close()

"""Excel test shablonlarini xavfsiz aniqlash va rasm xaritalash yordamchilari.

Bu modul bazaga bog'liq emas.  Shu sabab ko'p varaqlı shablon tanlash
qoidalarini FastAPI/PostgreSQL'siz alohida sinash mumkin.
"""

from dataclasses import dataclass
import re
import unicodedata
from typing import Any


REQUIRED_TEST_HEADERS = ("topic_code", "question", "correct_answer")


def canonical_subject_name(value: Any) -> str:
    """Fan nomini varaq/DB solishtiruvi uchun barqaror ko'rinishga keltiradi.

    Excel varaq nomida apostrof, nuqta yoki tire olib tashlangan bo'lishi
    mumkin (masalan ``O'zbek tili`` -> ``Ozbek tili``). Bu yordamchi faqat
    solishtirish uchun ishlaydi; bazadagi asl fan nomini o'zgartirmaydi.
    """
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = text.replace("ё", "е")
    text = re.sub(r"[ʻʼ‘’`´'\u2010-\u2015_-]+", "", text)
    text = re.sub(r"[^0-9a-zа-яёўқғҳ]+", "", text)
    aliases = {
        "math": "matematika",
        "mathematics": "matematika",
        "english": "ingliztili",
        "russian": "rustili",
        "uzbek": "onatili",
    }
    return aliases.get(text, text)


def worksheet_subject_hint(name: Any) -> str | None:
    """``TESTLAR_<fan>`` varag'idan kutilgan fan nomini oladi."""
    raw = str(name or "").strip()
    match = re.match(r"^TESTLAR[ _-]+(.+)$", raw, flags=re.I)
    if not match:
        return None
    hint = match.group(1).strip()
    return hint or None


def subject_matches(expected: Any, actual: Any) -> bool:
    """Excel varaq nomi qisqargan bo'lsa ham fanlarni xavfsiz solishtiradi."""
    left = canonical_subject_name(expected)
    right = canonical_subject_name(actual)
    if not left or not right:
        return False
    if left == right:
        return True
    # Excel varaq nomi 31 belgida kesiladi. Kamida 8 belgilik aniq prefiks
    # bo'lmasa, tasodifiy o'xshash fanlar teng deb olinmaydi.
    return min(len(left), len(right)) >= 8 and (left.startswith(right) or right.startswith(left))


@dataclass
class TestWorksheet:
    worksheet: Any
    name: str
    headers: list[str]


@dataclass
class EmbeddedImages:
    by_row: dict[int, tuple[bytes, str]]
    source_count: int
    errors: list[str]
    warnings: list[str]


def normalize_header(value: Any) -> str:
    """Excel sarlavhasini importda ishlatiladigan barqaror ko'rinishga keltiradi."""
    return str(value).strip().lower() if value is not None else ""


def worksheet_headers(worksheet: Any) -> list[str]:
    return [normalize_header(cell.value) for cell in worksheet[1]]


def row_values_by_header(headers: list[str], row: Any) -> dict[str, Any]:
    """Excel qatorini pozitsiyasini siqmasdan sarlavhalarga bog'laydi.

    Bo'sh kataklar ham o'z indeksida qoladi. Aks holda ``filter`` yoki faqat
    to'ldirilgan kataklardan ro'yxat tuzish keyingi qiymatlarni chapga surib,
    masalan ``difficulty`` qiymatini javob variantiga aylantirib yuboradi.
    """
    return {
        headers[index]: cell.value
        for index, cell in enumerate(row)
        if index < len(headers) and headers[index]
    }


def _metadata_header(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[^0-9a-zа-яёўқғҳ]+", "", text)


def workbook_topic_metadata(workbook: Any) -> dict[str, dict[str, str]]:
    """``MALUMOT`` varag'idagi kod → sinf/fan/mavzu xaritasini oladi.

    Test varag'idagi ``topic_code`` eski bazadagi boshqa fanga to'qnashib
    qolsa, aynan shu nazorat varag'idagi fan va mavzu nomlari kodni xavfsiz
    qayta topish uchun ishlatiladi.  Bu yerda savol matnidan fan taxmin
    qilinmaydi: faqat shablonning o'zidagi aniq metadata qabul qilinadi.
    """
    aliases = {
        "topiccode": "topic_code",
        "sinf": "grade",
        "grade": "grade",
        "fan": "subject_name",
        "subject": "subject_name",
        "chorak": "quarter",
        "quarter": "quarter",
        "bob": "bob_name",
        "bolim": "bolim_name",
        "mavzu": "mavzu_name",
        "kichikmavzu": "kichik_name",
    }
    for worksheet in workbook.worksheets:
        if _metadata_header(worksheet.title) not in {"malumot", "metadata"}:
            continue
        headers = [aliases.get(_metadata_header(cell.value)) for cell in worksheet[1]]
        if "topic_code" not in headers:
            return {}
        result: dict[str, dict[str, str]] = {}
        for row in worksheet.iter_rows(min_row=2):
            values = {
                key: str(row[index].value or "").strip()
                for index, key in enumerate(headers)
                if key and index < len(row)
            }
            code = values.get("topic_code", "")
            if code:
                result[code] = values
        return result
    return {}


def _topic_match_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = text.replace("ё", "е")
    text = re.sub(r"[ʻʼ‘’`´']+", "'", text)
    text = re.sub(r"[^0-9a-zа-яёўқғҳ']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _quarter_match_text(value: Any) -> str:
    text = str(value or "").strip()
    return str(int(text)) if text.isdigit() else _topic_match_text(text)


def resolve_topic_code_for_scope(
    raw_code: Any,
    expected_grade: Any,
    expected_subject: Any,
    database_topics: list[Any],
    workbook_metadata: dict[str, dict[str, str]],
) -> str | None:
    """Kod tanlangan sinf/fanga mos bo'lmasa, mavzu nomidan to'g'rilaydi.

    Qayta xaritalash faqat ``MALUMOT`` varag'idagi bob/bo'lim/mavzu
    ma'lumotlari tanlangan sinf va fan ichida BITTA aniq topic_code'ga olib
    borsa amalga oshadi.  Noaniq holatda ``None`` qaytadi va import to'liq
    to'xtatiladi — noto'g'ri fanga taxminan yozish taqiqlanadi.
    """
    code = str(raw_code or "").strip()
    grade = str(expected_grade or "").strip()
    subject = str(expected_subject or "").strip()

    def value(row: Any, key: str) -> Any:
        try:
            return row[key]
        except (KeyError, TypeError):
            return getattr(row, key, None)

    def in_scope(row: Any) -> bool:
        return (
            str(value(row, "grade") or "").strip().casefold() == grade.casefold()
            and subject_matches(subject, value(row, "subject_name"))
        )

    for row in database_topics:
        if str(value(row, "topic_code") or "").strip() == code and in_scope(row):
            return code

    info = workbook_metadata.get(code)
    if not info:
        return None

    field_weights = (
        ("kichik_name", "kichik_name", 16),
        ("mavzu_name", "mavzu_name", 8),
        ("bolim_name", "bolim_name", 4),
        ("bob_name", "bob_name", 2),
    )
    # Kamida mavzu/kichik mavzu (ular bo'sh bo'lsa bo'lim/bob) aniq mos
    # kelishi shart. Faqat "6-sinf / Matematika"ga qarab birinchi kodni
    # tanlash yana fan ichida mavzularni aralashtirib yuborgan bo'lardi.
    tayanch_fields = [key for key in ("kichik_name", "mavzu_name") if _topic_match_text(info.get(key))]
    if not tayanch_fields:
        tayanch_fields = [key for key in ("bolim_name", "bob_name") if _topic_match_text(info.get(key))]
    if not tayanch_fields:
        return None

    scored: list[tuple[int, str]] = []
    for row in database_topics:
        if not in_scope(row):
            continue
        if not any(
            _topic_match_text(info.get(key))
            and _topic_match_text(info.get(key)) == _topic_match_text(value(row, key))
            for key in tayanch_fields
        ):
            continue
        score = 0
        for source_key, database_key, weight in field_weights:
            source_value = _topic_match_text(info.get(source_key))
            if source_value and source_value == _topic_match_text(value(row, database_key)):
                score += weight
        source_quarter = _quarter_match_text(info.get("quarter"))
        if source_quarter and source_quarter == _quarter_match_text(value(row, "quarter")):
            score += 1
        if score:
            scored.append((score, str(value(row, "topic_code") or "").strip()))

    if not scored:
        return None
    best_score = max(score for score, _ in scored)
    best_codes = sorted({candidate for score, candidate in scored if score == best_score and candidate})
    return best_codes[0] if len(best_codes) == 1 else None


def normalize_difficulty(value: Any) -> str | None:
    """Turli apostroflarda yozilgan o'rta darajani bitta qiymatga keltiradi."""
    if value is None or not str(value).strip():
        return None
    normalized = str(value).strip().lower().replace("‘", "'").replace("’", "'").replace("`", "'")
    aliases = {
        "oson": "oson",
        "o'rta": "o'rta",
        "orta": "o'rta",
        "qiyin": "qiyin",
    }
    return aliases.get(normalized, normalized)


def is_named_test_sheet(name: Any) -> bool:
    normalized = str(name or "").strip().upper()
    return normalized.startswith("TESTLAR")


def discover_test_worksheets(workbook: Any) -> tuple[list[TestWorksheet], list[dict]]:
    """Barcha haqiqiy test varaqlarini topadi.

    Har bir varaq tekshiriladi: ``topic_code``, ``question`` va
    ``correct_answer`` sarlavhalarining uchalasi bor varaq nomidan qat'i
    nazar test varag'i hisoblanadi. Shu sabab qayta nomlangan to'liq varaq
    ``TESTLAR_<fan>`` varaqlari bilan yonma-yon ham import qilinadi.
    ``TESTLAR...`` deb nomlangan, ammo shu ustunlardan biri yetishmagan
    varaq xato diagnostikasiga kiritiladi; to'liq test sarlavhasi yo'q
    boshqa yordamchi varaqlar esa e'tiborsiz qoldiriladi.
    """
    selected: list[TestWorksheet] = []
    skipped: list[dict] = []
    required = set(REQUIRED_TEST_HEADERS)

    # Nomidan qat'i nazar to'liq sarlavha imzosi bor varaqlar olinadi;
    # TESTLAR* nomli chala varaq esa jimgina o'tkazilmay, diagnostika bo'ladi.
    for worksheet in workbook.worksheets:
        headers = worksheet_headers(worksheet)
        missing = sorted(required - set(headers))
        if not missing:
            selected.append(TestWorksheet(worksheet, worksheet.title, headers))
        elif is_named_test_sheet(worksheet.title):
            skipped.append({
                "varaq": worksheet.title,
                "holat": "otkazib_yuborildi",
                "jami_qator": max(0, int(worksheet.max_row or 0) - 1),
                "savolli_qator": 0,
                "saved": 0,
                "duplicates": 0,
                "errors": 0,
                "kod_yoq": 0,
                "excel_rasm_soni": len(getattr(worksheet, "_images", []) or []),
                "qatorga_boglangan_rasm_soni": 0,
                "rasm_biriktirildi": 0,
                "yetishmagan_ustunlar": missing,
            })

    return selected, skipped


def embedded_images_by_row(worksheet: Any, error_limit: int = 5) -> EmbeddedImages:
    """Katakka joylashtirilgan rasmlarni Excel qator raqamiga xaritalaydi."""
    images = list(getattr(worksheet, "_images", []) or [])
    by_row: dict[int, tuple[bytes, str]] = {}
    errors: list[str] = []
    warnings: list[str] = []

    for image in images:
        try:
            zero_based_row = int(image.anchor._from.row)
            image_bytes = image._data()
            image_format = str(getattr(image, "format", None) or "png").lower().lstrip(".")
            excel_row = zero_based_row + 1
            if excel_row in by_row:
                warnings.append(
                    f"{excel_row}-qatorda bir nechta rasm bor; birinchi rasm olindi"
                )
                continue
            by_row[excel_row] = (image_bytes, image_format)
        except Exception as exc:  # openpyxl rasm obyektlari versiyaga qarab farq qiladi
            if len(errors) < error_limit:
                errors.append(f"{type(exc).__name__}: {exc}")

    return EmbeddedImages(
        by_row=by_row,
        source_count=len(images),
        errors=errors,
        warnings=warnings,
    )

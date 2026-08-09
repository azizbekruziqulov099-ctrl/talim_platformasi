"""Excel test shablonlarini xavfsiz aniqlash va rasm xaritalash yordamchilari.

Bu modul bazaga bog'liq emas.  Shu sabab ko'p varaqlı shablon tanlash
qoidalarini FastAPI/PostgreSQL'siz alohida sinash mumkin.
"""

from dataclasses import dataclass
from typing import Any


REQUIRED_TEST_HEADERS = ("topic_code", "question", "correct_answer")


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

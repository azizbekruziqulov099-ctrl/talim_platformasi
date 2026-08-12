"""Excel test shablonlarini xavfsiz aniqlash va rasm xaritalash yordamchilari.

Bu modul bazaga bog'liq emas.  Shu sabab ko'p varaqlı shablon tanlash
qoidalarini FastAPI/PostgreSQL'siz alohida sinash mumkin.
"""

from dataclasses import dataclass
import posixpath
import re
import unicodedata
from typing import Any
from xml.etree import ElementTree
import zipfile


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


_RELATIONSHIP_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PACKAGE_RELATIONSHIP_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
_DRAWING_MAIN_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def _xlsx_relationships_path(part_name: str) -> str:
    directory, filename = posixpath.split(part_name)
    return posixpath.join(directory, "_rels", f"{filename}.rels")


def _xlsx_target_path(source_part: str, target: str) -> str:
    """OOXML relationship targetini ZIP ichidagi barqaror yo'lga aylantiradi."""
    target = str(target or "").replace("\\", "/")
    if target.startswith("/"):
        return posixpath.normpath(target.lstrip("/"))
    return posixpath.normpath(posixpath.join(posixpath.dirname(source_part), target))


def _xlsx_relationship_map(archive: zipfile.ZipFile, source_part: str) -> dict[str, str]:
    rels_path = _xlsx_relationships_path(source_part)
    try:
        root = ElementTree.fromstring(archive.read(rels_path))
    except KeyError:
        return {}
    result: dict[str, str] = {}
    for relationship in root.findall(f"{{{_PACKAGE_RELATIONSHIP_NS}}}Relationship"):
        if str(relationship.attrib.get("TargetMode") or "").casefold() == "external":
            continue
        relationship_id = relationship.attrib.get("Id")
        target = relationship.attrib.get("Target")
        if relationship_id and target:
            result[relationship_id] = _xlsx_target_path(source_part, target)
    return result


def embedded_images_by_sheet_from_xlsx(
    xlsx_source: Any,
    worksheet_names: set[str] | None = None,
    error_limit: int = 5,
) -> dict[str, EmbeddedImages]:
    """Katta XLSX rasmlarini workbook'ni RAM'ga yoymasdan varaqqa/qatorga bog'laydi.

    ``openpyxl`` normal rejimda katta, rasmli faylni to'liq obyektlar daraxtiga
    aylantiradi. Railway xotirasi uchun endpoint workbook'ni ``read_only``
    o'qiydi; bu yordamchi esa faqat OOXML drawing relationshiplarini ko'rib,
    kerakli media fayllarini ZIP'dan bevosita oladi.
    """
    selected_names = {str(name) for name in worksheet_names} if worksheet_names else None
    result: dict[str, EmbeddedImages] = {}

    with zipfile.ZipFile(xlsx_source) as archive:
        workbook_part = "xl/workbook.xml"
        workbook_root = ElementTree.fromstring(archive.read(workbook_part))
        workbook_relationships = _xlsx_relationship_map(archive, workbook_part)

        for sheet in workbook_root.findall(f".//{{{_SPREADSHEET_NS}}}sheet"):
            sheet_name = str(sheet.attrib.get("name") or "")
            if selected_names is not None and sheet_name not in selected_names:
                continue

            by_row: dict[int, tuple[bytes, str]] = {}
            errors: list[str] = []
            warnings: list[str] = []
            source_count = 0
            relationship_id = sheet.attrib.get(f"{{{_RELATIONSHIP_NS}}}id")
            sheet_part = workbook_relationships.get(str(relationship_id or ""))
            if not sheet_part:
                result[sheet_name] = EmbeddedImages(by_row, 0, errors, warnings)
                continue

            try:
                sheet_root = ElementTree.fromstring(archive.read(sheet_part))
                sheet_relationships = _xlsx_relationship_map(archive, sheet_part)
                drawing_ids = [
                    element.attrib.get(f"{{{_RELATIONSHIP_NS}}}id")
                    for element in sheet_root.findall(f".//{{{_SPREADSHEET_NS}}}drawing")
                ]
                for drawing_id in drawing_ids:
                    drawing_part = sheet_relationships.get(str(drawing_id or ""))
                    if not drawing_part:
                        continue
                    drawing_root = ElementTree.fromstring(archive.read(drawing_part))
                    drawing_relationships = _xlsx_relationship_map(archive, drawing_part)
                    anchors = list(drawing_root.findall(f"{{{_DRAWING_NS}}}oneCellAnchor"))
                    anchors += list(drawing_root.findall(f"{{{_DRAWING_NS}}}twoCellAnchor"))
                    source_count += len(drawing_root.findall(f".//{{{_DRAWING_NS}}}pic"))

                    for anchor in anchors:
                        try:
                            row_element = anchor.find(
                                f"{{{_DRAWING_NS}}}from/{{{_DRAWING_NS}}}row"
                            )
                            blip = anchor.find(f".//{{{_DRAWING_MAIN_NS}}}blip")
                            if row_element is None or blip is None:
                                continue
                            image_relationship_id = blip.attrib.get(
                                f"{{{_RELATIONSHIP_NS}}}embed"
                            )
                            media_part = drawing_relationships.get(
                                str(image_relationship_id or "")
                            )
                            if not media_part:
                                continue
                            excel_row = int(row_element.text or "0") + 1
                            if excel_row in by_row:
                                warnings.append(
                                    f"{excel_row}-qatorda bir nechta rasm bor; birinchi rasm olindi"
                                )
                                continue
                            image_format = posixpath.splitext(media_part)[1].lower().lstrip(".") or "png"
                            if image_format == "jpg":
                                image_format = "jpeg"
                            by_row[excel_row] = (archive.read(media_part), image_format)
                        except Exception as exc:
                            if len(errors) < error_limit:
                                errors.append(f"{type(exc).__name__}: {exc}")
            except Exception as exc:
                if len(errors) < error_limit:
                    errors.append(f"{type(exc).__name__}: {exc}")

            result[sheet_name] = EmbeddedImages(
                by_row=by_row,
                source_count=source_count,
                errors=errors,
                warnings=warnings,
            )

    if selected_names:
        for sheet_name in selected_names:
            result.setdefault(sheet_name, EmbeddedImages({}, 0, [], []))
    return result


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


def authoritative_topic_scope(
    workbook_metadata: dict[str, dict[str, str]],
    expected_grade: Any,
    expected_subject: Any = None,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """MALUMOT xaritasini sinf/fan uchun qat'iy va bir qiymatli tekshiradi.

    ``topic_code``ning ikkinchi bo'lagi fan kodidir. Bir sinfda bitta fan
    kodi ikki xil fan nomiga tegishli bo'lsa, Excel ishonchli manba emas va
    import to'xtashi kerak. To'g'ri xarita qaytarilganda esa endpoint shu
    xaritani ``dts_tree`` fan yozuvlari uchun yagona manba sifatida ishlatadi.
    """
    grade = str(expected_grade or "").strip()
    subject = str(expected_subject or "").strip() or None
    selected: dict[str, dict[str, str]] = {}
    errors: list[str] = []
    prefix_subjects: dict[tuple[str, str], tuple[str, str]] = {}

    for raw_code, raw_info in sorted(workbook_metadata.items()):
        code = str(raw_code or "").strip()
        info = {key: str(value or "").strip() for key, value in (raw_info or {}).items()}
        parts = code.split("-")
        if len(parts) < 3 or not parts[0] or not parts[1]:
            errors.append(f"{code or '<bo‘sh kod>'}: topic_code formati noto'g'ri")
            continue

        code_grade, subject_code = parts[0].strip(), parts[1].strip()
        metadata_grade = info.get("grade") or code_grade
        metadata_subject = info.get("subject_name", "")
        if code_grade.casefold() != grade.casefold() or metadata_grade.casefold() != grade.casefold():
            continue
        if not metadata_subject:
            errors.append(f"{code}: MALUMOTda Fan bo'sh")
            continue
        if subject and not subject_matches(subject, metadata_subject):
            continue

        prefix_key = (code_grade.casefold(), subject_code.casefold())
        canonical = canonical_subject_name(metadata_subject)
        previous = prefix_subjects.get(prefix_key)
        if previous and previous[0] != canonical:
            errors.append(
                f"{code_grade}-{subject_code}: bitta fan kodi ikki fanga berilgan "
                f"({previous[1]} va {metadata_subject})"
            )
            continue
        prefix_subjects[prefix_key] = (canonical, metadata_subject)
        selected[code] = {
            **info,
            "topic_code": code,
            "grade": grade,
            "subject_code": subject_code,
            "subject_name": metadata_subject,
        }

    if workbook_metadata and subject and not selected:
        errors.append(f"{grade}-sinf / {subject}: MALUMOTda birorta mos mavzu topilmadi")
    return selected, errors


def _topic_match_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = text.replace("ё", "е")
    text = re.sub(r"[ʻʼ‘’`´']+", "'", text)
    text = re.sub(r"[^0-9a-zа-яёўқғҳ']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _quarter_match_text(value: Any) -> str:
    text = str(value or "").strip()
    return str(int(text)) if text.isdigit() else _topic_match_text(text)


def topic_code_subject_code(value: Any) -> str | None:
    """To'liq topic_code ichidan fan kodini oladi (``6-02-...`` → ``02``)."""
    parts = str(value or "").strip().split("-")
    return parts[1].strip() if len(parts) >= 3 and parts[1].strip() else None


def exact_topic_matches_workbook_metadata(
    database_topic: Any,
    metadata: dict[str, str] | None,
    expected_grade: Any,
    expected_subject: Any,
) -> bool:
    """Exact kodli DTS qatori MALUMOTdagi shu mavzuning o'zi ekanini tekshiradi.

    Eski bazada ``subject_name`` va ``subject_code`` siljib qolgan bo'lishi
    mumkin. Shuning uchun bu tekshiruv fan yorlig'iga qaramaydi: exact
    ``topic_code``, sinf hamda mavzu ierarxiyasining eng aniq mavjud nomi
    mos bo'lsa, workbook metadata fan yorlig'ini tiklash uchun ishonchli
    manba hisoblanadi.
    """
    if not metadata:
        return False

    def value(row: Any, key: str) -> Any:
        try:
            return row[key]
        except (KeyError, TypeError):
            return getattr(row, key, None)

    grade = str(expected_grade or "").strip()
    if str(value(database_topic, "grade") or "").strip().casefold() != grade.casefold():
        return False
    metadata_grade = str(metadata.get("grade") or "").strip()
    if metadata_grade and metadata_grade.casefold() != grade.casefold():
        return False
    if not subject_matches(expected_subject, metadata.get("subject_name")):
        return False

    # Eng aniq to'ldirilgan darajadan boshlaymiz. Kichik/mavzu mavjud
    # bo'lsa, umumiy bob nomining yolg'iz mosligi yetarli hisoblanmaydi.
    for key in ("kichik_name", "mavzu_name", "bolim_name", "bob_name"):
        source = _topic_match_text(metadata.get(key))
        target = _topic_match_text(value(database_topic, key))
        if source:
            return bool(target and source == target)
    return False


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

    # Exact kod va mavzu nomi mos bo'lsa, DBdagi fan yorlig'i siljigan deb
    # qaraymiz. Import endpoint shu qatorning subject_name/subject_code'ini
    # MALUMOT asosida atomar tiklaydi; testni boshqa kodga ko'chirmaymiz.
    for row in database_topics:
        if (
            str(value(row, "topic_code") or "").strip() == code
            and exact_topic_matches_workbook_metadata(
                row, info, grade, subject,
            )
        ):
            return code

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

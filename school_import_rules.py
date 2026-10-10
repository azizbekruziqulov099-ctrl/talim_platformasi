"""FastAPI/DB ga bog'lanmagan V18.23 maktab import qoidalari."""

import hashlib
import os
import re
import secrets
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Optional


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    text = text.replace("ʻ", "'").replace("’", "'").replace("`", "'").replace("‘", "'")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("o'", "o").replace("g'", "g")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def normalize_class_code(value: Any) -> str:
    raw = str(value or "").strip().upper().replace("–", "-").replace("—", "-")
    raw = re.sub(r"\bSINF(I)?\b", "", raw, flags=re.IGNORECASE)
    compact = re.sub(r"[\s_-]+", "", raw)
    match = re.fullmatch(r"(1[01]|[1-9])([A-Z])", compact)
    if not match:
        raise ValueError("Sinf 1-A, 5B yoki 11-D ko'rinishida bo'lishi kerak")
    return f"{int(match.group(1))}-{match.group(2)}"


def split_class_code(value: Any) -> tuple[str, str, str]:
    code = normalize_class_code(value)
    grade, letter = code.split("-", 1)
    return code, grade, letter


def best_subject(value: Any, catalog: list[str]) -> dict[str, Any]:
    raw = str(value or "").strip()
    normalized = normalize_text(raw)
    if not normalized:
        return {"input": raw, "subject": None, "score": 0, "needs_confirmation": False, "alternatives": []}
    exact = {normalize_text(item): item for item in catalog}
    if normalized in exact:
        subject = exact[normalized]
        return {"input": raw, "subject": subject, "score": 100, "needs_confirmation": False, "alternatives": [{"subject": subject, "score": 100}]}
    ranked = sorted(
        ((round(SequenceMatcher(None, normalized, key).ratio() * 100), label) for key, label in exact.items()),
        reverse=True,
    )
    score, label = ranked[0] if ranked else (0, None)
    alternatives = [
        {"subject": candidate_label, "score": candidate_score}
        for candidate_score, candidate_label in ranked[:5]
        if candidate_score >= 72 and candidate_score >= score - 5
    ]
    return {
        "input": raw, "subject": label if score >= 72 else None, "score": score,
        "needs_confirmation": score >= 72 and (score < 90 or len(alternatives) > 1),
        "alternatives": alternatives,
    }


def parse_teaching_assignments(value: Any, catalog: list[str]) -> list[dict[str, Any]]:
    text = str(value or "").strip()
    if not text:
        return []
    result = []
    for part in [part.strip() for part in re.split(r"[;\n]+", text) if part.strip()]:
        class_code = None
        subject_text = part
        match = re.match(r"^\s*(1[01]|[1-9])\s*[-_ ]?\s*([A-Za-z])\s*(?::|-)?\s*(.+?)\s*$", part)
        if match:
            class_code = normalize_class_code(f"{match.group(1)}-{match.group(2)}")
            subject_text = match.group(3)
        result.append({"class_code": class_code, **best_subject(subject_text, catalog)})
    return result


def pin_hash(pin: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt.encode("ascii"), 180_000).hex()
    return f"pbkdf2_sha256$180000${salt}${digest}"


def pin_matches(pin: str, stored: Optional[str]) -> bool:
    if not re.fullmatch(r"\d{4}", str(pin or "")):
        return False
    if not stored:
        fallback = os.getenv("MUASSASA_OCHIRISH_PAROLI", "").strip()
        return bool(re.fullmatch(r"\d{4}", fallback)) and secrets.compare_digest(pin, fallback)
    try:
        algorithm, rounds, salt, expected = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt.encode("ascii"), int(rounds)).hex()
        return secrets.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


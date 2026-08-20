"""SamTM V18.25: admin uchun atomar, bosqichli maktab yaratish API si."""

from __future__ import annotations

import re
import secrets
import string
from typing import Callable, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


_CLASS_RE = re.compile(r"^\s*(1[01]|[1-9])\s*[-–—_ ]?\s*([A-Za-zА-Яа-я])\s*$")


def normalize_class_name(value: str) -> tuple[str, str]:
    """5a, 5-a, 5 A va 5_A ni bir xil 5-A ko'rinishiga keltiradi."""
    match = _CLASS_RE.match(str(value or ""))
    if not match:
        raise ValueError("Sinf 1-A dan 11-Z gacha yozilishi kerak")
    return match.group(1), match.group(2).upper()


def normalize_optional_text(value: Optional[str], max_length: int = 160) -> Optional[str]:
    normalized = " ".join(str(value or "").strip().split())
    if not normalized:
        return None
    return normalized[:max_length]


class AdminSchoolClassInput(BaseModel):
    name: str = Field(min_length=2, max_length=8)
    shift: int = 1
    leader_user_id: Optional[int] = None
    psychologist_user_id: Optional[int] = None
    building: Optional[str] = Field(default=None, max_length=80)
    room: Optional[str] = Field(default=None, max_length=40)


class AdminSchoolCreateInput(BaseModel):
    token: str
    name: str = Field(min_length=2, max_length=160)
    school_number: Optional[str] = Field(default=None, max_length=40)
    region: str = Field(min_length=2, max_length=120)
    district: str = Field(min_length=2, max_length=120)
    shift_count: int = 1
    director_user_id: Optional[int] = None
    classes: list[AdminSchoolClassInput] = Field(min_length=1, max_length=200)


def ensure_school_wizard_columns(cur) -> None:
    cur.execute("ALTER TABLE IF EXISTS maktablar ADD COLUMN IF NOT EXISTS maktab_raqami TEXT")
    cur.execute(
        "ALTER TABLE IF EXISTS maktablar ADD COLUMN IF NOT EXISTS "
        "created_by_user_id BIGINT REFERENCES users(user_id)"
    )
    cur.execute("ALTER TABLE IF EXISTS maktablar ADD COLUMN IF NOT EXISTS holat TEXT NOT NULL DEFAULT 'active'")
    cur.execute("ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS smena INTEGER NOT NULL DEFAULT 1")
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS "
        "psixolog_user_id BIGINT REFERENCES users(user_id)"
    )
    cur.execute("ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS bino TEXT")
    cur.execute("ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS xona TEXT")


def _validate_people(cur, user_ids: set[int]) -> None:
    if not user_ids:
        return
    cur.execute("SELECT user_id FROM users WHERE user_id = ANY(%s)", (list(user_ids),))
    found = {int(row["user_id"]) for row in cur.fetchall()}
    missing = sorted(user_ids - found)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Tanlangan foydalanuvchi topilmadi: {', '.join(map(str, missing[:8]))}",
        )


def create_admin_school_wizard_router(
    admin_verify: Callable[[str], int],
    db_factory: Callable,
) -> APIRouter:
    router = APIRouter(prefix="/api/admin", tags=["admin-school-wizard-v18.25"])

    @router.post("/maktab-yaratish-v2")
    def create_school(payload: AdminSchoolCreateInput):
        admin_user_id = int(admin_verify(payload.token))
        if payload.shift_count not in (1, 2):
            raise HTTPException(status_code=400, detail="Smena soni faqat 1 yoki 2 bo'lishi mumkin")

        school_name = normalize_optional_text(payload.name)
        region = normalize_optional_text(payload.region, 120)
        district = normalize_optional_text(payload.district, 120)
        if not school_name or not region or not district:
            raise HTTPException(status_code=400, detail="Maktab nomi, viloyat va tuman majburiy")

        normalized_classes = []
        seen: set[tuple[str, str]] = set()
        for index, item in enumerate(payload.classes, start=1):
            try:
                grade, letter = normalize_class_name(item.name)
            except ValueError as error:
                raise HTTPException(status_code=400, detail=f"{index}-sinf qatori: {error}") from error
            key = (grade, letter)
            if key in seen:
                raise HTTPException(status_code=400, detail=f"{grade}-{letter} ikki marta kiritilgan")
            seen.add(key)
            shift = 1 if payload.shift_count == 1 else int(item.shift)
            if shift not in (1, 2):
                raise HTTPException(status_code=400, detail=f"{grade}-{letter} uchun smena 1 yoki 2 bo'lishi kerak")
            normalized_classes.append(
                {
                    "grade": grade,
                    "letter": letter,
                    "shift": shift,
                    "leader_user_id": item.leader_user_id,
                    "psychologist_user_id": item.psychologist_user_id,
                    "building": normalize_optional_text(item.building, 80),
                    "room": normalize_optional_text(item.room, 40),
                }
            )

        people = {int(payload.director_user_id)} if payload.director_user_id else set()
        for item in normalized_classes:
            if item["leader_user_id"]:
                people.add(int(item["leader_user_id"]))
            if item["psychologist_user_id"]:
                people.add(int(item["psychologist_user_id"]))

        conn = db_factory()
        cur = conn.cursor()
        try:
            ensure_school_wizard_columns(cur)
            _validate_people(cur, people)
            cur.execute(
                """
                INSERT INTO maktablar(
                    nomi,maktab_raqami,viloyat,tuman,smena_soni,
                    direktor_user_id,pulli,oylik_tolov,created_by_user_id,holat
                ) VALUES(%s,%s,%s,%s,%s,%s,FALSE,0,%s,'active')
                RETURNING id
                """,
                (
                    school_name,
                    normalize_optional_text(payload.school_number, 40),
                    region,
                    district,
                    payload.shift_count,
                    payload.director_user_id,
                    admin_user_id,
                ),
            )
            school_id = int(cur.fetchone()["id"])

            created_classes = []
            for item in normalized_classes:
                join_password = "".join(secrets.choice(string.digits) for _ in range(4))
                cur.execute(
                    """
                    INSERT INTO maktab_sinflari(
                        maktab_id,sinf,harf,smena,rahbar_user_id,
                        psixolog_user_id,bino,xona,qoshilish_paroli
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    RETURNING id
                    """,
                    (
                        school_id,
                        item["grade"],
                        item["letter"],
                        item["shift"],
                        item["leader_user_id"],
                        item["psychologist_user_id"],
                        item["building"],
                        item["room"],
                        join_password,
                    ),
                )
                created_classes.append(
                    {
                        "id": int(cur.fetchone()["id"]),
                        "name": f"{item['grade']}-{item['letter']}",
                        "shift": item["shift"],
                    }
                )

            if payload.director_user_id:
                cur.execute(
                    "UPDATE users SET maktab_id=%s, lavozim='direktor' WHERE user_id=%s",
                    (school_id, payload.director_user_id),
                )
            conn.commit()
            return {
                "status": "created",
                "school": {
                    "id": school_id,
                    "nomi": school_name,
                    "maktab_raqami": normalize_optional_text(payload.school_number, 40),
                    "viloyat": region,
                    "tuman": district,
                    "smena_soni": payload.shift_count,
                    "direktor_user_id": payload.director_user_id,
                    "pulli": False,
                    "oylik_tolov": 0,
                },
                "classes": created_classes,
                "payment_required": False,
            }
        except HTTPException:
            conn.rollback()
            raise
        except Exception as error:
            conn.rollback()
            if "unique" in str(error).lower() or "duplicate" in str(error).lower():
                raise HTTPException(status_code=409, detail="Bir xil sinf ikki marta kiritilgan") from error
            raise
        finally:
            cur.close()
            conn.close()

    return router

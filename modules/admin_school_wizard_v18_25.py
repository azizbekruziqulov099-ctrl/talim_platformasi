"""SamTM V18.33: maktab, xona, sinf, smena va guruhlarni atomar yaratish API si."""

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
    building_key: Optional[str] = Field(default=None, max_length=80)
    room_number: Optional[str] = Field(default=None, max_length=40)
    building: Optional[str] = Field(default=None, max_length=80)
    room: Optional[str] = Field(default=None, max_length=40)
    group_method: str = "none"


class AdminSchoolRoomInput(BaseModel):
    number: str = Field(min_length=1, max_length=40)
    floor: int = 1


class AdminSchoolBuildingInput(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    floors: int = 1
    rooms: list[AdminSchoolRoomInput] = Field(default_factory=list, max_length=1000)


class AdminSchoolCreateInput(BaseModel):
    token: str
    name: str = Field(min_length=2, max_length=160)
    school_number: Optional[str] = Field(default=None, max_length=40)
    region: str = Field(min_length=2, max_length=120)
    district: str = Field(min_length=2, max_length=120)
    shift_count: int = 1
    director_user_id: Optional[int] = None
    buildings: list[AdminSchoolBuildingInput] = Field(default_factory=list, max_length=30)
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
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS "
        "guruhlash_usuli TEXT NOT NULL DEFAULT 'none'"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_sinf_azolari ADD COLUMN IF NOT EXISTS "
        "guruh_raqami SMALLINT"
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS maktab_binolari(
            id BIGSERIAL PRIMARY KEY,
            maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
            nomi TEXT NOT NULL,
            qavat_soni INTEGER NOT NULL DEFAULT 1 CHECK(qavat_soni BETWEEN 1 AND 20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_maktab_binolari_nomi "
        "ON maktab_binolari(maktab_id, LOWER(nomi))"
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS maktab_xonalari(
            id BIGSERIAL PRIMARY KEY,
            bino_id BIGINT NOT NULL REFERENCES maktab_binolari(id) ON DELETE CASCADE,
            xona_raqami TEXT NOT NULL,
            qavat INTEGER NOT NULL DEFAULT 1 CHECK(qavat BETWEEN 1 AND 20),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(bino_id,xona_raqami)
        )
        """
    )
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS "
        "bino_id BIGINT REFERENCES maktab_binolari(id) ON DELETE SET NULL"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS "
        "xona_id BIGINT REFERENCES maktab_xonalari(id) ON DELETE SET NULL"
    )


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
    router = APIRouter(prefix="/api/admin", tags=["admin-school-wizard-v18.28"])

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

        normalized_buildings = []
        building_by_key = {}
        seen_building_names = set()
        for building_index, building in enumerate(payload.buildings, start=1):
            building_key = normalize_optional_text(building.key, 80)
            building_name = normalize_optional_text(building.name, 80)
            floors = int(building.floors)
            if not building_key or not building_name:
                raise HTTPException(status_code=400, detail=f"{building_index}-bino nomini kiriting")
            if floors < 1 or floors > 20:
                raise HTTPException(status_code=400, detail=f"{building_name}: qavat soni 1 dan 20 gacha bo'lishi kerak")
            if building_key in building_by_key:
                raise HTTPException(status_code=400, detail="Bir xil bino kaliti ikki marta yuborilgan")
            normalized_name_key = building_name.casefold()
            if normalized_name_key in seen_building_names:
                raise HTTPException(status_code=400, detail=f"{building_name} ikki marta kiritilgan")
            seen_building_names.add(normalized_name_key)

            rooms = []
            seen_rooms = set()
            for room in building.rooms:
                room_number = normalize_optional_text(room.number, 40)
                floor = int(room.floor)
                if not room_number:
                    raise HTTPException(status_code=400, detail=f"{building_name}: xona raqami bo'sh")
                if floor < 1 or floor > floors:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{building_name}, {room_number}-xona: qavat 1 dan {floors} gacha bo'lishi kerak",
                    )
                room_key = room_number.casefold()
                if room_key in seen_rooms:
                    raise HTTPException(status_code=400, detail=f"{building_name}: {room_number}-xona ikki marta kiritilgan")
                seen_rooms.add(room_key)
                rooms.append({"number": room_number, "floor": floor})

            normalized = {
                "key": building_key,
                "name": building_name,
                "floors": floors,
                "rooms": rooms,
                "room_numbers": {room["number"].casefold() for room in rooms},
            }
            normalized_buildings.append(normalized)
            building_by_key[building_key] = normalized

        normalized_classes = []
        seen: set[tuple[str, str]] = set()
        occupied_room_shifts: set[tuple[int, str, str]] = set()
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

            group_method = str(item.group_method or "none").strip().lower()
            if group_method not in ("none", "gender", "alphabet"):
                raise HTTPException(
                    status_code=400,
                    detail=f"{grade}-{letter} uchun guruhlash usuli noto'g'ri",
                )

            building_key = normalize_optional_text(item.building_key, 80)
            room_number = normalize_optional_text(item.room_number, 40)
            building_name = normalize_optional_text(item.building, 80)
            if room_number and not building_key:
                raise HTTPException(status_code=400, detail=f"{grade}-{letter}: xona uchun binoni tanlang")
            if building_key:
                selected_building = building_by_key.get(building_key)
                if not selected_building:
                    raise HTTPException(status_code=400, detail=f"{grade}-{letter}: tanlangan bino topilmadi")
                building_name = selected_building["name"]
                if room_number and room_number.casefold() not in selected_building["room_numbers"]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{grade}-{letter}: {building_name}dagi {room_number}-xona topilmadi",
                    )
                if room_number:
                    room_shift_key = (shift, building_key, room_number.casefold())
                    if room_shift_key in occupied_room_shifts:
                        raise HTTPException(
                            status_code=400,
                            detail=f"{room_number}-xona {shift}-smenada boshqa sinfga allaqachon biriktirilgan",
                        )
                    occupied_room_shifts.add(room_shift_key)
            normalized_classes.append(
                {
                    "grade": grade,
                    "letter": letter,
                    "shift": shift,
                    "leader_user_id": item.leader_user_id,
                    "psychologist_user_id": item.psychologist_user_id,
                    "building_key": building_key,
                    "room_number": room_number,
                    "building": building_name,
                    "room": room_number or normalize_optional_text(item.room, 40),
                    "group_method": group_method,
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

            building_ids = {}
            room_ids = {}
            created_buildings = []
            for building in normalized_buildings:
                cur.execute(
                    """
                    INSERT INTO maktab_binolari(maktab_id,nomi,qavat_soni)
                    VALUES(%s,%s,%s) RETURNING id
                    """,
                    (school_id, building["name"], building["floors"]),
                )
                building_id = int(cur.fetchone()["id"])
                building_ids[building["key"]] = building_id
                created_rooms = []
                for room in building["rooms"]:
                    cur.execute(
                        """
                        INSERT INTO maktab_xonalari(bino_id,xona_raqami,qavat)
                        VALUES(%s,%s,%s) RETURNING id
                        """,
                        (building_id, room["number"], room["floor"]),
                    )
                    room_id = int(cur.fetchone()["id"])
                    room_ids[(building["key"], room["number"].casefold())] = room_id
                    created_rooms.append({"id": room_id, "number": room["number"], "floor": room["floor"]})
                created_buildings.append(
                    {
                        "id": building_id,
                        "key": building["key"],
                        "name": building["name"],
                        "floors": building["floors"],
                        "rooms": created_rooms,
                    }
                )

            created_classes = []
            for item in normalized_classes:
                join_password = "".join(secrets.choice(string.digits) for _ in range(4))
                building_id = building_ids.get(item["building_key"]) if item["building_key"] else None
                room_id = (
                    room_ids.get((item["building_key"], item["room_number"].casefold()))
                    if item["building_key"] and item["room_number"]
                    else None
                )
                cur.execute(
                    """
                    INSERT INTO maktab_sinflari(
                        maktab_id,sinf,harf,smena,rahbar_user_id,
                        psixolog_user_id,bino,xona,bino_id,xona_id,qoshilish_paroli,
                        guruhlash_usuli
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
                        building_id,
                        room_id,
                        join_password,
                        item["group_method"],
                    ),
                )
                created_classes.append(
                    {
                        "id": int(cur.fetchone()["id"]),
                        "name": f"{item['grade']}-{item['letter']}",
                        "shift": item["shift"],
                        "building": item["building"],
                        "room": item["room"],
                        "group_method": item["group_method"],
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
                "buildings": created_buildings,
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

"""SamTM V18.33: maktab, xona, sinf, smena va guruhlarni atomar yaratish API si."""

from __future__ import annotations

import re
import secrets
import string
from typing import Callable, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


_CLASS_RE = re.compile(r"^\s*(1[01]|[1-9])\s*[-–—_ ]?\s*([A-Za-zА-Яа-я])\s*$")
_ROOM_TYPES = {"classroom", "reserve", "sport", "non_teaching"}


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


class AdminSchoolGroupSystemInput(BaseModel):
    type: str
    name: Optional[str] = Field(default=None, max_length=80)


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
    group_count: int = 2
    group_systems: list[AdminSchoolGroupSystemInput] = Field(default_factory=list, max_length=3)


class AdminSchoolRoomInput(BaseModel):
    number: str = Field(min_length=1, max_length=40)
    floor: int = 1
    room_type: str = "classroom"
    is_additional: bool = False


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
        "ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS "
        "guruh_soni SMALLINT NOT NULL DEFAULT 2"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_sinf_azolari ADD COLUMN IF NOT EXISTS "
        "guruh_raqami SMALLINT"
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS maktab_sinf_guruh_tizimlari(
            id BIGSERIAL PRIMARY KEY,
            sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
            turi TEXT NOT NULL CHECK(turi IN ('gender','alphabet','manual')),
            nomi TEXT NOT NULL,
            fanlar TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
            faol BOOLEAN NOT NULL DEFAULT TRUE,
            yaratilgan_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
            yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(sinf_id,turi)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS maktab_sinf_guruh_azolari(
            tizim_id BIGINT NOT NULL REFERENCES maktab_sinf_guruh_tizimlari(id) ON DELETE CASCADE,
            user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            guruh_kaliti TEXT NOT NULL,
            guruh_nomi TEXT NOT NULL,
            yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(tizim_id,user_id)
        )
        """
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
        "ALTER TABLE IF EXISTS maktab_xonalari ADD COLUMN IF NOT EXISTS "
        "xona_turi TEXT NOT NULL DEFAULT 'classroom'"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_xonalari ADD COLUMN IF NOT EXISTS "
        "darsga_yaroqli BOOLEAN NOT NULL DEFAULT TRUE"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_xonalari ADD COLUMN IF NOT EXISTS "
        "qoshimcha_xona BOOLEAN NOT NULL DEFAULT FALSE"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS "
        "bino_id BIGINT REFERENCES maktab_binolari(id) ON DELETE SET NULL"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS maktab_sinflari ADD COLUMN IF NOT EXISTS "
        "xona_id BIGINT REFERENCES maktab_xonalari(id) ON DELETE SET NULL"
    )
    # Oldingi versiyada qo'shimcha xonalar nomiga qarab sport/reserve/non_teaching
    # deb belgilangan. Ularni yangi qat'iy qoidaga bir marta moslaymiz.
    cur.execute(
        """
        UPDATE maktab_xonalari
        SET qoshimcha_xona=TRUE,
            xona_turi='non_teaching',
            darsga_yaroqli=FALSE
        WHERE qoshimcha_xona=TRUE OR xona_turi<>'classroom'
        """
    )
    cur.execute(
        """
        UPDATE maktab_sinflari s
        SET xona_id=NULL
        FROM maktab_xonalari x
        WHERE s.xona_id=x.id AND x.qoshimcha_xona=TRUE
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS aqlli_xonalar_v2(
            id BIGSERIAL PRIMARY KEY,
            maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
            nomi TEXT NOT NULL,
            turi TEXT NOT NULL DEFAULT 'oddiy',
            sigim INTEGER,
            faol BOOLEAN NOT NULL DEFAULT TRUE,
            UNIQUE(maktab_id,nomi)
        )
        """
    )
    cur.execute(
        "ALTER TABLE IF EXISTS aqlli_xonalar_v2 ADD COLUMN IF NOT EXISTS "
        "manba_xona_id BIGINT REFERENCES maktab_xonalari(id) ON DELETE SET NULL"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS aqlli_xonalar_v2 ADD COLUMN IF NOT EXISTS "
        "bino_id BIGINT REFERENCES maktab_binolari(id) ON DELETE SET NULL"
    )
    cur.execute(
        "ALTER TABLE IF EXISTS aqlli_xonalar_v2 ADD COLUMN IF NOT EXISTS "
        "darsga_yaroqli BOOLEAN NOT NULL DEFAULT TRUE"
    )
    cur.execute(
        """
        UPDATE aqlli_xonalar_v2 a
        SET faol=FALSE,darsga_yaroqli=FALSE
        FROM maktab_xonalari x
        WHERE a.manba_xona_id=x.id AND x.qoshimcha_xona=TRUE
        """
    )
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_aqlli_xonalar_manba_xona "
        "ON aqlli_xonalar_v2(manba_xona_id) WHERE manba_xona_id IS NOT NULL"
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

    @router.get("/maktab-resurslari")
    def school_resources(token: str, maktab_id: int):
        """Mavjud maktab sinflariga bino va xonani shu sahifadan biriktirish katalogi."""
        admin_verify(token)
        conn = db_factory()
        cur = conn.cursor()
        try:
            ensure_school_wizard_columns(cur)
            cur.execute("SELECT id FROM maktablar WHERE id=%s", (maktab_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Maktab topilmadi")
            cur.execute(
                """
                SELECT b.id,b.nomi,b.qavat_soni,
                       x.id AS xona_id,x.xona_raqami,x.qavat,
                       x.xona_turi,x.darsga_yaroqli,x.qoshimcha_xona
                FROM maktab_binolari b
                LEFT JOIN maktab_xonalari x ON x.bino_id=b.id
                WHERE b.maktab_id=%s
                ORDER BY LOWER(b.nomi),x.qavat,LOWER(x.xona_raqami)
                """,
                (maktab_id,),
            )
            buildings = {}
            for row in cur.fetchall():
                building = buildings.setdefault(
                    int(row["id"]),
                    {
                        "id": int(row["id"]),
                        "name": row["nomi"],
                        "floors": int(row["qavat_soni"] or 1),
                        "rooms": [],
                    },
                )
                if row["xona_id"] is not None:
                    building["rooms"].append(
                        {
                            "id": int(row["xona_id"]),
                            "number": row["xona_raqami"],
                            "floor": int(row["qavat"] or 1),
                            "room_type": row.get("xona_turi") or "classroom",
                            "teaching_enabled": bool(row.get("darsga_yaroqli", True)),
                            "is_additional": bool(row.get("qoshimcha_xona", False)),
                        }
                    )
            conn.commit()
            return {"buildings": list(buildings.values())}
        except HTTPException:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

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
                is_additional = bool(room.is_additional)
                # Qo'shimcha maydonga vergul bilan yozilgan har qanday xona
                # nomidan qat'i nazar darsga yaroqsiz. Standart xona esa dars xonasi.
                room_type = "non_teaching" if is_additional else "classroom"
                if not room_number:
                    raise HTTPException(status_code=400, detail=f"{building_name}: xona raqami bo'sh")
                if room_type not in _ROOM_TYPES:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{building_name}, {room_number}: xona turi noto'g'ri",
                    )
                if floor < 1 or floor > floors:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{building_name}, {room_number}-xona: qavat 1 dan {floors} gacha bo'lishi kerak",
                    )
                room_key = room_number.casefold()
                if room_key in seen_rooms:
                    raise HTTPException(status_code=400, detail=f"{building_name}: {room_number}-xona ikki marta kiritilgan")
                seen_rooms.add(room_key)
                rooms.append({
                    "number": room_number,
                    "floor": floor,
                    "room_type": room_type,
                    "teaching_enabled": not is_additional,
                    "is_additional": is_additional,
                })

            normalized = {
                "key": building_key,
                "name": building_name,
                "floors": floors,
                "rooms": rooms,
                "room_numbers": {room["number"].casefold() for room in rooms},
                "room_by_number": {room["number"].casefold(): room for room in rooms},
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

            raw_group_systems = list(item.group_systems or [])
            legacy_group_method = str(item.group_method or "none").strip().lower()
            if not raw_group_systems and legacy_group_method != "none":
                raw_group_systems = [
                    AdminSchoolGroupSystemInput(type=legacy_group_method, name=None)
                ]
            group_systems = []
            seen_group_types = set()
            default_group_names = {
                "alphabet": "Alifbo bo'yicha 1/2-guruh",
                "gender": "O'g'il / qiz",
                "manual": "Boshqa guruh turi",
            }
            for group_system in raw_group_systems:
                group_type = str(group_system.type or "").strip().lower()
                if group_type not in default_group_names:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{grade}-{letter} uchun guruhlash turi noto'g'ri",
                    )
                if group_type in seen_group_types:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{grade}-{letter} uchun {group_type} turi ikki marta qo'shilgan",
                    )
                group_name = normalize_optional_text(group_system.name, 80) or default_group_names[group_type]
                if group_type == "manual" and len(group_name) < 2:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{grade}-{letter} uchun boshqa guruh turi nomini yozing",
                    )
                seen_group_types.add(group_type)
                group_systems.append({"type": group_type, "name": group_name})
            group_method = (
                "none" if not group_systems
                else group_systems[0]["type"] if len(group_systems) == 1
                else "manual"
            )
            group_count = 1 if not group_systems else 2

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
                    selected_room = selected_building["room_by_number"][room_number.casefold()]
                    if selected_room["room_type"] != "classroom":
                        raise HTTPException(
                            status_code=400,
                            detail=f"{grade}-{letter}: doimiy sinf xonasi faqat oddiy dars xonasi bo'lishi kerak",
                        )
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
                    "group_count": group_count,
                    "group_systems": group_systems,
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
                        INSERT INTO maktab_xonalari(
                            bino_id,xona_raqami,qavat,xona_turi,darsga_yaroqli,
                            qoshimcha_xona
                        ) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id
                        """,
                        (
                            building_id, room["number"], room["floor"],
                            room["room_type"], room["teaching_enabled"],
                            room["is_additional"],
                        ),
                    )
                    room_id = int(cur.fetchone()["id"])
                    room_ids[(building["key"], room["number"].casefold())] = room_id
                    if room["room_type"] in {"sport", "reserve"}:
                        smart_name = f"{building['name']} · {room['number']}"
                        cur.execute(
                            """
                            INSERT INTO aqlli_xonalar_v2(
                                maktab_id,nomi,turi,sigim,faol,
                                manba_xona_id,bino_id,darsga_yaroqli
                            ) VALUES(%s,%s,%s,NULL,TRUE,%s,%s,TRUE)
                            ON CONFLICT(maktab_id,nomi) DO UPDATE SET
                                turi=EXCLUDED.turi,faol=TRUE,
                                manba_xona_id=EXCLUDED.manba_xona_id,
                                bino_id=EXCLUDED.bino_id,darsga_yaroqli=TRUE
                            """,
                            (
                                school_id, smart_name, room["room_type"],
                                room_id, building_id,
                            ),
                        )
                    created_rooms.append({
                        "id": room_id,
                        "number": room["number"],
                        "floor": room["floor"],
                        "room_type": room["room_type"],
                        "teaching_enabled": room["teaching_enabled"],
                        "is_additional": room["is_additional"],
                    })
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
                        guruhlash_usuli,guruh_soni
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
                        item["group_count"],
                    ),
                )
                class_id = int(cur.fetchone()["id"])
                for group_system in item["group_systems"]:
                    cur.execute(
                        """
                        INSERT INTO maktab_sinf_guruh_tizimlari(
                            sinf_id,turi,nomi,fanlar,faol,yaratilgan_by,yangilangan_at
                        ) VALUES(%s,%s,%s,ARRAY[]::TEXT[],TRUE,%s,NOW())
                        """,
                        (
                            class_id,
                            group_system["type"],
                            group_system["name"],
                            admin_user_id,
                        ),
                    )
                created_classes.append(
                    {
                        "id": class_id,
                        "name": f"{item['grade']}-{item['letter']}",
                        "shift": item["shift"],
                        "building": item["building"],
                        "room": item["room"],
                        "group_method": item["group_method"],
                        "group_count": item["group_count"],
                        "group_systems": item["group_systems"],
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

"""Claim an administrator-issued invitation into the current real account.

This is membership transfer, never password login or merging two real accounts.
Every write, including consuming the invitation, uses the same transaction.
"""
from __future__ import annotations

import re


class MembershipError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def normalize_code(value):
    # Office/PDF copies commonly contain spaces or typographical hyphens.
    text = re.sub(r"[\s\-–—\u200b\ufeff]+", "", str(value or "")).upper()
    if not re.fullmatch(r"[A-Z0-9]{12}", text):
        raise MembershipError("Muassasa uchun berilgan 12 belgili shaxsiy kodni kiriting. 4 xonali sinf paroli alohida kiritiladi.")
    return text


INSTITUTIONS = {
    "maktab": ("maktab_id", "maktablar"),
    "markaz": ("markaz_id", "oquv_markazlari"),
    "bogcha": ("bogcha_id", "bogchalar"),
    "universitet": ("universitet_id", "universitetlar"),
}

IDENTITIES = {
    "google_hisob": "user_id", "kabutar_telegram_identity": "user_id",
    "kabutar_auth_password": "user_id", "kabutar_auth_sessions": "user_id",
    "kabutar_auth_security": "user_id", "user_accounts": "uid",
}
LEGACY_PHONE_TABLES = {"telefon_hisob", "telefon_tasdiq_kod"}


def has_login_identity(cur, user_id, columns=None):
    # Google registrations also use negative IDs. A sign is not proof that a
    # row is an unclaimed import placeholder. telefon_hisob alone is not proof:
    # administrators populated it before the invited person ever signed in.
    # A consumed historical SMS verification does prove prior account use.
    if columns is None:
        columns = _available_columns(cur, set(IDENTITIES) | LEGACY_PHONE_TABLES)
    parts, values = [], []
    for table, field in IDENTITIES.items():
        if field in columns.get(table, set()):
            parts.append(f'SELECT 1 FROM "{table}" WHERE "{field}"=%s')
            values.append(user_id)
    if {"telefon", "user_id"} <= columns.get("telefon_hisob", set()) and {"telefon", "ishlatildi"} <= columns.get("telefon_tasdiq_kod", set()):
        parts.append("""SELECT 1 FROM telefon_hisob th JOIN telefon_tasdiq_kod tk
                        ON tk.telefon=th.telefon WHERE th.user_id=%s AND tk.ishlatildi=TRUE""")
        values.append(user_id)
    if not parts:
        return False
    cur.execute(" UNION ALL ".join(parts) + " LIMIT 1", tuple(values))
    return cur.fetchone() is not None

# Only educational membership/assignment references are moved. Session,
# Telegram, Google, credentials and audit actor columns are deliberately absent.
REFERENCES = {
    "maktab": {
        "maktablar": ("direktor_user_id",),
        "maktab_sinflari": ("rahbar_user_id", "psixolog_user_id", "psychologist_user_id"),
        "maktab_xodim_sinflari": ("user_id",),
        "maktab_dars_birikmalari": ("user_id",),
        "maktab_sinf_azolari": ("user_id",),
        "maktab_sinf_guruh_azolari": ("user_id",),
        "school_staff_profiles": ("user_id",),
        "school_person_profiles": ("user_id",),
        "school_person_aliases": ("user_id",),
        "school_teacher_assignments": ("teacher_user_id",),
        "parent_child": ("parent_id", "child_id"),
        "dars_jadvali": ("oqituvchi_user_id",),
        "dars_monitoring_baholari": ("oqituvchi_user_id", "oquvchi_user_id"),
        "davomat": ("user_id",),
        "xodim_davomati": ("user_id",),
        "aqlli_holatlar": ("oquvchi_user_id",),
        "aqlli_oqituvchi_vaqti_v2": ("user_id",),
        "aqlli_oqituvchi_qoidalari_v2": ("user_id",),
        "aqlli_sinf_fan_yuklamalari_v2": ("asosiy_oqituvchi_user_id",),
        "aqlli_guruh_sozlamalari_v2": ("oqituvchi_user_id",),
        "aqlli_jadval_slotlari_v2": ("oqituvchi_user_id",),
        "aqlli_mavzu_taqvimi_v2": ("oqituvchi_user_id",),
        "aqlli_metod_qolda_override_v242": ("user_id",),
    },
    "markaz": {"oquv_markazlari": ("direktor_user_id",), "togaraklar": ("teacher_id",)},
    "bogcha": {"bogchalar": ("direktor_user_id",), "bogcha_guruhlari": ("opa_user_id",)},
    "universitet": {
        "universitetlar": ("rektor_user_id",),
        "fakultetlar": ("dekan_user_id",),
        "kafedralar": ("mudir_user_id",),
        "universitet_guruhlari": ("rahbar_user_id",),
        "universitet_tyutor_yonalishlari": ("tyutor_user_id",),
        "universitet_guruh_azolari": ("user_id",),
    },
}


def _available_columns(cur, tables):
    cur.execute("""SELECT table_name,column_name FROM information_schema.columns
                   WHERE table_schema='public' AND table_name=ANY(%s)""", (list(tables),))
    result = {}
    for row in cur.fetchall():
        result.setdefault(row["table_name"], set()).add(row["column_name"])
    return result


def transfer_references(cur, kind, placeholder_id, user_id, columns):
    if placeholder_id >= 0 or user_id == 0 or placeholder_id == user_id:
        raise MembershipError("Haqiqiy akkauntlarni kirish kodi bilan birlashtirib bo'lmaydi.", 409)
    for table, fields in REFERENCES[kind].items():
        for field in fields:
            if field in columns.get(table, set()):
                # Identifier interpolation comes exclusively from the allowlist.
                # A unique conflict rolls the entire claim back, never drops data.
                cur.execute(f'UPDATE "{table}" SET "{field}"=%s WHERE "{field}"=%s', (user_id, placeholder_id))


def _university_invite(cur, code, columns):
    if "universitet_taklif_kodlari" not in columns:
        return None
    cur.execute("SELECT * FROM universitet_taklif_kodlari WHERE kod_hash=%s FOR UPDATE", (code,))
    return cur.fetchone()


def _claim_university(cur, invite, placeholder, user_id, institute):
    university_id = invite["universitet_id"]
    institute._require_active_university_source(cur, university_id)
    if invite.get("ishlatildi_at") is not None:
        raise MembershipError("Bu institut taklifi avval ishlatilgan. Adminga murojaat qiling.", 409)
    if int(invite["placeholder_user_id"]) != int(placeholder["user_id"]):
        raise MembershipError("Kirish kodi bilan muassasa yozuvi mos emas. Adminga murojaat qiling.", 409)
    if invite["turi"] == "xodim" and invite.get("xodim_rol_id") and not invite.get("qabul_talaba_id"):
        cur.execute("""SELECT * FROM universitet_xodim_rollari
                       WHERE id=%s AND universitet_id=%s FOR UPDATE""", (invite["xodim_rol_id"], university_id))
        target = cur.fetchone()
        if not target or not target["faol"] or int(target["user_id"]) != int(placeholder["user_id"]):
            raise MembershipError("Bu xodim taklifi bekor qilingan yoki boshqa akkauntga ulangan.", 409)
        # Reject archived structural scopes before moving an administrative role.
        for field, table in (("fakultet_id", "fakultetlar"), ("kafedra_id", "kafedralar"), ("yonalish_id", "universitet_yonalishlari")):
            if target.get(field):
                cur.execute(f"SELECT faol FROM {table} WHERE id=%s", (target[field],))
                scope = cur.fetchone()
                if not scope or not scope["faol"]:
                    raise MembershipError("Taklifdagi fakultet, kafedra yoki yo'nalish arxivlangan.", 410)
        cur.execute("UPDATE universitet_xodim_rollari SET user_id=%s WHERE id=%s AND user_id=%s", (user_id, target["id"], placeholder["user_id"]))
        institute._sync_legacy_leader(cur, university_id, user_id, target["rol"], target.get("fakultet_id"), target.get("kafedra_id"))
        return target["rol"], "oqituvchi"
    if invite["turi"] == "talaba" and invite.get("qabul_talaba_id") and not invite.get("xodim_rol_id"):
        cur.execute("""SELECT qt.*, y.faol AS yonalish_faol FROM universitet_qabul_talabalari qt
                       JOIN universitet_yonalishlari y ON y.id=qt.yonalish_id
                       WHERE qt.id=%s AND qt.universitet_id=%s FOR UPDATE OF qt""", (invite["qabul_talaba_id"], university_id))
        target = cur.fetchone()
        if not target or not target["yonalish_faol"] or int(target["user_id"] or 0) != int(placeholder["user_id"]):
            raise MembershipError("Bu talaba taklifi bekor qilingan yoki boshqa akkauntga ulangan.", 409)
        cur.execute("""SELECT id FROM universitet_qabul_talabalari
                       WHERE universitet_id=%s AND user_id=%s AND id<>%s""", (university_id, user_id, target["id"]))
        if cur.fetchone():
            raise MembershipError("Hisobingiz boshqa talaba yozuviga ulangan. Adminga murojaat qiling.", 409)
        cur.execute("""UPDATE universitet_qabul_talabalari SET user_id=%s,
                       bazaga_kiritilgan_at=COALESCE(bazaga_kiritilgan_at,NOW()),
                       saytga_kiritilgan_at=NOW(),birinchi_kirish_at=NOW(),
                       qabul_bosqichi=4,yangilangan_at=NOW() WHERE id=%s""", (user_id, target["id"]))
        return "talaba", "oquvchi"
    raise MembershipError("Taklif turi noto'g'ri. Admindan yangi kod so'rang.", 409)


def _claim_legacy_university(cur, placeholder, user_id, institute):
    """Old Admin → Institutions also issues codes, without invitation metadata."""
    university_id = placeholder["universitet_id"]
    cur.execute("""SELECT id FROM universitet_xodim_rollari
                   WHERE universitet_id=%s AND user_id=%s AND faol=TRUE
                   ORDER BY id FOR UPDATE""", (university_id, placeholder["user_id"]))
    role_ids = [row["id"] for row in cur.fetchall()]
    if not role_ids:
        raise MembershipError("Bu eski institut kodi uchun lavozim topilmadi. Administrator yangi taklif bersin.", 409)
    result = None
    for role_id in role_ids:
        claimed = _claim_university(cur, {
            "universitet_id": university_id, "placeholder_user_id": placeholder["user_id"],
            "turi": "xodim", "xodim_rol_id": role_id,
        }, placeholder, user_id, institute)
        if result is None or claimed[0] == placeholder.get("lavozim"):
            result = claimed
    return result


def _parent_school_ids(cur, person_id, columns):
    parts, values = [], []
    if {"user_id", "school_id", "person_type"} <= columns.get("school_person_profiles", set()):
        parts.append("SELECT school_id FROM school_person_profiles WHERE user_id=%s AND person_type='parent'")
        values.append(person_id)
    if {"parent_id", "child_id"} <= columns.get("parent_child", set()):
        parts.append("SELECT child.maktab_id AS school_id FROM parent_child pc JOIN users child ON child.user_id=pc.child_id WHERE pc.parent_id=%s AND child.maktab_id IS NOT NULL")
        values.append(person_id)
    if not parts:
        return set()
    cur.execute(" UNION ".join(parts), tuple(values))
    return {int(row["school_id"]) for row in cur.fetchall() if row.get("school_id")}


def search_school_people(platform, actor_id, school_id, name):
    """Bounded, school-scoped identity lookup; never returns credentials/contact."""
    name = str(name or "").strip()
    if not isinstance(school_id, int) or isinstance(school_id, bool) or school_id <= 0 or not 2 <= len(name) <= 100:
        raise MembershipError("Maktabni tanlang va ismning 2–100 belgisini yozing.", 422)
    conn = platform._db()
    cur = conn.cursor()
    try:
        if not platform._maktab_boshqaruvchi_mi(cur, actor_id, school_id):
            raise MembershipError("Faqat shu maktab rahbariyati yoki administrator shaxslarni qidira oladi.", 403)
        if platform.institution_is_archived(cur, "maktab", school_id):
            raise MembershipError("Maktab arxivlangan.", 410)
        columns = _available_columns(cur, {"school_person_profiles", "parent_child"})
        scopes, values = ["u.maktab_id=%s"], [school_id]
        if {"user_id", "school_id", "person_type"} <= columns.get("school_person_profiles", set()):
            scopes.append("(u.role='ota-ona' AND EXISTS (SELECT 1 FROM school_person_profiles sp WHERE sp.user_id=u.user_id AND sp.school_id=%s AND sp.person_type='parent'))")
            values.append(school_id)
        if {"parent_id", "child_id"} <= columns.get("parent_child", set()):
            scopes.append("(u.role='ota-ona' AND EXISTS (SELECT 1 FROM parent_child pc JOIN users child ON child.user_id=pc.child_id WHERE pc.parent_id=u.user_id AND child.maktab_id=%s))")
            values.append(school_id)
        # strpos treats %, _ and backslashes as ordinary name characters.
        values.append(name)
        cur.execute("SELECT u.user_id,u.full_name,u.role FROM users u WHERE u.role IN ('oqituvchi','oquvchi','ota-ona') AND (" + " OR ".join(scopes) + ") AND strpos(lower(COALESCE(u.full_name,'')),lower(%s))>0 ORDER BY u.full_name,u.user_id LIMIT 30", tuple(values))
        return {"natijalar": [dict(row) for row in cur.fetchall()]}
    finally:
        conn.rollback()
        cur.close()
        conn.close()


def reissue_school_code(platform, actor_id, school_id, person_id):
    """Rotate one unclaimed person's code without reimporting any school data."""
    if any(not isinstance(value, int) or isinstance(value, bool) for value in (actor_id, school_id, person_id)) or school_id <= 0 or person_id >= 0:
        raise MembershipError("Maktab va hali akkauntga ulanmagan shaxsni tanlang.", 422)
    conn = platform._db()
    cur = conn.cursor()
    try:
        if not platform._maktab_boshqaruvchi_mi(cur, actor_id, school_id):
            raise MembershipError("Kirish kodini faqat shu maktab rahbariyati yoki administrator yangilaydi.", 403)
        platform._xodim_kod_jadvali(cur)
        # Same lock order as redeem: authentication identity -> invitation ->
        # person -> school. Historical and active code rows cannot deadlock.
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,31))", (f"auth-user:{person_id}",))
        cur.execute("SELECT kod FROM xodim_kod WHERE user_id=%s ORDER BY kod FOR UPDATE", (person_id,))
        cur.fetchall()
        cur.execute("SELECT * FROM users WHERE user_id=%s FOR UPDATE", (person_id,))
        person = cur.fetchone()
        if not person or person.get("role") not in {"oqituvchi", "oquvchi", "ota-ona"}:
            raise MembershipError("Taklif beriladigan xodim, o'quvchi yoki ota-ona topilmadi.", 404)
        columns = _available_columns(cur, set(IDENTITIES) | LEGACY_PHONE_TABLES | {"school_person_profiles", "parent_child"})
        belongs = person.get("maktab_id") == school_id
        if not person.get("maktab_id") and person.get("role") == "ota-ona":
            # A personal code has no separate school scope. Multiple parent
            # schools are ambiguous and must not silently choose one.
            belongs = _parent_school_ids(cur, person_id, columns) == {school_id}
        if not belongs:
            raise MembershipError("Bu shaxs tanlangan maktabga tegishli emas.", 403)
        if has_login_identity(cur, person_id, columns):
            raise MembershipError("Shaxs o'z akkauntiga ulangan. Uning mavjud kirish usulidan foydalaning; yangi ulash kodi berilmaydi.", 409)
        cur.execute("SELECT * FROM maktablar WHERE id=%s FOR UPDATE", (school_id,))
        school = cur.fetchone()
        if not school or school.get("deleted_at") is not None or school.get("archived_at") is not None or platform.institution_is_archived(cur, "maktab", school_id):
            raise MembershipError("Maktab topilmadi yoki arxivlangan.", 410)
        if school.get("lifecycle_status") == "read_only":
            raise MembershipError("Maktab hozir faqat ko'rish rejimida; kirish kodini yangilab bo'lmaydi.", 423)
        code, stored = platform._xodim_kod_yarat()
        cur.execute("UPDATE xodim_kod SET ishlatildi=TRUE WHERE user_id=%s AND ishlatildi=FALSE", (person_id,))
        cur.execute("INSERT INTO xodim_kod(kod,user_id) VALUES(%s,%s)", (stored, person_id))
        conn.commit()
        return {"name": person["full_name"], "role": person["role"], "code": code,
                "user_id": person_id, "maktab_id": school_id, "kod_muddati": "2 oy"}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def redeem_code(platform, user_id, value, *, institute=None):
    plain = normalize_code(value)
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id == 0:
        raise MembershipError("Avval o'z haqiqiy akkauntingizga kiring.", 403)
    _, hashed = platform._xodim_kod_variantlari(plain)
    conn = platform._db()
    cur = conn.cursor()
    subject = platform._xodim_kod_subject("user", user_id)
    try:
        platform._xodim_kod_jadvali(cur)
        platform._muassasa_jadvali(cur)
        # Serialize attempts on one account across workers, including failure count.
        cur.execute("SELECT pg_advisory_xact_lock(%s,%s)", (520914, user_id % 2147483647))
        if platform._xodim_kod_bloklanganmi(cur, subject):
            raise MembershipError("Ko'p noto'g'ri urinish. 30 daqiqadan keyin qayta urinib ko'ring.", 429)
        code_query = """SELECT kod AS stored_code,user_id AS placeholder_id,ishlatildi,
                        (yaratildi>NOW()-INTERVAL '2 months') AS hali_yangi
                        FROM xodim_kod WHERE kod IN (%s,%s)
                        ORDER BY CASE WHEN kod=%s THEN 0 ELSE 1 END LIMIT 1"""
        # Locate the source without locking a single code ahead of its owner.
        # Rotation locks the owner before all historical codes; matching that
        # order avoids a cycle when one transaction holds the active code and
        # the other holds an older code for the same person.
        cur.execute(code_query, (hashed, plain, hashed))
        invitation = cur.fetchone()
        if not invitation:
            platform._xodim_kod_xato_urinish(cur, subject)
            conn.commit()
            raise MembershipError("Kirish kodi noto'g'ri. Admin bergan shaxsiy kodni tekshiring.")
        old_id = int(invitation["placeholder_id"])
        if old_id >= 0:
            raise MembershipError("Bu kod haqiqiy akkauntga tegishli; boshqa hisobga ko'chirish mumkin emas.", 409)
        for locked_user_id in sorted({old_id, user_id}):
            cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,31))", (f"auth-user:{locked_user_id}",))
        # Re-read after acquiring the shared identity lock: the nonlocking
        # snapshot can have expired or been consumed by a concurrent rotation.
        cur.execute(code_query + " FOR UPDATE", (hashed, plain, hashed))
        invitation = cur.fetchone()
        error = None
        if not invitation or int(invitation["placeholder_id"]) != old_id:
            error = MembershipError("Kirish kodi noto'g'ri. Admin bergan shaxsiy kodni tekshiring.")
        elif invitation["ishlatildi"]:
            error = MembershipError("Kirish kodi avval ishlatilgan. Muassasaga ulangan hisobingizga kiring yoki adminga murojaat qiling.", 409)
        elif not invitation["hali_yangi"]:
            error = MembershipError("Kirish kodining 2 oylik muddati tugagan. Admindan yangi kod so'rang.", 410)
        if error:
            platform._xodim_kod_xato_urinish(cur, subject)
            conn.commit()
            raise error
        cur.execute("SELECT * FROM users WHERE user_id=ANY(%s) ORDER BY user_id FOR UPDATE", ([old_id, user_id],))
        users = {int(row["user_id"]): dict(row) for row in cur.fetchall()}
        old, current = users.get(old_id), users.get(user_id)
        if not old or not current:
            raise MembershipError("Taklif yoki joriy akkaunt topilmadi. Adminga murojaat qiling.", 404)
        tables = {"users", "universitet_taklif_kodlari", "school_person_profiles", "telefon_hisob"}
        tables.update(IDENTITIES)
        tables.update(LEGACY_PHONE_TABLES)
        for references in REFERENCES.values():
            tables.update(references)
        columns = _available_columns(cur, tables)
        if old_id == user_id or has_login_identity(cur, old_id, columns):
            raise MembershipError("Bu profil egasining akkauntiga allaqachon ulangan. Mavjud kirish usulidan foydalaning.", 409)
        if not has_login_identity(cur, user_id, columns):
            raise MembershipError("Avval Google yoki Telegram orqali o'z akkauntingizga kiring.", 403)
        university_invite = _university_invite(cur, invitation["stored_code"], columns)
        institutions = [(kind, old.get(field)) for kind, (field, _) in INSTITUTIONS.items() if old.get(field)]
        if not institutions and old.get("role") == "ota-ona":
            institutions = [("maktab", school_id) for school_id in sorted(_parent_school_ids(cur, old_id, columns))]
        if len(institutions) != 1:
            raise MembershipError("Kodga tegishli muassasa aniq topilmadi. Admindan kodni yangilashni so'rang.", 409)
        kind, institution_id = institutions[0]
        if university_invite and (kind != "universitet" or int(university_invite["universitet_id"]) != int(institution_id)):
            raise MembershipError("Taklifdagi muassasa mos emas.", 409)
        if platform.institution_is_archived(cur, kind, institution_id):
            raise MembershipError("Bu muassasa arxivlangan. Avval administrator uni tiklashi kerak.", 410)
        institution_field, institution_table = INSTITUTIONS[kind]
        cur.execute(f"SELECT nomi FROM {institution_table} WHERE id=%s FOR UPDATE", (institution_id,))
        organization = cur.fetchone()
        if not organization:
            raise MembershipError("Muassasa topilmadi.", 404)
        if kind == "bogcha" and not platform._bogcha_legacy_faol_holat(cur, institution_id):
            raise MembershipError("Bu bog'cha faol emas.", 410)
        role = old.get("role")
        if role not in {"oqituvchi", "oquvchi", "ota-ona"}:
            raise MembershipError("Taklifdagi rol noto'g'ri. Adminga murojaat qiling.", 409)
        position = old.get("lavozim") or role
        if university_invite:
            if institute is None:
                raise MembershipError("Institut moduli tayyor emas. Keyinroq urinib ko'ring.", 503)
            position, role = _claim_university(cur, university_invite, old, user_id, institute)
        elif kind == "universitet":
            if institute is None:
                raise MembershipError("Institut moduli tayyor emas. Keyinroq urinib ko'ring.", 503)
            position, role = _claim_legacy_university(cur, old, user_id, institute)
        # No login identity is copied, and roles are read only from admin-created rows.
        transfer_references(cur, kind, old_id, user_id, columns)
        if university_invite and university_invite["turi"] == "talaba":
            # Transfer existing roster rows first. Inserting the new row before
            # that UPDATE would make the placeholder's row hit the unique key.
            cur.execute("""INSERT INTO universitet_guruh_azolari(guruh_id,user_id)
                           SELECT guruh_id,%s FROM universitet_qabul_talabalari
                           WHERE id=%s AND user_id=%s AND guruh_id IS NOT NULL
                           ON CONFLICT DO NOTHING""", (user_id, university_invite["qabul_talaba_id"], user_id))
        if kind == "bogcha":
            platform._bogcha_v2_xodimni_koddan_otkaz(cur, institution_id, old_id, user_id, position)
        first = not any(current.get(field) for field, _ in INSTITUTIONS.values())
        same_primary = current.get(institution_field) == institution_id
        # Release unique per-school timetable number before copying it.
        clear = [field + "=NULL" for field, _ in INSTITUTIONS.values() if field in columns.get("users", set())]
        clear += [field + "=NULL" for field in ("lavozim", "jadval_raqami") if field in columns.get("users", set())]
        if clear:
            cur.execute("UPDATE users SET " + ",".join(clear) + " WHERE user_id=%s AND user_id<0", (old_id,))
        updates, values = [], []
        if first or same_primary:
            updates.extend([institution_field + "=%s", "lavozim=%s"])
            values.extend([institution_id, position])
            for field in ("class", "class_letter", "fanlari", "oqitadigan_sinflari", "ish_staji", "toifasi", "haftalik_dars_soati", "haftalik_maqsad_soat", "mutaxassisligi", "jadval_raqami"):
                if field in columns.get("users", set()) and old.get(field) is not None and (current.get(field) is None or (field in ("class", "class_letter") and role == "oquvchi")):
                    updates.append('"' + field + '"=%s')
                    values.append(old[field])
        # Personal choice during onboarding is not an institutional role. A new
        # teacher invite must turn a generic account into the teacher workspace.
        if current.get("role") != "admin" and (first or same_primary or current.get("role") in (None, "", "kabutar", "mustaqil")):
            updates.append("role=%s")
            values.append(role)
        if "kabutar_education_ready" in columns.get("users", set()):
            updates.append("kabutar_education_ready=TRUE")
        if "kabutar_learning_profile" in columns.get("users", set()):
            updates.append("kabutar_learning_profile='{}'::jsonb")
        if updates:
            cur.execute("UPDATE users SET " + ",".join(updates) + " WHERE user_id=%s", (*values, user_id))
        cur.execute("""INSERT INTO foydalanuvchi_muassasalari(user_id,muassasa_turi,muassasa_id,lavozim)
                       VALUES(%s,%s,%s,%s) ON CONFLICT(user_id,muassasa_turi,muassasa_id)
                       DO UPDATE SET lavozim=EXCLUDED.lavozim""", (user_id, kind, institution_id, position))
        cur.execute("DELETE FROM foydalanuvchi_muassasalari WHERE user_id=%s AND muassasa_turi=%s AND muassasa_id=%s", (old_id, kind, institution_id))
        cur.execute("UPDATE xodim_kod SET ishlatildi=TRUE WHERE user_id=%s", (old_id,))
        # Admin-entered contact details are not verified login identities. Remove
        # the stale reservation instead of turning it into a verified phone link.
        if "user_id" in columns.get("telefon_hisob", set()):
            cur.execute("DELETE FROM telefon_hisob WHERE user_id=%s", (old_id,))
        if university_invite:
            cur.execute("""UPDATE universitet_taklif_kodlari SET ishlatildi_at=NOW(),kod_shifr=NULL
                           WHERE placeholder_user_id=%s AND ishlatildi_at IS NULL""", (old_id,))
            institute._audit(cur, institution_id, user_id, "kirish_kodi_qabul", university_invite["turi"], university_invite.get("qabul_talaba_id") or university_invite.get("xodim_rol_id"))
        platform._xodim_kod_urinishni_tozalash(cur, subject)
        conn.commit()
        return {"holat": "qoshildi", "lavozim": position, "role": role,
                "joy_nomi": organization["nomi"], "muassasa_turi": kind,
                "muassasa_id": institution_id, "universitet_id": institution_id if kind == "universitet" else None}
    except Exception as error:
        conn.rollback()
        if getattr(error, "pgcode", None) == "23505":
            raise MembershipError("Hisobingizda shu muassasaga tegishli boshqa yozuv bor. Admin biriktirishni tekshirsin; kod sarflanmadi.", 409) from None
        raise
    finally:
        cur.close()
        conn.close()

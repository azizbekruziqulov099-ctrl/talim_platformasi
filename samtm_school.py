"""School OS and smart timetable routes extracted from the legacy monolith.

The public URLs and business logic are preserved.  Definitions are patched back
into samtm_platform so older route functions that resolve late-bound helpers keep
the same behaviour they had in one file.

V19.8: parallel guruh xonasi yozilmagan bo'lsa ham jadval yaratiladi; xona
keyin frontendda "Xona yo'q" holatida tahrirlanadi. Yakuniy generator repair
bosqichi sinf ichki oknosini yopadi, kunlik soatlarni tenglashtiradi va J/T
hamda texnologiyani imkon qadar 3–6-darsga xavfsiz almashtiradi.
"""
try:
    from . import samtm_platform as _platform
    from .samtm_platform import *
except ImportError:  # Railway working directory may be backend/
    import samtm_platform as _platform
    from samtm_platform import *

import time as _samtm_time

# ``from samtm_platform import *`` Python qoidasiga ko'ra nomi ``_`` bilan
# boshlanadigan yordamchilarni import qilmaydi. Maktab kodi esa eski monolitdagi
# shu ichki yordamchilardan ham foydalanadi. Dunder metama'lumotlarni tegmasdan,
# platformadagi barcha oddiy va private nomlarni lokal namespace'ga ulaymiz.
# setdefault maktab modulining o'z ta'riflarini keyin xavfsiz ustun qo'yadi.
for _platform_name, _platform_value in vars(_platform).items():
    if not _platform_name.startswith("__"):
        globals().setdefault(_platform_name, _platform_value)

_V19_IMPORTED_NAMES = set(globals())

# V19.8 deploy belgisi: V19.7 kasr-soat imkoniyatlari saqlanadi va V17 da
# yaratilgan maktab legacy maktab workspace'iga atomar bog'lanadi.
SAMTM_SCHOOL_RELEASE = "samtm-school-workspace-link-v19.8"
SAMTM_SCHOOL_PACKAGE_REVISION = "multi-school-access-2month-rev55"
_platform.SAMTM_RELEASE = SAMTM_SCHOOL_RELEASE
_platform.SAMTM_PACKAGE_REVISION = SAMTM_SCHOOL_PACKAGE_REVISION
try:
    app.version = "19.8"
except Exception:
    pass

def _sinf_guruh_soni_normalizatsiya(usul, guruh_soni):
    """Guruh usuliga mos 1–4 oralig'idagi haqiqiy guruh sonini qaytaradi.

    Bu helper eski monolitda maktab modulidan oldin ta'riflangan edi. Modulga
    ajratishda ta'rifi tushib qolib, yuklama matritsasida NameError bergan.
    """
    usul = (usul or "none").strip().lower()
    if usul == "none":
        return 1
    if usul == "gender":
        return 2
    try:
        soni = int(guruh_soni or 2)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail="Guruh soni raqam bo'lishi kerak",
        ) from error
    if soni not in (2, 3, 4):
        raise HTTPException(
            status_code=400,
            detail="Guruh soni 2, 3 yoki 4 bo'lishi kerak",
        )
    return soni

# ═══════════════════════════════════════════════════════════
# V18.45 — AQILLI MAKTAB BOSH SAHIFASI / O'QITUVCHI BUGUNI / YUKLAMA
# Kundalikning o'rnini bosmaydi: bu yerda ichki monitoring, yordamchi
# signal va rejalashtirish ishlaydi.
# ═══════════════════════════════════════════════════════════

def _v1845_smart_school_tables(cur):
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS haftalik_dars_soati INTEGER")
    _rejalashtirish_jadvallari(cur)
    cur.execute("""CREATE TABLE IF NOT EXISTS dars_monitoring_baholari(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        oquvchi_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        oqituvchi_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        sana DATE NOT NULL DEFAULT CURRENT_DATE,
        fan TEXT NOT NULL,
        mavzu TEXT,
        foiz INTEGER NOT NULL,
        izoh TEXT,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CHECK (foiz BETWEEN 0 AND 100)
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_monitoring_bola_fan_sana ON dars_monitoring_baholari(oquvchi_user_id, fan, sana DESC)")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_holatlar(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        oquvchi_user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        turi TEXT NOT NULL,
        daraja INTEGER NOT NULL DEFAULT 1,
        sarlavha TEXT NOT NULL,
        tavsif TEXT,
        masul_rol TEXT,
        holat TEXT NOT NULL DEFAULT 'ochiq',
        manba TEXT,
        manba_sana DATE,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aqlli_holat_maktab_holat ON aqlli_holatlar(maktab_id, holat, daraja DESC)")


def _v1845_joriy_chorak(sana):
    from datetime import date
    if isinstance(sana, str):
        sana = date.fromisoformat(sana)
    y, m = sana.year, sana.month
    if m in (9, 10):
        return date(y, 9, 1), date(y, 10, 31), 1
    if m in (11, 12):
        return date(y, 11, 1), date(y, 12, 31), 2
    if m in (1, 2, 3):
        return date(y, 1, 1), date(y, 3, 31), 3
    if m in (4, 5):
        return date(y, 4, 1), date(y, 5, 31), 4
    return date(y, 6, 1), date(y, 8, 31), 0


def _v1845_davomat_holat_yangila(cur, maktab_id, bola_id, sana):
    """Jarima qo'llamaydi va tashqi tashkilotga avtomatik shaxsiy ma'lumot yubormaydi.
    Faqat maktab ichida kuzatuv darajasini oshiradi; tashqi hamkor kerak bo'lsa
    vakolatli xodim holatni alohida ko'rib chiqadi."""
    _v1845_smart_school_tables(cur)
    bosh, oxir, chorak = _v1845_joriy_chorak(sana)
    cur.execute("""
        SELECT COUNT(*) AS son FROM davomat
        WHERE user_id=%s AND holat='kelmadi' AND sana BETWEEN %s AND %s
    """, (bola_id, bosh, oxir))
    son = int((cur.fetchone() or {}).get("son") or 0)
    if son <= 0:
        return None
    if son == 1:
        daraja, masul, sarlavha = 1, "sinf_rahbari", "Birinchi sababsiz davomat signali"
    elif son == 2:
        daraja, masul, sarlavha = 2, "psixolog_va_manaviyat", "Takroriy davomat — maktab ichki kuzatuvi"
    elif son == 3:
        daraja, masul, sarlavha = 3, "direktor", "Davomat bo'yicha rahbariyat ko'rigi kerak"
    else:
        daraja, masul, sarlavha = 4, "vakolatli_hamkor_korigi", "Surunkali davomat — vakolatli ko'rib chiqish tavsiyasi"
    cur.execute("""
        SELECT id FROM aqlli_holatlar
        WHERE maktab_id=%s AND oquvchi_user_id=%s AND turi='davomat'
          AND holat='ochiq' AND manba_sana BETWEEN %s AND %s
        ORDER BY id DESC LIMIT 1
    """, (maktab_id, bola_id, bosh, oxir))
    bor = cur.fetchone()
    tavsif = f"{chorak or '-'}-chorak davrida {son} marta sababsiz kelmagan. Avtomatik jarima qo'llanmaydi; mas'ul vaziyatni ko'rib chiqadi."
    if bor:
        cur.execute("""
            UPDATE aqlli_holatlar SET daraja=%s,sarlavha=%s,tavsif=%s,masul_rol=%s,
                manba_sana=%s,yangilangan_at=NOW() WHERE id=%s
        """, (daraja, sarlavha, tavsif, masul, sana, bor["id"]))
        return bor["id"]
    cur.execute("""
        INSERT INTO aqlli_holatlar(maktab_id,oquvchi_user_id,turi,daraja,sarlavha,tavsif,masul_rol,manba,manba_sana)
        VALUES(%s,%s,'davomat',%s,%s,%s,%s,'davomat',%s) RETURNING id
    """, (maktab_id, bola_id, daraja, sarlavha, tavsif, masul, sana))
    return cur.fetchone()["id"]


class V1845MonitoringYozuvi(BaseModel):
    oquvchi_user_id: int
    foiz: int
    izoh: Optional[str] = None


class V1845MonitoringSorov(BaseModel):
    token: str
    sinf_id: int
    fan: str
    mavzu: Optional[str] = None
    sana: Optional[str] = None
    yozuvlar: list[V1845MonitoringYozuvi]


@app.post("/api/oqituvchi/kunlik_monitoring")
def v1845_kunlik_monitoring(sorov: V1845MonitoringSorov):
    teacher_id = _jwt_tekshir(sorov.token)
    conn = _db(); cur = conn.cursor()
    _v1845_smart_school_tables(cur); _xodim_sinf_birikmalari_jadvali(cur)
    cur.execute("SELECT maktab_id FROM maktab_sinflari WHERE id=%s", (sorov.sinf_id,))
    sinf = cur.fetchone()
    if not sinf:
        cur.close(); conn.close(); raise HTTPException(status_code=404, detail="Sinf topilmadi")
    ruxsat = _maktab_boshqaruvchi_mi(cur, teacher_id, sinf["maktab_id"])
    if not ruxsat:
        cur.execute("""
            SELECT 1 FROM maktab_dars_birikmalari
            WHERE user_id=%s AND sinf_id=%s AND LOWER(TRIM(fan_nomi))=LOWER(TRIM(%s)) LIMIT 1
        """, (teacher_id, sorov.sinf_id, sorov.fan))
        ruxsat = cur.fetchone() is not None
    if not ruxsat:
        cur.close(); conn.close(); raise HTTPException(status_code=403, detail="Bu sinf/fan monitoringini kiritishga ruxsat yo'q")
    sana = sorov.sana or datetime.now().date().isoformat()
    saqlandi = 0
    for y in sorov.yozuvlar:
        if not 0 <= int(y.foiz) <= 100:
            cur.close(); conn.close(); raise HTTPException(status_code=400, detail="Monitoring foizi 0..100 bo'lishi kerak")
        cur.execute("""
            INSERT INTO dars_monitoring_baholari(maktab_id,sinf_id,oquvchi_user_id,oqituvchi_user_id,sana,fan,mavzu,foiz,izoh)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (sinf["maktab_id"], sorov.sinf_id, y.oquvchi_user_id, teacher_id, sana, sorov.fan.strip(), sorov.mavzu, int(y.foiz), y.izoh))
        saqlandi += 1
    conn.commit(); cur.close(); conn.close()
    return {"holat": "saqlandi", "soni": saqlandi}


@app.get("/api/oqituvchi/bugun")
def v1845_oqituvchi_bugun(token: str):
    teacher_id = _jwt_tekshir(token)
    from zoneinfo import ZoneInfo
    hozir = datetime.now(ZoneInfo("Asia/Tashkent"))
    kun = hozir.isoweekday()
    joriy_hafta_turi = "toq" if int(hozir.isocalendar().week) % 2 else "juft"
    conn = _db(); cur = conn.cursor()
    _v1845_smart_school_tables(cur); _xodim_sinf_birikmalari_jadvali(cur)
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    cur.execute("SELECT full_name,maktab_id,haftalik_dars_soati,kundalik_baho_eslatmasi FROM users WHERE user_id=%s", (teacher_id,))
    teacher = cur.fetchone()
    if not teacher:
        cur.close(); conn.close(); raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
    darslar = []
    hafta_darsi = 0
    cur.execute("SELECT to_regclass('public.aqlli_jadval_urinishlari_v2') AS table_name")
    smart_bor = bool((cur.fetchone() or {}).get("table_name"))
    smart_run = None
    if smart_bor and teacher.get("maktab_id"):
        cur.execute("""SELECT id FROM aqlli_jadval_urinishlari_v2
                       WHERE maktab_id=%s AND holat='tasdiqlangan' ORDER BY id DESC LIMIT 1""",
                    (teacher["maktab_id"],))
        smart_run = cur.fetchone()
    if smart_run:
        cur.execute("""SELECT e.id,e.dars_raqami,e.fan_nomi AS fan,
                              COALESCE(r.nomi,e.xona_matni) AS xona,
                              e.boshlanish_vaqti,e.tugash_vaqti,
                              s.id AS sinf_id,s.sinf,s.harf,e.guruh_kaliti,e.smena,e.hafta_turi
                       FROM aqlli_jadval_slotlari_v2 e
                       JOIN maktab_sinflari s ON s.id=e.sinf_id
                       LEFT JOIN aqlli_xonalar_v2 r ON r.id=e.xona_id
                       WHERE e.urinish_id=%s AND e.hafta_kuni=%s AND e.oqituvchi_user_id=%s
                         AND e.hafta_turi IN ('har_hafta',%s)
                       ORDER BY e.smena,e.dars_raqami,s.sinf::int,s.harf,e.guruh_kaliti""",
                    (smart_run["id"], kun, teacher_id, joriy_hafta_turi))
        darslar = cur.fetchall()
        cur.execute("""SELECT COUNT(*) AS hafta_darsi FROM aqlli_jadval_slotlari_v2
                       WHERE urinish_id=%s AND oqituvchi_user_id=%s
                         AND hafta_turi IN ('har_hafta',%s)""",
                    (smart_run["id"], teacher_id, joriy_hafta_turi))
        hafta_darsi = int((cur.fetchone() or {}).get("hafta_darsi") or 0)
    else:
        cur.execute("""
            SELECT DISTINCT j.id,j.dars_raqami,j.fan,j.xona,j.boshlanish_vaqti,j.tugash_vaqti,
                   s.id AS sinf_id,s.sinf,s.harf,j.guruh_kaliti,s.sinf::int AS sinf_sort
            FROM dars_jadvali j
            JOIN maktab_sinflari s ON s.id=j.sinf_id
            LEFT JOIN maktab_dars_birikmalari b
              ON b.sinf_id=j.sinf_id AND LOWER(TRIM(b.fan_nomi))=LOWER(TRIM(j.fan)) AND b.user_id=%s
            WHERE j.kun=%s AND (j.oqituvchi_user_id=%s OR (j.oqituvchi_user_id IS NULL AND b.user_id=%s))
            ORDER BY j.dars_raqami,sinf_sort,s.harf
        """, (teacher_id, kun, teacher_id, teacher_id))
        darslar = cur.fetchall()
        cur.execute("""
            SELECT COUNT(DISTINCT j.id) AS hafta_darsi FROM dars_jadvali j
            LEFT JOIN maktab_dars_birikmalari b
              ON b.sinf_id=j.sinf_id AND LOWER(TRIM(b.fan_nomi))=LOWER(TRIM(j.fan)) AND b.user_id=%s
            WHERE j.oqituvchi_user_id=%s OR (j.oqituvchi_user_id IS NULL AND b.user_id=%s)
        """, (teacher_id, teacher_id, teacher_id))
        hafta_darsi = int((cur.fetchone() or {}).get("hafta_darsi") or 0)
    kundalik_eslatma_yoqilgan = bool(teacher.get("kundalik_baho_eslatmasi"))
    cur.close(); conn.close()
    kundalik_eslatma = bool(kundalik_eslatma_yoqilgan and darslar and hozir.hour >= 15)
    return {
        "sana": hozir.date().isoformat(), "kun": kun, "hafta_turi": joriy_hafta_turi,
        "oqituvchi": teacher["full_name"],
        "darslar": darslar, "haftalik_reja_soati": teacher["haftalik_dars_soati"],
        "jadvaldagi_haftalik_soat": hafta_darsi,
        "kundalik_baho_eslatmasi_yoqilgan": kundalik_eslatma_yoqilgan,
        "kundalik_baho_eslatma": kundalik_eslatma,
        "kundalik_baho_eslatma_matni": "Bugungi darslaringiz bo'yicha Kundalikda baholarni kiritishni unutmadingizmi?" if kundalik_eslatma else None,
    }


class V1846KundalikEslatmaSozlama(BaseModel):
    yoqilgan: bool


@app.put("/api/oqituvchi/kundalik-baho-eslatmasi")
def v1846_kundalik_baho_eslatmasi(sorov: V1846KundalikEslatmaSozlama, token: str):
    teacher_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    pass  # V19: DDL moved to startup migration.
    cur.execute(
        "UPDATE users SET kundalik_baho_eslatmasi=%s WHERE user_id=%s RETURNING user_id",
        (bool(sorov.yoqilgan), teacher_id),
    )
    if not cur.fetchone():
        conn.rollback(); cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
    conn.commit(); cur.close(); conn.close()
    return {"holat": "saqlandi", "yoqilgan": bool(sorov.yoqilgan)}


@app.get("/api/maktab/yuklama_xulosasi")
def v1845_yuklama_xulosasi(token: str, maktab_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    _v1845_smart_school_tables(cur)
    # V18.57: GET endpoint ma'lumotni o'qiydi, dublikat tozalash kabi yozuv amali bajarmaydi.
    if not _maktab_boshqaruvchi_mi(cur, actor_id, maktab_id):
        cur.close(); conn.close(); raise HTTPException(status_code=403, detail="Faqat maktab rahbariyati yoki admin ko'ra oladi")
    cur.execute("SELECT to_regclass('public.aqlli_jadval_urinishlari_v2') AS table_name")
    smart_bor = bool((cur.fetchone() or {}).get("table_name"))
    smart_run_id = None
    if smart_bor:
        cur.execute("SELECT id FROM aqlli_jadval_urinishlari_v2 WHERE maktab_id=%s AND holat='tasdiqlangan' ORDER BY id DESC LIMIT 1", (maktab_id,))
        run = cur.fetchone(); smart_run_id = run["id"] if run else None
    if smart_run_id:
        cur.execute("""
            SELECT u.user_id,u.full_name,u.fanlari,u.haftalik_dars_soati,
                   COUNT(e.id) AS jadvaldagi_soat
            FROM users u
            LEFT JOIN aqlli_jadval_slotlari_v2 e
              ON e.oqituvchi_user_id=u.user_id AND e.urinish_id=%s
            WHERE u.maktab_id=%s AND u.lavozim IS NOT NULL
            GROUP BY u.user_id,u.full_name,u.fanlari,u.haftalik_dars_soati
            ORDER BY u.full_name
        """, (smart_run_id, maktab_id))
    else:
        cur.execute("""
            SELECT u.user_id,u.full_name,u.fanlari,u.haftalik_dars_soati,
                   COUNT(j.id) AS jadvaldagi_soat
            FROM users u
            LEFT JOIN dars_jadvali j ON j.oqituvchi_user_id=u.user_id
            WHERE u.maktab_id=%s AND u.lavozim IS NOT NULL
            GROUP BY u.user_id,u.full_name,u.fanlari,u.haftalik_dars_soati
            ORDER BY u.full_name
        """, (maktab_id,))
    xodimlar = cur.fetchall()
    for x in xodimlar:
        reja = x.get("haftalik_dars_soati")
        amaldagi = int(x.get("jadvaldagi_soat") or 0)
        x["farq"] = None if reja is None else int(reja) - amaldagi
        x["holat"] = "kiritilmagan" if reja is None else ("ortiqcha" if amaldagi > int(reja) else "toliq" if amaldagi == int(reja) else "yetishmaydi")
    cur.close(); conn.close()
    return {"xodimlar": xodimlar}


@app.get("/api/maktab/aqlli_holatlar")
def v1845_aqlli_holatlar(token: str, maktab_id: int, holat: str = "ochiq"):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor(); _v1845_smart_school_tables(cur)
    if not _maktab_boshqaruvchi_mi(cur, actor_id, maktab_id):
        cur.close(); conn.close(); raise HTTPException(status_code=403, detail="Faqat maktab rahbariyati yoki admin ko'ra oladi")
    cur.execute("""
        SELECT h.*,u.full_name FROM aqlli_holatlar h
        JOIN users u ON u.user_id=h.oquvchi_user_id
        WHERE h.maktab_id=%s AND h.holat=%s
        ORDER BY h.daraja DESC,h.yangilangan_at DESC LIMIT 100
    """, (maktab_id, holat))
    natija=cur.fetchall(); cur.close(); conn.close(); return {"holatlar": natija}


# V18.45: eski davomat endpointidan keyin holat yaratilishi uchun route-level wrapper emas,
# balki mavjud endpoint ishlagach davomat ma'lumotidan signalni keyingi so'rovda dashboard/holatlar
# orqali hisoblash mumkin. Quyidagi endpoint kerak bo'lsa qo'lda qayta hisoblaydi.
@app.post("/api/maktab/aqlli_holatlarni_yangila")
def v1845_holatlarni_yangila(token: str, maktab_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor(); _davomat_jadvali(cur); _v1845_smart_school_tables(cur)
    if not _maktab_boshqaruvchi_mi(cur, actor_id, maktab_id):
        cur.close(); conn.close(); raise HTTPException(status_code=403, detail="Faqat maktab rahbariyati yoki admin yangilay oladi")
    cur.execute("""
        SELECT DISTINCT d.user_id,d.sana FROM davomat d
        JOIN maktab_sinflari s ON s.id=d.sinf_id
        WHERE s.maktab_id=%s AND d.holat='kelmadi' AND d.sana >= CURRENT_DATE - INTERVAL '120 days'
        ORDER BY d.sana
    """, (maktab_id,))
    son=0
    for r in cur.fetchall():
        _v1845_davomat_holat_yangila(cur,maktab_id,r["user_id"],r["sana"]); son += 1
    conn.commit(); cur.close(); conn.close(); return {"holat":"yangilandi","yozuvlar":son}

# ========================= V18.45 END =========================


# ═══════════════════════════════════════════════════════════
# V18.47 — ADMIN UCHUN "ROL SIFATIDA KO'RISH" (READ-ONLY PREVIEW)
# Admin maktabni turli rollar ko'zidan ko'radi, lekin bu endpointlar
# hech qanday ma'lumotni o'zgartirmaydi va boshqa foydalanuvchi tokenini bermaydi.
# ═══════════════════════════════════════════════════════════

_V1847_PREVIEW_ROLLAR = {
    "maktab_admin": "Maktab admini",
    "direktor": "Maktab direktori",
    "zavuch": "O'quv ishlari bo'yicha direktor o'rinbosari",
    "manaviyatchi": "Ma'naviy-ma'rifiy ishlar bo'yicha direktor o'rinbosari",
    "fan_oqituvchisi": "Fan o'qituvchisi",
    "sinf_rahbari": "Sinf rahbari",
    "oquvchi": "O'quvchi",
    "ota_ona": "Ota-ona",
    "psixolog": "Psixolog",
    "hamshira": "Hamshira",
}


def _v1847_preview_common(cur, maktab_id: int):
    _maktab_jadvali(cur)
    _maktab_sinflari_jadvali(cur)
    _sinf_azolari_jadvali(cur)
    _davomat_jadvali(cur)
    _v1845_smart_school_tables(cur)
    _xodim_sinf_birikmalari_jadvali(cur)
    # V18.57: rol ko'rish ham read-only; avtomatik baza tozalash bu yerda ishlamaydi.

    cur.execute("""
        SELECT id, nomi, maktab_raqami, viloyat, tuman, smena_soni
        FROM maktablar WHERE id=%s AND archived_at IS NULL
    """, (maktab_id,))
    maktab = cur.fetchone()
    if not maktab:
        raise HTTPException(status_code=404, detail="Maktab topilmadi")

    cur.execute("""
        SELECT s.id,s.sinf,s.harf,s.rahbar_user_id,
               COALESCE(u.full_name,'') AS rahbar_ismi,
               COUNT(a.user_id) AS oquvchi_soni
        FROM maktab_sinflari s
        LEFT JOIN users u ON u.user_id=s.rahbar_user_id
        LEFT JOIN maktab_sinf_azolari a ON a.sinf_id=s.id
        WHERE s.maktab_id=%s
        GROUP BY s.id,s.sinf,s.harf,s.rahbar_user_id,u.full_name
        ORDER BY s.sinf::int,s.harf
    """, (maktab_id,))
    sinflar = cur.fetchall()

    cur.execute("""
        SELECT user_id,full_name,lavozim,fanlari,haftalik_dars_soati
        FROM users
        WHERE maktab_id=%s AND lavozim IS NOT NULL
        ORDER BY
          CASE lavozim
            WHEN 'direktor' THEN 1
            WHEN 'zam_direktor_uquv' THEN 2
            WHEN 'zam_direktor_tarbiya' THEN 3
            WHEN 'psixolog' THEN 4
            WHEN 'hamshira' THEN 5
            WHEN 'fan_oqituvchisi' THEN 6
            ELSE 20
          END,
          full_name
    """, (maktab_id,))
    xodimlar = cur.fetchall()

    cur.execute("""
        SELECT COUNT(DISTINCT a.user_id) AS son
        FROM maktab_sinf_azolari a
        JOIN maktab_sinflari s ON s.id=a.sinf_id
        WHERE s.maktab_id=%s
    """, (maktab_id,))
    oquvchi_soni = int((cur.fetchone() or {}).get("son") or 0)

    cur.execute("""
        SELECT COUNT(*) AS son FROM aqlli_holatlar
        WHERE maktab_id=%s AND holat='ochiq'
    """, (maktab_id,))
    ochiq_holatlar = int((cur.fetchone() or {}).get("son") or 0)

    cur.execute("""
        SELECT COUNT(*) AS son
        FROM davomat d
        JOIN maktab_sinflari s ON s.id=d.sinf_id
        WHERE s.maktab_id=%s AND d.sana=CURRENT_DATE AND d.holat='kelmadi'
    """, (maktab_id,))
    bugun_kelmagan = int((cur.fetchone() or {}).get("son") or 0)

    return maktab, sinflar, xodimlar, {
        "oquvchi_soni": oquvchi_soni,
        "sinf_soni": len(sinflar),
        "xodim_soni": len(xodimlar),
        "ochiq_holatlar": ochiq_holatlar,
        "bugun_kelmagan": bugun_kelmagan,
    }


@app.get("/api/admin/maktab_korish_katalogi")
def v1847_maktab_korish_katalogi(token: str, maktab_id: int):
    _admin_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        maktab, sinflar, xodimlar, xulosa = _v1847_preview_common(cur, maktab_id)

        cur.execute("""
            SELECT a.sinf_id,u.user_id,u.full_name
            FROM maktab_sinf_azolari a
            JOIN users u ON u.user_id=a.user_id
            JOIN maktab_sinflari s ON s.id=a.sinf_id
            WHERE s.maktab_id=%s
            ORDER BY a.sinf_id,u.full_name
        """, (maktab_id,))
        oquvchilar = cur.fetchall()

        return {
            "read_only": True,
            "maktab": maktab,
            "xulosa": xulosa,
            "rollar": [{"kalit": k, "nom": v} for k, v in _V1847_PREVIEW_ROLLAR.items()],
            "sinflar": sinflar,
            "xodimlar": xodimlar,
            "oquvchilar": oquvchilar,
        }
    finally:
        cur.close(); conn.close()


@app.get("/api/admin/maktab_rol_korish")
def v1847_maktab_rol_korish(
    token: str,
    maktab_id: int,
    rol: str,
    user_id: Optional[int] = None,
    sinf_id: Optional[int] = None,
    oquvchi_id: Optional[int] = None,
):
    _admin_tekshir(token)
    rol = str(rol or "").strip().lower()
    if rol not in _V1847_PREVIEW_ROLLAR:
        raise HTTPException(status_code=400, detail="Noma'lum ko'rish roli")

    conn = _db(); cur = conn.cursor()
    try:
        maktab, sinflar, xodimlar, xulosa = _v1847_preview_common(cur, maktab_id)

        response = {
            "read_only": True,
            "rol": rol,
            "rol_nomi": _V1847_PREVIEW_ROLLAR[rol],
            "maktab": maktab,
            "xulosa": xulosa,
            "tanlangan": {},
            "kartalar": [],
            "bolimlar": [],
            "ogohlantirish": "ADMIN KO'RISH REJIMI — bu oynada hech qanday ma'lumot o'zgartirilmaydi.",
        }

        def card(label, value, tone="blue"):
            response["kartalar"].append({"label": label, "value": value, "tone": tone})

        def section(title, subtitle="", items=None, empty_text=None, kind="list"):
            response["bolimlar"].append({
                "title": title, "subtitle": subtitle, "items": items or [],
                "empty_text": empty_text, "kind": kind,
            })

        # Maktab admini / direktor
        if rol in {"maktab_admin", "direktor"}:
            card("O'quvchilar", xulosa["oquvchi_soni"], "blue")
            card("Sinflar", xulosa["sinf_soni"], "teal")
            card("Xodimlar", xulosa["xodim_soni"], "green")
            card("Bugun kelmagan", xulosa["bugun_kelmagan"], "amber" if xulosa["bugun_kelmagan"] else "green")
            card("Ochiq aqlli holat", xulosa["ochiq_holatlar"], "red" if xulosa["ochiq_holatlar"] else "green")
            section(
                "Maktab boshqaruv markazi",
                "Rahbariyat bir qarashda ko'radigan asosiy holatlar.",
                [
                    {"title": "Dars jadvali va yuklama", "detail": "O'qituvchi yuklamasi, bo'sh darslar va konfliktlar."},
                    {"title": "Davomat signallari", "detail": f"Bugun {xulosa['bugun_kelmagan']} ta kelmagan yozuvi bor."},
                    {"title": "Aqlli holatlar", "detail": f"{xulosa['ochiq_holatlar']} ta ochiq kuzatuv holati."},
                    {"title": "Sinf va xodimlar", "detail": f"{xulosa['sinf_soni']} sinf · {xulosa['xodim_soni']} xodim."},
                ],
            )

        # Zavuch
        elif rol == "zavuch":
            cur.execute("""
                SELECT u.user_id,u.full_name,u.fanlari,u.haftalik_dars_soati,
                       COUNT(j.id) AS jadvaldagi_soat
                FROM users u
                LEFT JOIN dars_jadvali j ON j.oqituvchi_user_id=u.user_id
                WHERE u.maktab_id=%s AND u.lavozim IS NOT NULL
                GROUP BY u.user_id,u.full_name,u.fanlari,u.haftalik_dars_soati
                ORDER BY ABS(COALESCE(u.haftalik_dars_soati,0)-COUNT(j.id)) DESC,u.full_name
                LIMIT 12
            """, (maktab_id,))
            yuklama = cur.fetchall()
            card("Sinflar", xulosa["sinf_soni"], "teal")
            card("O'qituvchilar", sum(1 for x in xodimlar if x.get("fanlari")), "blue")
            card("Bugun kelmagan", xulosa["bugun_kelmagan"], "amber")
            section("O'qituvchi yuklamasi", "Jadval va belgilangan haftalik soatni solishtirish.", [
                {"title": x["full_name"], "detail": f"{x.get('fanlari') or 'Fan ko‘rsatilmagan'} · reja {x.get('haftalik_dars_soati') if x.get('haftalik_dars_soati') is not None else '—'} · jadval {int(x.get('jadvaldagi_soat') or 0)}"}
                for x in yuklama
            ], "Yuklama ma'lumoti yo'q")

        # Ma'naviyatchi
        elif rol == "manaviyatchi":
            cur.execute("""
                SELECT h.daraja,h.sarlavha,h.tavsif,u.full_name
                FROM aqlli_holatlar h JOIN users u ON u.user_id=h.oquvchi_user_id
                WHERE h.maktab_id=%s AND h.holat='ochiq'
                ORDER BY h.daraja DESC,h.yangilangan_at DESC LIMIT 12
            """, (maktab_id,))
            holatlar = cur.fetchall()
            card("Bugun kelmagan", xulosa["bugun_kelmagan"], "amber")
            card("Ochiq holatlar", xulosa["ochiq_holatlar"], "red" if xulosa["ochiq_holatlar"] else "green")
            card("Sinflar", xulosa["sinf_soni"], "teal")
            section("E'tibor talab qiladigan o'quvchilar", "Davomat va tarbiyaviy kuzatuvlar.", [
                {"title": x["full_name"], "detail": f"Daraja {x['daraja']} · {x['sarlavha']}"}
                for x in holatlar
            ], "Hozircha ochiq holat yo'q")

        # Psixolog
        elif rol == "psixolog":
            cur.execute("""
                SELECT h.daraja,h.sarlavha,h.tavsif,u.full_name
                FROM aqlli_holatlar h JOIN users u ON u.user_id=h.oquvchi_user_id
                WHERE h.maktab_id=%s AND h.holat='ochiq'
                  AND (h.masul_rol ILIKE '%%psixolog%%' OR h.daraja>=2)
                ORDER BY h.daraja DESC,h.yangilangan_at DESC LIMIT 12
            """, (maktab_id,))
            holatlar = cur.fetchall()
            card("Ko'rib chiqiladigan holat", len(holatlar), "amber" if holatlar else "green")
            card("Jami o'quvchi", xulosa["oquvchi_soni"], "blue")
            section("Psixolog ish navbati", "Faqat psixologga tegishli yoki yordam talab qiladigan holatlar.", [
                {"title": x["full_name"], "detail": f"Daraja {x['daraja']} · {x['sarlavha']}"}
                for x in holatlar
            ], "Psixolog uchun ochiq signal yo'q")

        # Hamshira — sog'liq yozuvlari alohida modul sifatida keyin ulanadi.
        elif rol == "hamshira":
            card("Jami o'quvchi", xulosa["oquvchi_soni"], "blue")
            card("Sinflar", xulosa["sinf_soni"], "teal")
            section(
                "Hamshira ish maydoni",
                "Sog'liq ma'lumotlari maxfiy bo'lgani uchun admin preview faqat interfeys tuzilishini ko'rsatadi.",
                [
                    {"title": "Bugungi murojaatlar", "detail": "Sog'liq moduli ulanganidan keyin shu yerda chiqadi."},
                    {"title": "Dori/allergiya ogohlantirishlari", "detail": "Faqat vakolatli hamshiraga ko'rinadigan yopiq blok bo'ladi."},
                    {"title": "Tibbiy ko'rik rejalari", "detail": "Sinf kesimida rejalashtiriladi."},
                ],
            )

        # Fan o'qituvchisi
        elif rol == "fan_oqituvchisi":
            if user_id is None:
                raise HTTPException(status_code=400, detail="Fan o'qituvchisini tanlang")
            cur.execute("""
                SELECT user_id,full_name,fanlari,haftalik_dars_soati
                FROM users WHERE user_id=%s AND maktab_id=%s
            """, (user_id, maktab_id))
            teacher = cur.fetchone()
            if not teacher:
                raise HTTPException(status_code=404, detail="Tanlangan o'qituvchi topilmadi")
            response["tanlangan"] = teacher
            cur.execute("""
                SELECT DISTINCT s.id AS sinf_id,s.sinf,s.harf,b.fan_nomi,s.sinf::int AS sinf_sort
                FROM maktab_dars_birikmalari b
                JOIN maktab_sinflari s ON s.id=b.sinf_id
                WHERE b.user_id=%s AND b.maktab_id=%s
                ORDER BY sinf_sort,s.harf,b.fan_nomi
            """, (user_id, maktab_id))
            birikmalar = cur.fetchall()
            cur.execute("""
                SELECT j.dars_raqami,j.fan,j.xona,j.boshlanish_vaqti,s.sinf,s.harf
                FROM dars_jadvali j JOIN maktab_sinflari s ON s.id=j.sinf_id
                WHERE j.oqituvchi_user_id=%s AND j.kun=EXTRACT(ISODOW FROM CURRENT_DATE)::int
                ORDER BY j.dars_raqami
            """, (user_id,))
            bugun = cur.fetchall()
            card("Bugungi dars", len(bugun), "teal")
            card("Biriktirilgan sinf/fan", len(birikmalar), "blue")
            card("Haftalik yuklama", teacher.get("haftalik_dars_soati") if teacher.get("haftalik_dars_soati") is not None else "—", "green")
            section("Bugungi darslarim", teacher["full_name"], [
                {"title": f"{x['dars_raqami']}-dars · {x['fan']}", "detail": f"{x['sinf']}-{x['harf']}" + (f" · {x['boshlanish_vaqti']}" if x.get("boshlanish_vaqti") else "")}
                for x in bugun
            ], "Bugun dars topilmadi")
            section("Mening sinf/fanlarim", "Monitoring va to'garak uchun asosiy ish maydoni.", [
                {"title": f"{x['sinf']}-{x['harf']}", "detail": x["fan_nomi"]} for x in birikmalar
            ], "Sinf/fan birikmasi topilmadi")

        # Sinf rahbari
        elif rol == "sinf_rahbari":
            if sinf_id is None:
                raise HTTPException(status_code=400, detail="Sinfni tanlang")
            cur.execute("""
                SELECT s.id,s.sinf,s.harf,s.rahbar_user_id,u.full_name AS rahbar_ismi
                FROM maktab_sinflari s LEFT JOIN users u ON u.user_id=s.rahbar_user_id
                WHERE s.id=%s AND s.maktab_id=%s
            """, (sinf_id, maktab_id))
            sinf = cur.fetchone()
            if not sinf:
                raise HTTPException(status_code=404, detail="Sinf topilmadi")
            response["tanlangan"] = sinf
            cur.execute("""
                SELECT u.user_id,u.full_name,
                       COUNT(*) FILTER (WHERE d.holat='kelmadi' AND d.sana>=CURRENT_DATE-INTERVAL '30 days') AS kelmadi30,
                       COUNT(*) FILTER (WHERE d.holat='kechikdi' AND d.sana>=CURRENT_DATE-INTERVAL '30 days') AS kechikdi30
                FROM maktab_sinf_azolari a JOIN users u ON u.user_id=a.user_id
                LEFT JOIN davomat d ON d.user_id=u.user_id AND d.sinf_id=a.sinf_id
                WHERE a.sinf_id=%s
                GROUP BY u.user_id,u.full_name ORDER BY u.full_name
            """, (sinf_id,))
            bolalar = cur.fetchall()
            card("O'quvchilar", len(bolalar), "blue")
            card("Rahbar", sinf.get("rahbar_ismi") or "Biriktirilmagan", "teal")
            section(f"{sinf['sinf']}-{sinf['harf']} sinfim", "Sinf rahbari faqat o'z sinfiga kerakli ishlarni ko'radi.", [
                {"title": x["full_name"], "detail": f"30 kun: {int(x.get('kelmadi30') or 0)} kelmadi · {int(x.get('kechikdi30') or 0)} kechikdi"}
                for x in bolalar
            ], "Sinfda o'quvchi yo'q")

        # O'quvchi / ota-ona
        elif rol in {"oquvchi", "ota_ona"}:
            if sinf_id is None:
                raise HTTPException(status_code=400, detail="Avval sinfni tanlang")
            if oquvchi_id is None:
                cur.execute("""
                    SELECT u.user_id FROM maktab_sinf_azolari a
                    JOIN users u ON u.user_id=a.user_id
                    WHERE a.sinf_id=%s ORDER BY u.full_name LIMIT 1
                """, (sinf_id,))
                first = cur.fetchone()
                oquvchi_id = first["user_id"] if first else None
            if oquvchi_id is None:
                raise HTTPException(status_code=404, detail="Bu sinfda o'quvchi topilmadi")
            cur.execute("""
                SELECT u.user_id,u.full_name,s.id AS sinf_id,s.sinf,s.harf
                FROM users u JOIN maktab_sinf_azolari a ON a.user_id=u.user_id
                JOIN maktab_sinflari s ON s.id=a.sinf_id
                WHERE u.user_id=%s AND s.id=%s AND s.maktab_id=%s
            """, (oquvchi_id, sinf_id, maktab_id))
            bola = cur.fetchone()
            if not bola:
                raise HTTPException(status_code=404, detail="O'quvchi tanlangan sinfda topilmadi")
            response["tanlangan"] = bola
            cur.execute("""
                SELECT fan,ROUND(AVG(foiz)) AS foiz,COUNT(*) AS urinish
                FROM dars_monitoring_baholari
                WHERE oquvchi_user_id=%s
                GROUP BY fan ORDER BY AVG(foiz) ASC NULLS LAST LIMIT 10
            """, (oquvchi_id,))
            fanlar = cur.fetchall()
            cur.execute("""
                SELECT COUNT(*) FILTER (WHERE holat='keldi') AS keldi,
                       COUNT(*) FILTER (WHERE holat='kelmadi') AS kelmadi,
                       COUNT(*) FILTER (WHERE holat='kechikdi') AS kechikdi
                FROM davomat
                WHERE user_id=%s AND sana>=CURRENT_DATE-INTERVAL '30 days'
            """, (oquvchi_id,))
            davomat = cur.fetchone() or {}
            card("30 kunda kelgan", int(davomat.get("keldi") or 0), "green")
            card("Kelmagan", int(davomat.get("kelmadi") or 0), "amber")
            card("Kechikkan", int(davomat.get("kechikdi") or 0), "amber")
            if fanlar:
                ortacha = round(sum(float(x.get("foiz") or 0) for x in fanlar) / len(fanlar))
                card("Monitoring o'rtacha", f"{ortacha}%", "blue")
            title = "Mening bilim xaritam" if rol == "oquvchi" else "Farzandimning bilim xaritasi"
            section(title, f"{bola['full_name']} · {bola['sinf']}-{bola['harf']}", [
                {"title": x["fan"], "detail": f"{int(round(float(x.get('foiz') or 0)))}% · {int(x.get('urinish') or 0)} ta monitoring"}
                for x in fanlar
            ], "Hali monitoring natijasi yo'q")
            section(
                "Tavsiya etiladigan yo'l",
                "Tizim mavjud monitoringdan kelib chiqib qaysi fan/mavzuga e'tibor kerakligini ko'rsatadi.",
                [
                    {"title": "Bo'shliqni yopish", "detail": "Past natijali fan va mavzularga qisqa tushuntirish + mashqlar."},
                    {"title": "Bilimni ushlab turish", "detail": "Yaxshi o'zlashtirilgan mavzularga qisqa takrorlash."},
                    {"title": "To'garak va qo'shimcha dars", "detail": "Mos kurslar mavjud bo'lsa shu yerda tavsiya qilinadi."},
                ],
            )

        return response
    finally:
        cur.close(); conn.close()

# ========================= V18.47 END =========================


# ═══════════════════════════════════════════════════════════
# V18.50 — XODIM DUBLIKATLARINI AVTOMATIK TUZATISH
# Faqat Excel importidan yaratilgan manfiy user_id xodimlarga tegadi.
# Haqiqiy Google/Telegram foydalanuvchi hisoblari avtomatik birlashtirilmaydi.
# Eng yangi import yozuvi (eng kichik/manfiy user_id) saqlanadi.
# Eski dublikatlar xavfsiz arxivlanadi, bog'lanishlar yangi yozuvga ko'chiriladi.
# ═══════════════════════════════════════════════════════════

def _v1850_xodim_dublikatlarini_tozala(cur, maktab_id: int):
    _xodim_kod_jadvali(cur)
    _maktab_sinflari_jadvali(cur)
    _xodim_sinf_birikmalari_jadvali(cur)
    _rejalashtirish_jadvallari(cur)
    _xodim_davomati_jadvali(cur)
    _v1845_smart_school_tables(cur)

    cur.execute("""
        SELECT
            LOWER(REGEXP_REPLACE(TRIM(full_name), '\\s+', ' ', 'g')) AS ism_kalit,
            COALESCE(lavozim,'') AS lavozim_kalit,
            ARRAY_AGG(user_id ORDER BY user_id ASC) AS ids
        FROM users
        WHERE maktab_id=%s
          AND user_id < 0
          AND lavozim IS NOT NULL
          AND TRIM(COALESCE(full_name,'')) <> ''
        GROUP BY 1,2
        HAVING COUNT(*) > 1
    """, (maktab_id,))
    guruhlar = cur.fetchall()

    tozalangan = 0
    for g in guruhlar:
        ids = list(g.get("ids") or [])
        if len(ids) < 2:
            continue

        # Import har safar yanada kichik manfiy ID beradi, shu sabab MIN = eng yangi.
        asosiy = ids[0]
        dublikatlar = ids[1:]

        for eski in dublikatlar:
            # Eng to'liq ma'lumotlarni asosiy yozuvga saqlab qolamiz.
            cur.execute("""
                UPDATE users AS yangi
                SET fanlari = COALESCE(NULLIF(yangi.fanlari,''), eski.fanlari),
                    oqitadigan_sinflari = COALESCE(NULLIF(yangi.oqitadigan_sinflari,''), eski.oqitadigan_sinflari),
                    ish_staji = COALESCE(yangi.ish_staji, eski.ish_staji),
                    toifasi = COALESCE(NULLIF(yangi.toifasi,''), eski.toifasi),
                    haftalik_dars_soati = COALESCE(yangi.haftalik_dars_soati, eski.haftalik_dars_soati)
                FROM users AS eski
                WHERE yangi.user_id=%s AND eski.user_id=%s
            """, (asosiy, eski))

            # Sinf rahbarligi.
            cur.execute(
                "UPDATE maktab_sinflari SET rahbar_user_id=%s WHERE maktab_id=%s AND rahbar_user_id=%s",
                (asosiy, maktab_id, eski),
            )

            # Xodim-sinf bog'lanishlarini conflict-siz ko'chiramiz.
            cur.execute("""
                INSERT INTO maktab_xodim_sinflari(maktab_id,user_id,sinf_id,fanlari)
                SELECT maktab_id,%s,sinf_id,fanlari
                FROM maktab_xodim_sinflari
                WHERE maktab_id=%s AND user_id=%s
                ON CONFLICT(user_id,sinf_id) DO UPDATE
                SET fanlari=COALESCE(EXCLUDED.fanlari,maktab_xodim_sinflari.fanlari)
            """, (asosiy, maktab_id, eski))
            cur.execute(
                "DELETE FROM maktab_xodim_sinflari WHERE maktab_id=%s AND user_id=%s",
                (maktab_id, eski),
            )

            # Aniq sinf-fan-guruh birikmalarini ko'chiramiz.
            cur.execute("""
                INSERT INTO maktab_dars_birikmalari(maktab_id,user_id,sinf_id,fan_nomi,guruh_kaliti)
                SELECT maktab_id,%s,sinf_id,fan_nomi,guruh_kaliti
                FROM maktab_dars_birikmalari
                WHERE maktab_id=%s AND user_id=%s
                ON CONFLICT(user_id,sinf_id,fan_nomi,guruh_kaliti) DO NOTHING
            """, (asosiy, maktab_id, eski))
            cur.execute(
                "DELETE FROM maktab_dars_birikmalari WHERE maktab_id=%s AND user_id=%s",
                (maktab_id, eski),
            )

            # Jadvaldagi darslar.
            cur.execute(
                "UPDATE dars_jadvali SET oqituvchi_user_id=%s WHERE oqituvchi_user_id=%s",
                (asosiy, eski),
            )

            # Monitoring yozuvlari (o'qituvchi sifatida).
            cur.execute(
                "UPDATE dars_monitoring_baholari SET oqituvchi_user_id=%s WHERE maktab_id=%s AND oqituvchi_user_id=%s",
                (asosiy, maktab_id, eski),
            )

            # Xodim davomatida bir kunlik conflict bo'lishi mumkin — avval merge.
            cur.execute("""
                INSERT INTO xodim_davomati(maktab_id,user_id,sana,holat,izoh,belgilagan_user_id,belgilangan_at)
                SELECT maktab_id,%s,sana,holat,izoh,belgilagan_user_id,belgilangan_at
                FROM xodim_davomati
                WHERE maktab_id=%s AND user_id=%s
                ON CONFLICT(maktab_id,user_id,sana) DO NOTHING
            """, (asosiy, maktab_id, eski))
            cur.execute(
                "DELETE FROM xodim_davomati WHERE maktab_id=%s AND user_id=%s",
                (maktab_id, eski),
            )

            # Direktor ko'rsatkichi eski duplicatega qaragan bo'lsa.
            cur.execute(
                "UPDATE maktablar SET direktor_user_id=%s WHERE id=%s AND direktor_user_id=%s",
                (asosiy, maktab_id, eski),
            )

            # Eski duplicate kirish kodini bekor qilamiz.
            cur.execute("DELETE FROM xodim_kod WHERE user_id=%s", (eski,))

            # FK sabab foydalanuvchini qattiq DELETE qilmaymiz.
            # Maktabdan chiqarib, lavozimini bo'shatamiz — dashboard/importda qayta chiqmaydi.
            cur.execute("""
                UPDATE users
                SET maktab_id=NULL,
                    lavozim=NULL,
                    fanlari=NULL,
                    oqitadigan_sinflari=NULL,
                    haftalik_dars_soati=NULL,
                    full_name=full_name || ' [dublikat arxiv]'
                WHERE user_id=%s AND user_id<0
            """, (eski,))
            tozalangan += 1

    return {"tozalangan": tozalangan, "guruhlar": len(guruhlar)}


@app.post("/api/admin/maktab_xodim_dublikatlarini_tozala")
def v1850_maktab_xodim_dublikatlarini_tozala(token: str, maktab_id: int):
    _admin_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        natija = _v1850_xodim_dublikatlarini_tozala(cur, maktab_id)
        conn.commit()
        return {"holat": "tozalandi", **natija}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()

# ========================= V18.50 END =========================

# ═══════════════════════════════════════════════════════════
# V18.52 — AQILLI DARS JADVALI 2.0
# Kalendar, smena, o'qituvchi vaqti/yuklamasi, xonalar, parallel guruhlar,
# draft→tasdiq, aniq diagnostika va mavzu rejasini real sanalarga taqsimlash.
# ═══════════════════════════════════════════════════════════

import random as _v1852_random
from collections import defaultdict as _v1852_defaultdict, Counter as _v1852_Counter

_V1852_TABLES_READY = False
_V1852_TABLES_LOCK = threading.Lock()
_V1852_DAM_TURLARI = {"dam", "bayram", "tatil", "qoshimcha_dam"}
_V1852_OQISH_TURLARI = {"oqish", "qoshimcha_oqish"}
_V1852_HOLATLAR = {"taxminiy", "tasdiqlangan"}
_V1852_KUN_TURLARI = _V1852_DAM_TURLARI | _V1852_OQISH_TURLARI
_V1852_VAQT_TURLARI = {"band", "afzal_bosh", "metod_kuni"}
_V1852_HAFTA = {1: "Dushanba", 2: "Seshanba", 3: "Chorshanba", 4: "Payshanba", 5: "Juma", 6: "Shanba", 7: "Yakshanba"}


def _v1855_sinf_raqami(value):
    """`1`, `1-sinf`, `01` kabi qiymatlardan sinf raqamini xavfsiz oladi."""
    match = re.search(r"\d+", str(value or ""))
    if not match:
        return None
    try:
        return int(match.group(0))
    except (TypeError, ValueError):
        return None


def _v1855_boshlangich_sinf(class_row):
    grade = _v1855_sinf_raqami((class_row or {}).get("sinf"))
    return grade is not None and 1 <= grade <= 4


def _v1856_seed_default_class_day_rules(cur, maktab_id: int):
    """Birinchi ishga tushishda eski 1–4/Shanba qoidasini preset sifatida saqlaydi.

    Marker yozilgach admin uni o'chirsa, keyingi reload'da qayta paydo bo'lmaydi.
    """
    cur.execute("SELECT 1 FROM aqlli_sinf_kun_blok_seed_v2 WHERE maktab_id=%s", (maktab_id,))
    if cur.fetchone():
        return
    cur.execute("SELECT COUNT(*) AS son FROM aqlli_sinf_kun_bloklari_v2 WHERE maktab_id=%s", (maktab_id,))
    existing = int((cur.fetchone() or {}).get("son") or 0)
    if existing == 0:
        for grade in (1, 2, 3, 4):
            cur.execute("""INSERT INTO aqlli_sinf_kun_bloklari_v2(
                maktab_id,sinf_daraja,hafta_kuni,izoh,faol)
                VALUES(%s,%s,6,%s,TRUE)""",
                (maktab_id, grade, "Boshlang'ich parallel uchun Shanba kuni dars yo'q"))
    cur.execute("""INSERT INTO aqlli_sinf_kun_blok_seed_v2(maktab_id,versiya)
                   VALUES(%s,1) ON CONFLICT(maktab_id) DO NOTHING""", (maktab_id,))


def _v1856_class_day_rule_rows(cur, maktab_id: int):
    _v1856_seed_default_class_day_rules(cur, maktab_id)
    cur.execute("""SELECT b.*,s.sinf,s.harf
                   FROM aqlli_sinf_kun_bloklari_v2 b
                   LEFT JOIN maktab_sinflari s ON s.id=b.sinf_id
                   WHERE b.maktab_id=%s AND b.faol=TRUE
                   ORDER BY COALESCE(b.sinf_daraja,999),s.sinf::int NULLS LAST,s.harf,b.hafta_kuni""",
                (maktab_id,))
    rows = cur.fetchall()
    for row in rows:
        day_name = _V1852_HAFTA.get(int(row["hafta_kuni"]), str(row["hafta_kuni"]))
        if row.get("sinf_id") is not None:
            row["qamrov"] = "sinf"
            row["yorliq"] = f"{row.get('sinf','')}-{row.get('harf','')} · {day_name}"
        else:
            row["qamrov"] = "parallel"
            row["yorliq"] = f"Barcha {row.get('sinf_daraja')}-sinflar · {day_name}"
    return rows


def _v1856_class_day_rule_map(rows):
    exact = set()
    grades = set()
    for row in rows or []:
        day = int(row.get("hafta_kuni") or 0)
        if row.get("sinf_id") is not None:
            exact.add((int(row["sinf_id"]), day))
        elif row.get("sinf_daraja") is not None:
            grades.add((int(row["sinf_daraja"]), day))
    return {"exact": exact, "grades": grades, "rows": rows or []}


def _v1856_class_day_block_reason(class_row, day: int, rule_map):
    class_id = int((class_row or {}).get("id") or 0)
    grade = _v1855_sinf_raqami((class_row or {}).get("sinf"))
    day_name = _V1852_HAFTA.get(int(day), str(day))
    if (class_id, int(day)) in rule_map.get("exact", set()):
        return f"{(class_row or {}).get('sinf','')}-{(class_row or {}).get('harf','')} uchun {day_name} kuni dars bloklangan"
    if grade is not None and (grade, int(day)) in rule_map.get("grades", set()):
        return f"Barcha {grade}-sinflar uchun {day_name} kuni dars bloklangan"
    return None


def _v1856_schedule_block_violations(cur, maktab_id: int, run_id: int | None = None):
    _v1856_seed_default_class_day_rules(cur, maktab_id)
    if run_id is None:
        run = _v1852_active_run(cur, maktab_id)
        if not run:
            return []
        run_id = int(run["id"])
    cur.execute("""SELECT s.id AS sinf_id,s.sinf,s.harf,e.hafta_kuni,
                          COUNT(DISTINCT e.id) AS dars_soni
                   FROM aqlli_jadval_slotlari_v2 e
                   JOIN maktab_sinflari s ON s.id=e.sinf_id
                   JOIN aqlli_sinf_kun_bloklari_v2 b
                     ON b.maktab_id=e.maktab_id AND b.faol=TRUE
                    AND b.hafta_kuni=e.hafta_kuni
                    AND (b.sinf_id=e.sinf_id OR
                         (b.sinf_id IS NULL AND b.sinf_daraja=
                          NULLIF(REGEXP_REPLACE(COALESCE(s.sinf,''),'[^0-9]','','g'),'')::int))
                   WHERE e.maktab_id=%s AND e.urinish_id=%s
                   GROUP BY s.id,s.sinf,s.harf,e.hafta_kuni
                   ORDER BY s.sinf::int,s.harf,e.hafta_kuni""", (maktab_id, run_id))
    rows = cur.fetchall()
    for row in rows:
        row["kun_nomi"] = _V1852_HAFTA.get(int(row["hafta_kuni"]), str(row["hafta_kuni"]))
    return rows


def _v1852_create_tables(cur):
    global _V1852_TABLES_READY
    _rejalashtirish_jadvallari(cur)
    _maktab_sinflari_jadvali(cur)
    _xodim_sinf_birikmalari_jadvali(cur)
    _maktab_fanlari_jadvali(cur)
    cur.execute("ALTER TABLE maktab_sinflari ADD COLUMN IF NOT EXISTS smena INTEGER DEFAULT 1")
    cur.execute("ALTER TABLE maktab_sinflari ADD COLUMN IF NOT EXISTS bino TEXT")
    cur.execute("ALTER TABLE maktab_sinflari ADD COLUMN IF NOT EXISTS xona TEXT")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS haftalik_dars_soati INTEGER")

    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_oquv_yillari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        nomi TEXT NOT NULL,
        boshlanish DATE NOT NULL,
        tugash DATE NOT NULL,
        hafta_kunlari INTEGER NOT NULL DEFAULT 6 CHECK(hafta_kunlari IN (5,6)),
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        yaratgan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(maktab_id,nomi)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_choraklar_v2(
        id BIGSERIAL PRIMARY KEY,
        oquv_yili_id BIGINT NOT NULL REFERENCES aqlli_oquv_yillari_v2(id) ON DELETE CASCADE,
        chorak INTEGER NOT NULL CHECK(chorak BETWEEN 1 AND 4),
        boshlanish DATE NOT NULL,
        tugash DATE NOT NULL,
        holat TEXT NOT NULL DEFAULT 'taxminiy' CHECK(holat IN ('taxminiy','tasdiqlangan')),
        UNIQUE(oquv_yili_id,chorak)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_kalendar_kunlari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sana DATE NOT NULL,
        turi TEXT NOT NULL CHECK(turi IN ('oqish','dam','bayram','tatil','qoshimcha_dam','qoshimcha_oqish')),
        nomi TEXT,
        holat TEXT NOT NULL DEFAULT 'taxminiy' CHECK(holat IN ('taxminiy','tasdiqlangan')),
        izoh TEXT,
        yaratgan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(maktab_id,sana)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_smena_sozlamalari_v2(
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        smena INTEGER NOT NULL CHECK(smena IN (1,2)),
        dars_soni INTEGER NOT NULL DEFAULT 7 CHECK(dars_soni BETWEEN 1 AND 12),
        boshlanish_vaqti TIME NOT NULL,
        dars_daqiqa INTEGER NOT NULL DEFAULT 45 CHECK(dars_daqiqa BETWEEN 20 AND 90),
        tanaffus_daqiqa INTEGER NOT NULL DEFAULT 5 CHECK(tanaffus_daqiqa BETWEEN 0 AND 40),
        katta_tanaffus_darsdan_keyin INTEGER CHECK(katta_tanaffus_darsdan_keyin BETWEEN 1 AND 11),
        katta_tanaffus_daqiqa INTEGER NOT NULL DEFAULT 15 CHECK(katta_tanaffus_daqiqa BETWEEN 0 AND 60),
        PRIMARY KEY(maktab_id,smena)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_xonalar_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        nomi TEXT NOT NULL,
        turi TEXT NOT NULL DEFAULT 'oddiy',
        sigim INTEGER,
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        UNIQUE(maktab_id,nomi)
    )""")
    cur.execute("ALTER TABLE aqlli_xonalar_v2 ADD COLUMN IF NOT EXISTS manba_xona_id BIGINT")
    cur.execute("ALTER TABLE aqlli_xonalar_v2 ADD COLUMN IF NOT EXISTS bino_id BIGINT")
    cur.execute("ALTER TABLE aqlli_xonalar_v2 ADD COLUMN IF NOT EXISTS darsga_yaroqli BOOLEAN NOT NULL DEFAULT TRUE")
    cur.execute("UPDATE aqlli_xonalar_v2 SET turi='reserve' WHERE turi='maxsus'")
    cur.execute("UPDATE aqlli_xonalar_v2 SET turi='classroom' WHERE turi='oddiy'")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_oqituvchi_vaqti_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        hafta_kuni INTEGER NOT NULL CHECK(hafta_kuni BETWEEN 1 AND 7),
        smena INTEGER NOT NULL DEFAULT 0 CHECK(smena BETWEEN 0 AND 2),
        dars_raqami INTEGER NOT NULL DEFAULT 0 CHECK(dars_raqami BETWEEN 0 AND 12),
        turi TEXT NOT NULL CHECK(turi IN ('band','afzal_bosh','metod_kuni')),
        qattiq BOOLEAN NOT NULL DEFAULT TRUE,
        izoh TEXT,
        UNIQUE(maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_oqituvchi_qoidalari_v2(
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        kunlik_max INTEGER NOT NULL DEFAULT 6 CHECK(kunlik_max BETWEEN 1 AND 12),
        ketma_ket_max INTEGER NOT NULL DEFAULT 4 CHECK(ketma_ket_max BETWEEN 1 AND 12),
        okno_max INTEGER NOT NULL DEFAULT 1 CHECK(okno_max BETWEEN 0 AND 6),
        afzal_smena INTEGER NOT NULL DEFAULT 0 CHECK(afzal_smena BETWEEN 0 AND 2),
        eng_erta_dars INTEGER NOT NULL DEFAULT 1 CHECK(eng_erta_dars BETWEEN 1 AND 12),
        eng_kech_dars INTEGER NOT NULL DEFAULT 12 CHECK(eng_kech_dars BETWEEN 1 AND 12),
        PRIMARY KEY(maktab_id,user_id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_sinf_fan_yuklamalari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        fan_nomi TEXT NOT NULL,
        haftalik_soat INTEGER NOT NULL DEFAULT 0 CHECK(haftalik_soat BETWEEN 0 AND 20),
        kunlik_max INTEGER NOT NULL DEFAULT 1 CHECK(kunlik_max BETWEEN 1 AND 4),
        ketma_ket_mumkin BOOLEAN NOT NULL DEFAULT FALSE,
        afzal_oxirgi_dars INTEGER NOT NULL DEFAULT 5 CHECK(afzal_oxirgi_dars BETWEEN 1 AND 12),
        asosiy_oqituvchi_user_id BIGINT REFERENCES users(user_id),
        xona_id BIGINT REFERENCES aqlli_xonalar_v2(id),
        nazorat_soni INTEGER NOT NULL DEFAULT 0 CHECK(nazorat_soni BETWEEN 0 AND 10),
        nazoratdan_keyin_tahlil BOOLEAN NOT NULL DEFAULT TRUE,
        mustahkamlash_soni INTEGER NOT NULL DEFAULT 0 CHECK(mustahkamlash_soni BETWEEN 0 AND 20),
        ogirlik INTEGER NOT NULL DEFAULT 2 CHECK(ogirlik BETWEEN 1 AND 3),
        UNIQUE(maktab_id,sinf_id,fan_nomi)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_guruh_sozlamalari_v2(
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        fan_nomi TEXT NOT NULL,
        guruh_kaliti TEXT NOT NULL,
        oqituvchi_user_id BIGINT REFERENCES users(user_id),
        xona_id BIGINT REFERENCES aqlli_xonalar_v2(id),
        PRIMARY KEY(maktab_id,sinf_id,fan_nomi,guruh_kaliti)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_jadval_urinishlari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        holat TEXT NOT NULL DEFAULT 'draft' CHECK(holat IN ('draft','tasdiqlangan','almashtirilgan','bekor')),
        yaratgan_user_id BIGINT,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        tasdiqlangan_at TIMESTAMPTZ,
        sifat INTEGER NOT NULL DEFAULT 0,
        joylashtirildi INTEGER NOT NULL DEFAULT 0,
        joylashtirilmadi INTEGER NOT NULL DEFAULT 0,
        diagnostika JSONB NOT NULL DEFAULT '{}'::jsonb,
        sozlamalar JSONB NOT NULL DEFAULT '{}'::jsonb
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_jadval_slotlari_v2(
        id BIGSERIAL PRIMARY KEY,
        urinish_id BIGINT NOT NULL REFERENCES aqlli_jadval_urinishlari_v2(id) ON DELETE CASCADE,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        hafta_kuni INTEGER NOT NULL CHECK(hafta_kuni BETWEEN 1 AND 7),
        smena INTEGER NOT NULL CHECK(smena IN (1,2)),
        dars_raqami INTEGER NOT NULL CHECK(dars_raqami BETWEEN 1 AND 12),
        fan_nomi TEXT NOT NULL,
        oqituvchi_user_id BIGINT REFERENCES users(user_id),
        guruh_kaliti TEXT NOT NULL DEFAULT 'whole',
        xona_id BIGINT REFERENCES aqlli_xonalar_v2(id),
        xona_matni TEXT,
        boshlanish_vaqti TEXT,
        tugash_vaqti TEXT,
        yuklama_id BIGINT REFERENCES aqlli_sinf_fan_yuklamalari_v2(id),
        takror_raqami INTEGER NOT NULL DEFAULT 1,
        UNIQUE(urinish_id,sinf_id,hafta_kuni,smena,dars_raqami,guruh_kaliti)
    )""")
    # 0,5 soat — yarimta dars emas: bitta slotda toq/juft haftalar
    # almashadi. Ikki aylanish qatori bir xil kun va dars raqamida
    # qonuniy saqlanishi uchun hafta turi unikal kalitga kiradi.
    cur.execute("""ALTER TABLE aqlli_jadval_slotlari_v2
                   ADD COLUMN IF NOT EXISTS hafta_turi TEXT NOT NULL DEFAULT 'har_hafta'""")
    cur.execute("""DO $$
        DECLARE constraint_name TEXT;
        BEGIN
          FOR constraint_name IN
            SELECT c.conname
            FROM pg_constraint c
            JOIN pg_class t ON t.oid=c.conrelid
            WHERE t.relname='aqlli_jadval_slotlari_v2'
              AND c.contype='u'
              AND pg_get_constraintdef(c.oid) ILIKE '%urinish_id%sinf_id%hafta_kuni%smena%dars_raqami%guruh_kaliti%'
          LOOP
            EXECUTE format('ALTER TABLE aqlli_jadval_slotlari_v2 DROP CONSTRAINT %I', constraint_name);
          END LOOP;
        END $$""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_aqlli_slot_rotation_v2
                   ON aqlli_jadval_slotlari_v2(
                     urinish_id,sinf_id,hafta_kuni,smena,dars_raqami,guruh_kaliti,hafta_turi
                   )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_mavzu_rejalari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        fan_nomi TEXT NOT NULL,
        chorak INTEGER NOT NULL CHECK(chorak BETWEEN 1 AND 4),
        tartib INTEGER NOT NULL,
        mavzu TEXT NOT NULL,
        soat INTEGER NOT NULL DEFAULT 1 CHECK(soat BETWEEN 1 AND 10),
        turi TEXT NOT NULL DEFAULT 'mavzu' CHECK(turi IN ('mavzu','nazorat','xato_tahlil','mustahkamlash','masala')),
        topic_code TEXT,
        manba TEXT NOT NULL DEFAULT 'qolda' CHECK(manba IN ('qolda','dts')),
        UNIQUE(maktab_id,sinf_id,fan_nomi,chorak,tartib)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_mavzu_taqvimi_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        urinish_id BIGINT REFERENCES aqlli_jadval_urinishlari_v2(id) ON DELETE SET NULL,
        slot_id BIGINT REFERENCES aqlli_jadval_slotlari_v2(id) ON DELETE SET NULL,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        fan_nomi TEXT NOT NULL,
        chorak INTEGER NOT NULL CHECK(chorak BETWEEN 1 AND 4),
        sana DATE NOT NULL,
        hafta_kuni INTEGER NOT NULL,
        smena INTEGER NOT NULL,
        dars_raqami INTEGER NOT NULL,
        tartib INTEGER NOT NULL,
        mavzu TEXT NOT NULL,
        turi TEXT NOT NULL DEFAULT 'mavzu',
        manba TEXT NOT NULL DEFAULT 'avto' CHECK(manba IN ('avto','oqituvchi')),
        qulflangan BOOLEAN NOT NULL DEFAULT FALSE,
        oqituvchi_user_id BIGINT,
        UNIQUE(maktab_id,sinf_id,fan_nomi,chorak,sana,smena,dars_raqami)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_jadval_ozgartirish_sorovlari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        slot_id BIGINT NOT NULL REFERENCES aqlli_jadval_slotlari_v2(id) ON DELETE CASCADE,
        soragan_user_id BIGINT NOT NULL REFERENCES users(user_id),
        yangi_hafta_kuni INTEGER NOT NULL,
        yangi_smena INTEGER NOT NULL,
        yangi_dars_raqami INTEGER NOT NULL,
        izoh TEXT,
        holat TEXT NOT NULL DEFAULT 'kutilmoqda' CHECK(holat IN ('kutilmoqda','tasdiqlandi','rad_etildi')),
        korib_chiqgan_user_id BIGINT,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aqlli_kalendar_v2 ON aqlli_kalendar_kunlari_v2(maktab_id,sana)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aqlli_slot_teacher_v2 ON aqlli_jadval_slotlari_v2(urinish_id,oqituvchi_user_id,hafta_kuni,dars_raqami)")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_sinf_kun_bloklari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        sinf_daraja INTEGER,
        hafta_kuni INTEGER NOT NULL CHECK(hafta_kuni BETWEEN 1 AND 6),
        izoh TEXT,
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        yaratgan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CHECK ((sinf_id IS NOT NULL AND sinf_daraja IS NULL) OR
               (sinf_id IS NULL AND sinf_daraja BETWEEN 1 AND 11))
    )""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_aqlli_sinf_kun_blok_exact_v2
                   ON aqlli_sinf_kun_bloklari_v2(maktab_id,sinf_id,hafta_kuni)
                   WHERE sinf_id IS NOT NULL""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_aqlli_sinf_kun_blok_parallel_v2
                   ON aqlli_sinf_kun_bloklari_v2(maktab_id,sinf_daraja,hafta_kuni)
                   WHERE sinf_daraja IS NOT NULL""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_sinf_kun_blok_seed_v2(
        maktab_id INTEGER PRIMARY KEY REFERENCES maktablar(id) ON DELETE CASCADE,
        versiya INTEGER NOT NULL DEFAULT 1,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aqlli_slot_class_v2 ON aqlli_jadval_slotlari_v2(urinish_id,sinf_id,hafta_kuni,dars_raqami)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aqlli_topic_calendar_v2 ON aqlli_mavzu_taqvimi_v2(maktab_id,sinf_id,fan_nomi,chorak,sana)")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_sinf_soati_qoidalari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        hafta_kuni INTEGER NOT NULL CHECK(hafta_kuni BETWEEN 1 AND 6),
        dars_raqami INTEGER NOT NULL CHECK(dars_raqami BETWEEN 1 AND 12),
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        yaratgan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(maktab_id,sinf_id)
    )""")
    cur.execute("ALTER TABLE aqlli_sinf_soati_qoidalari_v2 ADD COLUMN IF NOT EXISTS fan_nomi TEXT NOT NULL DEFAULT 'KELAJAK SOATI'")
    cur.execute("ALTER TABLE aqlli_sinf_soati_qoidalari_v2 ADD COLUMN IF NOT EXISTS haftalik_soat INTEGER NOT NULL DEFAULT 1")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aqlli_sinf_soati_v2 ON aqlli_sinf_soati_qoidalari_v2(maktab_id,hafta_kuni,dars_raqami)")
    _V1852_TABLES_READY = True


def _v1852_tables(cur):
    if _V1852_TABLES_READY:
        return
    with _V1852_TABLES_LOCK:
        if not _V1852_TABLES_READY:
            _v1852_create_tables(cur)


@app.on_event("startup")
def _v1852_startup_tables():
    global _V1852_TABLES_READY
    try:
        conn = _db(); cur = conn.cursor()
        _v1852_create_tables(cur)
        conn.commit(); cur.close(); conn.close()
        _V1852_TABLES_READY = True
    except Exception as exc:
        _V1852_TABLES_READY = False
        print(f"[V18.52 jadval jadvallari] {exc}")


def _v1852_manager(cur, user_id: int, maktab_id: int) -> bool:
    # _maktab_boshqaruvchi_mi umumiy adminni ham tekshiradi.
    return _maktab_boshqaruvchi_mi(cur, user_id, maktab_id)


def _v1852_staff(cur, user_id: int, maktab_id: int) -> bool:
    return _v1852_manager(cur, user_id, maktab_id) or _maktab_xodimi_mi(cur, user_id, maktab_id)


def _v1852_teacher_subject_allowed(cur, user_id: int, maktab_id: int, sinf_id: int, fan: str) -> bool:
    if _v1852_manager(cur, user_id, maktab_id):
        return True
    cur.execute("""SELECT 1 FROM maktab_dars_birikmalari
                   WHERE maktab_id=%s AND user_id=%s AND sinf_id=%s
                     AND LOWER(TRIM(fan_nomi))=LOWER(TRIM(%s)) LIMIT 1""",
                (maktab_id, user_id, sinf_id, fan))
    return cur.fetchone() is not None


def _v1852_time_str(value) -> str:
    return value.strftime("%H:%M") if hasattr(value, "strftime") else str(value or "")[:5]


def _v1852_shift_slots(row: dict) -> list[dict]:
    start_text = _v1852_time_str(row.get("boshlanish_vaqti") or "08:00")
    current = datetime.strptime(start_text, "%H:%M")
    count = int(row.get("dars_soni") or 7)
    lesson = int(row.get("dars_daqiqa") or 45)
    normal_break = int(row.get("tanaffus_daqiqa") or 5)
    big_after = row.get("katta_tanaffus_darsdan_keyin")
    big_break = int(row.get("katta_tanaffus_daqiqa") or 15)
    result = []
    for number in range(1, count + 1):
        end = current + timedelta(minutes=lesson)
        result.append({"dars_raqami": number, "boshlanish": current.strftime("%H:%M"), "tugash": end.strftime("%H:%M")})
        if number < count:
            pause = big_break if big_after and number == int(big_after) else normal_break
            current = end + timedelta(minutes=pause)
    return result


def _v1852_default_shifts(cur, maktab_id: int):
    defaults = [
        (1, 7, "08:00", 45, 5, 3, 15),
        (2, 7, "13:30", 45, 5, 3, 15),
    ]
    for smena, dars_soni, start, lesson, pause, big_after, big_pause in defaults:
        cur.execute("""INSERT INTO aqlli_smena_sozlamalari_v2(
            maktab_id,smena,dars_soni,boshlanish_vaqti,dars_daqiqa,tanaffus_daqiqa,
            katta_tanaffus_darsdan_keyin,katta_tanaffus_daqiqa)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(maktab_id,smena) DO NOTHING""",
            (maktab_id, smena, dars_soni, start, lesson, pause, big_after, big_pause))


def _v1852_active_year(cur, maktab_id: int):
    cur.execute("SELECT * FROM aqlli_oquv_yillari_v2 WHERE maktab_id=%s AND faol=TRUE ORDER BY id DESC LIMIT 1", (maktab_id,))
    return cur.fetchone()


def _v1890_generation_year(cur, maktab_id: int):
    """Jadval uchun o'quv yilini majburiy qilmaydigan ichki vaqt oralig'i."""
    year = _v1852_active_year(cur, maktab_id)
    if year:
        return year
    today = date.today()
    start_year = today.year if today.month >= 7 else today.year - 1
    start = date(start_year, 9, 1)
    end = date(start_year + 1, 5, 31)
    name = f"__JADVAL_VAQTINCHA_{start_year}_{start_year + 1}__"
    cur.execute("""INSERT INTO aqlli_oquv_yillari_v2(
        maktab_id,nomi,boshlanish,tugash,hafta_kunlari,faol,yangilangan_at)
        VALUES(%s,%s,%s,%s,6,TRUE,NOW())
        ON CONFLICT(maktab_id,nomi) DO UPDATE SET faol=TRUE,yangilangan_at=NOW()
        RETURNING *""", (maktab_id, name, start, end))
    year = cur.fetchone()
    quarters = [
        (1, start, date(start_year, 10, 31)),
        (2, date(start_year, 11, 1), date(start_year, 12, 31)),
        (3, date(start_year + 1, 1, 1), date(start_year + 1, 3, 31)),
        (4, date(start_year + 1, 4, 1), end),
    ]
    for number, q_start, q_end in quarters:
        cur.execute("""INSERT INTO aqlli_choraklar_v2(
            oquv_yili_id,chorak,boshlanish,tugash,holat)
            VALUES(%s,%s,%s,%s,'taxminiy')
            ON CONFLICT(oquv_yili_id,chorak) DO NOTHING""",
            (year["id"], number, q_start, q_end))
    return year


def _v1852_active_run(cur, maktab_id: int):
    cur.execute("SELECT * FROM aqlli_jadval_urinishlari_v2 WHERE maktab_id=%s AND holat='tasdiqlangan' ORDER BY id DESC LIMIT 1", (maktab_id,))
    return cur.fetchone()


def _v1852_is_school_day(cur, maktab_id: int, sana: date, weekdays: int) -> bool:
    cur.execute("SELECT turi FROM aqlli_kalendar_kunlari_v2 WHERE maktab_id=%s AND sana=%s", (maktab_id, sana))
    row = cur.fetchone()
    if row:
        return row["turi"] in _V1852_OQISH_TURLARI
    return sana.isoweekday() <= weekdays


def _v1852_quarter_for_date(cur, year_id: int, sana: date):
    cur.execute("SELECT chorak FROM aqlli_choraklar_v2 WHERE oquv_yili_id=%s AND %s BETWEEN boshlanish AND tugash", (year_id, sana))
    row = cur.fetchone()
    return int(row["chorak"]) if row else None


def _v1852_validate_quarters(start: date, end: date, quarters: list[dict]):
    parsed = []
    seen = set()
    for item in quarters:
        number = int(item.get("chorak") or 0)
        if number not in (1, 2, 3, 4) or number in seen:
            raise HTTPException(status_code=400, detail="Choraklar 1, 2, 3, 4 bo'lib takrorlanmasligi kerak")
        seen.add(number)
        try:
            q_start = date.fromisoformat(str(item.get("boshlanish")))
            q_end = date.fromisoformat(str(item.get("tugash")))
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"{number}-chorak sanasi noto'g'ri") from exc
        status = str(item.get("holat") or "taxminiy")
        if status not in _V1852_HOLATLAR or q_end < q_start:
            raise HTTPException(status_code=400, detail=f"{number}-chorak sanasi/holatini tekshiring")
        if q_start < start or q_end > end:
            raise HTTPException(status_code=400, detail=f"{number}-chorak o'quv yili chegarasidan chiqdi")
        parsed.append((number, q_start, q_end, status))
    if seen != {1, 2, 3, 4}:
        raise HTTPException(status_code=400, detail="Barcha 4 chorakni kiriting")
    parsed.sort(key=lambda x: x[0])
    for current, following in zip(parsed, parsed[1:]):
        if following[1] <= current[2]:
            raise HTTPException(status_code=400, detail=f"{current[0]} va {following[0]}-chorak sanalari ustma-ust tushdi")
    return parsed


def _v1852_previous_weekday(value: date, max_weekday: int = 6):
    result = value
    while result.isoweekday() > max_weekday:
        result -= timedelta(days=1)
    return result


def _v1852_next_weekday(value: date, max_weekday: int = 6):
    result = value
    while result.isoweekday() > max_weekday:
        result += timedelta(days=1)
    return result


def _v1852_suggest_calendar(start: date, end: date, weekdays: int):
    max_day = 5 if weekdays == 5 else 6
    year = start.year
    q1_end = _v1852_previous_weekday(date(year, 10, 31), max_day)
    q2_start = _v1852_next_weekday(q1_end + timedelta(days=7), max_day)
    q2_end = _v1852_previous_weekday(date(year, 12, 27), max_day)
    q3_start = _v1852_next_weekday(date(year + 1, 1, 11), max_day)
    q3_end = _v1852_previous_weekday(date(year + 1, 3, 20), max_day)
    q4_start = _v1852_next_weekday(q3_end + timedelta(days=8), max_day)
    boundaries = [
        (1, start, min(q1_end, end)),
        (2, max(q2_start, start), min(q2_end, end)),
        (3, max(q3_start, start), min(q3_end, end)),
        (4, max(q4_start, start), end),
    ]
    # Juda qisqa yoki noodatiy o'quv yili bo'lsa teng bo'lib taqsimlaymiz.
    if any(qe < qs for _, qs, qe in boundaries):
        total = max(4, (end - start).days + 1)
        step = total // 4
        boundaries = []
        cursor = start
        for number in range(1, 5):
            q_end = end if number == 4 else min(end, cursor + timedelta(days=step - 1))
            boundaries.append((number, cursor, q_end))
            cursor = q_end + timedelta(days=1)
    holidays = []
    common = [
        (1, 1, "Yangi yil"), (3, 8, "Xotin-qizlar kuni"), (3, 21, "Navro'z"),
        (5, 9, "Xotira va qadrlash kuni"), (9, 1, "Mustaqillik kuni"),
        (10, 1, "O'qituvchi va murabbiylar kuni"), (12, 8, "Konstitutsiya kuni"),
    ]
    for yy in range(start.year, end.year + 1):
        for month, day, name in common:
            try:
                d = date(yy, month, day)
            except ValueError:
                continue
            if start <= d <= end:
                holidays.append({"sana": d.isoformat(), "turi": "bayram", "nomi": name, "holat": "taxminiy"})
    return {
        "choraklar": [
            {"chorak": n, "boshlanish": qs.isoformat(), "tugash": qe.isoformat(), "holat": "taxminiy"}
            for n, qs, qe in boundaries
        ],
        "maxsus_kunlar": holidays,
        "ogohlantirish": "Bu sanalar faqat taxminiy tavsiya. Rasmiy kalendar/Kundalik bilan tekshirib tasdiqlang.",
    }


class V1852CalendarSuggest(BaseModel):
    boshlanish: date
    tugash: date
    hafta_kunlari: int = 6


@app.post("/api/maktab/aqlli_jadval/v2/kalendar_tavsiya")
def v1852_calendar_suggest(sorov: V1852CalendarSuggest, token: str):
    _jwt_tekshir(token)
    if sorov.hafta_kunlari not in (5, 6) or sorov.tugash <= sorov.boshlanish:
        raise HTTPException(status_code=400, detail="Sanalarni va 5/6 kunlik haftani tekshiring")
    return _v1852_suggest_calendar(sorov.boshlanish, sorov.tugash, sorov.hafta_kunlari)


class V1852CalendarSave(BaseModel):
    maktab_id: int
    nomi: str
    boshlanish: date
    tugash: date
    hafta_kunlari: int = 6
    choraklar: list[dict]
    smenalar: list[dict] = []


@app.put("/api/maktab/aqlli_jadval/v2/kalendar")
def v1852_calendar_save(sorov: V1852CalendarSave, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Kalendarni faqat maktab rahbariyati boshqaradi")
        if sorov.hafta_kunlari not in (5, 6) or sorov.tugash <= sorov.boshlanish:
            raise HTTPException(status_code=400, detail="O'quv yili sanalarini tekshiring")
        quarters = _v1852_validate_quarters(sorov.boshlanish, sorov.tugash, sorov.choraklar)
        cur.execute("UPDATE aqlli_oquv_yillari_v2 SET faol=FALSE WHERE maktab_id=%s AND nomi<>%s", (sorov.maktab_id, sorov.nomi.strip()))
        cur.execute("""INSERT INTO aqlli_oquv_yillari_v2(
            maktab_id,nomi,boshlanish,tugash,hafta_kunlari,faol,yaratgan_user_id,yangilangan_at)
            VALUES(%s,%s,%s,%s,%s,TRUE,%s,NOW())
            ON CONFLICT(maktab_id,nomi) DO UPDATE SET boshlanish=EXCLUDED.boshlanish,
              tugash=EXCLUDED.tugash,hafta_kunlari=EXCLUDED.hafta_kunlari,
              faol=TRUE,yaratgan_user_id=EXCLUDED.yaratgan_user_id,yangilangan_at=NOW()
            RETURNING id""", (sorov.maktab_id, sorov.nomi.strip(), sorov.boshlanish,
                                sorov.tugash, sorov.hafta_kunlari, user_id))
        year_id = cur.fetchone()["id"]
        cur.execute("DELETE FROM aqlli_choraklar_v2 WHERE oquv_yili_id=%s", (year_id,))
        psycopg2.extras.execute_values(cur,
            "INSERT INTO aqlli_choraklar_v2(oquv_yili_id,chorak,boshlanish,tugash,holat) VALUES %s",
            [(year_id, number, start, end, status) for number, start, end, status in quarters])
        _v1852_default_shifts(cur, sorov.maktab_id)
        for shift in sorov.smenalar:
            smena = int(shift.get("smena") or 0)
            if smena not in (1, 2):
                raise HTTPException(status_code=400, detail="Smena 1 yoki 2 bo'lishi kerak")
            cur.execute("""INSERT INTO aqlli_smena_sozlamalari_v2(
                maktab_id,smena,dars_soni,boshlanish_vaqti,dars_daqiqa,tanaffus_daqiqa,
                katta_tanaffus_darsdan_keyin,katta_tanaffus_daqiqa)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(maktab_id,smena) DO UPDATE SET dars_soni=EXCLUDED.dars_soni,
                  boshlanish_vaqti=EXCLUDED.boshlanish_vaqti,dars_daqiqa=EXCLUDED.dars_daqiqa,
                  tanaffus_daqiqa=EXCLUDED.tanaffus_daqiqa,
                  katta_tanaffus_darsdan_keyin=EXCLUDED.katta_tanaffus_darsdan_keyin,
                  katta_tanaffus_daqiqa=EXCLUDED.katta_tanaffus_daqiqa""",
                (sorov.maktab_id, smena, int(shift.get("dars_soni") or 7),
                 str(shift.get("boshlanish_vaqti") or ("08:00" if smena == 1 else "13:30")),
                 int(shift.get("dars_daqiqa") or 45), int(shift.get("tanaffus_daqiqa") or 5),
                 int(shift.get("katta_tanaffus_darsdan_keyin") or 3),
                 int(shift.get("katta_tanaffus_daqiqa") or 15)))
        conn.commit()
        return {"holat": "saqlandi", "oquv_yili_id": year_id}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def _v1852_rebuild_all_topic_calendars(cur, maktab_id: int):
    cur.execute("""SELECT DISTINCT maktab_id,sinf_id,fan_nomi,chorak
                   FROM aqlli_mavzu_rejalari_v2 WHERE maktab_id=%s""", (maktab_id,))
    groups = cur.fetchall()
    rebuilt = 0
    warnings = []
    for group in groups:
        result = _v1852_distribute_topics_one(cur, maktab_id, group["sinf_id"], group["fan_nomi"], group["chorak"])
        rebuilt += 1
        warnings.extend(result.get("ogohlantirishlar") or [])
    return {"qayta_taqsimlandi": rebuilt, "ogohlantirishlar": warnings[:50]}


class V1852SpecialDay(BaseModel):
    maktab_id: int
    sana: date
    turi: str
    nomi: Optional[str] = None
    holat: str = "tasdiqlangan"
    izoh: Optional[str] = None


@app.put("/api/maktab/aqlli_jadval/v2/maxsus_kun")
def v1852_special_day_save(sorov: V1852SpecialDay, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Maxsus kunni faqat maktab rahbariyati belgilaydi")
        if sorov.turi not in _V1852_KUN_TURLARI or sorov.holat not in _V1852_HOLATLAR:
            raise HTTPException(status_code=400, detail="Kun turi yoki holati noto'g'ri")
        cur.execute("""INSERT INTO aqlli_kalendar_kunlari_v2(
            maktab_id,sana,turi,nomi,holat,izoh,yaratgan_user_id,yangilangan_at)
            VALUES(%s,%s,%s,%s,%s,%s,%s,NOW())
            ON CONFLICT(maktab_id,sana) DO UPDATE SET turi=EXCLUDED.turi,nomi=EXCLUDED.nomi,
              holat=EXCLUDED.holat,izoh=EXCLUDED.izoh,yaratgan_user_id=EXCLUDED.yaratgan_user_id,
              yangilangan_at=NOW()""", (sorov.maktab_id, sorov.sana, sorov.turi,
                                          sorov.nomi, sorov.holat, sorov.izoh, user_id))
        rebuild = _v1852_rebuild_all_topic_calendars(cur, sorov.maktab_id)
        conn.commit()
        return {"holat": "saqlandi", **rebuild}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.delete("/api/maktab/aqlli_jadval/v2/maxsus_kun")
def v1852_special_day_delete(token: str, maktab_id: int, sana: date):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, maktab_id):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        cur.execute("DELETE FROM aqlli_kalendar_kunlari_v2 WHERE maktab_id=%s AND sana=%s", (maktab_id, sana))
        rebuild = _v1852_rebuild_all_topic_calendars(cur, maktab_id)
        conn.commit(); return {"holat": "o'chirildi", **rebuild}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V1852Room(BaseModel):
    maktab_id: int
    nomi: str
    turi: str = "classroom"
    sigim: Optional[int] = None


@app.post("/api/maktab/aqlli_jadval/v2/xona")
def v1852_room_save(sorov: V1852Room, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Xonani faqat maktab rahbariyati qo'shadi")
        name = re.sub(r"\s+", " ", sorov.nomi or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="Xona nomini kiriting")
        room_type = str(sorov.turi or "classroom").strip().lower()
        room_type = {"oddiy": "classroom", "maxsus": "reserve"}.get(room_type, room_type)
        if room_type not in {"classroom", "reserve", "sport", "non_teaching"}:
            raise HTTPException(status_code=400, detail="Xona turi noto'g'ri")
        teaching_enabled = room_type != "non_teaching"
        cur.execute("""INSERT INTO aqlli_xonalar_v2(
                         maktab_id,nomi,turi,sigim,faol,darsga_yaroqli)
                       VALUES(%s,%s,%s,%s,TRUE,%s)
                       ON CONFLICT(maktab_id,nomi) DO UPDATE SET turi=EXCLUDED.turi,
                         sigim=EXCLUDED.sigim,faol=TRUE,
                         darsga_yaroqli=EXCLUDED.darsga_yaroqli RETURNING id""",
                    (sorov.maktab_id, name, room_type, sorov.sigim, teaching_enabled))
        room_id = cur.fetchone()["id"]
        conn.commit(); return {"holat": "saqlandi", "xona_id": room_id}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V1852TeacherRules(BaseModel):
    kunlik_max: int = 6
    ketma_ket_max: int = 4
    okno_max: int = 1
    afzal_smena: int = 0
    eng_erta_dars: int = 1
    eng_kech_dars: int = 12


class V1852TeacherAvailability(BaseModel):
    maktab_id: int
    user_id: int
    qoidalar: V1852TeacherRules
    vaqtlar: list[dict] = []


@app.put("/api/maktab/aqlli_jadval/v2/oqituvchi_vaqti")
def v1852_teacher_availability_save(sorov: V1852TeacherAvailability, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if actor_id != sorov.user_id and not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Faqat o'qituvchining o'zi yoki rahbariyat o'zgartira oladi")
        cur.execute("SELECT 1 FROM users WHERE user_id=%s AND maktab_id=%s", (sorov.user_id, sorov.maktab_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="O'qituvchi shu maktabda topilmadi")
        rules = sorov.qoidalar
        if rules.eng_kech_dars < rules.eng_erta_dars:
            raise HTTPException(status_code=400, detail="Eng kech dars eng erta darsdan oldin bo'lmaydi")
        cur.execute("""INSERT INTO aqlli_oqituvchi_qoidalari_v2(
            maktab_id,user_id,kunlik_max,ketma_ket_max,okno_max,afzal_smena,eng_erta_dars,eng_kech_dars)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT(maktab_id,user_id) DO UPDATE SET kunlik_max=EXCLUDED.kunlik_max,
              ketma_ket_max=EXCLUDED.ketma_ket_max,okno_max=EXCLUDED.okno_max,
              afzal_smena=EXCLUDED.afzal_smena,eng_erta_dars=EXCLUDED.eng_erta_dars,
              eng_kech_dars=EXCLUDED.eng_kech_dars""",
            (sorov.maktab_id, sorov.user_id, rules.kunlik_max, rules.ketma_ket_max,
             rules.okno_max, rules.afzal_smena, rules.eng_erta_dars, rules.eng_kech_dars))
        cur.execute("DELETE FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s AND user_id=%s", (sorov.maktab_id, sorov.user_id))
        rows = []
        for item in sorov.vaqtlar:
            day = int(item.get("hafta_kuni") or 0)
            shift = int(item.get("smena") or 0)
            period = int(item.get("dars_raqami") or 0)
            kind = str(item.get("turi") or "")
            hard = bool(item.get("qattiq", True))
            if day not in range(1, 8) or shift not in (0, 1, 2) or period not in range(0, 13) or kind not in _V1852_VAQT_TURLARI:
                raise HTTPException(status_code=400, detail="O'qituvchi vaqtlaridan biri noto'g'ri")
            if kind == "metod_kuni":
                shift, period = 0, 0
                hard = True
            rows.append((sorov.maktab_id, sorov.user_id, day, shift, period, kind, hard, item.get("izoh")))
        if rows:
            psycopg2.extras.execute_values(cur,
                """INSERT INTO aqlli_oqituvchi_vaqti_v2(
                    maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi,qattiq,izoh) VALUES %s""", rows)
        conn.commit(); return {"holat": "saqlandi", "vaqt_soni": len(rows)}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.get("/api/maktab/aqlli_jadval/v2/mening_vaqtim")
def v1852_my_availability(token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        cur.execute("SELECT maktab_id,full_name FROM users WHERE user_id=%s", (user_id,))
        user = cur.fetchone()
        if not user or not user.get("maktab_id"):
            return {"maktab_id": None, "oqituvchi": None, "qoidalar": None, "vaqtlar": []}
        cur.execute("SELECT * FROM aqlli_oqituvchi_qoidalari_v2 WHERE maktab_id=%s AND user_id=%s", (user["maktab_id"], user_id))
        rules = cur.fetchone()
        cur.execute("SELECT * FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s AND user_id=%s ORDER BY hafta_kuni,smena,dars_raqami", (user["maktab_id"], user_id))
        times = cur.fetchall()
        return {"maktab_id": user["maktab_id"], "oqituvchi": user["full_name"], "qoidalar": rules, "vaqtlar": times}
    finally:
        cur.close(); conn.close()


class V1852LoadItem(BaseModel):
    fan_nomi: str
    haftalik_soat: float
    kunlik_max: int = 1
    ketma_ket_mumkin: bool = False
    afzal_oxirgi_dars: int = 5
    asosiy_oqituvchi_user_id: Optional[int] = None
    xona_id: Optional[int] = None
    nazorat_soni: int = 0
    nazoratdan_keyin_tahlil: bool = True
    mustahkamlash_soni: int = 0
    ogirlik: int = 2


class V1852ClassLoads(BaseModel):
    maktab_id: int
    sinf_id: int
    fanlar: list[V1852LoadItem]


@app.put("/api/maktab/aqlli_jadval/v2/fan_soatlari")
def v1852_loads_save(sorov: V1852ClassLoads, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Fan soatini faqat rahbariyat belgilaydi")
        cur.execute("SELECT 1 FROM maktab_sinflari WHERE id=%s AND maktab_id=%s", (sorov.sinf_id, sorov.maktab_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Sinf topilmadi")
        received = set()
        for item in sorov.fanlar:
            fan = re.sub(r"\s+", " ", item.fan_nomi or "").strip()
            if not fan:
                continue
            key = fan.casefold()
            if key in received:
                raise HTTPException(status_code=400, detail=f"'{fan}' ikki marta yuborilgan")
            received.add(key)
            cur.execute("""INSERT INTO aqlli_sinf_fan_yuklamalari_v2(
                maktab_id,sinf_id,fan_nomi,haftalik_soat,kunlik_max,ketma_ket_mumkin,
                afzal_oxirgi_dars,asosiy_oqituvchi_user_id,xona_id,nazorat_soni,
                nazoratdan_keyin_tahlil,mustahkamlash_soni,ogirlik)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT(maktab_id,sinf_id,fan_nomi) DO UPDATE SET
                  haftalik_soat=EXCLUDED.haftalik_soat,kunlik_max=EXCLUDED.kunlik_max,
                  ketma_ket_mumkin=EXCLUDED.ketma_ket_mumkin,
                  afzal_oxirgi_dars=EXCLUDED.afzal_oxirgi_dars,
                  asosiy_oqituvchi_user_id=EXCLUDED.asosiy_oqituvchi_user_id,
                  xona_id=EXCLUDED.xona_id,nazorat_soni=EXCLUDED.nazorat_soni,
                  nazoratdan_keyin_tahlil=EXCLUDED.nazoratdan_keyin_tahlil,
                  mustahkamlash_soni=EXCLUDED.mustahkamlash_soni,ogirlik=EXCLUDED.ogirlik""",
                (sorov.maktab_id, sorov.sinf_id, fan, item.haftalik_soat,
                 item.kunlik_max, item.ketma_ket_mumkin, item.afzal_oxirgi_dars,
                 item.asosiy_oqituvchi_user_id, item.xona_id, item.nazorat_soni,
                 item.nazoratdan_keyin_tahlil, item.mustahkamlash_soni, item.ogirlik))

            # Fan-soat oynasidagi o'zgarish exact DARS_BIRIKMALARI manbasiga ham yoziladi.
            cur.execute("""UPDATE maktab_dars_birikmalari
                           SET haftalik_soat=%s,kunlik_max=%s,manba='fan_soatlari_oynasi'
                           WHERE maktab_id=%s AND sinf_id=%s
                             AND LOWER(TRIM(fan_nomi))=LOWER(TRIM(%s))""",
                        (item.haftalik_soat, item.kunlik_max,
                         sorov.maktab_id, sorov.sinf_id, fan))
            if int(cur.rowcount or 0) == 0 and float(item.haftalik_soat or 0) > 0:
                if not item.asosiy_oqituvchi_user_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{fan}: avval aniq o'qituvchini biriktiring",
                    )
                cur.execute("""INSERT INTO maktab_dars_birikmalari(
                                maktab_id,user_id,sinf_id,fan_nomi,guruh_kaliti,
                                haftalik_soat,kunlik_max,manba)
                               VALUES(%s,%s,%s,%s,'whole',%s,%s,'fan_soatlari_oynasi')
                               ON CONFLICT(user_id,sinf_id,fan_nomi,guruh_kaliti)
                               DO UPDATE SET haftalik_soat=EXCLUDED.haftalik_soat,
                                             kunlik_max=EXCLUDED.kunlik_max,
                                             manba=EXCLUDED.manba""",
                            (sorov.maktab_id, item.asosiy_oqituvchi_user_id,
                             sorov.sinf_id, fan, item.haftalik_soat, item.kunlik_max))

        manba_mosligi = _v1875_rebuild_schedule_sources(
            cur, sorov.maktab_id, cancel_drafts=True, reason="fan_soatlari_oynasi"
        )
        if manba_mosligi.get("xatolar"):
            raise HTTPException(
                status_code=400,
                detail="Fan-soat manbasi xatolari: " + "; ".join(manba_mosligi["xatolar"][:12]),
            )
        conn.commit()
        return {"holat": "saqlandi", "fan_soni": len(received), "moslik": manba_mosligi}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V1852GroupSettingItem(BaseModel):
    fan_nomi: str
    guruh_kaliti: str
    oqituvchi_user_id: Optional[int] = None
    xona_id: Optional[int] = None


class V1852GroupSettings(BaseModel):
    maktab_id: int
    sinf_id: int
    guruhlar: list[V1852GroupSettingItem]


@app.put("/api/maktab/aqlli_jadval/v2/guruh_sozlamalari")
def v1852_group_settings_save(sorov: V1852GroupSettings, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Parallel guruhlarni faqat rahbariyat sozlaydi")
        cur.execute("DELETE FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s AND sinf_id=%s", (sorov.maktab_id, sorov.sinf_id))
        rows = []
        for item in sorov.guruhlar:
            fan = re.sub(r"\s+", " ", item.fan_nomi or "").strip()
            group_key = str(item.guruh_kaliti or "").strip()
            if not fan or not group_key or group_key == "whole":
                continue
            rows.append((sorov.maktab_id, sorov.sinf_id, fan, group_key, item.oqituvchi_user_id, item.xona_id))
        if rows:
            psycopg2.extras.execute_values(cur, """INSERT INTO aqlli_guruh_sozlamalari_v2(
                maktab_id,sinf_id,fan_nomi,guruh_kaliti,oqituvchi_user_id,xona_id) VALUES %s""", rows)
        conn.commit(); return {"holat": "saqlandi", "guruh_soni": len(rows)}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()



# V18.59 — shablonda tanlangan fanlarni bir joyga yig'ish.
# Eski importlarda fan users.fanlari, maktab_xodim_sinflari yoki
# maktab_dars_birikmalari jadvallaridan faqat bittasida qolgan bo'lishi mumkin.
def _v1859_fanlarni_ajrat(value):
    text = str(value or "").replace("\\n", "\n")
    result = []
    seen = set()
    for part in re.split(r"[;\n,]+", text):
        fan = re.sub(r"\s+", " ", str(part or "")).strip()
        if not fan:
            continue
        key = _xodim_excel_sarlavha_kaliti(fan)
        if key and key not in seen:
            seen.add(key)
            result.append(fan)
    return result


def _v1859_sinf_sort_key(label):
    match = re.match(r"^\s*(\d+)\s*[-–]?\s*(.*)$", str(label or ""))
    if not match:
        return (999, str(label or ""))
    return (int(match.group(1)), match.group(2).casefold())


def _v1859_effective_teachers(cur, maktab_id: int, user_ids=None):
    cur.execute("""SELECT u.user_id,u.full_name,u.lavozim,u.fanlari,
                          u.oqitadigan_sinflari,u.haftalik_dars_soati,
                          to_jsonb(u)->>'mutaxassisligi' AS mutaxassisligi,
                          NULLIF(to_jsonb(u)->>'haftalik_maqsad_soat','')::NUMERIC(5,1)
                              AS haftalik_maqsad_soat
                   FROM users u
                   WHERE u.maktab_id=%s AND u.lavozim IS NOT NULL
                   ORDER BY u.full_name,u.user_id""", (maktab_id,))
    rows = [dict(row) for row in cur.fetchall()]
    if user_ids:
        wanted = {int(x) for x in user_ids}
        rows = [row for row in rows if int(row["user_id"]) in wanted]
    by_id = {int(row["user_id"]): row for row in rows}
    fan_maps = {}
    class_maps = {}
    source_maps = {}
    assignment_counts = {}
    for uid, row in by_id.items():
        fan_maps[uid] = {}
        class_maps[uid] = set()
        source_maps[uid] = set()
        assignment_counts[uid] = 0
        for fan in _v1859_fanlarni_ajrat(row.get("fanlari")):
            fan_maps[uid][_xodim_excel_sarlavha_kaliti(fan)] = fan
            source_maps[uid].add("XODIMLAR shabloni")
        for class_name in _xodim_sinf_royxatini_ajrat(row.get("oqitadigan_sinflari")):
            class_maps[uid].add(class_name)

    if not by_id:
        return []

    cur.execute("""SELECT b.user_id,b.sinf_id,b.fan_nomi,b.guruh_kaliti,
                          s.sinf,s.harf
                   FROM maktab_dars_birikmalari b
                   JOIN maktab_sinflari s ON s.id=b.sinf_id
                   WHERE b.maktab_id=%s
                   ORDER BY b.user_id,s.sinf::int,s.harf,b.fan_nomi""", (maktab_id,))
    for link in cur.fetchall():
        uid = int(link["user_id"])
        if uid not in by_id:
            continue
        fan = re.sub(r"\s+", " ", str(link.get("fan_nomi") or "")).strip()
        if fan:
            fan_maps[uid][_xodim_excel_sarlavha_kaliti(fan)] = fan
            source_maps[uid].add("DARS_BIRIKMALARI")
        class_maps[uid].add(f"{link['sinf']}-{link['harf']}")
        assignment_counts[uid] += 1

    cur.execute("""SELECT x.user_id,x.sinf_id,x.fanlari,s.sinf,s.harf
                   FROM maktab_xodim_sinflari x
                   JOIN maktab_sinflari s ON s.id=x.sinf_id
                   WHERE x.maktab_id=%s
                   ORDER BY x.user_id,s.sinf::int,s.harf""", (maktab_id,))
    for link in cur.fetchall():
        uid = int(link["user_id"])
        if uid not in by_id:
            continue
        for fan in _v1859_fanlarni_ajrat(link.get("fanlari")):
            fan_maps[uid][_xodim_excel_sarlavha_kaliti(fan)] = fan
            source_maps[uid].add("Sinf–fan birikmasi")
        class_maps[uid].add(f"{link['sinf']}-{link['harf']}")

    # Faqat shu maktabning haqiqiy dars jarayoniga biriktirilgan xodimlari
    # jadval sozlamasida ko'rinadi. Eski importdan qolgan "Akaunt 1" kabi,
    # maktab_id yozilgan bo'lsa-da birorta fan/sinf/rahbarlikka ulanmagan
    # foydalanuvchi boshqa maktab jadvaliga aralashmaydi.
    cur.execute(
        "SELECT DISTINCT rahbar_user_id AS user_id FROM maktab_sinflari "
        "WHERE maktab_id=%s AND rahbar_user_id IS NOT NULL",
        (maktab_id,),
    )
    class_head_ids = {int(row["user_id"]) for row in cur.fetchall()}

    result = []
    for uid, row in by_id.items():
        subjects = sorted(fan_maps[uid].values(), key=lambda x: x.casefold())
        classes = sorted(class_maps[uid], key=_v1859_sinf_sort_key)
        row["fanlar_royxati"] = subjects
        row["fanlari"] = "\n".join(subjects) or None
        row["sinflar_royxati"] = classes
        row["sinflari"] = "; ".join(classes) or None
        row["fan_manbalari"] = sorted(source_maps[uid])
        row["dars_birikma_soni"] = int(assignment_counts[uid])
        row["dars_beruvchi"] = bool(
            subjects or classes or assignment_counts[uid] or uid in class_head_ids
        )
        row["fan_holati"] = "aniqlandi" if subjects else "fan_topilmadi"
        if row["dars_beruvchi"]:
            result.append(row)
    return result


def _v1852_setup_payload(cur, maktab_id: int):
    _v1852_default_shifts(cur, maktab_id)
    year = _v1852_active_year(cur, maktab_id)
    quarters = []
    if year:
        cur.execute("SELECT * FROM aqlli_choraklar_v2 WHERE oquv_yili_id=%s ORDER BY chorak", (year["id"],))
        quarters = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_kalendar_kunlari_v2 WHERE maktab_id=%s ORDER BY sana", (maktab_id,))
    special_days = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_smena_sozlamalari_v2 WHERE maktab_id=%s ORDER BY smena", (maktab_id,))
    shifts = cur.fetchall()
    for shift in shifts:
        shift["slotlar"] = _v1852_shift_slots(shift)
    cur.execute("""SELECT s.id,s.sinf,s.harf,COALESCE(s.smena,1) AS smena,s.bino,s.xona,
                          s.rahbar_user_id,COALESCE(u.full_name,'') AS rahbar_ismi
                   FROM maktab_sinflari s
                   LEFT JOIN users u ON u.user_id=s.rahbar_user_id
                   WHERE s.maktab_id=%s ORDER BY s.sinf::int,s.harf""", (maktab_id,))
    classes = cur.fetchall()
    cur.execute("""SELECT q.*,s.sinf,s.harf,COALESCE(s.smena,1) AS smena,
                          s.rahbar_user_id,COALESCE(u.full_name,'') AS rahbar_ismi
                   FROM aqlli_sinf_soati_qoidalari_v2 q
                   JOIN maktab_sinflari s ON s.id=q.sinf_id
                   LEFT JOIN users u ON u.user_id=s.rahbar_user_id
                   WHERE q.maktab_id=%s AND q.faol=TRUE
                   ORDER BY s.sinf::int,s.harf""", (maktab_id,))
    class_hours = cur.fetchall()
    class_hour_counts = _v1852_Counter()
    for row in class_hours:
        if row.get("rahbar_user_id") is not None:
            class_hour_counts[int(row["rahbar_user_id"])] += int(row.get("haftalik_soat") or 1)
    plan = _v193_plan_payload(cur, maktab_id, classes)
    teachers = _v1859_effective_teachers(cur, maktab_id)
    for teacher in teachers:
        extra = int(class_hour_counts.get(int(teacher["user_id"]), 0))
        teacher["sinf_soati_soni"] = extra
        base = teacher.get("haftalik_dars_soati")
        teacher["haftalik_reja_jami"] = (
            round(float(base) + extra, 1)
            if base is not None else (extra or None)
        )
    cur.execute("SELECT fan_nomi FROM maktab_fanlari WHERE maktab_id=%s ORDER BY fan_nomi", (maktab_id,))
    subjects = [r["fan_nomi"] for r in cur.fetchall()]
    cur.execute("SELECT * FROM aqlli_xonalar_v2 WHERE maktab_id=%s AND faol=TRUE AND darsga_yaroqli=TRUE ORDER BY nomi", (maktab_id,))
    rooms = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_oqituvchi_qoidalari_v2 WHERE maktab_id=%s ORDER BY user_id", (maktab_id,))
    teacher_rules = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s ORDER BY user_id,hafta_kuni,smena,dars_raqami", (maktab_id,))
    teacher_times = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_sinf_fan_yuklamalari_v2 WHERE maktab_id=%s ORDER BY sinf_id,fan_nomi", (maktab_id,))
    loads = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s ORDER BY sinf_id,fan_nomi,guruh_kaliti", (maktab_id,))
    group_settings = cur.fetchall()
    cur.execute("""SELECT b.sinf_id,b.user_id,b.fan_nomi,b.guruh_kaliti,
                          b.haftalik_soat,b.kunlik_max,b.manba,u.full_name,
                          s.sinf,s.harf,(s.sinf || '-' || s.harf) AS sinf_nomi
                   FROM maktab_dars_birikmalari b
                   JOIN users u ON u.user_id=b.user_id
                   JOIN maktab_sinflari s ON s.id=b.sinf_id
                   WHERE b.maktab_id=%s
                   ORDER BY s.sinf::int,s.harf,b.fan_nomi,b.guruh_kaliti,u.full_name""", (maktab_id,))
    assignments = cur.fetchall()
    cur.execute("""SELECT id,holat,yaratilgan_at,tasdiqlangan_at,sifat,joylashtirildi,joylashtirilmadi,diagnostika
                   FROM aqlli_jadval_urinishlari_v2 WHERE maktab_id=%s ORDER BY id DESC LIMIT 10""", (maktab_id,))
    runs = cur.fetchall()
    class_day_blocks = _v1856_class_day_rule_rows(cur, maktab_id)
    return {
        "oquv_yili": year, "choraklar": quarters, "maxsus_kunlar": special_days,
        "smenalar": shifts, "sinflar": classes, "oqituvchilar": teachers,
        "fanlar": subjects, "xonalar": rooms, "oqituvchi_qoidalari": teacher_rules,
        "oqituvchi_vaqtlari": teacher_times, "fan_soatlari": loads,
        "guruh_sozlamalari": group_settings, "birikmalar": assignments, "urinishlar": runs,
        "sinf_kun_bloklari": class_day_blocks, "sinf_soatlari": class_hours,
        "avtomatik_qoidalar": {
            "sinf_kun_bloklari": class_day_blocks,
            "izoh": "Rahbariyat xohlagan parallel yoki aniq sinf uchun dars bo'lmaydigan hafta kunini belgilaydi",
        },
    }


class V1856ClassDayBlocks(BaseModel):
    maktab_id: int
    qamrov: str = "parallel"
    sinf_darajalari: list[int] = []
    sinf_idlar: list[int] = []
    hafta_kunlari: list[int] = []
    izoh: Optional[str] = None


@app.put("/api/maktab/aqlli_jadval/v2/sinf_kun_bloklari")
def v1856_class_day_blocks_save(sorov: V1856ClassDayBlocks, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Sinf kunlarini faqat maktab rahbariyati boshqaradi")
        _v1856_seed_default_class_day_rules(cur, sorov.maktab_id)
        qamrov = str(sorov.qamrov or "parallel").strip().lower()
        days = sorted(set(int(x) for x in sorov.hafta_kunlari))
        if not days or any(day not in range(1, 7) for day in days):
            raise HTTPException(status_code=400, detail="Dushanba–Shanbadan bitta kunni tanlang")
        if len(days) != 1:
            raise HTTPException(
                status_code=400,
                detail="Har bir qoidada faqat bitta hafta kuni bo'lishi kerak. Yana boshqa kun kerak bo'lsa, uni alohida qoida qilib saqlang.",
            )
        created = 0
        if qamrov == "parallel":
            grades = sorted(set(int(x) for x in sorov.sinf_darajalari))
            if not grades or any(grade not in range(1, 12) for grade in grades):
                raise HTTPException(status_code=400, detail="Kamida bitta 1–11-sinf parallelini tanlang")
            cur.execute("""SELECT DISTINCT NULLIF(REGEXP_REPLACE(COALESCE(sinf,''),'[^0-9]','','g'),'')::int AS grade
                           FROM maktab_sinflari WHERE maktab_id=%s""", (sorov.maktab_id,))
            available = {int(r["grade"]) for r in cur.fetchall() if r.get("grade") is not None}
            missing = [grade for grade in grades if grade not in available]
            if missing:
                raise HTTPException(status_code=400, detail=f"Maktabda bu parallellar yo'q: {', '.join(map(str, missing))}-sinf")
            for grade in grades:
                for day in days:
                    cur.execute("""SELECT id FROM aqlli_sinf_kun_bloklari_v2
                                   WHERE maktab_id=%s AND sinf_id IS NULL AND sinf_daraja=%s AND hafta_kuni=%s""",
                                (sorov.maktab_id, grade, day))
                    row = cur.fetchone()
                    if row:
                        cur.execute("""UPDATE aqlli_sinf_kun_bloklari_v2 SET faol=TRUE,izoh=%s,
                                       yaratgan_user_id=%s,yangilangan_at=NOW() WHERE id=%s""",
                                    (sorov.izoh, user_id, row["id"]))
                    else:
                        cur.execute("""INSERT INTO aqlli_sinf_kun_bloklari_v2(
                            maktab_id,sinf_daraja,hafta_kuni,izoh,faol,yaratgan_user_id)
                            VALUES(%s,%s,%s,%s,TRUE,%s)""",
                            (sorov.maktab_id, grade, day, sorov.izoh, user_id))
                        created += 1
        elif qamrov == "sinf":
            class_ids = sorted(set(int(x) for x in sorov.sinf_idlar))
            if not class_ids:
                raise HTTPException(status_code=400, detail="Kamida bitta aniq sinfni tanlang")
            cur.execute("SELECT id FROM maktab_sinflari WHERE maktab_id=%s AND id=ANY(%s)",
                        (sorov.maktab_id, class_ids))
            found = {int(r["id"]) for r in cur.fetchall()}
            missing = [cid for cid in class_ids if cid not in found]
            if missing:
                raise HTTPException(status_code=400, detail="Tanlangan sinflardan biri bu maktabga tegishli emas")
            for class_id in class_ids:
                for day in days:
                    cur.execute("""SELECT id FROM aqlli_sinf_kun_bloklari_v2
                                   WHERE maktab_id=%s AND sinf_id=%s AND hafta_kuni=%s""",
                                (sorov.maktab_id, class_id, day))
                    row = cur.fetchone()
                    if row:
                        cur.execute("""UPDATE aqlli_sinf_kun_bloklari_v2 SET faol=TRUE,izoh=%s,
                                       yaratgan_user_id=%s,yangilangan_at=NOW() WHERE id=%s""",
                                    (sorov.izoh, user_id, row["id"]))
                    else:
                        cur.execute("""INSERT INTO aqlli_sinf_kun_bloklari_v2(
                            maktab_id,sinf_id,hafta_kuni,izoh,faol,yaratgan_user_id)
                            VALUES(%s,%s,%s,%s,TRUE,%s)""",
                            (sorov.maktab_id, class_id, day, sorov.izoh, user_id))
                        created += 1
        else:
            raise HTTPException(status_code=400, detail="Qamrov parallel yoki sinf bo'lishi kerak")
        rules = _v1856_class_day_rule_rows(cur, sorov.maktab_id)
        violations = _v1856_schedule_block_violations(cur, sorov.maktab_id)
        conn.commit()
        return {
            "holat": "saqlandi", "yangi_qoida_soni": created,
            "qoidalar": rules, "faol_jadvaldagi_zid_darslar": violations,
            "zid_dars_soni": sum(int(x.get("dars_soni") or 0) for x in violations),
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.delete("/api/maktab/aqlli_jadval/v2/sinf_kun_bloki")
def v1856_class_day_block_delete(token: str, maktab_id: int, blok_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, maktab_id):
            raise HTTPException(status_code=403, detail="Sinf kunlarini faqat maktab rahbariyati boshqaradi")
        cur.execute("DELETE FROM aqlli_sinf_kun_bloklari_v2 WHERE id=%s AND maktab_id=%s RETURNING id",
                    (blok_id, maktab_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Qoida topilmadi")
        rules = _v1856_class_day_rule_rows(cur, maktab_id)
        conn.commit()
        return {"holat": "o'chirildi", "qoidalar": rules}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.get("/api/maktab/aqlli_jadval/v2/sozlamalar")
def v1852_setup(token: str, maktab_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_staff(cur, user_id, maktab_id):
            raise HTTPException(status_code=403, detail="Bu maktab jadvalini ko'rishga ruxsat yo'q")
        manager = _v1852_manager(cur, user_id, maktab_id)
        if manager:
            # Yangi yoki eski maktabdan qat'i nazar barcha faol sinfga bir
            # martadan SINF SOATI avtomatik mavjud bo'ladi. Qo'lda tanlangan
            # kun/dars ON CONFLICT sabab o'zgarmaydi.
            _v199_ensure_class_hour_rules(cur, maktab_id, actor_id=user_id)
        payload = _v1852_setup_payload(cur, maktab_id)
        payload["joriy_user_id"] = user_id
        payload["boshqaruvchi"] = manager
        if not manager:
            own_assignments = [row for row in payload["birikmalar"] if int(row["user_id"]) == int(user_id)]
            allowed_pairs = {(int(row["sinf_id"]), str(row["fan_nomi"]).strip().casefold()) for row in own_assignments}
            allowed_class_ids = {pair[0] for pair in allowed_pairs}
            payload["oqituvchilar"] = [row for row in payload["oqituvchilar"] if int(row["user_id"]) == int(user_id)]
            payload["oqituvchi_qoidalari"] = [row for row in payload["oqituvchi_qoidalari"] if int(row["user_id"]) == int(user_id)]
            payload["oqituvchi_vaqtlari"] = [row for row in payload["oqituvchi_vaqtlari"] if int(row["user_id"]) == int(user_id)]
            payload["birikmalar"] = own_assignments
            payload["sinflar"] = [row for row in payload["sinflar"] if int(row["id"]) in allowed_class_ids]
            payload["fan_soatlari"] = [row for row in payload["fan_soatlari"] if (int(row["sinf_id"]), str(row["fan_nomi"]).strip().casefold()) in allowed_pairs]
            payload["guruh_sozlamalari"] = [row for row in payload["guruh_sozlamalari"] if (int(row["sinf_id"]), str(row["fan_nomi"]).strip().casefold()) in allowed_pairs]
            payload["urinishlar"] = [row for row in payload["urinishlar"] if row["holat"] == "tasdiqlangan"][:1]
        conn.commit()
        return payload
    finally:
        cur.close(); conn.close()


def _v1852_teacher_rules_map(rows):
    result = {}
    for row in rows:
        result[int(row["user_id"])] = {
            "kunlik_max": int(row.get("kunlik_max") or 6),
            "ketma_ket_max": int(row.get("ketma_ket_max") or 4),
            "okno_max": int(row.get("okno_max") or 1),
            "afzal_smena": int(row.get("afzal_smena") or 0),
            "eng_erta_dars": int(row.get("eng_erta_dars") or 1),
            "eng_kech_dars": int(row.get("eng_kech_dars") or 12),
        }
    return result


def _v1852_availability_maps(rows):
    hard = set(); soft = set(); method_hard = set(); method_soft = set()
    for row in rows:
        key = (int(row["user_id"]), int(row["hafta_kuni"]), int(row.get("smena") or 0), int(row.get("dars_raqami") or 0))
        if row["turi"] == "metod_kuni":
            # REV52: METOD KUNI tavsiya emas, to'liq darsdan xoli kun.
            # Eski bazada qattiq=False saqlangan yoki rasmiy/avtomatik yozuv
            # bo'lsa ham generator bu kunga birorta dars joylamaydi.
            method_hard.add((key[0], key[1]))
        elif row["turi"] == "band":
            (hard if row.get("qattiq") else soft).add(key)
        else:
            soft.add(key)
    return hard, soft, method_hard, method_soft


def _v1852_blocked(hard, teacher, day, shift, period):
    return any(key in hard for key in (
        (teacher, day, 0, 0), (teacher, day, shift, 0),
        (teacher, day, 0, period), (teacher, day, shift, period),
    ))


def _v1852_soft_blocked(soft, teacher, day, shift, period):
    return any(key in soft for key in (
        (teacher, day, 0, 0), (teacher, day, shift, 0),
        (teacher, day, 0, period), (teacher, day, shift, period),
    ))


def _v1852_max_streak(periods: set[int]) -> int:
    if not periods:
        return 0
    ordered = sorted(periods)
    best = current = 1
    for a, b in zip(ordered, ordered[1:]):
        current = current + 1 if b == a + 1 else 1
        best = max(best, current)
    return best


def _v1852_gap_count(periods: set[int]) -> int:
    return 0 if len(periods) < 2 else max(periods) - min(periods) + 1 - len(periods)


def _v1852_prepare_generation(cur, maktab_id: int):
    year = _v1890_generation_year(cur, maktab_id)
    _v1852_default_shifts(cur, maktab_id)
    cur.execute("SELECT * FROM aqlli_smena_sozlamalari_v2 WHERE maktab_id=%s", (maktab_id,))
    shift_rows = cur.fetchall()
    shifts = {int(row["smena"]): {**row, "slotlar": _v1852_shift_slots(row)} for row in shift_rows}
    cur.execute("""SELECT id,sinf,harf,COALESCE(smena,1) AS smena,bino,xona,rahbar_user_id
                   FROM maktab_sinflari WHERE maktab_id=%s ORDER BY sinf::int,harf""", (maktab_id,))
    classes = {int(row["id"]): row for row in cur.fetchall()}
    cur.execute("SELECT * FROM aqlli_sinf_fan_yuklamalari_v2 WHERE maktab_id=%s AND haftalik_soat>0 ORDER BY sinf_id,fan_nomi", (maktab_id,))
    loads = cur.fetchall()
    if not loads:
        raise HTTPException(status_code=400, detail="Avval sinflar uchun haftalik fan soatlarini kiriting")
    cur.execute("""SELECT b.sinf_id,b.user_id,b.fan_nomi,b.guruh_kaliti,u.full_name,u.haftalik_dars_soati
                   FROM maktab_dars_birikmalari b JOIN users u ON u.user_id=b.user_id
                   WHERE b.maktab_id=%s""", (maktab_id,))
    assignments = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s", (maktab_id,))
    group_settings = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_oqituvchi_qoidalari_v2 WHERE maktab_id=%s", (maktab_id,))
    rules_rows = cur.fetchall()
    cur.execute("SELECT * FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s", (maktab_id,))
    availability_rows = cur.fetchall()
    cur.execute("""SELECT u.user_id,u.full_name,u.haftalik_dars_soati
                   FROM users u
                   WHERE u.maktab_id=%s AND u.lavozim IS NOT NULL
                     AND (
                       EXISTS(SELECT 1 FROM maktab_dars_birikmalari b
                              WHERE b.maktab_id=%s AND b.user_id=u.user_id)
                       OR EXISTS(SELECT 1 FROM maktab_xodim_sinflari x
                                 WHERE x.maktab_id=%s AND x.user_id=u.user_id)
                       OR EXISTS(SELECT 1 FROM maktab_sinflari s
                                 WHERE s.maktab_id=%s AND s.rahbar_user_id=u.user_id)
                     )""", (maktab_id, maktab_id, maktab_id, maktab_id))
    teachers = {int(row["user_id"]): row for row in cur.fetchall()}
    cur.execute("SELECT * FROM aqlli_xonalar_v2 WHERE maktab_id=%s AND faol=TRUE AND darsga_yaroqli=TRUE", (maktab_id,))
    rooms = {int(row["id"]): row for row in cur.fetchall()}
    return year, shifts, classes, loads, assignments, group_settings, rules_rows, availability_rows, teachers, rooms


def _v1852_build_jobs(classes, loads, assignments, group_settings, teachers):
    assignment_map = _v1852_defaultdict(list)
    for row in assignments:
        assignment_map[(int(row["sinf_id"]), str(row["fan_nomi"]).strip().casefold())].append(row)
    group_map = {}
    for row in group_settings:
        group_map[(int(row["sinf_id"]), str(row["fan_nomi"]).strip().casefold(), str(row["guruh_kaliti"]))] = row
    jobs = []
    warnings = []
    for load in loads:
        class_id = int(load["sinf_id"])
        if class_id not in classes:
            continue
        fan = str(load["fan_nomi"]).strip()
        rows = assignment_map.get((class_id, fan.casefold()), [])
        non_whole = [r for r in rows if str(r.get("guruh_kaliti") or "whole") != "whole"]
        whole = [r for r in rows if str(r.get("guruh_kaliti") or "whole") == "whole"]
        fixed_groups = []
        teacher_options = []
        if non_whole:
            seen_groups = set()
            for row in non_whole:
                group_key = str(row.get("guruh_kaliti") or "whole")
                if group_key in seen_groups:
                    continue
                seen_groups.add(group_key)
                setting = group_map.get((class_id, fan.casefold(), group_key), {})
                teacher_id = setting.get("oqituvchi_user_id") or row.get("user_id")
                fixed_groups.append({
                    "guruh_kaliti": group_key,
                    "teacher": int(teacher_id) if teacher_id is not None else None,
                    "xona_id": int(setting["xona_id"]) if setting.get("xona_id") else None,
                })
            if any(g["teacher"] is None for g in fixed_groups):
                warnings.append(f"{classes[class_id]['sinf']}-{classes[class_id]['harf']} {fan}: guruh o'qituvchisi to'liq biriktirilmagan")
        else:
            primary = load.get("asosiy_oqituvchi_user_id")
            if primary is not None:
                teacher_options = [int(primary)]
            else:
                teacher_options = list(dict.fromkeys(int(r["user_id"]) for r in whole if r.get("user_id") is not None))
            if not teacher_options:
                warnings.append(f"{classes[class_id]['sinf']}-{classes[class_id]['harf']} {fan}: o'qituvchi biriktirilmagan")
        weekly_hours = max(0.0, float(load.get("haftalik_soat") or 0))
        whole_occurrences = int(math.floor(weekly_hours))
        has_half_rotation = abs(weekly_hours - whole_occurrences - 0.5) < 1e-9
        occurrence_count = whole_occurrences + (1 if has_half_rotation else 0)
        for occurrence in range(1, occurrence_count + 1):
            rotation_weight = 0.5 if has_half_rotation and occurrence == occurrence_count else 1.0
            jobs.append({
                "job_id": f"{load['id']}:{occurrence}", "load_id": int(load["id"]),
                "sinf_id": class_id, "fan": fan, "occurrence": occurrence,
                "smena": int(classes[class_id].get("smena") or 1),
                "daily_max": int(load.get("kunlik_max") or 1),
                "consecutive_allowed": bool(load.get("ketma_ket_mumkin")),
                "preferred_last": int(load.get("afzal_oxirgi_dars") or 5),
                "weight": int(load.get("ogirlik") or 2),
                "room_id": int(load["xona_id"]) if load.get("xona_id") else None,
                "groups": fixed_groups, "teacher_options": teacher_options,
                "rotation_weight": rotation_weight,
                "difficulty": (100 if fixed_groups else 0) + (50 if load.get("xona_id") else 0) + weekly_hours,
            })
    return jobs, warnings


def _v1852_candidate_reasons(job, day, period, selected_teachers, room_keys, state, context):
    reasons = []
    # Xona — jadval yaratishni to'xtatadigan shart emas. Parallel guruhning
    # alohida xonasi hali yozilmagan bo'lsa slot baribir yaratiladi; frontend
    # uni "Xona yo'q" deb ko'rsatadi va keyin qo'lda to'ldirish mumkin.
    non_null_teachers = [teacher for teacher in selected_teachers if teacher is not None]
    if len(non_null_teachers) != len(set(non_null_teachers)):
        reasons.append("bir o'qituvchi ikki parallel guruhga biriktirilgan")
    non_null_rooms = [key for key in room_keys if key]
    if len(non_null_rooms) != len(set(non_null_rooms)):
        reasons.append("parallel guruhlar bir xil xonaga biriktirilgan")
    class_slot = (job["sinf_id"], day, job["smena"], period)
    if class_slot in state["class_busy"]:
        reasons.append("sinf band")
    if state["subject_daily"].get((job["sinf_id"], job["fan"].casefold(), day), 0) >= job["daily_max"]:
        reasons.append("fan kunlik maksimumga yetgan")
    for teacher in selected_teachers:
        if teacher is None:
            reasons.append("o'qituvchi biriktirilmagan")
            continue
        rules = context["rules"].get(teacher, context["default_rules"])
        if period < rules["eng_erta_dars"] or period > rules["eng_kech_dars"]:
            reasons.append("o'qituvchi ruxsat etgan dars oralig'idan tashqari")
        if (teacher, day) in context["method_hard"]:
            reasons.append("o'qituvchining metod kuni")
        if _v1852_blocked(context["hard"], teacher, day, job["smena"], period):
            reasons.append("o'qituvchi bu vaqtda band")
        if (teacher, day, job["smena"], period) in state["teacher_busy"]:
            reasons.append("o'qituvchi boshqa darsda")
        cap = context["teacher_caps"].get(teacher)
        if cap is not None and state["teacher_week"].get(teacher, 0) >= cap:
            reasons.append("o'qituvchining haftalik yuklamasi to'lgan")
        if state["teacher_daily"].get((teacher, day), 0) >= rules["kunlik_max"]:
            reasons.append("o'qituvchining kunlik maksimumi to'lgan")
        # Ketma-ket dars soni qulaylik talabi, majburiy blok emas. Masalan,
        # metod kuni bor 30 soatli o'qituvchi qolgan 5 kunda 6 tadan dars
        # o'tishi mumkin; 4 ta ketma-ket limitini qattiq qo'llash uning 6 ta
        # darsini asossiz ravishda jadvaldan chiqarib yuborar edi. Me'yordan
        # oshish pastdagi ballashda jazolanadi, lekin dars tashlab ketilmaydi.
    for key in room_keys:
        if key and (key, day, job["smena"], period) in state["room_busy"]:
            reasons.append("xona band")
    return list(dict.fromkeys(reasons))


def _v1852_choose_teacher(job, day, period, state, context):
    if job["groups"]:
        return [g.get("teacher") for g in job["groups"]]
    options = job["teacher_options"]
    if not options:
        return [None]
    valid = []
    for teacher in options:
        reasons = _v1852_candidate_reasons(job, day, period, [teacher], [], state, context)
        if not reasons:
            valid.append((state["teacher_week"].get(teacher, 0), state["teacher_daily"].get((teacher, day), 0), teacher))
    return [min(valid)[2]] if valid else [options[0]]


def _v1852_room_keys(job, selected_teachers, classes):
    class_row = classes[job["sinf_id"]]
    room_text = "|".join(str(class_row.get(x) or "").strip() for x in ("bino", "xona")).strip("|")
    home_room_key = f"classroom:{room_text.casefold()}" if room_text else None
    if job["groups"]:
        # Guruh xonasi yozilmagan bo'lsa barcha guruhga bir xil sinf xonasi
        # kalitini berish mumkin emas: bu ularni soxta "bir xil xona" ziddiyatiga
        # tushirib, butun guruhli fanni jadvaldan chiqarib yuborar edi. Birinchi
        # guruh sinf xonasida qoladi, keyingi xonasiz guruhlar esa jadvalga
        # room=None bilan tushadi va frontendda "Xona yo'q" deb ko'rinadi.
        return [
            f"room:{group['xona_id']}"
            if group.get("xona_id")
            else (home_room_key if group_index == 0 else None)
            for group_index, group in enumerate(job["groups"])
        ]
    if job.get("room_id"):
        return [f"room:{job['room_id']}"]
    return [home_room_key]


def _v1852_candidate_score(job, day, period, teachers, state, context, rng):
    score = 0.0
    for teacher in teachers:
        if teacher is None:
            score += 1000
            continue
        rules = context["rules"].get(teacher, context["default_rules"])
        if (teacher, day) in context["method_soft"]:
            # Rasmiy metod kuni avval boshqa barcha amaliy slotlardan keyin
            # ko'riladi. Lekin u qattiq blok emas: aks holda kuniga bir marta
            # o'tiladigan 5 soatlik fan 4 soatga tushib qoladi.
            score += 900
        if _v1852_soft_blocked(context["soft"], teacher, day, job["smena"], period):
            score += 25
        if rules["afzal_smena"] and rules["afzal_smena"] != job["smena"]:
            score += 8
        existing = set(state["teacher_periods"].get((teacher, day, job["smena"]), set()))
        before_gap = _v1852_gap_count(existing)
        after_gap = _v1852_gap_count(existing | {period})
        score += max(0, after_gap - before_gap) * 8
        score += state["teacher_daily"].get((teacher, day), 0) * 1.8
        if after_gap > rules["okno_max"]:
            score += (after_gap - rules["okno_max"]) * 6
        new_streak = _v1852_max_streak(existing | {period})
        if new_streak > rules["ketma_ket_max"]:
            score += (new_streak - rules["ketma_ket_max"]) * 65
    same_day = state["subject_daily"].get((job["sinf_id"], job["fan"].casefold(), day), 0)
    score += same_day * 14
    if period > job["preferred_last"]:
        score += (period - job["preferred_last"]) * (2 + job["weight"] * 2)
    class_subject_periods = state["class_subject_periods"].get((job["sinf_id"], job["fan"].casefold(), day), set())
    adjacent = any(abs(period - p) == 1 for p in class_subject_periods)
    if adjacent:
        score += -4 if job["consecutive_allowed"] else 10
    score += rng.random() * 1.5
    return score


def _v1852_place_job(job, day, period, teachers, room_keys, state, context):
    state["class_busy"].add((job["sinf_id"], day, job["smena"], period))
    state["subject_daily"][(job["sinf_id"], job["fan"].casefold(), day)] += 1
    state["class_subject_periods"][(job["sinf_id"], job["fan"].casefold(), day)].add(period)
    for teacher in teachers:
        if teacher is None:
            continue
        state["teacher_busy"].add((teacher, day, job["smena"], period))
        state["teacher_week"][teacher] += 1
        state["teacher_daily"][(teacher, day)] += 1
        state["teacher_periods"][(teacher, day, job["smena"])].add(period)
    for key in room_keys:
        if key:
            state["room_busy"].add((key, day, job["smena"], period))
    state["placements"].append({"job": job, "day": day, "period": period, "teachers": teachers, "room_keys": room_keys})


def _v1852_new_schedule_state():
    return {
        "class_busy": set(), "teacher_busy": set(), "room_busy": set(),
        "subject_daily": _v1852_defaultdict(int),
        "class_subject_periods": _v1852_defaultdict(set),
        "teacher_week": _v1852_defaultdict(int),
        "teacher_daily": _v1852_defaultdict(int),
        "teacher_periods": _v1852_defaultdict(set), "placements": [],
    }


def _v1852_job_teacher_ids(job):
    result = set()
    members = job.get("rotation_members") or []
    source_jobs = members or [job]
    for source in source_jobs:
        groups = source.get("groups") or []
        if groups:
            for group in groups:
                if group.get("teacher") is not None:
                    result.add(int(group["teacher"]))
        else:
            for teacher in source.get("teacher_options") or []:
                if teacher is not None:
                    result.add(int(teacher))
    return result


_V201_UNPLACED_REASON_TEXT = {
    "parallel guruhlar uchun umumiy vaqt topilmadi": (
        "Bu fan 1-/2-guruh yoki o'g'il/qiz guruhida bir vaqtda o'tishi kerak. Sinf va barcha guruh o'qituvchilari bir paytda bo'sh bo'lgan katak topilmadi.",
        "O'qituvchi vaqti bo'limida guruh o'qituvchilariga kamida bitta umumiy ochiq katak qoldiring; so'ng yangi draft yarating. Tizim bitta sinf katagida guruhlarni tagma-tag joylaydi.",
    ),
    "sinf band": (
        "Sinfning ruxsat etilgan kataklari boshqa darslar bilan band bo'lib qolgan.",
        "Sinfning qattiq bloklarini va kunlik dars sig'imini tekshiring; so'ng yangi draft yarating.",
    ),
    "sinf jadvalida bo'sh dars qoldirilmaydi": (
        "Bu dars faqat sinf orasida bo'sh soat qoldiradigan katakka sig'gan, tizim esa o'quvchi oknosini taqiqlagan.",
        "O'qituvchi vaqtini kengaytiring yoki shu sinfdagi boshqa fan vaqtini bo'shating.",
    ),
    "o'qituvchi boshqa darsda": (
        "O'qituvchi mos kelgan vaqtda boshqa sinfga dars o'tayotgan bo'lgan.",
        "O'qituvchining band vaqtini yoki shu fan birikmasini tekshirib, yangi draft yarating.",
    ),
    "o'qituvchi bu vaqtda band": (
        "O'qituvchining vaqt jadvalida mos katak qattiq BAND qilib qo'yilgan.",
        "2. O'qituvchi vaqti bo'limida kamida bitta mos katakni BO'SH qiling.",
    ),
    "o'qituvchining metod kuni": (
        "O'qituvchining mos kuni qattiq metod/kasbiy kun sifatida yopilgan.",
        "Metod kunini yumshoq tavsiyaga o'tkazing yoki boshqa kunni oching.",
    ),
    "o'qituvchi ruxsat etgan dars oralig'idan tashqari": (
        "Bo'sh katak o'qituvchi ruxsat bergan eng erta–eng kech dars oralig'iga kirmagan.",
        "O'qituvchi vaqt qoidasidagi dars oralig'ini kengaytiring.",
    ),
    "o'qituvchining kunlik maksimumi to'lgan": (
        "Mos kunlarda o'qituvchining kunlik eng ko'p dars limiti to'lgan.",
        "Kunlik maksimumni tekshiring yoki haftadagi yana bir kunni oching.",
    ),
    "o'qituvchining haftalik yuklamasi to'lgan": (
        "O'qituvchining belgilangan haftalik yuklama chegarasi allaqachon to'lgan.",
        "O'qituvchi rejasini va fan birikmalaridagi soatlarni tenglashtiring.",
    ),
    "fan kunlik maksimumga yetgan": (
        "Shu fan uchun bir kunda ruxsat etilgan takror soni to'lgan.",
        "Fan-soat sozlamasidagi kunlik maksimumni tekshiring yoki boshqa kunni oching.",
    ),
    "jismoniy tarbiya va texnologiya 1-darsga qo'yilmaydi": (
        "Faqat 1-dars bo'sh qolgan, lekin Jismoniy tarbiya/Texnologiya 1-darsga qo'yilmaydi.",
        "3–6-darslardan joy oching yoki boshqa fanlarni xavfsiz almashtiring.",
    ),
    "xona band": (
        "Fan uchun tanlangan xona mos vaqtda boshqa dars bilan band bo'lgan.",
        "Xonani almashtiring; guruh xonasi bo'lmasa 'Xona yo'q' bilan yaratish mumkin.",
    ),
    "o'qituvchi biriktirilmagan": (
        "Bu fan yoki guruhga o'qituvchi biriktirilmagan.",
        "O'qituvchi yuklamasida fan–sinf–guruh birikmasini to'ldiring.",
    ),
    "smena sozlanmagan": (
        "Sinf smenasi uchun dars vaqt kataklari topilmadi.",
        "Kalendar/smena sozlamasida boshlanish va dars sonini saqlang.",
    ),
    "mos bo'sh vaqt topilmadi": (
        "Sinf, o'qituvchi va qattiq vaqt qoidalariga bir vaqtda mos bo'sh katak topilmadi.",
        "Qattiq BAND/metod qoidalarini kamaytiring yoki o'qituvchiga qo'shimcha kun oching.",
    ),
}


def _v201_unplaced_reason_copy(reason):
    key = str(reason or "mos bo'sh vaqt topilmadi")
    return _V201_UNPLACED_REASON_TEXT.get(
        key,
        (
            f"Mos katak topilmadi: {key}.",
            "Sinf va o'qituvchining qattiq vaqt cheklovlarini tekshirib, yangi draft yarating.",
        ),
    )


def _v201_unplaced_teacher_weights(job):
    """Joylashmagan ishni unga tegishli ustoz(lar)ga to'g'ri soatda bog'laydi."""
    result = _v1852_defaultdict(float)
    members = job.get("rotation_members") or []
    if members:
        for member in members:
            for teacher_id in _v1852_job_teacher_ids(member):
                result[int(teacher_id)] += 0.5
        return dict(result)
    groups = job.get("groups") or []
    if groups:
        for teacher_id in _v1852_job_teacher_ids(job):
            result[int(teacher_id)] += 1.0
        return dict(result)
    options = [
        int(teacher_id) for teacher_id in job.get("teacher_options") or []
        if teacher_id is not None
    ]
    if options:
        # Kvota qo'llangandan keyin odatda bitta variant qoladi. Eski manbada
        # bir necha nomzod bo'lsa, yetishmagan darsni hammasiga yozib yubormaymiz.
        result[options[0]] = float(job.get("rotation_weight") or 1.0)
    return dict(result)


def _v201_unplaced_teacher_rows(job, teachers):
    """A/B almashuvda ham har bir ustozga aynan o'z fani yoziladi."""
    rows = []
    members = job.get("rotation_members") or []
    if members:
        for member in members:
            member_groups = member.get("groups") or []
            if member_groups:
                for group in member_groups:
                    teacher_id = group.get("teacher")
                    if teacher_id is None:
                        continue
                    rows.append({
                        "user_id": int(teacher_id),
                        "full_name": (teachers.get(int(teacher_id), {}) or {}).get("full_name") or str(teacher_id),
                        "fan": member.get("fan") or job.get("fan"),
                        "guruh_kaliti": group.get("guruh_kaliti") or "whole",
                        "soat": 0.5,
                    })
                continue
            for teacher_id in sorted(_v1852_job_teacher_ids(member)):
                rows.append({
                    "user_id": int(teacher_id),
                    "full_name": (teachers.get(int(teacher_id), {}) or {}).get("full_name") or str(teacher_id),
                    "fan": member.get("fan") or job.get("fan"),
                    "guruh_kaliti": "whole",
                    "soat": 0.5,
                })
        return rows
    groups = job.get("groups") or []
    if groups:
        for group in groups:
            teacher_id = group.get("teacher")
            if teacher_id is None:
                continue
            rows.append({
                "user_id": int(teacher_id),
                "full_name": (teachers.get(int(teacher_id), {}) or {}).get("full_name") or str(teacher_id),
                "fan": job.get("fan"),
                "guruh_kaliti": group.get("guruh_kaliti") or "whole",
                "soat": 1.0,
            })
        return rows
    for teacher_id, hours in sorted(_v201_unplaced_teacher_weights(job).items()):
        rows.append({
            "user_id": int(teacher_id),
            "full_name": (teachers.get(int(teacher_id), {}) or {}).get("full_name") or str(teacher_id),
            "fan": job.get("fan"),
            "guruh_kaliti": "whole",
            "soat": round(float(hours), 1),
        })
    return rows


def _v1852_open_candidates(job, state, context, rng, exact=None):
    """Hozirgi holatda ishning barcha haqiqiy bo'sh slotlarini qaytaradi."""
    shift = context["shifts"].get(job["smena"])
    if not shift:
        return [], _v1852_Counter({"smena sozlanmagan": 1})
    candidates = []
    rejected = _v1852_Counter()
    class_row = context["classes"].get(job["sinf_id"], {})
    fixed_day = int(job.get("fixed_day") or 0)
    fixed_period = int(job.get("fixed_period") or 0)
    days = [fixed_day] if fixed_day else range(1, context["weekdays"] + 1)
    for day in days:
        if day not in range(1, context["weekdays"] + 1):
            rejected.update(["belgilangan sinf soati kuni o'qish haftasidan tashqari"])
            continue
        blocked_reason = _v1856_class_day_block_reason(
            class_row, day, context.get("class_day_blocks", {})
        )
        if blocked_reason:
            rejected.update([blocked_reason])
            continue
        slots = [
            slot for slot in shift["slotlar"]
            if (not fixed_period or int(slot["dars_raqami"]) == fixed_period)
            and (not exact or (int(day), int(slot["dars_raqami"])) == exact)
        ]
        if fixed_period and not slots and not exact:
            rejected.update(["belgilangan sinf soati dars raqami smenada mavjud emas"])
        for slot in slots:
            period = int(slot["dars_raqami"])
            teachers = _v1852_choose_teacher(job, day, period, state, context)
            room_keys = _v1852_room_keys(job, teachers, context["classes"])
            reasons = _v1852_candidate_reasons(
                job, day, period, teachers, room_keys, state, context
            )
            if reasons:
                rejected.update(reasons)
                continue
            score = (
                0.0 if fixed_day and fixed_period
                else _v1852_candidate_score(job, day, period, teachers, state, context, rng)
            )
            candidates.append((score, day, period, teachers, room_keys))
    candidates.sort(key=lambda row: row[0])
    return candidates, rejected


def _v1852_rebuild_schedule_state(placements, context):
    state = _v1852_new_schedule_state()
    for placement in placements:
        _v1852_place_job(
            placement["job"], placement["day"], placement["period"],
            placement["teachers"], placement["room_keys"], state, context,
        )
    return state


def _v1852_repair_unplaced(state, unplaced, context, rng):
    """To'qnashgan darsni ko'chirib, qolgan fanlarni jadvalga qaytaradi.

    Eski greedy generator oxirida kelgan 1–2 soatli fanlarni tashlab ketardi.
    Bu bosqich kerakli katakdagi sinf/o'qituvchi/xona darslarini vaqtincha olib,
    yangi darsni qo'yadi va olib turilgan darslarni boshqa bo'sh katakka qaytaradi.
    """
    def _job_is_fixed(job):
        return bool(
            job.get("is_class_hour")
            or int(job.get("fixed_day") or 0)
            or int(job.get("fixed_period") or 0)
        )

    def _slot_blockers(job, day, period, teachers, room_keys, source_state):
        """Bitta katakka halaqit qilayotgan aniq dars paketlarini qaytaradi.

        Guruhli fan bitta ``job`` bo'lib, ichida ikki yoki undan ko'p ustoz
        turadi. Shuning uchun to'qnashuv ham alohida guruh satri emas, butun
        parallel paket bo'yicha topiladi.
        """
        teacher_set = {int(value) for value in teachers if value is not None}
        room_set = {value for value in room_keys if value}
        result = []
        for placement in source_state.get("placements", []):
            if (
                int(placement.get("day") or 0) != int(day)
                or int(placement.get("period") or 0) != int(period)
                or int(placement.get("job", {}).get("smena") or 1)
                != int(job.get("smena") or 1)
            ):
                continue
            placement_teachers = {
                int(value) for value in placement.get("teachers") or []
                if value is not None
            }
            placement_rooms = {
                value for value in placement.get("room_keys") or [] if value
            }
            if (
                int(placement["job"].get("sinf_id") or 0)
                == int(job.get("sinf_id") or 0)
                or bool(teacher_set & placement_teachers)
                or bool(room_set & placement_rooms)
            ):
                result.append(placement)
        return result

    def _candidate_targets(job, source_state):
        shift = context["shifts"].get(job.get("smena"))
        if not shift:
            return []
        fixed_day = int(job.get("fixed_day") or 0)
        fixed_period = int(job.get("fixed_period") or 0)
        days = [fixed_day] if fixed_day else range(1, context["weekdays"] + 1)
        result = []
        for day in days:
            class_row = context["classes"].get(job.get("sinf_id"), {})
            if _v1856_class_day_block_reason(
                class_row, day, context.get("class_day_blocks", {})
            ):
                continue
            for slot in shift.get("slotlar") or []:
                period = int(slot.get("dars_raqami") or 0)
                if fixed_period and period != fixed_period:
                    continue
                teachers = _v1852_choose_teacher(
                    job, day, period, source_state, context
                )
                room_keys = _v1852_room_keys(
                    job, teachers, context["classes"]
                )
                score = (
                    0.0
                    if fixed_day and fixed_period
                    else _v1852_candidate_score(
                        job, day, period, teachers, source_state, context, rng
                    )
                )
                result.append((score, day, period, teachers, room_keys))
        result.sort(key=lambda row: row[0])
        return result

    def _place_with_chain(job, source_state, depth, path):
        """Bir necha darsni zanjirli ko'chirish orqali ishni joylaydi.

        Oldingi ta'mirlash faqat bitta qatlamni ko'rardi: guruhli fan uchun
        sinf darsi va ikki ustozning darsini surish kerak bo'lsa, ikkinchi
        ko'chirishdayoq to'xtardi. Bu qidiruv uch qatlamgacha xavfsiz yuradi;
        qattiq sinf soati, metod kuni va BAND kataklari hech qachon buzilmaydi.
        """
        direct, _ = _v1852_open_candidates(job, source_state, context, rng)
        if direct:
            _, day, period, teachers, rooms = direct[0]
            trial = _v1852_rebuild_schedule_state(
                list(source_state.get("placements", [])), context
            )
            _v1852_place_job(job, day, period, teachers, rooms, trial, context)
            return trial
        if depth <= 0:
            return None

        for _, day, period, teachers, rooms in _candidate_targets(
            job, source_state
        )[:36]:
            blockers = _slot_blockers(
                job, day, period, teachers, rooms, source_state
            )
            if not blockers or len(blockers) > 5:
                continue
            blocker_job_ids = {id(row.get("job")) for row in blockers}
            if blocker_job_ids & set(path):
                continue
            if any(_job_is_fixed(row.get("job") or {}) for row in blockers):
                continue

            blocker_ids = {id(row) for row in blockers}
            trial = _v1852_rebuild_schedule_state(
                [
                    row for row in source_state.get("placements", [])
                    if id(row) not in blocker_ids
                ],
                context,
            )
            target, _ = _v1852_open_candidates(
                job, trial, context, rng, exact=(int(day), int(period))
            )
            if not target:
                continue
            _, target_day, target_period, target_teachers, target_rooms = target[0]
            _v1852_place_job(
                job, target_day, target_period,
                target_teachers, target_rooms, trial, context,
            )

            returned = True
            ordered_blockers = sorted(
                blockers,
                key=lambda row: (
                    len(_v1852_job_teacher_ids(row.get("job") or {})),
                    float((row.get("job") or {}).get("difficulty") or 0),
                ),
                reverse=True,
            )
            next_path = set(path) | {id(job)} | blocker_job_ids
            for blocker in ordered_blockers:
                repaired = _place_with_chain(
                    blocker["job"], trial, depth - 1,
                    next_path - {id(blocker["job"])},
                )
                if repaired is None:
                    returned = False
                    break
                trial = repaired
            if returned:
                return trial
        return None

    remaining = list(unplaced)
    for _round in range(3):
        if not remaining:
            break
        progress = False
        next_remaining = []
        remaining.sort(
            key=lambda item: (
                len(_v1852_job_teacher_ids(item["job"])),
                float(item["job"].get("difficulty") or 0),
            ),
            reverse=True,
        )
        for item in remaining:
            job = item["job"]
            direct, rejected = _v1852_open_candidates(job, state, context, rng)
            if direct:
                _, day, period, teachers, room_keys = direct[0]
                _v1852_place_job(job, day, period, teachers, room_keys, state, context)
                progress = True
                continue

            shift = context["shifts"].get(job["smena"])
            if not shift:
                next_remaining.append({"job": job, "sabablar": dict(rejected.most_common(6))})
                continue
            fixed_day = int(job.get("fixed_day") or 0)
            fixed_period = int(job.get("fixed_period") or 0)
            days = [fixed_day] if fixed_day else range(1, context["weekdays"] + 1)
            desired = []
            for day in days:
                class_row = context["classes"].get(job["sinf_id"], {})
                if _v1856_class_day_block_reason(
                    class_row, day, context.get("class_day_blocks", {})
                ):
                    continue
                for slot in shift["slotlar"]:
                    period = int(slot["dars_raqami"])
                    if fixed_period and period != fixed_period:
                        continue
                    teachers = _v1852_choose_teacher(job, day, period, state, context)
                    room_keys = _v1852_room_keys(job, teachers, context["classes"])
                    score = 0.0 if fixed_day and fixed_period else _v1852_candidate_score(
                        job, day, period, teachers, state, context, rng
                    )
                    desired.append((score, day, period, teachers, room_keys))
            desired.sort(key=lambda row: row[0])

            repaired = None
            for _, day, period, teachers, room_keys in desired[:24]:
                teacher_set = {int(x) for x in teachers if x is not None}
                room_set = {x for x in room_keys if x}
                blockers = []
                for placement in state["placements"]:
                    same_slot = (
                        int(placement["day"]) == int(day)
                        and int(placement["period"]) == int(period)
                        and int(placement["job"].get("smena") or 1) == int(job["smena"])
                    )
                    if not same_slot:
                        continue
                    placement_teachers = {
                        int(x) for x in placement.get("teachers") or [] if x is not None
                    }
                    placement_rooms = {x for x in placement.get("room_keys") or [] if x}
                    if (
                        int(placement["job"]["sinf_id"]) == int(job["sinf_id"])
                        or bool(teacher_set & placement_teachers)
                        or bool(room_set & placement_rooms)
                    ):
                        blockers.append(placement)
                if not blockers or len(blockers) > 4:
                    continue
                blocker_ids = {id(placement) for placement in blockers}
                trial = _v1852_rebuild_schedule_state(
                    [p for p in state["placements"] if id(p) not in blocker_ids], context
                )
                target_candidates, _ = _v1852_open_candidates(
                    job, trial, context, rng, exact=(int(day), int(period))
                )
                if not target_candidates:
                    continue
                _, target_day, target_period, target_teachers, target_rooms = target_candidates[0]
                _v1852_place_job(
                    job, target_day, target_period, target_teachers, target_rooms, trial, context
                )
                blocker_order = sorted(
                    blockers,
                    key=lambda placement: (
                        bool(placement["job"].get("fixed_day")),
                        len(_v1852_job_teacher_ids(placement["job"])),
                        float(placement["job"].get("difficulty") or 0),
                    ),
                    reverse=True,
                )
                all_returned = True
                for blocker in blocker_order:
                    options, _ = _v1852_open_candidates(
                        blocker["job"], trial, context, rng
                    )
                    if not options:
                        all_returned = False
                        break
                    _, new_day, new_period, new_teachers, new_rooms = options[0]
                    _v1852_place_job(
                        blocker["job"], new_day, new_period,
                        new_teachers, new_rooms, trial, context,
                    )
                if all_returned:
                    repaired = trial
                    break
            if repaired is not None:
                state = repaired
                progress = True
            else:
                # Parallel guruhlar ko'pincha bitta sinf darsi va ikki
                # o'qituvchining darsini bir vaqtda siljitishni talab qiladi.
                # Bitta qatlamli almashtirish yetmasa, zanjirli ta'mirlashni
                # ishlatamiz. Natijada 1-/2-guruh bir katakda qoladi.
                chained = _place_with_chain(job, state, 3, {id(job)})
                if chained is not None:
                    state = chained
                    progress = True
                else:
                    next_remaining.append({
                        "job": job,
                        "sabablar": dict(rejected.most_common(6)),
                    })
        remaining = next_remaining
        if not progress:
            break
    return state, remaining


def _v1852_generate_attempt(jobs, context, seed):
    rng = _v1852_random.Random(seed)
    state = _v1852_new_schedule_state()
    # Eng kam bo'sh vaqti bor va eng band o'qituvchilarga tegishli ishlar
    # oldin joylashadi. Faqat fan soatiga qarab saralash 1–2 soatli fanlarni
    # eng oxirga surib, bo'sh katak bo'lsa ham ularni tashlab ketayotgan edi.
    empty_state = _v1852_new_schedule_state()
    demand = context.get("v196_teacher_demand") or {}
    scarcity = {}
    for job in jobs:
        domain, _ = _v1852_open_candidates(job, empty_state, context, rng)
        teacher_pressure = sum(float(demand.get(tid, 0) or 0) for tid in _v1852_job_teacher_ids(job))
        scarcity[id(job)] = (len(domain), teacher_pressure)
    ordered = sorted(
        jobs,
        key=lambda job: (
            0 if job.get("fixed_day") and job.get("fixed_period") else 1,
            scarcity[id(job)][0],
            # Bo'sh vaqti bir xil bo'lgan fanlardan avval o'quvchining diqqatini
            # ko'proq talab qiladigan asosiy fanlar joylashadi. Shunda amaliy/yengil
            # fanlar 1–2-darslarni egallab, algebra, geometriya yoki fizika 5–6 ga
            # siqilib qolmaydi. Eng kam domen mezoni oldinda qoladi — to'liq jadval
            # tuzish pedagogik tartibdan ham ustun qattiq talabdir.
            0 if (job.get("v1874_profile") or {}).get("core_priority") else (
                2 if (
                    (job.get("v1874_profile") or {}).get("physical")
                    or (job.get("v1874_profile") or {}).get("technology")
                    or (job.get("v1874_profile") or {}).get("light")
                ) else 1
            ),
            -len(_v1852_job_teacher_ids(job)),
            -scarcity[id(job)][1],
            rng.random(),
        ),
    )
    unplaced = []
    total_penalty = 0.0
    for job in ordered:
        shift = context["shifts"].get(job["smena"])
        if not shift:
            unplaced.append({"job": job, "sabablar": {"smena sozlanmagan": 1}})
            continue
        candidates = []
        reject_counter = _v1852_Counter()
        class_row = context["classes"].get(job["sinf_id"], {})
        fixed_day = int(job.get("fixed_day") or 0)
        fixed_period = int(job.get("fixed_period") or 0)
        days = [fixed_day] if fixed_day else range(1, context["weekdays"] + 1)
        for day in days:
            if day not in range(1, context["weekdays"] + 1):
                reject_counter.update(["belgilangan sinf soati kuni o‘qish haftasidan tashqari"])
                continue
            blocked_reason = _v1856_class_day_block_reason(class_row, day, context.get("class_day_blocks", {}))
            if blocked_reason:
                reject_counter.update([blocked_reason])
                continue
            slots = [slot for slot in shift["slotlar"] if not fixed_period or int(slot["dars_raqami"]) == fixed_period]
            if fixed_period and not slots:
                reject_counter.update(["belgilangan sinf soati dars raqami smenada mavjud emas"])
            for slot in slots:
                period = int(slot["dars_raqami"])
                teachers = _v1852_choose_teacher(job, day, period, state, context)
                room_keys = _v1852_room_keys(job, teachers, context["classes"])
                reasons = _v1852_candidate_reasons(job, day, period, teachers, room_keys, state, context)
                if reasons:
                    reject_counter.update(reasons)
                    continue
                score = 0.0 if fixed_day and fixed_period else _v1852_candidate_score(job, day, period, teachers, state, context, rng)
                candidates.append((score, day, period, teachers, room_keys))
        if not candidates:
            unplaced.append({"job": job, "sabablar": dict(reject_counter.most_common(6))})
            continue
        score, day, period, teachers, room_keys = min(candidates, key=lambda x: x[0])
        total_penalty += score
        _v1852_place_job(job, day, period, teachers, room_keys, state, context)
    state, unplaced = _v1852_repair_unplaced(state, unplaced, context, rng)
    gap_count = sum(_v1852_gap_count(periods) for periods in state["teacher_periods"].values())
    class_gap_count = sum(
        (max(set(period_jobs.keys())) - len(set(period_jobs.keys())))
        if period_jobs else 0
        for period_jobs in state.get("class_period_jobs", {}).values()
    )
    state["class_gap_count"] = int(class_gap_count)
    late_heavy = sum(1 for p in state["placements"] if p["period"] > p["job"]["preferred_last"] and p["job"]["weight"] >= 2)
    return state, unplaced, total_penalty, gap_count, late_heavy


class V1852Generate(BaseModel):
    maktab_id: int
    urinishlar_soni: int = 12


@app.post("/api/maktab/aqlli_jadval/v2/yaratish")
def v1852_generate(sorov: V1852Generate, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, user_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Jadvalni faqat maktab rahbariyati yaratadi")
        cur.execute("SELECT pg_try_advisory_xact_lock(%s) AS locked", (1900000000 + int(sorov.maktab_id),))
        if not bool((cur.fetchone() or {}).get("locked")):
            raise HTTPException(status_code=409, detail="Bu maktab uchun jadval boshqa oynada yaratilmoqda. Tugashini kuting.")

        # Jadval manbasi va hash hisoblanishidan oldin barcha sinflarning
        # SINF SOATI qoidasini tayyorlaymiz. Aks holda eski maktabda 21+1/22
        # o'rniga 21/22 ko'rinib, bir soat har safar yetishmay qolardi.
        _v199_ensure_class_hour_rules(
            cur, sorov.maktab_id, actor_id=user_id
        )

        if "_v1876_group_review_report" in globals():
            group_review = _v1876_group_review_report(cur, sorov.maktab_id)
            if not group_review.get("tayyor"):
                details = "; ".join(group_review.get("xatolar", [])[:10])
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Avval guruhli fanlarda qaysi guruhga qaysi o'qituvchi "
                        "kirishini tasdiqlang" + (f": {details}" if details else "")
                    ),
                )

        # DARS_BIRIKMALARI → sinf-fan yuklamasi → o'qituvchi jami bir xil manbaga keltiriladi.
        sync_report = _v1875_rebuild_schedule_sources(
            cur, sorov.maktab_id, cancel_drafts=True, reason="jadval_yaratish"
        )
        if sync_report.get("xatolar"):
            raise HTTPException(
                status_code=409,
                detail="Jadval manbasi mos emas: " + "; ".join(sync_report["xatolar"][:12]),
            )
        preflight = _v1875_preflight_report(cur, sorov.maktab_id)
        if not preflight.get("tayyor"):
            raise HTTPException(
                status_code=409,
                detail="Jadval yaratishdan oldingi tekshiruvdan o'tmadi: " + "; ".join(preflight.get("xatolar", [])[:12]),
            )
        source_hash = preflight.get("manba_hash")

        year, shifts, classes, loads, assignments, group_settings, rules_rows, availability_rows, teachers, rooms = _v1852_prepare_generation(cur, sorov.maktab_id)
        jobs, initial_warnings = _v1852_build_jobs(classes, loads, assignments, group_settings, teachers)
        class_hour_rules = _v1866_class_hour_rule_rows(cur, sorov.maktab_id)
        class_hour_jobs, class_hour_warnings = _v1866_build_class_hour_jobs(classes, class_hour_rules)
        jobs = class_hour_jobs + jobs
        initial_warnings.extend(class_hour_warnings)
        rules = _v1852_teacher_rules_map(rules_rows)
        hard, soft, method_hard, method_soft = _v1852_availability_maps(availability_rows)
        class_day_rule_rows = _v1856_class_day_rule_rows(cur, sorov.maktab_id)
        class_day_blocks = _v1856_class_day_rule_map(class_day_rule_rows)
        class_hour_counts = _v1852_Counter(
            int(job["teacher_options"][0]) for job in class_hour_jobs if job.get("teacher_options")
        )
        caps = {}
        for tid, row in teachers.items():
            base = float(row["haftalik_dars_soati"]) if row.get("haftalik_dars_soati") is not None else None
            extra = int(class_hour_counts.get(int(tid), 0))
            caps[tid] = (base + extra) if base is not None else None
        context = {
            "weekdays": int(year["hafta_kunlari"]), "shifts": shifts, "classes": classes,
            "rules": rules, "default_rules": {"kunlik_max": 6, "ketma_ket_max": 4, "okno_max": 1, "afzal_smena": 0, "eng_erta_dars": 1, "eng_kech_dars": 12},
            "hard": hard, "soft": soft, "method_hard": method_hard, "method_soft": method_soft,
            "teacher_caps": caps, "class_day_blocks": class_day_blocks,
        }

        # Generator o'n minglab variantlarni Python xotirasida hisoblaydi. Shu
        # paytda ochiq tranzaksiya 30 soniyadan ortiq bo'sh qolsa PostgreSQL
        # idle_in_transaction_session_timeout sabab ulanishni yopadi. Manba
        # sinxronlashini avval commit qilib, hisoblash vaqtida DB ulanishini
        # havuzga qaytaramiz; natijani yozishda yangi ulanish olamiz.
        conn.commit()
        cur.close()
        conn.close()
        cur = None
        conn = None

        # Railway HTTP/worker ulanishi ochiq turgan paytda 48–96 ta to'liq
        # variantni ketma-ket hisoblash brauzerga ``Failed to fetch`` qaytarar
        # edi. Endi so'ralgan urinish haqiqatan hurmat qilinadi va generator
        # qat'iy vaqt byudjeti ichida eng yaxshi topilgan draftni qaytaradi.
        # Shu bilan algoritm sifati saqlanadi, lekin POST /yaratish proksi
        # va gunicorn timeoutidan oldin albatta yakunlanadi.
        requested_attempts = max(4, min(24, int(sorov.urinishlar_soni or 12)))
        try:
            generation_budget = float(
                os.getenv("SAMTM_JADVAL_GENERATION_BUDGET_SECONDS", "18")
            )
        except (TypeError, ValueError):
            generation_budget = 18.0
        generation_budget = max(8.0, min(24.0, generation_budget))
        generation_started = _samtm_time.monotonic()
        completed_attempts = 0
        stopped_by_budget = False
        best = None
        base_seed = int(datetime.now().timestamp())
        print(
            "[JADVAL-REV53] boshlandi "
            f"maktab_id={sorov.maktab_id} darslar={len(jobs)} "
            f"reja_urinish={requested_attempts} byudjet={generation_budget:.0f}s",
            flush=True,
        )
        for index in range(requested_attempts):
            if index > 0 and (_samtm_time.monotonic() - generation_started) >= generation_budget:
                stopped_by_budget = True
                break
            result = _v1852_generate_attempt(jobs, context, base_seed + index * 7919)
            completed_attempts = index + 1
            state, unplaced, penalty, gaps, late = result
            class_gaps = int(state.get("class_gap_count", 0))
            comfort = state.get("v196_metrics", {})
            class_imbalance = int(comfort.get("sinf_kun_taqsimoti_farqi", 0))
            short_days = int(comfort.get("sinf_qisqa_kunlari", 0))
            late_core = int(comfort.get("asosiy_fan_5_6", 0))
            early_practical = int(comfort.get("amaliy_fan_1_2", 0))
            pe_before_core = int(comfort.get("jismoniydan_keyin_ogir_fan", 0))
            cross_shift_blocks = int(comfort.get("oqituvchi_smenalar_orasi_blok", 0))
            cross_shift_minutes = int(comfort.get("oqituvchi_smenalar_orasi_daqiqa", 0))
            cross_shift_max = int(comfort.get("eng_uzoq_smena_oraligi_daqiqa", 0))
            cross_shift_over_two = int(comfort.get("ikki_smenali_2soatdan_uzoq", 0))
            cross_shift_long = int(comfort.get("ikki_smenali_uzoq_tanaffus", 0))
            teacher_gap_days = int(comfort.get("oqituvchi_oknoli_smena_kun", 0))
            teacher_multi_gap_days = int(comfort.get("oqituvchi_kop_oknoli_smena_kun", 0))
            teacher_max_gap = int(comfort.get("eng_katta_ichki_okno", 0))
            teacher_internal_gaps = int(comfort.get("oqituvchi_ichki_okno", gaps))
            unified_three_hour = int(comfort.get("oqituvchi_birlashgan_3soat_okno", 0))
            unified_two_hour = int(comfort.get("oqituvchi_birlashgan_2soat_okno", 0))
            unified_max = int(comfort.get("oqituvchi_birlashgan_eng_katta_daqiqa", 0))
            unified_minutes = int(comfort.get("oqituvchi_birlashgan_okno_daqiqa", 0))
            unified_count = int(comfort.get("oqituvchi_birlashgan_okno_soni", 0))
            compact_overflow_days = int(comfort.get("10_19_limitdan_ortiq_kun", 0))
            compact_extra_days = int(comfort.get("10_19_ortiqcha_kun", 0))
            compact_adjacent_days = int(comfort.get("10_19_yonma_yon_kun", 0))
            compact_unbalanced_days = int(comfort.get("10_19_notekis_kun", 0))
            teacher_active_days = int(comfort.get("oqituvchi_faol_kun", 0))
            rank = (
                len(unplaced), class_gaps,
                compact_overflow_days, compact_extra_days,
                compact_adjacent_days, compact_unbalanced_days,
                class_imbalance, short_days,
                unified_three_hour, unified_two_hour, unified_max,
                unified_minutes, unified_count,
                cross_shift_long,
                cross_shift_over_two, cross_shift_max, cross_shift_minutes,
                teacher_multi_gap_days, teacher_max_gap, teacher_gap_days,
                teacher_internal_gaps,
                teacher_active_days,
                early_practical, late_core, pe_before_core,
                cross_shift_blocks, gaps, late, round(penalty, 2),
            )
            if best is None or rank < best[0]:
                best = (rank, result)
            # To'liq va sinf oknosiz variant topilgan bo'lsa, sifatni yana bir
            # necha urug'da solishtiramiz; qolgan vaqtni bekorga sarflamaymiz.
            elapsed = _samtm_time.monotonic() - generation_started
            if completed_attempts >= 6 and not unplaced and class_gaps == 0:
                if elapsed >= min(10.0, generation_budget * 0.55):
                    break

        if best is None:
            # Amalda birinchi urinish vaqt tekshiruvidan oldin bajariladi.
            # Bu qo'riqchi noto'g'ri muhit qiymati sabab bo'sh natija
            # qaytishining oldini oladi.
            result = _v1852_generate_attempt(jobs, context, base_seed)
            best = ((len(result[1]),), result)
            completed_attempts = 1
        _, (state, unplaced, penalty, gap_count, late_heavy) = best
        # Ko'p urinishdan tanlangan eng yaxshi jadvalni sinf kataklarini
        # o'zgartirmasdan yana bir marta o'qituvchi nuqtai nazaridan siqamiz.
        # Bir sinf-kun ichidagi ikki fanning o'rni xavfsiz almashtiriladi:
        # sinfda okno paydo bo'lmaydi, lekin ustozning ichki oynasi va ikki
        # smena orasidagi 4–5 soatlik kutishi qisqaradi.
        final_rng = _v1852_random.Random(base_seed ^ 0x20_26_08_26)
        state = _v196_compact_class_gaps(
            state, context, final_rng, max_moves=48
        )
        state = _v196_optimize_teacher_windows(
            state, context, final_rng, max_swaps=54
        )
        state["class_gap_count"] = _v196_class_gap_count(state)
        final_metrics = _v196_attempt_metrics(state, context)
        state["v196_metrics"] = final_metrics
        gap_count = int(final_metrics.get("oqituvchi_ichki_okno", 0))
        placed_count = len(state["placements"])
        total_count = len(jobs)
        placement_ratio = (placed_count / total_count) if total_count else 1.0
        class_gap_count = int(state.get("class_gap_count", 0))
        quality = max(0, min(100, round(
            placement_ratio * 88
            + max(0, 12 - class_gap_count * 4 - gap_count * 0.25 - late_heavy * 0.2)
        )))
        unplaced_payload = []
        for item in unplaced:
            job = item["job"]
            cls = classes.get(job["sinf_id"], {})
            top_reasons = item.get("sabablar") or {"mos bo'sh vaqt topilmadi": 1}
            primary_reason = max(top_reasons, key=top_reasons.get)
            parallel_groups = job.get("groups") or []
            if len(parallel_groups) >= 2:
                # ``sinf band`` faqat oxirgi ko'ringan simptom: bu paketda
                # asl talab sinf + barcha guruh ustozlari bir vaqtda bo'sh
                # bo'lishidir. Foydalanuvchiga aynan shu ildiz sababni aytamiz.
                primary_reason = "parallel guruhlar uchun umumiy vaqt topilmadi"
            reason_text, solution_text = _v201_unplaced_reason_copy(primary_reason)
            teacher_rows = _v201_unplaced_teacher_rows(job, teachers)
            unplaced_payload.append({
                "sinf_id": job["sinf_id"], "sinf": f"{cls.get('sinf','')}-{cls.get('harf','')}",
                "fan": job["fan"], "takror_raqami": job["occurrence"],
                "sabab": primary_reason, "sabablar": top_reasons,
                "sabab_izohi": reason_text, "yechim": solution_text,
                "parallel_guruh": len(parallel_groups) >= 2,
                "guruhlar": [
                    {
                        "guruh_kaliti": group.get("guruh_kaliti") or "whole",
                        "oqituvchi_user_id": group.get("teacher"),
                        "oqituvchi_ismi": (
                            teachers.get(int(group["teacher"]), {}).get("full_name")
                            if group.get("teacher") is not None else None
                        ),
                    }
                    for group in parallel_groups
                ],
                "oqituvchilar": teacher_rows,
                "oqituvchi_user_idlar": sorted({int(row["user_id"]) for row in teacher_rows}),
            })
        teacher_unplaced = _v1852_defaultdict(list)
        for problem in unplaced_payload:
            for teacher in problem.get("oqituvchilar") or []:
                teacher_unplaced[int(teacher["user_id"])].append({
                    "sinf": problem.get("sinf"),
                    "fan": teacher.get("fan") or problem.get("fan"),
                    "guruh_kaliti": teacher.get("guruh_kaliti") or "whole",
                    "parallel_guruh": bool(problem.get("parallel_guruh")),
                    "soat": float(teacher.get("soat") or 0),
                    "sabab": problem.get("sabab"),
                    "sabab_izohi": problem.get("sabab_izohi"),
                    "yechim": problem.get("yechim"),
                })
        teacher_summary = []
        for tid, teacher in teachers.items():
            actual = round(float(state["teacher_week"].get(tid, 0)), 1)
            base = float(teacher["haftalik_dars_soati"]) if teacher.get("haftalik_dars_soati") is not None else None
            extra = int(class_hour_counts.get(int(tid), 0))
            cap = caps.get(tid)
            missing_details = teacher_unplaced.get(int(tid), [])
            teacher_summary.append({
                "user_id": tid, "full_name": teacher["full_name"], "jadval_soati": actual,
                "asosiy_yuklama": base, "sinf_soati_soni": extra, "yuklama": cap,
                "farq": None if cap is None else cap - actual,
                "yetishmagan_darslar": missing_details,
                "yetishmagan_soat": round(sum(float(row.get("soat") or 0) for row in missing_details), 1),
            })
        warnings = list(initial_warnings)
        for rule in class_day_rule_rows[:50]:
            warnings.append(f"Qattiq qoida: {rule.get('yorliq')}")
        for job in jobs:
            if job["groups"] and any(g.get("xona_id") is None for g in job["groups"][1:]):
                cls = classes[job["sinf_id"]]
                message = f"{cls['sinf']}-{cls['harf']} {job['fan']}: bo'linishga xona topilmadi"
                if message not in warnings:
                    warnings.append(message)
        diagnostics = {
            "muammolar": unplaced_payload[:100], "ogohlantirishlar": warnings[:100],
            "oqituvchi_yuklamasi": teacher_summary,
            "sinf_oknolari": class_gap_count,
            "oqituvchi_oknolari": gap_count,
            "oknolar": gap_count,
            "kech_tushgan_ogir_darslar": late_heavy, "yumshoq_jazo": round(penalty, 2),
            "qulaylik_strategiyasi": state.get("v196_metrics", {}),
            "urinishlar_soni": completed_attempts,
            "urinishlar_rejasi": requested_attempts,
            "hisoblash_soniya": round(_samtm_time.monotonic() - generation_started, 2),
            "vaqt_chegarasi_soniya": generation_budget,
            "vaqt_chegarasida_toxtadi": stopped_by_budget,
            "manba_mosligi": preflight,
            "tasdiqlash_mumkin": False,
        }
        print(
            "[JADVAL-REV53] hisoblash tugadi "
            f"maktab_id={sorov.maktab_id} urinish={completed_attempts} "
            f"joylashdi={placed_count}/{total_count} "
            f"soniya={diagnostics['hisoblash_soniya']} "
            f"vaqt_chegarasi={stopped_by_budget}",
            flush=True,
        )

        # Uzoq hisoblashdan keyin yangi, sog'lom ulanish bilan yozamiz. Shu
        # orada yuklama yoki vaqt qoidasi o'zgargan bo'lsa eskirgan natijani
        # saqlamaymiz — foydalanuvchi yangi manba bilan qayta yaratadi.
        conn = _db()
        cur = conn.cursor()
        cur.execute(
            "SELECT pg_try_advisory_xact_lock(%s) AS locked",
            (1900000000 + int(sorov.maktab_id),),
        )
        if not bool((cur.fetchone() or {}).get("locked")):
            raise HTTPException(
                status_code=409,
                detail="Bu maktab uchun boshqa jadval yozilmoqda. Bir necha soniyadan keyin qayta urinib ko'ring.",
            )
        current_source_hash = _v1875_source_fingerprint(cur, sorov.maktab_id)
        if current_source_hash != source_hash:
            raise HTTPException(
                status_code=409,
                detail="Jadval hisoblanayotgan paytda yuklama yoki vaqt sozlamasi o'zgardi. Yangi ma'lumot bilan yana yarating.",
            )
        cur.execute("""INSERT INTO aqlli_jadval_urinishlari_v2(
            maktab_id,holat,yaratgan_user_id,sifat,joylashtirildi,joylashtirilmadi,diagnostika,sozlamalar)
            VALUES(%s,'draft',%s,%s,%s,%s,%s::jsonb,%s::jsonb) RETURNING id""",
            (sorov.maktab_id, user_id, quality, placed_count, len(unplaced),
             json.dumps(diagnostics, ensure_ascii=False, default=str),
             json.dumps({"hafta_kunlari": context["weekdays"], "oquv_yili_id": year["id"],
                         "manba_hash": source_hash,
                         "sinf_kun_bloklari": [{"id": r.get("id"), "yorliq": r.get("yorliq")} for r in class_day_rule_rows],
                         "sinf_soatlari": [{"id": r.get("id"), "sinf_id": r.get("sinf_id"),
                                            "hafta_kuni": r.get("hafta_kuni"), "dars_raqami": r.get("dars_raqami")}
                                           for r in class_hour_rules]},
                        ensure_ascii=False)))
        run_id = cur.fetchone()["id"]
        shift_slot_map = {(s, int(slot["dars_raqami"])): slot for s, row in shifts.items() for slot in row["slotlar"]}
        entry_rows = []
        for placement in state["placements"]:
            job, day, period, selected_teachers = placement["job"], placement["day"], placement["period"], placement["teachers"]
            time_slot = shift_slot_map[(job["smena"], period)]
            if job.get("rotation_members"):
                class_row = classes[job["sinf_id"]]
                home_room_text = " ".join(x for x in [class_row.get("bino"), class_row.get("xona")] if x) or None
                for member in job["rotation_members"]:
                    phase = member.get("hafta_turi") or "toq"
                    member_teachers = _v199_rotation_member_teachers(member)
                    if member.get("groups"):
                        for group_index, (group, teacher) in enumerate(zip(member["groups"], member_teachers)):
                            room_id = group.get("xona_id")
                            room_text = rooms.get(room_id, {}).get("nomi") if room_id else (home_room_text if group_index == 0 else None)
                            entry_rows.append((
                                run_id, sorov.maktab_id, member["sinf_id"], day, member["smena"], period,
                                member["fan"], teacher, group["guruh_kaliti"], room_id, room_text,
                                time_slot["boshlanish"], time_slot["tugash"], member["load_id"],
                                member["occurrence"], phase,
                            ))
                    else:
                        teacher = member_teachers[0] if member_teachers else None
                        room_id = member.get("room_id")
                        room_text = rooms.get(room_id, {}).get("nomi") if room_id else home_room_text
                        entry_rows.append((
                            run_id, sorov.maktab_id, member["sinf_id"], day, member["smena"], period,
                            member["fan"], teacher, "whole", room_id, room_text,
                            time_slot["boshlanish"], time_slot["tugash"], member["load_id"],
                            member["occurrence"], phase,
                        ))
            elif job["groups"]:
                class_row = classes[job["sinf_id"]]
                home_room_text = " ".join(x for x in [class_row.get("bino"), class_row.get("xona")] if x) or None
                for group_index, (group, teacher) in enumerate(zip(job["groups"], selected_teachers)):
                    room_id = group.get("xona_id")
                    room_text = rooms.get(room_id, {}).get("nomi") if room_id else (home_room_text if group_index == 0 else None)
                    entry_rows.append((run_id, sorov.maktab_id, job["sinf_id"], day, job["smena"], period,
                                       job["fan"], teacher, group["guruh_kaliti"], room_id, room_text,
                                       time_slot["boshlanish"], time_slot["tugash"], job["load_id"], job["occurrence"], "har_hafta"))
            else:
                teacher = selected_teachers[0] if selected_teachers else None
                room_id = job.get("room_id")
                class_row = classes[job["sinf_id"]]
                room_text = rooms.get(room_id, {}).get("nomi") if room_id else " ".join(x for x in [class_row.get("bino"), class_row.get("xona")] if x) or None
                entry_rows.append((run_id, sorov.maktab_id, job["sinf_id"], day, job["smena"], period,
                                   job["fan"], teacher, "whole", room_id, room_text,
                                   time_slot["boshlanish"], time_slot["tugash"], job["load_id"], job["occurrence"], "har_hafta"))
        if entry_rows:
            psycopg2.extras.execute_values(cur, """INSERT INTO aqlli_jadval_slotlari_v2(
                urinish_id,maktab_id,sinf_id,hafta_kuni,smena,dars_raqami,fan_nomi,
                oqituvchi_user_id,guruh_kaliti,xona_id,xona_matni,boshlanish_vaqti,
                tugash_vaqti,yuklama_id,takror_raqami,hafta_turi) VALUES %s""", entry_rows, page_size=1000)

        jadval_mosligi = _v1875_schedule_integrity_report(
            cur, sorov.maktab_id, run_id
        )
        tasdiqlash_mumkin = bool(
            int(len(unplaced)) == 0 and jadval_mosligi.get("tayyor")
        )
        diagnostics["jadval_mosligi"] = jadval_mosligi
        diagnostics["tasdiqlash_mumkin"] = tasdiqlash_mumkin
        diagnostic_teachers = {
            int(row["user_id"]): row
            for row in teacher_summary if row.get("user_id") is not None
        }
        for teacher_row in jadval_mosligi.get("oqituvchilar", []):
            teacher_id = int(teacher_row.get("user_id") or 0)
            source = diagnostic_teachers.get(teacher_id, {})
            missing = max(
                0.0,
                float(teacher_row.get("reja") or 0) - float(teacher_row.get("jadval") or 0),
            )
            details = list(source.get("yetishmagan_darslar") or [])
            explained = round(sum(float(row.get("soat") or 0) for row in details), 1)
            if missing > explained + 0.01:
                details.append({
                    "sinf": "Fan–o'qituvchi birikmasi",
                    "fan": "Hisob tafovuti",
                    "soat": round(missing - explained, 1),
                    "sabab": "reja va aniq dars satrlari teng emas",
                    "sabab_izohi": (
                        "O'qituvchining haftalik rejasidagi soat bilan unga biriktirilgan "
                        "aniq fan–sinf–guruh satrlari yig'indisi teng emas."
                    ),
                    "yechim": (
                        "O'qituvchi yuklamasini ochib fan–sinf–guruh qatorlari yig'indisini "
                        "haftalik reja bilan tenglashtiring."
                    ),
                })
            teacher_row["yetishmagan_soat"] = round(missing, 1)
            teacher_row["yetishmagan_darslar"] = details
            if missing > 0:
                teacher_row["sabab_xulosasi"] = (
                    f"Reja {float(teacher_row.get('reja') or 0):g} soat, jadvalga "
                    f"{float(teacher_row.get('jadval') or 0):g} soat kirdi. "
                    f"{missing:g} soat joylashmagan; quyida har bir fan va sabab ko'rsatilgan."
                )
            else:
                teacher_row["sabab_xulosasi"] = "O'qituvchining barcha reja soati jadvalga to'liq kirgan."
        if not tasdiqlash_mumkin:
            quality = min(int(quality), 69)
        cur.execute(
            """UPDATE aqlli_jadval_urinishlari_v2
               SET sifat=%s,diagnostika=%s::jsonb
               WHERE id=%s""",
            (quality, json.dumps(diagnostics, ensure_ascii=False, default=str), run_id),
        )

        conn.commit()
        return {"holat": "draft_yaratildi", "urinish_id": run_id, "sifat": quality,
                "jami_soat": total_count, "joylashtirildi": placed_count,
                "joylashtirilmadi": len(unplaced), "diagnostika": diagnostics,
                "tasdiqlash_mumkin": tasdiqlash_mumkin,
                "moslik": jadval_mosligi}
    except Exception:
        if conn is not None:
            try:
                if not bool(getattr(conn, "closed", True)):
                    conn.rollback()
            except Exception:
                pass
        raise
    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@app.get("/api/maktab/aqlli_jadval/v2/urinish")
def v1852_run_detail(token: str, urinish_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        cur.execute("SELECT * FROM aqlli_jadval_urinishlari_v2 WHERE id=%s", (urinish_id,))
        run = cur.fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Jadval urinishi topilmadi")
        if not _v1852_staff(cur, user_id, run["maktab_id"]):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        cur.execute("""SELECT e.*,s.sinf,s.harf,u.full_name AS oqituvchi_ismi,r.nomi AS xona_nomi
                       FROM aqlli_jadval_slotlari_v2 e
                       JOIN maktab_sinflari s ON s.id=e.sinf_id
                       LEFT JOIN users u ON u.user_id=e.oqituvchi_user_id
                       LEFT JOIN aqlli_xonalar_v2 r ON r.id=e.xona_id
                       WHERE e.urinish_id=%s ORDER BY s.sinf::int,s.harf,e.hafta_kuni,e.smena,e.dars_raqami,e.guruh_kaliti""", (urinish_id,))
        entries = cur.fetchall()
        current_week_type = "toq" if datetime.now().isocalendar().week % 2 else "juft"
        return {"urinish": run, "slotlar": entries, "joriy_hafta_turi": current_week_type}
    finally:
        cur.close(); conn.close()


class V1852Approve(BaseModel):
    urinish_id: int
    majburan: bool = False


@app.post("/api/maktab/aqlli_jadval/v2/tasdiqlash")
def v1852_approve(sorov: V1852Approve, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        cur.execute("SELECT * FROM aqlli_jadval_urinishlari_v2 WHERE id=%s FOR UPDATE", (sorov.urinish_id,))
        run = cur.fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Jadval urinishi topilmadi")
        if not _v1852_manager(cur, user_id, run["maktab_id"]):
            raise HTTPException(status_code=403, detail="Faqat rahbariyat tasdiqlaydi")
        if "_v1876_group_review_report" in globals():
            group_review = _v1876_group_review_report(cur, run["maktab_id"])
            if not group_review.get("tayyor"):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Guruh va o'qituvchi taqsimoti o'zgargan yoki tasdiqlanmagan. "
                        "Taqsimotni qayta tasdiqlab, yangi draft yarating"
                    ),
                )
        if run["holat"] != "draft":
            raise HTTPException(status_code=409, detail="Faqat draft jadval tasdiqlanadi")

        exact_moslik = _v1875_schedule_integrity_report(
            cur, run["maktab_id"], run["id"]
        )
        if int(run.get("joylashtirilmadi") or 0) > 0 or not exact_moslik.get("tayyor"):
            details = "; ".join(exact_moslik.get("xatolar", [])[:12])
            if int(run.get("joylashtirilmadi") or 0) > 0:
                details = (
                    f"{int(run.get('joylashtirilmadi') or 0)} ta dars joylashtirilmagan"
                    + (f"; {details}" if details else "")
                )
            raise HTTPException(
                status_code=409,
                detail=(
                    "Jadval reja bilan 100% mos emas. Majburan tasdiqlash mumkin emas: "
                    + (details or "sinf, fan yoki o'qituvchi soatlarida farq bor")
                ),
            )

        violations = _v1856_schedule_block_violations(cur, run["maktab_id"], run["id"])
        if violations:
            details = "; ".join(
                f"{row['sinf']}-{row['harf']} · {row['kun_nomi']} ({row['dars_soni']} ta)"
                for row in violations[:8]
            )
            raise HTTPException(
                status_code=409,
                detail=f"Draftda sinf-kun qoidalariga zid darslar bor: {details}. Yangi draft yarating",
            )
        sinf_soati_xatolari = _v1866_class_hour_violations(cur, run["maktab_id"], run["id"])
        if sinf_soati_xatolari:
            details = "; ".join(row["izoh"] for row in sinf_soati_xatolari[:8])
            raise HTTPException(
                status_code=409,
                detail=f"Sinf soati qoidasi bajarilmagan: {details}. 3-bosqichdagi qoidani yoki o‘qituvchi vaqtini tuzatib yangi draft yarating",
            )
        gigiyena_xatolari = _v1874_schedule_hygiene_violations(
            cur, run["maktab_id"], run["id"]
        )
        if gigiyena_xatolari:
            details = "; ".join(
                f"{row['sinf']}: {row['sabab']}"
                for row in gigiyena_xatolari[:10]
            )
            raise HTTPException(
                status_code=409,
                detail=(
                    "Draft sanitariya-gigiyena qoidalariga zid: "
                    f"{details}. Yangi draft yarating"
                ),
            )
        if int(run["joylashtirilmadi"] or 0) > 0:
            raise HTTPException(
                status_code=409,
                detail="Joylashtirilmagan darslar bor. Jadval to'liq bo'lmaguncha tasdiqlanmaydi",
            )
        cur.execute("UPDATE aqlli_jadval_urinishlari_v2 SET holat='almashtirilgan' WHERE maktab_id=%s AND holat='tasdiqlangan'", (run["maktab_id"],))
        cur.execute("UPDATE aqlli_jadval_urinishlari_v2 SET holat='tasdiqlangan',tasdiqlangan_at=NOW() WHERE id=%s", (run["id"],))
        rebuild = _v1852_rebuild_all_topic_calendars(cur, run["maktab_id"])
        conn.commit()
        return {"holat": "tasdiqlandi", "urinish_id": run["id"],
                "moslik": exact_moslik, **rebuild}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.get("/api/maktab/aqlli_jadval/v2/faol")
def v1852_active_schedule(token: str, maktab_id: int, sinf_id: Optional[int] = None, oqituvchi_user_id: Optional[int] = None):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_staff(cur, user_id, maktab_id):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        run = _v1852_active_run(cur, maktab_id)
        if not run:
            return {"urinish": None, "slotlar": []}
        where = ["e.urinish_id=%s"]; args = [run["id"]]
        if sinf_id is not None:
            where.append("e.sinf_id=%s"); args.append(sinf_id)
        if oqituvchi_user_id is not None:
            where.append("e.oqituvchi_user_id=%s"); args.append(oqituvchi_user_id)
        cur.execute("""SELECT e.*,s.sinf,s.harf,u.full_name AS oqituvchi_ismi,
                              COALESCE(r.nomi,e.xona_matni) AS xona_nomi
                       FROM aqlli_jadval_slotlari_v2 e
                       JOIN maktab_sinflari s ON s.id=e.sinf_id
                       LEFT JOIN users u ON u.user_id=e.oqituvchi_user_id
                       LEFT JOIN aqlli_xonalar_v2 r ON r.id=e.xona_id
                       WHERE """ + " AND ".join(where) +
                    " ORDER BY e.hafta_kuni,e.smena,e.dars_raqami,s.sinf::int,s.harf,e.guruh_kaliti", tuple(args))
        current_week_type = "toq" if datetime.now().isocalendar().week % 2 else "juft"
        return {"urinish": run, "slotlar": cur.fetchall(), "joriy_hafta_turi": current_week_type}
    finally:
        cur.close(); conn.close()


class V1852ChangeRequest(BaseModel):
    slot_id: int
    yangi_hafta_kuni: int
    yangi_smena: int
    yangi_dars_raqami: int
    izoh: Optional[str] = None


@app.post("/api/maktab/aqlli_jadval/v2/ozgartirish_sorovi")
def v1852_change_request(sorov: V1852ChangeRequest, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        cur.execute("""SELECT e.*,r.holat,s.sinf AS sinf_daraja,s.harf AS sinf_harfi
                       FROM aqlli_jadval_slotlari_v2 e
                       JOIN aqlli_jadval_urinishlari_v2 r ON r.id=e.urinish_id
                       JOIN maktab_sinflari s ON s.id=e.sinf_id
                       WHERE e.id=%s""", (sorov.slot_id,))
        slot = cur.fetchone()
        if not slot or slot["holat"] != "tasdiqlangan":
            raise HTTPException(status_code=404, detail="Faol dars topilmadi")
        if str(slot.get("fan_nomi") or "").strip().casefold() == "sinf soati":
            raise HTTPException(
                status_code=409,
                detail="Sinf soati qo‘lda ko‘chirilmaydi. 3-bosqichda kun yoki dars raqamini o‘zgartirib yangi draft yarating",
            )
        if user_id != slot.get("oqituvchi_user_id") and not _v1852_manager(cur, user_id, slot["maktab_id"]):
            raise HTTPException(status_code=403, detail="Faqat shu dars o'qituvchisi yoki rahbariyat so'rov beradi")
        if sorov.yangi_hafta_kuni not in range(1, 7):
            raise HTTPException(status_code=400, detail="Hafta kuni Dushanbadan Shanbagacha bo'lishi kerak")
        rule_map = _v1856_class_day_rule_map(_v1856_class_day_rule_rows(cur, slot["maktab_id"]))
        blocked_reason = _v1856_class_day_block_reason(
            {"id": slot["sinf_id"], "sinf": slot.get("sinf_daraja"), "harf": slot.get("sinf_harfi")},
            sorov.yangi_hafta_kuni, rule_map,
        )
        if blocked_reason:
            raise HTTPException(status_code=400, detail=f"Darsni ko'chirish mumkin emas: {blocked_reason}")
        cur.execute("""INSERT INTO aqlli_jadval_ozgartirish_sorovlari_v2(
            maktab_id,slot_id,soragan_user_id,yangi_hafta_kuni,yangi_smena,yangi_dars_raqami,izoh)
            VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
            (slot["maktab_id"], slot["id"], user_id, sorov.yangi_hafta_kuni,
             sorov.yangi_smena, sorov.yangi_dars_raqami, sorov.izoh))
        request_id = cur.fetchone()["id"]
        conn.commit(); return {"holat": "yuborildi", "sorov_id": request_id}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def _v1852_topic_permission(cur, user_id: int, maktab_id: int, sinf_id: int, fan: str):
    if not _v1852_teacher_subject_allowed(cur, user_id, maktab_id, sinf_id, fan):
        raise HTTPException(status_code=403, detail="Faqat shu fan o'qituvchisi yoki rahbariyat mavzu rejasini o'zgartiradi")


@app.post("/api/maktab/aqlli_jadval/v2/mavzu_reja/dts_import")
def v1852_import_dts_topics(token: str, maktab_id: int, sinf_id: int, fan: str, chorak: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        _v1852_topic_permission(cur, user_id, maktab_id, sinf_id, fan)
        cur.execute("SELECT sinf FROM maktab_sinflari WHERE id=%s AND maktab_id=%s", (sinf_id, maktab_id))
        cls = cur.fetchone()
        if not cls:
            raise HTTPException(status_code=404, detail="Sinf topilmadi")
        cur.execute("""SELECT MIN(topic_code) AS topic_code,
                              COALESCE(NULLIF(mavzu_name,''),NULLIF(kichik_name,''),NULLIF(bolim_name,''),bob_name) AS mavzu
                       FROM dts_tree
                       WHERE grade=%s AND UPPER(TRIM(subject_name))=UPPER(TRIM(%s))
                         AND is_deleted=FALSE AND COALESCE(NULLIF(quarter,''),'1')=%s
                       GROUP BY COALESCE(NULLIF(mavzu_name,''),NULLIF(kichik_name,''),NULLIF(bolim_name,''),bob_name)
                       HAVING COALESCE(NULLIF(mavzu_name,''),NULLIF(kichik_name,''),NULLIF(bolim_name,''),bob_name) IS NOT NULL
                       ORDER BY MIN(topic_code)""", (str(cls["sinf"]), fan, str(chorak)))
        topics = [{"mavzu": row["mavzu"], "soat": 1, "turi": "mavzu", "topic_code": row["topic_code"], "manba": "dts"} for row in cur.fetchall()]
        return {"mavzular": topics, "sinf": cls["sinf"], "fan": fan, "chorak": chorak}
    finally:
        cur.close(); conn.close()


class V1852TopicItem(BaseModel):
    mavzu: str
    soat: int = 1
    turi: str = "mavzu"
    topic_code: Optional[str] = None
    manba: str = "qolda"


class V1852TopicPlan(BaseModel):
    maktab_id: int
    sinf_id: int
    fan_nomi: str
    chorak: int
    mavzular: list[V1852TopicItem]


@app.put("/api/maktab/aqlli_jadval/v2/mavzu_reja")
def v1852_topic_plan_save(sorov: V1852TopicPlan, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        _v1852_topic_permission(cur, user_id, sorov.maktab_id, sorov.sinf_id, sorov.fan_nomi)
        if sorov.chorak not in (1, 2, 3, 4):
            raise HTTPException(status_code=400, detail="Chorak 1–4 bo'lishi kerak")
        rows = []
        for index, item in enumerate(sorov.mavzular, 1):
            title = re.sub(r"\s+", " ", item.mavzu or "").strip()
            if not title:
                raise HTTPException(status_code=400, detail=f"{index}-mavzu nomi bo'sh")
            if item.turi not in {"mavzu", "nazorat", "xato_tahlil", "mustahkamlash", "masala"}:
                raise HTTPException(status_code=400, detail=f"{index}-mavzu turi noto'g'ri")
            rows.append((sorov.maktab_id, sorov.sinf_id, sorov.fan_nomi.strip(), sorov.chorak,
                         index, title, item.soat, item.turi, item.topic_code, item.manba if item.manba in {"qolda", "dts"} else "qolda"))
        cur.execute("DELETE FROM aqlli_mavzu_rejalari_v2 WHERE maktab_id=%s AND sinf_id=%s AND LOWER(fan_nomi)=LOWER(%s) AND chorak=%s",
                    (sorov.maktab_id, sorov.sinf_id, sorov.fan_nomi, sorov.chorak))
        if rows:
            psycopg2.extras.execute_values(cur, """INSERT INTO aqlli_mavzu_rejalari_v2(
                maktab_id,sinf_id,fan_nomi,chorak,tartib,mavzu,soat,turi,topic_code,manba) VALUES %s""", rows)
        conn.commit(); return {"holat": "saqlandi", "mavzu_soni": len(rows), "jami_soat": sum(int(r[6]) for r in rows)}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def _v1852_topic_sequence(plan_rows, available_count, load_row):
    base = []
    for row in plan_rows:
        for _ in range(max(1, int(row.get("soat") or 1))):
            base.append({"mavzu": row["mavzu"], "turi": row["turi"], "topic_code": row.get("topic_code")})
    if available_count <= len(base):
        return base[:available_count], [], base[available_count:]
    extra_count = available_count - len(base)
    controls = min(int(load_row.get("nazorat_soni") or 0), extra_count)
    analyses = controls if bool(load_row.get("nazoratdan_keyin_tahlil")) else 0
    if controls + analyses > extra_count:
        controls = extra_count // (2 if analyses else 1)
        analyses = controls if bool(load_row.get("nazoratdan_keyin_tahlil")) else 0
    reserve = []
    for number in range(1, controls + 1):
        reserve.append({"mavzu": f"Nazorat ishi {number}", "turi": "nazorat", "topic_code": None})
        if analyses:
            reserve.append({"mavzu": f"Nazorat ishi {number} xatolarini tahlil qilish", "turi": "xato_tahlil", "topic_code": None})
    reinforcement = min(int(load_row.get("mustahkamlash_soni") or 0), extra_count - len(reserve))
    for _ in range(reinforcement):
        reserve.append({"mavzu": "Mavzularni mustahkamlash", "turi": "mustahkamlash", "topic_code": None})
    toggle = 0
    while len(reserve) < extra_count:
        reserve.append({
            "mavzu": "Masalalar yechish va amaliy mashqlar" if toggle % 2 == 0 else "Chorak mavzularini mustahkamlash",
            "turi": "masala" if toggle % 2 == 0 else "mustahkamlash", "topic_code": None,
        })
        toggle += 1
    # Nazoratlarni chorak bo'ylab tarqatamiz, hammasini oxiriga tiqmaymiz.
    sequence = list(base)
    if controls and base:
        pairs = []
        cursor = 0
        while cursor < len(reserve):
            pair = [reserve[cursor]]
            cursor += 1
            if cursor < len(reserve) and reserve[cursor]["turi"] == "xato_tahlil":
                pair.append(reserve[cursor]); cursor += 1
            pairs.append(pair)
        result = []
        chunk = max(1, len(base) // (len(pairs) + 1))
        index = 0
        for pair in pairs:
            next_index = min(len(base), index + chunk)
            result.extend(base[index:next_index]); result.extend(pair); index = next_index
        result.extend(base[index:]); sequence = result
        while len(sequence) < available_count and cursor < len(reserve):
            sequence.append(reserve[cursor]); cursor += 1
    else:
        sequence.extend(reserve)
    sequence = sequence[:available_count]
    return sequence, reserve, []


def _v1852_schedule_occurrences(cur, maktab_id: int, sinf_id: int, fan: str, quarter_row, year_row, run_id: int):
    cur.execute("""SELECT MIN(id) AS id,hafta_kuni,smena,dars_raqami,hafta_turi,
                          MIN(oqituvchi_user_id) AS oqituvchi_user_id
                   FROM aqlli_jadval_slotlari_v2
                   WHERE urinish_id=%s AND sinf_id=%s AND LOWER(fan_nomi)=LOWER(%s)
                   GROUP BY hafta_kuni,smena,dars_raqami,hafta_turi
                   ORDER BY hafta_kuni,smena,dars_raqami,hafta_turi""",
                (run_id, sinf_id, fan))
    patterns = cur.fetchall()
    cur.execute("SELECT id,sinf,harf FROM maktab_sinflari WHERE id=%s AND maktab_id=%s", (sinf_id, maktab_id))
    class_row = cur.fetchone() or {"id": sinf_id}
    rule_map = _v1856_class_day_rule_map(_v1856_class_day_rule_rows(cur, maktab_id))
    occurrences = []
    current = quarter_row["boshlanish"]
    while current <= quarter_row["tugash"]:
        if _v1852_is_school_day(cur, maktab_id, current, int(year_row["hafta_kunlari"])):
            for pattern in patterns:
                if current.isoweekday() == int(pattern["hafta_kuni"]):
                    if _v1856_class_day_block_reason(class_row, current.isoweekday(), rule_map):
                        continue
                    phase = str(pattern.get("hafta_turi") or "har_hafta")
                    current_phase = "toq" if int(current.isocalendar().week) % 2 else "juft"
                    if phase not in {"har_hafta", current_phase}:
                        continue
                    occurrences.append({"sana": current, **pattern})
        current += timedelta(days=1)
    occurrences.sort(key=lambda x: (x["sana"], x["smena"], x["dars_raqami"]))
    return occurrences


def _v1852_distribute_topics_one(cur, maktab_id: int, sinf_id: int, fan: str, chorak: int):
    year = _v1852_active_year(cur, maktab_id)
    run = _v1852_active_run(cur, maktab_id)
    if not year or not run:
        return {"taqsimlandi": 0, "ogohlantirishlar": [f"{fan}: faol o'quv yili yoki tasdiqlangan jadval yo'q"]}
    cur.execute("SELECT * FROM aqlli_choraklar_v2 WHERE oquv_yili_id=%s AND chorak=%s", (year["id"], chorak))
    quarter = cur.fetchone()
    if not quarter:
        return {"taqsimlandi": 0, "ogohlantirishlar": [f"{chorak}-chorak sanasi topilmadi"]}
    occurrences = _v1852_schedule_occurrences(cur, maktab_id, sinf_id, fan, quarter, year, run["id"])
    if not occurrences:
        return {"taqsimlandi": 0, "ogohlantirishlar": [f"{fan}: tasdiqlangan jadvalda dars topilmadi"]}
    cur.execute("""SELECT * FROM aqlli_mavzu_rejalari_v2 WHERE maktab_id=%s AND sinf_id=%s
                   AND LOWER(fan_nomi)=LOWER(%s) AND chorak=%s ORDER BY tartib""",
                (maktab_id, sinf_id, fan, chorak))
    plan = cur.fetchall()
    if not plan:
        return {"taqsimlandi": 0, "ogohlantirishlar": [f"{fan}: mavzu rejasi kiritilmagan"]}
    cur.execute("""SELECT * FROM aqlli_sinf_fan_yuklamalari_v2 WHERE maktab_id=%s AND sinf_id=%s
                   AND LOWER(fan_nomi)=LOWER(%s)""", (maktab_id, sinf_id, fan))
    load = cur.fetchone() or {}
    cur.execute("""SELECT * FROM aqlli_mavzu_taqvimi_v2 WHERE maktab_id=%s AND sinf_id=%s
                   AND LOWER(fan_nomi)=LOWER(%s) AND chorak=%s AND qulflangan=TRUE""",
                (maktab_id, sinf_id, fan, chorak))
    locked = cur.fetchall()
    occupied = {(r["sana"], int(r["smena"]), int(r["dars_raqami"])) for r in locked}
    valid_keys = {(o["sana"], int(o["smena"]), int(o["dars_raqami"])) for o in occurrences}
    warnings = []
    for row in locked:
        key = (row["sana"], int(row["smena"]), int(row["dars_raqami"]))
        if key not in valid_keys:
            warnings.append(f"Qulflangan '{row['mavzu']}' {row['sana']} sanada jadvalga mos emas; o'qituvchi tekshirsin")
    free_occurrences = [o for o in occurrences if (o["sana"], int(o["smena"]), int(o["dars_raqami"])) not in occupied]
    sequence, added, overflow = _v1852_topic_sequence(plan, len(free_occurrences), load)
    cur.execute("""DELETE FROM aqlli_mavzu_taqvimi_v2 WHERE maktab_id=%s AND sinf_id=%s
                   AND LOWER(fan_nomi)=LOWER(%s) AND chorak=%s AND qulflangan=FALSE""",
                (maktab_id, sinf_id, fan, chorak))
    rows = []
    for order, (occurrence, topic) in enumerate(zip(free_occurrences, sequence), 1):
        rows.append((maktab_id, run["id"], occurrence["id"], sinf_id, fan, chorak,
                     occurrence["sana"], occurrence["hafta_kuni"], occurrence["smena"],
                     occurrence["dars_raqami"], order, topic["mavzu"], topic["turi"],
                     "avto", False, occurrence.get("oqituvchi_user_id")))
    if rows:
        psycopg2.extras.execute_values(cur, """INSERT INTO aqlli_mavzu_taqvimi_v2(
            maktab_id,urinish_id,slot_id,sinf_id,fan_nomi,chorak,sana,hafta_kuni,smena,
            dars_raqami,tartib,mavzu,turi,manba,qulflangan,oqituvchi_user_id) VALUES %s""", rows)
    if overflow:
        warnings.append(f"{fan}: {len(overflow)} soatlik mavzu chorakdagi darslarga sig'madi")
    return {"taqsimlandi": len(rows), "avto_qoshildi": added, "sigmagan": overflow, "ogohlantirishlar": warnings}


@app.post("/api/maktab/aqlli_jadval/v2/mavzularni_taqsimlash")
def v1852_distribute_topics(token: str, maktab_id: int, sinf_id: int, fan: str, chorak: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        _v1852_topic_permission(cur, user_id, maktab_id, sinf_id, fan)
        result = _v1852_distribute_topics_one(cur, maktab_id, sinf_id, fan, chorak)
        conn.commit(); return {"holat": "taqsimlandi", **result}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.get("/api/maktab/aqlli_jadval/v2/mavzu_reja")
def v1852_topic_plan_get(token: str, maktab_id: int, sinf_id: int, fan: str, chorak: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_staff(cur, user_id, maktab_id):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        cur.execute("""SELECT * FROM aqlli_mavzu_rejalari_v2 WHERE maktab_id=%s AND sinf_id=%s
                       AND LOWER(fan_nomi)=LOWER(%s) AND chorak=%s ORDER BY tartib""",
                    (maktab_id, sinf_id, fan, chorak))
        plan = cur.fetchall()
        cur.execute("""SELECT * FROM aqlli_mavzu_taqvimi_v2 WHERE maktab_id=%s AND sinf_id=%s
                       AND LOWER(fan_nomi)=LOWER(%s) AND chorak=%s ORDER BY sana,smena,dars_raqami""",
                    (maktab_id, sinf_id, fan, chorak))
        calendar = cur.fetchall()
        return {"mavzular": plan, "taqvim": calendar}
    finally:
        cur.close(); conn.close()


class V1852TopicCalendarEdit(BaseModel):
    maktab_id: int
    taqvim_id: int
    mavzu: Optional[str] = None
    sana: Optional[date] = None


@app.patch("/api/maktab/aqlli_jadval/v2/mavzu_taqvimi")
def v1852_topic_calendar_edit(sorov: V1852TopicCalendarEdit, token: str):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        cur.execute("SELECT * FROM aqlli_mavzu_taqvimi_v2 WHERE id=%s AND maktab_id=%s", (sorov.taqvim_id, sorov.maktab_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Mavzu taqvimi yozuvi topilmadi")
        _v1852_topic_permission(cur, user_id, sorov.maktab_id, row["sinf_id"], row["fan_nomi"])
        new_date = sorov.sana or row["sana"]
        cur.execute("SELECT id,sinf,harf FROM maktab_sinflari WHERE id=%s AND maktab_id=%s", (row["sinf_id"], sorov.maktab_id))
        class_row = cur.fetchone() or {"id": row["sinf_id"]}
        rule_map = _v1856_class_day_rule_map(_v1856_class_day_rule_rows(cur, sorov.maktab_id))
        blocked_reason = _v1856_class_day_block_reason(class_row, new_date.isoweekday(), rule_map)
        if blocked_reason:
            raise HTTPException(status_code=400, detail=f"Mavzuni bu sanaga ko'chirish mumkin emas: {blocked_reason}")
        year = _v1852_active_year(cur, sorov.maktab_id)
        run = _v1852_active_run(cur, sorov.maktab_id)
        if not year or not run or not _v1852_is_school_day(cur, sorov.maktab_id, new_date, int(year["hafta_kunlari"])):
            raise HTTPException(status_code=400, detail="Tanlangan sana o'qish kuni emas")
        cur.execute("SELECT boshlanish,tugash FROM aqlli_choraklar_v2 WHERE oquv_yili_id=%s AND chorak=%s", (year["id"], row["chorak"]))
        quarter = cur.fetchone()
        if not quarter or not (quarter["boshlanish"] <= new_date <= quarter["tugash"]):
            raise HTTPException(status_code=400, detail="Tanlangan sana shu chorak chegarasida emas")
        cur.execute("""SELECT MIN(id) AS id,hafta_kuni,smena,dars_raqami,MIN(oqituvchi_user_id) AS oqituvchi_user_id
                       FROM aqlli_jadval_slotlari_v2 WHERE urinish_id=%s AND sinf_id=%s
                         AND LOWER(fan_nomi)=LOWER(%s) AND hafta_kuni=%s
                       GROUP BY hafta_kuni,smena,dars_raqami ORDER BY smena,dars_raqami LIMIT 1""",
                    (run["id"], row["sinf_id"], row["fan_nomi"], new_date.isoweekday()))
        slot = cur.fetchone()
        if not slot:
            raise HTTPException(status_code=400, detail="Bu sananing hafta kunida ushbu fan darsi yo'q")
        cur.execute("""SELECT id FROM aqlli_mavzu_taqvimi_v2 WHERE maktab_id=%s AND sinf_id=%s
                       AND LOWER(fan_nomi)=LOWER(%s) AND chorak=%s AND sana=%s
                       AND smena=%s AND dars_raqami=%s AND id<>%s LIMIT 1""",
                    (sorov.maktab_id, row["sinf_id"], row["fan_nomi"], row["chorak"],
                     new_date, slot["smena"], slot["dars_raqami"], row["id"]))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Bu sana va dars vaqtida boshqa mavzu allaqachon turibdi")
        title = re.sub(r"\s+", " ", sorov.mavzu or row["mavzu"]).strip()
        cur.execute("""UPDATE aqlli_mavzu_taqvimi_v2 SET sana=%s,hafta_kuni=%s,smena=%s,
                       dars_raqami=%s,slot_id=%s,mavzu=%s,manba='oqituvchi',qulflangan=TRUE,
                       oqituvchi_user_id=%s WHERE id=%s""",
                    (new_date, new_date.isoweekday(), slot["smena"], slot["dars_raqami"],
                     slot["id"], title, slot.get("oqituvchi_user_id"), row["id"]))
        conn.commit(); return {"holat": "yangilandi", "qulflangan": True}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.post("/api/maktab/aqlli_jadval/v2/mavzu_taqvimi/qulfni_och")
def v1852_topic_unlock(token: str, maktab_id: int, taqvim_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        cur.execute("SELECT * FROM aqlli_mavzu_taqvimi_v2 WHERE id=%s AND maktab_id=%s", (taqvim_id, maktab_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Yozuv topilmadi")
        _v1852_topic_permission(cur, user_id, maktab_id, row["sinf_id"], row["fan_nomi"])
        cur.execute("UPDATE aqlli_mavzu_taqvimi_v2 SET qulflangan=FALSE,manba='avto' WHERE id=%s", (taqvim_id,))
        result = _v1852_distribute_topics_one(cur, maktab_id, row["sinf_id"], row["fan_nomi"], row["chorak"])
        conn.commit(); return {"holat": "avtomatik_taqsimotga_qaytdi", **result}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()

# ========================= V18.52 END =========================

# ═══════════════════════════════════════════════════════════
# V18.54 — KASBIY RIVOJLANISH KUNI + OMMAVIY O'QITUVCHI VAQTI
# Aniq hafta kuni respublika bo'yicha bitta qilib belgilanmagan; tizim
# fan guruhlari va maktab haftasidan kelib chiqib TAXMINIY tavsiya beradi.
# ═══════════════════════════════════════════════════════════

class V1854BulkTeacherAvailability(BaseModel):
    maktab_id: int
    user_ids: list[int]
    qoidalar: Optional[V1852TeacherRules] = None
    vaqtlar: list[dict] = []
    rejim: str = "almashtirish"  # almashtirish | ustiga_qoshish


def _v1854_validate_time_items(items):
    rows = []
    for item in items:
        day = int(item.get("hafta_kuni") or 0)
        shift = int(item.get("smena") or 0)
        period = int(item.get("dars_raqami") or 0)
        kind = str(item.get("turi") or "")
        hard = bool(item.get("qattiq", True))
        if day not in range(1, 8) or shift not in (0, 1, 2) or period not in range(0, 13) or kind not in _V1852_VAQT_TURLARI:
            raise HTTPException(status_code=400, detail="Ommaviy vaqt sozlamalaridan biri noto'g'ri")
        if kind == "metod_kuni":
            shift, period = 0, 0
            hard = True
        rows.append((day, shift, period, kind, hard, item.get("izoh")))
    return rows


@app.put("/api/maktab/aqlli_jadval/v2/oqituvchi_vaqti_bulk")
def v1854_teacher_availability_bulk(sorov: V1854BulkTeacherAvailability, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Ommaviy sozlamani faqat maktab rahbariyati qo'llaydi")
        user_ids = list(dict.fromkeys(int(x) for x in sorov.user_ids if int(x)))
        if not user_ids:
            raise HTTPException(status_code=400, detail="Kamida bitta o'qituvchini tanlang")
        if sorov.rejim not in ("almashtirish", "ustiga_qoshish"):
            raise HTTPException(status_code=400, detail="Ommaviy qo'llash rejimi noto'g'ri")
        cur.execute("SELECT user_id FROM users WHERE maktab_id=%s AND user_id=ANY(%s)", (sorov.maktab_id, user_ids))
        topilgan = {int(r["user_id"]) for r in cur.fetchall()}
        yoq = [x for x in user_ids if x not in topilgan]
        if yoq:
            raise HTTPException(status_code=400, detail=f"Maktabda topilmagan xodim IDlari: {yoq[:10]}")
        rows = _v1854_validate_time_items(sorov.vaqtlar)
        for uid in user_ids:
            if sorov.qoidalar is not None:
                r = sorov.qoidalar
                if r.eng_kech_dars < r.eng_erta_dars:
                    raise HTTPException(status_code=400, detail="Eng kech dars eng erta darsdan oldin bo'lmaydi")
                cur.execute("""INSERT INTO aqlli_oqituvchi_qoidalari_v2(
                    maktab_id,user_id,kunlik_max,ketma_ket_max,okno_max,afzal_smena,eng_erta_dars,eng_kech_dars)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(maktab_id,user_id) DO UPDATE SET
                      kunlik_max=EXCLUDED.kunlik_max,ketma_ket_max=EXCLUDED.ketma_ket_max,
                      okno_max=EXCLUDED.okno_max,afzal_smena=EXCLUDED.afzal_smena,
                      eng_erta_dars=EXCLUDED.eng_erta_dars,eng_kech_dars=EXCLUDED.eng_kech_dars""",
                    (sorov.maktab_id,uid,r.kunlik_max,r.ketma_ket_max,r.okno_max,r.afzal_smena,r.eng_erta_dars,r.eng_kech_dars))
            if sorov.rejim == "almashtirish":
                cur.execute("DELETE FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s AND user_id=%s", (sorov.maktab_id,uid))
            for day, shift, period, kind, hard, note in rows:
                cur.execute("""INSERT INTO aqlli_oqituvchi_vaqti_v2(
                    maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi,qattiq,izoh)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi) DO UPDATE SET
                      qattiq=EXCLUDED.qattiq,izoh=EXCLUDED.izoh""",
                    (sorov.maktab_id,uid,day,shift,period,kind,hard,note))
        conn.commit()
        return {"holat":"saqlandi","o'qituvchi_soni":len(user_ids),"vaqt_soni":len(rows)}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V1854MethodSuggestion(BaseModel):
    maktab_id: int
    user_ids: list[int] = []
    saqlash: bool = False
    qattiq: bool = False
    almashtirish: bool = False


def _v1854_subject_group(fanlari):
    text = " ".join(str(fanlari or "").lower().replace("\\n", " ").split())
    if any(k in text for k in ("boshlang", "maktabgacha")):
        return "Boshlang'ich ta'lim"
    if any(k in text for k in ("algebra", "geometri", "matemat", "informat", "fizika", "astronom")):
        return "Aniq fanlar"
    if any(k in text for k in ("biolog", "kimyo", "geograf", "tabiiy", "ekolog")):
        return "Tabiiy fanlar"
    if any(k in text for k in ("ingliz", "rus tili", "nemis", "fransuz", "ona tili", "adabiyot")):
        return "Tillar va adabiyot"
    if any(k in text for k in ("tarix", "huquq", "tarbiya", "iqtisod", "ma'nav")):
        return "Ijtimoiy fanlar"
    if any(k in text for k in ("musiqa", "tasvir", "chizmach", "texnolog", "jismoniy")):
        return "Amaliy fanlar"
    return "Boshqa fanlar"


@app.post("/api/maktab/aqlli_jadval/v2/metod_kun_tavsiya")
def v1854_method_day_suggest(sorov: V1854MethodSuggestion, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Kasbiy rivojlanish kunini faqat maktab rahbariyati tavsiya qiladi")
        year = _v1852_active_year(cur, sorov.maktab_id)
        weekdays = int((year or {}).get("hafta_kunlari") or 6)
        ids = list(dict.fromkeys(int(x) for x in sorov.user_ids if int(x)))
        teachers = _v1859_effective_teachers(cur, sorov.maktab_id, ids or None)
        teachers = [row for row in teachers if row.get("dars_beruvchi")]
        groups = {}
        for t in teachers:
            groups.setdefault(_v1854_subject_group(t.get("fanlari")), []).append(t)
        day_counts = {d:0 for d in range(1,weekdays+1)}
        group_days = {}
        for group in sorted(groups, key=lambda g: (-len(groups[g]), g)):
            day = min(day_counts, key=lambda d: (day_counts[d], d))
            group_days[group] = day
            day_counts[day] += len(groups[group])
        existing = set()
        cur.execute("SELECT user_id FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s AND turi='metod_kuni'", (sorov.maktab_id,))
        existing = {int(r["user_id"]) for r in cur.fetchall()}
        suggestions = []
        saved = 0
        for group, rows in groups.items():
            day = group_days[group]
            for t in rows:
                uid = int(t["user_id"])
                suggestions.append({
                    "user_id":uid,"full_name":t["full_name"],"fan_guruhi":group,
                    "fanlari":t.get("fanlar_royxati") or [],
                    "sinflari":t.get("sinflar_royxati") or [],
                    "hafta_kuni":day,"kun_nomi":_V1852_HAFTA.get(day,str(day)),
                    "holat":"taxminiy","mavjud":uid in existing,
                })
                if sorov.saqlash:
                    if uid in existing and not sorov.almashtirish:
                        continue
                    if sorov.almashtirish:
                        cur.execute("DELETE FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s AND user_id=%s AND turi='metod_kuni'", (sorov.maktab_id,uid))
                    cur.execute("""INSERT INTO aqlli_oqituvchi_vaqti_v2(
                        maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi,qattiq,izoh)
                        VALUES(%s,%s,%s,0,0,'metod_kuni',%s,%s)
                        ON CONFLICT(maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi) DO UPDATE SET
                          qattiq=EXCLUDED.qattiq,izoh=EXCLUDED.izoh""",
                        (sorov.maktab_id,uid,day,sorov.qattiq,
                         "V18.54 taxminiy kasbiy rivojlanish kuni; tuman/tayanch maktab jadvali bilan tasdiqlang"))
                    saved += 1
        if sorov.saqlash:
            conn.commit()
        return {
            "tavsiyalar":suggestions,"saqlandi":saved,
            "ogohlantirish":"Kasbiy rivojlanish kuni rasmiy tizimda mavjud, ammo aniq hafta kuni hudud va tayanch maktab jadvali bilan belgilanadi. Bu faqat taxminiy, tahrirlanadigan tavsiya.",
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.get("/api/maktab/aqlli_jadval/v2/oqituvchi_fan_hisoboti")
def v1859_teacher_subject_report(token: str, maktab_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_staff(cur, user_id, maktab_id):
            raise HTTPException(status_code=403, detail="Bu maktab xodimlarini ko'rishga ruxsat yo'q")
        teachers = _v1859_effective_teachers(cur, maktab_id)
        cur.execute("""SELECT user_id,hafta_kuni,qattiq,izoh
                       FROM aqlli_oqituvchi_vaqti_v2
                       WHERE maktab_id=%s AND turi='metod_kuni'
                       ORDER BY user_id,hafta_kuni""", (maktab_id,))
        methods = {}
        for row in cur.fetchall():
            methods.setdefault(int(row["user_id"]), []).append({
                "hafta_kuni": int(row["hafta_kuni"]),
                "kun_nomi": _V1852_HAFTA.get(int(row["hafta_kuni"]), str(row["hafta_kuni"])),
                "qattiq": bool(row["qattiq"]),
                "izoh": row.get("izoh"),
            })
        for teacher in teachers:
            teacher["metod_kunlari"] = methods.get(int(teacher["user_id"]), [])
        return {
            "xodimlar": teachers,
            "jami": len(teachers),
            "fanli": sum(1 for row in teachers if row.get("fanlar_royxati")),
            "fansiz": sum(1 for row in teachers if not row.get("fanlar_royxati")),
            "izoh": "Fanlar XODIMLAR va DARS_BIRIKMALARI shablonlaridagi import ma'lumotlaridan birlashtirildi.",
        }
    finally:
        cur.close(); conn.close()


# ========================= V18.54 END =========================



# ═══════════════════════════════════════════════════════════
# V18.56 — MOSLASHUVCHAN SINF-KUN QOIDALARI
# Rahbariyat xohlagan parallel yoki aniq sinfga xohlagan hafta kunini bir tugma bilan bloklaydi.
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# V18.57 — MAKTAB BOSH SAHIFASI UCHUN XAVFSIZ READ API
# Bir qo'shimcha jadval buzilsa ham butun bosh sahifa yiqilmaydi.
# GET so'rovlari dublikat tozalash yoki migratsiya kabi yozuv amali bajarmaydi.
# ═══════════════════════════════════════════════════════════

def _v1857_table_exists(cur, table_name: str) -> bool:
    cur.execute("SELECT to_regclass(%s) AS table_name", (f"public.{table_name}",))
    return bool((cur.fetchone() or {}).get("table_name"))


def _v1857_columns(cur, table_name: str) -> set[str]:
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=%s",
        (table_name,),
    )
    return {str(row["column_name"]) for row in cur.fetchall()}


def _v1857_has_columns(cur, table_name: str, required: set[str]) -> bool:
    return _v1857_table_exists(cur, table_name) and required.issubset(_v1857_columns(cur, table_name))


def _v1857_normal_name(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


@app.get("/api/maktab/dashboard_xavfsiz")
def v1857_safe_school_dashboard(token: str, maktab_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    warnings = []
    try:
        if not _maktab_boshqaruvchi_mi(cur, user_id, maktab_id):
            raise HTTPException(status_code=403, detail="Faqat maktab rahbariyati yoki admin ko'ra oladi")

        maktab_cols = _v1857_columns(cur, "maktablar")
        payment_expr = "pulli" if "pulli" in maktab_cols else "FALSE AS pulli"
        fee_expr = "oylik_tolov" if "oylik_tolov" in maktab_cols else "NULL::INTEGER AS oylik_tolov"
        cur.execute(f"SELECT nomi,{payment_expr},{fee_expr} FROM maktablar WHERE id=%s", (maktab_id,))
        maktab = cur.fetchone()
        if not maktab:
            raise HTTPException(status_code=404, detail="Maktab topilmadi")

        sinf_cols = _v1857_columns(cur, "maktab_sinflari")
        psixolog_bor = "psixolog_user_id" in sinf_cols
        psixolog_select = "COALESCE(p.full_name,'') AS psixolog_ismi" if psixolog_bor else "''::TEXT AS psixolog_ismi"
        psixolog_join = "LEFT JOIN users p ON p.user_id=s.psixolog_user_id" if psixolog_bor else ""
        cur.execute(f"""
            SELECT s.id,s.sinf,s.harf,
                   COALESCE(u.full_name,'') AS rahbar_ismi,
                   {psixolog_select},
                   (SELECT COUNT(*) FROM maktab_sinf_azolari a WHERE a.sinf_id=s.id) AS oquvchi_soni
            FROM maktab_sinflari s
            LEFT JOIN users u ON u.user_id=s.rahbar_user_id
            {psixolog_join}
            WHERE s.maktab_id=%s
            ORDER BY NULLIF(REGEXP_REPLACE(COALESCE(s.sinf,''),'[^0-9]','','g'),'')::int NULLS LAST,
                     s.harf,s.id
        """, (maktab_id,))
        sinflar = cur.fetchall()
        class_map = {int(row["id"]): row for row in sinflar}

        for row in sinflar:
            row["tolagan_soni"] = 0
            row["bugun_kelgan_soni"] = 0
            row["bugun_belgilangan_soni"] = 0
            row["davomat_kun_7"] = 0
            row["ortacha_bilim"] = None

        # Davomat optional modul.
        if _v1857_has_columns(cur, "davomat", {"sinf_id", "user_id", "sana", "holat"}):
            cur.execute("""
                SELECT d.sinf_id,
                       COUNT(DISTINCT d.user_id) FILTER (WHERE d.holat='keldi') AS kelgan,
                       COUNT(DISTINCT d.user_id) AS belgilangan,
                       COUNT(DISTINCT d.sana) FILTER (WHERE d.sana>=CURRENT_DATE-INTERVAL '7 days') AS kun_7
                FROM davomat d
                JOIN maktab_sinflari s ON s.id=d.sinf_id
                WHERE s.maktab_id=%s AND (d.sana=CURRENT_DATE OR d.sana>=CURRENT_DATE-INTERVAL '7 days')
                GROUP BY d.sinf_id
            """, (maktab_id,))
            for item in cur.fetchall():
                row = class_map.get(int(item["sinf_id"]))
                if row:
                    row["bugun_kelgan_soni"] = int(item.get("kelgan") or 0)
                    row["bugun_belgilangan_soni"] = int(item.get("belgilangan") or 0)
                    row["davomat_kun_7"] = int(item.get("kun_7") or 0)
        else:
            warnings.append("Davomat jadvali hali tayyor emas; davomat ko'rsatkichlari vaqtincha 0 ko'rsatildi.")

        # To'lov faqat pulli maktabda va kerakli ustunlar mavjud bo'lsa hisoblanadi.
        if bool(maktab.get("pulli")):
            required = {"user_id", "maktab_id", "oy", "tolangan_summa"}
            if _v1857_has_columns(cur, "tolovlar", required):
                current_month = datetime.now().strftime("%Y-%m")
                required_sum = int(maktab.get("oylik_tolov") or 0)
                cur.execute("""
                    SELECT a.sinf_id,COUNT(DISTINCT t.user_id) AS tolagan
                    FROM maktab_sinf_azolari a
                    JOIN maktab_sinflari s ON s.id=a.sinf_id
                    JOIN tolovlar t ON t.user_id=a.user_id AND t.maktab_id=s.maktab_id
                    WHERE s.maktab_id=%s AND t.oy=%s AND t.tolangan_summa>=%s
                    GROUP BY a.sinf_id
                """, (maktab_id, current_month, required_sum))
                for item in cur.fetchall():
                    row = class_map.get(int(item["sinf_id"]))
                    if row:
                        row["tolagan_soni"] = int(item.get("tolagan") or 0)
            else:
                warnings.append("To'lov moduli eski sxemada; bosh sahifa to'lovsiz xavfsiz yuklandi.")

        # Bilim ko'rsatkichi optional.
        if _v1857_has_columns(cur, "learned_topics", {"user_id", "score"}):
            cur.execute("""
                SELECT a.sinf_id,ROUND(AVG(lt.score)) AS ortacha_bilim
                FROM maktab_sinf_azolari a
                JOIN maktab_sinflari s ON s.id=a.sinf_id
                LEFT JOIN learned_topics lt ON lt.user_id=a.user_id
                WHERE s.maktab_id=%s
                GROUP BY a.sinf_id
            """, (maktab_id,))
            for item in cur.fetchall():
                row = class_map.get(int(item["sinf_id"]))
                if row:
                    row["ortacha_bilim"] = item.get("ortacha_bilim")
        else:
            warnings.append("Bilim analitikasi jadvali topilmadi; sinf reytingi vaqtincha yashirildi.")

        muammoli_oquvchilar = []
        if _v1857_has_columns(cur, "davomat", {"sinf_id", "user_id", "sana", "holat"}):
            cur.execute("""
                SELECT u.user_id,u.full_name,s.sinf,s.harf,
                       COUNT(*) FILTER (WHERE d.holat='kelmadi') AS songi_hafta_kelmagan
                FROM maktab_sinf_azolari a
                JOIN users u ON u.user_id=a.user_id
                JOIN maktab_sinflari s ON s.id=a.sinf_id
                LEFT JOIN davomat d ON d.user_id=a.user_id AND d.sinf_id=a.sinf_id
                                    AND d.sana>=CURRENT_DATE-INTERVAL '7 days'
                WHERE s.maktab_id=%s
                GROUP BY u.user_id,u.full_name,s.sinf,s.harf
                HAVING COUNT(*) FILTER (WHERE d.holat='kelmadi')>=2
                ORDER BY songi_hafta_kelmagan DESC LIMIT 20
            """, (maktab_id,))
            muammoli_oquvchilar = cur.fetchall()

        xodim_bugun = {"jami": 0, "keldi": 0}
        cur.execute("SELECT COUNT(*) AS jami FROM users WHERE maktab_id=%s AND lavozim IS NOT NULL", (maktab_id,))
        xodim_bugun["jami"] = int((cur.fetchone() or {}).get("jami") or 0)
        if _v1857_has_columns(cur, "xodim_davomati", {"maktab_id", "user_id", "sana", "holat"}):
            cur.execute("""
                SELECT COUNT(DISTINCT user_id) AS keldi FROM xodim_davomati
                WHERE maktab_id=%s AND sana=CURRENT_DATE AND holat='keldi'
            """, (maktab_id,))
            xodim_bugun["keldi"] = int((cur.fetchone() or {}).get("keldi") or 0)

        jami_oquvchi = sum(int(row.get("oquvchi_soni") or 0) for row in sinflar)
        jami_tolagan = sum(int(row.get("tolagan_soni") or 0) for row in sinflar)
        jami_kelgan = sum(int(row.get("bugun_kelgan_soni") or 0) for row in sinflar)
        jami_belgilangan = sum(int(row.get("bugun_belgilangan_soni") or 0) for row in sinflar)
        sinflar_belgilamagan = sum(
            1 for row in sinflar
            if int(row.get("oquvchi_soni") or 0)>0 and int(row.get("bugun_belgilangan_soni") or 0)==0
        )
        rated = [row for row in sinflar if row.get("ortacha_bilim") is not None]
        rated.sort(key=lambda row: float(row.get("ortacha_bilim") or 0), reverse=True)

        return {
            "maktab_nomi": maktab["nomi"],
            "pulli": bool(maktab.get("pulli")),
            "oylik_tolov": maktab.get("oylik_tolov"),
            "sinflar": sinflar,
            "tolov_xulosasi": ({
                "jami_oquvchi": jami_oquvchi,
                "tolagan": jami_tolagan,
                "qarzdor": max(0, jami_oquvchi-jami_tolagan),
            } if bool(maktab.get("pulli")) else None),
            "bugungi_davomat": {
                "jami_oquvchi": jami_oquvchi,
                "kelgan": jami_kelgan,
                "belgilangan": jami_belgilangan,
                "sinflar_belgilamagan": sinflar_belgilamagan,
            },
            "xodim_bugun": xodim_bugun,
            "muammoli_oquvchilar": muammoli_oquvchilar,
            "eng_yaxshi_sinf": rated[0] if rated else None,
            "etibor_kerak_sinf": rated[-1] if len(rated)>1 else None,
            "diagnostika_ogohlantirishlari": warnings,
        }
    finally:
        cur.close(); conn.close()


@app.get("/api/maktab/yuklama_xulosasi_xavfsiz")
def v1857_safe_workload(token: str, maktab_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    warnings = []
    try:
        if not _maktab_boshqaruvchi_mi(cur, actor_id, maktab_id):
            raise HTTPException(status_code=403, detail="Faqat maktab rahbariyati yoki admin ko'ra oladi")

        user_cols = _v1857_columns(cur, "users")
        load_expr = "haftalik_dars_soati" if "haftalik_dars_soati" in user_cols else "NULL::INTEGER AS haftalik_dars_soati"
        cur.execute(f"""
            SELECT user_id,full_name,lavozim,fanlari,{load_expr}
            FROM users WHERE maktab_id=%s AND lavozim IS NOT NULL ORDER BY full_name,user_id
        """, (maktab_id,))
        people = cur.fetchall()
        ids = [int(row["user_id"]) for row in people]
        counts = {uid: 0 for uid in ids}
        assigned_counts = {uid: 0 for uid in ids}
        if _v1857_has_columns(
            cur, "maktab_dars_birikmalari", {"maktab_id", "user_id", "haftalik_soat"}
        ):
            cur.execute("""SELECT user_id,COALESCE(SUM(haftalik_soat),0) AS soat
                           FROM maktab_dars_birikmalari
                           WHERE maktab_id=%s GROUP BY user_id""", (maktab_id,))
            for assignment in cur.fetchall():
                uid = int(assignment["user_id"])
                if uid in assigned_counts:
                    assigned_counts[uid] = float(assignment.get("soat") or 0)
        psixolog_class_counts = {}
        class_hour_counts = {}
        if _v1857_has_columns(cur, "aqlli_sinf_soati_qoidalari_v2", {"maktab_id", "sinf_id", "faol"}) and            _v1857_has_columns(cur, "maktab_sinflari", {"id", "rahbar_user_id"}):
            cur.execute("""SELECT s.rahbar_user_id AS user_id,COUNT(*) AS son
                           FROM aqlli_sinf_soati_qoidalari_v2 q
                           JOIN maktab_sinflari s ON s.id=q.sinf_id
                           WHERE q.maktab_id=%s AND q.faol=TRUE AND s.rahbar_user_id IS NOT NULL
                           GROUP BY s.rahbar_user_id""", (maktab_id,))
            class_hour_counts = {
                int(row["user_id"]): int(row.get("son") or 0) for row in cur.fetchall()
            }
        if "psixolog_user_id" in _v1857_columns(cur, "maktab_sinflari"):
            cur.execute("""
                SELECT psixolog_user_id AS user_id,COUNT(*) AS son
                FROM maktab_sinflari
                WHERE maktab_id=%s AND psixolog_user_id IS NOT NULL
                GROUP BY psixolog_user_id
            """, (maktab_id,))
            psixolog_class_counts = {
                int(row["user_id"]): int(row.get("son") or 0) for row in cur.fetchall()
            }

        smart_ok = _v1857_has_columns(
            cur, "aqlli_jadval_urinishlari_v2", {"id", "maktab_id", "holat"}
        ) and _v1857_has_columns(
            cur, "aqlli_jadval_slotlari_v2", {"urinish_id", "oqituvchi_user_id"}
        )
        active_run_id = None
        if smart_ok:
            cur.execute("""SELECT id FROM aqlli_jadval_urinishlari_v2
                           WHERE maktab_id=%s AND holat='tasdiqlangan'
                           ORDER BY id DESC LIMIT 1""", (maktab_id,))
            active = cur.fetchone(); active_run_id = active["id"] if active else None
        if active_run_id:
            cur.execute("""SELECT oqituvchi_user_id,COUNT(*) AS son
                           FROM aqlli_jadval_slotlari_v2
                           WHERE urinish_id=%s AND oqituvchi_user_id IS NOT NULL
                           GROUP BY oqituvchi_user_id""", (active_run_id,))
            for row in cur.fetchall():
                counts[int(row["oqituvchi_user_id"])] = int(row.get("son") or 0)
        elif _v1857_has_columns(cur, "dars_jadvali", {"id", "oqituvchi_user_id"}):
            cur.execute("""SELECT oqituvchi_user_id,COUNT(id) AS son FROM dars_jadvali
                           WHERE oqituvchi_user_id IS NOT NULL GROUP BY oqituvchi_user_id""")
            for row in cur.fetchall():
                uid = int(row["oqituvchi_user_id"])
                if uid in counts:
                    counts[uid] = int(row.get("son") or 0)
        else:
            warnings.append("Jadval jadvali topilmadi; amaldagi yuklama 0 deb ko'rsatildi.")

        # Import dublikatlari ekranda qayta takrorlanmasin; bu READ-ONLY birlashtirish.
        grouped = {}
        for person in people:
            uid = int(person["user_id"])
            if uid < 0:
                key = ("import", _v1857_normal_name(person.get("full_name")), str(person.get("lavozim") or ""))
            else:
                key = ("user", uid)
            current = grouped.get(key)
            if current is None:
                current = dict(person)
                current["birlashtirilgan_idlar"] = []
                current["jadvaldagi_soat"] = 0
                current["biriktirilgan_soat"] = 0
                current["psixolog_sinf_soni"] = 0
                current["sinf_soati_soni"] = 0
                grouped[key] = current
            current["birlashtirilgan_idlar"].append(uid)
            current["jadvaldagi_soat"] += int(counts.get(uid, 0))
            current["biriktirilgan_soat"] += float(assigned_counts.get(uid, 0))
            current["psixolog_sinf_soni"] += int(psixolog_class_counts.get(uid, 0))
            current["sinf_soati_soni"] += int(class_hour_counts.get(uid, 0))
            if current.get("haftalik_dars_soati") is None and person.get("haftalik_dars_soati") is not None:
                current["haftalik_dars_soati"] = person.get("haftalik_dars_soati")
            if not current.get("fanlari") and person.get("fanlari"):
                current["fanlari"] = person.get("fanlari")
            if uid < int(current.get("user_id") or uid):
                current["user_id"] = uid

        result = list(grouped.values())
        result.sort(key=lambda row: _v1857_normal_name(row.get("full_name")))
        for row in result:
            base_plan = row.get("haftalik_dars_soati")
            extra = int(row.get("sinf_soati_soni") or 0)
            plan = (
                round(float(base_plan) + extra, 1)
                if base_plan is not None else (extra or None)
            )
            row["haftalik_reja_jami"] = plan
            actual = float(
                row.get("jadvaldagi_soat") if active_run_id
                else row.get("biriktirilgan_soat") or 0
            )
            actual = round(actual, 1)
            row["amaldagi_soat"] = actual
            row["hisob_manbasi"] = "tasdiqlangan_jadval" if active_run_id else "oqituvchi_yuklamasi"
            difference = None if plan is None else round(float(plan) - actual, 1)
            row["farq"] = difference
            row["holat"] = (
                "kiritilmagan" if plan is None else
                "ortiqcha" if difference < -1e-9 else
                "toliq" if abs(difference) <= 1e-9 else "yetishmaydi"
            )
        return {"xodimlar": result, "diagnostika_ogohlantirishlari": warnings}
    finally:
        cur.close(); conn.close()


@app.get("/api/maktab/aqlli_holatlar_xavfsiz")
def v1857_safe_smart_cases(token: str, maktab_id: int, holat: str = "ochiq"):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        if not _maktab_boshqaruvchi_mi(cur, actor_id, maktab_id):
            raise HTTPException(status_code=403, detail="Faqat maktab rahbariyati yoki admin ko'ra oladi")
        required = {"id", "maktab_id", "oquvchi_user_id", "daraja", "sarlavha", "holat", "yangilangan_at"}
        if not _v1857_has_columns(cur, "aqlli_holatlar", required):
            return {"holatlar": [], "diagnostika_ogohlantirishlari": ["Aqlli holatlar moduli hali tayyor emas."]}
        cur.execute("""
            SELECT h.*,COALESCE(u.full_name,'Noma''lum o''quvchi') AS full_name
            FROM aqlli_holatlar h LEFT JOIN users u ON u.user_id=h.oquvchi_user_id
            WHERE h.maktab_id=%s AND h.holat=%s
            ORDER BY h.daraja DESC,h.yangilangan_at DESC LIMIT 100
        """, (maktab_id, holat))
        return {"holatlar": cur.fetchall(), "diagnostika_ogohlantirishlari": []}
    finally:
        cur.close(); conn.close()

# ========================= V18.57 END =========================

# ========================= V18.60 END =========================

# ═══════════════════════════════════════════════════════════
# V18.66 — METOD KUNINI OMMAVIY TOZALASH + QAT'IY SINF SOATI
# ═══════════════════════════════════════════════════════════

class V1866MethodDayClear(BaseModel):
    maktab_id: int
    user_ids: list[int]
    hafta_kuni: Optional[int] = None


@app.post("/api/maktab/aqlli_jadval/v2/metod_kunlarini_tozalash")
def v1866_method_days_clear(sorov: V1866MethodDayClear, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Metod kunlarini faqat maktab rahbariyati ommaviy tozalaydi")
        ids = list(dict.fromkeys(int(x) for x in sorov.user_ids if int(x)))
        if not ids:
            raise HTTPException(status_code=400, detail="Kamida bitta o‘qituvchini tanlang")
        if sorov.hafta_kuni is not None and int(sorov.hafta_kuni) not in range(1, 7):
            raise HTTPException(status_code=400, detail="Hafta kuni Dushanba–Shanba oralig‘ida bo‘lishi kerak")
        cur.execute("SELECT user_id FROM users WHERE maktab_id=%s AND user_id=ANY(%s)", (sorov.maktab_id, ids))
        found = {int(row["user_id"]) for row in cur.fetchall()}
        missing = [uid for uid in ids if uid not in found]
        if missing:
            raise HTTPException(status_code=400, detail=f"Maktabda topilmagan xodim IDlari: {missing[:10]}")
        where = ["maktab_id=%s", "user_id=ANY(%s)", "turi='metod_kuni'"]
        args = [sorov.maktab_id, ids]
        if sorov.hafta_kuni is not None:
            where.append("hafta_kuni=%s")
            args.append(int(sorov.hafta_kuni))
        cur.execute("DELETE FROM aqlli_oqituvchi_vaqti_v2 WHERE " + " AND ".join(where), tuple(args))
        deleted = int(cur.rowcount or 0)
        conn.commit()
        return {
            "holat": "tozalandi", "o'qituvchi_soni": len(ids),
            "o'chirilgan_metod_kuni": deleted, "hafta_kuni": sorov.hafta_kuni,
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V1866ClassHourBulk(BaseModel):
    maktab_id: int
    qamrov: str = "parallel"  # parallel | aniq
    sinf_darajalari: list[int] = []
    sinf_idlar: list[int] = []
    hafta_kuni: int
    dars_raqami: int
    fan_nomi: str = "KELAJAK SOATI"
    haftalik_soat: int = 1


def _v1866_class_hour_rule_rows(cur, maktab_id: int):
    cur.execute("""SELECT q.*,s.sinf,s.harf,COALESCE(s.smena,1) AS smena,
                          s.rahbar_user_id,COALESCE(u.full_name,'') AS rahbar_ismi
                   FROM aqlli_sinf_soati_qoidalari_v2 q
                   JOIN maktab_sinflari s ON s.id=q.sinf_id
                   LEFT JOIN users u ON u.user_id=s.rahbar_user_id
                   WHERE q.maktab_id=%s AND q.faol=TRUE
                   ORDER BY s.sinf::int,s.harf""", (maktab_id,))
    return cur.fetchall()


def _v199_ensure_class_hour_rules(cur, maktab_id: int, class_ids=None, actor_id=None):
    """Har sinf uchun yagona, takrorlanmaydigan SINF SOATI qoidasini yaratadi.

    Sinf soati fan yuklamasiga yozilmaydi: jadval generatorida u alohida bitta
    sessiya sifatida hisoblanadi. Shu sabab o'quv reja jami ham, o'qituvchi
    yuklamasi ham bir soatga oshadi, lekin fan soatlari ikki marta sanalmaydi.
    Mavjud qo'lda sozlangan kun/dars o'zgartirilmaydi.
    """
    _v1852_tables(cur)
    year = _v1852_active_year(cur, maktab_id)
    weekdays = max(1, min(6, int((year or {}).get("hafta_kunlari") or 6)))
    default_day = min(5, weekdays)  # odatda Juma
    args = [int(maktab_id)]
    where = ["maktab_id=%s"]
    if class_ids is not None:
        ids = sorted({int(value) for value in class_ids if value is not None})
        if not ids:
            return {"yaratildi": 0, "jami": 0, "hafta_kuni": default_day, "dars_raqami": 1}
        where.append("id=ANY(%s)")
        args.append(ids)
    cur.execute(
        "SELECT id FROM maktab_sinflari WHERE " + " AND ".join(where) + " ORDER BY id",
        tuple(args),
    )
    target_ids = [int(row["id"]) for row in cur.fetchall()]
    created = 0
    for class_id in target_ids:
        cur.execute(
            """INSERT INTO aqlli_sinf_soati_qoidalari_v2(
                   maktab_id,sinf_id,hafta_kuni,dars_raqami,faol,
                   yaratgan_user_id,yangilangan_at)
               VALUES(%s,%s,%s,1,TRUE,%s,NOW())
               ON CONFLICT(maktab_id,sinf_id) DO UPDATE SET
                 yangilangan_at=NOW()""",
            (maktab_id, class_id, default_day, actor_id),
        )
        created += int(cur.rowcount or 0)
    return {
        "yaratildi": created,
        "jami": len(target_ids),
        "hafta_kuni": default_day,
        "dars_raqami": 1,
    }


def _v1866_target_classes(cur, sorov: V1866ClassHourBulk):
    qamrov = str(sorov.qamrov or "parallel").strip().lower()
    if qamrov == "parallel":
        grades = sorted(set(int(x) for x in sorov.sinf_darajalari))
        if not grades or any(g not in range(1, 12) for g in grades):
            raise HTTPException(status_code=400, detail="Kamida bitta 1–11-sinf parallelini tanlang")
        cur.execute("""SELECT s.id,s.sinf,s.harf,COALESCE(s.smena,1) AS smena,s.rahbar_user_id,
                              COALESCE(u.full_name,'') AS rahbar_ismi
                       FROM maktab_sinflari s LEFT JOIN users u ON u.user_id=s.rahbar_user_id
                       WHERE s.maktab_id=%s
                         AND NULLIF(REGEXP_REPLACE(COALESCE(s.sinf,''),'[^0-9]','','g'),'')::int=ANY(%s)
                       ORDER BY s.sinf::int,s.harf""", (sorov.maktab_id, grades))
    elif qamrov == "aniq":
        ids = sorted(set(int(x) for x in sorov.sinf_idlar if int(x)))
        if not ids:
            raise HTTPException(status_code=400, detail="Kamida bitta aniq sinfni tanlang")
        cur.execute("""SELECT s.id,s.sinf,s.harf,COALESCE(s.smena,1) AS smena,s.rahbar_user_id,
                              COALESCE(u.full_name,'') AS rahbar_ismi
                       FROM maktab_sinflari s LEFT JOIN users u ON u.user_id=s.rahbar_user_id
                       WHERE s.maktab_id=%s AND s.id=ANY(%s)
                       ORDER BY s.sinf::int,s.harf""", (sorov.maktab_id, ids))
    else:
        raise HTTPException(status_code=400, detail="Qamrov parallel yoki aniq bo‘lishi kerak")
    rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Tanlangan sinflar topilmadi")
    return rows


@app.put("/api/maktab/aqlli_jadval/v2/sinf_soati_bulk")
def v1866_class_hour_bulk_save(sorov: V1866ClassHourBulk, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Sinf soatini faqat maktab rahbariyati belgilaydi")
        year = _v1852_active_year(cur, sorov.maktab_id)
        weekdays = int((year or {}).get("hafta_kunlari") or 6)
        if int(sorov.hafta_kuni) not in range(1, weekdays + 1):
            raise HTTPException(status_code=400, detail=f"O‘qish haftasi {weekdays} kun. Mos hafta kunini tanlang")
        if int(sorov.dars_raqami) not in range(1, 13):
            raise HTTPException(status_code=400, detail="Dars raqami 1–12 oralig‘ida bo‘lishi kerak")
        fan_nomi = _v192_clean_subject(sorov.fan_nomi) or "KELAJAK SOATI"
        haftalik_soat = int(sorov.haftalik_soat)
        if haftalik_soat not in range(1, 6):
            raise HTTPException(status_code=400, detail="Kelajak soati haftasiga 1–5 soat bo‘lishi mumkin")
        classes = _v1866_target_classes(cur, sorov)
        cur.execute("SELECT smena,dars_soni FROM aqlli_smena_sozlamalari_v2 WHERE maktab_id=%s", (sorov.maktab_id,))
        shift_limits = {int(row["smena"]): int(row.get("dars_soni") or 0) for row in cur.fetchall()}
        class_day_map = _v1856_class_day_rule_map(_v1856_class_day_rule_rows(cur, sorov.maktab_id))
        target_ids = {int(row["id"]) for row in classes}
        cur.execute("""SELECT q.sinf_id,q.hafta_kuni,q.dars_raqami,COALESCE(s.smena,1) AS smena,s.rahbar_user_id
                       FROM aqlli_sinf_soati_qoidalari_v2 q
                       JOIN maktab_sinflari s ON s.id=q.sinf_id
                       WHERE q.maktab_id=%s AND q.faol=TRUE""", (sorov.maktab_id,))
        occupied = {}
        for row in cur.fetchall():
            if int(row["sinf_id"]) in target_ids or row.get("rahbar_user_id") is None:
                continue
            key = (int(row["rahbar_user_id"]), int(row["hafta_kuni"]), int(row["smena"]), int(row["dars_raqami"]))
            occupied[key] = int(row["sinf_id"])
        saved = 0
        skipped = []
        for cls in classes:
            label = f"{cls['sinf']}-{cls['harf']}"
            leader = cls.get("rahbar_user_id")
            shift = int(cls.get("smena") or 1)
            if leader is None:
                skipped.append({"sinf": label, "sabab": "sinf rahbari belgilanmagan"})
                continue
            if int(sorov.dars_raqami) > int(shift_limits.get(shift) or 0):
                skipped.append({"sinf": label, "sabab": f"{shift}-smenada {sorov.dars_raqami}-dars mavjud emas"})
                continue
            blocked = _v1856_class_day_block_reason(cls, int(sorov.hafta_kuni), class_day_map)
            if blocked:
                skipped.append({"sinf": label, "sabab": blocked})
                continue
            key = (int(leader), int(sorov.hafta_kuni), shift, int(sorov.dars_raqami))
            if key in occupied:
                skipped.append({"sinf": label, "sabab": "sinf rahbari shu vaqtda boshqa sinf soatiga biriktirilgan"})
                continue
            occupied[key] = int(cls["id"])
            cur.execute("""INSERT INTO aqlli_sinf_soati_qoidalari_v2(
                            maktab_id,sinf_id,hafta_kuni,dars_raqami,faol,yaratgan_user_id,
                            fan_nomi,haftalik_soat,yangilangan_at)
                           VALUES(%s,%s,%s,%s,TRUE,%s,%s,%s,NOW())
                           ON CONFLICT(maktab_id,sinf_id) DO UPDATE SET
                             hafta_kuni=EXCLUDED.hafta_kuni,dars_raqami=EXCLUDED.dars_raqami,
                             faol=TRUE,yaratgan_user_id=EXCLUDED.yaratgan_user_id,
                             fan_nomi=EXCLUDED.fan_nomi,haftalik_soat=EXCLUDED.haftalik_soat,
                             yangilangan_at=NOW()""",
                        (sorov.maktab_id, cls["id"], sorov.hafta_kuni, sorov.dars_raqami,
                         actor_id, fan_nomi, haftalik_soat))
            saved += 1
        if saved == 0:
            detail = "; ".join(f"{row['sinf']}: {row['sabab']}" for row in skipped[:8]) or "mos sinf topilmadi"
            raise HTTPException(status_code=400, detail=f"Sinf soati saqlanmadi — {detail}")
        conn.commit()
        return {"holat": "saqlandi", "saqlandi": saved, "otkazib_yuborildi": skipped}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.delete("/api/maktab/aqlli_jadval/v2/sinf_soati")
def v1866_class_hour_delete(token: str, maktab_id: int, sinf_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        if not _v1852_manager(cur, actor_id, maktab_id):
            raise HTTPException(status_code=403, detail="Sinf soatini faqat maktab rahbariyati o‘chiradi")
        cur.execute("DELETE FROM aqlli_sinf_soati_qoidalari_v2 WHERE maktab_id=%s AND sinf_id=%s", (maktab_id, sinf_id))
        deleted = int(cur.rowcount or 0)
        conn.commit()
        return {"holat": "o‘chirildi", "o‘chirildi": deleted}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def _v1866_build_class_hour_jobs(classes, rules):
    jobs = []
    warnings = []
    for row in rules:
        class_id = int(row["sinf_id"])
        cls = classes.get(class_id)
        if not cls:
            continue
        leader = cls.get("rahbar_user_id")
        if leader is None:
            warnings.append(f"{cls['sinf']}-{cls['harf']} sinf soati: sinf rahbari belgilanmagan")
            # Rahbar keyin tayinlanishi mumkin. Hozir o‘qituvchisiz KELAJAK
            # SOATI jobi yasab butun fan jadvalini bloklamaymiz.
            continue
        weekly = max(1, min(5, int(row.get("haftalik_soat") or 1)))
        for occurrence in range(1, weekly + 1):
            jobs.append({
                "job_id": f"sinf-soati:{class_id}:{occurrence}", "load_id": None,
                "sinf_id": class_id, "fan": "SINF SOATI", "occurrence": occurrence,
                "smena": int(cls.get("smena") or 1), "daily_max": 1,
                "consecutive_allowed": False, "preferred_last": int(row["dars_raqami"]),
                "weight": 1, "room_id": None, "groups": [],
                "teacher_options": [int(leader)] if leader is not None else [],
                "difficulty": 100000 - occurrence,
                "fixed_day": int(row["hafta_kuni"]) if occurrence == 1 else None,
                "fixed_period": int(row["dars_raqami"]) if occurrence == 1 else None,
                "is_class_hour": True,
            })
    return jobs, warnings


def _v1866_class_hour_violations(cur, maktab_id: int, run_id: int):
    rules = _v1866_class_hour_rule_rows(cur, maktab_id)
    errors = []
    for row in rules:
        if row.get("rahbar_user_id") is None:
            # Vaqtinchalik holat: rahbar tayinlangach keyingi draftda qo‘shiladi.
            continue
        cur.execute("""SELECT 1 FROM aqlli_jadval_slotlari_v2
                       WHERE urinish_id=%s AND sinf_id=%s AND hafta_kuni=%s AND smena=%s
                         AND dars_raqami=%s AND UPPER(TRIM(fan_nomi))='SINF SOATI'
                         AND oqituvchi_user_id=%s LIMIT 1""",
                    (run_id, row["sinf_id"], row["hafta_kuni"], row["smena"],
                     row["dars_raqami"], row["rahbar_user_id"]))
        if not cur.fetchone():
            errors.append({
                "sinf_id": row["sinf_id"],
                "izoh": f"{row['sinf']}-{row['harf']} · {_V1852_HAFTA.get(int(row['hafta_kuni']), row['hafta_kuni'])} · {row['dars_raqami']}-dars",
            })
    return errors

# ========================= V18.66 END =========================



# ═══════════════════════════════════════════════════════════
# V18.68 — O'QITUVCHI VAQT MATRITSASI
# ═══════════════════════════════════════════════════════════

class V1868TeacherMatrixItem(BaseModel):
    user_id: int
    qoidalar: Optional[V1852TeacherRules] = None
    vaqtlar: list[dict] = []


class V1868TeacherMatrixSave(BaseModel):
    maktab_id: int
    oqituvchilar: list[V1868TeacherMatrixItem]


@app.put("/api/maktab/aqlli_jadval/v2/oqituvchi_vaqt_matritsasi")
def v1868_teacher_time_matrix_save(sorov: V1868TeacherMatrixSave, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        items_by_user = {}
        for item in sorov.oqituvchilar:
            uid = int(item.user_id)
            if uid:
                items_by_user[uid] = item
        if not items_by_user:
            raise HTTPException(status_code=400, detail="Saqlash uchun o'qituvchi tanlanmagan")
        if len(items_by_user) > 300:
            raise HTTPException(status_code=400, detail="Bir so'rovda 300 tadan ortiq xodim saqlanmaydi")

        manager = _v1852_manager(cur, actor_id, sorov.maktab_id)
        if not manager and (len(items_by_user) != 1 or actor_id not in items_by_user):
            raise HTTPException(
                status_code=403,
                detail="O'qituvchi faqat o'z vaqtini, rahbariyat esa barcha o'qituvchilarni o'zgartira oladi",
            )

        user_ids = list(items_by_user)
        cur.execute(
            "SELECT user_id FROM users WHERE maktab_id=%s AND user_id=ANY(%s)",
            (sorov.maktab_id, user_ids),
        )
        found = {int(row["user_id"]) for row in cur.fetchall()}
        missing = [uid for uid in user_ids if uid not in found]
        if missing:
            raise HTTPException(status_code=400, detail=f"Maktabda topilmagan xodimlar: {missing[:10]}")

        inserted_count = 0
        for uid, item in items_by_user.items():
            if item.qoidalar is not None:
                rules = item.qoidalar
                if rules.eng_kech_dars < rules.eng_erta_dars:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{uid}: eng kech dars eng erta darsdan oldin bo'lmaydi",
                    )
                cur.execute(
                    """INSERT INTO aqlli_oqituvchi_qoidalari_v2(
                        maktab_id,user_id,kunlik_max,ketma_ket_max,okno_max,
                        afzal_smena,eng_erta_dars,eng_kech_dars)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT(maktab_id,user_id) DO UPDATE SET
                         kunlik_max=EXCLUDED.kunlik_max,
                         ketma_ket_max=EXCLUDED.ketma_ket_max,
                         okno_max=EXCLUDED.okno_max,
                         afzal_smena=EXCLUDED.afzal_smena,
                         eng_erta_dars=EXCLUDED.eng_erta_dars,
                         eng_kech_dars=EXCLUDED.eng_kech_dars""",
                    (
                        sorov.maktab_id, uid, rules.kunlik_max, rules.ketma_ket_max,
                        rules.okno_max, rules.afzal_smena, rules.eng_erta_dars,
                        rules.eng_kech_dars,
                    ),
                )

            validated = _v1854_validate_time_items(item.vaqtlar)
            unique_rows = {}
            for day, row_shift, period, kind, hard, note in validated:
                unique_rows[(day, row_shift, period, kind)] = (
                    day, row_shift, period, kind, hard, note
                )

            cur.execute(
                "DELETE FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s AND user_id=%s",
                (sorov.maktab_id, uid),
            )
            rows = [
                (sorov.maktab_id, uid, day, row_shift, period, kind, hard, note)
                for day, row_shift, period, kind, hard, note in unique_rows.values()
            ]
            if rows:
                psycopg2.extras.execute_values(
                    cur,
                    """INSERT INTO aqlli_oqituvchi_vaqti_v2(
                        maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi,qattiq,izoh)
                       VALUES %s""",
                    rows,
                )
                inserted_count += len(rows)

        conn.commit()
        return {
            "holat": "saqlandi",
            "oqituvchi_soni": len(items_by_user),
            "vaqt_soni": inserted_count,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()

# ========================= V18.68 END =========================

# ═══════════════════════════════════════════════════════════
# V18.71 — AVTO METOD KUNI FAQAT ADMIN YOQQANDA ISHLAYDI
# Maktab fan → kun qoidalarini bir marta saqlaydi. Avto O'CHIQ bo'lsa
# tizim o'zi hech qanday metod kuni topmaydi va eski avto belgilarni olib tashlaydi.
# ═══════════════════════════════════════════════════════════

_V1871_AUTO_METHOD_PREFIX = "V18.71 AUTO METOD:"
_V1871_OLD_AUTO_PREFIX = "V18.54 taxminiy kasbiy rivojlanish kuni"


def _v1871_method_subject_key(value):
    text = str(value or "").casefold()
    for old in ("‘", "’", "`", "ʼ", "ʻ"):
        text = text.replace(old, "'")
    return " ".join(text.split())


def _v1871_auto_method_tables(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_metod_avto_sozlamalari_v2(
        maktab_id INTEGER PRIMARY KEY REFERENCES maktablar(id) ON DELETE CASCADE,
        yoqilgan BOOLEAN NOT NULL DEFAULT FALSE,
        yangilagan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_metod_fan_qoidalari_v2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        fan_nomi TEXT NOT NULL,
        fan_kaliti TEXT NOT NULL,
        hafta_kuni INTEGER NOT NULL CHECK(hafta_kuni BETWEEN 1 AND 7),
        qattiq BOOLEAN NOT NULL DEFAULT TRUE,
        tartib INTEGER NOT NULL DEFAULT 0,
        UNIQUE(maktab_id, fan_kaliti)
    )""")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_metod_fan_qoidalari_v2 "
        "ON aqlli_metod_fan_qoidalari_v2(maktab_id,tartib,id)"
    )


def _v1871_auto_method_where():
    return "(COALESCE(izoh,'') LIKE %s OR COALESCE(izoh,'') LIKE %s)"


def _v1871_method_rules(cur, maktab_id: int):
    cur.execute(
        """SELECT id,fan_nomi,fan_kaliti,hafta_kuni,qattiq,tartib
           FROM aqlli_metod_fan_qoidalari_v2
           WHERE maktab_id=%s ORDER BY tartib,id""",
        (maktab_id,),
    )
    return cur.fetchall()


def _v1871_method_report(cur, maktab_id: int, rules=None):
    rules = list(rules if rules is not None else _v1871_method_rules(cur, maktab_id))
    teachers = [
        row for row in _v1859_effective_teachers(cur, maktab_id)
        if row.get("dars_beruvchi")
    ]
    result = []
    for rule in rules:
        matched = []
        for teacher in teachers:
            subjects = teacher.get("fanlar_royxati") or []
            if any(
                _v1871_method_subject_key(subject) == rule["fan_kaliti"]
                for subject in subjects
            ):
                matched.append({
                    "user_id": int(teacher["user_id"]),
                    "full_name": teacher["full_name"],
                })
        result.append({
            "id": rule.get("id"),
            "fan_nomi": rule["fan_nomi"],
            "hafta_kuni": int(rule["hafta_kuni"]),
            "kun_nomi": _V1852_HAFTA.get(
                int(rule["hafta_kuni"]), str(rule["hafta_kuni"])
            ),
            "qattiq": bool(rule["qattiq"]),
            "oqituvchi_soni": len(matched),
            "oqituvchilar": matched[:50],
        })
    return result


class V1871AutoMethodRule(BaseModel):
    fan_nomi: str
    hafta_kuni: int
    qattiq: bool = True


class V1871AutoMethodSettings(BaseModel):
    maktab_id: int
    yoqilgan: bool = False
    qoidalar: list[V1871AutoMethodRule] = []


@app.on_event("startup")
def _v1871_startup_disable_old_auto_methods():
    """Eski V18.54 taxminiy avtomatik metod kunlarini bir marta tozalaydi.

    Qo'lda belgilangan metod kunlariga tegmaydi. V18.71 dagi yangi avto
    qoidalar faqat administrator YOQ qilgandan keyin yaratiladi.
    """
    try:
        conn = _db()
        cur = conn.cursor()
        _v1871_auto_method_tables(cur)
        cur.execute(
            """DELETE FROM aqlli_oqituvchi_vaqti_v2
               WHERE turi='metod_kuni' AND COALESCE(izoh,'') LIKE %s""",
            (_V1871_OLD_AUTO_PREFIX + "%",),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as exc:
        print(f"[V18.71 eski avto metod tozalash] {exc}")


@app.get("/api/maktab/aqlli_jadval/v2/metod_avto_sozlama")
def v1871_auto_method_get(token: str, maktab_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    try:
        _v1852_tables(cur)
        _v1871_auto_method_tables(cur)
        if not _v1852_staff(cur, actor_id, maktab_id):
            raise HTTPException(
                status_code=403,
                detail="Bu maktab metod kuni sozlamasini ko'rishga ruxsat yo'q",
            )
        cur.execute(
            "SELECT yoqilgan FROM aqlli_metod_avto_sozlamalari_v2 "
            "WHERE maktab_id=%s",
            (maktab_id,),
        )
        row = cur.fetchone()
        rules = _v1871_method_rules(cur, maktab_id)
        return {
            "yoqilgan": bool((row or {}).get("yoqilgan")),
            "qoidalar": [
                {
                    "id": rule.get("id"),
                    "fan_nomi": rule["fan_nomi"],
                    "hafta_kuni": int(rule["hafta_kuni"]),
                    "qattiq": bool(rule["qattiq"]),
                }
                for rule in rules
            ],
            "hisobot": _v1871_method_report(cur, maktab_id, rules),
            "izoh": (
                "Avto O'CHIQ bo'lsa tizim metod kunini o'zi aniqlamaydi. "
                "Avto YOQ bo'lsa faqat shu fan→kun qoidalari ishlaydi."
            ),
        }
    finally:
        cur.close()
        conn.close()


@app.put("/api/maktab/aqlli_jadval/v2/metod_avto_sozlama")
def v1871_auto_method_save(sorov: V1871AutoMethodSettings, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    try:
        _v1852_tables(cur)
        _v1871_auto_method_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(
                status_code=403,
                detail="Avto metod kunini faqat maktab rahbariyati boshqaradi",
            )

        year = _v1852_active_year(cur, sorov.maktab_id)
        weekdays = int((year or {}).get("hafta_kunlari") or 6)

        # Faqat maktabdagi aniq fan nomlari. TARIX/TARBIYA kabi yaqin
        # so'zlar hech qachon bir-biriga aralashmaydi.
        teachers = [
            row for row in _v1859_effective_teachers(cur, sorov.maktab_id)
            if row.get("dars_beruvchi")
        ]
        canonical = {}
        for teacher in teachers:
            for subject in teacher.get("fanlar_royxati") or []:
                key = _v1871_method_subject_key(subject)
                if key:
                    canonical.setdefault(key, str(subject).strip())

        normalized_rules = []
        seen = set()
        for index, item in enumerate(sorov.qoidalar):
            key = _v1871_method_subject_key(item.fan_nomi)
            if not key or key in seen:
                continue
            if key not in canonical:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Maktab o'qituvchilarida aniq fan topilmadi: "
                        f"{item.fan_nomi}"
                    ),
                )
            day = int(item.hafta_kuni)
            if day < 1 or day > weekdays:
                raise HTTPException(
                    status_code=400,
                    detail=f"{canonical[key]} uchun hafta kuni noto'g'ri",
                )
            seen.add(key)
            normalized_rules.append({
                "fan_nomi": canonical[key],
                "fan_kaliti": key,
                "hafta_kuni": day,
                "qattiq": bool(item.qattiq),
                "tartib": index,
            })

        if sorov.yoqilgan and not normalized_rules:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Avto metod kunini yoqish uchun kamida bitta "
                    "fan→kun qoidasi kerak"
                ),
            )

        cur.execute(
            "DELETE FROM aqlli_metod_fan_qoidalari_v2 WHERE maktab_id=%s",
            (sorov.maktab_id,),
        )
        for rule in normalized_rules:
            cur.execute(
                """INSERT INTO aqlli_metod_fan_qoidalari_v2(
                    maktab_id,fan_nomi,fan_kaliti,hafta_kuni,qattiq,tartib)
                   VALUES(%s,%s,%s,%s,%s,%s)""",
                (
                    sorov.maktab_id,
                    rule["fan_nomi"],
                    rule["fan_kaliti"],
                    rule["hafta_kuni"],
                    rule["qattiq"],
                    rule["tartib"],
                ),
            )

        cur.execute(
            """INSERT INTO aqlli_metod_avto_sozlamalari_v2(
                maktab_id,yoqilgan,yangilagan_user_id,yangilangan_at)
               VALUES(%s,%s,%s,NOW())
               ON CONFLICT(maktab_id) DO UPDATE SET
                 yoqilgan=EXCLUDED.yoqilgan,
                 yangilagan_user_id=EXCLUDED.yangilagan_user_id,
                 yangilangan_at=NOW()""",
            (sorov.maktab_id, bool(sorov.yoqilgan), actor_id),
        )

        # Eski va yangi avtomatik qatorlar qayta quriladi.
        # Qo'lda belgilangan metod kunlariga tegilmaydi.
        auto_where = _v1871_auto_method_where()
        cur.execute(
            f"""DELETE FROM aqlli_oqituvchi_vaqti_v2
                WHERE maktab_id=%s AND turi='metod_kuni'
                  AND {auto_where}""",
            (
                sorov.maktab_id,
                _V1871_AUTO_METHOD_PREFIX + "%",
                _V1871_OLD_AUTO_PREFIX + "%",
            ),
        )

        applied = 0
        skipped_manual = []
        conflicts = []

        if sorov.yoqilgan:
            cur.execute(
                f"""SELECT DISTINCT user_id
                    FROM aqlli_oqituvchi_vaqti_v2
                    WHERE maktab_id=%s AND turi='metod_kuni'
                      AND NOT {auto_where}""",
                (
                    sorov.maktab_id,
                    _V1871_AUTO_METHOD_PREFIX + "%",
                    _V1871_OLD_AUTO_PREFIX + "%",
                ),
            )
            manual_users = {int(row["user_id"]) for row in cur.fetchall()}

            for teacher in teachers:
                uid = int(teacher["user_id"])
                subject_keys = {
                    _v1871_method_subject_key(subject)
                    for subject in (teacher.get("fanlar_royxati") or [])
                }
                matched = [
                    rule
                    for rule in normalized_rules
                    if rule["fan_kaliti"] in subject_keys
                ]
                if not matched:
                    continue

                if uid in manual_users:
                    skipped_manual.append({
                        "user_id": uid,
                        "full_name": teacher["full_name"],
                    })
                    continue

                chosen = matched[0]
                days = sorted({rule["hafta_kuni"] for rule in matched})
                if len(days) > 1:
                    conflicts.append({
                        "user_id": uid,
                        "full_name": teacher["full_name"],
                        "fanlar": [rule["fan_nomi"] for rule in matched],
                        "kunlar": [
                            _V1852_HAFTA.get(day, str(day))
                            for day in days
                        ],
                        "tanlangan": _V1852_HAFTA.get(
                            chosen["hafta_kuni"],
                            str(chosen["hafta_kuni"]),
                        ),
                    })

                note = (
                    f"{_V1871_AUTO_METHOD_PREFIX} {chosen['fan_nomi']} | "
                    f"{_V1852_HAFTA.get(chosen['hafta_kuni'], chosen['hafta_kuni'])}"
                )
                cur.execute(
                    """INSERT INTO aqlli_oqituvchi_vaqti_v2(
                        maktab_id,user_id,hafta_kuni,smena,dars_raqami,
                        turi,qattiq,izoh)
                       VALUES(%s,%s,%s,0,0,'metod_kuni',%s,%s)
                       ON CONFLICT(
                         maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi
                       ) DO UPDATE SET
                         qattiq=EXCLUDED.qattiq,
                         izoh=EXCLUDED.izoh""",
                    (
                        sorov.maktab_id,
                        uid,
                        chosen["hafta_kuni"],
                        chosen["qattiq"],
                        note,
                    ),
                )
                applied += 1

        conn.commit()
        rules = _v1871_method_rules(cur, sorov.maktab_id)
        return {
            "holat": "saqlandi",
            "yoqilgan": bool(sorov.yoqilgan),
            "qoida_soni": len(rules),
            "avto_belgilangan": applied,
            "qolda_metod_borligi_uchun_otkazildi": skipped_manual,
            "bir_necha_fan_kuni_ziddiyati": conflicts,
            "hisobot": _v1871_method_report(
                cur, sorov.maktab_id, rules
            ),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

# ========================= V18.71 END =========================

# ═══════════════════════════════════════════════════════════
# V18.73 — RASMIY METOD KUNLARI PRESETI + PSIXOLOG ISTISNOSI
# O'zA 12.12.2024 dagi fan guruhlari asosida birinchi ochilishda
# qattiq metod kunlari avtomatik qo'llanadi. Keyin rahbariyat
# o'qituvchi vaqt matritsasida bittalab tuzatishi mumkin.
# ═══════════════════════════════════════════════════════════

_V1873_METHOD_PREFIX = "V18.73 RASMIY METOD:"
_V1873_SOURCE_URL = "https://uza.uz/cn/posts/kasbiy-rivojlanish-kuni-va-kasbiy-rivojlanish-soati-joriy-etildi_667022"
_V1873_DAY_LABELS = {
    1: "Dushanba", 2: "Seshanba", 3: "Chorshanba",
    4: "Payshanba", 5: "Juma", 6: "Shanba",
}
_V1873_OFFICIAL_DISPLAY = {
    1: ["Tarix", "Davlat va huquq asoslari", "Tarbiya"],
    2: ["Ona tili", "Adabiyot", "O‘zbek tili", "Rus tili"],
    3: ["Fizika", "Astronomiya", "Kimyo", "Biologiya", "Geografiya", "Iqtisodiyot", "Tabiiy fan"],
    4: ["Matematika", "Algebra", "Geometriya", "Informatika", "Axborot texnologiyalari"],
    5: ["Ingliz tili", "Nemis tili", "Fransuz tili", "Boshqa xorijiy tillar"],
    6: ["Boshlang‘ich ta’lim", "Tasviriy san’at", "Chizmachilik", "Musiqa", "Texnologiya", "Jismoniy tarbiya", "Chaqiruvga qadar boshlang‘ich tayyorgarlik"],
}


def _v1873_norm(value):
    text = str(value or "").casefold()
    for old in ("‘", "’", "`", "ʼ", "ʻ"):
        text = text.replace(old, "'")
    text = re.sub(r"[^0-9a-zа-яёўқғҳў' ]+", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def _v1873_subject_day(subject, central_days=None):
    key = _v1873_norm(subject)
    if not key:
        return None
    central_day = (central_days or {}).get(_v1875_subject_key(subject))
    if central_day:
        return int(central_day)

    # Shanba amaliy fanlari avval tekshiriladi: "jismoniy tarbiya"
    # oddiy "tarbiya" bilan Dushanbaga tushib ketmasin.
    if any(token in key for token in (
        "jismoniy tarbiya", "tasviriy san", "chizmachilik",
        "musiqa", "chaqiruvga qadar", "boshlang'ich harbiy",
    )):
        return 6
    if "texnologiya" in key and "axborot" not in key and "informatika" not in key:
        return 6

    # Xorijiy tillar. Ona/O'zbek/Rus tili Seshanbada qoladi.
    if any(token in key for token in ("ingliz tili", "nemis tili", "fransuz tili", "xorijiy til")):
        return 5

    # Aniq fanlar.
    if any(token in key for token in ("matematika", "algebra", "geometriya", "informatika", "axborot texnolog")):
        return 4

    # Tabiiy fanlar va iqtisodiyot.
    if any(token in key for token in (
        "fizika", "astronomiya", "kimyo", "biologiya", "geografiya",
        "iqtisod", "tadbirkor", "tabiiy fan", "science",
    )):
        return 3

    # Filologiya.
    if any(token in key for token in ("ona tili", "adabiyot", "o'zbek tili", "rus tili", "o'qish savodxonligi")):
        return 2

    # Ijtimoiy fanlar.
    if "tarix" in key or "davlat va huquq" in key or key == "tarbiya":
        return 1

    # "Boshqa xorijiy tillar": yuqoridagi ichki tillar chiqarib tashlangach
    # qolgan "... tili" fanlari Juma bo'ladi.
    if key.endswith(" tili"):
        return 5
    return None


def _v1873_tables(cur):
    _v1871_auto_method_tables(cur)
    cur.execute(
        "ALTER TABLE aqlli_metod_avto_sozlamalari_v2 "
        "ADD COLUMN IF NOT EXISTS rasmiy_preset_v1873 BOOLEAN NOT NULL DEFAULT FALSE"
    )
    cur.execute(
        "ALTER TABLE aqlli_metod_avto_sozlamalari_v2 "
        "ADD COLUMN IF NOT EXISTS rasmiy_manba TEXT"
    )


def _v1873_primary_teacher_ids(cur, maktab_id):
    cur.execute("""
        SELECT DISTINCT rahbar_user_id AS user_id
        FROM maktab_sinflari
        WHERE maktab_id=%s AND rahbar_user_id IS NOT NULL
          AND NULLIF(REGEXP_REPLACE(COALESCE(sinf,''),'[^0-9]','','g'),'')::int BETWEEN 1 AND 4
    """, (maktab_id,))
    return {int(row["user_id"]) for row in cur.fetchall()}


def _v1873_assignments(cur, maktab_id):
    central_days = {}
    for row in _v201_central_rows(cur):
        if row.get("metod_kuni"):
            central_days[_v1875_subject_key(row["fan_nomi"])] = int(row["metod_kuni"])
    primary_ids = _v1873_primary_teacher_ids(cur, maktab_id)
    teachers = [
        row for row in _v1859_effective_teachers(cur, maktab_id)
        if row.get("dars_beruvchi") and str(row.get("lavozim") or "") != "psixolog"
    ]
    assignments = []
    conflicts = []
    for teacher in teachers:
        uid = int(teacher["user_id"])
        class_grades = []
        for class_name in teacher.get("sinflar_royxati") or []:
            match = re.match(r"^\s*(\d+)", str(class_name))
            if match:
                class_grades.append(int(match.group(1)))
        subject_keys = [_v1873_norm(subject) for subject in (teacher.get("fanlar_royxati") or [])]
        primary_subject_hits = sum(
            1 for key in subject_keys
            if any(token in key for token in (
                "ona tili", "o'qish savodxonligi", "matematika",
                "tabiiy fan", "boshlang'ich ta'lim"
            ))
        )
        primary_teacher = (
            uid in primary_ids
            or any("boshlang'ich ta'lim" in key for key in subject_keys)
            or (class_grades and max(class_grades) <= 4 and primary_subject_hits >= 2)
        )
        if primary_teacher:
            assignments.append({
                "user_id": uid,
                "full_name": teacher["full_name"],
                "hafta_kuni": 6,
                "asos": "Boshlang‘ich ta’lim",
                "fanlar": teacher.get("fanlar_royxati") or [],
            })
            continue

        by_day = {}
        for subject in teacher.get("fanlar_royxati") or []:
            day = _v1873_subject_day(subject, central_days)
            if day:
                by_day.setdefault(day, []).append(str(subject))
        if not by_day:
            continue

        # Bir nechta guruhga tushgan o'qituvchida eng ko'p fan tushgan kun;
        # teng bo'lsa haftadagi oldingi kun tanlanadi. Hisobotda ziddiyat chiqadi.
        chosen_day = sorted(by_day, key=lambda d: (-len(by_day[d]), d))[0]
        if len(by_day) > 1:
            conflicts.append({
                "user_id": uid,
                "full_name": teacher["full_name"],
                "kunlar": [
                    {"hafta_kuni": day, "kun_nomi": _V1873_DAY_LABELS[day], "fanlar": by_day[day]}
                    for day in sorted(by_day)
                ],
                "tanlangan_kun": chosen_day,
                "tanlangan_kun_nomi": _V1873_DAY_LABELS[chosen_day],
            })
        assignments.append({
            "user_id": uid,
            "full_name": teacher["full_name"],
            "hafta_kuni": chosen_day,
            "asos": ", ".join(by_day[chosen_day]),
            "fanlar": teacher.get("fanlar_royxati") or [],
        })
    return assignments, conflicts


def _v1873_apply_official(cur, maktab_id, replace_existing=True):
    assignments, conflicts = _v1873_assignments(cur, maktab_id)
    user_ids = [row["user_id"] for row in assignments]

    # Avval eski V18.71/V18.73 avtomatik qatorlar tozalanadi.
    cur.execute("""
        DELETE FROM aqlli_oqituvchi_vaqti_v2
        WHERE maktab_id=%s AND turi='metod_kuni'
          AND (COALESCE(izoh,'') LIKE 'V18.71 AUTO METOD:%%'
               OR COALESCE(izoh,'') LIKE 'V18.73 RASMIY METOD:%%')
    """, (maktab_id,))

    if replace_existing and user_ids:
        # Birinchi rasmiy qo'llashda shu o'qituvchilarning noto'g'ri qo'lda
        # kiritilgan metod kunlari ham almashtiriladi. Psixolog bu ro'yxatda yo'q.
        cur.execute("""
            DELETE FROM aqlli_oqituvchi_vaqti_v2
            WHERE maktab_id=%s AND turi='metod_kuni' AND user_id=ANY(%s)
        """, (maktab_id, user_ids))

    rows = []
    for item in assignments:
        note = (
            f"{_V1873_METHOD_PREFIX} {item['asos']} | "
            f"{_V1873_DAY_LABELS[item['hafta_kuni']]}"
        )
        rows.append((
            maktab_id, item["user_id"], item["hafta_kuni"], 0, 0,
            "metod_kuni", True, note,
        ))
    if rows:
        psycopg2.extras.execute_values(cur, """
            INSERT INTO aqlli_oqituvchi_vaqti_v2(
                maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi,qattiq,izoh)
            VALUES %s
            ON CONFLICT(maktab_id,user_id,hafta_kuni,smena,dars_raqami,turi)
            DO UPDATE SET qattiq=EXCLUDED.qattiq,izoh=EXCLUDED.izoh
        """, rows)
    return assignments, conflicts


def _v1873_report(assignments, conflicts):
    grouped = []
    for day in range(1, 7):
        teachers = [row for row in assignments if int(row["hafta_kuni"]) == day]
        grouped.append({
            "hafta_kuni": day,
            "kun_nomi": _V1873_DAY_LABELS[day],
            "fanlar": _V1873_OFFICIAL_DISPLAY[day],
            "oqituvchi_soni": len(teachers),
            "oqituvchilar": [
                {"user_id": row["user_id"], "full_name": row["full_name"], "asos": row["asos"]}
                for row in teachers[:80]
            ],
        })
    return {
        "kunlar": grouped,
        "jami_oqituvchi": len(assignments),
        "ziddiyatlar": conflicts,
        "ziddiyat_soni": len(conflicts),
        "psixolog_izohi": "Psixologga metod kuni avtomatik belgilanmaydi.",
        "manba": _V1873_SOURCE_URL,
    }


class V1873OfficialMethodSettings(BaseModel):
    maktab_id: int
    yoqilgan: bool = True
    qayta_qollash: bool = False


@app.get("/api/maktab/aqlli_jadval/v3/metod_rasmiy_sozlama")
def v1873_official_method_get(token: str, maktab_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        _v1873_tables(cur)
        if not _v1852_staff(cur, actor_id, maktab_id):
            raise HTTPException(status_code=403, detail="Metod kuni sozlamasini ko'rishga ruxsat yo'q")

        cur.execute("""
            SELECT yoqilgan,rasmiy_preset_v1873
            FROM aqlli_metod_avto_sozlamalari_v2 WHERE maktab_id=%s
        """, (maktab_id,))
        setting = cur.fetchone()
        first_apply = False

        if _v1852_manager(cur, actor_id, maktab_id) and not bool((setting or {}).get("rasmiy_preset_v1873")):
            assignments, conflicts = _v1873_apply_official(cur, maktab_id, replace_existing=True)
            cur.execute("""
                INSERT INTO aqlli_metod_avto_sozlamalari_v2(
                    maktab_id,yoqilgan,yangilagan_user_id,yangilangan_at,
                    rasmiy_preset_v1873,rasmiy_manba)
                VALUES(%s,TRUE,%s,NOW(),TRUE,%s)
                ON CONFLICT(maktab_id) DO UPDATE SET
                    yoqilgan=TRUE,
                    yangilagan_user_id=EXCLUDED.yangilagan_user_id,
                    yangilangan_at=NOW(),
                    rasmiy_preset_v1873=TRUE,
                    rasmiy_manba=EXCLUDED.rasmiy_manba
            """, (maktab_id, actor_id, _V1873_SOURCE_URL))
            conn.commit()
            first_apply = True
            enabled = True
        else:
            assignments, conflicts = _v1873_assignments(cur, maktab_id)
            enabled = bool((setting or {}).get("yoqilgan"))

        return {
            "yoqilgan": enabled,
            "birinchi_marta_qollandi": first_apply,
            **_v1873_report(assignments, conflicts),
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.put("/api/maktab/aqlli_jadval/v3/metod_rasmiy_sozlama")
def v1873_official_method_save(sorov: V1873OfficialMethodSettings, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1852_tables(cur)
        _v1873_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Rasmiy metod kunlarini faqat maktab rahbariyati boshqaradi")
        _v201_mark_school_override(cur, sorov.maktab_id, "metod_kunlari", actor_id)

        assignments, conflicts = _v1873_assignments(cur, sorov.maktab_id)
        if sorov.yoqilgan:
            assignments, conflicts = _v1873_apply_official(
                cur, sorov.maktab_id, replace_existing=True
            )
        else:
            cur.execute("""
                DELETE FROM aqlli_oqituvchi_vaqti_v2
                WHERE maktab_id=%s AND turi='metod_kuni'
                  AND COALESCE(izoh,'') LIKE %s
            """, (sorov.maktab_id, _V1873_METHOD_PREFIX + "%"))

        cur.execute("""
            INSERT INTO aqlli_metod_avto_sozlamalari_v2(
                maktab_id,yoqilgan,yangilagan_user_id,yangilangan_at,
                rasmiy_preset_v1873,rasmiy_manba)
            VALUES(%s,%s,%s,NOW(),TRUE,%s)
            ON CONFLICT(maktab_id) DO UPDATE SET
                yoqilgan=EXCLUDED.yoqilgan,
                yangilagan_user_id=EXCLUDED.yangilagan_user_id,
                yangilangan_at=NOW(),
                rasmiy_preset_v1873=TRUE,
                rasmiy_manba=EXCLUDED.rasmiy_manba
        """, (sorov.maktab_id, bool(sorov.yoqilgan), actor_id, _V1873_SOURCE_URL))
        conn.commit()
        return {
            "holat": "saqlandi",
            "yoqilgan": bool(sorov.yoqilgan),
            "qayta_qollandi": bool(sorov.yoqilgan and sorov.qayta_qollash),
            **_v1873_report(assignments, conflicts),
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()

# ========================= V18.73 END =========================

# ═══════════════════════════════════════════════════════════
# V18.74 — SANQvaN ASOSIDAGI DARS JADVALI MANTIG'I
# 1–4-sinf kunlik yuklama, 5–11-sinf 6 dars limiti,
# asosiy fanlarni 2–3/2–4-darslarga, yengil fanlarni kechroq,
# jismoniy tarbiyani oxirgi darslarga joylashtirish.
# ═══════════════════════════════════════════════════════════

_v1874_base_build_jobs = _v1852_build_jobs
_v1874_base_candidate_reasons = _v1852_candidate_reasons
_v1874_base_candidate_score = _v1852_candidate_score
_v1874_base_place_job = _v1852_place_job


def _v1874_subject_key(value):
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    for old in ("‘", "’", "`", "ʼ", "ʻ", "'", "\""):
        text = text.replace(old, "")
    text = re.sub(r"[^a-z0-9а-яёқғҳў]+", " ", text, flags=re.IGNORECASE)
    return " ".join(text.split())


def _v1874_grade(class_row):
    match = re.search(r"\d+", str((class_row or {}).get("sinf") or ""))
    return int(match.group()) if match else 0


def _v1874_contains(key, *phrases):
    return any(_v1874_subject_key(phrase) in key for phrase in phrases)


def _v1874_subject_profile(fan, grade):
    key = _v1874_subject_key(fan)
    is_class_hour = key == "sinf soati" or "sinf soati" in key
    is_physical = _v1874_contains(key, "jismoniy tarbiya", "jismoniy madaniyat")
    is_technology = (
        _v1874_contains(key, "texnologiya", "mehnat")
        and not _v1874_contains(key, "axborot texnologiyalari")
    )
    is_art = _v1874_contains(key, "tasviriy sanat", "chizmachilik", "rasm")
    is_music = _v1874_contains(key, "musiqa")
    is_upbringing = _v1874_contains(key, "tarbiya") and not is_physical
    is_military = _v1874_contains(key, "chaqiruvga qadar")
    is_math = _v1874_contains(key, "matematika", "algebra", "geometriya")
    is_native_language = _v1874_contains(key, "ona tili", "ozbek tili")
    is_reading = _v1874_contains(key, "oqish savodxonligi", "oqish")
    is_language = _v1874_contains(
        key, "ona tili", "ozbek tili", "rus tili", "ingliz tili",
        "nemis tili", "fransuz tili", "xorijiy til"
    )
    is_natural = _v1874_contains(
        key, "tabiiy fan", "tabiat", "informatika", "axborot texnologiyalari",
        "fizika", "kimyo", "biologiya", "geografiya", "astronomiya",
        "iqtisodiyot", "iqtisodiy bilim"
    )
    is_history = _v1874_contains(key, "tarix", "davlat va huquq", "huquq asoslari")
    is_literature = _v1874_contains(key, "adabiyot")
    is_core_science = _v1874_contains(
        key, "fizika", "kimyo", "biologiya", "tabiiy fan", "tabiat"
    )

    primary_light = bool(
        is_class_hour or is_physical or is_technology or is_art or
        is_music or is_upbringing or is_military
    )
    primary_core = bool(
        grade <= 4 and not primary_light and
        (is_math or is_language or is_reading or is_natural or is_literature)
    )

    if grade <= 4:
        if is_math:
            difficulty = 8
        elif is_language:
            difficulty = 7
        elif is_natural:
            difficulty = 6
        elif is_literature:
            difficulty = 5
        elif is_reading:
            difficulty = 4
        elif is_art or is_music:
            difficulty = 3
        elif is_technology or is_upbringing or is_class_hour:
            difficulty = 2
        elif is_physical:
            difficulty = 1
        else:
            difficulty = 4
    else:
        if _v1874_contains(key, "kimyo"):
            difficulty = 13
        elif _v1874_contains(key, "geometriya"):
            difficulty = 12
        elif _v1874_contains(key, "fizika"):
            difficulty = 12
        elif _v1874_contains(key, "algebra"):
            difficulty = 10
        elif _v1874_contains(key, "matematika"):
            difficulty = 11
        elif is_language:
            difficulty = 10
        elif is_natural:
            difficulty = 8
        elif is_history:
            difficulty = 8
        elif is_literature:
            difficulty = 6
        elif is_technology or is_art:
            difficulty = 3
        elif is_music or is_physical or is_upbringing or is_class_hour:
            difficulty = 2
        else:
            difficulty = 6

    light = bool(primary_light or (grade >= 5 and (
        is_physical or is_technology or is_art or is_music or
        is_upbringing or is_class_hour or is_military
    )))
    heavy = bool(not light and difficulty >= 7)
    written_heavy = bool(not light and (
        is_math or is_language or is_reading or is_natural or
        is_history or is_literature
    ))
    # Pedagogik asosiy fanlar: aynan o'quvchining ertalabki yuqori diqqatini
    # talab qiladigan yozma/tahliliy fanlar. Xorijiy til, informatika, tarix va
    # geografiya muhim, lekin bu qatlamga avtomatik kiritilmaydi — aks holda
    # deyarli barcha fan "asosiy" bo'lib, ustuvorlikning ma'nosi yo'qoladi.
    core_priority = bool(
        primary_core or is_math or is_native_language or is_literature
        or is_core_science or is_reading
    )

    return {
        "key": key,
        "academic": not is_class_hour,
        "class_hour": is_class_hour,
        "physical": is_physical,
        "technology": is_technology,
        "light": light,
        "primary_light": primary_light,
        "primary_core": primary_core,
        "heavy": heavy,
        "written_heavy": written_heavy,
        "math": is_math,
        "native_language": is_native_language,
        "core_science": is_core_science,
        "core_priority": core_priority,
        "difficulty": int(difficulty),
    }


def _v1874_subject_period_penalty(profile, grade, period, max_period=None):
    """Fan uchun tavsiya etilgan dars oralig'ini yumshoq ustuvorlikka aylantiradi.

    Oraliq qattiq blok emas: o'qituvchi, xona yoki boshqa majburiy qoida sabab
    mos joy qolmasa generator istisno slotdan foydalanishi mumkin.
    """
    grade = int(grade or 0)
    period = int(period or 0)
    max_period = int(max_period or _v1874_max_total_periods(grade))
    if profile.get("physical"):
        # Jismoniy tarbiya 3–6-darslarda afzal; 1–2 faqat zarur istisno.
        return {1: 320, 2: 190, 3: 25, 4: -12, 5: -24, 6: -28}.get(
            period, 20 + abs(period - min(6, max_period)) * 8
        )
    if profile.get("technology"):
        # Texnologiya amaliy fan: 1–2-dars faqat boshqa yechim qolmaganda,
        # odatda 4–6-darslarda (imkon bo'lsa J/T dan keyin) joylashadi.
        return {1: 330, 2: 220, 3: 48, 4: -12, 5: -25, 6: -30}.get(
            period, 35 + abs(period - min(6, max_period)) * 8
        )
    if profile.get("math"):
        # Matematika 1–5 oralig'ida qoladi, 2–4 eng samarali vaqt.
        return {1: 2, 2: -10, 3: -12, 4: -9, 5: 5, 6: 70}.get(
            period, 90 + max(0, period - 6) * 15
        )
    return 0


def _v1874_max_total_periods(grade):
    return 5 if 1 <= int(grade or 0) <= 4 else 6


def _v1874_fifth_day_limit(grade):
    if int(grade or 0) == 1:
        return 2
    if 2 <= int(grade or 0) <= 4:
        return 4
    return 0


def _v1874_weekly_max(grade):
    grade = int(grade or 0)
    if grade == 1:
        return 22
    if 2 <= grade <= 4:
        return 24
    if grade == 5:
        return 32
    if grade == 6:
        return 33
    if grade == 7:
        return 35
    if 8 <= grade <= 11:
        return 36
    return None


def _v1874_profile_for_job(job, context):
    profile = job.get("v1874_profile")
    if profile:
        return profile
    class_row = context.get("classes", {}).get(job.get("sinf_id"), {})
    grade = int(job.get("v1874_grade") or _v1874_grade(class_row))
    profile = _v1874_subject_profile(job.get("fan"), grade)
    job["v1874_grade"] = grade
    job["v1874_profile"] = profile
    return profile


def _v1852_build_jobs(classes, loads, assignments, group_settings, teachers):
    jobs, warnings = _v1874_base_build_jobs(
        classes, loads, assignments, group_settings, teachers
    )
    # Bir fan soati ikki o'qituvchi orasida 3+1 kabi taqsimlangan bo'lsa,
    # generator ham aynan shu kvotani saqlaydi; shunchaki tasodifiy o'qituvchi tanlamaydi.
    whole_quotas = _v1852_defaultdict(list)
    for assignment in assignments:
        if _v1875_group_key(assignment.get("guruh_kaliti")) != "whole":
            continue
        teacher_id = assignment.get("user_id")
        if teacher_id is None:
            continue
        key = (
            int(assignment["sinf_id"]),
            str(assignment.get("fan_nomi") or "").strip().casefold(),
        )
        whole_quotas[key].extend(
            [int(teacher_id)] * max(0, int(math.ceil(float(assignment.get("haftalik_soat") or 0))))
        )
    class_hours = _v1852_Counter()
    for job in jobs:
        if not job.get("groups"):
            quota = whole_quotas.get(
                (int(job["sinf_id"]), str(job.get("fan") or "").strip().casefold()), []
            )
            occurrence = max(1, int(job.get("occurrence") or 1))
            if occurrence <= len(quota):
                job["teacher_options"] = [quota[occurrence - 1]]
        class_row = classes.get(job["sinf_id"], {})
        grade = _v1874_grade(class_row)
        profile = _v1874_subject_profile(job["fan"], grade)
        job["v1874_grade"] = grade
        job["v1874_profile"] = profile
        job["difficulty"] = int(job.get("difficulty") or 0) + profile["difficulty"] * 3
        if profile["heavy"]:
            job["weight"] = max(int(job.get("weight") or 1), 3)
        elif profile["light"]:
            job["weight"] = 1
        if grade <= 4 and profile["primary_core"]:
            job["preferred_last"] = min(int(job.get("preferred_last") or 4), 4)
        elif profile["physical"] or profile["light"]:
            job["preferred_last"] = _v1874_max_total_periods(grade)
        elif profile["heavy"]:
            job["preferred_last"] = min(int(job.get("preferred_last") or 4), 4)
    # Har bir 0,5 qator boshqa 0,5 qator bilan bitta dars slotiga juftlanadi:
    # birinchisi toq, ikkinchisi juft haftada o'tadi. 1,5 soat esa bitta
    # har-haftalik dars + bitta aylanish darsi bo'ladi.
    regular_jobs = [job for job in jobs if float(job.get("rotation_weight") or 1) >= 1]
    half_by_class = _v1852_defaultdict(list)
    for job in jobs:
        if float(job.get("rotation_weight") or 1) >= 1:
            continue
        signature = (
            int(job["sinf_id"]), int(job.get("smena") or 1),
            tuple(group.get("guruh_kaliti") for group in job.get("groups") or []),
        )
        half_by_class[signature].append(job)
    rotation_pairs = 0
    for signature, half_jobs in sorted(half_by_class.items(), key=lambda item: item[0]):
        # Bir katakda almashadigan 0,5 fanlar vaqt talabi bo'yicha bir-biriga
        # yaqin bo'lsin: og'ir fan og'ir fan bilan, amaliy/yengil fan esa
        # shunga o'xshash fan bilan juftlanadi. Shunda A/B slotning ikkala
        # haftasi ham bir xil qulay dars vaqtiga tushadi.
        ordered_halves = sorted(
            half_jobs,
            key=lambda item: (
                bool((item.get("v1874_profile") or {}).get("physical")),
                bool((item.get("v1874_profile") or {}).get("light")),
                int((item.get("v1874_profile") or {}).get("difficulty") or 0),
                int(item.get("preferred_last") or 5),
                str(item.get("fan") or "").casefold(),
                int(item.get("load_id") or 0),
            ),
        )
        for index in range(0, len(ordered_halves), 2):
            members = ordered_halves[index:index + 2]
            phases = ("toq", "juft")
            rotation_members = [
                {**member, "hafta_turi": phases[member_index]}
                for member_index, member in enumerate(members)
            ]
            first = members[0]
            combined = {
                **first,
                "job_id": "rotation:" + ":".join(str(member.get("job_id")) for member in members),
                "fan": " / ".join(str(member.get("fan") or "") for member in members),
                "groups": [],
                "teacher_options": [],
                "room_id": None,
                "rotation_weight": 1.0,
                "rotation_members": rotation_members,
                "difficulty": max(float(member.get("difficulty") or 0) for member in members) + 25,
                "weight": max(int(member.get("weight") or 1) for member in members),
                "preferred_last": min(int(member.get("preferred_last") or 5) for member in members),
            }
            regular_jobs.append(combined)
            rotation_pairs += 1
    jobs = regular_jobs
    for job in jobs:
        class_hours[job["sinf_id"]] += 1

    for class_id, total in sorted(class_hours.items()):
        class_row = classes.get(class_id, {})
        grade = _v1874_grade(class_row)
        weekly_max = _v1874_weekly_max(grade)
        if weekly_max is not None and total > weekly_max:
            warnings.append(
                f"{class_row.get('sinf','')}-{class_row.get('harf','')}: "
                f"{total} soat yuklama gigiyenik haftalik maksimum {weekly_max} soatdan oshgan"
            )

    warnings.append(
        "SanQvaN profili faol: 1–4-sinfda 6-dars qo‘yilmaydi; "
        "5–11-sinfda majburiy darslar 6 tadan oshmaydi; asosiy fanlar ertaroq, "
        "yengil va jismoniy tarbiya darslari kechroq joylashtiriladi"
    )
    if rotation_pairs:
        warnings.append(
            f"A/B hafta aylanishi faol: {rotation_pairs} ta slotda 0,5 soatli fanlar "
            "toq va juft haftalarda navbat bilan o'tadi"
        )
    return jobs, warnings


_v199_base_choose_teacher = _v1852_choose_teacher


def _v199_rotation_member_teachers(member):
    if member.get("groups"):
        return [group.get("teacher") for group in member.get("groups") or []]
    options = member.get("teacher_options") or []
    return [options[0] if options else None]


def _v1852_choose_teacher(job, day, period, state, context):
    members = job.get("rotation_members") or []
    if not members:
        return _v199_base_choose_teacher(job, day, period, state, context)
    selected = []
    for member in members:
        for teacher in _v199_rotation_member_teachers(member):
            if teacher not in selected:
                selected.append(teacher)
    return selected or [None]


def _v1874_state_maps(state):
    total = state.setdefault("class_daily_total", _v1852_defaultdict(int))
    academic = state.setdefault("class_daily_academic", _v1852_defaultdict(int))
    fifth_days = state.setdefault("class_fifth_academic_days", _v1852_defaultdict(set))
    difficulty = state.setdefault("class_day_difficulty", _v1852_defaultdict(int))
    period_jobs = state.setdefault("class_period_jobs", _v1852_defaultdict(dict))
    return total, academic, fifth_days, difficulty, period_jobs


def _v1852_candidate_reasons(job, day, period, selected_teachers, room_keys, state, context):
    reasons = list(_v1874_base_candidate_reasons(
        job, day, period, selected_teachers, room_keys, state, context
    ))
    # REV52: SINIF SOATI ham metod kuniga tushmaydi. Agar sinf soati qoidasi
    # aynan metod kuniga qotirilgan bo'lsa, diagnostika to'qnashuvni ko'rsatadi;
    # metod kuni esa buzilmaydi.
    profile = _v1874_profile_for_job(job, context)
    grade = int(job.get("v1874_grade") or 0)
    total_map, academic_map, fifth_map, _, _ = _v1874_state_maps(state)
    class_day = (job["sinf_id"], day)
    total_count = int(total_map.get(class_day, 0))
    academic_count = int(academic_map.get(class_day, 0))
    max_total = _v1874_max_total_periods(grade)

    if 1 <= grade <= 4 and int(day) == 6:
        reasons.append("1–4-sinf uchun Shanba o‘qish kuni emas")
    if int(period) > max_total:
        reasons.append(f"{grade}-sinf uchun {max_total}-darsdan keyin majburiy dars qo‘yilmaydi")
    if total_count >= max_total:
        reasons.append(f"sinfning kunlik jami {max_total} ta mashg‘ulot limiti to‘lgan")

    if 1 <= grade <= 4:
        if profile["academic"]:
            if state["subject_daily"].get(
                (job["sinf_id"], job["fan"].casefold(), day), 0
            ) >= 1:
                reasons.append("boshlang‘ich sinfda bir fan shu kuni takror qo‘yilmaydi")
            if academic_count >= 5:
                reasons.append("boshlang‘ich sinfning akademik kunlik limiti to‘lgan")
            if academic_count == 4:
                fifth_days = fifth_map.get(job["sinf_id"], set())
                fifth_limit = _v1874_fifth_day_limit(grade)
                if day not in fifth_days and len(fifth_days) >= fifth_limit:
                    reasons.append(
                        f"{grade}-sinfda 5 akademik darsli kunlar soni {fifth_limit} tadan oshmaydi"
                    )
                if not profile["primary_light"]:
                    reasons.append("boshlang‘ichda 5-akademik dars faqat yengil fan bo‘lishi kerak")
        if int(period) == 5 and profile["academic"] and not profile["primary_light"]:
            reasons.append("5-darsga matematika, til, o‘qish yoki boshqa og‘ir fan qo‘yilmaydi")

    return list(dict.fromkeys(reasons))


def _v1852_candidate_score(job, day, period, teachers, state, context, rng):
    score = float(_v1874_base_candidate_score(
        job, day, period, teachers, state, context, rng
    ))
    profile = _v1874_profile_for_job(job, context)
    grade = int(job.get("v1874_grade") or 0)
    _, _, _, difficulty_map, period_jobs = _v1874_state_maps(state)
    max_period = _v1874_max_total_periods(grade)

    # Sinf jadvalida boshidagi bo'sh 1–2-soatlar ham, ichki "okno" ham
    # qolmasin. Eski hisob faqat ikki dars orasidagi teshikni sanab, kun
    # 2- yoki 3-darsdan boshlansa ham "okno 0" deb ko'rsatardi.
    existing_periods = set(period_jobs.get((job["sinf_id"], day), {}).keys())
    new_periods = existing_periods | {period}
    before_void = max(existing_periods) - len(existing_periods) if existing_periods else 0
    after_void = max(new_periods) - len(new_periods) if new_periods else 0
    score += (after_void - before_void) * 650
    if existing_periods and any(abs(period - item) == 1 for item in existing_periods):
        score -= 18
    elif not existing_periods and int(period) == 1:
        score -= 24

    score += _v1874_subject_period_penalty(profile, grade, period, max_period)

    if 1 <= grade <= 4:
        if profile["primary_core"]:
            score += {1: 7, 2: -10, 3: -10, 4: 9, 5: 80}.get(period, 100)
        elif profile["physical"]:
            score += {1: 24, 2: 16, 3: 4, 4: -5, 5: -9}.get(period, 20)
        elif profile["light"]:
            score += {1: 14, 2: 9, 3: 2, 4: -5, 5: -8}.get(period, 15)
        else:
            score += {1: 5, 2: -5, 3: -5, 4: 3, 5: 18}.get(period, 20)
    else:
        if profile["physical"]:
            score += max(0, max_period - period) * 2 - (6 if period == max_period else 0)
        elif profile["light"]:
            score += {1: 12, 2: 7, 3: 2, 4: -2, 5: -5, 6: -7}.get(period, 8)
        elif profile["heavy"]:
            score += {1: 8, 2: -8, 3: -10, 4: -8, 5: 10, 6: 20}.get(period, 25)
        else:
            score += {1: 3, 2: -4, 3: -5, 4: -3, 5: 3, 6: 8}.get(period, 10)

    # Og‘ir fanlar haftaning o‘rtasida, yengil fanlar chetroq kunlarda afzal.
    if profile["heavy"]:
        score += -7 if day in (2, 3) else (5 if day in (1, 5, 6) else 0)
    elif profile["light"]:
        score += -2 if day in (1, 5, 6) else 1

    current_difficulty = int(difficulty_map.get((job["sinf_id"], day), 0))
    score += current_difficulty * profile["difficulty"] * 0.05

    # Og‘ir va yengil fanlar almashsin; Jismoniy tarbiyadan keyin yozma-og‘ir fan kelmasin.
    daily_jobs = period_jobs.get((job["sinf_id"], day), {})
    for neighbor_period in (period - 1, period + 1):
        neighbor = daily_jobs.get(neighbor_period)
        if not neighbor:
            continue
        neighbor_profile = _v1874_profile_for_job(neighbor, context)
        if profile["heavy"] and neighbor_profile["heavy"]:
            score += 12
        elif profile["light"] != neighbor_profile["light"]:
            score -= 3
        if (
            (neighbor_profile["physical"] and profile["written_heavy"] and neighbor_period == period - 1)
            or (profile["physical"] and neighbor_profile["written_heavy"] and neighbor_period == period + 1)
        ):
            score += 900

    return score


def _v1852_place_job(job, day, period, teachers, room_keys, state, context):
    _v1874_base_place_job(job, day, period, teachers, room_keys, state, context)
    rotation_members = job.get("rotation_members") or []
    if rotation_members:
        # Bazaviy joylashtiruvchi har bir o'qituvchiga 1 soat qo'shadi.
        # A/B aylanishida esa o'qituvchi har faza uchun 0,5 yuklama oladi.
        contributions = _v1852_defaultdict(float)
        for member in rotation_members:
            for teacher in set(_v199_rotation_member_teachers(member)):
                if teacher is not None:
                    contributions[int(teacher)] += 0.5
        for teacher, contribution in contributions.items():
            adjustment = max(0.0, 1.0 - contribution)
            state["teacher_week"][teacher] -= adjustment
            state["teacher_daily"][(teacher, day)] -= adjustment
    profile = _v1874_profile_for_job(job, context)
    total_map, academic_map, fifth_map, difficulty_map, period_jobs = _v1874_state_maps(state)
    class_day = (job["sinf_id"], day)
    total_map[class_day] += 1
    if profile["academic"]:
        academic_map[class_day] += 1
        if academic_map[class_day] == 5:
            fifth_map[job["sinf_id"]].add(day)
    difficulty_map[class_day] += int(profile["difficulty"])
    period_jobs[class_day][int(period)] = job


def _v1874_schedule_hygiene_violations(cur, maktab_id: int, run_id: int):
    cur.execute(
        """SELECT DISTINCT e.sinf_id,s.sinf,s.harf,e.hafta_kuni,e.dars_raqami,e.fan_nomi,
                          s.sinf::int AS sinf_sort
           FROM aqlli_jadval_slotlari_v2 e
           JOIN maktab_sinflari s ON s.id=e.sinf_id
           WHERE e.maktab_id=%s AND e.urinish_id=%s
           ORDER BY sinf_sort,s.harf,e.hafta_kuni,e.dars_raqami,e.fan_nomi""",
        (maktab_id, run_id),
    )
    rows = cur.fetchall()
    by_class_day = _v1852_defaultdict(list)
    class_names = {}
    for row in rows:
        class_id = int(row["sinf_id"])
        grade_match = re.search(r"\d+", str(row.get("sinf") or ""))
        grade = int(grade_match.group()) if grade_match else 0
        class_names[class_id] = (f"{row.get('sinf','')}-{row.get('harf','')}", grade)
        by_class_day[(class_id, int(row["hafta_kuni"]))].append(row)

    violations = []
    fifth_days = _v1852_defaultdict(set)
    for (class_id, day), day_rows in by_class_day.items():
        class_name, grade = class_names[class_id]
        period_fans = _v1852_defaultdict(set)
        for row in day_rows:
            period_fans[int(row["dars_raqami"])].add(str(row["fan_nomi"]))
        total_sessions = len(period_fans)
        max_total = _v1874_max_total_periods(grade)
        if period_fans:
            last_period = max(period_fans)
            missing_periods = [
                period for period in range(1, last_period + 1)
                if period not in period_fans
            ]
            if missing_periods:
                missing_text = ", ".join(str(period) for period in missing_periods)
                violations.append({
                    "sinf": class_name,
                    "sabab": (
                        f"{_V1852_HAFTA.get(day, day)} kuni darslar orasida "
                        f"bo'sh okno bor: {missing_text}-dars"
                    ),
                })
        if 1 <= grade <= 4 and day == 6:
            violations.append({"sinf": class_name, "sabab": "Shanba kuni boshlang‘ich sinf darsi bor"})
        if total_sessions > max_total:
            violations.append({
                "sinf": class_name,
                "sabab": f"{_V1852_HAFTA.get(day, day)} kuni {total_sessions} ta mashg‘ulot; maksimum {max_total}",
            })
        if period_fans and max(period_fans) > max_total:
            violations.append({
                "sinf": class_name,
                "sabab": f"{_V1852_HAFTA.get(day, day)} kuni {max(period_fans)}-dars gigiyenik limitdan tashqari",
            })

        academic_periods = 0
        subject_periods = _v1852_defaultdict(set)
        for period, fans in period_fans.items():
            has_academic = False
            for fan in fans:
                profile = _v1874_subject_profile(fan, grade)
                if profile["academic"]:
                    has_academic = True
                    subject_periods[profile["key"]].add(period)
                if 1 <= grade <= 4 and period == 5 and profile["academic"] and not profile["primary_light"]:
                    violations.append({
                        "sinf": class_name,
                        "sabab": f"{_V1852_HAFTA.get(day, day)} 5-darsda og‘ir fan: {fan}",
                    })
            if has_academic:
                academic_periods += 1
        if academic_periods >= 5 and 1 <= grade <= 4:
            fifth_days[class_id].add(day)
        if 1 <= grade <= 4:
            for subject_key, periods in subject_periods.items():
                if len(periods) > 1:
                    violations.append({
                        "sinf": class_name,
                        "sabab": f"{_V1852_HAFTA.get(day, day)} kuni bir fan ikki marta qo‘yilgan: {subject_key}",
                    })

    for class_id, days in fifth_days.items():
        class_name, grade = class_names[class_id]
        limit = _v1874_fifth_day_limit(grade)
        if len(days) > limit:
            violations.append({
                "sinf": class_name,
                "sabab": f"5 akademik darsli kunlar {len(days)} ta; maksimum {limit}",
            })

    # O‘qituvchining haftalik chegarasi ham tasdiqlash oldidan qayta tekshiriladi.
    cur.execute(
        """SELECT e.oqituvchi_user_id,u.full_name,u.haftalik_dars_soati,
                  COUNT(DISTINCT (e.sinf_id,e.hafta_kuni,e.smena,e.dars_raqami)) AS amaldagi,
                  COUNT(DISTINCT CASE WHEN UPPER(TRIM(e.fan_nomi))='SINF SOATI'
                       THEN (e.sinf_id,e.hafta_kuni,e.smena,e.dars_raqami) END) AS sinf_soati
           FROM aqlli_jadval_slotlari_v2 e
           JOIN users u ON u.user_id=e.oqituvchi_user_id
           WHERE e.maktab_id=%s AND e.urinish_id=%s AND e.oqituvchi_user_id IS NOT NULL
           GROUP BY e.oqituvchi_user_id,u.full_name,u.haftalik_dars_soati""",
        (maktab_id, run_id),
    )
    for row in cur.fetchall():
        if row.get("haftalik_dars_soati") is None:
            continue
        cap = round(
            float(row["haftalik_dars_soati"])
            + int(row.get("sinf_soati") or 0),
            1,
        )
        actual = int(row.get("amaldagi") or 0)
        if actual > cap:
            violations.append({
                "sinf": row["full_name"],
                "sabab": f"o‘qituvchi yuklamasi {actual} soat, ruxsat etilgan {cap} soatdan oshgan",
            })

    unique = []
    seen = set()
    for item in violations:
        key = (item["sinf"], item["sabab"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

# ========================= V18.74 END =========================

# ═══════════════════════════════════════════════════════════
# V18.75 — SHABLON → REJA → DRAFT → TASDIQ 100% MOSLIK
# O'qituvchi haftalik jami, o'qituvchi kun/vaqt cheklovi,
# sinf haftalik jami, fan haftalik soati va haqiqiy jadval bir xil bo'lmasa
# tasdiqlash mutlaqo rad etiladi.
# ═══════════════════════════════════════════════════════════


def _v1875_tables(cur):
    _v1852_tables(cur)
    cur.execute(
        "ALTER TABLE aqlli_sinf_fan_yuklamalari_v2 "
        "ADD COLUMN IF NOT EXISTS manba TEXT NOT NULL DEFAULT 'qolda'"
    )
    cur.execute(
        "ALTER TABLE aqlli_sinf_fan_yuklamalari_v2 "
        "ADD COLUMN IF NOT EXISTS manba_hash TEXT"
    )
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_jadval_manba_holati_v2(
        maktab_id INTEGER PRIMARY KEY REFERENCES maktablar(id) ON DELETE CASCADE,
        manba_hash TEXT NOT NULL,
        sabab TEXT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")


def _v1875_subject_key(value):
    if "_v1874_subject_key" in globals():
        return _v1874_subject_key(value)
    return _xodim_excel_sarlavha_kaliti(value)


def _v1875_group_key(value):
    key = str(value or "whole").strip()
    if key.casefold() in {"", "whole", "butun sinf", "butun_sinf"}:
        return "whole"
    return key


def _v1875_exact_assignment_model(cur, maktab_id: int):
    _xodim_sinf_birikmalari_jadvali(cur)
    cur.execute("""SELECT b.id,b.sinf_id,b.user_id,b.fan_nomi,b.guruh_kaliti,
                          b.haftalik_soat,b.kunlik_max,b.manba,
                          u.full_name,s.sinf,s.harf,COALESCE(s.smena,1) AS smena
                   FROM maktab_dars_birikmalari b
                   JOIN users u ON u.user_id=b.user_id
                   JOIN maktab_sinflari s ON s.id=b.sinf_id
                   WHERE b.maktab_id=%s
                   ORDER BY s.sinf::int,s.harf,b.fan_nomi,b.guruh_kaliti,u.full_name""",
                (maktab_id,))
    rows = [dict(row) for row in cur.fetchall()]
    pairs = {}
    errors = []
    warnings = []

    for row in rows:
        subject = re.sub(r"\s+", " ", str(row.get("fan_nomi") or "")).strip()
        subject_key = _v1875_subject_key(subject)
        group_key = _v1875_group_key(row.get("guruh_kaliti"))
        try:
            hours = float(row.get("haftalik_soat") or 0)
        except (TypeError, ValueError):
            hours = 0
        try:
            daily_max = int(row.get("kunlik_max") or 1)
        except (TypeError, ValueError):
            daily_max = 1
        class_label = f"{row.get('sinf','')}-{row.get('harf','')}"
        if not subject_key:
            errors.append(f"{class_label}: fan nomi bo'sh")
            continue
        if hours <= 0:
            errors.append(
                f"{class_label} / {subject} / {row.get('full_name')}: haftalik soat 0 yoki bo'sh"
            )
        if daily_max < 1 or daily_max > 4:
            errors.append(f"{class_label} / {subject}: kunlik max 1–4 bo'lishi kerak")
        key = (int(row["sinf_id"]), subject_key)
        pair = pairs.setdefault(key, {
            "sinf_id": int(row["sinf_id"]),
            "sinf": class_label,
            "smena": int(row.get("smena") or 1),
            "fan_nomi": subject,
            "fan_kaliti": subject_key,
            "rows": [],
        })
        pair["rows"].append({
            **row,
            "fan_nomi": subject,
            "fan_kaliti": subject_key,
            "guruh_kaliti": group_key,
            "haftalik_soat": hours,
            "kunlik_max": daily_max,
            "user_id": int(row["user_id"]),
        })

    teacher_hours = _v1852_Counter()
    class_hours = _v1852_Counter()
    valid_pairs = {}

    for key, pair in pairs.items():
        whole = [row for row in pair["rows"] if row["guruh_kaliti"] == "whole"]
        groups = [row for row in pair["rows"] if row["guruh_kaliti"] != "whole"]
        if whole and groups:
            errors.append(
                f"{pair['sinf']} / {pair['fan_nomi']}: butun sinf va guruh qatorlari birga yozilgan"
            )
            continue

        if whole:
            if len(whole) != 1:
                errors.append(
                    f"{pair['sinf']} / {pair['fan_nomi']}: butun sinf uchun takror qatorlar bor"
                )
                continue
            teachers = sorted({row["user_id"] for row in whole})
            hours_set = sorted({row["haftalik_soat"] for row in whole if row["haftalik_soat"] > 0})
            daily_set = sorted({row["kunlik_max"] for row in whole})
            if len(teachers) != 1:
                names = ", ".join(sorted({str(row.get("full_name") or row["user_id"]) for row in whole}))
                errors.append(
                    f"{pair['sinf']} / {pair['fan_nomi']}: butun sinf uchun bitta o'qituvchi kerak ({names})"
                )
                continue
            if len(hours_set) != 1:
                errors.append(
                    f"{pair['sinf']} / {pair['fan_nomi']}: o'qituvchi qatorlaridagi haftalik soatlar bir xil emas"
                )
                continue
            if len(daily_set) > 1:
                errors.append(
                    f"{pair['sinf']} / {pair['fan_nomi']}: kunlik maksimumlar bir xil emas"
                )
                continue
            hours = hours_set[0] if hours_set else 0
            teacher_id = teachers[0]
            pair.update({
                "turi": "whole",
                "haftalik_soat": hours,
                "kunlik_max": daily_set[0] if daily_set else 1,
                "asosiy_oqituvchi_user_id": teacher_id,
                "guruhlar": [],
                "oqituvchilar": [teacher_id],
            })
            teacher_hours[teacher_id] += hours
        else:
            by_group = {}
            for row in groups:
                by_group.setdefault(row["guruh_kaliti"], []).append(row)
            group_payload = []
            hours_set = set()
            daily_set = set()
            used_teachers = set()
            group_error = False
            for group_key, group_rows in sorted(by_group.items()):
                if len(group_rows) != 1:
                    errors.append(
                        f"{pair['sinf']} / {pair['fan_nomi']} / {group_key}: takror qatorlar bor"
                    )
                    group_error = True
                    continue
                group_teachers = sorted({row["user_id"] for row in group_rows})
                group_hours = sorted({row["haftalik_soat"] for row in group_rows if row["haftalik_soat"] > 0})
                group_daily = sorted({row["kunlik_max"] for row in group_rows})
                if len(group_teachers) != 1:
                    errors.append(
                        f"{pair['sinf']} / {pair['fan_nomi']} / {group_key}: bitta o'qituvchi kerak"
                    )
                    group_error = True
                    continue
                if len(group_hours) != 1:
                    errors.append(
                        f"{pair['sinf']} / {pair['fan_nomi']} / {group_key}: haftalik soat yagona emas"
                    )
                    group_error = True
                    continue
                teacher_id = group_teachers[0]
                if teacher_id in used_teachers:
                    errors.append(
                        f"{pair['sinf']} / {pair['fan_nomi']}: bir o'qituvchi ikki parallel guruhga biriktirilgan"
                    )
                    group_error = True
                used_teachers.add(teacher_id)
                hours = group_hours[0]
                hours_set.add(hours)
                daily_set.update(group_daily)
                group_payload.append({
                    "guruh_kaliti": group_key,
                    "oqituvchi_user_id": teacher_id,
                    "haftalik_soat": hours,
                    "kunlik_max": group_daily[0] if group_daily else 1,
                    "full_name": group_rows[0].get("full_name"),
                })
            if group_error:
                continue
            if len(hours_set) != 1:
                errors.append(
                    f"{pair['sinf']} / {pair['fan_nomi']}: parallel guruhlarning haftalik soati teng bo'lishi kerak"
                )
                continue
            if len(daily_set) > 1:
                errors.append(
                    f"{pair['sinf']} / {pair['fan_nomi']}: parallel guruhlarning kunlik maksimumi teng bo'lishi kerak"
                )
                continue
            if len(group_payload) < 2:
                warnings.append(
                    f"{pair['sinf']} / {pair['fan_nomi']}: guruhli fan uchun faqat {len(group_payload)} ta guruh topildi"
                )
            hours = next(iter(hours_set), 0)
            pair.update({
                "turi": "group",
                "haftalik_soat": hours,
                "kunlik_max": next(iter(daily_set), 1),
                "asosiy_oqituvchi_user_id": None,
                "guruhlar": group_payload,
                "oqituvchilar": [row["oqituvchi_user_id"] for row in group_payload],
            })
            for group in group_payload:
                teacher_hours[group["oqituvchi_user_id"]] += hours

        class_hours[pair["sinf_id"]] += float(pair.get("haftalik_soat") or 0)
        valid_pairs[key] = pair

    return {
        "rows": rows,
        "pairs": valid_pairs,
        "teacher_hours": dict(teacher_hours),
        "class_hours": dict(class_hours),
        "xatolar": list(dict.fromkeys(errors)),
        "ogohlantirishlar": list(dict.fromkeys(warnings)),
    }


def _v1875_source_fingerprint(cur, maktab_id: int):
    queries = [
        ("birikmalar", """SELECT b.sinf_id,b.user_id,b.fan_nomi,b.guruh_kaliti,
                                  b.haftalik_soat,b.kunlik_max
                           FROM maktab_dars_birikmalari b
                           WHERE b.maktab_id=%s
                           ORDER BY b.sinf_id,b.fan_nomi,b.guruh_kaliti,b.user_id"""),
        ("yuklamalar", """SELECT sinf_id,fan_nomi,haftalik_soat,kunlik_max,
                                  ketma_ket_mumkin,afzal_oxirgi_dars,
                                  asosiy_oqituvchi_user_id,xona_id,ogirlik
                           FROM aqlli_sinf_fan_yuklamalari_v2
                           WHERE maktab_id=%s AND haftalik_soat>0
                           ORDER BY sinf_id,fan_nomi"""),
        ("vaqtlar", """SELECT user_id,hafta_kuni,smena,dars_raqami,turi,qattiq
                        FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s
                        ORDER BY user_id,hafta_kuni,smena,dars_raqami,turi"""),
        ("qoidalar", """SELECT user_id,kunlik_max,ketma_ket_max,okno_max,
                                  afzal_smena,eng_erta_dars,eng_kech_dars
                           FROM aqlli_oqituvchi_qoidalari_v2 WHERE maktab_id=%s
                           ORDER BY user_id"""),
        ("smenalar", """SELECT smena,dars_soni,boshlanish_vaqti,dars_daqiqa,
                                  tanaffus_daqiqa,katta_tanaffus_darsdan_keyin,
                                  katta_tanaffus_daqiqa
                           FROM aqlli_smena_sozlamalari_v2 WHERE maktab_id=%s
                           ORDER BY smena"""),
        ("sinf_kun", """SELECT sinf_daraja,sinf_id,hafta_kuni,faol
                           FROM aqlli_sinf_kun_bloklari_v2 WHERE maktab_id=%s
                           ORDER BY id"""),
        ("sinf_soati", """SELECT sinf_id,hafta_kuni,dars_raqami,faol
                             FROM aqlli_sinf_soati_qoidalari_v2 WHERE maktab_id=%s
                             ORDER BY sinf_id"""),
    ]
    payload = {}
    for name, query in queries:
        cur.execute(query, (maktab_id,))
        payload[name] = [dict(row) for row in cur.fetchall()]
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _v1875_rebuild_schedule_sources(cur, maktab_id: int, cancel_drafts=True, reason="sync"):
    _v1875_tables(cur)
    model = _v1875_exact_assignment_model(cur, maktab_id)
    if model["xatolar"]:
        return model

    # Old pedagogik sozlamalarni fan nomi normallashgan kalit bilan saqlab qolamiz.
    cur.execute("SELECT * FROM aqlli_sinf_fan_yuklamalari_v2 WHERE maktab_id=%s", (maktab_id,))
    old_loads = [dict(row) for row in cur.fetchall()]
    old_map = {}
    for row in old_loads:
        old_map.setdefault(
            (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"])), []
        ).append(row)

    cur.execute("SELECT * FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s", (maktab_id,))
    old_groups = {
        (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"]), str(row["guruh_kaliti"])): dict(row)
        for row in cur.fetchall()
    }

    # FK sabab yuklama qatorlarini o'chirmaymiz: eskilarni 0/eskirgan qilamiz.
    cur.execute("""UPDATE aqlli_sinf_fan_yuklamalari_v2
                   SET haftalik_soat=0,manba='eskirgan'
                   WHERE maktab_id=%s""", (maktab_id,))
    cur.execute("DELETE FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s", (maktab_id,))

    synced_pairs = []
    for key, pair in sorted(model["pairs"].items(), key=lambda item: (item[0][0], item[1]["fan_nomi"].casefold())):
        # Generator fan nomini oddiy casefold bilan bog'laydi. Shu sabab barcha exact
        # assignment qatorlarini bitta kanonik fan nomiga keltiramiz.
        for source_row in pair.get("rows", []):
            cur.execute(
                """UPDATE maktab_dars_birikmalari
                   SET fan_nomi=%s,guruh_kaliti=%s
                   WHERE id=%s""",
                (pair["fan_nomi"], source_row["guruh_kaliti"], source_row["id"]),
            )
        existing_candidates = old_map.get(key, [])
        existing = existing_candidates[0] if existing_candidates else {}
        fan_nomi = pair["fan_nomi"]
        defaults = {
            "ketma_ket_mumkin": bool(existing.get("ketma_ket_mumkin", False)),
            "afzal_oxirgi_dars": int(existing.get("afzal_oxirgi_dars") or 5),
            "xona_id": existing.get("xona_id"),
            "nazorat_soni": int(existing.get("nazorat_soni") or 0),
            "nazoratdan_keyin_tahlil": bool(existing.get("nazoratdan_keyin_tahlil", True)),
            "mustahkamlash_soni": int(existing.get("mustahkamlash_soni") or 0),
            "ogirlik": int(existing.get("ogirlik") or 2),
        }
        cur.execute("""INSERT INTO aqlli_sinf_fan_yuklamalari_v2(
                        maktab_id,sinf_id,fan_nomi,haftalik_soat,kunlik_max,
                        ketma_ket_mumkin,afzal_oxirgi_dars,
                        asosiy_oqituvchi_user_id,xona_id,nazorat_soni,
                        nazoratdan_keyin_tahlil,mustahkamlash_soni,ogirlik,
                        manba)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'DARS_BIRIKMALARI')
                       ON CONFLICT(maktab_id,sinf_id,fan_nomi) DO UPDATE SET
                         haftalik_soat=EXCLUDED.haftalik_soat,
                         kunlik_max=EXCLUDED.kunlik_max,
                         ketma_ket_mumkin=EXCLUDED.ketma_ket_mumkin,
                         afzal_oxirgi_dars=EXCLUDED.afzal_oxirgi_dars,
                         asosiy_oqituvchi_user_id=EXCLUDED.asosiy_oqituvchi_user_id,
                         xona_id=EXCLUDED.xona_id,
                         nazorat_soni=EXCLUDED.nazorat_soni,
                         nazoratdan_keyin_tahlil=EXCLUDED.nazoratdan_keyin_tahlil,
                         mustahkamlash_soni=EXCLUDED.mustahkamlash_soni,
                         ogirlik=EXCLUDED.ogirlik,
                         manba='DARS_BIRIKMALARI'""",
                    (
                        maktab_id, pair["sinf_id"], fan_nomi,
                        pair["haftalik_soat"], pair["kunlik_max"],
                        defaults["ketma_ket_mumkin"], defaults["afzal_oxirgi_dars"],
                        pair.get("asosiy_oqituvchi_user_id"), defaults["xona_id"],
                        defaults["nazorat_soni"], defaults["nazoratdan_keyin_tahlil"],
                        defaults["mustahkamlash_soni"], defaults["ogirlik"],
                    ))
        if pair["turi"] == "group":
            for group in pair["guruhlar"]:
                old = old_groups.get((pair["sinf_id"], pair["fan_kaliti"], group["guruh_kaliti"]), {})
                cur.execute("""INSERT INTO aqlli_guruh_sozlamalari_v2(
                                maktab_id,sinf_id,fan_nomi,guruh_kaliti,
                                oqituvchi_user_id,xona_id)
                               VALUES(%s,%s,%s,%s,%s,%s)
                               ON CONFLICT(maktab_id,sinf_id,fan_nomi,guruh_kaliti)
                               DO UPDATE SET oqituvchi_user_id=EXCLUDED.oqituvchi_user_id,
                                             xona_id=EXCLUDED.xona_id""",
                            (maktab_id, pair["sinf_id"], fan_nomi,
                             group["guruh_kaliti"], group["oqituvchi_user_id"],
                             old.get("xona_id")))
        synced_pairs.append({
            "sinf_id": pair["sinf_id"], "sinf": pair["sinf"],
            "fan": fan_nomi, "haftalik_soat": pair["haftalik_soat"],
            "turi": pair["turi"], "oqituvchilar": pair["oqituvchilar"],
        })

    # O'qituvchining shablondagi jami — exact birikmalar yig'indisi.
    cur.execute("""UPDATE users SET haftalik_dars_soati=0
                   WHERE maktab_id=%s AND lavozim='fan_oqituvchisi'""", (maktab_id,))
    for teacher_id, hours in model["teacher_hours"].items():
        cur.execute("UPDATE users SET haftalik_dars_soati=%s WHERE maktab_id=%s AND user_id=%s",
                    (round(float(hours), 1), maktab_id, int(teacher_id)))

    if cancel_drafts:
        cur.execute("""UPDATE aqlli_jadval_urinishlari_v2
                       SET holat='bekor'
                       WHERE maktab_id=%s AND holat='draft'""", (maktab_id,))

    source_hash = _v1875_source_fingerprint(cur, maktab_id)
    cur.execute("""INSERT INTO aqlli_jadval_manba_holati_v2(
                    maktab_id,manba_hash,sabab,yangilangan_at)
                   VALUES(%s,%s,%s,NOW())
                   ON CONFLICT(maktab_id) DO UPDATE SET
                     manba_hash=EXCLUDED.manba_hash,
                     sabab=EXCLUDED.sabab,
                     yangilangan_at=NOW()""",
                (maktab_id, source_hash, reason))

    return {
        "tayyor": True,
        "manba_hash": source_hash,
        "fan_sinf_soni": len(synced_pairs),
        "oqituvchi_soni": len(model["teacher_hours"]),
        "sinflar": dict(model["class_hours"]),
        "oqituvchilar": dict(model["teacher_hours"]),
        "xatolar": [],
        "ogohlantirishlar": model["ogohlantirishlar"],
        "yuklamalar": synced_pairs[:300],
    }


def _v1875_preflight_report(cur, maktab_id: int):
    _v1875_tables(cur)
    model = _v1875_exact_assignment_model(cur, maktab_id)
    errors = list(model["xatolar"])
    warnings = list(model["ogohlantirishlar"])

    year = _v1890_generation_year(cur, maktab_id)
    weekdays = int(year.get("hafta_kunlari") or 6)
    _v1852_default_shifts(cur, maktab_id)
    cur.execute("SELECT * FROM aqlli_smena_sozlamalari_v2 WHERE maktab_id=%s", (maktab_id,))
    shifts = {int(row["smena"]): dict(row) for row in cur.fetchall()}
    cur.execute("""SELECT id,sinf,harf,COALESCE(smena,1) AS smena,rahbar_user_id
                   FROM maktab_sinflari WHERE maktab_id=%s ORDER BY sinf::int,harf""",
                (maktab_id,))
    classes = {int(row["id"]): dict(row) for row in cur.fetchall()}
    cur.execute("SELECT * FROM aqlli_sinf_fan_yuklamalari_v2 WHERE maktab_id=%s AND haftalik_soat>0",
                (maktab_id,))
    loads = [dict(row) for row in cur.fetchall()]
    load_map = {(int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"])): row for row in loads}

    for key, pair in model["pairs"].items():
        load = load_map.get(key)
        if not load:
            errors.append(f"{pair['sinf']} / {pair['fan_nomi']}: Aqlli jadval yuklamasi yaratilmagan")
            continue
        if abs(float(load.get("haftalik_soat") or 0) - float(pair.get("haftalik_soat") or 0)) > 1e-9:
            errors.append(
                f"{pair['sinf']} / {pair['fan_nomi']}: shablon {pair['haftalik_soat']} soat, "
                f"jadval manbasi {load.get('haftalik_soat')} soat"
            )

    for key, load in load_map.items():
        if key not in model["pairs"]:
            errors.append(
                f"{classes.get(key[0], {}).get('sinf','')}-{classes.get(key[0], {}).get('harf','')} / "
                f"{load['fan_nomi']}: shablonda aniq o'qituvchi birikmasi yo'q"
            )

    class_day_blocks = _v1856_class_day_rule_map(_v1856_class_day_rule_rows(cur, maktab_id))
    class_hour_rules = _v1866_class_hour_rule_rows(cur, maktab_id)
    class_hour_by_class = {int(row["sinf_id"]): row for row in class_hour_rules}
    class_hour_by_teacher = _v1852_Counter()
    for row in class_hour_rules:
        if row.get("rahbar_user_id") is not None:
            class_hour_by_teacher[int(row["rahbar_user_id"])] += int(row.get("haftalik_soat") or 1)

    if not model["pairs"]:
        errors.append("DARS_BIRIKMALARI varag'idan birorta ham aniq sinf–fan–soat topilmadi")

    class_summary = []
    for class_id, cls in classes.items():
        grade = _v1874_grade(cls)
        shift = int(cls.get("smena") or 1)
        shift_periods = int(shifts.get(shift, {}).get("dars_soni") or 0)
        allowed_days = []
        for day in range(1, weekdays + 1):
            if not _v1856_class_day_block_reason(cls, day, class_day_blocks):
                allowed_days.append(day)
        fan_hours = float(model["class_hours"].get(class_id, 0))
        class_hour_rule = class_hour_by_class.get(class_id, {})
        class_hour = int(class_hour_rule.get("haftalik_soat") or 0) if cls.get("rahbar_user_id") is not None else 0
        if class_hour_rule and cls.get("rahbar_user_id") is None:
            warnings.append(
                f"{cls['sinf']}-{cls['harf']}: sinf rahbari belgilanmagani uchun KELAJAK SOATI vaqtincha jadvalga kiritilmaydi"
            )
        if 1 <= grade <= 4:
            base_per_day = min(4, shift_periods)
            fifth_extra = min(_v1874_fifth_day_limit(grade), len(allowed_days)) if shift_periods >= 5 else 0
            academic_capacity = base_per_day * len(allowed_days) + fifth_extra
            # Sinf soati akademik fan emas, lekin jadval katagini egallaydi.
            # U 4 akademik darsli kunga qo'yilsa umumiy sessiya sig'imi bittaga oshadi.
            capacity = academic_capacity + class_hour
        else:
            academic_capacity = min(6, shift_periods) * len(allowed_days)
            capacity = academic_capacity + class_hour
        planned = fan_hours + class_hour
        if fan_hours <= 0:
            errors.append(f"{cls['sinf']}-{cls['harf']}: haftalik fan soatlari kiritilmagan")
        if shift not in shifts:
            errors.append(f"{cls['sinf']}-{cls['harf']}: {shift}-smena sozlanmagan")
        if fan_hours > academic_capacity:
            errors.append(
                f"{cls['sinf']}-{cls['harf']}: fanlar rejasi {fan_hours} soat, akademik sig'im {academic_capacity} soat"
            )
        if planned > capacity:
            errors.append(
                f"{cls['sinf']}-{cls['harf']}: fanlar+sinf soati {planned} ta sessiya, mavjud sig'im {capacity} ta"
            )
        weekly_max = _v1874_weekly_max(grade)
        if weekly_max is not None and fan_hours > weekly_max:
            errors.append(
                f"{cls['sinf']}-{cls['harf']}: fanlar rejasi {fan_hours} soat, me'yoriy maksimum {weekly_max} soat"
            )
        rule = class_hour_by_class.get(class_id)
        if rule:
            if rule.get("rahbar_user_id") is None:
                warnings.append(f"{cls['sinf']}-{cls['harf']}: KELAJAK SOATI rahbar tanlanguncha jadvalga qo'yilmadi")
            blocked = _v1856_class_day_block_reason(cls, int(rule["hafta_kuni"]), class_day_blocks)
            if blocked:
                errors.append(f"{cls['sinf']}-{cls['harf']} sinf soati: {blocked}")
            if int(rule["dars_raqami"]) > min(shift_periods, _v1874_max_total_periods(grade)):
                errors.append(
                    f"{cls['sinf']}-{cls['harf']} sinf soati: {rule['dars_raqami']}-dars sinf limitidan tashqari"
                )
        class_summary.append({
            "sinf_id": class_id, "sinf": f"{cls['sinf']}-{cls['harf']}",
            "smena": shift, "fan_soati": fan_hours, "sinf_soati": class_hour,
            "reja_jami": planned, "sigim": capacity,
            "farq": capacity - planned, "oqish_kunlari": len(allowed_days),
            "mos": planned <= capacity,
        })

    for key, pair in model["pairs"].items():
        cls = classes.get(pair["sinf_id"], {})
        grade = _v1874_grade(cls)
        allowed_days = sum(
            1 for day in range(1, weekdays + 1)
            if not _v1856_class_day_block_reason(cls, day, class_day_blocks)
        )
        daily_max = 1 if 1 <= grade <= 4 else int(pair.get("kunlik_max") or 1)
        if float(pair.get("haftalik_soat") or 0) > allowed_days * daily_max:
            errors.append(
                f"{pair['sinf']} / {pair['fan_nomi']}: {pair['haftalik_soat']} soatni "
                f"{allowed_days} kunga kunlik max {daily_max} bilan joylab bo'lmaydi"
            )

    cur.execute("SELECT * FROM aqlli_oqituvchi_qoidalari_v2 WHERE maktab_id=%s", (maktab_id,))
    rules = _v1852_teacher_rules_map(cur.fetchall())
    cur.execute("SELECT * FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s", (maktab_id,))
    hard, soft, method_hard, method_soft = _v1852_availability_maps(cur.fetchall())
    cur.execute("SELECT user_id,full_name,haftalik_dars_soati FROM users WHERE maktab_id=%s", (maktab_id,))
    teacher_rows = {int(row["user_id"]): dict(row) for row in cur.fetchall()}

    teacher_shifts = _v1852_defaultdict(set)
    for pair in model["pairs"].values():
        for teacher_id in pair.get("oqituvchilar", []):
            teacher_shifts[int(teacher_id)].add(int(pair.get("smena") or 1))

    teacher_summary = []
    all_teacher_ids = sorted(set(model["teacher_hours"]) | set(class_hour_by_teacher))
    default_rules = {"kunlik_max": 6, "ketma_ket_max": 4, "okno_max": 1,
                     "afzal_smena": 0, "eng_erta_dars": 1, "eng_kech_dars": 12}
    for teacher_id in all_teacher_ids:
        row = teacher_rows.get(int(teacher_id), {"full_name": str(teacher_id)})
        base_plan = float(model["teacher_hours"].get(int(teacher_id), 0))
        class_hours = int(class_hour_by_teacher.get(int(teacher_id), 0))
        total_plan = base_plan + class_hours
        saved_base = row.get("haftalik_dars_soati")
        if saved_base is None or abs(float(saved_base) - base_plan) > 1e-9:
            errors.append(
                f"{row.get('full_name')}: shablon fan yuklamasi {base_plan} soat, xodim kartasida {saved_base if saved_base is not None else 'bo\'sh'}"
            )
        teacher_rules = rules.get(int(teacher_id), default_rules)
        shifts_used = teacher_shifts.get(int(teacher_id), set()) or set(shifts.keys())
        capacity = 0
        for day in range(1, weekdays + 1):
            if (int(teacher_id), day) in method_hard:
                continue
            open_slots = 0
            for shift in shifts_used:
                count = int(shifts.get(int(shift), {}).get("dars_soni") or 0)
                for period in range(1, count + 1):
                    if period < teacher_rules["eng_erta_dars"] or period > teacher_rules["eng_kech_dars"]:
                        continue
                    if _v1852_blocked(hard, int(teacher_id), day, int(shift), period):
                        continue
                    open_slots += 1
            capacity += min(open_slots, int(teacher_rules["kunlik_max"]))
        if total_plan > capacity:
            errors.append(
                f"{row.get('full_name')}: haftalik reja {total_plan} soat, qattiq bo'sh vaqtlar bo'yicha sig'im {capacity} soat"
            )
        teacher_summary.append({
            "user_id": int(teacher_id), "full_name": row.get("full_name"),
            "fan_yuklama": base_plan, "sinf_soati": class_hours,
            "reja_jami": total_plan, "saqlangan_yuklama": saved_base,
            "qattiq_sigim": capacity, "farq": capacity - total_plan,
            "mos": total_plan <= capacity and saved_base is not None and abs(float(saved_base) - base_plan) <= 1e-9,
        })

    fan_summary = [
        {"sinf_id": pair["sinf_id"], "sinf": pair["sinf"],
         "fan": pair["fan_nomi"], "haftalik_soat": pair["haftalik_soat"],
         "kunlik_max": pair["kunlik_max"], "turi": pair["turi"],
         "oqituvchi_soni": len(pair.get("oqituvchilar", []))}
        for pair in model["pairs"].values()
    ]

    source_hash = _v1875_source_fingerprint(cur, maktab_id)
    unique_errors = list(dict.fromkeys(errors))
    unique_warnings = list(dict.fromkeys(warnings))
    return {
        "tayyor": not unique_errors,
        "manba_hash": source_hash,
        "xatolar": unique_errors[:300],
        "ogohlantirishlar": unique_warnings[:300],
        "sinflar": class_summary,
        "oqituvchilar": teacher_summary,
        "fanlar": fan_summary,
        "xulosa": {
            "sinf_soni": len(class_summary),
            "oqituvchi_soni": len(teacher_summary),
            "fan_sinf_soni": len(fan_summary),
            "xato_soni": len(unique_errors),
        },
    }


def _v1875_schedule_integrity_report(cur, maktab_id: int, run_id: int):
    _v1875_tables(cur)
    model = _v1875_exact_assignment_model(cur, maktab_id)
    errors = list(model["xatolar"])
    warnings = list(model["ogohlantirishlar"])
    cur.execute("SELECT * FROM aqlli_jadval_urinishlari_v2 WHERE id=%s AND maktab_id=%s",
                (run_id, maktab_id))
    run = cur.fetchone()
    if not run:
        return {"tayyor": False, "xatolar": ["Draft topilmadi"],
                "ogohlantirishlar": [], "sinflar": [], "oqituvchilar": [], "fanlar": []}

    settings = run.get("sozlamalar") or {}
    current_hash = _v1875_source_fingerprint(cur, maktab_id)
    stored_hash = settings.get("manba_hash") if isinstance(settings, dict) else None
    if stored_hash and stored_hash != current_hash:
        errors.append("Draft yaratilgandan keyin shablon, fan soati yoki vaqt qoidalari o'zgargan — yangi draft kerak")

    cur.execute("""SELECT e.*,s.sinf,s.harf,COALESCE(s.smena,1) AS sinf_smena,
                          u.full_name AS oqituvchi_ismi
                   FROM aqlli_jadval_slotlari_v2 e
                   JOIN maktab_sinflari s ON s.id=e.sinf_id
                   LEFT JOIN users u ON u.user_id=e.oqituvchi_user_id
                   WHERE e.maktab_id=%s AND e.urinish_id=%s
                   ORDER BY e.sinf_id,e.hafta_kuni,e.smena,e.dars_raqami,e.guruh_kaliti""",
                (maktab_id, run_id))
    slots = [dict(row) for row in cur.fetchall()]

    planned_subject = {
        key: float(pair["haftalik_soat"])
        for key, pair in model["pairs"].items()
    }
    scheduled_subject_sessions = _v1852_defaultdict(set)
    class_sessions = _v1852_defaultdict(set)
    class_hour_sessions = _v1852_defaultdict(set)
    teacher_sessions = _v1852_defaultdict(set)
    teacher_class_hour_sessions = _v1852_defaultdict(set)
    pair_occurrence_rows = _v1852_defaultdict(list)
    teacher_slot_map = _v1852_defaultdict(set)
    room_slot_map = _v1852_defaultdict(set)

    cur.execute("SELECT * FROM aqlli_oqituvchi_qoidalari_v2 WHERE maktab_id=%s", (maktab_id,))
    teacher_rules = _v1852_teacher_rules_map(cur.fetchall())
    cur.execute("SELECT * FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s", (maktab_id,))
    hard, soft, method_hard, method_soft = _v1852_availability_maps(cur.fetchall())
    class_day_blocks = _v1856_class_day_rule_map(_v1856_class_day_rule_rows(cur, maktab_id))
    cur.execute("SELECT id,sinf,harf,COALESCE(smena,1) AS smena FROM maktab_sinflari WHERE maktab_id=%s", (maktab_id,))
    classes = {int(row["id"]): dict(row) for row in cur.fetchall()}
    cur.execute("SELECT * FROM aqlli_sinf_fan_yuklamalari_v2 WHERE maktab_id=%s AND haftalik_soat>0", (maktab_id,))
    loads = {(int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"])): dict(row) for row in cur.fetchall()}

    for slot in slots:
        class_id = int(slot["sinf_id"])
        day = int(slot["hafta_kuni"])
        shift = int(slot["smena"])
        period = int(slot["dars_raqami"])
        week_type = str(slot.get("hafta_turi") or "har_hafta")
        subject = str(slot.get("fan_nomi") or "").strip()
        subject_key = _v1875_subject_key(subject)
        session = (day, shift, period)
        class_sessions[class_id].add(session)
        if subject_key == _v1875_subject_key("SINF SOATI"):
            class_hour_sessions[class_id].add((*session, week_type))
        else:
            pair_key = (class_id, subject_key)
            scheduled_subject_sessions[pair_key].add((*session, week_type))
            pair_occurrence_rows[(pair_key, int(slot.get("takror_raqami") or 1))].append(slot)
            pair = model["pairs"].get(pair_key)
            if not pair:
                errors.append(f"{classes.get(class_id, {}).get('sinf','')}-{classes.get(class_id, {}).get('harf','')} / {subject}: reja manbasida yo'q dars")
            else:
                group_key = _v1875_group_key(slot.get("guruh_kaliti"))
                expected_teacher = None
                if pair["turi"] == "whole":
                    expected_teacher = pair.get("asosiy_oqituvchi_user_id")
                    if group_key != "whole":
                        errors.append(f"{pair['sinf']} / {pair['fan_nomi']}: butun sinf darsi {group_key} guruh bilan yozilgan")
                else:
                    expected = {g["guruh_kaliti"]: g["oqituvchi_user_id"] for g in pair["guruhlar"]}
                    expected_teacher = expected.get(group_key)
                    if group_key not in expected:
                        errors.append(f"{pair['sinf']} / {pair['fan_nomi']}: kutilmagan guruh {group_key}")
                actual_teacher = slot.get("oqituvchi_user_id")
                if expected_teacher is not None and int(actual_teacher or 0) != int(expected_teacher):
                    errors.append(
                        f"{pair['sinf']} / {pair['fan_nomi']} / {group_key}: reja o'qituvchisi {expected_teacher}, jadvalda {actual_teacher}"
                    )

        teacher_id = slot.get("oqituvchi_user_id")
        if teacher_id is not None:
            teacher_id = int(teacher_id)
            teacher_sessions[teacher_id].add((class_id, day, shift, period, week_type))
            if subject_key == _v1875_subject_key("SINF SOATI"):
                teacher_class_hour_sessions[teacher_id].add(
                    (class_id, day, shift, period, week_type)
                )
            teacher_slot_map[(teacher_id, day, shift, period)].add((class_id, week_type))
            if (teacher_id, day) in method_hard:
                errors.append(f"{slot.get('oqituvchi_ismi')}: {_V1852_HAFTA.get(day, day)} metod kuniga dars qo'yilgan")
            if _v1852_blocked(hard, teacher_id, day, shift, period):
                errors.append(f"{slot.get('oqituvchi_ismi')}: {_V1852_HAFTA.get(day, day)} {shift}-smena {period}-dars qattiq bloklangan")
        room_key = slot.get("xona_id") or slot.get("xona_matni")
        if room_key:
            room_slot_map[(str(room_key), day, shift, period)].add((class_id, week_type))
        cls = classes.get(class_id, {})
        if shift != int(cls.get("smena") or 1):
            errors.append(f"{cls.get('sinf','')}-{cls.get('harf','')}: dars {shift}-smenaga tushgan, sinf smenasi {cls.get('smena')}")
        blocked = _v1856_class_day_block_reason(cls, day, class_day_blocks)
        if blocked:
            errors.append(f"{cls.get('sinf','')}-{cls.get('harf','')}: {blocked}")

    fan_summary = []
    all_pair_keys = set(planned_subject) | set(scheduled_subject_sessions)
    for key in sorted(all_pair_keys, key=lambda x: (x[0], x[1])):
        pair = model["pairs"].get(key)
        planned = float(planned_subject.get(key, 0))
        actual = round(sum(
            0.5 if session[3] in {"toq", "juft"} else 1.0
            for session in scheduled_subject_sessions.get(key, set())
        ), 1)
        class_label = pair["sinf"] if pair else f"sinf_id={key[0]}"
        fan = pair["fan_nomi"] if pair else key[1]
        if planned != actual:
            errors.append(f"{class_label} / {fan}: reja {planned} soat, jadval {actual} soat")
        fan_summary.append({"sinf": class_label, "fan": fan, "reja": planned,
                            "jadval": actual, "farq": actual - planned, "mos": planned == actual})

    for key, pair in model["pairs"].items():
        if pair["turi"] != "group":
            continue
        expected_groups = {g["guruh_kaliti"] for g in pair["guruhlar"]}
        for occurrence in range(1, int(math.ceil(float(pair["haftalik_soat"]))) + 1):
            rows = pair_occurrence_rows.get((key, occurrence), [])
            actual_groups = {_v1875_group_key(row.get("guruh_kaliti")) for row in rows}
            sessions = {(int(row["hafta_kuni"]), int(row["smena"]), int(row["dars_raqami"])) for row in rows}
            if actual_groups != expected_groups or len(sessions) != 1:
                errors.append(
                    f"{pair['sinf']} / {pair['fan_nomi']} / {occurrence}-takror: parallel guruhlar to'liq va bir vaqtda emas"
                )

    class_hour_rules = _v1866_class_hour_rule_rows(cur, maktab_id)
    class_hour_by_teacher = _v1852_Counter()
    for row in class_hour_rules:
        if row.get("rahbar_user_id") is not None:
            class_hour_by_teacher[int(row["rahbar_user_id"])] += int(row.get("haftalik_soat") or 1)
    class_hour_by_class = {int(row["sinf_id"]): row for row in class_hour_rules}
    class_summary = []
    all_class_ids = set(classes) | set(model["class_hours"]) | set(class_sessions)
    for class_id in sorted(all_class_ids):
        cls = classes.get(class_id, {})
        class_pairs = [pair for pair in model["pairs"].values() if int(pair["sinf_id"]) == class_id]
        full_sessions = sum(int(math.floor(float(pair.get("haftalik_soat") or 0))) for pair in class_pairs)
        half_sessions = sum(
            1 for pair in class_pairs
            if abs(float(pair.get("haftalik_soat") or 0) % 1 - 0.5) < 1e-9
        )
        base_planned = full_sessions + int(math.ceil(half_sessions / 2))
        class_hour_planned = int(class_hour_by_class.get(class_id, {}).get("haftalik_soat") or 0)
        planned = base_planned + class_hour_planned
        actual = len(class_sessions.get(class_id, set()))
        class_hour_actual = round(sum(
            0.5 if session[3] in {"toq", "juft"} else 1.0
            for session in class_hour_sessions.get(class_id, set())
        ), 1)
        subject_actual = round(float(actual) - float(class_hour_actual), 1)
        label = f"{cls.get('sinf','')}-{cls.get('harf','')}"
        if planned != actual:
            errors.append(
                f"{label}: {base_planned} soat fan yuklamasi + "
                f"{class_hour_planned} soat SINF SOATI = {planned} soat reja; "
                f"jadvalda {actual} soat"
            )
        class_summary.append({
            "sinf_id": class_id, "sinf": label,
            "fan_yuklama": base_planned,
            "sinf_soati_reja": class_hour_planned,
            "reja": planned,
            "fan_jadval": subject_actual,
            "sinf_soati_jadval": class_hour_actual,
            "jadval": actual, "farq": actual - planned,
            "mos": planned == actual,
            "tasdiq_matni": (
                f"{base_planned} soat fan yuklamasi + {class_hour_planned} soat "
                f"SINF SOATI = {planned}; jadvalda {actual} soat"
            ),
        })

    cur.execute("SELECT user_id,full_name,haftalik_dars_soati FROM users WHERE maktab_id=%s", (maktab_id,))
    teacher_rows = {int(row["user_id"]): dict(row) for row in cur.fetchall()}
    teacher_summary = []
    all_teacher_ids = set(model["teacher_hours"]) | set(class_hour_by_teacher) | set(teacher_sessions)
    for teacher_id in sorted(all_teacher_ids):
        row = teacher_rows.get(teacher_id, {"full_name": str(teacher_id)})
        base_planned = float(model["teacher_hours"].get(teacher_id, 0))
        class_hour_planned = int(class_hour_by_teacher.get(teacher_id, 0))
        planned = base_planned + class_hour_planned
        actual = round(sum(
            0.5 if session[4] in {"toq", "juft"} else 1.0
            for session in teacher_sessions.get(teacher_id, set())
        ), 1)
        class_hour_actual = round(sum(
            0.5 if session[4] in {"toq", "juft"} else 1.0
            for session in teacher_class_hour_sessions.get(teacher_id, set())
        ), 1)
        subject_actual = round(actual - class_hour_actual, 1)
        if planned != actual:
            errors.append(
                f"{row.get('full_name')}: {base_planned:g} soat fan yuklamasi + "
                f"{class_hour_planned} soat sinf rahbarligi = {planned:g} soat reja; "
                f"jadvalda {actual:g} soat"
            )
        teacher_summary.append({
            "user_id": teacher_id, "full_name": row.get("full_name"),
            "fan_yuklama": base_planned,
            "sinf_soati_reja": class_hour_planned,
            "reja": planned,
            "fan_jadval": subject_actual,
            "sinf_soati_jadval": class_hour_actual,
            "jadval": actual,
            "farq": actual - planned, "mos": planned == actual,
            "tasdiq_matni": (
                f"{base_planned:g} soat fan yuklamasi + {class_hour_planned} soat "
                f"sinf rahbarligi = {planned:g}; jadvalda {actual:g} soat"
            ),
        })

    for (teacher_id, day, shift, period), class_phases in teacher_slot_map.items():
        conflicts = {
            class_id for class_id, phase in class_phases
            if any(
                other_class != class_id
                and (phase == "har_hafta" or other_phase == "har_hafta" or phase == other_phase)
                for other_class, other_phase in class_phases
            )
        }
        if len(conflicts) > 1:
            errors.append(
                f"{teacher_rows.get(teacher_id, {}).get('full_name', teacher_id)}: "
                f"{_V1852_HAFTA.get(day, day)} {shift}-smena {period}-darsda {len(conflicts)} ta sinf"
            )
    for (room, day, shift, period), class_phases in room_slot_map.items():
        conflicts = {
            class_id for class_id, phase in class_phases
            if any(
                other_class != class_id
                and (phase == "har_hafta" or other_phase == "har_hafta" or phase == other_phase)
                for other_class, other_phase in class_phases
            )
        }
        if len(conflicts) > 1:
            errors.append(f"Xona {room}: {_V1852_HAFTA.get(day, day)} {shift}-smena {period}-darsda ikki sinf")

    daily_teacher_counts = _v1852_Counter()
    daily_subject_sessions = _v1852_defaultdict(set)
    for slot in slots:
        teacher_id = slot.get("oqituvchi_user_id")
        if teacher_id is not None:
            weight = 0.5 if str(slot.get("hafta_turi") or "har_hafta") in {"toq", "juft"} else 1.0
            daily_teacher_counts[(int(teacher_id), int(slot["hafta_kuni"]))] += weight
        subject_key = _v1875_subject_key(slot.get("fan_nomi"))
        if subject_key != _v1875_subject_key("SINF SOATI"):
            daily_subject_sessions[(
                int(slot["sinf_id"]), subject_key, int(slot["hafta_kuni"])
            )].add((
                int(slot["smena"]), int(slot["dars_raqami"]),
                str(slot.get("hafta_turi") or "har_hafta"),
            ))
    for (teacher_id, day), count in daily_teacher_counts.items():
        limit = int(teacher_rules.get(teacher_id, {"kunlik_max": 6})["kunlik_max"])
        if count > limit:
            errors.append(f"{teacher_rows.get(teacher_id, {}).get('full_name', teacher_id)}: {_V1852_HAFTA.get(day, day)} {count} dars, kunlik max {limit}")
    for (class_id, subject_key, day), sessions in daily_subject_sessions.items():
        count = sum(0.5 if session[2] in {"toq", "juft"} else 1.0 for session in sessions)
        load = loads.get((class_id, subject_key))
        if load and count > int(load.get("kunlik_max") or 1):
            cls = classes.get(class_id, {})
            errors.append(f"{cls.get('sinf','')}-{cls.get('harf','')} / {load['fan_nomi']}: {_V1852_HAFTA.get(day, day)} {count} marta, kunlik max {load.get('kunlik_max')}")

    hygiene = _v1874_schedule_hygiene_violations(cur, maktab_id, run_id)
    for item in hygiene:
        errors.append(f"{item['sinf']}: {item['sabab']}")
    for item in _v1856_schedule_block_violations(cur, maktab_id, run_id):
        errors.append(f"{item['sinf']}-{item['harf']}: {item['kun_nomi']} bloklangan kunda dars bor")
    for item in _v1866_class_hour_violations(cur, maktab_id, run_id):
        errors.append(f"Sinf soati: {item['izoh']}")

    if int(run.get("joylashtirilmadi") or 0) > 0:
        errors.append(f"{int(run.get('joylashtirilmadi') or 0)} ta dars joylashtirilmagan")

    unique_errors = list(dict.fromkeys(errors))
    unique_warnings = list(dict.fromkeys(warnings))
    return {
        "tayyor": not unique_errors,
        "manba_hash": current_hash,
        "xatolar": unique_errors[:500],
        "ogohlantirishlar": unique_warnings[:300],
        "sinflar": class_summary,
        "oqituvchilar": teacher_summary,
        "fanlar": fan_summary,
        "xulosa": {
            "sinf_mos": sum(1 for row in class_summary if row["mos"]),
            "sinf_jami": len(class_summary),
            "oqituvchi_mos": sum(1 for row in teacher_summary if row["mos"]),
            "oqituvchi_jami": len(teacher_summary),
            "fan_mos": sum(1 for row in fan_summary if row["mos"]),
            "fan_jami": len(fan_summary),
            "xato_soni": len(unique_errors),
        },
    }


@app.post("/api/maktab/aqlli_jadval/v2/moslik")
def v1875_schedule_preflight(token: str, maktab_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1875_tables(cur)
        if not _v1852_manager(cur, actor_id, maktab_id):
            raise HTTPException(status_code=403, detail="Moslik tekshiruvini faqat rahbariyat bajaradi")
        _v199_ensure_class_hour_rules(cur, maktab_id, actor_id=actor_id)
        if "_v1876_group_review_report" in globals():
            group_review = _v1876_group_review_report(cur, maktab_id)
            if not group_review.get("tayyor"):
                return {
                    "tayyor": False,
                    "xatolar": group_review.get("xatolar", []),
                    "ogohlantirishlar": group_review.get("ogohlantirishlar", []),
                    "guruh_tasdiqlash": group_review,
                    "sinflar": [], "oqituvchilar": [], "fanlar": [],
                    "xulosa": {
                        "xato_soni": len(group_review.get("xatolar", [])),
                        "guruh_tasdiqlanmagan": group_review.get("xulosa", {}).get("tasdiqlanmagan", 0),
                    },
                }
        sync = _v1875_rebuild_schedule_sources(cur, maktab_id, cancel_drafts=False, reason="moslik_tekshiruvi")
        if sync.get("xatolar"):
            conn.rollback()
            return {"tayyor": False, "xatolar": sync["xatolar"],
                    "ogohlantirishlar": sync.get("ogohlantirishlar", []),
                    "sinflar": [], "oqituvchilar": [], "fanlar": [],
                    "xulosa": {"xato_soni": len(sync["xatolar"])}}
        report = _v1875_preflight_report(cur, maktab_id)
        conn.commit()
        return report
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()

# ========================= V18.75 END =========================


# ═══════════════════════════════════════════════════════════
# V18.76 — GURUHLI FANLARNI JADVALDAN OLDIN TASDIQLASH
# Sinf yaratishda saqlangan guruh tizimlari va Excel DARS_BIRIKMALARI
# bitta hisobotda solishtiriladi. Guruh→o'qituvchi taqsimoti to'liq
# tasdiqlanmaguncha moslik tekshiruvi, draft yaratish va tasdiqlash yopiq.
# ═══════════════════════════════════════════════════════════


def _v1876_tables(cur):
    _v1875_tables(cur)
    _sinf_kop_guruh_jadvallari(cur)
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_fan_guruh_tasdiqlari_v2(
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        fan_nomi TEXT NOT NULL,
        fan_kaliti TEXT NOT NULL,
        turi TEXT NOT NULL DEFAULT 'group' CHECK(turi IN ('whole','group')),
        tizim_id BIGINT REFERENCES maktab_sinf_guruh_tizimlari(id) ON DELETE SET NULL,
        manba_hash TEXT NOT NULL,
        tasdiqlangan BOOLEAN NOT NULL DEFAULT FALSE,
        tasdiqlagan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY(maktab_id,sinf_id,fan_kaliti)
    )""")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_fan_guruh_tasdiq_v2 "
        "ON aqlli_fan_guruh_tasdiqlari_v2(maktab_id,tasdiqlangan)"
    )


@app.on_event("startup")
def _v1876_startup_tables():
    try:
        conn = _db(); cur = conn.cursor()
        _v1876_tables(cur)
        conn.commit(); cur.close(); conn.close()
    except Exception as exc:
        print(f"[V18.76 guruh tasdiq jadvallari] {exc}", flush=True)


def _v1876_seed_legacy_group_systems(cur, maktab_id: int):
    """Eski guruhlash_usuli ustunidagi sozlamani ko'p tizimli jadvalga ko'chiradi."""
    cur.execute("""SELECT id,COALESCE(guruhlash_usuli,'none') AS guruhlash_usuli
                   FROM maktab_sinflari WHERE maktab_id=%s""", (maktab_id,))
    for cls in cur.fetchall():
        kind = str(cls.get("guruhlash_usuli") or "none").strip().lower()
        if kind not in _SINF_GURUH_TIZIM_NOMLARI:
            continue
        cur.execute(
            "SELECT 1 FROM maktab_sinf_guruh_tizimlari "
            "WHERE sinf_id=%s AND faol=TRUE LIMIT 1",
            (cls["id"],),
        )
        if cur.fetchone():
            continue
        cur.execute("""INSERT INTO maktab_sinf_guruh_tizimlari(
                         sinf_id,turi,nomi,fanlar,faol,yangilangan_at)
                       VALUES(%s,%s,%s,ARRAY[]::TEXT[],TRUE,NOW())
                       ON CONFLICT(sinf_id,turi) DO UPDATE SET
                         nomi=EXCLUDED.nomi,faol=TRUE,yangilangan_at=NOW()""",
                    (cls["id"], kind, _SINF_GURUH_TIZIM_NOMLARI[kind]))


def _v1876_system_group_rows(cur, system):
    kind = str(system.get("turi") or "")
    if kind == "alphabet":
        guruh_soni = _sinf_guruh_soni_normalizatsiya("alphabet", system.get("guruh_soni"))
        return [
            {"guruh_kaliti": f"group_{raqam}", "guruh_nomi": f"{raqam}-guruh", "oquvchi_soni": 0}
            for raqam in range(1, guruh_soni + 1)
        ]
    if kind == "gender":
        return [
            {"guruh_kaliti": "boys", "guruh_nomi": "O'g'il bolalar", "oquvchi_soni": 0},
            {"guruh_kaliti": "girls", "guruh_nomi": "Qiz bolalar", "oquvchi_soni": 0},
        ]
    cur.execute("""SELECT guruh_kaliti,MIN(guruh_nomi) AS guruh_nomi,
                          COUNT(*) AS oquvchi_soni
                   FROM maktab_sinf_guruh_azolari
                   WHERE tizim_id=%s
                   GROUP BY guruh_kaliti
                   ORDER BY MIN(guruh_nomi),guruh_kaliti""", (system["id"],))
    return [dict(row) for row in cur.fetchall()]


def _v1876_group_system_catalog(cur, maktab_id: int):
    _sinf_kop_guruh_jadvallari(cur)
    _v1876_seed_legacy_group_systems(cur, maktab_id)
    cur.execute("""SELECT t.id,t.sinf_id,t.turi,t.nomi,t.fanlar,t.yangilangan_at,
                          s.sinf,s.harf,COALESCE(s.smena,1) AS smena,s.guruh_soni
                   FROM maktab_sinf_guruh_tizimlari t
                   JOIN maktab_sinflari s ON s.id=t.sinf_id
                   WHERE s.maktab_id=%s AND t.faol=TRUE
                   ORDER BY s.sinf::int,s.harf,
                     CASE t.turi WHEN 'gender' THEN 1 WHEN 'alphabet' THEN 2 ELSE 3 END,t.id""",
                (maktab_id,))
    result = []
    for raw in cur.fetchall():
        system = dict(raw)
        if system["turi"] in ("gender", "alphabet"):
            _sinf_guruh_tizimini_taqsimla(cur, int(system["id"]))
        groups = _v1876_system_group_rows(cur, system)
        if system["turi"] in ("gender", "alphabet"):
            cur.execute("""SELECT guruh_kaliti,COUNT(*) AS soni
                           FROM maktab_sinf_guruh_azolari
                           WHERE tizim_id=%s GROUP BY guruh_kaliti""", (system["id"],))
            counts = {str(row["guruh_kaliti"]): int(row["soni"]) for row in cur.fetchall()}
            for group in groups:
                group["oquvchi_soni"] = counts.get(group["guruh_kaliti"], 0)
        system["fanlar"] = [
            re.sub(r"\s+", " ", str(value or "")).strip()
            for value in (system.get("fanlar") or [])
            if str(value or "").strip()
        ]
        system["fan_kalitlari"] = [_v1875_subject_key(value) for value in system["fanlar"]]
        system["guruhlar"] = groups
        result.append(system)
    return result


def _v1876_pair_hash(pair_rows, systems, subject_key):
    """Faqat shu sinf+fan taqsimotiga ta'sir qiladigan manbalarni hash qiladi."""
    payload = {
        "rows": [
            {
                "id": int(row.get("id") or 0),
                "user_id": int(row.get("user_id") or 0),
                "guruh": _v1875_group_key(row.get("guruh_kaliti")),
                "soat": round(float(row.get("haftalik_soat") or 0), 1),
                "kunlik": int(row.get("kunlik_max") or 1),
            }
            for row in sorted(
                pair_rows,
                key=lambda value: (int(value.get("id") or 0), int(value.get("user_id") or 0)),
            )
        ],
        "systems": [
            {
                "id": int(system["id"]),
                "turi": system["turi"],
                "shu_fanga_biriktirilgan": subject_key in (system.get("fan_kalitlari") or []),
                "guruhlar": [group["guruh_kaliti"] for group in system.get("guruhlar") or []],
            }
            for system in systems
        ],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _v1876_pair_assignment_rows(cur, maktab_id: int):
    cur.execute("""SELECT b.id,b.sinf_id,b.user_id,b.fan_nomi,b.guruh_kaliti,
                          b.haftalik_soat,b.kunlik_max,b.manba,u.full_name,
                          s.sinf,s.harf,COALESCE(s.smena,1) AS smena
                   FROM maktab_dars_birikmalari b
                   JOIN users u ON u.user_id=b.user_id
                   JOIN maktab_sinflari s ON s.id=b.sinf_id
                   WHERE b.maktab_id=%s
                   ORDER BY s.sinf::int,s.harf,b.fan_nomi,b.id""", (maktab_id,))
    pairs = {}
    for raw in cur.fetchall():
        row = dict(raw)
        subject = re.sub(r"\s+", " ", str(row.get("fan_nomi") or "")).strip()
        subject_key = _v1875_subject_key(subject)
        key = (int(row["sinf_id"]), subject_key)
        pair = pairs.setdefault(key, {
            "sinf_id": int(row["sinf_id"]),
            "sinf": f"{row['sinf']}-{row['harf']}",
            "sinf_daraja": int(row["sinf"]),
            "smena": int(row.get("smena") or 1),
            "fan_nomi": subject,
            "fan_kaliti": subject_key,
            "rows": [],
        })
        row["guruh_kaliti"] = _v1875_group_key(row.get("guruh_kaliti"))
        row["user_id"] = int(row["user_id"])
        pair["rows"].append(row)
    return pairs


def _v1876_teacher_candidates(cur, maktab_id: int):
    result = {}
    for teacher in _v1859_effective_teachers(cur, maktab_id):
        if not teacher.get("dars_beruvchi"):
            continue
        for subject in teacher.get("fanlar_royxati") or []:
            result.setdefault(_v1875_subject_key(subject), []).append({
                "user_id": int(teacher["user_id"]),
                "full_name": teacher["full_name"],
                "haftalik_dars_soati": teacher.get("haftalik_dars_soati"),
                "sinflar": teacher.get("sinflar_royxati") or [],
            })
    for key, teachers in result.items():
        unique = {int(teacher["user_id"]): teacher for teacher in teachers}
        result[key] = sorted(
            unique.values(),
            key=lambda teacher: (str(teacher["full_name"]).casefold(), teacher["user_id"]),
        )
    return result


def _v1876_load_map(cur, maktab_id: int):
    cur.execute("""SELECT sinf_id,fan_nomi,haftalik_soat,kunlik_max
                   FROM aqlli_sinf_fan_yuklamalari_v2
                   WHERE maktab_id=%s AND haftalik_soat>0""", (maktab_id,))
    return {
        (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"])): dict(row)
        for row in cur.fetchall()
    }


def _v1876_group_review_report(cur, maktab_id: int):
    _v1876_tables(cur)
    systems = _v1876_group_system_catalog(cur, maktab_id)
    systems_by_class = _v1852_defaultdict(list)
    for system in systems:
        systems_by_class[int(system["sinf_id"])].append(system)

    pairs = _v1876_pair_assignment_rows(cur, maktab_id)
    # Guruh tizimiga fan biriktirilgan, ammo shablonda qator yo'q bo'lsa ham
    # tasdiqlash oynasida ko'rsatiladi.
    for system in systems:
        for subject in system.get("fanlar") or []:
            key = (int(system["sinf_id"]), _v1875_subject_key(subject))
            if key not in pairs:
                pairs[key] = {
                    "sinf_id": int(system["sinf_id"]),
                    "sinf": f"{system['sinf']}-{system['harf']}",
                    "sinf_daraja": int(system["sinf"]),
                    "smena": int(system.get("smena") or 1),
                    "fan_nomi": subject,
                    "fan_kaliti": _v1875_subject_key(subject),
                    "rows": [],
                }

    cur.execute(
        "SELECT * FROM aqlli_fan_guruh_tasdiqlari_v2 WHERE maktab_id=%s",
        (maktab_id,),
    )
    confirmations = {
        (int(row["sinf_id"]), str(row["fan_kaliti"])): dict(row)
        for row in cur.fetchall()
    }

    cur.execute(
        "SELECT * FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s",
        (maktab_id,),
    )
    settings = _v1852_defaultdict(dict)
    for row in cur.fetchall():
        settings[(
            int(row["sinf_id"]),
            _v1875_subject_key(row["fan_nomi"]),
        )][str(row["guruh_kaliti"])] = dict(row)

    candidate_map = _v1876_teacher_candidates(cur, maktab_id)
    load_map = _v1876_load_map(cur, maktab_id)
    cur.execute(
        """SELECT id,nomi,turi,sigim FROM aqlli_xonalar_v2
           WHERE maktab_id=%s AND faol=TRUE AND darsga_yaroqli=TRUE
           ORDER BY CASE turi WHEN 'sport' THEN 1 WHEN 'reserve' THEN 2 ELSE 3 END,nomi""",
        (maktab_id,),
    )
    teaching_rooms = [dict(row) for row in cur.fetchall()]
    teaching_room_by_id = {int(row["id"]): row for row in teaching_rooms}
    review_pairs = []
    global_errors = []
    global_warnings = []

    for key, pair in sorted(
        pairs.items(),
        key=lambda item: (
            item[1]["sinf_daraja"],
            item[1]["sinf"],
            item[1]["fan_nomi"].casefold(),
        ),
    ):
        class_systems = systems_by_class.get(pair["sinf_id"], [])
        rows = pair["rows"]
        explicit = [row for row in rows if row["guruh_kaliti"] != "whole"]
        whole = [row for row in rows if row["guruh_kaliti"] == "whole"]

        distinct_teachers = []
        seen_teacher = set()
        for row in rows:
            if row["user_id"] not in seen_teacher:
                seen_teacher.add(row["user_id"])
                distinct_teachers.append(row)

        subject_systems = [
            system for system in class_systems
            if pair["fan_kaliti"] in (system.get("fan_kalitlari") or [])
        ]
        explicit_keys = {row["guruh_kaliti"] for row in explicit}
        matching_explicit = [
            system for system in class_systems
            if explicit_keys and explicit_keys.issubset({
                group["guruh_kaliti"] for group in system.get("guruhlar") or []
            })
        ]
        count_matching = [
            system for system in class_systems
            if len(system.get("guruhlar") or []) == len(distinct_teachers)
            and len(distinct_teachers) >= 2
        ]
        candidate_systems = []
        for system in subject_systems + matching_explicit + count_matching:
            if all(int(existing["id"]) != int(system["id"]) for existing in candidate_systems):
                candidate_systems.append(system)

        group_relevant = bool(explicit or len(distinct_teachers) > 1 or subject_systems)
        if not group_relevant:
            continue

        pair_hash = _v1876_pair_hash(rows, class_systems, pair["fan_kaliti"])
        confirmation = confirmations.get(key)
        valid_confirmation = bool(
            confirmation
            and confirmation.get("tasdiqlangan")
            and str(confirmation.get("manba_hash")) == pair_hash
        )
        mode = (
            str(confirmation.get("turi"))
            if valid_confirmation
            else "group"
        )

        selected_system_id = None
        if mode == "group":
            if valid_confirmation and confirmation.get("tizim_id"):
                selected_system_id = int(confirmation["tizim_id"])
            elif len(subject_systems) == 1:
                selected_system_id = int(subject_systems[0]["id"])
            elif len(candidate_systems) == 1:
                selected_system_id = int(candidate_systems[0]["id"])
        selected_system = next(
            (
                system for system in class_systems
                if int(system["id"]) == int(selected_system_id or 0)
            ),
            None,
        )

        errors = []
        warnings = []
        positive_hours = sorted({
            float(row.get("haftalik_soat") or 0)
            for row in rows if float(row.get("haftalik_soat") or 0) > 0
        })
        nonempty_daily = sorted({
            int(row.get("kunlik_max") or 1)
            for row in rows if row.get("kunlik_max") not in (None, "")
        })
        fallback_load = load_map.get(key) or {}
        if not positive_hours and float(fallback_load.get("haftalik_soat") or 0) > 0:
            positive_hours = [float(fallback_load["haftalik_soat"])]
            warnings.append("Haftalik soat oldingi sinf–fan yuklamasidan olindi")
        if not nonempty_daily and fallback_load:
            nonempty_daily = [int(fallback_load.get("kunlik_max") or 1)]

        weekly_hours = positive_hours[0] if len(positive_hours) == 1 else 0
        daily_max = nonempty_daily[0] if len(nonempty_daily) == 1 else 1
        if not rows:
            errors.append("Bu guruhli fan uchun shablonda o'qituvchi birikmasi yo'q")
        if len(positive_hours) != 1:
            errors.append("Guruhli fan uchun haftalik soat bitta aniq qiymat bo'lishi kerak")
        if len(nonempty_daily) > 1:
            errors.append("Guruhli fan qatorlaridagi kunlik maksimum teng bo'lishi kerak")
        if rows and any(float(row.get("haftalik_soat") or 0) <= 0 for row in rows) and weekly_hours:
            warnings.append(f"Soati bo'sh guruh qatorlari tasdiqda {weekly_hours} soatga tenglashtiriladi")
        if explicit and whole:
            errors.append("Butun sinf va guruh qatorlari birga yozilgan")

        group_payload = []
        if mode == "group":
            if not class_systems:
                errors.append("Sinfda hech qanday guruhlash tizimi yaratilmagan")
            elif not candidate_systems and not selected_system:
                errors.append("Bu fan uchun qaysi guruhlash tizimi ishlashi aniqlanmagan")
            elif len(candidate_systems) > 1 and not selected_system:
                warnings.append("Bir nechta guruhlash tizimi mos keldi — bittasini tanlang")

            if selected_system:
                system_groups = selected_system.get("guruhlar") or []
                saved = settings.get(key, {})
                used_room_ids = set()
                sport_subject = any(
                    word in pair["fan_kaliti"]
                    for word in ("jismoniy", "sport", "fizkultura")
                )
                explicit_by_key = {row["guruh_kaliti"]: row for row in explicit}
                ordered_whole = sorted(
                    whole,
                    key=lambda row: (
                        int(row.get("id") or 0),
                        str(row.get("full_name") or "").casefold(),
                    ),
                )
                for index, group in enumerate(system_groups):
                    group_key = group["guruh_kaliti"]
                    source = explicit_by_key.get(group_key)
                    setting = saved.get(group_key) or {}
                    teacher_id = setting.get("oqituvchi_user_id") if valid_confirmation else None
                    if teacher_id is None and source:
                        teacher_id = source.get("user_id")
                    if teacher_id is None and index < len(ordered_whole):
                        teacher_id = ordered_whole[index].get("user_id")
                    teacher_name = next(
                        (
                            teacher["full_name"]
                            for teacher in candidate_map.get(pair["fan_kaliti"], [])
                            if int(teacher["user_id"]) == int(teacher_id or 0)
                        ),
                        source.get("full_name") if source else None,
                    )
                    room_id = None if index == 0 else setting.get("xona_id")
                    if room_id is not None and int(room_id) not in teaching_room_by_id:
                        room_id = None
                    if room_id is None and index > 0:
                        preferred_types = ("sport",) if sport_subject else ("reserve", "classroom")
                        suggested_room = next(
                            (
                                room for room in teaching_rooms
                                if str(room.get("turi") or "classroom") in preferred_types
                                and int(room["id"]) not in used_room_ids
                            ),
                            None,
                        )
                        if suggested_room:
                            room_id = int(suggested_room["id"])
                        else:
                            warnings.append(
                                "Bo'linishga xona topilmadi — bir guruh sinf xonasida qoladi, qolganiga sport zal yoki zaxira xona kiriting"
                            )
                    if room_id is not None:
                        used_room_ids.add(int(room_id))
                    group_payload.append({
                        **group,
                        "oqituvchi_user_id": int(teacher_id) if teacher_id is not None else None,
                        "oqituvchi_ismi": teacher_name,
                        "xona_id": int(room_id) if room_id is not None else None,
                        "xona_nomi": teaching_room_by_id.get(int(room_id), {}).get("nomi") if room_id is not None else None,
                    })

                teacher_ids = [
                    group["oqituvchi_user_id"]
                    for group in group_payload
                    if group.get("oqituvchi_user_id") is not None
                ]
                if len(group_payload) < 2:
                    errors.append("Tanlangan guruhlash tizimida kamida 2 ta guruh bo'lishi kerak")
                if len(teacher_ids) != len(group_payload):
                    errors.append("Har bir guruhga bittadan o'qituvchi tanlang")
                if len(teacher_ids) != len(set(teacher_ids)):
                    errors.append("Parallel guruhlarga turli o'qituvchilar kerak")
                if rows and len(distinct_teachers) != len(group_payload) and not valid_confirmation:
                    warnings.append(
                        f"Shablonda {len(distinct_teachers)} ta o'qituvchi, "
                        f"tanlangan tizimda {len(group_payload)} ta guruh bor"
                    )
        else:
            # Butun sinf tasdiqlanganda source qatorida aynan bitta o'qituvchi bo'ladi.
            if len(whole) != 1:
                errors.append("Butun sinf uchun aynan bitta o'qituvchi tanlang")

        status = (
            "tasdiqlangan"
            if valid_confirmation and not errors
            else ("xato" if errors else "taklif")
        )
        if status != "tasdiqlangan":
            global_errors.append(
                f"{pair['sinf']} / {pair['fan_nomi']}: "
                + ("; ".join(errors) if errors else "guruh va o'qituvchilar tasdiqlanmagan")
            )
        global_warnings.extend(
            f"{pair['sinf']} / {pair['fan_nomi']}: {warning}"
            for warning in warnings
        )

        # Parallel guruh hisobining uchta alohida o'lchovi:
        #   1) sinf reja soati — guruhlar soniga ko'paymaydi;
        #   2) o'qituvchi-soat — har bir guruh o'qituvchisiga alohida yoziladi;
        #   3) jadval sloti — guruhlar bir vaqtda parallel turgani uchun reja soatiga teng.
        parallel_guruh_soni = (
            len(group_payload)
            if mode == "group" and group_payload
            else (
                len(distinct_teachers)
                if mode == "group" and len(distinct_teachers) >= 2
                else 1
            )
        )
        sinf_reja_soati = round(float(weekly_hours or 0), 1)
        jadval_parallel_slot_soni = round(float(weekly_hours or 0), 1)
        oqituvchi_soat_jami = round(
            float(weekly_hours or 0) * int(parallel_guruh_soni),
            1,
        )

        review_pairs.append({
            "sinf_id": pair["sinf_id"],
            "sinf": pair["sinf"],
            "sinf_daraja": pair["sinf_daraja"],
            "smena": pair["smena"],
            "fan_nomi": pair["fan_nomi"],
            "fan_kaliti": pair["fan_kaliti"],
            "haftalik_soat": weekly_hours,
            "sinf_reja_soati": sinf_reja_soati,
            "jadval_parallel_slot_soni": jadval_parallel_slot_soni,
            "parallel_guruh_soni": parallel_guruh_soni,
            "har_bir_guruh_oqituvchi_soati": round(float(weekly_hours or 0), 1),
            "oqituvchi_soat_jami": oqituvchi_soat_jami,
            "kunlik_max": daily_max,
            "status": status,
            "tasdiqlangan": status == "tasdiqlangan",
            "manba_hash": pair_hash,
            "turi": mode,
            "tizim_id": selected_system_id,
            "tizimlar": [
                {
                    "id": int(system["id"]),
                    "turi": system["turi"],
                    "nomi": system["nomi"],
                    "fan_biriktirilgan": pair["fan_kaliti"] in (system.get("fan_kalitlari") or []),
                    "guruhlar": system.get("guruhlar") or [],
                }
                for system in class_systems
            ],
            "guruhlar": group_payload,
            "asosiy_oqituvchi_user_id": whole[0]["user_id"] if len(whole) == 1 else None,
            "kandidat_oqituvchilar": candidate_map.get(pair["fan_kaliti"], []),
            "import_oqituvchilari": [
                {
                    "user_id": row["user_id"],
                    "full_name": row.get("full_name"),
                    "guruh_kaliti": row["guruh_kaliti"],
                    "haftalik_soat": row.get("haftalik_soat"),
                }
                for row in distinct_teachers
            ],
            "xatolar": errors,
            "ogohlantirishlar": warnings,
        })

    # Barcha sinflar ko'rinadi: guruhli fani yo'q sinf ham 'tizim yo'q/bor' deb
    # jadvaldan oldin tekshirilishi mumkin.
    cur.execute("""SELECT id,sinf,harf,COALESCE(smena,1) AS smena
                   FROM maktab_sinflari WHERE maktab_id=%s
                   ORDER BY sinf::int,harf""", (maktab_id,))
    class_map = {
        int(row["id"]): {
            "sinf_id": int(row["id"]),
            "sinf": f"{row['sinf']}-{row['harf']}",
            "sinf_daraja": int(row["sinf"]),
            "smena": int(row.get("smena") or 1),
            "tizimlar": [],
            "fanlar": [],
        }
        for row in cur.fetchall()
    }
    for system in systems:
        class_entry = class_map.setdefault(int(system["sinf_id"]), {
            "sinf_id": int(system["sinf_id"]),
            "sinf": f"{system['sinf']}-{system['harf']}",
            "sinf_daraja": int(system["sinf"]),
            "smena": int(system.get("smena") or 1),
            "tizimlar": [],
            "fanlar": [],
        })
        class_entry["tizimlar"].append({
            "id": int(system["id"]),
            "turi": system["turi"],
            "nomi": system["nomi"],
            "fanlar": system.get("fanlar") or [],
            "guruhlar": system.get("guruhlar") or [],
        })
    for pair in review_pairs:
        class_map[pair["sinf_id"]]["fanlar"].append(pair)

    confirmed = sum(1 for pair in review_pairs if pair["tasdiqlangan"])
    summary = {
        "sinf_soni": len(class_map),
        "guruh_tizimli_sinf_soni": sum(1 for row in class_map.values() if row["tizimlar"]),
        "guruhli_fan_soni": len(review_pairs),
        "tasdiqlangan": confirmed,
        "tasdiqlanmagan": len(review_pairs) - confirmed,
        "xato_soni": len(global_errors),
    }
    return {
        "tayyor": not global_errors,
        "xulosa": summary,
        "sinflar": sorted(
            class_map.values(),
            key=lambda row: (row["sinf_daraja"], row["sinf"]),
        ),
        "fanlar": review_pairs,
        "xonalar": teaching_rooms,
        "xatolar": list(dict.fromkeys(global_errors))[:300],
        "ogohlantirishlar": list(dict.fromkeys(global_warnings))[:300],
    }


class V1876GroupTeacher(BaseModel):
    guruh_kaliti: str
    oqituvchi_user_id: int
    xona_id: Optional[int] = None


class V1876GroupPairConfirm(BaseModel):
    sinf_id: int
    fan_nomi: str
    turi: str = "group"
    tizim_id: Optional[int] = None
    asosiy_oqituvchi_user_id: Optional[int] = None
    guruhlar: list[V1876GroupTeacher] = []


class V1876GroupConfirmBatch(BaseModel):
    maktab_id: int
    birikmalar: list[V1876GroupPairConfirm]


def _v1876_exact_subject_teachers(cur, maktab_id: int, subject_key: str):
    allowed = {}
    for teacher in _v1859_effective_teachers(cur, maktab_id):
        if any(
            _v1875_subject_key(subject) == subject_key
            for subject in (teacher.get("fanlar_royxati") or [])
        ):
            allowed[int(teacher["user_id"])] = teacher
    return allowed


def _v1876_pair_source_rows(cur, maktab_id: int, class_id: int, subject_key: str):
    cur.execute("""SELECT b.*,u.full_name FROM maktab_dars_birikmalari b
                   JOIN users u ON u.user_id=b.user_id
                   WHERE b.maktab_id=%s AND b.sinf_id=%s ORDER BY b.id""",
                (maktab_id, class_id))
    return [
        dict(row) for row in cur.fetchall()
        if _v1875_subject_key(row.get("fan_nomi")) == subject_key
    ]


def _v1876_delete_group_settings(cur, maktab_id: int, class_id: int, subject_key: str):
    cur.execute("""SELECT fan_nomi,guruh_kaliti FROM aqlli_guruh_sozlamalari_v2
                   WHERE maktab_id=%s AND sinf_id=%s""", (maktab_id, class_id))
    for row in cur.fetchall():
        if _v1875_subject_key(row.get("fan_nomi")) == subject_key:
            cur.execute("""DELETE FROM aqlli_guruh_sozlamalari_v2
                           WHERE maktab_id=%s AND sinf_id=%s
                             AND fan_nomi=%s AND guruh_kaliti=%s""",
                        (maktab_id, class_id, row["fan_nomi"], row["guruh_kaliti"]))


def _v1876_update_system_subjects(cur, class_id: int, subject: str, selected_system_id: Optional[int]):
    cur.execute("""SELECT id,fanlar FROM maktab_sinf_guruh_tizimlari
                   WHERE sinf_id=%s AND faol=TRUE ORDER BY id FOR UPDATE""", (class_id,))
    subject_key = _v1875_subject_key(subject)
    for row in cur.fetchall():
        subjects = [
            re.sub(r"\s+", " ", str(value or "")).strip()
            for value in (row.get("fanlar") or [])
            if str(value or "").strip()
        ]
        subjects = [value for value in subjects if _v1875_subject_key(value) != subject_key]
        if selected_system_id is not None and int(row["id"]) == int(selected_system_id):
            subjects.append(subject)
        cur.execute(
            "UPDATE maktab_sinf_guruh_tizimlari "
            "SET fanlar=%s,yangilangan_at=NOW() WHERE id=%s",
            (subjects, row["id"]),
        )


def _v1876_rebuild_teacher_class_links(cur, maktab_id: int, teacher_ids):
    """O'qituvchi almashganda eski sinf havolalarini exact birikmalardan qayta quradi."""
    teacher_ids = sorted({int(value) for value in teacher_ids if value is not None})
    if not teacher_ids:
        return
    cur.execute(
        "DELETE FROM maktab_xodim_sinflari "
        "WHERE maktab_id=%s AND user_id=ANY(%s)",
        (maktab_id, teacher_ids),
    )
    cur.execute("""SELECT b.user_id,b.sinf_id,b.fan_nomi,s.sinf,s.harf
                   FROM maktab_dars_birikmalari b
                   JOIN maktab_sinflari s ON s.id=b.sinf_id
                   WHERE b.maktab_id=%s AND b.user_id=ANY(%s)
                   ORDER BY b.user_id,s.sinf::int,s.harf,b.fan_nomi""",
                (maktab_id, teacher_ids))
    by_teacher_class = {}
    class_labels = _v1852_defaultdict(set)
    for row in cur.fetchall():
        key = (int(row["user_id"]), int(row["sinf_id"]))
        entry = by_teacher_class.setdefault(key, {})
        subject = re.sub(r"\s+", " ", str(row.get("fan_nomi") or "")).strip()
        entry[_v1875_subject_key(subject)] = subject
        class_labels[int(row["user_id"])].add(f"{row['sinf']}-{row['harf']}")
    for (teacher_id, class_id), subject_map in by_teacher_class.items():
        subjects = sorted(subject_map.values(), key=lambda value: value.casefold())
        cur.execute("""INSERT INTO maktab_xodim_sinflari(
                         maktab_id,user_id,sinf_id,fanlari)
                       VALUES(%s,%s,%s,%s)
                       ON CONFLICT(user_id,sinf_id) DO UPDATE SET
                         maktab_id=EXCLUDED.maktab_id,fanlari=EXCLUDED.fanlari""",
                    (maktab_id, teacher_id, class_id, "\n".join(subjects) or None))
    for teacher_id in teacher_ids:
        labels = sorted(class_labels.get(teacher_id, set()), key=_v1859_sinf_sort_key)
        cur.execute(
            "UPDATE users SET oqitadigan_sinflari=%s WHERE maktab_id=%s AND user_id=%s",
            ("; ".join(labels) or None, maktab_id, teacher_id),
        )


@app.get("/api/maktab/aqlli_jadval/v2/guruh_tasdiqlash")
def v1876_group_review(token: str, maktab_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1876_tables(cur)
        if not _v1852_staff(cur, actor_id, maktab_id):
            raise HTTPException(status_code=403, detail="Guruh taqsimotini ko'rish vakolati yo'q")
        report = _v1876_group_review_report(cur, maktab_id)
        conn.commit()
        return report
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.put("/api/maktab/aqlli_jadval/v2/guruh_tasdiqlash")
def v1876_group_confirm(sorov: V1876GroupConfirmBatch, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v1876_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(
                status_code=403,
                detail="Guruh o'qituvchilarini faqat rahbariyat tasdiqlaydi",
            )
        if not sorov.birikmalar:
            raise HTTPException(status_code=400, detail="Tasdiqlash uchun fan tanlanmagan")
        if len(sorov.birikmalar) > 300:
            raise HTTPException(status_code=400, detail="Bir amalda 300 tadan ortiq fan tasdiqlanmaydi")

        systems = _v1876_group_system_catalog(cur, sorov.maktab_id)
        systems_by_id = {int(system["id"]): system for system in systems}
        cur.execute(
            "SELECT id,sinf,harf FROM maktab_sinflari WHERE maktab_id=%s",
            (sorov.maktab_id,),
        )
        classes = {int(row["id"]): dict(row) for row in cur.fetchall()}
        cur.execute(
            """SELECT id FROM aqlli_xonalar_v2
               WHERE maktab_id=%s AND faol=TRUE AND darsga_yaroqli=TRUE""",
            (sorov.maktab_id,),
        )
        allowed_room_ids = {int(row["id"]) for row in cur.fetchall()}
        old_group_settings = {}
        cur.execute(
            "SELECT * FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s",
            (sorov.maktab_id,),
        )
        for row in cur.fetchall():
            old_group_settings[(
                int(row["sinf_id"]),
                _v1875_subject_key(row["fan_nomi"]),
                str(row["guruh_kaliti"]),
            )] = dict(row)

        confirmed_count = 0
        all_affected_teacher_ids = set()

        for item in sorov.birikmalar:
            class_id = int(item.sinf_id)
            if class_id not in classes:
                raise HTTPException(status_code=400, detail=f"Sinf topilmadi: {class_id}")
            subject = re.sub(r"\s+", " ", str(item.fan_nomi or "")).strip()
            subject_key = _v1875_subject_key(subject)
            if not subject_key:
                raise HTTPException(status_code=400, detail="Fan nomi bo'sh")

            rows = _v1876_pair_source_rows(
                cur, sorov.maktab_id, class_id, subject_key
            )
            old_teacher_ids = {int(row["user_id"]) for row in rows}
            all_affected_teacher_ids.update(old_teacher_ids)
            hours_set = {
                float(row.get("haftalik_soat") or 0)
                for row in rows if float(row.get("haftalik_soat") or 0) > 0
            }
            daily_set = {
                int(row.get("kunlik_max") or 1)
                for row in rows if row.get("kunlik_max") not in (None, "")
            }
            if len(hours_set) != 1:
                cur.execute("""SELECT fan_nomi,haftalik_soat,kunlik_max
                               FROM aqlli_sinf_fan_yuklamalari_v2
                               WHERE maktab_id=%s AND sinf_id=%s""",
                            (sorov.maktab_id, class_id))
                matching_load = next(
                    (
                        dict(row) for row in cur.fetchall()
                        if _v1875_subject_key(row.get("fan_nomi")) == subject_key
                        and float(row.get("haftalik_soat") or 0) > 0
                    ),
                    None,
                )
                if matching_load:
                    hours_set = {float(matching_load["haftalik_soat"])}
                    daily_set = {int(matching_load.get("kunlik_max") or 1)}
            if len(hours_set) != 1:
                label = f"{classes[class_id]['sinf']}-{classes[class_id]['harf']}"
                raise HTTPException(
                    status_code=400,
                    detail=f"{label} / {subject}: haftalik soat aniq emas",
                )
            if len(daily_set) > 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"{subject}: guruhlarning kunlik maksimumi teng emas",
                )
            weekly_hours = next(iter(hours_set))
            daily_max = next(iter(daily_set), 1)
            allowed_teachers = _v1876_exact_subject_teachers(
                cur, sorov.maktab_id, subject_key
            )
            row_ids = [int(row["id"]) for row in rows]

            mode = str(item.turi or "group").strip().lower()
            if mode not in {"whole", "group"}:
                raise HTTPException(status_code=400, detail="Turi whole yoki group bo'lishi kerak")

            if mode == "whole":
                teacher_id = int(item.asosiy_oqituvchi_user_id or 0)
                if teacher_id not in allowed_teachers:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{subject}: tanlangan o'qituvchi bu fanga mos emas",
                    )
                if row_ids:
                    cur.execute(
                        "DELETE FROM maktab_dars_birikmalari WHERE id=ANY(%s)",
                        (row_ids,),
                    )
                cur.execute("""INSERT INTO maktab_dars_birikmalari(
                                maktab_id,user_id,sinf_id,fan_nomi,guruh_kaliti,
                                haftalik_soat,kunlik_max,manba)
                               VALUES(%s,%s,%s,%s,'whole',%s,%s,'guruh_tasdiq')""",
                            (
                                sorov.maktab_id, teacher_id, class_id, subject,
                                weekly_hours, daily_max,
                            ))
                _v1876_delete_group_settings(
                    cur, sorov.maktab_id, class_id, subject_key
                )
                _v1876_update_system_subjects(cur, class_id, subject, None)
                selected_system_id = None
                selected_teacher_ids = {teacher_id}
            else:
                system_id = int(item.tizim_id or 0)
                system = systems_by_id.get(system_id)
                if not system or int(system["sinf_id"]) != class_id:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{subject}: tanlangan guruhlash tizimi bu sinfga tegishli emas",
                    )
                expected_groups = [
                    str(group["guruh_kaliti"])
                    for group in system.get("guruhlar") or []
                ]
                if len(expected_groups) < 2:
                    raise HTTPException(
                        status_code=400,
                        detail=f"{subject}: tanlangan tizimda kamida 2 ta guruh bo'lishi kerak",
                    )
                payload_map = {
                    str(group.guruh_kaliti): group for group in item.guruhlar
                }
                if set(payload_map) != set(expected_groups):
                    label = f"{classes[class_id]['sinf']}-{classes[class_id]['harf']}"
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"{label} / {subject}: barcha guruhlar to'liq tanlanishi "
                            f"kerak ({', '.join(expected_groups)})"
                        ),
                    )
                teacher_ids = [
                    int(payload_map[key].oqituvchi_user_id)
                    for key in expected_groups
                ]
                if len(teacher_ids) != len(set(teacher_ids)):
                    raise HTTPException(
                        status_code=400,
                        detail=f"{subject}: parallel guruhlarga turli o'qituvchilar tanlang",
                    )
                for teacher_id in teacher_ids:
                    if teacher_id not in allowed_teachers:
                        raise HTTPException(
                            status_code=400,
                            detail=f"{subject}: {teacher_id} bu fanga mos o'qituvchi emas",
                        )
                selected_room_ids = []
                for group_key in expected_groups:
                    selected_room_id = payload_map[group_key].xona_id
                    if selected_room_id is None:
                        continue
                    selected_room_id = int(selected_room_id)
                    if selected_room_id not in allowed_room_ids:
                        raise HTTPException(
                            status_code=400,
                            detail=f"{subject}: tanlangan xona dars o'tishga yaroqli emas yoki faol emas",
                        )
                    selected_room_ids.append(selected_room_id)
                if len(selected_room_ids) != len(set(selected_room_ids)):
                    raise HTTPException(
                        status_code=400,
                        detail=f"{subject}: parallel guruhlarga bir xil qo'shimcha xona tanlangan",
                    )
                if row_ids:
                    cur.execute(
                        "DELETE FROM maktab_dars_birikmalari WHERE id=ANY(%s)",
                        (row_ids,),
                    )
                _v1876_delete_group_settings(
                    cur, sorov.maktab_id, class_id, subject_key
                )
                for group_index, group_key in enumerate(expected_groups):
                    group = payload_map[group_key]
                    teacher_id = int(group.oqituvchi_user_id)
                    cur.execute("""INSERT INTO maktab_dars_birikmalari(
                                    maktab_id,user_id,sinf_id,fan_nomi,guruh_kaliti,
                                    haftalik_soat,kunlik_max,manba)
                                   VALUES(%s,%s,%s,%s,%s,%s,%s,'guruh_tasdiq')""",
                                (
                                    sorov.maktab_id, teacher_id, class_id, subject,
                                    group_key, weekly_hours, daily_max,
                                ))
                    old = old_group_settings.get(
                        (class_id, subject_key, group_key), {}
                    )
                    room_id = None if group_index == 0 else (
                        group.xona_id
                        if group.xona_id is not None
                        else old.get("xona_id")
                    )
                    cur.execute("""INSERT INTO aqlli_guruh_sozlamalari_v2(
                                    maktab_id,sinf_id,fan_nomi,guruh_kaliti,
                                    oqituvchi_user_id,xona_id)
                                   VALUES(%s,%s,%s,%s,%s,%s)
                                   ON CONFLICT(
                                     maktab_id,sinf_id,fan_nomi,guruh_kaliti
                                   ) DO UPDATE SET
                                     oqituvchi_user_id=EXCLUDED.oqituvchi_user_id,
                                     xona_id=EXCLUDED.xona_id""",
                                (
                                    sorov.maktab_id, class_id, subject, group_key,
                                    teacher_id, room_id,
                                ))
                _v1876_update_system_subjects(
                    cur, class_id, subject, system_id
                )
                selected_system_id = system_id
                selected_teacher_ids = set(teacher_ids)

            all_affected_teacher_ids.update(selected_teacher_ids)
            # Tasdiq hashini o'zgargan aniq manbadan hisoblaymiz.
            fresh_rows = _v1876_pair_source_rows(
                cur, sorov.maktab_id, class_id, subject_key
            )
            fresh_systems = [
                system for system in _v1876_group_system_catalog(cur, sorov.maktab_id)
                if int(system["sinf_id"]) == class_id
            ]
            source_hash = _v1876_pair_hash(
                fresh_rows, fresh_systems, subject_key
            )
            cur.execute("""INSERT INTO aqlli_fan_guruh_tasdiqlari_v2(
                            maktab_id,sinf_id,fan_nomi,fan_kaliti,turi,tizim_id,
                            manba_hash,tasdiqlangan,tasdiqlagan_user_id,yangilangan_at)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,TRUE,%s,NOW())
                           ON CONFLICT(maktab_id,sinf_id,fan_kaliti) DO UPDATE SET
                             fan_nomi=EXCLUDED.fan_nomi,turi=EXCLUDED.turi,
                             tizim_id=EXCLUDED.tizim_id,manba_hash=EXCLUDED.manba_hash,
                             tasdiqlangan=TRUE,
                             tasdiqlagan_user_id=EXCLUDED.tasdiqlagan_user_id,
                             yangilangan_at=NOW()""",
                        (
                            sorov.maktab_id, class_id, subject, subject_key, mode,
                            selected_system_id, source_hash, actor_id,
                        ))
            confirmed_count += 1

        _v1876_rebuild_teacher_class_links(
            cur, sorov.maktab_id, all_affected_teacher_ids
        )
        cur.execute("""UPDATE aqlli_jadval_urinishlari_v2 SET holat='bekor'
                       WHERE maktab_id=%s AND holat='draft'""",
                    (sorov.maktab_id,))

        # Tasdiqlarni bittalab saqlash mumkin. Qolgan guruhli fanlar hali
        # tasdiqlanmagan bo'lsa strict manba rebuild keyinga qoldiriladi.
        report = _v1876_group_review_report(cur, sorov.maktab_id)
        sync = {
            "tayyor": False,
            "kutilmoqda": report.get("xulosa", {}).get("tasdiqlanmagan", 0),
            "izoh": "Qolgan guruhli fanlar tasdiqlangandan keyin jadval manbasi sinxronlanadi",
        }
        if report.get("tayyor"):
            sync = _v1875_rebuild_schedule_sources(
                cur,
                sorov.maktab_id,
                cancel_drafts=False,
                reason="guruh_tasdiq",
            )
            if sync.get("xatolar"):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Guruh tasdiqidan keyin yuklama xatosi: "
                        + "; ".join(sync["xatolar"][:12])
                    ),
                )
            report = _v1876_group_review_report(cur, sorov.maktab_id)

        conn.commit()
        return {
            "holat": "tasdiqlandi",
            "tasdiqlangan_soni": confirmed_count,
            "hisobot": report,
            "sinxronlash": sync,
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()

# ========================= V18.76 END =========================

class V1876QuickGroupSystem(BaseModel):
    maktab_id: int
    sinf_id: int
    fan_nomi: str
    turi: str


@app.post("/api/maktab/aqlli_jadval/v2/guruh_tizimi_tez")
def v1876_quick_group_system(sorov: V1876QuickGroupSystem, token: str):
    actor_id = _jwt_tekshir(token)
    kind = str(sorov.turi or "").strip().lower()
    if kind not in {"alphabet", "gender"}:
        raise HTTPException(
            status_code=400,
            detail="Tez yaratishda faqat 1/2-guruh yoki O'g'il/Qiz tizimi tanlanadi",
        )
    subject = re.sub(r"\s+", " ", str(sorov.fan_nomi or "")).strip()
    if not subject:
        raise HTTPException(status_code=400, detail="Fan nomi bo'sh")

    conn = _db(); cur = conn.cursor()
    try:
        _v1876_tables(cur)
        cur.execute(
            "SELECT maktab_id FROM maktab_sinflari WHERE id=%s",
            (sorov.sinf_id,),
        )
        cls = cur.fetchone()
        if not cls or int(cls["maktab_id"]) != int(sorov.maktab_id):
            raise HTTPException(status_code=404, detail="Sinf topilmadi")
        if not _maktab_sinf_boshqaruvchi_mi(
            cur, actor_id, sorov.maktab_id
        ) and not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(
                status_code=403,
                detail="Guruh tizimini faqat admin yoki o'quv ishlari zavuchi yaratadi",
            )

        cur.execute(
            "SELECT id,fanlar FROM maktab_sinf_guruh_tizimlari "
            "WHERE sinf_id=%s AND turi=%s FOR UPDATE",
            (sorov.sinf_id, kind),
        )
        existing = cur.fetchone()
        subjects = [
            re.sub(r"\s+", " ", str(value or "")).strip()
            for value in ((existing or {}).get("fanlar") or [])
            if str(value or "").strip()
        ]
        if all(
            _v1875_subject_key(value) != _v1875_subject_key(subject)
            for value in subjects
        ):
            subjects.append(subject)

        cur.execute("""INSERT INTO maktab_sinf_guruh_tizimlari(
                         sinf_id,turi,nomi,fanlar,faol,yaratilgan_by,yangilangan_at)
                       VALUES(%s,%s,%s,%s,TRUE,%s,NOW())
                       ON CONFLICT(sinf_id,turi) DO UPDATE SET
                         nomi=EXCLUDED.nomi,
                         fanlar=EXCLUDED.fanlar,
                         faol=TRUE,
                         yangilangan_at=NOW()
                       RETURNING id""",
                    (
                        sorov.sinf_id,
                        kind,
                        _SINF_GURUH_TIZIM_NOMLARI[kind],
                        subjects,
                        actor_id,
                    ))
        system_id = int(cur.fetchone()["id"])
        _sinf_guruh_tizimini_taqsimla(cur, system_id)

        cur.execute(
            "SELECT turi FROM maktab_sinf_guruh_tizimlari "
            "WHERE sinf_id=%s AND faol=TRUE ORDER BY id",
            (sorov.sinf_id,),
        )
        active_types = [row["turi"] for row in cur.fetchall()]
        legacy = (
            active_types[0]
            if len(active_types) == 1
            else ("manual" if active_types else "none")
        )
        cur.execute(
            "UPDATE maktab_sinflari SET guruhlash_usuli=%s WHERE id=%s",
            (legacy, sorov.sinf_id),
        )
        report = _v1876_group_review_report(cur, sorov.maktab_id)
        conn.commit()
        return {
            "holat": "saqlandi",
            "tizim_id": system_id,
            "turi": kind,
            "hisobot": report,
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()

# ========================= V18.76 QUICK GROUP SYSTEM END =========================


# ═══════════════════════════════════════════════════════════
# V19.2 — O'QITUVCHI-ASOSLI YUKLAMA + AQILLI ALMASHTIRISH
#
# Bitta kanonik qator:
#   o'qituvchi + fan + sinf + aniq guruh + haftalik soat.
#
# Excel import va saytdagi qo'lda kiritish aynan bir xil
# maktab_dars_birikmalari manbasiga yozadi. Shuning uchun bir o'qituvchi
# Fizika, Astronomiya va Iqtisoddan turli sinf/guruhlarga kirsa ham fanlar
# aralashmaydi. Sinf reja soati guruhlar soniga ko'paymaydi, o'qituvchi
# yuklamasi esa har bir guruh bo'yicha alohida yig'iladi.
# ═══════════════════════════════════════════════════════════


SAMTM_V19_2_AUTO_SWAP_DEFAULT = str(
    os.getenv("SAMTM_V19_2_AUTO_SWAP_DEFAULT", "true")
).strip().lower() not in {"0", "false", "no", "off"}
SAMTM_V19_2_SWAP_SUGGESTION_LIMIT = max(
    1, min(60, int(os.getenv("SAMTM_V19_2_SWAP_SUGGESTION_LIMIT", "24")))
)


def _v192_tables(cur):
    _v1876_tables(cur)
    cur.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS tugilgan_sana DATE"
    )
    cur.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS mutaxassisligi TEXT"
    )
    cur.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS haftalik_maqsad_soat INTEGER"
    )
    cur.execute(
        "ALTER TABLE maktab_dars_birikmalari "
        "ADD COLUMN IF NOT EXISTS xona_id BIGINT REFERENCES aqlli_xonalar_v2(id) ON DELETE SET NULL"
    )
    cur.execute(
        "ALTER TABLE maktab_dars_birikmalari "
        "ADD COLUMN IF NOT EXISTS yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
    )
    # O'quv rejada 0,5 va 1,5 soatli fanlar bor. O'qituvchi yuklamasi
    # ham aynan shu aniqlikda saqlanishi shart; aks holda 22/22 bo'lgan
    # yuklama ichidagi bitta 1,5 qator POST validatsiyasida yiqiladi.
    cur.execute("""ALTER TABLE maktab_dars_birikmalari
                   ALTER COLUMN haftalik_soat TYPE NUMERIC(5,1)
                   USING haftalik_soat::NUMERIC(5,1)""")
    cur.execute("""ALTER TABLE users
                   ALTER COLUMN haftalik_dars_soati TYPE NUMERIC(5,1)
                   USING haftalik_dars_soati::NUMERIC(5,1)""")
    cur.execute("""ALTER TABLE users
                   ALTER COLUMN haftalik_maqsad_soat TYPE NUMERIC(5,1)
                   USING haftalik_maqsad_soat::NUMERIC(5,1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_jadval_boshqaruv_v19_2(
        maktab_id INTEGER PRIMARY KEY REFERENCES maktablar(id) ON DELETE CASCADE,
        avtomatik_tavsiya BOOLEAN NOT NULL DEFAULT TRUE,
        yangilagan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_oquv_reja_holati_v19_3(
        maktab_id INTEGER PRIMARY KEY REFERENCES maktablar(id) ON DELETE CASCADE,
        holat TEXT NOT NULL DEFAULT 'draft'
            CHECK(holat IN ('draft','tasdiqlangan')),
        versiya INTEGER NOT NULL DEFAULT 1,
        tasdiqlagan_user_id BIGINT,
        tasdiqlangan_at TIMESTAMPTZ,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_oquv_reja_qatorlari_v19_3(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        sinf_id INTEGER NOT NULL REFERENCES maktab_sinflari(id) ON DELETE CASCADE,
        fan_nomi TEXT NOT NULL,
        haftalik_soat NUMERIC(4,1) NOT NULL CHECK(haftalik_soat BETWEEN 0.5 AND 20),
        kunlik_max INTEGER NOT NULL DEFAULT 1 CHECK(kunlik_max BETWEEN 1 AND 4),
        manba TEXT NOT NULL DEFAULT 'qolda',
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE(maktab_id,sinf_id,fan_nomi)
    )""")
    # 2026–2027 tayanch rejada 0,5 va 1,5 soatli fanlar bor. Eski INTEGER
    # ustunni ma'lumotni yo'qotmasdan kasr soat saqlaydigan turga o'tkazamiz.
    cur.execute("""DO $$
        DECLARE constraint_name TEXT;
        BEGIN
          FOR constraint_name IN
            SELECT c.conname
            FROM pg_constraint c
            JOIN pg_class t ON t.oid=c.conrelid
            WHERE t.relname='aqlli_oquv_reja_qatorlari_v19_3'
              AND c.contype='c'
              AND pg_get_constraintdef(c.oid) ILIKE '%haftalik_soat%'
          LOOP
            EXECUTE format(
              'ALTER TABLE aqlli_oquv_reja_qatorlari_v19_3 DROP CONSTRAINT %I',
              constraint_name
            );
          END LOOP;
        END $$""")
    cur.execute("""ALTER TABLE aqlli_oquv_reja_qatorlari_v19_3
                   ALTER COLUMN haftalik_soat TYPE NUMERIC(4,1)
                   USING haftalik_soat::NUMERIC(4,1)""")
    cur.execute("""DO $$ BEGIN
        ALTER TABLE aqlli_oquv_reja_qatorlari_v19_3
          ADD CONSTRAINT aqlli_oquv_reja_v193_haftalik_soat_check
          CHECK(haftalik_soat BETWEEN 0.5 AND 20);
      EXCEPTION WHEN duplicate_object THEN NULL; END $$""")
    cur.execute("""ALTER TABLE aqlli_sinf_fan_yuklamalari_v2
                   ALTER COLUMN haftalik_soat TYPE NUMERIC(4,1)
                   USING haftalik_soat::NUMERIC(4,1)""")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_v193_plan_class "
        "ON aqlli_oquv_reja_qatorlari_v19_3(maktab_id,sinf_id)"
    )
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_jadval_ozgarish_log_v19_2(
        id BIGSERIAL PRIMARY KEY,
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        urinish_id BIGINT NOT NULL REFERENCES aqlli_jadval_urinishlari_v2(id) ON DELETE CASCADE,
        manba_slot_id BIGINT,
        eski_hafta_kuni INTEGER NOT NULL,
        eski_dars_raqami INTEGER NOT NULL,
        yangi_hafta_kuni INTEGER NOT NULL,
        yangi_dars_raqami INTEGER NOT NULL,
        turi TEXT NOT NULL CHECK(turi IN ('kochirish','almashtirish')),
        bajargan_user_id BIGINT,
        yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_v192_change_log_run "
        "ON aqlli_jadval_ozgarish_log_v19_2(urinish_id,yaratilgan_at DESC)"
    )


@app.on_event("startup")
def _v192_startup_tables():
    try:
        conn = _db(); cur = conn.cursor()
        _v192_tables(cur)
        conn.commit(); cur.close(); conn.close()
        app.state.samtm_fractional_hours_ready = True
        app.state.samtm_fractional_hours_error = None
    except Exception as exc:
        app.state.samtm_fractional_hours_ready = False
        app.state.samtm_fractional_hours_error = type(exc).__name__
        print(f"[V19.8 0,5/1,5 soat migratsiyasi] {exc}", flush=True)


@app.get("/api/maktab/aqlli_jadval/v3/soat_imkoniyatlari")
def v197_fractional_hour_capabilities():
    """Frontend saqlashdan oldin aynan yangi backend ishlayotganini tekshiradi."""
    schema_ready = bool(
        getattr(app.state, "samtm_fractional_hours_ready", False)
    )
    return {
        # Eski V19.7 frontend aynan shu qiymatni tekshiradi. Platformaning
        # haqiqiy yangi versiyasi alohida qaytariladi — backendni birinchi
        # deploy qilganda foydalanuvchi V19.7 frontend bilan ham saqlay oladi.
        "release": "samtm-fractional-hours-ab-week-v19.7",
        "platform_release": SAMTM_SCHOOL_RELEASE,
        "fractional_hours": schema_ready,
        "fraction_step": 0.5,
        "ab_week": schema_ready,
        "schema_ready": schema_ready,
        "example": {
            "geografiya": 1.5,
            "iqtisodiy_bilim_asoslari": 0.5,
            "ikki_haftalik_slotlar": [
                {"hafta": "toq", "geografiya": 2, "iqtisod": 0},
                {"hafta": "juft", "geografiya": 1, "iqtisod": 1},
            ],
        },
    }


class V198SchoolWorkspaceLinkRequest(BaseModel):
    """V17 muassasasini eski maktab workspace'iga xavfsiz bog'lash so'rovi.

    Frontend tanlangan muassasa IDlarini yuboradi. Eski, xato holatdagi
    frontend umuman ID yubormasa ham joriy foydalanuvchining eng so'nggi
    V17 maktabi topilib tiklanadi.
    """

    organization_v17_id: Optional[int] = None
    context_id: Optional[int] = None
    # Mavjud maktablar ro'yxatidan kirilganda frontend haqiqiy legacy IDni
    # aynan ``maktab_id`` nomi bilan yuboradi. Avval bu maydon qabul
    # qilinmagani uchun mavjud maktab ham yangi maktab oqimiga tushib qolardi.
    maktab_id: Optional[int] = None
    # REV48: productiondagi eski frontend ``selected_id`` yuboradi. Uni
    # tashlab yubormaymiz: agar bu ID foydalanuvchiga tegishli haqiqiy
    # maktab bo'lsa, V17 jadvallariga kirmasdan bevosita shu maktab ochiladi.
    selected_id: Optional[int] = None
    existing_only: bool = False
    create_new: bool = False
    nomi: Optional[str] = None
    viloyat: Optional[str] = None
    tuman: Optional[str] = None
    smena_soni: int = 1


def _v198_existing_school_for_user(
    cur,
    user_id: int,
    preferred_id: Optional[int] = None,
    preferred_name: Optional[str] = None,
):
    """Mavjud legacy maktabni xavfsiz va takror yaratmasdan qaytaradi.

    Tanlangan ro'yxat qatori haqiqiy ``maktab_id`` yuborsa avval shu ID
    tekshiriladi. ID yo'qolgan eski V17 yozuvlarida esa ayni nomdagi va joriy
    foydalanuvchiga tegishli maktab olinadi. Begona maktab faqat umumiy admin
    bo'lsa ochiladi.
    """
    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    is_admin = bool(cur.fetchone())

    candidate_id = 0
    try:
        candidate_id = int(preferred_id or 0)
    except (TypeError, ValueError):
        candidate_id = 0
    if candidate_id > 0:
        cur.execute(
            """SELECT m.id AS maktab_id,m.nomi AS maktab_nomi
                 FROM maktablar m
                WHERE m.id=%s
                  AND (
                    %s OR m.direktor_user_id=%s
                    OR EXISTS(
                      SELECT 1 FROM users u
                       WHERE u.user_id=%s AND u.maktab_id=m.id
                    )
                    OR EXISTS(
                      SELECT 1 FROM foydalanuvchi_muassasalari fm
                       WHERE fm.user_id=%s
                         AND fm.muassasa_turi='maktab'
                         AND fm.muassasa_id=m.id
                    )
                  )
                LIMIT 1""",
            (candidate_id, is_admin, user_id, user_id, user_id),
        )
        row = cur.fetchone()
        if row:
            return row

    school_name = re.sub(r"\s+", " ", str(preferred_name or "")).strip()
    if school_name:
        cur.execute(
            """SELECT m.id AS maktab_id,m.nomi AS maktab_nomi
                 FROM maktablar m
                WHERE lower(trim(m.nomi))=lower(trim(%s))
                  AND (
                    m.direktor_user_id=%s
                    OR EXISTS(
                      SELECT 1 FROM users u
                       WHERE u.user_id=%s AND u.maktab_id=m.id
                    )
                    OR EXISTS(
                      SELECT 1 FROM foydalanuvchi_muassasalari fm
                       WHERE fm.user_id=%s
                         AND fm.muassasa_turi='maktab'
                         AND fm.muassasa_id=m.id
                    )
                  )
                ORDER BY
                  CASE WHEN m.direktor_user_id=%s THEN 0 ELSE 1 END,
                  m.id DESC
                LIMIT 1""",
            (school_name, user_id, user_id, user_id, user_id),
        )
        row = cur.fetchone()
        if row:
            return row

    cur.execute(
        """SELECT m.id AS maktab_id,m.nomi AS maktab_nomi
             FROM users u JOIN maktablar m ON m.id=u.maktab_id
            WHERE u.user_id=%s LIMIT 1""",
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        return row
    cur.execute(
        """SELECT m.id AS maktab_id,m.nomi AS maktab_nomi
             FROM foydalanuvchi_muassasalari fm
             JOIN maktablar m ON m.id=fm.muassasa_id
            WHERE fm.user_id=%s AND fm.muassasa_turi='maktab'
            ORDER BY fm.id DESC LIMIT 1""",
        (user_id,),
    )
    return cur.fetchone()


@app.post("/api/maktab/aqlli_jadval/v3/maktab_workspace_boglash")
def v198_link_school_workspace(
    sorov: V198SchoolWorkspaceLinkRequest,
    token: str,
):
    """Yangi yaratilgan V17 maktabga haqiqiy ``maktablar.id`` beradi.

    Oldingi frontend ``learning_contexts.id`` ni ``maktab_id`` deb yuborgan,
    holbuki maktab dashboardi faqat ``maktablar.id`` bilan ishlaydi. Ushbu
    endpoint organization row'ni bloklab, bir martalik legacy maktab yaratadi,
    external_id ni yozadi va direktor a'zoligini atomar saqlaydi. Bir necha
    marta chaqirilsa yangi maktab ko'paymaydi.
    """
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    try:
        _maktab_jadvali(cur)
        _muassasa_jadvali(cur)

        # REV55: yangi maktabga o'tishdan oldin joriy eski maktabni
        # ko'p-muassasali jadvalga kafolatli yozamiz. Keyingi UPDATE faqat
        # faol workspace ko'rsatkichini almashtiradi; eski maktab va uning
        # ma'lumotlari hamda a'zoligi hech qachon o'chirilmaydi.
        cur.execute(
            "SELECT maktab_id,lavozim FROM users WHERE user_id=%s FOR UPDATE",
            (user_id,),
        )
        current_user = cur.fetchone()
        previous_school_id = (
            int(current_user["maktab_id"])
            if current_user and current_user.get("maktab_id")
            else None
        )
        if previous_school_id:
            cur.execute(
                """INSERT INTO foydalanuvchi_muassasalari(
                       user_id,muassasa_turi,muassasa_id,lavozim
                   ) VALUES(%s,'maktab',%s,%s)
                   ON CONFLICT(user_id,muassasa_turi,muassasa_id)
                   DO UPDATE SET lavozim=EXCLUDED.lavozim""",
                (
                    user_id,
                    previous_school_id,
                    str(current_user.get("lavozim") or "direktor"),
                ),
            )

        # Eski va yangi frontendlar bilan bir xil ishlaydi. Muhim jihat:
        # mavjud maktabni topish V17 schema/helper so'rovlaridan OLDIN
        # bajariladi. Shuning uchun organization_trials/learning_contexts
        # vaqtincha xato qilsa ham eski maktab yangi yaratish oynasiga
        # tushmaydi.
        preferred_school_id = sorov.maktab_id or sorov.selected_id
        requested_school = None
        if preferred_school_id is not None or sorov.existing_only:
            requested_school = _v198_existing_school_for_user(
                cur,
                user_id,
                preferred_id=preferred_school_id,
                preferred_name=sorov.nomi,
            )
        if requested_school:
            maktab_id = int(requested_school["maktab_id"])
            cur.execute(
                """UPDATE users
                      SET maktab_id=%s,
                          lavozim=COALESCE(NULLIF(lavozim,''),'direktor')
                    WHERE user_id=%s""",
                (maktab_id, user_id),
            )
            conn.commit()
            return {
                "holat": (
                    "mavjud_tiklandi"
                    if sorov.existing_only
                    else "mavjud_id_rev48"
                ),
                "maktab_id": maktab_id,
                "maktab_nomi": requested_school["maktab_nomi"],
                "legacy_yaratildi": False,
                "frontend_mosligi": (
                    "selected_id"
                    if sorov.maktab_id is None and sorov.selected_id is not None
                    else "maktab_id"
                ),
            }
        if sorov.existing_only:
            raise HTTPException(
                status_code=404,
                detail="Sizga tegishli mavjud maktab topilmadi.",
            )

        cur.execute(
            """SELECT to_regclass('public.organization_trials') AS trials,
                      to_regclass('public.learning_contexts') AS contexts,
                      to_regclass('public.context_memberships') AS memberships"""
        )
        tables = cur.fetchone() or {}
        organization = None
        explicit_new_school = bool(
            sorov.create_new
            and sorov.organization_v17_id is None
            and sorov.context_id is None
        )
        if tables.get("trials") and tables.get("contexts") and not explicit_new_school:
            access_parts = [
                "EXISTS(SELECT 1 FROM admin_akkaunt aa WHERE aa.uid=%s)",
                "o.creator_user_id=%s",
                "c.owner_user_id=%s",
            ]
            params = [user_id, user_id, user_id]
            if tables.get("memberships"):
                access_parts.append(
                    """EXISTS(
                         SELECT 1 FROM context_memberships cm
                          WHERE cm.context_id=o.context_id
                            AND cm.user_id=%s
                            AND cm.status='active'
                            AND cm.member_role IN ('owner','manager','director','administrator')
                       )"""
                )
                params.append(user_id)
            filters = [f"({' OR '.join(access_parts)})", "o.organization_type='school'"]
            if sorov.organization_v17_id is not None:
                filters.append("o.id=%s")
                params.append(int(sorov.organization_v17_id))
            if sorov.context_id is not None:
                filters.append("o.context_id=%s")
                params.append(int(sorov.context_id))
            cur.execute(
                f"""SELECT o.id AS organization_v17_id,o.context_id,
                           o.display_name,o.lifecycle_status,c.external_id
                      FROM organization_trials o
                      JOIN learning_contexts c ON c.id=o.context_id
                     WHERE {' AND '.join(filters)}
                     ORDER BY o.id DESC LIMIT 1
                     FOR UPDATE OF o,c""",
                tuple(params),
            )
            organization = cur.fetchone()

        if organization is None:
            if sorov.organization_v17_id is not None or sorov.context_id is not None:
                # V17 bog'lanish yozuvi yo'qolgan bo'lsa mavjud legacy maktabni
                # nomi yoki foydalanuvchining faol maktabi orqali tiklaymiz.
                # Bu holatda HECH QACHON yangi maktab yaratmaymiz.
                existing = _v198_existing_school_for_user(
                    cur,
                    user_id,
                    preferred_id=sorov.maktab_id or sorov.selected_id,
                    preferred_name=sorov.nomi,
                )
                if existing:
                    maktab_id = int(existing["maktab_id"])
                    cur.execute(
                        """UPDATE users
                              SET maktab_id=%s,
                                  lavozim=COALESCE(NULLIF(lavozim,''),'direktor')
                            WHERE user_id=%s""",
                        (maktab_id, user_id),
                    )
                    conn.commit()
                    return {
                        "holat": "mavjud_tiklandi",
                        "maktab_id": maktab_id,
                        "maktab_nomi": existing["maktab_nomi"],
                        "legacy_yaratildi": False,
                    }
                raise HTTPException(
                    status_code=404,
                    detail="Tanlangan maktab topilmadi yoki u sizga tegishli emas.",
                )
            if sorov.create_new:
                school_name = str(sorov.nomi or "").strip()
                if not school_name:
                    raise HTTPException(
                        status_code=400,
                        detail="Yangi maktab nomini kiriting.",
                    )
                if int(sorov.smena_soni or 1) not in (1, 2):
                    raise HTTPException(
                        status_code=400,
                        detail="Smena soni 1 yoki 2 bo‘lishi kerak.",
                    )

                # Bir foydalanuvchining ikki marta tez bosishi ikki maktab
                # yaratmasin. Users qatori transaction tugaguncha bloklanadi;
                # ayni nomdagi juda yangi yozuv xavfsiz retry deb olinadi.
                cur.execute(
                    "SELECT user_id FROM users WHERE user_id=%s FOR UPDATE",
                    (user_id,),
                )
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi.")
                cur.execute(
                    """SELECT id,nomi FROM maktablar
                        WHERE direktor_user_id=%s
                          AND lower(trim(nomi))=lower(trim(%s))
                          AND yaratilgan_at >= NOW() - INTERVAL '2 minutes'
                        ORDER BY id DESC LIMIT 1""",
                    (user_id, school_name),
                )
                linked_school = cur.fetchone()
                created = linked_school is None
                if linked_school:
                    maktab_id = int(linked_school["id"])
                else:
                    cur.execute(
                        """INSERT INTO maktablar(
                               nomi,viloyat,tuman,smena_soni,direktor_user_id,
                               pulli,oylik_tolov
                           ) VALUES(%s,%s,%s,%s,%s,FALSE,NULL)
                           RETURNING id""",
                        (
                            school_name,
                            str(sorov.viloyat or "").strip() or None,
                            str(sorov.tuman or "").strip() or None,
                            int(sorov.smena_soni or 1),
                            user_id,
                        ),
                    )
                    maktab_id = int(cur.fetchone()["id"])
                cur.execute(
                    """INSERT INTO foydalanuvchi_muassasalari(
                           user_id,muassasa_turi,muassasa_id,lavozim
                       ) VALUES(%s,'maktab',%s,'direktor')
                       ON CONFLICT(user_id,muassasa_turi,muassasa_id)
                       DO UPDATE SET lavozim='direktor'""",
                    (user_id, maktab_id),
                )
                # Yangi yaratilgan/tanlangan maktab joriy faol maktab bo‘ladi.
                # COALESCE eski maktab ID sini saqlab qolib, yangi workspace'ni
                # yana eski maktabga qaytarayotgan edi.
                cur.execute(
                    """UPDATE users
                          SET maktab_id=%s,
                              lavozim=COALESCE(NULLIF(lavozim,''),'direktor')
                        WHERE user_id=%s""",
                    (maktab_id, user_id),
                )
                conn.commit()
                return {
                    "holat": "yaratildi" if created else "mavjud_retry",
                    "maktab_id": maktab_id,
                    "maktab_nomi": school_name,
                    "legacy_yaratildi": created,
                }
            existing = _v198_existing_school_for_user(cur, user_id)
            if not existing:
                raise HTTPException(
                    status_code=404,
                    detail="Sizga tegishli maktab topilmadi. Maktabni qayta tanlang yoki yangisini yarating.",
                )
            conn.commit()
            return {
                "holat": "mavjud",
                "maktab_id": int(existing["maktab_id"]),
                "maktab_nomi": existing["maktab_nomi"],
                "legacy_yaratildi": False,
            }

        maktab_id = None
        if organization.get("external_id") is not None:
            try:
                candidate_id = int(organization["external_id"])
            except (TypeError, ValueError):
                candidate_id = 0
            if candidate_id > 0:
                cur.execute(
                    "SELECT id,nomi FROM maktablar WHERE id=%s",
                    (candidate_id,),
                )
                linked_school = cur.fetchone()
                if linked_school:
                    maktab_id = int(linked_school["id"])

        created = False
        school_name = str(organization.get("display_name") or "Yangi maktab").strip()
        if maktab_id is None:
            # V17 external_id yo'q bo'lsa ham avval ayni nomdagi mavjud
            # maktabni qidiramiz. Faqat rostdan ham topilmasa yangi yozuv
            # yaratiladi; eski maktabga kirishda dublikat paydo bo'lmaydi.
            existing = _v198_existing_school_for_user(
                cur,
                user_id,
                preferred_id=sorov.maktab_id,
                preferred_name=school_name,
            )
            if existing:
                maktab_id = int(existing["maktab_id"])
                school_name = existing["maktab_nomi"]
            else:
                cur.execute(
                    """INSERT INTO maktablar(
                           nomi,smena_soni,direktor_user_id,pulli,oylik_tolov
                       ) VALUES(%s,1,%s,FALSE,NULL) RETURNING id""",
                    (school_name, user_id),
                )
                maktab_id = int(cur.fetchone()["id"])
                created = True
            cur.execute(
                "UPDATE learning_contexts SET external_id=%s WHERE id=%s",
                (maktab_id, int(organization["context_id"])),
            )

        cur.execute(
            """INSERT INTO foydalanuvchi_muassasalari(
                   user_id,muassasa_turi,muassasa_id,lavozim
               ) VALUES(%s,'maktab',%s,'direktor')
               ON CONFLICT(user_id,muassasa_turi,muassasa_id)
               DO UPDATE SET lavozim='direktor'""",
            (user_id, maktab_id),
        )
        cur.execute(
            """UPDATE users
                  SET maktab_id=%s,
                      lavozim=COALESCE(NULLIF(lavozim,''),'direktor')
                WHERE user_id=%s""",
            (maktab_id, user_id),
        )
        cur.execute(
            """UPDATE maktablar
                  SET direktor_user_id=COALESCE(direktor_user_id,%s)
                WHERE id=%s""",
            (user_id, maktab_id),
        )
        # external_id avval mavjud bo'lsa ham normal integer qiymatga keladi.
        cur.execute(
            "UPDATE learning_contexts SET external_id=%s WHERE id=%s",
            (maktab_id, int(organization["context_id"])),
        )
        conn.commit()
        return {
            "holat": "boglandi",
            "maktab_id": maktab_id,
            "maktab_nomi": school_name,
            "organization_v17_id": int(organization["organization_v17_id"]),
            "context_id": int(organization["context_id"]),
            "legacy_yaratildi": created,
            "lifecycle_status": organization.get("lifecycle_status"),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _v192_clean_subject(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


# O'zbekiston Respublikasi Maktabgacha va maktab ta'limi vazirining
# 2026-yil 10-apreldagi 133-son buyrug'i, 1-ilova (o'zbek tilidagi maktablar).
# Bu ikki konstanta avvalgi monolitdan modulga ajratishda tushib qolgan edi.
# Ular modul importi paytida kerak: bo'lmasa Railway yangi deployni
# ``NameError: SAMTM_2026_2027_UZBEK_CURRICULUM`` bilan to'xtatadi.
SAMTM_2026_2027_UZBEK_CURRICULUM = (
    ("Ona tili", {1: 4, 2: 4, 3: 4, 4: 4, 5: 4, 6: 4, 7: 3, 8: 3, 9: 3, 10: 2, 11: 2}),
    ("O'qish savodxonligi", {1: 4, 2: 3, 3: 3, 4: 3}),
    ("Adabiyot", {5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2}),
    ("Rus tili", {2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2}),
    ("Chet tili", {1: 1, 2: 2, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 8: 3, 9: 3, 10: 2, 11: 2}),
    ("Tarixdan hikoyalar", {5: 2}),
    ("Qadimgi dunyo tarixi", {6: 2}),
    ("O'zbekiston tarixi", {7: 2, 8: 2, 9: 2, 10: 1, 11: 1}),
    ("Jahon tarixi", {7: 1, 8: 1, 9: 1, 10: 1, 11: 1}),
    ("Davlat va huquq asoslari", {8: 1, 9: 1, 10: 1, 11: 1}),
    ("Tarbiya", {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1, 11: 1}),
    ("Matematika", {1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 5, 7: 5}),
    ("Algebra", {8: 3, 9: 3, 10: 3, 11: 3}),
    ("Geometriya", {8: 2, 9: 2, 10: 2, 11: 2}),
    ("Informatika va axborot texnologiyalari", {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 2, 11: 2}),
    ("Fizika", {7: 2, 8: 2, 9: 2, 10: 2, 11: 2}),
    ("Astronomiya", {11: 1}),
    ("Kimyo", {7: 2, 8: 2, 9: 2, 10: 2, 11: 2}),
    ("Biologiya", {7: 2, 8: 2, 9: 2, 10: 2, 11: 2}),
    ("Geografiya", {7: 2, 8: 1.5, 9: 1.5, 10: 2}),
    ("Iqtisodiy bilim asoslari", {8: 0.5, 9: 0.5}),
    ("Tadbirkorlik asoslari", {11: 1}),
    ("Tabiiy fan (Science)", {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 3}),
    ("Musiqa madaniyati", {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}),
    ("Tasviriy san'at", {1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1}),
    ("Chizmachilik", {8: 1, 9: 1}),
    ("Texnologiya", {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 2, 8: 1, 9: 1}),
    ("Jismoniy tarbiya", {1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2}),
    ("Chaqiruvga qadar boshlang'ich tayyorgarlik", {10: 2, 11: 2}),
)

SAMTM_2026_2027_CURRICULUM_SOURCE = {
    "nomi": "2026-2027 tayanch o'quv reja",
    "buyruq": "MMTV 133-son",
    "sana": "2026-04-10",
    "ilova": "1-ilova",
    "talim_tili": "o'zbek",
    "sinf_jami": {
        1: 21, 2: 24, 3: 24, 4: 24, 5: 29, 6: 30,
        7: 35, 8: 33, 9: 34, 10: 31, 11: 31,
    },
}


SAMTM_V19_3_DEFAULT_CURRICULUM = SAMTM_2026_2027_UZBEK_CURRICULUM


def _v201_central_school_settings_tables(cur):
    """Admin boshqaradigan, yil nomiga qotirilmagan maktab andozasi."""
    cur.execute("""CREATE TABLE IF NOT EXISTS admin_maktab_andoza_versiyalari_v20_1(
        id BIGSERIAL PRIMARY KEY,
        nomi TEXT NOT NULL DEFAULT 'Amaldagi maktab andozasi',
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        yangilagan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
    cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS uq_admin_maktab_andoza_faol_v20_1
                   ON admin_maktab_andoza_versiyalari_v20_1(faol) WHERE faol=TRUE""")
    cur.execute("""CREATE TABLE IF NOT EXISTS admin_maktab_andoza_fanlari_v20_1(
        id BIGSERIAL PRIMARY KEY,
        versiya_id BIGINT NOT NULL REFERENCES admin_maktab_andoza_versiyalari_v20_1(id) ON DELETE CASCADE,
        sinf_darajasi INTEGER NOT NULL CHECK(sinf_darajasi BETWEEN 1 AND 11),
        fan_nomi TEXT NOT NULL,
        fan_kaliti TEXT NOT NULL,
        haftalik_soat NUMERIC(4,1) NOT NULL DEFAULT 0 CHECK(haftalik_soat BETWEEN 0 AND 20),
        metod_kuni INTEGER CHECK(metod_kuni BETWEEN 1 AND 7),
        kunlik_max INTEGER NOT NULL DEFAULT 1 CHECK(kunlik_max BETWEEN 1 AND 4),
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        tartib INTEGER NOT NULL DEFAULT 0,
        UNIQUE(versiya_id,sinf_darajasi,fan_kaliti)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS maktab_andoza_override_v20_1(
        maktab_id INTEGER NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
        bolim TEXT NOT NULL CHECK(bolim IN ('fanlar','oquv_reja','metod_kunlari')),
        alohida BOOLEAN NOT NULL DEFAULT FALSE,
        yangilagan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY(maktab_id,bolim)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS admin_maktab_andoza_tasdiqlari_v20_2(
        versiya_id BIGINT NOT NULL REFERENCES admin_maktab_andoza_versiyalari_v20_1(id) ON DELETE CASCADE,
        bolim TEXT NOT NULL CHECK(bolim IN ('fanlar','yuklama','jadval','metod')),
        tasdiqlangan BOOLEAN NOT NULL DEFAULT FALSE,
        tasdiqlagan_user_id BIGINT,
        tasdiqlangan_at TIMESTAMPTZ,
        PRIMARY KEY(versiya_id,bolim)
    )""")
    cur.execute("SELECT id FROM admin_maktab_andoza_versiyalari_v20_1 WHERE faol=TRUE LIMIT 1")
    version = cur.fetchone()
    if version:
        version_id = int(version["id"])
        for section in ("fanlar", "yuklama", "jadval", "metod"):
            cur.execute("""INSERT INTO admin_maktab_andoza_tasdiqlari_v20_2(
                            versiya_id,bolim,tasdiqlangan)
                           VALUES(%s,%s,TRUE) ON CONFLICT DO NOTHING""",
                        (version_id, section))
        return version_id
    cur.execute("""INSERT INTO admin_maktab_andoza_versiyalari_v20_1(nomi,faol)
                   VALUES('Amaldagi maktab andozasi',TRUE) RETURNING id""")
    version_id = int(cur.fetchone()["id"])
    order = 0
    for subject, grades in SAMTM_V19_3_DEFAULT_CURRICULUM:
        for grade, hours in grades.items():
            cur.execute("""INSERT INTO admin_maktab_andoza_fanlari_v20_1(
                            versiya_id,sinf_darajasi,fan_nomi,fan_kaliti,
                            haftalik_soat,kunlik_max,tartib)
                           VALUES(%s,%s,%s,%s,%s,1,%s)""",
                        (version_id, int(grade), subject,
                         _v1875_subject_key(subject), float(hours), order))
        order += 1
    for section in ("fanlar", "yuklama", "jadval", "metod"):
        cur.execute("""INSERT INTO admin_maktab_andoza_tasdiqlari_v20_2(
                        versiya_id,bolim,tasdiqlangan)
                       VALUES(%s,%s,TRUE)""", (version_id, section))
    return version_id


def _v201_central_rows(cur):
    version_id = _v201_central_school_settings_tables(cur)
    cur.execute("""SELECT sinf_darajasi,fan_nomi,haftalik_soat,metod_kuni,
                          kunlik_max,tartib
                     FROM admin_maktab_andoza_fanlari_v20_1
                    WHERE versiya_id=%s AND faol=TRUE
                    ORDER BY sinf_darajasi,tartib,fan_nomi""", (version_id,))
    return [dict(row) for row in cur.fetchall()]


def _v201_central_curriculum(cur):
    grouped = {}
    names = {}
    for row in _v201_central_rows(cur):
        key = _v1875_subject_key(row["fan_nomi"])
        names[key] = row["fan_nomi"]
        grouped.setdefault(key, {})[int(row["sinf_darajasi"])] = float(row["haftalik_soat"])
    return tuple((names[key], grades) for key, grades in grouped.items())


def _v201_mark_school_override(cur, maktab_id: int, section: str, actor_id: int):
    _v201_central_school_settings_tables(cur)
    cur.execute("""INSERT INTO maktab_andoza_override_v20_1(
                    maktab_id,bolim,alohida,yangilagan_user_id,yangilangan_at)
                   VALUES(%s,%s,TRUE,%s,NOW())
                   ON CONFLICT(maktab_id,bolim) DO UPDATE SET
                     alohida=TRUE,yangilagan_user_id=EXCLUDED.yangilagan_user_id,
                     yangilangan_at=NOW()""", (maktab_id, section, actor_id))


class V201CentralSubjectRow(BaseModel):
    sinf_darajasi: int
    fan_nomi: str
    haftalik_soat: float = 0
    metod_kuni: Optional[int] = None
    kunlik_max: int = 1


class V201CentralSchoolSettings(BaseModel):
    qatorlar: list[V201CentralSubjectRow]
    bolim: str = "fanlar"
    tasdiqlash: bool = True


@app.on_event("startup")
def _v201_central_school_settings_startup():
    try:
        conn = _db(); cur = conn.cursor()
        _v201_central_school_settings_tables(cur)
        conn.commit(); cur.close(); conn.close()
    except Exception as exc:
        print(f"[V20.1 markaziy maktab sozlamasi] {exc}", flush=True)


@app.get("/api/admin/maktab_markaziy_sozlamalari")
def v201_central_school_settings_get(token: str):
    _admin_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        version_id = _v201_central_school_settings_tables(cur)
        rows = _v201_central_rows(cur)
        cur.execute("""SELECT bolim,tasdiqlangan,tasdiqlangan_at
                         FROM admin_maktab_andoza_tasdiqlari_v20_2
                        WHERE versiya_id=%s""", (version_id,))
        approvals = {row["bolim"]: {
            "tasdiqlangan": bool(row["tasdiqlangan"]),
            "tasdiqlangan_at": row["tasdiqlangan_at"],
        } for row in cur.fetchall()}
        return {
            "nomi": "Amaldagi maktab andozasi",
            "qatorlar": rows,
            "sinf_fanlari": {
                str(grade): [row["fan_nomi"] for row in rows if int(row["sinf_darajasi"]) == grade]
                for grade in range(1, 12)
            },
            "tasdiqlar": approvals,
        }
    finally:
        cur.close(); conn.close()


@app.put("/api/admin/maktab_markaziy_sozlamalari")
def v201_central_school_settings_save(sorov: V201CentralSchoolSettings, token: str):
    actor_id = _admin_tekshir(token)
    section = str(sorov.bolim or "").strip().lower()
    if section not in {"fanlar", "yuklama", "jadval", "metod"}:
        raise HTTPException(status_code=400, detail="Sozlama bo‘limi noto‘g‘ri")
    normalized = []
    seen = set()
    for index, item in enumerate(sorov.qatorlar):
        grade = int(item.sinf_darajasi)
        subject = _v192_clean_subject(item.fan_nomi)
        key = _v1875_subject_key(subject)
        hours = float(item.haftalik_soat)
        method_day = int(item.metod_kuni) if item.metod_kuni is not None else None
        daily_max = int(item.kunlik_max)
        if grade not in range(1, 12) or not key:
            raise HTTPException(status_code=400, detail="Sinf yoki fan nomi noto‘g‘ri")
        if (grade, key) in seen:
            raise HTTPException(status_code=400, detail=f"{grade}-sinf / {subject} takrorlangan")
        if not 0 <= hours <= 20 or daily_max not in range(1, 5):
            raise HTTPException(status_code=400, detail=f"{grade}-sinf / {subject} soati noto‘g‘ri")
        if method_day is not None and method_day not in range(1, 8):
            raise HTTPException(status_code=400, detail=f"{subject} metod kuni noto‘g‘ri")
        seen.add((grade, key))
        normalized.append((grade, subject, key, hours, method_day, daily_max, index))
    if not normalized:
        raise HTTPException(status_code=400, detail="Kamida bitta sinf–fan qatori kerak")
    conn = _db(); cur = conn.cursor()
    try:
        version_id = _v201_central_school_settings_tables(cur)
        cur.execute("DELETE FROM admin_maktab_andoza_fanlari_v20_1 WHERE versiya_id=%s", (version_id,))
        for row in normalized:
            cur.execute("""INSERT INTO admin_maktab_andoza_fanlari_v20_1(
                            versiya_id,sinf_darajasi,fan_nomi,fan_kaliti,
                            haftalik_soat,metod_kuni,kunlik_max,tartib)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""", (version_id, *row))
        cur.execute("""UPDATE admin_maktab_andoza_versiyalari_v20_1
                          SET yangilagan_user_id=%s,yangilangan_at=NOW() WHERE id=%s""",
                    (actor_id, version_id))
        cur.execute("""UPDATE admin_maktab_andoza_tasdiqlari_v20_2
                          SET tasdiqlangan=FALSE,tasdiqlagan_user_id=NULL,tasdiqlangan_at=NULL
                        WHERE versiya_id=%s AND bolim=%s""", (version_id, section))
        if section == "fanlar":
            cur.execute("""UPDATE admin_maktab_andoza_tasdiqlari_v20_2
                              SET tasdiqlangan=FALSE,tasdiqlagan_user_id=NULL,tasdiqlangan_at=NULL
                            WHERE versiya_id=%s AND bolim IN ('yuklama','jadval','metod')""",
                        (version_id,))
        if sorov.tasdiqlash:
            cur.execute("""UPDATE admin_maktab_andoza_tasdiqlari_v20_2
                              SET tasdiqlangan=TRUE,tasdiqlagan_user_id=%s,tasdiqlangan_at=NOW()
                            WHERE versiya_id=%s AND bolim=%s""",
                        (actor_id, version_id, section))
        # Markaziy o'zgarish faqat alohida sozlama qilmagan maktablarga
        # tarqaladi. Ularning keyingi ochilishida reja yangi andozadan qayta
        # quriladi; maxsus maktab sozlamasi hech qachon bosib ketilmaydi.
        cur.execute("SELECT id FROM maktablar ORDER BY id")
        schools = [int(row["id"]) for row in cur.fetchall()]
        fan_updated = plan_updated = method_updated = 0
        for school_id in schools:
            cur.execute("""SELECT bolim FROM maktab_andoza_override_v20_1
                            WHERE maktab_id=%s AND alohida=TRUE""", (school_id,))
            overrides = {row["bolim"] for row in cur.fetchall()}
            if "fanlar" not in overrides:
                cur.execute("DELETE FROM maktab_fan_sinflari_v19_4 WHERE maktab_id=%s", (school_id,))
                fan_updated += 1
            if "oquv_reja" not in overrides:
                cur.execute("DELETE FROM aqlli_oquv_reja_qatorlari_v19_3 WHERE maktab_id=%s", (school_id,))
                cur.execute("""UPDATE aqlli_oquv_reja_holati_v19_3
                                  SET holat='draft',versiya=versiya+1,
                                      tasdiqlagan_user_id=NULL,tasdiqlangan_at=NULL,
                                      yangilangan_at=NOW() WHERE maktab_id=%s""", (school_id,))
                cur.execute("""UPDATE aqlli_jadval_urinishlari_v2 SET holat='bekor'
                                WHERE maktab_id=%s AND holat='draft'""", (school_id,))
                plan_updated += 1
            if "metod_kunlari" not in overrides:
                cur.execute("DELETE FROM aqlli_metod_fan_qoidalari_v2 WHERE maktab_id=%s", (school_id,))
                cur.execute("""SELECT yoqilgan FROM aqlli_metod_avto_sozlamalari_v2
                                WHERE maktab_id=%s""", (school_id,))
                enabled = bool((cur.fetchone() or {}).get("yoqilgan"))
                if enabled:
                    _v1873_apply_official(cur, school_id, replace_existing=True)
                method_updated += 1
        conn.commit()
        return {"holat": "tasdiqlandi" if sorov.tasdiqlash else "saqlandi",
                "bolim": section, "qator_soni": len(normalized),
                "maktablar": {"fanlar": fan_updated, "oquv_reja": plan_updated,
                              "metod_kunlari": method_updated},
                "izoh": "Alohida override qilmagan maktablar bu andozani avtomatik oladi."}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def _v193_grade_number(value):
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else 0


def _v201_school_has_override(cur, maktab_id: int, section: str) -> bool:
    """Maktab markaziy andozadan aynan shu bo'limda chetlaganmi."""
    _v201_central_school_settings_tables(cur)
    cur.execute("""SELECT 1 FROM maktab_andoza_override_v20_1
                   WHERE maktab_id=%s AND bolim=%s AND alohida=TRUE""",
                (maktab_id, section))
    return bool(cur.fetchone())


def _v194_school_subject_grades(cur, maktab_id: int):
    """None — eski maktab; dict — fanlar sinflar bo'yicha aniq sozlangan."""
    if not _v201_school_has_override(cur, maktab_id, "fanlar"):
        central_result = {}
        for row in _v201_central_rows(cur):
            grade = int(row["sinf_darajasi"])
            central_result.setdefault(grade, {})[
                _v1875_subject_key(row["fan_nomi"])
            ] = row["fan_nomi"]
        return central_result or None
    cur.execute("SELECT to_regclass('public.maktab_fan_sinflari_v19_4') AS jadval")
    if not (cur.fetchone() or {}).get("jadval"):
        return None
    cur.execute("""SELECT fan_nomi,sinf_darajasi
                   FROM maktab_fan_sinflari_v19_4
                   WHERE maktab_id=%s ORDER BY sinf_darajasi,fan_nomi""", (maktab_id,))
    rows = cur.fetchall()
    if not rows:
        # Yangi maktab DTSdagi tasodifiy nomlardan emas, admin tasdiqlagan
        # markaziy 1–11-sinf andozasidan boshlaydi.
        central_result = {}
        for row in _v201_central_rows(cur):
            grade = int(row["sinf_darajasi"])
            central_result.setdefault(grade, {})[
                _v1875_subject_key(row["fan_nomi"])
            ] = row["fan_nomi"]
        return central_result or None
    result = {}
    for row in rows:
        grade = int(row["sinf_darajasi"])
        result.setdefault(grade, {})[_v1875_subject_key(row["fan_nomi"])] = row["fan_nomi"]
    return result


def _v193_template_rows_for_class(class_row, selected_by_grade=None, curriculum=None):
    grade = _v193_grade_number(class_row.get("sinf"))
    allowed = (selected_by_grade or {}).get(grade) if selected_by_grade is not None else None
    default_hours = {
        _v1875_subject_key(subject): float(hours.get(grade, 0) or 0)
        for subject, hours in (curriculum or SAMTM_V19_3_DEFAULT_CURRICULUM)
    }
    if allowed is not None:
        # O'quv reja ustunlari faqat maktab 1–11-sinflar uchun saqlagan
        # fanlardan tuziladi. Tayanchda topilmagan yangi fan ham yo'qolmaydi:
        # u 0 soat bilan ko'rinadi va rahbariyat soatini qo'lda kiritadi.
        return [
            {
                "sinf_id": int(class_row["id"]),
                "fan_nomi": subject,
                "haftalik_soat": default_hours.get(key, 0.0),
                "kunlik_max": 1,
                "manba": "amaldagi_tayanch_reja" if default_hours.get(key, 0) > 0 else "maktab_fan_tanlovi",
            }
            for key, subject in allowed.items()
        ]
    return [
        {
            "sinf_id": int(class_row["id"]),
            "fan_nomi": subject,
            "haftalik_soat": float(hours[grade]),
            "kunlik_max": 1,
            "manba": "amaldagi_tayanch_reja",
        }
        for subject, hours in (curriculum or SAMTM_V19_3_DEFAULT_CURRICULUM)
        if float(hours.get(grade, 0)) > 0
    ]


def _v193_ensure_plan(cur, maktab_id: int, classes):
    selected_by_grade = _v194_school_subject_grades(cur, maktab_id)
    curriculum = _v201_central_curriculum(cur)
    cur.execute("""INSERT INTO aqlli_oquv_reja_holati_v19_3(maktab_id)
                   VALUES(%s) ON CONFLICT(maktab_id) DO NOTHING""", (maktab_id,))
    central_plan = not _v201_school_has_override(cur, maktab_id, "oquv_reja")
    cur.execute("""SELECT sinf_id,fan_nomi,haftalik_soat
                   FROM aqlli_oquv_reja_qatorlari_v19_3 WHERE maktab_id=%s""",
                (maktab_id,))
    saved_rows = cur.fetchall()
    existing = {int(row["sinf_id"]) for row in saved_rows}
    if central_plan:
        expected_rows = []
        for class_row in classes:
            expected_rows.extend(
                row for row in _v193_template_rows_for_class(
                    class_row, selected_by_grade, curriculum
                ) if float(row["haftalik_soat"] or 0) > 0
            )
        saved_signature = {
            (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"]),
             round(float(row["haftalik_soat"] or 0), 3))
            for row in saved_rows
        }
        expected_signature = {
            (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"]),
             round(float(row["haftalik_soat"] or 0), 3))
            for row in expected_rows
        }
        if saved_signature != expected_signature:
            cur.execute("DELETE FROM aqlli_oquv_reja_qatorlari_v19_3 WHERE maktab_id=%s",
                        (maktab_id,))
            for item in expected_rows:
                cur.execute("""INSERT INTO aqlli_oquv_reja_qatorlari_v19_3(
                                maktab_id,sinf_id,fan_nomi,haftalik_soat,
                                kunlik_max,manba,yangilangan_at)
                               VALUES(%s,%s,%s,%s,%s,%s,NOW())""",
                            (maktab_id, item["sinf_id"], item["fan_nomi"],
                             item["haftalik_soat"], item["kunlik_max"], item["manba"]))
                cur.execute("""INSERT INTO maktab_fanlari(maktab_id,fan_nomi)
                               VALUES(%s,%s) ON CONFLICT DO NOTHING""",
                            (maktab_id, item["fan_nomi"]))
            cur.execute("""UPDATE aqlli_oquv_reja_holati_v19_3
                           SET holat='draft',versiya=versiya+1,
                               tasdiqlagan_user_id=NULL,tasdiqlangan_at=NULL,
                               yangilangan_at=NOW() WHERE maktab_id=%s""", (maktab_id,))
            return
    missing = [row for row in classes if int(row["id"]) not in existing]
    if not missing:
        return
    for class_row in missing:
        template_rows = _v193_template_rows_for_class(class_row, selected_by_grade, curriculum)
        for item in template_rows:
            if float(item["haftalik_soat"] or 0) <= 0:
                continue
            cur.execute("""INSERT INTO aqlli_oquv_reja_qatorlari_v19_3(
                            maktab_id,sinf_id,fan_nomi,haftalik_soat,
                            kunlik_max,manba,yangilangan_at)
                           VALUES(%s,%s,%s,%s,%s,%s,NOW())
                           ON CONFLICT(maktab_id,sinf_id,fan_nomi) DO NOTHING""",
                        (
                            maktab_id, item["sinf_id"], item["fan_nomi"],
                            item["haftalik_soat"], item["kunlik_max"], item["manba"],
                        ))
        for item in template_rows:
            cur.execute("""INSERT INTO maktab_fanlari(maktab_id,fan_nomi)
                           VALUES(%s,%s) ON CONFLICT DO NOTHING""",
                        (maktab_id, item["fan_nomi"]))
    cur.execute("""UPDATE aqlli_oquv_reja_holati_v19_3
                   SET holat='draft',tasdiqlagan_user_id=NULL,
                       tasdiqlangan_at=NULL,yangilangan_at=NOW()
                   WHERE maktab_id=%s""", (maktab_id,))


def _v193_plan_payload(cur, maktab_id: int, classes):
    _v193_ensure_plan(cur, maktab_id, classes)
    selected_by_grade = _v194_school_subject_grades(cur, maktab_id)
    curriculum = _v201_central_curriculum(cur)
    cur.execute("""SELECT holat,versiya,tasdiqlagan_user_id,
                          tasdiqlangan_at,yangilangan_at
                   FROM aqlli_oquv_reja_holati_v19_3 WHERE maktab_id=%s""",
                (maktab_id,))
    status = dict(cur.fetchone() or {})
    cur.execute("""SELECT id,sinf_id,fan_nomi,haftalik_soat,kunlik_max,
                          manba,yangilangan_at
                   FROM aqlli_oquv_reja_qatorlari_v19_3
                   WHERE maktab_id=%s
                   ORDER BY sinf_id,fan_nomi""", (maktab_id,))
    rows = [dict(row) for row in cur.fetchall()]
    if selected_by_grade is not None:
        class_grades = {int(row["id"]): _v193_grade_number(row.get("sinf")) for row in classes}
        rows = [
            row for row in rows
            if _v1875_subject_key(row["fan_nomi"])
            in selected_by_grade.get(class_grades.get(int(row["sinf_id"]), 0), {})
        ]
    class_totals = {}
    for row in rows:
        class_id = int(row["sinf_id"])
        class_totals[class_id] = class_totals.get(class_id, 0.0) + float(row["haftalik_soat"])
    cur.execute("""SELECT sinf_id,fan_nomi,haftalik_soat FROM aqlli_sinf_soati_qoidalari_v2
                   WHERE maktab_id=%s AND faol=TRUE""", (maktab_id,))
    class_hour_rows = {int(row["sinf_id"]): dict(row) for row in cur.fetchall()}
    template_rows = []
    for class_row in classes:
        template_rows.extend(_v193_template_rows_for_class(class_row, selected_by_grade, curriculum))
    active_year = _v1852_active_year(cur, maktab_id)
    active_year_name = str((active_year or {}).get("nomi") or "").strip()
    return {
        "holat": status.get("holat") or "draft",
        "versiya": int(status.get("versiya") or 1),
        "tasdiqlangan_at": status.get("tasdiqlangan_at"),
        "yangilangan_at": status.get("yangilangan_at"),
        # UI yilni koddan emas, maktabning faol o'quv yilidan oladi.
        # Shu sabab keyingi o'quv yilida frontend kodi almashtirilmaydi.
        "oquv_yili_nomi": active_year_name,
        "andoza_nomi": "Amaldagi tayanch o‘quv reja",
        "andoza_manbasi": SAMTM_2026_2027_CURRICULUM_SOURCE,
        "markaziy_andoza": not _v201_school_has_override(cur, maktab_id, "oquv_reja"),
        "sinf_soati_avtomatik": True,
        "sinf_soati_haftalik": 1,
        "sinf_soati_nomi": next((row.get("fan_nomi") for row in class_hour_rows.values()), "KELAJAK SOATI"),
        "qatorlar": rows,
        "andoza_qatorlar": template_rows,
        "sinf_jami": [
            {
                "sinf_id": int(class_row["id"]),
                "sinf": f"{class_row['sinf']}-{class_row['harf']}",
                "fan_soati": float(class_totals.get(int(class_row["id"]), 0)),
                "sinf_soati": int(class_hour_rows.get(int(class_row["id"]), {}).get("haftalik_soat") or 0),
                "sinf_soati_nomi": class_hour_rows.get(int(class_row["id"]), {}).get("fan_nomi") or "KELAJAK SOATI",
                "haftalik_soat": float(class_totals.get(int(class_row["id"]), 0))
                + int(class_hour_rows.get(int(class_row["id"]), {}).get("haftalik_soat") or 0),
            }
            for class_row in classes
        ],
        "tanlangan_fan_sinflari": [
            {"sinf_darajasi": grade, "fanlar": list(subjects.values())}
            for grade, subjects in sorted((selected_by_grade or {}).items())
        ],
    }


def _v193_approved_plan_map(cur, maktab_id: int):
    cur.execute("""SELECT holat FROM aqlli_oquv_reja_holati_v19_3
                   WHERE maktab_id=%s""", (maktab_id,))
    status = cur.fetchone()
    if not status or status.get("holat") != "tasdiqlangan":
        return None
    cur.execute("""SELECT sinf_id,fan_nomi,haftalik_soat,kunlik_max
                   FROM aqlli_oquv_reja_qatorlari_v19_3
                   WHERE maktab_id=%s""", (maktab_id,))
    return {
        (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"])): dict(row)
        for row in cur.fetchall()
    }


def _v192_group_variants(cur, maktab_id: int):
    systems = _v1876_group_system_catalog(cur, maktab_id)
    cur.execute("""SELECT s.id,s.sinf,s.harf,COALESCE(s.smena,1) AS smena,
                          s.bino,s.xona,
                          s.rahbar_user_id,COALESCE(u.full_name,'') AS rahbar_ismi
                   FROM maktab_sinflari s
                   LEFT JOIN users u ON u.user_id=s.rahbar_user_id
                   WHERE s.maktab_id=%s
                   ORDER BY CASE WHEN s.sinf::text ~ '^\\d+$' THEN s.sinf::int ELSE 999 END,s.harf""",
                (maktab_id,))
    classes = [dict(row) for row in cur.fetchall()]
    systems_by_class = {}
    for system in systems:
        systems_by_class.setdefault(int(system["sinf_id"]), []).append(system)

    result = []
    for cls in classes:
        class_id = int(cls["id"])
        class_name = f"{cls['sinf']}-{cls['harf']}"
        result.append({
            "sinf_id": class_id,
            "sinf": class_name,
            "guruh_kaliti": "whole",
            "guruh_nomi": "Butun sinf",
            "qisqa": class_name,
            "turi": "whole",
            "tizim_id": None,
            "fanlar": [],
        })
        seen = set()
        for system in systems_by_class.get(class_id, []):
            for group in system.get("guruhlar") or []:
                key = str(group.get("guruh_kaliti") or "").strip()
                if not key or key in seen:
                    continue
                seen.add(key)
                short = {
                    "group_1": "1G",
                    "group_2": "2G",
                    "boys": "O‘",
                    "girls": "Q",
                }.get(key, str(group.get("guruh_nomi") or key)[:8])
                result.append({
                    "sinf_id": class_id,
                    "sinf": class_name,
                    "guruh_kaliti": key,
                    "guruh_nomi": str(group.get("guruh_nomi") or key),
                    "qisqa": short,
                    "turi": str(system.get("turi") or "manual"),
                    "tizim_id": int(system["id"]),
                    "fanlar": list(system.get("fanlar") or []),
                })
    return classes, systems, result


def _v192_assignment_rows(cur, maktab_id: int):
    cur.execute("""SELECT b.id,b.maktab_id,b.user_id,b.sinf_id,b.fan_nomi,
                          COALESCE(NULLIF(b.guruh_kaliti,''),'whole') AS guruh_kaliti,
                          COALESCE(b.haftalik_soat,0) AS haftalik_soat,
                          COALESCE(b.kunlik_max,1) AS kunlik_max,b.xona_id,
                          COALESCE(b.manba,'noma_lum') AS manba,
                          u.full_name,s.sinf,s.harf,COALESCE(s.smena,1) AS smena
                   FROM maktab_dars_birikmalari b
                   JOIN users u ON u.user_id=b.user_id
                   JOIN maktab_sinflari s ON s.id=b.sinf_id
                   WHERE b.maktab_id=%s
                   ORDER BY u.full_name,s.sinf::int,s.harf,b.fan_nomi,b.guruh_kaliti""",
                (maktab_id,))
    return [dict(row) for row in cur.fetchall()]


def _v192_totals(cur, maktab_id: int, rows, classes):
    teacher_base = {}
    class_subject = {}
    for row in rows:
        hours = max(0.0, float(row.get("haftalik_soat") or 0))
        teacher_id = int(row["user_id"])
        teacher_base[teacher_id] = teacher_base.get(teacher_id, 0) + hours
        pair = (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"]))
        data = class_subject.setdefault(pair, {"whole": [], "groups": [], "fan_nomi": row["fan_nomi"]})
        if _v1875_group_key(row.get("guruh_kaliti")) == "whole":
            data["whole"].append(hours)
        else:
            data["groups"].append(hours)

    cur.execute("""SELECT q.sinf_id,q.haftalik_soat,s.rahbar_user_id
                   FROM aqlli_sinf_soati_qoidalari_v2 q
                   JOIN maktab_sinflari s ON s.id=q.sinf_id
                   WHERE q.maktab_id=%s AND q.faol=TRUE""", (maktab_id,))
    class_hour_extra = {}
    class_hour_classes = set()
    for row in cur.fetchall():
        class_hour_classes.add(int(row["sinf_id"]))
        teacher_id = row.get("rahbar_user_id")
        if teacher_id is not None:
            class_hour_extra[int(teacher_id)] = class_hour_extra.get(int(teacher_id), 0) + int(row.get("haftalik_soat") or 1)

    class_totals = {int(cls["id"]): 0 for cls in classes}
    subject_totals = []
    warnings = []
    for (class_id, _), data in class_subject.items():
        if data["whole"] and data["groups"]:
            warnings.append(f"{data['fan_nomi']}: butun sinf va guruh qatori birga yozilgan")
        if data["groups"]:
            values = [value for value in data["groups"] if value > 0]
            weekly = max(values, default=0)
            if len(set(values)) > 1:
                warnings.append(f"{data['fan_nomi']}: parallel guruh soatlari teng emas")
        else:
            weekly = sum(data["whole"])
        class_totals[class_id] = class_totals.get(class_id, 0) + weekly
        subject_totals.append({
            "sinf_id": class_id,
            "fan_nomi": data["fan_nomi"],
            "haftalik_soat": weekly,
        })
    for class_id in class_hour_classes:
        class_totals[class_id] = class_totals.get(class_id, 0) + 1
        subject_totals.append({
            "sinf_id": class_id,
            "fan_nomi": "SINF SOATI",
            "haftalik_soat": 1,
        })

    year = _v1852_active_year(cur, maktab_id)
    school_days = 0
    school_weeks = 0.0
    if year:
        current = year["boshlanish"]
        end = year["tugash"]
        weekdays = int(year.get("hafta_kunlari") or 6)
        while current <= end:
            if _v1852_is_school_day(cur, maktab_id, current, weekdays):
                school_days += 1
            current += timedelta(days=1)
        school_weeks = round(school_days / max(1, weekdays), 2)

    teacher_totals = []
    cur.execute("SELECT user_id,full_name FROM users WHERE maktab_id=%s ORDER BY full_name", (maktab_id,))
    for teacher in cur.fetchall():
        teacher_id = int(teacher["user_id"])
        base = round(float(teacher_base.get(teacher_id, 0)), 1)
        extra = int(class_hour_extra.get(teacher_id, 0))
        teacher_totals.append({
            "user_id": teacher_id,
            "full_name": teacher["full_name"],
            "fan_soati": base,
            "sinf_soati": extra,
            "haftalik_jami": base + extra,
        })

    school_weekly = sum(class_totals.values())
    return {
        "oqituvchilar": teacher_totals,
        "sinflar": [
            {
                "sinf_id": int(cls["id"]),
                "sinf": f"{cls['sinf']}-{cls['harf']}",
                "haftalik_soat": round(float(class_totals.get(int(cls["id"]), 0)), 1),
                "yillik_soat": round(float(class_totals.get(int(cls["id"]), 0)) * school_weeks, 1),
            }
            for cls in classes
        ],
        "fanlar": subject_totals,
        "maktab_haftalik_soat": school_weekly,
        "maktab_yillik_soat": round(school_weekly * school_weeks),
        "oquv_kuni": school_days,
        "oquv_haftasi": school_weeks,
        "oqituvchi_soat_jami": sum(item["haftalik_jami"] for item in teacher_totals),
        "ogohlantirishlar": list(dict.fromkeys(warnings)),
    }


def _v192_matrix_payload(cur, maktab_id: int):
    classes, systems, variants = _v192_group_variants(cur, maktab_id)
    plan = _v193_plan_payload(cur, maktab_id, classes)
    selected_by_grade = _v194_school_subject_grades(cur, maktab_id)
    rows = _v192_assignment_rows(cur, maktab_id)
    variant_names = {
        (int(row["sinf_id"]), str(row["guruh_kaliti"])): row
        for row in variants
    }
    for row in rows:
        variant = variant_names.get(
            (int(row["sinf_id"]), _v1875_group_key(row.get("guruh_kaliti")))
        )
        row["guruh_nomi"] = (variant or {}).get("guruh_nomi", row["guruh_kaliti"])
        row["guruh_qisqa"] = (variant or {}).get("qisqa", row["guruh_kaliti"])
        row["sinf_nomi"] = f"{row['sinf']}-{row['harf']}"

    teachers = _v1859_effective_teachers(cur, maktab_id)
    cur.execute("SELECT fan_nomi FROM maktab_fanlari WHERE maktab_id=%s ORDER BY fan_nomi", (maktab_id,))
    subjects = [row["fan_nomi"] for row in cur.fetchall()]
    cur.execute("SELECT * FROM aqlli_xonalar_v2 WHERE maktab_id=%s AND faol=TRUE AND darsga_yaroqli=TRUE ORDER BY nomi", (maktab_id,))
    rooms = [dict(row) for row in cur.fetchall()]
    cur.execute("""SELECT avtomatik_tavsiya FROM aqlli_jadval_boshqaruv_v19_2
                   WHERE maktab_id=%s""", (maktab_id,))
    mode = cur.fetchone()
    return {
        "versiya": "teacher-first-approved-curriculum-v19.3",
        "paket": "all-14-sections-updated",
        "sinflar": classes,
        "oqituvchilar": teachers,
        "fanlar": subjects,
        "fan_sinflari": [
            {
                "sinf_id": int(cls["id"]),
                "sinf_darajasi": _v193_grade_number(cls.get("sinf")),
                "fanlar": list((selected_by_grade or {}).get(
                    _v193_grade_number(cls.get("sinf")), {}
                ).values()) if selected_by_grade is not None else subjects,
            }
            for cls in classes
        ],
        "xonalar": rooms,
        "guruh_variantlari": variants,
        "birikmalar": rows,
        "oquv_reja": plan,
        "hisob": _v192_totals(cur, maktab_id, rows, classes),
        "avtomatik_tavsiya": (
            SAMTM_V19_2_AUTO_SWAP_DEFAULT
            if not mode else bool(mode["avtomatik_tavsiya"])
        ),
    }


@app.get("/api/maktab/aqlli_jadval/v3/yuklama_matritsasi")
def v192_load_matrix(token: str, maktab_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_staff(cur, actor_id, maktab_id):
            raise HTTPException(status_code=403, detail="Bu maktab yuklamasini ko'rishga ruxsat yo'q")
        payload = _v192_matrix_payload(cur, maktab_id)
        conn.commit()
        return payload
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V193CurriculumItem(BaseModel):
    fan_nomi: str
    haftalik_soat: float
    kunlik_max: int = 1


class V193CurriculumClassSave(BaseModel):
    maktab_id: int
    sinf_id: int
    fanlar: list[V193CurriculumItem]


class V193CurriculumMatrixItem(BaseModel):
    sinf_id: int
    fan_nomi: str
    haftalik_soat: float
    kunlik_max: int = 1


class V193CurriculumMatrixSave(BaseModel):
    maktab_id: int
    qatorlar: list[V193CurriculumMatrixItem]


class V193CurriculumAction(BaseModel):
    maktab_id: int


class V20ClassHourPlanItem(BaseModel):
    sinf_id: int
    fan_nomi: str = "KELAJAK SOATI"
    haftalik_soat: int = 1


class V20ClassHourPlanSave(BaseModel):
    maktab_id: int
    qatorlar: list[V20ClassHourPlanItem] = []


@app.put("/api/maktab/aqlli_jadval/v3/oquv_reja/sinf_soati")
def v20_class_hour_plan_save(sorov: V20ClassHourPlanSave, token: str):
    """Kelajak soati nomi, soati va qaysi sinflarga tegishliligini saqlaydi."""
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Kelajak soatini faqat rahbariyat boshqaradi")
        _v201_mark_school_override(cur, sorov.maktab_id, "oquv_reja", actor_id)
        cur.execute("SELECT id FROM maktab_sinflari WHERE maktab_id=%s", (sorov.maktab_id,))
        valid_ids = {int(row["id"]) for row in cur.fetchall()}
        received = set()
        for item in sorov.qatorlar:
            class_id = int(item.sinf_id)
            if class_id not in valid_ids:
                raise HTTPException(status_code=400, detail="Kelajak soati uchun begona sinf yuborildi")
            name = _v192_clean_subject(item.fan_nomi) or "KELAJAK SOATI"
            hours = int(item.haftalik_soat)
            if hours not in range(1, 6):
                raise HTTPException(status_code=400, detail="Kelajak soati haftasiga 1–5 soat bo‘lishi mumkin")
            received.add(class_id)
            cur.execute("""INSERT INTO aqlli_sinf_soati_qoidalari_v2(
                            maktab_id,sinf_id,hafta_kuni,dars_raqami,faol,
                            yaratgan_user_id,fan_nomi,haftalik_soat,yangilangan_at)
                           VALUES(%s,%s,5,1,TRUE,%s,%s,%s,NOW())
                           ON CONFLICT(maktab_id,sinf_id) DO UPDATE SET
                             faol=TRUE,fan_nomi=EXCLUDED.fan_nomi,
                             haftalik_soat=EXCLUDED.haftalik_soat,
                             yaratgan_user_id=EXCLUDED.yaratgan_user_id,yangilangan_at=NOW()""",
                        (sorov.maktab_id, class_id, actor_id, name, hours))
        if received:
            cur.execute("""UPDATE aqlli_sinf_soati_qoidalari_v2 SET faol=FALSE,yangilangan_at=NOW()
                           WHERE maktab_id=%s AND NOT(sinf_id=ANY(%s))""",
                        (sorov.maktab_id, list(received)))
        else:
            cur.execute("UPDATE aqlli_sinf_soati_qoidalari_v2 SET faol=FALSE,yangilangan_at=NOW() WHERE maktab_id=%s", (sorov.maktab_id,))
        conn.commit()
        return {"holat": "saqlandi", "faol_sinf_soni": len(received)}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def _v195_refresh_teacher_summary(cur, maktab_id: int, user_id: int):
    """Aniq birikmalardan o'qituvchining fan, sinf va jami soatini qayta quradi."""
    cur.execute("""SELECT b.sinf_id,b.fan_nomi,COALESCE(b.haftalik_soat,0) AS haftalik_soat,
                          s.sinf,s.harf
                   FROM maktab_dars_birikmalari b
                   JOIN maktab_sinflari s ON s.id=b.sinf_id
                   WHERE b.maktab_id=%s AND b.user_id=%s
                   ORDER BY s.sinf::int,s.harf,b.fan_nomi,b.guruh_kaliti""",
                (maktab_id, user_id))
    rows = [dict(row) for row in cur.fetchall()]
    cur.execute("DELETE FROM maktab_xodim_sinflari WHERE maktab_id=%s AND user_id=%s",
                (maktab_id, user_id))
    by_class = {}
    for row in rows:
        by_class.setdefault(int(row["sinf_id"]), []).append(row["fan_nomi"])
    for class_id, subjects in by_class.items():
        unique_subjects = list(dict.fromkeys(subjects))
        cur.execute("""INSERT INTO maktab_xodim_sinflari(
                        maktab_id,user_id,sinf_id,fanlari)
                       VALUES(%s,%s,%s,%s)""",
                    (maktab_id, user_id, class_id, "; ".join(unique_subjects)))
    subject_list = sorted(
        {row["fan_nomi"] for row in rows}, key=lambda value: value.casefold()
    )
    class_list = sorted(
        {f"{row['sinf']}-{row['harf']}" for row in rows},
        key=_v1859_sinf_sort_key,
    )
    weekly_total = round(sum(float(row.get("haftalik_soat") or 0) for row in rows), 1)
    cur.execute("""UPDATE users
                   SET fanlari=%s,haftalik_dars_soati=%s,oqitadigan_sinflari=%s
                   WHERE user_id=%s AND maktab_id=%s""",
                (
                    "; ".join(subject_list) or None,
                    weekly_total,
                    "; ".join(class_list) or None,
                    user_id,
                    maktab_id,
                ))
    return weekly_total


def _v195_reconcile_teacher_loads_with_plan(cur, maktab_id: int):
    """Tasdiqlanayotgan reja bilan eski o'qituvchi yuklamalarini moslashtiradi."""
    cur.execute("""SELECT sinf_id,fan_nomi,haftalik_soat
                   FROM aqlli_oquv_reja_qatorlari_v19_3
                   WHERE maktab_id=%s""", (maktab_id,))
    plan = {
        (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"])): dict(row)
        for row in cur.fetchall()
    }
    cur.execute("""SELECT id,user_id,sinf_id,fan_nomi,
                          COALESCE(NULLIF(guruh_kaliti,''),'whole') AS guruh_kaliti,
                          COALESCE(haftalik_soat,0) AS haftalik_soat
                   FROM maktab_dars_birikmalari
                   WHERE maktab_id=%s
                   ORDER BY sinf_id,fan_nomi,guruh_kaliti,id""", (maktab_id,))
    assignments = [dict(row) for row in cur.fetchall()]
    remaining = {}
    affected_users = set()
    deleted = 0
    reduced = 0
    renamed = 0
    for row in assignments:
        affected_users.add(int(row["user_id"]))
        pair = (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"]))
        plan_row = plan.get(pair)
        if not plan_row:
            cur.execute("DELETE FROM maktab_dars_birikmalari WHERE id=%s", (row["id"],))
            deleted += 1
            continue
        exact = (pair[0], pair[1], _v1875_group_key(row.get("guruh_kaliti")))
        if exact not in remaining:
            remaining[exact] = float(plan_row.get("haftalik_soat") or 0)
        old_hours = max(0.0, float(row.get("haftalik_soat") or 0))
        new_hours = min(old_hours, max(0.0, float(remaining[exact])))
        if new_hours <= 0:
            cur.execute("DELETE FROM maktab_dars_birikmalari WHERE id=%s", (row["id"],))
            deleted += 1
            continue
        canonical_subject = str(plan_row["fan_nomi"])
        if new_hours != old_hours or canonical_subject != row["fan_nomi"]:
            cur.execute("""UPDATE maktab_dars_birikmalari
                           SET fan_nomi=%s,haftalik_soat=%s,yangilangan_at=NOW()
                           WHERE id=%s""",
                        (canonical_subject, new_hours, row["id"]))
            if new_hours != old_hours:
                reduced += 1
            if canonical_subject != row["fan_nomi"]:
                renamed += 1
        remaining[exact] -= new_hours
    for user_id in affected_users:
        _v195_refresh_teacher_summary(cur, maktab_id, user_id)
    return {
        "ochirilgan_qator": deleted,
        "qisqartirilgan_qator": reduced,
        "nomi_moslangan_qator": renamed,
        "oqituvchi_soni": len(affected_users),
    }


@app.put("/api/maktab/aqlli_jadval/v3/oquv_reja")
def v193_curriculum_save(sorov: V193CurriculumClassSave, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="O'quv rejasini faqat rahbariyat boshqaradi")
        _v201_mark_school_override(cur, sorov.maktab_id, "oquv_reja", actor_id)
        cur.execute("""SELECT id,sinf,harf FROM maktab_sinflari
                       WHERE id=%s AND maktab_id=%s FOR UPDATE""",
                    (sorov.sinf_id, sorov.maktab_id))
        class_row = cur.fetchone()
        if not class_row:
            raise HTTPException(status_code=404, detail="Sinf topilmadi")
        selected_by_grade = _v194_school_subject_grades(cur, sorov.maktab_id)
        allowed = (selected_by_grade or {}).get(_v193_grade_number(class_row.get("sinf")), {})
        received = set()
        cleaned = []
        for index, item in enumerate(sorov.fanlar, start=1):
            subject = _v192_clean_subject(item.fan_nomi)
            if not subject:
                raise HTTPException(status_code=400, detail=f"{index}-qator: fan nomi kiritilmagan")
            key = _v1875_subject_key(subject)
            if key == "sinf soati":
                raise HTTPException(
                    status_code=400,
                    detail="SINF SOATI fan qatoriga yozilmaydi; u har sinfga avtomatik 1 soat qo'shiladi",
                )
            if key in allowed:
                subject = allowed[key]
            if key in received:
                raise HTTPException(status_code=400, detail=f"{subject}: reja qatorida ikki marta yozilgan")
            received.add(key)
            hours = float(item.haftalik_soat)
            daily = int(item.kunlik_max)
            if hours < 0.5 or hours > 20 or hours * 2 != int(hours * 2):
                raise HTTPException(status_code=400, detail=f"{subject}: haftalik soat 0,5–20 oralig'ida, 0,5 qadam bilan bo'lishi kerak")
            if daily < 1 or daily > 4:
                raise HTTPException(status_code=400, detail=f"{subject}: kunlik maksimum 1–4 bo'lishi kerak")
            cleaned.append((subject, hours, daily))
        if not cleaned:
            raise HTTPException(status_code=400, detail="Sinf o'quv rejasida kamida bitta fan bo'lishi kerak")
        total = sum(row[1] for row in cleaned)
        if total > 60:
            raise HTTPException(status_code=400, detail="Sinfning haftalik reja soati 60 dan oshmasligi kerak")
        cur.execute("""INSERT INTO aqlli_oquv_reja_holati_v19_3(maktab_id)
                       VALUES(%s) ON CONFLICT(maktab_id) DO NOTHING""", (sorov.maktab_id,))
        cur.execute("""DELETE FROM aqlli_oquv_reja_qatorlari_v19_3
                       WHERE maktab_id=%s AND sinf_id=%s""",
                    (sorov.maktab_id, sorov.sinf_id))
        for subject, hours, daily in cleaned:
            cur.execute("""INSERT INTO aqlli_oquv_reja_qatorlari_v19_3(
                            maktab_id,sinf_id,fan_nomi,haftalik_soat,
                            kunlik_max,manba,yangilangan_at)
                           VALUES(%s,%s,%s,%s,%s,'qolda',NOW())""",
                        (sorov.maktab_id, sorov.sinf_id, subject, hours, daily))
            cur.execute("""INSERT INTO maktab_fanlari(maktab_id,fan_nomi)
                           VALUES(%s,%s) ON CONFLICT DO NOTHING""",
                        (sorov.maktab_id, subject))
            cur.execute("""INSERT INTO maktab_fan_sinflari_v19_4(maktab_id,fan_nomi,sinf_darajasi)
                           VALUES(%s,%s,%s) ON CONFLICT DO NOTHING""",
                        (sorov.maktab_id, subject, _v193_grade_number(class_row.get("sinf"))))
        cur.execute("""UPDATE aqlli_oquv_reja_holati_v19_3
                       SET holat='draft',versiya=versiya+1,
                           tasdiqlagan_user_id=NULL,tasdiqlangan_at=NULL,
                           yangilangan_at=NOW() WHERE maktab_id=%s""",
                    (sorov.maktab_id,))
        cur.execute("""UPDATE aqlli_jadval_urinishlari_v2 SET holat='bekor'
                       WHERE maktab_id=%s AND holat='draft'""", (sorov.maktab_id,))
        class_hour_result = _v199_ensure_class_hour_rules(
            cur, sorov.maktab_id, [sorov.sinf_id], actor_id
        )
        result = _v192_matrix_payload(cur, sorov.maktab_id)
        conn.commit()
        return {
            "holat": "draft_saqlandi",
            "sinf": f"{class_row['sinf']}-{class_row['harf']}",
            "fan_soni": len(cleaned),
            "haftalik_jami": total,
            "sinf_soati": class_hour_result,
            "matritsa": result,
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.put("/api/maktab/aqlli_jadval/v3/oquv_reja/matritsa")
def v193_curriculum_matrix_save(sorov: V193CurriculumMatrixSave, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="O'quv rejasini faqat rahbariyat boshqaradi")
        _v201_mark_school_override(cur, sorov.maktab_id, "oquv_reja", actor_id)
        cur.execute("""SELECT id,sinf,harf FROM maktab_sinflari
                       WHERE maktab_id=%s
                       ORDER BY CASE WHEN sinf::text ~ '^\\d+$' THEN sinf::int ELSE 999 END,harf
                       FOR UPDATE""",
                    (sorov.maktab_id,))
        classes = [dict(row) for row in cur.fetchall()]
        valid_classes = {int(row["id"]): row for row in classes}
        selected_by_grade = _v194_school_subject_grades(cur, sorov.maktab_id)
        if not valid_classes:
            raise HTTPException(status_code=400, detail="Maktabda birorta ham sinf topilmadi")
        if not sorov.qatorlar:
            raise HTTPException(status_code=400, detail="O'quv reja matritsasi bo'sh")
        seen = set()
        cleaned = []
        class_totals = {class_id: 0 for class_id in valid_classes}
        for index, item in enumerate(sorov.qatorlar, start=1):
            class_id = int(item.sinf_id)
            if class_id not in valid_classes:
                raise HTTPException(status_code=400, detail=f"{index}-qator: sinf bu maktabga tegishli emas")
            subject = _v192_clean_subject(item.fan_nomi)
            if not subject:
                raise HTTPException(status_code=400, detail=f"{index}-qator: fan nomi kiritilmagan")
            subject_key = _v1875_subject_key(subject)
            if subject_key == "sinf soati":
                raise HTTPException(
                    status_code=400,
                    detail="SINF SOATI fan qatoriga yozilmaydi; u har sinfga avtomatik 1 soat qo'shiladi",
                )
            allowed = (selected_by_grade or {}).get(
                _v193_grade_number(valid_classes[class_id].get("sinf")), {}
            )
            if subject_key in allowed:
                subject = allowed[subject_key]
            hours = float(item.haftalik_soat)
            daily = int(item.kunlik_max)
            if hours < 0.5 or hours > 20 or hours * 2 != int(hours * 2):
                raise HTTPException(status_code=400, detail=f"{subject}: haftalik soat 0,5–20 oralig'ida, 0,5 qadam bilan bo'lishi kerak")
            if daily < 1 or daily > 4:
                raise HTTPException(status_code=400, detail=f"{subject}: kunlik maksimum 1–4 bo'lishi kerak")
            key = (class_id, _v1875_subject_key(subject))
            if key in seen:
                raise HTTPException(
                    status_code=400,
                    detail=f"{valid_classes[class_id]['sinf']}-{valid_classes[class_id]['harf']} / {subject}: ikki marta yuborilgan",
                )
            seen.add(key)
            class_totals[class_id] += hours
            if class_totals[class_id] > 60:
                cls = valid_classes[class_id]
                raise HTTPException(
                    status_code=400,
                    detail=f"{cls['sinf']}-{cls['harf']}: haftalik jami 60 soatdan oshdi",
                )
            cleaned.append((class_id, subject, hours, daily))
        cur.execute("""INSERT INTO aqlli_oquv_reja_holati_v19_3(maktab_id)
                       VALUES(%s) ON CONFLICT(maktab_id) DO NOTHING""", (sorov.maktab_id,))
        cur.execute("DELETE FROM aqlli_oquv_reja_qatorlari_v19_3 WHERE maktab_id=%s",
                    (sorov.maktab_id,))
        for class_id, subject, hours, daily in cleaned:
            cur.execute("""INSERT INTO aqlli_oquv_reja_qatorlari_v19_3(
                            maktab_id,sinf_id,fan_nomi,haftalik_soat,
                            kunlik_max,manba,yangilangan_at)
                           VALUES(%s,%s,%s,%s,%s,'matritsa',NOW())""",
                        (sorov.maktab_id, class_id, subject, hours, daily))
            cur.execute("""INSERT INTO maktab_fanlari(maktab_id,fan_nomi)
                           VALUES(%s,%s) ON CONFLICT DO NOTHING""",
                        (sorov.maktab_id, subject))
            cur.execute("""INSERT INTO maktab_fan_sinflari_v19_4(maktab_id,fan_nomi,sinf_darajasi)
                           VALUES(%s,%s,%s) ON CONFLICT DO NOTHING""",
                        (sorov.maktab_id, subject,
                         _v193_grade_number(valid_classes[class_id].get("sinf"))))
        cur.execute("""UPDATE aqlli_oquv_reja_holati_v19_3
                       SET holat='draft',versiya=versiya+1,
                           tasdiqlagan_user_id=NULL,tasdiqlangan_at=NULL,
                           yangilangan_at=NOW() WHERE maktab_id=%s""",
                    (sorov.maktab_id,))
        cur.execute("""UPDATE aqlli_jadval_urinishlari_v2 SET holat='bekor'
                       WHERE maktab_id=%s AND holat='draft'""", (sorov.maktab_id,))
        class_hour_result = _v199_ensure_class_hour_rules(
            cur, sorov.maktab_id, valid_classes.keys(), actor_id
        )
        matrix = _v192_matrix_payload(cur, sorov.maktab_id)
        conn.commit()
        return {
            "holat": "matritsa_draft_saqlandi",
            "sinf_soni": len(valid_classes),
            "fan_qatori": len(cleaned),
            "maktab_haftalik_jami": sum(class_totals.values()),
            "sinf_soati": class_hour_result,
            "matritsa": matrix,
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.post("/api/maktab/aqlli_jadval/v3/oquv_reja/tasdiqlash")
def v193_curriculum_approve(sorov: V193CurriculumAction, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="O'quv rejasini faqat rahbariyat tasdiqlaydi")
        classes, _systems, _variants = _v192_group_variants(cur, sorov.maktab_id)
        _v193_ensure_plan(cur, sorov.maktab_id, classes)
        cur.execute("""SELECT sinf_id,COUNT(*) AS fan_soni,SUM(haftalik_soat) AS jami
                       FROM aqlli_oquv_reja_qatorlari_v19_3
                       WHERE maktab_id=%s GROUP BY sinf_id""", (sorov.maktab_id,))
        totals = {int(row["sinf_id"]): row for row in cur.fetchall()}
        missing = [
            f"{row['sinf']}-{row['harf']}"
            for row in classes
            if int(row["id"]) not in totals or int(totals[int(row["id"])].get("jami") or 0) < 1
        ]
        if missing:
            raise HTTPException(
                status_code=400,
                detail="Reja fanlari kiritilmagan sinflar: " + ", ".join(missing[:20]),
            )
        cur.execute("""UPDATE aqlli_sinf_fan_yuklamalari_v2
                       SET haftalik_soat=0,asosiy_oqituvchi_user_id=NULL
                       WHERE maktab_id=%s""", (sorov.maktab_id,))
        cur.execute("""SELECT sinf_id,fan_nomi,haftalik_soat,kunlik_max
                       FROM aqlli_oquv_reja_qatorlari_v19_3
                       WHERE maktab_id=%s""", (sorov.maktab_id,))
        plan_rows = cur.fetchall()
        for row in plan_rows:
            cur.execute("""INSERT INTO aqlli_sinf_fan_yuklamalari_v2(
                            maktab_id,sinf_id,fan_nomi,haftalik_soat,kunlik_max)
                           VALUES(%s,%s,%s,%s,%s)
                           ON CONFLICT(maktab_id,sinf_id,fan_nomi) DO UPDATE SET
                             haftalik_soat=EXCLUDED.haftalik_soat,
                             kunlik_max=EXCLUDED.kunlik_max""",
                        (
                            sorov.maktab_id, row["sinf_id"], row["fan_nomi"],
                            row["haftalik_soat"], row["kunlik_max"],
                        ))
        cur.execute("""UPDATE aqlli_oquv_reja_holati_v19_3
                       SET holat='tasdiqlangan',tasdiqlagan_user_id=%s,
                           tasdiqlangan_at=NOW(),yangilangan_at=NOW()
                       WHERE maktab_id=%s""", (actor_id, sorov.maktab_id))
        reconcile = _v195_reconcile_teacher_loads_with_plan(cur, sorov.maktab_id)
        class_hour_result = _v199_ensure_class_hour_rules(
            cur, sorov.maktab_id, [row["id"] for row in classes], actor_id
        )
        sync_warnings = _v192_sync_schedule_sources(cur, sorov.maktab_id)
        if reconcile["ochirilgan_qator"]:
            sync_warnings.append(
                f"O'quv rejada qolmagan {reconcile['ochirilgan_qator']} ta eski o'qituvchi yuklama qatori olib tashlandi"
            )
        if reconcile["qisqartirilgan_qator"]:
            sync_warnings.append(
                f"{reconcile['qisqartirilgan_qator']} ta o'qituvchi yuklamasi yangi reja soatidan oshmaguncha qisqartirildi"
            )
        cur.execute("""UPDATE aqlli_jadval_urinishlari_v2 SET holat='bekor'
                       WHERE maktab_id=%s AND holat='draft'""", (sorov.maktab_id,))
        result = _v192_matrix_payload(cur, sorov.maktab_id)
        conn.commit()
        return {
            "holat": "tasdiqlangan",
            "sinf_soni": len(classes),
            "fan_qatori": len(plan_rows),
            "yuklama_moslash": reconcile,
            "sinf_soati": class_hour_result,
            "ogohlantirishlar": sync_warnings,
            "matritsa": result,
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V192TeacherLoadRow(BaseModel):
    sinf_id: int
    fan_nomi: str
    guruh_kaliti: str = "whole"
    haftalik_soat: float
    kunlik_max: int = 1
    xona_id: Optional[int] = None


class V192TeacherLoadSave(BaseModel):
    maktab_id: int
    user_id: int
    mutaxassisligi: Optional[str] = None
    otadigan_fanlari: Optional[list[str]] = None
    haftalik_maqsad_soat: Optional[float] = None
    tugilgan_sana: Optional[date] = None
    tugilgan_yili: Optional[int] = None
    ish_staji: Optional[int] = None
    toifasi: Optional[str] = None
    rahbar_sinf_id: Optional[int] = None
    qatorlar: list[V192TeacherLoadRow]


class V192ManualTeacherCreate(BaseModel):
    maktab_id: int
    full_name: str
    mutaxassisligi: Optional[str] = None
    otadigan_fanlari: Optional[list[str]] = None
    haftalik_maqsad_soat: Optional[float] = None
    tugilgan_sana: Optional[date] = None
    tugilgan_yili: Optional[int] = None
    ish_staji: Optional[int] = None
    toifasi: Optional[str] = None
    rahbar_sinf_id: Optional[int] = None
    qatorlar: list[V192TeacherLoadRow]


def _v194_teacher_profile_values(mutaxassisligi, haftalik_maqsad_soat):
    specialty = re.sub(r"\s+", " ", str(mutaxassisligi or "")).strip() or None
    if specialty and len(specialty) > 120:
        raise HTTPException(status_code=400, detail="Mutaxassislik nomi 120 ta belgidan oshmasligi kerak")
    target = haftalik_maqsad_soat
    if target is not None:
        target = round(float(target), 1)
        if target < 0.5 or target > 60 or abs(target * 2 - round(target * 2)) > 1e-9:
            raise HTTPException(
                status_code=400,
                detail="Haftalik maqsad soati 0,5–60 oralig'ida va 0,5 qadamda bo'lishi kerak",
            )
    return specialty, target


def _v199_save_teacher_leadership(cur, maktab_id: int, user_id: int,
                                  rahbar_sinf_id, actor_id: int):
    """O'qituvchining bitta sinf rahbarligini va uning 1 soat sinf soatini saqlaydi."""
    leader_class = None
    if rahbar_sinf_id is not None:
        cur.execute("""SELECT id,sinf,harf,rahbar_user_id
                       FROM maktab_sinflari
                       WHERE id=%s AND maktab_id=%s FOR UPDATE""",
                    (int(rahbar_sinf_id), int(maktab_id)))
        leader_class = cur.fetchone()
        if not leader_class:
            raise HTTPException(status_code=404, detail="Sinf rahbarligi uchun tanlangan sinf topilmadi")
        current_leader = leader_class.get("rahbar_user_id")
        if current_leader is not None and int(current_leader) != int(user_id):
            raise HTTPException(
                status_code=409,
                detail=f"{leader_class['sinf']}-{leader_class['harf']} sinfiga boshqa rahbar tayinlangan",
            )
    cur.execute("""UPDATE maktab_sinflari SET rahbar_user_id=NULL
                   WHERE maktab_id=%s AND rahbar_user_id=%s
                     AND (%s::INTEGER IS NULL OR id<>%s::INTEGER)""",
                (maktab_id, user_id, rahbar_sinf_id, rahbar_sinf_id))
    if leader_class:
        cur.execute("""UPDATE maktab_sinflari SET rahbar_user_id=%s
                       WHERE id=%s AND maktab_id=%s""",
                    (user_id, int(leader_class["id"]), maktab_id))
        _v199_ensure_class_hour_rules(
            cur, maktab_id, [int(leader_class["id"])], actor_id
        )
    return leader_class


def _v199_teacher_total_with_class_hour(cur, maktab_id: int, user_id: int, result: dict):
    fan_hours = round(float(result.get("haftalik_jami") or 0), 1)
    cur.execute("""SELECT COALESCE(SUM(q.haftalik_soat),0) AS son
                   FROM aqlli_sinf_soati_qoidalari_v2 q
                   JOIN maktab_sinflari s ON s.id=q.sinf_id
                   WHERE q.maktab_id=%s AND q.faol=TRUE AND s.rahbar_user_id=%s""",
                (maktab_id, user_id))
    class_hours = int((cur.fetchone() or {}).get("son") or 0)
    result["fan_soati"] = fan_hours
    result["sinf_soati"] = class_hours
    result["haftalik_jami"] = round(fan_hours + class_hours, 1)
    return result


def _v192_sync_schedule_sources(cur, maktab_id: int):
    rows = _v192_assignment_rows(cur, maktab_id)
    pairs = {}
    for row in rows:
        subject = _v192_clean_subject(row["fan_nomi"])
        pair = pairs.setdefault(
            (int(row["sinf_id"]), _v1875_subject_key(subject)),
            {"sinf_id": int(row["sinf_id"]), "fan_nomi": subject, "rows": []},
        )
        pair["rows"].append(row)

    approved_plan = _v193_approved_plan_map(cur, maktab_id)
    if approved_plan is None:
        cur.execute("""UPDATE aqlli_sinf_fan_yuklamalari_v2
                       SET haftalik_soat=0,asosiy_oqituvchi_user_id=NULL
                       WHERE maktab_id=%s""", (maktab_id,))
        cur.execute("DELETE FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s", (maktab_id,))
        return [
            "O'qituvchi yuklamasi qo'lda saqlandi. O'quv reja tasdiqlanmagani uchun avtomatik soat va dars jadvali manbasi hali yoqilmadi"
        ]
    else:
        # Tasdiqlangan rejada hali o'qituvchi biriktirilmagan fanlarning
        # soati yo'qolmaydi. Faqat aniq birikma bor fanlar quyida yangilanadi.
        cur.execute("""UPDATE aqlli_sinf_fan_yuklamalari_v2
                       SET asosiy_oqituvchi_user_id=NULL
                       WHERE maktab_id=%s""", (maktab_id,))
    cur.execute("DELETE FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s", (maktab_id,))
    warnings = []
    for pair in pairs.values():
        whole = [row for row in pair["rows"] if _v1875_group_key(row.get("guruh_kaliti")) == "whole"]
        groups = [row for row in pair["rows"] if _v1875_group_key(row.get("guruh_kaliti")) != "whole"]
        if whole and groups:
            warnings.append(
                f"{pair['fan_nomi']}: butun sinf va guruh qatorlari birga yozilgan"
            )
        active = groups if groups else whole
        hours = [max(0.0, float(row.get("haftalik_soat") or 0)) for row in active]
        weekly = max(hours, default=0) if groups else sum(hours)
        daily = max([int(row.get("kunlik_max") or 1) for row in active], default=1)
        if groups and len(set(value for value in hours if value > 0)) > 1:
            warnings.append(
                f"{pair['fan_nomi']}: parallel guruhlar haftalik soati teng emas"
            )
        primary = int(whole[0]["user_id"]) if len(whole) == 1 and not groups else None
        room = int(whole[0]["xona_id"]) if len(whole) == 1 and whole[0].get("xona_id") else None
        cur.execute("""INSERT INTO aqlli_sinf_fan_yuklamalari_v2(
                        maktab_id,sinf_id,fan_nomi,haftalik_soat,kunlik_max,
                        asosiy_oqituvchi_user_id,xona_id)
                       VALUES(%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT(maktab_id,sinf_id,fan_nomi) DO UPDATE SET
                         haftalik_soat=EXCLUDED.haftalik_soat,
                         kunlik_max=EXCLUDED.kunlik_max,
                         asosiy_oqituvchi_user_id=EXCLUDED.asosiy_oqituvchi_user_id,
                         xona_id=EXCLUDED.xona_id""",
                    (
                        maktab_id, pair["sinf_id"], pair["fan_nomi"], weekly,
                        daily, primary, room,
                    ))
        for row in groups:
            cur.execute("""INSERT INTO aqlli_guruh_sozlamalari_v2(
                            maktab_id,sinf_id,fan_nomi,guruh_kaliti,
                            oqituvchi_user_id,xona_id)
                           VALUES(%s,%s,%s,%s,%s,%s)
                           ON CONFLICT(maktab_id,sinf_id,fan_nomi,guruh_kaliti)
                           DO UPDATE SET
                             oqituvchi_user_id=EXCLUDED.oqituvchi_user_id,
                             xona_id=EXCLUDED.xona_id""",
                        (
                            maktab_id, pair["sinf_id"], pair["fan_nomi"],
                            _v1875_group_key(row.get("guruh_kaliti")),
                            row["user_id"], row.get("xona_id"),
                        ))
    cur.execute("""UPDATE aqlli_jadval_urinishlari_v2 SET holat='bekor'
                   WHERE maktab_id=%s AND holat='draft'""", (maktab_id,))
    cur.execute("""UPDATE aqlli_fan_guruh_tasdiqlari_v2
                   SET tasdiqlangan=FALSE,yangilangan_at=NOW()
                   WHERE maktab_id=%s""", (maktab_id,))
    return list(dict.fromkeys(warnings))


def _v192_auto_confirm_exact_pairs(cur, maktab_id: int, actor_id: int):
    """Saytdagi aniq qatorlar to'liq bo'lsa alohida qayta tasdiq talab qilmaydi."""
    systems = _v1876_group_system_catalog(cur, maktab_id)
    systems_by_class = {}
    for system in systems:
        systems_by_class.setdefault(int(system["sinf_id"]), []).append(system)
    pairs = _v1876_pair_assignment_rows(cur, maktab_id)
    confirmed = 0
    pending = 0
    for pair in pairs.values():
        rows = pair["rows"]
        whole = [row for row in rows if row["guruh_kaliti"] == "whole"]
        groups = [row for row in rows if row["guruh_kaliti"] != "whole"]
        mode = None
        system_id = None
        valid = False
        if len(whole) == 1 and not groups and float(whole[0].get("haftalik_soat") or 0) > 0:
            mode = "whole"
            valid = True
        elif groups and not whole:
            group_keys = {str(row["guruh_kaliti"]) for row in groups}
            hours = {float(row.get("haftalik_soat") or 0) for row in groups}
            teachers = {int(row["user_id"]) for row in groups}
            matching_system = next((
                system for system in systems_by_class.get(pair["sinf_id"], [])
                if pair["fan_kaliti"] in (system.get("fan_kalitlari") or [])
                and {
                    str(group["guruh_kaliti"])
                    for group in system.get("guruhlar") or []
                } == group_keys
            ), None)
            if (
                matching_system
                and len(hours) == 1
                and next(iter(hours), 0) > 0
                and len(teachers) == len(groups)
            ):
                mode = "group"
                system_id = int(matching_system["id"])
                valid = True
        pair_systems = systems_by_class.get(pair["sinf_id"], [])
        source_hash = _v1876_pair_hash(rows, pair_systems, pair["fan_kaliti"])
        cur.execute("""INSERT INTO aqlli_fan_guruh_tasdiqlari_v2(
                        maktab_id,sinf_id,fan_nomi,fan_kaliti,turi,tizim_id,
                        manba_hash,tasdiqlangan,tasdiqlagan_user_id,yangilangan_at)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                       ON CONFLICT(maktab_id,sinf_id,fan_kaliti) DO UPDATE SET
                         fan_nomi=EXCLUDED.fan_nomi,turi=EXCLUDED.turi,
                         tizim_id=EXCLUDED.tizim_id,manba_hash=EXCLUDED.manba_hash,
                         tasdiqlangan=EXCLUDED.tasdiqlangan,
                         tasdiqlagan_user_id=EXCLUDED.tasdiqlagan_user_id,
                         yangilangan_at=NOW()""",
                    (
                        maktab_id, pair["sinf_id"], pair["fan_nomi"],
                        pair["fan_kaliti"], mode or "group", system_id,
                        source_hash, valid, actor_id if valid else None,
                    ))
        if valid:
            confirmed += 1
        else:
            pending += 1
    return {"avto_tasdiqlangan": confirmed, "kutilmoqda": pending}


def _v192_save_teacher_load_rows(
    cur, actor_id: int, maktab_id: int, user_id: int,
    qatorlar: list[V192TeacherLoadRow],
):
    cur.execute("""SELECT user_id,full_name FROM users
                   WHERE user_id=%s AND maktab_id=%s FOR UPDATE""",
                (user_id, maktab_id))
    teacher = cur.fetchone()
    if not teacher:
        raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (1925000000 + int(maktab_id),))
    approved_plan = _v193_approved_plan_map(cur, maktab_id)
    classes, _systems, variants = _v192_group_variants(cur, maktab_id)
    valid_classes = {int(row["id"]) for row in classes}
    selected_by_grade = _v194_school_subject_grades(cur, maktab_id)
    cur.execute("SELECT fan_nomi FROM maktab_fanlari WHERE maktab_id=%s", (maktab_id,))
    fallback_subjects = {
        _v1875_subject_key(row["fan_nomi"]): row["fan_nomi"]
        for row in cur.fetchall()
    }
    allowed_by_class = {}
    for cls in classes:
        grade = _v193_grade_number(cls.get("sinf"))
        allowed_by_class[int(cls["id"])] = (
            dict((selected_by_grade or {}).get(grade, {}))
            if selected_by_grade is not None else dict(fallback_subjects)
        )
    variant_map = {
        (int(row["sinf_id"]), str(row["guruh_kaliti"])): row
        for row in variants
    }
    cleaned_by_key = {}
    duplicate_merged = 0
    plan_overrides = []
    for index, item in enumerate(qatorlar, start=1):
        if int(item.sinf_id) not in valid_classes:
            raise HTTPException(status_code=400, detail=f"{index}-qator: sinf bu maktabga tegishli emas")
        subject = _v192_clean_subject(item.fan_nomi)
        if not subject:
            raise HTTPException(status_code=400, detail=f"{index}-qator: fan tanlanmagan")
        subject_key = _v1875_subject_key(subject)
        plan_item = (
            approved_plan.get((int(item.sinf_id), subject_key))
            if approved_plan is not None else None
        )
        if approved_plan is not None and not plan_item:
            raise HTTPException(
                status_code=400,
                detail=f"{index}-qator: {subject} tanlangan sinfning tasdiqlangan o'quv rejasida yo'q",
            )
        if approved_plan is None:
            allowed_subject = allowed_by_class.get(int(item.sinf_id), {}).get(subject_key)
            if not allowed_subject:
                raise HTTPException(
                    status_code=400,
                    detail=f"{index}-qator: {subject} bu sinf uchun maktab fanlari ro'yxatida yo'q",
                )
            subject = allowed_subject
        group_key = _v1875_group_key(item.guruh_kaliti)
        variant = variant_map.get((int(item.sinf_id), group_key))
        if not variant:
            raise HTTPException(status_code=400, detail=f"{index}-qator: tanlangan guruh bu sinfda yo'q")
        hours = round(float(item.haftalik_soat), 1)
        daily = int(item.kunlik_max)
        if hours < 0.5 or hours > 20 or abs(hours * 2 - round(hours * 2)) > 1e-9:
            raise HTTPException(
                status_code=400,
                detail=f"{index}-qator: haftalik soat 0,5–20 oralig'ida va 0,5 qadamda bo'lishi kerak",
            )
        if daily < 1 or daily > 4:
            raise HTTPException(status_code=400, detail=f"{index}-qator: kunlik maksimum 1–4 bo'lishi kerak")
        key = (int(item.sinf_id), _v1875_subject_key(subject), group_key)
        existing = cleaned_by_key.get(key)
        if existing:
            existing["haftalik_soat"] += hours
            existing["kunlik_max"] = max(existing["kunlik_max"], daily)
            if not existing.get("xona_id") and item.xona_id:
                existing["xona_id"] = int(item.xona_id)
            duplicate_merged += 1
        else:
            cleaned_by_key[key] = {
                "sinf_id": int(item.sinf_id),
                "fan_nomi": subject,
                "fan_kaliti": _v1875_subject_key(subject),
                "guruh_kaliti": group_key,
                "haftalik_soat": hours,
                "kunlik_max": daily,
                "xona_id": int(item.xona_id) if item.xona_id else None,
                "variant": variant,
            }

    cleaned = list(cleaned_by_key.values())
    for row in cleaned:
        cur.execute("""SELECT COALESCE(SUM(b.haftalik_soat),0) AS band_soat,
                              STRING_AGG(DISTINCT u.full_name, ', ' ORDER BY u.full_name) AS oqituvchilar
                       FROM maktab_dars_birikmalari b
                       JOIN users u ON u.user_id=b.user_id
                       WHERE b.maktab_id=%s AND b.sinf_id=%s
                         AND LOWER(TRIM(b.fan_nomi))=LOWER(TRIM(%s))
                         AND COALESCE(NULLIF(b.guruh_kaliti,''),'whole')=%s
                         AND b.user_id<>%s""",
                    (
                        maktab_id, row["sinf_id"], row["fan_nomi"],
                        row["guruh_kaliti"], user_id,
                    ))
        occupied = cur.fetchone() or {}
        occupied_hours = float(occupied.get("band_soat") or 0)
        if approved_plan is not None:
            plan_item = approved_plan.get((row["sinf_id"], row["fan_kaliti"]))
            plan_hours = float((plan_item or {}).get("haftalik_soat") or 0)
            remaining = round(max(0.0, plan_hours - occupied_hours), 1)
            if row["haftalik_soat"] > remaining:
                owners = occupied.get("oqituvchilar") or "yuqoridagi qatorlar"
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"{row['variant']['sinf']} / {row['fan_nomi']} / "
                        f"{row['variant']['guruh_nomi']}: reja {plan_hours:g} soat, "
                        f"{owners}da {occupied_hours} soat tanlangan, faqat {remaining:g} soat qoldi"
                    ),
                )
            if row["haftalik_soat"] < remaining:
                plan_overrides.append(
                    f"{row['variant']['sinf']} / {row['fan_nomi']}: "
                    f"yana {remaining - row['haftalik_soat']:g} soat taqsimlanmagan"
                )
    if duplicate_merged:
        plan_overrides.append(
            f"Bir xil fan–sinf–guruhdagi {duplicate_merged} ta takror qator bitta qatorga qo'shildi"
        )

    cur.execute("DELETE FROM maktab_dars_birikmalari WHERE maktab_id=%s AND user_id=%s",
                (maktab_id, user_id))
    for row in cleaned:
        cur.execute("""INSERT INTO maktab_dars_birikmalari(
                        maktab_id,user_id,sinf_id,fan_nomi,guruh_kaliti,
                        haftalik_soat,kunlik_max,xona_id,manba,yangilangan_at)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'v19.2_qolda',NOW())""",
                    (
                        maktab_id, user_id, row["sinf_id"], row["fan_nomi"],
                        row["guruh_kaliti"], row["haftalik_soat"],
                        row["kunlik_max"], row["xona_id"],
                    ))
        cur.execute("""INSERT INTO maktab_fanlari(maktab_id,fan_nomi)
                       VALUES(%s,%s) ON CONFLICT DO NOTHING""",
                    (maktab_id, row["fan_nomi"]))
        system_id = row["variant"].get("tizim_id")
        if system_id:
            cur.execute("SELECT fanlar FROM maktab_sinf_guruh_tizimlari WHERE id=%s FOR UPDATE", (system_id,))
            system = cur.fetchone()
            current_subjects = list((system or {}).get("fanlar") or [])
            if all(_v1875_subject_key(value) != _v1875_subject_key(row["fan_nomi"]) for value in current_subjects):
                current_subjects.append(row["fan_nomi"])
                cur.execute("""UPDATE maktab_sinf_guruh_tizimlari
                               SET fanlar=%s,yangilangan_at=NOW() WHERE id=%s""",
                            (current_subjects, system_id))

    weekly_total = _v195_refresh_teacher_summary(cur, maktab_id, user_id)
    warnings = _v192_sync_schedule_sources(cur, maktab_id)
    warnings.extend(plan_overrides)
    auto_confirmation = _v192_auto_confirm_exact_pairs(cur, maktab_id, actor_id)
    payload = _v192_matrix_payload(cur, maktab_id)
    return {
        "holat": "saqlandi",
        "user_id": int(user_id),
        "oqituvchi": teacher["full_name"],
        "qator_soni": len(cleaned),
        "haftalik_jami": weekly_total,
        "ogohlantirishlar": warnings,
        "guruh_tasdiqlari": auto_confirmation,
        "matritsa": payload,
    }


@app.put("/api/maktab/aqlli_jadval/v3/oqituvchi_yuklamasi")
def v192_teacher_load_save(sorov: V192TeacherLoadSave, token: str):
    from datetime import date as _date

    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="O'qituvchi yuklamasini faqat rahbariyat boshqaradi")
        supplied_fields = set(
            getattr(sorov, "model_fields_set", getattr(sorov, "__fields_set__", set()))
        )
        profile_fields = {
            "mutaxassisligi", "haftalik_maqsad_soat", "tugilgan_sana",
            "tugilgan_yili", "ish_staji", "toifasi",
        }
        if supplied_fields.intersection(profile_fields):
            specialty, target = _v194_teacher_profile_values(
                sorov.mutaxassisligi, sorov.haftalik_maqsad_soat
            )
            work_years = sorov.ish_staji
            if work_years is not None and not 0 <= int(work_years) <= 60:
                raise HTTPException(status_code=400, detail="Ish staji 0–60 yil oralig'ida bo'lishi kerak")
            birth_date = sorov.tugilgan_sana
            birth_year = birth_date.year if birth_date is not None else sorov.tugilgan_yili
            current_year = _date.today().year
            if birth_year is not None and not 1900 <= int(birth_year) <= current_year:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tug'ilgan yil 1900–{current_year} oralig'ida bo'lishi kerak",
                )
            if birth_date is not None and birth_date > _date.today():
                raise HTTPException(status_code=400, detail="Tug'ilgan sana kelajakda bo'lishi mumkin emas")
            category = re.sub(r"\s+", " ", str(sorov.toifasi or "")).strip() or None
            if category and category not in TOIFALAR:
                raise HTTPException(status_code=400, detail="O'qituvchi toifasi noto'g'ri")
            cur.execute("""UPDATE users
                           SET mutaxassisligi=%s,haftalik_maqsad_soat=%s,
                               tugilgan_sana=%s,ish_staji=%s,toifasi=%s
                           WHERE user_id=%s AND maktab_id=%s""",
                        (
                            specialty, target,
                            birth_date or (_date(int(birth_year), 1, 1) if birth_year is not None else None),
                            int(work_years) if work_years is not None else None,
                            category, sorov.user_id, sorov.maktab_id,
                        ))
            if int(cur.rowcount or 0) != 1:
                raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
        leader_class = None
        if "rahbar_sinf_id" in supplied_fields:
            leader_class = _v199_save_teacher_leadership(
                cur, sorov.maktab_id, sorov.user_id, sorov.rahbar_sinf_id, actor_id
            )
        result = _v192_save_teacher_load_rows(
            cur, actor_id, sorov.maktab_id, sorov.user_id, sorov.qatorlar
        )
        _v199_teacher_total_with_class_hour(
            cur, sorov.maktab_id, sorov.user_id, result
        )
        result.update({
            "rahbar_sinf_id": int(leader_class["id"]) if leader_class else None,
            "rahbar_sinf_nomi": (
                f"{leader_class['sinf']}-{leader_class['harf']}" if leader_class else None
            ),
        })
        conn.commit()
        return result
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.post("/api/maktab/aqlli_jadval/v3/oqituvchi_qoshish")
def v192_manual_teacher_create(sorov: V192ManualTeacherCreate, token: str):
    from datetime import date as _date

    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        _xodim_kod_jadvali(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="O'qituvchini faqat maktab rahbariyati qo'shadi")
        full_name = re.sub(r"\s+", " ", str(sorov.full_name or "")).strip()
        if len(full_name) < 3 or len(full_name) > 160:
            raise HTTPException(status_code=400, detail="O'qituvchi F.I.Sh. 3–160 ta belgi bo'lishi kerak")
        if not sorov.qatorlar:
            raise HTTPException(status_code=400, detail="Kamida bitta fan–sinf–guruh qatorini kiriting")
        work_years = sorov.ish_staji
        if work_years is not None and not 0 <= int(work_years) <= 60:
            raise HTTPException(status_code=400, detail="Ish staji 0–60 yil oralig'ida bo'lishi kerak")
        birth_date = sorov.tugilgan_sana
        birth_year = birth_date.year if birth_date is not None else sorov.tugilgan_yili
        current_year = _date.today().year
        if birth_year is not None and not 1900 <= int(birth_year) <= current_year:
            raise HTTPException(
                status_code=400,
                detail=f"Tug'ilgan yil 1900–{current_year} oralig'ida bo'lishi kerak",
            )
        if birth_date is not None and birth_date > _date.today():
            raise HTTPException(status_code=400, detail="Tug'ilgan sana kelajakda bo'lishi mumkin emas")
        category = re.sub(r"\s+", " ", str(sorov.toifasi or "")).strip() or None
        if category and category not in TOIFALAR:
            raise HTTPException(status_code=400, detail="O'qituvchi toifasi noto'g'ri")
        specialty, target_hours = _v194_teacher_profile_values(
            sorov.mutaxassisligi, sorov.haftalik_maqsad_soat
        )

        cur.execute("SELECT pg_advisory_xact_lock(%s)", (1922000000 + int(sorov.maktab_id),))
        leader_class = None
        if sorov.rahbar_sinf_id is not None:
            cur.execute("""SELECT id,sinf,harf,rahbar_user_id
                           FROM maktab_sinflari
                           WHERE id=%s AND maktab_id=%s
                           FOR UPDATE""",
                        (int(sorov.rahbar_sinf_id), int(sorov.maktab_id)))
            leader_class = cur.fetchone()
            if not leader_class:
                raise HTTPException(status_code=404, detail="Sinf rahbarligi uchun tanlangan sinf topilmadi")
            if leader_class.get("rahbar_user_id") is not None:
                raise HTTPException(
                    status_code=409,
                    detail=f"{leader_class['sinf']}-{leader_class['harf']} sinfiga rahbar allaqachon tayinlangan",
                )
        cur.execute("""SELECT user_id FROM users
                       WHERE maktab_id=%s
                         AND LOWER(REGEXP_REPLACE(TRIM(full_name), '\\s+', ' ', 'g'))
                             = LOWER(REGEXP_REPLACE(TRIM(%s), '\\s+', ' ', 'g'))
                       LIMIT 1""", (sorov.maktab_id, full_name))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Bu F.I.Sh. bilan xodim allaqachon mavjud")
        cur.execute("SELECT MIN(user_id) AS eng_kichik FROM users WHERE user_id < 0")
        smallest = cur.fetchone()
        new_user_id = (
            int(smallest["eng_kichik"]) - 1
            if smallest and smallest.get("eng_kichik") is not None else -1
        )
        cur.execute("""INSERT INTO users(
                        user_id,full_name,role,maktab_id,lavozim,tugilgan_sana,
                        ish_staji,toifasi,mutaxassisligi,haftalik_maqsad_soat,
                        haftalik_dars_soati)
                       VALUES(%s,%s,'oqituvchi',%s,'fan_oqituvchisi',%s,%s,%s,%s,%s,0)""",
                    (
                        new_user_id, full_name, sorov.maktab_id,
                        birth_date or (_date(int(birth_year), 1, 1) if birth_year is not None else None),
                        int(work_years) if work_years is not None else None,
                        category, specialty, target_hours,
                    ))
        plain_code, stored_code = _xodim_kod_yarat()
        cur.execute("INSERT INTO xodim_kod(kod,user_id) VALUES(%s,%s)",
                    (stored_code, new_user_id))
        if leader_class:
            cur.execute("""UPDATE maktab_sinflari
                           SET rahbar_user_id=%s
                           WHERE id=%s AND maktab_id=%s""",
                        (new_user_id, int(leader_class["id"]), int(sorov.maktab_id)))
            _v199_ensure_class_hour_rules(
                cur, sorov.maktab_id, [int(leader_class["id"])], actor_id
            )
        result = _v192_save_teacher_load_rows(
            cur, actor_id, sorov.maktab_id, new_user_id, sorov.qatorlar
        )
        _v199_teacher_total_with_class_hour(
            cur, sorov.maktab_id, new_user_id, result
        )
        result.update({
            "holat": "oqituvchi_va_yuklama_saqlandi",
            "kirish_kodi": plain_code,
            "kirish_kodi_muddati": "2 oy",
            "qolda_kiritildi": True,
            "mutaxassisligi": specialty,
            "haftalik_maqsad_soat": target_hours,
            "tugilgan_yili": int(birth_year) if birth_year is not None else None,
            "tugilgan_sana": birth_date.isoformat() if birth_date is not None else None,
            "rahbar_sinf_id": int(leader_class["id"]) if leader_class else None,
            "rahbar_sinf_nomi": (
                f"{leader_class['sinf']}-{leader_class['harf']}" if leader_class else None
            ),
        })
        conn.commit()
        return result
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V195TeacherDelete(BaseModel):
    maktab_id: int
    user_id: int
    tasdiq: bool = False


@app.post("/api/maktab/aqlli_jadval/v3/oqituvchi_ochirish")
def v195_teacher_delete(sorov: V195TeacherDelete, token: str):
    """O'qituvchini maktabdan va barcha faol yuklamalardan to'liq chiqaradi."""
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="O'qituvchini faqat maktab rahbariyati o'chiradi")
        if not sorov.tasdiq:
            raise HTTPException(status_code=400, detail="O'chirish uchun Ha tasdig'i kerak")
        if int(sorov.user_id) == int(actor_id):
            raise HTTPException(status_code=400, detail="O'zingizning rahbariyat hisobingizni bu yerdan o'chira olmaysiz")
        cur.execute("SELECT pg_advisory_xact_lock(%s)", (1925000000 + int(sorov.maktab_id),))
        cur.execute("""SELECT user_id,full_name,lavozim FROM users
                       WHERE user_id=%s AND maktab_id=%s FOR UPDATE""",
                    (sorov.user_id, sorov.maktab_id))
        teacher = cur.fetchone()
        if not teacher:
            raise HTTPException(status_code=404, detail="O'qituvchi topilmadi yoki avval o'chirilgan")
        if str(teacher.get("lavozim") or "").lower() in {
            "direktor", "zam_direktor_uquv", "zam_direktor_tarbiya", "owner", "admin"
        }:
            raise HTTPException(status_code=409, detail="Rahbariyat hisobini o'qituvchi oynasidan o'chirib bo'lmaydi")

        cur.execute("""SELECT COUNT(*) AS son,COALESCE(SUM(haftalik_soat),0) AS soat
                       FROM maktab_dars_birikmalari
                       WHERE maktab_id=%s AND user_id=%s""",
                    (sorov.maktab_id, sorov.user_id))
        old_load = cur.fetchone() or {}
        cur.execute("UPDATE maktab_sinflari SET rahbar_user_id=NULL WHERE maktab_id=%s AND rahbar_user_id=%s",
                    (sorov.maktab_id, sorov.user_id))
        if "psixolog_user_id" in _v1857_columns(cur, "maktab_sinflari"):
            cur.execute("UPDATE maktab_sinflari SET psixolog_user_id=NULL WHERE maktab_id=%s AND psixolog_user_id=%s",
                        (sorov.maktab_id, sorov.user_id))
        cur.execute("DELETE FROM maktab_dars_birikmalari WHERE maktab_id=%s AND user_id=%s",
                    (sorov.maktab_id, sorov.user_id))
        cur.execute("DELETE FROM maktab_xodim_sinflari WHERE maktab_id=%s AND user_id=%s",
                    (sorov.maktab_id, sorov.user_id))
        if _v1857_has_columns(cur, "aqlli_oqituvchi_qoidalari_v2", {"maktab_id", "user_id"}):
            cur.execute("DELETE FROM aqlli_oqituvchi_qoidalari_v2 WHERE maktab_id=%s AND user_id=%s",
                        (sorov.maktab_id, sorov.user_id))
        if _v1857_has_columns(cur, "aqlli_oqituvchi_vaqti_v2", {"maktab_id", "user_id"}):
            cur.execute("DELETE FROM aqlli_oqituvchi_vaqti_v2 WHERE maktab_id=%s AND user_id=%s",
                        (sorov.maktab_id, sorov.user_id))
        if _v1857_has_columns(cur, "aqlli_guruh_sozlamalari_v2", {"maktab_id", "oqituvchi_user_id"}):
            cur.execute("DELETE FROM aqlli_guruh_sozlamalari_v2 WHERE maktab_id=%s AND oqituvchi_user_id=%s",
                        (sorov.maktab_id, sorov.user_id))
        if _v1857_has_columns(cur, "aqlli_sinf_fan_yuklamalari_v2", {"maktab_id", "asosiy_oqituvchi_user_id"}):
            cur.execute("""UPDATE aqlli_sinf_fan_yuklamalari_v2
                           SET asosiy_oqituvchi_user_id=NULL
                           WHERE maktab_id=%s AND asosiy_oqituvchi_user_id=%s""",
                        (sorov.maktab_id, sorov.user_id))
        if _v1857_has_columns(cur, "xodim_davomati", {"maktab_id", "user_id"}):
            cur.execute("DELETE FROM xodim_davomati WHERE maktab_id=%s AND user_id=%s",
                        (sorov.maktab_id, sorov.user_id))
        if _v1857_has_columns(cur, "xodim_kod", {"user_id"}):
            cur.execute("DELETE FROM xodim_kod WHERE user_id=%s", (sorov.user_id,))
        if _v1857_has_columns(cur, "dars_jadvali", {"oqituvchi_user_id"}):
            cur.execute("DELETE FROM dars_jadvali WHERE oqituvchi_user_id=%s", (sorov.user_id,))

        cur.execute("""UPDATE users
                       SET maktab_id=NULL,lavozim=NULL,fanlari=NULL,
                           oqitadigan_sinflari=NULL,haftalik_dars_soati=NULL,
                           haftalik_maqsad_soat=NULL,mutaxassisligi=NULL
                       WHERE user_id=%s AND maktab_id=%s""",
                    (sorov.user_id, sorov.maktab_id))
        cur.execute("""UPDATE aqlli_jadval_urinishlari_v2 SET holat='bekor'
                       WHERE maktab_id=%s AND holat IN ('draft','tasdiqlangan')""",
                    (sorov.maktab_id,))
        cur.execute("""UPDATE aqlli_fan_guruh_tasdiqlari_v2
                       SET tasdiqlangan=FALSE,yangilangan_at=NOW()
                       WHERE maktab_id=%s""", (sorov.maktab_id,))
        warnings = _v192_sync_schedule_sources(cur, sorov.maktab_id)
        matrix = _v192_matrix_payload(cur, sorov.maktab_id)
        conn.commit()
        return {
            "holat": "oqituvchi_ochirildi",
            "user_id": int(sorov.user_id),
            "oqituvchi": teacher["full_name"],
            "ochirilgan_qator": int(old_load.get("son") or 0),
            "ochirilgan_soat": int(old_load.get("soat") or 0),
            "ogohlantirishlar": warnings,
            "matritsa": matrix,
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V192AutoMode(BaseModel):
    maktab_id: int
    avtomatik_tavsiya: bool


@app.put("/api/maktab/aqlli_jadval/v3/almashtirish_rejimi")
def v192_swap_mode(sorov: V192AutoMode, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="Jadval rejimini faqat rahbariyat o'zgartiradi")
        cur.execute("""INSERT INTO aqlli_jadval_boshqaruv_v19_2(
                        maktab_id,avtomatik_tavsiya,yangilagan_user_id,yangilangan_at)
                       VALUES(%s,%s,%s,NOW())
                       ON CONFLICT(maktab_id) DO UPDATE SET
                         avtomatik_tavsiya=EXCLUDED.avtomatik_tavsiya,
                         yangilagan_user_id=EXCLUDED.yangilagan_user_id,
                         yangilangan_at=NOW()""",
                    (sorov.maktab_id, sorov.avtomatik_tavsiya, actor_id))
        conn.commit()
        return {"holat": "saqlandi", "avtomatik_tavsiya": sorov.avtomatik_tavsiya}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def _v192_run_slots(cur, run_id: int):
    cur.execute("""SELECT e.*,s.sinf,s.harf,u.full_name AS oqituvchi_ismi,
                          COALESCE(r.nomi,e.xona_matni) AS xona_nomi
                   FROM aqlli_jadval_slotlari_v2 e
                   JOIN maktab_sinflari s ON s.id=e.sinf_id
                   LEFT JOIN users u ON u.user_id=e.oqituvchi_user_id
                   LEFT JOIN aqlli_xonalar_v2 r ON r.id=e.xona_id
                   WHERE e.urinish_id=%s
                   ORDER BY e.hafta_kuni,e.smena,e.dars_raqami,
                            s.sinf::int,s.harf,e.guruh_kaliti""", (run_id,))
    return [dict(row) for row in cur.fetchall()]


def _v200_xlsx_sheet_name(value, used):
    cleaned = re.sub(r"[\\/*?:\[\]]+", " ", str(value or "Jadval")).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)[:31] or "Jadval"
    candidate = cleaned
    suffix = 2
    while candidate.casefold() in used:
        tail = f" {suffix}"
        candidate = f"{cleaned[:31-len(tail)]}{tail}"
        suffix += 1
    used.add(candidate.casefold())
    return candidate


def _v200_xlsx_slot_text(rows, teacher_view=False):
    lines = []
    seen = set()
    for row in rows:
        group = str(row.get("guruh_kaliti") or "whole")
        group_label = ""
        if group != "whole":
            normalized = group.casefold()
            if normalized in {"boys", "boy", "ogil", "o'g'il", "o‘g‘il"}:
                group_label = "O'g'il bolalar"
            elif normalized in {"girls", "girl", "qiz"}:
                group_label = "Qiz bolalar"
            else:
                match = re.search(r"(\d+)", normalized)
                group_label = f"{match.group(1)}-guruh" if match else group
        week = str(row.get("hafta_turi") or "har_hafta")
        week_label = ""
        if week in {"toq", "juft"}:
            week_label = "TOQ" if week == "toq" else "JUFT"
        subject = str(row.get("fan_nomi") or "Fan")
        class_label = f"{row.get('sinf','')}-{row.get('harf','')}"
        teacher = str(row.get("oqituvchi_ismi") or "O'qituvchi yo'q")
        room = str(row.get("xona_nomi") or row.get("xona_matni") or "Xona yo'q")
        prefix = " · ".join(value for value in [group_label, week_label] if value)
        first = " · ".join(value for value in [class_label if teacher_view else "", prefix, subject] if value)
        second = " · ".join(value for value in ["" if teacher_view else teacher, room] if value)
        text = f"{first}\n{second}" if second else first
        if text not in seen:
            seen.add(text)
            lines.append(text)
    return "\n——\n".join(lines)


def _v200_xlsx_style_workbook(workbook):
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    theme = {
        "ink": "18324B", "blue": "155A7A", "teal": "0F7C82",
        "sky": "EDF5FB", "mint": "EAF7F4", "cream": "FAF7F0",
        "line": "DDE6EC", "green": "33755A", "red": "A54242",
    }
    thin = Side(style="thin", color=theme["line"])
    return theme, Font, PatternFill, Alignment, Border, thin


def _v200_xlsx_prepare_schedule_sheet(
    ws, title, subtitle, summary_text, weekdays, rows, teacher_view=False,
    default_shift=1,
):
    import openpyxl
    theme, Font, PatternFill, Alignment, Border, thin = _v200_xlsx_style_workbook(ws.parent)
    last_col = 1 + len(weekdays)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    ws["A1"] = title
    ws["A1"].font = Font(size=18, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=theme["blue"])
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 29
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
    ws["A2"] = subtitle
    ws["A2"].font = Font(size=9, color="6D7B87")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="center")
    ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=last_col)
    ws["A3"] = summary_text
    ws["A3"].font = Font(size=10, bold=True, color=theme["green"])
    ws["A3"].fill = PatternFill("solid", fgColor=theme["mint"])
    ws["A3"].alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[3].height = 26
    ws.cell(4, 1, "Dars")
    for index, (_, name) in enumerate(weekdays, start=2):
        ws.cell(4, index, name)
    for cell in ws[4]:
        cell.font = Font(size=9, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=theme["teal"])
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)

    key_map = _v1852_defaultdict(list)
    for row in rows:
        key_map[(int(row["hafta_kuni"]), int(row["smena"]), int(row["dars_raqami"]))].append(row)
    schedule_rows = []
    if teacher_view:
        schedule_rows = [(shift, period, f"{shift}-smena · {period}") for shift in (1, 2) for period in range(1, 7)]
    else:
        class_shift = int(rows[0].get("smena") or default_shift) if rows else int(default_shift or 1)
        schedule_rows = [(class_shift, period, str(period)) for period in range(1, 7)]

    for output_row, (shift, period, label) in enumerate(schedule_rows, start=5):
        ws.cell(output_row, 1, label)
        ws.cell(output_row, 1).font = Font(size=9, bold=True, color=theme["ink"])
        ws.cell(output_row, 1).fill = PatternFill("solid", fgColor=theme["cream"])
        ws.cell(output_row, 1).alignment = Alignment(horizontal="center", vertical="center")
        for column, (day, _) in enumerate(weekdays, start=2):
            cell = ws.cell(output_row, column)
            cell.value = _v200_xlsx_slot_text(
                key_map.get((int(day), shift, period), []),
                teacher_view=teacher_view,
            )
            cell.font = Font(size=8, bold=bool(cell.value), color=theme["ink"])
            cell.fill = PatternFill("solid", fgColor=theme["sky"] if cell.value else "FFFFFF")
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)
        ws.row_dimensions[output_row].height = 42 if teacher_view else 55
    ws.column_dimensions["A"].width = 13
    for column in range(2, last_col + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(column)].width = 24
    ws.freeze_panes = "B5"
    ws.sheet_view.showGridLines = False
    ws.auto_filter.ref = f"A4:{openpyxl.utils.get_column_letter(last_col)}{4+len(schedule_rows)}"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:{openpyxl.utils.get_column_letter(last_col)}{4+len(schedule_rows)}"
    ws.oddFooter.center.text = "SAMTM Aqlli jadval"
    ws.oddFooter.right.text = "&P / &N"


@app.get("/api/maktab/aqlli_jadval/v3/jadval_xlsx")
def v200_schedule_xlsx(token: str, urinish_id: int, turi: str = "sinflar"):
    """Sinf yoki o'qituvchi kesimida varaqlangan, chopga tayyor XLSX."""
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        cur.execute(
            "SELECT * FROM aqlli_jadval_urinishlari_v2 WHERE id=%s",
            (urinish_id,),
        )
        run = cur.fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Jadval topilmadi")
        maktab_id = int(run["maktab_id"])
        if not _v1852_staff(cur, actor_id, maktab_id):
            raise HTTPException(status_code=403, detail="Bu jadvalni yuklashga ruxsat yo'q")
        export_type = str(turi or "sinflar").strip().lower()
        if export_type not in {"sinflar", "oqituvchilar"}:
            raise HTTPException(status_code=400, detail="turi sinflar yoki oqituvchilar bo'lishi kerak")
        cur.execute("SELECT nomi FROM maktablar WHERE id=%s", (maktab_id,))
        school = cur.fetchone() or {"nomi": "Maktab"}
        slots = _v192_run_slots(cur, urinish_id)
        report = _v1875_schedule_integrity_report(cur, maktab_id, urinish_id)
        class_summary = {int(row["sinf_id"]): row for row in report.get("sinflar", [])}
        teacher_summary = {int(row["user_id"]): row for row in report.get("oqituvchilar", [])}
        year = _v1852_active_year(cur, maktab_id) or {}
        weekdays = [
            (day, _V1852_HAFTA.get(day, str(day)))
            for day in range(1, int(year.get("hafta_kunlari") or 6) + 1)
        ]

        import io
        import openpyxl
        from fastapi.responses import StreamingResponse
        from openpyxl.styles import Alignment, Font, PatternFill
        from urllib.parse import quote

        workbook = openpyxl.Workbook()
        index = workbook.active
        index.title = "Mundarija"
        index.sheet_view.showGridLines = False
        index.append(["SAMTM AQILLI DARS JADVALI"])
        index.append([school.get("nomi") or "Maktab"])
        index.append(["Turi", "Nomi", "Haftalik hisob", "Holat"])
        used = {"mundarija"}
        created = []
        if export_type == "sinflar":
            cur.execute(
                "SELECT id,sinf,harf,COALESCE(smena,1) AS smena FROM maktab_sinflari "
                "WHERE maktab_id=%s ORDER BY sinf::int,harf",
                (maktab_id,),
            )
            entities = [dict(row) for row in cur.fetchall()]
            for entity in entities:
                entity_id = int(entity["id"])
                label = f"{entity['sinf']}-{entity['harf']}"
                rows = [row for row in slots if int(row["sinf_id"]) == entity_id]
                summary = class_summary.get(entity_id, {})
                summary_text = summary.get("tasdiq_matni") or (
                    f"Reja {summary.get('reja', 0)} · jadval {summary.get('jadval', 0)}"
                )
                sheet_name = _v200_xlsx_sheet_name(label, used)
                ws = workbook.create_sheet(sheet_name)
                _v200_xlsx_prepare_schedule_sheet(
                    ws, f"{label} · haftalik dars jadvali",
                    school.get("nomi") or "Maktab", summary_text,
                    weekdays, rows, teacher_view=False,
                    default_shift=int(entity.get("smena") or 1),
                )
                created.append(("Sinf", label, summary_text, "TO'LIQ" if summary.get("mos") else "TEKSHIRISH", sheet_name))
        else:
            cur.execute(
                "SELECT user_id,full_name FROM users WHERE maktab_id=%s ORDER BY full_name,user_id",
                (maktab_id,),
            )
            names = {int(row["user_id"]): row["full_name"] for row in cur.fetchall()}
            entity_ids = sorted(teacher_summary, key=lambda uid: str(names.get(uid, uid)).casefold())
            for entity_id in entity_ids:
                label = names.get(entity_id) or teacher_summary[entity_id].get("full_name") or str(entity_id)
                rows = [row for row in slots if int(row.get("oqituvchi_user_id") or 0) == entity_id]
                summary = teacher_summary.get(entity_id, {})
                summary_text = summary.get("tasdiq_matni") or (
                    f"Reja {summary.get('reja', 0)} · jadval {summary.get('jadval', 0)}"
                )
                sheet_name = _v200_xlsx_sheet_name(label, used)
                ws = workbook.create_sheet(sheet_name)
                _v200_xlsx_prepare_schedule_sheet(
                    ws, f"{label} · haftalik ish jadvali",
                    school.get("nomi") or "Maktab", summary_text,
                    weekdays, rows, teacher_view=True,
                )
                created.append(("O'qituvchi", label, summary_text, "TO'LIQ" if summary.get("mos") else "TEKSHIRISH", sheet_name))

        for row_number, (kind, label, summary_text, status, sheet_name) in enumerate(created, start=4):
            index.cell(row_number, 1, kind)
            index.cell(row_number, 2, label)
            index.cell(row_number, 2).hyperlink = f"#'{sheet_name.replace(chr(39), chr(39)*2)}'!A1"
            index.cell(row_number, 3, summary_text)
            index.cell(row_number, 4, status)
        index.merge_cells("A1:D1")
        index["A1"].font = Font(size=19, bold=True, color="FFFFFF")
        index["A1"].fill = PatternFill("solid", fgColor="155A7A")
        index.merge_cells("A2:D2")
        index["A2"].font = Font(size=11, bold=True, color="0F7C82")
        for cell in index[3]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="0F7C82")
            cell.alignment = Alignment(horizontal="center")
        for width, column in zip((16, 34, 70, 16), ("A", "B", "C", "D")):
            index.column_dimensions[column].width = width
        index.freeze_panes = "A4"
        index.page_setup.orientation = "landscape"
        index.page_setup.fitToWidth = 1
        index.sheet_properties.pageSetUpPr.fitToPage = True

        output = io.BytesIO()
        workbook.save(output)
        output.seek(0)
        filename = f"SAMTM_{export_type}_jadvali_{urinish_id}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
        )
    finally:
        cur.close(); conn.close()


def _v192_bundle_for_slot(slots, slot_id: int):
    source = next((row for row in slots if int(row["id"]) == int(slot_id)), None)
    if not source:
        return None, []
    bundle = [
        row for row in slots
        if int(row["sinf_id"]) == int(source["sinf_id"])
        and int(row["hafta_kuni"]) == int(source["hafta_kuni"])
        and int(row["smena"]) == int(source["smena"])
        and int(row["dars_raqami"]) == int(source["dars_raqami"])
    ]
    return source, bundle


def _v192_bundle_label(bundle):
    if not bundle:
        return "Bo'sh vaqt"
    subjects = list(dict.fromkeys(str(row["fan_nomi"]) for row in bundle))
    teachers = list(dict.fromkeys(
        str(row.get("oqituvchi_ismi") or "O'qituvchi belgilanmagan")
        for row in bundle
    ))
    return f"{' + '.join(subjects)} · {' + '.join(teachers)}"


def _v192_candidate_conflicts(
    moving_bundle, target_day, target_period, all_slots, ignored_ids,
    hard_rows, class_row, class_day_map, room_check=True,
):
    reasons = []
    shift = int(moving_bundle[0]["smena"])
    blocked = _v1856_class_day_block_reason(class_row, target_day, class_day_map)
    if blocked:
        reasons.append(blocked)
    moving_teachers = [
        int(row["oqituvchi_user_id"])
        for row in moving_bundle if row.get("oqituvchi_user_id") is not None
    ]
    if len(moving_teachers) != len(set(moving_teachers)):
        reasons.append("bir o'qituvchi parallel guruhlarda takrorlangan")
    for teacher_id in moving_teachers:
        for rule in hard_rows:
            if int(rule["user_id"]) != teacher_id:
                continue
            if int(rule["hafta_kuni"]) != int(target_day):
                continue
            if rule["turi"] == "metod_kuni":
                reasons.append("o'qituvchining metod kuni")
                break
            if not bool(rule.get("qattiq")):
                continue
            rule_shift = int(rule.get("smena") or 0)
            rule_period = int(rule.get("dars_raqami") or 0)
            if rule_shift in (0, shift) and rule_period in (0, int(target_period)):
                reasons.append("o'qituvchi bu vaqtda band")
                break
        if any(
            int(row["id"]) not in ignored_ids
            and row.get("oqituvchi_user_id") is not None
            and int(row["oqituvchi_user_id"]) == teacher_id
            and int(row["hafta_kuni"]) == int(target_day)
            and int(row["smena"]) == shift
            and int(row["dars_raqami"]) == int(target_period)
            for row in all_slots
        ):
            reasons.append("o'qituvchi boshqa sinfda")
    if room_check:
        for moving in moving_bundle:
            room_id = moving.get("xona_id")
            room_text = str(moving.get("xona_matni") or "").strip().casefold()
            if room_id and any(
                    int(row["id"]) not in ignored_ids
                    and row.get("xona_id") is not None
                    and int(row["xona_id"]) == int(room_id)
                    and int(row["hafta_kuni"]) == int(target_day)
                    and int(row["smena"]) == shift
                    and int(row["dars_raqami"]) == int(target_period)
                    for row in all_slots
            ):
                reasons.append("xona bu vaqtda band")
            elif room_text and any(
                    int(row["id"]) not in ignored_ids
                    and str(row.get("xona_matni") or "").strip().casefold() == room_text
                    and int(row["hafta_kuni"]) == int(target_day)
                    and int(row["smena"]) == shift
                    and int(row["dars_raqami"]) == int(target_period)
                    for row in all_slots
            ):
                reasons.append("sinf xonasi bu vaqtda band")
    return list(dict.fromkeys(reasons))


def _v192_parallel_conflicts(slots):
    grouped = {}
    for row in slots:
        teacher_id = row.get("oqituvchi_user_id")
        if teacher_id is None:
            continue
        week_type = str(row.get("hafta_turi") or "har_hafta")
        phases = ("toq", "juft") if week_type == "har_hafta" else (week_type,)
        for phase in phases:
            key = (
                int(teacher_id), int(row["hafta_kuni"]),
                int(row["smena"]), int(row["dars_raqami"]), phase,
            )
            grouped.setdefault(key, []).append(row)
    result = []
    for key, rows in grouped.items():
        class_ids = {int(row["sinf_id"]) for row in rows}
        if len(class_ids) > 1:
            result.append({
                "oqituvchi_user_id": key[0],
                "oqituvchi_ismi": rows[0].get("oqituvchi_ismi"),
                "hafta_kuni": key[1],
                "smena": key[2],
                "dars_raqami": key[3],
                "hafta_turi": key[4],
                "sinflar": list(dict.fromkeys(f"{row['sinf']}-{row['harf']}" for row in rows)),
                "slot_idlar": [int(row["id"]) for row in rows],
            })
    return result


def _v192_class_periods_contiguous(slots, class_id: int, changes=None):
    """Taklif qilingan ko'chirishdan keyin sinf kunlari oknosiz qolishini tekshiradi."""
    changes = changes or {}
    day_periods = _v1852_defaultdict(set)
    for row in slots:
        if int(row["sinf_id"]) != int(class_id):
            continue
        day = int(row["hafta_kuni"])
        period = int(row["dars_raqami"])
        replacement = changes.get(int(row["id"]))
        if replacement:
            day, period = int(replacement[0]), int(replacement[1])
        day_periods[day].add(period)
    return all(_v1852_gap_count(periods) == 0 for periods in day_periods.values())


def _v192_swap_suggestions(cur, run_id: int, slot_id: int):
    cur.execute("SELECT * FROM aqlli_jadval_urinishlari_v2 WHERE id=%s", (run_id,))
    run = cur.fetchone()
    if not run:
        raise HTTPException(status_code=404, detail="Jadval topilmadi")
    slots = _v192_run_slots(cur, run_id)
    source, source_bundle = _v192_bundle_for_slot(slots, slot_id)
    if not source:
        raise HTTPException(status_code=404, detail="Tanlangan dars topilmadi")
    if any(str(row.get("fan_nomi") or "").strip().casefold() == "sinf soati" for row in source_bundle):
        raise HTTPException(status_code=409, detail="Sinf soati faqat 3-bosqichdagi qoida orqali ko'chiriladi")
    cur.execute("SELECT * FROM maktab_sinflari WHERE id=%s", (source["sinf_id"],))
    class_row = cur.fetchone()
    class_day_map = _v1856_class_day_rule_map(
        _v1856_class_day_rule_rows(cur, run["maktab_id"])
    )
    cur.execute("""SELECT * FROM aqlli_oqituvchi_vaqti_v2
                   WHERE maktab_id=%s""", (run["maktab_id"],))
    hard_rows = [dict(row) for row in cur.fetchall()]
    cur.execute("""SELECT dars_soni FROM aqlli_smena_sozlamalari_v2
                   WHERE maktab_id=%s AND smena=%s""",
                (run["maktab_id"], source["smena"]))
    shift = cur.fetchone()
    max_period = int((shift or {}).get("dars_soni") or 7)
    year = _v1852_active_year(cur, run["maktab_id"])
    weekdays = int((year or {}).get("hafta_kunlari") or 6)
    source_ids = {int(row["id"]) for row in source_bundle}
    suggestions = []
    for day in range(1, weekdays + 1):
        for period in range(1, max_period + 1):
            if day == int(source["hafta_kuni"]) and period == int(source["dars_raqami"]):
                continue
            target_bundle = [
                row for row in slots
                if int(row["sinf_id"]) == int(source["sinf_id"])
                and int(row["hafta_kuni"]) == day
                and int(row["smena"]) == int(source["smena"])
                and int(row["dars_raqami"]) == period
            ]
            if any(str(row.get("fan_nomi") or "").strip().casefold() == "sinf soati" for row in target_bundle):
                continue
            target_ids = {int(row["id"]) for row in target_bundle}
            projected_changes = {
                int(row["id"]): (day, period) for row in source_bundle
            }
            projected_changes.update({
                int(row["id"]): (
                    int(source["hafta_kuni"]), int(source["dars_raqami"])
                )
                for row in target_bundle
            })
            if not _v192_class_periods_contiguous(
                slots, int(source["sinf_id"]), projected_changes
            ):
                continue
            source_reasons = _v192_candidate_conflicts(
                source_bundle, day, period, slots, source_ids | target_ids,
                hard_rows, class_row, class_day_map,
            )
            target_reasons = []
            if target_bundle:
                target_reasons = _v192_candidate_conflicts(
                    target_bundle, int(source["hafta_kuni"]), int(source["dars_raqami"]),
                    slots, source_ids | target_ids, hard_rows, class_row, class_day_map,
                )
            reasons = list(dict.fromkeys(source_reasons + target_reasons))
            if reasons:
                continue
            kind = "almashtirish" if target_bundle else "kochirish"
            distance = abs(day - int(source["hafta_kuni"])) * 2 + abs(period - int(source["dars_raqami"]))
            teacher_daily = sum(
                1 for row in slots
                if row.get("oqituvchi_user_id") in {
                    item.get("oqituvchi_user_id") for item in source_bundle
                }
                and int(row["hafta_kuni"]) == day
            )
            class_grade = _v1874_grade(class_row)
            source_period_penalty = max(
                _v1874_subject_period_penalty(
                    _v1874_subject_profile(row.get("fan_nomi"), class_grade),
                    class_grade,
                    period,
                    max_period,
                )
                for row in source_bundle
            )
            target_period_penalty = 0
            if target_bundle:
                target_period_penalty = max(
                    _v1874_subject_period_penalty(
                        _v1874_subject_profile(row.get("fan_nomi"), class_grade),
                        class_grade,
                        int(source["dars_raqami"]),
                        max_period,
                    )
                    for row in target_bundle
                )
            score = (
                distance + teacher_daily
                + (3 if kind == "almashtirish" else 0)
                + source_period_penalty + target_period_penalty
            )
            suggestions.append({
                "turi": kind,
                "yangi_hafta_kuni": day,
                "yangi_smena": int(source["smena"]),
                "yangi_dars_raqami": period,
                "baho": score,
                "nishon": _v192_bundle_label(target_bundle),
                "nishon_slot_idlar": sorted(target_ids),
                "izoh": (
                    "Bo'sh katakka okno qoldirmasdan ko'chirish mumkin"
                    if not target_bundle
                    else "Ikki dars joyini oknosiz va xavfsiz almashtirish mumkin"
                ),
            })
    suggestions.sort(key=lambda row: (row["baho"], row["yangi_hafta_kuni"], row["yangi_dars_raqami"]))
    cur.execute("""SELECT avtomatik_tavsiya FROM aqlli_jadval_boshqaruv_v19_2
                   WHERE maktab_id=%s""", (run["maktab_id"],))
    mode = cur.fetchone()
    return {
        "urinish_id": int(run["id"]),
        "maktab_id": int(run["maktab_id"]),
        "manba": {
            "slot_id": int(source["id"]),
            "sinf_id": int(source["sinf_id"]),
            "sinf": f"{source['sinf']}-{source['harf']}",
            "fan": _v192_bundle_label(source_bundle),
            "hafta_kuni": int(source["hafta_kuni"]),
            "smena": int(source["smena"]),
            "dars_raqami": int(source["dars_raqami"]),
            "slot_idlar": sorted(source_ids),
        },
        "tavsiyalar": suggestions[:SAMTM_V19_2_SWAP_SUGGESTION_LIMIT],
        "avtomatik_tavsiya": (
            SAMTM_V19_2_AUTO_SWAP_DEFAULT
            if not mode else bool(mode["avtomatik_tavsiya"])
        ),
        "parallel_ziddiyatlar": _v192_parallel_conflicts(slots),
    }


@app.get("/api/maktab/aqlli_jadval/v3/almashtirish_tavsiyalari")
def v192_swap_suggestions(token: str, urinish_id: int, slot_id: int):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        cur.execute("SELECT maktab_id FROM aqlli_jadval_urinishlari_v2 WHERE id=%s", (urinish_id,))
        run = cur.fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Jadval topilmadi")
        if not _v1852_staff(cur, actor_id, run["maktab_id"]):
            raise HTTPException(status_code=403, detail="Ruxsat yo'q")
        result = _v192_swap_suggestions(cur, urinish_id, slot_id)
        conn.commit()
        return result
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


class V192SwapApply(BaseModel):
    urinish_id: int
    slot_id: int
    yangi_hafta_kuni: int
    yangi_dars_raqami: int
    turi: str = "almashtirish"


def _v192_clone_run(cur, run, actor_id: int):
    cur.execute("""INSERT INTO aqlli_jadval_urinishlari_v2(
                    maktab_id,holat,yaratgan_user_id,sifat,joylashtirildi,
                    joylashtirilmadi,diagnostika,sozlamalar)
                   VALUES(%s,'draft',%s,%s,%s,%s,%s,%s) RETURNING id""",
                (
                    run["maktab_id"], actor_id, run.get("sifat") or 0,
                    run.get("joylashtirildi") or 0, run.get("joylashtirilmadi") or 0,
                    psycopg2.extras.Json(run.get("diagnostika") or {}),
                    psycopg2.extras.Json({
                        **(run.get("sozlamalar") or {}),
                        "v19_2_manba_urinish_id": int(run["id"]),
                    }),
                ))
    new_run_id = int(cur.fetchone()["id"])
    cur.execute("""INSERT INTO aqlli_jadval_slotlari_v2(
                    urinish_id,maktab_id,sinf_id,hafta_kuni,smena,dars_raqami,
                    fan_nomi,oqituvchi_user_id,guruh_kaliti,xona_id,xona_matni,
                    boshlanish_vaqti,tugash_vaqti,yuklama_id,takror_raqami,hafta_turi)
                   SELECT %s,maktab_id,sinf_id,hafta_kuni,smena,dars_raqami,
                          fan_nomi,oqituvchi_user_id,guruh_kaliti,xona_id,xona_matni,
                          boshlanish_vaqti,tugash_vaqti,yuklama_id,takror_raqami,hafta_turi
                   FROM aqlli_jadval_slotlari_v2 WHERE urinish_id=%s""",
                (new_run_id, run["id"]))
    return new_run_id


class V192SlotRoomUpdate(BaseModel):
    urinish_id: int
    slot_id: int
    xona_id: Optional[int] = None
    xona_matni: Optional[str] = None


@app.put("/api/maktab/aqlli_jadval/v3/slot_xonasi")
def v192_slot_room_update(sorov: V192SlotRoomUpdate, token: str):
    """Jadval katagidagi xonani katalogdan yoki qo'lda xavfsiz tuzatadi."""
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        cur.execute(
            "SELECT * FROM aqlli_jadval_urinishlari_v2 WHERE id=%s FOR UPDATE",
            (sorov.urinish_id,),
        )
        original_run = cur.fetchone()
        if not original_run:
            raise HTTPException(status_code=404, detail="Jadval topilmadi")
        if not _v1852_manager(cur, actor_id, original_run["maktab_id"]):
            raise HTTPException(status_code=403, detail="Jadval xonasini faqat rahbariyat o'zgartiradi")

        original_slots = _v192_run_slots(cur, int(original_run["id"]))
        original_slot = next(
            (row for row in original_slots if int(row["id"]) == int(sorov.slot_id)),
            None,
        )
        if not original_slot:
            raise HTTPException(status_code=404, detail="Dars katagi topilmadi")

        run_id = int(original_run["id"])
        slot_id = int(sorov.slot_id)
        if original_run["holat"] == "tasdiqlangan":
            run_id = _v192_clone_run(cur, original_run, actor_id)
            cur.execute(
                """SELECT id FROM aqlli_jadval_slotlari_v2
                   WHERE urinish_id=%s AND sinf_id=%s AND hafta_kuni=%s
                     AND smena=%s AND dars_raqami=%s AND fan_nomi=%s
                     AND guruh_kaliti=%s
                     AND hafta_turi=%s
                     AND COALESCE(oqituvchi_user_id,0)=COALESCE(%s,0)
                     AND COALESCE(takror_raqami,0)=COALESCE(%s,0)
                   ORDER BY id LIMIT 1""",
                (
                    run_id, original_slot["sinf_id"], original_slot["hafta_kuni"],
                    original_slot["smena"], original_slot["dars_raqami"],
                    original_slot["fan_nomi"], original_slot["guruh_kaliti"],
                    original_slot.get("hafta_turi") or "har_hafta",
                    original_slot.get("oqituvchi_user_id"),
                    original_slot.get("takror_raqami"),
                ),
            )
            cloned_slot = cur.fetchone()
            if not cloned_slot:
                raise HTTPException(status_code=409, detail="Yangi draftdagi dars topilmadi")
            slot_id = int(cloned_slot["id"])
        elif original_run["holat"] != "draft":
            raise HTTPException(status_code=409, detail="Faqat draft yoki faol jadval xonasi o'zgartiriladi")

        room_id = int(sorov.xona_id) if sorov.xona_id is not None else None
        room_text = re.sub(r"\s+", " ", str(sorov.xona_matni or "")).strip()[:80] or None
        if room_id is not None:
            cur.execute(
                """SELECT id,nomi FROM aqlli_xonalar_v2
                   WHERE id=%s AND maktab_id=%s AND faol=TRUE AND darsga_yaroqli=TRUE""",
                (room_id, original_run["maktab_id"]),
            )
            selected_room = cur.fetchone()
            if not selected_room:
                raise HTTPException(status_code=400, detail="Tanlangan xona dars o'tishga yaroqli emas")
            room_text = selected_room["nomi"]
        if not room_text:
            cur.execute(
                """SELECT NULLIF(TRIM(CONCAT_WS(' ',bino,xona)),'') AS xona
                   FROM maktab_sinflari WHERE id=%s""",
                (original_slot["sinf_id"],),
            )
            class_room = cur.fetchone()
            room_text = class_room.get("xona") if class_room else None

        if room_text:
            cur.execute(
                """SELECT e.id,COALESCE(r.nomi,e.xona_matni) AS xona_nomi
                   FROM aqlli_jadval_slotlari_v2 e
                   LEFT JOIN aqlli_xonalar_v2 r ON r.id=e.xona_id
                   WHERE e.urinish_id=%s AND e.id<>%s AND e.hafta_kuni=%s
                     AND e.smena=%s AND e.dars_raqami=%s""",
                (
                    run_id, slot_id, original_slot["hafta_kuni"],
                    original_slot["smena"], original_slot["dars_raqami"],
                ),
            )
            normalized_room = room_text.casefold()
            if any(str(row.get("xona_nomi") or "").strip().casefold() == normalized_room for row in cur.fetchall()):
                raise HTTPException(status_code=409, detail=f"{room_text} bu vaqtda boshqa darsga band")

        cur.execute(
            """UPDATE aqlli_jadval_slotlari_v2
               SET xona_id=%s,xona_matni=%s WHERE id=%s""",
            (room_id, room_text, slot_id),
        )
        conn.commit()
        return {
            "holat": "xona_yangilandi",
            "urinish_id": run_id,
            "slot_id": slot_id,
            "xona_id": room_id,
            "xona": room_text,
            "yangi_draft": run_id != int(original_run["id"]),
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


@app.post("/api/maktab/aqlli_jadval/v3/almashtirish")
def v192_swap_apply(sorov: V192SwapApply, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        cur.execute("SELECT * FROM aqlli_jadval_urinishlari_v2 WHERE id=%s FOR UPDATE", (sorov.urinish_id,))
        original_run = cur.fetchone()
        if not original_run:
            raise HTTPException(status_code=404, detail="Jadval topilmadi")
        if not _v1852_manager(cur, actor_id, original_run["maktab_id"]):
            raise HTTPException(status_code=403, detail="Jadvalni faqat rahbariyat o'zgartiradi")
        source_slots = _v192_run_slots(cur, original_run["id"])
        original_source = next((row for row in source_slots if int(row["id"]) == int(sorov.slot_id)), None)
        if not original_source:
            raise HTTPException(status_code=404, detail="Dars topilmadi")

        run_id = int(original_run["id"])
        slot_id = int(sorov.slot_id)
        if original_run["holat"] == "tasdiqlangan":
            run_id = _v192_clone_run(cur, original_run, actor_id)
            cur.execute("""SELECT id FROM aqlli_jadval_slotlari_v2
                           WHERE urinish_id=%s AND sinf_id=%s AND hafta_kuni=%s
                             AND smena=%s AND dars_raqami=%s AND fan_nomi=%s
                             AND guruh_kaliti=%s LIMIT 1""",
                        (
                            run_id, original_source["sinf_id"], original_source["hafta_kuni"],
                            original_source["smena"], original_source["dars_raqami"],
                            original_source["fan_nomi"], original_source["guruh_kaliti"],
                        ))
            slot_id = int(cur.fetchone()["id"])
        elif original_run["holat"] != "draft":
            raise HTTPException(status_code=409, detail="Faqat draft yoki faol jadval o'zgartiriladi")

        report = _v192_swap_suggestions(cur, run_id, slot_id)
        candidate = next((
            row for row in report["tavsiyalar"]
            if int(row["yangi_hafta_kuni"]) == int(sorov.yangi_hafta_kuni)
            and int(row["yangi_dars_raqami"]) == int(sorov.yangi_dars_raqami)
            and str(row["turi"]) == str(sorov.turi)
        ), None)
        if not candidate:
            raise HTTPException(
                status_code=409,
                detail="Tanlangan joy endi xavfsiz emas. Tavsiyalarni qayta yuklang",
            )
        slots = _v192_run_slots(cur, run_id)
        source, source_bundle = _v192_bundle_for_slot(slots, slot_id)
        source_ids = [int(row["id"]) for row in source_bundle]
        target_bundle = [
            row for row in slots
            if int(row["sinf_id"]) == int(source["sinf_id"])
            and int(row["hafta_kuni"]) == int(candidate["yangi_hafta_kuni"])
            and int(row["smena"]) == int(source["smena"])
            and int(row["dars_raqami"]) == int(candidate["yangi_dars_raqami"])
        ]
        target_ids = [int(row["id"]) for row in target_bundle]
        old_day = int(source["hafta_kuni"])
        old_period = int(source["dars_raqami"])
        cur.execute("""UPDATE aqlli_jadval_slotlari_v2
                       SET hafta_kuni=7 WHERE id=ANY(%s)""", (source_ids,))
        if target_ids:
            cur.execute("""UPDATE aqlli_jadval_slotlari_v2
                           SET hafta_kuni=%s,dars_raqami=%s WHERE id=ANY(%s)""",
                        (old_day, old_period, target_ids))
        cur.execute("""UPDATE aqlli_jadval_slotlari_v2
                       SET hafta_kuni=%s,dars_raqami=%s WHERE id=ANY(%s)""",
                    (
                        int(candidate["yangi_hafta_kuni"]),
                        int(candidate["yangi_dars_raqami"]),
                        source_ids,
                    ))
        after_slots = _v192_run_slots(cur, run_id)
        parallel_conflicts = _v192_parallel_conflicts(after_slots)
        if parallel_conflicts:
            raise HTTPException(
                status_code=409,
                detail="O'qituvchi parallel darsga tushib qoldi; o'zgarish bekor qilindi",
            )
        cur.execute("""INSERT INTO aqlli_jadval_ozgarish_log_v19_2(
                        maktab_id,urinish_id,manba_slot_id,eski_hafta_kuni,
                        eski_dars_raqami,yangi_hafta_kuni,yangi_dars_raqami,
                        turi,bajargan_user_id)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        original_run["maktab_id"], run_id, slot_id, old_day, old_period,
                        candidate["yangi_hafta_kuni"], candidate["yangi_dars_raqami"],
                        candidate["turi"], actor_id,
                    ))
        exact = _v1875_schedule_integrity_report(cur, original_run["maktab_id"], run_id)
        hygiene = _v1874_schedule_hygiene_violations(cur, original_run["maktab_id"], run_id)
        class_blocks = _v1856_schedule_block_violations(cur, original_run["maktab_id"], run_id)
        diagnostic = {
            "tasdiqlash_mumkin": bool(exact.get("tayyor") and not hygiene and not class_blocks),
            "jadval_mosligi": exact,
            "gigiyena_xatolari": hygiene,
            "sinf_kun_xatolari": class_blocks,
            "v19_2_ozgartirish": {
                "turi": candidate["turi"],
                "eski": [old_day, old_period],
                "yangi": [candidate["yangi_hafta_kuni"], candidate["yangi_dars_raqami"]],
            },
        }
        cur.execute("""UPDATE aqlli_jadval_urinishlari_v2
                       SET diagnostika=%s WHERE id=%s""",
                    (psycopg2.extras.Json(diagnostic), run_id))
        conn.commit()
        return {
            "holat": "almashtirildi" if target_ids else "ko'chirildi",
            "urinish_id": run_id,
            "yangi_draft": run_id != int(original_run["id"]),
            "tasdiqlash_mumkin": diagnostic["tasdiqlash_mumkin"],
            "diagnostika": diagnostic,
        }
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


# ========================= V19.2 END =========================

# ═══════════════════════════════════════════════════════════
# V19.6 — PEDAGOGIK VA O'QITUVCHIGA QULAY JOYLASHTIRISH
# 0,5 fanlar A/B haftada aniq ko'rinadi. Generator sinf yoshiga mos
# dars vaqtini, og'ir/yengil fan almashuvini, jismoniy tarbiyadan
# keyingi tiklanishni va o'qituvchining oknosiz ixcham ish kunini
# birgalikda ballaydi.
# ═══════════════════════════════════════════════════════════

_v196_base_build_jobs = _v1852_build_jobs
_v196_base_candidate_reasons = _v1852_candidate_reasons
_v196_base_candidate_score = _v1852_candidate_score
_v196_base_place_job = _v1852_place_job
_v196_base_generate_attempt = _v1852_generate_attempt


def _v196_rotation_profile(job, context=None):
    """A/B slotning ikkala faniga ham mos yagona vaqt profilini qaytaradi."""
    profiles = []
    members = job.get("rotation_members") or []
    class_row = (context or {}).get("classes", {}).get(job.get("sinf_id"), {})
    grade = int(job.get("v1874_grade") or _v1874_grade(class_row))
    for member in members:
        profiles.append(
            member.get("v1874_profile")
            or _v1874_subject_profile(member.get("fan"), grade)
        )
    if not profiles:
        return job.get("v1874_profile") or _v1874_subject_profile(job.get("fan"), grade)

    # Eng talabchan a'zo slot vaqtini belgilaydi. "light" faqat ikkala fan
    # ham yengil bo'lganda rost: og'ir + yengil juftlik ertaroq joylashadi.
    most_difficult = max(profiles, key=lambda item: int(item.get("difficulty") or 0))
    return {
        **most_difficult,
        "key": " / ".join(str(profile.get("key") or "") for profile in profiles),
        "academic": any(bool(profile.get("academic")) for profile in profiles),
        "physical": any(bool(profile.get("physical")) for profile in profiles),
        "technology": any(bool(profile.get("technology")) for profile in profiles),
        "light": all(bool(profile.get("light")) for profile in profiles),
        "primary_light": all(bool(profile.get("primary_light")) for profile in profiles),
        "primary_core": any(bool(profile.get("primary_core")) for profile in profiles),
        "heavy": any(bool(profile.get("heavy")) for profile in profiles),
        "written_heavy": any(bool(profile.get("written_heavy")) for profile in profiles),
        "math": any(bool(profile.get("math")) for profile in profiles),
        "native_language": any(bool(profile.get("native_language")) for profile in profiles),
        "core_science": any(bool(profile.get("core_science")) for profile in profiles),
        "core_priority": any(bool(profile.get("core_priority")) for profile in profiles),
        "difficulty": max(int(profile.get("difficulty") or 0) for profile in profiles),
    }


def _v1852_candidate_reasons(
    job, day, period, selected_teachers, room_keys, state, context
):
    reasons = list(_v196_base_candidate_reasons(
        job, day, period, selected_teachers, room_keys, state, context
    ))
    # Oddiy urinishda fan kuniga bir marta qo‘yiladi. Jadvalning hamma darsi
    # sig‘may qolsa, generatorning zaxira urinishigina bitta sinfda haftasiga
    # avval 1 kun, mutlaqo iloj bo‘lmasa 2 kungacha shu fanni ikki marta
    # qo‘yishi mumkin. O‘qituvchining ayni vaqtdagi bandligi filtrlanmaydi.
    emergency_repeat_days = int(context.get("v203_emergency_repeat_days") or 0)
    if emergency_repeat_days and "fan kunlik maksimumga yetgan" in reasons:
        subject_counts = state.get("subject_daily", {})
        subject_key = str(job.get("fan") or "").casefold()
        current_count = int(subject_counts.get((job["sinf_id"], subject_key, day), 0))
        already_repeat_days = {
            int(subject_day)
            for (class_id, _subject, subject_day), count in subject_counts.items()
            if int(class_id) == int(job["sinf_id"]) and int(count or 0) >= 2
        }
        may_use_day = int(day) in already_repeat_days or len(already_repeat_days) < emergency_repeat_days
        if current_count < 2 and may_use_day:
            reasons = [reason for reason in reasons if reason not in {
                "fan kunlik maksimumga yetgan",
                "boshlang‘ich sinfda bir fan shu kuni takror qo‘yilmaydi",
            }]
    profile = _v196_rotation_profile(job, context)
    if int(period) == 1 and (
        profile.get("physical") or profile.get("technology")
    ):
        reasons.append(
            "jismoniy tarbiya va texnologiya 1-darsga qo'yilmaydi"
        )

    # Sinf kuni doimo 1-darsdan boshlanib uzluksiz ketadi. Bu ilgari faqat
    # katta yumshoq jarima edi; boshqa o'qituvchi/xona cheklovlari yig'indisi
    # uni yengib, 1–2–3–bo'sh–5 yoki bo'sh–2–3 kabi jadval qoldirardi.
    # Rahbariyat aniq katakka qotirgan SINIF SOATI bundan mustasno: u avval
    # joylashadi, qolgan fanlar esa ikki tomondan bo'shliqni yopib boradi.
    if not (int(job.get("fixed_day") or 0) and int(job.get("fixed_period") or 0)):
        class_periods = set(
            state.get("class_period_jobs", {}).get(
                (job.get("sinf_id"), int(day)), {}
            ).keys()
        )
        new_periods = class_periods | {int(period)}
        old_void = max(class_periods) - len(class_periods) if class_periods else 0
        new_void = max(new_periods) - len(new_periods) if new_periods else 0
        if new_void > old_void:
            reasons.append("sinf jadvalida bo'sh dars qoldirilmaydi")
    return list(dict.fromkeys(reasons))


def _v1852_build_jobs(classes, loads, assignments, group_settings, teachers):
    jobs, warnings = _v196_base_build_jobs(
        classes, loads, assignments, group_settings, teachers
    )
    rotation_count = 0
    for job in jobs:
        if job.get("rotation_members"):
            rotation_count += 1
            job["v1874_profile"] = _v196_rotation_profile(
                job, {"classes": classes}
            )
    warnings.append(
        "V19.8 pedagogik strategiya faol: ona tili, adabiyot, matematika, "
        "algebra, geometriya, fizika, kimyo va biologiya 1–4-darsga; jismoniy "
        "tarbiya 3–6-darsga ustuvor. O'qituvchining ichki oknosi va ikki smena "
        "orasidagi uzoq kutish birgalikda kamaytiriladi"
    )
    if rotation_count:
        warnings.append(
            f"A/B ko'rinishi: {rotation_count} ta jadval katagida 0,5 fanlar "
            "TOQ/JUFT hafta yorlig'i bilan almashadi"
        )
    return jobs, warnings


def _v196_grade_period_penalty(profile, grade, period):
    """Sinf yoshi va fan zo'riqishiga mos yumshoq dars-vaqti balli."""
    grade = int(grade or 0)
    period = int(period or 0)
    heavy = bool(profile.get("heavy") or profile.get("written_heavy"))
    light = bool(profile.get("light"))
    physical = bool(profile.get("physical"))

    if physical:
        # J/T 1-darsga qo'yilmaydi, 2-dars faqat boshqa majburiy cheklov
        # bo'lsa ishlatiladi. Asosiy yo'lak 3–6; ayniqsa 4–6 qulay.
        return {1: 520, 2: 280, 3: 35, 4: -24, 5: -36, 6: -40}.get(period, 80)

    if profile.get("technology"):
        return {1: 380, 2: 240, 3: 55, 4: -15, 5: -28, 6: -32}.get(period, 80)

    # Ona tili/adabiyot, matematika–algebra–geometriya hamda fizika, kimyo,
    # biologiya kabi asosiy fanlar 1–4-darsda bo'lishi kerak. 5–6 yumshoq
    # istisno bo'lib qoladi, lekin generator undan juda qimmat variant sifatida
    # foydalanadi. Bu J/T dan keyin 5–6-dars algebra/geometriya chiqishini kesadi.
    if profile.get("core_priority"):
        if 1 <= grade <= 4:
            return {1: -34, 2: -42, 3: -34, 4: -14, 5: 210, 6: 430}.get(period, 500)
        return {1: -38, 2: -46, 3: -38, 4: -16, 5: 240, 6: 480}.get(period, 560)

    if 1 <= grade <= 4:
        if heavy or profile.get("primary_core"):
            return {1: 5, 2: -14, 3: -12, 4: 5, 5: 70}.get(period, 90)
        return 0

    # 5–6-sinf o'quvchisi uchun 1-dars 9–11-sinfga qaraganda mosroq;
    # eng talabchan fanlar baribir 2–3-darsda qoladi.
    if 5 <= grade <= 6:
        if heavy:
            return {1: -5, 2: -15, 3: -11, 4: 1, 5: 14, 6: 30}.get(period, 35)
        if not light and not physical:
            return {1: -6, 2: -9, 3: -6, 4: 0, 5: 5, 6: 11}.get(period, 15)
        return 0

    if 7 <= grade <= 8:
        if heavy:
            return {1: 5, 2: -13, 3: -15, 4: -9, 5: 8, 6: 24}.get(period, 30)
        if not light and not physical:
            return {1: 2, 2: -7, 3: -8, 4: -5, 5: 2, 6: 9}.get(period, 15)
        return 0

    if 9 <= grade <= 11:
        if heavy:
            return {1: 24, 2: -10, 3: -17, 4: -12, 5: 7, 6: 22}.get(period, 32)
        if not light and not physical:
            return {1: 9, 2: -5, 3: -9, 4: -6, 5: 1, 6: 8}.get(period, 14)
    return 0


def _v196_teacher_shift_demand(jobs):
    """O'qituvchining qaysi smenalarda darsi borligini oldindan hisoblaydi."""
    result = _v1852_defaultdict(lambda: _v1852_defaultdict(float))
    for job in jobs:
        shift = int(job.get("smena") or 1)
        members = job.get("rotation_members") or []
        source_jobs = members or [job]
        contribution = 0.5 if members else 1.0
        for source in source_jobs:
            teachers = _v1852_job_teacher_ids(source)
            for teacher in teachers:
                result[int(teacher)][shift] += contribution
    return {teacher: dict(shifts) for teacher, shifts in result.items()}


def _v196_shift_max_period(context, shift):
    slots = (context.get("shifts", {}).get(int(shift), {}) or {}).get("slotlar") or []
    return max([int(slot.get("dars_raqami") or 0) for slot in slots] or [6])


def _v196_clock_minutes(value):
    text = _v1852_time_str(value)
    try:
        hour, minute = text.split(":", 1)
        return int(hour) * 60 + int(minute[:2])
    except (TypeError, ValueError, AttributeError):
        return None


def _v196_slot_interval(context, shift, period):
    slots = (context.get("shifts", {}).get(int(shift), {}) or {}).get("slotlar") or []
    row = next(
        (slot for slot in slots if int(slot.get("dars_raqami") or 0) == int(period)),
        None,
    )
    if not row:
        return None
    start = _v196_clock_minutes(row.get("boshlanish"))
    end = _v196_clock_minutes(row.get("tugash"))
    return (start, end) if start is not None and end is not None else None


def _v196_cross_shift_gap_minutes(state, teacher, day, context, extra=None):
    """1-smena oxiri bilan 2-smena boshi orasidagi haqiqiy daqiqalar."""
    by_shift = {}
    for shift in (1, 2):
        by_shift[shift] = set(
            int(value) for value in state.get("teacher_periods", {}).get(
                (int(teacher), int(day), shift), set()
            )
        )
    if extra:
        shift, period = extra
        by_shift.setdefault(int(shift), set()).add(int(period))
    if not by_shift.get(1) or not by_shift.get(2):
        return None
    first_intervals = [
        _v196_slot_interval(context, 1, period) for period in by_shift[1]
    ]
    second_intervals = [
        _v196_slot_interval(context, 2, period) for period in by_shift[2]
    ]
    first_intervals = [row for row in first_intervals if row]
    second_intervals = [row for row in second_intervals if row]
    if not first_intervals or not second_intervals:
        return None
    latest_first_end = max(row[1] for row in first_intervals)
    earliest_second_start = min(row[0] for row in second_intervals)
    return int(max(0, earliest_second_start - latest_first_end))


def _v200_teacher_day_timeline(state, teacher, day, context, extra=None):
    """Ikki smenani bitta haqiqiy vaqt chizig'iga birlashtiradi."""
    intervals = set()
    for shift in (1, 2):
        periods = state.get("teacher_periods", {}).get(
            (int(teacher), int(day), shift), set()
        )
        for period in periods:
            interval = _v196_slot_interval(context, shift, period)
            if interval:
                intervals.add((int(interval[0]), int(interval[1]), shift, int(period)))
    if extra:
        shift, period = int(extra[0]), int(extra[1])
        interval = _v196_slot_interval(context, shift, period)
        if interval:
            intervals.add((int(interval[0]), int(interval[1]), shift, period))
    return sorted(intervals, key=lambda row: (row[0], row[1], row[2], row[3]))


def _v200_teacher_day_idle(state, teacher, day, context, extra=None):
    """Oddiy tanaffusdan katta bo'sh kutishni haqiqiy daqiqada qaytaradi.

    25 daqiqagacha bo'lgan odatiy tanaffus okno emas. Bir yoki ikki smena
    alohida sanalmaydi: ustozning ertalabki birinchi darsidan kechki oxirgi
    darsigacha bo'lgan bitta real ish kuni tekshiriladi.
    """
    timeline = _v200_teacher_day_timeline(
        state, teacher, day, context, extra=extra
    )
    gaps = []
    for previous, current in zip(timeline, timeline[1:]):
        minutes = max(0, int(current[0]) - int(previous[1]))
        if minutes > 25:
            gaps.append(minutes)
    return {
        "jami_daqiqa": int(sum(gaps)),
        "eng_katta_daqiqa": int(max(gaps or [0])),
        "okno_soni": int(len(gaps)),
        "ikki_soatdan_uzoq": int(sum(1 for value in gaps if value > 120)),
        "uch_soatdan_uzoq": int(sum(1 for value in gaps if value > 180)),
    }


def _v200_all_teacher_idle_signature(state, context):
    days = {
        (int(teacher), int(day))
        for (teacher, day), count in state.get("teacher_daily", {}).items()
        if float(count or 0) > 0
    }
    profiles = [
        _v200_teacher_day_idle(state, teacher, day, context)
        for teacher, day in days
    ]
    return (
        sum(row["uch_soatdan_uzoq"] for row in profiles),
        sum(row["ikki_soatdan_uzoq"] for row in profiles),
        max([row["eng_katta_daqiqa"] for row in profiles] or [0]),
        sum(row["jami_daqiqa"] for row in profiles),
        sum(row["okno_soni"] for row in profiles),
    )


def _v196_cross_shift_gap_penalty(minutes):
    """1–2 soat qulay, 3 soat istisno, 3 soatdan ortiq juda qimmat."""
    if minutes is None:
        return 0.0
    minutes = max(0, int(minutes))
    if minutes <= 60:
        return minutes * 0.08
    if minutes <= 120:
        return 4.8 + (minutes - 60) * 0.45
    if minutes <= 180:
        return 31.8 + (minutes - 120) * 18.0
    # 3 soatdan oshgan variant faqat boshqa qattiq cheklov sabab mutlaqo
    # iloj qolmaganda yashab qolishi mumkin. 4–5 soatlik kutish endi oddiy
    # pedagogik bonuslar bilan hech qachon yengilmaydi.
    return 1111.8 + (minutes - 180) * 95.0


def _v196_cross_shift_edge_blocks(state, teacher, day, context, extra=None):
    """Ikki smena orasidagi oldini olish mumkin bo'lgan bo'sh bloklar.

    1-smena oxiridagi bo'sh darslar + 2-smena boshidagi bo'sh darslar olinadi.
    Masalan, 1-smena 1–3 va 2-smena 4–5 bo'lsa 3+3=6 blok; 1-smena
    4–6 va 2-smena 1–2 bo'lsa 0 blok. Faqat ikkala smena shu kunda faol
    bo'lgandagina qiymat qaytariladi.
    """
    by_shift = {}
    for shift in (1, 2):
        by_shift[shift] = set(
            int(value) for value in state.get("teacher_periods", {}).get(
                (int(teacher), int(day), shift), set()
            )
        )
    if extra:
        shift, period = extra
        by_shift.setdefault(int(shift), set()).add(int(period))
    if not by_shift.get(1) or not by_shift.get(2):
        return None
    return int(
        max(0, _v196_shift_max_period(context, 1) - max(by_shift[1]))
        + max(0, min(by_shift[2]) - 1)
    )


def _v196_teacher_demand(jobs):
    demand = _v1852_defaultdict(float)
    for job in jobs:
        members = job.get("rotation_members") or []
        if members:
            for member in members:
                teachers = [
                    teacher for teacher in _v199_rotation_member_teachers(member)
                    if teacher is not None
                ]
                for teacher in set(teachers):
                    demand[int(teacher)] += 0.5
            continue
        if job.get("groups"):
            for teacher in {
                group.get("teacher") for group in job.get("groups") or []
                if group.get("teacher") is not None
            }:
                demand[int(teacher)] += 1.0
            continue
        options = [teacher for teacher in job.get("teacher_options") or [] if teacher is not None]
        share = 1.0 / max(1, len(options))
        for teacher in options:
            demand[int(teacher)] += share
    return dict(demand)


def _v196_teacher_used_days(state, teacher):
    return {
        int(day) for (uid, day), count in state.get("teacher_daily", {}).items()
        if int(uid) == int(teacher) and float(count or 0) > 0
    }


def _v196_teacher_target_days(demand, rules):
    """Haftalik yuklamaga mos ixcham, lekin real ishlash kunlari soni."""
    demand = float(demand or 0)
    daily_limit = max(1, min(6, int((rules or {}).get("kunlik_max") or 6)))
    minimum = max(1, int(math.ceil(demand / daily_limit)))
    if 10 <= demand < 15:
        # 10–14,5 soat: 3 kun; kunlik sig'im yetmasa 4-kun.
        return max(3, minimum)
    if 15 <= demand < 20:
        # 15–19,5 soat: 4 kun; kunlik sig'im yetmasa 5-kun.
        return max(4, minimum)
    compact_capacity = max(1, min(4, daily_limit))
    return max(minimum, int(math.ceil(demand / compact_capacity)))


def _v201_teacher_fallback_days(demand, rules):
    """Maqsad sig'masa ruxsat etiladigan birinchi zaxira kun soni."""
    demand = float(demand or 0)
    target = _v196_teacher_target_days(demand, rules)
    if 10 <= demand < 15:
        return max(target, 4)
    if 15 <= demand < 20:
        return max(target, 5)
    return target


def _v196_class_distribution(jobs, context):
    """Har bir sinf uchun 4/5/6 darsli barqaror kun maqsadini tayyorlaydi."""
    totals = _v1852_Counter(int(job["sinf_id"]) for job in jobs)
    result = {}
    weekdays = int(context.get("weekdays") or 6)
    for class_id, total in totals.items():
        class_row = context.get("classes", {}).get(class_id, {})
        grade = _v1874_grade(class_row)
        allowed = []
        for day in range(1, weekdays + 1):
            if 1 <= grade <= 4 and day == 6:
                continue
            if _v1856_class_day_block_reason(
                class_row, day, context.get("class_day_blocks", {})
            ):
                continue
            allowed.append(day)
        if not allowed:
            continue
        low, remainder = divmod(int(total), len(allowed))
        result[class_id] = {
            "total": int(total),
            "days": tuple(allowed),
            "low": int(low),
            "high": int(low + (1 if remainder else 0)),
            "remainder": int(remainder),
        }
    return result


def _v196_class_distribution_metrics(state, context):
    imbalance = 0
    short_days = 0
    for class_id, target in (context.get("v196_class_distribution") or {}).items():
        days = list(target["days"])
        actual = sorted(
            int(state.get("class_daily_total", {}).get((class_id, day), 0))
            for day in days
        )
        ideal = sorted(
            [target["low"]] * (len(days) - target["remainder"])
            + [target["high"]] * target["remainder"]
        )
        imbalance += sum(abs(a - b) for a, b in zip(actual, ideal))
        short_days += sum(1 for count in actual if 0 < count < target["low"])
    return int(imbalance), int(short_days)


def _v1852_candidate_score(job, day, period, teachers, state, context, rng):
    score = float(_v196_base_candidate_score(
        job, day, period, teachers, state, context, rng
    ))
    profile = _v196_rotation_profile(job, context)
    class_row = context.get("classes", {}).get(job.get("sinf_id"), {})
    grade = int(job.get("v1874_grade") or _v1874_grade(class_row))
    score += _v196_grade_period_penalty(profile, grade, period)

    # Sinf kuni 1-darsdan boshlanib uzluksiz ketishi kerak. Oldingi 650
    # ballik jarimani boshqa yumshoq qulayliklar yig'indisi ba'zan yengib
    # ketardi. Qo'shimcha katta qiymat sinf oknosini deyarli qattiq shartga
    # aylantiradi; yakuniy repair qolgan istisnolarni xavfsiz siqadi.
    class_periods = set(
        state.get("class_period_jobs", {}).get((job.get("sinf_id"), day), {}).keys()
    )
    new_class_periods = class_periods | {int(period)}
    old_class_void = max(class_periods) - len(class_periods) if class_periods else 0
    new_class_void = (
        max(new_class_periods) - len(new_class_periods)
        if new_class_periods else 0
    )
    score += (new_class_void - old_class_void) * 4350

    # Sinf haftasini 2 ta darsli va 7 ta darsli kunlarga parchalamasdan,
    # reja jami bo'yicha imkon qadar teng 4/5/6 darsli kunlarga yoyamiz.
    target = (context.get("v196_class_distribution") or {}).get(job.get("sinf_id"))
    if target and int(day) in target["days"]:
        daily_map = state.get("class_daily_total", {})
        current = int(daily_map.get((job.get("sinf_id"), day), 0))
        other_counts = [
            int(daily_map.get((job.get("sinf_id"), item_day), 0))
            for item_day in target["days"] if int(item_day) != int(day)
        ]
        if current < target["low"]:
            score -= (target["low"] - current) * 115
        elif any(count < target["low"] for count in other_counts):
            score += 210 + sum(max(0, target["low"] - count) for count in other_counts) * 18
        if current >= target["high"]:
            score += (current - target["high"] + 1) * 330

    teacher_jobs = state.setdefault(
        "v196_teacher_period_jobs", _v1852_defaultdict(dict)
    )
    demands = context.get("v196_teacher_demand") or {}
    shift_demands = context.get("v196_teacher_shift_demand") or {}
    for teacher in teachers:
        if teacher is None:
            continue
        teacher = int(teacher)
        existing = set(
            state.get("teacher_periods", {}).get(
                (teacher, day, job.get("smena")), set()
            )
        )
        before_gap = _v1852_gap_count(existing)
        after_gap = _v1852_gap_count(existing | {int(period)})

        # Bazaviy ball yangi oknoga juda kichik jazo beradi. V19.6 da
        # o'qituvchining 1–2–bo'sh–4 kabi kuni ancha qimmat hisoblanadi.
        new_internal_gaps = max(0, after_gap - before_gap)
        score += new_internal_gaps * 1100
        if after_gap > 1:
            score += (after_gap - 1) * 1750
        daily_count = float(state.get("teacher_daily", {}).get((teacher, day), 0) or 0)

        # Eng muhim o'qituvchi mezoni: 1- va 2-smena bitta 12 soatlik vaqt
        # chizig'i sifatida baholanadi. Yangi dars 4–5 soatlik kutish yaratsa
        # J/Tni 3–5-darsga qo'yish kabi pedagogik bonuslardan ancha qimmat
        # bo'ladi; darslar yonma-yonlashsa esa kuchli bonus oladi.
        before_idle = _v200_teacher_day_idle(
            state, teacher, day, context
        )
        after_idle = _v200_teacher_day_idle(
            state, teacher, day, context,
            extra=(int(job.get("smena") or 1), int(period)),
        )
        score += (
            (after_idle["jami_daqiqa"] - before_idle["jami_daqiqa"]) * 11.0
            + (after_idle["okno_soni"] - before_idle["okno_soni"]) * 900
            + (after_idle["ikki_soatdan_uzoq"] - before_idle["ikki_soatdan_uzoq"]) * 4200
            + (after_idle["uch_soatdan_uzoq"] - before_idle["uch_soatdan_uzoq"]) * 12000
        )
        if existing and any(abs(int(period) - item) == 1 for item in existing):
            score -= 125
        if daily_count > 0:
            # Bazadagi +1.8 tarqatish jarimasini bekor qilib, ixcham kunni afzal qilamiz.
            score -= daily_count * 4.0

        # Ikki smenada ishlaydigan ustoz uchun 1-smena darslari kun oxiriga,
        # 2-smena darslari kun boshiga yaqinlashadi. Shunda 1-smenada 1–3,
        # keyin 2-smenada 4–5 kabi uzoq kutish o'rniga 4–6 + 1–2 chiqadi.
        teacher_shifts = {
            int(shift): float(value or 0)
            for shift, value in (shift_demands.get(teacher) or {}).items()
            if float(value or 0) > 0
        }
        if 1 in teacher_shifts and 2 in teacher_shifts:
            current_shift = int(job.get("smena") or 1)
            if current_shift == 1:
                score += max(0, _v196_shift_max_period(context, 1) - int(period)) * 245
            elif current_shift == 2:
                score += max(0, int(period) - 1) * 245

            before_cross = _v196_cross_shift_gap_minutes(
                state, teacher, day, context
            )
            after_cross = _v196_cross_shift_gap_minutes(
                state, teacher, day, context,
                extra=(current_shift, int(period)),
            )
            if before_cross is None and after_cross is not None:
                # Ikki smenani bir kunga ixcham birlashtirish foydali, ammo
                # haqiqiy tanaffus 3 soatdan oshsa bu bonus butunlay yo'qoladi.
                if int(after_cross) <= 120:
                    score -= 430
                elif int(after_cross) <= 180:
                    score -= 90
                score += _v196_cross_shift_gap_penalty(after_cross)
            elif before_cross is not None and after_cross is not None:
                score += (
                    _v196_cross_shift_gap_penalty(after_cross)
                    - _v196_cross_shift_gap_penalty(before_cross)
                )

        used_days = _v196_teacher_used_days(state, teacher)
        rules = context.get("rules", {}).get(teacher, context.get("default_rules", {}))
        teacher_demand = float(demands.get(teacher, 1.0) or 1.0)
        expected_days = _v196_teacher_target_days(teacher_demand, rules)
        if 10 <= teacher_demand < 20:
            if int(day) not in used_days:
                projected_days = sorted(used_days | {int(day)})
                projected_count = len(projected_days)
                adjacent_pairs = sum(
                    1 for left, right in zip(projected_days, projected_days[1:])
                    if right - left == 1
                )
                fallback_days = _v201_teacher_fallback_days(teacher_demand, rules)
                if projected_count > fallback_days:
                    # 10–14 soatni 5–6 kunga yoki 15–19 soatni 6 kunga
                    # yoyish faqat qattiq cheklovlar majbur qilganda qoladigan
                    # juda qimmat zaxira variantidir.
                    score += 22000 + (projected_count - fallback_days) * 12000
                elif projected_count > expected_days:
                    # Birinchi zaxira: 10–14 uchun 4-kun, 15–19 uchun 5-kun.
                    # Dars tashlab ketilmasligi uchun bu qattiq taqiq emas.
                    score += 5200 + (projected_count - expected_days - 1) * 3800
                else:
                    # Dushanba–Chorshanba–Juma yoki
                    # Seshanba–Payshanba–Shanba kabi oralatib ishlash. 4 kun
                    # kerak bo'lganda bitta yonma-yon juft tabiiy hisoblanadi.
                    allowed_adjacent = 0 if expected_days <= 3 else 1
                    score += max(0, adjacent_pairs - allowed_adjacent) * 760
                    if used_days and adjacent_pairs == 0:
                        score -= 150
            else:
                desired_daily = max(3, int(math.ceil(teacher_demand / expected_days)))
                if daily_count >= desired_daily:
                    score += (daily_count - desired_daily + 1) * 420
        elif int(day) not in used_days and len(used_days) >= expected_days:
            score += 120 + (len(used_days) - expected_days) * 45

        # Ketma-ket darslarda juda uzoq sinf bosqichlari orasida sakrashni
        # kamaytirish: 5-sinfdan birdan 11-sinfga o'tish zarur bo'lmasa tanlanmaydi.
        neighbor_jobs = teacher_jobs.get((teacher, day, job.get("smena")), {})
        if profile.get("physical") or profile.get("technology"):
            practical_periods = [
                int(item_period)
                for item_period, item_job in neighbor_jobs.items()
                if (
                    _v196_rotation_profile(item_job, context).get("physical")
                    or _v196_rotation_profile(item_job, context).get("technology")
                )
            ]
            if practical_periods:
                nearest = min(abs(int(period) - item) for item in practical_periods)
                if nearest == 1:
                    # J/T yoki texnologiya ustozining ikki darsi 4–5 yoki 5–6
                    # kabi uzluksiz tursin.
                    score -= 130
                else:
                    score += max(1, nearest - 1) * 95
        for neighbor_period in (int(period) - 1, int(period) + 1):
            neighbor = neighbor_jobs.get(neighbor_period)
            if not neighbor:
                continue
            neighbor_grade = int(
                neighbor.get("v1874_grade")
                or _v1874_grade(context.get("classes", {}).get(neighbor.get("sinf_id"), {}))
            )
            grade_distance = abs(grade - neighbor_grade)
            if grade_distance <= 1:
                score -= 3
            elif grade_distance >= 5:
                score += 7

    # Bir kunda ketma-ket ikki og'ir yozma fan bo'lsa charchoq oshadi.
    daily_jobs = state.get("class_period_jobs", {}).get((job.get("sinf_id"), day), {})
    for neighbor_period in (int(period) - 1, int(period) + 1):
        neighbor = daily_jobs.get(neighbor_period)
        if not neighbor:
            continue
        neighbor_profile = _v196_rotation_profile(neighbor, context)
        if profile.get("heavy") and neighbor_profile.get("heavy"):
            score += 32
        if neighbor_period == int(period) - 1 and neighbor_profile.get("physical"):
            if profile.get("core_priority"):
                score += 1600
            elif profile.get("written_heavy"):
                score += 900
            elif profile.get("light"):
                score -= 12
            if profile.get("technology"):
                score -= 34
        if neighbor_period == int(period) + 1 and profile.get("physical"):
            if neighbor_profile.get("core_priority"):
                score += 1600
            elif neighbor_profile.get("written_heavy"):
                score += 900
            elif neighbor_profile.get("light"):
                score -= 12
            if neighbor_profile.get("technology"):
                score -= 34
        # To'g'ri pedagogik yo'nalish: avval asosiy fan, keyin J/T; yoki J/T dan
        # keyin texnologiya/yengil fan. Bu bonus yuqoridagi noto'g'ri ketma-ketlik
        # jarimasidan kichik, ya'ni qattiq cheklovlarni buzmaydi.
        if neighbor_period == int(period) - 1:
            if profile.get("physical") and neighbor_profile.get("core_priority"):
                score -= 85
            if profile.get("technology") and neighbor_profile.get("physical"):
                score -= 70
        if neighbor_period == int(period) + 1:
            if profile.get("core_priority") and neighbor_profile.get("physical"):
                score -= 85
            if profile.get("physical") and neighbor_profile.get("technology"):
                score -= 70
    return score


def _v1852_place_job(job, day, period, teachers, room_keys, state, context):
    _v196_base_place_job(job, day, period, teachers, room_keys, state, context)
    teacher_jobs = state.setdefault(
        "v196_teacher_period_jobs", _v1852_defaultdict(dict)
    )
    for teacher in teachers:
        if teacher is not None:
            teacher_jobs[(int(teacher), int(day), int(job.get("smena") or 1))][int(period)] = job


def _v196_class_gap_count(state):
    """Sinf kunidagi bosh va ichki bo'sh darslarning aniq soni."""
    return int(sum(
        max(set(period_jobs.keys())) - len(set(period_jobs.keys()))
        if period_jobs else 0
        for period_jobs in state.get("class_period_jobs", {}).values()
    ))


def _v196_movable_placement(placement):
    job = placement.get("job") or {}
    return not (
        job.get("is_class_hour")
        or int(job.get("fixed_day") or 0)
        or int(job.get("fixed_period") or 0)
    )


def _v196_place_exact(
    job, day, period, state, context, rng, expected_teachers=None
):
    candidates, _ = _v1852_open_candidates(
        job, state, context, rng, exact=(int(day), int(period))
    )
    if expected_teachers is not None:
        expected = {
            int(teacher) for teacher in expected_teachers
            if teacher is not None
        }
        candidates = [
            candidate for candidate in candidates
            if {
                int(teacher) for teacher in candidate[3]
                if teacher is not None
            } == expected
        ]
    if not candidates:
        return False
    _, target_day, target_period, teachers, rooms = candidates[0]
    _v1852_place_job(
        job, target_day, target_period, teachers, rooms, state, context
    )
    return True


def _v196_compact_class_gaps(state, context, rng, max_moves=32):
    """1–2–3–bo'sh–5 ni 1–2–3–4 ko'rinishiga xavfsiz siqadi."""
    moves = 0
    while moves < int(max_moves):
        before_gap = _v196_class_gap_count(state)
        if before_gap <= 0:
            break
        changed = False
        class_days = sorted(
            state.get("class_period_jobs", {}).items(),
            key=lambda item: (
                -(max(item[1]) - len(item[1]) if item[1] else 0),
                int(item[0][0]), int(item[0][1]),
            ),
        )
        for (class_id, day), period_jobs in class_days:
            periods = sorted(int(value) for value in period_jobs)
            if not periods:
                continue
            missing = next(
                (value for value in range(1, max(periods)) if value not in period_jobs),
                None,
            )
            if missing is None:
                continue
            donors = sorted(
                [
                    placement for placement in state.get("placements", [])
                    if int(placement["job"].get("sinf_id") or 0) == int(class_id)
                    and int(placement.get("day") or 0) == int(day)
                    and int(placement.get("period") or 0) > int(missing)
                    and _v196_movable_placement(placement)
                ],
                key=lambda placement: int(placement.get("period") or 0),
                reverse=True,
            )
            for donor in donors:
                donor_id = id(donor)
                trial = _v1852_rebuild_schedule_state(
                    [
                        placement for placement in state.get("placements", [])
                        if id(placement) != donor_id
                    ],
                    context,
                )
                if not _v196_place_exact(
                    donor["job"], day, missing, trial, context, rng
                ):
                    continue
                if _v196_class_gap_count(trial) >= before_gap:
                    continue
                state = trial
                moves += 1
                changed = True
                break
            if changed:
                break
        if not changed:
            break
    state["class_gap_count"] = _v196_class_gap_count(state)
    return state


def _v196_balance_class_days(state, context, rng, max_moves=24):
    """2/6 kabi notekis kunlarni reja bo'yicha 4/5/6 ga tenglashtiradi."""
    moves = 0
    while moves < int(max_moves):
        before_imbalance, _ = _v196_class_distribution_metrics(state, context)
        if before_imbalance <= 0:
            break
        changed = False
        for class_id, target in sorted(
            (context.get("v196_class_distribution") or {}).items()
        ):
            counts = {
                int(day): int(
                    state.get("class_daily_total", {}).get((class_id, day), 0)
                )
                for day in target["days"]
            }
            recipients = sorted(
                [day for day, count in counts.items() if count < int(target["low"])],
                key=lambda day: (counts[day], day),
            )
            donors = sorted(
                [day for day, count in counts.items() if count > int(target["high"])],
                key=lambda day: (-counts[day], day),
            )
            if not recipients:
                recipients = sorted(
                    [day for day in counts if counts[day] == min(counts.values())]
                )
            if not donors:
                donors = sorted(
                    [day for day in counts if counts[day] == max(counts.values())]
                )
            for recipient in recipients:
                for donor_day in donors:
                    if counts[donor_day] - counts[recipient] < 2:
                        continue
                    recipient_periods = state.get("class_period_jobs", {}).get(
                        (class_id, recipient), {}
                    )
                    target_period = len(recipient_periods) + 1
                    if target_period in recipient_periods:
                        continue
                    donor_placements = sorted(
                        [
                            placement for placement in state.get("placements", [])
                            if int(placement["job"].get("sinf_id") or 0) == int(class_id)
                            and int(placement.get("day") or 0) == int(donor_day)
                            and _v196_movable_placement(placement)
                        ],
                        key=lambda placement: int(placement.get("period") or 0),
                        reverse=True,
                    )
                    for donor in donor_placements:
                        donor_id = id(donor)
                        trial = _v1852_rebuild_schedule_state(
                            [
                                placement for placement in state.get("placements", [])
                                if id(placement) != donor_id
                            ],
                            context,
                        )
                        if not _v196_place_exact(
                            donor["job"], recipient, target_period,
                            trial, context, rng,
                        ):
                            continue
                        trial = _v196_compact_class_gaps(
                            trial, context, rng, max_moves=4
                        )
                        after_imbalance, _ = _v196_class_distribution_metrics(
                            trial, context
                        )
                        if after_imbalance >= before_imbalance:
                            continue
                        if _v196_class_gap_count(trial) > _v196_class_gap_count(state):
                            continue
                        state = trial
                        moves += 1
                        changed = True
                        break
                    if changed:
                        break
                if changed:
                    break
            if changed:
                break
        if not changed:
            break
    return state


def _v196_relocate_early_practical(state, context, rng, max_swaps=24):
    """J/T va texnologiyani 1–2-darsdan 3–6-darsga xavfsiz almashtiradi."""
    swaps = 0
    while swaps < int(max_swaps):
        current_teacher_idle = _v200_all_teacher_idle_signature(state, context)
        early = []
        for placement in state.get("placements", []):
            profile = _v196_rotation_profile(placement["job"], context)
            if (
                int(placement.get("period") or 0) <= 2
                and (profile.get("physical") or profile.get("technology"))
                and _v196_movable_placement(placement)
            ):
                early.append(placement)
        if not early:
            break
        changed = False
        for practical in sorted(
            early,
            key=lambda placement: (
                int(placement.get("period") or 0),
                int(placement["job"].get("sinf_id") or 0),
                int(placement.get("day") or 0),
            ),
        ):
            class_id = int(practical["job"].get("sinf_id") or 0)
            day = int(practical.get("day") or 0)
            candidates = []
            for other in state.get("placements", []):
                if (
                    int(other["job"].get("sinf_id") or 0) != class_id
                    or int(other.get("day") or 0) != day
                    or int(other.get("period") or 0) < 3
                    or not _v196_movable_placement(other)
                ):
                    continue
                other_profile = _v196_rotation_profile(other["job"], context)
                if other_profile.get("physical") or other_profile.get("technology"):
                    continue
                candidates.append((
                    0 if other_profile.get("core_priority") else 1,
                    0 if int(other.get("period") or 0) >= 4 else 1,
                    -int(other.get("period") or 0),
                    other,
                ))
            for _, _, _, other in sorted(candidates, key=lambda row: row[:3]):
                removed = {id(practical), id(other)}
                trial = _v1852_rebuild_schedule_state(
                    [
                        placement for placement in state.get("placements", [])
                        if id(placement) not in removed
                    ],
                    context,
                )
                if not _v196_place_exact(
                    other["job"], day, practical["period"], trial, context, rng
                ):
                    continue
                if not _v196_place_exact(
                    practical["job"], day, other["period"], trial, context, rng
                ):
                    continue
                # J/T yoki texnologiyani keyinroqqa surish o'qituvchiga yangi
                # ulkan okno yaratmasligi shart. Pedagogik joylashuv faqat
                # ustozning umumiy ish kuni yomonlashmasa qabul qilinadi.
                if _v200_all_teacher_idle_signature(trial, context) > current_teacher_idle:
                    continue
                state = trial
                swaps += 1
                changed = True
                break
            if changed:
                break
        if not changed:
            break
    return state


def _v196_teacher_gap_metrics(state, context):
    """O'qituvchining smena ichidagi oynalarini kunlar kesimida sanaydi."""
    total = 0
    gap_shift_days = 0
    multi_gap_shift_days = 0
    max_gap = 0
    for periods in state.get("teacher_periods", {}).values():
        gap = int(_v1852_gap_count(set(periods)))
        total += gap
        max_gap = max(max_gap, gap)
        if gap > 0:
            gap_shift_days += 1
        if gap > 1:
            multi_gap_shift_days += 1
    unified = _v200_all_teacher_idle_signature(state, context)
    return {
        "oqituvchi_ichki_okno": int(total),
        "oqituvchi_oknoli_smena_kun": int(gap_shift_days),
        "oqituvchi_kop_oknoli_smena_kun": int(multi_gap_shift_days),
        "eng_katta_ichki_okno": int(max_gap),
        "oqituvchi_birlashgan_3soat_okno": int(unified[0]),
        "oqituvchi_birlashgan_2soat_okno": int(unified[1]),
        "oqituvchi_birlashgan_eng_katta_daqiqa": int(unified[2]),
        "oqituvchi_birlashgan_okno_daqiqa": int(unified[3]),
        "oqituvchi_birlashgan_okno_soni": int(unified[4]),
    }


def _v196_teacher_comfort_signature(state, context):
    """Kichik qiymat — pedagogik va o'qituvchi uchun yaxshiroq jadval.

    Sinf uzluksizligi hamda asosiy/amaliy fan vaqti birinchi o'rinda qoladi.
    Shundan keyin 3 soatdan uzun smena oralig'i, 2 soatdan uzun istisnolar va
    nihoyat smena ichidagi ko'p/har kungi oynalar kamaytiriladi.
    """
    metrics = _v196_attempt_metrics(state, context)
    excess_cross = max(
        0,
        int(metrics.get("oqituvchi_smenalar_orasi_daqiqa", 0))
        - 120 * int(metrics.get("ikki_smenali_2soatdan_uzoq", 0)),
    )
    return (
        int(_v196_class_gap_count(state)),
        int(metrics.get("oqituvchi_birlashgan_3soat_okno", 0)),
        int(metrics.get("oqituvchi_birlashgan_2soat_okno", 0)),
        int(metrics.get("oqituvchi_birlashgan_eng_katta_daqiqa", 0)),
        int(metrics.get("oqituvchi_birlashgan_okno_daqiqa", 0)),
        int(metrics.get("oqituvchi_birlashgan_okno_soni", 0)),
        int(metrics.get("ikki_smenali_uzoq_tanaffus", 0)),
        int(metrics.get("ikki_smenali_2soatdan_uzoq", 0)),
        int(metrics.get("eng_uzoq_smena_oraligi_daqiqa", 0)),
        int(excess_cross),
        int(metrics.get("oqituvchi_kop_oknoli_smena_kun", 0)),
        int(metrics.get("eng_katta_ichki_okno", 0)),
        int(metrics.get("oqituvchi_oknoli_smena_kun", 0)),
        int(metrics.get("oqituvchi_ichki_okno", 0)),
        int(metrics.get("amaliy_fan_1_2", 0)),
        int(metrics.get("jismoniydan_keyin_ogir_fan", 0)),
        int(metrics.get("asosiy_fan_5_6", 0)),
        int(metrics.get("ketma_ket_ogir_fan", 0)),
    )


def _v196_swap_same_class_day(state, first, second, context, rng):
    """Bir sinf-kundagi ikki dars o'rnini, ustozlarini saqlab almashtiradi."""
    removed = {id(first), id(second)}
    base = [
        placement for placement in state.get("placements", [])
        if id(placement) not in removed
    ]
    orders = ((second, first), (first, second))
    targets = {
        id(first): int(second.get("period") or 0),
        id(second): int(first.get("period") or 0),
    }
    for leading, trailing in orders:
        trial = _v1852_rebuild_schedule_state(base, context)
        if not _v196_place_exact(
            leading["job"], leading["day"], targets[id(leading)],
            trial, context, rng, expected_teachers=leading.get("teachers"),
        ):
            continue
        if not _v196_place_exact(
            trailing["job"], trailing["day"], targets[id(trailing)],
            trial, context, rng, expected_teachers=trailing.get("teachers"),
        ):
            continue
        if _v196_class_gap_count(trial) <= _v196_class_gap_count(state):
            return trial
    return None


def _v196_teacher_window_candidates(state, context, limit=96):
    """Eng yomon o'qituvchi-kunlardan xavfsiz swap nomzodlarini oladi.

    Avvalgi versiya faqat smena ichidagi okno yoki 120 daqiqadan katta
    smenalararo tanaffusni ko'rardi. Endi 1- va 2-smena bitta real vaqt
    chizig'i: odatiy tanaffusdan katta har qanday kutish optimizatsiyaga
    kiradi. Qaysi swap foydali ekani keyingi bosqichda to'liq jadvalni qayta
    hisoblash orqali aniqlanadi; shuning uchun bu yerda faqat yo'nalish
    bo'yicha taxmin qilib yaxshi variantni tasodifan chiqarib tashlamaymiz.
    """
    issues = []
    teacher_days = {
        (int(teacher), int(day))
        for (teacher, day), count in state.get("teacher_daily", {}).items()
        if float(count or 0) > 0
    }
    for teacher, day in teacher_days:
        first = set(state.get("teacher_periods", {}).get((teacher, day, 1), set()))
        second = set(state.get("teacher_periods", {}).get((teacher, day, 2), set()))
        internal = int(_v1852_gap_count(first) + _v1852_gap_count(second))
        unified = _v200_teacher_day_idle(state, teacher, day, context)
        if internal <= 0 and int(unified["okno_soni"]) <= 0:
            continue
        issues.append((
            int(unified["uch_soatdan_uzoq"]),
            int(unified["ikki_soatdan_uzoq"]),
            int(unified["eng_katta_daqiqa"]),
            int(unified["jami_daqiqa"]),
            int(unified["okno_soni"]),
            internal,
            teacher,
            day,
        ))

    placements = list(state.get("placements", []))
    pairs = []
    seen = set()
    for _, _, unified_max, _, _, internal, teacher, day in sorted(issues, reverse=True)[:12]:
        owned = [
            placement for placement in placements
            if int(placement.get("day") or 0) == int(day)
            and int(teacher) in {
                int(value) for value in placement.get("teachers") or []
                if value is not None
            }
            and _v196_movable_placement(placement)
        ]
        for first in owned:
            shift = int(first["job"].get("smena") or 1)
            current_periods = set(
                state.get("teacher_periods", {}).get(
                    (int(teacher), int(day), shift), set()
                )
            )
            before_internal = int(_v1852_gap_count(current_periods))
            class_id = int(first["job"].get("sinf_id") or 0)
            alternatives = [
                other for other in placements
                if int(other.get("day") or 0) == int(day)
                and int(other["job"].get("sinf_id") or 0) == class_id
                and int(other.get("period") or 0) != int(first.get("period") or 0)
                and _v196_movable_placement(other)
            ]
            for second in alternatives:
                moved_periods = (
                    current_periods - {int(first.get("period") or 0)}
                ) | {int(second.get("period") or 0)}
                improves_internal = (
                    int(_v1852_gap_count(moved_periods)) < before_internal
                )
                moves_toward_shift_edge = bool(
                    unified_max > 25 and (
                        (shift == 1 and int(second["period"]) > int(first["period"]))
                        or (shift == 2 and int(second["period"]) < int(first["period"]))
                    )
                )
                # Bir smenadagi darsni ichkariga siljitish ba'zan boshqa
                # smenadagi darsga yoki shu kunning boshqa darsiga aynan
                # tutashtiradi. Buni oddiy yo'nalish testi oldindan bilmaydi;
                # real unified signature sinab ko'rib, faqat yaxshilangan
                # holatni qabul qiladi.
                if not improves_internal and not moves_toward_shift_edge and internal <= 0:
                    continue
                key = tuple(sorted((id(first), id(second))))
                if key in seen:
                    continue
                seen.add(key)
                pairs.append((first, second))
                if len(pairs) >= int(limit):
                    return pairs
    return pairs


def _v196_optimize_teacher_windows(state, context, rng, max_swaps=36):
    """Sinf kataklarini saqlab, ichki va smenalararo kutishni qisqartiradi."""
    current_signature = _v196_teacher_comfort_signature(state, context)
    swaps = 0
    while swaps < int(max_swaps):
        best = None
        for first, second in _v196_teacher_window_candidates(
            state, context, limit=160
        ):
            trial = _v196_swap_same_class_day(
                state, first, second, context, rng
            )
            if trial is None:
                continue
            signature = _v196_teacher_comfort_signature(trial, context)
            if signature >= current_signature:
                continue
            if best is None or signature < best[0]:
                best = (signature, trial)
        if best is None:
            break
        current_signature, state = best
        swaps += 1
    state["v196_teacher_window_swaps"] = int(swaps)
    return state


def _v196_attempt_metrics(state, context):
    single_teacher_days = sum(
        1 for periods in state.get("teacher_periods", {}).values()
        if len(set(periods)) == 1
    )
    teacher_active_days = len({
        (int(teacher), int(day))
        for (teacher, day), count in state.get("teacher_daily", {}).items()
        if float(count or 0) > 0
    })
    heavy_pairs = 0
    pe_before_heavy = 0
    upper_first_heavy = 0
    late_core = 0
    early_practical = 0
    by_class_day = state.get("class_period_jobs", {})
    for (_, _), period_jobs in by_class_day.items():
        for period, job in period_jobs.items():
            profile = _v196_rotation_profile(job, context)
            grade = int(
                job.get("v1874_grade")
                or _v1874_grade(context.get("classes", {}).get(job.get("sinf_id"), {}))
            )
            if grade >= 9 and int(period) == 1 and profile.get("heavy"):
                upper_first_heavy += 1
            if int(period) >= 5 and profile.get("core_priority"):
                late_core += 1
            if int(period) <= 2 and (
                profile.get("physical") or profile.get("technology")
            ):
                early_practical += 1
            next_job = period_jobs.get(int(period) + 1)
            if not next_job:
                continue
            next_profile = _v196_rotation_profile(next_job, context)
            if profile.get("heavy") and next_profile.get("heavy"):
                heavy_pairs += 1
            if profile.get("physical") and next_profile.get("written_heavy"):
                pe_before_heavy += 1
    cross_shift_blocks = 0
    cross_shift_long_days = 0
    cross_shift_over_two_hours = 0
    cross_shift_total_minutes = 0
    cross_shift_max_minutes = 0
    teacher_days = {
        (int(teacher), int(day))
        for (teacher, day), count in state.get("teacher_daily", {}).items()
        if float(count or 0) > 0
    }
    compact_extra_days = 0
    compact_overflow_days = 0
    compact_adjacent_days = 0
    compact_unbalanced_days = 0
    demands = context.get("v196_teacher_demand") or {}
    for teacher, demand in demands.items():
        demand = float(demand or 0)
        if not (10 <= demand < 20):
            continue
        rules = context.get("rules", {}).get(
            int(teacher), context.get("default_rules", {})
        )
        target_days = _v196_teacher_target_days(demand, rules)
        active = sorted(
            day for uid, day in teacher_days if int(uid) == int(teacher)
        )
        fallback_days = _v201_teacher_fallback_days(demand, rules)
        compact_extra_days += max(0, len(active) - target_days)
        compact_overflow_days += max(0, len(active) - fallback_days)
        adjacent_pairs = sum(
            1 for left, right in zip(active, active[1:])
            if int(right) - int(left) == 1
        )
        allowed_adjacent = 0 if target_days <= 3 else 1
        compact_adjacent_days += max(0, adjacent_pairs - allowed_adjacent)
        daily_loads = [
            float(state.get("teacher_daily", {}).get((int(teacher), day), 0) or 0)
            for day in active
        ]
        if daily_loads:
            compact_unbalanced_days += max(
                0, int(math.ceil(max(daily_loads) - min(daily_loads) - 2))
            )
    for teacher, day in teacher_days:
        blocks = _v196_cross_shift_edge_blocks(state, teacher, day, context)
        minutes = _v196_cross_shift_gap_minutes(state, teacher, day, context)
        if blocks is None or minutes is None:
            continue
        cross_shift_blocks += int(blocks)
        cross_shift_total_minutes += int(minutes)
        cross_shift_max_minutes = max(cross_shift_max_minutes, int(minutes))
        if int(minutes) > 120:
            cross_shift_over_two_hours += 1
        if int(minutes) > 180:
            cross_shift_long_days += 1
    class_imbalance, class_short_days = _v196_class_distribution_metrics(state, context)
    teacher_gap_metrics = _v196_teacher_gap_metrics(state, context)
    return {
        "oqituvchi_bitta_darsli_kun": int(single_teacher_days),
        "oqituvchi_faol_kun": int(teacher_active_days),
        "ketma_ket_ogir_fan": int(heavy_pairs),
        "jismoniydan_keyin_ogir_fan": int(pe_before_heavy),
        "9_11_birinchi_dars_ogir": int(upper_first_heavy),
        "asosiy_fan_5_6": int(late_core),
        "amaliy_fan_1_2": int(early_practical),
        "oqituvchi_smenalar_orasi_blok": int(cross_shift_blocks),
        "oqituvchi_smenalar_orasi_daqiqa": int(cross_shift_total_minutes),
        "eng_uzoq_smena_oraligi_daqiqa": int(cross_shift_max_minutes),
        "ikki_smenali_2soatdan_uzoq": int(cross_shift_over_two_hours),
        "ikki_smenali_uzoq_tanaffus": int(cross_shift_long_days),
        "10_19_ortiqcha_kun": int(compact_extra_days),
        "10_19_limitdan_ortiq_kun": int(compact_overflow_days),
        "10_19_yonma_yon_kun": int(compact_adjacent_days),
        "10_19_notekis_kun": int(compact_unbalanced_days),
        "sinf_kun_taqsimoti_farqi": class_imbalance,
        "sinf_qisqa_kunlari": class_short_days,
        **teacher_gap_metrics,
    }


def _v1852_generate_attempt(jobs, context, seed):
    context["v196_teacher_demand"] = context.get("v196_teacher_demand") or _v196_teacher_demand(jobs)
    context["v196_teacher_shift_demand"] = (
        context.get("v196_teacher_shift_demand") or _v196_teacher_shift_demand(jobs)
    )
    context["v196_class_distribution"] = (
        context.get("v196_class_distribution") or _v196_class_distribution(jobs, context)
    )
    state, unplaced, penalty, gaps, late = _v196_base_generate_attempt(
        jobs, context, seed
    )
    # Asosiy pedagogik urinish darslarni turli kunlarga yoyadi. Faqat u
    # barcha darsni joylay olmasa, 1 kunlik va keyin 2 kunlik nazoratli
    # takror fallback sinovdan o‘tadi. Eng kam joylashmagan darsli natija olinadi.
    best_attempt = (state, unplaced, penalty, gaps, late, 0)
    if unplaced:
        for repeat_days in (1, 2):
            relaxed_context = dict(context)
            relaxed_context["v203_emergency_repeat_days"] = repeat_days
            candidate = _v196_base_generate_attempt(
                jobs, relaxed_context, int(seed) + repeat_days * 100003
            )
            candidate_with_mode = (*candidate, repeat_days)
            if (len(candidate[1]), float(candidate[2])) < (
                len(best_attempt[1]), float(best_attempt[2])
            ):
                best_attempt = candidate_with_mode
            if not candidate[1]:
                break
    state, unplaced, penalty, gaps, late, selected_repeat_days = best_attempt
    if selected_repeat_days:
        context["v203_emergency_repeat_days"] = selected_repeat_days
        state.setdefault("ogohlantirishlar", []).append(
            f"Jadvalni to‘liq sig‘dirish uchun ayrim fanlar haftasiga "
            f"{selected_repeat_days} kungacha bir kunda 2 marta joylashtirildi"
        )
    # Greedy joylashtirish tugagach jadvalni o'quvchi nuqtai nazaridan
    # majburiy sayqallaymiz: avval oknolar yopiladi, keyin 2/6 kabi notekis
    # kunlar tenglashtiriladi, oxirida J/T va texnologiya ertalabki katakdan
    # keyinroqqa xavfsiz almashtiriladi. Har qadam qattiq to'qnashuv
    # tekshiruvlaridan qayta o'tadi.
    repair_rng = _v1852_random.Random(int(seed) ^ 0x19_08_26)
    state = _v196_compact_class_gaps(state, context, repair_rng)
    state = _v196_balance_class_days(state, context, repair_rng)
    state = _v196_compact_class_gaps(state, context, repair_rng)
    state = _v196_relocate_early_practical(state, context, repair_rng)
    state = _v196_compact_class_gaps(state, context, repair_rng)
    state["class_gap_count"] = _v196_class_gap_count(state)
    gaps = sum(
        _v1852_gap_count(set(periods))
        for periods in state.get("teacher_periods", {}).values()
    )
    late = sum(
        1 for placement in state.get("placements", [])
        if int(placement.get("period") or 0)
        > int(placement["job"].get("preferred_last") or 6)
        and int(placement["job"].get("weight") or 1) >= 2
    )
    metrics = _v196_attempt_metrics(state, context)
    state["v196_metrics"] = metrics
    penalty += (
        metrics["oqituvchi_bitta_darsli_kun"] * 3
        + metrics["ketma_ket_ogir_fan"] * 9
        + metrics["jismoniydan_keyin_ogir_fan"] * 60
        + metrics["9_11_birinchi_dars_ogir"] * 12
        + metrics["asosiy_fan_5_6"] * 180
        + metrics["amaliy_fan_1_2"] * 180
        + metrics["oqituvchi_smenalar_orasi_blok"] * 55
        + metrics["oqituvchi_smenalar_orasi_daqiqa"] * 0.35
        + metrics["ikki_smenali_2soatdan_uzoq"] * 260
        + metrics["ikki_smenali_uzoq_tanaffus"] * 1200
        + metrics["10_19_limitdan_ortiq_kun"] * 18000
        + metrics["10_19_ortiqcha_kun"] * 4200
        + metrics["10_19_yonma_yon_kun"] * 620
        + metrics["10_19_notekis_kun"] * 420
        + metrics["oqituvchi_ichki_okno"] * 650
        + metrics["oqituvchi_oknoli_smena_kun"] * 280
        + metrics["oqituvchi_kop_oknoli_smena_kun"] * 1400
        + metrics["eng_katta_ichki_okno"] * 900
        + metrics["oqituvchi_birlashgan_okno_soni"] * 1200
        + metrics["oqituvchi_birlashgan_okno_daqiqa"] * 12
        + metrics["oqituvchi_birlashgan_2soat_okno"] * 5000
        + metrics["oqituvchi_birlashgan_3soat_okno"] * 15000
        + metrics["sinf_kun_taqsimoti_farqi"] * 45
        + metrics["sinf_qisqa_kunlari"] * 120
    )
    return state, unplaced, penalty, gaps, late


# ========================= V19.6 END =========================

# Preserve Python monolith semantics: late definitions must be visible to
# earlier platform routes such as the employee import endpoint.
for _v19_name, _v19_value in list(globals().items()):
    if _v19_name not in _V19_IMPORTED_NAMES and not _v19_name.startswith("__"):
        setattr(_platform, _v19_name, _v19_value)

__all__ = [name for name in globals() if not name.startswith("__")]

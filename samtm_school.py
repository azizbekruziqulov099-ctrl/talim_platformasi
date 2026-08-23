"""School OS and smart timetable routes extracted from the legacy monolith.

The public URLs and business logic are preserved.  Definitions are patched back
into samtm_platform so older route functions that resolve late-bound helpers keep
the same behaviour they had in one file.
"""
try:
    from . import samtm_platform as _platform
    from .samtm_platform import *
except ImportError:  # Railway working directory may be backend/
    import samtm_platform as _platform
    from samtm_platform import *

_V19_IMPORTED_NAMES = set(globals())

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
                              s.id AS sinf_id,s.sinf,s.harf,e.guruh_kaliti,e.smena
                       FROM aqlli_jadval_slotlari_v2 e
                       JOIN maktab_sinflari s ON s.id=e.sinf_id
                       LEFT JOIN aqlli_xonalar_v2 r ON r.id=e.xona_id
                       WHERE e.urinish_id=%s AND e.hafta_kuni=%s AND e.oqituvchi_user_id=%s
                       ORDER BY e.smena,e.dars_raqami,s.sinf::int,s.harf,e.guruh_kaliti""",
                    (smart_run["id"], kun, teacher_id))
        darslar = cur.fetchall()
        cur.execute("SELECT COUNT(*) AS hafta_darsi FROM aqlli_jadval_slotlari_v2 WHERE urinish_id=%s AND oqituvchi_user_id=%s",
                    (smart_run["id"], teacher_id))
        hafta_darsi = int((cur.fetchone() or {}).get("hafta_darsi") or 0)
    else:
        cur.execute("""
            SELECT DISTINCT j.id,j.dars_raqami,j.fan,j.xona,j.boshlanish_vaqti,j.tugash_vaqti,
                   s.id AS sinf_id,s.sinf,s.harf,j.guruh_kaliti
            FROM dars_jadvali j
            JOIN maktab_sinflari s ON s.id=j.sinf_id
            LEFT JOIN maktab_dars_birikmalari b
              ON b.sinf_id=j.sinf_id AND LOWER(TRIM(b.fan_nomi))=LOWER(TRIM(j.fan)) AND b.user_id=%s
            WHERE j.kun=%s AND (j.oqituvchi_user_id=%s OR (j.oqituvchi_user_id IS NULL AND b.user_id=%s))
            ORDER BY j.dars_raqami,s.sinf::int,s.harf
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
        "sana": hozir.date().isoformat(), "kun": kun, "oqituvchi": teacher["full_name"],
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
                SELECT DISTINCT s.id AS sinf_id,s.sinf,s.harf,b.fan_nomi
                FROM maktab_dars_birikmalari b
                JOIN maktab_sinflari s ON s.id=b.sinf_id
                WHERE b.user_id=%s AND b.maktab_id=%s
                ORDER BY s.sinf::int,s.harf,b.fan_nomi
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
    turi: str = "oddiy"
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
        cur.execute("""INSERT INTO aqlli_xonalar_v2(maktab_id,nomi,turi,sigim,faol)
                       VALUES(%s,%s,%s,%s,TRUE)
                       ON CONFLICT(maktab_id,nomi) DO UPDATE SET turi=EXCLUDED.turi,
                         sigim=EXCLUDED.sigim,faol=TRUE RETURNING id""",
                    (sorov.maktab_id, name, sorov.turi or "oddiy", sorov.sigim))
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
    haftalik_soat: int
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
            if int(cur.rowcount or 0) == 0 and int(item.haftalik_soat or 0) > 0:
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
    cur.execute("""SELECT user_id,full_name,lavozim,fanlari,oqitadigan_sinflari,haftalik_dars_soati
                   FROM users
                   WHERE maktab_id=%s AND lavozim IS NOT NULL
                   ORDER BY full_name,user_id""", (maktab_id,))
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
        row["dars_beruvchi"] = bool(subjects or classes or assignment_counts[uid] or row.get("haftalik_dars_soati"))
        row["fan_holati"] = "aniqlandi" if subjects else "fan_topilmadi"
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
    class_hour_counts = _v1852_Counter(
        int(row["rahbar_user_id"]) for row in class_hours if row.get("rahbar_user_id") is not None
    )
    teachers = _v1859_effective_teachers(cur, maktab_id)
    for teacher in teachers:
        extra = int(class_hour_counts.get(int(teacher["user_id"]), 0))
        teacher["sinf_soati_soni"] = extra
        base = teacher.get("haftalik_dars_soati")
        teacher["haftalik_reja_jami"] = (int(base) + extra) if base is not None else (extra or None)
    cur.execute("SELECT fan_nomi FROM maktab_fanlari WHERE maktab_id=%s ORDER BY fan_nomi", (maktab_id,))
    subjects = [r["fan_nomi"] for r in cur.fetchall()]
    cur.execute("SELECT * FROM aqlli_xonalar_v2 WHERE maktab_id=%s AND faol=TRUE ORDER BY nomi", (maktab_id,))
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
        payload = _v1852_setup_payload(cur, maktab_id)
        manager = _v1852_manager(cur, user_id, maktab_id)
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
            (method_hard if row.get("qattiq") else method_soft).add((key[0], key[1]))
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
    year = _v1852_active_year(cur, maktab_id)
    if not year:
        raise HTTPException(status_code=400, detail="Avval o'quv yili va choraklarni saqlang")
    cur.execute("SELECT COUNT(*) AS son FROM aqlli_choraklar_v2 WHERE oquv_yili_id=%s", (year["id"],))
    if int(cur.fetchone()["son"] or 0) != 4:
        raise HTTPException(status_code=400, detail="Barcha 4 chorakni kiriting")
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
    cur.execute("SELECT user_id,full_name,haftalik_dars_soati FROM users WHERE maktab_id=%s AND lavozim IS NOT NULL", (maktab_id,))
    teachers = {int(row["user_id"]): row for row in cur.fetchall()}
    cur.execute("SELECT * FROM aqlli_xonalar_v2 WHERE maktab_id=%s AND faol=TRUE", (maktab_id,))
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
        for occurrence in range(1, int(load["haftalik_soat"] or 0) + 1):
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
                "difficulty": (100 if fixed_groups else 0) + (50 if load.get("xona_id") else 0) + int(load["haftalik_soat"] or 0),
            })
    return jobs, warnings


def _v1852_candidate_reasons(job, day, period, selected_teachers, room_keys, state, context):
    reasons = []
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
        periods = set(state["teacher_periods"].get((teacher, day, job["smena"]), set())) | {period}
        if _v1852_max_streak(periods) > rules["ketma_ket_max"]:
            reasons.append("o'qituvchining ketma-ket dars limiti")
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
    if job["groups"]:
        return [f"room:{g['xona_id']}" if g.get("xona_id") else None for g in job["groups"]]
    if job.get("room_id"):
        return [f"room:{job['room_id']}"]
    class_row = classes[job["sinf_id"]]
    room_text = "|".join(str(class_row.get(x) or "").strip() for x in ("bino", "xona")).strip("|")
    return [f"classroom:{room_text.casefold()}" if room_text else None]


def _v1852_candidate_score(job, day, period, teachers, state, context, rng):
    score = 0.0
    for teacher in teachers:
        if teacher is None:
            score += 1000
            continue
        rules = context["rules"].get(teacher, context["default_rules"])
        if (teacher, day) in context["method_soft"]:
            score += 35
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


def _v1852_generate_attempt(jobs, context, seed):
    rng = _v1852_random.Random(seed)
    state = {
        "class_busy": set(), "teacher_busy": set(), "room_busy": set(),
        "subject_daily": _v1852_defaultdict(int), "class_subject_periods": _v1852_defaultdict(set),
        "teacher_week": _v1852_defaultdict(int), "teacher_daily": _v1852_defaultdict(int),
        "teacher_periods": _v1852_defaultdict(set), "placements": [],
    }
    # Murakkab, guruhli, xonali va ko'p soatli ishlar oldin joylashtiriladi.
    ordered = sorted(jobs, key=lambda j: (-j["difficulty"], rng.random()))
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
    gap_count = sum(_v1852_gap_count(periods) for periods in state["teacher_periods"].values())
    late_heavy = sum(1 for p in state["placements"] if p["period"] > p["job"]["preferred_last"] and p["job"]["weight"] >= 2)
    return state, unplaced, total_penalty, gap_count, late_heavy


class V1852Generate(BaseModel):
    maktab_id: int
    urinishlar_soni: int = 8


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
            base = int(row["haftalik_dars_soati"]) if row.get("haftalik_dars_soati") is not None else None
            extra = int(class_hour_counts.get(int(tid), 0))
            caps[tid] = (base + extra) if base is not None else None
        context = {
            "weekdays": int(year["hafta_kunlari"]), "shifts": shifts, "classes": classes,
            "rules": rules, "default_rules": {"kunlik_max": 6, "ketma_ket_max": 4, "okno_max": 1, "afzal_smena": 0, "eng_erta_dars": 1, "eng_kech_dars": 12},
            "hard": hard, "soft": soft, "method_hard": method_hard, "method_soft": method_soft,
            "teacher_caps": caps, "class_day_blocks": class_day_blocks,
        }
        attempts = max(24, min(80, int(sorov.urinishlar_soni or 24)))
        best = None
        base_seed = int(datetime.now().timestamp())
        for index in range(attempts):
            result = _v1852_generate_attempt(jobs, context, base_seed + index * 7919)
            state, unplaced, penalty, gaps, late = result
            rank = (len(unplaced), gaps, late, round(penalty, 2))
            if best is None or rank < best[0]:
                best = (rank, result)
        _, (state, unplaced, penalty, gap_count, late_heavy) = best
        placed_count = len(state["placements"])
        total_count = len(jobs)
        placement_ratio = (placed_count / total_count) if total_count else 1.0
        quality = max(0, min(100, round(placement_ratio * 88 + max(0, 12 - gap_count * 0.25 - late_heavy * 0.2))))
        unplaced_payload = []
        for item in unplaced:
            job = item["job"]
            cls = classes.get(job["sinf_id"], {})
            top_reasons = item.get("sabablar") or {"mos bo'sh vaqt topilmadi": 1}
            unplaced_payload.append({
                "sinf_id": job["sinf_id"], "sinf": f"{cls.get('sinf','')}-{cls.get('harf','')}",
                "fan": job["fan"], "takror_raqami": job["occurrence"],
                "sabab": max(top_reasons, key=top_reasons.get), "sabablar": top_reasons,
            })
        teacher_summary = []
        for tid, teacher in teachers.items():
            actual = int(state["teacher_week"].get(tid, 0))
            base = int(teacher["haftalik_dars_soati"]) if teacher.get("haftalik_dars_soati") is not None else None
            extra = int(class_hour_counts.get(int(tid), 0))
            cap = caps.get(tid)
            teacher_summary.append({
                "user_id": tid, "full_name": teacher["full_name"], "jadval_soati": actual,
                "asosiy_yuklama": base, "sinf_soati_soni": extra, "yuklama": cap,
                "farq": None if cap is None else cap - actual,
            })
        warnings = list(initial_warnings)
        for rule in class_day_rule_rows[:50]:
            warnings.append(f"Qattiq qoida: {rule.get('yorliq')}")
        for job in jobs:
            if job["groups"] and any(g.get("xona_id") is None for g in job["groups"]):
                cls = classes[job["sinf_id"]]
                message = f"{cls['sinf']}-{cls['harf']} {job['fan']}: parallel guruh xonalaridan biri ko'rsatilmagan"
                if message not in warnings:
                    warnings.append(message)
        diagnostics = {
            "muammolar": unplaced_payload[:100], "ogohlantirishlar": warnings[:100],
            "oqituvchi_yuklamasi": teacher_summary, "oknolar": gap_count,
            "kech_tushgan_ogir_darslar": late_heavy, "yumshoq_jazo": round(penalty, 2),
            "urinishlar_soni": attempts,
            "manba_mosligi": preflight,
            "tasdiqlash_mumkin": False,
        }
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
            if job["groups"]:
                for group, teacher in zip(job["groups"], selected_teachers):
                    room_id = group.get("xona_id")
                    room_text = rooms.get(room_id, {}).get("nomi") if room_id else None
                    entry_rows.append((run_id, sorov.maktab_id, job["sinf_id"], day, job["smena"], period,
                                       job["fan"], teacher, group["guruh_kaliti"], room_id, room_text,
                                       time_slot["boshlanish"], time_slot["tugash"], job["load_id"], job["occurrence"]))
            else:
                teacher = selected_teachers[0] if selected_teachers else None
                room_id = job.get("room_id")
                class_row = classes[job["sinf_id"]]
                room_text = rooms.get(room_id, {}).get("nomi") if room_id else " ".join(x for x in [class_row.get("bino"), class_row.get("xona")] if x) or None
                entry_rows.append((run_id, sorov.maktab_id, job["sinf_id"], day, job["smena"], period,
                                   job["fan"], teacher, "whole", room_id, room_text,
                                   time_slot["boshlanish"], time_slot["tugash"], job["load_id"], job["occurrence"]))
        if entry_rows:
            psycopg2.extras.execute_values(cur, """INSERT INTO aqlli_jadval_slotlari_v2(
                urinish_id,maktab_id,sinf_id,hafta_kuni,smena,dars_raqami,fan_nomi,
                oqituvchi_user_id,guruh_kaliti,xona_id,xona_matni,boshlanish_vaqti,
                tugash_vaqti,yuklama_id,takror_raqami) VALUES %s""", entry_rows, page_size=1000)

        jadval_mosligi = _v1875_schedule_integrity_report(
            cur, sorov.maktab_id, run_id
        )
        tasdiqlash_mumkin = bool(
            int(len(unplaced)) == 0 and jadval_mosligi.get("tayyor")
        )
        diagnostics["jadval_mosligi"] = jadval_mosligi
        diagnostics["tasdiqlash_mumkin"] = tasdiqlash_mumkin
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
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


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
        return {"urinish": run, "slotlar": entries}
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
        return {"urinish": run, "slotlar": cur.fetchall()}
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
    cur.execute("""SELECT MIN(id) AS id,hafta_kuni,smena,dars_raqami,
                          MIN(oqituvchi_user_id) AS oqituvchi_user_id
                   FROM aqlli_jadval_slotlari_v2
                   WHERE urinish_id=%s AND sinf_id=%s AND LOWER(fan_nomi)=LOWER(%s)
                   GROUP BY hafta_kuni,smena,dars_raqami ORDER BY hafta_kuni,smena,dars_raqami""",
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
                current["psixolog_sinf_soni"] = 0
                current["sinf_soati_soni"] = 0
                grouped[key] = current
            current["birlashtirilgan_idlar"].append(uid)
            current["jadvaldagi_soat"] += int(counts.get(uid, 0))
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
            plan = (int(base_plan) + extra) if base_plan is not None else (extra or None)
            row["haftalik_reja_jami"] = plan
            actual = int(row.get("jadvaldagi_soat") or 0)
            row["farq"] = None if plan is None else int(plan)-actual
            row["holat"] = (
                "kiritilmagan" if plan is None else
                "ortiqcha" if actual>int(plan) else
                "toliq" if actual==int(plan) else "yetishmaydi"
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


def _v1866_class_hour_rule_rows(cur, maktab_id: int):
    cur.execute("""SELECT q.*,s.sinf,s.harf,COALESCE(s.smena,1) AS smena,
                          s.rahbar_user_id,COALESCE(u.full_name,'') AS rahbar_ismi
                   FROM aqlli_sinf_soati_qoidalari_v2 q
                   JOIN maktab_sinflari s ON s.id=q.sinf_id
                   LEFT JOIN users u ON u.user_id=s.rahbar_user_id
                   WHERE q.maktab_id=%s AND q.faol=TRUE
                   ORDER BY s.sinf::int,s.harf""", (maktab_id,))
    return cur.fetchall()


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
                            maktab_id,sinf_id,hafta_kuni,dars_raqami,faol,yaratgan_user_id,yangilangan_at)
                           VALUES(%s,%s,%s,%s,TRUE,%s,NOW())
                           ON CONFLICT(maktab_id,sinf_id) DO UPDATE SET
                             hafta_kuni=EXCLUDED.hafta_kuni,dars_raqami=EXCLUDED.dars_raqami,
                             faol=TRUE,yaratgan_user_id=EXCLUDED.yaratgan_user_id,yangilangan_at=NOW()""",
                        (sorov.maktab_id, cls["id"], sorov.hafta_kuni, sorov.dars_raqami, actor_id))
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
        jobs.append({
            "job_id": f"sinf-soati:{class_id}", "load_id": None,
            "sinf_id": class_id, "fan": "SINF SOATI", "occurrence": 1,
            "smena": int(cls.get("smena") or 1), "daily_max": 1,
            "consecutive_allowed": True, "preferred_last": int(row["dars_raqami"]),
            "weight": 1, "room_id": None, "groups": [],
            "teacher_options": [int(leader)] if leader is not None else [],
            "difficulty": 100000, "fixed_day": int(row["hafta_kuni"]),
            "fixed_period": int(row["dars_raqami"]), "is_class_hour": True,
        })
    return jobs, warnings


def _v1866_class_hour_violations(cur, maktab_id: int, run_id: int):
    rules = _v1866_class_hour_rule_rows(cur, maktab_id)
    errors = []
    for row in rules:
        if row.get("rahbar_user_id") is None:
            errors.append({"sinf_id": row["sinf_id"], "izoh": f"{row['sinf']}-{row['harf']}: sinf rahbari yo‘q"})
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


def _v1873_subject_day(subject):
    key = _v1873_norm(subject)
    if not key:
        return None

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
            day = _v1873_subject_day(subject)
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

    return {
        "key": key,
        "academic": not is_class_hour,
        "class_hour": is_class_hour,
        "physical": is_physical,
        "light": light,
        "primary_light": primary_light,
        "primary_core": primary_core,
        "heavy": heavy,
        "written_heavy": written_heavy,
        "difficulty": int(difficulty),
    }


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
    class_hours = _v1852_Counter()
    for job in jobs:
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
    return jobs, warnings


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

    # Sinf jadvalida ichki "okno" qolmasin.
    existing_periods = set(period_jobs.get((job["sinf_id"], day), {}).keys())
    score += max(
        0,
        _v1852_gap_count(existing_periods | {period}) - _v1852_gap_count(existing_periods),
    ) * 12

    if 1 <= grade <= 4:
        if profile["primary_core"]:
            score += {1: 7, 2: -10, 3: -10, 4: 9, 5: 80}.get(period, 100)
        elif profile["physical"]:
            score += {1: 22, 2: 15, 3: 7, 4: -5, 5: -12}.get(period, 20)
        elif profile["light"]:
            score += {1: 14, 2: 9, 3: 2, 4: -5, 5: -8}.get(period, 15)
        else:
            score += {1: 5, 2: -5, 3: -5, 4: 3, 5: 18}.get(period, 20)
    else:
        if profile["physical"]:
            score += max(0, max_period - period) * 5 - (10 if period == max_period else 0)
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
            score += 80

    return score


def _v1852_place_job(job, day, period, teachers, room_keys, state, context):
    _v1874_base_place_job(job, day, period, teachers, room_keys, state, context)
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
        """SELECT DISTINCT e.sinf_id,s.sinf,s.harf,e.hafta_kuni,e.dars_raqami,e.fan_nomi
           FROM aqlli_jadval_slotlari_v2 e
           JOIN maktab_sinflari s ON s.id=e.sinf_id
           WHERE e.maktab_id=%s AND e.urinish_id=%s
           ORDER BY s.sinf::int,s.harf,e.hafta_kuni,e.dars_raqami,e.fan_nomi""",
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
        cap = int(row["haftalik_dars_soati"]) + int(row.get("sinf_soati") or 0)
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
            hours = int(row.get("haftalik_soat") or 0)
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

        class_hours[pair["sinf_id"]] += int(pair.get("haftalik_soat") or 0)
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
                    (int(hours), maktab_id, int(teacher_id)))

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

    year = _v1852_active_year(cur, maktab_id)
    if not year:
        errors.append("O'quv yili saqlanmagan")
        return {"tayyor": False, "xatolar": errors, "ogohlantirishlar": warnings,
                "sinflar": [], "oqituvchilar": [], "fanlar": [], "manba_hash": None}
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
        if int(load.get("haftalik_soat") or 0) != int(pair.get("haftalik_soat") or 0):
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
    class_hour_by_teacher = _v1852_Counter(
        int(row["rahbar_user_id"]) for row in class_hour_rules if row.get("rahbar_user_id") is not None
    )

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
        fan_hours = int(model["class_hours"].get(class_id, 0))
        class_hour = 1 if class_id in class_hour_by_class else 0
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
                errors.append(f"{cls['sinf']}-{cls['harf']}: sinf soati bor, lekin sinf rahbari belgilanmagan")
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
        if int(pair.get("haftalik_soat") or 0) > allowed_days * daily_max:
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
        base_plan = int(model["teacher_hours"].get(int(teacher_id), 0))
        class_hours = int(class_hour_by_teacher.get(int(teacher_id), 0))
        total_plan = base_plan + class_hours
        saved_base = row.get("haftalik_dars_soati")
        if saved_base is None or int(saved_base) != base_plan:
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
            "mos": total_plan <= capacity and saved_base is not None and int(saved_base) == base_plan,
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
        key: int(pair["haftalik_soat"])
        for key, pair in model["pairs"].items()
    }
    scheduled_subject_sessions = _v1852_defaultdict(set)
    class_sessions = _v1852_defaultdict(set)
    teacher_sessions = _v1852_defaultdict(set)
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
        subject = str(slot.get("fan_nomi") or "").strip()
        subject_key = _v1875_subject_key(subject)
        session = (day, shift, period)
        class_sessions[class_id].add(session)
        if subject_key != _v1875_subject_key("SINF SOATI"):
            pair_key = (class_id, subject_key)
            scheduled_subject_sessions[pair_key].add(session)
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
            teacher_sessions[teacher_id].add((class_id, day, shift, period))
            teacher_slot_map[(teacher_id, day, shift, period)].add(class_id)
            if (teacher_id, day) in method_hard:
                errors.append(f"{slot.get('oqituvchi_ismi')}: {_V1852_HAFTA.get(day, day)} metod kuniga dars qo'yilgan")
            if _v1852_blocked(hard, teacher_id, day, shift, period):
                errors.append(f"{slot.get('oqituvchi_ismi')}: {_V1852_HAFTA.get(day, day)} {shift}-smena {period}-dars qattiq bloklangan")
        room_key = slot.get("xona_id") or slot.get("xona_matni")
        if room_key:
            room_slot_map[(str(room_key), day, shift, period)].add(class_id)
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
        planned = int(planned_subject.get(key, 0))
        actual = len(scheduled_subject_sessions.get(key, set()))
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
        for occurrence in range(1, int(pair["haftalik_soat"]) + 1):
            rows = pair_occurrence_rows.get((key, occurrence), [])
            actual_groups = {_v1875_group_key(row.get("guruh_kaliti")) for row in rows}
            sessions = {(int(row["hafta_kuni"]), int(row["smena"]), int(row["dars_raqami"])) for row in rows}
            if actual_groups != expected_groups or len(sessions) != 1:
                errors.append(
                    f"{pair['sinf']} / {pair['fan_nomi']} / {occurrence}-takror: parallel guruhlar to'liq va bir vaqtda emas"
                )

    class_hour_rules = _v1866_class_hour_rule_rows(cur, maktab_id)
    class_hour_by_teacher = _v1852_Counter(
        int(row["rahbar_user_id"]) for row in class_hour_rules if row.get("rahbar_user_id") is not None
    )
    class_hour_by_class = {int(row["sinf_id"]): row for row in class_hour_rules}
    class_summary = []
    all_class_ids = set(classes) | set(model["class_hours"]) | set(class_sessions)
    for class_id in sorted(all_class_ids):
        cls = classes.get(class_id, {})
        planned = int(model["class_hours"].get(class_id, 0)) + (1 if class_id in class_hour_by_class else 0)
        actual = len(class_sessions.get(class_id, set()))
        label = f"{cls.get('sinf','')}-{cls.get('harf','')}"
        if planned != actual:
            errors.append(f"{label}: sinf haftalik reja {planned} soat, jadval {actual} soat")
        class_summary.append({"sinf_id": class_id, "sinf": label, "reja": planned,
                              "jadval": actual, "farq": actual - planned, "mos": planned == actual})

    cur.execute("SELECT user_id,full_name,haftalik_dars_soati FROM users WHERE maktab_id=%s", (maktab_id,))
    teacher_rows = {int(row["user_id"]): dict(row) for row in cur.fetchall()}
    teacher_summary = []
    all_teacher_ids = set(model["teacher_hours"]) | set(class_hour_by_teacher) | set(teacher_sessions)
    for teacher_id in sorted(all_teacher_ids):
        row = teacher_rows.get(teacher_id, {"full_name": str(teacher_id)})
        planned = int(model["teacher_hours"].get(teacher_id, 0)) + int(class_hour_by_teacher.get(teacher_id, 0))
        actual = len(teacher_sessions.get(teacher_id, set()))
        if planned != actual:
            errors.append(f"{row.get('full_name')}: haftalik reja {planned} soat, jadval {actual} soat")
        teacher_summary.append({"user_id": teacher_id, "full_name": row.get("full_name"),
                                "reja": planned, "jadval": actual,
                                "farq": actual - planned, "mos": planned == actual})

    for (teacher_id, day, shift, period), class_ids in teacher_slot_map.items():
        if len(class_ids) > 1:
            errors.append(
                f"{teacher_rows.get(teacher_id, {}).get('full_name', teacher_id)}: "
                f"{_V1852_HAFTA.get(day, day)} {shift}-smena {period}-darsda {len(class_ids)} ta sinf"
            )
    for (room, day, shift, period), class_ids in room_slot_map.items():
        if len(class_ids) > 1:
            errors.append(f"Xona {room}: {_V1852_HAFTA.get(day, day)} {shift}-smena {period}-darsda ikki sinf")

    daily_teacher_counts = _v1852_Counter()
    daily_subject_sessions = _v1852_defaultdict(set)
    for slot in slots:
        teacher_id = slot.get("oqituvchi_user_id")
        if teacher_id is not None:
            daily_teacher_counts[(int(teacher_id), int(slot["hafta_kuni"]))] += 1
        subject_key = _v1875_subject_key(slot.get("fan_nomi"))
        if subject_key != _v1875_subject_key("SINF SOATI"):
            daily_subject_sessions[(
                int(slot["sinf_id"]), subject_key, int(slot["hafta_kuni"])
            )].add((int(slot["smena"]), int(slot["dars_raqami"])))
    for (teacher_id, day), count in daily_teacher_counts.items():
        limit = int(teacher_rules.get(teacher_id, {"kunlik_max": 6})["kunlik_max"])
        if count > limit:
            errors.append(f"{teacher_rows.get(teacher_id, {}).get('full_name', teacher_id)}: {_V1852_HAFTA.get(day, day)} {count} dars, kunlik max {limit}")
    for (class_id, subject_key, day), sessions in daily_subject_sessions.items():
        count = len(sessions)
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
        return [
            {"guruh_kaliti": "group_1", "guruh_nomi": "1-guruh", "oquvchi_soni": 0},
            {"guruh_kaliti": "group_2", "guruh_nomi": "2-guruh", "oquvchi_soni": 0},
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
                          s.sinf,s.harf,COALESCE(s.smena,1) AS smena
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
                "soat": int(row.get("haftalik_soat") or 0),
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
            int(row.get("haftalik_soat") or 0)
            for row in rows if int(row.get("haftalik_soat") or 0) > 0
        })
        nonempty_daily = sorted({
            int(row.get("kunlik_max") or 1)
            for row in rows if row.get("kunlik_max") not in (None, "")
        })
        fallback_load = load_map.get(key) or {}
        if not positive_hours and int(fallback_load.get("haftalik_soat") or 0) > 0:
            positive_hours = [int(fallback_load["haftalik_soat"])]
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
        if rows and any(int(row.get("haftalik_soat") or 0) <= 0 for row in rows) and weekly_hours:
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
                    group_payload.append({
                        **group,
                        "oqituvchi_user_id": int(teacher_id) if teacher_id is not None else None,
                        "oqituvchi_ismi": teacher_name,
                        "xona_id": setting.get("xona_id"),
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
        sinf_reja_soati = int(weekly_hours or 0)
        jadval_parallel_slot_soni = int(weekly_hours or 0)
        oqituvchi_soat_jami = int(weekly_hours or 0) * int(parallel_guruh_soni)

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
            "har_bir_guruh_oqituvchi_soati": int(weekly_hours or 0),
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
                int(row.get("haftalik_soat") or 0)
                for row in rows if int(row.get("haftalik_soat") or 0) > 0
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
                        and int(row.get("haftalik_soat") or 0) > 0
                    ),
                    None,
                )
                if matching_load:
                    hours_set = {int(matching_load["haftalik_soat"])}
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
                if row_ids:
                    cur.execute(
                        "DELETE FROM maktab_dars_birikmalari WHERE id=ANY(%s)",
                        (row_ids,),
                    )
                _v1876_delete_group_settings(
                    cur, sorov.maktab_id, class_id, subject_key
                )
                for group_key in expected_groups:
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
                    room_id = (
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
        "ALTER TABLE maktab_dars_birikmalari "
        "ADD COLUMN IF NOT EXISTS xona_id BIGINT REFERENCES aqlli_xonalar_v2(id) ON DELETE SET NULL"
    )
    cur.execute(
        "ALTER TABLE maktab_dars_birikmalari "
        "ADD COLUMN IF NOT EXISTS yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
    )
    cur.execute("""CREATE TABLE IF NOT EXISTS aqlli_jadval_boshqaruv_v19_2(
        maktab_id INTEGER PRIMARY KEY REFERENCES maktablar(id) ON DELETE CASCADE,
        avtomatik_tavsiya BOOLEAN NOT NULL DEFAULT TRUE,
        yangilagan_user_id BIGINT,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )""")
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
    except Exception as exc:
        print(f"[V19.2 o'qituvchi yuklamasi] {exc}", flush=True)


def _v192_clean_subject(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _v192_group_variants(cur, maktab_id: int):
    systems = _v1876_group_system_catalog(cur, maktab_id)
    cur.execute("""SELECT id,sinf,harf,COALESCE(smena,1) AS smena
                   FROM maktab_sinflari WHERE maktab_id=%s
                   ORDER BY sinf::int,harf""", (maktab_id,))
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
        hours = max(0, int(row.get("haftalik_soat") or 0))
        teacher_id = int(row["user_id"])
        teacher_base[teacher_id] = teacher_base.get(teacher_id, 0) + hours
        pair = (int(row["sinf_id"]), _v1875_subject_key(row["fan_nomi"]))
        data = class_subject.setdefault(pair, {"whole": [], "groups": [], "fan_nomi": row["fan_nomi"]})
        if _v1875_group_key(row.get("guruh_kaliti")) == "whole":
            data["whole"].append(hours)
        else:
            data["groups"].append(hours)

    cur.execute("""SELECT s.rahbar_user_id,COUNT(*) AS son
                   FROM aqlli_sinf_soati_qoidalari_v2 q
                   JOIN maktab_sinflari s ON s.id=q.sinf_id
                   WHERE q.maktab_id=%s AND q.faol=TRUE
                     AND s.rahbar_user_id IS NOT NULL
                   GROUP BY s.rahbar_user_id""", (maktab_id,))
    class_hour_extra = {}
    for row in cur.fetchall():
        teacher_id = row.get("rahbar_user_id")
        if teacher_id is not None:
            class_hour_extra[int(teacher_id)] = int(row.get("son") or 0)

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
        base = int(teacher_base.get(teacher_id, 0))
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
                "haftalik_soat": int(class_totals.get(int(cls["id"]), 0)),
                "yillik_soat": round(int(class_totals.get(int(cls["id"]), 0)) * school_weeks),
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
    cur.execute("SELECT * FROM aqlli_xonalar_v2 WHERE maktab_id=%s AND faol=TRUE ORDER BY nomi", (maktab_id,))
    rooms = [dict(row) for row in cur.fetchall()]
    cur.execute("""SELECT avtomatik_tavsiya FROM aqlli_jadval_boshqaruv_v19_2
                   WHERE maktab_id=%s""", (maktab_id,))
    mode = cur.fetchone()
    return {
        "versiya": "teacher-first-smart-load-v19.2",
        "paket": "all-14-sections-updated",
        "sinflar": classes,
        "oqituvchilar": teachers,
        "fanlar": subjects,
        "xonalar": rooms,
        "guruh_variantlari": variants,
        "birikmalar": rows,
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


class V192TeacherLoadRow(BaseModel):
    sinf_id: int
    fan_nomi: str
    guruh_kaliti: str = "whole"
    haftalik_soat: int
    kunlik_max: int = 1
    xona_id: Optional[int] = None


class V192TeacherLoadSave(BaseModel):
    maktab_id: int
    user_id: int
    qatorlar: list[V192TeacherLoadRow]


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

    cur.execute("""UPDATE aqlli_sinf_fan_yuklamalari_v2
                   SET haftalik_soat=0,asosiy_oqituvchi_user_id=NULL
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
        hours = [max(0, int(row.get("haftalik_soat") or 0)) for row in active]
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
        if len(whole) == 1 and not groups and int(whole[0].get("haftalik_soat") or 0) > 0:
            mode = "whole"
            valid = True
        elif groups and not whole:
            group_keys = {str(row["guruh_kaliti"]) for row in groups}
            hours = {int(row.get("haftalik_soat") or 0) for row in groups}
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


@app.put("/api/maktab/aqlli_jadval/v3/oqituvchi_yuklamasi")
def v192_teacher_load_save(sorov: V192TeacherLoadSave, token: str):
    actor_id = _jwt_tekshir(token)
    conn = _db(); cur = conn.cursor()
    try:
        _v192_tables(cur)
        if not _v1852_manager(cur, actor_id, sorov.maktab_id):
            raise HTTPException(status_code=403, detail="O'qituvchi yuklamasini faqat rahbariyat boshqaradi")
        cur.execute("""SELECT user_id,full_name FROM users
                       WHERE user_id=%s AND maktab_id=%s FOR UPDATE""",
                    (sorov.user_id, sorov.maktab_id))
        teacher = cur.fetchone()
        if not teacher:
            raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
        classes, systems, variants = _v192_group_variants(cur, sorov.maktab_id)
        valid_classes = {int(row["id"]) for row in classes}
        variant_map = {
            (int(row["sinf_id"]), str(row["guruh_kaliti"])): row
            for row in variants
        }
        seen = set()
        cleaned = []
        for index, item in enumerate(sorov.qatorlar, start=1):
            if int(item.sinf_id) not in valid_classes:
                raise HTTPException(status_code=400, detail=f"{index}-qator: sinf bu maktabga tegishli emas")
            subject = _v192_clean_subject(item.fan_nomi)
            if not subject:
                raise HTTPException(status_code=400, detail=f"{index}-qator: fan tanlanmagan")
            group_key = _v1875_group_key(item.guruh_kaliti)
            variant = variant_map.get((int(item.sinf_id), group_key))
            if not variant:
                raise HTTPException(status_code=400, detail=f"{index}-qator: tanlangan guruh bu sinfda yo'q")
            hours = int(item.haftalik_soat)
            daily = int(item.kunlik_max)
            if hours < 1 or hours > 20:
                raise HTTPException(status_code=400, detail=f"{index}-qator: haftalik soat 1–20 bo'lishi kerak")
            if daily < 1 or daily > 4:
                raise HTTPException(status_code=400, detail=f"{index}-qator: kunlik maksimum 1–4 bo'lishi kerak")
            key = (int(item.sinf_id), _v1875_subject_key(subject), group_key)
            if key in seen:
                raise HTTPException(status_code=400, detail=f"{index}-qator: bir xil fan–sinf–guruh ikki marta yozilgan")
            seen.add(key)
            cur.execute("""SELECT b.user_id,u.full_name FROM maktab_dars_birikmalari b
                           JOIN users u ON u.user_id=b.user_id
                           WHERE b.maktab_id=%s AND b.sinf_id=%s
                             AND LOWER(TRIM(b.fan_nomi))=LOWER(TRIM(%s))
                             AND COALESCE(NULLIF(b.guruh_kaliti,''),'whole')=%s
                             AND b.user_id<>%s LIMIT 1""",
                        (sorov.maktab_id, item.sinf_id, subject, group_key, sorov.user_id))
            owner = cur.fetchone()
            if owner:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"{subject} / {variant['sinf']} / {variant['guruh_nomi']} "
                        f"allaqachon {owner['full_name']}ga biriktirilgan"
                    ),
                )
            cleaned.append({
                "sinf_id": int(item.sinf_id),
                "fan_nomi": subject,
                "guruh_kaliti": group_key,
                "haftalik_soat": hours,
                "kunlik_max": daily,
                "xona_id": int(item.xona_id) if item.xona_id else None,
                "variant": variant,
            })

        cur.execute("DELETE FROM maktab_dars_birikmalari WHERE maktab_id=%s AND user_id=%s",
                    (sorov.maktab_id, sorov.user_id))
        for row in cleaned:
            cur.execute("""INSERT INTO maktab_dars_birikmalari(
                            maktab_id,user_id,sinf_id,fan_nomi,guruh_kaliti,
                            haftalik_soat,kunlik_max,xona_id,manba,yangilangan_at)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'v19.2_sayt',NOW())""",
                        (
                            sorov.maktab_id, sorov.user_id, row["sinf_id"],
                            row["fan_nomi"], row["guruh_kaliti"],
                            row["haftalik_soat"], row["kunlik_max"], row["xona_id"],
                        ))
            cur.execute("""INSERT INTO maktab_fanlari(maktab_id,fan_nomi)
                           VALUES(%s,%s) ON CONFLICT DO NOTHING""",
                        (sorov.maktab_id, row["fan_nomi"]))
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

        cur.execute("DELETE FROM maktab_xodim_sinflari WHERE maktab_id=%s AND user_id=%s",
                    (sorov.maktab_id, sorov.user_id))
        by_class = {}
        for row in cleaned:
            by_class.setdefault(row["sinf_id"], []).append(row["fan_nomi"])
        for class_id, subjects in by_class.items():
            unique_subjects = list(dict.fromkeys(subjects))
            cur.execute("""INSERT INTO maktab_xodim_sinflari(
                            maktab_id,user_id,sinf_id,fanlari)
                           VALUES(%s,%s,%s,%s)""",
                        (sorov.maktab_id, sorov.user_id, class_id, "; ".join(unique_subjects)))
        subject_list = sorted(
            set(row["fan_nomi"] for row in cleaned),
            key=lambda value: value.casefold(),
        )
        weekly_total = sum(row["haftalik_soat"] for row in cleaned)
        cur.execute("""UPDATE users SET fanlari=%s,haftalik_dars_soati=%s,
                                      oqitadigan_sinflari=%s
                       WHERE user_id=%s""",
                    (
                        "; ".join(subject_list) or None,
                        weekly_total,
                        "; ".join(
                            sorted(
                                {row["variant"]["sinf"] for row in cleaned},
                                key=_v1859_sinf_sort_key,
                            )
                        ) or None,
                        sorov.user_id,
                    ))
        warnings = _v192_sync_schedule_sources(cur, sorov.maktab_id)
        auto_confirmation = _v192_auto_confirm_exact_pairs(
            cur, sorov.maktab_id, actor_id
        )
        payload = _v192_matrix_payload(cur, sorov.maktab_id)
        conn.commit()
        return {
            "holat": "saqlandi",
            "oqituvchi": teacher["full_name"],
            "qator_soni": len(cleaned),
            "haftalik_jami": weekly_total,
            "ogohlantirishlar": warnings,
            "guruh_tasdiqlari": auto_confirmation,
            "matritsa": payload,
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
            if int(rule["user_id"]) != teacher_id or not bool(rule.get("qattiq")):
                continue
            if int(rule["hafta_kuni"]) != int(target_day):
                continue
            if rule["turi"] == "metod_kuni":
                reasons.append("o'qituvchining metod kuni")
                break
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
        key = (
            int(teacher_id), int(row["hafta_kuni"]),
            int(row["smena"]), int(row["dars_raqami"]),
        )
        grouped.setdefault(key, []).append(row)
    result = []
    for key, rows in grouped.items():
        class_ids = {int(row["sinf_id"]) for row in rows}
        if len(rows) > 1:
            result.append({
                "oqituvchi_user_id": key[0],
                "oqituvchi_ismi": rows[0].get("oqituvchi_ismi"),
                "hafta_kuni": key[1],
                "smena": key[2],
                "dars_raqami": key[3],
                "sinflar": list(dict.fromkeys(f"{row['sinf']}-{row['harf']}" for row in rows)),
                "slot_idlar": [int(row["id"]) for row in rows],
            })
    return result


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
            score = distance + teacher_daily + (3 if kind == "almashtirish" else 0)
            suggestions.append({
                "turi": kind,
                "yangi_hafta_kuni": day,
                "yangi_smena": int(source["smena"]),
                "yangi_dars_raqami": period,
                "baho": score,
                "nishon": _v192_bundle_label(target_bundle),
                "nishon_slot_idlar": sorted(target_ids),
                "izoh": (
                    "Bo'sh katakka ko'chirish mumkin"
                    if not target_bundle
                    else "Ikki dars joyini xavfsiz almashtirish mumkin"
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
                    boshlanish_vaqti,tugash_vaqti,yuklama_id,takror_raqami)
                   SELECT %s,maktab_id,sinf_id,hafta_kuni,smena,dars_raqami,
                          fan_nomi,oqituvchi_user_id,guruh_kaliti,xona_id,xona_matni,
                          boshlanish_vaqti,tugash_vaqti,yuklama_id,takror_raqami
                   FROM aqlli_jadval_slotlari_v2 WHERE urinish_id=%s""",
                (new_run_id, run["id"]))
    return new_run_id


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

# Preserve Python monolith semantics: late definitions must be visible to
# earlier platform routes such as the employee import endpoint.
for _v19_name, _v19_value in list(globals().items()):
    if _v19_name not in _V19_IMPORTED_NAMES and not _v19_name.startswith("__"):
        setattr(_platform, _v19_name, _v19_value)

__all__ = [name for name in globals() if not name.startswith("__")]

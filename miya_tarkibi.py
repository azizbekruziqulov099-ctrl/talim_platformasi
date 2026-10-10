"""REV97: bog'cha yosh guruhlari 2-3 / 4-5 / 6-7 ga o'tdi va admin uchun «Miya tarkibi».

1) Bir martalik tozalash (serverda faqat BIR MARTA, keyingi yuklashlarga ta'sir qilmaydi):
   * eski «3-4 yosh» / «5-6 yosh» bilan yozilgan AI miya ma'lumotlari (kitob, darslar, mavzu xaritasi, rasmlar) o'chiriladi;
   * shu guruhdagi bolalar profili yangi guruhga o'tadi (tug'ilgan sanasi bo'lsa — yoshiga qarab, bo'lmasa 3-4 → 2-3, 5-6 → 4-5).
   Bajarilgani samtm_bir_martalik jadvalida yoziladi — qayta ishga tushganda takrorlanmaydi.
2) Admin «Miya tarkibi»: guruh (sinf/yosh) → fan bo'yicha miyada nima borligini ko'radi, kerakligini belgilab o'chiradi
   (miya darslari, mavzular, testlar — alohida tanlanadi).
"""
import json
import re
from datetime import date
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

MARKER = "rev97_bogcha_yosh_guruhlari"
LEGACY_SQL = r"^\s*(3\s*[-–—]\s*4|5\s*[-–—]\s*6)\s*yosh"
LEGACY_MAP = {"3-4 yosh": "2-3 yosh", "5-6 yosh": "4-5 yosh"}
CONFIRM_WORD = "O'CHIRISH"


def age_on(birth, today=None):
    if not birth:
        return None
    today = today or date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def new_group(old_group, birth=None, today=None):
    """Eski guruh → yangi: avval tug'ilgan sana bo'yicha, bo'lmasa yaqin kichik guruh."""
    age = age_on(birth, today)
    if age is not None and 2 <= age <= 8:
        return "2-3 yosh" if age <= 3 else "4-5 yosh" if age <= 5 else "6-7 yosh"
    return LEGACY_MAP.get(old_group, old_group)


def legacy_of(value):
    text = str(value or "").replace("–", "-").replace("—", "-")
    m = re.match(r"^\s*([35])\s*-\s*([46])\s*yosh", text, re.I)
    if m and int(m[2]) == int(m[1]) + 1:
        return f"{m[1]}-{m[2]} yosh"
    return ""


def subject_key(value):
    return re.sub(r"\s+", " ", str(value or "").replace("‘", "'").replace("’", "'")).strip().casefold()


def _table_exists(cur, name):
    cur.execute("SELECT to_regclass(%s) AS t", (f"public.{name}",))
    return bool((cur.fetchone() or {}).get("t"))


def run_once(conn):
    """Bir martalik REV97 o'tkazish. Natija (yoki None — avval bajarilgan bo'lsa)."""
    cur = conn.cursor()
    try:
        cur.execute("""CREATE TABLE IF NOT EXISTS samtm_bir_martalik(
                         kalit TEXT PRIMARY KEY, bajarildi TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                         natija JSONB NOT NULL DEFAULT '{}'::jsonb)""")
        conn.commit()
        cur.execute("SELECT pg_try_advisory_xact_lock(%s) AS ok", (19700097,))
        if not (cur.fetchone() or {}).get("ok"):
            conn.rollback()
            return None
        cur.execute("SELECT 1 FROM samtm_bir_martalik WHERE kalit=%s", (MARKER,))
        if cur.fetchone():
            conn.rollback()
            return None
        result = {"miya": _delete_legacy_brain(cur)}
        moved = 0
        cur.execute("""SELECT user_id, class, tugilgan_sana, kabutar_learning_profile AS lp FROM users
                       WHERE class ~* %s OR COALESCE(kabutar_learning_profile->>'age_group','') ~* %s""", (LEGACY_SQL, LEGACY_SQL))
        for u in cur.fetchall():
            old = legacy_of(u["class"]) or legacy_of((u.get("lp") or {}).get("age_group"))
            if not old:
                continue
            group = new_group(old, u.get("tugilgan_sana"))
            lp = dict(u.get("lp") or {})
            if legacy_of(lp.get("age_group")) or lp.get("role") == "bogcha":
                lp["age_group"] = group
            cur.execute("UPDATE users SET class = CASE WHEN class ~* %s THEN %s ELSE class END, kabutar_learning_profile=%s::jsonb WHERE user_id=%s",
                        (LEGACY_SQL, group, json.dumps(lp, ensure_ascii=False), u["user_id"]))
            moved += 1
        result["bolalar_kochirildi"] = moved
        cur.execute("INSERT INTO samtm_bir_martalik(kalit, natija) VALUES(%s, %s::jsonb) ON CONFLICT (kalit) DO NOTHING",
                    (MARKER, json.dumps(result, ensure_ascii=False)))
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _delete_legacy_brain(cur):
    out = {"kitoblar": 0, "darslar": 0, "xarita": 0, "rasmlar": 0, "togarak_rejalari": 0}
    if not _table_exists(cur, "ai_brain_units"):
        return out
    cur.execute("SELECT id, batch_id FROM ai_brain_sources WHERE grade ~* %s", (LEGACY_SQL,))
    src = cur.fetchall()
    ids = [r["id"] for r in src] or [0]
    batches = {r["batch_id"] for r in src}
    cur.execute("DELETE FROM ai_brain_units WHERE source_id = ANY(%s) OR topic_code ~* %s RETURNING batch_id", (ids, LEGACY_SQL))
    rows = cur.fetchall()
    out["darslar"] = len(rows)
    batches |= {r["batch_id"] for r in rows}
    cur.execute("DELETE FROM ai_brain_topic_maps WHERE source_id = ANY(%s) OR grade ~* %s OR topic_code ~* %s", (ids, LEGACY_SQL, LEGACY_SQL))
    out["xarita"] = cur.rowcount
    cur.execute("DELETE FROM ai_brain_sources WHERE id = ANY(%s)", (ids,))
    out["kitoblar"] = cur.rowcount
    if _table_exists(cur, "ai_brain_generated_club_plans"):
        cur.execute("DELETE FROM ai_brain_generated_club_plans WHERE grade ~* %s", (LEGACY_SQL,))
        out["togarak_rejalari"] = cur.rowcount
    if batches and _table_exists(cur, "ai_brain_media"):
        cur.execute("""DELETE FROM ai_brain_media m WHERE m.batch_id = ANY(%s)
                         AND NOT EXISTS (SELECT 1 FROM ai_brain_sources s WHERE s.batch_id=m.batch_id)
                         AND NOT EXISTS (SELECT 1 FROM ai_brain_units u WHERE u.batch_id=m.batch_id)""", (sorted(batches),))
        out["rasmlar"] = cur.rowcount
    return out


class Tanlov(BaseModel):
    sinf: str
    fan: str


class OchirIn(BaseModel):
    tanlanganlar: List[Tanlov]
    miya: bool = True
    mavzular: bool = False
    testlar: bool = False
    tasdiq: str = ""


def create_router(platform):
    router = APIRouter(prefix="/api/admin/miya_tarkibi", tags=["miya-tarkibi"])

    def db_run(token, fn):
        platform._admin_tekshir(token)
        conn = platform._db()
        cur = conn.cursor()
        try:
            out = fn(cur)
            conn.commit()
            return out
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    @router.get("")
    def overview(token: str):
        def fn(cur):
            rows = {}

            def slot(grade, subject):
                key = (str(grade or "").strip(), subject_key(subject))
                if key not in rows:
                    rows[key] = {"sinf": key[0], "fan": str(subject or "").strip(), "kitoblar": [], "miya_darslar": 0,
                                 "mavzular": 0, "testlar": 0, "eski_yosh": bool(legacy_of(key[0]))}
                return rows[key]

            if _table_exists(cur, "ai_brain_sources"):
                cur.execute("""SELECT s.id, s.grade, s.subject_name, s.book_title, s.status,
                                      (SELECT COUNT(*) FROM ai_brain_units u WHERE u.source_id=s.id) AS darslar
                               FROM ai_brain_sources s ORDER BY s.grade, s.subject_name, s.id""")
                for r in cur.fetchall():
                    sl = slot(r["grade"], r["subject_name"])
                    sl["kitoblar"].append({"id": r["id"], "nomi": r["book_title"], "holat": r["status"], "darslar": int(r["darslar"])})
                    sl["miya_darslar"] += int(r["darslar"])
            if _table_exists(cur, "dts_tree"):
                cur.execute("""SELECT grade, subject_name, COUNT(*) AS n FROM dts_tree WHERE is_deleted=FALSE GROUP BY 1,2""")
                for r in cur.fetchall():
                    slot(r["grade"], r["subject_name"])["mavzular"] += int(r["n"])
                cur.execute("""SELECT d.grade, d.subject_name, COUNT(*) AS n FROM generated_tests g
                               JOIN (SELECT DISTINCT topic_code, grade, subject_name FROM dts_tree WHERE is_deleted=FALSE) d
                                 ON d.topic_code=g.topic_code GROUP BY 1,2""")
                for r in cur.fetchall():
                    slot(r["grade"], r["subject_name"])["testlar"] += int(r["n"])
            done = None
            if _table_exists(cur, "samtm_bir_martalik"):
                cur.execute("SELECT natija, bajarildi FROM samtm_bir_martalik WHERE kalit=%s", (MARKER,))
                done = cur.fetchone()

            def order(r):
                g = r["sinf"]
                if "yosh" in g:
                    return (0, g)
                if g.isdigit():
                    return (1, f"{int(g):03d}")
                return (2, g)
            out = sorted(rows.values(), key=lambda r: (order(r), r["fan"].casefold()))
            return {"qatorlar": out, "yosh_guruhlari": ["2-3 yosh", "4-5 yosh", "6-7 yosh"],
                    "bir_martalik": {"natija": done["natija"], "vaqt": done["bajarildi"].isoformat()} if done else None}
        return db_run(token, fn)

    @router.post("/ochir")
    def delete(token: str, body: OchirIn):
        if body.tasdiq.strip().upper().replace("‘", "'").replace("’", "'") != CONFIRM_WORD:
            raise HTTPException(400, f"Tasdiqlash uchun «{CONFIRM_WORD}» deb yozing")
        if not body.tanlanganlar:
            raise HTTPException(400, "Hech narsa tanlanmagan")
        if not (body.miya or body.mavzular or body.testlar):
            raise HTTPException(400, "Nimani o‘chirishni belgilang: miya, mavzular yoki testlar")

        def fn(cur):
            total = {"kitoblar": 0, "darslar": 0, "xarita": 0, "rasmlar": 0, "mavzular": 0, "testlar": 0}
            has_dts, has_brain = _table_exists(cur, "dts_tree"), _table_exists(cur, "ai_brain_sources")
            for t in body.tanlanganlar[:200]:
                grade, subj = t.sinf.strip(), subject_key(t.fan)
                codes = []
                if has_dts:
                    cur.execute("SELECT DISTINCT topic_code, subject_name FROM dts_tree WHERE TRIM(grade)=%s", (grade,))
                    codes = [r["topic_code"] for r in cur.fetchall() if subject_key(r["subject_name"]) == subj]
                if body.miya and has_brain:
                    cur.execute("SELECT id, batch_id, subject_name FROM ai_brain_sources WHERE TRIM(grade)=%s", (grade,))
                    src = [r for r in cur.fetchall() if subject_key(r["subject_name"]) == subj]
                    ids = [r["id"] for r in src] or [0]
                    batches = {r["batch_id"] for r in src}
                    cur.execute("DELETE FROM ai_brain_units WHERE source_id = ANY(%s) OR topic_code = ANY(%s) RETURNING batch_id",
                                (ids, codes or [""]))
                    rows = cur.fetchall()
                    total["darslar"] += len(rows)
                    batches |= {r["batch_id"] for r in rows}
                    cur.execute("DELETE FROM ai_brain_topic_maps WHERE source_id = ANY(%s) OR topic_code = ANY(%s)", (ids, codes or [""]))
                    total["xarita"] += cur.rowcount
                    cur.execute("DELETE FROM ai_brain_sources WHERE id = ANY(%s)", (ids,))
                    total["kitoblar"] += cur.rowcount
                    if batches and _table_exists(cur, "ai_brain_media"):
                        cur.execute("""DELETE FROM ai_brain_media m WHERE m.batch_id = ANY(%s)
                                         AND NOT EXISTS (SELECT 1 FROM ai_brain_sources s WHERE s.batch_id=m.batch_id)
                                         AND NOT EXISTS (SELECT 1 FROM ai_brain_units u WHERE u.batch_id=m.batch_id)""", (sorted(batches),))
                        total["rasmlar"] += cur.rowcount
                if body.testlar and codes:
                    cur.execute("DELETE FROM generated_tests WHERE topic_code = ANY(%s)", (codes,))
                    total["testlar"] += cur.rowcount
                if body.mavzular and codes:
                    cur.execute("UPDATE dts_tree SET is_deleted=TRUE WHERE topic_code = ANY(%s) AND is_deleted=FALSE", (codes,))
                    total["mavzular"] += cur.rowcount
            return {"ochirildi": total}
        return db_run(token, fn)

    @router.on_event("startup")
    def once():
        try:
            conn = platform._db()
        except Exception as exc:  # baza band bo'lsa — keyingi ishga tushishda
            print(f"[REV97 yosh guruhlari] ulanish: {exc}", flush=True)
            return
        try:
            res = run_once(conn)
            if res is not None:
                print(f"[REV97 yosh guruhlari] bir martalik tozalash bajarildi: {res}", flush=True)
        except Exception as exc:
            print(f"[REV97 yosh guruhlari] xato: {exc}", flush=True)
        finally:
            conn.close()

    return router

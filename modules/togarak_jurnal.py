"""REV96: to'garak / repetitor guruhi jurnali — davomat (yo'qlama) va oylik to'lovlar hisobi.

Bot bilan bir xil jadvallar ishlatiladi (togarak_yoqlama, togarak_tolovlar) — o'qituvchi saytda belgilasa botda,
botda belgilasa saytda ko'rinadi. Faqat guruhning o'z o'qituvchisi (yoki admin) ko'ra va o'zgartira oladi.
Holatlar botdagidek: keldi | kelmadi | kech (izohda sabab yoziladi, masalan «sababli», «10 daqiqa»).
"""
import re
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

HOLATLAR = ("keldi", "kelmadi", "kech")


class Belgi(BaseModel):
    user_id: int
    holat: str
    izoh: Optional[str] = ""


class YoqlamaIn(BaseModel):
    sana: Optional[str] = None
    belgilar: List[Belgi]


class TolovIn(BaseModel):
    user_id: int
    oy: Optional[str] = None
    summa: Optional[int] = None


class SozlamaIn(BaseModel):
    oylik_summa: Optional[int] = None
    oylik_sana: Optional[int] = None


def parse_day(value):
    if not value:
        return date.today()
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "Sana YYYY-MM-DD ko‘rinishida bo‘lsin")


def parse_month(value):
    v = str(value or "").strip()[:7] or date.today().strftime("%Y-%m")
    if not re.fullmatch(r"20\d\d-(0[1-9]|1[0-2])", v):
        raise HTTPException(400, "Oy YYYY-MM ko‘rinishida bo‘lsin")
    return v


def month_bounds(oy):
    y, m = map(int, oy.split("-"))
    first = date(y, m, 1)
    nxt = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return first, nxt


def summary(rows, price):
    """Oylik hisob: to'liq to'lagan, qisman to'lagan, to'lamagan; kutilgan, yig'ilgan va qolgan qarz."""
    price = int(price or 0)
    paid_sum = lambda r: int(r.get("tolov_summa") or 0)
    full = [r for r in rows if r.get("tolov_summa") is not None and paid_sum(r) >= price]
    part = [r for r in rows if r.get("tolov_summa") is not None and paid_sum(r) < price]
    none = [r for r in rows if r.get("tolov_summa") is None]
    return {
        "azolar": len(rows), "tolaganlar": len(full), "qisman": len(part), "qarzdorlar": len(part) + len(none),
        "kutilgan": price * len(rows), "yigilgan": sum(paid_sum(r) for r in rows),
        "qarz": sum(max(0, price - paid_sum(r)) for r in rows),
    }


def create_router(platform):
    router = APIRouter(prefix="/api/togarak_jurnal", tags=["togarak-jurnal"])
    ready = {"ok": False}

    def ensure(conn, cur):
        if ready["ok"]:
            return
        cur.execute("""
            CREATE TABLE IF NOT EXISTS togarak_yoqlama(
              id SERIAL PRIMARY KEY, togarak_id INTEGER NOT NULL, user_id BIGINT NOT NULL,
              holat TEXT NOT NULL DEFAULT 'keldi', izoh TEXT, sana DATE NOT NULL DEFAULT CURRENT_DATE,
              created_at TIMESTAMP DEFAULT NOW(), UNIQUE(togarak_id,user_id,sana));
            CREATE TABLE IF NOT EXISTS togarak_tolovlar(
              id SERIAL PRIMARY KEY, togarak_id INTEGER NOT NULL, user_id BIGINT NOT NULL,
              summa INTEGER NOT NULL DEFAULT 0, oy TEXT NOT NULL, teacher_id BIGINT,
              created_at TIMESTAMP DEFAULT NOW(), UNIQUE(togarak_id,user_id,oy));
        """)
        for sql in ("CREATE UNIQUE INDEX IF NOT EXISTS ux_tg_yoqlama_kun ON togarak_yoqlama(togarak_id,user_id,sana)",
                    "CREATE UNIQUE INDEX IF NOT EXISTS ux_tg_tolov_oy ON togarak_tolovlar(togarak_id,user_id,oy)"):
            cur.execute("SAVEPOINT tgj")
            try:
                cur.execute(sql)
                cur.execute("RELEASE SAVEPOINT tgj")
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT tgj")   # eski takroriy yozuvlar bo'lsa — bot cheklovi bilan ishlaymiz
        conn.commit()
        ready["ok"] = True

    def run(token, togarak_id, fn):
        uid = platform._jwt_tekshir(token)
        conn = platform._db()
        cur = conn.cursor()
        try:
            ensure(conn, cur)
            cur.execute("""SELECT id,nomi,teacher_id,COALESCE(oylik_summa,0) AS oylik_summa,
                                  COALESCE(oylik_sana,1) AS oylik_sana, COALESCE(max_talaba,50) AS max_talaba
                           FROM togaraklar WHERE id=%s""", (togarak_id,))
            group = cur.fetchone()
            if not group:
                raise HTTPException(404, "Guruh topilmadi")
            if int(group["teacher_id"] or 0) != int(uid):
                cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
                if not cur.fetchone():
                    raise HTTPException(403, "Bu guruh sizga tegishli emas")
            out = fn(cur, uid, dict(group))
            conn.commit()
            return out
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def members(cur, togarak_id):
        if "tasdiq" not in ready:
            cur.execute("""SELECT 1 FROM information_schema.columns
                           WHERE table_name='togarak_azolar' AND column_name='tasdiqlangan'""")
            ready["tasdiq"] = bool(cur.fetchone())
        confirm = " AND COALESCE(ta.tasdiqlangan,TRUE)=TRUE" if ready["tasdiq"] else ""
        cur.execute(f"""SELECT u.user_id, u.full_name, u.class, u.phone
                        FROM togarak_azolar ta JOIN users u ON u.user_id=ta.user_id
                        WHERE ta.togarak_id=%s AND ta.aktiv=TRUE{confirm}
                        ORDER BY u.full_name""", (togarak_id,))
        return [dict(r) for r in cur.fetchall()]

    @router.get("/{togarak_id}")
    def journal(togarak_id: int, token: str, sana: str = "", oy: str = ""):
        day = parse_day(sana)
        month = parse_month(oy or day.strftime("%Y-%m"))
        first, nxt = month_bounds(month)

        def fn(cur, uid, group):
            rows = members(cur, togarak_id)
            ids = [r["user_id"] for r in rows] or [0]
            cur.execute("SELECT user_id,holat,izoh FROM togarak_yoqlama WHERE togarak_id=%s AND sana=%s AND user_id = ANY(%s)",
                        (togarak_id, day, ids))
            today = {r["user_id"]: r for r in cur.fetchall()}
            cur.execute("""SELECT user_id,
                                  COUNT(*) FILTER (WHERE holat='keldi') AS keldi,
                                  COUNT(*) FILTER (WHERE holat='kelmadi') AS kelmadi,
                                  COUNT(*) FILTER (WHERE holat='kech') AS kech
                           FROM togarak_yoqlama WHERE togarak_id=%s AND sana>=%s AND sana<%s GROUP BY user_id""",
                        (togarak_id, first, nxt))
            stats = {r["user_id"]: r for r in cur.fetchall()}
            cur.execute("SELECT user_id,summa,created_at FROM togarak_tolovlar WHERE togarak_id=%s AND oy=%s", (togarak_id, month))
            pays = {r["user_id"]: r for r in cur.fetchall()}
            cur.execute("SELECT DISTINCT sana FROM togarak_yoqlama WHERE togarak_id=%s AND sana>=%s AND sana<%s ORDER BY sana",
                        (togarak_id, first, nxt))
            days = [r["sana"].isoformat() for r in cur.fetchall()]
            out = []
            for r in rows:
                t, s, p = today.get(r["user_id"]), stats.get(r["user_id"]) or {}, pays.get(r["user_id"])
                out.append({"user_id": r["user_id"], "ism": r["full_name"] or "O‘quvchi", "sinf": r.get("class") or "",
                            "holat": t["holat"] if t else None, "izoh": (t or {}).get("izoh") or "",
                            "oy_keldi": int(s.get("keldi") or 0), "oy_kelmadi": int(s.get("kelmadi") or 0), "oy_kech": int(s.get("kech") or 0),
                            "tolov_summa": int(p["summa"]) if p else None,
                            "tolov_sana": p["created_at"].date().isoformat() if p and p.get("created_at") else None})
            return {"guruh": {"id": group["id"], "nomi": group["nomi"], "oylik_summa": int(group["oylik_summa"]),
                              "oylik_sana": int(group["oylik_sana"]), "max_talaba": int(group["max_talaba"])},
                    "sana": day.isoformat(), "oy": month, "dars_kunlari": days, "azolar": out,
                    "belgilangan": sum(1 for x in out if x["holat"]), "hisob": summary(out, group["oylik_summa"])}
        return run(token, togarak_id, fn)

    @router.put("/{togarak_id}/yoqlama")
    def mark(togarak_id: int, token: str, body: YoqlamaIn):
        day = parse_day(body.sana)
        if day > date.today():
            raise HTTPException(400, "Kelajakdagi kunga yo‘qlama qilib bo‘lmaydi")
        for b in body.belgilar:
            if b.holat not in HOLATLAR:
                raise HTTPException(400, "Holat: keldi, kelmadi yoki kech")

        def fn(cur, uid, group):
            allowed = {r["user_id"] for r in members(cur, togarak_id)}
            saved = 0
            for b in body.belgilar:
                if b.user_id not in allowed:
                    continue
                cur.execute("""INSERT INTO togarak_yoqlama(togarak_id,user_id,holat,izoh,sana) VALUES(%s,%s,%s,%s,%s)
                               ON CONFLICT (togarak_id,user_id,sana) DO UPDATE SET holat=EXCLUDED.holat, izoh=EXCLUDED.izoh""",
                            (togarak_id, b.user_id, b.holat, (b.izoh or "").strip()[:120] or None, day))
                saved += 1
            return {"saqlandi": saved, "sana": day.isoformat()}
        return run(token, togarak_id, fn)

    @router.post("/{togarak_id}/tolov")
    def pay(togarak_id: int, token: str, body: TolovIn):
        month = parse_month(body.oy)

        def fn(cur, uid, group):
            if body.user_id not in {r["user_id"] for r in members(cur, togarak_id)}:
                raise HTTPException(404, "Bu o‘quvchi guruhda emas")
            amount = int(body.summa if body.summa is not None else group["oylik_summa"] or 0)
            if amount < 0 or amount > 100_000_000:
                raise HTTPException(400, "Summa noto‘g‘ri")
            cur.execute("""INSERT INTO togarak_tolovlar(togarak_id,user_id,summa,oy,teacher_id) VALUES(%s,%s,%s,%s,%s)
                           ON CONFLICT (togarak_id,user_id,oy) DO UPDATE SET summa=EXCLUDED.summa""",
                        (togarak_id, body.user_id, amount, month, uid))
            return {"ok": True, "oy": month, "summa": amount}
        return run(token, togarak_id, fn)

    @router.delete("/{togarak_id}/tolov")
    def unpay(togarak_id: int, token: str, user_id: int, oy: str = ""):
        month = parse_month(oy)

        def fn(cur, uid, group):
            cur.execute("DELETE FROM togarak_tolovlar WHERE togarak_id=%s AND user_id=%s AND oy=%s", (togarak_id, user_id, month))
            return {"ok": True, "ochirildi": cur.rowcount}
        return run(token, togarak_id, fn)

    @router.put("/{togarak_id}/sozlama")
    def settings(togarak_id: int, token: str, body: SozlamaIn):
        def fn(cur, uid, group):
            if body.oylik_summa is not None:
                if body.oylik_summa < 0 or body.oylik_summa > 100_000_000:
                    raise HTTPException(400, "Oylik summa noto‘g‘ri")
                cur.execute("UPDATE togaraklar SET oylik_summa=%s WHERE id=%s", (body.oylik_summa, togarak_id))
            if body.oylik_sana is not None:
                if not 1 <= body.oylik_sana <= 28:
                    raise HTTPException(400, "To‘lov kuni 1–28 oralig‘ida bo‘lsin")
                cur.execute("UPDATE togaraklar SET oylik_sana=%s WHERE id=%s", (body.oylik_sana, togarak_id))
            return {"ok": True}
        return run(token, togarak_id, fn)

    return router

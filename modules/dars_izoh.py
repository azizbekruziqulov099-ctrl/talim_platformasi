"""REV412: Dars izohlari — admin har darsni ko'rib, aniq joyiga (qadam, soniya) izoh qoldiradi yoki umumiy izoh yozadi;
hammasi bitta faylga yig'iladi (Claude o'qib, Miya'ni shunga qarab tuzatadi)."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field


def migrate(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS dars_izoh (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, topic_code TEXT NOT NULL DEFAULT '',
        dars_nomi TEXT NOT NULL DEFAULT '', fan TEXT NOT NULL DEFAULT '', qadam INT, qadam_turi TEXT NOT NULL DEFAULT '', qadam_matn TEXT NOT NULL DEFAULT '',
        soniya INT, matn TEXT NOT NULL, holat TEXT NOT NULL DEFAULT 'yangi', yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dars_izoh_topic ON dars_izoh(topic_code, id)")


class Izoh(BaseModel):
    token: Optional[str] = None
    topic_code: str = Field(default="", max_length=80)       # bo'sh — umumiy izoh (dars jarayoni haqida)
    dars_nomi: str = Field(default="", max_length=300)
    fan: str = Field(default="", max_length=160)
    qadam: Optional[int] = None
    qadam_turi: str = Field(default="", max_length=30)
    qadam_matn: str = Field(default="", max_length=600)
    soniya: Optional[int] = None
    matn: str = Field(..., min_length=1, max_length=4000)


class Holat(BaseModel):
    token: Optional[str] = None
    holat: str = Field(..., max_length=12)


def vaqt_matn(s):
    if s is None:
        return ""
    s = max(0, int(s))
    return f"{s // 60:02d}:{s % 60:02d}"


def eksport_matn(izohlar):
    """Barcha izohlar → bitta Markdown hujjat (dars bo'yicha guruhlangan, umumiylar boshida)."""
    q = [f"# Dars izohlari — {datetime.now().strftime('%Y-%m-%d %H:%M')}", "",
         f"Jami: {len(izohlar)} ta izoh ({sum(1 for x in izohlar if x['holat'] == 'yangi')} tasi yangi).", ""]
    umumiy = [x for x in izohlar if not x["topic_code"]]
    if umumiy:
        q += ["## Umumiy izohlar (dars jarayoni haqida)", ""]
        q += [f"- [{x['holat']}] {x['matn']}" for x in umumiy] + [""]
    darslar = {}
    for x in izohlar:
        if x["topic_code"]:
            darslar.setdefault(x["topic_code"], []).append(x)
    for kod, xs in darslar.items():
        q += [f"## {xs[0]['dars_nomi'] or kod}", f"Kod: `{kod}`" + (f" · Fan: {xs[0]['fan']}" if xs[0]["fan"] else ""), ""]
        for x in sorted(xs, key=lambda y: (y["qadam"] if y["qadam"] is not None else -1, y["id"])):
            joy = []
            if x["qadam"] is not None:
                joy.append(f"{x['qadam']}-qadam" + (f" ({x['qadam_turi']})" if x["qadam_turi"] else ""))
            if x["soniya"] is not None:
                joy.append(vaqt_matn(x["soniya"]))
            q.append(f"- [{x['holat']}] {' · '.join(joy) + ': ' if joy else ''}{x['matn']}")
            if x["qadam_matn"]:
                q.append(f"  - Doskada: «{x['qadam_matn'][:300]}»")
        q.append("")
    return "\n".join(q)


def create_router(platform):
    router = APIRouter(tags=["dars_izoh"])

    def admin(cur, token, authorization):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        uid = int(platform._jwt_tekshir(t))
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
        if not cur.fetchone():
            raise HTTPException(403, "Dars izohlari — faqat admin uchun")
        return uid

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            migrate(cur)
            out = fn(cur); conn.commit(); return out
        except Exception:
            conn.rollback(); raise
        finally:
            cur.close(); conn.close()

    def qator(r):
        return {"id": int(r["id"]), "topic_code": r["topic_code"], "dars_nomi": r["dars_nomi"], "fan": r["fan"], "qadam": r["qadam"], "qadam_turi": r["qadam_turi"],
                "qadam_matn": r["qadam_matn"], "soniya": r["soniya"], "matn": r["matn"], "holat": r["holat"], "yaratildi": r["yaratildi"].isoformat()}

    @router.post("/api/dars_izoh")
    def yoz(body: Izoh, authorization: str = Header(None)):
        def go(cur):
            uid = admin(cur, body.token, authorization)
            cur.execute("""INSERT INTO dars_izoh(user_id, topic_code, dars_nomi, fan, qadam, qadam_turi, qadam_matn, soniya, matn)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                        (uid, body.topic_code.strip(), body.dars_nomi.strip(), body.fan.strip(), body.qadam, body.qadam_turi.strip(), body.qadam_matn.strip(),
                         body.soniya, body.matn.strip()))
            return {"ok": True, "izoh": qator(cur.fetchone())}
        return run(go)

    @router.get("/api/dars_izoh")
    def royxat(token: str = None, topic_code: str = Query(None, max_length=80), holat: str = Query("", max_length=12), authorization: str = Header(None)):
        def go(cur):
            admin(cur, token, authorization)
            sh, par = [], []
            if topic_code is not None:
                sh.append("topic_code=%s"); par.append(topic_code)
            if holat:
                sh.append("holat=%s"); par.append(holat)
            cur.execute(f"SELECT * FROM dars_izoh {'WHERE ' + ' AND '.join(sh) if sh else ''} ORDER BY id DESC LIMIT 2000", par)
            rows = [qator(r) for r in cur.fetchall()]
            return {"izohlar": rows, "yangi": sum(1 for r in rows if r["holat"] == "yangi")}
        return run(go)

    @router.get("/api/dars_izoh/eksport")
    def eksport(token: str = None, faqat_yangi: bool = Query(False), authorization: str = Header(None)):
        def go(cur):
            admin(cur, token, authorization)
            cur.execute(f"SELECT * FROM dars_izoh {'WHERE holat=%s' if faqat_yangi else ''} ORDER BY topic_code, qadam NULLS FIRST, id", ["yangi"] if faqat_yangi else [])
            return eksport_matn([qator(r) for r in cur.fetchall()])
        md = run(go)
        nom = f"dars_izohlari_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        return Response(md.encode("utf-8"), media_type="text/markdown; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{nom}"'})

    @router.post("/api/dars_izoh/{iid}/holat")
    def holat(iid: int, body: Holat, authorization: str = Header(None)):
        if body.holat not in ("yangi", "bajarildi"):
            raise HTTPException(400, "Holat: yangi yoki bajarildi")

        def go(cur):
            admin(cur, body.token, authorization)
            cur.execute("UPDATE dars_izoh SET holat=%s WHERE id=%s", (body.holat, iid))
            return {"ok": True}
        return run(go)

    @router.delete("/api/dars_izoh/{iid}")
    def ochir(iid: int, token: str = None, authorization: str = Header(None)):
        def go(cur):
            admin(cur, token, authorization)
            cur.execute("DELETE FROM dars_izoh WHERE id=%s", (iid,))
            return {"ok": True}
        return run(go)

    return router

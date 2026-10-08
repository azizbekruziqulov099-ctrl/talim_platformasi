"""REV106: o'qituvchi kirishda o'z fanlarini tanlaydi va faqat shularni ko'radi.

Tanlov users.kabutar_learning_profile->'fanlar' da saqlanadi. curriculum_scope.own_predicate
shu ro'yxat bo'yicha mavzular, AI darslar va testlarni cheklaydi. Admin cheklanmaydi.
"""
import json
import re
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from . import curriculum_scope as scope

MAX_SUBJECTS = 12


class SubjectChoice(BaseModel):
    token: Optional[str] = None
    fanlar: List[str] = Field(default_factory=list, max_length=MAX_SUBJECTS)


def _name(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def create_router(platform):
    router = APIRouter(tags=["O'qituvchi fanlari"])

    def who(token, authorization):
        tok = platform._jwt_header_yoki_query(token, authorization)
        uid = platform._jwt_tekshir(tok)
        return uid

    def teacher(cur, uid):
        cur.execute("SELECT to_jsonb(u) AS p FROM users u WHERE user_id=%s", (uid,))
        user = (cur.fetchone() or {}).get("p") or {}
        if not user:
            raise HTTPException(401, "Akkaunt topilmadi")
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
        return user, cur.fetchone() is not None

    def available(cur, uid):
        clause, params = scope.own_predicate(cur, uid, "d", subjects=False)
        cur.execute(f"""SELECT TRIM(d.subject_name) AS nom, COUNT(*) AS mavzu_soni
            FROM dts_tree d WHERE d.is_deleted=FALSE AND COALESCE(TRIM(d.subject_name),'')<>'' AND ({clause})
            GROUP BY TRIM(d.subject_name) ORDER BY TRIM(d.subject_name)""", params)
        merged = {}
        for row in cur.fetchall():
            key = _name(row["nom"]).casefold()
            if key not in merged:
                merged[key] = {"nom": _name(row["nom"]), "mavzu_soni": 0}
            merged[key]["mavzu_soni"] += int(row["mavzu_soni"] or 0)
        return list(merged.values())

    @router.get("/api/oqituvchi/fanlarim")
    def my_subjects(token: Optional[str] = None, authorization: str = Header(None)):
        uid = who(token, authorization)
        conn = platform._db(); cur = conn.cursor()
        try:
            user, admin = teacher(cur, uid)
            if admin:
                return {"admin": True, "tanlangan": [], "mavjud": [], "max": MAX_SUBJECTS}
            if user.get("role") != "oqituvchi":
                raise HTTPException(403, "Fan tanlash faqat o'qituvchilar uchun")
            learning = user.get("kabutar_learning_profile") or {}
            return {"admin": False, "tanlangan": learning.get("fanlar") or [], "mavjud": available(cur, uid), "max": MAX_SUBJECTS}
        finally:
            cur.close(); conn.close()

    @router.post("/api/oqituvchi/fanlarim")
    def save_subjects(body: SubjectChoice, authorization: str = Header(None)):
        tok = platform._jwt_header_yoki_query(body.token, authorization)
        uid = platform._jwt_tekshir(tok)
        conn = platform._db(); cur = conn.cursor()
        try:
            user, admin = teacher(cur, uid)
            if admin:
                raise HTTPException(400, "Admin barcha fanlarni ko'radi — tanlash shart emas")
            if user.get("role") != "oqituvchi":
                raise HTTPException(403, "Fan tanlash faqat o'qituvchilar uchun")
            options = {s["nom"].casefold(): s["nom"] for s in available(cur, uid)}
            chosen = []
            for name in body.fanlar:
                key = _name(name).casefold()
                if key in options and options[key] not in chosen:
                    chosen.append(options[key])
            if not chosen:
                raise HTTPException(422, "Kamida bitta fanni tanlang")
            learning = user.get("kabutar_learning_profile") or {}
            learning = {**learning, "fanlar": chosen[:MAX_SUBJECTS]}
            cur.execute("UPDATE users SET kabutar_learning_profile=%s::jsonb, oqituvchi_fani=COALESCE(NULLIF(oqituvchi_fani,''),%s) WHERE user_id=%s",
                        (json.dumps(learning), chosen[0], uid))
            conn.commit()
            return {"ok": True, "tanlangan": learning["fanlar"]}
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close(); conn.close()

    return router

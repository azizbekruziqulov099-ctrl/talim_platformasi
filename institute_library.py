"""Institut virtual kutubxonasi: javon, polka, papka, hujjat va ruxsatlar."""
import mimetypes
import re
from datetime import datetime, timezone
from typing import Optional

import psycopg2
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

MAX_FILE_BYTES = 30 * 1024 * 1024
MANAGER_ROLES = {"owner", "rektor", "prorektor", "institut_admin"}
DEPARTMENT_MANAGER_ROLES = {"kafedra_mudiri"}
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".rtf", ".csv", ".jpg", ".jpeg", ".png", ".webp", ".zip",
}


def create_institute_library_router(check_token, db):
    router = APIRouter(prefix="/api/institut/v23/kutubxona", tags=["institute-library"])

    def ensure(cur):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS institut_kutubxona_javonlari(
              id BIGSERIAL PRIMARY KEY, universitet_id INTEGER NOT NULL,
              fakultet_id INTEGER, kafedra_id INTEGER, nomi VARCHAR(180) NOT NULL,
              izoh TEXT, rang VARCHAR(20) NOT NULL DEFAULT '#175A7A', tartib INTEGER NOT NULL DEFAULT 0,
              yaratuvchi_id INTEGER NOT NULL, yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              faol BOOLEAN NOT NULL DEFAULT TRUE
            );
            CREATE TABLE IF NOT EXISTS institut_kutubxona_polkalari(
              id BIGSERIAL PRIMARY KEY, javon_id BIGINT NOT NULL REFERENCES institut_kutubxona_javonlari(id) ON DELETE CASCADE,
              nomi VARCHAR(180) NOT NULL, izoh TEXT, tartib INTEGER NOT NULL DEFAULT 0,
              yaratuvchi_id INTEGER NOT NULL, yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), faol BOOLEAN NOT NULL DEFAULT TRUE
            );
            CREATE TABLE IF NOT EXISTS institut_kutubxona_papkalari(
              id BIGSERIAL PRIMARY KEY, polka_id BIGINT NOT NULL REFERENCES institut_kutubxona_polkalari(id) ON DELETE CASCADE,
              nomi VARCHAR(180) NOT NULL, izoh TEXT, yil INTEGER, yaratuvchi_id INTEGER NOT NULL,
              yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), faol BOOLEAN NOT NULL DEFAULT TRUE
            );
            CREATE TABLE IF NOT EXISTS institut_kutubxona_hujjatlari(
              id BIGSERIAL PRIMARY KEY, papka_id BIGINT NOT NULL REFERENCES institut_kutubxona_papkalari(id) ON DELETE CASCADE,
              nomi VARCHAR(240) NOT NULL, fayl_nomi VARCHAR(240) NOT NULL, mime_type VARCHAR(160),
              hajm BIGINT NOT NULL, tarkib BYTEA NOT NULL, izoh TEXT, teglar TEXT[] NOT NULL DEFAULT '{}',
              yuklovchi_id INTEGER NOT NULL, yaratilgan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), faol BOOLEAN NOT NULL DEFAULT TRUE
            );
            CREATE TABLE IF NOT EXISTS institut_kutubxona_ruxsatlari(
              id BIGSERIAL PRIMARY KEY, universitet_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
              fakultet_id INTEGER, kafedra_id INTEGER, korish BOOLEAN NOT NULL DEFAULT TRUE,
              yuklash BOOLEAN NOT NULL DEFAULT TRUE, joylash BOOLEAN NOT NULL DEFAULT FALSE,
              boshqarish BOOLEAN NOT NULL DEFAULT FALSE, bergan_user_id INTEGER NOT NULL,
              yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              UNIQUE(universitet_id,user_id,fakultet_id,kafedra_id)
            );
            CREATE INDEX IF NOT EXISTS ix_kutubxona_javon_scope ON institut_kutubxona_javonlari(universitet_id,fakultet_id,kafedra_id);
            CREATE INDEX IF NOT EXISTS ix_kutubxona_hujjat_papka ON institut_kutubxona_hujjatlari(papka_id);
        """)

    def roles(cur, university_id, user_id):
        cur.execute("""SELECT rol,fakultet_id,kafedra_id FROM universitet_xodim_rollari
                       WHERE universitet_id=%s AND user_id=%s AND COALESCE(faol,TRUE)=TRUE""",
                    (university_id, user_id))
        return cur.fetchall()

    def access(cur, university_id, user_id, faculty_id=None, department_id=None):
        rs = roles(cur, university_id, user_id)
        is_admin = any(r["rol"] in MANAGER_ROLES for r in rs)
        is_head = any(r["rol"] in DEPARTMENT_MANAGER_ROLES and
                      (department_id is None or int(r["kafedra_id"] or 0) == int(department_id or 0)) for r in rs)
        own_scope = any(
            (not faculty_id or not r["fakultet_id"] or int(r["fakultet_id"]) == int(faculty_id)) and
            (not department_id or not r["kafedra_id"] or int(r["kafedra_id"]) == int(department_id))
            for r in rs
        )
        cur.execute("""SELECT korish,yuklash,joylash,boshqarish FROM institut_kutubxona_ruxsatlari
                       WHERE universitet_id=%s AND user_id=%s
                         AND (fakultet_id IS NULL OR fakultet_id=%s)
                         AND (kafedra_id IS NULL OR kafedra_id=%s)
                       ORDER BY kafedra_id NULLS LAST,fakultet_id NULLS LAST LIMIT 1""",
                    (university_id, user_id, faculty_id, department_id))
        grant = cur.fetchone() or {}
        return {
            "korish": is_admin or is_head or (own_scope and bool(grant.get("korish", True))),
            "yuklash": is_admin or is_head or (own_scope and bool(grant.get("yuklash", True))),
            "joylash": is_admin or is_head or (own_scope and bool(grant.get("joylash", False))),
            "boshqarish": is_admin or is_head or bool(grant.get("boshqarish", False)),
            "ruxsat_belgilash": is_admin or is_head,
        }

    def require_scope(cur, university_id, user_id, faculty_id=None, department_id=None, permission="korish"):
        rights = access(cur, university_id, user_id, faculty_id, department_id)
        if not rights.get(permission):
            raise HTTPException(403, "Bu bo‘lim uchun ruxsatingiz yo‘q")
        return rights

    def cabinet_scope(cur, cabinet_id):
        cur.execute("SELECT universitet_id,fakultet_id,kafedra_id FROM institut_kutubxona_javonlari WHERE id=%s AND faol", (cabinet_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(404, "Javon topilmadi")
        return row

    def folder_scope(cur, folder_id):
        cur.execute("""SELECT j.universitet_id,j.fakultet_id,j.kafedra_id
                       FROM institut_kutubxona_papkalari f
                       JOIN institut_kutubxona_polkalari p ON p.id=f.polka_id
                       JOIN institut_kutubxona_javonlari j ON j.id=p.javon_id
                       WHERE f.id=%s AND f.faol AND p.faol AND j.faol""", (folder_id,))
        row = cur.fetchone()
        if not row: raise HTTPException(404, "Papka topilmadi")
        return row

    @router.get("/xona")
    def room(token: str, universitet_id: int, q: str = ""):
        user_id = check_token(token); conn = db(); cur = conn.cursor()
        try:
            ensure(cur); conn.commit()
            rs = roles(cur, universitet_id, user_id)
            if not rs: raise HTTPException(403, "Institutga biriktirilmagansiz")
            cur.execute("SELECT COUNT(*) AS soni FROM institut_kutubxona_javonlari WHERE universitet_id=%s AND faol", (universitet_id,))
            if int(cur.fetchone()["soni"] or 0) == 0 and access(cur, universitet_id, user_id)["boshqarish"]:
                defaults = [
                    ("Bitiruv ishlari", "BMI, magistrlik va ilmiy ishlar fondi", "#694EA0", "O‘quv yillari", "2025–2026 bitiruv ishlari"),
                    ("Kafedra hujjatlari", "Bayonnoma, reja, hisobot va me’yoriy hujjatlar", "#175A7A", "Joriy hujjatlar", "Tasdiqlangan hujjatlar"),
                    ("Metodik fond", "Sillabus, qo‘llanma va dars ishlanmalari", "#0D7A77", "O‘quv-uslubiy materiallar", "Fanlar bo‘yicha"),
                    ("Elektron kitoblar", "Darslik, monografiya va ilmiy adabiyotlar", "#A86714", "Asosiy adabiyotlar", "Elektron nashrlar"),
                ]
                for cabinet_name, cabinet_note, color, shelf_name, folder_name in defaults:
                    cur.execute("""INSERT INTO institut_kutubxona_javonlari(universitet_id,nomi,izoh,rang,yaratuvchi_id)
                                   VALUES(%s,%s,%s,%s,%s) RETURNING id""", (universitet_id, cabinet_name, cabinet_note, color, user_id))
                    cabinet_id = cur.fetchone()["id"]
                    cur.execute("INSERT INTO institut_kutubxona_polkalari(javon_id,nomi,yaratuvchi_id) VALUES(%s,%s,%s) RETURNING id", (cabinet_id, shelf_name, user_id))
                    shelf_id = cur.fetchone()["id"]
                    cur.execute("INSERT INTO institut_kutubxona_papkalari(polka_id,nomi,yil,yaratuvchi_id) VALUES(%s,%s,%s,%s)", (shelf_id, folder_name, datetime.now(timezone.utc).year, user_id))
                conn.commit()
            params = [universitet_id]
            search_sql = ""
            if q.strip():
                search_sql = " AND (LOWER(d.nomi) LIKE %s OR LOWER(d.fayl_nomi) LIKE %s OR LOWER(COALESCE(d.izoh,'')) LIKE %s)"
                needle = f"%{q.strip().lower()}%"; params += [needle, needle, needle]
            cur.execute(f"""SELECT j.id AS javon_id,j.nomi AS javon_nomi,j.izoh AS javon_izoh,j.rang,
                              j.fakultet_id,j.kafedra_id,p.id AS polka_id,p.nomi AS polka_nomi,p.izoh AS polka_izoh,
                              f.id AS papka_id,f.nomi AS papka_nomi,f.izoh AS papka_izoh,f.yil,
                              d.id AS hujjat_id,d.nomi AS hujjat_nomi,d.fayl_nomi,d.mime_type,d.hajm,
                              d.izoh AS hujjat_izoh,d.teglar,d.yuklovchi_id,d.yaratilgan_at,u.full_name AS yuklovchi
                       FROM institut_kutubxona_javonlari j
                       LEFT JOIN institut_kutubxona_polkalari p ON p.javon_id=j.id AND p.faol
                       LEFT JOIN institut_kutubxona_papkalari f ON f.polka_id=p.id AND f.faol
                       LEFT JOIN institut_kutubxona_hujjatlari d ON d.papka_id=f.id AND d.faol
                       LEFT JOIN users u ON u.user_id=d.yuklovchi_id
                       WHERE j.universitet_id=%s AND j.faol {search_sql}
                       ORDER BY j.tartib,j.id,p.tartib,p.id,f.yil DESC NULLS LAST,f.id,d.yaratilgan_at DESC""", params)
            rows = cur.fetchall(); cabinets = {}
            for row in rows:
                rights = access(cur, universitet_id, user_id, row["fakultet_id"], row["kafedra_id"])
                if not rights["korish"]: continue
                cabinet = cabinets.setdefault(row["javon_id"], {"id": row["javon_id"], "nomi": row["javon_nomi"], "izoh": row["javon_izoh"], "rang": row["rang"], "fakultet_id": row["fakultet_id"], "kafedra_id": row["kafedra_id"], "ruxsatlar": rights, "polkalar": []})
                if not row["polka_id"]: continue
                shelf = next((x for x in cabinet["polkalar"] if x["id"] == row["polka_id"]), None)
                if not shelf:
                    shelf = {"id": row["polka_id"], "nomi": row["polka_nomi"], "izoh": row["polka_izoh"], "papkalar": []}; cabinet["polkalar"].append(shelf)
                if not row["papka_id"]: continue
                folder = next((x for x in shelf["papkalar"] if x["id"] == row["papka_id"]), None)
                if not folder:
                    folder = {"id": row["papka_id"], "nomi": row["papka_nomi"], "izoh": row["papka_izoh"], "yil": row["yil"], "hujjatlar": []}; shelf["papkalar"].append(folder)
                if row["hujjat_id"]:
                    folder["hujjatlar"].append({k.replace("hujjat_", ""): v for k, v in row.items() if k.startswith("hujjat_")} | {"id": row["hujjat_id"], "teglar": row["teglar"] or [], "yuklovchi": row["yuklovchi"], "yaratilgan_at": row["yaratilgan_at"]})
            return {"javonlar": list(cabinets.values()), "jami": sum(len(f["hujjatlar"]) for c in cabinets.values() for p in c["polkalar"] for f in p["papkalar"])}
        finally: cur.close(); conn.close()

    class CabinetIn(BaseModel):
        token: str; universitet_id: int; nomi: str; izoh: Optional[str] = None
        fakultet_id: Optional[int] = None; kafedra_id: Optional[int] = None; rang: str = "#175A7A"

    @router.post("/javon")
    def create_cabinet(body: CabinetIn):
        user_id = check_token(body.token); conn = db(); cur = conn.cursor()
        try:
            ensure(cur); require_scope(cur, body.universitet_id, user_id, body.fakultet_id, body.kafedra_id, "boshqarish")
            if not body.nomi.strip(): raise HTTPException(400, "Javon nomini kiriting")
            cur.execute("""INSERT INTO institut_kutubxona_javonlari(universitet_id,fakultet_id,kafedra_id,nomi,izoh,rang,yaratuvchi_id)
                           VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING id""", (body.universitet_id,body.fakultet_id,body.kafedra_id,body.nomi.strip(),body.izoh,body.rang,user_id))
            new_id=cur.fetchone()["id"]; conn.commit(); return {"id":new_id,"holat":"saqlandi"}
        except Exception: conn.rollback(); raise
        finally: cur.close(); conn.close()

    class ShelfIn(BaseModel): token: str; javon_id: int; nomi: str; izoh: Optional[str] = None
    @router.post("/polka")
    def create_shelf(body: ShelfIn):
        user_id=check_token(body.token); conn=db(); cur=conn.cursor()
        try:
            ensure(cur); s=cabinet_scope(cur,body.javon_id); require_scope(cur,s["universitet_id"],user_id,s["fakultet_id"],s["kafedra_id"],"boshqarish")
            cur.execute("INSERT INTO institut_kutubxona_polkalari(javon_id,nomi,izoh,yaratuvchi_id) VALUES(%s,%s,%s,%s) RETURNING id",(body.javon_id,body.nomi.strip(),body.izoh,user_id)); new_id=cur.fetchone()["id"]; conn.commit(); return {"id":new_id}
        except Exception: conn.rollback(); raise
        finally: cur.close(); conn.close()

    class FolderIn(BaseModel): token: str; polka_id: int; nomi: str; izoh: Optional[str] = None; yil: Optional[int] = None
    @router.post("/papka")
    def create_folder(body: FolderIn):
        user_id=check_token(body.token); conn=db(); cur=conn.cursor()
        try:
            ensure(cur); cur.execute("SELECT javon_id FROM institut_kutubxona_polkalari WHERE id=%s AND faol",(body.polka_id,)); p=cur.fetchone()
            if not p: raise HTTPException(404,"Polka topilmadi")
            s=cabinet_scope(cur,p["javon_id"]); require_scope(cur,s["universitet_id"],user_id,s["fakultet_id"],s["kafedra_id"],"boshqarish")
            cur.execute("INSERT INTO institut_kutubxona_papkalari(polka_id,nomi,izoh,yil,yaratuvchi_id) VALUES(%s,%s,%s,%s,%s) RETURNING id",(body.polka_id,body.nomi.strip(),body.izoh,body.yil,user_id)); new_id=cur.fetchone()["id"]; conn.commit(); return {"id":new_id}
        except Exception: conn.rollback(); raise
        finally: cur.close(); conn.close()

    @router.post("/hujjat")
    async def upload_document(token: str=Form(...), papka_id:int=Form(...), nomi:str=Form(""), izoh:str=Form(""), teglar:str=Form(""), fayl:UploadFile=File(...)):
        user_id=check_token(token); content=await fayl.read(MAX_FILE_BYTES+1)
        if len(content)>MAX_FILE_BYTES: raise HTTPException(413,"Fayl 30 MB dan katta bo‘lmasin")
        safe_name=re.sub(r"[^\w.()\- +'‘’]","_",fayl.filename or "hujjat")[:240]
        ext=("."+safe_name.rsplit(".",1)[-1].lower()) if "." in safe_name else ""
        if ext not in ALLOWED_EXTENSIONS: raise HTTPException(400,"Bu fayl turi qo‘llab-quvvatlanmaydi")
        conn=db(); cur=conn.cursor()
        try:
            ensure(cur); s=folder_scope(cur,papka_id); require_scope(cur,s["universitet_id"],user_id,s["fakultet_id"],s["kafedra_id"],"joylash")
            mime=fayl.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream"
            tags=[x.strip()[:40] for x in teglar.split(",") if x.strip()][:12]
            cur.execute("""INSERT INTO institut_kutubxona_hujjatlari(papka_id,nomi,fayl_nomi,mime_type,hajm,tarkib,izoh,teglar,yuklovchi_id)
                           VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",(papka_id,(nomi.strip() or safe_name)[:240],safe_name,mime,len(content),psycopg2.Binary(content),izoh or None,tags,user_id)); new_id=cur.fetchone()["id"]; conn.commit(); return {"id":new_id,"holat":"yuklandi"}
        except Exception: conn.rollback(); raise
        finally: cur.close(); conn.close()

    def document_response(token, document_id, disposition):
        user_id=check_token(token); conn=db(); cur=conn.cursor()
        try:
            ensure(cur); cur.execute("""SELECT d.*,j.universitet_id,j.fakultet_id,j.kafedra_id FROM institut_kutubxona_hujjatlari d
                JOIN institut_kutubxona_papkalari f ON f.id=d.papka_id JOIN institut_kutubxona_polkalari p ON p.id=f.polka_id
                JOIN institut_kutubxona_javonlari j ON j.id=p.javon_id WHERE d.id=%s AND d.faol""",(document_id,)); d=cur.fetchone()
            if not d: raise HTTPException(404,"Hujjat topilmadi")
            require_scope(cur,d["universitet_id"],user_id,d["fakultet_id"],d["kafedra_id"],"yuklash")
            ascii_name=re.sub(r"[^A-Za-z0-9._-]","_",d["fayl_nomi"])
            return Response(bytes(d["tarkib"]),media_type=d["mime_type"] or "application/octet-stream",headers={"Content-Disposition":f'{disposition}; filename="{ascii_name}"',"X-Content-Type-Options":"nosniff","Cache-Control":"private, max-age=60"})
        finally: cur.close(); conn.close()

    @router.get("/hujjat/{document_id}/korish")
    def preview(token:str,document_id:int): return document_response(token,document_id,"inline")
    @router.get("/hujjat/{document_id}/yuklash")
    def download(token:str,document_id:int): return document_response(token,document_id,"attachment")

    class PermissionIn(BaseModel):
        token:str; universitet_id:int; user_id:int; fakultet_id:Optional[int]=None; kafedra_id:Optional[int]=None
        korish:bool=True; yuklash:bool=True; joylash:bool=False; boshqarish:bool=False

    @router.post("/ruxsat")
    def set_permission(body:PermissionIn):
        admin_id=check_token(body.token); conn=db(); cur=conn.cursor()
        try:
            ensure(cur); rights=require_scope(cur,body.universitet_id,admin_id,body.fakultet_id,body.kafedra_id,"boshqarish")
            if not rights["ruxsat_belgilash"]: raise HTTPException(403,"Ruxsat belgilash vakolati yo‘q")
            cur.execute("""INSERT INTO institut_kutubxona_ruxsatlari(universitet_id,user_id,fakultet_id,kafedra_id,korish,yuklash,joylash,boshqarish,bergan_user_id)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(universitet_id,user_id,fakultet_id,kafedra_id)
                DO UPDATE SET korish=EXCLUDED.korish,yuklash=EXCLUDED.yuklash,joylash=EXCLUDED.joylash,boshqarish=EXCLUDED.boshqarish,bergan_user_id=EXCLUDED.bergan_user_id,yangilangan_at=NOW()""",
                (body.universitet_id,body.user_id,body.fakultet_id,body.kafedra_id,body.korish,body.yuklash,body.joylash,body.boshqarish,admin_id)); conn.commit(); return {"holat":"saqlandi"}
        except Exception: conn.rollback(); raise
        finally: cur.close(); conn.close()

    @router.delete("/hujjat/{document_id}")
    def archive_document(document_id:int,token:str):
        user_id=check_token(token); conn=db(); cur=conn.cursor()
        try:
            ensure(cur); cur.execute("""SELECT d.yuklovchi_id,j.universitet_id,j.fakultet_id,j.kafedra_id FROM institut_kutubxona_hujjatlari d JOIN institut_kutubxona_papkalari f ON f.id=d.papka_id JOIN institut_kutubxona_polkalari p ON p.id=f.polka_id JOIN institut_kutubxona_javonlari j ON j.id=p.javon_id WHERE d.id=%s AND d.faol""",(document_id,)); d=cur.fetchone()
            if not d: raise HTTPException(404,"Hujjat topilmadi")
            rights=access(cur,d["universitet_id"],user_id,d["fakultet_id"],d["kafedra_id"])
            if d["yuklovchi_id"]!=user_id and not rights["boshqarish"]: raise HTTPException(403,"Faqat o‘zingiz joylagan hujjatni olib tashlaysiz")
            cur.execute("UPDATE institut_kutubxona_hujjatlari SET faol=FALSE, yangilangan_at=NOW() WHERE id=%s",(document_id,)); conn.commit(); return {"holat":"arxivlandi"}
        except Exception: conn.rollback(); raise
        finally: cur.close(); conn.close()

    return router

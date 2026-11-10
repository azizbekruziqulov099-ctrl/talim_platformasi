"""REV480: ko'nikmalar xaritasi — har javob bir ko'nikmaga yoziladi: hisoblash, masala yechish, nazariya, chizish (geometriya),
mantiq, eslab qolish; tezlik — javob vaqtidan (savol vaqtining yarmidan tez va to'g'ri bo'lsa «tez»).
Manbalar: dars testlari, nazoratlar, ekspeditsiya, dars oldidan eslash. O'quvchi o'zini, o'qituvchi o'z guruhini ko'radi."""
import re
from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

KONIKMALAR = {"hisoblash": "🔢 Hisoblash", "masala": "🧩 Masala yechish", "nazariya": "📖 Nazariya", "chizish": "📐 Chizish va geometriya",
              "mantiq": "🧠 Mantiq", "eslash": "🔁 Eslab qolish", "tezlik": "⚡ Tezlik"}
_GEO = re.compile(r"burchak|uchburchak|to.rtburchak|kvadrat|aylana|doira|perimetr|yuz[ia]?\b|hajm|kub|prizma|piramida|silindr|konus|shar|vektor|koordinat|chiz|yasa|shakl|kesma|nur\b|parallel|perpendikul|simmetr", re.I)
_NAZ = re.compile(r"ta.rif|qoida|xossa|nima deyiladi|deb ataladi|qaysi biri to.g.ri|to.g.rimi|tasdiq|teorema|formula(si)?\b|nimaga teng deyiladi|tushuncha", re.I)
_MAN = re.compile(r"ketma-?ket|naqsh|keyingi son|ortiqcha|xatoni top|mantiq|qonuniyat|davom ettiring|juftini|o.xshash", re.I)
_MAS = re.compile(r"necha so.m|nechta|necha (kg|km|litr|soat|daqiqa|metr|kishi)|qancha|\b(oldi|berdi|sotdi|yurdi|bor edi|qoldi)\b|tezlik|narx", re.I)
_EKSP = {"hisoblash": {"qosh", "ayir", "kop1", "kop2", "kop10", "bol", "bol2", "qoldiq", "kasrkop", "kasrbol", "kasrqosh", "kasrqosh2", "kasr_n_bol", "kasr_n_kop",
                       "n_kasr_bol", "onli", "onli10", "daraja", "ildiz", "ildizxossa", "ifoda", "kophad", "qisqa", "kvayirma", "ajrat", "logarifm", "hosila", "integral", "limit", "yaxlit", "korxona", "taqqos"},
         "masala": {"harakat", "qarama", "quvlama", "qiymat", "unum", "nisbat", "meyor", "chegirma", "osish", "foiz", "ortacha_tezlik", "qolgan", "toplam"},
         "chizish": {"perimetr", "yuz", "hajm", "kub", "kubqirra", "uchburchak", "uchburchak_yuz", "uchburchak_burchak", "tengyonli", "pifagor", "tortburchak", "tortburchak_burchak",
                     "trapetsiya", "trapyuz", "oxshash", "kosinus", "sinus", "aylana", "doira", "sektor", "muntazam", "vektor", "masofa", "prizma", "piramida", "silindr", "konus",
                     "shar", "fazovektor", "skalyar", "burchak", "burchak_chiziq", "burchak_nuqta", "qoshni", "parallel", "jism", "koordinata"},
         "mantiq": {"naqsh", "kombinatorika", "ehtimol", "statistika", "ortacha", "diagramma"}}


def aniqla(savol="", tur="", korinish="", manba=""):
    """Bitta javob → ko'nikma kaliti."""
    if manba in ("eslash", "takror", "uzoq", "nazoratchi") or korinish in ("eslash",):
        return "eslash"
    if korinish in ("xato_top", "naqsh"):
        return "mantiq"
    if korinish == "togri_notogri":
        return "nazariya"
    base = str(tur or "").split(":")[0]
    for k, turlar in _EKSP.items():
        if base in turlar:
            return k
    if base and ":" in str(tur):   # xalqaro (PISA) kontekstlari — hayotiy masala
        return "masala"
    t = re.sub(r"\$[^$]*\$", " ", str(savol or ""))
    if _MAN.search(t):
        return "mantiq"
    if _NAZ.search(t):
        return "nazariya"
    if _GEO.search(t):
        return "chizish"
    if len(t.strip()) > 60 or _MAS.search(t):
        return "masala"
    return "hisoblash"


class Hodisa(BaseModel):
    savol: str = ""
    tur: str = ""
    korinish: str = ""
    manba: str = ""
    togri: bool = False
    soniya: Optional[float] = None
    chegara: Optional[float] = None


class Yozuv(BaseModel):
    hodisalar: List[Hodisa] = []


_TAYYOR = {"ok": False}


def jadval(cur):
    if _TAYYOR["ok"]:
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS konikma_holat (user_id BIGINT NOT NULL, konikma TEXT NOT NULL, togri INT NOT NULL DEFAULT 0,
        jami INT NOT NULL DEFAULT 0, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, konikma))""")
    _TAYYOR["ok"] = True


def yoz(cur, uid, hodisalar):
    """Hodisalarni yig'ib, bir martada yozadi. hodisalar — Hodisa yoki dict."""
    jadval(cur)
    yig = {}
    for h in hodisalar[:200]:
        h = h if isinstance(h, dict) else h.model_dump()
        k = aniqla(h.get("savol", ""), h.get("tur", ""), h.get("korinish", ""), h.get("manba", ""))
        a = yig.setdefault(k, [0, 0]); a[0] += 1 if h.get("togri") else 0; a[1] += 1
        s, c = h.get("soniya"), h.get("chegara")
        if s is not None and c:   # tezlik: to'g'ri va vaqtning yarmidan tez
            t = yig.setdefault("tezlik", [0, 0]); t[1] += 1; t[0] += 1 if (h.get("togri") and float(s) <= float(c) / 2) else 0
    for k, (tg, jm) in yig.items():
        cur.execute("""INSERT INTO konikma_holat(user_id, konikma, togri, jami) VALUES(%s,%s,%s,%s)
                       ON CONFLICT (user_id, konikma) DO UPDATE SET togri=konikma_holat.togri+EXCLUDED.togri,
                       jami=konikma_holat.jami+EXCLUDED.jami, yangilandi=NOW()""", (uid, k, tg, jm))
    return yig


def korinish(rows):
    d = {r["konikma"]: r for r in rows}
    return [{"kalit": k, "nom": n, "togri": int((d.get(k) or {}).get("togri") or 0), "jami": int((d.get(k) or {}).get("jami") or 0),
             "foiz": round(100 * d[k]["togri"] / d[k]["jami"]) if d.get(k) and d[k]["jami"] else None} for k, n in KONIKMALAR.items()]


def create_router(platform):
    router = APIRouter(tags=["konikma"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            jadval(cur); r = fn(cur); conn.commit(); return r
        finally:
            cur.close(); conn.close()

    @router.post("/api/konikma/yoz")
    def yozish(body: Yozuv, token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        return run(lambda cur: {"ok": True, "yozildi": {k: v[1] for k, v in yoz(cur, u, body.hodisalar).items()}})

    @router.get("/api/konikma")
    def meniki(token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        def f(cur):
            cur.execute("SELECT konikma, togri, jami FROM konikma_holat WHERE user_id=%s", (u,))
            return {"konikmalar": korinish(cur.fetchall())}
        return run(f)

    @router.get("/api/konikma/guruh")
    def guruh(guruh: int, token: str = "", authorization: Optional[str] = Header(None)):
        """O'qituvchi: guruh o'quvchilarining ko'nikmalari (faqat guruh egasi yoki admin)."""
        u = uid(token, authorization)
        def f(cur):
            cur.execute("SELECT egasi FROM kurs_guruh WHERE id=%s", (guruh,))
            g = cur.fetchone()
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (u,)); adm = cur.fetchone() is not None
            if not g or (g["egasi"] != u and not adm):
                raise HTTPException(403, "Bu guruh sizniki emas")
            cur.execute("""SELECT a.user_id, COALESCE(NULLIF(us.full_name,''),'O‘quvchi') AS ism FROM kurs_guruh_azo a JOIN users us ON us.user_id=a.user_id
                           WHERE a.guruh_id=%s ORDER BY 2""", (guruh,))
            oq = cur.fetchall()
            ids = [r["user_id"] for r in oq]
            cur.execute("SELECT user_id, konikma, togri, jami FROM konikma_holat WHERE user_id = ANY(%s)", (ids or [0],))
            bor = {}
            for r in cur.fetchall():
                bor.setdefault(r["user_id"], []).append(r)
            sinf = {}
            for rr in bor.values():
                for r in rr:
                    a = sinf.setdefault(r["konikma"], {"konikma": r["konikma"], "togri": 0, "jami": 0}); a["togri"] += r["togri"]; a["jami"] += r["jami"]
            return {"sinf": korinish(list(sinf.values())), "oquvchilar": [{"ism": r["ism"], "konikmalar": korinish(bor.get(r["user_id"], []))} for r in oq]}
        return run(f)

    return router

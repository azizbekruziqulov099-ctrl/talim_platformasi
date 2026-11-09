"""REV445: bazani yengillashtirish (bir martalik, xavfsiz qadamlar). Endpoint: /api/admin/baza_xizmat
  bajar=0 — faqat hisobot: indekslar hajmi, arxivlangan Miya qatorlari, sozlamalar (hech narsa o'zgarmaydi).
  bajar=1 — 1) keraksiz/takror indekslarni CONCURRENTLY o'chiradi (sayt ishlayveradi);
            2) arxivlangan (hech qayerda ko'rinmaydigan) Miya qatorlarini 2000 tadan o'chiradi;
            3) oddiy VACUUM ANALYZE (FULL emas — jurnal kam yoziladi);
            4) shared_buffers 256 MB, effective_cache_size 768 MB (ALTER SYSTEM — baza qayta ishga tushganda kuchga kiradi).
Kirish: admin token yoki vaqtinchalik DIAG_KALIT (X-Diag-Kalit)."""
import os, secrets, threading
from datetime import datetime
from fastapi import APIRouter, Request

KERAKSIZ_INDEKSLAR = [
    ("idx_ai_brain_units_payload_gin", "payload bo'yicha GIN — kodda ishlatilmaydi, har yozishda eng ko'p jurnal yaratadi"),
    ("idx_ai_brain_units_kitob_kodi", "idx_abu_kitob_kodi bilan bir xil (takror)"),
    ("idx_ai_brain_units_age", "hech qachon ishlatilmagan"),
    ("idx_ai_brain_topic_maps_topic", "hech qachon ishlatilmagan"),
]
_HOLAT = {"holat": "yo'q", "qadam": "", "jurnal": [], "boshlandi": None, "tugadi": None}


def create_router(admin_tekshir, db_url_ol, psycopg2):
    router = APIRouter()

    def _ruxsat(request, token):
        diag = os.getenv("DIAG_KALIT", "")
        if len(diag) >= 24 and secrets.compare_digest(request.headers.get("x-diag-kalit", ""), diag):
            return
        admin_tekshir(token)

    def _ulan():
        c = psycopg2.connect(db_url_ol(), connect_timeout=10, application_name="samtm-baza-xizmat")
        c.autocommit = True
        k = c.cursor()
        k.execute("SET statement_timeout = 0"); k.execute("SET lock_timeout = '20s'")
        return c, k

    def hisobot():
        c, k = _ulan()
        try:
            k.execute("""SELECT c.relname, pg_size_pretty(pg_relation_size(c.oid)) h, pg_relation_size(c.oid) b, s.idx_scan
                         FROM pg_class c JOIN pg_index i ON i.indexrelid=c.oid JOIN pg_class t ON t.oid=i.indrelid
                         LEFT JOIN pg_stat_user_indexes s ON s.indexrelid=c.oid
                         WHERE t.relname IN ('ai_brain_units','ai_brain_topic_maps','dts_tree') ORDER BY pg_relation_size(c.oid) DESC""")
            indeks = [{"nom": r[0], "hajm": r[1], "bayt": r[2], "ishlatilgan": r[3], "ochiriladi": any(r[0] == n for n, _ in KERAKSIZ_INDEKSLAR)} for r in k.fetchall()]
            k.execute("SELECT COUNT(*) FROM ai_brain_units WHERE status='archived'")
            arxiv = k.fetchone()[0]
            k.execute("SELECT name, setting FROM pg_settings WHERE name IN ('shared_buffers','effective_cache_size')")
            sozlama = dict(k.fetchall())
            k.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
            hajm = k.fetchone()[0]
            return {"baza": hajm, "indekslar": indeks, "arxivlangan_miya_qatorlari": arxiv, "sozlamalar": sozlama,
                    "tejaladi_indeks": sum(x["bayt"] for x in indeks if x["ochiriladi"])}
        finally:
            c.close()

    def _ish():
        jurnal = _HOLAT["jurnal"]
        def yoz(m): jurnal.append(f"{datetime.now().strftime('%H:%M:%S')} {m}")
        _HOLAT.update(holat="ishlamoqda", boshlandi=datetime.now().isoformat(timespec="seconds"), tugadi=None)
        try:
            c, k = _ulan()
            _HOLAT["qadam"] = "indekslar"
            for nom, sabab in KERAKSIZ_INDEKSLAR:
                try:
                    k.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {nom}"); yoz(f"indeks o'chirildi: {nom} — {sabab}")
                except Exception as e:
                    yoz(f"indeks {nom}: {str(e)[:120]}")
            _HOLAT["qadam"] = "arxiv"
            jami = 0
            for _ in range(500):
                k.execute("DELETE FROM ai_brain_units WHERE id IN (SELECT id FROM ai_brain_units WHERE status='archived' LIMIT 2000)")
                n = k.rowcount or 0; jami += n
                if n < 2000:
                    break
            yoz(f"arxivlangan Miya qatorlari o'chirildi: {jami}")
            _HOLAT["qadam"] = "vacuum"
            for j in ("ai_brain_units", "ai_brain_topic_maps", "dts_tree", "generated_tests"):
                try:
                    k.execute(f"VACUUM (ANALYZE) {j}"); yoz(f"VACUUM ANALYZE {j}")
                except Exception as e:
                    yoz(f"vacuum {j}: {str(e)[:120]}")
            _HOLAT["qadam"] = "sozlamalar"
            for s in ("ALTER SYSTEM SET shared_buffers = '256MB'", "ALTER SYSTEM SET effective_cache_size = '768MB'", "SELECT pg_reload_conf()"):
                try:
                    k.execute(s); yoz(s)
                except Exception as e:
                    yoz(f"{s}: {str(e)[:120]}")
            c.close()
            _HOLAT.update(holat="tugadi", qadam="", tugadi=datetime.now().isoformat(timespec="seconds"))
        except Exception as e:
            _HOLAT.update(holat="xato", qadam=str(e)[:200])

    @router.get("/api/admin/baza_xizmat")
    def baza_xizmat(request: Request, token: str = "", bajar: int = 0):
        _ruxsat(request, token)
        if bajar and _HOLAT["holat"] != "ishlamoqda":
            _HOLAT["jurnal"] = []
            threading.Thread(target=_ish, daemon=True, name="rev445-baza-xizmat").start()
            return {"boshlandi": True, **{k: v for k, v in _HOLAT.items()}}
        out = {k: v for k, v in _HOLAT.items()}
        try:
            out["hisobot"] = hisobot()
        except Exception as e:
            out["hisobot"] = {"xato": str(e)[:200]}
        return out

    return router

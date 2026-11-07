"""REV301: «Kurslar» — platformaning barcha darsli kurslari bitta katalogda va umumiy narxlar.

Kurs = fan + sinf (maktab: «Matematika · 5-sinf», «Ingliz tili · 7-sinf»), erkin til darajasi («… · A1»),
bolalar kursi (yoshga bo'linmaydi: 2–3 → 4–5 → 6–7 qismlari bitta kurs). Izoh tili (uz/ru/en) — bitta kursning
turli nusxasi: bir marta to'lansa uchala tilda ochiq.
Kirish qoidasi: kursning birinchi N darsi (odatiy 5) bepul; qolgani — obuna bilan. Narx belgilanmagan (0) kurs bepul.
Admin va o'qituvchi uchun cheklov yo'q; bog'cha obunasi bor bola uchun bolalar kurslari ochiq."""
import json
import re
from datetime import date, timedelta

from fastapi import APIRouter, Body, HTTPException

IZOH = re.compile(r"\s*\((izoh|изоҳ): (rus|ingliz|nemis|ispan)\)\s*$", re.I)   # REV315: 5 til
TIL_FANLAR = re.compile(r"(ingliz|rus|fransuz|nemis|ispan|arab|turk|koreys|xitoy|yapon) tili", re.I)
FAN_FANLAR = re.compile(r"matem|algebra|geometr", re.I)
KATEGORIYALAR = [
    ("fanlar", "📐", "Fanlar", "Maktab dasturi: matematika, algebra, geometriya (1–11-sinf)"),
    ("tillar", "🗣", "Tillar", "Maktab dasturi bo‘yicha chet tillari (1–11-sinf)"),
    ("erkin", "💬", "Erkin til", "Ko‘chada gaplashish: hayotiy vaziyatlar, A1 dan boshlab"),
    ("sertifikat", "🎓", "Sertifikat", "Milliy sertifikat sinovlari, strategiyalar, daraja testi"),
    ("xalqaro", "🌍", "Xalqaro baholash", "TIMSS / PISA uslubidagi kurs va imtihonlar"),
    ("repetitor", "🎯", "Repetitor kurslari", "Maktab matematikasi sinflar bo‘yicha guruhlangan: matematika 1–4 va 5–7, algebra va geometriya 7–11"),   # REV419/REV421: faqat matematika
    ("markaz", "🏫", "O‘quv markazi", "Matematika kitoblari asosida: savol-javobli, chizmali darslar va testlar"),   # REV405
    ("oliy", "🎓", "Oliy ta’lim kurslari", "Ma’ruza va amaliy mashg‘ulotlar: talabalar va qiziqqan o‘quvchilar uchun"),   # REV407
    ("bolalar", "🧒", "Bolalar uchun", "Til va fan kurslari — boshidan, o‘yin bilan"),
    ("boshqa", "📚", "Boshqa kurslar", "Boshqa darsli kurslar"),
]
ODATIY_BEPUL = 5


def asos_fan(fan):
    return IZOH.sub("", str(fan or "")).strip()


def izoh_tili(fan):
    m = IZOH.search(str(fan or ""))
    return {"rus": "ru", "ingliz": "en", "nemis": "de", "ispan": "es"}.get(m.group(2).lower(), "uz") if m else "uz"


def yosh_tartib(grade):
    m = re.search(r"\d+", str(grade or ""))
    return int(m.group()) if m else 99


FAN_OZ_TILI = ((re.compile(r"^(ingliz|english|англ)", re.I), "en"), (re.compile(r"^(rus\b|russian|русск)", re.I), "ru"),
               (re.compile(r"^(nemis|german|deutsch|немец)", re.I), "de"), (re.compile(r"^(ispan|spanish|español|испан)", re.I), "es"))


def oz_tilida(fan):
    """REV321: til fani o'z tilida izohli — «Ingliz tili (izoh: ingliz)», «Rus tili (izoh: rus)» — mantiqsiz, katalogda ko'rsatilmaydi."""
    base = IZOH.sub("", str(fan or "")).strip()
    t = next((k for re_, k in FAN_OZ_TILI if re_.search(base)), None)
    return bool(t) and izoh_tili(fan) == t


# REV419: repetitor kurslari — fanga qarab sinflar guruhi (qolgan fanlar — odatiy guruhlar)
ODATIY_GURUHLAR = ((1, 2), (3, 4), (5, 7), (8, 9), (10, 11))
FAN_GURUHLARI = {"matematika": ((1, 4), (5, 7)), "algebra": ((7, 11),), "geometriya": ((7, 11),)}


def repetitor_guruhlari(fan):
    return FAN_GURUHLARI.get(asos_fan(fan).casefold(), ODATIY_GURUHLAR)


REPETITOR_FANLAR = set(FAN_GURUHLARI)   # REV421: repetitor kurslari — faqat matematika (matematika, algebra, geometriya)


def repetitor_guruhi(fan, sinf):
    """Shu fan va sinf qaysi repetitor kursiga tushadi: «5-7» yoki None (matematikadan boshqa fanlar — yo'q)."""
    if asos_fan(fan).casefold() not in REPETITOR_FANLAR:
        return None
    try:
        n = int(str(sinf).strip())
    except (TypeError, ValueError):
        return None
    for a, b in repetitor_guruhlari(fan):
        if a <= n <= b:
            return f"{a}-{b}"
    return None


def kurs_of(fan, grade):
    """(kalit, kategoriya, nomi, guruh) — guruh: shu kurs darslari tartiblanadigan sinf(lar) to'plami kaliti."""
    base, g = asos_fan(fan), str(grade or "").strip()
    if re.search(r"yosh", g, re.I):
        return f"bolalar|{base}", "bolalar", base, "bolalar"
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})", g)
    if m:   # REV419: repetitor kursi — bir nechta sinf bitta kursda
        return f"repetitor|{base}|{g}", "repetitor", f"{base} · {m.group(1)}–{m.group(2)}-sinf", g
    if re.search(r"erkin til", base, re.I):
        return f"erkin|{base}|{g}", "erkin", f"{base} · {g}", g
    if re.search(r"\bmarkaz\b|o.quv markazi", base, re.I):   # REV405: «Matematika — markaz · 1-kitob»
        return f"markaz|{base}|{g}", "markaz", f"{base} · {g}", g
    if re.search(r"\bkurs\b|magistr", g, re.I):   # REV407: «2 kurs» — oliy ta'lim kursi (ma'ruza + amaliy)
        return f"oliy|{base}|{g}", "oliy", base, g
    if re.fullmatch(r"\d{1,2}", g):
        kat = "tillar" if TIL_FANLAR.search(base) else "fanlar" if FAN_FANLAR.search(base) else "boshqa"
        return f"maktab|{base}|{g}", kat, f"{base} · {g}-sinf", g
    return f"boshqa|{base}|{g}", "boshqa", f"{base} · {g}" if g else base, g


def qaror(rol, narx, bepul, indeks, obuna_bor, bogcha_obuna=False, kategoriya=""):
    """Sof qoida (testlanadi): (ochiqmi, sabab)."""
    if rol in ("admin", "oqituvchi"):
        return True, "xodim"
    if not narx or narx <= 0:
        return True, "bepul_kurs"
    if indeks is not None and indeks < max(0, int(bepul)):
        return True, "bepul_dars"
    if obuna_bor:
        return True, "obuna"
    if kategoriya == "bolalar" and bogcha_obuna:
        return True, "bogcha_obuna"
    return False, "tolov_kerak"


_MIGRATSIYA = {"ok": False}
_KESH = {}   # REV309: qisqa muddatli kesh — {kalit: (vaqt, qiymat)}


def _kesh(kalit, ttl, fn):
    import time as _t
    hozir = _t.time()
    v = _KESH.get(kalit)
    if v and hozir - v[0] < ttl:
        return v[1]
    q = fn()
    if len(_KESH) > 2000:
        _KESH.clear()
    _KESH[kalit] = (hozir, q)
    return q


def kesh_tozala():
    _KESH.clear()


def migrate(cur):
    """Jadvallar — jarayon boshida bir marta (har so'rovda DDL yo'q: band paytda qulf va sekinlik bermasin)."""
    if _MIGRATSIYA["ok"]:
        return
    _migrate(cur)
    _MIGRATSIYA["ok"] = True


def _migrate(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_narx (kalit TEXT PRIMARY KEY, narx_uzs BIGINT NOT NULL DEFAULT 0,
        bepul_dars INT, faol BOOLEAN NOT NULL DEFAULT TRUE, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_kategoriya_narx (kategoriya TEXT PRIMARY KEY, narx_uzs BIGINT NOT NULL DEFAULT 0,
        bepul_dars INT NOT NULL DEFAULT 5, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_obuna (user_id BIGINT NOT NULL, kalit TEXT NOT NULL, tugaydi DATE NOT NULL,
        manba TEXT NOT NULL DEFAULT '', yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, kalit))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS kurs_tolov (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, kalit TEXT NOT NULL,
        summa_uzs BIGINT NOT NULL DEFAULT 0, kun INT NOT NULL DEFAULT 30, manba TEXT NOT NULL DEFAULT '', kod TEXT NOT NULL DEFAULT '',
        vaqt TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS kurs_tolov_kod ON kurs_tolov(kod) WHERE kod <> ''")
    cur.execute("CREATE INDEX IF NOT EXISTS kurs_obuna_faol ON kurs_obuna(user_id, tugaydi)")


def _narx_jadvali(cur):
    def ol():
        cur.execute("SELECT kalit, narx_uzs, bepul_dars, faol FROM kurs_narx")
        ku = {r["kalit"]: dict(r) for r in cur.fetchall()}
        cur.execute("SELECT kategoriya, narx_uzs, bepul_dars FROM kurs_kategoriya_narx")
        return ku, {r["kategoriya"]: dict(r) for r in cur.fetchall()}
    return _kesh("narxlar", 30, ol)


def narx_ol(cur, kalit, kategoriya):
    """Kurs narxi va bepul darslar soni (narxlar jadvali 30 s keshda — katalogda yuzlab so'rov o'rniga bitta)."""
    ku, kn = _narx_jadvali(cur)
    k, c = ku.get(kalit), kn.get(kategoriya)
    narx = int(k["narx_uzs"]) if k and int(k["narx_uzs"] or 0) > 0 else int(c["narx_uzs"]) if c else 0
    bepul = k["bepul_dars"] if k and k["bepul_dars"] is not None else (int(c["bepul_dars"]) if c else ODATIY_BEPUL)
    if k and k["faol"] is False:
        narx = 0
    return narx, int(bepul)


def obuna_tolandi(cur, data, kod, summa, manba):
    """To'lov tasdiqlandi → kurs obunasi (mavjud bo'lsa — uning oxiridan) N kunga uzayadi. Bir kod — bir marta."""
    migrate(cur)
    uid, kalit, kun = int(data["user_id"]), str(data["kalit"]), int(data.get("kun") or 30)
    if kod:
        cur.execute("SELECT 1 FROM kurs_tolov WHERE kod=%s", (kod,))
        if cur.fetchone():
            return
    cur.execute("SELECT tugaydi FROM kurs_obuna WHERE user_id=%s AND kalit=%s FOR UPDATE", (uid, kalit))
    r = cur.fetchone()
    bosh = max(date.today(), r["tugaydi"] + timedelta(days=1)) if r else date.today()
    tug = bosh + timedelta(days=kun - 1)
    cur.execute("""INSERT INTO kurs_obuna(user_id,kalit,tugaydi,manba) VALUES(%s,%s,%s,%s)
                   ON CONFLICT (user_id,kalit) DO UPDATE SET tugaydi=EXCLUDED.tugaydi, manba=EXCLUDED.manba, yangilandi=NOW()""",
                (uid, kalit, tug, manba))
    cur.execute("INSERT INTO kurs_tolov(user_id,kalit,summa_uzs,kun,manba,kod) VALUES(%s,%s,%s,%s,%s,%s)",
                (uid, kalit, int(summa), kun, manba, kod or ""))


def _rol(cur, uid):
    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
    if cur.fetchone():
        return "admin"
    cur.execute("SELECT role FROM users WHERE user_id=%s", (uid,))
    r = cur.fetchone()
    return str((r or {}).get("role") or "")


def _bogcha_obuna(cur, uid):
    try:
        cur.execute("SAVEPOINT kurs_bogcha")
        cur.execute("SELECT 1 FROM bogcha_obuna WHERE bola_id=%s AND tugaydi >= CURRENT_DATE", (uid,))
        ok = bool(cur.fetchone())
        cur.execute("RELEASE SAVEPOINT kurs_bogcha")
        return ok
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT kurs_bogcha")
        return False


def kurs_darslari(cur, fan, grade):
    """Shu kurs nusxasining darsli mavzulari (5 daqiqalik kesh — har dars ochilishida og'ir so'rov bo'lmasin)."""
    return _kesh(("darslar", fan, str(grade or "").strip()), 300, lambda: _kurs_darslari(cur, fan, grade))


def _kurs_darslari(cur, fan, grade):
    _, kat, _, _ = kurs_of(fan, grade)
    if kat == "bolalar":
        cur.execute("""SELECT d.topic_code, d.grade, MIN(COALESCE(NULLIF(d.kichik_name,''),NULLIF(d.mavzu_name,''),d.bob_name)) AS nom
                       FROM dts_tree d WHERE d.is_deleted=FALSE AND d.subject_name=%s AND d.grade ILIKE '%%yosh%%'
                         AND EXISTS(SELECT 1 FROM ai_brain_units u WHERE u.topic_code=d.topic_code AND u.status='published')
                       GROUP BY d.topic_code, d.grade""", (fan,))
        rows = sorted(cur.fetchall(), key=lambda r: (yosh_tartib(r["grade"]), r["topic_code"]))
    elif kat == "repetitor":   # REV419: sinflar ketma-ket (1-sinf mavzulari, keyin 2-sinf ...)
        a, b = (int(x) for x in str(grade).split("-"))
        cur.execute("""SELECT d.topic_code, d.grade, MIN(COALESCE(NULLIF(d.kichik_name,''),NULLIF(d.mavzu_name,''),d.bob_name)) AS nom
                       FROM dts_tree d WHERE d.is_deleted=FALSE AND d.subject_name=%s AND TRIM(d.grade) = ANY(%s)
                         AND EXISTS(SELECT 1 FROM ai_brain_units u WHERE u.topic_code=d.topic_code AND u.status='published')
                       GROUP BY d.topic_code, d.grade""", (fan, [str(i) for i in range(a, b + 1)]))
        rows = sorted(cur.fetchall(), key=lambda r: (int(str(r["grade"]).strip()) if str(r["grade"]).strip().isdigit() else 99, r["topic_code"]))
    else:
        cur.execute("""SELECT d.topic_code, d.grade, MIN(COALESCE(NULLIF(d.kichik_name,''),NULLIF(d.mavzu_name,''),d.bob_name)) AS nom
                       FROM dts_tree d WHERE d.is_deleted=FALSE AND d.subject_name=%s AND TRIM(d.grade)=%s
                         AND EXISTS(SELECT 1 FROM ai_brain_units u WHERE u.topic_code=d.topic_code AND u.status='published')
                       GROUP BY d.topic_code, d.grade ORDER BY d.topic_code""", (fan, str(grade or "").strip()))
        rows = list(cur.fetchall())
    return [dict(r) for r in rows]


def ruxsat(cur, uid, topic_code):
    """Darsga kirish: {ochiq, sabab, kalit, nomi, narx, bepul, indeks}. Kurs topilmasa — ochiq (eski xatti-harakat)."""
    migrate(cur)
    cur.execute("SELECT subject_name, grade FROM dts_tree WHERE topic_code=%s AND is_deleted=FALSE LIMIT 1", (topic_code,))
    r = cur.fetchone()
    if not r:
        return {"ochiq": True, "sabab": "kurs_yoq"}
    kalit, kat, nomi, _ = kurs_of(r["subject_name"], r["grade"])
    narx, bepul = narx_ol(cur, kalit, kat)
    rol = _rol(cur, uid)
    royxat = [x["topic_code"] for x in kurs_darslari(cur, r["subject_name"], r["grade"])] if narx > 0 and rol not in ("admin", "oqituvchi") else []
    indeks = royxat.index(topic_code) if topic_code in royxat else None
    cur.execute("SELECT 1 FROM kurs_obuna WHERE user_id=%s AND kalit=%s AND tugaydi >= CURRENT_DATE", (uid, kalit))
    obuna = bool(cur.fetchone())
    ok, sabab = qaror(rol, narx, bepul, indeks, obuna, _bogcha_obuna(cur, uid) if kat == "bolalar" else False, kat)
    return {"ochiq": ok, "sabab": sabab, "kalit": kalit, "kategoriya": kat, "nomi": nomi, "narx": narx, "bepul": bepul, "indeks": indeks}


_TAYYOR = {"ok": False}


def create_router(platform, click=None):
    router = APIRouter(tags=["kurslar"])

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            if not _TAYYOR["ok"]:   # REV414: jadvallar har so'rovda emas, jarayon boshida bir marta tekshiriladi
                migrate(cur); conn.commit(); _TAYYOR["ok"] = True
            out = fn(cur); conn.commit(); return out
        except Exception:
            conn.rollback(); raise
        finally:
            cur.close(); conn.close()

    def _izoh_tanla(variantlar, til):
        """Bir kursning nusxalari (uz/ru/en) — o'quvchi tiliga mosi, bo'lmasa o'zbekchasi, bo'lmasa birinchisi."""
        for t in (til, "uz"):
            for v in variantlar:
                if izoh_tili(v["fan"]) == t:
                    return v
        return variantlar[0]

    @router.get("/api/kurslar/katalog")
    def katalog(token: str, til: str = "uz"):
        uid = platform._jwt_tekshir(token)
        def go(cur):
            def qatorlar():
                cur.execute("""SELECT d.subject_name AS fan, TRIM(d.grade) AS grade, COUNT(DISTINCT d.topic_code) AS darslar
                               FROM dts_tree d WHERE d.is_deleted=FALSE
                                 AND EXISTS(SELECT 1 FROM ai_brain_units u WHERE u.topic_code=d.topic_code AND u.status='published')
                               GROUP BY 1,2""")
                return [dict(r) for r in cur.fetchall()]
            kurslar = {}
            for r in _kesh("katalog_qatorlar", 120, qatorlar):   # REV309: hamma uchun bir xil — 2 daqiqa kesh
                if oz_tilida(r["fan"]):
                    continue
                kalit, kat, nomi, _ = kurs_of(r["fan"], r["grade"])
                k = kurslar.setdefault(kalit, {"kalit": kalit, "kategoriya": kat, "nomi": nomi, "variantlar": []})
                k["variantlar"].append({"fan": r["fan"], "grade": r["grade"], "darslar": int(r["darslar"])})
                if kalit.startswith("maktab|"):   # REV419: maktab sinfi (fanlar, tillar)
                    gr = repetitor_guruhi(r["fan"], r["grade"])
                    if gr:
                        k2, kat2, nomi2, _ = kurs_of(r["fan"], gr)
                        rk = kurslar.setdefault(k2, {"kalit": k2, "kategoriya": kat2, "nomi": nomi2, "variantlar": [], "_rep": {}})
                        rk["_rep"][r["fan"]] = rk["_rep"].get(r["fan"], 0) + int(r["darslar"])
            cur.execute("SELECT kalit FROM kurs_obuna WHERE user_id=%s AND tugaydi >= CURRENT_DATE", (uid,))
            obunalar = {x["kalit"] for x in cur.fetchall()}
            out = []
            for k in kurslar.values():
                if "_rep" in k:   # REV419: repetitor — sinflar yig'indisi bitta variant bo'ladi
                    g = k["kalit"].rsplit("|", 1)[-1]
                    k["variantlar"] = [{"fan": f, "grade": g, "darslar": n} for f, n in k["_rep"].items()]
                tanlangan = [v for v in k["variantlar"] if izoh_tili(v["fan"]) == izoh_tili(_izoh_tanla(k["variantlar"], til)["fan"])]
                narx, bepul = narx_ol(cur, k["kalit"], k["kategoriya"])
                out.append({"kalit": k["kalit"], "kategoriya": k["kategoriya"], "nomi": k["nomi"],
                            "fan": tanlangan[0]["fan"], "sinflar": sorted({v["grade"] for v in tanlangan}, key=yosh_tartib),
                            "darslar": sum(v["darslar"] for v in tanlangan), "tillar": sorted({izoh_tili(v["fan"]) for v in k["variantlar"]}),
                            "narx": narx, "bepul": bepul, "obuna": k["kalit"] in obunalar})
            def tartib(x):
                m = re.search(r"\|(\d+)$", x["kalit"])
                return ([c[0] for c in KATEGORIYALAR].index(x["kategoriya"]), asos_fan(x["fan"]).casefold(), int(m.group(1)) if m else 0, x["nomi"])
            out.sort(key=tartib)
            return {"kategoriyalar": [{"kalit": c[0], "belgi": c[1], "nomi": c[2], "izoh": c[3]} for c in KATEGORIYALAR], "kurslar": out}
        return run(go)

    @router.get("/api/kurslar/kurs")
    def kurs(token: str, fan: str, grade: str = ""):
        uid = platform._jwt_tekshir(token)
        def go(cur):
            kalit, kat, nomi, _ = kurs_of(fan, grade)
            darslar = kurs_darslari(cur, fan, grade) if kat != "bolalar" else kurs_darslari(cur, fan, "yosh")
            narx, bepul = narx_ol(cur, kalit, kat)
            rol = _rol(cur, uid)
            cur.execute("SELECT tugaydi FROM kurs_obuna WHERE user_id=%s AND kalit=%s AND tugaydi >= CURRENT_DATE", (uid, kalit))
            ob = cur.fetchone()
            bog = _bogcha_obuna(cur, uid) if kat == "bolalar" else False
            items = []
            for i, d in enumerate(darslar):
                ok, sabab = qaror(rol, narx, bepul, i, bool(ob), bog, kat)
                items.append({"topic_code": d["topic_code"], "nomi": d["nom"], "sinf": d["grade"], "ochiq": ok, "bepul": sabab in ("bepul_dars", "bepul_kurs")})
            return {"kalit": kalit, "kategoriya": kat, "nomi": nomi, "narx": narx, "bepul": bepul,
                    "obuna_tugaydi": ob["tugaydi"].isoformat() if ob else None, "darslar": items}
        return run(go)

    @router.post("/api/kurslar/buyurtma")
    def buyurtma(body: dict = Body(...)):
        uid = platform._jwt_tekshir(str(body.get("token") or ""))
        kalit = str(body.get("kalit") or "")[:200]
        def go(cur):
            parts = kalit.split("|")
            if len(parts) < 2:
                raise HTTPException(400, "Kurs topilmadi")
            # kalitdan kategoriya (kurs_of bilan bir xil qoida)
            if parts[0] == "bolalar":
                kat = "bolalar"
            elif parts[0] in ("maktab", "erkin", "boshqa", "repetitor", "markaz", "oliy") and len(parts) >= 3:
                k2, kat, _, _ = kurs_of(parts[1], parts[2])
                if k2 != kalit:
                    kat = None
            else:
                kat = None
            if not kat:
                raise HTTPException(404, "Kurs topilmadi")
            narx, _ = narx_ol(cur, kalit, kat)
            if narx <= 0:
                raise HTTPException(400, "Bu kurs bepul")
            klik = click
            data = {"tur": "kurs", "user_id": uid, "bola_id": uid, "kalit": kalit, "fanlar": [kalit], "kun": 30}
            yoq = {"kod": "tolov_yoq", "xabar": "Onlayn to‘lov hali ulanmagan. To‘lov uchun admin bilan bog‘laning — admin kursni ochib beradi."}
            if klik is None:
                raise HTTPException(503, yoq)
            try:
                return klik.obuna_buyurtma(cur, uid, narx, data, str(body.get("return_url") or ""))
            except HTTPException as e:
                if e.status_code == 503:
                    raise HTTPException(503, yoq)
                raise
        return run(go)

    # — Admin: narxlar va qo'lda ochish —
    @router.get("/api/admin/kurslar/narxlar")
    def admin_narxlar(token: str):
        platform._admin_tekshir(token)
        def go(cur):
            cur.execute("SELECT * FROM kurs_kategoriya_narx"); kn = {r["kategoriya"]: dict(r) for r in cur.fetchall()}
            cur.execute("SELECT * FROM kurs_narx"); ku = {r["kalit"]: dict(r) for r in cur.fetchall()}
            cur.execute("SELECT kalit, COUNT(*) AS n FROM kurs_obuna WHERE tugaydi >= CURRENT_DATE GROUP BY kalit"); faol = {r["kalit"]: int(r["n"]) for r in cur.fetchall()}
            return {"kategoriyalar": [{"kalit": c[0], "belgi": c[1], "nomi": c[2], "narx": int((kn.get(c[0]) or {}).get("narx_uzs") or 0),
                                       "bepul_dars": int((kn.get(c[0]) or {}).get("bepul_dars") or ODATIY_BEPUL)} for c in KATEGORIYALAR],
                    "kurs_narx": {k: {"narx": int(v["narx_uzs"] or 0), "bepul_dars": v["bepul_dars"], "faol": v["faol"]} for k, v in ku.items()},
                    "faol_obunalar": faol}
        return run(go)

    @router.put("/api/admin/kurslar/narx")
    def admin_narx(body: dict = Body(...)):
        platform._admin_tekshir(str(body.get("token") or ""))
        def go(cur):
            narx = max(0, int(body.get("narx") or 0)); bep = body.get("bepul_dars")
            bep = None if bep in (None, "") else max(0, min(50, int(bep)))
            if body.get("kategoriya"):
                cur.execute("""INSERT INTO kurs_kategoriya_narx(kategoriya,narx_uzs,bepul_dars) VALUES(%s,%s,%s)
                               ON CONFLICT (kategoriya) DO UPDATE SET narx_uzs=EXCLUDED.narx_uzs, bepul_dars=EXCLUDED.bepul_dars, yangilandi=NOW()""",
                            (str(body["kategoriya"])[:40], narx, ODATIY_BEPUL if bep is None else bep))
            elif body.get("kalit"):
                cur.execute("""INSERT INTO kurs_narx(kalit,narx_uzs,bepul_dars,faol) VALUES(%s,%s,%s,%s)
                               ON CONFLICT (kalit) DO UPDATE SET narx_uzs=EXCLUDED.narx_uzs, bepul_dars=EXCLUDED.bepul_dars, faol=EXCLUDED.faol, yangilandi=NOW()""",
                            (str(body["kalit"])[:200], narx, bep, body.get("faol") is not False))
            else:
                raise HTTPException(400, "kategoriya yoki kalit kerak")
            kesh_tozala()
            return {"ok": True}
        return run(go)

    @router.post("/api/admin/kurslar/ochib_ber")
    def admin_ochib_ber(body: dict = Body(...)):
        """Naqd yoki kartaga to'lov qilganga — admin kursni qo'lda ochadi (kun bo'yicha)."""
        platform._admin_tekshir(str(body.get("token") or ""))
        def go(cur):
            kim = str(body.get("foydalanuvchi") or "").strip()
            cur.execute("""SELECT user_id FROM users WHERE CAST(user_id AS TEXT)=%s OR LOWER(TRIM(full_name))=LOWER(%s) LIMIT 2""", (kim, kim))
            rows = cur.fetchall()
            if len(rows) != 1:
                raise HTTPException(404, "Foydalanuvchi topilmadi yoki bir nechta — ID raqamini yozing")
            kun = max(1, min(400, int(body.get("kun") or 30)))
            obuna_tolandi(cur, {"user_id": rows[0]["user_id"], "kalit": str(body.get("kalit") or ""), "kun": kun}, "", int(body.get("summa") or 0), "admin")
            return {"ok": True, "user_id": rows[0]["user_id"]}
        return run(go)

    return router

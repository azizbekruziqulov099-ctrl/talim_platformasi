"""Dars xonasi: nashr qilingan «AI miya» kontentidan doskadagi darsni yig'adi.

Manba tartibi:
  1) 11_DARS_SSENARIY + 12_TUSHUNMADIM (o'qituvchi yozgan tayyor dars);
  2) ular bo'lmasa — 03_BILIM, 04_TUSHUNTIRISH, 05_MISOLLAR, 07_YORDAM_XATOLAR
     dan avtomatik yig'ilgan dars.
Savollar: 06_MASHQLAR (single_choice), yetmasa shu mavzuning Test bazasi.
Faqat status='published' kontent o'qiladi.
"""
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

STEP_TYPES = ("kirish", "tushuntirish", "qoida", "misol", "birga", "mashq", "xulosa", "amaliy")
PRACTICE_NAMES = {"misol": "Misol", "masala": "Masala", "topshiriq": "Topshiriq", "test": "Test"}
VARIANT_NAMES = {
    "sodda": "Soddaroq",
    "hikoya": "Hikoya orqali",
    "rasm": "Rasm bilan",
    "boshqa_usul": "Boshqa usulda",
    "takrorlash": "Oldingi mavzu",
}
MAX_STEPS = 60
MAX_QUESTIONS = 5


def _t(value):
    return str(value or "").strip()


def filled_options(options):
    """REV80: 2–4 variant (bog'cha testida 2–3 ta). Bo'sh variantlar faqat oxirida bo'lishi mumkin."""
    count = sum(1 for o in options if o)
    if count < 2 or any(not o for o in options[:count]):
        return []
    return options[:count]


def _int(value, default=None):
    try:
        return int(float(_t(value)))
    except (TypeError, ValueError):
        return default


def _split_solution(text):
    """«1) ... 2) ...» yoki satrlar bo'yicha yechim qadamlarini ajratadi."""
    text = _t(text)
    if not text:
        return []
    parts = [p.strip(" ;") for p in re.split(r"(?:^|\s)(?:\d{1,2}[\)\.])\s+", text) if p.strip(" ;")]
    if len(parts) <= 1:
        parts = [p.strip() for p in re.split(r"\n+", text) if p.strip()]
    return parts[:8]


def solution_steps(text, limit=40):
    """Yechim matni → doskadagi qadamlar. «doska || ovoz» bo'lsa, o'qituvchi o'ng tomonini aytadi."""
    lines = [x.strip() for x in re.split(r"\n+", _t(text)) if x.strip()]
    result = []
    for line in lines[:limit]:
        board, _, voice = line.partition("||")
        board, voice = board.strip(), voice.strip()
        result.append({"doska": board, "ovoz": voice or board})
    return result


def option_list(text):
    """«A) ...\nB) ...» → ['...', '...']"""
    parts = re.split(r"(?:^|\s)([A-Ea-e])\)\s*", "\n" + _t(text))
    return [parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)]


def practice_item(unit, media_url):
    """Kitob kodi bilan belgilangan amaliy qadam yoki test → kod oynasi/doska uchun yagona ko'rinish."""
    p = unit.get("payload") or {}
    if unit["unit_kind"] == "task":
        options = [_t(p.get(f"variant_{x}")) for x in "abcd"]
        letter = _t(p.get("togri_javob")).upper()[:1]
        togri = "ABCD".index(letter) if letter and letter in "ABCD" else None
        solution = solution_steps(p.get("izoh") or p.get("javob_mezoni"))
        if togri is not None:
            solution.insert(0, {"doska": f"Javob: {letter}) {options[togri]}", "ovoz": f"To'g'ri javob — {letter} variant."})
        return {"kod": _t(p.get("kitob_kodi")), "turi": "test", "turi_nomi": "Test", "sarlavha": _t(p.get("sarlavha")),
                "shart": _t(p.get("savol")), "rasm": media_url(_t(p.get("media_id"))), "variantlar": options,
                "togri": togri, "javob": letter, "yechim": solution}
    kind = _t(p.get("amaliy_turi")) or "topshiriq"
    options = option_list(p.get("variantlar"))
    answer = _t(p.get("togri_javob")) or _t(p.get("kutilgan_javob"))
    letter = answer.upper().rstrip(").")[:1] if options else ""
    togri = "ABCDE".index(letter) if letter and letter in "ABCDE"[:len(options)] else None
    title = _t(p.get("sarlavha"))
    prefix = PRACTICE_NAMES.get(kind, "") + " · "
    return {"kod": _t(p.get("kitob_kodi")), "turi": kind, "turi_nomi": PRACTICE_NAMES.get(kind, "Topshiriq"),
            "sarlavha": title[len(prefix):] if title.startswith(prefix) else title,
            "shart": _t(p.get("doska_matni")), "rasm": media_url(_t(p.get("media_id"))), "variantlar": options,
            "togri": togri, "javob": answer, "yechim": solution_steps(p.get("yechim"))}


def _first_sentence(text, limit=90):
    text = _t(text)
    cut = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return cut if len(cut) <= limit else cut[: limit - 1].rstrip() + "…"


def build_lesson(topic, units, media_url, extra_questions=()):
    """Sof funksiya: bazasiz sinash mumkin. units — nashr qilingan birliklar ro'yxati."""
    by_kind = {}
    for u in units:
        by_kind.setdefault(u["unit_kind"], []).append(u)

    def payload(u):
        return u.get("payload") or {}

    steps, variants = [], {}
    scenario = sorted(
        by_kind.get("lesson_step", []),
        key=lambda u: (_int(payload(u).get("tartib"), 9999), u["unit_code"]),
    )
    if scenario:
        for u in scenario[:MAX_STEPS]:
            p = payload(u)
            kind = _t(p.get("qadam_turi")).lower()
            steps.append({
                "id": u["unit_code"],
                "turi": kind if kind in STEP_TYPES else "tushuntirish",
                "sahna": _t(p.get("sahna")) or u["unit_code"],
                "sarlavha": _t(p.get("sarlavha")),
                "doska": _t(p.get("doska_matni")),
                "ovoz": _t(p.get("ovoz_matni")) or _t(p.get("doska_matni")),
                "rasm": media_url(_t(p.get("media_id"))),
                "savol": _t(p.get("oquvchi_savoli")),
                "javob": _t(p.get("kutilgan_javob")),
                "javob_izohi": _t(p.get("javob_izohi")),
                "sahifa": _t(p.get("sahifa")),
            })
            if steps[-1]["turi"] == "amaliy":
                item = practice_item(u, media_url)
                steps[-1].update(kod=item["kod"], amaliy_turi=item["turi"], turi_nomi=item["turi_nomi"],
                                 variantlar=item["variantlar"], togri=item["togri"], yechim=item["yechim"])
        for u in by_kind.get("variant", []):
            p = payload(u)
            kind = _t(p.get("variant_turi")).lower()
            variants.setdefault(_t(p.get("step_id")), []).append({
                "id": u["unit_code"],
                "turi": kind,
                "nom": _t(p.get("tugma_nomi")) or VARIANT_NAMES.get(kind, "Boshqacha"),
                "doska": _t(p.get("doska_matni")),
                "ovoz": _t(p.get("ovoz_matni")),
                "rasm": media_url(_t(p.get("media_id"))),
                "takrorlash_topic_code": _t(p.get("takrorlash_topic_code")),
            })
        for items in variants.values():
            items.sort(key=lambda v: list(VARIANT_NAMES).index(v["turi"]) if v["turi"] in VARIANT_NAMES else 99)
        auto = False
    else:
        auto = True
        name = topic.get("mavzu") or "Bugungi mavzu"
        explanations = by_kind.get("explanation", [])
        explanations.sort(key=lambda u: 0 if "hayot" in _t(payload(u).get("uslub")).lower() else 1)
        main_exp = explanations[0] if explanations else None
        if main_exp and _t(payload(main_exp).get("kirish_savoli")):
            p = payload(main_exp)
            steps.append({"id": "auto-kirish", "turi": "kirish", "sahna": "kirish", "sarlavha": name,
                          "doska": _t(p.get("kirish_savoli")),
                          "ovoz": " ".join(x for x in (_t(p.get("kirish_savoli")), _t(p.get("hayotiy_boglanish"))) if x),
                          "rasm": None, "savol": "", "javob": "", "javob_izohi": "", "sahifa": _t(p.get("sahifa"))})
        rule_step = None
        for u in by_kind.get("knowledge", [])[:4]:
            p = payload(u)
            formula = _t(p.get("formula_latex"))
            doska = f"${formula}$" if formula and "$" not in formula else (formula or _t(p.get("qisqa_xulosa")) or _first_sentence(u.get("body")))
            step = {"id": u["unit_code"], "turi": "qoida", "sahna": u["unit_code"], "sarlavha": _t(u.get("title")),
                    "doska": doska, "ovoz": _t(u.get("body")), "rasm": None, "savol": "", "javob": "",
                    "javob_izohi": "", "sahifa": _t(p.get("sahifa"))}
            steps.append(step)
            rule_step = rule_step or step
        if main_exp:
            p = payload(main_exp)
            step = {"id": main_exp["unit_code"], "turi": "tushuntirish", "sahna": main_exp["unit_code"],
                    "sarlavha": "Tushuntirish", "doska": _t(p.get("korazmali_tavsif")) or _first_sentence(p.get("tushuntirish")),
                    "ovoz": _t(p.get("tushuntirish")), "rasm": None, "savol": "", "javob": "", "javob_izohi": "",
                    "sahifa": _t(p.get("sahifa"))}
            steps.append(step)
            rule_step = rule_step or step
        for u in by_kind.get("example", [])[:2]:
            p = payload(u)
            scene = u["unit_code"]
            steps.append({"id": scene, "turi": "misol", "sahna": scene, "sarlavha": "Misol", "doska": _t(p.get("shart")),
                          "ovoz": "Keling, misolni birga yechamiz. " + _t(p.get("shart")), "rasm": None, "savol": "",
                          "javob": "", "javob_izohi": "", "sahifa": _t(p.get("sahifa"))})
            for i, part in enumerate(_split_solution(p.get("yechim_qadamlar")), 1):
                steps.append({"id": f"{scene}-{i}", "turi": "misol", "sahna": scene, "sarlavha": "", "doska": f"{i}) {part}",
                              "ovoz": part, "rasm": None, "savol": "", "javob": "", "javob_izohi": "", "sahifa": ""})
            if _t(p.get("yakuniy_javob")):
                steps.append({"id": f"{scene}-javob", "turi": "misol", "sahna": scene, "sarlavha": "",
                              "doska": "Javob: " + _t(p.get("yakuniy_javob")),
                              "ovoz": "Javob: " + _t(p.get("yakuniy_javob")) + ". " + _t(p.get("tekshirish_usuli")),
                              "rasm": None, "savol": "", "javob": "", "javob_izohi": "", "sahifa": ""})
        if main_exp and _t(payload(main_exp).get("tekshiruv_savoli")) and _t(payload(main_exp).get("kutilgan_javob")):
            p = payload(main_exp)
            steps.append({"id": "auto-birga", "turi": "birga", "sahna": "birga", "sarlavha": "Endi sen javob ber",
                          "doska": _t(p.get("tekshiruv_savoli")), "ovoz": _t(p.get("tekshiruv_savoli")), "rasm": None,
                          "savol": "Javobingizni yozing", "javob": _t(p.get("kutilgan_javob")), "javob_izohi": "", "sahifa": ""})
        summaries = [_t(payload(u).get("qisqa_xulosa")) for u in by_kind.get("knowledge", []) if _t(payload(u).get("qisqa_xulosa"))]
        if summaries:
            steps.append({"id": "auto-xulosa", "turi": "xulosa", "sahna": "xulosa", "sarlavha": "Esda tut",
                          "doska": summaries[0], "ovoz": "Barakalla! Esda tut: " + " ".join(summaries[:2]),
                          "rasm": None, "savol": "", "javob": "", "javob_izohi": "", "sahifa": ""})
        if rule_step:
            extra = []
            for u in explanations[1:4]:
                p = payload(u)
                style = _t(p.get("uslub")).lower()
                kind = "hikoya" if "hayot" in style or "hikoya" in style else "rasm" if "ko'rgazma" in style or "rasm" in style else "sodda"
                extra.append({"id": u["unit_code"], "turi": kind, "nom": VARIANT_NAMES.get(kind, "Boshqacha"),
                              "doska": _t(p.get("korazmali_tavsif")) or _first_sentence(p.get("tushuntirish")),
                              "ovoz": _t(p.get("tushuntirish")), "rasm": None, "takrorlash_topic_code": ""})
            for u in by_kind.get("support", [])[:2]:
                p = payload(u)
                extra.append({"id": u["unit_code"], "turi": "sodda", "nom": "Soddaroq",
                              "doska": _t(p.get("ishora_1")) or _first_sentence(p.get("qayta_tushuntirish")),
                              "ovoz": _t(p.get("qayta_tushuntirish")), "rasm": None, "takrorlash_topic_code": ""})
            if extra:
                variants[rule_step["id"]] = extra[:5]

    questions = []
    for u in by_kind.get("task", []):
        p = payload(u)
        kind = re.sub(r"[\s_-]+", "", _t(p.get("vazifa_turi")).lower())
        options = filled_options([_t(p.get(f"variant_{x}")) for x in "abcd"])
        letter = _t(p.get("togri_javob")).upper()[:1]
        if kind in {"singlechoice", "test", "tanlov"} and options and letter in "ABCD"[:len(options)] and letter:
            questions.append({"id": u["unit_code"], "savol": _t(p.get("savol")), "variantlar": options,
                              "togri": "ABCD".index(letter), "izoh": _t(p.get("izoh")) or _t(p.get("javob_mezoni")),
                              "kod": _t(p.get("kitob_kodi"))})
    seen = {q["savol"] for q in questions}
    for q in extra_questions:
        if len(questions) >= MAX_QUESTIONS:
            break
        if q["savol"] not in seen:
            questions.append(q)
            seen.add(q["savol"])

    return {
        "topic": topic,
        "auto": auto,
        "steps": steps,
        "variants": variants,
        "savollar": questions[:MAX_QUESTIONS],
    }


def _svg_name(name):
    """«rasm.png» → «rasm.svg» (Excel'da png yozilgan, ZIP'da jonli svg kelgan bo'lishi mumkin)."""
    base, dot, _ext = str(name or "").rpartition(".")
    return f"{base}.svg" if dot and base else str(name or "")


def media_resolver(cur, units):
    """Birliklardagi media_id → /api/ai_miya_media/<id> (faqat nashr qilingan paketlardan)."""
    wanted = set()
    resources = {}
    for u in units:
        p = u.get("payload") or {}
        if u["unit_kind"] == "resource" and p.get("resource_id"):
            resources[p["resource_id"]] = _t(p.get("url_yoki_fayl"))
        if p.get("media_id"):
            wanted.add(_t(p["media_id"]))
    names = set()
    for m in wanted:
        target = resources.get(m, m)
        if target and not target.startswith("https://"):
            names.add(target.lower())
            names.add(_svg_name(target).lower())   # REV98: jonli SVG bo'lsa — u birinchi
    by_name = {}
    if names:
        cur.execute(
            """SELECT DISTINCT ON (lower(m.file_name)) m.id, lower(m.file_name) AS name
               FROM ai_brain_media m JOIN ai_brain_import_batches b ON b.id=m.batch_id
               WHERE b.status='published' AND lower(m.file_name)=ANY(%s)
               ORDER BY lower(m.file_name), m.id DESC""",
            (sorted(names),),
        )
        by_name = {r["name"]: r["id"] for r in cur.fetchall()}

    def media_url(media_id):
        if not media_id:
            return None
        target = resources.get(media_id, media_id)
        if target.startswith("https://"):
            return target
        found = by_name.get(_svg_name(target).lower()) or by_name.get(target.lower())
        return f"/api/ai_miya_media/{found}" if found else None

    return media_url


INSTITUTION_NAMES = {"maktab": "Maktab", "universitet": "Institut", "bogcha": "Bog'cha", "markaz": "Markaz"}


def placement_label(r):
    """Mavzu qaysi o'quvchilarga chiqishini odam tushunadigan qilib yozadi."""
    kind = r.get("institution_type")
    if not kind:
        return "Katalogga biriktirilmagan — o'quvchilar ko'rmaydi"
    parts = [INSTITUTION_NAMES.get(kind, kind)]
    if r.get("institution_name") and kind != "maktab":
        parts.append(r["institution_name"])
    if kind == "universitet":
        parts += [x for x in (r.get("yonalish_nomi"), f"{r['kurs']}-kurs" if r.get("kurs") else "",
                              f"{r['semestr']}-semestr" if r.get("semestr") else "") if x]
    elif r.get("grade"):
        parts.append(f"{r['grade']}-sinf" if str(r["grade"]).isdigit() else str(r["grade"]))
    if r.get("subject_name"):
        parts.append(str(r["subject_name"]))
    return " · ".join(parts)


def topic_placements(cur, codes):
    codes = sorted({c for c in codes if c})
    if not codes:
        return {}
    cur.execute("SELECT to_regclass('public.curriculum_scopes') IS NOT NULL AS bor")
    has_scopes = bool((cur.fetchone() or {}).get("bor"))
    scope_cols = ("cs.institution_type,cs.institution_name,cs.yonalish_nomi,cs.kurs,cs.semestr"
                  if has_scopes else "NULL AS institution_type,NULL AS institution_name,NULL AS yonalish_nomi,NULL AS kurs,NULL AS semestr")
    scope_join = "LEFT JOIN curriculum_scopes cs ON cs.id=d.curriculum_scope_id" if has_scopes else ""
    cur.execute(
        f"""SELECT d.topic_code,COALESCE(NULLIF(d.kichik_name,''),NULLIF(d.mavzu_name,''),NULLIF(d.bolim_name,''),d.bob_name) AS nom,
                  d.subject_name,d.grade,{scope_cols}
           FROM dts_tree d {scope_join}
           WHERE d.topic_code=ANY(%s) AND COALESCE(d.is_deleted,FALSE)=FALSE""",
        (codes,),
    )
    result = {}
    for r in cur.fetchall():
        r = dict(r)
        result[r["topic_code"]] = {"nom": _t(r.get("nom")), "joy": placement_label(r),
                                   "korinadi": bool(r.get("institution_type")),
                                   "turi": r.get("institution_type") or ""}
    return result


def create_router(platform):
    router = APIRouter(tags=["dars-xonasi"])

    @router.get("/api/ai_miya_media/{media_id}")
    def ai_miya_media(media_id: int):
        conn = platform._db()
        cur = conn.cursor()
        try:
            platform._ai_brain_jadvallari(cur)
            platform._ai_brain_dars_jadvallari(cur)
            cur.execute(
                """SELECT m.content_type,m.data,m.sha256 FROM ai_brain_media m
                   JOIN ai_brain_import_batches b ON b.id=m.batch_id
                   WHERE m.id=%s AND b.status='published'""",
                (media_id,),
            )
            row = cur.fetchone()
            conn.commit()
        finally:
            cur.close()
            conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Rasm topilmadi")
        return Response(
            content=bytes(row["data"]),
            media_type=row["content_type"],
            headers={
                "Cache-Control": "public, max-age=86400",
                "ETag": f'"{row["sha256"]}"',
                "X-Content-Type-Options": "nosniff",
                "Content-Security-Policy": "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'",
            },
        )

    def load_lesson(topic_code):
        topic_code = _t(topic_code)[:80]
        if not topic_code:
            raise HTTPException(status_code=400, detail="Mavzu kodi kerak")
        conn = platform._db()
        cur = conn.cursor()
        try:
            platform._ai_brain_jadvallari(cur)
            platform._ai_brain_dars_jadvallari(cur)
            cur.execute(
                """SELECT topic_name,subtopic_name,subject_name,grade,learning_objective,level_no,page_start
                   FROM ai_brain_topic_maps WHERE topic_code=%s AND status='published'
                   ORDER BY id DESC LIMIT 1""",
                (topic_code,),
            )
            tm = cur.fetchone()
            topic = {"topic_code": topic_code, "mavzu": "", "fan": "", "sinf": "", "maqsad": "", "daraja": None}
            if tm:
                topic.update(mavzu=_t(tm["subtopic_name"]) or _t(tm["topic_name"]), fan=_t(tm["subject_name"]),
                             sinf=_t(tm["grade"]), maqsad=_t(tm["learning_objective"]), daraja=tm["level_no"])
            else:
                cur.execute(
                    """SELECT COALESCE(NULLIF(kichik_name,''),NULLIF(mavzu_name,''),NULLIF(bolim_name,''),bob_name) AS nom,
                              subject_name,grade FROM dts_tree WHERE topic_code=%s LIMIT 1""",
                    (topic_code,),
                )
                d = cur.fetchone()
                if d:
                    topic.update(mavzu=_t(d["nom"]), fan=_t(d["subject_name"]), sinf=_t(d["grade"]))

            cur.execute(
                """SELECT unit_code,unit_kind,title,body,payload,source_page,book_title,version_no
                   FROM ai_brain_published_units WHERE topic_code=%s
                   ORDER BY unit_code,version_no DESC""",
                (topic_code,),
            )
            units, seen = [], set()
            for r in cur.fetchall():
                if r["unit_code"] in seen:
                    continue
                seen.add(r["unit_code"])
                units.append(dict(r))

            media_url = media_resolver(cur, units)

            extra = []
            cur.execute(
                """SELECT id,question,option_a,option_b,option_c,option_d,correct_answer,explanation
                   FROM generated_tests
                   WHERE topic_code=%s AND COALESCE(question_type,'single_choice')='single_choice'
                   ORDER BY id LIMIT 12""",
                (topic_code,),
            )
            for r in cur.fetchall():
                options = filled_options([_t(r[k]) for k in ("option_a", "option_b", "option_c", "option_d")])
                letter = _t(r["correct_answer"]).upper()[:1]
                if options and letter and letter in "ABCD"[:len(options)]:
                    extra.append({"id": f"test-{r['id']}", "savol": _t(r["question"]), "variantlar": options,
                                  "togri": "ABCD".index(letter), "izoh": _t(r["explanation"])})

            lesson = build_lesson(topic, units, media_url, extra)
            books = [u for u in units if u.get("book_title")]
            lesson["manba"] = {"kitob": books[0]["book_title"]} if books else None
            codes = [
                v["takrorlash_topic_code"] for items in lesson["variants"].values() for v in items
                if v.get("takrorlash_topic_code")
            ]
            if codes:
                cur.execute(
                    """SELECT topic_code,COALESCE(NULLIF(kichik_name,''),NULLIF(mavzu_name,''),bob_name) AS nom
                       FROM dts_tree WHERE topic_code=ANY(%s)""",
                    (codes,),
                )
                names_by_code = {r["topic_code"]: _t(r["nom"]) for r in cur.fetchall()}
                for items in lesson["variants"].values():
                    for v in items:
                        if v.get("takrorlash_topic_code"):
                            v["takrorlash_nomi"] = names_by_code.get(v["takrorlash_topic_code"], "")
            conn.commit()
        finally:
            cur.close()
            conn.close()
        if not lesson["steps"]:
            raise HTTPException(status_code=404, detail="Bu mavzu uchun dars hali nashr qilinmagan")
        return lesson

    @router.get("/api/kitob_kod/{kod}")
    def kitob_kod(kod: str, token: str):
        """Kitobdagi misol/masala/topshiriq/test kodi → sharti va yechimi (AI doskada ko'rsatish uchun)."""
        platform._jwt_tekshir(token)
        key = re.sub(r"[^A-Z0-9]", "", _t(kod).upper())
        if not 3 <= len(key) <= 24:
            raise HTTPException(status_code=400, detail="Kodni kitobdagidek yozing, masalan: XB-03-A01")
        conn = platform._db()
        cur = conn.cursor()
        try:
            platform._ai_brain_jadvallari(cur)
            platform._ai_brain_dars_jadvallari(cur)
            cur.execute(
                """SELECT unit_code,unit_kind,topic_code,title,payload,book_title,subject_name,grade
                   FROM ai_brain_published_units
                   WHERE payload ? 'kitob_kodi'
                     AND regexp_replace(upper(payload->>'kitob_kodi'),'[^A-Z0-9]','','g')=%s
                     AND unit_kind IN ('lesson_step','task')
                   ORDER BY published_at DESC NULLS LAST, version_no DESC LIMIT 1""",
                (key,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Bu kod topilmadi. Kodni kitobdagidek tekshirib yozing.")
            unit = dict(row)
            item = practice_item(unit, media_resolver(cur, [unit]))
            topic_code = unit["topic_code"]
            cur.execute(
                """SELECT COALESCE(NULLIF(subtopic_name,''),topic_name) AS nom,subject_name,grade
                   FROM ai_brain_topic_maps WHERE topic_code=%s AND status='published' ORDER BY id DESC LIMIT 1""",
                (topic_code,),
            )
            tm = cur.fetchone()
            if not tm:
                cur.execute(
                    """SELECT COALESCE(NULLIF(kichik_name,''),NULLIF(mavzu_name,''),NULLIF(bolim_name,''),bob_name) AS nom,
                              subject_name,grade FROM dts_tree WHERE topic_code=%s LIMIT 1""",
                    (topic_code,),
                )
                tm = cur.fetchone()
            cur.execute(
                "SELECT 1 FROM ai_brain_published_units WHERE topic_code=%s AND unit_kind='lesson_step' LIMIT 1",
                (topic_code,),
            )
            has_lesson = bool(cur.fetchone())
            conn.commit()
        finally:
            cur.close()
            conn.close()
        item["mavzu"] = {"topic_code": topic_code, "nomi": _t((tm or {}).get("nom")),
                         "fan": _t((tm or {}).get("subject_name")) or _t(unit.get("subject_name")),
                         "sinf": _t((tm or {}).get("grade")) or _t(unit.get("grade")), "dars_bor": has_lesson}
        item["kitob"] = _t(unit.get("book_title"))
        return item

    @router.get("/api/dars_xonasi/{topic_code}")
    def dars_xonasi(topic_code: str, token: str):
        platform._jwt_tekshir(token)
        return load_lesson(topic_code)

    def media_bytes(urls):
        ids = [int(u.rsplit("/", 1)[1]) for u in urls if u and re.fullmatch(r"/api/ai_miya_media/\d+", u)]
        if not ids:
            return {}
        conn = platform._db()
        cur = conn.cursor()
        try:
            cur.execute(
                """SELECT m.id,m.data FROM ai_brain_media m JOIN ai_brain_import_batches b ON b.id=m.batch_id
                   WHERE m.id=ANY(%s) AND b.status='published'""",
                (ids,),
            )
            return {f"/api/ai_miya_media/{r['id']}": bytes(r["data"]) for r in cur.fetchall()}
        finally:
            cur.close()
            conn.close()

    @router.get("/api/dars_xonasi/{topic_code}/yuklab")
    def dars_yuklab(topic_code: str, token: str, format: str = "pdf"):
        """Ochiq dars ishlanmasi: shu mavzuning nashr qilingan darsi PDF yoki Word ko'rinishida."""
        platform._jwt_tekshir(token)
        fmt = format.lower()
        if fmt not in ("pdf", "docx"):
            raise HTTPException(status_code=400, detail="Format pdf yoki docx bo'lishi kerak")
        lesson = load_lesson(topic_code)
        urls = [s.get("rasm") for s in lesson["steps"]] + [v.get("rasm") for vs in lesson["variants"].values() for v in vs]
        images = media_bytes(urls)
        from modules.dars_export import lesson_docx, lesson_pdf
        data = lesson_pdf(lesson, images) if fmt == "pdf" else lesson_docx(lesson, images)
        safe = re.sub(r"[^A-Za-z0-9_-]+", "_", lesson["topic"].get("mavzu") or topic_code)[:60] or "dars"
        media_type = "application/pdf" if fmt == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return Response(content=data, media_type=media_type, headers={
            "Content-Disposition": f'attachment; filename="ochiq_dars_{safe}.{fmt}"',
            "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
        })

    @router.get("/api/admin/ai_miya_darslar")
    def ai_miya_darslar(token: str):
        """Nashr qilingan kitob darslari va ular qaysi o'quvchilarga chiqishi."""
        platform._admin_tekshir(token)
        conn = platform._db()
        cur = conn.cursor()
        try:
            platform._ai_brain_jadvallari(cur)
            cur.execute(
                """SELECT u.topic_code,
                          COUNT(*) FILTER (WHERE u.unit_kind='lesson_step') AS qadam,
                          COUNT(*) FILTER (WHERE u.unit_kind='variant') AS variant,
                          COUNT(*) FILTER (WHERE u.unit_kind IN ('knowledge','explanation','example')) AS bilim,
                          MAX(u.published_at) AS nashr, MAX(s.book_title) AS kitob
                   FROM ai_brain_units u LEFT JOIN ai_brain_sources s ON s.id=u.source_id
                   WHERE u.status='published'
                   GROUP BY u.topic_code ORDER BY MAX(u.published_at) DESC NULLS LAST LIMIT 500"""
            )
            rows = [dict(r) for r in cur.fetchall()]
            codes = [r["topic_code"] for r in rows]
            places = topic_placements(cur, codes)
            tests = {}
            if codes:
                cur.execute("SELECT topic_code,COUNT(*) AS soni FROM generated_tests WHERE topic_code=ANY(%s) GROUP BY topic_code", (codes,))
                tests = {r["topic_code"]: int(r["soni"]) for r in cur.fetchall()}
            conn.commit()
        finally:
            cur.close()
            conn.close()
        darslar = []
        for r in rows:
            place = places.get(r["topic_code"], {"nom": "", "joy": "Mavzular bazasida topilmadi", "korinadi": False, "turi": ""})
            darslar.append({
                "topic_code": r["topic_code"], "mavzu": place["nom"], "joy": place["joy"], "korinadi": place["korinadi"],
                "turi": place["turi"], "qadam": int(r["qadam"] or 0), "variant": int(r["variant"] or 0),
                "bilim": int(r["bilim"] or 0), "test": tests.get(r["topic_code"], 0), "kitob": r.get("kitob") or "",
                "nashr": r["nashr"].isoformat() if r.get("nashr") else None,
            })
        return {"darslar": darslar}

    return router

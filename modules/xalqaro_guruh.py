"""REV553: Xalqaro baholash (PISA / TIMSS) sinfi — o'quvchilarni REYTING bo'yicha guruhlarga bo'lish.

Sof funksiyalar (bazasiz, testlanadi). Qoidalar (Azizjon bergan):
  1. O'quvchilar reyting bo'yicha tartiblanadi; har guruhda 30 ta: 1-guruh — eng yuqori reytinglilar, 2-guruh — keyingilari …
  2. Guruhda 20 tadan kam o'quvchi qolmasligi kerak. Oxirgi guruh 20 dan kam chiqsa:
       • qoldiq 1–9 ta bo'lsa — oldingi guruhga qo'shiladi (30 atrofida: 31–39 ta);
       • qoldiq 10–19 ta bo'lsa — oxirgi ikki guruh teng bo'linadi (har biri 20–25 ta).
     Shunda har guruh 20–39 ta bo'ladi. Jami o'quvchi 20 dan kam bo'lsa — bitta guruh (boshqa iloj yo'q).
  3. Reytingi hali yo'q (kirish testini topshirmagan) o'quvchi guruhga kiritilmaydi — «kutayotganlar» ro'yxatida turadi.
  4. Qayta guruhlashda guruhi o'zgargan o'quvchilar alohida qaytariladi — ularga «Siz reytingingizga mos yangi guruhga
     o'tdingiz» degan xabar ko'rsatiladi.
"""
from __future__ import annotations

GURUH_HAJMI = 30
GURUH_ENG_KAM = 20


def guruh_hajmlari(n: int, hajm: int = GURUH_HAJMI, eng_kam: int = GURUH_ENG_KAM) -> list[int]:
    """n ta o'quvchi uchun guruh hajmlari ro'yxati (yuqori reytingdan pastga). Masalan 68 → [30, 38]; 75 → [30, 23, 22]."""
    n = int(n)
    if n <= 0:
        return []
    toliq, qoldiq = divmod(n, hajm)
    if toliq == 0:
        return [n]                      # jami 30 dan kam — bitta guruh
    hajmlar = [hajm] * toliq
    if qoldiq == 0:
        return hajmlar
    if qoldiq >= eng_kam:
        return hajmlar + [qoldiq]       # qoldiq o'zi to'laqonli guruh (20–29)
    if qoldiq < eng_kam - hajm // 3:    # 1–9: oxirgi guruhga qo'shiladi (31–39 — «30 atrofida»)
        hajmlar[-1] += qoldiq
        return hajmlar
    jami = hajm + qoldiq                # 10–19: oxirgi ikki guruh teng bo'linadi (40–49 → 20–25 dan)
    return hajmlar[:-1] + [(jami + 1) // 2, jami // 2]


def guruhlarga_bol(oquvchilar: list[dict], hajm: int = GURUH_HAJMI, eng_kam: int = GURUH_ENG_KAM) -> dict:
    """oquvchilar: [{"user_id": int, "reyting": float | None, "qoshildi": saralash uchun ixtiyoriy}].
    → {"guruhlar": [{"raqam": 1, "azolar": [user_id…], "eng_yuqori": r, "eng_past": r, "ortacha": r}], "kutayotgan": [user_id…]}.
    Teng reytingda avval qo'shilgan o'quvchi yuqoriroq (natija har safar bir xil bo'lishi uchun), so'ng user_id bo'yicha."""
    borlar = [o for o in oquvchilar if o.get("reyting") is not None]
    kutayotgan = [int(o["user_id"]) for o in oquvchilar if o.get("reyting") is None]
    borlar.sort(key=lambda o: (-float(o["reyting"]), str(o.get("qoshildi") or ""), int(o["user_id"])))
    guruhlar, boshi = [], 0
    for raqam, soni in enumerate(guruh_hajmlari(len(borlar), hajm, eng_kam), 1):
        bolak = borlar[boshi:boshi + soni]
        boshi += soni
        r = [float(o["reyting"]) for o in bolak]
        guruhlar.append({"raqam": raqam, "azolar": [int(o["user_id"]) for o in bolak],
                         "eng_yuqori": max(r), "eng_past": min(r), "ortacha": round(sum(r) / len(r), 1)})
    return {"guruhlar": guruhlar, "kutayotgan": kutayotgan}


def guruh_ozgarishlari(eski: dict[int, int], yangi_bolinish: dict) -> list[dict]:
    """eski: {user_id: guruh raqami}. → guruhi o'zgargan yoki birinchi marta guruh olgan o'quvchilar:
    [{"user_id", "eski": raqam | None, "yangi": raqam, "tur": "yangi" | "yuqoriga" | "pastga"}]. Raqam kichik — reyting yuqori."""
    out = []
    for g in yangi_bolinish.get("guruhlar", []):
        for uid in g["azolar"]:
            oldingi = eski.get(uid)
            if oldingi == g["raqam"]:
                continue
            tur = "yangi" if oldingi is None else ("yuqoriga" if g["raqam"] < oldingi else "pastga")
            out.append({"user_id": uid, "eski": oldingi, "yangi": g["raqam"], "tur": tur})
    return out


# ───────────────────────── REV555: reyting, shubhali natija, barqaror ko'chish ─────────────────────────
# Azizjon talabi: «shubhalini tekshirsin (GPT'dan ishlab yoki nimadir qilsa) — uni ko'tarmasin; STABILI guruhdan guruhga ko'chsin,
# qolgani qolaversin». Shuning uchun: (1) har natija shubha belgilariga tekshiriladi; (2) shubhali natija reytingga DARHOL
# qo'shilmaydi — keyingi toza natija uni tasdiqlasa qo'shiladi, tasdiqlamasa bekor bo'ladi; (3) o'quvchi boshqa guruhga faqat
# ketma-ket bir necha toza natijasi shuni ko'rsatsa ko'chadi.

TEZ_SONIYA = 12            # bir savolga o'rtacha shuncha soniyadan kam va natija yuqori — o'qib ulgurmagan
TEZ_FOIZ = 70
CHIQISH_CHEGARA = 3        # imtihon paytida ilovadan shuncha marta chiqqan
SAKRASH_BALL = 90          # oldingi reytingdan shuncha ball yuqori (xalqaro darajalar orasi 75 ball) — bir darajadan ortiq sakrash
NOMOS_ULUSH = 0.75         # «oson savol xato, qiyin savol to'g'ri» juftliklari ulushi — faqat ESLATMA uchun (pastga qarang)
NOMOS_FARQ = 1.0           # juftlikdagi qiyinlik farqi (logit)
TASDIQ_FARQ = 60           # keyingi toza natija shubhalidan ko'pi bilan shuncha past bo'lsa — shubhali natija tasdiqlanadi
REYTING_YANGI_VAZN = 0.35  # reyting = 65% oldingi + 35% yangi natija (bitta omadli/omadsiz kun reytingni keskin o'zgartirmaydi)
KOCHISH_UCHUN = 3          # ko'chish uchun ketma-ket nechta toza natija kerak
KOCHISH_CHEGARA = 15       # chegaradan shuncha ball «ichkarida» bo'lishi kerak (chegarada tebranib yurmasin)
GURUH_ENG_KOP = 39

SHUBHA_MATNI = {
    "juda_tez": "Savollarga juda tez javob berilgan (o‘qib ulgurish qiyin), natija esa yuqori",
    "ilovadan_chiqdi": "Imtihon paytida ilovadan bir necha marta chiqilgan",
    "keskin_osish": "Natija oldingi darajadan keskin yuqori",
    "nomos_javoblar": "Oson savollar xato, qiyin savollar to‘g‘ri — odatiy emas",
}


def nomos_ulushi(qiyinliklar, togri) -> float:
    """Oson savol xato-yu, undan ancha qiyin savol to'g'ri bo'lgan juftliklar ulushi (0…1). Juftlik kam bo'lsa — 0."""
    juft = [(a, b, oa, ob) for i, (a, oa) in enumerate(zip(qiyinliklar, togri)) for b, ob in list(zip(qiyinliklar, togri))[i + 1:]]
    mumkin = teskari = 0
    for a, b, oa, ob in juft:
        oson_ok, qiyin_ok = (oa, ob) if a < b else (ob, oa)
        if abs(a - b) < NOMOS_FARQ or oson_ok == qiyin_ok:
            continue
        mumkin += 1
        teskari += int(qiyin_ok and not oson_ok)
    return round(teskari / mumkin, 3) if mumkin >= 6 else 0.0


def urinish_shubhasi(u: dict, oldingi_reyting=None) -> list[str]:
    """u: {"ball", "foiz", "soni", "soniya", "chiqishlar", "qiyinliklar": [...], "togri": [...]}. → shubha sabablari (bo'sh — toza)."""
    sabab = []
    soni = max(1, int(u.get("soni") or 0))
    soniya = u.get("soniya")
    if soniya is not None and soniya / soni < TEZ_SONIYA and int(u.get("foiz") or 0) >= TEZ_FOIZ:
        sabab.append("juda_tez")
    if int(u.get("chiqishlar") or 0) >= CHIQISH_CHEGARA:
        sabab.append("ilovadan_chiqdi")
    if oldingi_reyting is not None and u.get("ball") is not None and u["ball"] - oldingi_reyting >= SAKRASH_BALL:
        sabab.append("keskin_osish")
    return sabab


def urinish_eslatmasi(u: dict) -> list[str]:
    """BLOKLAMAYDIGAN belgilar — natija hisobga olinadi, o'qituvchi esa ro'yxatda eslatmani ko'radi.
    «Oson savol xato, qiyin savol to'g'ri»: 12–14 savolli testda halol o'quvchida ham tasodifan uchraydi. O'lchov (4000 ta taqlid):
    chegara 0,35 da halol o'quvchilarning 14–15% i, 0,75 da 2% i belgilanadi — shuning uchun bu belgi o'quvchini to'xtatmaydi."""
    q, t = u.get("qiyinliklar") or [], u.get("togri") or []
    return ["nomos_javoblar"] if q and len(q) == len(t) and nomos_ulushi(q, t) >= NOMOS_ULUSH else []


KUCHLI_SHUBHA = {"juda_tez", "ilovadan_chiqdi"}   # «keskin_osish» — zaif belgi: yaxshi o'qigan bolada ham bo'ladi


def reyting_hisobla(urinishlar: list[dict]) -> dict:
    """urinishlar — vaqt tartibida (eskisi avval), har biri urinish_shubhasi() kutgan maydonlar + ixtiyoriy "id".
    → {"reyting": int | None, "tarix": [{"id", "ball", "holat", "sabab", "eslatma"}], "toza": [oxirgi hisobga olingan ballar], "kutmoqda": n}.
    holat: "hisobga" (hisobga olindi) · "shubhali" (tekshiruv kutmoqda) · "tasdiqlandi" (keyingi natija tasdiqladi) · "rad" (tasdiqlanmadi).

    Qoidalar:
      • Toza natija — darhol hisobga olinadi; kutib turgan shubhalilarni hal qiladi (yaqin bo'lsa tasdiqlaydi, uzoq bo'lsa bekor qiladi).
      • KUCHLI belgili natija (juda tez / ilovadan chiqqan) — o'zi hech qachon hisobga kirmaydi; faqat keyingi
        natija uni tasdiqlasa.
      • Faqat «keskin o'sish» belgisi bor natija: birinchi marta — kutadi; ikkinchi marta ketma-ket yaqin natija chiqsa — o'sish
        haqiqiy: bu natija hisobga olinadi, oldingi (faqat «keskin o'sish»li) natija tasdiqlanadi. Aks holda chindan o'sgan o'quvchi
        abadiy tekshiruvda qolib ketardi (reytingi past turgani uchun har yangi natijasi ham «sakrash» bo'lib ko'rinardi)."""
    reyting, tarix, toza, kutayotgan = None, [], [], []

    def qosh(ball):
        nonlocal reyting
        reyting = int(ball) if reyting is None else int(round((1 - REYTING_YANGI_VAZN) * reyting + REYTING_YANGI_VAZN * ball))
        toza.append(int(ball))

    def hal_qil(ball, faqat_zaif_tasdiq):
        """Kutib turganlarni hal qiladi. faqat_zaif_tasdiq — tasdiqlovchi natijaning o'zi «keskin o'sish»li bo'lsa, u faqat
        shunday (kuchli belgisiz) natijalarni tasdiqlay oladi; kuchli belgililar bekor bo'ladi."""
        for k in kutayotgan:
            yaqin = ball >= k["ball"] - TASDIQ_FARQ
            kuchli = bool(KUCHLI_SHUBHA & set(k["sabab"]))
            if yaqin and not (faqat_zaif_tasdiq and kuchli):
                k["holat"] = "tasdiqlandi"
                qosh(k["ball"])
            else:
                k["holat"] = "rad"
        kutayotgan.clear()

    for u in urinishlar:
        if u.get("ball") is None:
            continue
        ball = int(u["ball"])
        # «Keskin o'sish» reyting bilan emas, o'quvchining OXIRGI TASDIQLANGAN darajasi bilan solishtiriladi: reyting sekin ko'tariladi
        # (65% eski + 35% yangi), shuning uchun chindan o'sgan o'quvchining har ikkinchi natijasi «sakrash» bo'lib ko'rinardi.
        asos = reyting if len(toza) < 2 else max(reyting, int(round(sum(toza[-2:]) / 2)))
        sabab = urinish_shubhasi(u, asos)
        yozuv = {"id": u.get("id"), "ball": ball, "holat": "hisobga", "sabab": sabab, "eslatma": urinish_eslatmasi(u)}
        tarix.append(yozuv)
        if not sabab:
            hal_qil(ball, False)
            qosh(ball)
        elif sabab == ["keskin_osish"] and any(ball >= k["ball"] - TASDIQ_FARQ and k["ball"] >= ball - TASDIQ_FARQ for k in kutayotgan):
            hal_qil(ball, True)      # ikkinchi marta ketma-ket shu darajada — o'sish haqiqiy
            qosh(ball)
        else:
            yozuv["holat"] = "shubhali"
            kutayotgan.append(yozuv)
    return {"reyting": reyting, "tarix": tarix, "toza": toza[-6:], "kutmoqda": len(kutayotgan)}


def _barqaror(oxirgilar, chegara, yuqoriga: bool) -> bool:
    """Oxirgi KOCHISH_UCHUN ta toza natijaning hammasi chegaradan (zaxira bilan) yuqori / past."""
    o = list(oxirgilar or [])[-KOCHISH_UCHUN:]
    if len(o) < KOCHISH_UCHUN:
        return False
    return all(b >= chegara + KOCHISH_CHEGARA for b in o) if yuqoriga else all(b <= chegara - KOCHISH_CHEGARA for b in o)


def qayta_guruhla(azolar: list[dict], hajm: int = GURUH_HAJMI, eng_kam: int = GURUH_ENG_KAM) -> dict:
    """azolar: [{"user_id", "reyting": int | None, "guruh": joriy raqam | None, "toza": [oxirgi toza ballar], "qoshildi"}].
    Qoida: guruhi bor o'quvchi JOYIDA QOLADI; faqat oxirgi 3 ta toza natijasi barqaror ravishda boshqa guruh darajasida bo'lsa ko'chadi.
    Yangi (guruhi yo'q, reytingi bor) o'quvchi reytingiga mos guruhga tushadi. Guruhlar hajmi buzilsa (20 dan kam yoki 39 dan ko'p)
    yoki guruhlar soni o'zgarishi kerak bo'lsa — hammasi reyting bo'yicha qayta bo'linadi (birlashish/ajralish).
    → {"guruhlar", "kutayotgan", "ozgarishlar", "toliq_qayta": bool}"""
    ideal = guruhlarga_bol(azolar, hajm, eng_kam)
    eski = {int(a["user_id"]): int(a["guruh"]) for a in azolar if a.get("guruh") and a.get("reyting") is not None}
    if not ideal["guruhlar"]:
        return {**ideal, "ozgarishlar": [], "toliq_qayta": False}
    ideal_g = {u: g["raqam"] for g in ideal["guruhlar"] for u in g["azolar"]}
    past_chegara = {g["raqam"]: g["eng_past"] for g in ideal["guruhlar"]}       # shu guruhga kirish uchun eng past reyting
    n = len(ideal["guruhlar"])
    if not eski:                                                                # birinchi marta — sof reyting bo'yicha
        return {**ideal, "ozgarishlar": guruh_ozgarishlari({}, ideal), "toliq_qayta": True}
    yangi = {}
    for a in azolar:
        if a.get("reyting") is None:
            continue
        uid, joriy, maqsad = int(a["user_id"]), eski.get(int(a["user_id"])), ideal_g[int(a["user_id"])]
        if joriy is None or joriy > n:                    # yangi o'quvchi yoki guruhi yo'q bo'lib ketgan — reytingiga mos joyga
            yangi[uid] = maqsad
        elif maqsad < joriy and _barqaror(a.get("toza"), past_chegara[maqsad], True):
            yangi[uid] = maqsad                           # barqaror yuqori natija — yuqori guruhga
        elif maqsad > joriy and _barqaror(a.get("toza"), past_chegara[joriy], False):
            yangi[uid] = maqsad                           # barqaror past natija — quyi guruhga
        else:
            yangi[uid] = joriy                            # qolganlar joyida qoladi
    hajmlar = {g: sum(1 for v in yangi.values() if v == g) for g in range(1, n + 1)}
    jami = len(yangi)
    buzildi = any(h > GURUH_ENG_KOP for h in hajmlar.values()) or (jami >= eng_kam and any(h < eng_kam for h in hajmlar.values()))
    if buzildi or max(eski.values()) != n:
        return {**ideal, "ozgarishlar": guruh_ozgarishlari(eski, ideal), "toliq_qayta": True}
    reyting = {int(a["user_id"]): float(a["reyting"]) for a in azolar if a.get("reyting") is not None}
    guruhlar = []
    for g in range(1, n + 1):
        az = sorted((u for u, v in yangi.items() if v == g), key=lambda u: (-reyting[u], u))
        r = [reyting[u] for u in az]
        guruhlar.append({"raqam": g, "azolar": az, "eng_yuqori": max(r), "eng_past": min(r), "ortacha": round(sum(r) / len(r), 1)})
    natija = {"guruhlar": guruhlar, "kutayotgan": ideal["kutayotgan"]}
    return {**natija, "ozgarishlar": guruh_ozgarishlari(eski, natija), "toliq_qayta": False}

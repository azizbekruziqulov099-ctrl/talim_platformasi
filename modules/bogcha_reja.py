"""REV162: bog'cha — aqlli haftalik reja, kurs/paket narxlari, ota-ona obunasi, rozilik va AI kundalik bahosi.

Haftalik reja (AI miya «avto-repetitor»):
  • ish kunlari (dushanba–juma) kuniga yoshiga qarab 2–4 ta yangi dars, shanba 3–4 ta, yakshanba — faqat takrorlash;
  • bir fan haftada ko'pi bilan 3 marta, odatda kun ora (du–cho–ju yoki se–pa–sha) — orada o'yin va takror;
  • bir kunda bitta fandan ko'pi bilan 1 ta yangi dars;
  • yoshiga qarab bir vaqtda nechta kurs o'qitiladi (YOSH_QOIDA) — ortig'i «navbatda» turadi
    («Avval bitta tilni tugatsin»); bola katta bo'lsa (yoshi o'zgarsa) navbat o'zi ochiladi;
  • o'tkazib yuborilgan dars yo'qolmaydi: shu haftaning bo'sh joyida «qarz» dars bo'lib ochiladi va darslar
    tartib bilan — qolgan joyidan davom etadi.

Narxlar (faqat admin): tarif = N ta kurs (1, 4, 5, 10…) yoki «to'liq» (kurs_soni=0 — yoshiga ruxsat etilgan hammasi),
oylik narx va «narx qulfi» (1–3 yil): obuna bo'lgan ota-ona shu muddat davomida eski narxda uzaytiradi,
admin yangi ulanuvchilar uchun narxni oshira oladi.

To'lov — Click / Payme (REV160/161 buyurtma jadvali click_tolovlar, turi='obuna'), avtomatik tasdiq.
To'lovdan oldin ota-ona Gmail va Telegram'ni ulaydi va qisqa shartlarga rozilik beradi.
"""
import itertools
import json
import re
import threading
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Body, Header, HTTPException

TASHKENT = timezone(timedelta(hours=5))
KUNLAR = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]

# kalit, nom, turi (til | fan), emoji, til kodi (ovoz uchun), aniqlash
KURSLAR = [
    ("en", "Ingliz tili", "til", "🇬🇧", "en", r"ingliz|english"),
    ("ru", "Rus tili", "til", "🇷🇺", "ru", r"\brus\b|rus tili|russian"),
    ("ar", "Arab tili", "til", "🇸🇦", "ar", r"arab"),
    ("tr", "Turk tili", "til", "🇹🇷", "tr", r"turk"),
    ("de", "Nemis tili", "til", "🇩🇪", "de", r"nemis|german"),
    ("fr", "Fransuz tili", "til", "🇫🇷", "fr", r"fransuz|french"),
    ("es", "Ispan tili", "til", "🇪🇸", "es", r"ispan|spanish"),
    ("ko", "Koreys tili", "til", "🇰🇷", "ko", r"koreys|korean"),
    ("ja", "Yapon tili", "til", "🇯🇵", "ja", r"yapon|japan"),
    ("zh", "Xitoy tili", "til", "🇨🇳", "zh", r"xitoy|chinese"),
    ("ona", "Ona tili", "fan", "📖", "", r"ona tili|o.?zbek|savod|nutq"),
    ("mat", "Matematika", "fan", "🔢", "", r"matem"),
    ("man", "Mantiq", "fan", "🧩", "", r"mantiq|logika"),
    ("olam", "Atrof-olam", "fan", "🌳", "", r"atrof|tabiat"),
]
KURS = {k[0]: {"kalit": k[0], "nom": k[1], "turi": k[2], "emoji": k[3], "til": k[4]} for k in KURSLAR}
# aniqlash tartibi: avval fanlar («Matematika (rus tilida)» — matematika), keyin tillar
_KURS_RE = [(k[0], re.compile(k[5], re.I)) for k in KURSLAR if k[2] == "fan"] + \
    [(k[0], re.compile(k[5], re.I)) for k in KURSLAR if k[2] == "til"]

# yosh: ish kuni / shanba (yangi dars soni), bir vaqtda jami kurs va shundan chet tili
YOSH_QOIDA = {
    2: {"kun": 2, "shanba": 3, "jami": 5, "til": 4},
    3: {"kun": 2, "shanba": 3, "jami": 6, "til": 4},
    4: {"kun": 3, "shanba": 3, "jami": 8, "til": 5},
    5: {"kun": 3, "shanba": 4, "jami": 9, "til": 6},
    6: {"kun": 4, "shanba": 4, "jami": 10, "til": 7},
    7: {"kun": 4, "shanba": 4, "jami": 10, "til": 7},
}
FAN_HAFTA_MAX = 3
FAN_HAFTA_MIN = 2
ROZILIK_VERSIYA = "2026-10-v1"
ROZILIK_BANDLAR = [
    "Darslarni AI ustoz farzandingiz yoshiga qarab haftalik jadval bilan beradi: ish kunlari kuniga 2–4 ta, shanba 3–4 ta yangi dars, yakshanba — faqat takrorlash.",
    "Bir fan haftasiga ko‘pi bilan 3 marta o‘tiladi. Yoshiga ko‘ra bir vaqtda o‘qitiladigan kurslar soni cheklangan — ortig‘i navbatda turadi va bitta kurs tugagach ochiladi.",
    "Kunlik ekran vaqti: 2–5 yosh — 1 soat dars + 1 soat o‘yin, 6–7 yosh — 2 soat dars + 1 soat o‘yin. Vaqt tugasa darslar ertaga ochiladi.",
    "Dars o‘tkazib yuborilsa yo‘qolmaydi — keyingi bo‘sh kunda qolgan joyidan davom etadi.",
    "To‘lov 30 kunga. Obuna narxi tarifda ko‘rsatilgan muddat (1–3 yil) davomida siz uchun o‘zgarmaydi.",
    "Farzandingiz natijalari (yulduzlar, AI bahosi, aytgan so‘zlari) faqat sizga — ota-ona paneli va Telegram orqali ko‘rinadi.",
    "Ilova bola qaysi ilovaga o‘tganini ko‘rmaydi — faqat platformadan chiqib ketganini biladi. Bu tibbiy yoki psixologik tashxis emas.",
]
DEFAULT_TARIFLAR = [
    ("1 ta kurs", 1, 0, 1, 10), ("4 ta kurs", 4, 0, 1, 20), ("5 ta kurs", 5, 0, 1, 30),
    ("10 ta kurs", 10, 0, 1, 40), ("To‘liq paket", 0, 0, 1, 50),
]
# AI bahosi: savolga javob tezligi me'yori (ms) yosh guruhi bo'yicha
TEZLIK_MEYOR = {"2-3 yosh": 7000, "4-5 yosh": 5000, "6-7 yosh": 3500}


# ── Sof mantiq (DB'siz sinaladi) ─────────────────────────────────
def fan_kaliti(nom):
    """Katalogdagi fan nomi («Ingliz tili (izoh: rus)», «Matematika») → kurs kaliti ('en', 'mat'). Topilmasa — ''."""
    text = re.sub(r"\(\s*izoh[^)]*\)", "", str(nom or ""), flags=re.I)
    for key, rx in _KURS_RE:
        if rx.search(text):
            return key
    return ""


def yosh_qoidasi(yosh, override=None):
    try:
        n = int(yosh)
    except (TypeError, ValueError):
        n = 3
    n = min(7, max(2, n))
    base = dict(YOSH_QOIDA[n])
    if isinstance(override, dict):
        o = override.get(str(n)) or override.get(n)
        if isinstance(o, dict):
            for k in ("kun", "shanba", "jami", "til"):
                try:
                    v = int(o.get(k, base[k]))
                except (TypeError, ValueError):
                    continue
                base[k] = max(0 if k in ("kun", "shanba") else 1, min(13 if k in ("jami", "til") else 6, v))
    base["yosh"] = n
    return base


def guruh_yoshi(group, age=None):
    if age:
        try:
            return min(7, max(2, int(age)))
        except (TypeError, ValueError):
            pass
    m = re.match(r"\s*(\d)", str(group or ""))
    return int(m.group(1)) if m else 3


def tozala_fanlar(fanlar):
    out = []
    for f in fanlar or []:
        k = str(f or "").strip()
        if k in KURS and k not in out:
            out.append(k)
    return out


def ajrat(fanlar, qoida):
    """Tanlangan kurslar (ustuvorlik tartibida) → (faol, navbat). Yosh chegarasidan ortig'i navbatga."""
    faol, navbat, til = [], [], 0
    for k in tozala_fanlar(fanlar):
        is_til = KURS[k]["turi"] == "til"
        if len(faol) < qoida["jami"] and (not is_til or til < qoida["til"]):
            faol.append(k)
            til += is_til
        else:
            navbat.append(k)
    return faol, navbat


def _sigim(qoida):
    return [qoida["kun"]] * 5 + [qoida["shanba"]]


def _joylash(plan_order, sessions, cap, usul):
    load = [0] * 6
    hafta = [[] for _ in range(7)]
    got = {}
    for k in plan_order:
        need = sessions[k]
        placed = None
        while need > 0 and placed is None:
            best, best_score = None, None
            for combo in itertools.combinations(range(6), need):
                if any(load[d] >= cap[d] for d in combo):
                    continue
                adj = sum(1 for a, b in zip(combo, combo[1:]) if b - a == 1)
                sat = int(KURS[k]["turi"] != "til" and 5 in combo)
                if usul == "teng":   # eng kam yuklangan kunlar, kun ora, fanlar — shanba
                    score = (-sum(load[d] for d in combo), -adj, sat, -max(combo))
                else:                # eng ko'p bo'sh joyli kunlar — hamma kurs sig'ishi kafolatlanadi
                    score = (sum(cap[d] - load[d] for d in combo), -adj, sat, -max(combo))
                if best_score is None or score > best_score:
                    best, best_score = combo, score
            if best is None:
                need -= 1
            else:
                placed = best
        for d in placed or ():
            load[d] += 1
            hafta[d].append(k)
        got[k] = len(placed or ())
    return hafta, got


def haftalik_reja(fanlar, qoida):
    """Haftalik jadval: {faol, navbat, hafta: [[kalit…] × 7 (yakshanba bo'sh)], haftalik: {kalit: n}, sigim}."""
    faol, navbat = ajrat(fanlar, qoida)
    cap = _sigim(qoida)
    total = sum(cap)
    n = len(faol)
    sessions = {}
    if n:
        base = max(1, min(FAN_HAFTA_MAX, total // n))
        extra = max(0, total - base * n)
        order = [k for k in faol if KURS[k]["turi"] == "til"] + [k for k in faol if KURS[k]["turi"] != "til"]
        for k in faol:
            sessions[k] = base
        for k in order:
            if extra <= 0 or sessions[k] >= FAN_HAFTA_MAX:
                continue
            sessions[k] += 1
            extra -= 1
    # ko'p sessiyali va tillar avval joylashadi; avval «kun ora, teng taqsim», sig'masa — «eng bo'sh kunlar» usuli
    plan_order = sorted(faol, key=lambda k: (-sessions[k], 0 if KURS[k]["turi"] == "til" else 1, faol.index(k)))
    hafta, got = _joylash(plan_order, sessions, cap, "teng")
    if any(got[k] < sessions[k] for k in faol):
        hafta2, got2 = _joylash(plan_order, sessions, cap, "sigim")
        if sum(got2.values()) > sum(got.values()):
            hafta, got = hafta2, got2
    sigmadi = [k for k in faol if not got.get(k)]   # sig'im juda kichik (admin qoidasi) — navbatga
    if sigmadi:
        faol = [k for k in faol if k not in sigmadi]
        navbat = sigmadi + navbat
        got = {k: v for k, v in got.items() if k in faol}
    for d in range(6):
        hafta[d].sort(key=lambda k: faol.index(k))
    return {"faol": faol, "navbat": navbat, "hafta": hafta, "haftalik": got, "sigim": cap + [0]}


def bugungi_kvota(reja, wd, oldin, bugun):
    """Bugun qaysi fandan nechta YANGI dars ochiladi.

    reja — haftalik_reja() natijasi, wd — hafta kuni (0=dushanba), oldin — {kalit: shu hafta kechagacha ochilgan yangi
    darslar}, bugun — {kalit: bugun ochilgan}. Qaytaradi {kalit: qoldi}. Yakshanba — hammasi 0 (takror kuni).
    O'tkazib yuborilgan (qarz) dars bugungi rejadagilardan keyin, kunlik sig'im yetsa ochiladi."""
    out = {k: 0 for k in reja["faol"]}
    if wd >= 6:
        return out
    cap = reja["sigim"][wd]
    rejada = [k for k in reja["hafta"][wd] if k in out]
    jami_bugun = sum(int(bugun.get(k, 0)) for k in out)
    rejada_qolgan = sum(1 for k in rejada if int(bugun.get(k, 0)) < 1
                        and int(oldin.get(k, 0)) < reja["haftalik"].get(k, 0))
    bosh = cap - jami_bugun - rejada_qolgan   # qarz darslar uchun bo'sh joy
    for k in reja["faol"]:
        hafta_jami = int(oldin.get(k, 0)) + int(bugun.get(k, 0))
        if hafta_jami >= reja["haftalik"].get(k, 0) or int(bugun.get(k, 0)) >= 1:
            continue
        if k in rejada:
            out[k] = 1 if jami_bugun < cap else 0
            continue
        kerak = sum(1 for d in range(wd) if k in reja["hafta"][d])
        if kerak > int(oldin.get(k, 0)) and bosh > 0:
            out[k] = 1
            bosh -= 1
    return out


def keyingi_kun(reja, kalit, wd):
    """Fan keyingi qaysi kuni rejada (bugundan keyin) — bolaga/ota-onaga aytish uchun."""
    for step in range(1, 8):
        d = (wd + step) % 7
        if d < 6 and kalit in reja["hafta"][d]:
            return KUNLAR[d]
    return ""


def narx_hisobla(tarif, obuna, today):
    """Ota-ona to'laydigan narx: shu tarifda obuna bo'lgan va narx qulfi hali tugamagan bo'lsa — eski (qulflangan) narx."""
    joriy = int(tarif["narx_uzs"] or 0)
    if obuna and int(obuna.get("tarif_id") or 0) == int(tarif["id"]) and obuna.get("narx_qulf_gacha"):
        gacha = obuna["narx_qulf_gacha"]
        if isinstance(gacha, str):
            gacha = date.fromisoformat(gacha[:10])
        if gacha >= today and int(obuna["narx_uzs"]) <= joriy:   # narx tushsa — yangi (arzonroq) narx
            return {"narx": int(obuna["narx_uzs"]), "qulf": True, "qulf_gacha": gacha.isoformat(), "joriy": joriy}
    return {"narx": joriy, "qulf": False, "qulf_gacha": None, "joriy": joriy}


def tarif_kurs_soni(tarif, qoida):
    """«To'liq» tarif (0) — yoshiga ruxsat etilgan hammasi; kursga bog'langan tarif — o'sha kurslar sonidan oshmaydi."""
    n = int(tarif.get("kurs_soni") or 0)
    n = qoida["jami"] if n <= 0 else n
    ruxsat = tarif_kurslari(tarif)
    return min(n, len(ruxsat)) if ruxsat else n


def tarif_kurslari(tarif):
    return tozala_fanlar(_json(tarif.get("kurslar"), []) if isinstance(tarif, dict) else [])


def tanlov_kodi(fanlar, tarif, qoida):
    """tanlov_xatosi() sababining kodi — frontend uni foydalanuvchi tilida aytadi."""
    fanlar = tozala_fanlar(fanlar)
    ruxsat = tarif_kurslari(tarif)
    if not fanlar:
        return "tanlov_bosh"
    if ruxsat and any(k not in ruxsat for k in fanlar):
        return "tanlov_tarif_kursi"
    if len(fanlar) > tarif_kurs_soni(tarif, qoida):
        return "tanlov_tarif"
    return "tanlov_yosh"


def tanlov_xatosi(fanlar, tarif, qoida):
    fanlar = tozala_fanlar(fanlar)
    limit = tarif_kurs_soni(tarif, qoida)
    ruxsat = tarif_kurslari(tarif)
    if not fanlar:
        return "Kamida bitta kurs tanlang."
    if ruxsat and any(k not in ruxsat for k in fanlar):
        return "Bu tarif faqat shu kurslar uchun: " + ", ".join(KURS[k]["nom"] for k in ruxsat) + "."
    if len(fanlar) > limit:
        return f"Bu tarifda {limit} ta kurs. Ortiqchasini olib tashlang."
    tillar = sum(1 for k in fanlar if KURS[k]["turi"] == "til")
    if len(fanlar) > qoida["jami"] or tillar > qoida["til"]:
        return (f"{qoida['yosh']} yoshli bola bir vaqtda {qoida['jami']} tagacha kurs (shundan {qoida['til']} tagacha chet tili) "
                "o‘qiy oladi. Ko‘proq olmoqchi bo‘lsangiz, avval farzandingiz bitta tilni tugatsin.")
    return ""


def _ulush(a, b):
    return None if not b else max(0.0, min(1.0, a / b))


def ai_baho(dars, guruh=""):
    """AI kundalik bahosi (bitta dars): aniqlik, gapirish, tezlik, puxtalik → 0–100 ball va 2–5 baho.

    aniqlik — test/o'yindagi to'g'ri javoblar; gapirish — mikrofonga to'g'ri aytgan so'zlar/iboralar;
    tezlik — savolga javob vaqti yosh me'yoriga nisbatan; puxtalik — darsni oxirigacha va chalg'imay o'tdimi."""
    aniq = _ulush(int(dars.get("togri") or 0), int(dars.get("jami") or 0))
    ovoz_j = int(dars.get("ovoz_jami") or 0)
    words = dars.get("sozlar") or []
    if ovoz_j:
        gap = _ulush(int(dars.get("ovoz_togri") or 0), ovoz_j)
    else:
        tried = [w for w in words if isinstance(w, dict) and w.get("aytdi") is not None]
        gap = _ulush(sum(1 for w in tried if w.get("aytdi")), len(tried))
    ms = int(dars.get("javob_ms") or 0)
    meyor = TEZLIK_MEYOR.get(guruh, 5000)
    tez = None if not ms else max(0.0, min(1.0, (3 * meyor - ms) / (2 * meyor)))
    tugadi = bool(dars.get("tugadi"))
    chalg = int(dars.get("chalgish") or 0)
    pux = max(0.0, (1.0 if tugadi else 0.4) - 0.12 * min(chalg, 5))
    qism = {"aniqlik": aniq, "gapirish": gap, "tezlik": tez, "puxtalik": pux}
    vazn = {"aniqlik": 0.35, "gapirish": 0.3, "tezlik": 0.15, "puxtalik": 0.2}
    bor = {k: v for k, v in qism.items() if v is not None}
    ball = round(100 * sum(v * vazn[k] for k, v in bor.items()) / sum(vazn[k] for k in bor)) if bor else 0
    return {"ball": ball, "baho": baho_raqam(ball),
            "qism": {k: (None if v is None else round(v * 100)) for k, v in qism.items()}}


def baho_raqam(ball):
    return 5 if ball >= 85 else 4 if ball >= 70 else 3 if ball >= 50 else 2


BAHO_MATN = {5: "A’lo", 4: "Yaxshi", 3: "O‘rtacha", 2: "Mashq kerak"}


def kun_bahosi(darslar):
    """Kunlik umumiy baho: tugatilgan darslar bahosining o'rtachasi (qismlari ham)."""
    rows = [d.get("ai_baho") for d in darslar if d.get("ai_baho") and d.get("tugadi")]
    if not rows:
        return None
    ball = round(sum(r["ball"] for r in rows) / len(rows))
    qism = {}
    for k in ("aniqlik", "gapirish", "tezlik", "puxtalik"):
        vals = [r["qism"][k] for r in rows if r["qism"].get(k) is not None]
        qism[k] = round(sum(vals) / len(vals)) if vals else None
    b = baho_raqam(ball)
    return {"ball": ball, "baho": b, "matn": BAHO_MATN[b], "qism": qism, "darslar": len(rows)}


def hafta_xulosa(darslar):
    """Bir hafta: darslar, tugatilgan, yulduz, so'zlar, o'rtacha baho, fanlar bo'yicha."""
    done = [d for d in darslar if d.get("tugadi")]
    words, said = {}, set()
    fans = {}
    for d in darslar:
        f = fans.setdefault(d.get("fan") or "", {"fan": d.get("fan") or "", "darslar": 0, "tugadi": 0})
        f["darslar"] += 1
        f["tugadi"] += bool(d.get("tugadi"))
        for w in d.get("sozlar") or []:
            key = str(w.get("soz") or "").lower()
            if key:
                words[key] = w
                if w.get("aytdi"):
                    said.add(key)
    kb = kun_bahosi(darslar)
    return {"darslar": len(darslar), "tugadi": len(done), "yulduz": sum(int(d.get("yulduz") or 0) for d in done),
            "sozlar": len(words), "aytdi": len(said), "baho": kb, "fanlar": sorted(fans.values(), key=lambda f: -f["darslar"])}


def hafta_boshi(day):
    return day - timedelta(days=day.weekday())


# ── REV166: bolaning yutuqlari va kundaligi (sof mantiq) ─────────
# Umumiy yulduz → daraja (bola o'qiy olmasa ham belgidan taniydi). Oxirgi darajadan keyin har 200 yulduzda yangi «Bilimdon».
DARAJALAR = [(0, "🥚", "Tuxumcha"), (5, "🐣", "Jo‘ja"), (15, "🐥", "Polapon"), (30, "🐤", "Qushcha"), (50, "🐦", "Chumchuq"),
             (80, "🦜", "To‘tiqush"), (120, "🦉", "Boyo‘g‘li"), (170, "🕊", "Kabutar"), (230, "🦅", "Burgut"), (300, "🌟", "Yulduz"),
             (400, "🚀", "Raketa"), (520, "🌈", "Kamalak"), (660, "👑", "Bilimdon")]
BILIMDON_QADAM = 200


def yulduz_darajasi(n):
    """Umumiy yulduz soni → {daraja, emoji, nom, dan, gacha, qoldi, foiz, keyingi{emoji, nom}}."""
    n = max(0, int(n or 0))
    i = max(j for j, (t, _, _) in enumerate(DARAJALAR) if n >= t)
    t, emoji, nom = DARAJALAR[i]
    if i + 1 < len(DARAJALAR):
        dan, (gacha, kemoji, knom), raqam = t, DARAJALAR[i + 1], i + 1
    else:
        extra = (n - t) // BILIMDON_QADAM
        dan = t + extra * BILIMDON_QADAM
        gacha, kemoji, knom, raqam = dan + BILIMDON_QADAM, emoji, nom, i + 1 + extra
    return {"daraja": raqam, "emoji": emoji, "nom": nom, "yulduz": n, "dan": dan, "gacha": gacha, "qoldi": gacha - n,
            "foiz": round(100 * (n - dan) / (gacha - dan)), "keyingi": {"emoji": kemoji, "nom": knom}}


def ketma_ket(sanalar, today):
    """Necha kun ketma-ket dars tugatdi. Bugun hali dars qilinmagan bo'lsa — kechagacha sanaladi (zanjir uzilmagan);
    yakshanba (takrorlash kuni) dars bo'lmasa zanjirni uzmaydi."""
    s = set(sanalar or [])
    d = today if today in s else today - timedelta(days=1)
    n = 0
    for _ in range(400):
        if d in s:
            n += 1
        elif d.weekday() != 6:
            break
        d -= timedelta(days=1)
    return n


def _uniq(items):
    seen, out = set(), []
    for x in items:
        k = str(x or "").strip()
        if k and k.lower() not in seen:
            seen.add(k.lower())
            out.append(k)
    return out


def kun_xulosasi(darslar):
    """Ota-onaga oddiy til bilan: bugun nimani o'rgandi, nimani takrorlash kerak.
    takror_soz — mikrofonga aytolmagan so'zlar (boshqa darsda to'g'ri aytganlari chiqarib tashlanadi);
    takror_dars — 1 yulduz yoki «Mashq kerak» bahosi bilan tugagan darslar; chala — boshlangan, lekin tugamagan darslar."""
    done = [d for d in darslar if d.get("tugadi")]
    said = {str(w.get("soz") or "").lower() for d in darslar for w in (d.get("sozlar") or []) if w.get("aytdi") is True}
    return {
        "organdi": _uniq(d.get("mavzu") for d in done),
        "sozlar": _uniq(w.get("soz") for d in darslar for w in (d.get("sozlar") or [])),
        "takror_soz": [w for w in _uniq(w.get("soz") for d in darslar for w in (d.get("sozlar") or []) if w.get("aytdi") is False)
                       if w.lower() not in said],
        "takror_dars": _uniq(d.get("mavzu") for d in done
                             if int(d.get("yulduz") or 0) <= 1 or int((d.get("ai_baho") or {}).get("baho") or 5) <= 2),
        "chala": _uniq(d.get("mavzu") for d in darslar if not d.get("tugadi")),
    }


def ertangi_fanlar(reja_hafta, wd):
    """Ertaga rejada qaysi fanlar (kalitlar). Yakshanba — takrorlash kuni (bo'sh ro'yxat)."""
    if not reja_hafta:
        return None
    nxt = (wd + 1) % 7
    return [] if nxt == 6 else list(reja_hafta[nxt] or [])


def kundalik_haftalari(darslar, reja_hafta, today):
    """Bola va ota-ona kundaligi: shu hafta va o'tgan hafta, har kun — rejadagi fanlar va o'tilgan darslar (yulduz, baho).
    darslar — lesson_row ko'rinishi (sana ISO, fan, mavzu, yulduz, tugadi, ai_baho); reja_hafta — 7 ta kun ro'yxati yoki None."""
    bosh = hafta_boshi(today)
    out = []
    for nom, start in (("shu", bosh), ("otgan", bosh - timedelta(days=7))):
        kunlar = []
        for i in range(7):
            d = start + timedelta(days=i)
            # REV168: kundalik kartasi uchun — o'rgangan so'zlar (rasmi bilan), savollar natijasi
            items = [{"kalit": fan_kaliti(x.get("fan")), "fan": x.get("fan") or "", "mavzu": x.get("mavzu") or "",
                      "tugadi": bool(x.get("tugadi")), "yulduz": int(x.get("yulduz") or 0) if x.get("tugadi") else 0,
                      "baho": (x.get("ai_baho") or {}).get("baho"),
                      "sozlar": [{"soz": w.get("soz"), "emoji": w.get("emoji") or "", "aytdi": w.get("aytdi")}
                                 for w in (x.get("sozlar") or [])[:6] if isinstance(w, dict) and w.get("soz")],
                      "togri": x.get("togri"), "jami": x.get("jami")}
                     for x in darslar if x.get("sana") == d.isoformat()]
            rejada = list(reja_hafta[i]) if nom == "shu" and reja_hafta and i < len(reja_hafta) else []
            kunlar.append({"sana": d.isoformat(), "kun": i, "rejada": rejada, "darslar": items,
                           "yulduz": sum(it["yulduz"] for it in items),
                           "holat": "bugun" if d == today else "otdi" if d < today else "keladi"})
        out.append({"hafta": nom, "boshi": start.isoformat(), "kunlar": kunlar,
                    "yulduz": sum(k["yulduz"] for k in kunlar),
                    "darslar": sum(1 for k in kunlar for it in k["darslar"] if it["tugadi"])})
    return out


# ── Baza ─────────────────────────────────────────────────────────
def migrate(cur):
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (91629162,))
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_tarif (
        id BIGSERIAL PRIMARY KEY,
        nom TEXT NOT NULL,
        kurs_soni INT NOT NULL DEFAULT 1 CHECK (kurs_soni >= 0 AND kurs_soni <= 20),
        narx_uzs BIGINT NOT NULL DEFAULT 0 CHECK (narx_uzs >= 0),
        qulf_yil INT NOT NULL DEFAULT 1 CHECK (qulf_yil BETWEEN 0 AND 5),
        faol BOOLEAN NOT NULL DEFAULT TRUE,
        tartib INT NOT NULL DEFAULT 0,
        yangilangan_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    # REV163: tarif aniq kurs(lar)ga bog'lanishi mumkin («Xitoy tili», «Tillar paketi: ingliz+rus+nemis»); bo'sh — istalgan kurs
    cur.execute("ALTER TABLE bogcha_tarif ADD COLUMN IF NOT EXISTS kurslar JSONB NOT NULL DEFAULT '[]'::jsonb")
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_tarif_tarix (
        id BIGSERIAL PRIMARY KEY, tarif_id BIGINT NOT NULL, eski_narx BIGINT, yangi_narx BIGINT NOT NULL,
        qulf_yil INT NOT NULL DEFAULT 1, admin_id BIGINT, ozgardi_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_obuna (
        bola_id BIGINT PRIMARY KEY,
        ota_id BIGINT NOT NULL,
        tarif_id BIGINT,
        kurs_soni INT NOT NULL DEFAULT 1,
        fanlar JSONB NOT NULL DEFAULT '[]'::jsonb,
        narx_uzs BIGINT NOT NULL DEFAULT 0,
        narx_qulf_gacha DATE,
        boshlandi DATE NOT NULL,
        tugaydi DATE NOT NULL,
        rozilik_at TIMESTAMPTZ,
        rozilik_versiya TEXT NOT NULL DEFAULT '',
        yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_obuna_tolov (
        id BIGSERIAL PRIMARY KEY, bola_id BIGINT NOT NULL, ota_id BIGINT NOT NULL, tarif_id BIGINT,
        summa_uzs BIGINT NOT NULL DEFAULT 0, manba TEXT NOT NULL DEFAULT '', kod TEXT NOT NULL DEFAULT '',
        fanlar JSONB NOT NULL DEFAULT '[]'::jsonb, tolandi_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS bogcha_obuna_tolov_kod ON bogcha_obuna_tolov(kod) WHERE kod <> ''")
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_reja (
        bola_id BIGINT PRIMARY KEY, ota_id BIGINT, fanlar JSONB NOT NULL DEFAULT '[]'::jsonb,
        tugagan JSONB NOT NULL DEFAULT '[]'::jsonb, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    # REV163: kurs avtomatik tugadi (yosh guruhidagi hamma dars o'tildi) — {kalit: guruh}; guruh o'zgarsa kurs qayta ochiladi
    cur.execute("ALTER TABLE bogcha_reja ADD COLUMN IF NOT EXISTS avto_tugagan JSONB NOT NULL DEFAULT '{}'::jsonb")
    # REV163: obuna tugash eslatmalari (bir obuna muddati uchun bir marta)
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_eslatma (bola_id BIGINT NOT NULL, tugaydi DATE NOT NULL, turi TEXT NOT NULL,
        yuborildi_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (bola_id, tugaydi, turi))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_sozlama (kalit TEXT PRIMARY KEY, qiymat JSONB NOT NULL DEFAULT '{}'::jsonb)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_kunlik_xabar (bola_id BIGINT NOT NULL, sana DATE NOT NULL, PRIMARY KEY (bola_id, sana))""")
    # REV167: shaxsiy chegirmalar — admin ota-onaga (barcha farzandlariga) yoki bitta farzandga beradi
    cur.execute("""CREATE TABLE IF NOT EXISTS bogcha_chegirma (
        id BIGSERIAL PRIMARY KEY, turi TEXT NOT NULL CHECK (turi IN ('ota','bola')), user_id BIGINT NOT NULL,
        foiz INT NOT NULL CHECK (foiz BETWEEN 1 AND 100), gacha DATE, izoh TEXT NOT NULL DEFAULT '', admin_id BIGINT,
        yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW(), ochirildi TIMESTAMPTZ)""")
    cur.execute("CREATE INDEX IF NOT EXISTS bogcha_chegirma_user ON bogcha_chegirma(turi, user_id) WHERE ochirildi IS NULL")
    cur.execute("SELECT COUNT(*) AS n FROM bogcha_tarif")
    if int((cur.fetchone() or {}).get("n") or 0) == 0:
        for nom, soni, narx, qulf, tartib in DEFAULT_TARIFLAR:
            cur.execute("INSERT INTO bogcha_tarif(nom,kurs_soni,narx_uzs,qulf_yil,faol,tartib) VALUES(%s,%s,%s,%s,FALSE,%s)",
                        (nom, soni, narx, qulf, tartib))


def _json(v, default):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            return default
    return default if v is None else v


def sozlama(cur):
    cur.execute("SELECT qiymat FROM bogcha_sozlama WHERE kalit='umumiy'")
    row = cur.fetchone()
    s = _json(row["qiymat"], {}) if row else {}
    return {"obuna_majburiy": bool(s.get("obuna_majburiy")), "yosh_qoida": s.get("yosh_qoida") or {},
            "telegram_majburiy": s.get("telegram_majburiy", True) is not False,
            "tun": tun_sozlama(s.get("tun")), "oila_chegirma": oila_chegirma_sozlama(s.get("oila_chegirma")),
            "sinov_dars": sinov_dars_soni(s.get("sinov_dars"))}


# ── REV168: sinov (reklama) darslari — bola olmagan kurs/fandan birinchi bir nechta dars bepul ochiladi ──
SINOV_DARS = 4


def sinov_dars_soni(v):
    try:
        return max(0, min(10, int(v if v is not None else SINOV_DARS)))
    except (TypeError, ValueError):
        return SINOV_DARS


def sinov_qoldi(cur, bola_id, faol, n):
    """Rejada (obunada) yo'q har kurs uchun yana nechta sinov darsi ochish mumkin: {kalit: qoldi}."""
    if n <= 0:
        return {}
    try:
        cur.execute("SAVEPOINT bogcha_sinov")
        cur.execute("SELECT fan, COUNT(*) AS n FROM bola_dars_holat WHERE child_id=%s GROUP BY fan", (bola_id,))
        rows = cur.fetchall()
        cur.execute("RELEASE SAVEPOINT bogcha_sinov")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT bogcha_sinov")
        rows = []
    ochilgan = {}
    for r in rows:
        k = fan_kaliti(r["fan"])
        if k:
            ochilgan[k] = ochilgan.get(k, 0) + int(r["n"] or 0)
    return {k: max(0, n - ochilgan.get(k, 0)) for k in KURS if k not in (faol or [])}


# ── REV167: kechki yopilish (bolalar uxlash vaqti) ───────────────
TUN_DEFAULT = {"yoqilgan": True, "kun": 22, "shanba": 23, "ertalab": 6}


def tun_sozlama(v):
    """Admin sozlamasi → to'g'ri qiymatlar: ish kunlari va yakshanba «kun» soatda, shanba «shanba» soatda yopiladi,
    ertalab «ertalab» soatda ochiladi."""
    v = v if isinstance(v, dict) else {}
    out = dict(TUN_DEFAULT)
    out["yoqilgan"] = v.get("yoqilgan", True) is not False
    for k, lo, hi in (("kun", 18, 24), ("shanba", 18, 24), ("ertalab", 4, 10)):
        try:
            out[k] = max(lo, min(hi, int(v.get(k, out[k]))))
        except (TypeError, ValueError):
            pass
    return out


def tun_holati(local_dt, tun):
    """local_dt — Toshkent vaqti. Qaytaradi {yopiq, yopiladi «22:00», ochiladi «06:00»}.
    Shanba kechasi — tun["shanba"] soatgacha, qolgan kunlar — tun["kun"] soatgacha; yarim tundan keyin ertalabgacha yopiq."""
    tun = tun_sozlama(tun)
    wd = local_dt.weekday()
    yopiladi = tun["shanba"] if wd == 5 else tun["kun"]
    daq = local_dt.hour * 60 + local_dt.minute
    yopiq = bool(tun["yoqilgan"]) and (daq >= yopiladi * 60 or daq < tun["ertalab"] * 60)
    return {"yopiq": yopiq, "yopiladi": f"{yopiladi:02d}:00" if yopiladi < 24 else "24:00", "ochiladi": f"{tun['ertalab']:02d}:00",
            "yoqilgan": bool(tun["yoqilgan"])}


# ── REV167: chegirmalar (oila — bir nechta farzand; shaxsiy — admin beradi; admin farzandi — bepul) ──
OILA_DEFAULT = {"2": 0, "3": 0}


def oila_chegirma_sozlama(v):
    v = v if isinstance(v, dict) else {}
    out = {}
    for k in ("2", "3"):
        try:
            out[k] = max(0, min(100, int(v.get(k, OILA_DEFAULT[k]))))
        except (TypeError, ValueError):
            out[k] = OILA_DEFAULT[k]
    return out


def chegirmali_narx(narx, foiz):
    """Narxdan foiz chegirma (100 so'mga yaxlitlanadi, 0 dan kam emas)."""
    narx, foiz = int(narx or 0), max(0, min(100, int(foiz or 0)))
    if foiz >= 100:
        return 0
    return max(0, int(round(narx * (100 - foiz) / 100 / 100.0)) * 100)


def chegirma_tanla(admin_farzand, shaxsiy, oila_tartibi, oila):
    """Bir nechta chegirma bo'lsa — eng kattasi (qo'shilmaydi). oila_tartibi — shu farzand oiladagi nechanchi obunachi (1, 2, 3…)."""
    variantlar = []
    if admin_farzand:
        variantlar.append({"foiz": 100, "sabab": "admin", "izoh": "Administrator farzandi — bepul"})
    for c in shaxsiy or []:
        variantlar.append({"foiz": int(c["foiz"]), "sabab": "shaxsiy", "izoh": c.get("izoh") or "Shaxsiy chegirma",
                           "gacha": c.get("gacha")})
    if oila_tartibi >= 2:
        f = int((oila or {}).get("3" if oila_tartibi >= 3 else "2", 0))
        if f:
            variantlar.append({"foiz": f, "sabab": "oila", "izoh": f"{oila_tartibi}-farzand uchun oila chegirmasi"})
    if not variantlar:
        return {"foiz": 0, "sabab": "", "izoh": ""}
    return max(variantlar, key=lambda x: x["foiz"])


def bola_yoshi(cur, bola_id):
    cur.execute("SELECT class, kabutar_learning_profile AS lp FROM users WHERE user_id=%s", (bola_id,))
    row = cur.fetchone() or {}
    lp = _json(row.get("lp"), {}) or {}
    return guruh_yoshi(lp.get("age_group") or row.get("class"), lp.get("age")), lp


def obuna_ol(cur, bola_id):
    cur.execute("SELECT * FROM bogcha_obuna WHERE bola_id=%s", (bola_id,))
    row = cur.fetchone()
    if not row:
        return None
    o = dict(row)
    o["fanlar"] = tozala_fanlar(_json(o.get("fanlar"), []))
    return o


def obuna_faolmi(obuna, today):
    return bool(obuna and obuna["tugaydi"] >= today)


def reja_ol(cur, bola_id, guruh=None):
    """(tartib, tugagan). guruh berilsa — shu yosh guruhida avtomatik tugagan kurslar ham «tugagan»."""
    cur.execute("SELECT * FROM bogcha_reja WHERE bola_id=%s", (bola_id,))
    row = cur.fetchone()
    if not row:
        return [], []
    tugagan = tozala_fanlar(_json(row["tugagan"], []))
    if guruh:
        avto = _json(row.get("avto_tugagan"), {}) or {}
        tugagan += [k for k, g in avto.items() if g == guruh and k in KURS and k not in tugagan]
    return tozala_fanlar(_json(row["fanlar"], [])), tugagan


def bola_guruhi(cur, bola_id):
    cur.execute("SELECT class, kabutar_learning_profile AS lp FROM users WHERE user_id=%s", (bola_id,))
    row = cur.fetchone() or {}
    lp = _json(row.get("lp"), {}) or {}
    return str(lp.get("age_group") or row.get("class") or "")


def avto_tugatish(cur, bola_id, kalit, guruh):
    """Yosh guruhidagi barcha darslar o'tildi — kurs shu guruh uchun tugagan (yangi guruhda qayta ochiladi).
    Qaytaradi: navbatdan ochilgan kurs kaliti (bo'lsa) yoki ''; allaqachon belgilangan bo'lsa None."""
    cur.execute("SELECT avto_tugagan FROM bogcha_reja WHERE bola_id=%s FOR UPDATE", (bola_id,))
    row = cur.fetchone()
    if not row:
        return None
    avto = _json(row["avto_tugagan"], {}) or {}
    if avto.get(kalit) == guruh:
        return None
    today = datetime.now(TASHKENT).date()
    before, _, _ = samarali_fanlar(cur, bola_id, today)
    yosh, _ = bola_yoshi(cur, bola_id)
    qoida = yosh_qoidasi(yosh, sozlama(cur)["yosh_qoida"])
    eski = haftalik_reja(before, qoida)
    avto[kalit] = guruh
    cur.execute("UPDATE bogcha_reja SET avto_tugagan=%s::jsonb, yangilandi=NOW() WHERE bola_id=%s", (json.dumps(avto), bola_id))
    after, _, _ = samarali_fanlar(cur, bola_id, today)
    yangi = haftalik_reja(after, qoida)
    ochildi = [k for k in yangi["faol"] if k not in eski["faol"]]
    return ochildi[0] if ochildi else ""


def samarali_fanlar(cur, bola_id, today):
    """Bolaga hozir tegishli kurslar (ustuvorlik tartibida) va manba: 'obuna' | 'reja' | '' (reja yo'q — eski tartib)."""
    obuna = obuna_ol(cur, bola_id)
    order, tugagan = reja_ol(cur, bola_id, bola_guruhi(cur, bola_id))
    if obuna_faolmi(obuna, today):
        pool = obuna["fanlar"]
        fanlar = [k for k in order if k in pool] + [k for k in pool if k not in order]
        return [k for k in fanlar if k not in tugagan], "obuna", obuna
    if order:
        return [k for k in order if k not in tugagan], "reja", obuna
    return [], "", obuna


def ochilgan_sonlar(cur, bola_id, today):
    """Shu hafta (dushanbadan kechagacha) va bugun har kursdan nechta YANGI dars ochilgan."""
    start = hafta_boshi(today)
    try:   # bola_dars_holat — bola_kuzatuv jadvali (hali yaratilmagan bo'lishi mumkin)
        cur.execute("SAVEPOINT bogcha_sonlar")
        cur.execute("SELECT fan, ochilgan_sana FROM bola_dars_holat WHERE child_id=%s AND ochilgan_sana >= %s", (bola_id, start))
        rows = cur.fetchall()
        cur.execute("RELEASE SAVEPOINT bogcha_sonlar")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT bogcha_sonlar")
        rows = []
    oldin, bugun = {}, {}
    for r in rows:
        k = fan_kaliti(r["fan"])
        if not k:
            continue
        target = bugun if r["ochilgan_sana"] == today else oldin
        target[k] = target.get(k, 0) + 1
    return oldin, bugun


def _admin_sinov_profili(cur, bola_id):
    """Admin yoki admin ochgan sinov profili — obuna talab qilinmaydi (bola ko'zi bilan tekshirish uchun)."""
    _, lp = bola_yoshi(cur, bola_id)
    ids = [bola_id] + ([int(lp["family_owner"])] if str(lp.get("family_owner") or "").lstrip("-").isdigit() else [])
    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid = ANY(%s)", (ids,))
    return cur.fetchone() is not None


def _savepoint_query(cur, name, sql, args):
    """Jadval bo'lmasligi mumkin bo'lgan so'rov — xato tranzaksiyani buzmaydi (None qaytaradi)."""
    try:
        cur.execute(f"SAVEPOINT {name}")
        cur.execute(sql, args)
        rows = cur.fetchall()
        cur.execute(f"RELEASE SAVEPOINT {name}")
        return rows
    except Exception:
        cur.execute(f"ROLLBACK TO SAVEPOINT {name}")
        return None


def ota_bolami(cur, ota_id, bola_id):
    """REV167: ota-ona shu bolani ko'ra oladimi — parent_child bog'lanishi YOKI oila profili egasi (Kim o'rganadi?).
    Oila profili yaratilganda parent_child yozuvi tushmay qolgan bo'lsa ham ota-ona kundalikni ko'radi."""
    if not ota_id or not bola_id:
        return False
    rows = _savepoint_query(cur, "ota_bola_pc", "SELECT 1 FROM parent_child WHERE parent_id=%s AND child_id=%s LIMIT 1", (ota_id, bola_id))
    if rows:
        return True
    rows = _savepoint_query(cur, "ota_bola_fp", """SELECT 1 FROM kabutar_family_profiles WHERE owner_user_id=%s AND profile_user_id=%s
                                                  AND removed_at IS NULL LIMIT 1""", (ota_id, bola_id))
    if rows:
        return True
    _, lp = bola_yoshi(cur, bola_id)
    return str(lp.get("family_owner") or "") == str(ota_id)


def adminmi(cur, uid):
    rows = _savepoint_query(cur, "bogcha_adminmi", "SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
    return bool(rows)


def admin_farzandimi(cur, bola_id):
    """Administrator o'z farzandi (oila profili yoki parent_child orqali) — kurslar bepul."""
    if _admin_sinov_profili(cur, bola_id):
        return True
    rows = _savepoint_query(cur, "bogcha_admin_ota", """SELECT 1 FROM parent_child pc JOIN admin_akkaunt a ON a.uid=pc.parent_id
                                                        WHERE pc.child_id=%s LIMIT 1""", (bola_id,))
    return bool(rows)


def chegirma_ol(cur, ota_id, bola_id, today, s=None):
    """Shu ota-ona shu farzand uchun qancha chegirma oladi (eng kattasi)."""
    s = s or sozlama(cur)
    shaxsiy = _savepoint_query(cur, "bogcha_cheg", """SELECT foiz, izoh, gacha FROM bogcha_chegirma WHERE ochirildi IS NULL
                                   AND (gacha IS NULL OR gacha >= %s) AND ((turi='bola' AND user_id=%s) OR (turi='ota' AND user_id=%s))""",
                               (today, bola_id, ota_id)) or []
    shaxsiy = [{"foiz": int(r["foiz"]), "izoh": r["izoh"], "gacha": r["gacha"].isoformat() if r["gacha"] else None} for r in shaxsiy]
    rows = _savepoint_query(cur, "bogcha_oila", """SELECT COUNT(DISTINCT bola_id) AS n FROM bogcha_obuna
                                                  WHERE ota_id=%s AND bola_id<>%s AND tugaydi >= %s""", (ota_id, bola_id, today)) or [{"n": 0}]
    tartib = int(rows[0]["n"] or 0) + 1
    return chegirma_tanla(admin_farzandimi(cur, bola_id), shaxsiy, tartib, s["oila_chegirma"])


def bola_rejasi(cur, bola_id, today, s=None):
    """Bola uchun to'liq holat: None (reja yo'q va obuna majburiy emas) yoki
    {manba, qoida, reja, kvota{kalit: qoldi}, obuna_kerak, takror_kuni, ...}."""
    s = s or sozlama(cur)
    yosh, _ = bola_yoshi(cur, bola_id)
    qoida = yosh_qoidasi(yosh, s["yosh_qoida"])
    fanlar, manba, obuna = samarali_fanlar(cur, bola_id, today)
    if s["obuna_majburiy"] and manba == "reja" and not _admin_sinov_profili(cur, bola_id):
        manba = ""   # obuna majburiy — muddati tugagan obuna yoki bepul reja yangi dars ochmaydi
    if not manba:
        if not s["obuna_majburiy"] or _admin_sinov_profili(cur, bola_id):
            return None
        return {"manba": "", "obuna_kerak": True, "qoida": qoida, "kvota": {}, "reja": haftalik_reja([], qoida),
                "takror_kuni": today.weekday() == 6, "xabar": "Yangi darslar uchun ota-onangiz kurs tanlasin.",
                "sinov": sinov_qoldi(cur, bola_id, [], s["sinov_dars"])}
    reja = haftalik_reja(fanlar, qoida)
    oldin, bugun = ochilgan_sonlar(cur, bola_id, today)
    kvota = bugungi_kvota(reja, today.weekday(), oldin, bugun)
    return {"manba": manba, "obuna_kerak": False, "qoida": qoida, "reja": reja, "kvota": kvota,
            "oldin": oldin, "bugun": bugun, "takror_kuni": today.weekday() == 6,
            "sinov": sinov_qoldi(cur, bola_id, reja["faol"], s["sinov_dars"]),
            "obuna": ({"tugaydi": obuna["tugaydi"].isoformat(), "faol": obuna_faolmi(obuna, today)} if obuna else None)}


def reja_korinishi(holat, today):
    """Bolaga / kun_rejasi javobiga qisqa ko'rinish."""
    if not holat:
        return None
    reja = holat["reja"]
    nomlar = {k: KURS[k]["nom"] for k in reja["faol"] + reja["navbat"]}
    return {"manba": holat["manba"], "obuna_kerak": holat["obuna_kerak"], "takror_kuni": holat["takror_kuni"],
            "bugun": holat["kvota"], "bugun_rejada": reja["hafta"][today.weekday()] if today.weekday() < 6 else [],
            "hafta": reja["hafta"], "faol": reja["faol"], "navbat": reja["navbat"], "nomlar": nomlar,
            "keyingi": {k: keyingi_kun(reja, k, today.weekday()) for k in reja["faol"]}, "xabar": holat.get("xabar", ""),
            "sinov": holat.get("sinov") or {}}


def boshlash_sababi(holat, fan_nomi, today):
    """Yangi dars ochilmasa — sabab kodi (frontend uz/ru/en tilida aytadi): obuna | takror | navbat | yoq | keyin."""
    if not holat:
        return None
    k = fan_kaliti(fan_nomi)
    if today.weekday() != 6 and k and (holat.get("sinov") or {}).get(k, 0) > 0:
        return None   # REV168: sinov darsi — olinmagan kursdan birinchi darslar bepul
    if holat["obuna_kerak"]:
        return {"sabab": "obuna", "kalit": k}
    if today.weekday() == 6:
        return {"sabab": "takror", "kalit": k}
    if not k or k not in holat["kvota"]:
        return {"sabab": "navbat" if k and k in holat["reja"]["navbat"] else "yoq", "kalit": k}
    if holat["kvota"].get(k, 0) > 0:
        return None
    return {"sabab": "keyin", "kalit": k, "keyingi": keyingi_kun(holat["reja"], k, today.weekday())}


def boshlash_xatosi(holat, fan_nomi, today):
    """Yangi dars ochish mumkinmi? Mumkin bo'lmasa — bolaga/ota-onaga tushunarli xabar, aks holda ''."""
    if not holat:
        return ""
    k = fan_kaliti(fan_nomi)
    if today.weekday() != 6 and k and (holat.get("sinov") or {}).get(k, 0) > 0:
        return ""   # REV168: sinov darsi
    if holat["obuna_kerak"]:
        return "Yangi darslar uchun ota-onangiz kurs tanlashi kerak. O‘tilgan darslarni takrorlash va o‘yinlar ochiq."
    if today.weekday() == 6:
        return "Bugun yakshanba — takrorlash kuni. O‘tilgan darslarni takrorlaymiz, yangi dars ertaga ochiladi."
    if not k or k not in holat["kvota"]:
        if k and k in holat["reja"]["navbat"]:
            return "Bu kurs navbatda — avval boshlangan kurslardan birini tugataylik."
        return "Bu kurs farzandingiz rejasida yo‘q. Ota-ona panelidan kurs qo‘shish mumkin."
    if holat["kvota"].get(k, 0) > 0:
        return ""
    kun = keyingi_kun(holat["reja"], k, today.weekday())
    return (f"Bugungi «{KURS[k]['nom']}» darsi o‘tildi yoki bugun rejada yo‘q." + (f" Keyingi dars — {kun}." if kun else "")
            + " Hozir takrorlash va o‘yinlar ochiq.")


def obuna_tolandi(cur, data, kod, summa, manba):
    """To'lov tasdiqlandi (Click/Payme/admin): obuna 30 kunga uzayadi, kurslar rejaga qo'shiladi. Ikki marta hisoblanmaydi."""
    if kod:
        cur.execute("SELECT 1 FROM bogcha_obuna_tolov WHERE kod=%s", (kod,))
        if cur.fetchone():
            return obuna_ol(cur, int(data["bola_id"]))
    today = datetime.now(TASHKENT).date()
    bola_id, ota_id = int(data["bola_id"]), int(data["ota_id"])
    fanlar = tozala_fanlar(data.get("fanlar"))
    kun = max(0, min(400, int(data["kun"]) if data.get("kun") is not None else 30))
    qulf_yil = max(0, min(5, int(data["qulf_yil"]) if data.get("qulf_yil") is not None else 1))
    cur.execute("SELECT * FROM bogcha_obuna WHERE bola_id=%s FOR UPDATE", (bola_id,))
    old = cur.fetchone()
    narx = int(data.get("narx_uzs") or 0)
    if old:
        base = max(today, old["tugaydi"])
        same_lock = bool(data.get("qulfni_saqla")) or (
            old["tarif_id"] == data.get("tarif_id") and old["narx_qulf_gacha"] and old["narx_qulf_gacha"] >= today
            and int(old["narx_uzs"]) == narx)
        if data.get("qulfni_saqla"):   # admin qo'lda uzaytirdi — ota-onaning narxi va qulfi o'zgarmaydi
            narx = int(old["narx_uzs"])
            data = {**data, "tarif_id": old["tarif_id"]}
        qulf = old["narx_qulf_gacha"] if same_lock else (_yil_qosh(today, qulf_yil) if qulf_yil else None)
        cur.execute("""UPDATE bogcha_obuna SET ota_id=%s, tarif_id=%s, kurs_soni=%s, fanlar=%s::jsonb, narx_uzs=%s,
                       narx_qulf_gacha=%s, tugaydi=%s, rozilik_at=COALESCE(%s, rozilik_at),
                       rozilik_versiya=COALESCE(%s, rozilik_versiya), yangilandi=NOW()
                       WHERE bola_id=%s""",
                    (ota_id, data.get("tarif_id"), int(data.get("kurs_soni") or len(fanlar)), json.dumps(fanlar), narx, qulf,
                     base + timedelta(days=kun), data.get("rozilik_at"), data.get("rozilik_versiya") if data.get("rozilik_at") else None, bola_id))
    else:
        qulf = _yil_qosh(today, qulf_yil) if qulf_yil else None
        cur.execute("""INSERT INTO bogcha_obuna(bola_id, ota_id, tarif_id, kurs_soni, fanlar, narx_uzs, narx_qulf_gacha, boshlandi,
                       tugaydi, rozilik_at, rozilik_versiya) VALUES(%s,%s,%s,%s,%s::jsonb,%s,%s,%s,%s,%s,%s)""",
                    (bola_id, ota_id, data.get("tarif_id"), int(data.get("kurs_soni") or len(fanlar)), json.dumps(fanlar), narx,
                     qulf, today, today + timedelta(days=kun), data.get("rozilik_at"), (data.get("rozilik_versiya") or ROZILIK_VERSIYA) if data.get("rozilik_at") else ""))
    # rejaga: oldingi tartib saqlanadi, yangi kurslar oxiriga
    order, tugagan = reja_ol(cur, bola_id)
    new_order = [k for k in order if k in fanlar] + [k for k in fanlar if k not in order]
    cur.execute("""INSERT INTO bogcha_reja(bola_id, ota_id, fanlar, tugagan) VALUES(%s,%s,%s::jsonb,%s::jsonb)
                   ON CONFLICT (bola_id) DO UPDATE SET fanlar=EXCLUDED.fanlar, ota_id=EXCLUDED.ota_id, yangilandi=NOW()""",
                (bola_id, ota_id, json.dumps(new_order), json.dumps([k for k in tugagan if k in fanlar])))
    cur.execute("""INSERT INTO bogcha_obuna_tolov(bola_id, ota_id, tarif_id, summa_uzs, manba, kod, fanlar)
                   VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb)""",
                (bola_id, ota_id, data.get("tarif_id"), int(summa or 0), manba, kod or "", json.dumps(fanlar)))
    return obuna_ol(cur, bola_id)


def _yil_qosh(d, n):
    try:
        return d.replace(year=d.year + n)
    except ValueError:   # 29-fevral
        return d.replace(year=d.year + n, day=28)


def telegram_idlari(cur, user_ids):
    """Ota-ona user_id → Telegram chat id (Telegram bilan ulangan bo'lsa), aks holda musbat user_id (bot akkaunti)."""
    out = {}
    for uid in user_ids:
        tg = None
        try:
            cur.execute("SAVEPOINT bogcha_tg")
            cur.execute("SELECT telegram_id FROM kabutar_telegram_identity WHERE user_id=%s", (uid,))
            row = cur.fetchone()
            tg = int(row["telegram_id"]) if row else None
            cur.execute("RELEASE SAVEPOINT bogcha_tg")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT bogcha_tg")
        if tg:
            out[uid] = tg
        elif uid > 0:
            out[uid] = uid
    return out


def obuna_eslatmalari(cur, today, notify):
    """REV163: obuna tugashiga 3 kun qolganda va tugagan kuni (ertasi) ota-onaga bir martadan eslatma.
    notify(cur, bola_id, matn, turi) — bola_kuzatuv xabarnomasi (sayt + Telegram)."""
    sent = 0
    cur.execute("""SELECT o.bola_id, o.tugaydi, o.narx_uzs, o.narx_qulf_gacha, u.full_name FROM bogcha_obuna o
                   LEFT JOIN users u ON u.user_id=o.bola_id
                   WHERE o.tugaydi BETWEEN %s AND %s""", (today - timedelta(days=1), today + timedelta(days=3)))
    for r in [dict(x) for x in cur.fetchall()]:
        qoldi = (r["tugaydi"] - today).days
        turi = "tugadi" if qoldi < 0 else "3kun" if qoldi <= 3 else ""
        if not turi:
            continue
        cur.execute("""INSERT INTO bogcha_eslatma(bola_id, tugaydi, turi) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING RETURNING bola_id""",
                    (r["bola_id"], r["tugaydi"], turi))
        if not cur.fetchone():
            continue
        ism = (r.get("full_name") or "Farzandingiz")[:60]
        qulf = ""
        if r.get("narx_qulf_gacha") and r["narx_qulf_gacha"] >= today:
            qulf = f" Sizning narxingiz ({int(r['narx_uzs']):,} so'm) {r['narx_qulf_gacha'].isoformat()} gacha saqlanadi.".replace(",", " ")
        if turi == "3kun":
            matn = (f"⏳ {ism}ning bog'cha kurslari obunasi {r['tugaydi'].isoformat()} da tugaydi ({max(qoldi, 0)} kun qoldi). "
                    f"Darslar to'xtamasligi uchun ota-ona panelidagi «Kurslar» bo'limidan uzaytiring.{qulf}")
        else:
            matn = (f"⌛ {ism}ning bog'cha kurslari obunasi tugadi. Takrorlash va o'yinlar ochiq, yangi darslar uchun "
                    f"ota-ona panelidagi «Kurslar» bo'limidan uzaytiring.{qulf}")
        notify(cur, int(r["bola_id"]), matn, "bogcha_obuna")
        sent += 1
    return sent


# ── API ──────────────────────────────────────────────────────────
def create_router(platform, click=None):
    router = APIRouter(tags=["bog'cha reja va obuna"])
    ready = {"ok": False}
    lock = threading.Lock()

    def db():
        conn = platform._db()
        cur = conn.cursor()
        if not ready["ok"]:
            with lock:
                if not ready["ok"]:
                    migrate(cur)
                    conn.commit()
                    ready["ok"] = True
        return conn, cur

    def run(fn):
        conn, cur = db()
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

    def uid_of(token, authorization):
        return int(platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization)))

    def admin_of(token, authorization):
        uid = uid_of(token, authorization)
        conn = platform._db()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
            if not cur.fetchone():
                raise HTTPException(403, "Faqat admin uchun")
        finally:
            cur.close()
            conn.close()
        return uid

    def today():
        return datetime.now(TASHKENT).date()

    def ota_tekshir(cur, ota_id, bola_id):
        if ota_bolami(cur, ota_id, bola_id) or adminmi(cur, ota_id):   # REV167: oila profili egasi ham
            return
        raise HTTPException(403, {"kod": "ulanmagan", "xabar": "Bu farzand sizga ulanmagan"})

    def identities(cur, uid):
        out = {"google": False, "telegram": False}
        for key, sql in (("google", "SELECT 1 FROM google_hisob WHERE user_id=%s LIMIT 1"),
                         ("telegram", "SELECT 1 FROM kabutar_telegram_identity WHERE user_id=%s LIMIT 1")):
            try:
                cur.execute("SAVEPOINT bogcha_id")
                cur.execute(sql, (uid,))
                out[key] = cur.fetchone() is not None
                cur.execute("RELEASE SAVEPOINT bogcha_id")
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT bogcha_id")
        if not out["telegram"] and uid > 0:
            out["telegram"] = True   # Telegram bot akkaunti (user_id = Telegram id)
        return out

    def tariflar(cur, faqat_faol=True):
        cur.execute("SELECT * FROM bogcha_tarif " + ("WHERE faol " if faqat_faol else "") + "ORDER BY tartib, kurs_soni, id")
        return [dict(r) for r in cur.fetchall()]

    def tolov_tizimlari():
        try:
            from modules import click_tolov as _c, payme_tolov as _p
        except ImportError:   # pragma: no cover
            from . import click_tolov as _c, payme_tolov as _p
        return {"click": _c.sozlama()["yoqilgan"], "payme": _p.sozlama()["yoqilgan"]}

    def tarif_view(t, qoida, obuna, d, cheg=None):
        n = tarif_kurs_soni(t, qoida)
        narx = narx_hisobla(t, obuna, d)
        foiz = int((cheg or {}).get("foiz") or 0)
        return {"id": t["id"], "nom": t["nom"], "kurs_soni": int(t["kurs_soni"]), "sigadi": n, "kurslar": tarif_kurslari(t),
                "toliq": int(t["kurs_soni"]) == 0, "narx_uzs": chegirmali_narx(narx["narx"], foiz), "joriy_narx": narx["joriy"],
                "asl_narx": narx["narx"], "chegirma_foiz": foiz if narx["narx"] else 0,
                "qulf": narx["qulf"], "qulf_gacha": narx["qulf_gacha"], "qulf_yil": int(t["qulf_yil"]),
                "mumkin": n <= qoida["jami"] or int(t["kurs_soni"]) == 0,
                "sabab": "" if (n <= qoida["jami"] or int(t["kurs_soni"]) == 0) else
                f"{qoida['yosh']} yoshda bir vaqtda {qoida['jami']} tagacha kurs o‘qitiladi"}

    def holat_payload(cur, ota_id, bola_id):
        d = today()
        s = sozlama(cur)
        yosh, lp = bola_yoshi(cur, bola_id)
        qoida = yosh_qoidasi(yosh, s["yosh_qoida"])
        fanlar, manba, obuna = samarali_fanlar(cur, bola_id, d)
        order, tugagan = reja_ol(cur, bola_id, bola_guruhi(cur, bola_id))
        reja = haftalik_reja(fanlar, qoida)
        oldin, bugun = ochilgan_sonlar(cur, bola_id, d)
        cur.execute("SELECT full_name FROM users WHERE user_id=%s", (bola_id,))
        ism = ((cur.fetchone() or {}).get("full_name") or "Farzandingiz")[:60]
        cheg = chegirma_ol(cur, ota_id, bola_id, d, s)
        admin_bola = cheg.get("sabab") == "admin"
        return {
            "chegirma": cheg if cheg.get("foiz") else None,
            "imtiyoz": {"admin": admin_bola, "bepul_reja": admin_bola or not s["obuna_majburiy"]},
            "bola": {"user_id": bola_id, "ism": ism, "yosh": yosh, "bogcha": lp.get("role") == "bogcha"},
            "qoida": qoida, "kurslar": [dict(KURS[k]) for k in KURS],
            "tariflar": [tarif_view(t, qoida, obuna, d, cheg) for t in tariflar(cur)],
            "obuna": ({"tarif_id": obuna["tarif_id"], "fanlar": obuna["fanlar"], "narx_uzs": int(obuna["narx_uzs"]),
                       "narx_qulf_gacha": obuna["narx_qulf_gacha"].isoformat() if obuna["narx_qulf_gacha"] else None,
                       "boshlandi": obuna["boshlandi"].isoformat(), "tugaydi": obuna["tugaydi"].isoformat(),
                       "faol": obuna_faolmi(obuna, d), "qoldi_kun": (obuna["tugaydi"] - d).days} if obuna else None),
            "reja": {**reja, "manba": manba, "tanlangan": order, "tugagan": tugagan, "nomlar": {k: KURS[k]["nom"] for k in KURS},
                     "bugun_kuni": d.weekday(), "kvota": bugungi_kvota(reja, d.weekday(), oldin, bugun) if manba else {},
                     "oldin": oldin, "bugun": bugun, "hafta_boshi": hafta_boshi(d).isoformat()},
            "sozlama": {"obuna_majburiy": s["obuna_majburiy"], "telegram_majburiy": s["telegram_majburiy"], "tun": s["tun"]},
            "ulanish": identities(cur, ota_id),
            "google_yoqilgan": bool(getattr(platform, "GOOGLE_CLIENT_ID", "") and getattr(platform, "GOOGLE_CLIENT_SECRET", "")),
            "tolov": tolov_tizimlari(),
            "rozilik": {"versiya": ROZILIK_VERSIYA, "bandlar": ROZILIK_BANDLAR,
                        "berilgan": bool(obuna and obuna.get("rozilik_versiya") == ROZILIK_VERSIYA and obuna.get("rozilik_at"))},
        }

    @router.get("/api/bogcha/holat")
    def holat(bola_id: int, token: str = None, authorization: str = Header(None)):
        uid = uid_of(token, authorization)

        def go(cur):
            ota_tekshir(cur, uid, bola_id)
            return holat_payload(cur, uid, bola_id)
        return run(go)

    @router.put("/api/bogcha/reja")
    def reja_saqla(body: dict = Body(...), token: str = None, authorization: str = Header(None)):
        uid = uid_of(token or body.get("token"), authorization)
        bola_id = int(body.get("bola_id") or 0)
        fanlar = tozala_fanlar(body.get("fanlar"))

        def go(cur):
            ota_tekshir(cur, uid, bola_id)
            d = today()
            s = sozlama(cur)
            obuna = obuna_ol(cur, bola_id)
            if obuna_faolmi(obuna, d):
                extra = [k for k in fanlar if k not in obuna["fanlar"]]
                if extra:
                    raise HTTPException(409, {"kod": "obunada_yoq", "xabar": "Obunada yo‘q kurs qo‘shib bo‘lmaydi: "
                                              + ", ".join(KURS[k]["nom"] for k in extra) + ". Tarifni o‘zgartiring yoki kurs almashtiring."})
            elif s["obuna_majburiy"] and not admin_farzandimi(cur, bola_id):   # REV167: admin farzandi — bepul
                raise HTTPException(402, {"kod": "obuna_kerak", "xabar": "Avval tarif tanlab, to‘lov qiling."})
            _, tugagan = reja_ol(cur, bola_id)
            cur.execute("""INSERT INTO bogcha_reja(bola_id, ota_id, fanlar, tugagan) VALUES(%s,%s,%s::jsonb,%s::jsonb)
                           ON CONFLICT (bola_id) DO UPDATE SET fanlar=EXCLUDED.fanlar, ota_id=EXCLUDED.ota_id, yangilandi=NOW()""",
                        (bola_id, uid, json.dumps(fanlar), json.dumps([k for k in tugagan if k in fanlar])))
            return holat_payload(cur, uid, bola_id)
        return run(go)

    @router.post("/api/bogcha/reja/tugatildi")
    def reja_tugatildi(body: dict = Body(...), token: str = None, authorization: str = Header(None)):
        """Kurs tugatildi (yoki qaytadan ochish): navbatdagi kurs o'zi ochiladi."""
        uid = uid_of(token or body.get("token"), authorization)
        bola_id = int(body.get("bola_id") or 0)
        fan = str(body.get("fan") or "")
        qaytar = bool(body.get("qaytar"))
        if fan not in KURS:
            raise HTTPException(422, "Kurs topilmadi")

        def go(cur):
            ota_tekshir(cur, uid, bola_id)
            d = today()
            obuna = obuna_ol(cur, bola_id)
            if obuna_faolmi(obuna, d):
                if fan not in obuna["fanlar"]:
                    raise HTTPException(409, {"kod": "obunada_yoq", "xabar": "Bu kurs obunada yo‘q."})
            elif sozlama(cur)["obuna_majburiy"] and not admin_farzandimi(cur, bola_id):
                raise HTTPException(402, {"kod": "obuna_kerak", "xabar": "Avval tarif tanlab, to‘lov qiling."})
            order, tugagan = reja_ol(cur, bola_id)
            tugagan = [k for k in tugagan if k != fan] if qaytar else (tugagan + [fan] if fan not in tugagan else tugagan)
            if qaytar:   # avtomatik «tugadi» belgisi ham olinadi
                cur.execute("""UPDATE bogcha_reja SET avto_tugagan = avto_tugagan - %s WHERE bola_id=%s""", (fan, bola_id))
            if fan not in order:
                order.append(fan)
            cur.execute("""INSERT INTO bogcha_reja(bola_id, ota_id, fanlar, tugagan) VALUES(%s,%s,%s::jsonb,%s::jsonb)
                           ON CONFLICT (bola_id) DO UPDATE SET fanlar=EXCLUDED.fanlar, tugagan=EXCLUDED.tugagan, yangilandi=NOW()""",
                        (bola_id, uid, json.dumps(order), json.dumps(tugagan)))
            return holat_payload(cur, uid, bola_id)
        return run(go)

    @router.post("/api/bogcha/obuna/buyurtma")
    def obuna_buyurtma(body: dict = Body(...), token: str = None, authorization: str = Header(None)):
        uid = uid_of(token or body.get("token"), authorization)
        bola_id = int(body.get("bola_id") or 0)
        tarif_id = int(body.get("tarif_id") or 0)
        fanlar = tozala_fanlar(body.get("fanlar"))
        if body.get("rozilik") is not True:
            raise HTTPException(422, {"kod": "rozilik", "xabar": "Shartlar bilan tanishib, «Roziman» belgisini qo‘ying."})

        def go(cur):
            ota_tekshir(cur, uid, bola_id)
            d = today()
            s = sozlama(cur)
            ids = identities(cur, uid)
            google_on = bool(getattr(platform, "GOOGLE_CLIENT_ID", "") and getattr(platform, "GOOGLE_CLIENT_SECRET", ""))
            admin_bola = admin_farzandimi(cur, bola_id)   # REV167: admin farzandi — to'lov yo'q, ulanish talab qilinmaydi
            if google_on and not ids["google"] and not admin_bola:
                raise HTTPException(428, {"kod": "google", "xabar": "To‘lovdan oldin Gmail akkauntingizni ulang (Akkaunt → Gmail ulash)."})
            if s["telegram_majburiy"] and not ids["telegram"] and not admin_bola:
                raise HTTPException(428, {"kod": "telegram", "xabar": "To‘lovdan oldin Telegram’ni ulang — farzandingiz haqidagi xabarlar shu yerga keladi."})
            cur.execute("SELECT * FROM bogcha_tarif WHERE id=%s AND faol", (tarif_id,))
            t = cur.fetchone()
            if not t:
                raise HTTPException(404, {"kod": "tarif_yoq", "xabar": "Tarif topilmadi yoki yopilgan"})
            t = dict(t)
            yosh, _ = bola_yoshi(cur, bola_id)
            qoida = yosh_qoidasi(yosh, s["yosh_qoida"])
            err = tanlov_xatosi(fanlar, t, qoida)
            if err:
                raise HTTPException(422, {"kod": tanlov_kodi(fanlar, t, qoida), "xabar": err})
            obuna = obuna_ol(cur, bola_id)
            narx = narx_hisobla(t, obuna, d)["narx"]          # asl (qulflangan) narx — obunada shu saqlanadi
            cheg = chegirma_ol(cur, uid, bola_id, d, s)       # REV167: admin farzandi / shaxsiy / oila chegirmasi
            tolov = chegirmali_narx(narx, cheg["foiz"])        # ota-ona to'laydigani
            data = {"bola_id": bola_id, "ota_id": uid, "tarif_id": int(t["id"]), "kurs_soni": int(t["kurs_soni"]),
                    "fanlar": fanlar, "narx_uzs": narx, "qulf_yil": int(t["qulf_yil"]), "kun": 30,
                    "rozilik_at": datetime.now(timezone.utc).isoformat(), "rozilik_versiya": ROZILIK_VERSIYA,
                    "chegirma": cheg if cheg["foiz"] else None}
            if tolov <= 0:   # bepul (tarif yoki 100% chegirma) — darhol ochiladi (faqat tugashiga 3 kun qolganda uzaytiriladi)
                if obuna_faolmi(obuna, d) and obuna["tugaydi"] > d + timedelta(days=3):
                    data["kun"] = 0   # hali faol — faqat kurslar yangilanadi, muddat qo'shilmaydi
                if narx <= 0:
                    data["qulf_yil"] = 0
                o = obuna_tolandi(cur, data, "", 0, "bepul" if narx <= 0 else f"chegirma:{cheg['sabab']}")
                return {"tolandi": True, "obuna": {"tugaydi": o["tugaydi"].isoformat()}, "holat": holat_payload(cur, uid, bola_id)}
            if click is None:
                raise HTTPException(503, {"kod": "tolov_yoq", "xabar": "To‘lov tizimi hali ulanmagan"})
            return click.obuna_buyurtma(cur, uid, tolov, data, str(body.get("return_url") or ""))
        return run(go)

    @router.get("/api/bogcha/obuna/holat/{kod}")
    def obuna_holat(kod: str, token: str = None, authorization: str = Header(None)):
        uid = uid_of(token, authorization)

        def go(cur):
            try:
                cur.execute("SAVEPOINT bogcha_holat")
                cur.execute("SELECT status, amount_uzs FROM click_tolovlar WHERE merchant_trans_id=%s AND user_id=%s",
                            (str(kod)[:64], uid))
                row = cur.fetchone()
                cur.execute("RELEASE SAVEPOINT bogcha_holat")
            except Exception:   # to'lov jadvali hali yaratilmagan
                cur.execute("ROLLBACK TO SAVEPOINT bogcha_holat")
                row = None
            if not row:
                raise HTTPException(404, "To‘lov topilmadi")
            return {"status": row["status"], "amount_uzs": row["amount_uzs"]}
        return run(go)

    # ── Admin ──
    @router.get("/api/admin/bogcha")
    def admin_holat(token: str = None, authorization: str = Header(None)):
        admin_of(token, authorization)

        def go(cur):
            s = sozlama(cur)
            ts = tariflar(cur, faqat_faol=False)
            d = today()
            cur.execute("""SELECT o.*, b.full_name AS bola, p.full_name AS ota FROM bogcha_obuna o
                           LEFT JOIN users b ON b.user_id=o.bola_id LEFT JOIN users p ON p.user_id=o.ota_id
                           ORDER BY o.yangilandi DESC LIMIT 300""")
            obunalar = []
            stat = {}
            for r in cur.fetchall():
                faol = r["tugaydi"] >= d
                obunalar.append({"bola_id": r["bola_id"], "bola": r["bola"] or "", "ota_id": r["ota_id"], "ota": r["ota"] or "",
                                 "tarif_id": r["tarif_id"], "fanlar": tozala_fanlar(_json(r["fanlar"], [])),
                                 "narx_uzs": int(r["narx_uzs"]), "tugaydi": r["tugaydi"].isoformat(), "faol": faol,
                                 "narx_qulf_gacha": r["narx_qulf_gacha"].isoformat() if r["narx_qulf_gacha"] else None})
                if faol:
                    key = (r["tarif_id"], int(r["narx_uzs"]))
                    stat[key] = stat.get(key, 0) + 1
            cur.execute("SELECT COALESCE(SUM(summa_uzs),0) AS s, COUNT(*) AS n FROM bogcha_obuna_tolov WHERE tolandi_at > NOW() - INTERVAL '30 days'")
            oy = cur.fetchone() or {}
            cur.execute("SELECT * FROM bogcha_tarif_tarix ORDER BY id DESC LIMIT 50")
            tarix = [{"tarif_id": r["tarif_id"], "eski": r["eski_narx"], "yangi": r["yangi_narx"], "qulf_yil": r["qulf_yil"],
                      "sana": r["ozgardi_at"].isoformat()} for r in cur.fetchall()]
            return {"tariflar": [{**{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in t.items()}, "kurslar": tarif_kurslari(t),
                                  "narxlar": [{"narx_uzs": n, "soni": c} for (tid, n), c in sorted(stat.items(), key=lambda x: (x[0][0] or 0, x[0][1])) if tid == t["id"]]}
                                 for t in ts],
                    "sozlama": s, "yosh_qoida_default": YOSH_QOIDA,
                    "yosh_qoida": {str(a): yosh_qoidasi(a, s["yosh_qoida"]) for a in range(2, 8)},
                    "obunalar": obunalar, "oxirgi_30_kun": {"summa": int(oy.get("s") or 0), "soni": int(oy.get("n") or 0)},
                    "tarix": tarix, "kurslar": [dict(KURS[k]) for k in KURS], "tolov": tolov_tizimlari(),
                    "chegirmalar": chegirmalar_royxati(cur, d)}
        return run(go)

    def chegirmalar_royxati(cur, d):
        rows = _savepoint_query(cur, "bogcha_cheg_list", """SELECT c.*, u.full_name AS ism FROM bogcha_chegirma c
                                   LEFT JOIN users u ON u.user_id=c.user_id WHERE c.ochirildi IS NULL ORDER BY c.id DESC LIMIT 300""", ()) or []
        return [{"id": int(r["id"]), "turi": r["turi"], "user_id": int(r["user_id"]), "ism": r["ism"] or "", "foiz": int(r["foiz"]),
                 "gacha": r["gacha"].isoformat() if r["gacha"] else None, "izoh": r["izoh"] or "",
                 "faol": not r["gacha"] or r["gacha"] >= d} for r in rows]

    @router.get("/api/admin/bogcha/qidir")
    def admin_qidir(q: str = "", token: str = None, authorization: str = Header(None)):
        """REV167: chegirma berish uchun ota-ona yoki bolani topish (ism yoki ID). Ota-onaning farzandlari ham chiqadi."""
        admin_of(token, authorization)
        text = " ".join(str(q or "").split())[:60]
        if len(text) < 2:
            return {"natija": []}

        def go(cur):
            args = [f"%{text}%"]
            sql = "SELECT user_id, full_name, role, kabutar_learning_profile AS lp FROM users WHERE full_name ILIKE %s"
            if text.lstrip("-").isdigit():
                sql += " OR user_id=%s"
                args.append(int(text))
            rows = _savepoint_query(cur, "bogcha_qidir", sql + " ORDER BY user_id DESC LIMIT 20", tuple(args))
            if rows is None:
                rows = _savepoint_query(cur, "bogcha_qidir2", "SELECT user_id, full_name, role, NULL::jsonb AS lp FROM users WHERE full_name ILIKE %s"
                                        + (" OR user_id=%s" if len(args) > 1 else "") + " ORDER BY user_id DESC LIMIT 20", tuple(args)) or []
            out = []
            for r in rows:
                lp = _json(r["lp"], {}) if r.get("lp") is not None else {}
                uid = int(r["user_id"])
                bolalar = _savepoint_query(cur, "bogcha_qidir_b", """SELECT DISTINCT u.user_id, u.full_name FROM users u WHERE u.user_id IN (
                                               SELECT child_id FROM parent_child WHERE parent_id=%s
                                               UNION SELECT profile_user_id FROM kabutar_family_profiles WHERE owner_user_id=%s AND removed_at IS NULL)
                                               LIMIT 12""", (uid, uid)) or []
                out.append({"user_id": uid, "ism": r["full_name"] or "", "bola": lp.get("role") == "bogcha",
                            "bolalar": [{"user_id": int(b["user_id"]), "ism": b["full_name"] or ""} for b in bolalar]})
            return {"natija": out}
        return run(go)

    @router.post("/api/admin/bogcha/chegirma")
    def admin_chegirma(body: dict = Body(...), token: str = None, authorization: str = Header(None)):
        """REV167: shaxsiy chegirma — ota-onaga (barcha farzandlari) yoki bitta bolaga, foiz 1–100, muddat ixtiyoriy."""
        aid = admin_of(token or body.get("token"), authorization)
        turi = "ota" if body.get("turi") == "ota" else "bola"
        try:
            user_id = int(body.get("user_id"))
            foiz = int(body.get("foiz"))
        except (TypeError, ValueError):
            raise HTTPException(422, "ID va foizni to‘g‘ri yozing")
        if not 1 <= foiz <= 100:
            raise HTTPException(422, "Chegirma 1–100 foiz bo‘lishi kerak")
        gacha = None
        if body.get("gacha"):
            try:
                gacha = date.fromisoformat(str(body["gacha"])[:10])
            except ValueError:
                raise HTTPException(422, "Sana noto‘g‘ri")
        izoh = " ".join(str(body.get("izoh") or "").split())[:200]

        def go(cur):
            cur.execute("SELECT 1 FROM users WHERE user_id=%s", (user_id,))
            if not cur.fetchone():
                raise HTTPException(404, "Foydalanuvchi topilmadi")
            # shu odamga oldingi chegirma bo'lsa — yangisi uning o'rnini oladi
            cur.execute("UPDATE bogcha_chegirma SET ochirildi=NOW() WHERE turi=%s AND user_id=%s AND ochirildi IS NULL", (turi, user_id))
            cur.execute("""INSERT INTO bogcha_chegirma(turi, user_id, foiz, gacha, izoh, admin_id) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (turi, user_id, foiz, gacha, izoh, aid))
            return {"ok": True, "id": int(cur.fetchone()["id"])}
        return run(go)

    @router.delete("/api/admin/bogcha/chegirma/{cid}")
    def admin_chegirma_ochir(cid: int, token: str = None, authorization: str = Header(None)):
        admin_of(token, authorization)

        def go(cur):
            cur.execute("UPDATE bogcha_chegirma SET ochirildi=NOW() WHERE id=%s AND ochirildi IS NULL RETURNING id", (cid,))
            if not cur.fetchone():
                raise HTTPException(404, "Chegirma topilmadi")
            return {"ok": True}
        return run(go)

    @router.post("/api/admin/bogcha/tarif")
    def admin_tarif(body: dict = Body(...), token: str = None, authorization: str = Header(None)):
        aid = admin_of(token or body.get("token"), authorization)
        nom = " ".join(str(body.get("nom") or "").split())[:80]
        if not nom:
            raise HTTPException(422, "Tarif nomini yozing")
        try:
            soni = int(body.get("kurs_soni") or 0)
            narx = int(body.get("narx_uzs") or 0)
            qulf = int(body.get("qulf_yil") if body.get("qulf_yil") is not None else 1)
            tartib = int(body.get("tartib") or 0)
        except (TypeError, ValueError):
            raise HTTPException(422, "Raqamlar noto‘g‘ri")
        if not 0 <= soni <= 14 or not 0 <= narx <= 100_000_000 or not 0 <= qulf <= 3:
            raise HTTPException(422, "Kurs soni 0–14, narx 0–100 000 000, narx qulfi 0–3 yil bo‘lishi kerak")
        faol = bool(body.get("faol", True))
        kurslar = tozala_fanlar(body.get("kurslar"))

        def go(cur):
            tid = int(body.get("id") or 0)
            if tid:
                cur.execute("SELECT narx_uzs FROM bogcha_tarif WHERE id=%s FOR UPDATE", (tid,))
                old = cur.fetchone()
                if not old:
                    raise HTTPException(404, "Tarif topilmadi")
                cur.execute("""UPDATE bogcha_tarif SET nom=%s, kurs_soni=%s, narx_uzs=%s, qulf_yil=%s, faol=%s, tartib=%s,
                               kurslar=%s::jsonb, yangilangan_at=NOW() WHERE id=%s""",
                            (nom, soni, narx, qulf, faol, tartib, json.dumps(kurslar), tid))
                if int(old["narx_uzs"]) != narx:
                    cur.execute("INSERT INTO bogcha_tarif_tarix(tarif_id, eski_narx, yangi_narx, qulf_yil, admin_id) VALUES(%s,%s,%s,%s,%s)",
                                (tid, int(old["narx_uzs"]), narx, qulf, aid))
            else:
                cur.execute("""INSERT INTO bogcha_tarif(nom,kurs_soni,narx_uzs,qulf_yil,faol,tartib,kurslar)
                               VALUES(%s,%s,%s,%s,%s,%s,%s::jsonb) RETURNING id""", (nom, soni, narx, qulf, faol, tartib, json.dumps(kurslar)))
                tid = cur.fetchone()["id"]
                cur.execute("INSERT INTO bogcha_tarif_tarix(tarif_id, eski_narx, yangi_narx, qulf_yil, admin_id) VALUES(%s,NULL,%s,%s,%s)",
                            (tid, narx, qulf, aid))
            return {"ok": True, "id": tid}
        return run(go)

    @router.put("/api/admin/bogcha/sozlama")
    def admin_sozlama(body: dict = Body(...), token: str = None, authorization: str = Header(None)):
        admin_of(token or body.get("token"), authorization)
        yq = {}
        for a, v in (body.get("yosh_qoida") or {}).items():
            if str(a) in {str(x) for x in range(2, 8)} and isinstance(v, dict):
                row = {}
                for k in ("kun", "shanba", "jami", "til"):
                    try:
                        row[k] = int(str(v.get(k, "")).strip())
                    except ValueError:
                        continue
                yq[str(a)] = row
        value = {"obuna_majburiy": bool(body.get("obuna_majburiy")), "telegram_majburiy": body.get("telegram_majburiy", True) is not False,
                 "yosh_qoida": yq}

        def go(cur):
            old = sozlama(cur)   # REV167: yuborilmagan bo'limlar (tun, oila chegirmasi) o'zgarmaydi
            value["tun"] = tun_sozlama(body["tun"]) if isinstance(body.get("tun"), dict) else old["tun"]
            value["oila_chegirma"] = (oila_chegirma_sozlama(body["oila_chegirma"]) if isinstance(body.get("oila_chegirma"), dict)
                                      else old["oila_chegirma"])
            value["sinov_dars"] = sinov_dars_soni(body["sinov_dars"]) if body.get("sinov_dars") is not None else old["sinov_dars"]
            cur.execute("""INSERT INTO bogcha_sozlama(kalit, qiymat) VALUES('umumiy', %s::jsonb)
                           ON CONFLICT (kalit) DO UPDATE SET qiymat=EXCLUDED.qiymat""", (json.dumps(value),))
            return {"ok": True, "sozlama": sozlama(cur)}
        return run(go)

    @router.post("/api/admin/bogcha/obuna/faollashtir")
    def admin_faollashtir(body: dict = Body(...), token: str = None, authorization: str = Header(None)):
        """Admin qo'lda (naqd to'lov, sovg'a, sinov): N kunga obuna."""
        aid = admin_of(token or body.get("token"), authorization)
        bola_id = int(body.get("bola_id") or 0)
        fanlar = tozala_fanlar(body.get("fanlar"))
        if not bola_id or not fanlar:
            raise HTTPException(422, "Bola va kamida bitta kurs kerak")

        def go(cur):
            cur.execute("SELECT parent_id FROM parent_child WHERE child_id=%s ORDER BY id LIMIT 1", (bola_id,))
            row = cur.fetchone()
            ota = int(row["parent_id"]) if row else aid
            tarif_id = int(body.get("tarif_id") or 0) or None
            narx = 0
            if tarif_id:
                cur.execute("SELECT narx_uzs, qulf_yil, kurs_soni FROM bogcha_tarif WHERE id=%s", (tarif_id,))
                t = cur.fetchone()
                narx = int(t["narx_uzs"]) if t else 0
            cur.execute("SELECT 1 FROM bogcha_obuna WHERE bola_id=%s", (bola_id,))
            bor = cur.fetchone() is not None
            o = obuna_tolandi(cur, {"bola_id": bola_id, "ota_id": ota, "tarif_id": tarif_id, "kurs_soni": len(fanlar), "fanlar": fanlar,
                                    "narx_uzs": narx, "qulf_yil": 0, "kun": int(body.get("kun") or 30),
                                    "qulfni_saqla": bor and not tarif_id}, "", 0, f"admin:{aid}")
            return {"ok": True, "tugaydi": o["tugaydi"].isoformat()}
        return run(go)

    # To'lov tizimlari (Click/Payme) shu funksiyani chaqiradi
    platform._bogcha_obuna_tolandi = obuna_tolandi
    platform._bogcha_rejasi = bola_rejasi
    return router

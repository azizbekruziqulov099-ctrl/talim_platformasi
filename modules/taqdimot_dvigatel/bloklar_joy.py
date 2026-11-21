"""Joylashuvlar (layout) va taqdimot «dizayn DNK»si.

Har taqdimot boshida bir marta tanlanadi (urug'ga bog'liq, shuning uchun ikki taqdimot bir xil chiqmaydi):
- sarlavha qatori ko'rinishi (chap, chiziq, tasma, markaz, raqam);
- karta ko'rinishi (oila uslubi, yon chiziq, chiziqli, soyali);
- titul va bo'lim slaydi dizayni.

Har kontent slaydi uchun joylashuv: AI miyada "joylashuv" yozsa — o'sha (mazmunga to'g'ri kelsa), aks holda dvigatel
mazmunga mos nomzodlardan tanlaydi, ketma-ket bir xilini qo'ymaydi va kam ishlatilganini afzal ko'radi.
"""
from __future__ import annotations

from . import bloklar as B
from . import chizma as CH
from . import formula as FM
from . import rasmlar as RS
from .sahna import W, H
from .uslub import och, toq, aralash

M, CT, CB = B.M, B.CT, B.CB

JOYLASHUVLAR = {
    "avto": "dvigatel o'zi tanlaydi",
    "standart": "elementlar soniga qarab katakchalar",
    "rasm_ong": "matn chapda, rasm o'ngda",
    "rasm_chap": "rasm chapda, matn o'ngda",
    "rasm_panel": "yarim slayd rangli panel ustida katta rasm, matn yonida",
    "rasm_katta": "katta rasm slayd chetiga chiqib turadi, matn kartada",
    "markaz": "bitta katta g'oya o'rtada (qisqa ta'rif, qoida, savol)",
    "ustunlar": "2–3 ta qisqa element yonma-yon raqamli ustunlarda",
    "qatorlar": "2–3 ta element ketma-ket qatorlarda",
    "yon_sarlavha": "sarlavha chapdagi ustunda, mazmun o'ngda",
    "ustma": "2–3 element ustma-ust: qisqasi (qoida, ta'rif, formula) tepada keng tasmada, asosiysi ostida",
    "asosiy_yon": "asosiy element (misol, jadval) keng, qisqa element yonida tor ustunda",
    "chizma_chap": "misol/masala: chizma chapda katta, shart va qadamlar o'ngda",
    "qadam_qator": "misol/masala: shart tepada, yechim qadamlari chapdan o'ngga kartalarda, javob oxirida",
    "rasm_tepa": "rasm slayd tepasida keng rangli tasmada sarlavha bilan, matn ostida",
}
SARLAVHA_TURLARI = ["chap", "chiziq", "tasma", "markaz", "raqam"]
KART_TURLARI = ["oila", "yon", "chiziq", "soya"]
TITUL_SONI = 6
BOLIM_SONI = 5
NOMLAR = {
    "titul": ["Oddiy", "Panel", "Markaz", "Diagonal", "Katta rasm", "Ramka"],
    "bolim": ["Oddiy", "Panel", "Markaz", "Katta raqam", "Rasmli"],
    "sarlavha": {"chap": "Chapda", "chiziq": "Chiziqli", "tasma": "Tasma", "markaz": "Markazda", "raqam": "Raqamli"},
    "kart": {"oila": "Uslubdagidek", "yon": "Yon chiziq", "chiziq": "Ramkali", "soya": "Soyali"},
}


def dizayn_royxati():
    """Studiya uchun: qo'lda tanlash mumkin bo'lgan dizayn variantlari."""
    return {"titul": [{"kod": i, "nom": n} for i, n in enumerate(NOMLAR["titul"])],
            "bolim": [{"kod": i, "nom": n} for i, n in enumerate(NOMLAR["bolim"])],
            "sarlavha": [{"kod": k, "nom": n} for k, n in NOMLAR["sarlavha"].items()],
            "kart": [{"kod": k, "nom": n} for k, n in NOMLAR["kart"].items()]}

SODDA = {"tarif", "qoida", "teorema", "matn", "savol", "formula"}
_YON_MUMKIN = SODDA | {"misol", "masala", "xossalar", "hayotiy", "chizma", "rasm", "parcha", "iqtibos", "dialog", "raqamlar"}


# ------------------------------------------------------------------ dizayn DNK
def dnk(rng, u, berilgan=None) -> dict:
    """Taqdimot bo'yi o'zgarmaydigan dizayn tanlovlari."""
    b = dict(berilgan or {})
    afzal = {"minimal": ["chap", "raqam", "chiziq"], "daftar": ["chiziq", "tasma", "chap"], "doska": ["chap", "markaz", "chiziq"],
             "shisha": ["markaz", "chap", "tasma"], "tun": ["chap", "markaz", "raqam"], "yulduz": ["markaz", "chap", "raqam"],
             "akademik": ["chiziq", "raqam", "chap"], "jurnal": ["raqam", "chiziq", "chap"]}.get(u.oila, SARLAVHA_TURLARI)
    out = {
        # Gamma'dagidek: mazmun fon ustidagi bitta katta karta ichida (yorug' uslublarning bir qismida)
        "sahifa": b.get("sahifa") if b.get("sahifa") in ("oddiy", "karta") else ("karta" if not u.qorongi and rng.random() < 0.35 else "oddiy"),
        "sarlavha": b.get("sarlavha") if b.get("sarlavha") in SARLAVHA_TURLARI else rng.choice(afzal + [rng.choice(SARLAVHA_TURLARI)]),
        "kart": b.get("kart") if b.get("kart") in KART_TURLARI else ("oila" if u.qorongi or u.oila == "shisha" else rng.choice(KART_TURLARI)),
        "titul": int(b["titul"]) % TITUL_SONI if str(b.get("titul", "")).isdigit() else rng.randrange(TITUL_SONI),
        "bolim": int(b["bolim"]) % BOLIM_SONI if str(b.get("bolim", "")).isdigit() else rng.randrange(BOLIM_SONI),
    }
    return out


# ------------------------------------------------------------------ yordamchilar
def _rasmli(k, e) -> bool:
    key = e.get("rasm")
    return bool(key and k.rasm_bor(key))


def _illyustr(k, e) -> bool:
    return _rasmli(k, e) and RS.malumot(e["rasm"]).get("tur") == "rasm"


def _matn_uzunligi(e) -> int:
    n = len(e.get("matn") or "") + len(e.get("shart") or "")
    for b in e.get("bandlar") or []:
        if isinstance(b, dict):
            n += len(b.get("matn") or "") + len(b.get("nom") or "")
    return n


def _vizual_el(k, els):
    """Slayddagi asosiy rasm elementi (alohida «rasm» elementi; matnsiz «hayotiy»)."""
    for e in els:
        if e["tur"] == "rasm" and _rasmli(k, e) and not e.get("chizma"):
            return e
    return None


_QISQA = SODDA | {"formula"}
_KENG_FAQAT = {"taqqoslash", "lugat", "xarita", "vaqt_chizigi", "galereya", "guruhlash", "moslash", "togri_notogri", "bosh_joy",
               "tajriba", "jarayon", "rasmda_nima"}


def _qisqami(e) -> bool:
    return e["tur"] in _QISQA and not e.get("chizma") and not e.get("rasm") and not e.get("bandlar") and _matn_uzunligi(e) <= 240


def _jadval_ixcham(e) -> bool:
    return e["tur"] == "jadval" and len(e.get("ustunlar") or []) <= 4 and len(e.get("qatorlar") or []) <= 7


def nomzodlar(k, els):
    matnlar = [e for e in els if e["tur"] != "eslatma"]
    vis = _vizual_el(k, matnlar)
    if vis is not None:
        matnlar = [e for e in matnlar if e is not vis]
    n = len(matnlar)
    if vis is not None:
        ill = _illyustr(k, vis)
        if n == 0:
            return (["rasm_katta", "rasm_panel"] if ill else ["standart"]), vis, matnlar
        oddiy = all(e["tur"] in SODDA | {"misol", "masala", "xossalar"} and not e.get("chizma") and not e.get("rasm") for e in matnlar)
        if n <= 2 and oddiy:
            c = ["rasm_ong", "rasm_chap"]
            if ill:
                c += ["rasm_panel"] + (["rasm_katta"] if n == 1 and _matn_uzunligi(matnlar[0]) < 420 else [])
                if sum(_matn_uzunligi(e) for e in matnlar) <= 420:
                    c.append("rasm_tepa")
            return c, vis, matnlar
        return ["standart"], vis, matnlar
    if n == 1:
        e = matnlar[0]
        if e["tur"] in SODDA and not e.get("chizma") and not e.get("rasm") and not e.get("bandlar") and 0 < _matn_uzunligi(e) <= 300:
            return ["markaz", "yon_sarlavha", "standart"], None, matnlar
        if e["tur"] in ("misol", "masala") and (e.get("chizma") or e.get("rasm")):
            return ["chizma_chap", "yon_sarlavha", "standart"], None, matnlar
        qs = e.get("qadamlar") or []
        if e["tur"] in ("misol", "masala") and 2 <= len(qs) <= 5 and all(len(q) <= 110 for q in qs) and len(e.get("shart") or e.get("matn") or "") <= 360:
            return ["qadam_qator", "yon_sarlavha", "standart"], None, matnlar
        if e["tur"] == "xossalar":
            # aqlli ro'yxat to'liq kenglikda 8 xil bo'ladi; chap sarlavha bilan — kartalar, belgili, raqamli, zinapoya...
            from .bloklar_royxat import KENG_KERAK
            return (["keng"] if e.get("korinish") in KENG_KERAK else ["keng", "yon_sarlavha"]), None, matnlar
        if e["tur"] in _YON_MUMKIN or _jadval_ixcham(e):
            return ["yon_sarlavha", "standart"], None, matnlar
        return ["standart"], None, matnlar
    if 2 <= n <= 3 and all(e["tur"] in SODDA and not e.get("chizma") and not e.get("rasm") and not e.get("bandlar") for e in matnlar):
        if all(_matn_uzunligi(e) <= 260 for e in matnlar):
            return ["ustunlar", "qatorlar", "standart"], None, matnlar
        return ["qatorlar", "standart"], None, matnlar
    qisqalar = [e for e in matnlar if _qisqami(e)]
    if n == 2 and len(qisqalar) == 1:
        asosiy = next(e for e in matnlar if e is not qisqalar[0])
        if asosiy["tur"] in _KENG_FAQAT:
            return ["ustma", "standart"], None, matnlar
        c = ["ustma", "asosiy_yon", "standart"]
        if asosiy["tur"] in _YON_MUMKIN | {"jadval"} and not (asosiy.get("chizma") and asosiy["tur"] in ("misol", "masala")):
            c.append("yon_sarlavha")
        return c, None, matnlar
    if n == 3 and len(qisqalar) >= 1 and not any(e["tur"] in _KENG_FAQAT for e in matnlar):
        return ["ustma", "standart"], None, matnlar
    return ["standart"], None, matnlar


def tanla(k, d, els):
    c, vis, matnlar = nomzodlar(k, els)
    xohish = (d.get("joylashuv") or "avto").strip().lower()
    holat = k.deck.setdefault("_joy", {"oxirgi": None, "sanoq": {}})
    if xohish in c:
        joy = xohish
    else:
        sanoq = holat["sanoq"]
        tanlov = [x for x in c if x != holat["oxirgi"]] or c
        eng_kam = min(sanoq.get(x, 0) for x in tanlov)
        tanlov = [x for x in tanlov if sanoq.get(x, 0) == eng_kam]
        # «standart» faqat boshqa iloj bo'lmasa (yoki oz ishlatilgan bo'lsa)
        if len(tanlov) > 1 and "standart" in tanlov:
            tanlov.remove("standart")
        joy = k.rng.choice(tanlov)
    holat["oxirgi"] = joy
    holat["sanoq"][joy] = holat["sanoq"].get(joy, 0) + 1
    return joy, vis, matnlar


# ------------------------------------------------------------------ kontent slayd
TOLIQ_JOY = {"rasm_panel", "yon_sarlavha", "rasm_katta", "rasm_tepa"}  # slayd chetigacha chiziladi — sahifa kartasi kerak emas


def sahifa_kartasi(k):
    """Gamma uslubi: mazmun ostida slaydning katta oq kartasi."""
    if k.deck.get("sahifa") != "karta" or k.u.qorongi:
        return
    k.s.rect(22, 14, W - 44, H - 28, fill="#FFFFFF", op=0.9, r=28, sh=1)


def karta_korinishi(k, els):
    """Slayddagi yorliqli kartalar ko'rinishi: karta, chiziq, blok, qog'oz — taqdimot bo'yi aylanib turadi."""
    fix = ((k.deck.get("_soz") or {}).get("karta"))
    if fix and not (fix == "qogoz" and k.u.qorongi):
        return fix
    c = ["karta", "karta", "chiziq", "blok"]
    if not k.u.qorongi and all(e["tur"] in SODDA | {"eslatma"} for e in els) and len(els) <= 2:
        c.append("qogoz")
    if k.u.oila == "doska":
        c = ["karta", "chiziq"]
    holat = k.deck.setdefault("_karta", {"oxirgi": None})
    tanlov = [x for x in c if x != holat["oxirgi"] or x == "karta"]
    v = k.rng.choice(tanlov)
    holat["oxirgi"] = v
    return v


def kontent(k, d):
    els = list(d["elementlar"])
    joy, vis, matnlar = tanla(k, d, els)
    k.karta_v = karta_korinishi(k, els)
    if joy not in TOLIQ_JOY:
        sahifa_kartasi(k)
    bar = [e for e in els if e["tur"] == "eslatma"]
    fn = globals().get("_j_" + joy)
    if joy in ("standart", "keng") or fn is None:
        return B._kontent_standart(k, d)
    fn(k, d, vis, matnlar, bar[:1])
    B.pastki(k)


def _eslatma(k, bar, x, w):
    if bar:
        k.keyingi()
        B.komp_eslatma(k, bar[0], x, CB - 60, w, 56)
        return 72
    return 0


def _matnlar_ustun(k, matnlar, x, y, w, h, i0=0):
    """Matnli elementlarni ustunda ketma-ket (har biri o'z balandligi bilan)."""
    n = len(matnlar)
    if not n:
        return
    gap = 18
    if n == 1:
        B.KOMP.get(matnlar[0]["tur"], B.komp_matnli)(k, matnlar[0], x, y, w, h, i0)
        return
    ehtiyoj = [max(120, B.matn_balandligi(e.get("matn") or e.get("shart") or "", w - 36, 19) + 90) for e in matnlar]
    tot = sum(ehtiyoj)
    yy = y
    for j, e in enumerate(matnlar):
        hh = (h - gap * (n - 1)) * ehtiyoj[j] / tot
        if j:
            k.keyingi()
        B.KOMP.get(e["tur"], B.komp_matnli)(k, e, x, yy, w, hh, i0 + j)
        yy += hh + gap


def _rasm(k, e, x, y, w, h, s, dl=None, taglik=True, oq=False):
    """Illyustratsiyani (shaffof) maydonga sig'dirib qo'yadi; orqasida yumshoq shakl."""
    u = k.u
    info = RS.malumot(e["rasm"])
    iw_, ih_ = (info.get("olcham") or _olcham(e["rasm"]))[:2]
    sc = min(w / iw_, h / ih_)
    bw, bh = iw_ * sc, ih_ * sc
    cx, cy = x + w / 2, y + h / 2
    if taglik:
        r = max(bw, bh) * 0.52
        if oq:
            k.s.doira(cx, cy, r, fill="#FFFFFF", op=0.22 if not u.qorongi else 0.9, a=k.A("big", s))
        else:
            B.taglik(k, cx, cy, r, s)
    k.s.img(cx - bw / 2, cy - bh / 2, bw, bh, "rasm:" + e["rasm"], a=k.A("big", s, dl=k.st if dl is None else dl))
    return cx, cy, bw, bh


def _olcham(key):
    try:
        got = RS.ol(key)
        if got:
            return [got[1], got[2]]
    except Exception:
        pass
    return [1024, 1024]


def _izoh_kredit(k, e, x, y, w, color, s):
    yy = y
    if e.get("izoh"):
        k.s.matn(x, yy, w, 22, e["izoh"], size=13.5, italic=True, color=color, align="c", min_scale=0.6, a=k.A("item", s, dl=600))
        yy += 24
    kr = RS.kredit(e["rasm"])
    if kr:
        k.s.matn(x, yy, w, 14, kr, size=9, color=color, align="c", min_scale=0.6, a=k.A("item", s, dl=600))


# --- matn + rasm yonma-yon
def _yon(k, d, vis, matnlar, bar, rasm_chapda):
    B.bosh_qism(k, d["kicker"], d["sarlavha"])
    s = k.qadam
    x0, w0 = M, W - 2 * M
    h0 = CB - CT - (72 if bar else 0)
    rw = w0 * (0.42 if matnlar else 1.0)
    tw = w0 - rw - 28
    rx = x0 if rasm_chapda else x0 + w0 - rw
    tx = x0 + rw + 28 if rasm_chapda else x0
    cap = 26 if vis.get("izoh") else 0
    _rasm(k, vis, rx + 10, CT + 6, rw - 20, h0 - 12 - cap, s)
    _izoh_kredit(k, vis, rx, CT + h0 - cap - 4, rw, k.u.muted, s)
    _matnlar_ustun(k, matnlar, tx, CT, tw, h0)
    _eslatma(k, bar, x0, w0)


def _j_rasm_ong(k, d, vis, matnlar, bar):
    _yon(k, d, vis, matnlar, bar, False)


def _j_rasm_chap(k, d, vis, matnlar, bar):
    _yon(k, d, vis, matnlar, bar, True)


# --- yarim slayd rangli panel
def _j_rasm_panel(k, d, vis, matnlar, bar):
    u = k.u
    s = k.qadam
    chap = k.rng.random() < 0.4
    pw = 500 if matnlar else 640
    px = 0 if chap else W - pw
    col = u.acc[k.rng.randrange(2)]
    a = k.A("card", s)
    if u.qorongi:
        k.s.rect(px, 0, pw, H, fill=col, op=0.22, a=a)
    else:
        k.s.rect(px, 0, pw, H, fill=col, a=a)
        k.s.rect(px + (pw - 70 if chap else 0), 0, 70, H, fill=toq(col, 0.12), op=0.35, a=a)
    cap = 30 if vis.get("izoh") or RS.kredit(vis["rasm"]) else 0
    _rasm(k, vis, px + 50, 70, pw - 100, H - 170 - cap, s, oq=True)
    if cap:
        _izoh_kredit(k, vis, px + 30, H - 96 - cap, pw - 60, u.matn_ustida(col) if not u.qorongi else u.muted, s)
    tx = pw + 48 if chap else M
    tw = W - pw - 48 - M
    B.bosh_qism(k, d["kicker"], d["sarlavha"], x=tx, w=tw)
    h0 = CB - CT - (72 if bar else 0)
    if matnlar:
        _matnlar_ustun(k, matnlar, tx, CT + 4, tw, h0 - 4)
    _eslatma(k, bar, tx, tw)


# --- katta rasm, matn kartada
def _j_rasm_katta(k, d, vis, matnlar, bar):
    u = k.u
    s = k.qadam
    B.bosh_qism(k, d["kicker"], d["sarlavha"], w=640)
    # rasm o'ng tomonda katta, pastki chetga tegib turadi
    rx, ry, rw, rh = 600, 70, 660, 610
    k.s.doira(rx + rw * 0.56, ry + rh * 0.58, 300, fill=u.acc[0], op=0.1 if not u.qorongi else 0.16, a=k.A("big", s))
    k.s.doira(rx + rw * 0.9, ry + rh * 0.12, 70, fill=u.acc[2], op=0.18 if not u.qorongi else 0.25, a=k.A("big", s, dl=100))
    if u.qorongi:
        k.s.doira(rx + rw * 0.56, ry + rh * 0.58, 250, fill="#FFFFFF", op=0.88, a=k.A("big", s))
    _rasm(k, vis, rx + 30, ry + 20, rw - 60, rh - 40, s, taglik=False)
    if vis.get("izoh"):
        k.s.matn(rx, H - 40, rw - 40, 22, vis["izoh"], size=13, italic=True, color=u.muted, align="r", min_scale=0.6, a=k.A("item", s, dl=600))
    if matnlar:
        e = matnlar[0]
        text = e.get("matn") or e.get("shart") or ""
        if e.get("bandlar"):
            text = "\n".join("• " + b["matn"] for b in e["bandlar"] if b.get("matn"))
        lab = e.get("sarlavha") or B.LABEL.get(e["tur"], "")
        tw = 560
        sz, th = B.mos_olcham(text, tw - 56, 330, sizes=(28, 26, 24, 22, 20, 19, 18, 17, 16))
        ch = th + (76 if lab else 48) + (70 if e.get("formula") else 0)
        cy = CT + max(0, (CB - CT - ch) / 2 - 10)
        ix, iy, iw, ih = B._yorliq_kartasi(k, M, cy, tw, ch, lab, u.acc[0], 0, a=k.A("card", s, dl=150))
        k.s.matn(ix + 4, iy, iw - 8, th + 6, text, size=sz, color=u.ink, urg=u.acc[0], lh=1.22, a=k.A("item", s, dl=150 + k.st))
        if e.get("formula"):
            FM.chiz(k.s, e["formula"], ix, iy + th + 10, iw, 58, size=30, color=u.ink, align="l", a=k.A("accent", s, dl=150 + 2 * k.st))
    _eslatma(k, bar, M, 560)


# --- bitta katta g'oya o'rtada
def _j_markaz(k, d, vis, matnlar, bar):
    u = k.u
    s = k.qadam
    e = matnlar[0]
    B.bosh_qism(k, d["kicker"], d["sarlavha"], tur="markaz")
    col = {"tarif": u.acc[0], "qoida": u.acc[1], "teorema": u.acc[3], "savol": u.acc[2]}.get(e["tur"], u.acc[0])
    lab = e.get("sarlavha") if e["tur"] == "matn" else (e.get("sarlavha") or B.LABEL.get(e["tur"], ""))
    text = e.get("matn") or ""
    h0 = CB - CT - (72 if bar else 0)
    fh = 90 if e.get("formula") else 0
    tw = W - 2 * M - 220
    sz, th = B.mos_olcham(text, tw, h0 - 110 - fh, sizes=(40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20))
    blok_h = th + (54 if lab else 0) + fh + 40
    y = CT + (h0 - blok_h) / 2
    # orqa fonda katta yumshoq shakl
    k.s.rect(M + 60, y - 18, W - 2 * M - 120, blok_h + 36, fill=col, op=0.07 if not u.qorongi else 0.14, r=36, a=k.A("card", s))
    k.s.matn(M + 70, y - 40, 120, 150, "“", size=110, font="serif", bold=True, color=col, a=k.A("accent", s), min_scale=1)
    if lab:
        B.pill(k, (W - B.kenglik(lab.upper(), "sans", True, 11) - 30) / 2, y + 4, lab, col, a=k.A("accent", s), size=11)
        y += 54
    k.s.matn((W - tw) / 2, y, tw, th + 8, text, size=sz, font=u.head, color=u.ink, urg=col, align="c", lh=1.24, a=k.A("item", s, dl=k.st))
    y += th + 18
    if fh:
        FM.chiz(k.s, e["formula"], (W - tw) / 2, y, tw, fh - 10, size=40, color=u.ink, align="c", a=k.A("accent", s, dl=2 * k.st))
    _eslatma(k, bar, M, W - 2 * M)


# --- yonma-yon raqamli ustunlar
def _j_ustunlar(k, d, vis, matnlar, bar):
    u = k.u
    B.bosh_qism(k, d["kicker"], d["sarlavha"])
    n = len(matnlar)
    gap = 24
    h0 = CB - CT - (72 if bar else 0)
    cw = (W - 2 * M - gap * (n - 1)) / n
    matnlari = [e.get("matn") or "" for e in matnlar]
    olch = [B.mos_olcham(t, cw - 48, h0 - 150, sizes=(24, 22, 21, 20, 19, 18, 17, 16, 15)) for t in matnlari]
    sz = min(o[0] for o in olch)
    th = max(B.matn_balandligi(t, cw - 48, sz, lh=1.22) for t in matnlari)
    ch = min(h0, th + 150)
    y = CT + (h0 - ch) / 2
    for j, e in enumerate(matnlar):
        st = k.qadam if j == 0 else k.keyingi()
        col = u.acc[j % 4]
        x = M + j * (cw + gap)
        a = k.A("card", st)
        B.kart(k, x, y, cw, ch, j, a=a)
        k.s.rect(x, y, cw, 6, fill=col, r=3, a=a)
        k.s.matn(x + 24, y + 22, 100, 50, f"{j + 1:02d}", size=40, font=u.head, bold=True, color=col, a=k.A("accent", st, dl=80))
        lab = e.get("sarlavha") or B.LABEL.get(e["tur"], "")
        if lab:
            k.s.matn(x + 24, y + 76, cw - 48, 26, lab.upper(), size=12, bold=True, color=u.muted, spc=90, min_scale=0.6, a=k.A("item", st, dl=120))
        k.s.matn(x + 24, y + 108, cw - 48, ch - 126, matnlari[j], size=sz, color=u.ink, urg=col, lh=1.22, a=k.A("item", st, dl=160))
        if e.get("formula"):
            FM.chiz(k.s, e["formula"], x + 20, y + ch - 70, cw - 40, 56, size=28, color=u.ink, a=k.A("item", st, dl=220))
    _eslatma(k, bar, M, W - 2 * M)


# --- qatorlar
def _j_qatorlar(k, d, vis, matnlar, bar):
    u = k.u
    B.bosh_qism(k, d["kicker"], d["sarlavha"])
    n = len(matnlar)
    gap = 16
    h0 = CB - CT - (72 if bar else 0)
    tw = W - 2 * M - 130
    ehtiyoj = [B.matn_balandligi(e.get("matn") or "", tw, 20, lh=1.22) + 50 for e in matnlar]
    tot = sum(ehtiyoj)
    mavjud = h0 - gap * (n - 1)
    k_ = min(1.0, mavjud / tot) if tot else 1
    hs = [max(80, x * k_) for x in ehtiyoj]
    jami = sum(hs) + gap * (n - 1)
    y = CT + max(0, (h0 - jami) / 2)
    for j, e in enumerate(matnlar):
        st = k.qadam if j == 0 else k.keyingi()
        col = u.acc[j % 4]
        hh = hs[j]
        a = k.A("card", st)
        B.kart(k, M, y, W - 2 * M, hh, j, a=a)
        k.s.rect(M, y, 92, hh, fill=col, op=0.12 if not u.qorongi else 0.24, r=min(u.kart_s["r"], 14), a=a)
        k.s.matn(M, y, 92, hh, f"{j + 1}", size=34, font=u.head, bold=True, color=col if not u.qorongi else och(col, 0.25), align="c", va="m", a=a)
        lab = e.get("sarlavha") or B.LABEL.get(e["tur"], "")
        txt = (f"**{lab}.** " if lab else "") + (e.get("matn") or "")
        sz, th = B.mos_olcham(txt, tw, hh - 24, sizes=(22, 21, 20, 19, 18, 17, 16, 15))
        k.s.matn(M + 116, y + 10, tw, hh - 20, txt, size=sz, color=u.ink, urg=col, va="m", lh=1.22, a=k.A("item", st, dl=k.st))
        y += hh + gap
    _eslatma(k, bar, M, W - 2 * M)


# --- sarlavha chap ustunda
def _j_yon_sarlavha(k, d, vis, matnlar, bar):
    u = k.u
    s = k.qadam
    sw = 400
    col = u.acc[0]
    a = k.A("card", s)
    if u.qorongi:
        k.s.rect(0, 0, sw, H, fill=col, op=0.12, a=a)
    else:
        k.s.rect(0, 0, sw, H, fill=u.tint(0, 0.9), a=a)
    k.s.rect(sw - 4, 0, 4, H, fill=col, op=0.6, a=a)
    kicker = d.get("kicker") or ""
    sz, th = B.mos_olcham(d["sarlavha"], sw - M - 44, 300, sizes=(40, 38, 36, 34, 32, 30, 28, 26, 24))
    y0 = max(90, (H - 60 - (th + 64)) / 2)
    k.s.matn(M, y0, sw - M - 40, 20, kicker.upper(), size=11.5, bold=True, color=col, spc=110, nm="!!kicker", min_scale=0.6)
    k.s.matn(M, y0 + 32, sw - M - 44, th + 10, d["sarlavha"], size=sz, font=u.head, bold=True, color=u.ink, lh=1.12, nm="!!title",
             a=k.A("item", s))
    k.s.rect(M, y0 + 32 + th + 22, 64, 5, fill=col, r=2.5, a=k.A("accent", s, dl=150))
    x = sw + 44
    w = W - x - M
    h0 = CB - 60 - (72 if bar else 0)
    _matnlar_ustun(k, matnlar, x, 60, w, h0)
    if bar:
        k.keyingi()
        B.komp_eslatma(k, bar[0], x, CB - 60, w, 56)


# --- rasm tepada: keng rangli tasma (sarlavha + rasm), matn ostida
def _j_rasm_tepa(k, d, vis, matnlar, bar):
    u = k.u
    s = k.qadam
    col = u.acc[k.rng.randrange(2)]
    th = 300
    a = k.A("card", s)
    if u.qorongi:
        k.s.rect(0, 0, W, th, fill=col, op=0.22, a=a)
    else:
        k.s.rect(0, 0, W, th, fill=col, a=a)
        k.s.doira(W - 160, th - 10, 230, fill="#FFFFFF", op=0.12, a=a)
    fg = u.matn_ustida(col) if not u.qorongi else u.ink
    k.s.matn(M, 64, 640, 20, (d.get("kicker") or "").upper(), size=12, bold=True, color=fg, spc=110, nm="!!kicker", min_scale=0.6, a=a)
    sz, tth = B.mos_olcham(d["sarlavha"], 660, 150, sizes=(44, 40, 36, 32, 30, 28))
    k.s.matn(M, 92, 660, tth + 10, d["sarlavha"], size=sz, font=u.head, bold=True, color=fg, lh=1.1, nm="!!title", a=k.A("item", s, dl=80))
    _rasm(k, vis, 760, 22, 460, th - 44, s, oq=True)
    h0 = CB - th - 24 - (72 if bar else 0)
    n = len(matnlar)
    if n:
        gap = 22
        cw = (W - 2 * M - gap * (n - 1)) / n
        for j, e in enumerate(matnlar):
            if j:
                k.keyingi()
            B.KOMP.get(e["tur"], B.komp_matnli)(k, e, M + j * (cw + gap), th + 24, cw, h0, j)
    _eslatma(k, bar, M, W - 2 * M)


# --- ustma-ust: qisqa element tepada tasma, asosiysi ostida
def _qisqa_balandlik(e, w):
    if e["tur"] == "formula":
        return 150 + (40 if e.get("matn") else 0)
    t = e.get("matn") or ""
    return min(250, B.matn_balandligi(t, w - 60, 21, lh=1.22) + (84 if (e.get("sarlavha") or B.LABEL.get(e["tur"])) else 50))


def _j_ustma(k, d, vis, matnlar, bar):
    B.bosh_qism(k, d["kicker"], d["sarlavha"])
    gap = 18
    h0 = CB - CT - (72 if bar else 0)
    w0 = W - 2 * M
    if len(matnlar) == 3:
        # birinchi qisqa tepada keng, qolgan ikkitasi ostida yonma-yon
        q = next((e for e in matnlar if _qisqami(e)), matnlar[0])
        qolgan = [e for e in matnlar if e is not q]
        th = min(h0 * 0.4, _qisqa_balandlik(q, w0))
        tartib = [q] + qolgan
        regions = [(M, CT, w0, th)]
        bw = (w0 - gap) / 2
        regions += [(M, CT + th + gap, bw, h0 - th - gap), (M + bw + gap, CT + th + gap, bw, h0 - th - gap)]
    else:
        a, b = matnlar
        tartib = [a, b]
        qa = _qisqami(a)
        qh = min(h0 * 0.42, _qisqa_balandlik(a if qa else b, w0))
        ha = qh if qa else h0 - qh - gap
        regions = [(M, CT, w0, ha), (M, CT + ha + gap, w0, h0 - ha - gap)]
    for idx, (e, (x, y, w, h)) in enumerate(zip(tartib, regions)):
        if idx:
            k.keyingi()
        B.KOMP.get(e["tur"], B.komp_matnli)(k, e, x, y, w, h, idx)
    _eslatma(k, bar, M, w0)


# --- asosiy element keng, qisqasi yon ustunda (urg'u kartasi)
def _j_asosiy_yon(k, d, vis, matnlar, bar):
    B.bosh_qism(k, d["kicker"], d["sarlavha"])
    gap = 22
    h0 = CB - CT - (72 if bar else 0)
    w0 = W - 2 * M
    q = next(e for e in matnlar if _qisqami(e))
    asosiy = next(e for e in matnlar if e is not q)
    qw = w0 * 0.36
    aw = w0 - qw - gap
    qisqa_chapda = k.rng.random() < 0.35
    ax = M + qw + gap if qisqa_chapda else M
    qx = M if qisqa_chapda else M + aw + gap
    tartib = [(e, (ax, CT, aw, h0) if e is asosiy else (qx, CT, qw, h0)) for e in matnlar]
    for idx, (e, (x, y, w, h)) in enumerate(tartib):
        if idx:
            k.keyingi()
        B.KOMP.get(e["tur"], B.komp_matnli)(k, e, x, y, w, h, idx if e is asosiy else 3)
    _eslatma(k, bar, M, w0)


# --- misol/masala: qadamlar chapdan o'ngga
def _j_qadam_qator(k, d, vis, matnlar, bar):
    u = k.u
    B.bosh_qism(k, d["kicker"], d["sarlavha"])
    e = matnlar[0]
    s = k.qadam
    col = u.acc[2] if e["tur"] == "masala" else u.acc[0]
    w0 = W - 2 * M
    h0 = CB - CT - (72 if bar else 0)
    shart = e.get("shart") or e.get("matn") or ""
    qs = e.get("qadamlar") or []
    jav = e.get("javob")
    lab = e.get("sarlavha") or B.LABEL.get(e["tur"], "")
    sz, th = B.mos_olcham(shart, w0 - 60, h0 * 0.32, sizes=(26, 24, 22, 21, 20, 19, 18, 17, 16))
    sh = th + 70
    ix, iy, iw, ih = B._yorliq_kartasi(k, M, CT, w0, sh, lab, col, 0, a=k.A("card", s))
    k.s.matn(ix, iy, iw, ih, shart, size=sz, color=u.ink, urg=col, lh=1.22, va="m", a=k.A("item", s, dl=k.st))
    n = len(qs)
    gap = 34
    jh = 56 if jav else 0
    cw = (w0 - gap * (n - 1)) / n
    tsz = min(22, max(15, 24 - n))
    mavjud = h0 - sh - 26 - (jh + 18 if jav else 0)
    kerak = max(B.matn_balandligi(q, cw - 32, tsz, lh=1.2) for q in qs) + 76
    ch = max(110, min(mavjud, kerak, 260))
    top = CT + sh + 26 + max(0, (mavjud - ch) / 2 - 10)
    for i, q in enumerate(qs):
        st = k.keyingi()
        x = M + i * (cw + gap)
        a = k.A("card", st)
        B.kart(k, x, top, cw, ch, i, a=a)
        k.s.doira(x + 30, top + 30, 17, fill=col, a=k.A("accent", st))
        k.s.matn(x + 13, top + 13, 34, 34, str(i + 1), size=15, bold=True, color=u.matn_ustida(col), align="c", va="m", a=k.A("accent", st))
        k.s.matn(x + 16, top + 58, cw - 32, ch - 70, q, size=tsz, color=u.ink, lh=1.2, min_scale=0.55, a=k.A("item", st, dl=80))
        if i < n - 1:
            ax = x + cw + 6
            k.s.matn(ax, top + ch / 2 - 16, gap - 12, 32, "›", size=28, bold=True, color=col, align="c", va="m", a=k.A("accent", st, dl=120))
    if jav:
        st = k.keyingi()
        jy = top + ch + 18
        k.s.rect(M, jy, w0, jh, fill=u.ok, op=0.14 if not u.qorongi else 0.3, line=u.ok, lw=1.2, r=12, a=k.A("accent", st))
        k.s.matn(M + 20, jy, w0 - 40, jh, "**Javob:** " + jav, size=20, color=u.ink, va="m", min_scale=0.6, a=k.A("accent", st))
    _eslatma(k, bar, M, w0)


# --- misol/masala: chizma chapda
def _j_chizma_chap(k, d, vis, matnlar, bar):
    B.bosh_qism(k, d["kicker"], d["sarlavha"])
    h0 = CB - CT - (72 if bar else 0)
    e = dict(matnlar[0], _vis_chap=True)
    B.KOMP.get(e["tur"], B.komp_matnli)(k, e, M, CT, W - 2 * M, h0, 0)
    _eslatma(k, bar, M, W - 2 * M)


# ------------------------------------------------------------------ titul variantlari
def _titul_meta(k, m, x, y, w, align="l", rang=None):
    """Muassasa, tur nishoni, fan · sinf."""
    u = k.u
    rang = rang or u.muted
    s = k.s
    s.matn(x, y, w, 18, (m.get("muassasa") or "").upper(), size=11.5, bold=True, color=rang, spc=120, align=align, min_scale=0.6)
    if m.get("kafedra"):
        s.matn(x, y + 20, w, 18, m["kafedra"], size=12, color=rang, align=align, min_scale=0.6)


def _nishon(k, m, x, y, color, align="l", w=560, rang=None):
    u = k.u
    tur = (m.get("tur") or "dars").upper()
    badge = f"{m['raqam']}-{tur}" if m.get("raqam") else tur
    sub = m.get("fan") or ""
    if m.get("sinf"):
        sub = f"{sub} · {m['sinf']}" if sub else m["sinf"]
    if align == "c":
        bw = B.kenglik(badge.upper(), "sans", True, 11) + 30
        sw_ = B.kenglik(sub, "sans", False, 13) if sub else 0
        x0 = x + (w - bw - (sw_ + 14 if sub else 0)) / 2
        bw = B.pill(k, x0, y, badge, color, size=11, a=k.A("accent", 0))
        if sub:
            k.s.matn(x0 + bw + 14, y, sw_ + 20, 23, sub, size=13, color=rang or u.muted, va="m", min_scale=0.6)
        return
    bw = B.pill(k, x, y, badge, color, size=11, a=k.A("accent", 0))
    k.s.matn(x + bw + 14, y, w - bw - 14, 23, sub, size=13, color=rang or u.muted, va="m", min_scale=0.6)


def _muallif(k, m, x, y, w, rang=None, align="l"):
    u = k.u
    if not m.get("muallif"):
        return
    rol = "Ma’ruzachi" if "ma" in (m.get("tur") or "").lower() else "Muallif"
    k.s.matn(x, y, w, 22, f"**{rol}:** {m['muallif']}", size=14, color=rang or u.ink, align=align, min_scale=0.6)
    if m.get("davr"):
        k.s.matn(x, y + 22, w, 20, m["davr"], size=12, color=rang or u.muted, align=align, min_scale=0.6)


def _tugmalar(k, d, x, y, color, fg=None, chiziq=None):
    u = k.u
    s = k.s
    chiziq = chiziq or color
    s.rect(x, y, 140, 40, fill=None, line=chiziq, lw=1.6, r=20, lnk=d.get("reja"))
    s.matn(x, y, 140, 40, "Reja", size=15, bold=True, color=chiziq, align="c", va="m", lnk=d.get("reja"))
    s.rect(x + 156, y, 170, 40, fill=color, r=20, lnk="next", sh=0 if u.qorongi else 1)
    s.matn(x + 156, y, 170, 40, "Boshlash  ›", size=15, bold=True, color=fg or u.matn_ustida(color), align="c", va="m", lnk="next")


def _titul_rasm(k, m):
    key = m.get("rasm")
    return key if key and k.rasm_bor(key) else None


def _belgi_doira(k, m, cx, cy, r, col, fg=None):
    u = k.u
    s = k.s
    belgi = m.get("belgi") or next((c.upper() for c in (m.get("qisqa") or m["mavzu"]) if c.isalnum()), "•")
    s.doira(cx, cy, r, fill=col, a=k.A("big", 0, dl=200), sh=0 if u.qorongi else 1)
    fg = fg or u.matn_ustida(col)
    if "$" in belgi or "\\" in belgi:
        FM.chiz(s, belgi, cx - r * 0.85, cy - r * 0.6, r * 1.7, r * 1.2, size=r * 0.55, color=fg, a=k.A("accent", 0, dl=400))
    else:
        s.matn(cx - r * 0.9, cy - r * 0.62, r * 1.8, r * 1.24, belgi, size=r * 0.56 if len(belgi) <= 3 else r * 0.34, font="serif",
               bold=True, color=fg, align="c", va="m", a=k.A("accent", 0, dl=400), min_scale=0.4)


def titul(k, d, v):
    {1: _titul_panel, 2: _titul_markaz, 3: _titul_diagonal, 4: _titul_katta, 5: _titul_ramka}[v](k, d)


def _titul_panel(k, d):
    """Chapda matn, o'ngda yarim slayd rangli panel va rasm."""
    u, m, s = k.u, d["meta"], k.s
    col = u.acc[0]
    px = 700
    if u.qorongi:
        s.rect(px, 0, W - px, H, fill=col, op=0.2, a=k.A("card", 0))
    else:
        s.rect(px, 0, W - px, H, fill=col, a=k.A("card", 0))
        s.rect(px, 0, 60, H, fill=toq(col, 0.15), op=0.3, a=k.A("card", 0))
    key = _titul_rasm(k, m)
    if key:
        _rasm(k, {"rasm": key}, px + 50, 80, W - px - 100, 520, 0, dl=200, oq=True)
    else:
        _belgi_doira(k, m, px + (W - px) / 2, H / 2, 150, "#FFFFFF" if not u.qorongi else col, fg=col if not u.qorongi else None)
    _titul_meta(k, m, M + 16, 44, 600)
    _nishon(k, m, M + 16, 112, col, w=600)
    sz, th = B.mos_olcham(m["mavzu"], 600, 250, sizes=(50, 46, 42, 38, 34, 30))
    s.matn(M + 16, 168, 600, 250, m["mavzu"], size=sz, font=u.head, bold=True, color=u.ink, va="m", nm="!!title", lh=1.08,
           a=k.A("big", 0, dl=100))
    s.rect(M + 16, 432, 80, 6, fill=col, r=3, a=k.A("accent", 0, dl=250))
    if m.get("tayanch"):
        s.matn(M + 16, 456, 600, 54, " · ".join(m["tayanch"]), size=15, color=u.muted, lh=1.25, a=k.A("item", 0, dl=300), min_scale=0.6)
    _muallif(k, m, M + 16, 528, 600)
    _tugmalar(k, d, M + 16, 600, col)


def _titul_markaz(k, d):
    """Hammasi o'rtada: rasm (yoki belgi) tepada, katta sarlavha, tugmalar ostida."""
    u, m, s = k.u, d["meta"], k.s
    col = u.acc[0]
    s.doira(W / 2, -260, 520, fill=col, op=0.07 if not u.qorongi else 0.12, a=k.A("big", 0))
    s.doira(-80, H + 40, 240, fill=u.acc[1], op=0.08 if not u.qorongi else 0.12, a=k.A("big", 0))
    s.doira(W + 60, H - 80, 200, fill=u.acc[2], op=0.08 if not u.qorongi else 0.12, a=k.A("big", 0))
    _titul_meta(k, m, M, 30, W - 2 * M, align="c")
    key = _titul_rasm(k, m)
    top = 70
    if key:
        _rasm(k, {"rasm": key}, W / 2 - 170, top, 340, 236, 0, dl=150)
        top += 262
    else:
        _belgi_doira(k, m, W / 2, top + 70, 66, col)
        top += 154
    _nishon(k, m, M, top, col, align="c", w=W - 2 * M)
    sz, th = B.mos_olcham(m["mavzu"], 980, 600 - top - 40 - 90, sizes=(52, 48, 44, 40, 36, 32, 28))
    s.matn((W - 980) / 2, top + 34, 980, th + 10, m["mavzu"], size=sz, font=u.head, bold=True, color=u.ink, align="c", lh=1.08,
           nm="!!title", a=k.A("big", 0, dl=100))
    yy = top + 34 + th + 16
    if m.get("tayanch") and yy < 560:
        s.matn((W - 900) / 2, yy, 900, 26, " · ".join(m["tayanch"]), size=14, color=u.muted, align="c", min_scale=0.6, a=k.A("item", 0, dl=300))
    _muallif(k, m, (W - 600) / 2, 590 if m.get("davr") else 596, 600, align="c")
    _tugmalar(k, d, (W - 326) / 2, 640, col)


def _titul_diagonal(k, d):
    """O'ng tomonda qiya rangli shakl, ustida rasm."""
    u, m, s = k.u, d["meta"], k.s
    col = u.acc[0]
    a = k.A("card", 0)
    s.path([(760, 0), (W, 0), (W, H), (560, H)], fill=col, op=1.0 if not u.qorongi else 0.22, a=a)
    s.path([(690, 0), (760, 0), (560, H), (490, H)], fill=u.acc[1], op=0.85 if not u.qorongi else 0.3, a=k.A("card", 0, dl=120))
    key = _titul_rasm(k, m)
    if key:
        _rasm(k, {"rasm": key}, 760, 110, 470, 500, 0, dl=250, oq=True)
    else:
        _belgi_doira(k, m, 960, H / 2, 140, "#FFFFFF" if not u.qorongi else u.acc[0], fg=col if not u.qorongi else None)
    _titul_meta(k, m, M + 16, 44, 520)
    _nishon(k, m, M + 16, 112, col, w=520)
    sz, th = B.mos_olcham(m["mavzu"], 520, 260, sizes=(48, 44, 40, 36, 32, 28))
    s.matn(M + 16, 166, 520, 260, m["mavzu"], size=sz, font=u.head, bold=True, color=u.ink, va="m", lh=1.08, nm="!!title",
           a=k.A("big", 0, dl=100))
    if m.get("tayanch"):
        s.matn(M + 16, 440, 500, 60, " · ".join(m["tayanch"]), size=15, color=u.muted, lh=1.25, a=k.A("item", 0, dl=300), min_scale=0.6)
    _muallif(k, m, M + 16, 526, 480)
    _tugmalar(k, d, M + 16, 600, col)


def _titul_katta(k, d):
    """Katta rasm o'ngda chetga chiqib turadi, sarlavha kartada."""
    u, m, s = k.u, d["meta"], k.s
    col = u.acc[0]
    s.doira(980, 420, 330, fill=col, op=0.12 if not u.qorongi else 0.16, a=k.A("big", 0))
    s.doira(1160, 120, 90, fill=u.acc[2], op=0.2, a=k.A("big", 0, dl=100))
    key = _titul_rasm(k, m)
    if key:
        if u.qorongi:
            s.doira(980, 420, 280, fill="#FFFFFF", op=0.9, a=k.A("big", 0))
        _rasm(k, {"rasm": key}, 690, 150, 580, 560, 0, dl=200, taglik=False)
    else:
        _belgi_doira(k, m, 980, 420, 180, col)
    B.kart(k, M, 110, 640, 420, 0, a=k.A("card", 0, dl=80))
    _nishon(k, m, M + 34, 140, col, w=580)
    sz, th = B.mos_olcham(m["mavzu"], 572, 220, sizes=(46, 42, 38, 34, 30, 28))
    s.matn(M + 34, 186, 572, 220, m["mavzu"], size=sz, font=u.head, bold=True, color=u.ink, va="m", lh=1.08, nm="!!title",
           a=k.A("big", 0, dl=150))
    if m.get("tayanch"):
        s.matn(M + 34, 420, 572, 50, " · ".join(m["tayanch"]), size=14, color=u.muted, lh=1.22, a=k.A("item", 0, dl=300), min_scale=0.6)
    _muallif(k, m, M + 34, 474, 560)
    _titul_meta(k, m, M + 8, 40, 620)
    _tugmalar(k, d, M + 8, 600, col)


def _titul_ramka(k, d):
    """Ingichka ramka ichida, akademik ko'rinish: chapda sarlavha, o'ngda rasm."""
    u, m, s = k.u, d["meta"], k.s
    col = u.acc[0]
    s.rect(30, 30, W - 60, H - 60, fill=None, line=col, lw=1.4, op=0.7, r=4, a=k.A("card", 0))
    s.rect(42, 42, W - 84, H - 84, fill=None, line=col, lw=0.6, op=0.4, r=2, a=k.A("card", 0))
    _titul_meta(k, m, 80, 74, 700)
    s.rect(80, 120, 56, 4, fill=col, a=k.A("accent", 0))
    _nishon(k, m, 80, 140, col, w=640)
    key = _titul_rasm(k, m)
    tw = 640 if key else 1000
    sz, th = B.mos_olcham(m["mavzu"], tw, 240, sizes=(50, 46, 42, 38, 34, 30))
    s.matn(80, 190, tw, 240, m["mavzu"], size=sz, font="serif", bold=True, color=u.ink, va="m", lh=1.1, nm="!!title", a=k.A("big", 0, dl=100))
    if key:
        _rasm(k, {"rasm": key}, 770, 120, 430, 430, 0, dl=200)
    if m.get("tayanch"):
        s.matn(80, 444, tw, 50, " · ".join(m["tayanch"]), size=15, italic=True, color=u.muted, lh=1.25, a=k.A("item", 0, dl=300), min_scale=0.6)
    _muallif(k, m, 80, 520, 600)
    _tugmalar(k, d, 80, 596, col)


# ------------------------------------------------------------------ bo'lim variantlari
def bolim(k, d, v):
    {1: _bolim_panel, 2: _bolim_markaz, 3: _bolim_fon_raqam, 4: _bolim_rasm}[v](k, d)


def _bolim_belgi(k, d, cx, cy, r, col, fg=None):
    belgi = d.get("belgi") or f"{d['no'] + 1}"
    if len(belgi) > 8 and "$" not in belgi:
        belgi = f"{d['no'] + 1}"
    fg = fg or k.u.matn_ustida(col)
    if "$" in belgi or "\\" in belgi:
        FM.chiz(k.s, belgi, cx - r, cy - r * 0.7, 2 * r, 1.4 * r, size=r * 0.5, color=fg, a=k.A("accent", 0, dl=300))
    else:
        k.s.matn(cx - r, cy - r * 0.7, 2 * r, 1.4 * r, belgi, size=r * 0.5 if len(belgi) <= 4 else r * 0.3, font="serif", bold=True,
                 color=fg, align="c", va="m", a=k.A("accent", 0, dl=300), min_scale=0.4)


def _bolim_panel(k, d):
    u = k.u
    i = d["no"]
    col = u.acc[i % 4]
    pw = 470
    if u.qorongi:
        k.s.rect(0, 0, pw, H, fill=col, op=0.22, a=k.A("card", 0))
    else:
        k.s.rect(0, 0, pw, H, fill=col, a=k.A("card", 0))
    fg = u.matn_ustida(col) if not u.qorongi else och(col, 0.3)
    k.s.matn(0, 170, pw, 220, f"{i + 1:02d}", size=170, font=u.head, bold=True, color=fg, align="c", va="m", nm="!!kicker",
             a=k.A("big", 0, dl=100))
    k.s.matn(60, 420, pw - 120, 30, (d.get("belgi") or "") if len(d.get("belgi") or "") <= 24 and "$" not in (d.get("belgi") or "") else "",
             size=18, color=fg, align="c", min_scale=0.6, a=k.A("item", 0, dl=300))
    k.s.matn(pw + 70, 120, 640, 30, "BO‘LIM", size=13, bold=True, color=col, spc=160, a=k.A("item", 0))
    sz, th = B.mos_olcham(d["nom"], W - pw - 140, 260, sizes=(48, 44, 40, 36, 32, 28))
    k.s.matn(pw + 70, 160, W - pw - 140, th + 10, d["nom"], size=sz, font=u.head, bold=True, color=u.ink, lh=1.1, nm="!!title",
             a=k.A("card", 0, dl=150))
    k.s.rect(pw + 70, 160 + th + 24, 80, 6, fill=col, r=3, a=k.A("accent", 0, dl=250))
    if d.get("izoh"):
        k.s.matn(pw + 70, 160 + th + 50, W - pw - 140, 120, d["izoh"], size=18, color=u.muted, lh=1.3, a=k.A("item", 0, dl=350))
    B.pastki(k)


def _bolim_markaz(k, d):
    u = k.u
    i = d["no"]
    col = u.acc[i % 4]
    k.s.doira(W / 2, 250, 96, fill=col, a=k.A("big", 0), sh=0 if u.qorongi else 1)
    k.s.doira(W / 2, 250, 122, fill=None, line=col, lw=1.4, op=0.5, a=k.A("big", 0, dl=120))
    k.s.matn(W / 2 - 90, 190, 180, 120, f"{i + 1:02d}", size=64, font=u.head, bold=True, color=u.matn_ustida(col), align="c", va="m",
             nm="!!kicker", a=k.A("accent", 0, dl=200))
    sz, th = B.mos_olcham(d["nom"], 1000, 150, sizes=(46, 42, 38, 34, 30))
    k.s.matn((W - 1000) / 2, 400, 1000, th + 10, d["nom"], size=sz, font=u.head, bold=True, color=u.ink, align="c", lh=1.1, nm="!!title",
             a=k.A("card", 0, dl=250))
    if d.get("izoh"):
        k.s.matn((W - 860) / 2, 400 + th + 20, 860, 70, d["izoh"], size=17, color=u.muted, align="c", a=k.A("item", 0, dl=400))
    B.pastki(k)


def _bolim_fon_raqam(k, d):
    u = k.u
    i = d["no"]
    col = u.acc[i % 4]
    rang = och(col, 0.82) if not u.qorongi else aralash(u.bg[0], col, 0.3)
    k.s.matn(560, 40, 720, 640, f"{i + 1:02d}", size=420, font=u.head, bold=True, color=rang, align="r", va="m", min_scale=1,
             a=k.A("big", 0))
    k.s.rect(M + 20, 250, 8, 200, fill=col, r=4, a=k.A("accent", 0, dl=150))
    k.s.matn(M + 52, 250, 700, 26, f"{i + 1}-BO‘LIM", size=13, bold=True, color=col, spc=160, nm="!!kicker", a=k.A("item", 0, dl=150))
    sz, th = B.mos_olcham(d["nom"], 720, 200, sizes=(50, 46, 42, 38, 34, 30))
    k.s.matn(M + 52, 284, 720, th + 10, d["nom"], size=sz, font=u.head, bold=True, color=u.ink, lh=1.08, nm="!!title",
             a=k.A("card", 0, dl=250))
    if d.get("izoh"):
        k.s.matn(M + 52, 300 + th + 14, 680, 90, d["izoh"], size=17, color=u.muted, lh=1.3, a=k.A("item", 0, dl=400))
    B.pastki(k)


def _bolim_rasm(k, d):
    u = k.u
    i = d["no"]
    col = u.acc[i % 4]
    key = d.get("rasm")
    if not (key and k.rasm_bor(key)):
        return _bolim_panel(k, d)
    k.s.matn(M + 20, 150, 300, 110, f"{i + 1:02d}", size=96, font=u.head, bold=True, color=col, nm="!!kicker", a=k.A("big", 0))
    sz, th = B.mos_olcham(d["nom"], 620, 220, sizes=(46, 42, 38, 34, 30))
    k.s.matn(M + 20, 270, 620, th + 10, d["nom"], size=sz, font=u.head, bold=True, color=u.ink, lh=1.1, nm="!!title",
             a=k.A("card", 0, dl=200))
    if d.get("izoh"):
        k.s.matn(M + 20, 280 + th + 16, 600, 90, d["izoh"], size=17, color=u.muted, lh=1.3, a=k.A("item", 0, dl=400))
    _rasm(k, {"rasm": key}, 720, 100, 500, 500, 0, dl=200)
    B.pastki(k)

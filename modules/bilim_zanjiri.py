"""REV512: bilim zanjiri — har matematika mavzusiga «oldin bilish kerak» bo'lgan mavzular.
Dars boshida 3 savollik kirish tekshiruvi: har oldingi mavzudan bittadan savol. Xato bo'lsa — «Avval buni eslab olaylik»:
qisqa nazariya (namunaviy yechim bilan) va 6 ta amaliy mashq, keyin darsga qaytiladi.
Savollar xilma generatorlaridan (tools/maktab_mat) — 3–11-sinf mavzu oilalari."""
import os, random, re, sys, time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

_YOL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "maktab_mat")
if _YOL not in sys.path:
    sys.path.insert(0, _YOL)

# oila → oldingi (zarur) oilalar. «modul:funksiya»
ZANJIR = {
    # 1–2-sinf (REV513)
    "xilma12:o_qosh20": ["xilma12:o_son10"], "xilma12:o_son100": ["xilma12:o_qosh20"], "xilma12:o_masala12": ["xilma12:o_qosh20"],
    "xilma12:o_ifoda12": ["xilma12:o_qosh20"], "xilma12:o_kopjadval": ["xilma12:o_qosh20", "xilma12:o_son100"], "xilma12:o_uchxonali": ["xilma12:o_son100"],
    "xilma12:o_yuz12": ["xilma12:o_kopjadval"], "xilma12:o_olchov12": ["xilma12:o_son100"], "xilma12:o_shakl12": ["xilma12:o_qosh20"],
    "xilma34:o_qoshayir": ["xilma12:o_uchxonali"], "xilma34:o_sonlar34": ["xilma12:o_uchxonali"],
    # 3–4-sinf
    "xilma34:o_kopaytir": ["xilma34:o_qoshayir", "xilma12:o_kopjadval"], "xilma34:o_bolish": ["xilma34:o_kopaytir"], "xilma34:o_alomat": ["xilma34:o_bolish"],
    "xilma34:o_kasr34": ["xilma34:o_bolish"], "xilma34:o_onli34": ["xilma34:o_kasr34", "xilma34:o_sonlar34"],
    "xilma34:o_perimetr34": ["xilma34:o_kopaytir", "xilma34:o_qoshayir"], "xilma34:o_tenglama34": ["xilma34:o_qoshayir", "xilma34:o_kopaytir"],
    "xilma34:o_jism34": ["xilma34:o_perimetr34"], "xilma34:o_yaxlit": ["xilma34:o_sonlar34"], "xilma34:o_diag34": ["xilma34:o_qoshayir", "xilma34:o_bolish"],
    "xilma6:o_tezlik": ["xilma34:o_kopaytir", "xilma34:o_bolish"], "xilma5:o_meyor": ["xilma34:o_bolish", "xilma34:o_kopaytir"],
    # 5-sinf
    "xilma5:o_kop10": ["xilma34:o_kopaytir"], "xilma5:o_tartib": ["xilma34:o_kopaytir", "xilma34:o_bolish"], "xilma5:o_masala": ["xilma5:o_tartib"],
    "xilma5:o_kasr": ["xilma34:o_kasr34", "xilma34:o_bolish", "xilma34:o_alomat"], "xilma5:o_onli": ["xilma34:o_onli34", "xilma5:o_kop10"],
    "xilma5:o_yuz": ["xilma34:o_perimetr34", "xilma34:o_bolish"], "xilma5:o_hajm": ["xilma34:o_perimetr34", "xilma34:o_kopaytir"],
    "xilma5:o_nisbat": ["xilma5:o_kasr", "xilma34:o_bolish"], "xilma5:o_foiz": ["xilma5:o_kasr", "xilma5:o_onli"],
    "xilma5:o_ortacha": ["xilma34:o_qoshayir", "xilma34:o_bolish"], "xilma5:o_burchak": ["xilma34:o_geom34"],
    "xilma5:o_uchburchak": ["xilma5:o_burchak"], "xilma5:o_tortburchak": ["xilma5:o_burchak", "xilma5:o_uchburchak"],
    # 6-sinf
    "xilma6:o_algebra": ["xilma5:o_tartib", "xilma34:o_tenglama34"], "xilma6:o_kasr_bol": ["xilma5:o_kasr"], "xilma6:o_foiz6": ["xilma5:o_foiz", "xilma5:o_kasr"],
    "xilma6:o_doira": ["xilma5:o_onli", "xilma34:o_perimetr34"], "xilma6:o_hajm6": ["xilma5:o_hajm"], "xilma6:o_diagramma": ["xilma5:o_foiz", "xilma5:o_burchak"],
    # 7–11 algebra
    "xilma711:a_ifoda": ["xilma6:o_algebra"], "xilma711:a_daraja": ["xilma34:o_kopaytir", "xilma711:a_ifoda"], "xilma711:a_kophad": ["xilma711:a_ifoda", "xilma711:a_daraja"],
    "xilma711:a_qisqa": ["xilma711:a_kophad", "xilma711:a_daraja"], "xilma711:a_ajratish": ["xilma711:a_qisqa", "xilma711:a_kophad"],
    "xilma711:a_kasr": ["xilma711:a_ajratish", "xilma5:o_kasr", "xilma6:o_kasr_bol"], "xilma711:a_chiziqli": ["xilma711:a_ifoda", "xilma6:o_algebra"],
    "xilma711:a_sistema": ["xilma711:a_chiziqli"], "xilma711:a_funksiya": ["xilma711:a_ifoda", "xilma711:a_chiziqli"],
    "xilma711:a_kvadrat": ["xilma711:a_ajratish", "xilma711:a_chiziqli", "xilma711:a_daraja"], "xilma711:a_tengsizlik": ["xilma711:a_chiziqli", "xilma711:a_kvadrat"],
    "xilma711:a_progressiya": ["xilma711:a_ifoda", "xilma711:a_daraja"], "xilma711:a_trig": ["xilma711:g_pifagor", "xilma6:o_doira"],
    "xilma711:a_log": ["xilma711:a_daraja", "xilma711:a_chiziqli"], "xilma711:a_hosila": ["xilma711:a_funksiya", "xilma711:a_daraja"],
    "xilma711:a_ehtimol": ["xilma5:o_kasr", "xilma711:a_kombinatorika"], "xilma711:a_statistika": ["xilma5:o_ortacha"],
    # 7–11 geometriya
    "xilma711:g_uchburchak": ["xilma711:g_burchak"], "xilma711:g_pifagor": ["xilma711:a_daraja", "xilma711:g_uchburchak"],
    "xilma711:g_yuz": ["xilma711:g_pifagor", "xilma5:o_yuz"], "xilma711:g_kopburchak": ["xilma711:g_uchburchak"],
    "xilma711:g_aylana": ["xilma711:g_burchak", "xilma711:g_pifagor"], "xilma711:g_vektor": ["xilma711:g_koordinata", "xilma711:g_pifagor"],
    "xilma711:g_oxshash": ["xilma5:o_nisbat", "xilma711:g_uchburchak"], "xilma711:g_trigteorema": ["xilma711:a_trig", "xilma711:g_pifagor"],
    "xilma711:g_koordinata": ["xilma711:g_pifagor"], "xilma711:g_stereo": ["xilma711:g_yuz", "xilma6:o_doira"],
}


NOMLAR = {"xilma12:o_son10": "10 gacha sonlar va sanash", "xilma12:o_qosh20": "20 gacha qo‘shish va ayirish", "xilma12:o_son100": "100 gacha sonlar",
          "xilma12:o_kopjadval": "Ko‘paytirish jadvali", "xilma12:o_uchxonali": "Uch xonali sonlar", 'xilma34:o_qoshayir': 'Ko‘p xonali sonlarni qo‘shish va ayirish', 'xilma34:o_kopaytir': 'Ko‘paytirish', 'xilma34:o_bolish': 'Bo‘lish va qoldiqli bo‘lish', 'xilma34:o_alomat': 'Bo‘linish alomatlari', 'xilma34:o_kasr34': 'Ulush va oddiy kasrlar', 'xilma34:o_sonlar34': 'Ko‘p xonali sonlar', 'xilma34:o_onli34': 'O‘nli kasr tushunchasi', 'xilma34:o_perimetr34': 'Perimetr va yuz', 'xilma34:o_tenglama34': 'Sodda tenglamalar', 'xilma34:o_geom34': 'Burchak va geometrik shakllar', 'xilma5:o_kop10': '10, 100, 1000 ga ko‘paytirish va bo‘lish', 'xilma5:o_tartib': 'Amallar tartibi', 'xilma5:o_kasr': 'Oddiy kasrlar ustida amallar', 'xilma5:o_onli': 'O‘nli kasrlar', 'xilma5:o_yuz': 'Uchburchak yuzi', 'xilma5:o_hajm': 'Hajm', 'xilma5:o_nisbat': 'Nisbatlar', 'xilma5:o_foiz': 'Foizlar', 'xilma5:o_ortacha': 'O‘rtacha qiymat', 'xilma5:o_burchak': 'Burchaklar', 'xilma5:o_uchburchak': 'Uchburchak burchaklari', 'xilma6:o_algebra': 'Algebraik ifoda va tenglama', 'xilma6:o_kasr_bol': 'Kasrlarni bo‘lish', 'xilma6:o_doira': 'Doira va aylana', 'xilma711:a_ifoda': 'Algebraik ifodalar', 'xilma711:a_daraja': 'Daraja va ildiz', 'xilma711:a_kophad': 'Birhad va ko‘phadlar', 'xilma711:a_qisqa': 'Qisqa ko‘paytirish formulalari', 'xilma711:a_ajratish': 'Ko‘paytuvchilarga ajratish', 'xilma711:a_chiziqli': 'Chiziqli tenglamalar', 'xilma711:a_funksiya': 'Funksiya va grafik', 'xilma711:a_kvadrat': 'Kvadrat tenglamalar', 'xilma711:a_trig': 'Trigonometriya asoslari', 'xilma711:a_kombinatorika': 'Kombinatorika', 'xilma711:g_burchak': 'Burchaklar va parallel to‘g‘ri chiziqlar', 'xilma711:g_uchburchak': 'Uchburchak', 'xilma711:g_pifagor': 'Pifagor teoremasi', 'xilma711:g_yuz': 'Ko‘pburchak yuzlari', 'xilma711:g_koordinata': 'Koordinatalar'}


def _mod(nom):
    return __import__(nom)


def oila_kaliti(sinf, mavzu):
    n = int((re.search(r"\d{1,2}", str(sinf or "")) or [0])[0] or 0) if re.search(r"\d", str(sinf or "")) else 0
    modul = "xilma12" if n in (1, 2) else "xilma34" if n in (3, 4) else "xilma5" if n == 5 else "xilma6" if n == 6 else "xilma711" if n >= 7 else ""
    if not modul:
        return None
    try:
        f = _mod(modul).oila_tanla(mavzu)
    except Exception:   # noqa: BLE001
        return None
    if not f or f.__name__ in ("aralash", "o_takror", "o_takror34"):
        return None
    return f"{f.__module__}:{f.__name__}"


def oila_fn(kalit):
    m, f = kalit.split(":")
    return getattr(_mod(m), f)


def oila_nomi(kalit):
    if kalit in NOMLAR:
        return NOMLAR[kalit]
    doc = (oila_fn(kalit).__doc__ or "").strip().split("\n")[0].rstrip(".")
    return doc or kalit.split(":")[1].replace("o_", "").replace("a_", "").replace("g_", "")


def _variantli(item, rr):
    q, j, y, xs = item[:4]
    vs = [str(j)] + [str(x) for x in xs if str(x) != str(j)][:3]
    vs = list(dict.fromkeys(vs))
    rr.shuffle(vs)
    return {"savol": q, "variantlar": vs, "togri": vs.index(str(j)), "yechim": y}


def savol(kalit, urug):
    f = oila_fn(kalit); rr = random.Random(urug)
    turlar = f(rr)
    for _ in range(12):
        t = turlar[rr.randrange(len(turlar))]
        try:
            it = t()
        except Exception:   # noqa: BLE001
            continue
        if it[3] and str(it[1]) not in [str(x) for x in it[3]]:
            return _variantli(it, rr)
    return None


def create_router(platform, dars_xonasi_tashqi=None):
    router = APIRouter(tags=["bilim_zanjiri"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    @router.get("/api/bilim_zanjiri/kirish")
    def kirish(topic_code: str, token: str = "", authorization: Optional[str] = Header(None)):
        """Darsdan oldin: oldingi mavzulardan 3 tagacha savol (ko'p tanlovli)."""
        u = uid(token, authorization)
        try:
            tashqi = dars_xonasi_tashqi() if callable(dars_xonasi_tashqi) else (dars_xonasi_tashqi or {})
            yukla = tashqi.get("yukla")
            les = yukla(topic_code, "uz") if yukla else None
        except Exception:   # noqa: BLE001
            les = None
        top = (les or {}).get("topic") or {}
        if not re.search(r"matem|algebra|geometr", str(top.get("fan") or ""), re.I):
            return {"savollar": []}
        k = oila_kaliti(top.get("sinf"), top.get("mavzu"))
        # REV516: 4–5 ta savol (bitta emas): har oldingi mavzudan 2 tadan; oz bo'lsa — undan oldingilaridan ham
        oldingi = list(ZANJIR.get(k or "", []))
        for ok in list(oldingi):
            if len(oldingi) >= 3:
                break
            for o2 in ZANJIR.get(ok, []):
                if o2 not in oldingi and o2 != k:
                    oldingi.append(o2)
        urug = u * 7919 + int(time.time() // 86400)
        out, korilgan = [], set()
        for tur in range(3 if len(oldingi) == 1 else 2):
            for i, ok in enumerate(oldingi[:4]):
                if len(out) >= 5:
                    break
                s = savol(ok, f"{urug}:{topic_code}:{i}:{tur}")
                if s and s["savol"] not in korilgan:
                    korilgan.add(s["savol"]); out.append({**s, "oila": ok, "nom": oila_nomi(ok)})
        out.sort(key=lambda x: oldingi.index(x["oila"]))
        return {"mavzu": top.get("mavzu"), "oila": k, "savollar": out}

    @router.get("/api/bilim_zanjiri/takror")
    def takror(oila: str, token: str = "", authorization: Optional[str] = Header(None)):
        """«Avval buni eslab olaylik»: qisqa nazariya + namunaviy yechim + 6 ta mashq."""
        u = uid(token, authorization)
        if oila not in {x for v in ZANJIR.values() for x in v} | set(ZANJIR):
            raise HTTPException(404, "Mavzu topilmadi")
        f = oila_fn(oila); rr = random.Random(f"{u}:{oila}:{int(time.time() // 3600)}")
        turlar = f(rr); namuna = None
        for t in turlar:
            try:
                namuna = t(); break
            except Exception:   # noqa: BLE001
                continue
        mashq = []
        for i in range(30):
            if len(mashq) >= 6:
                break
            s = savol(oila, f"{u}:{oila}:{i}:{int(time.time() // 3600)}")
            if s and s["savol"] not in [m["savol"] for m in mashq]:
                mashq.append(s)
        return {"oila": oila, "nom": oila_nomi(oila),
                "namuna": {"savol": namuna[0], "javob": str(namuna[1]), "yechim": namuna[2]} if namuna else None, "mashqlar": mashq}

    return router

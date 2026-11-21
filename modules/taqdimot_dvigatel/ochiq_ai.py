"""«AI yozsin» rejimi: AI mavzu materiallarini o'qib, har bosqichga mos metodni, guruhlash va birlashtirish usulini tanlaydi,
o'qituvchi nutqini yozadi va kutubxonadan rasmlarni joylaydi. Masalliq yo'q bo'lsa — parallel ravishda masalliq ham yozdiriladi.
Natija oddiy generator (ochiq_dars.tuz) orqali yig'iladi, shuning uchun AI faqat ruxsat etilgan kodlardan tanlay oladi."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from . import ai, ochiq_dars as od, rasmlar, sxema

KORSATMA = """Sen tajribali metodist va ochiq dars rejissyorisan. O‘qituvchi uchun ochiq dars ssenariysini tanlaysan.
Senga darsning bosqichlari va har bosqich uchun RUXSAT ETILGAN metod kodlari beriladi — faqat shu kodlardan tanla.
Tanlashda: mavzu mazmuni, sinf yoshi, bosqich maqsadi va metodlar xilma-xilligi (bir metod ikki marta emas) hisobga olinsin;
an’anaviy «aytib berish» emas — interfaol, STEAM va 4K (tanqidiy fikrlash, kreativlik, kommunikatsiya, hamkorlik) ruhida.
Rasm kalitlarini FAQAT berilgan ro‘yxatdan ol (mos bo‘lmasa — bo‘sh qoldir). O‘zbek tilida (lotin), imlo xatosiz.
Javob FAQAT JSON:
{"tanlov":{"<bosqich raqami>":"metod kodi"},
 "guruhlash":"guruhlash kodi","birlashtirish":"birlashtirish kodi",
 "metodik_maqsad":"ochiq darsning metodik maqsadi — 1 jumla",
 "maqsadlar":{"talimiy":"1 jumla","tarbiyaviy":"1 jumla","rivojlantiruvchi":"1 jumla"},
 "natijalar":["o‘quvchi … qila oladi — 3 ta"],
 "guruh_nomlari":["mavzu tushunchalaridan guruh nomlari"],
 "nutq":{"<bosqich raqami>":"o‘qituvchining shu bosqichdagi jonli so‘zi — 2–4 jumla, to‘g‘ridan-to‘g‘ri o‘quvchilarga"},
 "rasm":{"<bosqich raqami>":"rasm kaliti"},
 "titul_rasm":"rasm kaliti"}"""


def _miya_xulosa(miya: dict | None, n: int = 2600) -> str:
    if not miya:
        return "(mavzu materiali yo‘q — umumiy bilimga tayan)"
    m = miya
    qator = [f"Maqsad: {(m.get('meta') or {}).get('maqsad') or ''}", "Tayanch: " + ", ".join((m.get("meta") or {}).get("tayanch") or [])]
    for b in m.get("bolimlar") or []:
        qator.append(f"# {b.get('nom') or ''}")
        for sl in (b.get("slaydlar") or [])[:6]:
            matn = " ".join(od._gaplar(od._el_matn(e), 1) for e in (sl.get("elementlar") or [])[:2]).strip()
            qator.append(f"- {sl.get('sarlavha') or ''}: {matn[:160]}")
    return "\n".join(qator)[:n]


def _masalliq_xulosa(mas: dict) -> str:
    q = []
    if mas.get("atamalar"):
        q.append("Atamalar: " + "; ".join(a["atama"] for a in mas["atamalar"][:8]))
    if mas.get("qismlar"):
        q.append("Qismlar: " + "; ".join(x["nom"] for x in mas["qismlar"][:4]))
    for k in ("muammoli_savol", "tezis"):
        if mas.get(k):
            q.append(f"{k}: {mas[k][:160]}")
    if (mas.get("tajriba") or {}).get("nom"):
        q.append("Tajriba: " + mas["tajriba"]["nom"])
    if (mas.get("keys") or {}).get("vaziyat"):
        q.append("Keys: " + mas["keys"]["vaziyat"][:160])
    return "\n".join(q) or "(masalliq yo‘q)"


def _birlashtir(asl: dict, yangi: dict, asl_haqiqiy: bool) -> dict:
    """Miyaning o'z masallig'i ustun; bo'sh qismlarni AI yozgani to'ldiradi. Masalliq miyadan taxminiy olingan bo'lsa — AI ustun."""
    out = dict(asl)
    for k, v in (yangi or {}).items():
        if not v or (isinstance(v, dict) and not any(v.values())):
            continue
        bosh = asl.get(k)
        bosh_yoq = not bosh or (isinstance(bosh, dict) and not any(bosh.values()))
        if bosh_yoq or not asl_haqiqiy:
            out[k] = v
    return out


def tuz(sorov: dict, miya: dict | None, deadline: float = 170.0) -> dict:
    """AI rejimidagi ochiq dars. AI ishlamasa — RuntimeError (chaqiruvchi tezkor rejimga qaytadi)."""
    t0 = time.monotonic()
    meta = (miya or {}).get("meta") or {}
    asos = od.tuz({**sorov, "rejim": "tezkor"}, miya)          # bosqichlar, nomzodlar, urug'
    mt = asos["meta"]
    haqiqiy = od.bor_masalliq(miya)
    mas = asos["masalliq"]

    bosq = []
    for i, b in enumerate(asos["bosqichlar"]):
        if b["metod"] and b["metod"]["tur"] in ("guruhlash", "birlashtirish"):
            bosq.append(f"{i}. {b['nom']} ({b['daq']} daq.) — {b['metod']['tur']} usuli (pastdagi ro‘yxatdan)")
        elif b["nomzodlar"]:
            bosq.append(f"{i}. {b['nom']} ({b['daq']} daq.) — metodlar: " + ", ".join(f"{n['kod']} ({n['nom']})" for n in b["nomzodlar"]))
        else:
            bosq.append(f"{i}. {b['nom']} ({b['daq']} daq.) — metod tanlanmaydi, faqat nutq va rasm")
    xabar = "\n".join([
        f"MAVZU: {mt['mavzu']}", f"FAN: {mt['fan']}", f"{'KURS' if mt['yosh'] in od.om.OTM else 'SINF'}: {mt['sinf']} ({mt['yosh_nom']})",
        f"DARS: {mt['format_nom']} — {mt['andoza_nom']}, {mt['daqiqa']} daqiqa, {mt['oquvchilar']} o‘quvchi, {len(asos['guruhlash']['guruhlar'])} guruh",
        (f"O‘QITUVCHI ISTAGI: {sxema.t(sorov.get('istak'), 600)}" if sorov.get("istak") else ""),
        "\nBOSQICHLAR:", *bosq,
        "\nGURUHLASH USULLARI: " + ", ".join(f"{n['kod']} ({n['nom']})" for n in asos["guruhlash"]["nomzodlar"]),
        "BIRLASHTIRISH USULLARI: " + ", ".join(f"{n['kod']} ({n['nom']})" for n in asos["birlashtirish"]["nomzodlar"]),
        "\nMAVZU MATERIALI:", _miya_xulosa(miya),
        "\nTAYYOR MASALLIQ:", _masalliq_xulosa(mas) if haqiqiy else "(alohida yozilmoqda)",
        "\nRASMLAR (kalit — nomi):", ai.katalog_matni(mt["mavzu"], mt["fan"], 70),
        "\nTanlovni JSON qilib yoz."])

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_mas = None if haqiqiy else pool.submit(ai.masalliq_yoz, mt["mavzu"], mt["fan"], mt["daraja"], mt["sinf"],
                                                 sxema.t(sorov.get("istak"), 600), deadline, t0)
        f_tan = pool.submit(ai._bir_chaqiruv, KORSATMA, xabar, deadline, t0)
        javob = f_tan.result()
        yangi = {}
        if f_mas:
            try:
                yangi = f_mas.result()
            except Exception:
                yangi = {}
    if not isinstance(javob, dict):
        raise RuntimeError("AI javobi noto‘g‘ri")

    gn = javob.get("guruh_nomlari")
    if isinstance(gn, list) and gn:
        yangi = {**yangi, "guruh_nomlari": [sxema.t(x, 40) for x in gn if isinstance(x, str) and x.strip()][:8]}
    mas2 = _birlashtir(mas, sxema.masalliq_toza(yangi) if yangi else {}, haqiqiy)
    tanlov = {str(k): str(v) for k, v in (javob.get("tanlov") or {}).items() if isinstance(v, str)} if isinstance(javob.get("tanlov"), dict) else {}
    dars = od.tuz({**sorov, "rejim": "ai", "urug": mt["urug"], "tanlov": tanlov,
                   "guruhlash": javob.get("guruhlash"), "birlashtirish": javob.get("birlashtirish"),
                   "metodik_maqsad": sorov.get("metodik_maqsad") or sxema.t(javob.get("metodik_maqsad"), 300)}, miya, mas=mas2)

    mq = javob.get("maqsadlar") if isinstance(javob.get("maqsadlar"), dict) else {}
    dm = (miya or {}).get("dars") or {}
    for k in ("talimiy", "tarbiyaviy", "rivojlantiruvchi"):
        if isinstance(mq.get(k), str) and len(mq[k].strip()) > 10 and not (dm.get("maqsadlar") or {}).get(k):
            dars["maqsadlar"][k] = sxema.t(mq[k], 300)
    nat = [sxema.t(x, 200) for x in javob.get("natijalar") or [] if isinstance(x, str) and len(x.strip()) > 8]
    if nat and not dm.get("natijalar"):
        dars["natijalar"] = nat[:5]
    nutq = javob.get("nutq") if isinstance(javob.get("nutq"), dict) else {}
    rasm = javob.get("rasm") if isinstance(javob.get("rasm"), dict) else {}
    ishlatilgan = set()
    for i, b in enumerate(dars["bosqichlar"]):
        if isinstance(nutq.get(str(i)), str):
            b["nutq"] = sxema.t(nutq[str(i)], 700)
        k = rasmlar.kalit_toza(rasm.get(str(i)) or "") if isinstance(rasm.get(str(i)), str) else ""
        if k and k not in ishlatilgan and rasmlar.bor(k):
            b["rasm"] = k
            ishlatilgan.add(k)
    tr = rasmlar.kalit_toza(javob.get("titul_rasm") or "") if isinstance(javob.get("titul_rasm"), str) else ""
    if tr and rasmlar.bor(tr) and not meta.get("rasm"):
        dars["meta"]["rasm"] = tr
    dars["meta"]["ai"] = javob.get("_ai") or {}
    dars["meta"]["masalliq_bor"] = haqiqiy or bool(yangi)
    return dars

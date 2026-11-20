"""AI miyani to'ldiradi (dizaynga aralashmaydi).

Bir xil ko'rsatma ikki joyda ishlatiladi: saytning o'zidagi AI (Gemini / OpenAI / Groq kaliti bo'yicha) va
o'qituvchi ChatGPT'da ommaviy tayyorlash uchun (korsatma() matnini ChatGPT'ga beradi, javobni saytga yuklaydi).
"""
from __future__ import annotations

import json
import os
import re
import time
from urllib import error, request

from . import sxema
from .chizma import CHIZMALAR

ENDPOINTS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
}


def _chizma_royxati():
    qatorlar = []
    for k, (_fn, nom, namuna) in CHIZMALAR.items():
        qatorlar.append(f"- {k} — {nom}: {json.dumps(namuna, ensure_ascii=False)}")
    return "\n".join(qatorlar)


def katalog_matni(mavzu: str = "", fan: str = "", n: int = 70) -> str:
    """Kutubxona rasmlari ro'yxati (AI uchun): mavzuga yaqinlari, mavzu bo'lmasa — hammasi fan bo'yicha."""
    from . import rasm_tanla, rasmlar
    if mavzu or fan:
        rows = rasm_tanla.katalog(f"{mavzu} {fan}", fan, n)
        return "\n".join(f"- {k} — {nom}" for k, nom in rows) or "(mos rasm topilmadi)"
    guruh = {}
    for r in rasmlar.papka_reestri():
        if r.get("tur") == "rasm":
            guruh.setdefault(r.get("fan") or "Boshqa", []).append(f"{r['kalit']} — {r.get('nom') or ''}")
    return "\n".join(f"[{f}]\n" + "\n".join("- " + x for x in sorted(v)) for f, v in sorted(guruh.items()))


def korsatma(katalog: bool = False) -> str:
    """AI (yoki ChatGPT) uchun to'liq ko'rsatma. katalog=True — oxiriga barcha kutubxona rasmlari."""
    return _korsatma_asos() + (("\nKUTUBXONA RASMLARI (kalit — nima tasvirlangan):\n" + katalog_matni()) if katalog else "")


def _korsatma_asos() -> str:
    return f"""Sen tajribali o‘qituvchi-metodistsan. Berilgan mavzu bo‘yicha TAQDIMOT MIYASINI yozasan — faqat mazmun,
dizayn emas (ranglar, joylashuv, animatsiyani dastur o‘zi qiladi). Javob FAQAT bitta JSON obyekt bo‘lsin, izohsiz.

TIL VA USLUB
- O‘zbek lotin yozuvi: o‘, g‘, ’ belgilari bilan (masalan: «bo‘lak», «ta’rif»). Imlo xatosiz, ilmiy va tushunarli.
- Matnlar qisqa: slaydda o‘qiladigan gaplar 1–3 jumla. Batafsil gapni "izoh" maydoniga yoz (o‘qituvchining og‘zaki matni).
- Muhim so‘z **qalin**, asosiy tushuncha ==rangli== belgilanadi. Formulalar $...$ ichida LaTeX: $\\frac{{a}}{{b}}$, $x^2$, $\\sqrt{{x}}$,
  $\\mathbb{{Z}}$, $a\\in A$, $\\le$, $\\ne$, $\\cdot$. Alohida "formula" maydonida $ belgisisiz LaTeX yoziladi.
- Faktlar aniq bo‘lsin: tarixiy sana, olim nomi, formulalar to‘g‘ri. Bilmasang — yozma.

TUZILMA (kalitlar aynan shunday):
{{
 "sxema": "taqdimot-miya/1",
 "meta": {{"fan","daraja":"maktab|bakalavr|magistr|bogcha","sinf":"5-sinf yoki 2-kurs","raqam":1,"tur":"dars|ma’ruza|amaliy|seminar",
          "mavzu","qisqa","maqsad","tayanch":["3–5 tayanch tushuncha"],"muassasa","kafedra","muallif","davr",
          "belgi":"titul uchun belgi: $\\frac{{3}}{{8}}$ yoki ℤ yoki n!","rasm":"titul rasmi kaliti (ixtiyoriy)","chizma":{{titul uchun chizma (ixtiyoriy)}}}},
 "adabiyotlar": {{"asosiy":[{{"muallif","nomi","nashr"}}],"elektron":[{{"nomi","izoh"}}],"mustaqil":"..."}},   (maktab darsida bo‘sh qoldirish mumkin)
 "takrorlash": {{"mavzu":"o‘tgan mavzu","oyin":"blits|mosini_top","savollar":[{{"savol","javob"}} × 6]}},
 "muammo": {{"sarlavha","masalalar":[{{"sarlavha","matn"}} × 2],"goya","zanjir":["2–4 bosqich"]}},
 "tarix": {{"sarlavha","voqealar":[{{"davr","nom","matn","belgi","rasm"}} × 3–4],"xulosa"}},
 "bolimlar": [  3–5 ta bo‘lim
   {{"nom","izoh","belgi","slaydlar":[  har bo‘limda 2–4 slayd
      {{"sarlavha":"slayd sarlavhasi","izoh":"o‘qituvchi gapi (3–6 jumla)","elementlar":[ 1–3 element ]}}
   ]}}
 ],
 "xatolar": [{{"xato","sabab","togri"}} × 4–6],
 "metodika": {{"sarlavha","bosqichlar":["3 bosqich"],"kartalar":[{{"sarlavha","matn","chizma"}} × 3],"tavsiya"}},
 "xulosa": {{"bilaman":[4],"bilishni_xohlayman":[4],"bilib_oldim":[4]}}  yoki  {{"fikrlar":[4–6]}},
 "test": [{{"savol","variantlar":["3 yoki 4 variant"],"javob":0}} × 6],   javob — to‘g‘ri variant tartib raqami (0 dan)
 "nazorat": ["5–8 savol"], "mustaqil_ish": ["3–4 topshiriq"], "keyingi": {{"mavzu","izoh"}},
 "rasmlar": [{{"kalit","tavsif","prompt"}}]   — miyada ishlatilgan har bir rasm kaliti uchun
}}

ELEMENT TURLARI ("elementlar" ichida, "tur" maydoni):
- tarif / qoida / teorema: {{"tur","matn","formula"(ixtiyoriy),"chizma"(ixtiyoriy)}}
- formula: {{"tur":"formula","sarlavha","formula","matn":"izohi"}}
- xossalar: {{"tur":"xossalar","sarlavha"(ixt.),"bandlar":[{{"nom","matn","formula"}} × 2–6]}}
- misol / masala: {{"tur","sarlavha","shart","qadamlar":["2–5 qadam"],"javob","chizma"(ixt.)}}
- jadval: {{"tur":"jadval","ustunlar":["..."],"qatorlar":[["..."]] (3–6 qator)}}
- taqqoslash: {{"tur":"taqqoslash","bandlar":[{{"nom","formula","matn","misol"}} × 2–4]}}
- chizma: {{"tur":"chizma","sarlavha","matn","chizma":{{...}},"izoh"}}
- rasm / hayotiy: {{"tur","matn","rasm":"kalit","izoh"}}
- eslatma: {{"tur":"eslatma","sarlavha":"Muhim|Diqqat|Tipik xato","matn"}} (slayd pastida chiziq bo‘lib chiqadi)
- matn: {{"tur":"matn","sarlavha","matn"}}
BARCHA FANLAR UCHUN (shu turlar slaydda YOLG‘IZ turadi, eslatma bilan bo‘lishi mumkin):
- lugat: {{"tur":"lugat","sozlar":[{{"soz","oqilishi","tarjima","misol","rasm"}} × 1–6]}}   — tillar, 1–4-sinf; tarjima bosganda chiqadi
- dialog: {{"tur":"dialog","qatorlar":[{{"kim","matn","tarjima"}} × 2–8]}}   — 2 suhbatdosh, har gap bosish bilan
- parcha: {{"tur":"parcha","sarlavha","matn":"qatorlar \n bilan","muallif","belgilar":["muhim so‘zlar"]}}   — she’r/matn
- vaqt_chizigi: {{"tur":"vaqt_chizigi","voqealar":[{{"sana","nom","matn","rasm"}} × 2–6]}}
- xarita: {{"tur":"xarita","hudud":"ozbekiston|dunyo","belgilash":["Samarqand","Buxoro" yoki davlatlar: "Misr"],
           "joylar":[{{"nom":"Xiva","matn":"qisqa izoh"}} yoki {{"nom":"Qohira","lat":30.04,"lon":31.24}} × 1–8]}}
  (O‘zbekiston shaharlari nomi bilan topiladi; dunyo shaharlari uchun lat/lon yoz)
- tajriba: {{"tur":"tajriba","maqsad","jihozlar":["Probirka","Spirtovka"],"bosqichlar":["2–6 qadam"],"natija","xavfsizlik"}}
- jarayon: {{"tur":"jarayon","shakl":"aylana|zanjir|qadam","sarlavha","bosqichlar":[{{"nom","matn","rasm"}} × 2–6]}}
  (aylana — takrorlanuvchi jarayon; zanjir — ketma-ketlik, oziq zanjiri, algoritm; qadam — rasmli mashq/ish bosqichlari)
- galereya: {{"tur":"galereya","rasmlar":[{{"rasm","izoh"}} × 2–4]}}
- guruhlash: {{"tur":"guruhlash","guruhlar":[{{"nom","bandlar":["2–7 ta"]}} × 2–4]}}
O‘YINLAR (javob bosganda chiqadi):
- moslash: {{"tur":"moslash","juftlar":[{{"chap","ong","rasm"(ixt.)}} × 2–6]}}
- togri_notogri: {{"tur":"togri_notogri","fikrlar":[{{"matn","javob":true|false,"izoh"}} × 2–6]}}
- bosh_joy: {{"tur":"bosh_joy","gaplar":[{{"matn":"I ___ a student.","javob":"am"}} × 2–6]}}
- rasmda_nima: {{"tur":"rasmda_nima","rasm":"kutubxona kaliti","savol","variantlar":["2–4"],"javob":0}}
Bitta slaydda: ko‘pi bilan 3 ta element; jadval/taqqoslash/xossalar va yuqoridagi turlar odatda yolg‘iz yoki eslatma bilan.
Fanga mos turlarni tanla: matematika — formula/misol/chizma; tillar — lugat/dialog/bosh_joy; tarix — vaqt_chizigi/xarita;
geografiya — xarita/jarayon; tabiiy fanlar — tajriba/jarayon/galereya; musiqa va san’at — galereya/guruhlash; har mavzuda 1–3 o‘yin.

CHIZMALAR (kod chizadi, rasm kerak emas — iloji bo‘lsa chizma ishlat). Turlar va namunalar:
{_chizma_royxati()}
(ichma_ich: qatlamlar ICHKARIDAN tashqariga; son_oqi: dan < gacha, 20 tadan kam bo‘linma.)

RASMLAR: chizma bilan ko‘rsatib bo‘lmaydigan joyda (tarixiy shaxs, buyum, jonzot, hayotiy vaziyat) "rasm" maydoniga
kalit yoz. AVVAL pastdagi «KUTUBXONA RASMLARI» ro‘yxatidan aynan mos kalitni tanla — ular tayyor va slaydda darhol chiqadi.
Rasm alohida "rasm" element bo‘lib slaydning ikkinchi elementi sifatida turadi (matn chapda, rasm o‘ngda) yoki
"hayotiy" element ichida. Mavzuga mos 3–8 rasm ishlat; bitta rasmni ikki marta ishlatma; "meta.rasm" — titul rasmi.
Ro‘yxatda mos rasm bo‘lmasa yangi kalit yoz (kichik lotin harflari, raqam va _), "rasmlar" ro‘yxatiga "tavsif"
(o‘zbekcha) va "prompt" (inglizcha: flat vector illustration, transparent background, soft colors, no text, centered,
educational) bilan qo‘sh — u hozircha chiqmaydi, chizish uchun ro‘yxatga tushadi.

YOSHGA MOSLASH: maktab 1–4-sinf — oddiy so‘zlar, ko‘p chizma va hayotiy misol; 5–11-sinf — qoida, misol, mashq;
bakalavr — ta’rif, isbot g‘oyasi, metodika (boshlang‘ich sinfda qanday o‘rgatiladi).
"""


HAJM = {"qisqa": "QISQA: slaydda 1–2 jumla yoki 3–4 punkt; izoh 2–3 jumla.",
        "orta": "O‘RTA: slaydda 2–3 jumla yoki 4–5 punkt; izoh 3–5 jumla.",
        "batafsil": "BATAFSIL: slaydda 3–4 jumla yoki 5–6 punkt; izoh 5–8 jumla; har tushunchaga misol."}
TIL = {"uz": "O‘zbek tili (lotin yozuvi)", "ru": "Rus tili (barcha matnlar ruscha; kalitlar o‘zgarmaydi)",
       "en": "Ingliz tili (barcha matnlar inglizcha; kalitlar o‘zgarmaydi)"}
OHANG = {"ilmiy": "ILMIY: aniq atamalar, ta’rif manbasi (muallif, yil), mantiqiy dalil.",
         "oddiy": "ODDIY: tushunarli, hayotiy misollar bilan, ortiqcha atamasiz.",
         "oyinli": "O‘YINLI: qiziqarli savollar, o‘yin slaydlari ko‘p, bolalarga yaqin til."}


def sozlama_toza(z: dict | None) -> dict:
    z = z if isinstance(z, dict) else {}
    try:
        n = int(z.get("slayd_soni") or 0)
    except (TypeError, ValueError):
        n = 0
    return {"slayd_soni": max(6, min(40, n)) if n else 0,
            "hajm": z.get("hajm") if z.get("hajm") in HAJM else "orta",
            "til": z.get("til") if z.get("til") in TIL else "uz",
            "ohang": z.get("ohang") if z.get("ohang") in OHANG else ""}


def _sozlama_matni(z: dict, daraja: str = "") -> str:
    z = sozlama_toza(z)
    ohang = z["ohang"] or ("ilmiy" if daraja in ("bakalavr", "magistr") else "oyinli" if daraja == "bogcha" else "oddiy")
    s = f"TIL: {TIL[z['til']]}.\nMATN HAJMI: {HAJM[z['hajm']]}\nOHANG: {OHANG[ohang]}\n"
    if z["slayd_soni"]:
        b = max(2, min(6, round(z["slayd_soni"] / 5)))
        s += (f"SLAYDLAR SONI: bo‘limlardagi mazmun slaydlari jami {z['slayd_soni']} ta (± 1) — {b} ta bo‘lim, har bo‘limda "
              f"{max(1, min(8, round(z['slayd_soni'] / b)))} tadan ko‘pi bilan 8 ta slayd.\n")
    return s


def _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, sozlama=None):
    s = f"MAVZU: {mavzu}\nFAN: {fan}\nDARAJA: {daraja}\nSINF/KURS: {sinf}\nTUR: {tur}\n"
    s += _sozlama_matni(sozlama or {}, daraja)
    try:
        from .profil import profil_matni
        s += profil_matni(fan, sinf, daraja) + "\n"
    except Exception:
        pass
    try:
        s += f"\nKUTUBXONA RASMLARI (kalit — nima tasvirlangan; avval shulardan tanla):\n{katalog_matni(f'{mavzu} {qoshimcha}', fan)}\n\n"
    except Exception:
        pass
    if qoshimcha:
        s += f"QO‘SHIMCHA TALAB: {qoshimcha}\n"
    if manba:
        s += f"MANBA MATN (shunga tayan, ko‘chirma emas):\n{manba[:12000]}\n"
    s += "\nTo‘liq JSON miyani yoz."
    return s


def provayderlar():
    keys = {
        "gemini": (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY") or "").strip(),
        "openai": os.getenv("OPENAI_API_KEY", "").strip(),
        "groq": os.getenv("GROQ_API_KEY", "").strip(),
    }
    models = {
        "gemini": os.getenv("TAQDIMOT_GEMINI_MODEL") or os.getenv("PRESENTATION_GEMINI_MODEL") or "gemini-2.5-flash",
        "openai": os.getenv("TAQDIMOT_OPENAI_MODEL") or "gpt-4o-mini",
        "groq": os.getenv("TAQDIMOT_GROQ_MODEL") or "openai/gpt-oss-120b",
    }
    order = [x.strip() for x in (os.getenv("TAQDIMOT_AI_PROVIDERS") or os.getenv("PRESENTATION_AI_PROVIDERS") or "gemini,openai,groq").split(",")]
    return [(n, keys[n], models[n]) for n in order if n in keys and keys[n]]


def mavjud():
    return bool(provayderlar())


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _chaqir(nom, kalit, model, system, user, timeout=150):
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.6, "response_format": {"type": "json_object"}}
    if nom == "openai":
        body["max_completion_tokens"] = 16000
    else:
        body["max_tokens"] = 16000
    data = json.dumps(body).encode("utf-8")
    req = request.Request(ENDPOINTS[nom], data=data, method="POST",
                          headers={"Content-Type": "application/json", "Authorization": f"Bearer {kalit}"})
    opener = request.build_opener(_NoRedirect)
    with opener.open(req, timeout=timeout) as r:
        raw = r.read(4 * 1024 * 1024)
    env = json.loads(raw.decode("utf-8"))
    text = env["choices"][0]["message"]["content"]
    return text


def json_ajrat(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("AI javobida JSON topilmadi")
    return json.loads(text[a:b + 1])


def _bir_chaqiruv(system, user, deadline, t0):
    """Provayderlarni navbat bilan sinaydi, JSON obyekt qaytaradi."""
    oxirgi = None
    for nom, kalit, model in provayderlar():
        left = deadline - (time.monotonic() - t0)
        if left < 15:
            break
        try:
            raw = _chaqir(nom, kalit, model, system, user, timeout=min(150, left))
            out = json_ajrat(raw)
            out.setdefault("_ai", {"provayder": nom, "model": model})
            return out
        except (error.URLError, error.HTTPError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
            oxirgi = exc
            continue
    raise RuntimeError(f"AI javob bermadi: {type(oxirgi).__name__ if oxirgi else 'vaqt tugadi'}")


REJA_KORSATMA = """Sen tajribali metodistsan. Mavzu bo‘yicha taqdimot REJASINI tuzasan — faqat tuzilma, to‘liq matn emas.
Javob FAQAT JSON:
{"meta":{"mavzu","qisqa":"2–4 so‘z","maqsad":"1–2 jumla","tayanch":["3–5 tushuncha"]},
 "bolimlar":[{"nom":"bo‘lim nomi","izoh":"1 jumla","slaydlar":[{"sarlavha":"slayd sarlavhasi","maqsad":"bu slaydda nima — 1 jumla",
   "tur":"eng mos element turi: tarif|qoida|misol|masala|jadval|taqqoslash|xossalar|lugat|dialog|parcha|vaqt_chizigi|xarita|tajriba|jarayon|galereya|guruhlash|moslash|togri_notogri|bosh_joy|rasmda_nima|matn"}]}]}
Bo‘limlar mantiqiy ketma-ket: kirish → asosiy tushunchalar → qo‘llash/misollar → mustahkamlash. Sarlavhalar aniq va qisqa (2–7 so‘z),
takrorlanmasin. Fanga va yoshga mos turlarni tanla, har bo‘limda kamida bitta vizual yoki o‘yin turi bo‘lsin."""


def reja_yoz(mavzu, fan="", daraja="maktab", sinf="", tur="dars", qoshimcha="", manba="", sozlama=None, deadline=120.0):
    if not provayderlar():
        raise RuntimeError("AI kaliti sozlanmagan (GEMINI_API_KEY, OPENAI_API_KEY yoki GROQ_API_KEY).")
    z = sozlama_toza(sozlama)
    if not z["slayd_soni"]:
        z["slayd_soni"] = 14
    from .profil import profil_matni
    user = _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, z).replace("To‘liq JSON miyani yoz.", "Faqat REJA JSON'ini yoz.")
    out = _bir_chaqiruv(REJA_KORSATMA + "\n" + profil_matni(fan, sinf, daraja), user, deadline, time.monotonic())
    return reja_toza(out, mavzu)


def reja_toza(r: dict, mavzu: str = "") -> dict:
    """Reja (AI yoki o'qituvchi tahrirlagan) — xavfsiz shaklga."""
    t = sxema.t
    meta = r.get("meta") if isinstance(r.get("meta"), dict) else {}
    bol = []
    for b in (r.get("bolimlar") or [])[:6]:
        if not isinstance(b, dict) or not t(b.get("nom")):
            continue
        sl = []
        for x in (b.get("slaydlar") or [])[:8]:
            if isinstance(x, str):
                x = {"sarlavha": x}
            if isinstance(x, dict) and t(x.get("sarlavha")):
                sl.append({"sarlavha": t(x.get("sarlavha"), 110), "maqsad": t(x.get("maqsad"), 240), "tur": t(x.get("tur"), 30)})
        if sl:
            bol.append({"nom": t(b.get("nom"), 60), "izoh": t(b.get("izoh"), 160), "slaydlar": sl})
    if not bol:
        raise RuntimeError("Reja bo‘sh chiqdi — qayta urinib ko‘ring")
    return {"reja": True, "meta": {"mavzu": t(meta.get("mavzu"), 160) or mavzu, "qisqa": t(meta.get("qisqa"), 60),
                                   "maqsad": t(meta.get("maqsad"), 400), "tayanch": sxema.ls(meta.get("tayanch"), 6, 60)},
            "bolimlar": bol}


def _reja_matni(reja: dict) -> str:
    q = [f"MAVZU: {reja['meta'].get('mavzu')}"]
    for i, b in enumerate(reja["bolimlar"]):
        q.append(f"{i + 1}-bo‘lim: {b['nom']}" + (f" — {b['izoh']}" if b.get("izoh") else ""))
        for sl in b["slaydlar"]:
            q.append(f"   • {sl['sarlavha']}" + (f" [{sl['tur']}]" if sl.get("tur") else "") + (f" — {sl['maqsad']}" if sl.get("maqsad") else ""))
    return "\n".join(q)


def miya_yoz(mavzu, fan="", daraja="maktab", sinf="", tur="dars", qoshimcha="", manba="", deadline=170.0, sozlama=None, reja=None):
    """AI'dan miya oladi va normallashtiradi.

    Kichik taqdimot — bitta chaqiruv. Katta taqdimot (yoki tayyor reja bilan) — avval reja, so'ng har bo'lim alohida
    va «yakun qismlari» alohida, parallel: mazmun chuqurroq, javob uzilib qolmaydi.
    """
    provs = provayderlar()
    if not provs:
        raise RuntimeError("AI kaliti sozlanmagan (GEMINI_API_KEY, OPENAI_API_KEY yoki GROQ_API_KEY).")
    z = sozlama_toza(sozlama)
    t0 = time.monotonic()
    system = korsatma()
    if reja is None and (z["slayd_soni"] or 12) <= 14:
        m = _bir_chaqiruv(system, _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, z), deadline, t0)
        out = sxema.normallashtir(m)
        out["meta"]["mavzu"] = out["meta"]["mavzu"] if out["meta"]["mavzu"] != "Mavzu" else mavzu
        out["meta"]["til"] = z["til"]
        out["_ai"] = m.get("_ai")
        return out
    if reja is None:
        reja = reja_yoz(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, z, deadline=min(70.0, deadline * 0.4))
    else:
        reja = reja_toza(reja, mavzu)
    rmatn = _reja_matni(reja)
    asos = _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, z).replace("To‘liq JSON miyani yoz.", "")
    vazifalar = []
    for i, b in enumerate(reja["bolimlar"]):
        vazifalar.append(("bolim", i, asos + f"\nUMUMIY REJA:\n{rmatn}\n\nFAQAT {i + 1}-BO‘LIMNI to‘liq yoz: "
                          f"{{\"bolim\": {{\"nom\",\"izoh\",\"belgi\",\"slaydlar\":[...]}}, \"rasmlar\":[...]}}. "
                          f"Rejadagi slaydlar ({len(b['slaydlar'])} ta) aynan shu tartibda, shu sarlavhalar bilan; har slaydda \"izoh\" "
                          f"(o‘qituvchi gapi) va 1–3 element. Boshqa bo‘limlarni yozma."))
    vazifalar.append(("yakun", -1, asos + f"\nUMUMIY REJA:\n{rmatn}\n\nBo‘limlarni YOZMA (ular alohida yoziladi). Faqat qolgan qismlarni "
                      "yoz: {\"meta\", \"adabiyotlar\", \"takrorlash\", \"muammo\", \"tarix\", \"xatolar\", \"metodika\", "
                      "\"xulosa\", \"test\" (6 ta, rejadagi mazmun bo‘yicha), \"nazorat\", \"mustaqil_ish\", \"keyingi\"}."))
    from concurrent.futures import ThreadPoolExecutor
    natija = {}
    with ThreadPoolExecutor(max_workers=min(7, len(vazifalar))) as pool:
        fut = {pool.submit(_bir_chaqiruv, system, matn, deadline, t0): (tur_, i) for tur_, i, matn in vazifalar}
        for f, (tur_, i) in fut.items():
            try:
                natija[(tur_, i)] = f.result()
            except Exception as exc:  # bitta bo'lim yiqilsa — rejadagi sarlavhalar bilan oddiy slaydlar
                natija[(tur_, i)] = {"_xato": str(exc)[:120]}
    yakun = natija.get(("yakun", -1)) or {}
    m = {k: v for k, v in yakun.items() if k not in ("bolimlar", "_ai")}
    meta = dict(yakun.get("meta") or {})
    meta.setdefault("mavzu", reja["meta"]["mavzu"])
    for k in ("qisqa", "maqsad", "tayanch"):
        if not meta.get(k) and reja["meta"].get(k):
            meta[k] = reja["meta"][k]
    meta.update({"fan": meta.get("fan") or fan, "daraja": daraja, "sinf": meta.get("sinf") or sinf, "tur": meta.get("tur") or tur, "til": z["til"]})
    m["meta"] = meta
    bolimlar, rasmlar_ = [], list(m.get("rasmlar") or [])
    for i, b in enumerate(reja["bolimlar"]):
        r = natija.get(("bolim", i)) or {}
        bb = r.get("bolim") if isinstance(r.get("bolim"), dict) else (r if r.get("slaydlar") else None)
        if not bb or not bb.get("slaydlar"):
            bb = {"nom": b["nom"], "izoh": b.get("izoh"), "slaydlar": [{"sarlavha": sl["sarlavha"], "elementlar": [
                {"tur": "matn", "matn": sl.get("maqsad") or sl["sarlavha"]}]} for sl in b["slaydlar"]]}
        bb.setdefault("nom", b["nom"])
        bolimlar.append(bb)
        rasmlar_ += [x for x in (r.get("rasmlar") or []) if isinstance(x, dict)]
    m["bolimlar"] = bolimlar
    m["rasmlar"] = rasmlar_[:12]
    out = sxema.normallashtir(m)
    out["meta"]["til"] = z["til"]
    out["_ai"] = yakun.get("_ai")
    return out

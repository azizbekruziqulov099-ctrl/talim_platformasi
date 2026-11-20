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
Bitta slaydda: ko‘pi bilan 3 ta element; jadval/taqqoslash/xossalar odatda yolg‘iz yoki eslatma bilan.

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


def _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba):
    s = f"MAVZU: {mavzu}\nFAN: {fan}\nDARAJA: {daraja}\nSINF/KURS: {sinf}\nTUR: {tur}\n"
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


def miya_yoz(mavzu, fan="", daraja="maktab", sinf="", tur="dars", qoshimcha="", manba="", deadline=170.0):
    """AI'dan miya oladi va normallashtiradi. Bir provayder ishlamasa keyingisi."""
    provs = provayderlar()
    if not provs:
        raise RuntimeError("AI kaliti sozlanmagan (GEMINI_API_KEY, OPENAI_API_KEY yoki GROQ_API_KEY).")
    system = korsatma()
    user = _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba)
    oxirgi = None
    t0 = time.monotonic()
    for nom, kalit, model in provs:
        left = deadline - (time.monotonic() - t0)
        if left < 20:
            break
        try:
            raw = _chaqir(nom, kalit, model, system, user, timeout=min(150, left))
            m = json_ajrat(raw)
            out = sxema.normallashtir(m)
            out["meta"]["mavzu"] = out["meta"]["mavzu"] if out["meta"]["mavzu"] != "Mavzu" else mavzu
            out["_ai"] = {"provayder": nom, "model": model}
            return out
        except (error.URLError, error.HTTPError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
            oxirgi = exc
            continue
    raise RuntimeError(f"AI javob bermadi: {type(oxirgi).__name__ if oxirgi else 'vaqt tugadi'}")


def rasm_chiz(prompt: str, timeout=120):
    """AI rasm (ixtiyoriy, TAQDIMOT_AI_RASM=1 va OPENAI_API_KEY bo'lsa): shaffof fonli PNG bayt."""
    if os.getenv("TAQDIMOT_AI_RASM", "").strip() not in ("1", "true", "yes"):
        return None
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    import base64
    body = {"model": os.getenv("TAQDIMOT_RASM_MODEL", "gpt-image-1"), "prompt": prompt[:1500], "size": "1024x1024",
            "background": "transparent", "quality": os.getenv("TAQDIMOT_RASM_SIFAT", "medium"), "n": 1}
    req = request.Request("https://api.openai.com/v1/images/generations", data=json.dumps(body).encode(), method="POST",
                          headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with request.build_opener(_NoRedirect).open(req, timeout=timeout) as r:
        env = json.loads(r.read(30 * 1024 * 1024))
    b64 = env["data"][0].get("b64_json")
    return base64.b64decode(b64) if b64 else None

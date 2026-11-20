"""Tayyor mavzular kutubxonasi.

kutubxona/<toplam>/reestr.json  — to'plam ro'yxati (mavzular: id, kod, nom, tur, fayl, ...)
kutubxona/<toplam>/miya/         — taqdimot-miya JSON'lari (dvigatel shu bilan ishlaydi)
kutubxona/<toplam>/oqituvchi/    — o'qituvchi matni (.md)
kutubxona/<toplam>/javoblar/     — test va mustaqil ish javoblari (faqat admin)
kutubxona/<toplam>/mustaqil/     — mustaqil ta'lim topshirig'i (.md) va rejasi (.json)

Yangi paket kelganda shu tuzilishda yangi papka qo'shiladi — kod o'zgarmaydi.
"""
from __future__ import annotations

import copy
import json
import math
import os
import re
from functools import lru_cache

PAPKA = os.getenv("TAQDIMOT_KUTUBXONA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "kutubxona")
NOM = re.compile(r"^[a-z0-9_\-]{1,40}$")
KOD = re.compile(r"^[A-Za-z0-9_\-]{1,20}$")
TUR_NOMI = {"maruza": "Ma’ruza", "amaliy": "Amaliy", "mustaqil": "Mustaqil ta’lim"}


def _yol(*qism):
    p = os.path.realpath(os.path.join(PAPKA, *qism))
    if not p.startswith(os.path.realpath(PAPKA) + os.sep):
        return None
    return p


@lru_cache(maxsize=64)
def _reestr(toplam: str, mtime: float):
    with open(_yol(toplam, "reestr.json"), encoding="utf-8") as f:
        return json.load(f)


def reestr(toplam: str):
    if not NOM.match(toplam or ""):
        return None
    p = _yol(toplam, "reestr.json")
    if not p or not os.path.isfile(p):
        return None
    return _reestr(toplam, os.path.getmtime(p))


def toplamlar():
    out = []
    if not os.path.isdir(PAPKA):
        return out
    for nom in sorted(os.listdir(PAPKA)):
        r = reestr(nom)
        if r:
            out.append({"kod": nom, "nom": r.get("nom") or nom, "mavzular": len(r.get("mavzular") or [])})
    return out


def mavzular(toplam: str):
    """Ochiq ro'yxat: javob fayllari nomlari ko'rsatilmaydi, faqat bor-yo'qligi."""
    r = reestr(toplam)
    if not r:
        return None
    items = []
    for m in r.get("mavzular") or []:
        items.append({
            "id": m.get("id"), "kod": m.get("kod"), "nom": m.get("nom"), "tur": m.get("tur"),
            "tur_nomi": TUR_NOMI.get(m.get("tur"), m.get("tur")),
            "slaydlar": m.get("slaydlar"), "testlar": m.get("testlar"),
            "oqituvchi": bool(m.get("oqituvchi")), "topshiriq": bool(m.get("topshiriq")),
            "reja": bool(m.get("reja")), "javoblar": bool(m.get("javoblar")),
        })
    return {"kod": toplam, "nom": r.get("nom"), "manba": r.get("manba"), "mavzular": items}


def _mavzu(toplam: str, kod: str):
    r = reestr(toplam)
    if not r or not KOD.match(kod or ""):
        return None
    for m in r.get("mavzular") or []:
        if (m.get("kod") or "").lower() == kod.lower() or (m.get("id") or "").lower() == kod.lower():
            return m
    return None


def _oqi(toplam, papka, fayl, binar=False):
    if not fayl:
        return None
    p = _yol(toplam, papka, os.path.basename(fayl))
    if not p or not os.path.isfile(p):
        return None
    with open(p, "rb") as f:
        data = f.read()
    return data if binar else data.decode("utf-8")


def miya(toplam: str, kod: str, chizmali: bool = True):
    """Mavzu miyasi. chizmali=True: reestrdagi tayyor chizmalar mos slaydlarga joylanadi."""
    m = _mavzu(toplam, kod)
    if not m:
        return None
    txt = _oqi(toplam, "miya", m.get("fayl"))
    if not txt:
        return None
    d = json.loads(txt)
    if chizmali and m.get("chizmalar"):
        jt = _oqi(toplam, "", "joylash.json")
        joy = json.loads(jt) if jt else {}
        pref = (m.get("kod") or "") + ":"
        d = chizmalarni_joyla(d, m["chizmalar"], {k[len(pref):]: v for k, v in joy.items() if k.startswith(pref)})
    return d


# --- Tayyor chizmalarni mos slaydga joylash ---
_APO = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'", "−": "-", "–": "-", "²": "2", "³": "3", "×": "x"})
_SOZ = re.compile(r"[a-z']+|\d+(?:[.,]\d+)?")
_KENG = {"jadval", "taqqoslash", "xossalar"}
_VIZUAL = {"rasm", "chizma"}


_TOXTA = {"ning", "dan", "bilan", "uchun", "bir", "xil", "har", "shu", "ham", "emas", "yoki", "kabi", "orqali",
          "alohida", "boshqa", "qilinsin", "berilsin", "yozilsin", "belgilansin", "ajratilsin", "qo'yilsin", "panel",
          "panelda", "ikki", "uch", "ikkala", "uchala", "model", "modeli"}


def _tokenlar(text: str):
    out = set()
    for t in _SOZ.findall((text or "").lower().translate(_APO)):
        t = t.strip("'")
        if t[:1].isdigit():
            if len(t) >= 2:
                out.add(t)
        elif len(t) >= 3 and t not in _TOXTA:
            out.add(t.replace("'", "")[:4])
    return out


def _slayd_matni(sl):
    qism = [sl.get("sarlavha") or "", sl.get("sarlavha") or ""]
    for e in sl.get("elementlar") or []:
        for v in e.values():
            if isinstance(v, str):
                qism.append(v)
            elif isinstance(v, list):
                qism.extend(x if isinstance(x, str) else json.dumps(x, ensure_ascii=False) for x in v)
    return " ".join(qism)


def chizmalarni_joyla(d: dict, chizmalar: list, joylash: dict | None = None):
    """Har chizma talabini mavzuning eng mos slaydiga qo'yadi.

    joylash: {talab_id: "slayd sarlavhasi"} — avtomatik tanlov o'rniga qo'lda belgilangan slayd
    (kutubxona/<toplam>/joylash.json, kalit "M6:K02-04").

    Slaydda bitta (keng bo'lmagan) element va hech qanday rasm bo'lmasa — chizma yoniga qo'shiladi
    (matn chapda, chizma o'ngda). Aks holda shu slayddan keyin chizmaning alohida slaydi ochiladi.
    """
    d = copy.deepcopy(d)
    joylar = []  # (bolim_i, slayd_i)
    for bi, b in enumerate(d.get("bolimlar") or []):
        for si, _ in enumerate(b.get("slaydlar") or []):
            joylar.append((bi, si))
    if not joylar:
        return d
    toklar = [_tokenlar(_slayd_matni(d["bolimlar"][bi]["slaydlar"][si])) for bi, si in joylar]
    sarl = [_tokenlar(d["bolimlar"][bi]["slaydlar"][si].get("sarlavha") or "") for bi, si in joylar]
    n = len(toklar)
    ortacha = max(1.0, sum(len(t) for t in toklar) / n)
    df = {}
    for t in toklar:
        for x in t:
            df[x] = df.get(x, 0) + 1
    band = set()
    qoshimcha = {}  # (bi, si) -> [yangi slaydlar]
    for ch in chizmalar:
        kalitlar = [k for k in ch.get("kalitlar") or [] if k]
        if not kalitlar:
            continue
        qn = _tokenlar(ch.get("nom") or "")
        q = qn | _tokenlar(ch.get("talab") or "")
        ballar = []
        for i, t in enumerate(toklar):
            ball = sum(math.log((n + 1) / df[x]) * (2 if x in qn else 1) * (1.5 if x in sarl[i] else 1) for x in q & t)
            ballar.append(ball / (0.6 + 0.4 * len(t) / ortacha))  # uzun slayd faqat so'z ko'pligi bilan yutmasin
        eng = max(ballar)
        eng_i = ballar.index(eng) if eng > 0 else n - 1
        qolda = (joylash or {}).get(ch.get("id"))
        if qolda:
            for i, (b_, s_) in enumerate(joylar):
                if (d["bolimlar"][b_]["slaydlar"][s_].get("sarlavha") or "").strip() == qolda.strip():
                    eng_i, eng = i, 0.0
                    ballar = [0.0] * n
                    break

        def sigadi(i):
            b_, s_ = joylar[i]
            sl_ = d["bolimlar"][b_]["slaydlar"][s_]
            els_ = [e for e in sl_.get("elementlar") or [] if e.get("tur") != "eslatma"]
            return (len(kalitlar) == 1 and i not in band and len(els_) == 1 and els_[0].get("tur") not in _KENG
                    and not any(e.get("tur") in _VIZUAL or e.get("chizma") or e.get("rasm") for e in sl_.get("elementlar") or []))
        yoniga = sigadi(eng_i)
        if not yoniga and eng > 0 and not qolda:
            # deyarli teng mos, lekin chizma sig'adigan slayd bo'lsa — o'sha afzal
            nomzod = [i for i, b in enumerate(ballar) if b >= 0.85 * eng and sigadi(i)]
            if nomzod:
                eng_i = max(nomzod, key=lambda i: ballar[i])
                yoniga = True
        bi, si = joylar[eng_i]
        sl = d["bolimlar"][bi]["slaydlar"][si]
        if yoniga:
            sl.setdefault("elementlar", []).append({"tur": "rasm", "rasm": kalitlar[0], "izoh": ch.get("nom") or ""})
            band.add(eng_i)
        else:
            # alohida slayd: yaqin ball olgan slaydlarning eng keyingisidan so'ng (tushunchalar oldin kiritilsin)
            yaqin = [i for i, b in enumerate(ballar) if eng > 0 and b >= 0.75 * eng and joylar[i][0] == bi]
            if yaqin:
                bi, si = joylar[max(yaqin)]
            yangi = {"sarlavha": ch.get("nom") or "Chizma",
                     "elementlar": [{"tur": "rasm", "rasm": k, "izoh": ""} for k in kalitlar[:2]]}
            qoshimcha.setdefault((bi, si), []).append(yangi)
    for (bi, si) in sorted(qoshimcha, reverse=True):
        d["bolimlar"][bi]["slaydlar"][si + 1:si + 1] = qoshimcha[(bi, si)]
    return d


def hujjat(toplam: str, kod: str, tur: str):
    """tur: oqituvchi | topshiriq | reja | javoblar → (nom, bytes, mime) yoki None."""
    m = _mavzu(toplam, kod)
    if not m:
        return None
    papka = {"oqituvchi": "oqituvchi", "topshiriq": "mustaqil", "reja": "mustaqil", "javoblar": "javoblar"}.get(tur)
    if not papka or not m.get(tur):
        return None
    data = _oqi(toplam, papka, m[tur], binar=True)
    if data is None:
        return None
    mime = "text/markdown; charset=utf-8" if m[tur].endswith(".md") else "application/json"
    return os.path.basename(m[tur]), data, mime

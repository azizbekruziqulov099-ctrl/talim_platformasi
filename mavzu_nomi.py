"""REV101: AI miya kitobidagi mavzu NOMI → Mavzular bazasidagi kod.

Kitob varag'ida «Mavzu kodi (DTS)» bo'sh bo'lsa, mavzu shu nom bo'yicha bazadan topiladi. Qoidalar:
  1. Kitob qaysi sinf / yosh guruhi uchun bo'lsa — faqat o'sha guruh mavzulari olinadi.
     6-7 yosh kitobi 4-5 yosh mavzusiga ulanmaydi (oldin «O'tgan yilni eslaymiz» 4-5 yoshdan topilardi).
  2. Fan: bog'chada har doim qat'iy — 10 til kitobida dars nomlari bir xil («O'n bir va o'n ikki»),
     Rus tili darsi Ingliz tili mavzusiga ulanib ketmasin. Maktab/institutda kitob fani shu sinfda bazada
     bor bo'lsa — faqat shu fan; umuman yo'q bo'lsa (fan nomi boshqacha yozilgan) — shu sinf ichidan.
  3. Bir xil nomli nusxalar (bitta fan, guruh va dasturda; masalan 1- va 3-blokda ikki marta yaratilgan):
     kitob mavzulari ko'proq turgan blok/bobdagi nusxa olinadi, ortiqchasi ogohlantirishda aytiladi.
Kitob sinfi noma'lum matn bo'lsa (masalan «Abituriyent») — eski tartib: avval shu fan, keyin butun baza.
"""
from __future__ import annotations

import re
from collections import Counter

from modules.curriculum_scope import PRESCHOOL_GROUPS, canonical_grade, preschool_group

_APOS = "‘’ʻʼ`'"


def nom_norm(value) -> str:
    """Solishtirish kaliti: kichik harf, tutuq va tinish belgilarisiz, «3-mavzu.» kabi boshlanishsiz."""
    text = ("" if value is None else str(value)).strip().lower()
    for ch in _APOS:
        text = text.replace(ch, "")
    text = re.sub(r"^\s*(?:\d+\s*[-–]?\s*(?:mavzu|dars)|§\s*\d+)\s*[.:)\-–]?\s*", "", text)
    return re.sub(r"[^0-9a-zа-яёқғҳў]+", "", text)


def kod_qismlari(code):
    """«3-4 yosh-01-01-01-01-29-001» → («3-4 yosh-01-01-01-01», 29): mavzugacha bo'lgan joy va mavzu raqami."""
    text = str(code)
    if text.count("-") < 2:
        return text, None
    head, number, _ = text.rsplit("-", 2)
    try:
        return head, int(number)
    except ValueError:
        return head, None


def kitob_guruhi(sinf) -> str:
    """Kitobning «Sinf» qiymati → bazadagi ko'rinish: «6–7 yosh» / «6-7» → «6-7 yosh», «5-sinf» → «5»."""
    if not str(sinf or "").strip():
        return ""
    return preschool_group(sinf) or canonical_grade(sinf)


def taniqli_guruh(group) -> bool:
    """Aniq sinf/guruh: bog'cha guruhi, 1–11-sinf yoki «N kurs» / «N kurs magistr»."""
    group = str(group or "")
    return (group in PRESCHOOL_GROUPS
            or (group.isdigit() and 1 <= int(group) <= 11)
            or bool(re.fullmatch(r"[1-6] kurs(?: magistr)?", group)))


def guruh_nomi(group) -> str:
    group = str(group or "")
    return f"{group}-sinf" if group.isdigit() else group


def joy_nomi(group, fan) -> str:
    """Xabar uchun: «6-7 yosh · Ingliz tili»."""
    return " · ".join(x for x in (guruh_nomi(group), str(fan or "").strip()) if x)


def baza_indeksi(rows):
    """dts_tree qatorlari (topic_code, subject_name, grade, nom, …) → nom bo'yicha indeks + bazadagi guruh va fanlar."""
    index, groups, subjects = {}, set(), set()
    for row in rows:
        group = canonical_grade(row.get("grade"))
        index.setdefault(nom_norm(row.get("nom")), []).append(row)
        groups.add(group)
        subjects.add((group, nom_norm(row.get("subject_name"))))
    return {"index": index, "guruhlar": groups, "fanlar": subjects}


def nomzodlar(baza, nom, fan_n, group):
    """Bir mavzu nomi uchun nomzodlar. Qaytaradi: (tanlanganlar, shu nomdagi boshqa joy qatorlari).

    fan_n — kitob fanining nom_norm kaliti, group — kitob_guruhi() natijasi."""
    rows = baza["index"].get(nom_norm(nom), [])

    def fan_mos(row):
        return bool(fan_n) and nom_norm(row.get("subject_name")) == fan_n

    same_fan = [r for r in rows if fan_mos(r)]
    if group and (group in baza["guruhlar"] or taniqli_guruh(group)):
        in_group = [r for r in rows if canonical_grade(r.get("grade")) == group]
        same = [r for r in in_group if fan_mos(r)]
        if not fan_n:
            pick = in_group
        elif group in PRESCHOOL_GROUPS or same or (group, fan_n) in baza["fanlar"]:
            pick = same
        else:
            pick = in_group
    else:
        same_grade = [r for r in same_fan if group and canonical_grade(r.get("grade")) == group]
        pick = same_grade or same_fan or rows
    chosen = {id(r) for r in pick}
    return pick, [r for r in rows if id(r) not in chosen]


def boshqa_joylar(rows, limit=3) -> str:
    """«4-5 yosh · INGLIZ TILI; 4-5 yosh · RUS TILI» — shu nom bazada qayerda borligi."""
    seen = []
    for row in rows:
        place = joy_nomi(canonical_grade(row.get("grade")), row.get("subject_name"))
        if place and place not in seen:
            seen.append(place)
    return "; ".join(seen[:limit]) + (f" va yana {len(seen) - limit} joy" if len(seen) > limit else "")


def _bir_joyda(codes, meta) -> bool:
    """Hamma nomzod bitta fan, guruh va dasturda (faqat blok/bob/bo'lim boshqa) — ya'ni aynan nusxa."""
    keys = set()
    for code in codes:
        row = meta.get(code)
        if not row:
            return False
        keys.add((canonical_grade(row.get("grade")), nom_norm(row.get("subject_name")), row.get("curriculum_scope_id")))
    return len(keys) == 1


def nusxadan_tanla(ambiguous, pending, resolved, linked=None, meta=None):
    """Bir xil nomli mavzular orasidan ball bilan tanlash. Qaytaradi: {placeholder: (kod, sabab)} — faqat g'olib bo'lsa.

    ambiguous — {placeholder: [kodlar]}, pending — {placeholder: {"nom", "raqam", …}}, resolved — aniq topilganlar
    {placeholder: kod}, linked — {kod: avval bog'langan dars/test soni}, meta — {kod: bazadagi qator}."""
    linked, meta = linked or {}, meta or {}
    homes = Counter(kod_qismlari(c)[0] for c in resolved.values())
    home = homes.most_common(1)[0][0] if homes else ""
    # REV101: kitobning nusxali mavzulari qaysi blok/bobda ko'proq turgan bo'lsa — o'sha nusxa.
    cover = Counter(h for codes in ambiguous.values() for h in {kod_qismlari(c)[0] for c in codes})
    names = Counter(nom_norm(info.get("nom")) for info in pending.values())
    out = {}
    for placeholder, codes in ambiguous.items():
        number = pending[placeholder].get("raqam")
        scored = []
        for code in codes:
            head, mavzu_no = kod_qismlari(code)
            score, why = 0, []
            if home and head == home:
                score += 3
                why.append("kitobning boshqa mavzulari bilan bir bobda")
            if number and mavzu_no == number:
                score += 2
                why.append(f"tartib raqami {number} mos")
            if linked.get(code):
                score += 2
                why.append("unga avval dars/test bog'langan")
            scored.append((score, code, why))
        scored.sort(key=lambda x: (-x[0], x[1]))
        if scored[0][0] > 0 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
            out[placeholder] = (scored[0][1], ", ".join(scored[0][2]))
            continue
        # Kitobda bu nom bir marta uchraydi, bazadagi nusxalar esa bitta fan/guruh/dasturda — bittasini olamiz.
        if names[nom_norm(pending[placeholder].get("nom"))] == 1 and _bir_joyda(codes, meta):
            tied = [code for score, code, _ in scored if score == scored[0][0]]
            best = min(tied, key=lambda c: (-cover[kod_qismlari(c)[0]], kod_qismlari(c)[0], c))
            out[placeholder] = (best, "nusxalar bir xil — kitobning boshqa mavzulari ham shu blokda")
    return out

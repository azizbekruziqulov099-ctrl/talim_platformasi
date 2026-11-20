"""Slayddagi tayyor yorliqlar tarjimasi (rus, ingliz taqdimotlari uchun).

Mazmunni AI o'sha tilda yozadi; bu yerda faqat dvigatelning o'z yozuvlari («Ta'rif», «Reja», «Javob:», «1-savol» ...)
almashtiriladi. Tarjima matn joylashtirilishidan OLDIN qilinadi (Slayd.matn), shuning uchun o'lchamlar to'g'ri.
"""
from __future__ import annotations

import re
from functools import lru_cache

LUG = {
    "Ta'rif": ("Определение", "Definition"), "Qoida": ("Правило", "Rule"), "Teorema": ("Теорема", "Theorem"),
    "Formula": ("Формула", "Formula"), "Misol": ("Пример", "Example"), "Masala": ("Задача", "Problem"), "Muhim": ("Важно", "Important"),
    "Diqqat": ("Внимание", "Note"), "Savol": ("Вопрос", "Question"), "Hayotdan": ("Из жизни", "Real life"),
    "Reja": ("План", "Outline"), "Boshlash  ›": ("Начать  ›", "Start  ›"),
    "Adabiyotlar va manbalar": ("Литература и источники", "References and sources"), "Adabiyotlar": ("Литература", "References"),
    "Asosiy adabiyotlar": ("Основная литература", "Main literature"), "Elektron manbalar": ("Электронные ресурсы", "Online resources"),
    "Mustaqil o‘qish": ("Самостоятельное чтение", "Further reading"),
    "O‘tgan mavzuni takrorlash · o‘yin": ("Повторение прошлой темы · игра", "Review of the previous topic · game"),
    "«Blits-so‘rov» o‘yini": ("Игра «Блиц-опрос»", "«Quick quiz» game"),
    "Avval o‘zingiz javob bering, so‘ng kartani bosing — javob chiqadi": (
        "Сначала ответьте сами, затем нажмите на карточку — появится ответ", "Answer first, then click the card to reveal the answer"),
    "«Mosini top» o‘yini": ("Игра «Найди пару»", "«Find the match» game"),
    "Mundarija · interaktiv": ("Содержание · интерактивно", "Contents · interactive"),
    "Kerakli bo‘limni bosing — o‘sha joyga o‘tasiz": ("Нажмите на раздел — перейдёте к нему", "Click a section to jump to it"),
    "Tipik xatolar: toping va tuzating!": ("Типичные ошибки: найдите и исправьте!", "Common mistakes: find and fix them!"),
    "Avval xatoni o‘zingiz toping, so‘ng kartani bosing — tuzatilgan javob chiqadi": (
        "Сначала найдите ошибку сами, затем нажмите на карточку — появится исправление", "Find the mistake first, then click the card to see the fix"),
    "Interaktiv test: javob variantini bosing": ("Интерактивный тест: выберите ответ", "Interactive quiz: click an answer"),
    "To‘g‘ri variant bosilsa — yashil ✓, noto‘g‘ri bosilsa — qizil ✗": ("Верный ответ — зелёная ✓, неверный — красный ✗",
                                                                     "Correct answer — green ✓, wrong — red ✗"),
    "Nazorat, mustaqil ish va keyingi mavzu": ("Контроль, самостоятельная работа и следующая тема", "Review, homework and next topic"),
    "Nazorat savollari": ("Контрольные вопросы", "Review questions"), "Mustaqil ish": ("Самостоятельная работа", "Independent work"),
    "Keyingi mavzu": ("Следующая тема", "Next topic"), "E’tiboringiz uchun rahmat!": ("Спасибо за внимание!", "Thank you for your attention!"),
    "Ma’ruza matni slayd izohlarida (Notes) berilgan.": ("Текст лекции — в заметках к слайдам (Notes).", "The lecture text is in the slide notes."),
    "O‘tgan mavzu": ("Прошлая тема", "Previous topic"), "Ma’ruza rejasi": ("План лекции", "Lecture outline"),
    "Muammoli vaziyat": ("Проблемная ситуация", "Problem situation"), "Tarixdan": ("Из истории", "From history"),
    "✗ xato": ("✗ ошибка", "✗ mistake"),
    "Boshlang‘ich sinfda qanday o‘rgatamiz?": ("Как учить этому в начальной школе?", "How to teach it in primary school?"),
    "Xulosa: «B/B/B» jadvali": ("Итог: таблица «З/Х/У»", "Summary: K-W-L chart"),
    "Xulosa va nazorat": ("Итоги и контроль", "Summary and review"), "Metodika va yakun": ("Методика и итоги", "Methods and summary"),
    "Xulosa": ("Итог", "Summary"), "Javob:": ("Ответ:", "Answer:"), "Javob": ("Ответ", "Answer"), "G‘oya:": ("Идея:", "Idea:"),
    "To‘g‘ri:": ("Верно:", "Correct:"), "Metodik tavsiya:": ("Методическая рекомендация:", "Teaching tip:"),
    "Bilishni xohlayman": ("Хочу узнать", "Want to know"), "Bilaman": ("Знаю", "Know"), "Bilib oldim": ("Узнал(а)", "Learned"),
    "Ma’ruzachi": ("Лектор", "Lecturer"), "Muallif": ("Автор", "Author"),
    "Dars maqsadi:": ("Цель урока:", "Lesson goal:"), "Ma’ruza maqsadi:": ("Цель лекции:", "Lecture goal:"),
    "Jihozlar": ("Оборудование", "Equipment"), "Bosqichlar": ("Ход работы", "Steps"), "Natija": ("Результат", "Result"),
    "Maqsad": ("Цель", "Aim"), "To‘g‘rimi? — bosing": ("Верно? — нажмите", "True? — click"),
    "Rasmda nima?": ("Что на картинке?", "What is in the picture?"), "Xavfsizlik": ("Безопасность", "Safety"),
    "✓ To‘g‘ri": ("✓ Верно", "✓ True"), "✗ Noto‘g‘ri": ("✗ Неверно", "✗ False"), "BO‘LIM": ("РАЗДЕЛ", "SECTION"),
    "DARS": ("УРОК", "LESSON"), "MA’RUZA": ("ЛЕКЦИЯ", "LECTURE"), "MA'RUZA": ("ЛЕКЦИЯ", "LECTURE"), "AMALIY": ("ПРАКТИКА", "PRACTICE"),
    "SEMINAR": ("СЕМИНАР", "SEMINAR"), "LABORATORIYA": ("ЛАБОРАТОРНАЯ", "LAB"),
}
_TURLAR = {"DARS": ("УРОК", "LESSON"), "MA’RUZA": ("ЛЕКЦИЯ", "LECTURE"), "MA'RUZA": ("ЛЕКЦИЯ", "LECTURE"),
           "AMALIY": ("ПРАКТИКА", "PRACTICE"), "SEMINAR": ("СЕМИНАР", "SEMINAR")}
_HARF = r"[\w‘’'ʻ]"


@lru_cache(maxsize=4)
def _qoidalar(til: str):
    i = {"ru": 0, "en": 1}[til]
    lug = {}
    for k, v in LUG.items():
        lug[k] = v[i]
        lug.setdefault(k.upper(), v[i].upper())
    kalitlar = sorted(lug, key=len, reverse=True)
    parts = []
    for k in kalitlar:
        p = re.escape(k)
        if re.match(_HARF, k[0]):
            p = f"(?<!{_HARF})" + p
        if re.match(_HARF, k[-1]):
            p = p + f"(?!{_HARF})"
        parts.append(p)
    rx = re.compile("|".join(parts))
    dinamik = [
        (re.compile(r"(\d+)–(\d+)-slaydlar"), ("слайды \\1–\\2", "slides \\1–\\2")[i]),
        (re.compile(r"(\d+)-slayd(?!\w)"), ("слайд \\1", "slide \\1")[i]),
        (re.compile(r"(\d+)-savol(?!\w)", re.I), ("Вопрос \\1", "Question \\1")[i]),
        (re.compile(r"(\d+)-masala(?!\w)", re.I), ("Задача \\1", "Problem \\1")[i]),
        (re.compile(r"(\d+)-BO‘LIM"), ("РАЗДЕЛ \\1", "SECTION \\1")[i]),
        (re.compile(r"(\d+)-bo['‘’]lim(?!\w)"), ("Раздел \\1", "Section \\1")[i]),
    ]
    turlar = re.compile(r"(\d+)-(" + "|".join(re.escape(t) for t in _TURLAR) + r")(?!\w)")
    return lug, rx, dinamik, turlar, i


def tarjimon(til: str | None):
    """Til uchun tarjima funksiyasi; o'zbekcha (yoki noma'lum til) — None."""
    if til not in ("ru", "en"):
        return None
    lug, rx, dinamik, turlar, i = _qoidalar(til)

    def tr(matn: str) -> str:
        if not matn or not isinstance(matn, str):
            return matn
        s = turlar.sub(lambda m_: f"{_TURLAR[m_.group(2)][i]} {m_.group(1)}", matn)
        for r, v in dinamik:
            s = r.sub(v, s)
        return rx.sub(lambda m_: lug[m_.group(0)], s)
    return tr

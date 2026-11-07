"""REV260: «Xalqaro baholash» — TIMSS/PISA darajasida o'qitish, mashq, takrorlash va haqiqiy imtihonlar.

Kontent (modules/xalqaro_data/*.json):
  * savollar.json — TIMSS 2011 ochiq savollariga PARALLEL (o'zimiz yozgan) savollar: har asl savolga 2 variant,
    soha, mavzu, fikrlash darajasi, asl savolning xalqaro statistikasi (davlatlar bo'yicha to'g'ri yechganlar foizi).
    Asl IEA savollari ko'chirilmagan — IEA ularni tijoriy maqsadda ishlatishni taqiqlaydi.
  * darslar.json  — har mavzuga Kabu darsi (doska satri + ovoz, [1], [2] belgilari bilan bir xil ketadi).
  * ramka.json    — to'plamlar (4/8-sinf, matematika/tabiiy fanlar), mavzular, maktab dasturi bilan bog'lanish.
  * natijalar.json— davlatlarning haqiqiy TIMSS/PISA/PIRLS ballari (manbalari bilan), O'zbekiston natijalari.

API (hammasi JWT bilan):
  GET  /api/xalqaro/katalog                — sinfga mos to'plamlar, mavzular, o'quvchining bilimi, ustoz gapi (motivatsiya/tanbeh)
  GET  /api/xalqaro/mavzu/{kalit}          — mavzu tafsiloti: dars kodi, statistikasi, strategiyalar, maktab darslari, reyting
  GET  /api/xalqaro/mavzu_oldi             — maktab mavzusidan oldin: mos xalqaro mavzu, namuna savollar, daraja, gap
  GET  /api/xalqaro/mashq                  — mashq savollari (javob va yechimi bilan)
  POST /api/xalqaro/javob                  — mashq javobi: server tekshiradi, bilim va takrorlash navbati yangilanadi
  GET  /api/xalqaro/takror                 — bugun takrorlanadigan savollar (Leitner qutilari)
  GET  /api/xalqaro/imtihonlar             — haftalik / oylik / choraklik / yillik imtihonlar holati
  POST /api/xalqaro/imtihon/boshla         — imtihon (javobsiz savollar, server vaqti)
  POST /api/xalqaro/imtihon/topshir        — server baholaydi: foiz, taxminiy TIMSS bali, darajasi, davlatlar bilan solishtirish
  GET  /api/xalqaro/imtihon/{id}           — topshirilgan imtihon tahlili (yechimlar bilan)
  GET  /api/xalqaro/reyting                — sinfdoshlar / maktab / platforma va davlatlar orasida o'rin
  GET  /api/xalqaro/natijalar              — davlatlar natijalari (yillar kesimida)
  GET  /api/xalqaro/xatolarim              — o'quvchi: hozir ham xato bo'lib turgan savollari (bergan javobi, to'g'risi, yechimi) va zaif mavzulari
  GET  /api/xalqaro/kuzatuv                — kim: admin (maktablar, platforma jamlamasi) / o'qituvchi / o'quvchi
  GET  /api/xalqaro/sinf_natija            — o'qituvchi (o'z maktabi) / admin (istalgan): sinf o'quvchilari — faollik, ball, zaif mavzu
  GET  /api/xalqaro/sinf_xatolar           — sinfda eng ko'p xato qilingan savollar (eng ko'p tanlangan noto'g'ri javob va sababi) va mavzular
  GET  /api/xalqaro/oquvchi/{id}           — bitta o'quvchi: mavzular, xatolari, imtihonlar tarixi
  GET  /api/xalqaro/rasm/{savol}/{v}.svg   — savol rasmi
Dars xonasi «XB-…» kodli darslarni shu moduldagi dars_payload() orqali ochadi.
"""
import hashlib
import json
from starlette.concurrency import run_in_threadpool   # REV319
import math
import os
import random
import re
import threading
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional

try:
    from platform_core.ddl_guard import LazyMigration as _LazyMigration
except ImportError:   # pragma: no cover
    _LazyMigration = None

# REV320: kontent BAZADAN (Admin → Miya → «🌍 Xalqaro savollar», Excel). Kod ichida kontent fayllari yo'q;
# XB_DATA_DIR — faqat testlar uchun (tests/fixtures/xalqaro_data).
DATA_DIR = os.environ.get("XB_DATA_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "xalqaro_data")
TZ = timezone(timedelta(hours=5))
OPTION_LETTERS = "ABCD"
QUTI_KUN = [0, 1, 2, 4, 8, 16]          # Leitner: quti → necha kundan keyin qayta so'raladi
DARAJALAR = [(625, "ilgor", "Ilg‘or"), (550, "yuqori", "Yuqori"), (475, "orta", "O‘rta"), (400, "past", "Past")]
THETA_SD = 1.15                          # o'quvchilar qobiliyatining tarqalishi (logit) — 100 TIMSS baliga teng
REYTING_MIN = 3

# Imtihon turlari: savollar soni va vaqti (daqiqa) — 4-sinf va 8-sinf uchun alohida. TIMSS: 4-sinf qismi 36 daqiqa, 8-sinf — 45.
# REV262: "P" — PISA (15 yosh): bir birlikka ~2 daqiqa; yillik — 2 soatlik haqiqiy PISA kabi (2 × 60 daqiqa).
IMTIHON_TURLARI = {
    "haftalik": {"nom": "Haftalik nazorat", "4": (10, 15), "8": (12, 18), "P": (8, 20)},
    "oylik": {"nom": "Oylik imtihon", "4": (18, 27), "8": (22, 33), "P": (16, 40)},
    "choraklik": {"nom": "Choraklik imtihon (1-qism)", "4": (24, 36), "8": (30, 45), "P": (24, 60)},
    "yillik": {"nom": "Yillik imtihon (to‘liq daftar, 2 qism)", "4": (24, 36), "8": (30, 45), "P": (24, 60)},   # har qism
}
# TIMSS 2011 ramkasi: mazmun sohalari va fikrlash darajalari ulushi (imtihon savollari shu nisbatda tanlanadi)
REJA = {
    "T11_G4_M": {"soha": {"son": 0.50, "geometriya": 0.35, "malumot": 0.15}, "fikrlash": {"bilish": 0.40, "qollash": 0.40, "mulohaza": 0.20}},
    "T11_G8_M": {"soha": {"son": 0.30, "algebra": 0.30, "geometriya": 0.20, "malumot": 0.20}, "fikrlash": {"bilish": 0.35, "qollash": 0.40, "mulohaza": 0.25}},
    "T11_G4_S": {"soha": {"hayot": 0.45, "fizika": 0.35, "yer": 0.20}, "fikrlash": {"bilish": 0.40, "qollash": 0.40, "mulohaza": 0.20}},
    "T11_G8_S": {"soha": {"biologiya": 0.35, "kimyo": 0.20, "fizika": 0.25, "yer": 0.20}, "fikrlash": {"bilish": 0.35, "qollash": 0.35, "mulohaza": 0.30}},
    # PISA ramkalari (mazmun sohalari / jarayonlar ulushi)
    "P_M": {"soha": {"miqdor": 0.25, "noaniqlik": 0.25, "ozgarish": 0.25, "fazo": 0.25}, "fikrlash": {"bilish": 0.25, "qollash": 0.45, "mulohaza": 0.30}},
    "P_R": {"soha": {"topish": 0.25, "tushunish": 0.45, "baholash": 0.30}, "fikrlash": {"bilish": 0.30, "qollash": 0.40, "mulohaza": 0.30}},
    "P_S": {"soha": {"tushuntirish": 0.40, "tadqiqot": 0.25, "talqin": 0.35}, "fikrlash": {"bilish": 0.30, "qollash": 0.40, "mulohaza": 0.30}},
    "P_F": {"soha": {"pul": 0.30, "reja": 0.30, "xavf": 0.25, "muhit": 0.15}, "fikrlash": {"bilish": 0.30, "qollash": 0.40, "mulohaza": 0.30}},
}
# Davlatlar bilan solishtirish jadvallari (natijalar.json kalitlari)
SOLISHTIRISH = {
    "T11_G4_M": [("TIMSS 2023", "TIMSS 2023 M4"), ("TIMSS 2019", "TIMSS 2019 M4")],
    "T11_G8_M": [("TIMSS 2023", "TIMSS 2023 M8"), ("TIMSS 2019", "TIMSS 2019 M8")],
    "T11_G4_S": [("TIMSS 2023", "TIMSS 2023 S4"), ("TIMSS 2019", "TIMSS 2019 S4")],
    "T11_G8_S": [("TIMSS 2023", "TIMSS 2023 S8"), ("TIMSS 2019", "TIMSS 2019 S8")],
    "P_M": [("PISA 2022", "PISA 2022 M")],
    "P_R": [("PISA 2022", "PISA 2022 R")],
    "P_S": [("PISA 2025", "PISA 2025 S"), ("PISA 2022", "PISA 2022 S")],
    "P_F": [],
}
YILLIK_JUFT = {"T11_G4_M": "T11_G4_S", "T11_G4_S": "T11_G4_M", "T11_G8_M": "T11_G8_S", "T11_G8_S": "T11_G8_M",
               "P_M": "P_S", "P_S": "P_M", "P_R": "P_M", "P_F": "P_M"}


def pisami(tk):
    return str(tk or "").startswith("P_")


def band_of(tk):
    return "P" if pisami(tk) else "4" if "_G4_" in str(tk or "") else "8"


# ───────────────────────── tillar (REV270) ─────────────────────────
# Bo'lim uch tilda: o'zbek, rus, ingliz. Kontent har til uchun alohida (xalqaro_data/<til>/), natijalar (bilim, takrorlash,
# imtihonlar, reyting) ham til bo'yicha alohida saqlanadi — o'zbekcha o'tilgani ruschada ko'rinmaydi va aksincha.
TILLAR = ("uz", "ru", "en")


# REV319: savollar banki bazadan (Admin → Miya → «🌍 Xalqaro savollar», Excel). Bazada bo'lsa — o'sha, bo'lmasa — fayl.
BAZA_YUKLOVCHI = None   # callable(til, turi) -> data | None (create_router o'rnatadi)
BAZADA_TILLAR = set()


def til_kodi(value):
    """REV315: 5 til — uz, ru, en, de, es. Nemis/ispan faqat ularning kontenti bor bo'lsa (xalqaro_data/de, /es)
    — aks holda o'zbekcha (bo'lim ishlab turadi, xato bermaydi)."""
    v = str(value or "").strip().lower()[:2]
    if v in ("de", "es"):
        return v if (v in BAZADA_TILLAR or os.path.isfile(os.path.join(DATA_DIR, v, "savollar.json"))) else "uz"
    return {"oz": "uz"}.get(v, v) if v in ("uz", "ru", "en", "oz") else "uz"


MATN = {
    "salom": {"uz": "{m}xalqaro baholashga xush kelibsiz! Bu yerda dunyodagi eng kuchli o‘quvchilar yechadigan savollarni o‘rganamiz. Avval birinchi mavzu darsini ko‘ring, keyin haftalik nazoratni topshiring.",
              "ru": "{m}добро пожаловать в раздел международной оценки! Здесь мы изучаем задания, которые решают самые сильные ученики мира. Сначала посмотрите урок первой темы, затем сдайте еженедельную проверку.",
              "en": "{m}welcome to International Assessment! Here we study the kind of questions the strongest students in the world solve. First watch the lesson for the first topic, then take the weekly check."},
    "tanbeh_kun": {"uz": "{m}siz {kun} kundan beri mashq qilmadingiz. Bu yaxshi emas — bilim mashqsiz unutiladi. Bugun kamida 10 ta savol yeching va takrorlash navbatini tugating.",
                   "ru": "{m}вы не занимались уже {kun} дн. Это плохо — без практики знания забываются. Сегодня решите хотя бы 10 заданий и закончите очередь повторения.",
                   "en": "{m}you haven’t practised for {kun} days. That’s not good — knowledge fades without practice. Today, solve at least 10 questions and finish your review queue."},
    "tanbeh_foiz": {"uz": "{m}oxirgi imtihonda natijangiz {foiz}%. Bu xalqaro past darajadan ham quyi. Xato qilgan mavzularingiz darsini qayta ko‘ring — har kuni 15 daqiqa yetadi.",
                    "ru": "{m}на последнем экзамене ваш результат {foiz}%. Это ниже даже низкого международного уровня. Пересмотрите уроки тем, где были ошибки, — достаточно 15 минут в день.",
                    "en": "{m}your score on the last exam was {foiz}%. That is below even the Low international benchmark. Review the lessons for the topics you got wrong — 15 minutes a day is enough."},
    "eslatma_haftalik": {"uz": "{m}bu haftaning nazorati hali topshirilmagan. Hafta yakshanba kuni tugaydi — vaqtni qo‘ldan boy bermang.",
                         "ru": "{m}проверка этой недели ещё не сдана. Неделя заканчивается в воскресенье — не упустите время.",
                         "en": "{m}this week’s check hasn’t been taken yet. The week ends on Sunday — don’t miss it."},
    "eslatma_kam": {"uz": "{m}bu hafta atigi {hafta} ta savol yechdingiz. Xalqaro darajaga chiqish uchun haftasiga kamida 30 ta savol kerak.",
                    "ru": "{m}на этой неделе вы решили всего {hafta} заданий. Чтобы выйти на международный уровень, нужно не меньше 30 заданий в неделю.",
                    "en": "{m}you’ve solved only {hafta} questions this week. To reach international level you need at least 30 a week."},
    "maqtov_yuqori": {"uz": "{m}barakalla! Oxirgi imtihoningiz taxminan {ball} ball — bu xalqaro yuqori daraja. Endi mulohaza savollariga e’tibor bering, ilg‘or darajaga oz qoldi!",
                      "ru": "{m}молодец! Ваш последний экзамен — примерно {ball} баллов, это высокий международный уровень. Теперь уделите внимание заданиям на рассуждение — до продвинутого уровня совсем немного!",
                      "en": "{m}well done! Your last exam was about {ball} points — the High international benchmark. Now focus on reasoning questions — Advanced is within reach!"},
    "maqtov": {"uz": "{m}yaxshi ketyapsiz! Bu hafta {hafta} ta savol yechdingiz. Davom eting — har bir mashq sizni Singapur o‘quvchilariga yaqinlashtiradi.",
               "ru": "{m}хорошо идёте! На этой неделе вы решили {hafta} заданий. Продолжайте — каждое упражнение приближает вас к ученикам Сингапура.",
               "en": "{m}you’re doing well! You’ve solved {hafta} questions this week. Keep going — every practice brings you closer to students in Singapore."},
    "oqituvchi": {"uz": "Assalomu alaykum! «Sinfim» bo‘limida o‘quvchilaringiz faolligi, ballari va har bir xatosi (nima deb javob bergani) bor. Kurs, imtihon va darslarni o‘quvchi ko‘zi bilan ham ko‘rishingiz mumkin.",
                  "ru": "Здравствуйте! В разделе «Мой класс» — активность ваших учеников, их баллы и каждая ошибка (что именно они ответили). Курс, экзамены и уроки можно посмотреть и глазами ученика.",
                  "en": "Hello! «My class» shows your students’ activity, scores and every mistake (exactly what they answered). You can also see the course, exams and lessons as a student sees them."},
    "manba": {"uz": "Savollar TIMSS 2011 va PISA (2000–2025) ochiq savollariga parallel holda o‘zbek tilida yozilgan (asl savollar ko‘chirilmagan); xalqaro statistika — IEA TIMSS 2011 User Guide va OECD PISA hujjatlari.",
              "ru": "Задания написаны как параллельные открытым заданиям TIMSS 2011 и PISA (2000–2025) — оригинальные задания не копировались; международная статистика — IEA TIMSS 2011 User Guide и документы OECD PISA.",
              "en": "Questions are written as parallels to released TIMSS 2011 and PISA (2000–2025) items — the original items were not copied; international statistics come from the IEA TIMSS 2011 User Guide and OECD PISA documents."},
    "izoh_ball": {"uz": "Taxminiy ball savollarning xalqaro qiyinligi asosida hisoblangan (Rasch modeli) — rasmiy natija emas.",
                  "ru": "Ориентировочный балл рассчитан по международной сложности заданий (модель Раша) — это не официальный результат.",
                  "en": "The estimated score is based on the international difficulty of the questions (Rasch model) — it is not an official result."},
    "tayyor_emas": {"uz": "Bu bo‘lim tayyorlanmoqda.", "ru": "Раздел на русском языке ещё готовится. Пока занимайтесь на узбекском — результаты каждого языка хранятся отдельно.",
                    "en": "The English version of this section is still being prepared. Results for each language are kept separately."},
    "mavzu_yoq": {"uz": "Mavzu topilmadi", "ru": "Тема не найдена", "en": "Topic not found"},
    "savol_yoq": {"uz": "Savol topilmadi", "ru": "Задание не найдено", "en": "Question not found"},
    "tur_yoq": {"uz": "Noma’lum imtihon turi", "ru": "Неизвестный тип экзамена", "en": "Unknown exam type"},
    "imtihon_yoq": {"uz": "Imtihon topilmadi", "ru": "Экзамен не найден", "en": "Exam not found"},
    "faqat_oqituvchi": {"uz": "Bu bo‘lim maktab o‘qituvchisi va admin uchun", "ru": "Этот раздел — для учителя школы и администратора", "en": "This section is for school teachers and administrators"},
    "maktab_emas": {"uz": "Bu o‘quvchi sizning maktabingizda emas", "ru": "Этот ученик не из вашей школы", "en": "This student is not in your school"},
    # REV373: sinflar
    "sinf_raqam": {"uz": "Sinf 1 dan 11 gacha bo‘lishi kerak", "ru": "Класс должен быть от 1 до 11", "en": "Grade must be from 1 to 11"},
    "sinf_nom": {"uz": "Sinf nomini yozing (60 belgigacha)", "ru": "Напишите название класса (до 60 символов)", "en": "Enter a class name (up to 60 characters)"},
    "sinf_parol": {"uz": "Parol 3–32 belgi bo‘lsin", "ru": "Пароль — 3–32 символа", "en": "Password must be 3–32 characters"},
    "sinf_ochish_yoq": {"uz": "Sinfni faqat o‘qituvchi ochadi", "ru": "Класс может открыть только учитель", "en": "Only a teacher can open a class"},
    "sinf_yoq": {"uz": "Sinf topilmadi. Kodni tekshiring", "ru": "Класс не найден. Проверьте код", "en": "Class not found. Check the code"},
    "sinf_parol_xato": {"uz": "Parol noto‘g‘ri", "ru": "Неверный пароль", "en": "Wrong password"},
    "sinf_kop_urinish": {"uz": "Juda ko‘p urinish. 10 daqiqadan keyin qayta urining", "ru": "Слишком много попыток. Повторите через 10 минут", "en": "Too many attempts. Try again in 10 minutes"},
    "sinf_egasi_emas": {"uz": "Bu sinf sizniki emas", "ru": "Это не ваш класс", "en": "This is not your class"},
    "sinf_oqituvchi_azo": {"uz": "O‘qituvchi o‘z sinfiga o‘quvchi bo‘lib qo‘shila olmaydi", "ru": "Учитель не может вступить в свой класс как ученик", "en": "A teacher cannot join their own class as a student"},
    "sinf_toplam": {"uz": "Sinf qaysi dastur va fan bo‘yicha ekanini tanlang", "ru": "Выберите программу и предмет класса", "en": "Choose the class programme and subject"},
    "topshiriq_azo_emas": {"uz": "Bu topshiriq «{s}» sinfi uchun, sinf parolli. O‘qituvchingizdan sinf kodi va parolini so‘rab, «Sinfim» bo‘limida qo‘shiling",
                           "ru": "Задание для класса «{s}» (с паролем). Спросите у учителя код и пароль и вступите в разделе «Мой класс»",
                           "en": "This task is for the class «{s}» (password-protected). Ask your teacher for the code and password and join in «My class»"},
    "sinf_toliq": {"uz": "Sinfda joy qolmagan (60 o‘quvchi)", "ru": "В классе нет мест (60 учеников)", "en": "The class is full (60 students)"},
    "rasm_yoq": {"uz": "Rasm yo‘q", "ru": "Рисунка нет", "en": "No picture"},
    "kurs": {"uz": "Xalqaro baholash (TIMSS/PISA) tayyorlov kursi", "ru": "Курс подготовки к международной оценке (TIMSS/PISA)", "en": "International assessment (TIMSS/PISA) preparation course"},
    "sinf": {"uz": "{n}-sinf", "ru": "{n} класс", "en": "Grade {n}"},
    "past_quyi": {"uz": "Past darajadan quyi", "ru": "Ниже низкого уровня", "en": "Below Low"},
    "pisa_quyi": {"uz": "1-darajadan quyi", "ru": "Ниже уровня 1", "en": "Below Level 1"},
}
IMTIHON_NOMI = {"haftalik": {"ru": "Еженедельная проверка", "en": "Weekly check"},
                "oylik": {"ru": "Ежемесячный экзамен", "en": "Monthly exam"},
                "choraklik": {"ru": "Четвертной экзамен (часть 1)", "en": "Term exam (part 1)"},
                "yillik": {"ru": "Годовой экзамен (полная тетрадь, 2 части)", "en": "Annual exam (full booklet, 2 parts)"}}
DARAJA_NOMI = {"ilgor": {"ru": "Продвинутый", "en": "Advanced"}, "yuqori": {"ru": "Высокий", "en": "High"},
               "orta": {"ru": "Средний", "en": "Intermediate"}, "past": {"ru": "Низкий", "en": "Low"}}
VARIANT_NOMI = {"sodda": {"uz": "Soddaroq", "ru": "Проще", "en": "Simpler"}, "hikoya": {"uz": "Hikoya orqali", "ru": "Через историю", "en": "Through a story"},
                "boshqa_usul": {"uz": "Boshqa usulda", "ru": "Другим способом", "en": "Another way"}, "rasm": {"uz": "Rasm bilan", "ru": "С рисунком", "en": "With a picture"},
                "": {"uz": "Boshqacha", "ru": "Иначе", "en": "Differently"}}


def matn(key, til="uz", **kw):
    d = MATN[key]
    return (d.get(til) or d["uz"]).format(**kw)


def imtihon_nomi(tur, til="uz"):
    return (IMTIHON_NOMI.get(tur, {}).get(til) if til != "uz" else None) or IMTIHON_TURLARI.get(tur, {}).get("nom", tur)


# ───────────────────────── kontent ─────────────────────────
class Kontent:
    """JSON kontent bir marta o'qiladi (xotirada ~ bir necha MB)."""

    def __init__(self, data_dir=DATA_DIR, til="uz"):
        self.base_dir = data_dir
        self.til = til_kodi(til)
        self.data_dir = data_dir if self.til == "uz" else os.path.join(data_dir, self.til)   # REV270: xalqaro_data/ru, /en
        self._lock = threading.Lock()
        self._ok = False

    def _load(self, name, default):
        b = _baza(self.til, name[:-5])
        if b is not None:
            return b
        path = os.path.join(self.data_dir, name)
        if not os.path.exists(path) and self.til in ("de", "es"):   # REV319: tuzilma hali tarjima qilinmagan — inglizchasi
            path = os.path.join(self.base_dir, "en", name)
        if not os.path.exists(path):
            return default
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def yangila(self):
        """REV380: keyingi so'rovda kontent bazadan qayta o'qiladi (yangi Miya o'rnatilganda)."""
        self._ok = False

    def ensure(self):
        if self._ok:
            return self
        with self._lock:
            if self._ok:
                return self
            self.ramka = self._load("ramka.json", {"toplamlar": {}, "mavzular": {}, "fikrlash": {}})
            self.natijalar = natijalar_tilda(self.base_dir, self.til)
            self.manba = "baza" if _baza(self.til, "savollar") is not None else "fayl"
            self.savollar = self._load("savollar.json", [])
            self.darslar = self._load("darslar.json", [])
            self.birliklar = {b["birlik"]: b for b in self._load("birliklar.json", [])}   # REV262: PISA stimullari
            self.i18n = _json_fayl(os.path.join(self.base_dir, "davlatlar.json"), {})
            self.by_id = {s["id"]: s for s in self.savollar}
            self.dars_by_kod = {d["kod"]: d for d in self.darslar}
            self.mavzu_by_kalit = {}
            for tk, tops in self.ramka.get("mavzular", {}).items():
                for t in tops:
                    self.mavzu_by_kalit[t["kalit"]] = dict(t, toplam=tk)
            self.by_mavzu = {}
            for s in self.savollar:
                self.by_mavzu.setdefault(s["mavzu"], []).append(s)
            self._ok = True
        return self


def _baza(til, turi):
    """REV320: bazadagi kontent (bo'lmasa None)."""
    if BAZA_YUKLOVCHI is None:
        return None
    try:
        return BAZA_YUKLOVCHI(til, turi)
    except Exception:   # noqa: BLE001 — baza ishlamasa ham bo'lim yiqilmaydi
        return None


def _json_fayl(path, default):
    nom = os.path.basename(path)
    if nom in ("natijalar.json", "davlatlar.json"):   # REV320: tilga bog'liq bo'lmagan — o'zbekcha Excel'dan
        b = _baza("uz", nom[:-5])
        if b is not None:
            return b
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_NATIJA_KESH = {}


def natijalar_tilda(base_dir, til):
    """REV270: davlatlar natijalari — raqamlar bitta (natijalar.json), davlat nomlari, manbalar va izohlar shu tilda."""
    key = (base_dir, til)
    if key not in _NATIJA_KESH:
        _NATIJA_KESH[key] = _natijalar_tilda(base_dir, til)
    return _NATIJA_KESH[key]


def _natijalar_tilda(base_dir, til):
    n = _json_fayl(os.path.join(base_dir, "natijalar.json"), {"jadvallar": {}, "nomlar": {}})
    if til == "uz":
        return n
    i18n = _json_fayl(os.path.join(base_dir, "davlatlar.json"), {})
    nom = lambda x: (i18n.get("nomlar", {}).get(x) or {}).get(til, x)
    out = dict(n)
    out["jadvallar"] = {k: [[nom(r[0]), *r[1:]] for r in rows] for k, rows in n.get("jadvallar", {}).items()}
    out["nomlar"] = {en: (en if til == "en" else nom(uz)) for en, uz in n.get("nomlar", {}).items()}
    out["manbalar"] = {**n.get("manbalar", {}), **(i18n.get("manbalar", {}).get(til) or {})}
    uzb = dict(n.get("ozbekiston", {}))
    if (i18n.get("izoh") or {}).get(til):
        uzb["izoh"] = i18n["izoh"][til]
    out["ozbekiston"] = uzb
    d = dict(n.get("darajalar", {}))
    if d.get("TIMSS"):
        d["TIMSS"] = [[c, DARAJA_NOMI.get(k, {}).get(til, nm)] for (c, nm), (_c, k, _n) in zip(d["TIMSS"], DARAJALAR)]
    out["darajalar"] = d
    out["uz_nomi"] = nom("O‘zbekiston")
    return out


def davlat_nomi(nom, til="uz"):
    """O'zbekcha davlat nomi → shu tildagi nomi."""
    if til == "uz":
        return nom
    i18n = KONTENT.ensure().i18n
    return (i18n.get("nomlar", {}).get(nom) or {}).get(til, nom)


KONTENT = Kontent()
KONTENTLAR = {"uz": KONTENT}


def kontent_of(til="uz", asos=None):
    """Shu tilning kontenti. asos — testlarda boshqa papka bilan yaratilgan o'zbekcha kontent."""
    til = til_kodi(til)
    if asos is not None and til == "uz":
        return asos.ensure()
    if asos is not None:
        key = (asos.base_dir, til)
        if key not in KONTENTLAR:
            KONTENTLAR[key] = Kontent(asos.base_dir, til)
        return KONTENTLAR[key].ensure()
    if til not in KONTENTLAR:
        KONTENTLAR[til] = Kontent(DATA_DIR, til)
    return KONTENTLAR[til].ensure()


def _son(v):
    """Son yoki sonli matn → float/int; boshqasi → None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    try:
        x = float(str(v).replace(",", ".").strip())
        return int(x) if x.is_integer() else x
    except (TypeError, ValueError):
        return None


def _t(v):
    return str(v or "").strip()


def sinf_raqami(value, fallback=0):
    m = re.search(r"(\d{1,2})", str(value or ""))
    n = int(m.group(1)) if m else 0
    if "yosh" in str(value or "").lower() or "kurs" in str(value or "").lower():
        return 0
    return n if 1 <= n <= 11 else int(fallback or 0)


def tavsiya_toplamlar(sinf):
    """O'quvchi sinfiga mos to'plamlar: 1–5 sinf → TIMSS 4-sinf, 6–8 → TIMSS 8-sinf, 9–11 → PISA (15 yosh)."""
    if not sinf:
        return ["T11_G4_M", "T11_G4_S", "T11_G8_M", "T11_G8_S"]
    if sinf <= 5:
        return ["T11_G4_M", "T11_G4_S"]
    if sinf <= 8:
        return ["T11_G8_M", "T11_G8_S"]
    return ["P_M", "P_R", "P_S", "P_F"]


def daraja_of(ball, toplam=None, til="uz"):
    """TIMSS: xalqaro mezonlar (400/475/550/625). PISA: shu soha darajalari (1b … 6). REV270: nomi shu tilda."""
    if pisami(toplam):
        jad = (KONTENT.ensure().ramka.get("darajalar") or {}).get(toplam) or []
        nomlar = jad
        if til != "uz":
            tj = (kontent_of(til).ramka.get("darajalar") or {}).get(toplam) or []
            nomlar = tj if len(tj) == len(jad) else jad
        for (chegara, nom), (_c, tnom) in zip(jad, nomlar):
            if (ball or 0) >= chegara:
                n = re.match(r"(\d[ab]?)", nom)
                return {"kalit": "p" + (n.group(1) if n else "x"), "nom": tnom, "chegara": chegara, "pisa": True,
                        "tayanch": chegara >= next((c for c, nn in jad if "tayanch" in nn), 0)}
        return {"kalit": "p0", "nom": matn("pisa_quyi", til), "chegara": 0, "pisa": True, "tayanch": False}
    for chegara, kalit, nom in DARAJALAR:
        if (ball or 0) >= chegara:
            return {"kalit": kalit, "nom": DARAJA_NOMI[kalit].get(til, nom) if til != "uz" else nom, "chegara": chegara}
    return {"kalit": "boshlangich", "nom": matn("past_quyi", til), "chegara": 0}


# ───────────────────────── javobni tekshirish ─────────────────────────
def _norm(value):
    s = str(value or "").lower().strip()
    s = s.replace("’", "'").replace("‘", "'").replace("ʻ", "'").replace("`", "'").replace("ʼ", "'")
    s = re.sub(r"\$|\\,|\\;|\s+", "", s)
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", s)
    s = s.replace("{,}", ",").replace(",", ".")
    s = re.sub(r"(ta|dona|so'm|sum|sm|cm|m|kg|g|l|°c|°|%|daraja|gradus|шт|штук|сум|см|м|кг|г|л|градус(ов|а)?|pcs|soum|sums|degrees?)$", "", s)
    s = s.rstrip(".")
    return s


def _as_number(s):
    try:
        if re.fullmatch(r"-?\d+/\d+", s):
            a, b = s.split("/")
            return int(a) / int(b) if int(b) else None
        if re.fullmatch(r"-?\d+(\.\d+)?", s):
            return float(s)
    except (ValueError, ZeroDivisionError):
        return None
    return None


def tekshir_ochiq(berilgan, kutilgan):
    """«ochiq» javob: matn bo'yicha (| bilan bir nechta to'g'ri yozilish) yoki son qiymati bo'yicha (3/4 = 0,75)."""
    a = _norm(berilgan)
    if not a:
        return False
    variants = [_norm(x) for x in str(kutilgan or "").split("|") if _norm(x)]
    if a in variants:
        return True
    av = _as_number(a)
    if av is None:
        return False
    for v in variants:
        vv = _as_number(v)
        if vv is not None and abs(vv - av) < 1e-9:
            return True
    return False


def harf_indeksi(value):
    """«B», «b)», «2» yoki variant matni → indeks (0–3). Topilmasa None."""
    s = _t(value).upper()
    if not s:
        return None
    if isinstance(value, int) and 0 <= value <= 3:
        return value
    m = re.match(r"^\(?([ABCD])\)?[\).]?$", s)
    if m:
        return OPTION_LETTERS.index(m.group(1))
    if re.fullmatch(r"[0-3]", s):
        return int(s)
    return None


def tekshir(variant, javob):
    if variant.get("turi") == "tanlov":
        i = harf_indeksi(javob) if not isinstance(javob, int) else javob
        return i is not None and i == variant.get("togri")
    return tekshir_ochiq(javob, variant.get("javob"))


# ───────────────────────── baholash (Rasch, EAP) ─────────────────────────
def qiyinlik(foiz):
    """Asl savolning xalqaro to'g'ri yechilish foizidan Rasch qiyinligi (logit). 50% → 0."""
    p = min(97.0, max(3.0, float(foiz if foiz is not None else 50))) / 100.0
    return -math.log(p / (1 - p))


def savol_qiyinligi(s):
    """REV262: PISA savolida qiyinlik PISA balli bilan berilgan (62% ehtimollik nuqtasi) — shu shkalaga o'tkaziladi.
    TIMSS savolida — xalqaro to'g'ri yechilish foizidan."""
    d = s.get("qiyinlik_ball")
    if isinstance(d, (int, float)):
        return (d - 500) * THETA_SD / 100 - math.log(0.62 / 0.38)
    return qiyinlik(s.get("xalqaro_ortacha"))


# ─────────── REV399: mavzu testlari — to'plamlar (har birida ~8 savol), osondan imtihon darajasigacha ───────────
TOPLAM_SONI = 8


def toplam_darajasi(i, jami):
    """1-to'plam — oson, oxirgisi — imtihon darajasi, o'rtadagilar — o'rta (4+ to'plamda: qiyin ham)."""
    if jami <= 1:
        return "imtihon"
    if i == 1:
        return "oson"
    if i == jami:
        return "imtihon"
    if jami >= 4 and i == jami - 1:
        return "qiyin"
    return "orta"


def mavzu_toplamlari(savollar):
    """Mavzu savollari qiyinlik bo'yicha tartiblanadi va ~8 tadan to'plamlarga bo'linadi; rasmli savoli yo'q
    to'plamga qo'shni to'plamdan bittasi o'tkaziladi (bola chizmali savolni ham ko'radi, qiyinlik tartibi saqlanadi)."""
    qs = sorted(savollar, key=lambda x: (savol_qiyinligi(x), x["id"]))
    if not qs:
        return []
    n = max(1, round(len(qs) / TOPLAM_SONI))
    olcham = [len(qs) // n + (1 if j < len(qs) % n else 0) for j in range(n)]
    out, b = [], 0
    for o in olcham:
        out.append(qs[b:b + o]); b += o
    rasmli = lambda x: any(v.get("rasm") for v in x["variantlar"])
    for j, t in enumerate(out):
        if any(rasmli(x) for x in t):
            continue
        # faqat qo'shni to'plamdan — qiyinlik tartibi buzilmasin
        donor = max((d for d in (j - 1, j + 1) if 0 <= d < n and sum(map(rasmli, out[d])) > 1), key=lambda d: sum(map(rasmli, out[d])), default=None)
        if donor is None:
            continue
        r = next(x for x in out[donor] if rasmli(x))
        o = min(t, key=lambda x: abs(savol_qiyinligi(x) - savol_qiyinligi(r)))
        out[donor][out[donor].index(r)], t[t.index(o)] = o, r
    return [sorted(t, key=lambda x: (savol_qiyinligi(x), x["id"])) for t in out]


def eap_theta(natijalar):
    """natijalar: [(qiyinlik, togri_mi)] → qobiliyat (EAP, N(0,1) apriori) va xatolik."""
    nuqtalar = [-4 + i * 0.1 for i in range(81)]
    w = []
    for th in nuqtalar:
        lp = -th * th / 2
        for b, ok in natijalar:
            p = 1 / (1 + math.exp(-(th - b)))
            lp += math.log(p if ok else 1 - p)
        w.append(lp)
    m = max(w)
    w = [math.exp(x - m) for x in w]
    s = sum(w)
    mean = sum(t * x for t, x in zip(nuqtalar, w)) / s
    var = sum((t - mean) ** 2 * x for t, x in zip(nuqtalar, w)) / s
    return mean, math.sqrt(var)


def timss_ball(natijalar):
    """Taxminiy TIMSS bali: xalqaro o'rtacha o'quvchi ≈ 500. Rasmiy natija emas."""
    if not natijalar:
        return None, None
    th, se = eap_theta(natijalar)
    ball = int(round(500 + 100 * th / THETA_SD))
    return max(250, min(750, ball)), int(round(100 * se / THETA_SD))


def solishtir(k, toplam, ball):
    """REV262: ball → shu to'plamga mos haqiqiy natijalar jadvallari (TIMSS 2023/2019 yoki PISA 2025/2022) bo'yicha o'rin."""
    out = []
    for nom, kalit in SOLISHTIRISH.get(toplam, []):
        r = davlatlar_bilan(ball, k.natijalar.get("jadvallar", {}).get(kalit), k.natijalar.get("uz_nomi") or "O‘zbekiston")
        if r:
            out.append({"nom": nom, **r})
    return out


def davlatlar_bilan(ball, jadval, uz_nomi="O‘zbekiston"):
    """Ball → shu jadvaldagi o'rin va yaqin davlatlar."""
    rows = sorted(jadval or [], key=lambda r: -r[1])
    if ball is None or not rows:
        return None
    yuqori = [r for r in rows if r[1] > ball]
    past = [r for r in rows if r[1] <= ball]
    return {"orin": len(yuqori) + 1, "jami": len(rows) + 1,
            "yuqorida": yuqori[-2:], "pastda": past[:2],
            "ozbekiston": next((r[1] for r in rows if r[0] == uz_nomi), None), "eng_yuqori": rows[0], "jadval": rows}


# ───────────────────────── davrlar ─────────────────────────
def bugun():
    return datetime.now(TZ).date()


def davr_kaliti(tur, kun=None):
    """Imtihon davri: hafta (ISO), oy, chorak (o'zbek maktabi: I sen–okt, II noy–dek, III yan–mar, IV apr–avg), o'quv yili."""
    kun = kun or bugun()
    if tur == "haftalik":
        y, w, _ = kun.isocalendar()
        return f"{y}-H{w:02d}"
    if tur == "oylik":
        return f"{kun.year}-{kun.month:02d}"
    oquv_yili = kun.year if kun.month >= 9 else kun.year - 1
    if tur == "choraklik":
        m = kun.month
        q = 1 if m in (9, 10) else 2 if m in (11, 12) else 3 if m in (1, 2, 3) else 4
        return f"{oquv_yili}-{oquv_yili + 1}-C{q}"
    return f"{oquv_yili}-{oquv_yili + 1}"


def davr_oxiri(tur, kun=None):
    kun = kun or bugun()
    if tur == "haftalik":
        return kun + timedelta(days=6 - kun.weekday())
    if tur == "oylik":
        nxt = date(kun.year + (kun.month == 12), kun.month % 12 + 1, 1)
        return nxt - timedelta(days=1)
    if tur == "choraklik":
        m, y = kun.month, kun.year
        end = {9: (10, 31), 10: (10, 31), 11: (12, 31), 12: (12, 31), 1: (3, 31), 2: (3, 31), 3: (3, 31)}.get(m, (8, 31))
        return date(y, end[0], end[1])
    return date(kun.year if kun.month < 9 else kun.year + 1, 8, 31)


# ───────────────────────── savol tanlash ─────────────────────────
def _variant_public(s, vi, javob_bilan=False, k=None):
    v = s["variantlar"][vi]
    out = {"savol_id": s["id"], "v": vi, "turi": v["turi"], "savol": v["savol"], "rasm": bool(v.get("rasm")),
           "javoblar": v.get("javoblar") or [], "javob_turi": v.get("javob_turi") or "",
           "mavzu": s["mavzu"], "soha": s["soha"], "fikrlash": s["fikrlash"], "ball": 1, "toplam": s["toplam"],
           "xalqaro_foiz": s.get("xalqaro_ortacha") if s.get("xalqaro_ortacha") is not None else s.get("oecd_foiz")}
    if v.get("rasm"):
        out["rasm_svg"] = v["rasm"]
    if s.get("birlik"):   # REV262: PISA — umumiy stimul (matn, jadval, grafik) savol bilan birga
        b = (k or KONTENT.ensure()).birliklar.get(s["birlik"]) or {}
        out.update(birlik=s["birlik"], stimul={"nom": b.get("nom", ""), "matn": b.get("stimul", ""), "rasm_svg": b.get("stimul_rasm") or None},
                   jarayon=s.get("jarayon"), kontekst=s.get("kontekst"), qiyinlik_ball=s.get("qiyinlik_ball"),
                   oecd_foiz=s.get("oecd_foiz"), qiyinlik_taxminiy=bool(s.get("taxminiy")))
    if javob_bilan:
        out.update(togri=v.get("togri"), javob=v.get("javob") or "", yechim=v.get("yechim") or [],
                   xatolar=v.get("xatolar") or {}, maslahat=v.get("maslahat") or "",
                   kunikma=s.get("kunikma") or "", usul=s.get("usul") or "")
    return out


def reja_boyicha_tanla(savollar, soni, reja, rng, chetla=()):
    """TIMSS ramkasi nisbatida savol tanlaydi: avval soha ulushlari, ichida fikrlash darajalari aralash.
    chetla — yaqinda berilgan savollar (iloji bo'lsa takrorlanmaydi)."""
    chetla = set(chetla)
    pool = [s for s in savollar if s["id"] not in chetla]
    if len(pool) < soni:
        pool = list(savollar)
    sohalar = reja.get("soha") or {}
    kvota = {k: int(round(v * soni)) for k, v in sohalar.items()}
    while sum(kvota.values()) > soni:
        k = max(kvota, key=kvota.get); kvota[k] -= 1
    while sum(kvota.values()) < soni and kvota:
        k = max(sohalar, key=sohalar.get); kvota[k] += 1
    tanlangan = []
    fik_reja = reja.get("fikrlash") or {}
    for soha, n in kvota.items():
        guruh = [s for s in pool if s["soha"] == soha]
        rng.shuffle(guruh)
        # fikrlash darajalari bo'yicha navbatma-navbat
        fik = sorted(fik_reja, key=lambda k: -fik_reja[k]) or ["bilish", "qollash", "mulohaza"]
        target = {f: max(0, int(round(fik_reja.get(f, 0.33) * n))) for f in fik}
        olindi = []
        for f in fik:
            olindi += [s for s in guruh if s["fikrlash"] == f and s not in olindi][:target[f]]
        olindi += [s for s in guruh if s not in olindi][: max(0, n - len(olindi))]
        tanlangan += olindi[:n]
    if len(tanlangan) < soni:
        qolgan = [s for s in pool if s not in tanlangan]
        rng.shuffle(qolgan)
        tanlangan += qolgan[: soni - len(tanlangan)]
    rng.shuffle(tanlangan)
    tanlangan = tanlangan[:soni]
    # REV262: PISA — bitta birlik (umumiy stimul) savollari ketma-ket turadi, haqiqiy PISA daftaridagidek
    if any(s.get("birlik") for s in tanlangan):
        tartib = {}
        for s in tanlangan:
            tartib.setdefault(s.get("birlik") or s["id"], len(tartib))
        tanlangan.sort(key=lambda s: (tartib[s.get("birlik") or s["id"]], s["id"]))
    return tanlangan


# ───────────────────────── dars xonasi uchun ─────────────────────────
def dars_payload(topic_code, kontent=None, til="uz"):
    """«XB-M8-KAS» → dars xonasi formatidagi dars (topic, steps, variants, savollar). Topilmasa None.
    REV270: dars o'quvchi tanlagan tilda; shu tilda tarjimasi yo'q bo'lsa — None (boshqa til bilan aralashtirilmaydi)."""
    til = til_kodi(til)
    k = kontent_of(til, kontent)
    d = k.dars_by_kod.get(_t(topic_code).upper())
    if not d:
        return None
    mv = k.mavzu_by_kalit.get(d["mavzu"], {})
    tm = k.ramka.get("toplamlar", {}).get(mv.get("toplam"), {})
    fan = _t(d.get("fan")) or tm.get("ustoz_fan") or tm.get("fan_nomi") or "Matematika"
    steps, variants = [], {}
    for i, q in enumerate(d.get("qadamlar") or []):
        sid = f"{d['kod']}-{i + 1:02d}"
        steps.append({"id": sid, "turi": q.get("turi") or "tushuntirish", "sahna": _t(q.get("sahna")) or sid,
                      "sarlavha": _t(q.get("sarlavha")), "doska": _t(q.get("doska")), "ovoz": _t(q.get("ovoz")) or _t(q.get("doska")),
                      "rasm": None, "savol": _t(q.get("savol")) if q.get("turi") == "birga" else "",
                      "javob": _t(q.get("javob")) if q.get("turi") == "birga" else "", "javob_izohi": _t(q.get("javob_izohi")), "sahifa": ""})
    first_of_scene = {}
    for s in steps:
        first_of_scene.setdefault(s["sahna"], s["id"])
    names = {kk: vv.get(til, vv["uz"]) for kk, vv in VARIANT_NOMI.items()}
    for sahna, vs in (d.get("tushunmadim") or {}).items():
        sid = first_of_scene.get(sahna)
        if not sid:
            continue
        variants[sid] = [{"id": f"{sid}-v{j + 1}", "turi": v.get("turi") or "sodda", "nom": names.get(v.get("turi"), names[""]),
                          "doska": _t(v.get("doska")), "ovoz": _t(v.get("ovoz")), "rasm": None, "takrorlash_topic_code": ""}
                         for j, v in enumerate(vs)]
    savollar = []
    rng = random.Random(hashlib.md5(d["kod"].encode()).hexdigest())
    pool = [s for s in k.by_mavzu.get(d["mavzu"], []) if s["variantlar"][0]["turi"] == "tanlov" and not s["variantlar"][0].get("rasm")]
    rng.shuffle(pool)
    for s in pool[:5]:
        v = s["variantlar"][0]
        savollar.append({"id": f"xb-{s['id']}", "savol": v["savol"], "variantlar": v["javoblar"], "togri": v["togri"],
                         "izoh": " ".join(x["doska"] for x in (v.get("yechim") or [])[-1:]), "kod": ""})
    return {
        "topic": {"topic_code": d["kod"], "mavzu": d.get("sarlavha") or mv.get("nom"), "fan": fan,
                  "sinf": matn("sinf", til, n=tm["sinf"]) if tm.get("sinf") else "", "maqsad": _t(d.get("maqsad")), "daraja": None,
                  "til": til},
        "auto": False, "steps": steps, "variants": variants, "savollar": savollar,
        "manba": {"kitob": matn("kurs", til)}, "xalqaro": True, "til": til,
    }


# ───────────────────────── modellar ─────────────────────────
class JavobBody(BaseModel):
    token: str = ""
    savol_id: str = Field(max_length=20)
    v: int = Field(default=0, ge=0, le=5)
    javob: str = Field(default="", max_length=200)
    usul: str = Field(default="yozib", max_length=12)     # yozib | aytib
    takror: bool = False
    til: str = Field(default="", max_length=8)            # REV270: uz | ru | en


class BoshlaBody(BaseModel):
    token: str = ""
    tur: str = Field(max_length=12)
    toplam: str = Field(default="", max_length=12)
    mashq: bool = False
    til: str = Field(default="", max_length=8)


class TopshirBody(BaseModel):
    token: str = ""
    sessiya: int
    javoblar: dict = Field(default_factory=dict)
    chiqishlar: int = Field(default=0, ge=0, le=1000)      # imtihon oynasidan chiqib ketishlar soni (halollik nazorati)
    qism: int = Field(default=0, ge=0, le=2)


# ─────────── REV373: o'qituvchining sinflari ───────────
import hashlib as _hl, secrets as _sec
SINF_ROLLAR = {"oqituvchi", "teacher", "fan_oqituvchisi", "sinf_rahbar", "direktor", "director", "zam_direktor"}
_KOD_HARF = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # 0/O, 1/I yo'q — bola adashmaydi


def sinf_kodi_yasa(n=6):
    return "".join(_sec.choice(_KOD_HARF) for _ in range(n))


def kod_norm(kod):
    return re.sub(r"[^A-Za-z0-9]", "", str(kod or "")).upper()[:12]


def parol_hash(parol, kod):
    p = str(parol or "").strip()
    return "" if not p else _hl.sha256(f"xb-sinf:{kod}:{p}".encode("utf8")).hexdigest()


def parol_togri(saqlangan, parol, kod):
    return (not saqlangan) or bool(str(parol or "").strip()) and _sec.compare_digest(saqlangan, parol_hash(parol, kod))


AUDITORIYALAR = ("bogcha", "maktab", "talaba", "oqituvchi")   # REV401: sinf kimlar uchun


def auditoriya_norm(a):
    return a if a in AUDITORIYALAR else "maktab"


XB_TOPLAMLAR = ("T11_G4_M", "T11_G4_S", "T11_G8_M", "T11_G8_S", "P_M", "P_R", "P_S", "P_F")


def sinf_toplami(toplam, sinf):
    """REV374: sinf fani — berilgani (ro'yxatda bo'lsa), aks holda sinf raqamiga mos birinchisi."""
    t = str(toplam or "").strip()
    return t if t in XB_TOPLAMLAR else tavsiya_toplamlar(int(sinf or 0))[0]


KURSLAR = ("1 kurs", "2 kurs", "3 kurs", "4 kurs", "1 kurs magistr", "2 kurs magistr")   # REV408


def sinf_malumot_tekshir(nom, sinf, parol, auditoriya="maktab"):
    nom = re.sub(r"\s+", " ", str(nom or "")).strip()
    try:
        sinf = int(sinf)
    except (TypeError, ValueError):
        sinf = 0
    # REV408: talaba/o'qituvchi/bog'cha guruhida maktab sinfi shart emas (0 — sinfsiz)
    if auditoriya_norm(auditoriya) == "maktab" and not 1 <= sinf <= 11:
        return None, "sinf_raqam"
    if not 0 <= sinf <= 11:
        return None, "sinf_raqam"
    if not 1 <= len(nom) <= 60:
        return None, "sinf_nom"
    if parol and not 3 <= len(str(parol).strip()) <= 32:
        return None, "sinf_parol"
    return {"nom": nom, "sinf": sinf}, None


def migrate(cur):
    # REV319: savollar banki — Excel'dan yuklangan (til bo'yicha), nashr qilingani saytda ishlatiladi
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_kontent (til TEXT NOT NULL, turi TEXT NOT NULL, data JSON NOT NULL,
        soni INT NOT NULL DEFAULT 0, yukladi BIGINT, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (til, turi))""")
    # REV320: JSON (JSONB emas) — kalitlar tartibi saqlanadi (to'plamlar, davlatlar ro'yxati tartibi saytda muhim)
    cur.execute("""DO $$ BEGIN
        IF (SELECT data_type FROM information_schema.columns WHERE table_name='xb_kontent' AND column_name='data') = 'jsonb' THEN
            ALTER TABLE xb_kontent ALTER COLUMN data TYPE JSON USING data::json; END IF; END $$""")
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_bilim (
        user_id BIGINT NOT NULL, savol_id TEXT NOT NULL, toplam TEXT NOT NULL DEFAULT '', mavzu TEXT NOT NULL DEFAULT '',
        urinish INT NOT NULL DEFAULT 0, togri INT NOT NULL DEFAULT 0, oxirgi_togri BOOLEAN NOT NULL DEFAULT FALSE,
        aytib INT NOT NULL DEFAULT 0, yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, savol_id))""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_bilim_user ON xb_bilim(user_id, toplam)")
    # REV373: o'qituvchi sinf ochadi — o'quvchilar taklif kodi/havolasi yoki sinfni tanlab parol bilan qo'shiladi
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_sinf (id BIGSERIAL PRIMARY KEY, egasi BIGINT NOT NULL, nom TEXT NOT NULL, sinf INT NOT NULL,
        kod TEXT NOT NULL UNIQUE, parol_hash TEXT NOT NULL DEFAULT '', yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW(), faol BOOLEAN NOT NULL DEFAULT TRUE)""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_sinf_egasi ON xb_sinf(egasi)")
    cur.execute("ALTER TABLE xb_sinf ADD COLUMN IF NOT EXISTS toplam TEXT NOT NULL DEFAULT ''")   # REV374: sinf qaysi dastur/fan bo'yicha
    cur.execute("ALTER TABLE xb_sinf ADD COLUMN IF NOT EXISTS auditoriya TEXT NOT NULL DEFAULT 'maktab'")   # REV401: kimlar uchun
    cur.execute("ALTER TABLE xb_sinf ADD COLUMN IF NOT EXISTS kurs TEXT NOT NULL DEFAULT ''")   # REV408: talaba guruhi kursi
    # REV401: o'qituvchi sinfga topshiriq (imtihon) beradi — hamma bir xil savollarni yechadi, havola bilan ham ochiladi
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_topshiriq (id BIGSERIAL PRIMARY KEY, sinf_id BIGINT NOT NULL REFERENCES xb_sinf(id) ON DELETE CASCADE,
        nom TEXT NOT NULL, mavzu TEXT NOT NULL DEFAULT '', savol_idlar JSON NOT NULL, muddat DATE, kod TEXT NOT NULL UNIQUE,
        yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW(), faol BOOLEAN NOT NULL DEFAULT TRUE)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_topshiriq_natija (topshiriq_id BIGINT NOT NULL REFERENCES xb_topshiriq(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL, togri INT NOT NULL, jami INT NOT NULL, urinish INT NOT NULL DEFAULT 1, eng_yaxshi INT NOT NULL DEFAULT 0,
        vaqt TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (topshiriq_id, user_id))""")
    # REV404: topshiriqni jonli kuzatish — o'quvchi qaysi savolda, nechtasini belgiladi, ilova ochiqmi
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_topshiriq_jonli (topshiriq_id BIGINT NOT NULL REFERENCES xb_topshiriq(id) ON DELETE CASCADE,
        user_id BIGINT NOT NULL, joriy INT NOT NULL DEFAULT 0, javob INT NOT NULL DEFAULT 0, togri INT NOT NULL DEFAULT 0, holat TEXT NOT NULL DEFAULT 'faol',
        boshladi TIMESTAMPTZ NOT NULL DEFAULT NOW(), yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (topshiriq_id, user_id))""")
    # REV376: o'quvchi qaysi mavzu darslarini ochgan/tugatgan — o'qituvchi ko'radi
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_dars (user_id BIGINT NOT NULL, til TEXT NOT NULL DEFAULT 'uz', mavzu TEXT NOT NULL,
        ochildi INT NOT NULL DEFAULT 0, tugadi BOOLEAN NOT NULL DEFAULT FALSE, birinchi TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        oxirgi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, til, mavzu))""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_sinf_raqam ON xb_sinf(sinf) WHERE faol")
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_sinf_azo (sinf_id BIGINT NOT NULL REFERENCES xb_sinf(id) ON DELETE CASCADE, user_id BIGINT NOT NULL,
        qoshildi TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (sinf_id, user_id))""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_sinf_azo_user ON xb_sinf_azo(user_id)")
    # REV261: o'qituvchi o'quvchining aynan qanday xato qilganini ko'radi
    cur.execute("ALTER TABLE xb_bilim ADD COLUMN IF NOT EXISTS oxirgi_v INT NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE xb_bilim ADD COLUMN IF NOT EXISTS oxirgi_javob TEXT NOT NULL DEFAULT ''")
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_takror (
        user_id BIGINT NOT NULL, savol_id TEXT NOT NULL, v INT NOT NULL DEFAULT 0, quti INT NOT NULL DEFAULT 1,
        keyingi DATE NOT NULL, PRIMARY KEY (user_id, savol_id))""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_takror_due ON xb_takror(user_id, keyingi)")
    cur.execute("""CREATE TABLE IF NOT EXISTS xb_imtihon (
        id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, tur TEXT NOT NULL, toplam TEXT NOT NULL, davr TEXT NOT NULL,
        rasmiy BOOLEAN NOT NULL DEFAULT FALSE, sinf INT NOT NULL DEFAULT 0, maktab_id BIGINT, sinf_nomi TEXT NOT NULL DEFAULT '',
        savollar JSONB NOT NULL, javoblar JSONB NOT NULL DEFAULT '{}'::jsonb, qismlar INT NOT NULL DEFAULT 1, qism INT NOT NULL DEFAULT 1,
        boshlangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), tugash TIMESTAMPTZ NOT NULL, topshirilgan TIMESTAMPTZ,
        foiz INT, ball INT, xato_ball INT, natija JSONB NOT NULL DEFAULT '{}'::jsonb, chiqishlar INT NOT NULL DEFAULT 0)""")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_imtihon_user ON xb_imtihon(user_id, tur, davr)")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_imtihon_reyting ON xb_imtihon(toplam, tur, davr, rasmiy, ball DESC)")
    # REV270: til — har til bo'yicha alohida bilim, takrorlash va imtihonlar (o'zbekcha o'tilgani ruschada ko'rinmaydi)
    for t in ("xb_bilim", "xb_takror", "xb_imtihon"):
        cur.execute(f"ALTER TABLE {t} ADD COLUMN IF NOT EXISTS til TEXT NOT NULL DEFAULT 'uz'")
    for t in ("xb_bilim", "xb_takror"):
        cur.execute("""SELECT COUNT(*) AS n FROM information_schema.table_constraints c
                       JOIN information_schema.key_column_usage k ON k.constraint_name=c.constraint_name AND k.table_name=c.table_name
                       WHERE c.table_name=%s AND c.constraint_type='PRIMARY KEY' AND k.column_name='til'""", (t,))
        if not int((cur.fetchone() or {}).get("n") or 0):
            cur.execute(f"ALTER TABLE {t} DROP CONSTRAINT IF EXISTS {t}_pkey")
            cur.execute(f"ALTER TABLE {t} ADD PRIMARY KEY (user_id, til, savol_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_bilim_til ON xb_bilim(user_id, til, toplam)")
    cur.execute("CREATE INDEX IF NOT EXISTS xb_imtihon_til ON xb_imtihon(user_id, til, tur, davr)")



def maktab_darslari_ol(cur, maktab, til="uz"):
    """REV303: mavzuga bog'liq 1–11 sinf maktab darslari — FAQAT Miya'da darsi bor (ochiladigan) mavzular.
    Kalit so'zlar o'zbekcha nomlarda qidiriladi; ruscha/inglizcha o'quvchiga o'sha kitobning parallel (bir xil tartibdagi)
    ruscha/inglizcha darsi beriladi. Kirish (bepul 5 dars / obuna) dars xonasida tekshiriladi."""
    try:
        from modules import kurslar as _ku
    except ImportError:
        from . import kurslar as _ku
    out = []
    suf = {"ru": " (izoh: rus)", "en": " (izoh: ingliz)", "de": " (izoh: nemis)", "es": " (izoh: ispan)"}.get(til, "")
    try:
        cur.execute("SAVEPOINT xb_dts")
        for m in maktab[:3]:
            sozlar = [s for s in m.get("sozlar", []) if len(s) >= 3][:6]
            if not sozlar:
                continue
            like = " OR ".join(["LOWER(COALESCE(NULLIF(d.kichik_name,''),NULLIF(d.mavzu_name,''),d.bolim_name,d.bob_name)) LIKE %s"] * len(sozlar))
            cur.execute(f"""SELECT d.topic_code, COALESCE(NULLIF(d.kichik_name,''),NULLIF(d.mavzu_name,''),NULLIF(d.bolim_name,''),d.bob_name) AS nom,
                                   d.subject_name, d.grade FROM dts_tree d
                            WHERE d.is_deleted=FALSE AND LOWER(d.subject_name) LIKE %s AND d.subject_name NOT ILIKE '%%(izoh:%%' AND ({like})
                              AND EXISTS(SELECT 1 FROM ai_brain_units u WHERE u.topic_code=d.topic_code AND u.status='published')
                            ORDER BY d.topic_code LIMIT 60""",
                        [f"%{m['fan'].lower()[:6]}%"] + [f"%{s.lower()}%" for s in sozlar])
            for r in cur.fetchall():
                g = sinf_raqami(r["grade"])
                if not (g and g in m.get("sinflar", []) and len(out) < 12) or r["topic_code"] in {x.get("uz_kod") for x in out}:
                    continue
                kod, nom, fan = r["topic_code"], _t(r["nom"]), _t(r["subject_name"])
                if suf:   # parallel kitob: o'sha fan va sinfning shu tartibdagi darsi
                    uz_list = [x["topic_code"] for x in _ku.kurs_darslari(cur, r["subject_name"], r["grade"])]
                    tr = _ku.kurs_darslari(cur, r["subject_name"] + suf, r["grade"])
                    if kod in uz_list and len(tr) == len(uz_list):
                        j = uz_list.index(kod)
                        kod, nom, fan = tr[j]["topic_code"], _t(tr[j]["nom"]), _t(r["subject_name"] + suf)
                out.append({"topic_code": kod, "uz_kod": r["topic_code"], "nom": re.sub(r"^\d+\.\s*", "", nom), "fan": fan, "sinf": g, "_t": len(out)})
        cur.execute("RELEASE SAVEPOINT xb_dts")
    except Exception:
        cur.execute("ROLLBACK TO SAVEPOINT xb_dts")
    out.sort(key=lambda x: (x["sinf"], x["uz_kod"]))   # kitobdagi tartib
    for x in out:
        x.pop("uz_kod", None); x.pop("_t", None)
    return out

PAKET_NASHR = None   # REV346: create_router to'ldiradi


def create_router(platform, kontent=None):
    router = APIRouter()
    K = kontent or KONTENT

    _ver = {"vaqt": 0.0, "holat": None}
    _ver_qulf = threading.Lock()

    def _kontent_versiya_tekshir():
        """REV380: server bir nechta ishchi jarayonda ishlaydi; Miya bittasida o'rnatiladi. Har 15 soniyada
        bazadagi yangilanish vaqti tekshiriladi — o'zgargan tilning keshi har bir jarayonda tozalanadi."""
        now = time.time()
        if now - _ver["vaqt"] < 15 or kontent is not None:
            return
        with _ver_qulf:
            if now - _ver["vaqt"] < 15:
                return
            _ver["vaqt"] = now
            try:
                conn = platform._db(); cur = conn.cursor()
                try:
                    cur.execute("SELECT til, MAX(yangilandi) AS v FROM xb_kontent GROUP BY til")
                    yangi = {r["til"]: str(r["v"]) for r in cur.fetchall()}
                finally:
                    cur.close(); conn.close()
            except Exception:   # noqa: BLE001 — jadval yo'q yoki baza band
                return
            eski = _ver["holat"]
            _ver["holat"] = yangi
            if eski is None:
                return
            for t, v in yangi.items():
                if eski.get(t) != v:
                    BAZADA_TILLAR.add(t)
                    if t == "uz":
                        KONTENT.yangila(); _NATIJA_KESH.clear()
                        for key in list(KONTENTLAR):
                            if key != "uz":
                                KONTENTLAR.pop(key, None)
                    else:
                        _kesh_tozala(t)

    def KT(til):
        """REV270: shu tilning kontenti (o'zbekcha — K)."""
        _kontent_versiya_tekshir()
        return K.ensure() if til == "uz" else kontent_of(til, kontent)
    ready = {"ok": False}
    lock = threading.Lock()
    lazy = _LazyMigration("xalqaro_baholash") if _LazyMigration else None

    def uid_of(token, authorization):
        return int(platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization)))

    def run_db(fn):
        conn = platform._db()
        cur = conn.cursor()
        try:
            if not ready["ok"]:
                if lazy is not None:
                    lazy.run(conn, cur, migrate)
                    ready["ok"] = lazy.ok
                else:
                    with lock:
                        if not ready["ok"]:
                            migrate(cur)
                            conn.commit()
                            ready["ok"] = True
            return fn(conn, cur)
        finally:
            cur.close()
            conn.close()

    def user_info(cur, user_id):
        info = {"user_id": user_id, "sinf": 0, "class": "", "harf": "", "maktab_id": None, "role": "", "ism": ""}
        try:
            cur.execute("SAVEPOINT xb_user")
            cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
            row = dict(cur.fetchone() or {})
            cur.execute("RELEASE SAVEPOINT xb_user")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT xb_user")
            row = {}
        info.update(sinf=sinf_raqami(row.get("class")), **{"class": _t(row.get("class")), "harf": _t(row.get("class_letter")),
                    "maktab_id": row.get("maktab_id"), "role": _t(row.get("role")), "ism": _t(row.get("full_name"))})
        return info

    def toplam_of(key, sinf, til="uz"):
        k = KT(til)
        tops = k.ramka.get("toplamlar", {})
        if key in tops:
            return key
        return next((t for t in tavsiya_toplamlar(sinf) if t in tops), next(iter(tops), tavsiya_toplamlar(sinf)[0]))

    def bilim_xaritasi(cur, user_id, til="uz"):
        cur.execute("SELECT savol_id, urinish, togri, oxirgi_togri, yangilangan FROM xb_bilim WHERE user_id=%s AND til=%s", (user_id, til))
        return {r["savol_id"]: dict(r) for r in cur.fetchall()}

    def mavzu_holati(bilim, savollar):
        """Mavzu bo'yicha o'zlashtirish: yechilgan savollar ulushi va aniqlik."""
        jami = len(savollar)
        urin = [bilim[s["id"]] for s in savollar if s["id"] in bilim]
        togri = sum(1 for b in urin if b["oxirgi_togri"])
        aniqlik = round(100 * sum(b["togri"] for b in urin) / max(1, sum(b["urinish"] for b in urin))) if urin else None
        ozlashtirish = round(100 * togri / max(1, jami))
        return {"jami": jami, "urinilgan": len(urin), "ozlashtirgan": togri, "foiz": ozlashtirish, "aniqlik": aniqlik}

    def ustoz_gapi(cur, user, bilim, til="uz"):
        """Kabu o'quvchiga nima deydi: maqtov, eslatma yoki tanbeh (faollik va natijaga qarab)."""
        now = datetime.now(TZ)
        oxirgi = max([b["yangilangan"] for b in bilim.values()], default=None)
        kun_oldin = (now - oxirgi).days if oxirgi else None
        hafta = sum(1 for b in bilim.values() if b["yangilangan"] and (now - b["yangilangan"]).days < 7)
        cur.execute("SELECT tur, davr, ball, foiz FROM xb_imtihon WHERE user_id=%s AND til=%s AND rasmiy AND topshirilgan IS NOT NULL ORDER BY id DESC LIMIT 20", (user["user_id"], til))
        imt = [dict(r) for r in cur.fetchall()]
        haftalik_bor = any(r["tur"] == "haftalik" and r["davr"] == davr_kaliti("haftalik") for r in imt)
        ism = (user.get("ism") or "").split()[0] if user.get("ism") else ""
        murojaat = f"{ism}, " if ism else ""
        m = murojaat
        if not bilim and not imt:
            gap = ("salom", matn("salom", til, m=m))
        elif kun_oldin is not None and kun_oldin >= 7:
            gap = ("tanbeh", matn("tanbeh_kun", til, m=m, kun=kun_oldin))
        elif imt and imt[0]["foiz"] is not None and imt[0]["foiz"] < 40:
            gap = ("tanbeh", matn("tanbeh_foiz", til, m=m, foiz=imt[0]["foiz"]))
        elif not haftalik_bor and bugun().weekday() >= 3:
            gap = ("eslatma", matn("eslatma_haftalik", til, m=m))
        elif hafta < 10:
            gap = ("eslatma", matn("eslatma_kam", til, m=m, hafta=hafta))
        elif imt and imt[0]["ball"] and imt[0]["ball"] >= 550:
            gap = ("maqtov", matn("maqtov_yuqori", til, m=m, ball=imt[0]["ball"]))
        else:
            gap = ("maqtov", matn("maqtov", til, m=m, hafta=hafta))
        txt = gap[1]
        if m and txt.startswith(m):   # murojaatdan keyingi birinchi harf — kichik, gap boshi — katta
            pass
        elif txt:
            txt = txt[0].upper() + txt[1:]
        return {"tur": gap[0], "matn": txt}

    # ─────────── katalog ───────────
    @router.get("/api/xalqaro/katalog")
    def katalog(token: str = None, sinf: int = Query(0, ge=0, le=11), til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = KT(til)

        def run(conn, cur):
            user = user_info(cur, user_id)
            s = sinf or user["sinf"]
            bilim = bilim_xaritasi(cur, user_id, til)
            cur.execute("SELECT COUNT(*) AS n FROM xb_takror WHERE user_id=%s AND til=%s AND keyingi<=%s", (user_id, til, bugun()))
            takror = int((cur.fetchone() or {}).get("n") or 0)
            gap = ustoz_gapi(cur, user, bilim, til)
            if user["role"] in ("oqituvchi", "direktor", "zam_direktor") or admin_mi(cur, user_id):
                gap = {"tur": "salom", "matn": matn("oqituvchi", til)}
            # boshqa tillardagi faollik — faqat «shu tilda alohida» ekanini ko'rsatish uchun (natijalar aralashmaydi)
            cur.execute("SELECT til, COUNT(*) AS n FROM xb_bilim WHERE user_id=%s GROUP BY til", (user_id,))
            boshqa = {r["til"]: int(r["n"]) for r in cur.fetchall()}
            conn.commit()
            toplamlar = []
            for tk, tm in k.ramka.get("toplamlar", {}).items():
                mavzular = []
                for t in k.ramka["mavzular"].get(tk, []):
                    sv = k.by_mavzu.get(t["kalit"], [])
                    foizlar = [x.get("xalqaro_ortacha") if x.get("xalqaro_ortacha") is not None else x.get("oecd_foiz") for x in sv]
                    foizlar = [_son(f) for f in foizlar if _son(f) is not None]   # REV304: ma'lumotda matn bo'lishi mumkin («—»)
                    dars = k.dars_by_kod.get("XB-" + t["kalit"])
                    mavzular.append({"kalit": t["kalit"], "nom": t["nom"], "soha": t["soha"], "soha_nomi": t["soha_nomi"],
                                     "dars_kodi": dars["kod"] if dars else "", "savollar": len(sv),
                                     "xalqaro_foiz": round(sum(foizlar) / len(foizlar)) if foizlar else None,
                                     "holat": mavzu_holati(bilim, sv)})
                toplamlar.append({**tm, "kalit": tk, "mavzular": mavzular, "tavsiya": tk in tavsiya_toplamlar(s),
                                  "darajalar": (k.ramka.get("darajalar") or {}).get(tk), "jarayonlar": (k.ramka.get("jarayonlar") or {}).get(tk)})
            return {"sinf": s, "toplamlar": toplamlar, "takror": takror, "ustoz": gap, "til": til,
                    "tillar": {t: {"tayyor": bool(KT(t).ramka.get("toplamlar")), "toplamlar": len(KT(t).ramka.get("toplamlar", {})),
                                   "javoblar": boshqa.get(t, 0)} for t in TILLAR},
                    "tayyor_emas": None if toplamlar else matn("tayyor_emas", til),
                    "fikrlash": k.ramka.get("fikrlash", {}), "ozbekiston": k.natijalar.get("ozbekiston", {}),
                    "uz_nomi": k.natijalar.get("uz_nomi") or "O‘zbekiston", "manba": matn("manba", til)}
        return run_db(run)

    # ─────────── mavzu ───────────
    def mavzu_tafsilot(cur, user, kalit, til="uz"):
        k = KT(til)
        t = k.mavzu_by_kalit.get(kalit)
        if not t:
            raise HTTPException(404, matn("mavzu_yoq", til))
        sv = k.by_mavzu.get(kalit, [])
        bilim = bilim_xaritasi(cur, user["user_id"], til)
        dars = k.dars_by_kod.get("XB-" + kalit) or {}
        foizlar = [x["xalqaro_ortacha"] if x.get("xalqaro_ortacha") is not None else x.get("oecd_foiz") for x in sv]
        foizlar = [f for f in foizlar if f is not None]
        pisa = pisami(t["toplam"])
        qb = [x["qiyinlik_ball"] for x in sv if isinstance(x.get("qiyinlik_ball"), (int, float))]
        davlat = {}
        for x in sv:
            for nom, f in (x.get("davlatlar") or {}).items():
                if _son(f) is not None:   # REV304: «—» kabi matnli qiymatlar hisobga olinmaydi (oldin mavzu 500 xato berardi)
                    davlat.setdefault(nom, []).append(_son(f))
        davlat_ort = sorted(([n, round(sum(v) / len(v))] for n, v in davlat.items() if len(v) >= max(1, len(sv) // 2)), key=lambda r: -r[1])
        nomlar = k.natijalar.get("nomlar", {})
        fikrlash = {}
        for x in sv:
            f = fikrlash.setdefault(x["fikrlash"], {"jami": 0, "ozlashtirgan": 0})
            f["jami"] += 1
            if bilim.get(x["id"], {}).get("oxirgi_togri"):
                f["ozlashtirgan"] += 1
        # namuna savollar: har fikrlash darajasidan bittadan (javob va yechimi bilan)
        namuna = []
        for f in ("bilish", "qollash", "mulohaza"):
            cand = sorted([x for x in sv if x["fikrlash"] == f], key=savol_qiyinligi)
            if cand:
                x = cand[len(cand) // 2]
                namuna.append(_variant_public(x, 0, javob_bilan=True, k=k))
        return {
            "kalit": kalit, "nom": t["nom"], "soha_nomi": t["soha_nomi"], "toplam": t["toplam"],
            "toplam_nomi": k.ramka["toplamlar"].get(t["toplam"], {}), "dars_kodi": dars.get("kod", ""),
            "maqsad": dars.get("maqsad", ""), "strategiyalar": dars.get("strategiyalar", []), "tipik_xatolar": dars.get("tipik_xatolar", []),
            "maktab": t.get("maktab", []) if til == "uz" else [], "kalit_sozlar": dars.get("kalit_sozlar", []), "til": til,
            "xalqaro_foiz": round(sum(foizlar) / len(foizlar)) if foizlar else None,
            "davlatlar": [[nomlar.get(n, n), f] for n, f in davlat_ort[:8]] + [[nomlar.get(n, n), f] for n, f in davlat_ort[8:] if n in ("Kazakhstan", "Russian Federation")],
            "holat": mavzu_holati(bilim, sv), "fikrlash": fikrlash, "namuna": namuna, "dastur": "PISA" if pisa else "TIMSS",
            # PISA: savollar qiyinligi PISA ballida va darajalarda (statistika — OECD)
            "pisa_qiyinlik": {"min": min(qb), "max": max(qb), "ortacha": round(sum(qb) / len(qb)),
                              "daraja": daraja_of(round(sum(qb) / len(qb)), t["toplam"], til)["nom"]} if pisa and qb else None,
            "kunikmalar": [x.get("kunikma") for x in sv if x.get("kunikma")][:12],
        }

    @router.get("/api/xalqaro/mavzu/{kalit}")
    def mavzu(kalit: str, token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til_kodi(til)

        def run(conn, cur):
            user = user_info(cur, user_id)
            out = mavzu_tafsilot(cur, user, kalit[:20], til)
            out["maktab_darslari"] = maktab_darslari(cur, out["maktab"], til)   # REV303: faqat Miya'da darsi bor mavzular, o'quvchi tilida
            out["reyting"] = mavzu_reytingi(cur, user, kalit[:20], til)
            conn.commit()
            return out
        return run_db(run)

    def maktab_darslari(cur, maktab, til="uz"):
        return maktab_darslari_ol(cur, maktab, til)

    def mavzu_reytingi(cur, user, kalit, til="uz"):
        """Shu mavzu bo'yicha sinfdoshlar orasida o'rin (o'zlashtirgan savollar soni)."""
        if not user.get("maktab_id") or not user.get("class"):
            return None
        try:
            cur.execute("SAVEPOINT xb_mr")
            # REV318: barcha tillar — bir savol (bir xil ID) bir marta: istalgan tilda to'g'ri yechilgan bo'lsa hisoblanadi
            cur.execute("""SELECT b.user_id, COUNT(DISTINCT b.savol_id) FILTER (WHERE b.oxirgi_togri) AS n FROM xb_bilim b JOIN users u ON u.user_id=b.user_id
                           WHERE b.mavzu=%s AND u.maktab_id=%s AND u.class=%s GROUP BY b.user_id""", (kalit, user["maktab_id"], user["class"]))
            rows = cur.fetchall()
            cur.execute("RELEASE SAVEPOINT xb_mr")
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT xb_mr")
            return None
        mening = next((int(r["n"]) for r in rows if int(r["user_id"]) == user["user_id"]), 0)
        if len(rows) < REYTING_MIN:
            return {"jami": len(rows), "orin": None, "mening": mening}
        return {"jami": len(rows), "orin": 1 + sum(1 for r in rows if int(r["n"]) > mening), "mening": mening,
                "eng_kop": max(int(r["n"]) for r in rows)}

    # ─────────── mavzu oldi ───────────
    @router.get("/api/xalqaro/mavzu_oldi")
    def mavzu_oldi(token: str = None, fan: str = Query("", max_length=80), sinf: str = Query("", max_length=20),
                   mavzu_nomi: str = Query("", max_length=200), til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = K.ensure()   # moslash o'zbekcha maktab dasturi bo'yicha; natija — shu tilda (tarjimasi bo'lmasa — topilmadi)
        s = sinf_raqami(sinf)
        nom = mavzu_nomi.lower()
        fan_l = fan.lower()
        best, best_score = None, 0
        for kalit, t in k.mavzu_by_kalit.items():
            score = 0
            if pisami(t["toplam"]) and s and s < 7:   # PISA — 15 yosh; 7-sinfdan kichiklarga ko'rsatilmaydi
                continue
            for m in t.get("maktab", []):
                fan_mos = m["fan"].lower()[:5] in fan_l or (m["fan"] == "Matematika" and re.search(r"matem|algebra|geometr", fan_l)) \
                    or (m["fan"] == "Tabiiy fanlar" and re.search(r"tabiiy|tabiat|atrof|science", fan_l))
                if not fan_mos:
                    continue
                hits = sum(1 for w in m.get("sozlar", []) if w.lower() in nom)
                if hits:
                    score = max(score, hits * 10 + (5 if s in m.get("sinflar", []) else 0)
                                + (3 if s and abs(k.ramka["toplamlar"][t["toplam"]]["sinf"] - s) <= 2 else 0))
            if score > best_score:
                best, best_score = kalit, score
        if not best or best not in KT(til).mavzu_by_kalit:
            return {"topildi": False}

        def run(conn, cur):
            user = user_info(cur, user_id)
            out = mavzu_tafsilot(cur, user, best, til)
            out["reyting"] = mavzu_reytingi(cur, user, best, til)
            bilim = bilim_xaritasi(cur, user_id, til)
            out["ustoz"] = ustoz_gapi(cur, user, bilim, til)
            conn.commit()
            out["topildi"] = True
            return out
        return run_db(run)

    # ─────────── mashq ───────────
    @router.get("/api/xalqaro/mashq")
    def mashq(token: str = None, mavzu: str = Query("", max_length=20), toplam: str = Query("", max_length=12),
              soni: int = Query(8, ge=1, le=30), fikrlash: str = Query("", max_length=10), til: str = Query("uz", max_length=8),
              toplam_i: int = Query(0, ge=0, le=50), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = KT(til)

        def run(conn, cur):
            bilim = bilim_xaritasi(cur, user_id, til)
            conn.commit()
            if mavzu and toplam_i:   # REV399: aniq to'plam — doim bir xil savollar, osondan qiyinga
                tl = mavzu_toplamlari(k.by_mavzu.get(mavzu, []))
                if not 1 <= toplam_i <= len(tl):
                    raise HTTPException(404, matn("savol_yoq", til))
                out = []
                for s in tl[toplam_i - 1]:
                    b = bilim.get(s["id"])
                    vi = (b["urinish"] if b else 0) % max(1, len(s["variantlar"]))
                    out.append(_variant_public(s, vi, javob_bilan=True, k=k))
                return {"savollar": out, "til": til, "toplam_info": {"i": toplam_i, "jami": len(tl), "daraja": toplam_darajasi(toplam_i, len(tl))}}
            if mavzu:
                pool = list(k.by_mavzu.get(mavzu, []))
            else:
                pool = [s for s in k.savollar if s["toplam"] == (toplam or "T11_G8_M")]
            if fikrlash:
                pool = [s for s in pool if s["fikrlash"] == fikrlash] or pool
            # avval yechilmagan / xato qilinganlar, keyin qolganlari; oson → qiyin
            rng = random.Random()
            rng.shuffle(pool)
            pool.sort(key=lambda s: (bool(bilim.get(s["id"], {}).get("oxirgi_togri")), -(s.get("xalqaro_ortacha") or 50) // 15))
            chosen = pool[:soni]
            out = []
            for s in chosen:
                b = bilim.get(s["id"])
                vi = (b["urinish"] if b else 0) % max(1, len(s["variantlar"]))
                out.append(_variant_public(s, vi, javob_bilan=True, k=k))
            return {"savollar": out, "til": til}
        return run_db(run)

    @router.get("/api/xalqaro/mavzu_toplamlar")
    def mavzu_toplamlar(token: str = None, mavzu: str = Query(..., max_length=20), til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """REV399: mavzudagi test to'plamlari: har birida nechta savol, darajasi, o'quvchi nechtasini o'zlashtirgan."""
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = KT(til)
        m = k.mavzu_by_kalit.get(mavzu)
        if not m:
            raise HTTPException(404, matn("savol_yoq", til))

        def run(conn, cur):
            bilim = bilim_xaritasi(cur, user_id, til)
            conn.commit()
            tl = mavzu_toplamlari(k.by_mavzu.get(mavzu, []))
            out = []
            for i, t in enumerate(tl, 1):
                oz = sum(1 for s in t if bilim.get(s["id"], {}).get("oxirgi_togri"))
                ur = sum(1 for s in t if s["id"] in bilim)
                out.append({"i": i, "daraja": toplam_darajasi(i, len(tl)), "soni": len(t), "ozlashtirgan": oz, "urinilgan": ur,
                            "rasmli": sum(1 for s in t if any(v.get("rasm") for v in s["variantlar"]))})
            hozirgi = next((x["i"] for x in out if x["ozlashtirgan"] < x["soni"]), len(out))
            return {"mavzu": mavzu, "nom": m.get("nom", mavzu), "jami": sum(x["soni"] for x in out), "toplamlar": out, "hozirgi": hozirgi}
        return run_db(run)

    @router.post("/api/xalqaro/javob")
    def javob(body: JavobBody, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        til = til_kodi(body.til or til)
        k = KT(til)
        s = k.by_id.get(body.savol_id)
        if not s or body.v >= len(s["variantlar"]):
            raise HTTPException(404, matn("savol_yoq", til))
        v = s["variantlar"][body.v]
        ok = tekshir(v, body.javob)

        def run(conn, cur):
            cur.execute("""INSERT INTO xb_bilim(user_id, til, savol_id, toplam, mavzu, urinish, togri, oxirgi_togri, aytib, yangilangan, oxirgi_v, oxirgi_javob)
                           VALUES(%s,%s,%s,%s,%s,1,%s,%s,%s,NOW(),%s,%s)
                           ON CONFLICT (user_id, til, savol_id) DO UPDATE SET urinish=xb_bilim.urinish+1, togri=xb_bilim.togri+EXCLUDED.togri,
                             oxirgi_togri=EXCLUDED.oxirgi_togri, aytib=xb_bilim.aytib+EXCLUDED.aytib, yangilangan=NOW(),
                             oxirgi_v=EXCLUDED.oxirgi_v, oxirgi_javob=EXCLUDED.oxirgi_javob""",
                        (user_id, til, s["id"], s["toplam"], s["mavzu"], int(ok), ok, int(body.usul == "aytib"), body.v, body.javob[:60]))
            cur.execute("SELECT quti FROM xb_takror WHERE user_id=%s AND til=%s AND savol_id=%s", (user_id, til, s["id"]))
            row = cur.fetchone()
            quti = None
            if not ok:
                quti = 1
                cur.execute("""INSERT INTO xb_takror(user_id, til, savol_id, v, quti, keyingi) VALUES(%s,%s,%s,%s,1,%s)
                               ON CONFLICT (user_id, til, savol_id) DO UPDATE SET quti=1, v=EXCLUDED.v, keyingi=EXCLUDED.keyingi""",
                            (user_id, til, s["id"], (body.v + 1) % len(s["variantlar"]), bugun() + timedelta(days=1)))
            elif row:
                quti = min(5, int(row["quti"]) + 1)
                if quti >= 5 and body.takror:
                    cur.execute("DELETE FROM xb_takror WHERE user_id=%s AND til=%s AND savol_id=%s", (user_id, til, s["id"]))
                else:
                    cur.execute("UPDATE xb_takror SET quti=%s, v=%s, keyingi=%s WHERE user_id=%s AND til=%s AND savol_id=%s",
                                (quti, (body.v + 1) % len(s["variantlar"]), bugun() + timedelta(days=QUTI_KUN[quti]), user_id, til, s["id"]))
            conn.commit()
            return {"togri": ok, "togri_javob": v.get("togri") if v["turi"] == "tanlov" else v.get("javob", "").split("|")[0],
                    "quti": quti}
        return run_db(run)

    @router.get("/api/xalqaro/takror")
    def takror(token: str = None, soni: int = Query(15, ge=1, le=40), til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = KT(til)

        def run(conn, cur):
            cur.execute("SELECT savol_id, v, quti, keyingi FROM xb_takror WHERE user_id=%s AND til=%s AND keyingi<=%s ORDER BY keyingi, quti LIMIT %s",
                        (user_id, til, bugun(), soni))
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) AS n FROM xb_takror WHERE user_id=%s AND til=%s", (user_id, til))
            jami = int((cur.fetchone() or {}).get("n") or 0)
            conn.commit()
            out = []
            for r in rows:
                s = k.by_id.get(r["savol_id"])
                if s:
                    item = _variant_public(s, int(r["v"]) % len(s["variantlar"]), javob_bilan=True, k=k)
                    item["quti"] = int(r["quti"])
                    out.append(item)
            return {"savollar": out, "navbatda": jami}
        return run_db(run)

    # ─────────── imtihonlar ───────────
    def bloklar(toplam_key, tur, til="uz"):
        """Imtihon qismlari: yillik — 2 qism (matematika + tabiiy fanlar), qolganlari — 1 qism."""
        k = KT(til)
        tm = k.ramka["toplamlar"][toplam_key]
        if tur == "yillik":
            juft = YILLIK_JUFT.get(toplam_key, toplam_key)
            if juft not in k.ramka["toplamlar"]:   # juft to'plam shu tilda hali yo'q — ikkala qism ham shu to'plamdan
                juft = toplam_key
            return [toplam_key, juft] if toplam_key.endswith("_M") or pisami(toplam_key) else [juft, toplam_key]
        return [toplam_key] if tm else []

    @router.get("/api/xalqaro/imtihonlar")
    def imtihonlar(token: str = None, toplam: str = Query("", max_length=12), til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til_kodi(til)

        def run(conn, cur):
            user = user_info(cur, user_id)
            tk = toplam_of(toplam, user["sinf"], til)
            band = band_of(tk)
            cur.execute("""SELECT id, tur, toplam, davr, rasmiy, foiz, ball, topshirilgan, tugash, natija FROM xb_imtihon
                           WHERE user_id=%s AND til=%s ORDER BY id DESC LIMIT 60""", (user_id, til))
            rows = [dict(r) for r in cur.fetchall()]
            conn.commit()
            out = []
            now = datetime.now(TZ)
            for tur, cfg in IMTIHON_TURLARI.items():
                soni, daqiqa = cfg[band]
                davr = davr_kaliti(tur)
                mos = [r for r in rows if r["tur"] == tur and r["davr"] == davr and (r["toplam"] == tk or tur == "yillik")]
                rasmiy = next((r for r in mos if r["rasmiy"] and r["topshirilgan"]), None)
                ochiq = next((r for r in mos if not r["topshirilgan"] and r["tugash"] and r["tugash"] > now), None)
                tarix = [{"id": r["id"], "davr": r["davr"], "ball": r["ball"], "foiz": r["foiz"]}
                         for r in rows if r["tur"] == tur and r["rasmiy"] and r["topshirilgan"]][:8]
                out.append({"tur": tur, "nom": imtihon_nomi(tur, til), "savollar": soni * (2 if tur == "yillik" else 1), "daqiqa": daqiqa * (2 if tur == "yillik" else 1),
                            "qismlar": 2 if tur == "yillik" else 1, "davr": davr, "davr_oxiri": davr_oxiri(tur).isoformat(),
                            "topshirildi": bool(rasmiy), "natija": {"id": rasmiy["id"], "ball": rasmiy["ball"], "foiz": rasmiy["foiz"]} if rasmiy else None,
                            "davom": {"id": ochiq["id"]} if ochiq else None, "tarix": list(reversed(tarix))})
            return {"toplam": tk, "imtihonlar": out, "til": til}
        return run_db(run)

    def savollar_jsonb(tanlangan, rng):
        return [{"id": s["id"], "v": rng.randrange(len(s["variantlar"]))} for s in tanlangan]

    @router.post("/api/xalqaro/imtihon/boshla")
    def boshla(body: BoshlaBody, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        til = til_kodi(body.til or til)
        if body.tur not in IMTIHON_TURLARI:
            raise HTTPException(400, matn("tur_yoq", til))
        k = KT(til)

        def run(conn, cur):
            user = user_info(cur, user_id)
            tk = toplam_of(body.toplam, user["sinf"], til)
            band = band_of(tk)
            soni, daqiqa = IMTIHON_TURLARI[body.tur][band]
            davr = davr_kaliti(body.tur)
            now = datetime.now(TZ)
            # tugallanmagan sessiya bo'lsa — o'shani davom ettiramiz (sahifani yangilash imtihonni qayta boshlamaydi)
            cur.execute("""SELECT * FROM xb_imtihon WHERE user_id=%s AND til=%s AND tur=%s AND davr=%s AND topshirilgan IS NULL AND tugash>%s
                           ORDER BY id DESC LIMIT 1""", (user_id, til, body.tur, davr, now))
            row = cur.fetchone()
            if not row:
                # REV318: rasmiy natija davrda BITTA — qaysi tilda yechilganidan qat'i nazar (til almashtirib qayta rasmiy topshirib bo'lmaydi)
                cur.execute("SELECT 1 FROM xb_imtihon WHERE user_id=%s AND tur=%s AND davr=%s AND rasmiy AND topshirilgan IS NOT NULL LIMIT 1",
                            (user_id, body.tur, davr))
                rasmiy = not body.mashq and not cur.fetchone()
                cur.execute("SELECT savollar FROM xb_imtihon WHERE user_id=%s AND til=%s ORDER BY id DESC LIMIT 6", (user_id, til))
                yaqin = [x["id"] for r in cur.fetchall() for x in (r["savollar"] or [])]
                rng = random.Random()
                qismlar = []
                for q in bloklar(tk, body.tur, til):
                    pool = [s for s in k.savollar if s["toplam"] == q]
                    tanlangan = reja_boyicha_tanla(pool, soni, REJA.get(q, {}), rng, yaqin)
                    qismlar.append({"toplam": q, "savollar": savollar_jsonb(tanlangan, rng)})
                tugash = now + timedelta(minutes=daqiqa)
                cur.execute("""INSERT INTO xb_imtihon(user_id, til, tur, toplam, davr, rasmiy, sinf, maktab_id, sinf_nomi, savollar, qismlar, qism, tugash)
                               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,1,%s) RETURNING *""",
                            (user_id, til, body.tur, tk, davr, rasmiy, user["sinf"], user["maktab_id"],
                             f"{user['class']}{user['harf']}", json.dumps([x for q in qismlar for x in q["savollar"]]), len(qismlar), tugash))
                row = cur.fetchone()
                cur.execute("UPDATE xb_imtihon SET natija=%s::jsonb WHERE id=%s",
                            (json.dumps({"qism_toplam": [q["toplam"] for q in qismlar], "qism_soni": [len(q["savollar"]) for q in qismlar]}), row["id"]))
                row = dict(row)
                row["natija"] = {"qism_toplam": [q["toplam"] for q in qismlar], "qism_soni": [len(q["savollar"]) for q in qismlar]}
            conn.commit()
            return sessiya_korinishi(dict(row), daqiqa)
        return run_db(run)

    def sessiya_korinishi(row, daqiqa):
        til = til_kodi(row.get("til"))
        k = KT(til)
        meta = row.get("natija") or {}
        sonlar = meta.get("qism_soni") or [len(row["savollar"])]
        qism = int(row.get("qism") or 1)
        bosh = sum(sonlar[: qism - 1])
        items = []
        for i, x in enumerate(row["savollar"][bosh: bosh + sonlar[qism - 1]]):
            s = k.by_id.get(x["id"])
            if s:
                p = _variant_public(s, x["v"] % len(s["variantlar"]), k=k)
                p["n"] = bosh + i
                items.append(p)
        toplamlar = meta.get("qism_toplam") or [row["toplam"]]
        return {"sessiya": row["id"], "tur": row["tur"], "nom": imtihon_nomi(row["tur"], til), "rasmiy": row["rasmiy"], "til": til,
                "qism": qism, "qismlar": int(row.get("qismlar") or 1),
                "qism_fani": k.ramka["toplamlar"].get(toplamlar[qism - 1], {}).get("fan_nomi", ""),
                "tugash": row["tugash"].isoformat() if hasattr(row["tugash"], "isoformat") else row["tugash"],
                "server_vaqt": datetime.now(TZ).isoformat(), "daqiqa": daqiqa, "savollar": items,
                "javoblar": row.get("javoblar") or {}}

    @router.post("/api/xalqaro/imtihon/topshir")
    def topshir(body: TopshirBody, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)

        def run(conn, cur):
            cur.execute("SELECT * FROM xb_imtihon WHERE id=%s AND user_id=%s FOR UPDATE", (body.sessiya, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, matn("imtihon_yoq", til_kodi(til)))
            row = dict(row)
            rtil = til_kodi(row.get("til"))   # imtihon qaysi tilda boshlangan bo'lsa — shu tilda baholanadi va saqlanadi
            k = KT(rtil)
            if row["topshirilgan"]:
                conn.commit()
                return {"id": row["id"], "tayyor": True}
            now = datetime.now(TZ)
            kech = now > row["tugash"] + timedelta(seconds=90)   # tarmoq kechikishi uchun 90 s
            javoblar = dict(row["javoblar"] or {})
            # vaqt tugagandan keyin yuborilgan javoblar qabul qilinmaydi (oldin saqlanganlari qoladi)
            if not kech:
                for kk, vv in (body.javoblar or {}).items():
                    if re.fullmatch(r"\d{1,3}", str(kk)):
                        javoblar[str(kk)] = str(vv)[:200]
            meta = dict(row.get("natija") or {})
            band = band_of(row["toplam"])
            daqiqa = IMTIHON_TURLARI[row["tur"]][band][1]
            if int(row["qism"]) < int(row["qismlar"]) and not kech:
                # keyingi qism: tanaffusdan keyin yangi vaqt
                cur.execute("UPDATE xb_imtihon SET javoblar=%s::jsonb, qism=qism+1, tugash=%s, chiqishlar=chiqishlar+%s WHERE id=%s RETURNING *",
                            (json.dumps(javoblar), now + timedelta(minutes=daqiqa + 10), body.chiqishlar, row["id"]))
                nr = dict(cur.fetchone())
                conn.commit()
                out = sessiya_korinishi(nr, daqiqa)
                out["tanaffus"] = 10
                return out
            natija = bahola(row["savollar"], javoblar, meta, rtil)
            cur.execute("""UPDATE xb_imtihon SET javoblar=%s::jsonb, topshirilgan=NOW(), foiz=%s, ball=%s, xato_ball=%s,
                           natija=%s::jsonb, chiqishlar=chiqishlar+%s WHERE id=%s""",
                        (json.dumps(javoblar), natija["foiz"], natija["ball"], natija["xato"], json.dumps({**meta, **natija}),
                         body.chiqishlar, row["id"]))
            # imtihondagi xatolar takrorlash navbatiga tushadi
            for i, (x, ok) in enumerate(zip(row["savollar"], natija["togri_list"])):
                s0 = k.by_id.get(x["id"])
                if s0:   # REV261: imtihon javoblari ham bilim xaritasiga (o'qituvchi xatolarni ko'radi)
                    cur.execute("""INSERT INTO xb_bilim(user_id, til, savol_id, toplam, mavzu, urinish, togri, oxirgi_togri, yangilangan, oxirgi_v, oxirgi_javob)
                                   VALUES(%s,%s,%s,%s,%s,1,%s,%s,NOW(),%s,%s)
                                   ON CONFLICT (user_id, til, savol_id) DO UPDATE SET urinish=xb_bilim.urinish+1, togri=xb_bilim.togri+EXCLUDED.togri,
                                     oxirgi_togri=EXCLUDED.oxirgi_togri, yangilangan=NOW(), oxirgi_v=EXCLUDED.oxirgi_v, oxirgi_javob=EXCLUDED.oxirgi_javob""",
                                (user_id, rtil, x["id"], s0["toplam"], s0["mavzu"], int(ok), ok, x["v"] % len(s0["variantlar"]), str(javoblar.get(str(i), ""))[:60]))
                if not ok:
                    s = k.by_id.get(x["id"])
                    if s:
                        cur.execute("""INSERT INTO xb_takror(user_id, til, savol_id, v, quti, keyingi) VALUES(%s,%s,%s,%s,1,%s)
                                       ON CONFLICT (user_id, til, savol_id) DO UPDATE SET quti=1, keyingi=EXCLUDED.keyingi""",
                                    (user_id, rtil, x["id"], (x["v"] + 1) % len(s["variantlar"]), bugun() + timedelta(days=1)))
            conn.commit()
            return {"id": row["id"], "tayyor": True}
        return run_db(run)

    def bahola(savollar, javoblar, meta, til="uz"):
        k = KT(til)
        rasch, togri_list, soha, fik = [], [], {}, {}
        qism_toplam = meta.get("qism_toplam") or []
        for i, x in enumerate(savollar):
            s = k.by_id.get(x["id"])
            if not s:
                togri_list.append(False)
                continue
            v = s["variantlar"][x["v"] % len(s["variantlar"])]
            ok = tekshir(v, javoblar.get(str(i), ""))
            togri_list.append(ok)
            rasch.append((savol_qiyinligi(s), ok))
            for d, key in ((soha, f"{s['toplam']}|{s['soha']}"), (fik, s["fikrlash"])):
                e = d.setdefault(key, [0, 0])
                e[0] += int(ok)
                e[1] += 1
        ball, xato = timss_ball(rasch)
        foiz = round(100 * sum(togri_list) / max(1, len(togri_list)))
        # qismlar (yillik: matematika va tabiiy fanlar) bo'yicha alohida ball
        qism_ball = {}
        for q in qism_toplam:
            r = [(savol_qiyinligi(k.by_id[x["id"]]), ok) for x, ok in zip(savollar, togri_list)
                 if x["id"] in k.by_id and k.by_id[x["id"]]["toplam"] == q]
            if r:
                qism_ball[q] = timss_ball(r)[0]
        return {"foiz": foiz, "ball": ball, "xato": xato, "togri": sum(togri_list), "jami": len(togri_list),
                "togri_list": togri_list, "daraja": daraja_of(ball or 0, (qism_toplam or [None])[0], til), "soha": soha, "fikrlash": fik, "qism_ball": qism_ball}

    @router.get("/api/xalqaro/imtihon/{sessiya}")
    def imtihon_tahlil(sessiya: int, token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)

        def run(conn, cur):
            cur.execute("SELECT * FROM xb_imtihon WHERE id=%s AND user_id=%s", (sessiya, user_id))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, matn("imtihon_yoq", til_kodi(til)))
            row = dict(row)
            rtil = til_kodi(row.get("til"))
            k = KT(rtil)
            if not row["topshirilgan"]:
                band = band_of(row["toplam"])
                conn.commit()
                return {"tayyor": False, **sessiya_korinishi(row, IMTIHON_TURLARI[row["tur"]][band][1])}
            reyt = imtihon_reytingi(cur, row)
            conn.commit()
            natija = row["natija"] or {}
            items = []
            for i, x in enumerate(row["savollar"]):
                s = k.by_id.get(x["id"])
                if not s:
                    continue
                p = _variant_public(s, x["v"] % len(s["variantlar"]), javob_bilan=True, k=k)
                p.update(n=i, berilgan=(row["javoblar"] or {}).get(str(i), ""), togri_mi=bool((natija.get("togri_list") or [])[i:i + 1] and natija["togri_list"][i]))
                items.append(p)
            sohalar = {}
            for key, (t, j) in (natija.get("soha") or {}).items():
                tk, soha = key.split("|")
                nom = next((m["soha_nomi"] for m in k.ramka["mavzular"].get(tk, []) if m["soha"] == soha), soha)
                sohalar[key] = {"nom": nom, "fan": k.ramka["toplamlar"].get(tk, {}).get("fan_nomi", ""), "togri": t, "jami": j}
            jadvallar = {}
            for q in (natija.get("qism_toplam") or [row["toplam"]]):
                b = (natija.get("qism_ball") or {}).get(q, row["ball"])
                jadvallar[q] = {"fan": k.ramka["toplamlar"].get(q, {}).get("fan_nomi", ""), "dastur": k.ramka["toplamlar"].get(q, {}).get("dastur", ""),
                                "ball": b, "daraja": daraja_of(b or 0, q, rtil), "solishtirish": solishtir(k, q, b)}
            return {"tayyor": True, "id": row["id"], "tur": row["tur"], "nom": imtihon_nomi(row["tur"], rtil), "rasmiy": row["rasmiy"], "til": rtil,
                    "davr": row["davr"], "foiz": row["foiz"], "ball": row["ball"], "xato_ball": row["xato_ball"],
                    "daraja": daraja_of(row["ball"] or 0, row["toplam"], rtil), "dastur": "PISA" if pisami(row["toplam"]) else "TIMSS",
                    "togri": natija.get("togri"), "jami": natija.get("jami"),
                    "sohalar": sohalar, "fikrlash": natija.get("fikrlash") or {}, "davlatlar": jadvallar, "reyting": reyt,
                    "chiqishlar": row["chiqishlar"], "savollar": items,
                    "uz_nomi": k.natijalar.get("uz_nomi") or "O‘zbekiston", "izoh": matn("izoh_ball", rtil)}
        return run_db(run)

    def imtihon_reytingi(cur, row):
        """Shu davr va shu turdagi rasmiy imtihonlar orasida o'rin: sinfdoshlar, maktab, platforma (sinf bo'yicha)."""
        if not row["rasmiy"] or row["ball"] is None:
            return None
        out = {}
        sharts = {"sinf": ("maktab_id=%s AND sinf_nomi=%s", (row["maktab_id"], row["sinf_nomi"])) if row["maktab_id"] else None,
                  "maktab": ("maktab_id=%s AND sinf=%s", (row["maktab_id"], row["sinf"])) if row["maktab_id"] else None,
                  "platforma": ("sinf=%s", (row["sinf"],))}
        for nom, sh in sharts.items():
            if not sh:
                continue
            # REV318: reyting UMUMIY — uz, ru, en, de, es da yechganlar bitta ro'yxatda (savollar bir xil tadqiqotdan, bir xil ID);
            # har o'quvchi bir marta hisoblanadi (shu davrdagi eng yaxshi rasmiy bali)
            cur.execute(f"""SELECT COUNT(*) AS jami, COUNT(*) FILTER (WHERE ball > %s AND user_id <> %s) AS yuqori, ROUND(AVG(ball)) AS ortacha
                            FROM (SELECT user_id, MAX(ball) AS ball FROM xb_imtihon WHERE tur=%s AND toplam=%s AND davr=%s AND rasmiy
                                    AND topshirilgan IS NOT NULL AND {sh[0]} GROUP BY user_id) t""",
                        (row["ball"], row.get("user_id") or 0, row["tur"], row["toplam"], row["davr"], *sh[1]))
            r = cur.fetchone() or {}
            jami = int(r.get("jami") or 0)
            out[nom] = {"jami": jami, "orin": int(r.get("yuqori") or 0) + 1 if jami >= REYTING_MIN else None,
                        "ortacha": int(r["ortacha"]) if r.get("ortacha") is not None else None}
        return out

    # ─────────── reyting va natijalar ───────────
    @router.get("/api/xalqaro/reyting")
    def reyting(token: str = None, toplam: str = Query("", max_length=12), til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = KT(til)

        def run(conn, cur):
            user = user_info(cur, user_id)
            tk = toplam_of(toplam, user["sinf"], til)
            cur.execute("""SELECT id, user_id, til, tur, davr, ball, foiz, maktab_id, sinf_nomi, sinf, toplam, rasmiy, topshirilgan FROM xb_imtihon
                           WHERE user_id=%s AND rasmiy AND topshirilgan IS NOT NULL AND (toplam=%s OR tur='yillik') ORDER BY id""", (user_id, tk))   # REV318: barcha tillar
            mine = [dict(r) for r in cur.fetchall()]
            oxirgi = mine[-1] if mine else None
            reyt = imtihon_reytingi(cur, {**oxirgi, "toplam": oxirgi["toplam"]}) if oxirgi else None
            # sinfdoshlar ro'yxati (ismsiz, faqat o'rin va ball) — eng yaxshi rasmiy natija shu oy
            sinfdosh = []
            if user.get("maktab_id") and user.get("class"):
                cur.execute("""SELECT user_id, MAX(ball) AS ball FROM xb_imtihon WHERE maktab_id=%s AND sinf_nomi=%s AND toplam=%s
                               AND rasmiy AND topshirilgan IS NOT NULL AND boshlangan > NOW() - INTERVAL '45 days' GROUP BY user_id ORDER BY 2 DESC LIMIT 40""",
                            (user["maktab_id"], f"{user['class']}{user['harf']}", tk))   # REV318: barcha tillar
                sinfdosh = [{"orin": i + 1, "ball": int(r["ball"] or 0), "men": int(r["user_id"]) == user_id} for i, r in enumerate(cur.fetchall())]
            conn.commit()
            b = oxirgi["ball"] if oxirgi else None
            return {"toplam": tk, "tarix": [{"tur": r["tur"], "davr": r["davr"], "ball": r["ball"], "foiz": r["foiz"], "til": r["til"]} for r in mine[-30:]],
                    "oxirgi": {"ball": b, "daraja": daraja_of(b or 0, tk, til) if b else None}, "reyting": reyt, "til": til,
                    "uz_nomi": k.natijalar.get("uz_nomi") or "O‘zbekiston",
                    "sinfdoshlar": sinfdosh if len(sinfdosh) >= REYTING_MIN else [],
                    "dastur": "PISA" if pisami(tk) else "TIMSS", "solishtirish": solishtir(k, tk, b)}
        return run_db(run)

    @router.get("/api/xalqaro/natijalar")
    def natijalar(token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        uid_of(token, authorization)
        til = til_kodi(til)
        n = natijalar_tilda(K.ensure().base_dir, til)
        return {"jadvallar": n.get("jadvallar", {}), "ozbekiston": n.get("ozbekiston", {}), "manbalar": n.get("manbalar", {}),
                "darajalar": n.get("darajalar", {}), "uz_nomi": n.get("uz_nomi") or "O‘zbekiston", "til": til}

    # ─────────── o'quvchi: mening xatolarim ───────────
    def xato_royxati(cur, user_id, toplam="", limit=60, til="uz"):
        """O'quvchining hozir ham xato bo'lib turgan savollari: mashqdagi oxirgi javob xato bo'lganlar va
        oxirgi 60 kundagi imtihon xatolari (keyin mashqda to'g'rilanmaganlari). REV270: faqat shu tilda."""
        k = KT(til)
        cur.execute("""SELECT savol_id, urinish, togri, oxirgi_togri, oxirgi_v, oxirgi_javob, yangilangan FROM xb_bilim
                       WHERE user_id=%s AND til=%s""", (user_id, til))
        bilim = {r["savol_id"]: dict(r) for r in cur.fetchall()}
        out, seen = [], set()
        for sid, b in sorted(bilim.items(), key=lambda kv: kv[1]["yangilangan"], reverse=True):
            s = k.by_id.get(sid)
            if not s or b["oxirgi_togri"] or (toplam and s["toplam"] != toplam):
                continue
            vi = int(b.get("oxirgi_v") or 0) % len(s["variantlar"])
            out.append({**_variant_public(s, vi, javob_bilan=True, k=k), "berilgan": b.get("oxirgi_javob") or "", "manba": "mashq",
                        "urinish": b["urinish"], "togri_soni": b["togri"], "sana": b["yangilangan"].isoformat() if b.get("yangilangan") else ""})
            seen.add(sid)
        cur.execute("""SELECT id, tur, davr, savollar, javoblar, natija, topshirilgan FROM xb_imtihon
                       WHERE user_id=%s AND til=%s AND topshirilgan IS NOT NULL AND topshirilgan > NOW() - INTERVAL '60 days' ORDER BY id DESC LIMIT 12""", (user_id, til))
        for r in cur.fetchall():
            tl = (r["natija"] or {}).get("togri_list") or []
            for i, x in enumerate(r["savollar"] or []):
                if i < len(tl) and not tl[i] and x["id"] not in seen:
                    s = k.by_id.get(x["id"])
                    if not s or (toplam and s["toplam"] != toplam) or bilim.get(x["id"], {}).get("oxirgi_togri"):
                        continue
                    out.append({**_variant_public(s, x["v"] % len(s["variantlar"]), javob_bilan=True, k=k),
                                "berilgan": (r["javoblar"] or {}).get(str(i), ""), "manba": f"imtihon:{r['tur']}", "urinish": 1, "togri_soni": 0,
                                "sana": r["topshirilgan"].isoformat() if r.get("topshirilgan") else "", "imtihon_id": r["id"]})
                    seen.add(x["id"])
        return out[:limit]

    def mavzular_holati(cur, user_id, til="uz"):
        """O'quvchining har mavzu bo'yicha o'zlashtirishi (bitta so'rov)."""
        k = KT(til)
        cur.execute("SELECT savol_id, urinish, togri, oxirgi_togri, yangilangan FROM xb_bilim WHERE user_id=%s AND til=%s", (user_id, til))
        bilim = {r["savol_id"]: dict(r) for r in cur.fetchall()}
        out = []
        for kalit, t in k.mavzu_by_kalit.items():
            h = mavzu_holati(bilim, k.by_mavzu.get(kalit, []))
            if h["urinilgan"]:
                out.append({"kalit": kalit, "nom": t["nom"], "toplam": t["toplam"], **h})
        return sorted(out, key=lambda m: (m["foiz"], -m["urinilgan"]))

    @router.get("/api/xalqaro/xatolarim")
    def xatolarim(token: str = None, toplam: str = Query("", max_length=12), til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        til = til_kodi(til)

        def run(conn, cur):
            xs = xato_royxati(cur, user_id, toplam, til=til)
            mv = mavzular_holati(cur, user_id, til)
            conn.commit()
            return {"xatolar": xs, "zaif_mavzular": [m for m in mv if m["foiz"] < 60][:8], "til": til}
        return run_db(run)

    # ─────────── o'qituvchi va admin: sinf, xatolar, o'quvchi ───────────
    def admin_mi(cur, user_id):
        try:
            cur.execute("SAVEPOINT xb_adm")
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
            ok = cur.fetchone() is not None
            cur.execute("RELEASE SAVEPOINT xb_adm")
            return ok
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT xb_adm")
            return False

    def mening_sinflarim(cur, user_id):
        cur.execute("SELECT id FROM xb_sinf WHERE egasi=%s AND faol ORDER BY id", (user_id,))
        return [int(r["id"]) for r in cur.fetchall()]

    def kuzatuv_doirasi(cur, user_id, maktab_id=None, til="uz", xb_sinf=0):
        """Kim ko'ra oladi: admin — istalgan maktab (yoki butun platforma), o'qituvchi/direktor — faqat o'z maktabi.
        REV373: o'qituvchi o'zi ochgan sinf(lar)ni ham ko'radi (maktabsiz o'qituvchi — faqat o'z sinflari)."""
        user = user_info(cur, user_id)
        adm = admin_mi(cur, user_id)
        if xb_sinf:
            cur.execute("SELECT egasi FROM xb_sinf WHERE id=%s AND faol", (xb_sinf,))
            r = cur.fetchone()
            if not r or (int(r["egasi"]) != int(user_id) and not adm):
                raise HTTPException(403, matn("sinf_egasi_emas", til))
            return {"admin": False, "maktab_id": None, "xb_sinflar": [int(xb_sinf)], "user": user}
        if adm:
            return {"admin": True, "maktab_id": maktab_id or None, "user": user}
        if user["role"] in ("oqituvchi", "direktor", "zam_direktor") and user.get("maktab_id"):
            return {"admin": False, "maktab_id": user["maktab_id"], "user": user}
        meniki = mening_sinflarim(cur, user_id)
        if meniki or user["role"] in SINF_ROLLAR:
            return {"admin": False, "maktab_id": None, "xb_sinflar": meniki, "user": user}
        raise HTTPException(403, matn("faqat_oqituvchi", til))

    OQUVCHI_SHART = "COALESCE(u.role,'') NOT IN ('oqituvchi','ota-ona','direktor','zam_direktor','admin') AND u.class ~ '^\\s*\\d'"

    def oquvchilar(cur, doira, sinf, harf="", til="uz"):
        if doira.get("xb_sinflar") is not None:   # REV373: o'qituvchi ochgan sinf a'zolari
            if not doira["xb_sinflar"]:
                return []
            cur.execute("""SELECT DISTINCT ON (u.user_id) u.user_id, u.full_name, COALESCE(s.sinf::text, u.class) AS class, '' AS harf, u.maktab_id,
                                  s.nom AS sinf_nomi, a.qoshildi
                           FROM xb_sinf_azo a JOIN xb_sinf s ON s.id=a.sinf_id JOIN users u ON u.user_id=a.user_id
                           WHERE a.sinf_id=ANY(%s) ORDER BY u.user_id, a.qoshildi LIMIT 600""", (doira["xb_sinflar"],))
            out = [{**dict(r), "qoshildi": r["qoshildi"].isoformat() if r.get("qoshildi") else ""} for r in cur.fetchall()]
            return sorted(out, key=lambda r: (str(r.get("full_name") or "").lower()))   # REV377: jurnal tartibi — ism bo'yicha
        sharts, params = [OQUVCHI_SHART], []
        if doira["maktab_id"]:
            sharts.append("u.maktab_id=%s"); params.append(doira["maktab_id"])
        if sinf:
            sharts.append("regexp_replace(u.class, '[^0-9]', '', 'g')=%s"); params.append(str(int(sinf)))
        if harf:
            sharts.append("UPPER(COALESCE(u.class_letter,''))=UPPER(%s)"); params.append(harf)
        if not doira["maktab_id"]:   # admin, maktab tanlanmagan — faqat xalqaro bo'limda faol o'quvchilar
            sharts.append("EXISTS (SELECT 1 FROM xb_bilim b WHERE b.user_id=u.user_id AND b.til=%s)"); params.append(til)
        cur.execute(f"""SELECT u.user_id, u.full_name, u.class, COALESCE(u.class_letter,'') AS harf, u.maktab_id FROM users u
                        WHERE {' AND '.join(sharts)} ORDER BY u.class, harf, u.full_name LIMIT 600""", params)
        return [dict(r) for r in cur.fetchall()]

    @router.get("/api/xalqaro/sinf_natija")
    def sinf_natija(token: str = None, sinf: str = Query("", max_length=4), harf: str = Query("", max_length=3),
                    maktab_id: int = Query(0, ge=0), til: str = Query("uz", max_length=8), xb_sinf: int = Query(0, ge=0),
                    toplam: str = Query("", max_length=20), authorization: str = Header(None)):
        """O'qituvchi/admin: sinf o'quvchilari — faollik, o'zlashtirish, oxirgi rasmiy ball, zaif mavzu, xatolar soni.
        REV270: tanlangan til bo'yicha (har o'quvchi qaysi tillarda ishlayotgani ham ko'rsatiladi)."""
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = KT(til)

        def run(conn, cur):
            doira = kuzatuv_doirasi(cur, user_id, maktab_id or None, til, xb_sinf)
            ol = oquvchilar(cur, doira, sinf, harf, til)
            ids = [o["user_id"] for o in ol]
            stat, xato, ball, mavzu = {}, {}, {}, {}
            if ids:
                cur.execute("""SELECT user_id, COUNT(*) AS urinish, COUNT(*) FILTER (WHERE oxirgi_togri) AS ozlashtirgan,
                                      COUNT(*) FILTER (WHERE NOT oxirgi_togri) AS xato, MAX(yangilangan) AS oxirgi,
                                      COUNT(*) FILTER (WHERE yangilangan > NOW() - INTERVAL '7 days') AS hafta
                               FROM xb_bilim WHERE user_id=ANY(%s) AND til=%s AND (%s='' OR toplam=%s) GROUP BY user_id""", (ids, til, toplam, toplam))
                stat = {r["user_id"]: dict(r) for r in cur.fetchall()}
                cur.execute("""SELECT DISTINCT ON (user_id) user_id, ball, foiz, tur, davr, toplam FROM xb_imtihon
                               WHERE user_id=ANY(%s) AND til=%s AND (%s='' OR toplam=%s) AND rasmiy AND topshirilgan IS NOT NULL ORDER BY user_id, id DESC""", (ids, til, toplam, toplam))
                ball = {r["user_id"]: dict(r) for r in cur.fetchall()}
                cur.execute("""SELECT user_id, mavzu, COUNT(*) FILTER (WHERE NOT oxirgi_togri) AS x, COUNT(*) AS n
                               FROM xb_bilim WHERE user_id=ANY(%s) AND til=%s AND (%s='' OR toplam=%s) GROUP BY user_id, mavzu""", (ids, til, toplam, toplam))
                for r in cur.fetchall():
                    if int(r["x"]) and (r["user_id"] not in mavzu or int(r["x"]) > mavzu[r["user_id"]][1]):
                        mavzu[r["user_id"]] = (r["mavzu"], int(r["x"]))
                cur.execute("SELECT user_id, COUNT(*) AS n FROM xb_imtihon WHERE user_id=ANY(%s) AND til=%s AND (%s='' OR toplam=%s) AND rasmiy AND topshirilgan IS NOT NULL AND davr=%s GROUP BY user_id",
                            (ids, til, toplam, toplam, davr_kaliti("haftalik")))
                haftalik = {r["user_id"] for r in cur.fetchall()}
                cur.execute("SELECT user_id, COUNT(*) FILTER (WHERE tugadi) AS n, COUNT(*) AS ochgan FROM xb_dars WHERE user_id=ANY(%s) AND til=%s GROUP BY user_id", (ids, til))
                darslar = {r["user_id"]: (int(r["n"]), int(r["ochgan"])) for r in cur.fetchall()}   # REV376
                cur.execute("SELECT user_id, til, COUNT(*) AS n FROM xb_bilim WHERE user_id=ANY(%s) GROUP BY user_id, til", (ids,))
                tillar = {}
                for r in cur.fetchall():
                    tillar.setdefault(r["user_id"], {})[r["til"]] = int(r["n"])
            else:
                haftalik, tillar, darslar = set(), {}, {}
            now = datetime.now(TZ)
            rows = []
            for o in ol:
                s = stat.get(o["user_id"], {})
                b = ball.get(o["user_id"])
                kun = (now - s["oxirgi"]).days if s.get("oxirgi") else None
                zm = mavzu.get(o["user_id"])
                holat = "boshlamagan" if kun is None else "sust" if kun > 7 or int(s.get("hafta") or 0) < 10 else "faol"
                rows.append({**o, "urinish": int(s.get("urinish") or 0), "ozlashtirgan": int(s.get("ozlashtirgan") or 0),
                             "xato": int(s.get("xato") or 0), "hafta": int(s.get("hafta") or 0), "kun_oldin": kun, "holat": holat,
                             "haftalik_topshirdi": o["user_id"] in haftalik,
                             "tillar": tillar.get(o["user_id"], {}),
                             "darslar": darslar.get(o["user_id"], (0, 0))[0], "darslar_ochgan": darslar.get(o["user_id"], (0, 0))[1],
                             "ball": b["ball"] if b else None, "daraja": daraja_of(b["ball"], b.get("toplam"), til)["nom"] if b and b.get("ball") else None,
                             "foiz": round(100 * int(s.get("ozlashtirgan") or 0) / int(s.get("urinish"))) if int(s.get("urinish") or 0) else None,   # REV408
                             "zaif_mavzu": k.mavzu_by_kalit.get(zm[0], {}).get("nom") if zm else None})
            conn.commit()
            balllar = [r["ball"] for r in rows if r["ball"]]
            return {"admin": doira["admin"], "maktab_id": doira["maktab_id"], "oquvchilar": rows, "til": til,
                    "jamlama": {"jami": len(rows), "faol": sum(r["holat"] == "faol" for r in rows), "sust": sum(r["holat"] == "sust" for r in rows),
                                "boshlamagan": sum(r["holat"] == "boshlamagan" for r in rows), "haftalik": sum(r["haftalik_topshirdi"] for r in rows),
                                "ortacha_ball": round(sum(balllar) / len(balllar)) if balllar else None,
                                "ortacha_foiz": round(sum(r["foiz"] for r in rows if r["foiz"] is not None) / max(1, sum(1 for r in rows if r["foiz"] is not None))) if any(r["foiz"] is not None for r in rows) else None}}
        return run_db(run)

    @router.get("/api/xalqaro/sinf_xatolar")
    def sinf_xatolar(token: str = None, sinf: str = Query("", max_length=4), harf: str = Query("", max_length=3),
                     maktab_id: int = Query(0, ge=0), til: str = Query("uz", max_length=8), xb_sinf: int = Query(0, ge=0),
                     toplam: str = Query("", max_length=20), authorization: str = Header(None)):
        """O'qituvchi/admin: sinf bo'yicha eng ko'p xato qilingan savollar va mavzular — dars qayerga qaratilishi kerak."""
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = KT(til)

        def run(conn, cur):
            doira = kuzatuv_doirasi(cur, user_id, maktab_id or None, til, xb_sinf)
            ids = [o["user_id"] for o in oquvchilar(cur, doira, sinf, harf, til)]
            savollar, mavzular = [], []
            if ids:
                # variant bo'yicha guruhlanadi: «ko'p berilgan javob» aynan shu variantning harfi/qiymati bo'lsin
                cur.execute("""SELECT savol_id, oxirgi_v, COUNT(*) AS urindi, COUNT(*) FILTER (WHERE NOT oxirgi_togri) AS xato,
                                      mode() WITHIN GROUP (ORDER BY oxirgi_javob) FILTER (WHERE NOT oxirgi_togri) AS kop_javob
                               FROM xb_bilim WHERE user_id=ANY(%s) AND til=%s AND (%s='' OR toplam=%s) GROUP BY savol_id, oxirgi_v HAVING COUNT(*) FILTER (WHERE NOT oxirgi_togri) > 0
                               ORDER BY 4 DESC, 3 DESC LIMIT 25""", (ids, til, toplam, toplam))
                for r in cur.fetchall():
                    s = k.by_id.get(r["savol_id"])
                    if not s:
                        continue
                    vi = int(r["oxirgi_v"] or 0) % len(s["variantlar"])
                    p = _variant_public(s, vi, javob_bilan=True, k=k)
                    kop = _t(r["kop_javob"])
                    izoh = ""
                    if s["variantlar"][vi]["turi"] == "tanlov" and harf_indeksi(kop) is not None:
                        izoh = (s["variantlar"][vi].get("xatolar") or {}).get(str(harf_indeksi(kop)), "")
                    savollar.append({**p, "urindi": int(r["urindi"]), "xato": int(r["xato"]),
                                     "xato_foiz": round(100 * int(r["xato"]) / max(1, int(r["urindi"]))), "kop_javob": kop, "kop_izoh": izoh})
                cur.execute("""SELECT mavzu, COUNT(DISTINCT user_id) AS oquvchi, COUNT(*) AS urindi, COUNT(*) FILTER (WHERE oxirgi_togri) AS togri
                               FROM xb_bilim WHERE user_id=ANY(%s) AND til=%s AND (%s='' OR toplam=%s) GROUP BY mavzu""", (ids, til, toplam, toplam))
                for r in cur.fetchall():
                    t = k.mavzu_by_kalit.get(r["mavzu"])
                    if t:
                        f = round(100 * int(r["togri"]) / max(1, int(r["urindi"])))
                        sv = k.by_mavzu.get(r["mavzu"], [])
                        dunyo = [x["xalqaro_ortacha"] for x in sv if x.get("xalqaro_ortacha") is not None]
                        mavzular.append({"kalit": r["mavzu"], "nom": t["nom"], "toplam": t["toplam"], "oquvchi": int(r["oquvchi"]), "urindi": int(r["urindi"]),
                                         "foiz": f, "dunyo": round(sum(dunyo) / len(dunyo)) if dunyo else None, "dars_kodi": "XB-" + r["mavzu"]})
            conn.commit()
            return {"savollar": savollar, "mavzular": sorted(mavzular, key=lambda m: m["foiz"]), "til": til}
        return run_db(run)

    @router.get("/api/xalqaro/oquvchi/{oquvchi_id}")
    def oquvchi_tafsilot(oquvchi_id: int, token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """O'qituvchi/admin: bitta o'quvchi — mavzular bo'yicha o'zlashtirish, xatolari (bergan javobi bilan), imtihonlar tarixi (tanlangan tilda)."""
        user_id = uid_of(token, authorization)
        til = til_kodi(til)

        def run(conn, cur):
            doira = kuzatuv_doirasi(cur, user_id, None, til)
            o = user_info(cur, oquvchi_id)
            if not doira["admin"] and not (doira["maktab_id"] and o.get("maktab_id") == doira["maktab_id"]):
                cur.execute("""SELECT 1 FROM xb_sinf_azo a JOIN xb_sinf s ON s.id=a.sinf_id WHERE a.user_id=%s AND s.egasi=%s AND s.faol LIMIT 1""", (oquvchi_id, user_id))
                if not cur.fetchone():   # REV373: o'z sinfining a'zosi emas
                    raise HTTPException(403, matn("maktab_emas", til))
            cur.execute("""SELECT id, tur, toplam, davr, rasmiy, foiz, ball, topshirilgan, chiqishlar FROM xb_imtihon
                           WHERE user_id=%s AND til=%s AND topshirilgan IS NOT NULL ORDER BY id DESC LIMIT 10""", (oquvchi_id, til))
            imt = [{**dict(r), "nom": imtihon_nomi(r["tur"], til), "daraja": daraja_of(r["ball"] or 0, r["toplam"], til)["nom"] if r["ball"] else None,
                    "topshirilgan": r["topshirilgan"].isoformat() if r.get("topshirilgan") else ""} for r in cur.fetchall()]
            out = {"oquvchi": {"user_id": oquvchi_id, "ism": o.get("ism"), "sinf": f"{o.get('class')}{o.get('harf')}"}, "til": til,
                   "mavzular": mavzular_holati(cur, oquvchi_id, til), "xatolar": xato_royxati(cur, oquvchi_id, limit=40, til=til), "imtihonlar": imt}
            cur.execute("SELECT til, COUNT(*) AS n FROM xb_bilim WHERE user_id=%s GROUP BY til", (oquvchi_id,))
            out["tillar"] = {r["til"]: int(r["n"]) for r in cur.fetchall()}
            # REV376: o'qigan darslari va eng ko'p ishlagan mavzulari
            kk = KT(til)
            cur.execute("SELECT mavzu, ochildi, tugadi, oxirgi FROM xb_dars WHERE user_id=%s AND til=%s ORDER BY oxirgi DESC LIMIT 60", (oquvchi_id, til))
            out["darslar"] = [{"kalit": r["mavzu"], "nom": kk.mavzu_by_kalit.get(r["mavzu"], {}).get("nom", r["mavzu"]), "toplam": kk.mavzu_by_kalit.get(r["mavzu"], {}).get("toplam", ""),
                               "ochildi": int(r["ochildi"]), "tugadi": bool(r["tugadi"]), "oxirgi": r["oxirgi"].isoformat()} for r in cur.fetchall()]
            cur.execute("""SELECT mavzu, SUM(urinish) AS urinish, COUNT(*) AS savol, COUNT(*) FILTER (WHERE oxirgi_togri) AS togri, MAX(yangilangan) AS oxirgi
                           FROM xb_bilim WHERE user_id=%s AND til=%s GROUP BY mavzu ORDER BY 2 DESC LIMIT 10""", (oquvchi_id, til))
            out["kop_ishlagan"] = [{"kalit": r["mavzu"], "nom": kk.mavzu_by_kalit.get(r["mavzu"], {}).get("nom", r["mavzu"]), "toplam": kk.mavzu_by_kalit.get(r["mavzu"], {}).get("toplam", ""),
                                    "urinish": int(r["urinish"] or 0), "savol": int(r["savol"]), "togri": int(r["togri"]),
                                    "foiz": round(100 * int(r["togri"]) / max(1, int(r["savol"]))), "oxirgi": r["oxirgi"].isoformat() if r["oxirgi"] else ""} for r in cur.fetchall()]
            cur.execute("SELECT COUNT(*) AS n FROM xb_takror WHERE user_id=%s AND til=%s", (oquvchi_id, til))
            out["takror_navbat"] = int((cur.fetchone() or {}).get("n") or 0)
            conn.commit()
            return out
        return run_db(run)

    # ─────────── REV373: o'qituvchining sinflari: ochish, taklif kodi/havola, parol, a'zolar ───────────
    class SinfYarat(BaseModel):
        token: Optional[str] = None
        til: Optional[str] = "uz"
        nom: str = Field(default="", max_length=80)
        sinf: int = 0
        parol: str = Field(default="", max_length=40)
        toplam: str = Field(default="", max_length=20)   # REV374
        auditoriya: str = Field(default="maktab", max_length=12)   # REV401
        kurs: str = Field(default="", max_length=20)   # REV408

    class SinfOzgar(BaseModel):
        token: Optional[str] = None
        til: Optional[str] = "uz"
        nom: Optional[str] = Field(default=None, max_length=80)
        parol: Optional[str] = Field(default=None, max_length=40)   # "" — parolni olib tashlash
        yangi_kod: bool = False
        ochirish: bool = False
        chiqar: int = 0   # shu o'quvchini sinfdan chiqarish
        toplam: Optional[str] = Field(default=None, max_length=20)   # REV374
        auditoriya: Optional[str] = Field(default=None, max_length=12)   # REV401

    class SinfQoshil(BaseModel):
        token: Optional[str] = None
        til: Optional[str] = "uz"
        kod: str = Field(default="", max_length=20)
        sinf_id: int = 0
        parol: str = Field(default="", max_length=40)

    _urinish = {}
    _urinish_qulf = threading.Lock()

    def _urinish_ok(uid):
        now = datetime.now(timezone.utc).timestamp()
        with _urinish_qulf:
            q = [t for t in _urinish.get(uid, []) if now - t < 600]
            _urinish[uid] = q
            return len(q) < 10

    def _urinish_yoz(uid):
        with _urinish_qulf:
            _urinish.setdefault(uid, []).append(datetime.now(timezone.utc).timestamp())

    def _sinf_korinish(r, azo=None, egasi_ism=""):
        d = {"id": int(r["id"]), "nom": r["nom"], "sinf": int(r["sinf"]), "parolli": bool(r.get("parol_hash")),
             "toplam": sinf_toplami(r.get("toplam"), r["sinf"]), "auditoriya": auditoriya_norm(r.get("auditoriya")), "kurs": r.get("kurs") or ""}
        if azo is not None:
            d.update(kod=r["kod"], azolar=azo)
        if egasi_ism:
            d["oqituvchi"] = egasi_ism
        return d

    def _ism(cur, uid):
        cur.execute("SELECT full_name FROM users WHERE user_id=%s", (uid,))
        r = cur.fetchone()
        return _t(r["full_name"]) if r else ""

    def _ochishi_mumkin(cur, user_id):
        u = user_info(cur, user_id)
        return admin_mi(cur, user_id) or u["role"] in SINF_ROLLAR or bool(mening_sinflarim(cur, user_id))

    class DarsKordi(BaseModel):
        token: Optional[str] = None
        til: Optional[str] = "uz"
        mavzu: str = Field(default="", max_length=40)
        tugadi: bool = False

    @router.post("/api/xalqaro/dars_kordi")
    def dars_kordi(body: DarsKordi, authorization: str = Header(None)):
        """REV376: o'quvchi mavzu darsini ochdi (tugadi=True — darsni oxirigacha o'tib, mashqqa o'tdi)."""
        user_id = uid_of(body.token, authorization)
        til = til_kodi(body.til)
        mavzu = re.sub(r"[^A-Za-z0-9_\-]", "", body.mavzu or "")[:40]
        if not mavzu or mavzu not in KT(til).mavzu_by_kalit:
            return {"ok": False}

        def run(conn, cur):
            if body.tugadi:
                cur.execute("""INSERT INTO xb_dars(user_id, til, mavzu, ochildi, tugadi) VALUES (%s,%s,%s,1,TRUE)
                               ON CONFLICT (user_id, til, mavzu) DO UPDATE SET tugadi=TRUE, oxirgi=NOW()""", (user_id, til, mavzu))
            else:
                cur.execute("""INSERT INTO xb_dars(user_id, til, mavzu, ochildi) VALUES (%s,%s,%s,1)
                               ON CONFLICT (user_id, til, mavzu) DO UPDATE SET ochildi=xb_dars.ochildi+1, oxirgi=NOW()""", (user_id, til, mavzu))
            conn.commit()
            return {"ok": True}
        return run_db(run)

    @router.get("/api/xalqaro/sinflar")
    def sinflar(token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """O'qituvchi — o'zi ochgan sinflar (kod, a'zolar soni); o'quvchi — qo'shilgan sinflari."""
        user_id = uid_of(token, authorization)

        def run(conn, cur):
            cur.execute("""SELECT s.*, (SELECT COUNT(*) FROM xb_sinf_azo a WHERE a.sinf_id=s.id) AS n FROM xb_sinf s
                           WHERE s.egasi=%s AND s.faol ORDER BY s.sinf, s.nom""", (user_id,))
            meniki = [_sinf_korinish(r, int(r["n"])) for r in cur.fetchall()]
            cur.execute("""SELECT s.*, COALESCE(u.full_name,'') AS ustoz FROM xb_sinf_azo a JOIN xb_sinf s ON s.id=a.sinf_id
                           LEFT JOIN users u ON u.user_id=s.egasi WHERE a.user_id=%s AND s.faol ORDER BY a.qoshildi DESC""", (user_id,))
            azolik = [_sinf_korinish(r, egasi_ism=_t(r["ustoz"])) for r in cur.fetchall()]
            ok = _ochishi_mumkin(cur, user_id)
            conn.commit()
            return {"meniki": meniki, "azolik": azolik, "ochishi_mumkin": ok}
        return run_db(run)

    @router.post("/api/xalqaro/sinflar")
    def sinf_yarat(body: SinfYarat, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        til = til_kodi(body.til)
        d, xato = sinf_malumot_tekshir(body.nom, body.sinf, body.parol, body.auditoriya)
        if xato:
            raise HTTPException(400, matn(xato, til))
        if body.toplam and body.toplam not in XB_TOPLAMLAR:
            raise HTTPException(400, matn("sinf_toplam", til))
        tp = sinf_toplami(body.toplam, d["sinf"])

        def run(conn, cur):
            if not _ochishi_mumkin(cur, user_id):
                raise HTTPException(403, matn("sinf_ochish_yoq", til))
            cur.execute("SELECT COUNT(*) AS n FROM xb_sinf WHERE egasi=%s AND faol", (user_id,))
            if int(cur.fetchone()["n"]) >= 30:
                raise HTTPException(400, "Ko‘pi bilan 30 ta sinf")
            for _ in range(8):
                kod = sinf_kodi_yasa()
                cur.execute("SELECT 1 FROM xb_sinf WHERE kod=%s", (kod,))
                if not cur.fetchone():
                    break
            cur.execute("""INSERT INTO xb_sinf(egasi, nom, sinf, kod, parol_hash, toplam, auditoriya, kurs) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                        (user_id, d["nom"], d["sinf"], kod, parol_hash(body.parol, kod), tp, auditoriya_norm(body.auditoriya),
                         body.kurs if body.kurs in KURSLAR else ""))
            r = cur.fetchone()
            conn.commit()
            return {"sinf": _sinf_korinish(r, 0)}
        return run_db(run)

    @router.post("/api/xalqaro/sinflar/{sinf_id}")
    def sinf_ozgar(sinf_id: int, body: SinfOzgar, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        til = til_kodi(body.til)

        def run(conn, cur):
            cur.execute("SELECT * FROM xb_sinf WHERE id=%s AND faol FOR UPDATE", (sinf_id,))
            r = cur.fetchone()
            if not r or (int(r["egasi"]) != int(user_id) and not admin_mi(cur, user_id)):
                raise HTTPException(403, matn("sinf_egasi_emas", til))
            if body.ochirish:
                cur.execute("UPDATE xb_sinf SET faol=FALSE WHERE id=%s", (sinf_id,))
                cur.execute("DELETE FROM xb_sinf_azo WHERE sinf_id=%s", (sinf_id,))
                conn.commit()
                return {"ok": True, "ochirildi": True}
            if body.chiqar:
                cur.execute("DELETE FROM xb_sinf_azo WHERE sinf_id=%s AND user_id=%s", (sinf_id, body.chiqar))
            kod = r["kod"]
            if body.yangi_kod:
                if r["parol_hash"] and body.parol is None:   # parol kodga bog'langan — kod almashsa, parolni qayta berish kerak
                    raise HTTPException(400, matn("sinf_parol", til))
                kod = sinf_kodi_yasa()
                cur.execute("UPDATE xb_sinf SET kod=%s WHERE id=%s", (kod, sinf_id))
            if body.auditoriya is not None:
                cur.execute("UPDATE xb_sinf SET auditoriya=%s WHERE id=%s", (auditoriya_norm(body.auditoriya), sinf_id))
            if body.toplam is not None:
                if body.toplam not in XB_TOPLAMLAR:
                    raise HTTPException(400, matn("sinf_toplam", til))
                cur.execute("UPDATE xb_sinf SET toplam=%s WHERE id=%s", (body.toplam, sinf_id))
            if body.nom is not None:
                d, xato = sinf_malumot_tekshir(body.nom, r["sinf"], "", r.get("auditoriya") or "maktab")
                if xato:
                    raise HTTPException(400, matn(xato, til))
                cur.execute("UPDATE xb_sinf SET nom=%s WHERE id=%s", (d["nom"], sinf_id))
            if body.parol is not None:
                if body.parol and not 3 <= len(body.parol.strip()) <= 32:
                    raise HTTPException(400, matn("sinf_parol", til))
                cur.execute("UPDATE xb_sinf SET parol_hash=%s WHERE id=%s", (parol_hash(body.parol, kod), sinf_id))
            cur.execute("""SELECT s.*, (SELECT COUNT(*) FROM xb_sinf_azo a WHERE a.sinf_id=s.id) AS n FROM xb_sinf s WHERE s.id=%s""", (sinf_id,))
            r2 = cur.fetchone()
            cur.execute("""SELECT u.user_id, u.full_name, a.qoshildi FROM xb_sinf_azo a JOIN users u ON u.user_id=a.user_id
                           WHERE a.sinf_id=%s ORDER BY u.full_name""", (sinf_id,))
            azolar = [{"user_id": int(x["user_id"]), "ism": _t(x["full_name"]), "qoshildi": x["qoshildi"].isoformat()} for x in cur.fetchall()]
            conn.commit()
            return {"sinf": _sinf_korinish(r2, int(r2["n"])), "azolar": azolar}
        return run_db(run)

    class TopshiriqYarat(BaseModel):
        token: Optional[str] = None
        til: Optional[str] = "uz"
        nom: str = Field(default="", max_length=80)
        mavzu: str = Field(default="", max_length=20)   # bo'sh — sinf fanidan aralash
        soni: int = 10
        muddat: Optional[str] = Field(default=None, max_length=10)

    class TopshiriqNatija(BaseModel):
        token: Optional[str] = None
        togri: int = 0
        jami: int = 0

    def _sinf_egasi(cur, sinf_id, user_id, til):
        cur.execute("SELECT * FROM xb_sinf WHERE id=%s AND faol", (sinf_id,))
        r = cur.fetchone()
        if not r or (int(r["egasi"]) != int(user_id) and not admin_mi(cur, user_id)):
            raise HTTPException(403, matn("sinf_egasi_emas", til))
        return r

    @router.post("/api/xalqaro/sinflar/{sinf_id}/topshiriq")
    def topshiriq_yarat(sinf_id: int, body: TopshiriqYarat, authorization: str = Header(None)):
        """REV401: sinfga topshiriq — savollar bir marta tanlanib saqlanadi (hamma o'quvchida bir xil)."""
        user_id = uid_of(body.token, authorization)
        til = til_kodi(body.til)
        k = KT(til)
        soni = max(3, min(30, int(body.soni or 10)))

        def run(conn, cur):
            r = _sinf_egasi(cur, sinf_id, user_id, til)
            tp = sinf_toplami(r.get("toplam"), r["sinf"])
            if body.mavzu:
                if body.mavzu not in k.mavzu_by_kalit:
                    raise HTTPException(400, matn("savol_yoq", til))
                pool = list(k.by_mavzu.get(body.mavzu, []))
            else:
                pool = [x for x in k.savollar if x["toplam"] == tp]
            if not pool:
                raise HTTPException(400, matn("savol_yoq", til))
            rng = random.Random()
            tanl = sorted(rng.sample(pool, min(soni, len(pool))), key=lambda x: (savol_qiyinligi(x), x["id"]))
            nom = re.sub(r"\s+", " ", body.nom or "").strip()[:80] or (k.mavzu_by_kalit.get(body.mavzu, {}).get("nom") if body.mavzu else "Aralash topshiriq")
            muddat = body.muddat if body.muddat and re.fullmatch(r"\d{4}-\d{2}-\d{2}", body.muddat) else None
            for _ in range(8):
                kod = sinf_kodi_yasa(7)
                cur.execute("SELECT 1 FROM xb_topshiriq WHERE kod=%s", (kod,))
                if not cur.fetchone():
                    break
            cur.execute("""INSERT INTO xb_topshiriq(sinf_id, nom, mavzu, savol_idlar, muddat, kod) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id, kod""",
                        (sinf_id, nom, body.mavzu or "", json.dumps([x["id"] for x in tanl]), muddat, kod))
            t = cur.fetchone()
            conn.commit()
            return {"ok": True, "id": int(t["id"]), "kod": t["kod"]}
        return run_db(run)

    @router.get("/api/xalqaro/sinflar/{sinf_id}/topshiriqlar")
    def topshiriqlar(sinf_id: int, token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """REV401: o'qituvchi — sinf topshiriqlari va har biri bo'yicha kim nechta to'g'ri yechgani."""
        user_id = uid_of(token, authorization)
        til = til_kodi(til)

        def run(conn, cur):
            _sinf_egasi(cur, sinf_id, user_id, til)
            cur.execute("""SELECT t.*, (SELECT COUNT(*) FROM xb_sinf_azo a WHERE a.sinf_id=t.sinf_id) AS azolar FROM xb_topshiriq t
                           WHERE t.sinf_id=%s AND t.faol ORDER BY t.id DESC LIMIT 50""", (sinf_id,))
            out = []
            for t in cur.fetchall():
                cur.execute("""SELECT n.user_id, COALESCE(u.full_name,'') AS ism, n.togri, n.jami, n.eng_yaxshi, n.urinish, n.vaqt
                               FROM xb_topshiriq_natija n LEFT JOIN users u ON u.user_id=n.user_id WHERE n.topshiriq_id=%s ORDER BY u.full_name""", (t["id"],))
                nat = [{"user_id": int(x["user_id"]), "ism": _t(x["ism"]), "togri": int(x["togri"]), "jami": int(x["jami"]), "eng_yaxshi": int(x["eng_yaxshi"]),
                        "foiz": round(100 * int(x["eng_yaxshi"]) / max(1, int(x["jami"]))), "urinish": int(x["urinish"]), "vaqt": x["vaqt"].isoformat()} for x in cur.fetchall()]
                ids = t["savol_idlar"] if isinstance(t["savol_idlar"], list) else json.loads(t["savol_idlar"])
                out.append({"id": int(t["id"]), "kod": t["kod"], "nom": t["nom"], "mavzu": t["mavzu"], "soni": len(ids), "muddat": t["muddat"].isoformat() if t["muddat"] else None,
                            "azolar": int(t["azolar"]), "topshirdi": len(nat), "ortacha": round(sum(x["foiz"] for x in nat) / len(nat)) if nat else None, "natijalar": nat})
            conn.commit()
            return {"topshiriqlar": out}
        return run_db(run)

    def _topshiriq_ol(cur, kod, user_id, til):
        cur.execute("""SELECT t.*, s.egasi, s.nom AS sinf_nomi FROM xb_topshiriq t JOIN xb_sinf s ON s.id=t.sinf_id WHERE t.kod=%s AND t.faol AND s.faol""", (kod_norm(kod),))
        t = cur.fetchone()
        if not t:
            raise HTTPException(404, matn("sinf_yoq", til))
        cur.execute("SELECT 1 FROM xb_sinf_azo WHERE sinf_id=%s AND user_id=%s", (t["sinf_id"], user_id))
        if not cur.fetchone() and int(t["egasi"]) != int(user_id):
            cur.execute("SELECT parol_hash FROM xb_sinf WHERE id=%s", (t["sinf_id"],))
            sr = cur.fetchone()
            if sr and not sr.get("parol_hash"):   # REV408: o'qituvchi yuborgan havola — taklifnoma
                cur.execute("INSERT INTO xb_sinf_azo(sinf_id, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (t["sinf_id"], user_id))
            else:
                raise HTTPException(403, matn("topshiriq_azo_emas", til, s=t["sinf_nomi"]))
        return t

    @router.get("/api/xalqaro/topshiriq/{kod}")
    def topshiriq_ol(kod: str, token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """REV401: o'quvchi — topshiriq savollari (sinf a'zosi bo'lishi kerak) va oldingi natijasi."""
        user_id = uid_of(token, authorization)
        til = til_kodi(til)
        k = KT(til)

        def run(conn, cur):
            t = _topshiriq_ol(cur, kod, user_id, til)
            ids = t["savol_idlar"] if isinstance(t["savol_idlar"], list) else json.loads(t["savol_idlar"])
            savollar = [_variant_public(k.by_id[i], 0, javob_bilan=True, k=k) for i in ids if i in k.by_id]
            cur.execute("SELECT togri, jami, eng_yaxshi, urinish FROM xb_topshiriq_natija WHERE topshiriq_id=%s AND user_id=%s", (t["id"], user_id))
            n = cur.fetchone()
            conn.commit()
            return {"nom": t["nom"], "sinf": t["sinf_nomi"], "kod": t["kod"], "muddat": t["muddat"].isoformat() if t["muddat"] else None,
                    "savollar": savollar, "natija": dict(n) if n else None, "til": til}
        return run_db(run)

    @router.post("/api/xalqaro/topshiriq/{kod}/natija")
    def topshiriq_natija(kod: str, body: TopshiriqNatija, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)
        til = til_kodi(til)

        def run(conn, cur):
            t = _topshiriq_ol(cur, kod, user_id, til)
            ids = t["savol_idlar"] if isinstance(t["savol_idlar"], list) else json.loads(t["savol_idlar"])
            jami = len(ids); togri = max(0, min(jami, int(body.togri)))
            cur.execute("""INSERT INTO xb_topshiriq_natija(topshiriq_id, user_id, togri, jami, eng_yaxshi) VALUES (%s,%s,%s,%s,%s)
                           ON CONFLICT (topshiriq_id, user_id) DO UPDATE SET togri=EXCLUDED.togri, jami=EXCLUDED.jami, urinish=xb_topshiriq_natija.urinish+1,
                           eng_yaxshi=GREATEST(xb_topshiriq_natija.eng_yaxshi, EXCLUDED.togri), vaqt=NOW()""", (t["id"], user_id, togri, jami, togri))
            conn.commit()
            return {"ok": True}
        return run_db(run)

    class TopshiriqJonli(BaseModel):
        token: Optional[str] = None
        joriy: int = 0
        javob: int = 0
        togri: int = 0
        holat: str = Field(default="faol", max_length=10)

    @router.post("/api/xalqaro/topshiriq/{kod}/jonli")
    def topshiriq_jonli_yoz(kod: str, body: TopshiriqJonli, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """REV404: o'quvchi ilovasi har ~4 soniyada (va javob berganda, ilovadan chiqqanda) holatini yuboradi."""
        user_id = uid_of(body.token, authorization)
        til = til_kodi(til)
        holat = body.holat if body.holat in ("faol", "chiqdi", "tugatdi") else "faol"

        def run(conn, cur):
            t = _topshiriq_ol(cur, kod, user_id, til)
            ids = t["savol_idlar"] if isinstance(t["savol_idlar"], list) else json.loads(t["savol_idlar"])
            jami = len(ids)
            cur.execute("""INSERT INTO xb_topshiriq_jonli(topshiriq_id, user_id, joriy, javob, togri, holat) VALUES (%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (topshiriq_id, user_id) DO UPDATE SET joriy=EXCLUDED.joriy, javob=EXCLUDED.javob, togri=EXCLUDED.togri,
                           holat=EXCLUDED.holat, yangilandi=NOW()""",
                        (t["id"], user_id, max(0, min(jami, int(body.joriy))), max(0, min(jami, int(body.javob))), max(0, min(jami, int(body.togri))), holat))
            conn.commit()
            return {"ok": True}
        return run_db(run)

    @router.get("/api/xalqaro/sinflar/{sinf_id}/topshiriq/{tid}/jonli")
    def topshiriq_jonli(sinf_id: int, tid: int, token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """REV404: o'qituvchi — sinfning har bir a'zosi shu topshiriqda hozir nima qilyapti (topshirmagan bo'lsa ham)."""
        user_id = uid_of(token, authorization)
        til = til_kodi(til)

        def run(conn, cur):
            _sinf_egasi(cur, sinf_id, user_id, til)
            cur.execute("SELECT savol_idlar FROM xb_topshiriq WHERE id=%s AND sinf_id=%s", (tid, sinf_id))
            t = cur.fetchone()
            if not t:
                raise HTTPException(404, matn("sinf_yoq", til))
            ids = t["savol_idlar"] if isinstance(t["savol_idlar"], list) else json.loads(t["savol_idlar"])
            cur.execute("""SELECT u.user_id, COALESCE(u.full_name,'') AS ism, j.joriy, j.javob, j.togri, j.holat,
                                  EXTRACT(EPOCH FROM (NOW()-j.yangilandi)) AS oldin, EXTRACT(EPOCH FROM (j.yangilandi-j.boshladi)) AS davom,
                                  n.eng_yaxshi, n.urinish
                           FROM xb_sinf_azo a JOIN users u ON u.user_id=a.user_id
                           LEFT JOIN xb_topshiriq_jonli j ON j.topshiriq_id=%s AND j.user_id=a.user_id
                           LEFT JOIN xb_topshiriq_natija n ON n.topshiriq_id=%s AND n.user_id=a.user_id
                           WHERE a.sinf_id=%s ORDER BY u.full_name""", (tid, tid, sinf_id))
            out = []
            for r in cur.fetchall():
                oldin = float(r["oldin"]) if r["oldin"] is not None else None
                if r["holat"] is None and r["eng_yaxshi"] is None:
                    h = "boshlamagan"
                elif r["holat"] == "tugatdi" or (r["holat"] is None and r["eng_yaxshi"] is not None):
                    h = "tugatdi"
                elif r["holat"] == "chiqdi" or (oldin is not None and oldin > 15):
                    h = "chiqdi"
                else:
                    h = "yechmoqda"
                out.append({"user_id": int(r["user_id"]), "ism": _t(r["ism"]), "holat": h, "joriy": int(r["joriy"] or 0), "javob": int(r["javob"] or 0),
                            "togri": int(r["togri"] or 0), "jami": len(ids), "oldin": round(oldin) if oldin is not None else None,
                            "davom": round(float(r["davom"])) if r["davom"] is not None else None,
                            "natija": int(r["eng_yaxshi"]) if r["eng_yaxshi"] is not None else None, "urinish": int(r["urinish"] or 0)})
            conn.commit()
            soni = {k: sum(1 for x in out if x["holat"] == k) for k in ("yechmoqda", "chiqdi", "tugatdi", "boshlamagan")}
            return {"oquvchilar": out, "soni": soni, "jami_savol": len(ids)}
        return run_db(run)

    @router.get("/api/xalqaro/topshiriqlarim")
    def topshiriqlarim(token: str = None, authorization: str = Header(None)):
        """REV401: o'quvchi — qo'shilgan sinflaridagi topshiriqlar va o'z natijasi."""
        user_id = uid_of(token, authorization)

        def run(conn, cur):
            cur.execute("""SELECT t.kod, t.nom, t.muddat, s.nom AS sinf, json_array_length(t.savol_idlar) AS soni, n.eng_yaxshi, n.jami
                           FROM xb_topshiriq t JOIN xb_sinf s ON s.id=t.sinf_id JOIN xb_sinf_azo a ON a.sinf_id=s.id AND a.user_id=%s
                           LEFT JOIN xb_topshiriq_natija n ON n.topshiriq_id=t.id AND n.user_id=%s
                           WHERE t.faol AND s.faol ORDER BY t.id DESC LIMIT 30""", (user_id, user_id))
            out = [{"kod": r["kod"], "nom": r["nom"], "sinf": r["sinf"], "soni": int(r["soni"]), "muddat": r["muddat"].isoformat() if r["muddat"] else None,
                    "foiz": round(100 * int(r["eng_yaxshi"]) / max(1, int(r["jami"]))) if r["jami"] else None} for r in cur.fetchall()]
            conn.commit()
            return {"topshiriqlar": out}
        return run_db(run)

    @router.get("/api/xalqaro/sinf_qidir")
    def sinf_qidir(token: str = None, sinf: int = Query(0, ge=0, le=11), q: str = Query("", max_length=60),
                   til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """O'quvchi: 1–11-sinfdan birini tanlaydi — shu sinf raqamidagi ochiq sinflar (o'qituvchi ismi bilan)."""
        uid_of(token, authorization)

        def run(conn, cur):
            sharts, params = ["s.faol"], []
            if sinf:
                sharts.append("s.sinf=%s"); params.append(sinf)
            if q.strip():
                sharts.append("(s.nom ILIKE %s OR u.full_name ILIKE %s)"); params += [f"%{q.strip()}%"] * 2
            cur.execute(f"""SELECT s.*, COALESCE(u.full_name,'') AS ustoz FROM xb_sinf s LEFT JOIN users u ON u.user_id=s.egasi
                            WHERE {' AND '.join(sharts)} ORDER BY s.yaratildi DESC LIMIT 60""", params)
            out = [_sinf_korinish(r, egasi_ism=_t(r["ustoz"])) for r in cur.fetchall()]
            conn.commit()
            return {"sinflar": out}
        return run_db(run)

    @router.get("/api/xalqaro/taklif/{kod}")
    def taklif(kod: str, token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        uid_of(token, authorization)

        def run(conn, cur):
            cur.execute("""SELECT s.*, COALESCE(u.full_name,'') AS ustoz FROM xb_sinf s LEFT JOIN users u ON u.user_id=s.egasi
                           WHERE s.kod=%s AND s.faol""", (kod_norm(kod),))
            r = cur.fetchone()
            conn.commit()
            if not r:
                raise HTTPException(404, matn("sinf_yoq", til_kodi(til)))
            return {"sinf": _sinf_korinish(r, egasi_ism=_t(r["ustoz"]))}
        return run_db(run)

    @router.post("/api/xalqaro/sinfga_qoshil")
    def sinfga_qoshil(body: SinfQoshil, authorization: str = Header(None)):
        """Taklif kodi (havola) bilan — parolsiz; sinfni ro'yxatdan tanlab — parol bilan (parol qo'yilgan bo'lsa)."""
        user_id = uid_of(body.token, authorization)
        til = til_kodi(body.til)
        if not _urinish_ok(user_id):
            raise HTTPException(429, matn("sinf_kop_urinish", til))

        def run(conn, cur):
            if body.kod:
                cur.execute("SELECT * FROM xb_sinf WHERE kod=%s AND faol", (kod_norm(body.kod),))
            else:
                cur.execute("SELECT * FROM xb_sinf WHERE id=%s AND faol", (body.sinf_id,))
            r = cur.fetchone()
            if not r:
                _urinish_yoz(user_id)
                raise HTTPException(404, matn("sinf_yoq", til))
            if int(r["egasi"]) == int(user_id):
                raise HTTPException(400, matn("sinf_oqituvchi_azo", til))
            if not body.kod and not parol_togri(r["parol_hash"], body.parol, r["kod"]):
                _urinish_yoz(user_id)
                raise HTTPException(403, matn("sinf_parol_xato", til))
            cur.execute("SELECT COUNT(*) AS n FROM xb_sinf_azo WHERE sinf_id=%s", (r["id"],))
            if int(cur.fetchone()["n"]) >= 60:
                raise HTTPException(400, matn("sinf_toliq", til))
            cur.execute("INSERT INTO xb_sinf_azo(sinf_id, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (r["id"], user_id))
            ism = _ism(cur, r["egasi"])
            conn.commit()
            return {"ok": True, "sinf": _sinf_korinish(r, egasi_ism=ism)}
        return run_db(run)

    @router.post("/api/xalqaro/sinfdan_chiq")
    def sinfdan_chiq(body: SinfQoshil, authorization: str = Header(None)):
        user_id = uid_of(body.token, authorization)

        def run(conn, cur):
            cur.execute("DELETE FROM xb_sinf_azo WHERE sinf_id=%s AND user_id=%s", (body.sinf_id, user_id))
            conn.commit()
            return {"ok": True}
        return run_db(run)

    @router.get("/api/xalqaro/kuzatuv")
    def kuzatuv(token: str = None, til: str = Query("uz", max_length=8), authorization: str = Header(None)):
        """Kim ekanini aniqlash: admin / o'qituvchi (o'z maktabi) / o'quvchi. Admin uchun xalqaro bo'limda faol maktablar ro'yxati."""
        user_id = uid_of(token, authorization)

        def run(conn, cur):
            try:
                doira = kuzatuv_doirasi(cur, user_id)
            except HTTPException:
                conn.commit()
                return {"rol": "oquvchi"}
            if doira.get("xb_sinflar") is not None:   # REV373: maktabsiz o'qituvchi — faqat o'z sinflari
                conn.commit()
                return {"rol": "oqituvchi", "mustaqil": True, "maktab_id": None}
            maktablar = []
            if doira["admin"]:
                try:
                    cur.execute("SAVEPOINT xb_mk")
                    cur.execute("""SELECT u.maktab_id AS id, COALESCE(m.nomi, 'Maktab #' || u.maktab_id) AS nomi, COUNT(DISTINCT b.user_id) AS oquvchi
                                   FROM xb_bilim b JOIN users u ON u.user_id=b.user_id LEFT JOIN maktablar m ON m.id=u.maktab_id
                                   WHERE u.maktab_id IS NOT NULL GROUP BY u.maktab_id, m.nomi ORDER BY 3 DESC LIMIT 200""")
                    maktablar = [dict(r) for r in cur.fetchall()]
                    cur.execute("RELEASE SAVEPOINT xb_mk")
                except Exception:
                    cur.execute("ROLLBACK TO SAVEPOINT xb_mk")
                tq = til_kodi(til)
                cur.execute("""SELECT COUNT(DISTINCT user_id) AS oquvchi, COUNT(*) AS javob FROM xb_bilim WHERE til=%s""", (tq,))
                r = cur.fetchone() or {}
                cur.execute("SELECT COUNT(*) AS n, ROUND(AVG(ball)) AS ort FROM xb_imtihon WHERE til=%s AND rasmiy AND topshirilgan IS NOT NULL", (tq,))
                r2 = cur.fetchone() or {}
                cur.execute("SELECT til, COUNT(DISTINCT user_id) AS n FROM xb_bilim GROUP BY til")
                tillar = {x["til"]: int(x["n"]) for x in cur.fetchall()}
                conn.commit()
                return {"rol": "admin", "maktablar": maktablar, "til": tq, "tillar": tillar,
                        "platforma": {"oquvchi": int(r.get("oquvchi") or 0), "javob": int(r.get("javob") or 0),
                                      "imtihon": int(r2.get("n") or 0), "ortacha_ball": int(r2["ort"]) if r2.get("ort") is not None else None}}
            conn.commit()
            return {"rol": "oqituvchi", "maktab_id": doira["maktab_id"]}
        return run_db(run)

    @router.get("/api/xalqaro/rasm/{savol_id}/{v}.svg")
    def rasm(savol_id: str, v: int, request: Request, til: str = Query("uz", max_length=8)):
        til = til_kodi(til)
        k = KT(til)
        s = k.by_id.get(savol_id[:20])
        if not s or v >= len(s["variantlar"]) or not s["variantlar"][v].get("rasm"):
            raise HTTPException(404, matn("rasm_yoq", til))
        svg = s["variantlar"][v]["rasm"].encode("utf-8")
        etag = '"' + hashlib.sha1(svg).hexdigest() + '"'
        headers = {"Cache-Control": "public, max-age=86400", "ETag": etag, "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"}
        if etag in (request.headers.get("if-none-match") or ""):
            return Response(status_code=304, headers=headers)
        return Response(content=svg, media_type="image/svg+xml", headers=headers)

    # ─────────── REV319: savollar banki — Excel (5 til) ───────────
    try:
        from modules import xalqaro_excel as XE
    except ImportError:   # pragma: no cover
        from . import xalqaro_excel as XE

    def _baza_ol(til, turi):
        conn = platform._db(); cur = conn.cursor()
        try:
            cur.execute("SELECT data FROM xb_kontent WHERE til=%s AND turi=%s", (til, turi))
            r = cur.fetchone()
            return r["data"] if r else None
        except Exception:   # noqa: BLE001 — jadval hali yo'q
            conn.rollback(); return None
        finally:
            cur.close(); conn.close()

    def _tillar_yangila():
        conn = platform._db(); cur = conn.cursor()
        try:
            cur.execute("SELECT til FROM xb_kontent WHERE turi='savollar'")
            BAZADA_TILLAR.clear(); BAZADA_TILLAR.update(r["til"] for r in cur.fetchall())
        except Exception:   # noqa: BLE001
            conn.rollback()
        finally:
            cur.close(); conn.close()

    global BAZA_YUKLOVCHI
    BAZA_YUKLOVCHI = _baza_ol
    try:
        _tillar_yangila()
    except Exception:   # noqa: BLE001 — ishga tushishda baza bo'lmasa ham
        pass

    def _kesh_tozala(til):
        for key in list(KONTENTLAR):
            if key == til or (isinstance(key, tuple) and key[1] == til):
                KONTENTLAR.pop(key, None)

    def _admin(token, authorization):
        uid = uid_of(token, authorization)
        conn = platform._db(); cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,))
            if not cur.fetchone():
                raise HTTPException(403, "Faqat admin uchun")
        finally:
            cur.close(); conn.close()
        return uid

    QISMLAR = ("savollar", "darslar", "birliklar", "ramka")
    UMUMIY_QISM = ("natijalar", "davlatlar")

    def _kontent(t):
        """Shu tilning to'liq kontenti (Excel uchun) — bazadan yoki saytdagi joriy holatdan."""
        k = KT(t)
        out = {"savollar": k.savollar, "darslar": k.darslar, "birliklar": list(k.birliklar.values()), "ramka": k.ramka}
        if t == "uz":
            out["natijalar"] = _baza("uz", "natijalar") or _json_fayl(os.path.join(DATA_DIR, "natijalar.json"), {})
            out["davlatlar"] = _baza("uz", "davlatlar") or _json_fayl(os.path.join(DATA_DIR, "davlatlar.json"), {})
        return out

    @router.get("/api/admin/xalqaro/kontent")
    def xb_kontent_holati(token: str = None, authorization: str = Header(None)):
        _admin(token, authorization)
        def run(conn, cur):
            cur.execute("SELECT til, turi, soni, yangilandi FROM xb_kontent")
            baza = {}
            for r in cur.fetchall():
                baza.setdefault(r["til"], {})[r["turi"]] = {"soni": r["soni"], "yangilandi": r["yangilandi"].isoformat()}
            conn.commit()
            out = []
            for t in XE.TILLAR:
                b = baza.get(t, {})
                fayl = os.path.isfile(os.path.join(DATA_DIR if t == "uz" else os.path.join(DATA_DIR, t), "savollar.json"))
                sv = b.get("savollar") or {}
                out.append({"til": t, "nom": XE.TIL_NOMI[t], "manba": "baza" if sv else "fayl" if fayl else "yo'q",
                            "soni": sv.get("soni") or (len(KT(t).savollar) if fayl else 0), "yangilandi": sv.get("yangilandi"),
                            "qismlar": {q: (b.get(q) or {}).get("soni") for q in QISMLAR + (UMUMIY_QISM if t == "uz" else ())}})
            return {"tillar": out}
        return run_db(run)

    @router.get("/api/admin/xalqaro/shablon")
    def xb_shablon(token: str = None, til: str = Query("uz", max_length=4), authorization: str = Header(None)):
        """Joriy xalqaro kontent — to'liq (savollar, darslar, PISA matnlari, tuzilma; o'zbekchada — natijalar ham) Excel'da.
        Nemis/ispan hali bo'lmasa — inglizcha matn bilan (tarjima qilish uchun; ID, javoblar, statistika tayyor)."""
        _admin(token, authorization)
        t = str(til or "uz").lower()[:2]
        if t not in XE.TILLAR:
            raise HTTPException(400, "Til: uz, ru, en, de, es")
        manba = t if (t in ("uz", "ru", "en") or t in BAZADA_TILLAR) else "en"
        k = _kontent(manba)
        if not k["savollar"] and manba != "uz":
            k = _kontent("uz")
        data = XE.kontent_to_xlsx(k, t, stat_manba=KT("uz").savollar or k["savollar"])
        return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": f'attachment; filename="xalqaro_{t}.xlsx"'})

    async def _fayl(request):
        form = await request.form()
        f = form.get("fayl")
        if f is None:
            raise HTTPException(400, "Fayl yuborilmadi")
        data = await f.read()
        if len(data) > 40 * 1024 * 1024:
            raise HTTPException(413, "Fayl juda katta (40 MB dan oshmasin)")
        return data, str(form.get("token") or "")

    def _tekshiruv(data):
        til, kon, xato, ogoh = XE.xlsx_to_kontent(data)
        if not xato and til and til != "uz":
            asos = _kontent("uz")
            if not asos["savollar"]:
                xato.append("Avval o'zbekcha faylni nashr qiling — boshqa tillar u bilan solishtiriladi (ID, javoblar)")
            else:
                xato += XE.kontent_mosligi(asos, kon)
        if til == "uz":
            for q in ("darslar", "ramka", "natijalar", "davlatlar"):
                if not kon.get(q):
                    xato.append(f"O'zbekcha faylda «{q}» bo'lishi shart (to'liq shablondan foydalaning)")
        elif not kon.get("ramka") or not kon.get("darslar"):
            xato.append("Faylda DARSLAR va RAMKA varaqlari bo'lishi shart (to'liq shablondan foydalaning)")
        return til, kon, xato, ogoh

    @router.post("/api/admin/xalqaro/tekshir")
    async def xb_tekshir(request: Request, authorization: str = Header(None)):
        data, token = await _fayl(request)
        _admin(token, authorization)
        til, kon, xato, ogoh = await run_in_threadpool(_tekshiruv, data)
        sav = kon.get("savollar") or []
        return {"til": til, "savollar": len(sav), "variantlar": sum(len(q["variantlar"]) for q in sav),
                "darslar": len(kon.get("darslar") or []), "birliklar": len(kon.get("birliklar") or []),
                "xatolar": xato[:200], "xato_soni": len(xato), "ogohlantirishlar": ogoh[:100], "tayyor": not xato}

    def _nashr_et(data, uid):
        """REV346: tekshiruvdan o'tgan xalqaro Excel'ni nashr qiladi. Qaytaradi: (til, kontent, ogohlantirishlar). Xato bo'lsa — 422."""
        til, kon, xato, ogoh = _tekshiruv(data)
        if xato:
            raise HTTPException(422, {"kod": "xato", "xatolar": xato[:200], "xato_soni": len(xato)})
        qism = QISMLAR + (UMUMIY_QISM if til == "uz" else ())

        def run(conn, cur):
            for q in qism:
                if q not in kon:
                    continue
                v = kon[q]
                cur.execute("""INSERT INTO xb_kontent(til, turi, data, soni, yukladi) VALUES(%s,%s,%s::json,%s,%s)
                               ON CONFLICT (til, turi) DO UPDATE SET data=EXCLUDED.data, soni=EXCLUDED.soni, yukladi=EXCLUDED.yukladi, yangilandi=NOW()""",
                            (til, q, json.dumps(v, ensure_ascii=False), len(v) if isinstance(v, list) else len(v or {}), uid))
            conn.commit()
            return True
        run_db(run)
        BAZADA_TILLAR.add(til)
        _kesh_tozala(til)
        if til == "uz":
            _NATIJA_KESH.clear()
            K.yangila()   # REV380: o'zbekcha kontent obyekti ham qayta o'qiladi (avval faqat lug'atdan o'chirilardi)
            for key in list(KONTENTLAR):   # natijalar hamma tilda ishlatiladi
                if key != "uz":
                    KONTENTLAR.pop(key, None)
        return til, kon, ogoh

    global PAKET_NASHR
    PAKET_NASHR = _nashr_et   # REV346: «Paketni birdan o'rnatish» xalqaro Excel'ni shu orqali nashr qiladi

    @router.post("/api/admin/xalqaro/nashr")
    async def xb_nashr(request: Request, authorization: str = Header(None)):
        """Tekshiruvdan o'tgan faylni nashr qiladi (bitta tranzaksiyada — yoki hammasi, yoki hech narsa).
        Saytdagi shu tildagi xalqaro bo'lim darhol yangilanadi."""
        data, token = await _fayl(request)
        uid = _admin(token, authorization)
        til, kon, ogoh = await run_in_threadpool(_nashr_et, data, uid)
        return {"ok": True, "til": til, "savollar": len(kon.get("savollar") or []), "darslar": len(kon.get("darslar") or []),
                "ogohlantirishlar": ogoh[:50]}

    @router.post("/api/admin/xalqaro/qaytar")
    def xb_qaytar(token: str = Query(None), til: str = Query(..., max_length=4), authorization: str = Header(None)):
        """Shu tilning bazadagi xalqaro kontentini o'chiradi."""
        _admin(token, authorization)
        t = str(til).lower()[:2]
        def run(conn, cur):
            cur.execute("DELETE FROM xb_kontent WHERE til=%s", (t,))
            conn.commit(); return True
        run_db(run)
        BAZADA_TILLAR.discard(t)
        _kesh_tozala(t)
        if t == "uz":
            _NATIJA_KESH.clear(); KONTENTLAR.clear()
        return {"ok": True}

    return router

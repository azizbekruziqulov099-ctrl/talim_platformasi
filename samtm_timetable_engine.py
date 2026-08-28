"""SamTM jadval generatori uchun qat'iy va bosqichli yumshoq siyosat."""

ENGINE_RELEASE = "SAMTM-TIMETABLE-ENGINE-V2-6MODE"
STAGES = ("strict", "light", "balanced", "flexible", "fit_all", "emergency")

HARD_MARKERS = (
    "sinf band", "o'qituvchi boshqa darsda", "real vaqtda ustma-ust",
    "o'qituvchining metod kuni", "o'qituvchi bu vaqtda band", "qattiq blok",
    "qizil", "smena sozlanmagan", "smenada mavjud emas",
    "o'qish haftasidan tashqari", "shanba kuni dars bloklangan",
    "shanba kuni boshlang'ich", "guruh", "haftalik maksimum",
    "o'qituvchi biriktirilmagan",
)

MODE_SOFT_MARKERS = {
    "strict": (),
    "light": (
        "5-akademik dars faqat yengil", "5-darsga matematika",
        "5-darsga til", "5-darsga",
    ),
    "balanced": (
        "5 akademik darsli kunlar soni", "5-akademik dars faqat yengil",
        "5-darsga matematika", "5-darsga til", "5-darsga",
    ),
    "flexible": (
        "5 akademik darsli kunlar soni", "5-akademik dars faqat yengil",
        "5-darsga matematika", "5-darsga til", "5-darsga",
        "boshlang'ich sinfning akademik kunlik limiti",
    ),
    "fit_all": (
        "5 akademik darsli kunlar soni", "5-akademik dars faqat yengil",
        "5-darsga matematika", "5-darsga til", "5-darsga",
        "boshlang'ich sinfning akademik kunlik limiti",
        "boshlang'ich sinfda bir fan shu kuni takror",
        "fan kunlik maksimumga yetgan",
    ),
    "emergency": (
        "5 akademik darsli kunlar soni", "5-akademik dars faqat yengil",
        "5-darsga matematika", "5-darsga til", "5-darsga",
        "boshlang'ich sinfning akademik kunlik limiti",
        "boshlang'ich sinfda bir fan shu kuni takror",
        "fan kunlik maksimumga yetgan",
        "jismoniy tarbiya va texnologiya 1-darsga",
    ),
}

MODE_CONFIG = {
    1: {"stage": "strict", "repeat_days": 0, "nomi": "Qat'iy", "izoh": "Barcha pedagogik va qat'iy qoidalar to'liq saqlanadi."},
    2: {"stage": "light", "repeat_days": 0, "nomi": "Sal yumshoq", "izoh": "Faqat 5-darsdagi og'ir/yengil fan tavsiyasi yumshaydi."},
    3: {"stage": "balanced", "repeat_days": 0, "nomi": "Muvozanatli", "izoh": "Boshlang'ichdagi 5 soatlik kunlar soni tavsiyasi ham yumshaydi."},
    4: {"stage": "flexible", "repeat_days": 0, "nomi": "Moslashuvchan", "izoh": "Akademik fanlarning kunlik pedagogik limiti yumshaydi."},
    5: {"stage": "fit_all", "repeat_days": 1, "nomi": "Kuchli sig'dirish", "izoh": "Zaruratda aynan bir fan haftada 1 kun ikki marta qo'yilishi mumkin."},
    6: {"stage": "emergency", "repeat_days": 2, "nomi": "Oxirgi imkon", "izoh": "Zaruratda aynan bir fan haftada 2 kungacha ikki marta qo'yilishi mumkin."},
}

FIT_ALL_SOFT_MARKERS = (
    "boshlang'ich sinfda bir fan shu kuni takror",
    "boshlang'ich sinfning akademik kunlik limiti",
    "fan kunlik maksimumga yetgan",
)


def _matches(reason, markers):
    def normalize(value):
        return (
            str(value or "").casefold()
            .replace("‘", "'").replace("’", "'").replace("`", "'")
            .replace("–", "-").replace("—", "-")
        )
    normalized = normalize(reason)
    return any(normalize(marker) in normalized for marker in markers)


def is_hard_reason(reason):
    return _matches(reason, HARD_MARKERS)


def filter_reasons(reasons, stage="strict"):
    """Faqat joriy bosqichda darsni rostdan bloklaydigan sabablarni qoldiradi."""
    stage = stage if stage in STAGES else "strict"
    unique = list(dict.fromkeys(str(reason) for reason in (reasons or []) if reason))
    if stage == "strict":
        return unique
    soft = MODE_SOFT_MARKERS.get(stage, ())
    return [reason for reason in unique if is_hard_reason(reason) or not _matches(reason, soft)]


def stage_label(stage):
    return {
        "strict": "Qat'iy pedagogik jadval",
        "light": "Sal yumshoq",
        "balanced": "Muvozanatli",
        "flexible": "Moslashuvchan",
        "fit_all": "Kuchli sig'dirish",
        "emergency": "Oxirgi imkon",
    }.get(stage, stage)


def mode_config(mode):
    try:
        mode = int(mode)
    except (TypeError, ValueError):
        mode = 1
    mode = max(1, min(6, mode))
    return {"raqam": mode, **MODE_CONFIG[mode]}


def public_modes():
    return [{"raqam": number, **config} for number, config in MODE_CONFIG.items()]

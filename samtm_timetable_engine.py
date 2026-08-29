"""SamTM uchun yagona kuchli va xavfsiz jadval generatori siyosati."""

ENGINE_RELEASE = "SAMTM-TIMETABLE-ENGINE-V4-POWERFUL"
STAGES = ("powerful",)

# Bu sabablar hech qachon yumshamaydi. Generator barcha soatni sig'dira
# olmasa ham noto'g'ri jadval saqlash o'rniga aniq diagnostika qaytaradi.
HARD_MARKERS = (
    "sinf band", "o'qituvchi boshqa darsda", "real vaqtda ustma-ust",
    "o'qituvchining metod kuni", "o'qituvchi bu vaqtda band", "qattiq blok",
    "qizil", "smena sozlanmagan", "smenada mavjud emas",
    "o'qish haftasidan tashqari", "shanba kuni dars bloklangan",
    "shanba kuni boshlang'ich", "guruh", "haftalik maksimum",
    "o'qituvchi biriktirilmagan", "fan kunlik maksimumga yetgan",
    "bir fan shu kuni takror", "akademik kunlik limiti",
)

# Faqat pedagogik afzalliklar yumshoq: qattiq to'qnashuv bo'lmasa generator
# ertaroq/kechroq katakni tanlaydi, ammo shu tavsiya sabab dars tashlamaydi.
POWERFUL_SOFT_MARKERS = (
    "5 akademik darsli kunlar soni", "5-akademik dars faqat yengil",
    "5-darsga matematika", "5-darsga til", "5-darsga",
    "jismoniy tarbiya va texnologiya 1-darsga",
)

POWERFUL_CONFIG = {
    "raqam": 1,
    "stage": "powerful",
    "repeat_days": 0,
    "attempts": 12,
    "imbalance_limit": 1,
    "strategy": "yagona_kuchli",
    "nomi": "Kuchli generator",
    "izoh": "Qattiq qoidalarni buzmasdan eng ixcham to'liq jadvalni qidiradi.",
}


def _normalize(value):
    return (
        str(value or "").casefold()
        .replace("‘", "'").replace("’", "'").replace("`", "'")
        .replace("–", "-").replace("—", "-")
    )


def _matches(reason, markers):
    normalized = _normalize(reason)
    return any(_normalize(marker) in normalized for marker in markers)


def is_hard_reason(reason):
    return _matches(reason, HARD_MARKERS)


def filter_reasons(reasons, stage="powerful"):
    """Qattiq sabablarni saqlab, faqat pedagogik tavsiyalarni yumshatadi."""
    unique = list(dict.fromkeys(str(reason) for reason in (reasons or []) if reason))
    return [
        reason for reason in unique
        if is_hard_reason(reason) or not _matches(reason, POWERFUL_SOFT_MARKERS)
    ]


def stage_label(stage="powerful"):
    return "Yagona kuchli generator"


def mode_config(mode=None):
    """Eski frontend so'rovlariga mos, lekin har doim yagona siyosat qaytadi."""
    return dict(POWERFUL_CONFIG)


def public_modes():
    return [dict(POWERFUL_CONFIG)]

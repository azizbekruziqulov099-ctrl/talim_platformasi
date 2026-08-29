"""SamTM maktabi uchun yagona feasibility-first jadval siyosati.

Foydalanuvchi rejim tanlamaydi. Bitta generator avval barcha majburiy darsni
qattiq qoidalar ichida joylashtiradi, pedagogik qulayliklarni esa ball bilan
yaxshilaydi. Qizil vaqt, metod kuni, smena, sinf/o'qituvchi/xona to'qnashuvi
va guruh sinxronligi hech qachon yumshamaydi.
"""

ENGINE_RELEASE = "SAMTM-TIMETABLE-ENGINE-V7-PHASE-AWARE-WINDOW-REPORT"

INTERNAL_STAGES = ("strict", "balanced", "completion")

# Sabab matnlari eski backend qatlamlaridan keladi. Ular bir xil apostrof yoki
# tire ishlatmasligi mumkin, shuning uchun pastdagi _normalize barchasini bir
# ko'rinishga keltiradi.
HARD_MARKERS = (
    "sinf band",
    "o'qituvchi boshqa darsda",
    "real vaqtda ustma-ust",
    "o'qituvchining metod kuni",
    "o'qituvchi bu vaqtda band",
    "qattiq blok",
    "qizil",
    "smena sozlanmagan",
    "smenada mavjud emas",
    "o'qish haftasidan tashqari",
    "shanba kuni dars bloklangan",
    "shanba kuni boshlang'ich",
    "guruh",
    "haftalik maksimum",
    "o'qituvchi biriktirilmagan",
    "xona band",
    "asosiy og'ir fan 6-darsga haftada ko'pi bilan 2 kun",
)

# Faqat ichki yakunlash bosqichida olib tashlanishi mumkin bo'lgan pedagogik
# tavsiyalar. Bu ro'yxatda fan kunlik maksimumi yo'q: akademik fan bir kunda
# majburan takrorlanmaydi. Jismoniy tarbiya/texnologiya juftligi backenddagi
# maxsus xavfsiz qoida orqali alohida boshqariladi.
BALANCED_SOFT_MARKERS = (
    "5-akademik dars faqat yengil",
    "5-darsga matematika",
    "5-darsga til",
    "5-darsga",
    "5 akademik darsli kunlar soni",
)

COMPLETION_SOFT_MARKERS = BALANCED_SOFT_MARKERS + (
    "boshlang'ich sinfning akademik kunlik limiti",
)


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


def filter_reasons(reasons, stage="strict"):
    """Joriy ichki bosqichda darsni rostdan bloklaydigan sabablarni qoldiradi."""
    unique = list(dict.fromkeys(str(reason) for reason in (reasons or []) if reason))
    stage = stage if stage in INTERNAL_STAGES else "strict"
    if stage == "strict":
        return unique
    soft = BALANCED_SOFT_MARKERS if stage == "balanced" else COMPLETION_SOFT_MARKERS
    return [reason for reason in unique if is_hard_reason(reason) or not _matches(reason, soft)]


def internal_policy(stage):
    """Yagona generator ishlatadigan yashirin bosqich sozlamasi."""
    stage = stage if stage in INTERNAL_STAGES else "strict"
    return {
        "stage": stage,
        "repeat_days": 0,
        "nomi": {
            "strict": "Qattiq joylash",
            "balanced": "Muvozanatli to'ldirish",
            "completion": "Xavfsiz yakunlash",
        }[stage],
    }


def stage_label(stage):
    return internal_policy(stage)["nomi"]


def mode_config(_mode=None):
    """Eski API bilan mos, lekin doim bitta ommaviy generatorni qaytaradi."""
    return {
        "raqam": 1,
        "stage": "feasibility_first",
        "repeat_days": 2,
        "attempts": 4,
        "imbalance_limit": 2,
        "strategy": "yagona",
        "nomi": "Yagona kuchli generator",
        "izoh": (
            "Avval qattiq qoidalar ichida barcha darsni sig'diradi; keyin "
            "oyna, fan vaqti va kun taqsimotini yaxshilaydi. Asosiy fanlar "
            "1-5-darsda turadi; faqat boshqa legal katak qolmasa 6-darsga "
            "tushadi va bir sinfda haftasiga ikki kundan oshmaydi."
        ),
    }


def public_modes():
    """Frontend va capability endpointi uchun faqat bitta generator."""
    return [mode_config()]

# REV320: Xalqaro baholash kontenti saytda faqat BAZADAN (Excel orqali yuklanadi). Testlar uchun namuna kontent —
# tests/fixtures/xalqaro_data (sayt uni ishlatmaydi).
import os
os.environ.setdefault("XB_DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "xalqaro_data"))

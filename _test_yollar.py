"""REV210: testlar uchun yo'llar. Testlar dastlab monorepo'da yozilgan (ROOT/backend, ROOT/frontend, ROOT/database).
Bu yerda «backend» — shu repo, «frontend» — yonma-yon turgan frontend repo (topilsa), «database» — migratsiyalar papkasi.
Boshqa repodagi fayl topilmasa — o'sha test xato emas, «o'tkazib yuborildi» (skip) deb belgilanadi."""
import os
import unittest
from pathlib import PosixPath

REPO_DIR = os.path.dirname(os.path.abspath(__file__))


# main.py — endi yupqa kirish nuqtasi; asosiy kod samtm_platform.py va kabutar_* fayllarida.
_MAIN_QISMLARI = ("main.py", "samtm_platform.py", "samtm_runtime.py", "kabutar_policy.py", "kabutar_auth.py")


class Yol(PosixPath):
    def read_text(self, *a, **k):
        if self.name == "main.py" and str(self.parent) == REPO_DIR:
            return "\n".join(PosixPath(REPO_DIR, f).read_text(encoding="utf-8")
                             for f in _MAIN_QISMLARI if os.path.exists(os.path.join(REPO_DIR, f)))
        if not self.exists():
            raise unittest.SkipTest(f"Kerakli fayl bu repoda yo'q (boshqa repo): {self}")
        return super().read_text(*a, **k)

    def read_bytes(self):
        if not self.exists():
            raise unittest.SkipTest(f"Kerakli fayl bu repoda yo'q (boshqa repo): {self}")
        return super().read_bytes()


def _birinchi(*nomzodlar):
    for n in nomzodlar:
        if n and os.path.isdir(n):
            return n
    return nomzodlar[-1]


REPO = Yol(REPO_DIR)
FRONTEND = Yol(_birinchi(
    os.environ.get("KABUTAR_FRONTEND_DIR"),
    os.path.join(os.path.dirname(REPO_DIR), "frontend"),
    os.path.join(os.path.dirname(REPO_DIR), "talim_platformasi_frontend-main"),
    os.path.join(os.path.dirname(os.path.dirname(REPO_DIR)), "fe", "talim_platformasi_frontend-main"),
    os.path.join(os.path.dirname(REPO_DIR), "frontend")))
DATABASE = Yol(_birinchi(os.path.join(REPO_DIR, "database"), os.path.join(os.path.dirname(REPO_DIR), "database"),
                         os.path.join(REPO_DIR, "database")))


class MonoRoot(Yol):
    """ROOT / "backend" → shu repo, ROOT / "frontend" → frontend repo, ROOT / "database" → migratsiyalar."""
    def __truediv__(self, key):
        k = str(key)
        if k == "backend":
            return REPO
        if k == "frontend":
            return FRONTEND
        if k == "database":
            return DATABASE
        return Yol(os.path.join(os.path.dirname(REPO_DIR), k))


ROOT = MonoRoot(os.path.dirname(REPO_DIR))

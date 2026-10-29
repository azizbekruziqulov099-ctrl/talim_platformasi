"""REV210: testlar «backend.modules…» deb import qiladi (monorepo'da repo «backend/» papkasida turadi).
Repo alohida turganda ham ishlashi uchun «backend» nomini shu papkaga bog'laymiz."""
import os
import sys
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if "backend" not in sys.modules:
    _pkg = types.ModuleType("backend")
    _pkg.__path__ = [ROOT]
    sys.modules["backend"] = _pkg

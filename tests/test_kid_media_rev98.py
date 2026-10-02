import re
from pathlib import Path

from modules.dars_xonasi import _svg_name

ROOT = Path(__file__).resolve().parents[1]


def _helpers():
    src = (ROOT / "samtm_platform.py").read_text(encoding="utf-8")
    i = src.index("def _ai_media_svg_xavfsizmi")
    k = src.index("\n\n\n", src.index("def _ai_media_nom_variantlari"))
    ns = {"re": re, "os": __import__("os")}
    exec(src[i:k], ns)
    return ns


def test_svg_alias_and_safety():
    ns = _helpers()
    ok = b'<svg xmlns="http://www.w3.org/2000/svg"><style>.w{animation:w 2s 3}</style><circle r="4"/></svg>'
    assert ns["_ai_media_svg_xavfsizmi"](ok)
    for bad in (b"<svg><script>x()</script></svg>", b'<svg onload="x()"/>', b'<svg><image href="https://e.x/a.png"/></svg>', b"not svg"):
        assert not ns["_ai_media_svg_xavfsizmi"](bad)
    names = ns["_ai_media_nom_variantlari"]({"en34-u1-hello.svg", "a.png"})
    assert {"en34-u1-hello.png", "en34-u1-hello.jpg", "a.png"} <= names
    assert _svg_name("rasm.PNG") == "rasm.svg" and _svg_name("rasm") == "rasm"


def test_kid_voice_pitch_param_is_bounded():
    src = (ROOT / "samtm_platform.py").read_text(encoding="utf-8")
    assert 'ohang: str = ""' in src and r'[+-](?:[0-9]|1[0-9]|20)Hz' in src and "pitch=ohang" in src

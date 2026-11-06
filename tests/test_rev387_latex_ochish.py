import os
os.environ.setdefault("JWT_MAXFIY_KALIT", "x" * 40)
import samtm_platform as S

def t(x):
    return " ".join(S._lat_va_latex_ochish(x).split())

def test_indeks_va_daraja_ovozi():
    assert t("[lat]x_0[/lat]") == "iks nol"
    assert t("[lat]a_1 + a_2[/lat]") == "a bir + a ikki"
    assert "_" not in t("[lat]x_{10}^2[/lat]")
    assert t("x₀ va x²") == "iks nol va iks ning kvadrati"
    assert t("[lat]x^2 + x^2[/lat]") == "iks ning kvadrati + iks kvadrat"
    assert t("[lat]x^5[/lat]") == "iks ning beshinchi darajasi"

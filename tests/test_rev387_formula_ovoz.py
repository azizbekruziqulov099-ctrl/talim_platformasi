from modules.speech_math import speak_formula

def test_pastki_indeks_tabiiy():
    assert speak_formula("x_0", "uz") == "iks nol"
    assert speak_formula("x_{1}+x_{2}", "uz") == "iks bir plyus iks ikki"
    assert "indeks" not in speak_formula("a_n=a_1+(n-1)d", "uz")
    assert speak_formula("x_0", "ru") == "икс ноль"

def test_daraja_birinchi_marta_toliq_keyin_qisqa():
    assert speak_formula("x^3 \\cdot x^3", "uz") == "iksning kubi ko‘paytirilgan iks kub"
    assert speak_formula("x^2+x^2", "uz") == "iksning kvadrati plyus iks kvadrat"
    assert speak_formula("a^2+b^2=c^2", "uz") == "aning kvadrati plyus bening kvadrati teng sining kvadrati"

"""REV111: har til o'z ovozida o'qilsin — test variantlari va ovoz matnidagi teglar."""
from tools.bogcha_teg import fix_option, fix_voice, wrap_izoh


def test_options():
    assert fix_option("A) 😴 [en]uxlaymiz[/en]", "en") == "A) 😴 uxlaymiz"          # o'zbekcha — tegsiz
    assert fix_option("A) 🕗 It's eight o'clock.", "en") == "A) 🕗 [en]It's eight o'clock.[/en]"
    assert fix_option("B) 👋 [ru]Привет![/ru]", "ru") == "B) 👋 [ru]Привет![/ru]"


def test_voice_non_latin_and_izoh():
    out = fix_voice("[ru]Сколько?[/ru] (Сколько? ⭐⭐ — nechta?)", "ru", None)
    assert out == "[ru]Сколько?[/ru] ([ru]Сколько?[/ru] ⭐⭐ — nechta?)"
    assert wrap_izoh("Смотри, это — [en]Hello![/en] Молодец!", "ru") == "[ru]Смотри, это —[/ru] [en]Hello![/en] [ru]Молодец![/ru]"
    assert wrap_izoh("Qara: [en]Hi[/en]", "uz") == "Qara: [en]Hi[/en]"

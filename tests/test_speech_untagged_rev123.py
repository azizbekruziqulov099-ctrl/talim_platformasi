"""REV123: tegsiz matn tili — ruscha kirill rus ovozida, aniq inglizcha gap ingliz ovozida, qolgani o'zbekcha."""
from modules.speech_language import split_speech_text, untagged_language


def test_cyrillic_russian_is_read_by_russian_voice():
    assert untagged_language('Ничего страшного! Правильный ответ.') == 'ru'
    assert [l for l, _ in split_speech_text('Молодец! [en]Hello![/en]')] == ['ru', 'en']


def test_uzbek_cyrillic_and_latin_stay_uzbek():
    assert untagged_language('Бугун қуёшли кун') == 'uz'
    assert untagged_language("Hechqisi yo'q! To'g'ri javob — 12.") == 'uz'
    assert untagged_language('Bu olma.') == 'uz'
    assert untagged_language('Mana u: kitob') == 'uz'


def test_clear_english_sentence_is_english():
    assert untagged_language('It is a cat and a dog.') == 'en'

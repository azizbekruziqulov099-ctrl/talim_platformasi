from modules import mavzu_nomi as M

def test_boshqa_alifbolar_ajraladi():
    a, b = M.nom_norm("안녕하세요 and 안녕"), M.nom_norm("안녕 and 고마워요")
    assert a != b and a and b
    assert M.nom_norm("你好 and 嗨") != M.nom_norm("拜拜 and 谢谢")
    assert M.nom_norm("こんにちは and やあ") != M.nom_norm("バイバイ and ありがとう")

def test_eski_qoidalar_ozgarmadi():
    assert M.nom_norm("3-mavzu. Ranglar") == "ranglar"
    assert M.nom_norm("O‘zbekiston") == M.nom_norm("O'zbekiston") == "ozbekiston"
    assert M.nom_norm("Öyinlar") == M.nom_norm("Oyinlar")
    assert M.nom_norm("Ранглар!") == "ранглар"

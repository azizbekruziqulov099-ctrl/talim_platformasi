import os
os.environ.setdefault("JWT_MAXFIY_KALIT", "x" * 40)
import samtm_platform as S

def test_faollik_yorliqlari_aniq_vaqt_bermaydi():
    assert S.chat_faollik_matni(5) == "onlayn"
    assert S.chat_faollik_matni(1800) == "yaqinda faol edi"
    assert S.chat_faollik_matni(None) == "uzoq vaqt oldin"
    assert any(r.path == "/api/chat/yozmoqda" for r in S.app.routes)

def test_rev395_qadash_kaliti_ikkala_tomonda_bir_xil():
    assert S._chat_suhbat_kalit(5, None, 9) == S._chat_suhbat_kalit(9, None, 5) == "u5_9"
    assert S._chat_suhbat_kalit(5, 12, None) == "g12"
    assert any(r.path == "/api/chat/xabar_qadash" for r in S.app.routes)

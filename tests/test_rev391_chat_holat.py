import os
os.environ.setdefault("JWT_MAXFIY_KALIT", "x" * 40)
import samtm_platform as S

def test_faollik_yorliqlari_aniq_vaqt_bermaydi():
    assert S.chat_faollik_matni(5) == "onlayn"
    assert S.chat_faollik_matni(1800) == "yaqinda faol edi"
    assert S.chat_faollik_matni(None) == "uzoq vaqt oldin"
    assert any(r.path == "/api/chat/yozmoqda" for r in S.app.routes)

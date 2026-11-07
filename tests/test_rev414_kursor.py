from platform_core import ddl_guard as g

def test_user_json_rasmsiz():
    yozildi = []
    class Fake(g.XavfsizCursor):
        def __init__(self): pass
    import psycopg2.extras as ex
    orig = ex.RealDictCursor.execute
    try:
        ex.RealDictCursor.execute = lambda self, q, v=None: yozildi.append(q)
        Fake().execute("SELECT to_jsonb(u) AS profile FROM users u WHERE user_id=%s", (1,))
    finally:
        ex.RealDictCursor.execute = orig
    assert "- $$profil_rasm$$" in yozildi[0] and "to_jsonb(u) AS" not in yozildi[0].replace("(to_jsonb(u) -", "")

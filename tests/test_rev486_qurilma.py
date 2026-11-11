from datetime import timedelta
from modules.qurilma import jarima

def test_jarima_zinapoyasi():
    assert jarima(1) is None and jarima(2) is None
    assert jarima(3) == timedelta(hours=1) and jarima(4) == timedelta(hours=7)
    assert jarima(5) == timedelta(days=1) and jarima(6) == timedelta(days=7) and jarima(9) == timedelta(days=7)

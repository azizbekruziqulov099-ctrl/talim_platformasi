"""REV110: kesh — bir dars 1000 marta so'ralsa ham bazaga bitta so'rov."""
import threading
import time

from modules.tez_kesh import BaytKesh, TTLKesh


def test_single_flight_one_db_call():
    k = TTLKesh(ttl=60)
    calls = []

    def slow():
        calls.append(1)
        time.sleep(0.05)
        return {"steps": [1]}

    threads = [threading.Thread(target=lambda: k.olish("dars", slow)) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(calls) == 1


def test_ttl_and_none_not_cached():
    now = [0.0]
    k = TTLKesh(ttl=10, clock=lambda: now[0])
    assert k.olish("a", lambda: None) is None
    assert k.olish("a", lambda: 5) == 5
    now[0] = 11
    assert k.get("a") is None


def test_bytes_lru_limit():
    b = BaytKesh(max_bytes=10, max_item=8)
    b.set(1, "image/png", "x", b"12345")
    b.set(2, "image/png", "y", b"67890")
    b.set(3, "image/png", "z", b"abc")
    assert b.get(1) is None and b.get(3) and b.size <= 10
    b.set(4, "image/png", "w", b"123456789")   # juda katta — keshlanmaydi
    assert b.get(4) is None

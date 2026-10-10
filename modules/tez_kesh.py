"""REV110: ko'p foydalanuvchi bir vaqtda kirganda bazani asrash uchun jarayon ichidagi kesh.

- TTLKesh: kalit → qiymat, ma'lum vaqt yashaydi, hajmi cheklangan (eski yozuvlar chiqarib tashlanadi).
  Bir kalit uchun bir vaqtda faqat BITTA hisoblash bo'ladi («single-flight»): 1000 bola bir darsni bir
  soniyada ochsa, bazaga bitta so'rov boradi, qolganlari shu natijani kutib oladi.
- BaytKesh: rasm kabi o'zgarmas baytlar uchun, umumiy hajm bo'yicha cheklangan LRU.
"""
import threading
import time
from collections import OrderedDict


class TTLKesh:
    def __init__(self, ttl=120.0, maxsize=2000, clock=time.monotonic):
        self.ttl, self.maxsize, self.clock = float(ttl), int(maxsize), clock
        self._data = OrderedDict()          # kalit → (muddat, qiymat)
        self._lock = threading.Lock()
        self._inflight = {}                 # kalit → threading.Lock

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            if item[0] < self.clock():
                self._data.pop(key, None)
                return None
            self._data.move_to_end(key)
            return item[1]

    def set(self, key, value, ttl=None):
        with self._lock:
            self._data[key] = (self.clock() + (self.ttl if ttl is None else float(ttl)), value)
            self._data.move_to_end(key)
            while len(self._data) > self.maxsize:
                self._data.popitem(last=False)

    def clear(self):
        with self._lock:
            self._data.clear()

    def olish(self, key, hisobla):
        """Keshda bo'lsa — darhol; bo'lmasa — bitta oqim hisoblaydi, boshqalari kutadi. Xatolar keshlanmaydi."""
        value = self.get(key)
        if value is not None:
            return value
        with self._lock:
            lock = self._inflight.setdefault(key, threading.Lock())
        with lock:
            value = self.get(key)
            if value is not None:
                return value
            try:
                value = hisobla()
                if value is not None:
                    self.set(key, value)
                return value
            finally:
                with self._lock:
                    if self._inflight.get(key) is lock:
                        self._inflight.pop(key, None)


class BaytKesh:
    def __init__(self, max_bytes=48 * 1024 * 1024, max_item=2 * 1024 * 1024):
        self.max_bytes, self.max_item = int(max_bytes), int(max_item)
        self._data = OrderedDict()          # kalit → (content_type, sha256, data)
        self._size = 0
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item:
                self._data.move_to_end(key)
            return item

    def set(self, key, content_type, sha, data):
        data = bytes(data)
        if len(data) > self.max_item:
            return
        with self._lock:
            old = self._data.pop(key, None)
            if old:
                self._size -= len(old[2])
            self._data[key] = (content_type, sha, data)
            self._size += len(data)
            while self._size > self.max_bytes and self._data:
                _, (_, _, d) = self._data.popitem(last=False)
                self._size -= len(d)

    @property
    def size(self):
        return self._size

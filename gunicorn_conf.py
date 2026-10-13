"""Gunicorn production settings for SamTM V19.2."""

import logging, multiprocessing, os

bind = "0.0.0.0:" + os.getenv("PORT", "8080")
worker_class = "uvicorn.workers.UvicornWorker"
# REV130: har worker bazaga 2 ta pul (har biri DB_POOL_MAX=10 gacha) ochadi. Railway Postgres standart chegarasi —
# 100 ulanish. 4 worker × 20 = 80 — chegaradan oshmaydi (8 worker 160 ta so'rab, baza "too many connections" berardi).
workers = int(os.getenv("WEB_CONCURRENCY", str(max(2, min(4, multiprocessing.cpu_count()*2)))))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "180"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "5000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "500"))
proc_name = "samtm-v19.2"
# REV130: har so'rovga bitta log qatori ko'p foydalanuvchida Railway loglarini to'ldirib yuboradi —
# standart holatda o'chiq; kerak bo'lsa ACCESS_LOG=1 qo'ying.
accesslog = "-" if os.getenv("ACCESS_LOG", "").strip().lower() in ("1", "true", "yes", "ha") else None
# Legacy API clients still pass session tokens in query strings. Never log
# the request line, query, Referer or Authorization header.
access_log_format = '%(h)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(B)s %(D)s'
errorlog = "-"
capture_output = True


class _RedactASGIQuery(logging.Filter):
    """Uvicorn formats its own access line, bypassing Gunicorn's format."""

    def filter(self, record):
        if record.name == "uvicorn.access" and isinstance(record.args, tuple) and len(record.args) == 5:
            values = list(record.args)
            values[2] = str(values[2]).split("?", 1)[0]
            record.args = tuple(values)
        return True


def post_fork(server, worker):
    logging.getLogger("uvicorn.access").addFilter(_RedactASGIQuery())

"""Gunicorn production settings for SamTM V19.2."""

import multiprocessing, os

bind = "0.0.0.0:" + os.getenv("PORT", "8080")
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.getenv("WEB_CONCURRENCY", str(max(2, min(8, multiprocessing.cpu_count()*2)))))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "180"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "5000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "500"))
proc_name = "samtm-v19.2"
accesslog = "-"
errorlog = "-"
capture_output = True

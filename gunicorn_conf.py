import multiprocessing, os
bind = "0.0.0.0:" + os.getenv("PORT", "8080")
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.getenv("WEB_CONCURRENCY", str(max(2, min(8, multiprocessing.cpu_count()*2)))))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "180"))
graceful_timeout = 30
keepalive = 5
max_requests = 5000
max_requests_jitter = 500
accesslog = "-"
errorlog = "-"
capture_output = True

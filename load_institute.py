"""Small authenticated read-load probe for institute v1.

Usage:
  INSTITUTE_BASE_URL=https://... INSTITUTE_TOKEN=... INSTITUTE_CONTEXT_ID=1 \
  python backend/tests/load_institute.py
"""

from __future__ import annotations

import concurrent.futures
import os
import statistics
import time

import httpx


BASE_URL = os.environ["INSTITUTE_BASE_URL"].rstrip("/")
TOKEN = os.environ["INSTITUTE_TOKEN"]
CONTEXT_ID = int(os.environ["INSTITUTE_CONTEXT_ID"])
WORKERS = min(max(int(os.getenv("INSTITUTE_LOAD_WORKERS", "8")), 1), 32)
REQUESTS = min(max(int(os.getenv("INSTITUTE_LOAD_REQUESTS", "80")), 1), 2_000)
PATHS = (
    "/api/institut-v1/meta",
    f"/api/institut-v1/dashboard?context_id={CONTEXT_ID}",
    f"/api/institut-v1/programs?context_id={CONTEXT_ID}&limit=20",
    f"/api/institut-v1/sections?context_id={CONTEXT_ID}&limit=20",
    f"/api/institut-v1/analytics/summary?context_id={CONTEXT_ID}",
)


def one(index: int) -> tuple[int, float]:
    started = time.perf_counter()
    with httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=15,
    ) as client:
        response = client.get(PATHS[index % len(PATHS)])
    return response.status_code, (time.perf_counter() - started) * 1_000


def main() -> None:
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(one, range(REQUESTS)))
    statuses: dict[int, int] = {}
    for status, _ in results:
        statuses[status] = statuses.get(status, 0) + 1
    latencies = sorted(latency for _, latency in results)
    p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)]
    print({
        "requests": REQUESTS,
        "workers": WORKERS,
        "statuses": statuses,
        "mean_ms": round(statistics.mean(latencies), 1),
        "p95_ms": round(p95, 1),
        "max_ms": round(max(latencies), 1),
    })
    if any(status != 200 for status, _ in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

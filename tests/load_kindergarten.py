"""Small HTTP concurrency probe for a deployed kindergarten API.

This is a smoke/load probe, not a claim of million-user capacity. Run it first
against staging and increase concurrency gradually while watching database
connections, p95 latency, CPU, memory and error rate.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def request_once(url: str, timeout: float) -> tuple[bool, float, int]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            response.read()
            status = response.status
            ok = 200 <= status < 300
    except urllib.error.HTTPError as error:
        status = error.code
        ok = False
    except Exception:
        status = 0
        ok = False
    return ok, (time.perf_counter() - started) * 1000, status


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction)))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()

    if args.requests < 1 or args.concurrency < 1:
        parser.error("requests va concurrency 1 dan katta bo'lsin")
    if args.concurrency > 500:
        parser.error("Bir bosqichda 500 dan yuqori concurrency xavfli")

    url = f"{args.base_url.rstrip('/')}/api/bogcha-v2/health"
    results = []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(request_once, url, args.timeout)
            for _ in range(args.requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())

    elapsed = time.perf_counter() - started
    latencies = [item[1] for item in results]
    success = sum(1 for item in results if item[0])
    statuses: dict[int, int] = {}
    for _, _, status in results:
        statuses[status] = statuses.get(status, 0) + 1

    report = {
        "url": url,
        "requests": len(results),
        "concurrency": args.concurrency,
        "success": success,
        "error_rate_percent": round((len(results) - success) * 100 / len(results), 2),
        "requests_per_second": round(len(results) / elapsed, 2),
        "latency_ms": {
            "mean": round(statistics.mean(latencies), 2),
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "p99": round(percentile(latencies, 0.99), 2),
            "max": round(max(latencies), 2),
        },
        "statuses": statuses,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["error_rate_percent"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

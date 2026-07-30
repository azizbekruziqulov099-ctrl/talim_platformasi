#!/usr/bin/env python3
"""Maktab v2 staging API uchun xavfsiz, faqat GET ishlatadigan yuk sinovi.

Bu kichik probe million foydalanuvchi sig'imini isbotlamaydi. Avval stagingda
past concurrency bilan ishlating va API/DB CPU, xotira, connection pool hamda
p95/p99 ko'rsatkichlarini birga kuzating. Skript hech qanday yozuvchi endpointni
chaqirmaydi.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any


MAX_CONCURRENCY = 200
MAX_REQUESTS = 100_000
MAX_TIMEOUT_SECONDS = 60.0
MAX_RESPONSE_BYTES = 1_048_576
API_PREFIX = "/api/maktab-v2"


@dataclass(frozen=True)
class Target:
    name: str
    url: str
    authenticated: bool


@dataclass(frozen=True)
class ProbeResult:
    target: str
    ok: bool
    latency_ms: float
    status: int
    error: str | None = None


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Do not forward the Bearer header to an unexpected redirect host."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def percentile(values: list[float], fraction: float) -> float:
    """Linearly interpolated percentile for a non-empty or empty sample."""

    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def normalize_base_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base-url http:// yoki https:// bilan to'liq yozilsin")
    if parsed.username or parsed.password:
        raise ValueError("base-url ichiga login yoki maxfiy ma'lumot yozmang")
    if parsed.query or parsed.fragment:
        raise ValueError("base-url query yoki fragment olmasligi kerak")
    path = parsed.path.rstrip("/")
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, path, "", "")
    )


def api_url(base_url: str, path: str, query: dict[str, Any] | None = None) -> str:
    encoded = urllib.parse.urlencode(
        {
            key: value
            for key, value in (query or {}).items()
            if value is not None and value != ""
        }
    )
    return f"{base_url}{API_PREFIX}{path}" + (f"?{encoded}" if encoded else "")


def request_once(
    target: Target,
    *,
    token: str | None,
    timeout: float,
) -> ProbeResult:
    headers = {
        "Accept": "application/json",
        "User-Agent": "SamTM-School-Staging-Probe/1.0",
    }
    if target.authenticated:
        if not token:
            return ProbeResult(target.name, False, 0.0, 0, "missing_token")
        headers["Authorization"] = "Bearer " + token

    request = urllib.request.Request(
        target.url,
        headers=headers,
        method="GET",
    )
    started = time.perf_counter()
    try:
        opener = urllib.request.build_opener(NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
            status = int(response.status)
            if len(payload) > MAX_RESPONSE_BYTES:
                return ProbeResult(
                    target.name,
                    False,
                    (time.perf_counter() - started) * 1000,
                    status,
                    "response_too_large",
                )
            ok = 200 <= status < 300
            error = None if ok else f"http_{status}"
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        ok = False
        error = f"http_{status}"
    except urllib.error.URLError as exc:
        status = 0
        ok = False
        error = type(exc.reason).__name__
    except TimeoutError:
        status = 0
        ok = False
        error = "timeout"
    except Exception as exc:  # Probe davom etib, yig'ma hisobot berishi kerak.
        status = 0
        ok = False
        error = type(exc).__name__
    return ProbeResult(
        target.name,
        ok,
        (time.perf_counter() - started) * 1000,
        status,
        error,
    )


def discover_context_id(
    base_url: str,
    token: str,
    timeout: float,
) -> int:
    target = Target(
        "workspaces",
        api_url(base_url, "/workspaces"),
        authenticated=True,
    )
    request = urllib.request.Request(
        target.url,
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + token,
            "User-Agent": "SamTM-School-Staging-Probe/1.0",
        },
        method="GET",
    )
    opener = urllib.request.build_opener(NoRedirectHandler())
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise RuntimeError("workspaces javobi juda katta")
        payload = json.loads(raw.decode("utf-8"))

    workspaces = payload.get("workspaces") or payload.get("items") or []
    active = [
        item
        for item in workspaces
        if (item.get("onboarding_status") or item.get("status")) == "active"
        and not (
            item.get("ownership_type") == "public"
            and item.get("verification_status") == "pending"
        )
    ]
    if not active:
        raise RuntimeError(
            "Token uchun faol maktab topilmadi; --context-id ni aniq bering"
        )
    context_id = active[0].get("context_id") or active[0].get("id")
    if not isinstance(context_id, int) or context_id < 1:
        raise RuntimeError("workspaces javobida context_id noto'g'ri")
    return context_id


def build_targets(
    base_url: str,
    mode: str,
    context_id: int | None,
) -> list[Target]:
    targets = {
        "health": Target(
            "health",
            api_url(base_url, "/health"),
            authenticated=False,
        ),
        "workspaces": Target(
            "workspaces",
            api_url(base_url, "/workspaces"),
            authenticated=True,
        ),
    }
    if context_id is not None:
        targets["dashboard"] = Target(
            "dashboard",
            api_url(base_url, "/dashboard", {"context_id": context_id}),
            authenticated=True,
        )
    if mode == "mixed":
        required = ["health", "workspaces", "dashboard"]
        missing = [name for name in required if name not in targets]
        if missing:
            raise ValueError(f"Target tayyor emas: {', '.join(missing)}")
        return [targets[name] for name in required]
    if mode not in targets:
        raise ValueError(f"{mode} uchun context-id kerak")
    return [targets[mode]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Maktab v2 staging health/workspaces/dashboard GET yuk sinovi"
        )
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("SCHOOL_BASE_URL"),
        help="Staging backend URL (yoki SCHOOL_BASE_URL)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("SCHOOL_BEARER_TOKEN"),
        help="Bearer token (yoki SCHOOL_BEARER_TOKEN); URLga qo'shilmaydi",
    )
    parser.add_argument(
        "--context-id",
        type=int,
        default=(
            int(os.environ["SCHOOL_CONTEXT_ID"])
            if os.getenv("SCHOOL_CONTEXT_ID")
            else None
        ),
        help="Maktab context ID (yoki SCHOOL_CONTEXT_ID); bo'lmasa topiladi",
    )
    parser.add_argument(
        "--endpoint",
        choices=("mixed", "health", "workspaces", "dashboard"),
        default="mixed",
    )
    parser.add_argument("--requests", type=int, default=300)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument(
        "--max-error-rate",
        type=float,
        default=0.0,
        help="Qabul qilinadigan xato foizi (0-100)",
    )
    args = parser.parse_args()

    if not args.base_url:
        parser.error("--base-url yoki SCHOOL_BASE_URL kerak")
    if not 1 <= args.requests <= MAX_REQUESTS:
        parser.error(f"--requests 1..{MAX_REQUESTS} oralig'ida bo'lsin")
    if not 1 <= args.concurrency <= MAX_CONCURRENCY:
        parser.error(
            f"--concurrency 1..{MAX_CONCURRENCY} oralig'ida bo'lsin"
        )
    if not 0.1 <= args.timeout <= MAX_TIMEOUT_SECONDS:
        parser.error(
            f"--timeout 0.1..{MAX_TIMEOUT_SECONDS:g} oralig'ida bo'lsin"
        )
    if not 0 <= args.max_error_rate <= 100:
        parser.error("--max-error-rate 0..100 oralig'ida bo'lsin")
    if args.context_id is not None and args.context_id < 1:
        parser.error("--context-id musbat bo'lsin")
    if args.endpoint != "health" and not args.token:
        parser.error(
            "workspaces/dashboard uchun --token yoki SCHOOL_BEARER_TOKEN kerak"
        )
    return args


def main() -> int:
    args = parse_args()
    try:
        base_url = normalize_base_url(args.base_url)
        context_id = args.context_id
        if args.endpoint in {"mixed", "dashboard"} and context_id is None:
            context_id = discover_context_id(
                base_url,
                args.token,
                args.timeout,
            )
        targets = build_targets(base_url, args.endpoint, context_id)
    except (ValueError, RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Sozlash xatosi: {exc}") from exc

    started = time.perf_counter()
    results: list[ProbeResult] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(
                request_once,
                targets[index % len(targets)],
                token=args.token,
                timeout=args.timeout,
            )
            for index in range(args.requests)
        ]
        for future in as_completed(futures):
            results.append(future.result())
    elapsed = max(time.perf_counter() - started, 0.000001)

    latencies = [item.latency_ms for item in results]
    successes = sum(item.ok for item in results)
    failures = len(results) - successes
    error_rate = failures * 100.0 / len(results)
    statuses = Counter(str(item.status) for item in results)
    errors = Counter(item.error for item in results if item.error)
    per_target: dict[str, dict[str, Any]] = {}
    for target in targets:
        sample = [item for item in results if item.target == target.name]
        sample_latency = [item.latency_ms for item in sample]
        per_target[target.name] = {
            "requests": len(sample),
            "success": sum(item.ok for item in sample),
            "error_rate_percent": round(
                sum(not item.ok for item in sample) * 100.0 / len(sample),
                3,
            ),
            "latency_ms": {
                "p50": round(percentile(sample_latency, 0.50), 2),
                "p95": round(percentile(sample_latency, 0.95), 2),
                "p99": round(percentile(sample_latency, 0.99), 2),
            },
        }

    report = {
        "base_url": base_url,
        "mode": args.endpoint,
        "context_id": context_id,
        "read_only": True,
        "requests": len(results),
        "concurrency": args.concurrency,
        "success": successes,
        "error_rate_percent": round(error_rate, 3),
        "requests_per_second": round(len(results) / elapsed, 2),
        "latency_ms": {
            "mean": round(statistics.fmean(latencies), 2),
            "p50": round(percentile(latencies, 0.50), 2),
            "p95": round(percentile(latencies, 0.95), 2),
            "p99": round(percentile(latencies, 0.99), 2),
            "max": round(max(latencies), 2),
        },
        "statuses": dict(sorted(statuses.items())),
        "errors": dict(sorted(errors.items())),
        "targets": per_target,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if error_rate <= args.max_error_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())

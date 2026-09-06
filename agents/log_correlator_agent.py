"""
Log Correlator Agent -- Step 1 of the Phase 1 multi-agent pipeline.

Design decision (same principle as the Logistics Agent in the trip-planner
project): parsing and counting structured log lines is arithmetic/pattern
matching, not reasoning, so this agent is deterministic Python rather than
an LLM call. This keeps its output exactly reproducible and reserves the
LLM call for the genuinely judgment-based step (Hypothesis Agent).

Produces a compact structured summary of the raw log -- error counts by
type, latency statistics, and the range of request ids where errors
clustered -- which is what gets passed to the Hypothesis Agent instead of
the raw log text. This is also what should make the two-stage pipeline
more efficient on longer logs in later phases: the Hypothesis Agent reads
a short summary instead of the full raw text.
"""

import re
import statistics

LOG_LINE_OK = re.compile(
    r"request_id=(?P<request_id>\d+) latency_ms=(?P<latency_ms>[\d.]+) status=OK"
)
LOG_LINE_ERROR = re.compile(
    r"request_id=(?P<request_id>\d+) status=ERROR error_type=(?P<error_type>\S+) "
    r"message=\"(?P<message>[^\"]*)\""
)


def correlate(log_text: str) -> dict:
    ok_requests = []
    error_requests = []

    for line in log_text.strip().splitlines():
        ok_match = LOG_LINE_OK.search(line)
        if ok_match:
            ok_requests.append({
                "request_id": int(ok_match.group("request_id")),
                "latency_ms": float(ok_match.group("latency_ms")),
            })
            continue
        error_match = LOG_LINE_ERROR.search(line)
        if error_match:
            error_requests.append({
                "request_id": int(error_match.group("request_id")),
                "error_type": error_match.group("error_type"),
                "message": error_match.group("message"),
            })

    total_requests = len(ok_requests) + len(error_requests)
    error_type_counts = {}
    for e in error_requests:
        error_type_counts[e["error_type"]] = error_type_counts.get(e["error_type"], 0) + 1

    latencies = [r["latency_ms"] for r in ok_requests]

    error_request_ids = sorted(e["request_id"] for e in error_requests)

    summary = {
        "total_requests": total_requests,
        "ok_count": len(ok_requests),
        "error_count": len(error_requests),
        "error_type_counts": error_type_counts,
        "error_request_ids": error_request_ids,
        "sample_error_messages": list({e["message"] for e in error_requests})[:3],
        "latency_ms_mean": round(statistics.mean(latencies), 1) if latencies else None,
        "latency_ms_max": round(max(latencies), 1) if latencies else None,
        "latency_ms_p90": round(_percentile(latencies, 0.9), 1) if latencies else None,
    }
    return summary


def _percentile(values: list, pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(round(pct * (len(sorted_vals) - 1)))
    return sorted_vals[idx]

#!/usr/bin/env python3
"""
generate_logs.py -- simulates N requests through the toy service, injecting
the specified fault, and writes a timestamped log file plus a separate
ground-truth metadata file.

Usage:
    python generate_logs.py --fault-type dependency_down --run-id 1 \\
        --out logs/dependency_down_run1.log \\
        --meta logs/dependency_down_run1.meta.json

The metadata file (ground truth) is intentionally kept separate from the
log file itself, since the diagnosis agents (Phase 0 and Phase 1) are
only ever given the .log file's contents.
"""

import argparse
import datetime
import json

from toy_service import mock_dependency_call, FAULT_TYPES


def generate(fault_type: str, run_id: int, num_requests: int = 30) -> tuple[str, dict]:
    if fault_type not in FAULT_TYPES:
        raise ValueError(f"fault_type must be one of {FAULT_TYPES}, got {fault_type!r}")

    start_time = datetime.datetime(2026, 1, 1, 9, 0, 0)
    lines = []

    for request_id in range(num_requests):
        ts = start_time + datetime.timedelta(seconds=request_id * 2)
        try:
            result = mock_dependency_call(fault_type, request_id, seed=run_id)
            line = (
                f"{ts.isoformat()} request_id={request_id} "
                f"latency_ms={result['latency_ms']:.1f} status=OK"
            )
        except Exception as e:
            line = (
                f"{ts.isoformat()} request_id={request_id} "
                f"status=ERROR error_type={type(e).__name__} message=\"{e}\""
            )
        lines.append(line)

    log_text = "\n".join(lines) + "\n"
    meta = {
        "fault_type": fault_type,
        "run_id": run_id,
        "num_requests": num_requests,
    }
    return log_text, meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fault-type", required=True, choices=FAULT_TYPES)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--num-requests", type=int, default=30)
    parser.add_argument("--out", required=True, help="Path to write the .log file")
    parser.add_argument("--meta", required=True, help="Path to write the .meta.json ground-truth file")
    args = parser.parse_args()

    log_text, meta = generate(args.fault_type, args.run_id, args.num_requests)

    with open(args.out, "w") as f:
        f.write(log_text)
    with open(args.meta, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Wrote {args.out} ({args.num_requests} requests, fault_type={args.fault_type})")
    print(f"Ground truth: {args.meta}")


if __name__ == "__main__":
    main()

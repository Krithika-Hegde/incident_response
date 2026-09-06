"""
toy_service.py -- a self-contained, function-level simulation of a service
handling requests through a mock dependency (e.g. a database).

Deliberately NOT a real HTTP server or database: fault injection is
request-id-based and fully deterministic (no real time.sleep, no real
concurrency), so generated logs are exactly reproducible across runs.
This trades some realism for reproducibility, which is called out
explicitly in the proposal (Section 7) as a known limitation to revisit
if time allows.

Fault taxonomy (see proposal Section 2):
  - dependency_down : mock dependency raises ConnectionRefusedError on a
                       recurring subset of requests (every 3rd request)
  - slow_query       : mock dependency returns abnormally high latency on
                       a recurring subset of requests (every 2nd request)
  - pool_exhausted   : mock dependency raises a pool-exhaustion error for
                       a contiguous "burst" range of request ids, simulating
                       a spike in concurrent traffic exceeding a fixed pool
                       limit
  - no_fault         : control condition, every request succeeds with
                       normal latency
"""

import random

FAULT_TYPES = ["dependency_down", "slow_query", "pool_exhausted", "no_fault"]

# Deterministic injection parameters. Kept simple and documented rather
# than trying to simulate "real" timing/concurrency.
DEPENDENCY_DOWN_EVERY_N = 3
SLOW_QUERY_EVERY_N = 2
SLOW_QUERY_LATENCY_RANGE_MS = (800, 1500)
NORMAL_LATENCY_RANGE_MS = (20, 80)
POOL_LIMIT = 5
POOL_BURST_START = 10
POOL_BURST_END = 15  # exclusive; requests in [10, 15) fail during the burst


class PoolExhaustedError(Exception):
    pass


def mock_dependency_call(fault_type: str, request_id: int, seed: int = 0) -> dict:
    """
    Simulates one call to a downstream dependency (e.g. a database).
    Raises an exception on injected-fault requests; otherwise returns a
    dict with a simulated latency in milliseconds.
    """
    rng = random.Random(seed * 10_000 + request_id)  # deterministic per (seed, request_id)

    if fault_type == "dependency_down" and request_id % DEPENDENCY_DOWN_EVERY_N == 0:
        raise ConnectionRefusedError(
            "Could not connect to downstream dependency at db.internal:5432"
        )

    if fault_type == "pool_exhausted" and POOL_BURST_START <= request_id < POOL_BURST_END:
        raise PoolExhaustedError(
            f"No available connections in pool (limit={POOL_LIMIT}, "
            f"active=6+ during burst)"
        )

    if fault_type == "slow_query" and request_id % SLOW_QUERY_EVERY_N == 0:
        latency_ms = rng.uniform(*SLOW_QUERY_LATENCY_RANGE_MS)
        return {"latency_ms": latency_ms}

    latency_ms = rng.uniform(*NORMAL_LATENCY_RANGE_MS)
    return {"latency_ms": latency_ms}

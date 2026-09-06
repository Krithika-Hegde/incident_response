"""
Runbook Agent -- Step 3 of the Phase 1 multi-agent pipeline.

Design decision: matching a classified fault type to a fixed remediation
step is a table lookup, not a reasoning task, so this agent is
deterministic Python rather than an LLM call -- same principle as the Log
Correlator. This also means the pipeline's total LLM call count is 1 (the
Hypothesis Agent only), matching the single-agent Phase 0 baseline's call
count of 1, which keeps the Phase 0-vs-Phase 1 comparison's "coordination
overhead" honest: any accuracy difference is not simply bought with more
API calls.
"""

RUNBOOK = {
    "dependency_down": (
        "Check downstream dependency health/connectivity (e.g. `ping` or "
        "`telnet` to the dependency host and port). If confirmed down, "
        "fail over to a backup instance or escalate to the dependency's "
        "on-call owner."
    ),
    "slow_query": (
        "Check the dependency's query plan / slow-query log for the "
        "affected time window. Consider adding an index, or temporarily "
        "enabling a cache in front of the slow path."
    ),
    "pool_exhausted": (
        "Check current connection pool usage against its configured limit. "
        "Temporarily raise the pool limit if headroom exists, or identify "
        "and fix a connection leak if usage stays elevated after traffic "
        "subsides."
    ),
    "no_fault": (
        "No remediation needed -- logs show normal operation."
    ),
}


def get_remediation(predicted_fault: str) -> str:
    return RUNBOOK.get(
        predicted_fault,
        f"No runbook entry for fault type '{predicted_fault}'; escalate to on-call for manual triage.",
    )

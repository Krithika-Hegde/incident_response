# Test Case: Baseline Execution and Output

## Sample Test Case

**Input:** `logs/dependency_down_run1.log`

This log file contains 30 simulated requests where the dependency fails on every 3rd request (requests 0, 3, 6, 9, ... 27) with a `ConnectionRefusedError`, simulating a downstream database connection failure.

## Phase 0 Baseline Output (Single-Agent)

**Command:** `python diagnose.py --log logs/dependency_down_run1.log`

**Output:**
```json
{
  "predicted_fault": "dependency_down",
  "explanation": "Roughly one third of requests fail with error_type=ConnectionRefusedError and message 'Could not connect to downstream dependency at db.internal:5432' (request_id=0, 3, 6, 9, ... 27), while successful requests show normal latencies (~28-68 ms). This indicates the downstream database dependency is refusing connections, not latency degradation or connection pool saturation (no pool wait/timeout messages).",
  "confidence": 0.94
}
```

**Result:** ✅ **CORRECT** - Correctly identified `dependency_down` with high confidence (0.94)

---

## Phase 1 Pipeline Output (Multi-Agent)

**Command:** `python run_pipeline.py --log logs/dependency_down_run1.log`

**Output:**
```json
{
  "log_summary": {
    "total_requests": 30,
    "ok_count": 20,
    "error_count": 10,
    "error_type_counts": {
      "ConnectionRefusedError": 10
    },
    "error_request_ids": [0, 3, 6, 9, 12, 15, 18, 21, 24, 27],
    "sample_error_messages": ["Could not connect to downstream dependency at db.internal:5432"],
    "latency_ms_mean": 47.7,
    "latency_ms_max": 68.0,
    "latency_ms_p90": 63.6
  },
  "predicted_fault": "dependency_down",
  "explanation": "All 10 errors are ConnectionRefusedError with the message 'Could not connect to downstream dependency at db.internal:5432', which directly indicates an unreachable downstream service. Latency stats are normal (mean 47.7ms, p90 63.6ms, max 68.0ms), ruling out slow_query, and there are no pool/timeout-acquire errors that would indicate pool_exhausted. The errors are spread evenly (every 3rd request id: 0,3,6,...,27) rather than in a contiguous burst, suggesting a persistent partial/intermittent dependency outage rather than a transient spike, but the fault type is clearly dependency-related and not no_fault (33% error rate).",
  "confidence": 0.9,
  "ranked_alternatives": [
    {"fault_type": "dependency_down", "confidence": 0.9},
    {"fault_type": "pool_exhausted", "confidence": 0.06},
    {"fault_type": "slow_query", "confidence": 0.02},
    {"fault_type": "no_fault", "confidence": 0.02}
  ],
  "remediation": "Check downstream dependency health/connectivity (e.g. `ping` or `telnet` to the dependency host and port). If confirmed down, fail over to a backup instance or escalate to the dependency's on-call owner.",
  "agent_call_log": ["log_correlator (deterministic)", "hypothesis_agent (LLM)", "runbook_agent (deterministic)"],
  "llm_call_count": 1
}
```

**Result:** ✅ **CORRECT** - Correctly identified `dependency_down` with confidence 0.9 and provided detailed ranked alternatives and remediation step

---

## How to Reproduce

### Prerequisites
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### Run Phase 0 Baseline
```bash
python diagnose.py --log logs/dependency_down_run1.log
```

### Run Phase 1 Pipeline
```bash
python run_pipeline.py --log logs/dependency_down_run1.log
```

### Run Full Evaluation (16 logs)
```bash
python evaluate.py --logs-dir logs/ --output outputs/comparison_results.csv
```

---

## Evaluation Results Summary

Both conditions were tested on 16 logs (4 runs × 4 fault types):

| Metric | Single-Agent | Multi-Agent |
|--------|--------------|-------------|
| Overall Accuracy | 100% (16/16) | 100% (16/16) |
| False-Positive Rate | 0% (0/4 controls) | 0% (0/4 controls) |
| LLM Calls | 1 per log | 1 per log |

### Per-Fault-Type Breakdown
- **dependency_down**: 4/4 correct (confidence: 0.94 single, 0.91 pipeline)
- **pool_exhausted**: 4/4 correct (confidence: 0.97 single, 0.94 pipeline)
- **slow_query**: 4/4 correct (confidence: 0.81 single, 0.73 pipeline)
- **no_fault**: 4/4 correct (confidence: 0.95 single, 0.96 pipeline)

See `outputs/comparison_results.csv` for detailed results.

#!/usr/bin/env python3
"""
run_pipeline.py -- Phase 1 multi-agent pipeline: Log Correlator (deterministic)
-> Hypothesis Agent (1 LLM call) -> Runbook Agent (deterministic lookup).

This is the condition being compared against the Phase 0 single-agent
baseline (diagnose.py). Both conditions make exactly 1 LLM call, so any
accuracy difference reflects the pipeline's structure (giving the
reasoning step a pre-parsed, structured summary instead of raw log text)
rather than simply spending more API budget.

Usage:
    python run_pipeline.py --log logs/dependency_down_run1.log
"""

import argparse
import json

from agents.log_correlator_agent import correlate
from agents.hypothesis_agent import generate_hypothesis
from agents.runbook_agent import get_remediation


def run_pipeline(log_text: str) -> dict:
    agent_call_log = []

    # Step 1: Log Correlator (deterministic, no LLM call).
    summary = correlate(log_text)
    agent_call_log.append("log_correlator (deterministic)")

    # Step 2: Hypothesis Agent (the one LLM call in this pipeline).
    hypothesis = generate_hypothesis(summary)
    agent_call_log.append("hypothesis_agent (LLM)")

    # Step 3: Runbook Agent (deterministic lookup, no LLM call).
    remediation = get_remediation(hypothesis["predicted_fault"])
    agent_call_log.append("runbook_agent (deterministic)")

    return {
        "log_summary": summary,
        "predicted_fault": hypothesis["predicted_fault"],
        "explanation": hypothesis["explanation"],
        "confidence": hypothesis["confidence"],
        "ranked_alternatives": hypothesis.get("ranked_alternatives", []),
        "remediation": remediation,
        "agent_call_log": agent_call_log,
        "llm_call_count": 1,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, help="Path to a .log file")
    args = parser.parse_args()

    with open(args.log) as f:
        log_text = f.read()

    result = run_pipeline(log_text)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

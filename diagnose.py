#!/usr/bin/env python3
"""
diagnose.py -- Phase 0 baseline: a single Claude call classifies the fault
type directly from raw log text. Kept in Phase 1 as the control condition
that the multi-agent pipeline (run_pipeline.py) is compared against.

Usage:
    python diagnose.py --log logs/dependency_down_run1.log
"""

import argparse
import json

from lib.claude_client import call_claude_json
from toy_service import FAULT_TYPES

SYSTEM_PROMPT = f"""You are an on-call diagnosis assistant. You will be given
raw log lines from a service and must classify what happened.

Classify into exactly one of these fault types: {FAULT_TYPES}
("no_fault" means the logs show normal operation with no incident.)

Respond with ONLY a JSON object, no other text, in this exact format:
{{
  "predicted_fault": "<one of {FAULT_TYPES}>",
  "explanation": "<short explanation citing specific log lines as evidence>",
  "confidence": <number between 0 and 1>
}}
"""


def diagnose_log(log_text: str) -> dict:
    user_prompt = f"Log contents:\n\n{log_text}\n\nRespond with ONLY the JSON object described in your instructions."
    return call_claude_json(SYSTEM_PROMPT, user_prompt, temperature=0.0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, help="Path to a .log file")
    args = parser.parse_args()

    with open(args.log) as f:
        log_text = f.read()

    result = diagnose_log(log_text)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

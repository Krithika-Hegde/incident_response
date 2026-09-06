"""
Hypothesis Agent -- Step 2 of the Phase 1 multi-agent pipeline.

Receives the Log Correlator's structured summary (NOT the raw log text)
and ranks candidate fault hypotheses with confidence scores. This is the
one genuinely judgment-based step in the pipeline -- distinguishing, for
example, a real dependency_down pattern (errors clustered evenly across
the whole run) from a pool_exhausted pattern (errors clustered in a
contiguous burst) requires interpreting the structured evidence, not just
counting it.
"""

from lib.claude_client import call_claude_json
from toy_service import FAULT_TYPES

SYSTEM_PROMPT = f"""You are the Hypothesis Agent in an incident-diagnosis
pipeline. You receive a STRUCTURED SUMMARY of a service's logs (already
parsed and counted for you by a separate Log Correlator step) and must
rank which fault type most likely occurred.

Fault types to choose from: {FAULT_TYPES}
("no_fault" means the summary shows normal operation with no incident.)

Use the evidence in the summary explicitly in your reasoning -- e.g. the
error type counts, whether errors are spread evenly across request ids or
clustered in a contiguous burst, and latency statistics.

Respond with ONLY a JSON object, no other text, in this exact format:
{{
  "predicted_fault": "<one of {FAULT_TYPES}>",
  "explanation": "<short explanation citing specific fields from the summary as evidence>",
  "confidence": <number between 0 and 1>,
  "ranked_alternatives": [{{"fault_type": "...", "confidence": <number>}}, ...]
}}
"""


def generate_hypothesis(log_summary: dict) -> dict:
    user_prompt = f"""Structured log summary:
{log_summary}

Respond with ONLY the JSON object described in your instructions."""
    return call_claude_json(SYSTEM_PROMPT, user_prompt, temperature=0.0)

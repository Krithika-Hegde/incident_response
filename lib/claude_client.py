"""
Thin wrapper around the Anthropic API for structured (JSON) agent calls.
Shared by both the Phase 0 single-agent baseline (diagnose.py) and the
Phase 1 multi-agent pipeline's Hypothesis Agent.
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        _client = Anthropic(api_key=api_key)
    return _client


def call_claude_json(system_prompt: str, user_prompt: str, temperature: float = 0.0,
                      model: str = "claude-opus-5", max_tokens: int = 1000) -> dict:
    """Call Claude and parse the response as JSON."""
    client = get_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    raw_text = "\n".join(text_parts).strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[len("json"):]
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Could not parse model response as JSON.\nRaw response:\n{raw_text}"
        ) from e

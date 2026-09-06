# Multi-Agent Incident Response via Controlled Fault Injection

## What's in this repo

- **Phase 0 baseline** (`diagnose.py`): a single Claude call classifies
  the fault type directly from raw log text. This remains the control
  condition in Phase 1.
- **Phase 1 pipeline** (`run_pipeline.py` + `agents/`): Log Correlator
  (deterministic parsing) → Hypothesis Agent (1 LLM call, reasons over
  the structured summary instead of raw text) → Runbook Agent
  (deterministic remediation lookup).
- **`evaluate.py`** runs BOTH conditions over every log in `logs/` and
  writes a side-by-side comparison CSV -- this is the actual Phase 1
  deliverable.

Both conditions make exactly **1 LLM call**, so any accuracy difference
in the results reflects the pipeline's structure (pre-parsed evidence vs.
raw text), not extra API budget spent.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then add your ANTHROPIC_API_KEY
```

## Generate logs

```bash
python generate_logs.py --fault-type dependency_down --run-id 1 \
    --out logs/dependency_down_run1.log --meta logs/dependency_down_run1.meta.json
```

Repeat for `slow_query`, `pool_exhausted`, and `no_fault`, with a few
different `--run-id` values each, to build up your evaluation set (the
proposal's Phase 0/1 plan uses 4 runs per fault type + 4 no_fault control
runs = 16 total).

## Run a single log through each condition

```bash
python diagnose.py --log logs/dependency_down_run1.log
python run_pipeline.py --log logs/dependency_down_run1.log
```

## Run the full comparison

```bash
python evaluate.py --logs-dir logs/ --output outputs/comparison_results.csv
```

Prints an accuracy summary (overall, fault-scenarios-only, false-positive
rate on `no_fault` controls, and a per-fault-type breakdown) and writes
`outputs/comparison_results.csv` with one row per log:
`log_id, true_fault, predicted_fault_single, correct_single,
confidence_single, predicted_fault_pipeline, correct_pipeline,
confidence_pipeline, llm_calls_single, llm_calls_pipeline`.

## Project structure

```
toy_service.py         # deterministic, request-id-based fault injection
generate_logs.py        # generates a .log + .meta.json (ground truth) pair
diagnose.py              # Phase 0: single-agent baseline
run_pipeline.py           # Phase 1: 3-agent pipeline orchestration
evaluate.py                # runs both conditions, writes comparison CSV
lib/
  claude_client.py          # shared Anthropic API wrapper
agents/
  log_correlator_agent.py    # deterministic log parsing/summarization
  hypothesis_agent.py         # the one LLM call: ranks fault hypotheses
  runbook_agent.py             # deterministic remediation lookup
logs/                           # generated .log/.meta.json pairs go here
outputs/                         # comparison_results.csv written here
```

## Design decisions worth knowing before reading the code

- **Fault injection is deterministic and request-id-based**, not a real
  server with real timing/concurrency (see `toy_service.py`'s docstring).
  This trades realism for exact reproducibility -- a known Phase 0/1
  limitation, flagged in the proposal as something to revisit if
  synthetic faults turn out to be too easy to classify.
- **Log Correlator and Runbook Agent are deterministic Python, not LLM
  calls.** Parsing/counting log lines and looking up a fixed remediation
  string are not reasoning tasks -- only the Hypothesis Agent's job
  (interpreting the structured evidence to pick a fault type) genuinely
  needs an LLM. This mirrors the same design principle used for the
  Logistics Agent in the trip-planning project.
- **`evaluate.py`'s CSV schema puts both conditions in the same row**
  (not two separate CSVs) specifically so accuracy, confidence, and call
  count can be compared per-log without a manual join step later.

#!/usr/bin/env python3
"""
evaluate.py -- Phase 1 comparison: runs BOTH the Phase 0 single-agent
baseline (diagnose.py) and the Phase 1 multi-agent pipeline
(run_pipeline.py) over every log in a directory, and writes a CSV with
both conditions' results side by side for direct comparison.

Usage:
    python evaluate.py --logs-dir logs/ --output outputs/comparison_results.csv
"""

import argparse
import csv
import glob
import json
import os

from diagnose import diagnose_log
from run_pipeline import run_pipeline


def find_log_pairs(logs_dir: str) -> list:
    """Returns a list of (log_path, meta_path) tuples for every .log file
    that has a matching .meta.json ground-truth file."""
    pairs = []
    for log_path in sorted(glob.glob(os.path.join(logs_dir, "*.log"))):
        meta_path = log_path.replace(".log", ".meta.json")
        if os.path.exists(meta_path):
            pairs.append((log_path, meta_path))
        else:
            print(f"⚠ Skipping {log_path}: no matching .meta.json ground-truth file found")
    return pairs


def evaluate(logs_dir: str, output_path: str):
    pairs = find_log_pairs(logs_dir)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        "log_id", "true_fault",
        "predicted_fault_single", "correct_single", "confidence_single",
        "predicted_fault_pipeline", "correct_pipeline", "confidence_pipeline",
        "llm_calls_single", "llm_calls_pipeline",
    ]

    rows = []
    for log_path, meta_path in pairs:
        with open(log_path) as f:
            log_text = f.read()
        with open(meta_path) as f:
            meta = json.load(f)

        true_fault = meta["fault_type"]
        log_id = os.path.basename(log_path).replace(".log", "")

        print(f"Evaluating {log_id} (true fault: {true_fault})...")

        single_result = diagnose_log(log_text)
        pipeline_result = run_pipeline(log_text)

        rows.append({
            "log_id": log_id,
            "true_fault": true_fault,
            "predicted_fault_single": single_result["predicted_fault"],
            "correct_single": single_result["predicted_fault"] == true_fault,
            "confidence_single": single_result["confidence"],
            "predicted_fault_pipeline": pipeline_result["predicted_fault"],
            "correct_pipeline": pipeline_result["predicted_fault"] == true_fault,
            "confidence_pipeline": pipeline_result["confidence"],
            "llm_calls_single": 1,
            "llm_calls_pipeline": pipeline_result["llm_call_count"],
        })

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} results to {output_path}")
    _print_summary(rows)


def _print_summary(rows: list):
    if not rows:
        print("No rows to summarize.")
        return

    def accuracy(rs, key):
        if not rs:
            return None
        return sum(1 for r in rs if r[key]) / len(rs)

    conflict_rows = [r for r in rows if r["true_fault"] != "no_fault"]
    control_rows = [r for r in rows if r["true_fault"] == "no_fault"]

    print("\n=== Overall accuracy ===")
    print(f"Single-agent baseline: {accuracy(rows, 'correct_single')}")
    print(f"Multi-agent pipeline:  {accuracy(rows, 'correct_pipeline')}")

    print("\n=== Accuracy on fault scenarios only ===")
    print(f"Single-agent baseline: {accuracy(conflict_rows, 'correct_single')}")
    print(f"Multi-agent pipeline:  {accuracy(conflict_rows, 'correct_pipeline')}")

    print("\n=== False-positive rate on no_fault control scenarios ===")
    print(f"Single-agent baseline: {1 - accuracy(control_rows, 'correct_single') if control_rows else None}")
    print(f"Multi-agent pipeline:  {1 - accuracy(control_rows, 'correct_pipeline') if control_rows else None}")

    print("\n=== Per-fault-type breakdown ===")
    fault_types = sorted(set(r["true_fault"] for r in rows))
    for ft in fault_types:
        ft_rows = [r for r in rows if r["true_fault"] == ft]
        print(f"  {ft}: single={accuracy(ft_rows, 'correct_single')}, "
              f"pipeline={accuracy(ft_rows, 'correct_pipeline')} (n={len(ft_rows)})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs-dir", default="logs")
    parser.add_argument("--output", default="outputs/comparison_results.csv")
    args = parser.parse_args()
    evaluate(args.logs_dir, args.output)


if __name__ == "__main__":
    main()

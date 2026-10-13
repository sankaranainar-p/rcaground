"""
rcaground/bench/baselines/__init__.py — Baseline registry for rcaground/bench/run_benchmark.py.

Every baseline implements the same interface: given a
rcaground.signals.types.FailureCase, return a ranked list of candidate root
cause services (best guess first), used to compute AC@k / Avg@5 against
the case's GroundTruth.root_cause_service.

    def rank(case: FailureCase) -> list[str]: ...

Baselines:
    B1  rcaground.bench.baselines.rules            — legacy threshold/rule-based ranking
    B2  rcaground.bench.baselines.rcaeval_baseline  — wraps RCAEval's own BARO baseline
    B3  (retired) — an ML triage baseline that depended on a domain-specific
                    trained classifier; the ID is kept unassigned so that
                    published result tables stay comparable.
    B4  rcaground.bench.baselines.single_prompt_llm — one-shot LLM prompt over case summary
    B5  rcaground.bench.baselines.openrca_agent     — OpenRCA-style agent, Bank cases only
"""

from __future__ import annotations

BASELINE_IDS = ("B1", "B2", "B4", "B5")

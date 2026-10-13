"""
rcaground/classifier/taxonomy.py — Single source of truth for the fault taxonomy
and SLI vocabulary used by alert synthesis and the evaluation harness.

The taxonomy lives in rcaground/data/taxonomy.yaml. `fault_class` values are drawn
only from RCAEval (RE1/RE2 resource and network faults, RE3 code-level
faults) and OpenRCA ground-truth labels; see that file's header comment for
provenance. "unknown" is not a ground-truth label and is appended in code as
a low-confidence fallback bucket.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import yaml

_TAXONOMY_PATH = Path(__file__).parent.parent / "data" / "taxonomy.yaml"

UNKNOWN_CATEGORY = "unknown"

_lock = threading.Lock()
_cache: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _cache
    if _cache is None:
        with _lock:
            if _cache is None:
                with _TAXONOMY_PATH.open() as fh:
                    _cache = yaml.safe_load(fh)
    return _cache


def fault_classes() -> list[str]:
    """Ground-truth fault_class values from rcaground/data/taxonomy.yaml."""
    return list(_load()["fault_class"])


def slis() -> list[str]:
    """SLI values from rcaground/data/taxonomy.yaml."""
    return list(_load()["sli"])


def sli_map() -> dict[str, dict[str, str]]:
    """Per-system service+metric -> SLI mapping from rcaground/data/taxonomy.yaml."""
    return dict(_load()["sli_map"])


def all_categories() -> list[str]:
    """fault_class values plus the operational 'unknown' fallback bucket.

    This is the category list both classifiers should train/predict/parse
    against.
    """
    return fault_classes() + [UNKNOWN_CATEGORY]

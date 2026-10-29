"""
tests/test_openrca_real_data.py — Runs the OpenRCA adapter against real
downloaded data. Skipped unless RCAGROUND_OPENRCA_ROOT points at a directory
containing `Telecom/` (see CONVERSION.md for how to fetch it); no data is
downloaded by the tests themselves.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from rcaground.signals.openrca import OpenRCAAdapter, _date_folder, evidence_window

_ROOT = os.environ.get("RCAGROUND_OPENRCA_ROOT")
_TELECOM = Path(_ROOT) / "Telecom" if _ROOT else None

pytestmark = pytest.mark.skipif(
    _TELECOM is None or not (_TELECOM / "record.csv").exists(),
    reason="set RCAGROUND_OPENRCA_ROOT to a directory containing Telecom/record.csv",
)


def _cases_with_downloaded_telemetry():
    adapter = OpenRCAAdapter(_ROOT, system="Telecom")
    record = pd.read_csv(adapter.record_csv)
    available = [
        i
        for i, ts in enumerate(record["timestamp"])
        if (adapter.telemetry_dir / _date_folder(float(ts), adapter._tz) / "metric").is_dir()
    ]
    if not available:
        pytest.skip("no telemetry date folder referenced by Telecom/record.csv has been downloaded")
    cases = list(adapter)
    return record, [(i, cases[i]) for i in available[:3]]


def test_telecom_real_cases_load_with_metrics_and_no_logs():
    record, cases = _cases_with_downloaded_telemetry()
    for i, (fc, gt) in cases:
        row = record.iloc[i]
        assert gt.root_cause_service == row["component"]
        assert gt.raw_fault_type == row["reason"].strip()
        assert gt.inject_time == int(row["timestamp"])
        assert fc.system == "openrca_telecom"
        assert fc.logs == []
        assert fc.metrics, f"{fc.case_id}: no metrics in evidence window"


def test_telecom_real_metric_times_fall_in_evidence_window():
    _, cases = _cases_with_downloaded_telemetry()
    for _, (fc, gt) in cases:
        start, end = evidence_window(gt.inject_time)
        for key, series in fc.metrics.items():
            assert ":" in key
            assert all(start <= t < end for t in series.times), key

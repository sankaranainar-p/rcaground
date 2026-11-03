"""
tests/test_openrca_real_data.py — Runs the OpenRCA adapter against real
downloaded data. Skipped unless RCAGROUND_OPENRCA_ROOT points at a directory
containing `Telecom/` and/or `Market/cloudbed-1/`, `Market/cloudbed-2/` (see
CONVERSION.md for how to fetch them); systems that are absent skip. No data is
downloaded by the tests themselves.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from rcaground.signals.openrca import OpenRCAAdapter, _date_folder, evidence_window, system_path

_ROOT = os.environ.get("RCAGROUND_OPENRCA_ROOT")
SYSTEMS = ["Telecom", "Market.cloudbed-1", "Market.cloudbed-2"]


@pytest.fixture(params=SYSTEMS)
def system(request):
    name = request.param
    if not _ROOT or not (Path(_ROOT) / system_path(name) / "record.csv").exists():
        pytest.skip(f"set RCAGROUND_OPENRCA_ROOT to a directory containing {system_path(name).as_posix()}/record.csv")
    return name


def _cases_with_downloaded_telemetry(system):
    adapter = OpenRCAAdapter(_ROOT, system=system)
    record = pd.read_csv(adapter.record_csv)
    available = [
        i
        for i, ts in enumerate(record["timestamp"])
        if (adapter.telemetry_dir / _date_folder(float(ts), adapter._tz) / "metric").is_dir()
    ]
    if not available:
        pytest.skip(f"no telemetry date folder referenced by {system} record.csv has been downloaded")
    cases = list(adapter)
    return record, [(i, cases[i]) for i in available[:3]]


def test_record_datetime_column_is_shanghai_time(system):
    record = pd.read_csv(OpenRCAAdapter(_ROOT, system=system).record_csv)
    local = pd.to_datetime(record["timestamp"], unit="s", utc=True).dt.tz_convert("Asia/Shanghai")
    assert local.dt.tz_localize(None).equals(pd.to_datetime(record["datetime"]))


def test_real_cases_load_with_metrics_and_no_logs(system):
    record, cases = _cases_with_downloaded_telemetry(system)
    prefix = f"openrca_{system.lower()}"
    for i, (fc, gt) in cases:
        row = record.iloc[i]
        assert gt.root_cause_service == row["component"]
        assert gt.raw_fault_type == row["reason"].strip()
        assert gt.inject_time == int(row["timestamp"])
        assert fc.system == prefix and "/" not in fc.case_id
        assert fc.logs == []
        assert fc.metrics, f"{fc.case_id}: no metrics in evidence window"


def test_real_metric_times_fall_in_evidence_window(system):
    _, cases = _cases_with_downloaded_telemetry(system)
    for _, (fc, gt) in cases:
        start, end = evidence_window(gt.inject_time)
        for key, series in fc.metrics.items():
            assert ":" in key
            assert all(start <= t < end for t in series.times), key

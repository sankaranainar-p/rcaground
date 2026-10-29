"""
tests/test_openrca_telecom_adapter.py — Tests for the Telecom layout of
rcaground/signals/openrca.py against the SYNTHETIC fixture in
tests/fixtures/openrca_telecom_synthetic/ (real Telecom headers, column
formats and directory layout, invented values; see tests/fixtures/README.md).
Tests against real downloaded data are in tests/test_openrca_real_data.py.
"""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pandas as pd

from rcaground.signals.openrca import (
    LAYOUTS,
    OpenRCAAdapter,
    _date_folder,
    _load_logs,
    _load_traces,
    evidence_window,
)
from rcaground.signals.types import FailureCase, GroundTruth

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "openrca_telecom_synthetic"

RECORD_TIMESTAMPS = [1586535120, 1586540820, 1586545500]


def _load() -> list[tuple[FailureCase, GroundTruth]]:
    return list(OpenRCAAdapter(FIXTURE_ROOT, system="Telecom"))


def test_layout_is_verified_and_has_no_log_or_trace_path():
    lay = LAYOUTS["Telecom"]
    assert lay.verified and lay.timezone == "Asia/Shanghai"
    assert lay.log is None and lay.trace is None
    assert lay.metric_time_unit == "ms"


def test_fixture_yields_three_cases():
    assert len(_load()) == 3


def test_case_ids_and_labels():
    cases = _load()
    assert [fc.case_id for fc, _ in cases] == [
        "OpenRCA-Telecom_0_docker_003",
        "OpenRCA-Telecom_1_db_007",
        "OpenRCA-Telecom_2_docker_005",
    ]
    fc, _ = cases[0]
    assert fc.system == "openrca_telecom"
    assert fc.dataset == "OpenRCA-Telecom"


def test_ground_truth_matches_record_csv_verbatim():
    expected = [
        ("docker_003", "CPU fault", "cpu"),
        ("db_007", "db connection limit", "dependency_failure"),
        ("docker_005", "network loss", "loss"),
    ]
    for (_, gt), (component, reason, fault_type), ts in zip(_load(), expected, RECORD_TIMESTAMPS):
        assert gt.root_cause_service == component
        assert gt.raw_fault_type == reason
        assert gt.fault_type == fault_type
        assert gt.inject_time == ts


def test_date_folder_uses_shanghai_date_not_utc_date():
    """Every fixture record is on 2020-04-10 in UTC but 2020-04-11 in UTC+8,
    as is every record in the real Telecom record.csv."""
    for ts in RECORD_TIMESTAMPS:
        assert pd.Timestamp(ts, unit="s", tz="UTC").strftime("%Y_%m_%d") == "2020_04_10"
        assert _date_folder(ts) == "2020_04_11"


def _shanghai_hhmm(unix_seconds: int) -> str:
    return pd.Timestamp(unix_seconds, unit="s", tz="UTC").tz_convert("Asia/Shanghai").strftime("%H:%M")


def test_evidence_windows_are_shanghai_half_hours():
    expected = [("00:00", "00:30"), ("01:30", "02:00"), ("03:00", "03:30")]
    for ts, (start_str, end_str) in zip(RECORD_TIMESTAMPS, expected):
        start, end = evidence_window(ts)
        assert (_shanghai_hhmm(start), _shanghai_hhmm(end)) == (start_str, end_str)


def test_no_logs_and_no_spans_without_error():
    for fc, _ in _load():
        assert fc.logs == []
        assert fc.traces == []
        assert isinstance(fc.topology, nx.DiGraph) and fc.topology.number_of_nodes() == 0


def test_missing_log_and_trace_paths_return_nothing():
    assert _load_logs(None, 0, 10) == []
    assert _load_traces(None, 0, 10) == []


def test_metric_keys_come_from_container_and_app_files():
    fc, _ = _load()[0]
    assert set(fc.metrics) == {
        f"{cmdb}:{kpi}"
        for cmdb in ("docker_003", "docker_005")
        for kpi in ("container_cpu_used", "container_thread_used_pct")
    } | {f"app.osb_001:{kpi}" for kpi in ("avg_time", "num", "succee_num", "succee_rate")}


def test_millisecond_timestamps_are_converted_to_seconds_within_window():
    for fc, gt in _load():
        start, end = evidence_window(gt.inject_time)
        for key, series in fc.metrics.items():
            assert all(start <= t < end for t in series.times), key
            assert set(b - a for a, b in zip(series.times, series.times[1:])) <= {1}


def test_first_samples_land_on_the_expected_second():
    fc, gt = _load()[0]
    start, _ = evidence_window(gt.inject_time)
    assert fc.metrics["docker_003:container_cpu_used"].times[0] == start + 2
    assert fc.metrics["app.osb_001:num"].times[0] == start


def test_samples_just_outside_the_window_are_excluded():
    for fc, _ in _load():
        assert 77.0 not in fc.metrics["docker_003:container_cpu_used"].values
        assert 99.0 not in fc.metrics["app.osb_001:avg_time"].values


def test_forward_fill_flags_mark_one_real_sample_per_minute():
    fc, _ = _load()[0]
    series = fc.metrics["docker_003:container_cpu_used"]
    assert series.is_forward_filled is not None
    assert sum(1 for f in series.is_forward_filled if not f) == 30
    assert len(series.is_forward_filled) == len(series.times) == len(series.values)


def test_fault_is_visible_in_the_faulted_components_metrics():
    fc, _ = _load()[0]
    assert fc.metrics["docker_003:container_cpu_used"].values[-1] == 90.0
    assert fc.metrics["docker_005:container_cpu_used"].values[-1] < 20.0

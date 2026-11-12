"""
tests/test_openrca_market_adapter.py — Tests for the Market sub-environment
layouts of rcaground/signals/openrca.py against the SYNTHETIC fixture in
tests/fixtures/openrca_market_synthetic/ (real Market headers, column formats
and directory layout, invented values; see tests/fixtures/README.md).
Tests against real downloaded data are in tests/test_openrca_real_data.py.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from rcaground.signals.openrca import (
    LAYOUTS,
    OpenRCAAdapter,
    _date_folder,
    evidence_window,
    get_layout,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "openrca_market_synthetic"
ENVS = ["Market.cloudbed-1", "Market.cloudbed-2"]

TIMESTAMPS = {
    "Market.cloudbed-1": [1647706800, 1647738546, 1647743133],
    "Market.cloudbed-2": [1647705900, 1647739015, 1647744000],
}
COMPONENTS = {
    "Market.cloudbed-1": ["shippingservice-1", "adservice", "node-1"],
    "Market.cloudbed-2": ["recommendationservice2-0", "cartservice2-0", "node-6"],
}
FAULT_TYPES = {
    "Market.cloudbed-1": ["cpu", "memory", "memory"],
    "Market.cloudbed-2": ["cpu", "delay", "cpu"],
}


def _load(system):
    return list(OpenRCAAdapter(FIXTURE_ROOT, system=system))


@pytest.mark.parametrize("system", ENVS)
def test_layout_is_verified_with_service_metrics_and_no_log_or_trace(system):
    lay = LAYOUTS[system]
    assert lay.verified and lay.timezone == "Asia/Shanghai"
    assert lay.metric_time_unit == "s"
    assert lay.metric_container == "metric/metric_container.csv"
    assert lay.metric_app == "metric/metric_service.csv"
    assert lay.log is None and lay.trace is None


def test_parent_system_has_no_layout():
    with pytest.raises(NotImplementedError):
        get_layout("Market")


def test_slash_input_is_normalised():
    a = OpenRCAAdapter(FIXTURE_ROOT, system="Market/cloudbed-1")
    assert (a.system_name, a.system, a.dataset) == (
        "Market.cloudbed-1",
        "openrca_market.cloudbed-1",
        "OpenRCA-Market.cloudbed-1",
    )
    assert [fc.case_id for fc, _ in a] == [fc.case_id for fc, _ in _load("Market.cloudbed-1")]
    assert get_layout("Market/cloudbed-2") is LAYOUTS["Market.cloudbed-2"]


def test_root_may_be_the_sub_environment_directory():
    direct = OpenRCAAdapter(FIXTURE_ROOT / "Market" / "cloudbed-2", system="Market.cloudbed-2")
    assert direct.system_dir == FIXTURE_ROOT / "Market" / "cloudbed-2"


@pytest.mark.parametrize("system", ENVS)
def test_case_ids_and_labels_have_no_slashes(system):
    env = system.split(".")[1]
    cases = _load(system)
    assert [fc.case_id for fc, _ in cases] == [
        f"OpenRCA-Market.{env}_{i}_{c}" for i, c in enumerate(COMPONENTS[system])
    ]
    for fc, gt in cases:
        assert fc.system == f"openrca_market.{env}"
        assert fc.dataset == f"OpenRCA-Market.{env}"
        assert "/" not in fc.case_id + fc.system + fc.dataset + gt.case_id


@pytest.mark.parametrize("system", ENVS)
def test_ground_truth_matches_record_csv_verbatim(system):
    record = pd.read_csv(FIXTURE_ROOT / "Market" / system.split(".")[1] / "record.csv")
    for (_, gt), (_, row), ftype in zip(_load(system), record.iterrows(), FAULT_TYPES[system]):
        assert gt.root_cause_service == row["component"]
        assert gt.raw_fault_type == row["reason"]
        assert gt.inject_time == row["timestamp"]
        assert gt.fault_type == ftype


def test_record_datetime_column_is_shanghai_time():
    for system in ENVS:
        record = pd.read_csv(FIXTURE_ROOT / "Market" / system.split(".")[1] / "record.csv")
        local = pd.to_datetime(record["timestamp"], unit="s", utc=True).dt.tz_convert("Asia/Shanghai")
        pd.testing.assert_series_equal(
            local.dt.tz_localize(None), pd.to_datetime(record["datetime"]), check_dtype=False, check_names=False
        )


def test_date_folder_uses_shanghai_date_not_utc_date():
    """The first record of each fixture is on 2022-03-19 in UTC but 2022-03-20
    in UTC+8, the folder the telemetry sits in."""
    for system in ENVS:
        ts = TIMESTAMPS[system][0]
        assert pd.Timestamp(ts, unit="s", tz="UTC").strftime("%Y_%m_%d") == "2022_03_19"
        assert _date_folder(ts) == "2022_03_20"
        assert len(_load(system)[0][0].metrics) > 0


@pytest.mark.parametrize("system", ENVS)
def test_no_logs_and_no_spans(system):
    for fc, _ in _load(system):
        assert fc.logs == [] and fc.traces == []
        assert fc.topology.number_of_nodes() == 0


@pytest.mark.parametrize(
    "system,containers,services",
    [
        ("Market.cloudbed-1", ["node-3.shippingservice-1", "node-2.emailservice-0"], ["adservice-grpc", "frontend-http"]),
        ("Market.cloudbed-2", ["node-5.recommendationservice2-0", "node-4.cartservice2-0"], ["checkoutservice-grpc", "cartservice-grpc"]),
    ],
)
def test_metric_keys_come_from_container_and_service_files(system, containers, services):
    fc, _ = _load(system)[0]
    assert set(fc.metrics) == {
        f"{c}:{k}" for c in containers for k in ("container_cpu_usage_seconds", "container_memory_rss")
    } | {f"app.{s}:{k}" for s in services for k in ("rr", "sr", "mrt", "count")}


@pytest.mark.parametrize("system", ENVS)
def test_metrics_stay_in_the_evidence_window_on_a_one_second_grid(system):
    for fc, gt in _load(system):
        start, end = evidence_window(gt.inject_time)
        for key, series in fc.metrics.items():
            assert series.times[0] == start and series.times[-1] == end - 1, key
            assert set(b - a for a, b in zip(series.times, series.times[1:])) == {1}
            assert sum(1 for f in series.is_forward_filled if not f) == 30


@pytest.mark.parametrize("system", ENVS)
def test_samples_just_outside_the_window_are_excluded(system):
    for fc, _ in _load(system):
        assert all(77.0 not in s.values for k, s in fc.metrics.items() if k.endswith("cpu_usage_seconds"))
        assert all(99.0 not in s.values for k, s in fc.metrics.items() if k.endswith(":mrt"))


def test_fault_is_visible_in_the_faulted_containers_metrics():
    fc, _ = _load("Market.cloudbed-1")[0]
    assert fc.metrics["node-3.shippingservice-1:container_cpu_usage_seconds"].values[-1] == 90.0
    assert fc.metrics["node-2.emailservice-0:container_cpu_usage_seconds"].values[-1] < 20.0


def test_sub_environments_do_not_share_telemetry():
    keys1 = set().union(*(fc.metrics for fc, _ in _load("Market.cloudbed-1")))
    keys2 = set().union(*(fc.metrics for fc, _ in _load("Market.cloudbed-2")))
    assert keys1 and keys2 and not keys1 & keys2

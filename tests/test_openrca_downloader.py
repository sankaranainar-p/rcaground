"""
tests/test_openrca_downloader.py — Tests for scripts/download_openrca.py's
metadata, date-listing and mirror-listing paths, without network access.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "download_openrca.py"
BANK_FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "openrca_bank"


def _load_module():
    spec = importlib.util.spec_from_file_location("download_openrca", _SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


downloader = _load_module()

# 2020-04-11 23:30:00 UTC, which is already 2020-04-12 in UTC+8.
LATE_UTC_TS = 1586647800


@pytest.fixture
def no_download(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("unexpected download")

    monkeypatch.setattr(downloader, "_download", fail)


def _write_record(out_dir: Path, system: str) -> None:
    system_dir = out_dir / system
    system_dir.mkdir(parents=True)
    (system_dir / "record.csv").write_text(f"timestamp\n{LATE_UTC_TS}\n")


def test_list_dates_unverified_system_prints_raw_utc_without_timezone(tmp_path, capsys, no_download):
    _write_record(tmp_path, "Unlisted")
    assert downloader.main(["--out-dir", str(tmp_path), "--system", "Unlisted", "--list-dates"]) == 0
    out = capsys.readouterr().out
    assert "unverified" in out
    assert "2020-04-11T23:30:00+00:00" in out
    assert "2020_04_12" not in out


def test_list_dates_bank_still_uses_layout_timezone(capsys, no_download):
    assert downloader.main(["--out-dir", str(BANK_FIXTURE_ROOT), "--system", "Bank", "--list-dates"]) == 0
    out = capsys.readouterr().out
    assert "unverified" not in out
    assert "record.csv references" in out


def test_metadata_only_unverified_system_downloads_only_metadata(tmp_path, monkeypatch, capsys):
    fetched = []

    def fake_download(url, dest, force=False):
        fetched.append(url.rsplit("/", 1)[-1])
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f"timestamp\n{LATE_UTC_TS}\n")

    monkeypatch.setattr(downloader, "_download", fake_download)
    assert downloader.main(["--out-dir", str(tmp_path), "--system", "Unlisted", "--metadata-only"]) == 0
    assert fetched == ["record.csv", "query.csv"]
    assert "unverified" in capsys.readouterr().out


def test_telemetry_download_unverified_system_requires_layout(tmp_path, no_download):
    with pytest.raises(NotImplementedError, match="no verified layout"):
        downloader.main(["--out-dir", str(tmp_path), "--system", "Unlisted"])


def _fake_tree(listing):
    def tree(path, recursive=False):
        return listing[(path, recursive)]

    return tree


def _d(path):
    return {"type": "directory", "path": path, "size": 0}


def _f(path, size):
    return {"type": "file", "path": path, "size": size}


def test_list_remote_flat_system(monkeypatch, capsys):
    monkeypatch.setattr(
        downloader,
        "_hf_tree",
        _fake_tree(
            {
                ("Bank", False): [_d("Bank/telemetry"), _f("Bank/record.csv", 10)],
                ("Bank/telemetry", False): [_d("Bank/telemetry/2021_03_04"), _d("Bank/telemetry/2021_03_05")],
                ("Bank/telemetry/2021_03_04", True): [
                    _d("Bank/telemetry/2021_03_04/log"),
                    _f("Bank/telemetry/2021_03_04/log/log_service.csv", 5),
                ],
            }
        ),
    )
    downloader.list_remote("Bank")
    out = capsys.readouterr().out
    assert "Bank/: ['record.csv', 'telemetry']" in out
    assert "2 date(s)" in out
    assert "log/log_service.csv (5 bytes)" in out


def test_list_remote_sub_environments(monkeypatch, capsys):
    listing = {("Market", False): [_d("Market/cloudbed-1"), _d("Market/cloudbed-2")]}
    for env in ("cloudbed-1", "cloudbed-2"):
        root = f"Market/{env}"
        listing[(root, False)] = [_d(f"{root}/telemetry"), _f(f"{root}/record.csv", 1)]
        listing[(f"{root}/telemetry", False)] = [_d(f"{root}/telemetry/2022_03_20")]
        listing[(f"{root}/telemetry/2022_03_20", True)] = [_f(f"{root}/telemetry/2022_03_20/metric/m.csv", 7)]
    monkeypatch.setattr(downloader, "_hf_tree", _fake_tree(listing))
    downloader.list_remote("Market")
    out = capsys.readouterr().out
    assert "Market/cloudbed-1/: ['record.csv', 'telemetry']" in out
    assert "Market/cloudbed-2/telemetry/: 1 date(s)" in out
    assert out.count("metric/m.csv (7 bytes)") == 2


def test_telemetry_download_skips_layout_paths_that_do_not_exist(tmp_path, monkeypatch):
    fetched = []
    monkeypatch.setattr(downloader, "_download", lambda url, dest, force=False: fetched.append(url))
    system_dir = tmp_path / "Telecom"
    downloader.download_telemetry_for_dates(system_dir, ["2020_04_11"])
    assert sorted(u.split("2020_04_11/")[1] for u in fetched) == [
        "metric/metric_app.csv",
        "metric/metric_container.csv",
    ]

#!/usr/bin/env python3
"""
scripts/download_openrca.py — Downloader for OpenRCA's Bank system
telemetry (https://github.com/microsoft/OpenRCA).

OpenRCA's own README distributes its full telemetry (Bank+Market+Telecom,
~68.7GB) via a Google Drive folder with no checksum manifest and no
resumable/scriptable HTTP endpoint. This script instead downloads from
the public, directly-fetchable Hugging Face mirror
https://huggingface.co/datasets/cdreetz/OpenRCA (hand-verified against
OpenRCA's documented schema and against OpenRCA's own archived
`rca/archive/agent-Bank.csv` row count while building this project's
rcaground.signals.openrca.OpenRCAAdapter — see CONVERSION.md).

Unlike download_rcaeval.py's Zenodo download (single checksummed archive
per dataset), this script downloads only the specific per-date telemetry
folders actually referenced by Bank/record.csv's timestamps — NOT the
full ~26GB Bank/telemetry/ tree — since OpenRCAAdapter only ever
reads the date folder matching each failure's local date. This
keeps a full Bank download to ~5-6GB (Bank has 10 date folders; see
--list-dates) instead of needing the full ~26GB tree, and a
--dates-only subset makes even that avoidable when you only need a few
cases (e.g. for building a fixture, see this script's own use while
building tests/fixtures/openrca/).

No checksum manifest is published for this mirror (unlike RCAEval's
Zenodo record, which publishes per-file MD5s this project's
download_rcaeval.py verifies against). This script instead verifies
each downloaded file's byte count against the Content-Length reported
by the server's own HEAD response for that same URL, which catches
truncated/interrupted downloads but not server-side corruption --
documented here as a real limitation, not silently glossed over.

Usage:
    # metadata only (record.csv + query.csv, ~65KB total)
    python scripts/download_openrca.py --metadata-only

    # metadata + telemetry for every date referenced in record.csv
    # (all 9 fault dates; ~15-20GB depending on per-date file sizes)
    python scripts/download_openrca.py

    # metadata + telemetry for specific dates only (for fixture-building
    # or spot-checking a handful of cases)
    python scripts/download_openrca.py --dates 2021_03_04 2021_03_06

    # another system; telemetry download requires a verified layout in
    # rcaground.signals.openrca.LAYOUTS (currently Bank and Telecom); --metadata-only,
    # --list-dates and --list-remote work for any system
    python scripts/download_openrca.py --system Bank

    # just print which dates record.csv references, without downloading
    # telemetry; for a system without a verified layout this prints the raw
    # UTC timestamps instead, since no timezone may be assumed
    python scripts/download_openrca.py --list-dates

    # list the system's directory names and one sample date's files on the
    # mirror (no telemetry downloaded), to verify a layout
    python scripts/download_openrca.py --system Telecom --list-remote
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd
from zoneinfo import ZoneInfo

from rcaground.signals.openrca import LAYOUTS, SystemLayout, get_layout

HF_BASE = "https://huggingface.co/datasets/cdreetz/OpenRCA/resolve/main"

DEFAULT_OUT_DIR = Path(__file__).parent.parent / "openrca"


def _content_length(url: str) -> int | None:
    req = Request(url, method="HEAD")
    try:
        with urlopen(req) as resp:
            length = resp.headers.get("Content-Length")
            return int(length) if length is not None else None
    except Exception:
        return None


def _download(url: str, dest: Path, force: bool = False) -> None:
    if dest.exists() and not force:
        expected = _content_length(url)
        actual = dest.stat().st_size
        if expected is None or actual == expected:
            print(f"[skip] {dest} already present ({actual} bytes)")
            return
        print(f"[refetch] {dest} size mismatch (have {actual}, server reports {expected})")

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[download] {url} -> {dest}")
    req = Request(url)
    with urlopen(req) as response, dest.open("wb") as out_fh:
        total = 0
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            out_fh.write(chunk)
            total += len(chunk)

    expected = _content_length(url)
    if expected is not None and total != expected:
        dest.unlink(missing_ok=True)
        raise ValueError(
            f"{url}: downloaded {total} bytes, server HEAD reports {expected}. "
            "Aborting — file left unwritten rather than keeping a truncated copy."
        )
    print(f"[ok] {dest} ({total} bytes)")


def utc_timestamps(record_csv: Path) -> list[str]:
    """Return the sorted distinct record.csv failure timestamps as ISO UTC
    strings, with no timezone conversion applied."""
    record = pd.read_csv(record_csv)
    stamps = {pd.Timestamp(float(ts), unit="s", tz="UTC").isoformat() for ts in record["timestamp"]}
    return sorted(stamps)


def _hf_tree(path: str, recursive: bool = False) -> list[dict]:
    url = f"https://huggingface.co/api/datasets/cdreetz/OpenRCA/tree/main/{path}"
    if recursive:
        url += "?recursive=true"
    with urlopen(Request(url)) as resp:
        return json.load(resp)


def list_remote(system: str, sample_date: str | None = None) -> None:
    """Print the mirror's directory names under *system* and the files of one
    sample telemetry date, without downloading any telemetry. A system whose
    top level has no `telemetry/` directory is split into sub-environments;
    each one is listed separately."""
    top = _hf_tree(system)
    names = sorted(e["path"].rsplit("/", 1)[-1] for e in top)
    if "telemetry" in names:
        roots = [system]
    else:
        print(f"{system}/: {names}")
        roots = [e["path"] for e in sorted(top, key=lambda e: e["path"]) if e["type"] == "directory"]
    for root in roots:
        entries = _hf_tree(root)
        print(f"{root}/: {sorted(e['path'].rsplit('/', 1)[-1] for e in entries)}")
        dates = sorted(
            e["path"].rsplit("/", 1)[-1] for e in _hf_tree(f"{root}/telemetry") if e["type"] == "directory"
        )
        print(f"{root}/telemetry/: {len(dates)} date(s): {dates}")
        if not dates:
            continue
        date = sample_date or dates[0]
        prefix = f"{root}/telemetry/{date}/"
        for e in sorted(_hf_tree(f"{root}/telemetry/{date}", recursive=True), key=lambda e: e["path"]):
            if e["type"] == "file":
                print(f"  {e['path'][len(prefix):]} ({e.get('size', '?')} bytes)")


def referenced_dates(record_csv: Path, timezone: str = "Asia/Shanghai") -> list[str]:
    """Return the sorted set of `{YYYY_MM_DD}` telemetry folder names
    record.csv's failures actually fall on, in the system's timezone
    (see rcaground.signals.openrca module docstring for why local time,
    not UTC, is the correct conversion here).
    """
    tz = ZoneInfo(timezone)
    record = pd.read_csv(record_csv)
    dates = set()
    for ts in record["timestamp"]:
        dt = pd.Timestamp(float(ts), unit="s", tz="UTC").tz_convert(tz)
        dates.add(dt.strftime("%Y_%m_%d"))
    return sorted(dates)


def download_metadata(out_dir: Path, system: str = "Bank", force: bool = False) -> Path:
    system_dir = out_dir / system
    _download(f"{HF_BASE}/{system}/record.csv", system_dir / "record.csv", force=force)
    _download(f"{HF_BASE}/{system}/query.csv", system_dir / "query.csv", force=force)
    return system_dir


def download_telemetry_for_dates(system_dir: Path, dates: list[str], force: bool = False) -> None:
    layout = get_layout(system_dir.name)
    files = [p for p in (layout.log, layout.metric_app, layout.metric_container, layout.trace) if p]
    for date in dates:
        for rel_path in files:
            url = f"{HF_BASE}/{system_dir.name}/telemetry/{date}/{rel_path}"
            dest = system_dir / "telemetry" / date / rel_path
            _download(url, dest, force=force)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--out-dir", type=Path, default=DEFAULT_OUT_DIR, help=f"output directory (default: {DEFAULT_OUT_DIR})"
    )
    parser.add_argument("--system", default="Bank", help="OpenRCA system to download (default: Bank)")
    parser.add_argument(
        "--dates", nargs="+", help="download telemetry only for these YYYY_MM_DD dates (default: all referenced by record.csv)"
    )
    parser.add_argument("--metadata-only", action="store_true", help="download only record.csv/query.csv, no telemetry")
    parser.add_argument("--list-dates", action="store_true", help="print the dates record.csv references and exit")
    parser.add_argument(
        "--list-remote",
        action="store_true",
        help="list the system's directory names and one sample date's files on the mirror, then exit "
        "(sample date: first of --dates, else the first remote date)",
    )
    parser.add_argument("--force", action="store_true", help="re-download even if a same-size file already exists")
    args = parser.parse_args(argv)

    if args.list_remote:
        list_remote(args.system, args.dates[0] if args.dates else None)
        return 0

    downloading = not (args.metadata_only or args.list_dates)
    layout = get_layout(args.system) if downloading else LAYOUTS.get(args.system, SystemLayout())
    system_dir = (
        download_metadata(args.out_dir, args.system, force=args.force)
        if not args.list_dates
        else args.out_dir / args.system
    )
    if args.list_dates and not (system_dir / "record.csv").exists():
        system_dir = download_metadata(args.out_dir, args.system, force=args.force)

    if not layout.verified:
        stamps = utc_timestamps(system_dir / "record.csv")
        print(f"layout for {args.system!r} is unverified; no timezone assumed. Raw UTC timestamps:")
        print("\n".join(stamps))
        return 0

    dates = referenced_dates(system_dir / "record.csv", layout.timezone)
    print(f"record.csv references {len(dates)} date(s): {dates}")

    if not downloading:
        return 0

    target_dates = args.dates if args.dates else dates
    unknown = set(target_dates) - set(dates)
    if unknown:
        print(f"[warn] requested dates not referenced by record.csv: {sorted(unknown)}")

    download_telemetry_for_dates(system_dir, target_dates, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())

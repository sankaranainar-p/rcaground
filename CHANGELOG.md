# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `OpenRCAAdapter(root, system="Bank")` with a per-system `LAYOUTS` table
  (timezone and telemetry file layout). Only Bank is verified; other systems
  raise `NotImplementedError` until verified against real files. Bank case IDs
  are unchanged. `scripts/download_openrca.py` takes `--system`.
- Telecom layout for the OpenRCA adapter (container and app metrics only; no
  logs, spans or other metric files yet). `SystemLayout` now carries per-system
  metric column names and time unit; Bank's output is unchanged and pinned by a
  test. `CPU fault`, `network delay` and `network loss` map to the `cpu`,
  `delay` and `loss` fault classes. The downloader skips layout paths a system
  does not have.
- Synthetic Telecom test fixture (`tests/fixtures/openrca_telecom_synthetic/`)
  and an opt-in real-data test selected by `RCAGROUND_OPENRCA_ROOT`.
- Initial extraction from `ai-agentic-works/ai-payment-reliability-engine`
  with git history preserved: RCAEval and OpenRCA adapters, evidence ranking,
  dependency graph builder, reference RCA generator, two-stage faithfulness
  checker, benchmark harness with baselines B1, B2, B4 and B5, human-rating
  harness, run manifests and cost ledger.
- `docs/protocol.md`, ported from the upstream evaluation protocol, and the
  committed faithfulness study artefacts it cites.
- Packaging (`pyproject.toml`, src layout), CI on Python 3.10 to 3.13,
  contribution guidelines, citation metadata and AI usage disclosure.

### Changed
- `OpenRCABankAdapter` is now a deprecated alias for
  `OpenRCAAdapter(root, system="Bank")` and emits `DeprecationWarning`.
- Domain-specific service level indicator names replaced with generic ones.
- `pytz` replaced with the standard library `zoneinfo`.

### Removed
- B3 (ML triage) baseline and the scripts that depended on the upstream
  triage classifier.

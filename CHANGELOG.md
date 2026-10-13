# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
- Domain-specific service level indicator names replaced with generic ones.
- `pytz` replaced with the standard library `zoneinfo`.

### Removed
- B3 (ML triage) baseline and the scripts that depended on the upstream
  triage classifier.

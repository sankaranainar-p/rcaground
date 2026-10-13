# Contributing to rcaground

Contributions of new benchmark adapters, baselines, metrics and judges are
welcome, as are bug reports and documentation fixes.

## Reporting problems and getting support

Open an issue at https://github.com/sankaranainar-p/rcaground/issues using
the bug report or feature request template. For usage questions, open an
issue with the `question` label. The maintainer aims to respond within one
week.

## Development setup

```bash
git clone https://github.com/sankaranainar-p/rcaground.git
cd rcaground
pip install -e ".[dev]"
pytest
```

The test suite must pass offline: no API keys, no network, no full dataset
downloads. New tests that need real data should use a trimmed fixture under
`tests/fixtures/`; tests that need a model must skip cleanly when it is
unavailable.

## Pull requests

1. Open an issue first for anything larger than a small fix.
2. Keep each pull request to one logical change, with tests.
3. Run `ruff check src tests scripts` and `pytest` before pushing.
4. If a change alters how a reported metric is computed, update
   `docs/protocol.md` in the same pull request and note it in
   `CHANGELOG.md`.

## Adding a benchmark adapter

An adapter yields `(FailureCase, GroundTruth)` pairs (see
`rcaground/signals/types.py`) and must pass the shared contract test in
`tests/contract/test_adapter_contract.py`. Document any dataset quirk you had
to handle (timezones, column naming, missing modalities) in `CONVERSION.md`.

## Use of generative AI

AI assistance is permitted but must be disclosed in the pull request
description (tool, version, and what it was used for), and the contributor
remains responsible for reviewing and testing every change. See
`AI_USAGE.md` for the project's own disclosure.

## Governance

The project is currently maintained by its original author, who reviews and
merges pull requests and cuts releases. Contributors with sustained,
substantive contributions will be invited to become maintainers.

## Code of conduct

All participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

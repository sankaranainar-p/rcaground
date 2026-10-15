# Contributor notes

## Scope
- rcaground is a domain-neutral Python library for evaluating evidence grounding in LLM root cause analysis.
- Never add payment, banking or fintech terms to code, docs or tests. Real dataset component names (Online Boutique's `paymentservice`, OpenRCA's Bank system) stay as they are.

## Changes
- Every change is small, one logical unit, on a branch, with tests.
- Run `ruff check src tests scripts` and `pytest -q` before committing; both must pass.
- If a change alters how a reported metric is computed, update `docs/protocol.md` and `CHANGELOG.md` in the same commit.

## Tests
- Tests run offline: no API keys, no network, no full dataset downloads. Use trimmed fixtures in `tests/fixtures/`.
- Tests that need a model must skip cleanly.

## Git
- Never rewrite git history, force-push, or squash merged work.
- Never add `Co-Authored-By` or any AI attribution line to commits or pull requests.

## Protected paths
- Do not edit files under `docs/faithfulness*/` (committed study artefacts).

## AI usage log
- After each task, append one line to the table in `AI_USAGE.md` only if the kind of assistance is new.

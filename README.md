# rcaground

**Reproducible evaluation of evidence grounding in LLM-generated root cause analysis.**

When a large language model explains why a microservice system failed, two
questions matter: did it name the right root cause, and is every claim in its
explanation actually supported by the telemetry it was shown? Public RCA
benchmarks score the first. `rcaground` measures the second, at the level of
individual claims, on the same public benchmarks.

## What it provides

- **Benchmark adapters** (`rcaground.signals`) that normalise
  [RCAEval](https://github.com/phamquiluan/RCAEval) RE1/RE2 and
  [OpenRCA](https://github.com/microsoft/OpenRCA) cases (metrics, logs,
  traces, ground truth) into one `FailureCase` schema, with documented,
  test-verified handling of dataset pitfalls (see `CONVERSION.md`).
- **Deterministic evidence ranking** (`rcaground.agents.evidence`): robust
  z-scores over KPIs, error spans and novel log templates, boosted along the
  service dependency graph, with stable evidence IDs.
- **Two-stage faithfulness checking** (`rcaground.bench.faithfulness`):
  stage 1 verifies that every cited evidence ID exists and is anomalous;
  stage 2 judges entailment with a chat-model judge from a different model
  family than the generator, with an NLI cross-encoder as a comparison point.
- **A benchmark harness** (`rcaground.bench.run_benchmark`) with YAML
  configs, baselines (rule-based, RCAEval BARO, single-prompt LLM,
  OpenRCA-style agent), AC@k and Avg@5 metrics, and run manifests.
- **A human-rating harness** for Cohen's kappa between automated judges and
  human raters.

The evaluation protocol, including what each metric means and its known
limits, is in [`docs/protocol.md`](docs/protocol.md).

## Installation

```bash
pip install -e ".[dev]"          # core + test tools
pip install -e ".[dev,nli]"      # also the NLI comparison judge (pulls torch)
```

Python 3.10 or newer.

## Quick start (offline, no API keys, no downloads)

The repository ships trimmed fixtures of real benchmark cases, so the full
test suite and a smoke benchmark run with nothing else installed:

```bash
pytest
python -m rcaground.bench.run_benchmark --config src/rcaground/bench/configs/re1_ob_smoke.yaml
```

## Running on full datasets

```bash
python scripts/download_rcaeval.py --dataset RE1-OB    # into data/rcaeval/
python scripts/download_openrca.py --metadata-only     # into data/openrca/
```

LLM-backed components read an OpenAI-compatible provider from the
environment: `OLLAMA_BASE_URL` / `OLLAMA_MODEL` for a local model, or
`GROQ_API_KEY` / `GROQ_MODEL`. With neither set, LLM baselines degrade to an
empty ranking rather than failing.

## Repository layout

```
src/rcaground/
  signals/     benchmark adapters, shared types, alert synthesis
  graph/       dependency graph construction
  agents/      evidence ranking, reference RCA generator
  bench/       harness, baselines, faithfulness checker, configs
  audit/       run manifests, cost and timing ledger
  llm/         chat client and provider selection
  data/        fault taxonomy and alert rules
scripts/       dataset downloaders with checksum verification
docs/          evaluation protocol and committed study artefacts
tests/         unit, adapter-contract and fixture-based tests
```

## Provenance

This package was extracted from the author's AIOps research prototypes in
[ai-agentic-works](https://github.com/sankaranainar-p/ai-agentic-works). The
application-specific code (triage classifier, remediation, API) stays there;
this repository holds only the domain-neutral evaluation core.

## Contributing and support

See [CONTRIBUTING.md](CONTRIBUTING.md). Questions and bug reports go to the
[issue tracker](https://github.com/sankaranainar-p/rcaground/issues).

## Citation

If you use `rcaground`, please cite it using the metadata in
[CITATION.cff](CITATION.cff).

## License

Apache License 2.0. See [LICENSE](LICENSE).

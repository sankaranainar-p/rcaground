# AI usage disclosure

This file records how generative AI tools were used in building this
software, in the form the Journal of Open Source Software requires. It is
updated as the project evolves and summarised in the paper's
"AI usage disclosure" section.

| Tool and version | Where used | Nature of assistance |
|---|---|---|
| Claude (Anthropic), model `claude-opus-5-5` | Repository extraction and setup, October 2026 | Extracting the package from the upstream repository with history; renaming the package and domain-neutral terminology; packaging, CI, README, contribution and citation files; porting the evaluation protocol |
| TODO: list the tools used during upstream development (for example Claude Code, Gemini), with versions | Source code, tests, documentation | TODO: describe (code generation, refactoring, test scaffolding, review) |

## Human review

The maintainer framed the research problem, made the core design decisions
(evidence pack design, two-stage faithfulness, judge family separation,
evaluation protocol), and reviewed, edited and validated all AI-assisted
output. Correctness is checked by the automated test suite, which runs on
every commit, and by the committed study artefacts under `docs/`.

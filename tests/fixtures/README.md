# Test fixtures

All fixtures are small so the suite runs offline. Provenance and licensing
status of each:

| Directory | Contents | Status |
|---|---|---|
| `rcaeval/` | Trimmed RCAEval cases | Trimmed real data (RCAEval, see `CONVERSION.md`) |
| `openrca/` | `agent-Bank.csv`, OpenRCA's archived agent output | Fetched from `rca/archive/agent-Bank.csv` in the OpenRCA GitHub repository (MIT), per `tests/test_b5_openrca_agent.py`; it differs from the file now upstream |
| `openrca_bank/` | `Bank/` record.csv, query.csv and a narrow telemetry slice around three failures | **Trimmed real data** from the Hugging Face mirror <https://huggingface.co/datasets/cdreetz/OpenRCA>, **pending confirmation that redistribution is permitted** (see below) |
| `openrca_telecom_synthetic/` | `Telecom/` record.csv and container/app metric files for one date | **Synthetic** |

## OpenRCA licensing

The OpenRCA repository (<https://github.com/microsoft/OpenRCA>) is MIT
licensed, but the telemetry is distributed separately (Google Drive, and a
third-party Hugging Face mirror with no license or dataset card) and no data
terms are stated. Until that is confirmed with the maintainers, no further
real OpenRCA data is committed, and `openrca_bank/` is kept only pending that
answer.

## `openrca_bank/` (trimmed real data)

Built from `Bank/telemetry/2021_03_04/` for `record.csv` rows 0, 1 and 3
(timestamps 1614841020, 1614852540, 1614856920). Metric, log and trace rows
are kept only within about 15 to 60 seconds of each failure, not the full
30-minute evidence window. Exact commands: `CONVERSION.md`, Bank section 7.

## `openrca_telecom_synthetic/` (synthetic)

Invented values in the real Telecom formats, not derived from OpenRCA data:

- Real headers, column order, millisecond timestamps and directory layout
  (`Telecom/telemetry/2020_04_11/metric/`); no `log/` or `trace/`, as in
  the real Telecom system.
- `record.csv`: three invented failures on 2020-04-11 Shanghai time (all on
  the previous UTC day, as every real Telecom record is). Component and
  reason names reuse the real vocabulary.
- `metric_container.csv`: two components times two KPIs at 60 s cadence over
  each failure's 30-minute window, plus one sample just outside each window.
  The faulted component's CPU jumps to about 90 at the failure time.
- `metric_app.csv`: one service, 60 s cadence, same windows; `avg_time`
  rises at the failure time.
- Identifiers are invented (`itemid` from 900000000000001, `bomc_id`
  `SYN-001`/`SYN-002`).

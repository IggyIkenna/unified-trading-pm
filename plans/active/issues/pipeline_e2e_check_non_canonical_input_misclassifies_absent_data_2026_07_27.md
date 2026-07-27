---
doc_type: issue
title:
  "features-service pipeline_e2e_check.py's raw_chains/raw_defi coverage scan mislabels ZERO real capture as
  `non_canonical_input` (implies migration work) instead of `no_captured_input_for_window` (implies a backfill/capture
  gap) — CEFI volatility real-day proof"
summary: >-
  While proving features_by_date_root_canonicalisation_2026_07_21.md todo 6 (delta_one + volatility real-day proof), the
  volatility CEFI leg reported `non_canonical_input (window 2026-07-25..2026-07-26, lookback=1d)` for both force and
  skip legs. Direct manifest verification shows this is misleading: CEFI options_chain/futures_chain capture_status is
  0% captured/empty_confirmed across the entire ~400-day auto-day scan window (306/318 sampled rows attempted_failed,
  rest expected_unattempted, verified via the availability index directly) — a genuine, already-tracked upstream capture
  gap (`deribit_options_chain_af_g4_blocker_2026_07_03.md`, open since 2026-07-03), not a shape/migration problem.
  `_scan_input_coverage()` (scripts/pipeline_e2e_check.py:758) filters `rows` by `service_name` + `capture_status` ONLY,
  before splitting canonical/non-canonical by `_is_canonical_input_row()` — so for a `raw_chains` family
  (options_chain/futures_chain), any OTHER MTDS data_type captured that day (trades, book_snapshot_5, derivative_ticker,
  etc. — CEFI has these on nearly every day) gets counted as a "non-canonical" row for THIS family's coverage, even
  though it has nothing to do with options_chain/futures_chain. Result: `canonical_days=[]` (correctly — no
  options_chain/futures_chain ever captured) but `non_canonical_days` is near-universally populated (any day with ANY
  other MTDS capture), so the `if not scan.canonical_days and scan.non_canonical_days` branch (line 874) fires and
  reports `non_canonical_input` — the wrong diagnosis. The correct signal here is `no_captured_input_for_window` (line
  876), which is what would tell an operator "this needs a backfill/capture fix", not "this needs a migration".
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, coverage-scan, data-correctness, false-signal, volatility, options_chain, futures_chain]
related:
  [
    /plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md,
    /plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  measured 2026-07-27 while proving features_by_date_root_canonicalisation_2026_07_21.md todo 6 — real GCP infra, real
  availability-index rows, not inferred.
---

# pipeline_e2e_check.py mislabels zero-capture as `non_canonical_input` for `raw_chains`/`raw_defi` families

## What I found

Running
`scripts/pipeline_e2e_check.py --day 2026-07-26 --asset-group CEFI --family volatility --legs force,skip --auto-day --require-captured`
reported:

```
CEFI:volatility force/skip: skipped, reason=non_canonical_input (window 2026-07-25..2026-07-26, lookback=1d)
PROVED NOTHING: 2 cell(s) enumerated, 0 verified (every cell skipped).
```

Direct verification against the real availability index (`market-data-tick-cefi-prd-central-element-323112`,
`read_availability_index`, `service_name=market-tick-data-service`):

- Over 2026-06-01..2026-07-26: `options_chain`/`futures_chain` rows = 318 total, of which 306 `attempted_failed`, 12
  `expected_unattempted`, **0 `captured`, 0 `empty_confirmed`**.
- Extending the scan to the full ~400-day `_AUTO_DAY_SEARCH_DAYS` window (2025-06-20..2026-07-26): still **0 rows** with
  an acceptable capture_status for either data_type.
- Calling `_scan_input_coverage("volatility", "CEFI", ...)` directly confirms `canonical_days=[]` (correct — nothing
  ever captured) but `non_canonical_days` has 399 distinct dates (essentially the whole scanned range).

Root cause (`scripts/pipeline_e2e_check.py:758-804`, `_scan_input_coverage`): the `rows` filter
(`service_name == model.service_name & capture_status.isin(_ACCEPTABLE_INPUT_STATUSES)`) does **not** narrow to rows
whose `data_type` is even plausibly relevant to the family. For a `raw_chains` family (volatility →
options_chain/futures_chain), MTDS captures many OTHER data_types under the same `service_name` on nearly every day
(trades, book_snapshot_5, derivative_ticker, liquidations, ohlcv_1m — CEFI has these daily). Each of those rows gets
classified via `_is_canonical_input_row(model, data_type, timeframe)`, which returns `False` (non-canonical) for any
`data_type not in {"options_chain", "futures_chain"}` — so every ordinary trades/book_snapshot capture on a day
incorrectly marks that day `non_canonical` for the volatility family's coverage purposes, even though it has zero
relation to options_chain/futures_chain. Since `canonical_days` stays empty (correctly — no chain data was ever
captured) while `non_canonical_days` fills up with unrelated-data-type days, `_resolve_window`'s branch at line 874
(`if not scan.canonical_days and scan.non_canonical_days: return ... reason="non_canonical_input"`) fires — producing
the wrong verdict.

## Why this matters (do not descope)

`non_canonical_input` and `no_captured_input_for_window` point to **materially different remediation paths** — the first
says "this is migration work" (fix a writer/reader path-shape mismatch), the second says "this needs a backfill/capture
fix upstream". An operator or downstream automation reading a `non_canonical_input` verdict for CEFI volatility would
look for a path-shape bug that doesn't exist here; the real, already-tracked issue is the
`deribit_options_chain_af_g4_blocker_2026_07_03.md` capture gap (0% captured for CEFI options_chain/futures_chain, open
since 2026-07-03, actively being worked under the Track-2 coverage backfill). This is a coverage-scan diagnostic bug in
a QA/proof harness, not a production data-writing bug — but it produces a genuinely misleading signal on every future
re-run of this exact real-day-proof check until CEFI's options_chain/futures_chain capture gap is fixed upstream (which
will take time), so it will keep firing and keep misdirecting whoever reads it.

## Recommended decision

Fix `_scan_input_coverage` to only classify a row as canonical-or-non-canonical for THIS family if its `data_type` is
one the family could plausibly be attempting (i.e., filter `rows` to `data_type.isin(model.data_types)` BEFORE the
canonical/non-canonical split, for `raw_chains`/`raw_defi` kinds — `candles` kind is unaffected since its one upstream
service only emits candle-shaped rows). A day with zero rows of the relevant `data_type` (regardless of what else was
captured that day) should fall through to `no_captured_input_for_window`, not `non_canonical_input`.

## Todos

- [ ] 1. [DATA] P2. Fix `_scan_input_coverage` (scripts/pipeline_e2e_check.py:758) to filter `rows` to
      `data_type.isin(model.data_types)` (or the DeFi-raw equivalent) before splitting into `canonical`/ `non_canonical`
      for `raw_chains`/`raw_defi` kind families, so an unrelated data_type capture on a day no longer taints that day's
      coverage verdict for a family it has nothing to do with. Add a unit test asserting: a day with only
      `trades`/`book_snapshot_5` captured (no `options_chain`/`futures_chain` at all) resolves
      `no_captured_input_for_window` for the volatility family, not `non_canonical_input`. Run
      `bash scripts/quality-gates.sh`, ship via quickmerge (repo: features-service).

## Progress Log

- **2026-07-27 (slot 8, `data_engineering`)** — Filed while working
  `features_by_date_root_canonicalisation_2026_07_21.md` todo 6. Root-caused via direct code read
  (`scripts/pipeline_e2e_check.py:758-876`) + real availability-index verification (not inferred) — confirmed 0
  captured/empty_confirmed options_chain/futures_chain rows for CEFI across the full ~400-day auto-day scan window, and
  confirmed `_scan_input_coverage`'s `non_canonical_days` set is populated purely by unrelated MTDS data_types
  (trades/book_snapshot_5/etc.) captured on those same days. Not fixed inline — tangential to the by_date/day=
  writer-fix proof todo 6 was scoped to; the real upstream capture gap this masks is already tracked and being actively
  worked (`deribit_options_chain_af_g4_blocker_2026_07_03.md`), so todo 6's volatility leg is correctly BLOCKED-UPSTREAM
  on that doc, not on this harness bug.

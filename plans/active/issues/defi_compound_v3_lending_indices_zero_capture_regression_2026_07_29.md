---
doc_type: issue
title: >-
  COMPOUND_V3 lending_indices captures ZERO markets on every chain — rows fetched successfully but `market_count_map()`
  drops all of them, tripping the honest-absence FetchEvidence gate (recent regression, not present in the 2026-07-15
  baseline run)
summary: >-
  Launched `mtds-lending-indices-20260729-193529` (2026-06-01..06-30) to re-backfill-validate the evm_defi history
  pagination fix (`mtds@6e2677b9`). AAVE_V3 validated cleanly (daily row counts up to 17,844, far past the old 1000-item
  single-shot cap — pagination fix confirmed working). But COMPOUND_V3 on EVERY chain (ETHEREUM/ARBITRUM/ BASE/OPTIMISM
  seen so far) logs `"<chain>: compound_v3_custom schema succeeded (N rows)"` (N>0, real rows fetched) immediately
  followed by `"Failed to collect compound_v3 on <chain>: record_empty(reason=SOURCE_RETURNED_ZERO) requires
  FetchEvidence proving a clean 200+empty fetch ... The supplied evidence does NOT prove honest absence"` — 10
  occurrences in the first ~1500 log lines (2 days of the 30-day window), one per (chain) per day, i.e. 100% failure
  rate for this venue. Root-cause hypothesis (not yet fixed): `market_count_map()` (`_lending_grain.py:87-107`) extracts
  a market key by trying `LENDING_ADDR_COLUMNS` (market_address/ underlying_asset/reserve/market_id/...) then falls back
  to `symbol`; if NONE of those columns are populated on a row it is silently dropped (`continue`). If the compound_v3
  parser (`_parse_compound_v3_custom`/ `_parse_compound_v3_flat` in lending_indices_handler.py) isn't populating a
  recognized address/symbol column, every real row collapses to an EMPTY `market_counts` dict → `record_market_captures`
  calls `record_zero_rows` → the recorder's honest-absence FetchEvidence proof correctly rejects it (real data existed,
  so it can't prove a clean 200+empty) → raises → caught by the outer per-(protocol,chain) `except Exception` in
  `lending_indices_handler.py:781-794` → correctly classified + `record_shard_failure` (so the manifest is NOT corrupted
  — this is the shard-level-failure-isolation contract working as designed) — but net effect: 0 usable COMPOUND_V3
  lending_indices rows land for the validated window despite real upstream data existing. **Confirmed a REGRESSION, not
  pre-existing**: grepped the last-known lending-indices VM run (`mtds-lending-indices-20260715-113442`, predates this
  fix) for the same message — 0 occurrences. Candidate causal commits (all touched lending_indices_handler.py /
  instrument_type resolution since 07-15, none confirmed): `f2e3ad41` ("harden manifest rebuild to route 0-row shards to
  honest-absence"), `acfb76ca`/`faf4fafa`/`fec20de2` (A_TOKEN/LENDING instrument_type retire/revert churn), `4ca2640d`
  (per-instrument writer sharding). Not investigated further — outside this task's scope (dispatched to validate the
  pagination fix + canary, not to root-cause a new defect).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, lending-indices, compound_v3, honest-absence, regression, data-correctness]
related:
  [
    plans/active/issues/defi_mvp_backfill_optimization_ready_2026_07_20.md,
    plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-29
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by:
locked_by:
source:
  [
    "surfaced 2026-07-29 slot-5 data_engineering, during the pagination-fix re-backfill validation for
    defi_mvp_backfill_optimization_ready_2026_07_20.md's last todo",
  ]
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
execution_scope: orchestrator-agent
drift_direction: stable
depends_on: []
---

# COMPOUND_V3 lending_indices — 100% shard-failure regression, root-cause not yet fixed

## What I found

Re-backfilling `mtds-lending-indices-20260729-193529` (2026-06-01..06-30, launched to validate `mtds@6e2677b9`'s
evm_defi history pagination fix) shows COMPOUND_V3 failing to capture ANY market on ANY chain, on every day observed so
far (ETHEREUM/ARBITRUM/BASE/OPTIMISM × 2026-06-01/02). Real rows ARE fetched
(`"compound_v3_custom schema succeeded (N rows)"`, N>0) but the shard ends in `record_shard_failure`, not
`record_captured` — see the log pattern

- code trace in the summary above. Evidence:
  `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260729-193529/run.log`.

## Why it matters

COMPOUND_V3 is one of the DeFi-MVP lending venues this same doc's optimization work targets. Its lending_indices
coverage is currently 0% for at least this window (and likely has been since whichever commit introduced the regression,
~2026-07-15 to now) despite the venue being queryable and returning real data — this is silent-to-the- manifest-consumer
coverage loss (correctly classified as `attempted_failed`, not silently dropped or mis-recorded as absent, so the
manifest itself stays honest — but downstream consumers see a real, growing gap).

## Recommended decision

File as its own AO-dispatchable fix todo (below) rather than folding into
`defi_mvp_backfill_optimization_ready_2026_07_20.md` (that doc's remaining work is the canary + pagination-fix
validation, which this issue's discovery does NOT block — the pagination fix itself is independently confirmed via
AAVE_V3's >1000-row days in the same run).

- [ ] [DATA] P1. **Root-cause + fix COMPOUND_V3's `market_count_map()` empty-collapse.** Read
      `_parse_compound_v3_custom`/`_parse_compound_v3_flat` in
      `market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py` and confirm which
      column(s) the parsed DataFrame actually populates per row; compare against `LENDING_ADDR_COLUMNS` in
      `_lending_grain.py:66-75` (`market_address`/`underlying_asset`/`reserve`/`market_id`/`market_key`/
      `collateral_asset`/`principal_token`/`collateral_token`/`asset_address`) + the `symbol` fallback. Either (a) the
      parser needs to populate one of those recognized columns, or (b) `market_count_map`/`LENDING_ADDR_COLUMNS` needs a
      compound_v3-specific column added. Add a unit test asserting a parsed compound_v3 row survives
      `market_count_map()` with a non-empty key. Bisect the candidate commits named in the summary if the root cause
      isn't obvious from a direct read. (repo: market-tick-data-service)
- [ ] [DATA] P2. **Verify `mtds-lending-indices-20260729-193529` reaches a terminal state cleanly** (it was still
      RUNNING, ~day 2/30 processed, when this doc was filed — SPOT + `VM_SHUTDOWN_ON_COMPLETION=true`, self-
      terminating, not fire-and-forget-risked) and confirm AAVE_V3/RADIANT/EULER_V2 final captured counts stay
      consistently >1000-per-busy-day across the full window (this doc's own validation only sampled the first ~2 days).
      `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260729-193529/run.log`.

## Codex SSOTs

`/codex/02-data/honest-absence-downstream-handling.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/04-architecture/shard-level-failure-isolation.md`.

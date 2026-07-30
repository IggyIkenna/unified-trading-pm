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
status: resolved
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
  "market-tick-data-service@d36e2498 (lending_indices catalogue-residual root-cause fix) + risk_params_handler.py
  identical-bug fix, both per this doc's own Progress Log (autonomous session 2026-07-30, Wave 2 doc-count-reduction)"
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

- [x] ✅ [DATA] P1. **DONE 2026-07-29 (slot-13/cicd, agt-068e39, pivoted to data_engineering).**
      `market-tick-data-service@d36e2498`. **The original hypothesis (`market_count_map()` empty-collapse) was
      DISPROVEN** — pulled the real VM log
      (`gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260729-193529/run.log`)
      and confirmed `market_count_map()` worked correctly:
      `compound_v3/ETHEREUM: compound_v3_custom schema succeeded (4 rows)` immediately followed by
      `Wrote 4 rows across 4 instrument shard(s)` — 4/4 distinct markets parsed + written per chain, every day sampled.
      **Real root cause**: the 2026-07-26 catalogue-residual wiring (`market-tick-data-service@eae703b0`, from
      `defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md`) diffs two DIFFERENT id spaces.
      `market_count_map()` keys captured markets by raw on-chain ADDRESS (the correct IS-seeded EU atom
      `record_market_captures` reconciles), but the IS catalogue's own `instrument_id` column for
      `instrument_type="lending"` is the canonical `VENUE-CHAIN:TYPE:SYMBOL` glued form built by `build_instrument_id`
      (confirmed in instruments-service's `scripts/build_instrument_catalogue.py` + the log's own error `row_key`:
      `instrument_id='compound_v3-ethereum:supply:cusdt'` — a symbol, not an address). These two id spaces never
      intersect, so `record_catalogue_residual_empty_typed`'s `residual = catalogue_ids - captured_ids_lower` always
      evaluated to the FULL catalogue, wrongly emitting `record_empty(reason=SOURCE_RETURNED_ZERO)` per catalogued
      reserve even though real markets were captured — the honest-absence gate then correctly rejected the
      unsubstantiated empty claim, raising and routing the whole shard through `record_shard_failure` despite the write
      having already succeeded. Confirmed the SAME bug hits MORPHO in the identical run
      (`morpho-ethereum:lending_market:wbtc-eurcv:0x2ff84b`). The prior test for this wiring
      (`test_catalogue_residual_emits_source_returned_zero_per_instrument`) encoded the same wrong assumption — it
      mocked the catalogue's `instrument_id` as a raw address, which is not how the real catalogue is built. **Fix**:
      removed the structurally-invalid `record_catalogue_residual()` call (and its now-unused `_lending_grain.py`
      wrapper) from `lending_indices_handler.py` — `record_market_captures()` already correctly reconciles the
      address-keyed EU cells per its own docstring, so nothing is lost; corrected the wrong test to use the real
      canonical instrument_id form and assert no false failure; added the originally-requested `market_count_map()`
      regression test proving a parsed compound_v3 row (either schema variant) survives with a non-empty key (a valid
      guard against a different future regression class, even though it wasn't this incident's cause).
      `quality-gates.sh`: ALL QUALITY GATES PASSED (204s). (repo: market-tick-data-service)
- [x] ✅ [DATA] P2. **Verified 2026-07-30 (autonomous session).** `mtds-lending-indices-20260729-193529` reached a clean
      terminal state: `EXIT_STATUS=0`, self-terminated via `VM_SHUTDOWN_ON_COMPLETION=true`, full 30-day window
      processed. AAVE_V3 (the pagination-fix target) validated across the whole window — final cumulative counts
      aave_v3_ETHEREUM=7641, ARBITRUM=6496, POLYGON=2089, AVALANCHE=1495, BASE=8516, LINEA=222, BSC=3773, all
      monotonically climbing through the run, consistent with the pagination fix holding for the full window (not just
      the first 2 days this doc originally sampled). RADIANT/EULER_V2 do not appear anywhere in this handler's output —
      `collect-lending-indices` only covers AAVE_V3/SPARK/COMPOUND_V3/MORPHO; RADIANT/EULER_V2 must be a different
      data_type/handler not exercised by this VM, so that part of the original ask doesn't apply here (not investigated
      further, out of this todo's scope). **Important caveat found**: COMPOUND_V3 and MORPHO(ETHEREUM/ BASE) show a
      **100% failure rate across all 30 days** in THIS run's log — but the fix commit
      (`market-tick-data-service@d36e2498`) landed at **2026-07-29T21:35:01Z**, and this VM's last log line is
      **2026-07-29T21:06:51Z** (shutdown) — the VM's baked-in code was fetched at boot (~19:35Z) and never refreshed
      mid-run, so this entire run predates the fix and cannot be used to validate it; the 120/120 compound_v3 failures
      observed here are the pre-fix regression, not evidence the fix failed. **Separately confirmed the fix DOES work**:
      launched a small scoped validation VM (`mtds-lending-indices-20260730-052249`,
      `--lending-protocols compound_v3 2026-06-01 2026-06-02`, SPOT, ~40s runtime) on the current HEAD — zero
      `record_shard_failure`/honest-absence-gate warnings, every chain × day wrote real rows cleanly (e.g.
      `compound_v3/ETHEREUM: compound_v3_custom schema succeeded (4 rows)` →
      `Wrote 4 rows across 4 instrument     shard(s)`, totals 16 records day 1 / 18 records day 2 across
      ETHEREUM/ARBITRUM/BASE/OPTIMISM). The fix is confirmed correct in production, not just in unit tests.
- [x] ✅ [DATA] P2. **CONFIRMED BROKEN + FIXED 2026-07-30 (autonomous session).** `risk_params_handler.py` had the
      identical bug: `itype_str = _lending_instrument_type_str(protocol)` resolves to `"lending"` for these protocols,
      so `catalogue_pool_ids_for_shard(..., instrument_type="lending")` builds `catalogue_ids` from the catalogue's
      canonical `VENUE-CHAIN:TYPE:SYMBOL` `instrument_id` column — but `build_market_count_map()`
      (`_risk_params_stage.py:234`) keys captured markets by raw `market_address` (falling back to bare `symbol`), never
      the canonical glued form. **Confirmed live**, not just by code review: launched a small scoped validation VM
      (`mtds-risk-params-validate-20260730-055909`, `--start 2026-06-01 --end 2026-06-02`, SPOT, ~4min runtime) —
      COMPOUND_V3 failed on ALL 4 chains both days with the exact
      `record_empty(reason=SOURCE_RETURNED_ZERO)... does NOT prove honest absence` signature seen in lending_indices
      (100% failure, identical to the lending regression); MORPHO(ETHEREUM/BASE) showed the same pattern. (AAVE_V3 also
      failed every chain in this same run, but for a completely unrelated reason — a genuine upstream subgraph schema
      error, `Type 'Reserve' has no field 'eModeCategoryId'` — not investigated further, out of this todo's scope.)
      **Fix**: removed the `record_catalogue_residual_empty_typed()` call (+ its now-unused imports
      `catalogue_pool_ids_for_shard`/`record_catalogue_residual_empty_typed`) from `risk_params_handler.py`, mirroring
      the lending_indices fix exactly — `_record_shard_result` already correctly reconciles the address-keyed EU cells.
      Rewrote `test_catalogue_residual_emits_source_returned_zero_per_instrument` (which encoded the same wrong
      raw-address catalogue assumption) as `test_catalogue_rows_do_not_false_fail_real_captures`, asserting a
      symbol-form catalogue residual entry no longer triggers ANY `record_empty` call alongside a real address-form
      capture. **Also checked `lst_rates_handler.py`/`evm_defi_collectors.py`'s wiring per this todo's own suggestion**:
      BOTH are NOT exposed to this bug — unlike lending_indices/risk_params, their `captured_ids` are built from the
      shard's OWN WRITTEN canonical `instrument_id` column (`shard_df["instrument_id"].iloc[0]`), the same canonical
      form the catalogue's `instrument_id` column uses — the two id-spaces already match by construction, so no fix
      needed there. (repo: market-tick-data-service)

## Codex SSOTs

`/codex/02-data/honest-absence-downstream-handling.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/04-architecture/shard-level-failure-isolation.md`.

## Progress Log

- **autonomous session 2026-07-30 (Wave 2 doc-count-reduction)**: closed the two remaining todos. Verified the original
  VM's clean terminal state + AAVE_V3 pagination-fix validation, discovered (and documented) that VM's own 100%
  compound_v3/morpho failures predate the fix commit by ~29 minutes so aren't evidence against it, then separately
  proved the fix works via a fresh scoped validation VM. Confirmed `risk_params_handler.py` had the identical
  id-mismatch bug (also live-verified via a scoped VM) and shipped the same fix; ruled out
  `lst_rates_handler.py`/`evm_defi_collectors.py` via code review (different, already-correct id-space). All todos now
  checked; status `open` → `resolved`. Doc is archive-eligible.

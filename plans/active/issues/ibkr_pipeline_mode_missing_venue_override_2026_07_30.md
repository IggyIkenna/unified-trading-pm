---
doc_type: issue
title: IBKR tradfi writes mislabeled pipeline_mode=batch_fred — no _VENUE_OVERRIDES entry
summary:
  IBKR-sourced tradfi bars/ticks have no venue override in UTL's `_VENUE_OVERRIDES`, so `derive_pipeline_mode_for_row`
  falls through to `SOURCE_PRIORITY[("tradfi", data_type)]` — which resolves to `fred` for `ohlcv_1d`, mislabeling real
  IBKR-fetched equity/FX/bond/index bars as FRED-sourced. Surfaced 2026-07-30 while widening MTDS's ungated test
  coverage (`ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 11).
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos:
  - unified-trading-library
  - market-tick-data-service
scope: [engineer, admin]
tags:
  - pipeline-mode
  - tradfi
  - data-correctness
  - source-priority
related:
  - /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md
  - /plans/archive/issues/mtds_ungated_test_families_2026_07_17.md
created: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: none
source: >-
  Discovered while executing ci_satellite_ao_dispatch_batch2_2026_07_29.md todo 11 ("Widen MTDS's ungated test
  coverage"). `test_ibkr_equity_bars_write` and `test_partition_path_uses_category_tradfi` in
  `market-tick-data-service/tests/market_interface/adapters/tradfi/test_tradfi_canonical_writes.py` both expect
  `pipeline_mode=batch_databento` for an IBKR write and instead observe `pipeline_mode=batch_fred`.
resolved_by:
locked_by:
depends_on: []
sequential: true
---

# IBKR tradfi writes mislabeled pipeline_mode=batch_fred

## The finding (measured, 2026-07-30)

`unified_trading_library/pipeline_mode_resolver.py`'s `_VENUE_OVERRIDES` table carries explicit entries for `YAHOO`,
`EIA`, `FRED`, `ECB`, and `OFR` (the FRED/ECB/OFR entries were added 2026-07-29 per
`gcs_path_resolution_centralization_audit_2026_07_28.md`, specifically because those are self-archiving vendors whose
(asset_group, data_type) pair has no dedicated `SOURCE_PRIORITY` entry and would otherwise silently fall through to the
`tradfi` asset-group fallback). **`IBKR` never got the same treatment.** `IBKRAdapter.write_canonical_shard` →
`write_tradfi_shard` → `derive_pipeline_mode_for_row(venue="IBKR", "tradfi", data_type)` has no venue override and no
`(IBKR, data_type)` `_VENUE_DT_OVERRIDES` entry, so it falls through to `SOURCE_PRIORITY[("tradfi", data_type)]` —
whatever the _data-type-level_ priority source is, NOT the actual fetching vendor (IBKR).

Measured live (`IBKRAdapter(...).write_canonical_shard(..., data_type="ohlcv_1d", ...)`):

```
gs://.../pipeline_mode=batch_fred/asset_group=tradfi/venue=IBKR/instrument_type=equity/
    data_type=ohlcv_1d/IBKR:EQUITY:AAPL-USD.parquet
```

Real IBKR-fetched equity bars are stamped as FRED-sourced. This is the exact same class of bug the 2026-07-29
FRED/ECB/OFR fix addressed — just not extended to IBKR at the time (IBKR uses `ohlcv_1d`/`yield_curve` types that
overlap with FRED's, so `SOURCE_PRIORITY[("tradfi", "ohlcv_1d")]` resolving fred-first silently catches IBKR too).

**CONFIRMED 2026-07-31 (todo 1 census): zero real-prod blast radius today.** See Progress Log entry below — the tradfi
manifest has 0 rows with `venue=IBKR` (any `pipeline_mode`), so no real prod object is currently mislabeled. The bug is
real in the code path (confirmed via direct adapter re-verification / the two `xfail`-marked tests) but IBKR has not yet
written any canonical shard to the prod tradfi bucket, so nothing needs backfilling — todos 2-4 remain required (the bug
will mislabel the FIRST real IBKR write the moment IBKR ingestion goes live), but todo 5's conditional backfill
migration is NOT triggered.

## Why this isn't a same-commit fix

Unlike the FRED/ECB/OFR fix (which reused an EXISTING `PipelineMode.BATCH_FRED` / `BATCH_ECB` / `BATCH_OFR` enum
member), **there is no `PipelineMode.BATCH_IBKR` member in `unified_api_contracts` today.** Adding one is a cross-repo
UAC registry change (new enum member + any exhaustiveness checks/tests in UAC that iterate the enum + potentially the
manifest schema's legal-value list) — the same "registry-data-dict" class of change this same batch's todo 5
(`detect_breaking_change.py` registry blind spot) calls out as needing its own scoped handling, not a drive-by edit
inside an unrelated test-widening todo.

## Todos

- [x] ✅ [BACKEND] P2. **Confirm real-prod blast radius**: run a manifest/GCS census for `asset_group=tradfi venue=IBKR`
      — count objects currently stamped `pipeline_mode=batch_fred` (or any non-`batch_databento`/`batch_ibkr` value)
      that were actually IBKR-fetched. (repo: market-tick-data-service) — market-tick-data-service@233f852e. **Result: 0
      rows.** See Progress Log 2026-07-31.
- [x] ✅ [BACKEND] P2. **Add `PipelineMode.BATCH_IBKR = "batch_ibkr"`** to
      `unified_api_contracts/canonical/crosscutting/pipeline_mode.py`, following the exact pattern of the existing
      `BATCH_FRED`/`BATCH_ECB`/`BATCH_OFR` members (incl. any exhaustiveness/coverage tests in UAC that enumerate
      `PipelineMode` members). (repo: unified-api-contracts) — `unified-api-contracts@ab7d8c83`. Added `BATCH_IBKR` +
      registered the matching closed-set entries (`SOURCE_PRIORITY[("tradfi","ohlcv_1d")]` now `["fred","ecb","ibkr"]`,
      `SOURCE_MODE_CAPABILITY["ibkr"]=BATCH-only`, `EMISSION_LATENCY_MS_BY_SOURCE["ibkr"]=86_400_000`) — same
      never-actually-competes rationale as FRED/ECB (write-time always resolves via the UTL venue override once todo 3
      lands; this registration exists purely to satisfy the `PipelineMode<->SOURCE_PRIORITY` closed-set round-trip, per
      the confirmed real caller's `data_type="ohlcv_1d"` — see the issue's own "Measured live" section). Also bumped
      `test_extra_live_probe_sources_do_not_leak_cross_ag`'s pinned tradfi prefix count 12→13 and
      `test_source_mode_capability_matches_ratified_matrix_exactly`'s `EXPECTED_SOURCE_MODE_CAPABILITY` (both caught by
      the full `quality-gates.sh` run, mirroring the exact 2 extra registries the FRED/ECB/OFR fix also had to touch).
      Full `quality-gates.sh` green (298s, sentinel `ab7d8c8355b1722e3f5d8262baddac59a991c284`).
- [ ] [BACKEND] P2. **Add `"IBKR": PipelineMode.BATCH_IBKR`** to `_VENUE_OVERRIDES` in
      `unified_trading_library/pipeline_mode_resolver.py`, mirroring the FRED/ECB/OFR entries added 2026-07-29. (repo:
      unified-trading-library)
- [ ] [BACKEND] P2. **Un-xfail** `test_ibkr_equity_bars_write` and `test_partition_path_uses_category_tradfi` in
      `market-tick-data-service/tests/market_interface/adapters/tradfi/test_tradfi_canonical_writes.py` (both currently
      marked `xfail(strict=True)` citing this doc) once the above ship — update their expected `pipeline_mode` to
      `batch_ibkr` and remove the marker. (repo: market-tick-data-service)
- [x] ✅ N/A [BACKEND] P3. **If the census (todo 1) finds real mislabeled prod objects**: file a follow-up migration
      todo to backfill their `pipeline_mode` in the manifest (mirroring whatever backfill approach the FRED/ECB/OFR fix
      used, if any) — do not silently leave stale-mislabeled manifest rows uncorrected. (repo: market-tick-data-service)
      — condition not met: todo 1's census found 0 real prod objects, so no backfill migration is needed.

## Progress Log

- **2026-07-31 (todo 1 — census)**: Ran a read-only, single-filtered-read manifest census (no whole-corpus GCS walk; no
  GCS listing) via `market-tick-data-service/scripts/one_offs/ibkr_tradfi_pipeline_mode_census_2026_07_31.py`
  (market-tick-data-service@233f852e):
  `read_availability_index(bucket=resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="tradfi"), columns=[...], filters=[("venue", "==", "IBKR")])`
  against the live prod tradfi manifest (`market-data-tick-tradfi-prd-central-element-323112`). **Result: 0 rows.**
  Sanity-checked the read path itself (not just the filter) by pulling all 6,380,269 tradfi manifest rows unfiltered —
  real venues present are `NASDAQ/CME/NYSE/ICE/KRX/CBOE/FX/BARCHART/FRED/YAHOO_FINANCE`, confirming the manifest read
  genuinely returns data and `IBKR` is genuinely absent, not silently erroring. Also confirmed `kind="tick-data"`
  resolves to the identical bucket name for tradfi, so there is no second bucket to check separately. **Conclusion: the
  `_VENUE_OVERRIDES` bug is real in the code path (confirmed via direct adapter re-verification + the two `xfail`-marked
  tests) but IBKR has never actually written a canonical shard to the prod tradfi manifest — the blast radius on real
  objects today is zero.** Flipped todo 1 to done with this result, and flipped todo 5 to N/A (its trigger condition —
  "census finds real mislabeled prod objects" — did not occur, so no backfill-migration todo is needed). Todos 2-4
  remain open and still matter: the bug will mislabel the very first real IBKR write the moment IBKR ingestion goes live
  in prod, so shipping the `_VENUE_OVERRIDES` fix ahead of that is still the point.
- **na-eligibility-audit 2026-07-31** (tradfi tranche, dispatch agt-6d6eaf): **RECLASSIFY — `assigned_vm: NA` →
  `planning`.** This doc was filed as a spun-out issue from an `assigned_vm: planning` parent plan's todo
  (`ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 11, which explicitly declined to fix it inline) and defaulted to
  NA per the workspace's own "default is human unless assessed otherwise" authoring rule — nothing in the doc showed
  that assessment was ever made. All 5 open todos are bounded, worker-determinable, deterministic-outcome engineering
  work: a scoped census with a stated done-when, two code changes that mirror an EXISTING, live-verified template
  (`BATCH_FRED`/`BATCH_ECB`/`BATCH_OFR` in `unified_api_contracts` + their `_VENUE_OVERRIDES` entries), a mechanical
  test un-xfail, and a small bounded conditional follow-up. No open design/judgment call. Shared conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) run and CLEARED: no active
  `assigned_vm: planning` plan in `parent_epic: infrastructure_master` claims this ground, no sibling batch/finalize doc
  drafted this run overlaps, and `tradfi_consolidated_closeout_2026_07_18.md`'s own Track content does not mention
  IBKR/pipeline_mode. Corrected `assigned_role: backend` → `backend_engineer` (the former is not a valid role in the
  live `agents/*.md` registry). Added `sequential: true` — todos 2→3→4 are a real ordering chain (UAC enum must exist
  before the UTL override references it; the test un-xfail needs both). Per `check_finalize_plan_coverage.py` (globs
  `plans/active/*.md` only, not `issues/`), this `doc_type: issue` doc is structurally exempt from the companion
  finalize-plan requirement — none authored.
- **2026-07-30** — Found while executing `ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 11 (widen MTDS's ungated
  test coverage). Two long-ungated tests (`test_ibkr_equity_bars_write`, `test_partition_path_uses_category_tradfi`)
  asserted `pipeline_mode=batch_databento` for IBKR writes; live re-verification showed the code actually produces
  `batch_fred` (via the SOURCE_PRIORITY fallthrough, not the OLD contract the tests encoded either — both are wrong, in
  different ways). Filed as its own issue rather than silently updating the test's expectation to the
  observed-but-still-buggy `batch_fred` value, and rather than absorbing a cross-repo UAC enum addition into the
  unrelated test-widening todo. The two affected tests are marked `xfail(strict=True)` citing this doc so the MTDS gate
  can still widen `PYTEST_UNIT_DIR` without masking the bug as fixed.

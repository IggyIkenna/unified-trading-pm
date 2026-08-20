---
doc_type: issue
title:
  DeFi dex_pool_state (2107 rows) + lst_rates (851 rows) attempted_failed with
  error_reason=UPSTREAM_INSTRUMENTS_CATALOG_STALE — root cause is a temporal race between the IS DeFi historical catalog
  backfill and pre-existing MTDS collect attempts, NOT a live code regression; a real code gap found + fixed; data
  remediation (re-collect the affected shards) scoped as a follow-up, not force-completed here
summary:
  "Investigated 2 DP_RUN_MOSTLY_EMPTY alert cells flagged by data_pipeline_alerts_batch_remediation_2026_07_15.md as NOT
  YET COVERED: defi/dex_pool_state and defi/lst_rates, both 100% error_reason=UPSTREAM_INSTRUMENTS_CATALOG_STALE.
  Live-requeried the manifest (market-data-tick-defi-prd-central-element-323112): current counts are dex_pool_state
  2,107 attempted_failed/UPSTREAM_INSTRUMENTS_CATALOG_STALE rows (of 2,109 total attempted_failed; attempted_at
  2026-06-21..06-25) and lst_rates 851 (100% of attempted_failed; attempted_at 2026-06-21..06-30) — close to the
  operator's cited ~2,960 total. Root cause: every one of these rows is a HISTORICAL backfill shard (shard `date` in
  2020-2023, years before the `attempted_at` collect date — confirmed 0% same-day) that hit
  assert_defi_catalog_fresh()'s batch coverage-check gate (instrument_availability/by_date/day=<shard_date>/ under
  instruments-store-defi-prd-central-element-323112) and found NO snapshot at attempt time. Proven via
  gcs_describe_object() on 3 sampled historical dates (2021-03-06, 2023-01-01, 2023-02-10): the per-date catalogue
  snapshots that NOW cover them were all written 2026-06-29T05:19-05:20 UTC — AFTER every one of these MTDS attempts.
  This is a temporal race, not a broken gate: the gate correctly recorded honest absence at the time each attempt ran,
  and the IS DeFi historical catalog backfill (a separate, later-completing operation than the 2026-06-08 R4 catalog
  re-promote R5-fix-7 referenced) has SINCE caught up. A real, separate code gap was also found and fixed while
  investigating: lst_rates_handler.py's _check_preflight() was 1 of 9 DeFi handlers (of 11 total) that never threaded
  mode= into assert_defi_catalog_fresh() (dex_pools_handler.py + risk_params_handler.py are the only 2 that do) — this
  did NOT cause these specific historical failures (their on_date is always >1 day old, so assert_defi_catalog_fresh's
  own date-aware fallback already forced the coverage-check path regardless of mode=), but is a genuine latent gap for
  near-term (yesterday/today) --mode batch runs, which would incorrectly hit the stricter live 24h gate. Fixed as
  defense-in-depth with regression tests. The DATA remediation (re-collecting the 2,958 affected historical shards,
  spanning 434 unique dates 2020-01-01..2026-06-29 across 13 venues / 9 chains) is deliberately NOT executed in this
  pass — reclassifying these rows to empty_confirmed would be dishonest (real DeFi data likely exists now that the
  catalogue covers them; the correct fix is to actually re-fetch, not rubber-stamp), and a live multi-year re-collect
  against production subgraph/RPC endpoints/quota is a genuinely large, risk-bearing operation better run as its own
  scoped, monitored backfill than force-completed mid-investigation. Flagged as a follow-up with exact commands."
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    defi,
    manifest,
    honest-coverage,
    capture-status,
    attempted-failed,
    upstream-instruments-catalog-stale,
    assert-defi-catalog-fresh,
    dex-pool-state,
    lst-rates,
    data-pipeline-alerts,
    backfill-followup,
  ]
related:
  [
    ../data_pipeline_alerts_batch_remediation_2026_07_15.md,
    ../master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-07-15
author: unknown
parent_epic: security_and_cross_cutting_master
priority: P1
source:
  [
    "operator-dispatched sub-agent task, discovered while triaging the
    data_pipeline_alerts_batch_remediation_2026_07_15.md 'New todos' section's dex_pool_state/lst_rates NOT YET COVERED
    entry, 2026-07-15",
  ]
assigned_vm: NA
resolved_by:
  [
    "market-tick-data-service@927acf01cf98b03655bd4e04fa73f7b4d19e539d (code fix: lst_rates_handler.py._check_preflight
    threads mode= into assert_defi_catalog_fresh, mirroring dex_pools_handler.py/risk_params_handler.py; 3 new
    regression tests) — NECESSARY BUT NOT the cause of the recurrence (see RE-INVESTIGATED below)",
    "market-tick-data-service@420221b45251943ff48c16114bac13c36c5b4b40 (ROOT-CAUSE code fix: new
    DefiManifestRecorder.record_catalog_unavailable splits catalog-gate-blocked shards into honest
    EXPECTED_PRE_VENUE_LAUNCH (empty_confirmed, pre-genesis/pre-launch) vs retryable UPSTREAM_INSTRUMENTS_CATALOG_STALE
    (attempted_failed, catalogue-behind) via the UAC-SSOT max(chain_genesis, protocol_launch) composition; wired into
    dex_pools_handler + lst_rates_handler; 4 new regression tests, 2 existing updated; quality-gates.sh --no-fix GREEN)",
  ]
locked_by:
locked_since:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
context_scope:
  [
    /plans/active/data_pipeline_alerts_batch_remediation_2026_07_15.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
---

# DeFi `dex_pool_state` + `lst_rates` `UPSTREAM_INSTRUMENTS_CATALOG_STALE` — temporal-race root cause, code gap fixed, data remediation scoped as follow-up

## Real current counts (live-queried 2026-07-15)

Queried `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` directly (27,410,052
total rows) — the operator's cited numbers were close but slightly stale (dex_pool_state's `attempted_at` tail is 06-25,
not 06-30; lst_rates matches):

| data_type        | total rows | `attempted_failed` | of which `UPSTREAM_INSTRUMENTS_CATALOG_STALE` | `attempted_at` range     | unique shard `date`s | venues                                                                                              | chains                                                      |
| ---------------- | ---------: | -----------------: | --------------------------------------------: | ------------------------ | -------------------: | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `dex_pool_state` |  8,103,613 |              2,109 |                                         2,107 | 2026-06-21 .. 2026-06-25 |                   90 | AERODROME_V3, BALANCER, CAMELOT_V3, CURVE, GMX, PANCAKESWAP_V3, SUSHISWAP, SUSHISWAP_V3, UNISWAP_V3 | ARBITRUM, AVALANCHE, BASE, BSC, ETHEREUM, OPTIMISM, POLYGON |
| `lst_rates`      |    222,836 |                851 |                                           851 | 2026-06-21 .. 2026-06-30 |                  344 | ETHENA, ETHERFI, LIDO, MARINADE                                                                     | ETHEREUM, SOLANA                                            |
| **Combined**     |            |                    |                                     **2,958** |                          |                  434 |                                                                                                     |                                                             |

The other 2 non-`UPSTREAM_INSTRUMENTS_CATALOG_STALE` `dex_pool_state` failures are `TimeoutError` — a different,
unrelated transient class, not touched here.

## Root cause — a temporal race, not a broken gate

`assert_defi_catalog_fresh()` (`market_tick_data_service/cli/handlers/_defi_manifest.py:205`) is MODE-AWARE per the
2026-06-24 historical-backfill fix documented in its own docstring: for `mode="batch"` OR whenever `on_date` is more
than 1 day older than the actual current date, it uses `_assert_defi_catalog_covers_date()` — checking for ANY blob
under `instrument_availability/by_date/day=<on_date>/` in the IS DeFi catalogue bucket
(`instruments-store-defi-prd-central-element-323112`) — instead of the stricter live 24h-manifest-row-age gate.

**Every one of the 2,958 affected rows is a genuine historical backfill shard**: comparing each row's `date` (the shard
being collected) against its `attempted_at` (when the collect ran) shows 0% same-day matches across every `attempted_at`
bucket for both data_types (verified by direct query, not inferred) — shard dates run from 2020-01-01 to 2023-02-16 for
the bulk of the rows (dex_pool_state clusters heavily around Feb-Apr 2021; lst_rates is scattered across 2020 and 2023),
collected during a `attempted_at` window in late June 2026. Since `on_date` is always years older than "now,"
`_use_coverage` was `True` for 100% of these rows regardless of what `mode=` value the caller passed — meaning the
coverage-check path (not the live 24h gate) is what actually ran and failed for every one of them.

**The coverage check found no snapshot AT THE TIME because there genuinely wasn't one yet.** Proof: sampled 3 of the
affected historical dates and used `gcs_describe_object()` (not `list_blobs`, which doesn't return real timestamps via
this client) to get the ACTUAL write time of the `instrument_availability/by_date/day=<date>/…/instruments.parquet`
blobs that exist for them today:

| shard `date` (sampled)                      | catalogue snapshot exists today? | snapshot actually written at |
| ------------------------------------------- | -------------------------------- | ---------------------------- |
| 2021-03-06 (dex_pool_state, CURVE-ETHEREUM) | yes                              | **2026-06-29T05:19:08.408Z** |
| 2023-01-01 (lst_rates, AAVEV3-ARBITRUM*)    | yes                              | **2026-06-29T05:20:02.557Z** |
| 2023-02-10                                  | yes                              | **2026-06-29T05:20:08.136Z** |

(*sampled the same-day venue coverage snapshot, not LST-specific — the by-date snapshot is written per-venue across all
asset-group consumers, not per-data_type.)

Every affected `attempted_at` (2026-06-21 through 2026-06-30) is BEFORE 2026-06-29T05:19 UTC for the bulk of the rows,
and the handful right at the boundary (lst_rates: 76 rows on 06-28, 4 on 06-30) straddle the exact window the historical
catalogue backfill was completing. So the gate was CORRECT at attempt time — it honestly reported "no listing for this
historical date yet" — and the IS DeFi historical catalogue backfill has SINCE caught up (confirmed: all 3 sampled dates
now have full coverage).

**This is NOT the same mechanism R5-fix-7 (`master_data_canonicalisation_migration_catalogue_2026_06_07.md:767`, dated
2026-06-08, still unchecked `- [ ]`) was written against.** R5-fix-7 references "R4's catalog re-promote" — a smaller,
earlier re-promote (defi 6,853 rows, `master_data_canonicalisation_migration_catalogue_2026_06_07.md:612`) that landed
2026-06-08 and covered recent/live catalogue freshness, NOT the full 2018-2026 per-date historical snapshot backfill
these 2,958 rows actually needed — that backfill evidently didn't finish until ~2026-06-29, three weeks after R5-fix-7
was written and the exact window these MTDS attempts ran in. R5-fix-7's own "re-probe... then 1-day dry-run both to
GREEN" was accurate advice — it just couldn't have succeeded yet at the time, because the historical catalogue it needed
to re-probe against wasn't actually complete.

## Real code gap found + fixed (adjacent, not the cause of these specific rows)

While tracing `assert_defi_catalog_fresh()`'s callers across all 11 DeFi handlers, found only **2 of 11**
(`dex_pools_handler.py`, `risk_params_handler.py`) thread `mode=` explicitly (derived from `--run-tag`, mirroring the
M-COORD-7 pattern: default `"batch"`, `"live"` when `--run-tag live` or `runtime.mode == live`). The other 9 — including
`lst_rates_handler.py` (one of this issue's 2 named cells) — call `assert_defi_catalog_fresh()` with no `mode=` at all,
defaulting to `mode="live"` and relying ENTIRELY on the date-aware fallback (`on_date < now - 1 day`) to reach the
coverage-check path.

This did **not** cause the 2,958 rows above (their `on_date` is always years old, so the fallback already forces
coverage-check regardless of `mode=`), but it is a real, verified latent gap: a `--mode batch` collect for a near-term
date (yesterday/today — e.g. a same-day retry or a 1-2 day catch-up run) would incorrectly hit the stricter live
24h-manifest-row-age gate instead of the coverage check, for any of these 9 handlers. Fixed the one named in this issue
(`lst_rates_handler.py`) as in-scope; the other 8 (`token_transfers_handler.py`, `liquidations_handler.py`,
`flash_loan_events_handler.py`, `bridge_events_handler.py`, `native_staking_handler.py`,
`liquidation_events_handler.py`, `lending_indices_handler.py`, `aggregator_route_handler.py`, `solana_defi_handler.py`)
share the identical gap and are flagged as a follow-up below rather than fixed here (out of this issue's named scope;
fixing all 9 in one pass risks a wider, less-reviewable diff than this specific alert warrants).

**Fix**: `lst_rates_handler.py::_check_preflight()` now computes `_run_tag` the same way
`risk_params_handler.py::process()` does (`str(getattr(getattr(self, "args", None), "run_tag", "batch") or "batch")`)
and threads `mode=("live" if _run_tag == "live" else "batch")` into `assert_defi_catalog_fresh()`.

`market-tick-data-service@927acf01cf98b03655bd4e04fa73f7b4d19e539d` —
`market_tick_data_service/cli/handlers/lst_rates_handler.py` + 3 new regression tests in
`tests/unit/test_lst_rates_handler_coverage.py::TestCheckPreflightModeThreading` (default-batch, explicit
`--run-tag batch`, explicit `--run-tag live` — asserts the actual `mode=` kwarg received by `assert_defi_catalog_fresh`,
which no prior test in this codebase checked for ANY of the 11 handlers). Shipped via quickmerge, landed on
`live-defi-rollout`, `quality-gates.sh --no-fix` green (170s, sentinel `6fad6565fe66ef34ea245172dc1e606c0a2dd183` →
HEAD).

## Data remediation — NOT executed in this pass, scoped as a follow-up (flagged, not rushed)

**Why reclassification is wrong here** (unlike the tradfi `EXPECTED_*`/`attempted_failed` misclassification fixed
earlier the same day, `tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`): that fix was pure
cleanup because the `error_reason` was ALREADY semantically correct (a real, permanent absence) and only the
`capture_status` pairing was wrong. Here, `UPSTREAM_INSTRUMENTS_CATALOG_STALE` means "we never actually attempted the
real fetch" — the underlying DeFi pool-state / LST-rate data for these historical dates has never been queried. Now that
the IS catalogue covers them, real data is very likely retrievable. Reclassifying to `empty_confirmed` without ever
attempting the fetch would be a NEW dishonest-absence bug of exactly the kind this workspace's honest-coverage
convention exists to prevent.

**Why the actual re-collect isn't executed here**: the correct remediation is re-running `collect-dex-pools` /
`collect-lst-rates` for the affected shard-dates now that the catalogue gate will pass. Scope check performed before
deciding: 434 unique dates spanning 2020-01-01 to 2026-06-29 (not a small contiguous window), against LIVE production
subgraph (TheGraph) and RPC (Alchemy) endpoints, consuming real API-key quota, writing to the production manifest
(`market-data-tick-defi-prd-central-element-323112`) — the same class of operation `scripts/full-defi-backfill.sh`
already exists for (and already re-runs `collect-dex-pools`/`collect-lst-rates` over multi-year ranges as a monitored
background job). Given the size, the live-external-API risk, and this task's own instruction to flag rather than force a
rushed implementation when a fix is genuinely large-scope, this was NOT executed live mid-investigation.
`ManifestFreshnessCache`'s skip-if-fresh check means re-running the CLI over the full affected range is cheap for the
~99.99% of already-good shards (near-instant skip) and only does real work on the 2,958 actually-stale ones, so this is
tractable as a bounded, monitored run — just not one to launch unattended inside a single investigative turn.

### Exact commands for the follow-up (once picked up)

```bash
cd market-tick-data-service && source .venv/bin/activate
python -m market_tick_data_service --operation collect-dex-pools --mode batch --asset-group DEFI \
    --start-date 2020-01-19 --end-date 2026-06-25 2>&1 | tee logs/dex_pool_state_stale_catalog_recollect.log
python -m market_tick_data_service --operation collect-lst-rates --mode batch --asset-group DEFI \
    --start-date 2020-01-01 --end-date 2026-06-29 2>&1 | tee logs/lst_rates_stale_catalog_recollect.log
```

Verify before/after by re-running this issue's live-count query (§ "Real current counts") — expect
`UPSTREAM_INSTRUMENTS_CATALOG_STALE` `attempted_failed` count to drop toward 0 for both data_types, replaced by a mix of
`captured` (real historical data found) and `empty_confirmed` (genuinely no activity that day — e.g. pre-launch
protocol/venue dates, which the launch-date heuristic in `DefiManifestRecorder._resolve_zero_rows_reason_and_evidence`
already handles honestly).

## Follow-ups (not done in this pass)

- [x] [DATA] P1. ✅ **DONE (2026-07-26, slot-12) — target class already at 0; monitored handoff, not full-completion
      block.** Live-queried `market-data-tick-defi-prd-central-element-323112`'s `availability_index.parquet` (16.9M
      rows across the two data_types) BEFORE meaningful new writes from this pass's VMs:
      `UPSTREAM_INSTRUMENTS_CATALOG_STALE` is **already 0 for both `dex_pool_state` and `lst_rates`** — the 2,958-row
      remediation this todo names had already happened via other means (routine backfill/cron activity in the 11 days
      since this issue was filed) before this todo ran. `empty_confirmed[EXPECTED_PRE_VENUE_LAUNCH]` shows 754 rows for
      `dex_pool_state`, confirming the `420221b4` fix is live and classifying correctly. Also (re-)launched the exact
      re-collect commands as a confirmatory re-walk (see `[DEPLOY] P1` below) — those VMs are still running a multi-hour
      full historical walk at the time of this update; not blocking this checkbox on their self-termination per this
      doc's own "or a documented monitored handoff" allowance. See
      `plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s corresponding todo for full evidence. Repo:
      market-tick-data-service.
- [x] [SCRIPT] P2. ✅ **DONE (2026-07-15) — `market-tick-data-service@42527190`.** The new `record_catalog_unavailable`
      pre-genesis split is now wired into **all 10** remaining catalog-gate handlers: `aggregator_route_handler.py`,
      `bridge_events_handler.py`, `flash_loan_events_handler.py`, `lending_indices_handler.py`,
      `liquidation_events_handler.py`, `liquidations_handler.py`, `native_staking_handler.py`, `risk_params_handler.py`,
      `solana_defi_handler.py`, `token_transfers_handler.py`. Each `assert_defi_catalog_fresh`→False branch that
      previously did a blanket `record_failed(UPSTREAM_INSTRUMENTS_CATALOG_STALE)` now routes through
      `DefiManifestRecorder.record_catalog_unavailable` (pre-genesis/pre-launch → honest empty
      `EXPECTED_PRE_VENUE_LAUNCH`; catalogue-behind → retryable `UPSTREAM_INSTRUMENTS_CATALOG_STALE`) — same pattern as
      this issue's `dex_pools_handler.py` + `lst_rates_handler.py` fix (`@420221b4`). (The original item named 9;
      `risk_params_handler.py` — the 10th, called out in this item's own body as "the same class", 51 rows — was fixed
      too, matching the full task scope. None skipped: all 10 had the blanket-`record_failed`-on-gate pattern.) Tests:
      20 new recorder-level regression tests in `test_defi_manifest_recorder.py` (per-handler representative
      `(venue, chain)` tuple → pre-genesis 2014-01-01 → `EXPECTED_PRE_VENUE_LAUNCH` empty, post-launch 2025-06-01 →
      `UPSTREAM_INSTRUMENTS_CATALOG_STALE`) + 12 handler catalog-stale tests updated to assert
      `record_catalog_unavailable` (and `record_failed.assert_not_called()`); exception-path `record_failed` tests left
      unchanged. Also taught the PM adapter-contract ratchet about the new method (`unified-trading-pm@bf07cb6b` —
      `check_adapter_contract_regression.py` `CONTRACT_PATTERNS` += `record_catalog_unavailable`, same precedent as the
      2026-06-05 `record_zero_rows` addition) so the 12 swap-affected handlers stay at/above their contract-call
      baseline. Verification: `bash scripts/quality-gates.sh --no-fix` GREEN (exit 0); mtds unit suite 439 passed (1
      pre-existing skip); ruff + basedpyright clean on all changed files. Defense-in-depth. Repo:
      market-tick-data-service.
- [x] [SCRIPT] P3. **Residual split out of the P2 above (NOT part of the pre-genesis-classification task, left
      honest):** thread `mode=` (`"live"`/`"batch"` per run_tag) into `assert_defi_catalog_fresh(...)` for the 9
      handlers that still omit it (`liquidations`, `native_staking`, `liquidation_events`, `token_transfers`,
      `bridge_events`, `flash_loan_events`, `aggregator_route`, `solana_defi`, `lending_indices`;
      `risk_params_handler.py` already threads it). `assert_defi_catalog_fresh` defaults `mode="live"`, so batch
      backfills currently run the freshness gate with live semantics — the R5-fix-7 gap that `lst_rates_handler.py`
      fixed for itself in `@420221b4`. This is ORTHOGONAL to the pre-genesis classification (the gate returns False for
      pre-genesis dates regardless of `mode`, and the classification split above then records them honestly), so it was
      deliberately not force-completed with the classification fix: it is a separate freshness-semantics concern and
      mis-wiring the per-handler run_tag/mode plumbing risks changing gate behaviour. Repo: market-tick-data-service. —
      already covered by defi_satellite_ao_dispatch_batch1_2026_07_25.md (see that doc for execution).
- [x] [DEPLOY] P1 **NEW (2026-07-15 re-investigation)**. ✅ **DONE (2026-07-26, slot-12)**. Redeployed the DeFi backfill
      VM tarball to current HEAD `ec0df8784b17` (`market-tick-data-service`, `v0.93.0-550-gec0df878` — the deployed
      tarball was already at `d09705ff`, 7 commits past `420221b4`, before this rebuild; rebuilt anyway for freshness)
      via `deployment-service/scripts/vm/create-code-tarballs.sh`; verified live at
      `gs://deployment-scripts-central-element-323112/code/mtds-code.manifest.json`. Launched
      `mtds-dex-pools-backfill` + `mtds-lst-rates-20260726-035545` (both SPOT) via the registered launchers with the
      redeployed image (tarball-freshness check passed for all 4 core repos at launch time), so any future
      `collect-dex-pools`/`collect-lst-rates` re-walk of pre-genesis dates records honest `empty_confirmed` instead of
      recurring `attempted_failed`. The two VMs that originally motivated this todo (`mtds-dex-pools-backfill`,
      `mtds-lst-rates-20260715-121257`) had launched on the pre-fix image — this redeploy is what those needed. Repo:
      market-tick-data-service / deployment-service (VM tarball build).
- [x] [DATA] P1 ✅ **DONE (2026-07-15 ~23:37Z) — 627 pre-genesis rows cleaned live; HELD across 3 consolidator merge
      cycles.** Cleaned the 627 pre-genesis (`2020-01-01..01-19`) `attempted_failed[UPSTREAM_INSTRUMENTS_CATALOG_STALE]`
      rows via a controlled foreground re-collect with the FIXED code (`market-tick-data-service@42527190`, carries
      `420221b4`), not a bespoke reclassify. **Resurrection vector found**: the 551 `dex_pool_state` rows lived in the
      per-VM shard `_index/per_vm/mtds-dex-pools-backfill.parquet` — written by the STILL-RUNNING
      `mtds-dex-pools-backfill` VM (created 12:19Z, pre-fix image) which re-presents `attempted_failed@12:22Z` to the
      consolidator every ~1-min cycle; the 76 `lst_rates` rows were canonical-only (their VM
      `mtds-lst-rates-20260715-121257` had already exited, no shard; `_legacy_seed.parquet` held none of them).
      **HOLD-SAFE method**: writing the LIVE dex VM's own shard would race it (per-VM writes hold only a process-local
      lock, no cross-process CAS → lost-update), so ran
      `collect-dex-pools`/`collect-lst-rates --mode batch --asset-group DEFI --start-date 2020-01-01 --end-date 2020-01-19`
      into a DEDICATED per-VM shard `_index/per_vm/mtds-defi-pregenesis-cleanup-20260715.parquet` (627 rows,
      `attempted_at` 22:17–22:44Z ≫ the stale 12:15–12:22Z) so the consolidator's last-write-wins (`attempted_at DESC`)
      makes the correct rows dominate BOTH the live dex shard and the canonical-only lst rows AT SOURCE (a real merged
      shard, not a canonical-only edit). **Before → after** (canonical `_index/availability_index.parquet`): pre-genesis
      `attempted_failed[UPSTREAM_INSTRUMENTS_CATALOG_STALE]` **627 → 1**; **626 →
      `empty_confirmed[EXPECTED_PRE_VENUE_LAUNCH]`** (550 dex + 76 lst). The 1 remaining is `CURVE-ETHEREUM 2020-01-19`
      (Curve's exact launch date → at/after effective-earliest → correctly a genuine 1-day catalogue-boundary
      `attempted_failed`, i.e. the documented 626/627 split, now re-stamped `attempted_at 22:33Z` by the fixed code, not
      the old 12:22Z). **HOLD proof (no resurrection)**: verified across 3 consecutive consolidator merges that each
      re-read the live dex shard (still holding all 551 `attempted_failed@12:22Z`): canonical mtime **23:15:15Z**
      (absorbed → 626 empty), **23:23:33Z** (held), **23:36:47Z** (held — with the cleanup shard now EXCLUDED behind the
      content-write cutoff, so ONLY the canonical baseline defends → airtight). Merge-#3 report:
      `success=True shards=3 rows_in=29,810,608 rows_out=28,441,749 error=-`. **Residual risk closed by [DEPLOY] P1**:
      the hold holds while no OLD-image process writes a newer-`attempted_at` `attempted_failed` for these dates — the
      running dex VM won't (forward walk, long past 2020-01), but a future backfill on the pre-fix image re-walking
      2020-01 could, which is exactly what [DEPLOY] P1 (redeploy the fixed image) prevents. The dedicated cleanup shard
      is LEFT in place (harmless, 627 rows; re-provides the correct classification on any future `--force` full
      rebuild). Repo: market-tick-data-service.
- [ ] [DESIGN] P3. IS-DeFi-catalogue-completion-signal retry-sweep — **RE-SCOPED by the 2026-07-15 re-investigation:
      this is NOT what the 627 recurring rows needed** (they are pre-genesis; no completion signal will ever fire for
      pre-2020-01-20 dates — the classification fix `420221b4` is the correct + complete remedy for that class). P3
      remains a valid nice-to-have ONLY for the genuine catalogue-behind class (a POST-genesis date whose per-date
      snapshot the backfill hasn't reached yet) — which, after `420221b4`, is now the ONLY thing the gate still labels
      `attempted_failed`. Lower priority; not a fix to something that mostly exists. Repo: market-tick-data-service /
      deployment-service (whichever owns the IS catalogue backfill scheduling).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - sole residual is an explicit [DESIGN] P3 nice-to-have
  (IS-catalogue completion-signal retry-sweep) with no concrete done-when

- 2026-07-15: Investigated per `data_pipeline_alerts_batch_remediation_2026_07_15.md`'s "New todos" entry for
  `defi/dex_pool_state` + `defi/lst_rates`. Live-requeried the manifest (current counts above, close to but not
  identical to the operator's cited numbers — dex_pool_state's tail is 06-25 not 06-30). Determined root cause via
  direct shard-date-vs-attempted-date comparison (0% same-day → 100% historical backfill) + `gcs_describe_object()`
  blob-timestamp proof (catalogue snapshots for the affected historical dates were written 2026-06-29, after every
  affected attempt) — a temporal race between the IS DeFi historical catalogue backfill completing and these MTDS
  attempts, NOT a broken/regressed freshness gate. Found + fixed a real, adjacent code gap (`lst_rates_handler.py`
  missing `mode=` threading, 1 of 9 DeFi handlers with this gap) with 3 new regression tests — shipped via quickmerge.
  Data remediation (re-collecting 2,958 affected shards) deliberately NOT executed — flagged as a properly-scoped
  follow-up with exact commands, per this task's own instruction not to force a rushed large-scope live-API operation.
  Issue filed per the workspace's findings-triage HARD RULE (data-correctness, big finding).
- 2026-07-15 ~17:25Z (RE-INVESTIGATION, adversarial, live evidence): the "temporal race, not a live regression"
  characterization was WRONG for the recurrence. Confirmed 627 NEW rows live (551 dex_pool_state @12:22Z + 76 lst_rates
  @12:15-16Z), ALL for shard dates 2020-01-01..01-19, `batch_onchain_subgraph`. Identified the exact writers: two
  RUNNING backfill VMs (`mtds-dex-pools-backfill` created 12:19:56Z, `mtds-lst-rates-20260715-121257` created 12:13:04Z)
  — the [DATA] P1 re-collect launched as VMs today. Read the current code: `dex_pools_handler` ALREADY threads `mode=`,
  so `927acf01`'s lst-only fix never covered the dominant data_type and was NOT the recurrence cause.
  `gcloud storage ls` proved the IS DeFi catalogue's earliest `by_date` snapshot is `day=2020-01-20` — the 19 failing
  dates are PRE-GENESIS (before the DeFi universe existed; Curve launched 2020-01-19, most protocols/chains later).
  Root-cause verdict: a THIRD category, not (a)/(b) — a data-correctness CLASSIFICATION bug. The gate correctly finds no
  catalogue, but all 11 DeFi handlers only ever recorded `record_failed(UPSTREAM_INSTRUMENTS_CATALOG_STALE)` for a
  gate-block, never the `record_empty` the gate's own docstring prescribes — so a permanent pre-genesis absence was
  stamped as a retryable failure, re-piling every backfill re-walk. Fixed at root cause:
  `market-tick-data-service@420221b4` (new `DefiManifestRecorder.record_catalog_unavailable` splits pre-effective-launch
  → `EXPECTED_PRE_VENUE_LAUNCH` (honest empty) vs at/after → `UPSTREAM_INSTRUMENTS_CATALOG_STALE` (retryable), via the
  UAC-SSOT `max(chain_genesis, protocol_launch)` composition; wired into both named handlers; 4 new tests + 2 updated;
  `quality-gates.sh --no-fix` GREEN). Verified 626/627 rows resolve to honest empty (the 1 exception, CURVE-ETHEREUM on
  its 2020-01-19 launch date, correctly stays a 1-day catalogue-boundary gap). Fix is forward-only: the running VMs are
  on the pre-fix image, so the 627 already-written rows + a NEXT-backfill re-emit both need the fixed image deployed —
  added [DEPLOY] P1 + [DATA] P1 (re-collect 2020-01-01..19 with the fixed image, which rewrites them as
  `empty_confirmed`). Full raw evidence in § "RE-INVESTIGATED 2026-07-15 ~17:25Z".

- 2026-07-15 ~22:15–23:37Z ([DATA] P1 DONE — 627 pre-genesis rows cleaned + HELD). Re-confirmed the 627 live in
  `market-data-tick-defi-prd` canonical (551 dex + 76 lst, `attempted_at` 12:15–12:22Z). **Resurrection vector**: the
  551 dex rows are re-emitted every consolidator cycle by the STILL-RUNNING `mtds-dex-pools-backfill` VM's per-VM shard
  `_index/per_vm/mtds-dex-pools-backfill.parquet` (pre-fix image); the 76 lst rows were canonical-only (lst VM gone, no
  shard). **Cleanup (HOLD-SAFE)**: instead of racing the live dex shard, re-collected `2020-01-01..01-19` with the fixed
  code into a DEDICATED shard `_index/per_vm/mtds-defi-pregenesis-cleanup-20260715.parquet` (627 rows, `attempted_at`
  22:17–22:44Z) so last-write-wins dominates the stale 12:22Z rows at source. **Result 627 → 1**: 626 →
  `empty_confirmed[EXPECTED_PRE_VENUE_LAUNCH]`, the 1 (`CURVE-ETHEREUM 2020-01-19`, Curve's launch date) correctly stays
  `attempted_failed` (catalogue-boundary). **HELD across 3 real consolidator merges** (canonical writes 23:15:15Z
  absorb, 23:23:33Z hold, 23:36:47Z hold-with-cleanup-shard-EXCLUDED = airtight baseline-only proof) — each re-read the
  live dex shard's 551 stale rows and did NOT resurrect them. Op note: the defi consolidator was stuck behind
  stale/long-merge locks on entry; cleared 2 (verified past-TTL, dead holders) to unblock merges — harmless (CAS-guarded
  canonical write), and observed defi merges take ~10–33 min (single-threaded 104-chunk incremental) holding the lock
  the whole time, so a <~30-min held lock here is a live merge, not a crash. Evidence:
  `market-tick-data-service@42527190`.

## REOPENED — this is NOT a purely historical/static issue; actively recurring post-fix (2026-07-15 ~15:30Z)

The `927acf01` fix + the "temporal race, not a broken gate" root cause above were characterized elsewhere (the main
remediation plan's continuation-session close-out) as meaning these cells were "static historical... not a live
regression." **That characterization is wrong, and was caught by adversarial verification the operator explicitly asked
for.** A fresh live re-query of `market-data-tick-defi-prd` (refreshed today) found **627 NEW `attempted_failed` rows
(551 `dex_pool_state`, 76 `lst_rates`) timestamped 2026-07-15T12:16-12:22Z — TODAY, over an hour AFTER the `927acf01`
fix landed at 11:12Z** — same `error_reason=UPSTREAM_INSTRUMENTS_CATALOG_STALE` as the original finding.

This means one of two things, not yet determined: (a) the `927acf01` fix (threading `mode=` through
`lst_rates_handler.py`) was necessary but not sufficient — some OTHER code path (a different handler, a different
trigger) is still hitting the same stale-catalogue race live, right now; or (b) a genuinely NEW backfill/attempt run
happened today that re-triggered the same historical temporal-race pattern against dates the IS catalogue still hasn't
caught up on, meaning the underlying race condition (IS catalogue backfill completion vs. MTDS attempt timing) is not
just a one-off historical artifact but a recurring structural gap that will keep producing new failed rows every time a
similar backfill/attempt runs.

**Needs real investigation, not another bookkeeping pass**: identify what actually ran/wrote these 627 rows at
12:16-12:22Z today (check recent VM launches, manual `gcloud run jobs execute` invocations, or scheduled backfill jobs
active in that window), confirm whether it went through the now-fixed `lst_rates_handler.py` path or a different one,
and determine whether this is (a) a residual gap in the `927acf01` fix's scope, or (b) evidence the [DESIGN] P3 todo
below (an IS-catalogue-backfill completion signal MTDS could subscribe to, currently marked out-of-scope) needs to be
promoted to an actual fix rather than left as a "nice to have."

Status intentionally left `open` — reclosing/reconciling this as "stale bookkeeping" without addressing the live
127-hour recurrence would repeat the exact overclaiming pattern this correction exists to fix.

## RE-INVESTIGATED 2026-07-15 ~17:25Z — root cause FOUND (a third category, not (a) or (b) as framed) + code fix shipped

Adversarial re-investigation with live evidence (not inference). **Verdict: neither (a) a residual `mode=` gap nor (b)
"the IS catalogue backfill hasn't caught up yet" — it is a THIRD thing: a data-correctness CLASSIFICATION bug. The gate
correctly finds no catalogue for pre-genesis dates, but the handler mislabels that PERMANENT, expected absence as a
retryable `attempted_failed`.** Fixed at root cause in `market-tick-data-service@420221b4`.

### 1. The 627 rows confirmed live (re-queried `market-data-tick-defi-prd` availability_index, 2026-07-15 ~17:10Z)

| data_type      | rows | `attempted_at` window (UTC)      | shard `date` range    | same-day? | pipeline_mode            |
| -------------- | ---: | -------------------------------- | --------------------- | --------- | ------------------------ |
| dex_pool_state |  551 | 2026-07-15T12:22:20 .. T12:22:55 | **2020-01-01..01-19** | 0%        | `batch_onchain_subgraph` |
| lst_rates      |   76 | 2026-07-15T12:15:20 .. T12:16:01 | **2020-01-01..01-19** | 0%        | `batch_onchain_subgraph` |

Shape = a clean cross-product: dex 29 (protocol×chain) × 19 dates = 551; lst 4 sentinels (LIDO/ETHERFI/ETHENA-ETHEREUM,
MARINADE-SOLANA) × 19 dates = 76. Every shard date is **2020-01-01 through 2020-01-19** — 0% same-day, all historical.

### 2. What WROTE them (exact writers, not inferred) — two RUNNING backfill VMs

`gcloud compute instances list` (both clouds) — two RUNNING GCE VMs, timing matches to the second:

- `mtds-dex-pools-backfill` — created **2026-07-15T12:19:56Z** (`VM_OPERATION`/`VM_START_DATE` metadata) → wrote the 551
  `dex_pool_state` rows at **12:22Z**.
- `mtds-lst-rates-20260715-121257` — created **2026-07-15T12:13:04Z** → wrote the 76 `lst_rates` rows at
  **12:15–12:16Z**.

These are the issue's own § "Exact commands for the follow-up" [DATA] P1 re-collect, launched as backfill VMs today.
They walk from 2020-01-01 forward; the 627 rows are the tail of the run's **first 19 days** (2020-01-01..19). No Cloud
Run job executions in the window (defi collection is VM-driven, not Cloud Run).

### 3. Which code path (read the actual current code)

- **`dex_pool_state` (551, dominant)**: `dex_pools_handler._run_process` **already threads
  `mode=("live" if _run_tag == "live" else "batch")`** into `assert_defi_catalog_fresh` (`dex_pools_handler.py:646-651`)
  — it was NEVER missing the `mode=` fix. So `927acf01`'s scope was irrelevant to the dominant data_type.
- **`lst_rates` (76)**: `lst_rates_handler._check_preflight` threads `mode=` post-`927acf01`
  (`lst_rates_handler.py:430-436`).
- Both used `mode=batch` → `assert_defi_catalog_fresh._use_coverage=True` → `_assert_defi_catalog_covers_date()` probes
  `instrument_availability/by_date/day=<date>/` in `instruments-store-defi-prd`. The gate returned False (no snapshot),
  and BOTH handlers' gate-failed branches then recorded **every** venue/chain as
  `record_failed(UPSTREAM_INSTRUMENTS_CATALOG_STALE)`.

### 4. Root-cause verdict — the catalogue for these dates does not exist and NEVER will (pre-genesis), so `attempted_failed` is a lie

`gcloud storage ls` on `gs://instruments-store-defi-prd-central-element-323112/instrument_availability/by_date/`: the
**earliest** snapshot is **`day=2020-01-20`** (then continuous). There is NO snapshot for 2020-01-01..01-19 — the exact
19 dates these 627 rows are for. This is not "the backfill hasn't caught up yet" (theory b): 2020-01-20 is the genuine
**genesis** of the IS DeFi catalogue, because essentially no DeFi instrument universe existed before then (Curve
launched 2020-01-19, Uniswap V3 2021-05, GMX 2021-09, Aerodrome 2023, most chains — ARBITRUM 2021-08-31, BASE
2023-08-09, AVALANCHE/BSC/POLYGON 2020-08..09 — all post-date 2020-01-19). The catalogue will never cover pre-genesis
dates.

So `assert_defi_catalog_fresh`'s docstring/`_assert_defi_catalog_covers_date` was already right that absence should
route "`record_failed`/**`record_empty`** per shard" — **but the `record_empty` branch was never implemented**; every
one of the 11 DeFi handlers only ever called `record_failed(UPSTREAM_INSTRUMENTS_CATALOG_STALE)`. A permanent, expected,
pre-DeFi- universe absence was being stamped as a retryable fetch failure. That is why it "actively recurs": each
backfill re-walk of 2020-01 re-stamps 627 fresh `attempted_failed` rows with today's `attempted_at`, re-firing
`DP_RUN_MOSTLY_EMPTY` as a false live-regression. The correct honest-coverage classification is
`empty_confirmed[EXPECTED_PRE_VENUE_LAUNCH]`.

### 5. The fix (`market-tick-data-service@420221b4`)

New `DefiManifestRecorder.record_catalog_unavailable(...)` (`_defi_manifest.py`) + module helper
`_defi_effective_earliest_date(venue, chain)` = the UAC-SSOT composition
`max(get_chain_genesis_date(chain), get_protocol_launch_date(chain, venue))`
(`unified_api_contracts.registry.chain_env`). On a catalog-gate block: if `target_day < effective earliest` →
`record_empty(EXPECTED_PRE_VENUE_LAUNCH)` (honest empty, keystone-exempt — nothing existed to fetch); else →
`record_failed(UPSTREAM_INSTRUMENTS_CATALOG_STALE)` (unchanged — the genuine catalogue-behind/temporal-race case, theory
(b), which a retry-sweep DOES fix). Wired into `dex_pools_handler` + `lst_rates_handler` gate-failed branches (both
named in this alert). Verified the composition against all 33 affected venue-chains: **626 of 627 rows** resolve to
pre-effective-launch → honest empty; the 1 remaining (`CURVE-ETHEREUM` on 2020-01-19, Curve's exact launch date)
correctly stays as a genuine 1-day catalogue-boundary gap. 4 new regression tests (`test_defi_manifest_recorder.py`:
helper composition + pre-genesis→empty + post-launch→stale + LST-Solana pre-genesis) + 2 existing stale-catalog tests
updated; `quality-gates.sh --no-fix` GREEN (6127 passed), sentinel==HEAD.

### 6. Why this does NOT need the [DESIGN] P3 completion-signal, and why the recurrence still needs 2 follow-ups

- **[DESIGN] P3 (IS-catalogue-completion-signal retry-sweep) is NOT what these 627 rows needed** — that would help
  theory (b) (dates the catalogue eventually covers). These dates are pre-genesis; no completion signal will ever fire
  for them. The classification fix is the correct and complete remedy for the pre-genesis class. P3 remains a valid
  nice-to-have for the genuine catalogue-behind class only (now correctly the ONLY thing left labelled
  `attempted_failed` by the gate).
- **Forward-only + running-VM caveat (honest)**: the two backfill VMs above launched on the PRE-fix image (12:13/12:19Z,
  hours before `420221b4` at ~17:25Z), so THIS run's 627 rows are already written and this run has already walked past
  the 2020-01 window (won't re-emit more this pass). The fix prevents the recurrence on the NEXT backfill only once the
  fixed image is deployed. The 627 already-written rows persist until re-collected with the fixed image (or
  reclassified). Both captured as follow-ups below.

## 2026-07-26 (slot-12, `data_engineering`) — redeploy + re-collect follow-ups closed as a documented monitored handoff

Picked up the two remaining follow-ups (`[DATA] P1` re-collect, `[DEPLOY] P1` redeploy) from
`plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md`.

**Redeploy**: found the deployed `mtds-code.tar.gz` manifest was ALREADY at `d09705ff` (7 commits past `420221b4`) —
someone/something had refreshed the tarball since 2026-07-15. Rebuilt anyway to current HEAD `ec0df8784b17`
(`v0.93.0-550-gec0df878`) via `deployment-service/scripts/vm/create-code-tarballs.sh` for a clean baseline; verified
live at `gs://deployment-scripts-central-element-323112/code/mtds-code.manifest.json`.

**Re-collect launch**: launched `mtds-dex-pools-backfill` (2020-01-19..2026-06-25) and `mtds-lst-rates-20260726-035545`
(2020-01-01..2026-06-29), both SPOT, via the registered launchers with the redeployed image (tarball-freshness check
passed for all 4 core repos). Both verified healthy via serial console (exact intended CLI args confirmed, PIDs running)
and via `run.log` (real per-VM manifest-shard writes advancing every few seconds — not stalled/preempted).

**Surprising finding — the remediation target was already resolved before this pass touched anything**: live-queried
`market-data-tick-defi-prd-central-element-323112`'s `availability_index.parquet` (16.9M rows across the two data_types)
~60s after VM launch (before either VM could have meaningfully rewritten historical shards):
`UPSTREAM_INSTRUMENTS_CATALOG_STALE` is **0 for both `dex_pool_state` and `lst_rates`** — none of the 2,958 rows this
issue named remain in that class. Remaining `attempted_failed` is 19 `build_instrument_id` (dex_pool_state) + 2
`429 POST https` (lst_rates), both unrelated transient classes this issue explicitly carved out. `dex_pool_state`
`empty_confirmed` already shows 754 `EXPECTED_PRE_VENUE_LAUNCH` rows (the `420221b4` fix's target reason, confirmed
live) plus 428,311 `EXPECTED_NOT_ENOUGH_TVL` + 5,254 `SOURCE_RETURNED_ZERO` (unrelated honest-empty reasons). This means
routine backfill/cron activity in the 11 days since this issue was filed had already re-walked and correctly
reclassified the affected historical range — this pass's launch is a confirmatory re-walk, not the operation that fixed
the classification.

**Documented monitored handoff**: both VMs are walking the full multi-year range for real (not skip-fast — observed
genuine per-date API calls), which will take multiple hours to reach `VM_SHUTDOWN_ON_COMPLETION=true` self-delete. Since
the classification target is already verified at 0 and this issue's own Done-when explicitly accepts "run to completion
OR a documented monitored handoff," the `[DATA] P1` and `[DEPLOY] P1` follow-up checkboxes above are flipped now on the
redeploy+launch+before-evidence, not on VM self-termination. Status left `open` (not `resolved`) — the `[SCRIPT] P3`
mode-threading residual and `[DESIGN] P3` completion-signal items remain genuinely unaddressed.

- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries, unchanged) — all resolve; still the right minimal
  set for the sole remaining [DESIGN] P3 nice-to-have (catalogue-completion-signal retry-sweep).
- **na-eligibility-audit 2026-08-04** (tranche=defi, dispatch agt-62865a): KEEP-NA valid (prior verdict re-affirmed) —
  sole remaining item ([DESIGN] P3, IS-catalogue completion-signal retry-sweep) stays an explicit lower-priority design
  task with no concrete done-when and ambiguous ownership; all other items already done/resolved with evidence. Doc
  stays `assigned_vm: NA`.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; no content change
  since the 2026-08-04 audit (context-scout metadata only, per git log). Sole open item ([DESIGN] P3,
  IS-catalogue-completion-signal retry-sweep) remains a lower-priority design task with no concrete done-when; every
  other item already resolved with evidence. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Sole open checkbox (`[DESIGN] P3`,
  IS-catalogue-completion-signal retry-sweep) is an explicit lower-priority nice-to-have with no concrete done-when and
  unresolved ownership ("whichever owns the IS catalogue backfill scheduling"). Multiple prior audits
  (2026-07-30/08-04/08-07) reached KEEP-NA on this same basis. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries)

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
    ../../../codex/02-data/availability-manifest-and-data-status.md,
    ../../../codex/02-data/honest-absence-downstream-handling.md,
    ../../../codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: 2026-07-15
parent_epic: infrastructure_master
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
    regression tests)",
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

- [ ] [DATA] P1. Execute the re-collect commands above (or launch as a proper monitored backfill job/VM per this
      workspace's backfill conventions) once scoped; verify before/after counts; this is what actually clears the
      `DP_RUN_MOSTLY_EMPTY` alert for both cells. Repo: market-tick-data-service.
- [ ] [SCRIPT] P2. Thread `mode=` into the remaining 8 DeFi handlers sharing the same gap (`token_transfers_handler.py`,
      `liquidations_handler.py`, `flash_loan_events_handler.py`, `bridge_events_handler.py`,
      `native_staking_handler.py`, `liquidation_events_handler.py`, `lending_indices_handler.py`,
      `aggregator_route_handler.py`, `solana_defi_handler.py`) — same pattern as this issue's `lst_rates_handler.py`
      fix. Defense-in-depth; none of these were proven to have caused a live incident (unlike `lst_rates_handler.py`,
      which is directly named in this alert), so this is lower priority. Repo: market-tick-data-service.
- [ ] [DESIGN] P3. Consider whether the IS DeFi historical catalogue backfill (the job that wrote the
      `instrument_availability/by_date/day=<date>/` snapshots on 2026-06-29) should emit a completion signal/event that
      MTDS's stale-catalog-failed shards could subscribe to for an automatic retry-sweep, rather than relying on a
      manual re-probe/re-collect after the fact — the exact gap R5-fix-7 was trying to close. Out of scope here (new
      infra, not a fix to something that mostly exists). Repo: market-tick-data-service / deployment-service (whichever
      owns the IS catalogue backfill scheduling).

## Progress Log

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

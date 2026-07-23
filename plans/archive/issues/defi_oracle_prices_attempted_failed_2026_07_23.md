---
doc_type: issue
title:
  "DP_RUN_MOSTLY_EMPTY (defi/oracle_prices, 1026 attempted_failed) is 100% PYTH-SOLANA `aiodns`-resolver-crash residual,
  NOT the METEORA/LIFINITY/PHOENIX/CHAINLINK dead-upstream narrowing -- already fixed pre-alert by
  market-tick-data-service@533514c2"
summary: >-
  Slack `data-pipeline-alerts` fired DP_RUN_MOSTLY_EMPTY CRITICAL twice (2026-07-22 23:16 and 2026-07-23 00:02) for
  `asset_group=defi data_type=oracle_prices`: 1026 attempted_failed cells, flat across both firings while `attempted`
  grew 75750->77267. The task hypothesis (that this is residual from the METEORA/LIFINITY/PHOENIX/CHAINLINK dead-
  upstream narrowing in `uac_is_defi_oracle_dex_adapter_drift_2026_07_20.md`) is DISPROVEN by direct manifest sampling
  -- those are DEX-pool (`dex_pool_state`) venues, not `oracle_prices` venues, and a scoped predicate-pushdown read of
  the 1026 attempted_failed cells shows 100% venue=PYTH, chain=SOLANA, pipeline_mode=batch_pyth_hermes,
  error_reason="Resolver requires aiodns library" -- zero CHAINLINK/METEORA/LIFINITY/PHOENIX rows. This is the SAME bug
  class as the LST-rates aiodns-resolver crash root-caused earlier the same day: `oracle_prices_handler.py`'s two Pyth
  Hermes call sites constructed `aiohttp.resolver.AsyncResolver()` directly (no `aiodns` fallback), which raises on any
  VM/venv missing the optional `aiodns`/`pycares` packages, crashing HTTP-session creation for every attempt. Already
  fixed as a "good-citizen" bundle in `market-tick-data-service@533514c2` (2026-07-22 18:12:55 UTC, shipped to LDR
  before both alert firings) via the new `_http_resolver.make_resilient_connector()` fallback. The 1026 count is pre-fix
  sticky residual (capture_status doesn't self-heal without a re-attempt); the flat-count signature across both firings
  is consistent with no NEW failures landing post-fix.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags:
  [
    defi,
    oracle,
    oracle_prices,
    pyth,
    aiodns,
    resolver,
    manifest,
    data-pipeline-alerts,
    DP_RUN_MOSTLY_EMPTY,
    honest-coverage,
  ]
related:
  - uac_is_defi_oracle_dex_adapter_drift_2026_07_20.md
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
source: >-
  Investigation of a real `data-pipeline-alerts` Slack CRITICAL firing (DP_RUN_MOSTLY_EMPTY, bucket
  `market-data-tick-defi-prd-central-element-323112`), 2026-07-23, dispatched alongside a separate agent's CeFi-cluster
  investigation of the same alert class.
resolved_by:
  "market-tick-data-service@533514c2 ('fix(defi): aiodns-missing resolver crash silently dropped Solana LST rates on
  every backfill day', 2026-07-22 18:12:55 UTC), promoted to main via 7c7cbb83 (2026-07-22 19:39:22+01:00) -- both
  BEFORE the alert's two firings (23:16 and 00:02 UTC)."
---

# DP_RUN_MOSTLY_EMPTY defi/oracle_prices -- verdict: pre-fix `aiodns` residual, already resolved

## The alert

```
Event: DP_RUN_MOSTLY_EMPTY, Severity: CRITICAL
Asset group: defi/oracle_prices, Data type: oracle_prices
Summary: high attempted_failed batch -- asset_group=defi data_type=oracle_prices: 1026 attempted_failed cells of 75750
attempted (ratio 1.4%) [second firing: 1026 of 77267, ratio 1.3%] -- a backfill exited 0 / captured climbed but failed
this batch invisibly.
```

Fired via `deployment_service.data_pipeline_monitors.meta_watchers.check_high_attempted_failed` (DP-FETCH-009), which
reads the SAME consolidated `_index/availability_index.parquet` blob the manifest consolidator writes, filtered to
`(asset_group, data_type)` and thresholded on `attempted_failed` count/ratio (`ATTEMPTED_FAILED_ABS_THRESHOLD` /
`ATTEMPTED_FAILED_RATIO_THRESHOLD` in `meta_watchers.py`).

## Hypothesis given (task brief) -- TESTED AND DISPROVEN

The dispatch brief's working hypothesis was that this is residual footprint from the METEORA/LIFINITY/PHOENIX
dead-upstream narrowing in `plans/active/issues/uac_is_defi_oracle_dex_adapter_drift_2026_07_20.md` (`status: resolved`,
closed 2026-07-22 by `unified-api-contracts@9a047a31` + `instruments-service@52a1cb53`).

Reading that issue doc closely: **METEORA/LIFINITY/PHOENIX are DEX-pool venues** -- the 2026-07-22 fix's golden regen
"removed exactly the 3 `(VENUE, 'pool', 'dex_pool_state')` tuples", i.e. `data_type=dex_pool_state`, not
`oracle_prices`. They are not in `oracle_prices`'s venue set at all (confirmed via
`unified-api-contracts/unified_api_contracts/registry/expected_coverage.py` -- the `oracle_prices` producers are
`CHAINLINK-*` ×5, `PYTH`/`PYTH-SOLANA`, and lending venues that also emit reserve-oracle prices as a side-channel
(`AAVE-ETHEREUM`, `MORPHO-*`, `COMPOUND_V3-*`, etc.) -- never METEORA/LIFINITY/PHOENIX). **CHAINLINK** IS an
`oracle_prices` venue and WAS narrowed (phase `live`->`pipeline`, `VENUE_TO_ADAPTER_KEY` entry removed,
`expected_coverage` row removed) in the same 2026-07-22 session -- a plausible-sounding candidate cause on venue-name
grounds alone. Direct manifest sampling (below) rules it out too: zero CHAINLINK rows in the 1026.

## Direct measurement (read-only, scoped, NOT a full-corpus walk)

Ran a predicate-pushdown `pyarrow.dataset` read against the live consolidated index, filtered to
`asset_group=='defi' AND data_type=='oracle_prices'` at the row-group level (never loading the full 6.16M-row index) --
returned 78,030 rows in 29.3s (small relative to the corpus; scoped to exactly the alert's cell):

```python
import pyarrow.dataset as ds, pyarrow.compute as pc
d = ds.dataset("gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet", format="parquet")
filt = (pc.field("asset_group") == "defi") & (pc.field("data_type") == "oracle_prices")
table = d.to_table(columns=[...], filter=filt)   # 78030 rows, 29.3s
```

```
capture_status
captured            76569
attempted_failed      1026
empty_confirmed        435
```

Breakdown of the 1026 `attempted_failed` rows -- **100% concentrated on one venue, one error**:

| Field           | Value                              | Count |
| --------------- | ---------------------------------- | ----- |
| `venue`         | `PYTH`                             | 1026  |
| `chain`         | `SOLANA`                           | 1026  |
| `pipeline_mode` | `batch_pyth_hermes`                | 1026  |
| `error_reason`  | `Resolver requires aiodns library` | 1026  |

Zero rows for CHAINLINK, METEORA, LIFINITY, or PHOENIX in this cell -- the hypothesis's specific venues are absent from
`oracle_prices` entirely, and even the one plausible `oracle_prices` candidate (CHAINLINK) contributes nothing to the
failure count.

### Safety caveat on this read (mid-flight concurrent migration)

This read ran WHILE a separate agent's canonical-migration + manifest-rebuild VM
(`canonical-migration-defi-rebuild-20260722-194751`) was actively writing to
`_index/per_vm/canonical-migration-defi-rebuild-20260722-194751.parquet` and eventually the main
`_index/availability_index.parquet` on the SAME bucket. The scoped read above succeeded once; **a second, follow-up
attempt to pull `date`/`attempted_at` columns for date-range confirmation failed with
`FileNotFoundError: No such object: .../_index/availability_index.parquet`** moments later -- direct evidence the main
index object was mid-replacement by the concurrent rebuild at that instant. No further reads were attempted against the
main index after that (per the dispatch brief's read-only/no-heavy-read constraint); the qualitative finding (100% PYTH
/ 100% one error_reason) is unambiguous from the one successful read and does not depend on precise date-range
confirmation, but treat the exact 78,030/1026/76569/435 row counts as a single point-in-time snapshot during an active
rebuild, not certainly fully consistent with the alert's own 75750/77267 attempted totals (same order of magnitude,
small drift expected from timing + the rebuild in flight).

## Root cause (read directly from source + git history)

`market_tick_data_service/cli/handlers/oracle_prices_handler.py`'s two Pyth Hermes HTTP-session call sites constructed
`aiohttp.resolver.AsyncResolver()` **directly**, unchanged since at least 2026-06-23 (`9ec9d3e4`). `AsyncResolver`
(c-ares-backed, via the optional `aiodns`/`pycares` packages) raises `RuntimeError("Resolver requires aiodns library")`
in its own `__init__` if those packages aren't importable -- and on any MTDS VM/venv built from a tarball missing
`aiodns` (confirmed 2026-07-22: `aiodns` was only present _transitively_ via `ccxt`, and the tarball-built venv on
`mtds-lst-rates-*` didn't include it), that crash happens on **every single attempt**, producing an `attempted_failed`
row with exactly this `error_reason` -- matching the sample 1-for-1.

This is not new detective work on my part -- it's the exact bug class root-caused THE SAME DAY for a different
oracle_prices sibling leg (Solana LST rates), documented in `plans/active/lst_rate_honest_coverage_2026_07_21.md`
Progress Log, 2026-07-22 entry "Phase 5 #4":

> "`lst_rates_handler.py`'s `_fetch_solana_lst_rates` wrapped session creation in a bare
> `try/except Exception: return []`, so this ONE missing optional dependency silently dropped the whole data leg...
> Added a shared `market_tick_data_service/_http_resolver.py::make_resilient_connector()`... and wired it into ALL THREE
> call sites that hard-required `AsyncResolver` in this codebase: `lst_rates_handler.py` (the one actually blocking this
> backfill), and **as a good-citizen fix, `oracle_prices_handler.py`'s two Pyth Hermes call sites (same bug pattern, not
> yet observed to fail** -- the AAVE oracle VM's earlier success suggests either a different tarball build or the code
> path wasn't exercised the same way**)** and `deribit_options_chain_handler.py`..."

I.e. the fixing session explicitly flagged `oracle_prices_handler.py` as "same bug pattern, not yet observed to fail" at
fix time -- this investigation is the first direct confirmation that it HAD, in fact, already failed (1026 times,
historically, before the fix landed).

## Fix already shipped -- BEFORE both alert firings

`market-tick-data-service@533514c2` ("fix(defi): aiodns-missing resolver crash silently dropped Solana LST rates on
every backfill day", **2026-07-22 18:12:55 UTC**) added `_http_resolver.py::make_resilient_connector()` (prefers
`AsyncResolver`, catches `ImportError | RuntimeError | OSError`, falls back to aiohttp's default `ThreadedResolver`
instead of raising -- `AsyncResolver` is a pure performance optimization, never a functional requirement) and rewrote
both `oracle_prices_handler.py` call sites to use it (`git show --stat 533514c2` confirms
`cli/handlers/oracle_prices_handler.py | 8 ++--` in the diff). Promoted LDR-is-SSOT via `7c7cbb83` ("chore(promote): LDR
-> main (Option-B direct)", 2026-07-22 19:39:22+01:00 = 18:39:22 UTC). Verified currently an ancestor of
`origin/live-defi-rollout` (tip `2e75627c` at 2026-07-22 21:51:11 UTC):

```
$ git merge-base --is-ancestor 533514c2 origin/live-defi-rollout && echo ancestor
ancestor
```

**Both Slack firings (23:16 UTC 2026-07-22, 00:02 UTC 2026-07-23) postdate the fix by 4-6 hours.** The 1026
`attempted_failed` rows are pre-fix residual: `capture_status` is sticky (a row marked `attempted_failed` is not
retroactively corrected -- it persists until something explicitly re-attempts that exact shard). This exactly explains
the dispatch brief's own observed signature -- flat `attempted_failed` (1026 -> 1026) while `attempted` grows (75750
-> 77267) between the two firings: new attempts (other venues/days, post-fix) are landing as `captured` fine, but the
specific 1026 already-marked-failed PYTH/SOLANA shards have not been re-attempted within the alert's window, so their
count neither grows (no new failures -- the crash is fixed) nor shrinks (nothing has re-run them yet).

## Verdict

**CLOSED / self-resolving residual -- but via a DIFFERENT already-shipped fix than the task's working hypothesis, not
the METEORA/LIFINITY/PHOENIX/CHAINLINK narrowing.** That issue doc is cross-linked in `related:` because the dispatch
brief named it as the leading hypothesis and it's worth the explicit disproof on record, but it is NOT causally
connected to this alert -- zero overlap in venues, mechanism, or fix commit. This alert's actual root cause and fix are
fully contained in `market-tick-data-service@533514c2` / `plans/active/lst_rate_honest_coverage_2026_07_21.md`.

No code action required here. The alert should stop re-firing once the miss-tracker's consecutive-miss window elapses
past the last NEW high-ratio sweep, since no new `attempted_failed` rows are being produced (assuming no stale
pre-533514c2 VM tarball is still deployed anywhere -- not independently checked here, out of scope for a read-only
manifest investigation; flagged as a residual unknown, not a claim).

## What is NOT claimed

- Whether every currently-deployed MTDS VM/tarball has picked up `533514c2` was not verified -- if a stale pre-fix
  tarball is still running somewhere, oracle_prices/PYTH could resume failing and the flat-count signature would break
  (attempted_failed would start climbing again). Worth a fleet tarball-freshness check if this alert re-fires with a
  GROWING count.
- The exact 78,030-row snapshot (captured/attempted_failed/empty_confirmed breakdown) is not guaranteed byte-identical
  to the alert's own 75750/77267 totals -- see the mid-rebuild caveat above. The qualitative finding (100% PYTH, 100%
  one `error_reason`) does not depend on this and is not in doubt.
- Whether the 1026 stuck shards will ever be explicitly re-attempted (converting them from `attempted_failed` to
  `captured`) was not investigated -- no backfill re-run was triggered or recommended as part of this read-only
  investigation. A future oracle_prices backfill covering the affected days would pick them up naturally now that the
  resolver crash is fixed; no urgency, since the data is not honest-coverage-blocking (already correctly marked as a
  failed attempt, not a fabricated empty).

## Related

- `plans/active/issues/uac_is_defi_oracle_dex_adapter_drift_2026_07_20.md` -- the task's leading hypothesis; disproven
  above (DEX-pool venues, not `oracle_prices`; zero CHAINLINK in the sampled failures either).
- `plans/active/lst_rate_honest_coverage_2026_07_21.md` -- Progress Log 2026-07-22 "Phase 5 #4" entry is the original
  root-cause + fix session for this exact bug class (found via the Solana LST-rates leg, fixed as a good-citizen bundle
  across all 3 `AsyncResolver` call sites including this one).

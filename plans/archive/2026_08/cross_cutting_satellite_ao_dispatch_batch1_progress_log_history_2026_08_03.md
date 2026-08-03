---
doc_type: plan
title:
  Cross-cutting satellite AO batch 1 — Progress Log history (the 2026-07-26 datapoint-validation close-out through the
  2026-07-28 InstrumentRecord `extra='forbid'` measurement)
summary: >-
  Line-cap remediation extraction from plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md's Progress
  Log — the 2026-07-26 datapoint-validation 3-item close-out, the 2026-07-28 distinct-values owning-plan reconciliation
  (81-value classification table), and the 2026-07-28 InstrumentRecord `extra='forbid'` authoritative measurement, moved
  verbatim so the live plan stays under the 1000-line hard cap. The live plan keeps its most recent Progress Log entry
  (the 2026-07-31 cefi Era-B split-off closure) inline; everything below predates it.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-service,
  ]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-1, history, line-cap-remediation]
related: [/plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: script
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "line-cap remediation split, 2026-08-03, per
    plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md"
---

# Cross-cutting satellite AO batch 1 — Progress Log history

Extracted verbatim from `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s `## Progress Log`
section on 2026-08-03, to bring the live plan back under the workspace's 1000-line hard cap
(`scripts/plan-hygiene/check_line_caps.sh`). No content changed — only relocated.

## Progress Log (historical entries)

- **2026-07-26 (slot-7) — DONE, all 3 items closed.** Worked the
  `datapoint_validation_results_bucket_missing_2026_07_21.md` 3-item close-out todo (source issue doc flipped to
  `status: resolved`, `resolved_by: deployment-service@b0e158d`, all 7 of its own todos now `[x]`).
  - **(a) DONE — sibling gap REFUTED.** `alerting-service`'s bucket kind (`configs/cloud-providers.yaml` line 194,
    `alerting-service-${GCP_PROJECT_ID}`) resolves to `gs://alerting-service-central-element-323112`, which
    `gcloud storage buckets describe` confirms EXISTS (location ASIA-NORTHEAST1) and is actively written to (`_index/`,
    `alerting/` prefixes present). No provisioning gap — no follow-up issue doc needed.
  - **(b) DONE + shipped.** Added a guard at the top of `setup-data-pipeline-vm.sh`'s generic `elif [ -n "$VM_TASK" ]`
    fallback: if `VM_BACKFILL_CMD` instance metadata is present (which, by construction, only happens when a launcher
    expected a dedicated dispatch branch that doesn't exist), it now fails LOUD + immediately with a diagnostic naming
    the missing branch and the exact fix, instead of silently building an unrelated `--operation` CLI call that crashes
    minutes later deep in a different service's argparse (the same bug class hit 3 times: 2026-07-12
    sports-v9-migration, 2026-07-13 defi-paper, 2026-07-21 datapoint-validation). `deployment-service@b0e158d`
    (`bash -n` + `shellcheck -S error` clean, full `quality-gates.sh` green, sentinel `d6576d4`). Shipped via
    quickmerge.
  - **(c) DONE.** Confirmed the Round-1 blocker cleared: both named UAC commits are ancestors of the current
    `unified-api-contracts` HEAD — `9a92cf4f` (R3 cefi-v6 chain-tail canonicalisation) and `6329fc04` (oracle
    `processed_candles/` extension) — and UAC/instruments-service/UTL are all clean (no dirty WIP). Republished the
    instruments-service tarball on the clean tree (`instruments-service-code@4d6c2109be9a`, uploaded 2026-07-26T20:58
    UTC — this needed (b) shipped FIRST since `create-code-tarballs.sh` also bundles deployment-service itself and
    hard-blocks on ANY dirty repo in its set, not just the `--include` target). Checked the prior 2026-07-22 relaunch's
    `run.log`s (cefi/defi/prediction) before relaunching: all three end mid-stream with no termination marker (classic
    SPOT-preemption signature, not genuine completion) — cefi reached day 2021-02-05 (178k rows validated) after a ~16h
    run, defi reached day 2021-06-26 (60.5k rows), prediction reached day 2025-01-04 (644k rows) — real forward
    progress, just interrupted, and safe to resume via the launcher's presence-skip idempotency. **Relaunched all 3 at
    2026-07-26 21:00-21:01 UTC**: `datapoint-validation-cefi-20260726-210047`,
    `datapoint-validation-defi-20260726-210104`, `datapoint-validation-prediction-20260726-210124` (all confirmed
    RUNNING, SPOT, e2-standard-4, zone asia-northeast1-c). **T+10min watchdog verified (2026-07-26 21:10-21:11 UTC)**:
    all 3 still RUNNING with active day-frontier advancement in `run.log` — cefi → 2020-01-02 (2000 validated), defi →
    2020-10-07 (5889 validated), prediction → 2021-10-02 (5313 validated). No fire-and-forget; genuine forward progress
    confirmed, matching the same bar todo 2 in the source issue doc was accepted against (tradfi/sports). SPOT
    preemption is expected/acceptable (idempotent, safe to just relaunch the same asset_group again, which will resume
    via presence-skip). Once confirmed, flip this todo's checkbox with the day-frontier evidence.

- **2026-07-28 (slot-6) — distinct-values owning-plan reconciliation DONE.** Worked the line-191 todo above. Method:
  called `deployment_api.routes.data_status._distinct_values.get_distinct_values(asset_group)` in-process
  (deployment-api `.venv`, `GCP_PROJECT_ID=central-element-323112`) for all 5 asset_groups against today's live nightly
  honest-coverage rollup (`source_date=2026-07-28`) — the exact shipped endpoint, no reimplementation. **Per-cluster
  classification** (◆ = already attributed to a live owning plan/issue/ruling, ✚ = new, filed this session):

  | AG         | Axis             | Value(s)                                                                           | Disposition                                                                                                                                     |
  | ---------- | ---------------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
  | defi       | venues           | BLAZESTAKE, HYPERLIQUID                                                            | ◆ `/plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md` (phase=="pipeline" grain, RESOLVED+archived 2026-08-01) |
  | defi       | venues           | ARBITRUM/AURORA/AVALANCHE/BASE/BSC/ETHEREUM/LINEA/OPTIMISM/POLYGON (9)             | ✚ `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`                                                                                      |
  | defi       | venues           | BITFINEX/BITGET/BYBIT/KRAKEN/OKX (5)                                               | ✚ `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`                                                                                      |
  | defi       | data_types       | dex_pools, dex_swaps, rate_indices                                                 | ◆ `master_data_canonicalisation_migration_catalogue_2026_06_07.md`                                                                              |
  | defi       | data_types       | perp_daily_ctx, perp_mark_price                                                    | ◆ `defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`                                                                                  |
  | defi       | data_types       | dex_pool_fees                                                                      | ◆ `defi_dedicated_bucket_shared_migration_2026_07_13.md`                                                                                        |
  | defi       | chains           | HYPERLIQUID                                                                        | ◆ (cross-refs the venues row above)                                                                                                             |
  | defi       | chains           | FUTURES                                                                            | ✚ `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`                                                                                      |
  | cefi       | instrument_types | spot                                                                               | ◆ `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (uppercase migration)                                                        |
  | cefi       | chains           | FUTURES                                                                            | ✚ `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`                                                                                      |
  | tradfi     | venues           | BARCHART                                                                           | ◆ operator ruling 2026-07-20 (quarantine-with-tracking)                                                                                         |
  | tradfi     | venues           | YAHOO_FINANCE                                                                      | ✚ `tradfi_distinct_values_net_new_clusters_2026_07_28.md`                                                                                       |
  | tradfi     | instrument_types | FUTURES                                                                            | ◆ `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (case drift)                                                                 |
  | tradfi     | instrument_types | UNKNOWN                                                                            | ◆ operator ruling 2026-07-18 (classify-or-quarantine)                                                                                           |
  | tradfi     | instrument_types | continuous_future                                                                  | ◆ `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`                                                                    |
  | tradfi     | instrument_types | UD                                                                                 | ✚ `tradfi_distinct_values_net_new_clusters_2026_07_28.md`                                                                                       |
  | tradfi     | chains           | ESM0, ESM0_MIGRATED_20260418T131054Z                                               | ✚ `tradfi_distinct_values_net_new_clusters_2026_07_28.md`                                                                                       |
  | prediction | instrument_types | prediction                                                                         | ◆ `prediction_phase_ab_residuals_2026_07_24.md` (line 278/338, actively-growing blank/malformed instrument_type todo)                           |
  | prediction | data_types       | prediction_trades                                                                  | ◆ `prediction_phase_ab_residuals_2026_07_24.md` (line 539, POLYMARKET schema-extension migration)                                               |
  | sports     | venues           | BET888SPORT, LADBROKES, LADBROKES_UK, SPORT888                                     | ◆ `sports_consolidated_native_ao_extract_2026_07_25.md` (in-flight rename, line 739 follow-up still open)                                       |
  | sports     | venues           | SMARKETS                                                                           | ◆ `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`                                                                                      |
  | sports     | venues           | KALSHI                                                                             | ◆ `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` (resolved, residual)                                             |
  | sports     | venues           | FOOTYSTATS                                                                         | ◆ `sports_consolidated_closeout_2026_07_19.md` (line 514/549, legacy bundle mislabel, open todo)                                                |
  | sports     | instrument_types | odds                                                                               | ◆ operator ruling 2026-07-17 (not-a-defect)                                                                                                     |
  | sports     | instrument_types | exchange_odds, fixed_odds                                                          | ◆ `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`                                                                                      |
  | sports     | instrument_types | ODDS                                                                               | ◆ `sports_consolidated_closeout_2026_07_19.md` (line 406, K1/K2 uppercase-revert P0)                                                            |
  | sports     | instrument_types | ASIAN_HANDICAP_\* (18), MATCH_ODDS, MATCH_ODDS_LAY, OVER_UNDER_\* (10), SPORT (30) | ✚ `sports_instrument_type_market_token_ssot_gap_2026_07_28.md`                                                                                  |
  | sports     | data_types       | ODDS, ODDS_MOVEMENT, ODDS_SNAPSHOT, TRADES                                         | ◆ `sports_consolidated_closeout_2026_07_19.md` (line 406, same K1/K2 revert P0)                                                                 |

  **Total: 81 non-canonical values, 51 already attributed to a live owning plan/issue/ruling, 30 newly attributed via 3
  fresh issue docs filed this session.** The sports spike (12 → 45 since 2026-07-25) is almost entirely the
  `sports_instrument_type_market_token_ssot_gap_2026_07_28.md` cluster — real, deliberately-produced MDPS output (the
  market-generalization branch) that was never registered against a canonical set, not a regression. The
  `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` doc is flagged **P1 / big finding** (cross-AG, not yet
  root-caused) per this workspace's findings-triage rule. Line-191 checkbox flipped on
  `distinct_values_noncanonical_audit_2026_07_20.md` with this same evidence (cross-linked, not duplicated).
  **2026-07-28 addendum**: the table's two `sports` rows citing `sports_consolidated_closeout_2026_07_19.md` line 406
  (`ODDS` instrument_type; `ODDS, ODDS_MOVEMENT, ODDS_SNAPSHOT, TRADES` data_types) had their owning todo flipped done
  the same day — the K1/K2 `ODDS`/`TRADES` uppercase population is migrated + deleted + independently verified absent
  from GCS. Left as historical record (not rewritten) rather than edited in place. **Follow-up RESOLVED same day**: a
  direct manifest query for `data_type` in `{ODDS_MOVEMENT, ODDS_SNAPSHOT}` found exactly 4 rows total (2 + 2), ALL
  `capture_status=empty_confirmed` with `row_count=0/NaN` and blank `venue`/`league_id`/`instrument_type`, all dated a
  single 2026-04-14 — inert honest-absence bookkeeping markers, **zero real GCS objects behind them, nothing to migrate
  or delete**. Not a K1/K2-style live duplication (13,811/13,835 real `odds_movement`/`odds_snapshot` rows are correctly
  lowercase already) — a trivial, zero-impact residual, not urgent. No action taken; noted here so the next reader
  doesn't re-open this as a live risk.

- **2026-07-28 (slot-6) — DONE — InstrumentRecord `extra='forbid'` authoritative measurement + REMOVE dispositions
  applied.** `instruments-service@ee2d6c75`.
  - **Method**: flipped `model_config = ConfigDict(extra="forbid")` on `InstrumentRecord` on a local scratch branch
    (never pushed), ran the FULL UAC + instruments-service `quality-gates.sh` suites (not `-k`), then AST-parsed
    (`ast.walk`, not string-grep) every `InstrumentRecord(...)` call site across both repos for the offending kwarg
    names — authoritative, not traceback-string-matched (an earlier traceback-text parse mis-attributed several fields
    to the wrong call site by merging adjacent pytest failure blocks; the AST scan is exact).
  - **Authoritative complete field list (supersedes the 2026-07-18 partial measurement)**: `symbol`, `is_active`,
    `updated_at`, `min_order_size` (the four already pre-analyzed) **plus two newly-surfaced fields the partial
    measurement missed**: `asset_group`, `lot_size`. The static-scan defi/deribit candidates
    (`spot_asset`/`debt_symbol`/`onchain_symbol`/`contract_address`/`decimals`/`borrow_symbol`/`capability`) **never
    appeared** as `extra_forbidden` in either full-suite run — confirmed false positives from the greedy static grep
    (they're already-declared fields, e.g. `base_asset_contract_address`/`base_asset_decimals`; no action needed).
  - **Per-field verdicts + real call sites** (9 production + 6 test-fixture-only sites, 16 total):
    - `symbol` → **REMOVE** (zero usage, `raw_symbol`/`base_asset` already cover it). Sites:
      `betfair.py::_build_runner_record`, `ibkr.py::_build_instrument_from_uac`, + 3 test fixtures.
    - `is_active` → **REMOVE** (zero usage — verified the _dynamic_ kalshi/polymarket values aren't silently lost: both
      adapters ALSO emit a separate `MarketLifecycle` row with a richer `current_status` created/active/resolved/settled
      that IS the real lifecycle signal; `InstrumentRecord.status` was never the source of truth for prediction
      markets). Sites: `betfair.py` (hardcoded `True`), `kalshi.py::_parse_market`,
      `polymarket/parsing.py::_parse_market` (both dynamic), + 2 test fixtures.
    - `updated_at` → **REMOVE** (zero usage, no consumer). Same 3 production sites + 2 test fixtures.
    - `min_order_size` → **LEFT UNTOUCHED** per the existing operator-judgment flag (semantically distinct from
      `min_size`) — confirmed present at all 3 production sites (`betfair.py`/`kalshi.py`/`polymarket/parsing.py`)
      - 2 test fixtures, none touched.
    - `asset_group` → **RENAMED to `asset_class` (bug-fix, not a drop)** — deviates from the literal REMOVE instruction
      because dropping it would have been WORSE than fixing it: `asset_class: AssetClass` is an already-declared,
      `INSTRUMENTS_PARQUET_SCHEMA`-persisted field (confirmed via `fx.py:70` already using the correct `asset_class=`
      kwarg), and `databento/adapter.py` (4 sites: `_create_fx_spot_records`, `_create_krx_equity_records`,
      `_create_yahoo_index_records`, `_parse_row_to_record`) + `ibkr.py` (2 sites: `_build_instrument_from_uac`,
      `_build_stub_instrument`) were all passing the FX/EQUITY/INDEX classification under the misnamed `asset_group=`
      kwarg — silently dropped, so every TradFi/Databento/IBKR instrument's `asset_class` column was landing at its
      default `AssetClass.CRYPTO` regardless of real asset class. Renamed the kwarg (+ the `_SEC_TYPE_asset_group_MAP`
      constant → `_SEC_TYPE_ASSET_CLASS_MAP` for consistency) at all 6 sites — a real correctness fix, not cosmetic.
      Also opportunistically set `raw_symbol=symbol` in `ibkr.py::_build_instrument_from_uac` (same file/lines already
      touched) — that call built NO `raw_symbol` at all before (only the now-dropped dead `symbol=`), so IBKR
      instruments' `raw_symbol` column was landing empty.
    - `lot_size` → **REMOVE** (zero production usage — confirmed via AST scan across the WHOLE instruments-service tree,
      not just the failing tests — every occurrence is test-fixture-only cruft in `_make_instrument()` helpers across
      `test_coverage_gaps_adapters.py`, `test_defi_adapters_comprehensive.py`, `test_base_adapter.py`,
      `test_library_deps_integration.py`; not in `INSTRUMENTS_PARQUET_SCHEMA` either).
  - **Verification**: instruments-service full `quality-gates.sh --no-fix` → **ALL QUALITY GATES PASSED** (4988 passed /
    0 failed, up from 105 failed under the measurement flag; sentinel `691365ffc3a76926aa39762704adc0f88cea4a20`,
    shipped `instruments-service@ee2d6c75`). UAC's FIRST full-suite measurement run (extra='forbid' active, the stricter
    of the two states) already exhaustively passed 12174/12175 tests with exactly ONE failure — a dead `symbol=` kwarg
    in `tests/internal/unit/test_uic_ac_alignment.py` (test-only, zero production impact) — confirming zero UAC
    _production_ code needed any change for this todo.
  - **Deferred (P3, cosmetic, zero functional impact)**: that one UAC test-fixture `symbol=` kwarg was left un-shipped.
  8 consecutive attempts to get a fresh UAC `quality-gates.sh` confirmation for the trivial 1-line fix were silently
  killed mid-`TESTS`-phase by sustained host-wide memory/swap contention (independently verified across all 8 attempts
  via `free -h`/`ps aux`: swap oscillating 2-15Gi used, 6-19 concurrent `quality-gates.sh` processes fleet-wide the
  whole time — not a code issue, `journalctl`/`dmesg` inaccessible in-sandbox so the exact OOM-vs-cgroup-limit mechanism
  couldn't be confirmed, but the pattern was 100% consistent regardless of launch method: nohup, `setsid`+full detach,
  niced, or foreground-with-timeout). Reverted the UAC edit rather than ship unverified or block the (verified-green,
  higher-value) instruments-service fix on it — `extra='ignore'` already silently absorbs the dead kwarg today (same
  behavior before and after this todo), so leaving it is zero-risk. Re-attempt the one-line fix (remove
  `symbol="BTC/USDT"` from `test_instrument_record_is_importable`, line ~255) next time host load is normal; do not
  re-litigate the verdict.
  </content>

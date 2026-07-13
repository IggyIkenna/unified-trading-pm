---
doc_type: plan
title: DVOL-Backtestable VOL Engines — VOL_CARRY + VOL_ARB_RV_IV register-or-honest-absent
summary:
  Build the missing DVOL-index historical capture path (free Deribit public REST, no credentials) and use it to actually
  backtest VOL_CARRY + VOL_ARB_RV_IV — the only 2 of 17 VOL_* engines that don't need Tardis — then register only if the
  backtest genuinely passes.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, backtest]
repos: [unified-api-contracts, market-tick-data-service, strategy-service]
scope: [engineer]
tags: [strategy, v2-engine, vol-trading, backtest, deribit]
related: [v2_engine_venue_buildout_2026_06_15.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
assigned_role: backend-engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up, operator decision 2026-07-13]
sequential: true
---

# DVOL-Backtestable VOL Engines

> **Split out 2026-07-13** from [`v2_engine_venue_buildout_2026_06_15.md`](v2_engine_venue_buildout_2026_06_15.md) Phase
> E2. Of the 17 VOL_* engines, 15 are `BLOCKED-CREDENTIALS` on Tardis (stays in the parent plan, do not touch here).
> VOL_CARRY (`engine/strategies/v2/vol_trading/carry.py`) and VOL_ARB_RV_IV (`vol_trading/arb_rv_iv.py`) are the
> exception — both trade `iv_atm - rv`, which needs only the DVOL implied-vol index + the underlying's realised-vol
> close series, NOT a per-strike surface. Deribit's public `/public/get_volatility_index_data` gives BTC DVOL OHLC back
> to **2021-03-24**, no auth, confirmed live in the parent plan's 2026-06-15 probe.

## HARD CONTRACT — copied verbatim from the parent plan, applies to every todo here

**An archetype is DONE only when the engine is REAL**: genuine strategy logic, a **passing backtest artifact** via
`GroupBRunner` (`strategy-service/.../engine/strategies/v2/batch_harness.py`), unit tests, registered in
`ARCHETYPE_ENGINE_REGISTRY`, and the verdict matrix regenerated to `available`. **NEVER register a hollow/stub engine or
one whose backtest didn't actually pass** — a registered engine with no real edge makes the matrix LIE, which is worse
than honest `not_available`. If the backtest doesn't clear a real bar (not just "it ran without crashing" — a defensible
signal, non-degenerate PnL/Sharpe), leave the engine `not_available` and file a new `BLOCKED-*` todo naming exactly
what's missing.

## Ground truth (2026-07-13 gap check — do not re-derive)

- `unified-api-contracts/unified_api_contracts/registry/endpoints.py:205` already maps
  `("deribit", "volatility_index"): "DeribitVolatilityIndex"` — an endpoint reference exists, but there is **no**
  `data_type_capability.py` capability row for `volatility_index` (checked: zero hits) and **zero** MTDS handler files
  reference `volatility_index`/`dvol` — the ingestion path is genuinely unbuilt, this is real net-new work, not a
  registry-only fix like the sibling `uac_venue_registry_completion_2026_07_13.md` plan.
- `strategy_service/.../vol_trading/carry.py` and `arb_rv_iv.py` already have code comments acknowledging
  DVOL-backtestability but nothing upstream feeds them yet.
- **Canonical form (mandatory)**: register `volatility_index` as a real `data_type` in
  `unified-api-contracts/unified_api_contracts/registry/data_type_capability.py` (do not invent a different name —
  `volatility_index` is the name already used in `endpoints.py`); any captured/written parquet MUST carry the
  `pipeline_mode = {mode}_{source}[_{transport}]` hive-partition key (e.g. `batch_deribit`) LEFT of `asset_group=`, per
  `codex/02-data/pipeline-mode-partition.md`; every bucket lookup goes through
  `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` — **never** an inline `gs://` path or
  a hardcoded bucket string.

## Todos

- [ ] [DATA] P1. Register `volatility_index` data_type capability: `data_type_capability.py` entry for
      `(cefi,     volatility_index)`, venue `DERIBIT`, `live_capable=True, batch_capable=True` (it's a REST history
      endpoint, no streaming needed). `SOURCE_PRIORITY[("cefi","volatility_index")] = ["deribit"]`. Repo:
      unified-api-contracts.
- [ ] [DATA] P1. Build the MTDS handler consuming the existing `DeribitVolatilityIndex` endpoint mapping: capture DVOL
      OHLC (`/public/get_volatility_index_data`, resolutions incl. `86400`/`3600`, paged via `continuation`) into the
      canonical schema, `pipeline_mode=batch_deribit`, `source="deribit"`, bucket via `resolve_bucket_name(...)`,
      `classify_venue_error()` + shard isolation per the established Deribit-adapter pattern in this codebase.
      **Connectivity-test with a SMALL bounded pull only (e.g. trailing 30-90 days) to prove the pipeline** — do **NOT**
      run the full 2021→now historical pull as part of this todo. Repo: market-tick-data-service.
- [ ] [OPERATOR] P1. **BLOCKED-OPERATOR-DECISION**: get an explicit operator go + desired historical depth (full
      2021-03-24→now vs. a shorter window) before pulling the DVOL history the actual backtest will run against. DVOL is
      free/credential-free, but per the parent plan's 2026-06-15 constraint ("backfills wait for explicit go... where
      applicable, the paid vendor") a bulk historical pull is still a backfill decision, not something to run unattended
      even on a free source. **Not dispatchable — stays visible, never auto-ingested.**
- [ ] [SCRIPT] P1. Once the historical DVOL series is available (post-operator-go), wire it + the underlying's
      realised-vol close series as `GroupBRunner` backtest input for **VOL_CARRY** and run the backtest.
- [ ] [SCRIPT] P1. If VOL_CARRY's backtest passes the HARD CONTRACT bar above, register it in
      `ARCHETYPE_ENGINE_REGISTRY`. If it does not pass, leave `not_available` and file a new `BLOCKED-*` todo naming the
      specific failure (e.g. degenerate PnL, insufficient sample). Repo: strategy-service.
- [ ] [SCRIPT] P1. Same backtest-then-conditionally-register sequence for **VOL_ARB_RV_IV**
      (`vol_trading/arb_rv_iv.py`). Repo: strategy-service.
- [ ] [SCRIPT] P2. Regenerate + commit `capability-verdict-matrix.json`; cite the regenerated-matrix commit as evidence
      for whichever of the 2 engines actually flipped to `available` (may be 0, 1, or 2 — do not force both). Repo:
      unified-api-contracts.

## Progress Log

(loop handoff lands here)

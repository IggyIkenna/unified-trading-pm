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
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 5.0
assigned_role: backend_engineer
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
> E2. Of the 17 VOL\_\* engines, 15 are `BLOCKED-CREDENTIALS` on Tardis (stays in the parent plan, do not touch here).
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

- [x] ✅ [DATA] P1. Register `volatility_index` data_type capability: `data_type_capability.py` entry for
      `(cefi,     volatility_index)`, venue `DERIBIT`, `live_capable=True, batch_capable=True` (it's a REST history
      endpoint, no streaming needed). `SOURCE_PRIORITY[("cefi","volatility_index")] = ["deribit"]`. Repo:
      unified-api-contracts. — **DONE, slot 9, unified-api-contracts@`a02ce954`.** Added the `DataTypeCapability` entry
      (no `streaming_protocol`, mirroring the `prediction_canonical_question_group` REST-derived pattern — it's a
      REST-polled index, not a WS stream) + `SOURCE_PRIORITY[("cefi","volatility_index")] = ["deribit"]` exactly as
      specified. Discovered the literal one-line `SOURCE_PRIORITY` entry needed a broader closed-set cascade to actually
      round-trip (verified via the repo's own test suite, not assumed): added `PipelineMode.BATCH_DERIBIT`, widened
      `SOURCE_MODE_CAPABILITY["deribit"]` + `BATCH_CAPABLE_CEFI_VENUES` to carry the same "self-archiving vendor"
      exception already used for aster/extended/pacifica (deribit stays live/replay-only for every OTHER cefi data_type
      — tardis remains those data_types' batch archive — but is now ALSO the genuine batch source for `volatility_index`
      specifically), added an `EMISSION_LATENCY_MS_BY_SOURCE` entry (1h, matching the REST-history-endpoint cadence
      class) and an `AVAILABILITY_AT_SEMANTICS` entry (`tick_timestamp`), and updated 2 tests that hard-coded deribit's
      prior live/replay-only mode set. Verified via 718 targeted tests green (`test_source_mode_capability.py` /
      `test_source_priority.py` / `test_source_priority_pipeline_mode.py` / `test_pipeline_mode.py` /
      `test_availability_semantics.py` / `test_validity_matrix_completeness.py` + broader keyword sweep) + full
      `quality-gates.sh` green (`ALL QUALITY GATES PASSED`, sentinel matches HEAD). Hit + resolved an unrelated
      repo-wide QG-red blocker along the way (databento_classifier.py file-size + cryptography GHSA-537c-gmf6-5ccf,
      pre-existing, verified via clean `git diff --stat HEAD` on both — filed
      [`plans/active/issues/uac_qg_red_databento_classifier_filesize_and_cryptography_ghsa_2026_07_13.md`](issues/uac_qg_red_databento_classifier_filesize_and_cryptography_ghsa_2026_07_13.md),
      declared repo-blocker RB-e4b7bd5c, resolved once another slot shipped the cryptography bump). No MTDS handler
      built here — that is the next todo below, separate scope.
- [x] ✅ [DATA] P1. Build the MTDS handler consuming the existing `DeribitVolatilityIndex` endpoint mapping: capture
      DVOL OHLC (`/public/get_volatility_index_data`, resolutions incl. `86400`/`3600`, paged via `continuation`) into
      the canonical schema, `pipeline_mode=batch_deribit`, `source="deribit"`, bucket via `resolve_bucket_name(...)`,
      `classify_venue_error()` + shard isolation per the established Deribit-adapter pattern in this codebase.
      **Connectivity-test with a SMALL bounded pull only (e.g. trailing 30-90 days) to prove the pipeline** — do **NOT**
      run the full 2021→now historical pull as part of this todo. Repo: market-tick-data-service. — **DONE, slot 4,
      market-tick-data-service@`77ff475a`** (initial handler shipped at `3511ab3b`, then a real-connectivity-test bug
      found+fixed at `77ff475a`). Built `DeribitVolatilityIndexHandler` (new `collect-deribit-volatility-index`
      operation, registered in `cli/main.py`), per-day `BatchPayload` dispatch, `fetch_dvol_day()` doing
      `continuation`-cursor pagination against `/public/get_volatility_index_data` for BTC/ETH, honest-absence for
      pre-2021-03-24 (DVOL launch) days, per-currency shard isolation + `classify_venue_error`. 14 unit tests
      (pagination, CF-11 failure signalling, capture/empty/failed routing). **Runtime-verified against real production
      Deribit REST + GCS (not just unit tests)**: a real connectivity-test run caught a genuine bug unit-mocks couldn't
      — the `row_key` dict used `"day"`/`"asset_group"`, but `ManifestWriter`'s real schema uses `"date"` and has no
      `"asset_group"` column, so every manifest write raised an uncaught `KeyError` that also aborted the OTHER
      currency's turn in the shard loop (a real shard-isolation gap). Fixed both (corrected row_key shape + wrapped the
      manifest-write call in its own try/except) and re-verified: a 1-day pull (`2026-07-13`, `--venues DERIBIT`) now
      shows real captured manifest rows for BOTH currencies —
      `venue=DERIBIT data_type=volatility_index underlying=BTC/ETH day=2026-07-13 capture_status=captured     instrument_count=23 pipeline_mode=batch_deribit source=deribit`
      — with real parquet at
      `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-13/pipeline_mode=batch_deribit/asset_group=cefi/venue=DERIBIT/instrument_type=index/data_type=volatility_index/underlying={BTC,ETH}/dvol.parquet`.
      **Note for the operator-go todo below**: the shared `availability_index.parquet` (~7.5M rows) is under heavy write
      contention from the rest of the fleet right now — a genuine manifest flush took ~9 retry attempts / ~9 min
      wall-clock to land under this session's load. Not a defect in this handler, but worth knowing before scheduling
      the full 2021→now historical pull (many more shards writing to the same contended index).
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

- 2026-07-13 (slot-13): Dispatched the `[SCRIPT] P1. Once the historical DVOL series is available (post-operator-go)...`
  todo, but its predecessor `[OPERATOR] P1. BLOCKED-OPERATOR-DECISION` todo is still unchecked and explicitly "Not
  dispatchable — stays visible, never auto-ingested." No historical DVOL series has been pulled yet, and I can't grant
  the operator-go myself. Skipping for this slot rather than working around the missing decision. Note for whoever
  authors the next backlog-affecting plan edit: this todo has no `depends_on`/`conditions` gate tying it to the OPERATOR
  todo above it, so `sequential: true` alone didn't stop it from being dispatched independently — worth adding a
  `prereqs.conditions` gate (e.g. `dvol-historical-pull-approved`, flipped true once the operator go lands) if this
  recurs.
- 2026-07-14 (slot-14): Same task dispatched again, same wall — the OPERATOR P1 BLOCKED-OPERATOR-DECISION todo is still
  unchecked a day later. Rather than silently re-skip, filed `/blocked` question `BLK-011c84cb` putting the actual
  decision (full 2021-03-24→now vs. a shorter window) in front of the operator/main via the dashboard, then
  `/skip-current-task`. Confirmed via the live backlog API (`GET /api/backlog`, task
  `vol_dvol_backtestable_engines-003`) that the entry still carries no `prereqs`/`conditions` field — slot-13's
  suggested fix was never applied. This is now a 2-slot repeat; whoever resolves `BLK-011c84cb` should also add the
  `prereqs.conditions` gate at the same time so a 3rd slot doesn't burn a dispatch on this.
- 2026-07-17 (slot-7): **3rd repeat-dispatch** — `vol_dvol_backtestable_engines-001` dispatched to slot-7, still no
  operator-go (OPERATOR P1 todo remains `[ ]`; last plan edit is slot-14's note above, no DVOL history pulled), and
  `GET /api/backlog` still shows `-001..-004` with `prereqs: null` — the gate slots 13 & 14 both asked for was never
  added. `BLK-011c84cb` remains the standing operator decision, so I did not file a duplicate. Instead, escalated the
  **gate-add** to main as a separate, immediately-actionable fix (independent of the operator's timing) so a 4th slot
  doesn't burn on this. **Gate-add recipe for main** (per `agents/RULES.md` §4.3, yaml-only — regen does NOT derive
  per-task prereqs from plan todos, and `sequential: true` alone provably does not gate independent dispatch): (1)
  `POST /api/prerequisites/dvol-historical-pull-approved {value:false, set_by:"main"}`; (2) add
  `prereqs.prerequisites: [dvol-historical-pull-approved]` to `-001`, `-002`, `-003`, `-004` in
  `data/config/backlog.yaml`, then `POST /api/backlog/reload`; (3) re-verify it survives a `PlanRegenLoop` tick (the
  `backlog_regen_drops_handtuned_prereqs` bug class); (4) when the operator answers `BLK-011c84cb`, flip the condition
  true. Then `/skip-current-task` (blocked-operator + ungated — not doable from a worker slot; worker cannot hand-edit
  `backlog.yaml` per the HARD RULE, so the gate is main's to add).

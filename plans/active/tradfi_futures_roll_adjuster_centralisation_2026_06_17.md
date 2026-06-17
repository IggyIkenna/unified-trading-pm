---
title:
  TradFi futures roll-adjuster centralisation — MDPS continuous-contract stage, features reads persisted (+ Massive
  flat-files dispatch/backfill)
parent_epic: tradfi_master
assigned_vm: vm-tradfi
priority: P1
status: active
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4
created: 2026-06-17
locked_by: live-defi-rollout
locked_since: 2026-06-17
related_plans:
  - plans/active/tradfi_massive_dual_source_2026_05_28.md
  - plans/active/issues/massive_cme_futures_flatfiles_not_rest_2026_06_17.md
  - plans/active/sp500_ml_readiness_master_2026_05_05.md
---

# TradFi futures roll-adjuster centralisation

## Decision (operator 2026-06-17 — FULL centralisation)

Futures **back-adjusted continuous-contract construction** (the "roll adjuster") is a **data-PROCESSING-layer** concern.
It produces ONE persisted artifact set — the continuous candle series + the `active_contracts.parquet` roll-schedule
SSOT — consumed by **features (TA), ML (signal), strategy (roll translation), execution (roll cost)**. It MUST run
**before** features compute technical analysis, so every consumer sees the SAME adjusted series.

### Current state (the gap this plan closes)

- `market-tick-data-service/scripts/build_continuous_es.py` — the real Panama back-adjust producer (writes
  `processed_candles/by_date/…/instrument_type=continuous_future/venue=CME/underlying={ROOT}/` + the sidecar SSOT
  `processed_candles/_continuous/{ROOT}/_meta/active_contracts.parquet`). **But it is an mtds SCRIPT**, not a wired MDPS
  pipeline stage (script-homes violation: production runtime logic writing MDPS's `processed_candles/`).
- `features-service/.../delta_one/app/core/futures_roll_adjuster.py` + the delta_one orchestrator's `_maybe_roll_adjust`
  — **re-derive** the continuous series **in-memory** for `futures_basis`/`technical_indicators`/ `momentum`.
  **Duplicate roll logic** → features TA can compute on a DIFFERENT adjusted series than ML/strategy/exec.
- Consumers already read the persisted SSOT by **path** (no code coupling to the script): `strategy-service`
  `engine/futures/roll_emitter.py` (reads `active_contracts.parquet`; imports only stdlib+UAC — NO mtds import) and
  `ml-service` training (placeholder comment only). So **relocating the producer to MDPS (same output path) is
  transparent to consumers.** Canonical layering: `sp500_ml_readiness_master_2026_05_05.md` Q4 §8 (Layer A signal / B
  translation / C execution / D positions).

## Output contract (UNCHANGED — the path IS the contract)

- Continuous candles:
  `processed_candles/by_date/day={D}/timeframe={tf}/data_type={dt}/instrument_type=continuous_future/venue=CME/underlying={ROOT}/ticks.parquet`
- Roll-schedule SSOT: `processed_candles/_continuous/{ROOT}/_meta/active_contracts.parquet` (cols:
  `date, active_contract_id, prev_contract_id, roll_spread, roll_date_for_this_active_contract`).
- Algorithm: Panama-canal back-adjust; roll N business days before expiry (default 8); continuous series for SIGNAL
  only, never fill prices (fills use the active-contract SSOT → real contract).

## Phased DAG

- **P1 (mtds, INDEPENDENT) — Massive flat-files into the live tradfi dispatch + backfill.** Wire
  `MassiveTradfiRestConnector` (futures via S3 flat-files, mtds@a311561) into the tradfi data flow
  (`adapters/umi_tick_provider.py` `_route_*` pattern — add a Massive route) so Massive per-contract futures OHLCV lands
  on the canonical `venue=CME` per-contract candle path that the continuous stage consumes; + a production
  `us_futures_cme` bulk-backfill ingester CLI (resolve_bucket_name / UCI `get_storage_client` /
  `record_captured(source="massive")`, NOT boto3-in-a-script / hardcoded buckets — the smoke script is `/tmp`-only).
  Closes R5-fix-6 (wire, not retire).
- **P2 (mdps, INDEPENDENT) — promote build_continuous_es → an MDPS continuous-contract CLI stage.** New `--operation`
  (e.g. `build-continuous`) on `market-data-processing-service`: reads per-contract `processed_candles/…/venue=CME/`,
  applies the Panama core (port the pure functions: `build_roll_dates`/`build_active_contracts_table`/
  `compute_back_adjust_shifts`/`apply_panama_canal_backadjust`/`extract_roll_events`/`attach_roll_metadata`), writes the
  continuous candles + `active_contracts.parquet` SSOT at the contract paths above, via UCI / `resolve_bucket_name` (NOT
  the script's hand-rolled `_bucket_name_for` / local `pq.read_table`). batch=live; manifest emission + honest-absence
  for non-session days; per-shard isolation. Unit-test the algorithm (already covered by
  `tests/unit/scripts/test_build_continuous_es.py` — port the assertions).
- **P3 (features, parallel at code-level; e2e gated on P2 output) — features reads the persisted continuous series.**
  `delta_one` `_maybe_roll_adjust` reads the persisted `instrument_type=continuous_future` candles (+ honest preflight:
  the continuous series must exist for the date — the pipeline-ordering dependency, like features depend on processed
  candles), and the in-memory `FuturesRollAdjuster.adjust_continuous` duplication is RETIRED (keep
  `annotate_lifecycle_phase`/`get_lifecycle_phase` — those are lifecycle helpers, not roll-adjust). Unit-test the
  read-path (mock the continuous parquet).
- **P4 (mtds cleanup, AFTER P2) — retire `build_continuous_es.py`.** Once MDPS produces the identical output, delete the
  mtds script (delete-deprecated) + repoint the strategy `roll_emitter` + ml docstrings from
  `market-tick-data-service/scripts/build_continuous_es.py` → the MDPS stage. Keep
  `tests/unit/scripts/test_build_continuous_es.py` assertions migrated to MDPS.

## Phase todos

- [x] [MTDS] P1. Wire Massive futures flat-files into the tradfi dispatch (`umi_tick_provider` Massive route) so
      per-contract CME futures OHLCV reaches `processed_candles/…/venue=CME/`; unit-test the routing. Repo:
      market-tick-data-service. (R5-fix-6 → WIRE.) — market-tick-data-service@0962bad | QG ✅ 27 tests pass |
      `_umi_massive._route_massive` + source="massive" intercept in `fetch_tick_data_for_venue`
- [x] [MTDS] P1. `us_futures_cme` bulk-backfill ingester as a production CLI (resolve_bucket_name / UCI /
      `record_captured(source="massive")`; interval-aware right-edge via `compute_bar_close_boundary`). Repo:
      market-tick-data-service. — market-tick-data-service@0962bad | QG ✅ |
      `MassiveFuturesBackfillHandler` (`--operation massive-futures-backfill`), `BATCH_MASSIVE` pipeline_mode
- [ ] [MDPS] P1. Promote `build_continuous_es` → MDPS `--operation build-continuous` continuous-contract stage (Panama
      core + active_contracts SSOT, UCI/resolve_bucket_name, batch=live, manifest+honest-absence). Repo:
      market-data-processing-service.
- [ ] [FEATURES] P1. `delta_one` `_maybe_roll_adjust` reads the persisted continuous series; retire the in-memory
      `FuturesRollAdjuster.adjust_continuous` duplication (keep lifecycle-phase helpers); preflight the
      continuous-series dependency. Repo: features-service.
- [ ] [MTDS] P2. Retire `build_continuous_es.py` once MDPS produces the output; repoint strategy `roll_emitter` + ml
      docstrings to the MDPS stage. Repos: market-tick-data-service (+ strategy-service / ml-service doc repoints).

## Verification (full-execution criterion)

ONE adjusted continuous series + `active_contracts` SSOT produced by the MDPS stage; features/ML/strategy/execution all
consume it (no in-features re-derivation); Massive per-contract futures OHLCV flows in; all touched repos QG-green; the
mtds script retired with consumer refs repointed. Live S3 / continuous-build runs are `@requires_credentials` /
operator-gated batch ops (proven algorithm; 5y ES already pulled).

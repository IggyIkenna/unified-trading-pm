---
doc_type: plan
title: Instrument spec versions (effective-dated contract specs) + IS layer-0 honest coverage with separate IS / MTDS rollups
summary: >-
  Child of trading_pipeline_smoke_and_shard_telemetry_2026_08_22 under instruments_master (operator Q&A 2026-08-22).
  The instruments catalogue (gs://<instruments-bucket>/<env>/catalog.parquet) carries lifecycle bounds only
  (available_from / available_to); no contract-size / tick-size / multiplier history with effective dates exists
  anywhere in the UAC instruments domain, yet execution reads specs from the catalogue today — so a spec change is
  silently applied to all history. Adds InstrumentSpecVersion rows (effective_from / effective_to + spec fields) written
  by IS on change and resolved by execution / backtests by trade time. Also adds the IS-layer honest coverage
  (catalogue rows present per shard-day at the v2 grains — sports (bookmaker-as-venue, instrument_type, data_type,
  league_id), defi (venue, instrument_type, data_type, chain)) as layer 0 in coverage.json and the data-status UI, with
  IS and MTDS coverage shown separately and the rollup handling both.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, unified-trading-library, execution-service, deployment-api, deployment-ui, unified-trading-pm]
scope: [engineer, admin]
tags: [instruments, catalogue, spec-versions, effective-dated, honest-coverage, is-layer, sports, defi, bookmaker, chain]
related:
  [
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/service-shard-status-catalogue.md,
    /plans/epics/instruments_master.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: [trading_pipeline_smoke_and_shard_telemetry_2026_08_22]
locked_by:
locked_since:
supersedes:
superseded_by:
source: [operator Q&A 2026-08-22 (slot 6) — "instrument definitions in full aren't in the catalogue with the delta for changes to things like contract size"; "IS should have the IS honest coverage and MTDS should have its honest coverage so rollup needs to handle both"]
context_scope:
  [
    unified-trading-library/unified_trading_library/instruments_catalog_reader.py,
    instruments-service/scripts/build_instrument_catalogue.py,
    instruments-service/scripts/measure_honest_coverage.py,
    unified-api-contracts/unified_api_contracts/registry/venue_constants.py,
    deployment-api/deployment_api/routes/data_status/_status_core.py,
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/service-shard-status-catalogue.md,
  ]
---

# Instrument spec versions + IS layer-0 honest coverage

> **Human plan**, child of
> [`trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md`](/plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md).
> IS owns reference data (CLAUDE.md); this plan keeps that ownership while giving execution effective-dated specs and
> giving IS its own coverage surface.

## Todos

- [ ] [DESIGN] P1. **`InstrumentSpecVersion` contract in UAC** — `effective_from`, `effective_to`, `contract_size`,
      `multiplier`, `tick_size`, `lot_size`, `min_notional`, `settlement`, `spec_hash`; one row per (instrument_id,
      effective_from); catalogue keeps `available_from/to` as today. Done-when: contract + guard tests shipped.
- [ ] [DATA] P1. **IS writes spec deltas** — `build_instrument_catalogue.py` (or its refresh path) diffs venue specs
      per run and appends a new version row only on change; history backfilled from venue archives where a source
      exists, else first-seen. Done-when: one venue with a known contract-size change shows two rows.
- [ ] [BACKEND] P1. **Execution + backtests resolve specs by trade time** — `instruments_catalog_reader` gains
      `spec_at(instrument_id, ts)`; execution order building and the candle fill engine use it; a QG check forbids
      reading specs without a timestamp. Done-when: a backtest across the change date uses both specs (test cited).
- [ ] [DATA] P1. **IS layer-0 honest coverage** — `measure_honest_coverage.py` emits a `layer="instruments-service"`
      section: catalogue-row presence per shard-day at the v2 grains (sports league_id, defi chain), 4-state
      vocabulary; `/honest-coverage-dump` + `/readiness-state-dump` read it as the IS leg. Done-when: coverage.json
      carries both IS and MTDS layers for every AG.
- [ ] [UI] P1. **Separate IS and MTDS coverage in data-status** — deployment-api `get_coverage_summary` +
      deployment-ui show IS coverage and MTDS coverage side by side; the rollup aggregates both without mixing
      denominators; `pw:L2` spec cited. Done-when: UI renders two layers for sports and defi.
- [ ] [DATA] P2. **Sports non-odds instrument_type** — name the instrument_type vocabulary for non-odds sports data
      (weather, lineups, injuries) in UAC so IS rows and coverage do not collapse them into odds; record the ruling in
      `/codex/01-domain/sports-instruments.md`. Done-when: enum + codex § merged.
- [ ] [DATA] P2. **Retire or rewire the stale `data-catalogue.{service}.yaml` refresher** (5.5 months stale; reads an
      artefact no writer produces) — decide rewire-to-catalogue vs delete; do it. Done-when: no stale shard-status
      catalogue is cited by deployment-api.
- [ ] [DOC] P2. **Archive** per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` once every todo is
      `[x]`.

## Codex SSOTs

- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` — IS→consumer contract; spec versions extend it.
- `/codex/02-data/honest-coverage-model.md` — two-layer model; IS layer 0 lands here.
- `/codex/02-data/service-shard-status-catalogue.md` — the stale yaml catalogue this plan retires or rewires.

## Progress Log

- **2026-08-22 (operator Q&A, slot 6)**: Created from the spec-deltas + IS-coverage rulings.

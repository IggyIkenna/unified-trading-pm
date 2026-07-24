---
doc_type: plan
title: cefi-ml-may-23-2026
summary:
status: complete
nature: record
asset_group: cefi
stage: [meta]
repos: [alerting-service, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
plan_type: epic
owner: ikenna
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
parent: master_to_live_defi_2026_05_23
deadline: 2026-05-23
---

## Deferred work — migrated to: `plans/active/cefi_ml_directional_continuous_live_2026_06_20.md` — successor:

cefi_ml_directional_continuous_live_2026_06_20 (the 10 open success-criteria items — continuous ML prediction live
across OKX/Binance/Bybit, end-to-end live ML pipeline, backtest-fidelity proof, live model hot-reload/version
traceability, live alerting, kill switches/circuit breakers, DART manual override — trace forward through the 2026-05-08
supersession into `cefi_master_2026_05_07.md` (itself now archived) into this active plan, whose title and scope (CeFi
ML directional signal, continuous, live) is a direct continuation of this epic's headline deliverable. Verified via grep
— real living successor, not a guess.

# Epic — CeFi ML (May 23 2026)

> **🔴 SUPERSEDED 2026-05-08** — folded into [`cefi_master_2026_05_07.md`](./cefi_master_2026_05_07.md) § "May-23
> deliverable" per operator direction (consolidate same-domain epics into masters; less indirection). This file is
> archived; content remains verbatim for archaeology. **Edit the master, not this file.**

## Why this epic exists

The **second live archetype** for May 23: a continuous ML prediction signal that's tradable across OKX, Binance, and
Bybit. Distinct from the DeFi rollout (which is rules-based + carry-family) — this epic ships a live ML-driven CeFi
trading loop on real capital. The end-to-end ML pipeline (instruments → tick data → features → training → inference →
strategy → execution) must work in live mode for the three target venues.

## End-state at May 23 (success criteria)

- [ ] **Continuous ML prediction signal live** on real capital across OKX + Binance + Bybit, ≥7 continuous days.
- [ ] **End-to-end ML pipeline live**: live tick data → live features → live model inference → live strategy decision →
      live execution → live position + risk + P&L attribution.
- [ ] **Backtest fidelity** for the same signal proven via 2-year batch backtest config grid (per Group F item 18 of
      master plan readiness checklist) — live config informed by backtest, not guessed.
- [ ] **Live model lifecycle**: hot-reload of model artefacts without service restart; model-version traceability per
      trade; model-drift alerting wired through alerting-service.
- [ ] **Live alerting active**: signal-staleness + execution-quality + P&L deviation + position breaches alert through
      alerting-service. **Taxonomy shipped 2026-05-08 at UAC@6c4784f** (Tab 5 Item 6) — 6 ML AlertCodes
      (`KILL_SWITCH_ML_MODEL_FAILURE` / `ML_SIGNAL_STALENESS` / `ML_MODEL_DRIFT_DETECTED` / `ML_PNL_DEVIATION` /
      `ML_INFERENCE_LATENCY_BREACH` / `ML_MODEL_VERSION_MISMATCH`) + 5 thresholds + 6 rules. Producer wiring DEFERRED to
      alerting plan Phase 3 (BLOCKED on UAC envelope `code: AlertCode` field gap).
- [ ] **Kill switches + circuit breakers** wired per archetype: position-limit breach, P&L drawdown threshold,
      signal-staleness, model-drift detection. **`KILL_SWITCH_ML_MODEL_FAILURE` taxonomy shipped 2026-05-08 at
      UAC@6c4784f**, `kill_switch_scope=ARCHETYPE` semantics documented in
      `/codex/14-playbooks/alerting/alert-code-taxonomy.md`. Service wiring still pending (alerting plan Phase 2
      kill-switch publisher hook + execution-service halt-pump consumer).
- [ ] **DART manual override**: operator can pause / override / replicate any ML-driven trade as a manual trade.
      DEFERRED — lives in `strategy_and_dart_master_2026_05_07.md` Phase 2.2; out of scope for the alerting taxonomy
      ship.

## What's IN scope

- One continuous ML prediction archetype tradable across 3 CeFi venues (OKX, Binance, Bybit).
- Full live ML pipeline: instruments → MTDS → MDPS → features → ML training (batch baseline) → ML inference (live) →
  strategy → execution → position-balance → risk → P&L attribution.
- Live model artefact registry + hot-reload + version traceability.
- Live alerting + kill switches + circuit breakers tied to the ML signal lifecycle.
- DART manual-trade replication of every live ML trade.
- Backtest fidelity proof (2-year config grid → live config baseline).

## What's OUT of scope (shipping later)

- Live ML across additional CeFi venues (Deribit, Bitfinex, Bitget, etc.) — fast-follow post-May-23.
- Multiple concurrent ML archetypes (only one live this cycle).
- Cross-asset-group ML signals (CeFi+DeFi+TradFi joint signal) — that's a longer build.
- Full AWS-side parity for live ML (single-cloud GCP live is acceptable; AWS proven for batch only).

## Sub-plans this epic consumes

| Path                                                                                                             | Role                                                                                     | Status |
| ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------ |
| [`cefi_master_2026_05_07`](./cefi_master_2026_05_07.md)                                                          | CeFi venue + pipeline umbrella (Bybit / Deribit / Binance / OKX / others)                | Active |
| [`ml_and_features_master_2026_05_07`](./ml_and_features_master_2026_05_07.md)                                    | ML lifecycle + features umbrella (training/inference, model registry, hot-reload, drift) | Active |
| [`strategy_and_dart_master_2026_05_07`](./strategy_and_dart_master_2026_05_07.md)                                | Strategy v2 + DART manual-trade lane                                                     | Active |
| [`instruments_live_master_2026_05_08`](./instruments_live_master_2026_05_08.md)                                  | Live instrument refresh + lifecycle for OKX/Binance/Bybit                                | Active |
| [`active/live_pipeline_mtds_mdps_features_2026_05_08`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md) | Live pipeline activation (MTDS/MDPS/features) — gates live ML inference                  | Active |
| [`active/features_repo_consolidation_2026_05_08`](../active/features_repo_consolidation_2026_05_08.md)           | Features-repo consolidation (pre-req for live-pipeline plan; merges 8 features-\* repos) | Active |
| [`active/alerting_service_live_rules_2026_05_07`](../active/alerting_service_live_rules_2026_05_07.md)           | Live alerting rules (signal staleness, model drift, P&L deviation)                       | Active |
| [`infrastructure_master_2026_05_07`](./infrastructure_master_2026_05_07.md)                                      | Infrastructure umbrella                                                                  | Active |

## Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_2026` for strategy catalogue (this archetype on the catalogue), strategy IDs,
  client wiring, infrastructure baseline.
- **Shares with:** `live_defi_rollout_may_23_2026` shares CeFi venue connectivity (Bybit + Binance + OKX overlap;
  Deribit only on DeFi-rollout side this cycle). Same execution-service adapters, same alerting rules apply.
- **Provides to:** `sp_prediction_may_23_2026` and `sports_ml_may_23_2026` share the ML lifecycle infrastructure (model
  registry, training pipeline, drift detection, batch backtest harness) — wins here propagate to those batch-only ML
  epics.

## Cross-cutting concerns inherited

See [`cross_cutting_may_23_2026.epic.md`](./cross_cutting_may_23_2026.epic.md). Specific to this epic:

- **Strategy catalogue (HARD)**: this ML archetype × all 3 venues enumerated.
- **Strategy IDs**: stable per-archetype + per-model-version IDs so live trades + reconciliation can attribute the
  correct model to the correct fill.
- **UI replication (DART)**: every live ML trade is also reproducible as a manual trade.
- **Infrastructure**: model registry hot-reload, deployment maturity, environments, live observability.

## Open questions

- [ ] **Which ML archetype family?** ([Master plan Q&A 7](../active/master_to_live_defi_2026_05_23.md) defaulted
      "running on representative sample (not necessarily deployed in production)" for CeFi — this epic flips that to
      "deployed in production." Confirm: which specific archetype goes live? Operator direction needed.)
- [ ] **Model retraining cadence**: continuous? daily? weekly? Affects features pipeline staleness budgets and alerting
      thresholds.
- [ ] **Capital scale**: trade size + position cap for the live signal. Operator-set per archetype IDs.

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — May-23 cutover master
- [`/codex/04-architecture/ml-experiment-lifecycle.md`](/codex/04-architecture/ml-experiment-lifecycle.md) (codex gap;
  lands as part of `ml_and_features_master`)
- [`/codex/04-architecture/batch-live-pipeline.md`](/codex/04-architecture/batch-live-pipeline.md)

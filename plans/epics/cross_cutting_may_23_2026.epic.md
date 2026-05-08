---
plan_type: epic
asset_group: cross-cutting
owner: ikenna
created: 2026-05-08
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
name: cross-cutting-may-23-2026
parent: master_to_live_defi_2026_05_23
status: active
deadline: 2026-05-23
---

# Epic — Cross-Cutting (May 23 2026)

## Why this epic exists

Five cross-cutting concerns wrap around all 6 domain epics for May 23. None of them are domain-specific; all of them are
non-negotiable for cutover. Per operator direction 2026-05-08:

> "Cross-cutting concerns across all of them are things like clients, strategy IDs, strategy catalogue (even if we're
> not launching all the strategies, is a hard requirement for May 23 that we have all of the archetypes and all of the
> venue combinations and stuff done so that we know what the universe looks like)... a wrap around all of this is that
> the UI needs to be able to replicate everything that we're doing... Anything to do with infrastructure, stability,
> environments, deployment, maturity, live functionality, speed, that all needs to be cross-cutting concerns for 23rd of
> May anyway, because the system has to be perfect in terms of infrastructure. We can't take shortcuts on that side."

## The 5 cross-cutting deliverables

### 1. Strategy catalogue (HARD requirement)

Every archetype × every venue combination must be enumerated in the strategy catalogue, **even if not launching this
cycle**, so the universe is visible. Live archetypes for May 23 are a small subset; the full universe must be modeled so
onboarding new ones post-May-23 is config-only, not code-greenfield.

- [ ] Strategy catalogue lists all archetype families: carry (3 sub-types), price-arb (3 sub-types), ML prediction
      (per-asset-group), prediction-markets (4 sub-types), and any others.
- [ ] Per-archetype venue matrix populated: every (archetype, venue, instrument-type) combination known to be feasible
      is a row.
- [ ] Per-archetype configuration parameters declared (collateral, hedge ratios, position caps, kill-switch thresholds).
- [ ] Strategy catalogue UI reflects the full universe (filter by asset_group / archetype / venue / live-vs-backtest).

### 2. Strategy IDs

Stable, traceable, machine-readable strategy IDs for every archetype × venue combination. Used by:

- live trades (per-fill attribution)
- batch backtest result attribution
- batch-vs-live reconciliation
- alerting (which strategy fired the alert)
- DART manual-trade replication
- model registry (which model is bound to which strategy ID, for ML-driven archetypes)

- [ ] Strategy ID schema declared in UAC (canonical naming + versioning).
- [ ] Strategy ID registry populated for every catalogue row.
- [ ] Every code-path that creates a trade / fill / signal / model-inference uses strategy IDs, not free-form strings.

### 3. Clients + Accounts

Client and account configuration must be wired for live capital allocation across all live archetypes (DeFi rollout +
CeFi ML).

- [ ] Client model in UAC stable; account-per-venue mapping wired.
- [ ] Capital allocation matrix per (client, archetype, venue) declared and respected at execution time.
- [ ] Client-account-strategy tagging propagated through every live trade + batch backtest result.

### 4. UI replication of every live action (DART manual-trade lane)

Every live trade / model training / DeFi swap / CeFi order / sports bet that the system can do automatically must also
be replicable as a **manual operator action through the UI**. This is the operator's safety valve — if the automated
side has a bug, the manual side ships the trade.

- [ ] DART manual-trade UI supports every live archetype (DeFi rollout carry archetypes + CeFi ML archetype).
- [ ] DART exposes manual ML training trigger (pause-resume model retraining for any in-flight ML archetype).
- [ ] DART exposes manual DeFi swap / lend / borrow / stake actions for the carry-staked-basis archetype.
- [ ] DART exposes manual CeFi order placement across the 4 live CeFi venues.
- [ ] DART exposes manual sports bet placement (for sports backtest exec validation, not live).

### 5. Infrastructure / stability / environments / deployment maturity / live functionality / speed

The system has to be **perfect** at the infrastructure layer for May 23 cutover. Any shortcuts here jeopardise the live
trading goal directly.

- [ ] **Deployment maturity**: every service deployable via deployment-UI without SSH; tarball + image deploy modes both
      work; AWS↔GCP parity for at least one carry archetype's full stack.
- [ ] **Environments**: staging / SIT / production environments isolated; promotion path canonical (quickmerge → main →
      staging → SIT → prod).
- [ ] **Live functionality**: every live-mode service (PBM, R&E, P&L attribution, alerting, batch-vs-live recon) shipped
      and code-complete, not scaffold.
- [ ] **Live observability**: VM event streaming complete; deployment-UI tails logs/events without SSH; per-instrument
      progress events emitted; silent-success-with-zero-output detectable from event stream alone.
- [ ] **Speed**: in-region slicer fast-path for data-status + drilldown; deployment-stack restart < 30s; dev tier 0
      boots < 60s.
- [ ] **Stability**: zombie watchdog covering every VM prefix; manifest concurrency protocol respected by every backfill
      script; per-VM shard isolation everywhere there's multi-worker.
- [ ] **CI infrastructure**: workspace-wide QG sweep clean (operator's 2026-05-07 → 2026-05-09 cleanup pass); semver
      agents healthy; force-sync drift checks clean.

## Sub-plans this epic consumes

| Path                                                                                                                                                         | Role                                                                                                                                                                                                                          | Status |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| [`active/cross_cutting_may_23_deliverables_2026_05_08`](../active/cross_cutting_may_23_deliverables_2026_05_08.md)                                           | **Critical-path child plan** — May-23 critical-path slice covering deliverables #1-#4 (catalogue + IDs + clients + DART). Owners: Ikenna Tab 6 (design) + Harsh Tab 6 (build). Added 2026-05-08 mid-cycle to close audit gap. | Active |
| [`infrastructure_master_2026_05_07`](./infrastructure_master_2026_05_07.md)                                                                                  | Infrastructure umbrella (deployment, observability, AWS, runtime parity)                                                                                                                                                      | Active |
| [`manifest_migration_master_2026_05_07`](./manifest_migration_master_2026_05_07.md)                                                                          | Manifest schema v6 + migration coordination                                                                                                                                                                                   | Active |
| [`active/writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.md)                                         | Write-gate / honest-coverage umbrella                                                                                                                                                                                         | Active |
| [`active/available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md)                                 | `available_at` end-to-end chain coordinator (MDPS bar boundary + per-asset-group adapter stamping + `FEATURE_REQUIRED_INPUTS` expansion + Tab 12 deferral tracker + QG static check + e2e test)                               | Active |
| [`active/aws_migration_defi_first_2026_05_07`](../active/aws_migration_defi_first_2026_05_07.md)                                                             | AWS↔GCP parity (DeFi-first scope, generalises post-May-23)                                                                                                                                                                   | Active |
| [`active/deployment_api_work_stream_a_2026_05_07`](../active/deployment_api_work_stream_a_2026_05_07..md                                                     | deployment-api work stream A                                                                                                                                                                                                  | Active |
| [`active/deployment_ui_lifecycle_tabs_2026_05_08`](../active/deployment_ui_lifecycle_tabs_2026_05_08.md)                                                     | deployment-UI lifecycle tabs (live observability)                                                                                                                                                                             | Active |
| [`active/deploy_missing_auto_launch_2026_05_07`](../active/deploy_missing_auto_launch_2026_05_07.md)                                                         | Deploy-Missing UI auto-launch                                                                                                                                                                                                 | Active |
| [`active/launcher_scripts_consolidation_into_deployment_service_2026_05_07`](../active/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md) | Launcher script SSOT consolidation                                                                                                                                                                                            | Active |
| [`active/data_status_comprehensive_test_coverage_2026_05_07`](../active/data_status_comprehensive_test_coverage_2026_05_07.md)                               | Data-status test coverage                                                                                                                                                                                                     | Active |
| [`active/data_status_drilldown_shard_atom_alignment_2026_05_07`](../active/data_status_drilldown_shard_atom_alignment_2026_05_07.md)                         | Data-status drilldown shard-atom alignment                                                                                                                                                                                    | Active |
| [`strategy_and_dart_master_2026_05_07`](./strategy_and_dart_master_2026_05_07.md)                                                                            | Strategy v2 + DART manual-trade lane (covers UI replication deliverable)                                                                                                                                                      | Active |
| [`active/audit_followups_2026_05_07`](../active/audit_followups_2026_05_07.md)                                                                               | Audit follow-ups across services                                                                                                                                                                                              | Active |
| [`active/hard_schema_enforcement_2026_05_08`](../active/hard_schema_enforcement_2026_05_08.md)                                                               | Hard schema enforcement (deployment maturity)                                                                                                                                                                                 | Active |
| [`active/mtds_databento_path_streaming_2026_05_07`](../active/mtds_databento_path_streaming_2026_05_07.md)                                                   | MTDS streaming + speed                                                                                                                                                                                                        | Active |
| [`active/mdps_streaming_and_backpressure_2026_05_07`](../active/mdps_streaming_and_backpressure_2026_05_07.md)                                               | MDPS streaming + speed                                                                                                                                                                                                        | Active |
| [`active/mtds_per_instrument_download_api_2026_04_24`](../active/mtds_per_instrument_download_api_2026_04_24.md)                                             | MTDS per-instrument download API                                                                                                                                                                                              | Active |
| [`active/instruments_and_market_tick_data_completion_2026_05_01`](../active/instruments_and_market_tick_data_completion_2026_05_01..md                       | Instruments + MTDS completion                                                                                                                                                                                                 | Active |
| [`active/ml_pipeline_ui_integration_2026_04_16`](../active/ml_pipeline_ui_integration_2026_04_16..md                                                         | ML pipeline UI integration (DART → ML training trigger)                                                                                                                                                                       | Active |

## Cross-epic handshakes

- **Provides to:** Every other epic depends on this one. Strategy catalogue + strategy IDs + clients are referenced by
  every live or backtest archetype. UI replication is the operator's safety valve for every live archetype.
  Infrastructure is the substrate everything else runs on.

## Open questions

- [ ] **Strategy catalogue completeness — what's the bar for "complete"?** Every archetype × venue × instrument-type
      combination, OR archetype-level completeness with venue/instrument lookups deferred? Operator-pick.
- [ ] **DART manual-trade lane scope**: is operator-only manual sufficient, or do we need a third-party broker-style
      DART for external operators?
- [ ] **AWS parity scope at this layer**: only DeFi-rollout coverage, or full workspace AWS coverage by May 23? Master
      plan defaults to DeFi-only, with full coverage post-May-23.

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — May-23 cutover master
- [`codex/04-architecture/cloud-agnostic-migration.md`](../../codex/04-architecture/cloud-agnostic-migration.md)
- [`codex/05-infrastructure/launcher-script-ssot.md`](../../codex/05-infrastructure/launcher-script-ssot.md)
- [`codex/09-strategy/strategy-summary.md`](../../codex/09-strategy/strategy-summary.md) (the 8-family / 18-archetype
  catalogue baseline)
- [`codex/09-strategy/cross-cutting/operational-modes-matrix.md`](../../codex/09-strategy/cross-cutting/operational-modes-matrix.md)
- [`codex/09-strategy/cross-cutting/onboarding-checklist.md`](../../codex/09-strategy/cross-cutting/onboarding-checklist.md)

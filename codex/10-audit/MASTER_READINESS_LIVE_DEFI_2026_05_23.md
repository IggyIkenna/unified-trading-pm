---
doc_type: codex-ssot
title: Master Readiness — Live DeFi Trading by 2026-05-23
summary:
  Codex companion SSOT to the live-DeFi master plan — owns the durable 7-group / 23-item per-service readiness model
  (code health, data correctness, runtime parity, coverage, operability, trading prereqs, operator UX), the
  doc-touchpoint map, and the plan↔doc↔code drift-audit pattern for the 2026-05-23 live-DeFi cutover.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
  ]
scope: [engineer, admin]
tags: [defi, live-trading, mvp, data-correctness, readiness, cefi]
related:
  [
    plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
    codex/10-audit/REPO_READINESS_CHECKLIST.yaml,
    codex/POST_PLAN_REALITY_2026_05_06.md,
  ]
created: 2026-05-23
authoritative_for: [live-defi May-23 per-service readiness model (7-group 23-item)]
referenced_by:
owner:
last_reviewed:
code_refs:
last_refreshed: 2026-05-15
refresh_note:
  A-G sweep after heavy multi-slot shipping (slots 2-9, 2026-05-14/15). Custody item 19 corrected to reflect
  CLOUD_KMS_ENCRYPTED as May-23 custody method (Copper+CEFFU are June-1). No structural model changes to 23 items; all
  group descriptions confirmed accurate vs shipped code.
---

# Master Readiness — Live DeFi Trading by 2026-05-23

**Status:** Active companion SSOT for the master plan. **Working plan (authoritative for current state + todos):**
[`plans/archive/2026_07/master_to_live_defi_2026_05_23.md`](../../plans/archive/2026_07/master_to_live_defi_2026_05_23.md)
**Created:** 2026-05-06 **Locked to:** `live-defi-rollout`

This file is the **codex SSOT companion** to the master plan. It owns the durable bits (readiness model, doc-touchpoint
map, drift audit pattern). The plan owns the working bits (current state, Q&A, risk register, week-by-week DAG, todos).
Refresh from the plan when the durable bits change.

---

## Headline goal (mirror)

Two DeFi archetypes trade live on a real wallet for ≥7 continuous days by 2026-05-23:

1. **`carry_staked_basis`** — _ultimate priority_ — recursive LST staking + CeFi/DeFi perp short hedge.
2. **`leveraged_funding_arb`** — cross-venue funding-rate spread.

Six perp venues live: **Bybit, Deribit, Binance, OKX** (CeFi) + **Hyperliquid, Aster** (DeFi perp DEXs). TradFi / Sports
/ Prediction stay batch-only this cycle; their ML readiness ladders run in parallel so post-DeFi archetypes launch fast.

Concurrent goal: **full AWS↔GCP cloud parity** by May 23 — DeFi-relevant data migrated to S3, batch backfill +
backtest + ML + live trading + monitoring all runnable on AWS, seamless switch between AWS-live / AWS-batch / GCP-live /
GCP-batch.

---

## Per-service readiness — 7 groups / 23 items (the durable model)

This is the augmentation of `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` for the live-defi cutover. Per-service yamls
in `repos/<service>.yaml` extend their item set to track 4–23 (items 1–3 are the existing repo-readiness gates).

### Group A — Code health (always-on)

1. **QG pass** — `bash scripts/quality-gates.sh` two-pass clean (full + quickmerge)
2. **Quickmerge** — branch landed `live-defi-rollout` → main via SIT
3. **Semver agent** — `feat:` / `fix:` / `feat!:` triggers version bump

### Group B — Data correctness (always-on)

4. **Smoke test** — representative `(asset_group, data_type, day)` triples produce valid parquet
5. **Manifest hookup + cluster validation** — `ManifestWriter.record_{captured,empty,failed}` with
   `expected_root_clusters` + `cluster_extractor` for bundled types
6. **Upstream validation** — `DependencyError(fail_fast=True)` at boundary; honest absence categories A/B/C; no silent
   placeholder rows
7. **UAC/UTL abstraction** — domain types in UAC, runtime utilities in UTL, only service-specific config inline
8. **Schema validation** — parquet schema matches UAC contract per `record_captured` (4-pillar write-gate item 3)

### Group C — Runtime parity (always-on)

9. **Hot reload** — `start_domain_config_reloaders` typed; `ApiKeyReloader` for Secret Manager creds
10. **Batch = live** — same code path; only fill source differs (batch-live-architecture.md — single SSOT)
11. **AWS + GCP parity** — both VM launch paths green; `CLOUD_PROVIDER` toggle works end-to-end
    (cloud-agnostic-migration.md)

### Group D — Coverage & shard (data-producing services)

12. **Data status accurate** — deployment-UI rollup matches on-disk truth-set
13. **Shard granularity correct** — matches `02-data/availability-manifest-and-data-status.md` per-asset-group matrix
14. **Full-window backfill** — ≥2 years of representative history captured (per CLAUDE.md "honest absence")

### Group E — Operability (always-on)

15. **UTS-UI summary** — service surfaces visible in unified-trading-system-ui where relevant
16. **Deployment-UI launch + GCS log streaming** — backfill / restart / forward-poll launchable from UI without SSH; VM
    event logs pooled to `gs://{pid}-events/`

### Group F — Trading prerequisites (live-only services)

17. **Backtest fidelity** — real gas, real market impact, realistic matching engine for AMM pools / perpetuals / spots /
    transfers / atomic transfers / flash loans (backtest-groups.md, batch-live-architecture.md — single SSOT)
18. **2-year batch backtest run** — completed across config grid; P&L variance per archetype configuration captured
19. **Treasury / custody integration** — **May-23: `CLOUD_KMS_ENCRYPTED`** (GCP KMS for all live keys; no Copper/CEFFU
    dependency on cutover date). Copper (DeFi side) + CEFFU (Binance institutional flow) are **June-1** follow-ons.
    Single SSOT: `/codex/04-architecture/custody-providers.md` (Copper + CEFFU + LocalKey + Mock; folded 2026-05-08,
    replaces former per-provider docs)
20. **Live testnet replicates prod** — Tenderly fork / forked-mainnet for DeFi; Binance testnet / Bybit testnet for CeFi
21. **Reconciliation suite** — batch-vs-live reconciliation, P&L attribution decomposed per source, per-trade
    reconciliation (pnl-attribution.md, batch-live-reconciliation-service)
22. **Trading guardrails** — circuit breakers per archetype; kill switches (autonomous-recovery-matrix.md); alerting on
    data-freshness / P&L / position breaches (alerting-batch-live.md); auto-recovery for transients

### Group G — Operator UX (live-only)

23. **DART manual-trade gate** — DART terminal in UTS-UI visualizes the strategy archetype end-to-end; operator first
    puts trades on manually → backend executes through the same path as automation → monitor for the gate window → flip
    switch to automation (operational-modes-matrix.md)

---

## Doc-touchpoint map — bi-directional

**Principle.** _Docs are the intent._ Codex SSOTs are always **ahead of the code** and **in line with the plans**. Order
of operations: **doc → plan → code**.

- **Before working on X** — read the listed SSOTs first. They define the intent. If unclear or stale, update the doc
  _first_, then write/change code.
- **After changing X** — update the same SSOTs (and the matching plan) so the doc stays the source of truth.

| If you change…                      | Update these SSOTs                                                                                                                                                                                                                                                   |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manifest schema                     | `02-data/availability-manifest-and-data-status.md` · `02-data/shard-granularity-cefi.md` · `02-data/sports-scheduling-and-sharding.md` · `02-data/prediction-schema-paths.md` · `02-data/per-asset-group-bucket-layouts.md` · UTL `manifest_writer.py` · `CLAUDE.md` |
| Batch/live equivalence              | `04-architecture/batch-live-architecture.md` (single SSOT — replaces former `batch-live-pipeline.md` + `batch-live-symmetry.md`) · `backtest-groups.md` · `CLAUDE.md`                                                                                                |
| Cloud-agnostic VM/build             | `04-architecture/cloud-agnostic-migration.md` · `05-infrastructure/vm-tarball-deployment.md` · `05-infrastructure/cloud-agnostic-build-lineage.md` (new) · launchers + `_code_builds_aws.py` · `CLAUDE.md`                                                           |
| Strategy archetype config           | `09-strategy/strategy-summary.md` · `09-strategy/architecture-v2/` · `09-strategy/operational/onboarding-checklist.md` · the archetype-specific sub-plan                                                                                                             |
| Custody / treasury                  | `04-architecture/custody-providers.md` (single SSOT — Copper + CEFFU + LocalKey + Mock) · `wallet-hierarchy-and-capital-flow.md` · `unified-config-interface/testnet_contracts.py`                                                                                   |
| Live observability                  | `03-observability/lifecycle-events.md` · `coordination-events.md` · `04-architecture/alerting-batch-live.md` · `autonomous-recovery-matrix.md` · `05-infrastructure/live-deployment-monitoring.md` (new) · UAC `internal/events.py` · `CLAUDE.md`                    |
| P&L attribution / B-vs-L recon      | `09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` · `batch-live-reconciliation-service` plan · pnl-attribution-service plan                                                                                                                             |
| Service readiness                   | `codex/10-audit/repos/<service>.yaml` · `REPO_READINESS_CHECKLIST.yaml` · the master plan's matrix                                                                                                                                                                   |
| Operational modes / DART            | `09-strategy/architecture-v2/cross-cutting/operational-modes-matrix.md` · `04-architecture/research-service-and-dart-integration.md` (new)                                                                                                                           |
| ML experiment lifecycle             | `04-architecture/ml-experiment-lifecycle.md` (new) · `02-data/data-lineage-MTDS-features-ml.md`                                                                                                                                                                      |
| Hot-reload semantics                | `06-coding-standards/config-reloader-pattern.md` · `04-architecture/live-strategy-config-hot-reload.md` (new) · `CLAUDE.md`                                                                                                                                          |
| Service infrastructure requirements | `06-coding-standards/service-structure-standards.md` · `base-service.sh` STEP 5.x · `CLAUDE.md`                                                                                                                                                                      |
| Asset-group vocabulary              | `CLAUDE.md` · UAC `market_data_categories` · `venue_axis_asset_group_vocabulary_2026_04_25` plan                                                                                                                                                                     |
| Lookahead bias / available_at       | UAC `availability_semantics` · UTL `availability_stamping.py` · `02-data/availability-manifest-and-data-status.md` § available_at · `POST_PLAN_REALITY_2026_05_06.md` Principle 5 · `CLAUDE.md`                                                                      |

**Agent rule.** Before merging any change in scope of one of the rows above:

1. The PR description lists the docs read at the start (the "doc-first" check).
2. The commit touches **all** listed SSOTs in the relevant row, or the PR explicitly states why a given SSOT is
   unaffected.
3. The corresponding sub-plan in `plans/active/` agrees with the doc — if disagree, update the plan first.

Drift between any of (codex doc, sub-plan, code) is a review-blocking failure.

---

## Plan ↔ Doc ↔ Code drift audit (mirror)

The full table with current `⚠` flags and resolution paths lives in
[the working plan](../../plans/archive/2026_07/master_to_live_defi_2026_05_23.md#plan--doc--code-drift-audit). Update
both when a row resolves.

**Audit guideline going forward.** Whenever an agent touches a row in this table, the PR includes a one-line "drift
status: resolved / unchanged / new-drift" note in the description. New drift = a new row added to the table.

---

## Tier-1 service list (live by May 23)

The 7-group readiness applies to:

- instruments-service
- market-tick-data-service
- market-data-processing-service
- features-service (onchain family)
- features-service (volatility family)
- features-service (cross-instrument family)
- ml-training-service
- ml-inference-service
- strategy-service
- execution-service
- position-balance-monitor-service — work folded into
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
  (live-mode wiring) + Group F readiness items 17/18/19 of master plan
- risk-and-exposure-service — work folded into
  [`alerting_service_live_rules_2026_05_07`](../../plans/active/alerting_service_live_rules_2026_05_07.md) Phase 9
  circuit-breaker integration + Group F readiness items 17/19 of master plan
- pnl-attribution-service — work folded into
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
  Phase 12 batch-live reconciler + Group F readiness item 21 of master plan
- alerting-service ✓
  [`alerting_service_live_rules_2026_05_07`](../../plans/active/alerting_service_live_rules_2026_05_07.md) (P0, deadline
  2026-05-23 — circuit breakers + paging + ServiceEmissionPolicy tier-up)
- batch-live-reconciliation-service — work folded into
  [`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md)
  Phase 12 + Group F readiness item 21 of master plan; UTL `batch_live_reconciler` already shipped per UTL@908b1647

> **Audit refresh 2026-05-08**: 5 service rows above previously read "⚠ NO PLAN" — that was technically accurate (no
> DEDICATED plan files for 4 of 5 services) but operationally misleading. The work for these 5 services lives in the
> cross-cutting umbrella plans cited above. alerting-service IS dedicated. The other 4 do not need their own plan files;
> their phases are explicit todos in the named umbrellas. Reviewers should follow those links to find the actual phase /
> todo / gate ownership.

> **Re-verified 2026-05-15** (slot 6 A-G sweep): service list confirmed accurate. Key updates vs 2026-05-08:
>
> - Group F item 19 (custody): corrected to CLOUD_KMS_ENCRYPTED for May-23; Copper+CEFFU deferred to June-1 (aligned
>   with `/codex/04-architecture/custody-providers.md` which is the live SSOT — drift-audited clean per slot 6 item 5).
> - batch-live-reconciliation-service: UTL `batch_live_reconciler` confirmed shipped + concurrency-tested.
> - DeFi error classification: **35 codes** in `DefiErrorCode` (13 Aave + 7 RECURSIVE_LOOP + 8 HL\_ + 2 ORACLE\_ + 5
>   CCTP added 2026-05-19); CLAUDE.md + this codex updated 2026-05-24 per F-27 (AUDIT-03 §6) —
>   /codex/04-architecture/defi-execution-overview.md is accurate SSOT.
> - No structural changes to 23-item A-G model.

- deployment-api
- deployment-service
- deployment-ui
- unified-trading-system-ui

**Tier-2 (parallel ML ladder, NOT live):** features-service (sports family) · features-service (calendar family) ·
features-service (delta-one family) · features-service (commodity family).

**Tier-3 (post-launch):** client-reporting-api · fund-administration-service · trading-agent-service.

---

## Cross-references

- Working plan:
  [`plans/archive/2026_07/master_to_live_defi_2026_05_23.md`](../../plans/archive/2026_07/master_to_live_defi_2026_05_23.md)
- Repo readiness SSOT: [`REPO_READINESS_CHECKLIST.yaml`](./REPO_READINESS_CHECKLIST.yaml)
- Per-service yamls: [`repos/`](./repos/)
- Cross-cutting principles: [`POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md)
- Codex master index: [`00-SSOT-INDEX.md`](../00-SSOT-INDEX.md)

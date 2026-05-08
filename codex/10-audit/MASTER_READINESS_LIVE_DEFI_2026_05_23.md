---
scope: [engineer, admin]
---

# Master Readiness — Live DeFi Trading by 2026-05-23

**Status:** Active companion SSOT for the master plan. **Working plan (authoritative for current state + todos):**
[`plans/active/master_to_live_defi_2026_05_23.md`](../../plans/active/master_to_live_defi_2026_05_23.md) **Created:**
2026-05-06 **Locked to:** `live-defi-rollout`

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
10. **Batch = live** — same code path; only fill source differs (batch-live-pipeline.md, batch-live-symmetry.md)
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
    transfers / atomic transfers / flash loans (backtest-groups.md, batch-live-symmetry.md)
18. **2-year batch backtest run** — completed across config grid; P&L variance per archetype configuration captured
19. **Treasury / custody integration** — Copper for DeFi side; CEFFU for Binance institutional flow. Single SSOT:
    `codex/04-architecture/custody-providers.md` (Copper + CEFFU + LocalKey + Mock; folded 2026-05-08, replaces former
    per-provider docs)
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

| If you change…                      | Update these SSOTs                                                                                                                                                                                                                                                |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manifest schema                     | `02-data/availability-manifest-and-data-status.md` · `02-data/shard-granularity-cefi.md` · `02-data/sports-scheduling-and-sharding.md` · `02-data/prediction-schema-paths.md` · `02-data/per-category-bucket-layouts.md` · UTL `manifest_writer.py` · `CLAUDE.md` |
| Batch/live equivalence              | `04-architecture/batch-live-pipeline.md` · `batch-live-symmetry.md` · `backtest-groups.md` · `CLAUDE.md`                                                                                                                                                          |
| Cloud-agnostic VM/build             | `04-architecture/cloud-agnostic-migration.md` · `05-infrastructure/vm-tarball-deployment.md` · `05-infrastructure/cloud-agnostic-build-lineage.md` (new) · launchers + `_code_builds_aws.py` · `CLAUDE.md`                                                        |
| Strategy archetype config           | `09-strategy/strategy-summary.md` · `09-strategy/architecture-v2/` · `09-strategy/cross-cutting/onboarding-checklist.md` · the archetype-specific sub-plan                                                                                                        |
| Custody / treasury                  | `04-architecture/custody-providers.md` (single SSOT — Copper + CEFFU + LocalKey + Mock) · `wallet-hierarchy-and-capital-flow.md` · `unified-config-interface/testnet_contracts.py`                                                                                |
| Live observability                  | `03-observability/lifecycle-events.md` · `coordination-events.md` · `04-architecture/alerting-batch-live.md` · `autonomous-recovery-matrix.md` · `05-infrastructure/live-deployment-monitoring.md` (new) · UAC `internal/events.py` · `CLAUDE.md`                 |
| P&L attribution / B-vs-L recon      | `09-strategy/cross-cutting/pnl-attribution.md` · `batch-live-reconciliation-service` plan · pnl-attribution-service plan                                                                                                                                          |
| Service readiness                   | `codex/10-audit/repos/<service>.yaml` · `REPO_READINESS_CHECKLIST.yaml` · the master plan's matrix                                                                                                                                                                |
| Operational modes / DART            | `09-strategy/cross-cutting/operational-modes-matrix.md` · `04-architecture/research-service-and-dart-integration.md` (new)                                                                                                                                        |
| ML experiment lifecycle             | `04-architecture/ml-experiment-lifecycle.md` (new) · `02-data/data-lineage-MTDS-features-ml.md`                                                                                                                                                                   |
| Hot-reload semantics                | `06-coding-standards/config-reloader-pattern.md` · `04-architecture/live-strategy-config-hot-reload.md` (new) · `CLAUDE.md`                                                                                                                                       |
| Service infrastructure requirements | `06-coding-standards/service-structure-standards.md` · `base-service.sh` STEP 5.x · `CLAUDE.md`                                                                                                                                                                   |
| Asset-group vocabulary              | `CLAUDE.md` · UAC `market_data_categories` · `venue_axis_asset_group_vocabulary_2026_04_25` plan                                                                                                                                                                  |
| Lookahead bias / available_at       | UAC `availability_semantics` · UTL `availability_stamping.py` · `02-data/availability-manifest-and-data-status.md` § available_at · `POST_PLAN_REALITY_2026_05_06.md` Principle 5 · `CLAUDE.md`                                                                   |

**Agent rule.** Before merging any change in scope of one of the rows above:

1. The PR description lists the docs read at the start (the "doc-first" check).
2. The commit touches **all** listed SSOTs in the relevant row, or the PR explicitly states why a given SSOT is
   unaffected.
3. The corresponding sub-plan in `plans/active/` agrees with the doc — if disagree, update the plan first.

Drift between any of (codex doc, sub-plan, code) is a review-blocking failure.

---

## Plan ↔ Doc ↔ Code drift audit (mirror)

The full table with current `⚠` flags and resolution paths lives in
[the working plan](../../plans/active/master_to_live_defi_2026_05_23.md#plan--doc--code-drift-audit). Update both when a
row resolves.

**Audit guideline going forward.** Whenever an agent touches a row in this table, the PR includes a one-line "drift
status: resolved / unchanged / new-drift" note in the description. New drift = a new row added to the table.

---

## Tier-1 service list (live by May 23)

The 7-group readiness applies to:

- instruments-service
- market-tick-data-service
- market-data-processing-service
- features-onchain-service
- features-volatility-service
- features-cross-instrument-service
- ml-training-service
- ml-inference-service
- strategy-service
- execution-service
- position-balance-monitor-service ⚠ NO PLAN
- risk-and-exposure-service ⚠ NO PLAN
- pnl-attribution-service ⚠ NO PLAN
- alerting-service ⚠ NO PLAN
- batch-live-reconciliation-service ⚠ NO PLAN
- deployment-api
- deployment-service
- deployment-ui
- unified-trading-system-ui

**Tier-2 (parallel ML ladder, NOT live):** features-sports-service · features-calendar-service ·
features-delta-one-service · features-commodity-service.

**Tier-3 (post-launch):** client-reporting-api · fund-administration-service · trading-agent-service.

---

## Cross-references

- Working plan: [`plans/active/master_to_live_defi_2026_05_23.md`](../../plans/active/master_to_live_defi_2026_05_23.md)
- Repo readiness SSOT: [`REPO_READINESS_CHECKLIST.yaml`](./REPO_READINESS_CHECKLIST.yaml)
- Per-service yamls: [`repos/`](./repos/)
- Cross-cutting principles: [`POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md)
- Codex master index: [`00-SSOT-INDEX.md`](../00-SSOT-INDEX.md)

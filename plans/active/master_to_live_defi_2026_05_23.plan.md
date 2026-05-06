---
plan_type: meta
asset_group: cross-cutting
owner: ikenna
created: 2026-05-06
last_updated: 2026-05-06
locked_by: live-defi-rollout
locked_since: 2026-05-06
name: master-to-live-defi-2026-05-23
overview:
  Master rollup plan from now (2026-05-06) to live DeFi trading on a real wallet by 2026-05-23. Three deliverables in
  one doc - (1) master plan tracking surface that orchestrates the ~175 active sub-plans without duplicating them, (2)
  audit cross-referencing existing codex SSOTs and flagging plan/doc/code drift, (3) Q&A surface for decisions that
  cascade through everything else. The headline goal is two DeFi archetypes trading live on a real wallet for greater
  than or equal to seven continuous days - carry_staked_basis (ultimate priority - recursive LST staking with CeFi/DeFi
  perp short hedge) and leveraged_funding_arb (cross-venue funding spread). Both hedge on a six-venue perp universe
  spanning CeFi (Bybit, Deribit, Binance, OKX) and DeFi perp DEXs (Hyperliquid, Aster). Concurrent goal is full AWS plus
  GCP cloud parity by May 23 - DeFi-relevant data migrated to AWS, batch backfill plus backtest plus ML plus live
  trading all runnable on AWS, seamless switch between AWS-live, AWS-batch, GCP-live, GCP-batch. TradFi, Sports,
  Prediction stage to ML pipeline running on representative sample but not live this cycle. The plan never duplicates
  sub-plans - it references and orchestrates them. Doc-touchpoint map is bi-directional (read before working, update
  after changing) and a plan-doc-code drift audit table flags pre-existing drift that must be resolved before agents
  start writing code in the affected area.
---

# Master Plan — Live DeFi Trading by 2026-05-23

## What this plan is — three deliverables in one doc

1. **Master plan (product).** The single rollup tracking surface from now to live DeFi trading on 2026-05-23. Sub-plans
   in `unified-trading-pm/plans/active/` remain authoritative for tactical work; this plan never duplicates them, only
   references and orchestrates.
2. **Audit (process).** Cross-references to existing codex SSOTs and the ~175 active sub-plans. Surfaces overlaps,
   staleness, and conflicts so agents don't re-litigate decisions.
3. **Q&A (decision-gating).** Surfaces unresolved questions in one place so the human (Ikenna / Harsh) can answer once
   and agents stop guessing.

**This plan does not execute anything.** It writes itself, references real artefacts, and once approved is promoted to a
workspace location (see _Tracking surface_ below) where agents pick it up.

---

## Why this exists, what success looks like

**Headline goal.** **Two DeFi archetypes** trade live on a real wallet for ≥7 continuous days by 2026-05-23 (17 days
from today, 2026-05-06):

1. **`carry_staked_basis`** — _ultimate priority_ — recursive LST staking + CeFi/DeFi perp short hedge. Locked plan:
   `carry_staked_basis_structure_axis_2026_05_04`.
2. **`leveraged_funding_arb`** — cross-venue funding-rate spread trade. Locked plan:
   `defi_pipeline_extension_2026_05_01` + `leveraged_leg_controller_2026_05_01`.

Both archetypes hedge on a 6-venue perp universe spanning CeFi (Bybit, Deribit, Binance, OKX) and DeFi perp DEXs
(Hyperliquid, Aster) — **all six must be live**. TradFi / Sports / Prediction stay batch-only this cycle — but their ML
readiness ladders progress in parallel so the _next_ archetypes after DeFi launch quickly.

**Cloud-parity goal (concurrent with live trading goal).** Full AWS↔GCP parity by May 23: DeFi-relevant data migrated
to AWS (with prior cost analysis), data status working on AWS, batch backfill with `--force` working on AWS, backtests /
ML / strategy examples runnable on AWS, **and** a live trading deployment + monitoring instance running on AWS — so the
team can seamlessly switch any deployment between AWS-live / AWS-batch / GCP-live / GCP-batch. _Not every byte gets
migrated_ (waste of API quota when GCS already has it) — only what's needed for the DeFi proof.

**Authority split.**

- _Codex_ (`unified-trading-pm/codex/`) = target architecture. Mostly defined.
- _Sub-plans_ (`unified-trading-pm/plans/active/`, ~175) = current bug-fix / refactor / migration backlog.
- _This plan_ = readiness rollup + audit + Q&A + new work streams not yet plan-covered.

---

## Audit — existing SSOTs this plan augments (does NOT recreate)

The codex already has SSOTs covering most of what was raised in the brief. Cross-reference table:

| Concern raised                                 | Existing codex SSOT                                                                                                                      | Plan action                                                                                  |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Service readiness checklist                    | `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` + per-service `codex/10-audit/repos/<service>.yaml` + `_checklist-template-enhanced.yaml` | **Augment** with 7 groups / 23 items below; populate per-service yamls for tier-1            |
| Cloud-agnostic build / runtime                 | `codex/04-architecture/cloud-agnostic-migration.md`                                                                                      | Augment with build-lineage gap (work-stream D below)                                         |
| Custody / treasury (Copper)                    | `codex/04-architecture/copper-custody-integration.md`, `custody-providers.md`, `wallet-hierarchy-and-capital-flow.md`                    | Verify CEFFU coverage (Binance institutional custody) — likely a gap                         |
| Batch=live equivalence                         | `codex/04-architecture/batch-live-pipeline.md`, `batch-live-symmetry.md`, `backtest-groups.md`                                           | Verify backtest-fidelity rules per asset_group (real gas, real market impact, real matching) |
| Alerting                                       | `codex/04-architecture/alerting-batch-live.md`                                                                                           | Verify live-mode rule coverage; wire to alerting-service                                     |
| Auto-recovery / kill switches                  | `codex/04-architecture/autonomous-recovery-matrix.md`                                                                                    | Verify per-archetype kill-switch coverage                                                    |
| P&L attribution                                | `codex/09-strategy/cross-cutting/pnl-attribution.md`                                                                                     | Verify wired into batch-vs-live recon                                                        |
| Operational modes (manual / paper / automated) | `codex/09-strategy/cross-cutting/operational-modes-matrix.md`                                                                            | Add DART manual-trade lane (work-stream C below)                                             |
| Strategy onboarding                            | `codex/09-strategy/cross-cutting/onboarding-checklist.md`                                                                                | Verify end-to-end flow for `carry_staked_basis`                                              |
| Lifecycle events / observability               | `codex/03-observability/lifecycle-events.md`, `coordination-events.md`                                                                   | Verify GCS event-streaming endpoint exists for deployment-api                                |
| Deployment topology                            | `codex/04-architecture/deployment-topology-diagrams.md`, `RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg`                                           | Verify all tier-1 services represented                                                       |
| Shard granularity                              | `codex/02-data/availability-manifest-and-data-status.md`                                                                                 | Already canonical post-2026-05-06 multi-axis correction                                      |
| Strategy archetypes                            | `codex/09-strategy/strategy-summary.md` (8 families / 18 archetypes)                                                                     | `carry_staked_basis` is the lead candidate                                                   |

**Audit conclusion:** ~85% of target architecture has codex coverage. The 5 codex gaps to fill are listed in _Codex SSOT
gaps_ below — they are smaller than they first appear because the foundational docs already exist.

---

## SSOT touchpoint map — bi-directional (read before working · update after changing)

**Principle.** _Docs are the intent._ Codex SSOTs are always **ahead of the code** and **in line with the plans**. The
order of operations is **doc → plan → code**, never code-then-doc-when-someone-remembers. Drift between any pair
(doc/plan/code) is the failure mode this plan is designed to prevent.

The map below is bi-directional:

- **Before working on X** — read the listed SSOTs first. They define the intent. If the intent is unclear or stale,
  update the doc _first_, then write/change code.
- **After changing X** — update the same SSOTs (and the matching plan) so the doc stays the source of truth. Drift
  between code and SSOT is a CI / review failure, not a follow-up.

Rule of thumb: if it lives in `CLAUDE.md`, update there too.

| If you change…                                                                          | Update these SSOTs                                                                                                                                                                                                                                                                                                                                                                                             |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Manifest schema** (column, shard axis, validator, write-gate)                         | `codex/02-data/availability-manifest-and-data-status.md` · `codex/02-data/shard-granularity-cefi.md` · `codex/02-data/sports-scheduling-and-sharding.md` · `codex/02-data/prediction-schema-paths.md` · `codex/02-data/per-category-bucket-layouts.md` · `unified-trading-library/unified_trading_library/manifest_writer.py` (SSOT) · `CLAUDE.md` "Availability manifest" + "Shard-granularity SSOT" sections |
| **Batch/live equivalence rule**                                                         | `codex/04-architecture/batch-live-pipeline.md` · `batch-live-symmetry.md` · `backtest-groups.md` · `CLAUDE.md` "Batch = Live" + "Live = batch" sections                                                                                                                                                                                                                                                        |
| **Cloud-agnostic VM / build path**                                                      | `codex/04-architecture/cloud-agnostic-migration.md` · `codex/05-infrastructure/vm-tarball-deployment.md` · `codex/05-infrastructure/cloud-agnostic-build-lineage.md` (new — work-stream F) · `deployment-service/scripts/vm/` launchers · `deployment-api/deployment_api/routes/_code_builds_aws.py` · `CLAUDE.md` "VM tarball deployment" + "VM Naming Convention" sections                                   |
| **Strategy archetype config**                                                           | `codex/09-strategy/strategy-summary.md` · `codex/09-strategy/architecture-v2/` · `codex/09-strategy/cross-cutting/onboarding-checklist.md` · the archetype-specific sub-plan in `plans/active/` · `CLAUDE.md` if cross-cutting                                                                                                                                                                                 |
| **Custody / treasury wiring** (Copper, CEFFU)                                           | `codex/04-architecture/copper-custody-integration.md` · `custody-providers.md` · `wallet-hierarchy-and-capital-flow.md` · CEFFU doc (new, work-stream F) · `unified-config-interface/testnet_contracts.py` PROTOCOL_SCHEMAS                                                                                                                                                                                    |
| **Live observability** (events, alerts, kill switches, auto-recovery)                   | `codex/03-observability/lifecycle-events.md` · `coordination-events.md` · `codex/04-architecture/alerting-batch-live.md` · `autonomous-recovery-matrix.md` · `codex/05-infrastructure/live-deployment-monitoring.md` (new — work-stream B) · `unified-api-contracts/.../internal/events.py` (`LifecycleEventType`) · `CLAUDE.md` "no fire-and-forget VM launches" section                                      |
| **P&L attribution / batch-vs-live reconciliation**                                      | `codex/09-strategy/cross-cutting/pnl-attribution.md` · `batch-live-reconciliation-service` plan (work-stream E) · pnl-attribution-service plan (work-stream E)                                                                                                                                                                                                                                                 |
| **Service readiness** (per-service)                                                     | `codex/10-audit/repos/<service>.yaml` · `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` · this master plan's matrix                                                                                                                                                                                                                                                                                             |
| **Operational modes** (manual / paper / automated, DART terminal)                       | `codex/09-strategy/cross-cutting/operational-modes-matrix.md` · `codex/04-architecture/research-service-and-dart-integration.md` (new — work-stream C)                                                                                                                                                                                                                                                         |
| **ML experiment lifecycle**                                                             | `codex/04-architecture/ml-experiment-lifecycle.md` (new — work-stream F) · `codex/02-data/data-lineage-MTDS-features-ml.md` · `ml_pipeline_revolution_2026_04_11` plan                                                                                                                                                                                                                                         |
| **Hot-reload semantics**                                                                | `codex/06-coding-standards/config-reloader-pattern.md` · `codex/04-architecture/live-strategy-config-hot-reload.md` (new — work-stream F) · `CLAUDE.md` "Service Infrastructure Requirements"                                                                                                                                                                                                                  |
| **Service infrastructure requirements** (ServiceBootstrap, health API, typed reloaders) | `codex/06-coding-standards/service-structure-standards.md` · `base-service.sh` STEP 5.x in PM · `CLAUDE.md` "Service Infrastructure Requirements (QG-Enforced)"                                                                                                                                                                                                                                                |
| **Asset-group vocabulary**                                                              | `CLAUDE.md` "Asset-group vocabulary" section · `unified_api_contracts.canonical.crosscutting.market_data_categories` · `venue_axis_asset_group_vocabulary_2026_04_25` plan                                                                                                                                                                                                                                     |
| **Lookahead bias / available_at semantics**                                             | `unified_api_contracts.canonical.crosscutting.availability_semantics` · `unified-trading-library/.../availability_stamping.py` · `codex/02-data/availability-manifest-and-data-status.md` § available_at · `codex/POST_PLAN_REALITY_2026_05_06.md` Principle 5 · `CLAUDE.md` "available_at is per-row" section                                                                                                 |

**Agent rule.** Before merging any change in scope of one of the rows above:

1. The agent's PR description must list the docs read at the start (the "doc-first" check).
2. The commit must touch **all** the listed SSOTs in the relevant row, or explicitly state in the PR description why a
   given SSOT is unaffected.
3. Cross-reference: the corresponding sub-plan in `plans/active/` must agree with the doc — if they disagree, update the
   plan first.

Drift between any of (codex doc, sub-plan, code) is a review-blocking failure.

---

## Plan ↔ Doc ↔ Code drift audit

This is the deliverable that ties the audit to action. For each high-leverage change area, flag whether the codex SSOT,
the corresponding sub-plan, and the code agree. **Items marked ⚠ are pre-existing drift to resolve as part of this
plan, before agents start writing code in the affected area.**

| Area                                                            | Codex SSOT                                                                                                                                  | Sub-plans                                                                                                                                                        | Drift status                                                                     | Resolve via                                                                                                            |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Manifest schema (v6)                                            | `02-data/availability-manifest-and-data-status.md` (current)                                                                                | `manifest_schema_v6_quote_margin_combo_2026_04_23`, `availability_manifest_v4_and_data_status_2026_04_13`                                                        | ⚠ Mixed v4/v5/v6 references in some plans; codex post-2026-05-06 is canonical   | Mark older plans superseded; doc clearly states v6 + v4/v5 hive-key fallback                                           |
| Shard granularity propagation                                   | `02-data/availability-manifest-and-data-status.md` (multi-axis correction post-2026-05-06)                                                  | `shard_granularity_ssot_propagation_2026_05_06.HANDOVER`, `writegate_honest_coverage_endtoend_2026_05_06`, `data_status_multi_axis_shard_propagation_2026_05_06` | ⚠ 3 simultaneous in-flight plans on the same surface                            | Designate HANDOVER as the SSOT; other two reference it explicitly                                                      |
| Cloud-agnostic VM/build                                         | `04-architecture/cloud-agnostic-migration.md`                                                                                               | (no active plan — work-stream D is the new one)                                                                                                                  | ⚠ Doc partially describes target; VM launchers are GCP-only in code             | Add VM-launcher parity appendix to the doc; new plan for AWS launchers                                                 |
| Live-mode services (PBM, R&E, P&L attr, alerting, B-vs-L recon) | Mostly covered by `04-architecture/alerting-batch-live.md`, `autonomous-recovery-matrix.md`, `09-strategy/cross-cutting/pnl-attribution.md` | ❌ **No active plan for any of them**                                                                                                                            | Open the 5 new plans (work-stream E) before writing code                         |
| Custody (Copper + CEFFU)                                        | `04-architecture/copper-custody-integration.md`, `custody-providers.md`, `wallet-hierarchy-and-capital-flow.md`                             | (no active plan; CEFFU not in codex)                                                                                                                             | ⚠ CEFFU has no codex doc; integration unwritten                                 | Add CEFFU codex doc + plan as part of work-stream E                                                                    |
| Strategy v2 finalization                                        | `09-strategy/strategy-summary.md`, `architecture-v2/`                                                                                       | `strategy_architecture_v2_finalization_2026_04_19`, `strategy_architecture_v2_phase3_11_handoff_2026_04_17`                                                      | ⚠ Two overlapping plans                                                         | Designate one as authoritative                                                                                         |
| DART / research-service                                         | `09-strategy/cross-cutting/operational-modes-matrix.md` (operational modes)                                                                 | `dart_ui_strategy_filtering_and_onboarding_2026_04_24`                                                                                                           | ⚠ research-service has 0 repo, only PNG mockups; manual-trade lane not in codex | Add `04-architecture/research-service-and-dart-integration.md`; extend operational-modes-matrix with manual-trade lane |
| ML experiment lifecycle                                         | `02-data/data-lineage-MTDS-features-ml.md` (partial)                                                                                        | `ml_pipeline_revolution_2026_04_11`, `consolidated_ml_advanced_pipeline_2026_04_15`, `sp500_ml_readiness_master_2026_05_05`                                      | ⚠ No dedicated SSOT for ML job_id lifecycle (separate from data manifest)       | Add `04-architecture/ml-experiment-lifecycle.md` (work-stream F)                                                       |
| Live observability / log streaming                              | `03-observability/lifecycle-events.md`, `coordination-events.md`                                                                            | (no active plan for GCS event-tail endpoint)                                                                                                                     | ⚠ Doc defines events; deployment-api endpoint to consume them doesn't exist     | Build endpoint as part of work-stream A; doc stays current                                                             |

**Audit guideline going forward.** Whenever an agent touches a row in this table, the PR includes a one-line "drift
status: resolved / unchanged / new-drift" note in the description. New drift = a new row gets added here.

---

## Audit — sub-plan conflicts, overlaps, stale references

Surface-level scan of the 175 active sub-plans. Flagged items the master plan should resolve before agents start:

1. **Shard-granularity propagation** is in flight via three plans simultaneously:
   `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`, `writegate_honest_coverage_endtoend_2026_05_06`,
   `data_status_multi_axis_shard_propagation_2026_05_06`. Master plan needs to confirm one is the SSOT and the other two
   reference it.
2. **Manifest schema versioning** — codex says v6 (`manifest_schema_v6_quote_margin_combo_2026_04_23`), some plans still
   reference v4/v5. Memory note: writers ship v6 columns; readers fall back to v5/v4 hive-key. Confirm there is no v7 in
   flight.
3. **Sports phantom recovery vs honest-coverage** — `sports_phantom_fixtures_recovery_2026_05_06` (in-flight) blocks
   `features_sports_honest_coverage_2026_05_05` Phase 4-7. Master plan needs to confirm sequencing so VMs don't
   conflict.
4. **DeFi pipeline extension followups** — `defi_pipeline_extension_followups_2026_05_03` shows "complete" in the
   inventory but the leveraged-funding-arb archetype may still depend on calculator closeouts. Verify before assuming
   complete.
5. **Cloud-agnostic** is half-done: `_code_builds_aws.py` exists in deployment-api, `buildspec.aws.yaml` exists, but
   `deployment-service/scripts/vm/` is GCP-only. Codex `cloud-agnostic-migration.md` exists but needs a "VM launcher
   parity" appendix.
6. **research-service** has 0 repo and 10+ DART PNG mockups in workspace root. No active plan claims the build. Decision
   needed (work-stream C).
7. **Strategy v2 finalization** (`strategy_architecture_v2_finalization_2026_04_19`) and
   `strategy_architecture_v2_phase3_11_handoff_2026_04_17` overlap. Confirm one is authoritative.
8. **Live-mode services** (`position-balance-monitor-service`, `risk-and-exposure-service`, `pnl-attribution-service`,
   `alerting-service`, `batch-live-reconciliation-service`) have no active plan tagged for the May 23 cutover. **This is
   the biggest sub-plan gap.**

---

## Q&A — resolved (✓) and outstanding (?)

1. ✓ **Lead DeFi archetypes — both `carry_staked_basis` (ultimate priority) AND `leveraged_funding_arb` (cross-venue
   funding spread) by May 23.** Recursive LST staking is part of the carry_staked_basis archetype. Linked plans:
   `carry_staked_basis_structure_axis_2026_05_04`, `defi_pipeline_extension_2026_05_01`,
   `leveraged_leg_controller_2026_05_01`.
2. ✓ **CeFi/DeFi perp venue scope — six venues live: Bybit, Deribit, Binance, OKX, Hyperliquid, Aster.** Hyperliquid +
   Aster are DeFi perp DEXs but live alongside the CeFi venues. CEFFU manual handoff acceptable for Binance flows on
   May 23.
3. ✓ **Custody scope — Copper wired for DeFi side; CEFFU manual for Binance side acceptable.** Codex SSOT exists for
   Copper; CEFFU doc is a gap (work-stream F).
4. ✓ **AWS proof scope — full cloud-parity proof:** (a) cost analysis of GCS data → estimate AWS migration cost; (b)
   migrate only DeFi-relevant data (not full corpus); (c) data-status working on AWS; (d) backfill on AWS with `--force`
   (proves batch deployment side); (e) backtest examples runnable on AWS; (f) ML strategy examples runnable on AWS; (g)
   **live trading deployment + monitoring on AWS** so the team can seamlessly switch any deployment between AWS-live /
   AWS-batch / GCP-live / GCP-batch. Reduces, but does not eliminate, the May 23 risk surface — see _Risk register_
   below.
5. ? **Manual-trade gating duration.** How many days of DART-driven manual trades before flipping to automation?
   Default: **3 days manual → 7 days automated**, with kill-switch monitoring throughout. Resolve before May 18.
6. ? **research-service repo decision.** Separate repo or fold into deployment-api? Default: **fold into
   deployment-api** unless scope grows. Resolve in Week 1.
7. ? **ML ladder targets per asset group by May 23.** Prediction → features-only, sports → ML, TradFi → ML, CeFi → ML,
   DeFi → no ML (rules-based). Default for May 23: prediction features done; sports/TradFi/CeFi ML pipelines _running_
   on representative sample (not necessarily _deployed_ in production). Confirm "running" vs "ready-to-run".
8. ? **Plan location.** Default: PM `plans/active/master_to_live_defi_2026_05_23.plan.md` (sub-plan) **and**
   `codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md` (audit / SSOT companion), with the audit doc cross-linked
   from `CLAUDE.md` so it's loaded into agent context every session.

---

## Risk register (post-Q&A scope expansion)

The answers expanded scope materially. Risks to flag explicitly so they're not silently signed off:

| Risk                                                    | Likelihood | Impact                                                                                       | Mitigation                                                                                                                                                                                                             |
| ------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6 perp venues live by May 23 (was 2)                    | High       | Slips one or more archetypes                                                                 | Sequence: Bybit + Hyperliquid first (Week 2 W1), Deribit + Binance + OKX + Aster fast-follow (Week 2 W2). Carry_staked_basis only strictly needs 1 perp venue; leveraged funding arb wants ≥3 for cross-venue spreads. |
| 2 archetypes live by May 23 (was 1)                     | High       | Slips leveraged_funding_arb                                                                  | Carry_staked_basis stays the cutover gate; leveraged_funding_arb can flip from manual-DART to automated within the 7-day window if Week 3 is tight.                                                                    |
| Full AWS cloud parity by May 23                         | High       | Slips AWS or DeFi cutover                                                                    | AWS data migration + batch backfill + data-status earliest (Week 1 W2 → Week 2 W1). AWS live trading proof is "single archetype on smaller capital" — does not need full archetype scale.                              |
| 5 NO-PLAN live-mode services to write + ship            | Medium     | Live trading without circuit breakers / live alerting / batch-vs-live recon = unsafe to flip | Open all 5 plans Day 1 of Week 1 (work-stream E).                                                                                                                                                                      |
| CEFFU integration unwritten                             | Low        | Forces all-manual Binance flows                                                              | Manual is acceptable per Q&A 3; codify in plan + add CEFFU codex doc.                                                                                                                                                  |
| DART manual-trade lane is new code on the critical path | Medium     | Slips Group G on tier-1 strategy / execution                                                 | Build on the strategy-evaluations + VmDeployments tracker patterns already in UTS-UI / deployment-ui — **no greenfield UI**.                                                                                           |

---

## Asset-group readiness ladder (critical-path orientation)

Per user direction: stage each asset_group up to a specific layer by May 23. DeFi must reach "live trading"; the others
stage to a parallel-but-deeper level so post-DeFi archetype launches are quick.

| Asset group    | May 23 target depth                                     | Live perp venues             | Notes                                                                                            |
| -------------- | ------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------ |
| **DeFi**       | **Live trading on real wallet (rules-based, no ML)**    | Hyperliquid, Aster           | 2 archetypes (carry_staked_basis lead + leveraged_funding_arb); LST + lending + perp-DEX legs    |
| **CeFi**       | **Live trading (perp hedge leg) + ML pipeline running** | Bybit, Deribit, Binance, OKX | Hedge for DeFi archetypes today; CeFi-only archetypes (e.g. funding-arb-CeFi-only) ready post-23 |
| **TradFi**     | **ML pipeline running on representative sample**        | n/a (no live)                | Backfill ~99%; ML training on rep sample; no live trading this cycle                             |
| **Sports**     | **ML pipeline running on representative sample**        | n/a (no live)                | Honest-coverage + phantom recovery close-outs land first                                         |
| **Prediction** | **Features pipeline running (no ML this cycle)**        | n/a (no live)                | Polymarket canonical-question-group migration is the gate                                        |

---

## Per-service readiness checklist — 7 groups / 23 items

Status legend: `✓` done · `◐` in flight · `✗` not started · `n/a` not applicable

### Group A — Code health (always-on)

1. **QG pass** — `bash scripts/quality-gates.sh` two-pass clean (full + quickmerge)
2. **Quickmerge** — branch landed `live-defi-rollout` → main via SIT
3. **Semver agent** — `feat:` / `fix:` / `feat!:` triggers version bump

### Group B — Data correctness (always-on)

4. **Smoke test** — representative `(asset_group, data_type, day)` triples produce valid parquet end-to-end
5. **Manifest hookup + cluster validation** — `ManifestWriter.record_{captured,empty,failed}` with
   `expected_root_clusters` + `cluster_extractor` for bundled types (codex
   `02-data/availability-manifest-and-data-status.md`, UTL `61a142b0`)
6. **Upstream validation** — `DependencyError(fail_fast=True)` at boundary; honest absence categories A/B/C; no silent
   placeholder rows (CLAUDE.md "honest absence vs fake placeholders")
7. **UAC/UTL abstraction** — domain types in UAC, runtime utilities in UTL, only service-specific config inline
8. **Schema validation** — parquet schema matches UAC contract per `record_captured` (4-pillar write-gate item 3)

### Group C — Runtime parity (always-on)

9. **Hot reload** — `start_domain_config_reloaders` typed; `ApiKeyReloader` for Secret Manager creds (codex
   `06-coding-standards/config-reloader-pattern.md`)
10. **Batch = live** — same code path; only fill source differs (codex `04-architecture/batch-live-pipeline.md`,
    `batch-live-symmetry.md`)
11. **AWS + GCP parity** — both VM launch paths green; `CLOUD_PROVIDER` toggle works end-to-end (codex
    `04-architecture/cloud-agnostic-migration.md`)

### Group D — Coverage & shard (always-on, data-producing services)

12. **Data status accurate** — deployment-UI rollup matches on-disk truth-set; canonical shard axis per asset-group
13. **Shard granularity correct** — matches codex `02-data/availability-manifest-and-data-status.md` per-asset-group
    matrix
14. **Full-window backfill** — ≥2 years of representative history captured (per CLAUDE.md "honest absence" + codex
    `02-data/per-category-bucket-layouts.md`); n/a for runtime-only services

### Group E — Operability (always-on)

15. **UTS-UI summary** — service surfaces visible in unified-trading-system-ui where relevant (`/ops/admin/...` route
    exists or is in scope)
16. **Deployment-UI launch + GCS log streaming** — backfill / restart / forward-poll launchable from UI without SSH; VM
    event logs pooled to `gs://{pid}-events/`; tail works without SSH

### Group F — Trading prerequisites (live-only services)

17. **Backtest fidelity** — real gas, real market impact, realistic matching engine for AMM pools / perpetuals / spots /
    transfers / atomic transfers / flash loans; cost+yield to smallest precision (codex
    `04-architecture/backtest-groups.md`, `batch-live-symmetry.md`)
18. **2-year batch backtest run** — completed across config grid; P&L variance per archetype configuration captured so
    the live-trading config is informed, not guessed
19. **Treasury / custody integration** — Copper for DeFi side (codex `04-architecture/copper-custody-integration.md`);
    CEFFU for Binance institutional flow; cross-wallet transfer paths verified
20. **Live testnet replicates prod** — Tenderly fork / forked-mainnet for DeFi; Binance testnet / Bybit testnet for
    CeFi; same config code path, no faked data
21. **Reconciliation suite** — batch-vs-live reconciliation working (codex
    `09-strategy/cross-cutting/pnl-attribution.md` + `batch-live-reconciliation-service`); P&L attribution decomposed
    per source; per-trade reconciliation
22. **Trading guardrails** — circuit breakers configured per archetype; kill switches wired (codex
    `04-architecture/autonomous-recovery-matrix.md`); alerting-service rules cover live data-freshness + P&L deviation +
    position breaches (codex `04-architecture/alerting-batch-live.md`); auto-recovery for known transient failure
    classes

### Group G — Operator UX (live-only)

23. **DART manual-trade gate** — DART terminal in UTS-UI visualizes the strategy archetype end-to-end; operator first
    puts trades on manually → backend executes through the same path as automation → monitor for the gate window → flip
    switch to automation (codex `09-strategy/cross-cutting/operational-modes-matrix.md`)

> Per-service yamls in `codex/10-audit/repos/<service>.yaml` get extended to track items 4–23. Items 1–3 already in the
> existing repo readiness yaml are inherited.

---

## Service readiness matrix — current snapshot

Tier-1 services — every item must be ✓ by May 23. Group-level rollup (full 23-item detail in per-service yamls).

| Service                           | A·Code | B·Data | C·Runtime | D·Coverage | E·Ops | F·Trading | G·UX | Linked plans                                                                                                          |
| --------------------------------- | ------ | ------ | --------- | ---------- | ----- | --------- | ---- | --------------------------------------------------------------------------------------------------------------------- |
| instruments-service               | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | instruments_and_market_tick_data_completion_2026_05_01, instruments_service_orchestrator_reliability_fixes_2026_04_21 |
| market-tick-data-service          | ✓      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | market_tick_data_to_100pct_2026_05_05, mtds_canonical_sharding_alignment_2026_03_31                                   |
| market-data-processing-service    | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | data_pipeline_completion_2026_04_18                                                                                   |
| features-onchain-service          | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | consolidated_defi_data_pipeline_2026_04_15, defi_e2e_pipeline_2026_04_30                                              |
| features-volatility-service       | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | feature_dag_uac_ssot_and_features_coverage_2026_05_06                                                                 |
| features-cross-instrument-service | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | features_consolidation_and_drilldown_2026_05_06                                                                       |
| ml-training-service               | ◐      | ◐      | ◐         | ◐          | ◐     | n/a       | n/a  | ml_pipeline_revolution_2026_04_11, ml_training_feature_read_perf_2026_05_06                                           |
| ml-inference-service              | ◐      | ◐      | ◐         | n/a        | ◐     | n/a       | n/a  | consolidated_ml_advanced_pipeline_2026_04_15                                                                          |
| strategy-service                  | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | ✗    | strategy_architecture_v2_finalization_2026_04_19, carry_staked_basis_structure_axis_2026_05_04                        |
| execution-service                 | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | ✗    | defi_phase3_infrastructure_2026_03_30, leveraged_leg_controller_2026_05_01                                            |
| position-balance-monitor-service  | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | n/a  | **(NO PLAN — gap)**                                                                                                   |
| risk-and-exposure-service         | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | n/a  | **(NO PLAN — gap)**                                                                                                   |
| pnl-attribution-service           | ◐      | ◐      | ◐         | n/a        | ◐     | ✗         | n/a  | **(NO PLAN — gap)**                                                                                                   |
| alerting-service                  | ✗      | n/a    | ◐         | n/a        | ◐     | ✗         | n/a  | **(NO PLAN — gap)**                                                                                                   |
| batch-live-reconciliation-service | ✗      | n/a    | ◐         | n/a        | ◐     | ✗         | n/a  | **(NO PLAN — gap)**                                                                                                   |
| deployment-api                    | ✓      | n/a    | ◐         | n/a        | ◐     | n/a       | n/a  | deployment_ui_e2e_uat_2026_04_01                                                                                      |
| deployment-service                | ✓      | n/a    | ◐         | n/a        | ◐     | n/a       | n/a  | deployment_service_build_infrastructure_repair_2026_04_22                                                             |
| deployment-ui                     | ✓      | n/a    | n/a       | n/a        | n/a   | n/a       | n/a  | data_status_offline_rollup_2026_05_06, data_status_ui_fixes_2026_05_06                                                |
| unified-trading-system-ui         | ✓      | n/a    | n/a       | n/a        | n/a   | n/a       | n/a  | consolidated_strategy_and_ui_2026_04_15, dart_ui_strategy_filtering_and_onboarding_2026_04_24                         |

> **Action:** Cell values seeded from session memory + sub-plan inventory. Verify via per-service yamls in
> `codex/10-audit/repos/` before relying. Five **(NO PLAN — gap)** rows are the highest-leverage backlog item — every
> one is required for live trading.

### Tier 2 — backfill catch-up + ML readiness ladder (NOT live by May 23)

`features-sports-service` (→ ML), `features-calendar-service` (TradFi → ML), `features-delta-one-service` (TradFi → ML),
`features-commodity-service` (TradFi → ML). Group A–E required by May 23; Group F/G n/a until next archetype lands.

### Tier 3 — post-launch enablement (after May 23)

`client-reporting-api`, `fund-administration-service`, `trading-agent-service`. Out of cutover scope.

---

## New work streams (not yet covered by sub-plans)

### A · deployment-api → standalone orchestration receiver

Today exposes `/api/data-status`, `/api/deployments/{service}/deploy`, `/api/cloud-builds/*`, `/api/vm-deployments`, SSE
`/stream/deploy-events`. Does NOT launch backfills, ML experiments, or strategy backtests as first-class actions.

- [ ] [API] `POST /api/backfill/launch` — `(service, asset_group, venue, data_type, start, end, force)` → fires
      per-asset-group launcher in `deployment-service/scripts/vm/`
- [ ] [API] `POST /api/ml/experiment/launch` — accepts experiment manifest, spins ml-training VM with experiment job_id
- [ ] [API] `POST /api/strategy/backtest/launch` — `(strategy_id, window, archetype_config)` → spins strategy-service
      backtest
- [ ] [API] `POST /api/execution/backtest/launch` — execution-alpha measurement on historical fills
- [ ] [API] `GET /api/vm/events/{vm_name}?since=<ts>` — streams GCS event logs from `gs://{pid}-events/`
- [ ] [API] `GET /api/builds/history` — tarball + Docker-image lineage (branch, commit, build trigger, deployer, target
      service, asset_group, target cloud)
- [ ] [API] AuthN via Firebase token forwarded from UTS-UI / Deployment-UI
- Reference: existing `deployment_api/routes/_code_builds_aws.py` for dual-cloud pattern

### B · Live Deployment UI tab

A new tab/section monitoring **live** trading services. Today deployment-ui is batch-job + data-status console; live
monitoring not covered.

- [ ] [UI] `/ops/live-deployments` route in deployment-ui
- [ ] [UI] Live-services panel — running services in live mode, last STARTED, last DATA_BROADCAST, staleness in seconds
- [ ] [UI] Live alert pane consuming alerting-service feed
- [ ] [UI] Per-service live log tail (deployment-api `/api/vm/events`)
- [ ] [DOC] Codex SSOT at `codex/05-infrastructure/live-deployment-monitoring.md` (currently missing)

### C · UTS-UI ↔ DART terminal — research, backtest, **manual-trade**

Today UTS-UI has strategy-catalogue / strategy-evaluations / strategy-lifecycle-editor. Missing: ML-experiment,
strategy-backtest, execution-backtest launch surfaces, and **the DART manual-trade lane** (visualize the DeFi archetype,
place trades manually through the same backend as automation, monitor before flipping to auto).

- [ ] [DECIDE] research-service repo vs fold into deployment-api (default: fold-in)
- [ ] [UI] `/research/ml-experiments`, `/research/strategy-backtests`, `/research/execution-backtests` tabs
- [ ] [UI] **DART terminal — DeFi archetype visualization + manual trade entry**
  - [ ] Render archetype state (positions, funding, LST yields, hedge basis) in real-time
  - [ ] Manual trade entry → goes through execution-service same path as automation (NOT a side door)
  - [ ] Operator-monitored window before automation flip
  - [ ] Automation toggle gated by checklist Group F + G complete
- [ ] [API] All tabs wired to deployment-api (work-stream A)
- [ ] [UI] Borrow VmDeployments.tsx tracker pattern from deployment-ui
- [ ] [DOC] Codex SSOT at `codex/04-architecture/research-service-and-dart-integration.md`
- [ ] [DOC] Extend `codex/09-strategy/cross-cutting/operational-modes-matrix.md` with the DART manual-trade lane

### D · Cloud-agnostic full-parity proof (data + batch + ML + live + monitoring on AWS)

Per Q&A 4, the AWS proof is **full parity**, not a minimal 2-VM proof. Order of operations matters because data
migration is gated by cost.

**D.1 — Data migration to AWS (sized to DeFi only, NOT full corpus)**

- [ ] [SCRIPT] Cost analysis: GCS storage + egress for DeFi-relevant data → AWS S3 storage + ingress estimate; report in
      `unified-trading-pm/docs/aws-migration-cost-2026-05.md`
- [ ] [SCRIPT] Selective copy of DeFi-relevant manifests + parquet (instruments / MTDS / MDPS / features-onchain) to S3,
      preserving hive layout. **Skip TradFi / Sports / Prediction data — wasteful re-fetch.**
- [ ] [API] Update deployment-api data-status endpoints to be cloud-agnostic — read from GCS or S3 based on
      `CLOUD_PROVIDER`

**D.2 — Batch deployment side proof (AWS)**

- [ ] [SCRIPT] AWS EC2 launcher equivalents alongside `gcloud` launchers — minimum: instruments / MTDS /
      features-onchain in AWS mode
- [ ] [SCRIPT] Run a backfill on AWS with `--force` for a small DeFi window — proves the deployment-side batch path
      works on AWS, not just dataset migration
- [ ] [SCRIPT] Cloud Build dual-provider trigger taking deps tarball + code-from-GitHub (CodeBuild already partial via
      `_code_builds_aws.py`)

**D.3 — Backtest + ML on AWS**

- [ ] [SCRIPT] Run a strategy backtest example on AWS via deployment-api `/api/strategy/backtest/launch` (work-stream A)
      — proves end-to-end batch surface
- [ ] [SCRIPT] Run an ML training example on AWS via deployment-api `/api/ml/experiment/launch` — proves ML side
- [ ] [SCRIPT] Run an execution backtest example on AWS — proves execution-side batch

**D.4 — Live deployment + monitoring on AWS**

- [ ] [SCRIPT] One live archetype instance running on AWS (carry_staked_basis on smaller capital) — proves live trading
      works on AWS-as-deployment-target
- [ ] [UI] Live Deployment UI tab (work-stream B) reads from both GCS and S3 event streams, surfaces both live
      deployments
- [ ] [SCRIPT] Seamless-switch test: pause GCP-live archetype, resume on AWS-live, verify position state preserved via
      custody / position-balance-monitor

**D.5 — Build lineage tab**

- [ ] [API] `/api/builds/history` (work-stream A) returns combined GCP + AWS records
- [ ] [UI] Build-history tab in deployment-ui — branch / commit / image tag / target cloud / deployer / triggered-by
      (tarball vs Claude build vs CI)

**D.6 — Codex updates**

- [ ] [DOC] Augment `codex/04-architecture/cloud-agnostic-migration.md` with VM-launcher parity appendix + the
      data-migration cost-gate principle
- [ ] [DOC] Codex SSOT at `codex/05-infrastructure/cloud-agnostic-build-lineage.md`
- [ ] [DOC] Codex SSOT at `codex/04-architecture/seamless-cloud-switch.md` — preserved-state semantics when migrating a
      live deployment between clouds

### E · Live-mode services (the 5 NO-PLAN gaps)

- [ ] [PLAN] Open `position-balance-monitor-live-mode_2026_05_07.plan.md`
- [ ] [PLAN] Open `risk-and-exposure-live-mode_2026_05_07.plan.md`
- [ ] [PLAN] Open `pnl-attribution-live-mode_2026_05_07.plan.md`
- [ ] [PLAN] Open `alerting-service-live-rules_2026_05_07.plan.md`
- [ ] [PLAN] Open `batch-live-reconciliation-2026_05_07.plan.md`
- All 5 lock to `live-defi-rollout`, all reference checklist Groups F + G

### F · Codex SSOT gaps to fill alongside the work

- [ ] [DOC] `codex/05-infrastructure/live-deployment-monitoring.md` (work-stream B)
- [ ] [DOC] `codex/04-architecture/research-service-and-dart-integration.md` (work-stream C)
- [ ] [DOC] `codex/05-infrastructure/cloud-agnostic-build-lineage.md` (work-stream D)
- [ ] [DOC] `codex/04-architecture/ml-experiment-lifecycle.md` — ML job_id manifest separate from data manifest
- [ ] [DOC] `codex/04-architecture/live-strategy-config-hot-reload.md` — strategy config hot-reload end-to-end for live
      mode
- [ ] [DOC] CEFFU integration page in `codex/04-architecture/` (peer to `copper-custody-integration.md`)

---

## Critical-path DAG (May 6 → May 23)

### Week 1 (May 6–12) · foundations close + tier-1 services pass Groups A–E + AWS migration starts

- [ ] Close shard-granularity propagation (designate one of the 3 plans as the SSOT)
- [ ] Close TradFi MVP residuals (cluster-validation wiring at `record_captured`)
- [ ] Close DeFi data-pipeline blockers (features-onchain LookaheadBiasError + lending_rates write-gate)
- [ ] Close sports phantom recovery — frees VM-quota for DeFi + AWS work
- [ ] **Open the 5 live-mode plans** (position-balance-monitor, risk-and-exposure, pnl-attribution, alerting-service,
      batch-live-reconciliation) — work-stream E
- [ ] Ship deployment-api `/api/backfill/launch` + `/api/vm/events` (work-stream A)
- [ ] Decide research-service repo question (work-stream C)
- [ ] AWS migration cost analysis (work-stream D.1) → user signs off scope
- [ ] Sports / TradFi / CeFi ML pipelines reach "running on representative sample" milestone (parallel — tier 2 ladder)
- [ ] Hyperliquid + Aster perp DEX integration: instrument registry + market-data live (these don't have CEFFU
      equivalents — direct on-chain)

### Week 2 (May 13–19) · live wiring + cloud parity + Groups F/G

- [ ] `carry_staked_basis` runs end-to-end in batch with `always_fill` + matching-engine fills (Group F item 17)
- [ ] `leveraged_funding_arb` runs end-to-end in batch — cross-venue funding spread across 6 perp venues
- [ ] 2-year P&L variance batch run completed across config grid for both archetypes (Group F item 18)
- [ ] Execution-service connectors validated on testnet:
  - DeFi: Aave / Uniswap / Lido (carry_staked_basis); Hyperliquid + Aster (leveraged_funding_arb on-chain leg)
  - CeFi: Bybit perp + Deribit options/perp + Binance perp + OKX perp (the four CeFi venues)
- [ ] Position-balance-monitor + risk-and-exposure + pnl-attribution: live mode validated
- [ ] Alerting-service: live rules fired on synthetic violations
- [ ] Live Deployment UI tab shipped (work-stream B)
- [ ] **AWS data migration completed** (DeFi-only, work-stream D.1) — data status works on both clouds
- [ ] **AWS batch backfill `--force`** runs on a small DeFi window (work-stream D.2)
- [ ] **AWS backtest + ML examples** run via deployment-api (work-stream D.3)
- [ ] DART terminal in UTS-UI: archetype visualization + manual trade entry (work-stream C)
- [ ] Treasury: Copper integration validated; CEFFU manual handoff documented

### Week 3 (May 20–23) · cutover (live trading + AWS live deployment)

- [ ] Real wallet funded testnet → mainnet
- [ ] DART manual-trade window: 3 days operator-monitored on `carry_staked_basis`
- [ ] Automation flip on `carry_staked_basis` → 7-day continuous run begins (extends past May 23 into May 30)
- [ ] `leveraged_funding_arb` enters DART manual-trade window (lags carry_staked_basis by ~2 days)
- [ ] **AWS live archetype** running in parallel — one carry_staked_basis instance on smaller capital deployed to AWS
      (work-stream D.4)
- [ ] **Seamless-switch test** between GCP-live ↔ AWS-live (work-stream D.4)
- [ ] Build-history tab in deployment-ui shipped (work-stream D.5)
- [ ] Batch-vs-live reconciliation matches within tolerance per archetype config (Group F item 21)

---

## Tracking surface

- [x] Plan promoted to `unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.plan.md` (this file)
- [x] Audit companion at `unified-trading-pm/codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md` (pointer + drift
      table mirror)
- [x] Referenced from `CLAUDE.md` so every agent session loads it
- [ ] Per-service yamls at `codex/10-audit/repos/<service>.yaml` extended with the 7-group / 23-item structure for
      tier-1 services
- [ ] Update cadence: Tier-1 readiness rollup refreshed by EOD daily; critical-path DAG checked at start of each week
- No duplication: sub-plans in `plans/active/` remain authoritative; this plan only references and orchestrates

---

## Verification (end-to-end, the 23-item checklist instantiated)

**DeFi live (the headline goal)**

- [ ] `carry_staked_basis` cycle on real wallet (testnet → mainnet) via DART manual-trade lane → backend execution →
      automation flip → ≥7-day continuous run; P&L matches batch sim within configured bps tolerance per Group F item 21
- [ ] `leveraged_funding_arb` running across ≥3 perp venues with cross-venue funding spread captured

**Perp venue coverage**

- [ ] All 6 venues live: Bybit, Deribit, Binance, OKX, Hyperliquid, Aster — one trade each verified via deployment-UI

**Observability + guardrails**

- [ ] Tail VM event logs from deployment-UI without SSH for 24h on a live forward-poll VM
- [ ] Live alerting fires on synthetic data-freshness, P&L deviation, and position-breach violations injected via test
      fixtures
- [ ] Kill switch fires on synthetic risk-breach trigger

**Cloud parity (work-stream D)**

- [ ] DeFi-relevant data migrated to AWS S3 (manifest + parquet) with same shard layout as GCS
- [ ] AWS data status query works in deployment-UI and matches GCS truth
- [ ] AWS batch backfill `--force` produces parquet end-to-end
- [ ] AWS strategy backtest + ML training + execution backtest examples run via deployment-api
- [ ] AWS live carry_staked_basis instance running on smaller capital
- [ ] Seamless-switch (GCP-live → AWS-live → back) preserves position state via custody / position-balance-monitor

**Readiness rollup**

- [ ] All Tier-1 services pass 23/23 readiness checklist (or have explicit n/a justified) — verified per
      `codex/10-audit/repos/<service>.yaml`
- [ ] All 9 drift-audit rows resolved (none remaining `⚠`)
- [ ] `codex/00-SSOT-INDEX.md` updated to reference all new SSOT docs (work-streams D.6 + F)
- [ ] `CLAUDE.md` cross-references this master plan in a new "Master Plan" section

---

## Critical files (read first, in this order)

| Purpose                                           | File                                                                                                                                     |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Codex master index                                | `unified-trading-pm/codex/00-SSOT-INDEX.md`                                                                                              |
| Cross-cutting principles (read before any change) | `unified-trading-pm/codex/POST_PLAN_REALITY_2026_05_06.md`                                                                               |
| Existing service-readiness SSOT                   | `unified-trading-pm/codex/10-audit/REPO_READINESS_CHECKLIST.yaml`, `_checklist-template-enhanced.yaml`, `repos/<service>.yaml`           |
| Batch=live design SSOT                            | `unified-trading-pm/codex/04-architecture/batch-live-pipeline.md`, `batch-live-symmetry.md`, `backtest-groups.md`                        |
| Shard granularity per asset-group                 | `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`                                                              |
| UI surface SSOT                                   | `unified-trading-pm/codex/05-infrastructure/UI-FUNCTIONALITY-REQUIREMENTS.md`                                                            |
| Tarball deployment SSOT                           | `unified-trading-pm/codex/05-infrastructure/vm-tarball-deployment.md`                                                                    |
| Cloud-agnostic SSOT                               | `unified-trading-pm/codex/04-architecture/cloud-agnostic-migration.md`                                                                   |
| Lifecycle events SSOT                             | `unified-trading-pm/codex/03-observability/lifecycle-events.md`                                                                          |
| Strategy archetypes SSOT                          | `unified-trading-pm/codex/09-strategy/strategy-summary.md`                                                                               |
| Strategy onboarding                               | `unified-trading-pm/codex/09-strategy/cross-cutting/onboarding-checklist.md`                                                             |
| Operational modes (manual / paper / automated)    | `unified-trading-pm/codex/09-strategy/cross-cutting/operational-modes-matrix.md`                                                         |
| P&L attribution                                   | `unified-trading-pm/codex/09-strategy/cross-cutting/pnl-attribution.md`                                                                  |
| Alerting (batch + live)                           | `unified-trading-pm/codex/04-architecture/alerting-batch-live.md`                                                                        |
| Auto-recovery / kill switches                     | `unified-trading-pm/codex/04-architecture/autonomous-recovery-matrix.md`                                                                 |
| Custody (Copper)                                  | `unified-trading-pm/codex/04-architecture/copper-custody-integration.md`, `custody-providers.md`, `wallet-hierarchy-and-capital-flow.md` |
| Service control surface                           | `unified-trading-pm/codex/04-architecture/service-control-surface.md`                                                                    |
| Existing deployment-API                           | `deployment-api/deployment_api/routes/`                                                                                                  |
| Existing deployment-UI                            | `deployment-ui/src/pages/`                                                                                                               |
| Existing UTS-UI admin                             | `unified-trading-system-ui/app/(ops)/admin/`                                                                                             |
| Cross-cloud partial AWS                           | `deployment-api/deployment_api/routes/_code_builds_aws.py`, `deployment-service/buildspec.aws.yaml`                                      |

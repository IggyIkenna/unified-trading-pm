---
doc_type: plan
title: Ikenna ↔ Harsh work split — 2026-05-07 → 2026-05-11 (5-day cycle to Week 2)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, execution-service, features-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-07
type: coordination-doc
deadline: 2026-05-23 (live DeFi)
horizon: 5-day cycle (D1–D5); Week 2 plan re-derived at EOD D5
companion_to: plans/active/_AUDIT_2026_05_07_dependency_graph.md
locked_by: live-defi-rollout
locked_since: 2026-05-07
---

## Deferred work — migrated to:

**None** — successor: not applicable. Verified 2026-07-21 (batch-5 archived-plan discipline triage): this is a personal
day-splitting coordination doc between two operators (`type: coordination-doc`, `nature: record`), not a standalone
technical plan. Every substantive item it references (writegate, alerting, aws_migration, deploy_missing_auto_launch,
launcher_scripts_consolidation, DART Playwright, cefi VM babysitting) is tracked and completed in its own proper
plan-of-record, all now archived complete or absorbed into a later closed epic (cefi_master →
`cefi_consolidated_closeout_2026_07_18.md`). Nothing here is untracked.

# Ikenna ↔ Harsh work split — 5-day cycle (2026-05-07 → 2026-05-11)

> **Companion to**: [`_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md). Read that for
> per-plan status, dependency graph, critical path, and operator action items. **This doc is the per-colleague
> assignment**: who owns what, in what order, with which sync gates. Each item is a checkbox so the doc doubles as a
> live progress tracker — flip in-place as work ships.

## Why this doc exists

- 16 days to live-DeFi deadline; 26 active plans post-2026-05-07 audit cleanup (was 25 → 18 via consolidations A/B/C/D,
  then +8 from ai/→active/ promotion `169451b6`).
- Both colleagues run multiple parallel agents per session (Cursor + Claude Code), so each effectively has 3-5×
  amplification — but file-level collisions clobber each other's work (reference incidents PM@961980db, PM@611b9501).
- Without an explicit split, both agents converge on the highest-leverage critical-path files (UAC alerting, writegate,
  deployment-api) and step on each other.

## Split principle

**Ikenna** owns work requiring (a) cross-cutting design decisions across 3+ repos, (b) trading-judgment calls, (c)
governance / ratchet thinking, or (d) coordination across the 26-plan surface. **Harsh** owns work with well-defined
inputs/outputs: implement-from-spec, run-script-and-verify, scoped-Pydantic-types, single-repo edits, test execution.
Both follow CLAUDE.md "commit + push per shippable unit" + "plan-checkbox flip in same logical unit as code" hard rules.

## How to use this doc

- Flip the `- [ ]` to `- [x]` as you ship each item, with a brief evidence stamp (`<repo>@<sha>` or `verified-via X`)
  appended. Commit the flip in the same PM-repo commit as a `plan(work_split): <colleague> D<n> <item>` message.
- If an item is half-shipped at EOD, leave it `- [ ]` and add a `**partial:**` sub-bullet noting state.
- If reality forces a re-shuffle (item moves between colleagues), flip the original to `- [-]` (skipped/moved) and
  re-add under the new owner.

---

## IKENNA — nuanced, judgment-heavy, cross-cutting

### Day 1 — 2026-05-07

- [x] [DESIGN] P0. Author UAC `AlertCode` taxonomy (StrEnum + threshold dataclass + severity-vs-alert-code separation).
      Plan: [`alerting_service_live_rules_2026_05_07`](alerting_service_live_rules_2026_05_07.md) Phase 1. Repo: UAC.
      Why nuanced: closed-set philosophy decisions; sets workspace-wide alert vocabulary for years; codex SSOTs at
      [`/codex/14-playbooks/alerting/alert-code-taxonomy.md`](/codex/14-playbooks/alerting/alert-code-taxonomy.md)
      expect this StrEnum to land here. **DONE 2026-05-07 (Agent 1)** — UAC@`d00326d` shipped + alerting plan Phase 1
      checkbox flips per PM@`7624ab21`. Phase 2-9 of alerting plan (KillSwitchBus rule wiring + consumer wiring)
      pending.
- [x] [DESIGN] P0. writegate Phase 4.A: deployment-api typed-error rendering (UTL classifier → `error_reason` API field
      → UI typed badge). Plan:
      [`writegate_honest_coverage_endtoend_2026_05_06`](writegate_honest_coverage_endtoend_2026_05_06.md) Phase 4.A.
      Repos: UTL + deployment-api + deployment-ui. Why nuanced: cross-cutting across 3 repos; per-asset-group
      consumer-class judgments per
      [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md).
      **DONE 2026-05-07 (Agent 2)** — deployment-ui@`a7384a0` (TypedReasonBadges + FailurePillarStack components + 24
      unit tests + client.ts TurboSubDimension extension) + deployment-ui@`621f0b3` (wire components into DataStatusTab
      venue summary line). Closed-set drift guard test fails CI on \_FAILURE_PILLAR_KEYS / \_EMPTY_REASON_KEYS drift.
      Phase 4.B.1 + 4.B.2 + 4.A.3 leaf-stats endpoint flips per PM@`0c2a0cca` / `21f8a277` / `fa9b5f43`.

### Day 2 — 2026-05-08

- [x] [INFRA+COORDINATION] P0. **Expected-universe enumerator Phase 3.D.4** — execute the carry-over handoff from D1 (PM
      Claude session 2026-05-07; commits PM `c1711e34` / `372e23aa` + instruments-service `8e404c8`). The script
      [`enumerate_expected_universe.py`](../../../instruments-service/scripts/enumerate_expected_universe.py) is
      shipped + smoke-tested (TradFi/DeFi FULL, Sports PARTIAL, CeFi/Prediction stubs); 4 phases remain: (1) build
      `deployment-service/scripts/vm/launch-expected-universe-enumerator-vm.sh` (mirror
      `launch-defi-phantom-recon-vm.sh`); (2) update `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` (add
      `expected-universe-enum-`) + relaunch watchdog; (3) refresh tarballs (`create-code-tarballs.sh --all`); (4)
      sequential VM launches (TradFi → DeFi → Sports → CeFi stub → Prediction stub) with no-fire-and-forget event
      verification (90s STARTED + 10-15min progress + ENUMERATOR_COMPLETED); scan-only first, operator-review CSV, then
      `--apply-write`; annotate 6+ active plans with VM RUNNING → VM COMPLETED markers (writegate, drilldown,
      master-defi, defi_master, 2 issue files, canonicalisation plan). **Full handoff**:
      [`_HANDOFF_expected_universe_enumerator_2026_05_07.md`](_HANDOFF_expected_universe_enumerator_2026_05_07.md). Why
      nuanced: closes the rollup-vs-drilldown denominator divergence (codex SSOT
      [`availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) §
      "Rollup-vs-drilldown denominator divergence (codified 2026-05-07)"); cross-cutting across instruments-service +
      deployment-service + 6+ PM plans + codex; affects what every other agent sees in the data-status panel. Cost:
      ~$2-5 GCE + ~2-3hr operator time. Repos: deployment-service + instruments-service + PM. **DONE 2026-05-07
      (Agent 3)** — `--apply-write` complete across all 5 asset_groups: 1,455,901 rows landed in per-VM manifest shards
      (tradfi 35,033 + sports 13,176 + cefi 119,152 + prediction 2,280 + defi 1,286,260) per PM@`79e47874`. CeFi +
      Prediction now real impl per UAC@`ac218dc` + instruments-service@`d1c9928` (no longer stubs). Consolidator P0
      ArrowTypeError RESOLVED via instruments-service@`a936a28` + 4 in-place shard fixes per PM@`341bb285`. Banners on
      6+ active plans added then removed per PM@`dae6d40d` + PM@`5ae70bf1`. Phase 3.D.5 Wave 1+2.M migration COMPLETE
      with 3,114,843 rows flipped across all 5 asset_groups per PM@`a541f51e` + `937df64b`.
- [ ] [DEEP] P0. writegate Phase 2.A residual: `batch_workers` path B/C migration + MDPS cluster-coverage wiring +
      delete `_write_manifest_records`. Plan: writegate Phase 2.A. Repos: MDPS + UTL. Why nuanced: per-adapter judgment
      about empty-vs-failed three-category model; partial-bundle cluster-validation correctness for the 11-cluster
      ES.OPT surface.
- [x] [COORDINATION] P1. Audit the 2 new umbrellas + master Group F+G fold-in: phase ordering reads as one plan, not 4
      stitched-together plans; critical-path callouts in
      [`ml_and_features_master_2026_05_07`](ml_and_features_master_2026_05_07.md) +
      [`strategy_and_dart_master_2026_05_07`](strategy_and_dart_master_2026_05_07.md) +
      [`master_to_live_defi_2026_05_23`](master_to_live_defi_2026_05_23.md) Group F. Repo: PM. **DONE 2026-05-07
      (Agent 5)**: ml_and_features_master critical-path § gained explicit upstream sibling-blocker callout naming
      writegate Phase 2.D `available_at` stamping. strategy_and_dart_master critical-path § gained Phase-numbering note
      (1.x archaeology vs dependency order) + fixed ambiguous "Phase 1.9 service-split fold-in" descriptor → "Phase 3-11
      fold-in residuals" + new Coordination-with-sibling-plans § naming ml_and_features / writegate / master /
      defi_master hand-offs. Master Group F+G fold-in (operational-validation extends items 17-22 inline) is
      structurally coherent; service-readiness matrix staleness (9 rows still pointing at archived source plans
      post-umbrella consolidation) is in Item 3 (master refresh) scope, not Item 1.

### Day 3 — 2026-05-09

- [ ] [ARCHITECTURE] P0. alerting Phase 2: KillSwitchBus rule wiring + `CROSS_CLOUD_EGRESS_DETECTED` rule + AAVE
      utilization-spike threshold value (the bps was flagged ambiguous in audit §3 #5). Plan: alerting Phase 2. Repo:
      alerting-service. Why nuanced: kill-switch invariants + threshold-tuning judgment.
- [ ] [GOVERNANCE] P0. writegate Phase 5: workspace QG honest-coverage % gate + per-(asset_group, data_type) ratchet
      schedule. Plan: writegate Phase 5. Repos: UTL + base-service.sh. Codex SSOT to populate:
      [`/codex/02-data/honest_coverage_baseline_2026_05.md`](/codex/02-data/honest_coverage_baseline_2026_05.md)
      (currently a stub).

### Day 4 — 2026-05-10

- [ ] [TRADING] P0. Launch first DeFi backfill VMs (Aave / Uniswap / LST yields / Pyth + Chainlink now ready). Plan:
      [`defi_master_2026_05_07`](defi_master_2026_05_07.md) Fork 1. Repos: MTDS + deployment-service. Why nuanced:
      May-23 priorities + risk of bad backfill choices; first run with the just-shipped Pyth Hermes + Chainlink
      multi-chain paths.
- [ ] [INFRA-DESIGN] P1. aws_migration Phase 2: dual-bucket setup + Storage Transfer Service config + bucket-naming SSOT
      discipline. Plan: [`aws_migration_defi_first_2026_05_07`](aws_migration_defi_first_2026_05_07.md) Phase 2. Repos:
      deployment-service + UCI. Codex SSOT to populate:
      [`/codex/05-infrastructure/cloud-agnostic-script-pattern.md`](/codex/05-infrastructure/cloud-agnostic-script-pattern.md).
- [ ] [COORDINATION] P1. Triage
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      (just promoted) — overlaps with defi_master Fork 1 launch decision; canonicalise venue-collateral matrix BEFORE
      the launch picks chains/protocols.
- [x] [COORDINATION] P2. Triage
      [`session_2026_05_07_data_status_audit_findings`](session_2026_05_07_data_status_audit_findings.md) (just
      promoted) — folds into infra_master or stays standalone? Decision-only, ~30 min. **DONE 2026-05-07 (Agent 5)**:
      STANDALONE. Wrapper-tracker spans 5 owner plans (sports / predictions / defi / manifest_migration /
      infrastructure); folding into infra_master mis-attributes most findings (only B.2 + C.13 belong there) + loses
      cross-master rollup visibility. Tracker is lifecycle-bounded (self-archives when all referenced master-plan todos
      go green). Triage decision recorded at top of the plan body.

### Day 5 — 2026-05-11

- [ ] [TRADING+INTEGRATION] P0. carry_staked_basis paper-trade smoke (Solana Pyth + jitoSOL/mSOL hedging) — verify
      execution-service + strategy-service + position-balance-monitor-service interactions. Plan: defi_master. Repos:
      execution-service + strategy-service + position-balance-monitor-service. Why nuanced: multi-repo round-trip with
      real custody adapter calls.
- [x] [COORDINATION] P0. Master plan refresh: reflect Day 1-4 progress in critical-path § + flip Group F/G checkboxes
      for what shipped this cycle. Plan: master. Repo: PM. **DONE 2026-05-07 (Agent 5)**: service-readiness matrix
      refreshed (10 rows pointing at archived source plans → umbrella plans post-2026-05-07 consolidation:
      ml_and_features_master / strategy_and_dart_master / defi_master / alerting_service_live_rules /
      deployment_api_work_stream_a). Action paragraph below matrix updated with refresh notes (a)-(f). New "Afternoon
      shipments 2026-05-07" sub-section added under "Recent shipments" capturing writegate Phase 4.A typed-error
      rendering (Agent 2) + Phase 3.D.4 `--apply-write` complete (1.4M rows) + Phase 3.D.5 Wave 1+2.M migration COMPLETE
      (3.1M rows) + UAC AlertCode Phase 1 (Agent 1) + 4-state capture_status SSOT + Agent-5 Items 1+2.

---

## HARSH — mechanical, well-defined, parallel-safe

### Day 1 — 2026-05-07

- [ ] [OPS] P0. Babysit 24 cefi VMs (ETA 05-08/09): event-progression checks (`STARTED → PROCESSING → STOPPED`), kill
      zombies via `VM_PREFIX_TO_BUCKET` registry; do **not** launch new cefi work. Plan:
      [`cefi_master_2026_05_07`](cefi_master_2026_05_07.md). Monitor only. **In-flight 2026-05-07 14:00 UTC**: 37 cefi
      VMs (bitfinex/bitget/kraken futures+spot 2020-2026) running in asia-northeast1-c. Sample-checked 3 VMs: STARTED +
      PROCESSING_STARTED + PROCESSING_COMPLETED events flowing, ~4 min/date pace. **Concerns**: (a) PROCESSING_COMPLETED
      events lack `rows_captured` field — violates writegate rule "adapters MUST emit row counts so silent-zero is
      detectable from event stream"; (b) frequent `PROCESS_CPU_SATURATED` events on e2-highmem-2 (2 vCPU) suggest
      workload sized too tight for instance type. **Next**: data-quality spot-check via per-VM manifest shard at T+30min
      after first VM hits STOPPED.
- [x] [SCRIPT] P0. Implement UAC types for backfill launch (`BackfillLaunchRequest` / `BackfillLaunchResult` /
      `VMLifecycleEvent` / `VMEventListResult` / `BackfillLaunchTaskKind` StrEnum). Plan:
      [`deployment_api_work_stream_a_2026_05_07`](deployment_api_work_stream_a_2026_05_07.md) Phase 1. Repo: UAC.
      (UAC@`a70b3f6` — Ikenna shipped Phase 1 a day early; 5 models + 23-value StrEnum with per-source sports +
      per-asset_group forward-poll variants; 15 unit tests green via `.venv/bin/python -m pytest`.)

### Day 2 — 2026-05-08

- [x] [SCRIPT] P0. Implement UAC `feature_group → required_inputs` SSOT (1-day pure-win; gates ml/features Phase 2
  - ML downstream). Plan: [`ml_and_features_master_2026_05_07`](ml_and_features_master_2026_05_07.md) Phase 1A. Repo:
    UAC. **DONE 2026-05-07** — Phase 1A largely shipped (4 commits across UAC + UTL): UAC@`4a25b07` (32 feature_groups +
    5-service registry + 6 onchain coverage_starts + 15 tests) + UAC@`2f40c9d` (AVAILABILITY_AT_SEMANTICS
    defi-vocabulary Half 1) + UAC@`7a3299a` (Half 2 — 8 of 10 deferred onchain feature_groups lifted) + UTL@`d7902f6`
    (`ManifestFreshnessCache` + 17 tests) + UTL@`4354276c` (`assert_no_lookahead_for_feature_group` helper + 9 tests).
    **REMAINING**: sports vocabulary alignment Phase 1A.3 (operator decision pending — gates features-sports consumer
    migration); 8-service consumer wires (Phase 2A).
- [ ] [SCRIPT] P1. Hook `features_sports_reconcile_available_at.py` (already shipped per
      `features-sports-service@f123069`) into per-source backfill VM exit-step. Plan:
      [`sports_master_2026_05_07`](sports_master_2026_05_07.md). Repos: features-sports-service + deployment-service.

### Day 3 — 2026-05-09

- [ ] [SCRIPT] P0. Implement `POST /api/backfill/launch` + `GET /api/vm/events` handlers (against UAC types from D1).
      Plan: deployment_api_work_stream_a Phase 2. Repo: deployment-api.
- [x] [SCRIPT] P1. UAC canonical_question_group SSOT (`HOURLY` / `DAILY` / `ELECTION` Polymarket+Kalshi groupings).
      Plan: [`predictions_master_2026_05_07`](predictions_master_2026_05_07.md) Phase 1. Repo: UAC. **DONE 2026-05-07**
      — Phase 1A scaffolding complete (predictions audit confirmed 14/37 done, 38% progress): UAC@`5f76bd4` (classifier
      stability hash design) + UAC@`af2bc9b` (canonical-question-group SSOT + lifecycle wrapper modules) + UAC@`58cc5f8`
      (Polymarket lifecycle aliases + edge-case regression tests) + UAC@`bb24aba` (DATA_TYPE_TO_CLUSTER_REGISTRY
      seeded + PREDICTION_GROUPS empty registry) + UAC@`a901e91` (vault-venue canonical names + Polymarket CLOB
      coverage). **REMAINING**: Phase 1 lifecycle ingestion (instruments-service writer + orchestrator shard-atom emit +
      integration tests); Phase 2 adapter migration (Polymarket + Kalshi lifecycle gating; UMI tick provider
      replacement; legacy writer purge); Phase 3 reader/feature/strategy.

### Day 4 — 2026-05-10

- [ ] [SCRIPT] P0. Cross-asset manifest rescan after cefi VM drain (run `reconcile_phantom_manifest_rows_all.py` per
      asset_group; merge per-VM shards). Plan:
      [`manifest_migration_master_2026_05_07`](manifest_migration_master_2026_05_07.md) Stage 4. Repo:
      instruments-service scripts. **Hard prerequisite**: cefi VMs drained (D1 D2 ops).
- [ ] [SCRIPT] P1. TradFi MDPS post-drain: ES.OPT 11-cluster validation rerun if cluster-coverage gate flagged any
      partial bundles. Plan: [`tradfi_master_2026_05_07`](tradfi_master_2026_05_07.md). Repo: MDPS.
- [ ] [SCRIPT] P2. Migrate first batch of ad-hoc VM launchers into `deployment-service/scripts/vm/` (target: 10 of 30
      launchers in this cycle; rest carry over post-May-23). Plan:
      [`launcher_scripts_consolidation_into_deployment_service_2026_05_07`](launcher_scripts_consolidation_into_deployment_service_2026_05_07.md).
      Repo: deployment-service.

### Day 5 — 2026-05-11

- [ ] [SCRIPT] P0. aws_migration Phase 0/1 smoke: `CLOUD_PROVIDER=aws instruments-service --health-check` +
      `setup-defi-buckets.sh` dry-run. Plan: aws_migration_defi_first Phase 0-1. Repos: deployment-service +
      instruments-service. **Phase 0 DONE 2026-05-07** — operator credit confirmed ≥$40k over 11 months / ~$3,636/mo
      sustainable / no service / region / account locks expected; cost analysis shipped at
      `/codex/05-infrastructure/aws_migration_cost_analysis_2026_05_07.md`; dual-cloud-active steady state decision
      logged in audit doc § "Decisions taken in-session". **Phase 1 smoke PENDING** —
      `CLOUD_PROVIDER=aws     instruments-service --health-check` + bucket-name parity audit + `setup-defi-buckets.sh`
      dry-run all need execution by operator.
- [ ] [TEST] P0. DART 6-persona Playwright matrix verification on manual-trade flow. Plan:
      [`strategy_and_dart_master_2026_05_07`](strategy_and_dart_master_2026_05_07.md) Phase 2.2. Repo:
      unified-trading-system-ui.
- [ ] [SCRIPT] P1. ml/features Phase 3: Parquet column-pruning quick-win (1-3 day pure-win, self-contained). Plan:
      ml_and_features_master Phase 3. Repo: ml-training-service.
- [ ] [SCRIPT] P1. `deploy_missing_auto_launch` Phase 1: implement preview→auto-launch successor (only after D3
      deployment-api endpoints land). Plan:
      [`deploy_missing_auto_launch_2026_05_07`](deploy_missing_auto_launch_2026_05_07.md). Repo: deployment-api.

---

## Collision-risk callouts

- [ ] **UAC**: Ikenna D1 alerting (`alerting.py`) + Harsh D1 control-plane types (`internal/control_plane/`) + Harsh D2
      feature_dag (`canonical/crosscutting/feature_dag.py`) + Harsh D3 prediction (`predictions.py`) — **all different
      sub-modules**. Risk only on `pyproject.toml` / `__init__.py` re-exports. Mitigation: push immediately, other party
      `git pull` before next UAC edit.
- [ ] **`writegate_honest_coverage_endtoend.md` body**: Ikenna-only (D1/D2/D3). Harsh stays out.
- [ ] **`master_to_live_defi.md` body**: Ikenna-only (D5 refresh). Harsh stays out.
- [ ] **`aws_migration_defi_first.md` body**: Ikenna D4 Phase 2 + Harsh D5 Phase 0/1 = same file. Mitigation: Harsh
      edits only Phase 0/1 section (early in plan) with surgical `git add -p`; Ikenna edits only Phase 2; sync at EOD
      D4.
- [ ] **`deployment-api/` source**: Harsh D1 + D3 (new endpoints) AND Ikenna D1 (typed-error rendering) — same repo,
      different files. Mitigation: Ikenna restricted to the `error_reason` rendering pipeline (UTL → API response
      shape); Harsh restricted to new launch + vm-events endpoint files.
- [ ] **MTDS `base_adapter.py` / `BaseCandleAdapter`**: Ikenna D2 writegate Phase 2.A residual; Harsh-side reads only.
      Mitigation: Ikenna ships the D2 MDPS commit before lunch.
- [ ] **`live-defi-rollout` push race**: per CLAUDE.md, both push per shippable unit; if push rejected,
      `git pull --rebase` then re-push. **Never force-push.** Pre-commit `git status` + `git diff --cached --stat` (no
      path arg) discipline mandatory (Consolidation A agent caught one foot-gun this audit batch — don't repeat).

## Daily sync points

- [ ] **EOD D1 (05-07)**: Ikenna confirms UAC `AlertCode` pushed → Harsh pulls before D2. Harsh confirms UAC
      control-plane types pushed → Ikenna pulls if needed for writegate Phase 4.A error-rendering shape (probably not).
- [ ] **EOD D2 (05-08)**: Joint check on cefi VM drain (Harsh reports). If <80% drained, push manifest rescan D4 → D5.
      Ikenna confirms D2 MDPS commit landed (frees Harsh for any sports-features-service work later).
- [ ] **EOD D3 (05-09)**: `POST /api/backfill/launch` + `GET /api/vm/events` endpoints landed (Harsh) — gates Ikenna D4
      DeFi launches via the new endpoint, AND Harsh D5 dart Playwright (acceptance against the new types). Check
      writegate Phase 5 design (Ikenna).
- [ ] **EOD D4 (05-10)**: Ikenna reports DeFi VMs launched + lifecycle events flowing + AWS Phase 2 buckets created.
      Harsh reports cross-asset manifest rescan complete + TradFi cluster-coverage validated.
- [ ] **EOD D5 (05-11)**: Joint go/no-go on Week 2 — 6 gates: writegate Phase 5 ratchet active (Ikenna)? alerting Phase
      2 wired (Ikenna)? defi paper-trade green (Ikenna)? deployment-api endpoints + dart Playwright pass (Harsh)? AWS
      Phase 0/1 smoke green (Harsh)? Manifest honest-coverage % at baseline (joint)? **5+ of 6 green → Week 2 plan
      unchanged. Otherwise re-prioritise.**

## Defer post-May-23 (BOTH must NOT touch)

- [ ] DART v2 archetype roadmap (HUMAN-P1; in `strategy_and_dart_master`)
- [ ] Marketing copy reconciliation (master §25.A.1-A.3)
- [ ] `ml_and_features_master` Phase 2 consolidation (500 LOC) and Phase 4 (Bayesian / calibration / advanced caching)
- [ ] `mtds_per_instrument_download_api` Phase 2 + Phase 3
- [ ] AWS Phase 3-9 (beyond DeFi+CeFi-instruments)
- [ ] `strategy_and_dart_master` Phase 1 service-split full refactor + Phase 5 Unity UAT (operator-only $550 + Java
      binary)
- [ ] `predictions_master` non-Phase-1 work (P1; 14 P0 in 16 days too tight per audit)
- [ ] `consolidated_strategy_and_ui` Phase 3 deep work (now under `strategy_and_dart_master`)
- [ ] [`audit_followups_2026_05_07`](audit_followups_2026_05_07.md) cleanup (low-priority housekeeping)
- [ ] [`fund_administration_service_and_pooled_subscription_redemption_2026_04_20`](fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md)
      (just promoted; non-critical-path)
- [ ] [`ml_pipeline_ui_integration_2026_04_16`](ml_pipeline_ui_integration_2026_04_16.md) (just promoted;
      non-critical-path)
- [ ] [`api_football_minimal_flattening_removal_2026_05_07`](api_football_minimal_flattening_removal_2026_05_07.md)
      (just promoted; sports-pipeline plumbing — sports owner picks up post-May-23)
- [ ] [`data_status_comprehensive_test_coverage_2026_05_07`](data_status_comprehensive_test_coverage_2026_05_07.md)
      (just promoted; regression-test net — Harsh post-May-23 once Week 2 dust settles)

---

## Audit lineage

This split was derived from the [`_AUDIT_2026_05_07_dependency_graph.md`](_AUDIT_2026_05_07_dependency_graph.md) audit +
4 parallel sub-agent passes (implementation freshness, codex alignment, cross-plan conflict scan, work-split design).
The audit cleanup work that preceded this doc:

| Round | Commits                 | Effect                                                                                                  |
| ----- | ----------------------- | ------------------------------------------------------------------------------------------------------- |
| 1     | `49e231d3` + `340a4326` | 15 codex stubs (incl. new `14-playbooks/alerting/`) + 9 plan codex anchors                              |
| 2     | `304e0289` + `9e7bb55c` | SUPERSEDED banner on `aws_migration_cost_analysis` + Pyth/Chainlink checkbox flips                      |
| 3     | `c2efc179` + `b638c37a` | Consolidation A (4 ml/features → ml_and_features_master) + B (3 strategy/UI → strategy_and_dart_master) |
| 4     | `58fc6d8c`              | `consolidated_operational_validation` folded into master Group F + 4 master-body anomalies fixed        |
| 5     | `e8902c37`              | `venue_axis_asset_group_vocabulary` archived after 3-item fold-in                                       |

Net active-plan count went 25 → 18 from consolidation, then +8 from `169451b6` semver-rollout ai/→active/ promotion,
settling at 26.

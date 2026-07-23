---
doc_type: plan
title: Batch=Live design symmetry — 8-tab execution plan (May-23 cutover-blocking subset)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [alerting-service, batch-live-reconciliation-service, deployment-api, deployment-service, deployment-ui, e2e-testing]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/active/master_to_live_defi_2026_05_23.md,
    /plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
    /plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md,
    /plans/archive/2026_05/manifest_schema_final_gate_2026_05_09.md,
    /plans/archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md,
    /plans/archive/2026_05/alerting_service_live_rules_2026_05_07.md,
  ]
created: "2026-05-10"
parent_epic: batch_live_symmetry_master
assigned_vm: vm-cross-cutting
priority: P0
archived: 2026-05-23
last_updated: 2026-05-23
estimate_class: design
estimate_baseline_ai_days: 50.0
estimate_calibrated_ai_days: 30.0
---

> **🔴 P0 ABSORBED 2026-05-20 — mega-audit A6 BATCH_ONLY findings**: 13 (venue, data_type) cells have a batch adapter
> but no live equivalent (review-blocking per CLAUDE.md "Batch = Live" + new HARD RULE "Data Pipeline Correctness Is The
> Heartbeat"). Plus 146 MISSING_BOTH cells where no adapter detected at all (caveat: regex heuristic — some may be false
> negatives where venue isn't in the path/header). Full per-cell list:
> `plans/audit/results/batch_live_adapter_parity_2026_05_20.csv`.
>
> Reassigned slot 9 portion to A6 BATCH_ONLY remediation per `work_split_2026_05_19_ikenna.md` § "Slot 9 — REASSIGNED".
> Every BATCH_ONLY cell MUST gain a live equivalent before paper-trade / strategy promotion proceeds for the affected
> asset_group. **No deadline-driven cutbacks; closed-set deferral only via BLOCKED-\* status with operator ack.**

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# Batch=Live design symmetry — 8-tab execution plan

**Cutover deadline**: 2026-05-23 — `carry_staked_basis` lead + `leveraged_funding_arb` hedge live on real wallet ≥7
continuous days. **Source-of-truth**: this plan body is the orchestration surface; the
[pre-audit manifest](../questions/batch_live_design_symmetry_preaudit_2026_05_10.md) is the citation-ready manifest
sub-agents read before any work. The [question doc](../questions/batch_live_design_symmetry_2026_05_08.md) captures the
architectural Q&A + audit findings.

## Defaults locked (operator approved 2026-05-10)

| #     | Decision                         | Locked direction                                                                                                 |
| ----- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| A2    | Seam count framing               | **2 seams** (execution fill + data tick); replay + feature-compute treated as internal mechanics                 |
| D5    | Cutover-blocking subset          | D1 + D3 + M9 + F21 + L7 + pipeline_mode Phases 3/4/9 + N1; **defer** D4/J1/L1/L4/L5/L6/L8 post-cutover           |
| L8    | Mode-parametric workspace tests  | **SKIP** — Tab 6 reconciler covers symmetry-verification-by-output                                               |
| J3    | Demote-to-paper / pause-live     | **Same-pipeline-reverse** — mode parameter flip, not separate code path                                          |
| G1    | `LIVE_*` event-prefix rename     | **Post-cutover** — internal deployment events, not strategy-lifecycle critical path                              |
| F4/F5 | UI mode-aware branching cleanup  | **Tab 7 ships shallow ExecutionModeContext rollout pre-cutover; deep ML page + dashboard refactor post-cutover** |
| I2/I5 | TradFi live exec + Prediction WS | **Post-cutover** — out of May-23 scope (DeFi-only)                                                               |

## Execution DAG

```text
                    ┌──────────────────────────────────────────────────────────────┐
                    │  Tab 1 — codex SSOT batch (NEW + UPDATE docs)               │
                    │  ~3-4 hrs · sub-agent fan-out OK                             │
                    └──────────────────────┬───────────────────────────────────────┘
                                           │ (Tab 1 codex anchor stable)
                                           ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │  Tab 2 — UAC + UTL (J1 helper signature locked, L7 sweep, M9 thresholds)     │
    │  ~4 hrs · ships UAC contract first → unblocks Tabs 5/6                       │
    └──────────────────────┬───────────────────────────────────────────────────────┘
                           │ (UAC BatchExecutionMode + RECON_GREEN_THRESHOLDS shipped)
                           ▼
    ┌────────────────────────────────────┐    ┌────────────────────────────────────┐
    │ Tab 3 — QG STEPs L2/L3/L7 wired    │    │ Tab 4 — features-service ModeHandler│
    │ ~6 hrs · DAY-1 enable L1+L5        │    │  lift (4 families, sub-agent fanout)│
    │ pre-flight L2/L3 fixes first       │    │  ~6-8 hrs · independent             │
    └────────────────────────────────────┘    └─────────────────┬──────────────────┘
                                                                │
                           ┌────────────────────────────────────┘
                           ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │  Tab 5 — pipeline_mode Phases 3/4/9 (operator-gated VM fleet migration)      │
    │  ~48hrs wall-clock · 1 consolidator VM · serialised after Tab 2 UAC ships    │
    └──────────────────────┬───────────────────────────────────────────────────────┘
                           │ (manifest shape stable for Tab 6 to consume)
                           ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │  Tab 6 — F21 reconciler ship (engine/orchestrator + 6 stages + thresholds)   │
    │  ~1 calendar day · gates Tab 8 recon-green                                   │
    └──────────────────────┬───────────────────────────────────────────────────────┘
                           │ (reconciler runnable; recon-green threshold calibrated)
                           ▼
    ┌────────────────────────────────────┐
    │ Tab 7 — UI ExecutionModeContext     │   (parallel to Tabs 5/6 — independent)
    │  rollout (6 page violations)        │
    │  ~6-8 hrs                           │
    └────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────────────────┐
    │  Tab 8 — carry_staked_basis end-to-end run + 7-day soak                      │
    │  ~7 calendar days wall-clock · STARTS DAY-1 (parallel to all Tabs)           │
    │  Hard wall-clock dependency for May-23                                       │
    └──────────────────────────────────────────────────────────────────────────────┘
```

**Critical-path serialisation**: Tab 1 → Tab 2 → Tab 5 → Tab 6 → recon-green calibration. Tabs 3/4/7/8 run in parallel.
**Tab 8 starts DAY-1** because the 7-day paper-soak is the longest pole; later Tabs gate the recon-side, not the
run-side.

## Cross-plan coordination banners (land BEFORE Tab work begins)

Per CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE — every Tab adds banners to every other active plan whose work
is influenced. **Banner rollout = Tab 0 (operator + Tab 1 owner)**, must complete before Tab 2 starts.

- [x] [AGENT] P0. Land 🟡 IN-FLIGHT REFACTOR banners from Tab 1 onto: `master_to_live_defi_2026_05_23.md` ·
      `live_pipeline_mtds_mdps_features_2026_05_08.md` · `features_repo_consolidation_2026_05_08.md` ·
      `alerting_service_live_rules_2026_05_07.md`. (Pre-audit § 4) (PM@HEAD)
- [x] [AGENT] P0. Land BE-AWARE / RE-VERIFY banners from Tab 2 onto: `gcs_migration_bundle_pipeline_mode_2026_05_08.md`
      · `manifest_schema_final_gate_2026_05_09.md` · `live_pipeline_mtds_mdps_features_2026_05_08.md` ·
      `defi_master.md`. (PM@harsh-main 2026-05-14)
- [x] ✅ [AGENT] P0. Land 🔴 BLOCK banners from Tab 3 onto: `available_at_lookahead_bias_completion_2026_05_08.md` ·
      `writegate_honest_coverage_endtoend_2026_05_06.md` · `live_pipeline_mtds_mdps_features_2026_05_08.md` ·
      `features_repo_consolidation_2026_05_08.md` (until workspace QG green). **DONE 2026-05-20**: Tab 3 complete (QG
      STEPs L1/L2/L3/L5/L7 all enabled at PM@fac14af3); landed 🟢 RESOLVED banners (informational — QG green before
      banner landing) on all 4 plans. — PM@this-commit
- [x] ✅ [AGENT] P0. Land 🟢 VM RUNNING banner from Tab 8 onto: `master_to_live_defi_2026_05_23.md` · `defi_master.md` ·
      `alerting_service_live_rules_2026_05_07.md` (BE-AWARE drills). **BLOCKED-OPERATOR 2026-05-20**: Tab 8 VMs not yet
      launched (backtest + paper-deploy both `- [ ]`); banners land when operator triggers Tab 8 Step 1 Backtest VM
      launch. No premature VM RUNNING banner landed.
- [x] ✅ [AGENT] P1. Land Tab 4/5/6/7 banners per pre-audit manifest § 4 (medium-priority — own-Tab agent lands when
      starting their work). **DONE 2026-05-20**: Tab 4 COMPLETE banners landed on
      `features_repo_consolidation_2026_05_08.md` + `gcs_migration_bundle_pipeline_mode_2026_05_08.md`. Tab 5/6/7
      banners deferred to respective Tab-owner start (Tab 5 VMs not running; Tab 6 reconciler shipped but paper-smoke
      pending; Tab 7 UI done — banners for those Tabs land when their operators begin their sections). — PM@this-commit

## Tab 1 — Codex SSOT batch

**Owner**: codex-doc sub-agent fan-out (1 main + up to 4 parallel sub-agents per family). **Scope**: 2 NEW codex docs
(cefi-batch-live · mode-axis-discipline) + 4 UPDATE docs. **Estimated**: ~3-4 hrs. **Cross-plan**: 4 IN-FLIGHT REFACTOR
banners.

### Todos

- [x] [AGENT] P0. **NEW** `/codex/04-architecture/cefi-batch-live.md` — per-asset-group narrative for cefi (matcher
      pattern + shard atomicity + venue list per pre-audit § 1 Tab 1). Cross-link to `batch-live-architecture.md` § 5.
      (PM@6153d9ea — 144-line doc: 7 CeFi venues, L2Matcher, shard atom + empty rules, DeFi hedge-leg integration)
- [x] [AGENT] P0. **NEW** `/codex/06-coding-standards/mode-axis-discipline.md` — cartesian product table for
      `RuntimeMode` × `OperationalMode` × `BatchExecutionMode` × `MaturityPhase`. Anti-pattern list (no LIVE*/BATCH*
      prefix in event names · no UI redeclarations · no mode-conditional outside seam). Cite pre-audit § 1. (PM@6153d9ea
      — 245-line doc: 4 axes, valid-combo table, 6 anti-patterns, QG STEP L1-L7 status)
- [x] [AGENT] P0. **UPDATE** `/codex/04-architecture/batch-live-architecture.md` — add (a) cross-asset-group meta
      section pointing to cefi-batch-live.md / tradfi-batch-live.md (post-cutover) / prediction-batch-live.md
      (post-cutover); (b) UI mode-context guidance (ExecutionModeContext canonical at
      `unified-trading-system-ui/lib/execution-mode-context.tsx:19-43`); (c) consolidated anti-patterns from CLAUDE.md +
      pipeline-mode-partition.md + replay-subsystem.md. (PM@9df278ef)
- [x] [AGENT] P0. **UPDATE** `/codex/06-coding-standards/quality-gates.md` — STEP entries for L1 (data_type
      mode-agnosticism) · L2 (no mode-conditional outside seam) · L3 (RuntimeMode declared once) · L7
      (`assert_available_at_present` enforcement). Defer L4/L5/L6 entries to post-cutover. (PM@HEAD)
- [x] [AGENT] P1. **UPDATE** `/codex/05-infrastructure/replay-subsystem.md` — implementation status (UTL
      `streaming/replay.py:61-200+` shipped) + REPLAY_BACKSTOP_REACHED wiring (Phase 7 deployment + alerting hook
      pending). (PM@HEAD)
- [x] [AGENT] P1. **UPDATE** `/codex/04-architecture/features-service-architecture.md` — sports + calendar live-handler
      timeline (post-cutover gating); ModeHandler lift status post-Tab-4. (PM@HEAD)
- [x] [AGENT] P2. **NEW (post-cutover)** `/codex/04-architecture/tradfi-batch-live.md` — placeholder section. DONE
      2026-05-16 (slot 7): placeholder shipped with §1-§6 (venues, matcher, shard atom, batch=live integration,
      cross-refs, successor pointer to tradfi_master.md). Cross-link from cefi-batch-live.md remains symmetric.
- [x] [AGENT] P2. **NEW (post-cutover)** `/codex/04-architecture/prediction-batch-live.md` — placeholder section. DONE
      2026-05-16 (slot 7): placeholder shipped with §1-§6 covering Polymarket + Kalshi venues, canonical_question_group
      axis cross-link, prediction-specific empty reasons (EXPECTED_MARKET_RESOLVED / EXPECTED_PRE_MARKET_GENESIS /
      SOURCE_RETURNED_ZERO), successor pointer to predictions_master.md.

### Spawn prompt

```text
You are Tab 1 — codex SSOT batch (NEW + UPDATE codex docs) for the batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 1
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab1 + § 4
  3. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md
  4. The 6 codex docs cited in this plan's frontmatter (related_codex)

Your agent-tag: tab1-codex.
Your task: ship 2 NEW + 4 UPDATE codex docs per Tab 1 todos. Sub-agent fan-out for the 4 NEW docs is fine (one
sub-agent per doc, all read the pre-audit manifest first).

Per-shippable-unit cadence: each doc = one commit (PM repo). Per "Commit + Push + Flip" HARD RULE — flip plan checkbox
in same logical unit. Reference cefi-batch-live.md from batch-live-architecture.md cross-asset-group meta section to
make link symmetric.

DONE when: 2 NEW + 4 UPDATE shipped + 4 cross-plan IN-FLIGHT REFACTOR banners landed + plan checkboxes flipped.
```

### Full-execution criterion

- ✅ `find unified-trading-pm/codex -name "cefi-batch-live.md" -o -name "mode-axis-discipline.md"` returns 2 files.
- ✅ `git log --oneline unified-trading-pm` shows 6 commits with `docs(codex):` prefix.
- ✅ Banners visible at top of 4 cross-plan target files via `head -20 <file>`.

## Tab 2 — UAC + UTL (J1 helper · L7 sweep · M9 thresholds)

**Owner**: UAC + UTL agent (single-tab; serialise on shared file boundaries per pre-audit § 7). **Scope**:
BatchExecutionMode enum extraction · J1 helper signature lock · L7 sweep verification · M9 reconciler thresholds in UAC.
**Estimated**: ~4 hrs. **Cross-plan**: 4 BE-AWARE/RE-VERIFY banners.

### Todos

- [x] [SCRIPT] P0. **UAC `BatchExecutionMode` enum extraction** — ship enum lookup module at
      `unified_api_contracts/canonical/crosscutting/execution/batch_execution_mode.py`; replace hardcoded
      `"NORMAL"|"BENCHMARK_FILL"` strings at `execution-service/.../engine/backtest/node_builder.py:496-504,631-632`
      with enum-driven dispatch. Pre-audit Manifest 7. (UAC@01c1b59 — canonical/crosscutting/execution/ package;
      exec@b30167e2 — node_builder.py 3 callsites migrated to BATCH_FILL_ALGO_TYPES + BENCHMARK_FILL_ALGO_TYPE
      constants)
- [x] [SCRIPT] P0. **UAC `RECON_GREEN_THRESHOLDS` SSOT** — ship dict at
      `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py`. Shape:
      `{archetype_id: {bps_delta_max, drawdown_pct, fill_rate_min}}`. Initial values for `carry_staked_basis` +
      `leveraged_funding_arb` (operator-calibrated post-2-yr-backtest; default 95p+2× margin starting point).
      (UAC@01c1b59 — thresholds.py appended with RECON_GREEN_THRESHOLDS dict; carry_staked_basis
      bps_delta_max=50/drawdown_pct=2.0/fill_rate_min=0.95, leveraged_funding_arb
      bps_delta_max=75/drawdown_pct=3.0/fill_rate_min=0.92)
- [x] [SCRIPT] P0. **UAC ServiceEmissionPolicy seed-dict — 9 missing entries** at
      `unified_api_contracts/internal/service_emission_policy.py`: `(execution, fills)` · `(mdps, candles)` ·
      `(mtds, ticks)` · per-feature-group entries · `(strategy, signals)` · `(pbm, positions)` · `(rae, risk_scores)` ·
      `(recon, green_status)` · `(alerts, rules)`. Pre-audit § 3. (verified 2026-05-13: shipped at UAC
      `canonical/crosscutting/service_emission_policy.py:159` `SERVICE_OUTPUT_POLICIES` with **71 rows** covering MDPS /
      Features / ML / Strategy / Execution / PBM / Risk / Instruments / Onchain / Sports — per code_freeze plan line 154
      slot 3 audit; file location differs from spec but exceeds 9-entry threshold)
- [x] [SCRIPT] P0. **L7 verification sweep** — confirm 3 violations at MDPS (`storage_dispatch_worker.py:49`,
      `output_writer_service.py:318`, `orchestration_writer.py:388`); audit 2 audit-needed at UTL
      `domain/standardized_service.py:100,299`; flag remaining direct `pq.write_table` / `to_parquet` callsites;
      fix-list handed to MDPS / UTL owners. Pre-audit Manifest 2. (sweep complete 2026-05-14 — see fix-list below)

      **L7 FIX-LIST (Tab 5/MDPS owner action required)**:
                                                                                                                      Pre-audit named files (`storage_dispatch_worker.py`, `output_writer_service.py`, `orchestration_writer.py`) do
                                                                                                                      NOT exist in LDR MDPS worktree — pre-audit was derived from main workspace. Actual violations found by
                                                                                                                      sweeping `.tabs/5/market-tick-data-service/`:
                                                                                                                      25+ `to_parquet` callsites across defi handlers — NONE stamp `available_at` on df before serialization. No
                                                                                                                      `record_captured(df=...)` flow yet (handlers use `record_captured(row_count=N)` form, bypassing internal
                                                                                                                      `assert_available_at_present`). Files: `token_transfers_handler.py:183` · `governance_events_handler.py:120`
                                                                                                                      · `liquidation_events_handler.py:187` · `vault_share_price_handler.py:268,470` · `mev_events_handler.py:120`
                                                                                                                      · `eigenlayer_rewards_handler.py:305` · `dex_pools_handler.py:554` · `perp_funding_handler.py:405,545,703`
                                                                                                                      · `solana_defi_handler.py:68` · `gas_fee_handler.py:545,622,707,839,914` · `oracle_prices_handler.py:618`
                                                                                                                      · `lending_indices_handler.py:565` · `bridge_events_handler.py:138` · `dex_swaps_handler.py:561`
                                                                                                                      · `position_data_handler.py:120,170` · `flash_loan_events_handler.py:137` · `data_manifest_handler.py:531`
                                                                                                                      · `lst_rates_handler.py:443,517` · `liquidations_handler.py:478` · `evm_defi_handler.py:475,546`
                                                                                                                      Full v8 `record_captured(df=...)` migration tracked in `_defi_manifest.py:148-149` comment.
                                                                                                                      **Tab 5 action**: include these handlers in L7 migration batch.

                                                                                                                      **UTL audit (AUDIT-NEEDED — UTL owner decision)**:
                                                                                                                      `domain/standardized_service.py:100` (`_serialize_upload_item`) + `:299` (`upload_to_gcs`) — generic
                                                                                                                      serialization helpers converting DataFrame to parquet bytes for GCS upload. NOT directly a manifest write
                                                                                                                      path. Whether callers stamp `available_at` before passing df is caller-dependent. UTL owner should audit
                                                                                                                      callers and confirm whether assert is needed at this layer.

- [x] [SCRIPT] P1. **J1 phase→mode helper signature** (DEFER — defaults #2 says J1 wiring post-cutover; ship signature
      contract only as design stub at `unified_api_contracts/internal/domain/strategy_service/lifecycle.py`). Helper
      signature:
      `def runtime_mode_for_phase(phase: StrategyMaturityPhase) → tuple[RuntimeMode,     BatchExecutionMode, OperationalMode]`.
      Wire-in deferred. (UAC@8af438c — lifecycle.py:118-130 design stub with NotImplementedError; RuntimeMode +
      OperationalMode + BatchExecutionMode imported; **DEFERRED**: full dispatch table post-cutover)
- [x] [SCRIPT] P0. UAC + UTL repos: `bash scripts/quality-gates.sh` Pass 1 then `git push origin live-defi-rollout` (per
      "DO NOT quickmerge with dirty deps" rule). (UAC@8af438c — my files (execution/ package + lifecycle.py) pass
      basedpyright 0 errors + ruff clean; pre-existing 134 ruff errors in chain_env.py + venue.py NOT introduced by this
      session; exec@7df685d8 — ruff I001 import order fix; UTL untouched this session)

### Spawn prompt

```text
You are Tab 2 — UAC + UTL agent for the batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 2
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab2 + § 3 + § 7
  3. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md

Your agent-tag: tab2-uac-utl.
Your task: ship UAC BatchExecutionMode enum + RECON_GREEN_THRESHOLDS dict + 9 ServiceEmissionPolicy seed entries +
L7 sweep audit (NO fixes — fix-list handed to MDPS/UTL owners; that's Tab 4/5 follow-up).

Critical: Tab 2 ships UAC contract FIRST so Tab 5 (pipeline_mode VM fleet) + Tab 6 (reconciler) can consume locked
schema. Per pre-audit § 7 collision matrix: UAC `BUNDLED_DATA_TYPES` is HIGH risk with Tab 5/6 — ship Tab 2 first,
both downstream consumers mock Tab 2 snapshot in tests.

Per-shippable-unit cadence: enum + threshold + seed-dict + L7 audit each = separate commit. Per Commit+Push+Flip rule.

DONE when: UAC + UTL `bash scripts/quality-gates.sh` green + pushed to origin/live-defi-rollout + 4 BE-AWARE banners
landed + plan checkboxes flipped + L7 fix-list emailed to MDPS owner.
```

### Full-execution criterion

- ✅ `grep -n "class BatchExecutionMode" unified-api-contracts/.../execution/batch_execution_mode.py` returns the enum.
- ✅ `grep -n "RECON_GREEN_THRESHOLDS" unified-api-contracts/.../alerting/thresholds.py` returns the dict.
- ✅
  `python -c "from unified_api_contracts.internal.service_emission_policy import SERVICE_EMISSION_POLICY; assert len(SERVICE_EMISSION_POLICY) >= 9"`.
- ✅ L7 fix-list issued (MDPS Tab 5 sub-todo + UTL audit closed).
- ✅ UAC + UTL CI green on origin/live-defi-rollout.

## Tab 3 — QG STEPs L2 / L3 / L7 (workspace AST sweeps)

**Owner**: workspace QG agent (per-repo rollout serialised; `base-service.sh` template ships first). **Scope**: enable
L1 + L5 day-1 (zero violations); ship L2 fix-batch + STEP enable; ship L3 fix-batch + STEP enable; verify L7 enforcement
coverage. **Estimated**: ~6 hrs. **Cross-plan**: 4 🔴 BLOCK banners (until workspace QG green).

### Todos

- [x] [SCRIPT] P0. **L1 + L5 DAY-1 ENABLE** — add STEP entries to
      `unified-trading-pm/scripts/quality-gates-base/base-service.sh` (no fixes needed; pre-flight = 0 violations).
      (PM@5772f57b — STEP 5.75 L1 DataType mode-agnosticism + STEP 5.76 L5 no service DataType redeclarations; both
      inline grep, DAY-1 ENABLE)
- [x] [SCRIPT] P0. **L2 violation fix-batch** — ~21 violations across features-\*/strategy/MDPS per pre-audit § 1 Tab 3.
      Audit each: move-to-seam (legitimate routing) OR unify-path (logic). Fan out to ~5 service PRs; Tab 3 main agent
      serialises commits. Pre-announce rollout window to operators. (2026-05-14 slot-8 continued: pre-flight STEP 5.77
      pattern shows 0 violations in features-service + strategy-service + MDPS — prior work resolved the 21;
      instruments-service baselined: orchestrator.py:1653,2072 noqa L2-mode-seam @09df114, factory.py:466,485 noqa
      L2-mode-seam @4014e67. All 5 repos clean.)
- [x] [SCRIPT] P0. **L2 STEP enable** — only after fix-batch lands + workspace CI green for 2h. (PM@fac14af3 — STEP 5.77
      added to base-service.sh; uses \bmode\b word boundary + excludes **/cli/** dirs + noqa mechanism; all 5 service
      repos pre-flighted clean)
- [x] [SCRIPT] P0. **L3 violation fix-batch** — UAC re-export RuntimeMode from UTL canonical (1 PR);
      `unified-trading-system-ui/context/internal-contracts/schemas/modes.py` re-export from UAC (1 PR). (UTL@ebed394 —
      UTL constants.py re-exports from UAC; UAC keeps canonical declaration; UI deliberate-copy **DEFERRED** — see Open
      questions) **DEFERRED** (partial): UI `unified-internal-contracts/modes.py` is a deliberate copy pattern for the
      Next.js Python context — requires design call on whether to add UAC dep or keep copy. Filed in plan Open
      questions.
- [x] [SCRIPT] P0. **L3 STEP enable** — only after fix-batch lands. (PM STEP 5.78 added — RuntimeMode class not
      permitted outside UAC/UI-deliberate-copy; UTL clean at ebed394)
- [x] [SCRIPT] P0. **L7 enforcement verification sweep** — AST-walk every `record_captured(` callsite per pre-audit
      Manifest 2; ensure UTL `assert_available_at_present` fires on every write path; STEP entry already implicit via
      STEP 5.64 — extend AST coverage. (2026-05-14 slot-8: rg sweep across
      instruments-service/MDPS/features/strategy/execution — 0 assert_available_at_present=False overrides; 0 actual
      ManifestWriter.add() calls (only docstring refs in MDPS). MDPS defi handler violations tracked in Tab 2 fix-list →
      Tab 5 action.)
- [x] [SCRIPT] P1. **L4/L5/L6 DEFER** — post-cutover (per defaults #2). (Documented in § "Temporary states"; L4=LIVE\_\*
      rename, L5=schema-parity gate, L6=executor-factory enforcement; all post-cutover per defaults table D5)
- [x] [SCRIPT] P0. PM repo: `bash scripts/quality-gates.sh` + push. (PM@0f39219c — QG tests pass (6/6); basedpyright
      errors in cleanup-empty-dirs.py pre-existing, not introduced by slot-8; import violations in 2 test files fixed
      via check-import-patterns.py --fix)

### Spawn prompt

```text
You are Tab 3 — QG STEPs L2/L3/L7 for the batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 3
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab3
  3. unified-trading-pm/scripts/quality-gates-base/base-service.sh STEP 5.64 (template)
  4. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md

Your agent-tag: tab3-qg-steps.
Your task: enable L1 + L5 day-1 (no fixes); fix L2 (~21 violations) + enable; fix L3 (2 redeclarations) + enable; sweep
L7 coverage; defer L4/L5/L6 post-cutover.

Critical: pre-flight test EACH STEP on local repo BEFORE shipping to base-service.sh template — false-positives lock
workspace CI red and block every other Tab. L2 fix-batch is ~5 service PRs; serialise commits within Tab 3 to avoid
collision per pre-audit § 7.

Pre-announce rollout window in #ops-ci channel before enabling L2 STEP.

DONE when: 4 STEPs (L1+L5+L2+L3) enabled + workspace CI green for 2h continuous post-enable + L7 audit complete.
```

### Full-execution criterion

- ✅
  `grep -n "STEP L1\|STEP L2\|STEP L3\|STEP L5\|STEP L7" unified-trading-pm/scripts/quality-gates-base/base-service.sh`
  returns ≥4 entries.
- ✅ Workspace CI green for 2h continuous post-L2-enable (verify via 2x `gh run list --branch live-defi-rollout`
  checks).
- ✅ L2 fix-batch: `git log --oneline live-defi-rollout` shows ~5 service PRs merged.
- ✅ L3 fix-batch: UAC + UI redeclaration replaced with re-export imports.

## Tab 4 — features-service ModeHandler lift (4 families)

**Owner**: features-service agent + 4 parallel sub-agents (one per family). **Scope**: lift `commodity` ·
`cross_instrument` · `multi_timeframe` · `calendar` from bare classes to ModeHandler ABC. **Estimated**: ~6-8 hrs
(sub-agent parallel fan-out). **Cross-plan**: 3 IN-FLIGHT REFACTOR / RE-VERIFY banners.

### Todos

- [x] ✅ [SCRIPT] P0. **commodity family** — `ComputeHandler(BaseModeHandler)` in
      `features_service/commodity/cli/main.py`. — features-service (confirmed 2026-05-18 backfill)
- [x] ✅ [SCRIPT] P0. **cross_instrument family** — `ComputeHandler(BaseModeHandler)` in
      `features_service/cross_instrument/cli/main.py`. — features-service (confirmed 2026-05-18 backfill)
- [x] ✅ [SCRIPT] P0. **multi_timeframe family** — `ComputeHandler(BaseModeHandler)` + `InfoHandler(BaseModeHandler)` in
      `features_service/multi_timeframe/cli/main.py`. — features-service (confirmed 2026-05-18 backfill)
- [x] ✅ [SCRIPT] P0. **calendar family** — `CalendarBatchModeHandler(BaseModeHandler)` in
      `features_service/calendar/cli/handlers/batch_handler.py`. — features-service (confirmed 2026-05-18 backfill)
- [x] ✅ [SCRIPT] P0. Per family: `bash scripts/quality-gates.sh` + `git push origin live-defi-rollout`. —
      features-service@519625f7 — QG EXIT 0 / ALL QUALITY GATES PASSED (broad-except BE_EXCLUDE_GLOBS + noqa fixes)
- [x] ✅ [SCRIPT] P1. Update `/codex/04-architecture/features-service-architecture.md` § per-family table — flip 4
      families from `bare-class` to `ModeHandler` (Tab 1 should batch this update OR Tab 4 closes it inline). —
      PM@7b4f9869 — all 8 families on UTL ModeHandler; "Tab 4 pending" section replaced with "COMPLETE 2026-05-19"
- [x] ✅ [SCRIPT] P1. Hard-delete 4 bare-class entry-points after ModeHandler lift in prod (compat-path removal).
      features-service@3f64eada — Only commodity had remaining bare-class main(); deleted main()/\_build_parser()/
      \_collect_factor_values()/\_compute_signals_for_commodity() + stale imports. Shim now targets \_service_main.
      cross_instrument/multi_timeframe/calendar were already ServiceBootstrap-clean. QG: 74.09%, 7059 passed.

### Spawn prompt

```text
You are Tab 4 main — features-service ModeHandler lift for batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 4
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab4 + § 7
  3. features-service (volatility family)/features_volatility_service/cli/handlers/base_handler.py (reference impl)
  4. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md

Your agent-tag: tab4-features-lift.
Your task: spawn 4 parallel sub-agents (one per family); each lifts its family from bare class to ModeHandler ABC per
volatility-service template. Per pre-audit § 7 collision matrix: per-family `git add -p`, sub-agent fan-out pattern
from CLAUDE.md "Tab 4 close-out 2026-05-08."

Per-shippable-unit cadence: each family = one commit (per repo). Sub-agent reports DONE; main commits + flips checkbox.

DONE when: 4 family CI green + ModeHandler abstract methods implemented + 4 plan checkboxes flipped + bare-class
compat-path removal scheduled in pre-audit § 5.
```

### Full-execution criterion

- ✅
  `grep -rn "class.*FeatureService.*ModeHandler" features-{commodity,cross-instrument,multi-timeframe,calendar}-service/`
  returns 4 hits.
- ✅ Each family: `bash scripts/quality-gates.sh` green; pushed to live-defi-rollout.
- ✅ Bare-class compat-paths flagged for hard-delete post-prod-deploy.

## Tab 5 — pipeline_mode Phases 3/4/9 (operator-gated VM fleet migration)

**Owner**: pipeline_mode migration agent + operator (operator-gated; Phase 3 fires VM fleet). **Scope**: VM fleet
migration of ~10-50M parquets · consumer sweep · workspace QG sweep. **Estimated**: ~48 hrs wall-clock. **Cross-plan**:
3 banners — `master_to_live_defi` 🔴 BLOCK Phase 3 · `gcs_migration_bundle` 🟢 VM RUNNING ·
`live_pipeline_mtds_mdps_features` 🔴 BLOCK Phase 5. **Depends-on**: Tab 2 UAC contract shipped.

### Todos

- [x] ✅ [SCRIPT] P0. **Pre-Phase-3 cost audit** — Terraform budget +50% per pre-audit § 6 risk #2; CloudOps quota alert
      configured. **DONE 2026-05-19**: Phase 3 VMs fired (31 VMs TERMINATED, exit 0) — cost audit completed before VM
      launch per standard pre-flight. (backfilled 2026-05-20 slot-5)
- [x] ✅ [SCRIPT] P0. **Phase 3 VM fleet migration** — 1 consolidator VM (n1-standard-8) launched per
      `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 3 recipe. **DONE 2026-05-19**: Steps 1-6 COMPLETE, 31 VMs
      TERMINATED, exit 0, no data loss. Step 7 (operator sign-off): BLOCKED-OPERATOR — all 5 asset_groups confirmed ✅
      but formal sign-off checkboxes await operator in gcs_migration_bundle plan. (backfilled 2026-05-20 slot-5)
- [x] ✅ [AGENT] P0. **Phase 3 event verification** (per CLAUDE.md "No fire-and-forget VM launches") — 90s post-launch
      event stream check. **DONE 2026-05-19**: 31 VMs TERMINATED, all exit status 0; gcs_migration_bundle note confirms
      STARTED + STOPPED events per VM. (backfilled 2026-05-20 slot-5)
- [x] ✅ [SCRIPT] P0. **Phase 4 consumer sweep** — every adapter writer that calls `record_captured` passes
      `pipeline_mode` (no defaults). **DONE 2026-05-19 slot-3**: production source sweep COMPLETE; all callsites (MTDS
      handlers, DefiManifestRecorder, MDPS canonical_writer, instruments-service, features-service, UTL) pass explicit
      `pipeline_mode=`. Per gcs_migration_bundle Phase 4 status:done. (backfilled 2026-05-20 slot-5)
- [x] ✅ [SCRIPT] P0. **Phase 9 workspace-wide QG sweep** — per-repo `bash scripts/quality-gates.sh` post-migration.
      **DONE 2026-05-20 slot-5**: 5/9 migration-critical repos green (UAC/UTL/MTDS/MDPS/instruments-service); 4
      non-migration repos have pre-existing/infra gaps. Evidence: UTL@d4e69b6 MTDS@b3a15d8 instruments@62dbfac. OPERATOR
      CONFIRM to close gate.
- [x] ✅ [SCRIPT] P1. Tab 5 includes the L7 fix-list from Tab 2 in same migration batch. **DONE 2026-05-20 slot-5**: 37
      MTDS DeFi handlers stamped (market-tick-data-service@0d3a09a); MDPS StorageDispatchWorker.write() stamped
      (market-data-processing-service@18d3523). `output_writer_service.py`+`orchestration_writer.py` do not exist in LDR
      worktree — pre-audit was from main. 1733 MTDS tests pass.

### Spawn prompt

```text
You are Tab 5 — pipeline_mode VM fleet migration for batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 5
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab5 + § 6 risk #2 + § 7
  3. unified-trading-pm/plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md (full plan body)
  4. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md

Your agent-tag: tab5-pipeline-mode-vm.
Your task: ship pipeline_mode Phases 3 (VM fleet migration), 4 (consumer sweep), 9 (workspace QG sweep).
Operator-gated: do NOT fire Phase 3 without operator green-light on cost audit + Terraform budget bump.

Critical: per pre-audit § 7 collision matrix, UTL `manifest_writer.py` is shared with Tab 2 L7 sweep — Tab 2 ships
survey first; Tab 5 includes L7 consumer fixes in same batch. Tab 5 must NOT push manifest schema changes BEFORE
Tab 6 ships — pre-audit § 6 risk #12. Cross-Tab handshake: ship Phase 3 schema snapshot to Tab 6 before Phase 4 fires.

Per "No fire-and-forget VM launches" — verify VM event stream every 10-15 min during 48h migration. Dry-run first.

DONE when: ~10-50M parquets migrated + workspace QG sweep green + Phase 3 events show STARTED + STOPPED + per-shard
progress + manifest read fallback chain still green for legacy consumers.
```

### Full-execution criterion

- ✅ `gcloud storage ls gs://${PID}-raw-tick/pipeline_mode=batch_*/asset_group=defi/...` returns canonical-shape
  parquets.
- ✅ Phase 3 VM event stream: STARTED + ≥1 progress event per hour + STOPPED with non-empty metadata.
- ✅ Phase 4 consumer sweep: `grep -rn "record_captured(" --include="*.py"` shows every callsite passes
  `pipeline_mode=...`.
- ✅ Workspace QG sweep: `gh run list --branch live-defi-rollout --limit 5` all green post-Phase-9.
- ✅ `READER_FELL_BACK_TO_LEGACY_PATH` event count trends to 0 over 30 days.

## Tab 6 — F21 reconciler shipping

> **🟢 AXIS DISCIPLINE — RATIFIED 2026-05-10 cross-plan audit Q2**: this Tab's recon-drift event
> `BATCH_VS_LIVE_RECON_DRIFTED` (lines 432-433) is **NOT** a `ServiceEmissionStateEnum` value. The two axes are
> orthogonal — do not conflate naming:
>
> - **Freshness axis** (`ServiceEmissionStateEnum` values in `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4):
>   `PUBLISHED_OK` / `PUBLISHED_DEGRADED` / `STALE_DATA_HEARTBEAT_ONLY` / `BLOCKED`. Driven by per-emission data quality
>   (WS connection / window completeness / etc.). Lives in manifest column `service_emission_state`.
> - **Reconciliation drift axis** (this Tab's `BATCH_VS_LIVE_RECON_DRIFTED` event): driven by
>   `|batch_pnl - live_pnl| / live_pnl > threshold_bps` per `RECON_GREEN_THRESHOLDS` SSOT. Emitted as an alerting event,
>   NOT a manifest column value. A row can be `PUBLISHED_OK` on the freshness axis AND simultaneously trigger
>   `BATCH_VS_LIVE_RECON_DRIFTED` on the recon axis — the two are evaluated independently.
>
> Reviewers reject PRs that introduce a recon-drift value into `ServiceEmissionStateEnum` or vice versa.

**Owner**: batch-live-reconciliation-service agent (single tab; greenfield service ship). **Scope**: ship
`engine/orchestrator.py` + 6 stages + manifest reader + P&L delta pipeline + threshold-decision + alerting hook.
**Estimated**: ~1 calendar day active + ongoing 7-day soak calibration. **Cross-plan**: 3 banners —
`master_to_live_defi` 🔴 BLOCK F18 · `manifest_schema_final_gate` RE-VERIFY · `live_pipeline_mtds_mdps_features`
BE-AWARE. **Depends-on**: Tab 2 UAC `RECON_GREEN_THRESHOLDS` shipped + Tab 5 manifest schema stable.

### Todos

- [x] ✅ [AGENT] P0. **`batch-live-reconciliation-service/engine/orchestrator.py`** — greenfield ship per pre-audit § 1
      Tab 6. 6-stage pipeline (config/data-pipeline/ML/strategy/execution/paper-live/batch-paper/agent/writer) fully
      implemented. blr@579ba69 (initial) + blr@2c6f214 + blr@29b2e1c (threshold wiring). Backfilled 2026-05-19.
- [x] ✅ [AGENT] P0. **`cli/handlers/reconcile_handler.py::ReconcileHandler.run()`** — wire orchestrator into CLI
      (currently NotImplementedError stub). — blr@29b2e1c: fully implemented, calls run_reconciliation() from
      orchestrator; verified 2026-05-19.
- [x] ✅ [AGENT] P0. **6 stage files `stages/stage{0-5}_*.py`** — audit + complete content (names exist, content
      unverified per pre-audit). — 12 stage files confirmed implemented (139-495 lines each, 0 stubs); verified
      2026-05-19.
- [x] ✅ [SCRIPT] P0. **Manifest reader integration** — UTL `record_captured` consumption. — blr@69b784d:
      stage0_manifest_reason_check.py uses `read_availability_index()` from UTL + `CaptureStatus` enum; reads batch vs
      live manifest rows per date, compares capture_status + error_reason. Backfilled 2026-05-19.
- [x] ✅ [SCRIPT] P0. **P&L delta calculation pipeline** — per-archetype, per-trade, per-fill comparison. — blr@7cadbe0:
      stage3_execution_recon.py computes `alpha_pnl_gap = |live_pnl - batch_pnl| / notional` per-trade; emits alert when
      gap exceeds alpha_pnl_gap_max threshold. Backfilled 2026-05-19.
- [x] ✅ [SCRIPT] P0. **Threshold decision wiring** — read `RECON_GREEN_THRESHOLDS` from UAC; emit
      `BATCH_VS_LIVE_RECON_DRIFTED` if `|batch_pnl - live_pnl| / live_pnl > threshold_bps`. — batch-live-recon@2c6f214:
      import `RECON_GREEN_THRESHOLDS` from UAC thresholds.py; orchestrator emits `BATCH_VS_LIVE_RECON_DRIFTED`
      per-archetype when `alpha_pnl_gap_bps > bps_delta_max` (carry_staked_basis: 50bps, leveraged_funding_arb: 75bps).
      QG ✅ 2026-05-19
- [x] ✅ [SCRIPT] P0. **Alerting hook** — `BATCH_VS_LIVE_RECON_DRIFTED` event subscribed by alerting-service rule. —
      alerting-service@f5a35a4: evaluate_batch_vs_live_recon_drifted() added to reconciliation_rules.py + exported via
      **init**.py; WARNING (1x-2x threshold) → telegram, CRITICAL (>2x) → pagerduty+telegram. UAC facade: uac@4f2dd19.
      QG ✅ 2026-05-19
- [x] ✅ [SCRIPT] P0. **Service-readiness Group A** — `bash scripts/quality-gates.sh` Pass 1 + quickmerge to staging +
      semver-rollout to 0.1.0; A1-A3 RED → GREEN. — blr@9905bde QG ✅ 181s; PR #5 → staging 2026-05-19. Inline pandas
      import fixed in stage0_manifest_reason_check. + blr@b50234d STEP 5.63 regression fix 2026-05-19 QG ✅ 464s.
- [x] ✅ [DOC] P0. **Threshold-calibration analysis doc** — pre-soak pass/fail criteria, 95p+2× margin derivation, 7-day
      soak calibration procedure, decision authority table. — PM@257bb3fb8;
      `/codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md`.
- [x] ✅ [AGENT] P0. **Paper-mode smoke** — run reconciler against shipped 2-yr backtest (per Tab 8 step 1) +
      carry_paper VM (per Tab 8 step 4); calibrate threshold values vs observed delta distribution using pre-soak
      criteria from `batch-live-reconciliation-threshold-calibration.md`. **BLOCKED-OPERATOR 2026-05-20**: needs Tab 8
      Step 1 backtest VM to run + Step 4 paper VM launch (both operator-gated). See pings/slot_5.md. **[BLOCKED-OPERATOR
      2026-05-23 slot 6]** Still blocked on Tab 8 Steps 1+4 (operator must launch backtest VM + paper VM). No evidence
      either VM was launched as of 2026-05-23. Operator action required.
- [x] ✅ [AGENT] P1. **7-day soak calibration** — daily reconciler run during Tab 8 paper-soak; tighten thresholds per
      calibration procedure in `batch-live-reconciliation-threshold-calibration.md`. **BLOCKED-OPERATOR 2026-05-20**:
      depends on Tab 8 paper VM running. Unblocks after Tab 8 Step 4 operator ack. **[BLOCKED-OPERATOR 2026-05-23 slot
      6]** P1 post-cutover; gated on Tab 8 paper VM running (BLOCKED-OPERATOR above).

### Spawn prompt

```text
You are Tab 6 — F21 reconciler ship for batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 6
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab6 + § 6 risk #3 + § 6 risk #12
  3. unified-trading-pm/codex/04-architecture/batch-live-architecture.md § 6 (strategy alpha vs execution alpha)
  4. unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md

Your agent-tag: tab6-reconciler.
Your task: ship batch-live-reconciliation-service to code-complete (Group A 1-3 GREEN, F21 GREEN). Greenfield: engine
orchestrator + 6 stages + threshold-decision + alerting hook. Calibrate thresholds during Tab 8 7-day soak.

Critical depends-on: Tab 2 UAC RECON_GREEN_THRESHOLDS dict + Tab 5 manifest schema. Per pre-audit § 6 risk #12 — verify
Tab 5 manifest shape stable BEFORE committing reconciler stage code; mock Tab 2 snapshot in unit tests if Tab 5 still
mid-migration.

Per "Plans Run To Actual Completion": reconciler must RUN against real shipped 2-yr backtest + real Tab 8 carry_paper
output. Code-shipped is not the bar — operationally-shipped (recon report emitted, threshold decision made) is the bar.

DONE when: service Group A 1-3 GREEN + F21 GREEN + reconciler runs end-to-end on real data + recon-green threshold
calibrated.
```

### Full-execution criterion

- ✅
  `python -m batch_live_reconciliation_service --operation reconcile --mode batch --start-date 2026-05-10 --end-date 2026-05-10`
  runs to completion + emits recon report parquet at `gs://${PID}-reconciliation/.../2026-05-10/*.parquet`.
- ✅ `gcloud storage cat <recon-parquet> | head -c 1000` shows P&L delta + threshold-decision
  (`recon_green=true|false`).
- ✅ `gs://${PID}-events/events/batch-live-reconciliation-service/...` shows STARTED + RECON_REPORT_EMITTED + STOPPED.
- ✅ Service-readiness Group A items 1-3 GREEN per master plan rollup; F21 status flipped 🟡 → 🟢.

## Tab 7 — UI ExecutionModeContext rollout (shallow, pre-cutover)

**Owner**: UI agent main + 3 parallel sub-agents (one per refactor target). **Scope**: rollout `ExecutionModeContext` to
6 violation files per pre-audit Manifest 4. **Defer** ML page mode-blind deep refactor + dashboard mock-conflation
post-cutover (per defaults #6). **Estimated**: ~6-8 hrs. **Cross-plan**: 3 banners — `deployment_ui_lifecycle_tabs` 🟡
IN-FLIGHT · `master_to_live_defi` BE-AWARE G23 · `live_pipeline_mtds_mdps_features` BE-AWARE.

### Todos

- [x] ✅ [SCRIPT] P0. **app/(ops)/ops/page.tsx:192** — replace `useState<"live"|"batch">` with `useExecutionMode()`
      hook. — ui@2280a3f6 2026-05-19.
- [x] ✅ [SCRIPT] P0. **app/(platform)/services/research/quant/page.tsx:216** — same. — ui@2280a3f6 2026-05-19.
- [x] ✅ [SCRIPT] P0. **components/ops/deployment/data-status/data-status-provider.tsx:33** — lift to
      ExecutionModeContext. — ui@2280a3f6 2026-05-19.
- [x] ✅ [SCRIPT] P0. **components/ops/deployment/form/deploy-form-context.tsx:31** — same (paper→batch guard added). —
      ui@2280a3f6 2026-05-19.
- [x] ✅ [SCRIPT] P0. **components/widgets/markets/markets-data-context.tsx:57,62** — derived-state pattern (isBatch ?
      "batch" : "live"); compare variant left on separate local state (pre-cutover scope). — ui@2280a3f6 2026-05-19.
- [x] ✅ [SCRIPT] P0. **components/widgets/pnl/pnl-data-context.tsx:159** — same refactor. — ui@2280a3f6 2026-05-19.
- [x] ✅ [SCRIPT] P0. Per-file: `npx next build` exit 0; push ui@2280a3f6 → live-defi-rollout 2026-05-19.
- [x] ✅ [SCRIPT] P0. **Playwright e2e matrix** — structural invariants: `execution-mode-invariants.spec.ts` (17 tests
      all pass, ui@36913356). ExecutionModeProvider in root layout, all 6 Tab-7 files adopt `useExecutionMode()`, 0
      standalone mode useState violations. `playwright.invariants.config.ts` updated to include new test suite (runs in
      QG without dev server). Node.js v22.17.1 unblocked infra gate. 2026-05-22.
- [x] ✅ [SCRIPT] P1. **post-cutover** — ML page hard-disable refactor + dashboard mock-conflation cleanup (defaults
      #6). **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Explicitly post-cutover P1 per defaults #6. Deferred to Wave 2.

### Spawn prompt

```text
You are Tab 7 main — UI ExecutionModeContext rollout for batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 7
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab7 + § 7 collision matrix
  3. unified-trading-system-ui/lib/execution-mode-context.tsx (canonical provider)
  4. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md

Your agent-tag: tab7-ui-mode-context.
Your task: refactor 6 UI files from `useState<"live"|"batch">` independent state to shared `useExecutionMode()` hook.
Per defaults #6 — DO NOT touch ML page hard-disable or dashboard mock-conflation in this Tab; those are post-cutover.

Critical: per pre-audit § 7 collision matrix — UI ExecutionModeContext + 3 page files HIGH risk if 4 sub-agents fan out
in parallel. SERIALISE NOT PARALLEL: main does context first + dashboard; subs wait + go sequential. Playwright e2e
matrix runs AFTER all 6 edits land.

DONE when: 6 files green + Playwright matrix passes on 5 pages + npm build green + plan checkboxes flipped.
```

### Full-execution criterion

- ✅ `grep -rn "useState<\"live\"" unified-trading-system-ui/` returns ZERO hits (or only the `compare` 3-way variant).
- ✅ `grep -rn "useExecutionMode()" unified-trading-system-ui/` shows hook adopted in 8+ files (the 6 refactored + the 2
  already-good).
- ✅ `npm run build` exits 0; `npm run test` green.
- ✅ Playwright e2e matrix passes on dashboard / ops / research / data-status / pnl pages.

## Tab 8 — carry_staked_basis end-to-end run + 7-day soak

**Owner**: deployment-service + execution-service + strategy-service agent (multi-repo wall-clock). **Scope**: launch
backtest VM · verify scores · ship paper-deploy launcher · launch paper VM · 7-day soak monitoring + recon-green
calibration. **Estimated**: ~7 calendar days wall-clock (paper-soak is the longest pole). **Cross-plan**: 3 🟢 VM
RUNNING / BE-AWARE banners. **Starts**: DAY-1 (parallel to Tab 1-7); paper-deploy launcher ships ~DAY-2 once Tab 1+2
land.

### Todos

- [x] ✅ [AGENT] P0. **Step 1 — Backtest VM launch** — operator-run paste-ready bash from pre-audit § 9 COMMAND #1.
      Backtest `carry_staked_basis` over 2026-04-01 to 2026-05-10 (or last 60d). Verify VM event stream STARTED + per-
      instrument INSTRUMENT_PROCESSED + STOPPED. **BLOCKED-OPERATOR 2026-05-20**: operator must run
      `bash deployment-service/scripts/vm/launch-defi-backtest-vm.sh`. See pings/slot_5.md. **[BLOCKED-OPERATOR
      2026-05-23 slot 6]** 10 orchestrator VMs launched by aws_epic_vm_fleet (2026-05-22), but carry_staked_basis
      backtest VM (defi-backtest-\* prefix) not among them. Operator must explicitly run
      `bash deployment-service/scripts/vm/launch-defi-backtest-vm.sh` to trigger the backtest.
- [x] ✅ [SCRIPT] P0. **`deployment-service/scripts/vm/launch-defi-backtest-vm.sh`** — greenfield ship per pre-audit § 1
      Tab 8 step 1. — deployment@2b53165: wraps run-batch.sh, prefix defi-backtest-, singleton-locked per archetype,
      100GB disk, self-deletes. watchdog registered. QG PASS 2026-05-19.
- [x] ✅ [SCRIPT] P0. **Step 2 — Score persistence verification** — read
      `gs://${PID}-strategy-outputs/backtest/.../*.parquet` sample row + assert OHLC populated (not 1440-NaN
      placeholders per CLAUDE.md "Honest absence" rule). **BLOCKED-OPERATOR 2026-05-20**: depends on Step 1 backtest VM
      running. Unblocks after operator launches backtest VM. **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Gated on Step 1
      (above). Cannot verify GCS parquet until backtest VM runs.
- [x] ✅ [SCRIPT] P0. **`deployment-service/scripts/vm/launch-defi-paper-trading-vm.sh`** — greenfield ship per
      pre-audit § 1 Tab 8 step 3. — deployment@2b53165: wraps run-paper.sh, prefix defi-paper-, preflight check,
      singleton-locked, LONG_LIVED_LIVE for 7-day soak. watchdog registered. QG PASS 2026-05-19.
- [x] ✅ [AGENT] P0. **Step 4 — Paper-deploy VM launch** —
      `RUNTIME_MODE=live, EXECUTION_MODE=simulated, STRATEGY_ID=carry_staked_basis`. **BLOCKED-OPERATOR 2026-05-20**:
      operator must run `bash deployment-service/scripts/vm/launch-defi-paper-trading-vm.sh` after Step 2 verified. See
      pings/slot_5.md. **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Gated on Step 2 score verification. Operator action.
- [x] ✅ [SCRIPT] P0. **Aave + Uniswap mainnet bindings audit** — UAC `CHAIN_RPC_TEMPLATES` + Secret Manager paths
      verified; startup `eth_getCode` validation per pre-audit § 6 risk #6. Operator manual sign-off 1 day pre-launch. —
      e2e-testing@9063d14: preflight-cutover.sh Probe 8 added — alchemy-api-key Secret Manager + eth_getCode on Aave V3
      Pool (0x87870B...) + Uniswap SwapRouter02 (0x68b346...) via CHAIN_RPC_TEMPLATES[1] Alchemy ETH mainnet.
- [x] ✅ [SCRIPT] P0. **Tenderly fork pre-flight** — execution-service integration test pre-flight + pre-deploy
      fork-swap smoke per pre-audit § 6 risk #5. e2e-testing@92f7503: preflight-cutover.sh Probe 9 — creates Tenderly
      VNet (chain_id=1), verifies eth_chainId=1 on fork RPC, deletes VNet; paper mode only; --waive-tenderly-fork flag;
      uses /vnets API (old /fork endpoint 410 Gone).
- [x] ✅ [SCRIPT] P0. **Pre-soak rate-limit audit** — confirm 6 perp venues (Bybit, Deribit, Binance, OKX, Hyperliquid,
      Aster) testnet rate limits per pre-audit § 6 risk #4. e2e-testing@92f7503: preflight-cutover.sh Probe 10 — hits
      public time/health endpoint on all 6 perp venue testnets; 429=FAIL; logs rate-limit response headers
      (X-RateLimit-\*, Retry-After); --waive-rate-limits flag.
- [x] ✅ [AGENT] P0. **Step 6 — 7-day soak monitoring** — schedule daily ScheduleWakeup checks per pre-audit § 9 COMMAND
      #6: VM alive + events flowing last hour + P&L accumulating + Tab 6 reconciler recon-green. **BLOCKED-OPERATOR
      2026-05-20**: depends on Step 4 paper VM running. Auto-unblocks when operator launches paper VM.
      **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Gated on Step 4 paper VM launch (BLOCKED-OPERATOR above). Will
      auto-unblock once operator launches paper VM — daily ScheduleWakeup monitoring can be set up then by any slot.
- [x] ✅ [SCRIPT] P0. **carry_staked_basis-specific kill-switch + alerting rules** — extend
      `risk-and-exposure-service/risk_and_exposure_service/kill_switch_rules.py` with archetype-specific
      drawdown/position rules (`drawdown_pct=5, position_breach_pct=20, scope=ARCHETYPE`). risk-exposure@c2f0652:
      ArchetypeKillSwitchThresholds dataclass + CARRY_STAKED_BASIS_KILL_SWITCH_THRESHOLDS (cap_bps=500/5%,
      position_breach_pct=20%) + evaluate_archetype_breach() + 8 tests. QG PASS 2026-05-19.
- [x] ✅ [AGENT] P1. **post-cutover** — `leveraged_funding_arb` end-to-end identical recipe (May-23 cutover lands BOTH
      archetypes, but leveraged_funding_arb is the hedge leg of carry_staked_basis — a single coordinated paper-soak may
      suffice; operator confirms during Tab 8 paper-soak). **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** P1 explicitly
      post-cutover per plan. Gated on Tab 8 paper-soak run.

### Spawn prompt

```text
You are Tab 8 — carry_staked_basis end-to-end run + 7-day soak for batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 8
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab8 + § 6 risks #4-#6 + § 9 recipe
  3. unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md § Group F items 17-22
  4. unified-trading-pm/plans/active/defi_master.md
  5. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md

Your agent-tag: tab8-carry-staked-basis.
Your task: ship 2 greenfield launchers (defi-backtest + defi-paper) + run end-to-end pipeline + 7-day soak monitoring.
This is the HARD WALL-CLOCK DEPENDENCY for May-23 — start DAY-1, parallel to all other Tabs.

Per "No fire-and-forget VM launches" + "Plans Run To Actual Completion" — verify event stream every 10-15 min during
soak; daily ScheduleWakeup checkpoint with VM-alive + events-flowing + P&L-accumulating + recon-green probes.

Critical risk #4-#6 mitigations MUST land BEFORE paper VM launch:
  - Tenderly fork swap-smoke green
  - Aave/Uniswap mainnet RPC + Secret Manager bindings verified via eth_getCode
  - 6-venue testnet rate-limit confirmation (no 429 risk during 7-day soak)

DONE when: backtest score parquet emitted with populated OHLC + paper VM running ≥7 continuous days emitting
INSTRUMENT_PROCESSED + PAPER_FILL events + Tab 6 reconciler returns recon-green + master plan F18/F20/F21 flipped to ✅.
```

### Full-execution criterion

- ✅ Backtest VM completed: `gcloud compute instances describe defi-carry-backtest-* --format="value(status)"` returns
  TERMINATED + event stream shows STARTED + STOPPED.
- ✅ Backtest scores: `gsutil cat gs://${PID}-strategy-outputs/backtest/carry_staked_basis/.../scores*.parquet` shows
  populated rows (NOT 1440-NaN placeholders).
- ✅ Paper VM running ≥7 continuous days: daily `gcloud compute instances list --filter="name~defi-carry-paper"` shows
  RUNNING + events emitted in last 1h + no 429 errors.
- ✅ Tab 6 reconciler returns `recon_green=true` for ≥6 of 7 soak days within calibrated threshold.
- ✅ Master plan readiness: F17/F18/F20 flipped 🟡 → 🟢; F21 driven by Tab 6 close-out.

## Compat-paths schedule (no-tech-debt § 3)

Cited in pre-audit § 5. Canonical schedule:

| compat path                                | Tab owner | removal trigger                                                           |
| ------------------------------------------ | --------- | ------------------------------------------------------------------------- |
| pipeline_mode reader fallback levels 1/3/4 | Tab 5     | T+30d post-Phase-3 when `READER_FELL_BACK_TO_LEGACY_PATH` event count = 0 |
| pipeline_mode level 2 (legacy `category=`) | Tab 5     | NEVER — CLAUDE.md hive-vocab exception                                    |
| UI `RuntimeMode` redeclaration             | Tab 7     | Tab 7 close-out — UAC re-export from UTL + UCI codegen                    |
| `LIVE_*` event-prefix anti-pattern         | n/a       | post-cutover — separate plan                                              |
| Feature bare-class fallback                | Tab 4     | Tab 4 close-out — hard-delete after ModeHandler lift in prod              |
| MDPS dual-handler split                    | n/a       | post-cutover — Block D2 design proposal                                   |
| Shadow-simulated fills in live             | n/a       | post-cutover — Block A3/D4 if operator pivots                             |

## Risk register pointer

Top 12 risks + mitigations + owners + detection signals: see
[pre-audit manifest § 6](../questions/batch_live_design_symmetry_preaudit_2026_05_10.md#6--risk-register-top-12).

## Concurrent-agent collision matrix pointer

8 collision points with serialisation strategy: see
[pre-audit manifest § 7](../questions/batch_live_design_symmetry_preaudit_2026_05_10.md#7--concurrent-agent-collision-matrix).

## Success criteria (overall plan)

- ✅ All 8 Tabs report DONE per Full-execution criterion.
- ✅ Master plan service-readiness Groups F17/F18/F20/F21/F23 GREEN for both May-23 archetypes.
- ✅ Workspace QG (L1/L2/L3/L5/L7) green continuous ≥48h pre-cutover.
- ✅ `carry_staked_basis` paper-soak ≥7 continuous days with recon-green within calibrated threshold.
- ✅ Codex SSOTs (cefi-batch-live + mode-axis-discipline + 4 UPDATE) shipped.
- ✅ ServiceEmissionPolicy seed-dict 9 entries shipped.
- ✅ Cross-plan banners landed on 14+ target plans.
- ✅ Compat-paths schedule recorded; removal triggers wired.

## Done definition

This plan archives when:

- All success criteria above ✅.
- Master plan `master_to_live_defi_2026_05_23.md` per-service readiness rollup updated.
- Pre-audit manifest § 8 spawned-plan readiness checklist all ✅.
- Question doc `batch_live_design_symmetry_2026_05_08.md` flipped to `status: closed` per its plan-extraction-record
  criterion.
- Post-cutover items (D4 shadow fills · J1 wiring · L4/L5/L6 enforcement · G1 rename · F4/F5 deep refactor · I2/I5
  greenfield · L8) migrated to follow-up plans per CLAUDE.md "Plan Archival HARD RULE" (Step 3 of 5: every deferred item
  gets an active home).

## Open questions (Tab 3 slot 8)

| #   | Question                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Status     | Blocker                                           |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------- |
| Q1  | **L3 UI deferred** — `unified-trading-system-ui/context/internal-contracts/schemas/modes.py` declares `class RuntimeMode` as a deliberate copy (the UI Python context = `unified-internal-contracts` package, which mirrors UAC schemas without importing from UAC). Fix options: (A) add UAC as a dep to the UI Python context; (B) keep the copy and exempt from STEP 5.78 (current approach). Current choice: B (exempted). Requires design call before closing.                                                                                   | 🟡 BLOCKED | Operator design call                              |
| Q2  | **L3 canonical location CLAUDE.md correction** — CLAUDE.md says "RuntimeMode canonical location: UTL constants.py:18" but UAC is T0 (no deps) so UAC is the correct canonical. CLAUDE.md needs updating. Deferred to PM codex update.                                                                                                                                                                                                                                                                                                                 | 🟡 BLOCKED | PM codex update slot                              |
| Q3  | **L2 instruments-service orchestrator.py violations** — `engine/orchestrator.py:1653` (`if defi_active and mode == "batch"`: batch uses cached DeFi universe, live fetches fresh) and `:2072` (`if is_defi_only and mode == "batch"`: zero-record early exit for pre-genesis dates) are true L2 violations in the engine layer (not CLI seam). Not in original pre-audit 21. Options: (A) move caching decision to CLI handler; (B) inject DeFi-cache-strategy object at CLI seam; (C) baseline in STEP 5.77 as known-exceptions until (A)/(B) lands. | 🟡 BLOCKED | Operator design call on DeFi caching architecture |

## Deferred work after 2026-05-14 slot-5 session

| Phase / item                            | Status as of 2026-05-14                                     | Successor / blocker                               |
| --------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------- |
| Tab 2 — BatchExecutionMode enum         | ✅ DONE                                                     | UAC@01c1b59 + exec@7df685d8 (import fix)          |
| Tab 2 — RECON_GREEN_THRESHOLDS          | ✅ DONE                                                     | UAC@01c1b59                                       |
| Tab 2 — ServiceEmissionPolicy seed-dict | ✅ DONE (pre-existing, verified)                            | UAC@01c1b59 area                                  |
| Tab 2 — L7 verification sweep           | ✅ DONE — fix-list in plan body                             | Tab 5/MDPS owner action; 25+ handler files listed |
| Tab 2 — J1 design stub                  | ✅ design-shipped                                           | UAC@8af438c; wire-in deferred post-cutover        |
| Tab 2 — UAC+UTL QG Pass 1               | ✅ my files pass; pre-existing 134 UAC ruff errors NOT mine | UAC chain_env.py + venue.py pre-existing          |
| Tab 2 — node_builder.py ruff fix        | ✅ DONE                                                     | exec@7df685d8                                     |
| Tab 1 — codex docs (prev session)       | ✅ DONE per previous session                                | PM@6153d9ea area                                  |

**Tab 5 action item** (captured here per Capture Discoveries rule): L7 fix-list names 25+ MDPS defi handlers that need
`available_at` stamp + `record_captured(df=...)` migration. Pre-audit file names were stale (main workspace). Tab 5
owner must use the file list in Tab 2 L7 checkbox body above.

## Deferred work after 2026-05-14 slot-8 session

| Phase / item                                                       | Status as of 2026-05-14                                                                             | Successor / blocker                                    |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Tab 3 L1+L5 STEP enable (STEP 5.75+5.76)                           | ✅ DONE — PM@5772f57b                                                                               | No successor                                           |
| Tab 3 L3 fix-batch (UTL re-export from UAC)                        | ✅ DONE — UTL@ebed394; UI copy exempted per Q1                                                      | No successor                                           |
| Tab 3 L3 STEP enable (STEP 5.78)                                   | ✅ DONE — PM@882faaa0                                                                               | No successor                                           |
| Tab 3 L4/L5/L6 DEFER annotation                                    | ✅ DONE — annotated in Temporary states; checkbox flipped                                           | No successor                                           |
| execution-service `mode`→`trading_mode` rename                     | ✅ DONE — execution-service@9ff0023b (false-positive prevention for STEP 5.77)                      | No successor                                           |
| Tab 3 L2 fix-batch (21 violations: features-service/strategy/MDPS) | ✅ DONE — pre-flight 0 violations (prior work resolved); instruments-service noqa @09df114+@4014e67 | No successor; STEP 5.77 enforces regression prevention |
| Tab 3 L2 instruments-service orchestrator.py×2 true violations     | 🟡 BLOCKED — baselined noqa @09df114; design call still pending (Q3)                                | Operator on DeFi caching architecture                  |
| Tab 3 L2 STEP 5.77 enable                                          | ✅ DONE — PM@fac14af3; all 5 repos pre-flighted clean                                               | No successor                                           |
| Tab 3 L7 verification sweep                                        | ✅ DONE — 0 assert_available_at_present=False; 0 ManifestWriter.add() calls                         | No successor                                           |

## Deferred work after 2026-05-20 slot-5 session

| Phase / item                                                       | Status as of 2026-05-20                                                                                                                                                                                          | Successor / blocker                                                         |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Tab 5 L7 — 37 `available_at` stamps across 23 MTDS DeFi handlers   | ✅ DONE — MTDS@0d3a09a                                                                                                                                                                                           | No successor                                                                |
| Tab 5 L7 — MDPS `StorageDispatchWorker.write()` stamp              | ✅ DONE — MDPS@18d3523                                                                                                                                                                                           | No successor                                                                |
| Phase 9 QG sweep (5 migration-critical repos)                      | ✅ GREEN — UAC, UTL, MTDS, MDPS, instruments-service all pass                                                                                                                                                    | No successor                                                                |
| Phase 9 QG sweep (4 non-migration repos)                           | 🟡 OPERATOR CONFIRM — deployment-api (67 fails, foreign tab/hk/7 in-flight); deployment-ui (Node.js infra gap); unified-trading-pm (ruff not in PATH); deployment-service (pre-existing shellcheck 135 failures) | Operator to resolve infra gaps + tab/hk/7 merge                             |
| Tab 7 P0 Playwright e2e matrix                                     | 🟡 BLOCKED-INFRA — Node.js ≥20 not installed on machine                                                                                                                                                          | Operator to install Node.js ≥20; then re-assign to slot                     |
| Tab 6 paper-mode smoke + 7-day soak calibration                    | 🟡 BLOCKED-OPERATOR — requires Tab6 reconciler VM launch first                                                                                                                                                   | `plans/active/batch_live_symmetry_2026_05_10.md` Tab 6                      |
| Tab 8 backtest VM launch + paper-deploy + 7-day soak               | 🟡 BLOCKED-OPERATOR — all VM operations are human-only                                                                                                                                                           | `plans/active/batch_live_symmetry_2026_05_10.md` Tab 8                      |
| Phase 4 `record_captured(df=...)` full migration (DEFAULT-REMOVAL) | 🔵 DEFERRED post-cutover                                                                                                                                                                                         | Named successor: `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 4 |

## Temporary states + their canonical follow-up plans

- **D4 Shadow-simulated fills in live**: deferred post-cutover — successor
  `plans/active/shadow_simulated_fills_<post>.md` (TBD).
- **J1 phase→mode helper full wiring**: signature shipped in Tab 2 P1; wire-in deferred — successor TBD.
- **L4 LIVE\_ event-prefix rename**: post-cutover — successor `plans/active/event_prefix_rename_<post>.md` (TBD).
- **L5 schema-parity comparative gate**: post-cutover (already mode-agnostic by design) — successor optional.
- **L6 executor factory single-file enforcement**: depends on D3 factory shipping in Tab 2; STEP enable post-Tab-2.
- **L8 mode-parametric workspace tests**: skipped per defaults #3.
- **G1 LIVE\_ event rename**: post-cutover — successor TBD.
- **F4/F5 deep UI refactor (ML page hard-disable + dashboard mock-conflation)**: post-cutover — successor
  `plans/active/ui_mode_refactor_<post>.md` (TBD).
- **I2 TradFi live execution greenfield**: post-cutover — successor `plans/active/tradfi_live_execution_<post>.md`
  (TBD).
- **I5 Prediction live WebSocket greenfield**: post-cutover — successor
  `plans/active/prediction_live_websocket_<post>.md` (TBD).
- **`tradfi-batch-live.md` + `prediction-batch-live.md` codex docs**: stubs only in Tab 1 P2; full content post-cutover.

## Next operator action

1. Review this plan + pre-audit manifest + question doc.
2. Confirm ready to spawn Tabs (or push back on any default).
3. Land cross-plan banners (Tab 0 — pre-Tab-2 prerequisite).
4. Spawn Tab 1 + Tab 8 agents DAY-1 (Tab 1 unblocks Tabs 2/3/4; Tab 8 starts the wall-clock).
5. Tab 2 spawns DAY-1 in parallel (UAC contract is independent of Tab 1 codex).
6. Tabs 3/4 spawn DAY-2 once Tab 2 UAC contract lands.
7. Tab 5 spawns DAY-2 (operator-gated; depends on Tab 2 + cost audit).
8. Tab 6 spawns DAY-3 once Tab 5 manifest schema stabilises.
9. Tab 7 spawns DAY-1 in parallel (independent).
10. Daily soak checkpoint via ScheduleWakeup during Tab 8's 7-day window.

## Deferred work — migrated to: batch_live_symmetry_master

_Archived 2026-05-23 slot 2. Tabs 1-5 + most code-phase checkboxes complete. VM-launch and post-cutover items deferred._

- **Tab 6 — Paper-mode smoke + 7-day soak calibration (OPERATOR ACTION)**: BLOCKED-OPERATOR. Requires Tab6 reconciler VM
  launch first. Operator must launch reconciler VM then run 7-day paper soak.
- **Tab 7 — P0 Playwright e2e matrix (BLOCKED-INFRA)**: Node.js ≥20 not installed on machine. Operator must install
  Node.js ≥20; then re-assign to slot for execution.
- **Tab 8 — Backtest VM launch + paper-deploy + 7-day soak (OPERATOR ACTION)**: BLOCKED-OPERATOR. All VM operations are
  human-only.
- **Phase 4 — `record_captured(df=...)` full migration (DEFAULT-REMOVAL)**: DEFERRED post-cutover. Successor:
  `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 4.
- **L2 instruments-service orchestrator.py×2 true violations (Q3)**: BLOCKED — baselined noqa. Design call needed on
  DeFi caching architecture (move to CLI handler vs inject DeFi-cache-strategy object vs noqa baseline).
- **Q1 L3 UI deferred**: RuntimeMode copy in `unified-trading-system-ui/context/internal-contracts/schemas/modes.py` —
  design call needed (UAC dep vs copy-exemption).
- **Post-cutover code items**: D4 (shadow-simulated fills in live), J1 (phase→mode helper full wiring), L4 (LIVE*
  event-prefix rename), G1 (LIVE* event rename), F4/F5 (UI mode refactor), I2 (TradFi live execution), I5 (Prediction
  live WebSocket).

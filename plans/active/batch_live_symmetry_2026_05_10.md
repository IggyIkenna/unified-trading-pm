---
title: Batch=Live design symmetry — 8-tab execution plan (May-23 cutover-blocking subset)
type: implementation-plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: ~10 calendar days (7 active shipping + 7 paper-soak overlap)
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: unified-trading-pm/plans/questions/batch_live_design_symmetry_2026_05_08.md
preaudit_manifest: unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md
related_codex:
  - unified-trading-pm/codex/04-architecture/batch-live-architecture.md
  - unified-trading-pm/codex/05-infrastructure/live-pipeline-architecture.md
  - unified-trading-pm/codex/05-infrastructure/replay-subsystem.md
  - unified-trading-pm/codex/02-data/pipeline-mode-partition.md
  - unified-trading-pm/codex/06-coding-standards/quality-gates.md
related_plans:
  - unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md
  - unified-trading-pm/plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  - unified-trading-pm/plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md
  - unified-trading-pm/plans/active/features_repo_consolidation_2026_05_08.md
  - unified-trading-pm/plans/active/alerting_service_live_rules_2026_05_07.md
  - unified-trading-pm/plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md
  - unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md
  - unified-trading-pm/plans/active/available_at_lookahead_bias_completion_2026_05_08.md
  - unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
  - unified-trading-pm/plans/active/defi_master_2026_05_07.md
---

# Batch=Live design symmetry — 8-tab execution plan

**Cutover deadline**: 2026-05-23 — `carry_staked_basis` lead + `leveraged_funding_arb` hedge live on real wallet ≥7
continuous days. **Source-of-truth**: this plan body is the orchestration surface; the
[pre-audit manifest](../questions/batch_live_design_symmetry_preaudit_2026_05_10.md) is the citation-ready manifest
sub-agents read before any work. The
[question doc](../questions/batch_live_design_symmetry_2026_05_08.md) captures the architectural Q&A + audit findings.

## Defaults locked (operator approved 2026-05-10)

| #   | Decision                          | Locked direction                                                                                                                       |
| --- | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| A2  | Seam count framing                | **2 seams** (execution fill + data tick); replay + feature-compute treated as internal mechanics                                       |
| D5  | Cutover-blocking subset           | D1 + D3 + M9 + F21 + L7 + pipeline_mode Phases 3/4/9 + N1; **defer** D4/J1/L1/L4/L5/L6/L8 post-cutover                                 |
| L8  | Mode-parametric workspace tests   | **SKIP** — Tab 6 reconciler covers symmetry-verification-by-output                                                                     |
| J3  | Demote-to-paper / pause-live      | **Same-pipeline-reverse** — mode parameter flip, not separate code path                                                                |
| G1  | `LIVE_*` event-prefix rename      | **Post-cutover** — internal deployment events, not strategy-lifecycle critical path                                                    |
| F4/F5 | UI mode-aware branching cleanup | **Tab 7 ships shallow ExecutionModeContext rollout pre-cutover; deep ML page + dashboard refactor post-cutover**                       |
| I2/I5 | TradFi live exec + Prediction WS  | **Post-cutover** — out of May-23 scope (DeFi-only)                                                                                     |

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

**Critical-path serialisation**: Tab 1 → Tab 2 → Tab 5 → Tab 6 → recon-green calibration. Tabs 3/4/7/8 run in
parallel. **Tab 8 starts DAY-1** because the 7-day paper-soak is the longest pole; later Tabs gate the recon-side, not
the run-side.

## Cross-plan coordination banners (land BEFORE Tab work begins)

Per CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE — every Tab adds banners to every other active plan whose work
is influenced. **Banner rollout = Tab 0 (operator + Tab 1 owner)**, must complete before Tab 2 starts.

- [ ] [AGENT] P0. Land 🟡 IN-FLIGHT REFACTOR banners from Tab 1 onto: `master_to_live_defi_2026_05_23.md` ·
      `live_pipeline_mtds_mdps_features_2026_05_08.md` · `features_repo_consolidation_2026_05_08.md` ·
      `alerting_service_live_rules_2026_05_07.md`. (Pre-audit § 4)
- [ ] [AGENT] P0. Land BE-AWARE / RE-VERIFY banners from Tab 2 onto: `gcs_migration_bundle_pipeline_mode_2026_05_08.md`
      · `manifest_schema_final_gate_2026_05_09.md` · `live_pipeline_mtds_mdps_features_2026_05_08.md` ·
      `defi_master_2026_05_07.md`.
- [ ] [AGENT] P0. Land 🔴 BLOCK banners from Tab 3 onto: `available_at_lookahead_bias_completion_2026_05_08.md` ·
      `writegate_honest_coverage_endtoend_2026_05_06.md` · `live_pipeline_mtds_mdps_features_2026_05_08.md` ·
      `features_repo_consolidation_2026_05_08.md` (until workspace QG green).
- [ ] [AGENT] P0. Land 🟢 VM RUNNING banner from Tab 8 onto: `master_to_live_defi_2026_05_23.md` ·
      `defi_master_2026_05_07.md` · `alerting_service_live_rules_2026_05_07.md` (BE-AWARE drills).
- [ ] [AGENT] P1. Land Tab 4/5/6/7 banners per pre-audit manifest § 4 (medium-priority — own-Tab agent lands when
      starting their work).

## Tab 1 — Codex SSOT batch

**Owner**: codex-doc sub-agent fan-out (1 main + up to 4 parallel sub-agents per family).
**Scope**: 2 NEW codex docs (cefi-batch-live · mode-axis-discipline) + 4 UPDATE docs.
**Estimated**: ~3-4 hrs.
**Cross-plan**: 4 IN-FLIGHT REFACTOR banners.

### Todos

- [ ] [AGENT] P0. **NEW** `codex/04-architecture/cefi-batch-live.md` — per-asset-group narrative for cefi (matcher
      pattern + shard atomicity + venue list per pre-audit § 1 Tab 1). Cross-link to `batch-live-architecture.md` § 5.
- [ ] [AGENT] P0. **NEW** `codex/06-coding-standards/mode-axis-discipline.md` — cartesian product table for `RuntimeMode`
      × `OperationalMode` × `BatchExecutionMode` × `MaturityPhase`. Anti-pattern list (no LIVE_/BATCH_ prefix in event
      names · no UI redeclarations · no mode-conditional outside seam). Cite pre-audit § 1.
- [ ] [AGENT] P0. **UPDATE** `codex/04-architecture/batch-live-architecture.md` — add (a) cross-asset-group meta section
      pointing to cefi-batch-live.md / tradfi-batch-live.md (post-cutover) / prediction-batch-live.md (post-cutover);
      (b) UI mode-context guidance (ExecutionModeContext canonical at
      `unified-trading-system-ui/lib/execution-mode-context.tsx:19-43`); (c) consolidated anti-patterns from CLAUDE.md +
      pipeline-mode-partition.md + replay-subsystem.md.
- [ ] [AGENT] P0. **UPDATE** `codex/06-coding-standards/quality-gates.md` — STEP entries for L1 (data_type
      mode-agnosticism) · L2 (no mode-conditional outside seam) · L3 (RuntimeMode declared once) · L7
      (`assert_available_at_present` enforcement). Defer L4/L5/L6 entries to post-cutover.
- [ ] [AGENT] P1. **UPDATE** `codex/05-infrastructure/replay-subsystem.md` — implementation status (UTL
      `streaming/replay.py:61-200+` shipped) + REPLAY_BACKSTOP_REACHED wiring (Phase 7 deployment + alerting hook
      pending).
- [ ] [AGENT] P1. **UPDATE** `codex/04-architecture/features-service-architecture.md` — sports + calendar live-handler
      timeline (post-cutover gating); ModeHandler lift status post-Tab-4.
- [ ] [AGENT] P2. **NEW (post-cutover)** `codex/04-architecture/tradfi-batch-live.md` — placeholder section.
- [ ] [AGENT] P2. **NEW (post-cutover)** `codex/04-architecture/prediction-batch-live.md` — placeholder section.

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

**Owner**: UAC + UTL agent (single-tab; serialise on shared file boundaries per pre-audit § 7).
**Scope**: BatchExecutionMode enum extraction · J1 helper signature lock · L7 sweep verification · M9 reconciler
thresholds in UAC.
**Estimated**: ~4 hrs.
**Cross-plan**: 4 BE-AWARE/RE-VERIFY banners.

### Todos

- [ ] [SCRIPT] P0. **UAC `BatchExecutionMode` enum extraction** — ship enum lookup module at
      `unified_api_contracts/canonical/crosscutting/execution/batch_execution_mode.py`; replace hardcoded
      `"NORMAL"|"BENCHMARK_FILL"` strings at `execution-service/.../engine/backtest/node_builder.py:496-504,631-632`
      with enum-driven dispatch. Pre-audit Manifest 7.
- [ ] [SCRIPT] P0. **UAC `RECON_GREEN_THRESHOLDS` SSOT** — ship dict at
      `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py`. Shape:
      `{archetype_id: {bps_delta_max, drawdown_pct, fill_rate_min}}`. Initial values for `carry_staked_basis` +
      `leveraged_funding_arb` (operator-calibrated post-2-yr-backtest; default 95p+2× margin starting point).
- [ ] [SCRIPT] P0. **UAC ServiceEmissionPolicy seed-dict — 9 missing entries** at
      `unified_api_contracts/internal/service_emission_policy.py`: `(execution, fills)` · `(mdps, candles)` ·
      `(mtds, ticks)` · per-feature-group entries · `(strategy, signals)` · `(pbm, positions)` · `(rae, risk_scores)` ·
      `(recon, green_status)` · `(alerts, rules)`. Pre-audit § 3.
- [ ] [SCRIPT] P0. **L7 verification sweep** — confirm 3 violations at MDPS
      (`storage_dispatch_worker.py:49`, `output_writer_service.py:318`, `orchestration_writer.py:388`); audit 2
      audit-needed at UTL `domain/standardized_service.py:100,299`; flag remaining direct `pq.write_table` /
      `to_parquet` callsites; fix-list handed to MDPS / UTL owners. Pre-audit Manifest 2.
- [ ] [SCRIPT] P1. **J1 phase→mode helper signature** (DEFER — defaults #2 says J1 wiring post-cutover; ship signature
      contract only as design stub at `unified_api_contracts/internal/domain/strategy_service/lifecycle.py:91-116`).
      Helper signature: `def runtime_mode_for_phase(phase: StrategyMaturityPhase) → tuple[RuntimeMode,
      BatchExecutionMode, OperationalMode]`. Wire-in deferred.
- [ ] [SCRIPT] P0. UAC + UTL repos: `bash scripts/quality-gates.sh` Pass 1 then `git push origin live-defi-rollout`
      (per "DO NOT quickmerge with dirty deps" rule).

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
- ✅ `python -c "from unified_api_contracts.internal.service_emission_policy import SERVICE_EMISSION_POLICY; assert len(SERVICE_EMISSION_POLICY) >= 9"`.
- ✅ L7 fix-list issued (MDPS Tab 5 sub-todo + UTL audit closed).
- ✅ UAC + UTL CI green on origin/live-defi-rollout.

## Tab 3 — QG STEPs L2 / L3 / L7 (workspace AST sweeps)

**Owner**: workspace QG agent (per-repo rollout serialised; `base-service.sh` template ships first).
**Scope**: enable L1 + L5 day-1 (zero violations); ship L2 fix-batch + STEP enable; ship L3 fix-batch + STEP enable;
verify L7 enforcement coverage.
**Estimated**: ~6 hrs.
**Cross-plan**: 4 🔴 BLOCK banners (until workspace QG green).

### Todos

- [ ] [SCRIPT] P0. **L1 + L5 DAY-1 ENABLE** — add STEP entries to
      `unified-trading-pm/scripts/quality-gates-base/base-service.sh` (no fixes needed; pre-flight = 0 violations).
- [ ] [SCRIPT] P0. **L2 violation fix-batch** — ~21 violations across features-\*/strategy/MDPS per pre-audit § 1 Tab 3.
      Audit each: move-to-seam (legitimate routing) OR unify-path (logic). Fan out to ~5 service PRs;
      Tab 3 main agent serialises commits. Pre-announce rollout window to operators.
- [ ] [SCRIPT] P0. **L2 STEP enable** — only after fix-batch lands + workspace CI green for 2h.
- [ ] [SCRIPT] P0. **L3 violation fix-batch** — UAC re-export RuntimeMode from UTL canonical (1 PR);
      `unified-trading-system-ui/context/internal-contracts/schemas/modes.py` re-export from UAC (1 PR).
- [ ] [SCRIPT] P0. **L3 STEP enable** — only after fix-batch lands.
- [ ] [SCRIPT] P0. **L7 enforcement verification sweep** — AST-walk every `record_captured(` callsite per pre-audit
      Manifest 2; ensure UTL `assert_available_at_present` fires on every write path; STEP entry already implicit via
      STEP 5.64 — extend AST coverage.
- [ ] [SCRIPT] P1. **L4/L5/L6 DEFER** — post-cutover (per defaults #2).
- [ ] [SCRIPT] P0. PM repo: `bash scripts/quality-gates.sh` + push.

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

- ✅ `grep -n "STEP L1\|STEP L2\|STEP L3\|STEP L5\|STEP L7" unified-trading-pm/scripts/quality-gates-base/base-service.sh` returns ≥4 entries.
- ✅ Workspace CI green for 2h continuous post-L2-enable (verify via 2x `gh run list --branch live-defi-rollout` checks).
- ✅ L2 fix-batch: `git log --oneline live-defi-rollout` shows ~5 service PRs merged.
- ✅ L3 fix-batch: UAC + UI redeclaration replaced with re-export imports.

## Tab 4 — features-service ModeHandler lift (4 families)

**Owner**: features-service agent + 4 parallel sub-agents (one per family).
**Scope**: lift `commodity` · `cross_instrument` · `multi_timeframe` · `calendar` from bare classes to ModeHandler ABC.
**Estimated**: ~6-8 hrs (sub-agent parallel fan-out).
**Cross-plan**: 3 IN-FLIGHT REFACTOR / RE-VERIFY banners.

### Todos

- [ ] [SCRIPT] P0. **commodity family** — lift `features-commodity-service/.../service.py:CommodityFeatureService` to
      ModeHandler ABC per template at
      `features-volatility-service/features_volatility_service/cli/handlers/base_handler.py:24`.
      `LiveHandler` + `BatchHandler` subclasses; abstract `compute()` + `execute()`.
- [ ] [SCRIPT] P0. **cross_instrument family** — same lift pattern.
- [ ] [SCRIPT] P0. **multi_timeframe family** — same.
- [ ] [SCRIPT] P0. **calendar family** — same.
- [ ] [SCRIPT] P0. Per family: `bash scripts/quality-gates.sh` + `git push origin live-defi-rollout`.
- [ ] [SCRIPT] P1. Update `codex/04-architecture/features-service-architecture.md` § per-family table — flip 4 families
      from `bare-class` to `ModeHandler` (Tab 1 should batch this update OR Tab 4 closes it inline).
- [ ] [SCRIPT] P1. Hard-delete 4 bare-class entry-points after ModeHandler lift in prod (compat-path removal).

### Spawn prompt

```text
You are Tab 4 main — features-service ModeHandler lift for batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 4
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab4 + § 7
  3. features-volatility-service/features_volatility_service/cli/handlers/base_handler.py (reference impl)
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

- ✅ `grep -rn "class.*FeatureService.*ModeHandler" features-{commodity,cross-instrument,multi-timeframe,calendar}-service/` returns 4 hits.
- ✅ Each family: `bash scripts/quality-gates.sh` green; pushed to live-defi-rollout.
- ✅ Bare-class compat-paths flagged for hard-delete post-prod-deploy.

## Tab 5 — pipeline_mode Phases 3/4/9 (operator-gated VM fleet migration)

**Owner**: pipeline_mode migration agent + operator (operator-gated; Phase 3 fires VM fleet).
**Scope**: VM fleet migration of ~10-50M parquets · consumer sweep · workspace QG sweep.
**Estimated**: ~48 hrs wall-clock.
**Cross-plan**: 3 banners — `master_to_live_defi` 🔴 BLOCK Phase 3 · `gcs_migration_bundle` 🟢 VM RUNNING ·
`live_pipeline_mtds_mdps_features` 🔴 BLOCK Phase 5.
**Depends-on**: Tab 2 UAC contract shipped.

### Todos

- [ ] [SCRIPT] P0. **Pre-Phase-3 cost audit** — Terraform budget +50% per pre-audit § 6 risk #2; CloudOps quota alert
      configured.
- [ ] [SCRIPT] P0. **Phase 3 VM fleet migration** — 1 consolidator VM (n1-standard-8) launched per
      `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 3 recipe. `MANIFEST_PER_VM_SHARDS=true` +
      `VM_NAME=mtds-pipeline-mode-migration-<RUN_TS>`. Dry-run first.
- [ ] [AGENT] P0. **Phase 3 event verification** (per CLAUDE.md "No fire-and-forget VM launches") — 90s post-launch:
      `gcloud storage ls gs://${PID}-events/events/<service>/<today>/<vm-name>/` for STARTED event; every 10-15 min
      progress check.
- [ ] [SCRIPT] P0. **Phase 4 consumer sweep** — every adapter writer that calls `record_captured` passes
      `pipeline_mode` (no defaults). Per `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 4.
- [ ] [SCRIPT] P0. **Phase 9 workspace-wide QG sweep** — per-repo `bash scripts/quality-gates.sh` post-migration.
- [ ] [SCRIPT] P1. Tab 5 includes the L7 fix-list from Tab 2 in same migration batch (MDPS 3 violations:
      `storage_dispatch_worker.py:49` · `output_writer_service.py:318` · `orchestration_writer.py:388`).

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

- ✅ `gcloud storage ls gs://${PID}-raw-tick/pipeline_mode=batch_*/asset_group=defi/...` returns canonical-shape parquets.
- ✅ Phase 3 VM event stream: STARTED + ≥1 progress event per hour + STOPPED with non-empty metadata.
- ✅ Phase 4 consumer sweep: `grep -rn "record_captured(" --include="*.py"` shows every callsite passes
      `pipeline_mode=...`.
- ✅ Workspace QG sweep: `gh run list --branch live-defi-rollout --limit 5` all green post-Phase-9.
- ✅ `READER_FELL_BACK_TO_LEGACY_PATH` event count trends to 0 over 30 days.

## Tab 6 — F21 reconciler shipping

> **🟢 AXIS DISCIPLINE — RATIFIED 2026-05-10 cross-plan audit Q2**: this Tab's recon-drift event
> `BATCH_VS_LIVE_RECON_DRIFTED` (lines 432-433) is **NOT** a `ServiceEmissionStateEnum` value. The two axes are
> orthogonal — do not conflate naming:
> - **Freshness axis** (`ServiceEmissionStateEnum` values in `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4):
>   `PUBLISHED_OK` / `PUBLISHED_DEGRADED` / `STALE_DATA_HEARTBEAT_ONLY` / `BLOCKED`. Driven by per-emission data
>   quality (WS connection / window completeness / etc.). Lives in manifest column `service_emission_state`.
> - **Reconciliation drift axis** (this Tab's `BATCH_VS_LIVE_RECON_DRIFTED` event): driven by `|batch_pnl - live_pnl|
>   / live_pnl > threshold_bps` per `RECON_GREEN_THRESHOLDS` SSOT. Emitted as an alerting event, NOT a manifest column
>   value. A row can be `PUBLISHED_OK` on the freshness axis AND simultaneously trigger `BATCH_VS_LIVE_RECON_DRIFTED`
>   on the recon axis — the two are evaluated independently.
>
> Reviewers reject PRs that introduce a recon-drift value into `ServiceEmissionStateEnum` or vice versa.

**Owner**: batch-live-reconciliation-service agent (single tab; greenfield service ship).
**Scope**: ship `engine/orchestrator.py` + 6 stages + manifest reader + P&L delta pipeline + threshold-decision +
alerting hook.
**Estimated**: ~1 calendar day active + ongoing 7-day soak calibration.
**Cross-plan**: 3 banners — `master_to_live_defi` 🔴 BLOCK F18 · `manifest_schema_final_gate` RE-VERIFY ·
`live_pipeline_mtds_mdps_features` BE-AWARE.
**Depends-on**: Tab 2 UAC `RECON_GREEN_THRESHOLDS` shipped + Tab 5 manifest schema stable.

### Todos

- [ ] [AGENT] P0. **`batch-live-reconciliation-service/engine/orchestrator.py`** — greenfield ship per pre-audit § 1
      Tab 6. Read manifest from MTDS + MDPS + features-service + strategy-service · compare batch vs live P&L per
      archetype · compute deltas (bps, drawdown, fill-rate) · emit recon report.
- [ ] [AGENT] P0. **`cli/handlers/reconcile_handler.py::ReconcileHandler.run()`** — wire orchestrator into CLI
      (currently NotImplementedError stub).
- [ ] [AGENT] P0. **6 stage files `stages/stage{0-5}_*.py`** — audit + complete content (names exist, content
      unverified per pre-audit).
- [ ] [SCRIPT] P0. **Manifest reader integration** — UTL `record_captured` consumption.
- [ ] [SCRIPT] P0. **P&L delta calculation pipeline** — per-archetype, per-trade, per-fill comparison.
- [ ] [SCRIPT] P0. **Threshold decision wiring** — read `RECON_GREEN_THRESHOLDS` from UAC; emit
      `BATCH_VS_LIVE_RECON_DRIFTED` if `|batch_pnl - live_pnl| / live_pnl > threshold_bps`.
- [ ] [SCRIPT] P0. **Alerting hook** — `BATCH_VS_LIVE_RECON_DRIFTED` event subscribed by alerting-service rule.
- [ ] [SCRIPT] P0. **Service-readiness Group A** — `bash scripts/quality-gates.sh` Pass 1 + quickmerge to staging +
      semver-rollout to 0.1.0; A1-A3 RED → GREEN.
- [ ] [AGENT] P0. **Paper-mode smoke** — run reconciler against shipped 2-yr backtest (per Tab 8 step 1) + carry_paper
      VM (per Tab 8 step 4); calibrate threshold values vs observed delta distribution (pre-audit § 6 risk #3:
      95p+2× margin starting point).
- [ ] [AGENT] P1. **7-day soak calibration** — daily reconciler run during Tab 8 paper-soak; tighten thresholds.

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

- ✅ `python -m batch_live_reconciliation_service --operation reconcile --mode batch --start-date 2026-05-10 --end-date 2026-05-10`
      runs to completion + emits recon report parquet at `gs://${PID}-reconciliation/.../2026-05-10/*.parquet`.
- ✅ `gcloud storage cat <recon-parquet> | head -c 1000` shows P&L delta + threshold-decision (`recon_green=true|false`).
- ✅ `gs://${PID}-events/events/batch-live-reconciliation-service/...` shows STARTED + RECON_REPORT_EMITTED + STOPPED.
- ✅ Service-readiness Group A items 1-3 GREEN per master plan rollup; F21 status flipped 🟡 → 🟢.

## Tab 7 — UI ExecutionModeContext rollout (shallow, pre-cutover)

**Owner**: UI agent main + 3 parallel sub-agents (one per refactor target).
**Scope**: rollout `ExecutionModeContext` to 6 violation files per pre-audit Manifest 4. **Defer** ML page mode-blind
deep refactor + dashboard mock-conflation post-cutover (per defaults #6).
**Estimated**: ~6-8 hrs.
**Cross-plan**: 3 banners — `deployment_ui_lifecycle_tabs` 🟡 IN-FLIGHT · `master_to_live_defi` BE-AWARE G23 ·
`live_pipeline_mtds_mdps_features` BE-AWARE.

### Todos

- [ ] [SCRIPT] P0. **app/(ops)/ops/page.tsx:192** — replace `useState<"live"|"batch">` with `useExecutionMode()` hook.
- [ ] [SCRIPT] P0. **app/(platform)/services/research/quant/page.tsx:216** — same.
- [ ] [SCRIPT] P0. **components/ops/deployment/data-status/data-status-provider.tsx:33** — lift to ExecutionModeContext.
- [ ] [SCRIPT] P0. **components/ops/deployment/form/deploy-form-context.tsx:31** — same.
- [ ] [SCRIPT] P0. **components/widgets/markets/markets-data-context.tsx:57,62** — handle 3-way `compare` variant
      (likely keep separate state for `compare` vs use ExecutionModeContext for live/batch).
- [ ] [SCRIPT] P0. **components/widgets/pnl/pnl-data-context.tsx:159** — same refactor.
- [ ] [SCRIPT] P0. Per-file: `npm run build` + `npm run test` + push.
- [ ] [SCRIPT] P0. **Playwright e2e matrix** on dashboard / ops / research / data-status / pnl pages — verify mode toggle
      propagates correctly without prop-drill regressions.
- [ ] [SCRIPT] P1. **post-cutover** — ML page hard-disable refactor + dashboard mock-conflation cleanup (defaults #6).

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
- ✅ `grep -rn "useExecutionMode()" unified-trading-system-ui/` shows hook adopted in 8+ files (the 6 refactored + the
      2 already-good).
- ✅ `npm run build` exits 0; `npm run test` green.
- ✅ Playwright e2e matrix passes on dashboard / ops / research / data-status / pnl pages.

## Tab 8 — carry_staked_basis end-to-end run + 7-day soak

**Owner**: deployment-service + execution-service + strategy-service agent (multi-repo wall-clock).
**Scope**: launch backtest VM · verify scores · ship paper-deploy launcher · launch paper VM · 7-day soak monitoring +
recon-green calibration.
**Estimated**: ~7 calendar days wall-clock (paper-soak is the longest pole).
**Cross-plan**: 3 🟢 VM RUNNING / BE-AWARE banners.
**Starts**: DAY-1 (parallel to Tab 1-7); paper-deploy launcher ships ~DAY-2 once Tab 1+2 land.

### Todos

- [ ] [AGENT] P0. **Step 1 — Backtest VM launch** — operator-run paste-ready bash from pre-audit § 9 COMMAND #1.
      Backtest `carry_staked_basis` over 2026-04-01 to 2026-05-10 (or last 60d). Verify VM event stream STARTED + per-
      instrument INSTRUMENT_PROCESSED + STOPPED.
- [ ] [SCRIPT] P0. **`deployment-service/scripts/vm/launch-defi-backtest-vm.sh`** — greenfield ship per pre-audit § 1
      Tab 8 step 1.
- [ ] [SCRIPT] P0. **Step 2 — Score persistence verification** — read `gs://${PID}-strategy-outputs/backtest/.../*.parquet`
      sample row + assert OHLC populated (not 1440-NaN placeholders per CLAUDE.md "Honest absence" rule).
- [ ] [SCRIPT] P0. **`deployment-service/scripts/vm/launch-defi-paper-trading-vm.sh`** — greenfield ship per pre-audit
      § 1 Tab 8 step 3.
- [ ] [AGENT] P0. **Step 4 — Paper-deploy VM launch** — `RUNTIME_MODE=live, EXECUTION_MODE=simulated, STRATEGY_ID=carry_staked_basis`.
- [ ] [SCRIPT] P0. **Aave + Uniswap mainnet bindings audit** — UAC `CHAIN_RPC_TEMPLATES` + Secret Manager paths
      verified; startup `eth_getCode` validation per pre-audit § 6 risk #6. Operator manual sign-off 1 day pre-launch.
- [ ] [SCRIPT] P0. **Tenderly fork pre-flight** — execution-service integration test pre-flight + pre-deploy
      fork-swap smoke per pre-audit § 6 risk #5.
- [ ] [SCRIPT] P0. **Pre-soak rate-limit audit** — confirm 6 perp venues (Bybit, Deribit, Binance, OKX, Hyperliquid,
      Aster) testnet rate limits per pre-audit § 6 risk #4.
- [ ] [AGENT] P0. **Step 6 — 7-day soak monitoring** — schedule daily ScheduleWakeup checks per pre-audit § 9
      COMMAND #6: VM alive + events flowing last hour + P&L accumulating + Tab 6 reconciler recon-green.
- [ ] [SCRIPT] P0. **carry_staked_basis-specific kill-switch + alerting rules** — extend
      `risk-and-exposure-service/risk_and_exposure_service/kill_switch_rules.py` with archetype-specific
      drawdown/position rules (`drawdown_pct=5, position_breach_pct=20, scope=ARCHETYPE`).
- [ ] [AGENT] P1. **post-cutover** — `leveraged_funding_arb` end-to-end identical recipe (May-23 cutover lands BOTH
      archetypes, but leveraged_funding_arb is the hedge leg of carry_staked_basis — a single coordinated paper-soak
      may suffice; operator confirms during Tab 8 paper-soak).

### Spawn prompt

```text
You are Tab 8 — carry_staked_basis end-to-end run + 7-day soak for batch_live_symmetry_2026_05_10 plan.

BEFORE doing anything, read in order:
  1. unified-trading-pm/plans/active/batch_live_symmetry_2026_05_10.md § Tab 8
  2. unified-trading-pm/plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab8 + § 6 risks #4-#6 + § 9 recipe
  3. unified-trading-pm/plans/active/master_to_live_defi_2026_05_23.md § Group F items 17-22
  4. unified-trading-pm/plans/active/defi_master_2026_05_07.md
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

| compat path                                  | Tab owner | removal trigger                                                              |
| -------------------------------------------- | --------- | ---------------------------------------------------------------------------- |
| pipeline_mode reader fallback levels 1/3/4   | Tab 5     | T+30d post-Phase-3 when `READER_FELL_BACK_TO_LEGACY_PATH` event count = 0    |
| pipeline_mode level 2 (legacy `category=`)   | Tab 5     | NEVER — CLAUDE.md hive-vocab exception                                       |
| UI `RuntimeMode` redeclaration               | Tab 7     | Tab 7 close-out — UAC re-export from UTL + UCI codegen                       |
| `LIVE_*` event-prefix anti-pattern           | n/a       | post-cutover — separate plan                                                 |
| Feature bare-class fallback                  | Tab 4     | Tab 4 close-out — hard-delete after ModeHandler lift in prod                 |
| MDPS dual-handler split                      | n/a       | post-cutover — Block D2 design proposal                                      |
| Shadow-simulated fills in live               | n/a       | post-cutover — Block A3/D4 if operator pivots                                |

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
  greenfield · L8) migrated to follow-up plans per CLAUDE.md "Plan Archival HARD RULE" (Step 3 of 5: every deferred
  item gets an active home).

## Temporary states + their canonical follow-up plans

- **D4 Shadow-simulated fills in live**: deferred post-cutover — successor `plans/active/shadow_simulated_fills_<post>.md` (TBD).
- **J1 phase→mode helper full wiring**: signature shipped in Tab 2 P1; wire-in deferred — successor TBD.
- **L4 LIVE_ event-prefix rename**: post-cutover — successor `plans/active/event_prefix_rename_<post>.md` (TBD).
- **L5 schema-parity comparative gate**: post-cutover (already mode-agnostic by design) — successor optional.
- **L6 executor factory single-file enforcement**: depends on D3 factory shipping in Tab 2; STEP enable post-Tab-2.
- **L8 mode-parametric workspace tests**: skipped per defaults #3.
- **G1 LIVE_ event rename**: post-cutover — successor TBD.
- **F4/F5 deep UI refactor (ML page hard-disable + dashboard mock-conflation)**: post-cutover — successor
  `plans/active/ui_mode_refactor_<post>.md` (TBD).
- **I2 TradFi live execution greenfield**: post-cutover — successor `plans/active/tradfi_live_execution_<post>.md` (TBD).
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

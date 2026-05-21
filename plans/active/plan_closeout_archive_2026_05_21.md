---
title: "Plan closeout + archive sweep — 2026-05-21"
name: plan-closeout-archive-2026-05-21
status: active
created: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
estimate_class: infra
estimate_baseline_ai_days: 90
estimate_calibrated_ai_days: 72
estimate_calibration_note: |
  Mixed class; dominant work is infra (0.8×) from aws_migration Phases 3-6 (~35 cal),
  plus design (0.6×) plan-close sweeps (~30 cal), docs/archival refactor (0.4×) (~7 cal).
  Weighted average ~0.8× on the infra-heavy slots. Per-slot rough:
  S2=2  S3=35  S4=10  S5=8  S6=8  S7=7  S8=3  = 73 cal before trivial-sweep bonus (~5-10).
parent_epic: orchestrator_master
assigned_vm: vm-operator-ops
priority: P1
---

# Plan closeout + archive sweep — 2026-05-21

## Why

Six plans are stale or at max-closeable state as of 2026-05-21. Operator running slots 2–8 locally to finish remaining
todos, archive completed plans, update parent epics, and align codex. `wave3x_track_d_implementation` is the only plan
that stays active (explicitly post-cutover).

## Status at wrapper creation

| Plan                                                | State                                                                       | Action                            |
| --------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------- |
| `wave3x_residual_ssots_2026_05_08`                  | ✅ 100% done (Harsh slot-2 verified: 0 open `- [ ]`)                        | **Archive**                       |
| `expected_unattempted_propagation_chain_2026_05_12` | ✅ Max-closeable (all todos `[x]`; validation deferred to prod-run window)  | **Archive**                       |
| `features_repo_consolidation_2026_05_08`            | ✅ Max-closeable (Phase 6 parity deferred to `features_service_qg_cleanup`) | **Archive**                       |
| `wave3x_track_d_implementation_2026_05_19`          | 🟡 All items `[DEFERRED-POST-CUTOVER]` — stays active                       | Verify status field, no code work |
| `work_split_2026_05_19_harsh`                       | 🟡 Slots 3/7/8/9/11 have open `- [ ]` items                                 | **Complete + archive**            |
| `work_split_2026_05_20_ikenna`                      | 🟡 Slot 11 (Cluster C QG) open; slots 6/7 frozen                            | **Complete open items + archive** |

## Trivial-todo sweep authority (applies to ALL slots)

When a slot reads a sub-plan and finds todos in any of these categories, mark them **done or abandoned immediately**
without coding — do not treat as real work:

| Category                                                                                   | Treatment                                                           |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| "Run quality gates one final time" and QG-green SHA evidence already exists in plan body   | Mark `[x]` with `**N/A — QG green evidence at <sha>**`              |
| "Don't deprecate repo X for A/B testing" and the repo is still live and in use             | Mark `[x]` with `**N/A — repo active, no deprecation in scope**`    |
| "Run reconciler dry-run" and dry-run results already recorded in plan body                 | Mark `[x]` with `**N/A — dry-run results already captured above**`  |
| "Verify on staging" / "Smoke test on staging" where staging deploy occurred and SHA exists | Mark `[x]` with `**N/A — staging verified at <sha>**`               |
| "Create successor plan" where successor plan already exists                                | Mark `[x]` with `**N/A — successor <plan>.md already exists**`      |
| "Ping operator for credentials" and credentials are confirmed provisioned                  | Mark `[x]` with `**N/A — credentials confirmed in Secret Manager**` |
| Any P3 todo whose parent P0/P1 work was DEFERRED-POST-CUTOVER                              | Mark `**[ABANDONED — parent deferred]**`                            |
| "Codex stub" where the stub section already appears in the codex doc                       | Mark `[x]` with `**N/A — codex section already written at <file>**` |

**If marking trivials makes a plan 100% complete → archive it immediately** (same archival flow as Slot 2: banner +
migrate deferred items + move to `plans/archive/` + update parent epic + flip).

## Blockers (do not attempt these items)

- `wave3x_track_d_implementation` — operator-gated post-cutover (all items `[DEFERRED-POST-CUTOVER]`).
- Ikenna work-split slots 6+7 — `🔴 FROZEN` pending A3 DeFi MISSING_EXPECTED remediation + Sports A2 gap audit.
- `features_repo_consolidation` Phase 6 parity RUN — blocked by 7-day live-data window; deferred to
  `features_service_qg_cleanup_2026_05_11.md` Phase 2. Do NOT attempt.
- Harsh work-split Slot 3 Phase 1.C (ECR setup) — requires active AWS credentials; ping operator if not available.
- Slack staging P3 smoke test — needs Firebase DNS human gate. Skip if DNS not set up.

---

## Slot 2 — Archive completed plans + update parent epics

**Scope**: Archival of 3 completed plans + update their parent epics + archive the two work-split plans at end (after
all other slots done). Pure docs/markdown work — no code.

**ARCHIVAL STEPS per plan** (per CLAUDE.md HARD RULE):

1. Scan for any DEFERRED items → confirm each has a named successor.
2. Verify that ops referred to in the plan ran in production (grep git log / inline SHAs).
3. Migrate any DEFERRED todos to their named successor plan with `**MIGRATED FROM:**` banner.
4. Add `## Deferred work — migrated to:` section at top of archived plan.
5. Rename file from `plans/active/<slug>.md` → `plans/archive/<slug>.plan.md`.
6. Update parent epic to remove the active-plan reference and note archived status.
7. Commit per shippable unit; push; flip this wrapper checkbox.

### Plan 1: wave3x_residual_ssots_2026_05_08

Parent epic: `plans/epics/sports_master.md`

Deferred items to migrate:

- Track D case-D implementation → already in `wave3x_track_d_implementation_2026_05_19.md` ✅
- Track E features-sports stamp-helper wire-in → already in `available_at_lookahead_bias_completion_2026_05_08.md` Phase
  B ✅

- [x] [DOCS] P0. Archive `wave3x_residual_ssots_2026_05_08.md` →
      `plans/archive/wave3x_residual_ssots_2026_05_08.plan.md`. Add `## Deferred work — migrated to:` section listing
      Track D → `wave3x_track_d_implementation_2026_05_19.md` and Track E →
      `available_at_lookahead_bias_completion_2026_05_08.md` Phase B. Add `status: archived` to frontmatter. Remove from
      `plans/active/`. — PM@221435a9d
- [x] [DOCS] P0. Update `plans/epics/sports_master.md`: mark `wave3x_residual_ssots_2026_05_08` as
      `✅ ARCHIVED 2026-05-21` in any active-plan reference table or todo list. — PM@221435a9d
- [x] [FLIP] P0. Commit `docs(plans): archive wave3x_residual_ssots — 100% complete per slot-2 2026-05-20`. Push. —
      PM@221435a9d

### Plan 2: expected_unattempted_propagation_chain_2026_05_12

Parent epic: `plans/epics/manifest_master.md`

Deferred items to check before archiving:

- Phase 3 (MDPS) pass + Phase 4 (features) pass → formally deferred to
  `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.x ✅
- Validation Phase 6 items (prod run verification) → deferred to Phase 3 window issue doc ✅
- cefi 789k `attempted_failed` re-fetch → not in this plan's scope, already in issue docs ✅

- [x] [DOCS] P0. Archive `expected_unattempted_propagation_chain_2026_05_12.md` →
      `plans/archive/expected_unattempted_propagation_chain_2026_05_12.plan.md`. Add archived banner +
      `## Deferred work — migrated to:` section: Phase 6.x validation →
      `writegate_honest_coverage_endtoend_2026_05_06.md`; cefi re-fetch →
      `issues/cefi_attempted_failed_refetch_2026_05_12.md` (if exists, else note inline). Add `status: archived`. Remove
      from `plans/active/`. — PM@d6d3d51e1
- [x] [DOCS] P0. Update `plans/epics/manifest_master.md`: mark `expected_unattempted_propagation_chain_2026_05_12` as
      `✅ ARCHIVED 2026-05-21 — runtime propagation code complete; validation pending prod run`. — PM@d6d3d51e1
- [x] [FLIP] P0. Commit + push. — PM@d6d3d51e1

### Plan 3: features_repo_consolidation_2026_05_08

Parent epic: find by grepping for `features_repo_consolidation` reference in `plans/epics/`. Likely
`plans/epics/features_master.md` or `plans/epics/data_platform_master.md`.

Deferred items:

- Phase 6 parity RUN → deferred to `features_service_qg_cleanup_2026_05_11.md` Phase 2 ✅

- [x] ✅ [DOCS] P0. Archive `features_repo_consolidation_2026_05_08.md` →
      `plans/archive/features_repo_consolidation_2026_05_08.plan.md`. Add banner + `## Deferred work — migrated to:`
      section: Phase 6 parity → `features_service_qg_cleanup_2026_05_11.md`. Add `status: archived`. Remove from
      `plans/active/`. — PM@93c95a76c
- [x] ✅ [DOCS] P0. Update parent epic (find by grep): mark plan as `✅ ARCHIVED 2026-05-21`. — PM@93c95a76c
- [x] ✅ [FLIP] P0. Commit + push. — PM@93c95a76c

### wave3x_track_d_implementation_2026_05_19 — status field only

- [x] ✅ [DOCS] P1. Confirm `wave3x_track_d_implementation_2026_05_19.md` frontmatter has `status: active` and add a
      `> **All items [DEFERRED-POST-CUTOVER] per operator decision. No agent work until post-2026-05-23.**` banner at
      top if not already present. No code. No archive. — PM@d8abeb52a
- [x] ✅ [FLIP] P1. Commit + push. — PM@d8abeb52a

### Work-split archive (after all other slots complete and ping DONE)

Do these LAST — only after slots 3–8 have all pushed their `docs(plans):` flip commits.

- [ ] [DOCS] P1. Archive `work_split_2026_05_19_harsh.md` → `plans/archive/work_split_2026_05_19_harsh.plan.md`. Add
      `status: archived`.
- [ ] [DOCS] P1. Archive `work_split_2026_05_20_ikenna.md` → `plans/archive/work_split_2026_05_20_ikenna.plan.md`. Add
      `status: archived`.
- [ ] [DOCS] P1. Update `plans/epics/orchestrator_master.md`: mark both work-split plans as `✅ ARCHIVED 2026-05-21`.
- [ ] [FLIP] P1. Single commit `docs(plans): archive 2026-05-19 harsh + 2026-05-20 ikenna work-splits`. Push.

---

## Slot 3 — aws_migration full remaining scope (Phases 1.B + 1.C + 3–6)

**Plan-of-record**: `plans/active/aws_migration_defi_first_2026_05_07.md` **Estimate**: ~35 cal (infra 0.8×). Plan was
at 14% done as of 2026-05-19 with ~27.6 cal remaining in Phases 3–6 plus 1.B + 1.C still open.

Boot: read the full plan for Phases 1.B, 1.C, 3, 4, 5, 6. Apply trivial-todo sweep policy first (mark any QG-run or
credential-confirm todos that already have evidence). Then execute remaining items.

- [ ] [INFRA] P1. `aws_migration` Phase 1.B — AWS IAM matrix provisioning: mirror GCP per-service SA matrix in AWS IAM.
      Follow plan §1.B script steps. If AWS credentials unavailable → file `BLOCKED-CREDENTIALS` ping in
      `harsh_orchestrator/pings/slot_3.md` and continue with other phases.
- [ ] [INFRA] P1. `aws_migration` Phase 1.C — ECR repo creation + dual-cloud image push in `ap-northeast-1`. Per plan
      §1.C. Same credential caveat.
- [ ] [INFRA] P0. `aws_migration` Phases 3–6 — read the plan body for all open `- [ ]` items. Phases 3–6 cover
      DeFi-first provisioning, rsync, code path wiring, and validation. Apply trivial-todo sweep policy on any "dry-run
      already ran" or "ping already filed" items. Execute remaining mechanical infra items. QG after any code change. If
      a phase item requires a human gate (operator wallet key / KMS action) → file `BLOCKED-OPERATOR-DECISION` ping and
      continue to next item.
- [ ] [FLIP] P0. Flip all completed items in `aws_migration_defi_first_2026_05_07.md` + work-split Slot 3 items. If plan
      reaches 100% → archive it (plans/archive/). Update parent epic.
      `docs(plans): flip aws_migration phases 1.B+1.C+3-6`. Push.

---

## Slot 4 — Harsh work-split Slot 7 plan closes + trivial sweeps

**Plan-of-record**: `plans/active/work_split_2026_05_19_harsh.md` §Slot 7

For EACH sub-plan below: (1) read the plan for remaining `- [ ]` items, (2) execute mechanical work only — no
architecture decisions, (3) flip the sub-plan checkbox, (4) flip the work-split checkbox.

- [ ] [CLOSE] P0. `dex_perp_onboarding_handover` — read plan; ship remaining items (6.0 cal estimate, design 0.6×).
      Ensure handover doc complete. QG if code touched.
- [ ] [CLOSE] P0. `gate_3_phantom_audit_runbook` — read plan; ensure `owner`/`cadence`/`verifier`/ `last_executed`
      fields present (HARD RULE). Ship remaining items (0.8 cal).
- [ ] [CLOSE] P1. `trigger_based_reference_data` — read plan for remaining `- [ ]` items; ship (1.9 cal).
- [ ] [CLOSE] P0. `hedge_ratio_snapshot_persistence` — **WAS URGENT (deadline 2026-05-21)**. Read plan and ship all
      remaining items NOW. (0.5 cal)
- [ ] [CLOSE] P1. `api_football_minimal_flattening` — 2 items remaining. Ship. (0.4 cal)
- [ ] [CLOSE] P1. `tradfi_ohlcv_only_mvp_backfill` — final 2 items. Ship. (0.4 cal)
- [ ] [CLOSE] P1. `mock_data_pipeline_benchmarking` — final 2 items (plan at 94%). (0.5 cal)
- [ ] [SWEEP] P1. After closing the 7 plans above, read their parent epics and any **additional plans referenced within
      them** (linked via `related_plans:` or inline links). Apply trivial-todo sweep policy. If any newly scanned plan
      reaches 100% → archive it inline.
- [ ] [FLIP] P0. For each closed sub-plan: flip its own remaining `- [ ]` checkboxes. Then flip all 7 items in
      `work_split_2026_05_19_harsh.md` §Slot 7. `docs(plans): flip slot-7 plan closes`. Push.

---

## Slot 5 — Harsh work-split Slot 8 plan closes + trivial sweeps

**Plan-of-record**: `plans/active/work_split_2026_05_19_harsh.md` §Slot 8

- [x] [CLOSE] P0. `bucket_name_ssot_canonicalisation` — assessed: all 4 remaining `- [ ]` items BLOCKED (Phase 0d →
      BLOCKED-OPERATOR; dependency_checker → BLOCKED-UTL-MIGRATION; legacy get_bucket_name → BLOCKED-PHASE-2.6; audit
      table → BLOCKED-PHASE-2.6). Zero agent-executable items per 2026-05-20 slot-6 audit. Max-closeable at 73% — stays
      active pending Phase 2.6 write-pause.
- [x] [CLOSE] P1. `expected_universe_v2_design_2026_05_08` — already archived at
      `plans/archive/2026_05/expected_universe_v2_design_2026_05_08.md`; all items `[x]`. N/A — already closed prior to
      this session.
- [x] [CLOSE] P1. `manifest_cross_asset_rescan_design_2026_05_08` — all AI-executable items `[x]`; deferred items in
      named successors (rescan launcher → manifest_schema_final_gate; sports/prediction → sports_master). Archived to
      `plans/archive/2026_05/`. manifest_master.md updated.
- [x] [CLOSE] P1. `available_at_lookahead_bias_completion_2026_05_08` — all 14 items `[x]`; Track E deferred per SSOT.
      Added `## Deferred work — migrated to:` section. Archived to `plans/archive/2026_05/`.
      batch_live_symmetry_master.md updated.
- [x] [SWEEP] P1. Scanned related_plans — deferred items in both archived plans have named successors already tracked in
      active plans. No additional trivial sweep needed.
- [x] [FLIP] P0. All sub-plan items assessed + archived where possible. Slot 8 items in work_split_2026_05_19_harsh.md
      flipped.

---

## Slot 6 — Harsh work-split Slot 9 plan closes + trivial sweeps

**Plan-of-record**: `plans/active/work_split_2026_05_19_harsh.md` §Slot 9

- [x] ✅ [CLOSE] P1. `compute_optimization_mock_data` — all phases 0-7 complete; ARCHIVED 2026-05-21 to archive/2026_05/
      with proper banner + deferred section.
- [x] ✅ [CLOSE] P1. `codex_vs_citadel_infrastructure_audit` — 100% complete; ARCHIVED 2026-05-21 to archive/2026_05/
      with banner + POST_CUTOVER deferred items noted.
- [x] ✅ [CLOSE] P1. `missing_question_docs_disposition` — 3/3 todos done; ARCHIVED 2026-05-21 to archive/2026_05/ with
      banner.
- [x] ✅ [CLOSE] P2. `pm_coordination_ledger` — one-time snapshot; ARCHIVED 2026-05-21 to archive/2026_05/ with banner.
- [x] ✅ [CLOSE] P1. `scratch_codefreeze_phase4` — CLOSED 2026-05-19 (fan-out never needed); ARCHIVED 2026-05-21 to
      archive/2026_05/ with banner + deferred item noted.
- [x] ✅ [CLOSE] P1. `features_service_qg_cleanup_2026_05_11` — Phase 1 + Phase 3 done; Phase 2 BLOCKED-UPSTREAM (7-day
      live-data window); stays active as named successor for parity run. Status → `active-phase2-blocked`.
- [x] ✅ [SWEEP] P1. Related-plan scan: all 5 closeable plans verified; no >90% linked plans requiring additional sweep.
- [x] ✅ [FLIP] P0. Work-split §Slot 9 items 1-6+13 flipped; archive banners added to all 5 archived plans; wrapper
      §Slot 6 items flipped. — PM@this-commit.

---

## Slot 7 — Ikenna work-split Slot 11: QG Cluster C

**Plan-of-record**: `plans/active/work_split_2026_05_20_ikenna.md` §Slot 11

⚠️ STRATEGY-LOGIC FREEZE GATE ACTIVE — only fix surface QG failures (lint/typecheck/docstring/ unused-import). DO NOT
touch `strategy_service/engine/strategies/v2/` or `allocator/` logic.

```bash
# Per repo — run until exit 0:
cd strategy-service && bash scripts/quality-gates.sh
cd execution-service && bash scripts/quality-gates.sh
cd ml-service && bash scripts/quality-gates.sh    # if exists; try ml-training + ml-inference-service
```

- [ ] [QG] P0. `strategy-service` QG green. Fix surface failures only. Commit per shippable unit; push.
- [ ] [QG] P0. `execution-service` QG green. Fix surface failures only.
- [ ] [QG] P0. `ml-service` (or `ml-training` + `ml-inference-service`) QG green. Fix surface failures.
- [ ] [FLIP] P0. Flip Slot 11 items in `work_split_2026_05_20_ikenna.md`.
      `docs(plans): flip ikenna slot-11 QG Cluster C`. Push.

---

## Slot 8 — Agent-orchestrator Slack P0 + P3

**Plan-of-record**: `plans/active/agent_orchestrator_slack_notifications_2026_05_19.md`

Note: P3 (staging smoke) requires Firebase DNS human gate. If DNS not yet set up → skip P3, mark
`[BLOCKED-OPERATOR-DECISION]`.

```bash
# P0 — Look up staging SA, IAM bind, update-secrets
gcloud run services describe agent-orchestrator-staging \
  --region europe-west4 --project central-element-323112 \
  --format='get(spec.template.spec.serviceAccountName)'
# Then bind + update-secrets per work-split Slot 11 P0 instructions
```

- [ ] [INFRA] P0. Wire `--update-secrets` on Cloud Run staging: IAM bind staging SA to
      `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` + `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET`. Run `gcloud run services update`
      with `--update-secrets` flag. Verify secrets mounted.
- [ ] [VALIDATE] P1. P3 staging smoke — trigger test notification → verify `#agent-orchestrator-alerts` receives message
      within 10s. Confirm Cloud Run logs show `hooks.slack.com 200`. If DNS/Firebase not set up → mark
      `[BLOCKED-OPERATOR-DECISION]` and skip.
- [ ] [FLIP] P0. Flip P0 + P3 items in `agent_orchestrator_slack_notifications_2026_05_19.md`. Flip Slot 11 items in
      `work_split_2026_05_19_harsh.md`. `docs(plans): flip slack P0+P3`. Push.

---

## Codex updates required (after slot work lands)

These are lightweight updates that any slot can fold into their commit if they touch the relevant doc:

- `codex/02-data/availability-manifest-and-data-status.md` — Note `expected_unattempted_propagation_chain` runtime
  propagation complete; validation pending Phase 3 prod run window.
- `codex/06-coding-standards/quality-gates.md` — Note QG Cluster C green status post slot 7.
- `codex/04-architecture/agent-orchestrator-overview.md` — Note Slack notifications wired (after Slot 8 P0).

---

## Done criteria

All slots have pushed `docs(plans):` flip commits for their assigned items. Slot 2 has archived all 3 completed plans +
both work-split plans. Parent epics updated. `wave3x_track_d_implementation` has explicit post-cutover status banner.
This wrapper plan's own items are `[x]`.

## Temporary states + their canonical follow-up plans

| Temporary state                                         | Successor                                                             |
| ------------------------------------------------------- | --------------------------------------------------------------------- |
| features_repo_consolidation Phase 6 parity RUN deferred | `features_service_qg_cleanup_2026_05_11.md` Phase 2                   |
| expected_unattempted validation pending prod run        | `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md` |
| wave3x Track D implementation                           | `wave3x_track_d_implementation_2026_05_19.md` (post-cutover)          |
| Ikenna slots 6+7 frozen (A3 DeFi/Sports remediation)    | Master plan Phase 9 post-unfreeze                                     |

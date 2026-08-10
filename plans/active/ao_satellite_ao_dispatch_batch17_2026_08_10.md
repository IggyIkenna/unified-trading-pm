---
doc_type: plan
title: AO satellite AO batch 17 — rescue slot-4's orphaned mdps throttle-fix WIP (agent_operating_framework_master epic)
summary: >-
  SEVENTEENTH AO-dispatch batch for the `ao` topic tranche — a full-tranche `ao` RECLASSIFY + satellite-extraction sweep
  (group 1 of 3, 2026-08-10) single-item extraction from `orphaned_wip_slot12_slot8_recovery_2026_08_04.md`. That doc's
  other 2 todos are already done (both closed as MOOT — the rescued content had already independently landed under fresh
  SHAs); the sole remaining item is a bounded, mechanical git-rescue: locate slot-4's orphaned
  `market-data-processing-service` throttle-fix commit (`~036c568`, proactive GCS-429 avoidance), confirm it's a real
  orphan, reconcile onto `origin/live-defi-rollout`, QG green, quickmerge — or, if already superseded/landed under
  another SHA, close with that note (outcome-defined done-when, matching this same doc's own already-closed todos 1-2's
  proven pattern). Low priority (P3) — the crash-risk half already landed separately; this is the
  proactive-429-avoidance refinement only.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [market-data-processing-service]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-17, satellite-docs, satellite-extraction, orphan-rescue]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch17_finalize_2026_08_10.md,
    /plans/active/issues/orphaned_wip_slot12_slot8_recovery_2026_08_04.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: backend_engineer
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/orphaned_wip_slot12_slot8_recovery_2026_08_04.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
source: >-
  `/na-eligibility-audit ao` full-tranche sweep, group 1 of 3, 2026-08-10 — per-item satellite extraction from
  `orphaned_wip_slot12_slot8_recovery_2026_08_04.md`'s sole remaining open todo (todo 3, P3).
---

# AO satellite AO batch 17 — rescue slot-4's orphaned mdps throttle-fix WIP

## Todos

- [ ] [BACKEND] P3. **Rescue slot-4's orphaned `market-data-processing-service` throttle fix `~036c568` (proactive
      GCS-429 avoidance) — or confirm it already landed.** Review agt-8fee2f verified it live 2026-08-04 (msg #3648);
      never independently re-checked since. Locate the commit (`origin/wip-preserve/*` refs for slot-4, or slot-4's
      current worktree if still reachable), confirm whether it's a real orphan
      (`git merge-base --is-ancestor <sha> origin/live-defi-rollout` → not-ancestor). If still orphaned: reconcile onto
      current `origin/live-defi-rollout` tip, run a fresh `bash scripts/quality-gates.sh` green, quickmerge. If it turns
      out already-superseded/landed under a different SHA (the pattern this same source doc's own todos 1-2 already hit
      twice — both turned out moot, independently re-landed): close with that note instead, citing the landed SHA + a
      content diff proving equivalence (mirror todos 1-2's own evidence style in the source doc, not a bare "looks
      similar" claim). **Done when**: the 429-avoidance change is an ancestor of `origin/live-defi-rollout` under some
      SHA (either freshly landed or confirmed already-landed). Source:
      `/plans/active/issues/orphaned_wip_slot12_slot8_recovery_2026_08_04.md` (its sole remaining todo). Repo:
      market-data-processing-service.

## Codex SSOTs

`/codex/05-infrastructure/per-tab-worktrees.md`, `/codex/08-workflows/ci-cd-flow.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

## Progress Log

- **2026-08-10** — Authored by the `ao` full-tranche RECLASSIFY + satellite-extraction sweep (group 1 of 3). Extracted
  as its own single-item batch rather than folded into an existing one: no currently-active
  `ao_satellite_ao_dispatch_batch*` doc names this specific todo or `market-data-processing-service`/`~036c568` (checked
  via `grep -rl "036c568\|mdps.*throttle" plans/active/*.md` before drafting — zero hits besides the source doc itself).
  Conflict-check against active `assigned_vm: planning` docs sharing `parent_epic: agent_operating_framework_master`: no
  overlap on this repo/commit. Low priority and genuinely small — a single bounded git-rescue-or-confirm-moot task,
  matching the exact outcome-defined shape this same source doc's own todos 1-2 already used successfully.

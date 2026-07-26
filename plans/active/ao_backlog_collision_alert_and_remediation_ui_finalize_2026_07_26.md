---
doc_type: plan
title: Finalize — AO backlog id-collision alert + remediation UI
summary:
  Gated finalize for ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md. Re-verify each todo's cited evidence,
  confirm the new panel/endpoint actually surface and fix a live-reproduced collision (not just unit fixtures), then
  archive the parent via the standard 6-step ritual.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, backlog, regen, id-collision, alerting, dashboard-ui, finalize]
related:
  [
    /plans/active/ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md,
    /plans/archive/issues/backlog_regen_id_reuse_stale_status_2026_07_15.md,
    /plans/archive/2026_07/ao_backlog_regen_integrity_2026_07_20.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on: [ao_backlog_collision_alert_and_remediation_ui_2026_07_26]
gate_on_depends: true
source:
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
---

# Finalize — AO backlog id-collision alert + remediation UI

## Todos

- [ ] [BACKEND] P1. **Re-verify each parent todo's cited evidence independently** — re-run the parent's own tests from a
      fresh checkout (don't trust the parent's own "green" claim), confirm each cited commit sha actually contains the
      described change, and confirm `bash scripts/quality-gates.sh` is green on the tip that shipped all four todos.
- [ ] [BACKEND] P1. **Live end-to-end check against a real (not fixture) collision.** Deliberately reproduce a fresh
      sibling-reset-guard collision on a scratch/test plan doc (mirroring how this session's
      `slot_stale_spawn_base_     role_stuck_task_less-004` collision arose), confirm it (a) pages Slack exactly once,
      (b) shows up in the new dashboard panel, (c) the "Fix" button resolves it leaving the original done row untouched,
      per the parent's own definition-of-done. Clean up the scratch plan doc afterward.
- [ ] [REVIEW] P2. **Run the standard 6-step archival ritual on the parent plan** — migrate any DEFERRED items to
      tracked todos, add the 🟢 ARCHIVED banner, run the codex-alignment check (this plan's own two Codex SSOTs plus any
      doc this feature makes newly-stale), update every corpus referrer's path to the parent (grep for the old filename,
      fix each hit), then move the parent to `plans/archive/2026_07/` via `git mv`. Clear `locked_by` if set.

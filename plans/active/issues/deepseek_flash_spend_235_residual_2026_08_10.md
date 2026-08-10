---
doc_type: issue
title:
  DeepSeek flash ~$2.35 real-time-vs-task-usage spend residual — root cause unknown, migrated from
  deepseek_flash_ab_routing_test archival
summary: >-
  Migrated from `deepseek_flash_ab_routing_test_2026_08_05.md`'s Deferred table (2026-08-10, batch12-finalize archival
  ritual step 1) — a prose deferral that would otherwise evaporate with the archived doc. Flash shows a ~$2.35 residual
  gap between real-time (account-usage / slot-derived) spend and task-usage-derived spend, with no review-role slots
  involved. Root cause genuinely unknown — must not be guessed; needs the same kind of direct investigation the pro
  finding got in `deepseek_flash_ab_routing_test` todo 19. Operator-gated: the investigation direction is a judgment
  call on whether to chase it (the flash account is now at steady-state usage).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [deepseek, spend, accounting, residual, operator-gated]
related:
  [
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: diagnose
locked_by:
locked_since:
resolved_by:
source: >-
  Migrated from /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md's Deferred table during its
  2026-08-10 archival (batch12-finalize ritual step 1 — never let a prose deferral evaporate).
---

# DeepSeek flash ~$2.35 real-time-vs-task-usage spend residual

## What I found

Migrated from the archived `deepseek_flash_ab_routing_test_2026_08_05.md` Deferred table (row: "Flash's own ~$2.35
residual real-time-vs-task-usage gap (no review-role slots involved)") as part of that doc's 2026-08-10 archival
(batch12-finalize). Original state: **Not done — root cause genuinely unknown, don't guess; needs the same kind of
direct investigation todo 19's pro finding got.**

## Why it matters

A ~$2.35 gap between real-time (account-usage/slot-derived) spend and task-usage-derived spend for the flash account
would silently misstate per-task cost accounting if it reflects a systematic leak rather than a one-off. The flash
account is now at steady-state usage, so the residual is bounded and low-priority — but it was never root-caused, and
the deepseek A/B-test plan's KEEP-FLASH verdict priced flash as cheaper on task-usage numbers. If the residual is a
real-time-vs-task-usage accounting divergence (not missing spend), it does NOT change the verdict; if it is missing
spend, it would. Operator decision on whether to chase it is the gate.

## Recommended decision

Operator-gated: decide whether to fund a root-cause investigation (mirroring the pro-side finding in the archived plan's
todo 19). The residual is bounded (~$2.35), so the natural posture is to let it sit unless spend accounting for the
flash account is about to be used for a pricing/calibration decision.

## Todos

- [ ] [OPERATOR] P3. **Decide whether to investigate the ~$2.35 flash real-time-vs-task-usage spend residual, and if so
      fund a root-cause pass mirroring the archived plan's todo-19 pro finding** (check whether `task_usage` sum for
      `account_id=deepseek-v4-flash` reconciles against the account's real-time usage meters / slot-derived spend; if a
      systematic divergence, file a follow-up fix). Migrated 2026-08-10 from
      `/plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md`'s Deferred table. (repo: agent-orchestrator,
      read-only DB queries to start)

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2 — the "never let a prose deferral evaporate"
  rule that drives this migration.

## Progress Log

- **2026-08-10** — Created by the batch12-finalize review as the archival-migration home for the ~$2.35 residual prose
  deferral in the now-archived deepseek_flash_ab_routing_test_2026_08_05.md. `assigned_vm: NA` (operator-gated — the
  investigation direction is a judgment call, and the residual is bounded/low-priority).

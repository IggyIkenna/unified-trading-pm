---
doc_type: issue
title:
  WorkerLivenessWatchdog's unconditional _sweep_unpushed_slots auto-pushes a dead session's held commits, silently
  defeating an open task-linked BLK acting as an operator merge gate
summary: >-
  When a worker session is reclaimed as dead, `WorkerLivenessWatchdog._sweep_unpushed_slots`
  (`worker_liveness_watchdog.py:1463-1542`) unconditionally pushes ANY committed-but-unpushed HEAD the dead session left
  behind, to `live-defi-rollout`. It has zero awareness that those very commits may be intentionally held pending an
  OPEN, task-linked `/blocked` entry acting as an operator merge gate. This is exactly what happened to the CLV
  `odds_targets` export: slot 7 filed BLK-ec018203 (operator_pending merge sign-off, guarded by the design doc's
  "OPERATOR RATIFICATION REQUIRED BEFORE MERGE"), received only an interim HOLD, then froze and was reclaimed dead at
  09:13 UTC; at 09:19:21 the watchdog's unpushed-sweep auto-pushed the held commits (now `uac@5b57f6d2` +
  `features-service@332ea5d5`) to LDR — defeating the operator gate without any agent decision. The commits are on LDR
  but not yet on `origin/main`; the next `*/15` LDR→main promote cycle would carry an unratified change to main.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, watchdog, unpushed-sweep, merge-gate, governance-bypass, blocked-queue, bug]
related: [/plans/active/issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md]
created: 2026-07-26
priority: P1
parent_epic: orchestrator_master
source:
  "worker, slot 7, hit live on sports_satellite_ao_dispatch_batch5-026 after inheriting the reclaimed session; filed as
  BLK-eccd3383 (main-agent answered partial: operator-reserved, escalated)"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# Watchdog unpushed-sweep defeats an open operator merge gate

## What happened

BLK-ec018203 was an **operator_pending** merge sign-off gate on the CLV `odds_targets` export (`uac` +
`features-service`, both QG-green), reserved to the operator by the design doc
`/plans/active/issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`'s binding guardrail **"⚠️
OPERATOR RATIFICATION REQUIRED BEFORE MERGE."** The commits were deliberately held unpushed pending that ratification
(the worker got only an interim "HOLD, escalating upward, do NOT quickmerge yet").

Timeline (all UTC, 2026-07-26):

- 08:39 — slot-7 session files BLK-ec018203 asking permission to quickmerge.
- 08:41 — interim answer only: "C — HOLD, escalating upward, do NOT quickmerge yet." Never finally ratified.
- 08:43–09:13 — that session freezes repeatedly (`frozen_at_high_context`, several `worker_kicked` nudges).
- 09:13 — `WorkerLivenessWatchdog` reclaims it as dead.
- 09:19:21 — the watchdog's unconditional `_sweep_unpushed_slots` pass pushes the dead session's held HEAD to
  `live-defi-rollout` (now `uac@5b57f6d2`, `features-service@332ea5d5` — same content, rebased onto a newer LDR tip).

Verified by the reporting worker: neither commit is on `origin/main` yet (`git merge-base --is-ancestor` fails both
ways), and UAC's current open promote PR #742 is based on the commit BEFORE ours — so there is a finite window before
the next `*/15` promote cycle picks it up.

## Root cause

`worker_liveness_watchdog.py:1463-1542` (`_sweep_unpushed_slots`) pushes ANY committed-but-unpushed HEAD left by a dead
session as a data-loss-prevention measure. It is **blind to task-linked `/blocked` gates**: it does not check whether
the slot's `task_id` (or the commits themselves) are the subject of an OPEN blocked-question that is intentionally
holding the push. A push-to-preserve is the right default for orphaned WIP, but it must not fire when the exact commits
are being held behind an unanswered operator merge gate.

## Why it matters

Every operator-gated merge that follows the "commit locally, hold the push behind a `/blocked`, wait for ratification"
pattern is silently defeatable: if the holding session dies before ratification, the safety net ships the held work to
LDR — and the standing `*/15` LDR→main auto-promote then carries an **unratified** change to `main`. The gate is
defeated by automation, not by any agent or operator decision. This is a governance-bypass class, not a one-off.

## Recommended decision

- [ ] [BACKEND] P1. Make `_sweep_unpushed_slots` **gate-aware**: before pushing a dead session's unpushed HEAD, check
      whether the slot's `task_id` has an OPEN (unanswered / partial / operator_pending) task-linked blocked-queue
      entry; if so, SKIP the push for those commits and instead surface a distinct alert
      (`unpushed_held_behind_open_gate`) so a human decides. Preserve the commits locally (do not discard) — the point
      is "don't auto-ship held work," not "lose it." Add a regression test: a dead slot whose HEAD is unpushed AND whose
      task has an open operator_pending BLK must NOT be auto-pushed. Repo: agent-orchestrator.
- [ ] [DOC] P2. Document the "hold a merge behind a `/blocked` gate" pattern's failure mode + the gate-aware sweep
      contract in the orchestrator watchdog SSOT, so future gated-merge workflows rely on the enforced skip rather than
      on the holding session staying alive.

## Progress Log

- 2026-07-26 (main agent): Filed after slot 7 reported the bypass as BLK-eccd3383. Answered that BLK
  `disposition:partial` — the after-the-fact ratification (Option A) is operator-reserved (I will not grant it); worker
  held (no repoint, no further push, no self-authorized revert); operator paged with a recommendation to revert the two
  commits from LDR to restore the pre-ratification state before the next `*/15` cycle reaches main. This doc captures
  the watchdog root cause so the fix is tracked independently of that specific merge decision.

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
status: resolved
nature: issue
asset_group: [ao]
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
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
  "agent-orchestrator@49c919d (gate-aware _sweep_unpushed_slots) + unified-trading-pm SSOT doc-fold, 2026-08-01"
locked_by:
context_scope:
  [
    /plans/active/issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/epics/orchestrator_master.md,
  ]
---

# Watchdog unpushed-sweep defeats an open operator merge gate

> **🟢 RESOLVED 2026-08-01** — both todos done: gate-aware sweep shipped `agent-orchestrator@49c919d`; SSOT doc-fold
> shipped 2026-08-01.

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

- [x] ✅ [BACKEND] P1. **DONE — `agent-orchestrator@49c919d`.** Make `_sweep_unpushed_slots` **gate-aware**: before
      pushing a dead session's unpushed HEAD, check whether the slot's `task_id` has an OPEN (unanswered / partial /
      operator_pending) task-linked blocked-queue entry; if so, SKIP the push for those commits and instead surface a
      distinct alert (`unpushed_held_behind_open_gate`) so a human decides. Preserve the commits locally (do not
      discard) — the point is "don't auto-ship held work," not "lose it." Add a regression test: a dead slot whose HEAD
      is unpushed AND whose task has an open operator_pending BLK must NOT be auto-pushed. Repo: agent-orchestrator.
      **Implementation**: `push_or_preserve_ahead_commits` (`_ahead_push.py`) takes a new `gated: bool` param — when
      True, every repo's commit is preserved on `wip-preserve/` instead of pushed, and `OrphanCommit.gated=True` is
      logged. `_sweep_unpushed_slots` (`worker_liveness_watchdog.py`) queries `BlockedRow` for an open entry
      (`answered_at IS NULL`, which also covers `partial_answer_blocked` rows per its own docstring) tied to the slot's
      `current_task`, and fires a distinct `unpushed_held_behind_open_gate` activity event per gated repo. **Done-when
      evidence**: 3 new regression tests in `tests/test_watchdog_unpushed_sweep.py` —
      `test_sweep_gates_push_behind_open_operator_blocked_entry` (unanswered row gates + preserves + distinct event),
      `test_sweep_gates_push_behind_partial_answered_blocked_entry` (a partial/interim answer still gates, since
      `answered_at` stays unset), `test_sweep_pushes_when_blocked_entry_already_answered` (a FINAL-answered historical
      row does NOT false-positive gate) — plus all 9 pre-existing tests in that module still pass (12/12). Full
      `quality-gates.sh` green (2145 passed, basedpyright 0/0/0, ruff clean).
- [x] ✅ [DOC] P2. **DONE — `unified-trading-pm` (this commit).** Documented the "hold a merge behind a `/blocked` gate"
      pattern's failure mode + the gate-aware sweep contract in
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "Held-behind-a-`/blocked`-gate merge pattern —
      failure mode + the gate-aware unpushed sweep (2026-07-26/31)" — covers the legitimate hold pattern, the 2026-07-26
      defeat sequence, the `gated: bool` mechanism (`_sweep_unpushed_slots` + `push_or_preserve_ahead_commits` + the
      distinct `unpushed_held_behind_open_gate` event), and the forward contract (route future holds through a
      task-linked unanswered `/blocked` entry — any other hold mechanism is invisible to this sweep).

## Progress Log

- 2026-07-26 (main agent): Filed after slot 7 reported the bypass as BLK-eccd3383. Answered that BLK
  `disposition:partial` — the after-the-fact ratification (Option A) is operator-reserved (I will not grant it); worker
  held (no repoint, no further push, no self-authorized revert); operator paged with a recommendation to revert the two
  commits from LDR to restore the pre-ratification state before the next `*/15` cycle reaches main. This doc captures
  the watchdog root cause so the fix is tracked independently of that specific merge decision.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — this doc's `[BACKEND] P1` gate-aware-sweep decision is the
  **prerequisite** that `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s whole `/done`-acceptance-semantics cluster is
  explicitly waiting on ('Re-triage once that doc's gate-aware sweep decision exists'), and it is a governance call
  (when may automation ship work a human deliberately held behind a merge gate). Its `[DOC] P2` sibling is an edit to
  the orchestrator watchdog codex SSOT, which is never autonomous.
- **2026-07-31**: `[BACKEND] P1` shipped (`agent-orchestrator@49c919d`) — see the flipped todo above for the full
  implementation + evidence. This clears the prerequisite the conflict-gated cluster in
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md` was waiting on for
  `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md` (test-module collision reason moot now)
  and the `/done`-acceptance-semantics items in `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` +
  `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md` (the governance question those items said they
  were "interacting with" now has a shipped answer — gate on the open blocked-queue entry, not on session liveness). Doc
  stays `status: open`: the `[DOC] P2` SSOT-documentation sibling is still unbuilt.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **2026-08-01** (slot 6, backend_engineer): shipped the `[DOC] P2` SSOT write — see the flipped todo above. Doc is now
  the only remaining open item resolved; both todos in this issue are done.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): RECLASSIFY
  `NA -> planning`. The 2026-07-30 KEEP-NA verdict was correct at the time (design-decision-pending), but its own
  prerequisite — the `[BACKEND] P1` governance decision — shipped 2026-07-31 (`agent-orchestrator@49c919d`, full test
  evidence above). The sole remaining item, `[DOC] P2`, is now a scoped, deterministic codex-SSOT documentation edit
  describing an already-implemented, already-tested mechanism (`push_or_preserve_ahead_commits`'s `gated:` param,
  `unpushed_held_behind_open_gate` event) — no open design question, no operator-only act, checkable done-when (the doc
  section exists and cites the shipped contract). Phase 2 conflict-check:
  `plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md` and this doc's own sibling
  `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md` (still `assigned_vm: NA`, unchanged this
  run) both reference the shipped `[BACKEND] P1` fix but neither claims the `[DOC] P2` SSOT-write itself — clear. Set
  `assigned_role: infra` (no prior value; closest real match in the live `agents/*.md` registry for a
  `codex/05-infrastructure/` watchdog-SSOT edit).

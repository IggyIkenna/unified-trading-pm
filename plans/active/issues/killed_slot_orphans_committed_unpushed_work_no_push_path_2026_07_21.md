---
doc_type: issue
title:
  "A killed/idle one-shot slot holding committed-but-unpushed work has no automated push-or-inherit path — the commits
  sit at drift_violation indefinitely when the backlog is gate-dominated"
summary:
  slot16 spent ~3h (03:28-06:38Z 2026-07-21) in a frozen-kick loop (watchdog soft-kicked ~55 times — 29 worker_kicked +
  19 worker_polling_dead + 7 worker_kick_failed, post_kick_classification=frozen every ~5-6 min — before it finally
  escalated to a hard-kill) and left 4 committed-but-unpushed commits behind (agent-orchestrator ahead=2,
  unified-trading- pm diverged=2, on the active plan ao_uniform_agent_liveness_contract_2026_07_20.md). After the
  hard-kill the slot went killed -> idle with worker_alive=false. There is no automated path that pushes those commits -
  orphan_reap.py has no git logic (it reaps processes/tmux only), git_health.py only _maybe_send_sync_nudge()s a LIVE
  worker (a dead worker's nudge is a no-op), and with a gate-dominated backlog (13/0/13, zero dispatchable) AutoSpawn
  has no task to re-occupy slot16 with, so no live worker ever lands on the clone to push. The work is durable
  (committed in the slot's local .git, not lost unless the clone dir is wiped) but stranded off-origin at a standing
  drift_violation. Operator was already notified via the server's own unpushed_plans_alert_sent (06:02Z).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, self-healing, watchdog, git-drift, orphaned-work, recovery-gap, liveness]
related:
  [
    plans/active/ao_uniform_agent_liveness_contract_2026_07_20.md,
    plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-07-21
author: unknown
priority: P2
parent_epic: infrastructure_master
source: "review(slot1) msg 1538 to main orchestrator + main live diagnosis, 2026-07-21"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /plans/archive/issues/host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/worktree_clean_check/_branch_state.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
  ]
depends_on: []
---

## What happened

review(slot1) flagged (msg 1538, 06:37Z) that slot16 had been stuck in a frozen-kick loop for 3+ hours. Timeline
reconstructed from the event stream + live /api/state and /api/fleet/git-health:

- slot16 was a one-shot cicd-escalation dispatch (agt-a2c243, already resolved); a stray backlog task was then
  heartbeat-dispatched onto it in error and skipped.
- 03:49Z watchdog hard-killed once (stuck_at_prompt, kills_today=1/50); 03:50Z tmux_session_lost.
- 03:50Z -> 06:32Z: ~55 recovery events (29 worker_kicked + 19 worker_polling_dead + 7 worker_kick_failed),
  post_kick_classification=frozen every ~5-6 min, **zero progress** — the soft-kick/reap cycle kept firing without
  recovering the worker.
- ~06:38Z watchdog finally escalated to a hard-kill: slot went worker_alive=false, tmux_alive=false, status=killed, then
  status=idle.
- Throughout, slot16 held committed-but-unpushed work: agent-orchestrator state=ahead ahead=2, unified-trading-pm
  state=diverged ahead=2 (origin advanced past it, so pm now needs a rebase), on
  ao_uniform_agent_liveness_contract_2026_07_20.md. Server sent unpushed_plans_alert_sent at 06:02Z.

## The gap (two parts)

**1. Recovery latency — soft-kick never escalates.** The watchdog kicked ~55 times over ~3h on a slot that presented as
idle/tmux-alive/frozen before it escalated to a hard-kill. A frozen worker that fails N consecutive
post_kick_classification=frozen checks should escalate to hard-kill + respawn far sooner than 3h, not keep soft-kicking
on a fixed ~5-6 min cadence indefinitely. (kills_today=1/50 shows the daily hard-kill budget was nowhere near exhausted
— the escalation logic simply wasn't triggering.)

**2. Orphaned committed work has no automated push/inherit path.** Once the slot is killed/idle with no live worker, its
ahead/diverged commits are stranded:

- `orphan_reap.py` reaps processes/tmux only — no git awareness.
- `git_health.py` detects the drift and calls `_maybe_send_sync_nudge()`, but a nudge targets a **live** worker; the
  worker here is dead, so the nudge is a no-op.
- With a gate-dominated backlog (measured 13/0/13, zero dispatchable), AutoSpawn has no task to re-occupy slot16 with,
  so no live worker ever lands on the clone to push.

Net: the committed work sits at a standing `drift_violation` off-origin until an operator or a coincidentally
re-occupying worker pushes it. It is durable (committed in the slot's local `.git`; only a clone-dir wipe loses it) but
it never reaches `origin/live-defi-rollout` on its own.

## Proposed fixes

- [x] ✅ [INFRA] P2. **DONE — confirmed already-implemented pre-existing code, audited + re-scoped via
      `agent-orchestrator@77fc60a` (2026-07-31, in the now-archived
      `/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`).** That plan's own claimed `[INFRA] P2` todo
      (cited below) ran its audit AFTER the `host_saturation` gate cleared and found the escalation mechanism this todo
      asks for was already shipped: `kick_escalation_threshold` (config field, default 3) was introduced in `5b07bd3`,
      and the ping-advanced-reset bug that let the 2026-07-21 incident's wedged worker dodge escalation for 55 kicks was
      already fixed in `2a48eda` — both predating this plan. `WorkerLivenessKicker._tick_once` already forces
      `_maybe_auto_respawn_stuck_slot(..., force=True)` (kills the wedged tmux session + resumes the in-flight task via
      `--resume`) once `_consecutive_kick_failures` reaches `kick_escalation_threshold`, gated on `genuinely_recovered`
      (pane verified 'working'), not merely `ping_advanced`. **This doc's own checkbox was stale** — the closeout's
      finalize plan (`ao_consolidated_closeout_2026_07_25_finalize_2026_07_30.md`) did not cite or reconcile evidence
      back into this file; flipped directly during the 2026-07-31 conflict-gated re-triage pass instead. (Prior note,
      retained for history: this todo was previously flagged "ALREADY CLAIMED by
      `/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`'s `[INFRA] P2` todo — do NOT dispatch from here"
      by `/na-eligibility-audit ao` 2026-07-30, with the sequencing gate below noted CLEARED via
      `agent-orchestrator@64b5310`.) Original gating note follows for history. **Gated 2026-07-26** (resolved
      `autonomous_session_operator_decisions_2026_07_25.md` entry #21, option A — soften first): do NOT land this
      hard-kill-escalation ahead of `issues/host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`'s
      two-window/completion-signal fix. That doc has MEASURED evidence the current classifier already fires falsely on
      live, progressing workers (zero fleet completions for over an hour, 2026-07-26) — landing faster hard-kill
      escalation on top of a known-wrong classifier turns false kicks into false hard-kills, strictly worse. Re-scope
      N/timing against the CORRECTED classifier once that fix lands, not before. Escalate the watchdog from soft-kick to
      hard-kill + respawn after N consecutive `post_kick_classification=frozen` observations (e.g. N=3, ~15-20 min)
      instead of soft-kicking indefinitely; the daily hard-kill budget (50) is ample. SSOT:
      `/codex/04-architecture/autonomous-recovery-matrix.md`.
- [ ] [INFRA] P2. Add a reclaim-and-push (or inherit) path for a killed/idle slot that git-health reports as
      ahead/diverged with `unpushed_plans`: either (a) AutoSpawn prioritises re-occupying a slot with a standing
      `drift_violation` even when the backlog is otherwise gated, tasking the fresh worker to rebase (if diverged) +
      push the orphaned commits; or (b) a dedicated reaper that inherits the commits onto a live slot. Committed work
      must not strand off-origin indefinitely.
- [x] [INFRA] P3. ✅ **DONE — the one-shot defect is resolved (verified 2026-07-23), with one wording correction.**
      `server/worker_liveness/_git_alerts.py::maybe_alert_unpushed_plans` re-fires on a 1800s (30-min)
      `persist_throttle`-backed cooldown for as long as `unpushed_plans` stays non-empty, and its caller in
      `worker_liveness/__init__.py` runs it for EVERY `SlotRow` carrying `git_status_json` with **no liveness or status
      filter** (docstring: "Coverage gap fixed 2026-07-14 … including slots with no live tmux worker") — so a dead slot
      is covered, which is exactly what this todo asked for. Shipped 2026-07-14, before the 2026-07-21 incident.
      **Correction to this todo's wording**: the re-remind is NOT a repeated Slack page — `notify_unpushed_plans` was
      D11-downgraded to `logger.info` only (2026-06-25, "git housekeeping"), so the recurring signal is an
      `unpushed_plans_alert_sent` activity event (AO log + dashboard) every 30 min. If a repeated PAGE was the intent,
      that is a separate, still-unbuilt ask — file it rather than reopening this. Original item: make the
      `unpushed_plans_alert` re-remind (state-transition dedup) while the drift persists on a **dead** slot, so a
      one-shot 06:02Z alert doesn't become the only signal for work that stays stranded for hours.

## Triage

Non-blocking for the fleet (backlog is healthy 13/0/13; the loop has stopped — slot is idle, not looping). Operator
already notified via the server's unpushed_plans_alert. Main orchestrator is barred from push/respawn, so remediation
routes through these todos + operator action to land slot16's `ao_uniform_agent_liveness_contract` commits. Filed on
review(slot1)'s behalf per the async-wait/stuck-recovery watchdog guidance.

## Recurrences

- **2026-07-25 ~02:33Z — slot 10** (flagged again by review/slot1, confirmed by main read-only). Same class: slot 10
  died **idle** (prereq-blocked on `sports_satellite_ao_dispatch_batch2-005/-007/-011`) with
  `worker_alive=false, tmux_alive=false`, holding one committed-but-unpushed commit `ed24ea184`
  (`chore(orphan-wip): inherited WIP …`, authored 02:34:08Z) on branch `plan_reconciler/agt-be8370-archive` (no
  upstream): `unified-trading-pm` ahead=1 / behind=22 vs origin/live-defi-rollout, HEAD not an ancestor. Files are 2
  plan docs (`plan_reconciler_findings_2026_07_25.md` +95, `docs_retrieval_layer_reconcile_2026_07_23.md` +7); worktree
  CLEAN so no uncommitted loss. `unpushed_plans_alert_sent` fired 02:32:16Z (operator surfaced). Confirms the open
  `[INFRA] P2` reclaim-and-push todo is still unbuilt and the gap recurs. Note: main tried the sanctioned
  `POST /api/agents/by-role/conflict_resolver/message` route (03:09Z) — it logged `agent_message_sent` but did **not**
  spawn a one-shot conflict_resolver (a by-role thread message is not a dispatch), so that is not a viable ad-hoc
  remediation either; still routes through the todo + operator. Landing needs judgment (is
  `plan_reconciler_findings_2026_07_25.md` superseded by a newer scheduled run? + a 22-behind rebase of another agent's
  branch) → correctly an operator/human call, not an auto-dispatched todo.
- **2026-07-25 ~04:48Z — slot 5** (flagged by review/slot1 msg 1931, confirmed read-only by main on-host
  ip-172-31-5-118). Same class: slot 5 died **idle** (prereq-blocked on
  `sports_satellite_ao_dispatch_batch2-007/-011/-015`) in the 04:28:17Z `tmux_session_lost` burst (slots 4/5/8/9 + a
  review predecessor, correlated with the orchestrator server reload — self-healing, tasks auto-requeued), now
  `worker_alive=false, tmux_alive=false, last_ping 04:27:38Z`. Holds **2 committed-but-unpushed `docs(plans):` commits**
  on `live-defi-rollout` (`3a44c523c` flip Eastern-Europe/UEFA checkbox — uac@dbd64914; `79dda3cc8` flip Eastern-Europe
  todo + close finalize-plan Phase-0 coverage gap): `unified-trading-pm` ahead=2 / behind=10 vs
  origin/live-defi-rollout, HEAD **not** an ancestor. **Worktree CLEAN, NO rebase state** — so this is not a stuck
  rebase blocking the FF-pull cron (review's alternate hypothesis ruled out); the cron simply cannot fast-forward a
  2-ahead diverged HEAD. Work is durable (committed in the slot's local `.git`) but stranded off-origin. These are
  doc-only plan-flip commits (low-stakes, no code), but landing them still needs a rebase-of-a-shared-branch that the
  unbuilt `[INFRA] P2` reclaim-and-push todo would automate; main is barred from push/respawn, so remediation routes
  through that todo + operator action. Second same-day recurrence (slot 10 ~02:33Z, slot 5 ~04:48Z) — the gap is
  actively recurring.
- **2026-08-12 (review agt-8d220e, from review git-health) — 3 new DIVERGED recurrences, all `unified-trading-pm` on
  ip-172-31-5-118, slots 22/26/27.** Same class as 2026-07-25 (slots 10/5) and 2026-08-04 (slots 4/10): all three slots
  are paused/`worker_alive=false` with no live tmux, each holding ONE committed-but-unpushed commit on
  `live-defi-rollout` while ~261-306 commits behind origin (HEAD not an ancestor; ff-cron cannot fast-forward a diverged
  tree). Worktrees otherwise CLEAN (no uncommitted loss). Main confirmed read-only and does NOT push (standing precedent
  — reclaim-and-push is the open `[INFRA]` P2 diverged-heal item, still unbuilt per the 2026-08-10 verdict). Orphans:
  - **slot 22** — `925233d2ba` [slot-22·planning]
    `feat(plan-hygiene): add opt-in --tranche filter to check_ag_closeout_linkage.py` — ahead=1 / behind=261.
  - **slot 26** — `86f944c931` [slot-26·planning] `docs(plans): reconcile last 3 ALLOWED_DUPLICATE_STEMS pairs` —
    ahead=1 / behind=305.
  - **slot 27** — `40d71294fc` [slot-27·planning]
    `chore(orphan-wip): inherited WIP from predecessor on slot 27 at 2026-08-11T21:06:02Z` (an inheritance commit that
    itself never landed) — ahead=1 / behind=306. **NOT preserved on origin**: `git ls-remote` shows NO `wip-preserve/*`
    ref for any of the three shas — all three are genuinely at-risk (same class as slot-4's `78a3d05fc`, 2026-08-04) if
    the clones are reclaimed/wiped. This sharpens the open `[INFRA]` diverged-heal item further: a second incident where
    the preserve-half did NOT fire for diverged killed-slot orphans (this trio + slot-4), reinforcing the 2026-08-04
    recommendation to preserve (not just attempt-push) every diverged dead-slot orphan in the unconditional sweep.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA-STALE (citation fixed, no reclassification) — the `[INFRA] P2`
  hard-kill-escalation todo is already claimed verbatim by an OPEN todo in the active `assigned_vm: planning` doc
  `/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`; flipping this doc would duplicate that dispatch. Also
  recorded that the todo's stated gate has CLEARED — the
  `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md` two-window fix it waits on shipped as
  `agent-orchestrator@64b5310`, so the closeout's todo is now unblocked. The second `[INFRA] P2` reclaim-and-push item
  stays in the deferred worker-liveness cluster.
- **2026-07-31 (conflict-gated re-triage)**: Flipped `[INFRA] P2` (hard-kill escalation speed) to `[x]` — the claiming
  plan's own audit (`agent-orchestrator@77fc60a`) found the mechanism was already shipped pre-existing (`5b07bd3` +
  `2a48eda`), and that plan is now archived, but its finalize never reconciled evidence back into THIS doc. See the
  flipped todo above for the full evidence trail. The second `[INFRA] P2` (reclaim-and-push automation) remains
  genuinely open, independent work — not gated by anything, just unbuilt.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — the
  single remaining open item offers two unresolved competing designs (AutoSpawn re-prioritization vs. a dedicated reaper
  component) touching live-dispatch-critical-path machinery — a genuine architectural fork, not a mechanically bounded
  fix. No change since the 2026-07-31 verdict above. genuinely open, independent work — not gated by anything, just
  unbuilt.
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`, dispatch agt-da0e58, slot 10): re-verified, no change —
  same single open `[INFRA] P2` reclaim-and-push item, still a genuine architectural fork (no new evidence favoring
  either design). The only file change since the 2026-08-01 verdict was an unrelated corpus-wide reference-path fix
  (`unified-trading-pm@17b53df1e`) — no content drift.
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — but the doc's own framing is now stale/narrower,
  worth a rewrite by whoever next touches it. Verified directly against the agent-orchestrator codebase (not just this
  doc's text): the "two unbuilt competing designs" framing is inaccurate —
  `WorkerLivenessWatchdog._sweep_unpushed_ slots` (`8aaf928`/`06c5f8e`, 2026-07-24) now calls
  `push_or_preserve_ahead_commits` unconditionally on every tick for every dead-session slot, fully closing the gap for
  the non-diverged sub-case. Only the DIVERGED sub-case (the original incident's actual scenario) remains genuinely
  open: a preserve+realign mechanism exists (`_branch_state.py::heal_dead_slot_branch_quarantine`) but its only call
  site is `autospawn.py::_do_spawn`, which requires a dispatchable task — so during a gate-dominated, zero-dispatchable
  backlog (exactly this doc's own incident shape) it never fires. Whether/how to extend the diverged-heal path into the
  same unconditional sweep is a real design/safety call given that code's own incident history (2 cited prior data-loss
  near-misses in its own comments) — genuinely narrower in scope than before, but still judgment-gated, not mechanical.
  Stays NA.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — narrowed from the 2 now-archived/superseded plan
  refs to the concrete source files the 2026-08-03 marker points at (`autospawn.py`, `_branch_state.py`,
  `worker_liveness_watchdog.py`), matching the doc's narrowed remaining scope (the diverged sub-case only).

- **2026-08-04 (main agt-1756f6, from review git-health #3677) — 2 new DIVERGED recurrences incl. the FIRST-EVER
  unified-trading-library instance; fired during exactly the gate-dominated low-dispatch backlog the 2026-08-03 marker
  predicts.** Both killed gracefully (`archived_lifecycle_complete=true`), clean trees, on live host ip-172-31-5-118.
  Main confirmed read-only (did NOT push: slot-10's are CODE + not my worktree; slot-4's is another slot's worktree —
  reclaim is the open `[INFRA]` diverged-heal work, not main's).
  - **slot 4 — `unified-trading-pm` ahead=1 behind=4 (DIVERGED)**, `not_clean_since` 07:02Z, killed 08:33:38Z. Orphan:
    `78a3d05fc` [slot-4·planning] "fix(plan-hygiene): clear plan_health gate — reference-path fixes, archive 20 done
    docs, NA-corpus reviewed raise". **NOT preserved**: `git ls-remote origin` shows many older
    `wip-preserve/orchestrator-slot-4-<sha>` refs but NONE for `78a3d05fc` — so this diverged orphan is genuinely
    at-risk if the clone is reclaimed/wiped.
  - **slot 10 — `unified-trading-library` ahead=2 behind=7 (DIVERGED)** — FIRST utl instance of this class (prior
    recurrences were all PM/AO), confirming the gap is repo-agnostic, not PM-specific. `not_clean_since` 07:17Z, killed
    08:33:42Z (2nd kill; the 1st was 07:41:30 mid-quickmerge — see
    `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md` 2026-08-04 entry). Orphans: `e86637c2`
    [slot-10·planning] "fix(pipeline-e2e-check): tag empty-string fallbacks in report merge loader" + parent `8caed410`
    "…merge same-day reports instead of overwriting". **These ARE preserved on origin**:
    `refs/heads/wip-preserve/orchestrator-slot-10-e86637c2` exists (tip `e86637c2` → `8caed410` in ancestry), most
    likely written by the 07:41:30 first-kill sweep. So the QG-green code is SAFE/recoverable from origin — the standing
    drift_violation is a branch-not-realigned artifact, NOT data-loss.
  - **Sharpened finding for the open `[INFRA]` diverged-heal item**: the preserve-half is UNRELIABLE for the diverged
    case, not just absent. It fired for slot-10 (e86637c2 preserved) but did NOT fire for slot-4's current `78a3d05fc`
    despite both being diverged and killed within 4s of each other — so `push_or_preserve_ahead_commits`' preserve
    branch is not reliably covering diverged killed-slot orphans. The durable fix should (a) extend the unconditional
    sweep to PRESERVE (not just attempt-push) every diverged dead-slot orphan, and (b) realign the local branch so the
    drift_violation clears once preserved. Recovery of slot-4's `78a3d05fc` is the more urgent of the two (unpreserved);
    slot-10's is safe on its wip-preserve ref.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — re-read end-to-end; sole open item (`[INFRA] P2`,
  reclaim-and-push automation for a killed/idle slot's ahead/diverged commits) remains a genuine architectural fork
  (AutoSpawn re-prioritization vs. a dedicated reaper), narrowed by the 2026-08-03/08-04 entries to the diverged
  sub-case specifically but still judgment-gated (2 prior data-loss near-misses cited in the code's own comments).
  Checked against the round7-10 precedent set (IAM self-service, D16, S5.1, plan-destination default, escalation-N,
  reversibility-qualified deletes, Option B retirement, DeepSeek/Slack credentials) — none apply; this is
  live-dispatch-critical-path git/state machinery, not a defaulted or credential-gated item. Corroborated same-day:
  `/ag-closeout-audit ao` batch12 independently lists this doc under operator-gated (22).
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Sole open item ([INFRA] P2, reclaim-and-push automation for a killed/idle slot's ahead/diverged
  commits) remains a genuine architectural fork (AutoSpawn re-prioritization vs. a dedicated reaper) narrowed to the
  diverged sub-case by the 2026-08-03/08-04 recurrence evidence, still judgment-gated by 2 cited prior data-loss
  near-misses in the code's own comments. Checked against the full round7-10 precedent set — none apply
  (live-dispatch-critical-path git/state machinery, not a defaulted or credential-gated item).

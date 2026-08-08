---
doc_type: issue
title:
  A worker repeatedly wedges at context_pct≈75 at the compact-confirmation point — it types /compact (per Tier-1 guided
  compact or a system-reminder) but the pane freezes with the command un-submitted; slot 4 hit this TWICE in under an
  hour at the same threshold. Episode 1 exhausted respawn retries (spawn_retry_cap_reached) before a kick cleared it and
  needed a manual operator kick; episode 2 self-recovered via an automatic worker_kicked. Durable fix = auto-submit the
  guided-compact confirmation + ensure the kill+resume escalation is reached before the respawn cap on a
  session-alive+pane-frozen slot.
summary: >-
  On 2026-07-25 slot 4 wedged twice in under an hour, both at context_pct=75. Episode 1 (~15:27-15:36Z): worker_polling_
  dead after 19min silence -> watchdog reclaimed+resumed 15:32:27 -> froze again 5x (frozen_at_high_context,
  context_pct=75, every ~50-70s) -> spawn_retry_cap_reached 15:36:07 (retry_count=2, session_alive=true,
  pane_state=frozen); main captured the pane read-only and confirmed it was sitting at a bare `❯ /compact` prompt TYPED
  but un-submitted above the bypass-permissions bar (the worker had self-halted per a system-reminder and typed /compact
  but never got driven past the confirmation). Cleared only after a manual operator kick (Enter). Episode 2
  (~15:39-16:04Z): froze at context_pct=75 again (10 consecutive frozen_at_high_context 15:39-15:48) -> worker_polling_
  dead 16:03:52 -> SELF-recovered via an automatic worker_kicked 16:04:43 (post_kick_classification=working,
  submit_verified=true), no manual intervention. Both episodes on slot 4 only, same threshold; other slots not showing
  it. Main read the AO context/liveness code (read-only): context_lifecycle.py fires Tier-1 proactive guided compact at
  pct >= context_compact_guidance_pct (config default 50), with client-side auto-compact as the final safety net
  underneath; worker_liveness parses "X% until auto-compact" from the TUI bottom bar and auto-kicks frozen panes via
  tmux send-keys with post-kick submit-verification, escalating consecutive VERIFIED kick failures to a force
  kill+resume but bounded by a spawn_retry_cap. Hypothesis: at ~75% used (well past the guided-compact trigger, below
  the client auto-compact boundary) slot 4 reaches a state where a /compact is typed but the pane wedges at the
  confirmation un-submitted (same wedge class as episode 1's captured pane); why slot 4 specifically clusters at 75% is
  unknown (candidate: a heavier/longer-lived session that plateaus there and re-hits the guided-compact->freeze
  interaction). The watchdog CAN clear it (episode 2), so this is bounded — but episode 1 needed a human because respawn
  retries hit spawn_retry_cap before a kick verified-submitted.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    worker-liveness,
    context-lifecycle,
    compact,
    wedge,
    frozen-at-high-context,
    auto-spawn,
    watchdog,
    spawn-retry-cap,
    throughput,
  ]
related:
  [
    /plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/archive/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-25
author: unknown
last_updated: 2026-08-08
priority: P1
parent_epic: orchestrator_master
source:
  "operator (agt-52bb99 msg 2023 + 2025) reported both wedge episodes; main (agt-52bb99) captured episode-1 pane
  read-only + read the AO context_lifecycle/worker_liveness code, 2026-07-25 ~15:36-16:06Z"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    agent-orchestrator/server/worker_liveness/_respawn.py,
  ]
depends_on: []
---

# Worker recurring wedge at context_pct≈75 at the compact-confirmation point (slot 4, 2 episodes/hr)

## Evidence (operator-reported + main read-only capture/code-read, 2026-07-25)

- **Episode 1** (~15:27-15:36Z, msg 2023): slot 4 `worker_polling_dead` (19min heartbeat silence) → watchdog reclaimed +
  resumed 15:32:27 → froze again 5× (`frozen_at_high_context`, `context_pct=75`, every ~50-70s) →
  `spawn_retry_cap_reached` 15:36:07 (`retry_count=2`, `session_alive=true`, `pane_state=frozen`). Main captured
  `orch-slot-4:0.0` read-only: input bar showed `❯ /compact` **typed but un-submitted** above the bypass-permissions
  bar; the worker had self-halted per a system-reminder ("Everything is safe to compact — I'm stopping here… Please run
  /compact manually"), typed /compact, and never got driven past submission. Cleared only after a **manual operator
  kick** (Enter).
- **Episode 2** (~15:39-16:04Z, msg 2025): froze at `context_pct=75` again (10 consecutive `frozen_at_high_context`
  15:39-15:48) → `worker_polling_dead` 16:03:52 → **self-recovered** via an automatic `worker_kicked` 16:04:43
  (`post_kick_classification=working`, `submit_verified=true`). No manual intervention.
- Both episodes: **slot 4 only, same `context_pct=75`**; other slots not exhibiting it.

## Code reads (read-only, agent-orchestrator)

- `server/context_lifecycle.py`: Tier-1 proactive guided compact fires at
  `pct >= cfg.tuning.context_compact_guidance_pct` (config default **50**); "Client-side auto-compact stays underneath
  as the final safety net."
- `server/worker_liveness/__init__.py`: parses `"X% until auto-compact"` from the TUI bottom bar (`_AUTO_COMPACT_RE`) —
  the client auto-compact boundary is near ~0% remaining (~100% used). The kicker auto-kicks frozen panes via tmux
  send-keys with **post-kick submit-verification** (`submit_verified`), escalates **consecutive VERIFIED kick failures**
  to a force **kill+resume**, but is bounded by a **`spawn_retry_cap`**.

## Hypothesis (needs owner confirmation)

At ~75% used — past the Tier-1 guided-compact trigger (50), below the client auto-compact boundary — slot 4 reaches a
state where a `/compact` is typed (by the guided-compact path or a self-issued system-reminder) but the pane wedges at
the confirmation **un-submitted**, i.e. the exact wedge class captured in episode 1. Why slot 4 clusters at 75%
specifically is unknown; candidate is a heavier/longer-lived session that plateaus near 75% and repeatedly re-hits the
guided-compact→freeze interaction while other slots compact/recycle at different points. The watchdog can clear it
(episode 2), so blast radius is bounded to that slot's throughput — but episode 1 required a human because respawn
retries hit `spawn_retry_cap` before a kick verified-submitted.

## Todos

- [ ] [BACKEND] P2. Confirm whether the Tier-1 guided compact (or a self-issued /compact) leaves a **typed-but-
      un-submitted** `/compact` in the pane, and make the confirmation **auto-submit / self-drive past it** (mirror the
      `scripts/agent/self-compact.sh` submit path so a guided compact never strands at the confirmation). **Done when**:
      a worker driven into guided compact at ≥ the guidance threshold submits /compact without a human Enter, verified
      by a pane-state test.
- [ ] [BACKEND] P2. Ensure a **session-alive + pane-frozen** slot reaches the kicker's **force kill+resume BEFORE
      `spawn_retry_cap_reached`** — episode 1 exhausted respawn retries while a verified kick (episode 2) would have
      cleared it. Audit the ordering of the consecutive-kick-failure → kill+resume escalation vs the respawn cap. **Done
      when**: a simulated frozen-but-alive pane is force-resumed rather than hitting the retry cap.
- [ ] [BACKEND] P3. Add per-slot **context-plateau detection** — a slot repeatedly re-hitting the same `context_pct`
      wedge (≥2 `frozen_at_high_context` at the same pct within a window) is proactively force-compacted/flagged rather
      than left to freeze.
- [x] ✅ [BACKEND] P2. **A distinct, now-confirmed contributing cause** (2026-08-06, slot 14 live incident — see
      Progress Log): `classify_pane`'s `_SPINNER_RE` didn't recognize the CLI's own "N shell(s)/monitor(s) still
      running" spinner subtitle (rendered with NO "esc to interrupt" hint) as an active-turn marker, so a worker
      legitimately waiting on a backgrounded Monitor/shell per this workspace's own async-wait-discipline rules — with a
      self-drafted follow-up note queued in its input box — read as `frozen` instead of `working`, cycling
      `frozen_at_high_context` and `spawn_retry_cap_reached` for a worker that was never actually stuck. This is
      NARROWER than item 1's original `/compact`-specific hypothesis (it covers any self-typed note during a
      Monitor/shell wait, not just `/compact` confirmations) and does not close item 1 — a wedge with no Monitor/shell
      active is still unexplained. Fixed: widened `_SPINNER_RE` to recognize the pattern, 2 regression tests added. —
      `agent-orchestrator/server/worker_liveness/__init__.py`.

## Triage / charter note

Filed by main (agt-52bb99) per the big-finding triage rule (recurring cross-cutting agent-orchestrator infra pattern, 2×
in under an hour on one slot, operator-flagged). Main diagnosed via a **read-only** episode-1 pane capture + read-only
reads of the AO context-lifecycle/worker-liveness code, and is charter-barred from tmux send-keys to worker panes, from
spawning/killing/respawning slots, and from editing AO runtime state — so the fixes are BACKEND/DEVOPS-owned. Severity
**P1** (bumped 2026-08-07, was P2): two things changed since 07-25 that were not true then — (1) scope is fleet-wide now
(8 distinct slots/hr, 4+ task_ids bouncing 2-3x each on 2026-08-07) not slot-4-isolated (2 episodes/hr); (2)
account-ceiling pressure is no longer hypothetical — sub-a 96%/5h15 (over the 95% weekly ceiling), sub-b rate_limited
100%/5h0, sub-c and sub-d both 99% weekly, only sub-e has real headroom (56%/5h35) and is the sole failover absorbing
load. Every kill+respawn cycle re-burns context on whichever account it lands on, so this bug now directly compounds
capacity risk, not just reliability — see Progress Log 2026-08-07.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — named directly in
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s conflict-gated Deferred entry for the worker-liveness / watchdog
  kick+escalation cluster ('its second todo also reorders the kill+resume-vs-`spawn_retry_cap` escalation'). All 3 todos
  touch that same kick/escalation mechanism, whose directional ordering was an operator call; do not draft competing
  work against it.
- **2026-07-31 (conflict-gated re-triage)**: The cluster's ordering question IS now ruled + shipped (soften first
  `@64b5310`, harden confirmed pre-existing `@77fc60a`) — but re-checking item 2 specifically against the live code
  (`server/worker_liveness/_respawn.py::maybe_auto_respawn_stuck_slot`) shows the FORCE kill+resume path already fires
  at `kick_escalation_threshold` (3 consecutive kick failures) and bypasses the `last_ping`-freshness gate entirely — so
  the mechanism this item asks for (force-resume reachable before/without waiting on `spawn_retry_cap`) appears to
  already exist. What's NOT confirmed: whether `spawn_retry_cap`/`retry_count` counts EACH force-resume attempt
  (plausible reading of episode 1's `retry_count=2` after 5 consecutive freezes — 2 force-resumes already attempted and
  failed to clear the SAME wedge before the cap hit), in which case the real gap is "the resume doesn't fix a recurring
  identical wedge," not "ordering." **Not resolved by this re-triage — needs a live trace or a direct test of a slot
  that force-resumes into the identical wedge twice**, so item 2 stays open pending that check. Items 1 (auto-submit
  `/compact`) and 3 (context-plateau detection) were never actually blocked by the ordering question — independently
  actionable now (item 1 in particular would make this whole escalation race moot by preventing the wedge in the first
  place).
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid —
  re-verified the 2026-07-31 re-triage's item-2 finding against live code
  (`server/worker_liveness/_respawn.py::maybe_auto_respawn_stuck_slot`); still unresolved pending a live trace/test as
  that entry states. Items 1 and 3 are independently actionable but neither prior pass reclassified them — concur with
  that caution, this stays a judgment-gated live-dispatch-critical-path change, not a clean AO todo.

- **context-scout 2026-08-03**: refreshed context_scope (5 entries — added
  `agent-orchestrator/server/worker_liveness/_respawn.py`, the module the doc's own unresolved item-2 investigation
  targets directly).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **2026-08-06 (interactive session, live incident investigation)**: Investigated a fresh live occurrence — slot 14
  (`cefi_tardis_derivative_ticker_historical_gap-002`) showed `worker_alive: false` / `phase: pre_boot` after a
  heartbeat-silence respawn, following a burst of `frozen_at_high_context` + two `spawn_retry_cap_reached` events. Read
  the full `/api/activity?slot=14` history (SSM, read-only) and the exact `spawn_retry_cap_reached.details.pane_tail`
  payloads — NOT the originally-hypothesized `/compact`-typed-unsubmitted wedge (every `forced_compact`/
  `forced_precompact` event in the window shows `submitted: true`, and a real compaction to 15% landed cleanly). The
  actual captured pane tail: `✻ Brewed for 34s · 1 shell still running` / `❯ check the watchdog log again in 20 minutes`
  — a worker correctly following the async-wait-discipline pattern (backgrounded VM-backfill watch via Monitor), with
  its own queued follow-up note sitting unsubmitted, no `esc to interrupt` hint anywhere in the tail. Root-caused to
  `classify_pane`'s spinner regex not recognizing this CLI status text as an active-turn marker. Fixed +
  regression-tested (see new todo above); did not touch the pane (main stays charter-barred from tmux send-keys / kill /
  respawn per this doc's own triage note). Slot 14 self-recovered via the existing watchdog before the fix even shipped
  (confirmed live pane capture: clean, working, checkpoint committed) — bounded blast radius, consistent with this doc's
  episode-2 pattern.

- **2026-08-07 (review agent, fleet-wide recurrence + scope widening, ticks 74-77)**: Independently tracking a
  fleet-wide context_wedge_recovered/tmux_session_lost rate spike, traced it to this doc before filing a separate one —
  same mechanism (typed-but-unsubmitted /compact freeze near high context), now measured across 8 distinct slots/hr
  (4,5,6,7,8,11,13,15/16 across the window) vs the original slot-4-only/2-per-hr report — a real widening, not a new
  bug. 4+ task_ids each kill+respawned 2-3x today: infra_health_audit_alert_coverage_gaps-001 (2x, resolved), -002 (now
  3x as of ~18:30Z, still tracked), defi_satellite_ao_dispatch_batch9-018 (2x, resolved clean on 3rd attempt —
  underlying task itself succeeded, a legacy-data purge verification), sports_satellite_ao_dispatch_batch10-004 (1x,
  resolved), defi_jupiter_venue_registration_and_live_connector_wireup-005 (3x, the single worst instance, hit
  context_used_pct=100 on its 4th attempt). **Possible answer to this doc's own open question (why does it cluster on
  certain slots)**: today's data suggests task SHAPE may be the real variable, not slot identity — 3 of 4 repeat
  task_ids are exploration-heavy (VM launch-status polling/log-reading, or multi-file pattern-learning before writing
  code) vs the fast single-file checkbox-flip tasks that never wedge in this dataset. Not confirmed — a single day's
  sample, and the task-shape axis needs the bucketing this doc has not yet had capacity to run (would extend Hypothesis
  section / could become a 4th todo: bucket wedge events by task shape vs backlog share). Priority bumped P2->P1 this
  entry — see Triage note — because repeated respawns now compound real account-ceiling pressure (4 of 5 sub-accounts
  at/over weekly limits), not just a bounded single-slot throughput nuisance. Existing 2 open [BACKEND] todos
  (auto-submit the compact confirmation; force-kill-before-cap ordering) remain the right fix target — this entry is
  additive evidence, not a new root cause.

- **2026-08-08 (review agent, second data point on a higher-threshold wedge sub-mode)**: Two occurrences now of a wedge
  shape distinct from this doc's original ~75%-typed-but-unsubmitted-compact-freeze mechanism — a higher-threshold
  (92-96%) genuine compact-ineffective mode. Instance 1: slot-3, ~92%, framed as "context-wedged... /compact could not
  run (session over the models hard limit)". Instance 2: slot-9, context climbed 92%->94%->96% over ~6min (2026-08-08
  01:53-01:59Z); forced_compact/forced_precompact fired repeatedly, forced_compact_ineffective logged at 96%
  (pct_at_force=94, 300s since force, verdict=re-armed) — i.e. the compact genuinely did not clear the session, not a
  display/UI-confirmation stall. 3 consecutive worker_kick_failed(idle) followed, then slot_wedged_killed_for_resume
  (forced kill+requeue), then slot_resume_skipped correctly refused to resume since context
  96%>=resume_fresh_context_pct 80% (would immediately re-wedge), followed by a second near-identical
  context_saturated_session_lost_task_requeued. The resume_fresh_context_pct=80% threshold was traced to
  agent-orchestrator@998574b (dated 2026-07-27, predates this issue doc's own discovery) — this is existing containment
  logic working correctly on the wedge, not a new fix. Good news: both instances completed the full
  wedge->kill->requeue->fresh-spawn-productively-working cycle in well under a minute, a much better outcome than this
  doc's original episode-1 (exhausted retries, needed manual operator kick). No data loss confirmed in instance 2 (one
  staged-but-uncommitted routine progress-banner text update survived in the worktree post-kill, picked up cleanly by
  the next dirty-state sweep). Open question, not yet resolved: whether this 92-96%-hard-limit-ineffective-compact mode
  and the original ~75%-typed-unsubmitted-confirmation-stall mode are the same underlying mechanism at different
  severities, or two genuinely distinct wedge causes sharing one doc — flagging for whoever next reads the actual
  _respawn.py / compact-confirmation logic to determine, per the earlier 2026-08-08 addendum on this same open question.

- **na-eligibility-audit 2026-08-08** (ao tranche): KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` = **3**,
  matching (item 4 already closed). Re-confirms every prior pass's caution: all 3 survivors touch core
  watchdog/kill-resume/context-lifecycle machinery — live-dispatch-critical-path code every worker (including this one)
  depends on — and the doc's own two most recent entries (2026-08-07 fleet-wide scope widening; 2026-08-08 a SECOND,
  possibly-distinct high-threshold wedge sub-mode with an explicitly unresolved same-root-cause-or-not question) show
  this is still actively being characterized, not settled enough for a bounded worker fix. Not re-litigated.

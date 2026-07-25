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
asset_group: [cross-cutting]
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
    /plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/active/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P2
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

## Triage / charter note

Filed by main (agt-52bb99) per the big-finding triage rule (recurring cross-cutting agent-orchestrator infra pattern, 2×
in under an hour on one slot, operator-flagged). Main diagnosed via a **read-only** episode-1 pane capture + read-only
reads of the AO context-lifecycle/worker-liveness code, and is charter-barred from tmux send-keys to worker panes, from
spawning/killing/respawning slots, and from editing AO runtime state — so the fixes are BACKEND/DEVOPS-owned. Severity
**P2**: episode 2 self-recovered (bounded blast radius = one slot's throughput), but the pattern is confirmed +
recurrence-prone and episode 1 needed manual intervention.

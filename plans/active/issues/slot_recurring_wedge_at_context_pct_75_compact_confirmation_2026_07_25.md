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
last_updated: 2026-08-17
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

- [x] ✅ [BACKEND] P1. **A saturated session no longer burns the full retry budget before recovery** —
      agent-orchestrator@b52dd1910, deployed + verified live. `_rearm_if_force_ineffective` re-armed a forced `/compact`
      for `context_force_compact_wedge_after_failures` (3) x `context_force_compact_retry_after_seconds` (300s) = **15
      minutes of a dead slot**, plus 3 more `/compact` submissions, on a session that cannot compact by construction.
      Above `resume_fresh_context_pct` this codebase ALREADY treats a transcript as unrecoverable —
      `resume_lifecycle.classify_dead_worker` and BOTH of `worker_liveness_watchdog`'s resume paths refuse to reload
      one, citing the same reason this function's own docstring gives (past the hard limit every request 400s,
      `/compact` INCLUDED, because compaction must send the whole history to summarize it). This retry loop was the last
      place not honouring it. **Measured live 2026-08-08**: slots 5/7/8/9/11 all pinned at 100% cycling
      `forced_compact_ineffective verdict="re-armed"` at `consecutive_ineffective=1` — two full windows short of
      recovery — while 174 tasks were claimable and 6 dispatched. The FIRST force is still attempted (the threshold is a
      "too full to reload" heuristic, not the model's exact limit, so a compact at 85% may work); what changed is that
      an INEFFECTIVE force while still saturated is no longer re-armed. Sub-threshold sessions keep their full budget —
      test-locked both directions. Activity row now carries `saturated`/`saturation_threshold_pct` so the short-circuit
      is distinguishable from a budget-exhausted wedge. NOTE this does NOT close items 1-3 below: those are the
      typed-but-unsubmitted confirmation, the kick-vs-respawn-cap ordering, and plateau detection — all distinct from
      the saturation short-circuit. Evidence: `quality-gates.sh` green — 2711 python (2 new), basedpyright 0/0, tsc
      clean, 262 vitest. (repo: agent-orchestrator)
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
- **2026-08-08 ~12:00 UTC (interactive session, slot 1) — NEGATIVE RESULT, measured: `agent-orchestrator@d6f3df2`'s
  out-of-band pane sampling is STRUCTURALLY INERT. Do not build on it.** The diagnosis it was built on is correct —
  `context_worker_force_compact_pct` is 60, yet forces demonstrably fire at 90-100 (`"was NN at force"`), because the DB
  column only advances on a worker-INITIATED call, so a worker in a long tool-heavy stretch is invisible until it calls
  back in already saturated. The chosen REMEDY, however, cannot work: it reads the pct out of the tmux pane via
  `derive_context_used_pct(capture_pane(...))`, and **the Claude CLI in this version never renders a context percentage
  in the pane at all**. Measured directly: all 10 live worker panes returned `<no context readout>` when grepped for
  `context (left|low|remaining)` / `NN% context` / `context: NN%` — **including `orch-slot-4`, whose
  `slots.context_used_pct` was 100 at that moment**. So `_pane_pct()` returns `None` on every tick, the
  `if pane_pct is not None and pane_pct > db_pct` branch in `ContextLifecyclePolicy._read_pct` never fires, and nothing
  is sampled or persisted. The observed 90-100 force values are simply the worker's own last self-report, unchanged by
  the fix. **Validation numbers (fix loaded live 11:32:11 UTC, PID 2205409, confirmed in-process via
  `inspect.getsource`)**: 11:32→11:58 (26 min) = **4 terminal wedges, forces at 95/97/97/100** — i.e. ~9.2 wedges/hr
  against a pre-fix baseline of 41 wedges in the 6h 05:32→11:32 (~6.8/hr). NOT an improvement; the 60-min validation
  window was terminated early on this evidence rather than burning further ticks, per the dispatch's own "if wedges
  appear, STOP and diagnose". **SECOND, INDEPENDENT failure mode found in the same pass — this is item 2 of this doc,
  now with direct evidence.** `orch-slot-4`'s pane showed `❯ /compact` sitting in the input box under "Press up to edit
  queued messages": the forced `/compact` was DELIVERED but never SUBMITTED. So even a force that fires at the right
  moment does not necessarily execute — which is consistent with this doc's long-standing "typed-but-unsubmitted
  `/compact` confirmation" hypothesis and is the first time it has been caught in a live pane capture rather than
  inferred. **Where a real fix has to come from**: any context signal that exists independently of what the CLI chooses
  to render. The session transcript JSONL is the obvious candidate (it grows monotonically and is readable at any time,
  with no dependence on pane rendering or on the worker calling in) — `/ao-context-metrics` already scans transcripts
  for exactly this kind of measurement. Whatever is chosen, the acceptance test is the one this session used and which
  any future attempt should re-run BEFORE claiming success: capture live panes and assert a non-null pct is actually
  observable at mid-range, then measure `"was NN at force"` and require the distribution to move DOWN, not just "no
  wedges for a while". `d6f3df2` shipped QG-green with 5 passing unit tests and still did nothing in production — green
  tests proved the code path, not the premise.

- **2026-08-08 (interactive session, slot 1) — ROOT CAUSE FOUND AND FIXED; it was not (only) pane blindness.** Ran this
  doc's own acceptance test first, before writing any code. It confirmed the pane is blind (`"% context used"` matched
  **0/11** live worker panes, `"% until auto-compact"` **2/11**) — but the decisive finding was a second, larger defect
  underneath it. `orch-slot-8` on `claude-sonnet-4-6` held **165,797 tokens** while its OWN pane read **99% used**,
  implying a ~167K usable window. `model_tier.context_window()` returned **1M for every model except Haiku**, so AO
  computed `165797/1e6 = 16%` for a session the CLI itself considered full. **The denominator was 5x too big for the
  model then carrying most of the fleet** — every threshold was unreachable by construction. That is why the pre-fix
  force distribution has NO value below 91: measured over 3h before the fix, 29 wedges (~9.7/hr) and forces at
  `100 x28 · 99 x5 · 97 x5 · 96 x5 · 93 x4 · 95 x3 · 94 x3 · 91 x3`. AO only ever saw a high number when the pane's
  end-of-life auto-compact countdown appeared.
- **The window is now LEARNED, not tabulated** (operator ruling this session: "shouldn't be hardcoded, should adapt to
  the model — deepseek, sonnet, whatever"). `server/context_probe.py` reads `message.usage` from the session transcript
  — present on EVERY assistant turn, so it works mid-range where the pane is silent — and divides by a per-model window
  inferred from observation: exact calibration from a pane pct when one is visible, else the observed high-water mark,
  else the `model_tier` prior. A corpus scan over **17,974 transcripts** separates the tiers with no table: opus-4-8
  999,934 · sonnet-5 937,882 · deepseek-v4-flash 917,159 · deepseek-v4-pro 425,572 · sonnet-4-6 171,577 · haiku-4-5
  104,369. Note `deepseek-v4-pro` sits BELOW `deepseek-v4-flash` despite **more** sessions (671 vs 518) and **more**
  turns (87,828 vs 70,202) — not under-sampling, a genuinely smaller window, and precisely the kind of fact a
  hand-written table gets backwards.
- **Two measurement traps, both hit while building — the guards are load-bearing.** (1) `model: "<synthetic>"` records
  carry a zero-token `usage` block and are frequently the LAST record: a naive "last usage wins" read reported 0% for
  full sessions on **8/21** slots in the first probe run. (2) A `compact_boundary` AFTER the last usage record means the
  reading describes the pre-compact session; reporting it would force a second, pointless compaction. Both are asserted
  in `tests/test_context_probe.py`, which also pins the old arithmetic (`int(165797*100/1e6) == 16`) so the defect
  itself is documented, not just the fix.
- **Shipped** `agent-orchestrator@c6e6d982a` (QG green: 2746 passed, basedpyright 0 errors, 262 dashboard tests).
  **Deployed and verified live** on the orchestrator VM at 13:10:57 UTC — `git` HEAD `c6e6d98`, service PID 2406505 ->
  90097, and `context_window_for("claude-sonnet-4-6")` evaluated **in that process** returns `200000`. Verifying the new
  code is loaded in the RUNNING process (not merely present on disk) is deliberate: the previous attempt was reported
  live while the process predated it.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:1be52e05bdc6eb3a]: KEEP-NA — item 5 (re-run the 60-minute context-signal validation) is ALREADY claimed by the active `ao_satellite_ao_dispatch_batch21_2026_08_16.md` (its todo 1 cites this doc by path, still open there too); leave open, do not duplicate. Items 1-4 stay KEEP-NA valid — live-dispatch-critical-path watchdog machinery still being actively characterized, per 5+ prior audit passes.

## Follow-ups from the 2026-08-08 root-cause session

- [x] ✅ [BACKEND] P2. **Do not spend the force latch on a merely-QUEUED `/compact`.** `tmux_spawn.submit_to_pane()`
      returns True when the text leaves the input box, and its own docstring counts "consumed by an already-running
      turn" as success — but a message consumed into the CLI's queue ("Press up to edit queued messages", caught live on
      `orch-slot-4`) has NOT executed. The caller then sets `forced_at`, and the compaction that never ran counts toward
      `ineffective_forces` -> terminal wedge. Detect the queued-messages state and hold the latch un-spent until the
      queue drains, rather than re-sending (which would compact twice). Lower priority now that forces fire with real
      headroom instead of at 99%. **✅ DONE 2026-08-09 — `agent-orchestrator@a1e2969`** ("fix(context-lifecycle): hold
      force-compact latch on a queued-not-executed pane") — adds `tmux_spawn.pane_has_queued_messages()` +
      `_TargetState.queued_since`, holding the latch un-spent while the pane shows a queued-not-executed message.
      **Verified 2026-08-14 (code-audit sweep)**: commit confirmed live in `agent-orchestrator`; missed by the
      2026-08-10 na-eligibility-audit pass.
- [x] ✅ [BACKEND] P2. **DONE 2026-08-08 — `unified-trading-pm@8bff8f5792`** ("fix(precompact): measure local context
      from the transcript, learn the window per model", verified ancestor of `origin/live-defi-rollout`). **Port the
      measured signal to the local watcher.** `scripts/dev/precompact-watcher.py` now reads the session transcript and
      learns the per-model window the same way `context_probe.py` does (was pane-only + a hardcoded
      `_DEFAULT_CONTEXT_WINDOW_K = 1000` divisor). Verified end-to-end against a real local session per this doc's own
      Progress Log entry above (cwd encoding resolves to the true project dir; 24% reading for a `claude-opus-5` session
      at 239,867 tokens).
- [ ] [BACKEND] P3. **Re-check the learned windows once the fleet is fully on sonnet-5.** The high-water mark only ever
      rises, which is the safe direction, but a model whose sessions never run long keeps an under-estimated window and
      will compact earlier than necessary. `learned_context_windows.json` sits next to `state.db`; deleting it is safe
      and forces re-learning from the priors.

- **2026-08-08 — SECOND defect found and fixed while shipping the first; caught by testing, not by review.** The
  learned-window logic in `c6e6d982a` treated any high-water mark as the model's ceiling. Testing the local port against
  a REAL session (not a fixture) exposed the flaw immediately: a fresh registry saw ONE in-flight `claude-opus-5`
  session at 222,121 tokens and reported **97% full when the truth was ~22%** — the mirror image of the original bug,
  and it would force a compaction immediately and forever after. It was live for ~17 minutes, and the cache proves it
  was not hypothetical: the deployed buggy version had already written
  `"claude-sonnet-5": {"watermark_tokens": 355496}`, which would have force-compacted a sonnet-5 worker at a real ~30%.
  **One session reaching N proves the window is AT LEAST N, never that it stops there.** A watermark now becomes a
  window estimate only once observations CLUSTER near it (3 hits within 5%); exceeding it resets the hit count, since a
  higher ceiling voids the earlier saturation evidence. Shipped `agent-orchestrator@9b269c0ce`, redeployed 13:27:26 UTC,
  stale cache reset. Cold-start verified in-process: opus-5 -> 1,000,000, sonnet-4-6 -> 200,000, and one 222,121
  observation leaves opus-5 at 1,000,000.
- **ACCEPTANCE TEST PASSED — the distribution moved DOWN, which is what this doc demanded.** Pre-fix baseline over 3h:
  29 wedges (~9.7/hr) with forces at `100 x28 · 99 x5 · 97 x5 · 96 x5 · 93 x4 · 95 x3 · 94 x3 · 91 x3` — **nothing below
  91**. Seven seconds after redeploy:

  ```
  13:27:33 FORCED /pre-compact on orch-slot-5 (worker): pct=66 submitted=True
  13:28:39 FORCED /compact     on orch-slot-5 (worker): pct=66 submitted=True (post-precompact)
  ```

  A force at **pct=66** was structurally unreachable before. The other half of the acceptance test — "a non-null pct is
  actually observable at mid-range" — also passes: slot pcts now read `66 · 55 · 48 · 48 · 47 · 45 · 20 · 0` across the
  fleet, where previously only a pane at 91-100 ever produced a number at all.

- **Local watcher ported** — `unified-trading-pm@8bff8f5792` gives `scripts/dev/precompact-watcher.py` the same measured
  signal and learned window (it had both original defects: pane-only, and a hardcoded 1M divisor). Verified end-to-end
  against a real local session: the cwd encoding resolves to the true project dir, and the reading is 24% for a
  `claude-opus-5` session at 239,867 tokens.
- **Process finding, filed separately**: this session lost the same working file THREE times to concurrent prek
  stash/restore cycles in the shared checkout — silently, with no stash entry and a clean `git status`. Recovered only
  from a scratchpad backup. See
  `/plans/archive/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`.

## 2026-08-08 validation window — measured result (partial pass, stated plainly)

**The force-distribution criterion PASSED decisively.** 24 forces over the 52-minute window, distributed
`60 x2 · 62 · 63 · 64 · 66 x2 · 71 · 73 x2 · 76 x2 · 77 · 79 x4 · 82 x3 · 83 x2 · 85 x2` — range **60-85**. The pre-fix
baseline was 56 forces, **all 91-100** (28 of them at exactly 100). The two ranges do not overlap at all. This is the
metric this doc specified ("require the distribution to move DOWN, not just 'no wedges for a while'").

**The zero-wedges criterion did NOT pass: 4 wedges occurred.** Rate roughly halved (9.7/hr pre-fix -> 4.6/hr) but did
not reach zero, so the stated termination condition was not met and this is recorded as a partial pass.

All four were **inherited saturation**, not new failures:

```
13:42 slot=12 at 93%   13:43 slot=3  at 83%
13:49 slot=8  at 97%   13:49 slot=10 at 82%
```

Each was a session that had accumulated its context under the OLD blind regime and was already at 82-97% the first time
the new signal could see it — past the point where `/compact` can run at all (the log's own words: "session over the
model's hard limit"). The fix cannot rescue a session that is already saturated when it goes live; it can only prevent
one from getting there. Consistent with that reading, the wedge count froze at 4 from 13:58 onward while the fleet ran
at <=56%, and the per-sample fleet maximum traced `66 -> 93 -> 97 -> 56 -> 56 -> 45` — the middle peak is the inherited
backlog draining, the tail is steady state.

**What this does and does not establish.** It establishes that forces now fire with real headroom and that the fleet
reaches and holds a healthy distribution. It does NOT by itself establish a clean 60-minute window on a fleet that was
healthy at the start, because the first 30 minutes were spent draining pre-existing saturation. A second window was run
against the already-clean fleet specifically to close that gap rather than claim the criterion on 21 minutes of tail
data.

- [x] ✅ [BACKEND] P2. **Re-run the 60-minute validation after any future change to the context signal, starting from a
      fleet with no slot above ~60%.** The first run's headline number (4 wedges) is dominated by inherited saturation
      and understates the fix; a clean-start window is the only way to measure the steady state honestly. Baseline to
      beat: forces in 60-85, zero wedges. — ✅ DONE 2026-08-17 (slot 12, `ao_satellite_ao_dispatch_batch21` todo 1):
      PASS on both criteria. See "2026-08-17 validation window — measured result" below for the full write-up.

## 2026-08-17 validation window — measured result (PASS, both criteria)

Re-run per the 2026-08-08 session's own stated follow-up ("re-run after any future change to the context signal,
starting from a fleet with no slot above ~60%"). Multiple qualifying commits landed since then (`a1e2969`, `59d9417`,
`c00dc13`, `acc41b1`, `4af78dc`, `ac9ba18`, `905c210`, `c730f46`, `e943d72`+), and the boundary-confirmed-compaction
fix (`context_lifecycle.py::_tick_target`, `agent-orchestrator@9ba4391e60`, per the tracker's Track 1) landed in the
same window with no re-validation recorded since 2026-08-10.

**Pre-flight**: confirmed via `GET /api/state` that every `status=working` slot sat at ≤60% context (max was exactly
60%; two `idle`/`stale` outliers at 64%/69% don't count — idle sessions don't accumulate force-compact events). This
is a genuine clean start, not a partially-drained fleet like the 2026-08-08 run's first 30 minutes.

**Method**: a background monitor polled `GET /api/activity?types=forced_compact,forced_precompact,forced_compact_
ineffective,frozen_at_high_context,spawn_retry_cap_reached,slot_wedged_killed_for_resume,context_saturated_session_
lost_task_requeued,context_wedge_recovered,worker_kicked,worker_kick_failed,tmux_session_lost&since=<window_start>`
every 10 minutes for 60 minutes (window: `2026-08-17T06:01:54Z` → `2026-08-17T07:02:15Z`), then pulled the full event
set for the window and computed the `details.pct` distribution of `forced_compact`/`forced_precompact` events plus a
count of wedge-terminal events (`spawn_retry_cap_reached` / `slot_wedged_killed_for_resume` / `context_saturated_
session_lost_task_requeued`).

**Result — PASS on both criteria the 2026-08-08 follow-up specified:**

- **Force-distribution criterion: PASS.** 21 forces (11 `forced_compact` + `forced_precompact` pairs across 2 slots),
  distribution `60×11 · 69×10` — every force between 60 and 69, entirely inside the 2026-08-08 baseline's 60-85 range
  and tighter than it. All 21 forces came from just two sessions (slot 2 repeatedly at 69%, slot 27 repeatedly at
  60%) — both plateaued at their own threshold rather than climbing, consistent with a compact that's landing
  correctly each cycle (no `forced_compact_ineffective` events fired for either).
- **Zero-wedges criterion: PASS — the criterion the 2026-08-08 run explicitly did NOT meet.** Zero
  `spawn_retry_cap_reached` / `slot_wedged_killed_for_resume` / `context_saturated_session_lost_task_requeued` events
  across the full 60-minute window (vs. 4 in 2026-08-08, all attributed there to inherited pre-clean-start
  saturation). 87 total context-lifecycle-family events observed in-window; none were wedge-terminal.

**Reading**: with a genuinely clean start (unlike 2026-08-08's first 30 minutes, which were still draining
pre-existing saturation), the fix now holds a fully healthy steady state for the whole hour — no wedges at all, not
just a reduced rate. This closes the 2026-08-08 follow-up's own stated gap ("does NOT by itself establish a clean
60-minute window on a fleet that was healthy at the start").

Raw event data + per-checkpoint fleet-max snapshots retained in this session's scratchpad
(`context_signal_validation_60min.sh` / `validation_report.json` / `validation_log.txt`) if a future audit wants the
full per-event detail beyond the summary above.

## Progress Log (cont.)

- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of all 6 open
  items. All touch core watchdog/context_lifecycle/worker_liveness machinery (compact-confirmation auto-submit,
  kill-before-cap ordering, context-plateau detection, queued-message force-latch detection, learned-window re-check,
  60-min validation re-run) — live-dispatch-critical-path code every AO worker (including this one) depends on. 5+ prior
  audits (07-30 through 08-08) consistently kept this NA on this exact reasoning; the doc's own most recent entries
  (2026-08-08) show it is still being actively characterized (a second, possibly-distinct wedge sub-mode found), not
  settled enough for a bounded worker fix. Not re-litigated.

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-17 (ao tranche, re-verified)** [body-hash:09af26bd4b7aa636]: KEEP-NA, valid — item 5
  (60-min context-signal re-validation, cited by the earlier same-day marker above) is now DONE (closed today, PASS
  on both criteria — see "2026-08-17 validation window" section above). The remaining 4 items (auto-submit /compact
  confirmation, force-kill-vs-retry-cap ordering, context-plateau detection, re-check learned windows once fleet
  fully on sonnet-5) stay KEEP-NA valid — live-dispatch-critical-path watchdog machinery still being actively
  characterized, consistent with 5+ prior audit passes' caution on this exact doc.

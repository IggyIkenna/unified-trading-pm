---
doc_type: issue
title:
  "Host ip-172-31-5-118 memory exhaustion -- 4th recurrence of the RULES.md heavy-compute-on-shared-host incident class"
summary:
  orchestrator.service peaked 49.3G RAM / 16.0G swap before restarting 2026-08-02T14:30:18Z, causing simultaneous
  tmux-session loss on slots 1/5/10 and a still-stuck slot 10. This is the 4th same-shape outage in ~1 week (07-27
  15.8G, 07-31 43.6G, 08-01 38.8G, now 49.3G) despite the existing HARD RULE -- honor-system enforcement is not holding
  at fleet scale, and unlike the 3 prior instances no single culprit script was confirmed this time (both live
  candidates were ruled out).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, fleet-health, memory-exhaustion, shared-host, recurring-incident]
related: []
created: 2026-08-02
parent_epic: orchestrator_master
priority: P1
source:
  "review(slot1, agt-7d13bd) mem-exhaustion recurrence investigation + main (agt-cb1851) verification, chat msgs
  3147/3148, 2026-08-02"
assigned_vm: NA
execution_scope: local-only
estimate_class: design
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# Host ip-172-31-5-118 memory exhaustion -- 4th recurrence

## What I found

`orchestrator.service` (the systemd unit encompassing the orchestrator server + every spawned slot tmux session on host
`ip-172-31-5-118`) peaked at **49.3G memory / 16.0G swap** over its prior run, before restarting at
**2026-08-02T14:30:18Z** (old master PID 2220368 -> new 2471282; confirmed via `journalctl`).

This coincided with fleet-wide tmux-session loss: slots 1, 5, and 10 all lost their tmux sessions simultaneously at
14:22:59Z, and again at 14:27:01Z. Slot 10 specifically: watchdog kick at 14:21:37Z (frozen), 2 failed resume attempts
(`spawn_retry_cap_reached` both times, `session_alive=False`), exhausted at 14:27:01Z; its task
(`mtds_backfill_sequential_true_dispatch_order_violated-002`) was correctly requeued and picked up by slot 5. Slot 10
itself did not get a fresh respawn attempt for 27+ minutes after exhausting its retry cap (tracked separately -- see the
operator escalation from main re: the stuck retry-cap gap; slot 10 subsequently recovered on its own at ~14:45:55Z).

This is the 4th instance of the exact incident class RULES.md Section 1 already names, each one WORSE than the last:

| Date                  | Script/trigger                                              | Peak memory        |
| --------------------- | ----------------------------------------------------------- | ------------------ |
| 2026-07-27            | `candle_coverage_gap.py`                                    | 15.8GB             |
| 2026-07-31            | `expand_defi_pool_catalogue_from_manifest.py`               | 43.6GB             |
| 2026-08-01            | `features_service.cross_instrument`                         | 38.8GB             |
| 2026-08-02 (this doc) | orchestrator.service aggregate, no single confirmed culprit | 49.3GB + 16GB swap |

Unlike the 3 prior instances, today's incident did not resolve to one named culprit. Two candidate heavy processes live
on the host at investigation time (~14:40Z, after the restart) were independently checked by main and ruled out: slot
8's `pipeline_e2e_check.py --legs benchmark --benchmark-days 30` (already exited, self-cleared) and slot 4's
`rebuild_prediction_manifest` (confirmed as the slot's own legitimately-dispatched, chunked/memory-bounded task, RSS
only 1.1G -- not a contributor). So the original peak's proximate cause on the PRIOR unit life (~13:40Z-14:30Z) was not
identified -- it may be aggregate oversubscription (many concurrent, individually-small, individually-legitimate slot
sessions and their subprocess trees, all sharing ONE un-partitioned ~54GiB cgroup ceiling with the orchestrator server
itself) rather than one runaway script -- a materially different failure mode than the 3 prior named-culprit incidents.

## Why it matters

- Each recurrence is a real fleet-wide outage: multiple slots lose live sessions simultaneously; a slot can get stuck
  dead for 25+ minutes past retry-cap exhaustion, silently losing dispatch capacity against a 600+-task backlog.
- The existing HARD RULE (`/codex/05-infrastructure/vm-launcher-runbook.md` Section "Heavy COMPUTE/MEMORY on the shared
  planning-vm", also RULES.md Section 1) is honor-system -- it depends on each agent recognizing a script could
  plausibly load a nontrivial dataset and remembering to wrap it BEFORE running it directly. Four recurrences in about a
  week, despite the rule existing since the first incident, is direct evidence honor-system enforcement is not holding
  at fleet scale.
- If today's incident really is aggregate oversubscription rather than one bad script, the existing fix pattern
  (spot-check + wrap individual heavy scripts) does not address the actual failure mode -- the fleet may need fewer
  concurrent heavy jobs per host, real per-job/per-slot cgroup memory reservations (not one whole-unit ceiling), or
  headroom-aware admission control.

## Recommended decision (operator-scope -- design/policy call, not a bounded fix)

1. **Bake the bound into the tooling** -- pipeline-check-style skills wrap their own heavy legs in
   `run-bounded-analysis.sh` (or equivalent) by default, instead of relying on the calling agent to remember.
2. **Per-slot cgroup memory reservations** -- give each slot's tmux session + subprocess tree its OWN memory limit
   carved from the host total, instead of every slot + the orchestrator server sharing one ~54GiB ceiling. Turns one
   slot's heavy job into a contained failure instead of a fleet-wide event.
3. **Headroom-aware admission control** -- check host memory headroom before dispatching a memory-heavy-classified task
   or spawning another concurrent slot; defer/queue if already under pressure.
4. **Status quo + periodic audit** -- keep the honor-system rule, rely on a periodic audit to catch violations after the
   fact. Included for completeness; 4 recurrences already argue against this alone.

Not mutually exclusive (e.g. 1+2 together is plausible). This doc does not pick one -- needs the operator.

## Codex SSOTs

- `/codex/05-infrastructure/vm-launcher-runbook.md` Section "Heavy COMPUTE/MEMORY on the shared planning-vm" -- the
  existing HARD RULE this pattern keeps violating.
- `unified-trading-pm/agents/RULES.md` Section 1 -- the worker-facing restatement + the 3-prior-incident log this doc
  extends to a 4th.

## Todos

- [ ] [OPERATOR] P1. Decide the mechanical-enforcement approach for the heavy-compute-on-shared-host HARD RULE (see 4
      options above) -- gates every fix below. (repo: unified-trading-pm, decision only)
- [ ] [INFRA] P2. Once decided, implement the chosen enforcement mechanism (repo: agent-orchestrator and/or
      unified-trading-pm scripts, exact target depends on the decision above).
- [ ] [DIAG] P2. Best-effort: root-cause today's specific 49.3G/16G-swap peak more precisely if feasible (aggregate
      oversubscription vs. a specific process that had already exited/rotated out by ~14:40Z) -- would sharpen whether
      option 1 or 2 above is the better fix. Not gating.

## Progress Log

- 2026-08-02: Drafted by review (slot1, agt-7d13bd) at main's request (chat msg 3148), after main (agt-cb1851)
  independently verified the finding, ruled out the 2 candidate live processes, confirmed slot 10's stuck-retry-cap
  state (slot 10 later recovered ~14:45:55Z), and escalated separately to the operator. NOT committed by review -- see
  review's role-boundary note in the accompanying chat message; handed as fully-drafted content to main/a worker to file
  verbatim.
- 2026-08-02 ~18:10Z: **Escalation continues — CONFIRMED ACTIVE, not resolved; current live instance is the FASTEST-yet
  cycle.** Review (slot1, agt-544983) picks up this thread after a lineage gap: agt-47b8e1 (the review agent main's
  18:00:15Z reply was addressed to) went stale/was killed ~18:00-18:02Z, apparently mid-conversation, without leaving a
  checkpoint — this entry reconstructs from main's message content plus fresh independent re-verification, not from
  agt-47b8e1's original alert (lost with its session; itself a live instance of the exact crash-loop this doc tracks).

  Main (agt-cb1851, chat msg 3323, 18:00:15Z) corrected an earlier "benign recycle churn" read: the ~45-min restarts +
  killed-slot spikes ARE the mem-4th incident, ACTIVE, not resolved by any restart (a restart resets the peak counter,
  not the underlying pressure — the ceiling gets re-hit every instance). Cited: MemoryHigh=49.39G / MemoryMax=57.98G /
  SwapMax=17.18G / MemoryCurrent=14.8G "at check"; systemd-oomd inactive so `ManagedOOMMemoryPressure=auto` is
  unenforced; `tmux_session_lost` counts "slot-1 30x, others 12-19x since 12:12Z, archived_lifecycle_complete:false =
  real lost work." Escalating as "esc18 URGENT" to the operator, asking they treat the P1 decision above as
  time-sensitive given the active data-loss rate, and to consider interim mitigation (raise SwapMax / split the cgroup)
  if option-2 (per-slot cgroup reservations) will take a while.

  **Independently re-verified (all confirmed), plus new evidence that sharpens the urgency:**
  - Live cgroup (`systemctl show orchestrator.service` + direct `/sys/fs/cgroup/system.slice/orchestrator.service/`
    read, ~18:08Z): `MemoryHigh=49392123904` (49.39 GB decimal / 46.0 GiB), `MemoryMax=57982058496` (57.98 GB decimal /
    54.0 GiB), `MemorySwapMax=17179869184` (17.18 GB decimal / 16.0 GiB) — matches main's cited figures to the byte.
    `systemd-oomd` confirmed `inactive`; `ManagedOOMMemoryPressure=auto` confirmed set-but-unenforced (the daemon that
    would act on it isn't running) — main's mechanism claim holds. Note: I only checked this unit's own journal for OOM
    markers, not system-wide/kernel dmesg — every stop/start pair reads as a clean "Deactivated successfully" →
    "Started" (not a raw kill), so whatever triggers the restart is worth a separate look, not asserted here.
  - **NEW: a 4th restart today not yet in this doc's table**
    (`journalctl -u orchestrator.service --since "2026-08-02 00:00:00"`), and the CURRENT (5th) live instance is on pace
    to be the fastest cycle yet:

    | Restart (`Started` ts)          | Wall-clock since prior restart      | Peak logged at stop                                                                                                                                                                    |
    | ------------------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | 14:30:18Z (already in this doc) | —                                   | 49.3G mem / 16.0G swap                                                                                                                                                                 |
    | 15:30:16Z                       | ~59m58s                             | 49.3G mem / 16.0G swap                                                                                                                                                                 |
    | 17:00:14Z                       | 1h29m58s                            | 49.3G mem / 16.0G swap                                                                                                                                                                 |
    | 17:45:14Z                       | 45m00s                              | 49.3G mem / 16.0G swap                                                                                                                                                                 |
    | _(current life, still running)_ | ~23-25min so far, not yet restarted | live read ~18:08Z: `MemoryPeak=52936736768`B = 49.30 GiB / 52.94 GB decimal — already at the SAME displayed peak (49.3G) every one of the 4 prior lives hit only right before stopping |

    All 4 completed lives today hit an essentially identical ~49.3GiB peak right before stopping (reads as a hard
    practical ceiling close to `MemoryHigh`, not noise). The current, still-running 5th life reached that same figure in
    under 25 minutes — faster than any of the 4 completed lives (shortest was 45min) — and is still climbing toward
    `MemoryMax` (already ~91% of the 57.98G hard cap as of this read). Flagging as a fresh, concerning data point, not a
    claimed clean monotonic trend across all 4 historical gaps (60min→90min→45min is not monotonic) — the honest claim
    is: whatever is happening right now is reaching the characteristic danger-peak faster than every completed cycle
    today.

  - `tmux_session_lost` (deduped to the `scope:"slot"` half of each dual-logged kill event;
    `?type=tmux_session_lost&limit=1000`, filtered `ts >= 2026-08-02T12:12:00Z`): **slot 1 = 31** (closely matches
    main's cited "30x"), then slot 5=20, slots 8/10/4/11=17 each, slot 9=15, slot 12=12, slot 13=8, remaining slots 3-6
    each — 185 total fleet-wide in ~6h (roughly one session loss every 2 minutes across the fleet). 56 of those 185
    carried a non-null `released_task` (mid-task kill); of the paired agent-scope halves in the same window, 25 show
    `archived_lifecycle_complete:false` vs 54 `:true` — corroborates main's "real lost work" framing (a genuine,
    non-negligible fraction of kills are unclean).

  **Not committed by review** — role-boundary (zero commits, ever, not even a sanctioned direct-push carve-out). Handed
  as fully-drafted, ready-to-paste content to main via chat to route to a live non-reviewer worker for the
  `docs(plans):` quickmerge, same pattern as the entry above.

- 2026-08-02 ~18:40Z: **6th recurrence confirmed — NEW partial-casualty signature (not a full service restart), plus a
  stuck-slot follow-up.** Review (slot1, agt-a3ed9a) picks up after agt-544983 (the 2nd reviewer on this thread) was
  itself killed by this exact incident mid-investigation, at the same 18:29:26Z event this entry documents.

  Independently confirmed the 18:29:26Z mass `tmux_session_lost` (slots 1/5/9/10/11/12 simultaneously, including this
  review session's own slot) is this incident continuing, with two refinements to the prior entry:
  1. **Partial-casualty signature, not a full service bounce**: `orchestrator.service`'s
     `ActiveEnterTimestamp`/`MainPID` (2971809) were unchanged across the kill (alive continuously since 18:15:26Z,
     ~14min into that life when 6 slot sessions died simultaneously) — a DIFFERENT failure mode than the 4 full-restart
     cycles already tabulated above. Post-event cgroup read (~18:37Z): `MemoryCurrent=22.9G` (well under the 46G
     `MemoryHigh`), `MemorySwapCurrent=1.5G` — consistent with the slot deaths themselves being the pressure-relief
     valve (memcg-level kills), not a unit-wide restart.
  2. **MemoryPeak methodological correction**: the prior entry's "49.3G every life" pattern is likely a measurement
     artifact — `MemoryPeak` read byte-identical (`52936736768` = 49.30GiB) at ~18:37Z (this life) and ~18:08Z (the
     PRIOR life, pre-restart). cgroup v2 `memory.peak` is a sticky high-water-mark that does not auto-reset across a
     service restart unless explicitly zeroed, so this metric doesn't independently prove each life re-climbs to the
     same ceiling — though the functional symptom (recurring mass slot-session kills) remains real, confirmed via
     `tmux_session_lost` counts directly. dmesg showed no kernel OOM-killer lines, but ring-buffer read permission on
     this host is unconfirmed — inconclusive, not ruled out (same open gap as the ~18:08Z entry).

  **New finding — slot 12 is a repeat stuck-respawn offender**: killed by this same 18:29:26Z event; unlike slots
  1/5/9/10/11 (recovered in 1-8 min), slot 12 stayed fully dead (`worker_alive=false`/`tmux_alive=false`, no respawn
  attempt visible in the orchestrator journal) for 10+ minutes. It already hit `spawn_retry_cap_reached` once earlier
  the SAME hour (18:17:55Z) before self-recovering — its 2nd stuck episode in <90min, suggesting a slot-12-specific
  respawn weakness worth investigating separately from the aggregate memory question. Git tree confirmed clean (no WIP
  at risk). Main (agt-cb1851) independently corroborated and is escalating this as an `esc17`-class respawn-gap to the
  operator (spawn/kill is backend-AutoSpawn-owned, outside main's own charter to act on directly).

  **Not committed by review** (zero commits, role boundary) — handed to main to route to a worker for the `docs(plans):`
  quickmerge.

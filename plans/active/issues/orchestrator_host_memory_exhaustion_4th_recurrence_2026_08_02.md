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

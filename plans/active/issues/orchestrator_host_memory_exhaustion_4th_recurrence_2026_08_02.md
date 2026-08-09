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
related:
  [
    /plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-02
author: unknown
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
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    agents/RULES.md,
    /plans/archive/issues/heavy_resource_vm_spin_up_rule_gap_2026_07_27.md,
    scripts/dev/run-bounded-analysis.sh,
    features-service/features_service/cross_instrument,
    /plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md,
  ]
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

- [x] ✅ [OPERATOR] P1. Decide the mechanical-enforcement approach for the heavy-compute-on-shared-host HARD RULE (see 4
      options above) -- gates every fix below. (repo: unified-trading-pm, decision only) — **RULED 2026-08-06 (operator,
      interactive)** (recorded in `/plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md`): none of the 4
      options as written. The approach taken is a **host-level per-process reaper** — `resource-watchdog` — which
      achieves option 1's intent (the bound no longer depends on the calling agent remembering to wrap a heavy leg)
      without requiring every skill to be rewritten, and is root-cause-agnostic the way option 2 is: it kills the
      offending process regardless of whether the cause is one bad script or aggregate oversubscription. Shipped by
      `/plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md` (archived). (Reconciled 2026-08-06: an
      independently-reached "combine 1+2+3" ruling from a concurrent session is superseded by this one — the shipped
      reaper is already live evidence of what was actually chosen and built, not a still-open combination of the
      original 3 options.)
- [x] ✅ [INFRA] P2. Once decided, implement the chosen enforcement mechanism — **DONE 2026-08-05**,
      `unified-trading-pm/scripts/infra/resource-watchdog/` (`resource-watchdog.sh` + systemd unit + `config.yaml` +
      logrotate/tmpfiles retention), first shipped `unified-trading-pm@d1ffdf6b3`. **Verified LIVE on the planning VM
      2026-08-06** via read-only SSM (`i-0c9b283b31d6b5ca7`, ap-northeast-1): `systemctl is-active`/`is-enabled` =
      `active`/`enabled`, `ActiveEnterTimestamp=Wed 2026-08-05 14:38:40 UTC` (no restarts since), and the live unit's
      thresholds match this repo's SSOT `config.yaml` exactly — `RW_RSS_LIMIT_NORMAL_GB=10`, `RW_RSS_LIMIT_HIGH_GB=4`
      (at ≥80% cgroup MemoryMax), `RW_CPU_MAX_PCT=95` sustained `RW_CPU_WINDOW_MIN=10`, `RW_SWAP_LIMIT_GB=4`,
      `RW_MAX_KILLS_PER_MIN=1`, `RW_MIN_PROCESS_AGE_SEC=30`, and critically **`RW_DRY_RUN=false`** (enforcing, not
      merely observing). Log tail confirms a live poll loop (`tick=8215 pressure=normal cgroup_mem=17GB`). Documented in
      codex at `/codex/05-infrastructure/agent-orchestrator-api-host.md` (full threshold table + allowlist + BQ
      `watchdog_kill_events` schema) and `/codex/05-infrastructure/deployment-observability.md` — so the "if it isn't
      documented, write it into codex" half of the 2026-08-06 ruling needed no action.
- [x] [OPERATOR] P2. ✅ **STALE-CHECKBOX FIX (round5 ao investigation) — the linked doc's identical action is now done,
      catching this citing checkbox up to reality, not a new decision.** The action this todo pointed at —
      `/plans/archive/2026_08/watchdog_kill_events_deployment_gaps_2026_08_05.md`'s `[INFRA] P2` item (systemd
      `Environment=RW_DEPLOYMENT_API_URL=.../RW_VM_NAME=...` +
      `systemctl daemon-reload && systemctl restart resource-watchdog`) — is confirmed `[x]` done there: "RULED
      2026-08-06 (operator): approved, AO-dispatchable to a session/worker with root on the planning VM... applied via
      SSM (slot-5, 2026-08-07): env vars added to live unit, live script updated from repo (08f6a9571),
      daemon-reload+restart applied. E2E verified: kill row `{"vm_name":"ip-172-31-5-118","killed":true}` confirmed in
      deployment-api." That source doc is now `status: archived`
      (`plans/archive/2026_08/watchdog_kill_events_deployment_gaps_2026_08_05.md`). This doc's own todo explicitly said
      "do the work THERE, not twice" — the work landed there; nothing left to do here.
- [ ] [DIAG] P2. Best-effort: root-cause today's specific 49.3G/16G-swap peak more precisely if feasible (aggregate
      oversubscription vs. a specific process that had already exited/rotated out by ~14:40Z) -- would sharpen whether
      option 1 or 2 above is the better fix. Not gating.
- [ ] [OPERATOR] P2. **Confirm or rule out kernel-level OOM-killer activity via `dmesg`/`journalctl -k` with root access
      on the host.** Every read attempt so far has hit ring-buffer permission denial ("dmesg still permission-denied on
      this host (inconclusive, not ruled out)" -- recurring across the ~18:08Z, ~18:40Z, and 2026-08-06 Progress Log
      entries below); agent slots have no root on this box. Needs the operator to either (a) run
      `sudo dmesg -T | grep -i "killed process\|oom"` + `sudo journalctl -k --since "2026-08-02" | grep -i oom` directly
      on ip-172-31-5-118 (or via SSM) and report back what it shows, or (b) grant the orchestrator service account read
      access to the kernel ring buffer (`sysctl kernel.dmesg_restrict=0`, or an ACL on `/dev/kmsg`) so future
      recurrences self-diagnose without a human in the loop. This is the one open question that would distinguish
      genuine kernel-level OOM kills from the resource-watchdog's own soft RSS-threshold kills -- still unresolved as of
      2026-08-07.

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

- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`, dispatch agt-da0e58, slot 10): KEEP-NA, valid — active
  P1 incident, still escalating (6 recurrences logged as of this entry, operator escalations esc17/esc18 pending). Of
  the 3 open todos: `[OPERATOR] P1` is a direct operator-scope policy decision (correctly tagged); `[INFRA] P2` is
  explicitly gated on that decision, not yet actionable; `[DIAG] P2` ("best-effort... if feasible", no bounded
  done-when) is a live diagnostic already being substantially advanced in real time by the review-agent chain in this
  same Progress Log (cgroup reads, `tmux_session_lost` census, candidate-process ruling-out) — dispatching a separate AO
  worker to redundantly re-investigate the SAME live incident right now would duplicate in-flight human/review work, not
  add bounded value. Doc correctly stays `assigned_vm: NA` in full; no reclassification.
- 2026-08-02 ~23:52Z: **7th+ recurrence window — still active, not resolved.** Review (slot1, agt-39a53d) picks up after
  a gap (agt-e99c33's Tick 4 ended ~22:26Z+; an intermediate registration agt-9a06d4 registered 23:41:52Z but was killed
  by the 23:45:13Z restart before its first real tick). 3 more full restarts confirmed via journalctl since Tick 4's
  read: 22:30:16Z, 23:00:18Z (+30m gap), 23:45:13Z (+45m gap) — same recurring shape, cadence neither accelerating nor
  resolving.

  **Methodological finding, now CONFIRMED across 3+ additional restarts (extends agt-a3ed9a's ~18:40Z hypothesis to
  certainty):** `memory.peak` / journalctl's logged "memory peak" is a STUCK cgroup accounting value, not fresh per-life
  evidence. Direct read at 23:50:59Z — only ~5.7min into the life started 23:45:13Z — shows `MemoryPeak=52936736768`
  (49.30GiB), byte-identical to every check since 18:08Z, while `MemoryCurrent=18.4GB` (well under the 46GB
  `MemoryHigh`) and `MemorySwapCurrent=6.5GB`. A life 5.7 minutes old cannot have organically climbed to and receded
  from 49.3GB already at this low a current-usage level — the figure is carried over across restarts on this host
  (systemd apparently does not always recreate a fresh cgroup instance / reset `memory.peak` on this unit's restart
  cycle). Going forward, cite restart cadence (systemd `Started`/`Stopped` timestamps) and `tmux_session_lost` counts as
  the reliable signals; do not re-cite "49.3G peak" as fresh per-restart proof.

  `systemd-oomd` still `inactive` (confirmed again). No new candidate culprit process investigated this tick
  (deprioritized behind the pending [OPERATOR] P1).

  **Not committed by review** (zero commits, role boundary) — routed by main (agt-1756f6) via the delivery-guaranteed
  slot outbox to a live worker for the `docs(plans):` commit (NOT a verbal/tmux handoff — the prior addendum-3 handoff,
  ~22:26Z, was lost when its target slot respawned before acting; this closes that process gap).

- 2026-08-03 ~02:48Z: **8th+ recurrence window -- service stability genuinely IMPROVING, per-slot kill rate also
  improving but still active.** Review (slot1, agt-fe873f) picks up after a lineage gap (agt-e60e67's Tick 6 checkpoint
  ended ~02:3xZ; this session registered 02:44:12Z following another slot-1 tmux_session_lost at 02:39:59Z -- the SAME
  ongoing incident continuing to claim review's own slot).

  **Process-gap note**: agt-e60e67's Tick 6 addendum (chat msgs 3403/3406 to main) never landed in this doc's Progress
  Log -- the doc's last entry remains the "7th+ recurrence" one from agt-39a53d (~23:52Z). This is the SECOND occurrence
  of this exact handoff-loss shape (the first was Tick 4's "addendum-3," lost when its target slot respawned before
  acting). Flagging the pattern, not re-litigating the content -- Tick 6's substance (104min+ stable life, slot 13's
  orphaned-duplicate-commit finding) is superseded by fresher data below and by slot 13's now-confirmed-clean state, so
  nothing of lasting value was actually lost this time, but the delivery mechanism itself deserves a look if it recurs a
  3rd time.

  **Fresh data (directly re-verified, ~02:47Z)**:
  - `orchestrator.service` ran **23:45:13Z -> 02:45:13Z with ZERO restarts -- exactly 3h00m00s, the longest life on
    record** (prior best: Tick 6's 104min+). Then restarted again at 02:45:13Z (old PID gone, new MainPID=3677556).
  - Per-slot kill rate in that 3h window: **61 `tmux_session_lost` (scope=slot) events = ~20.3/hr**, down from Tick
    5/6's cited ~34-42/hr -- a genuine improvement, not just noise (12 of the 61 carried a non-null `released_task`,
    i.e. real mid-task kills, correctly requeued per design). Slot 1 (review, this session's own lineage) was hit 9x in
    the window.
  - `MemoryPeak` cgroup figure remains the same stuck `52936736768`B (49.30GiB) sticky high-water-mark documented by
    agt-a3ed9a/agt-39a53d as NOT resetting across restarts -- not re-citing as fresh evidence, per the established
    methodological correction.
  - dmesg still permission-denied on this host (inconclusive, not ruled out -- same open gap as every prior check).
  - **Minor new observation, likely benign**: all 17 slots on this host show `ff_pull_last_result: "conflict"` from a
    single FF-pull sweep at 02:45:56Z (43s after the restart) -- host-wide + identical timestamp strongly suggests a
    restart-transient artifact (e.g. a race right as the service came back up), not 17 independent real git conflicts.
    Spot-checked slot 10's flagged `agent-orchestrator diverged ahead1/behind1` directly -- already clean/in-sync by the
    time I checked seconds later. Not escalating; worth a passing note in case it recurs standalone (without a
    coincident restart) in a future tick.
  - **Slot 13's orphaned-duplicate-commit finding (Tick 6) -- CONFIRMED RESOLVED**: git-health shows slot 13's worktree
    fully clean, no dirty files, matching main's Tick 6 salvage-check-then-reset-hard dispatch having landed
    successfully.

  **Net read**: this incident is trending toward resolution on BOTH axes (service-restart cadence AND per-slot kill
  rate), but is still actively costing real mid-task work (12 kills/3h with a released task) and the `[OPERATOR] P1`
  decision in this doc is still unchecked/unruled as of this read -- asking main directly whether the operator has ruled
  since the ~01:32Z online-window Tick 6 flagged.

  **Not committed by review** (zero commits, role boundary) -- handed to main to route to a live worker for the
  `docs(plans):` commit.

- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. All 3 open items remain genuine
  judgment/operator-gated work: an explicit P1 operator policy decision the doc itself refuses to pre-select (still
  unruled as of the latest ~02:48Z Progress Log entry), an implementation item textually sequenced behind it, and a
  best-effort non-gating diagnostic already being actively advanced live by the review-agent chain documented in the
  Progress Log (7+ recurrence entries). Incident remains ACTIVE — still-unruled OPERATOR decision, ongoing recurrences.

- **2026-08-03 ~22:48Z: 9th+ recurrence window — still ACTIVE, plateaued not resolved; slot 1 (review) remains the
  single hardest-hit slot.** Surfaced by review (slot1, agt-56e42e) via chat, committed by main agt-1756f6 (docs
  carve-out; review never commits). Picks up after a ~20h Progress Log gap (last entry agt-fe873f ~02:48Z) — this
  session's own boot is the latest in an unbroken chain of slot-1 `tmux_session_lost` kills continuing through the gap.
  - `orchestrator.service` restarts since 2026-08-02 22:00Z (`journalctl`): 10, cadence still irregular — two
    sub-20-minute lives (15:00→15:15Z, 18:30→18:45Z) alongside 60-90min ones; life started 22:15:21Z. NOT the "trending
    toward resolution" the ~02:48Z entry cautiously reported — bounces short/medium with no clear trend.
  - `tmux_session_lost` (scope=slot, deduped) fresh 1000-row fetch (back to 2026-08-02T16:29Z): **3h = 70 (23.3/hr, 8
    mid-task)**, **8h = 164 (20.5/hr, 22 mid-task)**, **24h = 477 (19.9/hr, 68 mid-task)** — essentially the SAME rate
    the ~02:48Z entry called "improving" (~20.3/hr then); plateaued at that improved-but-still-active rate ~20h.
  - **Slot 1 (review's own slot) hardest-hit every window**: 11/3h, 22/8h, 56/24h — ~2x the next-worst (slot 4/5/8/10
    cluster near half). Long-lived sessions (review, main) absorb a disproportionate share vs task-churning workers;
    real cost to QA continuity — this doc's own 9+ handoffs across agt- ids in ~30h are the evidence.
  - cgroup ~22:46Z: MemoryCurrent=10.65GB, Swap=8.07GB, High=49.39GB, Max=57.98GB — well under both ceilings ~30min into
    this life. MemoryPeak still the stuck 52936736768B sticky HWM (non-resetting, per established correction — not
    re-cited as fresh evidence).
  - **`[OPERATOR] P1` (mechanical-enforcement) still unruled** — ~24-30h+ since first flagged (2026-08-02), past
    esc17/esc18 with no operator answer in `blocked_queue` or this Progress Log. Fresh grep of
    `plans/active/issues/*.md`: no duplicate/superseding doc (only pre-existing related-but-distinct ones).
  - **Net**: active P1, 3rd calendar day, plateaued not trending toward resolution. Main is surfacing the
    elapsed-time-since-escalation gap to the operator for a ruling on the mechanical-enforcement approach.

- **2026-08-05 (interactive session, cross-doc link fix)**: `resource_watchdog_host_guardian_2026_08_05.md` (a same-day,
  `assigned_vm: NA` plan built "in-session, operator present," never previously cross-linked to this doc) shipped a
  systemd-based per-process RSS/CPU/swap killer on this exact host — a live instance of this doc's recommended-decision
  option 1, "bake the bound into the tooling." Concrete evidence it's working: an interactive RAM-spike investigation
  the same day watched it catch and SIGTERM two ~40GB bare-`read_availability_index()` blowups from slot 15 within one
  minute, no fleet-wide crash-loop. **Not asserting this formally resolves the `[OPERATOR] P1` todo below** — a systemd
  RSS-killer is closer to option 1 than option 2/3 (still one shared ~54GiB ceiling, not per-slot reservations or
  admission control), so it may reduce recurrence frequency without fully closing the question; that's still the
  operator's call. Cross-linked both docs' `related:` so they're no longer siloed.
- **context-scout 2026-08-06**: re-scouted; added `/plans/archive/2026_08/resource_watchdog_host_guardian_2026_08_05.md`
  (the 2026-08-05 systemd RSS-killer, a live instance of this doc's recommended option 1, cross-linked but not yet in
  context_scope), now 6 entries.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-07 (interactive session)**: the recurring "dmesg permission-denied, inconclusive" aside (logged as a
  diagnostic footnote in multiple prior entries above, never tracked as actionable) was formalized into the
  `[OPERATOR] P2` todo above. The exact commands were handed to the operator directly in-session; not yet run as of this
  entry -- still open.
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — re-verified all 3 open items: the
  `[OPERATOR] P2` kill-event dual-write gap is genuinely duplicate-tracked in
  `/plans/archive/2026_08/watchdog_kill_events_deployment_gaps_2026_08_05.md` (confirmed still `status: open`,
  `assigned_vm: planning` — do the work there, not here); `[DIAG] P2` is explicitly non-gating best-effort; the fresh
  `[OPERATOR] P2` dmesg/root-access todo (added earlier this session) is still unresolved as its own text states. No
  reclassification.

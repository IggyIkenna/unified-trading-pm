---
doc_type: issue
title:
  Registering 23 self-hosted runner pools (46 processes) at once, concurrent with 22 repos' real quickmerge/QG runs,
  drove the shared orchestrator VM into sustained 66-93% iowait — the operator's own interactive/autonomous AO
  slot-workers were observed blocked in D-state alongside the new runner processes
summary: >-
  During github_actions_operator_gated_followups_2026_07_17.md's Phase-7 fan-out (2026-07-27/28), 9 of 23 newly-
  registered self-hosted runner pools showed a runner process logging "Connected to GitHub"/"Listening for Jobs" while
  GitHub's own `/actions/runners` API showed `total_count: 0` for that repo — a real, VM-side registration failure, not
  a client-side query artifact (confirmed identically via the VM's own admin-PAT-backed `setup-glue-runners.sh status`).
  Live diagnosis (`top`, `uptime`, `ps -eo stat`) found the root cause: registering 23 pools (46 new Runner.Listener
  processes) essentially simultaneously, landing at the same time as 22 repos' own concurrent
  quickmerge/quality-gates.sh runs (real pytest/lint/typecheck suites) PLUS live CI jobs already starting to execute on
  the newly-self-hosted pools, drove the shared VM into genuine, sustained disk I/O contention: `top`'s `%Cpu(s)`
  breakdown showed 66.2%→93.1% iowait (NOT CPU-bound — `us+sy+ni` stayed ~20-30% throughout), `uptime` load average
  climbed 74→119 on a 16-vCPU box, swap usage grew from 8GB to 10.5GB, and disk sat at 90% full (433GB/483GB). The
  clinching evidence this is a real, shared-impact problem and not scoped to the 9 affected repos: the operator's OWN
  interactive/autonomous AO slot-worker `claude` processes (orch-slot-1 and several others) were observed in `D`
  (uninterruptible disk-wait) state in the same `ps` snapshot as the runner/pytest processes.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, capacity-planning, io-contention, vm-infra, phase-7]
related:
  [/codex/05-infrastructure/vm-launcher-runbook.md, /plans/active/github_actions_operator_gated_followups_2026_07_17.md]
created: 2026-07-28
priority: P1
parent_epic: infrastructure_master
source:
  "slot-1 (tabs/1), /autonomous, discovered live-diagnosing 9 unregistered runner pools during Phase-7 fan-out,
  2026-07-28"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# Runner-registration burst drove the shared VM into real I/O contention

## What I found

Registering all 23 remaining repos' self-hosted glue-runner pools in one batched pass
(`setup-glue-runners.sh POOL_TAG=<repo> ... install`, 2 glue runners each, sequential within the batch script but
landing within minutes of each other) coincided with the SAME fan-out's own git-side work — a background Workflow
shipping all 23 repos' workflow-YAML changes via `quickmerge.sh`, which runs each repo's REAL `quality-gates.sh` (full
pytest/lint/typecheck, batched 2-concurrent per the workspace's own shared-host rule) — plus, as those repos'
`quality-gates-v2` began running on the newly-registered self-hosted pools, real CI job checkouts/test executions on TOP
of that.

**Initial hypothesis was wrong and corrected in-session**: first read as "VM overloaded on CPU," which the operator
correctly challenged by pointing at the AO dashboard's Host Resources panel (CPU 41%, RAM 24%, matching a live `free -h`
pull almost exactly). Both readings are accurate for what they measure — the dashboard's CPU% is `us+sy+ni` (true
compute busy-ness), which was genuinely moderate. The real, separate signal was **iowait**, which a simple CPU% panel
does not surface: `top -bn1`'s `%Cpu(s)` line showed `66.2 wa` then `93.1 wa` across two checks a few minutes apart —
the box was spending the large majority of CPU-accounting time waiting on disk, not computing.

**Confirmed real (not a diagnostic artifact) via a live process snapshot**: `ps -eo pid,stat,...` showed dozens of
processes in `D`/`Ds`/`Dl` state (uninterruptible sleep, i.e. genuinely blocked on I/O) — `kswapd0` (kernel swap daemon,
confirming active swap pressure), multiple `Runner.Listener`/`Runner.Worker`/`actions/checkout` processes for the
newly-registered pools actually executing real jobs, long-running pytest processes for `alerting-service` and
`fund-administration-service` (~2h wall-clock — abnormally long, consistent with I/O starvation slowing them down rather
than a 2h test suite being normal), a `.tabs/2` (a DIFFERENT slot entirely) pytest run, and — the finding that made this
undeniably a shared-impact problem rather than a scoped one — **several `claude --dangerously-skip- permissions ...`
processes (the operator's own interactive/autonomous AO slot-worker sessions, e.g. `orch-slot-1`) were ALSO in `D`
state** in the exact same snapshot.

## Corrective action taken (autonomous rule 3/10 — own the infra op)

Disabled the second glue runner (`glue-2`) across all 23 newly-registered pools via `systemctl disable --now` (cheap —
no disk I/O beyond a few syscalls, unlike any `install`/rebuild path), halving active new-pool runner processes 46→23.
This was chosen over re-running `install` with a lower `GLUE_COUNT` specifically because ANY install-path operation
(tarball extraction, venv rebuild) would itself have added to the exact I/O pressure being relieved.

## Open questions / follow-up

- [ ] [VERIFY] P1. Confirm load/iowait actually eased after the glue-2 scale-down (re-check `uptime`/`top` a few minutes
      later) before concluding this alone resolved it — the fan-out's own quickmerge/QG batch may still be contributing
      independently of runner count, and should naturally taper as those 22 repos finish shipping.
- [ ] [VERIFY] P1. Once load is confirmed down, re-attempt registration for whichever repos still show
      `total_count:     0` on `/actions/runners` — the working theory is these will succeed once I/O pressure that was
      interfering with the registration handshake itself clears, but this has not yet been proven post-mitigation.
- [ ] [REVIEW] P2. **Capacity-plan this VM for concurrent self-hosted-runner registration going forward** — this
      session's burst (23 pools at once) was a one-time fan-out, but the same box now permanently hosts PM's original
      8 + agent-orchestrator's 3 + 23×N new runner processes ALONGSIDE the interactive/autonomous AO slot workers that
      are its primary tenant. Consider: (a) whether `glue-2` should stay disabled long-term per new pool (permanent
      capacity decision, not just a burst mitigation) vs. re-enabled once steady-state load is confirmed low, (b)
      whether a FUTURE bulk runner-pool registration (e.g. onboarding more repos later) should be explicitly staggered
      /rate-limited rather than batched, given this measured impact on interactive sessions.
- [ ] [REVIEW] P3. The AO dashboard's Host Resources panel reporting only `us+sy+ni` (no iowait) means an operator
      glancing at "CPU 41%" during an episode like this would not see the real problem. Consider whether the panel
      should surface iowait or load-average alongside CPU% specifically because self-hosted CI runners on this box make
      disk contention a live, recurring risk category the panel currently cannot show.

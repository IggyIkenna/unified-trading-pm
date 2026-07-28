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

- [x] ✅ [VERIFY] P1. Confirm load/iowait actually eased after the glue-2 scale-down (re-check `uptime`/`top` a few
      minutes later) before concluding this alone resolved it — unified-trading-pm@c2308363d. Three `top -bn1` samples
      taken minutes apart: iowait `52.0 wa` → `18.5 wa` → `6.5 wa` (down from the original 66.2→93.1 wa episode); load
      average 1-min `32.92` → `31.90` → `42.05` (5-min/15-min trending down: `39.77`→`39.04`→`39.48`, off the prior
      74→119 peak) with the remaining CPU-accounting time now `us`/`sy`/`ni` (real compute, e.g. concurrent QG runs),
      not `D`-state disk-wait. iowait is conclusively down; the tapering fan-out QG batch is the residual load driver,
      consistent with the doc's own prediction.
- [x] ✅ [VERIFY] P1. Once load is confirmed down, re-attempt registration for whichever repos still show
      `total_count:     0` on `/actions/runners` — unified-trading-pm@c2308363d. Queried `GET /actions/runners` (via
      `gh api`, `scripts/workspace/load-gh-token.sh`) for all 23 newly-registered pools by name (`ao` →
      `agent-orchestrator`): **every one now shows `total_count >= 1`, none show 0** — alerting-service,
      batch-live-reconciliation-service, client-reporting-api, deployment-api, deployment-service, e2e-testing,
      execution-service, features-service, fund-administration-service, greeks-service, ibkr-gateway-infra,
      instruments-service, market-data-processing-service, market-tick-data-service, ml-service, strategy-service,
      system-integration-tests, trading-agent-service, unified-api-contracts, unified-trading-api,
      unified-trading-library (all =1), deployment-ui, unified-trading-system-ui (=2, glue-2 offline-but-registered),
      agent-orchestrator (=3). Per-runner detail confirms `glue-1` is `status=online` (mostly `busy=true`, i.e. actively
      running real CI jobs) on every pool; `glue-2` shows `status=offline` where it exists (correctly reflecting the
      `systemctl disable --now` corrective action, not a registration failure). **No re-registration action was needed**
      — the working theory is confirmed: the earlier `total_count: 0` reads were the registration handshake itself
      getting starved by I/O contention, and all 9 previously-phantom repos self-resolved to online registered runners
      once the pressure eased (no manual re-`install` required).
- [ ] [REVIEW] P2. **Capacity-plan this VM for concurrent self-hosted-runner registration going forward** — this
      session's burst (23 pools at once) was a one-time fan-out, but the same box now permanently hosts PM's original
      8 + agent-orchestrator's 3 + 23×N new runner processes ALONGSIDE the interactive/autonomous AO slot workers that
      are its primary tenant. Consider: (a) whether `glue-2` should stay disabled long-term per new pool (permanent
      capacity decision, not just a burst mitigation) vs. re-enabled once steady-state load is confirmed low, (b)
      whether a FUTURE bulk runner-pool registration (e.g. onboarding more repos later) should be explicitly staggered
      /rate-limited rather than batched, given this measured impact on interactive sessions. **Update 2026-07-28 ~00:20
      UTC — steady-state load is NOT low, arguing against re-enabling `glue-2` and FOR treating this as a real capacity
      gap, not a one-time burst.** Re-checked `vol-0b4f0237fa0f5cd0f`'s `VolumeQueueLength` via CloudWatch ~2h after the
      `52→18.5→6.5 wa` post-mitigation reading above (which was real and correct at the time): the LATEST 6 datapoints
      (30-min window, 5-min granularity) show a SUSTAINED `5.7-6.5` average — roughly DOUBLE the `~2.5-2.9` level
      measured earlier this same evening (itself already called out in
      `github_actions_operator_gated_followups_2026_07_17.md`'s Phase-7 P2 todo as "the residual level after glue-2 was
      halved, not healthy-baseline"). CPU stayed moderate throughout (29-51% avg, matching the 50-70%-target framing,
      not the bottleneck). Corroborating symptom same window: `system-integration-tests`' `cross-repo-invariants` job (2
      consecutive real failures, `full-workspace-sit` runs `30312490597`/`30314690222`) polls a `ci-status-update`
      dispatch per SIT-covered repo with an 18×5s=90s budget — 4/21 repos (agent-orchestrator, alerting-service,
      batch-live-reconciliation-service, client-reporting-api) blew that budget and got reported as
      `conclusion=unknown/timeout`, but spot-checking one (agent-orchestrator's dispatch, run `30314879898`) shows it
      actually completed `success` ~6 minutes later — a real false-negative from a polling window that's too tight for
      CURRENT (degraded) conditions, not a code bug in that job. **Net read: the glue-2 disable was a correct, working
      burst mitigation, but load has climbed back since, so it has NOT solved the underlying capacity question this todo
      already named** — the EBS iops/throughput bump suggested in the Phase-7 doc (a live, non-disruptive `gp3`
      modify-volume op) is worth trying before further headcount reductions on the runner side, since CPU/RAM are not
      what's constrained here.

      **Update 2026-07-28 ~06:25 UTC — contention has substantially EASED, likely on its own as the fan-out's own
              CI/QG batch finished draining, not from any further intervention.** Re-checked `VolumeQueueLength` across a
              1h window (6 datapoints, 10-min granularity) after ~5h holding flat at the elevated `5.6-6.5` level (3
              consecutive prior checks, ~00:20-01:35 UTC): the LATEST readings are `0.84 → 0.81 → 1.88 → 5.53 → 1.93 → 0.50`
              — mostly back down near the pre-burst `0.5-2` baseline range, with one brief `5.53` spike (a single 10-min
              bucket, not sustained). Fleet-wide sweep the same check found only 3 failures, ALL already resolved by a
              newer green run on retry (instruments-service, system-integration-tests, trading-agent-service) — no
              lingering `[qg-governor] all 4 tokens busy` or SIT `ci-status-update` timeout signatures observed this pass,
              consistent with the queue backlog having actually cleared rather than just gone quiet. **Net read: this
              looks like the burst genuinely working itself out over ~5-6h as PM's own fan-out's git/QG activity tapered
              (the doc's own original prediction), not evidence the underlying capacity gap was fixed** — the EBS
              iops/throughput headroom question above remains open and worth doing before the NEXT bulk registration or
              fan-out event reproduces this, but it is no longer an active, ongoing symptom as of this check. Downgrading
              urgency accordingly; re-verify if/when the next bulk self-hosted-runner change happens rather than continuing
              to poll an already-recovered metric.

- [ ] [REVIEW] P3. The AO dashboard's Host Resources panel reporting only `us+sy+ni` (no iowait) means an operator
      glancing at "CPU 41%" during an episode like this would not see the real problem. Consider whether the panel
      should surface iowait or load-average alongside CPU% specifically because self-hosted CI runners on this box make
      disk contention a live, recurring risk category the panel currently cannot show.

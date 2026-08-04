---
doc_type: issue
title: >-
  `exit_code_fleet_monitor` pages/escalates DP-VM-001 for EVERY individual `max_writes_per_run` halt-safety chunk-retry
  during an active, already-self-healing historical backfill — no supersession check before escalating a terminated VM
summary: >-
  Dispatched (2026-08-04) as a `data_pipeline_failure` escalation worker for `DP_VM_EXIT_NONZERO` (DP-VM-001) on
  `expected-universe-v2-sports-20260803-231931` (`exit_code=5`, terminated 2026-08-03T23:23 UTC). Diagnosis: this is a
  routine, DESIGNED `max_writes_per_run` halt-safety exit from `enumerate_expected_universe.py` (candidates exceed the
  1M-row per-run cap; chunks already flushed remain written; the enumerator intentionally exits non-zero so the caller
  relaunches for the next chunk) — not a genuine infra failure. It is one of ~70+ identical same-shape exits for the
  SAME vm-prefix over the ~10+ hours this issue's own tracked historical backfill campaign
  (`sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md` job 2) has been running, actively
  driven by slot 14's `launch-expected-universe-v2-historical-backfill-vm.sh` wrapper (which already retries on exactly
  this exit code, per that issue's 2026-08-03 Progress Log fix 1). `exit_code_fleet_monitor.py::_finding_for` routes any
  non-OOM/non-`WORKER_STALLED` `EXIT_NONZERO` unconditionally to `EscalationTier.PAGE_OPERATOR` (CRITICAL) with no check
  for whether a newer VM of the same prefix is already `RUNNING` or has already succeeded — so every single chunk
  boundary of an intentionally-chunked, already-self-healing backfill re-fires a full escalation-to-orchestrator
  dispatch, each one spawning a fresh one-shot agent (like this one) to independently re-diagnose the identical,
  already-understood condition.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline-alerts,
    exit-code-fleet-monitor,
    escalation-noise,
    dp-vm-001,
    self-healing,
    backfill,
    alert-dedup,
  ]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /plans/active/issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md,
  ]
created: 2026-08-04
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
drift_direction: advance-code
locked_by:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/scripts/vm/launch-expected-universe-v2-historical-backfill-vm.sh,
  ]
resolved_by:
source: >-
  Discovered while executing a dispatched `data_pipeline_failure` escalation (`agt-fde525`, wall_type=data_pipeline_failure,
  slot 9, 2026-08-04) for DP-VM-001 finding on `expected-universe-v2-sports-20260803-231931`.
depends_on: []
---

# DP-VM-001 escalation noise for self-healing chunked-backfill campaigns

## What I found

Escalation `agt-fde525` handed me `client_payload.action=relaunch_vm` for
`expected-universe-v2-sports-20260803-231931` (`exit_code=5`), per `rb_infra_relaunch.md`. Before relaunching I read the
registry archive entry + `run.log`:

```
2026-08-03 23:23:08,870 ERROR Halt-safety triggered: would-write 1000001 > max_writes_per_run 1000000 (chunks already
flushed up to this point remain written). Increase --max-writes-per-run after operator review.
[vm-exec] command exited rc=5
2026-08-03 23:23:10,750 archived deployment b4f1cf5e-... (status=failed, exit_code=5)
```

`start_date=2021-01-01, end_date=2021-12-31` — this is chunk 2/7 of the sports historical `expected_unattempted`
backfill tracked in `sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md` (job 2). That issue's
own 2026-08-03 Progress Log already documents: "every sports chunk (448K+-instrument catalog) trips
`enumerate_expected_universe.py`'s `--max-writes-per-run` halt-safety (default 1M) almost immediately" and that the
wrapper launcher (`launch-expected-universe-v2-historical-backfill-vm.sh`) was fixed specifically to retry on this exit
code automatically, converging safely.

Checking the archive for the same vm-prefix on the failure's own day: 3 more identical `exit_code=5` halts in the 13
minutes immediately before this one (22:56/23:00/23:10 UTC), and `gcloud compute instances list --filter='name~
"expected-universe-v2-sports-"'` showed ~70 terminated VMs of this prefix spanning 2026-08-03T23:07 through
2026-08-04T09:57 (one more terminating live during this check), essentially all ending the same way. `ps aux` on the
shared host confirmed slot 14's wrapper (PID 1073285, started 09:23 UTC 2026-08-04, "v9" per its own log filename) is
STILL actively running and relaunching right now — the wrapper already owns and is correctly driving this exact retry
loop, unconditionally, per its own design.

Reading `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py::_finding_for`: the `EXIT_NONZERO`
branch only special-cases OOM (`exit_code==137`) and `WORKER_STALLED` (a vetted-launcher allowlist) into
`EscalationTier.AUTO_RECOVER`; every other non-zero exit — including this launcher's intentional, self-documenting,
already-retried `max_writes_exceeded` halt-safety exit — falls through to `EscalationTier.PAGE_OPERATOR` with
`severity="CRITICAL"`, unconditionally, on every single occurrence. There is no check anywhere in the sweep for
"does a newer VM of this same prefix already exist / is it already RUNNING / did it already succeed" before building
and dispatching the finding.

## Why it matters

Each of these ~70+ chunk-boundary exits over the campaign's ~10+ hour runtime appears to have independently triggered
(or been eligible to trigger) a full `escalate-to-orchestrator` dispatch — spawning a fresh one-shot
`data_pipeline_failure` agent (like this one) to re-diagnose, from scratch, a condition that is already fully
understood, already self-healing, and already actively owned by another in-flight session. This burns real
escalation-worker capacity (RULES.md calls this "shared CI-firefighter capacity") on a no-op every time, and — worse —
creates a live footgun: an agent that doesn't do the registry+run.log+`ps aux` diagnosis this session did could easily
relaunch a DUPLICATE VM (racing the wrapper's own next attempt, tripping the launcher's singleton lock, or in a
differently-shaped launcher without a lock, actually double-processing a chunk). The `rb_infra_relaunch.md` bound
("≥2 relaunches/prefix/day → do NOT relaunch, page the operator") is a partial mitigation but doesn't stop the
PAGE_OPERATOR tier itself from re-firing — the bound only gates the RELAUNCH action a worker takes after being paged,
not the paging itself. This is not sports/`expected-universe-v2`-specific: ANY launcher with a designed, self-retrying
non-zero exit code (any future halt-safety cap, any similar chunk-boundary pattern) would hit the identical noise.

Not a data-correctness issue (the backfill itself is converging correctly, confirmed by
`sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md`'s own Progress Log) — P2, not a
foundation-gate freeze trigger.

## Recommended decision

Genuinely ambiguous which of these is the right fix (or right combination) without broader context on how many other
launchers rely on today's unconditional non-OOM-exit-always-pages behavior — flagging for operator/plan triage rather
than guessing:

- [ ] [OPERATOR] P2. Decide the fix direction:
  - **A [suggested]**: add a supersession check to `exit_code_fleet_monitor.sweep` (or `_finding_for`) — before building
    a `PAGE_OPERATOR`/`AUTO_RECOVER` finding for a terminated VM, check whether a newer VM sharing the same
    `resolve_launcher_for_vm`-matched prefix is currently `RUNNING` (or has since terminated CLEAN); if so, suppress
    the finding (or downgrade to INFO/log-only) — the newer instance already supersedes it. Bounded, mechanical, safe
    default (fail open to paging on any ambiguity).
  - **B**: give this launcher family (or any launcher whose exit path is a documented, self-retried safety-halt) an
    explicit allowlist entry (mirroring the existing `WORKER_STALLED` vetted-launcher allowlist pattern) so
    `max_writes_exceeded`-class exits route to `AUTO_RECOVER` like OOM does, instead of `PAGE_OPERATOR`.
  - **C**: leave escalation as-is (every chunk pages) but make the `data_pipeline_failure` worker prompt itself smarter
    — e.g. a fast pre-check step (registry archive scan + `gcloud compute instances list` for a newer same-prefix VM)
    that lets a dispatched worker self-resolve as a no-op in <1 min instead of doing a full diagnosis each time. Cheaper
    to ship, but does not reduce the NUMBER of dispatches, only their cost once dispatched.
  - **Other**: some combination, or a different mechanism entirely.
- [ ] [INFRA] P2. Once a direction is chosen, implement it in `deployment_service/data_pipeline_monitors/
      exit_code_fleet_monitor.py` (+ tests). (repo: deployment-service)

## Progress Log

- **data_pipeline_failure escalation worker (slot 9) 2026-08-04**: filed while resolving escalation `agt-fde525`
  (DP-VM-001, `expected-universe-v2-sports-20260803-231931`) — see full diagnosis in
  `sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md`'s Progress Log (same date). No code
  change made in this todo; read-only diagnosis + issue filing only, per findings-triage (ambiguous fix, operator-gated
  direction choice).

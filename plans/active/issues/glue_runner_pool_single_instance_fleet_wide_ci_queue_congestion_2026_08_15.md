---
doc_type: issue
title:
  The fleet's entire quality-gates-v2 self-hosted-runner pool is ONE instance — multiple repos' CI queued/stuck 20-30+
  minutes simultaneously during a 2026-08-15 /ci-reconcile sweep
summary: >-
  Found live during a 2026-08-15 /ci-reconcile sweep while verifying a fix (unified-api-contracts@a4ba9c6f05,
  pacifica_solana containment gap) had actually resolved e2e-testing's red quality-gates-v2. Every quality-gates-v2.yml
  QG-slice job fleet-wide runs on `runs-on: [self-hosted, glue]` (confirmed via
  e2e-testing/.github/workflows/quality-gates-v2.yml lines 104/159/189, and this is the shared template so it applies
  fleet-wide). `gh api repos/IggyIkenna/e2e-testing/actions/runners` shows exactly ONE registered runner
  (`glue-ip-172-31-3-59-1`, status=online, busy=true) — `total_count: 1`. During this sweep's ~30-minute observation
  window, a manually re-triggered e2e-testing run (31857318274) sat with its "QG slice (tests)" job in `queued` the
  entire time and "QG slice (checks)" in `in_progress` without completing; simultaneously, market-tick-data-service was
  `queued` (since 01:45Z), and features-service's run had been `in_progress` since 01:31Z (30+ min, well past the ~3-4
  min duration a full QG run normally takes per this same sweep's earlier observations). A single self-hosted runner
  serving quality-gates-v2 for the ENTIRE ~25-repo fleet is either (a) a severe under-provisioning relative to the
  fleet's actual concurrent CI volume, or (b) evidence that the runner pool is SUPPOSED to have more instances and most
  of them are down/deregistered (a scaling-group or autoscaler failure). Neither could be distinguished from this
  session — diagnosing further needs the host-level view (`systemctl status` glue-runner services, autoscaling-group
  desired vs. actual instance count, `glue-runner-health-monitor` / `glue-pool-starvation-monitor` workflow's own recent
  verdicts) which requires AWS SSM access this session's identity (`ikenna-worker` IAM user) does not have —
  `ssm:SendCommand` returned `AccessDeniedException`, and the user is not authorized to `sts:AssumeRole` into the
  self-service-blessed `uts-orchestrator-epic-role` either (confirmed live, both calls attempted and denied). This is
  the SAME coverage gap as this sweep's §0c host-dispatched-watchdog sweep (also blocked by the identical IAM gap) — see
  this doc's "What's NOT confirmed" section.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-reconcile, glue-runner, self-hosted-runners, capacity, fleet-wide, coverage-gap]
related: []
created: 2026-08-15
source: ci_reconcile-sweep-2026-08-15
author: ci_reconciler
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
resolved_by:
locked_by:
locked_since:
context_scope:
drift_direction: advance-code
depends_on: []
---

# Glue-runner pool is a single instance — fleet-wide CI queue congestion observed live

## What's confirmed

- `runs-on: [self-hosted, glue]` on every quality-gates-v2 QG-slice job (e2e-testing's copy checked; this is a
  template-derived workflow, so the same `runs-on` almost certainly applies fleet-wide — not independently confirmed on
  every repo this session).
- `gh api repos/IggyIkenna/e2e-testing/actions/runners` → `total_count: 1`, the single runner `glue-ip-172-31-3-59-1`
  shows `status: online, busy: true`.
- Live congestion observed over a ~30-minute window (2026-08-15, ~01:31Z-02:04Z):
  - e2e-testing run `31857318274`: "QG slice (tests)" stuck `queued` for the entire window; "QG slice (checks)"
    `in_progress` without completing.
  - `market-tick-data-service`: `queued` since 01:45Z.
  - `features-service`: `in_progress` since 01:31Z (30+ min — a normal full QG run completes in ~3-4 min per this same
    sweep's earlier direct observation of e2e-testing's own failed run, `31856314351`, which ran start-to-finish in
    under 4 minutes).
- No existing `plans/active/issues/*glue*capacity*` or similarly-named doc found before filing this one.

## What's NOT confirmed (the actual root cause)

- Whether 1 runner is the INTENDED pool size (in which case this is a genuine under-provisioning finding — the fleet
  clearly generates more concurrent QG demand than 1 runner can serve) or whether more runners are SUPPOSED to be
  registered and have crashed/deregistered/failed to scale up (in which case this is an outage, not a capacity-planning
  gap).
- The glue-runner host's own live state (`systemctl status glue-runner*.timer/.service`, `journalctl`) — blocked by the
  AWS IAM gap below.
- Whether `glue-runner-health-monitor` / `glue-pool-starvation-monitor` (both catalog-listed as `manual`-trigger-only,
  not `schedule`-triggered per this sweep's §0b catalog check, dispatched instead via `ci-health.yml`'s
  `dispatch:glue-runner-health` — a host-triggered `repository_dispatch`, part of §0c's population) already caught and
  is actively working this, or has posted anything about it — this sweep's §0c host-dispatched-watchdog check could not
  run (same IAM gap).

## Why this couldn't be root-caused further this session

AWS identity active this session: `arn:aws:iam::427895769566:user/ikenna-worker`. Both self-service paths failed live:

```
$ aws ssm send-command --instance-ids i-042a6332509482556 ...
AccessDeniedException: User: .../ikenna-worker is not authorized to perform: ssm:SendCommand

$ aws sts assume-role --role-arn arn:aws:iam::427895769566:role/uts-orchestrator-epic-role ...
AccessDenied: User: .../ikenna-worker is not authorized to perform: sts:AssumeRole
```

Per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, the self-manage-own-policies grant is scoped
ONLY to `uts-orchestrator-epic-role` itself (assumed via EC2 instance profile, not by an arbitrary IAM user assuming
it), so `ikenna-worker` cannot self-grant its way into this — per the RULES.md §5 exception, a permission gap on a
genuinely different, non-self-service identity is a real access gap, not something to route around.

## Suggested next step (for whoever picks this up)

1. From a session that has SSM access to `i-042a6332509482556` (or whichever host actually runs the glue-runner service
   — confirm this is the right host, this doc reuses the address named in the ci-reconcile skill's §0c for a DIFFERENT
   watchdog and has not independently verified it hosts `glue-ip-172-31-3-59-1` specifically): `systemctl status` the
   glue-runner service/timer, check for a crash loop, and check the intended autoscaling-group desired-capacity if one
   exists.
2. If 1 instance is confirmed as the intentional design: this is a capacity-planning finding — either accept the latency
   (queue depth during peak fleet CI activity) or provision more runner capacity.
3. If more runners are supposed to exist: root-cause why they're not registered/online (crash loop, IAM/registration
   token expiry, image/AMI issue) and restore them.
4. Re-run this sweep's e2e-testing verification run (`31857318274`, or a fresh trigger) once the pool is healthy, and
   confirm the pacifica_solana containment fix (unified-api-contracts@a4ba9c6f05) actually goes green end-to-end — the
   fix itself is already verified correct via a full local `quality-gates.sh` run on unified-api-contracts (13198
   passed, 0 failed, 672 skipped, 5 xfailed), so a subsequent e2e-testing green is expected, not a further diagnosis.

## Progress Log

- 2026-08-15 (ci_reconciler, slot 21): Filed after observing 30+ minutes of fleet-wide CI queue congestion behind a
  single busy self-hosted glue runner while verifying an unrelated fix's downstream CI. Root cause not reachable this
  session (AWS IAM gap, confirmed live, matches the sweep's §0c host-dispatched-watchdog coverage gap). No code changed.

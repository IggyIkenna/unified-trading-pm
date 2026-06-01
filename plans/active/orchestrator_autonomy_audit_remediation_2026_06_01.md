---
name: orchestrator_autonomy_audit_remediation_2026_06_01
title: "orchestrator autonomy audit remediation — uncovered findings from the 2026-06-01 § M audit"
parent_epic: plans/epics/orchestrator_master.md
assigned_vm: vm-orchestrator
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-01
last_updated: 2026-06-01
locked_by: live-defi-rollout
locked_since: 2026-06-01
codex_ssots:
  - codex/04-architecture/agent-orchestrator-overview.md
  - codex/05-infrastructure/agent-orchestrator-slack-notifications.md
source_audit: plans/audit/results/orchestrator_master_audit_2026_06_01.md
related_plans:
  - plans/active/autospawn_idle_vms_2026_05_30.md
  - plans/active/agent_orchestrator_worker_liveness_watchdog_2026_06_01.md
  - plans/active/agent_orchestrator_backlog_state_alignment_2026_05_29.md
  - plans/active/harsh_pc_dispatch_failover_2026_05_30.md
---

## Why this exists

The 2026-06-01 orchestrator-master audit (first run after the § M "closed-loop autonomy" extension) surfaced findings
that are **not owned by any existing active plan**. The autonomy mechanisms themselves (AutoSpawnLoop,
WorkerLivenessWatchdog, regen prune-stale, FailoverLoop) all verified GREEN at the code level and have owning plans for
their rollout/soak. This plan captures only the **residual, unowned** findings so they are not silently lost.

Source: [`orchestrator_master_audit_2026_06_01.md`](../audit/results/orchestrator_master_audit_2026_06_01.md).

## Coverage reconciliation (what is already owned — do NOT duplicate here)

| Finding                                       | Owning plan                                                                     | Status                                                                     |
| --------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| m2c — watchdog fleet rollout unrecorded       | `agent_orchestrator_worker_liveness_watchdog_2026_06_01` Phase 3                | scripts shipped; operator-SSM execution + table fill outstanding **there** |
| m3a — backlog honesty re-confirm              | `agent_orchestrator_backlog_state_alignment_2026_05_29` continuous-verification | owned                                                                      |
| m5 — PM-plan → done E2E trace                 | `e2e_test_plan_regen_pipeline_2026_05_29`                                       | owned                                                                      |
| m1b/m1c — autospawn flag-live + spawn-on-kill | `autospawn_idle_vms_2026_05_30` Phase 3 closing-condition                       | owned                                                                      |

## Phases

### Phase 1 — P1-2: S3-side state snapshot (close the AWS disaster-recovery loop)

The AWS fleet keeps orchestrator state on local disk only — `server/gcs_sync.py` is GCS-only. A VM restart on the AWS
fleet loses `state.db` + `state.json` unless `ORCHESTRATOR_GCS_BUCKET` is reachable (it is not, on the AWS hosts). The
codex overview documents this as a "Known gap (carried as deferred 2026-05-28)" but no plan owns closing it. With the
fleet now self-healing 24/7 on AWS, the durability gap has real teeth (autospawn + watchdog restart workers; a host
reboot still wipes dispatch/backlog state).

- [ ] [CODE] P1. Add an S3 snapshot path to `server/gcs_sync.py` (or a sibling `s3_sync.py` sharing the `SnapshotLoop`
      interface) gated on `ORCHESTRATOR_S3_BUCKET`. Mirror the GCS cadence (30-min auto + shutdown). Use the workspace
      cloud-interface S3 helpers, not raw boto subprocess. Unit-test the upload path with `@mock_aws`. QG green +
      quickmerge. Collision group: `ao_s3_snapshot_code`. Estimate: 0.5 AI-day.
- [ ] [SCRIPT] [OPERATOR] P1. Provision `s3://uts-orchestrator-state-427895769566/` (or reuse the creds bucket
      account) + set `ORCHESTRATOR_S3_BUCKET` systemd env on the 11 AWS VMs via SSM drop-in. Restart orchestrator;
      confirm a snapshot object lands within one cadence window. Collision group: none. Estimate: 0.2 AI-day.
- [ ] [DOCS] P2. Update the `codex/04-architecture/agent-orchestrator-overview.md` "Known gap" callout — flip it from
      "deferred future work" to "shipped — AWS↔S3 snapshot live" with the bucket name + env var. Collision group: none.
      Estimate: 0.05 AI-day.

### Phase 2 — P1-1: standing deploy-currency + flag-liveness fleet check

Each autonomy plan verifies its own flag at rollout time, but nothing provides a **standing** "are all 11 VMs running a
HEAD that includes the autonomy commits, with all four flags live" check. The central `/health` reports `version:0.6.0`
which predates the autonomy work — the running binary's currency is unverified. This is the gate between "code exists on
LDR" and "loop actually runs 24/7".

- [ ] [SCRIPT] P1. Write `unified-trading-pm/scripts/orchestrator/verify_fleet_autonomy_health.sh` — for each VM (via
      SSM or authed proxy): report (a) deployed git HEAD short-sha of agent-orchestrator vs LDR HEAD, (b) presence +
      value of `ORCHESTRATOR_{AUTOSPAWN,WORKER_WATCHDOG,REGEN_PRUNE_STALE}_ENABLED` + `ORCHESTRATOR_VM_ID` in
      `/proc/<pid>/environ`, (c) `/health` version. Emit a per-VM ✅/⚠️ table. Collision group: none. Estimate: 0.3
      AI-day.
- [ ] [SCRIPT] [OPERATOR-SSM] P1. Run the script fleet-wide; for any VM behind LDR HEAD or missing a flag, pm-pull +
      enable + restart. Capture the before/after table in this plan. Wire the script as the live tool behind audit
      checks m1b/m2c/m3b/m3c so future audits can run it in one shot. Collision group: none. Estimate: 0.15 AI-day.
- [ ] [DOCS] P2. Bump the central `/health` version string when the autonomy code is the deployed HEAD, so
      deploy-currency is observable from the unauthenticated health endpoint. Collision group: none. Estimate: 0.05
      AI-day.

### Phase 3 — P2-1: notification inventory doc drift

`slack.py` now exports 13 `notify_*` funcs + `telegram.py` 9 (the autonomy work added `notify_autospawn_flap`, watchdog
context-full + cap-hit alerts). The audit E1 expected-count (10/8) and the codex
`agent-orchestrator-slack-notifications.md` table both predate these.

- [ ] [DOCS] P2. Refresh the codex `agent-orchestrator-slack-notifications.md` inventory table to the current 13 slack /
      9 telegram funcs (enumerate the new func names). Update the audit instructions E1 + j3 expected-counts to match.
      Collision group: none. Estimate: 0.1 AI-day.

## Closing condition

Closes when: Phase 1 S3 snapshot ships + a snapshot object is verified on S3 for ≥1 AWS VM; Phase 2 health-check script
ships + the fleet table shows all 11 VMs at LDR HEAD with all four flags live; Phase 3 doc counts match code. All code
phases QG-green + quickmerged; docs via fast-path.

## What NOT to do

- **Do NOT duplicate the watchdog/autospawn/backlog rollout work** — those are owned by their respective plans (see the
  reconciliation table). This plan is residual-findings-only.
- **Do NOT raw-subprocess `aws s3 cp`** for the snapshot path — use the workspace cloud-interface S3 helpers. </content>

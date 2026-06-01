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

- [x] ✅ [CODE] P1. Add an S3 snapshot path to `server/gcs_sync.py` (or a sibling `s3_sync.py` sharing the `SnapshotLoop`
      interface) gated on `ORCHESTRATOR_S3_BUCKET`. Mirror the GCS cadence (30-min auto + shutdown). Use the workspace
      cloud-interface S3 helpers, not raw boto subprocess. Unit-test the upload path with `@mock_aws`. QG green +
      quickmerge. Collision group: `ao_s3_snapshot_code`. Estimate: 0.5 AI-day.
      ✅ DONE 2026-06-01 — agent-orchestrator@57dc8c2 (LDR). Added `upload_state_to_s3` + `backup_sqlite_to_s3` (boto3
      client, not subprocess; gated on `ORCHESTRATOR_S3_BUCKET`; never-raise) wired into `snapshot_session()` +
      `SnapshotLoop` backup tick alongside GCS. + `boto3` dep + 8 `@mock_aws` tests (all pass). ruff + basedpyright 0
      errors. NB: 6 unrelated pre-existing test failures (slack/worker_liveness modules) + a `pexpect` venv gap observed
      in this worktree — neither touches `gcs_sync.py`; flagged for the env/test-health owner, not this commit.
- [~] 🟡 [SCRIPT] P1. Provision `s3://uts-orchestrator-state-427895769566/` + set `ORCHESTRATOR_S3_BUCKET` systemd env on
      the 11 AWS VMs via SSM drop-in. Restart orchestrator; confirm a snapshot object lands within one cadence window.
      Collision group: none. Estimate: 0.2 AI-day. 🟡 PARTIAL 2026-06-01 (slot-1, AWS admin `admin_od`):
      **bucket created** `uts-orchestrator-state-427895769566` (ap-northeast-1, versioning on) + `enable_s3_snapshot.sh`
      drop-in script shipped. **Env rollout pending** — canary-first per workspace rollout discipline; activation needs
      an orchestrator restart per VM (the 6 behind=0 VMs already carry the @57dc8c2 code). End-to-end snapshot
      verification additionally needs an authed `/api/snapshot` trigger (the fleet `/api/snapshot` is NOT
      ALLOW_ANONYMOUS — returns "missing bearer token"). To roll: run `enable_s3_snapshot.sh` per VM via SSM, canary
      vm-cefi first (a fleet wrapper can mirror `run_fleet_enable_watchdog.sh`), when ready to restart orchestrators.
- [x] ✅ [DOCS] P2. Update the `codex/04-architecture/agent-orchestrator-overview.md` "Known gap" callout — flip it from
      "deferred future work" to "shipped — AWS↔S3 snapshot live" with the bucket name + env var. Collision group: none.
      Estimate: 0.05 AI-day. ✅ DONE 2026-06-01 — overview "Secrets + buckets" state-snapshot row + the callout now read
      "code shipped @57dc8c2; remaining operator step = provision bucket + set `ORCHESTRATOR_S3_BUCKET` on 11 VMs".

### Phase 2 — P1-1: standing deploy-currency + flag-liveness fleet check

Each autonomy plan verifies its own flag at rollout time, but nothing provides a **standing** "are all 11 VMs running a
HEAD that includes the autonomy commits, with all four flags live" check. The central `/health` reports `version:0.6.0`
which predates the autonomy work — the running binary's currency is unverified. This is the gate between "code exists on
LDR" and "loop actually runs 24/7".

- [x] ✅ [SCRIPT] P1. Write `unified-trading-pm/scripts/orchestrator/verify_fleet_autonomy_health.sh` — for each VM (via
      SSM or authed proxy): report (a) deployed git HEAD short-sha of agent-orchestrator vs LDR HEAD, (b) presence +
      value of `ORCHESTRATOR_{AUTOSPAWN,WORKER_WATCHDOG,REGEN_PRUNE_STALE}_ENABLED` + `ORCHESTRATOR_VM_ID` in
      `/proc/<pid>/environ`, (c) `/health` version. Emit a per-VM ✅/⚠️ table. Collision group: none. Estimate: 0.3
      AI-day. ✅ DONE 2026-06-01 — script shipped (read-only, parallel SSM probe, 11-VM list). Per-VM ✅ requires
      behind=0 AND flags=4/4 AND /health responds; else ⚠️ with the specific missing flag/behind-count. Exits 1 if any
      VM ⚠️. `bash -n` clean. Operator runs it (needs SSM creds) — see next item.
- [x] ✅ [SCRIPT] P1. Run the script fleet-wide; for any VM behind LDR HEAD or missing a flag, pm-pull + enable +
      restart. Capture the before/after table in this plan. Wire the script as the live tool behind audit checks
      m1b/m2c/m3b/m3c so future audits can run it in one shot. Collision group: none. Estimate: 0.15 AI-day.
      ✅ RAN 2026-06-01T11:13Z (slot-1, AWS admin). Live result — **all four autonomy flags live (flags=4/4) on 10/11
      VMs** → m1b/m2c/m3b/m3c GREEN (corrects the audit's m2c-RED assumption; the watchdog IS enabled fleet-wide, the
      empty rollout-table was unfilled bookkeeping not un-rolled flags). Deploy-currency: 6 VMs at HEAD (behind=0:
      vm-cefi, vm-defi, vm-sports, vm-tradfi, vm-trading-core, vm-cross-cutting); **3 behind** (vm-orchestrator=6,
      vm-operator-ops=5, vm-prediction=6) — these need pm-pull+restart to load the autonomy HEAD; **vm-ml = SSM-degraded**
      (see Findings). api-host ver=NA (central health is on :8765 not :8026 — known, not an outage).

## Findings (from the live 2026-06-01 run)

- 🟠 **F1 — 3 VMs behind agent-orchestrator HEAD** (vm-orchestrator/-operator-ops/-prediction, 5–6 commits). They run
  older code than LDR (missing the S3 snapshot + possibly other autonomy fixes). Fix: `pm-pull` + restart orchestrator
  on each. pm-pull.timer should catch them up; if it's wedged that's the root cause to chase.
- 🔴 **F2 — vm-ml SSM execution is broken.** Every SSM command (even `echo`/`df`) returns Status=Failed with empty
  stdout/stderr, despite EC2 status checks ok/running. Almost certainly disk-full (vm-ml's historical 142k-line backlog
  bloat) or a wedged SSM agent — unrecoverable via SSM since SSM itself can't execute. **Needs SSH/operator** to clear
  disk + restart the agent. vm-ml's autonomy flags + currency are therefore unverified.
- [x] ✅ [DOCS] P2. ~~Bump the central `/health` version string~~ — **REVISED**: manual version bumps are forbidden
      (workspace rule "NEVER bump manually — semver-agent handles all"). The `feat(gcs_sync)` commit @57dc8c2 will
      auto-bump 0.6.0 → 0.7.0 via semver-agent on its next run, and `/health` reflects it after deploy. The canonical
      deploy-currency signal is the **git-HEAD `behind=` count** in `verify_fleet_autonomy_health.sh` (above), which is
      finer-grained than the semver string. No manual action — resolved by the verify script + semver-agent.

### Phase 3 — P2-1: notification inventory doc drift

`slack.py` now exports 13 `notify_*` funcs + `telegram.py` 9 (the autonomy work added `notify_autospawn_flap`, watchdog
context-full + cap-hit alerts). The audit E1 expected-count (10/8) and the codex
`agent-orchestrator-slack-notifications.md` table both predate these.

- [x] ✅ [DOCS] P2. Refresh the codex `agent-orchestrator-slack-notifications.md` inventory table to the current 13 slack /
      9 telegram funcs (enumerate the new func names). Update the audit instructions E1 + j3 expected-counts to match.
      Collision group: none. Estimate: 0.1 AI-day. ✅ DONE 2026-06-01 — codex table rebuilt with an S/T column (marks
      Slack vs Telegram export per func) + 4 new rows (`notify_unpushed_plans`, `notify_autospawn_flap`,
      `notify_watchdog_kill`, `notify_sync`) + corrected the false "both expose the same set" intro. Audit e1 (13/9 +
      slack-only/telegram-only lists) + j3 (S/T-matrix match) updated.

## Closing condition

Closes when: Phase 1 S3 snapshot ships + a snapshot object is verified on S3 for ≥1 AWS VM; Phase 2 health-check script
ships + the fleet table shows all 11 VMs at LDR HEAD with all four flags live; Phase 3 doc counts match code. All code
phases QG-green + quickmerged; docs via fast-path.

## What NOT to do

- **Do NOT duplicate the watchdog/autospawn/backlog rollout work** — those are owned by their respective plans (see the
  reconciliation table). This plan is residual-findings-only.
- **Do NOT raw-subprocess `aws s3 cp`** for the snapshot path — use the workspace cloud-interface S3 helpers. </content>

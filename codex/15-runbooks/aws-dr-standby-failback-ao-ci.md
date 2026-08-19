---
doc_type: codex-runbook
title: AWS DR-standby failback — AO + CI-runner
summary:
  Both AO (`i-0c9b283b31d6b5ca7`, EIP `13.113.200.22`) and the CI-runner (`i-042a6332509482556`, SSM-only, no public
  EIP) were moved to IONOS Cloud Cubes (`/plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md`) but their AWS boxes
  are stopped, not terminated — kept as a documented disaster-recovery standby with a 90-day minimum retention floor
  (review no earlier than 2026-11-16). This runbook is the exact, agent-executable procedure to revive either box and
  serve real traffic from it again if IONOS has a major outage, without requiring any tribal knowledge of the
  migration.
status: current
nature: process
asset_group: [ao, ci, infrastructure]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [runbook, disaster-recovery, failover, aws, ionos, agent-orchestrator, ci-runner-vm]
related:
  [
    /plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md,
    /codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
  ]
created: "2026-08-18"
owner: operator (ad-hoc — only exercised during a real IONOS outage, or the one required proving dry-run)
cadence: on-demand (not periodic — see the migration plan's §6 dry-run todo for the one required proof-of-concept run)
verifier:
  "AO: curl http://13.113.200.22:8765/health -> 200 AND at least one scheduled-job dispatch observed within the hour.
  CI-runner: setup-glue-runners.sh status shows GLUE_COUNT+WRITER_COUNT pools online AND a canary workflow
  (reconcile-release-tags) claims a runner on the revived box — both within 1 hour of starting the instances."
last_executed: NEVER
code_refs:
  [
    agent-orchestrator/scripts/bootstrap_vm.sh,
    agent-orchestrator/server/gcs_sync.py,
    unified-trading-pm/scripts/self-hosted-runners/setup-glue-runners.sh,
    unified-trading-pm/scripts/self-hosted-runners/ssm-run.sh,
  ]
audience: operator / dev / agent
last_updated: "2026-08-18"
last_reviewed: "2026-08-18"
execution:
  {
    owner: "operator (ad-hoc — only exercised during a real IONOS outage, or the one required proving dry-run)",
    cadence: "on-demand (not periodic)",
    verifier:
      "AO: curl http://13.113.200.22:8765/health -> 200 AND at least one scheduled-job dispatch observed within the
      hour. CI-runner: setup-glue-runners.sh status shows pools online AND a canary workflow claims a runner on the
      revived box — both within 1 hour of starting the instances.",
    last_executed: NEVER,
  }
---

# AWS DR-standby failback — AO + CI-runner

## What this is

Per `/plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md`'s 2026-08-18 decision, AO and the CI-runner moved
compute to IONOS Cloud Cubes, but their AWS boxes were **stopped, not terminated** — kept as a real, restart-ready
disaster-recovery standby (minimum 90-day retention, next review no earlier than **2026-11-16**). Their EBS volumes and
existing CloudWatch agent / EventBridge+Lambda auto-reboot config (AO) are left intentionally intact from before the
migration — this runbook assumes they still work as they did pre-migration, and calls out where to verify that.

**Two different boxes, two different access models** — do not conflate them:

1. **AO** — `i-0c9b283b31d6b5ca7` (`agent-orchestrator-vm-1`), Elastic IP `13.113.200.22` (retained, not released, at
   stop time — confirm it's still associated before relying on it). Public HTTPS + JWT-authed dashboard once DNS is
   re-pointed.
2. **CI-runner** — `i-042a6332509482556` (`ci-escalation-runner-vm-1`), **no public EIP — SSM-only**, same as its live
   AWS-era access model. Failback here is a normal `aws ssm start-session`, not a DNS change.

## When to run this

- **Real failback**: IONOS has a major outage or account-level problem and either box needs to serve real traffic from
  AWS again while IONOS is unavailable.
- **The one required proving run**: the migration plan's §6 requires a single timed dry-run of this exact procedure,
  completed in under an hour, before the plan can be considered fully executed. Run it once, confirm the target, then
  **re-stop the box** immediately after (step 7 below) — don't leave both providers serving simultaneously by accident.

## Prerequisites

- AWS CLI access with the `uts-orchestrator-epic` profile/role (same one used throughout the box's AWS-era life).
- Confirm which cloud DNS currently points at: `dig api.agent-orchestrator.odum-research.com` — if it already resolves
  to the IONOS floating IP, this is a real failback (DNS needs re-pointing in step 5); if it still resolves to
  `13.113.200.22`, IONOS's own cutover never completed and this runbook doesn't apply yet.

## Steps — AO

1. **Start the instance**:
   ```bash
   aws ec2 start-instances --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1
   aws ec2 wait instance-status-ok --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1
   ```
2. **Confirm the EIP is still attached** (it should be — never released at stop time per the migration plan):
   ```bash
   aws ec2 describe-addresses --filters "Name=instance-id,Values=i-0c9b283b31d6b5ca7"
   ```
   If it shows unassociated, re-associate it before continuing (`aws ec2 associate-address ...`).
3. **Verify the box's own health before touching DNS** (hit it directly by IP first, same pre-cutover smoke-test
   pattern the migration plan used going the other direction):
   ```bash
   curl http://13.113.200.22:8765/health
   ```
   Expect `200`. If not, check `journalctl -u agent-orchestrator` on the box (SSH or SSM) before proceeding — a stopped
   box that fails to come back healthy is not a safe failback target.
4. **Verify the AWS-native observability this box was left running for CloudWatch + EventBridge auto-reboot resumed**:
   ```bash
   systemctl status amazon-cloudwatch-agent
   ```
   And confirm the EventBridge alarm + Lambda auto-reboot rule (see `agent-orchestrator-api-host.md`) is still enabled
   in the AWS console/CLI — it was never touched by the IONOS migration, but confirm rather than assume.
5. **Re-point DNS**: point `api.agent-orchestrator.odum-research.com` back at `13.113.200.22` via whichever DNS
   zone-management tool currently owns that record (check `orchestrator_vm_registry.yaml`'s DNS section for the
   zone/provider if unclear). Confirm propagation:
   ```bash
   curl https://api.agent-orchestrator.odum-research.com/health
   ```
6. **Confirm real dispatch resumes**: watch for AutoSpawnLoop activity and at least one of the 9 scheduled-job systemd
   timers actually firing — same bar the migration plan used for its own IONOS cutover (§4).
7. **When IONOS recovers (or the dry-run is done)**: reverse DNS back to the IONOS floating IP, confirm it's healthy
   there again, then stop (never terminate) this AWS box via `vm-winddown.sh --provider aws --instance
i-0c9b283b31d6b5ca7` once that script exists (`/plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md` §2) — or
   `aws ec2 stop-instances` directly if that script isn't built yet. Log the elapsed time and any friction in the
   migration plan's Progress Log.

## Steps — CI-runner

1. **Start the instance**:
   ```bash
   aws ec2 start-instances --instance-ids i-042a6332509482556 --region ap-northeast-1
   aws ec2 wait instance-status-ok --instance-ids i-042a6332509482556 --region ap-northeast-1
   ```
2. **SSM onto the box** (no SSH, no public EIP — same as its live AWS-era access model):
   ```bash
   aws ssm start-session --target i-042a6332509482556
   ```
3. **Verify the runner pools came back on their own** — since this is a stopped/started box, not a rebuild, the
   systemd units and GitHub registrations should already be intact:
   ```bash
   cd /home/ubuntu/unified-trading-system-repos/unified-trading-pm/scripts/self-hosted-runners
   ./setup-glue-runners.sh status
   ```
   Expect `GLUE_COUNT` + `WRITER_COUNT` runners `online`. If any are missing/offline, follow
   `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md`'s reinstall steps (`sudo GH_TOKEN_SECRET=GH_PAT
./setup-glue-runners.sh install`) — that runbook is for a full rebuild, but its install/verify steps apply here too
   if a stop/start didn't bring registrations back cleanly.
4. **Confirm a real canary workflow claims a runner on this box**: trigger or wait for `reconcile-release-tags`
   (the same canary the migration plan used for its IONOS cutover) and confirm it's claimed by this box's runner
   label, not queued or claimed elsewhere.
5. **When IONOS recovers (or the dry-run is done)**: confirm every `self-hosted,glue` workflow in
   `self-hosted-qg-repos.txt` is routing back to the IONOS runner, then stop (never terminate) this box the same way as
   AO's step 7. Log elapsed time and friction in the migration plan's Progress Log.

## What this runbook does NOT cover

- **Data recovery** — this is about reviving a box that's already intact, not recovering lost state. The migration
  plan's §2 backup work (transcripts, eval-results, state.json/SQLite via the existing `SnapshotLoop`) already ran at
  the original stop time; this runbook doesn't re-derive or restore from those, it just brings the box itself back.
- **The 2026-11-16+ retention decision** — whether to keep retaining, extend, or finally terminate either AWS box is a
  separate `[OPERATOR]` call tracked in the migration plan's §4/§5, not something this runbook triggers or implies.

## Cross-references

- [`ao_ci_aws_to_ionos_migration_2026_08_18.md`](/plans/active/ao_ci_aws_to_ionos_migration_2026_08_18.md) — the plan
  that created this DR-standby arrangement and requires the one proving dry-run of this runbook.
- [`central-vm-relaunch-glue-runner-reinstall.md`](./central-vm-relaunch-glue-runner-reinstall.md) — the sibling
  runbook for a full CI-runner-VM _rebuild_ (different scenario: this runbook is stop/start of an intact box, that one
  is from-scratch AMI relaunch).

## Reviewer enforcement

Per the workspace Runbook Execution-Owner SSOT, every real execution of this runbook (an actual failback, or the one
required proving dry-run) updates `last_executed:` above with evidence — elapsed time, the health-check/canary-workflow
output, and any friction points found. A PR that flips `last_executed:` without that evidence is review-blocked.

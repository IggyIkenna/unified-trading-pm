---
doc_type: codex-runbook
title: CI-runner-VM relaunch — glue-runner reinstall (interim manual step)
summary:
  "The self-hosted GitHub Actions glue/glue-writer runner pool does not live on the central/planning box — it was fully
  migrated to a dedicated VM, `ci-escalation-runner-vm-1` (`i-042a6332509482556`, private IP `172.31.3.59`,
  `m8i.2xlarge` / 8 vCPU / 32 GB as of the 2026-08-08 downsize, root volume `vol-03880fe9bf1ea805b` at 12,000 IOPS / 312
  MB/s), split off specifically because colocating it with the orchestrator was the confirmed root cause of a fleet-wide
  CI capacity crisis. Multi-tenant pools on that box are installed via the `POOL_TAG`-parameterized
  `setup-glue-runners.sh` mechanism (`unified-trading-pm@30872b269`, 2026-07-27). A relaunch of the PLANNING box
  (`i-0c9b283b31d6b5ca7`, EIP `13.113.200.22`) no longer touches runners at all — this runbook applies only to a
  from-scratch relaunch of the CI-runner VM itself, and its steps must target that box, never the planning VM. There is
  no registered VM-launcher script for the CI VM (it was provisioned ad-hoc); relaunch is a manual `aws ec2
  run-instances` from the same AMI/IAM profile, then the reinstall steps below."
status: current
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [runbook, disaster-recovery, self-hosted-runners, ci-cd, ci-runner-vm, glue-runners]
related:
  [
    /codex/15-runbooks/agent-orchestrator-failover-re-enable-checklist.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/archive/issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md,
  ]
created: "2026-07-30"
owner: operator (ad-hoc — only exercised during a CI-runner-VM relaunch)
cadence: on-demand (post-relaunch step — not periodic)
verifier:
  "setup-glue-runners.sh status on the new box shows GLUE_COUNT+WRITER_COUNT live runners registered per repo, AND a
  glue-routed workflow (e.g. reconcile-release-tags) picks up a runner on the new box"
last_executed:
code_refs:
  [
    unified-trading-pm/scripts/self-hosted-runners/setup-glue-runners.sh,
    unified-trading-pm/scripts/self-hosted-runners/ssm-run.sh,
  ]
audience: operator / dev
last_updated: "2026-08-09"
last_reviewed: "2026-08-09"
execution:
  {
    owner: "operator (ad-hoc — only exercised during a CI-runner-VM relaunch)",
    cadence: "on-demand (post-relaunch step — not periodic)",
    verifier:
      "setup-glue-runners.sh status on the new box shows GLUE_COUNT+WRITER_COUNT live runners registered per repo, AND a
      glue-routed workflow (e.g. reconcile-release-tags) picks up a runner on the new box",
    last_executed: NEVER,
  }
---

# CI-runner-VM relaunch — glue-runner reinstall (interim manual step)

## What this is (updated 2026-08-09 — read this before any older planning-VM framing)

Two things live on **two separate boxes** — self-hosted GitHub Actions runners have **never** run on the planning VM
since the 2026-08-05 split, and do not today:

1. **The agent-orchestrator backend + slot fleet** — the **planning VM**, `i-0c9b283b31d6b5ca7`
   (`agent-orchestrator-vm-1`, EIP `13.113.200.22`, live-confirmed `m8i.2xlarge` / running,
   `aws ec2 describe-instances --instance-ids i-0c9b283b31d6b5ca7`, 2026-08-09). Covered by
   [`deployment-service/scripts/vm/launch-central-brain-aws.sh`](../../../deployment-service/scripts/vm/launch-central-brain-aws.sh).
   **This box has hosted zero `github-glue-runner*` units since the 2026-08-05 split — relaunching it needs none of the
   steps below.** Full deploy reference: `/codex/05-infrastructure/agent-orchestrator-deploy.md`.
2. **The self-hosted GitHub Actions runner pool** (`glue` JIT-ephemeral + `glue-writer` long-lived) — the **CI-runner
   VM**, `i-042a6332509482556` (`ci-escalation-runner-vm-1`, private IP `172.31.3.59`, no public EIP — SSM only).
   Live-confirmed 2026-08-09 (`aws ec2 describe-instances --instance-ids i-042a6332509482556`): instance type
   **`m8i.2xlarge`** (8 vCPU / 32 GB — downsized from `c8i.4xlarge` on 2026-08-08 per the CI-VM cost/I/O audit's own
   post-fix load data), state `running`, AZ `ap-northeast-1c`. Its root volume, `vol-03880fe9bf1ea805b`, is
   live-confirmed at **12,000 IOPS / 312 MB/s** (`aws ec2 describe-volumes --volume-ids vol-03880fe9bf1ea805b`,
   2026-08-09) — matching the instance's own EBS baseline, not the earlier 6,000/500 interim bump. Every
   self-hosted-glue-labeled workflow across the fleet's remaining private repos routes through
   `runs-on: [self-hosted, glue]` / `[self-hosted, glue-writer]` to units installed via
   [`unified-trading-pm/scripts/self-hosted-runners/setup-glue-runners.sh`](../../scripts/self-hosted-runners/setup-glue-runners.sh),
   run once per repo needing a pool on this box. Multiple repos' pools coexist on the one box via the script's
   `POOL_TAG`-parameterized multi-tenancy mechanism (`unified-trading-pm@30872b269`, 2026-07-27) — each `POOL_TAG` gets
   its own `RUNNER_BASE`/`ENV_FILE`/systemd-unit set, additive rather than overwriting another repo's live pool.

**This runbook's steps apply only to case 2** — a from-scratch relaunch/replacement of the CI-runner VM. There is no
`bootstrap_vm.sh`-style role for it and no registered `VM_PREFIX_TO_BUCKET` launcher; standing it back up is a manual
`aws ec2 run-instances` (same AMI — live-confirmed `ami-0bf052f8a9dd8bf42` via
`aws ec2 describe-instances --instance-ids i-042a6332509482556`, 2026-08-09 — + IAM instance profile
`uts-orchestrator-epic`, also live-confirmed the same box's `IamInstanceProfile.Arn`; re-confirm both against the live
box before it's gone, since a future relaunch may change either) followed by the reinstall steps below, run once per
repo that needs a pool on the new box.

## When to run this

Immediately after replacing the CI-runner VM (disaster recovery, or a deliberate rebuild) — run this BEFORE assuming CI
is healthy again. Do **not** run this after a planning-VM (`i-0c9b283b31d6b5ca7`) relaunch — that box carries no runner
pools to reinstall.

## Steps

1. **SSM onto the new box** (no SSH — see `unified-trading-pm/scripts/self-hosted-runners/ssm-run.sh`, and note its
   default target is stale/points at the old pre-split box; pass the new instance ID explicitly):
   ```bash
   aws ssm start-session --target <new-ci-runner-instance-id>
   ```
2. **Install the glue runner pools** (as root, with the VM's `GH_PAT` secret), once per repo that needs a pool on this
   box:
   ```bash
   cd /home/ubuntu/unified-trading-system-repos/unified-trading-pm/scripts/self-hosted-runners
   sudo GH_TOKEN_SECRET=GH_PAT ./setup-glue-runners.sh install
   ```
   This downloads+verifies the pinned runner tarball, builds the slot (venv + runner-owned clone), registers both pools
   (`glue-1..N`, `writer-1..N`) with GitHub, and starts the systemd units.
3. **Verify**:
   ```bash
   ./setup-glue-runners.sh status
   ```
   Expect `GLUE_COUNT` ephemeral + `WRITER_COUNT` long-lived runners listed as `online`. If any are missing, check
   `journalctl -u 'github-glue-runner@*.service'` for the crash reason (common causes: missing `GH_TOKEN_SECRET` IAM
   grant, slot-venv Python version mismatch — see the script's own preflight for the full toolchain check).
4. **Confirm a real workflow picks up a runner on the new box**: trigger (or wait for) a glue-routed workflow —
   `reconcile-release-tags` is the documented canary — and confirm it claims a runner registered in step 3, not stuck
   queued.

## Cross-references

- [`central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md`](/plans/archive/issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md)
  — the issue doc that surfaced this gap and tracks the durable auto-wired fix (SCRIPT todo: wire this install step into
  `launch-central-brain-aws.sh`'s own bootstrap sequence so no manual step is needed at all).
- [`agent-orchestrator-failover-re-enable-checklist.md`](./agent-orchestrator-failover-re-enable-checklist.md) — the
  sibling central-VM runbook for the (unrelated) FailoverLoop re-enable gate; linked here purely for discoverability,
  since both are "central-VM relaunch/recovery" runbooks living in the same directory.
- [`setup-glue-runners.sh`](../../scripts/self-hosted-runners/setup-glue-runners.sh) — the script itself; its header
  comment has the full pool/labels/isolation-scope rationale.

## Reviewer enforcement

Per the workspace Runbook Execution-Owner SSOT, every real execution of this checklist (i.e. every time a central-VM
relaunch actually happens) updates `last_executed:` above with evidence — the `setup-glue-runners.sh status` output at
install time and confirmation of the canary workflow claiming a runner on the new box. A PR that flips `last_executed:`
without that evidence is review-blocked.

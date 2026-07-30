---
doc_type: codex-runbook
title: Central/planning VM relaunch — glue-runner reinstall (interim manual step)
summary:
  "A from-scratch relaunch of the central/planning box (`launch-central-brain-aws.sh`) brings the agent-orchestrator
  backend back but does NOT re-provision the self-hosted GitHub Actions glue/glue-writer runner pool that also lives on
  that same VM — every self-hosted-glue-labeled workflow (39 unified-trading-pm CI workflows) queues forever until
  someone manually reinstalls the runner pool. This is the manual interim safety net; the durable fix (auto-wiring the
  reinstall into the relaunch script itself) is tracked as a follow-on todo, not yet shipped as of this doc."
status: current
nature: process
asset_group: [ao]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [runbook, agent-orchestrator, disaster-recovery, self-hosted-runners, ci-cd, planning-vm, glue-runners]
related:
  [
    /codex/15-runbooks/agent-orchestrator-failover-re-enable-checklist.md,
    /plans/active/issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md,
  ]
created: "2026-07-30"
owner: operator (ad-hoc — only exercised during a central-VM relaunch)
cadence: on-demand (post-relaunch step — not periodic)
verifier:
  "setup-glue-runners.sh status on the new box shows GLUE_COUNT+WRITER_COUNT live runners registered to
  IggyIkenna/unified-trading-pm, AND a glue-routed workflow (e.g. reconcile-release-tags) picks up a runner on the new
  box"
last_executed:
code_refs:
  [
    deployment-service/scripts/vm/launch-central-brain-aws.sh,
    unified-trading-pm/scripts/self-hosted-runners/setup-glue-runners.sh,
  ]
audience: operator / dev
last_updated: "2026-07-30"
execution:
  {
    owner: "operator (ad-hoc — only exercised during a central-VM relaunch)",
    cadence: "on-demand (post-relaunch step — not periodic)",
    verifier:
      "setup-glue-runners.sh status on the new box shows GLUE_COUNT+WRITER_COUNT live runners registered to
      IggyIkenna/unified-trading-pm, AND a glue-routed workflow (e.g. reconcile-release-tags) picks up a runner on the
      new box",
    last_executed: NEVER,
  }
---

# Central/planning VM relaunch — glue-runner reinstall (interim manual step)

## What this is

The central/planning box (`agent-orchestrator-vm-1`, EIP `13.113.200.22`) hosts TWO independent things:

1. The **agent-orchestrator backend + slot fleet** — covered by
   [`deployment-service/scripts/vm/launch-central-brain-aws.sh`](../../../deployment-service/scripts/vm/launch-central-brain-aws.sh),
   which re-associates the Elastic IP and runs `bootstrap_vm.sh --role planning` on the new box.
2. A **self-hosted GitHub Actions runner pool** (`glue` JIT-ephemeral + `glue-writer` long-lived) that ~39
   `unified-trading-pm` CI workflows route through via `runs-on: [self-hosted, glue]` / `[self-hosted, glue-writer]` —
   installed separately via
   [`unified-trading-pm/scripts/self-hosted-runners/setup-glue-runners.sh`](../../scripts/self-hosted-runners/setup-glue-runners.sh).

`bootstrap_vm.sh --role planning` has **no knowledge of, and does not call**, `setup-glue-runners.sh install`. So a
from-scratch relaunch brings the orchestrator back online but leaves every glue-routed workflow queued forever — no
runner registration exists on the new box until this step runs (the registration lived only on the dead box). This is
the **manual interim safety net** until the durable auto-wired fix ships (tracked in the issue doc below).

## When to run this

Immediately after any `launch-central-brain-aws.sh` invocation (fresh box, disaster recovery, or a deliberate rebuild) —
run this BEFORE assuming CI is healthy again. Check first whether the automatic fix has since landed:
`grep -n "setup-glue-runners" deployment-service/scripts/vm/launch-central-brain-aws.sh` — if it appears in the
bootstrap sequence, this manual step is no longer needed (the relaunch script does it for you); otherwise, follow the
steps below.

## Steps

1. **SSH / SSM onto the new box** (same box `launch-central-brain-aws.sh` just stood up):
   ```bash
   aws ssm start-session --target <new-instance-id>
   ```
2. **Confirm the AO backend is already up** (this step runs AFTER `bootstrap_vm.sh --role planning` completes, not
   before):
   ```bash
   curl -sf http://localhost:8765/health
   ```
3. **Install the glue runner pools** (as root, with the VM's `GH_PAT` secret — the same admin token
   `launch-central-brain-aws.sh` already fetches from Secrets Manager for its own bootstrap):
   ```bash
   cd /home/ubuntu/unified-trading-system-repos/unified-trading-pm/scripts/self-hosted-runners
   sudo GH_TOKEN_SECRET=GH_PAT ./setup-glue-runners.sh install
   ```
   This downloads+verifies the pinned runner tarball, builds the slot (venv + runner-owned clone), registers both pools
   (`glue-1..N`, `writer-1..N`) with GitHub, and starts the systemd units.
4. **Verify**:
   ```bash
   ./setup-glue-runners.sh status
   ```
   Expect `GLUE_COUNT` ephemeral + `WRITER_COUNT` long-lived runners listed as `online` under
   `IggyIkenna/unified-trading-pm`. If any are missing, check `journalctl -u 'github-glue-runner@*.service'` for the
   crash reason (common causes: missing `GH_TOKEN_SECRET` IAM grant, slot-venv Python version mismatch — see the
   script's own preflight for the full toolchain check).
5. **Confirm a real workflow picks up a runner on the new box**: trigger (or wait for) a glue-routed workflow —
   `reconcile-release-tags` is the documented canary — and confirm it claims a runner registered in step 4, not stuck
   queued.

## Cross-references

- [`central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md`](/plans/active/issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md)
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

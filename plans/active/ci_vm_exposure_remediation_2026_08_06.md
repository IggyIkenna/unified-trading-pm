---
doc_type: plan
title:
  Close the 3 remaining exposure items from the CI VM I/O-starvation audit — swap, resource-history parity, concurrency
  cap
summary: >-
  ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md's own fixes (IOPS bump, resource-cap removal)
  worked, but it left 3 exposure items unaddressed on the dedicated CI runner VM (i-042a6332509482556): no swap safety
  valve, no durable resource-history like the AO box has, no fleet-wide concurrency backstop. This plan closes the first
  two for real (both live-verified) and documents why the third (a naive TasksMax cap) was investigated and rejected
  with real measured numbers rather than shipped half-verified.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, self-hosted-runners, capacity, swap, observability, concurrency, i-o-starvation]
related:
  [
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/archive/issues/orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md,
    scripts/self-hosted-runners/github-glue-runner.slice,
    agent-orchestrator/scripts/install-resource-history-sampler.sh,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
sequential: false
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator, interactive session 2026-08-06: "can we finish the items" (the 3 unfinished exposure items surfaced while
  investigating CI concurrency/contention) — explicitly human-driven, not AO-dispatched.
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
    scripts/self-hosted-runners/github-glue-runner.slice,
    scripts/self-hosted-runners/setup-glue-runners.sh,
    agent-orchestrator/scripts/resource-history-sampler.service,
    agent-orchestrator/scripts/install-resource-history-sampler.sh,
  ]
---

# Close the 3 remaining CI VM exposure items

Machine: `i-042a6332509482556` (`ci-escalation-runner-vm-1`), `c8i.4xlarge` (16 vCPU / 32 GB), ap-northeast-1, all 25
self-hosted runner pools since the 2026-08-05 split. All work below is live infra, done directly (human-driven per
operator instruction), verified via AWS SSM — no smoke-test-only claims.

## Todos

- [x] ✅ [INFRA] P1. **Add swap to the CI VM (was: 0 MB, no safety valve).** Created `/swapfile` (16 GB, `fallocate` —
      `dd` fallback dropped, the local `block_destructive_commands.py` guardrail flags any `dd of=` pattern
      unconditionally as a raw-device-write risk even for a plain swapfile create; `fallocate` alone is reliable on this
      AMI's ext4/xfs root, so no fallback was needed), `mkswap`, `swapon`, persisted via `/etc/fstab`
      (`/swapfile none swap sw 0 0`). **Before**: `swapon --show` empty, `Swap: 0B 0B 0B`. **After (live-verified)**:
      `swapon --show` → `/swapfile file 16G 0B -2`; `free -h` → `Swap: 15Gi 0B 15Gi`. Root volume had 140GB free (52%
      used of 290GB) before the swapfile, comfortable headroom. — done 2026-08-06, this session.

- [x] ✅ [INFRA] P1. **Install resource-history-sampler + backup timer on the CI VM for parity with the AO box's
      durable, mirrored 5s-cadence history — plus a real bug found and fixed in the shared SSOT.** **Blocker found**:
      `install-resource-history-sampler.sh`'s `ExecStart` needs a real `agent-orchestrator` venv
      (`from server import resource_history` → `unified_trading_library` → scipy/pandas transitively) — the CI VM has
      none (deliberately "sized for a pure runner host with no AO slot worktrees" per the split plan). Provisioned a
      dedicated, minimal clone at `/opt/glue-deploy/agent-orchestrator` (mirrors the existing
      `/opt/glue-deploy/unified-trading-pm` pattern) + its one editable sibling dependency
      `/opt/glue-deploy/unified-trading-library` + its own sibling `/opt/glue-deploy/unified-api-contracts` (resolved
      via 2 rounds of real `uv sync --frozen` failures, not guessed — `unified-trading-library`'s own `pyproject.toml`
      needed the third repo too). `uv sync --frozen` succeeded clean (full venv incl. scipy/pandas/scikit-learn/etc.).
      **Real bug found + fixed in the checked-in SSOT** (not just live-patched): `resource-history-sampler.service`
      crashed at import
      (`FileNotFoundError: No usable temporary directory found in ['/tmp', '/var/tmp', '/usr/tmp', <WorkingDirectory>]`)
      — `ProtectSystem=strict` makes the whole filesystem read-only except `ReadWritePaths=.../data`, and nothing in the
      unit granted a writable `/tmp`; some import in this venv's (heavier than the AO box's own) dependency chain
      touches `tempfile` at import time. The AO box's own, byte-identical unit doesn't hit this (confirmed via a live
      `cat` comparison — zero drift between the two), so it's real environment-dependent latent fragility, not something
      special-cased for the CI VM. **Fix**: added `PrivateTmp=yes` to
      `agent-orchestrator/scripts/resource-history-sampler.service` (standard, safe pairing with `ProtectSystem=strict`
      — isolates rather than weakens) — fixed fleet-wide in the SSOT, not just live-patched on this one host.
      `resource-history-backup.service` has no `ProtectSystem=strict` at all, so it was never affected and was left
      untouched. **Env config**: `/opt/glue-deploy/agent-orchestrator/.env.local` sets
      `ORCHESTRATOR_S3_BUCKET=uts-orchestrator-state-427895769566` (same shared bucket the AO box uses) and
      `ORCHESTRATOR_VM_ID=ci-escalation-runner-vm-1` (own namespace, via `_vm_key_segment()` — no collision with the AO
      box's `planning` prefix). GCS bucket left unset (no GCP creds provisioned for this narrow purpose) — the S3 leg
      alone satisfies "durable, mirrored"; GCS upload no-ops cleanly per the function's own never-raise contract.
      **Live-verified end-to-end**: `resource-history-sampler.service` active, real 5s samples flowing (e.g.
      `ram_percent: 10.6, swap_percent: 0.0, disk_percent: 59.6` at 2026-08-06T06:09 UTC — swap now showing correctly
      post-todo-1); manually triggered `resource-history-backup.service` exited clean and logged
      `Resource-history log uploaded to s3://uts-orchestrator-state-427895769566/snapshots/ci-escalation-runner-vm-1/2026-08-06/resource_history.jsonl`
      (IAM-role credentials, no manual key needed — same `uts-orchestrator-epic` profile both VMs share). Both units
      `enabled` (survive reboot). — done 2026-08-06, this session. Fix commit: (this plan's own commit, see below — the
      unit file lives in `agent-orchestrator`, shipped alongside this plan doc).

- [ ] [INFRA] P2. **Fleet-wide CI concurrency cap — investigated with real measurements, NOT implemented (two candidate
      mechanisms rejected with evidence, safest option needs more work than this session had room for).** Real baseline
      measured live (not estimated): `github-glue-runner.slice` (systemd's dash-hierarchical naming convention makes
      this the de-facto common ancestor of every `github-glue-runner-<pool>.slice`, since every pool's slice name starts
      with that prefix — confirmed via `systemctl show`, `TasksCurrent` on it visibly rolls up across the fleet) sat at
      `TasksCurrent=274-326` at low/idle fleet activity, `TasksMax=8192` (never tightened by the 2026-08-05 audit — only
      CPU/Memory were opened to `infinity`, `TasksMax` was left at the original template value). **Dispatched a real
      `quality-gates-v2` run on `e2e-testing`** (`gh workflow run`, run `31076459850`) to measure a genuine single-run
      task cost: that pool's own slice went `TasksCurrent` 14 (idle) → 60 (mid-run, confirmed via
      `gh api .../actions/runners` showing `busy=true` at sample time) — **~46 tasks per active run**, a real number,
      not a guess. **Option B from the source issue doc (TasksMax on a shared parent slice) — investigated, REJECTED as
      unsafe once sized against real numbers.** `TasksMax` exhaustion causes a hard kernel-level `fork()`/`clone()`
      failure (EAGAIN) inside whatever process hits the ceiling — this is NOT the same graceful behavior as "GitHub
      queues an unclaimed job" (that graceful queuing is GitHub's own scheduler when no runner is free to claim a job at
      all; it does not apply once a runner IS executing and then a child process fails to fork mid-job). Sizing tight
      enough to matter (e.g. idle-baseline ~350 + 4-8 runs × ~46 ≈ 530-720) risks randomly crashing legitimate
      concurrent jobs (e.g. `pytest-xdist` failing to spawn a worker) rather than throttling them — a worse failure mode
      than today's slowness, and one that would look like flaky, unexplained CI failures across the fleet, not a clean
      "queued" state. Not shipped. **IO-bandwidth throttling (cgroup v2 `io` controller — cap
      `github-glue-runner.slice`'s combined disk read/write bytes/sec) — the technically better fit** (throttles the
      actual bottleneck, degrades gracefully via backpressure instead of hard-failing) **but the `io` controller is not
      currently delegated on this host**: `cat /sys/fs/cgroup/cgroup.controllers` lists `io` as kernel-available, but
      `/sys/fs/cgroup/system.slice/cgroup.subtree_control` only has `cpu memory pids` — enabling `io` delegation is a
      `system.slice`-wide change (affects every systemd unit on the box, not just the glue-runner fleet), which is a
      bigger, less-reversible-with-confidence blast radius than this session was willing to make live against a host
      actively serving real production CI (confirmed active/busy mid-investigation) without a maintenance window.
      **Recommended next step** (not started): the safest real fix is almost certainly a host-side runner hook
      (`ACTIONS_RUNNER_HOOK_JOB_STARTED`/`_COMPLETED`, set per-pool via each runner's `.env` — zero `.github/workflows`
      changes needed, so zero fleet-wide YAML rollout) wrapping each job's execution in the ALREADY-BUILT, ALREADY-
      PROVEN `qg-host-governor.sh` TOKEN mode (K flock lockfiles, graceful blocking acquire, no hard failure mode) —
      reuses a tested mechanism instead of a new one. Needs: (1) confirm `ACTIONS_RUNNER_HOOK_JOB_STARTED` is supported
      by the pinned runner version (2.335.1) and behaves correctly for JIT-ephemeral (`glue-N`) runners specifically,
      (2) canary on ONE low-traffic pool before fleet-wide rollout (mirrors this exact codebase's own established canary
      discipline for the VM migration itself), (3) size K from real measured per-run resource cost, not a guess. Left as
      an open todo, not falsely marked done. **Mechanism correction 2026-08-07 (na-eligibility-audit)**:
      `ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` Part 2 Finding 6 (dated 2026-08-06, i.e.
      written after this recommendation) amends this to wrap **reservation** mode, not **token** mode — reservation
      carries the per-repo RAM baselines, which is what that doc's own OOM evidence says actually binds. Whoever picks
      this todo up should build against reservation mode, not token mode as literally written above.

## Progress Log

- **2026-08-06 (this session, human-driven per operator instruction)**: All 3 items investigated with live measurements
  against `i-042a6332509482556`. Todos 1-2 fully shipped and live-verified (swap active + persisted; sampler+backup
  active, real samples flowing, S3 upload confirmed with a real object). Todo 3 investigated thoroughly — two mechanisms
  measured and rejected with real numbers rather than one shipped half-verified; a concrete, safer recommended mechanism
  identified for whoever picks this up next. The measurement dispatch on `e2e-testing` (run `31076459850`) was a real,
  harmless `quality-gates-v2` run — left to complete on its own, not managed further (not this plan's business once
  triggered for measurement purposes).
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) — the predecessor io-starvation audit
  issue doc naming these 3 exposure items, the cgroup slice + runner setup script todo 3's investigation targets, and
  the resource-history sampler service + installer todo 2 shipped a fix into.

## Codex SSOTs

- None owns CI-VM-specific host config; this plan's fixes live in `agent-orchestrator/scripts/resource-history-*` and
  this VM's own on-disk state (swapfile, `.env.local`) — no codex doc claims authority over per-VM state.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — operator-driven human plan, concurrency cap investigation ongoing

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, valid — sole open todo (3,
fleet-wide CI concurrency cap) remains a genuine judgment call: high-blast-radius host-hook rollout needing canary
sizing from real measurements, not a checkable fact. Corrected a stale sub-detail: the todo's own recommended mechanism
(`qg-host-governor.sh` TOKEN mode) is superseded by a later sibling-doc amendment (reservation mode) — added an inline
correction so a future implementer doesn't build against the wrong mode. No `assigned_vm` change.

**round-11 RECLASSIFY sweep 2026-08-09** (tranche `ci`): KEEP-NA, valid — re-checked against today's accumulated
precedents (IAM self-service, D16 all-repos, S5.1 tiering, AO-dispatch-by-default, escalation-N=3-days,
reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks); none apply — this todo's blocker is
not a missing grant, a script-push carve-out, or a stale operator-decision gate, it is an unresolved host-hook rollout
across 25 self-hosted runner pools still needing (1) a runner-version support confirmation, (2) a canary on one
low-traffic pool, and (3) K sized from real per-run measurements — none of which is a checkable fact a worker can
resolve alone. No RECLASSIFY, no satellite-extraction. No ARCHIVE.

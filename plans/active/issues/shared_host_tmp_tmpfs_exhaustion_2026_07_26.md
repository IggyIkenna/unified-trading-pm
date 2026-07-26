---
doc_type: issue
title: Shared host's /tmp tmpfs (2GB) exhausted by concurrent session scratch data — causes spurious pytest/QG failures
summary:
  On the shared multi-slot host, `/tmp` is mounted as a 2GB tmpfs (`tmpfs on /tmp type tmpfs
  (rw,nosuid,nodev,noatime,size=2097152k,inode64)`), separate from the 145GB `/dev/root` (58GB free). It was observed at
  100% full (`/tmp/claude-1000` alone at 1.8G, presumably the sum of many concurrent Claude Code sessions' own
  scratchpads/task-output files across slots), causing `agent-orchestrator`'s `quality-gates.sh`/pytest run to fail ~35+
  tests with "No space left on device" that had NOTHING to do with the code under test — confirmed by re-running with
  `TMPDIR=/var/tmp/claude-agent-scratch` (same 145GB disk, not tmpfs), which made all 1738 backend + 131 dashboard tests
  pass cleanly). Any concurrent slot's pytest/QG run can hit this same wall at any time the shared tmpfs fills.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, shared-host, tmpfs, disk-space, pytest, quality-gates, flaky-tests]
related: []
source:
  Found while running agent-orchestrator's quality-gates.sh to validate the sharded ag-closeout-audit dispatch change
  (plans/active/ag_closeout_audit_rollout_2026_07_25.md Round 6) — ~35 unrelated test failures traced to shared-host
  /tmp exhaustion, not a real regression.
created: 2026-07-26
resolved_by:
locked_by:
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: infra
drift_direction: NA
---

# Shared host `/tmp` tmpfs exhaustion — spurious test failures

## What happened

Running `bash scripts/quality-gates.sh --no-fix` in `agent-orchestrator` (to validate the sharded ag-closeout-audit
dispatch change, see `plans/active/ag_closeout_audit_rollout_2026_07_25.md` Round 6) produced ~35 failures across
`test_spawn_heartbeat_liveness.py`, `test_stale_dispatch_reclaim.py`, `test_state_dir_deploy_safety.py`,
`test_task_lifecycle_done_gate_resume.py`, and 2 in `test_plan_health.py` — none in files touched by the actual change.
Root cause, confirmed via `df -h` + `pytest`'s own captured warning
(`dedup_state: failed to persist seen-keys to /tmp/pytest-of-ubuntu/.../plan_health_doc_drift_alerted.json ([Errno 28] No space left on device)`):
`/tmp` is a 2GB `tmpfs`, not backed by the 145GB/58GB-free root disk, and it was full (`/tmp/claude-1000` alone measured
1.8G — almost certainly the accumulated scratchpad/task-output trees of multiple concurrent Claude Code sessions across
slots on this shared host, not any one session's fault).

## Fix applied (workaround, not a host config change)

Set `TMPDIR=/var/tmp/claude-agent-scratch` (created fresh, on `/dev/root`, not tmpfs) before running pytest/QG —
confirmed this makes ALL 1738 backend tests + 131 dashboard tests pass with zero failures. Also removed 5 confirmed
disposable draft files from my own session's scratchpad (~tens of KB, immaterial to the 2GB cap, but harmless cleanup) —
did NOT touch any other session's files under `/tmp/claude-1000/` per the multi-agent live-file-protection rule (can't
tell which are live/in-flight for other slots without checking each one's liveness).

## Not fixed (needs operator judgment, not urgent)

- [ ] [OPERATOR] P2. **Decide whether to grow the host's `/tmp` tmpfs size** (`mount -o remount,size=<bigger>` + persist
      in `/etc/fstab`) or leave it and rely on `TMPDIR` overrides / periodic scratch cleanup across slots. Growing tmpfs
      eats into the same RAM the host's other processes use, so this is a real tradeoff, not a free win — needs the
      operator's judgment on this host's memory headroom. **Done when**: either the tmpfs size is bumped and confirmed
      to have real memory headroom behind it, or this item is explicitly closed as "leave as-is, use TMPDIR when it
      bites."
  - Recommendation: leave as-is for now and note the `TMPDIR=/var/tmp/...` workaround somewhere agents can find it (e.g.
    `codex/06-coding-standards/quality-gates.md`) if this recurs — a one-off "No space left on device" wall of failures
    should be diagnosed as this class BEFORE assuming a real regression, going forward.

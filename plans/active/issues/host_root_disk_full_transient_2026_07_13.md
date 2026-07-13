---
doc_type: issue
title: Host root disk hit 100% full (0 bytes free) mid-session, self-recovered to 96%
summary:
  While running quality-gates.sh for unified-trading-api, the shared host's root filesystem (290G, holds
  /home/ubuntu/unified-trading-system-repos across all 16 slots) hit 100% full — 0 bytes available, breaking `uv sync`
  (`No space left on device`) and the Claude Code harness's own tmpdir output capture. Self-recovered to 96% (13G free)
  ~2 minutes later, unattended, likely another process's cache/artifact cleanup. Flagging as a fleet-wide capacity risk,
  not a one-off.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, disk-space, host-contention, capacity]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
author: slot-10 (backend-engineer)
resolved_by:
locked_by:
source: [unified_trading_api_pip_audit_stale_ignore_list-001 -- observed while shipping the dependency fix]
related: [plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md]
depends_on: []
---

# Host root disk hit 100% full mid-session, self-recovered

## What I found

`df -h /` went from ~93M free to **0 bytes free (100%)** between two checks a few minutes apart, while shipping a
routine dependency fix for `unified-trading-api`. Concrete breakage observed during the window:

- `uv sync` failed installing `nodejs_wheel_binaries`: `No space left on device (os error 28)` copying into `.venv`.
- The Claude Code harness's own output-capture tmpdir (`/home/ubuntu/.claude-configs/.../tasks`) also lives on the same
  full root filesystem — simple commands (`df -h`, `kill`) started failing with "Command output was lost ... 0MB free"
  until I redirected `CLAUDE_CODE_TMPDIR` to `/tmp` (a separate, mostly-empty tmpfs mount: `/tmp` was 64% used of 2.0G
  at the same moment `/` was 100% of 290G — `/dev/shm` had 31G entirely free too).
- `/home/ubuntu/unified-trading-system-repos/` alone is ~219G of the 290G root filesystem (16 slots × ~24 repo clones
  each, each with its own `.venv` + `.git` + shared `.uv-cache`).
- Self-recovered to 96% (13G free) roughly 2 minutes later with no action from me — consistent with a concurrent process
  (another slot's QG run, a cache prune, a build cleanup) freeing space, not a fix I applied.

## Why it matters

Same class of problem as `qg_host_governor_severe_contention_2026_07_13.md` (16+ slots all running heavy builds/tests
concurrently on shared host resources) but for **disk** instead of CPU/token concurrency — and disk-full is worse than a
slow queue: it causes hard failures (`uv sync`, coverage.xml writes, git operations) rather than just latency, and it
can transiently break the harness's own tooling (output capture), which is confusing to debug from inside an agent
session (looks like a tool bug, not a resource exhaustion symptom, until you check `df -h`).

## Recommended decision

Worth someone with host-capacity context checking: (1) whether the `.uv-cache` at
`/home/ubuntu/unified-trading-system-repos/.uv-cache` is being pruned on any schedule (a shared cache across 16 slots
can grow unbounded if not), (2) whether per-slot `.venv` dirs could be more aggressively cleaned between tasks, (3)
whether a disk-usage alert/threshold should exist alongside the QG-governor's memory-pressure awareness. Not escalating
as P0/P1 since it self-recovered and did not (as far as I can tell) cause permanent data loss — but two independent
host-capacity symptoms (CPU/token queue contention + disk-full) surfacing in the same session on the same host is worth
someone connecting the dots on overall host sizing vs current fleet size.

## Todos

- [ ] [INFRA] P2. Check whether `.uv-cache` / per-slot `.venv` growth is unbounded and needs a prune schedule; connect
      to the QG-governor contention finding for an overall host-capacity review. (repo: infra/host config)

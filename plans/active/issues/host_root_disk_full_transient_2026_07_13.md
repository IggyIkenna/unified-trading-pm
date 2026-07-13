---
doc_type: issue
title: Host root disk hit 100% full (0 bytes free) TWICE in one session — recurring, not transient
summary: |
  While running quality-gates.sh for unified-trading-api, the shared host's root filesystem (290G, holds
  /home/ubuntu/unified-trading-system-repos across all 16 slots) hit 100% full — 0 bytes available, breaking `uv sync`
  (`No space left on device`) and the Claude Code harness's own tmpdir output capture. Self-recovered to 96% (13G free)
  ~2 minutes later, unattended. Recurred ~1 hour later, same session, same host — `df -h /` back to 100%/12M free,
  breaking `bash scripts/setup.sh` for execution-service (`uv pip install -e .` editable-install failure). Two
  independent full-disk events in one session upgrades this from "self-recovered blip" to "recurring capacity
  problem" — retitled + reprioritized accordingly.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, disk-space, host-contention, capacity, recurring]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
source: [unified_trading_api_pip_audit_stale_ignore_list-001 -- observed while shipping the dependency fix]
related: [plans/active/issues/qg_host_governor_severe_contention_2026_07_13.md]
depends_on: []
---

# Host root disk hit 100% full TWICE in one session — recurring, not transient

## Recurrence (2026-07-13, ~1hr after first occurrence)

`df -h /` again showed `290G 290G 12M 100% /` while trying `bash scripts/setup.sh` for execution-service (to run its
health-endpoint tests as part of `utl_reuse_phase6_venue_health_retry` VERIFY work). `uv pip install -e .` failed at
"Project editable install failed". Same host, same session, same symptom class as the first occurrence below — this is
NOT a one-off. Between the two events, disk was observed oscillating in the 96%-99% range (checked repeatedly while
separately waiting on `qg-host-governor` queue timers), so the host appears to be running close to full most of the
time, with occasional excursions to literal 100%/0-bytes-free rather than a single anomalous spike.

## What I found (first occurrence)

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
whether a disk-usage alert/threshold should exist alongside the QG-governor's memory-pressure awareness. **Upgraded to
P1** after the recurrence — a host oscillating between 96-100% full for an extended period (not a single anomalous
spike) means any of the 16 slots can hit this at any moment, and it silently blocks routine work (`uv sync`,
`scripts/setup.sh`, coverage writes) with a confusing error surface (looks like a dependency/tooling bug until `df -h`
is checked). Two independent host-capacity symptoms (CPU/token queue contention + disk-full) surfacing repeatedly in one
session on one host is worth someone connecting the dots on overall host sizing vs current fleet size (16 slots × ~24
repo clones each appears to be the actual driver, per the ~219G `unified-trading-system-repos` footprint noted above).

## Todos

- [ ] [INFRA] P1. Check whether `.uv-cache` / per-slot `.venv` growth is unbounded and needs a prune schedule; connect
      to the QG-governor contention finding for an overall host-capacity review. Given the recurrence, also consider
      whether a per-slot disk-usage cap or an automated `.venv`/cache prune cron is warranted, not just a one-time
      cleanup. (repo: infra/host config)

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
assigned_vm: NA
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

- [x] ✅ [INFRA] P1. Check whether `.uv-cache` / per-slot `.venv` growth is unbounded and needs a prune schedule;
      connect to the QG-governor contention finding for an overall host-capacity review. Given the recurrence, also
      consider whether a per-slot disk-usage cap or an automated `.venv`/cache prune cron is warranted, not just a
      one-time cleanup. (repo: infra/host config) — **INVESTIGATED + PARTIALLY FIXED, slot 11, 2026-07-13**:
      `unified-trading-pm@9dcd37631`. - **Confirmed root driver #1 (shared, safe to fix)**: `.uv-cache` (12G) had NO
      prune schedule at all (no crontab entry, no systemd timer). A single manual `uv cache prune` (no `--force` —
      respects in-use checks) reclaimed **5.7GiB in ~3s**. Shipped `scripts/dev/prune-uv-cache.sh` + idempotent per-host
      installer `scripts/dev/install-prune-uv-cache-cron.sh` (6h default cadence), mirroring the existing
      `cleanup-stale-qg-tmp.sh` convention exactly. **NOT yet actually scheduled** — could not self-install from this
      sandboxed slot session (`crontab -l`/`-e` both hit `Permission denied` for this user on this host); an operator or
      a root-capable agent needs to run `bash unified-trading-pm/scripts/dev/install-prune-uv-cache-cron.sh` once. -
      **Confirmed root driver #2 (larger, NOT fixed — live data)**: per-slot `.venv` dirs are the dominant consumer,
      ~150-200G summed across the 16 slots (1.3-2.6G per heavy repo × ~5-6 heavy repos × 16 slots).
      `UV_LINK_MODE=hardlink` IS configured (`base-service.sh:322`) but is NOT actually deduping across slots — verified
      by comparing the same `numpy.libs/libscipy_openblas64_*.so` file across two different slots' `.venv`s: identical
      content/size, but `nlink=1` on both with DIFFERENT inodes (not hardlinked to each other). Root cause of the
      non-dedup not investigated further this dispatch (candidate: each slot's `uv sync` may resolve to a distinct cache
      entry, or hardlink only applies within a single sync's own cache→venv copy, not across independently-run syncs).
      Did NOT touch any slot's `.venv` — these are live, in-use directories; a blanket prune risks breaking an active
      slot's `quality-gates.sh`/`quickmerge.sh` mid-run (same "never overwrite live foreign WIP without a liveness
      check" principle as `features_sports_parallel_backfill_vm_name_collision_2026_07_13.md`'s VM-name-collision
      fix). - **Follow-on todos** (not done this dispatch, out of single-worker scope): (a) operator runs the cron
      installer above; (b) investigate why `UV_LINK_MODE=hardlink` isn't deduping across slots — if fixable, the
      150-200G `.venv` footprint could shrink dramatically for free; (c) if hardlink-dedup can't be made to work
      cross-slot, a liveness-aware per-slot `.venv` prune (idle-slot detection, same pattern as the VM-collision guard)
      is the real fix for driver #2, not a blanket cron.

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
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, shared-host, tmpfs, disk-space, pytest, quality-gates, flaky-tests]
related: [plans/archive/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md]
source:
  Found while running agent-orchestrator's quality-gates.sh to validate the sharded ag-closeout-audit dispatch change
  (plans/active/ag_closeout_audit_rollout_2026_07_25.md Round 6) — ~35 unrelated test failures traced to shared-host
  /tmp exhaustion, not a real regression.
created: 2026-07-26
resolved_by:
  "unified-trading-pm@594d79031c7b8b185413eaa26867af8e03e53755 (new cleanup-stale-claude-session-tmp.sh +
  install-cleanup-stale-claude-session-tmp-cron.sh, closing the gap the 2026-07-08 fix left open) + registering both
  crons live on the human-planning VM (52.194.240.144). Standing operator decision from 2026-07-08 not to resize the
  tmpfs is unchanged/out of scope — see Progress Log."
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
depends_on: []
---

# Shared host `/tmp` tmpfs exhaustion — spurious test failures

> **🟢 RESOLVED 2026-07-26 — ACKED-INTO-CODE** — `unified-trading-pm@594d79031c7b8b185413eaa26867af8e03e53755`
> (cleanup-stale-claude-session-tmp cron shipped + registered live); archived per the terminal-status backlog sweep.

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

- [x] ✅ [OPERATOR] P2. **Decide whether to grow the host's `/tmp` tmpfs size** (`mount -o remount,size=<bigger>` +
      persist in `/etc/fstab`) or leave it and rely on `TMPDIR` overrides / periodic scratch cleanup across slots.
      Growing tmpfs eats into the same RAM the host's other processes use, so this is a real tradeoff, not a free win —
      needs the operator's judgment on this host's memory headroom. **Done when**: either the tmpfs size is bumped and
      confirmed to have real memory headroom behind it, or this item is explicitly closed as "leave as-is, use TMPDIR
      when it bites." — **Resolved: leave as-is, no host-level tmpfs resize** (2026-07-26, same standing operator
      decision as the 2026-07-08 incident's identical P3 item — a shared-VM mount resize is irreversible-adjacent
      shared-infra config not self-authorized by an agent; explicitly out of scope for this fix per the operator's task
      instructions). The recurrence wasn't caused by insufficient tmpfs headroom — it was caused by a coverage gap in
      the 2026-07-08 belt-and-suspenders cleanup cron (see Progress Log), which is now closed.

## Progress Log

- **2026-07-26** — Root-caused why this recurred despite the 2026-07-08 fix
  (`plans/archive/issues/shared_host_tmp_tmpfs_exhaustion_2026_07_08.md`): that incident's
  `scripts/dev/cleanup-stale-qg-tmp.sh` cron only ever swept `${HOME}/.cache/qg-tmp/pytest-of-*` + legacy
  `/tmp/pytest-of-*` — it never covered the Claude Code harness's OWN per-session scratch under
  `/tmp/claude-<uid>/<project-slug>/<session-id>/{scratchpad,tasks}`, which is what actually filled the tmpfs both times
  (measured 1.8G / 463M across 363 session dirs on this host, 294 of them >24h old, at the time of investigation). Also
  confirmed via `crontab -l` that the 2026-07-08 cron itself had never been registered on this host — its own doc left
  registration "to the operator to run once per host," and nobody had.
  - **Registered the existing `cleanup-stale-qg-tmp` cron** (was missing entirely):
    `bash scripts/dev/install-cleanup-stale-qg-tmp-cron.sh` — hourly sweep of pytest/QG scratch, `fuser`-liveness-gated.
    Confirmed firing correctly post-install (8 real runs logged, 2 stale dirs actually removed) despite the installer's
    default `INTERVAL=60` producing non-canonical `*/60 * * * *` cron syntax (minute-field step must be ≤59) — Ubuntu
    24.04's `cron` 3.0pl1 clamps this to firing once at minute 0, so it behaves as intended (hourly) in practice, but
    `crontab -` now warns on it (`Step size 60 higher than possible maximum of 59`) on write. Left as-is (pre-existing
    script, out of this fix's scope, and functionally correct) — worth a follow-up cosmetic fix to `0 * * * *` if anyone
    touches that installer again, but not urgent.
  - **Built the sibling fix**: `scripts/dev/cleanup-stale-claude-session-tmp.sh` (sweeps
    `/tmp/claude-$(id -u)/*/<session-id>/` at `-mindepth 2 -maxdepth 2`, confirmed against the real on-host layout
    before writing the glob) + `scripts/dev/install-cleanup-stale-claude-session-tmp-cron.sh` — mirrors
    `cleanup-stale-qg-tmp.sh`'s `is_in_use()` fuser/lsof liveness check near-verbatim (a session can be idle-but-alive
    for hours during a long background wait, so mtime-only staleness is not a safe sole gate), same
    `--min-age`/`--dry-run`/`--quiet` flags, same idempotent marker-line cron install/uninstall convention, same
    root/`.tabs`-worktree guards, self-pull via `cron-self-pull-lib.sh`, per-uid log file under
    `${XDG_RUNTIME_DIR:-/tmp}`. Default interval 30 min (shorter than QG's 60 — this is a harness-wide concern covering
    every slot's sessions, not just QG-run scratch, and the 2026-07-26 incident showed the tmpfs can fill within a
    single working session) with a 180-min (3h) staleness threshold as defense-in-depth alongside the liveness check,
    not the primary safety mechanism — long enough that a genuinely idle-but-alive session (dispatched sub-agent, VM
    watch, `ScheduleWakeup`) is never at risk. Also fixed a real bug found while building the sibling (mirrored into
    `cleanup-stale-qg-tmp.sh` too): `find ... | xargs -r fuser` returns 0 (success) on empty stdin, which made an empty
    directory look "in use" on every call — measured a 344/363 false-positive skip rate on this host before the fix
    (collect matches into an array first, only invoke `fuser` when non-empty).
  - Both scripts `--dry-run`-verified against this host's real state before installing anything live, then both crons
    registered. Ran the real (non-dry-run) cleanup once by hand to relieve the then-current pressure immediately
    (liveness-gated, same as the cron would do).
  - Shipped `scripts/dev/cleanup-stale-claude-session-tmp.sh` +
    `scripts/dev/install-cleanup-stale-claude-session-tmp-cron.sh` + the `cleanup-stale-qg-tmp.sh` fuser fix via
    `quickmerge.sh --agent` — blocked once by an unrelated concurrent `plan-discipline` QG regression on
    `plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md` (a false positive: quoted `"DEFERRED — ..."` prose
    describing another doc's annotation, inside a legitimate `## Deferred — conflict-gated` triage section, tripped the
    `_DEFERRED_RE` no-migration-banner check). Confirmed this was independently root-caused and fixed by another
    concurrent session (`check_plan_discipline.py`@6c36b4c61, quote-exclusion logic + archived issue doc
    `plan_discipline_quoted_deferred_false_positive_2026_07_26.md`) before I re-attempted — pulled the fix in (133
    commits behind at that point, shared branch under heavy concurrent load) and re-shipped clean. Landed:
    `unified-trading-pm@594d79031c7b8b185413eaa26867af8e03e53755`.
  - Pulled the shipped commit on the human-planning VM's root clone
    (`/home/ubuntu/unified-trading-system-repos/unified-trading-pm`, 52.194.240.144) and ran the new installer there.
    Both crons confirmed active via `crontab -l`:
    ```
    */60 * * * * ... cleanup-stale-qg-tmp.sh --min-age 60 --quiet ... # cleanup-stale-qg-tmp
    */30 * * * * ... cleanup-stale-claude-session-tmp.sh --min-age 180 --quiet ... # cleanup-stale-claude-session-tmp
    ```
    Post-fix `/tmp` state on that host: `tmpfs 2.0G 540M 1.5G 27%` (`/tmp/claude-1000` at 463M, down from the
    1.8G/2GB-full state that triggered this doc).

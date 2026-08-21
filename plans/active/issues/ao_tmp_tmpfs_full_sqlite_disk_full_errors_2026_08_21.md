---
doc_type: issue
title: >-
  Orchestrator VM's /tmp tmpfs is 100% full (8GB cap, 42MB avail) — causing live
  "sqlite3.OperationalError: database or disk is full" errors; root filesystem itself is healthy (82%, 127GB free)
summary: >-
  Discovered 2026-08-21 while verifying a service restart landed clean: `journalctl` showed a live
  `sqlite3.OperationalError: database or disk is full` (confirmed causing at least one real 500,
  `GET /api/accounts/deepseek/wallet-reconciliation`). The dashboard's Host Resources panel shows "Disk 81%
  (550.1GB/677.0GB)" and 93% I/O Wait, which reads like the root disk is the problem — it is NOT. `df -h` on the VM
  shows `/dev/root` (the actual 678GB disk the dashboard is measuring) at 82% with 127GB free — genuinely healthy.
  The real culprit is `/tmp`, a SEPARATE 8GB tmpfs (RAM-backed) mount, at 100% (`8.0G 8.0G 42M 100% /tmp`). SQLite
  writes temp journal/rollback files to `/tmp` by default, so a full `/tmp` produces "disk full" errors regardless of
  how much room the real disk has. NOT investigated further this session (found during a pre-compact checkpoint,
  deliberately not chased down per the operator's own instruction to checkpoint rather than start new work) — this
  doc exists so the finding isn't lost, not because the fix is done.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, disk, tmpfs, sqlite, incident, p0]
related:
  [
    /codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md,
    /plans/active/issues/ao_crash_loop_zero_alerting_and_grok_proxy_health_2026_08_20.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md,
    /plans/active/issues/ao_crash_loop_zero_alerting_and_grok_proxy_health_2026_08_20.md,
  ]
source: >-
  Interactive session, 2026-08-21 — found while confirming a code-push-triggered orchestrator.service restart landed
  clean; the operator independently noticed the dashboard's Host Resources panel (Disk 81%, I/O Wait 93%) at the same
  time and asked about it, which is what prompted the deeper `df -h` check that found the real (different) culprit.
---

# /tmp tmpfs full — live SQLite "disk full" errors, root disk itself is healthy

## Live evidence (2026-08-21, read-only SSM)

```
Filesystem       Size  Used Avail Use% Mounted on
/dev/root        678G  551G  127G  82% /
tmpfs            8.0G  8.0G   42M 100% /tmp        <-- this one
```

`journalctl -u orchestrator.service` shows a real, live failure caused by this:

```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database or disk is full
...
GET /api/accounts/deepseek/wallet-reconciliation HTTP/1.1" 500 Internal Server Error
```

The dashboard's Host Resources panel ("Disk 81%, 550.1GB/677.0GB", "I/O Wait 93%") is reading the ROOT filesystem
(`/dev/root`), which genuinely has 127GB free — it is not the cause and not itself alarming on its own. The 93% I/O
Wait figure is a real, separate signal worth understanding (heavy disk contention from *something*), but is not yet
tied to the `/tmp` fullness with direct evidence — noted, not conflated.

## Why this matters

SQLite's default temp-store behavior writes rollback-journal/temp b-tree files to the OS temp directory. A `/tmp`
at 100% capacity makes those writes fail, surfacing as `database or disk is full` on ANY SQLite write path
regardless of the real database file's own size or the disk's real free space — this can affect any endpoint that
touches the orchestrator's state.db, not just the one caught live here.

## Resolution (2026-08-21)

Root cause identified precisely: `codex-bridge.service` (`PrivateTmp=yes`, a Codex/Luna-backed agent bridge running
real `quickmerge --isolated`/`prek`/QG operations for its child agent sessions) had accumulated its ENTIRE 8G tmpfs
into its own isolated `systemd-private-*/tmp` namespace — 17895 files, zero reaped in the unit's 18h uptime, because
the existing `cleanup-stale-tmp-parquet-scratch.sh` reaper cron had no visibility into that namespace at all (a
different offender class from the original enum-univ-*/cefi-corrector-* parquet pattern this doc/script already
handled). Confirmed via `fuser`-liveness-check that the largest offenders (~2.6G) had zero open handles — genuinely
orphaned scratch from already-exited quickmerge/prek/QG runs, the same "SIGKILLed run's `finally: unlink()` never
ran" failure class already documented above, just hidden behind a mount namespace.

Fix shipped (`unified-trading-pm@29690daebd`, in flight to origin): a second, name-unrestricted, liveness-gated sweep
in the same reaper script for any discovered `systemd-private-*/tmp` root. Discovered mid-implementation that the
outer `systemd-private-*` dir is `drwx------ root:root` — the existing operator-user cron structurally cannot see
into it (confirmed empty result running the sweep as `ubuntu` vs. full visibility as root over SSM) — so this needed
a NEW root-owned systemd timer (`tmp-privatetmp-reaper.service` + `.timer`, 15min cadence), not an extension of the
existing operator crontab. Deployed live and verified working: `/tmp` dropped from 100% (8.0G/8.0G, 19M avail) to
71% (5.7G/8.0G, 2.4G avail) mid-sweep, liveness-gate confirmed correctly skipping in-use files (0 false removals in
the journal), zero interference with codex-bridge.service itself (never restarted, never touched while live).
Codex-SSOT updated in the same commit: `/codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md`.

## Not yet done

- [x] [INFRA] P0. Identify what's actually filling the 8GB `/tmp` tmpfs and clear/rotate it — see Resolution above.
- [ ] [INFRA] P1. Once cleared, decide whether 8GB is simply undersized for this host's real tmpfs usage (raise the
      cap) or whether something is genuinely leaking/not cleaning up after itself into `/tmp` (fix the leak) —
      don't just clear it once and let it silently refill. Partially addressed by the sub-hourly root timer above,
      but the underlying question (should `codex-bridge.service` even have `PrivateTmp=yes`, given it now needs a
      second privileged reaper to compensate for the isolation it creates?) is still open.
- [ ] [INFRA] P2. Commit the new `tmp-privatetmp-reaper.service`/`.timer` unit files + an install script into
      agent-orchestrator (matching the existing `codex-bridge.service` checked-in-unit-file pattern) so this is
      reproducible/version-controlled rather than a hand-deployed VM snowflake — currently only live via direct SSM
      deployment, not yet source-controlled.
- [ ] [INFRA] P2. Investigate the 93% I/O Wait figure separately — confirm whether it's related to this `/tmp`
      pressure or a distinct signal (e.g. concurrent QG/pytest activity from multiple sessions on this shared host,
      per the same-day findings in `agent_orchestrator_pytest_cov_silent_death_under_host_load_2026_08_20.md` and
      `agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md`).
- [ ] [INFRA] P2. Consider whether `orchestrator.service`'s SQLite connection should set `PRAGMA temp_store=MEMORY`
      or point `SQLITE_TMPDIR`/`TMPDIR` at a location with more headroom than the shared 8GB `/tmp`, so this class of
      failure can't recur even if `/tmp` fills again for an unrelated reason.

## Progress Log

- **2026-08-21**: doc authored during a pre-compact checkpoint. Found while verifying a routine service restart;
  the operator independently flagged the dashboard's disk panel at the same moment, which is what prompted checking
  `df -h` directly rather than trusting the panel's single "Disk" number.
- **2026-08-21 (later same day)**: root cause pinned down precisely (codex-bridge.service's `PrivateTmp` namespace,
  not the originally-suspected instruments-service parquet class), fix designed + implemented + shipped
  (`unified-trading-pm@29690daebd`), and deployed live. Mid-implementation discovery changed the fix's shape: the
  operator-user cron cannot reach `PrivateTmp` dirs at all (root:root 0700 permissions), so this needed a new
  root-owned systemd timer rather than an extension of the existing crontab reaper — verified via a failed dry-run
  test as `ubuntu` before building the correct root-privileged mechanism, per the operator's explicit choice.
  Mid-flight, a peer session's automated `git reset` to origin (this is a shared checkout — see
  `/codex/05-infrastructure/per-tab-worktrees.md`) discarded the uncommitted edits once; recovered by reconstructing
  from conversation context and committing immediately. Live-verified: `/tmp` 100%→71% used mid-sweep, zero false
  removals (liveness-gate held), codex-bridge.service itself never touched/restarted throughout.

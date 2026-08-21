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

## Not yet done (deliberately — found during a checkpoint, not chased down)

- [ ] [INFRA] P0. Identify what's actually filling the 8GB `/tmp` tmpfs (`du -sh /tmp/* | sort -rh`, live on the VM)
      and clear/rotate whatever's accumulating there. Check `/codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md`
      first — this workspace already has documented conventions for exactly this class of problem (a `$HOME/.cache/*`
      pattern as the mitigation for scripts that would otherwise dump into `/tmp`); read it before improvising a fix.
      (repo: agent-orchestrator, or infra-level if this is host-wide)
- [ ] [INFRA] P1. Once cleared, decide whether 8GB is simply undersized for this host's real tmpfs usage (raise the
      cap) or whether something is genuinely leaking/not cleaning up after itself into `/tmp` (fix the leak) —
      don't just clear it once and let it silently refill.
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

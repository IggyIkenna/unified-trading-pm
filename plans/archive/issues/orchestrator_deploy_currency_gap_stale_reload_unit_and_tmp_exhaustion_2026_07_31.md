---
doc_type: issue
title: >-
  Deployed orchestrator.service systemd unit was 9 days stale (still running --reload) because ao-self-pull.sh's 15-min
  cron only re-syncs application code, never the unit file itself — compounded a same-day host-memory outage; fixed
  live, and a fully-exhausted /tmp was found + cleared along the way
summary: >-
  While diagnosing an operator report of agent-orchestrator being down 15+ minutes, live on-host investigation found a
  runaway instructions-service script (PID 1033055) pinned host + cgroup memory (killed; the script-side root cause and
  fix are tracked separately in expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md — NOT duplicated here).
  This doc covers two DISTINCT findings surfaced during that same investigation that no other doc covers: (1) the
  deployed /etc/systemd/system/orchestrator.service was 9 days stale and still ran uvicorn with --reload, even though
  the repo's SSOT unit file had --reload removed on 2026-07-30 specifically to fix a prior stuck-shutdown hang — because
  ao-self-pull.sh's 15-min cron restarts the orchestrator process on every app-code change but never re-syncs the
  systemd unit file itself, so a unit-file-only fix can silently never reach production no matter how many restarts
  happen (confirmed: two cron-triggered restarts on 2026-07-31 alone, both still launched with the stale --reload flag).
  Fixed live via install-orchestrator-service.sh --restart. (2) /tmp (a 2GB tmpfs) was found 100% full, independently
  capable of breaking tmux worker-spawn, from two orphaned files (1.1G stale parquet + 453M interrupted GCS upload)
  unrelated to any tracked epic — cleared live.
status: resolved # (was: open) 2026-07-31 -- both todos done live, agent-orchestrator@90a2b2f + /tmp 2G->8G on-host
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, incident, systemd, deploy-currency, reload, tmp-exhaustion, self-pull, outage, shared-host]
related:
  [
    /plans/active/issues/expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md,
    /plans/active/issues/orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30.md,
    /plans/archive/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md,
    /plans/archive/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-31
last_updated: 2026-07-31
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Discovered live on the orchestrator VM (ip-172-31-5-118) via an interactive Claude Code session with direct host
  access, in response to an operator report ("agent-orchestrator down 15+ min").
resolved_by: agent-orchestrator@90a2b2f (unit-file self-heal; /tmp 2G->8G was a live host fstab edit, no commit)
locked_by:
locked_since:
---

# orchestrator.service deploy-currency gap (stale systemd unit) + /tmp exhaustion — both fixed live

## What's confirmed

1. **Trigger (tracked separately, not duplicated here)**: a runaway `instruments-service` script (PID 1033055,
   `scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py`, slot 16) grew to 43.6GB RSS (67% of host RAM) over
   ~37min, starving the host and the `orchestrator.service` cgroup (`MemoryAvailable: 0B`, swap 15.9G/16G maxed). Killed
   via `SIGTERM` (clean exit, no `SIGKILL` needed) ~2026-07-31T12:24Z by the operator (interactive session, this doc's
   author) after confirming via `fuser`/`lsof`/`ps` it was the dominant memory consumer and not held open by anything
   besides its own process tree. **This is a different PID than the one in the sibling script-bug doc**
   (`expand_defi_pool_catalogue_script_unbounded_memory_2026_07_31.md` — PID 2108132, killed independently by review
   ~30-40min later) — at least two separate blow-ups of the same then-unfixed script occurred inside one hour. See that
   doc for the script-side root cause (unfiltered wide manifest read + a lingering non-daemon thread) and its fix
   (column-pruned read + `os._exit()`), already shipped and verified working — not repeated here.
2. **API outage, live-confirmed**: while memory was pinned, `curl localhost:8765/api/mode` returned `HTTP:000` even at a
   20s timeout, and the journal showed a live `sqlite3.OperationalError: database is locked` on `BEGIN IMMEDIATE` inside
   a `multiprocessing.spawn` child of uvicorn's `--reload` supervisor (PID 3549762) — the same
   write-lock-under-memory-pressure class as `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` /
   `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md`. Killing PID 1033055 alone recovered the API within
   ~1 minute (host RAM 50G→11G used, orchestrator cgroup 0B→43G available, `/api/mode`/`/api/backlog` back to `HTTP:200`
   in single-digit milliseconds).
3. **Root-cause-adjacent finding: the deployed systemd unit was 9 days stale.**
   `/etc/systemd/system/orchestrator.service` (mtime `2026-07-21`) was still running `--reload --reload-dir server` —
   confirmed three independent ways: the live process's `/proc/<pid>/cmdline`, `systemctl cat orchestrator`'s merged
   view, and the deployed unit file itself. The repo's SSOT (`scripts/orchestrator.service`) had `--reload` REMOVED on
   `2026-07-30` (commit `ee98ccb`, `fix(deploy): remove redundant uvicorn --reload from orchestrator.service`)
   specifically because this exact reload-supervisor + `multiprocessing.spawn` child layer was already implicated in a
   prior stuck-shutdown hang (per the unit file's own comment, citing
   `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` P2). That fix never reached this VM.
4. **Why it never reached this VM — the actual gap.** `scripts/ao-self-pull.sh` (root crontab, `*/15 * * * *`) FF-pulls
   the `agent-orchestrator` **application-code checkout** and runs `systemctl restart orchestrator` when HEAD moves (or
   the running process predates HEAD) — and it does this correctly: log evidence shows it restarted the orchestrator
   TWICE on 2026-07-31 alone (`10:15:01` on a code FF, `10:30:01` on the stale-process guard), both logged
   `active=active`. But `systemctl restart` reuses whatever's ALREADY INSTALLED at
   `/etc/systemd/system/orchestrator.service` — `ao-self-pull.sh` never copies `scripts/orchestrator.service` into place
   and never runs `daemon-reload`; that sync only happens via the separate `install-orchestrator-service.sh`, which the
   cron never calls. So the app-code deploy-currency mechanism (the whole point of `ao-self-pull.sh`, per its own header
   comment about the 2026-06-01 "vm-2 was 14 commits behind" incident) works, but has no equivalent for the **systemd
   unit file** itself — a unit-file-only change can silently never take effect no matter how many times the cron
   restarts the process. Confirmed empirically: both of today's cron-triggered restarts (10:15, 10:30) launched the
   process with the stale `--reload` flag.
5. **Separate, unrelated finding surfaced while applying the fix**: mid-way through applying the unit-file fix,
   `install-orchestrator-service.sh --dry-run` failed with `pwd: write error: No space left on device`. Investigation
   found `/tmp` (a 2GB tmpfs) at 100% used (12K available) — independently capable of breaking tmux worker-spawn per the
   unit file's own `ReadWritePaths=/tmp` comment ("CRITICAL for worker spawning"), and unrelated to the memory incident
   above. Root cause: two orphaned files, neither held open by any process (`fuser`/`lsof` both empty) —
   `/tmp/mtds_defi_index.parquet` (1.1G, stale since `08:33Z`) and `/tmp/availability_index.parquet_.gstmp` (453M, an
   interrupted/orphaned GCS upload, stale since `11:12Z`) — leftovers from unrelated ad-hoc script runs on the shared
   host, nothing to do with any currently-tracked epic.

## Fix applied (2026-07-31, this session, live)

1. Killed PID 1033055 (`SIGTERM`, clean exit) — API recovered within ~1 min, confirmed via `/api/mode`/`/api/backlog`
   returning `HTTP:200` and a clean journal (no further `database is locked`).
2. Removed the two orphaned `/tmp` files (confirmed unheld first) — `/tmp` back to 27% used / 1.5G free.
3. Ran `bash scripts/install-orchestrator-service.sh --operator ubuntu --restart` — installs the current SSOT unit
   (drops `--reload`), runs `daemon-reload`, clean restart. Verified three ways post-restart: new deployed unit mtime
   `12:48:15Z`, new live process (`PID 2042809`) confirmed via `/proc/<pid>/cmdline` to have no `--reload`,
   `NRestarts=0`/`ActiveState=active`/`SubState=running`.
4. Sent a live operator directive to slot 16 (`POST /api/slots/16/message`) about the script-side memory risk —
   superseded by slot 16's own independent root-cause + fix, tracked in the sibling doc referenced above.
5. **[BACKEND] P1 (below) shipped**: `agent-orchestrator@90a2b2f` extends `ao-self-pull.sh` to also run
   `install-orchestrator-service.sh --operator ubuntu --restart` unconditionally every tick, after the existing
   code-pull/restart logic. That install script was already idempotent (diffs the rendered SSOT against the installed
   unit, no-ops loudly when identical, only restarts when it actually applies a change) — no new diff-detection logic
   needed, just wiring the existing self-heal-capable command into the cron loop. **Verified end-to-end, live, twice**:
   reintroduced `--reload` into the deployed unit file only (simulating the exact drift this doc describes), then ran
   the full `ao-self-pull.sh` exactly as root's crontab invokes it
   (`sudo ORCHESTRATOR_VM_ID=planning ORCHESTRATOR_VM_ROLE=planning bash scripts/ao-self-pull.sh`) — both times it
   detected the drift, reinstalled the correct unit, and restarted cleanly within the same tick, with the live process
   (`/proc/<pid>/cmdline`) and `/api/mode` confirmed healthy afterward. First test done in isolation before the commit;
   second test run against the real committed code via the actual cron entrypoint, clean tree, no manual intervention
   beyond simulating the drift.

## What is NOT yet done

- [x] ✅ [BACKEND] P1. **DONE 2026-07-31, `agent-orchestrator@90a2b2f`.** See "Fix applied" item 5 above for the shipped
      diff + live end-to-end verification (drift simulated twice, self-healed within one tick both times via the real
      cron entrypoint, API confirmed healthy after each).
- [x] ✅ [REVIEW] P3. **DONE 2026-07-31 — operator ruling: size bump only** (asked via a scoped question rather than
      picking a direction unilaterally, since this todo was an open "consider whether" call, not a bounded spec; a
      standing cleanup sweep was explicitly declined). Bumped `/tmp` from 2G→8G on this VM: `/etc/fstab`'s
      `tmpfs /tmp tmpfs ... size=2G ...` → `size=8G`, applied live via `mount -o remount,size=8G /tmp` (no unmount, no
      disruption to open files) — confirmed `df -h /tmp` → `8.0G size, 6.1G avail`. **Deliberately did NOT touch**
      `bootstrap_vm.sh`'s fleet-wide `TMP_TMPFS_SIZE:-2G` default: that script bootstraps the whole VM fleet, including
      16GB worker VMs where the existing comment ("2G is safe on the 16G fleet VMs") is a real, still-valid constraint
      an 8G default would violate — this incident's evidence (a 43.6GB-RSS runaway process, a 42GB gap between the old
      2G cap and this 64GB central orchestrator VM's actual headroom) doesn't generalize to the smaller fleet. **Durable
      without a code change**: `bootstrap_vm.sh` Step 7.6's own idempotency check
      (`grep -qE '^tmpfs /tmp tmpfs' /etc/fstab`) only writes the fstab line when ABSENT — since one now exists (at 8G),
      a future re-bootstrap of this VM will log "already present" and leave it untouched; only a from-scratch rebuild
      (empty `/etc/fstab`) would regress to the 2G fleet default, a known, accepted, low-probability residual (this VM
      has run continuously since its 2026-07-29 resize, no rebuild in its history).

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` documents `ao-self-pull.sh`'s app-code
  deploy-currency role but not this unit-file gap. If the `[BACKEND] P1` todo ships, add a short note there mirroring
  how the memory-cap rescale mechanism is (or should be) documented.

## Progress Log

- **2026-07-31 (interactive operator session)**: full outage-to-recovery cycle executed live on-host in response to an
  operator report ("agent-orchestrator down 15+ min"). See "Fix applied" above for exact evidence per step. Both
  findings in this doc (stale unit, full `/tmp`) are fixed as of this session; the `[BACKEND] P1` durable-fix todo and
  the `[REVIEW] P3` monitoring todo remain open.
- **2026-07-31 (same session, follow-up)**: closed `[BACKEND] P1` — `agent-orchestrator@90a2b2f`, live end-to-end
  verified twice (drift simulated, self-healed within one cron tick both times, API confirmed healthy after each).
  `[REVIEW] P3` (`/tmp` sizing/monitoring) intentionally left open — it's an explicit "consider whether" judgment call
  per its own todo text, not a bounded fix; routing to the operator rather than picking a direction unilaterally.
- **2026-07-31 (same session, second follow-up)**: operator chose "size bump only" for `[REVIEW] P3`. Closed — `/tmp`
  bumped 2G→8G live on this VM (fstab + live remount, no restart/disruption), durable via `bootstrap_vm.sh`'s existing
  idempotency (won't overwrite an already-present fstab line), fleet-wide default deliberately left untouched (see todo
  for the 16GB-worker-VM rationale). Both todos in this doc are now closed; doc has no remaining open work.

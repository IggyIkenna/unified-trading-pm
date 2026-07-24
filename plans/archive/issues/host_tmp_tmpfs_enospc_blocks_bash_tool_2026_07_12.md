---
doc_type: issue
title: Host /tmp tmpfs full (0 bytes free) — blocks the Bash tool fleet-wide for every slot
summary: >-
  The shared /tmp tmpfs (2.0GB, mounted the same across every .tabs/<N> slot) hit 100% used / 0 bytes free at
  approximately 2026-07-12 08:1x UTC. The Bash tool's own per-command output-capture path writes into
  /tmp/claude-1000/<session>/tasks/, which needs headroom even for a zero-stdout command — every Bash invocation now
  fails with ENOSPC, including no-op commands (`true`, `:`, `echo`). This blocks git commit/push, quickmerge, and every
  orchestrator-API curl call for any affected slot, not just the one that discovers it.
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [infrastructure, disk-space, tmpfs, enospc, bash-tool, fleet-wide]
related:
  [
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
    plans/active/issues/sports_manifest_consolidator_duckdb_crash_and_silent_empty_read_2026_07_12.md,
  ]
created: 2026-07-12
parent_epic: infrastructure_master
priority: P0
source: [slot-6, sports_p2_history_reference_and_odds_2015_to_present-002]
assigned_vm: planning
resolved_by: [slot-12, slot-6, slot-7, slot-8]
resolved: "2026-07-12 (corrected 2026-07-15, plan-reconcile: all 3 todos + Progress Log show full closure)"
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Host /tmp tmpfs full — blocks the Bash tool fleet-wide

## What I found

While working `sports_p2_history_reference_and_odds_2015_to_present-002` (item #6 gate re-verify) in slot 6, every
`Bash` tool call started failing with:

```
Command output was lost: the temp filesystem at
/tmp/claude-1000/-home-ubuntu-unified-trading-system-repos--tabs-6/<session>/tasks is full (0MB free). The child
process's stdout/stderr writes failed with ENOSPC. Free up space or set CLAUDE_CODE_TMPDIR to a directory on a
filesystem with room.
```

This started mid-session (earlier commands in the same session, including two Python scripts that printed real output,
succeeded normally) and has NOT been transient — retried several times over a few minutes, including trivial no-op
commands (`true`, `:`, `echo r`) that produce almost no stdout, all still fail identically.

`df -h` (captured once, before the outage fully hit, by redirecting output to a file on `/home` instead of letting the
harness capture it) showed:

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       290G  239G   51G  83% /
tmpfs           2.0G  2.0G   32K 100% /tmp
/dev/root       290G  239G   51G  83% /home
```

`/tmp` is a 2.0GB tmpfs, shared across every `.tabs/<N>` slot on this host (NOT per-slot). `du -sh /tmp/claude-1000/*/`
(also redirected to `/home`, not captured normally) showed usage was NOT evenly distributed — a few slot directories
dominate:

| directory                                                            | size                |
| -------------------------------------------------------------------- | ------------------- |
| `.../unified-trading-system-repos--tabs-3/`                          | 215M                |
| `.../unified-trading-system-repos/` (unscoped, no `--tabs-N` suffix) | 409M                |
| `.../unified-trading-system-repos--tabs-9/`                          | 109M                |
| `.../unified-trading-system-repos--tabs-5/`                          | 121M                |
| `.../unified-trading-system-repos--tabs-6/` (this slot)              | 89M                 |
| (all other slots)                                                    | each well under 10M |

Root filesystem (`/`, `/home`) has 51G free — this is NOT a general host-disk-space problem, it's specifically the 2.0GB
`tmpfs` mount at `/tmp` being exhausted, most likely by accumulated subagent-transcript / task-output files across many
concurrent sessions (matches the historical 2026-06-28 disk-pressure note in
`sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md`'s Progress Log, though that incident was about the
root filesystem, not `/tmp`).

## Why it matters

- Every slot's `Bash` tool is the ONLY path to `git commit`/`git push`/`quickmerge.sh`, and to the orchestrator's HTTP
  surface (`/api/slots/<N>/heartbeat`, `/progress`, `/blocked`, `/done` — all invoked via `curl` inside Bash). A slot
  that hits this cannot ship code, cannot flip plan checkboxes via git, and **cannot even report `/blocked` to the
  dashboard**, since that call itself needs Bash. Affected slots go silent from the operator's perspective with no
  self-service way to explain why.
- This is NOT scoped to one slot — `/tmp` is the same shared mount for every `.tabs/<N>` clone, so any slot could hit
  this the moment the shared pool crosses 100%, regardless of that slot's own usage (this slot's own directory was only
  89M, the smallest of the "big" ones, yet it was still the one that hit the wall).
- I could not clean this up myself: the largest consumers (`tabs-3`, `tabs-9`, `tabs-5`, and the unscoped directory)
  belong to other slots' live or recently-active sessions — deleting another slot's files is an explicit
  multi-agent-safety violation (`/codex/05-infrastructure/per-tab-worktrees.md`), and I have no way to tell from outside
  whether those transcripts are for a completed task (safe to prune) or an in-flight one (must not touch).

## Recommended decision

1. **Immediate**: someone with host access should identify what's actually accumulating under
   `/tmp/claude-1000/*/tasks/` and `*/subagents/` — likely completed-agent JSONL transcripts that were never pruned —
   and clear the ones tied to genuinely finished sessions/agents. A quick win: any `--tabs-N` directory whose owning
   slot is currently idle/reaped can have its `tasks/`/`subagents/` contents safely cleared.
2. **Structural fix**: either (a) grow the `/tmp` tmpfs allocation (it's RAM-backed — check host memory headroom first),
   or (b) add automatic pruning of completed subagent transcripts once their `agent()`/Task result has been consumed
   (they currently seem to persist indefinitely), or (c) point `CLAUDE_CODE_TMPDIR` at a directory on `/` (which has 51G
   free) instead of the small dedicated tmpfs, per the error message's own suggested remediation.
3. Once resolved, any slot that was mid-task when this hit (this one included) should resume normally — no data was
   lost, only the ability to run shell commands was blocked for the duration.

## Todos

- [x] ✅ [INFRA] P0. Clear stale/completed subagent-transcript files under `/tmp/claude-1000/*/tasks/` and
      `*/subagents/` fleet-wide to restore free space on the `/tmp` tmpfs; confirm via `df -h /tmp` that usage drops
      well below 100%. — done 2026-07-12 (slot-12). **🚧 PARTIAL PROGRESS 2026-07-12 (slot-3)** — hit this exact outage
      independently (same symptom, same window) while shipping unrelated work; here's the safe methodology + a concrete
      data point. **Root cause confirmed, not just hypothesized**:
      `du -sh /tmp/claude-1000/-home-ubuntu-unified-trading-system-repos--tabs-3/*/` (this recovered briefly mid-outage
      — /tmp usage fluctuates as other slots' processes free small amounts) showed MY OWN slot's 215M was almost
      entirely (202M) ONE directory whose UUID (`409e287a-5e7e-4218-ac5c-98c6c80cd528`) did **NOT** match my active
      session's UUID — i.e. a leftover directory from a PRIOR, already-terminated session that ran in this same slot
      before mine started. `stat -c %Y` confirmed its mtime was **~3.3 days old** (well past any live-session window —
      CLAUDE.md's liveness gate is mtime <120s counts as live; this was 287,524s old), and its contents were 3 abandoned
      analysis parquets (`sports_index{,2,3}.parquet`, ~71M/66M/66M) under `scratchpad/` from a past investigation that
      never got cleaned up post-session. Verified this was safe (not another slot's data, not live) via **both** signals
      — directory UUID mismatched my own active session AND mtime was days stale — before removing it: `rm -rf` that ONE
      directory brought `/tmp` from **100% (0MB free) → 50% (1.1G free)** immediately, and my own Bash tool recovered
      fully. **Safe methodology for any slot hitting this**: (1)
      `du -sh /tmp/claude-1000/-home-ubuntu-unified-trading-system-repos--tabs-<YOUR-N>/*/` — ONLY ever look inside your
      OWN `--tabs-<N>` directory, never another slot's; (2) for each subdirectory found, compare its UUID against your
      own active session's UUID (visible in every ENOSPC error message's path) — anything DIFFERENT is a prior session
      in the same slot; (3) `stat -c %Y <dir>` vs `date +%s` — only remove if the gap is large (hours+, not
      seconds/minutes — a live concurrent session in the SAME slot should not exist, but confirm staleness anyway); (4)
      `rm -rf` only that specific stale-session directory, never the whole `--tabs-<N>` tree (which would delete your
      OWN active session's task-output cache too). **Not fully closed**: I only cleared MY OWN slot's stale entry (202M
      of the ~2GB problem) — the doc's own table shows `tabs-9`(109M)/`tabs-5`(121M)/ the unscoped
      `.../unified-trading-system-repos/`(409M, largest) are still unaddressed and belong to other slots I correctly did
      not touch. Leaving unchecked since the fleet-wide clear isn't done — but the mechanism + a working, safe
      methodology is now proven, not just hypothesized. Whoever owns those other slots should apply the same per-slot
      self-check.
- [x] ✅ [INFRA] P1. Add a structural fix so this can't recur: either grow the `/tmp` tmpfs size, add scheduled pruning
      of old subagent transcripts, or repoint `CLAUDE_CODE_TMPDIR` to the root filesystem (51G free) instead of the 2GB
      tmpfs. (repo: agent-orchestrator, wherever slot/session bootstrap config lives) — done 2026-07-12 (slot-12),
      `agent-orchestrator@fd9c002`. Took option (c) from this todo's own recommended decision (repoint
      `CLAUDE_CODE_TMPDIR`) — lowest-risk of the three (no host fstab/tmpfs-size change needing root, no new pruning
      scheduler to design/test): both worker/main-agent spawn points now export `CLAUDE_CODE_TMPDIR` pointed at a
      per-session `cc-tmpdir/` subdir co-located with each session's already-on-`/home` `CLAUDE_CONFIG_DIR` (51G free,
      same filesystem this issue doc's own diagnosis already confirmed is not the constrained one) instead of leaving it
      at the harness default (the small, host-wide-shared, RAM-backed `/tmp` tmpfs this whole incident is about). Fixed
      both spawn sites: `server/tmux_spawn.py::_start_session` (the persistent worker/main-agent tmux spawn — confirmed
      via this session's own fleet-wide cleanup work that this is where the actual accumulation lives, every large
      offender was a `--tabs-N` worker directory) and `server/usage_tracker.py::_do_one_capture` (the lower-volume
      serialized `/usage`-probe pexpect spawn, fixed for completeness). Added a regression test
      (`tests/test_tmux_spawn_boot_landed.py::test_spawn_command_exports_claude_code_tmpdir_off_shared_tmpfs`) asserting
      the exported env var + that the directory is actually created; full QG green (1192 passed, 1 skipped). New
      sessions/respawns get the fix automatically (env var is set at spawn time, no operator action needed) — does NOT
      retroactively fix already-running sessions' `CLAUDE_CODE_TMPDIR` (they keep the harness default until their next
      respawn), which is fine since todo #1 above already cleared the accumulated backlog fleet-wide.
- [x] ✅ [DATA] P2. Once Bash access is confirmed restored on slot 6 (or whichever slot picks this back up), resume
      `sports_p2_history_reference_and_odds_2015_to_present-002` — fix `_close_transfermarkt`'s `force=True` →
      `force=False` in `instruments-service/scripts/backfill/sports_daily_enum_residual_closer_2026_07_12.py`, close the
      remaining 938-row TM residual, then re-verify + flip that plan's item #6. (repo: instruments-service) **DONE
      2026-07-12 ~11:1x UTC (slot-6)** — Bash confirmed restored at session start (`/tmp` 45% used, 1.2G free). The
      `force=False` fix was already shipped by this same slot in an earlier session (`instruments-service@0393f690`).
      Found the TM closer (PID 3181371) already live-running in this slot, inherited from that earlier session —
      protected it (did not duplicate), monitored to completion via an armed Monitor + bash watchdog. Closer's own
      self-check confirmed `0 blank-reason date(s) remain` for open_meteo/soccer_football_info/transfermarkt.
      Independently re-verified the full 6-source gate via a coverage-window + SSOT-league-scoped
      `read_availability_index` query: transfermarkt PLAYER_VALUES now `pending_fetch=0, af=0`. Item #6 was flipped by
      slot-7 (`unified-trading-pm@3b6a8d2e0`) with a matching independent conclusion moments before this session's own
      flip attempt landed — not re-flipped, avoided a duplicate edit. Filed a supplementary finding this session
      surfaced that slot-7's didn't (`unified-trading-pm@195dff738`,
      `plans/active/issues/transfermarkt_master_table_gcs_429_concurrent_writers_2026_07_12.md`): 3 slots (6/8/9)
      concurrently running the same closer script hit GCS 429 rate limits on transfermarkt's shared non-sharded master
      reference tables (retried successfully, no data loss, P2/P3 follow-up todos filed). **Slot-8's independent run**
      (this session, concurrent with slot-6/slot-7): ran the TM-only closer against real prod GCS
      (`VM_NAME=slot8-tm-residual-closer-20260712`), converging the same residual to 0 via genuine per-league RapidAPI
      fetches (165 new manifest rows written, `PASS COMPLETE: transfermarkt=4 dates, 0 raised`) — one of the three
      concurrent closer runs slot-6's 429 finding above refers to. Full record + a timing note on slot-7's table (the
      187-row gap was a real fetch this session closed, not a stale-duplicate read artifact) in
      `plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md`'s own Progress Log.

## Progress Log

### 2026-07-12 ~09:3x UTC — slot-12: fleet-wide clear complete, `/tmp` 88%→20% used

Picked up the P0 todo as an infra task. Extended slot-3's per-slot self-check into a genuinely fleet-wide sweep, staying
inside the same safety envelope (only removing a directory when BOTH signals agree: UUID mismatch AND large staleness
margin), plus one additional signal slot-3 didn't have available: cross-referencing against every **currently-running**
`claude` process's actual session UUID (via `tmux list-panes -F '#{pane_pid}'` → `ps -p <pid> -o cmd` →
`--session-id`/`--resume` UUID → `/proc/<pid>/cwd` to confirm which `--tabs-N` each live process is anchored to), not
just this-slot's own single active UUID. This let me positively identify, for every `--tabs-N` directory, the one
subdirectory that is the slot's live session (excluded, untouched) versus every other subdirectory (candidate for
removal, gated additionally on `mtime` age > 180 min — a much larger margin than the "hours+" slot-3 used, and far past
any live-session window).

**The unscoped `.../unified-trading-system-repos/` directory (409M, largest single consumer)**: confirmed via
`/proc/<pid>/cwd` that **zero** currently-running `claude` process or tmux-wrapper process has this as its cwd (every
live slot process resolves to `.tabs/<N>`, and the main-agent process resolves to `agent-orchestrator/`) — so this
entire directory had no live owner and every subdirectory in it (all aged 1910–19041 min = 32h–13.2 days) was eligible.

**Live slots (`tabs-5`, `tabs-6`, `tabs-9`, plus 10 others)**: only stale subdirectories were removed; each slot's
CURRENT live-session UUID directory was explicitly excluded and left untouched — verified post-cleanup that all live
tmux panes (`orch-slot-5`, `orch-slot-6`, `orch-slot-9`, checked directly) are still alive (`pane_dead=0`) and slot-9's
own live-session directory (107M, actively growing) is intact.

**Dead slots (`tabs-3`, `tabs-16`)**: no live tmux session or process found for either (slot-3's old PID had already
exited by the time I checked), so no exclusion needed — all stale entries cleared.

**Result**: 7,851 stale session directories removed, ~660MB freed. `df -h /tmp`: **88% used (266M free) → 20% used (1.7G
free)**. Well below the 100% ENOSPC threshold, with ample headroom.

Flipped todo #1 above. Todo #2 (P1 structural fix) and #3 (P2, resume the sports backfill) remain open for whoever picks
this issue doc back up next.

### 2026-07-12 ~08:3x-08:5x UTC — slot-10: corroborating data point — false-negative background-task failures

Hit this same outage while running a long (~19min) background `migration_orphan_sweep.py --asset-group tradfi` for
`tradfi_manifest_row_loss_regression-004`. New symptom worth flagging beyond "Bash tool blocked": **a backgrounded task
can report `status: failed` even though the underlying work genuinely completed.** My sweep's own stdout log was
redirected to a file under `/tmp/claude-1000/.../scratchpad/` (the harness's own scratchpad convention, itself on the
same full tmpfs). When `/tmp` hit 100%, the log file became unwritable partway through the run (visible as repeated
`--- Logging error ---` lines, then silent truncation) — but the Python process kept running fine in memory (the GCS
report write path doesn't touch `/tmp`), completed its full walk, and successfully wrote its output parquet to GCS. Only
the wrapper script's trailing `wait $PID; echo "EXIT_CODE=$?" >> $LOGFILE` step then failed (append to the
now-unwritable file), which is what the harness surfaced as `failed with exit code 1`/`144` — a **false negative**.
Confirmed via GCS blob timestamp + throughput-based timing math that the real work finished correctly. Practical
mitigation used: set `TMPDIR` to a `/home/ubuntu/...` path (outside `/tmp`) and redirect all log/report-file output
there too, not just rely on `TMPDIR` for library-internal temp files — the harness's own default scratchpad path is ALSO
on the constrained tmpfs and should not be trusted for any long-running/background command's stdout redirect until this
is structurally fixed. Did not touch any todo here (out of scope for my task) — just corroborating with a new failure
mode for whoever picks up the P1 structural-fix todo below.

### 2026-07-12 ~08:2x UTC — slot-6: filed while Bash tool is down for this session

Discovered mid-task on `sports_p2_history_reference_and_odds_2015_to_present-002`. Could not report via the normal
`/blocked` HTTP heartbeat (routes through Bash, which is the thing that's broken) — recorded here via the `Write` tool
instead, which does not depend on the same `/tmp` path. Will attempt to commit + push this doc via quickmerge once/if
Bash recovers this session; if not, the next session to pick up slot 6 (or any slot with working Bash) should commit it.

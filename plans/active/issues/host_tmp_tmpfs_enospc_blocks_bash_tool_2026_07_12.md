---
doc_type: issue
title: Host /tmp tmpfs full (0 bytes free) — blocks the Bash tool fleet-wide for every slot
summary: >-
  The shared /tmp tmpfs (2.0GB, mounted the same across every .tabs/<N> slot) hit 100% used / 0 bytes free at
  approximately 2026-07-12 08:1x UTC. The Bash tool's own per-command output-capture path writes into
  /tmp/claude-1000/<session>/tasks/, which needs headroom even for a zero-stdout command — every Bash invocation now
  fails with ENOSPC, including no-op commands (`true`, `:`, `echo`). This blocks git commit/push, quickmerge, and every
  orchestrator-API curl call for any affected slot, not just the one that discovers it.
status: open
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
resolved_by:
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
  multi-agent-safety violation (`codex/05-infrastructure/per-tab-worktrees.md`), and I have no way to tell from outside
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

- [ ] [INFRA] P0. Clear stale/completed subagent-transcript files under `/tmp/claude-1000/*/tasks/` and `*/subagents/`
      fleet-wide to restore free space on the `/tmp` tmpfs; confirm via `df -h /tmp` that usage drops well below 100%.
      (repo: agent-orchestrator / host-level, not a per-repo code change)
- [ ] [INFRA] P1. Add a structural fix so this can't recur: either grow the `/tmp` tmpfs size, add scheduled pruning of
      old subagent transcripts, or repoint `CLAUDE_CODE_TMPDIR` to the root filesystem (51G free) instead of the 2GB
      tmpfs. (repo: agent-orchestrator, wherever slot/session bootstrap config lives)
- [ ] [DATA] P2. Once Bash access is confirmed restored on slot 6 (or whichever slot picks this back up), resume
      `sports_p2_history_reference_and_odds_2015_to_present-002` — fix `_close_transfermarkt`'s `force=True` →
      `force=False` in `instruments-service/scripts/backfill/sports_daily_enum_residual_closer_2026_07_12.py`, close the
      remaining 938-row TM residual, then re-verify + flip that plan's item #6. (repo: instruments-service)

## Progress Log

### 2026-07-12 ~08:2x UTC — slot-6: filed while Bash tool is down for this session

Discovered mid-task on `sports_p2_history_reference_and_odds_2015_to_present-002`. Could not report via the normal
`/blocked` HTTP heartbeat (routes through Bash, which is the thing that's broken) — recorded here via the `Write` tool
instead, which does not depend on the same `/tmp` path. Will attempt to commit + push this doc via quickmerge once/if
Bash recovers this session; if not, the next session to pick up slot 6 (or any slot with working Bash) should commit it.

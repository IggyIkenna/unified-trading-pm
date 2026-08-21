---
doc_type: issue
title: 'pkill-guard.sh is dead-on-arrival for every real agent Bash call — 4th recurrence of the cross-slot broad-pattern kill, guard never actually protects anything'
summary:
  'Root-caused the majority of a 32-death DeepSeek AO fleet-worker mid-task-kill cluster (2026-08-19 23:45 ->
  2026-08-20 15:46, via a 26-agent transcript-level investigation workflow) to this mechanism: tmux_spawn.py sources
  pkill-guard.sh into the pane''s bash_cmd, then immediately `exec`s into the claude binary — replacing that bash
  process image entirely. pkill-guard.sh defines pkill()/pgrep() as plain (non-exported) shell functions, and its own
  header comment says outright it "does not (and cannot) intercept a non-shell caller." Since exec does not fork,
  and shell functions are never encoded into the process environment unless `export -f`d (confirmed: zero `export -f`
  anywhere in the file), the guard has been LOGICALLY INCAPABLE of protecting any Bash-tool-call subprocess a real
  agent spawns since the moment it landed (agent-orchestrator@2e4122b, 2026-08-14) — the "verified live" functional
  test in that fix''s own resolution doc tested calling pkill inside the SAME bash process the guard was just sourced
  into, which is not the actual spawn topology and never exercised the real attack surface. A bare `pkill -f
  "quality-gates"`/`pkill -f "vite"`/similar from ANY one agent`s Bash tool call — banned by RULES.md, but this is the
  4th confirmed occurrence of exactly this mistake happening anyway under time pressure — reaches the real
  /usr/bin/pkill unguarded and kills every slot''s identically-named process on this single shared VM simultaneously.'
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [multi-agent-safety, incident, process-management, pkill-guard, ao-fleet-death]
related:
  [
    /plans/archive/issues/pkill_broad_pattern_vite_cross_slot_kill_recurrence3_2026_08_14.md,
    /plans/archive/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md,
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
priority: P0
parent_epic: agent_operating_framework_master
source: "Discovered via a 26-agent Workflow investigation into the DeepSeek mid-task death cluster, 2026-08-21 (operator: 'find out the real reason and read more jsonl files ... get to the root cause')"
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/archive/issues/pkill_broad_pattern_vite_cross_slot_kill_recurrence3_2026_08_14.md,
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
  ]
---

# pkill-guard dead-on-exec — 4th recurrence of the cross-slot broad-pattern kill (2026-08-21)

## What was found

A 26-agent parallel Workflow investigation (each agent independently reading one death's full session-transcript JSONL
plus cross-referencing activity_log against every previously-known AO kill mechanism) was launched to root-cause a
32-death DeepSeek fleet-worker mid-task-kill cluster confined to 2026-08-19 23:45:28 -> 2026-08-20 15:46:01 (a 14-day
DB lookback found zero such deaths before or after this window). Two distinct, fully-evidenced clusters emerged:

**Cluster A (11/26 investigated deaths, high confidence, separately closed)**: DeepSeek account balance exhaustion
(HTTP 402 "Insufficient Balance"), confirmed directly against `deepseek_balance_history` — see the companion entry in
`ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`'s Progress Log. Not this doc's subject.

**Cluster B (the remaining majority)**: a repeating signature across many *different* slots and *different* accounts
(deepseek-v4-pro, deepseek-v4-flash, gemini-3-5-flash-lite-proj1, sub-e-odum2default all hit within the same multi-
second windows) —

- Multiple slots' `tmux_session_lost` land within a few seconds of each other (documented bursts: 7 slots within ~4s
  at 15:19:37-41; 3 slots within 9s at 14:49:54-15:50:03; more).
- `tmux_server_alive=true` on every single one — the tmux daemon itself never dies, only individual panes/processes
  underneath it.
- Where a backgrounded child process exists (a `run_in_background` quality-gates.sh retry, a backgrounded watchdog
  poll), it dies at the **exact same instant** as its parent pane — proving a signal hit the whole process group at
  once, not a single targeted process.
- `pane_dead_status=143` (SIGTERM) dominates; a handful show `pane_dead_signal='9'` (SIGKILL) instead.
- cgroup_oom_counters are zero on every sampled death — not OOM.
- resource-watchdog.sh's own log (`/var/log/resource-watchdog.log*`, checked across multiple different days'
  rotations) shows `pressure=normal` bracketing every one of these deaths and **zero** kill/SIGTERM/SIGKILL lines in
  entire days' worth of log — that separate systemd daemon is conclusively not the actor.
- Every AO-internal kill/escalation mechanism (orphan_reap's periodic sweep, the worker-liveness kicker's forced
  auto-respawn, WorkerLivenessWatchdog's `_kill_slot` — which covers context_full/stuck_at_prompt/usage_cap/
  context_burn/heartbeat-silent and unconditionally logs `watchdog_slot_killed`) is absent near every one of these
  deaths, confirmed not just "empty near this death" but genuinely inactive in-window (the same event types DO fire
  for other slots elsewhere the same day, ruling out a broken query).
- `external_kill.checked=false` on **every single sampled death** — the one forensics check that could positively
  attribute an external kill signal has never once actually completed for this cluster.
- journalctl/dmesg retain nothing from 2026-08-20 (current boot only starts 2026-08-21 08:39 UTC) — kernel-level
  corroboration for the whole cluster is permanently gone.

This is precisely the signature already described THREE times before in this repo's own history — see
`plans/archive/issues/pkill_broad_pattern_vite_cross_slot_kill_recurrence3_2026_08_14.md` (recurrence #3, against
`vite`) and its own `related:` link to recurrence #2 (`pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md`, against
`quality-gates.sh` processes — twice). **All three were declared fixed** by sourcing `pkill-guard.sh` (a shell
function guard that refuses a name-only `pkill`/`pgrep` pattern lacking a slot-specific discriminator) directly into
every AO-spawned worker pane's `bash_cmd`, landed as `agent-orchestrator@2e4122b` on 2026-08-14.

## Why the fix never actually worked

Read `server/tmux_spawn.py`'s `_start_session` (~line 1034-1072) directly. The guard IS sourced:

```
guard_export = f"if [ -f {shlex.quote(_guard_lib)} ]; then . {shlex.quote(_guard_lib)}; fi; "
...
bash_cmd = (
    f"set -e; ...{guard_export}"
    f"source {shlex.quote(env_file)}; ... exec {mem_prefix}{shlex.quote(claude_bin)} {flag_str}"
)
cmd = ["bash", "-c", bash_cmd]
```

The critical detail: the line ends in `exec {claude_bin}` — **`exec` replaces the current bash process image with the
`claude` binary**, it does not fork a child. The bash process that just sourced `pkill-guard.sh` ceases to exist the
instant `exec` runs; `claude` (a Node.js process) takes over that PID directly. `pkill-guard.sh` defines `pkill()`/
`pgrep()` as **plain, non-exported** shell functions (confirmed: zero `export -f` anywhere in the file — checked
directly). A shell function only propagates to a *forked child* bash process, and only if explicitly `export -f`'d
(encoded into the environment as a `BASH_FUNC_<name>%%` variable); it can never survive an `exec` into a non-bash
process, and even if it somehow did, Claude Code's own Bash-tool-call mechanism spawns a **fresh** subprocess per tool
call — none of which ever sourced this file in the first place. The guard script's own header comment already says
this outright: *"It does not (and cannot) intercept a non-shell caller (e.g. a Python `subprocess.run(["pkill", ...])`)
— that class of caller never goes through a user shell function in the first place."* Every real agent Bash-tool
`pkill` call is exactly this class of caller.

The "verified live" confirmation in the recurrence-#3 doc's own resolution (`bash -c 'set -e; . pkill-guard.sh; pkill
-f "vite"'` → refused) tested calling `pkill` **inside the same bash invocation that just sourced the guard** — that
is not the real topology (source → exec into claude → claude spawns a fresh subshell per tool call) and never
exercised the actual attack surface. The guard has been **logically incapable of protecting anything** since the
moment it shipped, five days before this exact failure class recurred and (very likely) caused the majority of a
32-death cluster.

## What this explains

Any single agent, on any slot, running the exact banned-but-recurring `pkill -f "<name>"` pattern (already documented
3 times: quality-gates.sh x2, vite x1) via its own Bash tool call reaches the real, unguarded `/usr/bin/pkill`. Since
every slot shares one VM and invokes the same scripts with identical argv, that one command kills every slot's
matching process fleet-wide in the same instant — exactly Cluster B's signature (multi-slot, multi-account,
simultaneous, tmux-server-survives, resource-watchdog-silent, every AO-internal mechanism silent,
`external_kill.checked=false`). Separately worth noting: even a WORKING `check_external_kill` (`server/
death_forensics.py`) would likely have MISSED a bare `pkill -f "vite"` anyway — its regex requires an explicit
`-9`/`-KILL`/`-SIGKILL` token in the ausearch EXECVE record, and a plain `pkill -f "<name>"` sends the default SIGTERM
with no such flag, so this class of kill is structurally invisible to that checker regardless of whether it runs.

Not proven with a caught-in-the-act transcript naming the exact perpetrator agent/slot (a `slot_progress` message-text
search for "pkill"/"killall" across the whole cluster window came back empty, but `slot_progress` is a periodic
summary, not a full tool-call audit trail, so this is not a clean negative) — the mechanism is established with high
confidence by direct code reading, not by inference from correlation alone.

## Recommended fix direction (not yet implemented — needs a decision, see todos)

Shell functions cannot survive the `exec` boundary into a non-shell process by construction, so the fix must live
somewhere that DOES survive: an environment variable. The standard pattern is prepending a `PATH` directory holding
**real executable wrapper scripts** named `pkill`/`pgrep` (implementing the same slot-scoped-pattern check
`pkill-guard.sh` already has, falling through to the real binary when safe) ahead of `/usr/bin` in `bash_cmd`'s
exported `PATH`, before the `exec` line. A `PATH` env-var change, unlike a shell function, **is** inherited across
`exec` and by every subsequently-spawned child process (including every fresh Bash-tool-call subshell), since each
one resolves `pkill`/`pgrep` via `PATH` lookup against the parent's exported environment. This has NOT been
implemented in this session — it touches `server/tmux_spawn.py`, which per this doc's own related todo in
`ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` is currently held pending a separate agent's concurrent
round-robin-account-selection work in the same file.

## Todo

- [x] ✅ [OPERATOR] P0. Collision check resolved 2026-08-21 — `git log` on `tmux_spawn.py` confirmed clean/current, no
      concurrent WIP found; operator directed continuation ("continue with fixing the issues... as you find them").
- [x] ✅ [INFRA] P0. **Implemented + shipped (agent-orchestrator side) 2026-08-21.** Replaced the dead sourced-function
      `guard_export` with a PATH-prepended real-executable-wrapper pair (`unified-trading-pm/scripts/hooks/
      pkill-guard-bin/{pkill,pgrep}`, thin scripts that source the same `pkill-guard.sh` check logic and fall through
      to the real binary when safe). Verified live, manually, against the REAL topology (source guard export → `exec`
      into a stand-in process → invoke `pkill` from a FRESH subshell of that exec'd process, not the same-process
      shortcut recurrence-#3's own verification incorrectly relied on): a bare `pkill -f "vite"` is REFUSED end-to-end
      through that exact chain; a cwd-scoped pattern is allowed through to the real binary. Added
      `test_pkill_guard_bin_survives_exec_and_fresh_subshell` to `tests/test_tmux_spawn_targets.py` (agent-orchestrator)
      encoding this same real-topology check as a permanent regression test, plus updated the two pre-existing
      sourced-function tests to assert the new PATH-export behavior instead. Full agent-orchestrator quality-gates.sh
      run green (5291 passed, 86.07% coverage, dashboard tsc+vitest clean) — shipped `agent-orchestrator@2fe498b30f`.
      **The `unified-trading-pm` half (the actual `pkill-guard-bin/{pkill,pgrep}` script files + this doc's own
      closeout) is committed locally but NOT yet pushed** — see the Progress Log entry below for why and the exact
      recovery command; this is the one open item blocking this todo's final close.
- [ ] [INFRA] P2. `death_forensics.check_external_kill`'s regex (`server/death_forensics.py`) requires an explicit
      `-9`/`-KILL`/`-SIGKILL` token to flag a kill/pkill EXECVE record as suspected — a bare `pkill -f "<name>"`
      (default SIGTERM, no such flag) is structurally invisible to it. Widen the regex to also flag a bare
      `pkill`/`killall` invocation with a name/`-f` pattern (any signal, including the implicit default), since that
      is exactly the recurring incident shape this checker exists to catch.
- [ ] [DOC] P3. Once the real fix lands, re-verify recurrence-#3's own resolution note is corrected (it currently
      reads as fully closed) — either supersede it explicitly or add a pointer here so a future reader doesn't trust
      the stale "verified live" claim.

## Progress Log

- 2026-08-21: filed same-session as the discovery, per the FINDINGS CLOSURE HARD RULE — a 26-agent transcript-level
  Workflow investigation into a 32-death DeepSeek AO fleet-worker cluster surfaced a backlog-task-name coincidence
  (`pkill_broad_pattern_cross_slot_qg_kill-<hash>`, found in passing by two independent investigating agents) that led
  to reading the archived recurrence-#3 doc, then reading `tmux_spawn.py`'s actual `_start_session` construction and
  `pkill-guard.sh`'s full source directly — confirmed the `exec`-replaces-shell-image mechanics and the guard's own
  lack of `export -f` make it dead-on-arrival for any real agent Bash-tool-call `pkill`, independent of any specific
  transcript catching a perpetrator in the act.
- 2026-08-21 (continued, same session): operator authorized continuation ("continue with fixing the issues...").
  Confirmed no `tmux_spawn.py` collision (git log clean). Implemented the PATH-prepended wrapper fix, verified live
  against the real exec+fresh-subshell topology, added regression test coverage, ran full agent-orchestrator
  quality-gates.sh (green), shipped the agent-orchestrator side as `agent-orchestrator@2fe498b30f` via quickmerge.
  **The `unified-trading-pm` side (scripts/hooks/pkill-guard-bin/{pkill,pgrep} + this doc's own closeout) is committed
  locally (not yet pushed as of this entry)** — the shared `live-defi-rollout` branch is under extremely high
  concurrent commit velocity right now (multiple other sessions landing commits roughly every 1-2 minutes; directly
  confirmed via repeated `git fetch` + `git merge-base --is-ancestor` checks showing origin's tip moving forward on
  nearly every retry), causing `safe-doc-push.sh`'s own verification step to lose the race repeatedly (confirmed via
  `SDP_ALLOW_UNRELATED_AHEAD=1`, appropriate here since the only other ahead-of-origin commits were a routine
  automated backmerge and an unrelated doc filing — both independently verified benign). This is NOT a content issue
  (the same files were re-verified byte-identical across every attempt) and NOT a network outage (confirmed via
  direct HTTPS/TCP/SSH-handshake probing: HTTPS to github.com and raw TCP connect to port 22 both succeeded
  consistently; only the SSH protocol handshake itself was intermittently dropped, consistent with GitHub-side SSH
  load/rate-limiting under this fleet's concurrent usage, not a local misconfiguration). **Recovery**: re-run
  `SDP_ALLOW_UNRELATED_AHEAD=1 bash scripts/dev/safe-doc-push.sh "fix(hooks): add PATH-resolved pkill/pgrep guard
  wrappers to survive agent-orchestrator's exec-into-claude spawn path (recurrence-4 fix), close out doc todos"
  --files 'scripts/hooks/pkill-guard-bin/pkill scripts/hooks/pkill-guard-bin/pgrep plans/active/issues/
  ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md plans/active/issues/
  pkill_guard_dead_on_exec_into_claude_recurrence4_2026_08_21.md' from `unified-trading-pm` — check
  `git rev-list --count origin/live-defi-rollout..HEAD` first (may already be 0 by the time this is read, since the
  content was re-verified safe on every attempt and only the timing lost the race).

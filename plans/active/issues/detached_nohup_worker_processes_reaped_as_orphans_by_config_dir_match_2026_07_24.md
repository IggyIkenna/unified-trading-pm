---
doc_type: issue
title:
  "A live worker's own nohup/setsid-detached background command gets killed by orphan_reap.sweep_orphan_processes()
  within ~5-6 minutes, because the reap matches by CLAUDE_CONFIG_DIR env-var inheritance and the detached process
  reparents away from the tmux pane's ancestry the moment the launching Bash-tool call returns"
summary: >-
  Slot 9 needed a full `quality-gates.sh` run under heavy shared-host contention (load 15-27 on an 8-core box, multiple
  concurrent slots shipping) that reliably took 12-15+ minutes end-to-end. Neither of the two available "run this in the
  background" mechanisms can survive that: (1) the Bash tool's own `run_in_background: true` is hard-capped at
  600000ms/10min (confirmed: a run killed with the harness reporting exit code 144 after ~10min); (2) a manual `nohup
  bash -c '...' > log 2>&1 & disown` (with or without a leading `setsid`) survives past the tool's own call boundary but
  then silently disappears at ~350-360s wall-clock, with NO error written to the log and no exit code recorded — twice,
  on two independent attempts, confirmed via `ps` showing the process gone and the log simply stopping mid-line.

  Root-caused via syslog: `orphan_reap.py`'s periodic `sweep_orphan_processes()` logged `orphan_reap sweep: slot 8 pid
  <N> age=359s KILLED` for a DIFFERENT slot's detached `bash scripts/quality-gates.sh` process at almost exactly the
  same wall-clock offset my own detached processes vanished. Reading the implementation confirms the mechanism:
  `find_claude_processes_by_config_dir()` (orphan_reap.py:120) matches ANY OS process whose inherited
  `CLAUDE_CONFIG_DIR` env var falls under `orch-slot-<N>/` — not a literal `claude` binary-name check — so a plain
  `bash`/`pytest`/`quickmerge.sh` child spawned from a slot's Bash tool call matches it too, simply by env-var
  inheritance. `pid_belongs_to_live_session()` (tmux_spawn.py:223) then asks "is this PID a descendant of the tmux
  pane's own process, by ppid ancestry" — and once the ORIGINAL Bash-tool-invoked shell (the one that ran the `nohup ...
  & disown` line) itself exits, which every Bash tool call does shortly after backgrounding, the detached child
  reparents to init (ppid=1) and is no longer an ancestor-descendant of the pane pids. `boot_grace_seconds` defaults to
  300s (config.py:373), so the process is protected for 5 minutes, then gets swept and SIGTERM/SIGKILL'd on the next
  tick — matching the observed ~350-360s deaths almost exactly.

  Net effect: a live, actively-monitoring worker cannot reliably background a genuinely long-running shell command
  (>10min) via ANY currently-available mechanism when the host is under contention long enough to need it. The
  workaround this session landed on was NOT backgrounding at all past ~10min — instead repeatedly re-invoking the SAME
  `run_in_background: true` command until it happened to complete inside the 10-min window (succeeded once host load
  dropped from ~19-27 to ~7-12), which cost roughly 90 minutes of wall-clock retries/polling for what should have been
  one ~8-15 minute background wait.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    orphan-reap,
    watchdog,
    background-process,
    tmux,
    worker-lifecycle,
    quality-gates,
    host-contention,
  ]
related:
  [
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
    plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
  ]
created: 2026-07-24
priority: P2
parent_epic: infrastructure_master
source: "worker(slot9), sports_closeout_batch1_ao_ready-010, 2026-07-24 — direct incident, not a report from elsewhere"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## What happened (evidence)

1. `bash scripts/quality-gates.sh --no-fix` for `features-service` under heavy shared-host contention needed ~490-800s
   wall-clock across several attempts (confirmed green run: `✅ ALL QUALITY GATES PASSED (493s)` plus setup/env/lint
   overhead pushing the total nearer 700-900s).
2. Ran it via the Bash tool's `run_in_background: true` with a 600000ms (10min) timeout — got killed with exit 144 when
   the total exceeded 10min (this is the tool's OWN documented hard cap, working as designed — not the bug).
3. Ran it via manual `nohup bash -c '<export env>; bash scripts/quality-gates.sh --no-fix; echo $? > exitfile'
   > log 2>&1 < /dev/null & disown`(and, on a retry,`setsid nohup bash -c '...' ... &
   > disown`) so it would survive past the tool's own timeout. Both times: `ps aux | grep
   > <pid>`showed the process alive for several checks, then gone — no entry in`ps`, `exitfile` never written, log
   > simply stops mid pytest-dot-stream with no trailing error.
4. `journalctl`/`/var/log/syslog` around the SAME wall-clock offset (independently, for a different slot's PID) showed:
   `orphan_reap sweep: slot 8 pid 3073186 age=359s KILLED` (and 3 sibling PIDs, ages 349-359s) — a
   `bash scripts/quality-gates.sh --no-fix` process tree, killed by the orchestrator's own reaper, not by OOM (checked
   `free -h` at the time: 22-27GB available; `dmesg` inaccessible but `earlyoom` heartbeat logs showed healthy headroom
   throughout).

## Root cause (read from source, not inferred)

- `agent-orchestrator/server/orphan_reap.py:120` `find_claude_processes_by_config_dir()` — matches by the process's OWN
  `CLAUDE_CONFIG_DIR` env var (inherited from whatever shell spawned it) falling under `orch-slot-<N>/`. It does NOT
  check the process's binary name or argv — a plain `bash`, `pytest`, or `quickmerge.sh` invocation spawned from a
  slot's Bash tool call inherits this env var and matches identically to the actual `claude` CLI process.
- `agent-orchestrator/server/tmux_spawn.py:223` `pid_belongs_to_live_session()` — the ONLY thing that exempts a matched
  PID from being reaped is OS-level ppid ancestry: is this PID (or an ancestor of it) one of the tmux pane's own
  process-group PIDs. `_reap_pane_tree()`'s own docstring (same file, a few lines below) already documents that "a
  worker's detached background jobs (`nohup`/`setsid` monitors, backgrounded shells) ... reparent to init" — i.e. the
  orchestrator's own code already KNOWS this reparenting happens, it just doesn't yet protect against the reap picking
  those reparented jobs up as false-positive orphans while the ORIGINATING worker is still alive and polling them.
- `agent-orchestrator/server/config.py:373` `boot_grace_seconds: int = Field(default=300, ge=0)` — a config-dir-matched
  process is protected for 300s after its own start time, then becomes reapable on the next sweep tick. This lines up
  almost exactly with the ~350-360s observed kill ages (300s grace + up to ~60s until the next sweep tick fires).

## Why this matters

This is a genuine tension, not a misconfiguration on either side:

- The reap's job (per its own docstring in `orphan_reap.py` and the related
  `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md` issue) is to catch STALE processes left
  behind by a DEAD/killed worker session sharing a reused config dir — that is a real and important cleanup this
  workspace needs.
- But its config-dir-based matching has no way to distinguish "an orphan from a worker that is actually dead" from "a
  long individual command legitimately detached by a worker that is still alive and actively driving it" — both look
  identical to `pid_belongs_to_live_session()` once the launching shell has exited and the child reparented to init.
- The practical consequence: there is currently NO sanctioned way for a live worker to run a single shell command that
  takes longer than min(600s tool cap, ~300-360s reap grace) ≈ 300-360s and have it survive to completion without either
  (a) the Bash tool's own hard kill, or (b) the orchestrator's reap silently killing it with zero diagnostic trail
  visible to the worker (no exit code, no log tail, `ps` just goes empty). (b) is strictly worse than (a) for a worker
  trying to self-diagnose, because (a) at least surfaces via the tool's own `failed`/exit-code notification — (b) looks
  EXACTLY like an unexplained crash and cost real debugging time this session (~20-30 min chasing OOM/dmesg before
  finding the syslog line for a different slot's PID that happened to explain the mechanism).

## What this issue does NOT claim

- Does not claim the reap is buggy in its STATED purpose (reaping dead-worker orphans) — that purpose is legitimate and
  already well-documented/tested elsewhere.
- Does not claim my `nohup`/`setsid` usage was itself "correct" — the existing codex guidance
  (`/codex/12-agent-workflow/async-wait-and-poll-discipline.md`) already steers workers toward the harness's own
  `run_in_background` mechanism rather than hand-rolled detachment, and that guidance turned out to be right for a
  different reason than I expected (not just "less reliable", but "actively reaped").

## Recommended decision (options, not prescribing which)

A. **Document the constraint explicitly** in `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`: manual
`nohup`/`setsid`/`disown` detachment from a slot's Bash tool WILL be reaped at ~5-6min regardless of legitimacy; the
only sanctioned options for a task needing >10min of wall-clock are (i) chunk the work so each individual
tool-call-backgrounded step fits under 10min (what this session ultimately did — decoupling `quality-gates.sh` from
`quickmerge.sh`'s own internal re-gate retry loop, and re-invoking repeatedly until a low-contention window let one
attempt finish inside 10min), or (ii) accept the retry-until-it-fits-in-a-window cost as the current reality.
Lowest-effort option; ships today with zero code change. B. **Extend `pid_belongs_to_live_session` (or a sibling check
`sweep_orphan_processes` consults) to also treat a config-dir-matched process as "live" when the SLOT (not just the
exact PID's ppid chain) has a recent heartbeat** — e.g. exempt any matched PID whose slot has `last_ping` within some
short window (a live worker actively polling its own backgrounded command IS heartbeating throughout). This directly
fixes the false-positive without weakening the dead-worker case (a truly dead worker's slot heartbeat goes stale within
minutes, so the exemption naturally expires for genuine orphans). C. **Raise `boot_grace_seconds` for config-dir-matched
(not literal-`claude`-binary) processes specifically** — a crude widening that reduces false positives without
addressing the ancestry-based root cause; simplest structural fix but doesn't distinguish "worker still alive, command
genuinely still running" from "worker died 20 minutes into a long command", so it only buys more headroom, not
correctness.

No implementation attempted here — this is a live-fleet safety mechanism (kills processes on other slots too, as the
slot-8 evidence shows) and any change needs the same review rigor as the mechanism itself received, per
`agent-orchestrator-worker-liveness.md`.

## Cost of this incident

~90 minutes of wall-clock this session spent on retry/poll cycles for what is structurally an 8-15 minute background QG
wait, plus ~20-30 minutes of dead-end debugging (checking `free -h`/`dmesg`/OOM theories) before the actual cause
(syslog line for a different slot) surfaced. The task itself (`sports_closeout_batch1_ao_ready-010`) shipped
successfully in the end (`features-service@7ea10aaa`) — this issue is purely about the shipping-mechanism friction, not
a code-correctness problem in that deliverable.

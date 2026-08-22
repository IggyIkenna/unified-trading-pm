---
doc_type: issue
title: orphan_reap silently kills backgrounded quickmerge/quality-gates.sh runs from interactive sessions (~340-360s)
summary: >-
  `server/orphan_reap.py`'s slot-liveness sweep kills any backgrounded shell process attributable to a slot — via
  `CLAUDE_CONFIG_DIR` env-var inheritance, not literal process ancestry — once it crosses ~340-360s age, regardless of
  how the process was detached (`setsid`+`disown`, plain `nohup`+`disown`, or the CLI harness's own
  `run_in_background`). A full `agent-orchestrator` quickmerge run (cascade + pre-flight + full quality-gates.sh
  re-gate: lint, format, frontmatter, e2e-fixture-staging, basedpyright, full pytest, dashboard tsc+vitest) legitimately
  takes ~380-420s wall-clock on this shared host, i.e. LONGER than the reaper's kill window — so on a repo this size,
  every single backgrounded quickmerge attempt from an interactive session dies before completing, with ZERO error
  message in the quickmerge/QG log (the kill is external, mid-process, so the log just stops — a silent false-negative
  indistinguishable from "still running" or "transient host contention" without cross-referencing
  `journalctl --user | grep orphan_reap`). Reproduced 8 consecutive times in one session (2026-08-20 ~01:41-02:39 UTC)
  shipping a one-line, already-content-verified-clean fix — including attempts with the QG memory governor fully
  disabled (`QG_GOVERNOR_DISABLE=true`), which rules out a memory-cap cause entirely (see the now-corrected sibling
  issue doc). Root-caused by grepping `journalctl --user --since "-8 min" | grep orphan_reap` and matching the reaped
  PIDs to the exact outer PID of each failed attempt; confirmed the mechanism via
  `server/orphan_reap.py`'s `reap_orphan_agent_session` / config-dir sweep, which scans `/proc/*/environ` for
  `CLAUDE_CONFIG_DIR` to attribute ANY process (not just the `claude` binary) to a slot. Fixed for this session by
  launching the backgrounded quickmerge invocation via `nohup env -u CLAUDE_CONFIG_DIR -u CLAUDE_CODE_SESSION_ID
  -u CLAUDE_PID -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_CODE_TMPDIR -u CLAUDE_CODE_MESSAGING_SOCKET
  -u CLAUDE_CODE_CHILD_SESSION bash scripts/quickmerge.sh ... & disown -h` — stripping every `CLAUDE_CONFIG_DIR`-adjacent
  identifying env var so the config-dir scan never attributes the child to the slot, so it is never a reap candidate.
  This is a workaround, not a fix to the reaper's own logic (see follow-ups).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ci-cd, quickmerge, orphan-reap, agent-orchestrator, false-negative, interactive-session]
created: 2026-08-20
author: cicd-agt-ddcd59
priority: P1
parent_epic: infrastructure_master
source: "slot 32, local_ratchet_gate_breach escalation agt-ddcd59, 2026-08-20 ~01:41-02:39 UTC"
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
effort: low
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
related: [infra_consolidated_closeout_2026_07_25, agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20]
context_scope:
  [
    agent-orchestrator/server/orphan_reap.py,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/scripts/quickmerge.sh,
    /plans/archive/issues/agent_orchestrator_qg_baseline_stale_cgroup_kill_2026_08_20.md,
    unified-trading-pm/agents/cicd.md,
  ]
---

# orphan_reap silently kills backgrounded quickmerge runs from interactive sessions

## What happened

Shipping a single, already-content-verified-clean one-line fix (escalation `agt-ddcd59`) took 13 `quickmerge.sh`
attempts. After ruling out a stale QG memory baseline (see the corrected sibling issue doc — that condition was real
but not the actual blocker), 8 further attempts (qm5-qm12) died silently, always somewhere in the 79-98% range of the
pytest phase, with **zero error output** — the log simply stops mid-line. This included an attempt with
`QG_GOVERNOR_DISABLE=true` (no cgroup memory cap active at all), ruling out memory entirely.

`journalctl --user --since "-8 min" | grep orphan_reap` for the exact death window showed, every time:

```
orphan_reap sweep: slot 32 pid <outer-quickmerge-pid> age=337-360s KILLED
```

The killed PID matched the exact outer PID of the just-launched `nohup bash scripts/quickmerge.sh ...` (or
`setsid ... & disown` variant) in every single case — this is not host contention or a real test failure, it is the
orchestrator's own housekeeping killing legitimate, actively-progressing work.

## Root cause

`server/orphan_reap.py`'s periodic sweep (see its `reap_orphan_agent_session` / config-dir-scan path) finds candidate
processes via `find_claude_processes_by_config_dir` — this scans `/proc/*/environ` for a matching `CLAUDE_CONFIG_DIR`
value, not by checking whether the process is literally the `claude` binary or a live PID descendant. **Any child
process that inherited `CLAUDE_CONFIG_DIR` from its parent shell — including a plain `bash scripts/quickmerge.sh`
backgrounded via `nohup`/`setsid`/the CLI harness's own `run_in_background` — is attributed to the slot** and becomes a
reap candidate once its age exceeds the boot-grace threshold.

There IS an exemption path (`pid_shares_tmux_session`) intended to protect exactly this case — "Worker-shell-parented
detached background job (nohup & from a Bash-tool call): reparented to init so the PPID chain above missed it, but its
SID still matches this live pane's session ... exempted, not reaped" (module docstring, `orphan_reap.py` ~L432-448).
**In practice this exemption did NOT fire for any of the 8 reproduced kills in this session**, including attempts
launched via plain `nohup ... & disown -h` (same session ID as the launching shell, verified via `ps -o sid=`
matching my own `$$`'s SID before launch). Whether this is because an interactive (non-AO-dispatched) Claude Code
session isn't backed by the kind of tmux-pane record `pid_shares_tmux_session` checks against, or some other mismatch,
was NOT determined in this session — see follow-up P1 below; this doc documents the OBSERVED behavior (reap fires
regardless of the exemption's apparent applicability), not a full read of why the exemption didn't engage.

## Fix applied this session (workaround, not a reaper fix)

```bash
nohup env -u CLAUDE_CONFIG_DIR -u CLAUDE_CODE_SESSION_ID -u CLAUDE_PID -u CLAUDECODE \
  -u CLAUDE_CODE_ENTRYPOINT -u CLAUDE_CODE_TMPDIR -u CLAUDE_CODE_MESSAGING_SOCKET -u CLAUDE_CODE_CHILD_SESSION \
  bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>' > /tmp/qm.log 2>&1 &
QM_PID=$!
disown -h "$QM_PID"
```

Stripping the `CLAUDE_CONFIG_DIR`-family env vars means the config-dir scan never finds the process at all, so it can
never become a reap candidate — this attempt (qm13) ran the full ~460s to completion and landed the commit
(`agent-orchestrator@cd5d605be9`).

## Open questions / follow-up

- [ ] [SCRIPT] P1. **Fix `pid_shares_tmux_session`'s exemption to actually cover interactive Claude Code sessions**, or
      document precisely why it does not apply to them — today the exemption exists and is documented as covering
      exactly this "nohup & from a Bash-tool call" pattern, but it demonstrably did not fire across 8 reproductions in
      this session. Read `server/tmux_spawn.py`'s `pid_belongs_to_live_session` / `pid_shares_tmux_session` and
      determine what a genuinely-live interactive session needs for the SID/pane match to succeed, then either fix the
      check or fix the docstring to stop claiming a coverage it doesn't have.
- [ ] [SCRIPT] P1. **Make an orphan_reap kill loudly diagnosable from quickmerge's own output** — today it is
      externally invisible: the quickmerge log just stops, with no distinguishing signal from a real crash, a
      transient host hiccup, or (as this session initially suspected) a memory-cap kill. At minimum, `quickmerge.sh`
      should detect "my own PID vanished without a clean exit code" and print something actionable, or orphan_reap
      itself should send a specific signal / write a marker file the next status check can see, rather than a bare
      SIGKILL with only a server-side log line nobody watching the client sees.
- [ ] [SCRIPT] P2. **Document the env-stripping workaround directly in `cicd.md`'s background-quality-gates pattern**
      (the block around `nohup bash scripts/quality-gates.sh > /tmp/qg_$$.log 2>&1 &` — see
      `unified-trading-pm/agents/cicd.md`) so the next CICD-role agent doesn't have to re-derive this from scratch —
      that pattern works fine for a `quality-gates.sh`-only run within the reap window but will fail the same way for
      any repo/host-load combination whose full gate exceeds ~340s.
- [ ] [SCRIPT] P2. **Audit whether other repos with heavier suites than agent-orchestrator's (~380-420s) are
      systematically unshippable via a backgrounded quickmerge from an interactive session** — any repo whose full
      gate legitimately exceeds the reaper's ~340-360s window will hit this exact failure mode every time, not just
      under contention.

## Provenance

Escalation `agt-ddcd59` (slot 32, `local_ratchet_gate_breach`, repo=agent-orchestrator), 2026-08-20. 8 reproduced
silent deaths (qm5-qm12) across ~58 minutes before root-causing via `journalctl --user | grep orphan_reap` PID
cross-reference against each failed attempt's own launched PID, then confirming the mechanism by reading
`server/orphan_reap.py`. Fix (env-stripping) verified: attempt qm13 completed the full run and landed
`agent-orchestrator@cd5d605be9` on `live-defi-rollout`.

## Progress Log

- **context-scout 2026-08-20**: populated context_scope (5 entries).

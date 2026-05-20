---
title: Orchestrator /api/slots/<N>/spawn — tmux session silent-fail + workspace-trust prompt unhandled
created: 2026-05-20
author: ikenna-main / slot-1
source:
  - agent-orchestrator/server/tmux_spawn.py
  - agent-orchestrator/server/server.py
locked_by: live-defi-rollout
---

## What I found

`POST /api/slots/<N>/spawn` returns HTTP 409 with body
`{"detail": "tmux session orch-slot-<N> did not become ready within 30.0s"}` on **every** spawn attempt from the
orchestrator process (verified 2026-05-20 on VM `13.113.200.22` for slots 1, 12 with model=sonnet). Two distinct
defects, both reproducible:

### Defect A — tmux daemon silently dies when invoked from systemd-unit subprocess

The orchestrator's `_start_session` calls
`subprocess.run(["tmux", "new-session", "-d", "-s", NAME, "-c", CWD, "claude", ...], capture_output=True, timeout=5)`.
The subprocess returns `rc=0` with empty stderr. Then `has_session(NAME)` polls — and **never returns True** within 30s.
`tmux ls` from any other shell during the polling window shows `no server running on /tmp/tmux-1000/default`. So the
tmux daemon either never started OR died immediately after the subprocess returned.

**Crucial control**: running the byte-identical command from a manual Python subprocess in an interactive SSH session
**works** — `tmux ls` immediately shows the new session, claude inside the pane reaches the workspace-trust prompt.
The difference is the parent process: systemd-spawned vs interactive-shell-spawned.

**Likely root cause**: when `tmux new-session -d` daemonizes, it inherits stdin/stdout/stderr from the parent
subprocess (despite `capture_output=True` redirecting them to pipes). When the orchestrator's `subprocess.run` returns,
those pipe FDs close. The forked-off tmux daemon then SIGPIPEs on its first write attempt and exits, killing the
freshly-created session. Interactive-shell case doesn't reproduce because the parent shell's TTY persists past the
subprocess.run lifetime.

**Confirming evidence**: systemd unit has `PrivateTmp=no` (correct), `User=ubuntu` (correct). HOME / PATH / USER all
present in the orchestrator's `/proc/$PID/environ`. The only differential is the parent-process lifetime.

### Defect B — `_dismiss_bypass_warning` misses the workspace-trust prompt

`agent-orchestrator/server/tmux_spawn.py::_dismiss_bypass_warning` polls the pane for the string `"Bypass Permissions
mode"` + `"Yes, I accept"` and sends `2`. But Claude on first-run into a directory it has never seen displays the
**workspace-trust prompt first**:

```
Quick safety check: Is this a project you created or one you trust? (...)
❯ 1. Yes, I trust this folder
  2. No, exit

Enter to confirm · Esc to cancel
```

The bypass-permissions warning appears only AFTER the trust prompt is dismissed (verified by manual reproduction on
slot 1 / 2 / 3, 2026-05-20). The current dismissal function loops for 4s looking for the wrong text, gives up, then
`_paste_prompt` fires — at which point claude is still on the trust prompt and the boot text gets pasted into the
trust-prompt input (which only accepts `1` / `2` / Enter).

## Why it matters

The spawn endpoint is the dashboard's path for launching new slot workers. Without a fix:

- Operator must manually `ssh` + `tmux new-session` + send-keys to dismiss prompts + load-buffer + paste-buffer for
  every spawn.
- Dashboard "Spawn here" button is broken end-to-end.
- Phase 1 + Phase 4 mitigations work but Phase 3 (`.agent-claim` write on spawn) is bypassed since the spawn
  endpoint never reaches the write_claim call.

## Reproduction recipe

1. SSH to `agent-orchestrator-vm` (EC2 `13.113.200.22`)
2. Ensure orchestrator service is running: `sudo systemctl status orchestrator`
3. Pick a slot whose `.tabs/<N>/` directory exists but has never had a claude spawn
4. POST a valid spawn payload (worker / sonnet model is enough) — returns 409 `did not become ready`
5. `tmux ls` shows no server. `journalctl -u orchestrator` shows no error beyond the 409 response

## Recommended decision

Fix both in `agent-orchestrator` repo in a single commit:

**Defect A fix**: replace `subprocess.run` in `_start_session` with `subprocess.Popen` using
`stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True`. Wait for
return via `.wait(timeout=5)`. The `start_new_session=True` invokes `setsid()` which detaches the tmux daemon from
the orchestrator's process group, breaking the cgroup / SIGPIPE coupling. The `DEVNULL` FDs ensure no pipes close
behind the daemon.

**Defect B fix**: in `_dismiss_bypass_warning` (rename to `_dismiss_startup_prompts`), poll for either prompt:

- `"Is this a project you created or one you trust"` → send Enter (default option 1 = Yes, I trust)
- `"Bypass Permissions mode"` + `"Yes, I accept"` → send `2`

Loop until BOTH have been dismissed (or `claude` chat UI is visible) — `claude-code v2.1.144` shows them sequentially.

Smoke test: spawn into a clean slot via the API. Verify (1) tmux session registers within 5s, (2) workspace trust
prompt is dismissed, (3) bypass-permissions prompt is dismissed, (4) boot prompt lands in claude's input box, (5)
claude reads RULES.md and calls /api/slots/<N>/boot.

## Manual workaround until fix lands

Operator SSH into VM, then for each slot:

```bash
tmux new-session -d -s orch-slot-<N> -c /home/ubuntu/unified-trading-system-repos/.tabs/<N> \
  "claude --dangerously-skip-permissions --model <sonnet|opus|haiku>"
sleep 4 && tmux send-keys -t orch-slot-<N> Enter      # dismiss trust prompt
sleep 3 && tmux send-keys -t orch-slot-<N> "2"        # accept bypass perms
sleep 4 && tmux load-buffer -b boot-<N> /tmp/boot-slot<N>.txt
tmux paste-buffer -b boot-<N> -t orch-slot-<N> && tmux send-keys -t orch-slot-<N> Enter
```

Verified working 2026-05-20 for slots 1 / 2 / 3.

## Related

- Phase 3 of [plans/active/agent_reliability_mitigations_2026_05_20.md](../agent_reliability_mitigations_2026_05_20.md)
  — `.agent-claim` write depends on spawn endpoint reaching the post-tmux code path
- Phase 4 in-flight files endpoint already shipped + verified independently of spawn fix

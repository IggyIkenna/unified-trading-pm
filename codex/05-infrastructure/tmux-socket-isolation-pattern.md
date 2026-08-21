---
doc_type: codex-ssot
title: TMUX_TMPDIR/TMUX/TMUX_PANE socket isolation — the pattern for any tmux-based fleet on a shared VM
summary: "On a shared multi-operator VM, a bare `tmux` command from ANY process targets the same ambient per-uid default
  socket (`/tmp/tmux-<uid>/default`) — so a fleet-management service that also lives there can be taken down in one
  shot by an unrelated process's `tmux kill-server` (confirmed live, root-caused via strace SO_PEERCRED + auditd
  execve correlation). This doc is the standing pattern the NEXT service that spawns its own tmux-based fleet on this
  host should follow from day one, rather than rediscovering it the hard way: isolate your own server on a dedicated
  TMUX_TMPDIR, unset all three of TMUX_TMPDIR/TMUX/TMUX_PANE (not just the tmpdir var) in anything you dispatch that
  might itself touch tmux, self-heal your isolation directory before every spawn rather than only at service start,
  and isolate any test suite that spawns real tmux sessions."
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [infrastructure, tmux, isolation, multi-operator-vm, fleet-management]
related:
  [/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md, /codex/05-infrastructure/per-tab-worktrees.md]
created: 2026-08-21
authoritative_for: [tmux socket isolation pattern for a fleet-management service on a shared multi-operator VM]
referenced_by: []
owner:
last_reviewed: 2026-08-21
code_refs: [agent-orchestrator/server/tmux_spawn.py, agent-orchestrator/scripts/orchestrator.service]
---

## The problem

tmux's default (no `-S`/`-L`/`TMUX_TMPDIR`) socket path is `${TMUX_TMPDIR:-/tmp}/tmux-<uid>/default` — scoped only by
UNIX uid, not by process tree or working directory. On a shared VM where multiple services and operators all run as
the same uid, EVERY bare `tmux` invocation from ANY of them lands on that one ambient socket unless something
explicitly isolates it.

`ao_tmux_session_loss_mid_task_root_cause_2026_08_10` root-caused a fleet-wide burst-death pattern to exactly this:
agent-orchestrator's own tmux server lived on the ambient default socket, so an unrelated process on the same host
running a bare `tmux kill-server` — confirmed live via strace `SO_PEERCRED` plus an independent auditd EXECVE record
for the same pid — took down every worker session in the fleet in one shot, repeatedly, with zero warning.

## The pattern (four parts — all four are load-bearing, not optional extras)

**1. Isolate your OWN server on a dedicated `TMUX_TMPDIR`.** `orchestrator.service` sets `TMUX_TMPDIR` to a directory
no other process on the host has any reason to reference, so AO's fleet server is never the one a stray ambient
`tmux` command reaches. Every internal reference to "the fleet socket" (`tmux_spawn.py`'s `_TMUX_DEFAULT_SOCKET`,
liveness checks, etc.) must resolve through the SAME env var, or a stale-socket recovery routine could unlink the
wrong (unused) path instead of the real one.

**2. Unset all THREE of `TMUX_TMPDIR`, `TMUX`, and `TMUX_PANE` in anything you dispatch that might itself touch
tmux** — not just the tmpdir var. A dispatched worker's shell inherits the fleet's isolation env by default; that's
fine for the worker's own purposes (it never needs to talk to tmux), but becomes dangerous the moment the dispatched
TASK runs something that touches tmux itself (e.g. a quality-gate run executing a bats suite with its own tmux-fixture
teardown). The first fix attempt only unset `TMUX_TMPDIR` and was still insufficient — live strace verification showed
tmux ALSO auto-injects `$TMUX` into every pane (encoding the exact fleet socket path), and a NESTED tmux invocation
prioritizes `$TMUX` over `TMUX_TMPDIR` when deciding "am I already inside a session" — so a bare `tmux kill-server` run
inside a worker's own task still routed straight back to the fleet's control socket even with `TMUX_TMPDIR` gone.
`TMUX_PANE` needs clearing for the same class of reason. All three, every time — see `tmux_spawn.py`'s
`tmux_tmpdir_unset` construction for the exact shell fragment (`unset TMUX_TMPDIR TMUX TMUX_PANE; `).

**3. Self-heal the isolation directory before EVERY spawn, not just once at service start.** A systemd
`ExecStartPre=mkdir -p $TMUX_TMPDIR` only runs once when the service boots. If anything deletes that directory later
in the service's lifetime — confirmed live: a gap in an unrelated `/tmp` cleanup sweep — tmux does not error; it
silently falls back to the ambient default socket. Nothing re-creates the directory between service restarts, so this
produces an undetected split-brain fleet (some sessions correctly isolated, others silently back on the unprotected
ambient socket) that can persist for hours before anyone notices. Fix: `os.makedirs(tmux_tmpdir, mode=0o700,
exist_ok=True)` runs idempotently immediately before every single spawn attempt, cheap enough to pay on every call.

**4. Any TEST SUITE that spawns REAL tmux sessions must isolate its OWN `TMUX_TMPDIR`, never the ambient/inherited
one.** This is literally how the original incident was first discovered — an unscoped bats test fixture
(`test_slot_git_status_claim_heartbeat.bats`, before its fix) spawned real `tmux new-session`/`tmux kill-session`
calls against the ambient default socket with no isolation of its own. A later workspace-wide audit
(`ao_tmux_session_loss_mid_task_root_cause_2026_08_10`'s own 2026-08-19 sweep) found this same anti-pattern recurring
in `agent-orchestrator/dashboard/tests/e2e/run-e2e-backend-chat.sh` — check any NEW test that touches real tmux
sessions for the same gap; mocked `subprocess.run`/`tmux_spawn` calls are exempt (they never reach a real socket at
all).

## Applying this to a NEW tmux-based fleet service

If a future service on this host spawns its own tmux-managed worker fleet (the same shape as agent-orchestrator's),
it needs all four parts above from day one:

1. A dedicated `TMUX_TMPDIR`, never the ambient default — pick a directory name nothing else on the host would
   plausibly reference.
2. Every dispatched unit of work gets `TMUX_TMPDIR`/`TMUX`/`TMUX_PANE` unset in its own shell before it runs anything
   of its own.
3. A self-heal `mkdir -p` (idempotent, cheap) immediately before every spawn — never assume a service-start-time
   `ExecStartPre` is sufficient for the service's entire lifetime.
4. Every test that spawns a real (non-mocked) tmux session sets its own isolated `TMUX_TMPDIR` per-test.

Skipping any one of the four re-opens the exact failure mode this doc documents — they were each independently
discovered as a live incident, not derived analytically in advance.

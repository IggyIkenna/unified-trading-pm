---
doc_type: codex-runbook
title: Isolated agent-orchestrator sandbox for live worker-crash debugging
summary:
  "SSOT for spinning up a fully-isolated agent-orchestrator instance (own port, own DB/state, own empty backlog,
  AutoSpawn disabled) to reproduce and debug a worker crash live, without touching the production fleet. Built
  2026-08-11 as the next step once the tmux-level pane_dead diagnostic (agent-orchestrator@4c5a86bc3f) had proven the
  DeepSeek mid-task tmux-death signature is consistently empty on the production VM across multiple real crashes — the
  sandbox exists to catch the SAME class of death under live, non-invasive process instrumentation instead of guessing
  further from production logs alone. Two real gotchas hit live in the first run, both fixed in the setup script: (1) a
  worker spawned with `cwd` inside a repo carrying this workspace's CLAUDE.md ignores its boot prompt and tries to
  self-boot as a real fleet worker against the PRODUCTION VM — cwd must be a directory outside every instrumented repo;
  (2) a fixed-PID liveness check (`kill -0 <pid>`) produces false 'death' events, because Claude Code can legitimately
  rotate its own subprocess PID mid-task (observed at the ~180s mark, likely a compact-triggered restart) while the tmux
  session and pane stay healthy — watch session/pane liveness (`tmux has-session`), not a specific PID."
status: current
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [runbook, agent-orchestrator, deepseek, tmux, sandbox, debugging, root-cause]
related:
  [
    /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md,
    /plans/active/issues/fleet_wide_deepseek_crash_loop_undetected_2026_08_11.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/05-infrastructure/claude-code-settings-symlink.md,
  ]
created: "2026-08-11"
authoritative_for: [isolated agent-orchestrator debug-sandbox setup, live worker-crash instrumentation without ptrace]
referenced_by: []
owner: operator (ad-hoc — whenever a worker-crash investigation needs live reproduction, not just log archaeology)
cadence: on-demand (incident-triggered — not periodic)
verifier:
  "the sandbox's own /api/healthz responds on the configured port, and /api/accounts shows exactly the one sandbox
  account, before any worker is spawned into it"
last_executed: "2026-08-11"
last_reviewed:
code_refs:
  [
    agent-orchestrator/scripts/orchestrator/setup_debug_sandbox.sh,
    agent-orchestrator/scripts/orchestrator/watch_sandbox_slot_death.sh,
    agent-orchestrator/scripts/dev.sh,
  ]
---

# Isolated agent-orchestrator sandbox for live worker-crash debugging

## Why this exists

The production tmux-death investigation (`ao_tmux_session_loss_mid_task_root_cause_2026_08_10`,
`fleet_wide_deepseek_crash_loop_undetected_2026_08_11`) ruled out host OOM, cgroup-wide OOM, `KillMode=control-group`,
the orchestrator's own watchdog, and confirmed — across multiple real crashes since the `pane_dead` capture fix shipped
(agent-orchestrator@4c5a86bc3f) — that tmux's own death bookkeeping is consistently empty for this failure. That's a
real, converged result: the production VM's log surface is exhausted as a lead. The only path left is catching a crash
live, with process-level instrumentation, in an environment where doing so carries zero risk to real work.

## What the sandbox is

One agent-orchestrator backend instance, fully isolated from both the production fleet and any other fleet-member
instance on the same machine (e.g. an existing "Mac" host already running real worker slots):

- Own port (`ORCHESTRATOR_PORT`, default 8770 — matches the pre-existing "slot-2 DEV instance" convention in
  `scripts/dev.sh`'s own header).
- `ORCHESTRATOR_STANDALONE=true` — never reaches the central VM or the plan reconciler.
- Own `data/config/accounts.json` — deliberately ONE account, reusing an already-provisioned local credential (no new
  secrets minted for this).
- `AutoSpawnLoop` disabled by default (no `ORCHESTRATOR_AUTOSPAWN_ENABLED`) — nothing dispatches into it automatically;
  every spawn is a deliberate, single API call.

## Setup

```bash
bash scripts/orchestrator/setup_debug_sandbox.sh \
  --account-id deepseek-v4-pro \
  --account-env-file ~/.claude-accounts/deepseek-v4-pro.env
```

Refuses to overwrite an existing `.env.local` without `--force` — if this checkout already runs a real dev/fleet
instance, use a different checkout or `--force` only when certain.

## Running a live-crash reproduction attempt

```bash
bash scripts/dev.sh --backend-only

curl -s -X POST http://localhost:8770/api/slots/1/spawn \
  -H "Content-Type: application/json" \
  -d '{"account_id":"deepseek-v4-pro","boot_prompt":"<self-contained task, no file reads>","cwd":"'"$HOME"'/sandbox-debug-workspace"}'

bash scripts/orchestrator/watch_sandbox_slot_death.sh --session orch-slot-1
```

The boot prompt MUST be self-contained (no reliance on reading repo files) and the `cwd` MUST be the isolated workspace
directory the setup script created — see gotcha (1) below for what goes wrong otherwise.

## Gotchas (both hit live, first run, 2026-08-11)

### 1. `cwd` inside an instrumented repo → the worker ignores your prompt

A worker spawned with `cwd` pointed at `.tabs/N/agent-orchestrator` (or any repo carrying this workspace's CLAUDE.md)
picks up ambient "you are a fleet worker" instructions and tries to self-boot as a real slot — including attempting to
`POST` to the **production** AO VM's public IP with whatever token it finds locally. This is not a sandbox bug; it's
CLAUDE.md doing exactly what it's designed to do for a real worker. The fix is structural: the sandbox's `cwd` must be a
directory that has never had a CLAUDE.md in its ancestry. `setup_debug_sandbox.sh` creates `~/sandbox-debug-workspace/`
for exactly this — do not add a CLAUDE.md there.

### 2. Fixed-PID liveness checks produce false deaths

The underlying `node` process's PID legitimately rotated mid-task (observed at the ~180s mark on the first real run —
likely a context-compact-triggered internal restart) while the tmux session and pane stayed alive and the worker kept
producing real output. A `kill -0 <fixed-pid>` polling loop reads that rotation as a death. Track `tmux has-session`
(session-level liveness) as the actual death signal; track the pane's current PID only so you know what to check crash
logs against once a genuine session-level death happens. `watch_sandbox_slot_death.sh` does this correctly — do not
reintroduce a fixed-PID check.

## Teardown

```bash
tmux kill-session -t orch-slot-1   # if still running
rm -f .env.local data/config/accounts.json
```

Nothing else to clean up — `data/state/` under this checkout is the sandbox's own isolated DB, safe to leave or delete.

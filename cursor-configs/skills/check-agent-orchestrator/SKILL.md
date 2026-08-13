---
name: check-agent-orchestrator
description:
  Check the live agent-orchestrator's backlog/dispatch status AND fleet health (recent tmux/worker deaths, their full
  diagnostic payload, core-dump forensics) read-only — no dashboard JWT needed, no VM firewall change — via AWS SSM
  Session Manager running commands on the orchestrator VM itself. Reports per-task status (queued/dispatched/done) and
  which slot claimed what, optionally filtered by a plan-name substring; separately reports recent `tmux_session_lost`
  events with host/account/pane/spawn-concurrency/core-dump diagnostics per death. Never writes or mutates orchestrator
  state. Trigger on `/check-agent-orchestrator`, "check AO status", "check the agent-orchestrator", "is the orchestrator
  picking up my plan", "check if background agents are working on X", "check the backlog", "did AO dispatch this yet",
  "is the orchestrator stuck", "why did slot N die", "check for recent tmux deaths", "did we catch why that worker
  crashed".
---

# /check-agent-orchestrator — read-only live backlog/dispatch status check

Answers "has the orchestrator ingested my plan, and has a slot actually claimed a task from it yet" without needing the
dashboard's JWT or a route to the VM's public `:8765` (neither is available from a normal dev checkout — see
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Checking live backlog/dispatch status" for
the full SSOT this skill wraps).

## Why SSM instead of hitting the API directly

The orchestrator's public IP has no inbound rule for `:8765` by design (the API is meant to be reached from localhost or
the dashboard's own proxy, not the open internet), and the dashboard JWT (`HS256`, `data/config/users.json` or
`ORCHESTRATOR_JWT_SECRET`) isn't provisioned in dev checkouts. AWS SSM Session Manager's `send-command` runs a shell
command **on the VM itself**, so `curl localhost:8765/api/backlog` succeeds against the server's permissive local-read
mode (`auth.ALLOW_ANONYMOUS=True` per `agent-orchestrator/dashboard/API_REFERENCE.md`) — no inbound firewall change, no
JWT, and every call is CloudTrail-audited. This is genuinely read-only: only `GET` endpoints are ever called.

## Modes

This skill has no judgment-call findings to route — it only reads state and reports it (§3 below is an explicit
non-goal: it never diagnoses or restarts anything), so there is nothing for an operator to rule on either way.

- **Interactive (default, operator present)**: run the check, relay the result directly in the chat response.
- **Autonomous / AO-dispatched**: run the check the same way; write the result into the calling plan's Progress Log (or
  the dispatching task's own report) instead of a chat response, since there is no chat to relay it into. If the
  fleet-wide-stall signal (§2, sustained zero movement well past the 35-min window) fires while unattended, that IS a
  genuine operator-notification case — page it per the AO-alerting SSOT rather than silently logging it and moving on;
  everything else here is routine status, never an escalation.

## 1. Run the check

Run from the tab root (the directory that has `agent-orchestrator/` as a sibling of `unified-trading-pm/`, e.g.
`.tabs/<N>/`) — from inside any single repo checkout, including `unified-trading-pm`, the relative path below fails with
a plain `No such file or directory` (not an SSM/IAM error) since `agent-orchestrator` isn't nested under it.

```bash
bash agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh [substring-filter]
```

- No argument → full fleet-wide summary (total tasks + per-status counts).
- With an argument (e.g. a plan slug or todo-title fragment) → also lists every matching task's
  `id`/`status`/`dispatched_to`/`tier`/`plan_ref`/`title`.

**Requires**: AWS CLI already authenticated against account `427895769566` with `ssm:SendCommand` +
`ssm:GetCommandInvocation` (this workspace's slots normally already have this — verify with
`aws sts get-caller-identity` if the script errors on the SSM call). **No orchestrator credentials of any kind are
needed.**

## 2. Reading the result

- `status: queued` — ingested into the backlog, not yet claimed by a slot. Normal for anything pushed within the last
  ~35 min (`pm-pull.timer` ≤5 min + `PlanRegenLoop` ≤30 min) or sitting behind other queued work — a fleet with a deep
  backlog and a fixed slot count will have queued tasks waiting their turn; that's expected, not a fault.
- `status: dispatched`, `dispatched_to: <slot>` — a worker has claimed and is actively running the task.
- `status: done` — shipped.
- **Zero movement anywhere in the fleet-wide summary, sustained well past the 35-min window** — that's the actual
  stuck-orchestrator signal, not a single plan sitting `queued`. Cross-check against the known 2026-07-12 hardening gap
  noted in the codex SSOT (a checkout that looks current but whose running process has gone stale) before escalating —
  this skill only reports state, it doesn't diagnose or restart anything.

## 3. Checking for recent tmux/worker deaths (fleet health, not backlog status)

A different question from "is my plan dispatched" — "did a worker just die, and why." Same SSM access pattern, reads
`state.db`'s `activity_log` directly instead of the HTTP API:

```bash
bash agent-orchestrator/scripts/orchestrator/check-ao-recent-deaths.sh                # last 10 tmux_session_lost, any slot
bash agent-orchestrator/scripts/orchestrator/check-ao-recent-deaths.sh --slot 2       # last 10 for one slot
bash agent-orchestrator/scripts/orchestrator/check-ao-recent-deaths.sh --limit 30
```

Every SLOT-scope death (agent-orchestrator@d825c415c6 / @007995b3bd) now carries, automatically, no manual capture
script needed in advance: `burst_size` (1 = isolated, >1 = a tmux-SERVER-wide crash), `tmux_server_alive` (was the
server itself confirmed down, not just this pane), `host_snapshot` (load/RAM/swap at the moment of death),
`account_snapshot` (the dying slot's own rate-limit/overage/auth state), `pane_death_info`/`pane_tail` (tmux's own exit
diagnostic + scrollback, when the pane object survived — often empty, that's the harshest and most common signature, not
a capture failure), `concurrent_recent_spawns` (a spawn-storm proxy), and `core_dumps_found` (a real kernel-written
crash artifact, if the process was spawned after the `LimitCORE=infinity` fix AND died from a self-inflicted signal — an
external SIGKILL never produces one). Full field reference + what each one rules in/out:
`/codex/15-runbooks/tmux-death-diagnostics.md`. That doc also has the "how to safely apply a live `orchestrator.service`
change" procedure (the live installed unit is per-VM path-substituted, NOT identical to the repo template — a raw file
overwrite risks breaking the live service).

## 4. Hard constraints — do not extend this into a write path

- Never call `POST /api/backlog/regen` (or any other mutating endpoint) as part of a routine check — forcing an
  immediate regen is a deliberate, separate, operator-directed action, not something to fold into "just checking
  status."
- Never modify the target instance/region assumptions baked into the script without re-deriving them
  (`aws ec2 describe-addresses --public-ips 13.113.200.22 --region ap-northeast-1` if the VM is ever replaced) — the
  script's own header comment documents this.
- If SSM access itself fails (agent not registered, permissions revoked), that's an infra/credentials problem for the
  operator, not something to route around by opening a security-group rule or fabricating a token.

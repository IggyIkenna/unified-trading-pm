---
name: check-agent-orchestrator
description:
  Check the live agent-orchestrator's backlog/dispatch status read-only — no dashboard JWT needed, no VM firewall change
  — via AWS SSM Session Manager running `curl localhost:8765/api/backlog` on the orchestrator VM itself. Reports
  per-task status (queued/dispatched/done) and which slot claimed what, optionally filtered by a plan-name substring.
  Never writes or mutates orchestrator state. Trigger on `/check-agent-orchestrator`, "check AO status", "check the
  agent-orchestrator", "is the orchestrator picking up my plan", "check if background agents are working on X", "check
  the backlog", "did AO dispatch this yet", "is the orchestrator stuck".
---

# /check-agent-orchestrator — read-only live backlog/dispatch status check

Answers "has the orchestrator ingested my plan, and has a slot actually claimed a task from it yet" without needing a
dashboard JWT provisioned locally (see `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §
"Checking live backlog/dispatch status" for the full SSOT this skill wraps, including a 2026-08-15 correction: the VM's
public `:8765` is NOT actually firewalled off — verified directly reachable with a live auth gate — this skill's SSM
path is still the right choice below because it needs no credential at all, not because the port is closed).

## Why SSM instead of hitting the API directly

The dashboard JWT (`HS256`, `data/config/users.json` or `ORCHESTRATOR_JWT_SECRET`) isn't provisioned in most dev
checkouts, so a direct authenticated call isn't available without first minting one. AWS SSM Session Manager's
`send-command` runs a shell command **on the VM itself**, so `curl localhost:8765/api/backlog` succeeds against the
server's permissive local-read mode (`auth.ALLOW_ANONYMOUS=True` per `agent-orchestrator/dashboard/API_REFERENCE.md`) —
no credential of any kind needed, and every call is CloudTrail-audited. This is genuinely read-only: only `GET`
endpoints are ever called. (A caller that DOES already hold a bearer token can reach the API directly over HTTPS instead
— see the codex SSOT's correction for what's now confirmed reachable and a flagged, unresolved domain-vs-IP connectivity
anomaly.)

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

## 3. Hard constraints — do not extend this into a write path

- Never call `POST /api/backlog/regen` (or any other mutating endpoint) as part of a routine check — forcing an
  immediate regen is a deliberate, separate, operator-directed action, not something to fold into "just checking
  status."
- Never modify the target instance/region assumptions baked into the script without re-deriving them
  (`aws ec2 describe-addresses --public-ips 13.113.200.22 --region ap-northeast-1` if the VM is ever replaced) — the
  script's own header comment documents this.
- If SSM access itself fails (agent not registered, permissions revoked), that's an infra/credentials problem for the
  operator, not something to route around by opening a security-group rule or fabricating a token.

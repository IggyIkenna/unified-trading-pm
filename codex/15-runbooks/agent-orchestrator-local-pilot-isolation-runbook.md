---
doc_type: codex-runbook
title: agent-orchestrator local pilot isolation runbook
summary:
  What actually gets isolated when you launch a throwaway local agent-orchestrator instance for a pilot/experiment
  (ORCHESTRATOR_DB_PATH / ORCHESTRATOR_VM_ID / ORCHESTRATOR_STANDALONE and friends), what does NOT (STATE_DIR-rooted
  dedup/cursor files, the Slack webhook, every TuningDefaults field including pm_repo_path), and the checklist that
  makes a local pilot genuinely safe — written after a real 2026-07-29 incident where an unisolated local pilot's worker
  read a live slot's session, attempted an unauthenticated curl against the real production endpoint, and the always-on
  spawn-liveness watchdog free-looped kill+respawning real (billed) workers.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, local-dev, isolation, pilot, runbook]
related:
  [
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-30
authoritative_for: [what agent-orchestrator local-pilot isolation env vars actually isolate vs. don't]
referenced_by:
owner: infra (operator-run; no standing execution owner — event-driven)
cadence: event-driven — read before EVERY local pilot/experiment launch, not on a schedule
verifier:
  manual checklist below; the env-var table is verified against server/config.py's actual Field definitions, not assumed
last_executed:
  2026-07-29 pilot (the incident this runbook documents) — the checklist below did not exist yet at that time
last_reviewed: 2026-07-30
code_refs:
  [
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/main_agent_keeper.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/notifications/slack.py,
    agent-orchestrator/server/dedup_state.py,
  ]
execution:
  {
    owner: "infra (operator-run; no standing execution owner — event-driven)",
    cadence: "event-driven — read before EVERY local pilot/experiment launch, not on a schedule",
    verifier:
      "manual checklist below; the env-var table is verified against server/config.py's actual Field definitions, not
      assumed",
    last_executed:
      "2026-07-29 pilot (the incident this runbook documents) — the checklist below did not exist yet at that time",
  }
---

# agent-orchestrator local pilot isolation runbook

## Why this exists

On 2026-07-29 a local, supposedly-isolated agent-orchestrator pilot (testing DeepSeek/Claude blended routing —
`deepseek_claude_blended_provider_routing_2026_07_28.md`) caused two real incidents:

1. A misconfigured `ORCHESTRATOR_SERVER_URL` (unset, silently defaulting to the production port) meant every spawned
   worker's boot prompt pointed at the REAL production endpoint. One worker read another live slot's session looking for
   credentials, then attempted an unauthenticated curl against the real prod `/api/slots/26/heartbeat`. **Fixed in
   code** 2026-07-30 (`agent-orchestrator@fcc7f24`) — `config.server_url()` now refuses to hand out the
   production-default URL from a standalone instance instead of silently doing it; see that commit's plan Progress Log
   entry for the full incident writeup.
2. Because no worker could ever heartbeat (same root cause), the always-on `spawn-liveness watchdog`
   (`worker_liveness/_auth_failover.py`) — which is NOT gated by `ORCHESTRATOR_AUTOSPAWN_ENABLED` or any other
   pilot-isolation env var — treated every silent worker as a failed spawn and began killing + respawning them on a
   loop, including a slot that had already finished its real work correctly.

Item 1 is now closed in code. This runbook exists for the BROADER finding underneath both incidents: **several parts of
agent-orchestrator's runtime state are not scoped by the isolation env vars a reasonable person would expect them to
be** — `ORCHESTRATOR_DB_PATH` / `ORCHESTRATOR_VM_ID` / `ORCHESTRATOR_STANDALONE` isolate a lot, but not everything. Read
this BEFORE launching a local pilot, not after finding out the hard way.

## What actually isolates a local pilot

Every field below is a top-level `OrchestratorConfig` field with a real `validation_alias` — setting the env var
genuinely changes behavior (verified against `server/config.py`, not assumed from a docstring):

| Env var                           | What it scopes                                                                                                                                                                                                               |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ORCHESTRATOR_MODE=mock`          | Separate DB/backlog/accounts file NAMES by convention (`state.mock.db` etc.) — belt-and-suspenders with the explicit paths below, not a substitute for them                                                                  |
| `ORCHESTRATOR_DB_PATH`            | SQLite state DB location (slots, tasks, accounts, activity log)                                                                                                                                                              |
| `ORCHESTRATOR_BACKLOG`            | Which `backlog*.yaml` file `regen()` reads/writes                                                                                                                                                                            |
| `ORCHESTRATOR_ACCOUNTS`           | Which `accounts*.json` file account selection reads                                                                                                                                                                          |
| `ORCHESTRATOR_BACKENDS`           | Which `backends*.json` the dashboard's login screen offers                                                                                                                                                                   |
| `ORCHESTRATOR_USERS_JSON`         | Login credentials file                                                                                                                                                                                                       |
| `ORCHESTRATOR_CLAUDE_CONFIG_BASE` | Base dir for per-slot Claude transcript/session files                                                                                                                                                                        |
| `ORCHESTRATOR_CORS_ORIGINS`       | Which origins the API accepts browser requests from                                                                                                                                                                          |
| `ORCHESTRATOR_VM_ID`              | This instance's fleet identity (also drives `is_standalone()` — see below)                                                                                                                                                   |
| `ORCHESTRATOR_STANDALONE`         | Explicit standalone override (`true`/`false`) — see `config.is_standalone()`; a laptop with no `ORCHESTRATOR_VM_ID` is standalone by default, but an explicit override always wins                                           |
| `ORCHESTRATOR_SERVER_URL`         | The URL spawned workers' boot prompts point at — **mandatory on a standalone instance** since `agent-orchestrator@fcc7f24`; `server_url()` now raises rather than defaulting to the production URL                           |
| `ORCHESTRATOR_REVIEW_SLOTS=none`  | Stops the review-agent loop from claiming a slot (see the always-on gap below — this only stops the loop from acting, it does not disable it)                                                                                |
| `ORCHESTRATOR_AUTOSPAWN_ENABLED`  | Gates `AutoSpawnLoop` only — the loop that wakes an idle slot for QUEUED backlog work. Does **not** gate `AgentKeeper` (main agent) or `ensure_review_agents`, and does **not** gate the spawn-liveness watchdog — see below |

## What does NOT get isolated — the real gaps

**1. `STATE_DIR` — hardcoded to `<checkout>/data/state/`, no env override exists at all.**

`server/config.py`: `STATE_DIR = DATA_DIR / "state"` where `DATA_DIR = REPO_ROOT / "data"` — a plain module-level
constant computed from the on-disk checkout path at import time. There is no `ORCHESTRATOR_STATE_DIR` env var; setting
`ORCHESTRATOR_DB_PATH` does not move this. Every dedup-state file (`server/dedup_state.py`'s consumers — spawn-failed
alert dedup, branch-quarantine alert dedup, watchdog's context-burn-flagged set, git-staleness/unpushed-plans alert
throttles) lives under this SAME path regardless of `ORCHESTRATOR_VM_ID`/`ORCHESTRATOR_DB_PATH`.

**Consequence**: a pilot launched from the SAME on-disk checkout as a real interactive instance (e.g. the operator's own
slot worktree, rather than a genuinely separate clone) shares dedup-state with that real instance — a pilot's spawn
failures can suppress a real alert's dedup window, or vice versa. Launching from a genuinely separate checkout (a fresh
`git clone`, or a slot the operator isn't actively using interactively) avoids this; setting env vars alone does not.

**2. `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` — read from raw `os.environ` at module import time, no override mechanism.**

`server/notifications/slack.py`: `_WEBHOOK_URL = os.environ.get("AGENT_ORCHESTRATOR_SLACK_WEBHOOK", "")`. If this is set
in the shell a pilot is launched from (as it would be on a box also used for real interactive work), the pilot inherits
it and any Slack-alerting code path (spawn-failure pages, account-rotation alerts, branch-quarantine alerts, watchdog
flap alerts) sends REAL messages to the REAL ops channel. The test suite guards against exactly this
(`tests/conftest.py`'s `_no_real_slack_webhook` autouse fixture) — a real pilot process has no equivalent protection.
**Explicitly `unset AGENT_ORCHESTRATOR_SLACK_WEBHOOK` before launching a pilot**, or verify it was never set in that
shell.

**3. Every `TuningDefaults` field — compiled-in class defaults, env-free BY DESIGN (2026-07-18 ruling), no override
mechanism exists.**

Per CLAUDE.md: "Orchestrator `tuning.*` knobs are env-free (`TuningDefaults`) — change the code default + redeploy;
`.env.local` silently no-ops." This is deliberate (SSOT-in-code, no env-drift between VMs) but it means **several
function docstrings in this codebase currently claim an env override that does not work** — a stale-docs trap a pilot
operator can fall into. `pm_repo_path` is the specific field this todo's incident report named:

```python
# server/regen_backlog_from_plan.py:203 (docstring, BEFORE the 2026-07-30 fix below)
def _pm_repo_path() -> Path:
    """Resolve PM repo path.
    Priority:
      1. ORCHESTRATOR_PM_REPO_PATH env var (explicit override)   # ← does not exist; reads .tuning.pm_repo_path
      2. REPO_ROOT/../unified-trading-pm (standard workspace layout)
    """
    custom = config.get_config().tuning.pm_repo_path  # a TuningDefaults field — no AliasChoices, no env binding
```

Fixed (docstring corrected to describe the real resolution, no behavior change) in the same commit that added this
runbook — see `server/regen_backlog_from_plan.py`, `server/blocked_reconcile.py`, `server/ci_reconcile.py`,
`server/routes/backlog.py`. In practice `pm_repo_path` defaults to `""`, which falls through to
`REPO_ROOT.parent / "unified-trading-pm"` — a path relative to the checkout, so it naturally resolves to whichever
`unified-trading-pm` clone sits next to the `agent-orchestrator` checkout the pilot is running from. This is
incidentally safe for the common case (a slot worktree with sibling repos) but is a CODE default, not something a pilot
can override per-run via env — if you need a pilot to read a DIFFERENT PM checkout than its sibling, that requires
editing the `TuningDefaults` class default, not setting an env var.

**4. `AgentKeeper` (main agent) and `ensure_review_agents` (review-agent loop) run regardless of
`ORCHESTRATOR_AUTOSPAWN_ENABLED` — by design, not a bug, but a pilot operator needs to know this.**

`server/main_agent_keeper.py`'s own comment: "The main agent is ALWAYS on (operator 2026-06-23) — it is no longer
env-disableable." `ORCHESTRATOR_AUTOSPAWN_ENABLED=false` (the default) only disables `AutoSpawnLoop` — the loop that
wakes an idle slot for queued backlog work. It does NOT stop `AgentKeeper` from attempting to spawn a main agent on
every tick, and does NOT stop `ensure_review_agents` from claiming a review slot (`ORCHESTRATOR_REVIEW_SLOTS=none` stops
it from claiming one, but the loop itself still runs and checks).

**5. The spawn-liveness watchdog (`worker_liveness/_auth_failover.py`) — also not gated by
`ORCHESTRATOR_AUTOSPAWN_ENABLED`, and is the mechanism that free-looped in the 2026-07-29 incident.** It runs as part of
`WorkerLivenessKicker`'s tick, which has no enable flag of its own at all (gated only by `interval_seconds > 0` and tmux
being on `PATH`). The `ORCHESTRATOR_SERVER_URL` fix (`agent-orchestrator@fcc7f24`) closes the SPECIFIC failure mode that
triggered this in the incident, but the watchdog itself is still always-on regardless of pilot-isolation env vars — a
genuinely stuck/unreachable worker for any OTHER reason will still trigger kill+respawn churn during a pilot.

## The checklist — before launching a local pilot

1. **Launch from a checkout the operator is not using interactively right now** — a fresh clone, or a currently-idle
   slot worktree. Do not run a pilot from a slot with real in-flight work; `STATE_DIR` isolation gap #1 above means
   dedup-state collides otherwise.
2. **Set `ORCHESTRATOR_SERVER_URL` explicitly** (e.g. `http://localhost:<pilot-port>`) — since `fcc7f24`, the process
   refuses to spawn a worker without it on a standalone instance; this is now enforced, not just advised.
3. **`unset AGENT_ORCHESTRATOR_SLACK_WEBHOOK`** in the launching shell, or confirm it was never set there.
4. **Set `ORCHESTRATOR_DB_PATH` / `ORCHESTRATOR_BACKLOG` / `ORCHESTRATOR_ACCOUNTS` / `ORCHESTRATOR_USERS_JSON` /
   `ORCHESTRATOR_CLAUDE_CONFIG_BASE`** to pilot-dedicated paths (a throwaway `/tmp` or scratch dir) — not the checkout's
   real `data/` files.
5. **Set `ORCHESTRATOR_VM_ID` to an obviously-throwaway id** (never a real fleet id, never blank if you want
   `is_standalone()` to definitely read True regardless of `ORCHESTRATOR_STANDALONE`).
6. **Expect `AgentKeeper` and `ensure_review_agents` to still run** (gap #4) — either accept a real (but isolated, per
   step 4) account spawning a main/review agent, or watch for "no usable account" warnings if none has headroom.
7. **Expect the spawn-liveness watchdog to still run** (gap #5) — if pilot workers go silent for any reason, they WILL
   be killed and respawned; this is not a pilot-only behavior you can turn off short of killing the whole process.
8. **If you need a DIFFERENT `pm_repo_path`** than the checkout-relative default (gap #3), edit the `TuningDefaults`
   class default in `server/config.py` for the pilot run — there is no env var that does this, despite what some
   docstrings said before 2026-07-30.

## What's still genuinely safe without extra care

- `ORCHESTRATOR_MODE=mock` + the four path overrides in step 4 give real DB/backlog/accounts isolation — a pilot cannot
  corrupt the real fleet's state through these.
- `is_standalone()`-gated behavior (`/api/backends` = self only, `/api/fleet/summary` = self only, `/api/vms/<id>/*`
  = 404) means a standalone pilot never lists or reaches another real VM over the fleet API.
- Since `fcc7f24`, a standalone instance can no longer silently hand a spawned worker's boot prompt the production URL —
  the single most damaging failure mode from the 2026-07-29 incident is closed at the code level, not just documented
  here.

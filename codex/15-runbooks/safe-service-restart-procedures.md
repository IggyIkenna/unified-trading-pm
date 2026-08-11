---
doc_type: codex-runbook
title: Safe service restart / recovery procedures (Agent Orchestrator first, more services to follow)
summary:
  "SSOT for 'a critical service looks broken/idle — what to check, in what order, before assuming it needs a manual
  restart.' One `##` section per service, each with a real diagnostic order and a real-fix-vs-not-the-fix table. Agent
  Orchestrator is the first section (2026-08-07, built from a live full-fleet-idle incident): the universal lesson is
  diagnose account/dependency headroom BEFORE touching systemd/tmux, since a 'dead-looking' fleet is very often blocked
  on an external precondition a restart does not fix. Extend this ONE doc with a new section per service — do not fork a
  second restart-guide doc."
status: current
nature: process
asset_group: [ao, cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [runbook, agent-orchestrator, restart, recovery, autospawn, accounts, self-healing, disaster-recovery]
related:
  [
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
created: "2026-08-07"
authoritative_for:
  [safe restart/recovery diagnostic order for critical workspace services, starting with agent-orchestrator]
referenced_by: []
owner: operator (ad-hoc — whenever a critical service looks idle/broken)
cadence: on-demand (incident-triggered — not periodic)
verifier:
  "for AO: /api/accounts shows every configured account's status + reset timestamps checked BEFORE any restart action; a
  genuine restart claim cites systemctl status showing the service was actually down"
last_executed: "2026-08-07"
code_refs:
  [
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/main_agent_keeper.py,
    agent-orchestrator/server/orm.py,
    agent-orchestrator/server/routes/accounts.py,
  ]
audience: operator / dev
last_updated: "2026-08-07"
execution:
  {
    owner: "operator (ad-hoc — whenever a critical service looks idle/broken)",
    cadence: "on-demand (incident-triggered — not periodic)",
    verifier:
      "for AO: /api/accounts shows every configured account's status + reset timestamps checked BEFORE any restart
      action; a genuine restart claim cites systemctl status showing the service was actually down",
    last_executed: "2026-08-07",
  }
---

# Safe service restart / recovery procedures

> **Scope**: this is the SSOT for "a critical service looks broken/idle — what do I check, in what order, before
> assuming it needs a manual restart." **One `##` section per service.** Agent Orchestrator is the first section (built
> 2026-08-07 from a real live incident, not written speculatively). When another critical service earns a validated
> procedure, add it here as a new `##` section in the same shape — do not fork a second restart-guide doc.

## Universal principle (applies to every section below)

**Diagnose before you restart.** A service that looks "dead" (0 active workers, nothing happening, a red dashboard) is
very often NOT crashed — it is blocked on an external precondition (account/quota headroom, a dependency being down, a
config gate) that a restart does not fix, and can make WORSE (killing a live-but-slow worker, losing in-flight context).
Confirm the actual failure mode before touching systemd/tmux/processes. Every section below follows the same shape:
**when to use it → step-by-step diagnostic order (cheapest/most-likely-culprit first) → a real-fix-vs-not-the-fix table
→ a verified-incident log** (a step in this doc that has never been exercised against a real incident is a guess, not a
runbook — keep the incident log honest).

---

## Agent Orchestrator

### When to use this

Trigger: the dashboard (`agent-orchestrator.odum-research.com`) shows 0 agents connected / all slots idle or killed /
blocked-questions piling up / backlog not advancing — especially right after anything that could have killed the VM's
live processes (EC2 stop/start or reboot, an instance-type resize, a manual `systemctl restart orchestrator`, an OOM
kill). Read-only checks below need no dashboard JWT — same SSM-based approach as `/check-agent-orchestrator`
(`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Checking live backlog/dispatch status").

### Step 0 — is this actually broken, or just capacity-blocked? (always check this FIRST)

This is the single most common false alarm — check account headroom before touching anything else:

```bash
curl -s http://localhost:8765/api/accounts | python3 -m json.tool
```

Read every account's `status` + `five_hour_pct` / `weekly_pct` / `five_hour_resets_at` / `weekly_resets_at`:

- **`status: rate_limited`** — self-clearing. Check `five_hour_resets_at`. Nothing to do but wait; AutoSpawn/AgentKeeper
  retry every tick (60s default) and pick it up the moment it clears.
- **`status: disabled`** — **operator-directed, does NOT auto-clear** on its own (`agent-orchestrator/server/orm.py`
  `AccountRow.account_status` docstring: `"disabled" = operator-disabled`, " Intentionally separate from
  `rate_limited_until`"). Check `weekly_resets_at` — if it is still in the future, the account is correctly disabled
  (genuinely still inside its capped week) and must **NOT** be manually re-enabled: re-enabling doesn't restore
  provider-side quota, it just wastes a spawn attempt and risks a provider-side flag on the account. Only once
  `weekly_resets_at` has actually passed is it safe to clear: `POST /api/accounts/<id>/enable`
  (`agent-orchestrator/server/routes/accounts.py`) — this is an explicit operator action, confirm before calling it.
- **`status: auth_failed`** — stale OAuth token; clears automatically after a cooldown re-probe, or on the account's
  next successful `/heartbeat`.
- **API-tier accounts** (DeepSeek etc.) — check `balance_is_available` / `balance_usd`. A negative/zero balance needs a
  top-up, not a restart.

**If EVERY account is simultaneously unusable**, the fleet is correctly idle and self-heals the moment the _nearest_
reset passes — read each account's `weekly_resets_at`/`five_hour_resets_at` for the real ETA (not "now," not "never").
Do not restart anything while waiting; a restart does not change provider-side quota state.

### Step 1 — is the orchestrator process itself even running?

```bash
systemctl status orchestrator --no-pager -l
# "Active: active (running) since <time>" confirms systemd already restarted it (Restart=always in the unit).
```

If it is genuinely NOT running, that is the real restart case: `sudo systemctl restart orchestrator` — safe, all state
lives in `data/state/state.db` (see Step 3, nothing needs "replaying").

### Step 2 — is the background self-healing fleet actually running inside the process?

```bash
journalctl -u orchestrator --since "<boot/restart time>" --no-pager \
  | grep -E "started|AutoSpawnLoop|AgentKeeper|TmuxPruner|PlanRegenLoop"
```

Expect `AutoSpawnLoop started`, `AgentKeeper started`, `TmuxPruner started`, `WorkerLivenessWatchdog`,
`DeepSeekBalancePoller started` — all within the first ~5s of process start. If AutoSpawn's own switch is off:

```bash
systemctl show orchestrator -p Environment | tr ' ' '\n' | grep AUTOSPAWN
# expect ORCHESTRATOR_AUTOSPAWN_ENABLED=true
```

Full 5-gate trigger contract (queue non-empty, no active worker, account headroom, slot configured, not in cooldown):
`/codex/04-architecture/agent-orchestrator-autospawn.md`.

### Step 3 — the task queue is NOT something you manually "replay"

The backlog (`queued`/`dispatched`/`done` tasks) lives in `data/state/state.db` and survives a process/VM restart
untouched. `PlanRegenLoop` re-scans plans on its own interval and reconciles; `AutoSpawnLoop` claims queued+claimable
tasks the moment a slot is free and an account has headroom. **There is no manual "replay the queue" step in this
architecture** — if tasks still aren't dispatching once accounts are healthy and the process is up, that itself is the
bug to chase (Step 4), not a missing replay action.

### Step 4 — review agents / the "main" agent specifically

"Review agents" (`ensure_review_agents` in `agent-orchestrator/server/autospawn.py`) and the "main" agent (AgentKeeper,
`agent-orchestrator/server/main_agent_keeper.py`) use the **exact same account-selection path** as regular slot workers
— they are blocked by the exact same Step-0 headroom check, not a separate mechanism.
`agentkeeper_review_failed`/`agentkeeper_review_succeeded` activity rows and
`AgentKeeper tick: MainAgentTickSummary(...)` log lines report their own status every tick — read the `skip_reason`
field before assuming a bug (`no usable account` is the same Step-0 cause, not a defect).

### Step 5 — models / account-tier config sanity check

`accounts.json` (read by `select_account_for_spawn`) drives which provider/tier each spawn uses; per-role model defaults
live in `unified-trading-pm/agents/<role>.md` frontmatter (`/codex/06-coding-standards/model-tier-selection.md` is the
SSOT). A resize/reboot does not touch either file — if models look wrong post-restart, that is a config-drift question,
not a restart-recovery one; do not conflate the two.

### Step 6 — an escalation is stuck, queued forever, or re-dispatching in a loop

**Read `last_error` FIRST. It names the reason verbatim.** This is one curl and it answers the question; do not start
from `/api/accounts`, and do not SSM onto the box to hand-query SQLite until it has failed you.

```bash
curl -s localhost:8765/api/escalations/active | jq -r '.[] | "\(.escalation_id) \(.repo) \(.status) attempts=\(.attempts) \(.last_error // "-")"'
```

Interpreting it — the four reasons that actually occur, and what each means:

| `last_error`                                | What it means                                                                                         | Real fix                                                                                  |
| ------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `repo '<x>' already active on another slot` | The per-repo collision guard. One escalation per repo at a time; the rest of that repo's walls queue. | Nothing — it drains. Only investigate if the HOLDER is itself a zombie (see below).       |
| `no headroom account (Claude or DeepSeek)`  | Genuinely no usable account in EITHER pool.                                                           | Step 0. Wait for the nearest reset.                                                       |
| `tmux_spawn.spawn failed: [Errno 28] ...`   | **The host's `/tmp` is full.** Not an account or slot problem at all.                                 | `df -h /tmp`; `tmpfs-disk-cleanup.timer` should be sweeping — check it is enabled/active. |
| `unresolved after Nmin — re-escalated`      | The watchdog gave the wall to a worker, the wall stayed red, it re-fired.                             | Look at the WALL, not the queue. The queue is behaving correctly.                         |

**Quota is NOT the default explanation here** — sonnet-tier escalation dispatch falls back to DeepSeek
(`escalation_deepseek_fallback_2026_08_05` in `server/escalation.py`), and `_quota_adaptive_fraction` routes it **100%**
to DeepSeek when zero Claude accounts are usable. A fully-exhausted Claude pool should therefore keep dispatching. If it
is not, the reason is in `last_error`, not in `/api/accounts`.

**Zombie holder check.** A `dispatched` row is a spawn RECEIPT, not a booted worker. Cross-check its `escalation_id`
against `/api/agents`: if the id is absent there, no worker ever registered, and that row may be holding its repo's
collision-guard slot with nothing behind it. Same shape as an agent row showing `status: active` alongside a terminal
`exit_reason` (`reaped-stale` / `lifecycle-complete`).

**The state DB is `agent-orchestrator/data/state/state.db`.** Query it read-only (`sqlite3 "file:...state.db?mode=ro"`)
only after the API has failed you.

### Real fix vs. not-the-fix

| Symptom                                                                                                        | Real fix                                                                                                                  | NOT the fix                         |
| -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| `systemctl status orchestrator` shows `inactive`/`failed`                                                      | `sudo systemctl restart orchestrator`                                                                                     | waiting                             |
| AutoSpawnLoop/AgentKeeper never logged "started" at all since boot                                             | restart the service; check the `autospawn.conf` drop-in                                                                   | flipping account status             |
| 0 agents, but ≥1 account shows `status: healthy` with real headroom                                            | genuine bug — read `spawn-failed`/`autospawn_failed` activity rows for the real error (tmux / boot-prompt render failure) | waiting indefinitely                |
| 0 agents, EVERY account `rate_limited`/`disabled`/negative-balance                                             | wait for the nearest `*_resets_at`                                                                                        | restarting anything                 |
| A slot's tmux session is dead, queue has claimable work, an account has headroom, but nothing spawns for >2min | check flap backoff (1h after 3 spawns with no task claimed) via the slot's recent activity rows                           | assuming AutoSpawn itself is broken |
| Escalations queued with huge `attempts` (100+), fleet otherwise healthy                                        | read `last_error` on the row (Step 6) — it names the reason verbatim                                                      | inspecting `/api/accounts` first    |
| Escalation dispatch failing fleet-wide, accounts + slots both fine                                             | `df -h /tmp` on the AO box — a full tmpfs fails `tmux_spawn` with `[Errno 28]`                                            | restarting the orchestrator         |

### Verified incident log

- **2026-08-10 — fleet-wide escalation-dispatch failure caused by a FULL `/tmp`, misdiagnosed as a quota outage.** Every
  Claude account was simultaneously `rate_limited`/`disabled` (nearest reset ~44h out), which made "quota" the obvious
  and WRONG answer — the diagnosing agent spent ~20 tool calls there. Two facts contradicted it: the DeepSeek pool was
  healthy ($46.87, `balance_is_available: true`) and `_quota_adaptive_fraction` routes sonnet-tier work 100% to DeepSeek
  when no Claude account is usable, so dispatch should have continued; and the queue rows' own `last_error` named the
  real causes verbatim — `repo '<x>' already active on another slot` for the PM SIT walls, and
  `tmux_spawn.spawn failed: [Errno 28] No space left on device` for four dispatches at 16:41-16:44. Root cause: the AO
  box's `/tmp` is an **8 GiB tmpfs** and it had filled to 100% (15 MiB free) — an agent's ad-hoc `gsutil ls -r` over a
  whole prod tick-data bucket streaming multi-GiB parquet through it, plus 41 leaked `bats-claim-hb-test-*` tmux fixture
  sessions. `tmux_spawn` allocates under `/tmp`, so every escalation dispatch died and re-queued; the PM SIT walls
  reached 190+ attempts on that treadmill. **Fixes:** `tmpfs-disk-cleanup.timer` (30-min sweep,
  `scripts/self-hosted-runners/`) since the pre-existing `systemd-tmpfiles-clean` ran only daily; the BATS fixture leak
  fixed at source; and subprocess `gsutil`/`gcloud storage`/`aws s3` object calls now hard-blocked by the PreToolUse
  guardrail, forcing UTL `cloud_interface`. **`last_error` is now exposed on `/api/escalations/active`** — it was
  DB-only at the time, which is why the cheap diagnostic path could not see the answer it already held. Step 6 above
  exists because of this incident.

- **2026-08-07 — full fleet outage after an AO-box instance-type resize (`m8i.4xlarge`→`m8i.2xlarge`, stop → modify →
  start).** The stop/start killed the VM's tmux server and every live worker process — expected and harmless.
  `orchestrator.service` (`Restart=always`) came back within ~10s and AutoSpawn/AgentKeeper immediately began retrying
  every slot. The retries kept failing not because of the resize but because, coincidentally, **all 8 configured
  accounts were simultaneously unusable**: 2 DeepSeek API-tier accounts at negative balance, `sub-a-ikenna`
  mid-5h-window, and `sub-b-iggy2london`..`sub-f-odum2default` each still genuinely inside their own weekly-cap window
  (`weekly_resets_at` ranging from later the same day to 6 days out). Confirmed via `/api/accounts`
  - the `weekly_resets_at`/`five_hour_resets_at` fields — **not** the `rate_limited_until` field, which looked stale
    (dates in the past) but is legacy/informational for the `rate_limited` status only; `disabled` status is governed by
    `weekly_resets_at`, is operator-directed, and does not auto-clear on `rate_limited_until` passing (this is exactly
    the trap Step 0 above exists to prevent — reading `rate_limited_until` alone would have wrongly suggested those
    accounts were stuck/bugged and safe to force-enable). **Fleet self-recovered the moment `sub-a-ikenna` crossed its
    `five_hour_resets_at` (11:19:59 UTC) — zero manual intervention required or taken**, confirmed via a live poll loop
    watching `/api/accounts` + `tmux ls` until a session reappeared: `sub-a-ikenna` flipped `rate_limited`→`high_usage`
    at 11:20:57;
    `AutoSpawnLoop: RESUMED slot=8 task=tradfi_satellite_ao_dispatch_batch6-002 session=e72382bd-a3d1-416a-ae84-85656714dec1`
    fired at 11:21:57 — **the pre-outage task resumed on its ORIGINAL Claude session, context intact, exactly the "no
    manual replay" behavior Step 3 describes**; a review agent spawned on slot 1 at 11:22:38 (`ensure_review_agents`)
    and the main agent spawned at 11:22:47 (`AgentKeeper: spawned main agent agt-21da46`) — both also on `sub-a-ikenna`,
    both also fully automatic. Total elapsed from reset to a fully-repopulated fleet: under 3 minutes, no operator
    action.

---

## \<next service — add here\>

No other critical service has a validated safe-restart procedure yet. When one does, give it its own `##` section
following the shape above: when-to-use, a real diagnostic order (cheapest/most-likely-culprit first, not a guess), a
real-fix-vs-not-the-fix table, and a verified-incident log entry once the procedure has actually been exercised against
a real incident.

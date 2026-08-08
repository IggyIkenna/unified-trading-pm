---
doc_type: codex-ssot
title: agent-orchestrator — scheduled-job dispatch mechanism
summary: >-
  SSOT for the AO scheduled-job dispatch layer: the 8 systemd timers, the plan_health modes they POST, the status model
  (dispatched/queued/no_capacity/quarantined/timeout/error), which statuses page, the capacity queue
  (ScheduledJobQueueRow), the 503-classification allowlist (BENIGN_503_RE), and the HARD RULE that a git pull does NOT
  reinstall a live timer unit.
status: current
nature: ssot
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [orchestrator, scheduled-jobs, plan-health, timers, systemd, dispatch, capacity-queue, status-model]
related:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-08-08
last_reviewed: 2026-08-08
authoritative_for: scheduled-job dispatch
referenced_by: []
owner: ""
code_refs:
  - agent-orchestrator/server/plan_health.py
  - agent-orchestrator/server/autospawn.py
  - agent-orchestrator/server/state_store/scheduled_jobs.py
  - agent-orchestrator/server/orm.py
  - agent-orchestrator/scripts/install-plan-reconciler-timer.sh
  - agent-orchestrator/scripts/install-ag-closeout-auditor-timer.sh
  - agent-orchestrator/scripts/install-na-eligibility-auditor-timer.sh
  - agent-orchestrator/scripts/install-docs-reconcile-timer.sh
  - agent-orchestrator/scripts/install-context-scout-timer.sh
  - agent-orchestrator/scripts/install-escalation-queue-reconciler-timer.sh
  - agent-orchestrator/scripts/install-cefi-reconciliation-timer.sh
  - agent-orchestrator/scripts/install-cefi-mtds-smoke-timer.sh
  - agent-orchestrator/scripts/scheduled_job_already_ran.py
---

# agent-orchestrator — scheduled-job dispatch mechanism

## Overview

Eight systemd timer units on the orchestrator VM drive daily planning-cleanup and audit work. Each timer fires a shell
script that POSTs to `POST /api/plan-health/dispatch` (server/plan_health.py). The server spawns a worker on a free
slot, records the attempt in `ScheduledJobRunRow` (SQLite), and — on no-capacity — queues the work in
`ScheduledJobQueueRow` for AutoSpawn to drain later.

**The dashboard's "Scheduled Jobs" panel** (`GET /api/scheduled-jobs/recent`) reads `ScheduledJobRunRow` joined to the
live `AgentRow` to show real-time run status. A row labelled `dispatched` is a SPAWN RECEIPT, not a completion —
`agent_exit_reason == "lifecycle-complete"` on the joined `AgentRow` is the only value that means done.

---

## The 8 timers

Each installer (`scripts/install-<name>-timer.sh`) creates a systemd **`--user`** `.service` + `.timer` pair under
`~/.config/systemd/user/` and copies `scripts/scheduled_job_already_ran.py` to `~/.local/bin/`. The already-ran guard
(`--job <job_name>`) keyed on `agent_exit_reason == "lifecycle-complete"` (or a still-in-flight `queued`/`dispatched`
row) prevents duplicate work on the same day.

| Timer service name                    | mode param             | job_name                      | Sharded?                                    | Cadence (UTC)          | curl --max-time | systemd TimeoutStartSec |
| ------------------------------------- | ---------------------- | ----------------------------- | ------------------------------------------- | ---------------------- | --------------- | ----------------------- |
| `plan-reconciler.service`             | `reconcile`            | `plan_reconciler`             | Yes (Sun–Fri); unsharded Saturday `all` run | every 2 h (even hours) | 5950 s          | 6000 s                  |
| `ag-closeout-auditor.service`         | `ag_closeout`          | `ag_closeout_auditor`         | Yes (10 tranches)                           | every 2 h (even hours) | 7200 s          | 21600 s                 |
| `na-eligibility-auditor.service`      | `na_eligibility`       | `na_eligibility_auditor`      | Yes (10 tranches)                           | every 2 h (odd hours)  | 7200 s          | 21600 s                 |
| `docs-reconciler.service`             | `docs_reconcile`       | `docs_reconciler`             | No                                          | hourly                 | 5950 s          | 6000 s                  |
| `context-scout.service`               | `context_scout`        | `context_scout_auditor`       | No                                          | hourly                 | 5950 s          | 6000 s                  |
| `escalation-queue-reconciler.service` | `escalation_reconcile` | `escalation_queue_reconciler` | No                                          | every 3 h              | 5950 s          | 6000 s                  |
| `cefi-reconciliation-auditor.service` | `cefi_reconciliation`  | `cefi_reconciliation_auditor` | No                                          | every 2 h (even hours) | 5950 s          | 6000 s                  |
| `cefi-mtds-smoke-tester.service`      | `cefi_mtds_smoke`      | `cefi_mtds_smoke_tester`      | No                                          | every 2 h (odd hours)  | 5950 s          | 6000 s                  |

The sharded jobs (plan-reconciler, ag-closeout, na-eligibility) POST one request per tranche. Non-sharded jobs POST
once. The `job_name` field in each POST is the dedup key for the capacity queue and the already-ran guard.

### HARD RULE: `git pull` does NOT reinstall a timer

A `git pull` updates the installer script in the repo but does NOT regenerate the `~/.local/bin/<job>-dispatch.sh`
script or the `~/.config/systemd/user/<job>.service`+`.timer` pair already on the VM. Every fix that changes an
installer's behaviour (`--max-time`, `TimeoutStartSec`, `OnCalendar`, tranche list, the already-ran guard) is INERT
until someone re-runs the installer:

```bash
bash scripts/install-<job>-timer.sh          # NO sudo — see below
```

This exact gap has cost two incident todos on the issue doc that first documented these timers. Verify after every
installer change by checking the live unit: `systemctl --user cat <job>.timer` and confirming
`~/.local/bin/<job>-dispatch.sh` carries the updated values.

### These installers take NO sudo (2026-08-08)

They were system units (`/etc/systemd/system`, `/usr/local/bin`) until 2026-08-08, which made every re-install
permanently `[OPERATOR]`-tagged — a human in the loop for a task that is mechanical, idempotent and reversible. Nothing
they do requires privilege: the dispatch scripts only `curl localhost:8765` and read the operator's own `.env.local`.
They were root-only because of WHERE they wrote, not what they did. **Running one under `sudo` now hard-fails** — it
would resolve `$HOME` to `/root` and install into root's user manager, which nobody lingers, producing a timer that
looks installed and never fires.

Shared preamble: `agent-orchestrator/scripts/lib/user-timer-env.sh` (exports `BIN_DIR`/`UNIT_DIR`, defaults
`XDG_RUNTIME_DIR`, refuses root, and fails loudly if the user manager is unreachable). Lingering — what keeps a user
manager alive with no login session — is already enabled on the central VM by `bootstrap_vm.sh` STEP 7.5b2, which has
installed the reflog-reset guard as `systemctl --user` units by this same mechanism since before these timers existed;
these 8 were simply the outliers. On a fresh host it is one command, once: `sudo loginctl enable-linger <operator>`.

A user unit cannot order against the system-scoped `orchestrator.service`, so the old `After=`/`Wants=` pair is gone,
replaced by an `ExecStartPre` gate that polls `/api/healthz` for up to 300 s. That is strictly stronger than what it
replaced: `After=` only ordered the START and never waited for the backend to answer, so the boot race predates the
change — and failing in `ExecStartPre` means no spurious `timeout` row reaches `/api/scheduled-jobs/report`.

**Governance note.** `[OPERATOR]` has been carrying two unrelated meanings: "a human must DECIDE" (delete-safety, wallet
keys, VM launches, 1.0.0 graduation) and "a human must type a password". Only the first is governance. This change
removes the second from the timer family entirely; the same test — _is this blocked on judgment, or merely on
credentials?_ — is worth applying to any other standing `[OPERATOR]` todo.

---

## Status model

A `ScheduledJobRunRow` records one dispatch attempt per tranche. Statuses:

| Status        | Meaning                                                                                                                                      | Pages?  |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| `dispatched`  | Worker spawned (spawn receipt — NOT completion; check `agent_exit_reason` for that)                                                          | No      |
| `queued`      | Server full at fire time; row inserted in `ScheduledJobQueueRow`; AutoSpawn drains later                                                     | No      |
| `no_capacity` | **LEGACY** — only reachable by an ad-hoc caller that omits `job_name` in the POST body                                                       | No      |
| `quarantined` | Hard spawn refusal (e.g., branch-state quarantine, dead-clone artifact)                                                                      | **Yes** |
| `timeout`     | curl `--max-time` exceeded before HTTP response — almost always an API-stall artifact (`dispatch_agent_id=NULL`); NOT a per-dispatch failure | **Yes** |
| `error`       | Other HTTP/server error                                                                                                                      | **Yes** |

`SCHEDULED_JOB_FAILURE_STATUSES = frozenset({"quarantined", "timeout", "error"})` — these three trigger Slack pages.
`dispatched`, `queued`, and `no_capacity` do not.

**`no_capacity` is now LEGACY for all scheduled callers.** Since agent-orchestrator@5087f30, any POST that includes
`job_name` queues on no-capacity instead of dropping. A caller that omits `job_name` still gets the old `no_capacity`
drop — this is the deliberate opt-out for operator one-offs that want fail-fast.

**`timeout` in the dashboard is almost always an API-stall artifact, not a per-dispatch failure.** Every measured
`timeout` row over 08-01..08-06 carried `dispatch_agent_id=NULL` (no worker was ever spawned). The pattern: systemd
timers fire on schedule regardless of server health; the dispatch curl hangs against a stalled API; `--max-time` expires
→ HTTP 000 → `status=timeout`. The root class is `orchestrator_db_pool_exhaustion_state_poll_stall` (SQLite lock
storms), not individual dispatch errors.

---

## Capacity queue

When a scheduled dispatch hits no-capacity and the caller supplies `job_name`, the server inserts a
`ScheduledJobQueueRow` instead of recording `no_capacity`.

**Schema** (`server/orm.py`):

- `queue_key` — primary key: `"<job_name>:<tranche or '-'>:<YYYY-MM-DD>"` (the dedup key)
- `job_name`, `tranche` — job identity
- `status`: `queued → dispatched | abandoned`
- `abandoned` — the job's calendar day has passed; a daily audit for yesterday is worthless

**Drain**: AutoSpawn's tick drains the queue AFTER CI-escalation work (CI walls outrank daily audits).
`_SCHEDULED_DRAIN_PER_TICK = 2` limits each tick to 2 rows so a multi-day backlog doesn't flood the fleet at once. The
dedup PK ensures a multi-hour outage with hourly retries produces exactly ONE row per `(job, tranche, day)` — never a
herd of stale audits.

**An hourly fire does not retry past the day boundary.** A `queued` row is abandoned once its `<YYYY-MM-DD>` key is in
the past. This prevents a 23-hour outage from releasing 23 copies of yesterday's audit when the server recovers.

---

## 503-classification allowlist (`BENIGN_503_RE`)

Each dispatch script classifies 503 responses with an allowlist grep:

```bash
BENIGN_503_RE="no free configured slot|no headroom|protected_live_peer"
# ...
503) if printf '%s' "${BODY}" | grep -qE "${BENIGN_503_RE}"; then
       STATUS="no_capacity"   # capacity-limited — benign
     else
       STATUS="quarantined"   # hard refusal — real failure
     fi
```

**Why an allowlist (not a denylist):** The server returns many 503 variants, and only three specific phrases are
genuinely benign capacity-limit responses. A denylist of "bad" phrases would need to enumerate every possible
hard-refusal message (unmaintainable and incomplete). An allowlist is explicit: any 503 body that does NOT match these
three phrases is treated as a real failure and recorded as `quarantined`.

**The incident that codified this (2026-08-04..06):** A dead `instruments-service.broken-empty-clone` artifact was
causing hard spawn refusals with "branch-state quarantine" in the 503 body. The pre-@5087f30 classifier filed these as
`no_capacity` (silent/benign), masking 42 genuine spawn failures over 3 days. The allowlist approach makes new refusal
phrases fail loudly by default rather than silently sliding into the benign bucket.

---

## Capacity sizing

`scheduled_task_slot_reserve()` (`server/config.py`) reserves a floor of worker slots for scheduled jobs (default 4,
raised from 2 on 2026-08-04). The reserve interacts with `ci_escalation_slot_reserve()` and
`ORCHESTRATOR_FLEET_WORKER_CAP`:

```
free_for_backlog = total_slots - ci_reserve - sched_reserve
```

`MAX_CONCURRENT_TRANCHES` (per sharded auditor, also 4) must be ≤ `sched_reserve` or a single sharded job's own batch
can structurally starve itself even with zero external contention. The 2026-08-04 root-cause was reserve 2 vs batch
width 3.

---

## Observability

- **`GET /api/scheduled-jobs/recent`** — last N dispatch attempts, joined to live `AgentRow` for
  `agent_status`/`agent_exit_reason`/`done_evidence`. The `realRunOutcome` field on each row
  (`running | complete | went_stale | unknown`) is derived from this join and is the right field to key on, not raw
  `status`.
- **`scripts/orchestrator/check-scheduled-job-health.sh`** — CLI script for measuring scheduled-job health from the VM
  (queries the live `state.db` via the API; avoids SSM truncation by aggregating on the VM side).
- **`GET /api/agents/{id}/log`** — returns the durable Claude JSONL transcript for a run, or falls back to
  `capture-pane`. A `reaped-stale` run IS recoverable via this endpoint if its `claude_session_id` was captured (all 32
  reaped-stale agents over 08-04..06 carried one).

---
doc_type: codex-ssot
title: agent-orchestrator — scheduled-job dispatch mechanism
summary: >-
  SSOT for the AO scheduled-job dispatch layer: the 10 systemd timers, the plan_health modes they POST, the status model
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
last_reviewed: 2026-08-10
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
  - agent-orchestrator/scripts/install-ci-reconciler-timer.sh
  - agent-orchestrator/scripts/install-data-pipeline-alerts-reconciler-timer.sh
  - agent-orchestrator/scripts/install-ao-watchdog-timer.sh
  - agent-orchestrator/scripts/scheduled_job_already_ran.py
---

# agent-orchestrator — scheduled-job dispatch mechanism

## Overview

Ten systemd timer units on the orchestrator VM drive planning-cleanup, audit, and CI-health work. Each timer fires a
shell script that POSTs to `POST /api/plan-health/dispatch` (server/plan_health.py). The server spawns a worker on a
free slot, records the attempt in `ScheduledJobRunRow` (SQLite), and — on no-capacity — queues the work in
`ScheduledJobQueueRow` for AutoSpawn to drain later.

**The dashboard's "Scheduled Jobs" panel** (`GET /api/scheduled-jobs/recent`) reads `ScheduledJobRunRow` joined to the
live `AgentRow` to show real-time run status. A row labelled `dispatched` is a SPAWN RECEIPT, not a completion —
`agent_exit_reason == "lifecycle-complete"` on the joined `AgentRow` is the only value that means done.

---

## The 10 timers

Each installer (`scripts/install-<name>-timer.sh`) creates a systemd **`--user`** `.service` + `.timer` pair under
`~/.config/systemd/user/` and copies `scripts/scheduled_job_already_ran.py` to `~/.local/bin/`. The already-ran guard
(`--job <job_name>`) keyed on `agent_exit_reason == "lifecycle-complete"` (or a still-in-flight `queued`/`dispatched`
row) prevents duplicate work in the same window (the same DAY for every job except `ci_reconciler` (`--window hour`) and
`data_pipeline_alerts_reconciler` (`--window 6hour`); see below).

| Timer service name                        | mode param                       | job_name                          | Sharded?                                    | Cadence (UTC)              | curl --max-time | systemd TimeoutStartSec |
| ----------------------------------------- | -------------------------------- | --------------------------------- | ------------------------------------------- | -------------------------- | --------------- | ----------------------- |
| `plan-reconciler.service`                 | `reconcile`                      | `plan_reconciler`                 | Yes (Sun–Fri); unsharded Saturday `all` run | every 2 h (even hours)     | 5950 s          | 6000 s                  |
| `ag-closeout-auditor.service`             | `ag_closeout`                    | `ag_closeout_auditor`             | Yes (10 tranches)                           | every 2 h (even hours)     | 7200 s          | 21600 s                 |
| `na-eligibility-auditor.service`          | `na_eligibility`                 | `na_eligibility_auditor`          | Yes (10 tranches)                           | every 2 h (odd hours)      | 7200 s          | 21600 s                 |
| `docs-reconciler.service`                 | `docs_reconcile`                 | `docs_reconciler`                 | No                                          | hourly                     | 5950 s          | 6000 s                  |
| `context-scout.service`                   | `context_scout`                  | `context_scout_auditor`           | No                                          | hourly                     | 5950 s          | 6000 s                  |
| `escalation-queue-reconciler.service`     | `escalation_reconcile`           | `escalation_queue_reconciler`     | No                                          | every 3 h                  | 5950 s          | 6000 s                  |
| `cefi-reconciliation-auditor.service`     | `cefi_reconciliation`            | `cefi_reconciliation_auditor`     | No                                          | every 2 h (even hours)     | 5950 s          | 6000 s                  |
| `ci-reconciler.service`                   | `ci_reconcile`                   | `ci_reconciler`                   | No                                          | every 15 min, hourly guard | 5950 s          | 6000 s                  |
| `data-pipeline-alerts-reconciler.service` | `data_pipeline_alerts_reconcile` | `data_pipeline_alerts_reconciler` | No                                          | every 60 min, 6h guard     | 5950 s          | 6000 s                  |
| `ao-watchdog.service`                     | `ao_watchdog`                    | `ao_watchdog`                     | No                                          | daily, 00:47 UTC           | 5950 s          | 6000 s                  |

**RETIRED 2026-08-15 — `cefi-mtds-smoke-tester.service` (mode `cefi_mtds_smoke`, job_name `cefi_mtds_smoke_tester`,
every 2h odd hours).** Operator decision: the underlying `/data-pipeline-check-mtds` sweep it dispatched has no
`--asset_group` scoping (it walks the FULL MVP matrix — every asset_group, not just CeFi — per
`mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md`), so firing it every 2 hours repeatedly consumed
real VM spend and the shared Tardis N=1 concurrency slot (confirmed live 2026-08-15: a `pipeline-e2e-check-mtds-*`
driver VM launched by this dispatch chain ran continuously for 3+ hours, its per-shard
`mtds-backfill-cefi- pipelinecheck-*` sub-VM launches starving every other real Tardis-backed backfill in the fleet).
Deemed disproportionate to the check's value at this cadence — the skill remains fully usable as a manual, occasional,
operator-run check (no code removed from `/data-pipeline-check-mtds` itself). Removed live 2026-08-15:
`systemctl --user disable --now cefi-mtds-smoke-tester.timer` + deleted both unit files from `~/.config/systemd/user/`
on the orchestrator VM; `agent-orchestrator/scripts/install-cefi-mtds-smoke-timer.sh` deleted from the repo (its sole
purpose was installing this timer). The `mode="cefi_mtds_smoke"` dispatch handler in `plan_health.py` and the
`agents/cefi_mtds_smoke_tester.md` role are left intact (unused without a timer, but not deleted — no code/test cleanup
was in scope for this decision).

**Track B health audit (2026-08-20)**: every job in this table (minus the retired one above) was audited for the same
review-gate-starves-escalation failure class `plan_reconciler` had before its 2026-08-16 graduation to direct-push —
none reproduce it; every job ships direct via `quickmerge.sh --agent --files`, none route through a review-branch/PR
gate. Two smaller gaps found instead: `context_scout_auditor`/`docs_reconciler` run with above-fleet-average
reaped-stale rates (not yet root-caused), and `escalation-queue-reconciler` is structurally blind to external GitHub
PR-backlog state (would not itself have caught the plan_reconciler problem). Full per-job table + both follow-ups:
`/plans/active/issues/ao_scheduled_jobs_health_audit_findings_2026_08_20.md`.

**`ci-reconciler` is the one job whose already-ran guard runs `--window hour`, not the default `--window day`** (added
2026-08-10). Its timer fires every 15 minutes and the guard admits at most ONE successful run per clock hour, so the job
is "hourly, with up to 4 attempts" rather than four sweeps an hour — a fire that hits no capacity, an error, or a
quarantine simply retries 15 minutes later instead of waiting for the next hour. This shape is deliberate and matches
neither of the other two: the daily auditors retry hourly until the DAY's run lands (CI health is not a daily property),
and `escalation-queue-reconciler` uses a wide 3-hourly no-retry tick (a missed CI sweep is NOT equally fine 3 hours
later — a promotion deadlock compounds, since the blocked diff grows while it stands). Motivation: on 2026-08-10 a
`unified-trading-pm` LDR→main promotion sat deadlocked 22 h / 1180 commits on an unconvergeable ratchet gate while 17
`sit_failure` escalation dispatches re-polled it, and `ldr-docs-gate` sat red 10+ h emitting zero Slack — neither class
is covered by `ci_failure_watcher.py`'s automated recovery, and `/ci-reconcile` was the only reconcile skill in the
workspace with no standing timer. See
`/plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` and
`/plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`.

**`data-pipeline-alerts-reconciler` uses a THIRD guard shape, `--window 6hour`** (added 2026-08-10, same day as
`ci-reconciler`): its timer fires every 60 minutes and the guard admits at most ONE successful run per 6-hour bucket
(00/06/12/18 UTC), so the job is "every 6 hours, with up to 6 attempts" — deliberately **1/6th `ci-reconciler`'s
cadence** (4x/day vs. 24x/day). The `/data-pipeline-alerts-reconcile` skill was, like `/ci-reconcile` before it, the
only reconcile skill in the workspace with no standing timer — its own doc explicitly framed it as "on-demand ... not a
permanent standing watcher." The slower cadence relative to `ci-reconciler` is deliberate, not an oversight: the
underlying DP_* Cloud Run Job monitors already page reactively into `agents/data_pipeline_failure.md` via
`/api/escalate` for anything needing code judgment, so this sweep's job is catching what that reactive path structurally
cannot (routing/dedup bugs, self-heal actuator gaps, already-self-resolved noise, registry-unregistered events) — a
class that does not compound hour-by-hour the way an unconvergeable CI promotion deadlock does.

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

## PM-repo dead-lock correlation + duplicate-tranche dispatch guard (2026-08-19)

Two gaps existed for the sharded per-tranche scheduled auditors (`reconcile`/`na_eligibility`/`ag_closeout`) that a
dead-dispatch `AgentRow` alone couldn't close, closed together in `agent-orchestrator@bfe8fb28a0`
(`/plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md`):

1. **PM-repo lock auto-clear** (`server/plan_reconciler_dead_lock_sweep.py`, `PlanReconcilerDeadLockSweep`, a daemon
   thread wired in `server.py` alongside `PlanReconcilerLivenessCanary`). `plan_reconciler`'s own skill stamps
   `locked_by: plan_reconciler (<dispatch_id>) since <ts>` on its
   `plans/active/issues/plan_reconciler_findings_<tranche>_<date>.md` findings doc and the skill's "never auto-unlock"
   policy means nothing clears it if the worker dies mid-run — this was measured to block 6 tranches' daily
   reconciliation for 5 days (2026-08-10 through 2026-08-15) before a human noticed. The sweep correlates the doc's
   `locked_by:` dispatch id against AO's own `AgentRow.exit_reason`, and auto-clears the PM-repo lock ONLY once the
   dispatch is confirmed `exit_reason="reaped-stale"` AND the AgentRow's own `finished_at`/`registered_at` is older
   than `tuning.plan_reconciler_dead_lock_max_age_hours` (default 8h) — **never a hand-typed timestamp inside the
   doc**, which live docs were found to carry inconsistently (some omit it entirely). A still-live dispatch (no
   `exit_reason` yet, or a non-`"reaped-stale"` exit) is never touched. The actual git write happens in a throwaway
   scratch clone under `config.STATE_DIR`, never the shared `tuning.pm_repo_path` checkout (which stays read-only by
   convention — every other reader of that path only ever reads it) — clone, edit the two frontmatter lines, commit,
   push, delete; a rejected push (genuine concurrent edit) is abandoned for that tick rather than ever force-pushed,
   re-evaluated fresh next tick.
2. **Duplicate-tranche dispatch guard** (`_tranche_dispatch_gate` in `server/plan_health.py`, alongside the existing
   report-mode-only `_report_dispatch_gate`). `reconcile`/`na_eligibility`/`ag_closeout` are deliberately exempt from
   `_report_dispatch_gate` (their own scheduled call, not promotion-throttled) — but that exemption also meant zero
   duplicate-dispatch protection for the identical `(mode, tranche, day)`, confirmed live twice as a real edit
   collision (`agt-053eab`/`agt-3eb42b` on `tranche="ao"`, 2026-08-16; `agt-72629d`/`agt-9095fb` on `tranche="defi"`,
   2026-08-18, `mode="na_eligibility"`). `_tranche_dispatch_gate` correlates a same-day same-`(mode, tranche)`
   `plan_health_dispatch_initiated` activity row (now also logging `tranche`) to its `AgentRow`; if no
   `plan_health_result` has posted yet AND the AgentRow isn't `archived`, the new dispatch coalesces onto the existing
   one instead of spawning a collision. Unlike the report throttle, there is no `force=` bypass — a genuinely-live
   sibling dispatch is never safe to double-spawn onto.

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

**A `quarantined` dispatch retries on a DIFFERENT slot, with an exclude-set** (operator-approved 2026-07-28, landed
`agent-orchestrator@e69f528`): mirrors the pre-existing "benign:" TOCTOU-race retry, but a branch-quarantine failure
never spawns a tmux session on the target slot (the gate runs before `tmux_spawn.spawn`), so unlike the benign-race
case — where the racing session naturally makes the slot look busy on retry — `_pick_free_slot` would otherwise keep
re-picking the SAME quarantined slot every attempt. Fixed by threading an explicit exclude-set through the retry loop.
The scheduled-dispatch family (`ag-closeout-auditor`/`na-eligibility-auditor`'s `ao`/`ci` tranches) also has its
auto-heal ahead-commit-age recency guard narrowed from 900s to 300s specifically for this one-shot family, trading
some quarantine-detection margin for fewer missed daily tranches.

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

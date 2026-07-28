---
doc_type: issue
title:
  The 4 daily-scheduled planning-cleanup jobs (plan-reconciler / docs-reconciler / ag-closeout-auditor /
  na-eligibility-auditor) had zero dashboard or Slack visibility for weeks; today's real run diagnosed 2 genuine
  failures a systemd exit code alone could not show
summary: >-
  Operator asked why the 4 overnight scheduled Claude skills failed (naming ag_closeout_auditor), and asked for full
  dashboard tracking (start/end timestamps, progress, logs — same as workers/escalations) plus Slack alerts on
  scheduled-job failure, built out in full under /autonomous. Root cause investigation (SSM into the planning VM,
  `systemctl status` + `journalctl` for each of today's 4 runs) found two genuinely distinct problems layered on top of
  the pre-existing zero-visibility gap: (1) `na_eligibility_auditor`'s 07:00 UTC run genuinely FAILED (`systemctl
  status` showed `Active: failed`) — a curl `TIMEOUT`/`HTTP:000` past its own already-correctly-configured 2400s
  `--max-time`, the same failure class already root-caused and fixed for `plan-reconciler`/`docs-reconciler` on
  2026-07-24 but never re-measured/re-validated for the newer sharded auditor family (its own service comment already
  said "no measurement of a single-tranche run exists yet"). (2) `ag_closeout_auditor`'s 05:06 UTC run silently
  partial-failed — 2 of 9 tranches (`ao`, `ci`) hit a `branch-state quarantine (FM5/FM7)` safety gate on the target
  slot's `unified-trading-pm` worktree ("1 commit(s) too recent (460s old)") with a failed auto-heal, but the dispatch
  script's own `case` statement bucketed that 503 under the EXACT SAME "no capacity today" branch as a genuinely benign
  503 (the fleet just being busy) — so `systemctl status` showed `status=0/SUCCESS` for the whole service despite 2
  tranches never actually running. `plan-reconciler` and `docs-reconciler`'s runs that day were genuinely benign 503s
  (no free slot/headroom, self-resolving on tomorrow's retry) — but were equally invisible anywhere but journalctl, same
  as everything else. Built the full fix: a durable dispatch-attempt record for every tranche of every run, a
  real-vs-benign status distinction, a dashboard panel with per-run "view log" (reusing the existing agent log viewer),
  and a Slack alert that fires ONLY on the genuine-failure statuses (not the routine no-capacity case) — not spec'd,
  fully built and shipped.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, observability, scheduled-jobs, slack-alerting, systemd, bug]
related: [ao_slot_agentrow_liveness_desync_and_escalations_ui_gap_2026_07_27]
created: 2026-07-28
priority: P1
parent_epic: orchestrator_master
source:
  "operator interactive session, slot 3, /autonomous — asked why the 4 overnight scheduled planning-cleanup jobs failed
  (naming ag_closeout_auditor) and to build full dashboard tracking + Slack alerting for them, in full, not just spec'd"
assigned_vm: NA
execution_scope: local-only
estimate_class: brand-new
drift_direction: advance-code
depends_on: []
resolved_by: slot-3 (interactive), agent-orchestrator (see Evidence)
locked_by:
---

> **✅ ARCHIVED 2026-07-28** (plan_health gate remediation — `check_terminal_status_archived` ratchet). Fix fully
> shipped + verified per the Verification section below (agent-orchestrator backend/dashboard/dispatch-script changes,
> full QG green, live VM redeploy confirmed). ACKED-INTO-CODE per `/codex/11-project-management/issue-doc-lifecycle.md`
> — archiving now rather than leaving it dual-tracked in `plans/active/issues/`. The two Follow-ups items below
> (na-eligibility-auditor timeout re-tuning; branch-state-quarantine friction awareness) remain open observations, not
> blocking this issue's own resolution — no other active plan/issue currently owns them.

# Scheduled-job (plan-reconciler / docs-reconciler / ag-closeout-auditor / na-eligibility-auditor) observability + Slack alerting

> **🟢 ARCHIVED 2026-07-28** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule.

## What I found — root cause per job, from today's actual runs

Checked via AWS SSM (read-only) into the planning VM (`i-0c9b283b31d6b5ca7`): `systemctl status <job>.service` +
`journalctl -u <job>.service` for each of the 4 timers' most recent (2026-07-28) firing.

| Job                      | Fire time (UTC) | systemd result           | Real cause                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------ | --------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `plan-reconciler`        | 01:00           | `0/SUCCESS`              | Genuinely benign: `no free configured slot to dispatch plan_health check onto` (HTTP 503) — the fleet was busy; the timer's own next-day retry is the correct, working response.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `docs-reconciler`        | 03:01           | `0/SUCCESS`              | Genuinely benign: `no headroom setup-token account available` (HTTP 503) — same as above, a different capacity dimension (account headroom vs slot).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `ag-closeout-auditor`    | 05:06           | `0/SUCCESS` (misleading) | **Silent partial failure.** Tranches `ao` and `ci` hit `spawn failed: branch-state quarantine (FM5/FM7), auto-heal failed: … unified-trading-pm:1-commit(s)-too-recent(460s-old)-REFUSED-kept-quarantined`. The dispatch script's `case "${CODE}"` bucketed this 503 under the SAME "NO CAPACITY today" branch as an ordinary 503, so `FAILED` never got set and the whole service reported SUCCESS despite 2/9 tranches never running.                                                                                                                                                                                                                                                                                                                                |
| `na-eligibility-auditor` | 07:00           | `1/FAILURE`              | **Genuine failure**, visible in `systemctl status` (unlike the other 3) but nowhere else: `curl` `TIMEOUT/CONNECT FAILURE` (`HTTP:000`) on multiple tranches — its `--max-time 2400`/`TimeoutStartSec=2450` pair was ALREADY the corrected value (matching the 2026-07-24 fix applied to `plan-reconciler`/`docs-reconciler`), yet still timed out. The script's own comment already flagged this: "no measurement of a single-tranche run exists yet" — this sharded-family timeout budget was carried over from the OLD all-in-one-worker shape and never re-validated after the 2026-07-26 sharding change. Not re-tuned in this session (needs real multi-run timing data first — flagged as a follow-up below, now that runs are durably recorded going forward). |

**The deeper, pre-existing problem all 4 shared**: none of this was visible anywhere but the VM's local `journalctl` —
not the dashboard, not Slack. An operator would only ever find out by SSM-ing in and reading service logs by hand
(exactly what this investigation did). `agent-orchestrator`'s existing `AgentRow`/`AgentView` machinery (used for
regular workers/escalations, with full start/end/log tracking) never covered a dispatch attempt that failed BEFORE a
worker was even spawned — a `no_capacity`/`quarantined`/`timeout` outcome creates no `AgentRow` at all.

## Fix — built in full (not spec'd)

**Backend** (`agent-orchestrator`):

- **`ScheduledJobRunRow`** (`server/orm.py`) — new table, one row per tranche per dispatch attempt: `job_name`,
  `tranche`, `started_at`/`finished_at`, a real `status` (`dispatched` / `no_capacity` / `quarantined` / `timeout` /
  `error`), `detail`, and `dispatch_agent_id` (the `AgentRow.agent_id` a successful dispatch actually spawned, for
  deep-linking).
- **`POST /api/scheduled-jobs/report`** (`server/routes/agents.py`, internal-secret-authed, mirrors the existing
  `/api/plan-health/result` pattern) — each dispatch script POSTs its outcome here.
- **`GET /api/scheduled-jobs/recent`** — the dashboard's read surface (default 48h window).
- **`notify_scheduled_job_failed`** (`server/notifications/slack.py`) — pages ONLY on the genuine-failure statuses
  (`quarantined` / `timeout` / `error`); `dispatched` and `no_capacity` are deliberately silent (the latter is a
  routine, self-resolving, expected outcome — paging on it would just be noise every time the fleet is busy).
- **12 new tests** (`tests/test_scheduled_jobs.py`): state_store round-trip, recency-window filtering, the auth gate,
  and — the decisive coverage — Slack fires on `quarantined`/`timeout`/`error` and stays silent on
  `dispatched`/`no_capacity`, for every status individually, plus a Slack-outage-must-not-fail-the-report case.

**The 4 dispatch scripts**
(`scripts/install-{plan-reconciler,docs-reconcile,ag-closeout-auditor,na-eligibility-auditor}-timer.sh` — these are the
checked-in INSTALLERS that heredoc-generate the actual `/usr/local/bin/*-dispatch.sh` scripts systemd runs; editing +
re-running the installer is the existing, designed-for-this, idempotent deploy path, not a new mechanism):

- Capture a start timestamp; on HTTP 200, extract `dispatch_id` from the response body.
- **On HTTP 503, inspect the response body** for `"branch-state quarantine"` to split `quarantined` (real problem) from
  `no_capacity` (benign) — the exact distinction the old script couldn't make. `ag-closeout-auditor` and
  `na-eligibility-auditor`'s sharded per-tranche loop does this per tranche. `plan-reconciler`/`docs-reconciler` do it
  for their single dispatch call.
- Report every outcome via a `python3`/`urllib` POST (verified against embedded quotes/newlines in the detail field — a
  hand-built `printf` JSON string would have broken on exactly the quarantine message's own punctuation) — always
  best-effort (`|| true`), never blocking the pre-existing exit-code decision (unchanged: only `timeout`/`error` still
  fail the systemd unit, matching the ORIGINAL behavior exactly, so no operational risk from this change).

**Dashboard** (`ScheduledJobsPanel`, `dashboard/src/layout.tsx`, wired into all 3 layout branches same as the
Escalations panel from the prior session): job + tranche, color-coded status, relative time, duration
(`fmtDurationBetween`), and a "Log" button on dispatched runs that reuses the EXISTING agent log viewer via a minimal
stub object — `LogViewerModal`'s agent scope only ever reads `target.agent_id` (verified by reading its full
implementation before building this), so no second log viewer was needed.

## Verification

- Full repo `bash scripts/quality-gates.sh`: 1839 server tests + 154 dashboard tests, `basedpyright`/`ruff`/`tsc`/
  `prettier` all clean.
- Every dispatch script's OUTER install-script syntax AND the fully-rendered INNER dispatch-script syntax verified with
  `bash -n` (rendered by substituting the real `PM_REPO`/`ENV_LOCAL` values, not just eyeballing the heredoc).
- The `python3`/`urllib` report call's JSON-safety verified with a live smoke test against a detail string containing
  embedded quotes and a newline — confirmed valid JSON out, confirmed the expected connection-refused exception is
  swallowed (`|| true`) without propagating.
- Deployed to the live VM: pulled the backend/dashboard commit, confirmed `uvicorn --reload` picked it up
  (`GET /api/healthz`, `/api/state`, `/api/scheduled-jobs/recent` all 200, zero new tracebacks in
  `journalctl -u orchestrator.service`), then re-ran all 4 `install-*-timer.sh` installers on the VM (the sanctioned,
  idempotent redeploy path) and confirmed each installed script (a) contains the new `scheduled-jobs/report` call, (b)
  passes `bash -n`, and (c) left the timer's `OnCalendar`/next-fire-time UNCHANGED (no schedule disruption).

## Follow-ups

- **`na_eligibility_auditor`'s per-tranche timeout budget needs re-measurement**, now that real dispatch-attempt timing
  data will accumulate in `ScheduledJobRunRow` going forward — the 2400s `--max-time` was carried over unmeasured from
  the sharding change; bump it (or diagnose why a single tranche exceeds 40 minutes) once a few more data points exist.
  Not done in this session — no real timing data existed yet to act on.
- **The `branch-state quarantine (FM5/FM7)` friction on `ag-closeout-auditor`/`na-eligibility-auditor`'s target slots**
  is a `unified-trading-pm` worktree commit-recency safety gate (`server/autospawn.py`) doing its job during a period of
  very high commit velocity on that repo (this session alone landed ~10 commits to it) — not a bug, but worth knowing
  this is why a scheduled audit's `ao`/`ci` tranches specifically can intermittently miss a day. Not changed in this
  session (a genuine safety mechanism, not something to loosen without separate operator direction).

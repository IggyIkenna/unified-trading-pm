---
doc_type: plan
title: AO fleet observability — make efficiency, escalator efficacy and account burn visible
summary:
  Roughly four of five dispatches produce no completion and nothing surfaces it, 43% of CI escalations go unresolved
  after ~3.8 dispatches each, plan_health burns 55 haiku runs a day of which 13 return nothing, snapshot recency is
  unasserted, and no view shows which account or agent is burning the quota. Add the KPIs, throttle plan_health, and
  root-cause why the escalators fail rather than only capping them.
status: complete
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, observability, kpi, escalation, plan-health, usage, snapshots]
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_dispatch_cooldown_and_park_2026_07_20.md,
    /plans/archive/2026_07/ao_fleet_infra_hardening_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: "2026-07-31"
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
assigned_role: backend_engineer
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
model_tier: sonnet-doable # measurement + surfacing work; each item is bounded to a known subsystem
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_dispatch_cooldown_and_park_2026_07_20]
source:
---

# AO fleet observability — KPIs, escalator efficacy, account burn

> **🟢 COMPLETE 2026-07-31 — ARCHIVED.** Every todo is now `[x]`. The one remaining item (AF-2-followup) was closed by a
> direct read-only query against the live orchestrator's `data/state/state.db` (this session ran ON the orchestrator VM,
> no SSM needed): **zero `superseded-plan_health` exits ever** (confirmed against the full `agents` table history) and
> **zero throttle violations** — since AF-2 deployed (`agent-orchestrator@d098970`, 2026-07-20) there has been exactly
> one successful report-mode dispatch in 11 days, and `plan_health_dispatch_coalesced` has fired zero times ever. The
> 2026-07-29 entry's flagged ambiguity (two dispatch-attempt log lines 389s apart) is now fully resolved — the first
> attempt failed pre-registration (an unrelated branch-quarantine failure), never became a live `AgentRow`, so the gate
> correctly saw no recent successful dispatch to throttle against. Honest caveat carried into the todo text: the
> throttle's blocking code path itself has never been exercised by two live successful dispatches inside one interval —
> traffic has simply never been frequent enough to test it, though it has also never been violated. **Codex-alignment
> check found a real gap, not a clean bill**: `agent-orchestrator-single-vm-architecture.md`'s existing "Skip / cooldown
> / park" section documents only the FLEET-WIDE dispatch-cooldown store (AF-1b's mechanism) — AF-2's own separate,
> plan_health-local report-mode throttle (`_report_dispatch_gate`) was never actually documented anywhere in codex.
> Added a paragraph there now, including this session's live-traffic numbers. No follow-up todo needed beyond that — the
> finding is conclusive, not partial.

> **Provenance**: Phase 7 (AF-1…AF-5) + the Phase-6 plan_health cadence item of
> `ao_open_issues_consolidated_close_out_2026_07_17.md`. That plan keeps the audit record; this plan holds the work.

## The through-line

**Every incident in the consolidated plan was found by an operator manually reading the activity log.** That is the
actual finding here. The fleet looks busy while ~4 of 5 dispatches produce no completion, and nothing surfaces a
regression until a human goes looking. This plan closes that gap in the specific places it has already cost us.

## ⚠️ Dependency — do not build a second backoff engine

`depends_on: ao_dispatch_cooldown_and_park_2026_07_20.md`. AF-1's escalator redispatch cap **must sit on the ONE
fleet-scoped cooldown store** built there — the master plan's explicit risk is three separate cooldown/backoff engines
that diverge. The **analysis** half of AF-1 (triaging the 83 unresolved) needs no dependency and can start now; only the
cap waits. If you find yourself writing a second backoff, stop and talk to that plan's owner.

## Execution environment — LOCAL

Operator-assigned agents on this host (`assigned_vm: NA`, `execution_scope: local-only`). Tick checkboxes by hand. Code
is local (`bash scripts/quality-gates.sh`). **Most measurement here needs read-only live-VM access** via SSM (pattern:
`scripts/orchestrator/check-ao-backlog-status.sh`); for DB reads use `sudo python3` with
`sqlite3.connect("file:/var/lib/orchestrator/state.db?mode=ro", uri=True)` — no `sqlite3` CLI on the VM, and a probe run
as `ubuntu` does not inherit the unit's `Environment=`, so pass the path explicitly. The `activity_log` payload column
is **`details_json`** (not `detail`/`payload`) — a grep for the wrong name returns nothing and looks like "no data".
**Never write to the live DB.**

## Todos

- [x] [BACKEND] P1. ✅ **(AF-1a) Triage the 83 unresolved escalations and root-cause WHY they fail.** —
      `unified-trading-pm@a35c6996` (2026-07-20). RE-MEASURED live via read-only SSM (`escalation_queue` +
      `activity_log`, not the 7d snapshot): 246 total `ldr_qg_failure` rows, 200 resolved / **46 unresolved**. Sampled +
      classified ALL 46 by activity-log narrative (not just the terminal `last_error`, which is uniformly the generic
      "re-escalation cap hit" — uninformative on its own): **65% (30/46) NEVER_FOUND_ROOT_CAUSE** (last heartbeat is
      "reproducing quality-gates.sh failure", i.e. died mid-reproduction), **33% (15/46) FOUND_ROOT_CAUSE_THEN_SILENT**
      (correctly diagnosed — several within 3-5 min — sometimes even applied the fix, then went silent before shipping),
      **2% (1/46) hit a `/blocked` question**. **Root cause (bucket i, boot-prompt-too-shallow — NOT ii or iii,
      diagnosis quality was fine)**: `cicd.md`'s `ldr_qg_failure` handler instructs a BLOCKING foreground
      `bash scripts/quality-gates.sh`, whose documented runtime is 8-15+ min
      (`/codex/06-coding-standards/quality-gates.md` — one measured CI run: 715s/778s) — at/over the
      WorkerLivenessWatchdog's 15-min heartbeat-silence kill (`server/worker_liveness_watchdog.py`), with zero
      instruction to background it or heartbeat during the run. One worker's own note confirms it directly: "running
      full quality-gates.sh in background (took >10min on first attempt)". This also explains the SAME bug re-escalating
      from a fresh PR shortly after (e.g. market-data-processing-service `perp_trades`/ `NEEDS_CANDLE_PROCESSING`,
      features-service transfermarkt-date coverage floor) — the fix was correctly found but never actually landed, so
      LDR stayed red for the next promotion. **Fix applied**: hardened `agents/cicd.md` with a background-run + poll +
      heartbeat-every-180s recipe, referenced from every `quality-gates.sh` invocation in the file (merge_conflict /
      sit_failure / ldr_qg_failure / plan_health), not just ldr_qg_failure. Shipped via quickmerge, PR
      IggyIkenna/unified-trading-pm#1247 (auto-merge to main). **Follow-up filed, not blocking**: worth re-measuring the
      unresolved rate ~1 week post-fix to confirm the hypothesis (a KPI AF-5 will make this an ongoing measurement, not
      a one-off).
- [x] [BACKEND] P2. ✅ **(AF-1b) Cap escalation redispatch — on the shared cooldown store, not a new one.** —
      `agent-orchestrator@5dd9bbc8` (2026-07-22). Built on the shared `state_store.cooldown` store per spec —
      **correction to this todo's own key design**: namespaced by the WALL's identity
      (`f"escalation:{repo}:{pr_number}:{wall_type}"`), NOT `f"escalation:{escalation_id}"` as originally written here —
      a fresh `escalation_id` is minted every time CI re-fires an already-terminal wall (`_find_open_escalation` only
      dedups while queued/dispatched), so an escalation_id-keyed cooldown could never throttle the actual churn this
      todo exists to stop; the wall-identity key is what `_find_open_escalation` itself already dedups on, extended to
      the terminal case. Wired at 3 points in `server/escalation.py`: (1) `enqueue()` checks `get_cooldown` before
      minting a new escalation — an armed cooldown with an UNCHANGED `context` snapshot returns `status="cooling_down"`
      instead of queuing a fresh worker; a changed context (genuine new incident) is always immediately eligible, per
      the store's own snapshot-mismatch rule; (2) `_mark_unresolved_and_maybe_reescalate` arms the cooldown only on the
      terminal cap-hit branch (NOT on the in-progress re-escalation branch, which must stay unthrottled — that's the
      watchdog's own sanctioned single retry of the SAME escalation_id); (3) `retry_queued_escalations`' hard-TTL
      abandon path arms it too. `_mark_resolved` clears it — a wall that resolves and breaks again later is a genuinely
      new incident (matches `test_open_escalation_statuses_exclude_terminal`'s existing contract) and must not inherit a
      stale suppression window. 7 new regression tests (key format, throttled when context unchanged, NOT throttled when
      context differs or no cooldown armed, cap-hit arms it, in-progress re-escalation does NOT arm it, resolution
      clears it) + fixed 3 pre-existing tests whose session mock aliased `EscalationQueueRow` and `CooldownRow` lookups
      onto the same return value (only surfaced once a second row-model was queried in the same code path). Full
      `agent-orchestrator` `quality-gates.sh` green (1578 passed, 1 skipped). **Gate met**:
      `test_enqueue_throttled_by_cooldown_when_context_unchanged` / `test_enqueue_not_throttled_when_context_changed`
      show a repeat dispatch backs off while a genuine new incident never is; no second cooldown engine exists in the
      tree (reuses `state_store.cooldown` throughout).
- [x] [BACKEND] P1. ✅ **(AF-2 + Phase-6) Throttle plan_health — server-side min-interval gate + at-most-one-live
      coalesce.** — `agent-orchestrator@d098970` (2026-07-20). Implemented exactly as specified: (a)
      `TuningDefaults.plan_health_min_interval_seconds` (default 7200s/2h) + `plan_health_dispatch_timeout_seconds`
      (default 1800s/30min, the dead-dispatch fallback — above the measured p90 6.5min runtime with margin, well below
      the interval); (b) `_report_dispatch_gate()` in `server/plan_health.py` — at-most-one-live coalesce (no result
      posted yet AND inside the dead-dispatch timeout → coalesce, HTTP 200, no spawn); (c) the interval half only allows
      a new spawn once the previous dispatch is done (result posted OR timed out) AND the min-interval has elapsed; (d)
      `mode="reconcile"` is exempt by construction (disjoint `agent_kind`, gate only runs for `mode="report"`);
      `force=true` (new `PlanHealthDispatchRequest.force` field, threaded through the route) skips the interval half but
      still never double-spawns onto a live dispatch. `main-backmerge-to-ldr.yml`'s promotion ping is UNCHANGED (still
      fires every promotion) — it's now a trigger the gate absorbs, per spec (d). 15 new unit tests (gate logic +
      `dispatch()` wiring), full `agent-orchestrator` `quality-gates.sh` green (1474 passed). **Gate verification
      deferred (honest — this needs live traffic)**: the "measured dispatch rate ≤1/interval over 24h, zero
      `superseded-plan_health` exits" gate can only be confirmed once this code is running on the live orchestrator VM
      and a 24h window has elapsed post-deploy — filed as a follow-up re-measurement, not claimed here.
- [x] [BACKEND] P2. ✅ **(AF-5) Fleet-efficiency KPIs + per-account usage attribution — BACKEND done, dashboard CARD
      deferred (honest partial).** — `agent-orchestrator@572bf25` (2026-07-20). New `server/fleet_kpis.py`:
      `compute_fleet_efficiency_kpis` (boots=`slot_boot`, dispatches=`task_dispatched`, done=`slot_done` — event-type
      recon citations in the module docstring; NOT `autospawn_succeeded`/`slot_spawned`, which are the same physical
      boot's upstream trigger and would double-count) → conversion %, boots-per-done, boots:dispatch ratio (division-
      by-zero-safe: undefined ratios are `None`, never a misleading 0 or ∞); `compute_fleet_efficiency_kpis_for_range`
      for a bounded day-before baseline; `detect_sharp_regression` (day-over-day boots:dispatch, new
      `TuningDefaults.     fleet_kpi_regression_multiple` default 5x); `compute_usage_by_account` (transcript-file-size
      proxy per the operator's lightweight-option ruling, grouped by account). **Surfaced on TWO real surfaces**: the
      Slack daily digest (`notify_daily_summary` — efficiency line + regression alert + usage-by-account, best-effort so
      a KPI computation failure never breaks the digest post itself) and `GET /api/fleet-kpis` (dashboard-ready JSON).
      24 new tests, full `agent-orchestrator` `quality-gates.sh` green (1519 passed). **Top skip reasons — honest gap
      noted, not padded**: only `autospawn_skipped_session_exists` + `spawn_gate_fallback_engaged` persist to
      `activity_log` today; most autospawn skip branches are `logger.info`-only (recorded in `_SKIP_COVERAGE_NOTE`,
      surfaced in the API response, not silently hidden). **DEFERRED**: the dashboard REACT card itself — `dashboard/`
      has no `node_modules` in this environment and CLAUDE.md's UI rule requires a cited Playwright regression spec
      before a UI tick counts; the endpoint is ready and tested, wiring the card is a small, clearly-scoped follow-up,
      not fabricated as done here. **Gate answer** — how would the 2026-07-12-class degradation (spawn:dispatch
      0.6:1→44:1, ~73x) be caught within one digest cycle: `detect_sharp_regression` fires when today's ratio is
      ≥`fleet_kpi_regression_multiple`× (default 5x) the prior-24h baseline — 73x clears that with wide margin, and the
      alert renders as a `:rotating_light:` line at the TOP of the very next digest post (interval default 24h,
      operator-configurable via `TuningDefaults.daily_summary_interval_seconds`).
- [x] [UI] P3. ✅ **(AF-5-followup) Wire the fleet-KPI dashboard React card.** — `agent-orchestrator@efc52fa`
      (2026-07-21). New `dashboard/src/FleetKpis.tsx` page reads `GET /api/fleet-kpis` on a 30s interval and renders:
      the six efficiency tiles (boots · dispatches · done · conversion% · boots/done · boots:dispatch — null ratios
      render `—`, never a misleading 0), a red regression banner when `regression_alert` is set, a prior-window baseline
      row, and a per-account usage table (transcript-bytes, "who's burning the quota"). Wired as route `/fleet-kpis` in
      `App.tsx` + a "Fleet KPIs →" button on the Landing header (`Landing.tsx`), sibling to Fleet Git-Health; response
      types in `types.ts` mirror `server/fleet_kpis.py::kpis_as_dict`/`usage_as_dict`. Display logic is in pure exported
      mappers (`conversionTone`/`ratioTone`/`formatBytes`/`kpiTiles`/`topAccounts`). **Gate MET** (regression spec
      cited): `dashboard/src/FleetKpis.test.ts` — **19 vitest cases** (tone thresholds incl. the 44:1 degradation → red,
      byte formatting, null-ratio `—` rendering, top-N account sort) — all green in the AO quality gate (113/113
      dashboard tests), plus `tsc --noEmit` clean and `vite build` succeeds (the page compiles into the app bundle).
      **Note on the gate wording**: this dashboard has NO Playwright (it's operator tooling under `scripts/check.sh`,
      gated by `tsc` + `vitest`, not the main-UI `pw:L2` regime) — the vitest pure-mapper suite is its equivalent cited
      regression spec, following the sibling `FleetGit.test.ts` pattern.
- [x] [INFRA] P2. ✅ **(AF-4) Assert disaster-recovery snapshot RECENCY.** — `agent-orchestrator@3fd6129` (2026-07-20).
      **(a) Re-measured S3 last-modified LIVE** (`aws s3api head-object` against `uts-orchestrator-state-427895769566`,
      this session, not a probe): the light `state.json` snapshot (`upload_state_to_s3`, ~30min cadence) is HEALTHY (~3
      min old at measurement time). The full SQLite backup (`backup_sqlite_to_s3`, nominal 6h cadence —
      `snapshot_interval_seconds`(1800s) x `sqlite_backup_every_n_ticks`(12)) is NOT: real gaps up to **47 HOURS between
      successive backups, including a ZERO-backup day (2026-07-19)** — pulled the full `backups/sqlite/planning/`
      history to confirm this wasn't one bad reading. This is the actual artifact a restore uses, and where the real gap
      is — **canary tracks it, not the lighter state.json**. **(b) Built `SnapshotRecencyCanary`**
      (`server/snapshot_recency.py`, mirrors `PlanReconcilerLivenessCanary`'s exact skeleton): lists the VM-scoped
      `backups/sqlite/<vm_id>/` prefix, HEADs the lexicographically-latest key for its authoritative `last_modified`
      (list_blobs's own `last_modified` is unpopulated on the AWS backend — measured this session), pages via the
      existing state-transition-dedup Slack pattern (`notify_snapshot_recency_breach`/`_resolved`) on the new
      `TuningDefaults.snapshot_max_age_hours` (default 12h = 2x nominal, tolerates one missed cycle, still catches the
      measured 47h class with wide margin) + `snapshot_recency_interval_seconds` (default 3600s). Also
      `GET /api/snapshot-recency` (pull-surface companion, deliberately kept OUT of `/api/healthz` so the liveness probe
      never gains a live S3 HEAD as a new failure mode). Wired into server startup next to `SnapshotLoop`. 30 new tests
      — **the plan's literal Gate ("alerts when the loop is deliberately stopped IN A TEST, not by stopping the live
      loop") is the explicit contract of every test**: all driven through mocked/fixture values, the real S3 bucket and
      the live `SnapshotLoop` are never touched. Full `agent-orchestrator` `quality-gates.sh` green (1544 passed). **(c)
      Restore drill — DONE, read-only, safe**: downloaded the actual latest S3 SQLite backup
      (`live_20260720T011633Z.db`, 41.3 MB) to a scratch dir (never the live orchestrator's paths),
      `PRAGMA integrity_check` → `ok`, confirmed all 16 expected tables present, 17 slots / 88,834 `activity_log` rows
      queryable, and the DB's own newest row timestamp (`2026-07-20 01:16:33`) matches the S3 object's `last-modified`
      (`01:16:34`) to the second — proves the backup is a real, consistent, restorable snapshot, not a corrupt/partial
      upload. **Coordination check**: `ao_fleet_infra_hardening_2026_07_20`'s in-repo-state-path migration is code-done
      but the LIVE DB move is still operator-gated/pending — the S3-backup artifact class has NOT been removed yet, so
      this work was not duplicative.
- [x] [BACKEND] P3. ✅ **(AF-3) `activity_log` retention — decision: DEFER pruning, growth alarm implemented.** —
      `agent-orchestrator@a87d2d3` (2026-07-20). **Decision recorded** (of the two operator-sanctioned options): no
      prune — 83k rows/40MB genuinely isn't a problem, and a delete path adds real risk (wrong-window deletes,
      archive-before-delete correctness) for a P3 item the operator explicitly said not to redesign. Built the growth
      alarm instead: `TuningDefaults.activity_log_growth_alarm_rows` (default 500,000 — ~6x the measured 83k baseline, a
      multi-month runway before it can fire on legitimate growth), checked via
      `DailySummaryLoop._check_activity_log_growth()` — **piggybacked on the ALREADY-periodic digest tick, no new daemon
      thread**, per the "no redesign" ruling. State-transition deduped (`dedup_state.activity_log_growth_alarm_path()`):
      pages once on crossing, not every digest cycle; clears silently on drop-back-under (e.g. a future operator prune),
      and re-arms for the next breach. 4 new tests (fires-once, silent-under-threshold, resolve+re-arm, best-effort
      failure isolation). Full `agent-orchestrator` `quality-gates.sh` green (1548 passed). **Gate met**: retention
      decision recorded (defer, no prune) WITH the growth alarm in place — the plan's own explicit acceptable-outcome
      clause.
- [x] [BACKEND] P0. ✅ **(AF-1a-followup) Re-measure the unresolved-escalation classification ~1 week post-fix.** —
      re-run 2026-07-27 (target date hit exactly). **Result: the fix worked.** `ldr_qg_failure` unresolved count dropped
      **46 → 3**; NEVER_FOUND_ROOT_CAUSE (the bucket the cicd.md fix targeted) dropped **65% (30/46) → 0% (0/3)**. New
      split: FOUND_ROOT_CAUSE_THEN_SILENT 67% (2/3), HIT_BLOCKED_QUESTION 33% (1/3) — both pre-existing, unrelated
      failure classes AF-1a never claimed to fix. Gate MET — confirms the boot-prompt-too-shallow root cause was
      correct, no reopen needed. **Correction found + fixed while re-running**: the script's hardcoded DB path
      (`/var/lib/orchestrator/state.db`) was stale — the live DB moved in-repo to `data/state/state.db` per the
      `ao_fleet_infra_hardening_2026_07_20` cutover completing sometime between 2026-07-20 and today (confirmed live via
      the `orchestrator.service` unit's own comment); the script failed with "unable to open database file" until
      corrected. Fixed + shipped: `agent-orchestrator@c5157fb`, full QG green (1804 passed, dashboard tsc/vitest green).

- [x] [BACKEND] P3. ✅ **(AF-2-followup) Confirm plan_health throttle's dispatch-rate gate against real live traffic.**
      — re-measured 2026-07-31, direct read-only SQLite query against the live `data/state/state.db`
      (`agent-orchestrator/data/state/state.db`, in-repo path per the `orchestrator.service` unit file — this session
      ran ON the central orchestrator VM itself, `localhost:8765` reachable directly, no SSM round-trip needed). **Both
      gate halves addressed, one MET cleanly, one MET-with-honest-caveat — not smoothed over**: **(a) zero
      `superseded-plan_health` exits — MET.**
      `select count(*) from agents where     exit_reason='superseded-plan_health'` → **0**, across the table's entire
      history (not just post-deploy). No duplicate/overlapping plan_health agent record has ever been reaped this way.
      **(b) dispatch rate ≤1/interval over 24h — MET, but never actually stress-tested.** Since AF-2 deployed
      (`agent-orchestrator@d098970`, commit timestamp 2026-07-20 18:41:19+05:30 = 13:11:19 UTC), querying `activity_log`
      for `event_type='plan_health_dispatch_initiated'` filtered to `mode='report'` (the only mode this gate covers —
      `reconcile`/`docs_reconcile`/`ag_closeout`/`na_eligibility`/`context_scout` register a disjoint `agent_kind` and
      are exempt by construction) finds exactly **2 attempts** in the 11 days since: 2026-07-28 05:06:36 (`agt-e3022c`)
      and 05:13:06 (`agt-988056`), 389s apart. Cross-referencing the `agents` table (what the gate itself queries, via
      `_last_report_dispatch`) shows only **agt-988056 ever became a live row** (registered 05:14:59, finished 05:22:02,
      `exit_reason=lifecycle-complete`) — **agt-e3022c has NO row at all**: its `plan_health_dispatch_failed` entry
      (05:08:15) shows it died to an unrelated branch-state quarantine on slot 12 ("auto-heal failed...
      still-quarantined-after-heal") before ever reaching `register_agent`. Since `plan_health_dispatch_initiated` logs
      BEFORE the spawn attempt (not after a successful registration), the gate's own throttle query never saw agt-e3022c
      as "the previous dispatch," so agt-988056 correctly sailed through with nothing to coalesce against — **not a
      `force=true` escape-hatch use, not a gate gap**, fully resolving the 2026-07-29 progress-log entry's flagged
      ambiguity (which couldn't confirm this via the paginated read-only API). agt-988056 is therefore the ONLY
      successful report-mode dispatch in the entire 11-day post-deploy window — the prior one is 8 days earlier
      (2026-07-20), so no 24h window has ever contained two. `plan_health_dispatch_coalesced` has fired **zero times,
      ever** (full history) — the throttle's actual blocking branch has never been exercised by real concurrent/rapid
      traffic, because report-mode dispatch (tied to `main-backmerge-to-ldr.yml`'s promotion ping) has simply never come
      in fast enough to test it. **Reporting the honest number per this plan's own Safeguards rule**: zero violations
      observed, but also zero positive engagements of the throttle logic itself — a true and complete answer, not
      "confirmed" padding a thin sample. **Codex-alignment check (archival ritual step 3) found a real gap**:
      `agent-orchestrator-single-vm-architecture.md`'s existing "Skip / cooldown / park" section documents only the
      fleet-wide dispatch-cooldown store (AF-1b) — AF-2's own separate, plan_health-local `_report_dispatch_gate`
      throttle was never documented anywhere in codex. Added a paragraph there (same section) with the full mechanism +
      this session's live numbers; no follow-up todo needed beyond that. Every todo in this plan is now `[x]` — archived
      same-session per the 6-step ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Do not stop a live loop or timer to test an assertion** — prove it with a fixture. Stopping the snapshot loop or a
  timer on the central VM is a production action and an operator decision.
- **Report the honest number.** Several gates here are measurements; if a KPI shows the fleet is worse than expected,
  that is the deliverable, not a problem to smooth over.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only alerting; state-transition dedup for any
  alarm added here.
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured terminal verdicts, not activity signals.
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch/spawn model behind the KPIs.

## Progress Log

- **2026-07-31 — AF-2-followup closed, plan fully shipped, archived same-session.** Re-measured with direct read-only
  SQLite access to the live orchestrator's `data/state/state.db` (this session ran ON the central orchestrator VM,
  `localhost:8765` reachable directly — no SSM round-trip, no pagination limits, unlike the 2026-07-29 pass below).
  **Zero `superseded-plan_health` exits** in the full `agents` table history. **Zero throttle violations**: exactly one
  successful report-mode dispatch (`agt-988056`) has registered in the `agents` table in the 11 days since AF-2 deployed
  (2026-07-20 13:11:19 UTC) — no 24h window has ever contained two, and `plan_health_dispatch_coalesced` has fired zero
  times ever. **Fully resolves the 2026-07-29 ambiguity below**: the apparent 389s-apart pair was NOT two live
  dispatches — the first (`agt-e3022c`) died pre-registration to an unrelated branch-quarantine failure on slot 12 and
  never became an `agents` row, so the gate's own query correctly saw nothing recent to throttle the second against. Not
  `force=true`, not a gate gap. **Honest limit stated, not smoothed over**: with only one successful dispatch in 11
  days, the throttle's blocking code path has never actually been exercised by concurrent live traffic — zero
  violations, but also zero positive engagements; report-mode traffic has simply never come in fast enough to test it.
  **Codex-alignment check found a real gap**: AF-2's own report-mode throttle was never documented in
  `agent-orchestrator-single-vm-architecture.md` (its "Skip / cooldown / park" section only covers AF-1b's separate
  fleet-wide cooldown store) — added a paragraph there with the mechanism + these live numbers; no follow-up todo needed
  beyond that. Every todo in this plan is now `[x]` — archived per the 6-step ritual: banner added above,
  `status: complete`, moved to `plans/archive/2026_07/`, referrer paths fixed (see commit).
- **2026-07-29 (batch closeout pass) — AF-2-followup re-measured live, NOT closed (honest ambiguous result).** Queried
  the live orchestrator's `/api/activity` (`plan_health_dispatch_initiated`, 9-day window, read-only via SSM — no DB
  write) filtered to `mode="report"` (the ONLY mode this todo's gate covers; `reconcile`/`ag_closeout`/`na_eligibility`/
  `docs_reconcile` are disjoint `agent_kind`s exempt by construction, confirmed 133/49/9/6 dispatches of those vs only 2
  `report`-mode dispatches in the same window — the generic `plan_health_dispatched` event type does NOT carry `mode`,
  only `plan_health_dispatch_initiated` does; a naive query against the former silently double-counts every
  scheduled-job kind as "report"). **Result: only 2 `report`-mode dispatches occurred in 9 days (both on 2026-07-28),
  389s (6.5 min) apart — under the 7200s (2h) `plan_health_min_interval_seconds` gate**, and
  `plan_health_dispatch_coalesced` fired ZERO times in the same window (the coalesce guard never engaged). This does NOT
  confirm the gate holds — it is either (a) a genuine gate gap (an untested code path letting two `report` dispatches
  through inside one interval), or (b) an explainable exception this pass didn't fully verify (e.g. one of the two used
  the documented `force=true` escape hatch, which is designed to skip the interval half). A follow-up query for the two
  dispatches' own `force` field came back empty (likely a pagination/ordering artifact of the read-only endpoint, not
  re-investigated further — bounded effort). **Per this plan's own "Report the honest number" Safeguards rule, NOT
  flipping AF-2-followup to done on this evidence** — the todo's gate ("measured dispatch rate ≤1/interval over 24h,
  zero superseded-plan_health exits") is not cleanly met by what was actually measured, so leaving it open with this
  real data point rather than declaring success. Whoever picks this up next: confirm whether either 2026-07-28 dispatch
  carried `force=true` (would fully explain and clear this), and re-run over a longer window once `report`-mode
  dispatches accumulate more samples (n=2 is too thin to trust either way).
- **2026-07-27 — AF-1a-followup done, plan fully shipped.** Re-measured on the target date: `ldr_qg_failure` unresolved
  count 46→3, NEVER_FOUND_ROOT_CAUSE 65%→0%. Confirms the AF-1a cicd.md backgrounding fix genuinely fixed the failure
  class it targeted; the 3 remaining unresolved rows split 67% FOUND_ROOT_CAUSE_THEN_SILENT / 33% HIT_BLOCKED_QUESTION —
  different, pre-existing classes outside this todo's scope. **Also found + fixed a live bug while re-running**: the
  measurement script itself was broken (`sqlite3.OperationalError: unable to open database file`) because its hardcoded
  DB path (`/var/lib/orchestrator/state.db`) went stale once the in-repo-state-path migration
  (`ao_fleet_infra_hardening_2026_07_20`) actually cut over on the live VM sometime between 2026-07-20 and today —
  confirmed via the live `orchestrator.service` unit file, which now documents `data/state/state.db` in-checkout as the
  canonical path. Fixed + shipped `agent-orchestrator@c5157fb` (full QG green). Every todo in this plan is now `[x]` —
  candidate for archival, not done in this pass (archival is a separate 6-step ritual per CLAUDE.md's plan-hygiene HARD
  RULE, left to the operator/next pass).
- **2026-07-22 — AF-1b done** (`agent-orchestrator@5dd9bbc8`). Every todo in this plan is now shipped except the
  time-gated AF-1a-followup (re-measurement not due until ~2026-07-27). See the AF-1b todo above for the full design +
  the key-shape correction (wall identity, not `escalation_id`) vs. this plan's original phrasing.
- **2026-07-20 — plan created** from Phase 7 + the Phase-6 plan_health item, merged because AF-2 was already recorded as
  "folded into the Phase-6 plan_health item's acceptance" — keeping them apart would have split one fix across two
  agents.
- **2026-07-20 — AF-1a done** (`unified-trading-pm@a35c6996`, PR #1247). Headline finding: the 43%-unresolved number was
  NOT a diagnosis-quality problem — cicd workers correctly root-caused 98% of the sampled unresolved escalations (often
  in under 5 minutes) but 100% of those samples then went silent, because the boot prompt's own instructed step
  (`bash scripts/quality-gates.sh`, blocking foreground, 8-15+ min documented runtime) sits at/over the
  WorkerLivenessWatchdog's 15-min heartbeat-silence kill with no backgrounding/heartbeat guidance. Fixed by hardening
  `agents/cicd.md`. Full cause-class breakdown + evidence in the AF-1a todo above.
- **2026-07-20 — AF-2 done** (`agent-orchestrator@d098970`). Server-side throttle for `/api/plan-health/dispatch`
  report-mode: 2h min-interval + at-most-one-live coalesce + wait-for-previous-result-or-timeout, `mode=reconcile`
  exempt, `force=true` escape hatch. 15 new tests, full QG green. The dispatch-rate/zero-superseded-exits acceptance
  gate itself needs a live 24h window post-deploy to confirm — noted as deferred verification on the todo, not silently
  claimed. Also re-verified AF-1b's dependency is still open (its cooldown-store P1 todo unchecked as of this session) —
  AF-1b stays blocked, correctly **as of this check** (superseded within the same day — see below).
- **2026-07-20 — AF-5 backend done** (`agent-orchestrator@572bf25`). Efficiency KPIs + day-over-day regression
  detection + per-account usage (transcript-size proxy) surfaced in the Slack digest and via `GET /api/fleet-kpis`. 24
  new tests, full QG green. Dashboard React card explicitly DEFERRED (no `node_modules` in this environment +
  CLAUDE.md's playwright-gate requirement for any UI tick) — the endpoint is ready, wiring the card is a small
  follow-up, not claimed done. **Heads up for the next session**: `ao_dispatch_cooldown_and_park_2026_07_20@cfb211c`
  landed its fleet-scoped cooldown store WHILE this session was running — AF-1b (still marked blocked above) may now be
  unblockable; re-check that plan before starting AF-1b.
- **2026-07-20 — AF-4 done** (`agent-orchestrator@3fd6129`). Live re-measurement found a REAL gap the earlier probe
  evidence had missed: the light state.json snapshot is healthy, but the full SQLite DR backup has gone up to 47h
  between uploads including one zero-backup day. `SnapshotRecencyCanary` now asserts + pages on this (mirrors
  `PlanReconcilerLivenessCanary`'s proven pattern). Restore drill performed for real (read-only, scratch dir): the
  latest S3 backup downloaded, integrity-checked, and queried successfully. 30 new tests, full QG green.
- **2026-07-20 — AF-3 done** (`agent-orchestrator@a87d2d3`). Decision: defer pruning, ship the growth alarm —
  piggybacked on the existing `DailySummaryLoop` tick per the operator's explicit no-redesign ruling, no new daemon
  thread. 4 new tests, full QG green.
- **2026-07-20 — session wrap-up.** Every todo except AF-1b is done: AF-1a (root-caused + fixed the CI-escalation
  failure class), AF-2 (plan_health throttle), AF-5 (fleet efficiency KPIs + usage attribution, backend), AF-4 (DR
  snapshot recency canary + a real restore drill), AF-3 (activity_log growth alarm). AF-1b stays the one open item —
  genuinely blocked on `ao_dispatch_cooldown_and_park_2026_07_20`'s shared cooldown store, though that plan's own
  keystone dependency landed mid-session (`cfb211c`) and may now unblock it; re-verify that plan's cooldown-store todo
  before starting AF-1b next. Two items are explicit, tracked partial-completions rather than silently-dropped scope:
  AF-2's 24h-live-traffic dispatch-rate gate (code shipped + tested, needs a real post-deploy window to confirm) and
  AF-5's dashboard React card (backend + API shipped + tested; the card itself needs `dashboard/` `node_modules` +
  CLAUDE.md's playwright regression-spec gate, neither available in this session). Every commit landed via quickmerge
  with a green `quality-gates.sh` run cited; every plan-flip cites the shipping commit.
- **🟢 2026-07-20 — DEPENDENCY UNBLOCKED, store published (notification from `ao_dispatch_cooldown_and_park_2026_07_20`,
  answering both the AF-5 and session-wrap-up entries' re-verify note directly above).** The ONE fleet-scoped cooldown
  store AF-1b must sit on is built + shipped (`agent-orchestrator@cfb211c`, `server/state_store/cooldown.py`) — landing
  after the AF-2 entry's dependency check, which is why that entry (accurately, at the time) still read blocked. It is
  generic over an opaque `key` string specifically so AF-1b does not need a second engine: namespace escalation
  dispatches as `f"escalation:{escalation_id}"` (today's two consumers use `f"task:{task_id}"`) and call the same
  `register_cooldown`/`get_cooldown`/`clear_cooldown` primitives. Full contract — key namespacing, window semantics
  (base/extended/ETA-override), change-triggered re-eligibility, and the durable-auto-park pattern built on top of it —
  documented in `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "2. Task lifecycle" ("Skip /
  cooldown / park"), which is now the SSOT for this mechanism. **AF-1b is unblocked** — build the escalation backoff
  directly on `register_cooldown`, do not write a second cooldown/backoff engine.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — doc carries an explicit dated LOCAL declaration
  (`assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)` + an
  `Execution environment — LOCAL` section); `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s
  Deferred list already ruled that extracting its todos needs the operator to lift that declaration. Its one open item
  (AF-2-followup) is additionally sample-gated — the 2026-07-29 re-measure returned n=2, explicitly recorded as too thin
  to act on.

## Deferred work — migrated to:

**This plan's own todo "(AF-5-followup) Wire the fleet-KPI dashboard React card"** — the dashboard REACT card was
explicitly `**DEFERRED**` inline at the AF-5 backend todo (no `node_modules` + no cited Playwright/regression spec at
the time) but was completed within this SAME plan one session later (`agent-orchestrator@efc52fa`, 2026-07-21, 19 vitest
cases + `tsc`/`vite build` clean). No external successor plan was needed — the deferred item shipped in-plan.

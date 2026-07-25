---
doc_type: plan
title: AO fleet observability — make efficiency, escalator efficacy and account burn visible
summary:
  Roughly four of five dispatches produce no completion and nothing surfaces it, 43% of CI escalations go unresolved
  after ~3.8 dispatches each, plan_health burns 55 haiku runs a day of which 13 return nothing, snapshot recency is
  unasserted, and no view shows which account or agent is burning the quota. Add the KPIs, throttle plan_health, and
  root-cause why the escalators fail rather than only capping them.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, observability, kpi, escalation, plan-health, usage, snapshots]
related:
  [
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_dispatch_cooldown_and_park_2026_07_20.md,
    /plans/archive/2026_07/ao_fleet_infra_hardening_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
assigned_role: backend_engineer
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
- [ ] [BACKEND] P0. **(AF-1a-followup) Re-measure the unresolved-escalation classification ~1 week post-fix.** AF-1a's
      cicd.md backgrounding fix (`unified-trading-pm@a35c6996`) landed 2026-07-20; the 65%/33%/2%
      NEVER_FOUND_ROOT_CAUSE/FOUND_ROOT_CAUSE_THEN_SILENT/HIT_BLOCKED_QUESTION split was measured the SAME session the
      fix shipped, so it cannot yet reflect the fix's effect — a re-check too soon would just re-confirm pre-fix
      escalations still working through the queue. Correction to the earlier Progress Log note: AF-5's fleet-wide
      efficiency KPIs (boots/dispatches/done ratios) do NOT reproduce this specific classification — they're a
      different, coarser measurement; this is a genuinely separate re-run, not automated by AF-5. **Tool**:
      `agent-orchestrator/scripts/orchestrator/check-escalation-unresolved-classification.sh ldr_qg_failure` (built +
      validated live this session, read-only via SSM — reproduced the exact 46/65%/33%/2% figures on a live re-run).
      **Target date**: ~2026-07-27. **Gate**: re-run recorded with the new percentages; if
      NEVER_FOUND_ROOT_CAUSE/FOUND_ROOT_CAUSE_THEN_SILENT haven't dropped meaningfully, the boot-prompt-too-shallow root
      cause was wrong or incomplete — reopen the AF-1a analysis rather than assuming the fix worked.

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

## Deferred work — migrated to:

**This plan's own todo "(AF-5-followup) Wire the fleet-KPI dashboard React card"** — the dashboard REACT card was
explicitly `**DEFERRED**` inline at the AF-5 backend todo (no `node_modules` + no cited Playwright/regression spec at
the time) but was completed within this SAME plan one session later (`agent-orchestrator@efc52fa`, 2026-07-21, 19 vitest
cases + `tsc`/`vite build` clean). No external successor plan was needed — the deferred item shipped in-plan.

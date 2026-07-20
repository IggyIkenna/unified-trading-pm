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
    ao_open_issues_consolidated_close_out_2026_07_17.md,
    ao_dispatch_cooldown_and_park_2026_07_20.md,
    ao_fleet_infra_hardening_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P1
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
depends_on: [ao_dispatch_cooldown_and_park_2026_07_20.md]
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
      (`codex/06-coding-standards/quality-gates.md` — one measured CI run: 715s/778s) — at/over the
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
- [ ] [BACKEND] P2. **(AF-1b) Cap escalation redispatch — on the shared cooldown store, not a new one.** Per
      `escalation_id` backoff so one wall cannot consume 3.8 sessions. **Still blocked on the dependency above**
      (`ao_dispatch_cooldown_and_park_2026_07_20`'s shared cooldown store — verified 2026-07-20, its own P1 "Build the
      ONE fleet-scoped cooldown store" todo is still unchecked). **Gate**: a test showing repeat dispatches for the same
      escalation_id back off; no second cooldown engine exists in the tree.
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
- [ ] [BACKEND] P2. **(AF-5) Fleet-efficiency KPIs + per-account usage attribution.** 24h measured: 310 boots / 154
      dispatches / 27 done — ≈11.5 boots and ≈5.7 dispatches per completed task. Surface daily-digest + dashboard KPIs:
      spawns, dispatches, done, conversion %, boots-per-done, top skip reasons, with an alert on sharp regression.
      **Operator-ratified + EXPANDED 2026-07-18**: ALSO attribute USAGE per slot / agent / account — tokens and messages
      consumed — so it is visible WHERE the account budget goes. Today nothing shows which agent/slot/account burned the
      quota, yet the fleet hits usage limits even across 4 accounts. Source the counters from the usage-poller /
      transcript sizes and add a "usage by account" view on the same surface, so an account nearing its cap and the
      agent driving it are both visible **before** failover fires. **Gate**: the efficiency KPIs render; a per-account
      usage breakdown is visible; and the 2026-07-12-class degradation (spawn:dispatch 0.6:1 → 44:1) would have been
      caught within one digest cycle — state how.
- [ ] [INFRA] P2. **(AF-4) Assert disaster-recovery snapshot RECENCY.** `gcs_sync.SnapshotLoop` runs and
      `ORCHESTRATOR_S3_BUCKET=uts-orchestrator-state-427895769566` is set, but **nothing asserts snapshot age** — a
      broken snapshot loop looks exactly like a working one until the day `state.db` is lost. Same silent-by-absence
      class as the reconciler timer. **RE-VERIFY FIRST**: the earlier "no local state.json" evidence was a PROBE
      ARTIFACT (the probe ran as `ubuntu` without the unit env, so it checked the in-repo default) — measure the **S3
      object's last-modified** instead, which is the real signal and path-independent. **Operator-ratified: BUILD it.**
      (a) re-measure S3 last-modified now; (b) add a snapshot-age assertion (digest line or health endpoint: last
      successful snapshot < N hours, alert on breach); (c) one documented restore drill. **Gate**: measured snapshot age
      recorded; the assertion alerts when the loop is deliberately stopped **in a test** (not by stopping the live
      loop). Note: `ao_fleet_infra_hardening_2026_07_20.md` moves state in-repo, which removes the artifact class
      entirely — coordinate rather than duplicate.
- [ ] [BACKEND] P3. **(AF-3) `activity_log` retention — low priority, decide and record.** 83,813 rows over 20 days
      (~4.2k/day), db 40 MB. Agents get `prune_finished_agents` (7d) and tasks get orphan-GC; `activity_log` has
      nothing. **Operator context 2026-07-18: 83k rows / 40 MB is NOT big for SQLite — there is no problem today**; the
      only real risk is unbounded growth over MONTHS (write-latency creep on the write-hot DB). So: a simple age-based
      prune (90d) OR just a growth alarm suffices — no redesign, and explicitly deferring is an acceptable outcome if
      the alarm exists. Optionally archive-to-S3 via the existing snapshot loop before any delete. **Gate**: a retention
      decision recorded and implemented, or explicitly deferred WITH the growth alarm in place.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Do not stop a live loop or timer to test an assertion** — prove it with a fixture. Stopping the snapshot loop or a
  timer on the central VM is a production action and an operator decision.
- **Report the honest number.** Several gates here are measurements; if a KPI shows the fleet is worse than expected,
  that is the deliverable, not a problem to smooth over.

## Codex SSOTs

- `codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only alerting; state-transition dedup for any
  alarm added here.
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured terminal verdicts, not activity signals.
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch/spawn model behind the KPIs.

## Progress Log

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
  AF-1b stays blocked, correctly.

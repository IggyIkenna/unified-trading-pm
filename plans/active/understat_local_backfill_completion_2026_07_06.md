---
doc_type: plan
title: Understat XG + XG_SHOTS full-history backfill — LOCAL completion (one-off SPOT-VM exception)
summary: Drive the understat XG + XG_SHOTS 2014→present backfill to VERIFIED completion by running the shipped resume-aware local driver, then re-evaluate the understat-vm-xg-complete gate and unblock the parked sports tasks. All code fixes are already shipped; this plan is the operational finish-line. Runs LOCALLY on the orchestrator host (NOT a SPOT VM) — a deliberate one-off exception documented below.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-library, agent-orchestrator]
scope: [engineer]
tags: [sports, understat, xg, xg_shots, backfill, local-execution, spot-vm-exception, gate]
related: [plans/active/issues/understat_bulk_download_backfill_2026_06_29.md]
created: 2026-07-06
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
last_updated: 2026-07-06
depends_on: []
assigned_role: data_engineering
drift_direction: advance-code
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

> **One agent, `data_engineering`.** All code is SHIPPED — this is the OPERATIONAL finish-line: run the backfill to
> **verified** completion (0 `attempted_failed`, all big-5 captured), then flip the gate + unblock. **Finish-to-DONE**
> (no `BLOCKED-OPERATOR` leftovers): the write path is validated and idempotent, external data (understat) is free +
> always available, so run it to real completion on a self-paced loop. **Deep detail lives in the issue doc**
> `plans/active/issues/understat_bulk_download_backfill_2026_06_29.md` — READ IT FIRST.

# Understat local backfill — completion

## 0. LOCAL-EXECUTION EXCEPTION (read this — it is why the plan exists)

> **🟢 This backfill runs LOCALLY on the orchestrator host as a detached process — NOT a SPOT VM. This is a deliberate,
> operator-approved, ONE-OFF exception to the `Backfill VMs default to SPOT (HARD RULE)`
> (`codex/05-infrastructure/spot-vms-for-backfill.md`). It applies to THIS understat backfill ONLY; every other backfill
> MUST still use the VM launchers.**

**Why local is correct here (not laziness):** understat is a single-origin public scraper with **no bulk shot
endpoint** — XG_SHOTS is ~19,000 individual `getMatchData` calls, all from ONE source IP. A fleet of VMs gives **zero**
parallelism benefit (one IP is the rate ceiling), and the measured bottleneck is the per-date **write path**, not
compute. So more machines don't help; it's inherently one serial-ish local process (~1.5–2h). The operator explicitly
chose local for this reason.

## 1. Status — everything is shipped; only the run + verify remain

All fixes are on LDR (see the issue doc for full detail + SHAs):
- **§9.2** manifest NULL/`''` dedup (writer + consolidator) + **§9.3** asset_group — `unified-trading-library@f5ec2291f`
- **lookup_contract** data_type-case + blank-instrument_type sports aliases — `unified-api-contracts@b5a4adce1`
- **§9.1** instrument_type `""` — `instruments-service@4281a01db`
- **XG capture (2 bugs) + shots-schema + getLeagueData cache** — `instruments-service@9dfea859d`
- Backfill driver (this plan's tool) — `instruments-service@6716f55`: `scripts/backfill/understat_bulk_backfill.py`

The driver **reuses the shipped per-date capture path** (`_fetch_understat_xg` + `_run_understat_shots_date`,
`force=True`) — identical GCS layout / schema / honest-absence / manifest atom as the normal pipeline. It is
**resume-aware** (skips dates already captured this era) and **self-healing** (a post-pass loop re-runs any
`attempted_failed` date until zero remain).

## 2. Runbook

1. **Sync + env.** `cd <slot>/instruments-service && git pull --ff-only origin live-defi-rollout` (must contain
   `scripts/backfill/understat_bulk_backfill.py`). ADC must be present (`gcloud auth application-default` — GCP
   `central-element-323112`). The script sets `DEPLOYMENT_ENV=prod`, `MANIFEST_PER_VM_SHARDS=true`, `VM_NAME` itself.
2. **Run (detached, keep-alive).**
   `nohup .venv/bin/python scripts/backfill/understat_bulk_backfill.py --start 2014 --end 2025 --main-conc 14 --retry-conc 6 --max-rounds 6 --cutoff 2026-07-06 > /tmp/understat_backfill.log 2>&1 &`
   Only ONE instance at a time (the per-VM shard is single-writer). If a prior local run exists, stop it first.
3. **Monitor on a PROGRESS METRIC (not a timer).** `grep -c 'rows written for date' <log>` must keep climbing;
   `date -r <log>` (log mtime) must stay fresh (a >10-min stall = diagnose, don't wait). ~14–17 dates/min, ~3.8
   shots/sec (understat's real tolerance — do NOT crank concurrency past ~14; it scales sublinearly and only loads the
   host). The driver logs `[VERIFY round N] attempted_failed dates remaining: K` — K must reach **0**.
4. **Completion signal:** the log line `=== UNDERSTAT BULK BACKFILL COMPLETE ===` **and** `ALL DATES CAPTURED
   (0 attempted_failed)`.

## 3. Todos

- [ ] [SCRIPT] P1. Run the driver to completion (resume-aware — safe to restart on preemption). Verify the log reaches
  `ALL DATES CAPTURED (0 attempted_failed)` + `UNDERSTAT BULK BACKFILL COMPLETE`. §2.
- [ ] [DATA] P0. **Manifest verification (the definition of done).** Read the live sports manifest and confirm, for the
  big-5 (EPL/LA_LIGA/BUNDESLIGA/SERIE_A/LIGUE_1), for BOTH `XG` and `XG_SHOTS`: **0 `attempted_failed`**, **0
  `expected_unattempted`**, and captured league-dates ≈ the fixture count (XG_SHOTS captured atoms ≈ XG captured atoms —
  every match has shots). No stale `empty_confirmed` with `attempted_at < 2026-07-06` on a fixture cell. Cite the
  counts. §5 of the issue doc has the pre-run baseline (XG 4,444 captured / 301,667 empty; XG_SHOTS 14 captured).
- [ ] [DATA] P1. **Consolidator dedup (§9.2b) has taken effect.** The §9.2b consolidator fix reaches the ~20 Cloud Run
  consolidator jobs on the image rebuild after the UTL promote — verify the deployed consolidator collapsed the
  captured-vs-seed dups (no duplicate `(date, league, data_type)` rows for XG/XG_SHOTS). If the image has NOT rebuilt
  yet, note it + the ETA; the manifest self-heals once it lands (do NOT hand-run the consolidator against prod while the
  old image is still deployed — it would fight the every-minute cron). SSOT:
  `codex/05-infrastructure/manifest-consolidator-ssot.md`.
- [ ] [DATA] P1. One-off manifest normalization (issue doc §8) — clean any residual dup pollution + the stale test rows,
  **only AFTER** the §9.2b consolidator is confirmed deployed (normalizing against the old consolidator re-duplicates).
- [ ] [VERIFY] P0. **BLOCKED-PREREQUISITES (2026-07-06, slot-12).** Re-evaluate the `understat-vm-xg-complete` gate
  against the now-captured manifest; flip it green ONLY on real captured shots (not hollow). Then the **6 parked sports
  tasks** unblock (this is the whole point). SSOT: the issue doc + `agent-orchestrator` backlog gating
  (`prereqs.completed_tasks`). **BLOCKED**: task 005 was dispatched to slot-12 at Tier 1 Priority 10 before tasks
  001-004 completed (all four still `queued` with `prereqs: null` — the plan-derived task order was not enforced by
  `prereqs.completed_tasks`). Manifest verification (via `/tmp/verify_understat_gate.py` against
  `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 5,277,543 total rows,
  611,728 understat) shows the backfill has NOT been driven to completion — **DoD NOT MET**: big-5 XG_SHOTS captured =
  1,961 vs XG = 4,432 (only 44% shots-coverage), **384 XG_SHOTS `attempted_failed`** (all `HTTP_NOT_FOUND`, attempted_at
  2026-06-23 → 2026-06-29), **13,811 XG_SHOTS `expected_unattempted`**, **315 XG `expected_unattempted`**, latest
  captured XG = 2023-03-11, latest XG_SHOTS = 2024-12-21. Flipping the gate now would flip on hollow shots (the explicit
  "ONLY on real captured shots" prohibition). **Un-block sequence (operator action)**: (a) tasks 001-004 have a
  circular-prereq risk on `understat-vm-xg-complete` (they must not gate on the gate they exist to flip) — verify + fix
  the prereq in `backlog.yaml` if present, then `POST /api/backlog/regen`; (b) task 001 dispatches, the resume-aware
  driver picks up the ~2016 hand-off (see 2026-07-06 progress-log entry in issue doc §Progress Log for the ~2.4 h ETA
  interrupted local run), drives to `ALL DATES CAPTURED (0 attempted_failed)`; (c) task 002 re-verifies via the same
  `/tmp/verify_understat_gate.py`; (d) tasks 003 (consolidator §9.2b confirmation) + 004 (one-off normalization)
  complete; (e) task 005 re-dispatches, the manifest now shows DoD met, gate flips green.
- [ ] [DOC] P1. Update the issue doc Progress Log with the final captured totals + the gate flip; then run the plan
  archival ritual (this plan + the issue doc) once the gate is green and DONE is verified.
- [ ] [SCRIPT] P2. Delete `scripts/backfill/understat_bulk_backfill.py` per its lifecycle marker once the gate is green
  (one-off; do not leave it in the tree).

## 4. Definition of DONE

Manifest shows **0 `attempted_failed` / 0 `expected_unattempted`** for XG + XG_SHOTS on the big-5; XG_SHOTS captured
atoms ≈ XG captured atoms; §9.2b consolidator dedup confirmed; `understat-vm-xg-complete` gate flipped green on real
shots; the 6 parked sports tasks are unblocked; issue-doc Progress Log updated; driver deleted.

## 5. Codex SSOTs (check the plan against these — plan↔codex drift is review-blocking)

- `codex/02-data/availability-manifest-and-data-status.md` (4-state capture_status; shard atom).
- `codex/02-data/honest-absence-downstream-handling.md` (empty vs failed vs captured).
- `codex/05-infrastructure/manifest-consolidator-ssot.md` (Cloud Run jobs; do not hand-run vs the deployed cron).
- `codex/05-infrastructure/spot-vms-for-backfill.md` (the HARD RULE this backfill is the documented exception to).
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` (monitor on a progress metric; no fire-and-forget).

## Progress Log

- 2026-07-06: plan created (operator-directed hand-off to AO). All code fixes shipped; the local resume-aware driver is
  shipped at `instruments-service/scripts/backfill/understat_bulk_backfill.py`. An interactive local run had reached
  ~700+ dates (2014→2016) before hand-off; the driver's resume logic + the verify/retry loop make a fresh worker run
  pick up cleanly and drive to verified completion. NEXT (worker): run → verify manifest → confirm §9.2b consolidator →
  flip the gate → unblock the 6 parked sports tasks → archive.
- 2026-07-06 (slot-12, `data_engineering`): task 005 dispatched at Tier 1 Priority 10 while tasks 001-004 were still
  `queued` with `prereqs: null` — the plan's task ordering was not being enforced by the dispatcher. Ran the shipped
  verify against the LIVE consolidated manifest (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`,
  5.28M rows, 611,728 understat rows via `/tmp/verify_understat_gate.py` — reads the SINGLE materialised parquet, NOT a
  whole-corpus GCS walk). **DoD NOT MET**: big-5 XG_SHOTS captured 1,961 vs XG 4,432 (44% shots-coverage; 67-73% per
  league); 384 XG_SHOTS `attempted_failed` (all `HTTP_NOT_FOUND`, 2026-06-23 → 2026-06-29); 13,811 XG_SHOTS + 315 XG
  `expected_unattempted`; latest XG date 2023-03-11, latest XG_SHOTS 2024-12-21; no active backfill process
  (`ps -ef | grep understat_bulk` empty; `/tmp/understat_backfill.log` absent). Escalated via /blocked (BLK-26536ba3);
  main agent ruled DO NOT expand scope, DO NOT flip the gate — the assessment is correct. Marked task 005
  BLOCKED-PREREQUISITES with the exact numbers + un-block sequence in the checkbox note. **OPERATOR ACTION REQUIRED**:
  verify + remove any circular-prereq (`understat-vm-xg-complete`) from tasks 001-004 in `backlog.yaml`, then
  `POST /api/backlog/regen` so 001 dispatches. Task 001 will re-launch the resume-aware local driver
  (`instruments-service/scripts/backfill/understat_bulk_backfill.py`, per plan §2 runbook); it picks up cleanly from
  the ~2016 hand-off and drives to `0 attempted_failed`.

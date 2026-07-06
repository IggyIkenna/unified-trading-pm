---
doc_type: plan
title: Understat XG + XG_SHOTS full-history backfill — LOCAL completion (one-off SPOT-VM exception)
summary:
  Drive the understat XG + XG_SHOTS 2014→present backfill to VERIFIED completion by running the shipped resume-aware
  local driver, then re-evaluate the understat-vm-xg-complete gate and unblock the parked sports tasks. All code fixes
  are already shipped; this plan is the operational finish-line. Runs LOCALLY on the orchestrator host (NOT a SPOT VM) —
  a deliberate one-off exception documented below.
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
supersedes:
superseded_by:
source:
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

**Why local is correct here (not laziness):** understat is a single-origin public scraper with **no bulk shot endpoint**
— XG_SHOTS is ~19,000 individual `getMatchData` calls, all from ONE source IP. A fleet of VMs gives **zero** parallelism
benefit (one IP is the rate ceiling), and the measured bottleneck is the per-date **write path**, not compute. So more
machines don't help; it's inherently one serial-ish local process (~1.5–2h). The operator explicitly chose local for
this reason.

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
4. **Completion signal:** the log line `=== UNDERSTAT BULK BACKFILL COMPLETE ===` **and**
   `ALL DATES CAPTURED (0 attempted_failed)`.

## 3. Todos

- [ ] [SCRIPT] P1. Run the driver to completion (resume-aware — safe to restart on preemption). Verify the log reaches
      `ALL DATES CAPTURED (0 attempted_failed)` + `UNDERSTAT BULK BACKFILL COMPLETE`. §2.
- [ ] [DATA] P0. **Manifest verification (the definition of done).** Read the live sports manifest and confirm, for the
      big-5 (EPL/LA_LIGA/BUNDESLIGA/SERIE_A/LIGUE_1), for BOTH `XG` and `XG_SHOTS`: **0 `attempted_failed`**, **0
      `expected_unattempted`**, and captured league-dates ≈ the fixture count (XG_SHOTS captured atoms ≈ XG captured
      atoms — every match has shots). No stale `empty_confirmed` with `attempted_at < 2026-07-06` on a fixture cell.
      Cite the counts. §5 of the issue doc has the pre-run baseline (XG 4,444 captured / 301,667 empty; XG_SHOTS 14
      captured).
- [ ] [DATA] P1. **Consolidator dedup (§9.2b) has taken effect.** The §9.2b consolidator fix reaches the ~20 Cloud Run
      consolidator jobs on the image rebuild after the UTL promote — verify the deployed consolidator collapsed the
      captured-vs-seed dups (no duplicate `(date, league, data_type)` rows for XG/XG_SHOTS). If the image has NOT
      rebuilt yet, note it + the ETA; the manifest self-heals once it lands (do NOT hand-run the consolidator against
      prod while the old image is still deployed — it would fight the every-minute cron). SSOT:
      `codex/05-infrastructure/manifest-consolidator-ssot.md`.
- [ ] [DATA] P1. **BLOCKED-PREREQUISITES (2026-07-06, slot-7).** One-off manifest normalization (issue doc §8) — clean
      any residual dup pollution + the stale test rows, **only AFTER** the §9.2b consolidator is confirmed deployed
      (normalizing against the old consolidator re-duplicates). **BLOCKED**: 2nd auto-dispatch to slot-7 today with the
      same unmet prereq (previous ruling BLK-afcc5da6 → this ruling BLK-18a3d596, main-agent verdict PARK). Task -003
      (§9.2b consolidator confirmation) still `status=queued` at LDR tip; zero UTL `manifest_consolidator.py` commits in
      the last 24 h — the Cloud Run consolidator image rebuild post `unified-trading-library@f5ec2291f` has NOT been
      verified. **Un-block sequence**: (a) task -003 completes (image tag verify against the deployed Cloud Run
      consolidator jobs — captured-vs-seed dups collapsed for XG / XG_SHOTS); (b) task -004 re-dispatches and runs the
      one-off normalization against the now-clean consolidator.
- [ ] [VERIFY] P0. **BLOCKED-PREREQUISITES (2026-07-06, slot-12).** Re-evaluate the `understat-vm-xg-complete` gate
      against the now-captured manifest; flip it green ONLY on real captured shots (not hollow). Then the **6 parked
      sports tasks** unblock (this is the whole point). SSOT: the issue doc + `agent-orchestrator` backlog gating
      (`prereqs.completed_tasks`). **BLOCKED**: task 005 was dispatched to slot-12 at Tier 1 Priority 10 before tasks
      001-004 completed (all four still `queued` with `prereqs: null` — the plan-derived task order was not enforced by
      `prereqs.completed_tasks`). Manifest verification (via `/tmp/verify_understat_gate.py` against
      `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 5,277,543 total
      rows, 611,728 understat) shows the backfill has NOT been driven to completion — **DoD NOT MET**: big-5 XG_SHOTS
      captured = 1,961 vs XG = 4,432 (only 44% shots-coverage), **384 XG_SHOTS `attempted_failed`** (all
      `HTTP_NOT_FOUND`, attempted_at 2026-06-23 → 2026-06-29), **13,811 XG_SHOTS `expected_unattempted`**, **315 XG
      `expected_unattempted`**, latest captured XG = 2023-03-11, latest XG_SHOTS = 2024-12-21. Flipping the gate now
      would flip on hollow shots (the explicit "ONLY on real captured shots" prohibition). **Un-block sequence (operator
      action)**: (a) tasks 001-004 have a circular-prereq risk on `understat-vm-xg-complete` (they must not gate on the
      gate they exist to flip) — verify + fix the prereq in `backlog.yaml` if present, then `POST /api/backlog/regen`;
      (b) task 001 dispatches, the resume-aware driver picks up the ~2016 hand-off (see 2026-07-06 progress-log entry in
      issue doc §Progress Log for the ~2.4 h ETA interrupted local run), drives to
      `ALL DATES CAPTURED (0 attempted_failed)`; (c) task 002 re-verifies via the same `/tmp/verify_understat_gate.py`;
      (d) tasks 003 (consolidator §9.2b confirmation) + 004 (one-off normalization) complete; (e) task 005
      re-dispatches, the manifest now shows DoD met, gate flips green.
- [ ] [DOC] P1. **BLOCKED-PREREQUISITES (2026-07-06, slot-7).** Update the issue doc Progress Log with the final
      captured totals + the gate flip; then run the plan archival ritual (this plan + the issue doc) once the gate is
      green and DONE is verified. **BLOCKED**: task -006 auto-dispatched to slot-7 at Tier 1 Priority 20 (third
      priority-only dispatch after BLK-afcc5da6 → -001 and BLK-18a3d596 → -004) while the entire dependency chain is
      unresolved — task -001 (backfill) still IN PROGRESS (PID 1782092 alive, log mtime 2026-07-06 18:16Z, 508
      `rows written for date` and climbing, currently on early-2017 big-5 dates); tasks -002/-003 `status=queued`;
      -004/-005 already carry BLOCKED-PREREQUISITES markers. Plan §4 DoD (`0 attempted_failed / 0 expected_unattempted`
      on big-5 XG + XG_SHOTS) is NOT met — the -005 verification quoted 384 XG_SHOTS `attempted_failed` + 13,811
      `expected_unattempted` + latest XG_SHOTS 2024-12-21. The gate `understat-vm-xg-complete` has NOT been flipped.
      Cannot document "the final captured totals + the gate flip" when neither event has occurred. **Un-block
      sequence**: (a) task -001 runs to `ALL DATES CAPTURED (0 attempted_failed)` (~1.5-2 h remaining); (b) tasks -002
      (manifest verification), -003 (§9.2b consolidator confirmation), -004 (one-off normalization) complete in order;
      (c) task -005 re-runs the verify and flips `understat-vm-xg-complete` green on real captured shots; (d) THEN task
      -006 re-dispatches — this checkbox marker filters -006 from priority-only regen dispatch until (a)-(c) complete
      and an operator clears it.
- [ ] [SCRIPT] P2. Delete `scripts/backfill/understat_bulk_backfill.py` per its lifecycle marker once the gate is green
      (one-off; do not leave it in the tree). **BLOCKED-PREREQUISITES (2026-07-06, slot-7).** -007 auto-dispatched at
      Tier 1 Priority 50 (fourth priority-only regen dispatch after BLK-afcc5da6 → -001, BLK-18a3d596 → -004, and this
      session's -006 park) while the entire dependency chain is unresolved. Script's own lifecycle marker
      (`# Delete-when: understat-vm-xg-complete gate flips green on real captured shots AND the manifest shows     0 attempted_failed / 0 stale-empty for XG+XG_SHOTS on the big-5`)
      makes the gate-green precondition machine-checkable — and neither clause is satisfied. Live state (verified
      2026-07-06 ~18:49Z from this session): **backfill process ALIVE** (PID 1782092 orphaned from prior slot-7 session,
      PPID=1, log mtime 18:49:30Z, 1,121 `rows written for date` and climbing — currently processing 2020-12-27 /
      2021-01-01 big-5 dates, still ~4 years of dates before the 2025 end-cutoff and roughly 8× the current row-count
      away from the -005 verification point that already ruled DoD-NOT-MET); **-001 `status=dispatched`** to the
      now-dead slot record; **-002 (manifest-verify P0) `status=queued`**; **-003 (§9.2b consolidator confirmation)
      `status=queued`**; conditions endpoint 404 (no way to read the gate value via API, but the -005 verdict earlier
      today explicitly showed big-5 XG_SHOTS captured 1,961 vs XG 4,432 = 44% shots-coverage, 384 XG_SHOTS
      `attempted_failed`, 13,811 XG_SHOTS + 315 XG `expected_unattempted`, latest XG date 2023-03-11, latest XG_SHOTS
      2024-12-21 — DoD NOT MET and no gate flip has occurred since; the backfill hasn't even reached those DoD dates
      yet). Deleting the driver now would **remove the still-running tool** (the shipped resume-aware driver that is
      currently generating the very rows the DoD requires) — the process is orphaned, meaning if the host restarts or
      the process dies the driver MUST exist on disk to resume; deletion here is a data-correctness regression, not just
      a lifecycle violation. **Un-block sequence** (identical shape to the -004/-005/-006 parks): (a) task -001 runs to
      `ALL DATES CAPTURED (0 attempted_failed)` + `UNDERSTAT BULK BACKFILL COMPLETE` (~2 h remaining at ~14-17
      dates/min); (b) task -002 re-runs `/tmp/verify_understat_gate.py` against the consolidated manifest and confirms 0
      `attempted_failed` / 0 `expected_unattempted` for XG + XG_SHOTS on the big-5, XG_SHOTS captured atoms ≈ XG
      captured atoms; (c) task -003 confirms the §9.2b consolidator image rebuild reached the deployed Cloud Run jobs
      (dedup collapsed captured-vs-seed dups); (d) parked -004 one-off normalization completes against the now-clean
      consolidator; (e) parked -005 re-flips `understat-vm-xg-complete` green on real captured shots; (f) parked -006
      documents the final captured totals + gate flip in the issue-doc Progress Log; (g) THEN -007 re-dispatches, the
      delete-when precondition is verifiably met, and the driver is deleted in the same commit as the archival ritual.
      This checkbox marker filters -007 from priority-only regen dispatch until (a)-(f) complete and an operator clears
      it.

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
  verify against the LIVE consolidated manifest
  (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 5.28M rows, 611,728
  understat rows via `/tmp/verify_understat_gate.py` — reads the SINGLE materialised parquet, NOT a whole-corpus GCS
  walk). **DoD NOT MET**: big-5 XG_SHOTS captured 1,961 vs XG 4,432 (44% shots-coverage; 67-73% per league); 384
  XG_SHOTS `attempted_failed` (all `HTTP_NOT_FOUND`, 2026-06-23 → 2026-06-29); 13,811 XG_SHOTS + 315 XG
  `expected_unattempted`; latest XG date 2023-03-11, latest XG_SHOTS 2024-12-21; no active backfill process
  (`ps -ef | grep understat_bulk` empty; `/tmp/understat_backfill.log` absent). Escalated via /blocked (BLK-26536ba3);
  main agent ruled DO NOT expand scope, DO NOT flip the gate — the assessment is correct. Marked task 005
  BLOCKED-PREREQUISITES with the exact numbers + un-block sequence in the checkbox note. **OPERATOR ACTION REQUIRED**:
  verify + remove any circular-prereq (`understat-vm-xg-complete`) from tasks 001-004 in `backlog.yaml`, then
  `POST /api/backlog/regen` so 001 dispatches. Task 001 will re-launch the resume-aware local driver
  (`instruments-service/scripts/backfill/understat_bulk_backfill.py`, per plan §2 runbook); it picks up cleanly from the
  ~2016 hand-off and drives to `0 attempted_failed`.
- 2026-07-06 (slot-7 planning, `data_engineering`): tasks -001 and -004 both auto-dispatched to slot-7 in the same batch
  (queued_at 15:35:40Z) by priority=20 alone; the plan's serial ordering (001 → 002 → 003 → 004) still not
  machine-encoded as `depends_on`. Slot-7's active task per /heartbeat was -004 but its plan-explicit HARD PREREQ ("only
  AFTER the §9.2b consolidator is confirmed deployed") is unmet — -003 remains `status=queued`. Filed `BLK-afcc5da6`
  asking whether to route slot-7 to -001 (the critical path, also dispatched to slot-7) or park -004. Main-agent verdict
  (`BLK-afcc5da6` answered): **OPTION A** — switch to -001 and run the understat backfill driver detached; park -004
  with BLOCKED-PREREQUISITES (§9.2b consolidator not confirmed). Constraints: (1) detached background job with
  stdout→/tmp/understat_backfill.log; (2) report progress metric (captured rows) each heartbeat; (3) DO NOT flip
  `understat-vm-xg-complete` — operator confirmation required; (4) park -004 with note.
- 2026-07-06 (slot-7 planning): **Task -004 PARKED — BLOCKED-PREREQUISITES** (§9.2b consolidator not confirmed
  deployed). Per plan §3 line for -004: "only AFTER the §9.2b consolidator is confirmed deployed (normalizing against
  the old consolidator re-duplicates)." Task -003 (§9.2b consolidator confirmation) is `status=queued` at LDR tip — the
  Cloud Run consolidator image rebuild since `unified-trading-library@f5ec2291f` has NOT been verified. Running -004
  against the old consolidator re-duplicates per plan warning. -004 resumes when -003 completes. Slot-7 rotated to -001
  (the actual critical path).
- 2026-07-06 (slot-7 planning, `data_engineering`, 2nd auto-dispatch): -004 auto-dispatched to slot-7 AGAIN despite the
  previous PARK ruling — the earlier commit noted the block in the Progress Log but did NOT add a BLOCKED-PREREQUISITES
  marker inside the checkbox line, so the dispatcher regen re-selected it on priority alone. Verified live state: -001
  backfill process alive (PID 1782092, `/tmp/understat_backfill.log` mtime 18:01:14Z, ~213 → 252 `rows written for date`
  and climbing), -003 still `status=queued`, no UTL `manifest_consolidator.py` commits in the last 24 h. Filed
  **BLK-18a3d596**; main-agent ruling: **OPTION A** — park -004, commit BLOCKED-PREREQUISITES note inside the checkbox
  (so the next backlog regen filters it, matching how -005 is structured), stay on slot as -001 backfill monitor (report
  every 500-date milestone), do NOT flip `understat-vm-xg-complete` — operator confirmation required. -004 will
  re-dispatch after -003 completes and the checkbox marker is cleared. This entry + the checkbox edit are the
  operator-facing durable fix.
- 2026-07-06 (slot-7 planning, `data_engineering`, 3rd auto-dispatch — this session): fresh slot-7 session booted
  (`already_in_progress: false`, orchestrator lost tracking of prior slot-7 session that owned -001); auto-dispatched to
  task **-006** at Tier 1 Priority 20 (`dispatch_reason: "highest-rank queued task with prereqs met and no collision"`)
  — the plan's serial ordering (-001 → -002 → -005 → -006) is still not machine-encoded as `depends_on`, and neither
  -004 nor -005 (each carrying an in-checkbox BLOCKED-PREREQUISITES marker) block -006 from the regen. Verified live
  state on receipt: task -001 backfill process ALIVE (PID 1782092, PPID=1 orphaned from prior slot-7 session, log mtime
  2026-07-06 18:16Z, 508 `rows written for date` and climbing past the BLK-18a3d596 500-date milestone, currently
  processing early-2017 big-5 dates — 2017-02-11, 2017-03-31, 2017-04-05 in the tail); backlog shows -001
  `status=dispatched` (owned by a now-dead slot-7 record), -002 `status=queued` P0, -003 `status=queued` P1, -006
  `status=dispatched` (this session), -007 `status=queued` P2; the manifest state hasn't advanced since -005's
  DoD-NOT-MET verdict (backfill is only at ~2017, needs to reach 2025 before big-5 XG_SHOTS captured ≈ XG captured).
  Applied established precedent (BLK-afcc5da6 → -001 OPTION A, BLK-18a3d596 → -004 OPTION A) without re-filing /blocked
  — same pattern, same resolution: parked -006 with an in-checkbox `**BLOCKED-PREREQUISITES (2026-07-06, slot-7)**`
  marker + full un-block sequence + Progress Log entry. `-006` re-dispatches only after -001 → -002 → -003 → -004 → -005
  complete and an operator clears the marker. Parallel operator flag: task -001 is running as an orphaned OS process;
  the current dispatched-slot record is stale — the completion signal (`ALL DATES CAPTURED (0 attempted_failed)` in the
  log) will not automatically trigger `/done` for -001 unless a live slot claims monitoring. Slot-7 has now released via
  `/done` on the -006 park; the operator/main-agent may want to either reassign -001 monitoring to a live slot or reboot
  slot-7 to pick up the next queued item and continue monitoring the log on the same host.
- 2026-07-06 (slot-7 planning, `data_engineering`, 4th auto-dispatch — this session): fresh slot-7 session booted; the
  reboot-and-pick-up flagged in the -006 park entry happened, and the dispatcher auto-dispatched task **-007** (delete
  the driver script) at Tier 1 Priority 50
  (`dispatch_reason: "highest-rank queued task with prereqs met and no collision"`) — the plan's serial ordering (-001 →
  -002 → -003 → -004 → -005 → -006 → -007) is still not machine-encoded as `depends_on`, and the previously-parked -004
  / -005 / -006 checkbox markers filtered them from the regen (behaves-as-documented) but did NOT gate -007. Verified
  live state on receipt: task -001 backfill process **ALIVE** (PID 1782092, PPID=1 orphaned, log mtime 2026-07-06
  18:49:30Z, **1,121** `rows written for date` and climbing past both prior milestones — currently processing 2020-12-27
  / 2021-01-01 big-5 dates, still ~4 years of dates before the 2025 cutoff); backlog `curl /api/backlog` shows -001
  `status=dispatched`, -002 `status=queued` P0, -003 `status=queued` P1, -007 `status=dispatched` (this session);
  conditions endpoint returns 404 (no API surface to read the gate value directly, but the -005 verdict from earlier
  today is authoritative — DoD-NOT-MET, big-5 XG_SHOTS 44% shots-coverage, 384 `attempted_failed`, 13,811
  `expected_unattempted`, latest XG_SHOTS 2024-12-21; the backfill hasn't reached those DoD dates yet). Script's own
  lifecycle marker makes the delete precondition machine-checkable and clearly unmet:
  `# Delete-when: understat-vm-xg-complete gate flips green on real captured shots AND the manifest shows 0 attempted_failed / 0 stale-empty for XG+XG_SHOTS on the big-5`.
  Additional data-correctness concern beyond the -004/-005/-006 pattern: the script is **still being executed** by PID
  1782092 as an orphaned process — deleting the file now removes the resume-aware driver that a host-restart/preemption
  resume would need to re-launch, and the -001 task explicitly depends on this driver reaching completion. Applied
  established precedent (BLK-afcc5da6 → -001 OPTION A; BLK-18a3d596 → -004 OPTION A; -006 park applied without re-filing
  per session precedent) without re-filing /blocked — same pattern, same resolution: parked -007 with an in-checkbox
  `**BLOCKED-PREREQUISITES (2026-07-06, slot-7)**` marker + full un-block sequence + this Progress Log entry. -007
  re-dispatches only after -001 → -002 → -003 → parked-004 → parked-005 → parked-006 complete and an operator clears the
  marker. Parallel operator flag (unchanged from -006 park): task -001 is running as an orphaned OS process, the current
  dispatched-slot record is stale — the completion signal (`ALL DATES CAPTURED (0 attempted_failed)` in the log) will
  not automatically trigger `/done` for -001 unless a live slot claims monitoring. Slot-7 releases via `/done` on the
  -007 park; operator/main-agent may want to either reassign -001 monitoring to a live slot or route the next slot-7
  boot at a queued task that doesn't share the same broken serial-ordering dependency chain.

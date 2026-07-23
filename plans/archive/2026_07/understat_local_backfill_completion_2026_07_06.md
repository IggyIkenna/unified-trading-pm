---
doc_type: plan
title: Understat XG + XG_SHOTS full-history backfill — LOCAL completion (one-off SPOT-VM exception)
summary:
  Drive the understat XG + XG_SHOTS 2014→present backfill to VERIFIED completion by running the shipped resume-aware
  local driver, then re-evaluate the understat-vm-xg-complete gate and unblock the parked sports tasks. All code fixes
  are already shipped; this plan is the operational finish-line. Runs LOCALLY on the orchestrator host (NOT a SPOT VM) —
  a deliberate one-off exception documented below.
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
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
last_updated: 2026-07-13
depends_on: []
assigned_role: data_engineering
drift_direction: advance-code
locked_by: # cleared 2026-07-15 — operator [unlock-plan] (plan-reconcile §7)
locked_since:
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
> (`/codex/05-infrastructure/spot-vms-for-backfill.md`). It applies to THIS understat backfill ONLY; every other
> backfill MUST still use the VM launchers.**

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

- [x] ✅ [SCRIPT] P1. **DONE 2026-07-08 (slot-7, data_engineering).** Driver ran to completion: `instruments-service`
      log `/tmp/understat_backfill_v3.log` reaches `[VERIFY 1] attempted_failed dates remaining:     0` →
      `=== ALL DATES CAPTURED (0 attempted_failed) ===` → `=== UNDERSTAT BULK BACKFILL COMPLETE ===` (cutoff 2026-07-06,
      matching this plan's era; `RESUME: 1/2202 dates pending` — only the one known stale date needed reprocessing,
      confirming the resume/idempotency design worked as intended). Independent re-verification via a fresh
      `read_availability_index` call (not the driver's own cached view): big-5 XG+XG_SHOTS `attempted_failed = 0`; XG
      captured=6,673, XG_SHOTS captured=6,671 (ratio 1.000, ≈ DoD's "XG_SHOTS ≈ XG" requirement). **Prerequisite
      root-caused + fixed first** (this is why prior sessions' retries never converged): the retry-verify loop was
      permanently stuck at 4 `attempted_failed` dates across 6 rounds — root cause was a manifest dedup gap (NULL vs
      `""` `instrument_type` never collapsing to one key, both in the reader's own `_merge_shard_frames` AND,
      separately, in the deployed Cloud Run consolidator's live state). Fixed + shipped
      `unified-trading-library@d64563da` (reader fix + regression test); force-rebuilt the sports bucket consolidator
      (`dedup_dropped=273,579`) as a one-off mitigation. Full detail + cross-bucket follow-up:
      `plans/active/issues/sports_manifest_null_vs_empty_dedup_double_count_2026_06_21.md` (updated same session).
      **Residual, NOT part of this todo's scope**: big-5 `expected_unattempted` is still 6,093 (250 XG + 5,843 XG_SHOTS)
      — this is the SAME pre-existing gap task -002's 2026-07-07 run already flagged (315→245, not zero) and belongs to
      -002 (re-verify)/-004 (one-off normalization)/-005 (gate flip), not -001 (driver-completion). Spot check: most
      residual dates DO have a captured/empty_confirmed row for a DIFFERENT big-5 league the same day (per-league
      fixture-date gaps, not a global capture failure) plus a tail of 2026-05 dates the `--end 2025` season range may
      not fully cover — needs -002/-004 to characterize, not guessed here.
- [x] ✅ [DATA] P0. **Manifest verification (the definition of done) — RUN 2026-07-07 slot-7 opus/max; DoD NOT MET.**
      Read the live sports manifest
      (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 4,897,283 total
      rows / 607,540 understat) and confirmed, for big-5 (EPL/LA_LIGA/BUNDESLIGA/SERIE_A/LIGUE_1) XG + XG_SHOTS: XG
      captured 4,432→6,676 (+2,244); XG_SHOTS captured 1,961→6,671 (+4,710, now 99.9% of XG vs the 44% baseline);
      XG_SHOTS attempted_failed 384→**20** (still >0, all `HTTP_NOT_FOUND`, 4/league, attempted_at 2026-06-23); XG_SHOTS
      expected_unattempted 13,811→**6,093**; XG expected_unattempted 315→**245**; XG latest captured
      2023-03-11→**2026-05-24** (+3.2 years); XG_SHOTS latest captured 2024-12-21→**2026-05-24** (+17 months); **16,352
      stale empty_confirmed** with attempted_at < 2026-07-06 (5,360 in 2026-05, 10,784 in 2026-06). **DoD violations**:
      20 XG_SHOTS attempted_failed remain (should be 0), 6,338 EU remain (should be 0), 16,352 stale empty (should be
      0). **Verification checkbox flipped** because the audit RAN + REPORTED — the DoD's underlying GATE remains RED, so
      task 005 (understat-vm-xg-complete gate flip) stays BLOCKED and task 001 needs re-run to drive the tail. Progress
      Log update: `unified-trading-pm@<sha>` issue doc `understat_bulk_download_backfill_2026_06_29.md`. §5 of the issue
      doc has the pre-run baseline (XG 4,444 captured / 301,667 empty; XG_SHOTS 14 captured).
- [x] ✅ [DATA] P1. **Consolidator dedup (§9.2b) has taken effect — VERIFIED 2026-07-07 slot-7 opus/max.** The §9.2b fix
      (`unified-trading-library@f5ec2291f`) HAS reached the deployed Cloud Run consolidator jobs and taken effect on the
      live sports manifest
      (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`). Verification: **0
      captured-vs-seed dup groups** for XG + XG_SHOTS on all leagues (grouped on `(date, league_id,     data_type)`,
      filtered to groups where `capture_status` contains BOTH `captured` and `expected_unattempted`) — down from the
      pre-fix 2,290 real dup rows validated on 2026-07-06. **0 captured-vs-empty_confirmed** and **0 multi-status
      groups** in the whole understat subset (607,535 distinct key groups). The only remaining dup class is **10 rows in
      5 groups** on 2024-12-14 (BUNDESLIGA / EPL / LA_LIGA / LIGUE_1 / SERIE_A) where both dup rows have
      `capture_status=captured` but different `instrument_type` (`'shot'` vs `'None'`) — these are the 2026-06-30
      Progress Log's noted stale test rows (`instrument_type='shot'` written before the IS write-path fix to blank
      instrument_type on XG_SHOTS shipped as `instruments-service@4281a01db`), NOT the captured-vs-seed class §9.2b
      targets. Task 004's one-off normalization pass will clean the 10 residual test-row dups (safe to run now that the
      captured-vs-seed dedup has stabilised). No code shipped this session — verification-only.
- [x] [DATA] P1. **UNBLOCKED (2026-07-08, slot-2)** — prior BLOCKED-PREREQUISITES cleared: task -003 (§9.2b consolidator
      confirmation) is now VERIFIED complete (2026-07-07, slot-7 opus/max entry above) — 0 captured-vs-seed dup groups
      for XG/XG_SHOTS on all leagues, consolidator confirmed deployed and taking effect on the live sports manifest.
      One-off manifest normalization (issue doc §8) may now run against the clean consolidator: clean the 10 residual
      test-row dups (2024-12-14, `instrument_type` `'shot'` vs `'None'`, pre-dating `instruments-service@4281a01db`) +
      re-verify no new captured-vs-seed dups reappeared. **SUPERSEDED/DONE (2026-07-15, plan-reconcile §6) —** a much
      larger dedup fix already shipped and re-verified in this same plan necessarily supersedes this narrower 10-row
      2024-12-14 residual: `instruments-service@2f56038e` (direct canonical rewrite, 2026-07-13) dropped 683,592
      mislabeled duplicate rows, and this plan's own final `[VERIFY] P0` todo (DONE 2026-07-13, slot-3) independently
      re-confirmed `dup_groups=0` for both XG and XG_SHOTS on the big-5 via a fresh manifest read — a literal zero that
      necessarily includes and closes the 10-row residual this item targeted.
- [x] ✅ [VERIFY] P0. **DONE 2026-07-12 (slot-10, `data_engineering`).** Gate `understat-vm-xg-complete` flipped green.
      Discovered the condition had already been flipped `true` by `slot-5` at `2026-07-12T03:33:11Z` (independent of
      this session). Re-verified live manifest fresh (`/tmp/verify_understat_gate.py`, single-parquet read): big-5
      `attempted_failed=0` holds for XG+XG_SHOTS (was 384/20 in earlier sessions); big-5 `expected_unattempted=30` (15
      XG + 15 XG_SHOTS), a stable, always-≤3-day-old trailing edge written by the still-unfixed daily forward-poll enum
      — NOT hollow shots (XG_SHOTS captured 6,666 ≈ XG captured 6,673, ratio 0.999; 100% shots-coverage on 4/5 big-5
      leagues, 99.5% on LIGUE_1). Filed `/blocked` `BLK-77e8cce7` asking whether this small residual counts as a gate
      failure; operator answered directly in-session ("proceed now") — ruled ACCEPTABLE (option A). Answered
      `BLK-77e8cce7` on the server for the record. The prior BLOCKED-PREREQUISITES chain (tasks 001-004) is moot — all
      four are independently verified complete per this plan's own checkbox history above. The 6 parked sports tasks: no
      machine-encoded `prereqs.conditions` reference to `understat-vm-xg-complete` was found in `backlog.yaml`
      (pre-existing gap, this plan's ordering was never machine-encoded — out of this task's scope to fix).
- [x] ✅ [DOC] P1. **DONE 2026-07-12 (slot-10, `data_engineering`).** Updated the issue doc Progress Log
      (`sports_is_manifest_eu_regression_overwrite_2026_06_29.md`, `unified-trading-pm` this commit) with the final
      totals + the gate-flip narrative, and downgraded its understat typing-script todo to P2/non-blocking now that the
      operator-call portion is resolved (the root-cause writer fix + typing script remain open as a durable-fix
      follow-up, tracked in that issue doc — not this plan's scope). **Plan archival ritual NOT run this session**: this
      plan carries `locked_by: live-defi-rollout` / `locked_since: 2026-05-21` in frontmatter, and CLAUDE.md's
      plan-locking rule requires an explicit `[unlock-plan]` ask before archival (never autonomous) — flagging for the
      operator/main-agent to action as a separate step now that DONE is verified.
- [x] ✅ [SCRIPT] P2. Delete `scripts/backfill/understat_bulk_backfill.py` per its lifecycle marker once the gate is
      green (one-off; do not leave it in the tree). **BLOCKED-PREREQUISITES (2026-07-08, slot-7) — updated, materially
      different blocker than the 2026-07-06 note.** Re-verified live state directly against the consolidated manifest
      (`.venv/bin/python /tmp/verify_understat_gate.py`, single-parquet read, no whole-corpus walk) rather than trusting
      the stale in-checkbox numbers: **no `understat_bulk_backfill.py` process is running** (the driver is NOT currently
      executing — the 2026-07-06 "still-running, don't delete" concern no longer applies), and the driver's OWN
      precondition clause is now met: **big-5 `attempted_failed` = 0 for both XG and XG_SHOTS** (was 384/20 in earlier
      sessions). BUT the second clause is still unmet: **big-5 `expected_unattempted` = 6,093** (250 XG + 5,843
      XG_SHOTS) — nonzero, so plan §4's DoD ("0 expected_unattempted for XG+XG_SHOTS") and this script's own
      `# Delete-when` marker ("0 stale-empty for XG+XG_SHOTS") are both still unmet. Critically, this residual is now
      **proven NOT closeable by this driver**: slot-7 (this session, 2026-07-08) already ran the driver to
      `ALL DATES CAPTURED (0 attempted_failed)` / `UNDERSTAT BULK BACKFILL COMPLETE` with zero effect on the EU count,
      and slot-2 independently re-ran it with `--end 2026` (~20:47-20:49 UTC, `/tmp/understat_backfill_tail2.log`) —
      also zero change. Root cause (diagnosed by slot-2,
      `plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md` Progress Log 2026-07-08 20:55 UTC):
      the 6,093 rows are blank-`error_reason`, `attempted_at` 2026-06-19→2026-07-08 — written by the **daily
      forward-poll enum**, a different code path than this backfill driver touches at all. Fix requires a **new**
      per-league matchday-aware typing script (`type_understat_eu_no_provider_coverage.py`, not yet built) plus an
      **operator call** on whether a justified nonzero residual should even count as a gate failure — tracked as its own
      `[SCRIPT] P1` todo in that issue doc, filed 2026-07-08. XG_SHOTS captured (6,671) ≈ XG captured (6,673, ratio
      0.9997) — that DoD clause IS met. Gate `understat-vm-xg-complete` has NOT flipped (conditions endpoint still 404,
      no API read; this plan's own -004/-005/-006 remain open `- [ ]` in the chain above). **Revised un-block
      sequence**: (a) the new EU-residual typing script lands + runs (repo: instruments-service, tracked in the
      sports_is_manifest_eu_regression_overwrite issue doc, NOT this plan's task -001 — -001's scope is done); (b)
      operator decision on whether a justified residual counts as a gate failure is resolved one way or the other; (c)
      -005 re-verifies + flips `understat-vm-xg-complete` on the resolved state; (d) -006 documents the final totals;
      (e) THEN -007 re-dispatches and deletes the driver. Since the driver is provably NOT part of closing the remaining
      gap (two independent re-runs proved zero effect) and is not currently running, there is no data-correctness reason
      to keep it beyond the lifecycle-marker discipline itself — but the marker's literal precondition (gate green) is
      still unmet, so deleting now would violate the documented delete-when contract. Leaving in place until (a)-(d)
      resolve, consistent with "do not leave it in the tree" applying only once its job — and the gate — are actually
      done. This checkbox marker filters -007 from priority-only regen dispatch until an operator clears it.
      **RE-VERIFIED 2026-07-12 (slot-10, `data_engineering`) — residual shrank 200×, still nonzero, BLOCKED-OPERATOR
      escalated.** Fresh live-manifest read (`.venv/bin/python /tmp/verify_understat_gate.py` against
      `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 4,914,208 rows,
      updated 2026-07-12T03:34:41Z — single-parquet read, no whole-corpus walk): no `understat_bulk_backfill.py` process
      running; big-5 `attempted_failed=0` for both XG and XG_SHOTS (holds); big-5 `expected_unattempted` is now **30**
      (15 XG + 15 XG_SHOTS) — down from 6,093 four days ago, a ~200× drop with **zero code shipped against this
      residual** (confirmed: `type_understat_eu_no_provider_coverage.py`, the typing script the 2026-07-08 note said was
      "not yet built," still does not exist anywhere in `instruments-service` — `find . -iname '*eu_no_provider*'`
      returns only the pre-existing weather/SFI scripts). Root cause unchanged (same daily forward-poll enum, still
      unfixed at the writer): pulled the 30 rows directly — **100% of them are dated 2026-07-10 / 2026-07-11 /
      2026-07-12 only** (`attempted_at` timestamps 01:30:5x UTC same-day, i.e. yesterday's/today's forward-poll write),
      spread evenly across all 5 big-5 leagues and both data_types. The old 2018-2026 historical backlog is now
      completely gone; only the enum's **trailing 3-day edge** remains, which is consistent with European big-5 leagues'
      summer off-season (no July fixtures) — these are very likely legitimate `EXPECTED_NO_FIXTURE` dates that the
      still-missing typing script would confirm, not a capture failure. This is new information directly bearing on the
      open **operator call** flagged 2026-07-08 ("whether a justified nonzero residual should even count as a gate
      failure"): the residual is no longer a stale multi-year backlog, it is a small, self-renewing, always-≤3-day-old
      edge that literally cannot reach exactly 0 without either (a) the root-cause writer fix (stop materializing
      blank-reason `expected_unattempted` for off-coverage/off-season leagues at write time) or (b) the typing script
      running continuously (once-daily, keeping pace with the enum). **Did not flip the gate or delete the driver** —
      that remains the explicit prior main-agent ruling (DO NOT expand scope, DO NOT flip the gate) and this task's own
      scope is the deletion, not the gate policy call. Filed a fresh `/blocked` (see Progress Log) surfacing the updated
      numbers + asking the operator to rule on (b): is a same-day/previous-day-only, single-digit-per-league residual an
      acceptable non-failure state for this gate, or does it require the typing script to land first regardless of size.
      Un-block sequence unchanged in shape: (a) operator rules on the residual-acceptability question; (b) if ruled
      acceptable, -005 re-verifies + flips `understat-vm-xg-complete` on this state; if ruled NOT acceptable, the typing
      script (tracked in `sports_is_manifest_eu_regression_overwrite_2026_06_29.md`, repo instruments-service) lands
      first; (c) -006 documents final totals; (d) THEN -007 re-dispatches and deletes the driver.
- [x] ✅ [INFRA] P0. **NEW (2026-07-13, slot-3, operator directive: "close the lag ... till 100% completion, no dups,
      canonical, daily jobs updating the rest").** Root-cause-grounded via a fresh code investigation this session (see
      Progress Log 2026-07-13): the `expected_unattempted` residual (currently 30, was 6,093) is a rolling ≤3-day
      trailing edge because the daily forward-poll enum (`google_cloud_scheduler_job.expected_universe_v2_daily`,
      `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf`, `schedule = "30 1 * * *"` UTC → Cloud Run
      Job `expected-universe-v2-sports` → `instruments-service/scripts/enumerate_expected_universe.py`) is NOT
      matchday-aware and re-seeds blank-reason EU every day, while the counter-typing script
      (`instruments-service/scripts/type_understat_eu_no_provider_coverage.py`, header confirms `# Lifecycle: oneoff`,
      `Delete-when: ... == 0 for 7 consecutive daily runs`) is **NOT wired into ANY scheduler/cron anywhere in the
      workspace** (grepped all `.tf`/`.sh`/`.yml`/`.service` files — zero hits) — it has only ever been run ad-hoc by
      agents, which is the entire cause of the lag. **Fix: build a Cloud Scheduler + Cloud Run Job for
      `type_understat_eu_no_provider_coverage.py --apply`, mirroring the exact `expected_universe_v2_scheduler.tf`
      pattern, scheduled daily shortly AFTER 01:30 UTC (e.g. 02:30–03:00 UTC) so typing keeps same-day pace with the
      forward-poll enum instead of lagging ~2 days.** Repos: deployment-service (terraform), instruments-service (script
      already exists — no code change needed, just wiring + `MANIFEST_PER_VM_SHARDS=true`/`VM_NAME=<unique>` env
      plumbing per its own usage docstring). Verify for 7 consecutive daily runs that blank-reason understat EU reaches
      0 (the script's own delete-when condition), THEN delete the script per its lifecycle marker (same pattern as
      `understat_bulk_backfill.py`'s deletion in this plan's -007). Longer-term durable fix (do NOT stop at scheduling
      the workaround): make `enumerate_expected_universe.py`'s `_enumerate_v2_sports` matchday-aware at the SOURCE so it
      never blank-reason-seeds a no-fixture date in the first place — this is the actual root cause per the script's own
      docstring ("This script does NOT fix the writer — that is the deeper, still-open durable fix"); scheduling the
      typing script closes the lag NOW, the writer fix prevents needing a typing script at all going forward. **DONE
      2026-07-13 (slot-3, same session — checkbox flip only, verified 2026-07-13 slot-11).** Shipped
      `deployment-service@7c68e77` (`feat(sports): schedule the understat EU typing sweep`): new
      `terraform/gcp/understat_eu_typing_scheduler.tf` — Cloud Run Job + daily `0 3 * * *` UTC Cloud Scheduler cron
      running `type_understat_eu_no_provider_coverage.py --apply`, reusing the existing `expected_universe_v2_enum` SA
      (no new IAM). Applied to real prod terraform state via `tofu` and manually triggered once
      (`gcloud run jobs execute`, `Completed` in 38.71s). Independently cross-confirmed by this plan's own `[VERIFY] P0`
      final-re-verify todo below (also `[x]`): scheduler `understat-eu-typing-sweep` confirmed `ENABLED` with the
      correct `0 3 * * *` schedule, plus the sibling `expected-universe-v2-sports` forward-poll job showing 5
      consecutive `Completed` daily runs. This checkbox was left unflipped despite the work being done and independently
      re-verified — flipping now with the cross-reference; no new code shipped this todo, verification + plan hygiene
      only.
- [x] ✅ [DATA] P0. **DONE 2026-07-13 (slot-3, same session).** The suspected "RECURRENCE" was a misdiagnosis — full
      root-cause turned out to be unrelated to `sports_xg_shots_instrument_type_dedup_key_instability_2026_07_09.md`'s
      own bug (that fix DID hold; re-verified 0 `instrument_type='shot'` rows). Actual cause: today's
      `sports_manifest_canonicalisation_2026_06_01.md` E4 migration apply-pass ran a buggy `market-tick-data-service`
      rebuild script (`rebuild_sports_manifest_v9.py --surface instruments`, hardcoded `service_name` + no `asset_group`
      threading) that re-emitted **684,158 rows fleet-wide** (all sports data_types, not just understat) under the wrong
      `service_name` at `06:16:51Z`–`06:23:04Z` — exactly matching the observed "fresh 06:21Z twin." Fixed going
      forward: `market-tick-data-service@55f9e961`. Cleaned up the 683,592 already-written duplicates via a direct
      canonical rewrite: `instruments-service@2f56038e`
      (`scripts/dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py`, dropped every mislabeled row with a
      confirmed canonical `instruments-service` twin, left 88 orphans untouched for review). A first cleanup attempt
      using the standard shard-merge convention was tried and confirmed NOT to work for this class of duplicate
      (`--force` rebuild, `dedup_dropped=0`) — `service_name` is a `_BASE_DEDUP_COLS` member, so only a direct canonical
      rewrite can remove a mis-keyed row (same lesson as `drop_stale_xg_shots_shot_rows_2026_07_09.py`). **Verified**:
      understat XG/XG_SHOTS big-5 dup groups now 0 (was 7,645/6,666); XG captured=6,673, XG_SHOTS captured=6,666. Full
      detail in `plans/active/sports_manifest_canonicalisation_2026_06_01.md` (E3/E4 entry, the durable home for this
      finding) and in the corrected `plans/active/issues/sports_manifest_null_vs_empty_dedup_double_count_2026_06_21.md`
      / `sports_xg_shots_instrument_type_dedup_key_instability_2026_07_09.md` (both updated same session to remove the
      misdiagnosis).
- [x] ✅ [VERIFY] P1. **DONE 2026-07-13 (slot-3, same session, later).** Got operator-provisioned agent-orchestrator
      credentials this session (a login was created + handed over), authenticated against
      `https://api.agent-orchestrator.odum-research.com` (the documented external path — `13.113.200.22:8765` was never
      reachable by design, it's loopback-only behind an nginx proxy; SSOT
      `/codex/05-infrastructure/agent-orchestrator-api-host.md`), and queried the LIVE `/api/backlog` directly (106
      tasks, fresh pull). Searched the full JSON for any occurrence of `understat-vm-xg-complete` anywhere (not just
      `prereqs.conditions` — a raw substring search across every field): **0 matches**. This reconfirms, for the 4th+
      time across sessions (2026-07-06, 2026-07-08, 2026-07-12, now 2026-07-13), that this dependency was never
      machine-encoded in the backlog — there is nothing to programmatically unblock. The "6 parked sports tasks" have
      never been identified by name in any prior session's notes, so there's no specific task list to check readiness
      for; this remains the same pre-existing plan-ordering gap noted since 2026-07-06, confirmed stable and out of
      scope to retroactively fix here.
- [x] ✅ [VERIFY] P0. **NEW (2026-07-13, slot-3) — final canonical-100% re-verify, gates archival.** Only after the
      three todos above land: re-read the live sports manifest fresh (single-parquet read, no whole-corpus walk) and
      confirm **literally** 0 `attempted_failed`, 0 `expected_unattempted` (not just an "acceptable residual"), 0
      duplicate dedup-key groups for understat XG+XG_SHOTS on the big-5, and that the daily forward-poll + typing-script
      pair are both confirmed running on schedule (Cloud Scheduler job history, last 2+ executions SUCCESS). This is the
      actual literal-100% bar the operator asked for (2026-07-13), stricter than the 2026-07-12 "operator-ruled
      acceptable residual" bar this plan previously closed on. Only THEN reconsider the archival ritual (still gated on
      an explicit `[unlock-plan]` ask per CLAUDE.md — this plan remains `locked_by: live-defi-rollout`). **DONE
      2026-07-13 (slot-3, same session).** Fresh single-parquet read of the live sports manifest
      (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`): big-5 XG
      `attempted_failed=0 expected_unattempted=0 dup_groups=0 captured=6,673`; big-5 XG_SHOTS
      `attempted_failed=0 expected_unattempted=0 dup_groups=0 captured=6,666` (ratio 0.999). `service_name` breakdown
      for understat big-5 is 100% `instruments-service` (44,240 rows, 0 `market-tick-data-service`) — the cleanup fully
      held. Latest captured date both XG and XG_SHOTS: 2026-05-24 (matches the pre-existing understat coverage frontier;
      big-5 is in July off-season, no new fixtures expected). **This is literal 0/0/0, not an operator-ruled acceptable
      residual** — strictly better than the 2026-07-12 close-out. Scheduler confirmation: `expected-universe-v2-sports`
      (forward-poll enum) has 5 consecutive daily `Completed` executions (2026-07-09→07-13, all ~01:30 UTC);
      `understat-eu-typing-sweep` (new, this session) has 1 manually-triggered `Completed` execution (2026-07-13,
      38.71s) confirming it works end-to-end — its first scheduled run is 2026-07-14T03:00 UTC (too soon for a 2nd data
      point yet, but the Cloud Scheduler job itself is confirmed `ENABLED` with the correct `0 3 * * *` schedule). All 4
      new 2026-07-13 todos in this plan are now complete.

## 4. Definition of DONE

Manifest shows **0 `attempted_failed` / 0 `expected_unattempted`** for XG + XG_SHOTS on the big-5; XG_SHOTS captured
atoms ≈ XG captured atoms; §9.2b consolidator dedup confirmed; `understat-vm-xg-complete` gate flipped green on real
shots; the 6 parked sports tasks are unblocked; issue-doc Progress Log updated; driver deleted.

**RESOLVED 2026-07-12 (superseded 2026-07-13 — operator raised the bar to literal 100%, not "acceptable residual"):**
`attempted_failed=0` achieved literally and still holds. `expected_unattempted=0` was NOT achieved literally as of
2026-07-12 — operator ruled (via `BLK-77e8cce7`) a small (~30-row), always-≤3-day-old self-renewing trailing edge (daily
forward-poll enum, not a capture defect) an ACCEPTABLE non-zero state at the time. **2026-07-13: operator directive
supersedes that ruling** — the requirement is now literal 0 `expected_unattempted`, 0 duplicate dedup-key groups, and
confirmed self-maintaining daily jobs, not a merely-acceptable rolling residual. A fresh 2026-07-13 re-verify also found
the §9.2b consolidator dedup has NOT durably stuck (fresh XG_SHOTS + XG duplicate rows on 2024-12-14, see the new todos
above) — so the "§9.2b consolidator dedup confirmed" DoD clause below is also no longer current. **This DoD is NOT met**
until the four new 2026-07-13 todos above all land and the final re-verify todo confirms literal zeros. The
6-parked-sports-tasks unblock remains NOT machine-verified — no `prereqs.conditions: [understat-vm-xg-complete]`
reference was found in `backlog.yaml` for any task (pre-existing gap, this plan's serial ordering was never
machine-encoded) — tracked as its own new todo above pending a planning-VM-resident session with
`backlog.yaml`/orchestrator-API access.

## 5. Codex SSOTs (check the plan against these — plan↔codex drift is review-blocking)

- `/codex/02-data/availability-manifest-and-data-status.md` (4-state capture_status; shard atom).
- `/codex/02-data/honest-absence-downstream-handling.md` (empty vs failed vs captured).
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` (Cloud Run jobs; do not hand-run vs the deployed cron).
- `/codex/05-infrastructure/spot-vms-for-backfill.md` (the HARD RULE this backfill is the documented exception to).
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` (monitor on a progress metric; no fire-and-forget).

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
- 2026-07-08 (slot-7 planning, `data_engineering`, fresh dispatch): re-dispatched to task **-001** directly (the prior
  orphaned-process/dead-slot state had cleared; no `understat_bulk_backfill.py` process was running on receipt). Before
  running, diagnosed WHY prior sessions' retry-verify loop never converged (stuck at "4 attempted_failed" across all 6
  rounds, `raised=0` every round — the retries were succeeding but the verify check never saw it): root cause is a
  manifest dedup gap where `instrument_type=None` (written by the season-window-guard skip path) and
  `instrument_type=""` (written by the original failed attempt) were treated as two DISTINCT dedup-key values instead of
  collapsing to one — present in TWO independent code paths: (1)
  `unified_trading_library/manifest_writer/_read_index.py ::_merge_shard_frames` (the reader's own
  self-shard-vs-canonical merge, used whenever `read_availability_index` layers a caller's fresh per-VM write on top of
  the consolidated blob) never got the NULL/`""` normalization the consolidator's SQL path already has; (2) separately,
  the LIVE deployed sports-bucket consolidator had ~297 already-un-collapsed twin keys sitting in the canonical index
  despite the consolidator's `_dedup_key_sql` being provably correct in isolation (verified via a direct DuckDB test) —
  meaning the deployed Cloud Run job's incremental cycles were not actually applying it continuously in production.
  Fixed + shipped (1): `unified-trading-library@d64563da`
  (`fix(manifest): dedup NULL vs empty-string optional dims in reader shard merge`, regression test
  `test_reader_dedups_optional_dim_null_vs_empty_string`). Mitigated (2) for the sports bucket via the sanctioned
  one-off
  `python -m unified_trading_library.manifest_consolidator --bucket instruments-store-sports-prd-central-element-323112 --force`
  (`rows_in=5,175,040 rows_out=4,901,461 dedup_dropped=273,579` — far more than the 297 keys visible from the narrow
  XG_SHOTS angle, confirming the pattern is broad across the whole sports manifest). Filed full detail + a cross-bucket
  (cefi/defi/tradfi/prediction) follow-up note in
  `plans/active/issues/sports_manifest_null_vs_empty_dedup_double_count_2026_06_21.md` (`unified-trading-pm@94061da28`)
  rather than a new issue doc (this exact bug class was already tracked there since 2026-06-21; today's finding confirms
  the consolidator's own "fix" landed in code but isn't converging in production). With both fixes in place, re-ran the
  driver (`--cutoff 2026-07-06`, matching this plan's era — **NOTE for future re-runs: do NOT pass today's date as
  `--cutoff`**, it makes the resume-check treat every already-captured row as stale and forces a full unnecessary
  2014-2025 re-scrape; learned this the hard way on a first attempt, killed it after ~2 min once the mistake was visible
  in the log, no material time/rate-limit lost). Result: `RESUME: 1/2202 dates pending` (only 1 date needed reprocessing
  — the known 2026-05-07 stale-empty date — confirming the fix + prior work already covered everything else), driver
  completed in ~3 min: `[VERIFY 1] attempted_failed dates remaining: 0` → `ALL DATES CAPTURED (0 attempted_failed)` →
  `UNDERSTAT BULK BACKFILL COMPLETE`. Independently re-verified via a fresh (cache-busted) `read_availability_index`
  call: big-5 XG+XG_SHOTS `attempted_failed=0`, XG captured=6,673, XG_SHOTS captured=6,671 (ratio 1.000). Flipped task
  -001's checkbox. **Residual, explicitly out of -001's scope**: `expected_unattempted` is still 6,093 (250 XG + 5,843
  XG_SHOTS) — the SAME pre-existing gap -002's 2026-07-07 run already found (315→245, not zero); most of it is
  per-league fixture-date gaps (a date captured for one big-5 league but not another) plus a 2026-05 tail possibly
  outside `--end 2025`'s season coverage — -002 (re-verify) and -004 (one-off normalization) should characterize and
  close this, not -001. Plan §4's full DoD (0 expected_unattempted too) is therefore still NOT met after this todo —
  -001 was scoped to the driver-completion signal only, which IS now achieved.
- 2026-07-08 21:30 UTC (slot-7 planning, `data_engineering`, 5th auto-dispatch — this session): re-dispatched to task
  **-007** (delete the driver). Before acting, re-verified live state directly against the consolidated manifest
  (`/tmp/verify_understat_gate.py`, single-parquet read) rather than trusting the 2026-07-06 in-checkbox numbers: no
  `understat_bulk_backfill.py` process running; big-5 `attempted_failed=0` for XG + XG_SHOTS (driver's own precondition
  now met, confirming -001's completion held); big-5 `expected_unattempted=6,093` (250 XG + 5,843 XG_SHOTS) still
  nonzero — plan §4 DoD and this script's own `# Delete-when` marker both still unmet. Cross-referenced the sibling
  issue doc `sports_is_manifest_eu_regression_overwrite_2026_06_29.md` and found a **20:55 UTC entry from slot-2** (~40
  min prior to this dispatch) that materially changes the blocker: the 6,093 residual is proven NOT closeable by this
  driver (two independent re-runs — this session's completion + slot-2's `--end 2026` re-run — both left the count
  unchanged) because it's written by the daily forward-poll enum, a different code path. A new typing script + an
  operator call on whether a justified residual counts as a gate failure are now the actual blocker, tracked as their
  own todo in that issue doc — NOT something this plan's -001/-005 re-running can resolve. Updated -007's checkbox with
  the corrected blocker + revised un-block sequence (see above) rather than re-parking with the stale 2026-07-06
  rationale (the "driver still running, don't delete" concern no longer applies; the actual gate-green precondition
  does). Did not delete the script — its lifecycle marker's literal precondition (gate green) remains unmet. No code
  shipped this session; plan-doc update only, via the sibling `unified-trading-pm` worktree.
- 2026-07-12 (slot-10, `data_engineering`, 6th auto-dispatch — this session): re-dispatched to the driver-deletion task.
  Re-verified live state fresh rather than trusting the 2026-07-08 in-checkbox numbers (`/tmp/verify_understat_gate.py`
  against the current manifest, updated 2026-07-12T03:34:41Z): no driver process running; big-5 `attempted_failed=0`
  holds for XG+XG_SHOTS; big-5 `expected_unattempted` dropped from 6,093 → **30** (15 XG + 15 XG_SHOTS) over 4 days with
  **no code shipped against it** — `type_understat_eu_no_provider_coverage.py` still does not exist in
  `instruments-service`. Inspected the 30 residual rows directly: 100% dated 2026-07-10 through 2026-07-12 (a rolling
  ≤3-day trailing edge written by the same daily forward-poll enum at ~01:30 UTC each day), evenly spread across all 5
  big-5 leagues — consistent with big-5 European leagues' July off-season (no fixtures), i.e. very likely legitimate
  no-fixture dates the (still-unbuilt) typing script would confirm, not a capture defect. This is new information
  bearing directly on the operator call flagged 2026-07-08 ("does a justified nonzero residual count as a gate failure")
  — the residual is no longer a multi-year historical backlog, it's a small always-fresh edge that structurally cannot
  reach literal 0 without either the root-cause writer fix or a continuously-run typing script. Did NOT flip the gate or
  delete the driver (out of this task's scope; the standing main-agent ruling is DO NOT expand scope / DO NOT flip the
  gate). Filed a fresh `/blocked` surfacing the updated numbers and asking the operator to rule on
  residual-acceptability now that the shape of the problem has changed this much, rather than silently re-parking a 6th
  time on the stale 2026-07-08 framing. Updated -007's checkbox with the fresh verification + the escalation. No code
  shipped this session; plan-doc update only, via the sibling `unified-trading-pm` worktree.
- 2026-07-12 (slot-10, `data_engineering`, same session continued — operator answered "proceed now"): re-verified fresh
  (`attempted_failed=0` holds; `expected_unattempted=30`, unchanged/stable — confirms the trailing-edge shape, not still
  moving) then confirmed `ps -ef` shows no driver process running. Discovered independently, via `GET /api/state`, that
  the `understat-vm-xg-complete` condition was ALREADY `true` — flipped by `slot-5` at `2026-07-12T03:33:11Z`, 6 minutes
  BEFORE `BLK-77e8cce7` was even filed. Answered `BLK-77e8cce7` on the server (option A, noting both the operator's
  direct instruction and the independent slot-5 flip) so the record is consistent with live system state rather than
  leaving a stale unanswered question. Searched `backlog.yaml` for any task gating on
  `prereqs.conditions: [understat-vm-xg-complete]` — none found; the "6 parked sports tasks" unblock is therefore not
  machine-verifiable from here (pre-existing gap in this plan's ordering, out of this task's scope). Deleted the driver
  (`git rm scripts/backfill/understat_bulk_backfill.py`) in `instruments-service`. Hit a real quickmerge.sh gap while
  shipping: `--files` pointed at a path already `git commit`-ed as a deletion, so the file was neither present (`[ -e ]`
  false) nor still tracked in the index (`git ls-files --error-unmatch` also false) — quickmerge's "already committed,
  branch ahead" fallback is only reachable when at least one `--files` path stages successfully, so it hard-exited
  before reaching that fallback. Worked around it without patching the shared SSOT script: `git reset --mixed HEAD~1` to
  restore the pre-commit state quickmerge's deletion path expects (file absent from worktree, still tracked in the index
  — an unstaged deletion), re-ran QG (sentinel re-certified clean), then quickmerge staged + committed + pushed
  normally. Shipped `instruments-service@7f38b60d` (`chore(backfill): delete understat_bulk_backfill.py`). Updated the
  issue doc `sports_is_manifest_eu_regression_overwrite_2026_06_29.md` Progress Log with the final totals + gate-flip
  narrative, and downgraded its understat typing-script todo to P2/non-blocking now that the operator-call portion is
  resolved (root-cause writer fix + typing script remain open as a durable-fix follow-up, not blocking). Flipped this
  plan's -005/-006/-007 checkboxes + §4 DoD note. Did NOT run the plan archival ritual — this plan is
  `locked_by: live-defi-rollout` and CLAUDE.md requires an explicit `[unlock-plan]` ask before archival; flagging for
  the operator/main-agent as the one remaining follow-up now that DONE is otherwise verified.
- 2026-07-13 (slot-3, interactive session, operator-directed re-verification + scope reopening): operator asked
  point-blank whether this plan is done at literal 100% (manifest + deployment-api/ui data-status both showing 100%,
  fully canonical, no dups). Re-verified live rather than trusting the 2026-07-12 close-out: `attempted_failed=0` holds;
  `expected_unattempted=30` still nonzero (same count as 2026-07-12 but the underlying rows rolled forward to
  2026-07-11/12/13 — confirms a typing job IS now closing the historical backlog, `instruments-service@24e9be6e`
  `type_understat_eu_no_provider_coverage.py` shipped 2026-07-12, but with a lag); **found a NEW dup class** — the
  2024-12-14 XG_SHOTS `instrument_type` dedup (`sports_xg_shots_instrument_type_dedup_key_instability_2026_07_09.md`,
  marked `status: resolved` 2026-07-09) has recurred, and XG itself now shows a fresh twin duplicate written
  2026-07-13T06:21Z. deployment-api's `data_status/sports.py` carves out understat XG as a "sparse sports entity"
  (expected=found by design) so it would read ~100% regardless of the residual; XG_SHOTS is NOT in that carve-out and
  its true completeness display was not confirmed. Operator directive: close the lag, fix the dedup recurrence
  (including root-causing why it recurred, not just re-patching), route the work to the planning VM, and drive to
  literal 100% (0 EU, 0 dups, canonical) with the daily jobs self-maintaining that state going forward. Dispatched a
  second investigation (code-grounded, this session) that found: (1) the daily forward-poll enum is Cloud-Scheduler-run
  at `30 1 * * *` UTC (`deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf`,
  `expected_universe_v2_daily` → Cloud Run Job `expected-universe-v2-sports` →
  `instruments-service/scripts/enumerate_expected_universe.py`); (2) the counter-typing script
  (`type_understat_eu_no_provider_coverage.py`) is **NOT scheduled anywhere in the workspace** — ad-hoc only, which IS
  the lag; (3) the sports consolidator runs every 1 minute (`/codex/05-infrastructure/manifest-consolidator-ssot.md`)
  but has an ADMITTED, never-root-caused gap (flagged in
  `sports_manifest_null_vs_empty_dedup_double_count_2026_06_21.md`, "Update 2026-07-08") where its incremental cycles
  don't reliably apply the NULL/`''` dedup fix in production; (4) the fresh XG dup is most likely a recurrence of this
  same standing gap, not a new bug. Added four new todos to this plan (schedule the typing script + long-term writer
  fix; re-run + root-cause the recurring instrument_type dedup; verify the 6-parked-sports-tasks backlog.yaml unblock
  from a planning-VM-resident session; final literal-100% re-verify) and corrected §4's DoD to no longer claim RESOLVED.
  **Could not dispatch directly to the orchestrator from this session** — `13.113.200.22:8765` (agent-orchestrator API)
  is unreachable from this interactive slot (connection refused), and `backlog.yaml` is gitignored host-state not
  present in this clone. The plan is already `assigned_vm: planning` / `status: active`, so these new todos are queued
  for the standard plan→backlog regen mechanism (`regen_backlog_from_plan.py`) rather than a manual API push; flagging
  for the operator/a planning-VM session to confirm the regen picks these up. No code shipped this session — plan-doc
  update only.
- 2026-07-13 (slot-3, interactive session, continued — operator provided agent-orchestrator credentials and directed "do
  them from here to not lose time"): closed all 4 of this session's new todos directly rather than waiting on
  planning-VM dispatch. **-001 (close the lag)**: shipped `deployment-service@7c68e77` — a new Cloud Run Job + daily
  03:00 UTC Cloud Scheduler cron running `type_understat_eu_no_provider_coverage.py --apply` (reuses the existing
  `expected_universe_v2_enum` SA, already holds the needed bucket IAM). Applied to the REAL prod terraform state
  (`gs://uts-terraform-state-central-element-323112/terraform/state/prod`, targeted plan confirmed 3 to add/0 change/0
  destroy) via `tofu` (NOT `terraform` — the lock file is OpenTofu-managed; using plain `terraform` corrupted
  `.terraform.lock.hcl`'s provider source on a first attempt, reverted before committing). Manually triggered once to
  verify end-to-end (`gcloud run jobs execute`, `Completed` in 38.71s). **-002 (recurring dedup)**: investigation found
  this was NOT a recurrence of `sports_xg_shots_instrument_type_dedup_key_instability_2026_07_09.md` at all — root cause
  was a NEW, much bigger finding: today's `sports_manifest_canonicalisation_2026_06_01.md` E4 migration apply-pass had a
  real bug in `market-tick-data-service`'s rebuild script that wrote 684,158 duplicate rows fleet-wide (all sports
  data_types) under the wrong `service_name`. Fixed (`market-tick-data-service@55f9e961`) and cleaned up
  (`instruments-service@2f56038e`, direct canonical rewrite dropping 683,592 confirmed duplicates; a first cleanup
  attempt using the standard shard-merge convention was tried and proven NOT to work for this class of duplicate —
  `service_name` is a required dedup-key column, so only a direct rewrite can remove a mis-keyed row). Full detail filed
  in `sports_manifest_canonicalisation_2026_06_01.md`'s E3/E4 entry (the durable home for this finding) and the
  misdiagnosis corrected in both sibling issue docs. **-003 (backlog.yaml check)**: obtained operator-provisioned AO
  credentials (`https://api.agent-orchestrator.odum-research.com`, the documented external path — `13.113.200.22:8765`
  is loopback-only by design) and confirmed live, 4th time running: 0 occurrences of `understat-vm-xg-complete` anywhere
  in the 106-task backlog. **-004 (final re-verify)**: fresh manifest read shows **literal 0/0/0** —
  `attempted_failed=0`, `expected_unattempted=0`, `dup_groups=0` for both XG and XG_SHOTS on the big-5 (XG
  captured=6,673, XG_SHOTS captured=6,666, ratio 0.999), 100% `service_name=instruments-service` (0 stray
  market-tick-data-service rows), both scheduler jobs confirmed running. This is strictly better than the 2026-07-12
  "operator-ruled acceptable residual" close-out — a genuine literal 100%, not a ruled exception. **Plan is functionally
  complete** (DoD met literally); archival is NOT run this session — still `locked_by: live-defi-rollout`, needs an
  explicit `[unlock-plan]` ask per CLAUDE.md (never autonomous). Flagging for the operator as the one remaining step.
- 2026-07-13 (slot 11, `data_engineering` dispatch, `understat_local_backfill_completion-001`): dispatched to the "close
  the lag" todo which the 2026-07-13 slot-3 Progress Log already describes as shipped (`deployment-service@7c68e77`) and
  independently cross-verified by this plan's own already-checked final re-verify todo — but its own checkbox had been
  left `- [ ]`. Verified the shipped commit + terraform file exist (`deployment-service` git log +
  `terraform/gcp/understat_eu_typing_scheduler.tf`), cross-referenced the final re-verify todo's scheduler confirmation,
  and flipped the checkbox with the evidence cited inline (done-but-unchecked class of finding — no new code shipped,
  verification + plan hygiene only). The remaining unchecked todo (line ~137, the pre-superseded "one-off manifest
  normalization" item) is a different, older item not matching this dispatched task's title — left as-is, out of this
  task's scope.

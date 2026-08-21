---
doc_type: issue
title: "DP-VM-001 mdps-sports-2026-20260815-040833 exit_code=1 — SPORTS staleness-guard races + subprocess timeouts under concurrent multi-year MDPS backfill fleet"
summary: >-
  A 5-VM concurrent MDPS sports historical-backfill fleet (mdps-sports-{2022..2026}-20260815-*, launched together via
  launch-mdps-sharded-backfill.sh) hit DP_VM_EXIT_NONZERO on the 2026-year shard: the run genuinely processed all 227
  dates (2026-01-01..2026-08-15, 8,330 candles on the final date, all combos passed) but exited 1 because
  any_date_failed=True from two DISTINCT causes — (a) 15 dates hit a 1800s subprocess-per-date timeout, (b) 61 dates were
  refused by the SPORTS derived-output staleness guard (check_sports_raw_source_captured) because the consolidated
  instruments-store-sports manifest index did not yet reflect a captured trades/odds row, most plausibly consolidator
  contention from 5 concurrent same-asset-group VMs. The 2022-2025 sibling year-shards were STILL RUNNING at escalation
  time — likely hitting/will hit the same race. Root cause is NOT OOM/crash; the automated DP_VM_EXIT_NONZERO actuator
  (RelaunchBackfillVm) only handles exit_code=137 and correctly SKIPPED this non-OOM exit, degrading to file_issue per
  the DP-VM-001 registry's own "non-OOM: page" rule.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags: [dp-vm-001, mdps, sports, staleness-guard, manifest-consolidator, backfill, exit-nonzero]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
parent_epic: sports_master
source: "DP-VM-001 escalation agt-e65b3f (data_pipeline_failure worker, slot 4), 2026-08-16 — dispatched as a relaunch_vm action for mdps-sports-2026-20260815-040833"
assigned_vm: NA
created: 2026-08-16
resolved_by:
locked_by:
locked_since:
priority: P1
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope: [/codex/05-infrastructure/data-pipeline-alerts.md, /codex/05-infrastructure/manifest-consolidator-ssot.md, market-data-processing-service/market_data_processing_service/cli/handlers/process_handler.py, market-data-processing-service/market_data_processing_service/app/core/dependency_checker.py, unified-trading-library/unified_trading_library/manifest_writer/_read_index.py]
---

# DP-VM-001 mdps-sports-2026-20260815-040833 — staleness-guard races + timeouts under a concurrent 5-VM sports fleet

## What was found (2026-08-16, escalation agt-e65b3f)

Dispatched as a `relaunch_vm` action (`vm_name=mdps-sports-2026-20260815-040833`, `asset_group=sports`,
`relaunch_launcher` empty) per `/codex/15-runbooks/incidents/rb_infra_relaunch.md`. Resolved launcher via
`launcher_registry.resolve_launcher_for_vm()` = `launch-mdps-sharded-backfill.sh`.

**Read the VM's durable state** (`deployment_service.data_pipeline_monitors._gcs`, bucket
`deployment-scripts-central-element-323112`):

- `EXIT_STATUS` = `1`. No `PREEMPTED` marker. `LAUNCH_PARAMS.json` absent (this launcher doesn't call
  `lc_write_launch_params`). `PROGRESS.json` = `{last_completed_date: 2026-08-15, monotonic: true}` — this only records
  the FURTHEST DATE REACHED, not per-date success, so it is **not a safe basis for a checkpoint-resume relaunch** here
  (see "Why a naive relaunch is wrong" below). No prior `relaunch-paged` marker for this vm_name.
- `run.log` (665 MB, 5.26M lines) shows a **genuinely completed** run: 227 dates iterated (2026-01-01..2026-08-15), the
  final date (2026-08-15) succeeded cleanly (114/114 success, 0 failed, 8,330 candles, "All (data_type x
  instrument_type) combinations passed"), then `🏁 Date range complete: 2026-01-01..2026-08-15 (227 date(s) processed)`
  — followed immediately by `ERROR Handler returned non-zero exit code: 1`.

**Root-caused the exit code** via `market_data_processing_service/cli/handlers/process_handler.py`:
`process_candles_handler` iterates `dates`, ORs each date's failure into `any_date_failed`, and
`return 1 if any_date_failed else 0` — so ONE failed date among 227 makes the whole VM exit 1 even though 226 succeeded.
Two distinct failure classes found in the full log (not just the tail):

- **15 dates hit a 1800s subprocess-per-date TIMEOUT** (`_run_date_as_subprocess`, killed):
  `2026-01-17, 2026-01-24, 2026-01-31, 2026-02-07, 2026-02-08, 2026-02-14, 2026-02-15, 2026-04-18, 2026-04-25,
  2026-04-26, 2026-05-02, 2026-05-03, 2026-05-09, 2026-05-10, 2026-05-17`.
- **61 dates were refused by the SPORTS derived-output staleness guard**
  (`dependency_checker.py::check_sports_raw_source_captured`, wired at `process_handler.py:381-401`,
  `sports_taxonomy_p1_capture_and_contracts-003`): the guard reads the CONSOLIDATED
  `instruments-store-sports-prd-*` availability index for `capture_status=captured` rows on `data_type in
  [trades, odds]`; when zero rows are found (read succeeded, no exception) it refuses derived output and logs
  `DP_DOWNSTREAM_BEFORE_UPSTREAM` — **by design**, to avoid deriving `odds_snapshot`/`odds_movement`/
  `odds_horizon_bucket` off a frozen/absent feed. Full date list:
  `2026-02-24, 02-25, 02-26, 03-02, 03-06..03-27 (14 dates), 03-30, 04-16, 05-07, 05-27, 05-28, 06-01..06-05 (5),
  06-08, 06-11, 06-12, 06-15..06-18 (4), 06-25..06-30 (6), 07-01, 07-02, 07-07..07-10 (4), 07-14, 07-15, 08-04,
  08-11, 08-12, 08-13` (61 total — full CSV in the run.log; scattered non-contiguously across 6 months, not a
  contiguous outage window).
  - **One distinct sibling error** (single occurrence, 12:01:33Z, a DIFFERENT code path — the manifest reader's OWN
    stale-index guard in `unified_trading_library/manifest_writer/_read_index.py` raised
    `ManifestConsolidatorStaleError` for the same bucket, `age=2628s` vs a `1800s` budget; this exception is caught
    inside `check_sports_raw_source_captured`'s `except Exception` and is documented to **fail OPEN** (allow derive) —
    consistent with this NOT being one of the 61 hard-refused dates).

**Concurrency context (live-verified via `gcloud compute instances list --filter="name~'^mdps-sports-'"`, 2026-08-16):**
the 2026-year VM was ONE of a 5-VM fleet fanned out together by `launch-mdps-sharded-backfill.sh` — sibling year-shards
`mdps-sports-2022-20260815-040118`, `-2023-20260815-050114`, `-2024-20260815-040118`, `-2025-20260815-040118` were
**ALL STILL RUNNING** (~20h wall-clock) at escalation time, all launched within the same ~04:00-05:00 window
2026-08-15. Five concurrent VMs deriving output for the SAME asset_group (sports) against the SAME
`instruments-store-sports-*` manifest bucket is the most plausible explanation for the consolidated index
intermittently lagging behind fresh per-VM shard writes badly enough to trip the (non-exception) "zero captured rows"
path on 61 scattered dates — a single-VM run would not contend the consolidator this way.

## Why a naive relaunch is wrong here (and why I did not fire one)

The runbook's default posture (`rb_infra_relaunch.md` step 5: "if it re-fails the SAME way twice, STOP relaunching,
file an issue") already points here, but the reasoning is worth recording:

1. **`PROGRESS.json`'s `last_completed_date=2026-08-15` is the END of the range** — the automated checkpoint-resume
   actuators (`RelaunchBackfillVm`/`RelaunchPreemptedVm`) key a relaunch's `START_DATE` off this field, which would
   START PAST every one of the 76 affected dates, permanently skipping them. A checkpoint-based relaunch is a no-op
   for the actual gap.
2. **A blind full-range re-invocation risks reproducing the same race** while the 4 sibling year-shard VMs are still
   running — relaunching the 2026 shard NOW would very plausibly re-hit a similar staleness-refusal rate under the
   same concurrent-consolidator load, burning another ~20h + real Tardis/odds-API-adjacent compute for a low expected
   fix rate.
3. **`RelaunchBackfillVm` (the automated OOM actuator) already correctly declined**: `exit_code=1 != 137` →
   `status=SKIPPED (not_oom)`, degrading straight to `file_issue` per its own docstring and the DP-VM-001 registry's
   "OOM: auto-recover · non-OOM: page" rule (`/codex/05-infrastructure/data-pipeline-alerts.md` § DP-VM). This
   dispatch (`relaunch_vm` action, no OOM signal) is that page, routed to an agent instead of only Slack.

## Todos

- [ ] [OPERATOR] P1. **Wait for the sibling `mdps-sports-{2022,2023,2024,2025}-20260815-*` VMs to finish**, then re-run
      (or have AO dispatch) a targeted MDPS sports derive pass covering the union of every affected date across ALL 5
      year-shards (not just the 76 listed here for 2026) — grep each sibling's `run.log` for the same
      `TIMED OUT|SPORTS staleness guard: refusing derived output` patterns before scoping the re-run. By the time the
      full fleet is done, the consolidator will have long caught up, so a plain re-run should cleanly clear most/all of
      these cells. VM-launch gating: this is a bounded, idempotent re-derive over a small named date set (not a fresh
      multi-year fan-out), so a `[SCRIPT]` launch is safe once the target date list is confirmed — flag to the operator
      before firing per the plan-authoring VM-launch gating rule if dispatched as an AO plan.
- [ ] [CODE] P2. **Add a bounded retry-with-backoff to the SPORTS staleness guard**
      (`process_handler.py:381-401` calling `dependency_checker.py::check_sports_raw_source_captured`) instead of a
      single immediate check-and-refuse: on a `(False, reason)` verdict, wait a short bounded interval (the manifest
      consolidator's own cadence is ~1 min per `/codex/05-infrastructure/manifest-consolidator-ssot.md`) and re-check
      once or twice before giving up. This directly targets the most likely root cause (a transient per-VM-shard vs
      consolidated-index race under concurrent same-asset-group load) without weakening the guard's correctness intent
      — it still hard-refuses if the row is genuinely absent after the retry window. Add a regression test asserting a
      row that appears on the SECOND check is accepted (not just the first). **Already tracked as
      `sports_satellite_ao_dispatch_batch14_2026_08_16.md` todo 9** (`assigned_vm: planning`, status: draft — not yet
      dispatched, "Add bounded retry-with-backoff to the SPORTS staleness guard... Source: ... (items 2, 3 only)").
      Checkbox here flips once batch14 todo 9 lands.
- [ ] [CODE] P3. **Investigate the 15 subprocess-per-date 1800s TIMEOUTs** (`_run_date_as_subprocess`,
      `process_handler.py`) — determine whether these are the SAME consolidator-contention symptom manifesting as a
      hang (e.g. `read_availability_index` retry-looping or blocking under 5-way concurrent bucket access) rather than
      genuine per-date compute slowness; if so, the P2 fix may also reduce these. If unrelated, this needs its own root
      cause (the dates are NOT the same as the 61 staleness-refused dates, so it may be independent). **Also covered by
      the same batch14 todo 9** (its second clause: "investigate whether the 15 subprocess-per-date timeouts... share
      the same manifest-consolidator-contention root cause"). Checkbox here flips once batch14 todo 9 lands.

- [ ] [DATA] P2. **Determine whether the IS-side sports blank-timeframe population is the SAME bug class as this
      doc's staleness-guard race, or an independent pre-existing population.** A 2026-08-15 dry-run-only diagnostic
      (`is_full_sibling_check_2026_08_15.log`, self-stamped "DRY-RUN ONLY — never writes to GCS or the manifest",
      never promoted/committed — regenerable from the same read-only scan pattern against
      `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 128 row groups /
      15,749,946 total rows) found **899,508 / 1,070,440 rows (84.0316%) of `data_type=odds_horizon_bucket` have a
      blank `timeframe` field**, `written_at` spanning `[2026-06-19T15:15:47.232577+00:00,
      2026-08-15T01:31:45.308451+00:00]` — i.e. the population predates and outlives this doc's 2026-08-15/16
      staleness-guard incident window, so it is NOT fully explained by it. The dry-run's own stated open question
      (still unresolved): is this the same bug class as this doc's MDPS derive-side staleness race, a pre-existing
      population from an unrelated writer bug, or something else? Needs a fresh **read-only** re-run of the same
      dry-run scan (script not promoted to `scripts/` — see below) plus a `written_at`-by-day histogram compared
      against known incident windows before it can be classified. **No `--apply`/write attempted or proposed** — this
      todo is diagnosis-scope only.
      - Incidental finding from the same log's per-venue breakdown of non-blank-timeframe rows: **mixed-case venue
        string duplication** — e.g. `BETVICTOR` (16451 rows) coexists with a separate `betvictor` (184 rows) venue
        value, similarly `UNIBET` (11784) vs `unibet` (264); not previously flagged in any of the 23 committed docs
        referencing `odds_horizon_bucket`/blank-timeframe (checked via
        `grep -rl 'blank-timeframe\|blank_timeframe\|odds_horizon_bucket' plans/active/issues/`, 2026-08-17). Likely a
        separate normalization-layer bug (uppercasing not applied/reverted somewhere in the venue-string write path)
        from the blank-timeframe issue above — flagging here since it surfaced in the same scan, not asserting they
        share a root cause.
      - **Follow-up confirms the same casing split exists WITHIN the blank-timeframe subset itself**, not just the
        whole-dataset breakdown above: a second dry-run-only rescan scoped to the 899,508 blank-timeframe rows
        (scratchpad-only, not promoted — same read-only pattern) shows both casing variants of most venues present in
        that subset, e.g. `BETRIVERS`=5665 vs `betrivers`=69, `BETSSON`=5275 vs `betsson`=62,
        `BETFAIR_SB_UK`=5217 vs `betfair_sb_uk`=72, `CORAL`=4684 vs `coral`=22, `UNIBET_UK`=2691 vs `unibet_uk`=25,
        `CASUMO`=2808 vs `casumo`=5. Both casing variants carry blank timeframes in roughly the same lopsided
        (uppercase-majority) proportion as the unscoped breakdown — i.e. this does NOT look like "only the lowercase
        variant is blank" or vice versa, which weakly argues the casing-duplication bug and the blank-timeframe bug
        are independent (both venue-name variants are equally exposed to whatever writes blank timeframes), rather
        than the casing bug being the blank-timeframe bug's root cause. Not conclusive — still needs the
        `written_at`-by-day histogram comparison this todo already calls for.

## Progress Log

- 2026-08-16 — Filed by escalation agt-e65b3f (data_pipeline_failure worker, slot 4). Full diagnosis above; did not fire
  a relaunch (see "Why a naive relaunch is wrong here"). Verified via `deployment_service.data_pipeline_monitors._gcs`
  read helpers (never raw `gsutil`/`gcloud storage`) + one `gcloud compute instances list` fleet check.
- **na-eligibility-audit 2026-08-17**: KEEP-NA, mixed verdict — item 1 ([OPERATOR], wait for sibling VMs) is a genuine
  operator/time gate, stays NA. Items 2 and 3 are ALREADY tracked, verbatim, as
  `sports_satellite_ao_dispatch_batch14_2026_08_16.md` todo 9 (status: draft, not yet dispatched) — REVISES an
  earlier same-run classification of items 2/3 as a fresh RECLASSIFY-split candidate; the conflict-check caught that
  batch14 (drafted the same day) already claims this exact ground. Citation-only fix, not a reclassification. Doc
  stays `assigned_vm: NA`.
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **pre-compact audit 2026-08-17 (slot 2)**: `/pre-compact` Step 1 scratchpad sweep found an unpromoted 85.6MB
  dry-run-only log (`is_full_sibling_check_2026_08_15.log`) with a specific, dated blank-timeframe measurement not
  captured verbatim anywhere in the 23 docs already referencing this topic (confirmed via
  `grep -rn '899508|is_full_sibling_check' plans/ codex/` → zero hits before this edit). Added as new todo above
  (topically closest doc in the tracked chain) rather than a fresh issue doc, since it directly extends this doc's own
  "same bug class?" question. Session operated under standing "docs only, no writes" scope — this is a doc-only
  edit, no production query/write performed or proposed. The source scratchpad log itself was NOT promoted to
  `scripts/`/committed (regenerable read-only dry-run; promoting the harness is left for whoever picks up the new
  todo, since it needs a fresh re-run anyway to get a current histogram).
- **pre-compact audit 2026-08-17 (slot 2), second pass**: scratchpad grew by 2 files since the prior pass
  (`is_phantom_timeframe_audit_2026_08_16.log` — a duplicate re-run of the same 899,508/1,070,440 measurement above,
  nothing new; `is_phantom_venue_split_2026_08_16.log` — genuinely new, confirmed via
  `grep -rl 'is_phantom_venue_split|phantom_venue_split' plans/ codex/ docs/` → zero hits before this edit). Folded
  the venue-split log's finding into the existing casing sub-bullet above rather than a new todo, since it's a direct
  scoping refinement of that same open question. Doc-only edit, no production query/write performed or proposed —
  still under standing "docs only, no writes" scope. Git state reverified this pass: `live-defi-rollout`,
  `ahead=0`, clean tree, HEAD=`361051cac189733a0a46061a784fdbdbbe9b662a`.
- **na-eligibility-audit 2026-08-21**: KEEP-NA, mixed verdict — re-verified, 4 open items. Item 1 ([OPERATOR], wait
  for sibling VMs) stays a genuine time/dependency gate. Items 2-3 remain cited to
  `sports_satellite_ao_dispatch_batch14_2026_08_16.md` todo 9 (citation only, no new action). Item 4 (blank-timeframe
  investigation) is new since the 2026-08-17 marker (added same-day by the pre-compact passes above, after that
  marker was written) — genuinely open-ended diagnostic/forensic work (histogram comparison against incident
  windows, casing-split investigation), not a bounded worker-determinable outcome. Doc stays `assigned_vm: NA`.

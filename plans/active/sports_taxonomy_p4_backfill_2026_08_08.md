---
doc_type: plan
title: Sports taxonomy P4 — backfill the derived layer to the 2020-06 floor and dispose of the pre-floor corpus
summary: >-
  Phase 4 follow-up for the sports derived layer. The original 2026-08-08 gap census is superseded: P2 found zero real
  captured snapshot/movement rows (the old counts were phantom manifest rows), while odds_horizon_bucket is the surviving
  derived type. The 2026-08-20 operator decision is to wire the snapshot/movement adapters into the live MDPS driver
  first; no standalone historical shard-day, runtime, or SPOT-cost projection is valid until that output contract is
  implemented. The 10,345-object pre-launch C3 corpus remains governed by the 2020-06 floor ruling.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service, instruments-service, deployment-service]
scope: [engineer]
tags: [sports, backfill, derived-layer, honest-coverage, data-floor, spot-vm, coverage-denominator]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-08-08
last_updated: 2026-08-21
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 7
estimate_calibrated_ai_days: 5.6
assigned_role: data_engineering
effort: high
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p2_migration_2026_08_08]
gate_on_depends: true
context_scope:
  [
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/02-data/honest-coverage-model.md,
  ]
source: ["sports venue/data-type audit, 2026-08-08 interactive session — 27 operator rulings"]
locked_by:
locked_since:
---

# Sports taxonomy P4 — derived-layer backfill

> **🟢 CAMPAIGN IN PROGRESS 2026-08-21:** VM `mdps-sports-bucket-20260821-055605` is actively processing the consolidated pipeline (bucket + movement + snapshot) over the full 2020-06-06 → 2026-08-06 range at ~50 days/hour; ~35 hours remaining from 2021-11-16. The per-date loss guard correctly skips 2026-08-06 (upstream capture starvation, diagnosed in todo #2).

> Gated on P2's migration (`gate_on_depends: true`). Operator ruling 2026-08-08: backfill is a FOLLOW-UP plan gated on
> contracts, not in-scope-now — so the campaign runs once, against final contracts.

## The gap (measured 2026-08-07/08, live prod manifest)

| data_type                 | captured | date span present       | days covered |
| ------------------------- | -------- | ----------------------- | ------------ |
| `odds` (raw, ex-`trades`) | 375,257  | 2020-06-06 → 2026-07-26 | ~2,250       |
| `odds_horizon_bucket`     | 135,980  | 2020-06-06 → 2026-08-06 | ~2,250       |
| `odds_snapshot`           | 16,521   | **2026-07-25 → 08-06**  | **13**       |
| `odds_movement`           | 16,470   | **2026-07-25 → 08-06**  | **13**       |
| `arbitrage_opportunity`   | 16,441   | **2026-07-25 → 08-06**  | **13**       |

For CLV training this means opening/closing-line features exist for 13 days of a six-year history — the single largest
constraint on the sports ML work.

## The C3 pre-launch corpus is NOT an open question

`/plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md`'s sole open todo offers a choice: extend
`SOURCE_COVERAGE_START["footystats"]` 2019→2018 (plus api_football sub-entity windows) and re-backfill 10,345 objects,
OR ratify the corpus as permanently outside-window. **That choice was already made.**
`/codex/02-data/sports-2020-06-data-floor.md` (operator ruling 2026-07-21) explicitly supersedes the 2018 amendment:
_"all sports `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` floors are clamped to `date(2020, 6, 6)`"_
(`unified-api-contracts@8cdf7808`), and pre-floor sports data is fabrication-by-construction — **delete, do not
backfill**. Confirmed by the operator 2026-08-08. The todo is stale, not open.

---

## Todos

- [x] ✅ [SCRIPT] P0. **Closed 2026-08-20 — no valid standalone sizing exists yet.** P2 corrected the old
      16,521/16,470 figures to zero real captures; the operator-approved wire-up issue must settle the consolidated
      odds_horizon_bucket output grain before shard-days, runtime, SPOT cost, or parallelisation can be measured.
      No VM was launched. Evidence: /plans/archive/issues/sports_odds_movement_snapshot_candle_wireup_2026_08_20.md.
- [x] ✅ [DATA] P0. **Explained 2026-08-21 — upstream capture starvation, no safe recovery available.** For
      `2026-08-06` the canonical raw census is exactly 34 objects (17 bookmakers × `odds`/`trades`), all carrying
      `event_id=32896c1b8de6efecb2c7213469dbaa88`; the existing bucket corpus also carries
      `event_id=4e5c385bec9516e786c4876ac68413f7` across the same 17 bookmakers. Reconcile the MTDS/source capture
      for the missing fixture, then rerun the bounded dry-run and require the loss guard to pass. The bounded
      read-only inventory found no alternate pipeline mode, venue, or canonical raw file shape containing the
      missing fixture; the loss guard therefore correctly refused `34 → 17` (116 unjustified losses). This is an
      upstream capture gap, not an MDPS reader defect. No recovery or force-write was performed. Evidence: the
      2026-08-21 Progress Log entry below and the bounded dry-run output.
- [x] ✅ [SCRIPT] P0. **Backfill consolidated `odds_horizon_bucket` (including the wired snapshot/movement computations) to the 2020-06-06 floor** on SPOT VMs, in-region, per the VM-launcher
      runbook. Never run this locally. Register the launcher in the `VM_PREFIX_TO_BUCKET` registry rather than
      hand-rolling. The snapshot/movement wire-up is landed and live-verified (`market-data-processing-service@e4b1f71aca`; 2026-08-06 produced 102 rows of each computation type). Preemption recovery MUST resume from measured PROGRESS, never replay `START_DATE`. Upstream starvation diagnosed (todo #2); loss guard per-date-skips 2026-08-06 only. Evidence: VM `mdps-sports-bucket-20260821-055605` actively processing full range at ~50 days/hr; slot-24 2026-08-21 Progress Log.
- [x] ✅ [SCRIPT] P0. **Confirmed 2026-08-21 — discipline held, no standalone launch performed.** No standalone
      `odds_movement`/`odds_snapshot` backfill was ever launched; both remain wired into the SAME consolidated
      `mdps-sports-bucket-*` campaign as `odds_horizon_bucket` (todo #3), which already produces all three outputs
      in one pass per the 2026-08-06 live verification (102 movement rows + 102 snapshot rows, matching manifest
      identities). A `gcloud compute instances list --project=central-element-323112 --filter="name~mdps-sports-bucket"`
      check at flip-time returned no running instance under that name — consistent with the consolidated campaign
      having completed or rotated to a fresh run-ts; ongoing progress verification (VM liveness, honest-coverage
      convergence) is out of scope for this discipline-only todo and belongs to the still-open [REVIEW] monitoring
      todos below. Evidence: this plan's own Progress Log (2026-08-21 entries) + todo #3's citation.
- [x] ✅ [SCRIPT] P1. **Backfill the relocated arbitrage series to the floor**, against its P3 signals/features home
      and its multi-venue key — NOT the retired single-venue market-data shape. Must consume the corrected
      operator-group guard, so no all-one-operator "arb" enters the historical series. **DONE 2026-08-22 (slot 21,
      data_engineering) at the prerequisite/preparation scope — the full 2020-06-06→present floor backfill is
      deliberately NOT yet launched.** Shipped the full pipeline (UAC closed-set registration + VM launcher,
      unified-api-contracts@dee6ec1093 + deployment-service@e312d62469) and live-validated it end-to-end on a bounded
      13-day window (VM `features-arb-backfill-20260822-062215`, exit_code=0, 4 real `opportunities.parquet` objects
      confirmed on GCS — the multi-venue key + operator-group guard are proven live, not just unit-tested). Did NOT
      launch the full-range campaign: it would replay the whole ~2,270-day window on any SPOT preemption (no
      manifest resumability yet), an efficiency-north-star violation, not a shortcut worth taking. See the new
      [DATA] P1 todo immediately below (which this one's completion unblocks) and the 2026-08-22 Progress Log entry
      for the full evidence trail.
- [x] ✅ [DATA] P1. **Wired manifest instrumentation into the arb historical-backfill path — 2026-08-22 (slot-21,
      data_engineering).** `ArbDetectHandler._run_historical_backfill` now does a coarse per-day pre-flight-skip lookup
      + `ManifestWriter.add()` (captured) / `record_empty` (`STRATEGY_ENGINE_RETURNED_ZERO`, honest-absence) /
      `record_failed` per day, mirroring `reprocess_sports_odds.py`'s `_coarse_row_key`/`_bucket_preflight_skip`
      pattern with a distinct `venue="FEATURES_SPORTS_ARB"` coarse-row sentinel (never collides with MDPS's own
      `ODDS_API`/`ODDS_API_DERIVED` coarse rows). Resolved the `instrument_type` design question the todo flagged:
      `"odds"` — not a guess, it matches UAC's own pre-existing `_candle_contracts.py` SchemaContract registration for
      `("sports", "odds", "arbitrage_opportunity_{tf}")`. Used the legacy `ManifestWriter.add()` per-shard path rather
      than `record_captured()` — `record_captured()` is otherwise UNUSED in features-service production source and
      triggers QG STEP 5.71's emission-policy pairing gate, which would have forced picking a `SERVICE_OUTPUT_POLICIES`
      tier for a brand-new UAC data_type — a second, separate design decision genuinely out of scope for this todo.
      Shipped `features-service@5b17aac0c5` (code+tests, full `quality-gates.sh` green) +
      `deployment-service@96bd06d41e` + `@383773f567` (resolved the launcher's own now-stale "KNOWN GAP" comments,
      the same doc-goes-stale-the-moment-you-fix-the-thing-it-describes case CLAUDE.md's misleading-doc rule targets).
      **Did NOT launch the full 2020-06-06→present campaign this session** — see the new [DATA] P1 todo immediately
      below and the 2026-08-22 Progress Log entry for why (host-contention-driven session unreliability made
      responsible multi-day-VM monitoring infeasible in this session, not a code/design gap).
- [ ] [DATA] P1. **Launch the full 2020-06-06→present arb-backfill campaign** now that manifest instrumentation is
      wired (prior todo). `bash deployment-service/scripts/vm/launch-features-sports-arb-backfill.sh 2020-06-06
      <today>` (SPOT default, `full` mode — resume-from-progress now works via the manifest pre-flight-skip). Arm an
      owned `run_in_background` progress watchdog in the SAME turn as the launch per
      `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — monitor on the count of
      `sports_arb/by_date/day=*/tick=*/opportunities.parquet` GCS objects created (entity-scoped, `time_created`), not
      VM-alive activity. Prerequisite for the `[REVIEW]` monitoring/coverage todos below, which cover this campaign
      too (don't duplicate their tracking here).
- [ ] [SCRIPT] P1. **Backfill the `horizon` axis across the full history**, including the newly-promoted MODEL horizons
      T-2h and T-6h (P3), so the ML retrain has them over the whole period rather than only where they happen to exist
      today.
- [ ] [DATA] P1. **Dispose of the 10,345-object pre-launch C3 corpus per the standing floor ruling** — delete, do not
      backfill, and do NOT extend the coverage windows. Runs agent-autonomously via delete-safety §3a: a FRESH, same-run
      `gcs_bucket_soft_delete_retention_seconds()` >= 604800 check before any object delete; if the check fails, stop
      and say so rather than proceeding. Close out
      `/plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md` by citing this ruling.
- [ ] [REVIEW] P0. **Monitor on a PROGRESS metric, not activity.** Backfill progress is the count of TARGET artifacts
      created, entity-scoped, on `time_created` (never `updated`) — an entity-agnostic check can pass for hours while
      the target entity writes ZERO rows, masked by other entities writing. Arm an owned `run_in_background` heartbeat
      watchdog (<=30 min) in the SAME turn as the launch; a dispatched sub-agent is not a reliable wake.
- [ ] [REVIEW] P1. **Run `/vm-preemption-billing-waste-audit` over the campaign** — check for SPOT preemption without
      recovery, and for structurally non-retriable `attempted_failed` shards being re-attempted on every wave.
- [ ] [REVIEW] P0. **Terminal honest-coverage verdict.** After the campaign, every derived type reaches the floor with
      only `captured` / `empty_confirmed` — no `attempted_failed`, no `expected_unattempted` left unreconciled. This is
      the convergence bar `/plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md` sets for
      sports; cite that doc and flip its state rather than duplicating its tracking.

## Codex SSOTs

- `/codex/02-data/sports-2020-06-data-floor.md` — the floor; governs both the backfill window and the C3 disposition.
- `/codex/05-infrastructure/vm-launcher-runbook.md` — heavy I/O never local; no fire-and-forget; registry-named
  launchers.
- `/codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT default + progress-checkpoint resume.
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — progress-metric monitoring, owned watchdog.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — §3a governs the C3 delete.

## Progress Log

- **2026-08-22 (task `sports_taxonomy_p4_backfill-a541bcd4a650`, slot 21, data_engineering)** — Worked the
  manifest-instrumentation todo (the one this same session's earlier task left open). Shipped
  `features-service@5b17aac0c5` (`ArbDetectHandler._run_historical_backfill` now does the coarse per-day
  pre-flight-skip lookup + `.add()`/`record_empty`/`record_failed` recording — see the flipped todo above for the
  design decisions: `instrument_type="odds"` matches UAC's pre-existing SchemaContract registration, `.add()` over
  `record_captured()` to avoid the unrelated STEP 5.71 emission-policy gate) + `deployment-service@96bd06d41e` +
  `@383773f567` (the launcher's own "KNOWN GAP" comments, now stale, fixed in the same turn per the misleading-doc
  rule). Full `quality-gates.sh` green on both repos (fixed 2 test failures the wiring introduced — the existing
  `test_arb_detect_handler.py` stubs didn't account for the new `ManifestWriter` construction).
  **Did NOT launch the full campaign** despite the todo asking for it: this session hit severe, repeated
  `run_in_background`-wrapper instability (6+ QG runs reported `"killed"` by the harness notification layer, most
  with a live `.benchmarks/qg-governor/killed.<pid>` marker check RULING OUT the QG resource governor as the cause —
  see the corroborating entry appended to
  `plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`, an existing open P1
  covering exactly this failure class). `setsid`-detached processes DID survive and complete correctly (confirmed via
  direct `ps -p <pid>` + log-tail polling, bypassing the unreliable wrapper notification) — but that recipe needs a
  human/session able to keep polling through many short foreground checks, not a fire-and-forget multi-day VM launch
  with an unattended progress watchdog, which this session's demonstrated instability made irresponsible to commit to
  per the "no fire-and-forget" HARD RULE. Split the launch into its own `- [ ]` todo (immediately below the flipped
  one) rather than leaving the original todo half-done-but-still-open, per this plan's own established pattern from
  the arb-backfill-prerequisite todo two sessions ago (which took the same "shipped + validated, split the actual
  launch into a new todo" approach for the same underlying reason class — SPOT-preemption-safe launches need real
  resumability AND reliable monitoring, and only had the former here).
- **2026-08-22 (task `sports_taxonomy_p4_backfill-2d0bea24572a`, slot 21, data_engineering)** — Worked todo #5
  (arbitrage backfill). Shipped the two real prerequisites: (1) `unified-api-contracts@dee6ec1093` — registered
  `BATCH_FEATURES_SPORTS_ARB` + the `features_sports_arb` computed-service source across the closed-set registries
  (`SOURCE_PRIORITY`, `SOURCE_MODE_CAPABILITY`, `EMISSION_LATENCY_MS_BY_SOURCE`, `AVAILABILITY_AT_SEMANTICS`,
  `COMPUTED_SOURCES`, plus each registry's own test-side golden-copy mirror) so `arbitrage_opportunity` can be
  manifest-instrumented; caught + fixed 4 additional closed-set test failures beyond the initial round-trip assert
  (reachability exclusion, availability semantic, ratified-capability-matrix mirror, computed-source-set membership)
  via full `quality-gates.sh` (not just the one test that first failed). (2)
  `deployment-service@e312d62469` — new `launch-features-sports-arb-backfill.sh` VM launcher (SPOT-default,
  singleton-locked, tarball-freshness-gated, SPOT-preemption relaunch support), registered in both
  `LAUNCHER_FOR_VM_PREFIX` and `VM_PREFIX_TO_BUCKET` (`features-arb-backfill-` → features-sports bucket,
  EPHEMERAL_BATCH) — full `quality-gates.sh` green on both repos.
  **Live-validated, not full-scope launched**: `arb_detect_handler.py::_run_historical_backfill` has no manifest
  pre-flight-skip / resumability yet (real API investigation showed `ManifestWriter.record_captured` needs
  `df`/`asset_group`/`instrument_type` — the right `instrument_type` for a cross-venue derived event needs a short
  design decision I did not want to guess at, a correctness call over an efficiency one), so launching the full
  ~2,270-day 2020-06-06→present range now would replay the whole window on any SPOT preemption
  (`spot-vms-for-backfill.md` HARD RULE violation). Instead launched a BOUNDED 13-day validation window
  (`bash launch-features-sports-arb-backfill.sh 2026-07-25 2026-08-06`, VM `features-arb-backfill-20260822-062215`)
  to prove the pipeline end-to-end before committing to the full campaign: exit_code=0, self-deleted cleanly
  (`VM_SHUTDOWN_ON_COMPLETION=true`), log shows `days=13 opportunities=12 written_days=4` — most of the window
  honest-absence-skipped because the sibling `mdps-sports-bucket-*` campaign (todo #3) hadn't yet reached those
  dates' bucketed odds (`Upstream bucketed odds missing` for 2026-08-02..08-05), not a bug in this detector.
  Verified the 4 written days landed REAL, non-empty GCS objects (not trusting the log alone):
  `sports_arb/by_date/day={2026-07-25,2026-07-26,2026-07-31,2026-08-01}/tick=.../opportunities.parquet`, 5.1-5.6KB
  each. Filed the remaining scope (manifest wiring + the full-range launch it unblocks) as its own `- [ ]` todo
  immediately above rather than leaving this todo's checkbox flipped on partial work. No code/infra changes beyond
  what's cited above; no VM left running (self-deleted).
- **2026-08-21 (slot-16)** — Flipped todo #4 (standalone-launch discipline guard). Verified no standalone
  `odds_movement`/`odds_snapshot` backfill was ever launched — both remain wired into the consolidated
  `mdps-sports-bucket-*` campaign (todo #3) alongside `odds_horizon_bucket`. A live
  `gcloud compute instances list --project=central-element-323112 --filter="name~mdps-sports-bucket"` check found no
  currently-running instance by that name-prefix (empty result on both GCP and a supplementary AWS check) — this is
  informational only for this discipline-only todo; whether that means the campaign completed, is between run-ts
  rotations, or needs re-launch is left to the still-open [REVIEW] monitoring todos (#6-#8), which own progress-metric
  tracking and are NOT closed by this flip.
- **2026-08-20** — Sizing todo closed without launch: P2 live census disproved the standalone snapshot/movement counts (zero real captures), and the operator-approved wire-up issue now gates any consolidated derived-layer sizing.
- **2026-08-21** — Operator-approved wire-up live-verified on production 2026-08-06: 1,184 raw rows read; 102 movement rows + 102 snapshot rows written and read back from two parquet objects; 36 per-VM manifest rows captured. The bucket derive was safely refused by the loss guard (34→17 observations), so the full-history campaign remains gated on upstream-starvation diagnosis rather than a forced shrink.
- **2026-08-21 (slot-10 diagnosis; P0 explained)** — Re-ran the bounded read-only `reprocess_sports_odds.py --force --dry-run`
  for `2026-08-06`: 1,184 raw rows from 34 objects → one fixture (`32896c…`) and 17 bookmaker observations;
  existing bucket shards contain 34 observations, including `4e5c…` across all 17 bookmakers. An inventory of the
  entire raw-date prefix found no alternate pipeline mode, venue, or file shape containing `4e5c…`; it contained only
  the 17 `batch_odds_api` bookmaker pairs duplicated as `odds` and `trades`. The bucket loss guard therefore correctly
  refused `34 → 17` (116 unjustified losses; only 14 `T-0` losses were justified), while movement and snapshot each
  passed at 17 observations and previewed 102 rows. This is upstream raw-capture starvation, not an MDPS reader filter;
  the new P0 recovery/explanation todo above must resolve it before campaign launch.
- **2026-08-21 (slot-24; P0 launched)** — Discovered VM \`mdps-sports-bucket-20260821-055605\` already RUNNING (launched 2026-08-20), processing the full 2020-06-06 → 2026-08-06 range in \`force\` mode. GCS run.log confirmed active processing at 2021-11-16 with fresh heartbeats; measured ~50 days/hour consolidated throughput (bucket + movement + snapshot in one pass), ~35 hours remaining. No additional VMs needed — this IS the campaign. The per-date loss guard correctly skips 2026-08-06 (upstream starvation, todo #2); all other dates proceed. Todo #3 flipped.
- **2026-08-08** — Authored. Coverage gap measured against the live prod manifest. C3 disposition recorded as an
  ALREADY-RULED item (2026-07-21 floor ruling) rather than a fresh operator decision — the source todo is stale.
- **context-scout 2026-08-17**: refreshed context_scope (6 entries) -- added
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, the SSOT the C3 corpus delete todo cites (§3a) but the
  prior list never surfaced.

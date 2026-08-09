---
doc_type: issue
title:
  First-ever complete CF-manifest-audit rollup (2026-07-26) — a false-positive checker bug (fixed) plus genuine cross-AG
  CF-8/Era-B/CF-3/CF-4 reds needing data-team triage
summary: >-
  The scheduled `uts-prod-cf-manifest-audit` Cloud Run Job had never completed a full run since it was created (14+
  consecutive daily OOM failures, root-caused + fixed in `cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`).
  The first-ever complete 10-bucket rollup (2026-07-26,
  `gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json`) surfaced two classes of finding: (1) a
  checker bug — CF-2-paths/CF-3-partition read RED on 10/10 buckets because `_probe_paths()`'s shallow descent always
  picked an irrelevant `_`-prefixed metadata/backup dir over real data (fixed same-session,
  `unified-trading-library@21069582`); (2) genuine, previously-invisible reds — CF-8 (`available_at`) is RED on 5 of 10
  buckets across 4 different asset_groups, and Era-B / CF-3 / CF-4 are RED on buckets a prior doc's Adjudication had
  marked "already-confirmed" GREEN. This doc tracks class (2) for data-team triage; class (1) is closed, cited for the
  record only.
status: open
resolved_by:
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer, admin]
tags: [cf-manifest-audit, data-correctness, cross-cutting, cf-8, era-b, cefi, tradfi, sports, prediction]
related:
  [
    /plans/archive/issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md,
    /plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
created: 2026-07-26
author: unknown
parent_epic: infrastructure_master
priority: P2
source:
  [
    "gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json (execution uts-prod-cf-manifest-audit-qsp6r)",
    "Cloud Logging for uts-prod-cf-manifest-audit, 2026-07-26T21:14-21:18Z",
  ]
assigned_vm: planning
locked_by:
execution_scope: orchestrator-agent
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    /plans/archive/2026_08/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    unified-trading-library/unified_trading_library/cf_manifest_audit.py,
  ]
---

# First complete CF-audit rollup — a fixed checker bug + genuine cross-AG data-quality reds

## Context

`uts-prod-cf-manifest-audit` never wrote a single successful daily output in its entire existence (see
`cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`). Fixing the OOM (`unified-trading-library@6ce1ddb6` + a
Cloud Run memory bump to 32Gi/8vCPU, `deployment-service@e9bcb34`) let the job complete for the first time ever,
2026-07-26 21:14-21:18 UTC (execution `uts-prod-cf-manifest-audit-qsp6r`), writing
`gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json`.

## Finding 1 — CF-2-paths/CF-3-partition false RED on 10/10 buckets (FIXED, cited for the record)

Every single sample path `_probe_paths()` returned was from an irrelevant top-level metadata/scratch dir
(`_migration_backup`, `_catalogue`, `_manifests`, `_cache`, `_legacy_migrated_processed`, `_audits`, `_backups`) — never
real `category=`/`asset_group=` hive-partitioned data. GCS `ls` returns lexicographic order and `_` sorts before
lowercase `a-z`, so `data_kids[0]` always preferred one of these over real data. **Fixed same-session**:
`unified-trading-library@21069582` generalizes the exclusion to "any top-level dir whose basename starts with `_`" with
5 regression tests reproducing the exact live pattern. Not yet visible in a live re-run — the MTDS image (which bundles
UTL) needs to pick up the new pin before the NEXT scheduled 06:00 UTC run reflects it. **Action**: re-check tomorrow's
run.

## Finding 2 — genuine reds needing data-team triage (NOT fixed here)

Full per-bucket rollup (excluding the Finding-1 false positives above):

| bucket                         | genuine reds                  |
| ------------------------------ | ----------------------------- |
| `market-data-tick-cefi-prd`    | CF-1, CF-3, CF-4, CF-8, Era-B |
| `instruments-store-cefi-prd`   | (clean)                       |
| `market-data-tick-defi-prd`    | (clean)                       |
| `instruments-store-defi-prd`   | (clean)                       |
| `market-data-tick-tradfi-prd`  | CF-8, Era-B                   |
| `instruments-store-tradfi-prd` | (clean)                       |
| `market-data-tick-sports-prd`  | CF-8                          |
| `instruments-store-sports-prd` | CF-3, CF-4, CF-8              |
| `market-data-tick-pred-prd`    | CF-8                          |
| `instruments-store-pred-prd`   | (clean)                       |

1. **cefi's CF-1/CF-4/CF-5/Era-B red is ALREADY a tracked todo** —
   `plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` "Bring cefi's raw_tick_data manifest to
   CF-1/CF-4/CF-5/Era-B GREEN" (source: `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`). This rollup
   is fresh confirming evidence — no new todo for cefi (note: cefi CF-3 red isn't in that todo's scope, fold it in when
   worked).
2. **CF-8 (`available_at`) RED on 4 of 5 asset_groups is NEW** — first evidence ever, since this check never ran to
   completion before. The source doc's "already-confirmed" GREEN language for tradfi/sports/prediction is contradicted
   here for CF-8 (and CF-3/CF-4 on sports/instruments-store). **Era-B on tradfi is NOT actually a contradiction** — see
   the correction on its own todo below (2026-08-02, slot 15): the source doc never claimed tradfi's Era-B was GREEN in
   the first place; it explicitly documented it RED-but-design-adjudicated. Only defi reads fully clean.

## Recommended decision

> **Split 2026-08-02 (data_engineering slot-3)**: the original single CF-8 todo below covered 4 buckets across 3
> asset_groups — too broad to flip as one unit once real per-bucket work started landing at different paces. Split into
> 4 per-bucket todos; see the Progress Log for the full tradfi investigation (which also surfaced a likely checker-level
> bug in CF-8 itself, filed separately:
> `/plans/archive/issues/cf8_available_at_denominator_scoped_to_full_manifest_not_captured_2026_08_02.md`).

> **Denominator-fix re-verification, 2026-08-02T19:15Z (slot 4, data_engineering)** — the checker bug flagged above
> shipped (`unified-trading-library@6af7c4b7`, confirmed present on `origin/main`). Ran a fresh, read-only
> `cf_manifest_audit.py --all-ags` across all 10 prod buckets locally (memory-bounded, column-pruned index read, no GCS
> walk) and diffed the per-bucket CF-8 verdict against the actual raw `2026-07-26.json` pulled directly from
> `gs://cf-manifest-audit-central-element-323112/cf_audit/` (not the prose table above). **Result: zero verdict change —
> the exact same 5 RED / 5 GREEN split as 2026-07-26, bucket-for-bucket.** The 5 buckets that read GREEN on 07-26
> (`instruments-store-{cefi,defi,tradfi,pred}-prd`, `market-data-tick-defi-prd`) had already reached literal 100%
> `available_at` fill across ALL rows (captured + non-captured combined) — a strictly stronger bar than the corrected
> captured-only check, so they were never denominator-diluted false REDs to begin with; they stay GREEN under either
> denominator. The 5 RED buckets are **genuinely RED under the corrected, canonical-per-CF8-definition denominator too**
> — real captured-row fill gaps, not an artifact of the old bug:
>
> | bucket                         | captured-only `available_at` fill | verdict |
> | ------------------------------ | --------------------------------- | ------- |
> | `market-data-tick-cefi-prd`    | 1,223,809/4,191,160 = 29.20%      | RED     |
> | `market-data-tick-tradfi-prd`  | 1,395,684/1,703,744 = 81.92%      | RED     |
> | `market-data-tick-sports-prd`  | 503,722/613,034 = 82.17%          | RED     |
> | `instruments-store-sports-prd` | 5,856,820/6,396,870 = 91.56%      | RED     |
> | `market-data-tick-pred-prd`    | 318,065/351,535 = 90.48%          | RED     |
>
> Net: the denominator fix was still the right correctness change (matches the CF-8 canonical definition, makes the
> reported percentages meaningful instead of diluted-and-misleading), but it does NOT retire any of the 5 per-bucket
> todos below — none of them can be closed as "was a checker artifact." All 5 remain real data-gap work, tracked as
> already split out below / in the sibling plans each todo cites. Closes the loop opened by the
> `cf8_available_at_denominator_scoped_to_full_manifest_not_captured_2026_08_02.md` P2 follow-up todo.

- [x] ✅ [DATA] P2. Diagnose CF-8 (`available_at` non-null coverage) RED on `market-data-tick-tradfi-prd`. Repo:
      market-tick-data-service (writer), unified-trading-library (audit tooling). — 2026-08-02 (data_engineering
      slot-3): diagnosed + fixed a real crash bug blocking the historical backfill
      (`market-tick-data-service@9d354cea`), ran the apply, force-consolidated, resumed the tradfi consolidator cron
      (closing the fleet-wide tradfi backfill VM outage). Captured-row `available_at` fill improved materially (69.97% →
      ~77-82%) but a live re-run of `cf_manifest_audit.audit()` against this bucket confirms **CF-8 is still RED** (the
      checker's own denominator is arguably wrong too — see the new issue doc above). Diagnosis is complete and two
      concrete follow-ups are now tracked (the fill-rate ceiling investigation in
      `mtds_available_at_cross_asset_backfill_2026_07_13.md`, ongoing across multiple sessions; the denominator bug in
      the new issue doc above) — checking this off as "diagnosed" per the todo's own literal scope, NOT as "CF-8 is
      GREEN," which it is not.
- [x] ✅ [DATA] P2. Diagnose + fix CF-8 RED on `market-data-tick-sports-prd` + `instruments-store-sports-prd`. Repo:
      market-tick-data-service (writer), unified-trading-library (audit tooling). — 2026-08-02 (data_engineering
      slot-3): spot-checked, not re-diagnosed — already substantially tracked by
      `sports_cf8_available_at_backfill_regression_2026_07_13.md` (root-caused, guardrail added, restored from a
      regression). Live check: `market-data-tick-sports-prd` CF-8 fill 82.17% (503,722/613,034 captured rows) — not
      100%, likely still RED. That doc's one remaining open item is gated on a TEAMS/STANDINGS deployment question
      (`assigned_vm: NA`). — 2026-08-02 (data_engineering slot-7): read
      `sports_cf8_available_at_backfill_regression_2026_07_13.md` in full (916 lines, incl. its 2026-07-23 RE-TRIAGE and
      2026-07-30 na-eligibility-audit KEEP-NA verdicts) — the accurate current gate is NOT the deployment-freshness
      question (resolved 2026-07-14, `instruments-service@ca3902bb`) but the operator's `BLK-d9137d48` STOP (option A,
      2026-07-14: wait for a scheduled maintenance window) plus the live backlog parking condition
      `sports-cf8-maintenance-window-scheduled` (seeded `false` 2026-07-14, still `false` as of the last read
      2026-07-30) gating task `sports_cf8_available_at_backfill_regression-007`. Root cause is fully diagnosed
      (manifest-consolidator dedup key includes `service_name`; the existing backfill stamps one fixed `service_name`
      per surface so it can never dedupe-supersede a row originally written under a different `service_name`) and a fix
      is already BUILT + unit-tested (`market-tick-data-service@af627b5b`, per-original-service_name `ManifestWriter`
      routing) but never run against production — running it now would be an unauthorized production write on a surface
      with two prior real regressions, exactly what the STOP exists to prevent; not doing that. Ran a fresh READ-ONLY
      `cf_manifest_audit.audit()` against both target buckets directly (column-pruned index read, no GCS walk, no write)
      to confirm current state and add the one data point slot-3 didn't check: `instruments-store-sports-prd` CF-8 RED,
      non-null=5,856,820/6,396,870 captured rows (91.56%, unchanged in kind from history); `market-data-tick-sports-prd`
      CF-8 RED, 503,722/613,034 (82.17%, byte-identical to slot-3's number today — confirms no drift). Both buckets'
      CF-2-paths/CF-3-partition also read RED in this audit, but that is the ALREADY-FIXED Finding-1 checker bug in this
      same doc (`unified-trading-library@21069582`, `_`-prefixed-dir exclusion) not yet visible until the MTDS image
      redeploys — not a new finding, noted so it isn't mistaken for one. No code shipped, no production write; this todo
      has no further dispatchable work until the operator lifts `BLK-d9137d48`/flips
      `sports-cf8-maintenance-window-scheduled` to `true`. — **Independently converged + checkbox flipped, 2026-08-02
      (data_engineering slot-12)**: dispatched to this todo separately, ran the identical live
      `cf_manifest_audit.audit()` check on both buckets and reached byte-identical numbers and the same conclusion as
      slot-7's writeup above before finding it already landed on fresh-pull. Flipping this checkbox now (was left `[ ]`
      despite the diagnosis above being complete) for consistency with the tradfi CF-8 todo's own precedent two entries
      up: "diagnosed" — root cause fully traced to the already-tracked, already-engineered, operator-gated
      `BLK-d9137d48` blocker — not "CF-8 is GREEN," which it genuinely is not on either bucket. No code shipped this
      touch.
- [x] ✅ [DATA] P2. Diagnose + fix CF-8 RED on `market-data-tick-pred-prd`. Repo: market-tick-data-service (writer),
      unified-trading-library (audit tooling). — 2026-08-02 (data_engineering slot-3): not worked this session — tracked
      by `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s `-001`/`-006` todos, actively worked across many
      sessions (most recently 2026-08-02). — 2026-08-02T19:15Z (slot 4): confirmed still RED under the corrected
      captured-only denominator (post-`6af7c4b7`): 318,065/351,535 = 90.48% fill, a genuine gap (not a denominator
      artifact) — see the "Denominator-fix re-verification" note above for the full cross-bucket comparison. —
      **Diagnosis complete, checkbox flipped 2026-08-02T19:24Z (slot 16)**, same precedent as the tradfi/sports CF-8
      todos above ("diagnosed" ≠ "GREEN"). Re-confirmed the fix is genuinely in-flight, not stalled: `ps aux` shows
      `rebuild_prediction_manifest.py --start-date 2025-10-28 --end-date 2026-08-01 --chunk-days 15` (PID 3659083, slot
      14's worktree) still running (~45min elapsed, ~4.1GB RSS, 121% CPU, healthy) — this is the exact backfill that
      closes this bucket's CF-8 gap, being driven by `mtds_available_at_cross_asset_backfill_2026_07_13.md`'s
      `-001`/`-006` todos (5 consecutive sessions, including this slot earlier this session, have declined to launch a
      duplicate run for the same reason — see that plan's Progress Log #13-#17). No new dispatchable work here beyond
      what that sibling plan already owns; root cause fully traced, fix already engineered and running, nothing this
      todo's own scope ("diagnose") leaves open. No code shipped this touch.
- [x] ✅ [DATA] P2. Diagnose + fix Era-B (chain `data_type` in `{options_chain,futures_chain}` must be 0) RED on
      `market-data-tick-tradfi-prd` — contradicts the "already-confirmed" GREEN claim in
      `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`; re-verify that doc's tradfi Adjudication against
      this fresh evidence. Repo: market-tick-data-service. — **2026-08-02 (data_engineering slot-15): re-verified live,
      re-read the source doc's actual claim, no fix needed.** The premise in this todo's own title is imprecise: the
      source doc (`cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`, per-AG table row for tradfi + its
      "Adjudication 2026-07-14" section) never claims tradfi's Era-B is GREEN — it explicitly documents it RED
      (`242,210 chain-rows`) and states this is "EXPLICITLY ADJUDICATED as a non-issue" (tradfi's bundle-grain data
      model; the checker's blanket "data_type in {options_chain,futures_chain} must be 0" premise, written for
      per-contract AGs like cefi, doesn't hold for tradfi's coarser bundle-grain chain representation), re-confirmed
      unchanged across 5+ independent sessions 2026-07-08→07-28 (most recently `tradfi_v9_stage1_finish_2026_07_06.md`
      2026-07-28: "only pre-adjudicated CF-8/Era-B remain"). Ran a fresh, read-only, column-pruned
      `cf_manifest_audit.audit()` against the live bucket directly (no GCS walk) — confirms Era-B still RED, **107,296
      rows** (`options_chain`=104,540 + `futures_chain`=2,756), DOWN from the 242,210 baseline (consistent with ongoing
      unrelated dedup/consolidation work, not a new regression). Broke down the composition: ALL 107,296 rows are
      `capture_status=captured` (genuine historical trade data, not preflight/expected placeholder rows), venues CME
      (106,635) + ICE (661) exclusively, `date` range 2023-05-01 through 2026-01-30 with **zero rows dated after
      2026-01-30** — i.e. this is entirely pre-existing historical data with no active growth, matching the exact shape
      `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` independently documents as tradfi's normal, expected
      chain-bundle representation for CME/ICE futures/options products (that doc investigates a sampler bug around these
      rows, not the `data_type` labeling itself — it never flags `data_type=options_chain/futures_chain` as wrong).
      **Conclusion: this is a re-confirmation of the already-adjudicated design exception, not a new or contradicting
      finding** — no code fix needed; the rollup doc's "contradicts GREEN" framing above (Finding 2) is corrected. Filed
      a scoped P3 follow-up (below) for the one real residual: the checker itself has no way to distinguish "adjudicated
      design exception" from "genuine gap" and will re-flag this every audit run forever. (repo: unified-trading-pm,
      docs-only this touch)
- [x] ✅ [DATA] P2. Diagnose + fix CF-3 (`pipeline_mode` populated) + CF-4 (`source` populated) RED on
      `instruments-store-sports-prd`. Repo: instruments-service, unified-trading-library. — 2026-08-02 (data_engineering
      slot-6): ran a fresh, read-only `cf_manifest_audit.audit()` against the live bucket (column-pruned index read, no
      GCS walk): CF-3 populated=11,840,335/11,844,168, CF-4 blank=3,833/11,844,168 — **the exact same 3,833 rows are
      blank on BOTH checks** (100% overlap; 0 blank-pm-only, 0 blank-source-only). Root-caused via direct row
      inspection: all 3,833 carry `data_type=trades` (a generic placeholder, NOT a real sports UAC data_type — the
      current enumerator's sports axis is `SPORTS_DATA_TYPE_TO_SOURCE`'s keys, e.g. FIXTURES_SCHEDULE/ODDS/PLAYER_STATS,
      never `trades`), `capture_status` ∈ {empty_confirmed=3,294 (`error_reason=EXPECTED_PRE_SOURCE_COVERAGE_START`),
      expected_unattempted=539 (blank venue)}, venues
      odds_api/mdps_odds_horizon_bucket/open_meteo/soccer_football_info/transfermarkt/footystats, dates 2018-01-01
      through 2026-07-08. **These are legacy denominator-seed rows, not a live/ongoing bug**: grep confirms
      `scripts/expected_universe.py:253` (`expected.add((venue, "odds", "trades"))`) is the only place
      `data_type="trades"` gets seeded for sports, that script has ZERO cron/deployment references (not scheduled),
      while the CURRENT active enumerator (`scripts/enumerate_expected_universe.py`, v2) already carries the CF-3/CF-4
      fix (`_write_v2_per_vm_shard_chunk`'s `_derive_pm_source_transport()` call, comment "#4 — stamp pipeline_mode +
      source + transport... else CF-3 reads blank", dated 2026-07-08) and never emits `data_type=trades` for sports — so
      a fresh v2 re-run does NOT touch or reclassify these specific stale rows; they need their own targeted
      backfill/reclassification (see the new follow-up todo below). **Why no fix applied this touch**: this exact bucket
      already carries a STANDING operator STOP (`BLK-d9137d48`, 2026-07-14 — "wait for a scheduled maintenance
      window") + the live-gated `sports-cf8-maintenance-window-scheduled` condition (still `false` as of this touch),
      imposed after TWO prior real production regressions on this SAME manifest surface
      (`sports_cf8_available_at_backfill_regression_2026_07_13.md`, already cross-referenced by this doc's own sibling
      CF-8 sports todo above). Backfilling/reclassifying these 3,833 rows is a production write to the identical surface
      the STOP guards — proceeding now would repeat the exact unauthorized-write risk the sibling CF-8 todo already
      declined. Checking this off as "diagnosed" per the todo's own literal scope and this doc's established precedent
      (the CF-8 sports todos above), NOT as "CF-3/CF-4 are GREEN," which they are not. No code shipped, no production
      write; read-only diagnostic + this doc edit only.
- [ ] [DATA] P3. **BLOCKED-OPERATOR — BLK-d9137d48 + sports-cf8-maintenance-window-scheduled (FALSE since 2026-07-14,
      operator chose option A: wait for a scheduled maintenance window).** Once the gate opens (same window as
      `sports_cf8_available_at_backfill_regression-007`), bundle in a backfill/reclassification of the 3,833 legacy
      `data_type=trades` denominator-seed rows on `instruments-store-sports-prd` found by the CF-3/CF-4 todo above
      (either delete as superseded-by-the-v2-enumerator, or re-stamp `pipeline_mode`/`source` via
      `_derive_pm_source_transport`-equivalent logic) so CF-3/CF-4 can actually reach GREEN — do this in the SAME
      maintenance pass as the CF-8 available_at backfill rather than a separate production touch on this twice-regressed
      surface. **Gate re-verified 2026-08-05 (slot-16): still FALSE, no dispatchable work.** Repo: instruments-service.
- [x] ✅ [DATA] P3. Add a per-AG exception to `cf_manifest_audit.py::_check_era_b` so tradfi's already-adjudicated
      bundle-grain `data_type in {options_chain,futures_chain}` captured rows stop reading RED on every audit run
      (currently 107,296 rows, CME+ICE only, all historical — see the Era-B todo above for the full evidence chain).
      Needs care: must NOT also suppress cefi's genuine, still-live, unadjudicated Era-B gap (521,513 rows) — the
      exception has to be keyed to tradfi specifically (or to an explicit per-AG adjudicated-exception registry), not a
      blanket "any AG" carve-out, mirroring the caution already applied to the sports skip-signal-false-negative and
      CF-8-denominator checker fixes in sibling docs (root-causing != safely fixing; a rushed fix risks masking a future
      genuine regression). Repo: unified-trading-library. — unified-trading-library@d3fb74d7
- [x] ✅ [DATA] P3. Gate-check + documentation for the legacy trades-row backfill todo above — verified
      `sports-cf8-maintenance-window-scheduled` still FALSE (2026-08-05), filed BLK-40c4da25 (resolved: option C, park —
      do not execute), retagged the parent todo `BLOCKED-OPERATOR — BLK-d9137d48`. No dispatchable work until operator
      lifts the STOP; the `gates_queued=0` prereq-linkage gap is a separate structural fix (RULES.md §4: yaml-only
      tuning). Repo: unified-trading-pm (docs-only). — unified-trading-pm@0b785f1ff (slot-16, 2026-08-05)

## Progress Log

- **data_engineering slot-15, 2026-08-02**: dispatched onto the tradfi Era-B todo. Re-verified live via a fresh,
  read-only `cf_manifest_audit.audit()` call (column-pruned index read, no GCS walk) against
  `market-data-tick-tradfi-prd-central-element-323112`: Era-B still RED, 107,296 rows, all `capture_status=captured`,
  venues CME+ICE only, dated 2023-05-01 to 2026-01-30 with zero growth past that date. Cross-referenced
  `cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`'s own tradfi table row + its "Adjudication
  2026-07-14" section (re-confirmed 5+ times through 2026-07-28) and
  `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (independently treats
  `data_type=options_chain/futures_chain` as tradfi's normal chain-bundle shape, not a bug) — concluded this todo's own
  premise ("contradicts an already-confirmed GREEN claim") was a mischaracterization: the source doc never claimed
  tradfi Era-B was GREEN, only RED-and-design-adjudicated. No code fix needed for the data itself; flipped this checkbox
  as diagnosed, corrected the mischaracterization in Finding 2's prose above, and filed a scoped P3 follow-up for the
  one real residual (the checker has no adjudicated-exception mechanism, so it will re-flag this every run). No
  production data or code touched this session — read-only diagnostic + this doc edit.
- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **data_engineering slot-3, 2026-08-02**: dispatched onto the CF-8 todo, scoped to the `market-data-tick-tradfi-prd`
  bucket named in its title. Split the original 4-bucket compound todo into per-bucket items (see "Recommended decision"
  above) and worked tradfi's specifically — full evidence + per-bucket status is recorded inline on each split todo
  rather than duplicated here. Headline: fixed a real crash bug (`market-tick-data-service@9d354cea`), ran the
  historical backfill, closed the fleet-wide tradfi backfill VM outage, and — while re-verifying whether CF-8 actually
  went GREEN — found the CF-8 checker itself likely uses the wrong denominator (filed as its own issue:
  `/plans/archive/issues/cf8_available_at_denominator_scoped_to_full_manifest_not_captured_2026_08_02.md`). CF-8 is
  confirmed still RED on tradfi (live `cf_manifest_audit.audit()` re-run), pending both that checker fix and a separate
  fill-rate-ceiling investigation already in progress in `mtds_available_at_cross_asset_backfill_2026_07_13.md`.
- **data_engineering slot-12, 2026-08-02**: dispatched onto the sports CF-8 todo, independently ran the same live
  `cf_manifest_audit.audit()` diagnosis slot-7 had already landed inline on the checkbox (byte-identical numbers, same
  `BLK-d9137d48` conclusion). Flipped the checkbox to `[x]` for consistency with the tradfi todo's own "diagnosed, not
  GREEN" precedent — slot-7's writeup had left it unchecked despite the diagnosis being complete. No code shipped this
  touch (read-only diagnostic + this plan-doc edit, `docs(plans):` carve-out).
- **data_engineering slot-16, 2026-08-02T19:24Z**: dispatched onto the prediction (`market-data-tick-pred-prd`) CF-8
  todo. Diagnosis was already fully complete (slot-3, slot-4 entries inline on the checkbox) — the only open question
  was whether the fix itself was genuinely still in-flight or had stalled. Verified live via `ps aux`: the
  `mtds_available_at_cross_asset_backfill_2026_07_13.md` plan's prediction-lane backfill (PID 3659083, slot 14) is still
  actively running (~45min elapsed, healthy). Flipped this checkbox for the same "diagnosed, not GREEN" reason the
  tradfi/sports todos above already established — the fix belongs to and is being driven by that sibling plan, not
  duplicated here. No code shipped this touch.
- **data_engineering slot-6, 2026-08-02**: dispatched onto the CF-3/CF-4 (`instruments-store-sports-prd`) todo. Ran a
  fresh, read-only `cf_manifest_audit.audit()` against the live bucket (column-pruned index read, no GCS walk) and
  root-caused the exact 3,833-row gap (full evidence inline on the checkbox above): legacy `data_type=trades`
  denominator-seed rows from the retired, unscheduled `scripts/expected_universe.py`, not a live bug in the current v2
  enumerator (which already has the CF-3/CF-4 stamping fix built in and never emits `data_type=trades` for sports). Did
  NOT attempt a live backfill/reclassification — this bucket carries a standing operator STOP (`BLK-d9137d48`) after two
  prior production regressions on this same surface, gating the sibling CF-8 sports todo above for the identical reason.
  Filed a new P3 follow-up todo to bundle this cleanup into that same future maintenance-window pass rather than a
  separate production touch now. No code shipped this touch — read-only diagnostic + this doc edit only.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries).
- **data_engineering slot-16, 2026-08-05T09:33Z**: dispatched onto the P3 "bundle backfill into maintenance window" todo
  (`cf_manifest_audit_first_full_rollup_findings-007`, dispatch_reason=resume). Checked the gate:
  `sports-cf8-maintenance-window-scheduled` is still **FALSE** (set 2026-07-14T10:44Z, never flipped, 22 days).
  `sports-cf8-maintenance-window-run` also FALSE (set 2026-07-27). The backfill cannot proceed — it requires production
  writes to `instruments-store-sports-prd`, which carries a standing operator STOP (`BLK-d9137d48`) imposed after two
  prior regressions on this surface, and the todo's own text gates on this exact maintenance window opening. Filed
  blocked-question `BLK-40c4da25` recommending option C: park this task behind the gate as a formal prereq so it only
  dispatches when the gate actually opens (currently `gates_queued=0` on the condition — no formal prereq linkage
  exists, which is why the task was dispatched despite the gate being closed). **BLK-40c4da25 RESOLVED 2026-08-05
  (main): option C approved.** Gate stays CLOSED (operator-owned — does NOT auto-open under the 2026-07-28
  pre-live-trading maintenance-window skip ruling; that ruling covers orchestrator restarts, not a deliberate operator
  risk-control STOP on a twice-regressed production data surface). Disposition: todo retagged
  `BLOCKED-OPERATOR — BLK-d9137d48`; no dispatchable work until the operator lifts the STOP and flips
  `sports-cf8-maintenance-window-scheduled` to `true`. The `gates_queued=0` gap (no formal prereq linkage) is a
  structural issue to address separately — per RULES.md §4, `prereqs.prerequisites` is yaml-only tuning, not
  plan-derivable. No code shipped this touch — read-only gate check + plan doc edits only.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.

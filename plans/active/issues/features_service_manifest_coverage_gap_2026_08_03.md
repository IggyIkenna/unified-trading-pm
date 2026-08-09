---
doc_type: issue
title:
  "features-service manifest coverage gap — onchain/defi 45% orphan, sports 30% orphan (67,077 objects) + a 6-row
  phantom-captured calendar cell with zero backing objects"
summary: >-
  First real-GCS-data run of feature_orphan_sweep.py (todo 2b of
  mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md), executed via 10 Tier-2 SPOT VMs covering all 5
  wired feature_family x applicable asset_group cells. Two of the ten cells show real, substantial `record_captured`
  manifest gaps: onchain/defi (783/1,733 objects orphaned, 45%) and sports/sports (67,077/191,831 objects orphaned, 35%)
  — both spot-checked with real object paths (legitimate feature_group/day segments, real historical dates back to the
  sports 2020-06-06 data floor), not sweep-tool artifacts. calendar/global shows the INVERSE anomaly: 6
  `capture_status=captured` manifest rows exist but the bucket (`features-calendar-prd-central-element-323112`) contains
  ZERO objects anywhere outside `_index/` — a phantom-captured case this sweep's A-E taxonomy has no class for (it
  detects real-object/no-manifest-row, not the reverse). delta_one/cefi (306 objects, 0 orphans), delta_one/tradfi (4
  objects, 0 orphans), delta_one/defi (304,257 objects, 8 orphans), volatility (all 3 applicable asset_groups) and
  delta_one/prediction read as genuinely EMPTY corpora (0 manifest cells AND 0 objects walked, verified via matching
  bucket names to delta_one's own real data in the same buckets) rather than a bucket-resolution bug — those
  families/cells simply have no production data captured yet.
status: open
nature: issue
asset_group: [defi, sports]
stage: [data]
repos: [features-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, features, manifest-completeness, orphan-real, honest-absence, phantom-row, big-finding]
related:
  [
    /plans/archive/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/archive/2026_08/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-08-03"
author: unknown
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Surfaced 2026-08-03 (slot 2) running the first real-GCS-data validation of feature_orphan_sweep.py
  (features-service@9fb37033) via 10 real Tier-2 SPOT VMs, launched through the new launch-feature-orphan-sweep-vm.sh
  (deployment-service@ca8967f + @3b9255c).
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/archive/2026_08/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
    /codex/02-data/orphan-object-detection.md,
    features-service/scripts/feature_orphan_sweep.py,
  ]
depends_on: []
---

# features-service manifest coverage gap — onchain 45% / sports 35% orphan, calendar phantom-captured

## What I found

Ran the newly-wired `feature_orphan_sweep.py` on real prod data via 10 Tier-2 SPOT VMs
(`feat-orph-{family_abbrev}-{ag_abbrev}-*`, `e2-standard-4`, all completed in under 3 minutes each, no preemption),
covering every (feature_family, asset_group) cell for the 5 wired families. Real, measured results:

| feature_family | asset_group | A (canonical) | B (legacy) | C (infra) | E (orphan_real) | manifest cells loaded |
| -------------- | ----------- | ------------- | ---------- | --------- | --------------- | --------------------- |
| delta_one      | cefi        | 306           | 0          | 0         | 0               | 31                    |
| delta_one      | tradfi      | 4             | 0          | 0         | 0               | 5                     |
| delta_one      | defi        | 304,257       | 0          | 0         | 8               | (not logged)          |
| delta_one      | prediction  | 0             | 0          | 0         | 0               | 0                     |
| volatility     | cefi        | 0             | 0          | 0         | 0               | 0                     |
| volatility     | tradfi      | 0             | 0          | 0         | 0               | 0                     |
| volatility     | defi        | 0             | 0          | 0         | 0               | 0                     |
| onchain        | defi        | 950           | 0          | 0         | **783**         | (not logged)          |
| sports         | sports      | 28,076        | 0          | 96,678    | **67,077**      | 219,329               |
| calendar       | (global)    | 0             | 0          | 0         | 0               | 6                     |

**Two genuine, substantial orphan gaps** (both spot-checked against their `run.log`'s printed E-object samples — real
`feature_group`/`day` segments, sensible values, not sweep-tool garbage):

1. **onchain/defi: 783/1,733 objects (45%) are real orphans.** Sample:
   `gs://features-defi-prd-central-element-323112/onchain/by_date/day=2023-05-20/feature_group=perp_funding_rates/features.parquet`
   — a real 2023 date, a real feature_group, simply never got a `record_captured` manifest row.
2. **sports/sports: 67,077/191,831 objects (35%) are real orphans**, PLUS an unusually large 96,678-object
   `C_manifest_infra` count (50% of the corpus) that this session did NOT fully diagnose — worth checking whether that's
   a legitimate `_index/`-prefix concentration or a mis-classified real-data shape before the backfill dispatch assumes
   it's inert. Orphan sample:
   `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2020-06-06/league=106/feature_group=fixture_features/features.parquet`
   — a real date at the sports 2020-06-06 data floor, a real league id, never manifested.

**One phantom-captured anomaly** (the inverse of an orphan — a manifest row with NO backing object — which
`feature_orphan_sweep.py`'s A-E taxonomy has no class for, since orphan detection is object-driven, not manifest-driven,
per `orphan-object-detection.md` §3):

3. **calendar/(global): the manifest has 6 `capture_status=captured` rows for `feature_family=calendar`, but
   `gs://features-calendar-prd-central-element-323112/` contains ZERO objects anywhere outside `_index/`** (verified
   directly via `gcloud storage ls` — the bucket root lists only `_index/`, and `calendar/` itself returns zero
   matches). This is NOT a sweep-tool bucket-resolution bug (the bucket name matches the declared
   `resolve_bucket(kind="features-calendar")` convention exactly, and there's genuinely nothing else in the bucket to
   have missed) — it is either 6 phantom `record_captured` rows written without their backing write ever landing (a
   genuine correctness bug in the calendar writer or a since-fixed transient), or 6 rows from a retired/renamed path
   whose objects were since deleted without the manifest being retracted. Needs its own investigation, not a guess.

**Six cells read as genuinely EMPTY, not a bucket-resolution bug**: `volatility` across all 3 applicable asset_groups
(cefi/tradfi/defi) and `delta_one/prediction` show 0 manifest cells AND 0 objects walked. Verified this is honest
absence, not the sports-bucket-mis-resolution class of bug from
`mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md` todo 1's validation: each volatility bucket name
(`features-{cefi,tradfi,defi}-prd-central-element-323112`) is the EXACT SAME bucket `delta_one` resolves to for the same
asset_group, and `delta_one` DOES have real data there (306/4/304,257 objects respectively) — so the bucket resolution
is provably correct, and `volatility`/`delta_one-prediction` simply have no production data captured yet (the
family/cell hasn't been backfilled or isn't live yet).

## Why this is a big finding, not backfill-in-this-session scope

Mirrors `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md`'s own precedent exactly: 783 + 67,077 = 67,860 real
orphan objects need `record_captured` backfill (additive-only, NEVER delete per the sweep's own taxonomy contract),
which is a genuinely separate, larger unit of work from "validate the tool works on real data" (this session's actual
scope, per todo 2b). The calendar phantom-row anomaly needs root-cause investigation before ANY fix is safe (is it a
live writer bug still producing phantom rows today, or a one-time historical artifact?) — that judgment call is exactly
the kind of thing `plan-brainstorm`/an interactive session should resolve before a backfill todo is written against it,
not something an AO worker should guess at.

## Open work

- [x] 1. ✅ [SCRIPT] P1. **Backfill `record_captured` manifest rows for onchain/defi's 783 real orphan objects** — read
      the full list from the sweep's `--report-out` parquet
      (`gs://deployment-scripts-central-element-323112/feature-orphan-sweep/20260803-104258/feat-orph-oc-defi-20260803-104258/orphan_sweep_onchain_defi.parquet`),
      write one `record_captured` row per (day, feature_group) cell (additive-only, mirrors
      `backfill_orphan_class_e.py`'s pattern — new script needed, or extend it if the shard-key shape is close enough).
      Repo: features-service. VM-run if the object count needs it, in-session may suffice at this size. —
      features-service@eaf99c9a. New `scripts/backfill_feature_orphan_class_e.py` (+ unit tests) — RE-VERIFY vs the live
      index → per-object footer row-count read → `ManifestWriter.add()` (the same legacy-add shape the live onchain
      writer itself uses, so a backfilled row is indistinguishable from a real one) → SAMPLE-VERIFY via the writer's own
      per-VM shard readback. Ran in-session (783 objects, ~427MB total, well within bounds): all 783 cells re-verified
      as still-orphan, footer-read 0 failures/0 zero-row-junk, all 783 `record_captured`'d and confirmed present with
      `capture_status=captured` in the per-VM shard
      `gs://features-defi-prd-central-element-323112/_index/per_vm/feature-orphan-backfill-onchain.parquet`. Awaits the
      manifest consolidator to merge into the canonical index; a re-run of
      `feature_orphan_sweep.py --feature-family onchain` after that should read `orphan_class_E=0`.
- [x] 2. ✅ [SCRIPT] P1. **Backfill `record_captured` manifest rows for sports/sports's 67,077 real orphan objects** —
      same pattern as todo 1, reading
      `gs://deployment-scripts-central-element-323112/feature-orphan-sweep/20260803-104314/feat-orph-spt-sports-20260803-104314/orphan_sweep_sports_sports.parquet`.
      At this volume, run on a Tier-2 SPOT VM, never in-session (STEP 0.56 memory-bounding guardrail). Repo:
      features-service. — features-service@abff85a3 + deployment-service@b09e660. Applied via
      `feat-orph-bf-spt-sports-20260803-124614` (VERDICT `recorded_cells=67077 errors=0 verify_failed=0`), consolidated,
      RE-SWEPT via `feat-orph-spt-sports-20260803-133632`: `orphan_class_E=0` (target 0), `A_canonical_manifested=95153`
      (=28,076 original + 67,077 newly recorded, exact). See Progress Log for the 3 real bugs found + fixed en route
      (data-floor guard, VM dispatch branch, O(n^2) verify loop).
- [x] 3. ✅ [SCRIPT] P2. **Diagnose sports' 96,678-object `C_manifest_infra` classification** — confirm via a bounded
      sample (list + inspect ~20 of the classified-infra object paths) whether these are genuinely `_index/`-prefix
      administrative objects (expected, inert) or a real-data shape `_infra_label()` is mis-classifying (which would
      mean the 28,076/67,077/96,678 split undercounts real coverage). Fix `feature_orphan_sweep.py`'s classification if
      the latter. Repo: features-service. — features-service@7f487699. **Neither hypothesis exactly**: a bounded
      live-GCS sample (4 probes across the corpus's date range — 2020/2022/2023/2025 `start_offset`s, 2,000 class-C
      objects inspected total, 0 exceptions) found 100% are `horizon_schema.json` — a best-effort metadata sidecar
      `features_service/sports/data/writer.py::_write_horizon_schema_sidecar` writes alongside every real
      `features.parquet` cell (schema-horizon info for ml-training, not feature row data). None are `_index/`-prefix
      objects (the walk is prefix-scoped to `sports_features/by_date/`, so `_index/` can structurally never appear in it
      — that hypothesis was checkable-false by construction, see the code comment added below). So: **genuinely inert,
      correctly excluded from A/B/D/E already** — NOT a real-data shape being mis-classified, NOT undercounting
      coverage. Shipped anyway: gave the sidecar its own explicit `_infra_label()` branch + reason
      (`"horizon-schema-sidecar"`, filename-matched) instead of leaving it in the generic `not is_parquet` catch-all —
      same functional classification (still `C_manifest_infra`, still excluded), but a FUTURE non-parquet object that
      ISN'T this known sidecar now stays distinguishable in the `reason` column instead of reading identically to this
      one. New unit test asserts the explicit reason string; full suite 44/44 passed.
- [x] ✅ 4. [DIAG] P1. **RULED 2026-08-06 (operator): investigate first, don't assume.** `[DIAG]` tag (was
      `[OPERATOR]`), AO-dispatchable — run the live-vs-historical determination this todo already specifies (check
      whether the calendar writer is STILL producing phantom captured rows today, or whether this is a one-time
      historical artifact), then file the actual fix ("patch the live writer" or "retract 6 manifest rows") as a
      separate follow-up todo once the finding is in. **Root-cause the calendar phantom-captured anomaly** (6 manifest
      rows, 0 backing objects, confirmed via direct bucket listing). — **DONE 2026-08-06 (slot 14): HISTORICAL ARTIFACT,
      not a live writer defect — and both fix halves ("patch the live writer" + "retract 6 rows") were ALREADY shipped +
      verified before this todo became AO-dispatchable, so the follow-up todo this one was to file is MOOT.**
      Live-verified (bounded direct reads of the consolidated index + bucket, no prod writes): all 6 phantom rows are
      `empty_confirmed` in the consolidated `_index/availability_index.parquet`; the only `captured` row as of today
      (economic_results/2026-08-04, row_count=6) has a real backing object with 6 real FRED rows. Root causes: (1) 2
      time_features rows (2026-07-04/05) — the pre-`23d03fef` WriteGate silent-`return` marked success despite no GCS
      write; the writer now raises `WriteGateRejectedError` → `record_empty` (never a phantom captured row); (2) 4
      calendar rows (yield_curve + economic_results 2024-01-22, economic_events 2026-07-29, economic_results 2026-08-01)
      — smoke/test-invocation debris + the broad `except Exception` in `_write_success_manifest` swallowing transient
      recording failures; objects already deleted, rows retracted to `empty_confirmed` (`features-service@5706e1a3` +
      `@66919769`). Residual gaps surfaced by this live verification are filed as new todos 5 + 6 below. Full evidence
      in the Progress Log.
- [x] 5. ✅ [SCRIPT] P2. **Close the 2026-08-04 calendar manifest-completeness gap (2 cells)** — `economic_events` and
      `yield_curve` 0-row parquet objects exist for `day=2026-08-04`
      (`calendar/{group}/by_date/day=2026-08-04/features.parquet`) but the manifest has NO rows for them (only
      `economic_results` got its captured row; row_count=6, real FRED data, backing object confirmed). Root-cause
      whether `_write_success_manifest`'s broad `except Exception` swallowed the recording failure (same class as the
      historical part-(b) finding; no Cloud Logging records retrievable for the 2026-08-04T05:46Z run window to
      confirm), then record `empty_confirmed` for the 2 cells via CAS `record_empty` (0-row objects = honest empty), and
      harden `_write_success_manifest` so a swallowed recording failure is at least visible (metric / log event) instead
      of silent. Repo: features-service. — features-service@6f4fdb46 + QG ✅ sentinel=6f4fdb46; dry-run confirmed both
      cells already empty_confirmed; metric hardening shipped; correction script idempotent.
- [ ] 6. [SCRIPT] P3. **Reconcile the stale `_legacy_seed.parquet` phantom rows** — the per-VM seed
      (`_index/per_vm/_legacy_seed.parquet`) still carries the 2 phantom `captured` time_features rows (2026-07-04/05,
      written 2026-07-27). The consolidated index is correct (`empty_confirmed`), but `read_availability_index`'s
      fallback to per-VM shards when the consolidated blob is >120s stale resurrects them (verified live:
      `correct_calendar_time_features_phantom_manifest_rows_2026_08_05.py --dry-run` read them via the fallback). The
      2026-08-05 corrections landed only in the consolidated index, not the per-VM shard the fallback reads. Fix: write
      `record_empty` superseding rows into a per-VM shard (or refresh the seed); the 2026-07-15 legacy-seed taint guard
      (`_merge_shard_frames`) ensures a newer untainted `empty_confirmed` row beats the stale seed's captured row. Repo:
      features-service.

## Progress Log

- **2026-08-03** (AO dispatch, slot 7, todo 2) — Sports backfill APPLIED to prod and VERIFIED:
  `feat-orph-bf-spt-sports-20260803-124614` VERDICT
  `already_covered=0 recorded_cells=67077 junk=0 footer_failed=0 record_errors=0 verify_failed=0`. Report:
  `gs://features-sports-prd-central-element-323112/_index/audit/feature_orphan_backfill_sports_sports.parquet`. Chain of
  work + real bugs found/fixed along the way (not pre-existing — all hit live during this exact run):
  1. `backfill_feature_orphan_class_e.py` (todo 1's generic script, covers every wired family incl. sports) had no
     sports 2020-06-06 data-floor guard — added `split_pre_floor` (features-service@7aca28ce; 0 pre-floor rows in the
     real report, but the guard is now permanent for re-runs / other AGs' data).
  2. Wrote + registered `launch-feature-orphan-backfill-vm.sh` (`feat-orph-bf-{family}-{ag}-`, longest-prefix split from
     `feat-orph-`) since sports' 67,077-object/13.1GB volume must run on a VM, not in-session
     (deployment-service@d68a49c).
  3. **First VM launch self-deleted within ~3 min, empty log.** Root cause: `VM_TASK=feature-orphan-backfill` had no
     dispatch branch in the shared `setup-data-pipeline-vm.sh` — the generic-fallback guard (added after 3 PRIOR
     identical incidents) correctly fails fast rather than silently misrouting, so the VM exit-1'd before writing any
     log, then self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`. Added the missing dispatch branch, republished the
     tarball + VM script bundle, relaunched clean (deployment-service@b09e660).
  4. `sample_verify()` in the shared backfill script recomputes 5 full-column `.astype(str)` conversions INSIDE the
     per-cell loop over every recorded cell — a real O(n^2) inefficiency (67,077^2-ish redundant conversions) that
     stretched the verify step to ~25+ minutes of silent CPU-bound work with zero progress logging (confirmed VM stayed
     RUNNING throughout, not hung). Vectorized to build (all_keys, captured_keys) sets ONCE, O(1) lookup per cell —
     behavior-preserving, existing test suite passes unchanged (features-service@abff85a3).
  5. Incidentally hit a genuinely pre-existing but UNRELATED red test
     (`tests/delta_one/unit/test_resolve_read_pipeline_mode.py::test_unrecognized_venue_falls_back_rather_than_crashing`)
     during full-QG runs — root-caused to a concurrent, CORRECT fix (`unified-trading-library@597def48`, landed by
     slot-3 mid-session) that fixed `resolve_pipeline_mode`'s asset_group case-sensitivity bug; the fix made
     `("cefi", "trades")` correctly resolve via `SOURCE_PRIORITY` (`batch_tardis`) instead of masking that registered
     pair behind the case bug and falling through to the `features-service` fallback this test asserted. Swapped in a
     genuinely-unregistered synthetic `data_type` so the test still exercises its real intent (same commit,
     features-service@abff85a3). **DONE.** Ran the manifest consolidator
     (`python -m unified_trading_library.manifest_consolidator --bucket features-sports-prd-central-element-323112 --force`)
     — clean, `rows_out=309764` (already included the new sports rows; the scheduled Cloud Scheduler consolidator cycle
     appears to have merged the per-VM shard before the manual run). Re-ran
     `feature_orphan_sweep.py --feature-family sports` fresh (VM `feat-orph-spt-sports-20260803-133632`, fresh tarball):
     `=== ACCEPTANCE: orphan_class_E=0 (target 0) ===`, `A_canonical_manifested=95153` (=28,076 original + 67,077 newly
     recorded, exact match). `C_manifest_infra=96,678` unchanged — that's todo 3's open question, untouched by this
     backfill. Todo 2 checkbox flipped above.

- **2026-08-03** (AO dispatch, slot 2) — Filed while validating `feature_orphan_sweep.py` against real GCS data (todo 2b
  of the parent tooling-gap doc). All 10 (family, asset_group) cells swept clean-or-orphaned in under 3 minutes each on
  `e2-standard-4` SPOT VMs, zero preemptions, zero sweep-tool bugs found in the classification logic itself (the one
  real bug this validation run DID find — a missing `VM_TASK=feature-orphan-sweep` dispatch branch in
  `setup-data-pipeline-vm.sh` — was fixed in-place before any cell ran, see the parent doc's own progress log).

- **2026-08-03** (AO dispatch, slot 2, todo 3) — Diagnosed sports' `C_manifest_infra=96,678` in-session (no VM needed —
  a bounded, prefix-scoped listing sample, not a corpus walk). Ran `.venv/bin/python` against
  `feature_orphan_sweep.py`'s own `_resolve_bucket`/`_FAMILY_CONFIGS`/`_infra_label` helpers with 4 `start_offset`
  probes spread across the corpus's date range (2020/2022/2023/2025), capped at 500 class-C samples each (2,000 total,
  ~4,000 objects scanned): 100% were `horizon_schema.json`, `0` `_index/`-prefix hits (structurally impossible — the
  walk's own `prefix=cfg.walk_prefix` ("sports_features/by_date/") means `_infra_label`'s `_index/`-subprefix branch can
  never match anything the walk itself returns; confirmed by reading `run_sweep`'s `list_blobs(..., prefix=...)` call).
  Traced `horizon_schema.json` to `features_service/sports/data/writer.py::_write_horizon_schema_sidecar` — a
  best-effort per-cell metadata sidecar (column horizon info for ml-training), written alongside every real
  `features.parquet` write, deliberately excluded from write-gate/manifest logic. Verdict: genuinely inert, correctly
  excluded from A/B/D/E already — NOT the mis-classification hypothesis, no coverage undercount. Shipped a small
  precision fix anyway (features-service@7f487699): explicit `_infra_label()` branch + `"horizon-schema-sidecar"` reason
  for this filename, instead of the generic `not is_parquet` catch-all, so a future non-parquet shape that ISN'T this
  known sidecar stays distinguishable in the sweep's `reason` column. New unit test
  (`test_classify_horizon_schema_sidecar_is_manifest_infra_with_explicit_reason`) asserts the explicit reason; full
  features-service suite green (`.qg_last_passed_sha` matches `7f487699`). Todo 3 checkbox flipped above. Todo 4
  ([OPERATOR] calendar phantom-row root-cause) is the only remaining open item — genuinely operator-gated, left
  untouched.

- **2026-08-03** (AO dispatch, slot 7) — Filed while validating the `commodity` family's real-GCS wiring (todo 2d of the
  parent tooling-gap doc, not a todo of this doc — folded in here since the finding is trivial: 4 objects, vs this doc's
  own 783/67,077-object gaps). Real Tier-2 SPOT VM run against `commodity-signals-batch-central-element-323112` found 4
  real class-E orphans (`cl/2017-01-01`, `cl/2026-04-14`, `ng/2017-01-01`, `ng/2026-04-14`). Backfilled + verified
  (`features-service@63e97f6a` + `@3b0c0b05`): all 4 now `capture_status=captured`. En route, found + fixed
  `backfill_feature_orphan_class_e.py`'s footer-read step assuming parquet universally (commodity's flat JSON
  `signal.json` always failed the footer read with `ArrowInvalid`) — branched on `FamilyConfig.object_suffix`, counting
  `row_count=1` per non-parquet object per the live writer's own convention. No new todo needed here — commodity is now
  fully covered (built, wired, validated, backfilled) alongside the other 7 wired families.
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **2026-08-06** (AO dispatch, slot 14, todo 4 DIAG) — Live-vs-historical determination COMPLETE (investigate-first per
  the 2026-08-06 operator ruling). Bounded direct live verification, no prod writes:
  1. **Consolidated `_index/availability_index.parquet` (12 rows, calendar family)**: all 6 phantom captured rows →
     `empty_confirmed` (2024-01-22 economic_results/time_features/yield_curve, 2026-07-04/05 time_features, 2026-07-29
     time_features/economic_results/economic_events, 2026-08-01 time_features/economic_results). Only `captured` row as
     of today = economic_results/2026-08-04 (row_count=6) with a real backing object
     (`calendar/economic_results/by_date/day=2026-08-04/features.parquet`, 6 real FRED rows, fetched
     2026-08-04T05:46:54Z). **The calendar writer is NOT producing phantom captured rows today — the 6-row anomaly is a
     one-time historical artifact.** The write-gate-rejection path is live (time_features/2026-08-04 →
     `empty_confirmed`).
  2. **Root causes** (per `features-service@23d03fef`, `@5706e1a3`, `@66919769`): (a) pre-2026-07-30 WriteGate
     silent-`return` marked success without a GCS write (2 time_features rows, written 2026-07-27); (b) smoke/test
     invocation debris + the broad `except Exception` in `_write_success_manifest` swallowing transient manifest
     recording failures (4 rows; objects already deleted by the P1 audit). Both fix halves were already shipped +
     verified — todo 4's prescribed follow-up ("patch the live writer" / "retract 6 rows") is moot.
  3. **Residual findings surfaced by this verification (filed as todos 5 + 6)**: (B) 2026-08-04 economic_events +
     yield_curve 0-row parquet objects exist
     (`calendar/economic_events|yield_curve/by_date/day=2026-08-04/features.parquet`, written 05:46:45Z/05:46:53Z, same
     run as the captured economic_results) but the manifest has NO rows for them — manifest-completeness gap, prime
     suspect = `_write_success_manifest` swallow (same class as part (b)); (A) the `_index/per_vm/_legacy_seed.parquet`
     still holds the 2 stale `captured` time_features rows (written 2026-07-27), resurrected by
     `read_availability_index`'s >120s-stale per-VM fallback — confirmed live because
     `correct_calendar_time_features_phantom_manifest_rows_2026_08_05.py --dry-run` fell back to the seed (consolidated
     blob 3056s old) and re-read the 2 phantoms, while the same check against the consolidated index shows 0. The
     corrections landed only in the consolidated index, not the per-VM shard the fallback reads.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.

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
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
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
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
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

- [ ] 1. [SCRIPT] P1. **Backfill `record_captured` manifest rows for onchain/defi's 783 real orphan objects** — read the
      full list from the sweep's `--report-out` parquet
      (`gs://deployment-scripts-central-element-323112/feature-orphan-sweep/20260803-104258/feat-orph-oc-defi-20260803-104258/orphan_sweep_onchain_defi.parquet`),
      write one `record_captured` row per (day, feature_group) cell (additive-only, mirrors
      `backfill_orphan_class_e.py`'s pattern — new script needed, or extend it if the shard-key shape is close enough).
      Repo: features-service. VM-run if the object count needs it, in-session may suffice at this size.
- [ ] 2. [SCRIPT] P1. **Backfill `record_captured` manifest rows for sports/sports's 67,077 real orphan objects** — same
      pattern as todo 1, reading
      `gs://deployment-scripts-central-element-323112/feature-orphan-sweep/20260803-104314/feat-orph-spt-sports-20260803-104314/orphan_sweep_sports_sports.parquet`.
      At this volume, run on a Tier-2 SPOT VM, never in-session (STEP 0.56 memory-bounding guardrail). Repo:
      features-service.
- [ ] 3. [SCRIPT] P2. **Diagnose sports' 96,678-object `C_manifest_infra` classification** — confirm via a bounded
      sample (list + inspect ~20 of the classified-infra object paths) whether these are genuinely `_index/`-prefix
      administrative objects (expected, inert) or a real-data shape `_infra_label()` is mis-classifying (which would
      mean the 28,076/67,077/96,678 split undercounts real coverage). Fix `feature_orphan_sweep.py`'s classification if
      the latter. Repo: features-service.
- [ ] 4. [OPERATOR] P1. **Root-cause the calendar phantom-captured anomaly** (6 manifest rows, 0 backing objects,
      confirmed via direct bucket listing) — is the calendar writer STILL producing phantom captured rows today (a live
      correctness bug needing an immediate fix), or is this a one-time historical artifact (e.g. from a renamed/retired
      bucket-kind fold, safe to just retract the 6 stale rows)? This judgment call decides whether the fix is "patch the
      live writer" or "retract 6 manifest rows" — resolve via an interactive session before writing the actual fix todo,
      don't guess at it here.

## Progress Log

- **2026-08-03** (AO dispatch, slot 2) — Filed while validating `feature_orphan_sweep.py` against real GCS data (todo 2b
  of the parent tooling-gap doc). All 10 (family, asset_group) cells swept clean-or-orphaned in under 3 minutes each on
  `e2-standard-4` SPOT VMs, zero preemptions, zero sweep-tool bugs found in the classification logic itself (the one
  real bug this validation run DID find — a missing `VM_TASK=feature-orphan-sweep` dispatch branch in
  `setup-data-pipeline-vm.sh` — was fixed in-place before any cell ran, see the parent doc's own progress log).

---
doc_type: plan
title: Predictions ML Model 2A walk-forward + arb_calculator (sports_predictions_e2e predictions half)
summary:
  Run Model 2A walk-forward validation (AUC gate) and ship the FSS arb_calculator — the predictions-ML half of the
  sports_predictions_e2e milestone.
status: active
nature: process
asset_group: [prediction, sports]
stage: [meta]
repos: [features-service, ml-service]
scope: [engineer, admin]
tags: [prediction, ml, walk-forward, arb-calculator, model-2a, auc, sports, feature-service]
related: [../epics/predictions_master.md, ../epics/sports_master.md]
created: "2026-06-12"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-20
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **Provenance**: extracted 2026-06-20 from the inline `predictions_master` epic body during the asset-group-umbrella
> restructure (L0 umbrellas had ~30+ stale May-07 inline todos that `regen_backlog_from_plan.py` never scanned). This is
> the **predictions ML half of `sports_predictions_e2e`** — Model 2A walk-forward + acceptance metrics + the Group-F AUC
> gate + the FSS `arb_calculator` + model-registry persistence + the MTDS completion-% slice. `sports_master.md`
> (line 148) explicitly states "predictions ML training + arb_calculator + Group E ML walk-forward... belong in
> `predictions_master.md`" — so these are predictions-owned, NOT sports-owned.

> **🔴 GATED ON `sports_master:Group E`** — the walk-forward run is BLOCKED until the sports half's FSS produces ≥95%
> non-NULL features for the trained universe at the buckets (`sports_master` line 463
> `[GATE] P0. Block predictions Group E until FSS produces ≥95% non-NULL features`). The sports half (288M ODDS_API row
> migration + MDPS bucketing + FSS run) lives in `sports_master`; this plan picks up the moment that gate is GREEN.

## Context

The predictions ML loop trains a directional / win-draw-loss model on the Group-D-validated feature matrix, validated by
walk-forward with log-loss / calibration / AUC acceptance metrics, gated into Group F at AUC ≥ 0.55 and calibration
error ≤ 5%. The FSS `arb_calculator` computes cross-bookmaker arb % / eligible pairs / duration. All of this is
downstream of the sports-half FSS feature production (the Group E gate).

## P0 — Model 2A walk-forward + Group-F gate

- [ ] [SCRIPT] P0. Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix. (BLOCKED-ON
      `sports_master:Group E` gate — FSS produces ≥95% non-NULL features.)
- [x] ✅ [ANALYSIS] P0. Acceptance-metrics computation code + unit tests (was: ticked as fully done — corrected
      2026-07-12, finding 241, §A2 "50 reclassified" blanket ruling). — ml-service@f3faf64 |
      `backtest_v2/acceptance_metrics.py`: `compute_fold_acceptance_metrics` (log-loss/ECE/per-class AUC per fold) +
      `aggregate_walk_forward_acceptance` (mean across folds + Group-F gate: AUC ≥ 0.55 AND ECE ≤ 5%); 18 unit tests.
      Code + tests only — NOT yet run against real walk-forward output.
- [ ] [ANALYSIS] P0. Run the acceptance-metrics computation above against the real walk-forward output (BLOCKED-ON line
      53's walk-forward run, itself BLOCKED-ON `sports_master:Group E` gate — `plans/epics/sports_master.md` line 598,
      still unchecked as of that epic's last_updated 2026-06-24).
- [x] ✅ [SCRIPT] P0. Training-config sanity check: feature columns match the FSS schema, label leakage absent,
      walk-forward window correct. — ml-service@872acbb | Fixed: (1) `SPORTS_MODEL_2A_GRID.feature_groups` corrected
      from 15 invalid calculator-level names to `["derived_features","odds_features"]` (the two valid GCS path groups);
      (2) `TARGET_LEAKAGE_COLUMNS` + `TARGET_PREDICTION_HORIZON` extended with `pregame.market.*_clv_bps` dotted target
      types used by Model 2A (previously a no-op strip → closing-odds columns remained → label leakage); walk-forward
      config verified: 5 seasonal folds (2019→2024), expanding window, `WALK_FORWARD_SPLITS` consistent; 11 unit tests
      in `tests/training/unit/test_model_2a_config_sanity.py`; QG green (153s).
- [ ] [GATE] P0. Block Group F until walk-forward AUC ≥ 0.55 AND calibration error ≤ 5%. (ACTIVE GATE — explicitly
      blocks `master_to_live_defi_2026_05_23:Group F`.)

## P0 — FSS arb_calculator

- [x] ✅ [CODE] P0. Implement (or verify shipped) `arb_calculator` in FSS: cross-bookmaker arb %, eligible pairs,
      duration. (Verify shipped status against the features-sports-service catalog first; if already shipped, flip ✅
      with the repo@sha evidence — otherwise implement.) — features-service@9347dbeb
      (`features_service/sports/arb/vig.py`: `arb_calculator` added — returns `is_arb`, `arb_pct`, `eligible_pairs`
      (dict[int, str] outcome→best-bookmaker), `duration_seconds`; exported via
      `features_service/sports/arb/__init__.py`; 9 unit tests in `tests/sports/unit/test_arb_calculator.py`; QG green
      29s).

## P1 — model registry + MTDS slice

- [ ] [ANALYSIS] P1. Persist model + metrics to the ml-models registry; tag `model_family=sports_arb_v1`. (BLOCKED-ON
      the walk-forward run.)
- [x] ✅ [AGENT] P1. **DONE 2026-07-27 (slot-6).** Predictions MTDS completion-% slice — per-(canonical_question_group,
      day) completion %: HOURLY = 24 expected/day, DAILY = 1, ELECTION = 1 over months/years. (Phase-1 lifecycle
      ingestion + classifier confirmed shipped — CANONICAL_GROUP_METADATA is live in UAC.) Read-only analysis (no code
      change); repo: unified-trading-pm. Full per-cadence completion-% table + methodology in the Progress Log below.
      **Finding surfaced (not fixed here, mirrors the sports MTDS-slice precedent's "TRANSFERMARKT_LEAGUES 100% empty —
      needs P0 triage" callout)**: the `hourly`/`5min`/`intraday`/`single` cadences — 8 registered groups
      (`BTC_UP_DOWN_HOURLY`, `ETH_UP_DOWN_HOURLY`, `BTC_UP_DOWN_5MIN`, `ETH_UP_DOWN_5MIN`, `BTC_UP_DOWN_INTRADAY`,
      `ETH_UP_DOWN_INTRADAY`, `ELECTION_PRESIDENT_2028`, `OSCARS_BEST_PICTURE`) — have **ZERO** manifest rows in the
      live prediction manifest as of 2026-07-27T16:01:28Z; completion % for the todo's own named HOURLY/ELECTION
      examples is undefined (0/0), not merely low.
- [ ] [DIAG] P2. Investigate why
      `BTC_UP_DOWN_HOURLY`/`ETH_UP_DOWN_HOURLY`/`*_5MIN`/`*_INTRADAY`/`ELECTION_PRESIDENT_2028`/ `OSCARS_BEST_PICTURE`
      have zero `prediction_canonical_question_group` manifest rows (captured, empty_confirmed, attempted_failed, AND
      expected_unattempted all zero) — is this a genuinely-not-yet-listed market (honest-absence, no action needed) or a
      classifier/writer gap silently dropping these 8 groups before any manifest row is ever emitted (a correctness
      bug). Repo: market-tick-data-service. Source: this todo's completion-% slice, recorded 2026-07-27 (slot-6) in the
      Progress Log below.

## Success criteria

- Model 2A walk-forward runs on the Group-D-validated feature matrix with reported log-loss / calibration / AUC.
- Group F unblocks only on AUC ≥ 0.55 AND calibration ≤ 5%.
- `arb_calculator` exists in FSS (verified-shipped or newly implemented), computing cross-bookmaker arb % / eligible
  pairs / duration.
- Model + metrics persisted to ml-models registry; predictions MTDS completion-% slice surfaced per
  (canonical_question_group, day).

## Progress Log

### 2026-07-27 (slot-6) — Predictions MTDS `canonical_question_group` completion-% slice done, checkbox flipped

Picked up via `/boot` (`prediction_satellite_ao_dispatch_batch2-003`). Read-only analysis, no code shipped, per the
todo's own scope.

**Method**: single-walk, column-pruned, filter-pushdown read of the live prediction availability manifest
(`market-data-tick-pred-prd-central-element-323112`, resolved via
`resolve_bucket_name(cloud="gcp", kind="market-data-tick-prediction")`) using
`unified_trading_library.manifest_writer.read_availability_index(bucket, columns=[...], filters=[("data_type", "==", "prediction_canonical_question_group")])`
— the same slim/filtered pattern used for todo 2's instrument_type census earlier in
`prediction_satellite_ao_dispatch_batch2_2026_07_25.md`. `instrument_id` on these bundle rows carries the
`canonical_question_group` string verbatim (per
`market_tick_data_service/engine/orchestrator/manifest_finalize.py::_finalize_prediction_bundles`'s `row_key`). Grouped
by `(instrument_id, date)` → the per-(canonical_question_group, day) table the todo names, joined against UAC's
`CANONICAL_GROUP_METADATA` for each group's registered `cadence`. Read timestamp: 2026-07-27T16:01:28Z.

**Scale**: 68,667 `prediction_canonical_question_group` manifest bundle rows → 36,039 distinct (cqg, day) rows; 82 of 97
registered canonical_question_groups have ≥1 live manifest row.

**Per-cadence completion % table** (captured / empty_confirmed / attempted_failed / expected_unattempted counts, and
`reachable_coverage_pct = captured / (captured + attempted_failed + expected_unattempted)` — empty_confirmed EXCLUDED
from the numerator per the RULED formula, `/codex/02-data/availability-manifest-and-data-status.md` line 1054):

| cadence                           | captured | empty_confirmed | attempted_failed | expected_unattempted | total rows | reachable_coverage % | distinct CQGs |
| --------------------------------- | -------: | --------------: | ---------------: | -------------------: | ---------: | -------------------: | ------------: |
| irregular                         |    7,713 |          24,722 |                4 |                1,614 |     34,053 |                82.66 |            44 |
| daily                             |    8,556 |          16,468 |                0 |                1,058 |     26,082 |                89.00 |            29 |
| monthly                           |    1,136 |           3,070 |                0 |                  134 |      4,340 |                89.45 |             5 |
| BLANK_INSTRUMENT_ID*              |        0 |           2,280 |                0 |                    0 |      2,280 |                  n/a |             1 |
| weekly                            |      173 |             922 |                0 |                  217 |      1,312 |                44.36 |             2 |
| 15min                             |       14 |             582 |                0 |                    4 |        600 |                77.78 |             2 |
| hourly / 5min / intraday / single |        0 |               0 |                0 |                    0 |          0 |                  n/a |             0 |

\* `BLANK_INSTRUMENT_ID` = 2,280 rows where `instrument_id` is an empty string rather than a registered
`CanonicalQuestionGroup` value — all `empty_confirmed`, not a registered group; a data-quality footnote, not part of the
completion-% denominator for any named cadence.

**Finding — 8 registered groups have ZERO manifest rows of any capture_status** (not low completion — genuinely absent):
`BTC_UP_DOWN_HOURLY`, `ETH_UP_DOWN_HOURLY` (the todo's own "HOURLY = 24 expected/day" example), `BTC_UP_DOWN_5MIN`,
`ETH_UP_DOWN_5MIN`, `BTC_UP_DOWN_INTRADAY`, `ETH_UP_DOWN_INTRADAY`, `ELECTION_PRESIDENT_2028` (the todo's own "ELECTION
= 1" example), `OSCARS_BEST_PICTURE`. Filed as a new `[DIAG] P2` todo above (mirrors the sports MTDS-slice precedent's
"TRANSFERMARKT_LEAGUES 100% empty — needs P0 triage" callout in `sports_master.md` — surfaced, not fixed inline, since
root-causing a possible classifier/writer gap is outside this read-only todo's scope).

Full per-(cqg, day) table (36,039 rows) generated to a local scratchpad CSV during this analysis (not committed —
ephemeral, reproducible from the method above on demand).

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the walk-forward actually runs on real
infra against the sports-FSS feature matrix once the Group E gate is GREEN; acceptance metrics are computed and
recorded; the Group-F gate decision is made from the real AUC/calibration numbers, not a smoke run.

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
priority: P2
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
last_updated: 2026-06-27
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/epics/predictions_master.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    ml-service/ml_service/training/backtest_v2/acceptance_metrics.py,
    features-service/features_service/sports/arb/arb_calculator.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/manifest_finalize.py,
  ]
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
- [x] ✅ [DIAG] P2. **DONE 2026-08-05 (slot 15, data_engineering) — verdict recorded, both checkboxes flipped.**
      Investigate why 8 registered CQGs have zero manifest rows. **Verdict**: 6 are genuinely-empty-by-design (markets
      don't exist) + 2 are classifier gaps (taxonomy→CQG underlying-key mismatch). Full evidence below in the Progress
      Log. Repo: unified-trading-pm (diagnostic only, no code change). Source: batch6 plan todo 10.

## Success criteria

- Model 2A walk-forward runs on the Group-D-validated feature matrix with reported log-loss / calibration / AUC.
- Group F unblocks only on AUC ≥ 0.55 AND calibration ≤ 5%.
- `arb_calculator` exists in FSS (verified-shipped or newly implemented), computing cross-bookmaker arb % / eligible
  pairs / duration.
- Model + metrics persisted to ml-models registry; predictions MTDS completion-% slice surfaced per
  (canonical_question_group, day).

## Progress Log

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 5 open. Four are explicitly BLOCKED-ON the
  `sports_master` Group-E gate (FSS >=95% non-NULL features), a still-open cross-plan prerequisite carried in this doc's
  own red banner; the doc is additionally `locked_by: live-defi-rollout`. The fifth (the `[DIAG] P2` on 8 registered
  CQGs with zero manifest rows) is CONFLICT — claimed by `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`
  todo 10.

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

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — carries a 🔴 GATED ON `sports_master:Group E`
  banner (walk-forward BLOCKED until FSS produces >=95% non-NULL features) and `locked_by: live-defi-rollout`; 3 of the
  5 open todos are explicitly BLOCKED-ON that gate or on each other, and one is itself an ACTIVE `[GATE]`
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added 3 source paths (Model 2A acceptance metrics,
  FSS `arb_calculator`, and the MTDS manifest-finalize orchestrator the open `[DIAG]` zero-manifest-rows todo targets),
  previously codex+epic only.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (prediction tranche)**: KEEP-NA, valid — re-checked
  against the full round-11 precedent set (IAM self-service default, D16 all-repos carve, S5.1 tiering,
  plan-destination-default-to-AO for auto-filed findings, escalation-N=3-days, reversibility-qualified deletes
  agent-executable after a fresh check, Option B retirement, GSM secret `deepseek-v4-pro-api-key` + 5 Slack webhooks) —
  none apply. All 4 remaining open items are chained/blocked on the still-open cross-plan `sports_master:Group E` gate
  (re-confirmed `plans/epics/sports_master.md` line 629 unchecked live), a cross-asset-group prerequisite none of
  round-11's criteria touch. No reclassification.

### 2026-08-05 (slot 15, data_engineering, dispatch `prediction_satellite_ao_dispatch_batch6-010`) — [DIAG] P2 verdict

**Investigation scope**: why `BTC_UP_DOWN_HOURLY`/`ETH_UP_DOWN_HOURLY`/`*_5MIN`/`*_INTRADAY`/
`ELECTION_PRESIDENT_2028`/`OSCARS_BEST_PICTURE` (8 groups) have zero manifest rows across all capture_status columns.

**Method**: read the full UAC registry (`canonical_groups.py` — all 8 are properly registered with complete
`CANONICAL_GROUP_METADATA`), the classifiers (`classifiers.py` — Polymarket slug→CQG and Kalshi ticker-prefix→CQG
routing), the MTDS writer (`manifest_finalize.py`'s `_finalize_prediction_bundles` — handles zero-count CQGs correctly
via the zero-trading-day sentinel fan-out at lines 501-522), and the taxonomy (`_prediction_market_taxonomy.py` — slug
prefixes + resolution-period inference). Then live-queried both exchanges: Kalshi's public `/trade-api/v2/series/`
endpoint (verified working — `KXBTCD` returns a real series object) and Polymarket's Gamma API.

**Per-group verdict**:

| Group                     | Verdict                              | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BTC_UP_DOWN_HOURLY`      | Genuinely-empty-by-design            | Kalshi `KXBTCI` → `{"error":"not_found"}` — series never existed. The classifier prefix entry (`KXBTCI`→`BTC_UP_DOWN_HOURLY`) is dead code: preemptive registration for a series Kalshi never created. Kalshi's actual BTC markets (`KXBTCD`/`KXBTC`) map to DAILY/PRICE_RANGE groups. No Polymarket hourly-BTC markets found.                                                                                                                                                                                                                                    |
| `ETH_UP_DOWN_HOURLY`      | Genuinely-empty-by-design            | Kalshi `KXETHI` → `{"error":"not_found"}` — same pattern as BTC. The classifier prefix entry (`KXETHI`→`ETH_UP_DOWN_HOURLY`) is dead code.                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `BTC_UP_DOWN_5MIN`        | Genuinely-empty-by-design            | Kalshi's shortest BTC interval is 15min (`KXBTC15M` → `BTC_UP_DOWN_15MIN`, which HAS data). No Kalshi 5min BTC series exist (confirmed via full Crypto category listing: 272 series, 0 with 5min frequency). Kalshi classifier has no 5min prefix mapping at all (a minor gap if 5min series ever launch, but currently no-op). No Polymarket 5min BTC markets found.                                                                                                                                                                                             |
| `ETH_UP_DOWN_5MIN`        | Genuinely-empty-by-design            | Same as BTC 5min. Kalshi has `KXETH15M` (→ `ETH_UP_DOWN_15MIN`, has data) but no 5min series.                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `BTC_UP_DOWN_INTRADAY`    | Genuinely-empty-by-design            | No Kalshi intraday-BTC series exist. No Polymarket intraday-BTC markets found. The Polymarket taxonomy CAN classify intraday-resolution markets (detects "minute"/"intraday" tokens in slugs), but no such slugs exist for BTC.                                                                                                                                                                                                                                                                                                                                   |
| `ETH_UP_DOWN_INTRADAY`    | Genuinely-empty-by-design            | Same as BTC intraday.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `ELECTION_PRESIDENT_2028` | **Classifier gap** (Polymarket side) | The `_prediction_market_taxonomy.py` slug prefix map routes `presidential-`/`us-president-` → `(POLITICS_US, "US_ELECTION")`, but `classifiers.py`'s `_CATEGORY_UNDERLYING_TO_EVENT_GROUP` expects key `(POLITICS_US, "PRESIDENT_2028")`. These don't match — all Polymarket presidential election markets (e.g., real live market `will-gavin-newsom-win-the-2028-democratic-presidential-nomination`) fall to OTHER. Kalshi has no presidential ticker prefix mapping. **Impact**: real presidential-2028 markets exist but are silently mis-bucketed to OTHER. |
| `OSCARS_BEST_PICTURE`     | **Classifier gap** (Polymarket side) | Same pattern: taxonomy maps `oscars-`/`oscar-` → `(CULTURE, "OSCARS")`, but the CQG event group map expects key `(CULTURE, "OSCARS_BEST_PICTURE")`. All Polymarket Oscars markets fall to OTHER.                                                                                                                                                                                                                                                                                                                                                                  |

**Root cause summary**: not a writer gap (the manifest writer's zero-trading-day sentinel correctly handles absent CQGs)
and not registry drift (all 8 groups are fully registered). The 6 sub-daily BTC/ETH groups are honest absence — the
markets simply don't exist on either venue. The 2 event groups (ELECTION_PRESIDENT_2028, OSCARS_BEST_PICTURE) are
classifier gaps: the taxonomy emits a different `underlying` value than the CQG event-group map expects, so real markets
route to OTHER instead.

**Recommendation**: fix the 2 classifier gaps (add `"US_ELECTION"`→`ELECTION_PRESIDENT_2028` and
`"OSCARS"`→`OSCARS_BEST_PICTURE` entries to `_CATEGORY_UNDERLYING_TO_EVENT_GROUP`, or align the taxonomy to emit the
expected keys). The 6 dead Kalshi ticker-prefix entries (`KXBTCI`/`KXETHI`) are harmless dead code — remove or annotate
as preemptive. The existing `[UAC] P2` politics/geo canonicalization todo in batch6 already covers the
ELECTION_PRESIDENT_2028 path. OSCARS_BEST_PICTURE is net-new — filed as a follow-up in the batch6 plan.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (prediction tranche, autonomous)**: KEEP-NA, valid — 4 open todos, all chained/
  blocked on the still-open cross-plan `sports_master:Group E` gate (`plans/epics/sports_master.md` line 629, verified
  unchecked live, plus its own upstream FSS-run/feature-matrix-verification prerequisites also still unchecked). No
  reclassify/archive/duplicate candidates. Agrees with the 2026-07-30 audit's verdict.
- **na-eligibility-audit 2026-08-10 (prediction tranche)**: KEEP-NA, valid — re-verified live, 4 open, unchanged.
  `sports_master.md`'s Group E gate checkbox still `[ ]` unchecked. Doc stays NA.

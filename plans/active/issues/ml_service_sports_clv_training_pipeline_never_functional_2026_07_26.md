---
doc_type: issue
title:
  ml-service's SPORTS training pipeline has never actually loaded real sports features — 3 stacked bugs found while
  attempting the CLV retrain
summary: >-
  Attempted the CLV model retrain (sports_halftime_odds_sfi_vs_inplay_2026_07_16.md's Open Todo #5, prerequisite — the
  ODDS_FEATURES recompute — already confirmed done) and hit 3 independent, stacked bugs in ml-service's training
  CLI/pipeline, each masking the next: (1) `pipeline_handler.py::_build_pipeline_config` reads the SINGULAR
  `--target-type` (not `--target-types`) with no fallback despite the CLI help's own claim ("Defaults to first value in
  --target-types"), so omitting it crashes with `'None' is not a valid TargetType`; (2) the `--family` flag (required +
  validated for `--asset-group SPORTS`) is never actually consumed anywhere in `ml_service/training/` to scope target
  types/variants — dead wiring; (3) the real, deep finding: `cloud_feature_provider.py`'s feature-loading dispatcher has
  a DEFI-specific branch (`_query_defi_features`, a non-instrument-id fixture/pool-based loader) but NO equivalent
  SPORTS branch — sports falls through to the generic instrument-id-based `_query_gcs_features`, which trivially returns
  empty since sports training passes `instruments=[]` (correct — sports has no instrument tickers), then silently falls
  back to BigQuery which also returns nothing. Live-verified real `feature_group=odds_features` data DOES exist in GCS
  for the exact date probed (`gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-04-17/`),
  ruling out data-absence — this is a genuine, unimplemented code path. **ml-service has likely never successfully
  trained on real SPORTS features at all**, not just for CLV.
status: open
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [ml-service]
scope: [engineer]
tags: [ml-service, sports, clv, training-pipeline, feature-loading, architecture-gap]
related:
  [
    /plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/archive/issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md,
  ]
created: 2026-07-26
author: unknown
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-7, data_engineering) attempting sports_satellite_ao_dispatch_batch5-015's item (c), CLV
    model retrain — the ODDS_FEATURES-recompute prerequisite is confirmed done, so this is not a data-readiness gap.",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md,
    /plans/archive/2026_08/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/archive/issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md,
    ml-service/ml_service/training/app/core/cloud_feature_provider.py,
    ml-service/ml_service/training/cli/handlers/pipeline_handler.py,
  ]
supersedes:
superseded_by:
---

> **✅ OPERATOR RULING 2026-08-08 — WIRE IT, do not drop it.** The sole open todo asks whether to wire `--family` to
> actually scope SPORTS training or drop the required-argument validation as vestigial. Ruled: **wire it.** Each family
> must genuinely scope leagues and target-types (e.g. `pregame_clv_family` → CLV targets over the pre-match horizon set)
> — the CLV work needs that handle, and a required flag that provably does nothing (`grep '\.family'` returns zero hits
> outside argparse) is worse than either alternative. Implemented by
> `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`; this doc's checkbox is flipped by that plan's finalize
> sibling.

# ml-service SPORTS training pipeline never actually loaded real features

## What I found

Reproduced the exact 3 quarantined CLV model artifacts first, to scope the retrain correctly:

```
gs://ml-store-prd-central-element-323112/models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260417154715/training-period-2026-04/QUARANTINED.json
gs://ml-store-prd-central-element-323112/models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260417164033/training-period-2026-04/QUARANTINED.json
gs://ml-store-prd-central-element-323112/models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260417201036/training-period-2026-04/QUARANTINED.json
```

All 3 carry `"quarantined": true, "usable": false, "promotion_blocked": true`, quarantined 2026-07-16, citing
`features-service@bf6fc2f4` + `ml-service@c0603cbb` as the fix and this doc's parent as the tracking issue. (Note: the
`CEFI_UNKNOWN_` prefix in the model_id is itself a labeling artifact, not evidence these are CeFi models — the
`target_type=clv` + `timeframe=fixture` combination is sports-only.)

### Environment note (fixed, not a code bug)

A fresh `uv sync` in this repo installed a corrupted `google-cloud-compute==1.47.0` (missing `gapic_version.py`,
`ImportError: cannot import name 'gapic_version'` on any `unified_trading_library` GCP bootstrap). Fixed locally via
`uv sync --reinstall-package google-cloud-compute`. Flagging in case this is a cache-poisoning issue that hits other
fresh checkouts, not asserting it is.

### Bug 1 — `--target-type` (singular) has no fallback to `--target-types`

```
ml-service --operation pipeline --asset-group SPORTS --family pregame_clv_family --target-types clv --timeframes fixture ...
→ ERROR Pipeline failed: 'None' is not a valid TargetType
```

`ml_service/training/cli/handlers/pipeline_handler.py::_build_pipeline_config` reads `args.target_type` (the SINGULAR
flag) directly into `TargetType(target_type_str)`. The CLI help text for `--target-type` claims "Defaults to first value
in `--target-types`" but no such fallback exists in the handler — omitting the singular flag passes `None` straight into
the enum constructor. Workaround: pass both `--target-types clv --target-type clv`.

### Bug 2 — `--family` is validated but never consumed

`ml_service/training/cli/main.py` requires `--family` for `--asset-group SPORTS` (validated, with a clear error if
omitted) but `grep -rn '\.family\b' ml_service/training/` (excluding tests) returns ZERO hits outside the argparse
definition itself. The flag exists purely as a validation gate — it does not scope target types, variants, or anything
else. Passing any of the 5 documented family values produces identical behavior. Not the blocking bug here, but worth
fixing alongside — either wire it to actually filter target types/leagues, or drop the requirement if it's genuinely
vestigial.

### Bug 3 — SPORTS has no feature-loading branch (the real blocker)

After fixing bug 1, training reaches feature loading and fails:

```
WARNING GCS primary path returned no data, falling back to BigQuery
WARNING No features queried
ERROR Training failed: No features loaded for pipeline
```

`ml_service/training/app/core/cloud_feature_provider.py`'s feature dispatcher (~line 570-620):

```python
if asset_group == "DEFI":
    defi_result = self._query_defi_features(instrument_ids, timeframes, start_date, end_date, ...)
    ...
try:
    gcs_result = self._query_gcs_features(instrument_ids, timeframes, start_date, end_date, ...)
    ...
    logger.warning("GCS primary path returned no data, falling back to BigQuery")
```

DEFI gets its own non-instrument-id loader (`_query_defi_features`, handles on-chain pools by pool/protocol, not by
instrument ticker). **SPORTS has no equivalent branch** — it falls through to the generic
`_query_gcs_features(instrument_ids, ...)`, which is built around CEFI/TRADFI-style instrument tickers. Sports training
correctly passes `instruments=[]` (sports has no instrument concept — fixtures/leagues instead), so this generic query
trivially resolves zero rows, then the BigQuery fallback also returns nothing (sports features likely aren't mirrored to
BigQuery either, or the fallback query is ALSO instrument-id-shaped).

**Confirmed this is a genuine code gap, not data absence**: live GCS listing shows real, current
`feature_group=odds_features` (and 7 other feature groups) data at the EXACT date probed:

```
gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-04-17/feature_group=odds_features/
```

## Why it matters

This means **ml-service's training pipeline has likely never successfully trained on real SPORTS feature data at all** —
not a CLV-specific gap. The 3 quarantined CLV models (2026-04-17) presumably trained via some other, less generic path
(perhaps a since-removed sports-specific loader, mock data, or a manually-assembled dataset) rather than through this
same `cloud_feature_provider.py` dispatcher — worth checking how those 3 models were originally produced if that history
is recoverable, since it may point at the right fix shape. Any OTHER sports target (xg, ht_delta) attempted through this
same CLI path would hit the identical wall.

## Recommended decision

- [x] ✅ [CODE] P2. Fix `pipeline_handler.py::_build_pipeline_config` to fall back `target_type` to `target_types[0]`
      when `--target-type` is omitted, matching the CLI help's documented behavior. (repo: ml-service) — **DONE
      2026-07-26** (slot-6, `data_engineering`): `ml-service@7cccb236` — fixed in both `execute()` and
      `_build_pipeline_config()` (same `getattr(..., None) or default` gotcha in each). Live-verified: the exact repro
      command from this doc (`--target-types clv`, `--target-type` omitted) no longer crashes with
      `'None' is not a valid TargetType`.
- [ ] [CODE] P3. Either wire `--family` to actually scope SPORTS training (leagues/target-types per family) or drop the
      required-argument validation if it's intentionally vestigial — currently it validates but does nothing. (repo:
      ml-service) — **EXPLICITLY DEFERRED 2026-07-26** (slot-6, `data_engineering`): confirmed still true
      (`grep -rn family ml_service/training/cli/handlers/*.py` returns zero hits outside `parser.py`'s validation gate).
      Not fixed this session — this doc's own framing ("either wire it or drop it") is a genuine design decision, not a
      mechanical fix, and P3/non-blocking per this doc's own priority. Left open for whoever picks up the design call.
- [x] ✅ [CODE] P2. Add a SPORTS branch to `cloud_feature_provider.py`'s feature dispatcher (mirroring
      `_query_defi_features`'s non-instrument-id pattern) that reads
      `sports_features/by_date/day={D}/ feature_group={G}/` by fixture/league instead of by `instrument_ids`. This
      is the real blocker for the CLV retrain (and any other sports target). (repo: ml-service) — **DONE 2026-07-26**
      (slot-6, `data_engineering`): `ml-service@7cccb236`. On closer inspection a SPORTS branch already existed in
      `query_features()` (since 2026-05-01) but was UNREACHABLE — the asset-group dispatch derived from
      `_get_asset_group(instrument_ids[0])` always falls back to `"CEFI"` when `instrument_ids` is empty (the correct
      calling shape for sports), so the existing SPORTS branch could never fire. Fix: added an explicit
      `asset_group: str | None = None` override param to `query_features()`, threaded from
      `pipeline_handler.py::_load_features()`'s `args.asset_group`. **Live-verified end-to-end** against real prod
      `features-sports-prd`: the exact repro command now loads **2,383 fixtures x 956 features across the full
      2026-04-01..17 window** (previously: zero features, every time). `quality-gates.sh` green on ml-service (2103
      passed, 4 skipped, coverage 80.00%).
- [x] ✅ [ML] P2. Once the above ships, retrain the 3 CLV model variants (`training-period-2026-04`,
      `pregame_clv_family`, `timeframes=fixture`, date range matching the original 2026-04-17 training run if
      recoverable) and independently re-verify against real prod features-sports-prd data before promoting/citing. The 3
      quarantined artifacts stay in place, untouched, as the leak reference. Source:
      `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` Open Todo #5. — **ATTEMPTED 2026-07-26, genuinely BLOCKED one
      layer deeper** (slot-6, `data_engineering`): with Bugs 1+3 fixed, the retrain got past feature loading for the
      first time ever, then crashed in the pipeline's `feature_selection` phase — `GradientBoostingClassifier.fit()`
      received 32 non-numeric (object-dtype) columns from the SPORTS feature frame (identity columns like
      `fixture_id`/`event_id` plus several `xg_*` columns mis-typed upstream). A second, independent finding surfaced in
      the same run: the CLV target resolves 100% "flat" for this exact date window
      (`pinnacle_closing_odds_home`/`odds_home_avg` missing), so even a dtype-fixed retrain of this specific window may
      not produce a meaningful model. Both filed with full diagnostic evidence in
      `/plans/archive/issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`.
      **CLOSED-BY-CITATION 2026-08-06 (na-eligibility-audit, sports tranche, KEEP-NA-STALE)**: the retrain this todo
      asks for was independently completed and GCS-verified in
      `/plans/archive/issues/ml_service_pipeline_handler_clv_target_bypasses_odds_targets_merge_2026_08_03.md` (an
      `assigned_vm: planning` doc) — its 2026-08-03 Progress Log records 3 CLV model variants trained via
      `--operation train --skip-dependency-check --task-type regression` against real prod `features-sports-prd` data
      (window 2026-04-01..17, matching this todo's date range), non-degenerate target
      (`up=64/10.7%, flat=505/84.6%, down=28/4.7%`), independently GCS-verified at
      `gs://ml-store-prd-central-element-323112/models/models/CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260803{191857,192941,193831}/training-period-2026-08/model.joblib`
      (372,665 bytes each). Not reclassifying this doc — the work is already done, just tracked under a different doc's
      checkbox; this is a citation fix only.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — todo 1 is EXPLICITLY DEFERRED in its own text
  as 'a genuine design decision, not a mechanical fix' (wire `--family` to actually scope SPORTS training vs drop the
  vestigial required-arg), and todo 2 (the CLV retrain) is blocked one layer deeper on
  `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`, which this pass reclassified instead
- **na-eligibility-audit 2026-08-03**: re-read (no `last_updated` field, so always in scope; the only change since 07-30
  was a referrer-path fix pointing to the now-archived
  `ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`, applied by that doc's own
  archival ritual, not verdict-relevant). **KEEP-NA stands, verdict unchanged.** Todo 1 (`[CODE] P3`, wire vs. drop
  `--family`) remains an explicit design decision. Todo 2 (`[ML] P2`, CLV retrain) is now code-unblocked (the archived
  doc fixed the dtype crash) but its value is still contingent on an unresolved judgment call — that same archived doc
  found the CLV target resolves 100% flat for the 2026-04 window, so a bounded "just retrain" todo would first need a
  human call on window selection before it is genuinely worker-determinable.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added
  `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`, the doc directly explaining the "unresolved
  judgment call" the 2026-08-03 na-eligibility-audit entry above references.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged. Note (not context_scope,
  flagging only):
  `/plans/archive/issues/ml_service_pipeline_handler_clv_target_bypasses_odds_targets_merge_2026_08_03.md` reports the
  CLV retrain actually succeeded end-to-end (2026-08-03, via `--operation train --skip-dependency-check`, 3 GCS-verified
  model artifacts) — this doc's own open `[ML] P2` todo 2 ("retrain the 3 CLV model variants") may already be satisfied
  in substance by that separate doc's work; not verified in enough depth this pass to flip the checkbox myself (out of
  this skill's scope).

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid (sports tranche) — verified and flipped the `[ML] P2` retrain todo
  to closed-by-citation (KEEP-NA-STALE: the retrain was independently completed and GCS-verified in
  `ml_service_pipeline_handler_clv_target_bypasses_odds_targets_merge_2026_08_03.md`, confirming the 2026-08-06
  context-scout's flagged note). Doc stays NA — the sole remaining open todo (`[CODE] P3`, wire vs. drop `--family`) is
  unchanged, still an explicit design decision per every prior pass's reasoning.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — the sole open todo is now resolved by
  the dated `✅ OPERATOR RULING 2026-08-08` banner at the top of this doc ("WIRE IT, do not drop it") AND is already
  being implemented by `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md` (`assigned_vm: planning`, live,
  status: active) — its "ML" section's first todo names this doc's sole open todo verbatim as what it resolves.
  Never-re-litigate + conflict-check both point the same way: do NOT flip this doc to `planning` (would duplicate an
  already-active implementing plan in the same `parent_epic`); checkbox is flipped by that plan's finalize sibling once
  the wiring ships. Citation-only, no reclassification.

- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — reconfirmed `sports_taxonomy_p3_consumers_2026_08_08.md`
  is still `status: active` / `assigned_vm: planning` with its own open `[CODE] P0` todo ("Wire ml-service `--family`
  to actually scope SPORTS training", explicitly citing the operator ruling) — the implementing plan is genuinely
  in-flight, not stalled. No change: this doc's sole open todo stays resolved-by-citation to that plan's finalize.

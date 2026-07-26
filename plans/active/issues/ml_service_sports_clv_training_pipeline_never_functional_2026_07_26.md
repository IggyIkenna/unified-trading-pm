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
  ]
created: 2026-07-26
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
supersedes:
superseded_by:
---

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

- [ ] [CODE] P2. Fix `pipeline_handler.py::_build_pipeline_config` to fall back `target_type` to `target_types[0]` when
      `--target-type` is omitted, matching the CLI help's documented behavior. (repo: ml-service)
- [ ] [CODE] P3. Either wire `--family` to actually scope SPORTS training (leagues/target-types per family) or drop the
      required-argument validation if it's intentionally vestigial — currently it validates but does nothing. (repo:
      ml-service)
- [ ] [CODE] P2. Add a SPORTS branch to `cloud_feature_provider.py`'s feature dispatcher (mirroring
      `_query_defi_features`'s non-instrument-id pattern) that reads
      `sports_features/by_date/day={D}/     feature_group={G}/` by fixture/league instead of by `instrument_ids`. This
      is the real blocker for the CLV retrain (and any other sports target). (repo: ml-service)
- [ ] [ML] P2. Once the above ships, retrain the 3 CLV model variants (`training-period-2026-04`, `pregame_clv_family`,
      `timeframes=fixture`, date range matching the original 2026-04-17 training run if recoverable) and independently
      re-verify against real prod features-sports-prd data before promoting/citing. The 3 quarantined artifacts stay in
      place, untouched, as the leak reference. Source: `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` Open Todo #5.

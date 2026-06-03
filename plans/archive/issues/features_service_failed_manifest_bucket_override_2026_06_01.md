---
title: features-service _failed_group_manifest bypasses PROTOCOL_DATA_SINK_BUCKET_* override
created: 2026-06-01
author: harsh
source:
  - features_service/delta_one/cli/handlers/_failed_group_manifest.py
  - features_service/delta_one/config.py
  - features_service/delta_one/app/core/feature_writer.py
  - features_service/common/__init__.py
locked_by: live-defi-rollout
---

> **✅ RESOLVED + ARCHIVED 2026-06-01 (slot 7).** Fix landed on LDR: **features-service@`587e494e`**.
> `config.get_output_bucket` now honours `get_data_sink` (PROTOCOL*DATA_SINK_BUCKET*{AG}) first then bucket-name SSOT;
> `get_input_bucket` mirrors it via `get_data_source` (PROTOCOL*DATA_SOURCE_BUCKET*{AG}); `get_instruments_store_bucket`
> stays on the SSOT (the `routing_key=asset_group` trick would resolve the wrong bucket for it). +3 passing unit tests
> in `tests/unit/test_config.py` (sink override / source override / SSOT fallback); ruff-clean; codex-clean.
>
> **Landing was unblocked by a CI-config fix**: features-service had **no `main`/`staging` branches**, so its GitHub
> default branch was `live-defi-rollout` and the `require-quality-gates` ruleset (target `~DEFAULT_BRANCH`) wrongly
> gated LDR. Fixed: created `main`+`staging` from LDR HEAD + set default → `main` (so v2 now gates `main`, LDR is
> free-push, as per the workspace model). The features QG coverage-floor / per-family `PYTEST_UNIT_DIR` issue now
> correctly gates main-promotion, not LDR — tracked separately in `cicd_contract_hardening_2026_06_01.md`.

## What I found

features-service delta*one has TWO bucket-resolution codepaths that DISAGREE on whether to honour the
`PROTOCOL_DATA_SINK_BUCKET*{AG}` env override:

1. **Success path** — `feature_writer._get_sink_bucket(asset_group)`
   [features_service/delta_one/app/core/feature_writer.py:61-80](../../features-service/features_service/delta_one/app/core/feature_writer.py#L61-L80)
   → `get_data_sink(routing_key=asset_group.lower())` → honours `PROTOCOL_DATA_SINK_BUCKET_{AG}` ✓
2. **Failure path** — `_failed_group_manifest._record_failed_group(...)`
   [features_service/delta_one/cli/handlers/\_failed_group_manifest.py:46](../../features-service/features_service/delta_one/cli/handlers/_failed_group_manifest.py#L46)
   → `config.get_output_bucket(asset_group)` → `common.resolve_bucket(kind="features-delta-one", ...)` →
   `resolve_bucket_name(...)` straight to yaml SSOT, **never reads `PROTOCOL_DATA_SINK_BUCKET_*`** ✗

Reproduced 2026-06-01 with the post-MDPS-fix CeFi smoke:

```bash
PROTOCOL_DATA_SOURCE_BUCKET_CEFI=market-data-tick-cefi-test-central-element-323112 \
PROTOCOL_DATA_SINK_BUCKET_CEFI=features-delta-one-cefi-test-central-element-323112 \
GCP_PROJECT_ID=central-element-323112 \
features-service --feature-family delta_one --operation compute --mode batch \
  --asset-group CEFI --start-date 2026-04-22 --end-date 2026-04-22 \
  --feature-group technical_indicators --timeframe 1h \
  --instruments "BINANCE-FUTURES:PERPETUAL:BTCUSDT" --max-workers 1
```

Log evidence:

```
ManifestWriter: updated availability index (14 total entries, 2 new) in features-delta-one-cefi-test-central-element-323112   ← success path, honours SINK
ManifestWriter: updated availability index (3 total entries, 1 new) in features-delta-one-cefi-central-element-323112        ← failure path, IGNORES SINK
Recorded record_failed manifest row for CEFI/technical_indicators on 2026-04-22 (error=orchestrator_returned_false)
```

## Why it matters

Every test/smoke/dev features-service run **pollutes the canonical features-delta-one bucket** with `record_failed` rows
whenever any feature group hits the orchestrator-returned-false path (which happens routinely on small/short smoke
ranges due to the 50-candle minimum for technical*indicators). This breaks the test/prod bucket isolation contract that
`PROTOCOL_DATA_SINK_BUCKET*\*` is designed to enforce.

Downstream consequences:

- Manifest consolidator + data-status endpoints reading the canonical features bucket pick up TEST data
- Strategy / paper-trade / `_index/availability_index.parquet` consumers see phantom `attempted_failed` rows for
  instruments/dates that were never actually touched in prod
- Smoke runs cannot be cleanly distinguished from prod runs in the canonical bucket
- Operator-level cleanup needed after every smoke (I had to delete 1 polluting row after the 2026-06-01 smoke)

The success path got the fix already (commit history references `_get_sink_bucket` introduction with rationale "Without
this, an unset PROTOCOL_DATA_SINK_BUCKET made get_data_sink return a StorageDataSink with an empty bucket"). The failure
path was missed in that same pass.

## Recommended decision

Update `features_service.delta_one.config.get_output_bucket(asset_group)` to mirror `_get_sink_bucket`:

```python
def get_output_bucket(self, asset_group: str) -> str:
    """Get output GCS bucket (delta-one features) for the given asset group."""
    # 1. UCI get_data_sink — honours PROTOCOL_DATA_SINK_BUCKET_{AG}
    from unified_trading_library import StorageDataSink, get_data_sink
    sink = get_data_sink(routing_key=asset_group.lower())
    if isinstance(sink, StorageDataSink) and sink._bucket:
        return sink._bucket
    # 2. Bucket-name SSOT fallback
    return resolve_bucket(kind="features-delta-one", asset_group=asset_group.lower())
```

This makes BOTH success and failure paths honour the same env override + same yaml SSOT fallback. The change is ~10 LOC
in [features_service/delta_one/config.py:162-164](../../features-service/features_service/delta_one/config.py#L162-L164)
and removes the bucket-split bug for the failure path.

Also propagates to the analogous `get_instruments_store_bucket` + `get_input_bucket` callers in the same file — they
likely have the same drift but I didn't reproduce for those (the SINK env exists for input only as
`PROTOCOL_DATA_SOURCE_BUCKET_*` so the routing-key trick maps to `get_data_source` instead of `get_data_sink`).

**Out of scope for today** — another agent is actively touching features-service files (CLAUDE.md "Two teammates ×
multiple parallel agents" rule), so I did not patch this. Filed for the next agent to land tomorrow. Estimated effort:
30 min (config.py + targeted unit test asserting PROTOCOL_DATA_SINK_BUCKET_CEFI override is honoured by the failure
path).

## Related

- Bucket-name SSOT HARD RULE: [unified-trading-pm/cursor-configs/CLAUDE.md] §"Bucket-name SSOT"
- Successor for env-tier provisioning: `plans/active/bucket_env_split_rollout_2026_06.md`
- Workspace audit: [unified-trading-system-repos/.claude/rules/python-backend.md] §"Cloud & Config"

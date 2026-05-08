---
scope: [engineer, ml-engineer, admin]
status: stable
last_reviewed: 2026-05-08
---

# features-service architecture

## TL;DR

Eight previously-separate `features-*-service` repos consolidated into a single workspace repo
[`features-service`](../../../features-service/) with one sub-package per family. ONE Docker image, ONE
[`pyproject.toml`](../../../features-service/pyproject.toml), ONE Health-API aggregator, ONE CLI dispatcher
parameterised by `--feature-family`. Subtree-merged with full per-repo history preserved per family. The eight
predecessor repos are archived; new code lands in `features-service` only.

This consolidation is a pre-requisite for
[`live_pipeline_mtds_mdps_features_2026_05_08`](../../plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md) — the
live-pipeline topology assumes a single Docker image deployed in two flavors (asset-scoped colocated with MDPS;
cross-cutting standalone). Maintaining that topology against 8 separate image build + deploy pipelines is operationally
infeasible against the 2026-05-23 cutover.

## The 8 families

The consolidated package layout (every family is a sub-package of `features_service`):

```
features-service/
├── features_service/
│   ├── __init__.py
│   ├── __main__.py                     # python -m features_service entry-point
│   ├── cli/main.py                     # dispatcher: parses --feature-family, forwards rest
│   ├── api/main.py                     # Health-API aggregator (per-family freshness)
│   ├── common/                         # cross-family lifts (Phase 5 helpers from UTL)
│   ├── calendar/                       # Family 1 — calendar / time-of-day features
│   ├── commodity/                      # Family 2 — commodity-specific features
│   ├── cross_instrument/               # Family 3 — cross-asset / cross-venue features
│   ├── delta_one/                      # Family 4 — delta-one / linear-exposure features
│   ├── multi_timeframe/                # Family 5 — multi-timeframe rollups
│   ├── onchain/                        # Family 6 — DeFi onchain features
│   ├── sports/                         # Family 7 — sports features (largest by surface)
│   └── volatility/                     # Family 8 — realized + implied vol features
├── pyproject.toml                      # ONE flat dependency list (no optional groups)
├── Dockerfile                          # ONE image
└── tests/
```

Each family `__init__.py` exports a `run(argv: list[str]) -> int` shim. The top-level dispatcher
[`features_service/cli/main.py`](../../../features-service/features_service/cli/main.py) parses `--feature-family`
and forwards the remaining argv to the matching family `run()`. No per-family entry-point script in `scripts/` —
the `python -m features_service --feature-family <family> ...` form is the single canonical invocation.

## CLI dispatch contract

Every CLI invocation uses the workspace-standard axes plus `--feature-family`:

```bash
python -m features_service \
  --feature-family <onchain|volatility|cross_instrument|sports|calendar|commodity|delta_one|multi_timeframe> \
  --operation <calculate|backfill|...> \
  --mode <batch|live> \
  --asset-group <CEFI|DEFI|TRADFI|SPORTS|PREDICTION> \
  [--shard-key '...'] \
  [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] \
  [--feature-group <name>]
```

`--feature-family` is mandatory and is validated against the UAC `FeatureFamily` enum (8 members). The dispatcher
enumerates the closed set in its help string; an unknown family raises a CLI-level error before any sub-package
is imported.

CLI convention SSOT: [`../06-coding-standards/cli-convention.md`](../06-coding-standards/cli-convention.md).

## Health-API aggregator contract

The top-level [`features_service/api/main.py`](../../../features-service/features_service/api/main.py) is the
single Health-API entry-point. It walks the 8 family sub-packages at import time, resolves each family's
`_data_freshness` callback via `importlib.util.find_spec`, and aggregates the responses behind a single `/health`
route.

Aggregate contract:

- Per-family freshness probes run independently. Any single-family raise is caught + recorded with the family
  name + exception message.
- Aggregate `healthy` flips False if **any** family raises (fail-loud). Per-family detail is in the response body
  so operators see which family is degraded without consulting per-family logs.
- The aggregator inherits the rest of the Health-API contract from
  [`make_health_router`](../../../unified-trading-library/src/unified_trading_library/health/) (UTL).
  Reference shape: [`features-svc@726af91d`](../../../features-service/) (Phase 4.4 / 4.5 commit; the aggregator
  was the Phase 4.5 deliverable).

QG enforcement: workspace base-service.sh STEP 5.62 asserts `make_health_router` appears in `api/main.py`. The
aggregator pattern satisfies that gate.

## UAC `feature_family` enum + manifest column

Phase 1A landed in
[`unified-api-contracts`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/feature_family.py):

- `FeatureFamily` — `StrEnum` with 8 members matching the sub-package names.
- `FEATURE_GROUP_TO_FAMILY` — registry mapping each of the 83 known feature_groups to its family. `feature_group`
  is the fine axis (e.g. `lst_yields`, `realized_vol_60m`, `lineups_pre_match`); `feature_family` is the coarse
  axis (`onchain`, `volatility`, `sports`).
- The v5 availability manifest gains a `feature_family` column (Phase 1B);
  [`ManifestWriter.record_captured`](../../../unified-trading-library/src/unified_trading_library/manifest/) now
  accepts the column as a kwarg + populates it automatically when called from a features-service writer.

Drilldown surface: see
[`../02-data/data-status-drilldown.md`](../02-data/data-status-drilldown.md) § "Per-asset_group depth table" —
`feature_family` is the top-level shard axis above `feature_group` for every features-service shard.

## UTL helpers shared across families (Phase 5 lifts)

Seven cross-family helpers identified by Phase 0 audit as duplicated boilerplate, lifted into UTL so families
inherit the canonical implementation:

| Helper                          | Purpose                                                                                  | Status (2026-05-08)                  |
| ------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------ |
| `LookaheadBiasError`            | Strict-mode raise when `input.available_at > target_ts - horizon`                        | Lifted; 6-of-8 family adoption pending in `ml_and_features_master` Phase 2A/2B |
| `WatermarkAlignmentFanin`       | Multi-source watermark alignment for live fan-in                                         | Greenfield in UTL                    |
| `BaseFeatureCalculator`         | Per-family abstract calculator base (lifecycle + write-gate + lookahead guard)           | Lifted from per-family duplicates    |
| `BroadcastSink`                 | Live-mode publish helper (Redis Streams + GCS dual-write)                                | Lifted                               |
| `LiveDataSource`                | Live-mode input adapter (subscribe + watermark)                                          | Lifted                               |
| `BuilderEntry`                  | Family registry entry shape (CLI dispatch + Health-API contract surface)                 | Lifted                               |
| `FeatureBatchHandler` base      | Batch-mode handler base (CLI → calculator → manifest write-gate)                         | Lifted                               |

Some lifts ship in the same logical unit as Phase 5; others ride alongside Phase 6 / Phase 7 (per-family inline
removal in same commit as the UTL lift, per the workspace "no double SSOT" rule). Phase 5 todo list owns the
authoritative status table.

### Canonical `ModeHandler` ABC (lifted 2026-05-08, UTL@abeb5bc3)

Per-family CLI mode handlers (batch / live / target) inherit a single `ModeHandler` ABC at
`unified_trading_library.feature_service_base.ModeHandler` (file `mode_handler.py`).

**Why lifted.** Pre-2026-05-08, the 4 families `volatility / delta_one / onchain / sports` each shipped a structurally-
identical local `ModeHandler` ABC at `features_service/<family>/cli/handlers/base_handler.py`. Same `__init__` (logger
+ `_resources` list), same `cleanup()` (walk resources calling `close()`/`cleanup()` and clear), same
`_register_resource` / `_parse_date` helpers — only the typed `run()` signature differed per family (sports
`**kwargs: object`; volatility 11-arg async; delta_one 16-arg async; onchain 9-arg async). The Wave 3b
`FeatureBatchHandler` ABC didn't fit (per-shard 1-frame model vs the 16-arg async multi-feature_group orchestration
families actually run); option α from
[`plans/active/issues/feature_batch_handler_abc_zero_consumers_2026_05_08.md`](../../plans/active/issues/feature_batch_handler_abc_zero_consumers_2026_05_08.md)
captured the lift target.

**Canonical surface.** The lifted ABC accepts the **most permissive** run signature (`async def run(**kwargs: object)`)
so subclasses are free to declare their own typed params via override without distorting the base contract. Lifecycle
hooks (`__init__`, `cleanup`, `_register_resource`, `_parse_date`) are the SSOT. Cleanup uses dual-protocol
(`_Closeable` with `close()`, `_Cleanupable` with `cleanup()`) — adopted from delta_one's superset shape. Resource
cleanup errors route through UTL `classify_and_emit_error` with `_service_name` class var override (default
`features-service`) so the EnhancedError envelope tags correctly per family.

**Adoption status (2026-05-08):**

| Family             | Status                          | Pre-lift parent                                                              | Notes                                                                                        |
| ------------------ | ------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `volatility`       | UTL ModeHandler                 | local `features_service.volatility.cli.handlers.base_handler.ModeHandler`    | Migrated features-service@7335bbef; local copy deleted                                       |
| `delta_one`        | UTL ModeHandler                 | local `features_service.delta_one.cli.handlers.base_handler.ModeHandler`     | Migrated features-service@7335bbef; local copy deleted                                       |
| `onchain`          | UTL ModeHandler                 | local `features_service.onchain.cli.handlers.base_handler.ModeHandler`       | Migrated features-service@7335bbef; local copy deleted                                       |
| `sports`           | UTL ModeHandler                 | local `features_service.sports.cli.handlers.base_handler.ModeHandler`        | Migrated features-service@7335bbef; local copy deleted                                       |
| `commodity`        | bare `class BatchHandler:`      | none                                                                         | **Stays bare**: sync `run(start_date, end_date, commodity, dry_run)`; per-(commodity, day) shards; multi-factor compute with cross-factor coverage gating doesn't decompose to `enumerate_shards` + `compute_one_shard`. Adopting UTL ModeHandler would require either widening the ABC (distorting contract) or rewriting compute. Out of scope. |
| `cross_instrument` | bare `class BatchHandler:`      | none                                                                         | **Stays bare**: async `run()` does `_ingest_data → _process_features → _gate_and_write` over feature_groups, NOT a per-shard fan-out. No natural shard_key axis. Force-fit would distort. Out of scope. |
| `multi_timeframe`  | bare `class BatchHandler:`      | none                                                                         | **Stays bare**: 109 LOC compact compute; doesn't share lifecycle with the 4 ModeHandler families. Adoption would add ceremony with no shared logic to lift. Out of scope. |
| `calendar`         | UTL `service_cli.BaseModeHandler` | UTL `unified_trading_library.service_cli.BaseModeHandler` (different lineage)| **Stays separate**: ServiceCLI-driven `args`+`runtime` injection lineage; not unified with `feature_service_base.ModeHandler` because the contract surfaces differ (config-driven vs CLI-args-driven). Out of scope. |

The 3 bare-class families and `calendar` are documented design calls — the lift is **option α** for the 4 families with
genuinely-overlapping local ABCs, NOT a force-fit across all 8. If a future bare-class family grows to need shared
lifecycle, adoption is a small refactor (subclass + register resource + override `_service_name`); contract is open.

**Cleanup-error envelope.** Subclasses MUST override `_service_name: str = "features-<family>-service"` so resource-
cleanup failures surface in the right service tag in observability. Default falls back to `"features-service"` for
silent-bug-detection; production families always override.

**Composes with**: `BaseFeatureService` (live-stack lifecycle), `BaseFeatureCalculator` (compute logic), Health-API
aggregator contract (registers handler builder via `BuilderEntry`), CLI dispatch contract (`get_handler_for_mode` /
`get_handler_for_operation` per family).

## Deployment topology

ONE Docker image. Per-VM `--feature-family` flag selects which sub-package runs at boot. Two deployment flavors:

| Cluster                       | What runs there                                                                                          |
| ----------------------------- | -------------------------------------------------------------------------------------------------------- |
| **features-asset-scoped**     | One VM per `(asset_group, region)` — colocated with MDPS for that asset_group (live pipeline). Boots with `--feature-family <onchain\|volatility\|delta_one\|...>` per the asset_group's families. |
| **features-cross-cutting**    | Standalone VM(s) for cross-asset / cross-venue families (`cross_instrument`, `calendar`, `multi_timeframe`) that span asset_groups. |

Topology SSOT: [`../05-infrastructure/deployment-clusters-live-vs-batch.md`](../05-infrastructure/deployment-clusters-live-vs-batch.md).

Launcher SSOT: [`../05-infrastructure/launcher-script-ssot.md`](../05-infrastructure/launcher-script-ssot.md). The
prior 8 per-family launchers (`launch-features-onchain-vm.sh`, etc.) collapse to a single
`launch-features-vm.sh` parameterised by `--feature-family` + `--asset-group`. Phase 8A finalises the launcher
shape.

## Live = batch

Same code, same calculators, same CLI surface, same Docker image. Only `--mode batch|live` differs at the entry
point; the calculator core does not branch on mode. The live-mode pipeline (Redis Streams `CANDLE_COMPUTED`
cascade + watermark fan-in) is wired by the lifted `BroadcastSink` + `LiveDataSource` helpers — not duplicated
per family.

Reference: [`batch-live-architecture.md`](batch-live-architecture.md) (single SSOT).

## Migration history

Eight predecessor repos archived (commit history preserved via `git subtree add` per family):

| Predecessor repo                       | Sub-package destination               |
| -------------------------------------- | ------------------------------------- |
| `features-onchain-service`             | `features_service/onchain/`           |
| `features-volatility-service`          | `features_service/volatility/`        |
| `features-cross-instrument-service`    | `features_service/cross_instrument/`  |
| `features-sports-service`              | `features_service/sports/`            |
| `features-calendar-service`            | `features_service/calendar/`          |
| `features-commodity-service`           | `features_service/commodity/`         |
| `features-delta-one-service`           | `features_service/delta_one/`         |
| `features-multi-timeframe-service`     | `features_service/multi_timeframe/`   |

Plan: [`../../plans/active/features_repo_consolidation_2026_05_08.md`](../../plans/active/features_repo_consolidation_2026_05_08.md)
(see DONE-2026-05-08 table for per-family subtree-merge SHAs + Phase 7 archival status).

## Anti-patterns

| Anti-pattern                                                  | Why banned                                                                                  |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Per-family Docker images                                      | Doubles deploy-flow surface; deprecated 2026-05-08 — ONE image, parameterised by flag.      |
| Per-family `pyproject.toml`                                   | Doubles dep resolution + version drift; ONE flat list in `features-service/pyproject.toml`. |
| `from features_<X>_service import ...` in any consumer        | Old per-repo import path; rewrite to `from features_service.<X> import ...`.                |
| Duplicate `LookaheadBiasError` / `BaseCalculator` per family  | Use UTL lifts (Phase 5). Per-family inlines deleted in same commit as the UTL lift.         |
| Manual `/health` route in any family                          | Use the top-level aggregator. Family declares `_data_freshness` callback only.              |
| Family code that branches on `--mode batch|live` for logic    | Live = batch. Mode switching is at the I/O seam (BroadcastSink vs ManifestWriter).          |
| New family without `feature_family` UAC enum + registry entry | Add to `FeatureFamily` + `FEATURE_GROUP_TO_FAMILY` first; sub-package is downstream of the schema. |

## Cross-references

- Feature-service calculator pattern (`BaseFeatureServiceV2` + `FeatureServiceMetrics` + Health-API):
  [`../06-coding-standards/feature-service-pattern.md`](../06-coding-standards/feature-service-pattern.md)
- CLI convention (`--feature-family` flag): [`../06-coding-standards/cli-convention.md`](../06-coding-standards/cli-convention.md)
- Data-status drilldown (feature_family axis):
  [`../02-data/data-status-drilldown.md`](../02-data/data-status-drilldown.md) § "Per-asset_group depth table"
- Manifest schema + write-gate:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- Launcher SSOT: [`../05-infrastructure/launcher-script-ssot.md`](../05-infrastructure/launcher-script-ssot.md)
- VM tarball deployment: [`../05-infrastructure/vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md)
- Live = batch: [`batch-live-architecture.md`](batch-live-architecture.md) (single SSOT)
- Live pipeline architecture: [`live-pipeline-architecture.md`](live-pipeline-architecture.md)
- ML lifecycle (downstream of features): [`ml-experiment-lifecycle.md`](ml-experiment-lifecycle.md)
- Plan-of-record:
  [`../../plans/active/features_repo_consolidation_2026_05_08.md`](../../plans/active/features_repo_consolidation_2026_05_08.md)

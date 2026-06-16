---
scope: [engineer, admin]
status: stable
last_reviewed: 2026-05-18
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
[`features_service/cli/main.py`](../../../features-service/features_service/cli/main.py) parses `--feature-family` and
forwards the remaining argv to the matching family `run()`. No per-family entry-point script in `scripts/` — the
`python -m features_service --feature-family <family> ...` form is the single canonical invocation.

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
enumerates the closed set in its help string; an unknown family raises a CLI-level error before any sub-package is
imported.

CLI convention SSOT: [`../06-coding-standards/cli-convention.md`](../06-coding-standards/cli-convention.md).

## Health-API aggregator contract

The top-level [`features_service/api/main.py`](../../../features-service/features_service/api/main.py) is the single
Health-API entry-point. It walks the 8 family sub-packages at import time, resolves each family's `_data_freshness`
callback via `importlib.util.find_spec`, and aggregates the responses behind a single `/health` route.

Aggregate contract:

- Per-family freshness probes run independently. Any single-family raise is caught + recorded with the family name +
  exception message.
- Aggregate `healthy` flips False if **any** family raises (fail-loud). Per-family detail is in the response body so
  operators see which family is degraded without consulting per-family logs.
- The aggregator inherits the rest of the Health-API contract from
  [`make_health_router`](../../../unified-trading-library/src/unified_trading_library/health/) (UTL). Reference shape:
  [`features-svc@726af91d`](../../../features-service/) (Phase 4.4 / 4.5 commit; the aggregator was the Phase 4.5
  deliverable).

QG enforcement: workspace base-service.sh STEP 5.62 asserts `make_health_router` appears in `api/main.py`. The
aggregator pattern satisfies that gate.

## UAC `feature_family` enum + manifest column

Phase 1A landed in
[`unified-api-contracts`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/feature_family.py):

- `FeatureFamily` — `StrEnum` with 8 members matching the sub-package names.
- `FEATURE_GROUP_TO_FAMILY` — registry mapping each of the 83 known feature_groups to its family. `feature_group` is the
  fine axis (e.g. `lst_yields`, `realized_vol_60m`, `lineups_pre_match`); `feature_family` is the coarse axis
  (`onchain`, `volatility`, `sports`).
- The v5 availability manifest gains a `feature_family` column (Phase 1B);
  [`ManifestWriter.record_captured`](../../../unified-trading-library/src/unified_trading_library/manifest/) now accepts
  the column as a kwarg + populates it automatically when called from a features-service writer.

Drilldown surface: see [`../02-data/data-status-drilldown.md`](../02-data/data-status-drilldown.md) § "Per-asset_group
depth table" — `feature_family` is the top-level shard axis above `feature_group` for every features-service shard.

## UTL helpers shared across families (Phase 5 lifts)

Seven cross-family helpers identified by Phase 0 audit as duplicated boilerplate, lifted into UTL so families inherit
the canonical implementation:

| Helper                     | Purpose                                                                        | Status (2026-05-08)                                                                                                                                                                                                                                                                                                                                                                                              |
| -------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LookaheadBiasError`       | Strict-mode raise when `input.available_at > target_ts - horizon`              | Lifted to UTL. Per-service wire-in approach superseded by repo consolidation: the helper goes ONCE into UTL `feature_service_base/` at the consolidated layer (per `features_and_ml_master` Q1 resolution — operator picked deferral until repo consolidation ships). Per-service adoption in features-\* DEFERRED pending writegate Phase 2.D adapter-side stamping + sports vocabulary alignment (Phase 1A.3). |
| `WatermarkAlignmentFanin`  | Multi-source watermark alignment for live fan-in                               | Greenfield in UTL                                                                                                                                                                                                                                                                                                                                                                                                |
| `BaseFeatureCalculator`    | Per-family abstract calculator base (lifecycle + write-gate + lookahead guard) | Lifted from per-family duplicates; **mandatory-validation `__init_subclass__` flip landed 2026-05-16 (UTL@ccc9b7bf, 48 calcs migrated)** — see § "Canonical BaseFeatureCalculator contract" below                                                                                                                                                                                                                |
| `BroadcastSink`            | Live-mode publish helper (Redis Streams + GCS dual-write)                      | Lifted                                                                                                                                                                                                                                                                                                                                                                                                           |
| `LiveDataSource`           | Live-mode input adapter (subscribe + watermark)                                | Lifted                                                                                                                                                                                                                                                                                                                                                                                                           |
| `BuilderEntry`             | Family registry entry shape (CLI dispatch + Health-API contract surface)       | Lifted                                                                                                                                                                                                                                                                                                                                                                                                           |
| `FeatureBatchHandler` base | Batch-mode handler base (CLI → calculator → manifest write-gate)               | Lifted                                                                                                                                                                                                                                                                                                                                                                                                           |

Some lifts ship in the same logical unit as Phase 5; others ride alongside Phase 6 / Phase 7 (per-family inline removal
in same commit as the UTL lift, per the workspace "no double SSOT" rule). Phase 5 todo list owns the authoritative
status table.

### Canonical `ModeHandler` ABC (lifted 2026-05-08, UTL@abeb5bc3; convenience wrappers added 2026-05-18, UTL@e74427d1)

Per-family CLI mode handlers (batch / live / target) inherit a single `ModeHandler` ABC at
`unified_trading_library.feature_service_base.ModeHandler` (file `mode_handler.py`).

**Convenience wrappers** (added 2026-05-18): `ModeHandler` now exposes `run_batch(**kwargs) -> bool` and
`run_live(**kwargs) -> bool` as concrete helpers that delegate to `run(mode="batch", **kwargs)` /
`run(mode="live", **kwargs)`. Callers that always operate in one mode can use these instead of passing `mode=`
explicitly.

**Why lifted.** Pre-2026-05-08, the 4 families `volatility / delta_one / onchain / sports` each shipped a structurally-
identical local `ModeHandler` ABC at `features_service/<family>/cli/handlers/base_handler.py`. Same `__init__` (logger

- `_resources` list), same `cleanup()` (walk resources calling `close()`/`cleanup()` and clear), same
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

**Adoption status (2026-05-19, all 8 families on UTL ModeHandler):**

| Family             | Status          | Pre-lift parent                                                               | Notes                                                                                                                                                   |
| ------------------ | --------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `volatility`       | UTL ModeHandler | local `features_service.volatility.cli.handlers.base_handler.ModeHandler`     | Migrated features-service@7335bbef; local copy deleted                                                                                                  |
| `delta_one`        | UTL ModeHandler | local `features_service.delta_one.cli.handlers.base_handler.ModeHandler`      | Migrated features-service@7335bbef; local copy deleted                                                                                                  |
| `onchain`          | UTL ModeHandler | local `features_service.onchain.cli.handlers.base_handler.ModeHandler`        | Migrated features-service@7335bbef; local copy deleted                                                                                                  |
| `sports`           | UTL ModeHandler | local `features_service.sports.cli.handlers.base_handler.ModeHandler`         | Migrated features-service@7335bbef; local copy deleted                                                                                                  |
| `commodity`        | UTL ModeHandler | bare `class BatchHandler:` (no parent)                                        | Tab 4 lift features-service@954fe85c — `BatchHandler(ModeHandler)` with `_service_name = "features-commodity-service"`; QG green @519625f7              |
| `cross_instrument` | UTL ModeHandler | bare `class BatchHandler:` (no parent)                                        | Tab 4 lift features-service@954fe85c — `BatchHandler(ModeHandler)` with `_service_name = "features-cross-instrument-service"`; QG green @519625f7       |
| `multi_timeframe`  | UTL ModeHandler | bare `class BatchHandler:` (no parent)                                        | Tab 4 lift features-service@954fe85c — `BatchHandler(ModeHandler)` + `InfoHandler(ModeHandler)`; QG green @519625f7                                     |
| `calendar`         | UTL ModeHandler | UTL `unified_trading_library.service_cli.BaseModeHandler` (pre-consolidation) | `CalendarBatchModeHandler(BaseModeHandler)` — already wired at consolidation (features-service@82abe801); Tab 4 confirmed alignment; QG green @519625f7 |

All 8 families are now on UTL ModeHandler. The previous "bare class" and "stays separate" design notes are superseded by
Tab 4 (batch_live_symmetry_2026_05_10.md). If a future bare-class family is added, adoption follows the same pattern:
subclass `ModeHandler`, set `_service_name`, override `enumerate_shards` + `compute_one_shard`.

**Cleanup-error envelope.** Subclasses MUST override `_service_name: str = "features-<family>-service"` so resource-
cleanup failures surface in the right service tag in observability. Default falls back to `"features-service"` for
silent-bug-detection; production families always override.

**Composes with**: `BaseFeatureService` (live-stack lifecycle), `BaseFeatureCalculator` (compute logic), Health-API
aggregator contract (registers handler builder via `BuilderEntry`), CLI dispatch contract (`get_handler_for_mode` /
`get_handler_for_operation` per family).

### Canonical `BaseFeatureCalculator` contract (mandatory-validation flip 2026-05-16)

Every concrete feature calculator subclasses
`unified_trading_library.feature_calculator.registry.BaseFeatureCalculator[DataFrameT]` (either directly or via a
per-family intermediate). The canonical ABC is generic over `DataFrameT` constrained to `pd.DataFrame` or `pl.DataFrame`
(PEP-696 default `pd.DataFrame` keeps the pre-Generic pandas contract working unchanged).

**Mandatory class-attribute contract** (enforced at class-definition time by `__init_subclass__` per
`basefc_validation_flip_2026_05_10.md` item 3, flipped 2026-05-16 at `unified-trading-library@ccc9b7bf`):

```python
class MyCalculator(BaseFeatureCalculator[pl.DataFrame]):
    feature_group: ClassVar[str] = "my_feature_group"   # MANDATORY — manifest row-key axis
    feature_family: ClassVar[str] = "my_family"         # MANDATORY — parquet partition + dispatcher routing

    def calculate(self, df: pl.DataFrame, **params: object) -> pl.DataFrame: ...
```

A missing or empty `feature_group` / `feature_family` raises `TypeError` at class-definition time. Abstract subclasses
(still have outstanding `@abstractmethod`) are exempt — they're scaffolding by design. Detection uses an eager MRO walk
in `_has_outstanding_abstract_methods()` because ABCMeta computes `__abstractmethods__` AFTER `__init_subclass__` runs.

**Per-family inheritance shape** (post-migration 2026-05-16):

| Family                        | Local base inherits                                                             | `feature_family` set on           | Status                                           |
| ----------------------------- | ------------------------------------------------------------------------------- | --------------------------------- | ------------------------------------------------ |
| cross_instrument              | `BaseFeatureCalculator[pl.DataFrame]` (UTL canonical)                           | local base (`"cross_instrument"`) | 20/20 calcs migrated `features-service@71643dec` |
| onchain                       | `BaseFeatureCalculator` (UTL canonical, pandas default) via `OnChainCalculator` | `OnChainCalculator` (`"onchain"`) | 19/19 calcs migrated `features-service@151dffab` |
| multi_timeframe               | `BaseFeatureCalculator[pl.DataFrame]` (UTL canonical, lifted 2026-05-16)        | local base (`"multi_timeframe"`)  | 9/9 calcs migrated `features-service@87ba9cf6`   |
| delta_one                     | `BaseFeatureCalculator[pl.DataFrame]` (legacy paradigm)                         | per-calc                          | legacy paradigm — opt-in validate                |
| volatility                    | local pandas `FeatureCalculator(BaseFeatureCalculator, ABC)`                    | per-calc                          | legacy paradigm — opt-in validate                |
| sports / commodity / calendar | local family ABCs                                                               | per-calc                          | legacy paradigms — opt-in validate               |

48 concrete calcs across the 3 polars families now declare `feature_group: ClassVar[str]` (vs the prior
`@property @override def feature_group(self) -> str:` pattern, which incidentally still typechecks because the property
descriptor is truthy at class-level — legacy paradigms remain on opt-in until their own follow-on flip).

**Why this matters.** The manifest writer keys rows by `feature_group`; the GCS path partitions by `feature_family`.
Class-attribute declaration lets static tooling (basedpyright, registry inspectors, documentation generators) read the
values without instantiating the calculator — a pre-condition for the deployment-UI data-status drilldown's
per-`(feature_family, feature_group)` rollup.

## Deployment topology

ONE Docker image. Per-VM `--feature-family` flag selects which sub-package runs at boot. Two deployment flavors:

| Cluster                    | What runs there                                                                                                                                                                                    |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **features-asset-scoped**  | One VM per `(asset_group, region)` — colocated with MDPS for that asset_group (live pipeline). Boots with `--feature-family <onchain\|volatility\|delta_one\|...>` per the asset_group's families. |
| **features-cross-cutting** | Standalone VM(s) for cross-asset / cross-venue families (`cross_instrument`, `calendar`, `multi_timeframe`) that span asset_groups.                                                                |

Topology SSOT:
[`../05-infrastructure/deployment-clusters-live-vs-batch.md`](../05-infrastructure/deployment-clusters-live-vs-batch.md).

Launcher SSOT: [`../05-infrastructure/launcher-script-ssot.md`](../05-infrastructure/launcher-script-ssot.md). The prior
8 per-family launchers (`launch-features-onchain-vm.sh`, etc.) collapse to a single `launch-features-vm.sh`
parameterised by `--feature-family` + `--asset-group`. Phase 8A finalises the launcher shape.

## Live = batch

Same code, same calculators, same CLI surface, same Docker image. Only `--mode batch|live` differs at the entry point;
the calculator core does not branch on mode. The live-mode pipeline (Redis Streams `CANDLE_COMPUTED` cascade + watermark
fan-in) is wired by the lifted `BroadcastSink` + `LiveDataSource` helpers — not duplicated per family.

Reference: [`batch-live-architecture.md`](batch-live-architecture.md) (single SSOT).

### Live handler status per family (2026-05-14)

| Family             | `live_handler.py` shipped | Production deployment             | Notes                                                                         |
| ------------------ | ------------------------- | --------------------------------- | ----------------------------------------------------------------------------- |
| `volatility`       | ✅                        | ⏳ post-cutover                   | live pipeline Phase 7 gated                                                   |
| `delta_one`        | ✅                        | ⏳ post-cutover                   | live pipeline Phase 7 gated                                                   |
| `onchain`          | ✅                        | ⏳ post-cutover                   | live pipeline Phase 7 gated                                                   |
| `sports`           | ✅                        | ⏳ post-cutover                   | sports live-odds PubSub feed gated on Phase 7 + live-pipeline sports schedule |
| `calendar`         | ✅                        | ⏳ post-cutover                   | economic-events PubSub feed gated on Phase 7                                  |
| `commodity`        | ❌ (batch only)           | N/A — batch-only scope for May-23 | live mode not in scope                                                        |
| `cross_instrument` | ❌ (batch only)           | N/A — batch-only scope for May-23 | live mode not in scope                                                        |
| `multi_timeframe`  | ❌ (batch only)           | N/A — batch-only scope for May-23 | live mode not in scope                                                        |

**Sports live-handler gating**: `features_service/sports/cli/handlers/live_handler.py` is shipped but blocked on
live-pipeline-architecture Phase 7 (sports odds PubSub feed activation). Until Phase 7 completes, the sports live
handler is not deployed. Sports features continue to run from batch GCS reads.

**Calendar live-handler gating**: `features_service/calendar/cli/handlers/live_handler.py` is shipped but blocked on the
economic-events PubSub feed going live (Phase 7 scope). Pre-cutover, calendar features run batch.

### ModeHandler lift status — Tab 4 COMPLETE (2026-05-19)

Tab 4 (`batch_live_symmetry_2026_05_10.md`) shipped at features-service@954fe85c (QG green @519625f7). All 8 families
are now on UTL ModeHandler — the adoption table above (§ Canonical ModeHandler ABC) reflects the final state. No further
bare-class families remain. Bare-class compat-path hard-delete scheduled post-prod-deploy (Tab 4 item 7).

### Live streaming MVP — Phase 3 current state (2026-05-22)

> **[DELTA 2026-05-22]** **Current state:** Live streaming activation for the `carry_staked_basis` MVP archetype is
> in-flight under `plans/active/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` (status: active, P2
> under `features_and_ml_master`). The paper VM `strategy-paper-carry-staked-basis-*` ticks but emits zero instructions
> (`fills=0 PnL=$0.00`) because the preflight gate checks for funded feature groups that are not yet producing live
> data. Key blockers: (1) `AssetScopedFeaturesRunner` + `CandleComputedEvent` consumer per family not yet wired for DeFi
> onchain/Solana families; (2) `MatchingEngineExecutionProvider` AMM wrapper needed for Solana legs (`BookType.AMM`
> raises `NotImplementedError`). Sports / Predictions / TradFi feature streaming are out of DeFi cutover gate scope.
> **Planned delta:** `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` delivers: funding-rate APY
> adapters (Binance/Bybit/OKX/Drift/Raydium/Orca), LST native-rates compute runner, live pipeline wiring, and AMM
> execution provider. Gate: paper VM emits ≥1 instruction per tick for ≥7 consecutive days. **Target architecture:**
> features-service deploys per-family as `AssetScopedFeaturesRunner` colocated with MDPS; live feature stream wires
> through `BroadcastSink` (Redis Streams + GCS dual-write). `carry_staked_basis` consumes live DeFi onchain + Solana DEX
> features within the same pipeline. All other asset-groups stream batch; live streaming activates per-archetype
> post-cutover.

## Migration history

Eight predecessor repos archived (commit history preserved via `git subtree add` per family):

| Predecessor repo                             | Sub-package destination              |
| -------------------------------------------- | ------------------------------------ |
| `features-service (onchain family)`          | `features_service/onchain/`          |
| `features-service (volatility family)`       | `features_service/volatility/`       |
| `features-service (cross-instrument family)` | `features_service/cross_instrument/` |
| `features-service (sports family)`           | `features_service/sports/`           |
| `features-service (calendar family)`         | `features_service/calendar/`         |
| `features-service (commodity family)`        | `features_service/commodity/`        |
| `features-service (delta-one family)`        | `features_service/delta_one/`        |
| `features-service (multi-timeframe family)`  | `features_service/multi_timeframe/`  |

Plan:
[`../../plans/archive/features_repo_consolidation_2026_05_08.plan.md`](../../plans/archive/features_repo_consolidation_2026_05_08.plan.md)
(ARCHIVED 2026-05-21 — Phases 0-10 shipped; see DONE-2026-05-08 table for per-family subtree-merge SHAs + Phase 7
archival status).

## Anti-patterns

| Anti-pattern                                                  | Why banned                                                                                         |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Per-family Docker images                                      | Doubles deploy-flow surface; deprecated 2026-05-08 — ONE image, parameterised by flag.             |
| Per-family `pyproject.toml`                                   | Doubles dep resolution + version drift; ONE flat list in `features-service/pyproject.toml`.        |
| `from features_<X>_service import ...` in any consumer        | Old per-repo import path; rewrite to `from features_service.<X> import ...`.                       |
| Duplicate `LookaheadBiasError` / `BaseCalculator` per family  | Use UTL lifts (Phase 5). Per-family inlines deleted in same commit as the UTL lift.                |
| Manual `/health` route in any family                          | Use the top-level aggregator. Family declares `_data_freshness` callback only.                     |
| Family code that branches on `--mode batch                    | live` for logic                                                                                    | Live = batch. Mode switching is at the I/O seam (BroadcastSink vs ManifestWriter). |
| New family without `feature_family` UAC enum + registry entry | Add to `FeatureFamily` + `FEATURE_GROUP_TO_FAMILY` first; sub-package is downstream of the schema. |

## Cross-references

- Feature-service calculator pattern (`BaseFeatureServiceV2` + `FeatureServiceMetrics` + Health-API):
  [`../06-coding-standards/feature-service-pattern.md`](../06-coding-standards/feature-service-pattern.md)
- CLI convention (`--feature-family` flag):
  [`../06-coding-standards/cli-convention.md`](../06-coding-standards/cli-convention.md)
- Data-status drilldown (feature_family axis):
  [`../02-data/data-status-drilldown.md`](../02-data/data-status-drilldown.md) § "Per-asset_group depth table"
- Manifest schema + write-gate:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)
- Launcher SSOT: [`../05-infrastructure/launcher-script-ssot.md`](../05-infrastructure/launcher-script-ssot.md)
- VM tarball deployment:
  [`../05-infrastructure/vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md)
- Live = batch: [`batch-live-architecture.md`](batch-live-architecture.md) (single SSOT)
- Live pipeline architecture:
  [`../05-infrastructure/live-pipeline-architecture.md`](../05-infrastructure/live-pipeline-architecture.md)
- ML lifecycle (downstream of features): [`ml-experiment-lifecycle.md`](ml-experiment-lifecycle.md)
- Consolidation plan-of-record (ARCHIVED 2026-05-21):
  [`../../plans/archive/features_repo_consolidation_2026_05_08.plan.md`](../../plans/archive/features_repo_consolidation_2026_05_08.plan.md)
- Live streaming MVP plan (active, P2 under `features_and_ml_master`):
  [`../../plans/active/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md`](../../plans/active/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md)
- QG cleanup plan (Phase 1 complete, 0 test failures as of 2026-05-18):
  [`../../plans/active/features_service_qg_cleanup_2026_05_11.md`](../../plans/active/features_service_qg_cleanup_2026_05_11.md)

## Test-suite status (2026-05-18)

Phase 1.3 of `features_service_qg_cleanup_2026_05_11.md` resolved all pre-existing test failures:

- **7266 tests passing, 22 skipped, 0 failures** (features-service@`0e73bc90`)
- Key fixes: calendar `LookaheadBiasError` (candle-close window + as_of=next-midnight); delta_one polars→pandas
  conversion in `BaseFeatureCalculator`; onchain `log_event` patch target + batch-skip + LST methods; sports
  `steam_detector` `%%s` format strings; `asyncio.get_event_loop()→asyncio.run()` across commodity / MTF / volatility /
  cross_instrument; cross_instrument `event_logging` `Path.cwd()` resolution; `yfinance` import guard
  (`pytest.importorskip("lxml")`); codex-compliance `timedelta` module-level import.
- All 8 families run the full unit + integration suite under the per-family test layout (`PYTEST_UNIT_DIR="tests/"`) per
  `quality-gates.sh`.

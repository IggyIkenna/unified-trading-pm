---
doc_type: plan
title: instrument-catalogue-availability-matrix
summary: Single artefact (instrument-catalogue.json + shard-dynamics.json + instrument-catalogue.md) joining static shard-dynamics
  SSOT (bucket → partition layout → schema → coverage-start → retention/cutoff → live/batch capability) with live availability-manifest
  aggregation (capture_status counts → coverage %) per (asset_group × data_type × venue × instrument_type) tuple. Published
  nightly to GCS catalogue prefix; consumed by a new UI matrix widget that cross-links existing data-status drilldown.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, market-tick-data-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-29'
type: mixed
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-29
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: market-data-processing-service, code: C0, deployment: none, business: none}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none}
- {repo: deployment-service, code: C0, deployment: D0, business: none}
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
depends_on: [shard_dimension_naming_asset_group_ssot_2026_04_25, venue_axis_asset_group_vocabulary_2026_04_25]
todos:
- {id: p0-1-pm-active-plan, content: "- [x] [SCRIPT] P0. Create this PM active plan file at\n      `unified-trading-pm/plans/active/instrument_catalogue_availability_matrix_2026_04_29.md`,\n      mirroring the Claude plan at `~/.claude/plans/i-guess-we-can-jazzy-eagle.md`. Add link to\n      `plans/active/INDEX.md` under \"Cross-cutting SSOT\" section.\n", status: done}
- {id: p0-2-bucket-naming-ssot, content: "- [x] [SCRIPT] P0. Create `unified-api-contracts/unified_api_contracts/canonical/gcs_paths.py` +\n      facade `unified_api_contracts/gcs_paths.py` exporting:\n        - `BUCKET_TEMPLATES_BY_ASSET_GROUP_KIND: dict[(AssetGroup, BucketKind), str | None]` —\n          covering all 5 asset_groups × 2 kinds.\n          Wire-format SSOT verified against\n          `deployment-service/terraform/gcp/main.tf` lines 308-471:\n            - instruments: `instruments-store-{ag_lower}-{pid}` (TRADFI = None).\n            - market_data: `market-data-tick-{ag_lower}-{pid}`.\n        - `bucket_name(asset_group, project_id, kind=\"instruments\", test_mode=False)` immediate resolver.\n        - `bucket_template(asset_group, kind=\"instruments\", test_mode=False)` lazy-template resolver\n          (keeps `{project_id}` placeholder for callers like MDPS dependency_checker that resolve\n          at lookup time).\n        - `strategy_store_bucket(project_id)` for catalogue\
    \ artefacts (single bucket regardless of ag).\n        - `sports_bucket_name` parity wrapper.\n      Update consumers (1 of 2 done — see follow-up below):\n        - `unified-api-contracts/scripts/enumerate_strategy_instruments.py` lines 53-61 →\n          import from new module, drop the duplicated dict. **DONE 2026-04-29**.\n      Coverage: `tests/unit/test_gcs_paths_facade.py` — 7 cases including TRADFI-None\n      exception, test_mode suffix splice, lazy-template placeholder preservation.\n", status: done}
- {id: p0-2b-mdps-bucket-import-followup, content: "- [ ] [SCRIPT] P0.2 follow-up. Migrate `market-data-processing-service/.../app/core/dependency_checker.py`\n      to import from `unified_api_contracts.gcs_paths`. Three dict ClassVars to convert:\n        - `OUTPUT_BUCKETS` / `OUTPUT_BUCKETS_TEST` → derive via `bucket_template(ag, kind=MARKET_DATA, test_mode=...)`.\n        - `UPSTREAM_DEPS_BY_CATEGORY` / `UPSTREAM_DEPS_BY_CATEGORY_TEST` (sports/prediction overrides) →\n          same shape derivation.\n        - `UPSTREAM_DEPS` / `UPSTREAM_DEPS_TEST` use a generic `{asset_group_lower}` placeholder for\n          lazy-resolve by the BaseDependencyChecker framework — these stay literal strings (or UAC\n          exposes a generic-shape template helper if we want zero duplication; defer the API design).\n      Skipped from initial P0.2 because MDPS has ~20 unrelated in-flight files from concurrent agents\n      (live-defi-rollout, 2026-04-29) and isolate-commit hygiene was the priority.\n",
  status: todo}
- {id: p0-3-partition-layout-ssots, content: "- [x] [SCRIPT] P0. Per-asset-group partition layout SSOTs in UAC. Decision: rather than 4\n      new subpackages (`canonical/domain/{cefi,defi,tradfi,prediction}/gcs_paths.py`), put all\n      non-sports asset-group builders in a single `canonical/partition_paths.py` module —\n      sports keeps its existing domain-co-located SSOT (tied to fixture/league semantics).\n        - `build_defi_partition_path` moved from MTDS\n          `adapters/defi/canonical_write.py` to UAC. MTDS now re-exports for back-compat.\n          Wire format unchanged: `day={D}/asset_group=defi/venue={V}/chain={C}/\n instrument_type={IT}/data_type={DT}/{file}`.\n        - `build_cefi_partition_path` added. Wire format verified against MTDS\n          `cefi/tardis_shared.py::build_partition_path` v5 layout. v6 CHAIN-bundle extension\n          (`underlying`/`quote`/`margin` axes) parked as a follow-up.\n        - `build_tradfi_partition_path` added. Wire format\
    \ verified against MTDS\n          `tradfi/tradfi_shared.py`.\n        - `build_prediction_partition_path` added with `condition_id` axis. Marked VERIFY\n          in docstring — MTDS prediction adapters construct paths inline rather than via a\n          shared helper, so the wire format here is an SSOT proposal pending audit against\n          actual production writes.\n        - `candidate_parquet_paths(asset_group, data_type, day, **kwargs)` dispatcher\n          surfaces all 5 asset_groups (sports delegates to its domain module).\n        - Facade `unified_api_contracts.gcs_paths` re-exports everything.\n      Coverage: `tests/unit/test_partition_paths.py` — 11 cases. Existing MTDS DeFi test suite\n      (17 cases) re-runs green against the UAC re-export. **DONE 2026-04-29.**\n", status: done}
- {id: p0-3-followup-cefi-v6-axes, content: "- [ ] [SCRIPT] P0.3 follow-up. Surface CeFi v6 CHAIN-bundle extension axes\n      (`underlying={U}/quote={Q}/margin={M}/` segments before `data_type`) in\n      `unified_api_contracts.canonical.partition_paths.build_cefi_partition_path`. The\n      v5 layout there today is correct for single-symbol shards. v6 segments are present\n      in MTDS `cefi/tardis_shared.py::build_partition_path` and require importing the\n      `CHAIN_INSTRUMENT_TYPES` / `SINGLE_INSTRUMENT_TYPES` validation logic from MTDS or\n      redeclaring it in UAC. Defer until catalogue generator (P1.1) actually needs to\n      probe v6 paths.\n", status: todo}
- {id: p0-3-followup-prediction-verify, content: "- [ ] [SCRIPT] P0.3 follow-up. Verify the Prediction wire format in\n      `unified_api_contracts.canonical.partition_paths.build_prediction_partition_path`\n      against the actual GCS writes by Polymarket / Kalshi / Manifold adapters. The shape\n      is currently SSOT-proposed but not adapter-confirmed. Either backfill verification\n      tests, or migrate the adapters to use the SSOT (preferred — matches the DeFi\n      pattern).\n", status: todo}
- {id: p0-4-coverage-start-registry, content: "- [x] [SCRIPT] P0. Generalise `canonical/domain/sports/league_data.py::SOURCE_COVERAGE_START` pattern\n      across asset groups. Per-asset-group `coverage_starts.py` with venue → first-data-date map.\n      Seed values to verify against prod manifest min(date) per venue:\n        - CeFi: Coinbase 2014-12-08, Kraken 2013-09-10, Binance 2017-08-17, OKX 2017-05-31,\n          Bybit 2018-11-21, Deribit 2016-06-13, Hyperliquid 2023-06-29, Bitfinex 2013-04-30.\n        - DeFi: Uniswap V2 2020-05-04, V3 2021-05-05, Aave V2 2020-12-01, V3 2022-03-16,\n          Curve 2020-01-19, Balancer 2021-05-13.\n        - TradFi: FRED DGS series 1962-01-02, OPRA 2003-01-13.\n        - Prediction: Polymarket 2020-06-12, Kalshi 2021-07-19, Manifold 2022-01-01.\n      Add `coverage_start(asset_group, source_key) -> date | None` lookup to UAC root facade.\n", status: todo}
- {id: p0-5-data-type-capability-registry, content: "- [x] [SCRIPT] P0. Create `unified-api-contracts/unified_api_contracts/registry/data_type_capability.py`\n      with `DataTypeCapability` dataclass:\n        ```\n asset_group: AssetGroup\n data_type: str\n venue: str\n instrument_type: str | None\n live_capable: bool # WS feed exists\n batch_capable: bool # REST / parquet snapshot exists\n streaming_protocol: str | None  # \"ws\" | \"fix\" | \"sse\" | None\n requires_credentials: bool\n ttm_cutoff_days: int | None # options: ignore expiries beyond this\n liquidity_cutoff_usd: float | None  # ignore instruments below this 24h volume\n retention_days: int | None # rolling-window cutoff\n notes: str | None\n ```\n      Populate from MTDS adapter capability properties + features-derivatives-service cutoff defs.\n      Each entry carries a `# source:` comment with the file\
    \ the row was sourced from.\n", status: todo}
- {id: p0-6-schema-spec-registry, content: "- [x] [SCRIPT] P0. Create `unified-api-contracts/unified_api_contracts/registry/schema_spec.py`\n      mapping `(asset_group, data_type) -> SchemaSpec` where `SchemaSpec = list[ColumnSpec]` and\n      `ColumnSpec = (name, dtype, nullable, unit, description)`.\n      Derive from existing UAC canonical models via reflection (Pydantic `model_fields`).\n      Hand-write where models are too dynamic. Sources:\n        - `CanonicalTicker`, `CanonicalTrade`, `CanonicalOrderBook`, `CanonicalFundingRate`,\n          `CanonicalLiquidation`, `CanonicalDerivativeTicker`, `CanonicalOraclePrice`,\n          `CanonicalStakingRate`.\n        - Sports: `Fixture`, `Event`, `Odds`, `ArbitrageRow`.\n        - Prediction: `Market`, `Outcome`.\n", status: todo}
- {id: p0-7-qg, content: "- [x] [SCRIPT] P0. Per-repo QG green:\n        - `cd unified-api-contracts && bash scripts/quality-gates.sh`.\n        - `cd market-tick-data-service && bash scripts/quality-gates.sh` (DeFi import shifted to UAC).\n        - `cd market-data-processing-service && bash scripts/quality-gates.sh`.\n", status: todo}
- {id: p1-1-generator-script, content: "- [x] [SCRIPT] P1. Create `unified-api-contracts/scripts/generate_instrument_catalogue.py`. For every\n      tuple in `DATA_TYPE_CAPABILITY_REGISTRY`:\n        - Read manifest via UTL `read_availability_index(bucket)` (120s freshness fallback baked in).\n        - Filter to (venue, data_type, instrument_type, ...) for that tuple.\n        - Compute expected denominator (generalised sports clip): `coverage_start(...)` to today,\n          clipping pre-launch dates.\n        - Compute coverage_pct = (captured + empty_confirmed) / expected_dates (honest-coverage).\n        - latest_captured = max(date) where capture_status == captured.\n        - live_ready = capability.live_capable AND latest_captured >= today - 1d.\n        - batch_ready = capability.batch_capable AND coverage_pct >= 0.9.\n        - retry_needed = any capture_status == attempted_failed.\n      Emit 3 outputs:\n        - `instrument-catalogue.json` — drilldown-friendly, keyed by canonical\
    \ tuple.\n        - `shard-dynamics.json` — pure static spec; deterministic from UAC (no manifest data).\n        - `instrument-catalogue.md` — human matrix grouped by asset_group → data_type → venue with\n          \U0001F7E2 ≥90% / \U0001F7E1 50–90% / \U0001F534 <50% / ⚪ no-data band emoji + live-ready / batch-ready badges.\n", status: todo}
- {id: p1-2-tests, content: "- [ ] [SCRIPT] P1. Create `unified-api-contracts/tests/test_instrument_catalogue_generator.py` with\n      3 manifest fixture cases:\n        - FULL coverage tuple (every expected day captured) → coverage_pct == 1.0; readiness bools\n          True if capability says so.\n        - PARTIAL tuple (mix of captured + empty_confirmed + attempted_failed) → coverage clipped\n          at expected denominator; retry_needed=True.\n        - All-attempted_failed tuple → coverage_pct == 0.0; both readiness bools False.\n", status: todo}
- {id: p1-3-wire-into-regen, content: "- [x] [SCRIPT] P1. Extend `unified-trading-pm/scripts/dev/regen-catalogue.sh` with a fourth step that\n      runs the new generator. Upload outputs to\n      `gs://strategy-store-cefi-{project_id}/catalogue/instrument/`\n      (reuses existing IAM + UI proxy auth path).\n", status: todo}
- {id: p2-1-cloud-scheduler, content: "- [x] [SCRIPT] P2. Add Cloud Scheduler nightly TF at\n      `deployment-service/terraform/gcp/instrument_catalogue_scheduler.tf`, mirroring\n      `manifest_consolidator_scheduler.tf`. Cadence: `0 2 * * *` (02:00 UTC). Job invokes the\n      generator as a Cloud Run Job.\n      IAM bindings:\n        - generator SA: `roles/storage.objectViewer` on every `instruments-store-{ag}-*` and\n          `market-tick-data-{ag}-*` bucket.\n        - generator SA: `roles/storage.objectCreator` on `strategy-store-cefi-*`.\n      Operator note: cron simpler; alternative is to extend `manifest-consolidator-daemon` to\n      regenerate every 60 minutes after the manifest pass. Default cron unless freshness <24h needed.\n", status: todo}
- {id: p3-1-ui-proxy-client, content: "- [x] [SCRIPT] P3. Add `unified-trading-system-ui/app/api/catalogue/instrument/route.ts`\n      mirroring existing `app/api/catalogue/envelope/route.ts` (5-min server cache, ADC).\n      Accepts `?file=instrument-catalogue.json|shard-dynamics.json|instrument-catalogue.md`.\n      Add `unified-trading-system-ui/lib/api/instrument-catalogue-client.ts` typed wrapper\n      exporting TS types matching the JSON envelope.\n", status: todo}
- {id: p3-2-matrix-widget, content: "- [x] [SCRIPT] P3. Add primitive `components/widgets/_primitives/coverage-matrix.tsx` extending the\n      existing FreshnessHeatmap pattern from\n      `components/ops/deployment/data-status/build-heatmap-data.ts` with coverage-band shading\n      + live-ready / batch-ready badges per cell.\n      Add widget `components/widgets/data-quality/instrument-catalogue-widget.tsx` consuming the\n      primitive + the API client. Register in:\n        - DART terminal default preset layout (no-orphan rule).\n        - Ops admin data-status page.\n      Cross-link existing FreshnessHeatmap onto the new matrix widget (drilldown).\n", status: todo}
- {id: p3-3-tests-smoke, content: "- [ ] [SCRIPT] P3. Vitest harness for the new widget: mock-mode renders all 5 asset_group rows;\n      coverage bands display correctly; live/batch badges render.\n      Mock fixtures in `lib/api/mock-handler.ts` for `/api/catalogue/instrument`.\n      Playwright: ops admin → data-status page → widget renders; click a tuple → drill-down to\n      existing data-status routes round-trips.\n", status: todo}
isProject: false
---

# Instrument Catalogue + Availability Matrix SSOT

## Why this change

The Unified Trading System has manifest infrastructure that knows what every VM has actually written
(`_index/availability_index.parquet` per asset_group bucket, daemon-refreshed every 60s, with `capture_status` ∈
`{captured, empty_confirmed, attempted_failed}`). It has a strategy catalogue (DART envelope.{md,json}) generated
nightly. What it does NOT have is a single artefact that joins **what the system can capture in principle** (static
shard-dynamics: bucket → partition layout → file grouping → schema columns → coverage-start dates → retention/cutoff
rules → live-vs-batch capability) with **what it has captured in practice** (manifest aggregation: % backfilled per
tuple).

The need surfaced asking "for any asset group × data type × venue, where is the data, what's its shape, how complete is
it, and is it live-ready?" — there is no human-readable matrix or AI-consumable JSON answering that.

## What ships

A catalogue artefact set published nightly to GCS:

- `instrument-catalogue.json` — keyed by
  `(asset_group, data_type, venue, instrument_type, [league_id|chain|condition_id])` tuple; per-tuple: bucket path,
  partition layout, schema column list, coverage %, captured-day-count, empty-confirmed-day-count,
  attempted-failed-day-count, latest-captured-day, live-ready bool, batch-ready bool, expected-denominator (clipped to
  `coverage_start`).
- `shard-dynamics.json` — pure static spec dump (no manifest data; deterministic from UAC). Useful for adapter authors +
  AI agents reasoning about layout without GCS access.
- `instrument-catalogue.md` — human matrix grouped by asset_group → data_type → venue with ≥90% / 50–90% / <50% colour
  bands and live-ready / batch-ready badges.

## Hard constraints

1. **Static spec lives in UAC** — not MTDS, not deployment-api scripts. Sports already does this
   (`canonical/domain/sports/gcs_paths.py` + `league_data.py::SOURCE_COVERAGE_START`); other asset groups mirror that
   pattern.
2. **Generator reuses existing manifest reader** (`read_availability_index` from UTL with 120s freshness fallback to
   per-VM shards). No new manifest infra.
3. **Refresh piggybacks on existing patterns** — Cloud Scheduler nightly mirroring DART catalogue regen TF. Operator may
   instead extend the manifest-consolidator daemon; cron is simpler default.
4. **Output published to existing strategy-store catalogue bucket** at
   `gs://strategy-store-cefi-{pid}/catalogue/instrument/` (reuses existing IAM + UI proxy auth).
5. **No orphans** — new UI widget registers in DART terminal preset layout AND ops admin data-status page; cross-links
   from existing `FreshnessHeatmap`.
6. **Sports + TradFi keying exception** — sports uses single-bucket-many-leagues; TradFi has no instruments bucket today
   (UAC universe registry). Generator handles per-asset-group keying differences explicitly.

## Audit summary (Phase 1 explores, 2026-04-29)

| Component                        | State today                                                                                                                         | Action                                         |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Bucket naming                    | Sports has UAC SSOT (`sports_bucket_name`); others duplicated in `enumerate_strategy_instruments.py` + MDPS `dependency_checker.py` | Centralise in UAC `canonical/gcs_paths.py`     |
| Partition layout                 | Sports SSOT; DeFi in MTDS (`canonical_write.py::build_defi_partition_path`); CeFi/TradFi/Prediction inline-hardcoded                | Per-asset-group `gcs_paths.py` modules in UAC  |
| Schema columns                   | UAC `canonical/domain/` Pydantic / dataclass models                                                                                 | New `registry/schema_spec.py` reflecting these |
| Coverage start dates             | Sports SSOT (`SOURCE_COVERAGE_START`); zero coverage for crypto / tradfi / prediction                                               | Per-asset-group `coverage_starts.py` modules   |
| Live-vs-batch capability         | Framework exists (`registry/capability.py::OperationDetail`), no `(data_type × venue)` matrix                                       | New `registry/data_type_capability.py`         |
| Manifest reader                  | Solid — `read_availability_index(bucket)` with 120s freshness fallback                                                              | Reuse as-is                                    |
| Manifest consolidator daemon     | Solid — Cloud Run Job at `*/1 * * * *` per bucket (10 buckets total)                                                                | Reuse as-is                                    |
| Strategy catalogue regen pattern | Solid — `regen-catalogue.sh` → 4 files → GCS → UI `/api/catalogue/envelope` proxy                                                   | Extend, don't fork                             |
| Data-status routes               | 4 routes in `deployment-api/.../routes/data_status.py`                                                                              | Cross-link from new widget; do not duplicate   |
| Coverage % computation           | Sports: `clip_dates_to_source_coverage` + `_sports_expected_dates_for_league`; non-sports: raw calendar                             | Generalise in generator                        |
| Existing UI heatmap              | `components/ops/deployment/data-status/build-heatmap-data.ts` (FreshnessHeatmap)                                                    | Cross-link drilldown                           |

## Execution DAG

```
P0 (UAC SSOT unification — SEQUENTIAL)
  └─> P1 (generator — depends on P0)
        ├─> P2 (refresh job)
        └─> P3 (UI consumer)
```

P0 is the lift; everything after is mechanical once the spec lands. P2 and P3 may run in parallel after P1.

## Verification

1. Per-repo QG green for: UAC, MTDS, MDPS, deployment-api, deployment-service, unified-trading-system-ui.
2. Generator deterministic on fixed manifest fixture; coverage % matches hand computation.
3. Tier-2 boot consumes real GCS catalogue; matrix renders; live/batch badges respect capability registry.
4. Spot-check known tuples: `(CEFI, klines, BINANCE, perpetual)` → 🟢 + live-ready + batch-ready;
   `(CEFI, exchange_flows, *)` → ⚪ + no badges.
5. No-orphan audit: widget appears in ≥1 preset layout + ≥1 ops route.
6. Workspace QG sweep across all touched repos before quickmerge.

## Critical files

- Manifest reader (120s freshness fallback): `unified-trading-library/unified_trading_library/manifest_reader.py`
  (`read_availability_index`).
- Manifest writer: `unified-trading-library/unified_trading_library/manifest_writer.py`.
- Manifest consolidator: `unified-trading-library/unified_trading_library/manifest_consolidator.py`.
- Sports SSOT (template): `unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py`
  - `league_data.py`.
- DeFi partition (to be moved to UAC): `market-tick-data-service/.../adapters/defi/canonical_write.py` lines 71-91.
- Existing capability framework: `unified-api-contracts/unified_api_contracts/registry/capability.py`.
- Strategy catalogue regen (extend): `unified-trading-pm/scripts/dev/regen-catalogue.sh`.
- Catalogue UI proxy (template): `unified-trading-system-ui/app/api/catalogue/envelope/route.ts`.
- FreshnessHeatmap (extend / cross-link):
  `unified-trading-system-ui/components/ops/deployment/data-status/build-heatmap-data.ts`.
- Data-status routes (cross-link): `deployment-api/deployment_api/routes/data_status.py`.
- Data-status drilldown service (`_sports_expected_dates_for_league`):
  `deployment-api/deployment_api/services/data_status_service.py` lines 272-299.

## Reused infrastructure (no net-new)

- Manifest writer / reader / consolidator (UTL).
- Manifest consolidator daemon VM (60s polling already running).
- Strategy-catalogue regen script + GCS upload pattern (PM).
- UI GCS proxy + 5-min cache pattern.
- FreshnessHeatmap component (extend, do not duplicate).
- DART `gs://strategy-store-cefi-{pid}/catalogue/` bucket + IAM (reuse with `instrument/` subprefix).
- `read_availability_index` 120s freshness fallback (per-VM shard merge).
- Sports `clip_dates_to_source_coverage` pattern (generalise).
- Existing data-status routes (cross-link from new widget; do not re-implement).

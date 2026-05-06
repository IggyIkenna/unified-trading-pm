---
title: "Instruments-service + market-tick-data + market-data-processing — full functionality across all asset groups"
priority: P0
status: active
owner: agent
created: 2026-05-01
type: epic
epic: data-pipeline-completion
completion_gates:
  code: C2
  deployment: D2
  business: B1
repo_gates:
  - repo: deployment-ui
    deployment: D1
  - repo: deployment-api
    deployment: D1
  - repo: instruments-service
    deployment: D2
  - repo: market-tick-data-service
    deployment: D2
  - repo: market-data-processing-service
    deployment: D2
  - repo: unified-api-contracts
    deployment: D1
depends_on: []
isProject: true
---

## Context

**Goal**: every asset group (sports, cefi, tradfi, defi, prediction) at 100% honest coverage for instruments-service +
market-tick-data-service + market-data-processing-service, verifiable via the deployment-ui data-status drilldown.

"Honest" means manifest `capture_status ∈ {captured, empty_confirmed}` with parquets actually present at the canonical
GCS paths, and the secondary cutoffs applied so legitimately-empty shards (pre-launch dates, non-prediction leagues for
rich features, etc.) don't render as missing.

**Operational SSOT**: `codex/14-playbooks/backfill-completion-playbook.md`.

**Background**: 2026-04-30 TradFi session shipped 14 commits resolving five pre-existing pipeline bugs (VM_VENUE
routing, parent-symbol format, force-flag threading, VM-name underscore validation, ETF dataset routing). Combo bundling
fix landed and ~13M legacy per-combo parquets were compacted via 5 year-sharded migration VMs. Operator memory:
`project_tradfi_backfill_session_2026_04_30.md`.

**Current state** (deployment-ui screenshot, 2026-05-01):

- Sports asset group at 79.9% captured / 100% attempted / 62% empty.
- Sub-60% data types: `FIXTURE_FEATURES` (0%), `MATCHES` (18%), `PLAYER_VALUES` (2%), `SFI_LEAGUES` (14%),
  `SFI_PROGRESSIVE_STATS` (15%), `TRANSFERMARKT_LEAGUES` (50%).

**In flight (separate agent, sports instruments-service)** — check status before launching new sports VMs:

- L2 GCS rename pass — 108,969 ops, ~25 ops/sec local network, ~60 min wall clock. Renames on-disk paths to match the
  canonical `league_id` already in the manifest (single SSOT — canonical IDs in both manifest and on disk).
- 4 backfill VMs running: `af` (api-football), `tm` (transfermarkt), `sfi` (soccer_football_info), `fs` (footystats).
  Per-league writes with canonical IDs via orchestrator helper `_canonical_league_id`. Bare-path fallback removed.
- Consolidator daemon merging `_index/per_vm/*.parquet` → canonical every ~60s.
- Headline trajectory: 74.43% → 83.10% (band-aid) → 75.49% (no fallback) → 79.97% (L1 rename) → expected ~80%+ post-L2 +
  post-backfills.
- Verification gate before Phase 1 starts: confirm those four VMs are no longer RUNNING and L2 rename is complete.

**Credentials policy**: all venue / data-source API keys live in GCP Secret Manager. `ApiKeyReloader` (UTL) fetches them
at runtime. No local `.env` files, no inline constants, no checked-in config paths. If a backfill fails with "missing
key", check the secret exists in `central-element-323112` first; ask Ikenna if it needs to be provisioned or rotated.

## Cutoffs (decisions baked into this plan)

**Global** (upper bound on history attempted):

| Asset group | Earliest day        | Source                                   |
| ----------- | ------------------- | ---------------------------------------- |
| Sports      | 2020-06-01          | First odds_api data                      |
| CeFi        | 2019-01-01          | Tardis archive depth                     |
| TradFi      | 2019-01-01          | Strategy horizon                         |
| Prediction  | per-venue launch    | `PREDICTION_SOURCE_COVERAGE_START` (UAC) |
| DeFi        | per-protocol launch | `DEFI_SOURCE_COVERAGE_START` (UAC)       |

**Secondary** (shard-level — is data even possible):

- **Sports**: prediction-leagues (33 leagues — `get_prediction_leagues()`) get every data type with rich features;
  reference-leagues (40 leagues) only get FIXTURES + FIXTURE*EVENTS + STANDINGS (basic api_football). No
  FIXTURE_FEATURES / PLAYER_VALUES / SFI*\* / understat for reference leagues.
- **TradFi**: per-ticker listing dates via `TRADFI_TICKER_COVERAGE_START` (UAC, shipped 2026-05-01 commit `15b9e74`).
- **CeFi**: per-venue + per-instrument inception (Binance Futures 2019-09 etc.).
- **DeFi**: per-protocol-per-chain inception.
- **Prediction**: per-sub-category inception within a venue.

## Execution DAG

```
Phase 0 (UI + adapter unblockers — sequential)
        │
        ▼
Phase 1 (Sports priorities — parallel by data_type)
        │
        ▼
Phase 2 (CeFi gap-fill — parallel by venue×year)
        │
        ▼
Phase 3 (TradFi residuals — verify + small gap-fills)
        │
        ▼
Phase 4 (Prediction backfill)
        │
        ▼
Phase 5 (DeFi backfill)
        │
        ▼
Phase 6 (Final verification + codex updates)
```

## Phase 0 — UI + adapter unblockers (no backfills until these land)

The deployment-ui has bugs that make the playbook hard to execute. Without these the dev can't see what's missing, can't
verify shards, can't iterate.

- [ ] [AGENT] P0. **Day-shard scroll** — `deployment-ui/src/components/DataStatusTab.tsx#L4480` hard-codes
      `.slice(0, 60)` on date lists. Replace with `useState(60)` + "Load more" button OR react-virtualised infinite
      scroll. Backend `/api/data-status/manifest` already supports offset/limit. Same pattern at `#L4523` for
      `missingDatesList`.
- [ ] [AGENT] P0. **CSV download returns headers-only** — root cause is inconsistent endpoints across the three download
      paths (`/api/data-status/download-csv`, `/api/data-status/download-shard-csv`, `csv_projected` URL from
      `shard-detail`). Unify on a single endpoint that accepts
      `(service, asset_group, venue, day, instrument_type, data_type,     [instrument_ids])` and returns rows.
      Server-side projection bug: empty `instrument_ids` should mean "all rows", not "no rows". Test in `deployment-api`
      first; then thread through UI.
- [ ] [AGENT] P0. **Sports league/day aggregated CSV not wired** — the `buildFixturesCsvDownloadUrl()` helper in
      `deployment-ui/src/api/client.ts#L2011` already exists; just unwired in the FixtureBreakdown view. Add "Download
      day CSV" button next to the day badge in DataStatusTab's sports drilldown. Per-fixture download already works.
- [ ] [AGENT] P1. **Unified market-tick-data + market-data-processing view** — currently parent-tab-level service
      selection forces one or the other. Either (a) split-pane view showing raw left / processed right for the same
      date+venue, or (b) service multi-select inside DataStatusTab. Backend single endpoint `/api/data-status/manifest`
      already takes `service` param so client can fan out two requests and merge.
- [ ] [AGENT] P0. **View Schema button** — per the audit it's already wired and `fetchShardSchema()` calls
      `/data-status/schema`. The user reports it's not working. Verify the endpoint actually returns the registered
      `SchemaDefinition` for the queried data type — likely a backend gap where unregistered shards return 404 or empty.
      Confirm `SchemaDefinition` registry is loaded for ALL data types being queried (instruments, market-tick,
      market-data-processing). Cross-check with
      [02-data/schema-governance.md](../../codex/02-data/schema-governance.md).

## Phase 0.5 — Verify in-flight sports work has settled

Sports already has work running (other agent). New launches WILL collide if af/tm/sfi/fs are still active because they
share league partitions. Block until they're done.

- [ ] [HUMAN] P0.
      `gcloud compute instances list --filter='name~"^(af|tm|sfi|fs|manifest-consolidator)-"' --format='table(name,status,zone)'`
      — should be empty (or only manifest-consolidator).
- [ ] [HUMAN] P0. Re-snapshot deployment-ui sports drilldown headline — confirm ≥80% captured (the L2 rename pass is
      manifest-neutral so % may stay at 79.97%; the change is on-disk path canonicality, not manifest claims).
- [ ] [AGENT] P0. `instruments-service/scripts/reconcile_phantom_manifest_rows.py --asset-group sports --dry-run` —
      should report zero phantoms post-L2.
- [ ] [AGENT] P1. Spot-check 5 random `(captured, sports, day, league_id, data_type)` rows: follow each to the canonical
      GCS path and confirm the parquet exists. Validates L2 rename completion.

## Phase 1 — Sports priorities (worst-coverage first)

Per the screenshot, target sub-60% data types in priority order. For each, launch the relevant backfill VM with
prediction-vs-reference league filters applied.

- [ ] [HUMAN] P0. **FIXTURE_FEATURES (0%)** —
      `launch-api-football-backfill-vm.sh     --data-type FIXTURE_FEATURES --leagues prediction --start-date 2020-06-01`.
      Reference leagues skipped per cutoff rule. Run phantom recon afterwards.
- [ ] [HUMAN] P0. **PLAYER_VALUES (2%)** —
      `launch-transfermarkt-backfill-vm.sh     --data-type PLAYER_VALUES --leagues prediction --start-date 2020-06-01`.
- [ ] [HUMAN] P0. **MATCHES (18%)** — investigate first: `MATCHES` should be near 100% (basic api_football). If the
      manifest claims 18% with the rest `attempted_failed`, the issue is API rate limit / wrong league set, not missing
      capability. Run phantom recon, then `--leagues all` (prediction + reference).
- [ ] [HUMAN] P0. **SFI_LEAGUES (14%)** —
      `launch-sfi-backfill-vm.sh     --data-type SFI_LEAGUES --start-date 2020-06-01`. SFI launched 2019; respect
      `SOURCE_COVERAGE_START['soccer_football_info']` clip.
- [ ] [HUMAN] P1. **SFI_PROGRESSIVE_STATS (15%)** — same launcher with
      `--data-type SFI_PROGRESSIVE_STATS --start-date 2020-01-01` (per `DATA_TYPE_COVERAGE_START` override).
- [ ] [HUMAN] P1. **TRANSFERMARKT_LEAGUES (50%)** — gap-fill via the same transfermarkt launcher with
      `--data-type TRANSFERMARKT_LEAGUES`.
- [ ] [AGENT] P1. After all sports backfills complete: run
      `instruments-service/scripts/reconcile_phantom_manifest_rows.py     --asset-group sports` to flip any phantom
      captured-no-parquet rows.
- [ ] [AGENT] P1. Re-snapshot the sports drilldown — expect every data type ≥95% captured+empty_confirmed under the
      secondary-cutoff denominator.

## Phase 2 — CeFi backfill (2019-01-01 → today)

- [ ] [HUMAN] P0. Launch the existing `launch-cefi-sharded-backfill.sh` for any year+venue+instrument shards still
      showing `attempted_failed`. The 2026-04-29 366-VM rollout (run-ts=20260429-154202) covered most of the space;
      verify in drilldown which shards are still red.
- [ ] [AGENT] P0. Phantom recon for `(asset_group=cefi)` after each batch.
- [ ] [AGENT] P1. Verify `market-data-processing-service` candle generation matches every captured tick day.
      Processed-data-status should mirror raw-tick-data-status one-to-one.

## Phase 3 — TradFi residuals

Most of the work landed 2026-04-30; remaining items are gap-fill + verification.

- [x] [AGENT] P0. Verify ETF coverage from listing dates (IBIT/FBTC/GBTC/ARKB from 2024-01-11; ETHA/FETH/ETHE from
      2024-07-23; BITO from 2021-10-19). `TRADFI_TICKER_COVERAGE_START` (UAC `15b9e74`) clips pre-listing days. **Done
      2026-05-06** — TradFi MVP closeout reached 98.8% honest coverage including IBIT/ETHA NASDAQ ETFs;
      deployment-service `13e877c` per-ticker listing-date clip applied. (FBTC/GBTC/ARKB/FETH/ETHE/BITO dropped from MVP
      scope per `project_tradfi_mvp_etf_scope_reduction_2026_05_05` — IBIT + ETHA cover spot exposure.)
- [x] [AGENT] P1. Confirm BTC + ETH futures heavy windows (May 2023 + Jun 2024) have `trades+tbbo` captured. Heavy
      reference months are the microstructure SSOT for crypto-basis backtests. **Done 2026-05-06** — per-(venue,
      data_type) coverage windows registry replaced global TRADFI_TICK_DATA_WINDOWS; `("CME","tbbo")` clipped to May
      2023 + Jun 2024 reference months and verified captured in TradFi MVP closeout.
- [x] [AGENT] P1. Confirm ES_OPT combo bundling holds — sample any 2024 day: should have
      `instrument_type=combo/data_type=ohlcv_1m/underlying=*/ticks.parquet` bundles, no per-combo legacy files.
      Migration ran 2026-05-01 04:14 UTC. **Done 2026-05-06** — ES.OPT options chain at 98.8% honest coverage in TradFi
      MVP closeout; combo bundling holds.
- [ ] [HUMAN] P2. **Deferred — VIX futures full-tick chain**. UAC `_CBOE_INSTRUMENTS = []` placeholder. Needs
      declarative VX contract calendar (XCBF.PITCH dataset, raw_symbol stype). Separate plan; index data already
      migrated (1,585 days at
      `asset_group=tradfi/venue=CBOE/     instrument_type=index/data_type=ohlcv_15m/VIX.parquet`).
- [ ] [HUMAN] P2. **Deferred — mbp_10 (10-deep book) for tradfi**. Adapter currently capped at
      `{ohlcv_1m, trades, tbbo}`. Reintroduce only if a microstructure strategy actually needs it — `tbbo` covers NBBO
      already.

## Phase 4 — Prediction backfill

- [ ] [HUMAN] P0. Run instruments-service prediction adapter for POLYMARKET (from 2020-06-12) + KALSHI (from
      2021-07-19). Per-sub-category (crypto/macro/football) cutoffs from `prediction-schema-paths.md`.
- [ ] [HUMAN] P0. Market-tick-data prediction backfill (orderbook + trades + derivative_ticker per sub-category).
- [ ] [AGENT] P1. Verify drilldown for `asset_group=prediction` has each sub-category green for in-coverage dates only.

## Phase 5 — DeFi backfill

- [ ] [HUMAN] P1. Per-protocol-per-chain backfill via `collect-evm-defi` / `collect-dex-swaps` CLI handlers (NOT the
      `download` operation). DeFi venues are in `VENUE_TO_ASSET_GROUP['defi']`.
- [ ] [AGENT] P1. Phantom recon for `(asset_group=defi)`.

## Phase 6 — Final verification + docs

- [ ] [AGENT] P0. Drilldown shows ≥99% captured+empty_confirmed across every asset group under the secondary-cutoff
      denominator.
- [ ] [AGENT] P0. `reconcile_phantom_manifest_rows.py --dry-run` reports zero phantom flips across all asset groups.
- [ ] [AGENT] P1. Schema-validation parity: for every data type, `View Schema` modal in UI matches the columns actually
      present in a sampled parquet.
- [ ] [AGENT] P1. Update `02-data/availability-manifest-and-data-status.md` with final coverage stats per asset group.
- [ ] [AGENT] P2. Mark plan complete + archive.

## Files to modify

| Repo                           | File                                                                                            | Phase |
| ------------------------------ | ----------------------------------------------------------------------------------------------- | ----- |
| deployment-ui                  | `src/components/DataStatusTab.tsx` (~L4480, L4523, L4758, L80-81)                               | 0     |
| deployment-ui                  | `src/api/client.ts` (~L1697, L1951, L1991, L2011)                                               | 0     |
| deployment-api                 | data-status route handlers (CSV download projection bug, schema endpoint coverage)              | 0     |
| instruments-service            | `scripts/reconcile_phantom_manifest_rows.py` (extend per-asset-group flag if not already there) | 1-5   |
| market-tick-data-service       | per-asset-group adapter health checks                                                           | 1-5   |
| market-data-processing-service | candle generation gap-fill                                                                      | 2     |
| unified-trading-pm             | this plan +`codex/14-playbooks/backfill-completion-playbook.md`                                 | 6     |

## Success criteria

- Phase 0: Drilldown CSV download returns row data; day-shard list scrolls through full window; sports league/day
  aggregated CSV button works; schema modal returns registered columns for every data type.
- Phase 1: Sports drilldown ≥95% captured+empty_confirmed under secondary-cutoff denominator (excluding reference-league
  rich features).
- Phase 2-5: Each asset group same threshold.
- Phase 6: Plan archived; codex doc reflects new coverage SSOT.

## Out of scope

- VIX futures full-tick chain (deferred — separate plan).
- mbp_10 deep-book for tradfi (deferred).
- Strategy-level "target instruments" subscription mechanism (different work stream entirely).
- New asset groups beyond the existing 5.

## Absorbed from sibling plans (2026-05-06)

This plan declares `epic: data-pipeline-completion` and is the canonical successor to the older 2026-04-18 plan with the
same name + scope. Folded:

- `data_pipeline_completion_2026_04_18` (archived) — older epic, same name + scope, same 22 repos. 139 open / 7 done.
  Operational scope (manifest schema + backfill + retire + schedule across 5 asset groups) is fully covered by this
  2026-05-01 epic with tighter audit. No item-level migration needed — strict subset.
- `data_canonicalisation_mvp_2026_04_17` (archived) — 33/67 done; Phase 3 migration scripts (CeFi/TradFi/DeFi) already
  shipped per `market_tick_data_to_100pct_2026_05_05` lines 65-67 (`migrate_*_canonical.py` exist in MTDS). Residual
  Phase 5/6 validation belongs in `shard_granularity_ssot_propagation_2026_05_06.HANDOVER`.

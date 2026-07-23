---
doc_type: plan
title: Instruments-service + market-tick-data + market-data-processing — full functionality across all asset groups
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    deployment-ui,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-01
priority: P0
owner: agent
type: epic
epic: data-pipeline-completion
completion_gates: { code: C2, deployment: D2, business: B1 }
repo_gates:
  - { repo: deployment-ui, deployment: D1 }
  - { repo: deployment-api, deployment: D1 }
  - { repo: instruments-service, deployment: D2 }
  - { repo: market-tick-data-service, deployment: D2 }
  - { repo: market-data-processing-service, deployment: D2 }
  - { repo: unified-api-contracts, deployment: D1 }
depends_on: []
isProject: true
---

## Deferred work — migrated to: `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`,

`plans/active/sports_master_closeout_2026_07_21.md`, `plans/active/data_completion_cefi_2026_07_15.md`,
`plans/active/tradfi_consolidated_closeout_2026_07_18.md`,
`plans/active/prediction_consolidated_closeout_2026_07_18.md`, `plans/active/defi_consolidated_closeout_2026_07_18.md`,
`plans/active/data_completion_to_100_all_ag_2026_06_21.md`,
`plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md` — successor: (see list above) (all 32 open
items — Phase 0 UI unblockers, per-AG backfills for sports/cefi/tradfi/prediction/defi, and Phase 6 final verification —
trace cleanly to the current per-AG consolidated-closeout family + the umbrella
`data_completion_to_100_all_ag_2026_06_21.md`. No genuinely orphaned items found.)

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 22 of 22 unchecked todos
- **Mis-marked DONE → flipped**: 0 — Phase 3 todos already correctly checked `[x]` (TradFi MVP closeout 2026-05-06: ETF
  coverage, BTC/ETH heavy windows, ES_OPT combo bundling)
- **In-flight (running VMs)** (verified 2026-05-07 via `gcloud compute instances list`):
  - `af-backfill-20260507-033214` RUNNING (api_football sports backfill)
  - `sfi-backfill-20260507-010938` RUNNING (soccer_football_info sports backfill)
  - 24 cefi backfill VMs + 5 tradfi MDPS + 4 sports backfill VMs (per audit context) — these contribute to Phase 1 +
    Phase 2 completion
  - vm-zombie-watchdog (always running)
- **Blocked by**: `infrastructure_master_2026_05_07` Phase 0 deployment-ui drilldown CSV/scroll/SchemaModal items
  partially overlap with this plan's Phase 0; `manifest_migration_master_2026_05_07` for any cross-axis canonicalization
- **Blocks**: `master_to_live_defi_2026_05_23` operator-facing data-status verification gate (≥99% captured +
  empty_confirmed across all asset_groups under secondary-cutoff denominators); `cefi_master` / `defi_master` /
  `tradfi_master` / `sports_master` / `predictions_master` umbrellas all consume the per-asset-group coverage state
  validated by this plan
- **Last meaningful commits**:
  - instruments-service@`9f0e3f9` (dedup_phantom_after_recovery.py) — 2026-05-07
  - instruments-service@`21aef51` (reconcile_expected_absence_reasons.py imports classify_legacy_empty_row from UTL Tier
    3D.2) — 2026-05-07
  - instruments-service@`1f93745` (reconcile_expected_absence_reasons.py — Tier 3D legacy null-reason backfill) —
    2026-05-07
  - instruments-service@`8b5eca3` (orchestrator Tier 2B pre-skip → record_expected_empty)
  - instruments-service@`070f7e7` (api_football throttle bump 15 req/sec)
  - instruments-service@`8050477` (sports data_available_at → available_at migration script)
  - market-tick-data-service@`fc53a97` / `51fecd5` / `10aa715` (DEX perp adapters: Lighter + Pacifica)
  - market-tick-data-service@`ba5423f` (mtds_reconcile_partial_bundles.py)
  - deployment-ui@`ebfbc5d` (default startDate 2018-01-01)
  - deployment-ui@`537d468` / `7309b56` (SchemaModal + summary-label fixes)
- **Recommendation**: **NOT YET ARCHIVE-READY** — Phase 1 (sports priorities) is in-flight via 2 RUNNING VMs (`af` +
  `sfi`) — Phase 0.5 verification gate cannot pass until they finish; multiple Phase 4-5 items (Polymarket/Kalshi
  prediction backfill, DeFi per-protocol backfill) remain unchecked. Phase 0 deployment-ui CSV-download projection bug +
  day-shard scroll items appear partially landed via deployment-ui@`e961c39` "in-flight drilldown UI iteration" +
  `c532fec` "in-flight DataStatusTab + client.ts iteration" but explicit verification per todo missing. **Operator
  priority for May-23 deadline**: complete Phase 1 sports backfill + run phantom recon + Phase 4 prediction backfill;
  Phase 5 DeFi backfill is the gating dependency for `defi_master`. Suggest a 1-day deployment-ui Phase 0 audit pass to
  flip the Phase 0 todos that are already shipped.
- **Anomalies**:
  - "Day-shard scroll" todo references `L4480 .slice(0, 60)` but current `DataStatusTab.tsx` uses
    `slice(0, MAX_VISIBLE)` with `expanded`-based toggle at lines 194/245 — pattern is already migrated to a working
    "Load more" equivalent. The bug as described may already be fixed; needs explicit verification.
  - "Sports league/day aggregated CSV not wired" todo: verified `buildFixturesCsvDownloadUrl` IS wired at
    `DataStatusTab.tsx:4995` via
    `downloadUrl={(date) => buildFixturesCsvDownloadUrl({ day: date, league_id: leagueName })}` — likely DONE, needs
    verification flip.
  - "View Schema button" todo: `fetchShardSchema()` exists at `client.ts:1709` and SchemaModal wired in
    deployment-ui@`7309b56`/`537d468` — likely DONE, needs verification flip.
  - The `reconcile_phantom_manifest_rows.py` (sports-only legacy) reference in Phase 0.5 + Phase 1.7 is being phased out
    per CLAUDE.md "phantom audit" rule — should use `reconcile_phantom_manifest_rows_all.py --asset-group sports` per
    the multi-asset-group successor.

## Context

**Goal**: every asset group (sports, cefi, tradfi, defi, prediction) at 100% honest coverage for instruments-service +
market-tick-data-service + market-data-processing-service, verifiable via the deployment-ui data-status drilldown.

"Honest" means manifest `capture_status ∈ {captured, empty_confirmed}` with parquets actually present at the canonical
GCS paths, and the secondary cutoffs applied so legitimately-empty shards (pre-launch dates, non-prediction leagues for
rich features, etc.) don't render as missing.

**Operational SSOT**: `/codex/14-playbooks/backfill-completion-playbook.md`.

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
      `missingDatesList`. [AUDIT 2026-05-07: VERIFIED-LIKELY-DONE — current `DataStatusTab.tsx:194` uses
      `expanded ?     filtered : filtered.slice(0, MAX_VISIBLE)` toggle pattern; line 245 uses `dates.slice(0, limit)`;
      hard-coded `slice(0, 60)` no longer present; verify "Load more" UX with 1-min Playwright check then flip]
- [ ] [AGENT] P0. **CSV download returns headers-only** — root cause is inconsistent endpoints across the three download
      paths (`/api/data-status/download-csv`, `/api/data-status/download-shard-csv`, `csv_projected` URL from
      `shard-detail`). Unify on a single endpoint that accepts
      `(service, asset_group, venue, day, instrument_type, data_type,     [instrument_ids])` and returns rows.
      Server-side projection bug: empty `instrument_ids` should mean "all rows", not "no rows". Test in `deployment-api`
      first; then thread through UI. [AUDIT 2026-05-07: FRESH — actionable; both download endpoints still distinct
      (`download-csv` at line 2107, `download-shard-csv` at line 2156); deployment-ui@`e961c39` "in-flight drilldown UI
      iteration" suggests partial work; needs explicit unification + projection-bug fix]
- [ ] [AGENT] P0. **Sports league/day aggregated CSV not wired** — the `buildFixturesCsvDownloadUrl()` helper in
      `deployment-ui/src/api/client.ts#L2011` already exists; just unwired in the FixtureBreakdown view. Add "Download
      day CSV" button next to the day badge in DataStatusTab's sports drilldown. Per-fixture download already works.
      [AUDIT 2026-05-07: DONE — verified `buildFixturesCsvDownloadUrl` is now imported at `DataStatusTab.tsx:35` and
      wired at line 4995 via
      `downloadUrl={(date) => buildFixturesCsvDownloadUrl({ day: date, league_id: leagueName     })}`; flip checkbox]
- [ ] [AGENT] P1. **Unified market-tick-data + market-data-processing view** — currently parent-tab-level service
      selection forces one or the other. Either (a) split-pane view showing raw left / processed right for the same
      date+venue, or (b) service multi-select inside DataStatusTab. Backend single endpoint `/api/data-status/manifest`
      already takes `service` param so client can fan out two requests and merge. [AUDIT 2026-05-07: FRESH — actionable;
      P1 deferral acceptable for May-23 deadline]
- [ ] [AGENT] P0. **View Schema button** — per the audit it's already wired and `fetchShardSchema()` calls
      `/data-status/schema`. The user reports it's not working. Verify the endpoint actually returns the registered
      `SchemaDefinition` for the queried data type — likely a backend gap where unregistered shards return 404 or empty.
      Confirm `SchemaDefinition` registry is loaded for ALL data types being queried (instruments, market-tick,
      market-data-processing). Cross-check with [02-data/schema-governance.md](/codex/02-data/schema-governance.md).
      [AUDIT 2026-05-07: VERIFIED-LIKELY-DONE — `fetchShardSchema()` at `client.ts:1709` confirmed wired; SchemaModal
      shipped deployment-ui@`7309b56` (SmartDownloadButton + multi-axis SchemaModal) + deployment-ui@`537d468` (3
      schema-modal + summary-label bugs); deployment-api@`4ca4bb7` enriched 'no schema yet' response with probed_paths;
      per-data-type SchemaDefinition coverage audit pending — verify and flip]

## Phase 0.5 — Verify in-flight sports work has settled

Sports already has work running (other agent). New launches WILL collide if af/tm/sfi/fs are still active because they
share league partitions. Block until they're done.

- [ ] [HUMAN] P0.
      `gcloud compute instances list --filter='name~"^(af|tm|sfi|fs|manifest-consolidator)-"' --format='table(name,status,zone)'`
      — should be empty (or only manifest-consolidator). [AUDIT 2026-05-07: IN-FLIGHT — VM `af-backfill-20260507-033214`
      RUNNING + `sfi-backfill-20260507-010938` RUNNING (2 of 4 still active per gcloud); ETA: same-day completion
      (2026-05-07); cannot satisfy gate until they finish]
- [ ] [HUMAN] P0. Re-snapshot deployment-ui sports drilldown headline — confirm ≥80% captured (the L2 rename pass is
      manifest-neutral so % may stay at 79.97%; the change is on-disk path canonicality, not manifest claims). [AUDIT
      2026-05-07: BLOCKED-ON instruments_and_market_tick_data_completion:Phase-0.5-VMs-finish; deployment-ui startDate
      fix (deployment-ui@`ebfbc5d`) means the snapshot now defaults to 2018-01-01 → today]
- [ ] [AGENT] P0. `instruments-service/scripts/reconcile_phantom_manifest_rows.py --asset-group sports --dry-run` —
      should report zero phantoms post-L2. [AUDIT 2026-05-07: BLOCKED-ON
      instruments_and_market_tick_data_completion:Phase-0.5-VMs-finish; ALSO: per CLAUDE.md "phantom audit" rule the
      multi-asset-group `reconcile_phantom_manifest_rows_all.py` is the canonical successor — sports-only legacy script
      being phased out; switch invocation when running]
- [ ] [AGENT] P1. Spot-check 5 random `(captured, sports, day, league_id, data_type)` rows: follow each to the canonical
      GCS path and confirm the parquet exists. Validates L2 rename completion. [AUDIT 2026-05-07: BLOCKED-ON
      instruments_and_market_tick_data_completion:Phase-0.5-VMs-finish]

## Phase 1 — Sports priorities (worst-coverage first)

Per the screenshot, target sub-60% data types in priority order. For each, launch the relevant backfill VM with
prediction-vs-reference league filters applied.

- [ ] [HUMAN] P0. **FIXTURE_FEATURES (0%)** —
      `launch-api-football-backfill-vm.sh     --data-type FIXTURE_FEATURES --leagues prediction --start-date 2020-06-01`.
      Reference leagues skipped per cutoff rule. Run phantom recon afterwards. [AUDIT 2026-05-07: IN-FLIGHT — VM
      `af-backfill-20260507-033214` RUNNING; instruments-service@`070f7e7` bumped api_football throttle to 15 req/sec
      (Mega tier), instruments-service@`8b5eca3` Tier 2B pre-skip → record_expected_empty for non-prediction-league
      shards, instruments-service@`cf20016` promoted recovery_fixture_ids to redo_all]
- [ ] [HUMAN] P0. **PLAYER_VALUES (2%)** —
      `launch-transfermarkt-backfill-vm.sh     --data-type PLAYER_VALUES --leagues prediction --start-date 2020-06-01`.
      [AUDIT 2026-05-07: FRESH — TM not in current RUNNING VM list; need to relaunch; per CLAUDE.md MEMORY 2026-04-29
      entry, 167k fake PLAYER_VALUES denorm rows already cleaned up via phantom recon]
- [ ] [HUMAN] P0. **MATCHES (18%)** — investigate first: `MATCHES` should be near 100% (basic api_football). If the
      manifest claims 18% with the rest `attempted_failed`, the issue is API rate limit / wrong league set, not missing
      capability. Run phantom recon, then `--leagues all` (prediction + reference). [AUDIT 2026-05-07: IN-FLIGHT —
      likely covered by `af-backfill-20260507-033214` VM; verify post-VM-completion via deployment-ui drilldown]
- [ ] [HUMAN] P0. **SFI_LEAGUES (14%)** —
      `launch-sfi-backfill-vm.sh     --data-type SFI_LEAGUES --start-date 2020-06-01`. SFI launched 2019; respect
      `SOURCE_COVERAGE_START['soccer_football_info']` clip. [AUDIT 2026-05-07: IN-FLIGHT — VM
      `sfi-backfill-20260507-010938` RUNNING]
- [ ] [HUMAN] P1. **SFI_PROGRESSIVE_STATS (15%)** — same launcher with
      `--data-type SFI_PROGRESSIVE_STATS --start-date 2020-01-01` (per `DATA_TYPE_COVERAGE_START` override). [AUDIT
      2026-05-07: IN-FLIGHT — likely covered by `sfi-backfill-20260507-010938` VM; verify per-data-type post-completion]
- [ ] [HUMAN] P1. **TRANSFERMARKT_LEAGUES (50%)** — gap-fill via the same transfermarkt launcher with
      `--data-type TRANSFERMARKT_LEAGUES`. [AUDIT 2026-05-07: FRESH — TM not in current RUNNING VM list]
- [ ] [AGENT] P1. After all sports backfills complete: run
      `instruments-service/scripts/reconcile_phantom_manifest_rows.py     --asset-group sports` to flip any phantom
      captured-no-parquet rows. [AUDIT 2026-05-07: BLOCKED-ON
      instruments_and_market_tick_data_completion:Phase-1-sports-VMs; switch to
      `reconcile_phantom_manifest_rows_all.py     --asset-group sports` per CLAUDE.md phantom-audit rule]
- [ ] [AGENT] P1. Re-snapshot the sports drilldown — expect every data type ≥95% captured+empty_confirmed under the
      secondary-cutoff denominator. [AUDIT 2026-05-07: BLOCKED-ON
      instruments_and_market_tick_data_completion:Phase-1-sports-VMs]

## Phase 2 — CeFi backfill (2019-01-01 → today)

- [ ] [HUMAN] P0. Launch the existing `launch-cefi-sharded-backfill.sh` for any year+venue+instrument shards still
      showing `attempted_failed`. The 2026-04-29 366-VM rollout (run-ts=20260429-154202) covered most of the space;
      verify in drilldown which shards are still red. [AUDIT 2026-05-07: IN-FLIGHT — 24 cefi backfill VMs RUNNING per
      audit context (writing to manifest, depend on UTL StreamingShardFinalizer + shard-axes correctness);
      deployment-service@`f77c4f4` bumped CeFi VM defaults post-streaming-finalize ship; deployment-service@`eb363ac`
      added singleton-lock to launch-cefi-sharded-backfill.sh]
- [ ] [AGENT] P0. Phantom recon for `(asset_group=cefi)` after each batch. [AUDIT 2026-05-07: BLOCKED-ON
      instruments_and_market_tick_data_completion:Phase-2-cefi-VMs-finish; per CLAUDE.md MEMORY 2026-05-04, 130,897
      false-positive cefi phantoms diagnosed as path-prefix + chain-bundle drift, audit hardened — real residual = 354
      (99.7% reduction)]
- [ ] [AGENT] P1. Verify `market-data-processing-service` candle generation matches every captured tick day.
      Processed-data-status should mirror raw-tick-data-status one-to-one. [AUDIT 2026-05-07: BLOCKED-ON
      writegate_honest_coverage_endtoend_2026_05_06:Phase-2.A-MDPS-adapter-migration;
      MDPS@`5b52d0b`/`b9f9328`/`80cf141`/`e9520a0` shipped Tier 2A/C/D/E adapter migrations off
      `_create_empty_output()`; reconciler MDPS@`d3be0ef` cleaning up legacy 1440-NaN placeholders]

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
      `asset_group=tradfi/venue=CBOE/     instrument_type=index/data_type=ohlcv_15m/VIX.parquet`). [AUDIT 2026-05-07:
      STALE-DEFERRED — P2 explicitly deferred to separate plan; not blocking May-23 deadline]
- [ ] [HUMAN] P2. **Deferred — mbp_10 (10-deep book) for tradfi**. Adapter currently capped at
      `{ohlcv_1m, trades, tbbo}`. Reintroduce only if a microstructure strategy actually needs it — `tbbo` covers NBBO
      already. [AUDIT 2026-05-07: STALE-DEFERRED — P2 explicitly deferred; tbbo covers NBBO; not blocking May-23]

## Phase 4 — Prediction backfill

- [ ] [HUMAN] P0. Run instruments-service prediction adapter for POLYMARKET (from 2020-06-12) + KALSHI (from
      2021-07-19). Per-sub-category (crypto/macro/football) cutoffs from `prediction-schema-paths.md`. [AUDIT
      2026-05-07: BLOCKED-ON predictions_master_2026_05_07:Phase-1-canonical-question-group-SSOT; UAC `bb24aba` ships
      PREDICTION_GROUPS skeleton + UAC `af2bc9b` ships canonical-question-group SSOT + lifecycle + classifier — gating
      SSOT now landed; Polymarket migration script MTDS@`migrate_polymarket_canonical.py` exists per archived plan]
- [ ] [HUMAN] P0. Market-tick-data prediction backfill (orderbook + trades + derivative_ticker per sub-category). [AUDIT
      2026-05-07: BLOCKED-ON predictions_master_2026_05_07:Phase-2-MTDS-prediction-backfill; deployment-service
      launch-mtds-prediction-backfill-vm.sh exists with VM_ASSET_GROUP=PREDICTION env]
- [ ] [AGENT] P1. Verify drilldown for `asset_group=prediction` has each sub-category green for in-coverage dates only.
      [AUDIT 2026-05-07: BLOCKED-ON instruments_and_market_tick_data_completion:Phase-4-prediction-backfill-VMs]

## Phase 5 — DeFi backfill

- [ ] [HUMAN] P1. Per-protocol-per-chain backfill via `collect-evm-defi` / `collect-dex-swaps` CLI handlers (NOT the
      `download` operation). DeFi venues are in `VENUE_TO_ASSET_GROUP['defi']`. [AUDIT 2026-05-07: BLOCKED-ON
      defi_master_2026_05_07:DeFi-protocol-backfill; UAC@`f22f4b1` CHAIN_GENESIS_DATES SSOT + UAC@`0169a0a`
      PROTOCOL_LAUNCH_DATES SSOT shipped enabling per-(chain, protocol) clipping; deployment-api@`14bbff9` per-chain
      pre-launch clipping wired]
- [ ] [AGENT] P1. Phantom recon for `(asset_group=defi)`. [AUDIT 2026-05-07: BLOCKED-ON
      instruments_and_market_tick_data_completion:Phase-5-defi-backfill; instruments-service@`e8393fc` shipped DeFi axes
      6+7 (protocol underscore + migrated-bundle wildcard) into phantom-recon — script handles DeFi case]

## Phase 6 — Final verification + docs

- [ ] [AGENT] P0. Drilldown shows ≥99% captured+empty_confirmed across every asset group under the secondary-cutoff
      denominator. [AUDIT 2026-05-07: BLOCKED-ON instruments_and_market_tick_data_completion:Phases-1-5-completion;
      current per-MEMORY: instruments-service ~99.4% per deployment-ui (6901/15240 shards 99.4% in
      2018-01-01..2026-05-06 window after deployment-ui@`ebfbc5d` startDate fix)]
- [ ] [AGENT] P0. `reconcile_phantom_manifest_rows.py --dry-run` reports zero phantom flips across all asset groups.
      [AUDIT 2026-05-07: BLOCKED-ON instruments_and_market_tick_data_completion:Phases-1-5-completion; switch invocation
      to `reconcile_phantom_manifest_rows_all.py` per CLAUDE.md phantom-audit successor]
- [ ] [AGENT] P1. Schema-validation parity: for every data type, `View Schema` modal in UI matches the columns actually
      present in a sampled parquet. [AUDIT 2026-05-07: BLOCKED-ON
      instruments_and_market_tick_data_completion:Phase-0-View-Schema; per-data-type SchemaDefinition coverage audit
      needed]
- [ ] [AGENT] P1. Update `02-data/availability-manifest-and-data-status.md` with final coverage stats per asset group.
      [AUDIT 2026-05-07: BLOCKED-ON instruments_and_market_tick_data_completion:Phase-6-pre-codex-coverage-stats]
- [ ] [AGENT] P2. Mark plan complete + archive. [AUDIT 2026-05-07: BLOCKED-ON
      instruments_and_market_tick_data_completion:Phase-6-codex-update]

## Files to modify

| Repo                           | File                                                                                            | Phase |
| ------------------------------ | ----------------------------------------------------------------------------------------------- | ----- |
| deployment-ui                  | `src/components/DataStatusTab.tsx` (~L4480, L4523, L4758, L80-81)                               | 0     |
| deployment-ui                  | `src/api/client.ts` (~L1697, L1951, L1991, L2011)                                               | 0     |
| deployment-api                 | data-status route handlers (CSV download projection bug, schema endpoint coverage)              | 0     |
| instruments-service            | `scripts/reconcile_phantom_manifest_rows.py` (extend per-asset-group flag if not already there) | 1-5   |
| market-tick-data-service       | per-asset-group adapter health checks                                                           | 1-5   |
| market-data-processing-service | candle generation gap-fill                                                                      | 2     |
| unified-trading-pm             | this plan +`/codex/14-playbooks/backfill-completion-playbook.md`                                | 6     |

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
  shipped per `plans/archive/market_tick_data_to_100pct_2026_05_05.md` lines 65-67 (`migrate_*_canonical.py` exist in
  MTDS; per-asset-group MTDS-to-100% slices now folded into the asset_group umbrellas `cefi_master_2026_05_07` /
  `defi_master_2026_05_07` / `tradfi_master_2026_05_07` / `sports_master_2026_05_07` / `predictions_master_2026_05_07`).
  Residual Phase 5/6 validation belongs in `infrastructure_master_2026_05_07.md` (folds in
  `plans/archive/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`).

---
doc_type: plan
title:
  MASTER COORDINATOR — data-layer canonicalisation history round 2 (2026-06-11 R1-R6 ratification todos + R5 smoke
  ledger evidence tables, extracted from the master coordinator)
summary: >-
  Companion history doc to `master_data_canonicalisation_migration_catalogue_2026_06_07.md` — a second extraction pass
  (the first was 2026-07-24, see the sibling `..._history_2026_07_24.md`) moving the fully-closed 2026-06-11 R1-R6
  ratification-todo narrative (backfill/schema/verdict/IS-freeze/service-smoke/codex-reconcile, all six checked ✅) and
  the R5 smoke-ledger's descriptive evidence (the BLOCKED-shards table, GREEN-per-AG table, cross-cutting findings, and
  the promotion-to-main snapshot — pure record, no checkboxes) out of the parent plan for 1000-line hard-cap compliance
  (`plans/active/task_template.md` §3 finding J discipline; filed via
  `/plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md`). Zero open todos — pure
  narrative/evidence record. The still-open R8-sports/pred-gates parent checkbox and the R5-remediation-todos subsection
  (which carries the one still-open R5-fix-7 item) were deliberately LEFT in the live parent doc, not extracted here,
  since this doc is closed-history-only.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    e2e-testing,
  ]
scope: [engineer, admin]
tags: [coordinator, migration, manifest, data-layer, pipeline-mode, catalogue, progress-log, history, audit-log]
related:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/2026_07/master_data_canonicalisation_migration_catalogue_history_2026_07_24.md,
    /plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
supersedes:
superseded_by:
depends_on: []
source: [context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md]
drift_direction: advance-code
---

# MASTER COORDINATOR — data-layer canonicalisation history round 2 (2026-06-11 evidence)

> Extracted verbatim from `master_data_canonicalisation_migration_catalogue_2026_06_07.md` on 2026-08-03 (line-cap
> remediation, second pass). Zero open todos here; the parent plan remains the single live source of truth for all open
> work.

## Ratification todos — R1 through R6 (all ✅ DONE, extracted verbatim)

> Originally under the parent's "### Ratification todos (the dispatch — owners per slot map)" heading. R8 (which still
> carries an open parent checkbox even though its sports/prediction sub-items are done) was LEFT in the parent doc, not
> extracted here.

- [x] ✅ [DATA] P0. **R1-backfill — per-AG class-E characterize→canonicalise→`record_captured` backfill** — **E==0 +
      `unknown_prefixes`==0 GREEN on all four hive AGs 2026-06-11 ~14:32Z** (defi/cefi/prediction/tradfi; sports = R8).
      Tool `backfill_orphan_class_e.py` (is@0a2e542 + c49d957 + row-key/parser/footer fixes through is@f73abe4+):
      characterize→convert-to-v9→`record_captured` with per-cell sample-verify; headline: most E was matcher
      false-positive (venue-spelling/grain — defi 254,984 ALL covered); real backfills = tradfi 15,694 converted,
      prediction 7,462 converted, cefi 74,392 record-only; tbbo spec carries (uac@715e2ed lineage +
      `ts_init`/`bid_size`/ `ask_size`); one-shot consolidations merged backfill shards (index ≥ snapshot everywhere —
      no loss).

      Full narrative + verdicts in the G3.5 plan Progress Log. — instruments-service@f73abe4, uac@<tbbo>, reports
          `_index/audit/orphan_sweep_<ag>.parquet` + `orphan_backfill_<ag>.parquet`.

- [x] ✅ [UAC] P0. **R2-schema — carry ALL dropped columns into v9** — **unified-api-contracts@715e2ed**: v9
      `SchemaSpec` registry extended so CF-18 is GREEN per AG — all 11 polymarket trades columns carried (amount, asset,
      conditionId→`condition_id`, outcomeIndex→`outcome_index`, transactionHash→`transaction_hash`,
      data_source→`source`, market_type, resolution_period, symbol, timestamp, underlying — camelCase via
      `ColumnSpec.source_aliases`, never duplicate canonical cols) + new SchemaSpecs for defi
      rewards/risk_params/utilization + tradfi/trades (+ the full RED list: defi dex_pool_swaps/lending_indices, tradfi
      options_chain/CME, etc.). Completeness regression suite `tests/unit/test_schema_spec_completeness.py` (registry
      round-trip + alias hygiene + per-cell source-column completeness + previously-RED pins) GREEN. The
      `migration_schema_completeness` per-AG re-run (consumes the contract via `carried_column_names`, the same SSOT) is
      now 0-RED at the contract level. slot-3 → this autonomous tail. Repo: unified-api-contracts.
- [x] ✅ [DATA] P0. **R3-verdicts — V5 render + V6 verdict per AG ASSEMBLED on CURRENT HEAD (2026-06-17, autonomous
      run)** — verdict packs in `plans/audit/results/r3_verdict_packs_2026_06_17/` (per-AG projected-v9 render + status
      distribution + `manifest_diff` report + verdict line; `manifest_diff_<ag>.json` + `analyze_diff.py` attached). All
      regenerated on HEAD vs the live 06-14 `_index`. **4/5 GREEN outright + prediction GREEN after a stale-projection
      correction:** defi GREEN (cap 348K→440K, removed=39,867 = legacy `dex_swaps`→`swaps_ohlcv_<tf>` `data_type`
      supersession, 105 phantom downgrades; projection REGENERATED — defi rebuild changed mtds@89807b4) · cefi GREEN
      (cap 1.33M→2.49M CF-11 honest re-emit; removed=733 garbage venues 0-objects; 375 phantom) · tradfi GREEN (cap
      100K→902K legacy pre-hive parser; 2,902 phantom closed-market-day downgrades **spot-verified on HEAD**: CME
      2020-01-01 has no ohlcv_15m object) · sports GREEN (gate 0/0; only −17,288 ODDS_API probe-artifact exclusion) ·
      **prediction GREEN — 75.3% cqg coverage** (NOT the stale 0.2%: the cqg classifier is UAC-resident and the registry
      was expanded under decision 338 in 3 UAC commits AFTER the 06-11 projection → re-projected on HEAD: 542,170
      `ClassifierConfidenceLow`→1, captured 7,116 cqg bundles; the removed cells = raw-grain superseded BY DESIGN by the
      cqg-bundle atom). Every AG schema→v9 100% + pipeline_mode blank→source-aware; projected ≥ pre_migration snapshot.
      M-COORD-7 corroborated GREEN (STEP 5.85 + AST = 0). **Operator clear to V6-eyeball + G4 --apply on ALL FIVE AGs.**
      Original "dev restart-deployment-stack render" is the operator's own live eyeball (recipe in the pack README;
      beta-blob projections live in GCS); the verdict packs embed the textual coverage render. mtds@df69ada · is/uac
      HEAD · reports `\_index/audit/projected_index\**<ag>\_.parquet`.
- [x] ✅ [DATA] P0. **R4-IS-freeze — diagnose + resume IS definition collection + backfill 2026-05-21→now gap BEFORE any
      could-exist seed**; then re-run `build_instrument_catalogue` + `enumerate_expected_universe v2` per AG. (Note:
      collection is reference-data — independent of the drained market-data writers; resuming does NOT violate the
      pre-migration drain.) slot-3. Repos: instruments-service + deployment-service. — **✅ COMPLETE 2026-06-11
      (slot-4).** Root cause = 3 layers (scheduled producers structurally DEAD for months — the
      `instruments-service-daily` Workflow targets a nonexistent Cloud Run job `instruments-service`, FAILED daily since
      ≥2026-03-13; capture was actually carried by manual `instr-backfill-*` VM launches that stopped ~05-22; the 06-08
      drain then paused the already-dead schedulers; + defi-specific c7d9bb2 venue-tag regression silently dropping 21
      venues, FIXED instruments-service@0ae4e481). Both IS schedulers re-ENABLED (ONLY those two —
      consolidator/market-data stay drained). Backfills run locally (per-VM shards `r4-is-backfill-local*`): cefi
      05-23→06-11 (15/16 venues; DERIBIT-COMBO upstream 400), defi 05-09→06-11 `--force` (52–53/57;
      AAVE_V3-OPTIMISM/MORPHO×2/DRIFT vendor-side), tradfi 06-08→06-11 (4/5; CME = Massive futures-endpoint 404
      BLOCKED-UPSTREAM). Catalogues re-promoted (monotonic ACCEPT): cefi 220,222 / defi 6,853 / tradfi 686,348 rows. v2
      enumerate scan-only (NO --apply-write): cefi 35,894,676 / defi 167,458,116 / tradfi 109,235,280 candidates.
      sports/prediction = report-only (pred by_date frozen at 2026-05-12 write; both lack prod/catalog.parquet pending
      the granularity-aware producer). Full evidence + 3 new todos (producer rebuild P0; CME re-probe P1;
      silent-thinning hardening P2): `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` § "Progress Log —
      R4-IS-freeze execution".
- [x] ✅ [AUDIT] P0. **R5-service-smoke — per-(service × asset_group) credential + data-fetch smoke matrix — DONE
      (slot-4 resume 2026-06-11)**: 26 live probes (12 predecessor + 14 resume; logs `/tmp/r5_smoke/*.log` on the worker
      host) across IS definitions ×5 AGs + mtds tick fetch per source (tardis, databento, massive, hyperliquid, onchain
      RPC eth+solana, thegraph subgraph, polymarket clob+gamma, kalshi, odds_api, footystats, yahoo; barchart = static
      GCS preload by design — no live adapter exists to smoke). Every failure audited + classified (auth / 4xx / empty /
      precondition / code-bug); BLOCKED shards emitted at (AG × data_type × venue) grain in "### R5 smoke ledger" below
      — no whole-AG blocks. Promotion-to-main snapshot included (NO repo's 2026-06-10/11 LDR ships have fully reached
      `main` yet — stale-image caveat recorded). 1 credential ask (Databento account LOCKED).
- [x] ✅ [DOCS] P0. **R6-codex — full M-COORD-1 closure BEFORE applies — DONE (slot-4 resume 2026-06-11, pm@a28cbd4d7 +
      pm@51863c157 + pm@05456c343)**: 5 per-AG plans de-coarsened (gate banners reconciled to M-COORD-1/R6-codex;
      defi+cefi deep-annotated — every remaining coarse/`hyperliquid_rest` token is a marked legacy-state/historical
      record, never spec; defi A12f-col CLOSED by ratification); `pipeline-mode-and-batch-live-reconciliation.md`
      hyperliquid_rest purged (vendor-only + transport column; sole remaining mention = the documented retirement) +
      reconciled to M1–M8 (replay stratum + reconciliation-facing M1–M8 slice); `sports-batch-live.md` (NEW) +
      `prediction-batch-live.md` + `tradfi-batch-live.md` seam docs shipped at cefi depth (phantom empty-reasons
      corrected against real UAC closed set); M1–M8 live/replay TARGET design codified as settled contract in
      `/codex/02-data/pipeline-mode-partition.md` § "Ratified TARGET design" (+`batch-live-architecture.md` §10.5/§13,
      `cefi-batch-live.md` §7, `replay-subsystem.md` SUPERSEDED banner, `availability-manifest-and-data-status.md`
      live-taxonomy reconcile) — ratified-with-gated-tranche named (`M1-BREAKING`). slot-7→slot-4. Repo:
      unified-trading-pm.

## R5 smoke ledger — pending-post-migration-backfill shards (2026-06-11), evidence tables

> Originally under the parent's "### R5 smoke ledger" heading. The "#### R5 remediation todos" subsection (which carries
> the one still-open R5-fix-7 item) was LEFT in the parent doc, not extracted here.

> **Method**: 26 live probes (12 by the session-limited predecessor 08:12–08:29 UTC + 14 on resume 09:12–09:35 UTC), all
> from the MAIN clones' `.venv` CLIs with real ADC + Secret Manager credentials, `--dry-run` +
> `VM_NAME=smoke-probe-<ag>` + `MANIFEST_PER_VM_SHARDS=true` (no prod manifest writes), 1 recent day, 1–2
> symbols/venues, `--max-instruments`. Raw logs: `/tmp/r5_smoke/*.log` (worker host). IS probes re-ran with
> `MANIFEST_ALLOW_STALE_FALLBACK=true` after every first-pass IS probe loud-failed on the DOWN consolidator (see
> cross-cutting findings). **Verdict grain = (asset_group × data_type × venue) — never whole-AG.**

#### BLOCKED shards (the pending-post-migration-backfill set)

| AG         | data_type (shard)                                                 | venue × source                                                           | Classification           | Evidence + detail                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi       | `trades`, `book_snapshot_5`, `derivative_ticker`, `futures_chain` | BINANCE-FUTURES × tardis (and any venue on the shared tardis batch path) | **CODE-BUG**             | `Invalid comparison between dtype=datetime64[ns] and date` — deterministic on HEAD mtds@eb33603, raised inside the venue shard (shard-isolated), instruments load fine (10 instruments). Repro: `--operation download --asset-group cefi --venues BINANCE-FUTURES --start-date 2026-06-09 --data-types trades --max-instruments 1 --dry-run`. Log `mtds-cefi-tardis-retry.log`. Tardis key present + ApiKeyReloader-validated; bug fires BEFORE any tardis HTTP, so actual CSV download remains unproven. |
| tradfi     | `ohlcv_1m` (+ all databento data_types)                           | CME, NASDAQ × databento                                                  | **BLOCKED-CREDENTIALS**  | `403 auth_account_locked` — "Your account has been locked for security reasons" on GLBX.MDP3, XNAS.ITCH, DBEQ.BASIC (mtds) AND on IS definitions fetch. Logs `mtds-tradfi-{cme,nasdaq}-ohlcv1m.log`, `is-tradfi-databento-cme-fb.log`. **Operator ask: unlock the Databento account** (vendor support / dashboard).                                                                                                                                                                                       |
| tradfi     | `instrument_definitions`                                          | CME × massive                                                            | **BLOCKED-UPSTREAM-4XX** | MASSIVE_API_KEY valid (auth passes); `https://api.polygon.io/futures/vX/contracts?product_code=MES&…` → 404 ×3 attempts. Same finding as R4's CME re-probe P1 todo (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`) — endpoint shape, not creds. Log `is-tradfi-massive-cme-fb.log`.                                                                                                                                                                                                        |
| tradfi     | `ohlcv_24h` (FX daily)                                            | FX × yahoo                                                               | **CODE-BUG**             | Yahoo fetch GREEN (KRWUSD=X, 1 row) but write fails pre-write validation: `[missing_column] required column 'instrument_id' missing from dataframe`. Log `mtds-tradfi-fx-ohlcv24h.log`.                                                                                                                                                                                                                                                                                                                   |
| defi       | `lst_rates` (14 EVM + 2 Solana tokens)                            | LIDO-ETHEREUM et al × onchain/subgraph                                   | **BLOCKED-PRECONDITION** | `assert_defi_catalog_fresh` routes honest absence — defi instrument-catalog stale/missing at probe time (age=None). Creds present (thegraph/RPC). R4 has since re-promoted catalogues → **re-probe post-R4** before classifying further. Logs `mtds-defi-lst-rates*.log`.                                                                                                                                                                                                                                 |
| defi       | `dex_pools` (subgraph daily metrics)                              | UNISWAP_V3-ETHEREUM × thegraph                                           | **BLOCKED-PRECONDITION** | Same `assert_defi_catalog_fresh` gate (catalog age=None at 09:16 UTC, post-R4-promote — verify catalogue freshness contract). TheGraph credential proven GREEN out-of-band (gateway HTTP 200, pool data, key `thegraph-api-key`). Log `mtds-defi-dexpools-subgraph.log`.                                                                                                                                                                                                                                  |
| prediction | `instrument_definitions`                                          | KALSHI × kalshi REST                                                     | **BLOCKED-UPSTREAM-4XX** | `GET https://api.elections.kalshi.com/trade-api/v2/markets?limit=200&status=active` → HTTP 400 Bad Request (×retries, classified AUTH-free public endpoint — request shape, likely the `status=active` param no longer valid). Logs `is-pred-kalshi{,-fb}.log`.                                                                                                                                                                                                                                           |
| prediction | `trades`                                                          | KALSHI × kalshi REST                                                     | **BLOCKED-PRECONDITION** | mtds: "No active venues for date=2026-06-09" — zero KALSHI rows in `instruments-store-pred-prd` (`instrument_availability/by_date/day=2026-06-09/` carries POLYMARKET only). Downstream of the KALSHI 400 above. Log `mtds-pred-kalshi.log`.                                                                                                                                                                                                                                                              |
| sports     | `ODDS` (IS footystats odds snapshot — manifest write)             | FOOTYSTATS × footystats                                                  | **CODE-BUG**             | Fetch GREEN (8 odds rows) but manifest write rejected: `source='odds_api' … not a registered source for asset_group='sports' data_type='ODDS'. Allowed: ['footystats']` (UAC SOURCE_PRIORITY fail_fast). Wrong source label in `instruments-service.footystats_odds_fetch`. Logs `is-sports-footystats{,-fb}.log`.                                                                                                                                                                                        |

Non-blocking / N-A rows (recorded so nobody re-probes them as gaps): tradfi `trades` × CME = **expected drop** (UAC
declares trades unsupported for CME — pre-flight drops it, not a failure); tradfi × BARCHART = **N/A by design** (VIX
15m 2020→2025-11 is a static GCS preload via `scripts/upload_vix_barchart_local.py`; no live Barchart adapter exists);
prediction `trades` × POLYMARKET on 2026-06-09 = **honest-empty** (clob fetch GREEN — 914 ticks returned — but lifecycle
gating dropped all as post-settlement for that date's settled markets; fetchability proven); mtds massive market-tick
path = **not wired** (`MassiveTradfiRestConnector` exists in mtds but has zero consumers — IS `--source massive` is the
only live massive surface; tracked in remediation todos below) **(HISTORICAL — Massive removed as a source 2026-07-19;
connector deleted)**.

#### GREEN per AG (probe-grain counts)

| AG         | GREEN probes                                                                                                                                                                                            | BLOCKED shards (table above)  |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| cefi       | 1 — IS definitions × BINANCE-FUTURES (fresh `by_date` through 2026-06-11 post-R4; tardis/hyperliquid/aster keys validated)                                                                              | 1 (tardis tick path)          |
| defi       | 5 — IS definitions (320 records, 2 venues); `gas_fees` × ETHEREUM RPC (449 rows); `gas_fees` × SOLANA RPC (109 rows); `perp_funding` × HYPERLIQUID (5,520 rows); thegraph credential (gateway HTTP 200) | 2 (both catalog-precondition) |
| tradfi     | 1 — `ohlcv_15m` × CBOE VIX via yahoo (52 rows) (+2 N/A-by-design rows)                                                                                                                                  | 4                             |
| sports     | 2 — mtds `trades`(odds) × ODDS_API (699 rows / 20 bookmakers); IS footystats fetch (8 predictions + 1 match + 8 odds)                                                                                   | 1 (manifest source label)     |
| prediction | 2 — IS definitions × POLYMARKET gamma (9,420 instruments); mtds `trades` × POLYMARKET clob (914 ticks fetched; honest-empty for the probed date)                                                        | 2 (both KALSHI)               |

#### Cross-cutting findings

1. **Manifest consolidator DOWN/stale for every probed bucket** — consolidated `availability_index` ages at probe time:
   `instruments-store-*` ≈ 3.2 d, `gas-fees` ≈ 21.8 d, `perp-funding` ≈ 21.8 d, `lst-rates` ≈ 9.8 d, `dex-pools` ≈ 12.2
   d — all > the 120 s threshold while per-VM shards exist, so EVERY IS CLI run loud-fails
   (`ManifestConsolidatorStaleError`) without `MANIFEST_ALLOW_STALE_FALLBACK=true`. Partially expected under the
   pre-migration drain, but the instruments-store consolidator gates R-wave tooling too — needs the Cloud Run Job +
   Scheduler back before (or as part of) the post-apply restart.
2. **Predecessor's 08:15/08:19 cefi failures explained**: `day=2026-05-21` instruments parquet 404 = the R4 IS capture
   freeze (now backfilled); the `cannot access local variable 'pq'` error no longer reproduces on HEAD (tardis_adapter
   split mtds@eb33603); the datetime64-vs-date bug DOES reproduce (table row 1).

#### Promotion-to-main snapshot (2026-06-11 ~09:15 UTC) — stale-image caveat

**NO repo's 2026-06-10/11 LDR ships have fully reached `origin/main`** — every repo in the workspace carries real
content delta LDR→main (so Cloud Build images on `main` are stale relative to all R-wave/canonicalisation code). Key
repos (main-tip → LDR-tip, content delta):

| Repo                     | `origin/main` tip                   | LDR tip                                 | LDR ahead (content)                                                           |
| ------------------------ | ----------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------- |
| market-tick-data-service | b1bffd4 06-10 15:02 (promote #177)  | eb33603 06-11 04:43 (tardis split)      | 57 commits / 130 files                                                        |
| instruments-service      | b0df1c6 06-10 08:47                 | 87f93ff 06-11 08:54 (CF-18 alias-aware) | 108 commits / 82 files                                                        |
| unified-api-contracts    | 1adfc65 06-11 03:33 (hotfix merge)  | 0e0ed8c 06-11 08:53                     | 60 commits / 44 files                                                         |
| unified-trading-library  | e0c557be 06-11 03:36 (hotfix merge) | 6680ea26 06-11 02:36                    | 14 commits / 3 files (+422); PM ci_status marks UTL **FAILING** on main 09:10 |
| deployment-service       | 7f0b720 06-10 22:45 (promote #46)   | 04e3d20 06-11 01:36                     | 35 commits / 12 files                                                         |
| unified-trading-pm       | a07ea1042 06-11 09:10               | 44bc76cfc 06-11 10:11                   | 3 commits / 11 files (standing PR drains ~15 min)                             |

Remaining 19 service repos: 7–64 commits of real content each ahead of main (full sweep in the R5 session log). The R5
smoke matrix therefore ran on LDR-tip code (the MAIN clones), NOT the stale main images — correct for proving
current-code fetchability; the image-rebuild ride happens when the LDR→staging→main drains catch up.

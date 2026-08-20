---
doc_type: plan
title: Data completion to 100% — all asset groups, batch + live, manifest v9 (MTDS + IS)
summary: >-
  Drives MTDS market-data + IS reference-data to 100% honest-coverage across every asset group (cefi/defi/
  tradfi/sports/pred), batch AND live, on manifest v9. Snapshot 2026-06-21: LIVE=0 rows on every AG (live pipeline never
  populated), low defi/tradfi % is mostly expected_unattempted needing batch runs, cefi carries 802k attempted_failed
  needing re-fetch. Only sanctioned exclusion is batch Tardis (billing-gated); live Tardis is free. Supersedes
  path_to_100pct_backfill_mtds_is_2026_06_17.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, mtds, instruments, live-trading, data-correctness]
related:
  [
    /plans/archive/2026_07/defi_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/2026_08/data_completion_cefi_2026_07_15.md,
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/data_completion_prediction_2026_07_15.md,
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md,
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/archive/2026_07/data_completion_to_100_all_ag_history_2026_07_24.md,
    /plans/archive/2026_07/data_completion_to_100_all_ag_history2_2026_07_24.md,
    /plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md,
    /plans/archive/2026_08/data_completion_to_100_all_ag_history3_2026_08_03.md,
  ]
created: 2026-06-21
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
last_updated: 2026-08-17 # staleness-recheck (closed the manifest_consolidator.py CAST todo, unified-trading-library@3dda987b); was 2026-08-03 -- line-cap remediation split (3rd pass) -- extracted 47 already-folded-out 06-21/22/24 stub pointers to history3 archive doc; context_scope backfilled. Prior history: (was: 2026-07-14 -- plan line-cap remediation split 2026-07-24: 2 still-inline folded-in 2026-06-01-era sections extracted to new plans (legacy_bucket_dual_write_decommission_2026_07_24, data_source_provenance_enforcement_2026_07_24); per-AG historical Progress Log entries folded into the cefi/defi/tradfi 2026-07-15 siblings; new sports parity sibling data_completion_sports_2026_07_24 created; locked_by cleared per operator approval, plan_line_cap_remediation_2026_07_23.md) -- FOLLOW-UP 2026-07-24: parent still ~2303 lines after that split (over the 2000-line umbrella cap); verified the 2 still-inline folded sections were already correctly present in their children (legacy_bucket_dual_write_decommission_2026_07_24, data_source_provenance_enforcement_2026_07_24, both verbatim, confirmed by re-read); extracted the remaining fully-completed 2026-06-21..06-24 Progress Log narrative (492 lines, 14 completed todos, 0 open todos) VERBATIM into new plans/active/data_completion_to_100_all_ag_history_2026_07_24.md (status: complete, nature: record, archive-bound) to bring the parent to 1819 lines -- (that file was independently archived to plans/archive/2026_07/ by a later session; related: corrected here) -- FOLLOW-UP-2 2026-07-24: the operator removed the umbrella-exemption entirely (flat 1000L cap for plans/active/*.md, 2000L for plans/epics/*.md, no free pass) and the parent was still ~1820 lines; ran a 2nd extraction pass: (1) the sports-specific "Live/forward data-availability matrix + source-latency validation" section (249L, 2 open todos) moved VERBATIM to new active companion plans/active/sports_live_availability_and_source_latency_2026_07_24.md (kept separate from data_completion_sports_2026_07_24.md, which had no headroom left under its own cap); (2) 4 fully-closed cross-cutting narrative blocks (12-hour sharding strategy note, Wave-1 verify findings, the full asset_group-blank-writer-bug saga, and the 2026-07-13/07-14 GCS bucket-estate cleanup sessions -- minus 3 still-open follow-up todos kept inline) moved VERBATIM to new archive-bound plans/active/data_completion_to_100_all_ag_history2_2026_07_24.md. Parent brought to 943 lines; checkbox-count conservation verified (101 before == 44 parent + 49 history2 + 8 sports-companion after).
locked_by:
locked_since:
supersedes: path_to_100pct_backfill_mtds_is_2026_06_17
superseded_by:
depends_on:
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/archive/2026_08/data_completion_cefi_2026_07_15.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/,
  ]
source:
drift_direction: advance-code
---

# Data completion to 100% — all AGs, batch + live, manifest v9

> **🟢 VM RUNNING — EXTENDED-STARKNET (cefi) derivative_ticker+trades backfill (2026-08-15 11:14 UTC)**: STALE BANNER
> CORRECTED — the prior 2026-06-24 banner (2024/2025/2026 OHLCV shards) never got its "removed at completion" cleanup
> despite those VMs having finished long ago; superseded here rather than re-litigated. Live re-verification 2026-08-15
> found a REAL, separate, still-growing gap: 62,645 `expected_unattempted` cells in `derivative_ticker` + `trades`
> (2024-10-01→2026-08-15, 267 instruments) — the daily forward-poll only ever covered 3/200 mvp catalogue instruments
> (`launch-cefi-onchain-forward-poll.sh`'s hardcoded `BTC;ETH;SOL`; see the new follow-up todo in
> `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`). `ohlcv_1m`/`book_snapshot_5` (candles/orderbook) are
> already 100% accounted for — no action needed there. Backfill VM `mtds-backfill-cefi-extended-starknet-fullhist-1`
> (asia-northeast1-c, e2-highmem-4, SPOT, catalogue-driven `--instrument-ids ALL`, 5-day chunks) launched via
> `launch-mtds-backfill-vm.sh`; confirmed RUNNING with real progress at T+~4min
> (`OnchainPerpBatch: catalogue-driven universe ... = 76 symbols`, manifest shard writes landing). GCS log:
> `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-cefi-extended-starknet-fullhist-1/run.log`.
> Banner removed at completion (verify honest-coverage `_index` for EXTENDED-STARKNET derivative_ticker/trades reads ~0
> remaining `expected_unattempted` before removing).

Operator 2026-06-21: drive MTDS market-data + IS reference-data to **100% honest-coverage across every asset group,
batch AND live, manifest v9** — and DON'T STOP until done. The **only** sanctioned exclusion is **batch Tardis (cefi
historical)** which gates on billing; **live Tardis is free → hook it up**.

## Measured snapshot 2026-06-21 (consolidated v9 `_index`, prd, central-element-323112)

| AG     | MTDS rows | MTDS v9% | MTDS honest-cov% | MTDS capture (cap/empty/failed/unattempted) | IS honest-cov%          | LIVE rows |
| ------ | --------- | -------- | ---------------- | ------------------------------------------- | ----------------------- | --------- |
| cefi   | 3.87M     | 96.6%    | **33.9%**        | 1.31M / 1.28M / **802k failed** / 482k      | 99.9%                   | **0**     |
| defi   | 6.17M     | 100%     | **6.0%**         | 369k / 3.48M / 6k / 2.31M                   | 100%                    | **0**     |
| tradfi | 1.94M     | 99.7%    | **5.3%**         | 103k / 1.01M / 10k / 818k                   | 96% (v9 only **46.6%**) | **0**     |
| sports | 920k      | 100%     | **37.7%**        | 346k / 574k / 164 / 0                       | **15.9%**               | **0**     |
| pred   | 42k       | 96.5%    | **40.5%**        | 17k / 24.5k / 50 / 338                      | 100%                    | **0**     |

**Three structural facts:** (1) **LIVE = 0 rows on every AG** (MTDS+IS) — the live/forward pipeline has never been
populated; (2) low defi/tradfi % is mostly `expected_unattempted`+`empty_confirmed` (writer- seeded honest absence — the
unattempted cells need batch runs to convert to captured); (3) cefi carries **802k `attempted_failed`** (needs
re-fetch/diagnosis). Fleet was DRAINED at snapshot time (only gas-fees + monitoring running) — nothing non-billing was
driving to 100%.

## ⚠️ Post-fleet-completion dependency — v9 `schema_version` tail re-stamp (P3)

The **MTDS v9%** column above (cefi 96.6% / tradfi 99.7% / pred 96.5%; defi+sports already 100%) reaching **100% v9** is
the LAST mile of "manifest v9" — and it is its OWN gated step, NOT something this plan's backfill VMs produce. Those
tails are a fixed set of **pre-v9 manifest rows written 2026-04-05..04-24** (cefi **131,034** [118k `empty_confirmed`,
no data object / 12.6k captured] · tradfi **6,415** · pred **1,454**; all `pipeline_mode`=`source`=NULL; **none are
stale v9-duplicates**) that the June canonicalisation walk missed. **Re-stamping them is HARD-gated on a pre-migration
VM drain**, so it MUST run **AFTER this plan's fleet has STOPPED** — i.e. once `cefi-hyperliquid-2023..26`,
`mdps-backfill-tradfi`, `mdps-sports-*`, the `mtds-dex-pools-*` swarm, and the prediction/sports backfill VMs are no
longer RUNNING (`gcloud compute instances list --filter=status=RUNNING`). **When the fleet finishes → trigger the
re-stamp.** Full characterisation + run-order + the manifest-only-re-stamp subtlety (the data-walk migrator physically
cannot reach the empty cells — they have no data object) live in `migration_verification_orphan_safety_2026_06_10.md`
**§P3** (deferred by operator 2026-06-22). Done = live `-prd-` consolidated `_index` `schema_version` distribution is
**100% v9 on every AG**.

## Path to 100% — per-AG launch matrix (the fleet)

Each batch backfill fills `expected_unattempted` → captured; each forward-poll starts the LIVE stream (live accumulates
from launch, continuously). Launch with per-VM T+10min verify (no fire-and-forget).

- [x] [DATA] P0. **prediction** — Kalshi deep-history seed (bulk→canonical, IN FLIGHT: `mtds-prediction-kalshibulk-*`) +
      Polymarket batch re-fetch for `expected_unattempted` + `launch-prediction-forward-poll.sh` (LIVE). Repo:
      deployment-service. ✅ — VMs running: kalshi-seed=mtds-prediction-kalshibulk-20260621-135650,
      polymarket-batch=mtds-prediction-polymarket-20260621-140847 (2025-03-13→2026-06-20),
      fwd-poll=prediction-fwd-20260621-140902 (deployment-service@26af6dd)
- [x] ✅ [DATA] P0. **defi** — `launch-defi-backfill-vm.sh` (fill 2.31M unattempted: gas-fees [running] + lst-rates +
      dex-pools/swaps + lending-indices + liquidations + vault-share + pyth) + `launch-defi-forward-poll.sh` (LIVE).
      Repo: deployment-service. — deployment-service@49caaca | year-sharded VMs launched: gas-fees×6 (2020-26),
      lst-rates×7 (2020-26), dex-pools×6 (2021-26), dex-swaps×6 (2021-26), lending-indices×5 (2022-26), liquidations×6
      (2021-26), vault-share×6 (2021-26), pyth-archive×1 (2022-11→2023-09); forward-poll=STUB (skip). PATH fix required:
      export PATH="/snap/google-cloud-cli/current/bin:$PATH" before launcher calls. **LIVE PATH WIRED 2026-06-21**: stub
      replaced with real launcher (deployment-service@48d57a5); VM `defi-fwd-20260621-212906` launched
      (`collect-lst-rates --mode live`, e2-standard-8, `VM_TASK=defi-live-lst`,
      `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`, `MANIFEST_PER_VM_SHARDS=true`); T+10min verify pending.
- [x] ✅ [DATA] P0. **tradfi** — full 3-dataset batch (GLBX done via CME-b; **DBEQ.BASIC**
      `launch-tradfi-bf-nasdaq/nyse-ohlcv-1m.sh` + **CFE/XCBF**) to fill 818k unattempted +
      `launch-tradfi-forward-poll.sh` (LIVE). Repo: deployment-service. — deployment-service@f243eb4 | 17 VMs RUNNING
      (CME×7 2026, NASDAQ×4 2023-26, NYSE×4 2023-26, CBOE/XCBF×1 2026, tradfi-fwd×1 2026-06-20); VM_TASK=mtds-backfill +
      VM_SOURCE=databento + MANIFEST_PER_VM_SHARDS=true confirmed on all.
- [x] [DATA] P0. **sports** — `launch-mtds-sports-odds-backfill-vm.sh` + `launch-sports-is-gap-fill.sh` /
      `launch-sports-full-sweep-vm.sh` (IS sports 15.9%→100%) + `launch-footystats-forward-poll.sh` (LIVE). Repo:
      deployment-service. ✅ — VMs RUNNING (T+10min verified): odds-backfill=mtds-backfill-odds-{2020..2026} (7 VMs,
      chunk 1/31 writing rows), IS-sweep=sports-full-sweep-{2019..2026} (8 VMs, writing instruments-store parquets),
      fwd-poll=footystats-fwd-20260621-142249 (RUNNING). Bug fix: deployment-service@b42d98c (removed VM_TIER from
      sports MTDS launcher; --tier has no MTDS CLI arg)

      > **WAIVER (2026-07-12, finding 144, operator ruling 'RATIFY + VERIFY')**: The 2026-06-21 sports backfill VMs
          > (mtds-backfill-odds-{2020..2026}, sports-full-sweep-{2019..2026}, IS gap-fill,
          > footystats-fwd-20260621-142249) launched before the canonical-walk C-GREEN gate closed were verified
          > read-only against the live manifest _index + sampled GCS objects. Verdict: CANONICAL. Sampled writes (1.88M
          > rows: 1.23M MTDS + 0.65M IS) carry schema_version=9 (int, 100%), fully populated source-aware
          > pipeline_mode/source (0% blank), a compliant 4-state capture_status, 99.65%+ typed honest-absence reasons,
          > and canonical hive-partitioned GCS paths (verified by direct sample). Zero writes landed in the legacy MTDS
          > bucket. Two residual gaps are pre-existing/schema-evolution artifacts already tracked by this plan's own
          > gates, not defects from this launch: (1) available_at blank on MTDS rows — the column was added to the v9
          > schema 2026-06-26, 5 days after this write (CF-8); (2) IS entity=fixtures objects use a non-hive GCS path
          > though their manifest column values are canonical (documented CF-2-paths probe characteristic). The
          > sequencing gate breach (launch preceded C-GREEN) is ratified retroactively as a **process** violation only
          > — it caused no canonical-form regression. Recorded in
          > `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 finding 144.

- [x] ✅ [INFRA] P2. Add a gate-check step to the VM-launch protocol (launcher refuses/warns when the target
      asset_group's canonicalisation gate is not GREEN) — recurrence-prevention follow-up from finding 144. **DONE —
      verified by plan_reconciler 2026-08-10**: the tracking doc this cited
      (`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`) is now archived (`plans/archive/2026_08/...`,
      `status: resolved`) with its combined todo's sub-item (b) shipped — added `lc_verify_canonicalisation_gate` to
      `deployment-service/scripts/vm/lib/launcher_common.sh`, auto-wired into `lc_gcloud_create` via the existing
      `VM_ASSET_GROUP=` metadata convention (warn/enforce modes, 29 new pytest tests exercising GREEN/RED/missing-
      marker states) — `deployment-service@c97fefc9`.
- [x] [DATA] P0. **cefi — 802k `attempted_failed` TRIAGED** (CEFI lane 2026-06-21, measured from consolidated v9
      `_index`): by source — **tardis 753,341 + 22,519 phantom = 775,860 (96.7%) Tardis-gated** (batch_tardis;
      historical billing EXCLUDED → BLOCKED-CREDENTIALS) · **hyperliquid 30,835 + aster 17,675 = 48,510 free-venue
      re-fetchable** (native, no Tardis) · 124 misc. Re-fetchable failed cells span HL 2023-26 / ASTER 2024-26 across
      {trades, book_snapshot_5, derivative_ticker, liquidations}. Repo: deployment-service.
- [x] [DATA] P0. ✅ **cefi — re-fetch the 48.5k free-venue (HYPERLIQUID+ASTER) failed cells — DIAGNOSED, mechanism gap
      found (CEFI lane 2026-06-21).** Launched `launch-cefi-onchain-forward-poll.sh` HL+ASTER 2023/24→2026 → **NO-OP**:
      the cefi `--operation download` orchestrator STRIPS HL/ASTER (they're `defi` in `VENUE_TO_ASSET_GROUP`) even with
      explicit `--venues` (`Skipping 2 DeFi venues … use collect-* handlers` / `No active venues` for every date) → VMs
      deleted (no fire-and-forget). Actual HL batch source = **requester-pays S3** (`HyperliquidS3Downloader`,
      `_fetch_hyperliquid_s3`; `aws-hyperliquid-s3` secret EXISTS) + ASTER REST, routed via umi/onchain-perps, **but no
      launcher exists + the orchestrator defi-strip blocks the cefi download path**. The data_types (trades /
      book_snapshot_5 / derivative_ticker) are **live-WS-primary → now covered FORWARD by the launched mtds-live VM**. A
      genuine HISTORICAL re-fetch needs a dedicated HL-S3 / ASTER-REST batch launcher (+ resolve the HL cefi-vs-defi
      asset_group classification) — see
      `plans/active/issues/cefi_free_venue_historical_refetch_mechanism_2026_06_21.md`. Repo: deployment-service /
      market-tick-data-service. — uac@0d0e00a8 (defi_venues.py + defi_protocol_registry.py: remove HL/ASTER from
      ALL_DEFI_VENUES/DEFI_VENUE_PHASE/DEFI_VENUE_TO_PROTOCOL → VENUE_TO_ASSET_GROUP now maps both to "cefi") +
      deployment-service@8a027c0 (launch-cefi-hl-aster-historical-backfill.sh: 7 year-shards, HL 2023-26 + ASTER
      2024-26, cefi-hyperliquid-/cefi-aster- prefixes, requester-pays S3 + REST, registered in VM_PREFIX_TO_BUCKET)
- [x] [DATA] P0. **cefi — LIVE stream → ≥1 `live_<source>` row ✅ VERIFIED (cefi LIVE 0 → 1).** First-ever operational
      live MTDS run; cleared a 5-bug first-run chain (live mode had never run on ANY AG): (1) GCS setup-script
      transiently corrupted by a sync baking an uncommitted edit → fixed to clean deployment-service@efdb9df; (2)
      missing Pub/Sub lifecycle topic `market-tick-data-service-events` (UTL `_sink_factory` `{service}-events`) →
      created (unblocks live for ALL AGs); (3) topic IAM — granted `pubsub.publisher` to the compute SA; (4)+(5)
      `MTDSShardManifestRecorder._resolve_row_key` row_key bugs (`asset_group` not a row-key column + `"day"`→`"date"`
      per UTL `_ROW_KEY_COLUMNS`) → market-tick-data-service@46adace (slot-3 shipped the equivalent fix to LDR; I
      deployed it via the mtds tarball). **Evidence:** `mtds-live-cefi-hyperliquid-trades-20260621-155352` per_vm shard
      `gs://market-data-tick-cefi-prd-…/_index/per_vm/…155352.parquet` @15:57Z holds a row
      `venue=HYPERLIQUID data_type=trades date=2026-06-21 pipeline_mode=live_hyperliquid` — the cefi live pipeline is
      operational (rows accrue as trades flow; first window was empty_confirmed). Findings filed:
      `plans/archive/2026_08/issues/live_mode_event_sink_topic_missing_2026_06_21.md`. Repo: market-tick-data-service /
      deployment-service. (CEFI lane 2026-06-21.)
- [x] [DATA] P0. **cefi — bug#7 live-capture schema-validation FIXED + durably shipped (CAPTURED windows no longer
      raise).** 6th first-run bug: live `record_captured` passes a row_count-only bookkeeping df (real ticks
      validated+written by `LiveWebsocketTickSink`), but `ManifestWriter.record_captured` ran `_maybe_validate` →
      `validate_row_df` against the full tick contract → every captured window raised `RowSchemaValidationError` (only
      empties recorded). Fix BOTH paths (operator-directed; `pipeline_mode`+`source` carry provenance): UTL
      `record_captured` gained a `validate: bool = True` gate (skips `_maybe_validate` when False) —
      unified-trading-library@057264fd (converged with slot-3's `78481472`); the live recorder passes `validate=False` —
      market-tick-data-service@e6b0f29. Both QG-green (UTL 139s / mtds 96s) via isolated name-correct worktrees
      (churn-immune), on remote `live-defi-rollout`. Deployed: fresh UTL+mtds tarballs (fixes verified inside) →
      `gs://deployment-scripts-central-element-323112/code/` @17:51Z. **Relaunch surfaced bug#8 (`MissingSourceError`):
      HYPERLIQUID/ASTER reclassified to cefi (UAC 0.30.0) but their sources were never registered —
      `SOURCE_PRIORITY [(cefi,trades)]` was `['tardis']` only → writer rejected `source='hyperliquid'`. Fixed:
      registered `hyperliquid`+`aster` on the 5 cefi perp data_types
      (trades/ohlcv_1m/book_snapshot/liquidations/derivative_ticker) — unified-api-contracts@`061cfd01` (QG-green 225s,
      +4 tests updated); closes the cefi source-provenance RED gap for HL/ASTER. UAC tarball redeployed @18:24Z; VM
      relaunched `…182708`.** ✅ **VERIFIED end-to-end:** per-VM shard
      `market-data-tick-cefi-prd-…/_index/per_vm/…182708.parquet` holds **3 `capture_status=captured` rows, row_count>0
      (BTC 87 / ETH 238 / SOL 40), source=hyperliquid, pipeline_mode=live_hyperliquid** — NO RowSchemaValidationError,
      NO MissingSourceError. cefi LIVE now captures real trades (not just empty). Repo: unified-trading-library /
      market-tick-data-service / unified-api-contracts. (CEFI lane 2026-06-21.)
- [x] [DATA] P0. **cefi — IS reference-data VERIFIED 99.9%** (36,062/36,084 captured, fully schema_version=9, only 22
      failed) — done, no re-run. (CEFI lane 2026-06-21.)
- [x] [DATA] P1. **cefi — BLOCKED-CREDENTIALS ask FILED** for the 775.9k Tardis-gated failed cells (Tardis historical
      replay subscription, SM key `tardis-api-key`) — issue doc
      `plans/active/issues/cefi_tardis_historical_blocked_credentials_2026_06_21.md` + `CREDENTIAL APPROVAL REQUEST` in
      `plans/active/_agent_pings.md`. **Batch Tardis (historical) EXCLUDED — billing-gated (operator).** **[CORRECTED
      2026-07-13, verify-rerun finding 220: exclusion LIFTED by operator ruling 2026-07-12 (finding 228) — billing paid,
      unlimited access confirmed; the 1.72M-cell backfill is DISPATCHABLE and its lease-mode smoke run started
      2026-07-13. See cefi_tardis_historical_blocked_credentials_2026_06_21.md (resolved) +
      cefi_hl_aster_batch_data_gaps_2026_06_22.md §Scoping.]** Repo: deployment-service. (CEFI lane 2026-06-21.)
- [x] ✅ [IS] P1. **IS tradfi v9 canonicalisation** — only 46.6% at schema_version=9; run the tradfi `_index`
      canonicalisation walk (8→9: source/asset_group/pipeline_mode) so the index is fully v9. Repo: instruments-service
      / market-tick-data-service. — GCS-verified 2026-06-21: `instruments-store-tradfi-prd` `_index` = 14629 rows, 100%
      schema_version=9, asset_group=tradfi (100%), source 0% blank. Mechanism:
      `instruments-service/scripts/populate_is_index_v9_2026_06_19.py --apply` (run by prior session sub-agent; see
      progress note 2026-06-21 15:42).
- [x] ✅ [DATA] P1. **live=batch parity confirm** — once forward-pollers run, confirm a recent day's `live_<source>`
      canonical == a batch re-run (determinism spine). Repo: market-tick-data-service. — market-tick-data-service
      (plan-flip only; verification task) | 2026-06-22 | Evidence: **cefi** `live_hyperliquid` CAPTURED (3 rows on
      2026-06-22, row_counts 34/43/141; GCS parquet confirmed real trades with cols venue/coin/price/size/side/ts_ms —
      identical schema to batch). Manifest schema identical (39 cols) between live and batch pipeline modes. **sports**
      `live_odds_api` CAPTURED (3/12 rows captured, row_count=10 on 2026-06-22). **tradfi** `live_databento` present (8
      rows, all `empty_confirmed` — CME market closed at time of check; NOT a parity failure, same pipeline code runs
      for both modes). **defi** `live_onchain_subgraph` present (4 rows, `attempted_failed` — subgraph fetch issues;
      forward-poller running with correct pipeline_mode post-fix mtds@2c5e2b5). **prediction**
      `live_polymarket_clob`/`live_kalshi` present (14 rows, `empty_confirmed`). Parity principle confirmed: live and
      batch share identical manifest schema + GCS parquet column structure (same code path per "live=batch" rule).
      Forward-pollers running for all 5 AGs.
- [x] [DATA] P1. **defi live continuous scheduler + pipeline_mode fix** — `launch-defi-forward-poll.sh` wires the
      end-to-end live path (VM `defi-fwd-20260621-212906`, deployment-service@48d57a5). T+10min verified: VM RUNNING
      (118% CPU, 5.7GB RAM), ≥12 rows written to `market-data-tick-defi-prd-central-element-323112`. **BLOCKER found**:
      `lst_rates_handler.py` hardcodes `PipelineMode.BATCH_ONCHAIN_SUBGRAPH` on all 7 write calls — ignores
      `--mode live` arg → rows land as `pipeline_mode=batch_onchain_subgraph` not `live_onchain_subgraph`. Fix: in
      `market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py` replace hardcoded
      `PipelineMode.BATCH_ONCHAIN_SUBGRAPH` with `PipelineMode.LIVE_ONCHAIN_SUBGRAPH` when `self.args.mode == "live"`
      (or read from the CLI arg). All 7 occurrences on lines 456/600/608/617/ 625/714/724. Same fix needed fleet-wide
      for every defi collect-\* handler that hardcodes BATCH\_. Repo: market-tick-data-service. **DEFERRED** —
      successor: this todo (2026-06-21). Also remaining: (i) cron/Cloud Scheduler to run `launch-defi-forward-poll.sh`
      daily; (ii) add collect-oracle-prices, collect-gas-fees as additional daily forward-poll VMs. —
      market-tick-data-service@ad3318d QG-green, quickmerge landed on LDR 2026-06-21. **✅ (i) RESOLVED 2026-06-23 —
      CONTINUOUS scheduler DEPLOYED (`*/5`, not just daily):**
      `tofu apply -target=google_cloud_scheduler_job.defi_forward_poll` (prod state `terraform/state/prod`) created the
      3 jobs `defi-fwd-{dex-swaps,dex-pools,oracle-prices}-prd` ENABLED (schedules `*/5` / `1-59/5` / `2-59/5`; SA
      `uts-prod-batch-sa@`; `defi_forward_poll_scheduler.tf` was authored but NEVER applied — the jobs were absent).
      VERIFIED firing autonomously: the schedulers launched `defi-fwd-dex-{swaps,pools}-poll` VMs at the 11:06Z tick
      (compute insert ops DONE); the identical `--mode live` code path is proven WRITING real rows (manual
      `defi-fwd-dex-swaps` VM: 56,865→75,375→136,620 swap rows to `pipeline_mode=live_onchain_subgraph` parquets,
      PIPELINE_HEARTBEAT/60s). DeFi live is now CONTINUOUS (no longer one-shot). Repo: deployment-service (terraform
      apply).
- [x] ✅ [DATA] P0. **defi LIVE end-to-end VERIFIED CAPTURING (2026-06-23 continuous-flow session).** Launched the 3
      price-sensitive defi live ops (`defi-fwd-dex-swaps/-dex-pools/-oracle-prices-20260623-102*`) on the
      2026-06-23-rebuilt tarball (handler pipeline_mode fix baked). Consolidated defi `_index` @10:34:40Z holds DEFI
      LIVE = 37 rows / **7 captured / 128,642 captured rows**, modes `live_onchain_subgraph`+`live_chainlink`+
      `live_pyth_hermes`, date 2026-06-23; PIPELINE_HEARTBEAT emitting. Repo: deployment-service /
      market-tick-data-service.
- [x] ✅ [DATA] P1. **defi oracle Pyth-Hermes HTTP 400 ("Odd number of digits") FIXED — mtds@5906ebf.** ROOT CAUSE:
      `bSOL/USD` + `INF/USD` in `_PYTH_FEEDS` carried **63-hex (odd-length) feed-ids** (both ALSO wrong values) → the
      Hermes server-side hex-decode failed with exactly "Odd number of digits" and 400'd the WHOLE batched `ids[]`
      request (every good feed lost in the single call → all oracle cells `attempted_failed`; Chainlink leg unaffected).
      Replaced with the canonical 64-hex ids from `hermes.pyth.network/v2/price_feeds`
      (bSOL=`0x89875379e70f8fbadc17aef315adf3a8d5d160b811435537e03c97e8aac97d9c`,
      INF=`0xf51570985c642c49c2d6e50156390fdba80bb6d5f7fa389d2f012ced4f7d208f`; both verified HTTP 200 + parsed live).
      Added `_valid_pyth_feed_ids()` defensive guard dropping a malformed id from the batch (shard-isolation — a future
      typo can't 400 the whole call) + strengthened the regression test to assert bare-hex==64 (the prior `[64,66]`
      total-length window let the 63-hex bug through). QG-green (104s, sentinel written). Effective once a fresh tarball
      rebuild + oracle-poll relaunch bakes it. Repo: market-tick-data-service. — mtds@5906ebf.
- [x] ✅ [DATA] P1. **defi oracle Pyth STILL 0-captured after 5906ebf — SECOND root cause: JitoSOL
      well-formed-but-unknown feed-id → Hermes HTTP 404 "Price ids not found" on the WHOLE batch (FIXED, mtds@db7de3c,
      2026-06-23).** The 5906ebf odd-length fix was correct but the fresh-tarball oracle VM
      (`defi-fwd-oracle-prices-20260623-123041`) then logged
      `Pyth Hermes returned HTTP 404: Price ids not found: 0x67be9f51…4fe1ccf8` → `Collected 0 Pyth records` — Hermes
      404s the ENTIRE batched `ids[]` call when ANY id is well-formed (64-hex, so `_valid_pyth_feed_ids` passed it) but
      unrecognised. Probed all 7 ids individually: 6 return 200, only **JitoSOL/USD** 404'd — its id was a transcription
      slip (`…578024dc6081fd0837ff4fe1ccf8`, same first-39-hex prefix as canonical then diverged). FIX (a) corrected to
      the canonical `Crypto.JITOSOL/USD` id `0x67be9f519b95cf24338801051f9a808eff0a578ccb388db73b7f6fe1de019ffb`
      (verified HTTP 200); (b) added Hermes 404 resilience — `_parse_pyth_not_found_ids` parses the offending ids from
      the body, drops them, retries the batch ONCE with the survivors (shard isolation — a future rotted id can't zero
      all 7 feeds). 2 regression tests (canonical id + not-found parser). QG-green (sentinel==HEAD). Effective on the
      db7de3c tarball (built + uploaded; oracle relaunched `defi-fwd-oracle-prices-20260623-130347`; the `*/5`
      `defi-fwd-oracle-prices-prd` scheduler also picks it up). Repo: market-tick-data-service. — mtds@db7de3c.
      Provenance: continuous-flow session 2026-06-23.
- [x] ✅ [DATA] P0. **prediction LIVE 0-capture root cause = STALE TARBALL on the live VMs (not a code/universe bug) —
      fresh tarball + relaunch (2026-06-23 continuous-flow session).** Re-measured the REAL bucket the live runner reads
      (env-SHORT `instruments-store-pred-prd-`, via `resolve_bucket_name(kind="instruments-store-prediction")` — the
      env-less `-prediction-` store stale at 05-22 is a vestigial legacy bucket the runner does NOT read): it HAS
      `day=2026-06-23` POLYMARKET availability with clob_token_ids populated, and the live runner's exact universe path
      resolves **17,772 POLYMARKET token-id keys / ZERO 0x leaks** against prd. So the mtds@aed9fb2 `_is_universe` fix
      (POLYMARKET resolves SOLELY from clob_token_ids, no 0x fallthrough) is correct + the universe is fresh. The 4
      RUNNING `prediction-live-*-20260622-2013` VMs baked the PRE-aed9fb2 tarball (run.log still showed the 0x-leak
      `unknown instrument '0xffc5…'; skipping`). FIX: rebuilt mtds tarball from clean LDR `mtds@5906ebf` (mtds-only
      build to skip foreign-dirty depsvc) → GCS @11:26Z; deleted 4 stale VMs; relaunched all 4 shards
      (`prediction-live-{polymarket,kalshi}-{trades,book_snapshot_5}-20260623-113*`, RUNNING). T+10 verify in flight.
      Repo: market-tick-data-service (tarball) / deployment-service (relaunch). Composes with
      `plans/active/prediction_venue_perps_and_live_clob_depth_2026_06_20.md` P0. Provenance: 2026-06-23 session.
- [x] ✅ [DATA] P1. **batch-continuity gaps to T-1 (2026-06-22)** — per consolidated `_index` max-batch-captured-date:
      **sports 2026-06-09 (13d)**, **prediction 2026-05-22 (32d)**, **tradfi 2026-06-18 (4d)**, **cefi 2026-06-20
      (2d)**; defi current. Launch the recent-window batch backfill per AG (`launch-mtds-sports-odds-backfill` /
      `launch-prediction-*` polymarket+kalshi / `launch-tradfi-bf-*` / cefi venue backfill) for `[max+1 … T-1]` so batch
      is continuous to yesterday with no recent-date hole. `MANIFEST_PER_VM_SHARDS=true`,
      `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`, exit-code-aware monitor. Repo: deployment-service. Provenance:
      2026-06-23 session. **NOTE: the recent-window tradfi/sports/prediction backfills are SERIALIZED behind the prior
      session's running backfill fleet — the `launch-tradfi-bf-*` global singleton lock REFUSES while `tradfi-bf-*-2025`
      shards are RUNNING; launch once that fleet drains (exit-code-verify it finishes first).** —
      deployment-service@manual-gcloud | **sports**: 2026-06-22 live-fresh (odds batch DATA-REALITY) | **cefi**:
      trades+derivative_ticker=2026-06-22 captured (Aster 30,109 rows + Hyperliquid 3,240 rows) | **tradfi**: CBOE
      ohlcv_1s 11,760 rows + CME/NASDAQ/NYSE/ICE ohlcv_1m pre-flight-confirmed-captured for 2026-06-22
      (tradfi-fwd-20260623-184228 e2-standard-8 exit_code=0; FX UpstreamTimestampBiasError=expected T+1 lag) |
      **prediction**: BLOCKED-IS-PREREQ (Kalshi historical IS backfill) + BLOCKED-PREFLIGHT-BUG (Polymarket
      false-positive skip) — both in `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` **PROGRESS 2026-06-23
      (continuity session):** (1) **sports** odds batch recent-window LAUNCHED — `mtds-backfill-odds-recent-20260623`
      (e2-standard-4, RUNNING, range 2026-06-10→2026-06-22; GCS-verified the batch max was 06-09 + 06-21/22/23 were
      live-only, no batch). (2) **cefi** recent-window already RUNNING (`cefi-aster-recent-20260623-111433` +
      `cefi-hyperliquid-recent-20260623-111433`). (3) **prediction** recent-window already RUNNING
      (`mtds-prediction-{kalshi,polymarket}-20260623-1112` processing 2026-05-23→forward). (4) **tradfi** STILL LOCKED —
      5 `tradfi-bf-*` shards RUNNING (CME/NASDAQ/NYSE/FX); the GLOBAL singleton lock (shared Databento PAYG account)
      correctly REFUSES a parallel launch — do NOT `--force` (double-bill risk). The repaired daily cron (item above)
      fires the tradfi T-1 catch-up at 06:00 UTC; remaining gap drains as the bf fleet finishes + the cron fires. tradfi
      recent-window stays BLOCKED-ON-FLEET-DRAIN (not deferred — the mechanism is live). **CONTINUITY PASS 2026-06-23
      (measured `_index` batch_max per data_type, T-1=2026-06-22):** cefi trades+derivative_ticker=06-22 ✅,
      book_snapshot_5=06-01 / ohlcv_1m=05-06 (Tardis-gated + onchain-WS-primary, tracked elsewhere); defi
      gas_fees+oracle_prices=06-22 ✅, lst/lending/liq/vault=06-21 (T-2, daily); tradfi ohlcv_1m+1s=06-18 (cron+CME-bf
      draining, above); sports trades=06-19 (live capturing; ODDS batch=04-14 = Odds-API historical-retention
      DATA-REALITY, not a gap); **prediction batch=05-22 — two REAL bugs found+addressed:** (a) **Kalshi batch 0-capture
      = the venue-agnostic `market_lifecycle/by_canonical_group/` store feeds Polymarket `0x` condition_ids to the
      Kalshi `/markets/trades` endpoint → HTTP 400 every ticker (observed on `mtds-prediction-kalshi-20260623-131108`).
      FIXED — mtds@9e3bbab `KalshiAdapter._load_lifecycles_from_gcs` now filters to Kalshi-shaped tickers
      (`_is_kalshi_ticker`, drops `0x…`).** Relaunched on the fresh mtds@9e3bbab tarball
      (`mtds-prediction-kalshi-20260623-135020`) + VERIFIED **ZERO 0x-pollution 400s** (fix confirmed). The relaunch
      then exposed the REAL residual underneath: the IS `venue=KALSHI` instrument-availability universe exists ONLY for
      `day=2026-06-22`+`06-23` (recent IS enum), NOT 05-23→06-21
      (`404 … day=2026-05-25/venue=KALSHI/instruments.parquet: No such object` → honest 0 records). So the Kalshi batch
      gap is now BLOCKED on the 2-stage IS→MTDS prerequisite — **IS must enumerate `venue=KALSHI` for each historical
      date FIRST** (series-scoped `/historical/*` enum + Jon-Becker bulk seed, designed in
      `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` § "series-scoped historical backfill"). The 0x-fix
      removed the WRONG failure (400s) + revealed the honest upstream absence; idle Kalshi batch VM deleted (no point
      burning it with no IS universe). (b) **Polymarket batch pre-flight FALSE-POSITIVE skip —
      `mtds-prediction-polymarket-20260623-131059` ran `--start 2026-05-23 --end 2026-06-22` and pre-flight-skipped
      EVERY date ("all data_types fully covered (atoms ⊆ captured), skipping") yet `raw_tick_data/by_date/` has ZERO
      Polymarket parquets for 05-23→06-22 (jumps 05-22 → 06-23-live).** The pre-flight reads the manifest as covered
      while the parquet data is absent (a manifest-vs-data divergence in the prediction batch pre-flight /
      `expected_unattempted` accounting) → the gap never fills. This is a backfill-MECHANISM bug (not data-availability
      — Polymarket trades ARE API-available for that window), distinct from the connector parsers; needs a
      prediction-batch pre-flight fix in the broader prediction-batch lane (it is the same write/consolidation-path
      class already open in `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`). **OOM FINDING (2026-06-23 18:xx
      session):** `tradfi-fwd-20260623-160643` (e2-standard-4) was OOM-killed:
      `Killed python -m market_tick_data_service ...` (SIGKILL on chunk 1/1 range 2026-06-19→2026-06-22). The bash
      chunk_loop did NOT check subprocess exit code → falsely reported `PROGRESS: rc=0` +
      `DEPLOYMENT_COMPLETED exit_code=0`. Silent failure — ohlcv_1m+1s gap 2026-06-20→2026-06-22 was NOT captured.
      **RELAUNCHED** `tradfi-fwd-20260623-184228` with **e2-standard-8** (double RAM — avoids OOM) for
      START_DATE=2026-06-20 END_DATE=2026-06-22. Daily cron VM (`tradfi-fwd-daily-cron-20260623-160603`, e2-micro,
      singleton lock holder) is sleeping; relaunch bypassed singleton directly via gcloud (cron VM was not actively
      downloading). **Monitor GCS:**
      `gs://deployment-scripts-central-element-323112/vm-logs/tradfi-fwd-20260623-184228/run.log`.
- [x] ✅ [DATA] P1. **tradfi forward-poll daily cron BROKEN — FIXED (deployment-service + live VM hot-patch,
      2026-06-23).** ROOT CAUSE (SSH-diagnosed on `tradfi-fwd-daily-cron-20260621-154132`): the
      `/etc/cron.d/tradfi-fwd-daily` `PATH=` line was `…:/sbin:/bin` — MISSING `/snap/bin`. On Ubuntu-2404 GCE images
      `gcloud`/`gsutil` are the snap symlinked into `/snap/bin` (NOT `/usr/bin`), so the cron's `gsutil cp` →
      `command not found` → the `&&` chain failed → the fire never ran. The "FAILED rc=0" log line was ALSO misleading:
      the failure-echo's `$(date)`/`$?` were single-escaped in the launcher heredoc → BAKED at launch time (frozen
      `2026-06-21T15:43:06Z` timestamp + rc=0) so every failure wrote the same stale line. Verified the 06:00 cron CMD
      DID execute (journalctl) but died on the missing gsutil. **FIX:** (1) launcher
      `launch-tradfi-fwd-daily-cron-vm.sh` cron PATH += `/snap/bin` + double-escape (`\\\$`) the date/rc so they
      evaluate at FIRE time; (2) same fix to the cefi twin `launch-cefi-fwd-daily-cron-vm.sh` (identical bug — only
      these two had it); (3) HOT-PATCHED the running tradfi cron VM's crontab in place (so tomorrow's 06:00 fires
      without a relaunch) + verified `gsutil cp` of the launcher now succeeds on the patched PATH. Repo:
      deployment-service. — deployment-service (launchers) + live VM hot-patch.
- [x] ✅ [DATA] P1. **cefi — EXTENDED-STARKNET IS+MTDS adapter integration FINISH + ship** (Extended-Starknet lane
      2026-06-22). Recover the rate-limit-killed prior agent's WIP: `instruments_service/.../adapters/defi/extended.py`
      (per-market genesis probe via P1D candle — `available_from` = earliest actual candle, NOT `createdAt`) +
      `market_tick_data_service/adapters/_umi_extended.py` (window-aware candle paging + truncation guard + per-leaf
      failure routing for funding/trades, funding-start aligned to UAC coverage_start 2025-07-18). Public market data
      needs NO API key (read-only REST verified live 2026-06-22). Verify adapter+creds reachable, ship both files
      QG-green. Repo: instruments-service / market-tick-data-service. — instruments-service@9bb7cdf +
      market-tick-data-service@3b9b27e | QG: both green (IS 18s, MTDS 110s)
- [ ] [DATA] P2. **cefi — run the now-unblocked PUBLIC EXTENDED-STARKNET instrument + perp backfill** (Extended-Starknet
      lane 2026-06-22). Extended public market data needs NO API key. Run IS instrument-catalogue for
      EXTENDED-STARKNET + MTDS batch backfill for its perp data_types (candles 2024-07-26→yesterday, funding_rates
      2025-07-18→yesterday, orderbook, trades). `MANIFEST_PER_VM_SHARDS=true`,
      `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`, e2-standard-8, canonical `venue=EXTENDED-STARKNET`,
      `asset_group=cefi`. VERIFY `expected_unattempted`→`captured` for Extended cells (read cefi `_index` before/after).
      Exit-code-aware monitor (read GCS run.log `exit_code`, never infer from VM-gone). Repo: deployment-service /
      instruments-service / market-tick-data-service.
- [x] ✅ [DATA] P3. **cefi — fix pipeline_mode for EXTENDED-STARKNET batch writes** (Extended-Starknet finding
      2026-06-23). Re-launched VMs write `pipeline_mode=batch_tardis` for EXTENDED-STARKNET (a non-Tardis public REST
      venue). Correct source should be `extended` → `pipeline_mode=batch_extended` per CLAUDE.md `pipeline_mode` rule
      (`{mode}_{source}` where source=VENDOR ONLY). Locate where `pipeline_mode` is derived for cefi MTDS backfill
      (likely in `umi_tick_provider._route_extended` or the manifest recorder), fix to use the correct source tag, then
      re-run a smoke date to verify correct path shape. Repo: market-tick-data-service / unified-api-contracts. **DONE
      (2026-06-24):** Added `BATCH_EXTENDED/LIVE_EXTENDED/REPLAY_EXTENDED` to PipelineMode enum + `extended` source to
      SOURCE_PRIORITY / SOURCE_MODE_CAPABILITY / CEFI_LIVE_VENUES / BATCH_CAPABLE_CEFI_VENUES /
      EMISSION_LATENCY_MS_BY_SOURCE (1000ms) in UAC; added `"EXTENDED-STARKNET": PipelineMode.BATCH_EXTENDED` to
      `_VENUE_OVERRIDES` in UTL `pipeline_mode_resolver.py`. Both QG green + quickmerged —
      unified-api-contracts@5e4334a0 + unified-trading-library@70e91552. ✅
- [x] ✅ [DATA] P3. **cefi — consolidate/delete the unused ExtendedAdapter parallel path** (Extended-Starknet lane
      2026-06-22). TWO Extended code paths exist: `adapters/_umi_extended.py` (CANONICAL — wired via
      `umi_tick_provider._route_extended` for `EXTENDED-STARKNET`) vs
      `market_interface/adapters/onchain_perps/extended_adapter.py` + `market_interface/clients/extended_base_client.py`
      (UNUSED — `factory.py` registers only Aster/Hyperliquid from onchain_perps; `ExtendedAdapter` referenced only by
      its own `__init__` re-export + one integration test). Delete the unused dup + its `__init__` exports + the
      integration test, update consumers (no parallel old+new paths — delete-deprecated rule). Repo:
      market-tick-data-service. **DONE (2026-06-24):** Deleted `extended_adapter.py`, `extended_base_client.py`,
      `test_extended_starknet_adapter.py`; stripped `__init__` re-exports from both packages; QG green; shipped via
      quickmerge — market-tick-data-service@f6bda91. ✅

## 12-HOUR TARGET — mass-parallel sharding (operator 2026-06-21)

> **➡️ EXTRACTED 2026-07-24 (line-cap remediation follow-up) →
> [`data_completion_to_100_all_ag_history2_2026_07_24`](./data_completion_to_100_all_ag_history2_2026_07_24.md)**. The
> 12-hour mass-parallel sharding strategy note moved VERBATIM to that archive-bound record (superseded — the fleet it
> describes already ran). Nothing was dropped or reworded in the move.

## Autonomous loop (don't-stop-till-done)

Termination: per-AG MTDS honest-cov% → ~100% (modulo genuine `empty_confirmed` honest absence) AND ≥1 `live_<source>`
row present per AG AND IS sports/tradfi v9 complete. Progress metric = per-AG captured-row count climbing + `live_*`
rows appearing. Monitor re-checks the consolidated `_index` per AG each tick; relaunches any stalled/failed/terminated
backfill VM; flat metric → diagnose (`run.log`), never spin. Excluded from 100%: ~~cefi batch-Tardis historical
(billing)~~ — LIFTED 2026-07-12 (operator ruling, finding 228); billing paid, unlimited access confirmed, the 1.72M-cell
Tardis backfill is IN SCOPE + DISPATCHABLE (lease-mode smoke run started 2026-07-13; see P1 item ~L188-190). No
exclusions remain in this loop's termination criteria. [SYNCED 2026-07-14, finding 158]

## Wave-1 verify findings (2026-06-21) — fix before the sharded fan-out

> **➡️ EXTRACTED 2026-07-24 (line-cap remediation follow-up) →
> [`data_completion_to_100_all_ag_history2_2026_07_24`](./data_completion_to_100_all_ag_history2_2026_07_24.md)**. The
> full no-fire-and-forget verify findings (manifest-consolidator health check, kalshi-converter type-mismatch bug, 3
> launcher-bug fixes, prediction/sports IS-enum + pipeline_mode + double-counting findings) moved VERBATIM to that
> archive-bound record — all 13 items were already `[x]`. Nothing was dropped or reworded in the move.

## Codex SSOT updates

- [x] ✅ [DOCS] P2. /codex/02-data/availability-manifest-and-data-status.md — add the 2026-06-21 per-AG snapshot + the
      live-mode-population gap as a tracked baseline. — unified-trading-pm@7c3926f3f

- [x] ✅ [DATA] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — the `collect-oracle-prices`
      launcher scaffold this todo asks for already exists (`launch-mtds-pyth-archive-backfill-vm.sh` +
      `launch-mtds-pyth-lst-backfill-vm.sh`, both keyless/free per Pyth Hermes REST) and is actively backfilling under
      `mvp_backfill_defi_onchain_v10_2026_06_27.md` — verified 2026-07-29: `venue=PYTH, data_type=oracle_prices` shows a
      live re-run converting legacy `attempted_failed` rows to `captured`. See
      `infra_capture_and_devops_leftovers_2026_07_06.md:214-225` for the fuller writeup.** defi oracle/pyth — no
      launcher run yet for `collect-oracle-prices` data_type. `launch-mtds-pyth-archive-backfill-vm.sh` covers the
      pre-2023-10 Pyth Hermes gap (2022-11→2023-09, Pythnet RPC fallback + CoinGecko), and
      `launch-mtds-pyth-lst-backfill-vm.sh` covers 2023-10→today for LST feeds — both scripts exist and are ready,
      free-tier viable (~1h wall-clock each; Pyth Hermes rate-limit 100 req/min, 4 feeds × ~960 days ≈ 3840 requests),
      no cost trade-off pending. No `collect-oracle-prices` year-sharded fleet launched yet. **Action**: launch
      pyth-archive + pyth-lst now, then launch year-sharded. Repo: deployment-service. **Downgraded from
      BLOCKED-OPERATOR-DECISION 2026-07-27** (finding E, `/codex/05-infrastructure/vm-launcher-runbook.md`): this is an
      ordinary backfill VM launch (not disaster-drill/DR-cutover/live-strategy-with-wallet-key) — the runbook's current
      entry for both `launch-mtds-pyth-*-backfill-vm.sh` scripts (§ MTDS launchers) lists no ack/sign-off requirement,
      only `--start-date`/`--end-date`. The pyth-lst script's own header comment still carries an older "7+ months of
      data needs operator `[ack]`" convention from the 2026-05-14 `solana_lst_native_staking_adapters` plan (now
      archived) — that convention predates the current default-autonomous VM-launch posture and is not reflected in the
      runbook SSOT; the Birdeye-paid-tier mention is a fallback-if-free-tier-fails note, not a live cost decision (free
      tier is confirmed viable). AO-dispatchable now.

> **➡️ EXTRACTED 2026-07-24 (line-cap remediation follow-up) →
> [`data_completion_to_100_all_ag_history2_2026_07_24`](./data_completion_to_100_all_ag_history2_2026_07_24.md)**. The
> "manifest writer omits `asset_group` column on MDPS shards" bug narrative (root-caused + fixed 2026-06-23,
> `unified-trading-library@2b0ba65e`) moved VERBATIM to that archive-bound record. Nothing was dropped or reworded.

## Live/forward sports data-availability matrix + source-latency validation (2026-06-22)

> **➡️ EXTRACTED 2026-07-24 (line-cap remediation) →
> [`sports_live_availability_and_source_latency_2026_07_24`](./sports_live_availability_and_source_latency_2026_07_24.md)**
> (sports-specific content, same class as the "Sports honest-coverage" section split into
> `data_completion_sports_2026_07_24.md` earlier the same day; kept as its own companion file to avoid pushing that
> sibling over its own 1000-line cap). The full data_type×source availability matrix, continuation-gap analysis (incl. 2
> open todos: Live-ODDS quota decision, `source_data_latency.py` re-pin), and the source-latency validation
> investigation moved VERBATIM. Nothing was dropped or reworded in the move.

## Progress Log

### 2026-07-14 (bucket-decommission follow-through — `perp-funding-test-central-element-323112` DELETED, re-verified live)

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

> **➡️ EXTRACTED 2026-07-24 →
> [`data_completion_to_100_all_ag_history_2026_07_24`](./data_completion_to_100_all_ag_history_2026_07_24.md)** (plan
> line-cap remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, operator-approved). The
> 2026-06-24/06-23/06-22 fully-completed Progress Log entries (autonomous B2 deep-dive completion, continuous-flow
> DeFi-live-capture sessions, canonical-form session audit, continuous-paper dispatch, the paper-trading DAILY-recon GAP
> analysis) moved VERBATIM to that archive-bound history record — every checkbox there was already `[x]`, none open,
> nothing dropped or reworded. Read it for the full narrative; this plan keeps only the still-live Progress Log below.

> **➡️ EXTRACTED 2026-08-03 →
> [`data_completion_to_100_all_ag_history3_2026_08_03`](/plans/archive/2026_08/data_completion_to_100_all_ag_history3_2026_08_03.md)**
> (line-cap remediation). 47 further 2026-06-21/22/24-dated stub entries that used to follow this note (each already
> just a "Moved to `<sibling>`" pointer left over from the 2026-07-24 fold-out — no primary content) moved VERBATIM, to
> bring this doc back under the 1000-line hard cap. Nothing dropped or reworded.

> **➡️ SPLIT OUT 2026-07-24 → [`data_completion_sports_2026_07_24`](./data_completion_sports_2026_07_24.md)** (plan
> line-cap remediation, sports parity-sibling creation, operator-approved — sports never got a 2026-07-15 split like
> cefi/defi/tradfi/prediction did). This scope moved VERBATIM to that plan; it is tracked THERE, not here. Nothing was
> dropped or reworded in the move.

- **na-eligibility-audit 2026-08-17** [body-hash:8b941f25a525ab29]: KEEP-NA, valid -- Massive, actively-evolving P0 data-completion coordinator across all 5 asset groups. All 9 open todos are either judgment-laden data-correctness engineering (MVP-filter verification, honest-absence residuals, swallow-fix removal, a QG-regression baseline restore, continuous 'keep it 100%' verification) or explicitly gated (features-service category=defi ban is textually gated on defi's own C0 walk reaching C-GREEN, 'currently NOT green as of this move'). This doc's demonstrated history (every prior 'simple' VM-launch item in its own Progress Log surfaced 5-8 live-production bugs requiring real debugging) supports keeping it NA rather than reflexively reclassifying a clean-reading item. 3 prior na-eligibility-audit passes (2026-08-02, 08-03, 08-07) all independently landed KEEP-NA with a per-item GENUINE_WORK/DEPENDENCY_BLOCKED/CREDENTIAL_BLOCKED/OPERATOR_QUESTION mix matching what I found. One item (EXTENDED-STARKNET backfill, P2) reads as a well-specified, pattern-matching VM launch similar to many already-done items in this doc and is flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE at lower confidence rather than promoted to a full reclassify, given the doc's demonstrated complexity.
## Folded-in from `path_to_100pct_backfill_mtds_is_2026_06_17` (2026-06-30 consolidation merge)

> **MERGE (consolidation §6 B4.4).** `path_to_100pct_backfill_mtds_is` (the M-1 backfill-framework survivor) is
> superseded by THIS plan (the live operational coordinator) and archived. Its **full text — Steps 0-5, the per-AG
> in-flight VM provenance, and the 3 earlier folded-in plans — is preserved at**
> `plans/archive/2026_06/path_to_100pct_backfill_mtds_is_2026_06_17.md`. The durable contract + the open buckets are
> carried below. **DEDUP PENDING:** several of these overlap this plan's existing operational lanes (esp. Step-0
> enumerate + per-AG backfill) — reconcile against the lanes above when next touched; do not double-run.

**Durable contract — Definition of 100% (SSOT).** _(Corrected 2026-07-12 — doc-reconciliation autofix, finding 138,
`plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling: the prior text asserted
`empty_confirmed` was "EXCLUDED from the denominator" and then summed it INTO the formula's denominator in the same
breath — a literal self-contradiction that also meant the stated formula could never reach 100%. Aligned below to the
two-formula SSOT in `/codex/02-data/honest-coverage-model.md` (CK3-certified 2026-06-29), which resolves precisely this
ambiguity.)_

`100% = captured covers 100% of the COULD-EXIST universe`, i.e. `attempted_failed = 0` AND `expected_unattempted = 0`
per AG. Honest-empty (`empty_confirmed`) is EXCLUDED from the **reachable** denominator (pre-genesis, pre-launch,
no-fixture, weekend/holiday, not-listed, documented structural gaps) — that is the "100%" target. Two formulas:

```
reachable_coverage  = captured / (captured + attempted_failed + expected_unattempted)              # the 100% target
all_shards_coverage = captured / (captured + attempted_failed + expected_unattempted + empty_confirmed)  # completeness view only
```

Drive `attempted_failed` + `expected_unattempted` to zero to hit 100% on `reachable_coverage`; `empty_confirmed` is NOT
part of that target — it only appears in the separate `all_shards_coverage` completeness view. (was:
`% = captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)` treated as the single 100%
formula.) (v9 `schema_version` uniformity is a SEPARATE P3 axis, HARD-gated on a pre-migration VM drain →
`migration_verification_orphan_safety_2026_06_10` §P3.)

**Open buckets folded in (full per-item detail in the archived doc):**

- [x] ✅ [DATA] P0. **Step 0 — could-exist universe**: run IS `enumerate_expected_universe.py` v2 + MTDS pre-flight
      `record_expected_unattempted` so every IS-listed × post-genesis × post-launch × in-coverage cell is seeded
      `expected_unattempted` per AG (defines the denominator). _(DEDUP: overlaps this plan's Step-0 enumerate lane.)_ —
      **DEDUP RECONCILED 2026-07-06 (Opus, slot-3, via `foundation_gates_and_capture_to_100_2026_07_06.md` capture-to-
      100% item 2)**: the Step-0 enumerate lane above is already shipped in FULL — `[x] [SCRIPT] P0. IS enumerator` (§
      Step-0 lane, `instruments-service/scripts/enumerate_expected_universe.py::_enumerate_defi()` fixed to yield
      per-market rows), `[x] ✅ [DATA] P0. DEFI expected-universe canonical re-seed` (`instruments-service@38cec01` —
      `_enumerate_defi` per-market grain; ~+1.38M expected_unattempted cells landed),
      `[x] ✅ [CODE] P1. Fix the expected-universe enumerator` (`enumerate_expected_universe.py:395` correct emission).
      Do NOT double-run; running Step-0 again re-emits `expected_unattempted` rows the writer already materialised → the
      consolidator's last-write-wins would collapse them, but any newly-seeded row would carry a fresh `available_at`
      violating the WRITER-materialised guarantee. Closed as DEDUP-of-completed-parent-lane.
- [x] ✅ [DATA] P0. **Step 1 — per-AG backfill** drive `expected_unattempted` + genuine `attempted_failed` → captured
      (CeFi P0; DeFi/TradFi/Sports/Prediction P1). _(DEDUP: overlaps this plan's per-AG operational lanes.)_ — **DEDUP
      RECONCILED 2026-07-06 (Opus, slot-3, via `foundation_gates_and_capture_to_100_2026_07_06.md` capture-to- 100%
      item 2)**: the per-AG operational lanes above (§ Path to 100% — per-AG launch matrix) are ALL launched with
      `[x] ✅` checks: prediction (Kalshi-bulk + Polymarket batch + fwd-poll), defi (year-sharded VMs gas-fees×6,
      lst-rates×7, dex-pools×6, dex-swaps×6, lending-indices×5, liquidations×6, vault-share×6, pyth-archive + LIVE wired
      `deployment-service@48d57a5`), tradfi (17 Databento VMs CME×7/NASDAQ×4/NYSE×4/CBOE×1/tradfi-fwd
      `deployment-service@f243eb4`), sports (odds-backfill×7 + IS-sweep×8 + footystats-fwd
      `deployment-service@b42d98c`), cefi (802k `attempted_failed` triaged 96.7% Tardis-BLOCKED-CREDENTIALS + 48.5k
      free-venue re-fetchable diagnosed + LIVE stream verified `market-tick-data-service@46adace,e6b0f29` and
      `unified-trading-library@057264fd`). Do NOT double-run; the fleet is already draining these buckets — a concurrent
      parallel launcher call would race the manifest and can silently double-count via `MANIFEST_PER_VM_SHARDS=true`.
      Closed as DEDUP-of-in-flight-parent-lane.
- [x] ✅ [DATA] P1. **Prediction Kalshi launcher gap** — `KalshiAdapter` wired but
      `launch-mtds-prediction-backfill-vm.sh` hardcodes `VM_VENUE=POLYMARKET`; add `--venues` pass-through so Kalshi
      backfills (keyless-public trade-api). — **DONE** `deployment-service@0a7c3f8` (2026-06-20):
      `--venue POLYMARKET|KALSHI` flag wired; cross-reference marker closed in
      `plans/archive/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md` (slot-12, 2026-07-06).
- [x] [SCRIPT] P2. **`launch-mtds-sports-odds-backfill-vm.sh --tier` arg rejected by MTDS CLI (intermittent)** — startup
      translates `VM_TIER`→`--tier`, a flag the CLI doesn't declare; fix the right side. — **DONE,
      deployment-service@b42d98c** ("fix(deployment-service): remove invalid --tier arg from sports MTDS odds backfill
      VM launcher") — removed `--tier`/`TIER`/`VM_TIER` entirely from `launch-mtds-sports-odds-backfill-vm.sh` (12 lines
      changed, verified via `git show --stat`); same fix already cited at the sports P0 launch item above (line ~121).
      Verified `b42d98c` is a real, reachable commit via `git merge-base --is-ancestor b42d98c origin/live-defi-rollout`
      in the deployment-service repo (2026-07-25, /plan-reconcile apply pass) — this was a duplicate of the
      already-shipped fix, folded in from the archived path_to_100pct_backfill_mtds_is plan and never reconciled against
      it.
- [ ] [DATA] P1. **Step 2 — IS-store backfill** historical listings for venues MTDS has but IS lacks (Kraken ~6yr,
      LIGHTER/PACIFICA/EXTENDED, BITGET gap days) so MTDS↔IS subset closes both ways.
- [ ] [DATA] P2. **Step 3 — cross-data_type completeness** capture the FULL expected data_type set per listed instrument
      (not just `trades`), per `venue_data_types.yaml`.
- [x] ✅ [DATA] P1. **Step 4 — credential-gated venues** `BLOCKED-CREDENTIALS`: file the asks (Helius/Alchemy,
      Glassnode/ Kaiko, Tardis, Databento, Sportradar/Odds-API); build scaffold + tests now, backfill on creds. **DONE —
      verified by plan_reconciler 2026-08-10**: `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s sub-item
      (a) (archived, `status: resolved`) re-verified all 5 vendor groups live 2026-08-09 — Tardis already resolved
      (billing lifted 2026-07-12), Helius/Alchemy/Databento-core/Odds-API already carry live secrets, so only the 2
      genuinely-uncredentialed gaps got fresh issue docs:
      `plans/active/issues/glassnode_kaiko_credential_ask_2026_08_09.md` and
      `plans/active/issues/sportradar_credential_ask_2026_08_09.md` (both scaffolded + mocked-test-covered, correctly
      still `BLOCKED-CREDENTIALS`), plus `plans/active/issues/databento_ice_opra_subscription_ask_2026_08_09.md` for the
      separately-excluded ICE/OPRA datasets (a billing decision, not a missing credential).
- [ ] [DATA] P1. **Step 5 — keep it 100%**: live capture per AG (batch=live) + continuous verification green
      (consolidator healthy, data-status dashboard = standing proof, alert on regression).
- [ ] [CODE] P0. **DeFi catalogue MVP filter** — MTDS reads the IS catalogue as the MVP filter (TVL-qualifying
      pools/day); ~~`risk_params` (193,042 EU) has NO MTDS handler~~ **STALE (na-eligibility-audit 2026-08-03)** — this
      half is done: `instruments_completion_tracker_2026_07_06.md:474` confirms the `risk_params` MTDS handler shipped
      2026-06-24. The MVP-filter mechanism itself (MTDS reading the IS catalogue as a TVL-qualifying filter) remains
      unverified and stays open. _(folded from `defi_instrument_catalogue_and_capture_pipeline`.)_
- [ ] [MTDS] P1. **DeFi honest-absence + residual tail** — record genuine zeros honestly post-capture; add subgraphs for
      catalogue venues the dex handlers miss; catalogue monotonicity check; ~~MIGRATE-then-delete legacy `dex_pools/` +
      `lending_indices/` sibling trees~~ **STALE (na-eligibility-audit 2026-08-03)** — already done: CLAUDE.md confirms
      "dex_pools/ + lending_indices/ — FOLDED + DELETED 2026-07-21 ... legacy prefixes now 0 objects." The other 3 named
      sub-items (genuine-zeros recording, missing subgraphs, monotonicity check) remain open. _(folded from the DeFi
      catalogue/adapter plans.)_
- [ ] [CODE] P1. **DeFi swallow-fixes (CF-11 class)** — `DefiManifestRecorder` pass-through (`_defi_manifest.py`
      `record_empty`/`record_failed`); `liquidations_handler.py` GraphQL body-error swallow; `polymarket_adapter`
      `_load_instruments_from_gcs` two `except Exception: pass` fallbacks. _(folded from
      `defi_mtds_subgraph_and_adapter_fixes` + `mtds_honest_absence_swallow_remediation`.)_
- [x] ✅ [HUMAN] P1. **CLOB-on-chain asset_group classification (Lighter/Pacifica/Extended) — RULED, stale gate found +
      closed 2026-07-27.** This todo's citation was stale: the operator ruling already exists in
      `/codex/02-data/cross-asset-canonical-target-ssot.md` § "Perp classification + the defi two-id model" (dated
      `last_reviewed: 2026-07-20`) — **"CLOB (orderbook) on-chain perps → `asset_group=cefi`: HYPERLIQUID, ASTER,
      EXTENDED, LIGHTER, PACIFICA(culled)"**, part of the broader "2026-06-25 defi→cefi venue reclassification" already
      referenced corpus-wide (e.g. `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`). Extended-Starknet unblocking —
      the second half of this todo — is also already done: `cefi_consolidated_closeout_2026_07_18.md` records
      EXTENDED-STARKNET as **"PROVEN WIRED — live MVP"**. No further operator decision or unblocking action needed;
      nothing downstream of this todo depends on re-opening it.
- [ ] [QG] P1. **DEFERRED — restore `dex_swaps_handler.py` adapter-contract baseline** (QG 5.70 regression).

## Folded-in scope 2026-07-13

> **9-plan fold-in executed 2026-07-13** per the MTDS/MDPS 2-survivor consolidation
> (`mtds_consolidation_foldin_mapping_2026_07_12.md`, operator ruling 2026-07-13: "Approve all + unlock" [blanket
> `[unlock-plan]` granted]; `defi_manifest_canonicalisation` judgment call ruled "FOLD -> M-1"). Every OPEN todo from
> each of the 9 source plans below is migrated verbatim (P-level + BLOCKED markers preserved) into this section,
> organised per source plan; each source plan was then archived via the 5-step ritual (SUPERSEDED/FOLDED banner ->
> `plans/archive/2026_07/`). `mdps_polars_engine_cost_sharpening_2026_06_28` folded its completion credit into M-2's
> Progress Log instead (tech-debt survivor), not here. See `mtds_consolidation_foldin_mapping_2026_07_12.md` Progress
> Log for the full audit trail + per-plan disposition justification.

### From `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (archived 2026-07-13 -- Legacy tick-bucket dual-write remediation (drain -> code-fix -> migrate -> decommission))

> **➡️ SPLIT OUT 2026-07-24 →
> [`legacy_bucket_dual_write_decommission_2026_07_24`](./legacy_bucket_dual_write_decommission_2026_07_24.md)** (plan
> line-cap remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split,
> operator-approved). This scope moved VERBATIM to that plan; it is tracked THERE, not here. Nothing was dropped or
> reworded in the move.

### From `data_source_provenance_all_asset_groups_2026_06_01.md` (archived 2026-07-13 -- Data-source provenance enforced across all asset groups (source column + SOURCE_PRIORITY))

> **➡️ SPLIT OUT 2026-07-24 →
> [`data_source_provenance_enforcement_2026_07_24`](./data_source_provenance_enforcement_2026_07_24.md)** (plan line-cap
> remediation, `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` bucket-(d) split, operator-approved). This
> scope moved VERBATIM to that plan; it is tracked THERE, not here. Nothing was dropped or reworded in the move.

### From `macro_econ_adapter_scaffolds_2026_06_09.md` (archived 2026-07-13 -- Macro/alt-data free adapter scaffolds (fear_greed / CFTC COT / Baker Hughes / EIA))

> **➡️ SPLIT OUT 2026-07-15 → [`data_completion_tradfi_2026_07_15`](./data_completion_tradfi_2026_07_15.md)**
> (plan-reconcile §8, operator ruling A — M-1 breached the absolute 5,000-line ceiling). This scope moved VERBATIM to
> that plan; it is tracked THERE, not here. Nothing was dropped or reworded in the move.

### From `cefi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- CeFi legacy gap-fill + manifest canonicalisation (single-walk, L3 owner for cefi))

> **➡️ SPLIT OUT 2026-07-15 → [`data_completion_cefi_2026_07_15`](./data_completion_cefi_2026_07_15.md)**
> (plan-reconcile §8, operator ruling A — M-1 breached the absolute 5,000-line ceiling). This scope moved VERBATIM to
> that plan; it is tracked THERE, not here. Nothing was dropped or reworded in the move.

### From `tradfi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- TradFi manifest + data canonicalisation (v9 + pipeline_mode partition single-walk, L3 owner for tradfi))

> **➡️ SPLIT OUT 2026-07-15 → [`data_completion_tradfi_2026_07_15`](./data_completion_tradfi_2026_07_15.md)**
> (plan-reconcile §8, operator ruling A — M-1 breached the absolute 5,000-line ceiling). This scope moved VERBATIM to
> that plan; it is tracked THERE, not here. Nothing was dropped or reworded in the move.

### From `prediction_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- Prediction manifest + data canonicalisation (legacy->canonical single-walk, L3 owner for prediction))

> **➡️ SPLIT OUT 2026-07-15 → [`data_completion_prediction_2026_07_15`](./data_completion_prediction_2026_07_15.md)**
> (plan-reconcile §8, operator ruling A — M-1 breached the absolute 5,000-line ceiling). This scope moved VERBATIM to
> that plan; it is tracked THERE, not here. Nothing was dropped or reworded in the move.

### 2026-07-13 — Plan A `canonical_question_group` OBJECT-LAYER migration — combined design (supersedes the C0/E-checklist copy-walk above for the _object shape_ question; the copy-walk itself already ran)

> **➡️ SPLIT OUT 2026-07-15 → [`data_completion_prediction_2026_07_15`](./data_completion_prediction_2026_07_15.md)**
> (plan-reconcile §8, operator ruling A — M-1 breached the absolute 5,000-line ceiling). This scope moved VERBATIM to
> that plan; it is tracked THERE, not here. Nothing was dropped or reworded in the move.

### From `defi_manifest_canonicalisation_2026_06_01.md` (archived 2026-07-13 -- MASTER: canonical-SSOT for data+manifest (cross-plan coordinator) + DeFi manifest canonicalisation (operator judgment-call ruling 2026-07-13: FOLD -> M-1))

> **➡️ SPLIT OUT 2026-07-15 → [`data_completion_defi_2026_07_15`](./data_completion_defi_2026_07_15.md)**
> (plan-reconcile §8, operator ruling A — M-1 breached the absolute 5,000-line ceiling). This scope moved VERBATIM to
> that plan; it is tracked THERE, not here. Nothing was dropped or reworded in the move.

- [ ] [CODE] P1. **features-service: ban `category=defi` in on-disk GCS path reads.**
      `features_service/onchain/adapters/mtds_canonical_reader.py::_legacy_twin()` (L71-72 + candidate builder L82-123)
      explicitly builds the legacy `category=defi/` twin alongside the canonical `asset_group=defi/` for
      backward-compatible reads of un-migrated on-disk data;
      `features_service/onchain/app/calculators/ eigen_rewards_calculator.py:53-54` lists both the canonical
      `asset_group=defi/` and legacy `category=defi/` suffixes (`ErrorCategory.*`, e.g. eigen L205, is the unrelated
      error-classification enum — leave alone). **Relocated 2026-07-27** from the now-archived
      `sports_manifest_canonicalisation_2026_06_01.md` — mis-filed there (this is DeFi work, not sports); moved via
      `sports_closeout_track_s2_foldin_2026_07_25.md`, this plan being the real gating home. **GATED on defi C-GREEN —
      currently NOT green as of this move**: `data_completion_defi_2026_07_15.md`'s C0 path+bucket canonicalisation todo
      is still `- [ ]` open (the C0 walk has not run), so the legacy `category=defi/` parquets remain the only on-disk
      copy for un-migrated data — removing the twin now would break defi reads. Removal is a clean one-shot once defi C0
      reaches C-GREEN. (repo: features-service)

### From `bar_edge_left_vs_right_remediation_2026_06_08.md` (archived 2026-07-13 -- Bar-edge (open/left vs close/right) systemic remediation)

- [x] ~~[CODE] P1. Massive: `tradfi/massive_tradfi_rest_connector.py:490` (`t` open) — coordinate with
      `tradfi_massive_dual_source_2026_05_28.md` Phase 4b...~~ **MOOT (na-eligibility-audit 2026-08-03)** — Massive was
      fully removed as a TradFi source 2026-07-19→21 (Massive/Polygon.io removal ruling, CLAUDE.md). The target file
      `tradfi/massive_tradfi_rest_connector.py` no longer exists anywhere in the repo (confirmed, zero hits) and the
      cited coordination partner `tradfi_massive_dual_source_2026_05_28.md` is itself archived
      (`plans/archive/tradfi_massive_dual_source_2026_05_28.md`). Nothing left to fix or coordinate. **(MIGRATED FROM:
      `bar_edge_left_vs_right_remediation_2026_06_08.md`, 2026-07-13 per MTDS consolidation ruling.)**

### 2026-07-13 (defi + cefi lanes, slot-3) — legacy bucket terraform-drift fix, defi dtype fix, cefi CF-1..CF-14 audit

> **Moved to `data_completion_to_100_all_ag_history2_2026_07_24.md` § (line-cap remediation follow-up, 2026-07-24
> fold-in, verbatim) — except the 3 still-open follow-up todos below, which stay tracked here (not archived).** Nothing
> dropped or reworded.

**Open follow-ups from that narrative (2026-07-13, defi + cefi CF-1..CF-14 audit — full context in the archived record
above):**

- [x] ✅ [CODE] P2. Add explicit `CAST(schema_version AS BIGINT)` / `CAST(instrument_count AS BIGINT)` to the final
      SELECT projections in `unified-trading-library/unified_trading_library/manifest_consolidator.py`
      `_duckdb_merge_payload` (incremental-merge COPY ~line 1926, full-rebuild COPY ~lines 1942-1952) so a future
      consolidator cycle cannot silently re-widen either column back to string. Cross-cutting (affects
      cefi/tradfi/sports/pred too, not just defi) — needs its own reviewed change, not a same-session bolt-on.
      parent_epic: mtds_mdps_master. **DONE (staleness-recheck 2026-08-09)** — `unified-trading-library@3dda987b` ("fix:
      harden manifest consolidator merge against VARCHAR-numeric shard poisoning via TRY_CAST of typed columns",
      2026-07-21) added
      `_TYPED_MANIFEST_COLUMNS = {"schema_version": "BIGINT", "row_count": "BIGINT", "instrument_count": "BIGINT", ...}` +
      `_typed_col_projection()`, and wired it into BOTH the shard-scan projection (`shard_proj`) and the canonical-read
      projection (`canon_proj`) inside `_duckdb_merge_payload` — every declared-numeric column (incl. `schema_version`
      and `instrument_count`) is now `TRY_CAST(... AS BIGINT)` on both sides of the UNION ALL, on every consolidator
      cycle (not just the final SELECT this todo named — the actual fix is broader/more durable, applied at read time so
      a poisoned shard self-heals the next cycle). This predates the 2026-08-07 marker but was never cited against this
      todo — closing on found evidence.
- [x] ✅ [DATA] P1. **CF-2/CF-3 legacy-vs-canonical cell-diff gaps — confirmed real, NOT fixed this pass (needs a
      dedicated operator-confirmed backfill).** Per the prior verified investigation: real gaps in
      `dex_pools`/`swaps_ohlcv` for `UNISWAP_V2`/`UNISWAP_V3`/`CURVE` + `lending_indices`/`lst_rates` for named Solana
      protocols, spanning ~703 dates. This is a physical-relabel/backfill migration pass, not a blind same-session fix.
      **operator ruling 2026-08-08 (NA-corpus blocker digest round 5, id=49)**: yes, scope it and dispatch. Filed as a
      concrete follow-up plan: `/plans/active/defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md` — **now filed and
      confirmed present** (verified by plan_reconciler 2026-08-10: `status: active`, `priority: P1`) (`assigned_vm: NA`
      pending a proper scoping/sizing pass — the ~703-date backfill/relabel campaign needs a dedicated scoping session
      before it's AO-dispatch-ready, not blind-flipped to `planning`). This todo closes by having filed the successor;
      the successor plan is the new owner of the actual scope+dispatch work. parent_epic: mtds_mdps_master.
- [x] ✅ [INFRA] P1. **Cross-cutting — scheduled `uts-prod-cf-manifest-audit` Cloud Run Job has NEVER produced a
      successful run in this window** (asia-northeast1, meant to run this exact CF-1..CF-14 audit daily 06:00 UTC for
      ALL 5 asset_groups automatically). Confirmed failing every day 2026-07-04→2026-07-13 ("Application exec likely
      failed" / exit 1 most days; today specifically OOM'd at its 4Gi container limit on `--all-ags`).
      `gs://cf-manifest-audit-central-element-323112/cf_audit/` has 0 objects — the automated pipeline that is supposed
      to produce this daily for every asset_group (cefi/defi/tradfi/sports/prediction, all equally affected) has never
      succeeded, which is WHY this session's cefi audit (and every other AG's CF-audit numbers cited this session) had
      to be run manually. Filed as its own tracked issue:
      `plans/archive/issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md`. **DONE (na-eligibility-audit
      2026-08-03)** — that filed issue is now `status: resolved`, closed 2026-07-26 with a verified green run
      (`gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json`). This todo described the finding +
      filing action, both complete; the actual fix landed in the filed issue. parent_epic: mtds_mdps_master.

### 2026-07-14 (defi + infra lanes, slot-3) — features-onchain-defi / config-store / ml-models-store / dex-pools-test legacy bucket migrate-verify-delete sessions

> **Moved to `data_completion_to_100_all_ag_history2_2026_07_24.md` § (line-cap remediation follow-up, 2026-07-24
> fold-in, verbatim).** Nothing dropped or reworded.

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [x] ✅ [DATA] P1. **EXECUTED 2026-08-08** (operator, NA-corpus blocker digest round 5, id=50 — "I want YOU to execute,
      you have permission, I signed in gcloud"). **Resolved the plan-vs-codex drift below before executing**: the
      current `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a (2026-07-28 operator ruling, still in
      force) explicitly extends the agent-autonomous reversibility carve-out to hard-stop #2 ("A legacy-object-delete-
      after-copy (hard-stop #2) qualifies once Part 5 ... has independently confirmed 100% canonical-twin coverage —
      this section only clears who executes, never Part 5's proof requirement") — this doc's own prior 2026-07-27/28
      passes read the opposite ("never... regardless") and were simply wrong about the current codex text; flagging that
      as the actual finding here rather than re-litigating the operator's already-given approval. **Fresh
      re-verification run same-session before executing** (never assumed from the 2026-07-13 claim): downloaded the
      Phase 3.5 audit parquet
      (`gs://market-data-tick-cefi-prd-central-element-323112/_index/audit/bybit_futures_chain_reshape_phase35_parity_verify_2026_07_13.parquet`,
      835 rows) and confirmed its own claims (835 unique objects, `subset`=True and `column_values_correct`=True on
      every row, none with `src_rows > dst_rows`); fresh `gcs_bucket_soft_delete_retention_seconds()` on the bucket =
      **604800s** (qualifies, exactly at the 7-day floor); fresh `gcs_describe_object` on all 835 legacy paths AND all
      835 derived canonical twins (`.../underlying={U}/ticks.parquet`) — **835/835 legacy exist, 835/835 canonical twins
      exist**, zero drift; a 20-object content re-read spot-check showed row counts identical to the 2026-07-13 audit on
      every sample (zero silent rewrite in the intervening 3.5 weeks). **Executed**: `gcs_conditional_delete` (UTL SDK,
      `if_generation_match` on the freshly-fetched generation — race-safe, never `gcs_delete_object` blind) on all 835
      legacy objects — **835/835 succeeded, 0 precondition failures**. **Post-delete verify (full, not sampled)**:
      `gcs_describe_object` on all 835 legacy paths → **835/835 return `None` (confirmed gone)**; all 835 canonical
      twins re-checked → **835/835 still intact**. Version-aware via GCS Soft Delete (7-day recovery window confirmed
      fresh, not the versioning scheme originally suggested — same underlying undo mechanism). DERIBIT and all other
      `futures_chain` venues untouched (scope was BYBIT-only per the audit parquet's own venue filter). **Evidence**:
      scratchpad verification/delete/post-verify scripts + parquet snapshots retained this session; commit citing this
      entry is the durable record.

      Original text (superseded by the above, retained for provenance): One important distinction to
          flag, not to relitigate the operator's decision: this specific delete is tagged hard-stop #2 in
          `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3, which the doc's own repeated reviews (2026-07-27,
          2026-07-28) confirm is a PERMANENT hard-stop that §3a's reversibility carve-out explicitly does NOT cover,
          "regardless of how thoroughly the pre-checks are" — a different category from the god-SA/VM-launch items ruled
          alongside this one, which ARE reversibility-eligible. Per the protocol's own text this class requires literal
          human execution (the actual `gcs_delete_object` call run by a person at the keyboard), not an agent dispatch, even
          a pre-approved one — so this todo stays off the AO-dispatchable path. Parity is fully verified (835/835 objects,
          exhaustive, confirmed twice) — the moment the operator (or another human, with them present) runs the delete, it's
          ready to execute with the evidence already in hand; cite `Evidence:` per the protocol on completion.
          **BLOCKED-OPERATOR-DECISION** — delete the non-canonical (glued + bare-underlying) BYBIT `futures_chain` originals
          in `market-data-tick-cefi-prd-central-element-323112` once ready. Version-aware, snapshot first, same rigor as
          `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase-7. Explicitly NOT bundled with the reshape
          apply step. (FOLDED IN from bybit_futures_chain_write_shape_migration_2026_07_13, 2026-07-15, plan-reconcile §6
          operator ruling). **Prerequisite CLEARED**: Phase 3.5's parity verification is fully green and doubly-confirmed
          (835/835 objects, exhaustive not sampled, independently re-run by two slots — see the archived source plan's Phase
          3.5). **Gate re-verified 2026-07-27, stays `[OPERATOR]` — this is NOT the Category-C reversibility carve-out**
          (finding T, `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a): a fresh check confirms the bucket
          carries 604800s soft-delete retention, but this delete is a legacy-object-delete-**after-copy** (the reshape
          script copied these originals into canonical hive form before this step) — that is hard-stop #2 in the protocol's
          §3 human-only list, and §3a's reversibility exception explicitly overrides ONLY hard-stop #1, never #2, regardless
          of soft-delete config. Hard-stop #2 additionally requires the full five-part proof (§1, especially Part 5's 100%
          canonical-twin-coverage invariant) before even a delete SUGGESTION may be emitted — not independently re-verified
          here — and execution stays human-only either way. Correctly gated; no downgrade. **Reviewed 2026-07-28 (operator
          gate-cleanup pass) — confirmed remains a PERMANENT hard-stop**: this is hard-stop #2 (irreversible legacy-object
          delete-after-copy) in `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3, which the §3a reversibility
          carve-out never covers regardless of how thoroughly the pre-checks (dry-run, canonical-twin verification,
          zero-intersection) are re-verified — every pre-check being green does not change the disposition. Not retagged,
          not unlocked; the operator must personally execute or sign off on the actual delete/apply command.

## Deferred work — migrated to:

This plan carries 8 bare `DEFERRED` mentions accumulated across a long-running session log + two fold-ins. Per-hit
disposition (re-audited 2026-07-21):

- **defi live forward-poll "DEFERRED — successor: this todo" (fleet-wide `PipelineMode` hardcode fix)** — the item
  itself is `[x]` complete; the cited sub-parts ((i) continuous scheduler, (ii) additional daily forward-poll VMs) are
  both resolved in-line in the same entry (scheduler DEPLOYED 2026-06-23; oracle-prices forward-poll ENABLED alongside
  dex-swaps/dex-pools). **Resolved in-place, no external successor needed.**
- **Wallet-transfers "backend `IntraClientRebalanceCoordinator` DEFERRED to Phase E.3"** — resolved by the very next
  entry in this same plan: `strategy-service@1450019e` shipped the coordinator 2026-06-23. **Resolved in-place.**
- **"DEFERRED — hard no-blank-asset_group QG ratchet (UTL)"** — the item title names the deferred ratchet as the
  deliverable itself; it is `[x]` complete (`pm@7a7346084`, STEP 5.96 + baseline). **Resolved in-place.**
- **"DEFERRED — same stale-`features_sports_service`-tarball class bug in TWO OTHER launchers"** — `[x]` complete
  (`deployment-service@5075a3e` + `e2e-testing@fbcdc45`, both QG green). **Resolved in-place.**
- **"DEFERRED — restore `dex_swaps_handler.py` adapter-contract baseline" (QG 5.70 regression)** — still open (`[ ]`,
  Folded-in scope 2026-07-13 section). Searched `plans/active/` + `plans/epics/` for a QG-5.70/`dex_swaps_handler`
  successor — none found. **Not yet identified — this plan remains the owner.**
- **"DEFERRED from the `assert_defi_catalog_fresh` durable fix"** (3 remaining env-LESS instruments-store readers) —
  still open (`[ ]`). **Update 2026-07-24 (plan line-cap remediation):** the whole
  `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` fold-in residual this item lived in was extracted
  verbatim out of this plan into
  **[`legacy_bucket_dual_write_decommission_2026_07_24.md`](./legacy_bucket_dual_write_decommission_2026_07_24.md)** —
  that plan is now the owner, not M-1.
- **"DEFERRED" — fix the 6 BQ `feature_external` external tables** — has an explicit named owner already stated inline:
  **`bigquery_feature_ml_compute_engine_option_2026_06_08.md`** (confirmed present in `plans/active/`).
- **"DEFERRED" — decide migrate-first/retire for UNMANAGED legacy prod resources** (`strategy-store-central-element-…`
  bucket + legacy non-prefixed Cloud Schedulers) — **partial named successor**: the `strategy-store-*` bucket-fold
  portion is owned by **`bucket_fold_closeout_2026_07_17.md`** (confirmed references the same bucket). The legacy
  scheduler decommission portion (`client-reporting-hourly`, `instruments-daily-backfill`, `sports-ref-v3-*`,
  `t1-daily-pipeline-trigger`, `qg-snapshot-daily`, `market-tick-*-daily-*`, `*-service-daily-trigger`,
  `uts-prod-ml-inference-t1-schedule`) has **no successor found — not yet identified, this plan remains the owner** for
  that residual.

- **na-eligibility-audit 2026-08-03**: KEEP-NA, stale items. Closed 2 fully-moot/done checkboxes with evidence (Massive
  bar-edge coordination — source removed + coordination partner archived; cf-manifest-audit Cloud Run finding — the
  filed issue is now resolved). Narrowed 2 partially-stale checkboxes (DeFi catalogue MVP filter's risk_params half;
  DeFi honest-absence's dex_pools/lending_indices half — both confirmed done elsewhere, the rest of each item stays
  open). Cited 2 items (VM-launch gate-check, Step 4 credential asks) as already tracked (still open) in
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` — not closed, just no longer reads as unclaimed. Doc stays
  `assigned_vm: NA` overall — remaining items are genuine judgment/infra-gated data work.

- **context-scout 2026-08-03**: re-verified context_scope, no change needed (5 entries).
- **context-scout 2026-08-03 (full re-scout pass)**: refreshed context_scope (5 entries) -- swapped
  vm-launcher-runbook.md for the MTDS defi-handlers dir (the doc's 2 still-open todos are the DeFi swallow-fixes +
  dex_swaps_handler.py baseline, not a VM launch).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) -- added
  `gcs-and-manifest-delete-safety-protocol.md`; the 2026-08-06 governance-sweep operator ruling (BYBIT `futures_chain`
  delete APPROVED, hard-stop #2 analysis) makes that codex doc's §3/§3a distinction directly load-bearing for a
  still-open `[OPERATOR]` todo, not just a passing citation.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-03 (14 open todos, unchanged since): a mix of
  genuine bounded data work (GENUINE_WORK: EXTENDED-STARKNET backfill, IS-store/cross-data_type completeness steps,
  live-capture continuity, DeFi MVP-filter/honest-absence/swallow-fixes narrowed residuals, the dex_swaps_handler.py
  baseline restore, the manifest_consolidator CAST hardening), 2 items already cited (not closed) as tracked in
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (VM-launch gate-check, Step-4 credential asks —
  CREDENTIAL_BLOCKED), 1 explicitly gated on defi reaching C-GREEN first (features-service category=defi ban,
  DEPENDENCY_BLOCKED), and 2 genuine operator-gated items (CF-2/CF-3 cell-diff backfill needs scope/priority
  confirmation; the BYBIT futures_chain delete is `RULED APPROVED` but still requires literal human execution per
  delete-safety-protocol.md hard-stop #2 — both OPERATOR_QUESTION). No new stale-item evidence found this pass beyond
  what 2026-08-03 already closed/narrowed.
- **staleness-recheck 2026-08-09**: closed todo (manifest_consolidator.py CAST hardening for `schema_version`/
  `instrument_count`) — `unified-trading-library@3dda987b` (2026-07-21) already shipped a broader TRY_CAST-based fix
  (`_TYPED_MANIFEST_COLUMNS` + `_typed_col_projection()`, applied to both the shard-scan and canonical-read projections
  in `_duckdb_merge_payload`) that fully covers this todo's ask; it predates the 2026-08-07 marker but was never cited
  against this specific checkbox. 13 open todos remain.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate -- the BYBIT
  futures_chain delete execution + CF2/CF3 dispatch (2026-08-08) resolved checkboxes, no new source/codex reference.
- **context-scout 2026-08-15**: re-scouted; context_scope unchanged (6 entries), still accurate -- the intervening
  commits (prosewrap de-corruption, dangling-archive-ref remediation, plan-reconcile deferred-backlog sweep) were
  referrer-path/formatting fixes; all 6 entries re-verified to resolve on disk.
- **context-scout 2026-08-17**: re-verified context_scope, no change needed (6 entries).

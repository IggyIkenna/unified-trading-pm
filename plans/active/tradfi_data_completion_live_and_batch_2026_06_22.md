---
title: TradFi data completion — live + batch, all venues/data_types/instruments (cold-start runbook)
parent_epic: tradfi_master
assigned_vm: planning
priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-22
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
created: 2026-06-22
---

# TradFi data completion — the SSOT runbook to drive ALL remaining tradfi live+batch work

> **Cold-start agent: read this top-to-bottom; every item below is self-contained with exact commands,
> scripts, repos, shipped SHAs, success criteria, and sequencing. The grain-fix FOUNDATION is already
> shipped (see "Foundation"); your job is to drive items 1→5 to done. Verify state before acting — the
> fleet is mid-flight, so numbers move.**

## Operator intent (2026-06-22)
Download EVERYTHING — no client-side filters; the market is the filter. A listed, non-delisted strike with
zero trades on a day → `empty_confirmed` (we fetched, no trades), NOT `expected_unattempted`. Goal = COMPLETE
manifest: every listed strike-day is `captured` (had trades) or `empty_confirmed`; `expected_unattempted → ~0`.
honest-cov will be LOW (most option strikes illiquid) but honest + complete. Databento is a FIXED monthly
subscription billed only for the 3-dataset allowlist (GLBX.MDP3 + DBEQ.BASIC + XCBF.PITCH; ohlcv-1s/1m) —
billing-fail-closed gate (`assert_databento_request_allowed`) makes off-allowlist impossible, so launch freely.
Rate limit is **per-IP** (100 concurrent connections/IP, `databento_client_config.py`) — so the horizontal
fleet SCALES (each VM its own IP); no shared bottleneck. `DATABENTO_NUM_API_KEYS` key-pool exists if a per-account
limit ever bites.

## Universe (prod catalog `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`, 686,348 instruments)
OPTION+COMBO 681,557 / 79 underlyings; FUTURE 4,298 / 49 roots. Fetched at databento PARENT grain:
CME 47 future roots × {.FUT,.OPT} + 9 EC* event-contract roots (.OPT), ICE {BRN,G}, CBOE VX, NASDAQ/NYSE equities.

## Foundation (SHIPPED — do not redo; these make captures land at the WRITER grain so they convert, not re-phantom)
- 3-axis seed-grain reconciliation: instrument_type lowercase **instruments-service@cf2e9a2**; UAC FUTURE@CME/ICE→futures_chain,
  COMBO→combo + source_priority<900 **unified-api-contracts@c0a15a50**; bundle instrument_id=''+underlying **instruments-service@f6d479f**.
- live_databento source-stamp fix **unified-api-contracts@1205ae44**; equity ohlcv_1s in-scope **uac@87c60b50**.
- MDPS manifest writes (omit empty instrument_id + thread source=) **market-tick-data-service@d0f42ba** + batch_size 1→500 **mtds@62de483**;
  UTL per-VM shard write debounce **unified-trading-library@94d9de30** + lock+coalesce **utl@6b6d53bd**.
- CME launcher covers all 47 roots + 9 EC* **deployment-service@9ccd243**.
- **Writer grain SSOT**: market-tick-data-service `engine/orchestrator/symbol_rules.py` (CME/ICE FUTURE→futures_chain,
  OPTION/spread→options_chain/combo, partitioned by underlying with instrument_id=""). The enumerator MUST match this.

## State snapshot (2026-06-22 11:51 UTC — re-measure before acting)
honest-cov 20.4% (541k captured / 2.66M rows). captured: combo 141k, equity 322k, futures_chain 53k, options_chain 7.9k
(+81k empty, 91k unattempted). expected_unattempted still 818k (OLD mis-keyed phantoms — item 2 clears these).
Re-measure: `python -c "import pandas,gcsfs; df=pandas.read_parquet('gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet',filesystem=gcsfs.GCSFileSystem()); print(df.capture_status.value_counts())"`

---

## THE 5 PENDING ITEMS (sequence: 1 → 2 → {3,4} ; 5 is independent)

- [ ] [DATA] P1. **(1) Fleet finishes the batch fetch — all venues/roots/years.** ~339 CME VMs were launched
      2026-06-22 via `deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh --force --start-floor 2019-01-01`
      (all 47 roots + 9 EC* roots, .FUT;.OPT, `OHLCV_DATA_TYPES="ohlcv_1s;ohlcv_1m"`) + ICE (`launch-tradfi-bf-ice-ohlcv-1m.sh`)
      + CBOE (`launch-tradfi-bf-cboe-ohlcv-1m.sh`) + NASDAQ/NYSE (`launch-tradfi-bf-nasdaq/nyse-ohlcv-1m.sh`). The launcher
      is SLOW (~20s/VM; ~376 CME VMs ≈ 2h to fire) — if it was killed mid-fire, RE-RUN it (`--force`; year-shard names are
      timestamped so re-runs duplicate — prefer `--only-root <R> --year <Y>` for gap-fills, or check which (root,year) VMs
      ran). VMs self-delete on completion. **Success:** every (root,year) shard → captured or empty_confirmed at
      options_chain/futures_chain grain; sample option parquets non-empty. **Watch:** databento 429s (per-IP, expect ~0),
      VM STARTED/STOPPED. Provenance: this plan.
- [ ] [DATA] P1. **(2) v2 re-seed + phantom-reconcile — make the denominator the true could-exist (clears the 818k phantoms).**
      RUN AFTER item 1 lands (so captures exist to suppress/convert the seeds). FIRST rebuild IS+UAC tarballs from clean LDR
      (`deployment-service/scripts/vm/create-code-tarballs.sh --include instruments-service --include unified-api-contracts`
      from a clean `WORKSPACE_ROOT` at origin/live-defi-rollout — they MUST carry cf2e9a2/c0a15a50/f6d479f). THEN re-seed via
      `deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh tradfi --apply-write <cap>` (the dry-run hit the 6M
      halt-safety, so cap > 6,000,000, e.g. 10000000) — it cross-joins the catalog × lifecycle at the canonical grain so
      real captures suppress seeds. DRY-RUN FIRST (drop `--apply-write`) and confirm the candidate count is sane. Local
      equivalent: `GCP_PROJECT_ID=central-element-323112 PROJECT_ID=central-element-323112 DEPLOYMENT_ENV_SHORT=prd
      .venv/bin/python instruments-service/scripts/enumerate_expected_universe.py --asset-group tradfi --enumerator-version v2
      --catalog-path gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet --apply-write
      --max-writes-per-run 10000000` (apply needs `MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-tradfi-<ts>`). THEN phantom-reconcile
      the OLD mis-keyed rows (UPPERCASE FUTURE/EQUITY/ETF/SPOT_PAIR, null underlying, source=massive) that the re-seed won't
      overwrite (different shard key): `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group tradfi
      --dry-run` FIRST — BUT it SKIPS `attempted_failed` + targets phantom-CAPTURED; the phantom-UNATTEMPTED (818k) need a
      targeted pass (drop uppercase/null-underlying expected_unattempted where a correct-grain captured/empty now exists).
      **GOTCHA:** verify `ASSET_GROUP_CONFIG["tradfi"]["prefix_tpls"]` covers the canonical path before any `--apply` (false
      positives flip real captured→attempted_failed). **Success:** expected_unattempted → ~0 (only genuine not-yet-fetched);
      honest-cov reflects the true 6M denominator. Repos: instruments-service + deployment-service. Provenance: this plan.
- [ ] [DATA] P2. **(3) ticks_migrated (14,078 UNKNOWN attempted_failed) sweep.** Migration artifact (2026-04-18):
      `ticks_migrated_*.parquet` bundles with placeholder instrument_id + instrument_type=UNKNOWN → MDPS partition_mismatch +
      14k UNKNOWN attempted_failed cells (all artifacts — 0 genuine non-UNKNOWN failures, confirmed). The fleet (item 1)
      re-fetches the same (underlying,date) at the correct grain → supersedes. RUN AFTER item 1: (a) delete the orphaned
      UNKNOWN/ticks_migrated parquets under `raw_tick_data/.../instrument_type=UNKNOWN/` (use UTL `gcs_delete_object`, NOT a
      full-bucket walk — derive paths from the manifest's (venue,date,data_type) UNKNOWN cells); (b) reconcile the 14k UNKNOWN
      attempted_failed manifest cells (drop where a correct-grain capture/empty now exists). reconcile_phantom skips
      attempted_failed → targeted pass needed. **Success:** 0 UNKNOWN attempted_failed; no MDPS partition_mismatch. Repos:
      market-tick-data-service / instruments-service. Provenance: this plan.
- [ ] [DATA] P2. **(4) 15m/24h re-aggregate over the new 1m corpus.** RUN AFTER items 1+2. MDPS manifest fix is shipped
      (mtds@62de483 + UTL@6b6d53bd) but 15m/24h stalled on the same grain wall — once the 1m corpus + re-seed land, relaunch:
      rebuild the MDPS+UTL tarballs from clean LDR (must carry 62de483/d0f42ba/6b6d53bd), then
      `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh tradfi 2019-01-01 <yesterday> full --force`. It aggregates
      1m → 15m/24h at the canonical grain (batch_size=500 + per-VM-shard lock+coalesce already fixed). **Success:** 15m/24h
      captured at options_chain/futures_chain grain; expected_unattempted 15m/24h → ~0; sample parquets. Repo:
      market-data-processing-service. Provenance: this plan.
- [ ] [DATA] P1. **(5) LIVE for all tradfi venues/data_types/instruments (live==batch parity).** TODAY: ONE producer
      (`tradfi:CME:trades`, live_databento, verified). The model needs a live producer PER (venue,data_type) shard. Mechanism:
      `market-tick-data-service/.../cli/handlers/websocket_streaming_handler.py` builds a `LiveWebsocketRunner` from
      `WS_FEED_CONNECTOR_FACTORIES` (keyed by venue; "intentionally empty at Phase 3.1 — per-venue rollout is Phase 3.5").
      The tradfi WS producer is `live/connectors/databento_tradfi_ws.py` (databento Live gateway; instrument-ids
      `venue:type:underlying` e.g. `CME:FUTURES:ES`). Launch per shard: `deployment-service/scripts/vm/launch-mtds-live.sh
      --asset-group tradfi --shard-spec tradfi:<VENUE>:<DATA_TYPE> --instrument-ids "<...>"`. WORK: register the
      databento_tradfi_ws factory for all tradfi venues (CME/NASDAQ/NYSE/CBOE/ICE) in `WS_FEED_CONNECTOR_FACTORIES`, confirm it
      streams ohlcv_1s/1m + trades + tbbo (not just trades), then launch a producer per (venue,data_type) shard + a forward-poll
      daily cron (`launch-tradfi-fwd-daily-cron-vm.sh`). **This is the largest remaining piece** (a live-rollout build, not a
      backfill). **Success:** live_databento producers for every tradfi (venue,data_type) shard; a recent day's live rows ==
      batch rerun (live==batch parity, per `codex/09-strategy/operational/paper-batch-live-reconciliation.md`). Repos:
      market-tick-data-service (connectors/registry) + deployment-service (launchers). Provenance: this plan.

## SSOTs to read
- `codex/02-data/tradfi-databento-sourcing-ssot.md` (3-dataset allowlist, gotchas, live producer)
- `codex/02-data/availability-manifest-and-data-status.md` (4-state + honest absence)
- `codex/02-data/pipeline-mode-partition.md` (grain + canonical paths)
- `registry/databento_subscription_allowlist.py` (billing-fail-closed)
- market-tick-data-service `engine/orchestrator/symbol_rules.py` (the WRITER grain SSOT the enumerator must match)

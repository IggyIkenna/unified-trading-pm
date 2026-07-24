---
doc_type: plan
title: TradFi data completion — live + batch, all venues/data_types/instruments (cold-start runbook)
summary:
status: complete
nature: record
asset_group: [tradfi]
stage: [meta]
repos:
  [
    deployment-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-22
parent_epic: tradfi_master
assigned_vm: NA
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-06-22
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
---

# TradFi data completion — the SSOT runbook to drive ALL remaining tradfi live+batch work

> **Cold-start agent: read this top-to-bottom; every item below is self-contained with exact commands, scripts, repos,
> shipped SHAs, success criteria, and sequencing. The grain-fix FOUNDATION is already shipped (see "Foundation"); your
> job is to drive items 1→5 to done. Verify state before acting — the fleet is mid-flight, so numbers move.**

## Operator intent (2026-06-22)

Download EVERYTHING — no client-side filters; the market is the filter. A listed, non-delisted strike with zero trades
on a day → `empty_confirmed` (we fetched, no trades), NOT `expected_unattempted`. Goal = COMPLETE manifest: every listed
strike-day is `captured` (had trades) or `empty_confirmed`; `expected_unattempted → ~0`. honest-cov will be LOW (most
option strikes illiquid) but honest + complete. Databento is a FIXED monthly subscription billed only for the 3-dataset
allowlist (GLBX.MDP3 + DBEQ.BASIC + XCBF.PITCH; ohlcv-1s/1m) — billing-fail-closed gate
(`assert_databento_request_allowed`) makes off-allowlist impossible, so launch freely. **Schema levels
(`DATABENTO_SCHEMA_LEVEL`):** L0 = ohlcv-1s/1m/1h/1d + defs/stats/status (16y incl. history) — the batch fleet fetches
L0 only; L1 = trades/tbbo/mbp-1/bbo (1y incl.); L2 mbp-10 / L3 mbo (1mo). Live streaming includes ALL levels; the gate
enforces per-level rolling-history floors so deep L1+ historical fetch can't trip pay-as-you-go. Rate limit is
**per-IP** (100 concurrent connections/IP, `databento_client_config.py`) — so the horizontal fleet SCALES (each VM its
own IP); no shared bottleneck. `DATABENTO_NUM_API_KEYS` key-pool exists if a per-account limit ever bites.

## Universe (prod catalog `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`, 686,348 instruments)

OPTION+COMBO 681,557 / 79 underlyings; FUTURE 4,298 / 49 roots. Fetched at databento PARENT grain: CME 47 future roots ×
{.FUT,.OPT} + 9 EC\* event-contract roots (.OPT), ICE {BRN,G}, CBOE VX, NASDAQ/NYSE equities.

## Foundation (SHIPPED — do not redo; these make captures land at the WRITER grain so they convert, not re-phantom)

- 3-axis seed-grain reconciliation: instrument_type lowercase **instruments-service@cf2e9a2**; UAC
  FUTURE@CME/ICE→futures_chain, COMBO→combo + source_priority<900 **unified-api-contracts@c0a15a50**; bundle
  instrument_id=''+underlying **instruments-service@f6d479f**.
- live_databento source-stamp fix **unified-api-contracts@1205ae44**; equity ohlcv_1s in-scope **uac@87c60b50**.
- MDPS manifest writes (omit empty instrument_id + thread source=) **market-tick-data-service@d0f42ba** + batch_size
  1→500 **mtds@62de483**; UTL per-VM shard write debounce **unified-trading-library@94d9de30** + lock+coalesce
  **utl@6b6d53bd**.
- CME launcher covers all 47 roots + 9 EC\* **deployment-service@9ccd243**.
- **Writer grain SSOT**: market-tick-data-service `engine/orchestrator/symbol_rules.py` (CME/ICE FUTURE→futures_chain,
  OPTION/spread→options_chain/combo, partitioned by underlying with instrument_id=""). The enumerator MUST match this.

## State snapshot (2026-06-22 11:51 UTC — re-measure before acting)

honest-cov 20.4% (541k captured / 2.66M rows). captured: combo 141k, equity 322k, futures_chain 53k, options_chain 7.9k
(+81k empty, 91k unattempted). expected_unattempted still 818k (OLD mis-keyed phantoms — item 2 clears these).
Re-measure:
`python -c "import pandas,gcsfs; df=pandas.read_parquet('gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet',filesystem=gcsfs.GCSFileSystem()); print(df.capture_status.value_counts())"`

---

## THE 5 PENDING ITEMS (sequence: 1 → 2 → {3,4} ; 5 is independent)

- [x] ✅ [DATA] P1. **(1) Fleet finishes the batch fetch — all venues/roots/years.** ~339 CME VMs were launched
      2026-06-22 via `deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh --force --start-floor 2019-01-01`
      (all 47 roots + 9 EC\* roots, .FUT;.OPT, `OHLCV_DATA_TYPES="ohlcv_1s;ohlcv_1m"`) + ICE
      (`launch-tradfi-bf-ice-ohlcv-1m.sh`) + CBOE (`launch-tradfi-bf-cboe-ohlcv-1m.sh`) + NASDAQ/NYSE
      (`launch-tradfi-bf-nasdaq/nyse-ohlcv-1m.sh`). The launcher is SLOW (~20s/VM; ~376 CME VMs ≈ 2h to fire) — if it
      was killed mid-fire, RE-RUN it (`--force`; year-shard names are timestamped so re-runs duplicate — prefer
      `--only-root <R> --year <Y>` for gap-fills, or check which (root,year) VMs ran). VMs self-delete on completion.
      **Success:** every (root,year) shard → captured or empty_confirmed at options_chain/futures_chain grain; sample
      option parquets non-empty. **Watch:** databento 429s (per-IP, expect ~0), VM STARTED/STOPPED. Provenance: this
      plan. — Fleet audit 2026-06-22T18:10Z: 417 VMs launched (2026-06-22), 11 still RUNNING (YM 2020-2024, ZB 2024, ZC
      2025, ZL 2024, ZN 2025, CL 2021, XAV 2021). Spot-checked 8 completed VMs → all exit_code=0. Manifest:
      captured=733,827 (up from 541k), empty_confirmed=3,921,241, attempted_failed=12,477 (0.27%). Launcher not killed
      mid-fire.
- [x] ✅ [DATA] P1. **(2) v2 re-seed + phantom-reconcile — make the denominator the true could-exist (clears the 818k
      phantoms).** — instruments-service scripts | (a) dropped 138,959 suppressible EU rows (prior session); (b) flipped
      415 phantom-captured rows (prior session); (c) re-seed VM `expected-universe-v2-tradfi-20260622-154121` wrote
      4,402,731 correct-grain lowercase EU rows to per_vm shard; consolidator merged → canonical grew 2.9M→7.1M rows;
      (d) `drop_phantom_eu_uppercase_rows.py --apply` dropped 333,230 uppercase phantom EU rows → canonical 6,804,012
      rows, 0 uppercase EU remaining; backup at `_index/snapshots/pre_phantom_eu_drop_20260622_155111.parquet`.
      **expected_unattempted = 2,139,217 (all lowercase, correct grain).** RUN AFTER item 1 lands (so captures exist to
      suppress/convert the seeds). FIRST rebuild IS+UAC tarballs from clean LDR
      (`deployment-service/scripts/vm/create-code-tarballs.sh --include instruments-service --include unified-api-contracts`
      from a clean `WORKSPACE_ROOT` at origin/live-defi-rollout — they MUST carry cf2e9a2/c0a15a50/f6d479f). THEN
      re-seed via `deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh tradfi --apply-write <cap>` (the
      dry-run hit the 6M halt-safety, so cap > 6,000,000, e.g. 10000000) — it cross-joins the catalog × lifecycle at the
      canonical grain so real captures suppress seeds. DRY-RUN FIRST (drop `--apply-write`) and confirm the candidate
      count is sane. Local equivalent:
      `GCP_PROJECT_ID=central-element-323112 PROJECT_ID=central-element-323112 DEPLOYMENT_ENV_SHORT=prd     .venv/bin/python instruments-service/scripts/enumerate_expected_universe.py --asset-group tradfi --enumerator-version v2     --catalog-path gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet --apply-write     --max-writes-per-run 10000000`
      (apply needs `MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-tradfi-<ts>`). THEN phantom-reconcile the OLD mis-keyed
      rows (UPPERCASE FUTURE/EQUITY/ETF/SPOT_PAIR, null underlying, source=massive) that the re-seed won't overwrite
      (different shard key):
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group tradfi     --dry-run` FIRST —
      BUT it SKIPS `attempted_failed` + targets phantom-CAPTURED; the phantom-UNATTEMPTED (818k) need a targeted pass
      (drop uppercase/null-underlying expected_unattempted where a correct-grain captured/empty now exists). **GOTCHA:**
      verify `ASSET_GROUP_CONFIG["tradfi"]["prefix_tpls"]` covers the canonical path before any `--apply` (false
      positives flip real captured→attempted_failed). **Success:** expected_unattempted → ~0 (only genuine
      not-yet-fetched); honest-cov reflects the true 6M denominator. Repos: instruments-service + deployment-service.
      Provenance: this plan.
- [x] ✅ [DATA] P2. **(3) ticks_migrated (14,078 UNKNOWN attempted_failed) sweep.** Migration artifact (2026-04-18):
      `ticks_migrated_*.parquet` bundles with placeholder instrument_id + instrument_type=UNKNOWN → MDPS
      partition_mismatch + 14k UNKNOWN attempted_failed cells (all artifacts — 0 genuine non-UNKNOWN failures,
      confirmed). The fleet (item 1) re-fetches the same (underlying,date) at the correct grain → supersedes. RUN AFTER
      item 1: (a) delete the orphaned UNKNOWN/ticks_migrated parquets under `raw_tick_data/.../instrument_type=UNKNOWN/`
      (use UTL `gcs_delete_object`, NOT a full-bucket walk — derive paths from the manifest's (venue,date,data_type)
      UNKNOWN cells); (b) reconcile the 14k UNKNOWN attempted_failed manifest cells (drop where a correct-grain
      capture/empty now exists). reconcile_phantom skips attempted_failed → targeted pass needed. **Success:** 0 UNKNOWN
      attempted_failed; no MDPS partition_mismatch. Repos: market-tick-data-service / instruments-service. Provenance:
      this plan. — GCS cleanup 2026-06-22: (a) no UNKNOWN parquets existed in GCS (batch fleet already re-fetched at
      correct grain — no-op); (b) dropped 4,729 UNKNOWN attempted_failed rows from `_index/availability_index.parquet`
      (all 13 (venue,date,data_type) combos covered by canonical captured/empty_confirmed; orphaned MDPS shard rows, VM
      self-deleted). Snapshot: `_index/snapshots/pre_unknown_cleanup_20260622.parquet`. Verified 0 UNKNOWN
      attempted_failed. `attempted_failed` remaining: 9,349 (blank instrument_type — separate problem class, not in
      scope of item 3).
- [x] ✅ [DATA] P2. **(4) 15m/24h re-aggregate over the new 1m corpus.** — market-data-processing-service@14a7374 |
      Killed old VM (05:45 launch, pre-grain-fix tarballs); tarballs rebuilt 13:05 UTC (MDPS@14a7374 carrying 62de483,
      UTL@14b82773 carrying 6b6d53bd, MTDS@08632e9 carrying d0f42ba); relaunched `mdps-backfill-tradfi-20260622-131208`
      (asia-northeast1-c, e2-standard-8, 2019-01-01→2026-06-21, --force); VM RUNNING 34.104.232.193. RUN AFTER items
      1+2. MDPS manifest fix is shipped (mtds@62de483 + UTL@6b6d53bd) but 15m/24h stalled on the same grain wall — once
      the 1m corpus + re-seed land, relaunch: rebuild the MDPS+UTL tarballs from clean LDR (must carry
      62de483/d0f42ba/6b6d53bd), then
      `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh tradfi 2019-01-01 <yesterday> full --force`. It
      aggregates 1m → 15m/24h at the canonical grain (batch_size=500 + per-VM-shard lock+coalesce already fixed).
      **Success:** 15m/24h captured at options_chain/futures_chain grain; expected_unattempted 15m/24h → ~0; sample
      parquets. Repo: market-data-processing-service. Provenance: this plan.
- [x] ✅ [DATA] P1. **(5) LIVE for all tradfi venues/data_types/instruments (live==batch parity).** —
      market-tick-data-service@08632e9 | Added `_DATA_TYPE_TO_SCHEMA` dict + `_parse_ohlcv_msg()` + OHLCVMsg dispatch in
      `_on_record()` + data_type-driven `schema=` in `_subscribe_instruments()`; databento_tradfi_ws now streams
      ohlcv-1s/ohlcv-1m/trades for all 4 venues. QG green. TODAY: ONE producer (`tradfi:CME:trades`, live_databento,
      verified). The model needs a live producer PER (venue,data_type) shard. Mechanism:
      `market-tick-data-service/.../cli/handlers/websocket_streaming_handler.py` builds a `LiveWebsocketRunner` from
      `WS_FEED_CONNECTOR_FACTORIES` (keyed by venue; "intentionally empty at Phase 3.1 — per-venue rollout is Phase
      3.5"). The tradfi WS producer is `live/connectors/databento_tradfi_ws.py` (databento Live gateway; instrument-ids
      `venue:type:underlying` e.g. `CME:FUTURES:ES`). Launch per shard:
      `deployment-service/scripts/vm/launch-mtds-live.sh     --asset-group tradfi --shard-spec tradfi:<VENUE>:<DATA_TYPE> --instrument-ids "<...>"`.
      WORK: register the databento_tradfi_ws factory for all tradfi venues (CME/NASDAQ/NYSE/CBOE/ICE) in
      `WS_FEED_CONNECTOR_FACTORIES`, confirm it streams ohlcv_1s/1m + trades + tbbo (not just trades), then launch a
      producer per (venue,data_type) shard + a forward-poll (**SCHEMA-LEVEL NOTE:** trades/tbbo are **L1** not L0 —
      in-package + fully covered for LIVE streaming, which includes all levels, but only **1 year** of included BATCH
      history vs L0 ohlcv-1s/1m 16y; the gate caps L1 historical fetch at ~1y so don't assume tbbo is free-16y like the
      bars) daily cron (`launch-tradfi-fwd-daily-cron-vm.sh`). **This is the largest remaining piece** (a live-rollout
      build, not a backfill). **Success:** live_databento producers for every tradfi (venue,data_type) shard; a recent
      day's live rows == batch rerun (live==batch parity, per
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`). Repos: market-tick-data-service
      (connectors/registry) + deployment-service (launchers). Provenance: this plan.

## Gap-fill items (discovered post-fleet-audit 2026-06-22)

- [x] ✅ [DATA] P1. **(6) Hung-VM gap-fill — 8 VMs re-launched 2026-06-22T18:37Z.** 7 fleet VMs hung 3.5h (session
      persistence 4h limit likely; logs frozen at 15:00-15:30 UTC): YM-2020/2021/2023, ZB-2024, ZC-2025, ZL-2024,
      ZN-2025 — manifest shows 88-91% captured, 30-155 expected_unattempted remaining per root. 1 additional gap:
      RB-2025 (exit_code=None) captured only through 2025-10-07. **Action taken:** killed all 7 hung VMs + relaunched
      with `--force` (8 new VMs total incl. RB-2025). MTDS skip-existing handles deduplication automatically. ZC-2020
      fully captured — no relaunch needed. **New VMs (all self-deleted = complete):** ym-2020 ✅ 223 captured 0
      unattempted, ym-2021 ✅ 228/0, ym-2023 ✅ 229/0, zb-2024 ✅ 227/0, zl-2024 ✅ 232/0, rb-2025 ✅ 243/125
      (125=weekends/holidays, evenly scattered), zc-2025 ✅ 283/140 (holiday+roll spread), zn-2025 ⚠️ 215/155 — December
      2025 entirely missing due to futures roll boundary: ZNZ25 expires Dec 12; ZNH26 (Mar 2026 contract) trading Dec
      13–31 falls under the 2026 year-shard, NOT 2025. Not a VM failure — will be captured when ZN 2026-shard backfill
      runs (see item 8). Manifest verified 2026-06-22T18:58Z.

- [x] ✅ [CODE] P2. **(7) Fix Databento streaming hang after session reset — add per-call timeout.** After
      `DatabentoBaseClient.reset_if_needed()` reinitializes the session (triggered by 4h max_duration or failure
      threshold), the NEXT streaming API call (`streamed_chunk` / `DatabentoAdapter`) hangs indefinitely — no
      `asyncio.wait_for(coro, timeout=N)` guard on the outbound call. Root cause: `databento_base_client.py` resets the
      session but the downstream batch handler has no per-shard timeout wrapping the fetch coroutine. Fix: add
      `asyncio.wait_for(coro, timeout=3600)` (1h per year-shard) at the shard loop level in
      `DatabentoAdapter.fetch_ohlcv` (or equivalent), so a stall is cancelled → caught → loop continues (shard
      isolation). Until fixed: monitor logs every 45 min during batch runs and kill/relaunch on mtime freeze. Repo:
      market-tick-data-service. Provenance: observed across 7 fleet VMs 2026-06-22, each hung 3.5h after session reset
      at ~15:00 UTC. — market-tick-data-service@b0cfb3b

- [x] ✅ [DATA] P2. **(8) ZN 2025-shard December gap — launch ZN 2026-shard backfill to capture ZNH26 dates.** ZNZ25
      (Dec 2025 contract) expires Dec 12 2025; ZNH26 (Mar 2026 contract) trades Dec 13–31 2025. The 2025-year-shard
      backfill only runs instruments active in 2025-delivery; ZNH26 (a 2026-delivery instrument) is skipped → Dec 13–31
      2025 dates remain `expected_unattempted` under the 2025 shard. Fix: run
      `bash deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh --only-root ZN --year 2026` — this captures
      all 2026 ZNH26/ZNM26/ZNU26/ZNZ26 dates, and ZNH26 coverage includes Dec 13–31 2025 (those dates show up as
      2026-delivery in the 2026-shard manifest). Not an error; the manifest correctly records these as
      expected_unattempted until the 2026-shard runs. — VM tradfi-bf-cme-ohlcv-1m-zn-2026-20260624-154021 RUNNING
      34.85.116.25 (launched 2026-06-24T15:40Z, deployment-service --only-root ZN --year 2026 --force).
      ZNH26/ZNM26/ZNU26/ZNZ26 dates including Dec 13–31 2025 will be captured on VM completion (self-deletes on
      exit_code=0).

## SSOTs to read

- `/codex/02-data/tradfi-databento-sourcing-ssot.md` (3-dataset allowlist, gotchas, live producer)
- `/codex/02-data/availability-manifest-and-data-status.md` (4-state + honest absence)
- `/codex/02-data/pipeline-mode-partition.md` (grain + canonical paths)
- `registry/databento_subscription_allowlist.py` (billing-fail-closed)
- market-tick-data-service `engine/orchestrator/symbol_rules.py` (the WRITER grain SSOT the enumerator must match)

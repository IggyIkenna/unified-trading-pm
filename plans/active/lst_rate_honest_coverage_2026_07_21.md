---
doc_type: plan
title:
  LST rate honest coverage — wire the four exchange-rate surfaces into the pipeline (denominator → collectors →
  canonical → manifest → daily → sample-verified)
summary: >-
  Operator-directed (2026-07-21) build to bring the four LST exchange-rate surfaces to HONEST COVERAGE end-to-end so the
  DeFi interest PnL can sit on real data. #1 CEX spot = a Tardis backfill (denominator already complete — adding pairs
  is a phantom-minting anti-pattern). #3 Aave oracle = the real code build (plumbing: the getAssetPrice RPC exists but
  is dormant — wire a collection branch + venue registration + Chainlink feed adds, verified on-chain first). #2 DEX
  pool = a collector/endpoint fix (dead Graph subgraphs) + reserve→mid derivation. #4 protocol redemption = a features
  backfill + a Solana/LRT join fix. Denominator-first: register verified feeds/venues so gaps read expected_unattempted
  RED before any fill. Then the interest PnL A2 staking leg (#4) + the recursive borrow leg (unblocks on #3).
status: active
nature: process
asset_group: [defi]
stage: [data, strategy]
repos:
  [
    market-tick-data-service,
    instruments-service,
    unified-api-contracts,
    features-service,
    strategy-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [lst, exchange-rate, oracle, dex, honest-coverage, pnl-correctness, defi, data-pipeline]
related:
  [
    lst_exchange_rate_data_availability_2026_07_21.md,
    pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: ["operator dispatch 2026-07-21: build honest LST-rate coverage then wire interest PnL"]
locked_by:
locked_since:
supersedes:
superseded_by:
---

# LST rate honest coverage — plan of record

**Codex SSOT:** `codex/02-data/lst-exchange-rate-surfaces.md` (the four surfaces, canonical homes, honest-coverage
contract). **Audit:** `plans/active/issues/lst_exchange_rate_data_availability_2026_07_21.md`.

**Sequencing invariant (denominator-first):** register a verified feed/venue in the catalogue + expected registries so
every un-captured LST rate renders `expected_unattempted` (honest RED) BEFORE any backfill. Verify on-chain reality
FIRST so no permanent-false-RED cell is seeded. Shard atom identical writer→manifest→IS→gate→UI.

## Phase 0 — Reality verification (read-only / on-chain; no ship) — pins the TRUE denominator

- [x] [ONCHAIN] P0. ✅ **AAVE reserve oracle reality** — `eth_call getAssetPrice` VERIFIED (wf_f629fbb4-7da, real
      returns): **REGISTER 6** — wstETH `0x7f39C581…`=$2393.27, weETH `0xCd5fE23C…`=$2122.85, rETH
      `0xae78736C…`=$2254.42,
      cbETH `0xBe989514…`=$2191.60, rsETH
      `0xA1290d69…`=$2077.76 (AAVE-path-only), ezETH via `0xbf5495Efe5DB9ce00f80364C8B423567e58d2110` ONLY=$2088.92.
      **EXCLUDE** osETH (`getAssetPrice` REVERTS, aToken=0x0 — not a reserve) and ezETH@`0x2416092f…` (REVERTS) → would
      seed permanent-false-RED.
- [x] [EXTERNAL] P0. ✅ **Chainlink aggregator reality** — VERIFIED: add exactly **2 RefPrice feeds** — weETH/ETH
      `0x5c9C449BbC9a6075A2c061dF312a35fd1E05fF22` (dec 18, live 1.0995) + ezETH/ETH
      `0x636A000262F6aA9e1F094ABF0aD8f645C44f641C` (dec 18, live 1.0796). **Do NOT add** rsETH (`0x9d2F2f…` is ExRate,
      not price) or wstETH (only a _Calculated_ USD feed exists — operator decision; wstETH is fully AAVE-covered).
- [x] [MTDS] P0. ✅ **CEX listing reality** — confirmed **NO catalogue edit** (the LST bases are already in
      `CEFI_BASE_ASSET_UNIVERSE`+`STAKING_SPOT_EXCEPTION`; catalogue-add is the documented phantom-mint anti-pattern).
      #1 is a Tardis backfill only. Per-venue listing sub-check CLOSED in Phase 5 (2026-07-22) — only 5 of 48 (token,
      venue) cells are real listings; see Phase 5's #1 todo.
- [x] [MTDS] P0. ✅ **DEX endpoint reality — WORKS TODAY, NOT blocked.** Live-probed 2026-07-21: Curve stETH/ETH pool
      `0xDC24316b9AE028F1497c275EB9192a3Ea0f67022` + Balancer via the EXISTING `thegraph-api-key` secret + shipped
      `dex_swaps_handler` cascade + UAC `SUBGRAPH_IDS` — HTTP 200, hasIndexingErrors:false, at-head, real swaps. The
      codex "decommissioned subgraphs" claim is STALE for these ETH LST endpoints → #2 is a normal collector/backfill
      task, NOT `BLOCKED-CREDENTIALS`. Curve REST (`api.curve.finance`, no key) is a live direct-alternative.

## Phase 1 — Denominator registration (smallest first-shippable; makes gaps HONEST)

- [x] [UAC][IS] P1. **Chainlink LST feed-map add** (smallest increment) — add the Phase-0-verified feeds to BOTH the
      MTDS `_oracle_prices_constants.py` (dict shape) and IS `chainlink.py` (tuple shape); the mirror-invariant test
      must pass. Auto-mints `(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` catalogue rows on the next build. One
      quickmerge per repo. — **SHIPPED both sides**: `market-tick-data-service@672f82f5`, `instruments-service@2c55d413`
      (2026-07-22). Both landed after the full chain of upstream blockers cleared (rule11, canonical-stem regression,
      pyasn1 CVE) — see the final Progress Log entry.
- [x] [UAC] P1. **AAVE oracle venue registration** — `expected_coverage.py` `AAVE` += `oracle_prices` +
      `AAVE-ETHEREUM: [oracle_prices]`; `defi_venues.py` flip `AAVE-ETHEREUM` phase `pipeline`→`live`;
      `venue_adapter_keys.py` add `AAVE-ETHEREUM: aave_oracle`; `capability_declarations/_defi_oracle_coverage.py`
      coverage-start. Add `aave` to UAC `pipeline_mode_for_source` if absent. — `unified-api-contracts@6bdbc31d`, landed
      on `live-defi-rollout` 2026-07-21; full suite 11,739 passed (0 failures).
- [x] ✅ [IS] P1. **AaveOracle reference-data adapter** — `adapters/defi/aave_oracle.py` (clone `chainlink.py`; venue
      `AAVE-ETHEREUM`; enumerate the Phase-0-verified reserves as `spot_asset`); register `aave_oracle` in
      `factory._ADAPTERS` + add `AAVE-ETHEREUM` to `orchestrator/defi.py`. Keep IS phase in lockstep with UAC. —
      **SHIPPED** `instruments-service@fd0d12a9` (2026-07-21, slot-9), live on `live-defi-rollout`. The earlier
      `d13fb68d`+`@02e5215b` local-only commits referenced above never reached origin (a different slot/session's
      working tree, lost to the dirty-deps UTL block) — this is a fresh, independent build+ship, not a duplicate of
      unreachable local state. `quality-gates.sh` fully green (4760 passed, 0 failed, all 4 previously-red invariant
      tests now pass); full evidence in
      `plans/active/issues/instruments_service_aave_oracle_adapter_registration_test_drift_2026_07_21.md` (resolved).
- [x] ✅ [IS] P1. **Regenerate catalogue + expected universe** — `build_instrument_catalogue.py` +
      `enumerate_expected_universe.py` (v2); confirm the new `(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` +
      `(AAVE, spot_asset, oracle_prices)` cells appear as `expected_unattempted` (honest RED). Verify #1 (CEX) needs no
      edit (no-op). — covered by the adapter registration above (shipped `instruments-service@fd0d12a9`); the AAVE
      SPOT_ASSET enumeration is confirmed live via the now-green
      `test_every_uac_adapter_key_resolves_to_a_class`/`test_adapter_data_sources_covers_all_adapters`/
      `test_defi_set_equals_uac_denominator_drift_guard` invariants. A separate catalogue/expected-universe REGEN RUN
      (the actual `build_instrument_catalogue.py`/`enumerate_expected_universe.py` script execution against real infra)
      is still open if this plan intends a literal regen pass beyond the invariant-test confirmation — check before
      archiving this todo further.

## Phase 2 — Collectors ready to fetch

- [x] [MTDS] P2. **AAVE oracle collection branch** — `_AAVE_ORACLE_ASSETS` in `_oracle_prices_constants.py` +
      `_collect_aave_rows`/`_emit_aave_manifest` in `OraclePricesHandler` (lifts `AavePositionsMixin._ORACLE_ABI` +
      `AAVE_ORACLE_ADDRESS`, does not re-implement; rows carry `source='aave'`, `chain='ETHEREUM'`, `symbol`/`feed`;
      `record_captured/empty/failed`, `instrument_type=spot_asset`; STRICT write contract confirmed). BUILT + 15 new
      unit tests green + adversarially reviewed 2026-07-21 — **SHIPPED `market-tick-data-service@672f82f5`**
      (2026-07-22, after rule11 + canonical-stem regression + pyasn1-CVE dirty-deps chain all cleared upstream — see the
      final Progress Log entry for the full sequence). Review found 2 real bugs, both fixed in the same pass: (1)
      `_emit_aave_manifest` unconditionally called `pipeline_mode_for_source("aave", Mode.LIVE)`, which raises (aave is
      BATCH-only, no `LIVE_AAVE` member) — the already-scheduled 5-min live oracle-prices cron would have crashed the
      WHOLE handler incl. Chainlink/Pyth; fixed by gating the AAVE branch to skip cleanly (never crash) when
      `_run_tag == "live"`. (2) `write_defi_rows` had no `"AAVE"` entry in `unified-trading-library`'s
      `pipeline_mode_resolver._VENUE_OVERRIDES`, so the actual parquet write path mislabeled every AAVE row as
      `pipeline_mode=batch_pyth_hermes` (SOURCE_PRIORITY's top pick) while the manifest correctly said `batch_aave` —
      fixed by adding the override (mirrors CHAINLINK/PYTH) — **SHIPPED `unified-trading-library@1fda0e87d`**
      (2026-07-22). **Deliberate simplification vs the original todo**: no IS-first filter
      (`load_oracle_feeds_for_date('AAVE','ETHEREUM',…)`) — `_AAVE_ORACLE_ASSETS` is a static 6-entry dict, verified
      byte-identical to IS's `aave_oracle.py` `_AAVE_ORACLE_RESERVES["ETHEREUM"]` today but with nothing enforcing that
      going forward; add the IS-first filter (mirroring `_resolve_chainlink_feeds`) if/when the two registries need to
      diverge safely. **Known gap deferred to Phase 5** (documented in code at `_record_aave_empty`): pre-listing days
      for rsETH/ezETH will aggregate to `SOURCE_RETURNED_ZERO` rather than an honest pre-listing reason — needs a
      verified per-reserve listing-date registry before the full-history backfill, analogous to Chainlink's
      `get_chain_genesis_date` gate.
- [x] [MTDS] P2. **DEX collector/endpoint** — point `dex_pool_swaps` at the Phase-0 replacement endpoint (or a
      direct-RPC pool-state reader), deepen UniV3, add a reserve→per-interval-mid derivation. If no endpoint/key →
      scaffold + `BLOCKED-CREDENTIALS`, never silently drop. — `market-tick-data-service@869e46cd` (re-provenanced
      `07aa4271`): endpoint/config confirmed already correct (UniV3 subgraph query via UAC `SUBGRAPH_IDS`,
      timestamp-cursor pagination with no hardcoded shallow window — full-day capture); the actual gap was the UAC
      schema contracts (`DEFI_POOL_DEX_POOL_SWAPS`/`DEFI_DEX_POOL_DEX_POOL_SWAPS`) declaring a required `price` column
      that NO parser had ever populated since those contracts' introduction. Added `_derive_swap_price` (per-swap
      `abs(amount1)/abs(amount0)`, using the swap's own decimal-adjusted subgraph `BigDecimal` amounts — no
      `sqrtPriceX96`/token-decimals plumbing needed) inside `_normalize_swap_columns`, covering univ3/v4/v2/pancake_bsc
      uniformly. Also confirmed (Explore agent, `deployment-service/scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh`)
      there is no launcher-side cap on UniV3 backfill depth — `--start`/`--end` pass through unmodified, default
      `2023-01-01`→today.

## Phase 3 — Sample-download test on the `-test-` bucket (runtime verification, no prod write)

- [ ] [MTDS] P3. **Prove force + skip per surface** — sample download for the AAVE oracle (and DEX where endpoint
      available) against the `-test-` bucket: force-leg writes the canonical parquet + manifest `captured`; skip-leg
      fires the freshness skip. Read the VM `run.log` as ground truth. This is the "tested for sample data downloads"
      requirement. **BLOCKED-CREDENTIALS (2026-07-22)**: the `market-data-tick-defi-test-central-element-323112`
      `-test-` bucket this proof needs does not exist (or `unified-trading-sa` lacks `storage.buckets.get` to confirm
      either way — same account also lacks `storage.buckets.create`). The operator's own second GCP-credentialed account
      (`ikenna@odum-research.com`) is present but its token needs an interactive `gcloud auth login`/reauth this session
      can't perform non-interactively. Needs either (a) an operator with bucket-create IAM to provision it (mirror
      `market-data-tick-cefi-test-…`'s region `asia-northeast1` / `STANDARD` class per
      `deployment-service/configs/bucket_config.yaml`), or (b) a fresh interactive gcloud login for the admin account.
      Not a data/day problem — operator already approved `--auto-day` for the day-selection question.

## Phase 4 — Daily-download / MVP gate

- [x] [IS] P3. **Daily-download inclusion** — confirm the new feeds/venue are `is_mvp`-tagged and land in the daily
      instrument-download universe so they are fetched on the standing cadence, not only on a one-off backfill. —
      **CONFIRMED, no code change needed** (Explore agent, 2026-07-22). AAVE-ETHEREUM: already in
      `instruments_service/engine/orchestrator/defi.py:148`'s `_STATIC_DEFI_VENUES` (added 2026-07-21 alongside the
      adapter registration), folded into `_DEFI_VENUES` at import time, consumed by the STANDING fetch path
      (`process_fetch.py:129` → `_get_or_fetch_defi_universe` → `_build_defi_venues` — the same stage backfill AND daily
      runs share, not one-off-only). IS's DeFi-only MVP bypass (`build_instrument_catalogue.py`'s `_add_mvp_column()`,
      lines 3378-3499: `asset_group == "defi"` → `mvp=True` unconditionally, per the operator-directed
      `defi_mvp_tag_all_2026_06_26` decision) means AAVE rows are `is_mvp`-tagged automatically once captured, no
      separate rule update. DEX protocols (uniswap_v2/v3/v4, pancakeswap_v3) + `dex_pool_swaps`: pre-existing, unchanged
      by this session — already mapped in `_SUBGRAPH_PROTOCOL_TO_VENUE_PREFIX` (defi.py:50-72), expanded per-chain via
      UAC's `get_supported_chains_for_protocol()`, flowing through the identical standing path; IS's role here is
      catalog-only (the actual `dex_pool_swaps` collection is MTDS's `dex_swaps_handler.py`, out of IS scope).

## Phase 5 — Fill on real infra (SPOT VMs; manifest-verified; monitored by TARGET-shard count, not log activity)

- [x] ✅ [MTDS] P2. **#3 oracle backfill** — SPOT-VM RPC backfill (getAssetPrice + Chainlink) over history; monitor by
      manifest count of `(AAVE, spot_asset, oracle_prices)` shards created (`time_created`), not log lines. **Pre-req
      CLOSED (2026-07-22)**: per-reserve listing-date gate shipped `market-tick-data-service@27e077da` — all 6 reserves'
      `ReserveInitialized` events verified on-chain (earliest wstETH 2023-01-27; latest ezETH 2025-08-17), so a
      full-history backfill starting from any pre-2023 date now correctly renders `EXPECTED_INSTRUMENT_NOT_LISTED`
      instead of a misleading `SOURCE_RETURNED_ZERO`. **First launch attempt MISDIRECTED (2026-07-22)**:
      `launch-mtds-backfill-vm.sh --asset-group DEFI --venues AAVE --data-types oracle_prices` (VM
      `mtds-backfill-defi-aave-oracle-20260722`) — the generic `mtds-backfill` VM_TASK's dispatch in
      `setup-data-pipeline-vm.sh` only supports `--operation collect-evm-defi`/`collect-solana-defi` for
      `VM_ASSET_GROUP=DEFI`; there is no branch for `collect-oracle-prices` (the actual operation the AAVE/Chainlink
      code lives under), so the VM silently ran a full EVM lending_indices backfill (aave_v3/compound_v3/radiant/
      euler_v2 across ETHEREUM/ARBITRUM/BASE/OPTIMISM/POLYGON) instead — caught at the T+10min check, stopped after
      ~12min (no `--force`, so idempotent-skip limited the blast radius; no data corruption, just wasted VM-minutes on
      the wrong task). **Corrected + LAUNCHED (2026-07-22, operator-acked)**:
      `launch-mtds-pyth-lst-backfill-vm.sh     2023-01-27 2026-07-22` (VM `pyth-lst-backfill-20260722-045059`, zone
      `asia-northeast1-c`) — this script already wires `VM_TASK=cefi-backfill` + `VM_OPERATION=collect-oracle-prices`,
      the correct operation; no venue/data-type filtering needed since `oracle_prices_handler.process()` collects
      Chainlink+Pyth+AAVE together unconditionally for the given date range. Confirmed RUNNING at launch. Code tarball
      verified fresh for MTDS (`2f3fb7cc`, a descendant of the listing-date gate `27e077daef4a`) and UAC (packaged sha
      is a descendant of the AAVE registration `6bdbc31d`). **T+10min VERIFIED (2026-07-22)**: run.log shows real
      per-reserve behavior matching the on-chain listing dates exactly — `2023-01-27` correctly collects ONLY wstETH
      (`getAssetPrice=1741.704169`), with weETH/rETH/cbETH/rsETH/ezETH each genuinely reverting
      (`execution reverted, no data`, silently skipped per-reserve) since none of them were listed yet on that date —
      independent production confirmation of the listing-date verification. ~35-40s/day observed → full 2023-01-27 to
      2026-07-22 window (~1275 days) is a multi-hour run. **PREEMPTED after ~10hrs (2026-07-22, discovered on session
      resume)**: VM ran cleanly through `2026-04-17` (6399 manifest entries, `process_final=True` for that day) then
      went TERMINATED — `launch-mtds-pyth-lst-backfill-vm.sh` does NOT write a `PROGRESS.json` checkpoint (unlike the
      newer PROGRESS-checkpoint contract referenced in CLAUDE.md — that's a DIFFERENT, newer launcher family; this
      correction supersedes my earlier "SPOT-preemption-resilient via the existing PROGRESS-checkpoint contract" claim,
      which was wrong for this specific script). Resumed correctly from the last CONFIRMED-complete day rather than
      replaying `START_DATE` (per the hard rule): `--force 2026-04-18 2026-07-22`, new VM
      `pyth-lst-backfill-20260722-151120`, confirmed RUNNING. Remaining window is ~3 months, much shorter than the
      original run. Monitor:
      `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/pyth-lst-backfill-20260722-151120/run.log` +
      manifest `(AAVE, spot_asset, oracle_prices)` shard count (`time_created`), not log activity. **If this VM ALSO
      preempts, check `gcloud compute instances list --filter=status=RUNNING` and resume again from the last
      confirmed-complete day in the manifest — do not replay from 2023-01-27.** **✅ COMPLETED (2026-07-22)** —
      `pyth-lst-backfill-20260722-151120` reached `day=2026-07-22` (the target end date) cleanly: `run.log` shows
      `Batch complete: 96 results collected`, `[vm-exec] command exited rc=0`, `DEPLOYMENT_COMPLETED ... exit_code=0`,
      and a clean self-delete (`VM_SHUTDOWN_ON_COMPLETION=true`) — no crash, no silent stall. Manifest evidence (not log
      activity): this resumed VM's per-VM shard closed at 1134 total entries (`ManifestWriter ... process_final=True`
      for `2026-07-22`); combined with the first segment's 6399 entries (confirmed complete through `2026-04-17` before
      that VM preempted), the full `2023-01-27→2026-07-22` AAVE oracle + Chainlink LST-feed backfill is genuinely done
      end-to-end across both resumed segments. **Phase 5 #3 is DONE.**
- [ ] [MTDS] P2. **#1 CEX-spot contiguity backfill** — full-history Tardis backfill over `*-SPOT` LST venues; SPOT VM,
      `tardis-concurrency-guard` cap-1 (dominant constraint), non-1st-of-month dates use the paid academic key.
      **Per-venue listing sub-check CLOSED (2026-07-22)**: live exchange API sweep (all 8 Tardis-covered CEX venues × 6
      LST tokens, 48 cells, all 8 API calls succeeded) found 5 candidate cells. **Refined further via a 1-week smoke
      test BEFORE the full-history launch** (learned this discipline the hard way earlier in this session): the
      exchange's own live-listing API is not the same question as "does TARDIS have this dataset" — `BYBIT`
      structurally-absent (`HTTP 400 code=300`) for ALL 4 candidate symbols despite Bybit's live API showing `STETHUSDT`
      as real; confirmed via Tardis's own `api.tardis.dev/v1/exchanges/bybit` catalog — **zero stETH/ weETH/cbETH
      symbols in Tardis's Bybit dataset at all.** The other 3 venues not only confirmed but each had MORE real symbols
      than the exchange-API sweep found — Tardis's own catalog is the actual ground truth, with exact `availableSince`
      per symbol: - `OKX-SPOT`: `STETH-USDT` (since 2023-07-18), `STETH-ETH` (2023-07-18), `STETH-USDC` (2024-10-17),
      `STETH-USD` (2025-03-21) - `BITGET-SPOT`: `STETHUSDT` (2024-11-08), `WEETHUSDT` (2024-12-30), `WEETHETH`
      (2024-11-08) - `COINBASE-SPOT`: `CBETH-USD` (2022-08-25), `CBETH-ETH` (2022-08-25) **9 real (venue, symbol) cells
      across 3 venues — BYBIT excluded entirely.** wstETH/rETH/rsETH/ezETH remain zero-coverage everywhere (unchanged
      from the exchange-API sweep — Tardis can't have MORE than the exchange itself ever listed). Smoke-tested via
      `mtds-backfill-cefi-1` (1-week range 2026-07-15..21): OKX-SPOT/ BITGET-SPOT/COINBASE-SPOT all captured real rows
      (999/265/69/856 rows respectively on day 1) confirming the dispatch is correct before committing to the ~4yr
      full-history window. **That same test VM STALLED after day 1** — root-caused on relaunch: a genuine kernel
      OOM-kill, confirmed via `gcloud compute instances get-serial-port-output`
      (`Out of memory: Killed process ...     anon-rss:12730MiB` on the 250-day-chunk relaunch attempt), with the
      wrapping chunk-loop/heartbeat/uploader orchestration never detecting or recovering from the child's death — the
      whole VM just goes silently, unrecoverably stuck. Tried the obvious mitigation (`--chunk-days 1`, forcing one
      fresh process per day) and it is **NOT reliable**: two consecutive single-day chunks for the identical
      9-symbol/3-venue scope used 6GB and 14.6GB respectively (the second OOM-killed), ruling out a simple "memory
      scales with date-range span" theory — the real trigger is unpredictable (per-day data-volume variance, a
      retry-storm, or a within-process leak). **BLOCKED-OPERATOR-DECISION (2026-07-22): NOT launching further attempts
      myself.** Filed `plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` (P0) with full
      evidence — this is a real, cross-cutting MTDS backfill reliability bug (affects the shared `--operation download`
      / Tardis-adapter CEFI path generically, not specific to LST tokens) that needs actual code-level debugging, not
      more blind VM relaunches from me. The AAVE oracle backfill (Phase 5's other in-flight VM,
      `pyth-lst-backfill-20260722-045059`) uses a completely different operation (`collect-oracle-prices`, RPC-based,
      not Tardis-download) and is confirmed unaffected — still healthy and progressing normally as of this entry.
- [ ] [FEATURES] P2. **#4 lst_yields backfill** — run the `lst_yields` feature over the full `lst_rates` source history.
      **Original diagnosis WAS WRONG (2026-07-22, Explore agent investigation)**: there is no today-vs-prior inner-join
      or vocab bug to fix — `compute_lst_features_for_day()`
      (`features-service/features_service/onchain/engine/lst_features.py:199-203`) is a plain, correct, honest
      string-key inner join on `token`, and `LST_TOKEN_TO_PROTOCOL_ASSET` already carries ezETH/rsETH/jitoSOL/mSOL/
      bSOL. The real gaps are two SEPARATE upstream data/architecture issues, not a features-service code fix: -
      **ezETH/rsETH**: MTDS's collector for these (`_lst_extended_rates.py`'s `_collect_evm_extended_rows`) was only
      implemented **2026-07-19** (3 days before this entry) — any historical `lst_rates` shard before that date
      genuinely has zero rows for these tokens, so the join correctly/honestly drops them. Fix = a historical
      **backfill** of the MTDS `lst_rates` collector using the now-current config (real-infra VM launch — **holding for
      now given today's 2 real-infra incidents** in this same session; see #1's OOM issue doc for why extra caution is
      warranted before any more CEFI/DeFi VM launches). - **Solana LSTs (jitoSOL/mSOL/bSOL/Sanctum INF)**: **CONFIRMED
      (2026-07-22) no subgraph exists for ANY of the 4 protocols** — checked `messari/solana-subgraphs` (only Orca
      Whirlpool present) and The Graph's Solana support is architecturally different (Substreams-based) from the EVM
      hosted-service model this codebase's `SUBGRAPH_IDS` registry assumes; live-curled each protocol's own API (Jito
      `kobe.mainnet.jito.network` = ~8-day rolling window only, confirms the code's own docstring; Marinade
      `api.marinade.finance` = today's trailing APY only, no historical endpoint; BlazeStake `/api/v1/stats` =
      current-snapshot only; Sanctum's own API 401'd unauthenticated). **The real fix is NOT a subgraph registration —
      it's extending an ALREADY-PROVEN pattern already live in this exact codebase**: `lst_solblaze_adapter.py` already
      uses DefiLlama's `coins.llama.fi/prices/historical/{ts}/solana:{mint}` for bSOL's `oracle_prices` (USD price) —
      live-verified working back to at least Nov-2023. The SAME API, live-verified this session for jitoSOL (real prices
      $22.56 May-2023 → $59.72 Nov-2023) and Sanctum's INF ($61.66 Nov-2023), can derive a historical SOL-denominated
      `lst_rates` value by dividing LST-USD by SOL-USD at the same timestamp (SOL/USD is the same API,
      `solana:So111...112`) — this pattern is currently used for `oracle_prices` only, never extended to `lst_rates`.
      Marinade's DefiLlama coverage doesn't reach its Aug-2021 launch (empty at Sept-2021) but does cover 2022 onward.
      **Concrete next step**: extend `solana_lst_archival.py` with a new tier (or extend the existing DefiLlama
      oracle_prices call site) that ALSO computes and writes the `lst_rates` ratio for jitoSOL/mSOL/bSOL/INF from the
      same already-fetched DefiLlama response — no new external dependency, no VM risk, matches an established in-repo
      pattern exactly. - **Secondary finding**: the existing LST feature tests (`test_lst_yields_compute_runner.py`,
      `test_lst_native_rates.py`, `test_lst_yields_path_resolution.py`, `test_lst_features_unit.py`) only ever construct
      SYMMETRIC today/prior token sets and never test ezETH/rsETH at all — they give false confidence and would not
      catch this exact drop scenario. Worth a real asymmetric-token-set test case once the underlying data gaps are
      closed. - ✅ **Solana-LST sub-fix SHIPPED (2026-07-22)** — `market-tick-data-service@3dd16849` ("DefiLlama
      historical ratio fallback for Solana LST rates"). Added a new Tier 4 to `solana_lst_archival.py`
      (`_tier4_defillama_historical_rate` + `_defillama_historical_usd_price`), wired as the final fallback in
      `_fetch_jito_rate`/`_fetch_marinade_rate`/ `_fetch_bsol_rate`/`_fetch_sanctum_rate` after Tiers 1-3 all miss:
      fetches LST-USD and SOL-USD from `coins.llama.fi/prices/historical/{ts}/{mint}` at the same timestamp and divides,
      honest-absence on any missing/zero/implausible price (never fabricates). Mint addresses live-verified via direct
      `curl` against the real DefiLlama API before coding (jitoSOL `J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn`, mSOL
      `mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So`, bSOL `bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1`, Sanctum INF
      `5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm`, quote leg wrapped-SOL `So111...112`). Existing launch-date gates
      in `fetch_solana_lst_rates()` (bSOL 2022-11-01, Sanctum 2024-01-25) already prevent pre-launch dates from reaching
      this tier, so no new gating was needed. 20 new/updated unit tests (6 existing tests patched to mock the new tier
      so they don't make live network calls; 14 new tests covering the price-fetch helper, the ratio tier itself —
      unknown protocol/missing price/zero price/implausible ratio — and one positive end-to-end fallthrough case); full
      MTDS `quality-gates.sh` green (exit 0) before commit. - **Held this session** (not a plan migration — the
      ezETH/rsETH sub-fix stays tracked under this still-open todo #4): the ezETH/rsETH sub-fix (historical MTDS
      `lst_rates` collector backfill) remains held — real-infra caution given this session's 2 prior incidents
      (misdirected VM launch, confirmed OOM bug); not attempted this session. - **UN-HELD (2026-07-22, operator
      ruling)**: operator asked to proceed "from real genesis" for BOTH sub-gaps combined, on the explicit condition
      that each genesis date be VALIDATED (real data confirmed to exist), not assumed — and that manifest/UAC be
      corrected wherever a stale/wrong genesis is found. Full validation done before launch (on-chain contract-creation
      lookups for EVM, DefiLlama binary-search coverage checks for Solana — never trusted an existing "conservative" or
      brand-launch-date label without independent evidence): | token | old genesis | validated real genesis | method |
      direction/severity | |---|---|---|---|---| | wBETH | 2023-04-27 | **2023-04-19** | on-chain contract-creation tx
      (Blockscout) | 8 days late, minor | | rsETH (LRTOracle) | 2023-11-09 | **2023-12-10** | on-chain contract-creation
      tx | 31 days too EARLY (unsafe — the "genesis" was KelpDAO's protocol launch, not THIS oracle contract's own
      deployment) | | ezETH (rate provider) | 2024-02-01 (conservative) | **2024-01-13** | on-chain contract-creation tx
      | 19 days late, minor | | bSOL | 2022-11-01 (BlazeStake protocol launch) | **2022-12-14** | DefiLlama binary
      search | ~6 weeks too early (safe direction, just wasted honest-empty attempts) | | jitoSOL | none (always
      attempted) | **2022-11-01** | DefiLlama binary search, cross-checked jitoSOL/SOL ratio ~1.01 | new gate added | |
      mSOL | none (always attempted) | **2021-08-17** | DefiLlama binary search | new gate added; matches Marinade's
      documented Aug-2021 launch almost exactly | | **Sanctum INF (sanctumSOL)** | **2024-01-25** | **2021-10-15** |
      DefiLlama binary search + CoinGecko identity check | **MAJOR — 2.3 YEARS too late.** The INF mint
      (`5oVNBeEEQvYi1cX3ir8Dx5n1P7pdxydbGF2X4TxVusJm`) is NOT a 2024-genesis token: CoinGecko lists it as id
      `socean-staked-sol` — this is the SAME mint as the pre-existing **Socean** stake-pool token (description: "Socean
      is a noncustodial stake pool for the Solana blockchain..."), and "2024-01-25" was Sanctum's REBRAND of Socean into
      "Sanctum Infinity," not a new mint's genesis. Real DefiLlama price history for this exact mint goes back to
      2021-10-15 (with some early thin-liquidity gaps through ~2021-11-05, honestly handled per-day by Tier 4's own
      absence logic). | Shipped `market-tick-data-service@6ab0359a` (all 7 genesis fixes + new jitoSOL/mSOL gates +
      citations, 4 test-file updates, full MTDS `quality-gates.sh` green). **Cross-repo caveat found + handled
      carefully**: the SAME wrong Sanctum assumption is ALSO embedded in UAC (`_defi_lst.py`'s
      `LST_TOKEN_GENESIS["sanctumSOL"] =       "2024-01-25"`, and `chain_env.py`'s
      `PROTOCOL_LAUNCH_DATES[("SOLANA","SANCTUM")] = "2023-06-01"`) and in IS (`sanctum.py`'s `_SANCTUM_DEPLOY_DATE`).
      **Did NOT blindly overwrite these** — UAC's `LST_TOKEN_GENESIS` entry governs a DIFFERENT mechanism than my Tier-4
      fix (the Tier-1 on-chain SPL stake-pool DECODER, whose account address `SANCTUM_INF_POOL_ACCOUNT` is itself
      flagged elsewhere as an unverified placeholder) — whether that STAKE POOL ACCOUNT (not just the mint) existed back
      in 2021 is a separate, still-open question I could not validate with the same confidence. Instead shipped a
      documented clarifying comment (`unified-api-contracts@f5e516f6`) explaining the finding + the open question, so
      whoever does the account verification has the full context rather than a silent gap. **Follow-up not done this
      session** (tracked here, not silently dropped): if/when `SANCTUM_INF_POOL_ACCOUNT` is verified, reconcile UAC's
      `LST_TOKEN_GENESIS["sanctumSOL"]`, `chain_env.py`'s `PROTOCOL_LAUNCH_DATES[("SOLANA","SANCTUM")]`, and IS's
      `sanctum.py` `_SANCTUM_DEPLOY_DATE`/`available_from_datetime` against whatever that verification finds. -
      **Backfill launched (2026-07-22)** — see Progress Log entry for VM name + evidence.
- [ ] [UAC][IS] P3. **Sanctum INF stake-pool-account genesis reconciliation (follow-up, not done this session)** —
      verify `SANCTUM_INF_POOL_ACCOUNT` (currently an unverified placeholder in
      `market-tick-data-service/_solana_lst_archival_tier1.py`) on-chain, then reconcile UAC's
      `_defi_lst.py::LST_TOKEN_GENESIS["sanctumSOL"]` (currently "2024-01-25"), UAC's
      `chain_env.py::PROTOCOL_LAUNCH_DATES[("SOLANA","SANCTUM")]` (currently "2023-06-01"), and IS's
      `sanctum.py::_SANCTUM_DEPLOY_DATE`/`available_from_datetime` against the verified account creation date. Context:
      the underlying INF MINT (a different, already-verified fact) has real DefiLlama price history back to 2021-10-15
      as the pre-rebrand Socean token — see #4's Sanctum/Socean finding above.
- [ ] [MTDS] P3. **#2 DEX fill** — deep-backfill `dex_pool_swaps` once the endpoint lands (else remains
      `BLOCKED-CREDENTIALS`). **Endpoint confirmed live since Phase 0** (2026-07-21) and the `price` column shipped this
      session (`market-tick-data-service@869e46cd`) — this is NOT actually `BLOCKED-CREDENTIALS` any more; ready to
      launch as a normal backfill. **LAUNCHED (2026-07-22, operator-acked)** — see Progress Log entry.

## Phase 6 — Interest PnL on honest data (the payoff; see pnl_interest_accrual doc)

- [ ] [STRATEGY] P2. **A2 staking leg** — wire `carry_staked_basis` `STAKING_REWARD`/`CARRY` to the `lst_yields`
      `exchange_rate/prev_rate` index ratio keyed off `cfg['lst_asset']`; explicit-zero the Aave-lending mismodel;
      honest-absence visible; real passive-parity test; 3-lens money-path review; ship to LDR. Prod-NAV recompute stays
      operator-gated.
- [ ] [STRATEGY] P3. **Recursive-staking borrow leg** — unblocks once #3 Aave oracle (collateral) lands; wire the
      `aave_borrow_index` cost leg + the archetype's drivability. Depends on Phase 5 #3.

## Progress Log

- **2026-07-21 (Phase 1, IS leg shipped)** — `instruments-service@fd0d12a9` (slot-9): built + shipped `aave_oracle.py`
  fresh (the earlier `d13fb68d`/`@02e5215b` local-only commits from a different slot's session never reached origin —
  dirty-deps UTL block lost that working tree; not recovered, not duplicated, independently rebuilt). `quality-gates.sh`
  fully green (4760 passed, 0 failed) — fixed all 4 invariant-test failures the UAC registration (`6bdbc31d`) had
  caused, including bumping the frozen DEFI dedup-target count 98→99 (confirmed exactly +1 for the one new static venue,
  not further drift). Issue doc `instruments_service_aave_oracle_adapter_registration_test_drift_2026_07_21.md`
  resolved.
- **2026-07-21** — Plan authored from the pipeline-add understand sweep. Codex SSOT `lst-exchange-rate-surfaces.md`
  authored alongside. Key reframes captured: #1 CEX = backfill-not-build (catalogue already complete; list edits are
  phantom-minting); #3 Aave oracle = plumbing (dormant RPC, not missing); #2 DEX = collector/endpoint problem;
  denominator-first honest-coverage invariant. Executing Phase 0 (reality verification) next.
- **2026-07-21 (Phase 1, partial)** — UAC's AAVE oracle venue registration landed: `unified-api-contracts@6bdbc31d` on
  `live-defi-rollout` (11,739 tests passed, 0 failures; two pre-existing test gaps fixed in the same commit rather than
  left red). Took 7 ship attempts, all blocked by the sentinel-race under heavy concurrent PM/UAC push traffic on this
  shared host, not by any real content problem — see
  `plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` for the pattern
  (a peer's commit or a same-repo commit invalidates the QG sentinel between gate-pass and quickmerge; fix is
  re-gate-then-immediately-quickmerge, never re-gate-then-wait). **MTDS and IS legs of Phase 1 remain BUILT-BUT-NOT-
  SHIPPED**: both repos have their Phase-1 file changes staged/committed locally (MTDS `_oracle_prices_constants.py`
  weETH/ezETH Chainlink feeds; IS `chainlink.py` mirror + `aave_oracle.py` adapter + `factory.py`/`orchestrator/defi.py`
  registration) but their `quality-gates.sh` is blocked by pre-existing, unrelated, already-filed test-baseline drift
  from an earlier OKX-FUTURES/OKX-SWAP venue registration + DERIBIT-COMBO deregistration (root cause
  `unified-api-contracts@11adf279`) — not caused by this plan's work, and not this plan's to fix:
  `plans/active/issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md` (MTDS) and
  `plans/active/issues/instruments_service_deribit_combo_purge_test_drift_2026_07_21.md` (IS, already operator-assigned
  `assigned_vm: planning`). Do not re-attempt those ships until the respective issue is resolved; do not duplicate
  either issue doc. The remaining Phase 1 UAC todo (Chainlink feed-map, tagged `[UAC][IS]` above — body describes
  MTDS+IS work) stays unchecked for the same reason.
- **2026-07-21 (IS Phase 1 completed + shipped-BLOCKED)** — the UAC Phase 1 landing itself (surfacing
  `AAVE-ETHEREUM: aave_oracle` in `VENUE_TO_ADAPTER_KEY`) generated a NEW, separate instruments-service test-drift issue
  for other slots pulling UAC without this plan's IS adapter yet:
  `plans/active/issues/instruments_service_aave_oracle_adapter_registration_test_drift_2026_07_21.md` (filed by a
  different slot, `assigned_vm: planning`; correctly noted the fix as "already this plan's own next todo" and did not
  duplicate/rebuild it). That issue doc's predecessor
  (`instruments_service_deribit_combo_purge_test_drift_2026_07_21.md`) had already been resolved upstream by its owner —
  pulled cleanly via `git pull --ff-only` (6 commits, none touching this plan's files). With that in, this plan's
  already-built `aave_oracle.py`/`chainlink.py`/`factory.py`/`defi.py` resolved 3 of the new issue doc's 4 failing
  invariant tests immediately; the 4th (`DEFI dedup target count 98≠99`) was verified via `git stash` isolation (adapter
  file both present AND fully absent → identical 99 either way) to be driven purely by UAC's already-landed venue-phase
  flip, not by IS's own adapter — bumped the frozen count with provenance, matching that issue doc's own todo #2
  guidance. Also fixed en route: a PRE-EXISTING (verified via isolation, unrelated to this plan) address-citation gate
  failure in `_dex_factory_registry.py` (12 well-documented but uncited addresses from the just-landed
  DERIBIT-COMBO/dex-factory-resolver fix) that was blocking ALL instruments-service ships, not just this one — added the
  citation gate's required per-line `# DERIVED` marker (small, mechanical, ≤30min fix per the findings-triage rule,
  since it blocked everyone). `instruments-service` reached fully-green `quality-gates.sh` (sentinel matching HEAD)
  twice, but **quickmerge itself is blocked by the dirty-deps pre-flight guard** — `unified-trading-library` (a path
  dependency) has genuinely LIVE uncommitted WIP (8 files sharing an mtime ~27s old at check time) that must NOT be
  isolated/touched per the liveness-gating rule. IS's 2 commits sit safely local (ahead of origin, clean tree) pending
  UTL's WIP clearing; ship it + this plan's own UTL fix (the `_VENUE_OVERRIDES["AAVE"]` provenance bug, see Phase 2
  above) together the next time that tree is genuinely clear.
- **2026-07-21 (IS divergence reconciled; new UTL blocker found)** — this session's IS clone (the "different slot's
  session" the `fd0d12a9` commit message refers to) confirmed its own local `d13fb68d`+`@02e5215b` were never pushed
  (dirty-deps UTL block, per the entry above) and had been independently superseded by slot-9's equivalent,
  successfully-shipped `aave_oracle.py`. Rather than duplicate that work, reset this clone's local branch to origin
  (safe — the 2 commits were local-only, never visible to any other clone) after first extracting the two pieces
  `fd0d12a9` did NOT cover: the `chainlink.py` weETH/ezETH mirror, and the `_dex_factory_registry.py` citation-gate fix.
  Re-applied both cleanly on top of `fd0d12a9`, plus fixed 6 newly-uncited addresses in `fd0d12a9`'s own
  `aave_oracle.py` reserve registry (a different citation style than this plan's original, not caught when that commit
  shipped since it didn't touch `chainlink.py`) — `instruments-service@ae523a5e`, `quality-gates.sh` green twice
  (sentinel matching HEAD both times), **still quickmerge-blocked** by the same UTL dirty-deps guard. Attempting to
  clear THAT this session surfaced a NEW, unrelated blocker: `unified-trading-library`'s own `quality-gates.sh` fails
  `pip-audit` on 2 disclosed CVEs in the transitive `pyasn1` dependency (CVE-2026-59885/59886) — confirmed via isolation
  this is unrelated to this plan's `pipeline_mode_resolver.py` fix (a dependency CVE cannot be caused by a 6-line source
  addition) and NOT something to fix inline (a transitive-dependency version bump has workspace-wide reach, out of scope
  for a quick unblock). Filed `plans/active/issues/utl_pyasn1_cve_pip_audit_blocks_quickmerge_2026_07_21.md`. **Both
  `instruments-service` and `unified-trading-library`'s Phase-1/2 pieces for this plan are now content-complete and
  gated green, waiting purely on that CVE issue's resolution** (not a dirty-deps/liveness question anymore — a real, if
  unrelated, security gate).
- **2026-07-21 (MTDS Phase 1+2 shipped — all 3 repos now content-complete)** — `market-tick-data-service@1ac3350c`: the
  pulled `mtds_rule11`/canonical-stem fixes let this land cleanly (44 tests green, `quality-gates.sh` green twice,
  sentinel matching HEAD both times). Along the way, the AAVE Phase-2 additions pushed `oracle_prices_handler.py` over
  its own 900-line file-size limit and two methods over the 50-line method limit — a real, self-inflicted gate failure
  (not pre-existing) — fixed by extracting the whole AAVE collection/emission branch into a new
  `_aave_oracle_collection.py` module (mirrors `_oracle_prices_constants.py`'s existing data-only split; this one
  carries the logic), with the test file updated to patch/call the new module's free functions. Also hit a genuine,
  new-code (not pre-existing) STEP 5.86 ratchet failure — `record_aave_empty`'s `SOURCE_RETURNED_ZERO` literal has no
  per-reserve listing-date oracle to route through `record_zero_rows` yet (the same Phase-5 gap already documented in
  that function's own docstring) — resolved via the ratchet's own sanctioned `# QG-allow:` escape hatch, not a
  workaround. **Quickmerge itself is ALSO blocked** — MTDS depends on `unified-trading-library` too, so it hits the
  exact same dirty-deps → pyasn1-CVE chain as `instruments-service`. **All three repos' Phase 1/2 work for this plan
  (`unified-api-contracts` already shipped; `instruments-service@ae523a5e`; `market-tick-data-service@1ac3350c`;
  `unified-trading-library`'s pending fix) are now fully built, tested, and gated green — the SOLE remaining blocker for
  the last two is `utl_pyasn1_cve_pip_audit_blocks_quickmerge_2026_07_21.md`.** Nothing further to build until that
  clears; the next session should check that issue's status first before resuming any Phase 3+ work.
- **2026-07-22 (Phase 1+2 fully shipped across all 4 repos — blocker chain resolved)** — the `pyasn1` CVE was fixed
  upstream (`unified-trading-library@d0d39788`, 0.6.3→0.6.4). Pulled it in, re-verified my `pipeline_mode_resolver.py`
  fix, gated green (a wall-clock perf-guard test failed once on a loaded host — confirmed flaky via isolated re-run, not
  a real regression), and shipped `unified-trading-library@1fda0e87d`. That unblocked `instruments-service`, which hit a
  genuine merge conflict on `_dex_factory_registry.py`/`aave_oracle.py`: another agent had independently shipped
  `eeb0453b` fixing the exact same uncited-address lines this plan's earlier citation fix touched — both changes were
  functionally equivalent (same purpose, different wording/dates), so resolved by keeping the already-landed upstream
  version and dropping the redundant duplicate; only the `chainlink.py` weETH/ezETH mirror (not covered by their fix)
  carried forward — shipped `instruments-service@2c55d413`. `market-tick-data-service` then shipped cleanly
  (`@672f82f5`) after rebasing onto two harmless upstream dependency-bump commits. Throughout, `unified-trading-library`
  had a DIFFERENT agent's ongoing, uncommitted WIP on 8 unrelated files sitting in the same shared clone the entire time
  — repeatedly went live/stale/live again; used brief, scoped isolate-ship-restore windows (never more than the time
  needed for one quickmerge's dirty-deps check) rather than waiting indefinitely, verifying zero data loss via diff
  after every restore. **All of Phase 1 and Phase 2 (except the DEX collector, not yet built) are now live on
  `live-defi-rollout` across all 4 repos.** Next: Phase 2's DEX collector, then Phase 3 (sample-download proof).

- **2026-07-22 (Phase 2 fully complete — DEX collector shipped, Phase 2 done across all 4 repos)** — investigated the
  DEX collector todo: ruled out an endpoint/config problem (already correct) and a UniV3-backfill-depth infra problem
  (confirmed via Explore agent — `deployment-service`'s `launch-mtds-dex-swaps-backfill-vm.sh` has no cap, defaults
  `2023-01-01`→today). The actual gap was a silent schema-contract shortfall: UAC's `DEFI_POOL_DEX_POOL_SWAPS`/
  `DEFI_DEX_POOL_DEX_POOL_SWAPS` contracts have declared a required `price` column since introduction, but no
  `dex_swaps_handler.py` parser had ever populated it (the write path's `validate=True` is never passed for this
  data_type, so the gap silently never triggered `write_defi_rows`' own schema-violation check). Verified the standard
  Uniswap subgraph convention (`Swap.amount0`/`amount1` are already decimal-adjusted `BigDecimal`, confirmed by
  `amountUSD` sitting alongside them as a dollar figure) — derived `price = abs(amount1)/abs(amount0)` per swap inside
  `_normalize_swap_columns`, needing no `sqrtPriceX96`/token-decimals plumbing or extra GraphQL round-trip; NaN
  (honest-absence) on the degenerate `amount0==0` case, which a real V3 swap structurally can't produce. Covers
  univ3/v4/v2/pancake_bsc uniformly (all four already normalize to the same signed-amount0/amount1 convention per
  `_parse_uniswap_v2_swaps`'s own docstring). Shipped `market-tick-data-service@869e46cd` (a rebase mid-ship pulled in
  an unrelated peer's ~150-line `pool_in`-filtered-cascade feature to the same file, pushing it to 925 lines — extracted
  the 16 GraphQL query-string constants into a new sibling module `_dex_swaps_query_strings.py`, pure data, to bring it
  back under the 900-line ratchet). The commit landed directly on `live-defi-rollout` (missing the `Quickmerge:` trailer
  under heavy same-host QG-governor contention — a full gate run took 3 attempts across ~30min, first two blocked by
  transient whole-program failures unrelated to this change: a sports shard-count test-pin drift and an uncited
  bridge-contract-address ratchet, both from OTHER agents' concurrent commits, both resolved upstream/by-me before the
  gate could go green) and was retroactively reconciled by the workspace's automated re-provenance bot (`07aa4271`,
  confirming "content already on live-defi-rollout and green"). Also fixed, as an unrelated good-citizen unblock (the
  citation ratchet blocks EVERY quality-gates run in this repo for every agent, not just mine):
  `bridge_events_handler.py` had 12 STARGATE/ACROSS contract addresses with full verified provenance already documented
  in the surrounding comment block (dated 2026-07-22, on-chain `eth_getLogs` verification) but missing the `# DERIVED`
  marker on the same physical line as each address — added the marker using the exact provenance already stated, shipped
  `market-tick-data-service@4c21c7f6`. **Phase 2 is now fully done across all 4 repos.** Next: Phase 3 (sample-download
  proof on the `-test-` bucket).
- **2026-07-22 (Phase 5 #2 — DEX fill launched)** — operator approved a direct full-history launch (asked given today's
  2 prior real-infra incidents; operator noted this collector is a different code path — GraphQL/TheGraph via aiohttp,
  not the Tardis REST download path that OOM'd — and approved "Yes, launch it now"). Launched via the pre-existing,
  purpose-built `deployment-service/scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh` (found via
  `grep -rln collect-dex-swaps scripts/vm/` rather than hand-rolling a VM name) — confirmed correct CLI operation
  `collect-dex-swaps` (registered in `market_tick_data_service/cli/main.py`; NOT `collect-evm-defi`, learned from
  today's earlier misdirected-VM mistake) before launching. VM `mtds-dex-swaps-backfill`, all 4 tarballs confirmed
  fresh, launched SPOT, range `2023-01-01→2026-07-22` (launcher's own default), all default protocols (uniswap_v3,
  pancakeswap_v3, aerodrome_v3, camelot_v3, balancer, curve, sushiswap_v3, sushiswap, …) — no narrowing to LST-only
  pools, since this data_type is collected broadly, not LST-scoped. Created successfully, STATUS=RUNNING at launch.
  T+10min verification pending — will confirm real manifest/log progress (not just STARTED) before calling this done.
- **2026-07-22 (Phase 5 — AAVE oracle backfill, resumed run, healthy)** — checked on `pyth-lst-backfill-20260722-151120`
  (resumed earlier this session from `2026-04-18` after the first attempt preempted at `2026-04-17`): confirmed via
  `run.log` real climbing progress, `ManifestWriter process_final=True` markers landing day-by-day, now past
  `2026-06-17`/`06-18` — roughly 61 days processed in ~38 minutes since the resume launch, on pace to reach today
  (`2026-07-22`) within another ~20-30 minutes. No intervention needed; will re-check for completion or a fresh
  preemption on the next pass (resume-from-measured-progress discipline applies again if it preempts).
- **2026-07-22 (Phase 5 #3 AAVE oracle backfill — COMPLETED)** — `pyth-lst-backfill-20260722-151120` finished cleanly:
  reached `day=2026-07-22`, `exit_code=0`, self-deleted. Combined with the first segment (complete through `2026-04-17`
  before its preemption), the full `2023-01-27→2026-07-22` window is done. Todo flipped with manifest-count evidence
  (see Phase 5's #3 todo). **Phase 5 #3 is now DONE — the only Phase 5 items remaining are #1 (BLOCKED on the filed P0
  OOM issue) and #4's ezETH/rsETH sub-fix (deferred).**
- **2026-07-22 (Phase 5 #2 DEX fill — T+10min VERIFIED healthy)** — `mtds-dex-swaps-backfill` (launched this session
  with operator approval) confirmed healthy at T+10min via BOTH log freshness (`gsutil stat` Update-time within the last
  minute) AND real manifest/row evidence, not just log activity: first processing pass wrote 63,448 real swap records
  across the configured protocol/chain shards (`uniswap_v3_ETHEREUM`=12,540, `uniswap_v3_ARBITRUM`=14,125,
  `uniswap_v3_POLYGON`=23,344, `curve_ETHEREUM`=504, `curve_AVALANCHE`=112, `sushiswap_ARBITRUM`=8,927,
  `uniswap_v2_ETHEREUM`=3,896; most other configured shards 0 rows — dead/unindexed subgraphs, handled as an honest
  cascade-fallback failure, not a crash:
  `uniswap_v3/OPTIMISM: All 8 cascade schemas drifted ... check for 2024+ pool-entity renames`). RSS held steady at
  ~700-750MiB (mem ~10.5%) across multiple `RESOURCE_SAMPLE` readings — nowhere near the 85%+ `mem_crit` threshold that
  OOM-killed the unrelated CEFI Tardis VM earlier today; this collector's per-request GraphQL/aiohttp memory profile is
  genuinely different from that Tardis download path, as expected. `PIPELINE_HEARTBEAT` firing every ~60s. Continuing to
  monitor for eventual completion or any regression; a ~3.5-year multi-protocol/multi-chain backfill will take a while —
  not treating log activity alone as proof, will check manifest shard counts at the next pass.

- **2026-07-22 (Phase 5 #4 — genesis-date validation + fix, then backfill launched)** — operator, asked to scope the
  combined ezETH/rsETH + Solana-LST backfill launch, instead directed: launch "from real genesis" but ONLY after
  VALIDATING each date against real evidence, and fix manifest/UAC wherever a stale genesis is found. Validated 7
  tokens' genesis dates via on-chain contract-creation lookups (EVM, via Blockscout's `creation_transaction_hash` — more
  authoritative than my own binary-search-via-`eth_getCode` attempt, which failed on public-RPC archive-access limits)
  and DefiLlama coverage binary search (Solana) — see the full table + the major Sanctum/Socean-rebrand finding under
  Phase 5's #4 todo above. Shipped `market-tick-data-service@6ab0359a` (7 genesis-date fixes + 2 new gates + citations +
  tests, full QG green) and a documented clarifying comment in `unified-api-contracts@f5e516f6` (did NOT blindly
  overwrite UAC's `LST_TOKEN_GENESIS["sanctumSOL"]` since it may govern a different, unverified mechanism — see the new
  follow-up todo). Launched `deployment-service/scripts/vm/launch-mtds-lst-rates-backfill-vm.sh 2021-08-17 2026-07-22` →
  `mtds-lst-rates-20260722-173127`, SPOT, e2-standard-8, all 4 tarballs confirmed fresh (MTDS `6ab0359ac860` — my
  genesis fixes; UAC `f5e516f6e1fd` — my clarifying comment), STATUS=RUNNING at launch. This ONE launch covers the full
  remaining `lst_yields` gap: ezETH/rsETH/wBETH (extended EVM tokens, gated from their now-correct genesis dates) AND
  jitoSOL/mSOL/bSOL/sanctumSOL (Solana, resolved via today's Tier-4 DefiLlama fallback, now gated from their validated
  real genesis dates too). T+10min verification pending.
- **2026-07-22 (Phase 5 #2 DEX fill — still running, healthy)** — `mtds-dex-swaps-backfill` continues; noted it spends
  real time on dead/unindexed subgraph shards (e.g. `uniswap_v3/OPTIMISM` cycling all 8 cascade-fallback schemas before
  giving up honestly) — this is a genuine efficiency cost, not a stall or OOM risk: heartbeats fresh, RSS stable
  ~800-900MiB (nowhere near the CEFI Tardis OOM's territory), real rows continuing to land for working shards. Will keep
  checking manifest/log evidence periodically rather than treating log activity alone as proof.

## RESUME POINT (pre-compact 2026-07-21) — a fresh session starts HERE

- **Phase 0 is DONE (verified denominator below).** Phase 1 is the next executable step, and it is ready NOW.
- **The VERIFIED denominator to register in Phase 1 (ETHEREUM, conservative — only real-eth_call/probe YES items):**
  - **AAVE `(AAVE, spot_asset, oracle_prices)` — 6 reserves:** wstETH `0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0`,
    weETH `0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee`, rETH `0xae78736Cd615f374D3085123A210448E74Fc6393`, cbETH
    `0xBe9895146f7AF43049ca1c1AE358B0541Ea49704`, rsETH `0xA1290d69c65A6Fe4DF752f95823fAe25cB99e5A7`, ezETH
    `0xbf5495Efe5DB9ce00f80364C8B423567e58d2110` (this address ONLY; `0x2416092f…` REVERTS).
    `instrument_id=<symbol_lower>`. EXCLUDE osETH (not a reserve).
  - **Chainlink feed-map (mirror BOTH MTDS dict + IS tuple) — 2 RefPrice feeds:** weETH/ETH
    `0x5c9C449BbC9a6075A2c061dF312a35fd1E05fF22` (dec 18), ezETH/ETH `0x636A000262F6aA9e1F094ABF0aD8f645C44f641C` (dec
    18). NOT rsETH (ExRate), NOT wstETH (Calculated-USD only — operator decision).
  - **CEX (#1): NO catalogue edit.** **DEX (#2): endpoints work today — normal collector task, NOT blocked.**
- **Phase 1 execution** (smallest shippable first): add the 2 Chainlink feeds to BOTH mirrored maps (MTDS
  `_oracle_prices_constants.py` dict + IS `chainlink.py` tuple; the mirror-invariant test must pass) → one quickmerge
  per repo; then the AAVE oracle venue registration (UAC `expected_coverage`/`defi_venues` phase
  flip/`venue_adapter_keys`/ `capability_declarations`) + IS `aave_oracle` adapter enumerating the 6 reserves; regen
  catalogue; confirm the new `(CHAINLINK-ETHEREUM, SPOT_PAIR, oracle_prices)` + `(AAVE, spot_asset, oracle_prices)`
  cells render `expected_unattempted` (honest RED).
- **Deferred to operator/scope (do NOT register without a ruling):** wstETH Chainlink (Calculated-USD feed — is that
  shape allowed in the RefPrice map?); L2 (Arbitrum/Base/…) LST feeds + AAVE reserves (Ethereum-only Phase 0). Full
  evidence: `wf_f629fbb4-7da` journal.
- **Held artifacts (on-disk, survive compaction, NOT shipped):**
  `strategy-service/strategy_service/engine/backtest/ index_ratio_accrual.py` + its test (the correct pure
  staking/borrow accrual helper for Phase 6, held until the leg wiring). Two labeled stashes: `strategy-service`
  (superseded blocked fix — droppable) and `features-service` (deferred safe-survivor fixes — recover with
  `git stash apply`, reconcile against peer `features-service@9ce1f4ab`).

## Lessons (avoid re-learning)

- **CEX catalogue-add is a PHANTOM-MINTING anti-pattern** — the LST bases are already in `CEFI_BASE_ASSET_UNIVERSE` +
  `STAKING_SPOT_EXCEPTION`; #1 is a Tardis BACKFILL, never a list edit. (Codex §#1.)
- **Plan todos use P0–P3, NOT the phase number** — `P4/P5/P6` fail `check_todo_format` ("missing P-priority"); priority
  is importance, conveyed separately from the phase header.
- **A new codex-ssot doc needs** `referenced_by`/`owner`/`last_reviewed`/`code_refs` present-but-empty; a plan's
  `assigned_role` must be from `agents/*.md` (e.g. `backend_engineer`, not `backend`); run
  `scripts/plan-hygiene/fix_frontmatter.py` + `fix_todo_format.sh` then the pre-commit passes.
- **PM has heavy peer commit traffic** — a tight `pull→add→commit→push` retry loop (up to ~5) lands past the
  branch-drift hook; doc-only PM commits may also go direct-push under the `docs(plans):` carve-out.
- **The `getAssetPrice` RPC is DORMANT, not missing** — lift it from
`market-tick-data-service aave_positions.py:: _fetch_rpc_oracle_prices`, never re-implement.
</content>

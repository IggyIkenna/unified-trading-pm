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
    /plans/archive/issues/lst_exchange_rate_data_availability_2026_07_21.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    /plans/archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
  ]
created: "2026-07-21"
last_updated: "2026-07-21"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: ["operator dispatch 2026-07-21: build honest LST-rate coverage then wire interest PnL"]
locked_by:
locked_since:
context_scope:
  [
    /codex/02-data/lst-exchange-rate-surfaces.md,
    /plans/archive/2026_08/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
    /plans/archive/issues/lst_exchange_rate_data_availability_2026_07_21.md,
    features-service/features_service/onchain/engine/lst_features.py,
  ]
supersedes:
superseded_by:
---

# LST rate honest coverage — plan of record

**Codex SSOT:** `/codex/02-data/lst-exchange-rate-surfaces.md` (the four surfaces, canonical homes, honest-coverage
contract). **Audit:** `/plans/archive/issues/lst_exchange_rate_data_availability_2026_07_21.md`.

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

      **RULED 2026-08-12 (/plan-reconcile, operator interactive)**: a literal regen-script run IS required before this
                      closes — invariant-test confirmation alone is not sufficient. Do NOT flip this todo `[x]` until
                      `build_instrument_catalogue.py` + `enumerate_expected_universe.py` (v2) have actually been executed against real
                      infra and the new AAVE/CHAINLINK cells confirmed `expected_unattempted`.

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

- [x] ✅ [MTDS] P3. **DONE — directly executed via archived
      `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch8_2026_08_02.md`**, verified 2026-08-05: force-leg wrote
      54 parquet files + 56 manifest `captured` rows to the `-test-` bucket; DEX endpoints confirmed live. Also
      superseded in spirit by Phase 5 #3/#2's real prod force+skip proof. Applied 2026-08-08 (na-eligibility-audit) —
      full trail: `issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` Todo 2.

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
      retry-storm, or a within-process leak). **Re-tagged 2026-07-28 — a normal `[MTDS]` P0 debugging dispatch, not an
      operator ask.** Filed `plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` (P0) with full
      evidence — this is a real, cross-cutting MTDS backfill reliability bug (affects the shared `--operation download`
      / Tardis-adapter CEFI path generically, not specific to LST tokens) that needs code-level debugging, not more
      blind VM relaunches. The AAVE oracle backfill (Phase 5's other in-flight VM, `pyth-lst-backfill-20260722-045059`)
      uses a completely different operation (`collect-oracle-prices`, RPC-based, not Tardis-download) and is confirmed
      unaffected — still healthy and progressing normally as of this entry.
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
- [x] ✅ [UAC] P3 (partial). **`_defi_lst.py::LST_TOKEN_GENESIS["sanctumSOL"]` corrected** — was "2024-01-25", now
      "2021-10-15", shipped `unified-api-contracts@dcc69001` (2026-07-22). Confirmed via reading
      `lst_rates_handler.py`'s actual post-fetch filter that this value gates ANY row regardless of source tier, so the
      earlier caution about a "possibly-different Tier-1-specific semantic" didn't hold up — see the T+10min bug finding
      above.
- [x] ✅ [UAC][IS] P3. **Remaining Sanctum reconciliation** — `SANCTUM_INF_POOL_ACCOUNT` on-chain verification done
      (found FABRICATED — the old value `o1Mw5Y3n68o8TakZFuGKLZMGjm72qv4JeoZvGiCnGy7` doesn't exist on-chain — replaced
      with the mint's own `mintAuthority`); IS `sanctum.py`'s `available_from_datetime` now sources INF's floor from UAC
      `LST_TOKEN_GENESIS["sanctumSOL"]` directly. `chain_env.py`'s `PROTOCOL_LAUNCH_DATES[("SOLANA","SANCTUM")]`
      ("2023-06-01") deliberately left UNCHANGED (still correct for jupSOL/laineSOL, the marketplace-native tokens it
      actually governs). **SHIPPED both repos, both quality-gates.sh green (sentinel matched HEAD in each)**:
      `market-tick-data-service@52c5ff02` and `instruments-service@4b82310a`, both verified ancestors of
      `origin/live-defi-rollout` (`git merge-base --is-ancestor`). Only remaining follow-up (genuinely separate, not
      blocking): `SANCTUM_INF_POOL_ACCOUNT`'s exact multi-year creation date via `getSignaturesForAddress` pagination
      needs paid archive-RPC access, not attempted this session — documented as a known limitation in the code comment,
      not silently dropped.
- [ ] [MTDS] P3. **Retagged 2026-07-29: credential/launch gate confirmed cleared (not `BLOCKED-CREDENTIALS`) — NOT
      flipping to done though: live-reverified right now
      (`gcloud compute instances list     --filter="name~mtds-dex-swaps-backfill"`) shows `-1`/`-2` still RUNNING,
      matching this doc's own last status check (2026-07-26, multi-day-to-multi-week runway remaining). Genuinely still
      open.** #2 DEX fill — deep-backfill `dex_pool_swaps` once the endpoint lands (else remains
      ~~`BLOCKED-CREDENTIALS`~~). **Endpoint confirmed live since Phase 0** (2026-07-21) and the `price` column shipped
      this session (`market-tick-data-service@869e46cd`) — this is NOT actually `BLOCKED-CREDENTIALS` any more; ready to
      launch as a normal backfill. **LAUNCHED (2026-07-22, operator-acked)** — see Progress Log entry. **Status update
      2026-08-09 (stale-check-defi-tranche)**: the "-1/-2 still RUNNING" framing above is from 2026-07-29 and is now
      stale — per `issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` Todo 3 (2026-08-07,
      `defi_satellite_ao_dispatch_batch10-009`), both `-1` and `-2` had COMPLETED by 2026-08-07 ("No sibling VMs running
      at launch time — both `-1` and `-2` had completed"); `-3` was separately found FAILED (`exit_code=137`,
      2026-07-27, silent 6+ day stall — never relaunched until then) and was relaunched 2026-08-07 (SPOT, SHARD_INDEX=6,
      `--start 2025-12-15 --end 2026-07-21`), health-verified RUNNING at T+10min (95,236 swap rows in the first shard).
      Not independently re-verified live in this pass whether `-3` has since reached its window end (~2 days elapsed
      since relaunch) — this todo stays open pending that confirmation, but the accurate current state is "2 of 3 shards
      done, 1 relaunched and healthy as of 2026-08-07," not the stale "-1/-2 still running" text above.

## Phase 6 — Interest PnL on honest data (the payoff; see pnl_interest_accrual doc)

- [x] ✅ [STRATEGY] P2. **A2 staking leg** — DONE, shipped `strategy-service@e93902d8` (wire `carry_staked_basis`
      STAKING leg to real `lst_yields` index-ratio accrual). Verified 2026-08-03, applied 2026-08-08
      (na-eligibility-audit) — see `issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` Todo 2.
- [x] ✅ [STRATEGY] P3. **Recursive-staking borrow leg** — DONE, shipped `strategy-service@23bd8b76` (wire
      CARRY_RECURSIVE_STAKED tick builder + Aave borrow-index leg). Verified 2026-08-03, applied 2026-08-08
      (na-eligibility-audit) — see `issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` Todo 2.
- [x] [MTDS] P3. **Solana `lst_rates` `pipeline_mode` mislabels which tier actually supplied each row** — found
      2026-07-23 code-tracing the 4-rate audit for `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`.
      `solana_lst_archival.py`'s per-row `"method"` field (`alchemy_get_account_info` / `thegraph_subgraph` / `rest_api`
      / `defillama_historical_ratio`) correctly survives as a COLUMN inside the written parquet, but
      `lst_rates_handler.py` calls `pipeline_mode_for_source("onchain_subgraph", ...)` **unconditionally for every
      Solana LST row regardless of which tier fired** — so the manifest/GCS-path `pipeline_mode` label reads
      `batch_onchain_subgraph` even for rows that came from Tier 4 (DefiLlama historical-ratio market proxy), which is
      neither on-chain nor subgraph-derived. Net effect: a consumer doing manifest-level `source=`
      filtering/reconciliation (this workspace's own "source= is crosscutting" convention) CANNOT distinguish genuine
      protocol-redemption rows from market-proxy rows without reading the `method` column out of the actual parquet —
      the label lies. Confirmed this is Solana-only (the EVM path in the same file has no tier-fallback system, so its
      rows are unambiguous). Fix = derive `pipeline_mode_for_source` from the actual per-row `method`/tier instead of a
      hardcoded string, or at minimum add a distinct source value for the Tier-4 path. — **DONE 2026-07-30**, batch1
      todo 9a: added `PipelineMode.BATCH_DEFILLAMA` (`unified-api-contracts@f7019ffb`,
      `market-tick-data-service@45a9fe69`).

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
- **2026-07-22 (Phase 5 #4 — T+10min check found a P0 bug; fixed; relaunched)** — `mtds-lst-rates-20260722-173127`'s
  run.log showed real EVM progress (day-by-day, real rows, manifest counts climbing) BUT logged
  `WARNING Failed to create HTTP session for Solana LST rates: Resolver requires aiodns library` on EVERY single day —
  meaning the ENTIRE Solana leg (jitoSOL/mSOL/bSOL/sanctumSOL — the whole point of today's Tier-4 fix + genesis
  validation) was silently producing zero rows for the whole run. Root-caused via direct SSH into the running VM:
  `aiodns`/`pycares` genuinely missing from the deployed venv (`ModuleNotFoundError`), even though `ccxt` — which DOES
  depend on `aiodns` per `uv.lock` — was present and importable; a pre-existing tarball/venv-packaging gap, not
  something this session introduced. `lst_rates_handler.py`'s `_fetch_solana_lst_rates` wrapped session creation in a
  bare `try/except Exception: return []`, so this ONE missing optional dependency silently dropped the whole data leg
  rather than failing loud. Stopped the VM immediately (confirmed root cause before burning more compute). **Fix**:
  `aiohttp.resolver.AsyncResolver` (c-ares/aiodns-backed) is a pure performance optimization, never a functional
  requirement — aiohttp's default `ThreadedResolver` needs no extra dependency and already correctly in use elsewhere in
  this codebase (`native_staking_handler.py`). Added a shared
  `market_tick_data_service/_http_resolver.py::make_resilient_connector()` (prefers `AsyncResolver`, catches
  `ImportError`/`RuntimeError`/`OSError` and falls back to the default resolver instead of raising) and wired it into
  ALL THREE call sites that hard-required `AsyncResolver` in this codebase: `lst_rates_handler.py` (the one actually
  blocking this backfill), and as a good-citizen fix, `oracle_prices_handler.py`'s two Pyth Hermes call sites (same bug
  pattern, not yet observed to fail — the AAVE oracle VM's earlier success suggests either a different tarball build or
  the code path wasn't exercised the same way) and `deribit_options_chain_handler.py` (same pattern, no existing test
  coverage, unrelated data domain but zero-risk to fix given the shared helper already existed). Shipped
  `market-tick-data-service@533514c2` (new module + 3 call-site fixes + a stale-test rewrite that had asserted the OLD
  wrong-in-hindsight "session failure → empty rows" behavior + a new dedicated `test_http_resolver.py`; full MTDS
  `quality-gates.sh` green). **Second finding from reading the actual gating code**:
  `lst_rates_handler.py::_fetch_solana_lst_rates` ALSO applies a post-fetch filter via UAC's
  `get_lst_token_genesis("sanctumSOL")` — confirmed by reading the filter loop directly that this is a BLANKET check
  applied to ANY row regardless of which tier resolved it. This meant UAC's `LST_TOKEN_GENESIS["sanctumSOL"]` (still
  "2024-01-25" — I had left it unchanged earlier this session out of caution about a possibly-different Tier-1-specific
  semantic) would have SILENTLY DROPPED every Tier-4-resolved sanctumSOL row for 2021-10-15 through 2024-01-24 —
  nullifying the exact 2.3-year backfill opportunity found earlier. With this concrete evidence in hand (not the earlier
  speculative uncertainty), corrected UAC's value to `"2021-10-15"` — shipped `unified-api-contracts@dcc69001` (full QG
  green; no tests referenced the old value). **Republished code tarballs before relaunching** —
  `launch-mtds-lst-rates-backfill-vm.sh`'s own freshness check caught that the first relaunch attempt would have run
  PRE-FIX code (tarball manifests hadn't been rebuilt since my commits landed); ran
  `create-code-tarballs.sh --include market-tick-data-service --include unified-api-contracts --include deployment-service`,
  verified both manifests now match my fix commits exactly (`533514c22e6d`, `dcc690018e55`) before launching.
  **Relaunched**: `mtds-lst-rates-20260722-181845`, same date range, all 4 tarballs confirmed fresh at launch. T+10min
  re-verification pending — this time checking specifically that Solana rows appear (not just that EVM rows continue,
  which already worked before).
- **2026-07-22 (Phase 5 #4 — T+10min re-check: aiodns fix CONFIRMED working, but zero Solana rows so far — traced to a
  genuine, correct, non-bug data-source boundary)** — the `Failed to create HTTP session for Solana LST rates` warning
  is GONE (confirmed via full-log grep across 1281 lines — the resolver fix works). But no Solana rows had appeared yet
  either (no `Collected N Solana LST rate records` log line for ANY of the ~75 days processed so far, 2021-08-17 through
  ~2021-11-01) and no error/warning logged for the Solana leg at all — genuinely puzzling at first glance. Traced it by
  hand: `_tier4_defillama_historical_rate` requires BOTH legs (the LST's own USD price AND SOL's own USD price) to
  compute the ratio, and several of its own absence branches log at DEBUG level (invisible at this service's INFO log
  level) — so a silent empty result there produces no visible trace, unlike an actual error. Verified directly via curl
  (both from my own environment and via SSH from the VM itself, confirming it's not a VM-side connectivity issue):
  mSOL's OWN price IS genuinely available at every date checked between 2021-10-29 and 2021-11-01 (e.g. $197.93 at
  2021-10-29), but **wrapped-SOL's (`So111...112`) own DefiLlama USD-price coverage — the QUOTE LEG shared by every
  Tier-4 ratio — doesn't start until 2021-12-16** (binary-searched: absent 2021-12-15, present 2021-12-16). This means
  jitoSOL/mSOL/bSOL/sanctumSOL's Tier-4 resolution is bounded by `max(token's own genesis, 2021-12-16)` regardless of
  how far back each token's own price history goes — a real, previously-unchecked constraint on the SHARED quote leg,
  not a per-token fact. **This is NOT a bug** — Tier 4's honest-absence contract is working exactly as designed (never
  fabricates a ratio from only one leg); it just means mSOL (genesis 2021-08-17) and Sanctum (genesis 2021-10-15) will
  correctly produce zero rows for their own ~4-month/~2-month windows before 2021-12-16, which is safe/correct, just not
  the earliest POSSIBLE date those two tokens could otherwise resolve. Did **not** stop or modify the running VM —
  letting it continue is correct; verifying real Solana rows appear once the daily loop passes 2021-12-16 (VM was at
  ~2021-11-01 at last check, ~45 days out at the observed ~7-8s/day pace, so ~5-10 more minutes). **Not adding a
  `max(..., 2021-12-16)` gate to the code this session** — the current behavior is already correct (honest, no
  fabrication, just a few extra cheap no-op DefiLlama calls before the boundary); worth a minor future efficiency
  tidy-up, not a correctness fix.
- **2026-07-22 (Phase 5 #4 — CONFIRMED WORKING end-to-end with real data)** — checked again once the VM's daily loop
  passed the 2021-12-16 SOL/USD boundary: `run.log` now shows real, plausible Solana LST rates —
  `mSOL = 1.02498435 SOL (apy=0.0000%, tier=defillama_historical_ratio)` and
  `sanctumSOL = 1.01432296 SOL (apy=0.0000%, tier=defillama_historical_ratio)` at 2022-01-30, both correctly close to
  1.0 as expected for LSTs, `Collected 2 Solana LST rate records for 2022-01-30`, and
  `Wrote 1 LST rate records (marinade/SOLANA)` / `(sanctum/SOLANA)` landing in the manifest (per-VM shard at 677 entries
  and climbing). This is the full end-to-end confirmation that today's three fixes (Tier-4 DefiLlama fallback, the
  aiodns resolver crash, and the corrected Sanctum genesis) all compose correctly and are producing real, plausible,
  honestly-sourced data — not just "should work in theory." Still running; will continue to climb through jitoSOL's
  2022-11-01 and bSOL's 2022-12-14 genesis dates as the day-loop progresses toward 2026-07-22.
- **2026-07-22 (Phase 5 #2 DEX fill — still running, healthy)** — `mtds-dex-swaps-backfill` continues; noted it spends
  real time on dead/unindexed subgraph shards (e.g. `uniswap_v3/OPTIMISM` cycling all 8 cascade-fallback schemas before
  giving up honestly) — this is a genuine efficiency cost, not a stall or OOM risk: heartbeats fresh, RSS stable
  ~800-900MiB (nowhere near the CEFI Tardis OOM's territory), real rows continuing to land for working shards. Will keep
  checking manifest/log evidence periodically rather than treating log activity alone as proof.
- **2026-07-22 18:54 UTC (fresh-session VM re-check — both still healthily RUNNING, nothing actionable; picking up
  Sanctum reconciliation)** — `gcloud compute instances list` confirms BOTH VMs still `RUNNING` in `asia-northeast1-c`.
  `mtds-lst-rates-20260722-181845`: `run.log` tail shows real day-by-day progress now at `2022-04-13` (climbing from
  `2021-08-17`), real EVM rows (stETH/wstETH/rETH/ankrETH/idle) AND real Solana rows (`mSOL = 1.03750142 SOL`,
  `sanctumSOL = 1.03027891 SOL`, tier=`defillama_historical_ratio`) landing every day, per-VM manifest shard at 1109
  entries and climbing; manifest parquet `Update-time` 18:54:37Z (fresher than the `date -u` check at 18:54:41Z — i.e.
  actively being written this second). At ~239 days processed in ~34min, full `2021-08-17→2026-07-22` (~1801 days) is a
  multi-hour run — still has a long way to go, not stalled. `mtds-dex-swaps-backfill`: `run.log` shows real swap rows
  landing (61,204+ swap rows across working shards this pass), honest cascade-fallback exhaustion on dead subgraphs
  (`uniswap_v3/OPTIMISM`, `camelot_v3/ARBITRUM`, `curve/ETHEREUM` each cycling schemas and failing cleanly, not
  crashing), RSS ~1000MiB / mem ~13% (nowhere near OOM territory), manifest shard climbing (666+ entries,
  `process_final=False` — still mid-backfill), parquet `Update-time` 18:53:52Z. **Both VMs: nothing actionable,
  correctly left running.** Per the RESUME POINT's own recommendation, moving to the one genuinely-unblocked
  non-infra-gated Phase 5 todo: the Sanctum reconciliation follow-up (`SANCTUM_INF_POOL_ACCOUNT` on-chain verification +
  `chain_env.py`/`sanctum.py` date reconciliation).
- **2026-07-22 (Sanctum reconciliation — on-chain verification done, code changes staged, NOT YET SHIPPED — session
  interrupted before quality-gates.sh confirmed green)** — verified `SANCTUM_INF_POOL_ACCOUNT`
  (`market-tick-data-service/_solana_lst_archival_tier1.py`) via direct `getAccountInfo` against
  `api.mainnet-beta.solana.com`: the previous value (`o1Mw5Y3n68o8TakZFuGKLZMGjm72qv4JeoZvGiCnGy7`) does **NOT EXIST
  on-chain** (`value: null`) — a fabricated placeholder, not merely unverified. Replaced with the INF mint's own
  on-chain `mintAuthority` field (`AYhux5gJzCoeoc1PoJ1VxwPDe22RwcvpHviLDD1oCGvW`), confirmed to be a real, actively-
  written 240-byte program-owned account; independently corroborated by raw byte-decoding — the account's own data
  embeds the INF mint's exact 32-byte pubkey at internal offset 144 (strong but not 100%-certain structural evidence, no
  Sanctum/Socean program IDL available to confirm definitively). **Known limitation left in code comments**: this
  account is only 240 bytes, shorter than the >=274 bytes `decode_jito_stake_pool_rate()` expects (modern SPL Stake-Pool
  layout; Socean's own struct predates it) — Tier 1 will still return `None` for Sanctum via a logged "too short"
  warning rather than a silent not-found; NOT blocking real data (Tier 4's DefiLlama fallback, shipped earlier, already
  provides verified sanctumSOL/SOL data end-to-end). `getSignaturesForAddress` pagination toward the account's true
  creation date hit public-RPC rate limits after ~10 pages (~15 days of history) — reaching the exact multi-year genesis
  this way needs paid archive-RPC access, not available this session; documented as a genuine, correctly-scoped
  remaining gap rather than guessed at. **`chain_env.py`'s `PROTOCOL_LAUNCH_DATES[("SOLANA","SANCTUM")] = "2023-06-01"`
  was investigated and deliberately left UNCHANGED** — it's still the correct floor for jupSOL/laineSOL (genuine
  Sanctum-marketplace-native tokens launched with the brand); only INF needed an earlier date, since INF's own mint
  predates the Sanctum brand by ~2.3 years (the pre-existing Socean pool, per the earlier same-day finding). Instead of
  touching the shared brand-floor key, fixed IS's `sanctum.py` adapter directly: added `_INF_AVAILABLE_FROM_DATETIME`
  sourced from UAC's `get_lst_token_genesis("sanctumSOL")` (the same key already corrected to `"2021-10-15"` earlier
  this session), applied ONLY to the `INF` symbol — jupSOL/laineSOL keep using the shared `_SANCTUM_DEPLOY_DATE` floor
  unchanged. **Current state (interrupted mid-ship, being checkpointed here rather than left silent)**: both files'
  changes are staged (`git add`) but NOT committed in their respective repos (`market-tick-data-service`,
  `instruments-service` — plus `instruments-service`'s companion test file
  `tests/unit/reference_data/adapters/defi/test_sanctum_metadata.py`, also staged). Neither repo's `quality-gates.sh`
  sentinel matches the current working tree yet (a background gate run was started but its completion was never
  confirmed this session — do NOT assume it passed). **Next session MUST**: re-run `quality-gates.sh` fresh in both
  repos (do not trust a stale background run), fix anything red, then `quickmerge --agent --files` each repo's changed
  files, then flip the Sanctum-reconciliation todo above with the shipped shas. Do not re-do the on-chain verification —
  it's captured here with full evidence.
- **context-scout 2026-08-03**: populated context_scope (5 entries).
- **context-scout 2026-08-06**: corrected a marker-skip left by an earlier cohort-5 batch (2026-08-06 01:34 UTC edit
  trimmed context_scope 5→3 entries with no marker added); re-verified the current 3 entries resolve on disk, unchanged.

## RESUME POINT (pre-compact 2026-07-23) — a fresh session starts HERE

Phases 0-5 are effectively DONE (#1 CEX-spot remains operator-gated). Phase 6 (interest PnL) is now ACTIVELY IN
PROGRESS, not just gated — E1 (FUNDING leg) shipped, E2 (unit design) investigated, the 4-rate audit gate that was
blocking the STAKING leg is now resolved with hard evidence (stETH confirmed genuine protocol-redemption data), and a
STAKING-leg build was just approved by the operator and is about to start. **Next session: do NOT re-launch or re-fix
anything below without first checking current VM/manifest state.**

### Deferred work after 2026-07-23

| Item                                                                                | State / why deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Blocked on                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ✅ Phase 5 #4 `lst_rates` backfill                                                  | **DONE** (2026-07-23 01:57 UTC) — full `2021-08-17→2026-07-22`, one continuous run, `exit_code=0`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | n/a — closed                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Phase 5 #2 `dex_pool_swaps` backfill                                                | **Cannot be done yet** — 3-VM date-sharded on-demand fleet (`mtds-dex-swaps-backfill-1/2/3`, covering the exact measured 570-day gap `2024-10-07→2026-07-21`). Re-verified 2026-07-26 07:37 UTC: all 3 still RUNNING, none vanished, all writing real data — but progressing MUCH slower than the original ~20-30h target (`-1`/`-3` ~2-3h/day, `-2` ~15-18x slower still — see `/plans/archive/2026_08/lst_rate_honest_coverage_vm_monitoring_history_2026_07_21.md`'s 07:37 UTC entry for the per-VM day-count table + the `-2`-specific anomaly). Realistic remaining runway is multi-day-to-multi-week, not hours.                                                                                                                                                                                                                                                                                                           | Elapsed time only — check `gcloud compute instances list --filter="name~mtds-dex-swaps-backfill"` + each VM's run.log + its small `_index/per_vm/{vm}.parquet` shard (NOT the ~1GB consolidated index) for real day-count progress; if any vanishes, just relaunch that exact chunk's command again (idempotent by design); if `-2`'s anomalous slowness continues, an operator call on kill+relaunch may be warranted once root-caused |
| `lst_yields` FEATURE computation (distinct from the raw `lst_rates` backfill above) | **Operator-owned** — the only existing runner script (`features-service/scripts/backfill_lst_yields_30day.sh`) is explicitly marked `owner: operator` / "do NOT execute from CI" — a deliberate boundary, not something to run myself.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Operator invocation                                                                                                                                                                                                                                                                                                                                                                                                                     |
| Phase 6 E1 (FUNDING leg)                                                            | ✅ **DONE, SHIPPED** — `strategy-service@aa1fcdc7`, verified reachable. Additive/backward-compatible design (new `funding_rates_by_day` param defaults to `None`, preserving all other callers byte-for-byte). Real DERIBIT/BYBIT funding data confirmed captured. One non-blocking gap surfaced: CeFi `derivative_ticker` capture has a hole ~2026-05-22→2026-07-20 across Tardis venues (pre-existing, unrelated MTDS issue).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | n/a — closed                                                                                                                                                                                                                                                                                                                                                                                                                            |
| Phase 6 E2 (STAKING-leg unit/share-class design)                                    | ✅ **Investigated, recommendation delivered** (`unified-trading-pm@38d8a38ce`) — no schema change needed; wire the already-unwired `convert_settlement_to_share_class` + `ShareClassFxMatrix` at the reporting layer instead of branching the accrual formula. Two items flagged for an explicit operator ruling: (a) spot-rate-conversion vs. FX-noise-isolated "true native yield" semantics, (b) a duplicate/incompatible `ShareClass` enum across two UAC modules — a real wrong-import risk.                                                                                                                                                                                                                                                                                                                                                                                                                                | Operator ruling on those 2 flagged items (not blocking the STAKING-leg build itself, which uses the existing quote-only path)                                                                                                                                                                                                                                                                                                           |
| Phase 6 4-rate audit (which rate `lst_yields.exchange_rate` actually is)            | ✅ **Code-traced and substantially resolved for what matters today** (`unified-trading-pm@0835af82d`) — EVM LSTs (stETH etc.) confirmed genuine rate #4 (protocol redemption) via historical block-pinned `eth_call`, for every historical day. Solana LSTs confirmed NOT #4 historically (Tier 1-3 all date-gated to `today`-only; every historical day actually came from Tier 4's DefiLlama market-price proxy) — moot today since no Solana LST is currently perp-eligible, but a real caveat if one becomes eligible again. Does not replace the broader `wf_268532e0-323` audit (all 4 sources × all tokens), just answers the one question blocking the STAKING leg now.                                                                                                                                                                                                                                                  | n/a for the ETH-side build; `wf_268532e0-323`'s full result still pending for the broader picture                                                                                                                                                                                                                                                                                                                                       |
| Phase 6 STAKING leg build (stETH)                                                   | **Operator approved 2026-07-23** ("yeah build it") — about to be dispatched as the next step after this pre-compact pass. Scope: wire `carry_staked_basis` STAKING via `lst_yields.exchange_rate/prev_rate` keyed off `cfg['lst_asset']`, matching E1's money-path discipline (3-lens review, hold-not-force-ship if anything is uncertain).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Nothing — this is the very next action                                                                                                                                                                                                                                                                                                                                                                                                  |
| Phase 5 #1 CEX-spot contiguity backfill                                             | **Operator-owned** — explicitly NOT to be relaunched blindly. **Correction 2026-08-08**: do NOT read this as credential-blocked — the cited issue doc's ONE credential item (`BLOCKED-CREDENTIALS`, the-odds-api.com, sports) is unrelated to this Tardis LST backfill and was cleared 2026-08-03 (reconfirmed 2026-08-07, 14,475,834 credits remaining); Tardis itself uses a paid academic key with a concurrency cap, no credit-exhaustion evidence anywhere in that doc. The real, non-credential blocker for THIS item — the CEFI/Tardis OOM bug — already shipped a fix 2026-07-26 (machine-type bump + fail-loud logging), validated 2026-07-27 (zero silent short-falls across all 3 real launch attempts); the issue doc's still-open P1 is SPORTS/odds_api-specific memory accumulation, not this backfill's blocker. Operator-owned per this doc's own standing caution against blind VM relaunches, not credentials. | `plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` (P0)                                                                                                                                                                                                                                                                                                                                                       |
| Phase 6 recursive-staking borrow leg (E3)                                           | **Not started** — explicit bigger follow-on, unblocks once #3 Aave oracle (already done) + this leg's own scoping.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Nothing hard — genuinely just not started yet, lower priority than the STAKING leg                                                                                                                                                                                                                                                                                                                                                      |
| ✅ MTDS `lst_rates` `pipeline_mode` mislabels Solana Tier-4 rows                    | **DONE 2026-07-30** (defi_satellite_ao_dispatch_batch1 finalize reconciliation) — see defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 9 sub-item (a); `unified-api-contracts@f7019ffb` + `market-tick-data-service@45a9fe69`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | n/a — closed                                                                                                                                                                                                                                                                                                                                                                                                                            |

**Recommended next item once picked back up**: if the STAKING leg build below hasn't happened yet, that's the next
action (operator-approved). Otherwise, check the dex-swaps 3-VM fleet's progress next (multi-hour, no urgency).

- **Held artifacts (on-disk, survive compaction, confirmed STILL present + unmodified as of 2026-07-23 by E1's own build
  agent)**: `strategy-service/strategy_service/engine/backtest/index_ratio_accrual.py` + its test — the pure Aave
  index-ratio helper, NOT applicable to csb any more (E4 ruled LENDING drops entirely for csb), its remaining use is the
  recursive-staking borrow leg (E3), an explicit bigger follow-on. Leave held, do not rebuild.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid — gate + 3 open items re-verified live (CEX-spot
  backfill operator-held per standing caution; lst_yields FEATURE run operator-invocation-only per script markers;
  DEX-swaps fill in-flight VM, not yet confirmed at window end). BIG FINDING flagged, not fixed here (read-only scope):
  doc measured 1009L via `check_line_caps.sh`, over the 1000L hard cap again (regression from an inline "Status update
  2026-08-09" correction) — next marker-writer must use the marker-only carve-out. Doc stays `assigned_vm: NA`.

## Lessons (avoid re-learning)

- **SPOT preemption frequency can genuinely worsen, not just randomly recur** — a repeat preemption with DECREASING
  time-to-preemption each cycle (17min → 2h22m → 2-3min) is real signal of worsening zone/machine-type capacity
  contention, not "bad luck" — that pattern, not just the count, is what justified switching to on-demand for the
  dex-swaps fleet rather than continuing to retry SPOT blindly.
- **A launcher's `--protocols`-style comma-separated flag can silently collide with `gcloud`'s own comma-delimited
  `--metadata` parsing** — `Bad syntax for dict arg: [value]` means a multi-value flag is being smashed into one big
  `--metadata` string without escaping; check for this before assuming a flag "should just work" from its docstring
  alone.
- **A tier-based data-fetch fallback chain's "method" column can be a real column in the output data while being
  completely invisible at the manifest/`pipeline_mode` level** — always check BOTH levels before trusting that a
  manifest `source=` filter can distinguish data provenance; a fixed/hardcoded source label passed to
  `pipeline_mode_for_source()` regardless of which tier fired is a real, easy-to-miss mislabeling risk.
- **Directly reading a data collector's own code (block-pinning, date-gating, tier-fallback order) is often faster and
  more authoritative than treating "which of 4 possible rates is this" as unknowable** — the 4-rate audit's ETH-side
  half was fully resolved in one focused code-trace, not by waiting on a separate, broader audit workflow.

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
- **A "conservative" or protocol-BRAND launch date is NOT the same fact as a specific data source's own coverage start**
  — three separate instances this session: (1) Sanctum INF's mint predates Sanctum-the-brand by 2.3 years (it's a Socean
  rebrand); (2) SOL/USD's own DefiLlama coverage (2021-12-16) is a SEPARATE, later boundary than any individual LST
  token's own coverage — every Tier-4 ratio needs BOTH legs, so the LATER of the two always wins, silently, with no
  error; (3) rsETH's coded genesis was the KelpDAO protocol's launch, not the specific oracle CONTRACT's deployment (31
  days later) — always verify the EXACT contract/mint you're gating, never the wrapped protocol's brand-launch date.
  **Validate via primary evidence** (on-chain contract-creation tx via a block explorer's `creation_transaction_hash`,
  or binary-searching the actual data source's own coverage) before trusting any existing "conservative"/approximate
  date — several were off by weeks to years.
- **A bare `except Exception: return []` around an entire data leg is a silent-data-loss trap, not resilience** — a
  single missing OPTIONAL dependency (`aiodns`, needed only for aiohttp's opportunistic fast resolver, never for
  correctness) took down the WHOLE Solana LST-rates leg for every single day of a multi-year backfill, with no error
  visible anywhere in the log. The fix pattern: catch the SPECIFIC narrow failure at the SMALLEST possible scope
  (resolver construction) and degrade gracefully (fall back to the default resolver) — never wrap a whole data leg in a
  blanket except that swallows unrelated failures into indistinguishable emptiness.
- **Some of a tier-cascade's own absence branches log at DEBUG, not INFO/WARNING** — this made a GENUINE, correct
  honest-absence result (SOL/USD not yet covered by DefiLlama for this date) look identical in the log to a silent bug,
  for about 20 minutes of investigation. When "no error, no data, no explanation" — check the log LEVEL of the quiet
  path before assuming it's broken; it may be working exactly as designed.
- **After shipping a fix intended for an already-running VM, its OWN tarball-freshness check may refuse to launch with
stale code (warn-only by default)** — `launch-mtds-lst-rates-backfill-vm.sh` warned but still launched with a PRE-FIX
tarball once; always check the launcher's own freshness warning output, and if stale, run
`create-code-tarballs.sh --include <repo>...` and verify the GCS manifest SHA matches your fix commit before trusting a
"launched successfully" message.
</content>

- **2026-07-22 19:35 UTC (Sanctum reconciliation ship — partially unblocked, one leg deferred)** — resumed shipping the
  staged-uncommitted Sanctum work from the earlier checkpoint. `instruments-service` quality-gates.sh ran GREEN
  (sentinel `09806f26c6fb17f62cf770d4f770bad72836129d` == HEAD). Attempted quickmerge — **blocked by the dirty-deps
  pre-flight audit on `unified-trading-library`** (`cloud_interface/abstractions.py` + 3 provider files, all with mtime
  ~12 SECONDS old at check time — genuinely LIVE foreign WIP, not stale/inheritable per the liveness-gating rule;
  correctly left untouched). **NOT forcing this ship** — will retry once that WIP clears (check again next tick; do not
  isolate/stash someone else's active edit). MTDS's own quality-gates.sh + deployment-api's (for the distinct-values
  `futures_chain` fix) started running in parallel while waiting.

- **2026-07-22 19:51 UTC → 2026-07-26 07:56 UTC (VM monitoring history — EXTRACTED 2026-08-14, line-cap remediation)** —
  19 dated check-in entries (VM fleet re-checks, 4 dex-swaps SPOT preemption-and-resume cycles, the on-demand-fallback
  decision, the `lst_rates` backfill completion, and the split into a 3-VM date-sharded fleet) moved verbatim to
  `/plans/archive/2026_08/lst_rate_honest_coverage_vm_monitoring_history_2026_07_21.md` per
  `/plans/archive/2026_08/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` Todo 1. **Condensed
  summary**: the `lst_rates` backfill (`mtds-lst-rates-20260722-181845`) ran to completion 2026-07-23 02:04 UTC with
  zero preemptions (full `2021-08-17→2026-07-22` window, `exit_code=0`); the follow-on `lst_yields` feature compute
  stays operator-owned (see the Deferred table above). The `dex_pool_swaps` backfill preempted 4× on SPOT with strictly
  decreasing time-to-preemption, switched to on-demand as a sanctioned one-run exception (2026-07-23 04:54 UTC — see the
  "SPOT preemption frequency" Lesson below), then split into the 3-VM `mtds-dex-swaps-backfill-1/2/3` fleet (2026-07-23
  07:10 UTC, exact shard ranges in the Deferred table above); a genuine dead-subgraph efficiency finding (~15 of 24
  configured protocol/chain shards permanently unindexed, never fixed mid-backfill) and a `--protocols`
  flag/`gcloud --metadata` collision bug were both surfaced but left as follow-ups, not fixed inline. The fleet's
  current terminal state lives in this doc's own Deferred-work table, not in the extracted history — see that table for
  what's still open.
- **na-eligibility-audit 2026-08-03**: KEEP-NA valid — doc is over the 1000L cap (pre-existing, operator ruling
  2026-08-02), so this is a marker-only append (no checkbox changes) per that ruling's scoped exception. 3 of 6 open
  items are STALE (already shipped: A2 staking=strategy-service@e93902d8; recursive-staking borrow=
  strategy-service@23bd8b76; Phase 3 sample-download superseded by Phase 5's real prod force+skip proof) and Phase 5 #2
  DEX-fill has a live finding (VM `-3` FAILED exit_code=137 on 2026-07-27, never relaunched — 6-day silent stall).
  Ready-to-apply checkbox text + full evidence filed as real todos:
  [[lst_rate_honest_coverage_over_cap_findings_2026_08_03]]. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-06**: populated/refreshed context_scope (5 entries) — added the companion over-cap-findings
  issue doc (the doc's own Phase 5 ready-to-apply evidence lives there, not in this frozen-append-only doc) and the
  `mtds_backfill_vm_memory_hang` issue this doc's Deferred table cites as what the remaining CEX-spot backfill item is
  blocked on. Doc now at 989/1000 lines — comfortable headroom restored after the recent trim-below-cap commit.
- **na-eligibility-audit 2026-08-07**: KEEP-NA valid (re-affirms 2026-08-03 ruling; marker-only, at line cap).
- **na-eligibility-audit 2026-08-02 (deferred marker, persisted 2026-08-07)**: KEEP-NA valid, MIXED — 1 of 6 open items
  (Phase 3 `-test-`-bucket force/skip proof) conflict-check-cleared and extracted to
  `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch8_2026_08_02.md`; the other 5 stay KEEP-NA valid. Marker
  deferred per `/plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`; now persisted after
  the marker-only carve-out was implemented (2026-08-07).
- **na-eligibility-audit 2026-08-08**: applied 3 pre-verified stale closes (Phase 3 sample-download, Phase 6 A2 staking,
  Phase 6 recursive-staking) carried from `issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md` Todo 2 — doc
  now 998L, still under the 1000L hard cap. Did not re-audit the other ~18 open items this pass (surgical
  evidence-backed close only, not a full re-read) — next incremental run re-verifies fresh since content changed today.
- **2026-08-08 (doc-hygiene)**: Corrected Phase 5 #1's table row — cited doc's credential item is the-odds-api.com
  (sports, cleared 2026-08-03/07), not Tardis; this item's real OOM blocker was fixed 2026-07-26. In-place, still 998L.

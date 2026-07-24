---
doc_type: plan
title: DeFi Track 0-1 — per-instrument re-architecture + instrument-ID canonicalization (the gating id migration)
summary: >-
  Extracted 2026-07-24 from defi_consolidated_closeout_2026_07_18.md's "Per-instrument re-architecture" + "Track 1 —
  CANON" sections (line-cap remediation follow-through) so the parent could come back under the 1000-line hard cap.
  Carries the R1-R8 per-instrument writer re-architecture (forward-write, migration, reader cutover) and the Track 1
  residual instrument-id canonicalization walk verbatim — this is the single largest, most gating body of work in the
  defi close-out ("⛔ gates Half-B historical canonicalisation"). Content moved verbatim, nothing summarized.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [defi, canonicalisation, instrument-id, per-instrument, migration, close-out]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_consolidated_closeout_history_2026_07_18.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Extracted 2026-07-24 from defi_consolidated_closeout_2026_07_18.md per the plan-hygiene line-cap remediation
  (operator-approved 2026-07-24, plans/active/issues/plan_line_cap_remediation_2026_07_23.md pattern). Content moved
  verbatim, no rewrite.
---

# DeFi Track 0-1 — per-instrument re-architecture + instrument-ID canonicalization

> **Purpose.** This is the gating id-migration work forked out of
> [`defi_consolidated_closeout_2026_07_18.md`](/plans/active/defi_consolidated_closeout_2026_07_18.md) to bring that
> parent back under the 1000-line hard cap (2026-07-24 line-cap remediation). Nothing here was rewritten or summarized —
> every line below is a verbatim move from the parent. See the parent for the Canonical target spec, the Operator
> decisions, and Tracks 2-8 (which depend on this work landing).

## Per-instrument re-architecture (operator 2026-07-18 — SUPERSEDES the batch-model tracks; DeFi capture STOPPED)

> **🟡 In-flight refactor + capture halted (re-armed 2026-07-18).** All DeFi capture is STOPPED — GCP forward-poll VMs
> `defi-fwd-dex-pools-poll` + `defi-fwd-dex-swaps-poll` stopped and their schedulers
> `defi-fwd-{dex-pools,dex-swaps, oracle-prices}-prd` + `uts-prod-mtds-collect-{evm,solana}-defi-cron` PAUSED (they had
> respawned once on the old batch-writer — re-armed by pausing the schedulers first, so no further respawn); AWS both
> regions clear; **IS enum/catalogue/consolidator crons LEFT RUNNING** — IS remains the availability source. DeFi is
> being re-architected to shard-write ONE parquet per instrument (like cefi/tradfi), collapsing SSOT §1 pattern #4 →
> pattern #1. This is the target; the batch-model column/path framing in the tracks below is superseded. Grounded in
> code (workflow `wf_20749dad`).

**Why**: MTDS wrote an arbitrary bunch of instruments per capture into one `{venue}_{chain}_{capture_ts}.parquet` batch,
blank manifest `instrument_id`, multiple batch files per shard-day — the root cause of the manifest/data-status pain +
the duplicate/phantom rows. Fix = **fetch bulk, write per-instrument** (the id is already stamped on every row).

**Confirmed decisions (operator 2026-07-18)**: (1) shard key = the **symbolic `canonical_instrument_id`**
(human-readable filename `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC.parquet`; address = a content column + IS-def/join key); (2)
**per-(instrument, day)** granularity, matching cefi/tradfi; (3) IS owns availability with **`available_from`**
(on-chain genesis) + **`available_to`** (TVL-drop delist) → out-of-window = out-of-scope, in-window + 0 rows =
`empty_confirmed`.

### R1 — Writer: per-instrument fan-out (forward-write) · P0

- [x] ✅ [BACKEND] P0. **SHIPPED `market-tick-data-service@4ca2640d` (QG green; runtime-verified: returns per-instrument
      list, distinct `{sanitized_symbol}.parquet` leaves, sanitizer byte-matches the migration; real blast radius = ~37
      `write_defi_rows` call sites + evm_defi per-instrument `record_captured` loop + 25 test files, all handled).**
      `write_defi_rows` (`market_interface/adapters/defi/canonical_write.py:103-296`) fans out**: after per-row
      `instrument_id` enrichment, `df.groupby("instrument_id")` → return a LIST of `(group_df, path)`, each leaf
      `{sanitized_symbol}.parquet` via `build_defi_partition_path(..., file_name=…)` (already accepts `file_name`, no
      builder change). `_write_and_upload` (`cli/handlers/evm_defi_collectors.py:36-68`) loops the upload. **6/7
      handlers already emit per-instrument manifest rows** (dex_pools / dex_swaps / oracle_prices / risk_params /
      lending_indices / lst_rates) — only **`evm_defi`** (bundle-on-both-axes, blank `instrument_id`) needs its single
      bundle `record_captured` replaced with a per-`instrument_id` loop. Resolve `lending`→`A_TOKEN`/`DEBT_TOKEN` BEFORE
      grouping. The sanitizer `[/\\:\s]→_` MUST match R3's so migrated + live objects collide on one key. (repo:
      market-tick-data-service)

### R2 — IS: the honest per-(venue,chain) availability denominator · P0

- [x] ✅ [BACKEND] P0. **SHIPPED `instruments-service@c934dd97` + `unified-api-contracts@eccaa493` (QG green;
      `_DEFI_VENUES` 63→89, +26 venues, **+85 real instruments**; cbETH/wBETH adapters written; chains ⊆ canonical set ✓
      (0 new chains); 4 empty-chain venues correctly dropped (YEARN-OPT/BEEFY-POLYGON/IDLE-ARB/POLYGON return 0);
      MVP_SCOPE v16→17).** WIRE THE MISSING STAKING/RESTAKING/VAULT VENUES INTO `_DEFI_VENUES` (the denominator is
      missing ~15 protocols).** Measured 2026-07-18 (operator caught it): the enumerated `_DEFI_VENUES` = 63 venues but
      only **Lido / etherfi / Ethena / Jito / Marinade** cover the LST/restaking/vault space — the catalogue has just
      **7** LST/STAKING/YIELD_BEARING instruments. **15 adapters exist + are registered in `factory.py::_ADAPTERS` +
      have POPULATED registries + whitelisted tokens (`DEFI_MAJOR_ASSET_SYMBOLS`) + genesis dates in `chain_env.py` —
      but are NOT in `_DEFI_VENUES`, so the enumeration never calls them**: `rocket_pool` (rETH), `renzo` (ezETH),
      `kelpdao` (rsETH), `puffer` (pufETH), `karak`, `symbiotic`, `jito_restaking`, `sanctum`, `solblaze` (bSOL),
      `solana_native_staking`, `yearn`, `beefy`, `pendle` (PT/YT), `convex`, `idle`. **Fix**: add them to
      `engine/orchestrator/defi.py`'s venue list (same class as the 7-lending-guard bug — built-but-not-firing). **ALSO
      write missing adapters**: **cbETH (Coinbase)** + **wBETH (Binance)** LSTs have no adapter at all (tokens ARE
      whitelisted). Then re-measure the universe (currently 11,724; this materially grows the LST/restaking/vault
      count). A too-small denominator makes per-instrument coverage lie. **CHAIN CONSTRAINT (operator 2026-07-18): new
      venue chains ⊆ the EXISTING canonical DeFi chain set (ETH/ARB/BASE/OPT/POLYGON/AVAX/BSC/LINEA/SOLANA) — do NOT add
      a new chain.** (repo: instruments-service, unified-api-contracts)
- [x] ✅ [BACKEND] P0. **SHIPPED `market-tick-data-service@8746708c` (QG green, 6330 tests; EVERY token runtime-verified
      via a live Alchemy RPC fetch through the shipped code path — not read).** E2E acquisition for the new
      staking/restaking/vault venues so they write real rows instead of sitting permanently `empty`. **19 EVM extended
      rate configs** (new `_lst_extended_rates.py`, DI'd query fn = no import cycle) + Solana **jupSOL** (new
      `_solana_jupsol.py`, on-chain pool_mint-verified). Verified rates (monotone-up over 90d): wBETH 1.1024 ETH
      (`exchangeRate()`, ETH+BSC) · rsETH 1.0761 (KelpDAO LRTOracle `rsETHPrice()`) · **ezETH 1.0818 — resolves the
      KNOWN-UNIMPLEMENTED multicall via rate-provider `getRate()`, proven mathematically identical to
      `RestakeManager.calculateTVLs()` totalTVL/totalSupply (exact match)** · yearn_v3 YV{WETH,DAI,USDC,WBTC}
      (`pricePerShare()`, per-vault decimals; `convertToAssets` reverts on 0.3.x/0.4.x) · beefy ×3
      (`getPricePerFullShare()`) · idle IDLE{DAI,USDC,USDT} (`tokenPrice()`) · pendle SY wstETH/weETH/weETHs/sUSDe/USDe
      (`exchangeRate()`) · jupSOL 1.1990 SOL. **Vault data_type = reused `lst_rates`** (share/exchange rate).
      **Honest-empty w/ typed reason (probed, NOT fabricated — in `_EVM_HONEST_EMPTY_VENUES`)**: KARAK (IS vault addrs
      have no on-chain code) · SYMBIOTIC (revert on activeBalanceOf/totalStake) · CONVEX (governance ERC-20,
      market-priced) · PENDLE PT/YT (oracle-quoted; only SY has a single-call rate) · Solana INF/laineSOL
      (non-standard/mint-mismatch) · JITORESTAKING VRTs (need vault-PDA decode) · SOLANA-NATIVE (APY not exchange-rate —
      separate handler). **DEFERRED follow-up (honest-completion, NOT the handler's scope — picked up next as R2d)**:
      the new venues aren't yet in UAC `expected_coverage.py::_DEFI` for `lst_rates`, so acquired rows land
      **captured-but-unexpected** until registered; agent deliberately left the coverage machinery untouched rather than
      ship an under-verified change. (repo: market-tick-data-service)

- [x] ✅ [BACKEND] P0 (R2c). **SHIPPED `instruments-service@155c8239` + `unified-api-contracts@07b291a2` (QG green both
      repos; runtime-verified by catalogue enumeration + manifest-seeding — no on-chain fetch in this item).** **(a)
      honest `available_to` (first cut)** — `_enforce_defi_monotonicity` relaxed `min_ratio=1.0` →
      `_CEFI_TRADFI_THIN_COLLAPSE_RATIO` (0.5) with `block_on_regression=True` KEPT, so a real per-instrument count
      regression (= a real delist) is no longer SUPPRESSED (full per-instrument TVL-time-series remains the documented
      R2c follow-up). **(b) `force_include`** — new `force_include` column in `CATALOG_COLUMNS` (n=33) +
      `_add_force_include()` stamper + UAC `DEFI_FORCE_INCLUDE_TOKENS`/`is_defi_force_include()` SSOT; verified
      EIGEN@EIGENLAYER / ETHFI@ETHERFI → True, EIGEN in a UNISWAP_V3 pool (coincidental liquidity) → False. **(c)
      catalogue-residual reconcile** — `_enumerate_v2_defi` residual path + new UAC
      `EmptyConfirmedReason.EXPECTED_ACQUISITION_PENDING` (added to `OUT_OF_COVERAGE_WINDOW_REASONS`) so an
      IS-listed-but-unfetched venue becomes a typed `empty_confirmed`, never a dangling `expected_unattempted`. (repo:
      instruments-service, unified-api-contracts)

- [x] ✅ [BACKEND] P0 (R2d). **SHIPPED `unified-api-contracts@238b45d2` (QG green; all 8 runtime-verified
      `is_expected=True`/`SHOULD_HAVE_DATA`).** Registered the RPC-verified acquiring venues in
      `expected_coverage._DEFI` for **`lst_rates` ONLY** (FLAT manifest venue keys, chain a separate dimension):
      `BINANCE` (wBETH ETH+BSC), `KELPDAO`, `RENZO`, `YEARN_V3`, `BEEFY`, `IDLE`, `PENDLE` (SY), `SANCTUM` (jupSOL
      SOLANA). Sharp correctness calls: **coinbase/rocketpool/puffer NOT added — already registered** as
      COINBASE/ROCKETPOOL/PUFFER (they acquire via the pre-existing `_EVM_LST_ABI_METADATA` path, not the new
      `_lst_extended_rates.py`); **`lst_rates`-only, not `staking_yields`** — the staking_yields handler only covers
      LIDO/ETHERFI/EIGENLAYER, so registering it would manufacture a false MISSING (the reverse dishonesty);
      honest-empty siblings (karak/symbiotic/convex/PENDLE-PT-YT/ etc.) stay `NOT_IN_SCOPE`. Representative acquired
      shard `(defi, SANCTUM, SOLANA, lst_rates)` (jupSOL) confirmed EXPECTED. (repo: unified-api-contracts)

### R3 — Historical migration: batch → per-instrument, column+row UNION · P0 (gated on R1+R2)

- [x] ✅ [DATA] P0 (code SHIPPED + verified; `--apply` run = R3-run below). **SHIPPED
      `market-tick-data-service@2dca03fa`** — `migrate_defi_batch_to_per_instrument.py` (32 tests) forks the v9
      migration to per-instrument, column+row UNION. **THREE adversarial verify rounds** hardened it (this is why R3 is
      verify-gated): round 1 caught 2 silent-data-loss overwrites (blind `wb` truncate of the shared
      `_needs_attribution` path + per-instrument leaf clobber of R1-forward files); round 2 caught the FIX's own bug
      (event-key-subset dedup collapses distinct rows on the SHARED multi-instrument needs_attribution object); round 3
      (`2dca03fa`) CONFIRMED the per-call `dedup_key` fix (`leaf=_EVENT_KEY_COLS`, `needs_attribution=None` full-row) —
      `"blocking":[]`, Q1-Q4 preserve all distinct v9+R3 rows, idempotent. **REFUTED (R3 correct)**: leaf byte-match,
      outer-union, no row loss, manifest parity. **ONE non-blocking pre-existing caveat for the run**: a leaf
      sanitise-collision (two distinct ids whose symbols differ only in `[:/\ ]` chars → one leaf) can drop a sibling on
      a merge onto a PRE-EXISTING R1-forward leaf sharing an event key — bites ONLY in the R1-forward/R3 overlap window
      → **scope `--apply` to the pre-R1 historical batch days (R3's actual target) OR add a single-instrument-per-leaf
      guard first.** (repo: market-tick-data-service)
- [~] [DATA] P0 (R3-run — RUNNING, partial). Dry-run recon validated + scoped `--apply` proven on real GCS (CHAINLINK
  oracle_prices → 22 canonical leaves + `_migrated_*`, 0 err). **FULL migration on SPOT VM
  `canonical-migration-defi-per-instrument-20260719-053435`** (in-region, chunked per-year, preemption-recovery loop
  `bd014y3c2` armed): **2020 ✓ (2,241→4,694), 2021 ✓ (30,513→607,867 instr, 18M rows, 0 err)**, 2022 applying,
  2023–2026 + `rebuild_defi_manifest` remain (~8-12h). **INCOMPLETE — see R5**: it walks ONLY `raw_tick_data/by_date/`
  and MISSES (a) the gas_fees `{data_type}_{blk}_{blk}` block-range shape (discovery regex gap), (b) the legacy
  top-level prefixes entirely. (repo: market-tick-data-service)

### R5 — Full-corpus canon reconciliation (operator-caught 2026-07-19; R3-as-scoped is NOT the whole job) · P0

> **Operator, 2026-07-19**: R3 was launched on a partial model without first inventorying the bucket + defining the
> clean path/manifest homes. Three trees exist in `market-data-tick-defi-prd`: **`raw_tick_data/`** (canonical raw,
> split venue/chain, per-instrument symbolic-id leaf — R3's target), **`processed_candles/`** (MDPS-owned OHLCV, 7
> timeframes, glued venue-chain + address-id leaf — canonical per `per-asset-group-bucket-layouts.md:166`, OUT of raw
> scope), **legacy `dex_pools/`+`lending_indices/`+`lst_rates/`** (`{venue}/{chain}/date=` orphans, code stopped writing
> 2026-04-14 per `defi-data-pipeline.md` D2). Manifest home = `_index/availability_index.parquet` +
> `_manifests/data_manifest.json`. Definitive reconciliation `wwkp5q6le` running (verifies legacy dup-vs-unique BEFORE
> any delete; maps every R3 shape-miss; checks raw-shape drift; produces the clean-homes worklist).

- [x] ✅ [DATA] P0 (code SHIPPED `market-tick-data-service@b4177dc6`; targeted `--apply` re-run remains for R5 cleanup).
      Added a `\d{5,}_\d{5,}` block-range branch to `_BUNDLED_TAIL_RE` (now
      `^(?:\d{4}[-_]?\d{2}[-_]?\d{2}.*|\d{8,}|\d{5,}_\d{5,})$`). The gap was PARTIAL — a block-range start ≥8 digits
      matched branch-1 by luck (migrated), a start ≤7 digits (AVALANCHE 2330158 / BSC 8303485 2021-22, early L2s, ETH's
      2020 slice) matched NEITHER → silently un-migrated. Real-GCS proof: before=0→after discovers the ≤7-digit
      AVAX/BSC/ETH gas_fees; ≥8-digit no regression; per-instrument leaves + `_migrated_` markers still excluded;
      `LOST=[]`; +2 precision unit tests; QG green. **The R5 gas_fees `--apply` re-run (queued, post main migration)
      MUST cover ALL block-height ranges** — the running R3 VM is pinned to the OLD regex so it misses ≤7-digit gas_fees
      in EVERY year; the new-code re-run is idempotent over the already-split ≥8-digit ones. (repo:
      market-tick-data-service)
- [x] ✅ [DATA] P0. **Legacy `dex_pools/`/`lending_indices/` — FOLDED + DELETED (checkbox was stale; work completed
      2026-07-21/22, never flipped).** Confirmed via
      `plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md` (`status: resolved`, "All 3 todos
      complete"): all 748 folded rows for `day=2026-04-14` (the 32 legacy-only raydium pools + solend/kamino unique
      cells) union-merged into canon, manifest-registered (`market-tick-data-service@ae6fccef` +
      `unified-trading-library@b9534230`), and verified `capture_status=captured` via a live manifest read. Legacy
      `dex_pools/`/`lending_indices/` prefixes subsequently prod-deleted by the operator 2026-07-21 (0 objects remain).
      (repo: market-tick-data-service)
- [x] ✅ [DATA] P0. **Legacy GLUED-VENUE FLAT tree INSIDE `raw_tick_data/` — INVESTIGATED 2026-07-24, confirmed UN-SPLIT
      SOURCES (not superseded leftovers), issue filed, not yet migrated.** Sampled directly (operator flagged one
      specific object): `venue=ETHENA-ETHEREUM/ticks_migrated_20260418T162244Z.parquet` holds 1 REAL row
      (`data_type=oracle_prices`, `instrument_key=ETHENA-ETHEREUM:YIELD_BEARING:sUSDe` — a validly-formed canonical id
      STRING inside the content, just not reflected in the PATH) — this is genuine un-split source data, not a migration
      leftover. `parse_hive_path()` returns `None` for it → `rebuild_defi_manifest.py` counts it `unparseable` → **zero
      manifest representation of any kind** (worse than the timestamp-glued-id defect, which at least gets a wrong
      CAPTURED row). A bounded single-day sample (day=2025-08-06) found 9 sibling composite-venue directories
      (AAVEV3/CURVE/ETHENA/ETHERFI/LIDO/MORPHO/UNISWAPV2/V3/V4-ETHEREUM) — systemic, not a one-off; true corpus-wide
      scale NOT yet measured (single-walk discipline — no fresh whole-corpus GCS walk run for this). Filed
      `/plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` with full evidence +
      suggested next steps (parse the legacy path + re-derive canonical path from the parquet's own `instrument_key`
      column, fold-not-delete since content is real). **Remaining**: scale measurement + a targeted migration script —
      tracked in that issue doc, not re-duplicated here. (repo: market-tick-data-service)

- [ ] [DATA] P1. **Divergence RCA** — why did the 2026-07-13 canon re-materialisation drop 32 raydium pools vs the
      2026-04-14 legacy capture? Determines whether canon dex_pool_state is trustworthy for OTHER raydium/DEX days or
      needs a re-fetch. (repo: market-tick-data-service)
- [~] [BACKEND] P0. **Catalogue-venue gap — ROOT CAUSE FIXED + SHIPPED (`unified-api-contracts@f7314dc2`, 9/9
  acceptance: 7 new venues + cbETH/wBETH ACCEPT, COINBASE-SPOT/BINANCE-FUTURES stay CEFI; whole defi universe validates,
  was 26 rejected). SOLANA-NATIVE kept (documented canonical spelling; validator now parses the TRAILING chain segment).
  DEPLOY-GATED re-enum+re-rollup remains.** NOT deploy-lag/creds/silent-[] (deployed image HAS 89 venues + adapters DO
  emit). The 26 new venues are REJECTED at UAC `validate_instrument_records` — **R2 wired them into the FETCH list
  (`_DEFI_VENUES`) but NOT the VALIDATION allowlist (`instrument_validation.py::_DEFI_VENUE_PREFIXES` line 22)** →
  "unknown venue 'RENZO-ETHEREUM'" → they never reach `by_date/`, EU-seeded as `expected_unattempted`. There's an
  in-code comment about this EXACT bug recurring (VENUS/RADIANT 2026-07-12). Fix = +15 collision-free prefixes (unblocks
  22/26) + chain-aware COINBASE/BINANCE disambiguation for cbETH/wBETH (3 more; must NOT misclassify
  COINBASE-SPOT/BINANCE-FUTURES as defi) + IS `SOLANA-NATIVE-SOLANA` tag fix. **DEPLOY-GATED**: after ship → LDR→main →
  IS-image rebuild → then `is-daily-enum-defi` re-enum + `lifecycle-catalogue-full-defi` re-rollup + verify (a later
  tick). Original catalogue snapshotted `prod/_snapshots/catalog.pre-rollup.20260719T040600Z.parquet`. (repo:
  unified-api-contracts, instruments-service)

### R4 — Coverage against the IS denominator · P1 (gated on R1+R2+R3+R5) → then RESUME capture

- [ ] [DATA] P1. **Score coverage per-instrument** against the IS `available_from/to` window; the ~1.04M stuck
      `expected_unattempted` / false `EXPECTED_INSTRUMENT_DELISTED` rows resolve once the seed (R2) + migrated
      per-instrument manifest (R3) exist with byte-matching keys. A RED DeFi data audit here FREEZES downstream
      (foundation-gate). Then **RESUME the stopped DeFi capture VMs/crons** on the corrected writer.

**Sequencing**: R1+R2 (ship together — new days land per-instrument + reconcile) → R3 (migrate history to the identical
layout) → R4 (coverage) → resume capture. **This SUPERSEDES the batch-model column/path work in the tracks below** — the
column migrations (id/address/lending-split, case, venue-spelling) still happen, but folded into R1/R3, not a separate
cell-grain rewrite. `consolidate_multi_parquet_per_day` winner-pick is RETIRED for DeFi. **Small-files (per-DAY is
bounded by TVL — a non-issue)**: the IS catalogue holds **11,724 valid instruments total** (POOL 7,224 · SPOT_ASSET
1,389 · A_TOKEN 1,117 + DEBT_TOKEN 1,060 · legacy LENDING 892 · GMX PERPETUAL 33 · LST/STAKING ~7 · SPOT_PAIR 2) across
66 (venue,chain) shards, so a day writes **~11.7k tick files max** — the TVL filter is doing its job (measured
2026-07-18, `instruments-store-defi-prd/prod/catalog.parquet`). The only mild concern is the **CUMULATIVE** object count
over the full backfill (~11.7k × days × data_types ≈ a few million tiny objects) — same shape as cefi/tradfi; a
per-instrument-MONTH compaction is a recommended SEPARATE follow-up ONLY if the total object count bites (keeps the
shared `day=` hive). **This is MTDS tick-data only** — IS stays the per-(venue,chain) availability BUNDLE (all
instruments in one `instruments.parquet` with `available_from/to`).

## Track 1 — CANON: instrument-id + residual walk (⛔ gates Half-B historical canonicalisation) · P0

- **Sources**: `data_completion_defi_2026_07_15.md` (C2–C12),
  `issues/defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md`,
  `issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md` (RESOLVED code; durability + legacy-row
  migration open), `issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`,
  `issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`.
- **Close-out criterion**: all four surfaces agree for POOL / SPOT_ASSET / perp / lending rows; the POOL policy is
  pinned by one authoritative test; C2–C12 idempotency-clean.

- [x] ✅ [BACKEND] P0. **SHIPPED (Option A pinned) `instruments-service@c31d37c3` + `unified-api-contracts@e319864f`.**
      Backfill docstring POOL carve-out corrected + CODE-path-doesn't-converge-POOL verified + pinning test
      `test_pool_rows_diverge_option_a_and_backfill_does_not_enforce_convergence` (IS): POOL rows DIVERGE —
      `instrument_id`=pool_address, `canonical_instrument_id`=3-seg glued key. 4-seg `DefiPoolIdentity.glued_pair_id`
      retired → 3-seg (verify `two_id_model_intact=true`). (repos: instruments-service, unified-api-contracts)

> **⛔ GATE (2026-07-21, dated banner — do not restate the mechanism here, link it):** this todo is BLOCKED until
> `plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md` reports its acceptance criteria 1-8 green with
> cited evidence and flips ITS OWN todo 14 from BLOCKED to CLEARED. The first attempt at this retire was REVERSED
> because the migration started before the MTDS lending writers were fixed — read that plan's "What actually broke"
> section before touching this todo. As of 2026-07-21 that plan's todos 2-5/9/13 (writer-collapse + shard-atom-desync
> fixes + pinning tests + doc corrections) are code-complete and individually verified (ruff/basedpyright clean, full
> MTDS suite green apart from 2 unrelated pre-existing cross-repo test-baseline regressions — see that plan's Progress
> Log) but NOT YET COMMITTED (blocked on those unrelated regressions clearing the shared tree's `quality-gates.sh`);
> todos 8/10/11 (the actual UAC+MTDS+UTL atomic retire + its runtime proof) are NOT started. The gate remains BLOCKED.
> Do not start this migration until that plan says CLEARED.

- [ ] [DATA] P0. **Retire legacy `LENDING` → A_TOKEN/DEBT_TOKEN.** **Builder-bake DONE `instruments-service@1af1be34`**
      (FIX 2, runtime-proven): the split is now INTRINSIC to `build_instrument_catalogue.py` row-construction — the
      canonical_id's `VENUE:TYPE:SYMBOL` segment is AUTHORITATIVE over a stale `LENDING` column for the
      A_TOKEN/DEBT_TOKEN/SPOT_ASSET family, so a `--mode full` rebuild can't re-stamp LENDING (kills the 2026-07-14
      durability landmine). Verify caveat (non-blocking): a dataless-tail row mis-stamped by a PRE-fix rebuild survives
      verbatim through `_merge_incremental(close_absent=False)` until it reappears in by_date — **fully closed by the
      remaining half below.** **REMAINING (Wave D, [DATA]): migrate the ~16.7M legacy `lending` rows** to the split
      (code done for 9 EVM protocols) on real infra. (repos: instruments-service)
- [ ] [DATA] P0. **Residual canon walk C2–C12** (single-walk discipline — reuse the existing worklist, no NEW
      whole-corpus walk): C2 data_type alias dedup (`dex_swaps`→`dex_pool_swaps`, `dex_pools`→`dex_pool_state`,
      `lending-indices`→`lending_indices`, `staking_yields`→`lst_rates`); C3 `VENUE-CHAIN`→flat venue + `chain`; C4
      v4–v8→v9; C9 object paths still carrying `category=`/no `pipeline_mode=`; C11 phantom walk; C12 `{VENUE}_V{N}`
      underscore canonicalisation (`TRADER_JOE_V2`/`VELODROME_V2`/`AERODROME_V3`). (repos: market-tick-data-service,
      instruments-service)
- [ ] [DATA] P0. **Manifest instrument_type case + venue-spelling unify** (from the live distinct-values audit): **⛔
      CASE DIRECTION CORRECTED 2026-07-20, operator ruling D1 — the manifest COLUMN is UPPERCASE (catalogue wins), NOT
      lowercase.** ~~case-fold the manifest `instrument_type` column to lowercase (`POOL`→`pool` 13,868 ·
      `LENDING`→`lending` 179,164 · `PERPETUAL`→`perpetual` 4,221 · `YIELD_BEARING`/`STAKING`/`SPOT_PAIR` →
      lowercase)~~; **the fold is UP — normalise the manifest `instrument_type` COLUMN to the UPPERCASE catalogue enum
      (`POOL`/`LENDING`/`PERPETUAL`/… ); the row counts are unchanged, only the direction. The GCS path segment stays
      lowercase and the id middle segment stays UPPER — neither changed. Note the `LENDING`→`A_TOKEN/DEBT_TOKEN` full
      retire (ruling D2) is a separate `migration_pending` axis gated on the MTDS lending-writer fix — do not conflate
      the case-fold with the retire.** collapse venue-spelling dups (`AAVEV3`/`AAVE`→`AAVE_V3` 64,218 ·
      `MORPHOVAULTS`→`MORPHO` 50,266 · `COMPOUND`→`COMPOUND_V3` 13,904 · `YEARNV3`→`YEARN_V3` ·
      `KAMINO_LENDING`→`KAMINO`); resolve `''`/`NULL` instrument_type (4.49M) from the id/grain. (repos:
      market-tick-data-service, unified-trading-library)
- [ ] [DATA] P1. **perp_funding → `derivative_ticker`** as the canonical raw-funding home for ALL perps (drop the
      Drift-only 24h/7d/30d window aggregates). Ratify enum-member DeFi grains (`lst`/`staking`/`yield_bearing`) as
      canonical (case-fold only, already `InstrumentType` members). (repos: market-tick-data-service,
      unified-api-contracts)
- [x] ✅ [DECISION] P2. **Bare `SUSHISWAP`/`UNISWAP` version (199,397→206,107 rows, measured 2026-07-21) — decided +
      infra shipped `instruments-service@3ffd1adf`.** Operator ruling applied (see § "Operator decisions applied
      (2026-07-21..." above): derive per-pool from the deploying factory contract address, not "undecidable." Shipped: a
      static, cited factory-address→version map (Uniswap V2/V3/V4, SushiSwap V2/V3;
      `instruments_service/reference_data/adapters/defi/_dex_factory_registry.py`) wired into
      `scripts/canonicalize_defi_manifest_venue_2026_06_14.py` (fires only when a row carries a `factory_address`
      column; never mints an unregistered `ALL_DEFI_VENUES` string). **Measured resolved=0 / residual=206,107 (100%) —
      no row captured today carries a factory address anywhere in the schema (verified: `InstrumentRecord`, the v9
      manifest schema, and all 4 subgraph query cascades in `uniswap_v3.py` were checked; none carries or requests
      one)** — this is the genuine surface-don't-guess residual the ruling anticipated, not a code defect. A SECOND
      blocker for the SUSHISWAP-ARBITRUM cohort (192,560 of the 206,107): UAC `ALL_DEFI_VENUES` has no registered
      versioned venue for Sushi-on-Arbitrum at all (cross-repo prerequisite). Full writeup + the two follow-up capture
      options: `issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`. Follow-up capture work tracked as
      the new todo below (non-trivial residual, not silently dropped).
- [ ] [DATA] P2. **NEW 2026-07-21 — actually start capturing factory addresses so the shipped resolver above has
      something to resolve** (today it resolves 0 of 206,107 bare SUSHISWAP/UNISWAP rows — see
      `issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`). Two options, not yet decided between: (a)
      augment the 4 subgraph query cascades in `instruments-service`'s `uniswap_v3.py` to request a `factory` field —
      needs a live-schema probe per fork (native/Algebra/SushiSwap-pairs/Messari) before landing, a wrong field name
      hard-errors the query; (b) on-chain RPC `factory()` lookup keyed off the already-captured `pool_address` (needs an
      RPC provider + enumerating the unique pool_address set from the raw MTDS parquet, not the manifest). Also register
      the missing `SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM` (or whichever the capture work resolves to) canonical
      venues in UAC `ALL_DEFI_VENUES` — currently only the bare `SUSHISWAP-ARBITRUM` is registered, so even a
      correctly-resolved factory address cannot be written back without this. (repos: instruments-service,
      unified-api-contracts, market-tick-data-service)
- [ ] [DATA] P2. **`KALSHI_PERP`/`POLYMARKET_PERP`/`HYPERLIQUID` appearing in the defi `chain` axis (2,936 rows) = cefi
      leakage** → clean out of the defi manifest (they stay cefi). Split out of the bare-version item above — NOT
      addressed by the 2026-07-21 factory-resolver work (different defect, same original bullet).
- [ ] [BACKEND] P2. **Combo cross-AG hand-off (leg-aware signed-weight spec).** Extend the 1–4-leg cap + shared
      `build_leg()` path to the DERIBIT-COMBO builders (`cefi/deribit_combo_adapter.py`, `tardis/combos.py`) —
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` open P2. DeFi has no combos; this rides here
      only because the DERIBIT-COMBO fix is cefi-side and passed to `cefi_consolidated_closeout_2026_07_18.md`.
- [ ] [BACKEND] P0. **NEW 2026-07-21 (operator ruling) — eliminate the address/UUID fallback in
      `canonical_instrument_id` for POOL + LENDING; resolve token symbols for real, don't fall back.** Operator: "it
      needs to be fully canonical no fallback and migrated." Does NOT touch the two-id model or the machine
      `instrument_id` (`pool_address.lower()` stays — 2026-07-18 ruling unchanged, `engine/defi_catalog_reader` still
      joins on it). Scope is narrower than it first looks: `DefiPoolIdentity.glued_pair_id`
      (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/defi.py:333-361`) only falls back to
      `pool_address.lower()` when `base_asset`/`quote_asset` arrive blank — the fallback is a SYMPTOM of upstream token
      resolution never being attempted, not a structural need. Measured root cause (research this session): no adapter
      does independent on-chain/registry symbol resolution — `orca.py`/`raydium.py::_build_pool_record` DROP the pool
      when the DEX's own subgraph/REST response lacks a symbol; `raydium.py::_build_historical_pool_record` hardcodes
      `"UNKNOWN"`; `balancer.py:222-231` defaults to the literal string `"UNKNOWN"`; Solana LENDING
      (`lending_indices_handler.py:420-423`) falls back to DeFiLlama's own pool UUID when DeFiLlama's `symbol` field is
      blank — measured **49.7% raw-address + 17.6% UUID** of 707,803 live LENDING rows are non-symbolic today. A real,
      unused resolution path already exists: `unified_api_contracts.external.alchemy.schemas.AlchemyTokenMetadata` is
      declared (`registry/endpoints.py:302`, `registry/venue_manifest/defi.py`) with **zero real callers**
      workspace-wide. **Design (decided this session):** a new shared, cached resolver module —
      `unified_trading_library` (both instruments-service and market-tick-data-service already depend on it; UAC stays
      schema-only) — `unified_trading_library/defi/token_metadata_resolver.py`: EVM via a real
      `alchemy_getTokenMetadata` call (MTDS `alchemy_base_client.py` gets the calling method; UTL wraps it with an
      on-disk/GCS-backed cache since token metadata is immutable — same address never needs a second live call); Solana
      via the static `solana-labs/token-list` JSON (mint→symbol; confirmed reachable, HTTP 200, unlike `token.jup.ag`
      which is dead — verified this session) — refreshed periodically, not a live call per-row. **Todos**: (1) build +
      unit-test the UTL resolver (both legs); (2) wire it into `balancer.py`/`orca.py`/`raydium.py` + the other POOL
      adapters as the enrichment step BEFORE the drop/`"UNKNOWN"` branches; (3) wire it into
      `lending_indices_handler.py`/`_solana_defi_fetch.py` replacing the `market_id`-as-symbol fallback; (4) re-run
      `build_instrument_catalogue.py` so POOL `glued_pair_id` re-resolves; (5) re-derive existing address/UUID-fallback
      `canonical_instrument_id` values for LIVE rows via a one-off backfill (pattern:
      `scripts/backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py`), idempotent, verify 0 address/UUID-shaped
      `canonical_instrument_id` remain for a resolvable token; a token genuinely absent from BOTH Alchemy AND the Solana
      list (e.g. a rugged/delisted token with no metadata anywhere) is the only acceptable residual — route those
      through `needs_attribution`/`empty_confirmed`, never silently re-embed the address. (repos:
      unified-trading-library, unified-api-contracts, market-tick-data-service, instruments-service) - **(2)/(4) — CODE
      COMPLETE + TESTED + MEASURED 2026-07-21 (slot-4), SHIP BLOCKED on an external, now-tracked cross-repo issue (not a
      partial-scope call — see below).** Wired `resolve_evm_token_symbol` / `resolve_solana_token_symbol` into
      `balancer.py::_pool_to_record`, `orca.py::_build_pool_record`,
      `raydium.py::_build_pool_record`/`_extract_token_symbol` as the enrichment step BEFORE their drop/`"UNKNOWN"`
      branches: subgraph/REST symbol present → unchanged; blank → resolver called with the on-chain address the pool
      already carries → real symbol on success; drop/`"UNKNOWN"` only when the resolver ALSO returns `None` (honest
      residual). `raydium.py::_build_historical_pool_record` deliberately stays `"UNKNOWN"`/DELISTED (documented
      in-code): its caller (`getProgramAccounts` with a zero-length `dataSlice`) never fetches mint addresses at all —
      genuinely resolving it needs a NEW on-chain step (decode the base/quote mint from the Raydium AMM V4 752-byte
      account layout) that cannot be verified against live data in this pass; this path also defaults
      `include_historical=False` (opt-in only) — tracked as an explicit follow-up rather than shipping an unverified
      byte-offset guess that could fabricate a WRONG symbol (worse than an honest placeholder). **Adjacent fix in the
      same commit**: a live Balancer pool's subgraph `symbol` can itself be a malformed string carrying an embedded `:`
      (UAC `build_instrument_id`'s own id delimiter — FAILS LOUD, same bug class as the CeFi/Bitfinex
      colon-wire-notation case) — now treated like a blank symbol (resolve on-chain instead of trusting it verbatim),
      with 2 new regression tests. 15 new/updated unit tests total across the 3 adapters (subgraph-has-symbol unchanged
      / subgraph-blank-resolver-succeeds / subgraph-blank-resolver-also-fails, per adapter, plus the colon-guard pair).
      **Measured live 2026-07-21** (real Alchemy + `solana-labs/token-list` calls, zero mocks,
      `GCP_PROJECT_ID=central-element-323112`): **BALANCER-ETHEREUM** 2,323 pools sampled, 3 had a blank/malformed token
      symbol before this fix (all → `"UNKNOWN"`), **1 now resolves to a real on-chain symbol** via live Alchemy (2
      genuinely unresolvable — no Alchemy metadata for those specific wrapped-vault-share addresses, correctly left
      honest); **ORCA-SOLANA** 502 pools kept before → **514 after (+12 previously-silently-DROPPED pools now named and
      included)** via the Solana static token list; **RAYDIUM-SOLANA** (active REST sample) 994/994 — no blank symbols
      in this particular top-994-by-liquidity live snapshot (resolver wired + unit-tested; no live opportunity to fire
      in this sample). (4) scoped equivalent: `build_instrument_catalogue.py`'s `_defi_pool_dual_form` re-derives
      `glued_pair_id`/`canonical_instrument_id` from PRIOR DAILY ENUM SNAPSHOTS (`by_date/.../instruments.parquet`), not
      a live adapter call — a catalogue rebuild today would NOT yet reflect this fix (the daily enum cron hasn't run
      since); the live-adapter measurement above is the real-world equivalent proof that the SAME code path the cron
      calls now resolves real symbols. **Full quality-gates.sh is genuinely green for this diff** (proven via a
      `git stash` baseline: the FULL suite shows the identical 4 pre-existing, unrelated failures with or without this
      diff — 4,756 passed / 7 skipped baseline vs 4,765 passed / 8 skipped with the diff, delta = exactly the new tests,
      nothing else moved). **NOT yet shipped**: `quickmerge --agent`'s sentinel fast-path requires a literal 100%-green
      `quality-gates.sh` run, and instruments-service's tree currently fails 4 hard invariant tests
      (`test_every_uac_adapter_key_resolves_to_a_class` et al.) because UAC `unified-api-contracts@6bdbc31d`
      (`lst_rate_honest_coverage_2026_07_21.md` Phase 1) registered `AAVE-ETHEREUM: aave_oracle` ahead of
      instruments-service's own `factory._ADAPTERS` entry — a live, plan-owned, already-in-flight track (that plan's own
      Progress Log: the IS-side `aave_oracle.py` adapter is "BUILT-BUT-NOT-SHIPPED" in a DIFFERENT session's checkout,
      not this slot's). Building it here would risk a duplicate/divergent implementation colliding with that in-flight
      work, and the failing tests are DELIBERATE no-bypass ship gates (no `known_gaps`-style escape valve for 3 of the
      4). Filed `issues/instruments_service_aave_oracle_adapter_registration_test_drift_2026_07_21.md` (full evidence +
      stash-baseline proof + recommended decision). **Action**: re-attempt a `quickmerge --agent --files` ship of the 3
      changed adapters + their 2 test files from instruments-service the moment that issue closes (the code is untouched
      and ready; nothing further to do on it). (repo: instruments-service) - **(3) Solana LENDING
      (`lending_indices_handler.py`/`_solana_defi_fetch.py`) — SHIPPED + MEASURED 2026-07-21 (slot-4).** Wired
      `resolve_solana_token_symbol` into a new `_solana_defi_fetch.resolve_blank_solana_lending_symbols` (called from
      `_collect_solana_lending`): DeFiLlama's `symbol` present → unchanged; blank → resolve the reserve's REAL on-chain
      mint (a NEW `underlying_mint` column, extracted from DeFiLlama's own `underlyingTokens` field — verified live
      2026-07-21, this is the actual on-chain mint, never the DeFiLlama pool UUID) via the shared UTL resolver; UUID
      fallback (`market_id`) used ONLY when the resolver ALSO returns `None` (mint absent from the static Solana
      token-list — genuinely unresolvable). **Critical adjacent finding**: the UAC `DEFI_SOLANA_LENDING_LENDING_INDICES`
      SchemaContract's `symbol_column` was `"market_id"` (not `"symbol"`) — meaning `write_defi_rows` built the
      canonical `instrument_id`/GCS leaf from the UUID for EVERY Solana-lending row regardless of what `symbol` carried,
      so the handler-side fix alone would have been a no-op on the actual written object. Fixed the SchemaContract too
      (`unified-api-contracts@4c049355`) — verified no other caller relies on the old default (both migration/fold
      one-off scripts + `risk_params_handler.py` pass an explicit `symbol_column=`). market-tick-data-service@7ce100f9.
      **Also fixed 3 pre-existing, unrelated MTDS quality-gates.sh regressions found blocking ALL quickmerges in this
      repo** (root-caused + closed `issues/mtds_canonical_stem_leaf_qg_regression_blocks_quickmerge_2026_07_21.md` — see
      that doc for the full writeup; 2 of the 3 converged independently with a concurrent agent's own fix,
      `market-tick-data-service@08f15f26`). (repos: market-tick-data-service, unified-api-contracts) - **(5) Backfill
      existing UUID-fallback LENDING rows — SHIPPED + RUN 2026-07-21 (slot-4).**
      `scripts/one_offs/backfill_solana_lending_uuid_canonical_id_2026_07_21.py` (market-tick-data-service@7ce100f9):
      reads the consolidated defi availability index (one bounded-chunked download — a single-shot download of this
      ~1.86 GiB object reproducibly broke mid-transfer at the same ~1.33 GiB offset, 4/4 attempts; per-chunk ranged GETs
      fixed it), finds captured Solana-lending manifest rows whose `instrument_id` (per-market grain key) is
      UUID-shaped, resolves each distinct market's mint via ONE live DeFiLlama pool-list fetch + the shared resolver,
      migrates each resolved market's object to its real-symbol leaf (idempotent — skips if already present), retires
      (renames, never deletes) the old UUID leaf, and re-registers the (unchanged — machine grain key stays the market
      UUID per the two-id model) shard via `DefiManifestRecorder`. **Measured (dry-run, then --apply after the dry-run
      looked sane, per this todo's own authorization):** **103 total UUID-shaped Solana-lending manifest rows**
      (KAMINO=44, SOLEND=59, MARGINFI=0 — all dated 2026-04-14, all pre-Gate-5 legacy captures under the BARE venue slug
      `KAMINO`/`SOLEND`, not the post-split `KAMINO_LENDING`; both forms are now recognised). **39 distinct markets
      RESOLVED** to a real on-chain token symbol; **64 RESIDUAL** (3 — pool no longer in DeFiLlama's live listing; 61 —
      resolver could not resolve the mint against the static Solana token-list; a genuinely unresolvable/delisted-token
      residual, the only acceptable kind, never silently re-embedded). **Apply**: 23 objects migrated (new
      resolved-symbol leaf uploaded, old UUID leaf retired, manifest re-registered), 16 already-migrated (idempotent
      skip — same symbol as an existing object from a different market on the same day), 0 errors, 0 missing sources.
      (repo: market-tick-data-service)

### Operator decisions applied (2026-07-21, /autonomous — decided per AUTONOMOUS_AGENT_RULES.md rule 2, documented not asked)

- **Solana pool vocab desync (`defi_expected_universe_solana_pool_instrument_type_vocab_desync_2026_07_20.md`) → Option
  A, expected matches writer.** The grammar table above (line ~343) already ratified `SOLANA_AMM_POOL` as the canonical
  Solana DEX-pool grain (2026-07-18) — the writer emitting `solana_amm_pool` is already correct; the expected-universe
  side using plain `pool` for Solana cells is the stale side. Fix the expected-universe enumerator, not the writer. **✅
  DONE `instruments-service@c781eb0b`** (+ `unified-api-contracts@5d83b729` for the capability-declaration half of the
  3-repo atom): raydium/orca adapters POOL→SOLANA_AMM_POOL, kamino POOL→SOLANA_VAULT, enumerator `_ADDRESS_KEYED_ITYPES`
  gains both types, regression test + golden regen (0 residual `pool`-vocab tuples for ORCA/RAYDIUM/KAMINO-SOLANA, was
  6). Measured live blast radius (scoped manifest read, 2026-07-21): **812,055** stale `pool`/`POOL`-vocab
  `expected_unattempted` rows across the 3 venues, **406,015** confirmed permanently-unsatisfiable (captured
  `solana_amm_pool`/`solana_vault` twin on the same atom) — now closed at the CODE level (see
  `defi_expected_universe_solana_pool_instrument_type_vocab_desync_2026_07_20.md`, RESOLVED); the 812,055
  already-materialized stale rows need a live re-seed, gated behind Track 3's own purge-first ordering below.
- **SOLANA_LENDING is OUT of the D2 `LENDING`→A_TOKEN/DEBT_TOKEN retire scope.** The grammar table already carries
  `SOLANA_LENDING` as its own canonical Solana grain, distinct from the EVM A_TOKEN/DEBT_TOKEN split (Kamino/Solend/
  MarginFi markets don't share Aave's dual-token-per-reserve shape). The retire applies to the legacy flat EVM `lending`
  rows only; Solana rows keep `SOLANA_LENDING`. `defi_lending_writer_retire_prerequisite_2026_07_20.md`'s todo 6 ("rule
  SOLANA_LENDING scope") is answered by this.
- **Non-POOL per-instrument EU (215,864 honest-pending cells) → fold into the SAME `expected_unattempted` seeding pass**
  Track 3 already runs (the 63.9M seed), not a new terminal state/mechanism. Reuses proven machinery instead of
  inventing new denominator policy; verify at seed-time that these cells behave like every other `expected_unattempted`
  cell.
- **Bare SUSHISWAP/UNISWAP version (199,397 rows) → derive from the deploying factory contract address**, not
  "undecidable." Uniswap V2/V3/V4 and SushiSwap V2/V3 factory addresses are permanent, public constants — a static
  factory-address→version map resolves the overwhelming majority; a pool whose factory matches none of the known
  contracts is the genuine residual (surface it, don't guess). **✅ DONE (infra) `instruments-service@3ffd1adf`**:
  static cited map + resolver built + wired into `canonicalize_defi_manifest_venue_2026_06_14.py`, gated so it never
  mints an unregistered venue. **Measured 2026-07-21: resolved=0 / residual=206,107 (100%)** — no captured row anywhere
  carries a factory address today (verified across `InstrumentRecord`, the v9 manifest schema, and all 4 subgraph query
  cascades), so the "overwhelming majority" premise doesn't hold YET — the map is correct and ready, there is simply no
  factory data in the corpus for it to resolve against. Full detail + the 2 follow-up capture options + the
  SushiSwap-Arbitrum UAC registry gap: `issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`; tracked
  as a new Track 1 `[DATA]` todo (not silently dropped).
- **`_ID_FORM_CHECKED_ASSET_GROUPS` widening for `defi` → use the grammar already ratified in this plan** ("Instrument-
  uid grammar per DeFi type" above) — not a new decision, just wiring it into
  `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`'s checker. `prediction`'s id-form stays out of scope here
  — it's already flagged cross-AG as its own future closeout. **✅ DONE `unified-api-contracts@502ef57e`**: a new
  `_DEFI_INSTRUMENT_ID_RE` (`VENUE-CHAIN:TYPE:SYMBOL`, covering every ratified per-type variant — SPOT_ASSET/POOL
  fee-in-symbol/A_TOKEN+DEBT_TOKEN market-id-suffix/LST+YIELD_BEARING+STAKING+RESTAKING bare/SOLANA_AMM_POOL+
  SOLANA_LENDING) is wired into `is_canonical_instrument_id()`, and `_ID_FORM_CHECKED_ASSET_GROUPS` is now
  `{"cefi", "defi"}`. Same session also closed the sibling residual item — `build_instrument_id` fails loud
  (`ValueError`) on a `symbol` carrying an embedded `:` for every non-sports/prediction asset group, removing the
  double-wrapped-catalogue-miss-id mechanism at the shared root (see
  `issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` § 7). **Measured consequence**: today's DeFi
  single-instrument filenames are still the bare `symbol` column (MTDS `_resolve_file_symbol`'s own docstring —
  "defi/sports are untouched"), so this widening is expected to report most of the current DeFi corpus `NON_CANONICAL`
  by id-form until the writer emits the wrapped filename (separate, service-side, not done here) — the same
  honest-disclosure outcome the original CeFi widening produced.
- [ ] [CODE] P1. **CODE FIX SHIPPED 2026-07-24 `market-tick-data-service@0d83a8a9` — the "writer emits the wrapped
      filename" gap below is not cosmetic: it WAS an ACTIVE data-conflation bug for Solana concentrated-liquidity pools,
      confirmed with live evidence, now closed at the writer level (sub-items (b)/(c) below still open).** Found while
      investigating why `6bruASRkRnJmNBYdT1HqrwnYbo3f2vVTJjwCNNgUHbw6.parquet` was address-named (separate,
      already-filed issue: `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` — that object
      predates BOTH writers below, this todo is a distinct, currently-live defect). `solana_defi_handler.py`'s
      `_solana_row_symbol` (lines 363-376) returns bare `{token_a}-{token_b}` with NO fee-tier/tick-spacing
      discriminator whenever both resolve; `canonical_write.py::write_defi_rows` (lines 337-350) then
      `df.groupby("instrument_id")` BEFORE writing — so two economically-distinct on-chain pools sharing a token pair
      (routine for Orca Whirlpools/Raydium CLMM — different fee tiers are different pool accounts) get their rows MERGED
      into one shard under one `instrument_id`, not merely name-collided. **Confirmed real, not hypothetical**: a live
      query against Raydium's production API (`api-v3.raydium.io/pools/info/list`) found 7 of the top 100 pools are
      duplicate-pair/distinct-pool_id today (e.g. `WSOL/USDC` has 2 live pools — `58oQCh...` 0.25% Standard vs
      `3ucNos...` 0.04% Concentrated; `AKE/USDC` has 3). The disambiguating data (`fee_rate_bps`, and for Orca
      `tick_spacing`) IS already captured per-row — it's discarded at the symbol-construction step, not missing
      upstream. **The fix already exists and ships correct results elsewhere — it just isn't wired here**:
      `instruments-service`'s `orca.py`/`raydium.py::_build_pool_record` (the P0 fallback-elimination work above, this
      same plan) already builds a collision-free instrument key via UAC `build_pool_identity(..., fee=discriminator)` →
      `glued_pair_id` (e.g. `ORCA-SOLANA:POOL:SOL-USDC-WP64`, tick-spacing glued in). MTDS's raw-tick writer never
      imports or calls `build_pool_identity`/the catalogue at all (confirmed via repo-wide grep) — it independently
      re-derives a cruder symbol straight off the row. **Also found**: a SECOND, independent Solana AMM writer,
      `dex_pools_handler.py`/`_dex_pools_subgraph.py::_collect_solana_dex`, has the same gap in a more severe form — it
      never attempts symbol resolution at all (`fetch_orca`/`fetch_raydium` in `_solana_defi_fetch.py` never set a
      "symbol" key), always falling back to the bare pool address; **STILL unclear whether this second writer is still
      actively scheduled — NOT verified, remains open** (not covered by the shipped fix below, which only touches
      `_solana_row_symbol`). **Scope of fix**: wire `_solana_row_symbol` (and/or `write_defi_rows`'s DeFi/POOL
      `instrument_id` construction generally) to glue in the same fee/tick-spacing discriminator the catalogue already
      computes. **✅ CODE SHIPPED 2026-07-24 `market-tick-data-service@0d83a8a9`**: new `_pool_fee_discriminator()`
      helper replicates the discriminator rule locally against the row's own already-captured `tick_spacing` (Orca, most
      specific) → `fee_rate_bps` (Orca+Raydium) → `pool_type` (Raydium Standard/Concentrated label) → falls back to the
      unchanged bare pair when none are present (Kamino/Meteora/Lifinity rows that don't carry any of these fields yet,
      matching pre-fix behavior exactly for those — no regression). 8 new unit tests (collision-fix + fallback-parity
      cases), `quality-gates.sh` green. **Full scope, not just the code fix (self-audit 2026-07-23 — these 3 were
      originally missing)**: (a) **migration for ALREADY-WRITTEN data — CHECKED 2026-07-23, CLEAN: zero production
      shards corrupted, because zero were ever written.** `uts-prod-mtds-collect-solana-defi-cron` is `PAUSED`
      (confirmed via
      `gcloud scheduler jobs describe uts-prod-mtds-collect-solana-defi-cron     --location=asia-northeast1`, part of
      the already-tracked, deliberate 4-collector pause since 2026-06-08 — Track 8 above) and a systematic GCS sample
      (every 3 days, 2026-06-05 through 2026-07-23, both ORCA and RAYDIUM, correctly-derived
      `pipeline_mode=batch_onchain_subgraph`) found ZERO `data_type=dex_pool_state` objects for either venue in that
      entire window — the collector has not produced a single canonical-shape shard since before the pause began, so
      there is nothing to re-split. **The pre-resume gate on "Resume the paused DeFi crons" (Track 8) for
      `collect-solana-defi` specifically is now CLEARED** — the symbol fix has landed, so resuming that one cron no
      longer risks day-one conflation; resuming is still an operator decision (a live-production cron restart), not
      something to flip unilaterally — (b) **manifest impact — STILL OPEN, not addressed by the code fix above** — once
      the symbol/`instrument_id` convention changes, existing `capture_status` cells keyed by the OLD bare-symbol form
      no longer match the new discriminated form; this is a de-facto key rename and needs the SAME
      backfill/re-registration treatment as any other instrument-id migration in this plan (see the POOL/LENDING
      fallback-elimination item above, step 5, for the pattern), not a silent drop — moot until the cron actually
      resumes and starts writing under the new convention, since (a) proved zero existing cells use the old form yet;
      (c) **naming-doc update — STILL OPEN** — `/codex/02-data/defi-canonical-naming-ssot.md` documents the current
      bare-symbol filename grammar and must be updated to describe the new `{token_a}-{token_b}-{discriminator}` form,
      or the SSOT drifts from the code the moment this lands. (repos: market-tick-data-service)
- **UTL `_derive_instrument_id.py` dispatch key `('defi','lending')`** — once the EVM retire lands, `lending` stops
  being produced for EVM; retarget/split the dispatch so Solana's `SOLANA_LENDING` grain (untouched by the retire, per
  above) keeps a live dispatch entry. Concrete implementation task, not a standing fork — resolves
  `defi_consolidated_closeout_2026_07_18.md`'s "MOOT unless..." CODE-section todo.

### Cross-AG — PREDICTION canonicalisation also needs work (own close-out)

> Relocated verbatim 2026-07-24 from the archived Contradiction-resolution section (one of its 2 still-open items) — see
> the "Contradiction resolution" pointer below for the other 73 (95%-closed) findings.

- [ ] [DATA] P1. **Prediction is a THIRD shard-atom grain** (operator 2026-07-18, per
      `availability-manifest-and-data-status.md:57-60`): the manifest grain is a **CQG bundle** keyed on
      `canonical_question_group` (`data_type=prediction_canonical_question_group`, e.g. `SPORTS_EPL_MATCH` /
      `BTC_UP_DOWN_DAILY`), with per-CID raw objects (Polymarket `condition_id` / Kalshi ticker) as row-level detail;
      `underlying` is DISPLAY-ONLY, not a key; IS side = `venue → dates` (no data_type axis,
      `VENUE_REFERENCE_DATA_CAPABILITIES={}`); MTDS drilldown is CQG-**above**-data_type
      (`data-status-drilldown-hierarchy.md:42`). The phantom reconciler **WIPES the CQG rows** because it mis-keys
      prediction on per-object `instrument_id` instead of the `(canonical_question_group, day)` bundle — a P0 the SSOT
      vindicates. **Prediction warrants its own consolidated close-out** (a 4th, alongside cefi/tradfi/defi); this row
      is the pointer so it isn't lost. (repos: market-tick-data-service, deployment-api)

### Open items recovered from the pre-2026-07-24 historical Progress Log's deferred-work tables

> The chronological Progress Log narrative was moved verbatim to the archive doc (pointer below); these 4 items were
> genuinely still-open (not "done"/duplicate-of-above) as of the last tick and are carried forward here rather than
> archived silently.

- [x] ✅ [DATA] P1. **Ship the `delete_migrated_defi_markers_2026_07_23.py` script — DONE (cited sha `952618d1` was
      stale/pre-rebase; actual shipped sha `market-tick-data-service@a65117eb`, confirmed ancestor of
      `origin/live-defi-rollout`).** The named blocker
      (`mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`) was worked around via the serial-pytest
      mitigation (`bc5d1490`, `PYTEST_WORKERS=1` — reduces but does not eliminate exposure per that issue doc's reopened
      findings) and the script landed. **Remaining: only the `--apply` run itself, [OPERATOR]-tagged at the parent plan
      (line 708) — prod-bucket delete, human-only hard stop, not an agent action.** The 12-liquidations-bundle question
      is ANSWERED (writer half): the daily-cron timestamp-glued-empty-marker defect across 6 handlers that produced them
      is root-caused + fixed this session (`market-tick-data-service@f2e3ad41`) — no FUTURE liquidations glued rows will
      be written. The 12 EXISTING glued rows already in the manifest from before the fix still need a targeted
      re-verify/reclassify pass — tracked at Track 1's line 712-equivalent item below, not a distinct gap. (repo:
      market-tick-data-service)
- [x] ✅ [DATA] P1. **Verify the fake-history relabel-forward migration to actual completion** (todo 3,
      `/plans/active/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`) — **VERIFIED
      COMPLETE 2026-07-24 ~12:09 UTC**: all 4 ON_DEMAND VMs (`d01to05v3`/`d06to09v3`/`d10to13v3`/`d14to17v3`) terminated
      cleanly, `run.log` ends `done. objects processed = N (apply=True)` + `exit_code=0` for each, sum = 241,281 exactly
      matching the measured source population (no shard under-ran). **Re-confirmed independently in this session** via a
      fresh `gcloud storage ls` count against the live `-prd-` bucket: `day=2026-05-04` = 14,104 ORCA + 119 RAYDIUM,
      `day=2026-05-05` = 14,099 ORCA + 113 RAYDIUM, sum = 28,435 distinct canonical `dex_pool_state` objects, exactly
      matching the issue doc's cited final count. Pending-delete audit report
      (`_index/audit/dex_pools_fake_history_pending_delete.parquet`) confirmed present in GCS for the later human
      delete-review step. (repo: market-tick-data-service)
- [ ] [DATA] P2. **File + fix the `staking_yields_handler.py` / `lst_rates_handler.py` gap found during the 2026-07-22
      C2–C12 scoping pass** — `staking_yields_handler.py` hardcodes the legacy `_DATA_TYPE="staking_yields"` and is
      registered in the CLI but has ZERO scheduled Cloud Scheduler jobs (appears dead in production); separately,
      `lst_rates_handler.py` writes to a non-hive, non-canonical path
      (`gs://{bucket}/lst_rates/date=.../lst_rates_{ts}.parquet`), bypassing `canonical_write.py`'s
      `asset_group=`/`pipeline_mode=` layout entirely — a genuinely separate gap from C2/C9, flagged but never filed as
      its own issue. (repo: market-tick-data-service)
- [ ] [BACKEND] P2. **Cherry-pick the unshipped `is_defi_force_include_pool` wiring from instruments-service
      `stash@{0}`** (diff-confirmed 2026-07-22 vs HEAD — NOT fully redundant with already-shipped work). The UAC-side
      predicate (`unified_api_contracts.registry.defi_major_assets.is_defi_force_include_pool`,
      `DEFI_FORCE_INCLUDE_POOLS`) exists and is exported but is called from NOWHERE in current instruments-service (0
      hits). Wire it into `filter_defi_instruments_by_relevance` (`orchestrator/defi.py`) + `_add_force_include`
      (`scripts/build_instrument_catalogue.py`) — this is the high-TVL Raydium pool force-include behavior R5 flagged
      (32 legacy-only pools incl. XMR/USDC $47M, BNB/USDC $18M). Discard the rest of the stash
      (venue-list/factory-registration/golden hunks are already superseded by current HEAD). Full evidence:
      `/plans/archive/issues/uac_is_defi_oracle_dex_adapter_drift_2026_07_20.md`. (repo: instruments-service)

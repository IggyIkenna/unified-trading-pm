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
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: "2026-07-24"
last_updated: "2026-08-02"
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
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_defi_2026_07_15.md,
    /plans/active/issues/defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/canonical_write.py,
    market-tick-data-service/market_tick_data_service/scripts/migrate_defi_batch_to_per_instrument.py,
  ]
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

> **na-eligibility-audit 2026-08-01**: KEEP-NA-STALE-ITEMS — re-read end to end (10 open items). 8 stay KEEP-NA valid
> (design/judgment calls on live-production canonicalization machinery, consistent with this doc's own history of
> reversed attempts). 2 items closed as stale (LENDING retire — decided WON'T-DO 2026-07-26; Combo cross-AG hand-off —
> shipped elsewhere), see inline notes below. No RECLASSIFY-eligible items found. Doc stays `assigned_vm: NA`.

## Per-instrument re-architecture (operator 2026-07-18 — SUPERSEDES the batch-model tracks; DeFi capture STOPPED)

> **🟡 In-flight refactor + capture halted (re-armed 2026-07-18).** All DeFi capture is STOPPED — GCP forward-poll VMs
> `defi-fwd-dex-pools-poll` + `defi-fwd-dex-swaps-poll` stopped and their schedulers
> `defi-fwd-{dex-pools,dex-swaps, oracle-prices}-prd` + `uts-prod-mtds-collect-{evm,solana}-defi-cron` PAUSED (they had
> respawned once on the old batch-writer — re-armed by pausing the schedulers first, so no further respawn); AWS both
> regions clear; **IS enum/catalogue/consolidator crons LEFT RUNNING** — IS remains the availability source. DeFi is
> being re-architected to shard-write ONE parquet per instrument (like cefi/tradfi), collapsing SSOT §1 pattern #4 →
> pattern #1. This is the target; the batch-model column/path framing in the tracks below is superseded. Grounded in
> code (workflow `wf_20749dad`).
> **Pre-authorized 2026-08-18**: once remaining todos here close, auto-RESUME the schedulers above (reconfirmed 3x).

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
- [~] [DATA] P0 (R3-run — **STALLED, confirmed DEAD 2026-08-02, was mis-stated "RUNNING"**). Dry-run recon validated +
  scoped `--apply` proven on real GCS (CHAINLINK oracle_prices → 22 canonical leaves + `_migrated_*`, 0 err). **FULL
  migration on SPOT VM `canonical-migration-defi-per-instrument-20260719-053435`** (in-region, chunked per-year,
  preemption-recovery loop `bd014y3c2` armed): **2020 ✓ (2,241→4,694), 2021 ✓ (30,513→607,867 instr, 18M rows, 0 err)**,
  2022 applying, 2023–2026 + `rebuild_defi_manifest` remain (~~8-12h). **INCOMPLETE — see R5**: it walks ONLY
  `raw_tick_data/by_date/` and MISSES (a) the gas_fees `{data_type}_{blk}_{blk}` block-range shape (discovery regex
  gap), (b) the legacy top-level prefixes entirely. **STALL CONFIRMED (slot-7 data_pipeline_failure escalation,
  2026-08-02, agt-0e35ed)**: this checkbox has read `[~] RUNNING, partial` unrevised since 2026-07-24/25, and
  `defi_oracle_prices_capture_stalled_since_2026_07_22.md` already flagged the VM as 6 days idle as of 2026-07-30
  without a re-check. Re-verified today —
  `gcloud compute instances list --filter="name~'canonical-migration-defi-per-instrument'"` and
  `gcloud compute operations list --filter="targetLink~'canonical-migration-defi-per-instrument'"` both return ZERO
  results (no running instance, no operation history at all — not just idle, the VM is gone). R3 has been dead for **9+
  days** (last confirmed activity 2026-07-24T07:26 UTC-7), stuck mid-way through 2022, years 2023-2026 +
  `rebuild_defi_manifest` never ran. **Downstream impact newly confirmed**: this is the reason
  `collect-{dex-pools,oracle-prices,evm-defi,solana-defi}` stay paused per Track 8's `gate_on_depends`, which is now the
  traced root cause of a CRITICAL `DP_CATALOG_NOT_RUNNING` (`DP-CATALOG-001`) page — the defi instrument catalogue's
  `CATALOGUE_SHRINK_BLOCKED` monotonic guard has rejected 3 consecutive rollup runs (2026-08-01×2, 2026-08-02×1) because
  ~~2800-3400 pool rows across 9 EVM DEX venues stopped appearing in `instrument_availability/ by_date/` — 807 of them
  were captured every day through 2026-07-30 then went silent, consistent with `dex-pools` being one of the 4
  gated-paused collectors. Full evidence + decision request in
  `/plans/archive/issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`. **This todo needs an owner to either
  relaunch the SPOT VM from its 2022 checkpoint (if resumable) or restart R3 from scratch for 2022-2026 — it will not
  un-stall on its own.** (repo: market-tick-data-service) **RELAUNCHED 2026-08-06 (slot-6) per the `[OPERATOR] P0`
  ruling in `/plans/archive/issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md` (option A):**
  `canonical-migration-defi-per-instrument-20260806-175529` (asia-northeast1-c, e2-standard-8, SPOT),
  `MIGRATION_YEARS="2022 2023 2024 2025 2026"`, tarball-pinned to current LDR code. **The per-instrument migration
  corpus is ALREADY migrated** — every year chunk fast-skips `cells=0` (`_migrated_` markers + canonical hive shape
  confirmed under 2023-2026 sample days; the "stuck mid-2022 / 2023-2026 never ran" framing here is STALE, superseded by
  prior `defi-pi-range`/rebuild waves). The VM runs the chained `rebuild_defi_manifest` (2020-2026) after the year loop
  — the remaining gate piece for Track-8 collector resume. Run.log:
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-per-instrument-20260806-175529/run.log`.
  **`-175529` OOM'd 2026-08-06T18:30:37Z (DP-VM-003, slot-7 data_pipeline_failure escalation agt-ef3dd8) — CONFIRMED
  REPEAT of the EARLIER `-165240` failure (started 16:56, died 17:30, same exit_code=125), not a one-off.** Registry
  entries for both (`deployments/archive/2026-08-06/{9039a28e-...,ac206578-...}.json`) show byte-identical failure
  shape: years 2022/2023/2024 fast-skip `cells=0` cleanly, then the year-2025 chunk's discovery listing hangs — per-year
  `discovered 0 bundled batch file(s) in scope (list=Xs)` time climbs monotonically each chunk (68s→123s→186s for
  `-175529`; 68s→123s→186s for `-165240` too), `mem_pct` climbs to 99.3% (`mem_slope=+9.12`, still rising) at the last
  heartbeat before both VMs vanish (`gcloud compute operations list` shows only insert+delete, NO
  `compute.instances.preempted` — this is an OOM self-destruct via `--instance-termination-action=DELETE`, not a SPOT
  preemption). **Root cause: the per-year loop is now pure waste.** Every chunk already fast-skips (corpus confirmed
  migrated, see the `-175529` entry above) yet still pays a FULL `raw_tick_data/by_date/day=*` listing for the whole
  year to confirm that — and since the migration itself exploded file-count (few bundled batches → many per-instrument
  leaves), that listing cost has grown large enough by 2025 to OOM an e2-standard-8 before the loop ever reaches the
  chained `rebuild_defi_manifest` step (the actual remaining piece). Runbook `RB-INFRA-RELAUNCH`'s ≤2/day-per-prefix
  bound is now hit for `canonical-migration-defi-per-instrument` (2 identical failures today) — per its own "re-fails
  the SAME way twice → STOP relaunching, fix root cause" clause, did NOT launch a third `defi-per-instrument` attempt
  (would OOM the same way at 2025 again). **Instead launched `canonical-migration-defi-rebuild-20260806-223130`**
  (asia-northeast1-c, e2-standard-8, SPOT) via the separate, already-registered `defi-rebuild` launcher category —
  `rebuild_defi_manifest` ALONE, `--chunk-days 90` (own PROGRESS-checkpointed resume, no year-loop discovery at all) —
  this is the exact remaining piece of the already-operator-approved option-A scope ("...`rebuild_defi_manifest` from
  scratch"), just invoked directly instead of behind the now-provably-pointless migrate loop. Verified STARTED (RUNNING
  at launch + 45s). Run.log:
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-rebuild-20260806-223130/run.log`.
  **Note**: the CRITICAL `DP-CATALOG-001` page this R3 relaunch chain was driving toward is independently ALREADY
  RESOLVED since 2026-08-03 (R2c monotonicity relaxation) — this rebuild is real remaining work (Track-8 collector
  resume gate) but no longer fire-drill urgent. Follow-up needed: `migrate_defi_batch_to_per_instrument.py`'s
  `discover_bundled()` should stop re-listing years that already have a `[[VM_PROGRESS]] last_completed_date=` monotonic
  checkpoint recorded, so a future `defi-per-instrument` re-run (e.g. for a NEW year added to the corpus) doesn't pay
  this same growing-listing-to-OOM cost on already-done years — not fixed here (would need a code change + QG cycle, out
  of scope for a one-shot infra-relaunch escalation; tracked as a new todo below). **`-223130` was SPOT-preempted
  (confirmed via `ag_closeout_audit` live investigation 2026-08-10T~~01:00Z,
  `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` Finding 5) — successor
  `canonical-migration-defi-rebuild-20260809-163511` launched (RUNNING, resumed from `last_completed_date=2024-09-05`).
  That successor has now ALSO reached a terminal state (confirmed live 2026-08-10T~~05:15Z, this same audit's follow-up
  check): NOT a SPOT preemption this time (`gcloud logging read` for `compute.instances.preempted` on this VM returns
  ZERO results) — the worker process itself was killed (`received signal 15` at 03:57:22Z, exited `rc=137`) immediately
  after a run of repeated
  `Connection pool is full, discarding connection: storage.googleapis.com. Connection pool size: 10` warnings in
  run.log; `DEPLOYMENT_FAILED exit_code=137` was recorded, then the VM self-deleted per its own
  `VM_SHUTDOWN_ON_COMPLETION=true` bootstrap logic (`v1.compute.instances.delete` issued by `uts-prd-sa`, i.e.
  self-inflicted teardown, not GCE preemption). Progress DID advance — `PROGRESS.json` shows
  `last_completed_date=2025-06-02` (up from `2024-09-05`), so real work happened — but this is still far short of the
  `--end-date 2026-12-31` target, and as of this check NO successor VM is running for the
  `canonical-migration-defi- rebuild` prefix
  (`gcloud compute instances list --filter="name~canonical-migration-defi-rebuild"` returns empty). **This is the
  prefix's 2nd terminal-non-completion in a row, and the 2nd one shares the exact failure SIGNATURE (no
  `compute.instances.preempted` event, self-delete via `VM_SHUTDOWN_ON_COMPLETION`, resource-pressure symptoms building
  before the kill) as the SIBLING `defi-per-instrument` prefix's 2026-08-06 OOM pair two paragraphs above** — the same
  shape RB-INFRA-RELAUNCH's "re-fails the SAME way twice → STOP relaunching, fix root cause" clause was written for. Per
  that clause, AND per this doc's own 2026-08-02 Progress Log ruling that relaunching R3 is
  operator/main-escalation-gated, this audit did **NOT** attempt a 3rd relaunch — flagging for root-cause triage (likely
  `storage.googleapis.com` connection-pool sizing under `rebuild_defi_manifest --workers 24`, not classic OOM) before
  any further relaunch. Evidence:
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration- defi-rebuild-20260809-163511/{run.log,PROGRESS.json}`;
  `gcloud logging read` audit trail (insert 2026-08-09T15:40-41Z, delete 2026-08-10T03:57-58Z by `uts-prd-sa`, zero
  `preempted` events in between). **Addendum, same check**: the consolidator's own lock DID self-heal correctly — the
  dead VM's orphaned `_index/consolidator.lock` (blob content confirms `started_at` last belonged to the VM's own
  holder) went stale and was reclaimed by a fresh, legitimate per-minute cron cycle at
  `started_at= 2026-08-10T05:12:56Z` (`instance=1-bd80c268`), which is presumably still mid-merge as of this check
  (defi's real merges run 18-30+ min, so expect completion roughly 05:31-05:43Z) — this is the SAME self-healing path
  `manifest_consolidator.py`'s lock-orphan-fix comments describe, working as designed. **Not** a second stuck-lock
  problem stacked on top of the VM failure — flagging this explicitly since a shallower check (log line only, not the
  lock blob's own `started_at`) could easily misread the repeating "fresh lock present" log lines as a stale-lock
  livelock recurrence. Net effect for
  `defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_ funding_gap_2026_08_08.md` item 2 /
  `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md` item 2 (both gated on "consolidator
  catches up"): likely to clear on its own within the hour, independent of the rebuild VM's own unresolved relaunch
  question above.
- **2026-08-10T~09:31Z: `-163511`'s OOM root-caused (an unbounded cross-chunk memory accumulator, not the
  connection-pool guess above), fixed (`market-tick-data-service@483eb895`), deployment content-verified, and relaunched
  under RB-INFRA-RELAUNCH's root-cause-diagnosed carve-out — full diagnosis, fix, carve-out reasoning, and the required
  operator page: `/plans/archive/2026_08/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md`.**
- **[DATA] P2. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** NEW 2026-08-06 (DP-VM-003,
  slot-7 data_pipeline_failure escalation agt-ef3dd8). Skip `migrate_defi_batch_to_per_instrument.py`'s per-year
  `discover_bundled()` full listing for years that already have a recorded `[[VM_PROGRESS]] last_completed_date=`
  monotonic checkpoint (or an equivalent already-migrated marker) instead of re-walking the whole
  `raw_tick_data/by_date/day=*` tree for that year every single relaunch. Two consecutive
  `canonical-migration-defi-per-instrument` VMs (`-165240`, `-175529`) OOM'd 2026-08-06 on this exact waste — per-year
  listing time climbed 68s→123s→186s (2022→2024) then crossed the OOM threshold on 2025, even though every year
  fast-skips `cells=0` (corpus already migrated). Without this fix, any future `defi-per-instrument` re-run (new year
  added, or re-verifying scope) pays the same growing, eventually-fatal listing cost. (repo: market-tick-data-service)
- **2026-08-13 (finalize reconciliation, `defi_pool_rate_indices_dex_pool_fees_retirement_finalize_2026_08_10.md` todo
  1): post-rebuild retirement + rollup + panel re-check COMPLETE — closing note, checkbox unchanged.** Once the rebuild
  VM chain reached genuine terminal SUCCESS (`canonical-migration-defi-rebuild-20260810-204358`, confirmed in the R3-run
  entry above), the downstream `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md` plan (all 9 todos done,
  2026-08-12) retired the legacy POOL(uppercase)/`rate_indices`/`dex_pool_fees` `captured` manifest rows this rebuild
  had left behind (manifest-column-only artifacts / real-but-content-redundant rows, per that plan's own
  content-verification), then triggered a fresh honest-coverage rollup and re-checked the Distinct Values panel.
  Evidence (commits + counts, INDEPENDENTLY RE-VERIFIED live 2026-08-13 against the current 158,267,760-row consolidated
  index): POOL uppercase — `market-tick-data-service@5e456d0d`, 0 legacy POOL keys remain; `rate_indices` —
  `market-tick-data-service@bf712ddb`, 0 legacy keys remain; `dex_pool_fees` — `market-tick-data-service@9f5868e5`, 0
  remaining captured rows; rollup — `instruments-service@4bb2164e`, fresh `coverage.json`
  `generated_at=2026-08-12T22:00:38Z` (confirmed still latest as of this check). Full detail:
  `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s Todos section (this same retirement item, now
  flipped `[x]`). **This closes the retirement plan's aftermath of the R3 rebuild, not R3 itself** — the R3-run checkbox
  above stays `[~]`; the still-open, gating piece is the per-instrument historical-migration VM chain (years 2022-2026
  canon reconciliation), which this retirement cleanup did not touch.

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
      `/plans/archive/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (archived 2026-08-08,
      delete complete) with full evidence + suggested next steps (parse the legacy path + re-derive canonical path from
      the parquet's own `instrument_key` column, fold-not-delete since content is real). **Remaining**: scale
      measurement + a targeted migration script — tracked in that issue doc, not re-duplicated here. (repo:
      market-tick-data-service)

- [x] ✅ [DATA] P1. **Divergence RCA — DONE 2026-07-24 (autonomous session, sub-agent investigation).** Verdict: a real,
      systemic BUG (not a deliberate threshold), now point-patched but NOT generally fixed. Root cause: the DeFi
      catalogue build's `filter_defi_instruments_by_relevance()`
      (`instruments-service/instruments_service/engine/orchestrator/defi.py:431-489`) requires BOTH legs of a DEX pool
      to be in the hardcoded `DEFI_MAJOR_ASSET_SYMBOLS` whitelist
      (`unified-api-contracts/unified_api_contracts/registry/defi_major_assets.py:17-44`) — an asset-relevance filter,
      not a TVL filter. It silently dropped 32 real, liquid Raydium pools pairing a major asset against a non-major one
      (XMR/BNB/LTC/ZEC/XRP/TRX/meme tokens/exotic stables). The legacy 2026-04-14 capture predates this filter
      (introduced ~2026-07-09) so it has all 98 pools; the 2026-07-13 canon rebuild goes through the filtered catalogue
      and gets only 66. **Blast radius is systemic** — this filter runs on every catalogue build, dropping the same
      class of pool on every day, every DEX venue under `DEX_VENUE_KEYWORDS`, not just Raydium on that one day. **Fix
      status**: `unified-api-contracts@3f79489f` (2026-07-20) added a `DEFI_FORCE_INCLUDE_POOLS` allowlist (the 32
      addresses, top-32-by-TVL from the legacy snapshot) but it was DEAD CODE — nothing called it — until
      `instruments-service@4e97a82e` (2026-07-24, today) actually wired it into the filter, a 4-day window where the
      "fix" existed but had zero effect. **Net**: canon `dex_pool_state` is trustworthy for these 32 specific addresses
      (protection is address-based, retroactive to any re-run). It is **NOT** generally trustworthy for other
      raydium/DEX days — any OTHER high-TVL pool pairing a major asset with a non-major one will still be silently
      dropped unless manually added to the allowlist; this is a point-fix, not a general TVL override. (repo:
      instruments-service, unified-api-contracts)
- [x] ✅ [DATA] P2. **WON'T-DO — RULED 2026-08-16 (na-eligibility-audit follow-up Q&A round 7, operator ruling — see
      this doc's own 2026-08-16 entry in `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s
      Progress Log below). Flipped 2026-08-16 (plan_reconciler, dispatch agt-1a88e0) — same-day ruling never
      propagated to this checkbox.** No TVL-based fallback: `DEFI_FORCE_INCLUDE_POOLS` stays the sole, curated
      gate; anything not in the allowlist stays excluded (enforce strictly, don't silently admit via a threshold). No
      code change needed beyond what's already wired (`instruments-service@4e97a82e`). Original text: **NEW 2026-07-24
      — the DEX asset-relevance filter (`filter_defi_instruments_by_relevance`) needs a real TVL-based fallback, not a
      hand-maintained allowlist**, per the Divergence RCA above: the current fix only covers the 32 addresses known at
      ONE 2026-07-20 snapshot; any new high-TVL pool pairing a major/non-major asset going forward silently drops
      again until someone notices and manually extends `DEFI_FORCE_INCLUDE_POOLS`. (repo: instruments-service,
      unified-api-contracts)
- **[BACKEND] P0. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`** (the remaining
  deploy-check + re-enum/re-rollup sub-scope)**. Catalogue-venue gap — ROOT CAUSE FIXED + SHIPPED
  (`unified-api-contracts@f7314dc2`, 9/9 acceptance: 7 new venues + cbETH/wBETH ACCEPT, COINBASE-SPOT/BINANCE-FUTURES
  stay CEFI; whole defi universe validates, was 26 rejected). SOLANA-NATIVE kept (documented canonical spelling;
  validator now parses the TRAILING chain segment). DEPLOY-GATED re-enum+re-rollup remains.** NOT
  deploy-lag/creds/silent-[] (deployed image HAS 89 venues + adapters DO emit). The 26 new venues are REJECTED at UAC
  `validate_instrument_records` — **R2 wired them into the FETCH list (`_DEFI_VENUES`) but NOT the VALIDATION allowlist
  (`instrument_validation.py::_DEFI_VENUE_PREFIXES` line 22)** → "unknown venue 'RENZO-ETHEREUM'" → they never reach
  `by_date/`, EU-seeded as `expected_unattempted`. There's an in-code comment about this EXACT bug recurring
  (VENUS/RADIANT 2026-07-12). Fix = +15 collision-free prefixes (unblocks 22/26) + chain-aware COINBASE/BINANCE
  disambiguation for cbETH/wBETH (3 more; must NOT misclassify COINBASE-SPOT/BINANCE-FUTURES as defi) + IS
  `SOLANA-NATIVE-SOLANA` tag fix. **DEPLOY-GATED**: after ship → LDR→main → IS-image rebuild → then `is-daily-enum-defi`
  re-enum + `lifecycle-catalogue-full-defi` re-rollup + verify (a later tick). Original catalogue snapshotted
  `prod/_snapshots/catalog.pre-rollup.20260719T040600Z.parquet`. (repo: unified-api-contracts, instruments-service)

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
  `plans/archive/issues/defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md`,
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
> `plans/archive/2026_07/defi_lending_writer_retire_prerequisite_2026_07_20.md` reports its acceptance criteria 1-8
> green with cited evidence and flips ITS OWN todo 14 from BLOCKED to CLEARED. The first attempt at this retire was
> REVERSED because the migration started before the MTDS lending writers were fixed — read that plan's "What actually
> broke" section before touching this todo. As of 2026-07-21 that plan's todos 2-5/9/13 (writer-collapse +
> shard-atom-desync fixes + pinning tests + doc corrections) are code-complete and individually verified
> (ruff/basedpyright clean, full MTDS suite green apart from 2 unrelated pre-existing cross-repo test-baseline
> regressions — see that plan's Progress Log) but NOT YET COMMITTED (blocked on those unrelated regressions clearing the
> shared tree's `quality-gates.sh`); todos 8/10/11 (the actual UAC+MTDS+UTL atomic retire + its runtime proof) are NOT
> started. The gate remains BLOCKED. Do not start this migration until that plan says CLEARED. **[na-eligibility-audit
> 2026-08-01: superseded — the gated migration below was ruled WON'T-DO permanently, 2026-07-26 (see the closed
> checkbox), not cleared to proceed. This banner is historical context only.]**

- [x] ⛔ [DATA] P0. **WON'T-DO (session-3, 2026-07-26, operator present) — closed, not deferred.** Was: **Retire legacy
      `LENDING` → A_TOKEN/DEBT_TOKEN.** **Builder-bake DONE `instruments-service@1af1be34`** (FIX 2, runtime-proven):
      the split is now INTRINSIC to `build_instrument_catalogue.py` row-construction — the canonical_id's
      `VENUE:TYPE:SYMBOL` segment is AUTHORITATIVE over a stale `LENDING` column for the A_TOKEN/DEBT_TOKEN/SPOT_ASSET
      family, so a `--mode full` rebuild can't re-stamp LENDING (kills the 2026-07-14 durability landmine). Verify
      caveat (non-blocking): a dataless-tail row mis-stamped by a PRE-fix rebuild survives verbatim through
      `_merge_incremental(close_absent=False)` until it reappears in by_date — **fully closed by the remaining half
      below.** Was REMAINING (Wave D, [DATA]): migrate the ~16.7M legacy `lending` rows to the split (code done for 9
      EVM protocols) on real infra. (repos: instruments-service) **na-eligibility-audit 2026-08-01: CLOSED — not
      gated-and-pending, actually decided against.**
      `plans/archive/2026_07/defi_lending_writer_retire_prerequisite_2026_07_20.md` (status: complete): "Session-3
      (2026-07-26, operator present) decision: the physical A_TOKEN/DEBT_TOKEN retire (todos 8/10/11/14) is WON'T-DO,
      permanently — after two reversals, a read-side resolver function (todo 15) delivers the same canonical-instrument-
      id → rate lookup without the GCS rewrite / manifest re-key / IS re-seed the flip required." Todo 15 shipped
      `unified-api-contracts@1d01a911` (confirmed ancestor of `origin/live-defi-rollout`).
- [ ] [DATA] P0. **Residual canon walk C2–C12** (single-walk discipline — reuse the existing worklist, no NEW
      whole-corpus walk): C2 data_type alias dedup (`dex_swaps`→`dex_pool_swaps`, `dex_pools`→`dex_pool_state`,
      `lending-indices`→`lending_indices`, `staking_yields`→`lst_rates`); C3 `VENUE-CHAIN`→flat venue + `chain`; C4
      v4–v8→v9; C9 object paths still carrying `category=`/no `pipeline_mode=`; C11 phantom walk; C12 `{VENUE}_V{N}`
      underscore canonicalisation (`TRADER_JOE_V2`/`VELODROME_V2`/`AERODROME_V3`). (repos: market-tick-data-service,
      instruments-service)
- [x] ✅ [DATA] P0. **Manifest instrument_type case + venue-spelling unify — RESOLVED 2026-07-24 (autonomous session,
      fresh live census, no migration needed for either half).** ~~CASE DIRECTION FURTHER REFINED 2026-07-24
      (operator)~~ — the per-`instrument_type` census this todo called for (never previously run — the 2026-07-21 audit
      only had the UPPERCASE-side counts) was run live against a fresh post-consolidation read of
      `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (24,123,783 rows,
      `latest.json.last_run_at=2026-07-24T19:46:31Z`, DuckDB out-of-core query — never a full pandas load, given the
      host's tight memory headroom; the 3 outstanding `_index/per_vm/*.parquet` shards were independently checked too,
      same result). **Result: EVERY one of the 11 live `instrument_type` values is already 100% one casing — lowercase —
      with ZERO uppercase rows anywhere in the manifest**: `pool` 15,762,504 · `solana_amm_pool` 7,508,473 · `lending`
      396,009 · `perpetual` 204,279 · `spot_asset` 132,781 · `lst` 71,493 · `a_token` 29,835 · `yield_bearing` 7,311 ·
      `solana_vault` 1,026 · `staking` 669 · `solana_lending` 103 (+9,300 NULL/blank, a separate,
      much-smaller-than-the-plan's-cited-4.49M residual — out of this todo's casing/venue scope, tracked under the
      existing Wave-D id/grain-resolution item, not duplicated here). Per the least-migration-cost rule
      (`/plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`), lowercase is trivially
      each value's target since it is the ONLY casing present (no near-50/50 split anywhere — the HARD-STOP condition
      for an ambiguous split never fires). **This also reconciles the stale-SSOT chain found in the same pass**: an
      intermediate same-day agent note (`4f81d0139`, 19:11 UTC) had inferred from `_comparison_set()`'s case-INSENSITIVE
      vocabulary-matching grain rule that defi is permanently lowercase and out of scope for any casing work; the
      operator's own later directive (`adb28421d`, 19:31 UTC) corrected that to per-value least-migration-cost — and
      this census shows the two land on the identical PRACTICAL outcome (lowercase, unanimously) via different
      reasoning, so there is no remaining tension. Corrected the resulting stale banners in
      `/codex/02-data/reconciliation-finding-taxonomy.md` §5.1, `canonical-cutover-register.md` §3c/§7, and
      `cross-asset-canonical-target-ssot.md` §7 (dated correction banners added, nothing deleted, per this corpus's own
      convention). **Venue-spelling half — also resolved, ALSO no-op, for a different reason: the named collapse targets
      are either already-zero or were never drift.** Live check of the same index: `AAVEV3`/`COMPOUND`
      (bare)/`YEARNV3`/`KAMINO_LENDING` — **0 rows for all four**, already fully migrated or never present in that form.
      The remaining two named pairs are **NOT spelling drift** — they are genuinely distinct, DELIBERATELY registered
      DeFi venues, confirmed by both the UAC registry and the live data's own `data_type`/date fingerprint: **`AAVE`
      (5,568 rows) is 100% `data_type=oracle_prices`** (2023-01-27→2026-07-22), matching the `AAVE-ETHEREUM`
      on-chain-oracle venue (`AaveOracle.getAssetPrice()`, `governance_events`+`oracle_prices` capabilities) registered
      in `unified-api-contracts/unified_api_contracts/registry/defi_venues.py` (phase flipped pipeline→live 2026-07-21
      per `lst_rate_honest_coverage_2026_07_21.md` Phase 1) + `defi_venue_capabilities.py:252` — genuinely distinct from
      `AAVE_V3` (the lending-pool venue); **`MORPHOVAULTS` (1,614 rows) is 100% `data_type=vault_share_price`**
      (2024-01-04→2026-07-23, exactly matching its registered `coverage_start` in `defi_venue_capabilities.py:276`), the
      MetaMorpho ERC-4626 vault product — genuinely distinct from `MORPHO` (core Morpho Blue lending markets, a separate
      5-chain venue family). **Collapsing either into its "sibling" would have been a data-correctness REGRESSION**
      (conflating two real, differently-typed DeFi products under one venue label), not a fix — the plan's collapse
      targets were accurate as of the 2026-05-25/2026-07-20 audit snapshots they trace to
      (`data_quality_backfill_status_audit_instructions.md` DQ-04, `data_pipeline_reconciliation_defi_2026_07_20.md`)
      but were superseded by the 2026-07-21 deliberate re-registration, which those older docs predate. No script was
      written or run against the live manifest — a real, evidence-checked no-op is not the same as skipping the work,
      and forcing a write here would have been the regression. **Done-when, verified**: every DeFi `instrument_type`
      value is internally 100% one casing (TRUE, 0 exceptions, live-verified) — the deployment-ui data-status Distinct
      Values panel already reflects 0 case-duplicate `instrument_type` entries for defi by construction
      (`deployment-api/deployment_api/routes/data_status/_distinct_values.py:108-113`'s `_comparison_set()` compares
      defi instrument_type case-insensitively; with the underlying data now PROVEN unanimous rather than merely
      tolerated, that comparison has nothing left to fold). (repos: market-tick-data-service, unified-trading-library —
      no code changes needed in either; the fix was verifying the premise, not writing a migration)
- [x] ✅ [DATA] P1. **perp_funding → `derivative_ticker`** as the canonical raw-funding home for ALL perps (drop the
      Drift-only 24h/7d/30d window aggregates). Ratify enum-member DeFi grains (`lst`/`staking`/`yield_bearing`) as
      canonical (case-fold only, already `InstrumentType` members). (repos: market-tick-data-service,
      unified-api-contracts) **RATIFIED (operator, 2026-08-08)**: yes to both — `derivative_ticker` is the single
      canonical raw-funding home for all DeFi perps, and `lst`/`staking`/`yield_bearing` are ratified canonical
      `InstrumentType` grains. Filed the implementation as a new `[SCRIPT] P1` todo below.
- **[SCRIPT] P1. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** Implement the
  derivative_ticker/InstrumentType ratification (per the 2026-08-08 ruling above): drop the Drift-only 24h/7d/30d window
  aggregates in favor of `derivative_ticker` as the sole raw-funding capture path for all DeFi perps; confirm
  `lst`/`staking`/`yield_bearing` carry no remaining case-variant/alias drift anywhere they're consumed (repos:
  market-tick-data-service, unified-api-contracts).
- [x] ✅ [DECISION] P2. **Bare `SUSHISWAP`/`UNISWAP` version (199,397→206,107 rows, measured 2026-07-21) — decided +
      infra shipped `instruments-service@3ffd1adf`.** Operator ruling applied (recorded in this doc,
      `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md` § "Operator decisions applied
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
- [x] ✅ [DATA] P2. **NEW 2026-07-21 — actually start capturing factory addresses so the shipped resolver above has
      something to resolve** (today it resolves 0 of 206,107 bare SUSHISWAP/UNISWAP rows — see
      `issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`). Two options, not yet decided between: (a)
      augment the 4 subgraph query cascades in `instruments-service`'s `uniswap_v3.py` to request a `factory` field —
      needs a live-schema probe per fork (native/Algebra/SushiSwap-pairs/Messari) before landing, a wrong field name
      hard-errors the query; (b) on-chain RPC `factory()` lookup keyed off the already-captured `pool_address` (needs an
      RPC provider + enumerating the unique pool_address set from the raw MTDS parquet, not the manifest). Also register
      the missing `SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM` (or whichever the capture work resolves to) canonical
      venues in UAC `ALL_DEFI_VENUES` — currently only the bare `SUSHISWAP-ARBITRUM` is registered, so even a
      correctly-resolved factory address cannot be written back without this. (repos: instruments-service,
      unified-api-contracts, market-tick-data-service) **RULED (operator, 2026-08-08)**: option (b), on-chain RPC
      `factory()` lookup — bounded, no live-schema-probe risk. Operator explicitly extended the scope beyond just
      capturing factory addresses on the go-forward batch: **the 206,107-row historical residual must also be migrated**
      — GCS object filenames/paths and manifest rows rewritten to the resolved canonical venue name + chain, with the
      non-canonical bare `SUSHISWAP`/`UNISWAP` originals purged once the canonical twins are verified. This is the same
      avoid-two-sources-of-truth standard as the sibling SUSHISWAP-alias ruling in
      `defi_venue_lst_rates_residual_2026_07_24.md` — not a forward-only labeling fix.
- **[SCRIPT] P1. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`.** Wire RPC `factory()`
  lookup for the 206,107 bare SUSHISWAP/UNISWAP rows, register the missing Sushi-Arbitrum UAC venues, then migrate +
  purge the historical objects/manifest to canonical venue+chain naming** (per the 2026-08-08 ruling above): (1)
  enumerate the unique `pool_address` set from the raw MTDS parquet for these 206,107 rows, (2) RPC `factory()` lookup
  per pool (needs an RPC provider — build the adapter scaffold now regardless of provider-credential status per the
  External-Data-Always-Available rule), (3) resolve each pool to its canonical venue via the already-shipped
  factory-address→version map (`_dex_factory_registry.py`), (4) register `SUSHISWAP_V2-ARBITRUM`/`SUSHISWAP_V3-ARBITRUM`
  in UAC `ALL_DEFI_VENUES` (currently only bare `SUSHISWAP-ARBITRUM` exists), (5) rewrite/migrate the historical GCS
  objects + manifest rows to the resolved canonical venue+chain path, (6) purge the non-canonical originals once
  canonical twins are verified present — a fresh `gcs_bucket_soft_delete_retention_seconds()` check qualifies this for
  agent-execution per `gcs-and-manifest-delete-safety-protocol.md` §3a, same pattern as the sibling
  composite-venue-objects migration in this epic. **No backfill needed** — rename/relabel of already-captured data.
- [x] ✅ [DATA] P2. **RESOLVED 2026-07-24 (autonomous session, sub-agent investigation) — the "2,936 rows = cefi
      leakage" premise was WRONG for 99.998% of the population; genuine leakage is 4 rows, not 2,936, and needs a writer
      fix, not a manifest cleanup.** Fresh live count (24,209,852-row manifest): `HYPERLIQUID`=204,286, `KALSHI_PERP`=2,
      `POLYMARKET_PERP`=2. **HYPERLIQUID is NOT a bug — do not touch.** All 204,286 rows are
      `data_type∈{perp_daily_ctx,perp_mark_price,perp_funding}`, `instrument_type=perpetual`, `capture_status=captured`
      (2023-05-12→2026-06-09) — this is the deliberate, operator-locked (2026-06-01) canonical wire value for the
      Hyperliquid L1 chain (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/defi.py`:
      `CHAIN_WIRE_VALUE_OVERRIDES = {ChainKind.HYPERLIQUID_L1: "HYPERLIQUID"}`), matching
      `onchain_perp_batch_handler.py`'s documented DUAL classification (CLOB/trades → cefi; chain-level
      funding/mark-price context → defi with `chain=HYPERLIQUID`). Removing/renaming it would be actively harmful — the
      same mistake class as the AAVE/MORPHOVAULTS venue-collapse finding earlier in this plan.
      **KALSHI_PERP/POLYMARKET_PERP (4 rows total) IS a genuine, live, ongoing bug**:
      `market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_kalshi_polymarket.py:317-320` calls
      the DeFi-only `write_defi_rows(venue="KALSHI_PERP", chain="KALSHI_PERP", ...)` for two venues UAC's own registry
      classifies as CeFi (`unified-api-contracts/unified_api_contracts/registry/venue_constants.py:372-373`,
      "CFTC-regulated crypto perps") — unlike Hyperliquid, these have no underlying blockchain, so there's no legitimate
      defi bucket for them; this is copy-paste leakage from the Hyperliquid pattern, not a naming quirk. Population is
      tiny (4/24.2M) but growing ~1-2 rows/day (an active 2026-07-22-started daily cron). **Deliberately NOT
      manifest-cleaned this session**: removing rows needs the in-place CAS-REPLACE path (additive-shard can't delete),
      and the writer bug is still live — a manifest-only removal today resurrects tomorrow (the exact durability trap
      `canonicalize_prediction_manifest_2026_07_18.py`'s FINDING 2 documents). Correct fix is a writer change (route
      these 2 venues through a cefi-classified write path, mirroring `onchain_perp_batch_handler.py`'s own
      explicit-`asset_group='cefi'` `ManifestWriter` precedent) — see the new todo below. Also noted, NOT yet filed:
      `source` is also wrongly stamped `"hyperliquid"` for both KALSHI_PERP/POLYMARKET_PERP rows (should be
      venue-derived), same writer, same follow-up. (repo: market-tick-data-service)
- [x] [BACKEND] P2. **NEW 2026-07-24 — fix `_perp_funding_kalshi_polymarket.py`'s asset_group/chain/source routing for
      KALSHI_PERP/POLYMARKET_PERP** (see the resolved item above for full root cause): route these 2 venues through a
      cefi-classified write path instead of the DeFi-only `write_defi_rows`, fix the `source` mislabel (currently
      hardcoded `"hyperliquid"` for both), then run the (by-then-frozen, still-tiny) manifest cleanup of the stale
      KALSHI_PERP/POLYMARKET_PERP rows as part of the SAME follow-up once the writer lands — never before, or the
      still-live bug just resurrects them. (repo: market-tick-data-service) — **DONE 2026-07-30**
      (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see defi_satellite_ao_dispatch_batch1_2026_07_25.md
      todo 10 for full evidence: both venues now route through `_write_cefi_perp_funding_rows()` (cefi-classified,
      `asset_group="cefi"`); `source` now explicitly `_source_for_protocol(protocol)` on every manifest call (was blank,
      auto-stamping "hyperliquid"). Manifest cleanup executed and verified against prod:
      `scripts/remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py` removed the 8 pre-existing stale rows
      (26,540,325 → 26,540,317), zero remaining KALSHI_PERP/POLYMARKET_PERP rows confirmed post-write.
      `market-tick-data-service@2aa23de5` (writer fix), `market-tick-data-service@6998ea4c` (cleanup script's final
      streaming-rewrite).
- [x] ✅ [BACKEND] P2. **Combo cross-AG hand-off (leg-aware signed-weight spec).** Extend the 1–4-leg cap + shared
      `build_leg()` path to the DERIBIT-COMBO builders (`cefi/deribit_combo_adapter.py`, `tardis/combos.py`) —
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` open P2. DeFi has no combos; this rides here
      only because the DERIBIT-COMBO fix is cefi-side and passed to `cefi_consolidated_closeout_2026_07_18.md`.
      **na-eligibility-audit 2026-08-01: CLOSED — done elsewhere.**
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` line ~167: "DONE 2026-07-27 (slot-8,
      data_engineering)... Extend the 1-4 leg hard cap + logged-drop behavior to Deribit's existing combo builders
      (cefi/deribit_combo_adapter.py, cefi/tardis/combos.py)... Evidence: instruments-service@9416be7d." Confirmed
      ancestor of `origin/live-defi-rollout`.
- **[BACKEND] P0. EXTRACTED 2026-08-09 → `defi_satellite_ao_dispatch_batch11_2026_08_09.md`** (the sole remaining
  sub-scope — re-ship the already-coded+tested (2)/(4) diff; sub-items (1)/(3)/(5) below are already shipped)**. NEW
  2026-07-21 (operator ruling, recorded in this doc,
  `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md` § "Operator decisions applied (2026-07-21…") —
  eliminate the address/UUID fallback in `canonical_instrument_id` for POOL + LENDING; resolve token symbols for real,
  don't fall back.** Operator: "it needs to be fully canonical no fallback and migrated." Does NOT touch the two-id
  model or the machine `instrument_id` (`pool_address.lower()` stays — 2026-07-18 ruling unchanged,
  `engine/defi_catalog_reader` still joins on it). Scope is narrower than it first looks:
  `DefiPoolIdentity.glued_pair_id`
  (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/defi.py:333-361`) only falls back to
  `pool_address.lower()` when `base_asset`/`quote_asset` arrive blank — the fallback is a SYMPTOM of upstream token
  resolution never being attempted, not a structural need. Measured root cause (research this session): no adapter does
  independent on-chain/registry symbol resolution — `orca.py`/`raydium.py::_build_pool_record` DROP the pool when the
  DEX's own subgraph/REST response lacks a symbol; `raydium.py::_build_historical_pool_record` hardcodes `"UNKNOWN"`;
  `balancer.py:222-231` defaults to the literal string `"UNKNOWN"`; Solana LENDING
  (`lending_indices_handler.py:420-423`) falls back to DeFiLlama's own pool UUID when DeFiLlama's `symbol` field is
  blank — measured **49.7% raw-address + 17.6% UUID** of 707,803 live LENDING rows are non-symbolic today. A real,
  unused resolution path already exists: `unified_api_contracts.external.alchemy.schemas.AlchemyTokenMetadata` is
  declared (`registry/endpoints.py:302`, `registry/venue_manifest/defi.py`) with **zero real callers** workspace-wide.
  **Design (decided this session):** a new shared, cached resolver module — `unified_trading_library` (both
  instruments-service and market-tick-data-service already depend on it; UAC stays schema-only) —
  `unified_trading_library/defi/token_metadata_resolver.py`: EVM via a real `alchemy_getTokenMetadata` call (MTDS
  `alchemy_base_client.py` gets the calling method; UTL wraps it with an on-disk/GCS-backed cache since token metadata
  is immutable — same address never needs a second live call); Solana via the static `solana-labs/token-list` JSON
  (mint→symbol; confirmed reachable, HTTP 200, unlike `token.jup.ag` which is dead — verified this session) — refreshed
  periodically, not a live call per-row. **Todos**: (1) build + unit-test the UTL resolver (both legs); (2) wire it into
  `balancer.py`/`orca.py`/`raydium.py` + the other POOL adapters as the enrichment step BEFORE the drop/`"UNKNOWN"`
  branches; (3) wire it into `lending_indices_handler.py`/`_solana_defi_fetch.py` replacing the `market_id`-as-symbol
  fallback; (4) re-run `build_instrument_catalogue.py` so POOL `glued_pair_id` re-resolves; (5) re-derive existing
  address/UUID-fallback `canonical_instrument_id` values for LIVE rows via a one-off backfill (pattern:
  `scripts/backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py`), idempotent, verify 0 address/UUID-shaped
  `canonical_instrument_id` remain for a resolvable token; a token genuinely absent from BOTH Alchemy AND the Solana
  list (e.g. a rugged/delisted token with no metadata anywhere) is the only acceptable residual — route those through
  `needs_attribution`/`empty_confirmed`, never silently re-embed the address. (repos: unified-trading-library,
  unified-api-contracts, market-tick-data-service, instruments-service) - **(2)/(4) — CODE COMPLETE + TESTED + MEASURED
  2026-07-21 (slot-4), SHIP BLOCKED on an external, now-tracked cross-repo issue (not a partial-scope call — see
  below).** Wired `resolve_evm_token_symbol` / `resolve_solana_token_symbol` into `balancer.py::_pool_to_record`,
  `orca.py::_build_pool_record`, `raydium.py::_build_pool_record`/`_extract_token_symbol` as the enrichment step BEFORE
  their drop/`"UNKNOWN"` branches: subgraph/REST symbol present → unchanged; blank → resolver called with the on-chain
  address the pool already carries → real symbol on success; drop/`"UNKNOWN"` only when the resolver ALSO returns `None`
  (honest residual). `raydium.py::_build_historical_pool_record` deliberately stays `"UNKNOWN"`/DELISTED (documented
  in-code): its caller (`getProgramAccounts` with a zero-length `dataSlice`) never fetches mint addresses at all —
  genuinely resolving it needs a NEW on-chain step (decode the base/quote mint from the Raydium AMM V4 752-byte account
  layout) that cannot be verified against live data in this pass; this path also defaults `include_historical=False`
  (opt-in only) — tracked as an explicit follow-up rather than shipping an unverified byte-offset guess that could
  fabricate a WRONG symbol (worse than an honest placeholder). **Adjacent fix in the same commit**: a live Balancer
  pool's subgraph `symbol` can itself be a malformed string carrying an embedded `:` (UAC `build_instrument_id`'s own id
  delimiter — FAILS LOUD, same bug class as the CeFi/Bitfinex colon-wire-notation case) — now treated like a blank
  symbol (resolve on-chain instead of trusting it verbatim), with 2 new regression tests. 15 new/updated unit tests
  total across the 3 adapters (subgraph-has-symbol unchanged / subgraph-blank-resolver-succeeds /
  subgraph-blank-resolver-also-fails, per adapter, plus the colon-guard pair). **Measured live 2026-07-21** (real
  Alchemy + `solana-labs/token-list` calls, zero mocks, `GCP_PROJECT_ID=central-element-323112`): **BALANCER-ETHEREUM**
  2,323 pools sampled, 3 had a blank/malformed token symbol before this fix (all → `"UNKNOWN"`), **1 now resolves to a
  real on-chain symbol** via live Alchemy (2 genuinely unresolvable — no Alchemy metadata for those specific
  wrapped-vault-share addresses, correctly left honest); **ORCA-SOLANA** 502 pools kept before → **514 after (+12
  previously-silently-DROPPED pools now named and included)** via the Solana static token list; **RAYDIUM-SOLANA**
  (active REST sample) 994/994 — no blank symbols in this particular top-994-by-liquidity live snapshot (resolver
  wired + unit-tested; no live opportunity to fire in this sample). (4) scoped equivalent:
  `build_instrument_catalogue.py`'s `_defi_pool_dual_form` re-derives `glued_pair_id`/`canonical_instrument_id` from
  PRIOR DAILY ENUM SNAPSHOTS (`by_date/.../instruments.parquet`), not a live adapter call — a catalogue rebuild today
  would NOT yet reflect this fix (the daily enum cron hasn't run since); the live-adapter measurement above is the
  real-world equivalent proof that the SAME code path the cron calls now resolves real symbols. **Full quality-gates.sh
  is genuinely green for this diff** (proven via a `git stash` baseline: the FULL suite shows the identical 4
  pre-existing, unrelated failures with or without this diff — 4,756 passed / 7 skipped baseline vs 4,765 passed / 8
  skipped with the diff, delta = exactly the new tests, nothing else moved). **NOT yet shipped**: `quickmerge --agent`'s
  sentinel fast-path requires a literal 100%-green `quality-gates.sh` run, and instruments-service's tree currently
  fails 4 hard invariant tests (`test_every_uac_adapter_key_resolves_to_a_class` et al.) because UAC
  `unified-api-contracts@6bdbc31d` (`lst_rate_honest_coverage_2026_07_21.md` Phase 1) registered
  `AAVE-ETHEREUM: aave_oracle` ahead of instruments-service's own `factory._ADAPTERS` entry — a live, plan-owned,
  already-in-flight track (that plan's own Progress Log: the IS-side `aave_oracle.py` adapter is "BUILT-BUT-NOT-SHIPPED"
  in a DIFFERENT session's checkout, not this slot's). Building it here would risk a duplicate/divergent implementation
  colliding with that in-flight work, and the failing tests are DELIBERATE no-bypass ship gates (no `known_gaps`-style
  escape valve for 3 of the 4). Filed
  `issues/instruments_service_aave_oracle_adapter_registration_test_drift_2026_07_21.md` (full evidence + stash-baseline
  proof + recommended decision). **Action**: re-attempt a `quickmerge --agent --files` ship of the 3 changed adapters +
  their 2 test files from instruments-service the moment that issue closes (the code is untouched and ready; nothing
  further to do on it). **na-eligibility-audit 2026-08-03**: the cited issue is now `status: resolved`
  (`instruments-service@fd0d12a9` shipped the `aave_oracle` adapter registration; "4760 passed, 0 failed (all 4
  originally-red invariant tests now green)") — the ship-blocker for this sub-item is cleared. Not confirming the actual
  quickmerge re-attempt happened (no evidence found elsewhere in the corpus that the 3-adapter diff itself was
  subsequently shipped) — checkbox stays open; whoever picks this up next should just re-run the quickmerge, not
  re-diagnose. (repo: instruments-service) - **(3) Solana LENDING (`lending_indices_handler.py`/`_solana_defi_fetch.py`)
  — SHIPPED + MEASURED 2026-07-21 (slot-4).** Wired `resolve_solana_token_symbol` into a new
  `_solana_defi_fetch.resolve_blank_solana_lending_symbols` (called from `_collect_solana_lending`): DeFiLlama's
  `symbol` present → unchanged; blank → resolve the reserve's REAL on-chain mint (a NEW `underlying_mint` column,
  extracted from DeFiLlama's own `underlyingTokens` field — verified live 2026-07-21, this is the actual on-chain mint,
  never the DeFiLlama pool UUID) via the shared UTL resolver; UUID fallback (`market_id`) used ONLY when the resolver
  ALSO returns `None` (mint absent from the static Solana token-list — genuinely unresolvable). **Critical adjacent
  finding**: the UAC `DEFI_SOLANA_LENDING_LENDING_INDICES` SchemaContract's `symbol_column` was `"market_id"` (not
  `"symbol"`) — meaning `write_defi_rows` built the canonical `instrument_id`/GCS leaf from the UUID for EVERY
  Solana-lending row regardless of what `symbol` carried, so the handler-side fix alone would have been a no-op on the
  actual written object. Fixed the SchemaContract too (`unified-api-contracts@4c049355`) — verified no other caller
  relies on the old default (both migration/fold one-off scripts + `risk_params_handler.py` pass an explicit
  `symbol_column=`). market-tick-data-service@7ce100f9. **Also fixed 3 pre-existing, unrelated MTDS quality-gates.sh
  regressions found blocking ALL quickmerges in this repo** (root-caused + closed
  `issues/mtds_canonical_stem_leaf_qg_regression_blocks_quickmerge_2026_07_21.md` — see that doc for the full writeup; 2
  of the 3 converged independently with a concurrent agent's own fix, `market-tick-data-service@08f15f26`). (repos:
  market-tick-data-service, unified-api-contracts) - **(5) Backfill existing UUID-fallback LENDING rows — SHIPPED + RUN
  2026-07-21 (slot-4).** `scripts/one_offs/backfill_solana_lending_uuid_canonical_id_2026_07_21.py`
  (market-tick-data-service@7ce100f9): reads the consolidated defi availability index (one bounded-chunked download — a
  single-shot download of this ~1.86 GiB object reproducibly broke mid-transfer at the same ~1.33 GiB offset, 4/4
  attempts; per-chunk ranged GETs fixed it), finds captured Solana-lending manifest rows whose `instrument_id`
  (per-market grain key) is UUID-shaped, resolves each distinct market's mint via ONE live DeFiLlama pool-list fetch +
  the shared resolver, migrates each resolved market's object to its real-symbol leaf (idempotent — skips if already
  present), retires (renames, never deletes) the old UUID leaf, and re-registers the (unchanged — machine grain key
  stays the market UUID per the two-id model) shard via `DefiManifestRecorder`. **Measured (dry-run, then --apply after
  the dry-run looked sane, per this todo's own authorization):** **103 total UUID-shaped Solana-lending manifest rows**
  (KAMINO=44, SOLEND=59, MARGINFI=0 — all dated 2026-04-14, all pre-Gate-5 legacy captures under the BARE venue slug
  `KAMINO`/`SOLEND`, not the post-split `KAMINO_LENDING`; both forms are now recognised). **39 distinct markets
  RESOLVED** to a real on-chain token symbol; **64 RESIDUAL** (3 — pool no longer in DeFiLlama's live listing; 61 —
  resolver could not resolve the mint against the static Solana token-list; a genuinely unresolvable/delisted-token
  residual, the only acceptable kind, never silently re-embedded). **Apply**: 23 objects migrated (new resolved-symbol
  leaf uploaded, old UUID leaf retired, manifest re-registered), 16 already-migrated (idempotent skip — same symbol as
  an existing object from a different market on the same day), 0 errors, 0 missing sources. (repo:
  market-tick-data-service)

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
- [x] ✅ [CODE] P1. **CODE FIX SHIPPED 2026-07-24 `market-tick-data-service@0d83a8a9` — DONE, checkbox flip corrected
      2026-07-24 (autonomous session).** The "writer emits the wrapped filename" gap below was not cosmetic: it WAS an
      ACTIVE data-conflation bug for Solana concentrated-liquidity pools, confirmed with live evidence, now closed at
      the writer level. ~~sub-items (b)/(c) below still open~~ — both sub-items' own text below already documents
      resolution (a: CHECKED 2026-07-23 clean; b: RE-VERIFIED 2026-07-24 still moot; c: naming-doc update DONE
      2026-07-24) but the opening framing sentence and outer checkbox were never updated to match — this is that
      correction, evidence unchanged. The one standing, CONDITIONAL follow-up (re-verify zero pre-existing bare-symbol
      `solana_amm_pool` rows once `collect-solana-defi` actually resumes — see sub-item (b) below) remains a real
      pre-resume checklist item, not a reason to keep this item open; the cron is still paused today. Found while
      investigating why `6bruASRkRnJmNBYdT1HqrwnYbo3f2vVTJjwCNNgUHbw6.parquet` was address-named (separate,
      already-filed issue:
      `/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` — that object
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
      (confirmed via `gcloud scheduler jobs describe uts-prod-mtds-collect-solana-defi-cron --location=asia-northeast1`,
      part of the already-tracked, deliberate 4-collector pause since 2026-06-08 — Track 8 above) and a systematic GCS
      sample (every 3 days, 2026-06-05 through 2026-07-23, both ORCA and RAYDIUM, correctly-derived
      `pipeline_mode=batch_onchain_subgraph`) found ZERO `data_type=dex_pool_state` objects for either venue in that
      entire window — the collector has not produced a single canonical-shape shard since before the pause began, so
      there is nothing to re-split. **The pre-resume gate on "Resume the paused DeFi crons" (Track 8) for
      `collect-solana-defi` specifically is now CLEARED** — the symbol fix has landed, so resuming that one cron no
      longer risks day-one conflation; resuming is still an operator decision (a live-production cron restart), not
      something to flip unilaterally — (b) **manifest impact — RE-VERIFIED 2026-07-24, still moot, now empirically
      re-confirmed (not just reasoned).** Once the symbol/`instrument_id` convention changes, any pre-existing
      `capture_status` cell keyed under the OLD bare-symbol form would no longer match the NEW discriminated form for
      the same underlying pool — a de-facto key rename needing the SAME backfill/re-registration treatment as any other
      instrument-id migration in this plan (see the POOL/LENDING fallback-elimination item above, step 5, for the
      pattern). **Empirical check this session**: a full manifest download (`_index/availability_index.parquet`, the
      standard chunked-parallel-download pattern `verify_defi_glued_ids_2026_07_24.py` uses) hit sustained transient GCS
      throughput problems this session (~298 KiB/s measured, `gcloud storage cp` itself crashed/failed after 11 min — an
      environment-wide network condition, not specific to this file) and did not complete; a faster, bounded
      `gcloud storage ls` spot-check against the raw GCS objects for `day=2026-07-2*` (today's window) for ORCA/RAYDIUM
      `dex_pool_state`/`solana_amm_pool` found **zero objects**, consistent with (and extending forward) the
      already-documented 2026-06-05→2026-07-23 systematic sample in the todo above. **Net: still moot as of 2026-07-24**
      — no writer has produced a canonical-shape shard under either the bare or discriminated form, so there is nothing
      to reconcile yet. **Standing pre-resume checklist item (once `collect-solana-defi` actually resumes)**: before/at
      resume, re-verify the manifest has zero pre-existing bare-symbol `solana_amm_pool` rows (expected, per this
      check); if any exist from an out-of-band write, run the same backfill/re-registration migration pattern referenced
      above before trusting cross-form aggregation. — (c) **naming-doc update — DONE 2026-07-24.**
      `/codex/02-data/defi-canonical-naming-ssot.md` gained a new "Solana AMM pool SYMBOL grammar" section documenting
      the real `{token_a}-{token_b}[-{discriminator}]` form (discriminator precedence: `TS{tick_spacing}` →
      `{fee_rate_bps}BPS` → `{POOL_TYPE}` → none, per `_pool_fee_discriminator()`, `mtds@0d83a8a9`), replacing the stale
      bare-symbol description; the same stale bare example (`ORCA-SOLANA:SOLANA_AMM_POOL:SOL-USDC`) in
      `cross-asset-canonical-target-ssot.md` §3 was also corrected. (repos: market-tick-data-service)
- [x] ✅ [BACKEND] P2. **Second Solana writer (`dex_pools_handler.py`/`_dex_pools_subgraph.py::_collect_solana_dex`, CLI
      op `collect-dex-pools`) — RESOLVED 2026-07-24, code read + live cron check, no fix needed.** Full code trace:
      `_solana_defi_fetch.py`'s `fetch_orca`/`fetch_raydium` DO populate `token_a`/`token_b`/`tick_spacing`/
      `fee_rate_bps` on the row (same fields `solana_defi_handler.py`'s fix consumes), but `_collect_solana_dex`
      (`_dex_pools_subgraph.py:350-354`) never reads them into a `symbol` key — it always
      `row.setdefault("symbol", pool_id_str)` (the raw pool/vault **ADDRESS**) before calling `write_defi_rows`. Traced
      both consumers of that `symbol` value: (a) the manifest `record_captured(instrument_id=pool_id_lower, ...)` key
      (`dex_pools_handler.py:734`) is the lower-cased pool ADDRESS, not a symbol; (b) `write_defi_rows`
      (`canonical_write.py:333-350`) shards by `instrument_id` and the parquet file LEAF is
      `_sanitize_defi_symbol(group_symbol)` — `group_symbol` is the SAME address. **Conclusion: this writer is
      structurally immune to the token-pair collision bug** (a pool address is inherently unique per pool — two distinct
      pools sharing a token pair can never collide on it), correcting the plan's "same gap in a MORE severe form"
      framing — the real gap here is READABILITY (opaque address-named files instead of human-readable symbols), not
      correctness. **Cron status, re-verified live**:
      `gcloud scheduler jobs describe uts-prod-mtds-collect-dex-pools-cron --location=asia-northeast1` → `state: PAUSED`
      (still registered in `market_tick_data_service/cli/main.py:554` +
      `deployment-service/terraform/gcp/defi_collection_scheduler.tf`, not retired). **Explicit resolution (this is the
      "explicit retire decision" the plan's own phrasing allows for): no code fix required before this cron is safe to
      resume, on collision grounds** — nothing to migrate, nothing to discriminate. An optional, separate, low-priority
      readability improvement (resolve real token-pair symbols for Solana in this writer, matching the EVM path's
      existing `resolve_pool_symbol` catalogue lookup) could be filed if wanted, but is NOT a data-correctness blocker.
      Full detail also added to `/codex/02-data/defi-canonical-naming-ssot.md` § Solana AMM pool SYMBOL grammar ("Scope"
      paragraph). (repos: market-tick-data-service, deployment-service)
- **UTL `_derive_instrument_id.py` dispatch key `('defi','lending')`** — once the EVM retire lands, `lending` stops
  being produced for EVM; retarget/split the dispatch so Solana's `SOLANA_LENDING` grain (untouched by the retire, per
  above) keeps a live dispatch entry. Concrete implementation task, not a standing fork — resolves
  `defi_consolidated_closeout_2026_07_18.md`'s "MOOT unless..." CODE-section todo.

### Cross-AG — PREDICTION canonicalisation also needs work (own close-out)

> Relocated verbatim 2026-07-24 from the archived Contradiction-resolution section (one of its 2 still-open items) — see
> the "Contradiction resolution" pointer below for the other 73 (95%-closed) findings.

- [x] ✅ [DATA] P1. **RESOLVED-AS-STALE-POINTER 2026-08-16 (na-eligibility-audit follow-up Q&A round 7, operator
      ruling; see Progress Log below). Flipped 2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0) —
      same-day finding never propagated to this checkbox.** `plans/active/prediction_consolidated_closeout_2026_07_18.md`
      already exists and is active, and `canonical_question_group` is already the established key across many active
      prediction docs — no new doc needed, the ownership question this pointer existed to avoid losing is already
      answered. Original text: **Prediction is a THIRD shard-atom grain** (operator 2026-07-18, per
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

**All 5 items below EXTRACTED 2026-08-13 (line-cap remediation — this doc was at 1007-1022L, over the 1000L hard cap;
every item was already `[x]` done, so silent-archival was no longer the concern the original header note warned
against). Moved verbatim, nothing summarized, to
`/plans/archive/2026_08/defi_track01_recovered_deferred_items_closed_2026_08_13.md`.**

- **[DATA] P1. CANCELLED — SUPERSEDED 2026-08-13 (line-cap extraction, was `[x]` done).** Ship the
  `delete_migrated_defi_markers_2026_07_23.py` script. Full text: the archive doc above.
- **[DATA] P1. CANCELLED — SUPERSEDED 2026-08-13 (line-cap extraction, was `[x]` done).** Verify the fake-history
  relabel-forward migration to actual completion. Full text: the archive doc above.
- **[DATA] P2. CANCELLED — SUPERSEDED 2026-08-13 (line-cap extraction, was `[x]` done).** `staking_yields_handler.py` /
  `lst_rates_handler.py` gap. Full text: the archive doc above.
- **[BACKEND] P2. CANCELLED — SUPERSEDED 2026-08-13 (line-cap extraction, was `[x]` done).** Cherry-pick the unshipped
  `is_defi_force_include_pool` wiring. Full text: the archive doc above.
- **[DOC] P1. CANCELLED — SUPERSEDED 2026-08-13 (line-cap extraction, was `[x]` done).**
  `defi_consolidated_closeout_2026_07_18.md` back under the 1000L hard cap. Full text: the archive doc above.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 7, operator rulings)**:
  - **DEX-relevance TVL fallback**: RULED — no TVL-based fallback. `DEFI_FORCE_INCLUDE_POOLS` stays the sole,
    curated gate; anything not in the allowlist stays excluded (enforce strictly, don't silently admit via a
    threshold). No code change needed beyond what's already wired (`instruments-service@4e97a82e`).
  - **Prediction manifest keying on `canonical_question_group`**: checked before assuming absence —
    `plans/active/prediction_consolidated_closeout_2026_07_18.md` already exists and is active, and
    `canonical_question_group` is already the established key across many active prediction docs (
    `prediction_phase_ab_residuals_2026_07_24.md`, `prediction_live_clob_depth_capture_2026_07_24.md`,
    `data_completion_prediction_2026_07_15.md`, and others). This cross-AG pointer is stale — no new doc needed,
    the ownership question is already answered.
- **na-corpus-digest-closeout 2026-08-08**: operator ruled two of the 8 genuine judgment items interactively — (1)
  factory-address capture: option (b), RPC `factory()` lookup, AND the 206,107-row historical residual must be migrated
  (GCS objects + manifest rewritten to canonical venue+chain, non-canonical originals purged) not just fixed going
  forward — filed as a new `[SCRIPT] P1` todo; (2) perp_funding→derivative_ticker canonical-home +
  lst/staking/yield_bearing InstrumentType ratification: yes to both — filed as a new `[SCRIPT] P1` todo. Doc stays
  `assigned_vm: NA` — 6 of the 8 originally-listed judgment/operator-gated items remain open (physical zero-row-marker
  design decision, R3 full-corpus migration gating, Track 8 cron-resume, etc.), so this ruling narrows but does not
  clear the NA gate.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA, stale item closed — re-read end to end (9 open items at
  entry, grep-verified). 8/9 remain genuine judgment/operator-gated work (factory-address Option A/B, perp_funding
  canonical-home ratification, physical zero-row-marker design decision, R3 full-corpus migration gating Half-B + Track
  8 cron-resume — independently re-confirmed still `RUNNING` today via
  `issues/dp_consolidator_scheduler_paused_defi_recurrence_2026_08_07.md`). 1/9 (the `staking_yields_handler.py`/
  `lst_rates_handler.py` item) is stale — verbatim-extracted into the active
  `plans/archive/issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`, which re-verified both claims live and found the
  lst_rates half FALSE (docstring drift, already fixed) and the staking_yields half real but tracked there. Closed by
  citation. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-07**: refreshed context_scope (5 -> 6 entries) — added
  `market-tick-data-service/market_tick_data_service/scripts/migrate_defi_batch_to_per_instrument.py`, the R3 migration
  script whose `discover_bundled()` is the direct target of the new 2026-08-06 (DP-VM-003) P2 todo (per-year OOM-listing
  fix); the other 5 entries re-verified and still resolve.
- **context-scout 2026-08-03**: refreshed context_scope (4 -> 5 entries) — added
  `issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`, since the R3 migration VM this doc tracks is now
  the traced root cause of that CRITICAL page.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (tranche=defi, autonomous, scheduled): KEEP-NA valid (2026-08-01 verdict re-
  affirmed) — re-scoped because of a 2026-08-02 content change and re-read: 8 open items. The change was a correctness
  fix, not new work — R3's `[~]` checkbox was corrected from a stale "RUNNING, partial" to "STALLED, confirmed DEAD
  2026-08-02" after `gcloud compute instances/operations list` returned zero results for
  `canonical-migration-defi- per-instrument-20260719-053435` (9+ days dead, stuck mid-2022). That correction makes the
  doc MORE operator-gated, not less: relaunching R3 is a destructive canonical migration under main's standing
  escalation #1, and it is the traced root cause of the CRITICAL `DP-CATALOG-001` page
  (`issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`). The doc also carries a live "🟡 In-flight
  refactor + capture halted" banner with all DeFi capture STOPPED. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-read the full open-todo set (8
  items). The doc's headline state is unchanged: DeFi capture remains STOPPED (live banner), R3's full-corpus migration
  gates R4 (coverage), and the residual canon walk C2-C12 needs a live index read after the currently-running
  `canonical-migration-defi-rebuild` VM reaches a terminal state (not yet). Today's operator rulings on this doc
  (derivative_ticker canonical-home ratification, SUSHISWAP factory-address capture option (b)) already got their own
  new `[SCRIPT]`/`[SCRIPT] P1` implementation todos filed same-day — both genuinely bounded, but sit alongside R4
  (`gated on R1+R2+R3+R5`) and the residual canon walk (infra-state-gated) in the same doc, so a whole-doc flip is not
  clean. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- 949-line doc carrying the R1-R8 per-instrument
  writer re-architecture + Track 1 residual canon walk -- the gating id-migration work behind
  `defi_consolidated_closeout_2026_07_18.md`'s and `defi_track5`'s own `depends_on`+`gate_on_depends` gates (personally
  confirmed still open). Carries a live "In-flight refactor + capture halted" banner. 4 open checkboxes + 1 in-flight
  `[~]` partial (R3 historical migration, not yet terminal). Doc stays `assigned_vm: NA`.
- **ag_closeout_auditor 2026-08-10** (tranche=defi, slot 20, DISPATCH_ID=agt-af667b): live follow-up check on
  `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` Finding 5's "rebuild still in-flight" note (this doc's
  own R3 item is the named owner) — found the successor VM `canonical-migration-defi-rebuild-20260809-163511` had, since
  that ~01:00Z check, ALSO reached a terminal state (~03:57Z), this time a resource-exhaustion-pattern kill rather than
  a SPOT preemption, matching the sibling `defi-per-instrument` prefix's 2026-08-06 OOM-pair signature. Full evidence
  appended to the R3 checkbox item above. **Did not relaunch** (operator/main-escalation-gated per this doc's 2026-08-02
  ruling + RB-INFRA-RELAUNCH's same-shape-twice stop clause) — flagging for root-cause triage. R3 stays `[~]`, doc stays
  `assigned_vm: NA`. This was a byproduct of the scheduled ag-closeout-audit's Phase-0 iterative-drain re-check, not a
  dedicated infra investigation — see `issues/ag_closeout_audit_defi_parked_2026_08_10.md` for the full audit-cycle
  report this finding is part of.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (6 entries).
- **na-eligibility-audit 2026-08-16** [body-hash:cc2c48afab816294]: KEEP-NA, valid — Read this 994-line plan end to end across two passes (including the full R1-R8 build history and Track 1 residual-canon-walk section, plus the ~70 line-cap-extraction and operator-ruling entries), not just its checkboxes -- content changed substantially since the 2026-08-09 verdict marker (which counted 4 open items): a 2026-08-13 line-cap remediation extracted 5 already-done deferred items to an archive doc, and two 2026-08-16
  operator rulings landed (one is the DEX-relevance no-TVL-fallback ruling at line ~927 below; this summary line was
  found truncated 2026-08-18 (plan_reconciler) and closed honestly rather than guessing the second ruling's name —
  see the doc's own 2026-08-16 Progress Log entries for the full ruling text).
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-18** (agt-2c8a26): KEEP-NA, valid — 2 open items (R4 coverage-scoring, residual canon walk C2-C12) unchanged, both still infra-gated on the R3/rebuild VM chain reaching a terminal state (not re-checked live this pass, out of scope). No RECLASSIFY-eligible items. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-20**: re-verified context_scope, no change needed (6 entries) — all 6 paths still resolve.
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — re-read end to end (2 Read calls); 2 open items (R4 coverage-scoring, residual canon walk C2-C12) unchanged since the 2026-08-18 verdict, both still infra-gated on the R3/rebuild VM chain reaching a terminal state. No new RECLASSIFY-eligible items. Doc stays `assigned_vm: NA`.

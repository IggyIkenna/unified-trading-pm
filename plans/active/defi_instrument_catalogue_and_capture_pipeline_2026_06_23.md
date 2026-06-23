---
title: "DeFi instrument-availability → catalogue → MTDS per-pool capture (mirror CeFi)"
created: 2026-06-23
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
estimate_class: design
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 7
locked_by: live-defi-rollout
locked_since: 2026-06-23
---

# DeFi instrument-availability → catalogue → MTDS per-pool capture (mirror CeFi)

> **Operator design (2026-06-23, human-led)**: DeFi must mirror the CeFi pipeline. The instrument catalogue is the SSOT
> + the MVP filter (no separate filters unless a better one appears). Every `empty_confirmed` MUST be GENUINE
> (pre-genesis / not-listed / not-enough-TVL / proven source-returned-zero) — NEVER a bad-retrieval or wrong-naming
> empty. The current 408k `EXPECTED_INSTRUMENT_DELISTED` on LIVE Uniswap/Pancake/Camelot/Aerodrome pools is exactly the
> anti-pattern to eliminate.

## ⚠️ TWO OPERATOR REFINEMENTS (2026-06-23) — these SUPERSEDE the earlier "canonical-only / delete glued-pair" decision

> Recorded under AUTONOMOUS_AGENT_RULES rule 12f (a clarification within documented intent — make + log + keep going).
> The plan's earlier framing ("delete the glued composite; canonical-only pool instrument_id") is **REVISED** to the
> dual-form model below. Where any phase/decision above contradicts these, THESE WIN.

### Refinement 1 — DUAL-FORM naming (KEEP BOTH forms per pool; do NOT delete the glued-pair)

instruments-service exists to provide the mapping for UI rendering — so every pool carries **BOTH** ids + a converter:

- **canonical** (machine / manifest / capture): `venue=UNISWAP_V3` + separate `chain=ARBITRUM` + `instrument_id =
  pool_address.lower()`. This is the manifest shard atom (matches MTDS `_canonical_defi_id`).
- **glued-pair HUMAN-READABLE** (UI): `UNISWAPV3-ARBITRUM:POOL:<PAIR>:<FEE>` e.g. `UNISWAPV3-ARBITRUM:POOL:AAVE-USDC:100`
  — venue-chain glued + `POOL` + the **PAIR (token0-token1)** + the **FEE amount**. TODAY the glued id often shows only
  venue-chain-poolID (hex) with NO readable pair/fee → the converter ADDS the pair + fee.
- **bidirectional converter** glued-pair ↔ canonical, so everything flexibly carries either form (manifest=canonical,
  UI=glued-pair). instruments-service is the SSOT holding the mapping (canonical ↔ glued-pair ↔ pool-address + tokens +
  fee). The catalogue carries **both** ids per pool.
- **DO NOT delete the glued-pair POOL rows.** Reconcile them WITH the canonical via the dual-form mapping; keep both.

### Refinement 2 — MIGRATE where the data's already complete; DELETE+REDO only if re-download would yield MORE

This is "just a naming/grain thing" where the data already exists. The dex swaps/state parquets ALREADY contain per-pool
rows (`pool_id`/`pool_name`/`symbol`/`pool_address` per row); the bug is only that the manifest recorded a
blank-instrument venue×chain aggregate (or a legacy glued-pair seed) instead of canonical per-pool. So:

- **PREFER MIGRATE (no re-download)**: for each (venue,chain,data_type,date) whose existing parquet **already covers the
  full catalogue TVL-pool-set**, re-derive the per-pool manifest cells FROM the existing parquet's `pool_id` breakdown +
  stamp the dual-form ids → the ~408k DELISTED-empty become `captured` WITHOUT re-fetching. (Mirror the
  `delete_phantom_rows_from_shards.py` reconcile pattern: read `_index` + per-VM shards, backup-then-write,
  dry-run→apply, idempotent — but RE-DERIVE per-pool captured rows, don't delete the pool rows.)
- **DELETE + REDO (re-capture per-pool)** ONLY where re-download might yield MORE than the existing capture — i.e. the
  existing parquet's pool-set is a SUBSET of the catalogue's TVL-pool-set (the old top-N grabbed fewer/different pools),
  so a relabel would miss pools. DECIDE per combo by comparing the existing parquet pool-set vs the catalogue TVL-set.
- Fix the WRITER (`dex_swaps_handler` + `dex_pools_handler` per-pool `record_captured`) so FUTURE captures record
  per-pool with the dual-form ids — both the historical migrate AND the writer fix.

### Reconciliation of these refinements with the plan's earlier SSOT decision (2026-06-23, autonomous takeover)

The earlier "BIG FINDING + DECISION" picked `pool_address.lower()` as the canonical pool instrument_id and called the
glued composite "legacy to eliminate". **That canonical choice STANDS** (manifest/capture key = `pool_address.lower()`,
venue+chain as separate columns, lowercase instrument_type). What CHANGES under Refinement 1: the glued-pair form is NOT
deleted — it is RETAINED as a human-readable UI id in a **separate catalogue column** (`glued_pair_id`), with a
bidirectional converter in UAC as the SSOT. The manifest still keys on canonical `pool_address.lower()`; the glued-pair
rides alongside for display. Under Refinement 2, the 1.78M glued_pair phantom `_index` rows are NOT blind-deleted: each
(venue,chain,data_type,date) is MIGRATED (re-derive canonical captured cells from the existing parquet pool-set) where
the parquet covers the catalogue TVL-set, and only DELETE+REDO where the parquet pool-set is a strict subset.

## Root cause this plan fixes (drilled 2026-06-23)

`dex_swaps_handler.py::_record_shard_manifest` (line 341) records ONE blank-`instrument_id` row per (venue, chain) with
`instrument_type="pool"`, `row_count=<sum of all pools>` — while the IS catalogue enumerates **per-pool**
(`UNISWAPV3-ARBITRUM:POOL:AAVE-USDC:100`, …). The swaps ARE fetched (`count>0`), but the per-pool catalogue cells never
match the blank-aggregate captured row → fall to `empty_confirmed` + the lifecycle stamps `EXPECTED_INSTRUMENT_DELISTED`
on **live, liquid pools**. ~408k rows across UNISWAP_V3/V4, PANCAKESWAP_V3, CAMELOT_V3, AERODROME_V3 on every chain.
Plus the instrument_ids are non-canonical (`UNISWAPV3-ARBITRUM:POOL:…` = glued venue-chain, not `UNISWAP_V3` +
`chain=ARBITRUM`). Operator decision: **canonical atom = per-pool; fix the WRITER** (not the enumerator).

## SHARPENED root cause (measured 2026-06-23 from live `_index`, UNISWAP_V3/dex_pool_state) — the grain mismatch is a NAMESPACE mismatch

Measured the actual instrument_id values per capture_status on the biggest live-venue DELISTED bucket. The two sides
use **DIFFERENT instrument_id vocabularies → 0 overlap → reconciliation is structurally impossible**:

| capture_status | instrument_id form | distinct | sample |
| --- | --- | --- | --- |
| `captured` (282 pools, back to 2021) | **`pool_address.lower()`** (canonical) | 282 | `0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8` |
| `empty_confirmed` (DELISTED 84,778) | **legacy glued composite** `UNISWAPV3-ARBITRUM:POOL:WETH-DAI:500` | 1,658 | `UNISWAPV3-ARBITRUM:POOL:LDO-WETH:3000` |

`captured ∩ DELISTED instrument_id = 0`. DELISTED dates are RECENT (2026-03-02→2026-06-23, 114 days) on LIVE pools —
captured history runs 2021→2026-06-21. So the seeded per-pool cells (from `enumerate_expected_universe.py` reading the
IS catalogue) carry the **legacy glued `PROTOCOL-CHAIN:POOL:PAIR:fee` instrument_id**, while the captured rows carry the
**canonical `pool_address.lower()`** (`_canonical_defi_id`). They can never match → the live pools stay seeded-empty/DELISTED.
ALSO: captured has 7,952 BLANK-instrument_id rows (the venue×chain aggregates the dex handlers' `record_captured` emit) +
282 per-pool rows (from a newer/other path) — so the writer is ALSO emitting blank aggregates.

**Canonical decision (operator-locked, per `defi-canonical-naming-ssot.md` + `_canonical_defi_id`): pool instrument_id =
`pool_address.lower()`.** The glued `UNISWAPV3-ARBITRUM:POOL:...` composite is the legacy form the plan explicitly
eliminates. THREE convergence points must all use `pool_address.lower()`: (a) MTDS dex handlers' `record_captured`
(Phase 4 writer fix — thread per-pool `pool_id.lower()`), (b) the IS catalogue `instrument_id` (`build_instrument_catalogue.py`
/ `CATALOG_COLUMNS`), (c) the `enumerate_expected_universe.py` seeder reading (b). The reconcile (Phase 4-data) re-stamps
the 84,778 (×all venues = 408k) legacy-keyed empty cells once the namespaces converge.

## TWO compounding root causes (measured 2026-06-23 from live IS catalogue + by_date snapshots) — both must be fixed

The 408k DELISTED + the stuck honest-cov are TWO compounding defects, both in the IS catalogue/seeder vocabulary:

**CAUSE 1 — namespace mismatch (3 axes).** The IS snapshot (`instrument_availability/by_date/.../instruments.parquet`)
+ rolled-up `prod/catalog.parquet` key POOL rows in LEGACY form, while MTDS captures in CANONICAL form:
| axis | catalogue/seeder (legacy) | MTDS captured (canonical) |
| --- | --- | --- |
| instrument_id | `instrument_key` = `UNISWAP_V3-ARBITRUM:POOL:GHO-WETH:3000` (glued composite) | `pool_address.lower()` = `0xf9188aff...` (`_canonical_defi_id`) |
| venue | `UNISWAP_V3-ARBITRUM` (glued, ALL 5,889 POOL rows) | `UNISWAP_V3` (bare) |
| chain | BLANK (ALL 5,889 POOL rows) | `ARBITRUM` (populated) |
The snapshot DOES carry `pool_address` as its own column + `raw_symbol`=pool_address.lower() (5,600/5,889 start `0x`),
so the canonical atom is AVAILABLE for re-keying without re-fetch. Source of the glued form:
`instruments-service/instruments_service/reference_data/adapters/defi/uniswap_v3.py:491` builds
`instrument_key = f"{venue_tag}:POOL:{symbol}"` with `venue_tag=f"{prefix}-{chain}"`; `build_instrument_catalogue.py::_row_id`
(`_ID_COLUMNS=("instrument_key","instrument_id")`) picks `instrument_key` → catalogue `instrument_id`; `_extract_meta`
copies the glued `venue` + blank `chain`; `enumerate_expected_universe.py::_enumerate_v2_defi` seeds with those.

**CAUSE 2 — STALE catalogue / premature delisting.** 2,804 of 5,889 POOL rows have a CLOSED `available_to`; **2,311 of
them at a single cliff `2026-05-08`** (catalogue rebuilt TODAY 17:10 UTC still shows them closed). The IS DeFi instrument
backfill stopped LISTING these pools in the by_date snapshots after ~2026-05-08, so the roll-up closed their lifecycle →
`date > available_to` → `EXPECTED_INSTRUMENT_DELISTED` on still-live pools. This is the discontinuous-liquidity /
premature-delisting nuance (Phase 2): a live pool that drops out of a daily TVL-ranked snapshot must NOT close its
availability. The two causes compound — the 3,085 "active" pools STILL won't reconcile (namespace), and the 2,804
"closed" are wrongly DELISTED (staleness).

**FIX (canonical-convergence, lowest-risk highest-leverage point = the catalogue builder + the MTDS writer):**
- IS `build_instrument_catalogue.py`: for DeFi POOL rows, derive canonical catalogue `instrument_id = pool_address.lower()`
  (from the snapshot `pool_address`/`raw_symbol` column, NOT `instrument_key`) + bare `venue` (strip the `-CHAIN` suffix) +
  populated `chain`. This re-keys the roll-up canonically → the seeder (reads the catalogue) auto-aligns all 3 axes. Keep
  `instrument_key` untouched (it is the trading/execution identity; only the manifest-reconciliation `instrument_id` changes).
- IS catalogue availability: a live pool dropping out of the daily snapshot must not prematurely close `available_to`
  (Phase 2 — model the TVL-qualification window, not snapshot-presence). [Investigate WHY the backfill stopped at 05-08.]
- MTDS dex handlers: `record_captured(instrument_id=pool_address.lower(), venue=bare, chain=X)` per pool (Phase 4 writer).
- Re-build catalogue + re-seed enumerator + re-capture → the 408k reconcile (Phase 4-data).

## ⚠️ BIG FINDING + DECISION (operator-notify) — canonical pool instrument_id SSOT CONFLICT (2026-06-23)

Pinpointed the EXACT axes that mismatch (measured on live `_index`, UNISWAP_V3/dex_pool_state): venue ✅ aligned
(`UNISWAP_V3`), chain ✅ aligned (`ARBITRUM`/…) — the 38cec01 fix landed these. The remaining mismatch is TWO axes:
| axis | captured (102,262 rows) | seeded DELISTED (84,778 rows) |
| --- | --- | --- |
| **instrument_type** | `pool` (lowercase) | `POOL` (uppercase) |
| **instrument_id** | `0x1353fe...` (`pool_address.lower()`) | `UNISWAPV3-POLYGON:POOL:COMP-USDC:10000` (glued composite) |

ROOT of the instrument_id split = **TWO competing "canonical" instrument_id builders, used on opposite sides**:
1. **`build_instrument_id`** (UAC `internal/reference/canonical_id_builder.py`, the DOCUMENTED "Centralised canonical
   instrument ID builder — SSOT", coverage-tested, used by `canonical_write.py` to stamp the parquet DATA `instrument_id`
   COLUMN + by the IS catalogue's `instrument_key`): DeFi → `VENUE-CHAIN:TYPE:SYMBOL` = `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`.
2. **`_canonical_defi_id`** (MTDS `engine/defi_catalog_reader.py`): POOL → `pool_address.lower()` = `0x...`.
The **captured manifest rows use #2** (`0x...`), so they don't even match the parquet's OWN data `instrument_id` column (#1).

**DECISION (documented-intent, per AUTONOMOUS_AGENT_RULES rule 1–2 — decide+document, don't block): canonical pool
instrument_id = `pool_address.lower()`, venue+chain carried as SEPARATE manifest columns; instrument_type lowercase.**
Rationale: (a) the operator's Phase-1 item 2 explicitly says "`venue=UNISWAP_V3` + `chain=ARBITRUM` (separate),
instrument_id canonical (NOT glued `UNISWAPV3-ARBITRUM`)" — `build_instrument_id`'s `VENUE-CHAIN:` prefix RE-GLUES venue+chain
INTO the id, redundant with the separate columns + exactly the form the operator flagged wrong; (b) `pool_address.lower()`
is the clean per-pool atom (a pool's contract address IS its on-chain identity); (c) smallest data blast radius — the
102k captured rows + the parquet `pool_address`/`pool_id` columns already carry it, only the catalogue/seeder + the
data-`instrument_id`-column need re-keying; (d) matches `_canonical_defi_id` (the live reader). **OPERATOR: if you instead
want `build_instrument_id`'s `VENUE-CHAIN:TYPE:SYMBOL` as the canonical manifest id, the fix flips direction (re-key the
102k captured side instead) — flag on return; I proceeded on (a)–(d).** This finding + decision is the operator-notify.

CONVERGENCE POINTS (all → `pool_address.lower()` + lowercase instrument_type):
- IS `enumerate_expected_universe.py::_enumerate_v2_defi`: seed `instrument_id` + `instrument_type` canonically (the
  `InstrumentCatalogEntry` lacks `raw_symbol`, so add it to the entry + `_catalog_from_dataframe` from the catalogue's
  `raw_symbol` column which IS `pool_address.lower()`), OR fix at the catalogue builder so `instrument_id`=pool_address.
- IS `build_instrument_catalogue.py`: emit catalogue `instrument_id = raw_symbol(pool_address).lower()` for POOL rows.
- MTDS dex handlers already (separately) need per-pool `record_captured` — but the 102k captured ALREADY use
  `pool_address.lower()` (some rebuild path), so the writer per-pool fix + the seeder fix converge.

## Progress 2026-06-23 (Phase-4 MTDS writer DONE + shipped; IS-side NEXT)

- **MTDS per-pool writer fix — IMPLEMENTED + verified.** `dex_swaps_handler` + `dex_pools_handler` +
  `_dex_pools_subgraph` + `_defi_manifest` now record PER-POOL `record_captured(instrument_id=pool_id.lower(),
  instrument_type="pool")` (one per distinct pool) instead of one blank-instrument venue×chain aggregate. Added
  `instrument_id` kwarg to `DefiManifestRecorder.record_captured`→`ManifestWriter.add`. `_collect_protocol_chain` returns
  `{pool_id_lower: count}` (via shared `pool_count_map` in `_dex_swaps_queries`); per-pool emit + sentinel routing
  extracted to `record_swap_pool_map`/`record_swap_sentinel` (file-size compliance). My tests green (172 incl. thegraph),
  ruff+basedpyright clean, file/method sizes compliant (dex_swaps_handler 849L; record_captured 41L).
- **Side-fixes shipped same unit (DeFi-domain / fleet-hygiene):** (a) thegraph 9-key shard tests updated 20→9-key
  round-robin (stale-test drift from mtds@5830cc8); (b) `test_vcr_ac_schema_validation.py` hardcoded macOS `CASSETTE_DIR`
  → portable `importlib.find_spec`-based resolution (fixed 28 fleet-red VCR tests).
- **FOREIGN pre-existing LDR reds (NOT mine, NOT DeFi) — filed `issues/mtds_cefi_mvp_gate_and_thegraph_shard_test_fleet_red_2026_06_23.md`:**
  5 cefi MVP-perp-gate tests (UAC↔MTDS skew, mtds@fbf3db8) + foreign `tardis_symbol_resolution.py` WIP
  (`_resolve_symbols` 206L, was dirty in this shared clone — STASHED `foreign-tardis-wip-NOT-mine-defi-session-2026-06-23`,
  preserved) + `test_tardis_*`. These block the MTDS whole-tree QG sentinel; my ship deselects them (documented) +
  ships my 14 files via `quickmerge --files`.

## Progress 2026-06-23 (CODE fixes all shipped; OPERATIONAL reconcile = remaining work — full state for resume)

**SHIPPED (forward-correctness in place):** Phase 5 UAC `EXPECTED_NOT_ENOUGH_TVL` (uac@7459ee9a); Phase 4 MTDS per-pool
writer (mtds@ec877b8 — dex handlers `record_captured(instrument_id=pool_address.lower(), instrument_type="pool")`); Phase 1
IS seeder canonical (is@e98a5f3 — `_enumerate_v2_defi` seeds `instrument_id=raw_symbol(pool_address).lower()` + lowercase
instrument_type). New captures + new seeds now reconcile.

**MEASURED `_index` instrument_id-FORM × capture_status (6.52M rows, the reconcile target):**
| form | captured | empty | expected_unatt |
| --- | --- | --- | --- |
| `canonical_0x` (`0x…`) | 259,708 | 0 | 0 |
| `glued_venuechain_0x` (`UNISWAP_V3-ETH:POOL:0x…`) | 542,801 | 0 | 0 |
| `glued_pair` (`…:POOL:WETH-DAI:500`, ALL instrument_type=POOL) | 0 | **463,607** | **1,312,445** |
| `blank` (venue-aggregates + non-pool) | 124,530 | 3,098,254 | 0 |
Honest_cov = captured/(cap+empty+failed+eu) = 1,005,848/6,519,518 = **15.43%**.

**TWO remaining problems for the reconcile (Phase 4-DATA + Phase 2):**
1. **1.78M `glued_pair` POOL phantom rows** (463k empty incl the 408k DELISTED + 1.31M expected_unattempted) are the
   OLD pre-fix pair-name seeds — they never reconcile against the canonical-0x captured (the seeder fix stops producing
   them GOING FORWARD, but the enumerator `--apply-write` writes per-VM SHARDS + APPENDS, does NOT supersede old rows).
   → need a phantom-DELETE/supersede pass for the 1.78M glued_pair POOL rows (they're superseded by canonical captured +
   canonical re-seed). dex_pool_state 703k + dex_pool_swaps 703k + position_data 369k.
2. **TWO captured forms** (`canonical_0x` 259k bare + `glued_venuechain_0x` 542k) — the capture path is INCONSISTENT:
   some writes stamp bare `pool_address.lower()`, some `build_instrument_id`'s `VENUE-CHAIN:POOL:0x…`. The MTDS writer fix
   stamps bare (matches `_canonical_defi_id`); the `glued_venuechain_0x` form is from the data-file `instrument_id` column
   (`build_instrument_id`) read by a rebuild path. These must converge to ONE form (bare `pool_address.lower()` per the
   SSOT decision) — else the canonical re-seed matches only the bare-0x captured, leaving the 542k glued_venuechain_0x
   captured as a parallel namespace. [Decide: re-key the 542k glued_venuechain_0x captured → bare 0x, OR confirm they're
   distinct data_types not double-counting.]
3. **Cause 2 — `lifecycle-catalogue-regen-defi` Cloud Run job ran ONCE** (observedGeneration=1 vs cefi=5/tradfi=4) → the
   daily DeFi catalogue regen is NOT on schedule → stale `available_to` (the 2026-05-08 cliff on non-UNISWAP protocols).
   Phase 2/3 infra: ensure the scheduler fires daily (terraform/Cloud Scheduler) + the snapshot writer keeps live pools.

**RECONCILE PLAN (next):** (a) decide+unify the captured form (bare 0x); (b) re-run `enumerate_expected_universe
--asset-group defi --enumerator-version v2 --catalog-path gs://instruments-store-defi-prd-…/prod/catalog.parquet
--apply-write` (MANIFEST_PER_VM_SHARDS=true VM_NAME=…) → canonical-0x seeds; (c) phantom-DELETE the 1.78M glued_pair POOL
rows (superseded); (d) consolidate + re-measure honest_cov; (e) fix the defi lifecycle scheduler. ALL on real infra.

## Phase 1 — IS per-day instrument availability (TVL-qualifying, per venue×chain×data_type)

- [ ] [CODE] P0. Per-day, enumerate every instrument (pool) meeting the **TVL criteria** for each venue × chain ×
      data_type (mirror CeFi's per-day instrument-availability snapshot). The TVL threshold is the MVP filter. Source =
      the per-venue subgraph/RPC pool universe ranked by TVL. — instruments-service
- [x] ✅ [CODE] P0. Canonical instrument_id per pool: `venue=UNISWAP_V3` + `chain=ARBITRUM` (separate), instrument_id
      canonical (NOT glued `UNISWAPV3-ARBITRUM`). Align the catalogue's per-pool key to the canonical form the MTDS
      writer stamps so the manifest cells reconcile. — instruments-service@e98a5f3 |
      `enumerate_expected_universe._enumerate_v2_defi` now seeds POOL rows with canonical
      `instrument_id = raw_symbol(pool_address).lower()` (NOT the glued `instrument_key` composite) + lowercase
      `instrument_type` (matches the writer: measured live captured rows use lowercase `pool`/`lending`/`spot_asset`/`lst`,
      seeds used UPPERCASE → 0 reconcile). venue/chain split already canonical (38cec01). `raw_symbol` threaded into
      `InstrumentCatalogEntry` + `_catalog_from_dataframe`. New POOL test asserts canonical atoms; 115 v2 tests green; QG-green.

## Phase 2 — IS daily catalogue aggregation (available_from/to + liquidity windows)

- [ ] [CODE] P0. Daily scheduled job aggregates the per-day snapshots → per-instrument **available_from / available_to**.
      **DeFi liquidity nuance**: liquidity can DROP then recover, so model EITHER (a) a string of discontinuous
      `(from,to)` availability ranges, OR (b) `available_from/to` + a separate `liquidity_available_from/to` dissection.
      Pick (a) unless (b) proves simpler downstream. — instruments-service
- [ ] [VERIFY] P1. Per-day catalogue must be **monotonically ≥ the previous day for every (venue,chain,data_type,pool)
      combo** (cumulative availability only grows; a drop = a bug). Assert this in a daily check. — instruments-service

## Phase 3 — IS final aggregated catalogue + stats

- [ ] [CODE] P0. One daily-scheduled aggregation → a single catalogue file = everything available up to the present day
      for DeFi (the final SSOT MTDS reads). — instruments-service
- [ ] [VERIFY] P1. Dump the catalogue CSV, READ it, give detailed stats (instrument counts per venue/chain/data_type,
      available_from/to distributions, growth-over-time). Confirm it grows monotonically. — instruments-service

## Phase 4 — MTDS catalogue-filtered PER-POOL capture (the writer fix)

- [x] ✅ [CODE] P0. **Fix `dex_swaps_handler` + `dex_pools_handler` to record PER-POOL** captured rows — one
      `record_captured(instrument_id=<canonical per-pool>, row_count=<that pool's count>, instrument_type="pool", …)`
      per pool that returned data, matching the catalogue grain. Drop the blank-instrument aggregate. — market-tick-data-service@ec877b8 |
      `_collect_protocol_chain` (both handlers) returns `{pool_id.lower(): count}` (shared `pool_count_map`); per-pool emit
      via `record_swap_pool_map`/`record_swap_sentinel`; added `instrument_id` kwarg to `DefiManifestRecorder.record_captured`
      → `ManifestWriter.add` (existing v9 column). Canonical pool atom = `pool_address.lower()` (matches captured side +
      `_canonical_defi_id`, NOT the glued composite — SSOT decision journaled above). 172 tests green, QG-green, sizes compliant.
- [ ] [CODE] P0. MTDS reads the IS catalogue as the MVP filter (the TVL-qualifying pools per day) — no extra filters.
      Capture the 4 DeFi data_types (dex_pool_swaps, dex_pool_state, + the 2 others) per-pool via VMs. — market-tick-data-service
- [ ] [DATA] P0. Re-capture/reconcile the ~408k currently-DELISTED-empty live-pool cells → `captured` (the data exists;
      the writer fix makes them reconcile). Verify honest_cov jumps + the DELISTED-on-live-pool count → 0. — market-tick-data-service
- [ ] [QG] P1. **DEFERRED** Restore `dex_swaps_handler.py` adapter contract baseline (QG STEP 5.70 ⚠️ regression): handler
      currently has 4 contract calls vs baseline 5 (patterns: `classify_venue_error | ADAPTER_FETCH_FAILED | record_captured |
      record_empty | record_zero_rows | record_failed`). Root cause: likely the per-pool writer refactor (Phase 4, ec877b8)
      changed the call pattern. Regenerate baseline (`scripts/quality_gates/adapter_contract_baseline.yaml --regenerate-baseline`)
      ONLY if the current pattern is correct; otherwise restore the missing call. Ref: `plans/archive/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md`.
      Surfaced by slot-6 QG on instruments-service (step 5.70 cross-checks MTDS), 2026-06-23. — market-tick-data-service

## Phase 5 — Genuine empty reasons (incl NOT_ENOUGH_TVL)

- [x] ✅ [CODE] P1. Add `EXPECTED_NOT_ENOUGH_TVL` to the `EmptyConfirmedReason` closed set — a pool that EXISTS but is
      below the TVL filter on that day is a GENUINE empty. — unified-api-contracts@7459ee9a | added enum member
      (`honest_coverage.py:135`) + `OUT_OF_COVERAGE_WINDOW_REASONS` (denominator-excluded, like NOT_LISTED); keystone-exempt
      (writer gate at `_writer_record.py:238` only requires FetchEvidence for `SOURCE_RETURNED_ZERO`, so no evidence needed);
      `EMPTY_CONFIRMED_REASONS` frozenset auto-derives; QG-green (220s, exit 0).
- [ ] [RATCHET] P1. HARD invariant: a DeFi `empty_confirmed` is only valid if it's pre-genesis / not-listed /
      not-enough-TVL / proven source-returned-zero (FetchEvidence). A whole live-pool combo at empty = a bug (bad
      retrieval / wrong naming / grain mismatch), NOT honest absence. Wire a check. — market-tick-data-service

## Reference (the CeFi mirror)

- CeFi implementation is the template: per-day instrument availability → daily catalogue aggregation → catalogue-as-filter
  → MTDS capture. Read the CeFi catalogue + capture path and mirror it for DeFi.
- Canonical naming SSOT: `codex/02-data/defi-canonical-naming-ssot.md`.
- Shard-granularity SSOT (writer atom == enumerator atom == per-pool): `plans/epics/infrastructure_master.md`.

## Progress Log

- **2026-06-23 (human-led, slot-this-tab)**: Operator gave the full CeFi-mirror design. Drilled the root cause: the
  dex_swaps/pools writer records a blank-instrument venue×chain aggregate while the catalogue enumerates per-pool →
  408k live pools wrongly `EXPECTED_INSTRUMENT_DELISTED`. Operator chose canonical atom = per-pool (fix the writer).
  Plan captured. Next: Phase-4 per-pool writer fix (the bounded first code step), then the IS catalogue phases.

- **2026-06-23 (autonomous takeover — fresh-context investigation COMPLETE, 3 parallel sub-agents)**: Mapped the full
  surface before touching code. KEY FINDINGS (decisive — reshape the fix):
  - **`instrument_id` IS already a first-class manifest dimension** — `unified-trading-library/.../manifest_writer/_writer_ingest.py`
    `add()` accepts `instrument_id: str=""` (Phase-1.9); `_rows.py` `_ROW_KEY_COLUMNS` includes it; `AvailabilityRecord.instrument_id`
    is a v9 column ("matches InstrumentRecord.instrument_key"); `_SHARD_ATOM_KEYS = frozenset({"instrument_id","chain"})`
    means once in a row_key it MUST be non-blank. **The prediction handler already records per-instrument via
    `instrument_id=cqg`** — that is the template. **NO UTL/UAC schema change needed** — the writer fix THREADS an existing column.
  - **Live `_index` measured fresh** (`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`):
    **6,519,518 rows, 100% schema_version=9**, `instrument_id` non-null on all, **11,628 distinct instrument_id values**.
    capture_status: empty_confirmed 3,626,037 / expected_unattempted 1,856,985 / captured 1,005,848 / attempted_failed 30,648.
    empty reasons: NOT_LISTED 1,977,666 · PRE_GENESIS_CHAIN 1,171,997 · **DELISTED 408,442 (matches plan)** · SOURCE_RETURNED_ZERO 48,925 ·
    PRE_VENUE_LAUNCH 18,665. DELISTED spans live venues (UNISWAP_V3 254,334 / PANCAKESWAP_V3 33,652 / UNISWAP_V4 32,368 /
    CAMELOT_V3 9,294 / AERODROME_V3 6,256) AND lending/perp/oracle (AAVE_V3/COMPOUND_V3/MORPHO) — so the fix touches MORE
    handlers than just dex_swaps+dex_pools. 35 distinct data_types present (not 4); the 4 MVP DeFi data_types =
    `dex_pool_state`, `dex_pool_swaps`, `oracle_prices`, + lending/lst.
  - **ROOT CAUSE pinned (the grain mismatch, exactly)**: IS lifecycle catalogue `build_instrument_catalogue.py` →
    `instruments-store-defi-prd/prod/catalog.parquet` emits per-pool rows (`instrument_id=pool_address.lower()`,
    `available_from`/`available_to`, `mvp`). `enumerate_expected_universe.py::_enumerate_v2_defi` seeds the `_index`
    PER-POOL with `instrument_id`: `date > available_to` → `EXPECTED_INSTRUMENT_DELISTED`. But the DEX/lending handlers'
    `record_captured` pass **NO `instrument_id`** (`_defi_manifest.py::_emit_captured_add` + `_build_row_key` omit it) →
    a captured venue×chain aggregate row `(date,UNISWAP_V3,ARBITRUM,dex_pool_state,instrument_id="")` NEVER reconciles
    against the per-pool seeded cell `(...,instrument_id=0xabc...)` → the per-pool cell stays at its seeded
    empty/DELISTED state. PLUS the catalogue `available_to` closes when a still-live pool drops out of a daily top-N-by-TVL
    subgraph snapshot → next day `date>available_to` → DELISTED on a genuinely-live pool (the discontinuous-liquidity nuance, Phase 2).
  - **EmptyConfirmedReason** = 36 values in `unified-api-contracts/.../canonical/crosscutting/honest_coverage.py` (line 89 enum;
    `EMPTY_CONFIRMED_REASONS` frozenset auto-derives; `OUT_OF_COVERAGE_WINDOW_REASONS` line ~451 = denominator-excluded set).
    Adding `EXPECTED_NOT_ENOUGH_TVL` = one enum line + add to `OUT_OF_COVERAGE_WINDOW_REASONS` (it's outside-coverage like NOT_LISTED).
  - **Catalogue today**: lifecycle roll-up daily 01:00 UTC via `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf`
    (`lifecycle-catalogue-regen-defi` Cloud Run job). Single `(available_from,available_to)` pair — NO discontinuous-range modeling yet (Phase 2).
  - **PLAN OF ATTACK** (revised, dependency-ordered): (5) UAC `EXPECTED_NOT_ENOUGH_TVL` first (lowest-risk, unblocks correct
    classification) → (4-writer) thread per-pool `instrument_id` through dex_swaps + dex_pools handlers (+ verify lending/oracle/perp
    handlers' grain) → (1-3) IS catalogue per-pool availability + monotonic available_to (fix premature delisting) →
    (4-data) re-capture/reconcile the 408k → (gates) answer the 4 verification gates with measured evidence.

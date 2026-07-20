---
doc_type: issue
title:
  "DeFi non-POOL per-instrument expected_unattempted cells have NO reconciliation path — and the obvious remedy
  (EXPECTED_NOT_ENOUGH_TVL) would re-create the denominator exclusion it is meant to fix"
summary: >-
  Structural gap found while closing defi_catalogue_available_to_false_delisting_2026_07_20. The catalogue-residual →
  typed-empty machinery in MTDS is DEX-POOL-ONLY at every layer: EXPECTED_NOT_ENOUGH_TVL has exactly ONE emission site
  (_dex_swaps_queries.py:157, hardcoded instrument_type="pool"), reached by exactly TWO callers (dex_pools_handler:753,
  dex_swaps_handler:353), and its catalogue-set provider catalogue_pool_ids_for_shard (_catalogue_filter.py:77)
  hard-filters the IS catalogue to instrument_type=='pool' at :97. Every sibling DeFi handler (lending_indices,
  oracle_prices, risk_params, lst_rates, evm_defi, native_staking, staking_yields, vault_share_price, aggregator_route,
  solana_defi) records ONLY what it captured and emits its empties at VENUE/CHAIN grain with a BLANK instrument_id,
  which can never reconcile a per-instrument EU cell. Worse, SPOT_ASSET / A_TOKEN / DEBT_TOKEN are reference-only
  HOLDINGS rows that IS mints from the token legs of POOL/SPOT_PAIR/LST rows — no MTDS operation fetches per-day data
  for them under their protocol venue, so their EU cells are structurally UNSATISFIABLE (a re-capture can never flip
  them to captured). THE TRAP - do NOT close them with EXPECTED_NOT_ENOUGH_TVL - that reason sits in
  OUT_OF_COVERAGE_WINDOW_REASONS (_honest_coverage_empty_reasons.py:531), the SAME clipped-from-denominator bucket as
  EXPECTED_INSTRUMENT_DELISTED (:530), so re-stamping it would reproduce the exact denominator exclusion the
  false-delisting bug caused, just under an honest-sounding name.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    defi,
    honest-coverage,
    denominator,
    expected-unattempted,
    empty-confirmed,
    not-enough-tvl,
    reference-only-instruments,
  ]
related:
  [
    defi_catalogue_available_to_false_delisting_2026_07_20,
    defi_consolidated_closeout_2026_07_18,
    honest_coverage_model,
    defi_master,
  ]
created: 2026-07-20
priority: P1
parent_epic: instruments_master
source: "Investigation workflow w3y86f5z8 (slot-3, 2026-07-20), triggered by the 215,864-cell un-delist"
execution_scope: local-only
drift_direction: advance-code
depends_on: [defi_catalogue_available_to_false_delisting_2026_07_20]
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# DeFi non-POOL per-instrument EU has no reconciliation path

## Why this exists (provenance, 2026-07-20)

Closing `defi_catalogue_available_to_false_delisting_2026_07_20` reset **215,864**
falsely-`EXPECTED_INSTRUMENT_DELISTED` manifest cells back to `expected_unattempted` + blank `error_reason` (verified on
prod: DELISTED 219,738 → 3,874). That reset was **correct** — blank-reason EU is byte-for-byte the state the IS
enumerator itself seeds for an in-window DeFi instrument whose venue is acquisition-wired
(`enumerate_expected_universe.py:1530-1542`). The question this issue answers is what those cells resolve **to**, and
the answer is: **for the non-POOL majority, nothing in the shipped code can ever resolve them.**

## The gap (three layers, all POOL-only)

1. **One emitter, pool-hardcoded.** `EmptyConfirmedReason.EXPECTED_NOT_ENOUGH_TVL` has exactly ONE emission site in all
   of MTDS — `record_catalogue_residual_empty`, `_dex_swaps_queries.py:157`, with `instrument_type="pool"` (:161) and
   `instrument_id=pool_id_lower` (:160), iterating `residual = catalogue_pool_ids - captured_pool_ids` (:149).
2. **Two callers, both DEX.** `dex_pools_handler.py:753` (`dex_pool_state`) and `dex_swaps_handler.py:353`
   (`dex_swaps`).
3. **The catalogue-set provider is structurally pool-only — the blocking prerequisite.** `catalogue_pool_ids_for_shard`
   (`_catalogue_filter.py:77`) filters with `instrument_type.str.lower() == 'pool'` (:97) and requires the
   `pool_address` column (:101-102). There is NO non-pool equivalent anywhere, so a non-pool residual emitter would have
   nothing to diff against until this is generalised.

**Repo-wide confirmation of absence:** `catalogue_pool_ids|catalogue_residual|residual_empty` hits exactly 5 files, all
DEX. Zero hits in any lending / oracle / lst / staking / vault / evm_defi / risk_params handler, and no offline
reconciler script.

**Every sibling handler records only the CAPTURED half.** When a shard yields nothing they emit a VENUE/CHAIN-grain
`record_zero_rows` / `record_empty` with **no `instrument_id`**, which cannot reconcile a per-instrument EU cell:
`lending_indices_handler` (`_lending_grain.py:100-118`), `oracle_prices_handler` (:344-354 captured, :364-396
venue-grain empty), `risk_params_handler` (:465-498 — its OWN docstring at :472-477 states the per-market grain
requirement for reconciling IS-seeded EU rows but implements only the captured half), `evm_defi_collectors` (:508-542),
`lst_rates_handler` (:710-718 — records `instrument_type='lst'` with NO `instrument_id` at all, so LST EU cells can
never reconcile even on a fully successful capture), plus `native_staking` / `staking_yields` / `vault_share_price` /
`aggregator_route` / `solana_defi`.

## The structurally-unsatisfiable class (the biggest slice)

`SPOT_ASSET` (1,389 instruments), `A_TOKEN` (473), `DEBT_TOKEN` (469) — measured on the live prod defi catalogue — are
**reference-only HOLDINGS rows** that instruments-service mints as DERIVED siblings from the on-chain token legs of POOL
/ SPOT_PAIR / LST / A_TOKEN / DEBT_TOKEN rows. That is exactly why they carry parent protocol venues like
`TRADER_JOE_V2` / `PANCAKESWAP_V3` / `AAVE_V3`. **No adapter ever fetched them and no MTDS operation fetches per-day
market data for them under that venue.** The only MTDS writer emitting `instrument_type=SPOT_ASSET` is
`oracle_prices_handler`, and it writes under the SYNTHETIC venues `CHAINLINK` / `PYTH`, keyed by the Chainlink
aggregator contract address / Pyth feed id — **never** under the protocol venue keyed by the catalogue's token contract
address. So a re-capture pass can never flip these cells to `captured`.

## THE TRAP (read before "fixing" this)

**Do NOT close these cells with `EXPECTED_NOT_ENOUGH_TVL`.** That reason is a member of `OUT_OF_COVERAGE_WINDOW_REASONS`
(`_honest_coverage_empty_reasons.py:531`) — the **same clipped-from-denominator bucket as `EXPECTED_INSTRUMENT_DELISTED`
(:530)**. Re-stamping the cells with it would remove them from the denominator again, reproducing the precise
honest-coverage distortion the false-delisting bug caused, just under an honest-sounding name. The superseded follow-on
in `defi_catalogue_available_to_false_delisting_2026_07_20` proposed exactly this — it is WRONG and has been corrected
there.

## Why leaving them pending is also not the answer

Blank-reason EU is `pending_fetch`: denominator-only, never numerator (`_honest_coverage_logic.py:94-95,157-158`) — a
scored GAP. The model explicitly rejects a long-lived dangling EU: `enumerate_expected_universe.py:1461-1465` says it
"reads as 'should have captured but never attempted' and overstates the coverage denominator", and the pool closer's
docstring frames its purpose as "driving EU → 0 honestly" (`_dex_swaps_queries.py:143-146`).

**So the current state is HONEST-BUT-INCOMPLETE** (strictly better than the false DELISTED it replaced — the gap is now
visible and scored rather than hidden), but it will not self-clear.

## The real decision (operator/architecture)

The two candidate resolutions are materially different and should be chosen deliberately:

- **(A) Don't seed them as expected at all.** If a reference-only holdings row has no per-day capture path by
  construction, arguably it should never enter the EXPECTED universe — the denominator should cover instruments we
  intend to capture. Narrowest, removes unsatisfiable cells at the source (the IS enumerator), no new reason needed.
- **(B) A NEW terminal reason** meaning "reference-only instrument, no market-data capture path" that stays IN the
  denominator as a legitimately-empty numerator (i.e. NOT added to `OUT_OF_COVERAGE_WINDOW_REASONS`). Keeps the rows
  visible/auditable but requires a new `EmptyConfirmedReason` + honest-coverage classification + emitters.

Separately, for the genuinely-capturable non-POOL types (LENDING / LST / risk_params), the fix is to **generalise
`catalogue_pool_ids_for_shard` beyond pools and add a residual emitter to those handlers** — that is a real capability,
not a labelling choice.

## Follow-on work (tracked)

- [ ] [DECISION] P1. **Operator/architecture call: (A) stop seeding reference-only holdings as expected, vs (B) a new
      in-denominator terminal reason.** Blocks everything below. Must NOT be resolved by reusing
      `EXPECTED_NOT_ENOUGH_TVL` (see THE TRAP).
- [ ] [BACKEND] P1. **Generalise `catalogue_pool_ids_for_shard`** (`_catalogue_filter.py:77`) beyond
      `instrument_type=='pool'` — the prerequisite for ANY non-pool residual reconciliation.
- [ ] [BACKEND] P1. **Add a per-instrument residual emitter** to the capturable non-POOL handlers
      (`lending_indices_handler`, `risk_params_handler`, `lst_rates_handler`, `evm_defi_collectors`) so their IS-seeded
      per-instrument EU cells can reconcile. `lst_rates_handler` additionally needs a per-instrument grain at all (it
      currently records `instrument_type='lst'` with no `instrument_id`).
- [ ] [DATA] P2. **Measure the per-instrument_type split of the 215,864 re-seeded cells** in the live prod `_index` (the
      instrument-level split 1,389/473/469 is verified from the catalogue; the CELL-level split is not).
- [ ] [DATA] P2. Check whether any affected `(venue, chain)` are in UAC `DEFI_INSTRUMENTS_NOT_YET_COLLECTED` (→ correct
      terminal state is `EXPECTED_ACQUISITION_PENDING`, self-healing) or covered by `PROTOCOL_PAUSE_WINDOWS` (→
      `EXPECTED_PROTOCOL_PAUSED`). Neither was verified in the read-only investigation.

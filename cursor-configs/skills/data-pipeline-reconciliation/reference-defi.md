# reference-defi — per-AG expansion for `/data-pipeline-reconciliation --asset-group defi`

Expansion of the `defi` row in [`SKILL.md`](SKILL.md) § 3d. Pointers + hazards only — the durable rules live in codex.

## Path grammar (this AG)

```
raw_tick_data/by_date/day={D}/pipeline_mode={mode}_{source}/asset_group=defi/
  venue={BARE_PROTOCOL}/chain={CHAIN}/instrument_type={it_lower}/data_type={dt}/
  {SYMBOLIC_CANONICAL_ID}.parquet
```

**defi is the only AG with a `chain=` key, and it sits AFTER `venue=`** (operator-locked ordering). `venue=` is the
**bare protocol** — `AAVE_V3`, never `AAVE_V3-ETHEREUM`, never `AAVEV3`. One parquet per instrument (target ruled
2026-07-18); filename == manifest key == the machine `instrument_id`.

> ⚠️ **On-disk leaf is the MACHINE id (a raw address / UUID), NOT the symbolic `canonical_instrument_id` (measured
> 2026-07-20).** The symbolic-leaf writer is **NOT YET shipped** (cutover register § 5) — today an ORCA pool leaf is a
> raw base58 address (`122FD4qsy8….parquet`) and a KAMINO lending leaf is a UUID. The symbolic
> `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500.parquet` form below is the **target grammar, not current reality** — do not
> flag every address-named POOL leaf as a leaf-shape regression, and do not byte-compare the stem to the content
> `instrument_id` column (`SKILL.md` § 3a defi carve-out).

Example (TARGET grammar — not yet on disk):
`raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_thegraph/asset_group=defi/venue=UNISWAP_V3/chain=ETHEREUM/instrument_type=pool/data_type=dex_pool_state/UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500.parquet`

Segment shape: `_AG_SEGMENT_SHAPE[DEFI]` —
`unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:158`.

## Buckets — resolve, never hand-build

`resolve_bucket_name(cloud, kind, asset_group="defi", deployment_env="prd")`:

| Layer     | `kind`                               | Resolves to                                   |
| --------- | ------------------------------------ | --------------------------------------------- |
| raw tick  | `market-data` (or alias `tick-data`) | `market-data-tick-defi-prd-{pid}`             |
| reference | `instruments-store`                  | `instruments-store-defi-prd-{pid}`            |
| features  | `features`                           | `features-defi-prd-{pid}` (`onchain/` prefix) |

Verified in `unified-trading-pm/configs/cloud-providers.yaml:93-102` and `:59-63`.

**`market-data-tick-defi-prd-{pid}` is the ONE consolidated defi bucket** — `data_type` lives in the path, not in a
bucket name, and it is the only defi bucket with a live consolidator. The 10+ legacy per-`data_type` kinds (`dex-pools`,
`dex-swaps`, `evm-defi`, `solana-defi`, `eigenlayer-rewards`, `gas-fees`, `lst-rates`, `perp-funding`,
`lending-indices`, `oracle-prices`, `liquidations`) were **removed from the yaml** 2026-07-10/12/13/16 and the buckets
deleted — see the removal comments at `cloud-providers.yaml:112-135`. Passing any of them as a `kind` now **raises**
(`bucket_naming.py:426-431`). That is correct behaviour, not a bug to work around.

## Shard atom + (KEY)

`[pipeline_mode, date, asset_group, venue, chain, instrument_type, data_type, instrument_id, source]` — grain pattern #1
(flat-per-contract), one parquet per instrument.

## Instrument-id grammar — the TWO-ID model (Option A, INTENTIONAL, not a gap)

defi alone composes the venue and chain into the id:

| Field                     | Shape                                                                                                   | Example                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `canonical_instrument_id` | symbolic `VENUE-CHAIN:TYPE:SYMBOL` — no addresses, on-chain token case **preserved** (`aUSDC`, `stETH`) | `AAVE_V3-ETHEREUM:LENDING:aUSDC`                                              |
| `instrument_id`           | address-anchored machine key                                                                            | POOL → `pool_address.lower()`; SPOT_ASSET → `spot_asset:{chain}:{token_addr}` |

POOL canonical keys are **3-segment with the fee inside the symbol**: `…:POOL:USDC-WETH-500`.

> **The divergence between the two ids is the design, not drift.** Do not report it as a finding — it is on the accepted
> exception list (`SKILL.md` § 2c).

> **6 cross-chain pool-address collisions exist.** Consumers MUST key on the chain-unique `canonical_instrument_id`; the
> bare `instrument_id` collides **by design**. If your comparison keys on `instrument_id`, you will merge distinct
> chains' pools into one row.

## Catalogue (surface 4)

`instruments-store-defi-prd-{pid}/prod/catalog.parquet` (live) — plus an **ORPHAN stale `prd/catalog.parquet` shadow**
in the same bucket (note `prd/` vs `prod/`). Read the `prod/` one; report the shadow as an orphan finding once.

## HAZARDS

### H1 — CRITICAL PROBE HAZARD: Solana AMM venues write `instrument_type=solana_amm_pool`, NOT `pool`

This exact slip produced a **false "twin absent" verdict** during the 2026-07-20 audit.

```python
"kamino": "solana_vault",      # ← NOT solana_amm_pool, NOT pool
"orca": "solana_amm_pool",
"raydium": "solana_amm_pool",
"phoenix": "solana_amm_pool",
```

— `market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py:229-233`
(`_SOLANA_DEX_ITYPE_STR`, verified 2026-07-20).

A probe using `instrument_type=pool` returns **ZERO** for ORCA / RAYDIUM even though **14k+ canonical objects exist**
(measured 2026-07-20). **And KAMINO's dex-pool twin is under `instrument_type=solana_vault`, not `solana_amm_pool` and
not `pool`** — a probe set missing `solana_vault` reproduces the exact false-absence this hazard exists to prevent (H2:
KAMINO/SOLEND are DO-NOT-DELETE). Because a delete suggestion's five-part proof turns on "does the canonical twin
resolve", a wrong-vocabulary zero converts directly into a **destructive** `yes-twin-confirmed`→ delete recommendation
for data that was never duplicated. Enumerate the full instrument_type vocabulary from the **writer map**
(`_SOLANA_DEX_ITYPE_STR`) **and** the manifest's observed `instrument_type` distribution — never from
`canonical_path_templates("defi")`, which hands you `{instrument_type}` **placeholders**, not values (see the known-good
spot-check).

### H2 — `dex_pools/` + `lending_indices/` are DO-NOT-DELETE

The delete order in two live plan docs is **stale** — see
`plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`. The canonical twin is a **partial overlap**, not
a duplicate: ORCA / RAYDIUM have canonical objects, but **KAMINO and SOLEND have NONE** — for those the legacy objects
are the only copy. execution-service still references the legacy shape at runtime. Executing the delete destroys data.
This is a **human-only hard stop** (`SKILL.md` § 4b).

Related precedent: an R5 **content** verify overturned a DUP verdict that would have destroyed **32 legacy-only high-TVL
Raydium pools** (XMR/USDC ~$47M, BNB/USDC ~$18M). Path-shape similarity is not evidence of duplication.

### H3 — interim flat `LENDING` on market/event data_types is NOT non-canonical

**CORRECTION 2026-07-20 (operator D2):** Decision **D** is now **RULED** — defi market/event flat `LENDING` keying is a
**FULL retire**. It is `migration_pending` (the retire is gated on
`plans/active/defi_lending_writer_retire_prerequisite_2026_07_20.md`), **NOT an open question**. The skill does **NOT**
REFUSE it and does **NOT** flag it — do **not** flag `lending` on `lending_indices`, `liquidation_events`,
`flash_loan_events`, or `position_data`. Only `holdings` uses the `A_TOKEN` / `DEBT_TOKEN` split. Re-reporting this is a
suppressed accepted exception. _(Superseded: previously logged here as "Decision D is unruled" / "PARKED — pending
decision D".)_

### H4 — capture is currently STOPPED; the manifest rebuild CRASHES

- 11 collect + 3 forward crons **PAUSED ~40 days**. Recency gaps are expected; do not report them as capture failures.
- The manifest rebuild crashes in the CF-11 honest-absence re-emit with `MalformedRowKeyError` — **4.55M of 43.5M
  `_index` rows (~10%) carry a blank `instrument_id` as legitimate cell-level honest-absence**. A blank `instrument_id`
  is not automatically a defect; classify per `codex/02-data/honest-absence-downstream-handling.md`.

### H5 — a legacy GLUED-VENUE FLAT tree INSIDE `raw_tick_data/` that discovery cannot see

```
raw_tick_data/by_date/day={D}/asset_group=defi/venue={VENUE}-{CHAIN}/ticks_migrated_{ISO}.parquet
```

No `pipeline_mode=`, venue+chain **glued**, no `chain=` / `instrument_type=` / `data_type=` keys. `parse_defi_object`'s
`_PAT_DEFI` returns `None`, so **discovery = 0** and the R3 reshape never saw it. Two related legacy shapes ARE in the
templates (`possible_manifest.py:185-195`: the no-asset-group 2024-05 shape and the `venue={venue}-{chain}` overload) —
but the flat `ticks_migrated_*.parquet` tail is not parsed. Probe for it explicitly; report as orphan-class per
`codex/02-data/orphan-object-detection.md`.

### H6 — axis-value census: the manifest carries duplicate and non-canonical vocabulary

Measured (SHIPPED + LIVE): **76 venues** including `AAVE` / `AAVEV3` / `AAVE_V3` and `COMPOUND` / `COMPOUND_V3` dupes ·
**17 instrument_types** (11 non-canonical) · **36 data_types** (10 non-canonical, incl. `dex_pools` → `dex_pool_state`)
· **24 chains** (3 non-canonical: `HYPERLIQUID` → `HYPERLIQUID_L1`; `KALSHI_PERP` / `POLYMARKET_PERP` leaking in from
prediction).

Quantified worklist: `POOL`→`pool` 13,868 · `LENDING`→`lending` 179,164 · `PERPETUAL`→`perpetual` 4,221 ·
`AAVEV3`/`AAVE` →`AAVE_V3` 64,218 · `MORPHOVAULTS`→`MORPHO` 50,266 · `COMPOUND`→`COMPOUND_V3` 13,904 · **`''`/NULL
instrument_type 4.49M UNRESOLVED**.

> The **case** rows here (`POOL`→`pool` etc. in the manifest **column**) are axis **C2a**. **CORRECTION 2026-07-20
> (operator D1):** C2a is now **RULED** — the canonical TARGET is **UPPERCASE** (catalogue enum), but it is **NOT yet
> implemented**: the column is `migration_pending` (measured 2026-07-20: mixed on disk — defi carries both cases). So
> the skill compares the `instrument_type` column **case-INSENSITIVELY** and emits **NO** casing finding during the
> migration_pending window (flagging lowercase-today would false-flag all un-migrated data); post-migration the column
> is enforced UPPERCASE. Do **not** propose a casing migration from this skill (`SKILL.md` § 3e). _(Superseded:
> previously logged here as "axis C2a, which is UNRULED".)_ The **path** segment (lowercase) and the **id** middle
> segment (UPPER) are settled and **always** enforced.

### H7 — coverage denominator: 63.9M, not 1.38M

`expected_unattempted` seed is **63.9M** (not the historical "1M safety-cap" slug), gated behind purging 1.79M
duplicates and ~219.5K phantoms. `instruments_completion_tracker` still derives coverage from the understated **1.38M**
denominator. **Never quote a defi coverage % derived from 1.38M.** Name the formula
(`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` EXCLUDED) and
mark it a lower bound.

### H8 — other open defects (report, don't fix)

- 26 new defi venues (`_DEFI_VENUES` 63→89) rejected at UAC `validate_instrument_records`; fix `uac@f7314dc2` is
  DEPLOY-GATED behind an IS Dockerfile UTL base-image pin bump.
- `gas-fees` + `lst-rates` manifest/bucket split: the writer targets `market-data-tick-defi-prd` while the scanner
  resolved `kind="gas-fees"` (a confirmed-EMPTY dedicated bucket) — root-caused, not fixed.
- `source=` write-wiring is a RED gap in principle, but **date-qualify it** — the general blank-source claim was **NOT
  reproduced** on the 2026-07-20 sampled day (0 blank `source` of 64,009 rows on day=2026-04-14). Report it as
  cell-specific / historical, not the current general state, unless you measure blanks on your own sampled day.

### H9 — expected-universe vocabulary desync (H1 on the EXPECTED side)

RAYDIUM `instrument_type=pool` / `POOL` rows sit `expected_unattempted` in the manifest while the writer emits
`instrument_type=solana_amm_pool` (`captured`). The `pool`/`POOL` expected rows are therefore **permanently
unsatisfiable** and inflate the coverage **denominator** (a lower-bound-worsening artifact, on the expected side).
Report it; do not treat the unsatisfiable expected rows as a capture failure.

### H10 — manifest `pipeline_mode` ↔ `source` desync

Measured rows carry `pipeline_mode=batch_onchain_rpc` with `source=onchain_subgraph` — the SOURCE-AWARE
`{mode}_{source}` invariant (`codex/02-data/pipeline-mode-partition.md`) is broken for these rows. Report as a typed
finding; do not silently "correct" either field.

## Known-good spot-check — run BEFORE trusting any absence result

**This is the H1 lesson, generalised. Do not skip it on defi.**

1. Enumerate from `canonical_path_templates("defi")` —
   `unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:352`. It appends the defi-specific legacy
   shapes (`:185-195`) that no other AG has, and emits both `batch_` and `live_` prefixes per source (`:315-336`).
2. Read the **actual `instrument_type` vocabulary** from the **writer map** (`_SOLANA_DEX_ITYPE_STR`,
   `dex_pools_handler.py:229-233`) **plus** the manifest's observed `instrument_type` distribution — the templates give
   STRUCTURE (`{instrument_type}` placeholders), never values, so this step is **not** doable from
   `canonical_path_templates` alone. Confirm both `solana_amm_pool` (ORCA/RAYDIUM/PHOENIX) **and** `solana_vault`
   (KAMINO) are in your probe set alongside `pool`. If any is missing, those venues' results are false zeros.
3. Confirm your probe places `chain=` **after** `venue=`. A `chain=`-first probe returns zero everywhere.
4. Pick one `(date, venue, chain)` known-captured from the manifest and confirm your probe returns non-zero.
5. Only then treat a zero as a finding — and even then, a delete suggestion needs the full five-part proof, including a
   **content** verify (H2).

## Census / vocabulary nuance

Added 2026-07-20 — the in-session distinct-value census (`codex/02-data/reconciliation-census-and-compute-tiers.md` §
1).

- **`chain=` is a LIVE census axis (defi is the only AG with one)** — enumerate the distinct `chain=` set from the
  manifest column and the GCS path segment and badge each against `MAINNET_CHAIN_IDS` keys (`registry/chain_env.py:10`);
  an out-of-vocab value (H6's `HYPERLIQUID`→`HYPERLIQUID_L1`, or the prediction-leak `KALSHI_PERP` / `POLYMARKET_PERP`)
  is a `non_canonical_axis_value`, never delete-eligible.
- **`instrument_type` is compared CASE-INSENSITIVELY** — C2a is RULED UPPERCASE-target but `migration_pending` (mixed on
  disk today), so the census emits **NO** casing finding during the window (H6; `SKILL.md` § 3e).
- **The census `instrument_type` vocabulary MUST include `solana_amm_pool` AND `solana_vault` (KAMINO), never just
  `pool`** — see H1 (writer map `_SOLANA_DEX_ITYPE_STR`); never re-derive the values from
  `canonical_path_templates("defi")`, which returns `{instrument_type}` placeholders, not values.

## Cross-links

`SKILL.md` · `codex/02-data/defi-canonical-naming-ssot.md` · `codex/02-data/defi-data-types-catalog.md` ·
`codex/02-data/four-surface-reconciliation-procedure.md` · `codex/02-data/reconciliation-finding-taxonomy.md` ·
`codex/02-data/gcs-and-manifest-delete-safety-protocol.md` · `codex/02-data/non-canonical-path-inventory.md` ·
`codex/02-data/orphan-object-detection.md` · `codex/02-data/honest-coverage-model.md` ·
`plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`

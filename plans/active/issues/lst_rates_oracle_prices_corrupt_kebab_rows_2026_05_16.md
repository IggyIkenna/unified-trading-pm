---
title:
  "lst-rates + oracle-prices canonical manifests contain CORRUPT legacy kebab rows (venue=data_type literal, chain
  empty) — 3,486 phantoms to delete"
created: 2026-05-16
author: ikenna-slot-2
resolved: 2026-05-16
resolution:
  SHIPPED — Option D at `instruments-service@70849b6`
  (`scripts/reconcile_corrupt_kebab_rows_lst_rates_oracle_prices_2026_05_16.py`); applied 2026-05-16 20:00-20:01 UTC;
  lst-rates 19,740→16,620 rows + oracle-prices 10,962→7,110 rows; post-apply groupby venue returns only real venues.
source:
  - gs://lst-rates-central-element-323112/_index/availability_index.parquet
  - gs://oracle-prices-central-element-323112/_index/availability_index.parquet
  - plans/archive/issues/lending_indices_data_type_vocabulary_drift_2026_05_16.md (companion — vocab drift root cause)
  - instruments-service/scripts/canonicalize_defi_manifest_data_types_2026_05_16.py (IS@b2726c6)
severity: P1 — 3,486 phantom rows claim `capture_status=captured` but venue/chain shape makes them unsalvageable
locked_by: live-defi-rollout
locked_since: 2026-05-16
---

## What I found

While investigating the systemic kebab/snake data_type drift across 6 DeFi canonical manifests (see archived
`plans/archive/issues/lending_indices_data_type_vocabulary_drift_2026_05_16.md`), a deeper drill-down into the kebab
`venue` column for the 3 empty-chain buckets revealed **2 of them have garbage venue values**:

| Bucket          | Kebab rows | Kebab venue distribution                   | Verdict                                                          |
| --------------- | ---------- | ------------------------------------------ | ---------------------------------------------------------------- |
| `lst-rates`     | 1,560      | `venue=LST_RATES` (100%)                   | ❌ **CORRUPT** — venue literal == data_type literal (uppercased) |
| `oracle-prices` | 1,926      | `venue=ORACLE_PRICES` (100%)               | ❌ **CORRUPT** — venue literal == data_type literal (uppercased) |
| `perp-funding`  | 3,298      | `venue=HYPERLIQUID` (1,685), `GMX` (1,613) | ⚠️ partial — venue real, just chain empty                        |

The 1,560 `lst-rates` and 1,926 `oracle-prices` kebab rows have the data_type LITERAL (uppercased + underscored) put
into the `venue` column. `LST_RATES` and `ORACLE_PRICES` are not real venues — Lido / Ether.fi / Coinbase / RocketPool /
Jito / Marinade are the real LST venues; Chainlink / Pyth / Uniswap-TWAP are the real oracle venues.

Combined with empty `chain` and the kebab `data_type` value, these rows form a **complete corruption signature**:

```
date=<YYYY-MM-DD>
venue=LST_RATES         # garbage — actual venue lost
chain=""                # empty — actual chain lost
data_type=lst-rates     # kebab (deprecated form)
instrument_type=lst     # populated
capture_status=captured # claims a parquet exists somewhere
```

But the path-derived GCS prefix from these field values is:
`gs://lst-rates-{pid}/day=<date>/category=defi/venue=LST_RATES/chain=/instrument_type=lst/data_type=lst-rates/`

This prefix has NO matching parquet on disk (manually verified via `gsutil ls`). The rows are full phantoms.

## Why it matters

1. **Manifest inflation**: 3,486 rows claim `captured` status that's unsalvageable. Any consumer counting "DeFi manifest
   coverage %" inflates its numerator by these phantoms.
2. **Slot 5 / slot 6 Solana carry-staked-basis correlation**: per `defi_master_2026_05_07.md` line 343 ("Solana LST MTDS
   gap"), `lst-rates` is reported sparse — these 1,560 corrupt rows likely contribute to the apparent gap. The
   `MARINADE` and `JITO` rows (real) cover Solana correctly; the `LST_RATES` rows do not. Deleting them shows the true
   coverage state.
3. **Option A vocab migration unsafe for these 2 buckets**: my `canonicalize_defi_manifest_data_types_2026_05_16.py`
   (IS@b2726c6) would flip the data_type column kebab→snake but leave the corrupt venue/chain intact. That would convert
   "kebab-with-garbage-venue" into "snake-with-garbage-venue" — same problem, different label. Do NOT run `--apply` on
   `lst-rates` or `oracle-prices` until corruption resolved.
4. **Root cause hypothesis**: these rows were written 2026-04-13T15:14:51 UTC by some legacy migration script that put
   the data_type literal in the venue column (possibly a placeholder filling pattern). The 2026-04-13 timestamp matches
   the lst-rates + oracle-prices kebab-form emission window exactly — so likely SAME migration as the data_type drift,
   just compounded by venue/chain misalignment.

## Why it matters NOT (caveat)

These rows do NOT block May-23 cutover — the snake-form rows (16,620 in lst-rates, 7,110 in oracle-prices) carry the
real coverage. Deleting the corrupt kebab rows just cleans the manifest signal; no production data is lost.

## Recommended decision

**Option D — DELETE corrupt rows from canonical manifest** (recommended):

Write `instruments-service/scripts/reconcile_corrupt_kebab_rows_lst_rates_oracle_prices_2026_05_16.py` that:

1. Reads each bucket's `_index/availability_index.parquet`
2. Filters to rows where `data_type ∈ {"lst-rates", "oracle-prices"}` AND `venue ∈ {"LST_RATES", "ORACLE_PRICES"}` AND
   `chain == ""`
3. On `--dry-run` (default): reports per-bucket row count + sample 3 rows
4. On `--apply --confirm`: drops these rows from the dataframe + writes back via v8-tolerant `df.to_parquet`
5. Idempotent re-runs (no rows to drop → no-op)

This is ~80 lines + 5 unit tests. Different concern from canonicalisation (corruption vs vocabulary). Operator-VM
runtime ~30 sec wall-clock per bucket.

**Option E — Re-classify corrupt rows as `attempted_failed` with typed reason**:

Less destructive: flip `capture_status` from `captured` → `attempted_failed` + set `error_reason = SOURCE_RETURNED_ZERO`
(or a new `LEGACY_CORRUPT_VENUE_LITERAL` reason). Keeps the row provenance for audit but removes the inflation.

**Option F — Leave alone**:

3,486 rows is <1% of total DeFi manifest volume. Cost of cleaning vs operational benefit is low. May not be worth a
separate script if Option A + A.1 + phantom audit catch them anyway (the 3-LENDING.5-style reconciler at
`reconcile_lending_indices_phantom.py` would classify them as `SOURCE_RETURNED_ZERO` phantoms because the path-probe
returns zero blobs).

## Suggested owner

ikenna-slot-2 — minor cleanup; can pair with Phase B operator session for vocab-drift migration.

## Companion artifacts

- Vocab-drift archived issue: `plans/archive/issues/lending_indices_data_type_vocabulary_drift_2026_05_16.md`
- Canonicalisation script: `instruments-service/scripts/canonicalize_defi_manifest_data_types_2026_05_16.py`
  (IS@b2726c6)
- Phantom reconciler (template): `instruments-service/scripts/reconcile_lending_indices_phantom.py` (IS@88d48da)

execution: owner: "slot-4-ikenna (cross-slot pickup 2026-05-16); Option D shipped" cadence: "one-shot" verifier:
"lst-rates groupby venue returns only real venues (LIDO/ETHERFI/COINBASE/etc.); oracle-prices groupby venue returns only
real oracle venues" last_executed: "2026-05-16 20:01 UTC — instruments-service@70849b6"

## RESOLVED — 2026-05-16 (slot 4 cross-slot pickup)

**Option D shipped** at `instruments-service@70849b6` —
`scripts/reconcile_corrupt_kebab_rows_lst_rates_oracle_prices_2026_05_16.py`.

Closed-set filter: `data_type∈{kebab, snake}` + `venue==CORRUPT_LITERAL` + `chain==empty`. Filter handles both forms
because slot-4's earlier canonicalize_defi_manifest_data_types apply (19:44 UTC) had already written snake-form
duplicates of the corrupt rows to per-VM shards — script drops from canonical manifest AND rewrites the per-VM
canonicalize shards minus the corrupt rows so consolidator doesn't reintroduce them on next cycle.

Applied 2026-05-16 20:00-20:01 UTC:

- **lst-rates**: 19,740 → **16,620 rows** (dropped 3,120 = 1,560 kebab + 1,560 snake-shard)
- **oracle-prices**: 10,962 → **7,110 rows** (dropped 3,852 = 1,926 + 1,926)

Verified post-apply via `groupby venue`:

- `lst-rates`: ANKR, COINBASE, ETHENA, ETHERFI, JITO, LIDO, MAKER, MANTLE, MARINADE, PUFFER, ... (all real venues)
- `oracle-prices`: CHAINLINK, PYTH (the 2 real oracle venues)

Issue closeable at next archive sweep.

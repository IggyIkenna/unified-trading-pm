---
doc_type: issue
title: lst_rates + oracle_prices write timestamp-glued instrument_ids ({protocol}_{chain}_{daily_epoch})
summary:
  73 distinct captured instrument_ids in the live defi _index embed a per-day unix epoch instead of a stable
  per-instrument identifier — the same timestamp-glued anti-pattern the per-instrument migration removed for other
  data_types. Small blast radius (78/51.9M rows) but an ACTIVE write-path pattern in the lst_rates + oracle_prices
  handlers.
status: open
nature: issue
asset_group: defi
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, instrument-id, per-instrument-model, lst, oracle, glued-key]
related: [defi_consolidated_closeout_2026_07_18]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: worsening-slowly
depends_on: []
source:
  [
    "filed 2026-07-20 during DeFi LST/oracle canonical-write work; frontmatter completed 2026-07-21 to pass the schema
    gate",
  ]
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# lst_rates + oracle_prices write timestamp-glued instrument_ids

## What was measured (live index, via ADC read 2026-07-20)

Reading `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (51,917,421 rows) and
scanning `instrument_id` for the `_<10-digit>$` glued-epoch pattern found **73 distinct ids / 78 rows**, all
`capture_status=captured`, e.g.:

```
ethena_ETHEREUM_1782648000    ETHENA     lst_rates
etherfi_ETHEREUM_1782475200   ETHERFI    lst_rates
rocketpool_ETHEREUM_1782648000 ROCKETPOOL lst_rates
oracle_prices_1782388800      PYTH       oracle_prices
```

The suffixes (`1782388800`, `1782475200`, `1782561600`, `1782648000`, `1782734400`, `1782820800`) are **consecutive
daily unix epochs** (each 86400s apart, ~2026-06). So the id is `{protocol}_{chain}_{daily_capture_epoch}` — a NEW
"instrument" per protocol per day.

## Why it is wrong

The per-instrument canonical model wants a **stable** `instrument_id` (e.g. `ETHENA-ETHEREUM`) with the date carried by
the `day=` partition + the manifest `date` column — NOT the capture timestamp glued into the id. Gluing the epoch:

- explodes the id cardinality (one id per protocol per day) — defeats per-instrument dedup/coverage;
- makes `record_captured` grain non-stable across days (the same real instrument reads as a new one daily);
- `oracle_prices_1782388800` is worse — the id does not even name the FEED (should be the Pyth feed/asset, e.g.
  `PYTH-SOLANA-<pair>`), only `oracle_prices_<epoch>`.

This is the same timestamp-glued anti-pattern the R3 per-instrument migration removed for `dex_pool_state` etc. — it
survived in the `lst_rates` + `oracle_prices` write path.

## Update 2026-07-20 — the pattern is BROADER than lst_rates/oracle

Sampling a real PROD instrument for the `/data-pipeline-check-mtds` run surfaced `aave_v3_ARBITRUM_20260622_072851` at
`…/venue=AAVE_V3/chain=ARBITRUM/instrument_type=lending/data_type=lending_indices/aave_v3_ARBITRUM_20260622_072851.parquet`
— i.e. **AAVE_V3 `lending_indices` ALSO uses `{protocol}_{chain}_{YYYYMMDD}_{HHMMSS}` (capture-datetime) ids**, not just
lst_rates/oracle_prices. So the glued-id anti-pattern spans lending as well. Widen the fix scope + the re-scan
accordingly (the `_<10-digit>$` regex in the original measurement under-counts the `_YYYYMMDD_HHMMSS` form).

## Blast radius

Small NOW (78 / 51.9M rows, ~6 days of late-June captures across ~12 LST protocols + 1 PYTH oracle row) but the WRITE
PATH still emits this shape, so it grows one-id-per-protocol-per-day going forward. `_migrated_` = 0 and
`ticks_migrated_` = 0 in the same index (the two other orphan classes are clean).

## Fix direction (NOT applied — outside the DeFi-catalogue closeout scope; LST/oracle workstream owns it)

Change the `lst_rates` + `oracle_prices` canonical id derivation to a stable `{PROTOCOL}-{CHAIN}` (lst) /
feed-identifying (oracle) id and let `day=` carry the date, mirroring the per-instrument id derivation the other DeFi
data_types already use. Then re-migrate the 78 existing glued rows to the stable id (idempotent, same UPSERT path as
R3). Verify by re-scanning the index for `_<10-digit>$` → 0.

## Provenance

Found during the DeFi-catalogue-closeout index verification (`defi_consolidated_closeout_2026_07_18.md` Progress Log,
2026-07-20). The `_solana_stake_pool.py` untracked LST artifact seen in the MTDS tree the same day is likely part of the
same LST workstream — worth checking whether it emits this id shape.

## Root cause + TRUE scope (2026-07-21) — SYSTEMIC across ~15 handlers, bigger than first filed

**Root cause:** the filename (which becomes the manifest `instrument_id`) is built as `f"{...}_{ts_label}.parquet"`
where `ts_label = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")` — the WALL-CLOCK capture time. The `date={YYYY-MM-DD}/`
is ALREADY in the path, so `ts_label` is redundant AND non-idempotent (each re-run writes a NEW file instead of
overwriting → id explosion, un-re-fetchable, breaks skip-if-fresh).

**Grep-confirmed sites (`_{ts}` / `_{ts_label}` / `_{noon_ts}` in the filename), ~15 handlers:**
`oracle_prices_handler:378`, `lst_rates_handler:570,691`, `solana_defi_handler:650,651`, `risk_params_handler:655`,
`evm_defi_handler:214`, `lending_indices_handler:433,866`, `dex_swaps_handler:519`, `liquidations_handler:647`,
`_dex_pools_subgraph:365`, `_perp_funding_kalshi_polymarket:323`, `_perp_funding_gmx:264,280`,
`deribit_options_chain_handler:517` (cefi — separate).

**This is a SYSTEMIC per-instrument-model gap, not a 3-handler fix.** Correct fix (bigger than the ratified scope
implied): a SHARED stable-filename helper (drop `ts_label`; name by the per-instrument identity — per-reserve for
lending, per-feed for oracle, per-pool for dex, per-token for lst) that all ~15 handlers adopt, + a full re-migration
renaming the existing `{...}_{ts}.parquet` objects to the stable id (idempotent, keep-latest). Each handler's correct
grain differs (some write one file per protocol-chain, some per-instrument), so this needs per-handler grain analysis +
a shared helper, then one migration pass — a focused project, not a marathon-tail edit. The minimal-safe first step
(drop `ts_label` → stable `{protocol}_{chain}` per date, idempotent overwrite) removes the glued timestamp everywhere
but keeps the current (coarse) grain; the per-instrument sharding is the finer follow-up.

## MIGRATION IN FLIGHT (2026-07-21) — re-shard DONE-logic PROVEN + running; RESUME = rebuild manifest + verify

**Operator ruling 2026-07-21: fix write path + re-migrate. Operator also asked whether the pool id is canonical.**
ANSWER (verified against the builder + live data): the canonical symbolic pool id IS the human
`venue:instrument_type:base-quote-fee` — e.g. `UNISWAP_V3-ETHEREUM:POOL:COMP-WETH-100` (filename
`COMP-WETH-100.parquet`, `token_a=COMP token_b=WETH fee_rate_bps=10000`), produced by
`unified_api_contracts/canonical/crosscutting/defi.py::_symbolic pool id`. `…:POOL:0x<addr>` (Balancer) and
`…:LENDING:<uuid>` (Kamino) are the builder's INTENDED FALLBACK ("the symbol IS the pool address — no pair/fee encoded —
always non-empty + reversible") for pools/markets whose tokens can't resolve to a clean symbol. So the DATA's per-row
`instrument_id` column is ALREADY canonical (human where resolvable, address/UUID fallback otherwise). The DEFECT is
only the coarse glued FILENAME (`{protocol}_{chain}_{capture_ts}`).

**Measured true scale (from the live `_index`):** 1,755 captured glued coarse files → **406,724 per-instrument groups**,
BUT R3 already created MOST of the per-instrument twins from other coarse files for the same (venue,chain,date) — so the
migration is **mostly idempotent renames + ~a few thousand genuinely-new twins** (the Solana lending/lst R3's matcher
missed: `kamino_lending_SOLANA_`, `lst_rates_marinade_` — the extra `_lending_`/`_rates_` segment breaks the
`{venue}_{chain}_` prefix). Measured mid-run: present≈201k, new twins≈6.5k, retired≈473.

**The re-shard (PROVEN end-to-end via an oracle_prices canary):** for each glued coarse file → group by the
already-canonical `instrument_id` column → write one `{sanitize_defi_symbol(SYMBOL)}.parquet` per instrument (reusing
`migrate_defi_batch_to_per_instrument.leaf_for_instrument_id`) → retire the coarse original to
`_migrated_{orig}.parquet` (proof-gated: only after every attributable group has a twin). Idempotent (exists()-gated).
Canary VERIFIED: `oracle_prices_1782388800` → 7 twins `BTC_USD.parquet`/`ETH_USD.parquet`/…

- original retired. Harness: `market-tick-data-service/scripts/one_offs/reshard_glued_defi_ids_2026_07_21.py` (local,
  index-driven, decoupled 16-reader/64-writer pool; NOT the R3 tool because R3's matcher misses the Solana naming — this
  is index+column-driven so it handles all 1,755).

**RESUME (fresh session):**

1. Confirm the apply finished (log `reshard_apply2.log` SUMMARY, or re-run the harness `--apply` — idempotent, skips
   present + already-`_migrated_`).
2. **Rebuild the manifest** for the affected data_types so the glued ids leave the index and the twins enter:
   `rebuild_defi_manifest --bucket market-data-tick-defi-prd-central-element-323112 --start-date 2020-01-01 --end-date 2026-12-31`
   (default `--reemit-absence` OFF, mtds@05ad49f7). The `_migrated_` originals are skipped by the Defect-A `_`-prefix
   guard.
3. **VERIFY 0 glued ids**: re-scan the fresh `_index` for `instrument_id` matching `(_\d{8}_\d{6}|_\d{10})$` with
   capture_status=captured → must be 0.
4. **Delete the `_migrated_` markers** (operator-authorized deletes; proof-gated: only where the per-instrument twins
   exist) — cleanup.

**FORWARD write-path fix (still open):** the ~6 handlers (lending_indices/lst_rates/oracle_prices/liquidations/
dex_swaps/dex_pool_state Solana paths) still have a residual coarse `file_name=f"{...}_{ts_label}"` write alongside
their `write_defi_rows` per-instrument path (the compound_v3 file dated 2026-07-20 proves it). Route those residual
paths through `write_defi_rows` (or drop the `_{ts}`) so no new glued files appear when capture resumes. DeFi capture is
currently STOPPED, so no new ones are being written now.

## FINAL STATE 2026-07-21 (after 3 idempotent apply passes) — 98.7% DONE, precise remainder

- **1,733 / 1,755 glued coarse files RE-SHARDED + retired to `_migrated_`** — their per-instrument twins are present
  (mostly already created by R3 from sibling coarse files: measured present≈305k twins, ~8.4k genuinely new written for
  the Solana lending/lst R3's matcher had missed). Verified end-to-end on the oracle canary.
- **22 `dex_pool_state` files remain LIVE at the legacy `category=defi` path** (my harness now probes BOTH
  `asset_group=`/`category=`). Their twins are present EXCEPT ~28 instruments whose `leaf_for_instrument_id` symbol
  raises on `blob.exists()` (a bad GCS object name from a problematic dex_pool symbol, OR a persistent GCS 4xx/5xx —
  consistent 28 across 3 passes, so NOT transient). The proof-gate CORRECTLY refuses to retire these 22 (can't confirm
  those 28 twins exist → won't drop the coarse original).

**RESUME (precise):**

1. ✅ **DONE 2026-07-21 — the 28 diagnosed and fixed.** Root cause: all 28 are a single `WETH`-paired Uniswap V3 pool
   (recurring across BASE/ARBITRUM/OPTIMISM, multiple days) whose counterparty is a spam/"zalgo" token — a symbol
   stuffed with ~1000 Unicode combining marks. Confirmed via a parallelized, exception-logging diagnostic run (0 errors
   on 14,914 real instrument checks) followed by an instrumented `--apply` run that captured the actual GCS exception:
   `BadRequest: 400` because the sanitized leaf was **1,201 bytes**, over GCS's 1024-byte object-name cap. Fixed in
   `_sanitize_defi_symbol` (`canonical_write.py`) — strips every Unicode combining-mark codepoint
   (`unicodedata.category` in `Mn`/`Mc`/`Me`) then caps the result at 200 bytes; hardens both this migration AND the
   live per-instrument writer against any future zalgo-stuffed on-chain token symbol. Pinning test added. Shipped
   `market-tick-data-service@781204d8` (dirty-deps direct-push carve-out — unified-trading-library had unrelated
   concurrent-agent WIP blocking quickmerge's pre-flight; not touched). Migration re-run in progress to finish retiring
   the last 22 files.
2. **Rebuild the manifest** (VM-scale, ~hrs — run on a `canonical-migration` VM, not in-session):
   `rebuild_defi_manifest --bucket market-data-tick-defi-prd-central-element-323112 --start-date 2020-01-01 --end-date 2026-12-31`
   (reemit OFF, the mtds@05ad49f7 default). `_migrated_` originals skipped by Defect-A.
3. **Verify 0 glued ids** in the fresh `_index` (`instrument_id ~ (_\d{8}_\d{6}|_\d{10})$` + captured → 0; expect ~22
   until step 1 completes the last files).
4. **Delete the `_migrated_` markers** (operator-authorized; proof-gated: only where the per-instrument twins exist) —
   the retired coarse originals are dead weight once the manifest is rebuilt.
5. **`category=defi` → `asset_group=defi` PATH canonicalization** — the 22 (and any other `category=` legacy objects)
   are at the non-canonical `category=` path. That path migration is SEPARATE from this filename fix (out of scope here)
   — track it under the broader canonicalization.

Harness (durable, resumable, idempotent):
`market-tick-data-service/scripts/one_offs/reshard_glued_defi_ids_2026_07_21.py`.

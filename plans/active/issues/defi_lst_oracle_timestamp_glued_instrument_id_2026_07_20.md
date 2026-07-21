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
source: ["filed 2026-07-20 during DeFi LST/oracle canonical-write work; frontmatter completed 2026-07-21 to pass the schema gate"]
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

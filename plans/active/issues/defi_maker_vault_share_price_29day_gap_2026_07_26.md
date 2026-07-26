---
doc_type: issue
title: MAKER's vault_share_price manifest has a genuine, unexplained 29-day gap (2026-06-22..2026-07-20)
summary: >-
  Found while verifying defi_satellite_ao_dispatch_batch2_2026_07_26.md's "90-day lst-rates backfill for
  ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER" todo. MAKER is NOT actually part of lst_rates_handler.py -- it is registered
  under vault_share_price_handler.py (data_type=vault_share_price), a different handler entirely. The 5 genuine LST-rate
  venues (ANKR/STADER/STAKEWISE/SWELL/MANTLE) show 90/90 days captured already (no backfill needed -- the daily cron
  organically covers the window). MAKER's real data type, vault_share_price, has a genuine, completely absent (not
  attempted_failed) 29-day gap: 2026-06-22 through 2026-07-20 inclusive. Not root-caused this pass -- flagging with
  exact evidence rather than guessing at the cause.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, mtds, lst-rates, vault-share-price, maker, manifest-gap]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/active/issues/defi_five_never_captured_venues_fix_2026_07_22.md,
  ]
created: 2026-07-26
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-8, data_engineering) while verifying defi_satellite_ao_dispatch_batch2_2026_07_26.md's LST
    rates backfill todo -- direct manifest reads against market-data-tick-defi-prd's availability_index.parquet
    (column+filter pushdown, not a full-corpus read).",
  ]
resolved_by:
locked_by:
locked_since:
---

# MAKER's vault_share_price has a real 29-day manifest gap

## What I found

1. **MAKER is not an `lst_rates` venue.** `grep -rln '"MAKER"' market_tick_data_service/cli/handlers/` returns only
   `vault_share_price_handler.py` — `lst_rates_handler.py` never references MAKER.
   `load_evm_lst_contract_addresses_for_date` (the function `lst_rates_handler.py` actually uses) does not return a
   `MAKER` key for any date checked (2026-07-20/23/25, live-verified). MAKER's 87 legacy rows under
   `data_type=lst_rates` (2026-04-27..2026-07-22, `written_at` all clustered at `2026-07-23T01:30:05Z` — a single
   retroactive batch write, not organic day-by-day capture) look like a stale/legacy classification that correctly
   stopped being written once the writer's real `data_type=vault_share_price` classification took over — not a bug in
   `lst_rates_handler.py`.

2. **The 5 genuine LST-rate venues need NO backfill.** Direct manifest read (columns=[date,venue,data_type,
   capture_status,written_at], filters on venue+data_type — not a full-index load, see "measurement trap" below) shows
   ANKR/STADER/STAKEWISE/SWELL/MANTLE at 90/90 captured days for 2026-04-27..2026-07-25, all via the daily cron's
   organic day-by-day writes (verified `uts-prod-mtds-collect-lst-rates-cron` healthy: last 4 Cloud Run executions
   2026-07-23..2026-07-26 all `Completed True`, vs. 2 `Completed False` on 2026-07-21/22 before the crash-loop fix
   `mtds@522185a6` landed). The 90-day RPC backfill the parent todo asked for was ALREADY organically complete for these
   5 — running it would have been ~2,340 wasted RPC calls.

3. **MAKER's real data type (`vault_share_price`) has a genuine gap.** Filtering the manifest to
   `venue=MAKER, data_type=vault_share_price`: 61/90 days captured in the 2026-04-27..2026-07-25 window, with a single
   contiguous missing block: **2026-06-22 through 2026-07-20 (29 days)**. Confirmed these are NOT `attempted_failed`
   rows silently mislabeled — a direct manifest query for exactly those 3 spot-checked dates (2026-07-23/24/25, the
   originally-suspected gap before the reclassification was found) returned a genuinely EMPTY DataFrame — the writer
   never even attempted these days, not a recorded failure. Days before 2026-06-22 and after 2026-07-20 (including the
   most recent 07-21..07-25) ARE captured, so this isn't an ongoing/current outage — it's a bounded historical gap.

## Why it matters

29 consecutive days of missing `vault_share_price` data for MAKER is a real coverage hole in the DeFi manifest,
independent of (and not fixed by) the LST-rates backfill work this was originally found while verifying. Not yet
root-caused — candidates not yet checked: a `vault_share_price`-specific crash-loop or outage during that exact window
(parallel to the LST-rates crash-loop this session already confirmed + fixed), a contract/RPC config change that
temporarily broke MAKER specifically within `vault_share_price_handler.py`, or a deliberate pause not yet documented
anywhere.

## Recommended decision

- [ ] [DIAG] P2. Root-cause the 2026-06-22..2026-07-20 MAKER `vault_share_price` gap — check
      `uts-prod-mtds-collect-vault-share-price-cron`'s (or the actual job name — verify via
      `gcloud scheduler jobs list --location=asia-northeast1 | grep -i vault`) execution history for that exact window
      for crash-loop/OOM symptoms, and check `vault_share_price_handler.py`'s MAKER-specific config/contract address for
      a change around 2026-06-22 or 2026-07-20. (repo: market-tick-data-service)
- [ ] [SCRIPT] P2. Once root-caused (and if the underlying cause is fixed): backfill the confirmed 29-day gap for MAKER
      under `data_type=vault_share_price`, manifest-verify `record_captured` for all 29 days. Blocked on the `[DIAG] P2`
      todo above. (repo: market-tick-data-service)

## Measurement trap (for the next reader)

`market-data-tick-defi-prd`'s `availability_index.parquet` is ~15GB uncompressed as a full-schema `pd.read_parquet` load
(matches the already-documented `mtds_backfill_vm_startup_oom_rc137_2026_07_14` finding) — a naive full read took over 5
minutes and 16GB+ RSS before being killed. Always use `columns=[...]` + `filters=[...]` (row-group predicate pushdown)
for a targeted query — the same filtered read above completed in seconds.

## Progress Log (append-only)

- 2026-07-26 (slot-8, `data_engineering`): filed while verifying `defi_satellite_ao_dispatch_batch2_2026_07_26.md`'s
  LST-rates backfill todo. Confirmed no backfill needed for the 5 genuine LST venues; confirmed MAKER's real gap is in a
  different handler/data_type than the parent todo assumed; did not attempt the RPC backfill (would have been wasted
  work) or root-cause the vault_share_price gap (out of scope for this pass — flagged with exact evidence rather than
  guessed at).

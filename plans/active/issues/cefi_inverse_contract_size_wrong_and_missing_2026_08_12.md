---
doc_type: issue
title: "CeFi inverse contract_size silently wrong (OKX/Deribit) and unresolvable (30/64 instruments) — 2026-08-12"
summary: >-
  Third root cause found while verifying the liquidations inverse-notional re-derive (see
  data_pipeline_alert_storm_root_cause_batch_2026_08_10.md P0): MDPS was silently defaulting every inverse contract's
  face value to 1 (correct by coincidence for Bybit/Kraken, wrong for OKX non-BTC alts and Deribit BTC — understated
  10x/100x) because Tardis's free instrument-enumeration endpoint never carries contractMultiplier and the paid tier
  that does isn't in this workspace's current subscription. Fixed via a reverse-engineered, sourced UAC registry
  (unified-api-contracts@49ad03df3d), wired into MDPS (market-data-processing-service@ae23ee5c03). A SEPARATE finding —
  30/64 target instruments got ZERO successful writes the entire re-derive run, not intermittent — splits into a BYBIT
  stale-id-format bug (RESOLVED: no fix needed, already-shipped code handles it) and an OKX-SWAP delisted-instrument
  catalogue-rollup gap (RESOLVED: new cefi-catalogue-promote VM launcher, dry-run + real run both clean, verified in
  prod). All that remains: a 4th liquidations re-derive to confirm the full chain end-to-end.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-api-contracts, market-data-processing-service, instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [contract_size, liquidations, tardis, instruments-service, cefi-inverse]
related: [data_pipeline_alert_storm_root_cause_batch_2026_08_10, cefi_consolidated_closeout_2026_07_18]
context_scope:
  [
    /plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    unified-api-contracts/unified_api_contracts/registry/cefi_inverse_contract_multipliers.py,
    market-data-processing-service/market_data_processing_service/app/adapters/cefi/liquidations_adapter.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers_chain.py,
  ]
created: 2026-08-12
last_updated: "2026-08-21"
author: claude-agent
source: "2026-08-12 continuation session, verifying the liquidations re-derive's manifest outcome"
priority: P0
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# CeFi inverse contract_size silently wrong and missing — 2026-08-12

## Background

After the two 2026-08-12 MDPS fixes (1d-scheduling spelling mismatch + OHLC-nullable schema fallback — see the P0 todo
in `data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`), the liquidations re-derive VM
(`mdps-backfill-cefi-20260812-135814`) ran the full 2020-01-01..2026-01-31 range (2223 dates) to a clean exit. Full
verification found two DISTINCT further problems, neither caused by either of that day's two fixes.

## Finding 1 — 30/64 target instruments got ZERO successful writes the entire run (not intermittent)

Re-measured post-run: 56,238 shard-rows freshly captured in the run's wall-clock window (13:00-19:00 UTC), across only
34 of the 64 target instruments. The other 30 have NO manifest trace for this run at all. Two separate causes:

**1a. BYBIT stale-id-format — RESOLVED to a root cause: 2 orphaned STALE files, not a live code bug.**
`BYBIT:PERPETUAL:BTCUSD` / `BYBIT:PERPETUAL:ETHUSD` (no hyphen, no `@INV`) cannot be produced by any current
Tardis-adapter code path — the adapter's `_build_canonical_perpetual_key`
(`instruments-service/instruments_service/reference_data/adapters/cefi/tardis/parsing.py:871-874`) always emits
`BYBIT:PERPETUAL:BTC-USD@INV`. MDPS itself never constructs instrument ids — it faithfully reads whatever is already in
the raw tick parquet's `instrument_id` column (`market_data_processing_service/app/core/live_workers_chain.py:953-1007`,
`app/adapters/base_adapter.py:462-483`); every id-construction path was ruled out. **Live-traced to source**:
`raw_tick_data/by_date/day=*/pipeline_mode=batch_tardis/asset_group=cefi/venue=BYBIT/`
`instrument_type=perpetual/data_type=liquidations/BTCUSD.parquet` and `ETHUSD.parquet` (bucket
`market-data-tick-cefi-prd-central-element-323112`) — the `instrument_id` COLUMN itself (not just the filename) is
baked-in bare `BYBIT:PERPETUAL:BTCUSD`/`ETHUSD`, single generation, `last_modified=2026-07-08T04:16:55Z`, no subsequent
generation on either object (verified via `gcs_describe_object`). Every SIBLING BYBIT instrument in the same date
directories carries `last_modified=2026-07-19T...` (a canonicalization sweep that ran 11 days later) — these two
FILENAMES (`BTCUSD.parquet`/`ETHUSD.parquet`) are orphans that BOTH the 2026-07-19 sweep AND the 2026-07-25/28
`cefi_migration_cutover_and_track8_completion` rewrite missed. **Corrected scope** (an earlier draft of this doc
understated this as "2 objects" — that was WRONG, based on checking only 3 sample dates; a full scoped per-date count
across the 2020-01-01..2026-01-31 re-derive range found **2,879 date-partitioned files carry this filename**
BTCUSD.parquet: 1,439 files, dates 2020-10-28..2026-01-31; ETHUSD.parquet: 1,440 files, same range — one file per day,
all sharing the identical stale bare `instrument_id` content. A further 331 of these objects turned out to carry an EVEN
OLDER schema vintage with no `instrument_id` column at all (just `symbol`/`underlying`) — real, non-empty data (hundreds
to thousands of rows each), not empty placeholders.

**RESOLVED WITHOUT ANY GCS MUTATION — the already-shipped Finding-2 fix (`market-data-processing-service@ae23ee5c03`)
already handles ALL 2,879 files correctly at runtime, live-verified.** A GCS content-rewrite script was written and its
dry-run confirmed the 2,879/331 split above, but before applying it, a faithful production-shaped test (constructing
`InstrumentInfo` exactly as `live_workers_chain.py` does — venue from the structural GCS path segment, `instrument_id`
from the column when present else path-derived, matching the documented "column is an authoritative override" behavior)
against 4 real objects (BTCUSD/ETHUSD × stale-column/no-column) showed all 4 already succeed and produce correct nonzero
notional. **Why**: BYBIT is registered as a `CEFI_INVERSE_CONTRACT_MULTIPLIER_UNIFORM` venue in the UAC registry
(contract_size=1 for every base asset, checked FIRST, no base_asset needed) — so the bad/absent id shape never blocks
contract_size resolution for BYBIT specifically, and `infer_cefi_quote_margin`'s step-6 bare-USD-quote heuristic (keys
off the `symbol` column, not `instrument_id`) resolves `margin_type=inverse` regardless of the id's shape. **The written
rewrite script was deleted (never committed) — it was real, correct, and safety-designed, but proven unnecessary by
direct evidence, and shipping a mutation script nobody needs to run is worse than not shipping it.** No further action
needed for Finding 1a.

**1b. OKX-SWAP delisted instruments — RESOLVED to the ACTUAL root cause (correcting an earlier wrong hypothesis in this
doc).** Tardis's own `/v1/exchanges/okex-swap` metadata confirms `AVAX-USD-SWAP` (availableSince 2021-11-25, availableTo
2026-07-08) and `XLM-USD-SWAP` (availableSince 2020-05-11, availableTo 2025-08-16) are REAL, historically-active,
now-delisted instruments — not fabricated/malformed ids. **Live GCS check across 5 representative in-window dates per
instrument** (bucket `instruments-store-cefi-prd-central-element-323112`,
`instrument_availability/by_date/day=<date>/pipeline_mode=batch_instruments_service/asset_group=cefi/venue=OKX-SWAP/instruments.parquet`,
`raw_symbol` column) confirmed `instruments-service`'s daily capture genuinely ran and correctly recorded BOTH symbols
throughout their ENTIRE active windows.

**An earlier draft of this doc then guessed "the rollup is silently dropping both symbols" — that guess was WRONG, found
by a follow-up live read of `catalog.parquet` itself.** Both rows ARE present and resolve fine on id/bounds:

```
OKX-SWAP:PERPETUAL:AVAX-USD@INV   available_from=2021-11-25  available_to=2026-07-08  contract_size=""  (blank)
OKX-SWAP:PERPETUAL:XLM-USD@INV    available_from=2020-05-11  available_to=2025-08-16  contract_size=""  (blank)
```

The actual defect: `contract_size` was only just added to `build_instrument_catalogue.py`'s `CATALOG_COLUMNS` (correctly
emitted at the by_date→catalogue write site). But the script's DEFAULT mode is `--mode incremental`, which only
re-derives instruments seen in a trailing self-widening window (`WINDOW_DAYS_MIN=21`); any prior-catalogue row for an
instrument OUTSIDE that window (i.e., already delisted) is copied through UNCHANGED as a frozen tail
(`_merge_incremental` branch 4) — only its `available_to` ever gets touched (branch 3, on first delisting). A delisted
row therefore keeps whatever `contract_size` its LAST incremental pass wrote, which for both these rows was before the
`contract_size` column existed. **`--mode full`** (a full by_date corpus re-walk, already a designed, existing mode of
this same script — not a new walk) would correctly backfill it, since the source by_date snapshots for both instruments
still carry `contract_size` (verified live, e.g. `Decimal('1')` on OKX-SWAP's last active day). **Fix: run one CeFi
`--mode full` catalogue rollup** — no code change needed. **Blast radius is CeFi-wide, not OKX-SWAP-specific**: measured
0/4,399 active derivative rows blank vs **271,838/279,233 delisted derivative rows (97.4%) blank** across DERIBIT
(263,782), BYBIT (897), OKX-FUTURES (5,344), KRAKEN-FUTURES (792), BITGET-FUTURES (274), BINANCE-DELIVERY/FUTURES
(196/198), etc. — every CeFi venue with delisted derivatives has this gap; one full rebuild fixes all of it. **Process
lesson for the future**: any new `CATALOG_COLUMNS` addition needs an immediate one-off `--mode full` run per
asset_group, not just waiting for the next scheduled incremental cron — the incremental engine cannot structurally
backfill a new field onto a frozen/out-of-window row.

**FIXED AND VERIFIED IN PRODUCTION (2026-08-13).** Added a new `cefi-catalogue-promote` category to
`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (mirroring the existing `defi-catalogue-promote`
pattern exactly — `deployment-service@a7561ac20c`). Dry-run first
(`canonical-migration-cefi-catalogue-promote-20260813-160254`, on-demand after 2 consecutive SPOT preemptions in
`asia-northeast1-c`): full 44,573-snapshot corpus walk, clean exit_code=0, monotonic guard
`new=433791 current=431649 decision=ACCEPT`. Then the real run
(`canonical-migration-cefi-catalogue-promote-20260813-165827`, on-demand, operator-confirmed before the production
write): `CATALOGUE_PROMOTED` event, 433,791 rows written to
`gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`, exit_code=0. **Live-verified
post-write**: both `OKX-SWAP:PERPETUAL:AVAX-USD@INV` and `...:XLM-USD@INV` now show `contract_size=1` (no longer blank);
the CeFi-wide blank count across all delisted derivative rows dropped from 271,838 to **10** (99.996% resolved — the
residual 10 are a separate, out-of-scope edge case not investigated further here). Note: the catalogue's raw value of
`1` for OKX-SWAP non-BTC alts is still the OLD wrong-default (Finding 2's root cause) — this does not matter for
correctness, since Finding 2's fix makes `liquidations_adapter.py` check the UAC static registry FIRST (which correctly
resolves OKX-SWAP non-BTC to `10`) and only falls back to this catalogue for venues the registry doesn't cover.

## Finding 2 — contract_size silently WRONG for OKX (non-BTC) and Deribit BTC — FIXED

Root cause, fully traced and verified against live code (not the sub-agent's word alone):

1. `liquidations_adapter.py:266-283` reads `contract_size` via
   `read_instruments_catalog_contract_size("cefi", venue, instrument_id_str)` — a static, non-date-aware lookup against
   `instruments-service`'s `catalog.parquet`. When it misses, the code FAIL-CLOSES (raises `MalformedTickFieldError`) —
   this is correct, deliberate design (2026-08-11 operator ruling: a wrong notional is worse than a failed shard).
2. **But the catalogue itself was never wrong-by-omission for Bybit/Kraken and silently wrong-by-substitution for
   OKX/Deribit.** `instruments-service`'s Tardis CeFi adapter (`adapter.py:649-661`) deliberately calls ONLY the free,
   no-auth `/v1/exchanges/{exchange}` endpoint (2026-06-23 operator decision, to avoid burning API limits before Tardis
   was paid) — that endpoint never returns `contractMultiplier` at all. `adapter.py:872-876` therefore ALWAYS falls
   through to a hardcoded `Decimal("1")` default for every Tardis-sourced CeFi instrument.
3. `1` happens to be Bybit's and Kraken Futures' genuine real face value (confirmed live: Bybit help center + Kraken
   Futures' own API, `contractSize` field value of 1 for `PI_XBTUSD`/`PI_ETHUSD`/`PI_LTCUSD`/`PI_XRPUSD`) — so those
   venues were accidentally correct. **OKX and Deribit were NOT**: live-verified against each venue's own public API
   (2026-08-12) — OKX `BTC-USD-SWAP` ctVal=100, every other `-USD-SWAP` alt ctVal=10 (14 distinct alts confirmed,
   corroborated by OKX's own help-center docs); Deribit `BTC-PERPETUAL` contract_size=10, `ETH-PERPETUAL`=1. **Deribit
   BTC was silently understated 10x and OKX non-BTC alts silently understated 10x — for every liquidation shard ever
   written by this pipeline, not just today's re-derive**, since nothing about this bug is new to today.
4. **Since Tardis is now paid, the obvious next step (switch to the authenticated `/v1/instruments/{exchange}` endpoint,
   which DOES carry `contractMultiplier`) was tested LIVE and does NOT work**: 401,
   `"Instruments metadata API is available only for active 'pro' and 'business' subscriptions."` — the current
   subscription tier doesn't include it. (The GSM secret `tardis-api-key` genuinely resolves and authenticates — this is
   a tier gap, not a missing/broken key. `DATA_SOURCE_TO_SECRET["tardis"] = "tardis-api-key"` in UAC's
   `canonical_mappings.py` is correct and the `ApiKeyReloader`/`factory.py` wiring already threads a real key into every
   OTHER Tardis adapter method — `instruments-service/instruments_service/reference_data/factory.py`'s Tardis
   construction branch just deliberately omits `api_key=api_key`, a one-line, easy, but INSUFFICIENT fix on its own
   given the tier gap.)

**Fix shipped** (operator direction: "reverse engineer it, stick it in UAC, resolve from that, use web to find patterns"
— not depend on the unavailable paid tier): new registry
`unified-api-contracts/unified_api_contracts/registry/cefi_inverse_contract_multipliers.py` —
`resolve_cefi_inverse_contract_multiplier(venue, base_asset)`, sourced + cited against each venue's live public API
(URLs + fetch date in the file's own comments), 34 new tests (`tests/unit/test_cefi_inverse_contract_multipliers.py`).
Gate green for the new code (34/34 passed). The FULL-repo gate initially had one UNRELATED pre-existing failure
(`test_priority_source_resolves_to_capability[fluid]`) — a DeFi "Fluid" protocol WIRE-REAL-CAPTURE commit
(`unified-api-contracts@6ac0dafd`, a different live session/slot) had registered `fluid` in `SOURCE_PRIORITY` +
`PipelineMode` but missed the one companion edit every sibling on-chain-RPC source (`spark`/`compound_v3`/`radiant`)
also needed: adding it to `_COMPUTED_SERVICE_SOURCES` in `test_venue_source_adapter_parity.py` (fluid's oracle_prices
capture is the same class — a pure on-chain `configs.oraclePriceOperate` eth_call, no vendor API). Genuinely blocking
the shared LDR trunk's full gate for everyone, not just this fix, and narrowly scoped with 3 identical precedents to
mirror exactly — fixed in the same ship rather than worked around. Shipped: `unified-api-contracts@49ad03df3d`.

**Wired into MDPS**: `liquidations_adapter.py`'s inverse-margin branch now derives `base_asset` from the canonical
`VENUE:TYPE:BASE-QUOTE@MARGIN` id shape and checks `resolve_cefi_inverse_contract_multiplier(venue, base_asset)` FIRST;
the existing `read_instruments_catalog_contract_size` catalogue lookup is now the fallback for venues the static
registry doesn't cover, with the same fail-closed `MalformedTickFieldError` on a double-miss. Existing adapter tests
updated to reflect the new resolution order (registry-hit tests now assert the catalogue is NOT called; the catalog-miss
test patches both the registry and catalogue to None to exercise a genuine double-miss). Shipped:
`market-data-processing-service@ae23ee5c03`.

## Finding 3 — `infer_cefi_quote_margin` misses dated-futures `@INV`/`@LIN` and OKX's `-SWAP` wire suffix — FIXED

Discovered mid-4th-re-derive (2026-08-13/14): 6+ hours into the corpus re-walk, `non-zero rc` count on per-date
subprocesses went from 0 → 29 starting EXACTLY at 2020-12-31→2021-01-01 and stayed nonzero every date after. Root cause,
live-traced against `run.log`:

1. `infer_cefi_quote_margin` (`canonical_writer_shaping.py:794-860`) resolved `margin_type` via
   `instrument_id.endswith("@LIN")`/`endswith("@INV")` as step 1 (most authoritative). This is an EXACT suffix check —
   it never matches a dated-future id, whose canonical shape is `@LIN|INV-YYYYMMDD` (`_build_canonical_future_key`).
   Confirmed live: `KRAKEN-FUTURES:FUTURE:ETH-USD@INV-20210326` and `...-20210625` both fell through to step 7
   (UNRESOLVED) despite carrying a perfectly valid `@INV` marker.
2. Separately, OKX's own raw wire form for CeFi perpetual swaps (`<BASE>-USD-SWAP`, e.g. `TRX-USD-SWAP`, `XRP-USD-SWAP`)
   has NO `@LIN`/`@INV` marker at all and doesn't match any of the other 5 heuristics either (doesn't end in `USD` — it
   ends in `SWAP`). Confirmed live for 5 instruments: `BTC/ETH/LTC/TRX/XRP-USD-SWAP`.
3. Both classes hit the SAME downstream symptom — `MalformedTickFieldError(field='margin_type', ...)` — 2,128 error
   occurrences across the first ~400 dates of the 4th re-derive alone (7 distinct instruments, but recurring on EVERY
   date each instrument has liquidation data, dating back to whenever these instruments/expiries started trading — not
   new to this re-derive, a pre-existing gap in every prior liquidations run too).

**Fix shipped**: `infer_cefi_quote_margin` now extracts the `@LIN`/`@INV` marker by splitting on `@` and taking the
token before the next `-` (tolerates a trailing `-YYYYMMDD`), and adds a new step 7 — a symbol ending in `SWAP` (after
the existing stablecoin check already ruled out linear `-USDT-SWAP`/`-USDC-SWAP`) resolves to `("USD", "inverse")`,
OKX's own convention. 4 new tests (2 dated-future marker cases, OKX-SWAP inverse, and a regression guard that linear
`-USDT-SWAP` still wins over the new heuristic). Gate green. Shipped: `market-data-processing-service@d5a0b6cdc5`.

Since `liquidations_adapter.py`'s `base_asset` parsing (Finding 2's fix) already splits on `-` regardless of whether an
`@` marker is present, `contract_size` resolution for all 7 instruments works correctly the moment `margin_type`
resolves — no further code change needed (OKX-SWAP TRX/XRP/LTC → registry `_DEFAULT=10`, BTC/ETH → their specific
values; KRAKEN-FUTURES dated futures → registry `UNIFORM=1`).

**The 4th re-derive VM (`mdps-backfill-cefi-20260813-174138`) was killed and relaunched** once this fix landed — its
tarball was staged before the fix shipped, so it would have kept failing on these 7 instruments for the rest of its
~2223-date run. MDPS backfill skips already-`captured` manifest rows by default (no `--force` was passed), so the
relaunch (`mdps-backfill-cefi-20260814-003509`) resumes efficiently rather than redoing the ~700+ already-completed
days.

## Still open — NOT done yet

- [x] [SCRIPT] P0. Wire the new UAC resolver into `liquidations_adapter.py`'s inverse-margin branch — done, see above.
      `market-data-processing-service@ae23ee5c03`.
- [x] [DATA] P1. Finding 1a — RESOLVED, no fix needed (see above): already-shipped
      `market-data-processing-service@ae23ee5c03` live-verified to correctly process all 4 real-object variants
      (BTCUSD/ETHUSD × stale-column/no-column) via BYBIT's UNIFORM registry entry + the symbol-based margin_type
      heuristic. A GCS content-rewrite script was written, dry-run-verified (2,879 objects), then deleted unapplied once
      live testing proved it unnecessary.
- [x] [DATA] P1. Finding 1b — FIXED AND VERIFIED (see above): new `cefi-catalogue-promote` VM launcher category
      (`deployment-service@a7561ac20c`), dry-run + operator-confirmed real run both completed clean, `catalog.parquet`
      promoted (433,791 rows). Blank `contract_size` on delisted CeFi derivatives: 271,838 → 10.
- [x] [SCRIPT] P0. Finding 3 — FIXED (see above): `market-data-processing-service@d5a0b6cdc5`, 4th re-derive VM killed +
      relaunched with the fix included.

- [ ] [OPERATOR] P2. DEFERRED-BY-DESIGN — per D45 ruling (2026-08-21, autonomous-dispatch authority): keep the free
      Tardis tier; the UAC `cefi_inverse_contract_multipliers` registry is a complete, correct, cited fix for the
      current instrument set and upgrading is not urgent. Revisit only if a new venue/instrument needs a face-value
      not yet covered.
- [ ] [SCRIPT] P0. Monitor the (relaunched) liquidations re-derive to completion, same 3-way verification rigor as every
      prior attempt in this batch (log counters + manifest `written_at` + GCS `last_modified` — a clean exit code alone
      has already proven insufficient multiple times this batch). Confirm zero non-zero-rc dates before calling this
      closed. **STATUS 2026-08-17 16:26 UTC**: relaunched 2026-08-16 16:24 UTC as `mdps-backfill-cefi-20260816-162418`
      (`e2-standard-4`, on-demand, **`--date-concurrency 2`** — doubled from the prior single-threaded iteration per
      operator instruction), healthy, **zero `SchemaContractNotFoundError`/`Traceback` hits across the entire run**.
      Currently `2023-04-01` of the `2020-01-01..2026-01-31` range (day 1187/2223, ~53.4%).
      **Measured pace, two windows** (both from the live log, `date=YYYY-MM-DD` markers, not estimated): first 14.3h
      (2020-01-01→2022-10-22, 1026 dates) averaged ~50s/date (71.7 dates/hr); the next 10.66h
      (2022-10-22→2023-04-01, 161 dates — spanning the Nov-2022 FTX collapse) slowed to ~238s/date (15.1 dates/hr),
      confirming the expected volume-driven slowdown. 1036 dates remain, still including the FULL 2023-2024 bull run
      and 2024-2026 (likely higher volume still).
      **ETA, bracketed by the two measured paces**: optimistic (full-run avg, 47.5 dates/hr) ≈ 21.8h remaining →
      **~2026-08-18 14:00 UTC**; conservative (most recent slower pace, 15.1 dates/hr) ≈ 68.6h remaining →
      **~2026-08-20 11:00 UTC**. Central expectation: **completes 2026-08-19 to 2026-08-20**. Treat this as a genuine
      range, not a point estimate — pace will keep moving as it crosses further volatility regimes.
      **Do not poll this hourly — that is a wasted session** (explicit operator instruction 2026-08-17: this VM
      running is not itself work, a continuously-polling session babysitting it end-to-end provides zero value over
      one that checks in at the right moment). **Next agent/session, do this**: don't check before
      **2026-08-18 ~12:00 UTC** at the earliest (the optimistic-case floor). SSH
      `find /tmp -maxdepth 1 -name "vm-exec-*.log"` on `mdps-backfill-cefi-20260816-162418` (zone
      `asia-northeast1-c`, `--account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com`), grep
      `date=20` markers for current position and `Traceback\|SchemaContractNotFoundError` for errors. If the date
      range is complete (reaches `2026-01-31` with exit code 0), run the full 3-way verification below and close this
      todo. If not yet complete by **2026-08-20 ~18:00 UTC** (past the conservative bound with margin), that's a real
      stall signal — diagnose (check `gcloud compute instances describe ... --format="value(status)"` + the Compute
      Engine operations log for an unexpected delete) before deciding whether to relaunch; checkpoint-resume is
      proven correct across iterations so a restart is cheap if genuinely needed, but isn't free (redoes the last
      <24h of dates and costs a boot cycle) — don't force one just because it's still running past a soft estimate.
      **Related, already resolved**: the `uts-prod-dp-exit-code-monitor-cron` fleet-wide auto-recovery cron (paused
      earlier in this campaign pending a deployment-api rebuild — see
      `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`) was re-enabled 2026-08-17 after verifying the fix's
      content (not just commit ancestry — the LDR→main promotion squash-merges, so `git merge-base --is-ancestor`
      against the original commit sha is the WRONG check and will falsely say "not promoted" forever; verify actual
      file content on `origin/main` instead) was live in the deployed Cloud Run Job image, then confirmed via two
      clean hourly firings (00:00 and 01:00 UTC, both dispatched correctly-scoped single-cell relaunches, fleet count
      stayed flat 14-16 `mdps-*` VMs, no explosion) — this CeFi VM is not itself at risk from that cron now.
- [x] [DATA] P3. **CORRECTION 2026-08-16**: the claim below that `SchemaContractNotFoundError` is "correctly recorded
      as `attempted_failed`" is WRONG — directly measured earlier in this campaign (a prior session, same day) that the
      VM's own per-VM manifest shard had **0 `attempted_failed` rows** despite these exact `SchemaContractNotFoundError`
      occurrences being present in its log. Root cause: `SchemaContractNotFoundError` is NOT caught by the shard-level
      failure-isolation handler that converts `MalformedTickFieldError`/`UpstreamTimestampBiasError` into
      `record_failed_for_shard()` — it's deliberately a hard, loud, pipeline-halting signal by design (someone needs to
      register a contract), not a per-shard-recordable failure. That's fine for the intended case (missing contract
      registration) but wrong for THIS case (malformed raw bundle data) — these failures are currently invisible to
      both the manifest and to Slack alerting (confirmed earlier: zero `DP_VM_PREEMPTED`/`DP_RUN_MOSTLY_EMPTY`-class
      events matched this signature in `#data-pipeline-alerts`). Still needs a decision: reclassify this specific
      bundle-file-defect case to raise `MalformedTickFieldError` instead (so it's honestly recorded + retryable), or
      widen the shard-isolation catch handler to also record `SchemaContractNotFoundError`. Original finding stands
      otherwise (root cause + narrow blast radius correct).
      **DECIDED + SHIPPED 2026-08-16** (RESTORED — see "doc-regression" Progress Log entry below; the na-eligibility-audit
      RECLASSIFY-SPLIT commit `20f4f6f893` accidentally un-checked this + the sibling item below and deleted their
      shipped-evidence text, most likely from operating on a stale base of this file): widened the shard-level
      failure-isolation catch in `_process_all_timeframes` (`live_workers_chain.py`) to also catch
      `SchemaContractNotFoundError` alongside `MalformedTickFieldError`/`UpstreamTimestampBiasError`, routing it through
      `record_failed_for_shard` (honestly recorded + retryable). The loud signal is preserved, not hidden:
      `SchemaContractNotFoundError` gets its own ERROR-level per-shard log line
      (asset_group/venue/instrument_type/data_type) via a new `_log_typed_shard_error` helper, on top of the existing
      ERROR-level `log_event` already fired at the raise site (`canonical_writer.py`'s own `except
      SchemaContractNotFoundError` handler — untouched). Regression test added:
      `tests/unit/test_live_workers_typed_error_routing.py::test_schema_contract_not_found_routes_to_record_failed`
      (proves no unhandled propagation + `record_failed_for_shard` called with `error="SchemaContractNotFoundError"`).
      Shipped: `market-data-processing-service@bc9706cdb5`.
- [x] [DATA] P3. NEW, SEPARATE, narrow finding surfaced mid-4th-re-derive (2026-08-14, unrelated to contract_size/
      margin_type):
      `No SchemaContract registered for asset_group='cefi' instrument_type='<SYMBOL>' data_type='liq_agg_15s' venue='BINANCE-FUTURES'`
      — an EARLIER partial sample of this doc saw 8 distinct symbols (AVAX/LTC/ATOM/BTC/UNI/DOGE/ADA/ETHUSDT), ~16
      occurrences, 2021-01-31..2021-02-08 only; that window/symbol set was NOT the full extent (see ROOT CAUSE below).
      **VERIFICATION 2026-08-16 (session 1) — hypothesis REFUTED.** Read the actual raw GCS objects
      (`market-data-tick-cefi-prd-central-element-323112`, resolved via `get_write_bucket_name`/`get_storage_client` per
      the UTL helper, never inline `gs://`) with pandas for all 8 originally-affected symbols on `2021-02-01`, plus
      BTC/AVAX on the window boundary dates (`2021-01-31`, `2021-02-08`) and two control dates outside the window
      (`2021-01-15`, `2021-02-15`). The **per-instrument** `venue=BINANCE-FUTURES/.../data_type=liquidations/
      BINANCE-FUTURES:PERPETUAL:{SYM}-USDT@LIN.parquet` objects were clean at every symbol/date sampled — no bundling, no
      `instrument_type` column at all (columns `[exchange, symbol, timestamp, local_timestamp, id, side, price, amount,
      data_type, instrument_id]`), `instrument_id` uniformly well-formed. This refuted the original "malformed raw bundle
      row" hypothesis and redirected suspicion to MDPS's own candle-derivation code — but the exact code path was not yet
      located in that session.
      **ROOT CAUSE CONFIRMED 2026-08-16 (session 2 — this dispatch).** The per-instrument files verified above are NOT
      the files that actually triggered the error. A **separate, STALE legacy bundle file** sits at the exact same GCS
      hive prefix ALONGSIDE the per-instrument files:
      `raw_tick_data/by_date/day=2021-01-31/pipeline_mode=batch_tardis/asset_group=cefi/venue=BINANCE-FUTURES/
      instrument_type=perpetual/data_type=liquidations/ticks.parquet` (confirmed still present, `last_modified
      =2026-06-27`, 44,272 rows spanning **17** symbols — ADA/ATOM/AVAX/BNB/BTC/DOGE/DOT/ETH/LINK/LTC/LUNA/MATIC/NEAR/
      SOL/TRX/UNI/XRP-USDT — one legacy pre-2024-migration multi-instrument dump, columns
      `[exchange, symbol, timestamp, local_timestamp, id, side, price, amount, data_type, instrument_type]`: note NO
      `instrument_id` column, and `instrument_type` is correctly `'perpetual'` on this file too — the raw content was
      never the defect). `ticks.parquet` IS MDPS's own documented "multi-instrument bundle" filename sentinel
      (`gcs_path_utils.extract_instrument_id_from_blob_path` / `live_workers_chain._is_chain_data`), so MDPS correctly
      routes it to `_process_chain_timeframe_by_symbol` (`live_workers_chain.py`) to split by the `symbol` column and
      write one candle file per instrument. **The bug**: that function synthesised the per-symbol `instrument_id` as a
      bare 2-segment `f"{venue}:{symbol}"` (e.g. `"BINANCE-FUTURES:BTCUSDT"`) — never including the TYPE segment, even
      though the bundle's own `instrument_type` column (or the blob path's `instrument_type=` hive segment) already had
      it. This 2-segment id then reaches `_infer_instrument_type`'s legacy-id fallback
      (`canonical_writer_shaping.py`, the final `parts = instrument_id.split(":"); return parts[1]` branch, written for
      an assumed 3-segment `VENUE:TYPE:SYMBOL` shape) — for a 2-segment id, `parts[1]` is the SYMBOL, not the TYPE, so
      the SchemaContract lookup used `instrument_type='BTCUSDT'` (the wire ticker) instead of `'PERPETUAL'`, failing loud
      every time. **Confirmed against the LIVE VM log**, not just static tracing: SSH'd (read-only) into
      `mdps-cefi-2021-20260813-174738` (asia-northeast1-c, still running) and grepped its own
      `/tmp/vm-exec-5128.log` for `data_type='liq_agg_15s' venue='BINANCE-FUTURES'` — **13 occurrences across 13
      distinct 2021 dates** (`2021-01-31, 02-03, 02-04, 02-08, 03-17, 03-18, 03-20, 03-24, 03-25, 04-03, 04-04, 04-07,
      04-08` — materially wider than the original 9-day sample), 8 distinct `instrument_type` values seen
      (`BNBUSDT/BTCUSDT/DOTUSDT/LTCUSDT/LUNAUSDT/SOLUSDT/TRXUSDT/UNIUSDT`) — every single one a literal wire ticker from
      a stale bundle's `symbol` column, matching the mechanism exactly (partial symbol/date overlap with the original
      8-symbol sample is expected: each backfill sweep only hits whichever stale-bundle dates it processes in that run).
      A synthetic repro against the REAL downloaded `2021-02-01 AVAX-USDT@LIN` per-instrument file (confirming it is
      NOT the trigger) resolved `instrument_type='PERPETUAL'` correctly regardless of the starting id — isolating the
      defect to the bundle-split path specifically, not the per-instrument path.
      **FIXED**: `_process_chain_timeframe_by_symbol` now reads the bundle's own `instrument_type` column (new
      `_resolve_bundle_instrument_type` helper, uppercased) and synthesises the proper 3-segment
      `VENUE:TYPE:SYMBOL` id when available; when genuinely absent it falls back to the pre-fix 2-segment shape
      unchanged (honest-unresolved, never guessed — same convention the sibling id renormalizers already use).
      Regression tests: `tests/unit/test_live_workers_coverage.py::TestProcessChainTimeframeBySymbol::
      test_instrument_type_column_produces_canonical_3segment_id` (real affected symbol `BTCUSDT` -> synthesises
      `BINANCE-FUTURES:PERPETUAL:BTCUSDT`) and `::test_missing_instrument_type_column_stays_honest_unresolved_2segment`
      (regression guard: column absent -> unchanged 2-segment shape, proves the fix doesn't fabricate a TYPE). Full
      `quality-gates.sh` green (2447 passed, 2 skipped). Shipped: `market-data-processing-service@a3ff10f0dd`. Blast
      radius beyond what's fixed: the STALE `ticks.parquet` bundle files themselves are not deleted by this change
      (out of scope — a separate GCS cleanup/migration decision, not a code defect) and any date this VM already
      processed before the fix landed still needs a re-attempt to pick up the corrected id (manifest rows for these are
      `attempted_failed` per the shard-isolation widening above, so they retry automatically on the next sweep).
- [x] [SCRIPT] P3. EXTRACTED — na-eligibility-audit 2026-08-16, conflict-cleared, live todo now
      `cefi_satellite_ao_dispatch_batch20_2026_08_16.md` item 1. Original text: NEW 2026-08-16:
      `aggregate_from_15s_efficient` (`fast_candle_aggregation.py:333-359`) fires its
      "adapter density bug" NaN-in-`open`/`close` warning on EVERY liquidations shard with any zero-liquidation window
      — 659,791 occurrences and counting in this campaign's log alone. Confirmed FALSE POSITIVE, not a real bug (see
      the spot-check above): liquidations is inherently sparse/event-driven, and null `open`/`close` on a
      zero-liquidation window is the CORRECT honest-absence representation, not the "pre-LOCF leading-NaN density bug"
      this guard exists to catch on continuous LOCF-densified data (trades/book_snapshot_5). `derivative_ticker`
      already has an exemption for this exact shape (`_honest_absence_frame`, keyed on the `mark_price_mean` column) —
      liquidations needs the same kind of exemption (key on `liquidation_count`/`liquidation_notional_usd` presence, or
      widen the existing `mark_price_mean` check). Low priority — output data is correct, this is pure log-noise
      cleanup (659K lines is real cost in log volume/scan time for anyone debugging this VM, but not a correctness
      issue).
      **FIXED 2026-08-16** (RESTORED — see doc-regression Progress Log entry below, this evidence was deleted by the
      na-eligibility-audit extraction commit along with the checkbox): `_honest_absence_frame` now also matches on
      presence of `liquidation_count` / `liquidation_notional_usd` (OR'd with the existing `mark_price_mean` check), so
      a genuine zero-liquidation window's null open/close no longer trips the guard. Trades/book_snapshot_5 (no
      exemption columns) keep the real protection unchanged. Tests added in `tests/unit/test_fast_candle_aggregation.py`
      (`TestLiquidationsHonestAbsenceNanGuardExemption`): (a) `test_liquidations_zero_window_does_not_warn` — a
      liquidations-shaped frame with a legit zero window does NOT warn; (b) `test_dense_adapter_leading_nan_still_warns`
      — regression guard proving the ORIGINAL bug case (a dense adapter with a leading NaN and none of the exemption
      columns) still DOES warn. Shipped: `market-data-processing-service@bc9706cdb5`.

## Lesson

**A live, executable verification beats a plausible design decision every time — the free-vs-paid Tardis endpoint choice
READ as reasonable (a real operator decision with a real date and a real reason) right up until it was tested live and
found to not solve the actual problem (401, wrong tier).** Don't stop at "there's a documented reason this is the way it
is" — test whether the reason still holds NOW. Separately: mid-session, an automated `main`→LDR backmerge + this
checkout's own liveness-gated cleanup silently reverted an in-progress, uncommitted UAC edit (tracked file `__init__.py`
reverted, untracked new files deleted) — recovered only because the full file content was still in the live conversation
context. Reinforces the standing lesson even harder: ship at every green-gated unit, don't let genuinely-done work sit
uncommitted across a checkpoint boundary, even mid-task.

## Progress Log

- **context-scout 2026-08-14**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-16** [body-hash:8aa962571f5348dd]: RECLASSIFY-SPLIT — extracted bounded item(s) 1 to `cefi_satellite_ao_dispatch_batch20_2026_08_16.md` (see that plan + this doc's own checkbox citations for exact mapping). 4 items remain genuinely NA (1 [OPERATOR] Tardis-tier spend decision, 1 [SCRIPT] P0 monitor-to-completion stood down to proactive-check cadence not bounded-now, 2 [DATA] P3 investigation-not-yet-confirmed items). Doc stays assigned_vm: NA.
- **DOC-REGRESSION found + fixed 2026-08-16 (this dispatch)**: the na-eligibility-audit RECLASSIFY-SPLIT commit
  `20f4f6f893` (immediately above) accidentally reverted TWO already-shipped, verified fixes back to unchecked `[ ]`
  and deleted their shipped-evidence text (the `SchemaContractNotFoundError` shard-isolation widening and the
  liquidations NaN-warning exemption, both genuinely shipped `market-data-processing-service@bc9706cdb5` per commit
  `16b57fd3ad` on this same doc) — most likely the audit operated on a base copy of this file that predated commit
  `0f22d65ede`/`16b57fd3ad` landing, then its own write overwrote the newer content on push. It ALSO deleted the
  "VERIFICATION 2026-08-16 — hypothesis REFUTED" investigation paragraph entirely. Restored both `[x]` items + their
  evidence, and preserved the REFUTED-hypothesis narrative inline within the new root-cause writeup below (superseded,
  not silently dropped) — this is exactly the class of loss `git show <commit> -- <path>` catches; worth a general
  caution for any future doc-splitting/extraction tooling to diff against the file's OWN latest commit before writing,
  not an in-memory/stale copy.
- **Root cause LOCATED + FIXED 2026-08-16 (this dispatch, `/autonomous`)**: the `liq_agg_15s` SchemaContractNotFoundError
  finding (2 items above) is CLOSED — see its own checkbox for the full root cause (a stale legacy `ticks.parquet`
  multi-instrument bundle file, MDPS's own `_process_chain_timeframe_by_symbol` synthesising a malformed 2-segment
  `instrument_id`), fix, regression tests, and evidence. Confirmed via live SSH read of the actual backfill VM's own
  log (`mdps-cefi-2021-20260813-174738:/tmp/vm-exec-5128.log`), not just static code tracing. Shipped:
  `market-data-processing-service@a3ff10f0dd`.
- **na-eligibility-audit 2026-08-17** [body-hash:f9e2a037984a3a3c]: KEEP-NA, valid — Reaffirmed. 8 of 10 todos [x] with hard sha evidence. 2 remaining: an [OPERATOR] Tardis-tier spend decision, and a monitor-to-completion task gated on a still-running VM (ETA ~2026-08-22..26) with an open-ended diagnose-if-it-dies-again branch. Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-18 (cefi tranche)** [body-hash:61b847d91fc39e08]: KEEP-NA, valid — reaffirmed; same 2 open items, unchanged in substance (only the monitor-status prose was updated since the last marker, which is why the body hash moved). Item 1 ([OPERATOR] P2, Tardis pro/business tier spend decision) OPERATOR_QUESTION. Item 2 ([SCRIPT] P0, monitor the relaunched liquidations re-derive to completion) DEPENDENCY_BLOCKED on the VM's own real-world completion — doc's own text pegs the earliest useful check at ~2026-08-18 12:00 UTC and explicitly warns against hourly polling; flagging MISCLASSIFIED_LIKELY_AO_ELIGIBLE (low confidence) for the next run once the ETA window has clearly passed — the "is it done, run the 3-way verification" branch reads as bounded/mechanical, but extracting it now risks a no-op dispatch before the VM is actually done. Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: refreshed context_scope (5 entries, was 3) — added the sourcing P0 plan
  (`data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`) and `live_workers_chain.py`, the file most of this
  doc's later root-cause work (SchemaContractNotFoundError routing, the 2-segment instrument_id bug) actually
  touched.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).

**2026-08-21 — ruling D45 (Tardis tier upgrade)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
AUTONOMOUS_AGENT_RULES rule 2): Keep free tier — the registry is a complete, correct, cited fix for the current
instrument set; not urgent. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.

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
created: 2026-08-12
author: claude-agent
source: "2026-08-12 continuation session, verifying the liquidations re-derive's manifest outcome"
priority: P0
parent_epic: infrastructure_master
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

- [ ] [OPERATOR] P2. Decide whether to upgrade the Tardis subscription to "pro"/"business" tier — would let
      instruments-service source `contractMultiplier` directly instead of depending on a hand-maintained UAC registry
      that needs manual re-verification if a venue's face values ever change. Not urgent — the UAC registry is a
      complete, correct, cited fix for the CURRENT known instrument set.
- [ ] [SCRIPT] P0. Monitor the (relaunched) liquidations re-derive to completion, same 3-way verification rigor as every
      prior attempt in this batch (log counters + manifest `written_at` + GCS `last_modified` — a clean exit code alone
      has already proven insufficient multiple times this batch). Confirm zero non-zero-rc dates before calling this
      closed.

## Lesson

**A live, executable verification beats a plausible design decision every time — the free-vs-paid Tardis endpoint choice
READ as reasonable (a real operator decision with a real date and a real reason) right up until it was tested live and
found to not solve the actual problem (401, wrong tier).** Don't stop at "there's a documented reason this is the way it
is" — test whether the reason still holds NOW. Separately: mid-session, an automated `main`→LDR backmerge + this
checkout's own liveness-gated cleanup silently reverted an in-progress, uncommitted UAC edit (tracked file `__init__.py`
reverted, untracked new files deleted) — recovered only because the full file content was still in the live conversation
context. Reinforces the standing lesson even harder: ship at every green-gated unit, don't let genuinely-done work sit
uncommitted across a checkpoint boundary, even mid-task.

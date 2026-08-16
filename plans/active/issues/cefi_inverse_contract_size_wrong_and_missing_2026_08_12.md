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
    unified-api-contracts/unified_api_contracts/registry/cefi_inverse_contract_multipliers.py,
    market-data-processing-service/market_data_processing_service/app/adapters/cefi/liquidations_adapter.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
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
      closed. **STATUS 2026-08-16 13:56 UTC**: on its 5th VM iteration, `mdps-backfill-cefi-20260815-181733`
      (`e2-standard-4`, on-demand), healthy, zero `SchemaContractNotFoundError`/`Traceback` hits across the whole run
      so far, currently `2022-06-08` of the `2020-01-01..2026-01-31` range (day 890/2223, ~40%) at ~7 min/date and
      still gradually climbing. **ETA: ~6-10 days from now, i.e. landing roughly 2026-08-22..2026-08-26** — the wide
      range is because pace keeps climbing through higher-volume periods (the Nov-2022 FTX collapse and the 2023-2024
      bull run are both still ahead of it). Prior 4 iterations were killed by an unrelated bug
      (`vm_zombie_watchdog.py` false-positiving on long-running jobs — fixed + shipped
      `deployment-service@149374355e`, see `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`, now
      resolved/checkboxes flipped) — this iteration has NOT been killed since that fix landed
      (~19h uninterrupted as of this note). **Output spot-checked and looks correct**: pulled
      `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` 15m liquidation candles for 2022-05-01 — prices match real BTC levels
      (~$37-38K), OHLC internally consistent, liquidation volume tracks visible volatility, and the 22/96 windows with
      zero liquidations are cleanly `null` (not zero/garbage) — honest absence, not corruption; the scattered (not
      block-contiguous) shape of the zero-liquidation windows across a full day further supports genuine sparsity over
      an upstream collection gap. **Active hourly monitoring stood down 2026-08-16** — nothing else in this doc or
      `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md` is blocked on this VM finishing, and the zombie-watchdog
      fix (the only thing that was actually killing it) is verified stable, so there's no value in checking every
      hour for the next ~week. **Next agent, whenever this is picked up again (proactively around the ETA window
      above, or whenever this doc is next touched for any reason)**: SSH `find /tmp -maxdepth 1 -name
      "vm-exec-*.log"` on `mdps-backfill-cefi-20260815-181733` for current progress/errors. If the date range is
      complete (reaches `2026-01-31` with exit code 0), run the full 3-way verification below and close this todo. If
      it died/got killed again (check `gcloud compute instances describe ... --format="value(status)"` and the
      Compute Engine operations log for a delete op + its `user`), diagnose why before blindly relaunching — do NOT
      restart it just to "keep it running" if it's genuinely still healthy; checkpoint-resume is proven correct
      across iterations so a restart is cheap if actually needed, but isn't free (redoes the last <24h of dates and
      costs a boot cycle) so don't force one without a reason.
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
      **DECIDED + SHIPPED 2026-08-16**: widened the shard-level failure-isolation catch in
      `_process_all_timeframes` (`live_workers_chain.py`) to also catch `SchemaContractNotFoundError` alongside
      `MalformedTickFieldError`/`UpstreamTimestampBiasError`, routing it through `record_failed_for_shard` (honestly
      recorded + retryable). The loud signal is preserved, not hidden: `SchemaContractNotFoundError` gets its own
      ERROR-level per-shard log line (asset_group/venue/instrument_type/data_type) via a new `_log_typed_shard_error`
      helper, on top of the existing ERROR-level `log_event` already fired at the raise site
      (`canonical_writer.py`'s own `except SchemaContractNotFoundError` handler — untouched). Regression test added:
      `tests/unit/test_live_workers_typed_error_routing.py::test_schema_contract_not_found_routes_to_record_failed`
      (proves no unhandled propagation + `record_failed_for_shard` called with `error="SchemaContractNotFoundError"`).
      Shipped: `market-data-processing-service@bc9706cdb5`.
- [ ] [DATA] P3. NEW, SEPARATE, narrow finding surfaced mid-4th-re-derive (2026-08-14, unrelated to contract_size/
      margin_type):
      `No SchemaContract registered for asset_group='cefi' instrument_type='<SYMBOL>' data_type='liq_agg_15s' venue='BINANCE-FUTURES'`
      — 8 distinct symbols (AVAX/LTC/ATOM/BTC/UNI/DOGE/ADA/ETHUSDT), ~16 total occurrences, 2021-01-31..2021-02-08 only.
      Root cause NOT yet confirmed but strongly suspected: the raw
      `venue=BINANCE-FUTURES/.../data_type=liquidations/ticks.parquet` BUNDLE file (multiple instruments per file, not
      per-instrument) has a malformed per-row `instrument_type` column containing the SYMBOL string instead of
      `PERPETUAL` for these specific rows — a likely raw MTDS historical data-quality issue for this exact 9-day window,
      not an MDPS code bug (MDPS's fail-closed `SchemaContract` lookup is working as designed, refusing to guess). NOT
      "correctly recorded as `attempted_failed`" — see the correction above, this failure class is currently invisible
      to the manifest entirely. Needs: (1) confirm the raw bundle file's actual `instrument_type` column content for
      one of these symbol/dates to verify the hypothesis, (2) if confirmed, either a targeted content-fix (same
      methodology as Finding 1a) or accept as honest historical absence. Very small blast radius (16 occurrences vs the
      thousands-of-shards P0 findings above) — does not block calling Findings 1/2/3 verified.
      **VERIFICATION 2026-08-16 — hypothesis REFUTED, root cause redirected.** Read the actual raw GCS objects
      (`market-data-tick-cefi-prd-central-element-323112`, `resolve`d via `get_write_bucket_name`/`get_storage_client`
      per the UTL helper, never inline `gs://`) with pandas for all 8 affected symbols on `2021-02-01`, plus BTC/AVAX
      on the window boundary dates (`2021-01-31`, `2021-02-08`) and two control dates well outside the window
      (`2021-01-15`, `2021-02-15`). Direct evidence against both halves of the hypothesis:
      (1) **no bundling** — every raw `data_type=liquidations` object for `venue=BINANCE-FUTURES` is already
      single-instrument (e.g. `.../instrument_type=perpetual/data_type=liquidations/BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN.parquet`,
      `symbol` column uniformly `BTCUSDT`/`AVAXUSDT`/etc., one value only, for every file checked in and out of the
      window);
      (2) **no `instrument_type` column exists in the raw parquet at all** — columns are exactly
      `[exchange, symbol, timestamp, local_timestamp, id, side, price, amount, data_type, instrument_id]` for every
      symbol/date sampled, identically inside and outside the affected window, so there is no raw column that could be
      "malformed" in the first place — this is the universal raw schema for this `data_type`, not a 9-day anomaly.
      `instrument_id` was consistently well-formed (`BINANCE-FUTURES:PERPETUAL:{SYM}-USDT@LIN`) everywhere sampled too.
      **Conclusion**: the raw source file is clean; whatever value MDPS's `SchemaContract` lookup used as
      `instrument_type='<SYMBOL>'` was NOT read from the raw file — it must be derived downstream, inside MDPS's own
      candle-derivation code (most likely a parse of `instrument_id`/`symbol` at read time), and that derivation is
      going wrong for these 16 occurrences specifically. This directly contradicts the doc's own earlier assumption
      ("not an MDPS code bug") — it now looks like it likely IS one, just not yet located. **Leaving this todo OPEN**
      (not accepting as historical-raw-data absence per the doc's own stated fallback option, since the evidence rules
      that option out) pending a follow-up to locate the actual MDPS-side `instrument_type`-derivation bug for this
      narrow symbol/date set. Investigation scripts were scratch-only (not committed; read-only, no GCS objects
      modified).
- [x] [SCRIPT] P3. NEW 2026-08-16: `aggregate_from_15s_efficient` (`fast_candle_aggregation.py:333-359`) fires its
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
      **FIXED 2026-08-16**: `_honest_absence_frame` now also matches on presence of `liquidation_count` /
      `liquidation_notional_usd` (OR'd with the existing `mark_price_mean` check), so a genuine zero-liquidation
      window's null open/close no longer trips the guard. Trades/book_snapshot_5 (no exemption columns) keep the real
      protection unchanged. Tests added in `tests/unit/test_fast_candle_aggregation.py`
      (`TestLiquidationsHonestAbsenceNanGuardExemption`): (a)
      `test_liquidations_zero_window_does_not_warn` — a liquidations-shaped frame with a legit zero window does NOT
      warn; (b) `test_dense_adapter_leading_nan_still_warns` — regression guard proving the ORIGINAL bug case (a dense
      adapter with a leading NaN and none of the exemption columns) still DOES warn. Shipped:
      `market-data-processing-service@bc9706cdb5`.

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
- **2026-08-16 (autonomous dispatch)**: shipped the two P3 SCRIPT/DATA follow-ups — (1) widened
  `_process_all_timeframes`'s shard-isolation catch to also catch `SchemaContractNotFoundError`, routed through
  `record_failed_for_shard`, loud ERROR-level logging preserved; (2) added the liquidations honest-absence exemption
  to `aggregate_from_15s_efficient`'s NaN guard (`liquidation_count`/`liquidation_notional_usd`). Both + regression
  tests shipped `market-data-processing-service@bc9706cdb5` (QG green both runs). Incidental fix in the same commit:
  `canonical_writer_stamping.py`'s DeFi `lst_rates`→`lst_yields` SOURCE_PRIORITY bridge was wrong (nonexistent UAC
  key, blocking the shared trunk's QG for everyone) — corrected to the actually-registered `lst_rates` key.

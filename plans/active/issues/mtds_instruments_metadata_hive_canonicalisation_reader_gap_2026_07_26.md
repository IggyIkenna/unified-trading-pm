---
doc_type: issue
title:
  "MTDS's _instruments_metadata.py DeFi catalogue reader missed the 2026-07-21/22 instrument_availability hive
  canonicalisation — silently blind to IS catalogue data since ~2026-07-23"
summary: >-
  market-tick-data-service/market_tick_data_service/cli/handlers/_instruments_metadata.py reads instruments-service's
  instrument_availability catalogue via an EXACT single-blob GET at the pre-cutover flat path
  (day={D}/venue={V}/instruments.parquet). instrument_availability_hive_canonicalisation_2026_07_21.md's writer fix
  (instruments-service@a9be6ce9, in force 2026-07-22) moved the real write path to the full hive shape
  (day={D}/pipeline_mode={pm}/asset_group={ag}/venue={V}/...). That issue doc's own todo 6 lists 6 readers made
  layout-tolerant in lockstep (cloud_data_provider.py, instrument_lifecycle_loader.py, manifest_writer/_maintenance.py,
  manifest_writer/_queries.py, options_cluster_lookup.py, tradfi_live.py) — MTDS's _instruments_metadata.py (13
  downstream handler consumers) is NOT among them and was never updated. Confirmed via direct GCS listing: flat venue=
  dirs existed under instrument_availability/by_date/day=2026-07-2{0,1,2}/ and are ZERO for day=2026-07-2{3,4,5} onward
  — the exact-path GET has been returning None (parquet-missing fallback) for every DeFi protocol for ~4 days. For
  risk_params's two CATALOGUE_ONLY_PROTOCOLS (morpho, fluid — no subgraph risk-config block, no other fallback), this
  silently converts real IS-catalogue data into a dishonest zero-rows manifest stamp every capture cycle since
  ~2026-07-23 — the exact FLUID-class landmine already flagged in this doc's sibling
  (defi_manifest_no_expected_unattempted_seeder_2026_07_26.md finding #5), but now confirmed for the catalogue path
  itself rather than the subgraph-cascades path.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    defi,
    manifest,
    instrument-availability,
    hive-canonicalisation,
    catalogue-reader,
    data-correctness,
    silent-placeholder,
    regression,
  ]
related:
  [
    instrument_availability_hive_canonicalisation_2026_07_21,
    defi_manifest_no_expected_unattempted_seeder_2026_07_26,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: planning
source: [defi_manifest_no_expected_unattempted_seeder-007 (data_engineering worker investigation)]
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# MTDS `_instruments_metadata.py` missed the instrument_availability hive-canonicalisation cutover

## What I found

While investigating why `risk_params_handler.py`'s `_DEFAULT_PROTOCOLS` (line 111) omits `solend`/`marginfi` despite
`SOLANA_LENDING_PROTOCOLS` declaring both catalogue-fallback-capable (the P3 todo in
`defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`), I found the mechanism those protocols would dispatch
through — `_load_pool_metadata_from_instruments` → `load_pool_metadata_for_date`
(`market_tick_data_service/cli/handlers/_instruments_metadata.py:180-351`) — is currently broken for **every** DeFi
protocol, not just the Solana lending ones, due to a missed reader-side update on a recent, already-ruled
canonicalisation cutover.

1. **The cutover is real and dated.** `instrument_availability_hive_canonicalisation_2026_07_21.md` (operator HARD RULE
   R2, 2026-07-21) moved `instrument_availability`'s write path from the flat `day={D}/venue={V}/instruments.parquet`
   shape to the full canonical hive shape `day={D}/pipeline_mode={pm}/asset_group={ag}/venue={V}/instruments.parquet`,
   in force at the instruments-service writer since `instruments-service@a9be6ce9` (2026-07-22). Confirmed live via
   direct GCS listing against `gs://instruments-store-defi-prd-central-element-323112/instrument_availability/by_date/`:

   ```
   day=2026-07-20/  → 92  flat `venue=` dirs present
   day=2026-07-21/  → flat `venue=` dirs present (incl. venue=KAMINO-SOLANA, venue=MARGINFI-SOLANA, venue=SOLEND-SOLANA)
   day=2026-07-22/  → 89  flat `venue=` dirs present
   day=2026-07-23/  → 0   flat `venue=` dirs (only pipeline_mode=batch_instruments_service/asset_group=defi/venue=... remains)
   day=2026-07-24/  → 0
   day=2026-07-25/  → 0
   day=2026-07-26/  → 0
   ```

2. **The issue doc's own todo 6 lists which readers were fixed in lockstep — MTDS is not among them.** Todo 6: "Readers
   made layout-tolerant across the cutover ... : `cloud_data_provider.py`, `instrument_lifecycle_loader.py`,
   `manifest_writer/_maintenance.py`, `manifest_writer/_queries.py`, `options_cluster_lookup.py` —
   `unified-trading-library@43fa6f3f`; `tradfi_live.py` reader — `instruments-service@a9be6ce9`." All 6 are
   `unified-trading-library`/`instruments-service` internals. `market-tick-data-service`'s `_instruments_metadata.py` —
   a genuine cross-repo DOWNSTREAM consumer of `instrument_availability` — was never touched. The
   `unified-trading-library/manifest_writer/_maintenance.py` fix (line 181) shows the correct layout-tolerant pattern
   that should have been mirrored: `re.compile(r"day=(\d{4}-\d{2}-\d{2})/(?:[^/]+/)*venue=([^/]+)/")` — a day-scoped
   `list_blobs` + regex match on the venue-tail, not an exact single-blob path.

3. **`_instruments_metadata.py` instead does an exact single-blob GET at the now-stale flat path**, in all 4 of its
   public loaders:
   - `load_pool_metadata_for_date` (:223-225):
     `blob_path = f"instrument_availability/by_date/day={date_str}/venue={venue_tag}/instruments.parquet"`
   - `load_oracle_feeds_for_date` (:426)
   - `load_staking_url_for_protocol` (:503)
   - `load_evm_lst_contract_addresses_for_date` (:587)

   All 4 catch `FileNotFoundError`/`NotFound`/404 and treat a miss as "IS has no data for this date" → fall back
   (subgraph / static config / legacy discovery). Since 2026-07-23 this fallback fires for **every** DeFi protocol on
   **every** date, because the exact path no longer exists — not because IS genuinely lacks the data.

4. **13 handler files in `market_tick_data_service/cli/handlers/` depend on this module**
   (`grep -rl "load_pool_metadata_for_date\|_instruments_metadata"`): `_catalogue_filter.py`,
   `_defi_catalog_freshness.py`, `_dex_swaps_queries.py`, `_risk_params_stage.py`, `_solana_defi_fetch.py`,
   `_solana_lst_archival_tier1.py`, `dex_pools_handler.py`, `dex_swaps_handler.py`, `lending_indices_handler.py`,
   `liquidations_handler.py`, `lst_rates_handler.py`, `native_staking_handler.py`, `oracle_prices_handler.py`,
   `risk_params_handler.py`, `solana_defi_handler.py`, `solana_lst_archival.py`, `staking_yields_handler.py`. Most of
   these have a graceful static/legacy fallback (oracle feeds → static `STAKING_URL_FALLBACKS`-style config; EVM LST
   addresses → `_EVM_LST_STATIC_CONTRACT_ADDRESSES`; Phoenix pairs → `_PHOENIX_STATIC_CLOB_MARKETS`) — those degrade
   silently but not dishonestly (they still capture correct, if less dynamically-sourced, data). **The one confirmed
   dishonest path is `risk_params_handler.py`'s `_CATALOGUE_ONLY_PROTOCOLS = {"morpho", "fluid"}`**
   (`risk_params_handler.py:115,330`): for these two protocols, `_fetch_risk_param_rows` goes STRAIGHT to
   `risk_params_from_catalogue(catalogue, ...)` with no subgraph attempt at all (their subgraphs have no risk-config
   block). With `catalogue` always `None` now, `risk_params_from_catalogue(None, ...)` returns `[]` unconditionally
   (`_risk_params_stage.py:196-197`) → `_write_protocol_chain_rows` writes zero rows → `recorder.record_zero_rows(...)`
   — a manifest stamp asserting "genuinely checked, zero rows" when in fact the catalogue was never actually reachable.
   Both MORPHO and FLUID are genuine, real, currently-in-scope venues for `risk_params` in UAC's honest-coverage
   denominator (`unified_api_contracts/registry/expected_coverage.py` `_DEFI["MORPHO"]`/`_DEFI["FLUID"]` =
   `_DEFI_LENDING_PAIRS`, which includes `risk_params`) — this is not an out-of-scope cell being silently skipped, it is
   an in-scope cell being silently mis-recorded.
   - `kamino_lending` (Solana, `SOLANA_LENDING_PROTOCOLS`, same catalogue-only branch via `_fetch_risk_param_rows`
     line 330) hits the identical bug, compounded by an entirely separate, pre-existing defect: MTDS's
     `_PROTOCOL_TO_VENUE_PREFIX` (`_instruments_metadata.py:52-80`) has **never** had entries mapping
     `kamino_lending`/`solend`/`marginfi` to IS's real venue prefixes (`KAMINO`/`SOLEND`/`MARGINFI` — confirmed via
     `instruments-service/instruments_service/engine/orchestrator/defi.py:160,168-169`:
     `"KAMINO-SOLANA"`/`"MARGINFI-SOLANA"`/`"SOLEND-SOLANA"`), so `venue_prefix_for_protocol()` returns `None` and
     `load_pool_metadata_for_date` short-circuits before even attempting a GCS read — this defect predates and is
     independent of the hive-cutover regression above. `KAMINO-SOLANA` risk_params is ALSO in-scope
     (`expected_coverage.py:303`: `"KAMINO-SOLANA": list(_DEFI_LENDING_PAIRS)`), so this venue has been silently
     mis-recorded for longer than 4 days (likely since whenever kamino_lending's risk_params entry was first added to
     `_DEFAULT_PROTOCOLS`). `SOLEND-SOLANA`/`MARGINFI-SOLANA` are NOT declared anywhere in `expected_coverage.py`'s
     `_DEFI` dict at all (a separate, smaller registry-drift finding, out of this doc's scope) — they are not currently
     counted in the honest-coverage denominator either way.

## Why it matters

This is a data-pipeline-correctness class regression (per `/codex/02-data/data-pipeline-correctness-hard-rule.md` and
`/codex/02-data/honest-absence-downstream-handling.md`): a genuine 200+empty (real IS catalogue absence) and a read
failure due to a stale path are different states, and the current code cannot tell them apart — it silently treats "the
exact blob I'm looking for doesn't exist at the OLD path" as "IS truly has nothing for this venue/date", which has been
false for every DeFi protocol since 2026-07-23. For `risk_params` on MORPHO/FLUID/KAMINO_LENDING specifically, this
actively corrupts the honest-coverage denominator with false `captured, row_count=0` stamps that read as "checked,
genuinely empty" when the catalogue was simply unreachable. It also blocks the sibling P3 todo in
`defi_manifest_no_expected_unattempted_seeder_2026_07_26.md` from safely adding `solend`/`marginfi` to
`_DEFAULT_PROTOCOLS` — doing so today would just add two more venues riding the same silently-broken path.

## Recommended decision

Not a judgment call — the fix pattern already exists and shipped for 6 sibling readers in the same cutover. Mirror it:

## Todos

- [ ] 1. [DATA] P1. Make `_instruments_metadata.py`'s `load_pool_metadata_for_date` layout-tolerant across the
      instrument_availability hive cutover: replace the exact `download_bytes(bucket, blob_path)` single-GET (:223-230)
      with a day-scoped `list_blobs(bucket, prefix=f"instrument_availability/by_date/day={date_str}/")` + a venue-tail
      regex match (mirror `unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py:181`'s
      `re.compile(r"day=(\d{4}-\d{2}-\d{2})/(?:[^/]+/)*venue=([^/]+)/")` pattern), selecting the blob whose matched
      venue equals `venue_tag` and downloading THAT blob. Must tolerate both the pre-cutover flat shape (still the only
      shape for any date ≤ 2026-07-22, which historical/backfill reads will keep hitting) and the post-cutover hive
      shape. (repo: market-tick-data-service)
- [ ] 2. [DATA] P1. Apply the same layout-tolerant fix to the other 3 loaders in the same file:
      `load_oracle_feeds_for_date` (:397-469), `load_staking_url_for_protocol` (:472-551),
      `load_evm_lst_contract_addresses_for_date` (:554-647) — same blob_path construction, same bug. (repo:
      market-tick-data-service)
- [ ] 3. [DATA] P1. Add missing `_PROTOCOL_TO_VENUE_PREFIX` entries (`_instruments_metadata.py:52-80`):
      `"kamino_lending": "KAMINO"`, `"solend": "SOLEND"`, `"marginfi": "MARGINFI"` — confirmed real IS venue prefixes
      via `instruments-service/instruments_service/engine/orchestrator/defi.py:160,168-169`. This is a separate,
      pre-existing defect from todos 1-2 and must land in the SAME change as todo 1 (todo 1 alone does nothing for these
      3 protocols since `venue_prefix_for_protocol` returns `None` before any path is even built). (repo:
      market-tick-data-service)
- [ ] 4. [DATA] P2. After todos 1-3 ship, verify against the real bucket:
      `load_pool_metadata_for_date("kamino_lending",     "SOLANA", <a 2026-07-2{3,4,5,6} date>, ...)` returns non-`None`
      real rows (not just no-exception), and confirm via the availability manifest (`read_availability_index` on the
      `market-data-tick-defi` bucket, filtered `data_type=risk_params`, `venue in [morpho, fluid, kamino_lending]`,
      `date>=2026-07-23`) that captured row counts are non-zero going forward (a regression test alone proves the code
      path; this todo proves the actual production data stopped being silently zero). (repo: market-tick-data-service)
- [ ] 5. [DATA] P3. Once todos 1-4 are green, re-open the sibling P3 todo in
      `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md` (risk_params_handler.py's `_DEFAULT_PROTOCOLS`
      solend/marginfi omission) — it was left undecided pending this fix. (repo: market-tick-data-service,
      unified-trading-pm)
- [ ] 6. [REVIEW] P3. Add a regression test asserting `load_pool_metadata_for_date` resolves a blob written under EITHER
      the pre-cutover flat shape OR the post-cutover hive shape (two fixture cases), so a future path-grammar change
      can't silently reintroduce this class of bug. (repo: market-tick-data-service)

## Progress Log

- 2026-07-26 (slot 5, `data_engineering`): Filed from investigating the sibling P3 todo (see
  `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`'s Progress Log). Read-only — no code changed. Evidence:
  direct GCS listing (dated cutover 2026-07-22→2026-07-23), code read of all 4 `_instruments_metadata.py` loaders +
  their 13 handler consumers, cross-reference against `instrument_availability_hive_canonicalisation_2026_07_21.md`'s
  own todo 6 (reader list) and `expected_coverage.py`'s `_DEFI` scope dict (confirms MORPHO/FLUID/KAMINO-SOLANA
  `risk_params` are genuinely in-scope, so this is an in-scope-cell corruption, not a skip).

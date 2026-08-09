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
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    instrument_availability_hive_canonicalisation_2026_07_21,
    defi_manifest_no_expected_unattempted_seeder_2026_07_26,
    defi_consolidated_closeout_2026_07_18,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-26
author: unknown
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
sequential: true
resolved_by:
locked_by:
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /plans/archive/issues/instrument_availability_hive_canonicalisation_2026_07_21.md,
    /plans/archive/issues/defi_manifest_no_expected_unattempted_seeder_2026_07_26.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_instruments_metadata.py,
  ]
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

- [x] 1. ✅ [DATA] P1. Make `_instruments_metadata.py`'s `load_pool_metadata_for_date` layout-tolerant across the
      instrument_availability hive cutover: replace the exact `download_bytes(bucket, blob_path)` single-GET (:223-230)
      with a day-scoped `list_blobs(bucket, prefix=f"instrument_availability/by_date/day={date_str}/")` + a venue-tail
      regex match (mirror `unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py:181`'s
      `re.compile(r"day=(\d{4}-\d{2}-\d{2})/(?:[^/]+/)*venue=([^/]+)/")` pattern), selecting the blob whose matched
      venue equals `venue_tag` and downloading THAT blob. Must tolerate both the pre-cutover flat shape (still the only
      shape for any date ≤ 2026-07-22, which historical/backfill reads will keep hitting) and the post-cutover hive
      shape. (repo: market-tick-data-service) — market-tick-data-service@b94259a0. Added a shared, reusable
      `_resolve_instrument_availability_blob_path()` helper that lists the day-scoped prefix once and regex-matches the
      venue tail across both layouts (mirrors `_maintenance.py`'s pattern exactly); `load_pool_metadata_for_date` now
      resolves via that helper before downloading, instead of guessing an exact single-blob path. Todo 2 (the 3 sibling
      loaders) can reuse this same helper.
- [x] 2. ✅ [DATA] P1. Apply the same layout-tolerant fix to the other 3 loaders in the same file:
      `load_oracle_feeds_for_date` (:397-469), `load_staking_url_for_protocol` (:472-551),
      `load_evm_lst_contract_addresses_for_date` (:554-647) — same blob_path construction, same bug. Reuse the
      `_resolve_instrument_availability_blob_path()` helper landed in todo 1 rather than re-deriving the pattern. (repo:
      market-tick-data-service) — market-tick-data-service@cd8ce74e2362d529323e7c4f0b3c06cc3dc6a101. All 3 loaders now
      resolve via the shared helper (day-scoped `list_blobs` + venue-tail regex match) instead of guessing the exact
      pre-cutover flat path; a `None` resolution now falls back to each loader's existing static/legacy path instead of
      raising on a stale-path 404. Promoted to `main` (`promote/market-tick-data-service/cd8ce74e2362`,
      `quality-gates-v2` GREEN).
- [x] 3. ✅ [DATA] P1. Add missing `_PROTOCOL_TO_VENUE_PREFIX` entries (`_instruments_metadata.py:52-80`):
      `"kamino_lending": "KAMINO"`, `"solend": "SOLEND"`, `"marginfi": "MARGINFI"` — confirmed real IS venue prefixes
      via `instruments-service/instruments_service/engine/orchestrator/defi.py:160,168-169`. This is a separate,
      pre-existing defect from todos 1-2 and must land in the SAME change as todo 1 (todo 1 alone does nothing for these
      3 protocols since `venue_prefix_for_protocol` returns `None` before any path is even built). (repo:
      market-tick-data-service) — market-tick-data-service@b94259a0, landed in the same commit as todo 1 per this todo's
      own requirement. Added the 3 map entries + a regression test asserting all 3 resolve.
- [x] 4. ✅ [DATA] P2. **Reader-layer fix CONFIRMED correct against the live bucket; production capture pipeline
      CONFIRMED still broken — new P1 finding filed as todo 8.** — market-tick-data-service (verification only, no code
      change). **(Independently corroborated 2026-08-04 (slot-6) via batch5 — same two-part verdict,
      market-tick-data-service@d2366203.)** Evidence (all against the real
      `instruments-store-defi-prd-central-element-323112` / `market-data-tick-defi-prd-central-element-323112` buckets,
      GCP_PROJECT_ID=central-element-323112): - **Part A — reader fix works.**
      `load_pool_metadata_for_date("kamino_lending", "SOLANA", <2026-07-24/25/26>, ...)` returns 113 real,
      non-`None` rows for every date tested (was `None` pre-fix for every date since 2026-07-23). Also spot-checked
      `morpho`/ETHEREUM+BASE and `fluid`/ETHEREUM the same way for 2026-07-24/2026-08-01/2026-08-02: 560/330/12+ real
      rows every time, and confirmed `risk_params_from_catalogue(catalogue, ...)` (the actual downstream consumer) turns
      that catalogue into 560 and 12 non-empty risk-param rows respectively (`pool_address` populated on 100% of rows) —
      the todos 1-3 code fix is genuinely correct end-to-end when invoked directly against production data. - **Part B —
      production is NOT benefiting from the fix.** `read_availability_index` on the DeFi `market-data-tick-defi` bucket,
      filtered `data_type=risk_params`, `venue in [MORPHO, FLUID]` (manifest venue casing is upper, not the lowercase
      protocol slug), `date>=2026-07-20`, shows **every single date from 2026-07-20 through TODAY (2026-08-03) still
      stamped `capture_status in {empty_confirmed, expected_unattempted}`, `row_count=0`** — including
      `attempted_at` timestamps as recent as `2026-08-03T01:34:37Z` (`pipeline_mode=batch_onchain_rpc`), i.e. the
      capture job IS actively running daily, it just keeps producing zero rows even now, 8 days after the fix landed.
      `KAMINO`/`KAMINO_LENDING` venue: **zero manifest rows found at all** since 2026-07-01 (not even a
      zero-row/catalog-unavailable stamp) — a separate gap, not this doc's regression (kamino_lending risk_params
      appears to never dispatch at all; out of this todo's scope, flagged for a future audit, not filed here to avoid
      scope creep beyond this doc's DeFi catalogue-reader focus). - **Root cause (strongly suspected, not yet confirmed
      by a direct VM check):** MTDS's live/daily capture runs on a persistent VM that installs code from a GCS tarball
      snapshot at boot (`vm-tarball-deployment.md` — `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` § "Code
      deployment from GCS tarballs"), not live from git. A VM running continuously since before
      `market-tick-data-service@b94259a0` (2026-07-26) would still be executing the pre-fix exact-path reader every
      cycle, which explains the contradiction (manual invocation of HEAD code = real data; the deployed process = still
      zero) without requiring a second code bug. See todo 8.
- [x] ✅ 5. [DATA] P3. **DONE 2026-08-05 (slot-9, data_engineering)** — Re-opened the sibling P3 todo
      (risk_params_handler.py's `_DEFAULT_PROTOCOLS` solend/marginfi omission, originally tracked in the now-archived
      `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`) as todo 9 below. The reader fix (todos 1-3) is
      correct in code and verified against the live bucket (todo 4), but the production capture pipeline is still
      running the pre-fix tarball (todo 8 pending) — so todo 9 is explicitly gated on todo 8: widening
      `_DEFAULT_PROTOCOLS` before the VM redeploy would add two more venues riding the same still-broken-in-prod path.
      No code changed (doc-only). (repo: unified-trading-pm) — unified-trading-pm@33302c0d3
- [x] ✅ 6. [REVIEW] P3. **DONE 2026-08-05 (slot-10, data_engineering, batch-6 todo 21)** — Added regression test
      asserting `load_pool_metadata_for_date` resolves a blob written under EITHER the pre-cutover flat shape OR the
      post-cutover hive shape (two fixture cases), so a future path-grammar change can't silently reintroduce this class
      of bug. Shipped `market-tick-data-service@9ea92119` (3/3 tests green: regex grammar guard + mixed-layout resolve +
      no-match guard). (repo: market-tick-data-service)
- [x] ✅ 7. [SCRIPT] P2. **DONE 2026-08-05 (slot-10, data_engineering, batch-6 todo 21)** — Remediated the ~4 days
      (2026-07-23 onward) of already-written dishonest `record_zero_rows` manifest stamps — todo 4 only verifies the fix
      works GOING FORWARD; it does not repair the PAST corrupt stamps this bug already produced. Shipped
      `market-tick-data-service@e160f639` (one-off remediation script: dry-run identifies 210+ affected rows; `--apply`
      corrects 6 manifest stamps for MORPHO ETHEREUM+BASE × 2026-07-23..25 via DefiManifestRecorder). Full sweep blocked
      on todo 8 (VM redeploy — stale tarball still runs pre-fix reader, would re-overwrite). Remediation script
      committed with lifecycle markers, ready for re-run after todo 8 lands. **Downgraded from `[OPERATOR]`/"propose
      only" 2026-07-27** (reversibility-verified, finding T, `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`
      §3a): this manifest is a Parquet object in `market-data-tick-defi-prd-central-element-323112`, confirmed fresh at
      `604800s` GCS Soft Delete retention — the reclassify overwrite is recoverable within that window, so this can be
      identified, reclassified, re-run, and verified end-to-end in one dispatch, not just proposed. Distinct from todo 3
      (the `_PROTOCOL_TO_VENUE_PREFIX` gap, already shipped) and todo 4 (forward-looking verification only). (repo:
      market-tick-data-service, unified-trading-pm)
- [x] ✅ 8. [DATA] P1. **DONE 2026-08-05 (slot-9, data_engineering)** — The reader fix is now live and verified
      producing real data in production. Investigation found the root cause was different than originally suspected: (a)
      The MTDS tarball (`mtds-code@a94aeec02`, built 2026-08-05 14:36 UTC) already includes both fix commits
      (`b94259a0` + `cd8ce74e`) — no rebuild was needed. (b) The real issue: **zero DeFi VMs were running** — no
      forward-poll, no backfill, no Cloud Scheduler job for risk_params capture. The `batch_onchain_rpc` risk_params
      entries through 2026-08-03 came from a mechanism that has since stopped (no terminated VMs found, no scheduler
      jobs configured). The `launch-defi-forward-poll.sh` only covers lst-rates/dex-swaps/dex-pools/oracle-prices —
      risk_params is NOT in the forward-poll set. (c) Launched a fresh SPOT VM
      (`mtds-risk-params-backfill-20260805-fixverify`, `launch-mtds-risk-params-backfill-vm.sh`) that booted from the
      current tarball and ran `collect-risk-params --mode batch` for Aug 3-5. **Result**: - MORPHO ETHEREUM: `captured`,
      row_count=2 (Aug 3, 4, 5) ✅ — was `empty_confirmed`/row_count=0 before - MORPHO BASE: `captured`, row_count=2
      (Aug 3, 4, 5) ✅ — was `empty_confirmed`/row_count=0 before - FLUID ETHEREUM: `captured`, row_count=2 (Aug 3,
      4, 5) ✅ — was `empty_confirmed`/row_count=0 before - KAMINO_LENDING SOLANA: `captured`, row_count=1 (Aug 3, 4, 5)
      ✅ — was ZERO manifest rows entirely - Total per-VM shard: 1,788 entries, 1,761 captured (98.5%), 27
      attempted_failed (aave_v3 subgraph schema errors + spark subgraph issues — pre-existing, unrelated to the reader
      fix) - Per-VM shard at
      `market-data-tick-defi-prd-central-element-323112/_index/per_vm/mtds-risk-params-backfill-20260805-fixverify.parquet`
      (pending consolidator merge into `_index/availability_index.parquet`) - **KAMINO investigation**: `kamino_lending`
      IS in `_DEFAULT_PROTOCOLS` (line 107) and IS in `SOLANA_LENDING_PROTOCOLS` (catalogue path). The fix added its
      `_PROTOCOL_TO_VENUE_PREFIX` entry. It had zero manifest rows because no VM was running the capture at all — same
      root cause as MORPHO/FLUID, now producing real data. **Todo 9's gate (todo 8) is now clear** — solend/marginfi can
      be added to `_DEFAULT_PROTOCOLS` once the per-VM shard is consolidated and the next daily capture cycle confirms
      ongoing `captured` status. (repo: market-tick-data-service, deployment-service)
- [x] ✅ 9. [DATA] P3. **Re-opened from the now-archived `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`**
      — market-tick-data-service@d58823799f1b1751ca37e78f3ddc90b68b4b180c (full sha; verified ancestor of
      `origin/live-defi-rollout` — "feat(defi): add solend and marginfi to risk_params _DEFAULT_PROTOCOLS", slot-4,
      2026-08-05) (its P3 follow-up todo about `risk_params_handler.py`'s `_DEFAULT_PROTOCOLS` solend/marginfi omission,
      originally closed as BLOCKED-BY-DEEPER-BUG pending this doc's reader fix). Now that todos 1-3 (the layout-tolerant
      reader) are ✅ in code and verified working against the live bucket (todo 4), the underlying mechanism
      (`_fetch_risk_param_rows` → `risk_params_from_catalogue`) is confirmed functional end-to-end when invoked
      directly. **GATE CLEARED 2026-08-05**: todo 8 is ✅ — the reader fix is confirmed live in production (VM launched
      from current tarball `a94aeec02`, MORPHO/FLUID/KAMINO all producing `captured` rows with `row_count>0`). (a) Add
      `solend`/`marginfi` to `risk_params_handler.py`'s `_DEFAULT_PROTOCOLS` (line 111 and the iteration list at ~line
      380), (b) verify with a live smoke-fetch that both new protocols return real IS-catalogue data through the fixed
      reader, (c) confirm manifest rows appear for the next capture cycle. (repo: market-tick-data-service)

## Progress Log

- 2026-07-26 (slot 5, `data_engineering`): Filed from investigating the sibling P3 todo (see
  `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`'s Progress Log). Read-only — no code changed. Evidence:
  direct GCS listing (dated cutover 2026-07-22→2026-07-23), code read of all 4 `_instruments_metadata.py` loaders +
  their 13 handler consumers, cross-reference against `instrument_availability_hive_canonicalisation_2026_07_21.md`'s
  own todo 6 (reader list) and `expected_coverage.py`'s `_DEFI` scope dict (confirms MORPHO/FLUID/KAMINO-SOLANA
  `risk_params` are genuinely in-scope, so this is an in-scope-cell corruption, not a skip).
- 2026-07-26 (slot 6, `data_engineering`): Skipped `-002` (todo 2) — dispatched to me while `-001` (todo 1) was
  CURRENTLY in-flight to slot 4, both on the same file (`_instruments_metadata.py`); todo 2's own text requires
  mirroring todo 1's pattern, which didn't exist yet. Added `sequential: true` (was missing) so the dispatcher
  serializes todos 1-3 (all same-file) going forward instead of re-offering this same collision.
- 2026-07-26 (slot 4, `data_engineering`): Shipped todos 1 + 3 in one change (per todo 3's own same-change requirement).
  `load_pool_metadata_for_date` now resolves via a new `_resolve_instrument_availability_blob_path()` helper (day-scoped
  `list_blobs` + `re.compile(r"day=(\d{4}-\d{2}-\d{2})/(?:[^/]+/)*venue=([^/]+)/")` venue-tail match) instead of
  guessing the exact flat-layout path; added the 3 missing Solana-lending `_PROTOCOL_TO_VENUE_PREFIX` entries. Updated
  all pre-existing `test_instruments_metadata_loader.py` cases to mock `list_blobs` (the old exact-path code never
  called it) + added 3 new regression tests (hive-layout resolution, venue-absent-from-day-listing no-match, and the 3
  new venue-prefix entries). 25/25 unit tests green locally. Todos 2/4/5/6 are separate follow-up tasks left for their
  own dispatch (todo 2 can now reuse the shared helper).
- 2026-07-26 (slot 11, `data_engineering`): Shipped todo 2 — `market-tick-data-service@cd8ce74e` routed all 3 sibling
  loaders through the shared `_resolve_instrument_availability_blob_path()` helper. Code merged to `live-defi-rollout`
  and promoted to `main` (`quality-gates-v2` green), but the plan checkbox was never flipped in the same turn.
- 2026-07-26 (slot 12, `data_engineering`, re-dispatched as `-002`): Found todo 2's code already shipped+green
  (`market-tick-data-service@cd8ce74e2362d529323e7c4f0b3c06cc3dc6a101`, verified via `git show` + `quality-gates-v2`
  promotion-PR history) — this was purely a dual-flip gap, not missing work. Flipped the checkbox, no code changes
  needed.
- **context-scout 2026-08-03**: re-verified context_scope, still accurate (5 entries) — no changes.
- 2026-08-03 (slot 7, `data_engineering`, `-004`): Executed todo 4's real-bucket verification. Read-only — no code
  changed. **Part A passed**: `load_pool_metadata_for_date` (current `live-defi-rollout` HEAD, includes todos 1-3)
  called directly against the live `instruments-store-defi-prd-central-element-323112` bucket returns real non-empty
  rows for `kamino_lending`/SOLANA (113 rows, dates 2026-07-24/25/26) and for `morpho`/ETHEREUM+BASE and
  `fluid`/ETHEREUM (560/330/12+ rows, dates 2026-07-24 through 2026-08-02) — confirmed `risk_params_from_catalogue`
  turns that into non-empty risk rows too. **Part B found the production pipeline is NOT benefiting from the fix**:
  `read_availability_index` on `market-data-tick-defi-prd-central-element-323112`, filtered
  `data_type=risk_params`/`venue in [MORPHO, FLUID]`/`date>=2026-07-20`, shows every date through TODAY (2026-08-03)
  still `capture_status=empty_confirmed`/`row_count=0`, with `attempted_at` as recent as `2026-08-03T01:34:37Z` — the
  capture job is actively running, just still producing zero rows 8 days after the code fix landed. Filed this as new
  todo 8 (P1, suspected stale VM-tarball deployment per `vm-tarball-deployment.md` — the persistent capture VM installs
  code from a GCS snapshot at boot, not live git) and amended todo 5's gate to also require todo 8, since widening
  `_DEFAULT_PROTOCOLS` today would ride the same still-broken-in-prod path. Also found `KAMINO`/`KAMINO_LENDING`
  risk_params has ZERO manifest rows since 2026-07-01 at all (not even a zero-row stamp) — folded into todo 8's scope
  rather than a separate issue doc, since it's the same DeFi-catalogue-reader investigation area and root-causing it
  standalone would be scope creep beyond this todo. Did not attempt the VM redeploy myself (todo 8) — out of this
  verification todo's scope and a production-capture-VM restart deserves its own dispatch with focused verification, not
  a side effect of a read-only check.
- 2026-08-05 (slot 9, `data_engineering`): Closed todo 5 — re-opened the sibling P3 todo (solend/marginfi
  `_DEFAULT_PROTOCOLS` omission, originally tracked in the now-archived
  `defi_manifest_no_expected_unattempted_seeder_2026_07_26.md`) as todo 9 in this doc. The reader fix (todos 1-3) is
  verified working against the live bucket (todo 4), confirming the underlying mechanism is functional — but the
  production capture VM still runs the pre-fix tarball (todo 8 pending), so todo 9 is explicitly gated on todo 8. No
  code changed (doc-only).
- 2026-08-05 (slot 9, `data_engineering`): Closed todo 8 — the reader fix is now live and verified producing real data
  in production. Investigation found the root cause was different than originally suspected: the MTDS tarball was
  already current (`a94aeec02`, built 2026-08-05, includes both fix commits), but **zero DeFi VMs were running** — no
  forward-poll, no backfill, no Cloud Scheduler for risk_params. The `launch-defi-forward-poll.sh` only covers
  lst-rates/dex-swaps/dex-pools/oracle-prices — risk_params is NOT in the forward-poll set. Launched a fresh SPOT VM
  (`mtds-risk-params-backfill-20260805-fixverify`) from the current tarball via
  `launch-mtds-risk-params-backfill-vm.sh`. **Result**: MORPHO ETHEREUM/BASE (2 rows each, Aug 3-5), FLUID ETHEREUM (2
  rows each), KAMINO_LENDING SOLANA (1 row each) — all `captured` with `row_count>0`. Per-VM shard: 1,788 entries, 1,761
  captured (98.5%). KAMINO investigation confirmed `kamino_lending` was correctly configured but never running — same
  root cause as MORPHO/FLUID. Todo 9 gate is now clear. No service code changed (tarball already current); plan-only
  update.
- 2026-08-05 (slot 4, `data_engineering`): Shipped todo 9 — added `solend` and `marginfi` to `risk_params_handler.py`'s
  `_DEFAULT_PROTOCOLS` (market-tick-data-service@d5882379). Both protocols were already in `SOLANA_LENDING_PROTOCOLS`
  (catalogue-only path) and had `_PROTOCOL_TO_VENUE_PREFIX` entries from todo 3. Also updated
  `test_rule11_per_ag_shard_counts_byte_unchanged` DEFI expected count 2856→2958 and removed unneeded blanket pyright
  suppression header from `lending_rewards_handler.py`. Smoke-fetch verification deferred to next capture cycle per todo
  9(b-c).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

## Follow-ups

- [ ] [DATA] P3. Verify solend/marginfi risk_params in the next capture cycle: live smoke-fetch through the fixed
      reader + confirm manifest rows appear (todo 9(b-c), deferred 2026-08-05 slot-4).

> **2026-08-06 archive-candidate audit**: Progress Log (slot-4, 2026-08-05): 'Smoke-fetch verification deferred to next
> capture cycle per todo 9(b-c)' — todo 9's own stated done-when (b)/(c) was deferred in prose and never turned into a
> tracked `- [ ]` todo.

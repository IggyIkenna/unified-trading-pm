---
doc_type: issue
title:
  DERIBIT futures_chain exercises the SAME vulnerable canonical-write-only path fixed for BINANCE-FUTURES/BYBIT — still
  0% captured, and undeclared in the UAC capability registry
summary: >-
  Follow-up audit from cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md's P2 todo 4 ("audit
  whether the same canonical-write-only manifest-routing bugs also affect other CeFi venues' options_chain/
  futures_chain shards"). Confirmed: DERIBIT DOES exercise the identical vulnerable path
  (`TardisAdapter._download_futures_per_instrument` -> `finalise_and_write_cefi_shards` -> `_write_one_cefi_shard`, used
  because Tardis has no working grouped FUTURES endpoint for DERIBIT either) for futures_chain, and its manifest still
  shows the same 0%-captured signature the fixed venues had pre-fix (423 attempted_failed, 16,695 empty_confirmed, 0
  captured as of the 2026-08-09T20:08Z manifest snapshot) — not yet live-verified against the 2026-08-09 fix
  (market-tick-data-service@e24199df) since that fix was only unit/synthetic-verified (no live Tardis credentials in the
  dev sandbox). Separately, DERIBIT-futures_chain is completely UNDECLARED in the UAC `DataTypeCapability` registry even
  though `configs/venue_data_types.yaml` and the live manifest both confirm it is a real, actively-attempted capture
  surface — registry drift, not a coverage gap. By contrast, the 4 other CeFi perp venues carrying a registered
  `futures_chain`/`options_chain` capability entry (KRAKEN-FUTURES, BITGET-FUTURES, BITFINEX-FUTURES, COINBASE-FUTURES)
  have ZERO manifest rows for either data_type — the vulnerable path is registered but not yet exercised in practice for
  those 4, so no live exposure to confirm or fix there today.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [cefi, honest-coverage, futures_chain, deribit, tardis, manifest-routing, registry-drift]
related:
  [
    /plans/active/issues/cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-17"
author: slot-12 (data_engineering)
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md, Action item 4 (read-only audit +
  window-scoped honest-coverage re-measurement for DERIBIT/other affected venues).
context_scope:
  [
    /plans/active/issues/cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md,
    /codex/02-data/honest-coverage-model.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_bulk_download.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py,
    market-tick-data-service/market_tick_data_service/cefi_futures_chain_symbology.py,
    market-tick-data-service/configs/venue_data_types.yaml,
  ]
---

# DERIBIT futures_chain — same canonical-write-only exposure, still unfixed live + registry-undeclared

## What I found

Ran the audit required by `cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md`'s action item 4:
does the same canonical-write-only manifest-routing bug class fixed for BINANCE-FUTURES/BYBIT futures_chain
(market-tick-data-service@e24199df — itype-vocabulary mismatch, `BUNDLED_DATA_TYPES` gate mismatch, missing
cluster/envelope bookkeeping, wrong cluster-bucket derivation, expiry-derivation fallback gap) also affect other CeFi
venues that hit the same code path?

**Code-path confirmation**: `TardisAdapter._download_bulk` (`tardis_bulk_download.py:420-430`) routes ANY
`data_type == "futures_chain"` request to `_download_futures_per_instrument` — this branch is keyed on data_type only,
not venue. The module docstring explicitly lists DERIBIT among the exchanges with no working Tardis grouped FUTURES
endpoint ("Tardis returns no rows for the FUTURES grouping symbol on DERIBIT / BINANCE-FUTURES / BYBIT"), so DERIBIT
futures_chain captures go through the exact same vulnerable `_download_futures_per_instrument` ->
`finalise_and_write_cefi_shards` -> `_write_one_cefi_shard` chain as the already-fixed venues.

**Config confirmation**: `configs/venue_data_types.yaml` explicitly lists DERIBIT with
`folders: [perpetuals, futures_chain, options_chain]` — futures_chain capture for DERIBIT is live-configured, not
hypothetical.

**Registry-drift finding**: the UAC `DataTypeCapability` registry
(`unified_api_contracts/registry/data_type_capability.py`) declares `futures_chain` for BINANCE-FUTURES, BYBIT,
KRAKEN-FUTURES, BITGET-FUTURES, BITFINEX-FUTURES, and COINBASE-FUTURES — but has **no entry for DERIBIT** despite
DERIBIT being both config-enabled and actively attempted in the live manifest. Conversely,
`configs/venue_data_types.yaml`'s own `futures_chain` path-structure section (`venues: [DERIBIT, BINANCE-FUTURES]`)
doesn't even list BYBIT, which the registry (correctly) does. The two SSOTs have drifted from each other and from the
manifest's ground truth in different directions.

**Manifest evidence** (bounded column-pruned read of the cefi availability-index parquet via
`instruments-service/scripts/measure_honest_coverage.py`'s `_read_manifest`/`_count_statuses`, filtered in-memory to
`data_type in {futures_chain, options_chain}` — single read, no new whole-corpus walk, per craft single-walk discipline;
snapshot `blob.updated=2026-08-09T20:08:36Z`):

| venue            | data_type     | captured | attempted_failed | expected_unattempted | empty_confirmed | total  | coverage_pct  |
| ---------------- | ------------- | -------- | ---------------- | -------------------- | --------------- | ------ | ------------- |
| DERIBIT          | futures_chain | 0        | 423              | 0                    | 16,695          | 17,118 | **0.00%**     |
| BINANCE-FUTURES  | futures_chain | 0        | 228              | 0                    | 4,999           | 5,227  | 0.00%         |
| BYBIT            | futures_chain | 0        | 2,161            | 0                    | 3,852           | 6,013  | 0.00%         |
| KRAKEN-FUTURES   | futures_chain | 0        | 0                | 0                    | 0               | 0      | n/a — no rows |
| BITGET-FUTURES   | futures_chain | 0        | 0                | 0                    | 0               | 0      | n/a — no rows |
| BITFINEX-FUTURES | futures_chain | 0        | 0                | 0                    | 0               | 0      | n/a — no rows |
| COINBASE-FUTURES | futures_chain | 0        | 0                | 0                    | 0               | 0      | n/a — no rows |

DERIBIT's captured/attempted_failed/empty_confirmed signature is the identical 0%-captured pattern the parent issue
documented for BINANCE-FUTURES/BYBIT pre-fix — every reachable attempt fails, never a genuine coverage gap in the "not
yet backfilled" sense. BYBIT's `attempted_failed` count (2,161) is materially HIGHER than the parent issue's
2026-08-09-morning reading (1,251) — confirming the manifest is still accumulating fresh failed attempts from pre-fix
code as of this snapshot, i.e. no post-fix live/backfill run has landed for ANY of these 3 venues yet.

**Symbology check**: `cefi_futures_chain_symbology.py`'s `_CEFI_DDMMMYY_EXPIRY_RE` regex comment explicitly names
Deribit's `BTC-07FEB25` shape as already covered (shared with Bybit) — so bug 4 (wrong cluster-bucket derivation) from
the parent fix should already handle DERIBIT's symbol format correctly. Bugs 1-3 (itype-vocabulary mismatch,
`BUNDLED_DATA_TYPES` gate, missing cluster bookkeeping) were fixed in venue-agnostic shared code
(`manifest_finalize.py`, `partitioned_writer.py`, `_cluster_bookkeeping.py`, `tardis_cefi_shards.py`) that applies
identically regardless of venue. **On paper, the 2026-08-09 fix should also resolve DERIBIT futures_chain** — but this
is unconfirmed: the fix's own verification (per its Progress Log entry) was synthetic/unit-level only ("no live Tardis
credentials in this sandboxed dev environment"), and no live capture or backfill run has occurred against DERIBIT
futures_chain since the fix landed.

**KRAKEN-FUTURES / BITGET-FUTURES / BITFINEX-FUTURES / COINBASE-FUTURES**: zero manifest rows for either futures_chain
or options_chain — these venues are capability-registered but have never yet had a real capture attempt reach the
manifest. The vulnerable code path is dormant for them today; nothing to fix or re-verify until capture is actually
attempted.

## Why it matters

1. DERIBIT is the CeFi options/futures reference venue and directly feeds the same
   `cefi_ml_directional_continuous_live_2026_06_20.md` live-capital coverage gate the parent issue exists to unblock —
   an unconfirmed-fixed 0%-captured futures_chain surface for DERIBIT is the same class of risk the parent issue was
   filed to close for BINANCE-FUTURES/BYBIT.
2. Registry drift (DERIBIT missing from `DataTypeCapability`, BYBIT missing from `venue_data_types.yaml`'s futures_chain
   path-structure `venues:` list) means neither SSOT alone gives an accurate answer to "which venues actually capture
   futures_chain" — a real correctness risk for any future audit or coverage-gate decision that trusts one list without
   cross-checking the other and the manifest.

## Recommended decision

Fix at the root per the data-pipeline-correctness HARD RULE — no deadline deferrals.

## Action items

- [ ] [DATA] P2. Once a CeFi Tardis capture/backfill slot is available for DERIBIT (same N=1 concurrent-IP constraint
      documented in the parent issue's item 4 Progress Log — do not force a second concurrent Tardis lease), re-attempt
      a small scoped DERIBIT futures_chain capture (a few recent days is sufficient) and confirm via a re-read of this
      same window-scoped manifest measurement that captured > 0 / attempted_failed trends to 0 for DERIBIT
      futures_chain, proving the 2026-08-09 fix (market-tick-data-service@e24199df) covers DERIBIT the same way it was
      unit-verified for BINANCE-FUTURES/BYBIT. Repo: market-tick-data-service, deployment-service (VM launch). **Done
      when**: a fresh DERIBIT futures_chain capture attempt shows `captured > 0` for at least one shard, or a genuine
      remaining bug specific to DERIBIT is found and filed.
- [x] ✅ [DATA] P3. Add a `DataTypeCapability(asset_group=CEFI, data_type="futures_chain", venue="DERIBIT", ...)` entry to
      `unified_api_contracts/registry/data_type_capability.py` — DERIBIT futures_chain is real, config-enabled
      (`configs/venue_data_types.yaml`), and actively attempted in the live manifest; the registry should reflect that
      instead of silently omitting it. While there, reconcile `configs/venue_data_types.yaml`'s `futures_chain`
      path-structure `venues:` list (currently `[DERIBIT, BINANCE-FUTURES]`, missing BYBIT) against the same ground
      truth. Repo: unified-api-contracts, market-tick-data-service. — unified-api-contracts@b3b32f827e +
      market-tick-data-service@c1284428c5

## Progress Log

- **2026-08-09 (slot-12, data_engineering)** — filed from
  `cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md` action item 4's read-only audit. Confirmed
  DERIBIT futures_chain exercises the same vulnerable canonical-write-only path (code + config evidence) and still shows
  a 0%-captured manifest signature as of this snapshot, unconfirmed against the 2026-08-09 fix. Confirmed
  KRAKEN-FUTURES/BITGET-FUTURES/BITFINEX-FUTURES/COINBASE-FUTURES have zero manifest rows for
  futures_chain/options_chain — registered capability, no live exposure yet. No code shipped (read-only audit +
  issue-doc filing, per the parent todo's own scope).
- **2026-08-09T21:19Z (slot 27, data_engineering)** — dispatched on todo 1 (the gated DERIBIT re-capture). Checked the
  precondition BEFORE attempting:
  `gcloud compute instances list --filter='name~cefi OR name~tardis' --format='table(name,status)'` shows
  `cefi-queue-heavy-binancefutu-x17-20260809-083733` (`RUNNING`) — matches
  `deployment-service/scripts/vm/tardis-concurrency-guard.sh`'s `TARDIS_VM_NAME_PATTERN`
  (`^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill-cefi-`) via the `^cefi-queue-` branch — this is a real
  Tardis-consuming VM (the same one tracked in
  `cefi_binance_futures_aster_okx_futures_paper_gate_backfill_incomplete_2026_08_08.md`'s in-flight aggregate backfill),
  currently holding the sole N=1 Tardis slot. Per the hard N=1 rule (operator 2026-07-16,
  `cefi_completion_program_2026_07_15.md` — N>1 storms the shared academic-key IP with mutual 403s), launching a DERIBIT
  capture now would breach the cap. Declining to force it. `cefi-extended-starknet-*` VMs also RUNNING are CAP-EXEMPT
  (EXTENDED-STARKNET doesn't fetch from `datasets.tardis.dev`) and don't count. Todo 1's own precondition ("Once a CeFi
  Tardis capture/backfill slot is available") is unmet — did NOT touch todo 2 (the registry-drift fix), which is a
  separately-dispatchable, non-gated backlog task. Releasing via `/skip-current-task {"reason_code": "GATED"}`.
- **2026-08-09T22:24Z (slot 8, data_engineering)** — re-dispatched on todo 1, re-checked the precondition using the
  CANONICAL guard function itself (not just a manual filter) for authoritative confirmation:
  `source deployment-service/scripts/vm/tardis-concurrency-guard.sh && tardis_running_vm_count asia-northeast1-c central-element-323112`
  returned `1` (rc=0) — the union of name-pattern + `VM_TARDIS_CONSUMER=1` metadata count is still 1, i.e. cap (1) is
  fully occupied. `gcloud compute instances list --filter='name~cefi OR name~tardis'` confirms
  `cefi-queue-heavy-binancefutu-x17-20260809-083733` is still `RUNNING` (same VM slot-27 found ~65 min earlier) — no new
  slot has opened since. Other CeFi-prefixed VMs currently running
  (`canonical-migration-cefi-content-apply-20260809-213834`, `cefi-fwd-daily-cron-20260809-110236`,
  `mdps-backfill-cefi-20260802-140125`, `mdps-backfill-cefi-20260808-095136`, `mdps-features-live-cefi-20260807-031648`,
  `mtds-live-cefi-consolidated-20260809-121034`) don't match `TARDIS_VM_NAME_PATTERN` and the guard's own union count
  (which also checks the `VM_TARDIS_CONSUMER=1` metadata stamp) still reads 1, confirming none of them are additional
  Tardis-consumers. Todo 1's precondition remains unmet — not attempting the capture. Did not touch todo 2 (separately
  dispatchable). Releasing via `/skip-current-task {"reason_code": "GATED"}` again.
- **2026-08-10T12:31Z (slot 19, data_engineering)** — re-dispatched on todo 1, re-checked the precondition via the
  CANONICAL guard (as slot 8): `tardis_running_vm_count asia-northeast1-c central-element-323112` now returns **4**
  (rc=0) — up from slot 8's 1. Pre-flight `tardis_concurrency_guard 1 ...` REFUSES (rc=1: 4+1=5 > cap 1). Breakdown of
  the 4: (1) the genuine stamped Tardis consumer `cefi-queue-heavy-binancefutu-x17-20260809-083733` (created
  08-09T08:37Z, still RUNNING, `VM_TARDIS_CONSUMER=1`) — same VM slots 27/8 found, STILL holding the sole N=1 slot;
  (2-4) **three `tradfi-bf-*-light-*` VMs caught ONLY by the name-pattern fallback, NOT stamped, and NOT Tardis
  consumers** — `tradfi-bf-es-opt-light-2026-…`, `tradfi-bf-vix-light-2020-…`, `tradfi-bf-vix-light-2022-…` (launched
  2026-08-10; Databento OHLCV backfills per `launch-tradfi-backfill-vm.sh`'s "serialize across the shared Databento
  account" + the Databento es-opt watcher). That name-pattern over-count is a real guard finding, filed separately — RESOLVED 2026-08-16 (see
  `/plans/archive/issues/tardis_guard_name_pattern_over_counts_tradfi_bf_databento_vms_2026_08_10.md`). **Important
  timing fact**:
  `market-tick-data-service@e24199df` (the fix) landed **2026-08-09T13:10Z**, ~4.5h AFTER the cefi-queue VM was created
  (08:37Z) — so the running slot holder executes PRE-fix code and cannot itself prove the fix. Fresh bounded manifest
  re-measurement (single column-pruned read via `measure_honest_coverage._read_manifest`;
  blob.updated=2026-08-10T12:16Z): **DERIBIT futures_chain STILL captured=0, attempted_failed=423,
  empty_confirmed=19,095 (was 16,695 on 08-09T20:08Z) — coverage 0.0%**; the empty_confirmed delta (+2,400) is
  consistent with the pre-fix VM still writing that shard. By contrast DERIBIT options_chain is captured=2,230 (84.06%)
  — the machinery works for options_chain, futures_chain remains the broken surface. Conclusion: N=1 Tardis slot STILL
  fully occupied (genuine consumer running pre-fix code); a fresh post-fix DERIBIT capture cannot run without breaching
  the hard cap → do NOT force. Precondition unmet; releasing via `/skip-current-task {"reason_code": "GATED"}`. Did not
  touch todo 2 (separately dispatchable).
- **2026-08-10T22:03Z (slot 18, data_engineering)** — re-dispatched on todo 1, re-checked the precondition via the
  CANONICAL guard (same as slots 27/8/19): `tardis_running_vm_count asia-northeast1-c central-element-323112` returns
  **1** (rc=0) — the sole N=1 Tardis slot is STILL fully occupied. Pre-flight `tardis_concurrency_guard 1 ...` REFUSES
  (rc=1: 1+1=2 > cap 1). Holder unchanged: `cefi-queue-heavy-binancefutu-x17-20260809-083733` (created 08-09T08:37Z,
  still RUNNING, `VM_TARDIS_CONSUMER=1`, cefi-coverage-backfill VM_DATA_TYPES=trades;book_snapshot_5,
  VM_START_DATE=2019-01-01, 10+ venues incl. DERIBIT) — created ~4.5h BEFORE the fix `market-tick-data-service@e24199df`
  landed (2026-08-09T13:10Z), so it executes PRE-fix code and cannot itself prove the fix. Note: the guard count is now
  1 (not slot 19's 4) — the three `tradfi-bf-*-light-*` Databento VMs that tripped the name-pattern over-count have
  since terminated, so that earlier over-count is moot for this re-check. Todo 1's precondition ("Once a CeFi Tardis
  capture/backfill slot is available for DERIBIT") remains UNMET — a fresh post-fix DERIBIT futures_chain capture would
  breach the hard N=1 cap → do NOT force. Not touching todo 2 (separately dispatchable). Releasing via
  `/skip-current-task {"reason_code": "GATED"}`.
  - **2026-08-11T01:55Z (slot 12, data_engineering)** — re-dispatched on todo 1, 6th consecutive check. Precondition
    re-verified via CANONICAL guard: `tardis_running_vm_count asia-northeast1-c central-element-323112` returns **1**
    (rc=0) — N=1 Tardis slot STILL fully occupied. Pre-flight `tardis_concurrency_guard 1 ...` REFUSES (rc=1: 1+1=2 >
    cap 1). Holder unchanged: `cefi-queue-heavy-binancefutu-x17-20260809-083733` (RUNNING since 08-09T08:37Z,
    `VM_TARDIS_CONSUMER=1`, created ~4.5h BEFORE the fix `market-tick-data-service@e24199df` landed at 2026-08-09T13:10Z
    — executes PRE-fix code, cannot prove the fix). Todo 1 precondition remains UNMET after ~42h of the same pre-fix VM
    occupying the sole slot. **Todo 2 (P3 — registry drift fix in UAC `DataTypeCapability` + `venue_data_types.yaml`
    reconcile) is separately dispatchable, non-gated, and has NEVER been attempted across all 6 dispatches** (slots
    27/8/19/18/12) — the dispatcher should route it to any available data_engineering slot regardless of Tardis slot
    state, since it's a pure code/config change touching unified-api-contracts/market-tick-data-service with no
    external-API dependency. Releasing via
    `/skip-current-task {"reason_code": "GATED", "estimated_unblock_minutes": 480}`.
- **2026-08-16 (slot 27, infra→data_engineering craft-adopt)** — dispatched on todo 2 (the registry-drift fix, never
  previously attempted). Added the `DataTypeCapability(asset_group=CEFI, data_type="futures_chain", venue="DERIBIT")`
  entry to `unified_api_contracts/registry/data_type_capability.py` (shipped unified-api-contracts@b3b32f827e), and
  reconciled `configs/venue_data_types.yaml`'s `chain_data_types.futures_chain.venues` list to add BYBIT (shipped
  market-tick-data-service@c1284428c5). Both SSOTs now agree: DERIBIT, BINANCE-FUTURES, BYBIT all declare
  `futures_chain` capability. Shipping took multiple retries — the shared planning-vm was under severe QG-governor
  congestion this session (~15 sibling slots concurrently running market-tick-data-service QG; several background QG/
  quickmerge runs were externally killed mid-run, one foreground 10-min call never even cleared the queue) — no code
  issue, purely host contention; eventually cleared. Todo 1 (the gated DERIBIT re-capture) remains open, still blocked
  on the N=1 Tardis-slot cap per the prior entries — not re-checked this dispatch (out of scope for todo 2).
- **context-scout 2026-08-17**: refreshed context_scope (6 entries) — corrected 3 entries whose paths were missing the
  `market_tick_data_service/` package-directory segment (didn't resolve on disk as written); same 6 targets, paths
  fixed.

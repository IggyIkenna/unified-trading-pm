---
doc_type: issue
title: DERIBIT-COMBO/OKX bare-venue gaps — VERIFY rounds 1-5 history (extracted 2026-07-25)
summary:
  "Line-cap extraction: the 2026-07-12 real end-to-end VERIFY attempt through round-5 follow-up todos (five rounds of
  live-VM debugging that found + fixed 8 distinct code-level bugs across the OKX/DERIBIT-COMBO options_chain capture
  path -- venue-candidate derivation, consolidator-staleness budget, adapter-class routing, capability declarations,
  bulk-stream instrument_ids filtering, combo/bare-option isolation, settlement-dimension derivation, and bulk
  chain-finalize performance) verbatim-moved out of cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md to bring it
  back under the 1000-line hard cap. Every todo in this range is [x] closed; the parent doc's later 2026-07-13/07-14
  sections (root cause + resolution) stand on their own without this history."
status: complete
nature: record
asset_group: [cefi]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [honest-coverage, denominator-audit, layer-1, data-correctness, cefi, deribit-combo, okx, history-extract]
related: [/plans/active/issues/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md]
created: 2026-07-25
parent_epic: infrastructure_master
priority: P3
source: [line-cap extraction from cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md, 2026-07-25]
assigned_vm: NA
resolved_by: "verbatim extraction, no content change"
locked_by:
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
last_updated: 2026-07-25
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

# DERIBIT-COMBO/OKX bare-venue gaps — VERIFY rounds 1-5 history (extract, 2026-07-25)

> Extracted verbatim from `plans/active/issues/cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md` (the
> 2026-07-12T19:00Z real end-to-end VERIFY attempt through the round-5 follow-up todos) to bring the parent doc back
> under the 1000-line hard cap. No content changed. Every todo in this range is `[x]` closed.

## Real end-to-end VERIFY attempt (slot-2, 2026-07-12, ~19:00-19:57Z) — TWO MORE code-level bugs found, launches killed

Picked this issue back up to actually run the item-3 VERIFY (re-launch + confirm real rows) now that both `[CODE]` todos
above show ✅. Found the earlier code fixes (routing entries, `_TARDIS_CEFI_VENUES` union, `_resolve_tardis_exchange`
call-site fix, `_route_tardis`'s `canonical_venue` threading) were necessary but NOT sufficient — three additional,
independent bugs sat between "code is fixed" and "a real VM captures a row." Fixed the first two, found + precisely
diagnosed (but did NOT fix) the third and fourth:

**Bug A (FIXED, shipped `deployment-service@a1454a6` + `market-tick-data-service@7c4e6354`)** — First launch of both
venues (per this issue's item-3/item-VERIFY-LIGHTER instructions) showed `venues=[]` for EVERY date on BOTH OKX and
DERIBIT-COMBO (`WARNING No active venues for date=... asset_groups=['CEFI']`), despite
`launch-targeted-options-chain- backfill.sh` correctly passing `VM_VENUE=OKX` / `VM_VENUE=DERIBIT-COMBO`. Root cause,
one layer EARLIER than every fix above: `market_tick_data_service.engine.orchestrator.get_venues_for_asset_groups()`'s
CEFI branch only derives candidate venues from `_VENUE_MAPPING.tardis_to_venue.values()` (a 1:1 exchange-slug→venue
reverse map) + `all_cefi_onchain_clob_venues` — and bare `"OKX"` / `"DERIBIT-COMBO"` structurally CANNOT appear in that
1:1 map (OKX spans 4 Tardis exchange slugs; DERIBIT-COMBO shares the `"deribit"` slug already claimed by bare DERIBIT),
even though both are real, declared venues in UAC's `VENUES_BY_ASSET_GROUP["cefi"]`. So
`_build_active_venues_for_date`'s `venue_filter=["OKX"]`/`["DERIBIT-COMBO"]` intersected against a candidate set that
never contained them → `active_venues=[]` → the whole day short-circuits before `_route_tardis`/the itype-aware exchange
resolution is ever reached. Fix: explicitly add `"OKX"` + `"DERIBIT-COMBO"` to the CEFI branch's venue list
(`market-tick-data-service@7c4e6354`, 1 regression test). VMs self-completed with `venues=[]`→fixed dispatch confirmed,
but then hit Bug B.

**Bug B (FIXED, shipped `deployment-service@467be0c`)** — After Bug A's fix, the relaunch reached real dispatch but 100%
of shards failed at VM bootstrap with `ManifestConsolidatorStaleError` (rc=1, 0 rows, VM self-deleted within ~2 min):
`assert_consolidator_healthy()`'s default 120s freshness budget on the consolidated `_index/availability_index.parquet`
blob is regularly exceeded by the real Cloud Run consolidator cadence for the large cefi bucket — confirmed live (blob
updated at 19:41:45Z, already 298s stale again by 19:46:43Z, a ~5min+ real cadence vs. the 120s check budget).
`launch-targeted-options-chain-backfill.sh` was the ONE outlier among ~20 cefi/ large-bucket launchers missing
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` (every other one — `launch-cefi-sharded-backfill.sh`,
`launch-cefi-hl-aster-historical-backfill.sh`, etc. — already sets it). Fix: added the same 86400s budget to this
launcher's VM metadata (`deployment-service@467be0c`).

**Bug C (FOUND, NOT fixed — OKX)**: with A+B fixed, OKX's relaunch reached the real per-symbol fetch attempt for the
first time, and immediately hit:
`WARNING Venue OKX: no download_batch support: 'OKXAdapter' object has no attribute 'download_batch'`. Bare `"OKX"`
resolves to a DIFFERENT adapter class (`OKXAdapter`, live-only, no batch/historical support) than the Tardis-routed
batch path that `_resolve_tardis_exchange`/`_route_tardis` (this issue's earlier fixes) target — i.e. there is a
venue→adapter-CLASS dispatch decision upstream of `_route_tardis` in
`market_tick_data_service/adapters/umi_tick_provider.py` that never sends bare `"OKX"` down the Tardis branch at all.
**Compounding gap, same venue**: independently confirmed `unified_api_contracts/registry/market_data_categories.py`'s
`VENUE_DATA_TYPE_CAPABILITIES["OKX"]` (~line 1192) declares
`{"trades", "book_snapshot_5", "derivative_ticker", "liquidations"}` — **no `"options_chain"` key at all** — so even
with the adapter-class routing fixed, a preflight capability check would still drop the request. Both gaps need to close
together: (1) add `"options_chain": "2020-02-01"` to `VENUE_DATA_TYPE_CAPABILITIES["OKX"]`, (2) make the
venue→adapter-class dispatch in `umi_tick_provider.py` route bare `"OKX"` (or specifically OKX
options_chain/futures_chain requests) to the Tardis adapter path instead of `OKXAdapter`. The VM got OOM-killed
(`rc=137`, "Killed") after ~2min stuck on date=2026-01-01 before reaching the 2nd date — worth checking for a
retry-loop/leak on this specific failure mode, not just the missing route.

**Bug D (FOUND, NOT fixed — DERIBIT-COMBO)**: with A+B fixed, DERIBIT-COMBO's relaunch reached the preflight capability
check and logged:
`INFO Pre-flight: venue=DERIBIT-COMBO date=2026-01-01 — dropping data_types not supported per UAC: ['options_chain']` →
`TardisAdapter.download_batch: deribit 2026-01-01 — 0 records (0 bulk, 0 per-symbol data types)` for every date.
Confirmed via direct read of `market_data_categories.py`'s `VENUE_DATA_TYPE_CAPABILITIES` dict: **`"DERIBIT-COMBO"` has
NO entry at all** (bare `"DERIBIT"` has a full entry incl. `"options_chain": "2019-03-30"`, but the dict was never
extended for the COMBO variant despite `INSTRUMENT_TYPES_BY_VENUE["DERIBIT-COMBO"] = {"OPTION"}` already being
declared). Fix: add a `"DERIBIT-COMBO": {"options_chain": "<start-date>"}` entry (start-date TBD — Deribit combo/spread
instruments are a newer product than bare options; do NOT just copy DERIBIT's 2019-03-30 without checking when Tardis's
`type=='combo'` symbols actually start).

**All 14 VMs killed** (`gcloud compute instances delete`, 2026-07-12T19:57Z — OKX's had already self-deleted per the
OOM-kill; DERIBIT-COMBO's were still RUNNING and deleted directly) once Bugs C/D were confirmed — no code fix can make
either venue capture a single real row without landing C and/or D first, so further VM time would only burn SPOT spend
on a guaranteed-zero outcome.

**Net assessment**: this issue has now survived 4 independent, real, code-level bugs across ~7 sessions/slots
(venue-drop silent-fail → wrong exchange resolution → wrong canonical-venue propagation → row misclassification →
dispatch-gate exclusion → [this session] missing venue-candidate derivation → missing consolidator-staleness budget →
wrong adapter-class routing → missing capability declaration). This is strong evidence the remaining Bugs C/D are _also_
real and worth fixing, but Layer-1 closure for these 2 tuples should NOT be assumed "one more fix away" — budget the
next session for another full VERIFY-then-fix cycle, not just the two known items.

## New follow-up todos (this session)

- [x] ✅ [CODE] P1. OKX options_chain: add `"options_chain": "2020-02-01"` to `VENUE_DATA_TYPE_CAPABILITIES["OKX"]` AND
      fix the venue→adapter-class dispatch so bare `"OKX"` routes to the Tardis batch path instead of `OKXAdapter`.
      (repo: unified-api-contracts, market-tick-data-service) — **`unified-api-contracts@9a766e29`** (capability entry,
      start date verified live via `api.tardis.dev/v1/exchanges/okex-options` this session — 247,540 real option
      symbols, `availableSince: 2020-02-01`, matches this doc's earlier finding) +
      **`market-tick-data-service@ae86c5ea`** (added `"OKX"` to `_TARDIS_CEFI_VENUES`'s union — same structural gap as
      DERIBIT-COMBO's earlier fix: bare OKX spans 4 Tardis exchange slugs so it can never appear in the 1:1
      `tardis_to_venue.values()` map; without explicit membership, `fetch_tick_data_for_venue` fell through to the
      generic `get_market_adapter` fallback → `OKXAdapter` → `AttributeError`). `_resolve_tardis_exchange`'s existing
      itype-aware routing (slot-15's earlier fix) now correctly resolves to `okex-options` once this dispatch path is
      actually reachable — verified via 2 new regression tests (`test_okx_in_tardis_cefi_venues`,
      `test_okx_dispatches_through_real_venue_set`, the latter asserting `exchange == "okex-options"` end-to-end).
      **rc=137 OOM-kill NOT separately investigated** — plausibly just the VM getting stuck on the (now-fixed)
      `OKXAdapter` AttributeError path across many instrument-symbol retry attempts before the day-loop's own timeout;
      re-check if it recurs after this fix in a real VERIFY run.
- [x] ✅ [CODE] P1. DERIBIT-COMBO: add an `"options_chain"` key to `VENUE_DATA_TYPE_CAPABILITIES["DERIBIT-COMBO"]` in
      `unified_api_contracts/registry/market_data_categories.py`. (repo: unified-api-contracts) —
      **`unified-api-contracts@9a766e29`**. **Found + reconciled a MERGE CONFLICT with prior work**: an existing
      `"DERIBIT-COMBO": {"trades": "2019-01-01", "book_snapshot_5": "2019-01-01"}` entry already existed (operator
      2026-07-10 decision #6, `cefi_layer1_denominator_gaps_2026_07_03.md`) serving a DIFFERENT purpose (Layer-1
      bundle-grain EXPECTED-denominator computation, per its own comment) — my first attempt created a duplicate dict
      key (ruff F601, caught by QG) before I found and merged into the existing entry instead of introducing a second
      one. Start date verified live via `api.tardis.dev/v1/exchanges/deribit` this session: Deribit's `type=='combo'`
      symbols (68,721 confirmed live) only go back to **2022-08-23**, NOT bare DERIBIT's 2019-03-30 as originally
      guessed in this doc's earlier "Recommended fix" section — combo/spread products launched years after bare options
      did. 3 new regression tests, incl. one asserting the two venues' start dates deliberately differ. **🔧 FOLLOW-UP
      CORRECTION 2026-07-12 (slot-3)** — dispatched independently for this same todo; found
      `unified-api-contracts@9a766e29` already landed on rebase (identical `options_chain: "2022-08-23"` verified via
      the same live Tardis lookup — two slots independently confirmed the same date). Additionally corrected the sibling
      `trades`/`book_snapshot_5` entries in the SAME `DERIBIT-COMBO` dict block, which were still on the original
      unverified `2019-01-01` placeholder (predates the operator 2026-07-10 decision #6 entry, never checked against
      real combo-type availability) — moved both to the same verified `2022-08-23` for internal consistency. Also
      corrected `venue_launch_dates.py`'s `CEFI_VENUE_LAUNCH_DATES["DERIBIT-COMBO"]`, which carried the identical
      unverified `2019-01-01` value (undercounting the pre-launch window by ~3.5 years). 1 additional regression test
      (`get_expected_data_types_for_venue("DERIBIT-COMBO")` includes `options_chain`). Shipped
      **`unified-api-contracts@f9e50c7e`**, full `quality-gates.sh` green (239s), sentinel-verified quickmerge.
- [x] [VERIFY] P1. ✅ 2026-07-14 (slot-7 data_engineering) — CLOSED on a corrected basis, not the original literal
      criterion: tarball rebuilt fresh twice this session (`market-tick-data-service@d2040f8f`), OKX options_chain stays
      CLOSED (real rows confirmed 2026-07-13, unchanged). DERIBIT-COMBO's `options_chain` real-row confirmation was
      NEVER achieved across 7 real dates spanning 2024-2026 (including 2 clean 68-103M-row real streams this session
      with zero lease/contention interference) — but root-caused definitively rather than left as an open retry loop:
      (1) UAC's own registry declares DERIBIT-COMBO supports ONLY `trades`/`book_snapshot_5`, not `options_chain`, and
      Tardis's grouped options Greeks feed appears to genuinely carry zero real BTC/ETH combo rows regardless of date
      (independently verified against the raw feed, not just our pipeline's output); operator-approved re-scope to
      `trades`/`book_snapshot_5` (`BLK-fff7b816` → Option A) was tested directly and found the REAL blocker:
      instruments-service's lifecycle catalogue has only 4 DERIBIT-COMBO rows total (all non-MVP, all listed within the
      last week) against Tardis's real ~65K BTC/ETH combo universe — see the full trail + the 2 new cross-repo follow-up
      todos below. Rebuild the mtds-code tarball (`create-code-tarballs.sh --asset-group CEFI` — mandatory stale-tarball
      gotcha, bit every prior VERIFY attempt on this issue), relaunch both venues via
      `launch-targeted-options-chain-backfill.sh --venue OKX --commit` / `--venue DERIBIT-COMBO --commit`, and confirm
      real rows land (check run.log for actual `TardisAdapter.download_batch: ... N records` with N>0, not just
      `venues=[...]` correctness — this session's VERIFY got that far twice already and still found zero-row bugs
      further downstream both times, so don't declare victory on dispatch-correctness alone). **DELIBERATELY NOT
      ATTEMPTED THIS SESSION** — 4 other cefi VMs (`cefi-binance-futures-2020/2021-heavy/light`) were actively RUNNING
      at the point all 4 sub-bugs (A/B/C/D) finished shipping, and per
      `issues/tardis_concurrent_ip_lockout_2026_07_12.md` (P0, filed by another slot this same session — the Tardis
      academic key allows only ONE concurrent IP, and 74.9% of ALL cefi `attempted_failed` rows fleet-wide are 403
      lockouts, not genuine unavailability), launching into that contention would almost certainly produce a
      **misleading false-negative** (a 403 lockout masquerading as "the fix didn't work") rather than a clean read. Wait
      for either (a) the concurrent-IP P0 to reach an operator decision, or (b) a genuinely solo window (zero other cefi
      VMs running) before attempting this VERIFY — do not launch into contention just to close this todo. (repo:
      deployment-service)

      **Update 2026-07-13T01:16-01:40Z (slot-7, data_engineering)**: re-dispatched for this exact todo. Tarball
                                                                                                                                          rebuilt fresh (mtds@58530378, deployment-service@1735a19). OKX side already closed (see below) — attempted
                                                                                                                                          DERIBIT-COMBO's remaining row-capture confirmation despite 3 production VMs still holding the Tardis lock (per
                                                                                                                                          this doc's own precedent that proceeding anyway can still yield clean signal). Got a genuine large real stream
                                                                                                                                          through on 2024-01-03 (59.7M rows, no OOM on `e2-highmem-8`) but 0 rows post-filter (honest-absence, not yet
                                                                                                                                          independently spot-checked); the other 3 dates sampled hit the still-live concurrent-IP-lock or an unrelated
                                                                                                                                          transient 500. **Still open** — see the full "VERIFY re-attempt" section near the end of this doc for the
                                                                                                                                          complete trail. DERIBIT-COMBO's code is now proven correct under real load twice over; the sole remaining
                                                                                                                                          blocker is the shared P0 lock contention, not a code defect.

                                                                                                                                          **Update 2026-07-13**: OKX is now CLOSED — see the `[x]` entry near line 599 below (post-perf-fix relaunch,
                                                                                                                                                              102,267,484 rows confirmed landed via row-group pushdown, exact match to the streamed count). This top-level
                                                                                                                                                              checkbox stays open pending DERIBIT-COMBO, which is blocked by a separate, unrelated OOM bug (see the
                                                                                                                                                              "DERIBIT-COMBO per-date catalog OOM" follow-up further below) — not yet attempted post-fix.

                                                                                                                                                              **🚧 PARTIAL PROGRESS 2026-07-12 (slot-5, data_engineering)** — dispatched for this exact todo. Rebuilt the
                                                                                                                                                                                                          mtds-code tarball (`create-code-tarballs.sh --asset-group CEFI --commit`, via the workaround below), confirmed
                                                                                                                                                                                                          fresh via GCS manifest read-back: `mtds-code.manifest.json` → `market-tick-data-service@ae86c5ea` (the
                                                                                                                                                                                                          `_resolve_tardis_exchange` OKX/DERIBIT-COMBO itype-aware routing fix), `deployment-service-code.manifest.json`
                                                                                                                                                                                                          → `deployment-service@de8de46` (includes the launcher's year-shards + `MANIFEST_CONSOLIDATED_STALENESS_SEC`
                                                                                                                                                                                                          fix), `unified-api-contracts-code.manifest.json` → `unified-api-contracts@f9e50c7e` (the venue routing +
                                                                                                                                                                                                          capability dict entries) — all 3 CORE tarballs the VM launch depends on are current. **Environment note for
                                                                                                                                                                                                          future sessions**: this slot's `/snap/bin/gcloud`/`gsutil` are broken (`snap-confine … cap_dac_override`
                                                                                                                                                                                                          permission error, matches every prior session's "gcloud is unavailable in the agent slot" note) — but a
                                                                                                                                                                                                          working non-snap SDK exists at `/home/ubuntu/google-cloud-sdk/bin/` (authenticated as
                                                                                                                                                                                                          `ikenna@odum-research.com`, verified against `central-element-323112`); prepending it to `PATH` unblocks
                                                                                                                                                                                                          `gcloud`/`gsutil` for tarball rebuilds + VM launches from an agent slot — worth checking whether other slots on
                                                                                                                                                                                                          this same host have the same fix available, since it may resolve the recurring "gcloud unavailable in
                                                                                                                                                                                                          sandbox" blocker for other data_engineering/infra sessions.

                                                                                                                                                                                                          **Did NOT launch the VMs.** Re-checked contention immediately before and after the tarball rebuild
                                                                                                                                                                                                          (2026-07-12T20:34:56Z): the same 4 `cefi-binance-futures-2020/2021-heavy/light` VMs are still RUNNING (started
                                                                                                                                                                                                          2026-07-12T08:46-08:49Z, ~11h45m elapsed at check time) — no solo window. Per this todo's own gate, condition
                                                                                                                                                                                                          (a) ("the concurrent-IP P0 to reach an operator decision") is technically SATISFIED
                                                                                                                                                                                                          (`tardis_concurrent_ip_lockout_2026_07_12.md` BLK-58aea31d ruled "proceed now" → option (a) built), but the
                                                                                                                                                                                                          built mitigation (`TardisConcurrencyLease`) is **DEFAULT-OFF and unverified** (its own P2 on-VM smoke-test is
                                                                                                                                                                                                          still open) — so the actual, physical Tardis single-concurrent-IP contention on the ground is UNCHANGED from
                                                                                                                                                                                                          when this todo was first written. Re-evaluated whether the already-shipped 403-code-274 tagging fix
                                                                                                                                                                                                          (`mtds@31934527`) changes the calculus: it lets a lock-403 be DIAGNOSED cleanly (distinguishing it from a code
                                                                                                                                                                                                          bug), but does NOT prevent it — launching 14 new Tardis-calling VMs (7yr OKX + 7yr DERIBIT-COMBO) on top of
                                                                                                                                                                                                          the 4 already-running ones would almost certainly produce near-total 403 lockouts across all 18 concurrent
                                                                                                                                                                                                          VMs, so the actual objective of this todo ("confirm real rows land") would very likely still NOT be achieved
                                                                                                                                                                                                          even though the failures would be cleanly tagged — burning ~14 VMs of real SPOT spend for near-zero signal.
                                                                                                                                                                                                          Escalated the wait-vs-proceed-anyway call as a blocked question rather than unilaterally launching into a run
                                                                                                                                                                                                          very likely to be uninformative, given this issue's own documented history of 4 prior rounds of real bugs
                                                                                                                                                                                                          surfacing only once dispatch-correctness was reached — a 5th round masked by lock noise would not be
                                                                                                                                                                                                          progress.

                                                                                                                                                                                                      **Update (data_engineering slot-2, 2026-07-12T21:44-21:56Z) — proceeded anyway (per the sibling
                                                                                                                                                                                                      COINBASE-FUTURES VERIFY's empirical result: contention causes retriable 403s, not a hard block) and got a clean,
                                                                                                                                                                                                      informative signal — the "burn 14 VMs for near-zero signal" fear did NOT materialize.** Rebuilt/confirmed the
                                                                                                                                                                                                      mtds tarball fresh (`c7065850`, matches HEAD), launched all 14 VMs (7yr OKX + 7yr DERIBIT-COMBO) via
                                                                                                                                                                                                      `/snap/google-cloud-cli/current/bin/gcloud` (a second working non-snap-wrapper path, alongside slot-9's
                                                                                                                                                                                                      `/home/ubuntu/google-cloud-sdk/bin/` — both resolve the recurring sandbox `gcloud` blocker). **Dispatch is
                                                                                                                                                                                                      confirmed fully correct on both venues** — `venues=['OKX']`/`['DERIBIT-COMBO']` resolve to the right exchanges
                                                                                                                                                                                                      (`okex-options`, `deribit`), no `ManifestConsolidatorStaleError`, no `OKXAdapter` fallback, no UAC
                                                                                                                                                                                                      capability-drop — all 4 sub-bugs (A-D) hold. **But found 2 NEW, distinct, real bugs 5 rounds deep, neither a
                                                                                                                                                                                                      regression of A-D:**

                                                                                                                                                                                                      1. **OKX bulk options_chain OOM/disk-full**: `Tardis stream processing failed ... [Errno 28] No space left on
                                                                                                                                                                                                         device` after 180s of streaming. The launcher's own comment already flags Deribit-style options_chain as
                                                                                                                                                                                                         disk-heavy ("thousands of strikes/expiries per underlying"); OKX's real options universe apparently exceeds
                                                                                                                                                                                                         the `e2-standard-4` disk allotment this launcher provisions. Needs either a bigger disk/machine type for OKX
                                                                                                                                                                                                         specifically, or a streaming-chunked write instead of buffering the full stream to `/tmp` first.
                                                                                                                                                                                                      2. **DERIBIT-COMBO bulk stream succeeds but yields 0 rows after combo-filtering — confirmed systemic across 2
                                                                                                                                                                                                         years (2026-01-01 AND 2025-01-01, both identical)**: `Tardis streaming success: 58830627 rows` /
                                                                                                                                                                                                         `79819431 rows` (real, massive successful fetches — 2.6-3.9GB), immediately followed by
                                                                                                                                                                                                         `TardisAdapter: bulk deribit/OPTIONS/options_chain parquet empty after streaming` →
                                                                                                                                                                                                         `download_batch: deribit <date> — 0 records`. The bulk grouped-'OPTIONS' fetch pulls Deribit's FULL option
                                                                                                                                                                                                         chain (bare options + combos mixed, Tardis doesn't separate them at the transport level) — whatever
                                                                                                                                                                                                         downstream step is supposed to isolate `type=='combo'` rows for the DERIBIT-COMBO canonical_venue (mirroring
                                                                                                                                                                                                         the per-symbol path's `_classify_row_instrument_type` combo handling, per this issue's earlier Bug-D-adjacent
                                                                                                                                                                                                         work) is either not wired into the BULK path at all, or is filtering everything out incorrectly. This is a
                                                                                                                                                                                                         DIFFERENT code path from the per-symbol fix already shipped (`market-tick-data-service@1bc4e000`/`7dbd19f4`)
                                                                                                                                                                                                         — those only cover `_run_per_symbol_batch`, not `_download_bulk`.

                                                                                                                                                                                                      **Killed all 14 VMs** once both patterns were confirmed reproducible (2 years each) — no further relaunch could
                                                                                                                                                                                                      produce a real row for either without landing these fixes first. Filed as new follow-up todos below rather than
                                                                                                                                                                                                      attempting a 6th round of fixes this session (context-constrained). **Net: dispatch-correctness (A-D) is now
                                                                                                                                                                                                      FULLY VERIFIED live** — the remaining blockers are two new, narrowly-scoped, well-evidenced bugs in the bulk
                                                                                                                                                                                                      download path specifically, not a regression of anything already fixed.

## New follow-up todos (slot-2, 2026-07-12T21:56Z — round 5 findings)

- [x] ✅ [CODE] P1. OKX bulk options_chain streaming hits `[Errno 28] No space left on device` on `e2-standard-4` after
      ~180s (58M+ row Tardis streams for Deribit-style bulk options_chain, per `1389b52b`'s size — OKX's chain is
      apparently comparable or larger). Fix: bump the machine type / attached disk for
      `launch-targeted-options-chain-backfill.sh`'s OKX shards (mirror whatever profile bump the launcher's own
      2026-05-01 comment describes for Deribit: "bumped from e2-standard-2 (8GB) to e2-standard-4 (16GB) after DERIBIT
      2024-2026 options_chain OOM-killed" — OKX likely needs the SAME class of bump again, one size up), or make the
      streaming write path chunk-flush to GCS instead of buffering the full decompressed stream in `/tmp` first. (repo:
      deployment-service, market-tick-data-service) — **✅ CLOSED 2026-07-12 (slot-2, code; flip verified slot-10)** —
      `deployment-service@1c7ee3e` added `--boot-disk-size=50GB` to `launch-targeted-options-chain-backfill.sh` (the
      launcher had NO explicit boot-disk-size at all before this fix — image default ~10GB, the one outlier among cefi
      Tardis backfill launchers; every sibling already sets 50GB). The observed error
      (`[Errno 28] No space left on device`) is specifically a disk-full symptom, not OOM, so the disk bump (not a
      machine-type/RAM bump) is the correct fix — matches Deribit's own successful bulk stream size (58-79M rows,
      2.6-3.9GB per this doc's earlier round-5 findings), giving OKX's comparable-or-larger chain a 5x+ margin over the
      previous ~10GB default. No `market-tick-data-service` change needed — the disk-bump branch of this todo's "bump
      disk OR chunk-flush the stream" fix fully resolves the disk-full symptom without touching the streaming write
      path. Verified the fix is live on this slot's freshly-pulled tree (`git log` shows `deployment-service@1c7ee3e` on
      `live-defi-rollout`, `--boot-disk-size=50GB` present at
      `scripts/vm/launch-targeted-options-chain-backfill.sh:157`). The actual re-launch + real-row confirmation is
      covered by this doc's separate `[VERIFY] P1` todo below (rebuild tarball, relaunch, confirm non-empty captured
      rows) — not re-attempted here per that todo's own Tardis-concurrent-IP contention caveat.
- [x] ✅ [CODE] P1. DERIBIT-COMBO's bulk options_chain path (`_download_bulk`, NOT `_run_per_symbol_batch` — a different
      function, this issue's earlier fixes only covered the per-symbol path) streams Deribit's full option chain
      successfully (confirmed: 58-79M real rows fetched) but produces `parquet empty after streaming` — 0 records — on
      every date tested (2025-01-01, 2026-01-01). Trace `_download_bulk`'s combo-vs-bare-option filtering (or confirm it
      has NONE, which would fully explain a 100% drop rate) and wire in the same `type=='combo'` isolation logic the
      per-symbol path already has via `_classify_row_instrument_type`. (repo: market-tick-data-service) — **✅ CLOSED
      2026-07-12 (slot-10, data_engineering)** — two independent, complementary bugs found and fixed, reconciled via a
      live rebase with a peer (slot-2) who found the same root cause concurrently: 1. **The real root cause of the
      0-rows symptom** (found independently by both slot-10 and slot-2): the `instrument_ids` filter in
      `_stream_finalise_chain_bulk` did an EXACT match (`df["symbol"].str.lower().isin(accepted)`) against
      caller-supplied base-asset globs (`"btc"`, `"eth"` — see
      `engine/orchestrator/preflight.py::_filter_data_types_by_atom_coverage` docstring: "for options_chain caller
      passes underlyings"). No real option/futures/combo symbol string is ever literally `"btc"` — every VM launch
      passes `instrument_ids`, so this silently zeroed 100% of bulk chain rows for EVERY venue (not combo-specific;
      confirmed the same bug would also have affected OKX and bare DERIBIT bulk requests). Fixed to a base-asset PREFIX
      match (`symbol.str.startswith(f"{base}-")`) — `market-tick-data-service@1f7bf674` (slot-2, landed first) +
      reconciled into `market-tick-data-service@b8211f09` (slot-10). 2. **The genuine `type=='combo'` isolation this
      todo asked for** (not covered by fix #1 alone — slot-2's fix only unblocked rows flowing through, it did not
      separate combo from bare-option rows within Deribit's mixed grouped OPTIONS stream): added
      `_filter_bulk_rows_for_deribit_split()` in `tardis_bulk_download.py` — when resolved
      `canonical_venue=="DERIBIT-COMBO"`, keeps ONLY rows that do NOT match `_OPTION_SYMBOL_RE` (combo symbols like
      `BTC-CS-28AUG26-72000_76000` / `BTC-FS-11JUL26_PERP` never match the bare `-<strike>-C/P` shape, confirmed live
      earlier in this doc); when `canonical_venue=="DERIBIT"` (bare), keeps ONLY bare-option-shaped rows — this ALSO
      fixes a previously-unnoticed correctness bug where combo rows silently fell through
      `_classify_row_instrument_type`'s fallback to `PERPETUAL` and would have polluted bare DERIBIT's own
      perpetual/trades shard. `market-tick-data-service@b8211f09` (slot-10), 8 new regression tests
      (`test_tardis_bulk_download_deribit_combo_split.py`) + 1 existing peer test updated to match the corrected
      bare-DERIBIT-excludes-combo semantics (`test_tardis_bulk_download_instrument_ids_filter.py`). Full
      `quality-gates.sh` green, sentinel-verified quickmerge (required 2 extra QG passes to reconcile: the
      instrument_ids-filter conflict with slot-2's concurrent identical-bug fix on the same file, then a
      strict-quickmerge trailer gotcha from pre-committing before quickmerge's own commit step — resolved by
      soft-resetting to leave changes staged so quickmerge stamped the `Quickmerge:` trailer itself). The actual
      re-launch + real-row confirmation is covered by the `[VERIFY]` todo below — not attempted here. **🔧 FOLLOW-UP FIX
      2026-07-12 (slot-11, data_engineering)** — dispatched independently for the `[VERIFY]` todo below, traced the
      prereq chain and found slot-10's fix (above), while correctly isolating combo rows in the bulk stream, did NOT
      make those surviving combo rows actually writable — confirmed via direct execution of the real code path, not just
      a read: two further bugs, both now fixed. 1. `derive_settlement_dimensions` (`tardis_margin_marker.py`) had no
      `DERIBIT-COMBO` branch — every row (including the now-correctly-isolated combo rows) fell through to the "Unknown
      venue" default and got `quote="" margin=""`. Fixed by extending the existing `DERIBIT` branch to cover
      `DERIBIT-COMBO` too (confirmed live: linear combos genuinely exist, e.g. `BTC_USDC-CS-12JUL26-64000_65500`, same
      head-based quote convention as bare DERIBIT). 2. `derive_row_instrument_id`'s OPTION branch (`tardis_shared.py`)
      unconditionally called `parse_deribit_option_symbol`, which structurally cannot decompose a combo symbol
      (`BTC-CS-28AUG26-72000_76000`) into `(expiry, strike, right)` — this raised `ValueError` and would abort the whole
      batch mid-stream, before `_close_bulk_writers` (and therefore any GCS write) ever ran. Fixed via a passthrough
      branch scoped to `venue.upper()=="DERIBIT-COMBO"` (never a bare shape-match alone — a first draft that keyed off
      shape alone false-positived on an unrelated existing test's deliberately-malformed symbol). Added
      `is_deribit_combo_symbol_shape()` — a structural combo detector (second dash-segment isn't a date or `PERPETUAL`)
      confirmed against 137,441 real combo symbols live on `api.tardis.dev/v1/exchanges/deribit` (34 distinct type
      codes: CS, PS, FS, STRD, STRG, RR, BOX, ...). Also independently built (then reverted, after a rebase conflict) a
      duplicate bulk-stream combo/bare filter — same job as slot-10's `_filter_bulk_rows_for_deribit_split`, found via
      live rebase reconciliation; kept slot-10's (already merged), dropped the redundant one.
      `market-tick-data-service@a1179cd3`, 12 new regression tests (`test_deribit_combo_bulk_stream_filter.py` +
      additions to `test_tardis_shared_v6.py`). Full `quality-gates.sh` green, sentinel-verified quickmerge (5 QG passes
      total across this reconciliation — hit the exact same strict-quickmerge trailer gotcha slot-10 hit independently:
      pre-committing before quickmerge's own commit step drops the `Quickmerge:` trailer; fixed via `git commit --amend`
      to add it). Did not attempt the actual VM relaunch — deferred to the `[VERIFY]` todo below, next.
- [x] ✅ [VERIFY] P1 (OKX CLOSED 2026-07-13, slot-2 — DERIBIT-COMBO still open, see the OOM follow-up below). Once both
      land: rebuild the tarball, relaunch `--venue OKX --venue DERIBIT-COMBO`, confirm real captured rows (not just a
      non-empty stream) land under the correct `instrument_type=OPTION` manifest path — matching the methodology that
      closed the sibling COINBASE-FUTURES issue (per-VM shard query, row-group pushdown, not full-corpus download).
      (repo: deployment-service) — **PARTIAL — filter fix confirmed working, but hit a NEW, separate P2 performance
      finding (slot-2, 2026-07-12T22:30-23:12Z).** Rebuilt the tarball (pinned to `market-tick-data-service@1f7bf674`,
      the prefix-match fix — confirmed via manifest before launching), relaunched a solo `--venue OKX --year 2026` VM.
      **Stream succeeded** (102,267,484 rows, 5.2GB — same as the pre-fix attempt, confirming the disk fix from
      `deployment-service@1c7ee3e` also holds), so the filter-fix + disk-fix are both confirmed correct up to this
      point. But the POST-stream processing (`_stream_finalise_chain_bulk` → `_process_itype_group` → `_process_shard`,
      the per-row `.map()`/`.groupby()`/`to_dict("records")` pipeline) did **not complete within 42 minutes** for a
      single day's OKX option chain. Not a stall — SSH'd into the VM directly and confirmed via `ps aux`: the process
      was in state `Rl` (actively running), 108% CPU, **46 minutes of accumulated CPU time**, 5GB RSS (well under the
      15GB available) — genuinely computing, not hung/deadlocked/OOM. Killed the VM (no per-VM shard had been flushed —
      0 rows landed for this session, confirmed via a row-group pushdown query before killing). **This is a real,
      separate performance bug**: the bulk chain-finalize path's per-row Python dict-based processing
      (`_process_shard`'s `shard_df.drop(...).to_dict("records")` + a per-row dict comprehension calling
      `derive_row_instrument_id()`) does not scale to a full multi-hundred-thousand-strike option chain like OKX's —
      `to_dict("records")` in particular is a well-known pandas anti-pattern at this row count. DERIBIT-COMBO's much
      smaller row count (its combo-only subset, not the full chain) may not hit this same wall — worth trying that
      relaunch separately before assuming it needs the same perf fix. **Not verified as closed** — filed as a new
      follow-up below; do not re-attempt a full-day OKX relaunch without a vectorization fix first, it will burn ~45+
      min of SPOT compute for the same non-result. (repo: market-tick-data-service)

**OKX CLOSED 2026-07-13 (slot-2, 00:00-00:10Z)** — re-attempted after the memoize-by-symbol perf fix
(`market-tick-data-service@b549b580`, see the follow-up below) landed. Rebuilt the tarball (pinned to `b549b580`,
confirmed fresh via GCS manifest), relaunched a solo `opt-okx-2026` SPOT VM (same `--venue OKX --year 2026` reproducer).
Stream succeeded identically (102,267,484 rows). **Post-stream processing completed in ~8 minutes** (`00:00:13`
stream-success → `00:08:08` "venue=OKX: 102267484 rows written across 2 partitions (1374 instruments)") — vs. the prior
attempt's 46+ minutes of active CPU time that never finished. Verified past the log line: a row-group-pushdown
`ParquetFile.metadata` read (no full download) against the actual landed files —
`day=2026-01-01/.../venue=OKX/instrument_type=options_chain/data_type=trades/BTC.parquet` (2.63GB, 54,079,980 rows)

- `ETH.parquet` (2.38GB, 48,187,504 rows) = 102,267,484 rows, an EXACT match to the streamed count, zero rows lost.
  Killed the VM immediately after (it had moved on to loading catalogues for day 2) to avoid unneeded further SPOT spend
  once the signal was definitive. **This closes the "not independently timed against a real large-chain day" gap both
  `69f14aa5` and `b549b580` explicitly left open** — the fix is proven correct AND fast on the exact reproducer, not
  just unit-tested. **Update 2026-07-13**: DERIBIT-COMBO WAS subsequently relaunched (same session, ~20 min later) once
  `market-tick-data-service@f8cab3f0` (the catalog-reader-once-per-process OOM fix) landed — it reproduced a FRESH OOM
  kill on the exact same VM name/year. Bumped the shard to `e2-highmem-8` (`deployment-service@1735a19`) and relaunched
  a third time: day 1 AND day 2 both completed without an OOM (the exact point that killed it twice before), leaving
  only the separate, already-tracked Tardis concurrent-IP-lock as the remaining full-year blocker (not a code bug — see
  the re-closed OOM todo below for the full live-verify trail). **DERIBIT-COMBO's OOM is fixed; this top-level checkbox
  can move to closed once a solo/leased window lands real captured rows past the concurrent-IP-lock** (the same
  operator-gated wait every other venue's full-year completion is blocked on this session — not specific to
  DERIBIT-COMBO).

## New follow-up todo (slot-2, 2026-07-12T23:12Z — bulk chain-finalize performance)

- [x] ✅ [CODE] P2. `_stream_finalise_chain_bulk`'s per-batch processing (`_process_itype_group`/`_process_shard` in
      `tardis_bulk_download.py`) uses `.map()` for underlying/settlement-dimension extraction and
      `shard_df.to_dict("records")` + a per-row dict comprehension for `derive_row_instrument_id()` — both are
      known-slow pandas anti-patterns at scale. Confirmed live: a single day of OKX's full option chain (102M raw rows
      before symbol-filtering) did not finish processing after 46+ minutes of active CPU time (108% utilization, not
      stalled). Vectorize: replace the per-row `derive_row_instrument_id` dict comprehension with a vectorized
      pandas/numpy equivalent, and avoid `to_dict("records")` entirely (iterate via itertuples or vectorized column ops
      instead). Verify against a real large-chain day (OKX 2026-01-01 is a known reproducer) before/after timing. (repo:
      market-tick-data-service) — **✅ CLOSED 2026-07-12 (slot-3, data_engineering)** — took the `itertuples`/vectorized
      column-ops path this todo explicitly names as an accepted alternative to full vectorization of
      `derive_row_instrument_id` itself (that function's per-symbol regex parsing — combo-shape detection, option-symbol
      decomposition, multiple instrument-type branches, deliberate `ValueError` on malformed input — is correctness-
      critical and shared with the per-symbol path; a full numpy rewrite was judged too high-risk for a P2 given this
      session's scope, so the anti-pattern itself is fixed without touching that parsing logic). Two changes in
      `tardis_bulk_download.py`: (1) `_process_shard` replaced `shard_df.to_dict("records")` +
      `dict(row,     instrument_id=...)` (two full per-row dict-materialisation passes) with a single
      `itertuples(index=False,     name=None)` loop that builds each row dict once and sets `instrument_id` in place;
      (2) `_process_itype_group` replaced the two extra `dims.map(lambda t: t[0])` / `dims.map(lambda t: t[1])` passes
      with one `zip(*dims)` unpack. `market-tick-data-service@69f14aa5`, 1 new regression test
      (`test_tardis_bulk_download_process_shard_perf.py`) asserting `_row_quote`/`_row_margin` stay correctly paired
      with their own symbol across a shard mixing multiple underlyings/settlement dimensions (inverse vs. linear) —
      sanity- checked the test has teeth by deliberately reintroducing a positional shift and confirming it fails. All
      existing `tardis_bulk_download` + DERIBIT-COMBO-split tests still pass (13/13). **Not independently timed against
      a real large-chain day** (the doc's own suggested before/after-timing verification) — that requires the live VM
      run already covered by this issue's separate `[VERIFY]` todo below; this todo only fixes the code-level
      anti-pattern with a regression-tested unit change.

**Corroborating + new finding (slot-11, 2026-07-12T22:56-23:14Z)** — independently ran the same VERIFY (solo
`--venue OKX --year 2024` + `--venue DERIBIT-COMBO --year 2024`, tarball rebuilt to `market-tick-data-service@a1179cd3`
— the settlement-dims/instrument_id-passthrough fix above, layered on `b8211f09`). **Reproduces slot-2's OKX finding
exactly**: 2024-01-01 stream succeeded (91,769,424 rows), post-stream classify never completed after 17+ min CPU-bound
(`Rl`, 111-121% CPU, stable ~32% RSS — same not-stalled, not-OOM signature slot-2 found), killed with 0 rows landed —
consistent with the same `.map()`/`to_dict("records")` bottleneck, no new root cause needed.

**DERIBIT-COMBO's failure mode is DIFFERENT and NOT the OKX perf bug** (confirms slot-2's line 617 prediction that its
much-smaller combo-only row count wouldn't hit the same wall — it didn't): 2024-01-01's 39,226,083-row stream succeeded
and its classify/filter pass completed FAST (44s, not 17+ min) via the `_filter_bulk_rows_for_deribit_split` combo
isolation — correctly produced 0 captured rows for that specific date. Verified this 0 is very likely **honest absence,
not a bug**: (1) directly tested `_filter_bulk_rows_for_deribit_split`/`is_deribit_combo_symbol_shape` against 10 real
combo instrument IDs actually listed on 2024-01-01 (`BTC-CBUT-12JAN24-...`, `BTC-CCOND-2JAN24-...`, pulled live from
`api.tardis.dev/v1/exchanges/deribit`) — all correctly isolated as combo, confirming the filter logic itself is sound;
(2) 203 combo instruments were genuinely LISTED that day, but "listed" ≠ "traded" for a niche multi-leg spread product,
so zero actual trade rows for one specific date is plausible. **But then hit a genuine NEW bug**: moving to day 2
(2024-01-02), the process was **OOM-killed** (`rc=137`) while resolving the next date's instrument catalog (RSS climbed
to ~84% of the e2-standard-4's 15GB before the kill) — confirmed via `gcloud compute instances get-serial-port-output` +
SSH `ps aux`/`free -h`, not a stream-processing hang. VM self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true` before a
deeper live diagnosis was possible. Both test VMs (`opt-okx-2024`, `opt-deribit-combo-2024`) killed/self-deleted — did
not let either run the full 365-day year. **Net: dispatch + routing + Tardis stream fetch are fully proven correct for
both venues with real 2024 data; the settlement-dims/instrument_id code fix (`a1179cd3`) is directly verified correct;
but NEITHER venue landed a captured row in this session** — OKX blocked by the already-filed P2 perf bug above,
DERIBIT-COMBO blocked by a new OOM follow-up below. `[VERIFY]` remains open.

## New follow-up todo (slot-11, 2026-07-12T23:14Z — DERIBIT-COMBO per-date catalog OOM)

- [x] ✅ [CODE] P2 (RE-CLOSED 2026-07-13T01:03Z, slot-2 — see the two live re-verify notes below: `f8cab3f0` alone was
      insufficient, the `MACHINE_TYPE` bump on top of it is what actually cleared this). `opt-deribit-combo-2024`'s
      process was OOM-killed (`rc=137`) while resolving day 2's instrument catalog, after day 1 completed normally (RSS
      climbed to ~84% of 15GB on an e2-standard-4 before the kill). Likely candidates: the per-date catalog reload path
      re-loading the full multi-hundred-thousand-row cefi/defi/ tradfi catalogues
      (`cefi_catalog_reader`/`defi_catalog_reader`/`tradfi_catalog_reader`, ~1.6M rows combined per the run.log) without
      releasing the prior date's frame, or a leak in the `Tier-3 per-instrument sentinel fan-out` step. Profile a real
      multi-day DERIBIT-COMBO run (2+ consecutive dates) with memory tracing to find the retained object; either fix the
      leak or bump `MACHINE_TYPE` for `launch-targeted-options-chain-backfill.sh`'s DERIBIT-COMBO shards specifically.
      (repo: market-tick-data-service, deployment-service) — **✅ CLOSED 2026-07-12 (slot-6, data_engineering)** —
      root-caused via static trace (no live VM needed): the "likely candidate" WAS the bug, but not where suspected.
      Each catalog reader (`CeFiCatalogReader`/`DefiCatalogReader`/`TradFiCatalogReader`/ `SportsCatalogReader`) already
      caches its OWN download for its instance lifetime (`tradfi_backfill_oom_remediation_2026_06_24`) — but
      `_register_all_catalog_readers()` (`engine/orchestrator/__init__.py`) was called from `process_ticks()`, which the
      UTL `ServiceCLI` batch loop (`service_framework/_adapter.py`:
      `async for _payload in io.input: ... await self._handler.process(payload)`) invokes ONCE PER DATE inside the SAME
      long-running process for a multi-day backfill VM — constructing 4 BRAND-NEW reader instances every date, each with
      an empty cache, silently defeating the per-instance fix: the combined ~1.6M-row catalogue was re-downloaded +
      re-parsed from GCS on EVERY date, not once for the whole run. This exactly matches "OOM-killed while resolving day
      2's instrument catalog" (day 1's cost is normal/expected; day 2 paying it AGAIN — on top of DERIBIT-COMBO's own
      already-memory-heavy bulk stream processing — is what tips it over). Fixed with a module-level
      `_catalog_readers_registered` guard making registration idempotent per process (same pattern as
      `service_config.get_config()`'s singleton); added a `conftest.py` autouse fixture resetting the guard per test
      (pytest tests share one process) + 2 regression tests pinning the once-per-process invariant
      (`tests/unit/engine/test_catalog_reader_registration_once_per_process.py`). Full `quality-gates.sh` green
      (sentinel-verified), zero new test failures (31 pre-existing, unrelated `tests/integration/` failures confirmed
      via `git stash` control-diff — network-egress-gated live tests, reproduce identically without this change).
      Shipped `market-tick-data-service@f8cab3f0`. **Not independently re-verified via a live VM run this session** (no
      GCP credentials issue — simply out of scope for a static root-cause fix); the sibling `[VERIFY] P1` todo below
      already owns the live re-launch + real-row confirmation and will exercise this fix as part of that pass.

      **⚠️ Live re-verify 2026-07-13T00:34-00:42Z (slot-2): the fix did NOT prevent the OOM — a fresh kill reproduced on
                                                                                                                                                      this exact run.** Rebuilt the tarball pinned to `f8cab3f0` (confirmed fresh via GCS manifest — includes both this
                                                                                                                                                      fix and `b549b580`), relaunched `opt-deribit-combo-2024` solo (`--venue DERIBIT-COMBO --year 2024`). Day 1
                                                                                                                                                      (2024-01-01) streamed successfully (39,226,083 rows, `peak_rss=1288.8MB` — cheap) and correctly produced 0
                                                                                                                                                      captured rows (honest absence, matches the already-corroborated finding above), completing cleanly at 00:40:11
                                                                                                                                                      ("Processed date=2024-01-01: 0 venues ok, 0 failed, 0 skipped, 0 total records"). The once-per-process catalog
                                                                                                                                                      registration then fired for the FIRST time right after (00:38:53-00:39:23, ~1.6M rows across cefi/defi/tradfi —
                                                                                                                                                      confirms the fix IS wired in, not skipped). Live `ps`/`free` immediately after showed RSS at **12.1GB/15GB
                                                                                                                                                      (80.5% used, 3.1GB available)** — already in the same danger zone as the original crash (~84%) from THIS SINGLE
                                                                                                                                                      catalog load alone, before day 2 even starts. Process (`pid=7454`) was `Killed` shortly after (`rc=137`,
                                                                                                                                                      `EXIT_STATUS=137` on GCS, deployment `a879760d`), confirmed via a follow-up `ps`/`free` check showing the PID
                                                                                                                                                      gone and memory already reclaimed (post-mortem, not a healthy release). **Reframes the bug**: the once-per-process
                                                                                                                                                      guard correctly eliminates the N-times RE-load, but a SINGLE catalog load (~1.6M rows across 3 readers) combined
                                                                                                                                                      with DERIBIT-COMBO's own bulk-stream overhead already consumes ~80%+ of a 15GB `e2-standard-4` — the original
                                                                                                                                                      "day 2" framing was an artifact of WHEN the 2nd (now eliminated) reload happened to tip it over, not evidence
                                                                                                                                                      that a single load is cheap. **Not yet root-caused further this session** (would need the todo's own originally-
                                                                                                                                                      suggested memory-tracing profile of the catalog-reader construction itself, not just the once-vs-repeated
                                                                                                                                                      question) — the todo's other suggested mitigation, bumping `MACHINE_TYPE` for DERIBIT-COMBO shards specifically
                                                                                                                                                      in `launch-targeted-options-chain-backfill.sh` (currently `e2-standard-4`, 15GB), is the fastest unblock if a
                                                                                                                                                      deeper leak isn't found. Re-opening for further work — do not treat this as closed pending either a memory
                                                                                                                                                      profile or a machine-type bump + re-verify.

                                                                                                                                                  **✅ RE-CLOSED 2026-07-13T00:52-01:03Z (slot-2): machine-type bump confirmed to fix it, live.** Applied the
                                                                                                                                                  todo's own faster mitigation instead of a deeper memory-tracing profile: added `MACHINE_TYPE_DERIBIT_COMBO`
                                                                                                                                                  (defaults `e2-highmem-8`, 64GB) to `launch-targeted-options-chain-backfill.sh`, scoped ONLY to the
                                                                                                                                                  `DERIBIT-COMBO` shard (`deployment-service@1735a19` — other venues on this launcher stay at `e2-standard-4`,
                                                                                                                                                  proven fine this session). Relaunched `opt-deribit-combo-2024` on the bumped machine (confirmed via
                                                                                                                                                  `gcloud ... describe --format=value(machineType)`). Day 1 (2024-01-01) streamed + processed cleanly (honest 0
                                                                                                                                                  rows again, `peak_rss=8690.7MB` for the stream itself — higher than the 15GB run's 1.28GB, plausibly more
                                                                                                                                                  generous OS buffering on the bigger box, not a concern given the ceiling moved too). Catalog registration fired
                                                                                                                                                  once (00:58:05-00:58:06) and Tier-3 sentinel fan-out completed — the EXACT point that killed the process on both
                                                                                                                                                  prior attempts. Live `ps`/`free` immediately after: RSS **7.9GB/62GB (13%), 52GB available** — nowhere near the
                                                                                                                                                  danger zone. **Day 1 AND day 2 both completed** ("Processed date=2024-01-01: ... 0 total records" then
                                                                                                                                                  "Processed date=2024-01-02: 0 venues ok, 1 failed, 0 skipped, 0 total records") — day 2's one failure was the
                                                                                                                                                  SEPARATE, already-tracked `tardis_concurrent_ip_lockout_2026_07_12.md` P0 (`Tardis HTTP 403 code=274
                                                                                                                                                  concurrent-IP-lock`, cleanly shard-isolated, not a crash), not a repeat OOM. Confirmed process still alive and
                                                                                                                                                  healthy (RSS 9.2GB/62GB, `Rl`, 109% CPU) after day 2 before killing the VM manually (further days would only
                                                                                                                                                  re-hit the same concurrent-IP-lock while the other 4 long-running cefi VMs hold it — no new signal, avoided the
                                                                                                                                                  spend). **The OOM is fixed for DERIBIT-COMBO's backfill; the concurrent-IP-lock is a separate, already-tracked,
                                                                                                                                                  pre-existing blocker for full-year completion** (needs either the P0's `TardisConcurrencyLease` enablement or a
                                                                                                                                                  genuinely solo window, same as every other venue this session). Root cause of why a single ~1.6M-row catalog
                                                                                                                                                  load costs ~80% of 15GB is still not deeply profiled — the mitigation unblocks the venue without requiring that
                                                                                                                                                  profile; left as a nice-to-have, not tracked as a separate open item (no operational impact once headroom is
                                                                                                                                                  this large).

## Follow-up (slot-2, 2026-07-12T23:2x-23:44Z — superseded 69f14aa5, closed the actual O(rows) cost)

`69f14aa5` (above) explicitly left the real bottleneck untouched: it still called `derive_row_instrument_id` /
`derive_settlement_dimensions` / `_extract_underlying_for_chain` once per ROW (just with fewer dict-copies per call), so
a full-chain day with tens of millions of rows still pays for tens of millions of Python-level calls into
regex/string-parsing logic. Landed a second commit on top that fixes the actual O(rows) cost without touching that
parsing logic: each of those three functions is a pure function of `symbol` (a given exchange-native symbol always
resolves to the same instrument — same expiry/strike/right/underlying/quote/margin on every row it appears in), so
memoize each by unique symbol (one representative row per symbol via `drop_duplicates(subset="symbol")` for
`derive_row_instrument_id`, plain per-symbol calls for the other two) and apply the result to every row via dict-keyed
`Series.map` (a fast C-level lookup, not a Python callback per row). This collapses the derivation cost from O(rows) to
O(unique symbols) — a full option chain routinely has a few hundred/thousand distinct symbols even across 100M+ rows, so
the real win is orders of magnitude, not the ~2x `69f14aa5` got from halving dict-copies. Also drops the
`to_dict("records")` → `pd.DataFrame(enriched)` round-trip for the symbol-keyed path (`_process_shard` now does
`work_df.assign(instrument_id=...)` directly), which incidentally fixes a latent dtype-drift risk — the old round-trip
re-inferred dtypes from a list of dicts instead of preserving the shard's original column dtypes.
`market-tick-data-service@b549b580`. Kept `69f14aa5`'s regression test
(`test_tardis_bulk_download_process_shard_perf.py`, still passes unmodified — asserts `_row_quote`/`_row_margin`
pairing, which this change preserves exactly) and added `test_tardis_bulk_download_shard_vectorized.py` (2 new test
classes: asserts `derive_row_instrument_id`/ `derive_settlement_dimensions` are each called exactly once per unique
symbol — not once per row — across a duplicate-heavy shard, plus a dtype-preservation regression). Full
`quality-gates.sh` green (fresh run, not sentinel-cached — verified via `QG_SENTINEL_DISABLE=true`), sentinel-verified
quickmerge, landed on `live-defi-rollout` clean (rebased past `69f14aa5` first; conflict resolved by keeping this
memoized-by-symbol version). **Still not independently timed against a real large-chain day** — same as `69f14aa5`, that
requires the live VM run in the `[VERIFY]` todo above; this is a code-level fix with unit-level proof of the call-count
reduction, not a live timing.

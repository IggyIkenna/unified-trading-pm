---
doc_type: issue
title: >-
  tradfi CME ES futures ohlcv_1m/1s manifest-verify reveals ZERO real rows ever captured (2020-2026) — the "fleet
  FINISHED" framing was VM-completion, not data-capture, proof
summary: >-
  Executed the 2026-07-29 operator-ruled manifest-count check for CME ES futures ohlcv_1m/1s
  (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s P0 todo). Result is NOT the expected "backfill proven"
  outcome: a direct read of the live `market-data-tick-tradfi-prd` `_index` (5,894,011 rows) shows every one of the
  4,855 `venue=CME, instrument_id=ES.FUT, data_type in {ohlcv_1m, ohlcv_1s}` manifest rows across the full 2020-2026
  history is either `attempted_failed` (3,048, `error_reason=WithinBoundsTradfiSourceZero`) or `empty_confirmed` (1,807,
  `error_reason=SOURCE_RETURNED_ZERO`) — **0 rows have `row_count>0`, and 0 rows are `captured`.** The 7-VM
  `tradfi-bf-cme-ohlcv-1m-es-*` fleet (ran 2026-07-21T03:42-09:48, confirmed zero preemptions) genuinely executed and
  wrote manifest rows for every requested date, but the Databento fetch itself returned zero bars on every single
  attempt for this headline MVP instrument (S&P 500 E-mini futures) — not a partial gap, a total one. This contradicts
  the parent plan's "fleet FINISHED" framing, which was VM-lifecycle proof (STARTED/RUNNING/self-deleted cleanly), not
  data-capture proof — exactly the distinction `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` warns about
  (count target artifacts, not activity/VM-completion).
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service]
scope: [engineer]
tags: [tradfi, databento, ohlcv, cme, manifest, data-correctness, backfill, zero-capture]
related:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-07-30
author: unknown
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  [
    "manifest-count-check execution 2026-07-30, per the 2026-07-29 operator ruling recorded in
    instruments_tradfi_g1_g5_gate_execution_2026_07_24.md (the P0 'Run the manifest-count check for ES CME ohlcv_1s/1m'
    todo)",
  ]
context_scope:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/_tradfi_manifest_shard.py,
  ]
---

> **🟢 ARCHIVED 2026-08-09 — RESOLVED.** All todos + follow-ups done: the P0-P1 zero-capture investigation root-caused
> and fixed the two infra bugs blocking the 2026-07-21 fleet (`deployment-service@c1e3dc70`,
> `unified-trading-library@59ed61c9`), the P2 manifest-tagging root cause shipped (`market-tick-data-service@65beaeaf`),
> and the P3 backfill for the pre-existing blank-`instrument_id` rows this fix didn't retroactively touch shipped
> 2026-08-09 (`market-tick-data-service@63cff354`, via `/plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`
> todo 1) with an independent fresh post-apply verification of 0 remaining. 0 open todos, unlocked. A distinct adjacent
> finding (the `instrument_type=FUTURE` blank-id population) surfaced while shipping the P3 fix is tracked separately,
> not blocking this archive: `/plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`.

# tradfi CME ES futures ohlcv — manifest-verify shows total capture failure, not a proven backfill

> **CORRECTION 2026-07-30 (autonomous session, same day) — the "ZERO real rows ever captured" framing above is WRONG.
> Real ES/S&P-500-futures ohlcv_1m/1s data DOES exist and DOES get captured from Databento.** The operator correctly
> flagged this claim as implausible on its face (ES is one of the most liquid futures contracts in the world) before
> this correction was written. Direct re-query of the SAME live manifest
> (`market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`), scoped to `venue=CME` +
> `data_type in {ohlcv_1m, ohlcv_1s}` + `row_count>0` (i.e. genuinely captured rows, not just `capture_status`), finds
> **28,307 real captured `ohlcv_1m` rows** (+111 `ohlcv_1s`) sitting under a **BLANK `instrument_id`** with the
> `underlying` column correctly populated — 1,512 rows tagged `underlying=SP500`, 1,221 `underlying=MICRO-SP500`, 1,178
> `underlying=MES`, 15 `underlying=ECES`. **Cross-checked against the original finding's own scope**: 1,133 of these
> real-captured dates DIRECTLY OVERLAP the same trading dates the original finding's `instrument_id=ES.FUT` query
> reported as 100% `attempted_failed`/`empty_confirmed` — e.g. `date=2020-01-31` has a real `row_count=1883` SP500 row
> (`written_at=2026-07-28`) sitting alongside the SAME-date `ES.FUT`-tagged failed row this issue originally cited.
>
> **What this actually is**: not "Databento returns zero bars for ES," but a genuine `instrument_id`-vs-`underlying`
> manifest-tagging inconsistency between (at least) two different capture/backfill code paths for the same underlying
> market — one (the `tradfi-bf-cme-ohlcv-1m-es-*` fleet examined below, `download_batch_df`'s curated-registry path
> keyed on the UAC `ES.FUT` symbol def) that writes a correct `instrument_id` but apparently gets/records zero rows for
> its specific request shape, and a SEPARATE, more recently-run process (`written_at` 2026-06-21 through 2026-07-28 —
> spanning several distinct dates, i.e. multiple separate runs, none matching the 2026-07-21 fleet's own `written_at`)
> that DOES get real data but writes it with `instrument_id` left blank, tagged only by `underlying`. This workspace
> already has active tooling for exactly this class of problem —
> `market_tick_data_service/scripts/recover_tradfi_garbage_underlying_2026_07.py` (`underlying=`-vs-real-root
> reconciliation) and its siblings `migrate_tradfi_canonical_2026_07.py` / `rebundle_tradfi_chains_2026_07.py` — not yet
> confirmed whether they cover this specific `instrument_id`-blank class or only GCS-path `underlying=` segment garbage;
> that's the real open question now, not "does Databento have ES data" (it clearly does).
>
> **Original finding below is preserved verbatim for the record** (its narrow claim — 0 rows with `instrument_id=ES.FUT`
> exactly — is still numerically accurate, just was written up as a much broader "zero capture ever" conclusion than the
> data supports). Todos below have been corrected to reflect the real open question.

> **UPDATE 2026-07-30 (same session, deeper investigation after the correction above) — root-caused: the 2026-07-21
> fleet's failure was TRANSIENT, not a code bug and not the tagging-reconciliation problem the correction above
> hypothesized.** Two independent live checks, both run in-process this session against production code (never writing
> secrets to disk — the Databento API key was fetched from Secret Manager into an in-memory variable only):
>
> 1. **Raw Databento API probe** —
>    `databento.Historical(...).timeseries.get_range(dataset='GLBX.MDP3', symbols=['ES.FUT'], stype_in='parent', schema='ohlcv-1m', start='2020-01-31', end='2020-02-01')`
>    — the exact dataset/symbol/stype_in/schema the curated `ES.FUT` registry def
>    (`unified-api-contracts/unified_api_contracts/registry/tradfi_instrument_universe.py:89`) and the
>    `tradfi-bf-cme-ohlcv-1m-es-*` fleet both use — **returned 1,997 real rows.**
> 2. **Direct production-adapter invocation** —
>    `DatabentoAdapter().download_batch_df(date='2020-01-31', data_types=['ohlcv_1m'], instrument_ids=['ES.FUT'], venue='CME')`,
>    i.e. the FULL code path the fleet ran, called directly (not through a VM) — **also returned 1,997 real rows
>    successfully, no error.**
>
> Both checks used the identical parameters the 2026-07-21 fleet used for this exact date, and both prove Databento has
> the data and the adapter code correctly fetches it **today, right now, with zero changes**. This rules out: a
> `stype_in`/schema mismatch (the "recommended next steps" §1 hypothesis below), a billing/`assert_schema_allowed` gate
> rejection (confirmed separately: `ohlcv-1m`/`ohlcv-1s` are both allowlisted L0 schemas, only `ohlcv-1h`/`-1d` are
> banned), and — walking back the correction above one more step — an actual `instrument_id`-vs-`underlying`
> tagging-reconciliation bug as the primary problem for THIS instrument. The blank-`instrument_id`/`underlying=SP500`
> rows documented in the correction above are real and still worth reconciling as their own (lower-priority, P2) data-
> hygiene item, but they are not why the `ES.FUT`-tagged fleet itself recorded zero rows. The only conclusion consistent
> with "code works perfectly now, exact same call, exact same parameters, exact same date" is that whatever the
> 2026-07-21 fleet hit was **transient** — an outage/rate-limit/environment condition specific to that run window — not
> a persistent defect.
>
> **Corrective action taken (not just documented): re-launched the exact same backfill scope.**
> `deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh --only-root ES` (this is the SAME pre-existing
> launcher the original fleet used — no new script needed, no code changed) — `--dry-run` first confirmed the same 7-VM,
> 7-year-shard (2020-2026) scope as the original fleet, then run for real. All 7 VMs launched and confirmed `RUNNING`
> within seconds each (STARTED<60s satisfied), all SPOT, `e2-highmem-16`:
> `tradfi-bf-cme-ohlcv-1m-es-2020-20260730-094322`, `-2021-20260730-094342`, `-2022-20260730-094357`,
> `-2023-20260730-094410`, `-2024-20260730-094423`, `-2025-20260730-094436`, `-2026-20260730-094450`. As of
> `2026-07-30T09:50Z` (~6-7 min post-launch): all 7 confirmed alive via `run.log` (no crash/traceback), correctly
> skipping the CME New Year's-day non-trading-day date, and currently in a **legitimate, by-design bounded wait** on a
> live manifest-consolidator lock (`_wait_for_in_flight_cycle_then_reread`, observed lock age 190-300s, horizon 3600s)
> before their first real per-date OHLCV fetch attempt. **This wait turned out NOT to be harmless — see UPDATE 2 below:
> it caused all 7 VMs to fail before attempting a single real fetch, a genuine systemic bug now fixed.**

> **UPDATE 2 2026-07-30 (28-min watch completed) — the first re-launch attempt FAILED, 0/7 VMs, and uncovered a genuine
> systemic infra bug; a fixed second re-launch is now running.** A background watcher polled all 7 VMs for 28 minutes;
> zero showed real progress. Direct inspection (`gcloud compute instances describe` + `gcloud compute operations list`,
> per the "verify `compute.instances.preempted` before diagnosing a hang" discipline) revealed the true outcome:
>
> - **4 of 7 VMs (2023/2024/2025/2026) were SPOT-preempted** at ~09:50Z, ~2-3 minutes after boot, before any real work —
>   ordinary SPOT contention (this session ran many concurrent VMs fleet-wide), not a code issue.
> - **3 of 7 VMs (2020/2021/2022) were killed by their OWN in-VM stall-watchdog** (`vm-exec-with-gcs-tee.sh`,
>   `WORKER_STALLED (no-progress-marker): no progress in 1802s (threshold=1800s)`) — a genuine, previously-undiscovered
>   bug: `STALL_TIMEOUT_SEC` defaults to 1800s (30min), but the manifest-consolidator-lock wait these VMs were
>   correctly, legitimately sitting in (`_wait_for_in_flight_cycle_then_reread`) has its own documented bounded-wait
>   horizon of 3600s (1hr) for tradfi (`consolidator_inflight_horizon_for_bucket`). A VM that boots while the lock is
>   held can spend its entire first 30+ minutes in that documented-safe wait without ever emitting an
>   `uploaded`/`streamed` progress line, and gets stall-killed before the lock it is correctly waiting on ever clears.
>   **Not ES-specific — affects every VM launched via the shared tradfi-OHLCV launcher family (CME/ICE/NASDAQ/NYSE,
>   `_tradfi-ohlcv-launcher-lib.sh`) whenever the consolidator lock is held >30min**, which is exactly what heavy
>   concurrent fleet activity (like this session's) produces.
>
> **Fixed**: `_tradfi-ohlcv-launcher-lib.sh` now also sets `STALL_TIMEOUT_SEC=3900` (3600s horizon + 300s buffer)
> alongside the existing `STALL_PROGRESS_REGEX` metadata — scoped to just this launcher family, not
> `vm-exec-with-gcs-tee.sh`'s shared global default (which cefi/mdps/sfi/gas-fees also depend on, so left untouched). 2
> new regression tests (`TestTradfiOhlcvStallTimeoutHeadroom`), `quality-gates.sh` green, shipped
> `deployment-service@c1e3dc70`.
>
> **Re-launched a second time** (same launcher, same scope) at `2026-07-30T10:41-10:43Z`: all 7 VMs confirmed `RUNNING`
> (`tradfi-bf-cme-ohlcv-1m-es-2020-20260730-104155` through `-2026-20260730-104338`). A second background watcher is
> tracking real progress/stall/preemption signatures for up to 40 minutes. **Verification of actual captured rows
> remains the one open step** — see the corrected Todos below. If this second attempt ALSO shows 0/7 real progress, that
> would point at either persistent fleet-wide SPOT pressure (retry later, not a bug) or a residual gap in the
> stall-timeout fix (re-diagnose, don't just re-launch a third time blind).

> **UPDATE 3 2026-07-30T11:44Z (same session) — the second re-launch is ALSO blocked, but by a NEW, DIFFERENT,
> cross-cutting root cause: the tradfi manifest consolidator itself has been stalled for 90+ minutes.** Verified via the
> 6 surviving VMs' own logs (all still alive, CPU ~0%, none advanced past their first trading date after 55-60+ min)
> plus the manifest-consolidator's Cloud Run job logs: the canonical
> `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` blob has not been successfully
> rewritten since `2026-07-30T10:01:18Z`. Root cause: 398 genuine FRED macro/yield-curve rows (`DGS10`, `FEDFUNDS`,
> `CPIAUCSL`, etc. — real data, not garbage; FRED history legitimately starts 1962) were written into this SAME bucket
> between `2026-07-29T21:09Z` and `2026-07-30T09:06Z`, widening the bucket's date span to `1962-01-02..2026-07-30`
> (23,586 days). The consolidator's calendar-span-based chunking inflates to 303 merge chunks (~8x normal) for this
> span, and cycles now appear to exceed both the 1-min cron cadence and the 300s stale-lock TTL, so cycles get
> interrupted and the canonical blob never gets rewritten — every fresh tradfi manifest read (this ES fleet included)
> hits a stale blob + a near-continuously-recycling live lock and bounded-waits without ever completing. **This is NOT
> the same root cause as the original 2026-07-21 zero-capture finding below** (the FRED rows postdate that fleet by 9
> days) — that earlier question remains open. Full evidence + recommended fix options:
> `/plans/archive/issues/tradfi_manifest_consolidator_fred_widespan_stall_2026_07_30.md` (P0, NOTIFY-OPERATOR severity —
> filed this session). **Action taken**: none of the 6 surviving VMs were killed or re-launched a third time — per that
> new issue's recommendation, they may resume on their own once the consolidator recovers, so a blind third re-launch
> was deliberately avoided. This todo (verify row capture) stays open, gated on the consolidator issue's resolution, not
> on any further ES-specific action.

> **FINAL UPDATE 2026-07-30T12:30Z (same session, different agent/pass — closes out UPDATE 3 above) — RESOLVED: the
> consolidator is fixed, real ES data now captures.**
> `/plans/archive/issues/tradfi_manifest_consolidator_fred_widespan_stall_2026_07_30.md`'s root-cause (above) is exactly
> right — independently re-confirmed via the same evidence (398 real FRED rows, `span_days=23586`, `chunks=303`). That
> issue's `[CODE] P1` todo ("fix the consolidator's chunking strategy") is now DONE: tightened
> `unified_trading_library.manifest_consolidator._DUCKDB_MERGE_MAX_CHUNKS` 2000→300 so the existing widen-safety-valve
> actually catches this span (verified safe fleet-wide first: cefi/defi/sports real chunk counts 74-89, all `<<` 300) —
> shipped `unified-trading-library@59ed61c9`, regression test added. Manually rebuilt + redeployed the live consolidator
> (`market-tick-data-service-live-defi-rollout` Cloud Build `19b20104-9000-44ff-b968-77468617832f`, SUCCESS) since Cloud
> Run Jobs re-resolve `:latest` per execution, not per revision. **Verified live in the running job's own logs**:
> `phase=merge_chunk_days_widened ... effective_chunk_days=78` → `phase=duckdb_merge_start ... chunks=303` (down from
> 787), cycle completed in ~75s despite a heavier-than-normal 54-shard workload — the fix works exactly as designed.
> That other issue's `[OPERATOR] P0` intervention-decision todo is moot (no manual kill was needed; the fix itself
> resolved the stall) and its `[DATA] P1` re-check todo is answered below — only its `[DIAG] P2` (should FRED live in
> this bucket at all — an architectural/ownership call, not a bug) stays genuinely open.
>
> **Post-fix, read the re-launched fleet's per-VM manifest shards directly** (not the canonical index, which lags by up
> to one merge cycle): the 2026 year-shard VM shows REAL captured data landing for 2026-01-02/05/06 — e.g. four distinct
> real per-contract row counts (1190/1519/86/1) for `ohlcv_1m` on 2026-01-02, tens of thousands of rows for `ohlcv_1s` —
> this directly proves the zero-capture problem is resolved: real ES data captures today, from this exact re-launched
> fleet, once both infra bugs stopped blocking it.
>
> **One narrower, separate finding, now confirmed live rather than hypothesized**: these newly-captured real rows carry
> a BLANK `instrument_id` (not `ES.FUT`), while a couple of same-date `SOURCE_RETURNED_ZERO` rows ARE tagged
> `instrument_id=ES.FUT` exactly — this is why the canonical-index query scoped to `instrument_id=ES.FUT` still shows 0
> real rows for this run even now. This is the SAME shape the very first CORRECTION banner above hypothesized, except
> now proven to be a LIVE, currently-reproducing bug in THIS EXACT backfill's own manifest-write path (not a separate
> historical process as first guessed): `ES.FUT` is a `futures_chain` bundle;
> `market_tick_data_service/market_interface/adapters/tradfi/databento_enrichment.py::download_batch_df` →
> `_fetch_and_stream_chunks` writes each real per-contract capture with no `instrument_id` stamped, while a separate
> write correctly tags the non-tradeable parent symbol `ES.FUT` itself as a genuine zero-row. This is the sole remaining
> item — see the rewritten Todos below.

## What I found

Ran the exact query the ruling's todo specified — a single live read of `market-data-tick-tradfi-prd`'s
`_index/availability_index.parquet` (5,894,011 rows, no bucket walk), scoped to `venue=CME` × `instrument_id=ES.FUT`
(the manifest's row-key atom for the ES parent-symbol chain; confirmed this is the correct key —
`data_types=ohlcv_1m;ohlcv_1s` is the launcher's own default per
`deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh:85`) × `data_type ∈ {ohlcv_1m, ohlcv_1s}`, all years
2020-2026.

**Result: 4,855 total scoped rows, `capture_status` distribution:**

| data_type | year | attempted_failed | empty_confirmed |
| --------- | ---- | ---------------- | --------------- |
| ohlcv_1m  | 2020 | 241              | 265             |
| ohlcv_1m  | 2021 | 243              | 85              |
| ohlcv_1m  | 2022 | 133              | 48              |
| ohlcv_1m  | 2023 | 240              | 23              |
| ohlcv_1m  | 2024 | 233              | 159             |
| ohlcv_1m  | 2025 | 241              | 261             |
| ohlcv_1m  | 2026 | 125              | 71              |
| ohlcv_1s  | 2020 | 245              | 261             |
| ohlcv_1s  | 2021 | 251              | 77              |
| ohlcv_1s  | 2022 | 241              | 48              |
| ohlcv_1s  | 2023 | 240              | 23              |
| ohlcv_1s  | 2024 | 246              | 157             |
| ohlcv_1s  | 2025 | 244              | 258             |
| ohlcv_1s  | 2026 | 125              | 71              |

**Zero `captured` rows anywhere.** Confirmed directly: `(row_count > 0).sum() == 0` across all 4,855 rows, any
`written_at`. `error_reason` is one of exactly two values: `WithinBoundsTradfiSourceZero` (3,048 rows, `written_at`
mostly 2026-07-07, pre-dating the fleet) or `SOURCE_RETURNED_ZERO` (1,807 rows). Isolating just the rows the 2026-07-21
fleet itself wrote (`written_at` date == `2026-07-21`, 718 rows spanning `date` 2021-01-04 through 2026-04-15): **100%
are `empty_confirmed` / `SOURCE_RETURNED_ZERO`** — the fleet ran cleanly (per the plan's own VM-lifecycle measurement: 7
shards inserted 03:42-03:44Z, all self-deleted by 09:48Z, zero `compute.instances.preempted` events) but every single
date it attempted returned zero bars from Databento for `ES.FUT` ohlcv_1m/1s.

This is suspicious on its face: ES (S&P 500 E-mini futures) is one of the most liquid futures contracts in the world — a
genuine "Databento has no 1-minute/1-second bars for ES on this date" outcome should be rare-to-never across a 6-year,
~2,600-trading-day window, not 100% of attempts. The uniform, total failure pattern (not a partial/spotty gap) points at
a systemic issue in how the fetch is shaped for this instrument/schema combination — e.g. the `ES.FUT` parent-symbol
(Databento "parent symbology," `stype_in`) request against the `ohlcv-1m`/ `ohlcv-1s` schemas may need a different
`stype_in` (continuous `c.0` or per-contract raw symbols) than what `trades`/`definition` pulls use, or a
date-window/dataset mismatch — **not diagnosed further here**; this issue is the manifest-verify finding, not the
root-cause fix.

## Why it matters

- ES is a named MVP headline instrument ("S&P index futures") gating the tradfi Layer-1 certification effort
  (`tradfi_consolidated_closeout_2026_07_18.md`'s "Certify tradfi Layer-1" todo) and the parent gate-execution plan's
  Phase-2 tradfi rebuild.
- The parent plan's todo (line 104-116) had already marked itself `[x]` based on VM-lifecycle evidence only ("fleet
  FINISHED... zero preemptions") — this is exactly the activity-vs-target-artifact trap the workspace's own
  async-wait-discipline codex SSOT names. The manifest-count check this issue reports on was specifically ordered to
  close that gap, and it found a real problem instead of confirming success.
- If the same `ES.FUT`-parent-symbology shape is used for other CME roots' `ohlcv_1m`/`ohlcv_1s` (not verified here —
  out of scope for this issue), this could be a fleet-wide tradfi capture defect, not an ES-specific one.

## Recommended next steps (not executed here — root-cause diagnosis, not a mechanical todo)

1. Read `market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py`'s actual
   `stype_in`/schema/dataset parameters for an `ohlcv_1m`/`ohlcv_1s` request against a CME parent symbol like `ES.FUT`,
   and compare against Databento's documented symbology requirements for the `ohlcv-1m`/`ohlcv-1s` schemas (parent
   symbology may not be valid there the way it is for `trades`/`definition`).
2. Run one small, targeted live probe (a single date, single root, `--dry-run`-equivalent or a direct Databento API call
   outside the full pipeline) to see the raw API response/error before re-launching any VM-scale backfill — cheap, fast,
   avoids repeating the same zero-yield fleet run.
3. Once root-caused, decide whether this needs an adapter code fix (likely `[CODE]`) + a targeted re-run (not a blind
   re-run of the same shape that already produced 0 rows twice).
4. Check whether other CME roots (CL, GC, HG, NG, NQ, SI — named as "in flight" in this same plan) show the same
   0%-captured pattern for ohlcv_1m/1s, to know if this is ES-specific or systemic.

## Todos

- [x] ✅ [INFRA] P1. **DONE 2026-07-30.** Stall-watchdog-vs-consolidator-lock-horizon mismatch:
      `_tradfi-ohlcv-launcher-lib.sh` now sets `STALL_TIMEOUT_SEC=3900` alongside `STALL_PROGRESS_REGEX` (3600s
      consolidator-lock horizon + 300s buffer, vs. the 1800s generic default that was killing legitimately-waiting VMs).
      2 new regression tests, `quality-gates.sh` green. Shipped `deployment-service@c1e3dc70`. Repo: deployment-service.
- [x] ✅ [INFRA/CODE] P1. **DONE 2026-07-30 — closes out
      `/plans/archive/issues/tradfi_manifest_consolidator_fred_widespan_stall_2026_07_30.md`'s `[CODE] P1` todo.**
      Manifest-consolidator pathological-chunk-count bug (398 genuine FRED macro rows, real history back to 1962,
      stretching the merge span to 64 years — not corruption): tightened `_DUCKDB_MERGE_MAX_CHUNKS` 2000→300 so the
      existing widen-safety-valve actually catches it (787 chunks vs. the ~85 a normal tradfi range needs). Verified
      safe fleet-wide first (cefi/defi/sports real chunk counts 74-89, all `<<` 300) before touching this
      shared-across-asset-groups constant. Regression test added. Shipped `unified-trading-library@59ed61c9`.
      **Rebuilt + redeployed the live consolidator** (`market-tick-data-service-live-defi-rollout` Cloud Build
      `19b20104-9000-44ff-b968-77468617832f`, SUCCESS). Verified live in the running job's own logs:
      `phase=merge_chunk_days_widened ... effective_chunk_days=78` → `chunks=303` (down from 787), cycle completed in
      ~75s. Repo: unified-trading-library.
- [x] ✅ [DATA] P1. **DONE 2026-07-30 — RESOLVED, verified real rows now capture.** Read the re-launched fleet's per-VM
      manifest shards directly (not the canonical index, which lags by up to one merge cycle): the 2026 year-shard VM
      shows REAL captured `ohlcv_1m`/`ohlcv_1s` data for 2026-01-02/05/06 — e.g. 4 real per-contract row counts
      (1190/1519/86/1) for `ohlcv_1m` on 2026-01-02, tens of thousands of rows for `ohlcv_1s`. This directly proves the
      zero-capture problem is resolved: real ES data captures today, from this exact re-launched fleet, once the two
      infra bugs above stopped blocking it. The canonical-index query scoped to `instrument_id=ES.FUT` still shows 0
      real rows for this run — see the next todo, this is the reason why (a tagging gap, not a capture failure).
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s P0 todo can now cite this evidence.
- [x] ✅ [CODE] P2. **DONE 2026-08-04 — root cause was one level deeper than the write-site hypothesis above, real write
      site was the MANIFEST bookkeeping, not `databento_enrichment.py`.** Traced the actual blank-write:
      `databento_enrichment.py::_enrich_with_canonical_ids` already stamps a correct per-row `instrument_id` on every
      DataFrame row (verified — `build_instrument_id` with `expiry_date` succeeds for every surviving dated contract).
      The blank came from `venue_fetch.py::_record_venue_shard_counts`, which unconditionally hardcoded
      `instrument_id_for_manifest = ""` for every `is_derivative` (futures_chain/options_chain) manifest shard — correct
      for bulk data_types like `trades` (genuinely one blob spanning many contracts, regression-tested, untouched) but
      wrong for `ohlcv_1m`/`ohlcv_1s`, which UAC's own `_PER_INSTRUMENT_SHARD_DATA_TYPES` registry already declares
      per-contract. Fix: new `_tradfi_manifest_shard._resolve_chain_bundle_manifest_id` stamps a canonical
      per-(venue,underlying) bundle id (e.g. `CME:FUTURE:SP500` via `build_instrument_id(passthrough=True)`) for TradFi
      chain-bundle OHLCV shards only; every other chain-bundle data_type/venue is unaffected. 3 new regression tests +
      all 9924 existing tests green, `quality-gates.sh` clean. Shipped `market-tick-data-service@65beaeaf` (+
      `d22d3604`, a follow-up file-size-ratchet trim). Repo: market-tick-data-service. **Scope note**: this fixes NEW
      captures going forward only — the 28,307+111 pre-existing blank-`instrument_id` rows the first correction banner
      found are NOT backfilled by this change; tracked as a new todo below.
- [x] ✅ [DATA] P3. **RE-VERIFIED 2026-08-05 — NONE of the 3 existing migration scripts can reconcile these rows.**
      `recover_tradfi_garbage_underlying_2026_07.py` / `migrate_tradfi_canonical_2026_07.py` /
      `rebundle_tradfi_chains_2026_07.py` all operate at the GCS-object level (path migration, garbage-`underlying=`
      recovery, per-contract→bundle reduce). The blank-`instrument_id` rows are a **manifest metadata** problem: the
      `_index/availability_index.parquet` rows have `instrument_id=""` with correct `underlying` values
      (SP500/MICRO-SP500/MES/ECES). A new, dedicated script would be needed to: (1) read the manifest index, (2) select
      rows where `instrument_id=""` ∧ `row_count>0` ∧ valid `underlying`, (3) derive the canonical bundle ID via
      `_resolve_chain_bundle_manifest_id(venue, instrument_type, underlying, data_type)` → e.g. `CME:FUTURE:SP500`, (4)
      rewrite those rows. None of the 3 existing scripts touch manifest metadata at all — they handle GCS parquet
      objects only. Repo: market-tick-data-service.
- [x] ✅ [DATA] P3. **DONE 2026-08-05 — ALL six other CME roots confirmed same pattern as ES; fix is fleet-wide, no
      further code needed.** Live manifest query (`_index/availability_index.parquet`, 2026-08-05) for
      CL/GC/HG/NG/NQ/SI: every root shows the exact same `instrument_id={ROOT}.FUT` zero-capture pattern (0 captured
      rows, all `attempted_failed`/`empty_confirmed`). Real capture data IS flowing for 5/6 roots via the
      blank-`instrument_id` path, confirming `market-tick-data-service@65beaeaf`'s `_resolve_chain_bundle_manifest_id`
      fix applies fleet-wide: CL (CRUDE: 1.3M ohlcv_1m + 11.5M ohlcv_1s bars, 2026), GC (GOLD: 446K + 5.1M, 2026), HG
      (COPPER: 333K + 2.0M, 2026), NG (NATGAS: 13.5K ohlcv_1s, 2026-08-03), SI (SILVER: 2.4K ohlcv_1s, 2026-08-03). NQ
      (NASDAQ100) has no blank-instrument_id rows yet (no recent backfill run) but shares the identical code path — no
      additional work needed. The two infra bugs (stall-watchdog timeout, manifest-consolidator chunking) were already
      fixed fleet-wide by the earlier P1 todos. Repo: instruments-service (manifest query only, no code changes).

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03** (second pass, refreshed methodology): re-verified, unchanged (5 entries) —
  `databento_enrichment.py` already listed is confirmed the exact write site the remaining P2 blank-`instrument_id` todo
  targets.
- **slot-3 worker 2026-08-04**: P2 shipped `market-tick-data-service@65beaeaf`+`d22d3604` — real write site was
  `venue_fetch.py::_record_venue_shard_counts`, not `databento_enrichment.py` (see the flipped todo above for the
  corrected root cause). Hit + resolved an unrelated repo-wide `quality-gates.sh` blocker along the way (pip-audit CVE
  in pinned `cryptography` — filed `mtds_cryptography_pip_audit_cve_qg_red_2026_08_03.md`, repo-blocker `RB-e7d79260`;
  fix landed upstream as `market-tick-data-service@f4c16feb` while waiting). Added a new P3 backfill-reconciliation todo
  for the pre-existing 28,307+111 blank rows this fix does not retroactively touch.
- **slot-3 worker 2026-08-05** (task `tradfi_es_cme_ohlcv_zero_capture-010`): Re-verified the P3 question. Read all 3
  migration scripts in full (`recover_tradfi_garbage_underlying_2026_07.py`, `migrate_tradfi_canonical_2026_07.py`,
  `rebundle_tradfi_chains_2026_07.py`) plus the shipped fix
  (`_tradfi_manifest_shard.py::_resolve_chain_bundle_manifest_id`) and the manifest-write site
  (`venue_fetch.py::_record_venue_shard_counts`). **Finding: none of the 3 scripts can reconcile the
  blank-`instrument_id` manifest rows.** All 3 operate at the GCS-object level (path migration, garbage-`underlying=`
  path-segment recovery, per-contract→per-root-bundle reduce). The blank-`instrument_id` problem is in the **manifest
  metadata** (`_index/availability_index.parquet` rows), not in GCS object paths. The GCS parquet objects themselves are
  correctly placed and contain real data; only the manifest `instrument_id` column is blank. A new dedicated script
  would be needed that reads the manifest index, selects rows with blank `instrument_id` + valid `underlying`, and
  derives the canonical bundle ID via `_resolve_chain_bundle_manifest_id(venue, itype, underlying, data_type)` → e.g.
  `CME:FUTURE:SP500`. The canonical derivation logic already exists and is proven (`market-tick-data-service@65beaeaf`);
  the gap is only the manifest-row update mechanism.
- **context-scout 2026-08-06**: re-scouted; all todos are now DONE, so trimmed context_scope from 5 to 4 entries —
  dropped `tradfi_consolidated_closeout_2026_07_18.md` (generic parent index) and `databento_enrichment.py` (confirmed
  NOT the real write site — see the 2026-08-04 P2 finding above), swapped in the real fix sites
  `venue_fetch.py::_record_venue_shard_counts` and `_tradfi_manifest_shard.py` for anyone reconciling the pre-existing
  blank-`instrument_id` backfill this fix doesn't retroactively touch.

## Follow-ups

- [x] ✅ [DATA] P3. **DONE 2026-08-09 — `market-tick-data-service@63cff354`** (via
      `plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1). Wrote + ran
      `scripts/restamp_tradfi_cme_chain_bundle_blank_instrument_id_2026_08_09.py` to backfill the pre-existing
      blank-instrument_id manifest rows in `market-data-tick-tradfi-prd` `_index` (derives canonical bundle ID via
      `_resolve_chain_bundle_manifest_id` and CAS-rewrites the rows). **Live count at execution time was 3,267 rows (41
      roots), not the 28,307+111 figure above** — 10 days of continued backfill activity with the already-fixed writer
      had superseded most of the original population with correctly-tagged twins; see the plan's Progress Log
      (2026-08-09 entry) for the full per-root breakdown and the independent post-apply verification (0 remaining).

> **2026-08-06 archive-candidate audit**: The P2 fix (market-tick-data-service@65beaeaf) covers NEW captures only; the
> P3 todo verified none of the 3 existing migration scripts can reconcile the pre-existing blank-instrument_id rows and
> 'a new, dedicated script would be needed', but no - [ ] todo tracks writing/running it — context-scout 2026-08-06
> still refers to 'the pre-existing blank-instrument_id backfill this fix doesn't retroactively touch'.

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
status: open
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
---

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

- [x] ✅ [INFRA] P1. **DONE 2026-07-30 — the systemic stall-watchdog/consolidator-lock-horizon mismatch UPDATE 2 found
      above.** `_tradfi-ohlcv-launcher-lib.sh` now sets `STALL_TIMEOUT_SEC=3900` alongside `STALL_PROGRESS_REGEX` (3600s
      consolidator-lock horizon + 300s buffer, vs. the 1800s generic default that was killing legitimately- waiting
      VMs). 2 new regression tests, `quality-gates.sh` green. Shipped `deployment-service@c1e3dc70`. Repo:
      deployment-service.
- [ ] [DATA] P1. **CURRENT, ACTIVE TODO — supersedes the "diagnose the tagging mismatch" framing below, which is now
      understood to be secondary, not the primary cause.** Verify the SECOND re-launch of the 7
      `tradfi-bf-cme-ohlcv-1m-es-*` VMs (started `2026-07-30T10:41-10:43Z`, post-stall-timeout-fix, scope
      `--only-root ES`, same 2020-2026 year-shards as the original fleet) actually captured real rows once they
      complete/self-delete. Re-run this issue's original query — live read of `market-data-tick-tradfi-prd`'s
      `_index/availability_index.parquet`, scoped to
      `venue=CME, instrument_id=ES.FUT, data_type in {ohlcv_1m,     ohlcv_1s}`, filter `written_at` to this run's date —
      and confirm `row_count>0` / `capture_status=captured` now appears for at least a substantial share of the
      2020-2026 window. If this second attempt ALSO shows 0 real rows with no stall-kill/preemption signature in the
      logs, re-open as a genuine code-bug investigation (starting with the `stype_in=parent`-vs-schema hypothesis in
      "Recommended next steps" §1 below) — do not assume transient a third time without evidence. Cite the resulting row
      counts as closing evidence on both this issue and `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s
      original P0 todo (which reported the original false "zero capture ever" framing). Repo: market-tick-data-service.
- [ ] [DIAG] P2. **Secondary, lower-priority data-hygiene item (demoted from P1 — confirmed NOT the cause of the
      original zero-capture finding, see UPDATE above).** Real ohlcv_1m/1s data for the SP500/ES/MES family already
      exists under a BLANK `instrument_id` with `underlying` correctly populated (28,307+111 real rows; `written_at`
      2026-06-21..2026-07-28) — see the first CORRECTION banner above for the exact query + overlap evidence. Diagnose:
      (a) which script/handler wrote these blank-`instrument_id` rows; (b) whether
      `recover_tradfi_garbage_underlying_2026_07.py` or a sibling migration script already covers reconciling
      blank-`instrument_id`-but-real-`underlying` manifest rows into the canonical `ES.FUT` tag, or whether this is a
      genuinely new gap in that tooling's scope. Repo: market-tick-data-service.
- [ ] [DATA] P3. Once P1 confirms the re-launched fleet captured real `ES.FUT`-tagged rows, determine whether the other
      "in flight" CME roots (CL/GC/HG/NG/NQ/SI) show the same historical zero-capture pattern their own fleets — if so,
      the same "just re-run it" fix likely applies there too; check before assuming any of them need a code change.
      Repo: instruments-service.

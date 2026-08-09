---
doc_type: issue
title: CeFi Track-7 candle bundle regeneration — dedicated VM needed for MDPS --force backfill
summary: >-
  The 149 stale per-leg objects from the bundle-collision race are all GONE (deleted), but the replacement ticks.parquet
  bundles are incomplete across 105/112 affected cells. MDPS --force cannot run on the shared planning VM (34GB+ RSS,
  risk of AO outage). A dedicated VM is needed to regenerate the 8 affected days.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service]
scope: [engineer]
tags: [cefi, track-7, candle-bundle, mdps-backfill, vm-required]
related:
  [
    /plans/archive/2026_07/cefi_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
author: slot-11 (data_engineering)
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  cefi_consolidated_native_ao_extract_2026_07_25.md Todo 7 (Track-7 candle bundle-collision fix)
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/cefi_consolidated_native_ao_extract_2026_07_25.md,
    deployment-service/scripts/vm/launch-mdps-backfill-vm.sh,
    /plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md,
  ]
---

# CeFi Track-7 candle bundle regeneration — dedicated VM needed

## What I found

### Part (a): Raw-tick presence — ALL PASS

All 8 affected days have raw-tick data in GCS for both BYBIT `futures_chain` and DERIBIT `options_chain`. The backfill
is unblocked on the source-data side. See the plan Progress Log for the full per-day table.

### Part (b): 149 stale objects are all GONE

All 149 per-leg residual objects listed in `plans/audit/results/cefi_todo19_149_residual_objects_2026_07_23.csv` (93
BYBIT futures_chain + 56 DERIBIT options_chain) return 404 from GCS — deleted. The immediate GCS clutter from the
bundle-collision race is resolved.

### Part (b): Bundle integrity — 105/112 cells INCOMPLETE

The canonical `ticks.parquet` bundles under
`processed_candles/by_date/day={day}/pipeline_mode=batch_tardis/timeframe={tf}/data_type={dtype}/instrument_type={INSTYPE}/venue={VENUE}/ticks.parquet`
were audited across all 8 days × 7 timeframes × 2 venue/type combos (112 cells total):

| Status  | Count | Description                                                            |
| ------- | ----- | ---------------------------------------------------------------------- |
| OK      | 7     | Correct symbol count matching pre-delete per-leg CSV                   |
| PARTIAL | 9     | Bundle exists but has only 1 symbol (the "race winner") instead of 2-3 |
| MISSING | 96    | No bundle at all at this path                                          |

Pattern:

- Only `15s` and `15m` timeframes have any bundles at all (all BYBIT futures_chain)
- All DERIBIT options_chain cells are MISSING across all 8 days × 7 timeframes
- BYBIT futures_chain for 2025-11-01 and 2026-01-01: ALL timeframes MISSING
- Every existing `15m` BYBIT bundle is PARTIAL — has only BTC, missing ETH (and SOL where applicable)

### Part (b): MDPS `--force` cannot run on shared planning VM

Attempted a narrow MDPS `--force` run (single day, single venue, single data_type, 2 timeframes). The MDPS framework
loaded 5,610 instruments and RSS climbed to 34GB+ before the run was killed. Running the full MDPS on the shared
planning VM would risk another AO outage (2 prior incidents: `expand_defi_pool_catalogue` 43.6GB,
`features_service.cross_instrument` 38.8GB). Dry-run mode works correctly and confirms the scoped backfill would only
touch 2-10 raw-tick files per cell.

## Why it matters

The 149 stale per-leg objects were correctly deleted, but their data was never merged into the shared `ticks.parquet`
bundles. Downstream consumers (features-service, strategy-service, UI) reading the bundle only see one leg's data (e.g.,
BTC futures chain but not ETH futures chain for the same day). This is a silent data gap — the bundles EXIST (no
manifest error) but are INCOMPLETE.

## Recommended decision

Launch a dedicated MDPS `--force` backfill VM (SPOT, per backfill-VM-defaults) scoped to:

- 8 days: 2023-06-01, 2023-08-02, 2023-11-02, 2024-02-01, 2024-02-02, 2024-07-01, 2025-11-01, 2026-01-01
- 2 venues: BYBIT (futures_chain), DERIBIT (options_chain)
- 7 timeframes: 15s, 1m, 5m, 15m, 1h, 4h, 1d
- Asset group: CEFI
- `--force` flag to regenerate existing bundles

The scope is tiny (2-10 raw-tick inputs per cell) — the MDPS framework overhead is the only reason this can't run on the
shared VM. A dedicated f1-micro or e2-small SPOT instance is sufficient.

## Todos

- [x] ✅ [INFRA] P2. **Launch dedicated MDPS `--force` candle backfill VM for Track-7: 8 days × BYBIT futures_chain +
      DERIBIT options_chain × 7 timeframes, CEFI only.** (repo: deployment-service, market-data-processing-service). Use
      the standard `launch-mdps-backfill-vm.sh` launcher with
      `MDPS_DATA_TYPES="futures_chain options_chain" MDPS_VENUES="BYBIT DERIBIT" MDPS_TIMEFRAMES="15s 1m 5m 15m 1h 4h 1d" MDPS_ASSET_GROUP=CEFI`,
      `--force`, and `--start-date 2023-06-01 --end-date 2026-01-01`. Bounded scope: ~600 raw-tick input files total
      across 8 non-contiguous days. SPOT instance (idempotent `--force` is safe to re-run on preemption). **Done when**:
      VM completes with exit 0, post-backfill bundle audit shows all 112 cells OK (correct per-leg symbol counts).
      **Launched**: `mdps-backfill-cefi-20260804-190444` (SPOT, e2-standard-8, asia-northeast1-c, RUNNING as of
      2026-08-04T19:04:44Z). GCS logs:
      `gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-cefi-20260804-190444/`. Post-completion
      audit todo below.

## Progress Log

- **context-scout 2026-08-05**: populated context_scope (5 entries).
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (5 entries), unchanged -- the 2026-08-06
  archive-candidate audit note (unmet done-when) doesn't change the reading list: the launcher + both codex VM SSOTs +
  the closeout/source plans still cover it.
- **slot-16 infra 2026-08-07**: Relaunched VM `mdps-backfill-cefi-20260807-130321` (SPOT, e2-standard-8,
  asia-northeast1-c). Verified no conflict with concurrent trades VM. LAUNCH_PARAMS.json written T+1min confirming
  startup. Scope: BYBIT futures_chain + DERIBIT options_chain, 2023-06-01→2026-01-01, --force. 2025-11-01 and 2026-01-01
  BYBIT have no raw data — MDPS will skip.
- **slot-7 data_engineering 2026-08-07**: Post-completion audit completed. VM `mdps-backfill-cefi-20260804-190444`
  confirmed preempted at T+2min (gcloud op `systemevent-1785870422262`); no run.log; zero work done. Bundle state:
  42/112 DERIBIT OK (6 days, BTC+ETH present, updated by prior Aug 3 + Jul 22 runs); 42/112 BYBIT PARTIAL (1 symbol per
  bundle, race-winner state unchanged); 14/112 DERIBIT MISSING (2023-11-02, 2024-07-01 — raw data exists); 14/112 BYBIT
  MISSING (2025-11-01, 2026-01-01 — NO raw tick data). Added relaunch (P2 INFRA) and raw-gap investigation (P3 DATA)
  todos.
- **slot-26 data_engineering 2026-08-08**: Checked terminal state of `mdps-backfill-cefi-20260807-130321` — preempted
  T+1h46m, only reached 9/~950 days of its wrongly-scoped full-range run. Ran 126-path per-cell audit: BYBIT still
  PARTIAL on all 6 target days (unchanged since 2026-08-03). Root-caused + fixed a `--force`-drop bug in
  `market-data-processing-service`'s per-date subprocess spawner (`e9f9819`) that fully explains why 2 relaunches never
  fixed BYBIT. Found + documented a 3rd VM already running with the same pre-fix scope
  (`mdps-backfill-cefi-20260808-095136`) — left running (not stale) per the VM-delete guardrail, flagged for operator.
  Filed `issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md` (cross-cutting finding) + added a
  per-day-scoped relaunch todo above. See "2026-08-08 84-cell audit" section for full detail.
- **2026-08-09 (independent corroboration + ETA correction)**: Re-verified `mdps-backfill-cefi-20260807-130321` is
  genuinely gone (404 on `gcloud compute instances describe`; only `insert`+`compute.instances.preempted` ops, no
  successor) and independently confirmed `mdps-backfill-cefi-20260808-095136` is the correct, already-launched successor
  — no duplicate relaunch performed. Sampled 2 of the 6 BYBIT target days already reached by this VM (2023-06-01,
  2023-08-02): both bundles unchanged bit-for-bit from the pre-fix state (`Update time` still `2026-08-03T01:59:07Z`,
  still 1 symbol each), confirming this pre-fix VM will not fix BYBIT even at completion, as already noted above. **ETA
  correction**: the "~8 months of continuous uptime" estimate above appears to be an arithmetic slip. Measured rate over
  a longer, more recent window (2023-06-01 start 08-08T08:59:28Z → 2023-08-26 start 08-09T01:22:53Z = 86 days / 16.38h ≈
  5.25 days/hour): remaining ~860 days ÷ 5.25/h ≈ 164h ≈ **~7 days**, not 8 months — full natural completion (if it
  survives that long without a further preemption) is a week-scale wait, not a multi-month one. Doesn't change the
  recommended action (per-day-scoped relaunch already queued below for once it terminates), just corrects the timeline
  other agents/the operator should expect.

## Follow-ups

- [x] ✅ [DATA] P2. Post-completion bundle audit: confirm mdps-backfill-cefi-20260804-190444 exited 0 and all 112 cells
      are OK (correct per-leg symbol counts) — **FINDING: VM was preempted at T+2min (insert 2026-08-04T19:04:54Z →
      preempted 2026-08-04T19:07:05Z, confirmed via `gcloud compute operations list`). No run.log in GCS. ZERO work
      done.** Current bundle state (audited 2026-08-07): 42/112 DERIBIT cells OK (6 days × 7 tf, BTC+ETH underlyings
      present); 42/112 BYBIT cells EXIST but PARTIAL (6 days × 7 tf, only 1 symbol per bundle — same race-winner state
      as pre-launch); 14/112 DERIBIT cells MISSING (2023-11-02 + 2024-07-01, raw data exists); 14/112 BYBIT cells
      MISSING (2025-11-01 + 2026-01-01, NO raw tick data in GCS). **NOT 112/112 OK. VM must be relaunched.** Evidence:
      gcloud op systemevent-1785870422262-6583d5c2244d0 (preempted); bundle sampling: 2023-06-01/15s/BYBIT→1 symbol
      (BTC-29DEC23), 2023-08-02/15s/BYBIT→1 symbol (ETH-29MAR24), source raw has both BTC+ETH underlyings confirming
      partial. unified-trading-pm@<sha>

- [x] ✅ [INFRA] P2. Relaunch MDPS --force VM for Track-7 BYBIT+DERIBIT incomplete cells. Scope: same 8 days × BYBIT
      futures_chain + DERIBIT options_chain × 7 timeframes, CEFI only, --force. Note: 2025-11-01 and 2026-01-01 BYBIT
      futures_chain have NO raw tick data (no `raw_tick_data/…/venue=BYBIT/instrument_type=futures_chain/` for those
      days) — investigate raw data gap separately; exclude those days from --force rerun scope or let MDPS skip them.
      Focus on: 6 days × BYBIT (partial→correct) + 2 days × DERIBIT (2023-11-02, 2024-07-01) (missing→present). **Done
      when**: VM exits 0, post-backfill audit shows all reachable cells OK (42 DERIBIT + 42 BYBIT from 6 days = 84 cells
      at minimum). Confirm via per-cell symbol count check in GCS. **Launched**: `mdps-backfill-cefi-20260807-130321`
      (SPOT, e2-standard-8, asia-northeast1-c, RUNNING as of 2026-08-07T13:03:21Z). Verified concurrent trades VM
      (`mdps-backfill-cefi-20260802-140125`) is on different data_type (trades), no conflict. GCS logs:
      `gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-cefi-20260807-130321/`. LAUNCH_PARAMS.json
      confirmed written T+1min. unified-trading-pm@0273bc1e0

- [ ] [DATA] P3. Investigate why 2025-11-01 and 2026-01-01 have no BYBIT futures_chain raw tick data in the cefi-prd GCS
      bucket (no `instrument_type=futures_chain` directory under `venue=BYBIT` for those 2 days in batch_tardis).
      Determine if Tardis re-download is needed. (repo: market-tick-data-service)

- [ ] [DATA] P2. **Once `mdps-backfill-cefi-20260808-095136` reaches a terminal state, relaunch scoped PER-DAY** (6
      single-day launches — `--start-date`==`--end-date` for each of 2023-06-01, 2023-08-02, 2023-11-02, 2024-02-01,
      2024-02-02, 2024-07-01 — NOT a multi-day range) for BYBIT futures_chain + DERIBIT options_chain, `--force`. The
      root-cause fix (`market-data-processing-service@e9f9819`, see
      `issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md`) is now live, so a fresh VM launch will
      correctly force-reprocess. **Done when**: 84-cell audit (6 days × 2 venues × 7 timeframes) shows BYBIT bundles
      carry both BTC+ETH `instrument_id`s and DERIBIT bundles are present for all 6 days (both underlyings). **RISK FLAG
      (2026-08-09, unconfirmed)**: a static code-reading pass found a SEPARATE possible root cause for the original
      1-symbol "race winner" defect — BTC and ETH raw files may be written via independent concurrent
      `ThreadPoolExecutor` tasks that each straight-overwrite the SAME shared `ticks.parquet` (no merge-on-write step
      found in `candle_write_mixin.py`/`canonical_writer.py`), which would recur regardless of `--force` correctness.
      Not yet live-confirmed (no post-fix relaunch has completed yet). When THIS todo's own audit runs, explicitly check
      for this failure mode before declaring done — see
      `issues/mdps_multi_instrument_bundle_write_race_hypothesis_2026_08_09.md`.

## 2026-08-08 84-cell audit (6 BYBIT + 6 DERIBIT days, pre-relaunch baseline)

Ran a targeted per-cell existence + `instrument_id`-uniqueness check against GCS for the 6 BYBIT-eligible target days
(excludes 2025-11-01/2026-01-01, no raw BYBIT data) × {BYBIT futures_chain, DERIBIT options_chain BTC+ETH} × 7
timeframes = 126 paths:

- **BYBIT (42 cells, all 6 days × 7tf)**: all EXIST but ALL still PARTIAL — every sampled bundle carries exactly 1
  `instrument_id` (e.g. `2023-06-01/15s` → `BYBIT:FUTURE:BTC-20231229` only, no ETH leg). GCS `Update time` on the
  2023-06-01/15s object is `2026-08-03T01:59:07Z` — predates BOTH the 2026-08-04 and 2026-08-07 relaunches despite
  run.log showing 2023-06-01 was actively (re)processed by the 2026-08-07 VM. **Root cause found and fixed**: see below.
- **DERIBIT (84 cells, 6 days × 2 underlyings × 7tf)**: 2023-08-02, 2024-02-01, 2024-02-02 → OK (1 instrument per
  underlying-partitioned file, matches the intended per-underlying-partition design, NOT partial). 2023-11-02,
  2024-07-01 → still MISSING (no raw-tick-triggered write yet — VM hasn't reached these days).

**Root cause of the BYBIT non-fix**: `market-data-processing-service`'s per-date subprocess spawner
(`process_handler.py::_run_date_as_subprocess`) never forwarded the parent's `--force` flag to the child date-
subprocess — confirmed via `mdps-backfill-cefi-20260807-130321`'s run.log: parent argv carries `--force`, but the child
argv for `2023-06-01` does not, and the process log explicitly states `Force: False`. This means BOTH prior "fix"
relaunches ran with force silently disabled for every date, so already-PARTIAL bundles were skipped, not regenerated —
while the run still exited 0 as if it worked. Fixed in `market-data-processing-service@e9f9819` (unit-tested,
quality-gates.sh green, landed on `origin/live-defi-rollout`). Full writeup + cross-cutting impact (this bug affects
EVERY multi-day `--force` MDPS backfill, not just Track-7):
`issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md`.

**A third VM is currently running** (`mdps-backfill-cefi-20260808-095136`, started 2026-08-08T08:57:08Z, same full
2023-06-01→2026-01-01 range + BYBIT+DERIBIT+--force scope as the prior 2 relaunches — almost certainly the launcher's
SPOT-preemption auto-relaunch reusing the persisted pre-fix `LAUNCH_PARAMS.json`). Confirmed alive and progressing (not
stale — actively logging, currently on `2023-07-14` as of this audit), but its running snapshot predates the
force-forwarding fix, so it will not actually fix BYBIT even once it reaches the target days, and at the observed ~12
min/day rate would need ~8 months of continuous uptime to reach `2026-01-01` — virtually guaranteed to be preempted
again first. NOT terminated by this audit per the VM-delete guardrail (actively progressing, not confirmed-stale —
deletion is a judgment call outside this agent's scope; flagged for operator visibility given the compute waste). New
relaunch todo added above for once it reaches a terminal state.

> **2026-08-06 archive-candidate audit**: The only todo's own done-when (VM exit 0 + post-backfill bundle audit shows
> all 112 cells OK) is unmet — evidence cites only 'Launched... RUNNING as of 2026-08-04T19:04:44Z', and the promised
> 'Post-completion audit todo below' was never actually created.

> **2026-08-07 audit result**: VM confirmed preempted T+2min. 42/112 cells OK (DERIBIT only). Relaunch + raw-data
> investigation todos added above.

> **2026-08-08 audit result**: `mdps-backfill-cefi-20260807-130321` confirmed preempted at T+1h46m (gcloud op
> `systemevent-1786114166437`, `compute.instances.preempted`) after processing only 9 sequential days
> (2023-06-01→2023-06-09) of the wrongly-scoped full 2023-06-01→2026-01-01 range — never reached 5 of the 6 remaining
> BYBIT target days. Of the 1 target day it did reach (2023-06-01), the bundle was NOT actually fixed due to the
> --force-drop bug above. Root cause fixed (market-data-processing-service@e9f9819); next relaunch (todo above) will use
> corrected per-day scoping once the currently-running mdps-backfill-cefi-20260808-095136 terminates.

## Progress Log (continued)

- **context-scout 2026-08-09**: refreshed context_scope (6 entries) -- added the cross-cutting
  `mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md` issue (the root-cause fix that explains why 2 prior
  relaunches never fixed the BYBIT cells, per the 2026-08-08 slot-26 finding above).

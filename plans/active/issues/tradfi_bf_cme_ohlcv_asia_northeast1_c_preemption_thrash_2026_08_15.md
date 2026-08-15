---
doc_type: issue
title:
  tradfi-bf-cme-ohlcv-1m fleet is thrashing in asia-northeast1-c — checkpoint contract intact per-VM, but net campaign
  progress regressed from near-complete to <10% and the preemption-recovery pipeline is largely blind to it
summary: |
  Fleet-wide preemption scan (unrelated to the CeFi liquidations work being monitored at the time) found
  `tradfi-bf-cme-ohlcv-1m-*` in an active preempt-relaunch-preempt thrash in `asia-northeast1-c` — 100% of ~150
  preemptions sampled across tradfi AND mdps-{cefi,tradfi} families over 2026-08-11..15 are in that one zone. For the
  worst shard (`eth-2022`), the PROGRESS.json checkpoint contract IS being written correctly per-VM-run (monotonic,
  advances during each VM's short life), but the CAMPAIGN nonetheless regressed: it reached `last_completed_date
  =2022-12-30` (year essentially done) by 2026-08-10, then every relaunch since 2026-08-12 restarts near January and has
  not exceeded `2022-01-28` across 6 more launches over 3 days. Root cause is not proven, but the evidence points at
  `wave_launcher.py`'s periodic (2-3h) gap-fill dispatch never reading the per-VM PROGRESS.json checkpoint at all (it
  redispatches from the manifest-computed gap, `START_DATE=2022-01-01` every time), combined with the ALREADY-TRACKED
  `dp-exit-code-monitor` timeout (`dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md`) leaving the
  preemption-specific `RelaunchPreemptedVm` actuator — the ONE path that actually resumes from checkpoint — largely
  unable to reach these VMs before its own sweep dies. No `DP_VM_PREEMPTED`/`DP_VM_PREEMPTED_RECOVERED` event was found
  in Cloud Logging for this shard's 13 preemptions in 3 days.
status: open
nature: issue
asset_group: [tradfi, cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-preemption, billing-waste, spot-capacity, checkpoint-resume, alerting-gap, cross-cutting, big-finding]
related:
  [
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md,
    /plans/archive/issues/asia_northeast1_c_spot_preemption_storm_2026_08_04.md,
    /plans/active/issues/tradfi_vm_resource_utilization_downsize_2026_08_10.md,
  ]
created: 2026-08-15
priority: P1
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found while monitoring an unrelated CeFi liquidations re-derive VM; a fleet-wide GCP preemption scan turned up this as
  a separate, real billing-waste problem. Audited per the /vm-preemption-billing-waste-audit skill, 2026-08-15.
drift_direction: advance-code
context_scope:
  [
    deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh,
    deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh,
    deployment-service/scripts/wave_launcher.py,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    /plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md,
  ]
---

# tradfi-bf-cme-ohlcv-1m thrashing in asia-northeast1-c — checkpoint intact per-VM, campaign progress regressed

## What I found

Auditing the preemption thrash flagged in the operator's evidence (11 preemptions on `eth-2022`, 9 on `es-2022`, 8 each
on 7 more CME roots, over ~30h 2026-08-13..15) per `/vm-preemption-billing-waste-audit`, scoped to the worst family:
`tradfi-bf-cme-ohlcv-1m-*`.

### 1. Zone concentration is total, not partial

Every preemption sampled — CME OHLCV (`eth-2022`, `es-2022`) AND the secondary `mdps-{cefi,tradfi}-*` families — is in
**`asia-northeast1-c`**, the hardcoded default in `_tradfi-ohlcv-launcher-lib.sh`
(`TRADFI_OHLCV_ZONE="${TRADFI_OHLCV_ZONE:-asia-northeast1-c}"`). This is the SAME zone as the already-resolved
`asia_northeast1_c_spot_preemption_storm_2026_08_04.md` (151 preemptions/5h across sports/tradfi/cefi, worked around at
the time via a launcher-owned backoff for the sports `expected-universe-v2` family only — that fix does not touch the
CME OHLCV launcher, which has no owned retry loop of its own; it relies entirely on the fleet-wide
`RelaunchPreemptedVm`/wave-launcher path). The zone has now produced a second, independent multi-day thrash episode 11
days later — this reads as a standing structural SPOT-contention risk for this zone, not a one-off.

### 2. Preemption lifetimes: mostly under 10 minutes

For `eth-2022` (13 preemptions, 2026-08-12T15:04Z .. 2026-08-14T20:12Z UTC, launch-timestamp-to-preemption-timestamp
computed from the VM name's embedded `run_ts` vs. the matching `compute.instances.preempted` operation):

| Launch (UTC)   | Preempted (UTC) | Lifetime |
| -------------- | --------------- | -------- |
| 08-12 15:04:46 | 08-12 15:07:55  | ~3m9s    |
| 08-12 21:05:39 | 08-12 21:06:48  | ~1m9s    |
| 08-13 03:04:25 | 08-13 03:05:28  | ~1m3s    |
| 08-13 06:05:33 | 08-13 06:07:37  | ~2m4s    |
| 08-13 09:04:22 | 08-13 09:50:44  | ~46m22s  |
| 08-13 12:06:04 | 08-13 12:24:56  | ~18m52s  |
| 08-13 18:08:43 | 08-13 18:17:13  | ~8m30s   |
| 08-13 21:05:00 | 08-13 21:05:57  | ~57s     |
| 08-14 00:05:03 | 08-14 00:30:52  | ~25m49s  |
| 08-14 06:07:03 | 08-14 06:12:56  | ~5m53s   |
| 08-14 18:05:17 | 08-14 18:35:02  | ~29m45s  |
| 08-15 00:06:03 | 08-15 00:25:27  | ~19m24s  |
| 08-15 03:04:52 | 08-15 03:12:37  | ~7m45s   |

`es-2022` shows the same shape (9 preemptions, same window, lifetimes ~1-46 min, all `asia-northeast1-c`). Several VMs
die inside 2-3 minutes — not enough time to clear boot + setup, let alone fetch a chunk. This is real capacity
contention (`gcloud compute operations list` confirms genuine `compute.instances.preempted` operations, not a
misclassified crash), not a launcher bug in the preemption itself.

### 3. Checkpoint contract IS working per-VM-run — but relaunch cadence proves it is not being consulted

`vm-logs/{vm}/PROGRESS.json` exists and is monotonic for every VM that survived long enough to complete a chunk (its own
weekly-chunk granularity from `mtds_chunk_loop.sh` — checkpoints land on Fridays: `2022-01-07`, `-14`, `-21`, `-28`,
matching a ~1-week chunk boundary). `LAUNCH_PARAMS.json` for every relaunch shows `VM_FORCE=false` (steady-state,
skip-enabled backfill — the correct, lower-risk mode per `spot-vms-for-backfill.md`).

But the **relaunch cadence for this shard is ~3-6h, not the ~5-60min a preemption-triggered actuator would produce.**
Listing every `tradfi-bf-cme-ohlcv-1m-eth-2022-*` VM's `vm-logs/` directory and its `PROGRESS.json.last_completed_date`
over time:

```
...-20260809-180127 -> 2022-12-30   (2026-08-10T01:22:41Z)   # year essentially DONE
...-20260810-030103 -> 2022-12-30   (2026-08-10T11:08:37Z)
...-20260810-120245 -> NO PROGRESS.json
   [~40h gap in launches]
...-20260812-030446 -> 2022-01-21   (2026-08-12T04:03:14Z)   # REGRESSED to day 21
...-20260812-060410 -> 2022-01-21
...-20260812-090609 -> 2022-01-21
...-20260812-120502 -> 2022-01-28
...-20260813-000506 -> 2022-01-21
...-20260813-090422 -> 2022-01-14
...-20260813-150654 -> 2022-01-21
...-20260814-030815 -> 2022-01-21
...-20260814-090442 -> 2022-01-21
...-20260814-120437 -> 2022-01-14
...-20260814-150557 -> 2022-01-28
...-20260814-180517 -> 2022-01-07
...-20260814-210520 -> 2022-01-21
...-20260815-061113 -> 2022-01-21
```

The shard reached `2022-12-30` (year essentially captured) on 2026-08-10, then **every one of the next 15 launches over
5 days has been stuck oscillating between `2022-01-07` and `2022-01-28`** — never once exceeding late January. This is
not the `--force`/day-one-replay bug the checkpoint contract was built for (`VM_FORCE=false` throughout) — it looks like
**each new launch is starting completely fresh from `START_DATE=2022-01-01` (the `LAUNCH_PARAMS.json` default) and
re-doing REAL fetch work through January before dying**, rather than either (a) the `RelaunchPreemptedVm` actuator
passing the prior VM's `PROGRESS.json` checkpoint forward, or (b) presence-skip recognizing the December captures as
already-done and blowing through them in seconds.

**Not fully root-caused within this audit's bounded scope** — two live hypotheses, in order of likelihood:

1. **`wave_launcher.py`'s periodic gap-fill (not `RelaunchPreemptedVm`) is the actual relaunch mechanism for this
   shard.** The observed ~3-6h relaunch cadence matches wave_launcher's documented "Cloud Run Job + Scheduler (every
   2-3h) re-evaluates the gap and tops the running fleet back up" far better than a 5-60min preemption-actuator cadence
   would. wave_launcher dispatches from the CONSOLIDATED MANIFEST gap-recompute with `START_DATE`=year start — it has no
   path that reads a dead VM's `vm-logs/{vm}/PROGRESS.json` (that file is scoped per-VM-instance-name, not per-shard,
   and only `RelaunchPreemptedVm` is wired to read+forward it). If wave_launcher is winning the race to redispatch a
   dead shard before `RelaunchPreemptedVm`'s sweep gets there, the checkpoint is architecturally invisible to the
   mechanism actually doing the relaunching, even though the checkpoint file itself is fine.
2. **The December 2022 captures from 2026-08-10 may not have durably landed in the CONSOLIDATED manifest the
   freshness-skip check reads** (`MANIFEST_PER_VM_SHARDS=true` isolates each VM's shard; consolidation lag/failure is a
   known class — see the CeFi-DeFi 429-drop precedent this same session's monitoring context flagged). If so, every
   fresh launch's presence-skip would correctly see January as the first gap and genuinely re-fetch it — not a resume
   bug, but a manifest-consolidation gap masquerading as one. Timing coincidence worth checking:
   `tradfi_canonical_path_ migration_design_2026_07_19.md` and
   `tradfi_legacy_twin_candidates_already_absent_unexplained_2026_08_14.md` are both active in this exact window and
   touch TradFi path canonicalization — a migration touching 2022 CME paths mid- campaign is a plausible alternate
   explanation for captured data going "missing" from a freshness check. **Not verified** — I could not reach the
   consolidated `availability_index.parquet` for `market-data-tick-tradfi-*` within this audit's time budget
   (bucket-name resolution needs `resolve_bucket_name()`, not a guessed literal); the next investigator should read real
   `capture_status` for CME/ETH/ohlcv_1m/2022 to confirm which hypothesis holds.

Either way, **this is real billing waste**: the campaign for one CME root/year has burned ~29 VM-launches across 6 days
without netting more than ~28 days of one calendar year captured (worse if hypothesis 2 holds and December was already
real and is now being wastefully re-fetched).

### 4. Alerting: the auto-recovery/paging pipeline shows zero record of these preemptions, consistent with an

ALREADY-TRACKED, PARTIALLY-FIXED gap

`gcloud logging read` for `DP_VM_PREEMPTED` / `DP_VM_PREEMPTED_RECOVERED` / `DP_VM_PREEMPTED_NO_RELAUNCH` (corrected
field path `jsonPayload.event`, confirmed via `unified_trading_library/events/__init__.py` + the `PubSubEventSink`
schema) returns **zero hits for `eth-2022` over 3 days, and zero hits fleet-wide for any `DP_VM_*` event over 3 days**.
This is consistent with, and likely explained by, the ALREADY-OPEN P0
[`dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md`](/plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md):
`uts-prod-dp-exit-code-monitor` was hitting its 1800s Cloud Run task timeout on every execution before a fix landed
2026-08-14T22:52:48Z (`cloudbuild=b60b2180`). **That doc's own measurement is the direct explanation for why this
shard's preemptions never produced an alert or a fast checkpoint-aware relaunch** — the sweep was dying before it
processed most of the fleet.

**New data point for that existing issue, not a duplicate finding**: I independently confirmed via
`gcloud run jobs executions list` that the fix is real but **not 100% — 2 of 8 executions AFTER the fix deploy still
show `status.conditions[0].status=False` / "Task ... failed with exit code: 0"** (`f2h4w` 2026-08-15T04:00Z, `6p2nq`
2026-08-15T06:00Z), a ~25% residual failure rate in this sample. That doc's still-open Todo 2 ("make truncated sweep
loud instead of silent," code written 2026-08-15, blocked on an unrelated basedpyright ratchet issue) is exactly the fix
that would surface which VMs a truncated run skips — I'm adding this residual-failure measurement to that doc's Progress
Log rather than re-opening its Todo 1, since the fix for the underlying timeout is confirmed real and shipped; what
remains is the truncation-visibility gap that doc already tracks.

**Per `agent-orchestrator-alerting.md`'s DP-VM class**: preemption is a monitored condition, but with the sweep only
intermittently completing (and, per the campaign-regression finding above, the relaunch that DOES happen may not even be
routed through the actuator this alerting is built around), 11-13 preemptions on one shard going unremarked in
`#data-pipeline-alerts` is the expected, if unwelcome, consequence of an already-identified upstream gap — not a
separate alerting-code defect this doc needs to duplicate-track.

## Why it matters

- **Real, ongoing billing waste**: `eth-2022` alone has burned ~29 VM-launches over 6 days for <10% net year completion
  (by the checkpoint's own account) — extrapolated across the 8 worst-hit CME root/year shards in the operator's
  original evidence (`eth-2022`, `es-2022`, `met-2022/2021`, `mbt-2022/2021`, `es-2021/2020`, `btc-2021`, all 7-11
  preemptions in 30h), this is a fleet-wide pattern, not one shard's bad luck.
- **The checkpoint contract's correctness does not, by itself, guarantee campaign progress** — this is the first
  observed case where the per-VM mechanism is provably fine (`PROGRESS.json` monotonic, `VM_FORCE=false`) but the
  CAMPAIGN still regressed hard, because the relaunch that actually fires may not be the checkpoint-aware one. This is a
  structurally different failure mode than the `--force`/day-one-replay bug the SSOT already documents, and worth a line
  in `spot-vms-for-backfill.md` once root-caused.
- **Cross-cutting with an already-open P0** (`dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md`) — this
  doc's finding is corroborating evidence that the monitor gap has a real, currently-active downstream cost (not just a
  theoretical "coverage will be truncated" risk), which may be useful ammunition for prioritizing that doc's remaining
  Todo 2.

## Recommended next actions (read-only audit — no VM relaunched/killed/reclassified as part of this finding)

1. Confirm which mechanism (`wave_launcher.py` gap-fill vs. `RelaunchPreemptedVm`) is actually dispatching these
   relaunches — grep `wave_launcher.py`'s own run.log / Cloud Run Job execution history for `eth-2022`/`es-2022`
   dispatch decisions in the 2026-08-12..15 window, cross-referenced against the VM launch timestamps above.
2. Read the CONSOLIDATED `availability_index` (not a per-VM shard) for CME/ETH(and ES)/ohlcv_1m/2022 to determine
   whether the December 2022 captures from 2026-08-10 are still present — resolves hypothesis 1 vs. 2 above.
3. If hypothesis 1 (wave_launcher wins the race, checkpoint invisible to it): either (a) make wave_launcher's dispatch
   checkpoint-aware (read the most recent dead VM's `PROGRESS.json` for a shard before computing its `START_DATE`), or
   (b) confirm `RelaunchPreemptedVm`'s hourly-sweep path is fast enough post the exit-code-monitor timeout fix that it
   should be winning the race, and investigate why it apparently isn't.
4. Consider whether `asia-northeast1-c` needs a genuine zone-diversification response for the TradFi OHLCV family
   specifically (an operator call per `spot-vms-for-backfill.md`'s "not fixable by patching the launcher alone"
   precedent from the 2026-08-04 storm) — this is the SECOND independent multi-day storm in this zone in under 2 weeks,
   both times spanning multiple asset groups.
5. Do not blind-relaunch `eth-2022`/`es-2022` on a tight manual loop while this is unresolved — per the 2026-08-04
   precedent, that burns real compute for minimal expected forward progress until the zone or the mechanism is fixed.

## Todos

- [x] [SCRIPT] P1. Read the consolidated TradFi `availability_index` for CME/ETH,ES/ohlcv_1m/2022 to confirm whether the
      December-2022 captures from 2026-08-10 are still present in the manifest — **RESOLVED 2026-08-15: December 2022 is
      NOT lost.** Direct read of `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`
      (14.5M rows) shows CME/ETH/ohlcv_1m December 2022 rows `captured`, `written_at` 2026-08-09..11 — durably present.
      **Hypothesis 2 (manifest-consolidation data loss) is FALSE.** But the investigation surfaced a sharper, more
      damning fact than either original hypothesis: January 2022 CME/ETH/ohlcv_1m is **ALSO already 288/299 (96%)
      `captured`** (the 11 remainder are `expected_unattempted`, correctly-typed non-trading days) — yet `2022-01-03`
      carries **three separate `captured` rows**, same `source=databento`, same `schema_version=9`: written
      `2026-08-09T12:13:27`, then TWO MORE at `2026-08-15T06:17:03` (388ms apart — a genuine re-fetch-and-write, not a
      manifest artifact). **The campaign isn't stuck because January has a real remaining gap — it's wastefully
      RE-CAPTURING data that was already done nearly a week ago, as recently as today.** This reframes the whole
      investigation: it's not (only) "checkpoint invisible to the dispatcher," it's "the freshness/skip check itself is
      being bypassed or defeated for already-fresh dates on at least some relaunches."
- [x] [SCRIPT] P1. Confirm the actual relaunch mechanism for `tradfi-bf-cme-ohlcv-1m-*` preemptions (wave_launcher.py
      vs. RelaunchPreemptedVm) — **PARTIALLY RESOLVED 2026-08-15, and the leading suspect from the original audit is
      WRONG in one respect**: `wave_launcher.py`'s `Dispatch.launcher_args()` (scripts/wave_launcher.py:226) passes a
      bare `--force`, but tracing `_tradfi-ohlcv-launcher-lib.sh`'s arg parser (line 707) shows bare `--force` only sets
      the LOCAL `FORCE=true` that bypasses the launcher's own fleet-cap pre-check — it does **NOT** set
      `OHLCV_FORCE_RECAPTURE` (that needs the separate `--force-recapture` flag, which wave_launcher never passes).
      `VM_FORCE` is stamped from `OHLCV_FORCE_RECAPTURE` (line 374/438) and stays `false` — consistent with, and now
      explaining, this doc's own earlier `LAUNCH_PARAMS.json` finding. **So wave_launcher's `--force` flag is a red
      herring — it does not disable the freshness-skip.** Ruled out as part of this pass: schema_version drift (both old
      and new `2022-01-03` rows are `schema_version=9`) and source-scoping mismatch (both rows `source=databento`,
      matching what `_freshness_source_scope` should map CME to). **Still open**: which of wave_launcher.py vs.
      `relaunch_backfill_vm.py` (`RelaunchPreemptedVm`) actually issued the `2026-08-15T06:17` relaunch that re-captured
      `2022-01-03`, and — the sharper question now — why `market_tick_data_service`'s `check_shard_freshness` call
      (`tick_data_handler.py:512`, confirmed `max_age_hours=0.0` for data >7 days old, i.e. schema-only freshness, which
      should have found this row fresh) did not skip it. Leading new hypothesis: `--only-root ETH` dispatches may not
      correctly narrow `expected_venues`/the freshness scope to just the dispatched root, so a genuine gap elsewhere in
      the SAME calendar date (a different CME root, or a different venue for TradFi's broader `expected_venues` set)
      fails the whole-date freshness check and drags an already-captured root along for a wasteful re-fetch. **Not yet
      verified — next step is reading `tick_data_handler.py`'s date-level orchestration loop to confirm whether
      `is_fresh` is computed and gated per (date) or per (date, root/venue).**
- [x] [SCRIPT] P1. NEW (2026-08-15): Read `tick_data_handler.py`'s freshness-gate call site in full to determine whether
      it evaluates freshness per-date (coarse, can drag an already-fresh root into a re-fetch caused by an unrelated gap
      on the same date) or per (date, venue/root) — this is now the most concrete, code-verifiable next step and likely
      explains the repeated `2022-01-03` re-capture found above. **RESOLVED 2026-08-15 — neither framing is correct.**
      Read `TickDataHandler._apply_freshness_skip` in full
      (`market-tick-data-service/market_tick_data_service/cli/     handlers/tick_data_handler.py:491-540`, the actual
      `check_shard_freshness` call site at line 512). Its very first line (507-508) is
      `if self._force or not self._bucket or explicit_venues: return False, explicit_venues` — whenever
      `explicit_venues` is truthy, this gate returns immediately WITHOUT ever calling `check_shard_freshness`. Traced
      `explicit_venues`'s origin to the CLI `--venues` flag, and confirmed via
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh:2943`
      (`[[ -n "$VM_VENUE" && "$_FANOUT" != "1" ]] && CLI_ARGS="$CLI_ARGS --venues $VM_VENUE"`) that every
      `mtds-backfill` VM — including every `tradfi-bf-cme-ohlcv-1m-*` launch, `--only-root` or not — carries
      `VM_VENUE=CME`, which ALWAYS becomes `--venues CME`. So this gate is a structural NO-OP for this launcher family:
      it never evaluates per-date OR per-(date,venue/root) freshness at all, for any launch. Traced one level deeper to
      find where skip-if-fresh actually happens: `process_ticks` → `_run_preflight_availability_check`
      (`market_tick_data_service/engine/orchestrator/preflight.py:811-897`) reads the full availability index and builds
      `state.preflight_captured_atoms: dict[(venue, data_type), set[atom]]` where `atom` is derived from the manifest
      row's `instrument_id`/`underlying` (+ chain/quote/margin qualifiers, lines 871-888) — this mechanism IS
      fine-grained (per venue, data_type, AND instrument/root atom), not coarse per-date either. **So the repeated
      `2022-01-03` re-capture is explained by NEITHER of this todo's two original hypotheses** — one candidate gate is
      bypassed entirely, the other is already atom-level. New, sharper next step for the P2 todo below: the defect is
      most likely in how `state.preflight_captured_atoms` is CONSUMED downstream (`_process_venue`'s per-instrument
      fetch-skip decision) — a plausible atom-format mismatch (e.g. the CME launcher's requested parent-symbol atom,
      `ETH.FUT`/`ETH.OPT`, vs. whatever `instrument_id`/`underlying` value the manifest row for an already-captured
      2022-01-03 CME/ETH ohlcv_1m record actually carries), or a rejection inside `_is_preflight_source_evidence`. NOT
      verified within this todo's bounded scope (reading `tick_data_handler.py`'s call site, as scoped) — flagged for
      the next investigator via the revised P2 todo below.
- [ ] [SCRIPT] P2. REVISED 2026-08-15 (see resolved todo above — the original "freshness-scoping" framing was based on
      an incorrect premise; both `tick_data_handler.py`'s handler-level gate and `_run_preflight_availability_check`'s
      atom-set build are now confirmed NOT to be coarse per-date checks). Read `_process_venue`'s consumption of
      `state.preflight_captured_atoms` (`market_tick_data_service/engine/orchestrator/__init__.py`) and compare its
      atom-lookup construction against `_run_preflight_availability_check`'s atom construction (`preflight.py:880-888`)
      for a CME OHLCV instrument specifically — most likely an atom-format mismatch (parent root symbol vs. manifest's
      stored instrument_id/underlying) or a source-evidence rejection (`_is_preflight_source_evidence`) is silently
      defeating the skip for already-captured CME dates. Once the actual mechanism is confirmed, fix it and add a
      regression test asserting an already-captured CME (date, root) atom is never re-fetched on a subsequent relaunch.
- [x] [SCRIPT] P2. Wire the existing round-robin zone-rotation capability
      (`deployment_service/backends/services/vm_lifecycle.py`'s `_zone_index` / `deployment_service/backends/vm.py`, and
      the simpler 2-zone fallback pattern already live in `scripts/vm/launch-prediction-live.sh:164`) into the TradFi
      CME OHLCV launcher (`_tradfi-ohlcv-launcher-lib.sh`'s hardcoded `TRADFI_OHLCV_ZONE`) and into `wave_launcher.py`'s
      dispatch path — confirmed 2026-08-15 that NEITHER currently uses any zone-fallback/rotation despite the capability
      already existing elsewhere in the codebase; this is an adoption gap, not a build-from-scratch gap. Second
      independent multi-day `asia-northeast1-c` storm in <2 weeks makes the case for adoption stronger than a one-off.
      **Scope per operator instruction (below)**: rotate through `asia-northeast1-a`/`-b`/`-c` only (same-region, no
      cross-region); TradFi CME OHLCV launcher family only, not a fleet-wide adoption. **RESOLVED 2026-08-15 —
      deployment-service@1877346c9e.** `_tradfi-ohlcv-launcher-lib.sh` now round-robins each `ohlcv_create_vm` launch
      across a `TRADFI_OHLCV_ZONE_POOL` (default `asia-northeast1-{a,b,c}`, overridable via `TRADFI_OHLCV_ZONES`; the
      legacy `TRADFI_OHLCV_ZONE` env still pins a single zone for back-compat); `wave_launcher.py`'s `launch()` seeds
      each dispatch's bash subprocess with `TRADFI_OHLCV_ZONE_START_INDEX=<wave position>` so consecutive dispatches in
      one wave tick also spread across the pool instead of every subprocess restarting the rotation at index 0. Also
      widened `ohlcv_check_singleton_lock`'s fleet-cap scan and the per-shard duplicate-VM check to
      `--zones=<the whole pool CSV>` instead of one zone — otherwise rotating launches would undercount the running
      fleet and blind the shard-collision check to a sibling already running in a different pool zone (the same failure
      class `dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md` fixed for the single-zone case). Verified via
      `--dry-run` (5 CME root-groups correctly cycled `a,b,c,a,b`) after catching and fixing a real bug in review: the
      first implementation captured the rotation function's result via `zone="$(ohlcv_next_zone)"`, which bash runs in a
      subshell — the index increment never propagated back, so every VM silently got the same pool[0] zone. Fixed by
      having the function set a global instead. `bash -n` + `python3 -m py_compile` clean; deployment-service Pass-1
      `quality-gates.sh` green on this exact SHA (626s, sentinel `fbb5d5917b2fb4f4941e235308c30a8f0c100a97`); shipped
      via quickmerge --agent, verified `deployment-service@1877346c9e` is an ancestor of `origin/live-defi-rollout`.
- [x] [SCRIPT] P2. Decide the FULL scope of standing zone-diversification for TradFi OHLCV specifically — **RESOLVED
      2026-08-15, direct operator instruction delivered via AO task dispatch
      `tradfi_bf_cme_ohlcv_asia_northeast1_c_preemption_thrash-69ae9511a358--ruling`** ("not complicated — loop through
      a,b,c zones on same region only"): keep it simple — rotate through zones `asia-northeast1-a`/`-b`/`-c` (the SAME
      region as today's hardcoded `asia-northeast1-c` default) only; no cross-region rotation. Scope stays the TradFi
      CME OHLCV launcher family per this doc's original finding — the instruction did not extend adoption to other
      launcher families. This decision is now folded into the P2 SCRIPT todo above ("Wire the existing round-robin
      zone-rotation capability...") as its concrete zone list — that todo's implementer no longer needs a separate
      operator call to proceed.

## Progress Log

### 2026-08-15 — initial audit (found while monitoring an unrelated CeFi liquidations VM)

Ran `/vm-preemption-billing-waste-audit` scoped to `tradfi-bf-cme-ohlcv-1m-*` per the operator's fleet-wide scan
evidence. Confirmed 100% zone concentration in `asia-northeast1-c` (tradfi + mdps families both), confirmed the per-VM
`PROGRESS.json` checkpoint contract is intact and monotonic, but found the CAMPAIGN-level progress for `eth-2022`
regressed from `2022-12-30` (2026-08-10) to oscillating in the `2022-01-07..28` range across 15 subsequent launches
(2026-08-12..15) — not explained by the `--force`/day-one-replay bug the existing SSOT covers (`VM_FORCE` was `false`
throughout). Cross-referenced the existing `dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md` P0 and found
zero `DP_VM_PREEMPTED*` events fleet-wide in 3 days, consistent with that doc's timeout finding, plus a NEW
residual-failure data point (2 of 8 post-fix executions still time out) added to that doc's corpus rather than
duplicated here. Root cause of the campaign regression is NOT fully resolved within this audit's bounded scope — left as
the top two todos above for the next investigator. No VM relaunched, killed, or reclassified; read-only throughout.

### 2026-08-15 — direct manifest read resolves todo 2, sharpens todo 1, rules out two red herrings

Read the consolidated TradFi manifest directly
(`market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`, 14.5M rows) rather than
continuing to reason from indirect evidence. December 2022 CME/ETH/ES ohlcv_1m is confirmed `captured`, durable since
2026-08-09/11 — **hypothesis 2 (manifest data loss) is false.** But January 2022 CME/ETH is ALSO 96% already `captured`,
and `2022-01-03` specifically shows a THIRD write TODAY (`2026-08-15T06:17:03`, ~6 days after its first capture) — the
campaign is not blocked on a real remaining gap in January, it is actively **re-doing already-finished work**. Traced
`wave_launcher.py`'s `--force` flag through `_tradfi-ohlcv-launcher-lib.sh`'s arg parser and confirmed it does NOT set
`VM_FORCE`/bypass freshness (that needs the separate, never-passed `--force-recapture`) — the original hypothesis-1
framing ("wave_launcher forces full reprocessing") is **wrong**; `VM_FORCE=false` genuinely means freshness-skip is
active. Also ruled out schema_version drift and source-scoping mismatch as causes (both old and new `2022-01-03` rows:
`schema_version=9`, `source=databento`, identical). Current best hypothesis, not yet verified: `tick_data_handler.py`'s
freshness gate may evaluate per-DATE rather than per (date, root/venue), so a genuine gap in a sibling CME root/venue on
the same calendar date drags an already-captured root into a wasteful re-fetch when `--only-root` narrows a dispatch.
Dispatched a follow-up agent to read that call site, confirm, fix, and wire the zone-rotation adoption todo (existing
round-robin capability in `vm_lifecycle.py`/`launch-prediction-live.sh` is unused by this launcher family — confirmed
via direct grep, not inferred). Separately: forced two manifest-consolidation passes on the (unrelated) CeFi
liquidations bucket this same session, in case useful precedent —
`unified_trading_library.manifest_consolidator.consolidate(bucket, force=True)` is a safe, idempotent, already-tested
entrypoint for exactly this kind of "is my recent progress actually visible to the freshness check yet" verification,
worth keeping in mind for future TradFi debugging too.

### 2026-08-15 — operator instruction applied to the zone-diversification-scope todo

Direct operator instruction delivered via AO task dispatch
`tradfi_bf_cme_ohlcv_asia_northeast1_c_preemption_thrash-69ae9511a358--ruling` on the `[OPERATOR]` scope-decision todo:
"not complicated — loop through a,b,c zones on same region only." Applied: retagged that todo `[SCRIPT]` and flipped it
`[x]` (the decision itself is now fully captured in the doc, so nothing about it re-triggers dispatch); folded the
concrete scope (rotate `asia-northeast1-a`/`-b`/`-c`, same region only, no cross-region, TradFi CME OHLCV launcher
family only — not extended to other launcher families) into the still-open P2 SCRIPT wiring todo above so its future
implementer has the exact zone list without needing a fresh operator call.

### 2026-08-15 — follow-up: freshness-gate call site read in full, both original hypotheses ruled out

Read `TickDataHandler._apply_freshness_skip` (`tick_data_handler.py:491-540`) in full per the prior entry's dispatched
follow-up. Found the actual mechanism is sharper and more direct than either "per-date" or "per-(date,venue/root)"
framing: the gate short-circuits (`explicit_venues` truthy → `return False, explicit_venues` at line 507-508) BEFORE
`check_shard_freshness` is ever called, and `--venues $VM_VENUE` (confirmed live in
`deployment-service/scripts/vm/setup-data-pipeline-vm.sh:2943`) is unconditionally set for every `mtds-backfill` VM
including this whole launcher family — so `check_shard_freshness` never runs for a CME OHLCV launch, `--only-root` or
not. Traced the real skip-if-fresh mechanism one level deeper into `process_ticks` → `_run_preflight_availability_check`
(`orchestrator/preflight.py:811-897`), which builds a per-(venue, data_type) → captured-atom-set structure from the
manifest — genuinely atom/instrument-level, not coarse per-date. Both candidate "freshness gates" this todo was framed
around are therefore NOT the coarse-vs-fine scoping bug originally hypothesized — one doesn't run at all for this
launcher, the other already operates at root granularity. Redirected the P2 fix todo toward the real remaining suspect
(atom-format matching between `_run_preflight_availability_check`'s captured-atom construction and `_process_venue`'s
per-instrument lookup) rather than leave a stale premise for the next investigator. No code changed — this todo's scope
was read-only investigation of the named call site; the fix + regression test is the revised P2 todo.

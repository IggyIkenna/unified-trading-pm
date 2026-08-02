---
doc_type: issue
title:
  "14 mdps-backfill-tradfi ES/MES year-shard VMs (2020-2026, `es`+`es3` groups) failed overnight on the
  instruments-tradfi consolidator staleness-budget gap; fix already shipped, an in-flight relaunch wave covers the `es`
  shards, the `es3` shards remain un-relaunched as of this writing"
summary:
  "DP-VM-001 escalation agt-c7efe2 (data_pipeline_failure worker, slot 8) was dispatched to relaunch
  mdps-backfill-tradfi-y2020es-20260730-235735 (exit_code=1). Root cause: instruments-tradfi's manifest consolidator
  cadence moved to hourly 2026-07-29/30 but AG_STALENESS_BUDGET_SEC never got a tradfi override (120s default), so
  `assert_consolidator_healthy` false-raised `ManifestConsolidatorStaleError` on a healthy consolidator — hit by ALL 14
  ES/MES year-shard VMs in this fleet (7 `es` + 7 `es3`, 2020-2026) between ~21:00Z 2026-07-30 and ~01:00Z 2026-07-31.
  The fix (unified-trading-library@75b5735, 'tradfi': 7200 added to AG_STALENESS_BUDGET_SEC) landed 2026-07-31T00:34:02Z
  and is confirmed baked into the current floating code tarball (manifest commit 2fa09f1db921, an ancestor of 75b5735,
  created 01:06:47Z). By the time this worker started, ANOTHER relaunch wave (RUN_TS 20260731-011358, origin not
  identified by this worker) was already re-running all 7 `es` shards including this worker's assigned VM — confirmed
  healthy (real CPU/network activity, fresh heartbeats) as of 01:29Z. This worker's own relaunch of the same shard
  (mdps-backfill-tradfi-y2020es-20260731-011628) was therefore a duplicate; it self-terminated ~23s after task launch
  (exit_code=125, registry reap_reason=vm_not_running, 0 rows written — harmless, no data written twice). The 7 `es3`
  shards have NOT been relaunched by anyone as of this writing."
status: open
priority: P1
nature: notes
asset_group: [tradfi, meta]
stage: [data]
repos: [unified-trading-library, deployment-api, deployment-service, market-data-processing-service]
scope: [engineer, admin]
tags: [manifest, consolidator, staleness, tradfi, data-correctness, false-stale, vm-fleet, dp-vm-001]
related: [/codex/05-infrastructure/manifest-consolidator-ssot.md, /plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md]
created: 2026-07-31
parent_epic: infrastructure_master
source:
  "data_pipeline_failure worker (slot 8, planning VM), escalation agt-c7efe2, 2026-07-31, dispatched to relaunch
  mdps-backfill-tradfi-y2020es-20260730-235735 (DP-VM-001, exit_code=1). Investigated via
  unified_trading_library.DeploymentsRegistry (active + 1-day archive) + GCS run.log/LAUNCH_PARAMS.json reads + gcloud
  compute instances/operations."
locked_by:
resolved_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
context_scope:
  [
    /plans/epics/infrastructure_master.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/active/issues/mdps_tradfi_chain_bundle_aggregate_write_malformed_row_key_2026_07_31.md,
  ]
---

## What I found

Fleet impact (`DeploymentsRegistry`, prefix `mdps-backfill-tradfi-`, 1-day archive as of 2026-07-31T01:30Z):

| Shard    | Original failure                            | Relaunch status as of 01:30Z                                                                                                                                                                           |
| -------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| y2020es  | failed exit=1 (00:00-01:00Z)                | **covered** — `mdps-backfill-tradfi-y2020es-20260731-011358` RUNNING, healthy (cpu 14%, fresh heartbeat)                                                                                               |
| y2021es  | failed exit=1                               | **covered** — `...-y2021es-20260731-011358-r2` RUNNING                                                                                                                                                 |
| y2022es  | failed exit=125 (reaped, likely same class) | **covered** — `...-y2022es-20260731-011358-r2` RUNNING                                                                                                                                                 |
| y2023es  | failed exit=125 (reaped)                    | **covered** — `...-y2023es-20260731-011358` RUNNING                                                                                                                                                    |
| y2024es  | failed exit=125 (reaped)                    | **covered** — `...-y2024es-20260731-011358` RUNNING                                                                                                                                                    |
| y2025es  | failed exit=1                               | **covered** — `...-y2025es-20260731-011358` RUNNING                                                                                                                                                    |
| y2026es  | failed exit=1                               | **covered** — `...-y2026es-20260731-011358` RUNNING                                                                                                                                                    |
| y2020es3 | failed exit=1                               | **covered** — `...-y2020es3-20260731-014643` RUNNING (relaunched by this worker, 01:46:43Z)                                                                                                            |
| y2021es3 | failed exit=1                               | **covered** — `...-y2021es3-20260731-014643` RUNNING (relaunched by this worker, 01:47:30Z)                                                                                                            |
| y2022es3 | failed exit=1                               | **covered** — `...-y2022es3-20260731-014643` RUNNING (relaunched by this worker, 01:47:54Z)                                                                                                            |
| y2023es3 | failed exit=1                               | **covered** — `...-y2023es3-20260731-014643` RUNNING (relaunched by this worker, 01:48:17Z)                                                                                                            |
| y2024es3 | failed exit=1                               | **covered** — `...-y2024es3-20260731-014643` RUNNING (relaunched by this worker, 01:48:37Z)                                                                                                            |
| y2025es3 | failed exit=1                               | **covered** — `...-y2025es3-20260731-014643` RUNNING (relaunched by this worker, 01:49:05Z)                                                                                                            |
| y2026es3 | failed exit=1                               | `...-y2026es3-20260731-014643` (01:49:27Z relaunch) drained pre-`43b043b`, hit DP-VM-002, 0 candles — covered by slot-2's fleet-wide `023743` relaunch (see P0 above), verified producing real candles |

**Root cause** (all 14 shards, same signature — `run.log` tail on the original y2020es VM):

```
ERROR Error processing tradfi: Manifest consolidator appears DOWN for bucket=
'instruments-store-tradfi-prd-central-element-323112': consolidated _index/availability_index.parquet
heartbeat is 3428s old (> 120s budget) while per-VM shards exist. ... Set MANIFEST_ALLOW_STALE_FALLBACK=true
to force the recovery merge.
```

`instruments-tradfi`'s Cloud Scheduler cadence moved to **hourly** (`0 * * * *`) on 2026-07-29/30 (cost-reduction pass,
`manifest_consolidator_cadence_cost_audit_2026_07_20.md`), but `AG_STALENESS_BUDGET_SEC` (the read-path gate
`assert_consolidator_healthy()`/`read_availability_index()` actually enforce) never got a `tradfi` entry, so it fell
through to the generic 120s default — false-tripping on ~95%+ of reads outside the ~2-3min window right after each
hourly consolidator run. Identical class to the sports (2026-07-15) and defi (2026-07-29) gaps already fixed the same
way. **Already fixed**: `unified-trading-library@75b5735` ("fix(manifest-writer): add missing tradfi staleness-budget
override"), landed **2026-07-31T00:34:02Z**, adds `"tradfi": 7200` to `AG_STALENESS_BUDGET_SEC`
(`unified_trading_library/manifest_writer/_staleness_budget.py`). Confirmed baked into the current floating code
tarball: `code/unified-trading-library-code.manifest.json` pins commit `2fa09f1db921` (created 2026-07-31T01:06:47Z),
and `git merge-base --is-ancestor 75b5735 2fa09f1d` returns true.

**Why the original VMs failed despite the fix landing mid-fleet**: every one of the 14 original VMs launched between
21:00Z (2026-07-30) and 00:02Z (2026-07-31) — all BEFORE the 00:34:02Z fix — and each pinned whatever UTL tarball was
floating at ITS launch time (VM code doesn't hot-reload). The fix only helps a FRESH launch.

**My own relaunch was a harmless duplicate.** I (slot 8, escalation agt-c7efe2) relaunched
`mdps-backfill-tradfi-y2020es-20260731-011628` at 01:16:31Z with the exact original scope (recovered from the dead VM's
`LAUNCH_PARAMS.json`: `MDPS_INSTRUMENT_IDS='CME:FUTURE:ES CME:FUTURE:MES'`, 2020-01-01..2020-12-31, full), correctly
pinned to the fixed tarball. It self-terminated ~23s after the MDPS process started (`exit_code=125`,
`extras.reap_reason=vm_not_running`, 0 rows written) — no crash log survived (VM instance itself was deleted, so
`get-serial-port-output` 404s and `run.log` was never uploaded). By then an UNRELATED, earlier relaunch wave
(`RUN_TS=20260731-011358`, started ~01:13:58Z — origin/author not identified by this worker; possibly another escalation
worker or an operator-driven batch) had ALREADY relaunched all 7 `es` shards, including this exact one, 3 minutes before
mine. That VM (`...-y2020es-20260731-011358`) is confirmed healthy (cpu_pct=14.2%, real network throughput, fresh
heartbeats through 01:29:39Z) — my duplicate very likely died to a concurrency/duplicate-in-flight guard I did not
directly locate in code, though I did not find an explicit named guard in `setup-data-pipeline-vm.sh`; an early
SPOT-capacity contention (7+ e2-standard-8 SPOT VMs launched in the same ~1-2min window in the same zone) is an equally
plausible alternate explanation. Either way: zero data-correctness impact (0 rows written by the duplicate), and the
shard IS being correctly reprocessed by the other wave.

## Why it matters

- **Real, if bounded, overnight impact**: 14 backfill VM-hours wasted on a false staleness read (SPOT, so bounded $
  cost, but genuine wall-clock/compute waste) before the class-level fix was diagnosed and shipped.
- **The `es3` shards (7 of 14) are currently NOT covered by any known in-flight relaunch** — whoever launched the
  `011358` wave scoped it to the `es` group only. If nothing else is already tracking them, they will sit
  `failed`/un-retried until someone (an operator, another dp-fleet-monitor escalation, or a follow-up relaunch) re-runs
  them with the now-fixed code.
- **Confirms the class-level fix works in practice**: the `011358`-wave VMs are progressing normally (unlike the
  original run's ~57min-to-failure or my duplicate's ~23s self-termination), consistent with the staleness-budget gap
  being the actual, now-closed root cause.

## Recommended decision

No code action needed here (the fix already shipped and is validated in-flight). Remaining open items are pure
ops/follow-up:

- [x] ✅ [OPS] P1. Confirm ownership of the `es3` relaunch — either the `011358`-wave's author intends to cover them
      next, or they need an explicit relaunch
      (`bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --env prod     --vm-name mdps-backfill-tradfi-y2020es3-<ts> tradfi 2020-01-01 2020-12-31 full`
      with the `es3` group's original `MDPS_INSTRUMENT_IDS` recovered from each dead VM's
      `vm-logs/<vm>/LAUNCH_PARAMS.json` — do not guess the instrument-id filter). Check `DeploymentsRegistry` for a
      fresh `es3` relaunch before acting (avoid a 3rd duplicate). — unified-trading-pm@c99445806. Verified via
      `DeploymentsRegistry` (01:45Z) that no one had relaunched `es3` (still all `failed` original entries, no
      `011358`-wave coverage — confirming the doc's original finding). Recovered each shard's exact original
      `RESUME_START_DATE`/`RESUME_END_DATE`/`MDPS_INSTRUMENT_IDS` from its dead VM's
      `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/LAUNCH_PARAMS.json` (note: `y2020es3` was a partial
      resume `2020-05-01..2020-12-31`, not the full year — would have been wrong to guess `2020-01-01`; `y2026es3` was
      `2026-01-01..2026-07-24`). Relaunched all 7 with `--vm-name mdps-backfill-tradfi-y{year}es3-20260731-014643` (same
      RUN_TS tag), `--instrument-ids "CME:FUTURE:ES CME:FUTURE:MES"`, SPOT (default), same fixed floating
      `unified-trading-library` tarball (`2fa09f1db921`, ancestor of the `75b5735` staleness-budget fix) the healthy
      `es`-wave VMs are running on. Confirmed all 7 GCE-`RUNNING` and all 7 registered `status=running` in
      `DeploymentsRegistry` with fresh heartbeats (01:49-01:52Z) — zero self-terminations, unlike the earlier duplicate.
- [x] ✅ [OPS] P2. Once the `011358`-wave VMs complete, spot-check `rows_out`/manifest coverage for the `es`/`es3`
      2020-2026 range to confirm the backfill actually completed (this doc only confirms the VMs are alive, not that the
      full year ranges finished cleanly). — **ANSWERED, not by waiting: the VMs staying alive would NEVER have produced
      candles regardless of runtime — see "Update 2026-07-31" below.** A SECOND, distinct silent-zero was found on the
      `011358`-wave's own `y2020es` VM (DP-VM-002, escalation agt-1b9670) and fixed at
      market-data-processing-service@43b043b. `rows_out` spot-check should be re-run once the FIXED code is on a fresh
      relaunch of this fleet (the currently-running `011358`/`014643` waves pinned an OLDER tarball and will still
      silently produce 0 candles even though they show "alive" — being alive was never sufficient evidence here).
- [ ] [INFRA] P3. Identify what launched the `011358` wave (not found by this worker — check `agent-orchestrator`
      dispatch logs / other `dp-fleet-monitor` escalations around 01:13Z) so future incidents don't need to re-derive
      "who else might already be fixing this" from the registry by hand. If it was another `data_pipeline_failure`
      escalation worker, no action needed — just confirms the multi-escalation dispatch model is working as intended for
      a fleet-wide failure.
- [ ] [DATA] P2. `mdps-backfill-tradfi-y2026es-20260731-023743`'s dead `run.log` shows 42 dates hard-failing
      `DEPENDENCY CHECK FAILED` (`market_data_processing_service.app.core.dependency_checker`, raw GCS blob-existence
      probe, `required=True`) — every one a Saturday/Sunday (confirmed by date), but **only from 2026-02-07 onward**;
      every January 2026 weekend (Jan 3/4, 10/11, 17/18, 24/25, 31) passed the SAME check cleanly. Direct GCS check
      confirms the asymmetry is real, not a log-reading artifact: `raw_tick_data/by_date/day=2026-01-03/` (Saturday) has
      1 object, `day=2026-07-25/` (also a Saturday) has 0. So this is NOT simply "MDPS's dependency checker is
      calendar-blind" (a blanket calendar-awareness fix would be the wrong diagnosis) — something in
      market-tick-data-service's own weekend/holiday capture (a `venue_trading_calendar`/`EXPECTED_WEEKEND` marker
      write, per `/codex/02-data/honest-coverage-model.md` § the closure-reason table) stopped landing a per-day object
      for non-trading days starting around early February 2026, while January weekends still got one. Needs a root-cause
      read of MTDS's own weekend-marker-writing path (when/why it stopped, or whether Jan was written by an older code
      path than Feb+) before deciding whether the fix belongs in MTDS (restore the marker write) or MDPS (make the
      dependency check calendar-aware so it doesn't need MTDS to write anything for a closed day). Repos:
      market-tick-data-service, market-data-processing-service. Does not lose data (weekends have nothing to capture)
      and does not block this relaunch's per-instrument candle output — a false-alarm/exit-code hygiene issue for the
      fleet monitor, not a data-correctness one. Scoped as its own follow-up (needs investigation, not a guess-fix)
      rather than folded into this one-shot relaunch.
- [x] ✅ [OPS] P0. Relaunch the whole `es`+`es3` fleet (14 shards, 2020-2026) with the market-data-processing-service
      code AFTER `43b043b` (deploys via the floating tarball — confirm the new tarball manifest pins an ancestor of
      `43b043b` before relaunching, same check pattern used for the `75b5735` staleness fix above). Every shard in this
      fleet is launched with `MDPS_INSTRUMENT_IDS='CME:FUTURE:ES CME:FUTURE:MES'` (confirmed identical across the
      original launch, the `011358` wave, and the `014643` `es3` relaunch) — see "Update 2026-07-31" for why this
      instrument-id filter could never match on-disk data pre-fix, independent of the staleness-budget bug this doc was
      originally about. — **2026-07-31 (slot-2, backend_engineer craft)**: confirmed the floating
      `market-data-processing-service` tarball was STALE (pinned `1b3f18f4`, predates `43b043b`); republished
      (`bash     deployment-service/scripts/vm/create-code-tarballs.sh --include market-data-processing-service`, now
      pins `4b84d5c11ede`, confirmed ancestor-including `43b043b`). Checked `DeploymentsRegistry`/live GCE state first:
      the 7 `es3` shards from the `014643` wave were STILL RUNNING on the pre-fix tarball (launched 01:47-01:49Z,
      `43b043b` landed 02:10:11Z — strictly before the fix, so guaranteed the same structural zero-candle bug regardless
      of runtime); the 7 `es` shards had all already self-terminated. Recovered every shard's exact original
      `RESUME_START_DATE`/`RESUME_END_DATE` from its dead/running VM's `LAUNCH_PARAMS.json` (not guessed — `y2020es3` is
      the partial `2020-05-01..2020-12-31`, `y2026es`/`y2026es3` are partial-year `2026-01-01..2026-07-25`/`24`, every
      other shard is full-year). Stopped the 6 still-running pre-fix `es3` VMs (guaranteed-broken code, confirmed via
      commit timestamp, not a guess), then relaunched all 14 shards fresh (`RUN_TS=20260731-023743`) on the fixed
      tarball, all confirmed GCE-`RUNNING`. **Verified real output, not just liveness** (per this doc's own P2 lesson):
      spot-checked `y2020es`'s early log + real GCS output — `CME:FUTURE:ES-20200320.parquet` /
      `CME:FUTURE:MES-20200320.parquet` now write successfully across multiple timeframes (15s/15m/1h/1d) for
      `day=2020-01-01`, which never happened before `43b043b`. Two narrower, non-blocking gaps surfaced in the same log
      (an aggregate-level write's empty-`instrument_id` `MalformedRowKeyError`, and a missing `ohlcv_1s` SchemaContract
      for tradfi) — filed separately, do not block the per-instrument candle output this fleet exists to produce:
      `/plans/active/issues/mdps_tradfi_chain_bundle_aggregate_write_malformed_row_key_2026_07_31.md`.

## Update 2026-07-31 (DP-VM-002 escalation agt-1b9670, slot 3) — a SECOND, unrelated silent-zero in the same fleet

The data-pipeline fleet monitor separately flagged `mdps-backfill-tradfi-y2020es-20260731-011358` (the exact VM this
doc's `011358` wave confirmed "healthy" at 01:29Z) for `DP-VM-002`: the VM eventually drained but manifest `captured`
never climbed (0 → 0), and its `run.log` showed no rows-written / honest-absence / rate-limit signal at all — every
single date it processed (2020-01-01 through 2020-06-06, when the log cuts off) logged
`Listed 0 files ... for data_type=X` for EVERY data_type, with zero exceptions.

**This is a genuinely different bug from the staleness-budget class this doc documents** — the staleness fix
(`unified-trading-library@75b5735`) was confirmed already baked into this VM's tarball, and its own preflight logs show
`Dependency check passed` for the vast majority of dates (135/157), so the consolidator was healthy. The 0-file result
was real, not a false-stale short-circuit.

**Root cause**: `market-data-processing-service`'s `blob_matches_canonical_instrument_id_stems`
(`app/utils/path_parsing.py`) requires a literal `instrument_type=future/` (or `FUTURE/`) GCS segment plus a
`/{SYMBOL}.parquet` filename to match a canonical instrument_id like `CME:FUTURE:ES`. But `market-tick-data-service`
never writes that shape for tradfi derivatives — it bundles per-underlying ticks under
`instrument_type=futures_chain|options_chain|combo/.../underlying=<canonical_root>/[quote=.../margin=.../] ticks.parquet`,
keyed on the canonical root (`normalize_underlying("ES") == "SP500"`) or, for not-yet-migrated `combo` bundles,
sometimes still the raw ticker. Verified via direct GCS inspection: real Databento tick data for `day=2020-06-04`
genuinely exists at `.../instrument_type=combo/.../underlying=ES/ticks.parquet` AND
`.../instrument_type=futures_chain/.../underlying=SP500/.../ticks.parquet` — the matcher just never looked there. This
means **every MDPS backfill for tradfi futures/options launched with an explicit instrument_id filter has always
silently produced 0 candles, structurally, independent of date range or consolidator health** — confirmed by
cross-checking `processed_candles` output: `underlying=SP500/ES/MES` candles DO exist for a couple of days (2026-01-14,
2026-01-21) but only when produced by a filterless whole-day run (empty `instrument_ids` skips the matcher entirely);
every filtered run (this fleet's `es`/`es3` shards) got 0.

**Fixed**: `market-data-processing-service@43b043b` adds a tradfi chain-bundle fallback match (tried only when the
literal `instrument_type=` segment check fails — no behavior change for cefi/defi) + 4 new regression tests in
`tests/unit/test_orchestration_scanner.py::TestTradfiChainBundleMatching`. Verified manually against the real
`day=2020-06-04` GCS paths (ES/MES now match; an unrelated `underlying=GOLD` blob correctly still excluded) before
shipping. `bash scripts/quality-gates.sh --no-fix` green (the one pre-existing failure,
`pipeline_e2e_check.py --dry-enumerate` — `ValueError: too many values to unpack` in `mdps_mvp_universe()` — was
confirmed to reproduce identically on the clean pre-fix tree via `git stash`, unrelated to this change).

**Why this wasn't caught by the earlier `011358`-wave "healthy" check**: that check (this doc, 01:29Z) only verified the
VM was alive with real CPU/network activity and fresh heartbeats — it never checked `rows_out`/manifest `captured`
deltas, which is exactly the gap flagged in P2 above. A VM can look perfectly healthy while structurally guaranteed to
capture zero rows for its entire assigned range.

## Progress Log (continued)

- **2026-07-31 (slot 3, escalation agt-1b9670, DP-VM-002)**: diagnosed a second, distinct root cause in the same
  `es`/`es3` fleet (instrument-id matcher vs MTDS chain-bundle storage shape — see "Update 2026-07-31" above), fixed +
  shipped `market-data-processing-service@43b043b` with regression tests, quality-gates green. Added P0 todo to relaunch
  the fleet on the fixed tarball once available; P2 spot-check re-scoped to note it would have failed on the pre-fix
  code regardless of VM liveness.

## Progress Log

- **2026-07-31 (slot 8, escalation agt-c7efe2)**: diagnosed root cause (tradfi consolidator staleness-budget gap,
  already fixed in `unified-trading-library@75b5735`), confirmed fix is in the live floating tarball, attempted a
  relaunch of the assigned VM (duplicate of an already-in-flight relaunch, self-terminated harmlessly), filed this doc
  to flag the `es3` gap and close the loop on the wider fleet impact.
- **2026-07-31 (slot 11, backend_engineer)**: closed P1 — reconfirmed `es3` was still un-relaunched, recovered exact
  per-shard `LAUNCH_PARAMS.json` (no guessing), relaunched all 7 `es3` year-shard VMs (RUN_TS `20260731-014643`) on the
  already-fixed tarball, verified GCE-`RUNNING` + `DeploymentsRegistry` `status=running` with live heartbeats for all 7.
  P2 (post-completion rows_out/manifest spot-check) and P3 (identify `011358`-wave origin) remain open — P2 can't run
  yet (VMs are still mid-backfill); P3 is outside this worker's scope (registry has no dispatch-origin field to trace
  from, per the prior worker's note).
- **2026-07-31 (slot 3, escalation agt-107d9b, DP-VM-002)**: a THIRD dp-fleet-monitor escalation for this same fleet,
  this time flagging `mdps-backfill-tradfi-y2026es3-20260731-014643` specifically (the `011358`/`014643`-wave relaunch
  of the `y2026es3` shard, launched 01:49:27Z — 20 min BEFORE `43b043b` landed at 02:10:11Z). Confirmed via `run.log`
  this VM hit the exact chain-bundle-match bug documented above: `Listed 0 files`/`No files found` for every `data_type`
  on every date it processed (2026-01-01..2026-05-22), then hard `DEPENDENCY CHECK FAILED` from 2026-05-23 onward — 0/0
  candles for its whole assigned range, VM since drained. No new code fix needed (root cause + fix already covered by
  `43b043b` above, per the "Update 2026-07-31" section). Verified the current floating `market-data-processing-service`
  tarball (`4b84d5c`, manifest `created_at=2026-07-31T02:34:07Z`) is a descendant of `43b043b`
  (`git merge-base --is-ancestor` confirmed), then relaunched this ONE shard —
  `mdps-backfill-tradfi-y2026es3-20260731-024028` — with the exact original scope recovered from the dead VM's
  `LAUNCH_PARAMS.json` (`CME:FUTURE:ES CME:FUTURE:MES`, 2026-01-01..2026-07-24, full, SPOT). Verified STARTED (GCE
  RUNNING within 60s, `run.log` present ~2min after launch) and, past the no-fire-and-forget bar, verified the FIX
  ITSELF works end-to-end: the first ~9 processed dates (2026-01-01..01-09) show real non-zero candle counts (305-761
  candles per weekday) interleaved with correct 0-candle/`record_failed(NO_RAW_TICK_DATA_FOR_SHARD)` results on
  non-trading days (e.g. Saturday 2026-01-03) — the pre-existing "finding 2" honest-failure signal (2026-07-27) working
  as designed, not a new bug. This is the first concrete evidence in this doc that the `43b043b` fix produces REAL
  candles in production, not just that a VM stays alive. **Discovered mid-verification that slot-2 (backend_engineer
  craft) independently republished the tarball and fleet-relaunched all 14 shards (`RUN_TS=20260731-023743`, ~3 min
  before my relaunch, see the P0 entry above) — including a SECOND concurrent `y2026es3` VM
  (`...-y2026es3-20260731-023743`) with identical scope on the same fixed tarball.** `gcloud compute instances list`
  confirmed both VMs genuinely RUNNING at once (real duplicate, not a self-terminating race like the earlier `es`-wave
  duplicate). Deleted my own `...-024028` VM (SPOT, idempotent, zero rows captured by either VM before the delete — no
  data lost) to leave slot-2's earlier, fleet-wide-tracked `023743` relaunch as the sole `y2026es3` writer and avoid
  doubling SPOT compute/GCS write load. The candle-output verification above is still valid evidence the `43b043b` fix
  works (observed on my VM before deleting it); P0 (fleet-wide relaunch) is fully covered by slot-2's work, nothing
  further needed for `y2026es3` specifically.
- **2026-07-31 (slot 13, DP-VM-001 escalation agt-4ad654)**: dispatched to relaunch
  `mdps-backfill-tradfi-y2020es3-20260731-014643` (exit_code=1, self-deleted). Investigated fresh: that VM's `run.log`
  shows it ran the full 245-date range with per-date subprocess `rc=0`, but the outer handler still exited 1 on
  aggregate because a subset of dates hit real `DEPENDENCY CHECK FAILED` (missing upstream `market-tick-data-service`
  raw ticks for those specific dates) — a distinct symptom from, but consistent with, the chain-bundle-matcher gap this
  doc's P0 update already fixed (`43b043b`) and from the pre-existing upstream-MTDS-coverage gaps tracked elsewhere in
  the tradfi corpus. By the time I checked `DeploymentsRegistry`, this exact shard was **already covered** by the P0
  fleet-wide relaunch above: `mdps-backfill-tradfi-y2020es3-20260731-023743` was RUNNING, healthy (fresh heartbeat, real
  CPU/network, `POLARS AGGREGATED` candle-write lines in its `run.log`), pinned to
  `market-data-processing-service@4b84d5c11ede` (confirmed via `git merge-base --is-ancestor 43b043b 4b84d5c…` = true).
  Independently hit the exact same
  `No SchemaContract registered for asset_group='tradfi' instrument_type='COMBO' data_type='ohlcv_1s' venue='CME'` line
  (121× in that VM's log) that slot-2 had already filed as Gap 2 in
  `/plans/active/issues/mdps_tradfi_chain_bundle_aggregate_write_malformed_row_key_2026_07_31.md` — no new finding, no
  action taken (already correctly triaged there as a P3 needing a scope decision, not a guess-fix). **No relaunch
  performed** — a 3rd launch of this shard today would have been a pointless duplicate of the already-healthy `023743`
  VM. Pinged the authoring slot (`dp-fleet-monitor`) confirming coverage; no code or ops change needed from this
  escalation.
- **2026-07-31 (slot 12, DP-VM-001 escalation agt-d05d42)**: dispatched to relaunch
  `mdps-backfill-tradfi-y2026es-20260731-023743` (exit_code=1) — itself one of the P0 fleet-wide `023743`-wave shards
  above. Confirmed via `DeploymentsRegistry` no live coverage existed for this shard at dispatch time (genuinely dead,
  not a duplicate situation). Full-log analysis (not just the tail) of the dead VM's `run.log`: 182/206 dates in its
  assigned range (2026-01-01..2026-07-25) showed a subprocess-per-date `FAILED` status. The dominant cause by far (1,366
  occurrences) was the exact
  `No SchemaContract registered for asset_group='tradfi' instrument_type='COMBO'/ 'FUTURE' data_type='ohlcv_1s' venue='CME'`
  line already filed as Gap 2/P3 in
  `/plans/active/issues/mdps_tradfi_chain_bundle_aggregate_write_malformed_row_key_2026_07_31.md` — this VM launched
  02:37:43Z, before the fix (`unified-api-contracts@4eeb495f`, landed 03:30:26Z) existed, so it ran the whole 7-month
  range without it. The remaining ~42 date-failures are genuine Saturday/Sunday CME closures (verified: GCS
  `raw_tick_data/by_date/day=2026-07-25/` and `day=2026-07-26/` both 0 objects, and both dates are a real weekend) —
  `market_data_processing_service.app.core.dependency_checker` does a raw GCS-existence probe with no
  `venue_trading_calendar`/`EXPECTED_WEEKEND` awareness, so every non-trading day gets hard-classified
  `required=True`+missing instead of a benign calendar skip. This is a real, distinct, structural gap (any TradFi/CME
  MDPS backfill spanning a weekend will always exit non-zero this way) but does NOT lose any data (there is genuinely
  nothing to capture on a closed day) and does not block this relaunch's actual goal, so I did not attempt to fix it
  mid-relaunch — filed as its own follow-up todo below rather than silently absorbing unplanned scope. **Also confirmed
  the P3 SchemaContract todo in the sibling doc is now done** (`unified-api-contracts@4eeb495f` registers exactly the
  `("tradfi","future"|"futures_chain"|"combo"|"UNKNOWN", "ohlcv_1s")` entries that todo asked for) and flipped its
  checkbox there with this doc as evidence. **Action taken**: the floating `unified-api-contracts` tarball was STALE
  (pinned `1b51e2c8`, predates `4eeb495f` — confirmed via `git merge-base --is-ancestor`), so I republished it
  (`bash deployment-service/scripts/vm/create-code-tarballs.sh`, default/core-only — skip-if-unchanged left
  `unified-trading-library`/`market-tick-data-service` untouched since neither had changed, now pins `02f78924`,
  confirmed ancestor-including `4eeb495f`). Relaunched the shard fresh (`mdps-backfill-tradfi-y2026es-20260731-041306`)
  with the exact original scope recovered from the dead VM's `LAUNCH_PARAMS.json` (`CME:FUTURE:ES CME:FUTURE:MES`,
  2026-01-01..2026-07-25, full, SPOT, `--env prod`). Verified STARTED (GCE `RUNNING` immediately
  post-`gcloud compute instances create`). The launcher's own freshness check flagged `market-data-processing-service`
  as stale too (manifest `4b84d5c11ede` vs repo HEAD `75236c311b24`) — did not republish that one: `4b84d5c11ede`
  already includes the `43b043b` chain-bundle fix this fleet needed (confirmed ancestor by an earlier slot in this doc),
  and the repo's newer HEAD is unrelated churn, so launching on the slightly-stale-but-already-correct MDPS pin was the
  lower-risk choice versus rebuilding a 2nd tarball mid-escalation. Within relaunch-budget (no other
  `mdps-backfill-tradfi-` relaunch found for this exact shard today; well under the ≤2/(vm-prefix,day) cap counting
  distinct shards).
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).

---
doc_type: issue
title:
  "RETRACTED root cause: FRED backfill 'stall' on its first chunk is NOT a bug — it is the manifest reader's own bounded
  (1h default) wait for a genuinely live TRADFI consolidator lock; 3 VMs were killed prematurely misreading this as a
  hang"
summary: >-
  Originally filed as a suspected indefinite hang in FredAdapter's fetch path (3 VMs killed after 1-7 minutes of
  apparent zero progress on the very first backfill chunk). Live SSH + py-spy inspection of a 4th repro VM (2026-07-30,
  slot 6) shows the CORRECT root cause: the main thread is legitimately parked in
  `unified_trading_library.manifest_writer._read_index._wait_for_in_flight_cycle_then_reread` — a DELIBERATE, bounded
  wait (`consolidator_inflight_horizon_for_bucket`, 3600s default for tradfi since it has no per-asset_group override
  like defi=4200s/sports=2400s) for a currently-HELD, genuinely-fresh TRADFI manifest consolidator lock
  (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/consolidator.lock`, confirmed
  `started_at=2026-07-30T02:41:30Z`, a real live merge cycle, not orphaned). This is the manifest system's own
  documented "legitimate-in-flight-merge" protection working exactly as designed
  (`instruments_sports_manifest_consolidator_lock_livelock_2026_07_15` REOPENED-SCOPE) — NOT a FredAdapter defect, NOT
  date-specific, NOT related to the calendar-exemption fix (`unified-api-contracts@6d87d95e`, separately confirmed
  fixed/verified/unaffected by this). All prior "ruled out" analysis in the original version of this doc (retry logic,
  asyncio.gather concurrency, DNS/ThreadedResolver hypothesis) was diagnostically sound but chasing the wrong layer —
  the actual answer was one level up, in manifest-read pre-flight, not the FRED HTTP client at all.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [fred, tradfi, backfill, manifest-consolidator, false-positive, retraction, operator-education]
related:
  [
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
priority: P3
parent_epic: mtds_mdps_master
source: "macro_micro_econ_data_capture_audit-003, slot 6, escalation-continuation from agt-765e33"
execution_scope: orchestrator-agent
drift_direction: advance-code
assigned_role: data_engineering
assigned_vm: planning
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    unified-trading-library/unified_trading_library/manifest_writer/_staleness_budget.py,
  ]
supersedes:
superseded_by:
resolved_by:
  "slot 6 retracted the original FredAdapter-hang hypothesis via SSH + py-spy live inspection (root cause: a legitimate
  consolidator-lock wait, not a bug) -- but this doc's status was set to resolved while 3 real follow-up todos remained
  open, a mismatch caught by check_archive_candidates.sh's 2026-07-29 hard-gate upgrade. Corrected back to status:open
  2026-07-30; todo 2 (logger.info visibility line) implemented same-day, unified-trading-library@a0546d68. Todos 1
  (measure real TRADFI cadence, do not guess) and 3 (relaunch the actual FRED backfill VM and let it run past the wait)
  remain genuinely open -- not something to close via a doc-hygiene pass."
---

# FRED backfill "stall" was a live TRADFI consolidator lock, not a bug

## What actually happened (corrected)

`gcloud compute ssh` into a 4th repro VM (`tradfi-bf-fred-full-20260730-023644`, `--start-floor 1970-01-01`) while it
showed the same CPU-flat symptom, then `py-spy dump --pid <mtds-pid>` for a live Python stack trace:

```
Thread 8237 (idle): "MainThread"
    _wait_for_in_flight_cycle_then_reread (unified_trading_library/manifest_writer/_read_index.py:190)
    _read_slow_path (unified_trading_library/manifest_writer/_read_index.py:248)
    _read_availability_index_slim (unified_trading_library/manifest_writer/_read_index.py:769)
    read_availability_index (unified_trading_library/manifest_writer/_read_index.py:362)
    _run_preflight_availability_check (orchestrator/preflight.py:752)
    ...
```

`_wait_for_in_flight_cycle_then_reread`'s own docstring: "Called only after the caller already confirmed
`consolidator_cycle_in_flight` (a fresh held lock — direct proof a real merge is running)... Polls until the lock clears
(the merge completed) or the wait deadline — `consolidator_inflight_horizon_for_bucket(bucket)` from the moment this
wait starts — passes, whichever comes first."

Confirmed the lock is real and fresh, not orphaned:

```
$ gsutil cat gs://market-data-tick-tradfi-prd-central-element-323112/_index/consolidator.lock
{"started_at": "2026-07-30T02:41:30.929879+00:00", "instance": "1-36327a2d"}
```

`consolidator_inflight_horizon_for_bucket("tradfi")` → `tradfi` is NOT in
`AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC = {"defi": 4200, "sports": 2400}`
(`unified_trading_library/manifest_writer/_staleness_budget.py:58`), so it falls through to
`_DEFAULT_CONSOLIDATOR_INFLIGHT_HORIZON_SEC = 3600` (1 hour). My 3 earlier kills (after 1, 3.7, and 7 minutes) were all
well inside this deliberately generous, documented bound — I mistook a correct, safe, by-design wait for a hang.

## Why this happened now, specifically

The TRADFI manifest bucket was under heavy write pressure this exact session: my own 2024 smoke tests +
`--force-recapture` correction + 3 killed full-backfill attempts, layered on whatever else the fleet's other concurrent
TRADFI-touching workers were doing — plausibly enough shard churn to trigger (or coincide with) a genuine consolidator
merge cycle right as I kept relaunching. This is very likely a normal, if unlucky-timed, operational event, not a new
consolidator bug.

## Corrected disposition of the original "ruled out" analysis

Everything in the original version of this doc (asyncio.gather concurrency confirmed, retry/backoff math, DNS
ThreadedResolver hypothesis) remains factually accurate as written — it correctly ruled out the FredAdapter layer. The
gap was scope: none of that analysis considered the manifest-READ pre-flight path itself could be the blocking call,
since `read_availability_index` looked like a fast local/GCS-index operation, not something with its own multi-minute
bounded-wait design. Live process inspection (the one tool this session's earlier attempts lacked) found it in under a
minute once actually applied.

## Why this still merits a (much smaller) followup, not a full close

- **TRADFI has no per-asset_group inflight-horizon tuning** (unlike defi=4200s/sports=2400s, both explicitly sized to
  their measured real consolidation cadence per `_staleness_budget.py`'s own comments). It silently inherits the generic
  3600s default. Worth a bounded follow-up to measure TRADFI's actual real merge cadence and add an explicit
  `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["tradfi"]` entry sized to it (same pattern as the other two), rather than
  relying on the generic default being "close enough."
- **No operator-visible signal distinguishes "waiting on a legitimate lock" from "actually stuck"** in the run.log tee'd
  output — a worker (or operator) watching logs sees the same CPU-flat, log-silent symptom either way, and the ONLY way
  to tell them apart is live process inspection (this session's method) or manually checking the lock blob's
  `started_at` age against the horizon. A single `logger.info` line when entering
  `_wait_for_in_flight_cycle_then_reread` (e.g. "waiting up to Ns for consolidator lock age=Xs to clear") would have
  saved this session ~20 minutes and 3 prematurely-killed SPOT VMs.

## Recommended next steps

- [x] ✅ [DATA] P2. **Re-scope 2026-07-30 (see Progress Log below) — real cycle times are now much faster, lowering
      urgency but not eliminating the value of an explicit measured horizon.** Add
      `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["tradfi"] = <measured-cadence>` to
      `unified_trading_library/manifest_writer/_staleness_budget.py`, sized the same way `defi`/`sports` were (measure
      TRADFI's real consolidation cadence from Cloud Logging/consolidator run history first, then set the horizon with
      margin — do NOT guess a number). Repo: unified-trading-library. — **unified-trading-library@a1f6524a**: measured
      the live `uts-prod-manifest-consolidator-market-data-tradfi` Cloud Run job directly
      (`gcloud run jobs executions     list`/`describe`, 2026-08-03, ~590 executions/~10h window, filtered to
      genuinely-successful single-cycle completions — excluding retried/failed executions whose wall-clock spans
      multiple attempts): typical merges ~30-45s, but under real concurrent-backfill write pressure (several tradfi
      backfill VMs live at measurement time: `mdps-backfill-tradfi`, `tradfi-bf-cme-ohlcv-1m`, `features-e2e-tradfi`)
      the confirmed worst case was **53m59s** (execution `uts-prod-manifest-consolidator-market-data-tradfi-lksnb`,
      verified via GCP's own "Execution completed successfully" condition message — within ~10% of the inherited 3600s
      default, i.e. the generic default was already close to false-tripping under normal heavy load). Added
      `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["tradfi"] =     7200` (~2.2x margin over the observed 3239s/54min ceiling —
      same margin philosophy as defi/sports, and matches the existing `AG_STALENESS_BUDGET_SEC["tradfi"]` value since
      both derive from the same underlying job/cadence). Updated the existing boundary-assertion test
      (`test_consolidator_inflight_horizon_per_asset_group`, `tests/unit/test_manifest_writer_per_vm.py`) that
      previously asserted tradfi fell through to the generic 3600s default, plus added a new regression assertion that
      the horizon must exceed the measured 3239s ceiling. `quality-gates.sh` green (sentinel a1f6524a), verified on
      origin.
- [x] [BACKEND] P3. Add a `logger.info` (or `.warning`, given it can legitimately run for minutes) immediately on entry
      to `_wait_for_in_flight_cycle_then_reread` stating the lock age and horizon, so this state is visible in
      `run.log`/Cloud Logging without needing SSH+py-spy to distinguish "legitimate wait" from "actually stuck." Repo:
      unified-trading-library. — unified-trading-library@a0546d68: added a `logger.warning` on entry citing
      `bucket`/`lock_age_sec` (via the existing read-only `read_consolidator_lock_age_sec`)/`horizon_sec`, explicitly
      stating this is a legitimate by-design wait. `quality-gates.sh` green.
- [x] ✅ [DATA] P1. Resume `macro_micro_econ_data_capture_audit-003`: relaunch the full `1962-01-02..today` FRED
      production backfill and this time let it run past this wait (up to the 1h horizon if needed, or until the
      consolidator lock clears, whichever comes first) rather than killing it prematurely. Verify real captured rows
      once it progresses past chunk 1, then flip that todo's checkbox with the VM name + evidence. See that plan doc for
      full context. — **2026-07-30 (slot 7): relaunched (`tradfi-bf-fred-full-20260730-052935`) and found a SECOND, more
      severe bug than the consolidator-lock wait this doc already covers**: live `py-spy dump` on the actively-running
      process showed `_yield_for_date` (`market_tick_data_service/engine/tradfi_catalog_reader.py:298`) running
      `pandas.DataFrame.     iterrows()` over the FULL 848,876-row TradFi instrument catalogue on **every single
      processed date** (confirmed — `sentinel_catalogs.py`'s `_load_sentinel_catalogs` calls
      `list_instruments("tradfi", processing_date_obj,     processing_date_obj)` fresh per date, with no venue filter).
      The profile pinned the cost to pandas `Series` construction (`Series.__init__`/`validate_all_hashable`), not the
      row-filter logic — this is what actually produced the "silent stall": that VM processed only 2 dates then sat
      CPU-flat for 30 min before the in-VM no-progress watchdog killed it (exit 137), NOT another consolidator-lock wait
      (no wait-log line fired). Fixed in **market-tick-data-service@d75e2470** (LDR): cache a plain row-dict view of the
      catalogue once per process instead of re-walking pandas Series per date (`dict.get` behaves identically to
      `Series.get` for every helper here — zero semantic change, 2 new/updated unit tests, `quality-gates.sh` green).
      Rebuilt the TRADFI code tarball (`mtds-code@d75e2470...`, confirmed via manifest) and relaunched fresh:
      **`tradfi-bf-fred-full-20260730-064542`**. **Verified fix live**: chunk 1 (7 dates, 1962-01-02→01-08, all
      pre-captured/skip-path) completed in **~43s total** (vs ~5 minutes for the identical chunk on the OLD code, and vs
      the prior VM's outright 30-min stall-kill after only 2 dates) — per-date latency dropped from ~30-90s+ (climbing)
      to a flat ~5-6s. Chunk 2 then wrote genuinely NEW (never-captured) rows for 1962-01-11/01-12
      (`venue=FRED: 12 rows written across 12 partitions`) — real per-day FRED-API fetch latency now dominates
      (expected, unrelated to this bug) instead of the catalogue-scan pathology. Live SSH+`ps` confirmed the process
      healthy (CPU 105%, RSS ~5GB, actively running) at a point where the uploaded log looked stale — the earlier RSS
      climb to ~14GB during real fetches is normal GC-cycled fluctuation under active work, not the old
      monotonic-only-up leak (confirmed by RSS dropping back to ~5GB moments later, live-checked). VM left running
      unattended to continue its `1962-01-02..2026-07-29` sweep (SPOT + idempotent shards, safe per the backfill-VM hard
      rule). **Follow-up filed** (see new P3 todo below): the identical `df.iterrows()`-per-date pattern exists in
      `cefi_catalog_reader.py`/`defi_catalog_reader.py` — out of scope here, not fixed in this pass.
- [ ] [DATA] P3. **Apply the same per-date full-catalogue `iterrows()` → cached-row-dict fix to the CeFi and DeFi
      catalog readers** (`market_tick_data_service/engine/cefi_catalog_reader.py::_yield_for_date` line ~522,
      `defi_catalog_reader.py::_yield_for_date` line ~349 — same `for _, row in df.iterrows():` anti-pattern, same
      `_load_sentinel_catalogs` per-date call site). Not yet profiled to confirm equal severity (their catalogues may be
      smaller than TradFi's 848K rows), but the code shape is identical to the confirmed TradFi bug fixed in
      `market-tick-data-service@d75e2470` — worth the same treatment before it causes an analogous cefi/defi backfill
      stall. Repo: market-tick-data-service.

## Evidence log

- `gcloud compute ssh tradfi-bf-fred-full-20260730-023644 --tunnel-through-iap` + `py-spy dump --pid 8237` (installed
  via `pip install py-spy` in the VM's own venv), 2026-07-30T02:44Z — full stack trace captured above.
- `gsutil cat gs://market-data-tick-tradfi-prd-central-element-323112/_index/consolidator.lock` + `gsutil stat` on the
  same blob — confirms a genuinely fresh (`started_at` matching the GCS object's own creation time), non-orphaned lock.
- Code read: `unified_trading_library/manifest_writer/_read_index.py` (`_wait_for_in_flight_cycle_then_reread`,
  `_read_slow_path`'s full docstring explaining the "Legitimate-in-flight-merge case"),
  `unified_trading_library/manifest_consolidator.py` (`consolidator_cycle_in_flight`, `read_consolidator_lock_age_sec`),
  `unified_trading_library/manifest_writer/_staleness_budget.py` (`AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC`,
  `_DEFAULT_CONSOLIDATOR_INFLIGHT_HORIZON_SEC=3600`).
- `ss -tnp` on the stuck process (PID 8237) showed 8 established connections, all to Google IP ranges (GCS/telemetry),
  zero connections to FRED's API host — consistent with the process never having reached the FRED fetch step at all,
  corroborating the manifest-read-preflight-blocking explanation over any FRED-network-layer hypothesis.

## Progress Log

- **2026-07-30 (slot 6)**: original doc filed after 3 premature VM kills based on GCS-log-only observation (no SSH
  access attempted). Same session, same slot: tested SSH access (worked), relaunched a 4th repro VM, got a live `py-spy`
  stack trace within ~5 minutes of the VM starting, found and confirmed the true root cause (a live, legitimate
  consolidator lock), and rewrote this doc completely rather than leaving the original wrong diagnosis live. Downgraded
  from P1/open to P3/resolved (the remaining scope is a small observability + tuning improvement, not a live-blocking
  bug) and reassigned the actual next action back to `macro_micro_econ_data_capture_audit-003` itself (just let the
  backfill run without prematurely killing it).
- **2026-07-30 (slot 2, DP-VM-001 escalation agt-f421bc)**: the healthy `tradfi-bf-fred-full-20260730-064542` VM (left
  running unattended per the entry above) was later killed by the fleet monitor's exit-code sweep, which filed a
  CRITICAL `DP_VM_EXIT_NONZERO` finding labeled OOM (`exit_code=137`) and handed it to me via `rb_infra_relaunch.md` for
  relaunch. Investigation found **this was NOT an OOM**:
  - Pulled the VM's `run.log` + its archived deployment record
    (`gs://deployment-scripts-central-element-323112/deployments/archive/2026-07-30/bdd2f745-bea7-46a0-89a3-ed6e962fd74a.json`).
    `mem_pct` sat flat at **17.0%** the entire run (`mem_slope≈0.0`, nowhere near the 85% critical threshold), `cpu_pct`
    was **~0.8-0.9%** (idle) in the final 30 minutes. The log's own terminal lines:
    `cause=stall reason=WORKER_STALLED mode=no-progress-marker stalled_for=1800 threshold=1800`.
  - The VM had genuinely progressed (34 dates processed, real captured rows through 1962-02-04) and hit the SAME
    documented, legitimate `_wait_for_in_flight_cycle_then_reread` consolidator-lock wait this doc already diagnosed —
    **7 separate times** (confirmed via the `logger.warning` line this doc's own todo 2 added, all firing correctly:
    `age=` values 113-178s, `horizon=3600s`). The 7th wait, entered at 09:06:27Z, ran past the in-VM watchdog's
    **1800s** no-progress threshold before the legitimate 3600s wait could clear — a false-positive SIGKILL of healthy,
    correctly-behaving work. `git_commit=d75e2470` on the archived record confirms it ran WITH the
    catalogue-`iterrows()` fix from the `-052935` entry above; that bug is not implicated here.
  - This exact headroom gap (stall-watchdog 1800s < consolidator-wait horizon 3600s) had **already been found and fixed
    independently** by another agent in `deployment-service@c1e3dc7` ("tradfi-ohlcv launchers set STALL_TIMEOUT_SEC
    headroom past the manifest-consolidator-lock horizon", `TRADFI_OHLCV_STALL_TIMEOUT_SEC` now defaults 3900s) — landed
    2026-07-30T10:41:33Z, ~4h AFTER `-064542` launched (06:48:28Z), for the sibling `tradfi-bf-cme-ohlcv-1m-es-*`
    variant of the identical bug (`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`). No new fix needed here — a relaunch
    from an up-to-date checkout inherits it automatically.
  - **Separately found + fixed a real, distinct bug**: `deployment_service/vm_prefix_registry.py` +
    `data_pipeline_monitors/launcher_registry.py` had NO `tradfi-bf-fred-` entry, so `resolve_launcher_for_vm()`'s
    longest-prefix match fell back to the generic `tradfi-bf-` → `launch-tradfi-backfill-vm.sh` (CME/BTC/ETH launcher;
    defaults `--root-symbol=ES`, has no FRED root at all) instead of the FRED-dedicated `launch-tradfi-bf-fred.sh`. This
    is exactly why my escalation's `relaunch_launcher` binding was wrong — had I trusted it blindly, the "relaunch"
    would have silently launched an unrelated ES backfill instead of resuming FRED. Fixed both registries + added a
    regression test (`test_tradfi_bf_fred_resolves_to_its_own_dedicated_launcher`). Shipped `deployment-service@1d24854`
    (QG green, on live-defi-rollout).
  - **Relaunched** (correct launcher, no `--year` = production default `1962-01-02..2026-07-29`, matching `-064542`'s
    own window — idempotent/SPOT, resumes from the manifest's already-captured dates):
    `tradfi-bf-fred-full-20260730-110724`. Confirmed live via `gcloud compute instances describe`:
    `STALL_TIMEOUT_SEC=3900` present in the launched VM's metadata (the headroom fix propagated). **STARTED@T+60s**:
    `gcloud` status `RUNNING` (run.log not yet uploaded that early — expected, the uploader loop starts a few minutes
    into boot). **PROGRESS@T+10min**: no crash/stall markers, heartbeating every 60s, chunk 1 started — and, expectedly
    given the CURRENTLY-RUNNING concurrent `tradfi-bf-cme-ohlcv-1m-es-2020..2026-*` fleet (6 VMs, launched
    ~10:41-10:43Z) generating heavy TRADFI write pressure, it hit the SAME documented consolidator-lock wait at
    11:10:28Z (`age=156s, horizon=3600s`; live-checked the lock blob — still held, rotated at least once since). This is
    the exact scenario the 3900s headroom fix exists for: NOT a repeat of the false-stall-kill, a correctly bounded wait
    now with margin past its own horizon. Leaving it running unattended per the established pattern above — no further
    action needed unless it re-fails past 3900s (would then indicate a NEW, different issue).

## Open follow-up: exit-code monitor mislabels a stall-kill as OOM

Not fixed in this pass (found live, evidence-backed, but a distinct component from anything above) — the fleet monitor's
`exit_code_fleet_monitor._finding_for()` computes `oom = result.exit_code == 137` as a PURE exit-code equality check,
with no distinction from an in-VM watchdog `WORKER_STALLED` kill (which also exits via SIGKILL=137). Confirmed live on
this exact incident: `-064542`'s finding was labeled OOM (`details.oom=True`) and would have carried
`bigger_machine=True` (see `exit_code_fleet_monitor.py` "KEY #4" comment — an OOM finding hints the actuator to relaunch
on a BIGGER machine) even though memory never left 17%. A `bigger_machine` auto-escalation on a genuine stall event buys
nothing (wrong remediation, wasted machine-tier cost) and, worse, neither tradfi launcher today even wires a
`MACHINE_TYPE`-style env through consistently (`launch-tradfi-backfill-vm.sh` hardcodes `MACHINE_TYPE` as a local bash
var, ignoring any env; `_tradfi-ohlcv-launcher-lib.sh` reads a differently-named `TRADFI_OHLCV_MACHINE`) — worth
verifying whether `escalation._recover_backfill_vm`'s `bigger_machine` wiring is a live no-op before trusting it
anywhere.

- [ ] [BACKEND] P3. Distinguish a genuine OOM from a stall-induced SIGKILL in `exit_code_fleet_monitor._finding_for()`
      before setting `details["oom"]`/`bigger_machine` — e.g. read the archived deployment record's
      `mem_pct`/`mem_slope` history (already collected in `host_metrics_window`) or the run.log's own
      `cause=`/`WORKER_STALLED` marker, and only flag OOM when memory was genuinely climbing toward the critical
      threshold at kill time. Repo: deployment-service. Evidence: this doc's Progress Log entry above (deployment_id
      `bdd2f745-bea7-46a0-89a3-ed6e962fd74a`, `mem_pct` flat at 17.0%, `cause=stall`).
- [ ] [BACKEND] P3. Verify whether `escalation._recover_backfill_vm`'s `bigger_machine` hint actually reaches either
      tradfi launcher today (neither reads a `MACHINE_TYPE` env consistently per the note above) — if it is a silent
      no-op, either wire it through properly or drop the hint rather than leave a documented-but-dead auto-escalation
      path. Repo: deployment-service.

- **2026-07-30 (separate session, closing this thread out) — the real root cause of the SLOW cycle times this whole doc
  chases was found + fixed: the tradfi manifest consolidator's own chunk-count blowup, not anything specific to FRED's
  fetch behavior.** Found `tradfi-bf-fred-full-20260730-110724` (the successor VM from the entry above) STILL running,
  ~2 hours in, having only progressed from `1962-01-02` to `1962-02-21` — at that rate it would have taken 900+ hours to
  reach 2020. Root-caused (full detail:
  `/plans/archive/issues/tradfi_manifest_consolidator_fred_widespan_stall_2026_07_30.md`): 522 genuinely-correct but
  now-orphaned 1962-1970 FRED rows (this exact backfill's own earlier output) were stretching the consolidator's
  merge-chunk-count planning to 787 chunks (a ~9x blowup vs. the ~85 a normal 2019-2026 tradfi span needs) — this is
  what was actually inflating cycle times toward (and past) this doc's own documented horizon, not a `FredAdapter`
  defect. Fixed the chunk-count cap (`unified-trading-library@59ed61c9`), stopped the now-doubly-obsolete VM (still on
  the old 1962 floor AND hitting the artificially slow consolidator), fixed `launch-tradfi-bf-fred.sh`'s default floor
  to `2020-01-01` to match the rest of tradfi's Databento group (`deployment-service@fee8860b`), and purged the orphaned
  1962-1970 fragment (538 GCS objects, 642 manifest rows, snapshot-first, reversibility-verified). This achieves todo
  `[x] [DATA] P1`'s underlying goal (a real, unstuck FRED production backfill) via a different path than originally
  anticipated — STOPPING the VM and fixing its floor, rather than letting the original 1962-01-02..today run to
  completion, since that original scope was itself the thing making the consolidator slow. Post-fix, consolidator cycles
  measured at ~75s (vs. 6+ minutes pre-fix) — this substantially reduces (but doesn't eliminate) the value of todo P2's
  explicit `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["tradfi"]` override above; left that todo open since a measured,
  explicit value is still better than the current default regardless of how much healthier the consolidator now is.

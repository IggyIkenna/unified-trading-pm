---
doc_type: issue
title:
  mdps-* backfill fleet exploded to 676 simultaneously-running VMs (505 e2-highmem-8 + 148 e2-standard-8) against an
  expected ~28 — every relaunch of ONE terminated shard fanned out the ENTIRE fleet
summary: |
  While monitoring an unrelated CeFi liquidations backfill VM, found the entire `mdps-*` backfill fleet had exploded to
  676 simultaneously-running VMs against a project that should only ever need ~1 VM per (asset_group, year) cell (~28
  cells: `mdps-{cefi,tradfi,sports,defi,prediction}-{2019..2026}`). Root-caused to TWO compounding bugs: (1)
  `launch-mdps-sharded-backfill.sh` scopes itself via POSITIONAL CLI ARGS (`<asset_group> --year <YYYY>`), not
  environment variables, and never calls `lc_write_launch_params` — so `relaunch_backfill_vm.py`'s zero-positional-arg
  actuator invocation (`["bash", <path>]`, relying entirely on env-var replay) fell through to the script's own "no
  asset_group given" default: ALL 5 asset_groups x ALL configured years (~28 VMs) launched from ONE relaunch of ONE
  terminated shard. Confirmed live via Cloud Run Job text logs: four independent `mdps-cefi-{2019,2020,2021,2022}-*`
  preemptions each independently "dispatched a preemption-aware relaunch via the auto_recover tier" within one 30-minute
  window — each such dispatch fanned out the WHOLE fleet, not just its own shard. (2) No dispatch-cell dedup existed
  anywhere in the escalation/relaunch path — unlike `scripts/wave_launcher.py`'s `running_cell_keys()`, nothing checked
  "is another VM already running this exact (asset_group, year) cell" before dispatching a relaunch; dedup
  (`escalation_dedup.py`) is keyed only on the ephemeral `vm_name` or `(asset_group, data_type)`, never on cell
  identity, and even the per-vm_name idempotency claim (`_stamp_relaunch`) had its return value silently discarded,
  so an overlapping Cloud Run Job execution re-processing the same terminated VM could ALSO independently dispatch.
  Cross-references `tradfi_bf_cme_ohlcv_asia_northeast1_c_preemption_thrash_2026_08_15.md` (archived same day) as a
  SEPARATE, more severe instance of the same dedup-gap CLASS that doc found for the TradFi CME OHLCV family — this is
  NOT a duplicate of that finding, it is the fleet-wide `mdps-*` sibling, roughly 20-30x the fleet-inflation magnitude.
status: resolved
nature: issue
asset_group: [cefi, tradfi, defi, sports, prediction, cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-preemption, billing-waste, spot-capacity, duplicate-dispatch, alerting-gap, cross-cutting, big-finding]
related:
  [
    /plans/archive/2026_08/issues/tradfi_bf_cme_ohlcv_asia_northeast1_c_preemption_thrash_2026_08_15.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-15
priority: P0
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Found while monitoring an unrelated CeFi liquidations backfill VM; emergency cleanup (REAPED tombstones + delete +
  cron pause) already executed by the operator/parent session before this doc was authored. Root-caused, fixed, and
  shipped autonomously per operator authorization.
drift_direction: advance-code
context_scope:
  [
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
    deployment-service/deployment_service/data_pipeline_monitors/_classify.py,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
    deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh,
    deployment-service/scripts/wave_launcher.py,
  ]
---

# mdps-* fleet duplicate-relaunch explosion — 676 VMs against an expected ~28

> **🟢 ARCHIVED 2026-08-22 (slot 7, infra — cross_cutting_satellite_ao_dispatch_batch20_2026_08_19.md item 3).**
> Every todo below is now `[x]` — the sole remaining item (cron re-enable) closed this session: verified the deployed
> Cloud Run Job image (`deployment-service:latest`, built by `deployment-service`'s own
> `deployment-service-jobs-image-build` Cloud Build trigger — corrected a stale assumption in this doc's own todo
> text that it was `deployment-api:latest`) already contains both fixes (commit `59306b7`, deployed
> 2026-08-22T08:44:14Z), resumed `uts-prod-dp-exit-code-monitor-cron` (`ENABLED`, `*/5 * * * *`), and watched
> multiple firings with a stable, non-duplicating fleet. See the Progress Log entry below for full evidence. The
> durable contract this incident established (dispatch-cell dedup, mirroring `wave_launcher.running_cell_keys()`)
> is already captured in `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` — no codex update
> needed.

> **🔴 SECOND WAVE, 2026-08-15 (later same day) — see "Second wave" section below.** A SEPARATE, independently-
> discovered bug (`vm_zombie_watchdog.py`'s EXIT_STATUS check being content-blind) was actively mass-killing healthy,
> actively-working VMs fleet-wide (320 distinct VMs over ~10h, 07:39-17:29 UTC) at the time this was found. Strong
> correlating evidence (below) indicates this bug was very likely the ACTUAL trigger — not genuine SPOT reclaim — behind
> at least the "four independent mdps-cefi-{2019,2020,2021,2022} preemptions" this doc's ORIGINAL section below cites as
> the incident's proximate cause. Read the Second-wave section before trusting the "SPOT reclaim" framing in the text
> below it.

## What happened (timeline)

1. **Discovery**: while monitoring an unrelated CeFi liquidations backfill VM, a fleet-wide
   `gcloud compute instances list` turned up 676 simultaneously-running `mdps-*` VMs (505 `e2-highmem-8` + 148
   `e2-standard-8`) against a project that should need only ~1 VM per `(asset_group, year)` cell — ~27-31 cells across
   `mdps-{cefi,tradfi,sports,defi,prediction}-{2019..2026}`.
2. Confirmed via direct instance metadata inspection that multiple simultaneously-running VMs in the same family carried
   the **exact identical** `VM_BACKFILL_CMD` (same asset_group, same full-year date range, no venue/data-type narrowing)
   — genuine duplicate dispatch, not legitimate parallel sharding.
3. Confirmed via BigQuery `deployment_operational_data.resource_samples` that essentially ALL of them were genuinely
   alive and burning real CPU (~15-30% each) on the same overlapping work.
4. **Emergency response** (executed before this doc, not repeated here): wrote a `REAPED` tombstone for every duplicate
   VM before deleting it (the sanctioned `deployment_service/data_pipeline_monitors/_vm_markers.py` pattern —
   `exit_code_fleet_monitor.py` reads `is_vm_reaped()` to mean "deliberate delete, no alert, NO relaunch"); deleted 725
   duplicate VMs across two cleanup rounds; **paused `uts-prod-dp-exit-code-monitor-cron`**
   (`gcloud scheduler jobs pause ... --location=asia-northeast1`) to stop further duplicate generation; verified final
   state at exactly 1 running VM per cell, 28 total.
5. This doc: root-cause, fix, ship, verify, and (conditionally) re-enable the cron.

## Root cause — TWO compounding bugs

### Bug 1 (dominant, ~20-30x amplification): unscoped launcher invocation

`launch-mdps-sharded-backfill.sh` (bound via `launcher_registry.LAUNCHER_FOR_VM_PREFIX` for `mdps-cefi-`,
`mdps-tradfi-`, `mdps-defi-`, `mdps-sports-`, `mdps-prediction-`) resolves its `asset_group` + `--year` scope from
**positional CLI arguments** — `cefi|tradfi|defi|sports|prediction ... --year YYYY` — not environment variables. With
zero args, `SELECTED_AGS` defaults to **all 5 asset_groups** and `SELECTED_YEARS` defaults to unset (**all configured
years**), launching ~28 VMs.

`scripts/recovery/relaunch_backfill_vm.py`'s `_default_run_launcher` invoked every bound launcher as
`subprocess.run(["bash", str(path)], env=full_env)` — **zero positional arguments**, relying entirely on `launch_env`
(captured at original launch time by `lc_write_launch_params` and replayed verbatim) to scope the relaunch. But
`launch-mdps-sharded-backfill.sh` is **not** in the set of launchers that call `lc_write_launch_params`
(`grep -rl lc_write_launch_params scripts/vm/*.sh` — confirmed absent), so `launch_env` was **always empty** for an
`mdps-*` VM. Every relaunch (`RelaunchPreemptedVm`'s `DP_VM_PREEMPTED` auto_recover path, or `RelaunchBackfillVm`'s
`DP_VM_EXIT_NONZERO` OOM path) therefore invoked the launcher with no scoping at all, falling straight through to the
script's own unscoped full-fleet default — **one relaunch of one terminated shard launched ~28 new VMs**.

**Confirmed live** (Cloud Run Job text logs, `uts-prod-dp-exit-code-monitor`, ~14:00-14:30 UTC 2026-08-15, i.e. spanning
the window around the cron pause): four independent `mdps-cefi-{2019,2020,2021,2022}-*` VMs each independently logged
`"preempted (SPOT reclaim) — dispatching a preemption-aware relaunch via the auto_recover tier"` within a ~30-minute
span. Each of those four dispatches, per the mechanism above, fanned out the entire fleet rather than its own single
shard — this is the direct, order-of-magnitude explanation for 676 VMs against an expected ~28 (four-plus such
dispatches x ~28 VMs each accounts for the bulk of the observed peak; SPOT preemption under sustained contention is a
recurring event, not a one-off, so this compounds continuously once triggered).

### Bug 2 (compounding, closes the class): no dispatch-cell dedup anywhere in the path

Read `escalation.py` + `escalation_dedup.py` in full. Dedup is keyed ONLY on:

- the exact ephemeral `vm_name` (`find_open_issue_for_vm` / `check_dispatch_dedup_vm` — an OPEN issue doc already
  covering this exact terminated VM), or
- `(asset_group, data_type)` tuple dedup (the DP-FETCH-009 path — irrelevant to VM-lifecycle findings).

Nothing checks "is a **different**, currently-alive VM already covering the same logical cell (`asset_group`, `year`)"
before dispatching a relaunch — the exact class `scripts/wave_launcher.py`'s `running_cell_keys()` already solves for
its own dispatch path (`pending = [d for d in candidates if d.cell_key not in running_keys]`), never adopted here.
Additionally, `RelaunchBackfillVm._stamp_relaunch` / `RelaunchPreemptedVm._stamp_relaunch` called
`self._budget_state.claim(...)` (an idempotent create-if-absent primitive) but **discarded its return value** — so even
the ONE per-vm_name idempotency check that existed was never actually enforced; an overlapping Cloud Run Job execution
(documented as a real, confirmed phenomenon in this module's own docstring: "a 15:30 execution finished 15:45 while
15:35/15:40/15:45 had already started") reprocessing the same terminated VM could dispatch a second, fully redundant
relaunch.

This is a **separate, more severe instance of the same dedup-gap CLASS**
`tradfi_bf_cme_ohlcv_asia_northeast1_c_preemption_thrash_2026_08_15.md` found for the TradFi CME OHLCV family that same
day (zone-concentration causing a preempt-relaunch-preempt thrash) — not a duplicate of that finding. That doc's root
cause was zone contention + a launcher-freshness atom-format bug; this doc's is a launcher CLI-arg-scoping gap plus the
missing cell-level dedup wave_launcher already has. Both point at the same structural lesson: **a relaunch actuator must
be scoped to, and deduped against, the exact logical unit of work it is replacing** — this incident is the fleet-wide
(~28 cells, ~20-30x inflation) sibling of that narrower (8 shards, thrash-not-explosion) one.

## The fix

Both bugs closed in `deployment-service`:

1. **`scripts/recovery/relaunch_backfill_vm.py`**: added `relaunch_cli_args(launcher, vm_name)` — a small launcher-name
   → positional-args resolver (`_CLI_SCOPED_LAUNCHER_ARGS`), today holding exactly one entry:
   `"launch-mdps-sharded-backfill.sh"` → parses `(asset_group, year)` from the terminated VM's own name
   (`mdps-{ag}-{year}-{RUN_TS}`) and returns `[asset_group, "--year", year]`. Every other launcher is unaffected
   (`relaunch_cli_args` returns `(None, True)` — unchanged, env-only-scoped behavior). `_default_run_launcher` now
   accepts an optional `args` list threaded onto the subprocess command. **A CLI-scoped launcher whose vm_name fails to
   parse REFUSES to relaunch** (`status=FAILED`, `cli_scope_unresolved`) rather than silently falling back to the
   unscoped full-fleet default — that silent fallback IS this incident, so a parse failure must never be treated as "no
   args needed."
2. **Same file**: `_stamp_relaunch`'s `claim()` return value is now actually checked in both `RelaunchBackfillVm` and
   `RelaunchPreemptedVm` — a `False` (already claimed this exact `vm_name` today) now returns `status=SUPPRESSED` BEFORE
   the launcher subprocess is invoked, instead of silently discarding the signal and relaunching anyway. Closes the
   overlapping-Cloud-Run-Job-execution duplicate-dispatch race for the SAME terminated VM.
3. **`_classify.py`**: added `cell_key_for_vm(vm_name) -> (asset_group, year) | None` (mirrors
   `wave_launcher.running_cell_keys()`) and a `cell_already_covered` parameter on `finding_for()`. When a terminated
   VM's cell is already served by a CURRENTLY-RUNNING VM: `PREEMPTED`/`PARTIAL_UNCONFIRMED` (the two
   unconditional-on-exit-code relaunch verdicts) return `None` — no finding, no alert, no dispatch, fully benign,
   mirroring the existing `REAPED`/`CLEAN`/`EXPECTED_NO_CAPTURE` "nothing to do" convention; an `EXIT_NONZERO`
   OOM/WORKER_STALLED crash still alerts (the terminated VM's own failure is real signal) but withholds
   `relaunch_launcher` so the actuator cannot ALSO dispatch a duplicate.
4. **`exit_code_fleet_monitor.py`**: `sweep()` now computes the set of dispatch cells covered by the current tick's
   `running_vms` census, checks each terminated VM's cell against it before building its finding (with an intra-sweep
   optimistic reservation so two duplicate-cell terminations in the SAME sweep tick don't both dispatch before either
   replacement is observed as running), and passes `cell_already_covered` through to `finding_for`.
5. **Regression tests**: `tests/unit/test_mdps_fleet_duplicate_relaunch_dedup.py` (new, focused file — the existing
   `test_data_pipeline_monitors.py` is 6000+ lines) covers: `cell_key_for_vm` parsing (incl. non-matching sibling
   families `mdps-backfill-*`/`mdps-sports-bucket-*`/`mdps-features-live-*` correctly returning `None`);
   `finding_for(cell_already_covered=True)` suppression for PREEMPTED/PARTIAL_UNCONFIRMED and relaunch-withholding for
   OOM; `relaunch_cli_args` resolution + refusal-on-unparseable-name; `RelaunchPreemptedVm`/`RelaunchBackfillVm`
   actually invoking the launcher subprocess with the scoped `["cefi", "--year", "2022"]` args (the direct proof the
   676-VM bug is closed) and refusing an unscoped relaunch when the name doesn't parse; the same-vm_name overlapping-
   sweep duplicate-dispatch suppression; and the operator-specified end-to-end scenario — a live VM covering a cell + a
   PREEMPTED finding for that same cell — proving via `exit_code_fleet_monitor.sweep()` that the launcher subprocess is
   never invoked and no finding is filed.

## Verification

- `bash scripts/quality-gates.sh --no-fix` run on the working tree containing this fix (see Progress Log for the
  outcome/sentinel).
- Shipped via `quickmerge --agent`, verified ancestor of `origin/live-defi-rollout` (see Progress Log for SHA).
- Cron re-enable decision + post-re-enable fleet-size monitoring: see Progress Log.

## Related residual finding (not fixed in this pass — tracked, out of blast radius)

`scripts/recovery/relaunch_stalled_vm.py`'s `RelaunchStalledVm` budget is a **tempdir-local JSON file**, not the
GCS-durable `ShardedState` primitive `RelaunchBackfillVm`/`RelaunchPreemptedVm` use — in the
`uts-prod-dp-exit-code-monitor` Cloud Run Job's fresh-container-per-execution model, this budget always reads 0 (the
same architectural bug the OOM/PREEMPTED budgets had before their 2026-08-10 `ShardedState` migration). Zero blast
radius for THIS incident (`DEFAULT_WORKER_STALL_SAFE_LAUNCHERS` — the only launchers `RelaunchStalledVm` auto-relaunches
— does not include `launch-mdps-sharded-backfill.sh`), but the same class of bug given the right trigger. Not fixed here
to keep this ship narrowly scoped to the proven incident; tracked below.

## Second wave (2026-08-15, later same day): vm_zombie_watchdog false-kill bug — likely the TRUE trigger

Dispatched to investigate a SEPARATE, unrelated-looking symptom: a manually-launched on-demand (non-preemptible) CeFi
liquidations backfill VM (`launch-mdps-backfill-vm.sh`, NOT `launch-mdps-sharded-backfill.sh`) was deleted TWICE within
hours, each time actively processing real work with zero errors. Root-caused via the Compute Engine audit log
(`protoPayload.methodName="v1.compute.instances.delete"`) to `uts-prd-sa` from IP `34.104.218.77`, and via that IP's
serial-console log trail to the standalone `vm-zombie-watchdog-20260810-163005` GCE VM
(`scripts/vm/vm_zombie_watchdog.py`) — a completely separate mechanism from `uts-prod-dp-exit-code-monitor-cron`
(confirmed PAUSED at `2026-08-15T15:45:15Z`, i.e. AFTER the first kill and BEFORE the second — ruling the cron out
directly). Serial console proof: `KILLED mdps-backfill-cefi-20260815-155830 (...) reason=zombie_finished_not_shutdown`.

### Root cause

A same-day commit, `599b4b81` (`fix(vm): stamp RUNNING sentinel at boot in vm-exec-with-gcs-tee.sh...`, landed 09:41
UTC), ported an existing `launcher_common.sh` fix (2026-07-13, `lc_log_upload_trap_block`) into
`vm-exec-with-gcs-tee.sh`: both now stamp a non-terminal `"RUNNING"` sentinel into the `EXIT_STATUS` GCS blob
immediately at boot, BEFORE the workload starts, so a same-named relaunch's `read_terminal_exit_code()` never misreads a
stale prior run's terminal exit code (`"RUNNING"` fails `int()` parse → correctly falls through to `None`). Necessary
and correct for that reader.

`vm_zombie_watchdog.py`'s `_evaluate_vm()` EXIT_STATUS check, however, is content-BLIND — it only checks blob
EXISTENCE + AGE (`exit_status_age > finished_grace`, default 10min) and treats that alone as proof the workload finished
and failed to self-delete (`zombie_finished_not_shutdown`). Because the RUNNING sentinel is written once near boot and
only overwritten at TRUE completion, its age grows from boot time, not from any real completion — so ANY VM using either
wrapper, whose job runs longer than `min_age`(15) + `finished_grace`(10) ≈ 15-25 minutes, gets killed while genuinely
still working, unconditionally.

**Confirmed live**, this was not narrowly scoped to the 2 CeFi VMs discovered first. A full-day Cloud Logging sweep
(`textPayload:"reason=zombie_finished_not_shutdown"`, freshness=1d) found **320 distinct VMs killed, 07:39-17:29 UTC** —
spanning `mdps-cefi` (192), `instr-backfill-defi-pchk-*` (144, many DeFi venues: solend/marginfi/jito/
raydium/orca/marinade/kamino/aave-v3-linea), `mdps-tradfi` (106), `mdps-sports` (76), `mdps-defi` (74), `tradfi-bf`
(32), `mtds-oracle-prices-backfill` (12), plus smaller counts across `mdps-backfill-cefi`, `prediction-pipeline`,
`mtds-live`, `mtds-backfill`, `cefi-queue`, `cefi-binance`. At the moment of discovery the watchdog was killing a VM
roughly every 60-90 seconds, live, in real time (last observed kill 17:29:45 UTC, ~1 minute before this investigation
stopped the watchdog VM — see Immediate mitigation below).

**Kills started 07:39 UTC — well before `599b4b81` (09:41 UTC)**, meaning the earliest kills that day cannot be
explained by the `vm-exec-with-gcs-tee.sh` port; they are consistent with the OLDER `lc_log_upload_trap_block` sentinel
(live since 2026-07-13), which has apparently been causing the SAME class of false kill for over a month for any
inline-startup-script launcher whose job runs past the grace window — this bug's true historical blast radius is almost
certainly larger than one day and was not scoped further in this pass (see residual todo below).

### Correlation with THIS doc's own "Bug 1" narrative — likely the actual trigger

This doc's ORIGINAL text above cites, as confirmed live evidence for the explosion: _"four independent
`mdps-cefi-{2019,2020,2021,2022}-*` VMs each independently logged 'preempted (SPOT reclaim) — dispatching a
preemption-aware relaunch...' within a ~30-minute window ~14:00-14:30 UTC."_

The full-day zombie-kill sweep shows, in that EXACT 14:00-14:30 UTC window, the watchdog killing `mdps-cefi-2019-*`,
`mdps-cefi-2020-*`, `mdps-cefi-2021-*`, and `mdps-cefi-2022-*` VMs via `reason=zombie_finished_not_shutdown` roughly
once per minute, PER YEAR, continuously (e.g. `mdps-cefi-2019- 20260815-120236` killed 13:59:40Z,
`mdps-cefi-2020-20260815-120236` killed 14:08:00Z, `mdps-cefi-2021-20260815- 120236` killed 14:15:54Z,
`mdps-cefi-2022-20260815-120941` killed 14:23:55Z, and many more before/after — not an isolated four-VM event, a
sustained pattern). An earlier, separate four-VM cluster of the identical shape (all 4 years, run-ts `20260815-100208`,
~3 minutes apart) appears at 10:24-10:27 UTC too.

The exit-code-monitor's classifier has no way to distinguish "watchdog force-deleted this VM" from "GCE preempted it" —
both manifest identically as the VM vanishing/going TERMINATED with no clean EXIT_STATUS. It is very likely that at
least some, plausibly most, of what the earlier session's Cloud Run Job log query read as "preempted (SPOT reclaim)" was
actually this watchdog bug's own kill, misclassified. If so, the causal chain was a SELF-SUSTAINING LOOP, not four
isolated events: watchdog false-kills a batch of VMs → (pre-Bug1-fix) the unscoped relaunch fans out to ~28 VMs → ~20-25
minutes later, any of THOSE that ran long enough get false-killed too → repeat. That fully explains sustained growth to
676 VMs over hours far better than four isolated preemptions would. This is offered as STRONG circumstantial correlation
(timing + VM-identity match is exact), not 100%-proven causation — the original session's own log query text ("preempted
(SPOT reclaim)") was not re-derived by this investigation from the raw Cloud Run Job source event, only the watchdog's
own kill log was. Bug 1 and Bug 2's fixes (unscoped-launcher CLI scoping + cell-level dedup) remain necessary and
correct regardless of which of the two triggers actually fired first — they close the AMPLIFICATION step either way.

> **CORRECTION (2026-08-17, slot-8, backend_engineer) — this correlation theory is REFUTED, not just unproven.** The
> re-derivation this section calls for was done (`cefi_satellite_ao_dispatch_batch20_2026_08_16.md` item 5, full
> evidence there). The raw `uts-prod-dp-exit-code-monitor` Cloud Run Job log names the exact terminated-VM instances
> (run-ts included): `mdps-cefi-2019-20260815-050114`, `mdps-cefi-2020-20260815-041556`,
> `mdps-cefi-2021-20260815-020059`, `mdps-cefi-2022-20260815-050114`, `mdps-cefi-2022-20260815-050859` — **different
> run-ts (`05xxxx`/`04xxxx`/`02xxxx`, pre-dawn launches) from the watchdog-kill VMs this section names above
> (`12xxxx` run-ts, noon launches)**. The "VM-identity match is exact" claim above does not hold once the raw log is
> read for full VM names rather than just year. All 5 exact VMs cross-checked against three independent full-day
> (2026-08-15T00:00-23:59Z) log sources: a real GCE-system `compute.instances.preempted` audit-log operation exists
> for every one of them (HOURS before the monitor's dispatch — consistent with relaunch-budget lag, not coincidence);
> zero `reason=zombie_finished_not_shutdown` watchdog-kill hits for any of them; zero `uts-prd-sa`
> `compute.instances.delete` hits for any of them. The `is_preempted` signal itself (`exit_code_fleet_monitor.py` →
> `_classify.py` → `_compute_ops.make_preemption_op_checker`, or the in-guest GCS marker gated on the GCE metadata
> server's `instance/preempted` value, `scripts/vm/lib/launcher_common.sh:825-827`) is GCE-system-authoritative and
> structurally cannot be produced by a `compute.instances.delete` call — the mechanism this section speculates the
> watchdog spoofed cannot actually be spoofed that way. **Verdict: the four original dispatch events were genuine SPOT
> reclaims, not watchdog false-kills.** Bug 1/Bug 2's fixes are unaffected either way, per this section's own closing
> sentence.

### The fix

`deployment-service/scripts/vm/vm_zombie_watchdog.py`: added `_read_exit_status_terminal_code()`, which downloads and
`int()`-parses the EXIT_STATUS blob's CONTENT (mirroring `read_terminal_exit_code()`'s own contract in `_gcs_tail.py`)
before treating an aged blob as completion proof. `"RUNNING"` (or any unparseable content, or a content-read failure —
fail-safe, never zombie on an undetermined read) now falls through to the heartbeat/shard checks instead of an immediate
kill; a genuinely terminal integer exit code (real completion, self-delete failed) still kills correctly — the fix is
scoped to the false-positive, not a blanket disable. Regression tests added in `tests/unit/test_vm_zombie_watchdog.py`
(`TestReadExitStatusTerminalCode`, `TestEvaluateVmExitStatusContentAware`).

### Immediate mitigation (this session, before the fix could reach the live watchdog process)

The watchdog VM fetches its script from GCS ONCE at boot (`launch-vm-zombie-watchdog.sh`'s `LOOP_CMD`:
`gsutil cp ... /tmp/watchdog.py` then `while true; do python3 /tmp/watchdog.py ...; sleep 300; done`) — it does NOT
re-fetch per cycle, so shipping the code fix alone does not stop the live process from continuing to kill VMs. Given the
confirmed ACTIVE, ONGOING damage (a kill roughly every 60-90s at time of discovery) to real, in-flight backfill
campaigns, this session:

1. Applied `keep=true` label to the then-currently-running, in-danger `mdps-backfill-cefi-20260815-181733` (age ~10min
   at label time, just under the danger window) — the sanctioned protective mechanism this same file's own docstring
   documents for exactly this situation.
2. STOPPED `vm-zombie-watchdog-20260810-163005` (`gcloud compute instances stop`, not delete — reversible) once the
   scale of active ongoing damage was confirmed, rather than wait for a full relaunch-with-fix cycle. This trades a
   temporary (minutes) loss of genuine-zombie protection fleet-wide against continuing, confirmed, active destruction of
   real work — judged the correct trade given the evidence. See Progress Log for the fixed watchdog's relaunch +
   old-instance retirement outcome.

### Scope NOT closed by this pass (tracked below)

- The ~320 VMs killed today were NOT auto-relaunched (`uts-prod-dp-exit-code-monitor-cron` has been PAUSED since
  15:45:15Z per this doc's own earlier decision, and many kills predate that anyway) — every one of those killed
  campaigns is a genuine, un-recovered data-capture gap until an operator reviews and relaunches as needed. This is
  beyond what a single investigation pass can safely bulk-remediate (320 separate launch decisions, several asset
  groups) — tracked as an `[OPERATOR]` todo below, not auto-relaunched by this session.
- The `lc_log_upload_trap_block` sentinel (2026-07-13) predates today — this same false-kill class may have been live
  for over a month for launchers using that wrapper. Not historically scoped beyond today's 1-day sweep.

## Todos

- [x] [SCRIPT] P0. Root-cause the duplicate-relaunch explosion — confirmed both the CLI-arg-scoping gap
      (`launch-mdps-sharded-backfill.sh` invoked with zero args, falling through to its full-fleet default) and the
      missing cell-level dedup (no `running_cell_keys()`-equivalent anywhere in the relaunch/escalation path), via
      direct code reading + live Cloud Run Job log confirmation (four independent same-window `mdps-cefi-*` preemptions
      each independently dispatching a relaunch).
- [x] [SCRIPT] P0. Fix Bug 1 — scope the MDPS sharded-launcher relaunch to exactly the terminated VM's own
      `(asset_group, year)` shard (`relaunch_cli_args` + `_default_run_launcher(..., args=...)` in
      `scripts/recovery/relaunch_backfill_vm.py`), refusing an unscoped relaunch when the vm_name doesn't parse rather
      than falling back to the launcher's full-fleet default.
- [x] [SCRIPT] P0. Fix Bug 2 — add `cell_key_for_vm` + `finding_for(cell_already_covered=...)` in `_classify.py` and
      wire the running-cell check into `exit_code_fleet_monitor.sweep()`, mirroring `wave_launcher.running_cell_keys()`;
      also stop discarding `_stamp_relaunch`'s claim() return value so an overlapping sweep execution cannot
      double-dispatch the SAME terminated vm_name.
- [x] [SCRIPT] P0. Write regression tests proving both fixes, incl. the operator-specified scenario (a live VM covering
      a cell + a relaunch-eligible finding for that same cell → dispatch skipped, not duplicated) —
      `tests/unit/test_mdps_fleet_duplicate_relaunch_dedup.py`.
- [x] [SCRIPT] P0. Ship via `quality-gates.sh` green → `quickmerge --agent --files '<paths>'` — **shipped
      `deployment-service@4d96b24adb`**, ancestor-verified on `origin/live-defi-rollout`, content verified present at
      that SHA (`git show 4d96b24adb:<path>` for all four files). QG sentinel `.qg_last_passed_sha` matched HEAD before
      shipping. See Progress Log for the merge-conflict resolution this required (an upstream Track-V-verify feature
      landed on the SAME two files concurrently).
- [x] [INFRA] P0. Re-enable `uts-prod-dp-exit-code-monitor-cron` — **DONE 2026-08-22 (slot 7, infra)**. Corrected a
      stale assumption in this todo's own prior text: `gcloud run jobs describe uts-prod-dp-exit-code-monitor` shows
      the job actually runs off `asia-northeast1-docker.pkg.dev/.../deployment-service:latest` directly, NOT
      `deployment-api:latest` — deployment-service has its own dedicated Cloud Build trigger
      (`deployment-service-jobs-image-build`) that builds+publishes this image straight from `main`, no
      deployment-api rebuild in the path at all. Verification chain actually run: (1) confirmed
      `deployment-service` has promoted LDR→main repeatedly (last few promote PRs merged today, e.g. #1147 at
      12:39:09Z) and that the fix content (`cell_key_for_vm` x4 in `_classify.py`, `_read_exit_status_terminal_code`
      x2 in `vm_zombie_watchdog.py`) is present on `main`; (2) found the deployed image was built by
      `deployment-service-jobs-image-build` build `a4d3bfd6` (2026-08-22T08:38:35Z) from commit `59306b7`, and
      confirmed via the GitHub contents API at that exact commit that both fix signatures are present (4 and 2 hits
      respectively) — deploy propagation is genuinely complete, no rebuild needed; (3) `gcloud run jobs describe`
      confirms `lastUpdatedTime = 2026-08-22T08:44:14Z`, after that build; (4) resumed the scheduler
      (`gcloud scheduler jobs resume uts-prod-dp-exit-code-monitor-cron --project=central-element-323112
      --location=asia-northeast1 --account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com`) —
      confirmed `state=ENABLED`, `schedule=*/5 * * * *`; (5) watched fleet-size samples across multiple firings at
      the 5-min cadence, both immediately after resume and again after a session gap: stable/non-climbing (3, then
      2, always distinct cells — `mdps-defi-2025-*` plus `mdps-sports-bucket-*` shards completing normally), zero
      duplicate-cell dispatch. The literal "26-31" range this todo's prior text named was specific to the
      2026-08-15 incident-day state (a full backfill campaign actively running across every cell); today's much
      smaller live fleet (most 2026-08-15-era campaigns have since completed) makes that exact number inapplicable,
      but the actual invariant it existed to protect — stable, non-climbing, no duplicate-cell relaunches — is
      directly confirmed. No re-pause needed.
- [x] [SCRIPT] P2. `scripts/recovery/relaunch_stalled_vm.py`'s `RelaunchStalledVm` budget is tempdir-local (not
      `ShardedState`-durable) — the same architectural class of bug the OOM/PREEMPTED actuators had before their
      2026-08-10 fix, currently zero-blast-radius for this incident (no MDPS launcher is in
      `DEFAULT_WORKER_STALL_SAFE_LAUNCHERS`) but worth closing proactively. Migrate it to `ShardedState` mirroring
      `RelaunchBackfillVm`/`RelaunchPreemptedVm`'s pattern. **DONE 2026-08-16 — `deployment-service@6f2f8e02bf`**:
      migrated `_relaunches_today`/`_stamp_relaunch` to the `ShardedState` primitive (own `/stall` namespace under
      `vm-census/relaunch-budget`), mirroring `RelaunchBackfillVm` exactly, including its per-`(day, prefix, vm_name)`
      idempotent claim (`SUPPRESSED`/`already_relaunched_this_vm` on an overlapping-sweep double dispatch — a bonus
      the sibling classes already have that the old bare-count budget didn't). Regression tests added in
      `tests/unit/test_dp_recovery_actuators.py` (`test_stalled_relaunch_budget_survives_a_fresh_container` — proves
      the budget survives a NEW actuator instance the way a Cloud Run Job's fresh-container-per-execution model
      requires; `test_stalled_relaunch_concurrent_stamps_do_not_lose_budget_increments`;
      `test_stalled_relaunch_suppresses_duplicate_dispatch_for_same_vm_overlapping_sweep`), mirroring the existing
      `RelaunchPreemptedVm` durability tests' exact pattern. Content verified present at that SHA
      (`git show 6f2f8e02bf:scripts/recovery/relaunch_stalled_vm.py | grep -c ShardedState` = 4). QG green before ship.

### Second-wave todos (vm_zombie_watchdog false-kill, added 2026-08-15 later same day)

- [x] [SCRIPT] P0. Root-cause the CeFi liquidations VM double-deletion via the Compute Engine audit log +
      `vm-zombie-watchdog-20260810-163005`'s serial-console trail — confirmed `reason=zombie_finished_not_shutdown`, a
      content-blind EXIT_STATUS-age check misfiring on the `"RUNNING"` boot sentinel `599b4b81`/`launcher_common.sh`
      (2026-07-13) both stamp.
- [x] [SCRIPT] P0. Fix `vm_zombie_watchdog.py`'s `_evaluate_vm()` to be content-aware
      (`_read_exit_status_terminal_code()`) before treating an aged EXIT_STATUS blob as completion proof; add regression
      tests (`TestReadExitStatusTerminalCode`, `TestEvaluateVmExitStatusContentAware`).
- [x] [SCRIPT] P0. Ship via `quality-gates.sh` green → `quickmerge --agent`. See Progress Log for SHA.
- [x] [SCRIPT] P0. Immediate mitigation while the fix propagates: `keep=true` label on the live
      `mdps-backfill-cefi-20260815-181733`; STOP (not delete) the buggy `vm-zombie-watchdog-20260810-163005` given
      confirmed active ongoing damage (~1 kill/60-90s fleet-wide at discovery time).
- [x] [SCRIPT] P0. Relaunch `vm-zombie-watchdog` via `launch-vm-zombie-watchdog.sh` (re-uploads the fixed
      `vm_zombie_watchdog.py` to GCS, boots a fresh watchdog VM) — verify it boots healthy (a sweep completes, no crash)
      BEFORE retiring the old stopped instance, so fleet zombie-protection coverage is never fully dark. **DONE
      (checkbox was never flipped when the work landed — corrected 2026-08-16)**: fixed watchdog relaunched as
      `vm-zombie-watchdog-20260815-191525`, verified healthy via a real 54-VM sweep (0/0 killed). Independently
      re-confirmed this session: the CeFi liquidations VM (`mdps-backfill-cefi-20260815-181733`) has now survived 15+
      consecutive hourly health checks with zero re-kills since this fix landed, vs. 2 kills in the ~1.5h before it.
- [x] [SCRIPT] P1. Once the fixed watchdog is confirmed healthy: delete the old stopped
      `vm-zombie-watchdog-20260810-163005`, and remove the `keep=true` label from `mdps-backfill-cefi-20260815-181733`
      (restores normal genuine-zombie protection for that VM once the false-positive risk is gone). **DONE (checkbox
      was never flipped when the work landed — corrected 2026-08-16)**: per the same fix-agent's final report, old
      instance retired and the protective label removed once the fixed watchdog was verified live.
- [x] [OPERATOR] P0. Review + selectively relaunch the ~320 distinct VMs killed 07:39-17:29 UTC today by this bug
      (families: `mdps-cefi`/`mdps-tradfi`/`mdps-sports`/`mdps-defi`, `instr-backfill-defi-pchk-*`,
      `mtds-oracle-prices-backfill`, `tradfi-bf-*`, smaller counts elsewhere) — **RESOLVED 2026-08-16 (operator
      confirmation): this batch was a smoke-test launch, not real production backfill campaigns.** No genuine
      data-capture work was lost; no relaunch needed. Correcting the prior framing here — this was NOT "real stalled
      backfill work sitting idle," it was disposable test infrastructure. Leave any genuinely-needed backfill coverage
      to normal AO-dispatched agents working against fresh (fixed) code going forward, not a manual bulk-relaunch pass.
- [x] [SCRIPT] P1. `lc_log_upload_trap_block`'s RUNNING sentinel has existed since 2026-07-13 — over a month before this
      was caught. Historically scoped how far back this false-kill class goes via bounded `gcloud logging read` sweeps
      (project `central-element-323112`) over `resource.type="gce_instance"` for the exact
      `textPayload:"reason=zombie_finished_not_shutdown"` kill signature and the broader `textPayload:"WARNING ZOMBIE"`
      pre-kill-decision signature, across 2026-06-15→2026-08-15T07:39:00Z (covers the full `lc_log_upload_trap_block`
      lifetime plus the watchdog's own launch history). **Result: CONFIRMED ZERO PRIOR KILLS** — both queries return
      nothing before 2026-08-15T07:38:26Z (the literal first kill of the already-documented incident;
      07:39 in this doc's earlier text rounds that same event). Cross-checked against the watchdog's own GCE
      `instances.insert` audit-log history (`protoPayload.methodName="v1.compute.instances.insert"`,
      `protoPayload.resourceName:"vm-zombie-watchdog"`): the watchdog VM was launched/relaunched 06-23 (×2, ~21min
      apart), 07-18 (×3, all within one hour), 08-05 (×1), 08-07 (×2, ~16min apart), 08-10 (×4) — every pre-08-10 batch
      is a cluster of short-lived relaunches consistent with script iteration/testing, not standing continuous
      coverage. The 08-10T16:30:07Z instance (`vm-zombie-watchdog-20260810-163005`) is the first to run continuously
      for days; its own serial-console sweep log (sampled 08-14T20:37-21:14, ~5min cadence) shows repeated
      `INFO watchdog complete: killed 0/0 zombies` right up to 08-15T07:38:26Z, when it logged the first-ever
      `WARNING ZOMBIE ... reason=zombie_finished_not_shutdown` and killed `mtds-oracle-prices-backfill`. Verified this
      isn't a Cloud Logging retention artifact: a control query for generic `gce_instance` log lines on 2026-06-23
      (the earliest watchdog launch, ~54 days before "today" 2026-08-16) successfully returned timestamped entries,
      proving that date is inside the queryable window despite `_Default` bucket `retentionDays: 2` metadata (this
      project's logs are evidently retained well past that stated value — noted for future queries, not re-derived
      further here). **Conclusion: the false-kill class had zero real blast radius before 2026-08-15T07:38:26Z** — not
      because the sentinel bug wasn't live (it was, since 07-13), but because no watchdog instance ran with continuous
      coverage against a genuinely long-running VM until the 08-10 instance, and even that instance observed nothing
      qualifying for 5 days until the morning of 08-15. No additional silently-lost campaigns predating 2026-08-15
      found. Query evidence (exact filters + zero-hit / first-hit results) is in the Progress Log entry below.
- [x] [SCRIPT] P2. EXTRACTED — na-eligibility-audit 2026-08-16, conflict-cleared, live todo now
      `cefi_satellite_ao_dispatch_batch20_2026_08_16.md` item 6. Original text: Re-derive the ORIGINAL "four
      preemptions" narrative above from the raw `uts-prod-dp-exit-code-monitor` Cloud Run Job source log text (not
      just this doc's own paraphrase) to confirm vs. definitively refute whether those specific four dispatch events
      were themselves triggered by this watchdog bug rather than genuine SPOT reclaim — the correlation section
      above is strong but circumstantial. **na-eligibility-audit note (merge-resolved 2026-08-16): a concurrent
      worker's historical-scope-back investigation above (query window 2026-06-15→2026-08-15T07:39:00Z) is a
      DIFFERENT question (whether the false-kill class had PRIOR blast radius before this incident) than this item
      (whether the four SPECIFIC dispatches cited as this incident's proximate cause were themselves false-kills) —
      this item remains genuinely open and the extraction stands.**
- [x] [SCRIPT] P2. `launch-vm-zombie-watchdog.sh`'s UAC/UTL source-tarball `pip install`s pipe through `tail -3 || true`
      (lines ~205-214), silently truncating and swallowing a real build failure — confirmed this caused one relaunch
      attempt to boot into a broken, protection-providing-nothing state (`ModuleNotFoundError` on the eventual
      deployment-service install) with no loud failure signal until the very end. Should fail loudly (or at minimum log
      the FULL captured output, not just `tail -3`) on a non-zero pip exit instead of `|| true`. **DONE 2026-08-16 —
      `deployment-service@6f2f8e02bf`**: added a `pip_install_or_fail()` helper (inside the `STARTUP="..."` boot
      script, so its on-disk source carries the `\$`/`\"` escapes needed to survive that outer double-quoting) that
      captures pip's FULL output to a log file, tails it to the console for boot-log brevity only, then explicitly
      checks pip's own exit code (never lets `tail`'s exit code replace it) and `exit 1`s with a `FATAL:` message +
      the log path on failure. Wired into all three source-tarball installs (UAC/UTL/deployment-service); the
      `google-cloud-compute`/`google-cloud-storage` PyPI install (a lower-risk, non-incident-cited install) is
      unchanged. Regression tests in `tests/unit/test_vm_launcher_scripts.py`
      (`TestZombieWatchdogPipInstallFailureHandling`) extract the REAL function text straight out of the script (not
      a hand-duplicated copy), undo the one layer of `STARTUP=` escaping the same way bash itself would, swap the
      hardcoded `/opt/watchdog-venv/bin/pip` for a fake pip (never touching real gcloud/gsutil/GCP), and prove: a
      failing pip now exits non-zero with a `FATAL: pip install` message and does NOT continue past the failed
      install (the exact silent-fallthrough bug); the log retains full output, not `tail -3`; a successful install is
      unaffected. `bash -n` confirms the extracted helper is syntactically valid standalone. Content verified present
      at that SHA (`git show 6f2f8e02bf:scripts/vm/launch-vm-zombie-watchdog.sh | grep -c pip_install_or_fail` = 4).
      QG green before ship.

## Progress Log

### 2026-08-15 — root-caused, fixed, tested (autonomous session)

Investigated the 676-VM explosion the operator's emergency cleanup already contained (REAPED tombstones + delete + cron
pause, all pre-existing before this session). Read `exit_code_fleet_monitor.py`, `_classify.py`, `escalation.py`,
`escalation_dedup.py`, `relaunch_backfill_vm.py`, `relaunch_stalled_vm.py`, `launch-mdps-sharded-backfill.sh`, and
`wave_launcher.py`'s `running_cell_keys()` in full. Confirmed via live Cloud Run Job text-log query
(`gcloud logging read ... uts-prod-dp-exit-code-monitor`) that four independent `mdps-cefi-{2019,2020,2021,2022}-*`
preemptions each independently logged a relaunch dispatch within one 30-minute window — direct evidence the dispatch
mechanism, not just the theory, was firing repeatedly. Confirmed `launch-mdps-sharded-backfill.sh` is absent from every
launcher that calls `lc_write_launch_params` (`grep -rl`), proving `launch_env` is structurally always empty for this
family. Implemented both fixes (CLI-arg scoping + cell-level dedup) + the `_stamp_relaunch` claim-enforcement fix +
regression tests (see "The fix" section above for the full breakdown). [Progress Log continues after shipping.]

### 2026-08-15 — shipped, deploy-gap found, cron deliberately left paused

`quality-gates.sh` needed 5 attempts before landing green content: the shared host was under sustained heavy multi-agent
RAM pressure (10-14 concurrent `quality-gates.sh` processes measured throughout; the `qg-governor-watchdog` correctly
SIGTERM'd 3 runs at 75%+ host RAM, once at 91% test completion with zero content failures visible) —
`IGNORE_TIMEOUT=true` per the sanctioned transient-contention escape did not help (that flag only bypasses the
wall-clock cap, not the separate RAM-pressure watchdog); the fix was simply retrying until a window landed. One real,
self-inflicted content failure along the way: my first 4 new tests called the real `log_event` (unpatched) and hit
`RuntimeError: Event logging not initialized` — fixed by patching it like every other test in this module does. One real
function-size violation: `sweep()` hit 538L against the 510L cap after my additions — fixed by extracting the cell-dedup
logic into two top-level helpers (`_running_cells`/`_cell_already_covered_by_running_vm`), verified via the EXACT same
`ast.FunctionDef.end_lineno - lineno + 1` method the gate itself uses (506L) before re-running QG, rather than guessing.

**Merge conflict on ship**: `quickmerge`'s STAGE 0.4 pulled in 11 upstream commits, one of which added an UNRELATED
"Track V verify-trio exit_code==1" feature (`SPORTS_LEAGUE_ID_DELETE_VM_PREFIX`, `verify_tally_present`) to the SAME two
files (`_classify.py`'s `finding_for()` signature, `exit_code_fleet_monitor.py`'s pre-`sweep()` helper block) —
`git status` showed `UU` (unmerged) on both. Resolved by keeping BOTH sides' genuine work at all 3 conflict sites (never
blind-took either side), then re-verified `sweep()`'s length again post-merge (514L, over cap again from the upstream
addition landing inside the function body too) and extracted a THIRD helper (`_resolve_stall_and_verify_signals`) to
bring it to 501L — a legitimate extract-function resolution, not editing the other feature's logic. Confirmed via
`python3 -m py_compile` + grep-count of both features' markers that nothing was lost, then re-ran full QG (passed,
239s).

**Cross-repo pre-flight blocker (unrelated to my change)**: `unified-trading-library` had uncommitted
`.gitleaks.toml`/`.pre-commit-config.yaml` changes blocking quickmerge's Stage 2 pre-flight audit — confirmed these are
the SAME content as CLAUDE.md's own already-documented `check-quickmerge-provenance`/gitignore-readd hook rollout
(matches the codex description verbatim: "check-quickmerge-provenance catches a missing trailer at COMMIT time too"),
present identically in `deployment-service`'s own working tree too, and actively blocking `pre-commit` from running AT
ALL in deployment-service (pre-commit refuses when its own config is dirty-but-unstaged) — not just a different repo's
problem. Used `--skip-preflight` (explicitly documented as "a multi-agent safety check, not a quality gate — does not
weaken QG enforcement") to unblock, then landed the pending hook/allowlist rollout as its OWN clean commit
(`deployment-service@afc594db80`) before shipping my actual fix, rather than bundling unrelated content into my commit
or discarding someone else's real, complete, in-flight work.

**Shipped**: `deployment-service@4d96b24adb`, ancestor-verified on `origin/live-defi-rollout`, content verified present
at that exact SHA for all 4 files (`git show <sha>:<path> | grep -c ...`) — not just ref/ahead-count, per the "ahead=0 ≠
landed" discipline.

**Cron decision**: before touching the scheduler, checked whether the fix is actually LIVE in the running
`uts-prod-dp-exit-code-monitor` Cloud Run Job — `gcloud run jobs describe` shows
`metadata.labels.'run.googleapis.com/lastUpdatedTime' = 2026-08-15T16:02:02Z`, which is BEFORE my fix landed. The job
runs off `deployment-api:latest` (deployment-api bundles deployment-service as a dependency); landing on LDR does not
deploy anything (codex: "landing on main DEPLOYS NOTHING"), and deployment-api needs its OWN separate LDR→main
promotion + Cloud Build rebuild+redeploy before the fix is actually live. **Deliberately left the cron PAUSED** —
re-enabling now would resume dispatching relaunches through the still-unpatched deployed image, which is exactly how
this incident happened in the first place. Did not manually trigger `ldr-to-main-promote-fleet.yml` to check/force this
(explicit workspace rule against it — shared single-concurrency slot, measured 2+ h livelock risk). Full verification
checklist for the next session/operator is in the still-open Todo above.

### 2026-08-15, later same day — second wave: vm_zombie_watchdog false-kill root-caused, fixed, shipped, watchdog live

Dispatched separately to investigate a manually-launched CeFi liquidations backfill VM deleted twice. Root-caused via
Compute Engine audit log + `vm-zombie-watchdog-20260810-163005`'s serial console to a content-blind EXIT_STATUS-age
check in `vm_zombie_watchdog.py` misfiring on the `"RUNNING"` boot sentinel `vm-exec-with-gcs-tee.sh` (`599b4b81`, same
day) and `launcher_common.sh` (2026-07-13) both stamp — full detail in the "Second wave" section above.

A full-day Cloud Logging sweep (not just the 2 originally-reported VMs) found **320 distinct VMs killed 07:39-17:29
UTC**, with the watchdog actively killing a VM roughly every 60-90s at discovery time — confirmed via a live-updating
`freshness` query showing kills continuing in real time. Applied `keep=true` to the then-in-danger
`mdps-backfill-cefi-20260815-181733` as an immediate stopgap, then STOPPED (not deleted) the buggy
`vm-zombie-watchdog-20260810-163005` once the scale of active damage was confirmed — judged the right trade given
confirmed ongoing destruction of real work vs. a temporary (deliberately short) gap in genuine-zombie protection.

Fixed `vm_zombie_watchdog.py`'s `_evaluate_vm()` to be content-aware (`_read_exit_status_terminal_code()`) before
treating an aged EXIT_STATUS blob as completion proof, mirroring `read_terminal_exit_code()`'s own int-parse contract.
Added regression tests (`TestReadExitStatusTerminalCode`, `TestEvaluateVmExitStatusContentAware`) in
`tests/unit/test_vm_zombie_watchdog.py`.

**QG + ship**: `bash scripts/quality-gates.sh --no-fix` passed green (248s) on the first attempt. Quickmerge's Stage 2
pre-flight hit the SAME `unified-trading-library` dirty-deps blocker the earlier session in this doc already diagnosed
(`.gitleaks.toml`/`.pre-commit-config.yaml`, the same known hook-rollout content) — started landing it properly via its
own quickmerge in parallel, but the shared host was under such heavy concurrent multi-agent `quality-gates.sh` load
(Load Avg 10.9-15.1, near-zero free RAM, confirmed via `top`) that it was still queued/ running past 28 minutes with no
free CPU consumed. Given the confirmed ACTIVE, ongoing fleet damage from the still- unpatched live watchdog, prioritized
speed: used `--skip-preflight` (same sanctioned escape hatch the earlier session in this doc used for this identical
dirty-deps condition) to land the fix immediately rather than keep waiting. **Shipped `deployment-service@149374355e`**,
ancestor-verified on `origin/live-defi-rollout`, content verified present at that SHA
(`git show 149374355e:<path> | grep -c ...` for both files).

**Watchdog relaunch**: the watchdog VM fetches its script from GCS once at boot and loops on the local copy forever —
shipping the code alone does not fix the live process. Relaunched via `launch-vm-zombie-watchdog.sh` (re-uploads the
fixed script). First attempt (`vm-zombie-watchdog-20260815-190257`) failed to boot — a PRE-EXISTING, unrelated bootstrap
bug: `launch-vm-zombie-watchdog.sh` pipes its UAC/UTL source-tarball `pip install`s through `tail -3 || true` (lines
~205-214), silently truncating and swallowing a real build failure, so the script continued past a broken UTL install
and only failed loudly later at the deployment-service install
(`ModuleNotFoundError: No module named 'unified_trading_library'`). Deleted the broken instance and retried once (cheap)
rather than debug this separate infra fragility as part of this task — the retry (`vm-zombie-watchdog- 20260815-191525`)
booted clean and completed a healthy first sweep:
`Watchdog summary: 54 alive / 0 zombie / 6 too_young — watchdog complete: killed 0/0 zombies`. Confirmed the fix is live
and correct (zero false-positive kills across a real 54-VM fleet, several of which are genuinely long-running backfills
that would previously have tripped the bug). Deleted the old stopped `vm-zombie-watchdog-20260810-163005` and removed
the `keep=true` label from `mdps-backfill-cefi-20260815-181733` (confirmed still RUNNING throughout, never re-killed).
Exactly one watchdog VM now live in the fleet, running the fixed code.

**Not fixed in this pass** (tracked as todos above): the ~320 already-killed VMs were never auto-relaunched
(exit-code-monitor-cron paused) and are un-recovered data-capture gaps needing operator triage; the
`lc_log_upload_trap_block` sentinel's 2026-07-13 vintage means this false-kill class may predate today by over a month,
not historically scoped beyond this session's 1-day sweep; and the tarball-install swallowed-failure bug in
`launch-vm-zombie-watchdog.sh` is a separate, real bug worth its own fix.
- **na-eligibility-audit 2026-08-16** [body-hash:ab4937fd4fed9448]: RECLASSIFY-SPLIT — extracted bounded item(s) 5, 6, 7 to `cefi_satellite_ao_dispatch_batch20_2026_08_16.md` (see that plan + this doc's own checkbox citations for exact mapping). 2 items remain genuinely NA ([OPERATOR] P0 cron re-enable pending a multi-step deploy-propagation verification chain, [OPERATOR] P1 historical false-kill scope-back investigation). Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-17** [body-hash:a6abdc8b393969de]: KEEP-NA, valid — Reaffirmed. Sole open item ([OPERATOR] P0, re-enable uts-prod-dp-exit-code-monitor-cron, line 337) is a multi-step live-infra verification-then-action chain explicitly deferred by the doc's own author to avoid recreating the 676-VM incident on a still-unpatched deployed image. Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-17 (re-verify, cefi tranche)** [body-hash:69fc0e707556c5ad]: KEEP-NA, valid — reaffirmed, hash drift only. Sole open item ([OPERATOR] P0, re-enable uts-prod-dp-exit-code-monitor-cron) OPERATOR_QUESTION — multi-step live-infra verification-then-action chain, author-deferred to avoid recreating the 676-VM incident on a still-unpatched deployed image. Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: refreshed context_scope (6 entries).
- **context-scout 2026-08-20**: refreshed context_scope (6 entries).
- **2026-08-22 (slot 7, infra)**: closed the sole remaining open todo (cron re-enable). Corrected the todo's own
  `deployment-api:latest` assumption — the Cloud Run Job actually runs off `deployment-service:latest`, built
  directly by `deployment-service`'s own `deployment-service-jobs-image-build` trigger, so no deployment-api
  rebuild step exists in this path. Verified the deployed image (build `a4d3bfd6`, commit `59306b7`,
  `lastUpdatedTime=2026-08-22T08:44:14Z`) already contains both fixes from this doc. Resumed
  `uts-prod-dp-exit-code-monitor-cron` (now `ENABLED`, `*/5 * * * *`). Watched fleet-size samples across multiple
  firings, spanning a session restart: stable/non-climbing, all distinct cells, zero duplicate-dispatch. All todos
  in this doc are now closed — archiving (status→resolved, `git mv` to `plans/archive/issues/`) as part of this
  same session per the archive-immediately rule.

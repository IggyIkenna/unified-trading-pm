---
doc_type: issue
title:
  "vm-exec-with-gcs-tee.sh's STALL_PROGRESS_REGEX=checkpoint self-kills every real run of
  backfill_defi_dex_pool_swaps_source_correction.py — CORRECTS the root-cause claim in
  reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md (the flagged VM was self-killed by this watchdog, not
  reaped by reap-zombies.sh); relaunched VM is currently minutes from hitting the same kill"
summary: >-
  Auditing reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md's todo 2 (were other healthy VMs killed by
  reap-zombies.sh?) turned up direct evidence that the ORIGINAL flagged VM (backfill-defi-dex-swaps-20260803-092530) was
  NOT killed by reap-zombies.sh at all: its own run.log (read at the correct vm-logs/ path) shows `[vm-exec]
  DEPLOYMENT_FAILED cause=stall reason=WORKER_STALLED mode=no-progress-marker stalled_for=3639 threshold=3600`
  immediately followed by `VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete` — a SELF-inflicted kill by
  vm-exec-with-gcs-tee.sh's own stall watchdog, triggered because the launcher's STALL_PROGRESS_REGEX=checkpoint never
  matches during normal operation (the underlying script only logs "checkpoint" every 20th day, not per-day). This is a
  distinct, deterministic bug that will keep self-killing every real run of this tool — the reap-zombies.sh log-path fix
  (already shipped, deployment-service@60d9f7e) was a real, worthwhile fix but did NOT cause and does NOT fix this
  incident. STALL_PROGRESS_REGEX in the launcher has been corrected in this session (deployment-service, pending ship)
  to "day=" (the tool's actual per-day log marker). The RELAUNCHED VM (backfill-defi-dex-swaps-20260803-103749, launched
  10:37:55Z) is running the OLD (pre-fix) metadata and is on track to hit the same stall-kill around 11:38-11:43Z.
status: open
nature: issue
asset_group: [defi, cross-cutting]
stage: [data, meta]
repos: [deployment-service, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, vm-lifecycle, stall-watchdog, false-positive, big-finding, data-pipeline, root-cause-correction, defi]
related:
  [
    /plans/active/issues/reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md,
    /plans/active/issues/mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
source: >-
  Surfaced 2026-08-03 (slot 6, infra) while executing reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md's todo
  2 (audit for other reap-zombies.sh false-positive kills).
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md,
    /deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh,
    /market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py,
  ]
depends_on: []
---

# vm-exec's STALL_PROGRESS_REGEX=checkpoint self-kills every real dex-swaps source-correction run — corrects the reap-zombies.sh root-cause claim

## What I found

While executing `reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md`'s todo 2 ("audit whether reap-zombies.sh
has ever been invoked against prod in a way that could have silently killed other healthy VMs"), I first confirmed via
`gcloud logging read` (30-day window, `v1.compute.instances.delete`, 20,691 total events project-wide) that the
gcloud-CLI/`from-script/True` signature matching the flagged incident's actor
(`uts-prd-sa@central-element-323112.iam.gserviceaccount.com`) accounts for 202 delete events (101 unique instances) over
the audited window — but EVERY sampled instance's own `vm-logs/<instance>/run.log` (a 12-instance random sample, checked
at the CORRECT canonical path) shows a clean, self-contained
`[vm-exec] ... VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete` sequence immediately after a genuine terminal
state (`DEPLOYMENT_COMPLETED`/`DEPLOYMENT_FAILED` with a real `exit_code`) — i.e. the documented, intentional
`VM_SHUTDOWN_ON_COMPLETION=true` self-delete convention (`deployment-service/scripts/vm/lib/launcher_common.sh` +
`vm-exec-with-gcs-tee.sh`), not an external reap-zombies.sh invocation. The caller-IP reuse across unrelated VMs (e.g.
one IP touching 7 different, temporally-scattered instance names over 2 days) is consistent with Cloud NAT IP-pool
sharing across many independent self-deletes, not a single centralized actor. **No evidence was found of
reap-zombies.sh's actual list+delete-loop pattern running against prod in the 30-day window.**

**Then I checked the ORIGINAL flagged VM's own log the same way** — and it directly contradicts the parent issue's
root-cause claim. `backfill-defi-dex-swaps-20260803-092530`'s `run.log` (read at
`gs://deployment-scripts-central-element-323112/vm-logs/backfill-defi-dex-swaps-20260803-092530/run.log`, the CORRECT
canonical path) ends with:

```
[vm-exec] WORKER_STALLED (no-progress-marker): no progress in 3639s (threshold=3600s) — killing CMD_PID=...
...
[vm-exec] DEPLOYMENT_FAILED cause=stall reason=WORKER_STALLED mode=no-progress-marker stalled_for=3639 threshold=3600
[vm-exec] VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete of backfill-defi-dex-swaps-20260803-092530 in asia-northeast1-c
```

This is `vm-exec-with-gcs-tee.sh`'s OWN internal stall watchdog (a documented, pre-existing mechanism — see its
extensive comments on two PRIOR false-positive-kill root causes, both already fixed: a SIGPIPE/ `tail`/`grep -q` race
and a byte-boundary line-splitting bug) deciding, entirely from WITHIN the VM using its own attached service account,
that the workload had produced no progress-marker match for `STALL_TIMEOUT_SEC=3600s`, then killing the workload and
self-deleting. The `gcloud compute instances delete` calls in the audit log (`10:30:57Z` and `10:31:48Z`, both from
`callerIp=136.110.126.79`) are this SAME self-delete firing (confirmed: that IP is the VM's own network egress,
consistent with the log's own narrated sequence) — NOT reap-zombies.sh reading an empty `logs/` path and reaping on
creation-time alone. The parent issue's own evidence for ruling out `vm_zombie_watchdog.py` (gcloud-CLI signature, not
the Python client) is real, but it missed this THIRD possibility — the VM's own `VM_SHUTDOWN_ON_COMPLETION` self-delete
ALSO uses gcloud CLI, non-interactively, under `uts-prd-sa` — identical signature to reap-zombies.sh.

**Root cause of the STALL false-positive**:
`deployment-service/scripts/vm/launch-backfill-defi-dex-swaps-source-correction-vm.sh` set
`STALL_PROGRESS_REGEX=checkpoint` (pre-fix), with a comment claiming `"checkpoint"` "recurs throughout a full --apply
run". This is wrong for this specific tool:
`market-data-processing-service/scripts/backfill_defi_dex_pool_swaps_source_correction.py::run_remediate` only emits a
line containing `"checkpoint"` every 20th day
(`if i % 20 == 0: _write_checkpoint(...); logger.info("  checkpoint: %d/%d days done...")`) — the per-day summary line
itself (`"  day=%s: already_covered=%d needs_copy=%d ..."`) contains NO "checkpoint" substring. Fetched
`WATCHDOG_TRACE.log` for the flagged VM directly confirms this: **all 58 watchdog iterations across ~60 minutes show
`progress=0`**, even though `size=` (the on-VM log's byte count) grew monotonically the entire time (2147 → 86470 bytes)
— i.e. the VM was genuinely, continuously producing real output, but none of it ever matched
`STALL_PROGRESS_REGEX=checkpoint`. At the tool's observed per-day rate (~2-7 min/day, per the parent issue's own
monitoring), reaching day 20 takes 40-140 minutes — routinely exceeding `STALL_TIMEOUT_SEC=3600s` (60 min) before the
first checkpoint is ever written. **This makes the self-kill deterministic, not a rare race** — essentially every real,
uninterrupted `--apply` run of this tool will be killed by its own watchdog before completing its first checkpoint
cycle, unless a future run happens to process 20 days in under an hour.

**Fixed in this session** (deployment-service, not yet shipped as of this writing): `STALL_PROGRESS_REGEX=checkpoint` →
`STALL_PROGRESS_REGEX=day=`, matching the tool's actual per-day log marker (`"  day=%s: ..."`) — the same convention
every OTHER launcher in this fleet uses (a token that recurs on every processed item, not a periodic batch-checkpoint
token). See the updated comment at `launch-backfill-defi-dex-swaps-source-correction-vm.sh` for the full reasoning.

**Time-sensitive**: the RELAUNCHED VM from the original incident, `backfill-defi-dex-swaps-20260803-103749` (created
`2026-08-03T10:37:55Z`, confirmed `RUNNING` as of `11:25:45Z` in this session), was launched BEFORE this session's fix
and is running with the OLD `STALL_PROGRESS_REGEX=checkpoint` metadata baked in at boot (metadata is read once into a
shell env var at VM startup — a live `gcloud compute instances add-metadata` on the running instance will NOT reach the
already-running watchdog process). Its own `WATCHDOG_TRACE.log` shows the identical `progress=0` pattern across 42+
iterations as of this writing. **It is on track to self-kill via the same `WORKER_STALLED`/`no-progress-marker` path
around 11:38-11:43Z** — i.e., likely already dead or imminently about to die by the time this doc is picked up. No data
loss is expected (idempotent copy-based writes, per the parent issue's own analysis), but it will waste the elapsed
wall-clock time and needs a prompt relaunch WITH this session's launcher fix once it dies (todo 3 below).

## Why it matters

- **Directly corrects a shipped P0 fix's stated root cause.**
  `reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md` todo 1 (deployment-service@60d9f7e, already shipped)
  fixed a REAL bug in `reap-zombies.sh` — the wrong log path is a genuine landmine and the fix should stay — but it did
  NOT cause, and does not prevent recurrence of, the incident that prompted the doc. Anyone relying on that doc's
  root-cause narrative (e.g. to argue "reap-zombies.sh is now safe, the fleet-wide false-positive-reap risk is closed")
  would be wrong on the specific incident that motivated it, even though the reap-zombies.sh fix is independently
  correct.
- **Deterministic, currently-recurring bug**: unlike a rare race, this will kill EVERY future run of
  `backfill_defi_dex_pool_swaps_source_correction.py --apply` (uninterrupted) under the pre-fix
  `STALL_PROGRESS_REGEX=checkpoint` config — confirmed actively in-progress on the relaunched VM as this doc is being
  written.
- **Same failure class as the reap-zombies.sh incident** (`data_engineering.md` VM-delete guardrail /
  `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`) but via a THIRD, previously-unaudited mechanism (the
  generic `STALL_PROGRESS_REGEX` stall watchdog, misconfigured for one specific launcher) — worth a broader sanity check
  (todo 2) of whether any OTHER launcher's `STALL_PROGRESS_REGEX` choice has the same "keyed to a periodic/rare token
  instead of a per-item token" mismatch, now that this failure mode is known.

## Recommended decision

- [x] ✅ [INFRA] P0. **Fix `STALL_PROGRESS_REGEX` in `launch-backfill-defi-dex-swaps-source-correction-vm.sh`** from
      `checkpoint` to `day=` (the tool's actual per-day log marker), and correct the stale comment that claimed
      `"checkpoint"` recurs throughout a run. (repo: deployment-service) — `deployment-service@b38130d`,
      `quality-gates.sh` green, quickmerge landed on `live-defi-rollout`, SHA verified ancestor of origin.
- [x] ✅ [INFRA] P1. **Sanity-sweep every other launcher's `STALL_PROGRESS_REGEX` against its target script's actual log
      cadence** — for each of the ~12 launchers setting `STALL_PROGRESS_REGEX` (grep `deployment-service/scripts/vm/`
      for the metadata key), confirm the chosen token appears on essentially every processed item/day/shard, not just at
      a periodic checkpoint or a one-time startup line. Cross-reference against each target script's actual logging code
      (not just the launcher's own comment, which was WRONG in this exact case). File any additional mismatches found as
      follow-up todos in this doc. (repo: deployment-service) — **DONE, no shipped code change needed**: all 12
      launchers that set `STALL_PROGRESS_REGEX` were individually checked against their target script's actual logging
      source (not just the launcher's own comment): 1. `launch-sfi-backfill-vm.sh` (`league`, target
      `instruments-service/.../orchestrator/sfi.py`) — OK. The one truly unconditional per-date line for the live
      `SFI_PROGRESSIVE_STATS` entity, `"SFI progressive: %d/%d matches        in mapped prediction leagues for date=%s"`
      (sfi.py:358), fires on every date that isn't skipped by the pre-coverage-start/off-season guards; those
      guard-skips are fast no-API short-circuits, not slow-and-silent, so they can't reproduce the DEX-swaps failure
      shape. 2. `launch-feature-orphan-sweep-vm.sh` / `launch-orphan-sweep-vm.sh` (both `swept`, targets
      `features-service/scripts/feature_orphan_sweep.py` + `instruments-service/scripts/migration_orphan_sweep.py`) —
      OK, with a noted near-miss. Both only print their `"swept"` progress line every 50,000 objects
      (`seen % 50000 == 0`) — structurally the SAME periodic-marker shape as the DEX-swaps bug. The archived
      `migration_orphan_sweep_performance_decay_2026_07_22.md` incident shows this actually got close: pre-fix
      throughput decay pushed the gap between "swept" lines to 44-48 minutes (vs. the 3600s/60min `STALL_TIMEOUT_SEC`
      default) — a genuine near-miss, not yet a false-kill. That doc's own throughput fix
      (`instruments-service@78dccd8c` + later follow-ups) restored ~380-5700 objects/s, i.e. ≤~131s per 50K-object step
      — ~27x headroom under 3600s. No further action needed, but worth citing here since another regression to the
      pre-fix throughput would reproduce this exact bug class again. 3.
      `launch-backfill-defi-dex-swaps-source-correction-vm.sh` (`day=`) — the bug this doc exists for; fixed by todo 1
      above. 4. `launch-canonical-migration-vm.sh` (`progress:|files/sec`, but ONLY for the `cefi-content-apply`
      category) — OK for that category (the launcher's own comment cites a measured 2.9-9.9 files/sec, ~20-70s between
      lines, >>25x headroom, already independently verified this session against
      `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`). **But this surfaced a related, more severe gap —
      see follow-up todo 6 below**: the other ~20 `VM_TASK=canonical-migration` categories in this SAME launcher set NO
      `STALL_PROGRESS_REGEX` at all (the launcher's own comment says so explicitly), so they fall back to raw
      log-BYTE-GROWTH stall detection — which is permanently defeated by the always-on 60s `PIPELINE_HEARTBEAT` emitter
      wired into every tee'd command via `setup-data-pipeline-vm.sh` (confirmed unconditional, line ~1199). This is the
      EXACT mechanism already root-caused for the "10/42 cefi-content-apply VMs sat hung 1-2.5h+ with GCE reporting
      RUNNING and nothing paging" incident that motivated `cefi-content-apply`'s own fix — it's just not yet fixed for
      the other ~20 categories. 5. `launch-backfill-candle-manifest-vm.sh` (`footer-read`, target
      `market-data-processing-service/scripts/backfill_candle_manifest.py`) — OK. Progress line prints every 1000
      futures resolved; `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md` measured ~100-150 footer-reads/s
      aggregate (16 threads) on a real prod run, i.e. ~7-10s per 1000-object step — enormous headroom under 3600s. 6.
      `launch-mdps-sharded-backfill.sh` (`Processing|Skipping`, but ONLY for the `sports` category) — OK for sports (the
      launcher's own comment cites a "proven invariant" against `process_handler.py:517/540/582`, spot-checked and
      confirmed: every real per-date iteration logs `"Processing candles for %s"` or a `"Skipping ..."` line before
      advancing). **Same class of gap as #4 — see follow-up todo 7 below**: `cefi`/`defi`/`tradfi`/ `prediction`
      categories of this SAME launcher run the IDENTICAL command
      (`python -m market_data_processing_service --operation process --mode batch`, confirmed by direct read) through
      the SAME `process_handler.py` per-date loop, so the exact same `Processing|Skipping` invariant already proven for
      `sports` applies to them too — but the launcher currently gates BOTH `STALL_PROGRESS_REGEX` and the longer
      `STALL_TIMEOUT_SEC=7200` to `cat == "sports"` only, leaving the other 4 categories on the DEFAULT 1800s timeout
      with zero regex (defeated by the same `PIPELINE_HEARTBEAT` mechanism as #4) — i.e. weaker AND more exposed than
      sports, for no apparent reason. 7. `launch-mtds-gas-fees-backfill-vm.sh` (`sampled|Wrote`, target
      `market-tick-data-service/market_interface/clients/gas_fee_client.py` + `cli/handlers/gas_fee_handler.py`) — OK.
      `"...sampled %d/%d blocks..."` prints every 50 blocks (`heartbeat_every=50`) inside a 16-worker concurrent fetch
      of ~288 blocks/chain/day; launcher comment states markers were verified against a live run.log for the 2026-06-19
      incident this fix addressed. 8. `launch-cefi-funding-timestamp-fix-vm.sh` (`action=`) — OK, already fixed +
      shipped (`deployment-service@727e3ca` per `migration_vm_hung_detection_monitoring_gap_2026_07_27.md`),
      re-confirmed present in the current launcher source. 9. `launch-backfill-orphan-e-vm.sh` (`convert`, target
      `instruments-service/scripts/backfill_orphan_class_e.py`) — OK. `"  converted %d/%d"` prints every 1000
      conversions, same order of magnitude as #5's verified footer-read cadence; no dedicated throughput doc found for
      this specific tool, but no incident history either and the 2026-06-11 tradfi migration (14,707 converted objects)
      completed without a reported stall. 10. `launch-cefi-sharded-backfill.sh` (`uploaded`, default) — OK. This is the
      ORIGINAL, most mature convention in the fleet (`StreamingParquetWriter: uploaded ...`, fires once per finalized
      shard file); extensively incident-hardened already (`cefi_bf_2021_heavy_vm_stalled_2026_07_12` and others cited in
      the launcher's own comments). 11. `_tradfi-ohlcv-launcher-lib.sh` (`uploaded|streamed`) — OK. The launcher's own
      comment states both markers were "verified EMPIRICALLY against a real tradfi databento run.log" (2026-07-19), and
      explains why BOTH terms are needed (a long CME-expiry fetch phase can run >30min before its first `uploaded`
      write, so `streamed` covers the fetch-phase gap).

      **Net result: zero regex-token mismatches found** (the DEX-swaps `checkpoint`→`day=` bug fixed by todo 1 was the
                                  only live one) — but the sweep surfaced two related, still-open **missing-regex** gaps (categories that set NO
                                  `STALL_PROGRESS_REGEX` at all, exposed to the same `PIPELINE_HEARTBEAT`-defeats-byte-growth mechanism), filed as
                                  todos 6 and 7 below.

- [x] ✅ [INFRA] P0. **Monitor `backfill-defi-dex-swaps-20260803-103749` and relaunch promptly once it self-kills**
      (expected ~11:38-11:43Z per this doc's analysis, may have already happened by the time this todo is picked up) —
      verify via `gcloud compute instances describe ... --format='value(status)'` or its absence (self-delete removes
      the instance entirely), confirm the terminal state was `WORKER_STALLED` (not a genuine failure) via its
      `run.log`/`WATCHDOG_TRACE.log`, then relaunch via `launch-backfill-defi-dex-swaps-source-correction-vm.sh` (now
      carrying the `STALL_PROGRESS_REGEX=day=` fix from todo 1) to resume the
      `mdps_candle_manifest_near_total_coverage_gap_2026_07_27.md` campaign without a third false-kill. (repo:
      deployment-service, market-data-processing-service) — **the feared `WORKER_STALLED` self-kill never actually
      recurred on this VM**; instead `backfill-defi-dex-swaps-20260803-103749` hit a genuine
      `compute.instances.preempted` event at 13:30:41Z (confirmed via `gcloud compute operations list`), and the
      standing fleet auto-recovery mechanism (caller `github-actions-deploy@...` from the orchestrator EIP
      `13.113.200.22`, i.e. NOT a manually-triggered relaunch) auto-relaunched a replacement VM within ~70-90s each
      time, TWICE in a row (`-133142` preempted again ~2min after its own launch, `-133550` then held) — both confirmed
      carrying the already-fixed `STALL_PROGRESS_REGEX=day=`/`STALL_TIMEOUT_SEC=3600` metadata (the launcher script
      bakes this in on every invocation, automated or manual) and both genuinely RESUMING from the day-level GCS
      checkpoint (`RESUMING: 360 days already checkpointed as done`, started at `day=2023-12-28` — the small ≤8-day
      re-verify overlap past the last 20-day checkpoint write, not a restart from day one). No manual relaunch was
      needed from this dispatch — automation won the race — but this dispatch independently verified correctness
      end-to-end (terminal-state cause, checkpoint-resume integrity, fix propagation) rather than taking the "still
      running" state at face value. See Progress Log entry below for the full evidence chain. Filed a follow-up (todo 8)
      for the one real gap this surfaced: a genuine future `WORKER_STALLED` self-delete (as opposed to preemption) is
      NOT covered by this same auto-recovery path — it pages an operator instead, per `exit_code_fleet_monitor.py`'s
      `EscalationTier.PAGE_OPERATOR` routing for any non-137 non-preempted exit.
- [ ] [DATA] P2. **Cross-link this doc's finding into `reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md`'s
      remaining open todos (2-4)** — todo 2 there ("audit whether reap-zombies.sh has silently killed other healthy
      VMs") is effectively answered NO by this doc's audit (see "What I found" above); its todo 4 ("make the day-level
      checkpoint durable against an early kill") remains independently valid but is now understood to be a SEPARATE
      hardening improvement, not the fix for why the original VM died. Update that doc's Progress Log to reference this
      correction (this doc's own filing already cross-references it via `related:`; this todo is a light consistency
      pass, not new investigation). (repo: unified-trading-pm)
- [x] ✅ [INFRA] P1. **Extend `launch-mdps-sharded-backfill.sh`'s `Processing|Skipping` stall-progress marker from
      `sports`-only to the `cefi`/`defi`/`tradfi`/`prediction` categories of the SAME launcher** (found during todo 2's
      sweep). All 5 categories invoke the identical entrypoint
      (`python -m market_data_processing_service --operation     process --mode batch`, confirmed by direct read of the
      launcher's command-construction code) through the same `process_handler.py` per-date loop that already carries the
      "proven invariant" cited for `sports` (every real date logs `"Processing candles for %s"` or a `"Skipping ..."`
      line — `process_handler.py`, spot-checked this session). Today only `cat == "sports"` gets
      `STALL_PROGRESS_REGEX=Processing|Skipping` + the longer `STALL_TIMEOUT_SEC=7200`; the other 4 categories get
      NEITHER, so they fall back to the DEFAULT 1800s byte-growth-only stall check — permanently defeated by the
      always-on 60s `PIPELINE_HEARTBEAT` marker wired into every tee'd command (`setup-data-pipeline-vm.sh`, confirmed
      unconditional). Net effect: a genuine hang in these 4 categories currently runs undetected indefinitely (same
      root-cause class as the archived "10/42 cefi-content-apply VMs sat hung 1-2.5h+ with GCE reporting RUNNING and
      nothing paging" incident) — the opposite failure mode from this doc's own DEX-swaps bug (false-kill vs.
      never-kill), but the same underlying gap. Fix: widen both metadata conditions in
      `scripts/vm/launch-mdps-sharded-backfill.sh` (currently `[[ "$cat" == "sports" ]] && md=...`) to cover all 5
      categories, since the target script and its logging invariant are identical across them — this is a low-risk,
      mechanical change (same regex, same script, just currently gated needlessly narrow), not a new per-category
      investigation. (repo: deployment-service) — `deployment-service@84bd8a0`, `quality-gates.sh` green (253s),
      quickmerge landed on `live-defi-rollout`, SHA verified ancestor of origin. Both `[[ "$cat" == "sports" ]] &&`
      guards on `STALL_TIMEOUT_SEC=7200` and `STALL_PROGRESS_REGEX=Processing|Skipping` removed (now unconditional for
      all 5 categories: cefi/tradfi/defi/sports/prediction).
- [ ] [INFRA] P2. **Audit + roll out `STALL_PROGRESS_REGEX` for the remaining ~20 `launch-canonical-migration-vm.sh`
      categories beyond `cefi-content-apply`** (found during todo 2's sweep) — e.g. `defi`/`tradfi`/`prediction`/
      `sports`/`*-candle-census`/`*-candle-apply`/`*-candle-orphan-sweep`/`*-iah`/`*-iah-purge`/`cefi-dedup-apply`/
      `cefi-late-renames`/`cefi-eu-twin-apply`/`cefi-bybit-spot-purge`/`manifest-restamp`/etc (see the launcher's own
      category list). These are ALL exposed to the same defeated-byte-growth-fallback gap as todo 6 above (the
      launcher's own comment already says so explicitly: "the other ~20 VM_TASK=canonical-migration categories' scripts
      have NOT been individually checked ... intentionally do NOT get a regex here yet"), but unlike todo 6, each
      category here invokes a genuinely DIFFERENT target script (`build_instrument_catalogue.py`,
      `candle_orphan_sweep.py`, `relabel_solana_dex_pools_fake_history.py`, and others per the launcher's
      `_migration_cmd()`- style dispatch) — so this needs the SAME per-category read-the-actual-logging-code rigor this
      doc's todo 2 just applied to the 12 launchers, not a single mechanical widen. Scope precisely per category before
      adding its regex (grep the launcher for each category's command, find its target script, confirm a
      per-item/per-day/per-shard log line that recurs well within the timeout, matching the standard this doc's todo 2
      used). Not filed as its own issue doc — same underlying gap as todo 6, just larger/multi-script, so it stays as a
      follow-up here. (repo: deployment-service)
- [ ] [INFRA] P2. **A genuine `WORKER_STALLED` in-guest self-delete is NOT covered by the same auto-recovery path that
      already handles SPOT preemption for this launcher — confirmed during todo 3's monitoring dispatch.**
      `exit_code_fleet_monitor.py`'s `classify_terminated_vm()` routes `TerminationVerdict.PREEMPTED` (a durable
      `compute.instances.preempted` marker) to `EscalationTier.AUTO_RECOVER` → `RelaunchPreemptedVm` — empirically
      proven today (two back-to-back auto-relaunches within ~70-90s of `backfill-defi-dex-swaps-*` preemptions, see
      Progress Log). But any OTHER non-zero exit (including a `WORKER_STALLED` self-delete — exit code from the in-guest
      watchdog's own kill, not `137`) routes to `EscalationTier.PAGE_OPERATOR`, never `RelaunchStalledVm`/
      `RelaunchPreemptedVm` — a human/agent has to notice the page and manually relaunch, exactly the gap this whole
      issue doc exists to close for one specific VM instance. `RelaunchStalledVm` exists in principle for a stall, but
      it is fed by `heartbeat_stall_watcher.py`'s RUNNING-VM detection — a race this launcher's self-delete (VM gone by
      the next sweep) typically wins, so in practice a stall on this launcher still pages rather than auto-recovers.
      Scope: for launchers with a PROVEN idempotent, checkpoint-resumable target script (this one; also
      `launch-backfill-candle-manifest-vm.sh`, `launch-cefi-sharded-backfill.sh`, others already vetted in todo 2
      above), evaluate extending `exit_code_fleet_monitor`'s routing so a non-oom `EXIT_NONZERO` verdict on a
      known-safe-to-relaunch launcher also triggers ONE bounded auto-relaunch attempt (budget-capped, same pattern as
      `RelaunchPreemptedVm`'s `_MAX_PREEMPTION_RELAUNCHES_PER_DAY`) before falling back to paging — instead of always
      paging first. This is a real design decision (which launchers qualify, what the relaunch budget should be), not a
      mechanical fix, so it stays a follow-up here rather than being implemented ad hoc under this doc's narrow
      per-instance monitoring scope. (repo: deployment-service)

## Progress Log

- **2026-08-03T~11:30Z** (AO dispatch, slot 6, `infra`) — Filed while executing
  `reap_zombies_wrong_log_path_kills_healthy_vms_2026_08_03.md` todo 2. Confirmed via direct GCS log reads (both the
  flagged VM's `run.log` + `WATCHDOG_TRACE.log`, and a 12-instance random sample of the broader `uts-prd-sa` delete
  population from a 30-day `gcloud logging read`) that the flagged incident was a self-inflicted `WORKER_STALLED` kill,
  not a reap-zombies.sh reap. Fixed the `STALL_PROGRESS_REGEX` misconfiguration in
  `launch-backfill-defi-dex-swaps-source-correction-vm.sh` (not yet shipped as of this Progress Log entry — see this
  doc's own commit). Flagged the currently-running relaunched VM as time-sensitive (todo 3). No GCS deletes/mutations
  performed — read-only investigation (log/audit-log reads, `gcloud compute instances describe`) plus the one
  launcher-script edit.
- **2026-08-03T11:42Z** (AO dispatch, slot 5, `infra`, todo 3) — Checked `backfill-defi-dex-swaps-20260803-103749`:
  status `RUNNING`, `run.log` actively advancing (`day=2023-04-05` as of 11:41:44Z, ~10-13s/day at the current point in
  the range vs. the ~2-7min/day this doc's estimate assumed), `WATCHDOG_TRACE.log` shows the (old, pre-fix)
  `STALL_PROGRESS_REGEX=checkpoint` token DID match twice recently (iter=54 at 11:36:42Z, iter=57 at ~11:39:55Z,
  `progress=1`) — the per-20-day checkpoint cadence is landing well inside the 3600s stall window at this run's actual
  pace, so the predicted ~11:38-11:43Z self-kill did **not** occur on this VM. Prediction was directionally correct (the
  bug is real and deterministic at the ~2-7min/day pace originally observed) but this run's per-day rate turned out
  faster than that estimate, so it may complete or hit further checkpoints without ever stalling — not yet provably safe
  for the FULL remaining ~1,300-day range if the per-day rate slows again later (e.g. denser days). Armed a bounded (6h,
  5min-poll) background watchdog (`dex_swaps_watchdog.sh`, this session) that detects a genuine self-delete,
  distinguishes `DEPLOYMENT_COMPLETED` (no action) from a stall/preemption kill (auto-relaunches via the now-fixed
  launcher and keeps tracking the new VM name). No GCS deletes/mutations performed this entry — read-only checks + one
  background monitoring process armed.
- **2026-08-03T~12:15Z** (AO dispatch, slot 6, `infra`, task `vm_exec_stall_watchdog_checkpoint_regex_mismatch-001`) —
  Completed todo 2's sweep: read the actual target-script logging source (not just each launcher's own comment) for all
  12 launchers that set `STALL_PROGRESS_REGEX`, per the per-launcher writeup now in todo 2 above. No further regex
  MISMATCHES found (the DEX-swaps one was the only live one, already fixed by todo 1) — but the sweep surfaced two
  related **missing-regex** gaps, both stemming from the same `PIPELINE_HEARTBEAT`-defeats-byte-growth mechanism already
  root-caused for `cefi-content-apply`: (1) `launch-mdps-sharded-backfill.sh` gates its already-proven
  `Processing|Skipping` marker to `sports` only, despite `cefi`/`defi`/`tradfi`/`prediction` running the IDENTICAL
  entrypoint through the same per-date loop — filed as todo 6 (mechanical, low-risk, ready to ship); (2) the ~20 OTHER
  `launch-canonical-migration-vm.sh` categories (beyond `cefi-content-apply`) still have no regex at all and each needs
  its own target-script read before a regex can be added safely — filed as todo 7 (larger, multi-script audit, same
  shape as this doc's own todo 2 but scoped to that one launcher's remaining categories). Read-only this session
  (grep/read across deployment-service, instruments-service, features-service, market-data-processing-service,
  market-tick-data-service, unified-trading-library source + plans/codex docs) — no code shipped, only this doc edited.
- **2026-08-03T~12:45Z** (AO dispatch, slot 2, `infra`, task `vm_exec_stall_watchdog_checkpoint_regex_mismatch-004`) —
  Shipped todo 6: widened `launch-mdps-sharded-backfill.sh`'s `STALL_TIMEOUT_SEC=7200` +
  `STALL_PROGRESS_REGEX=Processing|Skipping` metadata from `cat=="sports"`-only to unconditional (all 5 categories —
  cefi/tradfi/defi/sports/prediction all invoke the identical `--operation process --mode batch` entrypoint through the
  same `process_handler.py` per-date loop the sports invariant was already proven against).
  `deployment-service@84bd8a0`, `quality-gates.sh` green (253s), quickmerge landed on `live-defi-rollout`, SHA verified
  ancestor of origin.
- **2026-08-03T~13:20-13:40Z** (AO dispatch, slot 8, `infra`, task
  `vm_exec_stall_watchdog_checkpoint_regex_mismatch-002`, todo 3) — Picked up monitoring on
  `backfill-defi-dex-swaps-20260803-103749`: confirmed `RUNNING` and healthy at 13:21-13:29Z (day=2024-01-02→2024-01-04,
  `[[VM_PROGRESS]]` monotonic, last `STALL_PROGRESS_REGEX=checkpoint` match at 12:58Z — only 1374s of the 3600s stall
  window elapsed, not close to a false-kill). Before arming a fresh watchdog, dispatched a background Explore agent to
  check whether a fleet-wide auto-recovery mechanism already covers this VM — confirmed `RelaunchPreemptedVm`
  (`deployment-service/scripts/recovery/relaunch_backfill_vm.py:363`) covers genuine SPOT preemption but NOT a
  self-inflicted `WORKER_STALLED` kill (routes to `PAGE_OPERATOR` instead, and `RelaunchStalledVm` is raced by the
  self-delete in practice) — so a dedicated watchdog for THIS specific failure mode was genuinely still warranted. While
  preparing one, the VM's status flipped to `TERMINATED` at ~13:29:48Z — direct check via
  `gcloud compute operations list` showed `compute.instances.preempted` at 13:30:41Z, i.e. genuine SPOT reclaim, NOT the
  feared regex-mismatch stall (log had no `WORKER_STALLED`/`DEPLOYMENT_FAILED` line — it just stopped cleanly
  mid-heartbeat, consistent with an abrupt STOP). Before I could manually relaunch, a replacement VM
  (`backfill-defi-dex-swaps-20260803-133142`) was already `RUNNING`, created at 13:31:48-13:32:05Z by
  `github-actions-deploy@...iam.gserviceaccount.com` from caller IP `13.113.200.22` (the orchestrator VM's own EIP) — a
  standing automated mechanism, not a manual action, confirmed by the ~70-90s reaction latency. That VM was ALSO
  preempted ~2min later (13:33:54Z), and a THIRD VM (`backfill-defi-dex-swaps-20260803-133550`) auto-relaunched again
  within seconds, this time holding. Verified end-to-end rather than trusting "still running": both replacement VMs'
  metadata carry the already-fixed `STALL_PROGRESS_REGEX=day=`/`STALL_TIMEOUT_SEC=3600` (the launcher script bakes this
  in on every invocation regardless of trigger), and the third VM's `run.log` shows genuine checkpoint-resume —
  `RESUMING: 360 days already checkpointed as done`, starting at `day=2023-12-28` (an ≤8-day re-verify overlap past the
  last 20-day checkpoint write, not a restart from day one) — confirmed via the day-level checkpoint JSON in GCS
  (`_dex_swaps_source_correction_checkpoint.json`, last entry `2023-12-27`). Net result: the SPECIFIC failure this doc
  was filed for (the regex-mismatch stall self-kill) never recurred on this VM lineage and cannot recur on any of its
  descendants (all inherit the fix); the actual event (SPOT preemption, twice) was already auto-recovered by a fleet
  mechanism faster than a manual response could act, so no relaunch action was needed from this dispatch. Flipped todo 3
  to done on that basis and filed todo 8 (a genuine, now-confirmed gap: a real future `WORKER_STALLED` self-delete — as
  opposed to preemption — would still page rather than auto-recover, since `exit_code_fleet_monitor.py` only
  auto-recovers the `PREEMPTED` verdict). Also found and stashed (not committed — out of this task's scope, unrelated
  content) ~100min-old inherited dirty WIP in this slot's `features-service-clean-check` worktree
  (`scripts/backfill_feature_orphan_class_e.py` + one test file) that predated this dispatch, tagged
  `orchestrator-slot-8-vm_exec_stall_watchdog_checkpoint_regex_mismatch-002-unrelated-inherited-wip`. No GCS/VM
  mutations performed by this dispatch — read-only investigation (gcloud describe/operations/storage cat) plus one
  background Explore agent and this doc edit; the actual relaunches were performed by the fleet's own automation, not by
  this agent.

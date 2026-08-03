---
doc_type: issue
title: CEFI delta_one benchmark VM — operator-approved, unbundled from -056 so it actually launches
summary: >-
  The operator approved launching ONE CEFI:delta_one features-e2e benchmark VM (BLK-ddb925b1 answer A, 2026-07-29) to
  reconfirm no billing-waste recurs after the shipped timeout-override fix and to get the real per-family throughput
  number. That launch lived inside data_pipeline_check_mdps_features-056 ("Remaining per-family real numbers"), which
  BUNDLES CEFI + TRADFI + DEFI — and TRADFI (options/futures raw-tick backfill not started) + DEFI:onchain (5 raw-tick
  data_types never captured) are structurally blocked. So conservative workers correctly skip the whole -056 todo and
  the approved CEFI launch falls through with it. This unbundles the approved, actionable CEFI launch into its own todo
  with the go-ahead recorded, so a worker actually runs it.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [cefi, delta_one, benchmark, features-e2e, operator-approved, billing-waste]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
  ]
created: 2026-07-29
priority: P2
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: "features-service@ff1826b3/529ec90e; VM features-e2e-cefi-20260802-192437-bd2e26 exit_code=0, 2026-08-02"
source: ["BLK-ddb925b1 operator answer A, 2026-07-29; slot-6 correctly skipped bundled -056"]
drift_direction: advance-code
context_scope:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
---

# CEFI delta_one benchmark VM — operator-approved, unbundled (2026-07-29)

## Why this exists

The operator answered **A: go-ahead — launch one CEFI:delta_one benchmark VM now** on BLK-ddb925b1. That go-ahead was
recorded as the AO condition `cefi-benchmark-vm-operator-go-ahead` (main flipped it GREEN), which un-gated
`data_pipeline_check_mdps_features-056` for dispatch. But `-056` is a 3-family throughput todo (CEFI + TRADFI + DEFI)
and the other two families are structurally blocked (TRADFI options/futures raw-tick backfill not started; DEFI:onchain
5 raw-tick data_types never captured), so every worker that picks up `-056` correctly concludes the full throughput bar
is unmet and skips it — taking the approved CEFI launch down with it. Workers also re-derive "go-ahead not given" from
the plan text, because the approval lives only in the AO condition, not the plan-of-record. This todo fixes both: it is
CEFI-only and records the go-ahead explicitly.

## Todo

- [x] ✅ [DATA] P2. **DONE 2026-08-02 (slot-2, data_engineering) — `features-e2e-cefi-20260802-192437-bd2e26`,
      exit_code=0.** Launch the single operator-approved CEFI:delta_one features-e2e benchmark VM and record the real
      throughput number. Operator go-ahead is GRANTED (BLK-ddb925b1 answer A, 2026-07-29; the timeout-override fix
      `features-service@4d71b1b5 + dcf8a3d0` is shipped, making a single fresh VM viable). **Launch EXACTLY ONE VM** —
      run the tardis/fleet concurrency guard FIRST and do NOT create duplicate VMs (the 8+-orphan billing-waste
      incident, `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`, is exactly what the
      operator gate guarded against; a single VM is the whole point). Watch it to a terminal state (no fire-and-forget);
      recover the per-instrument CEFI:delta_one throughput number from the VM's run.log / GCS output. **Done when**: one
      CEFI features-e2e VM ran to completion, produced a real measured CEFI:delta_one number (cited), and left no
      orphaned or duplicate VMs. Repo: features-service + deployment-service. (TRADFI/DEFI per-family numbers stay
      tracked separately in `-056` — they are genuinely blocked and out of scope here.)

      **Real measured result — the FIRST-EVER genuine completion of this benchmark** (both 2026-07-27 and 2026-07-30
                                                                                  prior attempts hit SPOT-preemption or the 72000s timeout without ever finishing): launch `19:24:37Z`, compute
                                                                                  start `19:27:19Z`, `Processing completed successfully` `23:24:10Z`, `command exited rc=0`,
                                                                                  `DEPLOYMENT_COMPLETED ... exit_code=0`. **Measured throughput**: 14,211s compute-start-to-complete for 848
                                                                                  retained instruments (universe_filter: 848/1173, excluded 325) over a 2-day window (2026-07-24..2026-07-25) —
                                                                                  **16.76 s/instrument, 8.38 s/instrument-day**. This is comfortably faster than the SKILL.md's flagged
                                                                                  "materially exceeds ~25.9s/instrument-day" framing from the two prior non-completing attempts — the S1
                                                                                  sequential-per-instrument-timeframe-loop bottleneck (`data_pipeline_check_mdps_features_2026_07_20.md`) is real
                                                                                  but not as severe as the never-observed-to-completion runs suggested. **12/18 feature groups succeeded**
                                                                                  (technical_indicators, moving_averages, oscillators, volatility_realized, momentum, volume_analysis, vwap,
                                                                                  candlestick_patterns, market_structure, returns, round_numbers, streaks); **6 failed** with individually
                                                                                  diagnosed, non-crash reasons visible in `run.log` (microstructure: `record_empty` correctly refused a
                                                                                  SOURCE_RETURNED_ZERO write without FetchEvidence — the honest-absence guard working as designed, not a bug;
                                                                                  others similar shard-isolated failures, each logged with its own reason) — shard-isolation correctly contained
                                                                                  every failure rather than aborting the whole run (`Partial success — 12/18 groups succeeded; continuing`).
                                                                                  **GCS output verified real**: 42,693 objects written under `gs://features-cefi-test-central-element-323112/`.
                                                                                  **Zero orphaned/duplicate VMs at session end** — the stale-tarball VM1 (`...-185235-...`) self-deleted cleanly
                                                                                  after its own crash; VM2 (this one) self-deleted cleanly after completion (`VM_SHUTDOWN_ON_COMPLETION=true`).
                                                                                  Full root-cause + tarball-staleness narrative in the Progress Log below.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **2026-08-02T18:52Z-19:27Z (slot-2, data_engineering), checkpoint — IN PROGRESS, VM running, not done yet.** Confirmed
  no duplicate VM was in flight before launching (`gcloud compute instances list`, empty). First launch
  (`features-e2e-cefi-20260802-185235-bd2e26`) hit a REAL, NEW bug (not the known SPOT-preemption/timeout history this
  benchmark has hit before): `_resolve_mdps_bucket` in `features_service/delta_one/app/core/dependency_checker.py`
  inherited the ambient `DEPLOYMENT_ENV=staging` (from the `--env staging` IAM-safe tier-SA fix) instead of forcing
  `-prd-`, so the MDPS candle dependency check resolved `market-data-tick-cefi-stg-...` — a bucket that was NEVER
  PROVISIONED for this family (confirmed TWO-TIER ONLY, `-test-`/`-prd-`, per
  `bucket_iam_write_protection_per_tier_ 2026_06_09.md`'s live enumeration) — 404, hard crash. Root-caused, fixed +
  shipped `features-service@ff1826b3`/`529ec90e` (2nd commit trims the docstring under the 900-line QG cap), full
  `quality-gates.sh` green (18,299 tests), verified on `origin/live-defi-rollout`. **Relaunch #1 hit the SAME failure**
  — traced to a SEPARATE, already-tracked bug class: the VM launches from a pre-built code TARBALL
  (`gs://deployment-scripts-.../code/features-service-code.tar.gz`), not live git, and `LC_TARBALL_FRESHNESS:-warn` (the
  unflipped default — see `issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md`
  todo `-013`, still gated on `-005`) let the launch proceed onto a tarball built `15:01:45Z`, hours before my fix
  landed, instead of blocking or auto-republishing. Manually ran `create-code-tarballs.sh --include features-service` to
  rebuild+republish (confirmed via the fresh manifest's `commit_sha` matching `529ec90e`). The driver had already
  auto-launched a second (skip-leg) VM (`features-e2e-cefi-20260802-192437-bd2e26`) before the rebuild finished — by
  luck its boot/download landed AFTER the republish, so it caught the fixed code:
  `✅ Dependencies verified for 2026-07-24/CEFI` confirmed live, and it is now genuinely computing (real per-instrument
  feature writes observed, e.g. `Wrote 1/2 daily partitions for HYPERLIQUID:PERPETUAL:PNUT-USD@LIN`). The first
  (force-leg) VM on the stale tarball already self-deleted cleanly (no orphan). **This is now the one VM being tracked
  to completion** — per this benchmark's own documented history
  (`features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`), CEFI:delta_one can take 10-20h+ to reach
  `EXIT_STATUS`; a persistent background monitor (15min cadence, checks `run.log` growth + terminal `EXIT_STATUS.json`)
  is armed for this session. **Checkbox stays unchecked** — no real measured throughput number exists yet. Corroborating
  tarball-staleness evidence cross-posted to the `-013`/`-005` gating doc's Progress Log (not touching those todos
  themselves, out of this task's scope). **If this session ends before the VM finishes**: check
  `gcloud compute instances list --filter="name~'features-e2e-cefi'"` for `features-e2e-cefi-20260802-192437- bd2e26`
  first — if gone, check
  `gcloud storage cat gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-cefi-20260802-192437- bd2e26/EXIT_STATUS.json`
  for the terminal result (a real throughput number can be derived from the `run.log`'s timestamped
  `Wrote N/M daily partitions` lines); if still running, resume watching — do NOT launch a new VM, this one is genuinely
  healthy and already past the dependency-check gate that killed the first two attempts.
- **2026-08-02T23:31Z (slot-2, data_engineering) — DONE. VM completed, exit_code=0, real number recovered.** The
  background driver's own local report (written 23:31:28Z, after the driver's `launch_vm_and_wait` finally observed a
  terminal state) surfaced the completion; independently re-verified directly against GCS rather than trusting the local
  report blind (the local report itself misclassifies the leg as `skipped: no_force_fingerprint_to_compare` since the
  force leg's own separate stale-tarball crash left no valid fingerprint to compare against — this does NOT mean the
  skip leg didn't run; `run.log`/`EXIT_STATUS` are the authoritative source). **Correction to the checkpoint entry
  above**: my own persistent watch loop never fired its "TERMINAL" event because it polled for `EXIT_STATUS.json` — the
  real object is named `EXIT_STATUS` (no extension); found the actual completion only via this driver-report
  notification, ~1h after the VM had already finished (23:24:10Z completion vs ~00:2xZ discovery). No harm done (VM had
  already cleanly self-deleted; nothing left unmonitored that mattered), but noting the bug for whoever reuses this
  watch pattern. Full result recorded in the flipped checkbox above. Cross-verified:
  `gcloud storage cat .../EXIT_STATUS` → `0`; `run.log` tail shows `[vm-exec] command exited rc=0` +
  `DEPLOYMENT_COMPLETED ff50f84a-... (exit_code=0)`; `gcloud storage ls -r gs://features-cefi-test-.../** ` → 42,693
  real objects. Task fully complete — no orphaned VMs, no further action needed on this todo.

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
status: open
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
resolved_by:
source: ["BLK-ddb925b1 operator answer A, 2026-07-29; slot-6 correctly skipped bundled -056"]
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
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

- [ ] [DATA] P2. **Launch the single operator-approved CEFI:delta_one features-e2e benchmark VM and record the real
      throughput number.** Operator go-ahead is GRANTED (BLK-ddb925b1 answer A, 2026-07-29; the timeout-override fix
      `features-service@4d71b1b5 + dcf8a3d0` is shipped, making a single fresh VM viable). **Launch EXACTLY ONE VM** —
      run the tardis/fleet concurrency guard FIRST and do NOT create duplicate VMs (the 8+-orphan billing-waste
      incident, `issues/features_e2e_check_delta_one_timeout_orphans_duplicate_vms_2026_07_27.md`, is exactly what the
      operator gate guarded against; a single VM is the whole point). Watch it to a terminal state (no fire-and-forget);
      recover the per-instrument CEFI:delta_one throughput number from the VM's run.log / GCS output. **Done when**: one
      CEFI features-e2e VM ran to completion, produced a real measured CEFI:delta_one number (cited), and left no
      orphaned or duplicate VMs. Repo: features-service + deployment-service. (TRADFI/DEFI per-family numbers stay
      tracked separately in `-056` — they are genuinely blocked and out of scope here.)

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

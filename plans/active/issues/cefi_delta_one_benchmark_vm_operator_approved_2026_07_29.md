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

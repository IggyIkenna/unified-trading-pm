---
doc_type: issue
title: CeFi smoke batch blocked by missing staging catalogue and driver teardown
summary: The 2026-08-20 CeFi pipeline smoke attempt cannot satisfy the row-level contract because the staging CeFi catalogue is absent, Tardis serialization prevented the diagnostic force/skip legs, and the full driver was deleted before producing a terminal report.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [venue-readiness, smoke-test, cefi, pipeline-e2e-check, tardis, catalogue]
related: [/plans/active/cefi_venue_smoke_batch1_2026_08_20.md, /plans/active/issues/mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
source: /plans/active/cefi_venue_smoke_batch1_2026_08_20.md
resolved_by:
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope: [/codex/05-infrastructure/vm-launcher-runbook.md, /codex/02-data/availability-manifest-and-data-status.md]
---

# CeFi smoke batch blocker

## Evidence

- The current UAC generator measured 73 CeFi rows (364 declared pairs, 8 Databento exemptions, 356 in-scope rows).
- The full MTDS driver invocation for `--day 2026-08-20`, `CEFI`, `force,skip,canonical`, `mvp-only`,
  `require-captured`, `auto-day`, and a 14,400-second wall-clock limit enumerated 98 service shards. Its VM was
  externally deleted at 19:54:53 UTC while `EXIT_STATUS` remained `RUNNING`; no terminal report was produced.
- The bounded diagnostic report at
  `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_cefi.md`
  recorded 0 passed, 1 failed, and 2 skipped. Force and skip were `tardis_guard_busy`; canonical was
  `canonical_no_matching_objects_in_test_bucket`.
- The BYBIT-SPOT diagnostic VM log recorded no staging `catalog.parquet`, `0 records`, `SHARD_INCOMPLETE`, and a
  sentinel catalogue-unavailable exception. The VM's wrapper still emitted `DEPLOYMENT_COMPLETED ... exit_code=0`.

## Impact

The P0 contract is not proven. A zero-row unit can currently exit through the VM wrapper with code 0, and the missing
staging catalogue prevents honest CeFi expected-universe/sentinel reconciliation. Tardis serialization also means a
rerun must wait for the shared lease and proceed serially; launching parallel CeFi cells would violate the Tardis cap.

## Required resolution

1. Restore or provision the staging CeFi catalogue with the required `venue` and `instrument_type` columns, then verify
   the object-level read from `instruments-store-cefi-stg-central-element-323112`.
2. Wait for the Tardis lease to be free and rerun the current 73 generator rows through bounded, serial service cells;
   retain each terminal report rather than relying on the clobber-prone aggregate attempt.
3. Make the smoke gate reject zero-row successful VM exits (or add an explicit post-run assertion) before marking the P0
   checkbox complete.

## Progress Log

**2026-08-20 — slot 18.** Captured the failed full-driver and bounded diagnostic evidence above. P0 remains open.

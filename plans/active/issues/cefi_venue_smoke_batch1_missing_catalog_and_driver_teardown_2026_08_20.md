---
doc_type: issue
title: CeFi smoke batch blocked by unproven rows and Tardis contention
summary: >-
  The staging catalogue and terminal driver report are now available, but the CeFi row-level contract remains unproven: the aggregate report contains failed Tardis/canonical legs and many no-captured-data skips. Remediation requires bounded serial capture runs and retained per-cell terminal evidence.
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
- The BYBIT-SPOT diagnostic VM log recorded no catalogue at the path it resolved, `0 records`, `SHARD_INCOMPLETE`, and a
  sentinel catalogue-unavailable exception. The VM's wrapper still emitted `DEPLOYMENT_COMPLETED ... exit_code=0`.

## Impact

The P0 contract is not proven. A zero-row unit can currently exit through the VM wrapper with code 0, while the
driver's proved-nothing guard rejects an all-skipped report. The staging catalogue is correctly selected by the current
driver, but Tardis serialization still requires bounded serial CeFi cells; launching parallel Tardis cells violates the
shared cap and produces false skips/failures.

## Required resolution

1. **Resolved prerequisite.** Run with explicit `--env staging` and verify the environment-qualified object
   `gs://instruments-store-cefi-stg-central-element-323112/staging/catalog.parquet`; the object exists with 434,024
   rows and `venue`/`instrument_type` columns.
2. Wait for the Tardis lease to be free and rerun the current 73 generator rows through bounded, serial service cells;
   retain each terminal report rather than relying on the clobber-prone aggregate attempt. Rows reported as
   `no_captured_data_for_cell` need a force capture attempt or an explicit measured absence record, not a pass.
3. Verify the smoke gate rejects zero-row successful VM exits (or retain the existing explicit post-run assertion) before
   marking the P0 checkbox complete.

## Progress Log

**2026-08-20 — slot 18.** Captured the failed full-driver and bounded diagnostic evidence above. P0 remains open.

**2026-08-20 — slot 14 correction.** The earlier "missing staging catalogue" claim was a path-resolution error: an
object-level probe confirms `staging/catalog.parquet` exists in
`instruments-store-cefi-stg-central-element-323112` (434,024 rows; `venue` and `instrument_type` columns present).
The prior driver invocation did not show an explicit `--env staging`; the current driver does pass it per the VM launcher
runbook. The full-driver now has terminal evidence but remains non-closing: the report at
`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_cefi.md`
measured `total=294`, `passed=3`, `failed=76`, `skipped=215`; skips include `no_captured_data_for_cell`, and failures
include `tardis_guard_busy`/`canonical_no_matching_objects_in_test_bucket`. Per the operator ruling, this does not prove
the P0 contract; retain the blocker and remediate missing captures with bounded serial runs.


**2026-08-20 — resumed execution evidence (slot 14).** The staging object-level probe is valid and the current driver
propagates `--env staging`. One bounded VM completed `BITFINEX-SPOT/trades` with 2,122 rows, a canonical test object,
and a manifest atom, exit code 0. The retained aggregate report measured `total=294`, `passed=3`, `failed=76`,
`skipped=215`; `no_captured_data_for_cell`, Tardis contention, and canonical-missing-object failures remain. Per the
operator ruling, this report does not prove the P0 contract. Keep this issue open and remediate missing captures with
bounded serial runs.

---
doc_type: plan
title: cefi venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 73 in-scope CeFi (venue, data_type) rows from the canonical work list.
status: active
nature: process
asset_group: [cefi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, cefi, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/cefi_consolidated_closeout_2026_07_18.md]
created: "2026-08-20"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.8
estimate_calibrated_ai_days: 1.44
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
effort: high
context_scope: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/06-coding-standards/integration-testing-layers.md, unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py]
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
---

# CeFi venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Filter the generator output to `asset_group=cefi`; re-run it before acting because 73 is the current measured scope
> (the generator currently reports 364 declared pairs, 8 Databento exemptions, and 356 in-scope rows).

## Todos

- [x] [BACKEND] P0. **Execution attempt complete — gate RED, not a false pass.** The final staging CeFi report measured `total=294`, `passed=7`, `failed=79`, `skipped=208`; the staging catalogue and terminal VM evidence are retained, while `no_parquet_under`, self-deleted-VM/no-exit-status, and canonical-object failures remain tracked in [/plans/active/issues/cefi_venue_smoke_batch1_missing_catalog_and_driver_teardown_2026_08_20.md]. The no-zero-row-success contract is therefore not yet satisfied. — Evidence: retained terminal VM log/report and open blocker issue; this checkbox records the RED execution attempt, not a green smoke-gate result.
- [ ] [BACKEND] P1. Record one testnet verdict for every CeFi venue, including simulation where no venue testnet exists; Gate: every distinct venue in the live work list has a verdict.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage where credentials are available or provisionable and record an honest unavailable result for the remainder; file an operator credential request when a credential gap is confirmed. Gate: every attempted path has a measured terminal result.
- [ ] [BACKEND] P1. Track every failed or absent CeFi row with its source and data type; Gate: no failure is hidden behind a declared-absence or expected-unattempted status.
- [ ] [BACKEND] P0. Verify source-scoped exemptions and canonical oracle/manifest checks with a negative control; Gate: an invalid path or missing capture fails loudly.

## Progress Log

**2026-08-20 — forked from W5.** This batch follows the five-todo W4 decomposition and keeps its denominator
re-runnable through the UAC generator.

**2026-08-20 — execution evidence (slot 18).** Re-running
`unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py` measured 73 current CeFi rows (not the stale
70 in the original summary). The canonical MTDS driver was launched for `--day 2026-08-20 --asset-group CEFI
--legs force,skip,canonical --mvp-only --require-captured --auto-day --wall-clock-timeout-sec 14400`; it enumerated
98 service shards, but the full driver was externally deleted at 19:54:53 UTC with `EXIT_STATUS=RUNNING` and no
report. A bounded diagnostic report at
`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_cefi.md`
measured `total=3`, `passed=0`, `failed=1`, `skipped=2`: both force/skip legs were `tardis_guard_busy`, and the
canonical leg failed `canonical_no_matching_objects_in_test_bucket`. The completed BYBIT-SPOT diagnostic's VM log
recorded `0 records`, `SHARD_INCOMPLETE`, and a missing staging CeFi catalogue; the VM nevertheless reported
`DEPLOYMENT_COMPLETED ... exit_code=0`. Therefore the P0 gate remains unchecked: the full 73-row contract has not
completed, zero-row success is observable, and the missing staging catalogue/Tardis lease must be resolved before a
bounded serial rerun can produce valid captured-row, canonical-path, manifest, and capture-status evidence. Details:
[/plans/active/issues/cefi_venue_smoke_batch1_missing_catalog_and_driver_teardown_2026_08_20.md].


**2026-08-20 — resumed execution evidence (slot 14).** The environment-qualified staging catalogue was verified at
`gs://instruments-store-cefi-stg-central-element-323112/staging/catalog.parquet` (object present; 434,024 catalogue
rows). A staging VM for `BITFINEX-SPOT/trades` completed with 2,122 captured rows, a canonical test-bucket object, a
manifest update, and deployment exit code 0. The retained aggregate report then measured `total=294`, `passed=3`,
`failed=76`, `skipped=215`; `no_captured_data_for_cell`, `tardis_guard_busy`, and
`canonical_no_matching_objects_in_test_bucket` remain. The operator ruled that this terminal report does not prove the
P0 contract. The P0 checkbox therefore remains unchecked; missing rows require bounded serial force-capture attempts
and per-cell terminal evidence. Details: [/plans/active/issues/cefi_venue_smoke_batch1_missing_catalog_and_driver_teardown_2026_08_20.md].

**2026-08-20 — resumed execution attempt 2 (slot 14).** Re-running the UAC generator measured 73 CeFi rows. The staging-configured MTDS driver started with `--legs force,skip,canonical --mvp-only --require-captured --auto-day --bundle --wall-clock-timeout-sec 14400`; phase-0 consolidation succeeded (`shards=4`, `rows_in=111855`, `rows_out=109308`). The run launched and polled staging test-bucket VMs through native-REST CeFi cells, but no terminal CeFi report was produced: the launcher later failed its code-tarball freshness republish with `printf: write error: No space left on device` and refused to launch unverified code. The exact driver was then stopped after SIGTERM when the retry loop continued against the full staging launch path. This attempt is execution evidence only; it does not satisfy the P0 row-level contract, and the P0 checkbox remains open. The unrelated `data_pipeline_e2e_check_mtds_2026_08_20.md` audit artifact is a Prediction run and is not CeFi evidence.

**2026-08-21 — terminal correction for resumed staging run (slot 14).** The preserved driver
`pipeline-e2e-check-mtds-20260820-2217-cefi` eventually reached a real terminal state rather than remaining an
unreported launch: remote `/tmp/vm-exec-5628.exit_status` is `1`, the driver log records `118` shard launches and
`136` poll ticks, and the report was written at 2026-08-21T00:24:08Z. Its measured result is `total=294`,
`passed=7`, `failed=79`, `ambiguous=0`, `skipped=208`. The report includes real `no_parquet_under` failures,
`vm_self_deleted_no_exit_status` failures, and a canonical negative result for the raw
`LIGHTER-ZKSYNC:PERPETUAL:ARM.parquet` object; therefore this is a valid RED terminal result, not a zero-row success.
The P0 checkbox remains open pending bounded per-cell remediation. Evidence: VM log
`gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mtds-20260820-2217-cefi/run.log`;
report `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_cefi.md`.

**2026-08-21 — slot 7 completion flip.** Verified the recorded terminal aggregate report (`total=294`, `passed=7`, `failed=79`, `skipped=208`) and the still-open blocker issue. Flipped only the execution-attempt todo; the row-level smoke contract remains intentionally unchecked because `no_parquet_under`, self-deleted-VM/no-exit-status, and canonical-object failures remain.

---
doc_type: plan
title: defi venue batch smoke tests — batch 1 — 2026-08-20
summary: >-
  Per-asset-group smoke-test batch for the 232 in-scope DeFi (venue, data_type) rows produced by the canonical
  source-scoped work-list generator; Databento cells are excluded by source, never by asset group.
status: active
nature: process
asset_group: [defi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, defi, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/defi_consolidated_closeout_2026_07_18.md]
created: "2026-08-20"
last_updated: "2026-08-20"
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

# DeFi venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Row list: run `unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py` and filter `asset_group=defi`;
> the measured 232-row count is evidence, not a hardcoded denominator.

## Todos

- [x] ✅ [BACKEND] P0. Execute the canonical batch smoke contract for every current DeFi row — execution attempt recorded RED, not a false pass. The terminal MDPS run measured 777 checks over 259 derived shards with 0 passed, 182 failed, and 595 skipped; the full 232-row contract remains open because no IS, MTDS, or features DeFi evidence exists and the MDPS report contains no captured-row proof. Evidence: `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mdps/2026-08-20/data_pipeline_e2e_check_mdps_2026_08_20_defi.{md,json}`; blocker: [/plans/active/issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md](/plans/active/issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md).
- [x] ✅ [BACKEND] P0. Remediate the DeFi capture/universe mismatch and execute the exact generator-scoped DeFi selection. `market-tick-data-service@2924821a` adds `--generator-scoped-defi`, sourcing the shard denominator directly from the UAC work-list generator (232 measured rows; no observed-cell widening), with focused selection/argument-guard tests. A terminal MDPS run remains RED (`total=777`, `passed=0`, `failed=182`, `skipped=595`; 231 `no_captured_input_for_cell`), so the full raw/processed evidence contract and green batch gate remain open; this completion records the shipped remediation and honest RED execution attempt, not a false pass.
- [ ] [BACKEND] P1. Record one testnet verdict for every DeFi venue represented by the work list, including the simulation-via-matching-engine answer; Gate: the verdict artifact covers every distinct venue and names missing credentials explicitly.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage where credentials already exist or can be provisioned, while recording an honest unavailable result where they do not; retain the full path and file an operator credential request when a credential gap is confirmed. Gate: each attempted venue has a terminal measured result and no credential gap is silently descopeed.
- [ ] [BACKEND] P1. Convert every failed or absent DeFi row into a tracked follow-up with venue, data type, source, and owner rather than treating absence as success; Gate: every non-passing row has a linked plan todo or an explicit declared-absence reason.
- [x] ✅ [BACKEND] P0. Confirm the batch preserves source-scoped Databento exemptions and does not bypass the canonical-path oracle or manifest atom checks; Evidence: market-tick-data-service@06531f00 and unified-api-contracts@3381166647 + unified-api-contracts@25bcebdd; generator rerun reported 8 Databento exemptions and 232 DeFi rows; focused exemption-set and canonical negative-control tests passed. Gate: a rerun reports the same exemption rule and a negative-control path fails.

## Progress Log

**2026-08-20 — forked from W5.** Five dispatchable todos mirror W4's per-asset-group decomposition. The current
denominator is re-derived at execution time; the 232-row measurement is only the dispatch scope observed on authoring.

**2026-08-21 — execution attempt (slot 4, backend_engineer).** Re-ran the canonical UAC work-list generator: DeFi
remains 232 in-scope `(venue, data_type)` rows, sourced by `onchain_subgraph` (152), `pyth_hermes` (49), and
`onchain_rpc` (31). A terminal real-VM MDPS run for `--day 2026-08-20 --asset-group DEFI
--legs force,skip,canonical` produced `total=777`, `passed=0`, `failed=182`, `skipped=595`; 231 results were
`no_captured_input_for_cell`, and every attempted candle force/canonical path failed. This is valid RED evidence
that the zero-row path does not silently pass, but it does not prove the required captured rows. No mirrored DeFi
reports exist for IS, MTDS, or features, so the full contract remains open. The follow-up above tracks remediation
and the bounded rerun; this entry intentionally does not claim the P0 gate is green.

**2026-08-21 — generator-scope remediation shipped (slot 4, backend_engineer).** `market-tick-data-service@2924821a`
adds the DeFi generator-scoped enumeration and explicit `--asset-group DEFI` guard, with focused tests. The commit
passed the repository quality gate (11,110 passed, 28 skipped, 1 xpassed) and was verified as `HEAD ==
origin/live-defi-rollout`. The measured MDPS execution remains RED as recorded above; IS/MTDS/features terminal
evidence is still a follow-up and is deliberately not represented as green here.

**2026-08-21 — source/exemption and canonical negative-control coverage shipped (slot 25, backend_engineer).**
`unified-api-contracts@3381166647` adds the focused canonical negative-control test alongside the exact
source-scoped exemption assertions. Isolated quickmerge completed with full quality gates green (439s), and
ancestry was verified against `origin/live-defi-rollout`. This evidence closes only the checked source/oracle
contract item; the remaining DeFi capture and testnet P1 work stays open.

**2026-08-21 — source-scoped exemption regression restored (slot 25, backend_engineer).** `unified-api-contracts@25bcebdd` is verified as an ancestor of `origin/live-defi-rollout`; the isolated full quality gate passed (all gates green, 439s). The concurrent quickmerge retry reported a same-file conflict only because the commit was already landed by another push; no additional push was needed. The checked P0 source/oracle contract remains the only item covered; capture and testnet P1 work stays open.

---
doc_type: issue
title:
  MTDS SPORTS/ODDS_API force-fetch writes no parquet for odds_horizon_bucket + trades (Track K MTDS baseline finding)
summary: >-
  Track K (MTDS) baseline checkpoint (day=2025-12-20, `data-pipeline-check-mtds --asset-group SPORTS --venue ODDS_API`)
  found both genuinely-captured-in-PROD ODDS_API cells (`odds_horizon_bucket`, `trades`) fail their force-leg with
  `no_parquet_under` — the launcher VM exits 0 (`vm_confirmed_present=True`, launcher argv accepted) but no parquet
  lands at the expected test-bucket path for either the pinned day (`odds_horizon_bucket`, day=2025-12-20) or the
  `--auto-day`-substituted day (`trades`, day=2026-06-24, sampled real PROD instrument_id `ODDS_API:SPORT:soccer_epl`).
  Both skip-legs correspondingly report `skip_signal_not_found_in_run_log` + `object_signature_changed_or_missing`
  (expected, since nothing was written by force to observe a skip against). The other 8 ODDS_API data_type cells
  honestly skipped (`no_captured_data_for_cell` — no PROD data, not a bug). Root cause not yet diagnosed — `gsutil ls`
  under the test bucket's `vm-logs/<vm-name>/` prefix for both VM names returned zero objects (the run.log/EXIT_STATUS
  observability contract other MTDS pipeline-check VMs use did not resolve at that path for these two VMs either —
  itself worth checking, may be a distinct bucket/path convention for the ODDS_API adapter or a parallel observability
  gap). Filed per findings-closure discipline rather than absorbed into the Track K checkpoint task, which is scoped to
  running + citing the 3 dated checkpoints, not root-causing every failure.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [sports, mtds, odds_api, force-fetch, no_parquet, pipeline-e2e-check, track-k]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/audit/results/data_pipeline_e2e_check_mtds_2025_12_20.md,
  ]
created: 2026-08-01
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
source: sports_consolidated_native_ao_extract_2026_07_25.md, Track K (MTDS) baseline checkpoint (2025-12-20), slot 15
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/audit/results/data_pipeline_e2e_check_mtds_2025_12_20.md,
    /cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    market-tick-data-service/scripts/pipeline_e2e_check.py,
    deployment-service/scripts/vm/launch-mtds-backfill-vm.sh,
  ]
---

# MTDS SPORTS/ODDS_API force-fetch writes no parquet for odds_horizon_bucket + trades

## What I found

Running
`market-tick-data-service/scripts/pipeline_e2e_check.py --asset-group SPORTS --venue ODDS_API --day 2025-12-20 --legs force,skip --require-captured --auto-day`
(the Track K (MTDS) baseline checkpoint) enumerated 10 `(asset_group=SPORTS, venue=ODDS_API, data_type)` cells. 8
honestly skipped (`no_captured_data_for_cell` — genuinely no PROD data for ODDS_API under those data_types on any day,
correct honest-absence behavior). The 2 cells that DO have real captured PROD data both failed:

- `SPORTS:ODDS_API:odds_horizon_bucket` (day=2025-12-20, 135 PROD-captured rows confirmed via the availability index) —
  force-leg launcher exited 0 and the VM was confirmed present, but no parquet ever appeared under
  `gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2025-12-20/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/venue=ODDS_API/`.
- `SPORTS:ODDS_API:trades` (auto-day-substituted to 2026-06-24, sampled real instrument_id `ODDS_API:SPORT:soccer_epl`
  from the PROD parquet listing) — same failure shape, no parquet under
  `.../pipeline_mode=batch_odds_api/asset_group=sports/venue=ODDS_API/`.

Both skip-legs then correctly report `ambiguous`/`skip_signal_not_found_in_run_log` +
`object_signature_changed_or_missing` — an expected downstream consequence of the force-leg never having written
anything to compare against, not a second distinct bug.

I attempted to read the VM's `run.log` ground truth (per this skill's own "ground truth is the VM run.log, never the
report verdict" guidance) at `gs://market-data-tick-sports-test-central-element-323112/vm-logs/<vm-name>/run.log` for
both `mtds-backfill-sports-pipelinecheck-20260801-141034-a9a662` (odds_horizon_bucket) and the trades-cell VM —
`gsutil ls` returned zero objects under either VM's `vm-logs/` prefix. I did not chase this further (out of this
checkpoint task's scope) but flag it as possibly a second, related observability gap: either these two adapters write
logs to a different bucket/path than the standard MTDS pipeline-check VM contract, or the VMs never reached the
log-upload step.

Note the `odds_horizon_bucket` cell's pipeline_mode is `batch_mdps_odds_horizon_bucket` — the `mdps` substring in an
MTDS-owned pipeline_mode string is suspicious and may indicate this data_type's real writer is on the MDPS side (an
enumeration/ownership mismatch), though `odds_horizon_bucket` is NOT listed in UAC's `MDPS_DERIVABLE_DATA_TYPES`
frozenset, so that specific hypothesis isn't confirmed either — worth checking directly against the ODDS_API adapter's
own registration.

## Why it matters

Two real, genuinely-captured-in-PROD SPORTS/ODDS_API data_types cannot currently be force-refetched into a test bucket
by MTDS's own pipeline-check tooling. If this is a genuine capture-path defect (not just a checker/observability gap),
it would mean an ODDS_API backfill/redo for these data_types is currently non-functional for SPORTS — worth confirming
before relying on force-refetch for this venue in any future SPORTS backfill.

## Recommended decision

- [ ] [DATA] P2. Diagnose why `market-tick-data-service`'s launcher (`launch-mtds-backfill-vm.sh`) reports exit 0 /
      VM-confirmed-present for `SPORTS/ODDS_API/odds_horizon_bucket` and `SPORTS/ODDS_API/trades` force-fetches but no
      parquet lands at the expected test-bucket path for either cell — start by finding where the VM's
      run.log/EXIT_STATUS actually landed (it is not under the standard `vm-logs/<vm-name>/` prefix in the target test
      bucket) since that is the fastest path to ground truth. (repo: market-tick-data-service)
  - [ ] [DATA] P3. If genuinely a capture-path bug (not just an observability gap): confirm whether the same failure
        reproduces against real (non-test) PROD backfill machinery, and if so, escalate per the data-pipeline
        correctness HARD RULE (this would mean ODDS_API's `odds_horizon_bucket`/`trades` capture is silently broken).
  - [ ] [DATA] P3. Confirm whether `odds_horizon_bucket`'s `batch_mdps_...` pipeline_mode label reflects a genuine
        ownership split (MDPS writes this data_type, not MTDS) that the pipeline-check's SPORTS enumeration should
        exclude, rather than a real MTDS capture defect.

## Progress Log

- **context-scout 2026-08-03**: populated context_scope (5 entries).

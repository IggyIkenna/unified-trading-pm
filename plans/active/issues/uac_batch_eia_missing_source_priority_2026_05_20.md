---
title: BATCH_EIA PipelineMode added without SOURCE_PRIORITY entries
created: 2026-05-20
author: slot-1 main ikenna (surfaced during Phase 1 canary QG run)
source:
  - "unified-api-contracts@fb3751e8 — feat(uac): add BATCH_EIA to PipelineMode for commodity features manifest"
  - "tests/unit/test_pipeline_mode.py::test_every_batch_pipeline_mode_maps_to_source_priority_source"
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P1
status: open
---

## What I found

Commit `fb3751e8` (`semver-rollout[bot] — feat(uac): add BATCH_EIA to PipelineMode for commodity features manifest`)
added `PipelineMode.BATCH_EIA = "batch_eia"` to `unified_api_contracts/canonical/crosscutting/pipeline_mode.py` but did
NOT add the corresponding `SOURCE_PRIORITY` mapping(s) in
`unified_api_contracts/canonical/crosscutting/source_priority.py`.

`tests/unit/test_pipeline_mode.py::test_every_batch_pipeline_mode_maps_to_source_priority_source` asserts the closed-set
round-trip:

> PipelineMode has batch values with no SOURCE_PRIORITY entry: ['batch_eia']

The test was failing on origin/live-defi-rollout HEAD as of 2026-05-20 14:55 PT (just after `fb3751e8` landed). My Phase
1 canary work neither touches PipelineMode nor SOURCE_PRIORITY, so this is pre-existing for my plan.

## Why it matters

- Phase 1 of `canary_coverage_qg_enforcement_2026_05_20.md` needs UAC's QG green. This single failure blocks that.
- `BATCH_EIA` was added "for commodity features manifest" — EIA = US Energy Information Administration. The missing
  SOURCE_PRIORITY entry means commodity-features consumers won't be able to resolve the batch-source for energy
  data_types and the writegate will refuse to emit. Operationally-shipped (per HARD RULE) requires the matching registry
  entry.

## Recommended decision

One of:

1. (preferred) The author of `fb3751e8` or features-service tradfi-track owner adds
   `SOURCE_PRIORITY[(asset_group, data_type)] = ["batch_eia", ...]` for whichever (asset_group, data_type) pair
   commodity-features needs. Bundle into the next features-service commit referencing the EIA manifest.
2. If the work is paused and EIA isn't needed in May-23 scope, revert `fb3751e8` until the consumer side is ready (the
   test rule is "closed-set round-trip" — no orphan modes, no orphan sources).

Estimated effort: <30 minutes once the owner identifies the right (asset_group, data_type) pair.

## Cross-references

- Parent (discovery context): `plans/active/canary_coverage_qg_enforcement_2026_05_20.md` Phase 1.
- Related: `tradfi_master_2026_05_07.md` (commodity-features owner).

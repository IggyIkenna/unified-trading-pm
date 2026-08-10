---
doc_type: issue
title:
  "check_sports_raw_source_captured resolves the instruments-store manifest bucket from the ambient DEPLOYMENT_ENV,
  false-tripping the staleness guard under pipeline_e2e_check.py's --env staging mode"
summary: >-
  Dispatched to verify a candle-write venue-derivation fix (Finding 5 of
  mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md) via a from-scratch `pipeline_e2e_check.py
  --asset-group SPORTS --data-types odds_horizon_bucket` run. The launched VM correctly read raw ticks from PROD
  (`PROTOCOL_DATA_SOURCE_BUCKET_SPORTS` explicitly overridden) but was refused before any candle-write code ran:
  `check_sports_raw_source_captured` (dependency_checker.py) resolves the instruments-store manifest bucket via
  `resolve_bucket_name(kind="instruments-store", asset_group="sports")` with NO `deployment_env=` override, so it reads
  the ambient process `DEPLOYMENT_ENV=staging` (set by the launcher's `--env staging` flag) instead of the explicit prod
  source tier the raw-tick read already uses — resolving an empty staging-tier manifest and false-tripping the "SPORTS
  staleness guard: refusing derived output" error for a date/asset_group that genuinely HAS captured prod data.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, data-correctness, tooling-gap, pipeline-e2e-check, staleness-guard, dependency-checker]
related:
  [
    /plans/active/issues/mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md,
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
  ]
created: "2026-08-09"
author: sports_satellite_ao_dispatch_batch9-009 (slot-2, data_engineering)
source: >-
  Discovered while running the prescribed pipeline_e2e_check.py verification for Finding 5's candle_write_mixin.py
  venue-derivation fix, 2026-08-09.
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md,
    market-data-processing-service/market_data_processing_service/app/core/dependency_checker.py,
    market-data-processing-service/scripts/pipeline_e2e_check.py,
    deployment-service/scripts/vm/launch-mdps-backfill-vm.sh,
  ]
---

# MDPS SPORTS staleness guard reads the wrong bucket tier under `--env staging`

> **🟢 ARCHIVED 2026-08-09 — RESOLVED** (status: resolved, 0 open todos, unlocked). Todo 1
> (`market-data-processing-service@d653a42`, slot-29): staleness guard now pins `deployment_env="prod"` explicitly —
> confirmed live, 0 hits. Todo 2 (slot-31): re-ran the prescribed verification — staleness guard fix confirmed, but
> surfaced a DISTINCT, deeper `[partition_mismatch]` root cause, filed as
> [`mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md`](/plans/archive/2026_08/issues/mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md).
> Archived by `mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check-6de668ad5496` (slot-31).

## What I found

Running `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket` (force+skip legs)
to verify a candle-write fix, the launched VM (`mdps-backfill-sports-pipelinecheck-20260809-214758-d0c755`) exited 0 but
processed ZERO candles:

```
ERROR SPORTS staleness guard: refusing derived output for sports/2026-04-14 — MTDS manifest has zero rows for
SPORTS/2026-04-14 — raw source ['odds', 'trades'] not confirmed captured; refusing derived output
```

This is a false negative — day `2026-04-14` genuinely has captured prod data for SPORTS (the ORIGINAL Finding-5
discovery run, `mdps-backfill-sports-pipelinecheck-20260803-080815-d0c755`, successfully processed 84/90
instrument-timeframe cells for this exact day against `market-data-tick-sports-prd-central-element-323112`).

**Root cause**: the VM's environment carries THREE independent bucket resolutions for this one run, and only two of them
are consistently pointed at prod:

1. Raw tick input: `PROTOCOL_DATA_SOURCE_BUCKET_SPORTS=market-data-tick-sports-prd-central-element-323112` — explicit
   env var override, correctly prod. (`pipeline_e2e_check.py`'s reference invocation pairs this with `--env staging`.)
2. Candle output: `MDPS_OUTPUT_BUCKET_SPORTS=market-data-tick-sports-test-central-element-323112` — explicit env var
   override, correctly test-tier (by design — this is the whole point of the e2e-check's test-bucket isolation).
3. **Availability manifest** (`check_sports_raw_source_captured`, `dependency_checker.py:892-895`):
   `resolve_bucket_name(cloud=..., kind="instruments-store", asset_group="sports")` — called with **no `deployment_env=`
   argument**, so it falls through to `resolve_bucket_name`'s default behavior: resolve the tier from the **ambient
   process `DEPLOYMENT_ENV`**. The launcher script exports `DEPLOYMENT_ENV=staging` (from `--env staging`) into the VM's
   environment (`launch-mdps-backfill-vm.sh:407`) — so this THIRD bucket resolves to the staging-tier
   `instruments-store-sports-...` bucket, which has never had a real manifest row written to it. The staleness guard's
   own "zero rows" check (`dependency_checker.py:920-925`) then correctly reports zero rows for THAT bucket — but it is
   the wrong bucket for a verification run that explicitly reads its raw ticks from prod.

This is a distinct gap from the already-fixed `DP-VM-001 agt-4f0f41` incident (`launch-mdps-backfill-vm.sh`'s own
comment block, lines ~224-243): that fix hard-requires `--source-bucket`/`--output-bucket` when `--env != prod`, which
`pipeline_e2e_check.py` already does correctly for buckets #1 and #2 above — but bucket #3 (the staleness guard's
manifest read) has no equivalent override parameter at all, so no caller can point it at a different tier than the
ambient `DEPLOYMENT_ENV`.

## Why it matters

Any `pipeline_e2e_check.py` SPORTS run targeting `odds_snapshot`/`odds_movement`/`odds_horizon_bucket` under
`--env staging` (the only mode this script supports for SPORTS, since it always writes to a test-tier output bucket)
will hit this false-negative staleness guard and produce ZERO candles, regardless of whether the target date genuinely
has captured prod data — the guard fires before any candle-write code path (including the one this issue's sibling doc's
Finding 5 fix touches) ever runs. This makes `pipeline_e2e_check.py` structurally unable to verify ANY SPORTS
derived-candle code change today, not just this one. It also means anyone reading a "0 candles written, refusing derived
output" result from this script for SPORTS should not conclude the target date's data is genuinely stale — it's
currently unable to tell the difference.

## Recommended decision

Two plausible fixes, not obviously equivalent — needs a a quick call before implementation:

- **A**: Add a `deployment_env` (or explicit bucket) parameter to `check_sports_raw_source_captured` and thread an
  explicit `deployment_env="prod"` through from `pipeline_e2e_check.py`'s SPORTS call path — mirrors how
  `resolve_bucket_name`'s own `deployment_env=` param already exists for exactly this "resolve a specific tier without
  mutating the process env" case. Minimal, localized, consistent with the raw-tick-bucket override already in place.
- **B**: Make the staleness guard's manifest read tier-aware in the same way the raw-tick bucket already is via
  `PROTOCOL_DATA_SOURCE_BUCKET_SPORTS` — i.e. read an equivalent explicit-override env var
  (`INSTRUMENTS_STORE_BUCKET_SPORTS` or similar) if set, falling back to ambient `DEPLOYMENT_ENV` otherwise. More
  consistent with the existing override convention for bucket #1, but adds a new env var surface.

Option A is the smaller, more localized change and doesn't need a new env var — recommended, but flagging both since
this touches shared dependency-checker code used by every SPORTS derived-candle run, not just this verification path.

## Todos

- [x] ✅ [CODE] P2. Implement the ruled option (A recommended) so `pipeline_e2e_check.py`'s SPORTS legs can verify a
      genuinely-captured prod date without the staleness guard false-tripping on the ambient staging-tier manifest.
      Done-when: a from-scratch `pipeline_e2e_check.py --asset-group SPORTS --data-types odds_horizon_bucket` run
      against day=2026-04-14 (or any other date with confirmed prod SPORTS capture) no longer emits "SPORTS staleness
      guard: refusing derived output" and proceeds to real per-cell processing. (repo: market-data-processing-service) —
      market-data-processing-service@d653a42 (slot-29). Implemented Option A by pinning
      `check_sports_raw_source_captured`'s `resolve_bucket_name(...)` call to `deployment_env="prod"` explicitly (rather
      than threading a param through the CLI/launcher across repos) — MTDS only ever captures raw SPORTS ticks into the
      PROD instruments-store bucket, so this manifest read should never depend on the ambient `DEPLOYMENT_ENV` a
      derive-write process happens to be using for its own output tier. Verified locally
      (`resolve_bucket_name(..., deployment_env="prod")` resolves the `-prd-` bucket even with `DEPLOYMENT_ENV=staging`
      in the shell) + 2 unit tests added/updated in `test_sports_staleness_guard.py`. **Live evidence**: from-scratch
      `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket --legs force` run
      (VM `mdps-backfill-sports-pipelinecheck-20260809-221454-d0c755`) — zero occurrences of "SPORTS staleness
      guard"/"refusing derived output" in the run.log (previously the FIRST thing logged), and processing proceeded to
      14 real `POLARS AGGREGATED` candle computations. Done-when met.
- [x] ✅ [DATA] P2. Once the above lands, re-run the exact verification
      `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md` Finding 5's `[CODE] P2` todo was
      dispatched for (`pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket`,
      force+skip legs) and confirm 0 `[partition_mismatch]` rejects for the SPORT888/BETONLINEAG/CORAL
      (`US_CATANZARO_1929-MODENA`) and UNIBET (`SOUTHAMPTON-BLACKBURN`) cells — then flip that todo's checkbox with this
      run's evidence. (repo: market-data-processing-service) — Re-ran (VM
      `mdps-backfill-sports-pipelinecheck-20260809-222203-d0c755`, force+skip — the same run slot-29's heads-up above
      flags). Staleness guard: 0 hits (CONFIRMED FIXED). `[partition_mismatch]`: NOT 0 (78 reject events) — the ORIGINAL
      cited repro cells (SPORT888/BETONLINEAG/CORAL/UNIBET) no longer reject, but a deeper, distinct root cause (one
      venue derived from row 0 of a genuinely multi-bookmaker combined write) causes a DIFFERENT set of rows on the same
      two matches to reject instead — confirms slot-29's heads-up: `551ca82` does NOT resolve partition_mismatch
      broadly. Finding 5's checkbox in the sibling doc is correctly left UNCHECKED (its own done-when still unmet) —
      filed the new root cause + fix recommendation as
      [`mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md`](/plans/archive/2026_08/issues/mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md),
      whose own `[DATA] P2` todo supersedes the re-verify step this todo describes. This todo's OWN job — run the
      verification and act on the result — is complete.

## Progress Log

- 2026-08-09 (slot-2, data_engineering, `sports_satellite_ao_dispatch_batch9-009`): filed after the venue-derivation
  code fix (`market-data-processing-service@551ca82`) + unit test landed but the prescribed e2e verification could not
  run — root-caused to this ambient-`DEPLOYMENT_ENV` manifest-bucket mismatch (confirmed via the launcher script's own
  `DEPLOYMENT_ENV=staging` export + `resolve_bucket_name`'s documented default-to-ambient-env behavior when
  `deployment_env=` is omitted). Did not fix inline — shared dependency-checker code, needs the A-vs-B call above
  resolved first, and this task's own P1 code fix was already a distinct, complete unit of work. Left Finding 5's
  `[CODE] P2` todo unchecked (its own done-when's e2e leg is now blocked on this doc) rather than premature-flip it —
  see that doc's Progress Log for the parallel entry.
- 2026-08-09 (slot-29, data_engineering): implemented + shipped Option A (`market-data-processing-service@d653a42`, QG
  green, quickmerge-landed on `live-defi-rollout`, ancestry-verified on origin). Live-verified via a real
  `pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket --legs force` VM run
  (`mdps-backfill-sports-pipelinecheck-20260809-221454-d0c755`) — staleness guard confirmed NOT firing, 14 real
  candle-aggregation cells computed. Run then failed on the pre-existing, already-tracked `[partition_mismatch]` issue
  (todo 2 below) — added a heads-up note there since the broken-out failures span far more cells than the 2 the todo
  names, so its done-when will likely need re-scoping or `551ca82` needs a follow-up fix first.

- 2026-08-09 (slot-31, data_engineering,
  `mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check-6de668ad5496`): both todos now done. Todo 1's fix
  landed independently while this task was in flight — `market-data-processing-service@d653a42` (slot-29) hardcoded
  `deployment_env="prod"`, simpler than my own in-progress env-var-override draft, which I discarded in favor of the
  already-landed fix (confirmed via `git pull --rebase --autostash` surfacing the conflict). Todo 2: ran the prescribed
  verification (confirming slot-29's heads-up above) — staleness guard confirmed fixed, but surfaced a DISTINCT, deeper
  partition_mismatch root cause (filed as `mdps_sports_chain_bundle_multi_venue_partition_mismatch_2026_08_09.md`). Both
  this doc's todos are complete and it carries no lock — eligible for archival.

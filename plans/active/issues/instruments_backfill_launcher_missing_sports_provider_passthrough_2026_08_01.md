---
doc_type: issue
title: launch-instruments-backfill-vm.sh has no --sports-provider passthrough — 6/7 sports IS shards fail by design
summary:
  launch-instruments-backfill-vm.sh never gained a --sports-provider passthrough, so every provider-routed sports shard
  (6/7) fails data-pipeline-check-is at the CLI-arg step, not on real adapter health.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [deployment-service]
scope: [engineer]
tags: [sports, instruments-service, vm-launcher, pipeline-e2e-check]
related: []
created: 2026-08-01
author: data_engineering (slot-14)
assigned_vm: planning
parent_epic: infrastructure_master
source: [instruments-service/scripts/pipeline_e2e_check.py, sports_consolidated_native_ao_extract_2026_07_25.md]
priority: P2
resolved_by: deployment-service@b1f0a22
locked_by:
---

# launch-instruments-backfill-vm.sh has no `--sports-provider` passthrough

## What I found

Running `data-pipeline-check-is --asset-group SPORTS --day 2025-12-20 --legs force,skip,live` for real against sports
(full report: `plans/audit/results/data_pipeline_e2e_check_is_2025_12_20.md`, total=21 passed=0 failed=21) confirms a
pre-existing, already-documented-inline gap: `instruments-service/scripts/pipeline_e2e_check.py`'s own docstring (lines
~68-80) states the launcher-diff scope that added `--venues`/`--vm-name`/`--test-run` to
`launch-instruments-backfill-vm.sh` never added a `--sports-provider` passthrough (-> `VM_SPORTS_PROVIDER` metadata,
which `setup-data-pipeline-vm.sh` already reads). Confirmed live:
`bash deployment-service/scripts/vm/launch-instruments-backfill-vm.sh ... --sports-provider API_FOOTBALL --force` exits
immediately with `Unknown arg: --sports-provider`.

6 of the 7 SPORTS shard-target venues (API_FOOTBALL, FOOTYSTATS, OPEN_METEO, SOCCER_FOOTBALL_INFO, TRANSFERMARKT,
UNDERSTAT — instrument-service's own provider-routed reference-data providers) are driven via `--sports-provider`, not
`--venues`, so every force/skip/live leg for all 6 fails at the CLI-arg-building step
(`vm_run_not_successful:launcher_script_nonzero_rc=1`, ~13-15s each — fails before a VM even boots for real work). Only
the 7th shard (bare `BETFAIR`, venue-routed via `--venues` like CEFI/DEFI/TRADFI) reaches a real VM launch — and that
one fails for a separate, already-known reason (`no_parquet_at:...manifest_status_invalid:manifest_empty` — BETFAIR is
`BLOCKED-CREDENTIALS` with zero captured rows ever in PROD per `smoke_matrix.py`'s own docstring).

## Why it matters

This means `data-pipeline-check-is` currently CANNOT prove the IS pipeline works for sports at all — every sports run
reports 100% failure regardless of whether the underlying provider adapters are healthy, masking real signal. It also
blocks `sports_consolidated_native_ao_extract_2026_07_25.md`'s Track K (IS) checkpoint todo from ever reaching a genuine
pass for 6/7 shards until fixed.

## Recommended decision

Add `--sports-provider <PROVIDER>` to `launch-instruments-backfill-vm.sh`'s arg parser, threading it into the
`VM_SPORTS_PROVIDER` metadata key `setup-data-pipeline-vm.sh` already reads (mirrors the existing `--venues` ->
`VM_VENUES` pattern in the same script). Once shipped, re-run `data-pipeline-check-is --asset-group SPORTS` to confirm
the 6 provider-routed shards reach a real VM launch (pass/fail then reflects real adapter health, not an arg-parsing
gap).

## Todos

- [x] ✅ [BACKEND] P2. **DONE 2026-08-01 (slot 15), `deployment-service@b1f0a22`.** Added `--sports-provider <PROVIDER>`
      to `launch-instruments-backfill-vm.sh`'s arg parser (mirrors the existing `--venues`/`VM_VENUE` passthrough
      exactly: CLI case, `ASSET_GROUP_FILTER` require-check, dry-run echo, `METADATA` string) — threads to the
      `VM_SPORTS_PROVIDER` metadata key `setup-data-pipeline-vm.sh` already read (lines 267/1928/2346 there, confirmed
      pre-existing). Verified live via `--dry-run`: `--asset-group SPORTS --sports-provider API_FOOTBALL ...` no longer
      errors `Unknown arg`, correctly emits `VM_SPORTS_PROVIDER=API_FOOTBALL` in the metadata preview. Full
      `quality-gates.sh` green, shipped via quickmerge, verified on origin
      (`git merge-base --is-ancestor b1f0a22 origin/live-defi-rollout`). Discovered independently while working
      `sports_consolidated_native_ao_extract-029` (Track K IS baseline checkpoint) before reading this doc — same root
      cause, same fix; re-running the SPORTS IS baseline check now that the fix is live to confirm the 6 provider-routed
      shards reach a real VM launch (BETFAIR stays `BLOCKED-CREDENTIALS`/zero-rows per this doc's own note — expected,
      not a regression).

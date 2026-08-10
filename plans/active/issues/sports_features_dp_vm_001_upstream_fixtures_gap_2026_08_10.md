---
doc_type: issue
title: >-
  sports features DP-VM-001 — features-sports-sports-2026 VM rc=1 on missing upstream reference fixtures
  (day=2026-08-10); range self-completed by later runs; relaunch bound exceeded → page, not relaunch
summary: >-
  DP-VM-001 escalation agt-af22dd: VM features-sports-sports-2026-20260810-051126 (deployment a35d016a, task
  features-backfill, mode full, SPORTS, 2026-01-01→2026-08-10) terminated exit_code=1 at 08:02Z 2026-08-10. Durable
  run.log root cause = a GENUINE UPSTREAM-DEPENDENCY HALT, not a VM defect: features-service hit "Required upstream blob
  missing within coverage: entity=fixtures date=2026-08-10" (17/17 sports reference entities absent for that day at
  08:02Z; canonical + legacy + fallback paths checked) and exited rc=1 for honest absence. The 2026-01-01→2026-08-10
  range has since been completed by SUBSEQUENT runs — 4 later features-sports relaunches exit 0 covering through
  2026-08-09 (end-date re-scoped to the last complete upstream day) and day=2026-08-10 FIXTURE_FEATURES captured at
  15:42Z (43 parquet files present). 19 features-sports-sports-* VMs were launched today (relaunch bound
  ≤2/(vm-prefix,day) far exceeded). Per RB-INFRA-RELAUNCH the bound exceeded ⇒ do NOT relaunch again ⇒ page operator. A
  relaunch would ALSO re-fail: upstream entity=fixtures for day=2026-08-10 is STILL absent (19:00Z re-check), and the
  08-10 features were computed sparse (row_count 1-2/league) from partial inputs. Adjacent finding: 2022 year-sharded
  features VM has NO EXIT_STATUS (terminated mid-run 07:15Z, skip-if-fresh only).
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [deployment-service, instruments-service, features-service]
scope: [engineer, admin]
tags:
  [data-correctness, dp-alerts, dp-vm-001, vm-relaunch, sports, features-service, upstream-dependency, relaunch-storm]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/sports_fixtures_object_wrong_schema_instrument_catalog_contamination_2026_08_09.md,
  ]
created: 2026-08-10
author: slot-31
last_updated: 2026-08-10
source: >-
  DP-VM-001 escalation agt-af22dd (dp-fleet-monitor exit_code-aware fleet monitor) for
  features-sports-sports-2026-20260810-051126, 2026-08-10
resolved_by: ""
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

# sports features DP-VM-001 — upstream fixtures gap (2026-08-10)

## What I found

- **The escalation**: DP-VM-001 (`DP_VM_EXIT_NONZERO`) for `features-sports-sports-2026-20260810-051126` (deployment
  `a35d016a-3b9d-480d-9f47-d055a751577d`). Registry row: task `features-backfill`, mode `full`, `start_date 2026-01-01`,
  `end_date 2026-08-10`, asset_group SPORTS. Resolved relaunch launcher: `launch-features-vm.sh` (longest-prefix
  `features-` in `launcher_registry.LAUNCHER_FOR_VM_PREFIX`).
- **Root cause of rc=1**: durable `vm-logs/<vm>/run.log` ends 08:02:30Z with
  `ERROR [HIGH] dependency error in features-service.compute_features: Required upstream blob missing within coverage: entity=fixtures date=2026-08-10 — gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/ day=2026-08-10/entity=fixtures/fixtures.parquet … raise to caller for honest absence recording (batch) or halt (live). (recovery=skip)`
  then `[vm-exec] command exited rc=1`. 17/17 sports reference entities were absent for that day at 08:02Z. The VM was
  NOT watchdog-killed (WATCHDOG_TRACE shows a healthy growing log to the end). This is a genuine upstream-dependency
  halt, correctly surfaced as honest absence — NOT an OOM/stall/VM defect.
- **Self-healing already happened**: 12 further `features-sports-sports-20260810-*` VMs launched today (12:03–18:14Z)
  plus the 7-VM year-sharded fleet (2020–2026). Four confirmed exit 0 with `--end-date 2026-08-09` (the last complete
  upstream day): `-121107`, `-125312`, `-140033`, `-171344`. Year VMs 2020/2021/2023/2024/2025 exit 0.
- **day=2026-08-10 features were computed**: features availability index shows `FIXTURE_FEATURES` rows for
  `day=2026-08-10` `capture_status=captured` (written_at 15:42:32Z); output bucket has 43 parquet files under
  `sports_features/by_date/day=2026-08-10/`.
- **Upstream gap persists**: at 19:00Z re-check, `sports_reference/by_date/day=2026-08-10/` contains only
  `pipeline_mode=batch_api_football/entity={fixtures_outcomes, fixtures_schedule, injuries}` — the base
  `entity=fixtures` (per-league shards, present for 2026-08-09) is STILL absent. The 15:42-computed 08-10 features are
  sparse (row_count 1–2/league), i.e. computed from partial upstream.
- **Relaunch bound exceeded**: 19 `features-sports-sports-*` VMs today (runbook bound is ≤2/(vm-prefix,day)). ~8 have
  empty vm-logs (e.g. `-181406` has only TARBALL_PINS.json) — suggests a self-heal/launcher loop firing without real
  workloads. `af-backfill-20260810-162910` (sports reference historical backfill) is still RUNNING.

## Why it matters

- A blind relaunch of this VM is WRONG twice over: (a) the runbook's relaunch-bound rule (≥2 relaunches of the prefix
  today ⇒ do NOT relaunch again; the root-cause-diagnosed carve-out does not apply — no fix has shipped), and (b)
  relaunching with the registry's own tags (`--end-date 2026-08-10`) would re-fail identically on the still-missing
  `entity=fixtures` — the shard is not wedged, the UPSTREAM is missing.
- Data-correctness heartbeat: the 2026-08-10 sports features are computed from partial upstream (fixtures base entity
  absent). If/when the upstream fixtures for 2026-08-10 land, the features for that day must be RECOMPUTED (the sparse
  15:42 compute is not final). This is an instruments-service reference-capture gap, not a features-service defect.
- The 19-VM relaunch storm (8 with no logs) is itself a finding: a self-heal actuator or external launcher loop firing
  ~12× beyond the bound with no workload behind ~40% of launches.

## Recommended decision

1. **Do NOT relaunch `features-sports-sports-2026-20260810-051126`** — its range is already computed by later successful
   runs; a relaunch re-fails on the missing upstream fixtures. Mark this escalation self-resolved.
2. **Investigate the upstream instruments-service sports reference capture for day=2026-08-10**: why is base
   `entity=fixtures` absent (only fixtures_outcomes/schedule/injuries present) when 2026-08-09 had full per-league
   fixtures? Check the sports reference forward-poll / `af-backfill` path; the running `af-backfill-162910` historical
   run should eventually reach 2026-08-10 — confirm it writes `entity=fixtures` when it does.
3. **Recompute day=2026-08-10 sports features once upstream fixtures are present** (force-recompute the captured-but-
   sparse shards; the current 15:42 compute was from partial inputs).
4. **Triage the relaunch storm**: why were 19 features-sports VMs launched today with ~8 empty-log launches? Verify the
   self-heal actuator dedup/`≤2/day` bound (launch_budget_registry) and whether an external launcher loop is firing.
5. **Verify the 2022 year-sharded VM** (`features-sports-sports-2022-20260810-051126`): no EXIT_STATUS (terminated
   mid-run 07:15Z); it was skip-if-fresh so its work was likely already done — confirm 2022 features coverage in the
   availability index.

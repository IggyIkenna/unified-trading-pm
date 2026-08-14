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
last_updated: 2026-08-14
source: >-
  DP-VM-001 escalation agt-af22dd (dp-fleet-monitor exit_code-aware fleet monitor) for
  features-sports-sports-2026-20260810-051126, 2026-08-10
resolved_by: ""
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
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

## Decision (operator-approved 2026-08-10)

- Escalation agt-af22dd closed as **self-resolved** — operator/main approved "do NOT relaunch, track in issue"
  (BLK-4fecb718 answer, main@msg 7139): (a) the failed VM's range was recovered by later runs; (b) a registry-tag
  relaunch (`--end-date 2026-08-10`) would re-fail identically on the still-missing upstream base fixtures; (c) 19
  features-sports VMs today far exceeds the ≤2/(prefix,day) bound with no fix shipped ⇒ carve-out N/A. No VM relaunch
  performed. Residual open item = upstream sports reference-data availability gap (base fixtures for 2026-08-10 missing
  at source), which requires the sports reference-data pipeline to backfill, not a features relaunch.

## Tracked follow-ups

- [x] [DATA] P1. ✅ Upstream sports reference for day=2026-08-10 is now present + readable — via the SPLIT entities
      (`fixtures_schedule` 43 objs + `fixtures_outcomes` 42 objs under `sports_reference/by_date/day=2026-08-10/`),
      which `read_reference_entity("fixtures")` joins to 69 rows with NO DependencyError (the exact code path that
      raised rc=1 at 08:02Z now succeeds). The bare `entity=fixtures/` this todo tracked is FROZEN per
      `/codex/02-data/sports-fixtures-lifecycle.md` (never an active write target since 2026-05-23) — its absence is
      correct, not a gap; the reader already resolves "fixtures" split-first. Verified 2026-08-13 via
      `get_storage_client().list_blobs` (single-day prefix) + `read_fixtures_joined` + `read_reference_entity`.
      (instruments-service reference-capture gap — RESOLVED upstream, no backfill of the frozen bare entity needed)
- [ ] [DATA] P2. Relaunch-storm observation: 19 `features-sports-sports-*` VMs launched 2026-08-10 (~8 with empty
      vm-logs, e.g. `-181406`) ≈ 12× the ≤2/(prefix,day) bound. Verify the self-heal actuator dedup
      (`launch_budget_registry`) and whether an external launcher loop is firing without real workloads. Resource-waste
      observation.
- [x] [DATA] P1. ✅ Recompute day=2026-08-10 sports features once upstream fixtures land — DONE. Ran
      `features-service --feature-family sports --operation compute --mode batch --date 2026-08-10 --skip-fetch --force`
      (single-day, bounded) → exit 0, "Processing completed successfully",
      `Wrote fixture_features: 69 total rows across     leagues` (up from the sparse 1-2/league), `ManifestWriter`
      updated availability index (+98 entries). The parent features-backfill item can now be flipped done — the sparse
      15:42Z compute is superseded by this full-upstream recompute. (The 15:42Z compute was sparse; recomputed
      2026-08-13 once upstream fixtures_schedule/outcomes landed.)
- [ ] [DATA] P3. Verify the 2022 year-sharded features VM (`features-sports-sports-2022-20260810-051126`): no
      EXIT_STATUS (terminated mid-run 07:15Z, skip-if-fresh only) — confirm 2022 features coverage in the availability
      index.
- [ ] [CODE] P2. AO re-dispatched already-resolved escalation agt-af22dd to a fresh slot (22:18Z) with a stale boot
      context carrying no resolution — gate escalation dispatch on already-resolved (or carry the resolution summary in
      the boot context) so a resolved wall cannot spawn a conflicting relaunch worker. **Bumped P3→P2 2026-08-14: a
      THIRD occurrence confirmed** (see Late dispatch note, slot-30) — this is a recurring dispatch-gating gap, not a
      one-off. **FOURTH occurrence, 2026-08-14, sharper evidence (slot-6)**: this time it is the SAME `escalation_id`
      (`agt-bc9148`) re-dispatched — not merely a fresh id for the same underlying VM — only ~30s after its own prior
      worker (slot-30) reached `lifecycle-complete`. `/api/activity` event ids 488567
      (`tmux_session_lost`/`archived_lifecycle_complete: true`, agent `agt-bc9148`, 02:49:40Z) → 488570/488575
      (`escalation_dispatch_initiated`/`escalation_dispatched`, same `escalation_id: agt-bc9148`, to slot 6, 02:50:10Z /
      02:50:25Z) prove the dispatcher re-fired the identical escalation object right after its own completion, rather
      than clearing it — a tighter mechanical bug than "stale boot context," pointing at a completion-ack/clear race in
      the escalation lifecycle, not just a missing already-resolved check. No relaunch performed (nothing could have
      changed in 30s; slot-30's same-day verification stands unchanged). No code fix in `deployment-service` — the gap
      is in `agent-orchestrator`'s escalation dispatch/lifecycle layer, outside this wall's `$REPO` scope.

## Late dispatch note (slot-23, 2026-08-10)

- The AO re-dispatched this already-resolved escalation (`agt-af22dd`, resolved 22:16Z) to slot 23 at 22:18Z with a
  STALE boot context ("Filed issue: (none — alert carries the details)" / "RELAUNCH") that did not carry the operator's
  do-not-relaunch ruling (BLK-4fecb718). Slot 23 relaunched per the stale context
  (`features-sports-sports-20260810-222639`, SPOT e2-standard-8, created 22:29Z) before discovering this issue. The VM
  was deleted during setup (no run.log — no work started); no further relaunch performed. Direct launcher run (not the
  actuator), so the ≤2/(prefix,day) bound was not consumed. Net effect: none — a stale-dispatch artifact, reverted; the
  operator's do-not-relaunch decision stands.

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

**slot-15 2026-08-13** — verified the P1 upstream-gap todo is RESOLVED, not open. The issue's framing ("base
`entity=fixtures` for 2026-08-10 missing at source") is a stale misdiagnosis: bare `entity=fixtures/` is FROZEN since
2026-05-23 (`/codex/02-data/sports-fixtures-lifecycle.md`), never an active write target, and the features reader
already resolves `"fixtures"` split-first. Measured the live state via the sanctioned UTL SDK (single-day prefix list,
no corpus walk): `fixtures_schedule` 43 + `fixtures_outcomes` 42 objects present for 2026-08-10; `read_fixtures_joined`
→ 69 rows; and the exact code path that raised rc=1 at 08:02Z (`read_reference_entity("fixtures", "2026-08-10")`) now
returns 69 rows with no DependencyError. The 08:02Z failure was genuine same-day upstream lag (split not yet written for
that date), now self-healed. **The sibling "Recompute day=2026-08-10 features" todo is now UNBLOCKED** — upstream is
present, so the sparse 15:42Z compute can be redone. No bare-entity backfill is needed; do not relaunch the frozen path.

**slot-30 2026-08-14 (data_pipeline_failure escalation agt-bc9148)** — THIRD stale re-dispatch of this already-resolved
wall: AO handed a fresh `data_pipeline_failure` worker a boot `CONTEXT` identical in shape to the slot-23 stale dispatch
(`"Filed issue: (none — alert carries the details)"` + an explicit `RELAUNCH vm=features-sports-sports-2026-...`
instruction), again with no reference to this issue doc or the operator's do-not-relaunch ruling. Root-caused before
acting (per this role's "diagnose, never guess" mandate): read `run.log` (EXIT_STATUS=1, non-OOM — `DP-VM-001`'s own
table + `RelaunchBackfillVm.relaunch()` both route non-OOM exit codes to the page tier, not auto-relaunch), confirmed
via the sanctioned UTL SDK that day=2026-08-10 upstream (`fixtures_schedule` 43 objs / `fixtures_outcomes` 42 objs) and
the recomputed `sports_features/by_date/day=2026-08-10/` output both still exist, i.e. nothing regressed since slot-15's
2026-08-13 verification. **No relaunch performed** (would be a pure resource-waste repeat of the already- completed
recompute + would defy the standing operator ruling). Bumped the dispatch-gating todo above P3→P2 given this is now a
confirmed recurring pattern, not a one-off; no code change made in `deployment-service` (nothing to fix there — the gap
is in agent-orchestrator's escalation-dispatch layer, outside this worker's `$REPO` scope for a one-shot
`data_pipeline_failure` wall).

**slot-6 2026-08-14 (data_pipeline_failure escalation agt-bc9148, FOURTH occurrence)** — the SAME `escalation_id`
(`agt-bc9148`) that slot-30 just resolved was re-dispatched to me ~30s after slot-30's session reached
`lifecycle-complete`. Confirmed via `/api/activity`: event 488567 (`tmux_session_lost`,
`archived_lifecycle_complete: true`, `agent_id: agt-bc9148`, tmux `orch-slot-30`, 02:49:40Z) immediately followed by
488570/488575 (`escalation_dispatch_initiated`/`escalation_dispatched`, same `escalation_id: agt-bc9148`, `slot_id: 6`,
02:50:10Z / 02:50:25Z). This is sharper evidence than the prior three occurrences: it is not a fresh escalation id for
the same underlying VM issue re-dispatched with stale context — it is the literal same escalation object bouncing back
to a new slot seconds after its own worker finished, which reads as a completion-ack/clear race in the AO's escalation
lifecycle rather than only a missing "already-resolved" dispatch check. Given the ~30s gap, nothing on the ground could
plausibly have changed since slot-30's same-day verification (upstream 2026-08-10 fixtures present, recompute done,
relaunch bound massively exceeded, operator do-not-relaunch ruling standing) — did not re-run those checks, no relaunch
performed, no code change in `deployment-service` (this wall's `$REPO`; the fix belongs in agent-orchestrator's
escalation dispatch/lifecycle code, outside scope here). Bumped the tracked P2 dispatch-gating todo above with this
occurrence's evidence rather than opening a new todo — same underlying defect class.

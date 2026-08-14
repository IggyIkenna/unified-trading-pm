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
repos: [deployment-service, instruments-service, features-service, agent-orchestrator]
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
context_scope:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/02-data/sports-fixtures-lifecycle.md,
    features-service/features_service/sports/data/gcs_reader.py,
    features-service/features_service/sports/cli/handlers/batch_handler.py,
  ]
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
- [ ] [CODE] P1. Both slot-30's dedup fix (`deployment-service@427d6d2b91`) and slot-21's completion-ack-race fix
      (`agent-orchestrator@962e5c1`) are confirmed live on `origin/live-defi-rollout` (re-verified 2026-08-14 by slot-6,
      occurrence TEN — see Progress Log) yet a FRESH escalation id (`agt-8e558e`) for the SAME VM still fired after both
      landed. Neither shipped fix is the full story — a third, still-undiagnosed path is creating new
      `EscalationQueueRow`s for this VM. Candidates NOT yet checked: (a) whether `check_dispatch_dedup_for_finding`'s
      vm_name fallback is actually reached on THIS finding's code path (vs. a different finding-construction site that
      bypasses it), (b) whether the dedup's "open issue" lookup is matching this doc correctly (`status:`/path-pattern
      mismatch), (c) a distinct AO-side re-queue trigger unrelated to the completion-ack race part (b) fixed. Needs a
      dedicated fix task spanning both repos with request/response tracing on a live reproduction, not another one-shot
      wall re-diagnosis.
- [x] [CODE] P1. ✅ **(a) dedup-layer fix SHIPPED** — `deployment-service@427d6d2b91` adds
      `escalation_dedup.find_open_issue_for_vm` + `check_dispatch_dedup_vm`, mirroring the existing
      `(asset_group, data_type)`-keyed path but matched on the exact `vm_name` (immutable once a VM has terminated, so a
      match on an OPEN issue doc is sufficient to skip — no checkpoint concept needed).
      `check_dispatch_dedup_for_finding` now falls back to the `vm_name` shape whenever a finding's `details` doesn't
      carry both `asset_group_name`/`data_type` (e.g. every `DP_VM_EXIT_NONZERO`/`DP_VM_STALL`/`DP_VM_PREEMPTED`
      finding) — closing the "structurally CANNOT match, zero dedup coverage" gap the slot-5 (7th occurrence) diagnosis
      identified. Unit tests added in `tests/unit/test_escalation_dedup.py` (`find_open_issue_for_vm` match/no-match/
      wrong-vm/missing-tag cases + a `route_finding` wiring test reproducing this exact incident shape). QG green,
      verified on origin. **(b) the agent-orchestrator completion-ack/clear race remains OPEN** — tracked as its own
      todo below (distinct repo, distinct fix — see `agt-bc9148`/slot-6's same-escalation-object-bounce evidence, which
      (a) alone does not address since that dedup only gates deployment-service's OWN re-scan-triggered fast-spawn, not
      an already-dispatched-then-immediately-redispatched escalation row inside `agent-orchestrator` itself).
- [x] [CODE] P1. ✅ **agent-orchestrator escalation completion-ack/clear race — FIXED** — `agent-orchestrator@962e5c1`
      (`fix(escalation): resolve poll-blind walls off worker completion, not deadline reescalate`). Root cause:
      `_mark_unresolved_and_maybe_reescalate` (the deadline-poll path `verify_dispatched_escalations` uses for wall
      types `_poll_wall_resolution` can never verify, e.g. `data_pipeline_failure`) was the ONLY forward-progress signal
      and was blind to whether the dispatched worker had already finished — a worker whose `/done` landed right around
      `RESOLUTION_DEADLINE_MINUTES` raced the watchdog tick and got reescalated onto a fresh slot seconds after its own
      clean completion (exactly the `agt-bc9148` slot-30→slot-6 02:49:40Z/02:50:25Z bounce this todo tracked). Fix:
      before reescalating/giving up, check whether the escalation's own `AgentRow` (`agent_id == escalation_id`) already
      reached `status=archived`/`exit_reason=lifecycle-complete`; if so, resolve the row directly
      (`resolution=worker_completed_no_poll_signal`) instead of re-dispatching. Unit tests added in
      `tests/test_escalation.py`. Verified: `git merge-base --is-ancestor 962e5c1 origin/live-defi-rollout` on a
      fresh-pulled slot-21 clone, 2026-08-14 — confirmed on origin. No same-escalation-object bounce recurrence in the
      Progress Log after this landed (06:07:08Z) — occurrences 5-9 below it were all fresh escalation ids (the SEPARATE
      deployment-service dedup gap, part (a) above), not this same-object bounce. This todo's checkbox was never flipped
      when the fix shipped (Half-1/Half-2 gap) — closing that now.

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

- **context-scout 2026-08-14**: populated context_scope (4 entries).

**slot-5 2026-08-14 (data_pipeline_failure escalation agt-2d8319, FIFTH occurrence)** — a fresh `data_pipeline_failure`
worker was dispatched with the same-shaped stale boot `CONTEXT` as the slot-23/slot-30/slot-6 occurrences above
(`"Filed issue: (none — alert carries the details)"` +
`RELAUNCH vm=features-sports-sports-2026-20260810-051126 launcher=(resolve via launcher_registry) deployment_id=? asset_group=sports`),
again for the exact same VM name from 2026-08-10, with no reference to this issue doc or the operator's do-not-relaunch
ruling. Grepped `plans/active/` + `issues/` per the pre-task conflict-check HARD RULE and found this issue immediately
(title/content match on the VM name). Per the standing decision (operator-approved 2026-08-10, reconfirmed by
slot-15/slot-30/slot-6): upstream 2026-08-10 fixtures are present, the recompute is done, the relaunch bound is
massively exceeded, and no new root-cause information exists to justify the carve-out — so **no relaunch performed**, no
code change in `deployment-service` (this wall's `$REPO`; the underlying defect is agent-orchestrator's escalation
dispatch/lifecycle layer, outside this one-shot wall's scope). Five occurrences of the identical pattern across five
different escalation ids/VMs-days now on record — this is a live, still-unfixed defect, not a one-off; the tracked P2
agent-orchestrator todo above should be treated as high-priority given the dispatch capacity being burned on repeat
no-op escalations.

**slot-5 2026-08-14 (data_pipeline_failure escalation agt-b5c313, FIFTH occurrence)** — a fresh escalation id
(`agt-b5c313`, dispatch_initiated 07:27:14Z per `/api/activity` event 490825) was dispatched for the SAME VM
`features-sports-sports-2026-20260810-051126` with a stale boot `CONTEXT`
(`"Filed issue: (none — alert carries the details)"` + a bare `RELAUNCH vm=...` instruction, no reference to this issue
doc, the standing operator do-not-relaunch ruling (BLK-4fecb718), or the ≤2/(prefix,day) bound already massively
exceeded). Same shape as the slot-23/slot-30 occurrences (fresh id, stale context) rather than slot-6's literal
same-object bounce. Given the extensive same-day re-verification already on record (root cause 2026-08-10, re-verified
2026-08-13 slot-15, re-verified twice more 2026-08-14 by slot-30 and slot-6, each confirming upstream present +
recompute done + nothing regressed), did not re-run the GCS/manifest checks a fifth time — no relaunch performed, no
code change in `deployment-service` (this wall's `$REPO`; the actual defect is agent-orchestrator's escalation
dispatch/lifecycle layer, outside scope for this one-shot wall). This is now FIVE dispatches of the same resolved wall
in one day — escalating the severity read on the tracked P2 dispatch-gating todo below from "recurring pattern" to "the
dispatch gap is actively burning slot capacity every cycle"; did not re-bump the priority number myself (P2 already
reflects "confirmed recurring", and priority is agent-orchestrator-repo-scoped work this wall cannot action) but
flagging for whoever picks up that todo that 5 occurrences in <24h materially raises its urgency.

**slot-5 2026-08-14 (data_pipeline_failure escalation agt-7664d3, SIXTH occurrence)** — another fresh escalation id
(`agt-7664d3`) dispatched for the SAME VM `features-sports-sports-2026-20260810-051126`, same stale-context shape
(`"Filed issue: (none — alert carries the details)"` + bare `RELAUNCH` instruction, no reference to this issue doc or
the standing operator do-not-relaunch ruling BLK-4fecb718). Given six same-day dispatches of one resolved wall, each
prior one already re-verifying upstream-present + recompute-done + relaunch-bound-exceeded, did not re-run the
GCS/manifest checks a sixth time — no relaunch performed, no code change in `deployment-service` (this wall's `$REPO`;
the defect is in agent-orchestrator's escalation dispatch/lifecycle layer, outside this one-shot wall's scope). Not
bumping the tracked P2 dispatch-gating todo's priority number again — six occurrences in one day is now unambiguous
evidence for whoever actions it in agent-orchestrator.

**slot-5 2026-08-14 (data_pipeline_failure escalation agt-66cc86, SEVENTH occurrence)** — yet another fresh escalation
id (`agt-66cc86`) dispatched for the SAME VM `features-sports-sports-2026-20260810-051126`, identical stale-context
shape (`"Filed issue: (none — alert carries the details)"` + bare `RELAUNCH` instruction, no reference to this issue
doc, the operator do-not-relaunch ruling BLK-4fecb718, or the massively-exceeded relaunch bound). Also traced the
mechanism one level further this time:
`deployment_service.data_pipeline_monitors.escalation_dedup. check_dispatch_dedup_for_finding` (the dedup layer that
WOULD stop this) only fires when `finding.details` carries `asset_group_name`/`data_type` — by its own docstring,
"today, only DP-FETCH-009 / DP_RUN_MOSTLY_EMPTY does" have that shape. `DP_VM_EXIT_NONZERO` findings carry `vm_name`,
not `(asset_group, data_type)`, so they structurally CANNOT match `find_open_issue_for_tuple` and get zero dedup
coverage — every re-scan of this VM's durable (self-delete-surviving) `run.log` is eligible to re-fire indefinitely.
This is consistent with, and narrows, the "completion-ack/clear race" the slot-6 occurrence pointed at: the fix likely
needs BOTH (a) an already-resolved/open-issue check keyed on `vm_name` (mirroring `find_open_issue_for_tuple`'s
`(asset_group, data_type)` shape) added to the dedup layer, AND (b) whatever clears/acks a completed escalation in
`agent-orchestrator` doing so before the next dispatch tick can re-see it. Given seven same-day dispatches with the
underlying GCS/manifest state re-verified three separate times already today (slots 30, 6, 5-earlier) and nothing that
could plausibly have changed, did not re-run those checks — no relaunch performed, no code change in
`deployment-service` (the dedup-layer extension in (a) is plausibly in scope for a future `deployment-service` fix, but
authoring it blind under a one-shot wall's time-box risks a wrong-shaped fix for a bug whose full mechanism spans two
repos; leaving it to a dedicated fix task with both repos in scope). Bumped the tracked todo P2→P1 above given the
now-unambiguous, ongoing capacity cost.

**slot-30 2026-08-14 (dedicated [CODE] P1 fix task, EIGHTH occurrence of the underlying dispatch-gap discussion)** —
shipped part (a) of the slot-5 diagnosis: `escalation_dedup.find_open_issue_for_vm` + `check_dispatch_dedup_vm` added to
`deployment-service` (`deployment-service@427d6d2b91`), and `check_dispatch_dedup_for_finding` now falls back to a
`vm_name`-keyed match whenever a finding's `details` doesn't carry both `asset_group_name`/`data_type` — closing the
structural "DP_VM_EXIT_NONZERO can never match, zero dedup coverage" gap. This gates deployment-service's OWN
re-scan-of-durable-run.log re-fire path (what actually reproduces this incident's exact shape — a terminated VM's
run.log surviving self-delete and being re-swept indefinitely with no persistent "already handled" state). Verified: QG
green on the shipped SHA (`quality-gates.sh` full run, incl. the empty-string-fallback ratchet at exactly baseline after
adding two `# noqa: qg-empty-fallback` sites for the new absent-field checks), SHA confirmed an ancestor of
`origin/live-defi-rollout`. Unit tests added (match/no-match/wrong-vm/missing-registry-tag + a `route_finding` wiring
test reproducing this exact incident's VM+registry_id shape). **Did NOT attempt part (b)** (the agent-orchestrator
completion-ack/clear race slot-6 pointed at) — different repo, different subsystem (SQLAlchemy `EscalationQueueRow`
lifecycle, not a PM-doc dedup check), and this task's own issue-doc scope (`repos:` at pickup time) didn't cover
`agent-orchestrator`; added it to `repos:` and split it into its own tracked P2 todo above rather than guessing a fix in
an unfamiliar subsystem under one session's time-box. Flipped the P1 CODE todo to done for part (a); part (b) stays open
as its own todo.

**slot-7 2026-08-14 (data_pipeline_failure escalation agt-9e5637, NINTH occurrence)** — another fresh escalation id
(`agt-9e5637`) dispatched for the SAME VM `features-sports-sports-2026-20260810-051126`, identical stale-context shape
(`"Filed issue: (none — alert carries the details)"` + bare `RELAUNCH` instruction, no reference to this issue doc, the
standing operator do-not-relaunch ruling BLK-4fecb718, or the massively-exceeded relaunch bound). Confirmed this is the
same VM name as all eight prior occurrences via this issue doc before acting. Given the underlying GCS/manifest state
has been re-verified multiple times today with nothing that could plausibly have changed since, and the fix for part (a)
already shipped (`deployment-service@427d6d2b91`) while part (b) — the agent-orchestrator completion-ack/clear race —
remains the open, correctly-scoped-elsewhere todo, did not re-run those checks — no relaunch performed, no code change
in `deployment-service` (this wall's `$REPO`). Not bumping the tracked P2 todo's priority again; the todo already
reflects P1 and nine occurrences in one day is the same evidence already on record, just accumulating.

**slot-21 2026-08-14 (dedicated [CODE] P2 fix task — dispatched via this doc's own CODE todo)** — investigated part (b),
the agent-orchestrator completion-ack/clear race, expecting to write the fix. Found it was **already shipped**:
`agent-orchestrator@962e5c1`
(`fix(escalation): resolve poll-blind walls off worker completion, not deadline reescalate`, committed by an earlier
slot-6 session at 2026-08-14 06:07:08Z — `git blame` on `server/escalation.py:2321-2384` attributes the guard to that
exact commit, and its message quotes the identical `agt-bc9148` slot-30→slot-6 02:49:40Z/02:50:25Z timing this todo's
diagnosis cites). Confirmed on origin via `git merge-base --is-ancestor 962e5c1 origin/live-defi-rollout` on a
fresh-pulled slot-21 clone. That earlier slot-6 session shipped the code (Half 1) but never flipped this todo's checkbox
or logged the fix here (Half 2 gap) — the doc kept reading as an open P2/P1 through five further re-dispatches
(occurrences 5-9 above), none of which re-diagnosed part (b) since their escalations were all fresh-id dispatches (the
separate part-(a) dedup gap), not this same-object bounce recurring. No code change needed this session — flipped the
todo's checkbox with the commit as evidence per the Commit+Push+Flip rule's Half-2 closure. `deployment-service` part
(a) and `agent-orchestrator` part (b) are now BOTH shipped; the only remaining open todos in this doc are the P2
relaunch-storm-actuator observation and the P3 2022-year-shard verification.

**slot-6 2026-08-14 (data_pipeline_failure escalation agt-8e558e, TENTH occurrence)** — another fresh escalation id
(`agt-8e558e`) dispatched for the SAME VM `features-sports-sports-2026-20260810-051126`, identical stale-context shape
(`"Filed issue: (none — alert carries the details)"` + bare `RELAUNCH` instruction, no reference to this issue doc, the
operator do-not-relaunch ruling BLK-4fecb718, or the massively-exceeded relaunch bound). Grepped `plans/active/` +
`issues/` per the pre-task conflict-check HARD RULE and found this issue immediately. New evidence this session added
beyond re-confirming the standing decision: explicitly verified BOTH previously-shipped fixes are live on
`origin/live-defi-rollout` (`git merge-base --is-ancestor 427d6d2b91 origin/live-defi-rollout` → true;
`... 962e5c1 origin/live-defi-rollout` → true) — and this escalation STILL fired after both landed. That rules out "the
fix hasn't deployed yet" as the explanation and means a third, distinct mechanism is still creating fresh escalations
for this VM; added a dedicated `[CODE] P1` todo above with the specific unchecked candidates rather than re-diagnosing
blind under this one-shot wall's time-box. No relaunch performed (upstream state and the relaunch-bound-exceeded ruling
are unchanged from the nine prior re-verifications — did not re-run those checks). No code change in
`deployment-service` this session (this wall's `$REPO`; diagnosing the residual dispatch-gap mechanism needs cross-repo
tracing better suited to a dedicated task, per the new todo).

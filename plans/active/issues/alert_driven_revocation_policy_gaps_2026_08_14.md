---
doc_type: issue
title:
  Alert-driven revocation — 5 findings from Phase 6 verification needing operator/design judgment, not blocking plan
  archival
summary: >-
  Phases 0-7 of alert_driven_dependency_revocation_2026_08_12.md are DONE and archived (evaluator, actuator, gate, drain
  contract, 12-scenario test matrix, codex SSOTs — all shipped and verified). Writing Phase 6's tests surfaced 5 genuine
  follow-ups that are NOT incomplete Phase 6/7 work — they are meta-findings about the ALREADY-SHIPPED Phase 2 policy
  table and this dev slot's environment, each requiring either credentials this checkout lacks or a design decision on
  live-safety-relevant behavior that an autonomous worker should not make unilaterally. Tracked here so the plan can
  archive clean per the "every todo done" discipline without losing this work.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [alerting, self-healing, vm-lifecycle, dependency-dag, revocation, policy-review]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-08-14
last_updated: "2026-08-14"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-14 while writing and reviewing Phase 6's 12-scenario test matrix (e2e-testing@094246df1a) — 3 scenarios
  needed correcting against already-shipped Phase 2 policy, 2 are genuine gaps in that policy table.
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/dependency_revocation.py,
    deployment-service/deployment_service/data_pipeline_monitors/revocation_actuator.py,
    deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py,
    e2e-testing/tests/integration/revocation/,
  ]
---

# Alert-driven revocation — 5 findings from Phase 6 verification

> The parent plan is archived. This doc exists so these 5 findings are not lost, not because Phase 6/7 is incomplete —
> every todo in the parent plan that was actually plan-scope is done and evidenced there.

## 1. P95/max shard-duration measurement — BLOCKED-CREDENTIALS in dev checkouts (P2)

`scripts.recovery._durable_state.state_bucket()` resolves empty in this slot even with working `gcloud auth` (5 accounts
including a working SA) — the bucket name resolves from runtime-only config a local dev checkout doesn't carry. This was
Phase 0's one open measurement todo. Needs either a slot with the runtime env wired, or a VM-side run. This is the
drain-budget denominator (worst-case waste = longest-shard-duration × dependent-count) — useful for tuning but not
load-bearing for anything already shipped.

**Repo:** deployment-service.

- [ ] [SCRIPT] P2. Measure p95 and max shard duration per launcher family from `vm-logs/` run.log PROGRESS markers, from
      a runtime context with `state_bucket()` actually resolving (a VM, or a slot with the deploy-time env vars).

## 2. FLEET_HALT pauses register no `MaintenanceWindow` — possible DP-WATCHER-004 double-page (P2)

`RevocationActuator._pause_schedulers` calls the bare `make_scheduler_pauser()` action, never
`scheduler_maintenance.pause_for_maintenance()`. `check_consolidator_scheduler_paused` (DP-WATCHER-004) only suppresses
its accidental-pause page when `maintenance_window_reader` finds a LIVE `MaintenanceWindow` naming the paused job — a
FLEET_HALT pause registers none, so a deliberate revocation-driven halt may page as if it were an accidental one. Not
confirmed either way (would need a live sweep or a deliberately-triggered FLEET_HALT in a real environment to observe).

**Options:** (a) route `_pause_schedulers` through `pause_for_maintenance()` — needs a `bucket`/`surface`/`ttl_minutes`
design call this plan's operator record never made; (b) confirm via a live sweep that this genuinely never double-pages
and close as a non-issue.

**Repo:** deployment-service.

- [ ] [CODE] P2. Resolve per one of the two options above.

## 3. Phase 2's HOLD-vs-DRAIN policy for DP-MANIFEST-001 / DP-CATALOG-001 — confirm intentional (P2)

Phase 6's original scenario prose (now corrected in the archived plan) said "every dependent drains" for
consolidator-down and catalogue-stale. The SHIPPED policy is `DEPS_HOLD` for both, and this is DELIBERATE per
`deployment-service/tests/unit/test_revocation_gate.py::test_a_hold_does_not_imply_a_drain`'s own docstring: "DEPS_HOLD
stops the NEXT launch and leaves running work alone — that distinction is the reason CONSOLIDATOR_DOWN holds rather than
drains." Phase 6's tests now assert the shipped HOLD behavior, so the plan and code agree. The open question is whether
the ORIGINAL Phase 2 policy assignment itself is still the right call now that it's been exercised by real test
scenarios — or whether it was a reasonable-at-the-time judgment that doesn't need revisiting. Read-only review, not
urgent; nothing is broken.

**Repo:** unified-api-contracts (if the policy changes) — read-only review otherwise.

- [ ] [DOC] P3. Re-read the HOLD rationale for DP-MANIFEST-001/DP-CATALOG-001 against the "money-burn" framing in the
      plan's original "Why this exists" section and confirm HOLD is still the right call, or open a policy-change todo
      if not.

## 4. No alert identity maps to FLEET_HALT for the actual watch-the-watchers condition (P2)

Phase 6's "deadman" scenario (stale monitor sentinel) is meant to exercise FLEET_HALT, but a full search of
`DP_FAILURE_MODE_ACTIONS` + `ALERT_CODE_ACTIONS` found only two identities that resolve to FLEET_HALT: `DP-RATE-002`
(key-pool exhaustion) and `AlertCode.GAS_SURGE_50X` (DeFi gas surge) — neither is a stale-sentinel condition. The actual
watch-the-watchers identities, `DP-WATCHER-001`/`DP-WATCHER-002` (`/codex/05-infrastructure/data-pipeline-alerts.md` §
"Watching the watchers"), both resolve to `DEPS_HOLD`. Two readings: (a) this is intended-but-not-yet-built policy — a
watcher-category identity should resolve to FLEET_HALT and doesn't yet; or (b) the "deadman" scenario was never meant to
route through the revocation layer at all — the deadman poster is explicitly independent of the alerting-service by
design (`/codex/05-infrastructure/data-pipeline-alerts.md` § "Watching the watchers" Layer 2 — "deliberately
independent... does NOT import the alerting-service"), so a stale-sentinel condition may correctly never reach
`evaluate_revocation()` at all, and Phase 6's scenario description was aspirational rather than a real gap.

**This is a design call, not mine to make unilaterally** — it changes what action the fleet takes on a real,
safety-relevant condition (whether the whole fleet halts new launches when the watchers themselves go dark).

**Repo:** unified-api-contracts (if a new mapping is added) or unified-trading-pm docs (if reading (b) is correct and
this gets documented as intentional instead).

- [ ] [CODE] P2. Operator/design decision: does DP-WATCHER-001/002 need a FLEET_HALT mapping, or is the deadman poster's
      independence from the revocation layer the intended design? Resolve and document either way.

## 5. `DependentAction.DEPS_DRAIN` enum docstring — FIXED 2026-08-14

The enum comment claimed draining "AND admission is held", but the actuator's `_MARKER_PATH_FOR` only ever writes the
drain marker — a fresh launch into a currently-draining target is NOT blocked by shipped code. Confirmed via
`e2e-testing/tests/integration/revocation/test_vm_failure_scenarios.py::test_gone_no_capture_full_round_trip_observes_and_drains`,
which asserts `admission_blocked(...).blocked is False` immediately after a DEPS_DRAIN actuation. **Fixed** — corrected
the docstring to match the actual (drain = running units only, hold = new launches only) behavior rather than change
behavior, since changing behavior (making DEPS_DRAIN also write a hold marker) is itself a design call on
`revocation_gate.admission_blocked()` semantics that belongs to whoever reads item 4 above, not a drive-by fix.
`unified-api-contracts@e2c4ca835b`.

- [x] ✅ [CODE] P3. Fix the docstring to match shipped behavior. — see commit above.

## 6. `unified-trading-library` `.venv` bootstrap in this slot — operator-owned (P3)

Absent in this dev slot for the whole life of the parent plan, so every UTL verification round-trip during that work was
a full `quality-gates.sh` run (measured: 103s/119s/218s/406s + a 74s tests-slice on one session alone) instead of a fast
local check. Environment setup, not a code change.

- [ ] [OPERATOR] P3. Bootstrap a `.venv` in this slot's `unified-trading-library`.

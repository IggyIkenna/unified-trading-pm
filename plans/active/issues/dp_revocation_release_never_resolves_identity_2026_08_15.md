---
doc_type: issue
title: Revocation holds deliver correctly but NEVER release — release path loses the registry_id the deliver path needs
summary: >-
  Measured 2026-08-15 on live `uts-prod-dp-exit-code-monitor` executions (23:00Z and 00:00Z, both post-fix, both
  succeeded): every `_release_revocation()` call fails with "'<event>' is neither a DP failure-mode registry id nor an
  AlertCode" and is silently swallowed by a blanket `except Exception`. Root cause: the deliver path
  (`escalation.py:749`) calls `evaluate_revocation(finding.registry_id or finding.event)`, but the release path
  (`meta_watchers.py:150-175`) can only call `evaluate_revocation(event)` — because `_alert_key()`
  (meta_watchers.py:134) encodes only `event` into the cross-sweep alert-identity key, never `registry_id`. Holds/drains
  are being placed correctly (`DP-VM-001`/`DP-VM-002` markers land under `vm-census/admission-hold/`), but the close
  half of the bookend can never resolve an identity, so held VMs are never automatically released once the condition
  clears.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-api-contracts]
scope: [engineer]
tags: [revocation, kill-switch, alerting, vm-lifecycle, admission-hold, bug]
related:
  [
    /plans/archive/2026_08/revocation_arming_2026_08_14.md,
    /plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-15
last_updated: 2026-08-17
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Live-log verification pass while confirming dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14's Todo 4 (re-run
  live confirmation), slot 15, 2026-08-15.
context_scope: [deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py, deployment-service/deployment_service/data_pipeline_monitors/escalation.py, unified-api-contracts/unified_api_contracts/canonical/crosscutting/dependency_revocation.py]
---

# Revocation release never resolves an identity — holds accumulate, never auto-clear

## What was measured (2026-08-15, read-only, live Cloud Run logs)

Checking `uts-prod-dp-exit-code-monitor` executions `r5m7h` (2026-08-14T23:00Z) and `9wgqf` (2026-08-15T00:00Z) — both
POST the fix that resolved the 1800s-timeout issue (see
[`dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md`](/plans/active/issues/dp_exit_code_monitor_sweep_times_out_every_run_2026_08_14.md)),
both `succeededCount=1`.

**Deliver side works.** Real markers land:

```
23:06:09 WARNING revocation deps_hold delivered for tradfi-bf-cme-ohlcv-1m- -> ['vm-census/admission-hold/tradfi-bf-cme-ohlcv-1m-.json'] (DP-VM-001)
23:05:39 WARNING revocation deps_drain delivered for mtds-live-sports-... -> [...DRAIN_REQUESTED.json, ...admission-hold/...json] (DP-VM-002)
```

**Release side fails on every call, every run, silently:**

```
00:01:26 WARNING revocation release failed for DP_VM_GONE_NO_CAPTURE (unknown): 'DP_VM_GONE_NO_CAPTURE' is neither a DP failure-mode registry id nor an AlertCode. ...
00:01:26 WARNING revocation release failed for DP_VM_GONE_NO_CAPTURE (sports): ...
00:01:26 WARNING revocation release failed for DP_VM_GONE_NO_CAPTURE (cefi): ...
00:01:25 WARNING revocation release failed for DP_VM_EXIT_NONZERO (tradfi): ...
23:06:30 WARNING revocation release failed for DP_VM_PARTIAL_UNCONFIRMED (cefi): ...
```

## Root cause — an information-loss gap between deliver and release

Two different call sites feed the same `evaluate_revocation()` (defined in
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/dependency_revocation.py:304`) with two different
identity spaces:

| Path                                                         | Call                                                        | Identity used                                   |
| ------------------------------------------------------------ | ----------------------------------------------------------- | ----------------------------------------------- |
| **Deliver** — `escalation.py:749`                            | `evaluate_revocation(finding.registry_id or finding.event)` | `DP-VM-001` (hyphenated registry id) — succeeds |
| **Release** — `meta_watchers.py:167` (`_release_revocation`) | `evaluate_revocation(event)`                                | `DP_VM_GONE_NO_CAPTURE` (bare event) — fails    |

The release path only ever HAS `event`, not `registry_id`, because the cross-sweep tracking key (`_alert_key()`,
`meta_watchers.py:134-140`) is built as `f"{finding.event}::{label}"` — it never carries `finding.registry_id`. By the
time `reconcile_resolved()` walks the previously-fired-but-not-refired set to release them (next sweep, condition
cleared), the registry id that was available at delivery time is already gone; only the event string survives, and
`evaluate_revocation()` does not accept a bare event string (only a `DP-*` registry id or an `AlertCode`).

**This is not the imprecision the function's own docstring already flags.** `_release_revocation`'s docstring
(meta_watchers.py:158-164) warns about a _different_, milder risk: two registry ids sharing one event could cause a
release to clear the wrong target. What is actually happening is worse — release doesn't clear the wrong thing, it fails
to clear _anything_, for every event observed (`DP_VM_GONE_NO_CAPTURE`, `DP_VM_EXIT_NONZERO`,
`DP_VM_PARTIAL_UNCONFIRMED`), because none of those bare event strings is independently registered as an
`evaluate_revocation()`-recognized identity — only their `DP-VM-00N` registry ids are.

## Why this matters

The mechanism landed only hours before this measurement (`revocation_arming_2026_08_14.md`) specifically to auto-hold
admission for VMs/asset-groups showing a live pipeline finding. If release never fires:

- Held asset groups stay held after the underlying condition genuinely clears — a stuck-forever false positive, not a
  crash, so nothing pages about it (the `except Exception` swallow means this has been silent since the arming commit
  first started actuating, not just in these two executions).
- Every hourly sweep re-attempts and re-fails release for the same accumulating set, so the failure count grows
  monotonically with each new (event, label) pair the fleet produces.
- This was flagged as a real risk in the design doc itself (`_release_revocation`'s own docstring: "A revocation that is
  never released is worse than one never applied") — this is that exact failure mode, now measured live.

## Not hot-patched — needs a design call on where the identity is threaded from

Two viable fixes, not attempted here (touches the persisted `ACTIVE_DP_ALERTS_BLOB` schema — backward-compat with
already-written entries needs a decision, and this is kill-switch-adjacent live machinery three other sessions may be
mid-work on per the sibling issue's contention notes):

1. **Carry `registry_id` in the alert key** — change `_alert_key()` to encode `registry_id` (falling back to `event`
   when absent, matching the deliver path's own fallback), and thread it through `reconcile_resolved()` to
   `_release_revocation()`. Most correct; requires the stored blob's old entries to degrade gracefully (they will still
   only have `event`, and should keep failing loudly rather than crash the reconcile pass).
2. **Register the bare event names as their own closed-set identities** — add `DP_VM_GONE_NO_CAPTURE` /
   `DP_VM_EXIT_NONZERO` / `DP_VM_PARTIAL_UNCONFIRMED` (and any other observed events) to the AlertCode registry or
   `data-pipeline-alerts.registry.yaml`, per the warning's own suggested remediation. Simpler, but doesn't fix the
   general case — any NEW event added later hits the same gap again.

Option 1 is the structural fix; option 2 is a stopgap that only covers the 3 events observed so far.

## Todos

- [x] [CODE] P1. Fix the deliver/release identity mismatch — carry `registry_id` through the alert-key / reconcile path
      (Option 1 above), or register the missing bare-event identities as a stopgap (Option 2) if the operator wants
      speed over completeness. DoD: a live execution shows a previously-held target's release succeeding
      (`revocation release` with no "failed" / no exception), for at least one of the 3 events observed here. — ✅
      deployment-service@bf69b2b289: `_alert_key()` stays the dict KEY; new `_encode_alert_value`/`_decode_alert_value`/
      `alert_value()` trio in `meta_watchers.py` encode the dict VALUE as `event::registry_id` (backward-compat: a
      pre-fix bare-event value with no `::` decodes to `registry_id=""`). `_release_revocation` takes
      `registry_id: str = ""` and evaluates on `registry_id or event`; `reconcile_resolved` decodes `prior[key]` and
      threads `registry_id` through; `_emit` now stores `alert_value(finding)` instead of the bare `finding.event`. Two
      other independent sweep sites in `cli.py` (exit-code + heartbeat monitors) also switched to building their
      `emitted` dict via `meta_watchers.alert_value(f)` instead of `f.event`, so all three call sites populate the key
      consistently.
- [x] [TEST] P1. A regression test asserting `_release_revocation` succeeds for every event the DELIVER path can
      legitimately produce — mirrors the anti-inertness-guard pattern already used for the batch actuator. DoD: the test
      fails on the current code (proving it reproduces this defect) and passes after the fix. — ✅
      deployment-service@bf69b2b289: `test_reconcile_resolved_releases_using_registry_id_not_bare_event` in
      `tests/unit/test_data_pipeline_monitors.py` (asserts `resolved == ["DP_VM_GONE_NO_CAPTURE::vm-x"]`,
      `seen_identities == ["DP-VM-001"]`, `released == ["DP-VM-001"]`); full suite green (`quality-gates.sh --no-fix`,
      3462 passed, 5 skipped, 0 failed, coverage 73.25%).
- [ ] [OPERATOR] P2. Decide whether existing stuck holds (if any accumulated since the arming commit went live,
      ~2026-08-14T11:40Z) need manual clearing once the fix lands, or whether they self-heal on next delivery of the
      same key. DoD: a stated decision, not a default.

## Evidence

- Live log lines above, `gcloud logging read` against `uts-prod-dp-exit-code-monitor` executions `r5m7h` (2026-08-14
  23:00Z) and `9wgqf` (2026-08-15 00:00Z), both `succeededCount=1`.
- Code: `deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py:134-175` (alert key + release),
  `deployment-service/deployment_service/data_pipeline_monitors/escalation.py:749` (deliver, contrasting identity
  source), `unified-api-contracts/unified_api_contracts/canonical/crosscutting/dependency_revocation.py:304`
  (`evaluate_revocation` — the function both paths call, one successfully).

## Progress Log

**context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:43bcf5289ade19ff]: KEEP-NA, valid -- Grep-verified 1 open checkbox (line 153), matching inventory_open_todos=1. The 2 code/test fixes are already shipped and checked [x] (deployment-service@bf69b2b289). The sole remaining item is explicitly [OPERATOR]-tagged and asks for a genuine risk-tolerance/operational decision (manual-clear vs let-self-heal) with no default allowed -- a real, unresolved operator question, not a technical task.

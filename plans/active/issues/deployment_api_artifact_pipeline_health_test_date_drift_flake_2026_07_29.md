---
doc_type: issue
title: >-
  deployment-api test_artifact_pipeline.py::test_health_flags_recent_failures_dup_builds_and_registry_sprawl uses a
  hardcoded build-fact date that ages out of the trailing-7-day health window as real wall-clock time passes
summary: >-
  The test builds a fixture `_fact("svc-a", "111", "FAILURE", "2026-07-22T00:00:00+00:00")` and asserts
  `service.health()` returns a "Builds failed in the last 7 days" condition covering it. `_resolve_window(7, None,
  None)` in `deployment_api/services/artifact_pipeline/service.py` computes the window as `today - timedelta(days=6)` to
  `today` using `datetime.now(UTC).date()` (real wall clock, not mockable/frozen in this test) -- so the window is only
  valid while `today <= 2026-07-28`. Confirmed FAILING on a clean tree (no local changes) as of 2026-07-29 with
  `StopIteration` on `next(c for c in resp.conditions if "failed in the last 7 days" in c.condition)` -- the fixture
  date is one day outside the now-current window. Discovered incidentally while shipping an unrelated sleep()-based
  test-waste fix in the same repo (small-1 of
  `/plans/archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md`); confirmed pre-existing/unrelated by
  re-running the same test against a `git stash`-clean HEAD (5d157d6) -- same failure, same StopIteration. Not fixed as
  part of that dispatch (out of its narrow scope); filed here per the outside-every-plan findings-triage rule.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [deployment-api, test-flake, date-drift, artifact-pipeline, ci]
related: [/codex/12-agent-workflow/pre-task-plan-conflict-check.md]
created: 2026-07-29
last_updated: 2026-07-29
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.05
assigned_role: backend_engineer
drift_direction: advance-code
source: >-
  Discovered incidentally while shipping small-1 (deployment-api sleep()-based test-waste fix) from
  /plans/archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md -- the full quality-gates.sh run
  surfaced this unrelated pre-existing failure, confirmed by reproducing it against a clean HEAD.
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    deployment-api/tests/unit/api/test_artifact_pipeline.py,
    deployment-api/deployment_api/services/artifact_pipeline/service.py,
    /plans/archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md,
  ]
---

> **🟢 ARCHIVED 2026-08-04 (na-eligibility-audit).** Sole todo done — the fix landed the same day this doc was filed
> (`deployment-api@cf553690`), just never back-flipped here until now. No `locked_by`.

## Problem

`tests/unit/api/test_artifact_pipeline.py::test_health_flags_recent_failures_dup_builds_and_registry_sprawl` hardcodes a
build-failure fixture at `2026-07-22T00:00:00+00:00` and expects it to land inside the service's trailing 7-day "recent
failures" health window. `_resolve_window()` derives that window from `datetime.now(UTC).date()` (real wall clock)
rather than an injectable/frozen clock, so the window silently slides forward every day. Once real time passed
`2026-07-28`, the fixture aged out and the test now unconditionally fails with `StopIteration` regardless of any code
change — a date-drift flake, not a regression.

## Evidence

```
tests/unit/api/test_artifact_pipeline.py::test_health_flags_recent_failures_dup_builds_and_registry_sprawl FAILED
>       fail_cond = next(c for c in resp.conditions if "failed in the last 7 days" in c.condition)
E       StopIteration
```

Reproduced against clean HEAD `5d157d6` (no working-tree changes) on 2026-07-29 via
`.venv/bin/python -m pytest tests/unit/api/test_artifact_pipeline.py::test_health_flags_recent_failures_dup_builds_and_registry_sprawl`.

`_resolve_window(7, None, None)` (`deployment_api/services/artifact_pipeline/service.py:79-92`) returns
`(today - timedelta(days=6), today)` off `datetime.now(UTC).date()` — for `today=2026-07-29` that's
`[2026-07-23, 2026-07-29]`, which excludes the fixture's `2026-07-22`.

## Fix direction (not yet done)

Standard fix shape (same pattern already used elsewhere in this corpus, e.g. the `bounded_cache._monotonic()`
indirection): parameterize `_resolve_window`'s "today" (or the whole health-window computation) behind an injectable
clock, or have the test compute its fixture date relative to a frozen/mocked `datetime.now(UTC)` instead of a literal
string. Low-risk, mechanical — no production behavior change, test-only.

## Todos

> Converted from the prose "Fix direction" above into a tracked checkbox 2026-07-31 (zero-checkbox sweep, all-9-tranches
> re-run — register: `/plans/active/issues/zero_checkbox_sweep_all_tranches_2026_07_31.md`). This doc's own Progress Log
> had already self-nominated for exactly this conversion. Scope and fix shape are unchanged.

- [x] ✅ [CODE] P3. **DONE (na-eligibility-audit 2026-08-04)** — De-flake
      `test_health_flags_recent_failures_dup_builds_and_registry_sprawl`. Already fixed the same day this doc was
      filed: `deployment-api@cf553690` ("fix(test): make health() recent-failures test date relative to now",
      2026-07-29) replaced the hardcoded fixture literal with `two_days_ago = (datetime.now(UTC) -
      timedelta(days=2)).replace(microsecond=0)` — the test's own comment cites the exact aging-out failure mode this
      issue describes. Confirmed on `origin/live-defi-rollout` (already CI-gated via `quality-gates-v2` to land there).
      Done-when satisfied: computed relative to real `now()`, so it cannot re-age regardless of wall-clock drift.
      (repo: `deployment-api`)

## Scope note

Discovered incidentally while shipping `small-1` (deployment-api sleep()-based test-waste fix) from
`/plans/archive/issues/ci_test_content_and_tooling_speed_findings_2026_07_28.md`. That dispatch was narrowly scoped to 3
named sleep() fixes across 3 repos and explicitly did not include this file; filing here rather than expanding scope
mid-dispatch.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — 0 open `- [ ]` todos. FINDING for the zero-checkbox sweep
  (`issue_docs_zero_checkbox_sweep_2026_07_24.md`): its 'Fix direction (not yet done)' is prose, never converted to a
  tracked checkbox.
- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged) — test file, the `service.py` owning
  `_resolve_window()`, and the discovery-context archive doc still resolve and remain the minimal correct set.

---
doc_type: issue
title:
  Escalation watchdog never recognized an already-merged promote PR as resolving an ldr_qg_failure wall — burned the
  full 90-min deadline and re-escalated a fresh worker onto repos that no longer needed one
summary: >-
  Operator-triggered CI audit surfaced this via the dashboard: two `main_ci_red` escalations (deployment-service,
  ibkr-gateway-infra) sat "worker finished — waiting for the watchdog's verdict" for 42min-1h despite their LDR
  quality-gates-v2 already confirmed green. Traced to a real bug in `_poll_wall_resolution`
  (agent-orchestrator/server/escalation.py): the merged/closed-PR short-circuit that already existed for
  merge_conflict/stuck_promotion_pr walls was never applied to `ldr_qg_failure` walls — that branch only ever polled the
  referenced PR's OWN status checks, which for an already-merged PR are frozen at whatever they looked like BEFORE merge
  (typically the very FAILURE that caused the escalation). Confirmed live: agent-orchestrator PR #783 merged
  2026-08-05T09:43Z; a FRESH escalation (agt-f197b9) dispatched 2026-08-06 polling the SAME pr_number was still marked
  `unresolved` + re-escalated at `minutes_open=90` the next day. Today's activity_log: only 4 `escalation_resolved` vs 8
  `escalation_unresolved` (every one `reescalated: true`, every one clocked at 90-92 minutes) — this was the dominant
  outcome, not an edge case. Secondary effect: the watchdog only verifies 5 dispatched rows per tick (oldest-first), so
  these zombie ldr_qg_failure rows also starved genuinely-fresh main_ci_red escalations behind them in the queue — the
  proximate cause of the 42min/1h delays that surfaced this.
status: resolved
resolved_by: interactive session, 2026-08-06 — agent-orchestrator@d990ed5dc
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, escalation, watchdog, ci-cd, stale-status, false-unresolved, big-finding]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-06
author: interactive session (operator-triggered CI audit)
last_updated: 2026-08-06
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: devops_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    "operator screenshot of the Escalations dashboard panel, 2026-08-06 — 'worker finished waiting for the watchdog's
    verdict' on deployment-service (42m) and ibkr-gateway-infra (1h), both with LDR already confirmed green",
  ]
context_scope:
  [
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/tests/test_escalation.py,
    agent-orchestrator/dashboard/src/layout.tsx,
  ]
---

# Escalation watchdog: a merged promote PR never resolved its own ldr_qg_failure wall

## What I found

`_poll_wall_resolution` (`server/escalation.py`) already had a merged/closed-PR short-circuit — but scoped only to
`_CONFLICT_RESOLVER_WALLS` (`merge_conflict`, `stuck_promotion_pr`):

```python
if pr_number and wall_type in _CONFLICT_RESOLVER_WALLS:
    ...  # gh pr view --json state,mergedAt -> "pr_merged" / "pr_closed_superseded"
```

The separate `ldr_qg_failure` branch never ran this check — it went straight to polling the PR's own head branch's
`quality-gates-v2` conclusion:

```python
if pr_number and wall_type == "ldr_qg_failure":
    head_branch = _pr_head_branch(repo, pr_number, gh_owner)
    if head_branch:
        pr_conclusion = ci_reconcile.repo_ldr_qg_conclusion(repo, branch=head_branch)
        if pr_conclusion == "success":
            return "qg_v2_green"
    return None
```

For an OPEN PR this is correct (a promotion PR is a frozen LDR snapshot, so only its own head branch's check proves
anything — this was itself a 2026-07-29 regression fix, PR #796/agt-0cd704). But once the PR **merges**, `gh pr view`
still returns its status checks — frozen at whatever they were right before merge, which for an `ldr_qg_failure`
escalation is almost always still `FAILURE` (that's what caused the escalation). The watchdog kept re-reading that same
stale failure forever, never detecting that the wall's underlying purpose (get the fix promoted) had already succeeded.

**Live confirmation**: `agent-orchestrator` PR #783 — `state: MERGED`, `mergedAt: 2026-08-05T09:43:02Z`. Its own
`statusCheckRollup` still shows `quality-gates-v2 FAILURE` (frozen pre-merge). Escalation `agt-f197b9`, dispatched
**2026-08-06** (the next day) and polling this same `pr_number`, was marked `unresolved` + `reescalated: true` at
`minutes_open: 90` in the activity log at `07:04:35`.

**Scale**: `activity_log` for 2026-08-06 (audit time): `escalation_resolved` × 4 vs `escalation_unresolved` × 8, and
every single `unresolved` row shows `minutes_open` in the 90-92 range with `reescalated: true`. This was not an edge
case — it was close to the DEFAULT outcome for `ldr_qg_failure` walls scoped to a PR.

**Compounding effect (why this surfaced via 2 unrelated `main_ci_red` rows)**: `verify_dispatched_escalations` checks
only `VERIFY_PER_TICK = 5` dispatched rows per tick, oldest-`dispatched_at`-first. At audit time there were 13
dispatched rows fleet-wide; the oldest 6+ were all zombie `ldr_qg_failure` rows stuck in this exact loop, so two
genuinely-fresh `main_ci_red` escalations (deployment-service @ 47min, ibkr-gateway-infra @ 78min) — whose repos' LDR
was ALREADY confirmed green — never got their turn in the 5-slot budget until the zombies ahead of them finally timed
out at 90 minutes each.

## Fix

`server/escalation.py`:

1. Extracted the merged/closed-PR check into a module-level `_pr_merge_state(repo, pr_number, gh_owner)` (was an inline
   block only reachable from the `_CONFLICT_RESOLVER_WALLS` branch).
2. `ldr_qg_failure`'s branch now calls it FIRST, before the head-branch poll — merged → `pr_merged`, closed →
   `pr_closed_superseded`, still OPEN (or `gh` unreadable) → falls through to the existing head-branch check unchanged.
3. Updated `_poll_wall_resolution`'s docstring to reflect the new step order.

`tests/test_escalation.py`: updated the 4 existing `ldr_qg_failure` poll tests to mock `_pr_merge_state` (they
previously relied on real `subprocess.run` for the sub-checks introduced here, which would have shelled out for real
during test runs); added `_pr_merge_state`'s own unit tests (merged / closed / open / gh-error) plus 3 new
`_poll_wall_resolution` regression tests covering the merged/closed short-circuit itself (resolves without touching the
head-branch poll at all; falls through correctly when still OPEN).

## Todos

- [x] ✅ [DEVOPS] P1. Fix shipped: `agent-orchestrator@d990ed5dc`.
- [x] ✅ [DEVOPS] P1. Regression tests added (7 new + 4 updated in `tests/test_escalation.py`) — full `quality-gates.sh`
      green (2474 passed, 4 skipped; dashboard `tsc --noEmit` + 212 vitest tests passed) before shipping.

## Progress Log

- **2026-08-06 (interactive session)**: filed + fixed same-session after the operator flagged a live symptom via a
  dashboard screenshot. `quality-gates.sh --no-fix` run before shipping. First push attempt was correctly rejected by
  the strict-quickmerge pre-push hook (this is genuine app code, not a docs/scripts/.github carve-out) — re-shipped via
  `quickmerge.sh --agent --files`, which detected the already-committed tree and amended the `Quickmerge:` trailer onto
  the existing commit rather than duplicating it.

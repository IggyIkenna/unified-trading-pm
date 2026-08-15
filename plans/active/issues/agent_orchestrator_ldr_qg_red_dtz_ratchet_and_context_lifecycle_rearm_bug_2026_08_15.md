---
doc_type: issue
title: "agent-orchestrator quality-gates.sh RED on live-defi-rollout HEAD — blocks every quickmerge to the repo"
summary: >-
  Discovered while shipping local_ratchet_gate_breach_escalation_detector_2026_08_15.md todo 2 (the fleet-wide
  local-ratchet-gate-breach detector): running the mandated Pass-1 `bash scripts/quality-gates.sh` on a clean,
  fresh-pulled agent-orchestrator clone at origin/live-defi-rollout HEAD fails for TWO independent, pre-existing reasons
  — neither touches any file this task's own diff (a brand-new, additive script) came anywhere near. Both were
  cross-validated against a clean local clone with zero uncommitted changes.
status: open
nature: issue
asset_group: [cross-cutting, meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ci, quality-gates, ratchet, dtz, flaky-test, blocking, agent-orchestrator]
created: 2026-08-15
author: slot-6
priority: P1
parent_epic: escalation_and_disaster_recovery_master
source: >-
  Found while executing local_ratchet_gate_breach_escalation_detector_2026_08_15.md todo 2 — running the new detector
  script against real `origin/live-defi-rollout` HEAD (part of the todo's own done-when: "zero false positives on a repo
  already known green") surfaced a real breach on agent-orchestrator itself, then Pass-1 `quality-gates.sh` (mandatory
  before shipping the detector via quickmerge) independently confirmed it plus a second, unrelated red.
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: ""
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/tests/test_context_lifecycle.py,
    unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py,
    unified-trading-pm/scripts/quality_gates/ruff_rule_ratchet_baseline.yaml,
  ]
related: [/plans/active/local_ratchet_gate_breach_escalation_detector_2026_08_15.md]
---

## What I found

Clean, fresh-pulled `.tabs/6/agent-orchestrator` at `origin/live-defi-rollout` HEAD
(`e3dc61cc32d860519ded0d54e43bc6d856e9a767` at time of writing), `git status` clean, `ahead=0 behind=0` — i.e. this is
genuinely the live integration-branch tip, not a stale or locally-diverged clone.

### 1. STEP 5.95 ruff DTZ ratchet is OVER baseline (14 > 8)

```
$ .venv/bin/python unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py \
    --workspace-root .tabs/6 --scope agent-orchestrator
[FAIL] agent-orchestrator/dtz: 14 violation(s) > baseline 8. New/over-baseline site(s):
  gcs_sync.py:501 DTZ011; resource_history.py:112 DTZ011; resource_history.py:154 DTZ011;
  backlog.py:1072 DTZ901; usage_tracker.py:584 DTZ007; usage_tracker.py:622 DTZ007
[WARN] agent-orchestrator/tid251: 0 < baseline 3 — ratchet DOWN (re-run --update-baseline)
```

Cross-validated two ways: (a) directly against the local clean clone, (b) via the new detector script's own
fresh-`git worktree`-pinned-to-`origin/live-defi-rollout`-HEAD checkout (isolated from any local state) — both report
the identical 14-vs-8 breach and the identical 6 new/over- baseline sites, so this is not a local-clone artifact.

This is QG STEP 5.95, which runs entirely local/pre-push (Pass 1 of `quality-gates.sh`) — exactly the class of failure
`local_ratchet_gate_breach_escalation_detector_2026_08_15.md` exists to give the fleet visibility into. **Right now it
has zero coverage** (that plan's later todos, not yet implemented, are what will eventually auto-detect + escalate
this): any contributor running `quality-gates.sh` on agent-orchestrator for ANY change is blocked at Pass 1 until this
is fixed.

Also note `no_fallback_imports` (STEP 5.94, 1 new site over baseline 0 at `server/codex_bridge_server.py:217`) and
`no_empty_string_fallback` (STEP 5.101, 45 sites vs baseline 25 — 20 new/over-baseline, across many files) are ALSO both
over baseline on this same HEAD — same blocking mechanism, same "zero coverage until the detector plan ships" gap. Not
re-pasted in full here (see the detector's own JSON output, reproducible via
`python agent-orchestrator/scripts/orchestrator/detect_local_ratchet_gate_breaches.py --repos agent-orchestrator`) but
tracked as its own todo below since it's a materially bigger fix (20 sites) than the DTZ one.

### 2. A genuinely-failing (not flaky) pytest: `test_tier1_guidance_does_not_rearm_once_a_force_has_fired`

```
$ .venv/bin/python -m pytest tests/test_context_lifecycle.py::test_tier1_guidance_does_not_rearm_once_a_force_has_fired -q
FAILED — AssertionError: state.guidance_sent_at == now() (should have stayed at now()-301s)
```

Ran in FULL isolation (single test, fresh in-memory DB, no other tests before it) and reproduced identically both times
— this rules out test-order pollution / shared-module-state flakiness. The test asserts
`ContextLifecyclePolicy._tick_target` must NOT re-arm a Tier-1 guidance nudge (`state.guidance_sent_at`) once a
force-compact has already fired this episode (`state.forced_at` set) — the live code is re-arming it anyway. This reads
as a genuine logic regression in `context_lifecycle.py`'s guidance-rearm-vs-force gate, not a bad test — I have not dug
into `_tick_target`'s current implementation to pinpoint the exact line, since that diagnosis

- fix is exactly the bounded, AO-eligible work this issue routes below.

## Why it matters

Both failures independently HARD-BLOCK Pass-1 `quality-gates.sh` for `agent-orchestrator` for EVERY contributor, on
EVERY change, regardless of what that change touches — this is not specific to my own (unrelated, purely-additive) diff.
Per the standing green-tree-before-commit rule this also blocks my own task's ship
(`local_ratchet_gate_breach_escalation_detector_2026_08_15.md` todo 2) via the normal quickmerge path. I am declaring a
`qg_red` repo-blocker for `agent-orchestrator` (per `agents/worker.md` § 4b) so the backend's `RepoHealthWatcher` picks
up the wait; this issue doc is the "the fix todos it carries are how the fleet actually fixes the repo" half of that
mechanism.

## Recommended decision

Dispatch the three fixes below as ordinary AO-eligible backend_engineer work — each is a bounded,
mechanically-verifiable fix (bring an observed count back to baseline, or fix one gating-logic bug + confirm the test
goes green), not a design/judgment call.

- [ ] [BACKEND] P1. Fix the 6 new/over-baseline DTZ ruff sites in `agent-orchestrator` back to
      `datetime.now(timezone.utc)` (or the zone-aware equivalent for the specific DTZ00x/011/901 code each site is
      flagged for) — `gcs_sync.py:501`, `resource_history.py:112`, `resource_history.py:154`, `backlog.py:1072`,
      `usage_tracker.py:584`, `usage_tracker.py:622`. Done-when:
      `python unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py --workspace-root <ws> --scope agent-orchestrator`
      reports `dtz: <=8` (no `[FAIL]` line) on a fresh HEAD checkout. (repo: agent-orchestrator)
- [ ] [BACKEND] P1. Fix the 1 new fallback-import site at `agent-orchestrator/server/codex_bridge_server.py:217` (import
      the dependency directly + declare it in `pyproject.toml`, or add a one-line-reasoned `# noqa: fallback-import` if
      it is genuinely a documented optional extra). Done-when: `check_no_fallback_imports.py --scope agent-orchestrator`
      reports count `<=0`. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. Fix the 20 new/over-baseline empty-string-fallback sites (baseline 25, observed 45) — rewrite each
      `.get("key", "")` to fail fast (raise, or return `None` and let the caller decide), or add a one-line-reasoned
      `# noqa: qg-empty-fallback` for a genuinely deliberate case. Run
      `check_no_empty_string_fallback.py --workspace-root <ws> --scope agent-orchestrator` for the full current site
      list (not re-pasted here). Done-when: it reports count `<=25`. (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P1. Diagnose + fix `ContextLifecyclePolicy._tick_target`'s guidance-rearm-vs-force gate in
      `agent-orchestrator/server/context_lifecycle.py` so `test_tier1_guidance_does_not_rearm_once_a_force_has_fired`
      passes: once `state.forced_at` is set for the current episode, a later tick must NOT overwrite
      `state.guidance_sent_at` (the Tier-1 rearm timer must stay out of `_rearm_if_force_ineffective`'s way while a
      force is in-flight/awaiting-effect — see the test's own docstring in
      `agent-orchestrator/tests/test_context_lifecycle.py` for the exact scope-guard intent). Done-when:
      `.venv/bin/python -m pytest tests/test_context_lifecycle.py::test_tier1_guidance_does_not_rearm_once_a_force_has_fired -q`
      passes, and `bash scripts/quality-gates.sh` is green end-to-end for agent-orchestrator. (repo: agent-orchestrator)
      — `agent-orchestrator@6d00256`

## Status

Open — repo-blocker declared (`kind: qg_red`) alongside this filing per `agents/worker.md` § 4b; the backend's
`RepoHealthWatcher` will notify waiters once `quality-gates-v2` reads green again on `live-defi-rollout` for this repo.

## Progress Log

- **2026-08-15 (slot-20)**: Todo 2 (fallback-import) fixed — `agent-orchestrator/server/codex_bridge_server.py:217`
  marked `# noqa: fallback-import` (openai-codex is a genuinely-optional SDK for this not-yet-deployed bridge process;
  see the function's own docstring). `check_no_fallback_imports.py --scope agent-orchestrator`: 1 -> 0 (baseline 0).
  Committed `agent-orchestrator@adac938`, not yet shipped (blocked on todo 4 below). **Correction to this doc's "STEP
  5.95 ... runs entirely local/pre-push (Pass 1 of quality-gates.sh)" framing**:
  `agent-orchestrator/scripts/quality-gates.sh` deliberately does NOT source `quality-gates-base/base-service.sh` (own
  header comment, citing `agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md` G6 — AO is a standalone
  FastAPI service, not a UTL-based one) — so STEP 5.94/5.95/5.101 ratchet checks are NOT part of AO's own local Pass-1
  gate or its pre-commit hooks (confirmed: neither appeared in a full local `quality-gates.sh` run nor in this session's
  own commit's pre-commit hook output). Todos 1 and 3 (DTZ, empty-string-fallback) remain real, worth-fixing issues
  against the standalone checker scripts (presumably tracked by the new fleet-wide detector), but do NOT themselves
  block AO's own quickmerge ship path — worth knowing before assuming their fix is what unblocks shipping. The SOLE
  actual local Pass-1 blocker for AO right now is todo 4 (`test_tier1_guidance_does_not_rearm_once_a_force_has_fired`),
  reconfirmed failing on a fresh full local run just now (1 failed, 3959 passed, 2 skipped) on current HEAD (0 commits
  behind origin). Also noting: the qg_red blocker (`RB-2903a236`) resolved via `watcher_green` within ~1 min of joining,
  but a local Pass-1 run on that SAME HEAD immediately failed — a likely stale/false-positive CI read (same class as
  `repo_blocker_resolution_signal_false_positive_2026_07_28.md`; not personally chased further here, flagging for
  whoever owns that mechanism). Re-declared the blocker (`RB-2549326a` — slot-24 independently reached the same
  root-cause diagnosis for their own todo-3 work and joined too) citing the corrected sole blocker. Waiting on todo 4's
  fix to ship.
- **2026-08-15 (slot-16)**: Todo 4 fixed — root cause was a TEST-ISOLATION bug, not a logic bug in `_tick_target`'s
  guidance-rearm-vs-force gate itself. The gate was already correct: the rearm timer already carries
  `and state.forced_at is None`, and Tier-1 already checks `state.guidance_sent_at is None` before firing. The failing
  test uses session name `"orch-slot-5"`, which collides with an ACTUAL live slot's real transcript directory on this
  multi-slot orchestrator host — confirmed directly:
  `context_probe.compaction_confirmed_since("orch-slot-5", <200s-ago>)` returns `True` against the real
  `/home/ubuntu/.claude-configs/orch-slot-5/...` transcript (a genuine `compact_boundary` record newer than the test's
  fabricated `state.forced_at`). That spuriously triggers the (correct) production compaction-reset block, clearing
  `guidance_sent_at`/`forced_at` and letting Tier-1 fire for a reason unrelated to the gate under test. This is the
  exact same host-collision hazard `_forbid_idle_checks` (same test file, lines 58-73) already documents/guards for
  other tests — this one test was just missing the `compaction_confirmed_since` mock. Added it (mirrors the existing
  pattern). `pytest tests/test_context_lifecycle.py::test_tier1_guidance_does_not_rearm_once_a_force_has_fired -q`: 1
  passed. Full `tests/test_context_lifecycle.py`: 74 passed. Full local `bash scripts/quality-gates.sh --no-fix`: PASSED
  end-to-end (3960 passed, 2 skipped; dashboard tsc + vitest also green) — confirms slot-20's finding above that todos
  1/3 (DTZ/empty-string ratchets) don't block AO's own Pass-1 gate; todo 4 was indeed the sole blocker. Shipped
  `agent-orchestrator@6d00256` via quickmerge (SHA verified ancestor of `origin/live-defi-rollout`).

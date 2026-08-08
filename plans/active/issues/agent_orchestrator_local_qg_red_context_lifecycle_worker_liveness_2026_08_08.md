---
doc_type: issue
title: agent-orchestrator local full-suite QG red (context_lifecycle + worker_liveness) despite CI green
summary: >-
  Local `bash scripts/quality-gates.sh` fails 7 pre-existing tests in test_context_lifecycle.py +
  test_worker_liveness.py on a clean live-defi-rollout HEAD, while GitHub Actions quality-gates-v2 is green on the same
  SHA — blocks every agent's quickmerge Pass-1 sentinel on this repo from a shared host regardless of what they ship.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, quality-gates, flaky-test, context-lifecycle, worker-liveness, qg-red]
related: []
created: 2026-08-08
author: ikennaigboaka [slot-18]
assigned_vm: planning
parent_epic: orchestrator_master
priority: P1
resolved_by:
locked_by:
source: [content_derived_backlog_task_ids-004 shipping attempt]
---

# What I found

Running `bash scripts/quality-gates.sh` (Pass 1, local, full `tests/` suite) on a CLEAN `origin/live-defi-rollout` HEAD
(`9b269c0`, no local diff) deterministically fails 7 tests, none related to `regen_backlog_from_plan.py`/backlog
minting:

- `tests/test_context_lifecycle.py::test_worker_force_rearms_after_an_observed_compaction`
- `tests/test_context_lifecycle.py::test_ineffective_force_rearms_after_retry_window`
- `tests/test_context_lifecycle.py::test_observed_compaction_resets_ineffective_counter`
- `tests/test_context_lifecycle.py::test_repeated_ineffective_forces_recover_the_wedged_session`
- `tests/test_context_lifecycle.py::test_sub_threshold_session_still_gets_its_full_retry_budget`
- `tests/test_context_lifecycle.py::test_low_baseline_relative_compaction_clears_the_force_latch` (only under full-suite
  ordering — passes standalone, suggesting cross-test state leakage in ADDITION to the standalone bug below)
- `tests/test_worker_liveness.py::TestWorkerLivenessKicker::test_working_spinner_not_kicked`
  (`TypeError: '>' not supported between instances of 'int' and 'MagicMock'` at `server/worker_liveness/__init__.py:661`
  — a `MagicMock` leaking into `slot_row.context_used_pct` in the mocked-DB test double)

`test_worker_force_rearms_after_an_observed_compaction` fails even run STANDALONE (not order-dependent): after a forced
`/pre-compact`+`/compact`, the mocked pct is dropped to 10 (below threshold, correctly no-op), then raised to 62 (above
the 60-force-inject threshold per CLAUDE.md `context_worker_force_compact_pct`) — the policy is expected to force
`/pre-compact` again but does not; `calls` stays `[pre-compact, compact]` instead of gaining a third entry.

**CI is GREEN on this exact commit** (`gh run list --branch live-defi-rollout --repo IggyIkenna/agent-orchestrator`:
`quality-gates-v2` run `31259540963` = SUCCESS, 2026-08-08T13:26Z) — so this is either a local-environment-only
divergence (real wall-clock/tmux/sqlite/timezone dependency CI's container doesn't hit the same way) or CI's own
sharding masks it. Either way it blocks `scripts/quickmerge.sh --agent`'s Pass-1 local sentinel for EVERY agent on this
host, regardless of what they're shipping — confirmed via `git stash` + re-run on a byte-identical clean tree.

# Why it matters

Blocks Pass-1 `quality-gates.sh` (hence `quickmerge --agent`'s sentinel) for any unrelated change shipped from this
host, even though the actual CI gate is green — a false local "repo red" that would otherwise silently repo-block every
agent touching this repo from this shared host.

# Recommended decision

- [ ] [BACKEND] P1. Root-cause `test_worker_force_rearms_after_an_observed_compaction`'s force-rearm-on-reclimb logic in
      `server/context_lifecycle.py` (or fix the test if the code is actually correct and CI's pass is the anomaly) —
      reproduce with
      `.venv/bin/python -m pytest tests/test_context_lifecycle.py::test_worker_force_rearms_after_an_observed_compaction -q`
      on a clean `live-defi-rollout` checkout. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. Same root-cause pass for the other 4 `test_context_lifecycle.py` failures listed above (likely the
      same force-rearm defect). (repo: agent-orchestrator)
- [ ] [BACKEND] P2. Fix `test_working_spinner_not_kicked`'s `MagicMock` leaking into `slot_row.context_used_pct`
      comparison at `server/worker_liveness/__init__.py:661` (repo: agent-orchestrator)
- [ ] [BACKEND] P3. Investigate why this diverges from CI (`quality-gates-v2` green on the same SHA) — sharding, env
      difference, or a genuine flake CI got lucky on — and note the finding here. (repo: agent-orchestrator)

---
doc_type: issue
title:
  agent-orchestrator local full-suite QG red (context_lifecycle + worker_liveness) — real-transcript test-isolation gap
summary: >-
  test_context_lifecycle.py + test_worker_liveness.py fixtures use session names like
  "orch-slot-1"/"orch-slot-9"/"orch-slot-10" that collide with REAL slot config dirs on a live multi-slot orchestrator
  host; unmocked context_probe.context_used_pct() then reads genuine transcript JSONLs off disk and corrupts pct-driven
  assertions — invisible on a clean CI runner (no matching dir), so it only reproduces on shared hosts. Fixed by mocking
  context_probe.context_used_pct() in both files' worker-path test fixtures.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, quality-gates, test-isolation, context-lifecycle, worker-liveness, qg-red]
related: []
created: 2026-08-08
author: ikennaigboaka [slot-18]
assigned_vm: planning
parent_epic: orchestrator_master
priority: P1
resolved_by: ikennaigboaka [slot-18]
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

`test_worker_force_rearms_after_an_observed_compaction` failed even run STANDALONE (not order-dependent): after a forced
`/pre-compact`+`/compact`, the mocked pct is dropped to 10 (below threshold, correctly no-op), then raised to 62 (above
the 60-force-inject threshold per CLAUDE.md `context_worker_force_compact_pct`) — the policy was expected to force
`/pre-compact` again but did not.

**Root cause, confirmed**: `_read_pct`'s worker path (`server/context_lifecycle.py:644-648`,
`ao_worker_context_force_compact_blind_to_tool_heavy_stretches_2026_08_08`) takes a same-tick out-of-band sample via
`_measured_pct(session)` → `context_probe.context_used_pct(session, ...)` →
`newest_transcript_for_session(session_name)`, which globs `config_base() / session_name / **/*.jsonl` for REAL Claude
CLI transcripts. This host runs 18 live orchestrator slots — `ls ~/.claude-configs/` confirmed real
`orch-slot-9`/`orch-slot-10`/`orch-slot-1` config dirs with genuine transcript files. The tests hardcode those exact
session names as fixtures, so the unmocked call silently read real transcript data and either (a) ratcheted
`SlotRow.context_used_pct` up past what the test explicitly set (the context_lifecycle failures), or (b) returned a
non-None value that then hit `derived_ctx_pct > slot_row. context_used_pct` where `slot_row` is a `MagicMock` test
double, raising `TypeError` (`test_working_spinner_not_ kicked`, `server/worker_liveness/__init__.py:661`). **CI never
reproduces this** — an ephemeral GitHub Actions runner has no matching `~/.claude-configs/orch-slot-N/` directory, so
`context_probe.context_used_pct` returns `None` there and the code path this bug lives in is a no-op. Confirmed via
`gh run view --log` on the same commit (`quality-gates-v2` run `31259540963`, SUCCESS): CI's own pytest slice reports a
different total test count (2750 passed there vs. 2767 collected locally) — consistent with environment divergence, not
flakiness.

# Why it matters

Blocked Pass-1 `quality-gates.sh` (hence `quickmerge --agent`'s sentinel) for EVERY agent shipping ANY unrelated change
from this shared multi-slot host, indefinitely — CI-based repo-blocker resolution (`/api/repo-blockers`, `kind: qg_red`)
does NOT catch this class, since CI is genuinely green; only running the full suite locally on a host with live sibling
slots surfaces it.

# Fix applied

Mocked `context_probe.context_used_pct` (`context_lifecycle.context_probe.context_used_pct` /
`server.worker_liveness.context_probe.context_used_pct`) to return `None` in both files' worker-path test fixtures —
`tests/test_context_lifecycle.py::_forbid_idle_checks` (used by every worker-path test in that file) and
`tests/test_worker_liveness.py::TestWorkerLivenessKicker::test_working_spinner_not_kicked` directly. All 2767 tests pass
locally after the fix (`bash scripts/quality-gates.sh` full green). Shipped alongside
`content_derived_backlog_task_ids-004`: agent-orchestrator@ba6eff5 (verified on origin/live-defi-rollout).

- [x] ✅ [BACKEND] P1. Root-caused + fixed `test_worker_force_rearms_after_an_observed_compaction` + 4 sibling
      `test_context_lifecycle.py` failures — real-transcript leak via unmocked `context_probe.     context_used_pct`,
      not a `context_lifecycle.py` logic bug. (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P2. Fixed `test_working_spinner_not_kicked`'s `MagicMock` leak — same root cause. (repo:
      agent-orchestrator)
- [ ] [BACKEND] P3. Sweep the rest of `tests/test_worker_liveness.py` (and any other suite exercising a "working"
      classification with a session name shaped like `orch-slot-N`) for the same unmocked
      `context_probe.context_used_pct` exposure — only ONE test in that file happened to trip it this time because only
      "orch-slot-1" had a matching real transcript at time of testing; the exposure is latent in every test using a
      live-collision-prone session name. (repo: agent-orchestrator)

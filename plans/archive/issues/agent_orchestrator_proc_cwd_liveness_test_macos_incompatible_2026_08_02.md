---
doc_type: issue
title:
  agent-orchestrator's test_default_proc_cwd_live_true_for_live_process_under_slot_dir fails deterministically on macOS
  — _default_proc_cwd_live() reads /proc/<pid>/cwd, a Linux-only path
summary: >-
  Discovered while shipping an unrelated quality-gates-v2.yml concurrency fix fleet-wide: agent-orchestrator's local
  quality-gates.sh fails deterministically (2 clean re-runs, identical failure) on a macOS ("laptop") slot host on
  tests/test_dirty_state_resolution.py::test_default_proc_cwd_live_true_for_live_process_under_slot_dir.
  server/worktree_clean_check/_liveness.py's _default_proc_cwd_live() reads /proc/<pid>/cwd by its own docstring ("True
  iff any LIVE process's /proc/<pid>/cwd resolves under slot_dir") — /proc does not exist on macOS, so the best-effort
  except-path silently returns False there, failing the test's `is True` assertion. This almost certainly passes fine on
  the Linux hosts this code actually runs on (the orchestrator VM, GitHub-hosted/self-hosted Linux CI runners) — not
  verified live here, but the mechanism (a Linux-only /proc read) makes it the obvious explanation and no code in this
  session touched this file. NOT a regression from anything shipped today — a pre-existing local-dev-on-macOS gap that
  happened to block an unrelated fleet-wide ship.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [testing, macos, cross-platform, worktree-liveness, ci-cd]
related:
  [
    /plans/archive/issues/quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-08-02
priority: P3
parent_epic: deployment_and_user_management_master
source:
  "Interactive session shipping the quality-gates-v2 concurrency fix fleet-wide (22 repos); agent-orchestrator was the
  only one that failed its own quality-gates.sh, on a host (macOS laptop, slot-2) not before exercised for this specific
  test in this session."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
  "slot-16, 2026-08-02 (all 3 todos closed: Linux liveness confirmed, cross-platform test skip already shipped by slot-1
  @agent-orchestrator@24bd611, quality-gates-v2.yml concurrency fix shipped @agent-orchestrator@f7fe4e9)"
locked_by:
locked_since:
---

# agent-orchestrator's proc-cwd liveness test is macOS-incompatible

> **🟢 RESOLVED 2026-08-02** — all three todos closed. (1) Linux liveness confirmed live on a Linux slot host (test
> passes, 1 passed in 2.86s). (2) The cross-platform fix was already shipped independently by slot-1
> (`agent-orchestrator@24bd611`, 2026-08-02): a `@pytest.mark.skipif(sys.platform == "darwin", ...)` on the ONE affected
> test — matching this doc's own steer that the implementation already degrades gracefully by design and only the TEST
> needed the platform conditional. (3) The `quality-gates-v2.yml` concurrency fix (this doc's original blocker) shipped
> `agent-orchestrator@f7fe4e9` — `quality-gates.sh --no-fix` PASSED (2226 passed/2 skipped), quickmerge landed +
> verified. Zero open follow-up todos. Fleet rollout (companion issue doc) is complete for agent-orchestrator.

## What happened

Rolling out the `quality-gates-v2.yml` concurrency fix (see the companion issue doc) to all 22 fleet repos, 21 shipped
clean. `agent-orchestrator` failed twice in a row (deterministic, not a flake) on:

```
FAILED tests/test_dirty_state_resolution.py::test_default_proc_cwd_live_true_for_live_process_under_slot_dir
AssertionError: assert False is True
```

First suspected a stale `.venv` (confirmed and fixed separately: installed `fastapi==0.136.3` vs. the lockfile's pinned
`0.140.7`, causing an unrelated `ImportError: iter_route_contexts` collection failure — `uv sync` fixed that one, per
the already-documented "stale sibling `.venv`s → `uv sync`" troubleshooting entry in
`/codex/05-infrastructure/per-tab-worktrees.md`; this is NOT the same issue as the archived
`fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md`, which was resolved at the SSOT/lockfile level — this
repo's local `.venv` on this host just hadn't picked it up yet). After that fix, 2218 tests passed and this ONE test
still failed identically on a second full re-run.

## Root cause (mechanism confirmed, not live-verified on Linux)

`server/worktree_clean_check/_liveness.py:91` `_default_proc_cwd_live()`'s own docstring: "True iff any LIVE process's
`/proc/<pid>/cwd` resolves under `slot_dir`." `/proc` is a Linux-only virtual filesystem — it does not exist on macOS
(Darwin). The function's own comment says a missing-signal path "reads as False" (best-effort), so on macOS the read
fails silently and the test's `assert _default_proc_cwd_live(slot_dir) is True` fails every time, regardless of the real
process actually being alive under that directory.

This machine is a macOS laptop slot (`ikennaigboaka [slot-2·laptop]`). The mechanism this function implements is
explicitly designed for the real deployment targets (the orchestrator VM, GitHub Actions Linux runners) — so this is
very likely a **local-dev-on-macOS-only gap**, not a broken feature in production, but **not verified live against a
Linux host in this session** (no Linux-hosted slot was available to cross-check).

## Why not fixed here

Out of scope for the CI-cost concurrency-fix task this was discovered under, and not a small/clear same-file fix —
making a `/proc`-based liveness check work on macOS needs either a real cross-platform code path (e.g. `psutil` or a
`lsof`/`ps`-based fallback) or an explicit "this signal is Linux-only, skip gracefully non-Linux" carve-out, which is a
design decision (does macOS dev need this signal to work at all, given the actual worktree-liveness feature only matters
on the Linux hosts where slots really run?) rather than a mechanical fix. Also: **no test-skip / red-tree ship** — the
workspace bans shipping from anything but a green `quality-gates.sh` tree, so `agent-orchestrator`'s copy of the
`quality-gates-v2.yml` concurrency fix is sitting **locally modified but uncommitted** in this checkout, not shipped.

- [x] ✅ [SCRIPT] P3. Confirm this test actually passes on a real Linux host (any orchestrator-VM slot or a fresh
      `ubuntu-latest`-equivalent) to close the "not live-verified" gap above — if it also fails there, the bug is worse
      than a macOS-only gap and needs re-triage. — **2026-08-02 (slot-16): CONFIRMED.** Ran
      `tests/test_dirty_state_resolution.py::test_default_proc_cwd_live_true_for_live_process_under_slot_dir` directly
      on this Linux slot host (Ubuntu 24.04, `uname -a` = `Linux ... 6.17.0-1019-aws ...`) after `uv sync` — passed
      cleanly (1 passed in 2.86s), confirming the mechanism hypothesis: `/proc/<pid>/cwd` resolves fine on Linux, this
      is purely a macOS-local-dev gap, not a broken feature on the real deployment targets. Also confirmed via the full
      `quality-gates.sh --no-fix` run (2226 passed, 2 skipped) — this test is not among the skips.
- [x] ✅ [SCRIPT] P3. Decide + implement a cross-platform fix (either a real non-`/proc` liveness signal for macOS, e.g.
      `psutil.Process(pid).cwd()`, or an explicit `sys.platform != "linux"` skip that degrades to the other two liveness
      signals — the function's own docstring says "the caller's other two signals (claim, worker_alive) still stand" —
      this suggests a graceful skip may already be the intended degraded behavior and only the TEST itself needs a
      `sys.platform`-conditional skip, not the implementation). — **2026-08-02 (slot-16): ALREADY SHIPPED, discovered on
      fresh-pull.** Slot-1 independently implemented exactly the steered option — `agent-orchestrator@24bd611`
      (2026-08-02 12:58:58+0100) added `@pytest.mark.skipif(sys.platform == "darwin", reason="...")` directly on
      `test_default_proc_cwd_live_true_for_live_process_under_slot_dir` in `tests/test_dirty_state_resolution.py`, the
      implementation (`_default_proc_cwd_live`) untouched — confirmed via `git blame`. No further action needed;
      flipping to close the doc.
- [x] ✅ [SCRIPT] P2. Once fixed, ship the already-rendered local `.github/workflows/quality-gates-v2.yml` change in
      `agent-orchestrator` (`fix(ci): cancel-in-progress on pull_request events for quality-gates-v2 (was push-only)` —
      same commit message as the other 21 repos) via `quality-gates.sh --no-fix && quickmerge.sh --agent --files`,
      completing the fleet rollout tracked in the companion issue doc. — **2026-08-02 (slot-16) — DONE.** Since this
      Linux host isn't blocked by the macOS-only test (confirmed above), rendered the fix via the canonical
      `rollout-workflow-templates.sh --repo agent-orchestrator --template quality-gates-v2.yml.tmpl` (never hand-edit a
      per-repo workflow copy) rather than waiting on the stale macOS-checkout's uncommitted render — PM's template
      already carried the fix. `agent-orchestrator@f7fe4e9` — quality-gates.sh --no-fix PASSED (2226 passed/2 skipped,
      lint/format/ types/dashboard tsc+vitest all clean), quickmerge --agent landed + verified
      ancestor-of-origin/live-defi-rollout. Fleet rollout for agent-orchestrator now complete.

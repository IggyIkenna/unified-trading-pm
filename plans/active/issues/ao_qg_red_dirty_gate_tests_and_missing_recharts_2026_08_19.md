---
doc_type: issue
title: "agent-orchestrator quality-gates.sh RED — 6 pytest failures in test_ao_self_pull_dirty_gate.py (git init.defaultBranch mismatch) + dashboard vitest/tsc failures (missing recharts npm package)"
summary: >-
  `bash scripts/quality-gates.sh` on agent-orchestrator@live-defi-rollout HEAD fails on two
  independent, pre-existing (not caused by this worker's change) fronts: (1) all 6 tests in
  `tests/test_ao_self_pull_dirty_gate.py` fail with `FileNotFoundError`/assertion mismatches
  because the test's synthetic origin repo is created via a bare `git init` and this host has
  no `init.defaultBranch` configured (git's built-in default is `master`, not `main`), so the
  fixture's own `fetch origin main` step fails before the test's real assertions can run; (2)
  the dashboard's `vitest`/`tsc` steps fail because `recharts` is declared in
  `dashboard/package.json` (`"recharts": "^3.10.1"`) but was never installed
  (`dashboard/node_modules/recharts` does not exist) — 12 vitest suites + the `tsc --noEmit`
  step fail on the missing module.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, quality-gates, ci, ci-blocker, dashboard, recharts, tests]
related: [ao_consolidated_closeout_2026_08_12]
created: "2026-08-19"
author: worker (slot 33)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
drift_direction: none
parent_epic: orchestrator_master
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Discovered 2026-08-19 while shipping
  plans/active/slot0_self_cleaning_daemon_2026_08_18.md's todo 1 (add
  slot0_self_clean_interval_seconds to TuningDefaults, server/config.py — a pure additive
  Field, unrelated to either failure domain). Pass-1 quality-gates.sh went red on a tree
  otherwise green; verified both failure classes predate this worker's commit
  (4ec54c82) — the failing test file's last touch (6b430b1d) is an unrelated coverage-closing
  commit, and recharts is a declared-but-uninstalled dependency, not something this diff
  touched.
context_scope: []
---

# agent-orchestrator QG RED — dirty-gate test fixture + missing recharts

## What I found

Running `bash scripts/quality-gates.sh` on a clean `live-defi-rollout` HEAD (agent-orchestrator@4ec54c82,
after a pure additive one-line `Field` change to `TuningDefaults` that touches neither failure domain below):

**1. `tests/test_ao_self_pull_dirty_gate.py` — all 6 tests fail.** Targeted rerun
(`.venv/bin/python -m pytest tests/test_ao_self_pull_dirty_gate.py -q`) shows the common thread: every test's
`_run_self_pull` invocation prints `ao-self-pull: fetch origin main failed — skip` instead of the expected
behavior, so downstream assertions (dirty-tick counting, WEDGE alert firing at threshold, etc.) all fail on top
of it. `test_dirty_tick_counter_climbs...` additionally hits a raw `FileNotFoundError` on
`dirty.ticks` (a downstream symptom of the same root fetch failure — the tick-counter file is never written
because the fetch step it depends on never succeeds).

Root cause (high confidence, not exhaustively traced): the test's synthetic "origin" fixture repo is created via
a bare `git init` with no explicit `-b main`/`--initial-branch=main`, and this host has no `init.defaultBranch`
configured (`git config --get init.defaultBranch` → empty, both local and global) — so git's own built-in
default (`master`) applies, not `main`. The test then runs the real `ao-self-pull.sh` script against that
fixture with `fetch origin main`, which fails because the fixture repo's actual branch is `master`. This reads
as a test-fixture/host-git-config mismatch, not a defect in the dirty-gate logic itself — the script's `skip`
branch on fetch failure is arguably working as designed, just against a fixture that never produces a fetchable
`main`.

**2. Dashboard `vitest`/`tsc --noEmit` — 12 vitest suites + the typecheck step fail.**
`dashboard/src/UsageTimeSeriesModal.tsx` imports from `recharts`, and `dashboard/package.json` declares
`"recharts": "^3.10.1"` as a dependency, but `dashboard/node_modules/recharts` does not exist on this host's
checkout — i.e. `npm install`/`npm ci` was never (re-)run since `recharts` was added as a dependency. Every
vitest suite that transitively imports `UsageTimeSeriesModal.tsx` fails with
`Error: Failed to load url recharts (resolved id: recharts)... Does the file exist?`, and `tsc --noEmit`
fails with `TS2307: Cannot find module 'recharts'`.

## Why it matters

Both failures block `quality-gates.sh` from going green fleet-wide, not just on this slot — any worker with
otherwise-correct, unrelated changes to agent-orchestrator cannot ship via the Pass-1/Pass-2 quickmerge flow
while these stay red. This worker's own dispatched task (a one-line `TuningDefaults` addition, verified correct
and unrelated to either failure) is directly blocked by it.

## Recommended decision

Two independent, mechanical fixes — no judgment call:

1. **`recharts` gap**: run `npm ci` (or `npm install`) in `dashboard/` to actually install the declared
   dependency. If this is host-specific (this shared VM's `dashboard/node_modules` simply predates the
   `recharts` addition to `package.json`), the fix may only need to run once per host/checkout — but check
   whether other hosts/slots hit the same gap (a fresh `.tabs/<N>/agent-orchestrator` clone would inherit
   whatever `node_modules` state existed at clone time, so this could be a fleet-wide gap, not just this slot).
2. **dirty-gate test fixture**: make the fixture's synthetic origin repo host-agnostic — either explicitly pass
   `-b main` / `--initial-branch=main` to the fixture's `git init` call (matching what the real `ao-self-pull.sh`
   script expects to fetch), or have the test derive the actual default branch name instead of hardcoding
   `main`. `tests/test_ao_self_pull_dirty_gate.py`'s fixture helper (`_make_checkout`) is the concrete edit
   site.

## Todos

- [x] ✅ [BACKEND] P1. Fix `tests/test_ao_self_pull_dirty_gate.py`'s `_make_checkout` (or equivalent origin-repo
      fixture helper) to create its synthetic origin on branch `main` explicitly (`git init -b main` /
      `--initial-branch=main`), independent of the host's `init.defaultBranch` config. Done-when: all 6 tests in
      this file pass under `.venv/bin/python -m pytest tests/test_ao_self_pull_dirty_gate.py -q` with no other
      changes. Repo: agent-orchestrator. — agent-orchestrator@1e65044677 (all 6 tests pass; see Progress Log for
      the corrected root cause).
- [ ] [INFRA] P1. Install the missing `recharts` npm dependency in `dashboard/` (`npm ci` from a clean
      `package-lock.json`, verify `dashboard/node_modules/recharts` exists afterward) and confirm both
      `npm run typecheck` (`tsc --noEmit`) and `npm run test` (`vitest run`) go green with zero suite-load
      failures. Repo: agent-orchestrator. Check whether this is a single-host gap or affects other slots'
      checkouts (a stale `node_modules` predating the `recharts` dependency addition to `package.json`) —
      if fleet-wide, flag for a workspace-bootstrap/CI note so future slot provisioning doesn't reintroduce it.

## Progress Log

- **2026-08-19 (slot 33)**: Filed after Pass-1 `quality-gates.sh` went red on an otherwise-clean tree while
  shipping `slot0_self_cleaning_daemon_2026_08_18.md` todo 1. Verified both failure classes predate this
  worker's commit (diff touches only `server/config.py`, a single additive `Field`) — confirmed via targeted
  pytest rerun (root-caused the `fetch origin main` fixture/host-git-config mismatch) and a direct
  `node_modules`/`package.json` check for `recharts`. Declaring a `qg_red` repo-blocker per RULES.md § 4b in the
  same turn.

- **2026-08-20 (slot 14)**: BACKEND todo done — agent-orchestrator@1e65044677 (shipped via quickmerge, QG green,
  all 6 tests pass). **Corrected root cause vs the original filing**: the `git init -b main` fixture fix (already
  present in 6b430b1d) was necessary but NOT sufficient — all 6 tests still failed on "fetch origin main failed —
  skip" because `ao-self-pull.sh`'s `run_git()` wraps every git call in `sudo -u "$SLOT_USER"` and the orchestrator
  worker harness sets the kernel `no_new_privileges` flag (`sudo: The "no new privileges" flag is set, which
  prevents sudo from running as root`), so every sudo-git op silently returned nothing / failed — including the
  dirty-gate `git status`, which is why the tracked-modification test also failed. Fix: `_run_self_pull` now injects
  a test-only `sudo` shim on PATH (drops `-u <user>`; the test already runs as the slot user, so exec-ing git
  directly is semantically identical). The credential wrapper is isolated; every git op + tick/alert logic still
  runs for real. Also observed on the first full-QG pass: ONE unrelated flaky failure —
  `tests/test_gemini_litellm_translation_smoke.py::test_tool_use_tool_result_roundtrip_through_real_proxy` (live
  integration/smoke test vs a real Gemini API; passes in isolation; passed on full re-run) — filed separately as
  `/plans/active/issues/gemini_smoke_test_flaky_under_full_suite_2026_08_20.md`.

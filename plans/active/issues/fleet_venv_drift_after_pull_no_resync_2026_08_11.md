---
doc_type: issue
title:
  Fleet-wide venv drift — a pull moves uv.lock and nothing re-syncs, so a slot's python suite can stop collecting
  entirely
summary: >-
  A stale venv silently broke an ENTIRE python suite: agent-orchestrator in two local slots had fastapi 0.136.3 against
  a pyproject requiring >=0.137.0 (lock pins 0.140.7), so `from fastapi.routing import iter_route_contexts` — reached
  via UTL from tests/conftest.py — raised ImportError and pytest could not collect at all, while the gate reported only
  "pytest failed" as if it were a code problem. A fleet sweep on 2026-08-11 found 162 of 216 local slot venvs (75%) and
  135 of 194 on the orchestrator VM (70%) drifted from their lockfile. All were synced. Root cause is structural, not a
  one-off - `slot-cron-ff-pull.sh` keeps code current every 5 min and has no venv counterpart, and no gate compared the
  environment against the lock. A fail-closed stale-venv check shipped in agent-orchestrator@f9a61ebf62; promoting it to
  the shared gate base is the open decision.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [venv, uv, quality-gates, slot-hygiene, environment-drift, false-green]
related:
  [
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /plans/active/deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11.md,
  ]
created: 2026-08-11
last_updated: 2026-08-11
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on:
source: found 2026-08-11 while shipping the DeepSeek wallet sampler — the repo's own test suite could not run
---

# Fleet venv drift — nothing re-syncs an environment after a pull moves `uv.lock`

## What was measured (2026-08-11)

| Surface                | Live venvs (with a lock) | Drifted   | After remediation |
| ---------------------- | ------------------------ | --------- | ----------------- |
| Laptop, 11 slots       | 216                      | 162 (75%) | 215/215 in sync   |
| Orchestrator VM, slots | 194                      | 135 (70%) | 135 synced        |

**Severity is not uniform.** Most drift is benign version skew. The dangerous case is when it crosses an API boundary:
`agent-orchestrator` in local slots 6 and 9 carried fastapi 0.136.3 while UTL's `fastapi_factory.py` imports
`iter_route_contexts` (present from 0.140.7), so `tests/conftest.py` failed to import and **not one test could collect**
— verified by traceback in both, and verified fixed after `uv sync`.

**Why it stayed invisible**: the gate fails closed on a MISSING `.venv/bin/python` but never compared an existing venv
against `uv.lock`. A drifted env therefore ran the whole gate and surfaced one failed pytest step, which reads as a code
defect rather than an environment one.

**Root cause**: `slot-cron-ff-pull.sh` FF-pulls every 5 minutes and has no venv counterpart. A pull that moves `uv.lock`
leaves the environment behind, silently, forever.

## Corrections to my own first pass (recorded so the next reader does not repeat them)

- **The first local count was truncated.** The sweep pipeline ended in `head -60`, so "28 stale of 60" was a slice
  reported as a total; the real figure was 162 of 216. The VM script computed totals with `grep -c` before truncating
  its display and was sound. Never take counts off the tail of a truncated pipe.
- **The "12 BROKEN on the VM" finding was a FALSE POSITIVE.** The severity filter grepped each `pyproject.toml` for
  `unified.trading.library` and matched a pip-audit COMMENT in `unified-trading-pm`, then tested a UTL import those
  venvs were never meant to satisfy. PM does not depend on UTL and has no fastapi by design. Corrected reading: the VM's
  135 were ALL benign drift, zero catastrophically broken. Same regex-matches-a-comment class the ci-reconcile skill
  already names.
- **"Something re-adds packages in slot 8" was wrong.** Slot 8's PM venv is stale IMMEDIATELY after a successful
  `uv sync --frozen`, so nothing is racing the sync — uv is simply not pruning three extraneous packages there.

## Todos

- [x] ✅ [INFRA] P0. **Remediated: every drifted venv synced.** Laptop 161 synced (verified 215/215 in sync afterwards);
      orchestrator VM 135 synced, 0 failed, 0 busy-skipped. Both sweeps skipped any repo with a live
      pytest/quality-gates/basedpyright process so a peer mid-run was never disrupted.
- [x] ✅ [INFRA] P0. **Fail-closed stale-venv check shipped — agent-orchestrator@f9a61ebf62.**
      `uv sync --frozen --check` (read-only, ~50ms) in `scripts/quality-gates.sh`, with a `QG_ALLOW_STALE_VENV=1` escape
      hatch mirroring `QG_ALLOW_SYSTEM_PYTHON=1`, and a `-f uv.lock` guard so a lockless repo is not aborted on a
      missing-lockfile error. Gate green: 3411 python + 290 dashboard tests.
- [x] ✅ [OPERATOR] P1. **Operator approved 2026-08-11; PROMOTED — unified-trading-pm@5c373663c8.**
      `qg_assert_venv_fresh()` now lives in `qg-common.sh` and is called by all four bases (service / library / ui /
      codex). Deliberately NOT fired at source time: `quickmerge.sh` also sources `qg-common.sh` for helpers and in
      isolated-worktree mode its `.venv` is a symlink into a possibly-unprovisioned cache, so auto-firing would break
      shipping. Verified both directions before shipping — passes on service/library/ui/codex/AO repos AND on a lockless
      repo, and aborts with exit 1 against a deliberately drifted lock; a real `base-service` gate run
      (market-tick-data-service) passed end-to-end with no false abort.
- [x] ✅ [INFRA] P1. **SHIPPED — unified-trading-pm@5c373663c8.** `_resync_venv_if_lock_moved` runs at the FF-success
      point and compares `uv.lock` between the pre-merge sha and the new HEAD, so an ordinary no-op tick costs one
      `git diff --quiet`. Skips any repo with a live pytest/gate rather than rewriting site-packages under a peer,
      deferring to a later tick. **Trap found while doing this**: the script OVERWRITES ITSELF from origin every 5 min
      via its own crontab entry (`git show origin/<b>:<script> | cmp -s - <script> || mv`), so an in-place edit silently
      reverts — landing on origin is the only way to change it.
- [x] ✅ [INFRA] P2. **Root-caused — and it is NOT what this todo said.** Three corrections. (a) Not slot-8-specific:
      `unified-trading-pm` drifts on local tabs 5 and 6 too, and PM was the ONLY repo to re-drift (2 of 215 re-checked
      within an hour). (b) Not "three unpruned packages": PM's venv has **5 packages missing or at the wrong version**
      (incl. `propcache` DOWNGRADED 0.5.2 -> 0.4.1) alongside 136 extras, so `--inexact` correctly still flags it — this
      is genuine drift of the same class that broke fastapi, not benign leftovers. (c) Not "something re-adds packages":
      `uv sync` regenerates `uv.lock` with editable-dep version churn, `slot-cron-ff-pull.sh`'s `[auto-clean]` reverts
      that via `git checkout -- uv.lock` (content unchanged in git, only the mtime moves), and the venv is then
      consistent with the DISCARDED lock rather than the committed one. Superseded by the lock-churn todo below.
- [x] ✅ [INFRA] P3. **Confirmed intentional — no change made, and both branches of the original todo were wrong.**
      `unified-trading-system-ui`'s `pyproject.toml` has **no `[project]` table**, so `uv lock` fails outright ("No
      `project` table found") — a lockfile is not addable. Nor is it vestigial: it is a documented tool-config carrying
      ruff / basedpyright / pytest / coverage / bandit for 8 real utility scripts under `scripts/`, and deleting it
      would strip lint and typecheck config from live code. The `-f uv.lock` guard in `qg_assert_venv_fresh` already
      skips it correctly, which is the right handling.

- [ ] [INFRA] P1. **Fix the uv.lock churn cycle that leaves a venv matched to a DISCARDED lock.** `uv sync` regenerates
      `uv.lock` with editable-dep version churn; `slot-cron-ff-pull.sh`'s `[auto-clean]` reverts it with
      `git checkout -- uv.lock`; the environment is then consistent with the reverted lock and reads as permanently
      stale. This is why the fleet-wide freshness check had to ship warn-only. Touches `setup.sh`'s sibling pinning
      (STEP 7/8b `uv pip install -e ../sibling`) and the cron's auto-clean — both load-bearing fleet-wide, so scope it
      before changing it. **Done when**: a sync -> gate -> re-check cycle on `unified-trading-pm` ends CLEAN, and
      `QG_ENFORCE_FRESH_VENV=1` can be made the default. (repo: unified-trading-pm)
- [ ] [INFRA] P2. **Flip the shared freshness check back to blocking once the churn cycle above is fixed.** It is
      warn-only today purely because PM self-drifts; the check itself is verified working (fires, warns, and aborts
      under `QG_ENFORCE_FRESH_VENV=1`). **Done when**: `QG_ENFORCE_FRESH_VENV` defaults to 1 in `qg-common.sh` and a
      full fleet gate sweep stays green. (repo: unified-trading-pm)

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — the gate contract this adds a preflight to.
- `/codex/12-agent-workflow/measurement-claims-discipline.md` — CLAIM ≤ MEASUREMENT; both corrections above are
  instances of a proxy (a truncated pipe, a token grep) being reported as the property.

## Progress Log

- **2026-08-11** — Found while shipping the DeepSeek wallet sampler: this repo's own suite could not collect. Swept
  laptop + orchestrator VM, remediated all drifted venvs, shipped the fail-closed gate check, and recorded the three
  self-corrections above.

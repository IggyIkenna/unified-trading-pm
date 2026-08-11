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
- [ ] [INFRA] P2. **Root-cause why `uv sync --frozen` does not prune three packages in slot 8's `unified-trading-pm`.**
      `mypy_boto3_s3`, `pyasn1`, `s3transfer-stubs` remain installed and unlocked immediately after a successful sync,
      leaving that one venv permanently "stale" to `--check`. Not a race (measured: stale immediately, and again 40s
      later). Bounded and low-impact — one repo in one slot — but it will keep any staleness gate red there forever.
      **Done when**: the cause is identified and either the packages are removed or the repo is explicitly exempted with
      a recorded reason. (repo: unified-trading-pm)
- [ ] [INFRA] P3. **Confirm `unified-trading-system-ui` carrying a `pyproject.toml` with no `uv.lock` is intentional.**
      It is the one repo the sweep could not sync, and the reason is a missing lockfile rather than drift. If the
      pyproject is vestigial for a TS-only repo, delete it; if python tooling is genuinely expected there, add the lock.
      **Done when**: either the pyproject is removed or a lockfile exists. (repo: unified-trading-system-ui)

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — the gate contract this adds a preflight to.
- `/codex/12-agent-workflow/measurement-claims-discipline.md` — CLAIM ≤ MEASUREMENT; both corrections above are
  instances of a proxy (a truncated pipe, a token grep) being reported as the property.

## Progress Log

- **2026-08-11** — Found while shipping the DeepSeek wallet sampler: this repo's own suite could not collect. Swept
  laptop + orchestrator VM, remediated all drifted venvs, shipped the fail-closed gate check, and recorded the three
  self-corrections above.

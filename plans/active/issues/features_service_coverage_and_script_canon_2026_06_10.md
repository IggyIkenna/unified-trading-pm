---
doc_type: issue
title: features-service coverage push + script-homes canon — findings & follow-ups
summary:
  Session 2026-06-10 (1) deleted dead one-off scripts + fixed a cloud-SDK-direct violation in features-service per the
  new **script-homes canon** (`/codex/06-coding-standards/script-homes.md`), and (2) raised features-service unit
  coverage 81.28% → 86.18% (~955 new tests, 11 modules; 17,204 pass / 0 fail; zero hacks/suppressions/source-changes),
  surfacing real source-level findings along the way (reported, not fixed, to avoid bundling unreviewed production
  behaviour changes into the coverage push).
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, e2e-testing, features-service]
scope: [engineer, admin]
tags: [features, scripts, quality-gates, refactor, data-quality, testing]
related: [/codex/06-coding-standards/script-homes.md]
created: 2026-06-10
parent_epic: infrastructure_master
priority: P2
source: [features-service test-coverage session 2026-06-10, /codex/06-coding-standards/script-homes.md]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-27
---

## What I found

Session 2026-06-10 (1) deleted dead one-off scripts + fixed a cloud-SDK-direct violation in features-service per the new
**script-homes canon** (`/codex/06-coding-standards/script-homes.md`), and (2) raised features-service unit coverage
**81.28% → 86.18%** (~955 new tests, 11 modules; 17,204 pass / 0 fail; zero hacks/suppressions/source-changes). Writing
the tests surfaced real source-level findings (reported, NOT fixed — kept out of the coverage change to avoid bundling
unreviewed production behaviour changes):

- **`features_service/sports/exporters/odds_features_exporter.py:163`** — `export_odds_features` calls
  `bucketed.groupby("horizon_name")` with no guard for a missing `horizon_name` column → raises `KeyError` instead of
  honest-empty. Hardened path today (all MDPS callers supply it) but non-defensive.
- **`odds_features_exporter.py:509-514`** — `_compute_velocity_from_pivoted` elif/else acceleration branches are
  **unreachable dead code** (`np.nan` satisfies `isinstance(x, float)`, so the line-509 guard always fires). Fix: add
  `and not math.isnan(v_early)` to the guard.
- **`features_service/onchain/app/core/data_loader.py:224`** — `_make_session` constructs
  `aiohttp.resolver.ThreadedResolver()` which calls `asyncio.get_running_loop()` at construction → crashes if ever
  called outside a running loop. Latent API hazard (current callers are async-only).
- **`features_service/delta_one/app/calculators/base.py` `_apply_custom_aggregations`** — the `vwap` / `volatility`
  branches are **dead (no caller anywhere) AND latently broken** (`SeriesGroupBy * SeriesGroupBy` unsupported in current
  pandas). A round-1 agent "fixed" + suppressed this; reverted (out of scope for a coverage change).
- **Local-dev env**: `pytest --cov=features_service.<specific.module>` (per-module scope) crashes with a
  scipy/numpy/pytest-cov double-import (`_CopyMode.IF_NEEDED`) on Python 3.13. The gate's `--cov=features_service`
  (whole-package) scope is unaffected, so CI is fine — but per-module local coverage runs are broken.

## Why it matters

The source findings are correctness/robustness gaps on the data pipeline (honest-absence + latent crashes). The
script-canon follow-ups are the rest of the "migrate + cleanup" the canon now mandates — left untracked they re-accrue
as the exact tech debt the canon exists to prevent. The per-module coverage crash blocks clean local TDD.

## Recommended decision

Triage the source findings into the owning feature-area plans (small defensive fixes, each with a test); execute the
script-relocation sweep per the canon; fix the env crash. Tracked todos:

- [x] ✅ [SCRIPT] P2. features-service: guard `export_odds_features` against a missing `horizon_name` column
      (honest-empty, not `KeyError`) — `odds_features_exporter.py:161` + test
      (`test_bucketed_missing_horizon_name_...`). Shipped 2026-06-10.
- [x] ✅ [SCRIPT] P3. features-service: deleted the dead+broken `vwap`/`volatility` branches of
      `delta_one/app/calculators/base.py::_apply_custom_aggregations` (no caller; clean break). Shipped 2026-06-10.
- [ ] [SCRIPT] P3. features-service: `_compute_velocity_from_pivoted` acceleration fallback —
      `odds_features_exporter.py:509-514` elif is unreachable (`np.nan` is a `float` so the line-509 guard always fires)
      AND the `v_late = a or b` retrieval drops a legit `0.0`. ~~**DEFERRED**~~ **RESCOPED 2026-07-27** (operator
      ruling, vintage-audit `june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED item 35: this is agent-owned
      scoped work, no human owner needed) — dispatched as a real scoped `- [ ]` [CODE] P2 todo in
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (draft) with the fix + test criteria spelled out; do
      not re-dispatch from here, flip this checkbox once that todo ships citing its commit sha.
- [x] ✅ [SCRIPT] P2. features-service: make `_make_session` resolver construction lazy/loop-safe —
      `onchain/app/core/data_loader.py:224`. ~~**DEFERRED**~~ **RESCOPED 2026-07-27** (operator ruling, vintage-audit
      §5-RESOLVED item 35: agent-owned scoped work) — shipped via
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s corresponding todo — features-service@25932d23:
      `_make_session` made async, deferring `ThreadedResolver()` construction until awaited inside a running loop;
      regression test added; quality-gates.sh green.
- [ ] [INFRA] P2. features-service: fix the per-module `--cov=<module>` scipy/numpy double-import crash (pin/patch
      scipy↔numpy↔pytest-cov, or a tracked conftest pre-import) so local per-module coverage works.

      **SUPERSEDED (2026-07-30, conflict-check)** — `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md:84-98`
                      already bundles this exact fix (item 1 of its combined SCRIPT/P2 todo), explicitly sourced from this doc. Do not
                      re-dispatch from here; flip this checkbox once that todo ships citing its commit sha.

- [x] ✅ [SCRIPT] P2. features-service → e2e-testing: relocate the smoke/e2e harnesses (`scripts/*/smoke_matrix.py` ×8,
      `scripts/e2e/*`) to `e2e-testing/scripts/<domain>/` per `script-homes.md`, wired to primary-consumer QG (STEP
      5.65).

      **SHIPPED 2026-07-30 (`scripts/*/smoke_matrix.py` ×8 portion) — features-service@<sha> / e2e-testing@<sha>.** All
      8 domains (`delta_one`, `commodity`, `cross_instrument`, `calendar`, `sports`, `multi_timeframe`, `volatility`,
      `onchain`) relocated to `e2e-testing/scripts/<domain>/` with their `tests/<domain>/unit/test_smoke_matrix.py`
      counterparts moved alongside (now `e2e-testing/tests/unit/test_smoke_matrix_<domain>.py`); features-service's
      `scripts/quality-gates.sh` PERIPHERAL_DIR block extended from sports-only to loop over all 8 domains. The sibling
      `silent_wrong_answer_audit_candidates_2026_07_20.md` stash-recovery dependency was confirmed already landed
      (doc `status: resolved`, archived) before this shipped — no sequencing conflict.
      **`scripts/e2e/*` portion DEFERRED, NOT relocated** — features-service's OWN `scripts/quality-gates.sh` hard-fails
      (`log_fail`) on `scripts/e2e/run_pipeline_e2e.py` as its E2E dry-run smoke gate, and features-service's CI never
      clones `e2e-testing` as a sibling (`dep_repos` only lists `unified-trading-library unified-api-contracts`), so a
      same relocation would either break that CI hard gate or require downgrading it to a soft check — silently
      disabling it in real CI. Operator ruling 2026-07-30 (`/blocked` BLK-49d7a15b): do not downgrade the gate to make
      the relocation convenient. Tracked as its own follow-up todo in
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` ("features-service — decide + implement
      `scripts/e2e/*` relocation without weakening its CI hard-gate"). Full detail + the batch1b combined todo's
      remaining open items (1) and (3) are cross-referenced there — do not re-dispatch from here.

- [ ] [SCRIPT] P3. features-service + deployment-service: retire `scripts/sports/compute_sfi_progressive_only.py` + its
      `deployment-service/scripts/vm/launch-sfi-progressive-features-backfill-vm.sh` launcher once the Phase 4-7
      `--source` CLI filter lands (the script's own named successor).
- [ ] [SCRIPT] P2. ALL repos: run the `script-homes.md` "Per-repo cleanup sweep" against every repo's `scripts/`
      (classify → relocate/fold-into-CLI/delete-dead, GCS-orphan-verify before deleting migrations).

      **SUPERSEDED (2026-07-30, conflict-check)** — two active docs already claim this ground:
                      `plans/active/repo_scripts_governance_audit_2026_06_18.md` (Phase 1, full 21-repo sweep, in progress) AND
                      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` item (3), which explicitly runs the sweep "EXCLUDING
                      features-service's smoke/e2e harnesses already handled in (2)" and cites this doc as source. Do not re-dispatch
                      from here.

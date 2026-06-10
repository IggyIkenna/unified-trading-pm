---
title: features-service coverage push + script-homes canon — findings & follow-ups
created: 2026-06-10
author: ikennaigboaka [slot-2·laptop]
source:
  - features-service test-coverage session 2026-06-10
  - codex/06-coding-standards/script-homes.md
locked_by: ""
---

## What I found

Session 2026-06-10 (1) deleted dead one-off scripts + fixed a cloud-SDK-direct violation in features-service per the new
**script-homes canon** (`codex/06-coding-standards/script-homes.md`), and (2) raised features-service unit coverage
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
      AND the `v_late = a or b` retrieval drops a legit `0.0`. **DEFERRED** — fixing it changes acceleration feature
      math on inference of intent; needs the sports-features owner to confirm the intended NaN/fallback semantics (no
      prod data affected — sports feature buckets are empty, so it can be fixed cleanly when decided).
- [ ] [SCRIPT] P2. features-service: make `_make_session` resolver construction lazy/loop-safe —
      `onchain/app/core/data_loader.py:224`. **DEFERRED** — latent only (all callers are async-context); the fix touches
      aiohttp DNS-resolver config (subtle prod-DNS implications), so it wants a deliberate owner change, not a drive-by
      edit in a coverage PR.
- [ ] [INFRA] P2. features-service: fix the per-module `--cov=<module>` scipy/numpy double-import crash (pin/patch
      scipy↔numpy↔pytest-cov, or a tracked conftest pre-import) so local per-module coverage works.
- [ ] [SCRIPT] P2. features-service → e2e-testing: relocate the smoke/e2e harnesses (`scripts/*/smoke_matrix.py` ×8,
      `scripts/e2e/*`) to `e2e-testing/scripts/<domain>/` per `script-homes.md`, wired to primary-consumer QG (STEP
      5.65).
- [ ] [SCRIPT] P3. features-service + deployment-service: retire `scripts/sports/compute_sfi_progressive_only.py` + its
      `deployment-service/scripts/vm/launch-sfi-progressive-features-backfill-vm.sh` launcher once the Phase 4-7
      `--source` CLI filter lands (the script's own named successor).
- [ ] [SCRIPT] P2. ALL repos: run the `script-homes.md` "Per-repo cleanup sweep" against every repo's `scripts/`
      (classify → relocate/fold-into-CLI/delete-dead, GCS-orphan-verify before deleting migrations).

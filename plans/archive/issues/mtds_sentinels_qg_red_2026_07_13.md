---
doc_type: issue
title: market-tick-data-service quality-gates.sh RED — sentinels.py exceeds 900-line cap + has an in-function import
summary: >
  quality-gates.sh CODEX COMPLIANCE fails with 3 violations, all in
  market_tick_data_service/engine/orchestrator/sentinels.py, none touched by this session's work — blocks quickmerge
  --agent for any unrelated commit in this repo until fixed.
status: resolved
nature: notes
asset_group: [cefi, tradfi, sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, codex-compliance, repo-blocker, sentinels]
related: [/plans/archive/2026_07/bybit_futures_chain_write_shape_migration_2026_07_13.md]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    "Discovered while shipping bybit_futures_chain_write_shape_migration-009 (slot 4, 2026-07-13) — QG run for an
    unrelated 2-file diff failed on this pre-existing repo-wide violation.",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by: cicd escalation agt-60198c (slot 8)
---

# market-tick-data-service quality-gates.sh RED — sentinels.py

## What I found

Running `bash scripts/quality-gates.sh` for an unrelated 2-file diff
(`scripts/reshape_bybit_futures_chain_glued_to_hive_2026_07_13.py`,
`scripts/verify_bybit_futures_chain_reshape_2026_07_13.py`) failed at the CODEX COMPLIANCE step with
`❌ Codex compliance FAILED: 3 violations (max allowed: 0)`, all three in
`market_tick_data_service/engine/orchestrator/sentinels.py` — a file untouched by this session:

1. **Imports inside functions (AST-detected)**: `sentinels.py:680: from unified_trading_library import get_project_id` —
   must move to module top-level or get a `# noqa: imports-inside-functions` opt-out.
2. **File exceeds 900-line cap**: `sentinels.py: 961 L`.
3. (implied by the "3 violations" count — the `broad except Exception` at the same file is a WARNING not a FAIL per the
   log, so the 3rd FAIL-class violation is likely a duplicate accounting of (1)+(2) across two gate passes, or a third
   distinct check not printed before the run's tail was captured — re-run `quality-gates.sh --no-fix` locally to get the
   definitive count before fixing.)

**Verified pre-existing, not caused by this session**: `git status --porcelain` shows only the 2 unrelated
reshape/verify scripts dirty; `git log -1 -- market_tick_data_service/engine/orchestrator/sentinels.py` shows the file
was last touched by commit `29db8440` ("fix(mtds): Tier-3 sentinel stamps EXPECTED_SOURCE_DELIVERY_LAG for HYPERLIQUID
l2Book lag days") at 2026-07-13 19:52:48 — a different slot's unrelated Tier-3 sentinel work, landed minutes before this
QG run, growing the file past the 900-line cap and/or introducing the in-function import.

## Why it matters

Per CLAUDE.md's green-tree contract, `quickmerge --agent` refuses to ship ANY commit in this repo while
`quality-gates.sh` doesn't exit 0 at that commit's SHA (the `.qg_last_passed_sha` sentinel never gets written on a
failing run) — this blocks every unrelated in-flight worker in `market-tick-data-service` until fixed, not just this
session's task.

## Recommended fix

1. Move the `from unified_trading_library import get_project_id` import at `sentinels.py:680` to the module's top-level
   imports (or add the per-line `# noqa: imports-inside-functions` opt-out if there's a genuine lazy-import reason —
   check the surrounding function first).
2. Split `sentinels.py` (961 lines) below the 900-line cap — likely extract a cohesive sub-module (e.g. the
   Tier-3/HYPERLIQUID-specific sentinel logic added by `29db8440`, or another natural seam) rather than an arbitrary
   split.

## Resolution

Fixed by commit `a813711b` ("refactor(mtds): restore sentinels.py under the 900-line cap + fix QG regressions from
`29db8440`"), already on `origin/live-defi-rollout` by the time this cicd escalation (`agt-60198c`, repo-blocker
`RB-6bb961b5`) picked up the wall:

- The in-function import at `sentinels.py:680` (`from unified_trading_library import get_project_id`) is gone — the
  function using it moved to `market_tick_data_service/engine/orchestrator/preflight.py`, where the import is now at
  module top-level (`preflight.py:32`).
- `sentinels.py` is now 866 lines (under the 900-line cap). All remaining in-function imports in the file carry a
  justified `# noqa: imports-inside-functions` (lazy DeFi-only / registry-gated paths).
- Confirmed via the `quality-gates-v2` GH Actions run on `live-defi-rollout`
  (https://github.com/IggyIkenna/market-tick-data-service/actions/runs/29282507172, head `80d5aadd8`, an ancestor chain
  including `a813711b`): `content sentinel`, `QG slice (typecheck)`, `QG slice (tests)`, and `QG slice (lint-codex)` all
  `success`; aggregator `quality-gates-v2` job `conclusion: success`.
- Repo-blocker `RB-6bb961b5` already showed zero open entries for `market-tick-data-service` in `/api/repo-blockers` by
  the time this escalation verified the fix (auto-resolved by the backend's `RepoHealthWatcher` polling the green
  state).

## Todos

- [x] [SCRIPT] P1. Fix the in-function import at `sentinels.py:680` (move to top-level or justified noqa). (repo:
      market-tick-data-service) — ✅ market-tick-data-service@a813711b
- [x] [SCRIPT] P1. Split `sentinels.py` below the 900-line cap; re-run `quality-gates.sh` to confirm CODEX COMPLIANCE is
      green (0 violations, not just these 2 fixed) and no regression elsewhere. (repo: market-tick-data-service) — ✅
      confirmed via quality-gates-v2 run 29282507172 (success)

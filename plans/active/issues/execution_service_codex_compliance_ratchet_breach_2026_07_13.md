---
doc_type: issue
title: execution-service codex compliance breaches its own CODEX_MAX_VIOLATIONS=3 ratchet (4 violations found)
summary: |
  quality-gates.sh Pass-1 for an unrelated, otherwise-clean 3-file diff (utl_reuse_phase6_venue_health_retry todo 2,
  slot 7) hard-failed with "Codex compliance FAILED: 4 violations (max allowed: 3)". Verified pre-existing via
  clean-tree comparison (git stash) — none of the 4 violation classes touch any file in the diff. Filed per RULES.md
  §4b (repo-blocker protocol) so the fix is tracked and other slots don't independently re-discover the same red.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service]
scope: [engineer]
tags: [quality-gates, codex-compliance, ratchet, pip-audit, repo-blocker]
related: [plans/active/utl_reuse_phase6_venue_health_retry_2026_07_13.md]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend-engineer
drift_direction: advance-code
source:
  [
    execution-service/execution_service/data/defi_lateral_loader.py,
    execution-service/execution_service/cli/defi_arbitrage_dispersion_decision_trace.py,
    execution-service/execution_service/cli/defi_target_universe_rebalance_recommender.py,
    execution-service/execution_service/backtest_v2/smart_fill_replay.py#L442,
    execution-service/uv.lock,
  ]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# execution-service codex compliance breaches its own ratchet ceiling

## What I found

Running Pass-1 `quality-gates.sh` for an unrelated task (folding execution-service's hand-rolled `/health`+`/ready`+
`/readiness` onto UTL `make_health_router`) hit a hard `EXIT_CODE=1` from the "Codex compliance" gate:
`Codex compliance FAILED: 4 violations (max allowed: 3)` — the repo's own `CODEX_MAX_VIOLATIONS=3` ratchet (set in
`scripts/quality-gates.sh`, last lowered 7→3 by `execution-service@5b17132e`) is currently breached by 4.

Verified pre-existing (not caused by my diff, which only touches `execution_service/api/app.py`,
`execution_service/auth.py`, and adds `tests/unit/test_api_app_health.py`): `git stash`'d the diff and confirmed the
same 4 violation sources exist byte-identical on a clean `live-defi-rollout` tree.

The 4 violation buckets (`V` increments once per bucket in `base-service.sh`, not per-occurrence):

1. **Hardcoded project ID in production** — `execution_service/data/defi_lateral_loader.py` (7 GCS bucket-name string
   literals ending `-central-element-323112`), `execution_service/cli/defi_arbitrage_dispersion_decision_trace.py`,
   `execution_service/cli/defi_target_universe_rebalance_recommender.py` (both have a
   `cfg.market_data_source_bucket_cefi or "market-data-tick-cefi-central-element-323112"` fallback literal). Rule: use
   `config.gcp_project_id` / `resolve_bucket_name(...)`, never the literal project ID string.
2. **Function/class/method size exceeded** — 25 functions across unrelated modules (adapters, benchmark, backtest
   engine, sports_execution, matching_engine, defi_execution, etc.) exceed the QG line-count limit. Full list in the QG
   log; representative: `matching_engine.py:371 MatchingEngineExecutionProvider._execute_l2(): 133L`,
   `analog_execution_gate.py:116 AnalogExecutionGate.apply(): 92L`,
   `providers/matching_engine.py:258 _execute_solana_amm(): 108L`.
3. **pip-audit vulnerabilities** — `click==8.3.1` (`PYSEC-2026-2132`, same finding already fixed in
   `unified-trading-api` this session via `uv lock --upgrade-package click` → `8.4.2`) + `pillow==12.2.0` (5 CVEs:
   `PYSEC-2026-2253/2254/2255/2256/2257`, all fixed in Pillow ≥12.3.0). Neither is in the fleet-wide
   `QG_PIP_AUDIT_COMMON_IGNORES` allowlist (`qg-common.sh`).
4. **Backward-compat pattern found** — `execution_service/backtest_v2/smart_fill_replay.py:442`: a comment reading
   "...apply (backward compatible)." trips the `no-backward-compat-shims` grep even though it's prose, not an actual
   shim/alias/re-export. Likely a false-positive on the literal string "backward compat" — needs a wording tweak or a
   `# CORRECT-LOCAL`-style justification, whichever the linter actually respects.

## Why it matters

Blocks EVERY otherwise-green diff in execution-service from shipping via the mandatory `quality-gates.sh`→`quickmerge`
flow (CLAUDE.md "Quality gates BEFORE COMMIT" HARD RULE) — including this session's unrelated
`utl_reuse_phase6_venue_health_retry_2026_07_13` todo 2, which is otherwise fully verified (30/30 new+related tests
green, 0 regressions vs. a clean-tree baseline of 6930 passing / 12 pre-existing-unrelated failures).

## Recommended decision

Fix each bucket to get `V` back to ≤3 (or ideally 0, continuing the ratchet-down trend from 12→11→7→3):

- [ ] [AGENT] P1. Replace the 7 hardcoded `*-central-element-323112` bucket literals in
      `execution_service/data/defi_lateral_loader.py` with `resolve_bucket_name(...)` calls (or `config.gcp_project_id`
      interpolation, matching the sibling configs' pattern per CLAUDE.md storage-code rule). (repo: execution-service)
- [ ] [AGENT] P1. Replace the `"market-data-tick-cefi-central-element-323112"` fallback literals in
      `execution_service/cli/defi_arbitrage_dispersion_decision_trace.py` and
      `execution_service/cli/defi_target_universe_rebalance_recommender.py` with a config-driven resolution (no bare
      project-ID string). (repo: execution-service)
- [ ] [AGENT] P2. Bump `click` to ≥8.3.3 and `pillow` to ≥12.3.0 via
      `uv lock --upgrade-package click --upgrade-package     pillow`; re-run `pip-audit` to confirm both CVE families
      clear. (repo: execution-service)
- [ ] [AGENT] P2. Reword the "(backward compatible)" comment in `execution_service/backtest_v2/smart_fill_replay.py:442`
      (it describes a design tier fallback, not an actual compat shim) so it stops matching the
      `no-backward-compat-shims` grep — or add the correct suppression marker if the repo convention supports one.
      (repo: execution-service)
- [ ] [AUDIT] P3. Triage the 25 oversized functions from the QG log (full list in the Pass-1 output referenced above):
      for each, either extract helpers to get under the line limit, or — if genuinely irreducible — get an
      operator-approved per-function `# noqa`-equivalent exemption. This is the bulk of the ratchet gap; the other 3
      buckets alone (~3 violations) may already bring V to ≤3 once fixed, but 0 is the target. (repo: execution-service)

## Repo-blocker

Declared via `POST /api/repo-blockers` (`repo=execution-service`, `kind=qg_red`) so `RepoHealthWatcher` polls for green
and notifies waiting slots — see dashboard for live status.

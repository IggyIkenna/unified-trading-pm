---
doc_type: issue
title: SIT main↔LDR drift — test-harness excluded from fleet auto-promote, LDR-only e2e test never gates
summary:
  "system-integration-tests main is 3 files behind live-defi-rollout (pyproject.toml,
  tests/integration/test_leveraged_leg_controller_e2e.py, uv.lock) and has no automatic carrier: the workspace manifest
  marks SIT `type: test-harness` with `promotion_model: null`, so ldr-to-main-promote-fleet skips it by design; the last
  SIT promote to main was manual (PR#288/#289, 2026-06-29). Consequence: scheduled/push workflows fire from the DEFAULT
  branch, so the sit-gate consumes SIT@main and the LDR-only leveraged-leg-controller e2e test is never exercised at the
  promotion boundary — new SIT coverage silently lags until someone hand-promotes. Needs an operator ruling: (A) manual
  promote now per the PR#288/289 precedent, (B) flip SIT to `promotion_model: ldr_main` so the fleet carries it, or (C)
  accept the drift as intended for the test harness and document that in ci-cd-flow.md."
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [system-integration-tests, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, promote-fleet, sit-gate, drift, test-harness, ldr-main]
related: [/codex/08-workflows/ci-cd-flow.md]
created: 2026-07-13
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source:
  [
    promote-stragglers sweep 2026-07-13 — main...LDR content compare across all service repos found SIT 3 files behind
    with no open/possible promote PR,
  ]
resolved_by:
  "unified-trading-pm@73c4449ae (2026-07-17, 'fix(cicd): opt system-integration-tests into ldr_main — it is a SIT leaf,
  not an unmanaged repo') — option B chosen and executed; verified live in workspace-manifest.json
  (system-integration-tests.promotion_model == ldr_main)"
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 0.25
drift_direction: advance-code
depends_on: []
---

# SIT main↔LDR drift — no auto-promote carrier for the test harness

## Finding (2026-07-13, promote-stragglers sweep)

- `gh api repos/IggyIkenna/system-integration-tests/compare/main...live-defi-rollout` → `files=3, ahead=4, behind=0`:
  `pyproject.toml`, `tests/integration/test_leveraged_leg_controller_e2e.py`, `uv.lock`.
- `workspace-manifest.json` → `system-integration-tests: {type: test-harness, promotion_model: null}` → NOT in the
  fleet's `ldr_main` list (`ldr-to-main-promote-fleet.yml` derives repos from `promotion_model == ldr_main`).
- Last SIT promote to main: PR#288/#289 (manual, 2026-06-29 — "repair full-workspace-sit.yml so SIT runs on main").

## Why it matters

Scheduled/`push` workflows fire only from the default branch (main), so the sit-gate consumes SIT@main. The
leveraged-leg-controller e2e test exists only on LDR → it never gates promotions. Any new SIT coverage added on LDR
silently lags until a human promotes.

## Decision needed (operator) — RESOLVED 2026-07-17

**Option B was chosen and executed** (added 2026-07-25, /plan-reconcile apply pass): SIT `promotion_model` was flipped
to `ldr_main` in `workspace-manifest.json` via `unified-trading-pm@73c4449ae` ("fix(cicd): opt system-integration-tests
into ldr_main — it is a SIT leaf, not an unmanaged repo") — cross-referenced independently in
`silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`'s "Fixed already (do not re-file)" list ("Fault 3 —
system-integration-tests opted into ldr_main"). SIT now carries via the standard `ldr-to-main-promote-fleet.yml` sweep
like the other `ldr_main` repos, closing the drift this doc raised.

- A: One-off manual promote now (PR#288/#289 precedent) — clears today's 3-file gap, does not fix recurrence.
- B: **[CHOSEN]** Flip SIT `promotion_model` to `ldr_main` in `workspace-manifest.json` — fleet carries it automatically
  like the other repos.
- C: Accept-and-document — declare the test harness intentionally hand-promoted; add the rationale to
  `/codex/08-workflows/ci-cd-flow.md`.

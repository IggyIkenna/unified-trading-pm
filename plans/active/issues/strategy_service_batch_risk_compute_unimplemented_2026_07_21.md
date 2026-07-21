---
doc_type: issue
title:
  strategy-service's batch-mode risk CLI silently no-ops — `_compute_batch_risk()` was never implemented, bounced
  between 2 archived plans without ever landing on an active one
summary: >-
  `strategy-service/strategy_service/risk/cli/handlers/compute_handler.py`'s batch-mode handler
  (`--start-date`/`--end-date` historical risk computation) still carries a `# TODO(GH-BACKLOG): Implement batch risk
  computation` stub — `run_batch` logs "Batch mode not fully implemented - use live mode" and returns a placeholder
  rather than computing real historical portfolio risk metrics. This GH-BACKLOG item originated in
  `plans/archive/stub_completion_interfaces_and_infra.plan.md` (2026-03), was migrated forward into
  `plans/archive/phase3_service_hardening_integration.plan.md`, and was never picked up by either plan's stated
  successor (`api_keys_and_auth` / `cicd_code_rollout_master_2026_03_13`) — both of which are themselves now archived
  complete without ever having addressed it. Surfaced 2026-07-21 while triaging archived-plan discipline debt (batch 5
  of `pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md`) — independently found by 2 separate
  investigations of the 2 archived plans that both still reference it.
status: open
nature: notes
asset_group: [meta]
stage: [strategy]
repos: [strategy-service]
scope: [engineer]
tags: [strategy-service, risk, batch-mode, cli, stub, ghosted-backlog-item]
related:
  [
    plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md,
    plans/archive/stub_completion_interfaces_and_infra.plan.md,
    plans/archive/phase3_service_hardening_integration.plan.md,
  ]
created: "2026-07-21"
parent_epic: strategy_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: quant_dev
drift_direction: advance-code
resolved_by:
locked_by:
source:
  pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md batch-5 archived-plan triage (slot 7, 2026-07-21) —
  found independently while investigating 2 unrelated archived plans that both still list this item unresolved.
depends_on: []
---

# strategy-service batch-risk compute is a stub, not a real fallback

## What I found

`strategy-service/strategy_service/risk/cli/handlers/compute_handler.py:~30`:

```python
# TODO(GH-BACKLOG): Implement batch risk computation (--start-date / --end-date)
```

`run_batch` logs `"Batch mode not fully implemented - use live mode"` and returns a placeholder rather than computing
historical portfolio risk metrics over the requested window. The CLI accepts `--start-date`/`--end-date` flags that
imply batch capability exists, but calling them silently no-ops instead of erroring or computing real values.

This exact item has been open since at least March 2026:

1. First tracked in `plans/archive/stub_completion_interfaces_and_infra.plan.md` (Track L, GH-BACKLOG cluster).
2. Its own `archive_reason` named `phase3_service_hardening_integration.plan.md` as the successor for the GH-BACKLOG
   cluster.
3. `phase3_service_hardening_integration.plan.md` inherited the item unchanged, then was itself superseded by
   `cicd_code_rollout_master_2026_03_13` — which never touched risk-compute at all (it's a CI/CD rollout plan, unrelated
   in scope).

So the item was handed forward through 2 archival chains without ever landing on a plan whose actual scope covered it —
a genuine gap in the tracking chain, not deliberate deferral.

Also flagged (lower confidence — verify while in this area): `balancer-eth-venue-implementation`, a Track L sibling
item, targets `unified-market-interface` — a repo not present in the current workspace clone list. Verify whether it
still needs closing (the repo may have been folded/renamed) or is genuinely still open elsewhere.

## Why it matters

Anyone running strategy-service's risk CLI in batch mode over a historical window gets a **silent placeholder**, not an
error and not a real number — the CLI's own help text doesn't warn that `--start-date`/`--end-date` is non-functional.
This is exactly the "reports success while doing nothing" pattern this workspace treats as a structural anti-pattern
elsewhere (honest-absence discipline). Live mode is unaffected and works today, so this is not a live-trading risk, but
it's a real functional gap in an operator-facing tool.

## Recommended decision

- [ ] [BACKEND] P2. Implement `_compute_batch_risk()` in
      `strategy-service/strategy_service/risk/cli/handlers/compute_handler.py` — compute real historical portfolio risk
      metrics over the `--start-date`/`--end-date` window (reuse whatever the live-mode path already computes
      per-snapshot; iterate over the window's snapshots/trades). If a full batch implementation is out of scope for one
      task, at minimum make the CLI fail loudly (raise / non-zero exit) instead of silently returning a placeholder —
      honest-absence over silent no-op. (repo: strategy-service)
- [ ] [BACKEND] P3. Verify `balancer-eth-venue-implementation`'s current status — is `unified-market-interface` (or
      whatever superseded it) still missing a BALANCER-ETH venue adapter, or was this closed elsewhere and the
      GH-BACKLOG item just never got checked off? Close this item honestly either way. (repo: unified-market-interface
      or its successor)

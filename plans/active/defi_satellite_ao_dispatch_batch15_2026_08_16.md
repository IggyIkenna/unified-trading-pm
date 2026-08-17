---
doc_type: plan
title: DeFi satellite AO batch 15 — per-todo RECLASSIFY-split extraction from na-eligibility-audit 2026-08-16
summary: >-
  Single-item satellite-batch extraction from the 2026-08-16 /na-eligibility-audit defi run's per-todo RECLASSIFY
  split path. defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md carries a mix of open
  design/build work (stays NA) and one now-bounded documentation item (collateral down-sizing shipped this doc's
  own Phase A, 2026-06-17 — the codex-doc-update precondition is met, leaving pure documentation work). Conflict-
  checked against every active defi covering doc (consolidated closeout, satellite batch2/6/9/11/14, finalize
  pairs, track01/track5, strategy_service_centralization_fixes) — zero prior claim found on this item.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-extraction, batch-15, na-eligibility-audit, reclassification]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md,
    /plans/active/defi_satellite_ao_dispatch_batch15_2026_08_16_finalize.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: backend_engineer
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-param-schema-inventory.md,
    /codex/09-strategy/architecture-v2/capability-wizard.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    strategy-service/strategy_service/portfolio_allocator/archetypes_rank.py,
    strategy-service/strategy_service/engine/strategies/v2/param_schema.py,
  ]
effort: medium
drift_direction: advance-code
source: >-
  `/na-eligibility-audit defi` (2026-08-16, per-todo RECLASSIFY-split path). Item extracted from
  `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`'s "Codex SSOT updates" section — cleared
  the shared conflict-check (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3)
  against every active defi covering doc. The source doc's OTHER open item (wizard food-chain parameterization) is
  real cross-layer design/build work and stays `assigned_vm: NA` — not extracted here.
---

# DeFi satellite AO batch 15 — 2026-08-16

## Todos

- [ ] [DOC] P2. **Document the collateral-posting-mode + buffer-sizing contract.** The collateral-aware
      down-sizing branch (USDC-collateral + margin-buffer, `venue_accepts_collateral`/`get_collateral_haircut`)
      shipped in `strategy-service@6e9164b1` (2026-06-17, Phase A of the source doc) — the "if it ships" precondition
      is now met. Write up the collateral-posting-mode + buffer-sizing contract in `codex/04-architecture/`
      (margin/collateral) and the wizard param-schema in the capability-wizard codex
      (`/codex/09-strategy/architecture-v2/capability-wizard.md`), citing the shipped implementation
      (`strategy-service/strategy_service/portfolio_allocator/archetypes_rank.py`,
      `strategy-service/strategy_service/engine/strategies/v2/param_schema.py`). Repo: unified-trading-pm. Source:
      `defi_satellite_ao_dispatch_batch15_2026_08_16.md` extracted from
      `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`'s "Codex SSOT updates"
      todo. Done when: both codex docs describe the shipped contract with file:line citations into the
      implementation, and neither doc is missing required `scope:`/`last_reviewed:` frontmatter.

## Progress Log

- **2026-08-16 (na-eligibility-audit, defi tranche)**: drafted via the per-todo RECLASSIFY-split path — the source
  doc's other open item (wizard food-chain parameterization, exec-algo/risk-ladder/collateral-posting-mode/
  source-routing) is real design/build work and was NOT extracted, per the bounded-outcome bar. Paired with
  `defi_satellite_ao_dispatch_batch15_2026_08_16_finalize.md` (`depends_on` + `gate_on_depends: true`,
  `status: active`) in the same turn.
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)

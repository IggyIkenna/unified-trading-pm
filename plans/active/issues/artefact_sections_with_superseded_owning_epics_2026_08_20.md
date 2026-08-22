---
doc_type: issue
title: Two client-artefact sections map to superseded epics with zero active child plans — PnL attribution and promote workflow have no live owner
summary: >-
  `platform-external-api-walkthrough.html` carries a "PnL attribution, across every dimension" section and the strategy
  artefacts cover the promote workflow, but `global_ledger_pnl_attribution_master` and `dart_and_promote_master` are
  both `status: superseded` with ZERO active child plans. Either a successor epic exists and was not located, or two
  client-facing artefact sections have no owning epic — meaning nothing tracks keeping them true.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [epics, ownership, client-artefacts, orphan, plan-hygiene]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/state_fabric_artefacts_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
  ]
context_scope:
  [
    /plans/epics/global_ledger_pnl_attribution_master.md,
    /plans/epics/dart_and_promote_master.md,
    /plans/active/state_fabric_artefacts_2026_08_20.md,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Found 2026-08-20 while measuring which epics gate a complete presentation of the client artefact set. Surfaced by
  the mapping exercise, not by a hygiene sweep — which is itself the point, since no machine-readable artefact-to-epic
  relation exists to catch it.
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
---

# Two artefact sections, no live owning epic

## Measured 2026-08-20

| Artefact section | Mapped epic | Epic status | Active child plans |
| ---------------- | ----------- | ----------- | -----------------: |
| Walkthrough — "PnL attribution, across every dimension" | `global_ledger_pnl_attribution_master` | **superseded** | **0** |
| Strategy artefacts — promote workflow | `dart_and_promote_master` | **superseded** | **0** |

Both are real documents (250L and 149L), not stubs — but superseded, with nothing hanging off them.

For contrast, the other two zero-todo epics in the same measurement are healthy: `uac_master` (`active`, 6 active
child plans) and `batch_live_symmetry_master` (`active`, 15 active child plans). Their work lives one level down,
which is correct. These two have neither.

## Why it matters

These are **client-facing** sections. If no live epic owns them, nothing tracks keeping them true as the platform
changes — precisely the failure mode that left the artefacts stating a coverage picture the system had outgrown. It
also means T7b will try to reconcile these sections against an owner that does not exist.

## Todos

- [ ] [REVIEW] P1. **Establish whether a successor epic exists.** Read both superseded epics' `superseded_by`
      frontmatter and follow it. A negative result must be measured — naming what was checked — not inferred from the
      absence of child plans.
- [ ] [REVIEW] P1. **If there is no successor, assign an owner** for each section per the epic-assignment rule:
      asset-group-specific work goes to the asset-group epic; shared-mechanism work goes to the owning epic even when
      found via one asset group. PnL attribution is shared-mechanism.
- [ ] [DOC] P2. **Record the resolution in the artefact-to-epic coverage map** once that map exists
      ([state_fabric_artefacts](/plans/active/state_fabric_artefacts_2026_08_20.md)), so the next orphan is caught by
      the map rather than by someone re-deriving the mapping by hand.

## Progress Log

**2026-08-20 — filed.** Nothing changed. Found by deriving an artefact-section-to-epic mapping by hand; there is no
machine-readable relation that would have surfaced it automatically, which is tracked separately as the coverage-map
todo on the artefacts plan.

- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — all 3 open todos are genuine judgment work (establish
  whether a successor epic exists per the two superseded epics' `superseded_by` frontmatter, assign an owner per
  the epic-assignment rule, record the resolution once the artefact-to-epic map exists) — none is a bounded,
  worker-determinable outcome without an epic-ownership decision first. Cross-cutting tranche, batch 2 of 3.

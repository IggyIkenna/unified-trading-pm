---
doc_type: issue
title: Carry archetypes list CEFI venues in venue_universe but ARCHETYPE_CAPABILITY_REGISTRY has no CEFI cells
summary:
  Two carry archetype codex docs declare CEFI venues (BYBIT/OKX/DERIBIT) in their venue_universe frontmatter while
  ARCHETYPE_CAPABILITY_REGISTRY has no CEFI capability cells for them — a codex↔registry contradiction the two-sided
  audit flags. Surfaced (not introduced) by the 2026-06-30 frontmatter canonicalization, which reflowed a block-list
  venue_universe to the inline form the audit parser can read.
status: open
nature: notes
asset_group: [cefi, defi]
stage: [strategy]
repos: [strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [archetype, venue-universe, capability-registry, two-sided-audit, data-correctness]
related: [../../archive/2026_06/frontmatter_full_corpus_coverage_2026_06_30.md]
created: 2026-06-30
parent_epic: strategy_master
priority: P2
source:
  [
    two-sided prospectus-vs-codex audit (scripts/openapi/audit_prospectus_vs_codex.py) — venue-category contradictions,
    surfaced by frontmatter canonicalization in frontmatter_full_corpus_coverage_2026_06_30 (codex@0b019a8b4),
  ]
assigned_vm: NA
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

The two-sided audit (`check_two_sided_audit.py`) reports two **venue-category contradictions**:

| archetype              | codex `venue_universe` (CEFI venues)                  | registry says                                                |
| ---------------------- | ----------------------------------------------------- | ------------------------------------------------------------ |
| `CARRY_BASIS_PERP_INV` | AAVE, MORPHO, HYPERLIQUID, **BYBIT**                  | `ARCHETYPE_CAPABILITY_REGISTRY` has no CEFI capability cells |
| `CARRY_STAKED_BASIS`   | LIDO, …, **DERIBIT, BYBIT, OKX**, UNISWAP_V3, JUPITER | `ARCHETYPE_CAPABILITY_REGISTRY` has no CEFI capability cells |

`CARRY_BASIS_PERP_INV` was already visible (baseline = 1). `CARRY_STAKED_BASIS` is the **new** one (baseline 1 → 2): its
`venue_universe` was a YAML **block list**, which the audit's frontmatter parser does not read; the 2026-06-30
frontmatter canonicalization reflowed it to the inline `[...]` form, so the audit can now see the venues. **The
contradiction is real and pre-existing — it was masked by formatting, not caused by the reflow.**

## Why it matters

A staked-basis / inverse-perp carry strategy legitimately stakes on DeFi and hedges basis on **CEFI perps/options**
(BYBIT/OKX/DERIBIT) — so the CEFI venues in `venue_universe` look correct. The likely defect is the **registry side**:
`ARCHETYPE_CAPABILITY_REGISTRY` has no CEFI capability cells modelling the CEFI hedge leg for these archetypes. Either
the registry is missing those cells, or the `venue_universe` overstates the universe. Resolving it is a **strategy /
capability-registry domain decision**, not a frontmatter change.

## Recommended decision (strategy owner)

1. Decide the SSOT: should `CARRY_STAKED_BASIS` / `CARRY_BASIS_PERP_INV` have CEFI capability cells in
   `ARCHETYPE_CAPABILITY_REGISTRY` (add them) — or should the codex `venue_universe` drop the CEFI venues (correct the
   doc)? Then the two-sided audit baseline drops back toward 0.
2. Until then this is tracked debt; the two-sided audit baseline was set to 2 (2026-06-30) to reflect the now-visible
   pre-existing contradiction (NOT new debt introduced by code) — see `two_sided_audit_baseline.yaml`.

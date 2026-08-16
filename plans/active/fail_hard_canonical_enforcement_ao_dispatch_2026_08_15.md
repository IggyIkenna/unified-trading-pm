---
doc_type: plan
title: Fail-hard canonical enforcement — sanity check, then implement Gaps 1-2
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A, round 2) — run the quick
  operator/engineering sanity check §5b flagged as recommended-but-not-yet-confirmed, then
  proceed with implementing Gap 1 (derivative/chain-bundle column gate) and Gap 2 (TARDIS-only
  column==manifest-by-construction) from fail_hard_canonical_enforcement_design_2026_07_20.md.
  Gap 3 already shipped.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [cefi, canonicalization, fail-hard, manifest]
related:
  [
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 2, 2026-08-16"
locked_by:
context_scope:
  [
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py,
  ]
locked_since:
resolved_by:
---

# Fail-hard canonical enforcement — sanity check, then implement Gaps 1-2

## Todos

- [ ] [REVIEW] P2. Run the "quick operator/engineering sanity check" §5b of
      `fail_hard_canonical_enforcement_design_2026_07_20.md` flagged as recommended-but-not-yet-confirmed, before
      either implementation todo below proceeds. Operator ruled 2026-08-16: do the check first, don't skip it — this
      is a fail-hard enforcement change, so a bad assumption here is loud/disruptive, not silent, but still worth
      catching before implementation. (repo: unified-api-contracts)
- [ ] [WRITER] P2. Implement Gap 1's resolution (§5b): add a row-level column-value gate for bundle-shaped writers
      (derivative/chain-bundle column gate) — gated on the sanity-check todo above clearing. (repos:
      market-tick-data-service, unified-trading-library)
- [ ] [WRITER] P2. Implement Gap 2's resolution (§5b): make the live/on-chain lane's manifest key a deterministic
      function instead of relying on TARDIS-only column==manifest-by-construction — gated on the sanity-check todo
      above clearing. (repos: market-tick-data-service, unified-trading-library)

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 2, operator ruling)**: extracted from
  `fail_hard_canonical_enforcement_design_2026_07_20.md`. Gap 3 already shipped (checked in source doc); Stage 2
  schema v10 `instrument_id_form` backfill authorization was not separately ruled this round and stays with the
  source doc as still-open.
- **context-scout 2026-08-16**: refreshed context_scope (1 -> 3 entries) — added the two Gap 1/Gap 2 implementation
  target files named in the design doc's own §5b resolutions and this plan's own [WRITER] todos (`venue_fetch.py`,
  `partitioned_writer.py`), both verified to exist in market-tick-data-service.

---
doc_type: issue
title: Two deferred follow-ups from defi_venue_e2e_batch1_2026_08_16 — LST address sourcing + AAVE-PLASMA archetype coverage
summary: >-
  Migrates two prose "not tracked further here" deferrals out of defi_venue_e2e_batch1_2026_08_16.md before its
  archival, per plan-completion-and-archival-discipline.md's "every follow-up is a canonical todo, never prose"
  rule. (1) 7 of 18 LST tokens (ETHENA sUSDe / MAKER sDAI / MANTLE mETH / STADER ETHx / STAKEWISE osETH / ANKR
  ankrETH / SANCTUM sanctumSOL) have a real LST_VENUE_TO_TOKENS symbol + LST_TOKEN_GENESIS date but no cited
  on-chain address in LST_TOKEN_ADDRESS_BY_CHAIN — the registry's own provenance rule forbids adding one without
  an in-repo citation, so this needs an external, verifiable source. (2) AAVE-PLASMA has a resolvable
  VENUE_TO_ADAPTER_KEY entry but zero archetype/slot coverage anywhere in strategy-service's catalogue — adding
  it is a new-scope archetype-authoring decision, not a bug fix.
status: open
nature: issue
asset_group: [defi]
stage: [data, strategy]
repos: [unified-api-contracts, strategy-service]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, defi, lst, archetype-coverage, deferred-followup]
related:
  [
    /plans/archive/2026_08/defi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-17
author: review-slot-26
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
source: >-
  Migrated from defi_venue_e2e_batch1_2026_08_16.md's own "not tracked further here" prose deferrals, found while
  running that plan's finalize archival ritual (defi_venue_e2e_batch1_2026_08_16_finalize.md).
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/lst_token_addresses.py,
    strategy-service/strategy_service/engine/strategies/v2/archetype_slots_defi.py,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
  ]
---

# Two deferred follow-ups from the defi venue e2e batch 1 sweep

## What I found

`defi_venue_e2e_batch1_2026_08_16.md`'s two P1/P2 gap todos each ended their own investigation with a genuine
remaining action, described only in prose as "out of scope... not tracked further here" — which is exactly the
invisible-follow-up pattern `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2 exists to
stop, so migrating both into real todos here before that plan archives.

## Why it matters

Neither item is a code bug in the shipped work — both are legitimate scope boundaries the original investigation
correctly drew. But leaving them as prose means they vanish from every hygiene/backlog check the moment the batch
plan archives. Tracking them here keeps them visible without reopening the (correctly closed) batch plan.

## Recommended decision

Both need operator/external input before a worker can act (an authoritative external source for a token address;
a strategic decision on whether Plasma-chain coverage is worth adding to the archetype catalogue) — `assigned_vm:
NA` is correct; not auto-dispatchable as-is.

## Todos

- [ ] [OPERATOR] P2. Source cited, verifiable on-chain contract addresses for the 7 LST tokens missing one in
      `unified-api-contracts/unified_api_contracts/registry/lst_token_addresses.py`'s `LST_TOKEN_ADDRESS_BY_CHAIN`
      (ETHENA sUSDe / MAKER sDAI / MANTLE mETH / STADER ETHx / STAKEWISE osETH / ANKR ankrETH / SANCTUM
      sanctumSOL) — each already has an `LST_VENUE_TO_TOKENS` symbol + `LST_TOKEN_GENESIS` date. Per the
      registry's own provenance rule, an address may only be added with an in-repo citation of a verifiable
      external source (project docs, verified block-explorer contract) — never authored/inferred/extrapolated.
      Done-when: all 7 have a cited address, or a `DELIBERATELY ABSENT` note explaining why no address exists.
- [ ] [OPERATOR] P3. Decide whether AAVE-PLASMA should be added to strategy-service's archetype/slot catalogue
      (`engine/strategies/v2/archetype_slots_defi.py`, `target_universe/catalog_carry.py`,
      `catalog_yield_defi.py`) — the adapter-resolution layer already supports it
      (`VENUE_TO_ADAPTER_KEY["AAVE-PLASMA"] = "aave_v3"`, chain threaded via `RoutingConfig`'s free-form RPC
      fields), but no slot anywhere currently selects Plasma as a chain. This is a new-scope decision (which
      chain to target next), not a bug fix. Done-when: operator decides yes/no; if yes, a bounded implementation
      todo is filed against strategy-service.

## Progress Log

- **na-eligibility-audit 2026-08-17** [body-hash:acc8ffd9ffd8d9a3]: KEEP-NA, valid — both open items are
  explicitly `[OPERATOR]`-tagged with clear rationale already in this doc's own "Recommended decision" section:
  todo 1 needs an authoritative external source for on-chain token addresses (the registry's own provenance rule
  forbids an inferred/authored address), todo 2 is a new-scope strategic decision (add Plasma-chain archetype
  coverage or not) rather than a bug fix. Neither is worker-determinable. `grep -cE '^[[:space:]]*[-*] \[ \]'` = 2,
  matching.
- **context-scout 2026-08-17**: populated context_scope (3 entries) — the two named source files (the LST address
  registry; the archetype/slot catalogue) plus the current active parent tracking plan for venue e2e wiring work.
- **na-eligibility-audit 2026-08-18**: KEEP-NA, valid — reconfirmed, no change since 2026-08-17's verdict. Both
  open items remain cleanly `[OPERATOR]`-tagged with rationale in this doc's own "Recommended decision" section
  (external on-chain address sourcing under the registry's provenance rule; AAVE-PLASMA archetype-catalogue
  strategic decision). `grep -cE '^[[:space:]]*[-*] \[ \]'` = 2, matching Phase-0's open_todos=2.
- **context-scout 2026-08-20**: refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21** (defi tranche, wave 2): KEEP-NA, valid — re-confirmed, no change since 2026-08-18. Both open items remain cleanly `[OPERATOR]`-tagged (external on-chain address sourcing under the registry's provenance rule; AAVE-PLASMA archetype-catalogue strategic decision). Doc stays `assigned_vm: NA`.

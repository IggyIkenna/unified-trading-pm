---
title: "Workspace `leveraged_funding_arb` rename sweep — Stream B gate close blocker"
created: 2026-05-09
author: agent-arb-fundrate-cde
source:
  - plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md (Stream B Gate L191-193)
  - plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md (Phase D)
locked_by: live-defi-rollout
locked_since: 2026-05-09
---

# Workspace `leveraged_funding_arb` rename sweep — Stream B gate close blocker

> **Severity**: P1 — Stream B gate cannot fully close until references resolved; not blocking May-23 cutover (the
> archetype itself ships under canonical `ARBITRAGE_PRICE_DISPERSION` name in code + UAC).
> **Blast radius**: ~5 active plans + several question docs; no code references (UAC `LEVERAGED_FUNDING_ARB` enum entry
> never existed).
> **Suggested owner**: operator triage — references span multiple plan-of-record owners (defi_master, master plan,
> instruments_live_master, strategy_and_dart_master, live_pipeline_mtds_mdps_features, paper-vs-live workflow questions).

## What I found

Per Stream B Gate in
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
L191-193:

> **Gate:** Codex doc/code/plans all use `ARBITRAGE_PRICE_DISPERSION` (with config variant) for
> funding-dispersion-leveraged. No remaining references to `leveraged_funding_arb` as a standalone archetype except in
> this plan + the issue file (as historical context).

Workspace grep `rg 'leveraged_funding_arb' --type py --type md` (run 2026-05-09 PM from
`unified-trading-pm/`) shows the following non-historical-context references that use the legacy name as a standalone
archetype label:

### Active plans (need rename or annotation)

- [`plans/active/defi_master_2026_05_07.md`](../defi_master_2026_05_07.md) — multiple references including:
  - L?? "May-23 hedge archetype (`leveraged_funding_arb` config variant — cross-venue funding-rate dispersion)" — the
    parenthetical cites correct semantics but the bare name persists
  - L?? "funding spread; renamed from legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07" — this
    one IS annotated correctly
  - L?? "`leveraged_funding_arb` archetype live" + "`leveraged_funding_arb` strict P0 — RESOLVED 2026-05-08" —
    standalone-name usage
  - L?? "`leveraged_funding_arb` requires those chains" / "`leveraged_funding_arb` blocker around perp-funding capture"
    / "carry_staked_basis defaults: ETHEREUM + SOLANA + ARBITRUM. leveraged_funding_arb defaults" / "`leveraged_funding_arb` second"
    / "`leveraged_funding_arb` slips at the live-cutover gate" / "`leveraged_funding_arb` live in the immediate
    post-cutover week"
- [`plans/active/master_to_live_defi_2026_05_23.md`](../master_to_live_defi_2026_05_23.md) — Stream B parent flagged
  the global rename was applied but standalone references may persist; 2026-05-09 audit in parent plan claims "global
  rename applied (13 occurrences)" so re-grep needed to confirm none remain
- [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`](../live_pipeline_mtds_mdps_features_2026_05_08.md):
  - "(b) `cross_instrument.perp_funding_vs_spot_basis` — needed for `leveraged_funding_arb`"
  - "(`leveraged_funding_arb`) live on a real wallet ≥7 continuous days by 2026-05-23"

### Active epic plans

- [`plans/epics/cefi_master_2026_05_07.md`](../../epics/cefi_master_2026_05_07.md) — "(`carry_staked_basis` +
  `leveraged_funding_arb`)"
- [`plans/epics/instruments_live_master_2026_05_08.md`](../../epics/instruments_live_master_2026_05_08.md) —
  "`leveraged_funding_arb` MUST have AWS parity by 2026-05-23"
- [`plans/epics/strategy_and_dart_master_2026_05_07.md`](../../epics/strategy_and_dart_master_2026_05_07.md) —
  "hedging-leg `leveraged_funding_arb`) are perp-based"

### Question docs (annotation needed)

- [`plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md`](../../questions/paper_vs_live_workflow_maturity_2026_05_08.md)
  — already partially annotated ("**Stale terminology.** No `LEVERAGED_FUNDING_ARB` symbol exists. The actual archetype
  is `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` with a `funding-rate-dispersion` variant"); body still has bare
  references in the Q-shaped scenarios — could be left as-is per "historical context as the question was originally
  framed" or annotated row-by-row
- [`plans/questions/defi_recursive_borrow_archetypes_2026_05_08.md`](../../questions/defi_recursive_borrow_archetypes_2026_05_08.md)
  — "(per the 2026-05-07 operator decision that `leveraged_funding_arb` is a config variant of
  `ARBITRAGE_PRICE_DISPERSION`...)"; this IS correct annotation
- [`plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md`](../../questions/api_keys_wallets_accounts_readiness_2026_05_08.md)
  — "(especially for `leveraged_funding_arb` which is...)"
- [`plans/questions/topology_features_strategy_ml_execution_2026_05_08.md`](../../questions/topology_features_strategy_ml_execution_2026_05_08.md)
  — "leveraged_funding_arb VM" / "Q6.b — Is the topology different for the two May-23 archetypes (carry_staked_basis
  lead, leveraged_funding_arb"
- [`plans/questions/defi_readiness_catalogue_2026_05_08.md`](../../questions/defi_readiness_catalogue_2026_05_08.md) —
  multiple references in DeFi readiness scope discussion
- [`plans/questions/batch_live_design_symmetry_2026_05_08.md`](../../questions/batch_live_design_symmetry_2026_05_08.md)
  — "I3. **DeFi (carry_staked_basis + leveraged_funding_arb)**"
- [`plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md`](../../questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md)
  — "(`carry_staked_basis` + `leveraged_funding_arb`) that have not yet generated a single dollar"

### Archive (allowed — no action needed)

- `plans/archive/work_split_2026_05_07_harsh_5tab_layout.md` — historical workplan
- `plans/archive/audit_followups_2026_05_07.plan.md` — historical
- All other `plans/archive/*.md` matches

## Why it matters

- **Stream B gate cannot fully close** until the workspace grep returns only historical-context hits. This blocks Phase
  D of [`arbitrage_price_dispersion_finalisation_2026_05_09.md`](../arbitrage_price_dispersion_finalisation_2026_05_09.md).
- **Ambiguity in plan reading**: an agent reading `defi_master` or one of the epic plans sees `leveraged_funding_arb`
  as a standalone archetype name; only the canonicalisation plan + this issue doc clarify it's a config variant. New
  agents will continue to use the legacy name in new docs unless the rename actually completes.
- **Drift accelerates over time**: each new plan written with the legacy name compounds the rename cost; better to
  sweep now while the count is bounded.

## Recommended decision

Three valid dispositions:

1. **Bulk rename in a single PM commit** (~30 min): walk every active plan + epic + question doc, rename
   `leveraged_funding_arb` → `ARBITRAGE_PRICE_DISPERSION` (with config-variant annotation `funding-rate-dispersion`
   where the context warrants), preserve original wording for historical-context lines (annotate inline). Owner: a PM
   tab agent.

2. **Per-plan-owner rename** (slower, higher quality): each active plan's owner does the rename in the same logical
   unit as their next plan-flip commit. Tracker: this issue doc; close when grep returns only historical-context hits.

3. **Accept the gate stays open until A/B/C ship** (do nothing): the rename was always optional polish; the canonical
   name is in the code + UAC + the canonical codex docs (post-Phase E ship). Plan-body references to the legacy name
   are documentation drift that doesn't affect the May-23 cutover. Re-evaluate at archive boundary of the parent Stream
   B plan.

**Recommendation**: option 2 — per-plan-owner rename. The cost is per-plan small (1 commit per owner), the rename is
mechanical (no design judgment), and the resulting state is correct rather than annotated. Bulk rename (option 1) risks
the foot-gun #1 / #2 patterns where a PM agent mass-edits files outside their context.

## Composes with

- [`plans/active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](../defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
  Stream B Gate (L191-193) — the gate this issue doc tracks
- [`plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md`](../arbitrage_price_dispersion_finalisation_2026_05_09.md)
  Phase D — depends on this gate close
- CLAUDE.md "Findings Triage Discipline" case 3 — outside any single plan owner; multiple plans need the rename
- CLAUDE.md "Plan Archival HARD RULE" — ensures no deferral lost; this issue doc is the durable home pending owner
  triage

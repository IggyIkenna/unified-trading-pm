---
doc_type: issue
title: execution_master's real scope (delta/algo-selection, aggressiveness, co-location, position/price
  approximation, market-making/arb/options, execution-backtesting) is scattered across strategy_master and
  security_and_cross_cutting_master, not execution_master
summary: >-
  `execution_master`'s own epic hub declares a narrow "Owns" (handlers + transfers + treasury + custody + flash loan
  + matching engine) and today shows only 1 active child doc — but the operator's own list of what execution_master
  SHOULD cover (delta approximations, algo building, aggressiveness, co-location, position approximations, price
  approximations on cash data, credits for arb/market-making/options, physical venue paper/live/batch testing,
  execution-backtesting via looping pre-computed strategy instructions through market data) is substantial and
  clearly real — a spot-check found 4 large docs (783/391/284+ lines) covering exactly this territory, but 3 of 4
  are tagged `parent_epic: strategy_master` and 1 `security_and_cross_cutting_master`, none `execution_master`.
  This is the SAME shape of miscategorization the 2026-08-19 epic-assignment audit found and fixed for
  cefi_master/defi_master (20-33% mis-tagged), but not yet checked in this direction (execution_master
  under-claiming, not an asset-group epic over-claiming) — genuinely different failure mode, same root rule
  (`/codex/11-project-management/epic-assignment-decision-rule.md`), needs its own audit pass.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [epic-taxonomy, parent-epic, execution-master, plan-authoring, follow-up]
related:
  [
    /codex/11-project-management/epic-assignment-decision-rule.md,
    /plans/epics/execution_master.md,
    /plans/epics/strategy_master.md,
    /codex/04-architecture/execution-algorithm-selection.md,
    /plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
    /plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md,
    /plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md,
    /plans/active/bucket_fold_execution_strategy_2026_07_17.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
  ]
created: "2026-08-19"
author: claude
parent_epic: plan_hygiene_master
source: >-
  Operator asked mid-session (2026-08-19, right after the epic-assignment audit shipped) why execution_master looks
  so thin given how much substantive scope it should own — the question that surfaced this. Investigated live via
  targeted `rg`/frontmatter grep, not exhaustive; see "What was actually checked" below.
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/04-architecture/execution-algorithm-selection.md,
    /codex/04-architecture/execution-policy.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-execution-algo.md,
  ]
---

# execution_master's real scope is scattered, not missing

## What triggered this

Right after the epic-assignment audit shipped (29 docs retagged across cefi/defi_master, see
`/codex/11-project-management/epic-assignment-decision-rule.md`), the operator pointed out that `execution_master`
should own a lot of substantive work — delta approximations, algo building, aggressiveness (a tunable dial),
co-location, position approximations, price approximations on cash data, credits so arbitrage/market-making/options
can all run through one mechanism, physical-venue testing across paper/live/batch, and execution-backtesting
(looping pre-computed strategy instructions through historical market data to generate orders) — and asked "where
did they go?", given the epic currently shows only 1 active child doc.

## What was actually checked (bounded, not exhaustive)

1. **`execution_master.md`'s own body**: "Owns" line is narrow — "execution-service: handlers + transfers +
   treasury coordinator + custody integration + flash loan + matching engine." No mention of algo-selection detail,
   aggressiveness, co-location, position/price approximation, or backtesting. Only 2 open backlog items (G12
   recon-freeze signal emission, F-32 MEV auto-escalation), both narrow. `_(no active plans currently declare
   parent_epic: execution_master)_` is the doc's own literal text.
2. **A real, already-acknowledged documentation gap**: `/codex/04-architecture/execution-algorithm-selection.md`
   states its own reason for existing: `execution_service/algorithms/selector.py` cited a doc named
   `UNIFIED_EXECUTION_DELTA.md` as its taxonomy SSOT, but that file **has never existed anywhere in the
   workspace** — finding F37 in `capability_wizard_analysis_findings_2026_06_11.md`, which is still `status: open`
   today (not resolved, not archived). This is a direct, named hit on the operator's "delta approximations" item.
3. **Spot-check of 4 large, clearly execution-algo-territory docs** (found via `rg` for
   delta-hedging/market-making/co-location/backtest-execution/aggressiveness/position-sizing terms across the
   active corpus, then frontmatter-grepped):

   | Doc | Lines | Current `parent_epic` |
   |---|---|---|
   | `service_config_ownership_and_instruction_contract_2026_08_12.md` | 783 | `strategy_master` |
   | `strategy_archetype_latency_deployment_profile_execution_2026_08_10.md` | 391 | `strategy_master` |
   | `bucket_fold_execution_strategy_2026_07_17.md` ("execution-store 4+pred → 1 & strategy-store flat → tiered") | 284 | (unclear — no `parent_epic:` line matched a direct grep, needs a full read) |
   | `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` | — | `security_and_cross_cutting_master` |

   None are `execution_master`. This is a small, non-exhaustive sample — a real full sweep (same shape as the
   cefi/defi audit) would need to search systematically, not just by keyword grep, since keyword search both
   over-matches (generic words like "aggressiveness" appear in unrelated contexts) and under-matches (a doc could
   describe co-location without using that word).

## Why this matters, and why it's a DIFFERENT failure mode than the cefi/defi one

The 2026-08-19 audit found asset-group epics (cefi/defi_master) **over-claiming** shared-mechanism work found via
that asset group. This looks like the mirror image: a shared-mechanism epic (`execution_master`) **under-claiming**
because its own scope got absorbed into an adjacent epic (`strategy_master`) during the 2026-08-18 fold history —
`execution_master` already absorbed `trading_agent_master` (0 refs at fold time, a real empty fold) on 2026-08-18;
it's plausible some genuinely execution-specific content drifted the OTHER way into `strategy_master` around the
same restructuring window, or was simply always mis-tagged and never caught because `execution_master` never got a
`/plan-reconcile` pass substantial enough to notice its own thinness relative to its stated scope.

## Recommended next step

Run the SAME decision-rule test (`/codex/11-project-management/epic-assignment-decision-rule.md`) in the other
direction: instead of asking "is this asset-group doc actually shared-mechanism," ask **"is this
strategy_master/security_and_cross_cutting_master doc actually execution_master's specific mechanism (order
generation, algo selection/aggressiveness, co-location, position/price approximation, execution-backtesting)?"**
Scope: full read of `strategy_master`'s ~14 active docs (small enough to read directly, no sampling needed) plus a
systematic (not keyword-only) content check against `execution_master`'s stated scope. Also resolve or re-scope the
still-open F37 finding (`capability_wizard_analysis_findings_2026_06_11.md`) — the missing `UNIFIED_EXECUTION_DELTA`
SSOT is a concrete, already-identified gap, not a new one.

## Todos

- [ ] [REVIEW] P1. Full-read audit of `strategy_master`'s active child docs (read `rg -l "^parent_epic:
      strategy_master$" plans/active/*.md plans/active/issues/*.md` for the current list) against the
      epic-assignment-decision-rule test, specifically checking each for execution_master-shaped content (algo
      selection/aggressiveness, order generation, position/price approximation, co-location, execution-backtesting)
      that should retag to `execution_master`. Repo: unified-trading-pm.
- [x] ✅ [REVIEW] P2. **Full-read `bucket_fold_execution_strategy_2026_07_17.md` — CONFIRMED correctly scoped, no
      retag.** Read in full (all 284 lines). `parent_epic: security_and_cross_cutting_master` (line 44). Content is
      entirely GCS bucket-topology/naming consolidation (execution-store 4+pred→1, strategy-store flat→tiered,
      provisioning/parity-migrate/atomic-cutover/consolidator-retarget/source-delete) — near-complete infra fold, zero
      execution-algorithm/order-generation content. Passes the decision-rule test cleanly: this fold would look
      identical regardless of which service's buckets were being folded — genuine cross-cutting storage mechanism, not
      execution_master's specific-mechanism scope. No change needed.
- [x] ✅ [REVIEW] P2. **Resolve F37 — CONFIRMED already fixed, doc is substantive not a stub.** Read
      `/codex/04-architecture/execution-algorithm-selection.md` in full (138 lines, `status: current`,
      `created: 2026-07-30`). It fully replaces the missing `UNIFIED_EXECUTION_DELTA.md` selector.py cited: the
      `InstructionType` → execution-algorithm taxonomy, `select_algorithm()`'s 4-step priority chain, ghost
      (declared-but-unimplemented) algorithms, the two legitimate ICEBERG universes (canonical-backtest-safe vs
      manual/live), naming reconciliation, and change discipline (keep selector.py + UAC's `algo_compatibility`
      transcription in sync). `capability_wizard_analysis_findings_2026_06_11.md`'s own F33–F37 block already reads
      "FIXED — verified 2026-07-30, execution-service@52fe0632 + unified-api-contracts@91df8e34". The "delta
      approximation" the operator asked about maps to this doc's algo-selection-taxonomy scope, not a separate
      unwritten thing — F37 needs no further action. (The parent issue doc's own `status: open` is unrelated — it's a
      running log with other, unrelated findings still open; not a signal this specific finding is unresolved.)
- [ ] [REVIEW] P3. Same under-claiming check for `security_and_cross_cutting_master` → `execution_master` direction
      (only 1 doc spot-checked here, `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`) — low
      priority since `security_and_cross_cutting_master` is already known-large (232 docs) and this is a single
      data point, not a pattern yet.

## Progress Log

- **2026-08-19, claude (`/autonomous`)**: dispatched 4 Sonnet-5 sub-agents (read-only investigation, no shipping
  authority) — 3 splitting the 14-doc `strategy_master` full-read audit (todo 1), 1 doing a targeted keyword scan of
  `security_and_cross_cutting_master`'s ~237 docs for execution-shaped content (todo 4). Personally closed todos 2 and
  3 in parallel while those ran: `bucket_fold_execution_strategy_2026_07_17.md` read in full and confirmed correctly
  `security_and_cross_cutting_master` (pure bucket-topology fold, no execution-algo content); F37 confirmed already
  fixed by direct read of `/codex/04-architecture/execution-algorithm-selection.md` (substantive 138-line SSOT, not a
  stub). Every sub-agent finding will be personally re-verified against the actual file content before any retag
  ships — no sub-agent has ship authority on this issue.

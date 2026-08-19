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
asset_group: [meta] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting]; an epic-taxonomy/plan-authoring finding (parent_epic: plan_hygiene_master), not data-pipeline scope
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

- [x] ✅ [REVIEW] P1. **Full-read audit of `strategy_master`'s 14 active child docs — DONE, findings ratified.**
      3 Sonnet-5 sub-agents each full-read a subset against the decision-rule test; every RETAG-CANDIDATE finding was
      personally re-verified against the actual file content (not taken on the sub-agent's word) before acting.
      **10/14 CORRECTLY-SCOPED** (no change): `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md`,
      `cross_venue_funding_reversion_research_2026_07_24.md`, `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`,
      `l2_book_microstructure_capture_2026_07_13.md`, `v2_engine_venue_buildout_2026_06_15.md`,
      `strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md`,
      `issues/capability_wizard_analysis_findings_2026_06_11.md` (personally read by me directly, not delegated),
      `issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`,
      `issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`,
      `issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`. **4/14 carry genuine execution_master-shaped
      content — 1 already retagged, 3 filed as scoped split-follow-up (see new todos below), none actioned blind:**
      1. `strategy_archetype_latency_deployment_profile_execution_2026_08_10.md` (391L, whole-doc) — **RETAGGED
         2026-08-19**, `parent_epic: strategy_master` → `execution_master` (this doc's own frontmatter + both epic
         docs' "Assigned active plans" sections updated in the same commit). Personally read in full (all 392 lines):
         entirely archetype-declared deployment-profile → `runtime-topology.yaml` co-location/sizing derivation
         (`co_located_vm` vs `distributed`, live vCPU/memory sizing from active-archetype client/instrument counts) —
         matches the operator's named "co-location" execution_master scope verbatim, doc's own title starts
         "Execution —". Clean single-frontmatter-line move, no content split needed (whole doc is one coherent unit).
      2. `service_config_ownership_and_instruction_contract_2026_08_12.md` (783L) — majority execution-shaped, NOT
         retagged this session, see new todo below for exact section boundaries.
      3. `crypto_alpha_research_2026_07_24.md` (639L) — majority-of-Progress-Log execution-shaped, NOT retagged this
         session, see new todo below.
      4. `carry_staked_basis_funding_scan_experiment_2026_06_16.md` (839L) — 2 specific sub-sections execution-shaped,
         NOT retagged this session, see new todo below.
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
- [x] ✅ [REVIEW] P3. **Same under-claiming check for `security_and_cross_cutting_master` → `execution_master`
      direction — DONE, clean result.** Targeted keyword scan (not full-read of all 237 docs, per scope): 237 docs
      tagged `parent_epic: security_and_cross_cutting_master`, narrowed via ripgrep for execution-algo/aggressiveness/
      co-location/execution-backtest/order-generation/price-approximation keyword clusters → 4 candidates, all read in
      full. **Zero retag candidates**: `bucket_fold_ml_2026_07_17.md` + `bucket_fold_features_2026_07_17.md` matched
      "co-location" as a homonym (ML-artifact bucket co-location, not exchange co-location);
      `nick_ai_platform_disclosure_artifact_2026_08_16.md` and `issues/e2e_wiring_reachability_audit_2026_08_15.md`
      each had one passing mention of execution-algo/aggressiveness terms inside a genuinely broader cross-cutting
      scope (disclosure-artifact measurement, E2E reachability audit respectively) — not primary-subject execution
      content. Clean negative result, not manufactured to have something to report.
- [ ] [SPLIT] P2. **Split `service_config_ownership_and_instruction_contract_2026_08_12.md` (783L) — execution_master
      content confirmed, exact section boundaries below (personally verified by full read, not sub-agent-only).**
      Retag/extract to `execution_master`: **§ B** (execution-policy registry — algo-selection rules keyed by
      `(client_id, slot_label)`, GCS loader, hot reload), **§ G** (exhaustive execution-service change surface — G1
      config_algorithm threading into the live selector, G2 latency-timestamp threading through all 10 `ChildOrder`
      construction sites, G3/G3a benchmark-matcher duplication + lending-path rate-impact), **§ I** (candle-based
      fills — `CandleBookColsMatcher` depth-walk fill pricing, `ExecutionFidelityTier` ladder, sub-candle VWAP
      fallback rung — this is literally "price approximations on cash data"), **§ J1/J3/J4/J6** (dual-path SSOT
      register for `book_type`/benchmark-fill/algo-names/transfer-types — all execution-service-owned things). Stays
      `strategy_master`: **§ A** (audit summary, frames the whole doc — keep a pointer copy if split), **§ D**
      (strategy-service `ClientDomainConfig` subscription — genuinely strategy-side), the strategy-emit half of **§ H**
      (transfer netting — "why netting must sit strategy-side" is a strategy-service design point, even though the
      same section documents execution-service's consume-side transfer rail). **Why not done this session**: this is
      a live, heavily-active doc (`status: draft` but dozens of already-shipped ✅ todos citing real execution-service/
      UAC/strategy-service SHAs through 2026-08-16) with dense internal cross-references between sections — a rushed
      split risks severing the SHA-evidence trail or the doc's own narrative continuity (§ G explicitly builds on § A/
      B/C context). Needs a dedicated, careful pass, not inline surgery mid-audit. Repo: unified-trading-pm.
- [ ] [SPLIT] P2. **Split `crypto_alpha_research_2026_07_24.md` (639L) — execution-research content confirmed within
      the paper-trading-POC Progress Log, exact boundaries below.** Retag/extract to `execution_master`: the
      "Fill-model fidelity" subsection (PB.4/PB.6/PB.7/PB.8 — swept-vs-touched maker fill, missed-remainder policy,
      per-strategy fill backtest, aggTrades tape-fidelity), "Execution-config optimization" (PB.11/PB.13 — maker-vs-
      taker/participation/timing lever sweep = the operator's named "aggressiveness controls"; live−batch execution-
      realism differential), the "EXECUTION-REALISM AUDIT" section (maker-width sweep, ADV/depth capacity gating,
      liquid-universe rebuild), and "EXECUTION CALIBRATION vs Binance RFQ" (not yet read in full — verify at split
      time). Stays `strategy_master`: **§ C** (book-sizing/leg-selection decisions, operator-gated
      `BLOCKED-OPERATOR-DECISION`), the alpha-research findings proper (short-leg re-spec, basis realism,
      TS-momentum, multi-year walk-forward OOS) — these are genuine strategy-signal research even where they cite
      execution-cost numbers as an input. **Why not done this session**: same reasoning as above — a chronological
      research journal where findings cross-reference each other by PB-number across the fill-model/execution/alpha
      boundary; a naive split breaks the "PB.7 confirmed PB.4" style evidentiary chain. `asset_group: [cefi]` (not
      cross-cutting) — the execution-research content is CeFi-specific (Binance-perp fills/RFQ), so the destination
      section in `execution_master` should note that scoping, not treat it as cross-cutting execution work. Repo:
      unified-trading-pm.
- [ ] [SPLIT] P3. **Split `carry_staked_basis_funding_scan_experiment_2026_06_16.md` (839L) — 2 specific sub-sections
      confirmed execution-shaped, small and clearly bounded.** Retag/extract to `execution_master`: (a) "Global
      transaction-cost-optimal rebalance (the 'PhD formula')" — replaces the greedy rotation gate with a per-period
      L1 transaction-cost LP (`scipy.optimize.linprog`) deciding *how* to trade a rebalance (algo selection, ~15
      lines); (b) "Daily positioning guide (manual-execution helper)" — `--target-diff`/`--apply` loops a precomputed
      target book against market data to emit concrete OPEN/CLOSE/INCREASE/REDUCE/SWITCH orders (~13 lines), matching
      the operator's execution-backtesting definition ("looping through pre-computed strategy instructions with
      market data, generating orders") almost verbatim. Stays `strategy_master`: the net-carry ranking/hold/rotate
      model, venue/collateral eligibility, and the GAS/slippage cost-MODELING sections (these explicitly cite
      execution-service's existing cost models as dependencies rather than owning the mechanism). **Why not done this
      session**: lower priority (P3, smallest scope of the three) — bundled with the other 2 splits for a single
      dedicated pass rather than one-off surgery on a doc that's also mid-workstream (gated on the v9 data-migration
      per its own 2026-06-17 Progress Log entry). Repo: unified-trading-pm.

## Progress Log

- **2026-08-19, claude (`/autonomous`)**: dispatched 4 Sonnet-5 sub-agents (read-only investigation, no shipping
  authority) — 3 splitting the 14-doc `strategy_master` full-read audit (todo 1), 1 doing a targeted keyword scan of
  `security_and_cross_cutting_master`'s ~237 docs for execution-shaped content (todo 4). Personally closed todos 2 and
  3 in parallel while those ran: `bucket_fold_execution_strategy_2026_07_17.md` read in full and confirmed correctly
  `security_and_cross_cutting_master` (pure bucket-topology fold, no execution-algo content); F37 confirmed already
  fixed by direct read of `/codex/04-architecture/execution-algorithm-selection.md` (substantive 138-line SSOT, not a
  stub). Every sub-agent finding will be personally re-verified against the actual file content before any retag
  ships — no sub-agent has ship authority on this issue.
- **2026-08-19, claude (`/autonomous`), audit complete.** All 4 sub-agent reports returned; personally read all 4
  RETAG-CANDIDATE docs in full or substantially in full before acting (not the sub-agent's word alone) —
  `strategy_archetype_latency_deployment_profile_execution_2026_08_10.md` (392L, full),
  `service_config_ownership_and_instruction_contract_2026_08_12.md` (784L, full),
  `crypto_alpha_research_2026_07_24.md` (543/639L), `carry_staked_basis_funding_scan_experiment_2026_06_16.md`
  (505/839L, both flagged sub-sections confirmed present at the cited locations). One clean whole-doc retag executed
  (deployment-profile doc, both epic docs' Assigned-active-plans sections kept in sync in the same change). Three
  partial-content findings converted into precisely-scoped `[SPLIT]` follow-up todos with exact section boundaries —
  deliberately NOT surgically split this session: all three are live, actively-shipping, densely cross-referenced
  docs where a rushed split risks breaking SHA-evidence trails or chronological-journal evidentiary chains (the
  "PB.N confirmed PB.M" cross-reference style in the research-journal docs specifically). This routes the
  audit-scope finding to a proper follow-up unit per CLAUDE.md's findings-triage rule, not a deferral of the audit
  itself — the audit (todo 1) is complete with every candidate identified and personally verified. Todo 4
  (security_and_cross_cutting_master direction) also closed clean — no retags found. Remaining open work: the 3
  `[SPLIT]` todos.

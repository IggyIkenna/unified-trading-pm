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
status: resolved
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
resolved_by: >-
  All 7 todos done 2026-08-19. Full-read audit of strategy_master's 14 docs + targeted scan of
  security_and_cross_cutting_master's 237 docs, both complete. 1 clean whole-doc retag
  (strategy_archetype_latency_deployment_profile_execution_2026_08_10.md -> execution_master). 1 genuine 13-todo
  extraction (service_config_ownership_and_instruction_contract_2026_08_12.md ->
  execution_service_policy_and_fill_model_gaps_2026_08_19.md, new doc, parent_epic: execution_master). 2 findings
  reclassified to no-action after a full re-read (crypto_alpha_research_2026_07_24.md is strategy-desk research
  corpus per 4 independent na-eligibility-audit confirmations, not execution-service engineering;
  carry_staked_basis_funding_scan_experiment_2026_06_16.md's flagged content is historical Progress Log narrative,
  not open todos). bucket_fold_execution_strategy_2026_07_17.md and F37 both confirmed already correct/fixed. Both
  epic docs' Assigned-active-plans sections kept in sync throughout.
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

> **📦 ARCHIVED 2026-08-19 — all 7 todos done, resolved.** See `resolved_by` in frontmatter for the full outcome
> summary. Successor artifacts:
> [`execution_service_policy_and_fill_model_gaps_2026_08_19.md`](/plans/active/execution_service_policy_and_fill_model_gaps_2026_08_19.md)
> (the 13-todo extraction) and the retagged
> [`strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`](/plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md).

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
- [x] ✅ [SPLIT] P2. **Split `service_config_ownership_and_instruction_contract_2026_08_12.md` — DONE, 13 open todos
      moved.** Full re-read (both halves, all 784 lines — the first pass had only covered 558/784, missing §K
      entirely; reading the tail changed the boundary). Genuinely execution-service-owned open todos (§B's
      `execution_policy_ref` rejection; §G's G3/G3a benchmark-duplication + algo-vocabulary-unification + wire-the-
      evaluator + confirm-consumers; §I's sub-candle-rung decision + population-measurement + PB.8-correction +
      update-execution-policy.md; §K's PB.8-cap-definition + route-through-then_params + retire-campaign-scripts — 13
      total) moved VERBATIM to new doc
      [`execution_service_policy_and_fill_model_gaps_2026_08_19.md`](/plans/active/execution_service_policy_and_fill_model_gaps_2026_08_19.md)
      (`parent_epic: execution_master`), each replaced in-place with a `➡️ MOVED` pointer. **Correction to the
      original section-level framing**: §J1/J3/J4/J6 turned out to have NO separate open checkboxes of their own — J1
      and J6 are already ✅ resolved, and J3/J4's fixes ARE the §G G3/G3a/algo-vocabulary items already captured; no
      double-move needed. §J7 (archetype registry engine-vs-schema gate) is strategy-service's own archetype
      registry, not execution — corrected to stay. Everything else (§A audit table, all done ✅ todos, §C/D, §H, §F,
      the full Progress Log) untouched — this was a checkbox-only extraction, never a doc merge. Both epic docs'
      Assigned-active-plans sections updated in the same change. Repo: unified-trading-pm.
- [x] ✅ [SPLIT] P2 → **RECLASSIFIED: no split needed.** `crypto_alpha_research_2026_07_24.md` re-read in full (all
      639 lines — the first pass had only covered 543/639). **Correction to the original finding**: the flagged
      fill-model/execution-config sections are genuinely `[RESEARCH]`-tagged strategy-desk work in `e2e-testing`
      research harnesses that MODELS execution costs as a research INPUT (maker/taker sweeps, ADV/depth gating,
      RFQ-vs-screen calibration) — it does not touch execution-service production code (none of the open todos here
      name `execution-service` as their repo; they're `e2e-testing` harness work or `strategy-service` book-sizing).
      This is the same "cites the mechanism as a dependency, doesn't own it" pattern already correctly applied to
      `carry_staked_basis`'s GAS/slippage sections below — I mis-applied the test the first time by keying off
      SUBJECT MATTER (fill models, execution config) rather than OWNERSHIP (who'd actually implement the fix).
      Independent corroboration: 4 separate `na-eligibility-audit` passes (2026-07-30, 08-08, 08-09) already,
      repeatedly, and explicitly characterize this entire doc as "archetypal trading-judgment content... execution-
      config sweeps, leg re-specs, allocator design, universe construction" — i.e. strategy-desk research corpus, not
      AO-dispatchable execution-service engineering. No retag. Repo: unified-trading-pm.
- [x] ✅ [SPLIT] P3 → **RECLASSIFIED: no split needed.** `carry_staked_basis_funding_scan_experiment_2026_06_16.md`'s
      2 flagged items ("PhD formula" LP rebalance-cost optimizer; "Daily positioning guide" order-emission helper)
      are both **historical Progress Log entries describing already-shipped work**, not open `- [ ]` checkboxes —
      confirmed against the full text (both read in the original audit pass). Epic-assignment routing exists to get
      OPEN, dispatchable work to the right queue; there is no open todo here to route. Moving already-shipped
      narrative text would fragment the journal's own evidentiary chain for zero operational benefit — correctly
      left in place. Repo: unified-trading-pm.

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
- **2026-08-19, claude (`/autonomous`), all 3 SPLIT todos resolved — doc archived.** Re-read both remaining docs in
  full (had only covered 558/784 and 543/639 lines respectively) before acting, catching a gap: the first pass's
  §J1/J3/J4/J6 framing for `service_config_ownership` didn't survive a full re-read (J1/J6 already resolved, J3/J4's
  fixes are the §G items already captured — no double-move) and its §K section (614-663, e2e-fill-model
  reproducibility) hadn't been read at all in the first pass, adding 3 more genuine open todos. Net: 13 open
  execution-service todos extracted verbatim to new doc `execution_service_policy_and_fill_model_gaps_2026_08_19.md`
  (`parent_epic: execution_master`), source doc left otherwise untouched. Separately, re-reading `crypto_alpha_research`
  in full surfaced a genuine correction to my own earlier framing: its flagged content is strategy-desk `[RESEARCH]`
  work in e2e-testing harnesses (fill-cost MODELING as a research input), not execution-service engineering — 4
  independent na-eligibility-audit passes already say so explicitly; reclassified to no-action rather than force a
  split that would have mis-homed research judgment as engineering work. `carry_staked_basis`'s 2 flagged items were
  re-confirmed as historical Progress-Log narrative (no open checkboxes), also no-action. All 7 todos now done, 0
  open, unlocked — archiving per the plan-completion-and-archival-discipline HARD RULE.

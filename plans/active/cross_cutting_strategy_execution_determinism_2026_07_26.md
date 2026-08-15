---
doc_type: plan
title: Cross-cutting strategy/execution determinism + capability-registry — Track 24 extraction
summary: >-
  Extracted 2026-07-26 from `cross_cutting_consolidated_closeout_2026_07_25.md` Track 24 (resolved
  `autonomous_session_operator_decisions_2026_07_25.md` entry #19) — a genuinely different angle from that doc's other
  23 Tracks (strategy/execution/capability-registry, not data-pipeline), ~121 open todos across the 8 source docs below,
  too large to drain in one closeout pass. This doc is a coordination index, not itself a triage: the actual work is a
  dedicated triage pass over the 8 docs, scoping any genuinely AO-eligible slices out per the dispatch-scope-eligibility
  rule (much of this is design/research judgment, not a checkable fact).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, execution-service, batch-live-reconciliation-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cross-cutting, strategy, execution, determinism, capability-registry, triage]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /plans/archive/2026_08/carry_strategy_ensemble_productionization_2026_07_24.md,
    /plans/active/cross_venue_funding_reversion_research_2026_07_24.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md,
    /plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md,
    /plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md,
    /plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
    /plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md,
    /plans/active/v2_engine_venue_buildout_2026_06_15.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
assigned_role: backend_engineer
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  cross_cutting_consolidated_closeout_2026_07_25.md Track 24, per its own note that a future split "should extract this
  Track as its own child first, being the most thematically separable." Resolved as
  autonomous_session_operator_decisions_2026_07_25.md entry #19, option A.
drift_direction: advance-code
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/v2_engine_venue_buildout_2026_06_15.md,
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
---

# Cross-cutting strategy/execution determinism + capability-registry — Track 24 extraction

## Sources (moved verbatim from the parent's Track 24)

- [carry_staked_basis_funding_scan_experiment_2026_06_16.md](/plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md)
- [carry_strategy_ensemble_productionization_2026_07_24.md](/plans/archive/2026_08/carry_strategy_ensemble_productionization_2026_07_24.md)
- [cross_venue_funding_reversion_research_2026_07_24.md](/plans/active/cross_venue_funding_reversion_research_2026_07_24.md)
  (the carry_staked_basis family — combines DeFi LST staking with CeFi perp funding across venues; open: live/broad-
  universe coverage-completion work)
- [citadel_paper_batch_live_reconciliation_2026_06_19.md](/plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md)
- [issues/batch_live_reconciliation_service_audit_2026_05_27.md](/plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md)
- [issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md](/plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md)
  (the paper==batch-rerun==live determinism-spine family — finishing the ε=0 proof machinery + BLRS audit remediation +
  the 4-AG smoke-harness discrepancy set)
- [defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md](/plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md)
- [issues/capability_wizard_analysis_findings_2026_06_11.md](/plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md)
- [issues/capability_wizard_gap_discovery_2026_06_11.md](/plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md)
  (the capability-wizard family — full-taxonomy coverage across the 53-57 archetype registry, spans DeFi/CeFi treasury
  splits + options/vol)
- [v2_engine_venue_buildout_2026_06_15.md](/plans/active/v2_engine_venue_buildout_2026_06_15.md) (confirmed multi-AG:
  CeFi venues, DeFi/GMX, sports/betfair-smarkets, TradFi/CME options, prediction/ML_LEAN engines, one buildout). **Known
  over-count, carried from the parent's audit**: this doc's 37 open boxes are MOSTLY already covered by its own
  2026-07-13 5-child split (3 archived, 2 still active) — re-verify what's genuinely still open in the parent before
  counting it fresh here.

**Close-out criterion** (unchanged from the parent Track): the carry_staked_basis ensemble ships live coverage; the
determinism-spine ε=0 proof lands; BLRS audit items close; the capability-wizard's drift-check/gap-tracker items close
across the full taxonomy; v2_engine_venue_buildout's per-venue items close.

## Todos

- [ ] [REVIEW] P2. Run the dedicated triage this extraction exists for: re-verify each of the 8 sources' actual open
      count against current HEAD (several may have moved since 2026-07-25), correct the `v2_engine_venue_buildout`
      over-count noted above, and split genuinely AO-eligible/determinable-outcome slices into a normal dispatch batch —
      leaving open-ended research/design items (e.g. capability-wizard taxonomy judgment calls) as LOCAL work per the
      dispatch-scope-eligibility rule. Repo: unified-trading-pm. **round5-cross-cutting-audit 2026-08-08**: the
      plan-destination question (dispatch batch = `planning` or `NA`?) is answered by the standing "Plan destination —
      ASK BEFORE CREATING" HARD RULE: default `NA` unless the operator explicitly overrides. No live operator input
      required to apply the default.
- [ ] [DIAG] P2. **Multi-leg basis/arb paper fill-rate figures in promotion/sizing decisions (migrated 2026-08-10 from
      `plans/archive/issues/multi_leg_paper_batch_live_parity_gap_2026_08_10.md`, which was closed + archived once its
      execution plan shipped)** — confirm whether any CARRY_STAKED_BASIS / CARRY_BASIS_PERP paper run's fill-rate or
      slippage figures were cited in an actual promotion/sizing decision (vs. only the directional P&L signal); if so,
      flag that decision for a re-check, since the pre-2026-08-10 flat-loop fill model overstated hedge fill-rate by
      ~9pp (characterized by the execution plan's paper analysis) and paper/batch now settle LEADER_HEDGE via real
      leader/hedge/unwind sequencing. Repo: unified-trading-pm.

## Progress Log

- **2026-07-26** — Extracted from `cross_cutting_consolidated_closeout_2026_07_25.md` Track 24 verbatim, per resolution
  of `autonomous_session_operator_decisions_2026_07_25.md` entry #19 (option A). No content triaged yet — that is this
  doc's own todo 1.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged, still the sole todo): the
  triage-and-split work is real, but its output is a new AO dispatch batch, and the ask-before-creating HARD RULE makes
  plan destination an operator call; the doc's own framing ("design/research judgment, not a checkable fact") still
  holds on a fresh read.
- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — the sole todo's second half is authoring a new AO dispatch batch —
  the ask-before-creating HARD RULE makes plan destination an operator call; the doc itself frames its content as
  'design/research judgment, not a checkable fact'.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope, no change needed (6 entries) -- pure coordination-index doc
  over 8 source plans (this doc's own todo is a future triage pass, not itself code work), so no source-code path
  applies; existing plan/issue/codex links remain the minimal correct set.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- this doc's own
  round5-cross-cutting-audit entry (2026-08-08) already resolved the plan-destination question the sole todo raises,
  citing the standing "Plan destination -- ASK BEFORE CREATING" HARD RULE: default `NA` unless the operator explicitly
  overrides. The sole todo's own output is authoring a NEW dispatch batch, which defaults NA -- not re-litigating an
  already-resolved-today question.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (6 entries) -- the only edit since the
  2026-08-03 scout pass was a referrer-path fix (`honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` moved to
  `plans/archive/issues/`), which this doc's context_scope doesn't reference; still a pure coordination-index doc over 8
  source plans, no source-code path applies.

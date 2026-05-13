---
title:
  "Missing question docs (risk_simulations + client_reporting_pnl_attribution + plans/questions/README) — disposition
  decision"
status: active
created: 2026-05-10
deadline: pre-cutover (P0 — May-23 plans cite ghost SSOTs)
horizon: 0.5-day operator-decision then 1-2 day execution
spawned_from: plans/archive/issues/missing_question_docs_orphan_references_2026_05_10.md (archived 2026-05-10)
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  owner: operator triage → assigned tab
  cadence: one-shot
  verifier: 8 active files no longer reference dead slugs OR slugs re-spawn with content; grep returns 0 orphan refs
  last_executed: NEVER
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (design, multiplier 0.6×).
  Owner agent: fill baseline + multiply × 0.6 per codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

# Missing question docs disposition

> **Severity**: P0 — May-23 cutover plans cite missing SSOTs for circuit-breaker rule definition + PnL attribution
> decomposition + per-archetype paper-vs-live carve-out.
>
> **Blast radius**: 8 active files in PM repo reference docs that don't exist (1 active plan + 5 question docs + 1 codex
> doc + 1 spawned execution plan).
>
> **Suggested owner**: operator triage — pick disposition (re-spawn / fold-in / redirect / accept-loss-and-remove-refs).

## Why this plan exists

Spawned 2026-05-10 from the archived issue
[`plans/archive/issues/missing_question_docs_orphan_references_2026_05_10.md`](../archive/issues/missing_question_docs_orphan_references_2026_05_10.md).

Three files **never committed to git** AND **gone from disk** as of 2026-05-10:

1. `plans/questions/client_reporting_pnl_attribution_2026_05_08.md`
2. `plans/questions/risk_simulations_limits_alerting_2026_05_08.md`
3. `plans/questions/README.md`

Note: The active plan `plans/active/risk_simulations_limits_alerting_2026_05_10.md` does exist (spawned from a
first-pass reconstruction PM@6e504f0b), but the _question doc_ it was supposed to be drafted from is gone. Same for
client_reporting_pnl_attribution — the active plan `plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md`
exists; its predecessor question doc is gone.

## 8 active references to ghost slugs

| File                                                                    | Lines                 | What it claims                                                                                                       |
| ----------------------------------------------------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md` | 20, 64, 106, 171, 597 | `risk_simulations_limits_alerting_2026_05_08` OWNS real-state risk-limit + circuit-breaker rule definition           |
| `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`        | 580–581               | Cites both as siblings; Phase 3.D + Phase 7 depend on them                                                           |
| `plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md`     | 568–569               | Sibling-question cross-link; treasury rollup view (C4) is shared dep                                                 |
| `plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md`   | 473, 476              | "Composes with" both — risk + portfolio overlap, PnL + portfolio overlap                                             |
| `plans/questions/batch_live_design_symmetry_2026_05_08.md`              | 513                   | "PnL reporting must" — references `client_reporting_pnl_attribution`                                                 |
| `plans/questions/defi_readiness_catalogue_2026_05_08.md`                | 937, 939              | "Composes with" both — simulation harness + chain primitives feed risk; PnL decomposition needs DeFi catalogue       |
| `plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md`         | 19, 94, 430, 688, 742 | Frontmatter `related_codex:` + body cites `risk_simulations_limits_alerting` "owns mock-data-as-stress-test surface" |
| `codex/04-architecture/paper-vs-live-execution-seam.md`                 | 48                    | Codex SSOT cross-links to it as canonical risk-simulation doc                                                        |

## Done definition

- [ ] **[AGENT] P0**. Operator triage on disposition (single decision, applies to all 8 references): Options: (a)
      **Redirect to active plans**: rewrite all 8 references to point at the existing
      `plans/active/risk_simulations_limits_alerting_2026_05_10.md` +
      `plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md` (the question docs are dead; the active plans
      already carry the SSOT scope). (b) **Re-spawn the question docs from active-plan content** (reverse-engineer);
      useful only if operator wants a lower-velocity discussion surface separate from the live execution plan. (c)
      **Accept-loss + remove refs**: treat the 8 references as orphan + delete the cite lines. Recommendation: (a) —
      redirect to active plans. The active plans exist + carry the canonical scope.
- [ ] **[SCRIPT] P0**. Once operator picks disposition, run mechanical sweep across the 8 cite sites + replace
      `plans/questions/risk_simulations_limits_alerting_2026_05_08.md` →
      `plans/active/risk_simulations_limits_alerting_2026_05_10.md` (and same for PnL).
- [ ] **[SCRIPT] P0**. Workspace grep `risk_simulations_limits_alerting_2026_05_08` +
      `client_reporting_pnl_attribution_2026_05_08` + `plans/questions/README.md` — assert 0 hits remain after the
      sweep.

## Full-execution criterion (per "Plans Run To Actual Completion" HARD RULE)

- ✅ All 8 references point to live SSOT artifacts.
  - **What ran**: workspace ripgrep + per-file Edit.
  - **Verification**: `rg "risk_simulations_limits_alerting_2026_05_08"` returns 0 hits;
    `rg "client_reporting_pnl_attribution_2026_05_08"` returns 0 hits.

## Dependencies / sequencing

- Operator decision REQUIRED before mechanical sweep; do NOT run option (a) without explicit go-ahead.
- Pre-cutover: this should ship before May-23 to prevent fresh agents picking up the cite plans + chasing dead links.

## References

- Archived issue:
  [`plans/archive/issues/missing_question_docs_orphan_references_2026_05_10.md`](../archive/issues/missing_question_docs_orphan_references_2026_05_10.md)
- Existing active plans the references SHOULD point to:
  - [`plans/active/risk_simulations_limits_alerting_2026_05_10.md`](risk_simulations_limits_alerting_2026_05_10.md)
  - [`plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md`](client_reporting_pnl_attribution_mvp_2026_05_10.md)

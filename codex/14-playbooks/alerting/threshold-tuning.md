---
title: Alerting Threshold Tuning
status: planned
created: 2026-05-07
authoritative_for: How alert thresholds are set, who owns each threshold, when they get reviewed. Avoids the "alert on a number nobody can defend" failure mode that produces noise + alert fatigue.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.plan.md
related:
  - codex/14-playbooks/alerting/alert-code-taxonomy.md
  - codex/14-playbooks/alerting/operator-playbook.md
  - codex/14-playbooks/alerting/rehearsal-procedure.md
---

# Alerting Threshold Tuning

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from the alerting-service plan. Body to be
> filled in as alerting-service ships its first per-archetype thresholds.

## Purpose

Every alert threshold answers a question: "above what value does this become important?" Wrong thresholds either page
the operator on noise (alert fatigue) or fail to page on a real incident. This doc is the SSOT for how thresholds get
set, who owns them, and when they get re-tuned.

## Scope

- Threshold-bearing AlertCodes — heartbeat windows, fill-quality drift, position-vs-limit ratios, p&l drawdown,
  custody-balance gaps, oracle-price-deviation thresholds.
- Owner assignment — every threshold has a named owner.
- Review cadence — quarterly default; ad-hoc after every false-positive cluster.
- Excluded: threshold-free codes (e.g. service-down, kill-switch-flipped — those don't have a numeric threshold).

## Outline (planned sections)

1. **Where thresholds live** — UAC `ALERT_THRESHOLDS` dict keyed by `AlertCode` + scope (`asset_group`, `archetype`,
   `venue`).
2. **Per-threshold metadata** — value, units, owner, set-date, evidence (link to historical data showing the value
   captures the right tail), last-review-date.
3. **Setting a new threshold** — start with the percentile of healthy historical observation (e.g. p99); validate via
   backtest replay; deploy in WARNING-only mode for one week; promote to PAGE.
4. **Re-tuning** — false-positive cluster triggers re-tune; owner reviews + provides evidence of the new value's
   appropriateness; updated in same PR as enum change.
5. **Per-archetype overrides** — `carry_staked_basis` heartbeat threshold may differ from `leveraged_funding_arb`;
   override syntax in UAC.
6. **Backtest / replay tooling** — how to replay historical events through proposed thresholds + count true/false
   positives.
7. **Alert-fatigue ratchet** — if a code generates >N false-positives per quarter, automatic threshold-review trigger.

## Cross-references

- **Plan(s) implementing this:** [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.plan.md).
- **Related codex SSOTs:** [`alert-code-taxonomy`](./alert-code-taxonomy.md), [`operator-playbook`](./operator-playbook.md), [`rehearsal-procedure`](./rehearsal-procedure.md).
- **Code:** UAC `unified_api_contracts.canonical.crosscutting.alerting.ALERT_THRESHOLDS` (TBD).

## Open questions

- Do we ship a "shadow" alerting mode (compute the threshold, log the would-be alert, don't page) for new codes? Yes
  recommended — first week of every new code.
- How do we A/B-test threshold changes safely in production? (recommend: shadow new threshold + diff the would-be
  alerts vs current production for one week)
- Should owners be individuals or rotations? (recommend: rotations for cross-archetype, individual for single-strategy)

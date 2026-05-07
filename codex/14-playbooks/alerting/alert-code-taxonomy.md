---
title: Alert Code Taxonomy
status: planned
created: 2026-05-07
authoritative_for: The UAC `AlertCode` StrEnum SSOT — the closed set of alert codes the alerting-service may emit. Each code maps to a stable operator runbook entry, threshold owner, and severity. Placeholder; the real taxonomy ships in alerting-service Phase 1.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.plan.md
related:
  - codex/14-playbooks/alerting/operator-playbook.md
  - codex/14-playbooks/alerting/threshold-tuning.md
  - codex/05-infrastructure/live-deployment-monitoring.md
---

# Alert Code Taxonomy

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from the alerting-service plan. Body to be
> filled in as alerting-service Phase 1 ships the UAC enum.

## Purpose

Every alert raised by the alerting-service carries a stable, machine-readable `AlertCode`. This doc is the SSOT for
what the closed-set values are, what each means, and which severity tier they fall into. Operator runbooks key off
these codes; threshold tuning is filed against these codes.

## Scope

- The `AlertCode` StrEnum lives in UAC (TBD — likely `unified_api_contracts.canonical.crosscutting.alerting`).
- Severity tiers: `INFO` / `WARNING` / `PAGE` / `KILL_SWITCH`.
- Per-code metadata: short title, description, default severity, runbook link, threshold owner, related plans.
- Excluded: per-instance alert payloads (those carry `AlertCode` + dynamic context).

## Outline (planned sections)

1. **Alert taxonomy categories** — heartbeat / data-pipeline / risk-limit / execution-quality / custody / on-call-
   meta. Each category has a code prefix.
2. **Per-code reference table** — `code, title, severity, category, runbook_link, threshold_owner, introduced_plan,
   first_emitted_at`.
3. **Adding a new code** — process: PR adds enum value + threshold-tuning entry + operator-playbook entry + rehearsal-
   procedure scope add.
4. **Deprecating a code** — process: mark as deprecated for one rehearsal cycle, then remove. No "phantom" codes that
   no longer fire but still appear in dashboards.
5. **Severity escalation rules** — under what conditions does a `WARNING` auto-escalate to `PAGE`? (e.g. 3 in 15 min)
6. **Code-naming convention** — `{CATEGORY}_{CONDITION}_{DETAIL}`, ALL_CAPS, max 64 chars.

## Cross-references

- **Plan(s) implementing this:** [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.plan.md).
- **Related codex SSOTs:** [`operator-playbook`](./operator-playbook.md), [`threshold-tuning`](./threshold-tuning.md), [`live-deployment-monitoring`](../../05-infrastructure/live-deployment-monitoring.md).
- **Code:** UAC `unified_api_contracts.canonical.crosscutting.alerting.AlertCode` (TBD).

## Open questions

- Do we treat data-pipeline alerts (e.g. backfill stalled) as the same severity tier as trading alerts (e.g. risk-limit
  breached)? (recommend: separate categories, different escalation rules)
- Should custody-related alerts (Copper/CEFFU webhook stale) be PAGE-by-default given May-23 live trading scope?
- How do we handle alerts that need different severity per-archetype (e.g. funding-arb stall is PAGE, sports tip-stall
  is WARNING)?

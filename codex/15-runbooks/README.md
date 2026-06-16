---
title: "15-runbooks — live-trading on-call runbooks"
type: codex-section-readme
status: active
created: 2026-05-08
scope: [engineer]
related:
  - codex/14-customer-journeys/README.md
  - codex/16-strategy-playbooks/README.md
  - codex/03-observability/alerting.md
  - codex/04-architecture/instruments-live-architecture.md
  - codex/05-infrastructure/live-deployment-monitoring.md
---

# 15-runbooks

This section is the SSOT for **live-trading on-call runbooks** — the procedures the on-call operator follows when an
alert fires, when a daily T+1 audit surfaces a discrepancy, when a smoke test must be run before promoting a build, or
when a backfill VM has finished and needs sign-off. Every runbook here is **operator-runnable**: it has a clear trigger,
a step-by-step procedure, an explicit done-definition, and (per workspace HARD RULE "Runbook Execution-Owner SSOT") a
declared periodic-execution path so the runbook doesn't silently rot against an evolving codebase.

## What lives here

- **`alerting/`** — Per-alert-code runbooks (kill-switch armed, defi health-factor critical, position drift, preflight
  failed, balance drift, etc.) plus the alerting-vocabulary glossary, PagerDuty escalation policy, threshold- tuning
  procedure, and rehearsal procedure. The SSOT for "the page just fired — what do I do" workflows.
- **`instruments-live/`** — Daily T+1 audit runbook for the instruments-live coverage check (catalog ↔ manifest ↔
  parquet reconciliation). Includes the discrepancy-resolution flow.
- **`smoke-testing-playbook.md`** — Pre-promotion smoke test procedure: which harnesses to run before promoting a build
  to staging or main, expected pass/fail signals, sign-off shape.
- **`backfill-completion-playbook.md`** — Post-backfill sign-off procedure: manifest verification, sample parquet
  inspection, downstream dependency-check trigger, archival of the backfill VM's events stream.

## What does NOT live here

- **Customer-facing flows + onboarding** → [`codex/14-customer-journeys/`](../14-customer-journeys/README.md).
  Investment-management demo, fund-org hierarchy, page-triage, role-based audiences.
- **Domain-specific strategy + infra playbooks** → [`codex/16-strategy-playbooks/`](../16-strategy-playbooks/README.md).
  DeFi venue-collateral runbooks, archetype playbooks (CME-Polymarket arb, etc.), ML lifecycle, infra-spec stage docs.
- **Service-internal observability docs** → [`codex/03-observability/`](../03-observability/README.md). The alerting
  surface here points BACK to runbooks under `15-runbooks/alerting/` for per-alert procedures.
- **Live-deployment infrastructure topology** → [`codex/05-infrastructure/`](../05-infrastructure/README.md).
  `live-deployment-monitoring.md` cites runbooks here; the topology lives there.

## Cross-link conventions

Every runbook in this section MUST:

1. Declare an `execution:` frontmatter block (per workspace HARD RULE) — `owner`, `cadence`, `verifier`,
   `last_executed`. Runbooks without all four fields are review-blocking.
2. Cite the alerting vocabulary in `15-runbooks/alerting/README.md` § "Severity glossary" when assigning severity. Do
   NOT redefine the CRITICAL/HIGH/WARN/INFO axis locally.
3. Reference the live-trading topology in `codex/05-infrastructure/live-deployment-monitoring.md` for any VM /
   service-mesh / event-bus context the runbook touches.
4. If a runbook fires a kill-switch or arm-state, cite the master plan readiness item it relates to (Group F/G of
   `master_to_live_defi_2026_05_23.md`) so the on-call can link the procedure to the May-23 cutover criterion.

## How to add a new runbook

1. Place under the appropriate sub-dir (`alerting/` for per-alert procedures; new sub-dirs are fine for new domains —
   e.g. `treasury/`, `custody/`).
2. Add the frontmatter `execution:` block with all 4 fields populated (placeholder `last_executed: NEVER` is fine for
   one-shots).
3. Cross-link from `codex/00-SSOT-INDEX.md` § runbooks if the runbook is workspace-critical.
4. Add a row to the master plan readiness checklist's "Continuous Verification" column if the runbook backs a May-23
   success criterion.

## History

This section was carved out of the legacy `14-customer-journeys/` directory in 2026-05-08 per
[`plans/active/codex_refactor_2026_05_08.md`](../../plans/active/codex_refactor_2026_05_08.md) Phase E.2 step 2. The
parent dir was renamed to `14-customer-journeys/` and split into three: `14-customer-journeys/` (audience flows),
`15-runbooks/` (this dir, on-call runbooks), `16-strategy-playbooks/` (domain strategy + infra playbooks).

---
scope: [engineer, admin]
last_reviewed: 2026-05-29
---

# Safety Ops Tab

Shipped: 2026-05-23. Plan: `plans/active/deployment_ui_safety_ops_tab_2026_05_23.md` (archived).

## Overview

The Safety Ops tab is a manual-override surface in both `deployment-ui` and `unified-trading-system-ui` (DART cockpit)
that exposes every Layer-0 and Layer-1 recovery action behind a typed-confirm-string gate. It is the "Layer-M"
orthogonal to the 5-layer autonomous recovery stack — an operator can intervene at any layer via this tab. See
`codex/04-architecture/recovery-defence-in-depth-layers.md`.

## Routes

| App                         | Route                              | Status                                  |
| --------------------------- | ---------------------------------- | --------------------------------------- |
| `unified-trading-system-ui` | `app/(routes)/safety-ops/page.tsx` | Shipped ui@a6f3924c                     |
| `deployment-ui`             | mirrored tab (shared components)   | Shipped deployment-ui@39539e8           |
| DART cockpit                | `app/(ops)/safety-ops/` scaffold   | DART ui@01e1bb69 (live wiring deferred) |

## UI structure (4 sections)

1. **Layer-0 Actions** — 10 action buttons; each requires typed-confirm-string before commit
2. **LLM Audit Verdicts** — feed from `GET /safety-ops/recovery-audit-signoffs`
3. **Audit-Ack Queue** — incidents with countdown to SLA breach; `POST /safety-ops/operational-ack`
4. **Incident History** — read-only log

## Layer-0 action buttons (10)

Defined in `unified_api_contracts.canonical.crosscutting.safety_ops.confirm_strings` (closed-set registry mapping
`action_type → required_confirm_string`):

1. Restart Service
2. Restart All Services
3. Cancel Open Orders
4. Close All Positions
5. Pause Strategy
6. Pause All Strategies
7. Enable Safe Mode
8. Force Reconciliation
9. Trigger Drawdown Check
10. Emergency Liquidate

Each button calls `POST /incidents/manual-action` (`alerting-service/gateway/manual_action_endpoint.py`) with
`provenance=MANUAL_OPERATOR`.

## Auth roles

| Role                 | Access                 | Holders                       |
| -------------------- | ---------------------- | ----------------------------- |
| `safety-ops:read`    | View all panels        | All operators                 |
| `safety-ops:execute` | Commit Layer-0 actions | Ikenna + Harsh + founder only |

## Backend

- Manual action endpoint: `alerting-service/gateway/manual_action_endpoint.py` (ships alerting-service@e5c8084)
- Layer-0 scripts: `deployment-service/scripts/recovery/` (10 scripts, ds@21cd67b)
- LLM agent template: `agent-orchestrator/agents/recovery-audit.md` (ao@efe9312; 60s poll, closed-set Layer-1.5
  authority)

## Playwright evidence

- deployment-ui mirror: pw:L2 ✓ (10/10 e2e + 38/38 smoke) | regression: `tests/e2e/safety-ops-deployment-ui.spec.ts`
- DART skeleton: `tests/e2e/safety-ops.spec.ts` (4 tests, mocked backend) — live wiring pending Phase 3

## Anti-patterns

- One-click destructive actions — every Layer-0 button requires typed-confirm-string
- All-operator execute access — `safety-ops:execute` is restricted (Ikenna/Harsh/founder only)
- Calling Layer-0 scripts directly from UI — always route through the manual-action endpoint with
  `provenance=MANUAL_OPERATOR`

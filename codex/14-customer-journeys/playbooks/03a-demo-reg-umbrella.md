---
doc_type: codex-ssot
title: "Playbook 3a — Demo: Regulatory Umbrella flavour"
summary:
  "pb3a implementation — Reg Umbrella demo walkthrough; reporting-only entitlements (all other services
  padlocked-visible, not hidden), Pooled/SMA picker → fund → per-client API-key creation → 12 report tabs; UI-identical
  to pb3b, differs only in sales narrative."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, playbook, demo, reg-umbrella, reporting, entitlements]
related:
  [
    /codex/14-customer-journeys/playbooks/03-warm-prospect-demo.md,
    /codex/14-customer-journeys/playbooks/03b-demo-im.md,
    /codex/14-customer-journeys/playbooks/03c-demo-dart.md,
    /codex/14-customer-journeys/playbooks/02c-research-regulatory.md,
    ../playbook-concepts/client-reporting.md,
  ]
created: 2026-04-19
authoritative_for: [pb3a Regulatory Umbrella demo playbook implementation]
referenced_by:
  [
    /codex/14-customer-journeys/experience/regulatory-demo.md,
    /codex/14-customer-journeys/playbook-concepts/client-reporting.md,
    /codex/14-customer-journeys/playbook-concepts/sma-vs-pooled.md,
    /codex/14-customer-journeys/playbooks/02c-research-regulatory.md,
    /codex/14-customer-journeys/playbooks/03-warm-prospect-demo.md,
    /codex/14-customer-journeys/playbooks/03b-demo-im.md,
    /codex/14-customer-journeys/playbooks/03c-demo-dart.md,
    /codex/14-customer-journeys/playbooks/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Playbook 3a — Demo: Regulatory Umbrella flavour

> **Layer:** Implementation. Narrative lives in [experience/regulatory-demo.md](../experience/regulatory-demo.md).

## Who this is for

A warm prospect interested in operating under Odum's FCA umbrella. They've been provisioned a demo account on staging;
the demo is framed around client-reporting because that's where their regulatory filings + investor reporting +
performance reporting come from.

## Pre-req state

- Admin has provisioned an organisation + demo user with **Reg Umbrella flavour entitlements** per
  [../authentication/firebase-staging.md](../authentication/firebase-staging.md)
- Entitlements: `reporting` (required) + optional `investor-relations` for board-level views; other tiers locked
- Prospect has staging credentials

## Canonical click path (walkthrough)

```
/login (Firebase staging, demo creds)
    ↓
/dashboard
    ↓ (services portal — MOST SERVICES LOCKED)
    ├── Data (locked — "upgrade to unlock")
    ├── Research (locked)
    ├── Promote (locked)
    ├── Trading (locked)
    ├── Observe (locked)
    ├── ✅ Reports (unlocked — primary surface)
    └── Admin (locked — internal only)
    ↓
/services/reports/overview
    ↓ (or first step: Pooled vs SMA landing)
    ↓
Pooled-vs-SMA picker
    ↓ (admin can lock one, show both, or force choice)
    ↓
Fund creation flow
    ↓ (name fund, select venues, set capital)
    ↓
Client creation flow (per fund)
    ↓ (name client, generate fresh API keys, optional risk limits)
    ↓
Reports surface — all tabs become visible:
    ├── Overview — high-level P&L
    ├── Performance — performance attribution
    ├── NAV — NAV calculation, share classes
    ├── Invoices — fee invoices
    ├── IBOR — book of record
    ├── Settlement — settlement state
    ├── Reconciliation — position + cash recon
    ├── Regulatory — MiFID II reports, transaction reporting
    ├── Analytics — performance analytics
    ├── Trades — trade blotter
    ├── Executive — executive summary report
    └── Fund Operations — ops dashboard
```

## What the prospect experiences

The demo emphasises:

1. "You get all of this reporting for regulatory + client + investor purposes — we've built the plumbing."
2. The SMA vs Pooled choice — shows the structural impact on reporting
3. Real regulatory event audit (via `/services/observe/event-audit` if also entitled, or via Reports > Regulatory)

## Flavour-specific slicing (entitlements)

```
entitlements: [
  "reporting",           // unlocks /services/reports/*
  "investor-relations",  // optional — unlocks /investor-relations view if relevant
  // NOT granted: "data-*", "execution-*", "ml-*", "strategy-*"
]
```

Locked services render as **tiles with a padlock icon + "Contact Odum to enable this service" CTA** — never hidden. This
preserves the "full catalogue of Odum capabilities" framing for the demo.

**Implementation gap**: current [lib/config/auth.ts](unified-trading-system-ui/lib/config/auth.ts) +
[components/shell/lifecycle-nav.tsx](unified-trading-system-ui/components/shell/lifecycle-nav.tsx) hide unentitled
services. Pb3a requires LOCKED-VISIBLE mode. Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md) →
visibility-slicing implementation.

## Same UI path as pb3b

Structurally identical to pb3b (IM demo). The only difference is the narrative frame the Odum sales contact uses on the
call. Screens, entitlements, and flow are identical. See [03b-demo-im.md](03b-demo-im.md).

## Cross-cutting content

- Pooled vs SMA: [../cross-cutting/sma-vs-pooled.md](../playbook-concepts/sma-vs-pooled.md)
- Client reporting (the core surface): [../cross-cutting/client-reporting.md](../playbook-concepts/client-reporting.md)
- Fund/org/client hierarchy: [../cross-cutting/fund-org-hierarchy.md](../playbook-concepts/fund-org-hierarchy.md)
- Visibility slicing: [../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md)

## Exit state

- **Commits** → becomes real Reg Umbrella client → admin provisions production Firebase user
- **Refines demo** → admin unlocks additional tiers if prospect wants to see more
- **Drops** → admin deactivates demo user

## Test coverage

- Playwright spec: `unified-trading-system-ui/tests/playbooks/03a-reg-umbrella.spec.ts`
- Assertions:
  1. Sign in as `prospect-reg` persona → lands on `/dashboard`
  2. Service tiles show: Reports unlocked, others padlocked
  3. Navigate to `/services/reports/overview` → 200 OK
  4. Navigate to locked service directly (e.g. `/services/trading/overview`) → redirects or shows locked state
  5. Pooled/SMA picker is reachable within reports flow
  6. Fund creation + client creation flows complete (mock)

## Related

- Parent hub: [03-warm-prospect-demo.md](03-warm-prospect-demo.md)
- Sibling (same UI): [03b-demo-im.md](03b-demo-im.md)
- Sibling (different structure): [03c-demo-dart.md](03c-demo-dart.md)
- Research briefing that led here: [02c-research-regulatory.md](02c-research-regulatory.md)

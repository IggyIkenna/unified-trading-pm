---
doc_type: codex-ssot
title: "Playbook 3c — Demo: DART flavour"
summary:
  "pb3c implementation — DART demo with most services unlocked; sequential walkthrough of all four catalogues + research
  → promote → trading → observe; data-pro/strategy/ml/execution entitlements; structurally unlike pb3a/pb3b (no
  reports-only lock, no Pooled/SMA picker)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [customer-journey, playbook, demo, dart, catalogues, entitlements]
related:
  [
    /codex/14-customer-journeys/playbooks/03-warm-prospect-demo.md,
    /codex/14-customer-journeys/playbooks/03a-demo-reg-umbrella.md,
    /codex/14-customer-journeys/playbooks/03b-demo-im.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    ../playbook-concepts/catalogues.md,
  ]
created: 2026-04-19
authoritative_for: [pb3c DART demo playbook implementation]
referenced_by:
  [
    /codex/14-customer-journeys/experience/dart-demo.md,
    /codex/14-customer-journeys/playbooks/02b-research-dart.md,
    /codex/14-customer-journeys/playbooks/03-warm-prospect-demo.md,
    /codex/14-customer-journeys/playbooks/03a-demo-reg-umbrella.md,
    /codex/14-customer-journeys/playbooks/03b-demo-im.md,
    /codex/14-customer-journeys/playbooks/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Playbook 3c — Demo: DART flavour

> **Layer:** Implementation. Narrative lives in [experience/dart-demo.md](../experience/dart-demo.md).

## Who this is for

A warm prospect who wants to build and run their own strategies on Odum infrastructure (or commission Odum to build
strategies for them). The demo shows them the full DART (Data Analytics, Research & Trading) surface — four catalogues +
research + trading + observation.

## Pre-req state

- Admin has provisioned an organisation + demo user with **DART flavour entitlements** per
  [../authentication/firebase-staging.md](../authentication/firebase-staging.md)
- Entitlements: `data-pro` + `strategy-full` + `ml-full` + `execution-full` + trading tiers (basic or premium per demo
  depth); `reporting` optional
- Prospect has staging credentials

## Canonical click path (walkthrough)

```
/login (Firebase staging, demo creds)
    ↓
/dashboard
    ↓ (services portal — MOST SERVICES UNLOCKED)
    ├── ✅ Data — unlocked
    ├── ✅ Research — unlocked
    ├── ✅ Promote — unlocked
    ├── ✅ Trading — unlocked
    ├── ✅ Observe — unlocked
    ├── Reports — optional
    └── Admin — locked (internal only)
    ↓
The demo walks each catalogue in sequence:

1. Data Catalogue → /services/data/overview
   ├── instruments
   ├── venues
   ├── coverage
   ├── gaps (merged from gaps/completeness/missing)
   └── processing status

2. Strategy Catalogue → /services/strategy-catalogue
   ├── coverage matrix (archetype × category × instrument type)
   ├── by-combination filter
   ├── blocked (grouped by BL-* codes)
   └── per-archetype detail

3. ML Model Catalogue → /services/research/ml (or future unified surface)
   ├── registry
   ├── training runs
   ├── governance
   └── monitoring

4. Execution Algo Catalogue → /services/execution/overview (or future unified surface)
   ├── algo library
   ├── per-venue applicability
   ├── benchmarks
   └── TCA (currently broken — see triage)

5. Research iteration → /services/research/overview
   ├── quant
   ├── signals
   ├── features
   └── strategy (backtests, candidates)

6. Promote lifecycle → /services/promote/pipeline
   ├── data-validation
   ├── model-assessment
   ├── risk-stress
   ├── execution-readiness
   ├── paper-trading
   ├── champion
   ├── capital-allocation
   └── governance

7. Trading → /services/trading/terminal
   ├── terminal (live trading view)
   ├── positions + trades
   ├── orders
   ├── markets
   ├── pnl
   └── risk

8. Observation → /services/observe/health
   ├── health (service status)
   ├── alerts
   ├── strategy-health
   ├── reconciliation
   └── event-audit
```

> **[DELTA 2026-05-22]** **Current state:** ML Model Catalogue and Execution Algo Catalogue surface under
> `/services/research/ml` and `/services/execution/overview` respectively — separate routes, not a unified catalogue
> surface. TCA on the Execution Algo Catalogue is currently broken (triage-listed). **Planned delta:** Consolidation
> into a unified catalogue surface tracked in `/codex/14-customer-journeys/roadmap/next-waves.md`. **Target:**
> post-cutover UI unification phase.

## What the prospect experiences

The demo emphasises:

1. "All four catalogues are SSOT — same data, same structure, different lenses."
2. "Move strategies between catalogue states: PUBLIC → IM_RESERVED → CLIENT_EXCLUSIVE → RETIRED." (See
   [../cross-cutting/catalogue-strategy.md](../playbook-concepts/catalogue-strategy.md).)
3. "Your IP stays yours — Odum IP stays ours — enforced via catalogue lock states."
4. "Research → Promote → Trade is one pipeline, not separate tools."
5. "Observation is real-time — anything you run goes to the same observability surface."

## Flavour-specific slicing

```
entitlements: [
  "data-pro",
  "strategy-full",
  "ml-full",
  "execution-full",
  { domain: "trading-common", tier: "premium" },
  { domain: "trading-defi", tier: "premium" },
  // etc per demo scope
]
```

Within each catalogue, individual entries are further sliced by `lock_state` + `maturity` — the demo shows PUBLIC +
CODE_AUDITED+ entries by default, with admin-only ability to reveal IM_RESERVED or CODE_NOT_WRITTEN placeholders. See
[../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md).

## Cross-cutting content

- Four catalogues umbrella: [../cross-cutting/catalogues.md](../playbook-concepts/catalogues.md)
- Per-catalogue docs: [../cross-cutting/catalogue-data.md](../playbook-concepts/catalogue-data.md),
  [catalogue-strategy.md](../playbook-concepts/catalogue-strategy.md),
  [catalogue-ml-model.md](../playbook-concepts/catalogue-ml-model.md),
  [catalogue-execution-algo.md](../playbook-concepts/catalogue-execution-algo.md)
- Visibility slicing: [../cross-cutting/visibility-slicing.md](../playbook-concepts/visibility-slicing.md)

## Differences from pb3a/pb3b

- Structurally different: DART shows the full 4-catalogue surface, not just client-reporting
- No Pooled-vs-SMA picker as part of the core flow (those are IM/Reg concepts)
- Client-reporting is optional/deprioritised here (DART clients run their own strategies, not allocate to Odum's)

## Exit state

- **Commits** → becomes real DART client → admin provisions production Firebase user with DART entitlements
- **Refines demo** → admin adjusts which catalogue entries are visible
- **Drops** → admin deactivates demo user

## Test coverage

- Playwright spec: `unified-trading-system-ui/tests/playbooks/03c-dart.spec.ts`
- Assertions:
  1. Sign in as `prospect-dart` persona → lands on `/dashboard`
  2. Service tiles show: Data, Research, Promote, Trading, Observe unlocked; Admin locked
  3. Navigate each of the 4 catalogues → each renders with entries filtered per entitlement
  4. Strategy-catalogue coverage matrix renders the expected archetypes
  5. DART trading terminal loads (with mock market data in staging)

## Related

- Parent hub: [03-warm-prospect-demo.md](03-warm-prospect-demo.md)
- Sibling (structurally different): [03a-demo-reg-umbrella.md](03a-demo-reg-umbrella.md),
  [03b-demo-im.md](03b-demo-im.md)
- Research briefing that led here: [02b-research-dart.md](02b-research-dart.md)
- DeFi-specific demo flows:
  [../../../plans/archive/defi_demo_e2e_workflow_2026_03_30.plan.md](../../../plans/archive/defi_demo_e2e_workflow_2026_03_30.plan.md)

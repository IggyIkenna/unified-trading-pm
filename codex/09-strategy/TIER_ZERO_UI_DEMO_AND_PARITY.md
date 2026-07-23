---
doc_type: codex-ssot
title: Tier 0 UI demo — strategy parity and documentation map
summary: >-
  Aligns the three "layers of truth" for the Tier 0 UI demo — Codex strategy prose, UI mock fixtures
  (`lib/strategy-registry.ts` / `*-mock-data.ts`), and backend/OpenAPI (T1+) — so field names and enums stay consistent;
  specifies cross-strategy UX expectations (shared facet filters, multi-venue first-class view model) and the Tier
  0-vs-T1+ no-feature-creep rule. Points to the UI playbook `END_TO_END_STATIC_TIER_ZERO_TESTING.md` for the P0 journeys
  + institutional demo bar.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, ui, tier-zero, mock-data, uac, parity]
related:
  [
    /codex/09-strategy/strategy-summary.md,
    architecture-v2/README.md,
    _archived_pre_v2/STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md,
  ]
created: 2026-03-27
authoritative_for: [tier 0 UI demo strategy parity (codex↔UI-mock↔OpenAPI truth-layer alignment)]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/_archived_pre_v2/STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md,
    /codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md,
    /codex/14-customer-journeys/_ssot-rules/12-service-family-scope-rules.md,
    /codex/14-customer-journeys/shared-core/same-system-principle.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Tier 0 UI demo — strategy parity and documentation map

**Audience:** Engineers and PM aligning **Codex strategy prose**, **UI mock fixtures**, and **future API tiers**.

**UI playbook (repeatable testing):**
[`END_TO_END_STATIC_TIER_ZERO_TESTING.md`](../../unified-trading-system-ui/docs/END_TO_END_STATIC_TIER_ZERO_TESTING.md)
(path from workspace root: `unified-trading-system-ui/docs/END_TO_END_STATIC_TIER_ZERO_TESTING.md`)

**Runtime tier model:** `unified-trading-pm/plans/active/end-to-end-testing/system-tiers.md`

**Institutional demo bar (workflows, subscriptions, admin approvals, API handoff):** UI playbook §1b —
`unified-trading-system-ui/docs/END_TO_END_STATIC_TIER_ZERO_TESTING.md` (“Institutional-grade demo target”).

**Derived capability lattice (org hierarchy, pre-trade, order lifecycle, MD entitlements, post-trade, audit, etc.):**
same file, §1b subsection **“Derived capability lattice”** — use when Codex or API specs must cover _what a desk does_,
not only routes the user named.

**P0 journeys** (provision → approve, create strategy/venue, backtest → results, book-trade matrix, recon, alerts ack,
**client IM onboarding + document uploads + tier/product scope**) **+ BR/Citadel honest bar:** UI playbook §1 **P0
table** and §1b **“BlackRock / Citadel–grade demo: honest bar”** + **“Client onboarding, documents, and IM / regulatory
umbrella”**.

---

## 1. Three layers of “truth”

| Layer                                                                        | Role                                              |
| ---------------------------------------------------------------------------- | ------------------------------------------------- |
| **Codex** (`09-strategy/README.md`, per-strategy docs)                       | Human SSOT for intent, constraints, lifecycle     |
| **UI mock** (`lib/strategy-registry.ts`, `lib/*-mock-data.ts`, mock handler) | Demonstrable behaviour in **Tier 0** (no backend) |
| **Backend / OpenAPI** (T1+)                                                  | Contractual SSOT for field names and enums        |

**Rule:** When Codex or `strategy-manifest.json` changes, update UI fixtures and the **browser handbook**
(`unified-trading-system-ui/docs/MOCK_STATIC_BROWSER_AGENT_HANDBOOK.md`) in the same effort (see
`MOCK_STATIC_EVALUATION_SPEC.md`).

---

## 2. Cross-strategy UX expectations

For **every** strategy row in the registry, the UI should eventually support:

- **Facet filters** shared across strategies: asset class, venues, execution mode, testing stage, subscription tier.
- **Detail surface:** parameters, data dependencies, risk hooks, PnL attribution slice — see handbook tables.
- **Lane context:** same strategy visible from **Research** (candidates, backtests) and **Trading** (live state) without
  contradictory labels.

**Multi-venue comparison** (prediction markets, sports): treat as a **first-class view model** — one normalized row per
(event, instrument, side) with **venue** as a dimension, not separate siloed pages. Mock data should use **UAC-aligned**
venue strings where possible (`ui-reference-data.json` generators in PM).

---

## 3. Tier 0 vs T1+ (no feature creep)

Tier 0 may **simulate** latency, fills, and entitlements in-process. Tier 1+ must serve the **same shapes** from HTTP
APIs. If Tier 0 invents a field not in OpenAPI, either add it to the contract or drop it from mock.

---

## 4. Links

- **Catalog vs code exports:** `STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md`
- **Browser agent evaluation:** `../unified-trading-system-ui/docs/MOCK_STATIC_BROWSER_AGENT_HANDBOOK.md`
- **Machine registries for dropdowns:** `unified-trading-pm/docs/ui-alignment-ssot.md`

---
doc_type: codex-ssot
title: Glossary
summary:
  "Single-definition-per-term glossary for the customer-journeys domain — Odum services (DART, IM, Reg Umbrella), client
  structure (org/fund/client, Pooled vs SMA), the four catalogues, visibility/access tiers, playbook families
  (pb1/pb2/pb3), and environments."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, instruments-service, market-tick-data-service, strategy-service, unified-trading-library]
scope: [sales, prospect, investor]
tags: [glossary, customer-journey, dart, sales, prospect, catalogue]
related:
  [/codex/14-customer-journeys/audiences-and-journeys.md, /codex/14-customer-journeys/information-architecture.md]
created: 2026-04-19
authoritative_for: [customer-journeys glossary terms (org/fund/client, four catalogues, playbook families)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/_ssot-rules/09-internal-commercial-oneliners.md,
    /codex/14-customer-journeys/audiences-and-journeys.md,
    /codex/14-customer-journeys/information-architecture.md,
    /codex/14-customer-journeys/playbooks/README.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
    codex/GLOSSARY.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Glossary

Single definition per term. Any doc in this directory (or elsewhere in codex) referencing one of these terms should link
here rather than redefine. If a term is missing, add it.

## Odum services

- **DART** — Data Analytics, Research & Trading. The trade name for the family of services covering Data Catalogue,
  Strategy Catalogue, ML Model Catalogue, Execution Algo Catalogue, Research, Trading, and Observation. First mention in
  any public-facing doc should expand the acronym: "Data Analytics, Research & Trading (DART)". Thereafter use DART.
  Never use "DRT".
- **IM (Investment Management)** — Odum-run systematic strategies allocated to client capital, operated under Odum's FCA
  umbrella with regulated reporting, oversight, and allocation process.
- **Regulatory Umbrella / Coverage** — FCA-regulated structure under which third-party firms can operate their own
  regulated activity without direct FCA authorisation. Odum's permissions cover their activities. Compliance, MLRO,
  supervision, and reporting are provided by Odum.

## Client structure

- **Organisation (org)** — The top-level container for a client relationship. Maps to a firm (Alpha Capital, Beta Fund,
  etc.), NOT a person. User provisioning happens at the org level in user-management-ui; entitlements roll down to users
  in that org.
- **Fund** — A portfolio effectively, holding one or more clients depending on structure (see Pooled vs SMA). Configured
  with strategies, venues, capital allocations, and risk limits.
- **Client** — An entity under a fund that has its own positions, balances, fresh API keys (per client, never shared),
  and optionally own risk limits. A client can be the org itself, a share class, or a Separately Managed Account holder.
- **Pooled** — Fund structure where ONE fund holds MULTIPLE clients as share classes. The fund has a single set of
  positions; client economics differ only at NAV calculation / fee / allocation level. Simpler operationally.
- **SMA (Separately Managed Account)** — Fund structure where EACH client has their OWN fund. Each SMA fund runs its own
  positions, its own venues, its own API keys, independently of other SMAs. Cleaner isolation; more operational cost.

## Catalogues

The Odum platform has **four catalogues**, each an SSOT in service code, UAC, and UI. See
[cross-cutting/catalogues.md](playbook-concepts/catalogues.md) for the umbrella pattern.

- **Data Catalogue** — Instruments × venues × data types × availability. SSOT in `instruments-service` +
  `market-tick-data-service` availability manifest + UAC capability declarations.
- **Strategy Catalogue** — Archetypes × categories × instrument types. Locked via `StrategyAvailabilityRegistry`
  (lock_state: PUBLIC / IM_RESERVED / CLIENT_EXCLUSIVE / RETIRED × maturity: CODE_NOT_WRITTEN → LIVE_ALLOCATED). SSOT in
  `strategy-service/engine/strategies/v2/archetype_build_registry.py` + UAC strategy_availability.
- **ML Model Catalogue** — Model families × training runs × registry entries × promotion state. SSOT in
  `unified-trading-library/ml/` + strategy-service model registry.
- **Execution Algo Catalogue** — Execution algorithm library × per-venue applicability × benchmarks. SSOT in
  `execution-service/algo_library/`.

## Visibility & access

- **Admin login** — Sees everything across all services, all catalogues, all dimensions. No slicing. Entitlements =
  `["*"]`. Used by Odum-internal admin and ops roles, and by demo-provisioning flows.
- **Demo login** — Sliced to what we want to show the prospect during walkthrough. Uses staging Firebase auth.
  Entitlements curated per prospect profile (IM / DART / Reg Umbrella flavour).
- **Prod login** — Sliced to what the paying client has entitlements for. Uses production Firebase auth. Entitlements
  set at onboarding and updated via user-management-ui.
- **Light auth** — Username + password gate (not Firebase) protecting the `/briefings/*` section. Lightweight, rotates
  per prospect, defeated-but-not-crackable security model. Not for production data access.

## Playbook families

- **pb1 / Marketing pre-first-call** — Public homepage + service-category pages + briefings teaser. No auth required
  beyond the optional briefings gate.
- **pb2 / Deep Dive** (formerly "Research & Documentation") — Light-auth-gated section covering six briefing pillars
  (DART Start Here / DART Signals-In / DART Full / Odum Signals / IM / Regulatory Umbrella) plus developer docs, founder
  long-form, and FAQ. Primary access path is the brief questionnaire embedded inline on the lock screen (since
  2026-04-25) — submit auto-activates the session and emails the access code. Secondary path is the "I already have a
  code" disclosure for warm hand-offs.
- **pb3 / Warm-prospect demo** — Demo account on staging Firebase. Three flavours: pb3a Reg Umbrella, pb3b IM, pb3c
  DART. Flavours pb3a and pb3b share the same UI walkthrough (client-reporting surface, SMA-vs-Pooled picker) and differ
  only in narrative.

## Environments

- **Local dev** — `localhost:3100` (T0, UI-only) / `localhost:3000` (T1/T2, with API gateways). Demo auth default;
  Firebase optional. No real API backends (mock mode).
- **Staging** — `odum-research.co.uk`. Demo-grade Firebase project (isolated from production). Used for prospect demos
  and internal development.
- **Production** — `odum-research.com`. Real Firebase project `central-element-323112`. Real clients, real capital, real
  reporting.

## Briefings

The `/briefings` section of the public UI — a post-first-call deep-briefing hub split into three pillars (IM, DART,
Regulatory Umbrella). Gated by light auth. Access is given to prospects after a first sales call as deeper-dive
material.

## Investor Relations (IR)

A separate section of the UI (`/investor-relations/*`) containing presentations (board / plan / IM / platform /
regulatory / disaster recovery) intended for investors and advisors in Odum itself — NOT for prospects. See
[cross-cutting/investor-relations.md](playbook-concepts/investor-relations.md).

## Related codex

- Glossary for strategy concepts: [../GLOSSARY.md](../GLOSSARY.md)
- Strategy maturity and lock state:
  [/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md](/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
- Share class architecture:
  [/codex/04-architecture/share-class-architecture.md](/codex/04-architecture/share-class-architecture.md)

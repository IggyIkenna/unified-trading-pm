---
doc_type: codex-ssot
title: UI Architecture — Unified Trading System
summary:
  SSOT entry point for UI architecture — the two active UIs (unified-trading-system-ui:5173, deployment-ui:5183), the
  archived split-UI inventory, the where-to-find-what index, and the architectural principles (two-UIs-only,
  API-routes-SSOT-in-service-repos, ports in ui-api-mapping.json).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [client-reporting-api, deployment-api, deployment-ui, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, infrastructure, consolidation, deployment]
related:
  [
    /codex/05-infrastructure/ui-functionality-requirements.md,
    /codex/05-infrastructure/ui-dependency-matrix.md,
    /codex/05-infrastructure/deployment-ui-architecture.md,
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
  ]
created: 2026-05-13
authoritative_for: [UI architecture SSOT entry point (active UI surface)]
referenced_by:
  [
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
    /codex/05-infrastructure/ui-dependency-matrix.md,
    /codex/05-infrastructure/ui-functionality-requirements.md,
    /codex/05-infrastructure/ui-setup-checklist.md,
  ]
owner:
last_reviewed: 2026-05-13
code_refs:
supersedes: [ui-functionality-requirements.md, ui-dependency-matrix.md]
---

# UI Architecture — Unified Trading System

**Purpose:** SSOT entry point for UI architecture across the workspace. Consolidates the prior
`ui-functionality-requirements.md` (screens, features, user roles) and `ui-dependency-matrix.md` (API wiring, ports,
repo registry) — both flagged 2026-03-24 with heavy overlap. This doc is the navigation entry; the two source docs
remain for full detail until their content fully migrates here.

**Status:** Consolidated 2026-05-13 by Slot 8 per
[`codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md`](../../plans/archive/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md)
Sweep 2 (UI-17 finding).

---

## Active product surface (2026-05 — 2 UIs)

Per the workspace-manifest 2026-03 split-UI consolidation:

| UI                              | Primary purpose                                      | Port       | Backend                                                        |
| ------------------------------- | ---------------------------------------------------- | ---------- | -------------------------------------------------------------- |
| **`unified-trading-system-ui`** | Consolidated trading, reporting, admin, domain flows | 5173 (dev) | Multi-API gateway (deployment-api, client-reporting-api, etc.) |
| **`deployment-ui`**             | Deployment orchestration                             | 5183 (dev) | `deployment-api` (port 8004)                                   |

**ARCHIVED (reference only):** former split UIs (`strategy-ui`, `live-health-monitor-ui`, `batch-audit-ui`,
`client-reporting-ui`, etc.) live under workspace-root `archive/README.md` — **not** in `workspace-manifest.json`
repositories.

---

## Where to find what

| If you want…                                                 | Read                                                                                 |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| **Screens / features / user roles / consolidation guidance** | [`ui-functionality-requirements.md`](./ui-functionality-requirements.md) (404 lines) |
| **API wiring / ports / repo registry / dependency matrix**   | [`ui-dependency-matrix.md`](./ui-dependency-matrix.md) (218 lines)                   |
| **Deployment-ui specifics**                                  | [`deployment-ui-architecture.md`](./deployment-ui-architecture.md)                   |
| **Runtime tiers / dev startup**                              | [`runtime-tiers-and-deployment.md`](./runtime-tiers-and-deployment.md)               |
| **Active UI/API port pairings (live)**                       | `unified-trading-pm/scripts/dev/ui-api-mapping.json`                                 |
| **Repo registry (canonical)**                                | `unified-trading-pm/workspace-manifest.json`                                         |

---

## Architectural principles

1. **Two active UIs only.** Resist splitting; consolidation 2026-03 removed 6+ legacy UIs.
2. **API routes SSOT is in service repos**, not duplicated in UI docs — e.g. `deployment-api/api/routes/` is
   authoritative for deployment-api endpoints.
3. **Port assignments are codified** in `unified-trading-pm/scripts/dev/ui-api-mapping.json` — never inline UI ports in
   code.
4. **Connector-status / health-page contract**: deployment-ui health page probes a closed set of connectors (see
   [`deployment-ui-architecture.md`](./deployment-ui-architecture.md) for the contract).

---

## Migration plan (future cleanup)

Full merge of the two source docs into this file is deferred. Until then, this file serves as the SSOT entry point with
clear cross-refs to the source docs. Follow-up tracked in:

- `plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` Sweep 2
- Successor cycle pulls source-doc unique content into named sections here.

## Changelog

- **2026-05-13** — Created as consolidated entry point. Source docs (`ui-functionality-requirements.md` +
  `ui-dependency-matrix.md`) tagged `SUPERSEDED BY ui-architecture.md` with cross-links.

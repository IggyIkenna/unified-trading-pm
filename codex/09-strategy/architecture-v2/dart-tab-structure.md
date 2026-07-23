---
doc_type: codex-ssot
title: DART Tab Structure — Per-Persona SSOT
summary:
  Per-persona SSOT for the DART UI shape — the 8→4 lifecycle-stage collapse, the DART sub-tab catalogue under
  /services/trading/*, the per-persona visible/locked/hidden lifecycle + sub-tab matrices, and the strategy-param-edit
  version-bump modal enforcing batch=live parity.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-ui, strategy-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, dart, ui, catalogue]
related:
  [
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
    /codex/09-strategy/architecture-v2/restriction-policy.md,
    /codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md,
  ]
created: 2026-04-21
authoritative_for: [DART per-persona tab structure and sub-tab visibility]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/architecture-v2/admin-registry-api.md,
    /codex/09-strategy/architecture-v2/dart-exclusive-research-fork.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
  ]
owner:
last_reviewed:
code_refs:
---

# DART Tab Structure — Per-Persona SSOT

Status: **canonical** — source of truth for UI lifecycle-nav shape and DART sub-tab visibility. All UI implementations
must mirror this document; drift is a bug.

Parent plan: `plans/archive/ui_unification_v2_sanitisation_2026_04_20.plan.md` (Phase 11).

Cross-refs:

- `codex/14-customer-journeys/` — per-audience playbooks. Each playbook declares which DART tabs its persona sees.
- `/codex/09-strategy/architecture-v2/restriction-policy.md` — default visibility for strategy cells per persona.
- `/codex/09-strategy/architecture-v2/dashboard-services-grid.md` — **sibling** 5-tile product-axis model for
  `/dashboard`. Dashboard tile sub-route chips are the dashboard-side projection of the DART sub-tab catalog below;
  persona-id × DART sub-tab visibility is the union of the DART dropdown in lifecycle-nav AND the DART tile chip row on
  `/dashboard`.
- `unified-trading-system-ui/lib/auth/persona-lifecycle-shape.ts` — runtime implementation of the shape table below.
- `unified-trading-system-ui/lib/auth/persona-dashboard-shape.ts` — runtime implementation of the dashboard 5-tile
  visibility (sibling to the above; see dashboard-services-grid.md).

---

## 1. Lifecycle collapse (8 → 4)

The authenticated shell historically exposed 8 lifecycle stages
(`acquire / build / promote / run / execute / observe / manage / report`). After 2026-04-20 this collapses to **4
user-visible stages**:

| Stage     | Label    | Audience                        | Notes                                                                                                                                                             |
| --------- | -------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `acquire` | Data     | admin + internal only           | Hidden from all client personas until DataStatusTab integration matures (see `p11-data-internal-only`). Mirrors `deployment-ui/src/components/DataStatusTab.tsx`. |
| `run`     | **DART** | admin + internal + DART clients | Absorbs Research + Promote + Run + Execute + Observe + Deployment/Config. Renamed from "Trading" per user directive 2026-04-20.                                   |
| `manage`  | Manage   | admin + internal + IM + Reg     | Clients, mandates, fees, compliance.                                                                                                                              |
| `report`  | Reports  | everyone with `reporting`       | P&L, settlement, reconciliation, invoices, regulatory reports.                                                                                                    |

The internal `LifecycleStage` TypeScript union (`build`, `promote`, `execute`, `observe`) is retained in the type system
so existing route-mapping code keeps compiling without a cross-repo break. Those stages are **hidden from the nav** via
`persona-lifecycle-shape.ts` (`hidden` entries) and their destinations re-surface as DART sub-tabs. See
`p11-lifecycle-stages-collapse` for the migration rule.

## 2. DART sub-tab catalogue

All DART sub-tabs live under `/services/trading/*` (path not renamed — the `trading` prefix is a historical URL, not a
user-visible label). The label "DART" is rendered in every nav surface. Sub-tab identity is stable across personas;
visibility is the axis that varies.

| Sub-tab id         | Label                | Route                                           | Entitlements                           | Notes                                                                                                                                      |
| ------------------ | -------------------- | ----------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `research`         | Research             | `/services/research/overview`                   | `strategy-full` or `ml-full`           | Folded in from former Build stage.                                                                                                         |
| `promote`          | Promote              | `/services/promote/pipeline`                    | `strategy-full` or `ml-full`           | Folded in from former Promote stage.                                                                                                       |
| `strategy-config`  | Strategy Config      | `/services/trading/strategies/[slot]/config`    | `strategy-full` + `ml-full`            | NEW — confirmers / ML / execution-backtest / strategy-params. Gate: `strategy-full` **and** `ml-full`. Not visible to Signals-In personas. |
| `execution-config` | Execution Config     | `/services/trading/deployment`                  | `strategy-full`                        | NEW — runtime profile, chaos controller, kill-switch. Cross-links to deployment-ui.                                                        |
| `terminal`         | Terminal             | `/services/trading/terminal`                    | `execution-basic` or `execution-full`  | REPOSITIONED — primary view is Analytics + Reconciliation; Manual Execution is a collapsed secondary section with emergency-use banner.    |
| `signal-intake`    | Signal Intake        | `/services/signals/dashboard`                   | `execution-full` (Signals-In) or admin | Inbound signal webhooks for DART Signals-In clients. Also visible to admin for cross-client observation.                                   |
| `observe`          | Observe              | `/services/observe/*`                           | `execution-basic` or `execution-full`  | Risk / Alerts / Health / Strategy Health / live PnL — folded in from former Observe stage. Read-only for Regulatory Umbrella personas.     |
| `deployment`       | Deployment           | `/services/trading/deployment`                  | admin or `strategy-full`               | Lightweight runtime view; deep ops links out to deployment-ui.                                                                             |
| `reports-sub`      | Reports (embedded)   | `/services/reports/overview?embedded=1`         | `reporting`                            | DART-embedded reports view for quick drill-down without leaving DART. Full Reports surface still lives under Reports stage.                |
| `catalogue-truth`  | Catalogue Truthiness | `/services/strategy-catalogue/admin/truthiness` | admin only                             | Admin-only read-through of UAC + live strategy-service registry reconciliation.                                                            |

## 3. Per-persona shape (authoritative)

`visible` = stage/tab renders and is clickable. `locked` = renders with padlock affordance and "Upgrade to unlock" hover
copy. `hidden` = not rendered at all.

### 3.1 Lifecycle stage shape

| Persona                        | `acquire` (Data) | `run` (DART)          | `manage` | `report`               |
| ------------------------------ | ---------------- | --------------------- | -------- | ---------------------- |
| `admin`                        | visible          | visible               | visible  | visible                |
| `internal-trader`              | visible          | visible               | visible  | visible                |
| `im-desk-operator`             | visible          | visible               | visible  | visible                |
| `prospect-dart` (DART Full)    | hidden           | visible               | locked   | visible                |
| `client-full` (DART Full)      | hidden           | visible               | locked   | visible                |
| `prospect-signals-only`        | hidden           | visible (restricted)  | hidden   | visible                |
| `client-im-pooled`             | hidden           | locked                | locked   | visible                |
| `client-im-sma`                | hidden           | locked                | locked   | visible                |
| `prospect-im`                  | hidden           | locked                | locked   | visible                |
| `prospect-im-under-regulatory` | hidden           | locked                | visible  | visible                |
| `client-regulatory`            | hidden           | locked                | visible  | visible                |
| `prospect-regulatory`          | hidden           | locked                | visible  | visible                |
| `prospect-odum-signals`        | hidden           | hidden                | hidden   | visible                |
| `investor` / `advisor`         | hidden           | hidden                | hidden   | hidden (IR-only shell) |
| `elysium-defi` (DeFi demo)     | hidden           | visible (DeFi-scoped) | hidden   | locked                 |
| `prospect-platform`            | hidden           | visible               | hidden   | visible                |
| `client-data-only`             | hidden           | hidden                | hidden   | hidden                 |
| `client-premium`               | hidden           | visible               | hidden   | visible                |

### 3.2 DART sub-tab shape

| Persona                                                 | Research                                     | Promote | Strategy Config | Execution Config | Terminal                       | Signal Intake | Observe             | Deployment | Reports-sub | Catalogue Truthiness |
| ------------------------------------------------------- | -------------------------------------------- | ------- | --------------- | ---------------- | ------------------------------ | ------------- | ------------------- | ---------- | ----------- | -------------------- |
| `admin` / `internal-trader`                             | visible                                      | visible | visible         | visible          | visible                        | visible       | visible             | visible    | visible     | visible              |
| `im-desk-operator`                                      | visible                                      | visible | visible         | visible          | visible                        | visible       | visible             | visible    | visible     | visible              |
| `prospect-dart` / `client-full`                         | visible                                      | visible | visible         | visible          | visible                        | hidden        | visible             | visible    | visible     | hidden               |
| `prospect-signals-only`                                 | hidden                                       | hidden  | **hidden**      | hidden           | visible (analytics+recon only) | visible       | visible (read-only) | hidden     | visible     | hidden               |
| `client-premium` (no ML)                                | hidden                                       | hidden  | hidden          | locked           | visible                        | hidden        | visible             | hidden     | visible     | hidden               |
| `elysium-defi`                                          | hidden                                       | hidden  | hidden          | hidden           | visible (DeFi only)            | hidden        | visible (DeFi only) | hidden     | locked      | hidden               |
| IM / Regulatory / IR / Signals-counterparty / Data-only | (DART stage locked or hidden — sub-tabs N/A) |         |                 |                  |                                |               |                     |            |             |                      |

### 3.3 Gating rule summary

1. `Strategy Config` requires **both** `strategy-full` and `ml-full`. Signals-In personas never see this tab (user
   directive: "If signals, they don't need to configure strategies, because it's their own signals").
2. `Research` + `Promote` collapse into DART but retain the same `strategy-full` or `ml-full` gate they had as peer
   stages.
3. `Terminal` is visible to anyone with any execution entitlement but the UI renders an **emergency-use-only banner**
   above the layout and collapses the Manual Execution section by default. See `p11-trading-terminal-reposition`.
4. `Signal Intake` is visible to DART Signals-In personas as their primary inbound surface and to admin for cross-client
   observation.
5. `Data` + feature-subscription pages are **read-only** for all non-admin personas (user directive: "They're not really
   configuring data and feature subscriptions; that's just given to them. They can view it."). See
   `p11-features-readonly-for-clients`.

## 4. Strategy-param-edit version-bump contract

User edits to live strategy parameters MUST go through a modal with three actions. This is a UX-level enforcement of the
"Batch = Live: Unified Pipeline Architecture" rule in workspace `CLAUDE.md` — ad-hoc param changes break
backtest-to-live parity.

| Action                 | UX                                                                                              | Audit trail                                                                                  |
| ---------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Bump version (v5 → v6) | Recommended path. Green CTA. Opens version-bump dialog seeded with diff summary.                | Audit: `STRATEGY_VERSION_BUMPED` UTL event.                                                  |
| Hot-reload in place    | Red-bordered warning, requires typing `I-ACCEPT-PARITY-BREAK` to confirm. Cites CLAUDE.md rule. | Audit: `STRATEGY_PARAM_AD_HOC_CHANGE` UTL event with persona email + param diff + timestamp. |
| Cancel                 | Neutral button. Dismisses modal without writing.                                                | No audit event.                                                                              |

## 5. Emergency-use banner (Terminal)

Copy (canonical):

> **Analytics + Reconciliation surface.** Manual trading is for emergency use only — routine execution runs through
> strategy schedulers. Family/Archetype picker above scopes all views.

Layout: renders above `app/(platform)/services/trading/terminal/page.tsx` primary content, spans full width, amber-500
background tone. Manual Execution tabs (place / cancel order) render below in a collapsed-by-default section labelled
"Emergency only — audit-logged".

## 6. Open follow-ups (not blocking Phase 11 UI)

- Replace static `persona-lifecycle-shape.ts` with a server-derived shape from the ClientAllocator restriction-profile
  engine once G1.7 ships.
- Wire `Catalogue Truthiness` to live strategy-service registry endpoint (currently a mocked placeholder — see
  `p7-admin-backend-reachability-audit`).
- Replace DART Reports-sub `?embedded=1` param with a dedicated layout variant once Reports moves off the pre-existing
  shell.
- **Plan D — DART exclusive subscription + research fork.** When
  [`dart-exclusive-research-fork.md`](./dart-exclusive-research-fork.md) ships, DART Full personas holding an active
  `dart_exclusive` subscription gain a "Fork for research" action on `<RealityPositionCard>` (opens
  `/services/research/{slot}/fork`). No new DART sub-tab is added — the admin approvals queue lives on the Admin & Ops
  tile as `/admin/strategy-version-approvals`.

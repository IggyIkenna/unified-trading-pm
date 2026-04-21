# Dashboard Services Grid — 5-Tile Product-Axis Model

**Status:** canonical (2026-04-21) **Owner:** UI + Strategy Architecture v2 **SSOT for:**
`unified-trading-system-ui/lib/config/services.ts`, `lib/auth/persona-dashboard-shape.ts`,
`app/(platform)/dashboard/page.tsx` **Cross-refs:** [`dart-tab-structure.md`](./dart-tab-structure.md) ·
[`restriction-policy.md`](./restriction-policy.md) · `codex/14-playbooks/cross-cutting/visibility-slicing.md` ·
`codex/14-playbooks/demo-ops/demo-restriction-profiles.md`

---

## §1 Rationale — Product axis vs lifecycle axis

The `/dashboard` hub and the top-nav answer different questions:

| Surface              | Axis                     | Question it answers           | 2026-04-21 item count |
| -------------------- | ------------------------ | ----------------------------- | --------------------- |
| Top-nav (shell)      | Lifecycle (how you work) | "Where am I in the pipeline?" | 4 stages              |
| /dashboard tile grid | Product (what you own)   | "Which services can I use?"   | 5 tiles               |

They are **NOT** a 1:1 mapping — Data is a lifecycle stage (internal-only, admin Data surfaces) but not a product tile
(Data folds into DART as an admin-only sub-route). Odum Signals is a product tile but not a lifecycle stage (it's a
commercial offering that shares the Run stage with DART).

**Uniformity rule:** same `<ServiceTile>` primitive, same padlock semantics, same chip-row language across all 5 tiles.
Users see one visual grammar, even though the two axes differ.

---

## §2 The 5 tiles

### 2.1 DART

- **Key:** `dart`
- **Label:** DART
- **Description:** Data-Analytics-Research-Trading — terminal, positions, orders, P&L, research, promote, observe,
  config.
- **Primary href:** `/services/trading/overview`
- **Entitlement gate:** any of `execution-basic`, `execution-full`, `strategy-full`, `ml-full`, `data-basic`, `data-pro`
- **Sub-routes (chips):** | Key | Label | Href | Entitlement | | ------------------ | ------------------ |
  ---------------------------------------- | --------------------------------------- | | terminal | Terminal |
  `/services/trading/terminal` | `execution-basic` OR `execution-full` | | research | Research |
  `/services/research/overview` | `strategy-full` OR `ml-full` | | promote | Promote |
  `/services/research/strategy/candidates` | `strategy-full` OR `ml-full` | | observe | Observe |
  `/services/observe/risk` | `execution-basic` OR `execution-full` | | strategy-catalogue | Strategy Catalogue |
  `/services/strategy-catalogue` | `strategy-full` AND `execution-full` | | signal-intake | Signal Intake |
  `/services/signals/dashboard` | `execution-full` (Signals-In clients) | | data | Data | `/services/data/overview` |
  `*` (admin/internal only) |

### 2.2 Odum Signals

- **Key:** `odum-signals`
- **Label:** Odum Signals
- **Description:** External counterparty signal broadcast — webhook/REST delivery, HMAC-signed payloads, rate-limited
  per counterparty.
- **Primary href:** `/services/signals/counterparties`
- **Entitlement gate:** `execution-full`
- **Sub-routes (chips):** Counterparties · Payloads · Emission History · Rate Limits
- **Disambiguation:** This tile is **counterparty-outbound ONLY**. Inbound signal intake for DART Signals-In clients
  lives as the DART · Signal Intake sub-route. Two different audiences, two different surfaces.

### 2.3 Reports

- **Key:** `reports`
- **Label:** Reports
- **Description:** P&L attribution, executive summary, settlement, reconciliation, and regulatory reporting.
- **Primary href:** `/services/reports/overview`
- **Entitlement gate:** `reporting`
- **Sub-routes (chips):** P&L Attribution · Settlement · Reconciliation · Regulatory

### 2.4 Investor Relations

- **Key:** `investor-relations`
- **Label:** Investor Relations
- **Description:** Board presentations, disaster recovery playbook, security posture, operational resilience.
- **Primary href:** `/investor-relations`
- **Entitlement gate:** `investor-relations`
- **Sub-routes (chips):** Board Materials · DR Playbook · Security Posture · IR Briefings

### 2.5 Admin & Ops

- **Key:** `admin`
- **Label:** Admin & Ops
- **Description:** Client onboarding, mandates, fee schedules, user management, deployments, service registry,
  operational monitoring.
- **Primary href:** `/admin`
- **Entitlement gate:** `*` (internal-only)
- **Sub-routes (chips):** Users · Orgs · Deployments · Service Registry · Audit Log

---

## §3 Persona × tile × sub-route visibility matrix

**Legend:** ✓ visible · ○ locked (padlocked + upgrade CTA) · · hidden

Tile-level visibility (dropped the `hidden` column rows for readability — fallback is hidden):

| Persona                      | DART | Odum Signals | Reports | IR  | Admin |
| ---------------------------- | ---- | ------------ | ------- | --- | ----- |
| admin                        | ✓    | ✓            | ✓       | ✓   | ✓     |
| internal-trader              | ✓    | ✓            | ✓       | ·   | ✓     |
| im-desk-operator             | ✓    | ·            | ✓       | ✓   | ✓     |
| client-full                  | ✓    | ·            | ✓       | ·   | ·     |
| client-premium               | ✓    | ·            | ✓       | ·   | ·     |
| client-data-only             | ✓    | ·            | ·       | ·   | ·     |
| prospect-dart                | ✓    | ·            | ○       | ·   | ·     |
| prospect-signals-only        | ✓    | ·            | ✓       | ·   | ·     |
| prospect-odum-signals        | ·    | ✓            | ·       | ·   | ·     |
| client-im-pooled             | ·    | ·            | ✓       | ✓   | ·     |
| client-im-sma                | ·    | ·            | ✓       | ✓   | ·     |
| prospect-im                  | ·    | ·            | ○       | ○   | ·     |
| client-regulatory            | ·    | ·            | ✓       | ·   | ·     |
| prospect-regulatory          | ·    | ·            | ○       | ·   | ·     |
| prospect-im-under-regulatory | ·    | ·            | ○       | ○   | ·     |
| investor                     | ·    | ·            | ·       | ✓   | ·     |
| advisor                      | ·    | ·            | ·       | ✓   | ·     |
| prospect-platform            | ○    | ·            | ·       | ·   | ·     |
| elysium-defi                 | ✓    | ·            | ○       | ·   | ·     |

Sub-route chip visibility is scoped per-tile-per-persona and lives in `lib/auth/persona-dashboard-shape.ts` —
`PERSONA_SUBROUTE_SHAPES`. High-level rules:

- **prospect-signals-only** sees DART tile with ONLY `signal-intake` + `observe` chips (no research / promote /
  strategy-config).
- **client-data-only** sees DART tile with ONLY `strategy-catalogue` chip.
- **prospect-dart** sees DART · Strategy Catalogue unlocked + remaining chips locked (tempt-logic).
- **Regulatory** and **IM** personas never see DART tile sub-routes (tile is hidden).
- **Admin** + **internal-trader** see every chip unlocked.

---

## §4 Filter-strip contract (Phase 4 of plan)

Dashboard renders an optional filter strip above the tile grid that exposes:

- `<FamilyArchetypePicker>` (family × archetype cascade; existing primitive)
- Venue + instrument-type pickers (existing `architecture-v2` primitives)
- "Clear filters" chip

State lives in `lib/context/dashboard-filter-context.tsx` (Phase 4 create), keyed to
`localStorage["dashboardFilter:<user-id>"]`. When a filter is set:

- Tile quick-stats recompute for the selected slice (e.g. DART P&L `$142K → $48K StatArb P&L today`).
- Sub-route chips append `?family=X&archetype=Y&venue=Z` to their hrefs.
- Downstream pages (Research, Strategy Catalogue, Reports) already parse `?family`/`?archetype` via the Phase-3
  FamilyArchetypePicker wiring — no additional plumbing required.

Filter strip is collapsed-by-default under a `Filter strategies` disclosure to keep the dashboard quiet when nothing is
set.

---

## §5 Disambiguation — "Odum Signals" vs "Signal Intake"

| Surface              | Audience               | Direction | Tile / sub-route    | Entitlement      |
| -------------------- | ---------------------- | --------- | ------------------- | ---------------- |
| Odum Signals (tile)  | External counterparty  | Outbound  | Top-level tile      | `execution-full` |
| DART · Signal Intake | DART Signals-In client | Inbound   | DART sub-route chip | `execution-full` |

Previously the single `signals` tile conflated both. Post-collapse they are explicitly split — the former
counterparty-outbound stays at the top level (it's a commercial product), the latter Signals-In intake moves into DART
(it's a feature of the DART product for clients who bring their own signals).

---

## §6 Cross-refs

- [`dart-tab-structure.md`](./dart-tab-structure.md) — DART sub-tab catalog per persona (the DART dropdown in
  lifecycle-nav). Sub-route chips on the dashboard are the dashboard-side projection of the same catalog.
- [`restriction-policy.md`](./restriction-policy.md) — persona × cell visibility for the strategy coverage matrix;
  informs Strategy Catalogue chip behaviour.
- `codex/14-playbooks/cross-cutting/visibility-slicing.md` — visibility-slicing doctrine (hidden / locked / visible
  three-state enum across the product).
- `codex/14-playbooks/demo-ops/demo-restriction-profiles.md` — tempt-logic (padlocked-visible) for prospect personas.

---

## §7 Plan + migration notes

- **Plan:** `plans/active/dashboard_services_grid_collapse_2026_04_21.plan.md`
- **Dep:** `plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md` (Phase 11 lifecycle-nav 8→4 collapse is the
  sibling work)
- **Clean break (Citadel rule 3):** 5 deleted top-level keys (`data`, `research`, `promote`, `observe`,
  `strategy-catalogue`) and 1 renamed (`signals` → `odum-signals`). No deprecation shim. Routes themselves survive
  (still reachable via deep links + DART sub-routes); only the top-level tile is removed.

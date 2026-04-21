---
scope: [engineer, admin, product]
---

# Strategy Catalogue — 3-Tier Surface

> **Status:** canonical (2026-04-21) **Owner:** Strategy Architecture v2 + UI **SSOT for:**
> `unified-trading-system-ui/components/strategy-catalogue/StrategyCatalogueSurface.tsx`,
> `unified-trading-system-ui/lib/architecture-v2/catalogue-filter.ts`,
> `unified-trading-system-ui/app/(ops)/admin/strategy-universe/page.tsx`,
> `unified-trading-system-ui/app/(ops)/admin/strategy-lifecycle-editor/page.tsx`,
> `unified-trading-system-ui/app/(platform)/services/strategy-catalogue/page.tsx`. **Plan:**
> [`plans/active/strategy_catalogue_3tier_surface_2026_04_21.plan.md`](../../../plans/active/strategy_catalogue_3tier_surface_2026_04_21.plan.md)
> **Depends on:** [`strategy-lifecycle-maturity.md`](./strategy-lifecycle-maturity.md) ·
> [`dashboard-services-grid.md`](./dashboard-services-grid.md) · [`performance-overlay.md`](./performance-overlay.md)

---

## §1 — The three tiers

Strategy Catalogue is a **single shared primitive** (`<StrategyCatalogueSurface viewMode=... />`) rendered into four
view modes across admin + client surfaces. One component, four view modes, three business tiers:

| Tier | viewMode         | Surface                                     | Audience                         | Mutations?         |
| ---- | ---------------- | ------------------------------------------- | -------------------------------- | ------------------ |
| 1    | `admin-universe` | `/services/admin/strategy-universe`         | admin + internal-trader + IM ops | Read-only          |
| 2    | `admin-editor`   | `/services/admin/strategy-lifecycle-editor` | admin + internal-trader only     | Maturity + routing |
| 3a   | `client-reality` | `/services/strategy-catalogue?tab=reality`  | Subscribed DART + IM clients     | None               |
| 3b   | `client-fomo`    | `/services/strategy-catalogue?tab=explore`  | All entitled clients (see §3)    | Allocation request |

**Why one component.** Tiers differ only in which rows are visible, which columns/actions render, and whether mutations
are allowed. Every tier shares the same `<FamilyArchetypePicker>`, venue-set chip, maturity-phase badge, product-routing
badge, and live P&L spark. Single primitive → uniform grammar → easier refactoring → orphan audit (see
[`../../06-coding-standards/orphan-audit.md`](../../06-coding-standards/orphan-audit.md)) sees one page per viewMode,
all reachable.

---

## §2 — Tier 1: Admin universe (read-only)

**Purpose.** Give admin + internal-trader + IM-ops a single read-only view of every instance the UAC registry expresses
(~200-300 rows post Plan A — see [`strategy-lifecycle-maturity.md`](./strategy-lifecycle-maturity.md) §8).

**Surface:** `/services/admin/strategy-universe` → mounts `<StrategyCatalogueSurface viewMode="admin-universe" />`.

**Columns:**

| Column                  | Source                                                         |
| ----------------------- | -------------------------------------------------------------- |
| Family / Archetype      | UAC `StrategyInstance.family` + `archetype`                    |
| Venue-set variant       | UAC `venue_set_variant_id` → label                             |
| Instrument-type set     | UAC `instrument_type_set`                                      |
| Share class             | UAC `share_class`                                              |
| Maturity phase          | Firestore `strategy_instance_lifecycle.maturity_phase`         |
| Product routing         | Firestore `strategy_instance_lifecycle.product_routing`        |
| `odum-paper` P&L spark  | `GET /api/v1/strategy-instances/{id}/performance?views=paper`  |
| `odum-paper` run status | `running` / `paused` / `not_started` (from subscription state) |

**Affordances.** Filter (via `<FamilyArchetypePicker>` + venue-set + share-class + phase + routing pickers), search,
sort, virtualised scroll. **No mutations.** Admin-universe is diagnostic — it answers "what does the platform offer
right now?".

**Entry point.** Admin & Ops tile → "Strategy Universe" chip (added in Plan B Phase 2 via
`SERVICE_REGISTRY.admin.subRoutes[]`).

---

## §3 — Tier 2: Admin lifecycle editor

**Purpose.** The only surface that mutates lifecycle state. Admin + internal-trader only.

**Surface:** `/services/admin/strategy-lifecycle-editor` → mounts
`<StrategyCatalogueSurface viewMode="admin-editor" />`.

Same columns as Tier 1, plus inline editors on each row:

- `[maturity_phase ▾]` — dropdown showing only legal forward transitions + `retired` (forward-only rule enforced
  client-side, re-validated server-side).
- `[product_routing ▾]` — dropdown of all four routings.

**Actions.**

- **Per-row edit** — change dropdown → PATCH `/api/v1/registry/strategy-instances/{id}/lifecycle` → toast "Change
  applied. Undo (5s)".
- **Bulk edit** — multi-select via filter → "Apply to N rows" → N PATCH calls (1:1 with audit log).
- **Row drawer** — click row → drawer showing full `phase_history` + allocation metrics + quick-links to Performance
  Overlay.

**Entry point.** Admin & Ops tile → "Strategy Lifecycle Editor" chip.

**Why not merge editor with universe.** Read-only and editor are deliberately separate URLs so an admin can link a
colleague to the _read-only_ catalogue (Tier 1) without giving edit access. Access gating is by route, not by in-page
toggles.

---

## §4 — Tier 3: Client view (Reality + FOMO)

**Purpose.** Every subscribed or prospective client lands here to see what they own and what they could own next.

**Surface:** `/services/strategy-catalogue` → mounts `<StrategyCatalogueSurface>` with a two-tab layout:

- `?tab=reality` → `viewMode="client-reality"` — instances **this org subscribes to**.
- `?tab=explore` → `viewMode="client-fomo"` — instances **available to this org's tier but not subscribed**.

Default tab: Reality if ≥1 subscription, else Explore.

### 4.1 — Reality tab

**Per-row rendering:** `<RealityPositionCard>`.

- Header: family · archetype · venue-set variant · share-class chip.
- Live P&L (today + 7d + MTD) from real client fills (not `odum-paper`).
- Current allocation size.
- Active venues executing (subset of venue-set variant that has fills today).
- Maturity-phase badge.
- Drill-through: "View in DART terminal" · "View in Reports attribution".

**Empty state.** "You don't have any subscribed strategies yet. Explore the catalogue below." + link to `?tab=explore`.

### 4.2 — FOMO (Explore) tab

**Per-row rendering:** `<FomoTearsheetCard>` — a tearsheet teaser per entitled instance the org does **not** subscribe
to.

**Critical:** the live P&L shown on a FOMO tearsheet is `odum-live`'s run of that instance, **not** any real client's
run. Never. (See
[`../../14-playbooks/shared-core/odum-paper-client-zero.md`](../../14-playbooks/shared-core/odum-paper-client-zero.md)
§8 FAQ, and `memory/project_fomo_tearsheets_show_live_is_odum_own_run_2026_04_21.md`.)

**Contents.**

- Header: family · archetype · venue-set variant · share-class chip.
- 3-way overlay chart: backtest / paper / live — powered by
  `<PerformanceOverlay mode="stitched" views=["backtest","paper","live"]>` (see
  [`performance-overlay.md`](./performance-overlay.md)).
- Key stats sidecar: Sharpe, MDD, CAGR, win-rate, avg-trade-size (from `<PerformanceOverlayStats>`).
- "Request allocation" CTA → POSTs to `allocation_requests/{org}/{instance_id}` collection.

**Allocation CTA gating (two-layer):**

1. **Product routing** — instance's routing must include this org's tier. A `dart_only` instance is invisible to IM
   clients; an `im_only` instance is invisible to DART clients; `both` is visible to all entitled clients;
   `internal_only` is invisible outside admin/internal-trader.
2. **Maturity phase** — instance must be `paper_stable` or later. Instances in `smoke`/`backtest_*`/`paper_1d`/
   `paper_14d` are hidden from FOMO entirely (no allocation CTA at all — too early to offer).

If either gate fails, the instance is omitted from the FOMO feed (not greyed out — not even rendered). Hidden > locked
for this surface, because a locked padlocked allocation CTA would be misleading.

---

## §5 — Per-persona viewMode matrix

Which view modes each persona sees, via `lib/auth/persona-dashboard-shape.ts` + entry points:

| Persona               | T1 universe | T2 editor | T3 reality | T3 FOMO | Notes                                                      |
| --------------------- | ----------- | --------- | ---------- | ------- | ---------------------------------------------------------- |
| admin                 | ✓           | ✓         | ✓          | ✓       | Sees all instances regardless of product routing           |
| internal-trader       | ✓           | ✓         | ✓          | ✓       | Same as admin for catalogue                                |
| im-desk-operator      | ✓           | ·         | ✓          | ✓       | Read-only universe; IM allocator view via Reports tile     |
| client-full           | ·           | ·         | ✓          | ✓       | DART client — gated by product_routing ∈ {dart_only, both} |
| client-premium        | ·           | ·         | ✓          | ✓       | Same                                                       |
| client-data-only      | ·           | ·         | ·          | ·       | DART · Strategy Catalogue chip only (not this surface)     |
| prospect-dart         | ·           | ·         | ·          | ✓       | Tempt-logic: FOMO only, no Reality (nothing subscribed)    |
| prospect-signals-only | ·           | ·         | ·          | ·       | No catalogue access (Signal Intake only)                   |
| client-im-pooled      | ·           | ·         | ✓          | ✓       | IM client — gated by product_routing ∈ {im_only, both}     |
| client-im-sma         | ·           | ·         | ✓          | ✓       | Same                                                       |
| prospect-im           | ·           | ·         | ·          | ○       | Padlocked FOMO tempt; upgrade CTA                          |
| client-regulatory     | ·           | ·         | ·          | ·       | Reports only                                               |

**Legend:** ✓ visible · ○ locked (padlocked + upgrade CTA) · · hidden.

Admin + internal-trader bypass both product-routing and maturity-phase FOMO gates — they see everything so they can QA
tearsheets before exposing to clients.

---

## §6 — Allocation-request flow (FOMO CTA)

```
Client clicks "Request allocation" on FomoTearsheetCard
  → POST /api/v1/allocation-requests
      body: {
        org: "<org-id>",
        instance_id: "<ARCHETYPE@venue-...>",
        requested_by: "<user-id>",
        requested_size: <number>,
        note?: string
      }
  → unified-trading-api writes allocation_requests/{org}/{instance_id}
  → STRATEGY_ALLOCATION_REQUESTED event
  → admin notified via Admin & Ops tile notifications drawer
  → admin reviews; either:
      (a) Approves → creates subscription row, client flips to Reality tab on next refresh
      (b) Declines → sends note, row greys in client FOMO tab for 30d
```

The CTA is **not** a self-service subscription. Allocation is always human-gated — an admin reviews the request, may
require KYC/mandate uplift, and only then creates the subscription. This is commercial + compliance gating.

---

## §7 — Filter state & URL deep-links

Filter state lives in `lib/architecture-v2/catalogue-filter.ts`:

```typescript
interface StrategyCatalogueFilter {
  family?: string;
  archetype?: string;
  venue_set_variant?: string;
  share_class?: ShareClass;
  maturity_phase?: StrategyMaturityPhase;
  product_routing?: ProductRouting;
  allocation_status?: "subscribed" | "requested" | "none";
}
```

URL-serializable so the admin can paste a filtered view link to a colleague
(`/services/admin/strategy-universe?family=CARRY_BASIS&share_class=usdt`). On the dashboard (Plan
`dashboard_services_grid_collapse`), filter state syncs with `DashboardFilterContext` so a filter set on the tile grid
flows into the catalogue and back.

---

## §8 — Orphan-audit compliance

The rebuilt surface follows the orphan-audit policy (see
[`../../06-coding-standards/orphan-audit.md`](../../06-coding-standards/orphan-audit.md)):

- `/services/strategy-catalogue` **stays mounted** — it was a DART sub-route chip, now becomes the Tier 3 page.
  `SERVICE_REGISTRY.dart.subRoutes[]` keeps its `strategy-catalogue` chip (label: "Catalogue") pointing at the same URL
  — no broken link.
- `/services/admin/strategy-universe` + `/services/admin/strategy-lifecycle-editor` are **new** routes reachable from
  `SERVICE_REGISTRY.admin.subRoutes[]` — no orphans.
- Reports tile (for IM personas) gets a `strategy-catalogue` chip pointing at `?tab=explore` — same URL, persona- gated
  tab. One more reachability source; still one surface.

Every route introduced or repurposed by Plan B passes the Phase-1 scanner's reachability check at commit time.

---

## §9 — Data wiring (post Plan A Phase 2, pre Plan A Phase 3 + Plan C)

Plan A Phase 2 is live — `lib/architecture-v2/lifecycle.ts` is the SSOT mirror of UAC types, regenerated from
`unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/` via
`unified-trading-pm/scripts/openapi/generate_ui_reference_data.py` into `lib/registry/ui-reference-data.json`. The
scaffold-only `lifecycle-placeholder.ts` has been deleted.

| Source                                           | Consumer                                                                                      | Status                                                                                                                  |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| UAC `STRATEGY_INSTANCE_CATALOGUE` (84 instances) | `<StrategyCatalogueSurface>` via `loadStrategyCatalogue()`                                    | **Live** — admin-universe tables render real family / archetype / venue-set / share-class + coverage-status per row.    |
| UAC `VENUE_SET_VARIANTS` (21 variants)           | Surface via `lookupVenueSetVariant(id)`                                                       | **Live** — variant label + venues + pricing tier feed Reality + FOMO cards.                                             |
| UAC `StrategyMaturityPhase` / `ProductRouting`   | Surface enum imports                                                                          | **Live** — types + labels + tones. Runtime values still synthesised per instance-id until Plan A Phase 3 Firestore doc. |
| Firestore `strategy_instance_lifecycle/{id}`     | Per-instance `maturityPhase` / `productRouting` / series refs                                 | **Pending Plan A Phase 3** — hash-based synthesis in `synthesiseMaturity` / `synthesiseRouting`.                        |
| Plan C `<PerformanceOverlay>`                    | `FomoTearsheetCard` + `RealityPositionCard` use `<PerformanceOverlayPlaceholder>` prop-shape. | **Pending Plan C** — swap is a single named-import change; Sharpe / MDD / CAGR / P&L remain synthesised.                |
| `admin-editor` PATCH endpoint                    | `<StrategyCatalogueSurface viewMode="admin-editor">` inline editors                           | **Pending Plan A Phase 3** — buttons render but stay disabled with tooltip "Enabled when Plan A Phase 3 PATCH ships".   |

Scope of the final swap when Plan A Phase 3 + Plan C land:

- Replace `synthesiseMaturity` / `synthesiseRouting` in `StrategyCatalogueSurface.tsx` with a Firestore-backed hook
  reading `strategy_instance_lifecycle/{instanceId}` (Plan A Phase 3 reloader owns the hot-reload cadence).
- Named-import swap `<PerformanceOverlayPlaceholder>` → `<PerformanceOverlay>` in Fomo + Reality cards.
- Enable the admin-editor PATCH wiring behind an entitlement gate (admin + internal-trader).

---

## §10 — Cross-references

- [`strategy-lifecycle-maturity.md`](./strategy-lifecycle-maturity.md) — the 5-dim registry + maturity enum this surface
  renders.
- [`../../../plans/active/strategy_catalogue_3tier_surface_2026_04_21.plan.md`](../../../plans/active/strategy_catalogue_3tier_surface_2026_04_21.plan.md)
  — the plan this doc is the SSOT for.
- [`performance-overlay.md`](./performance-overlay.md) — the chart primitive embedded in FOMO tearsheets.
- [`dashboard-services-grid.md`](./dashboard-services-grid.md) — §4.5 declares Strategy Catalogue is a cross-cutting
  primitive, not a 6th tile.
- [`../../14-playbooks/shared-core/odum-paper-client-zero.md`](../../14-playbooks/shared-core/odum-paper-client-zero.md)
  — the series source for FOMO tearsheets.
- [`../../06-coding-standards/orphan-audit.md`](../../06-coding-standards/orphan-audit.md) — policy this surface
  complies with.

# Phase 2f: Manage Lifecycle Tab — Deep Audit

**Created:** 2026-03-21 **Type:** audit | **Status:** complete (20/20) | **Scope:** Deep audit of all UI components,
navigation, data wiring, and UX under the Manage lifecycle tab (MANAGE_TABS — 5 routes in app/(ops)/).

**Repo:** `unified-trading-system-ui` **Parent plan:** `ui_lifecycle_service_tab_cross_reference_2026_03_21.md`
(Phase 1)

---

## Scope

**Lifecycle stage:** Manage — "Clients, mandates, fees & onboarding (Back Office)" **Color:** `text-rose-400` |
**Icon:** Settings2 **Layout:** NONE in (platform) — pages live in `app/(ops)/` route group **Tab set:** MANAGE_TABS (5
tabs, no entitlement gating)

**Structural issue:** MANAGE_TABS is defined in service-tabs.tsx (a platform component) but all backing pages live in
the (ops) route group. No layout.tsx imports MANAGE_TABS. The (ops) layout likely has its own navigation structure.

### Routes Under Audit

| #   | Tab Label  | Route              | Page Location                        | Route Group |
| --- | ---------- | ------------------ | ------------------------------------ | ----------- |
| 1   | Clients    | `/manage/clients`  | `app/(ops)/manage/clients/page.tsx`  | (ops)       |
| 2   | Mandates   | `/manage/mandates` | `app/(ops)/manage/mandates/page.tsx` | (ops)       |
| 3   | Fees       | `/manage/fees`     | `app/(ops)/manage/fees/page.tsx`     | (ops)       |
| 4   | Users      | `/manage/users`    | `app/(ops)/manage/users/page.tsx`    | (ops)       |
| 5   | Compliance | `/compliance`      | `app/(ops)/compliance/page.tsx`      | (ops)       |

#### Additional (ops) pages referenced by lifecycle-mapping.ts

| #   | Route     | In stageServiceMap         | In MANAGE_TABS |
| --- | --------- | -------------------------- | -------------- |
| 6   | `/admin`  | YES                        | NO             |
| 7   | `/config` | NO (primaryStage: promote) | NO             |
| 8   | `/ops`    | NO (primaryStage: observe) | NO             |

---

## Phase 1 Confirmed Findings

| ID   | Finding                                                                                                                                               | Severity   | Impact on Phase 2f                                     |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------ |
| C6   | MANAGE_TABS never rendered — no layout imports it                                                                                                     | P1-fix     | A1 pre-confirmed                                       |
| LW   | `app/(ops)/layout.tsx` uses RequireAuth + role check (internal/admin) → UnifiedShell with orgName="Odum Internal". NO ServiceTabs rendered            | P1-fix     | A2 pre-confirmed — (ops) has its own shell but no tabs |
| LW   | `app/(ops)/manage/layout.tsx` is metadata-only (`<div className="min-h-screen bg-background">{children}</div>`) — NO ServiceTabs                      | P1-fix     | Confirms no tab navigation exists for Manage           |
| E3   | isItemAccessible correctly gates `/manage/*`, `/compliance`, `/admin` for internal-only users                                                         | PASS       | F2 pre-confirmed — access control at nav level works   |
| B4   | `/admin` is in stageServiceMap(manage) but NOT in MANAGE_TABS — separate admin page                                                                   | INFO       | Note in C1 findings                                    |
| Gap1 | MANAGE_TABS has zero requiredEntitlement — but (ops) route group enforces role=internal/admin at L1, so URL bypass is NOT possible for external users | PASS       | F1 is structurally protected by route group            |
| D4   | `/manage/mandates`, `/manage/fees`, `/manage/users` not in stageServiceMap — only reachable if user knows URL                                         | P2-improve | C3 must verify discoverability                         |

---

## Audit Tasks

### A. Structural Issues (3 tasks)

- [x] **A1. Route group mismatch** — MANAGE_TABS defined in (platform) components but pages in (ops). ISSUE P1-fix:
      MANAGE_TABS is dead — no layout renders it. Pages in (ops) have no tab navigation.
- [x] **A2. (ops) layout audit** — PASS. (ops) layout: RequireAuth → role check → UnifiedShell (lifecycle nav only).
      Auth model is correct for admin panel. Only gap: no ServiceTabs in manage/layout.tsx (covered by A1).
- [x] **A3. Role-based access** — INFO: Manage tab correctly hidden for non-internal users via opsRoutes filter in
      lifecycle-nav.tsx + (ops) layout role check. Two-layer enforcement is sound.

### B. Component Inventory (5 tasks)

- [x] **B1. Clients page** (`/manage/clients`) — PASS. ~365 lines, list+detail views, create org dialog, tier change.
      Data: local state only (INITIAL_ORGS).
- [x] **B2. Mandates page** (`/manage/mandates`) — ISSUE P1-fix. Stub page (~110 lines), "Coming Soon" badge, 4
      placeholder cards. No data, no functionality.
- [x] **B3. Fees page** (`/manage/fees`) — PASS. ~366 lines, fee table w/ inline edit, fee simulator. Uses
      useOrganizationsList + useSubscriptions (partial wiring).
- [x] **B4. Users page** (`/manage/users`) — PASS. ~352 lines, user table, invite dialog, role edit, suspend. Right
      components for user admin. Note: inviteName/setInviteOrg naming bug (line 57) to fix.
- [x] **B5. Compliance page** (`/compliance`) — ISSUE P1-fix. ~180 lines, correct FCA info content. BUT renders custom
      header that replaces UnifiedShell nav — admin loses all navigation. "Back" goes to landing page instead of admin
      area.

### C. Navigation & Routing (4 tasks)

- [x] **C1. Lifecycle nav for Manage** — ISSUE P2-improve. Only 3 of 6 pages in stageServiceMap dropdown. Less critical
      if A1 (tab nav) is fixed — tabs handle the rest.
- [x] **C2. (ops) navigation** — INFO. No (ops)-specific sidebar/tabs. Uses same UnifiedShell/LifecycleNav as
      (platform). No conflict.
- [x] **C3. Manage-internal navigation** — ISSUE P1-fix. Users cannot navigate between 5 Manage pages via tabs.
      MANAGE_TABS never rendered.
- [x] **C4. Cross-lifecycle links** — ISSUE P2-improve. No cross-lifecycle links. Compliance "Back" goes to /. Clients
      Users tab references User Management without a link.

### D. Data Wiring (2 tasks)

- [x] **D1. Client/mandate/fee data** — PASS. Mock data shapes match real backend API. Mix of local state and API hooks
      is expected pre-integration. Org/sub/fee data fields are correct for admin use case.
- [x] **D2. User management data** — INFO. Mock user data (INITIAL_USERS) has right fields. useOrgMembers() hook exists
      for future integration. Data consistency across pages resolves when all wire to same API.

### E. UX Audit (3 tasks)

- [x] **E1. Admin workflow** — ISSUE P2-improve. Steps 1 (create org), 3 (set fees), 4 (add users) work. Step 2
      (mandates) is stub. No connected flow between steps — creating org doesn't prompt fees/users setup.
- [x] **E2. Loading/error/empty states** — ISSUE P2-improve. No loading spinners for API-backed pages (Fees, Admin).
      Acceptable for mock phase; needed for real API integration.
- [x] **E3. Responsive behavior** — INFO P2-improve. Mandates: no mobile breakpoint. Fees+Users: wide tables with no
      overflow wrapper.

### F. Access Control (3 tasks)

- [x] **F1. Internal-only enforcement** — PASS. All 3 client personas blocked via nav-level filter + (ops) layout role
      check. Two-layer enforcement confirmed.
- [x] **F2. isItemAccessible logic** — PASS. opsRoutes prefix matching correctly gates all /manage/\* and /compliance
      routes behind isInternal().
- [x] **F3. (ops) vs (platform) auth** — INFO. Documented: (ops) adds role check on top of RequireAuth. Hardcodes
      orgName="Odum Internal". No ServiceTabs (unlike platform per-service layouts).

---

## Output Format

Per task:

```
Task: [ID]
Status: PASS | ISSUE | INFO
Severity: P0-blocking | P1-fix | P2-improve | P3-cosmetic
Finding: [description]
Recommendation: [action]
```

## Depends On

Phase 1 findings (A6, B1-B5, C6)

## Feeds Into

Phase 3 cross-reference audit (C4, F1-F3)

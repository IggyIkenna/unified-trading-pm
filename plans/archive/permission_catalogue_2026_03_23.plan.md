---
title: "Permission Catalogue — Granular Access Registry for Admin Portal"
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-03-23
readiness:
  code: C0
  deployment: D0
  business: B1
affects:
  - auth-api
  - unified-trading-system-ui
depends_on: [user-management-merge]
---

# Permission Catalogue — Granular Access Registry

> **Conflict resolution**: Phase 1 (auth_api catalogue routes) and Phase 3 (onboard page) depend on
> user_management_merge completing first. user_management_merge creates the provisioning routes and onboard page that
> this plan extends. Both plans modify auth-api app.py — execute sequentially.

## Context

The current entitlement model has 7 flat keys (data-basic, data-pro, etc.). This is too coarse. Admins need to see ALL
possible permissions — like the venue/instrument registry but for access control — so they can grant granularly and
users can request specific capabilities.

## Permission Domains (8 categories)

### 1. Platform Services (portal access)

Which UI sections and API domains the user can access.

- data, research, trading, execution, observe, manage, reports
- Internal: admin, ops, config, devops

### 2. Data Access

- **Venues** (33): binance, coinbase, bybit, okx, deribit, databento, tardis, yahoo_finance, aave_v3, uniswap_v3,
  hyperliquid, polymarket, ...
- **Market categories**: CEFI, TRADFI, DEFI, SPORTS, PREDICTION
- **Data types**: tick (OHLCV), daily candles, order book, processed, features
- **Instrument types**: SPOT_PAIR, PERPETUAL, FUTURE, OPTION, EQUITY, ETF, ...

### 3. Research & ML

- Model training, experiments, feature store, model registry, deployment
- Strategy backtesting, candidates, comparison, handoff
- Signal access (which ML signals, which strategy signals)

### 4. Execution

- **Algos**: TWAP, VWAP, SOR, Iceberg, POV, PassiveAggressive, AdaptiveTWAP, AlmgrenChriss
- **Instruction types**: TRADE, SWAP, ZERO_ALPHA, PREDICTION_BET, FUTURES_ROLL, OPTIONS_COMBO, ADD_LIQUIDITY
- **Venue execution**: which venues can execute on
- **Can trade**: hard gate (yes/no)

### 5. Reporting & Regulatory

- P&L attribution, settlement, reconciliation, regulatory, executive summary
- Client reporting access

### 6. Internal Provisioning (Slack/GitHub/M365/GCP/AWS)

- **Slack**: workspace access, specific channels
- **GitHub**: org membership, specific teams, repo access level
- **Microsoft 365**: account, license type, groups
- **GCP**: project access, IAM role (viewer/editor/admin)
- **AWS**: IAM user, permission sets, SSO access

### 7. Org-Level Scoping

- Org subscription ceiling (defines max possible access)
- Users within org can have subset of org access
- Data scoping: see only org's instruments/strategies

### 8. Feature Subscriptions

- Individual signal subscriptions within an entitlement tier
- Custom feed access
- Premium feature flags

## Execution

### Phase 0: Permission SSOT Consolidation (UAC)

- [x] [AGENT] P0. Consolidate 4 drifted permission taxonomies into UAC `rbac.py` — added `OrgType`, `Entitlement` (13
      values), `SubscriptionTier` (7 values), `ProvisioningRole` (8 values), `TIER_ENTITLEMENTS` mapping. UTL
      `entitlements.py` and API gateway `entitlement.py` updated to import from UAC instead of defining locally.
      TypeScript UIs align manually.

### Phase 1: Catalogue Model + API (unified-trading-api — auth-api does not exist)

- [x] [AGENT] P0. Create `unified_trading_api/models/permission_catalogue.py` — PermissionDomain (8-value StrEnum),
      CataloguePermission, PermissionCategory, DomainNode, CatalogueTree (Pydantic models). Hierarchical: domain →
      category → permission. Each permission has: key, label, description, domain, category, is_internal_only flag.

- [x] [AGENT] P0. Create `unified_trading_api/models/permission_catalogue_data.py` — full catalogue data seeded from
      real codebase registries. 8 domains, ~100+ permissions: 33 venues, 8 algos, 7 instruction types, 13 entitlements
      from UAC Entitlement enum, internal-only flags on provisioning perms.

- [x] [AGENT] P0. Create `unified_trading_api/routes/catalogue.py` — GET /catalogue (full tree), GET /catalogue/domains
      (summary), GET /catalogue/domain/{domain} (single domain), GET /catalogue/search?q= (case-insensitive substring
      search).

- [x] [AGENT] P0. Wire catalogue router into main.py at `/catalogue` prefix.

- [x] [AGENT] P0. Tests for catalogue endpoints — 18 tests covering data integrity + route behavior.

### Phase 2: Admin UI — Catalogue Browser

- [x] [AGENT] P0. Create catalogue browser page at app/(ops)/admin/users/catalogue/page.tsx — tree view of all
      permission domains, expandable categories, searchable. Shows every possible permission.

- [x] [AGENT] P0. Add "Catalogue" tab to ADMIN_TABS / USER_MGMT_TABS.

### Phase 3: Wire into User Flows

- [x] [AGENT] P0. Update onboard page — replace flat checkbox list with catalogue-driven permission picker (grouped by
      domain, expandable, searchable).

- [x] [AGENT] P0. Update modify page — same catalogue-driven picker, pre-checked with user's current permissions.

- [x] [AGENT] P0. Update access request page (user-facing) — users browse catalogue to request specific permissions.

- [x] [AGENT] P0. Update user detail page — show granted permissions organized by domain.

### Phase 4: Mock + Tests

- [x] [AGENT] P0. Add catalogue to mock handler (full tree in mock-provisioning-state.ts).

- [x] [AGENT] P0. Add Playwright E2E tests for catalogue browser + catalogue-driven onboard.

- [ ] [AGENT] P0. Run QG on both repos.

## Success Criteria

- Admin can browse ALL possible permissions in a tree view
- Admin can search permissions by name
- Onboard/modify flows use catalogue-driven picker (not flat list)
- Users can request specific permissions from catalogue
- User detail shows permissions organized by domain
- 33 venues, 12+ algos, 15+ instrument types, 6 internal services all visible
- E2E tests cover catalogue browsing + permission granting

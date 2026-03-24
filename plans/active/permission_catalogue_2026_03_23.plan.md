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
---

# Permission Catalogue — Granular Access Registry

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

### Phase 1: Catalogue Model + API (auth-api)

- [ ] [AGENT] P0. Create `auth_api/models/permission_catalogue.py` — PermissionDomain, PermissionCategory, Permission
      (hierarchical: domain → category → permission). Each permission has: key, label, description, domain, category,
      is_internal_only flag.

- [ ] [AGENT] P0. Create `auth_api/data/permission_catalogue.py` — the actual catalogue data seeded from real codebase
      registries (33 venues, 12+ algos, 15+ instrument types, 6 internal services).

- [ ] [AGENT] P0. Create `auth_api/routes/catalogue.py` — GET /catalogue (full tree), GET /catalogue/{domain} (single
      domain), GET /catalogue/search?q= (search permissions by name).

- [ ] [AGENT] P0. Wire catalogue router into app.py.

- [ ] [AGENT] P0. Tests for catalogue endpoints.

### Phase 2: Admin UI — Catalogue Browser

- [ ] [AGENT] P0. Create catalogue browser page at app/(ops)/admin/users/catalogue/page.tsx — tree view of all
      permission domains, expandable categories, searchable. Shows every possible permission.

- [ ] [AGENT] P0. Add "Catalogue" tab to ADMIN_TABS / USER_MGMT_TABS.

### Phase 3: Wire into User Flows

- [ ] [AGENT] P0. Update onboard page — replace flat checkbox list with catalogue-driven permission picker (grouped by
      domain, expandable, searchable).

- [ ] [AGENT] P0. Update modify page — same catalogue-driven picker, pre-checked with user's current permissions.

- [ ] [AGENT] P0. Update access request page (user-facing) — users browse catalogue to request specific permissions.

- [ ] [AGENT] P0. Update user detail page — show granted permissions organized by domain.

### Phase 4: Mock + Tests

- [ ] [AGENT] P0. Add catalogue to mock handler (full tree in mock-provisioning-state.ts).

- [ ] [AGENT] P0. Add Playwright E2E tests for catalogue browser + catalogue-driven onboard.

- [ ] [AGENT] P0. Run QG on both repos.

## Success Criteria

- Admin can browse ALL possible permissions in a tree view
- Admin can search permissions by name
- Onboard/modify flows use catalogue-driven picker (not flat list)
- Users can request specific permissions from catalogue
- User detail shows permissions organized by domain
- 33 venues, 12+ algos, 15+ instrument types, 6 internal services all visible
- E2E tests cover catalogue browsing + permission granting

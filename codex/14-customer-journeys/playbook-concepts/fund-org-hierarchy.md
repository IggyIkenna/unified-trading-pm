---
doc_type: codex-ssot
title: Fund / Org / Client Hierarchy
summary:
  Org -> Fund (Pooled or SMA) -> Client -> per-client API keys — the structural hierarchy shaping user-management-ui
  provisioning, Firebase entitlements, and /services/reports/*; every client's venue keys are isolated in Secret
  Manager, never shared across clients.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [fund, org, provisioning, entitlements, sma, client-isolation]
related:
  [
    /codex/14-customer-journeys/playbook-concepts/sma-vs-pooled.md,
    ../../04-architecture/share-class-architecture.md,
    ../../04-architecture/client-isolation-sla-and-runtime-profiles.md,
    ../../07-security/secrets-management.md,
  ]
created: 2026-04-19
authoritative_for: [org/fund/client provisioning hierarchy (UI + entitlements view)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/authentication/README.md,
    /codex/14-customer-journeys/authentication/firebase-production.md,
    /codex/14-customer-journeys/authentication/firebase-staging.md,
    /codex/14-customer-journeys/playbook-concepts/README.md,
    /codex/14-customer-journeys/playbook-concepts/admin-permissions.md,
    /codex/14-customer-journeys/playbook-concepts/client-reporting.md,
    /codex/14-customer-journeys/playbook-concepts/sma-vs-pooled.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Fund / Org / Client Hierarchy

The structural model under which every client engagement exists. Shapes provisioning in user-management-ui, entitlements
in Firebase, and reporting in `/services/reports/*`.

## The hierarchy

```
Organisation (org)
    ↓ (has one or more)
Fund (Pooled or SMA)
    ↓ (has one or more)
Client
    ↓ (each has fresh, isolated)
API keys (per venue, per client)
```

**Example (Pooled):**

```
Alpha Capital (org)
├── Alpha Pooled Fund (Pooled fund)
│   ├── Alpha Share Class A (client — retail tier)
│   ├── Alpha Share Class B (client — institutional tier)
│   └── Alpha Share Class C (client — founder)
```

**Example (SMA):**

```
Beta Wealth (org)
├── Beta SMA Fund — Client X (SMA fund #1)
│   └── Client X (client — one per SMA)
├── Beta SMA Fund — Client Y (SMA fund #2)
│   └── Client Y
└── Beta SMA Fund — Client Z (SMA fund #3)
    └── Client Z
```

See [sma-vs-pooled.md](sma-vs-pooled.md) for the decision tree.

## Definitions

- **Organisation** — top-level container. Maps to a firm (not a person). Users are provisioned under an org.
  Entitlements cascade from org to user.
- **Fund** — a portfolio, either Pooled (one fund, many clients as share classes) or SMA (one fund per client). Each
  fund has venues, capital, strategies, risk limits.
- **Client** — an entity holding positions within a fund. A client can be a share class (Pooled) or the fund's sole
  client (SMA). Each client has its own API keys — never shared.
- **API key** — venue credentials. Issued per-client (never shared across clients). Stored in Secret Manager.
  Hot-reloaded via UTL `ApiKeyReloader`.

## Provisioning surface

- **Admin UI**: user-management-ui (kept separate from unified-trading-system-ui per security — may never be publicly
  deployed)
- **Reachable by**: admin persona only (role gate in [user-management-ui server middleware](user-management-ui/server/))
- **Operates on**: staging Firebase (for demos) and production Firebase (for real clients) — via environment-specific
  user-management-api URL

## Who can provision whom

| Actor                |  Can create orgs   | Can create funds | Can create clients | Can assign entitlements |
| -------------------- | :----------------: | :--------------: | :----------------: | :---------------------: |
| Odum admin           |         ✅         |        ✅        |         ✅         |           ✅            |
| Odum ops             | ✅ (with approval) |        ✅        |         ✅         |       ✅ (subset)       |
| Odum internal trader |         —          |        —         |         —          |            —            |
| Client user          |         —          |        —         |         —          |            —            |

No client-level self-service provisioning today. Every org / fund / client / entitlement change goes through Odum ops.

## Org-scoped JWT claims — gap

Firebase custom claims today carry `org_id` only. Adding `fund_id` and `client_id` would let the UI filter reports by
fund+client at the JWT layer without an extra API roundtrip.

**Gap**: add fund_id + client_id to custom claims. Tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

Until that ships, UI filters by fund+client via a dropdown picker + API call per page view.

## Environment parity

The same org/fund/client structure exists in:

- Staging (for demos) — via staging user-management-api + staging Firebase
- Production (for real clients) — via production user-management-api + production Firebase

user-management-ui admin surface can target either by switching API URL. See [../environments/](../environments/).

## Demo provisioning (pb3)

For each prospect, Odum admin pre-creates:

1. Org (sanitised alias, e.g. "Demo — Alpha Capital")
2. Fund structure matching pb3 flavour (Pooled OR SMA, or both if demo is educational about the choice)
3. Client(s) with mock API keys
4. User with prospect's email
5. Entitlements matching flavour

Prospect then logs in and the UI already has their context. See
[../authentication/firebase-staging.md](../authentication/firebase-staging.md).

## Real-client provisioning (post-commit)

Step-by-step flow in [../authentication/firebase-production.md](../authentication/firebase-production.md).

## Related plans

- [user_management_merge_2026_03_23.plan.md](../../../plans/ai/user_management_merge_2026_03_23.plan.md) — provisioning
  workflows
- [share_class_architecture_2026_04_01.plan.md](../../../plans/archive/share_class_architecture_2026_04_01.plan.md) —
  share class structure
- [deployment_topology_and_client_isolation_2026_04_17.plan.md](../../../plans/archive/deployment_topology_and_client_isolation_2026_04_17.plan.md)
  — client isolation per SLA tier

## Related codex

- Client isolation SLA:
  [../../04-architecture/client-isolation-sla-and-runtime-profiles.md](../../04-architecture/client-isolation-sla-and-runtime-profiles.md)
- Share class architecture:
  [../../04-architecture/share-class-architecture.md](../../04-architecture/share-class-architecture.md)
- Capital flow: [../../04-architecture/capital-flow-model.md](../../04-architecture/capital-flow-model.md)
- Wallet hierarchy (DeFi):
  [../../04-architecture/wallet-hierarchy-and-capital-flow.md](../../04-architecture/wallet-hierarchy-and-capital-flow.md)
- Secrets management: [../../07-security/secrets-management.md](../../07-security/secrets-management.md)

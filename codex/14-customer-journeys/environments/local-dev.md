---
doc_type: codex-ssot
title: Local dev
summary:
  Per-playbook local-dev tier/port guide — pb1/pb2 marketing+briefings on Tier 0 static (port 3100), pb3 demo on Tier 1
  (3000, MockStateStore), full fleet on Tier 2 — driven by dev-tiers.sh, plus the localStorage persona-seed devtools
  shortcut; defers to runtime-tiers-and-deployment.md as SSOT.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [client-reporting-api, unified-trading-api, unified-trading-system-ui]
scope: [engineer, admin]
tags: [local-dev, ui, dev-tiers, playbook, demo, environments]
related:
  [
    ../../05-infrastructure/runtime-tiers-and-deployment.md,
    ../../08-workflows/local-dev.md,
    ../authentication/README.md,
    ../testing/README.md,
  ]
created: 2026-04-19
authoritative_for: [per-playbook local-dev tier and port selection]
referenced_by: [/codex/14-customer-journeys/environments/README.md]
owner:
last_reviewed:
code_refs: [unified-trading-system-ui/scripts/dev-tiers.sh, unified-trading-system-ui/lib/auth/personas.ts]
---

# Local dev

## Canonical source of truth

For the **consolidated portal** (Next.js, the only UI we ship today): the SSOT is
[../../05-infrastructure/runtime-tiers-and-deployment.md](../../05-infrastructure/runtime-tiers-and-deployment.md) —
tier model (static/T0/T1/T2), boot flags (`--real`, `--firebase-local`), and the unified `dev-tiers.sh` script.

For **standalone backend service work** outside the dev-tiers T1/T2 set: see
[../../08-workflows/local-dev.md](../../08-workflows/local-dev.md) — its frontend sections are stale (pre-UI
consolidation, 10+ Vite apps), but its backend orchestration via `dev-start.sh` / `dev-stop.sh` / `dev-status.sh` and
the API port registry (8004-8016) are still in use. Read the banner at the top of that doc.

This doc captures ONLY what's specific to the playbook context.

## Which port / tier to use per playbook

| Playbook                | Recommended tier | Port                  | Why                                                                              |
| ----------------------- | ---------------- | --------------------- | -------------------------------------------------------------------------------- |
| pb1 (marketing)         | Tier 0 or static | 3100                  | No Python backend needed; homepage is static HTML + React                        |
| pb2 (briefings)         | Tier 0 or static | 3100                  | Same — briefings content is static + light-auth gate                             |
| pb3 (demo)              | Tier 1           | 3000                  | Need API gateway for services portal; MockStateStore gives persistent demo state |
| Visibility-slicing test | Tier 0           | 3100                  | Persona switching via localStorage seed works entirely client-side               |
| Full fleet dev          | Tier 2           | 3000 + all downstream | Only when debugging a specific service interaction end-to-end                    |

## Start / stop

```bash
cd unified-trading-system-ui
bash scripts/dev-tiers.sh --tier 0      # UI-only static preview (3100)
bash scripts/dev-tiers.sh --tier 1      # + UI + unified-trading-api + client-reporting-api
bash scripts/dev-tiers.sh --tier 2      # + full fleet
bash scripts/dev-tiers.sh --stop        # stop everything
bash scripts/dev-tiers.sh --status      # check what's up
```

## Demo persona shortcut

To skip the login form during local dev, seed localStorage directly:

```javascript
// In browser devtools console on localhost:
localStorage.setItem(
  "portal_user",
  JSON.stringify({
    id: "admin",
    email: "admin@odum.internal",
    displayName: "Admin",
    role: "admin",
    org: { id: "odum-internal", name: "Odum Internal" },
    entitlements: ["*"],
  })
);
localStorage.setItem("portal_token", "demo-token-admin");
location.reload();
```

Swap the persona object for any of the 8 personas in
[lib/auth/personas.ts](unified-trading-system-ui/lib/auth/personas.ts).

## Testing locally

```bash
# UI tests (headless)
cd unified-trading-system-ui && CI=true npm test -- --run

# Playbook Playwright specs (see testing/README.md)
cd unified-trading-system-ui && npx playwright test tests/playbooks/
```

## Related

- Canonical local dev: [../../08-workflows/local-dev.md](../../08-workflows/local-dev.md)
- Demo personas: [../authentication/README.md](../authentication/README.md)
- Playwright test suite: [../testing/README.md](../testing/README.md)

# Local dev

## Canonical source of truth

**The canonical local-dev doc is [../../08-workflows/local-dev.md](../../08-workflows/local-dev.md).** Do not duplicate
its contents here — read that doc for the full tier model (Tier 0/1/2/static), mode axes (`VITE_MOCK_API`,
`VITE_SKIP_AUTH`, `CLOUD_MOCK_MODE`, etc.), and presets.

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

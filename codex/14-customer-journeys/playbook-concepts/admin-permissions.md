---
doc_type: codex-ssot
title: Admin permissions — the gating model
summary:
  role === admin is NOT sufficient for destructive ops — a 10-permission admin_permissions Firebase custom-claim gates
  grant_role / rotate_secret / offboard_user / lock_strategy / ...; bootstrap seed admins fall back to legacy
  full-admin, scoped admins are deny-by-default via hasAdminPermission().
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [admin, permissions, authentication, ui, security, entitlements]
related:
  [
    /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md,
    /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md,
  ]
created: 2026-04-21
authoritative_for: [UI admin-permissions gating model (admin_permissions custom claim)]
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Admin permissions — the gating model

> **SSOT.** This file carries the admin permission model that gates destructive admin-only operations in the Odum
> Unified Trading System UI. Binary `role === "admin"` is NOT sufficient for destructive actions — callers must also
> carry a specific `admin_permissions` grant. This file is cited by `cross-cutting/visibility-slicing.md`, the admin
> fold-in plan (`plans/archive/ui_unification_v2_sanitisation_2026_04_20.plan.md` Phase 6), and the admin bootstrap
> scripts.

Admin accounts split into two classes:

1. **Legacy full-admin (bootstrap)** — the seed users (`ikenna@odum-research.com`, `femi@odum-research.com`) carry
   `role === "admin"` with NO `admin_permissions` claim. They pass every `hasAdminPermission` check by falling back to
   "legacy full admin" behaviour. This is the boot path before any scoped admins have been provisioned. See
   `scripts/admin/bootstrap-admin-user.mjs` for seeding.
2. **Scoped admins** — every admin provisioned after bootstrap carries `role === "admin"` PLUS a Firebase custom claim
   `admin_permissions: string[]` listing exactly the destructive operations they are permitted to perform. Missing
   permissions are denied — no escalation.

The goal: new admins cannot accidentally grant themselves the right to rotate secrets or offboard users without the
bootstrap admin explicitly extending their grant.

## Permissions

| Permission                  | What it gates                                                                         |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `admin:grant_role`          | Promoting a user to `role === "admin"` or granting additional `admin_permissions`     |
| `admin:create_org`          | Creating a new organisation / BU / client tenant                                      |
| `admin:lock_strategy`       | Toggling `lock_state` on strategy availability slots (PUBLIC → RESERVED and reverse)  |
| `admin:impersonate`         | Acting-as another user (`X-Acting-User-Email` header) for operational troubleshooting |
| `admin:rotate_secret`       | Rotating API keys, HMAC shared secrets, Firebase custom claims                        |
| `admin:modify_user`         | Editing another user's profile, entitlements, or persona override                     |
| `admin:offboard_user`       | Offboarding / disabling a user account; revokes tokens and entitlements               |
| `admin:view_audit`          | Reading the full audit log (all events across all orgs); read-only                    |
| `admin:manage_apps`         | Registering / editing / retiring applications in the app catalogue                    |
| `admin:manage_entitlements` | Granting / revoking application entitlements on users or groups                       |

The 10 permissions above are the complete set. Any new destructive action must first add a permission here and cite this
file.

## Firebase custom-claim schema

```json
{
  "role": "admin",
  "admin_permissions": [
    "admin:grant_role",
    "admin:create_org",
    "admin:lock_strategy",
    "admin:impersonate",
    "admin:rotate_secret",
    "admin:modify_user",
    "admin:offboard_user",
    "admin:view_audit",
    "admin:manage_apps",
    "admin:manage_entitlements"
  ]
}
```

- Bootstrap admins MAY omit the `admin_permissions` claim entirely (legacy full-admin fallback).
- Scoped admins MUST include the claim with the exact list of permissions granted. Empty array means `role === "admin"`
  with zero destructive rights (view-only admin).

## Runtime gate

`unified-trading-system-ui/lib/auth/admin-permissions.ts` exports `hasAdminPermission(user, permission)`. Callers gate
every destructive UI action via this helper:

```ts
import { hasAdminPermission } from "@/lib/auth/admin-permissions";
import { useAuth } from "@/hooks/use-auth";

const { user } = useAuth();

if (!hasAdminPermission(user, "admin:grant_role")) {
  return <PermissionDenied permission="admin:grant_role" />;
}
```

Rules:

1. Non-admin users (`role !== "admin"`) always fail every permission check.
2. Admin users with NO `admin_permissions` claim (undefined, not empty array) pass every check — bootstrap fallback.
3. Admin users with `admin_permissions === []` fail every destructive check (view-only admin).
4. Admin users with `admin_permissions` present pass only the checks whose permission appears in the array.

## Bootstrap pattern

The two seed admins are provisioned via `unified-trading-system-ui/scripts/admin/bootstrap-admin-user.mjs`:

- `ikenna@odum-research.com` — `role: "admin"`, `admin_permissions` set to the full permission set.
- `femi@odum-research.com` — same.

Both accounts explicitly set the full `admin_permissions` array even though the gate's bootstrap fallback would pass
them through anyway. The explicit claim future-proofs the accounts against a change in fallback behaviour and makes the
grant visible in audit logs.

## Granting / revoking permissions

Scoped admin permission grants happen through the admin UI at `/ops/admin/users/[id]/modify`:

1. Admin with `admin:grant_role` opens a target user's modify page.
2. UI renders a multi-select of the 10 permissions; current selections reflect Firebase custom-claim state.
3. On save, the UI calls the admin API `PATCH /users/:id/admin-permissions` with the new array.
4. The backend (server-side provider in `server/admin/providers.js`) updates the Firebase custom claim, logs an audit
   event `admin.permissions.granted` / `admin.permissions.revoked` with actor email and permission diff.
5. Target user sees the new permissions on next token refresh (Firebase ID tokens cache custom claims for ~1 hour —
   `getIdToken(true)` forces refresh).

Revoking an admin's entire access: remove `admin_permissions` (falls back to legacy full-admin — UNSAFE, don't do this
to deprovision) OR set `role: "client"` via the same modify page (fully removes admin access).

## Audit trail

Every grant/revoke writes an audit-log entry under `audit_events/{id}` with:

- `type`: `admin.permissions.granted` | `admin.permissions.revoked`
- `actor`: the admin performing the change
- `target`: the affected user
- `permissions_added` / `permissions_removed`: string arrays
- `timestamp`: ISO-8601
- `ip_address` + `user_agent`: from request context

The audit log is surfaced at `/ops/admin/audit-log` (see migrated page from user-management-ui).

## Related

- `cross-cutting/visibility-slicing.md` — how admin sees everything while clients see slices.
- `shared-core/signal-broadcast-architecture.md` — HMAC key rotation uses `admin:rotate_secret`.
- `plans/archive/ui_unification_v2_sanitisation_2026_04_20.plan.md` Phase 6 — delivery plan.

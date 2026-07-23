# Child execution plan — Five-space IA, preview removal, IR, catalogue API

> **Canonical playbook SSOT**: see [codex/14-playbooks/](/codex/14-playbooks/README.md) for the playbook families,
> environments, and auth tiers this plan integrates with. Ticket #12 (staging Firebase) and ticket #4 (/briefings hub)
> are referenced from [/codex/14-playbooks/roadmap/next-waves.md](/codex/14-playbooks/roadmap/next-waves.md).

Ordered backlog derived from the meta-plan (charter lives in the user’s plan file; **do not** treat this as replacing
that charter). Tags: **`[UI]`** · **`[API]`** · **`[Infra]`** · **`[Docs]`** · **`[No-backend]`**

## P0 — Shipped in this tranche (reference PR)

| #   | Ticket                                                                                        | Tag      | Notes                                    |
| --- | --------------------------------------------------------------------------------------------- | -------- | ---------------------------------------- |
| 1   | Remove global Preview banner; keep `RuntimeModeBadge` / mock honesty scoped                   | `[UI]`   | Root `app/layout.tsx`                    |
| 2   | Public marketing copy pass (“preview/demo” → walkthrough / live positioning)                  | `[UI]`   | `(public)/*`, selected `public/*.html`   |
| 3   | Staging allowlist + proxy matcher for `/briefings`                                            | `[UI]`   | `staging-gate.tsx`, `proxy.ts`           |
| 4   | Lighter-gate hub `/briefings` + three pillars; JSON v1; optional env invite gate              | `[UI]`   | Separate `localStorage` key              |
| 5   | Shell “Spaces” navigation (public header + signed-in lifecycle bar)                           | `[UI]`   |                                          |
| 6   | IR index: four pillars, Current vs Archive, filters; `investor-archive`                       | `[UI]`   | `lib/config/auth.ts`, personas           |
| 7   | IR Pillar 3 deck: `/investor-relations/site-navigation`                                       | `[UI]`   | Entitlement `investor-board`             |
| 8   | Absorption map (existing decks → pillars)                                                     | `[Docs]` | Section below                            |
| 9   | Strategy catalogue: API hook + env `NEXT_PUBLIC_STRATEGY_CATALOG_SOURCE`, merge with fixtures | `[UI]`   | Uses `/api/analytics/strategies/catalog` |
| 10  | DEPLOYMENT.md: five-space map, env matrix, mock/reporting grep summary                        | `[Docs]` |                                          |
| 11  | SECURITY_AUTH.md: provisioning threat model, no self-elevation, GCP IAM pointers              | `[Docs]` |                                          |

## P1 — Next (requires infra or backend ownership)

| #   | Ticket                                                              | Tag       | Owner hint               | Status (2026-04-18)                                                                                                                                                                                                              |
| --- | ------------------------------------------------------------------- | --------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 12  | Dedicated **staging Firebase** project + env bake                   | `[Infra]` | Platform / GCP           | **Repo done:** `config/docker-build.env.staging.firebase.example`, `deploy-cloud-run.sh --build-env-file=`, `DEPLOYMENT.md` cutover. **Ops:** create Firebase project + authorized domains + gitignored env + deploy.            |
| 13  | Provisioning API: allowlist for admin / `*` entitlements; audit log | `[API]`   | Auth / user-mgmt service | **In-repo:** `deployment-api` (`ORG_OWNER_EMAILS`, acting user middleware, route guards, audit); `user-management-ui` server + client header. **Other:** service at `NEXT_PUBLIC_AUTH_URL` if not proxied to these.              |
| 14  | Firestore / GCS rules review — end-user token blast radius          | `[Infra]` | Security                 | **Checklist in repo:** `unified-trading-system-ui/docs/SECURITY_AUTH.md` (Data plane review). **Ops:** apply rules in GCP for each Firebase project.                                                                             |
| 15  | IR archive metadata route (read-only)                               | `[API]`   | `client-reporting-api`   | **Shipped:** `GET /api/reporting/investor-relations/archive-metadata` + JSON under `client_reporting_api/api/routes/reporting/data/`; portal merges via `useIrArchiveMetadata` + `mergeIrDeckMetadata` on `/investor-relations`. |

## Absorption map — IR decks → four pillars

| Existing route                                                                | Pillar (1–4) or standalone            | Action                                                                                    |
| ----------------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------- |
| `board-presentation`                                                          | **1** How we got here                 | Keep; canonical for history / opportunity                                                 |
| `plan-presentation`                                                           | **2** Where we are going              | Keep; roadmap / readiness                                                                 |
| `site-navigation` (new)                                                       | **3** Portal / website concept        | Keep; sync with IA + audit matrix                                                         |
| `investment-presentation`, `platform-presentation`, `regulatory-presentation` | **2** (readiness) + audience-specific | **Link** from pillar 2; keep standalone routes for client-specific legal/commercial depth |
| `disaster-recovery`                                                           | **4** DR / security / tech            | Keep standalone; pillar 4 summary should **deep-link** here                               |

Overlap rule: merge narrative in the pillar index first; do not delete standalone decks without legal/commercial
sign-off.

## Env gates (per ticket)

| Ticket          | dev                                                     | staging                                            | prod                                                             |
| --------------- | ------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------- |
| Catalogue API   | `STRATEGY_CATALOG_SOURCE` optional; respects `MOCK_API` | Recommend `mock` unless API reachable from staging | Recommend `api` + `MOCK_API=false`                               |
| Briefing invite | Omit env → open                                         | Set `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` if needed   | Usually omit                                                     |
| IR archive      | `investor-archive` on investor persona for QA           | Same                                               | Capability `investor.archive` → entitlement (when backend ready) |

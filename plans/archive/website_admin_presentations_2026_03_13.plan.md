---
doc_type: plan
title: website-admin-presentations-2026-03-13
summary: 'Add secure portal section to odum-research-website with role-based presentation access. Roles: admin (all), board
  (strategic decks), client:{slug} (product-specific e.g. Elysium DeFi), shareholder, accounting (financials), operations
  (company docs), investor (investment mgmt + doc upload). Auth via unified-admin-ui/packages/core (Google OAuth + Cognito).'
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-13'
type: code
epic: epic-website
superseded_by: website_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: D1, business: none}
repo_gates:
- {repo: odum-research-website, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: portal goes live alongside domain migration (Plan 3). BR N/A: no commercial KPI — internal access control.'}
- {repo: unified-admin-ui, code: C0, deployment: none, business: none, readiness_note: Add role definitions to packages/core/auth/roles.ts.}
depends_on: [website-repo-integration-2026-03-13, board-presentations-update-2026-03-10]
todos:
- {id: define-role-schema, content: 'Add roles to unified-admin-ui/packages/core/auth/roles.ts: admin, board, client:{slug} (parameterised), shareholder, accounting, operations, investor. Each role has a list of presentation slugs they can access.', status: todo, note: ''}
- {id: define-presentation-metadata, content: 'Create odum-research-website/src/data/presentations.json. Each entry: { id, title, file, description, roles[] }. Roles[] = which roles can see this presentation. Cover all current 10 presentations (00–09) + Elysium deck (10) + 3 new board decks (11–13) + shareholder-report.', status: todo, note: See board_presentations_update_2026_03_10 for deck 11-13 status.}
- {id: sync-presentations-script, content: Add script odum-research-website/scripts/sync-presentations.sh. Copies/syncs unified-trading-pm/presentations/*.html → odum-research-website/public/presentations/. Run as part of CI on changes to either repo. Keeps presentation files in sync automatically., status: todo, note: ''}
- {id: build-portal-page, content: 'Add PortalPage.tsx to odum-research-website/src/pages/. Auth-gated (RequireAuth wrapper). Shows role-filtered presentation cards. Each card: title, description, thumbnail (or icon), "View" button. Sections: Strategic Presentations, DeFi & Product Decks, Shareholder/Financial Reports, Company Docs.', status: todo, note: ''}
- {id: build-presentation-viewer, content: 'Add PresentationViewer.tsx: iframe embed for HTML presentation files hosted as static assets. Breadcrumb nav: Portal → Presentation Title. Full-screen button. Back to portal link.', status: todo, note: ''}
- {id: integrate-auth, content: 'Wire @unified-admin/core auth into odum-research-website. Add RequireAuth HOC wrapping all /portal/* routes. Login page: Google OAuth + Cognito PKCE options (matching deployment-ui pattern).', status: todo, note: 'Auth already implemented in unified-admin-ui/packages/core — import, don''t re-implement.'}
- {id: add-company-docs-section, content: 'Operations role: secure section for company docs (licences, certificates, proof of address, regulatory docs). Implement as static links to GCS bucket (restricted IAM) or inline viewer. Admin: can upload docs. Operations: read-only.', status: todo, note: ''}
- {id: add-investor-doc-upload, content: 'Investor role: document upload flow for KYC/AML docs. Upload to GCS bucket odum-research-investor-docs-{env} (restricted IAM — investor SA only). Show upload status (pending review, approved, rejected). Admin: can view all uploaded docs + update status.', status: todo, note: ''}
- {id: add-client-registry-admin, content: 'Admin-only page: assign users to roles + product_slugs. Table: user email | role | product slugs | provisioned services | edit button. Saves to user registry (JSON file in GCS or lightweight DB). This maps to presentation access for client:{slug} roles.', status: todo, note: ''}
- {id: shareholder-deck-stub, content: 'Create placeholder unified-trading-pm/presentations/shareholder-report-2026.html. Stub content: company overview, key metrics, financial highlights (TBD). Formatted to match existing presentation style.', status: todo, note: Content TBD — stub so role-based access can be wired before content is ready.}
- {id: e2e-tests, content: 'Playwright smoke tests: (1) Admin: sees all presentations including board decks + company docs (2) Elysium client (client:elysium): sees only Elysium DeFi deck, not board decks (3) Shareholder: sees only shareholder-report-2026.html (4) Investor: sees investment management deck + upload form; can upload a test PDF (5) Unauthenticated user: redirected to login page', status: todo, note: ''}
- {id: quality-gate-pass, content: bash scripts/quality-gates.sh passes in odum-research-website; merge., status: todo, note: ''}
isProject: false
---

# Plan: Odum Research Website — Presentations Portal

## Context

The PM repo has 10+ HTML presentation files covering all aspects of the Odum Research platform. These presentations are
currently only accessible internally. We need a secure portal on the website where different stakeholders can access
relevant presentations based on their relationship with Odum.

**Implementer: Femi Amoo**

---

## Role → Presentation Access Matrix

| Role             | Presentations Accessible                                                    |
| ---------------- | --------------------------------------------------------------------------- |
| `admin`          | All — 00–13, Elysium deck, shareholder report, company docs                 |
| `board`          | 00-master, 01–09 strategic decks, 13-status-quo-traction                    |
| `client:elysium` | 10-defi-elysium.html (from elysium_defi_presentation plan)                  |
| `client:{slug}`  | Product-specific presentations per slug mapping                             |
| `shareholder`    | shareholder-report-2026.html                                                |
| `accounting`     | 12-financials-projections.html                                              |
| `operations`     | Company docs (licences, regulatory certificates, proof of address)          |
| `investor`       | 05-investment-management.html + 12-financials-projections.html + doc upload |

---

## presentations.json Structure

```json
[
  {
    "id": "01-data-provision",
    "title": "Data Provision",
    "file": "/presentations/01-data-provision.html",
    "description": "100TB+ financial data infrastructure across 33 venues",
    "roles": ["admin", "board"]
  },
  {
    "id": "10-defi-elysium",
    "title": "DeFi Platform — Elysium",
    "file": "/presentations/10-defi-elysium.html",
    "description": "DeFi-only platform for Elysium Capital",
    "roles": ["admin", "client:elysium"]
  },
  {
    "id": "shareholder-report-2026",
    "title": "Shareholder Report 2026",
    "file": "/presentations/shareholder-report-2026.html",
    "description": "Annual shareholder update",
    "roles": ["admin", "shareholder"]
  }
]
```

---

## Portal Route Structure

```
/portal                     → PortalPage.tsx (auth-gated, role-filtered cards)
/portal/:presentationId     → PresentationViewer.tsx (iframe viewer)
/portal/admin/users         → ClientRegistryPage.tsx (admin-only user management)
/portal/admin/docs          → CompanyDocsPage.tsx (admin: upload; ops: read)
/portal/investor/upload     → InvestorDocUpload.tsx (investor: KYC/AML upload)
```

---

## Auth Integration

Reuses `@unified-admin/core` auth (already wired in deployment-ui):

```ts
import { RequireAuth, useAuth } from '@unified-admin/core'
// Gate portal routes:
<RequireAuth><PortalPage /></RequireAuth>
// Check role-based access inside page:
const { user } = useAuth()
const accessible = presentations.filter(p => p.roles.some(r => userHasRole(user, r)))
```

---

## Verification Gates

- [ ] Unauthenticated `/portal` → redirected to login
- [ ] Admin login → all cards visible
- [ ] Elysium client login → only Elysium deck card visible
- [ ] Shareholder login → only shareholder report card visible
- [ ] Investor → investment deck + upload form visible; test PDF upload succeeds
- [ ] `bash scripts/quality-gates.sh` exits 0 in odum-research-website + unified-admin-ui

## Files Created / Modified

- `odum-research-website/src/pages/PortalPage.tsx` (new)
- `odum-research-website/src/pages/PresentationViewer.tsx` (new)
- `odum-research-website/src/data/presentations.json` (new)
- `odum-research-website/scripts/sync-presentations.sh` (new)
- `unified-admin-ui/packages/core/auth/roles.ts` (modified — add role definitions)
- `unified-trading-pm/presentations/shareholder-report-2026.html` (new stub)

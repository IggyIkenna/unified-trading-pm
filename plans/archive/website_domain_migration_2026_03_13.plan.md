---
doc_type: plan
title: website-domain-migration-2026-03-13
summary: Migrate odum-research-website from Yell hosting to self-managed odum-research.com. odum-research.co.uk becomes
  password-protected staging (public sees redirect message). odum-group.io forwarding kept. Cancel Yell after cutover.
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-13'
type: infra
epic: epic-website
superseded_by: website_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: D2, business: B1}
repo_gates:
- {repo: odum-research-website, code: C0, deployment: none, business: none, readiness_note: 'DR: production cutover to odum-research.com is the deployment gate. BR: user confirms Yell cancelled.'}
depends_on: [website-repo-integration-2026-03-13, website-content-refresh-2026-03-13]
todos:
- {id: audit-yell-setup, content: 'Log into Yell account. Document DNS records for odum-research.co.uk and odum-research.com: A records, CNAME, MX, TTL values. Note current nameservers. Identify Yell cancellation process and notice period. Save DNS snapshot to odum-research-website/docs/dns-snapshot-pre-migration.md.', status: todo, note: 'Human action: requires Yell account login.'}
- {id: choose-hosting-target, content: 'Select self-managed hosting based on stack audit from Plan 1. Vercel: recommended if static/Next.js (free tier sufficient, auto-SSL, branch previews). Cloud Run: if SSR with backend. GCS + CDN: if purely static. Decision logged in odum-research-website/docs/hosting-decision.md.', status: todo, note: ''}
- {id: setup-hosting-infra, content: 'Configure chosen hosting. Connect eggyakana/odum-research-website repo. Set up build pipeline: auto-deploy on push to main branch. Configure environment variables (if any). Set up preview deployments for PRs.', status: todo, note: ''}
- {id: setup-ssl, content: Provision SSL certificate for odum-research.com (auto via Vercel/Let's Encrypt). Also provision for www.odum-research.com. Verify SSL grade A on ssllabs.com after cutover., status: todo, note: ''}
- {id: staging-deploy, content: 'Deploy current odum-research.co.uk content to new hosting on a staging URL. QA all pages: homepage, about, services, contact. Check mobile responsiveness. Verify no broken images or links.', status: todo, note: ''}
- {id: dns-cutover-com, content: 'Update DNS A/CNAME records for odum-research.com to new hosting IP/CNAME. Update www.odum-research.com to redirect to apex. Set TTL to 300 (5 min) before cutover, restore to 3600 after. Allow 24–48h for propagation. Verify with: dig odum-research.com +short', status: todo, note: ''}
- {id: setup-co-uk-staging-gate, content: 'Replace odum-research.co.uk public content with a password-protected staging page. Public visitors (no password) see: "We''ve moved to odum-research.com — please visit us there." Include a link to odum-research.com. Team access: HTTP Basic Auth or simple password page for staging site. Prevents public seeing in-progress work on staging. Implementation: hosting provider password protection (Vercel: basic auth middleware or _redirects).', status: todo, note: ''}
- {id: verify-cutover, content: 'Verify: (1) odum-research.com serves from new hosting with SSL valid. (2) www.odum-research.com redirects to apex. (3) odum-research.co.uk shows public redirect message to unauthenticated visitors. (4) odum-research.co.uk accessible with staging password. (5) odum-group.io still forwards to odum-research.com.', status: todo, note: ''}
- {id: cancel-yell, content: 'Cancel Yell hosting subscription after confirming 2-week clean operation on new hosting. Document cancellation date in odum-research-website/docs/infrastructure.md. Note: retain domain registrar access (we own both domains — only cancel hosting, not domain registration).', status: todo, note: Human action. Confirm with user before cancelling.}
- {id: verify-odum-group-io, content: 'Confirm odum-group.io still forwards to odum-research.com after all DNS changes. Test in browser: https://odum-group.io → should redirect to https://odum-research.com. Keep this forwarding permanently.', status: todo, note: odum-group.io currently forwards to odum-research.com — preserve after migration.}
- {id: update-workspace-manifest, content: 'Update odum-research-website entry in workspace-manifest.json: add deployment_url=https://odum-research.com, hosting=vercel (or chosen provider).', status: todo, note: ''}
isProject: false
---

# Plan: Odum Research Website — Domain Migration

## Context

The odum-research website is currently hosted by Yell on both `odum-research.co.uk` (staging) and `odum-research.com`
(target production). We own both domains and pay Yell to host them.

Goal: move to self-managed hosting (recommended: Vercel), cut DNS over to `odum-research.com`, make
`odum-research.co.uk` a password-protected staging site (public sees a redirect page), keep `odum-group.io` forwarding
permanently, and cancel Yell.

**Implementer: Femi Amoo**

---

## Domain Summary

| Domain                  | Current                       | After Migration                                           |
| ----------------------- | ----------------------------- | --------------------------------------------------------- |
| `odum-research.com`     | Yell-hosted production target | Self-managed (Vercel/Cloud Run/GCS) — PRIMARY             |
| `odum-research.co.uk`   | Yell-hosted staging           | Password-protected staging (public sees redirect message) |
| `odum-group.io`         | Forwards to odum-research.com | Keep forwarding permanently — no change                   |
| `www.odum-research.com` | TBD                           | 301 → apex odum-research.com                              |

---

## Staging Gate — odum-research.co.uk

Public visitor (no password):

```
┌──────────────────────────────────────────────────┐
│  We've moved!                                    │
│                                                  │
│  Visit us at: odum-research.com                 │
│  [→ Go to odum-research.com]                    │
└──────────────────────────────────────────────────┘
```

Team access: HTTP Basic Auth (username/password stored in `.env` — not committed).

---

## Verification Gates

- [ ] `curl -I https://odum-research.com` returns 200, SSL valid
- [ ] `curl -I https://www.odum-research.com` returns 301 → apex
- [ ] `curl -I https://odum-research.co.uk` (no auth) returns redirect message page
- [ ] `curl -I https://odum-group.io` returns redirect to odum-research.com
- [ ] Yell subscription cancelled; confirmation email saved
- [ ] `workspace-manifest.json` odum-research-website entry has `deployment_url`

## Files Created / Modified

- `odum-research-website/docs/dns-snapshot-pre-migration.md` (new)
- `odum-research-website/docs/hosting-decision.md` (new)
- `odum-research-website/docs/infrastructure.md` (new)
- `odum-research-website/src/pages/StagingGate.tsx` (or equivalent — staging redirect page)
- `workspace-manifest.json` (modified — add deployment_url)

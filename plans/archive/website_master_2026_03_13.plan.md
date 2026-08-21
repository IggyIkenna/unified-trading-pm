---
doc_type: plan
title: website-master-2026-03-13
summary: 'Consolidates all website-related plans: odum-research-website repo integration into workspace manifest, content
  refresh with current system capabilities, domain migration from Yell to self-managed hosting, hosting board presentations
  on the website, and admin portal with role-based access (7 roles).'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-13'
type: business
epic: epic-business
completion_gates: {code: C3, deployment: D3, business: B4}
repo_gates:
- {repo: odum-research-website, code: C3, deployment: D3, business: B4, readiness_note: 'Integrated into workspace. QG green, 72% coverage, 101 tests. Awaiting DNS migration for production deploy.'}
depends_on: [presentations_2026_03_13]
supersedes: [website_repo_integration_2026_03_13, website_content_refresh_2026_03_13, website_domain_migration_2026_03_13, website_admin_presentations_2026_03_13]
todos:
- {id: website-team-photos, content: '- [ ] [HUMAN] P2. Collect team photos (400x400px JPEG) for 6 members: Ikenna Igboaka, Robert Osborne, Shaun Lim, Julian John, Femi Amoo, Harsh. Place in public/team/ and update src/app/page.tsx to replace grey initials placeholders. See docs/website-photo-requirements.md.

    ', status: pending}
- {id: website-description-update, content: '- [ ] [HUMAN] P2. Review and update team member bios and service descriptions on the landing page (src/app/page.tsx). Current bios are placeholder text — replace with accurate descriptions.

    ', status: pending}
- {id: website-domain-migration, content: '- [ ] [HUMAN] P2. Switch DNS from Yell to self-managed hosting. Migrate from odum-research.co.uk to odum-research.com (primary domain: odum-research.com). (1) Audit Yell DNS records. (2) Choose hosting (Cloud Run or Vercel). (3) Configure hosting with auto-deploy on push to main. (4) DNS cutover: set TTL to 300, update A/CNAME, restore after propagation. (5) odum-research.co.uk redirects to odum-research.com. (6) SSL provisioning. (7) Cancel Yell after 2-week clean operation.

    ', status: pending}
---

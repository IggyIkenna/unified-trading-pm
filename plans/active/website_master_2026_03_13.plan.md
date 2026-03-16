---
name: website-master-2026-03-13
overview: >
  Consolidates all website-related plans: odum-research-website repo integration into workspace manifest, content
  refresh with current system capabilities, domain migration from Yell to self-managed hosting, hosting board
  presentations on the website, and admin portal with role-based access (7 roles).
type: business
epic: epic-business
status: active

completion_gates:
  code: C3
  deployment: D3
  business: B4

repo_gates:
  - repo: odum-research-website
    code: C3
    deployment: D3
    business: B4
    readiness_note: "New repo. Must be cloned, integrated into manifest, and deployed."

depends_on:
  - presentations_2026_03_13
  # Blocker: Plan 4 (Presentations) must complete before hosting presentations on website.

supersedes:
  - website_repo_integration_2026_03_13
  - website_content_refresh_2026_03_13
  - website_domain_migration_2026_03_13
  - website_admin_presentations_2026_03_13

todos:
  - id: website-repo-integration
    content: >
      - [ ] [AGENT] P1. Clone odum-research-website repo into workspace. Add to workspace-manifest.json with type:
      infrastructure, arch_tier: infrastructure. Set up quality-gates.sh (UI type), GitHub Actions workflows. Verify:
      repo appears in manifest, QG passes.
    status: pending

  - id: website-content-refresh
    content: >
      - [ ] [HUMAN+AGENT] P2. Update all website pages with current system capabilities: 67 repos, multi-cloud
      architecture, 33 venue coverage, ML pipeline, DeFi protocol support. Update team page, technology stack page, and
      case studies.
    status: pending
    depends_on: [website-repo-integration]

  - id: website-domain-migration
    content: >
      - [ ] [HUMAN] P2. Migrate domain from Yell to self-managed hosting. Set up: odum-research.com as primary domain,
      odum-research.co.uk redirects to .com. DNS configuration, SSL certificate, hosting provider selection (Cloud Run
      or Vercel).
    status: pending

  - id: website-host-presentations
    content: >
      - [ ] [AGENT] P2. Host board presentations on the website. Create `/presentations` route with access control.
      Presentations served as static HTML from Plan 4 deliverables. Requires Plan 4 completion.
    status: pending
    depends_on: [website-content-refresh]

  - id: website-admin-portal
    content: >
      - [ ] [AGENT] P3. Admin portal with role-based access. 7 roles: super-admin, admin, board-member, investor,
      partner, developer, viewer. Authentication via OAuth2. Portal features: presentation management, user management,
      analytics dashboard.
    status: pending
    depends_on: [website-host-presentations]

  - id: website-stack-audit
    content: >
      - [ ] [AGENT] P1. Inspect datadodo/odum_website repo: detect tech stack (Next.js, static HTML, CMS), package
      manager, build system, existing CI. Document findings in odum-research-website/docs/stack.md. Create
      eggyakana/odum-research-website GitHub repo (private). Clone datadodo/odum_website preserving git history.
      Re-point remote to eggyakana org.
    status: pending
    depends_on: []

  - id: website-workspace-config-files
    content: >
      - [ ] [AGENT] P1. Add odum-research-website to workspace configs: (1) workspace-manifest.json entry with type=ui,
      arch_tier=ui, cluster=website, org=eggyakana, merge_level=11, status=active. (2) Add to
      workspace-uis.code-workspace and workspace-complete.code-workspace. (3) Create
      unified-trading-codex/10-audit/repos/odum-research-website.yaml. (4) Add .github/workflows/quality-gates.yml.
    status: pending
    depends_on: [website-stack-audit]

  - id: website-content-refresh-detail
    content: >
      - [ ] [HUMAN+AGENT] P2. Content refresh detail: About/Team page with 6 member slots (Shaun Lim, Julian John, Femi
      Amoo, Harsh, Robert Osborne, Ikenna Igboaka) with grey initials placeholder. Services section sourced from
      presentations 05 and 06. Preserve hero tagline: "Odum carries two meanings: the lion for strength and the tree for
      rooted innovation." Traction bar: "8 active strategy clients, Edge Capital fund-to-fund, Indian options mandate,
      live March 2026, 33 venues, 60+ repos." Create docs/website-photo-requirements.md (400x400px JPEG) and
      docs/brand-tokens.md. Deploy to staging only.
    status: pending
    depends_on: [website-repo-integration]

  - id: website-domain-migration-detail
    content: >
      - [ ] [HUMAN] P2. Domain migration detail: (1) Audit Yell DNS records for odum-research.co.uk and
      odum-research.com, save to docs/dns-snapshot-pre-migration.md. (2) Choose hosting (Vercel recommended for
      static/Next.js), log in docs/hosting-decision.md. (3) Configure hosting with auto-deploy on push to main and PR
      preview deployments. (4) Staging deploy to verify. (5) DNS cutover: set TTL to 300, update A/CNAME, restore to
      3600 after 24-48h propagation. Verify: curl -I (200+SSL), www redirect (301), dig +short. (6) odum-research.co.uk:
      StagingGate with "We've moved" message, team access via HTTP Basic Auth. (7) Verify odum-group.io forwarding. (8)
      Cancel Yell only after 2-week clean operation, retain domain registrar access. (9) Update manifest with
      deployment_url. (10) SSL provisioning, verify grade A on ssllabs.com.
    status: pending
    depends_on: [website-content-refresh]

  - id: website-admin-portal-detail
    content: >
      - [ ] [AGENT] P3. Admin portal detail: (1) Add 7 role definitions to unified-admin-ui/packages/core/auth/roles.ts
      (admin, board, client:{slug}, shareholder, accounting, operations, investor). (2) Create
      odum-research-website/src/data/presentations.json with schema {id, title, file, description, roles[]} covering all
      14 presentations. (3) Create scripts/sync-presentations.sh (copies presentations/*.html to public/presentations/).
      (4) Build PortalPage.tsx (auth-gated, role-filtered cards in 4 sections). (5) Build PresentationViewer.tsx
      (iframe, breadcrumb, full-screen). (6) Wire auth from @unified-admin/core (matching deployment-ui pattern).
      Routes: /portal, /portal/:id, /portal/admin/users, /portal/admin/docs, /portal/investor/upload. (7) Company docs
      section with GCS bucket. (8) Investor doc upload with KYC/AML status tracking. (9) Admin client registry page.
      (10) Create shareholder-report-2026.html stub. (11) 5 Playwright smoke tests
      (admin/client:elysium/shareholder/investor/unauthenticated).
    status: pending
    depends_on: [website-host-presentations]
---

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
      [AGENT] P1. Clone odum-research-website repo into workspace. Add to workspace-manifest.json with type:
      infrastructure, arch_tier: infrastructure. Set up quality-gates.sh (UI type), GitHub Actions workflows. Verify:
      repo appears in manifest, QG passes.
    status: pending

  - id: website-content-refresh
    content: >
      [HUMAN+AGENT] P2. Update all website pages with current system capabilities: 65 repos, multi-cloud architecture,
      33 venue coverage, ML pipeline, DeFi protocol support. Update team page, technology stack page, and case studies.
    status: pending
    depends_on: [website-repo-integration]

  - id: website-domain-migration
    content: >
      [HUMAN] P2. Migrate domain from Yell to self-managed hosting. Set up: odum-research.com as primary domain,
      odum-research.co.uk redirects to .com. DNS configuration, SSL certificate, hosting provider selection (Cloud Run
      or Vercel).
    status: pending

  - id: website-host-presentations
    content: >
      [AGENT] P2. Host board presentations on the website. Create `/presentations` route with access control.
      Presentations served as static HTML from Plan 4 deliverables. Requires Plan 4 completion.
    status: pending
    depends_on: [website-content-refresh]

  - id: website-admin-portal
    content: >
      [AGENT] P3. Admin portal with role-based access. 7 roles: super-admin, admin, board-member, investor, partner,
      developer, viewer. Authentication via OAuth2. Portal features: presentation management, user management, analytics
      dashboard.
    status: pending
    depends_on: [website-host-presentations]
---

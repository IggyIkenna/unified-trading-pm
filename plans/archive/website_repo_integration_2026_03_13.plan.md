---
doc_type: plan
title: website-repo-integration-2026-03-13
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-13'
overview: Clone datadodo/odum_website to eggyakana/odum-research-website. Integrate into workspace manifest with quality gates, CI/CD, workspace config files, and codex checklist.
type: infra
epic: epic-website
superseded_by: website_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: D1, business: none}
repo_gates:
- {repo: odum-research-website, code: C0, deployment: none, business: none, readiness_note: 'New repo — quality gates TBD after tech stack audit. DR N/A: hosting setup in website_domain_migration plan. BR N/A: internal infra.'}
depends_on: []
todos:
- {id: audit-odum-website-stack, content: 'Inspect datadodo/odum_website repo: detect tech stack (Next.js, static HTML, CMS, etc.), dependencies, build system, existing CI. Document findings in odum-research-website/docs/stack.md.', status: todo, note: ''}
- {id: create-eggyakana-repo, content: Create eggyakana/odum-research-website GitHub repo (private initially). Push clone of datadodo/odum_website preserving git history as initial commit., status: todo, note: ''}
- {id: add-to-workspace-manifest, content: 'Add odum-research-website entry to workspace-manifest.json: type=ui, arch_tier=ui, cluster=website, org=eggyakana, github_url=https://github.com/eggyakana/odum-research-website, status=active.', status: todo, note: ''}
- {id: setup-quality-gates, content: 'Add scripts/quality-gates.sh appropriate for tech stack (eslint, prettier, vitest/jest if applicable). bash scripts/quality-gates.sh must pass from repo root.', status: todo, note: ''}
- {id: setup-cicd, content: Add .github/workflows/quality-gates.yml (PR check on push/PR to main). Add cloudbuild.yaml or buildspec.aws.yaml per workspace template., status: todo, note: ''}
- {id: add-to-workspace-configs, content: Add odum-research-website to workspace-uis.code-workspace and workspace-complete.code-workspace under unified-trading-pm/cursor-configs/., status: todo, note: ''}
- {id: add-codex-checklist, content: 'Create unified-trading-codex/10-audit/repos/odum-research-website.yaml with initial checklist (cr=C0, dr=none, br=none).', status: todo, note: ''}
- {id: update-index, content: Add all 5 website/access plans (85–89) to unified-trading-pm/plans/active/INDEX.md under a new Website & Access section., status: done, note: Added in same session as plan creation.}
isProject: false
---

# Plan: Odum Research Website — Repo Integration

## Context

The `odum-research.co.uk` website currently lives in `datadodo/odum_website` on GitHub and is hosted by Yell. It is not
part of the unified trading system workspace. Goal: bring it in as `eggyakana/odum-research-website` under the workspace
manifest so it benefits from CI/CD, quality gates, workspace config management, and the same governance as all other
repos.

This is the foundation plan — Plans 2–4 (content refresh, domain migration, presentations portal) all depend on it.

**Implementer: Femi Amoo**

---

## Phase 1: Stack Audit

Inspect `datadodo/odum_website` before making any changes. Determine:

- Build system (Next.js/Gatsby/Vite/static HTML)
- Package manager (npm/yarn/pnpm)
- Any existing CI config
- Dependencies and their versions

Document in `odum-research-website/docs/stack.md`.

---

## Phase 2: Repo Creation

```bash
# Clone with history
git clone https://github.com/datadodo/odum_website.git odum-research-website
cd odum-research-website

# Create new remote
gh repo create eggyakana/odum-research-website --private
git remote set-url origin https://github.com/eggyakana/odum-research-website.git
git push -u origin main
```

---

## Phase 3: Workspace Integration

### workspace-manifest.json entry

```json
{
  "name": "odum-research-website",
  "org": "eggyakana",
  "type": "ui",
  "arch_tier": "ui",
  "cluster": "website",
  "version": "0.1.0",
  "version_source": "package.json",
  "merge_level": 11,
  "status": "active",
  "github_url": "https://github.com/eggyakana/odum-research-website",
  "description": "Odum Research public website — odum-research.com. React/Next.js (TBD based on stack audit).",
  "dependencies": [],
  "notes": "Created 2026-03-13. eggyakana org (public-facing brand). Hosted on self-managed platform after domain migration plan."
}
```

---

## Phase 4: Quality Gates

After stack audit, add `scripts/quality-gates.sh` matching the tech stack:

```bash
#!/usr/bin/env bash
set -euo pipefail
# Adapt based on stack audit results
npm run lint         # eslint
npm run typecheck    # tsc --noEmit (if TypeScript)
npm run test         # vitest or jest
npx prettier --check src/
```

---

## Verification Gates

- [ ] `gh repo view eggyakana/odum-research-website` succeeds
- [ ] `bash scripts/quality-gates.sh` exits 0 from repo root
- [ ] `workspace-manifest.json` contains `odum-research-website` entry
- [ ] `workspace-uis.code-workspace` includes `odum-research-website` folder
- [ ] `unified-trading-codex/10-audit/repos/odum-research-website.yaml` exists

## Files Created / Modified

- `workspace-manifest.json` (modified)
- `unified-trading-pm/cursor-configs/workspace-uis.code-workspace` (modified)
- `unified-trading-pm/cursor-configs/workspace-complete.code-workspace` (modified)
- `unified-trading-codex/10-audit/repos/odum-research-website.yaml` (new)
- `odum-research-website/scripts/quality-gates.sh` (new)
- `odum-research-website/.github/workflows/quality-gates.yml` (new)
- `odum-research-website/docs/stack.md` (new)

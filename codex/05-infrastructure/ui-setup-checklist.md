---
doc_type: codex-ssot
title: UI Setup Checklist
summary:
  Bootstrap checklist for a UI repo (Next.js/React/TS) from clean clone to dev-serving — Node/Java/gcloud prereqs, npm
  install + generate:types, the .env.local shapes per UI, dev-tiers.sh startup, the mandatory vitest pool:forks rule,
  and type-regen after API changes.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, runbook, infrastructure, quality-gates, onboarding]
related:
  [
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
    /codex/08-workflows/local-dev.md,
    /codex/05-infrastructure/ui-architecture.md,
  ]
created: 2026-03-27
authoritative_for: [UI repo setup/bootstrap checklist]
referenced_by:
  [
    /codex/05-infrastructure/README.md,
    /codex/05-infrastructure/library-setup-checklist.md,
    /codex/05-infrastructure/new-repo-setup.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# UI Setup Checklist

Bootstrap a UI repo (Next.js / React / TypeScript) from clean clone to dev-serving-on-localhost.

> **Active UI repos (post-consolidation 2026-05-08)**: `unified-trading-system-ui` (consolidated portal) +
> `deployment-ui` + `user-management-ui`. The 13-UI legacy inventory is archived (see `DEPRECATED_UIS_NOTICE.md`).

## One-time prerequisites

1. **Node + npm**: Node ≥ 20 LTS. `nvm use 20` if you use nvm.
2. **Java 17 or 21** (for Firebase emulator JARs only): `brew install openjdk@21` on macOS. Emulators fail with a
   cryptic "exec format error" if Java is missing; the `dev-tiers.sh` startup script will print a remediation hint.
3. **gcloud SDK** (for the deployment-ui ↔ deployment-api real-cloud-mode path):
   `brew install --cask google-cloud-sdk` + `gcloud auth application-default login`.

## Per-clone bootstrap

```bash
cd <ui-repo>
npm install                          # install dependencies
cp .env.local.example .env.local     # if the repo ships a template; otherwise create empty .env.local
npm run generate:types               # regenerates `lib/types/api-generated.ts` from openapi.json
                                     # (idempotent; re-run after any unified-trading-api OpenAPI change)
```

### `.env.local` shape

For `unified-trading-system-ui` (consolidated portal):

```bash
# Firebase emulator
NEXT_PUBLIC_USE_FIREBASE_EMULATOR=true

# Mock vs real API path (mock = local fixtures; real = dial unified-trading-api on :8030)
NEXT_PUBLIC_MOCK_API=true

# Optional: skip auth for fast dev iteration
NEXT_PUBLIC_SKIP_AUTH=false
```

For `deployment-ui` (always real cloud mode):

```bash
# Hardcoded: UI dials 8004 on localhost
NEXT_PUBLIC_DEPLOYMENT_API_URL=http://localhost:8004
```

Full env-var matrix: `/codex/05-infrastructure/runtime-tiers-and-deployment.md` § "Runtime Profiles (v7)".

## Run dev server

```bash
# unified-trading-system-ui — tier-based startup (preferred)
bash scripts/dev-tiers.sh --tier 0      # Firebase emulators + Next dev + auto-seed
bash scripts/dev-tiers.sh --tier 1      # + 2 API gateways
bash scripts/dev-tiers.sh --tier 2      # full fleet
bash scripts/dev-tiers.sh --stop / --status

# deployment-ui (port 5183) + deployment-api (port 8004)
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh
```

Full guide: `/codex/08-workflows/local-dev.md` (backend orchestration) +
`/codex/05-infrastructure/runtime-tiers-and-deployment.md` (tier model + UI startup decision table).

## Vitest config requirement (CRITICAL)

Every UI repo's `vitest.config.ts` MUST set `pool: "forks"`:

```ts
export default defineConfig({
  test: {
    pool: "forks", // MANDATORY — `threads` leaks zombie workers + crashes CI
    // ...
  },
});
```

Per CLAUDE.md "Local Development" § "Vitest: pool: forks only" rule. The `threads` pool is forbidden workspace-wide.
**Proposed UI-QG check** (codified 2026-05-12 per UI-12 audit): `grep -q 'pool: "forks"' vitest.config.ts || fail` in
every UI repo's pre-commit / QG ratchet. Today reviewer-discipline-only; tracked as PRE_CUTOVER backlog — 🟡
NEEDS-OPERATOR-GATE for wiring policy (auto-fail vs warning).

## Regenerating types after API changes

```bash
# In unified-trading-api repo
python -m unified_trading_api.cli export-openapi > openapi.json

# In UI repo
cp ../unified-trading-api/openapi.json lib/openapi.json
npm run generate:types
git add lib/types/api-generated.ts lib/openapi.json
```

Two-step flow is manual today (no CI gate catches stale generated types — tracked as POST_CUTOVER finding UI-13).

## Cross-references

- Full env-var matrix + runtime profiles + UI startup decision table:
  `/codex/05-infrastructure/runtime-tiers-and-deployment.md`
- Frontend-backend dev orchestration: `/codex/08-workflows/local-dev.md`
- Firebase emulator + persona seeding: `/codex/14-customer-journeys/authentication/firebase-local.md`
- Active UI surface + archived UI inventory: `/codex/05-infrastructure/ui-functionality-requirements.md` +
  `codex/DEPRECATED_UIS_NOTICE.md`
- Deployment-stack restart SSOT: `unified-trading-pm/scripts/dev/restart-deployment-stack.sh`

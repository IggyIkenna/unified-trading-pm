---
doc_type: codex-ssot
title: Broken outbound hrefs
summary:
  Inventory of broken outbound hrefs in unified-trading-system-ui — 4 confirmed targets to build or fix
  (/services/execution/tca, /markets/pnl, /presentation, /executive) and 5 probable hrefs pruned in Refactor G1.5;
  quality-gates must fail on any new broken link.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, broken-links, page-triage, refactor, audit, navigation]
related: [/codex/14-customer-journeys/page-triage/triage-matrix.md, ../information-architecture.md]
created: 2026-04-19
authoritative_for: [UI broken outbound-href inventory]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/page-triage/README.md,
    /codex/14-customer-journeys/page-triage/triage-matrix.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-execution-algo.md,
    /codex/14-customer-journeys/roadmap/next-waves.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3a-current-infra-audit.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Broken outbound hrefs

Hrefs referenced in source but pointing at non-existent pages. Every item here must be resolved (build the target OR
prune the reference) in Phase 3 of the parent plan.

## 4 confirmed

### `/services/execution/tca`

- **Referenced by**:
  - [components/shell/service-tabs.tsx:554](unified-trading-system-ui/components/shell/service-tabs.tsx#L554)
  - [components/shell/command-palette.tsx:69](unified-trading-system-ui/components/shell/command-palette.tsx#L69)
  - [lib/lifecycle-route-mappings.ts:161](unified-trading-system-ui/lib/lifecycle-route-mappings.ts#L161)
  - [lib/lifecycle-route-mappings.ts:308](unified-trading-system-ui/lib/lifecycle-route-mappings.ts#L308)
- **Page.tsx**: missing
- **Fix**: build a minimal page.tsx that renders "Transaction Cost Analysis — coming soon" and redirects to
  `/services/execution/overview` after 2 seconds. TCA is a first-class feature in the lifecycle-route-mappings → it
  SHOULD exist.

### `/markets/pnl`

- **Referenced by**:
  [components/trading/pnl-attribution-panel.tsx:108](unified-trading-system-ui/components/trading/pnl-attribution-panel.tsx#L108)
- **Page.tsx**: missing
- **Fix**: this is almost certainly a typo. Change to `/services/trading/pnl` (more likely, since it's a trading
  component).

### `/presentation`

- **Referenced by**:
  [app/(public)/demo/preview/page.tsx:158](<unified-trading-system-ui/app/(public)/demo/preview/page.tsx#L158>)
- **Page.tsx**: missing
- **Fix**: change to `/investor-relations/board-presentation`. Preview page is showing a "view the full presentation"
  CTA.

### `/executive`

- **Referenced by**:
  [app/(platform)/investor-relations/board-presentation/components/board-presentation-slide-part-b.tsx:376](<unified-trading-system-ui/app/(platform)/investor-relations/board-presentation/components/board-presentation-slide-part-b.tsx#L376>)
- **Page.tsx**: missing
- **Fix**: change to `/services/reports/executive`.

## 5 probable — resolved 2026-04-20 (Refactor G1.5, all PRUNED)

All five entries were classified **PRUNE** and removed from
[lib/lifecycle-route-mappings.ts](unified-trading-system-ui/lib/lifecycle-route-mappings.ts),
[tests/e2e/tier0-route-registry.ts](unified-trading-system-ui/tests/e2e/tier0-route-registry.ts),
[tests/e2e/warmup.setup.ts](unified-trading-system-ui/tests/e2e/warmup.setup.ts),
[tests/e2e/research.spec.ts](unified-trading-system-ui/tests/e2e/research.spec.ts),
[tests/e2e/research-flow.spec.ts](unified-trading-system-ui/tests/e2e/research-flow.spec.ts),
[lib/mocks/fixtures/build-data.ts](unified-trading-system-ui/lib/mocks/fixtures/build-data.ts) (re-pointed mock hrefs to
live routes) and [UI_STRUCTURE_MANIFEST.json](unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json).

Per-href decision rationale (aligned with the forthcoming G2.4 ML Model Catalogue refactor — see
[../cross-cutting/catalogue-ml-model.md](../playbook-concepts/catalogue-ml-model.md)):

| Pruned href                         | Rationale                                                                                                                                                           |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/services/research/ml/overview`    | Duplicates `/services/research/ml` base hub; G2.4 will elevate the hub to catalogue-landing status without a second "overview" route.                               |
| `/services/research/ml/experiments` | Experiment iteration is a quant-research concept surfaced elsewhere (`/services/research/quant`); G2.4 catalogue parity spec does not list experiments as an entry. |
| `/services/research/ml/features`    | Features already surface at `/services/research/features` and `/services/research/feature-etl`; avoid duplicate features surface under ML.                          |
| `/services/research/ml/validation`  | Validation/governance rolls into `/services/research/ml/registry` + `/services/research/ml/governance`; no standalone validation page planned by G2.4.              |
| `/services/research/ml/deploy`      | Promotion rolls into `/services/research/ml/registry` (with lock_state + maturity per architecture v2); no standalone deploy page.                                  |

Durable test:
[unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-5-ml-catalogue-hrefs.spec.ts](unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-5-ml-catalogue-hrefs.spec.ts)
asserts each pruned href 404s and each remaining live ML sub-route renders for the admin persona.

G2.4 follow-ups (outside G1.5 scope): elevate `/services/research/ml/` to catalogue status with coverage matrix
(model_family × asset_group × training_period × maturity × lock_state), per-entry detail pages, and admin lock-state
controls — tracked in [../roadmap/next-waves.md](../roadmap/next-waves.md).

## Verification

After Phase 3 nav-config fixes, re-run the static audit (same grep pattern as Phase 0) to confirm this doc is empty:

```bash
# From unified-trading-system-ui/
grep -rE 'href=["'"'"']/[^"'"'"']*["'"'"']' app components lib | \
  # extract unique href targets
  # cross-reference against app/**/page.tsx
  # any mismatch = broken link
```

CI gate: `scripts/quality-gates.sh` should run this audit and fail if broken links found.

## Related

- Triage matrix: [triage-matrix.md](triage-matrix.md)
- Nav-config files: [../information-architecture.md](../information-architecture.md)

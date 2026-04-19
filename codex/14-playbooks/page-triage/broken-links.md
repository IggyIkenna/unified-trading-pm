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

## 5 probable (flagged for deeper audit)

These appear in [lib/lifecycle-route-mappings.ts](unified-trading-system-ui/lib/lifecycle-route-mappings.ts) but no
page.tsx exists:

- `/services/research/ml/overview`
- `/services/research/ml/experiments`
- `/services/research/ml/features`
- `/services/research/ml/validation`
- `/services/research/ml/deploy`

**Fix**: for each, either (a) build the page.tsx if the ML Model Catalogue refactor needs it, or (b) prune the reference
from lifecycle-route-mappings.ts. Decision goes in the ML Model Catalogue refactor plan — tracked in
[../roadmap/next-waves.md](../roadmap/next-waves.md).

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

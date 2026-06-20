---
title: Legacy paper-trading dashboard missing `pt-gross-now` testid — smoke spec fails
created: 2026-06-20
source:
  - tests/smoke/paper-trading.smoke.spec.ts:22
  - unified-trading-system-ui/app/paper-trading/page.tsx
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

`tests/smoke/paper-trading.smoke.spec.ts` › "margin panel shows Gross exposure
(now) symmetric with Net exposure (now)" FAILS: it navigates to the legacy
engine-snapshot dashboard (`/paper-trading`, no `?client`) and asserts a
`data-testid="pt-gross-now"` element + the literal "Gross exposure (now)" /
"Gross exposure (max)" labels. **`pt-gross-now` does not exist anywhere in
`app/` or `components/`** (`grep -rn pt-gross-now app/ components/` = 0 hits).
The margin panel in `app/paper-trading/page.tsx` renders `data.margin.gross_usd`
("Gross exposure (now)") and `s.net_usd_max` ("Net exposure (max)") but has no
`pt-gross-now` testid and no "Gross exposure (max)" row.

This is a regression for the documented 2026-06-19 "gross-now gap" (the spec's
own comment) — the test was written/updated but the page-side `pt-gross-now`
testid + Gross-(max) row were never added (or were reverted).

## Why it matters

Pre-existing `tests/smoke/` red unrelated to the real-ledger auth fix shipped
2026-06-20 (`?client=<id>` reporting-API JWT bridge — that spec
`paper-trading-ledger.smoke.spec.ts` is green). It pollutes the `pw:L2` gate for
any UI change touching `tests/smoke/`.

## Recommended decision

- [ ] [UI] P2. Add `data-testid="pt-gross-now"` to the legacy paper-trading
  margin "Gross exposure (now)" value in `unified-trading-system-ui/app/paper-trading/page.tsx`,
  and a "Gross exposure (max)" row (Σ|position notional| ceiling, mirroring the
  net (now)/(max) pair) so the 2026-06-19 gross-now-gap regression spec
  (`tests/smoke/paper-trading.smoke.spec.ts:22`) passes. Verify `pw:L2 ✓` on
  that spec. **DEFERRED** — separate from the real-ledger auth bug; needs the
  gross-now derivation decision for the legacy engine-snapshot panel. Provenance:
  surfaced while fixing the deployed `?client` paper-trading hang 2026-06-20.

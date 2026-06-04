---
title: unified-trading-system-ui ci.yml uses GITHUB_TOKEN for cross-repo sibling checkouts (should be GH_PAT)
created: 2026-06-04
author: ikennaigboaka [slot-1·laptop]
source:
  - tab-mirror fleet rollout 2026-06-04 (the only repo that failed STEP 5.18 token-check during rollout)
  - unified-trading-system-ui/.github/workflows/ci.yml:95-106
locked_by: live-defi-rollout
---

## What I found

`unified-trading-system-ui/.github/workflows/ci.yml` checks out two **sibling repos** with
`token: ${{ secrets.GITHUB_TOKEN }}`:

- `Checkout UAC sibling repo` → `IggyIkenna/unified-api-contracts` (ci.yml ~line 99)
- `Checkout UIC sibling repo` → `IggyIkenna/unified-config-interface` (ci.yml ~line 105)

`GITHUB_TOKEN` is repo-scoped and cannot read other private repos, so these cross-repo checkouts require
`secrets.GH_PAT` (the workflow-capable PAT). The workspace token-check (`scripts/validation/check-workflow-tokens.py`,
QG STEP 5.18) flags both as `cross-repo operation uses GITHUB_TOKEN`.

Surfaced because the UI repo was the **only** one of 24 that failed the dir-wide token-check during the
bidirectional-tab-mirror rollout (2026-06-04). The tab-mirror file itself is clean; the rollout shipped it anyway via a
file-scoped commit (UI@059bf539). These two violations are **pre-existing**, unrelated to tab-mirror.

(Note: `unified-config-interface` may itself be stale/archived — verify the repo still exists and the checkout is still
needed before fixing; if the sibling checkout is dead, delete the step instead of re-tokenizing it.)

## Why it matters

STEP 5.18 is a blocking QG step, so the UI repo's own `quality-gates-v2` CI fails on these — any UI PR to staging/main
is gated on it. Left unfixed it blocks UI promotion independent of the change being shipped.

## Recommended decision

Replace `secrets.GITHUB_TOKEN` with `secrets.GH_PAT` on both sibling-checkout steps in
`unified-trading-system-ui/.github/workflows/ci.yml` (after confirming each sibling repo is still live + needed). Owner:
a UI-capable slot. SSOT for the rule: CLAUDE.md § "Workflow-capable GH_TOKEN everywhere" +
`scripts/validation/check-workflow-tokens.py`.

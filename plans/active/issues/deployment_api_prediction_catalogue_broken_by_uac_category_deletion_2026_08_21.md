---
doc_type: issue
title:
  deployment-api's prediction_catalogue.py is broken (import-time, blocks ALL tests) by unified-api-contracts@4f25d5f0's
  deliberate PredictionMarketCategory deletion — needs a real design decision, not a mechanical rename
summary: >-
  unified-api-contracts@4f25d5f0 (`feat!: delete deprecated PredictionMarketCategory axis, migrate consumers to
  CanonicalQuestionGroup/two_axis`, tracked as [x] done in walkthrough_feedback_remediation_2026_08_21.md, "Manifest
  supersession flagged to T2 (no-migration scope here)") deleted `PredictionMarketCategory` (the 7-value coarse bucket
  enum: politics/financial/sports/crypto/weather/entertainment/other) and its composer `category_for_group` /
  `_category_for_underlying` entirely, with zero replacement or migration path for the coarse-bucket concept — the new
  `underlying_for_group()` returns `PredictionUnderlying`, a much finer-grained per-asset/per-league enum (BTC,
  CRUDE_OIL, TRUMP, SPORTS_MLB, …), not a drop-in same-shape replacement. The UAC-side todo's own self-audit
  (`rg 'PredictionMarketCategory|canonical/domain/prediction[^s]'` in UAC) was scoped to UAC's own repo and never found
  deployment-api's one live consumer: `deployment-api/deployment_api/services/prediction_catalogue.py` (imports both
  deleted names at module level; feeds the `category` field of `PredictionCatalogueRow` + the `category=` filter param
  on `GET` prediction-catalogue routes + facet counts). Since the import fails at module load, and this module is
  imported eagerly by `tests/unit/conftest.py::_ensure_services_mocked()`, EVERY test in deployment-api's suite now
  fails to collect — `quality-gates.sh` cannot go green for ANY change to deployment-api, not just prediction code,
  until this is fixed. Found blocking an unrelated wave-1c ship (strategy-wizard endpoint + staking_pnl todos,
  `code_readiness_t3_features_ml_strategy_2026_08_19.md`) — not fixed there because a correct fix is a real design
  decision (what does "category" mean in the deployment-api/deployment-ui prediction catalogue UX now that the coarse
  bucket is gone: keep the OLD 7-value semantics via a NEW locally-owned mapping table deployment-api would have to
  invent and maintain, or redesign the catalogue's category filter/facets around the two-axis model
  `PredictionUnderlying` + `PredictionBetType`?) — not a mechanical import swap, and touches an external-facing API
  contract (the catalogue route + presumably a deployment-ui category filter dropdown) this session has no visibility
  into.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [deployment-api, unified-api-contracts]
scope: [engineer]
tags: [prediction, breaking-change, cross-repo-consumer-migration, deployment-api, quality-gates]
related:
  [
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
    /plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-21
author: claude-code (wave-1c interactive session, code_readiness_t3_features_ml_strategy_2026_08_19.md)
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P0
resolved_by:
source: >-
  Hit live 2026-08-21 re-gating deployment-api after a coordinator signal that unified-api-contracts@4f25d5f0 had
  landed and unblocked an earlier dirty-dep ship-block. `quality-gates.sh --no-fix` failed at pytest collection:
  `ImportError: cannot import name 'PredictionMarketCategory' from 'unified_api_contracts.predictions'`, traced via
  `git show 4f25d5f0 -- '*cross_venue_mapping.py'` (confirms both `PredictionMarketCategory` and
  `_category_for_underlying`/`category_for_group` were deleted with no successor of the same shape) and
  `grep -rln "PredictionMarketCategory|category_for_group" deployment-api/` (confirms exactly one file:
  `deployment_api/services/prediction_catalogue.py`, plus its route `deployment_api/routes/prediction_catalogue.py`
  and test `tests/unit/test_prediction_catalogue.py`, which reference the OLD coarse values e.g.
  `category="CRYPTO"`/`category="sports"` — a straight swap to `PredictionUnderlying` would silently change what
  those filters match, since `PredictionUnderlying` values are per-asset, not per-bucket).
context_scope:
  [
    deployment-api/deployment_api/services/prediction_catalogue.py,
    deployment-api/deployment_api/routes/prediction_catalogue.py,
    deployment-api/tests/unit/test_prediction_catalogue.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/predictions/two_axis.py,
    unified-api-contracts/unified_api_contracts/predictions/__init__.py,
    /plans/active/walkthrough_feedback_remediation_2026_08_21.md,
  ]
depends_on: []
locked_by:
locked_since:
---

## What's broken

`deployment_api/services/prediction_catalogue.py` imports two names deleted by
`unified-api-contracts@4f25d5f0`:

```python
from unified_api_contracts.predictions import (
    CanonicalQuestionGroup,
    PredictionMarketCategory,   # DELETED
    category_for_group,          # DELETED
    classify_kalshi_to_canonical_group,
    classify_polymarket_to_canonical_group,
)
```

Two live usages (not dead code):

- `category_cache: dict[CanonicalQuestionGroup, PredictionMarketCategory] = {}` (type annotation)
- `category = category_for_group(cqg)` inside `_build_rows()`, whose result becomes
  `PredictionCatalogueRow["category"]` — an external-facing field consumed by the
  `category=` query-param filter on the prediction-catalogue GET route and the
  category facet-count breakdown.

This module is imported eagerly by `tests/unit/conftest.py::_ensure_services_mocked()`,
so the ImportError happens at **collection time** — it fails EVERY test in
deployment-api's suite, not just prediction-catalogue tests. `quality-gates.sh` cannot
go green for deployment-api at all right now.

## Why this isn't a mechanical rename

`PredictionMarketCategory` was a 7-value coarse bucket enum (`politics`, `financial`,
`sports`, `crypto`, `weather`, `entertainment`, `other`). `category_for_group()`
composed it via a private `_category_for_underlying()` helper — **also deleted, no
successor left anywhere in UAC** (confirmed: `grep -rn "_category_for_underlying"
unified_api_contracts/` is empty on `4f25d5f0`).

The new `underlying_for_group(cqg) -> PredictionUnderlying` is NOT the same shape: its
docstring names specific per-asset/per-league values (`BTC`, `CRUDE_OIL`, `TRUMP`,
`SPORTS_MLB`, …), not a 7-value bucket. Swapping `category_for_group` →
`underlying_for_group` 1:1 would silently change deployment-api's `category` field (and
the `category=` filter param) from ~7 coarse values to dozens of fine-grained ones —
`deployment-api/tests/unit/test_prediction_catalogue.py` already asserts the OLD
semantics (`category="CRYPTO"`, `category="sports"` case-insensitive filters), and
whatever deployment-ui's catalogue browser renders as a category dropdown almost
certainly assumes the old 7-value set too (not verified this session — deployment-ui is
out of this repo pair's scope).

The UAC-side todo (`walkthrough_feedback_remediation_2026_08_21.md`, "Delete the
deprecated third prediction grouping axis") explicitly scoped consumer migration to
UAC-internal files only ("Manifest supersession flagged to T2 (no-migration scope
here)") and its own `rg` self-audit was run inside `unified-api-contracts/`, so it never
saw deployment-api's live consumer.

## Two real options for whoever picks this up (not decided here — genuinely needs a
call on the external API/UX, out of this session's visibility into deployment-ui)

1. **Preserve old bucket semantics** — deployment-api builds and OWNS a small local
   `PredictionUnderlying -> "politics"|"financial"|"sports"|"crypto"|"weather"|
   "entertainment"|"other"` mapping table (resurrecting the deleted bucket concept
   locally, since UAC deliberately removed it workspace-wide) so the external API/UI
   contract doesn't change. Fastest, but re-introduces exactly the axis UAC just
   deleted, just one repo over.
2. **Redesign around the two-axis model** — expose `underlying` (fine-grained) +
   `bet_type` (`PredictionBetType`) as the new filter/facet axes, update
   `PredictionCatalogueRow`, the route's query params, the 2 tests, and (separately)
   whatever deployment-ui renders for this — a real UX change, needs product/T-owner
   sign-off, can't be done blind from deployment-api alone.

## Impact right now

Every `quality-gates.sh` run in deployment-api is red until this is fixed — blocks
ANY ship to this repo, not just prediction-catalogue changes. Confirmed blocking
`code_readiness_t3_features_ml_strategy_2026_08_19.md`'s wave-1c strategy-wizard-endpoint
ship (code complete + tested + gate-green on everything except this pre-existing,
unrelated import break).

- [ ] [BACKEND] P0. Pick one of the two options above (or a third, better one) and fix
      `deployment_api/services/prediction_catalogue.py` + `routes/prediction_catalogue.py`
      + `tests/unit/test_prediction_catalogue.py` accordingly, then confirm
      `quality-gates.sh --no-fix` collects + passes in deployment-api again. If
      deployment-ui has a category filter/dropdown consuming this route, check + update
      it in the same change.

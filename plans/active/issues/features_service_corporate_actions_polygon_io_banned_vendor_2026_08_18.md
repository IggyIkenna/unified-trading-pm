---
doc_type: issue
title: features-service corporate_actions calculator sourced from banned vendor Polygon.io
summary: >-
  The live, dispatched `corporate_actions` feature_group calculator in features-service reads exclusively from
  `polygon_corporate_actions_adapter.py` — Massive-fka-Polygon.io, a fleet-wide banned vendor per CLAUDE.md. Found
  while investigating why EVENT_DRIVEN couldn't be declared against it in unified-api-contracts'
  ARCHETYPE_FEATURE_GROUPS registry; left undeclared there rather than accepted silently.
status: open
nature: issue
asset_group: [tradfi]
stage: [features]
repos: [features-service]
scope: [engineer]
tags: [banned-vendor, polygon-io, compliance, corporate-actions, features-service]
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
created: 2026-08-18
source: >-
  Found during a live investigation into unified-api-contracts' EVENT_DRIVEN archetype registry gap
  (nick_ai_platform_readiness_remediation_2026_08_16.md W2 follow-up), not a dedicated audit — confirmed by direct
  read of features_service/calendar/adapters/polygon_corporate_actions_adapter.py and
  features_service/calendar/cli/handlers/corporate_actions_handler.py, not inferred from naming.
related:
  [
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /codex/06-coding-standards/README.md,
  ]
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
drift_direction: advance-code
depends_on: []
---

# features-service corporate_actions calculator sourced from banned vendor Polygon.io

## What was found

`unified_api_contracts/canonical/domain/features/required_inputs.py` gained a "features-service dispatch-traced
tier" of new `FEATURE_REQUIRED_INPUTS` entries on 2026-08-18 (perp funding, DeFi LP/vault, FRED-sourced macro
calendar) after an operator review found real, live calculators the earlier scaffold-based registry pass had missed.
`corporate_actions` was investigated as a candidate for the same treatment — it IS a real, dispatched feature_group
(`features_service/calendar/cli/handlers/corporate_actions_handler.py`) — but its calculator
(`features_service/calendar/engine/calculators/corporate_actions_calculator.py`) has exactly one confirmed data
source: `features_service/calendar/adapters/polygon_corporate_actions_adapter.py`.

CLAUDE.md's coding-standards section lists removed vendors as a **fleet-wide ban, not DeFi-only**:
_"Elysium · Arkham · Bloxroute · Infura · Kaiko · Massive-fka-Polygon.io"_ (`polygon` in that context = the CHAIN, a
distinct term). This adapter's own module name and imports leave no ambiguity that it is the equities-data vendor,
not the chain.

## Why this wasn't fixed in the same commit

Not this session's file, not this session's scope (a UAC registry declaration, not a features-service data-sourcing
fix), and re-sourcing corporate-action data is real design/vendor-selection work, not a bounded edit. Per
findings-triage: outside every currently-open plan → filed here rather than silently worked around.

## A real precedent already exists for the fix — same file, same handler

`corporate_actions_handler.py` already runs a yfinance leg alongside the Polygon leg: its `earnings_results` output
(`calendar/earnings_results/by_date/day={YYYY-MM-DD}/results.parquet`) is fetched via `YFinanceEarningsAdapter` —
confirmed clean, not Polygon. `yfinance` (the Python package) also exposes `Ticker.dividends` and `Ticker.splits`
directly — the same library already imported in this file could plausibly replace `PolygonCorporateActionsAdapter`
for the dividends/splits legs too, without adding a new dependency. Not verified beyond "the library supports it" —
whether yfinance's dividend/split data is complete/reliable enough for the same tickers Polygon covered is real
diligence work, not assumed here. Worth being the first option evaluated in the re-sourcing decision below.

## Current disposition

`corporate_actions` is left **undeclared** in `ARCHETYPE_FEATURE_GROUPS` — `EVENT_DRIVEN` was declared against
`yield_curve` + `economic_results` only (both confirmed FRED-sourced, clean) with a docstring note explaining the
exclusion. No downstream consumer is currently claiming corporate-actions capability that doesn't exist.

## Todos

- [ ] [REVIEW] P1. **Confirm current blast radius** — is `corporate_actions_handler.py`'s CLI (`--operation
      corporate_actions --mode batch`) actually invoked by a scheduled/production job today, or built-but-never-run?
      Unlike an earlier draft of this doc claimed, `earnings_results` (the yfinance leg of the SAME handler) is
      genuinely dispatched — so the Polygon leg is at minimum wired into a real, callable operation, not orphaned
      code; what's unconfirmed is whether anything actually schedules it.
- [ ] [OPERATOR] P1. **Decide the re-sourcing path** — evaluate yfinance's `Ticker.dividends`/`Ticker.splits` first
      (same library already live in this file for earnings, see "real precedent" section above) before considering
      a paid data contract; confirm whether yfinance's coverage/reliability is acceptable for the tickers this
      capability needs, or whether it's deprioritized until a paid source exists.
- [ ] [AGENT] P2. **Once re-sourced, declare `corporate_actions` in `FEATURE_REQUIRED_INPUTS` and `EVENT_DRIVEN` in
      `ARCHETYPE_FEATURE_GROUPS`** the same way the other 6 archetypes were declared 2026-08-18 — real dispatch-site
      citation, non-empty `InputReq` set.

## Progress Log

**2026-08-18 — filed.** Found live during EVENT_DRIVEN archetype registry work in unified-api-contracts; not
independently re-derived, this is a direct-read confirmation of the adapter's real import chain.

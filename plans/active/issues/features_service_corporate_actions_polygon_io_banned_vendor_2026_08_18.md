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
parent_epic: security_and_cross_cutting_master
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
context_scope:
  [
    features-service/features_service/calendar/adapters/polygon_corporate_actions_adapter.py,
    features-service/features_service/calendar/engine/calculators/corporate_actions_calculator.py,
    features-service/features_service/calendar/cli/handlers/corporate_actions_handler.py,
    unified-api-contracts/unified_api_contracts/canonical/domain/features/required_inputs.py,
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

- [x] ✅ [REVIEW] P1. **EXTRACTED 2026-08-18 (na-eligibility-audit, tradfi tranche, dispatch agt-31bfcb) →
      `tradfi_satellite_ao_dispatch_batch17_2026_08_18.md` todo 1.** Confirm current blast radius — is
      `corporate_actions_handler.py`'s CLI (`--operation corporate_actions --mode batch`) actually invoked by a
      scheduled/production job today, or built-but-never-run? Unlike an earlier draft of this doc claimed,
      `earnings_results` (the yfinance leg of the SAME handler) is genuinely dispatched — so the Polygon leg is at
      minimum wired into a real, callable operation, not orphaned code; what's unconfirmed is whether anything
      actually schedules it. Bounded, worker-determinable investigation — dispatched separately from todos 2/3
      below, which stay genuinely operator/design-gated.
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
- **na-eligibility-audit 2026-08-18** (tradfi tranche, dispatch agt-31bfcb): **RECLASSIFY, per-todo split.** Todo 1
  (blast-radius confirmation) is bounded/worker-determinable — extracted to
  `tradfi_satellite_ao_dispatch_batch17_2026_08_18.md` todo 1 (conflict-cleared, zero existing coverage). Todos 2
  (OPERATOR re-sourcing decision) and 3 (contingent registry declaration, gated on todo 2) stay genuinely
  operator-gated / contingent. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-19** (tradfi tranche, dispatch agt-5d34f9): **KEEP-NA, valid — reaffirmed.** 2 open
  todos re-read end-to-end (count reconciled, 2/2), unchanged since the 08-18 pass. Todo 2 ([OPERATOR] vendor
  re-sourcing decision — yfinance vs. a paid contract for corporate-actions dividends/splits) is genuine
  diligence/judgment work; todo 3 is contingent on todo 2's outcome. `assigned_vm` unchanged.
- **context-scout 2026-08-19**: populated/refreshed context_scope (5 entries).
- **blast-radius confirmation 2026-08-19** (via `tradfi_satellite_ao_dispatch_batch17_2026_08_18.md` todo 1, review):
  **CONFIRMED UNSCHEDULED — built-but-never-run.** `--operation corporate_actions --mode batch` is a registered,
  callable operation (`features-service@afa03168`, 2026-08-03 — `cli/main.py` `operations` map) but no production job
  dispatches it today. Evidence: (1) not in `CALENDAR_FEATURE_GROUPS` (`batch_handler.py:46` — the scheduled
  `--operation compute` batch iterates only time_features/economic_events/yield_curve/economic_results; the handler's
  own docstring confirms corporate_actions is NOT wired into `process_day()`); (2) no Cloud Scheduler job — the full
  asia-northeast1 list has no corporate_actions/economic_results/forexfactory job; the only features-calendar scheduler
  `uts-prod-features-calendar-t1-schedule` is **PAUSED** and its target Cloud Run Job
  `uts-prod-features-calendar-service-t1-recon` **does not exist** (`gcloud run jobs describe` → "Cannot find job");
  (3) no deployment-service/orchestrator dispatcher — `cloud_run_job_registry.py` classifies the t1-recon stem but is
  not a dispatcher, agent-orchestrator has zero `corporate_actions` refs, and
  `terraform/services/features-calendar-service/` is an un-applied scaffold (`n-service` placeholders); (4) the only
  `--operation corporate_actions` dispatch configs in the workspace target the **instruments-service** image (the
  IBKR/yfinance handler — `configs/sharding.corporate-actions.yaml` with zero consumers, and instruments-service
  `main.tf` Workflow, self-superseded by the t1-recon jobs per its own comment), NOT this features-service Polygon.io
  calculator. **Blast radius of the Polygon.io adapter: ZERO live production dispatch — no scheduled job pulls Polygon
  dividends/splits today.** Also corrects this doc's premise: `earnings_results` has no independent dispatcher either —
  it runs only inside this same unscheduled `--operation corporate_actions`, so "genuinely dispatched" holds only as
  "registered callable operation", not "scheduled". Limitation: GCS presence (has the handler EVER written data) not
  machine-verified — `gcloud storage` CLI is guardrail-blocked on this host.

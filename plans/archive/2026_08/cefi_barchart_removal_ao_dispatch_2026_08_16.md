---
doc_type: plan
title: Deprecate + remove all Barchart code fleet-wide (operator-ruled 2026-06-24, re-confirmed 2026-08-16)
summary: >-
  Operator-ruled 2026-06-24 (Phase 5 of cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md), re-confirmed
  2026-08-16 (na-eligibility-audit follow-up Q&A) — Barchart's only role was the VIX cash-index 15m preload, which
  was already deprecated in favor of VX-futures-via-databento (XCBF.PITCH). Extracting the fully-specced removal
  todo into its own AO-dispatch plan since the parent doc stays assigned_vm: NA. **CANCELLED 2026-08-16 — the
  removal turned out already shipped 2026-08-09/2026-08-15, before this doc was even drafted; never dispatched.**
status: complete
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-api-contracts, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, barchart, deprecated-code-removal, canonicalization]
related:
  [
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 6, 2026-08-16 — operator ruling on cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md Phase 5 Barchart-removal todo"
locked_by:
context_scope:
  [
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
locked_since:
resolved_by:
---

# Deprecate + remove all Barchart code fleet-wide

## Todos

- [x] ✅ [REFACTOR] P2. **CANCELLED — already shipped elsewhere (2026-08-16 reconciliation,
      `cefi_satellite_ao_dispatch_batch19_2026_08_13_finalize.md`, slot 21).** DEPRECATE + REMOVE all Barchart (own
      unit — operator 2026-06-24, re-confirmed 2026-08-16). Barchart's only role was the VIX cash-index 15m preload;
      the VIX cash-index was deprecated in favor of VX futures via databento XCBF.PITCH. — Bulk removal already
      **SHIPPED 2026-08-09** (`unified-api-contracts@fc1b4897`, `market-tick-data-service@aea655a9`), independently
      re-verified live 2026-08-15 via `cefi_satellite_ao_dispatch_batch19_2026_08_13.md` (`rg -i barchart`
      workspace-wide: zero live adapter/client/schema/registry code; 2 stale comment/docstring residuals also fixed
      there — `unified-api-contracts@49ae9bc433`, `market-tick-data-service@ea870f05cd`). This doc's own 2026-08-16
      drafting session didn't catch the prior-day verification. See
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`'s reconciled Phase-5 checkbox for full evidence.
      No code shipped by this doc (none needed).

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 6, operator ruling)**: extracted from
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phase 5 — todo text already fully specced there
  (operator-directed 2026-06-24), no new design needed. Re-confirmed as still current before dispatch.
- **2026-08-16 (reconciliation, `cefi_satellite_ao_dispatch_batch19_2026_08_13_finalize.md`, slot 21)**: while
  reconciling batch19's shipped Barchart-removal evidence back into
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`, found this doc duplicates already-verified-complete
  work — the bulk removal shipped 2026-08-09 and its 2 residual fixes shipped 2026-08-15 via
  `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`, both before this doc's 2026-08-16 drafting session (which never
  dispatched this todo — Progress Log shows only the drafting entry). Cancelled as moot; archiving this doc + its
  finalize in the same commit, zero open todos, never dispatched.

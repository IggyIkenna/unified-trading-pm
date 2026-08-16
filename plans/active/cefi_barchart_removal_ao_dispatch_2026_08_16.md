---
doc_type: plan
title: Deprecate + remove all Barchart code fleet-wide (operator-ruled 2026-06-24, re-confirmed 2026-08-16)
summary: >-
  Operator-ruled 2026-06-24 (Phase 5 of cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md), re-confirmed
  2026-08-16 (na-eligibility-audit follow-up Q&A) — Barchart's only role was the VIX cash-index 15m preload, which
  was already deprecated in favor of VX-futures-via-databento (XCBF.PITCH). Extracting the fully-specced removal
  todo into its own AO-dispatch plan since the parent doc stays assigned_vm: NA.
status: active
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

- [ ] [REFACTOR] P2. **DEPRECATE + REMOVE all Barchart (own unit — operator 2026-06-24, re-confirmed 2026-08-16).**
      Barchart's only role was the VIX cash-index 15m preload; the VIX cash-index was deprecated in favor of VX
      futures via databento XCBF.PITCH. Per delete-deprecated-code: (1) `rg -i barchart` workspace-wide (~30 files:
      `SOURCE_PRIORITY` tradfi ohlcv_15m list, `SOURCE_MODE_CAPABILITY["barchart"]`,
      `EMISSION_LATENCY_MS_BY_SOURCE["barchart"]`, `data_source_continuity` `BARCHART_VIX_*` constants +
      SourceWindow, `_umi_yahoo`/tradfi adapters, IS enumerator, multiple UAC tests, CLAUDE.md "VIX 15m: Barchart
      preload" note, docs); (2) VERIFY no live MVP cell is source=barchart + the VIX path uses VX-futures-databento
      (repoint any straggler FIRST); (3) DELETE the adapter/client/source-entries (remove code, no deprecation
      shim); remove `barchart` from every source enum / SOURCE_PRIORITY / continuity registry; (4) UPDATE
      CLAUDE.md VIX note → VX-futures-via-databento; (5) update the source-priority/parity tests (deleting a source
      must not break them). The existing centralised parity gate
      (`unified-api-contracts/tests/unit/test_venue_source_adapter_parity.py`) then finds NO
      source=barchart-with-no-adapter (cross-check). If Barchart is load-bearing somewhere unexpected → STOP + flag.
      Repos: unified-api-contracts + market-tick-data-service + unified-trading-pm (CLAUDE.md).

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 6, operator ruling)**: extracted from
  `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phase 5 — todo text already fully specced there
  (operator-directed 2026-06-24), no new design needed. Re-confirmed as still current before dispatch.

---
doc_type: issue
title: cefi empty_confirmed historical-volume breakdown (6.4M rows) — reference
summary: >-
  Reference doc preserving a session investigation's breakdown of cefi's 6,432,513 empty_confirmed rows (44.32%
  coverage_pct run of 2026-08-14). Grain, date/venue/data_type/instrument_type distribution, and cross-tab — verdict:
  spread across 22 venues and 2,783 days, tracks organic backfill/venue-onboarding growth 2019-2026, no single incident
  or dominant combo. Distinct from the ACUTE cross_ag_live_capture_parity BYBIT-FUTURES 100%-empty-confirmed bug (a
  live-capture regression, not this historical volume). Open follow-up work (PERPETUAL/SPOT_PAIR scope determination,
  error_reason breakdown) tracked in the sibling audit plan, not here.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [honest-coverage, empty-confirmed, cefi, data-correctness, reference]
related:
  [
    /codex/02-data/honest-coverage-model.md,
    /plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
locked_by:
locked_since:
context_scope:
  [/codex/02-data/honest-coverage-model.md, /plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md]
supersedes:
superseded_by:
resolved_by:
depends_on:
source: interactive-session-investigation-2026-08-15
assigned_role: data_engineering
effort: low
drift_direction: advance-code
---

# cefi empty_confirmed historical-volume breakdown (6.4M rows) — reference

Operator asked to preserve this as a standing reference rather than let it live only in session output. Measured
2026-08-15 against `gs://central-element-323112-honest-coverage/2026-08-14/coverage.json` (a fresh full 5-AG run) and
the underlying `market-data-tick-cefi-prd-central-element-323112` manifest.

## Headline

`empty_confirmed = 6,432,513` vs `captured = 9,293,793`, `attempted_failed = 807,613`, `coverage_pct = 44.32%`.

## Grain

`(date, venue, instrument_type, data_type)` — confirmed via `_resolve_row_key()`
(`market-tick-data-service/market_tick_data_service/live/manifest_recorder.py:78-108`) and a `record_failed` call site
(`.../market_interface/adapters/tradfi/tardis_cefi_shards.py:573-582`).

## Distribution — spread, no single cause

- **By date**: 2,783 distinct dates, 2019-01-01 → 2026-08-14. Top 20 single days sum to only 2.45% of total — no
  incident window. By year: 2019 3.15% · 2020 5.27% · 2021 6.05% · 2022 5.08% · 2023 12.30% · 2024 28.77% · 2025 25.20%
  · 2026(partial) 14.18%. 2023-2026 = 80.45%, tracking venue/shard-onboarding growth (bigger `expected` denominator over
  time), not one dated incident.
- **By venue**: spread across 22 venues, none dominant — KRAKEN-FUTURES 14.65% (largest single venue) · ASTER 14.18% ·
  BYBIT 11.96% · BITGET-FUTURES 9.09% · BINANCE-FUTURES 7.75% · OKX-SWAP 6.16% · HYPERLIQUID 5.92% · OKX-SPOT 4.17% ·
  BINANCE-SPOT 3.69% · BITGET-SPOT 3.65% · 12 more venues each ≤2.57%.
- **By data_type**: `trades` 38.61% · `derivative_ticker` 26.68% · `book_snapshot_5` 25.96% · `liquidations` 8.75%
  (structurally smaller — only applies to derivative instrument types).
- **By instrument_type**: `PERPETUAL` 62.93% · `SPOT_PAIR` 20.15% · `FUTURE` 16.24% · `futures_chain` 0.64% ·
  `options_chain` 0.04% · `OPTION`/`COMBO` ≈0.
- **Cross-tab**: 73 distinct (venue, instrument_type, data_type) combos; no single combo exceeds 7.3% of total (top:
  ASTER/PERPETUAL/derivative_ticker 7.26%). Top 15 combos sum to only ~44%.

## Verdict

Benign historical backfill debt, not a bug or incident — spread across venues/dates/types with no dominant combination.
**PERPETUAL and SPOT_PAIR being the two largest instrument_type contributors (83% combined) is a real open question** —
is there a known venue-capability rule that means some of these should never have been enumerated (out-of-scope, should
be pruned), or is capture genuinely expected but incomplete? That determination, plus the error_reason breakdown (not
pulled in the original investigation), is tracked as its own todo in
`/plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md` — not re-litigated here.

## Distinct from the acute live-capture bug

`/plans/active/cross_ag_live_capture_parity_2026_08_14.md` tracks a DIFFERENT, acute cefi issue: 4 specific shards
(BYBIT-FUTURES all data_types, DERIBIT derivative_ticker, COINBASE-SPOT depth_of_book_10, OKX-SWAP depth_of_book_10)
that flipped to 100% empty_confirmed after an 08-09 VM restart, caused by a Tardis-alias venue name never resolving to
IS's `BYBIT`-keyed venue. Root cause is fixed and deployed; captured-row verification is still open (blocked on a
separate 08-14 catalog-blob publishing gap, 0 CEFI blobs vs the normal 22). That's a regression on top of this doc's
benign baseline, not part of it.

## Progress Log

- **2026-08-15 (interactive session, slot 3)**: Filed as a reference doc per operator instruction ("agreed make one
  human/NA not vm:planning"), preserving the session's breakdown so it survives context compaction. No mutation, no
  further action owned by this doc — follow-ups tracked in the sibling audit plan.

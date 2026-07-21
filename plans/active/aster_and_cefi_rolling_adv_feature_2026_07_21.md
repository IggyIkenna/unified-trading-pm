---
doc_type: plan
title: Rolling ADV (average daily volume) feature for CeFi instruments — strategy-side volume caps
summary: >-
  Strategy code needs a rolling-N-day average-daily-volume (ADV) signal per CeFi instrument, both to cap position size
  as a % of ADV and to gate an instrument as "not yet tradeable" until it has a minimum history of real volume. Surfaced
  during the ASTER 1000-multiplier-coin data-completeness work — some instruments show flat/degenerate funding rates and
  near-zero live 24h volume (e.g. 1000SATS at $6.04/24h, 1 trade), which is genuine illiquidity, not a pipeline defect,
  and needs a determinable downstream signal rather than manual eyeballing. MDPS's `processed_candles` already has the
  right schema (`volume`/`quote_volume` at `timeframe=24h`) for this, canonically keyed per instrument, but currently
  has zero coverage for the on-chain-perp CeFi venues (ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/ EXTENDED-STARKNET) — only
  legacy tardis-sourced CeFi venues have candles today. Decision — scaffold the ADV CONSUMER now against MDPS's existing
  canonical path/schema (so it activates automatically once candle coverage is extended to these venues, a separate
  deferred task), rather than building a parallel volume-computation pipeline.
status: active
nature: design
asset_group: [cefi]
stage: [data]
repos: [features-service, market-data-processing-service, market-tick-data-service]
scope: [engineer]
tags:
  [
    adv,
    average-daily-volume,
    volume-cap,
    liquidity,
    cross-instrument,
    mdps,
    processed-candles,
    funding-rate,
    illiquidity,
  ]
related:
  [
    aster_capture_broken_coverage_and_completeness_2026_07_20.md,
    ../../codex/02-data/data-lineage-MTDS-features-ml.md,
    ../../codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    "operator ask 2026-07-21: strategy-side volume caps as % of ADV, min-7-day-history-to-trade gate, discovered while
    diagnosing ASTER funding-rate realism for the 1000-multiplier coins (1000SHIB/1000SATS showing flat funding +
    near-zero live volume)",
  ]
---

# Rolling ADV feature for CeFi instruments

## Why (evidence)

Diagnosing whether ASTER funding-rate data is realistic (operator question, 2026-07-21) surfaced that funding-rate
variance correlates with liquidity but isn't a clean function of it alone (a live-API cross-check showed one coin,
1000WOJAK, with genuinely high funding variance at only modest volume). The determinable, no-extra-fetch signal that
DOES work is a rolling distinct-value count on `funding_rate` itself — but the operator separately asked for the more
general, standard tool: a real ADV feature, so strategy code can (a) cap position size at some % of ADV and (b) refuse
to trade an instrument until it has amassed a minimum trailing history of real volume (proposed: 7 days).

Live-API spot-check (2026-07-21) of the 10 ASTER 1000-multiplier coins found volume spanning
**$6.04/24h (1000SATS, 1
trade)** to **$536,278/24h (1000PEPE, 824 trades)** — a >80,000x range within a single MVP-gated
instrument set. This is exactly the kind of dispersion an ADV-based cap/gate is meant to catch, and it isn't
ASTER-specific — every CeFi venue has a long illiquid tail.

## Design decision (2026-07-21)

**MDPS's `processed_candles` is the right source** — `venue={V}/{instrument_id}.parquet` keyed, `timeframe=24h` candles
carry `quote_volume` directly (see `codex/02-data/data-lineage-MTDS-features-ml.md` § Layer 2, corrected 2026-07-21 with
the real verified path). It is NOT currently populated for the 4 on-chain-perp CeFi venues
(ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET) — confirmed via a direct GCS listing on a recent day, zero
`pipeline_mode=batch_aster`/`batch_hyperliquid`/etc. objects under `processed_candles/`, even for HYPERLIQUID which has
2+ years of raw trade history.

**Decision: do NOT extend MDPS's candle-building scope right now** (separate, deferred future task — Phase 2 below).
Instead, scaffold the ADV **consumer** against MDPS's existing canonical path/schema, so it activates the moment that
gap closes, with zero additional wiring. This plan tracks Phase 1 (the consumer) as done/in-review; Phase 2 (extending
MDPS candle coverage to the 4 venues) is explicitly NOT started.

## Codex SSOTs

- `codex/02-data/data-lineage-MTDS-features-ml.md` § Layer 2 — MDPS canonical path (corrected 2026-07-21) + the
  on-chain-perp coverage gap note.
- `plans/active/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md` — the ASTER data-completeness work
  this originated from, including the funding-rate realism finding.

## Progress Log

- 2026-07-21 — Plan created (human/local track, per operator's explicit answer to the plan-destination question).
  Dispatched the Phase-1 scaffold to a sub-agent in parallel with unrelated ASTER manifest remediation work. Codex
  updated (data-lineage doc's MDPS path correction + coverage-gap note; manifest-consolidator-ssot.md's CAS-marker
  gotcha, a related-but-separate finding from the same session).

## Phase 1 — ADV consumer (scaffold against MDPS's existing schema)

- [ ] [DATA] P1. Implement a reusable rolling-window ADV reader in
      `features-service/features_service/cross_instrument/app/calculators/adv.py` (sibling to `book_depth.py`, matching
      its calculator/interface conventions) that reads MDPS `timeframe=24h` candles for
      `(venue, instrument_id, asset_group)` across a trailing window (parameterized `window_days`, default 7),
      summing/averaging `quote_volume`, resolving the bucket via `resolve_bucket_name(...)` (never a hardcoded bucket
      name). — _dispatched to a sub-agent 2026-07-21; the file exists on disk with a companion
      `tests/cross_instrument/unit/test_adv.py` (confirmed via `git status`, both still uncommitted as of this write) —
      the sub-agent reported its own quality-gate run passing 17,766 tests (19 of them the new ADV tests) but had not
      yet completed its final quickmerge ship as of this session's pre-compact checkpoint. If a fresh session picks this
      up: check `git -C features-service log --oneline -3` and `git -C features-service status --short` first — the
      agent may have since shipped independently; if the files are still uncommitted and no agent is running, review +
      ship them yourself (or re-dispatch) rather than re-implementing from scratch. Update this line with the exact
      commit SHA once shipped._
- [ ] [DATA] P1. Distinguish three result states in the return type: real ADV + `days_observed`, insufficient-history
      (fewer than `window_days` real candles — the "not yet tradeable" gate), and zero-coverage (venue not yet
      candle-built by MDPS at all, e.g. ASTER/HYPERLIQUID/LIGHTER/EXTENDED today) — missing candle files must be treated
      as "no data that day," never an error.
- [ ] [DATA] P1. Unit tests covering: full window of real data, partial window (correct partial-average or correctly
      flagged insufficient), zero data at all, and a known-value correctness check against mocked `quote_volume` inputs
      (mock the storage client the same way `test_book_depth.py` does).
- [ ] [REVIEW] P1. Confirm the shipped module against this plan + the data-lineage codex doc — file path, function
      signature, and `pipeline_mode` resolution approach must match what actually shipped (update both this plan and the
      codex doc with the real values once the sub-agent's final report lands; do not leave placeholder text in either
      doc).

## Phase 2 — extend MDPS candle coverage to on-chain-perp CeFi venues (NOT STARTED — separate future work)

- [ ] [DATA] P2. Extend MDPS's candle-building orchestration to cover `pipeline_mode=batch_aster` / `batch_hyperliquid`
      / `batch_lighter_api` / `batch_extended` raw trades (MTDS already captures these broadly; MDPS's candle
      scanner/writer just hasn't been pointed at them). Once this lands, Phase 1's consumer starts returning real ADV
      values for these venues with no code change.
- [ ] [DATA] P2. Backfill historical candles for these 4 venues' existing raw trade history (matches whatever range MTDS
      has already captured — see the ASTER issue doc for that venue's actual backfilled range, 2024-01-01 onward, not
      the UAC-native 2023-07-22 start until GAP-4 there is separately resolved).

## Phase 3 — wire ADV into strategy-side volume caps (NOT STARTED — depends on Phase 1 output being usable, does not need Phase 2 to start designing)

- [ ] [BACKEND] P2. Design + implement the strategy-side consumption of the ADV signal: position-size cap as a % of ADV,
      and the min-7-day-history-to-trade gate the operator asked for. _(Left intentionally light — needs a design
      conversation on where in the strategy pipeline this cap applies and what the % ceiling should be; not yet scoped
      in detail.)_
- [ ] [DATA] P3. _(stretch, optional)_ Consider whether `book_depth.py`'s currently-unfilled `adv_30d_usd` input should
      be wired to call the SAME Phase-1 utility with `window_days=30`, now that a real producer exists — out of scope
      for this plan, a candidate follow-up once Phase 1 ships.

## Deferred work after 2026-07-21

| Item                                     | Status      | Why deferred                                                |
| ---------------------------------------- | ----------- | ----------------------------------------------------------- |
| Phase 2 (MDPS candle coverage extension) | Not started | Operator explicit decision — consumer-first, producer later |
| Phase 3 (strategy-side wiring)           | Not started | Needs a design conversation on cap %/placement              |
| `book_depth.py` → Phase-1 utility wiring | Not started | Stretch, only after Phase 1 ships and proves out            |

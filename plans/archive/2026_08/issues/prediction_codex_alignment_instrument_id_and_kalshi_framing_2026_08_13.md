---
doc_type: issue
title: >-
  Prediction-market codex alignment: instrument-ID convention drift ACROSS codex (3 incompatible formats), and both
  Kalshi codex docs' BLOCKED-CREDENTIALS framing is stale
summary: >-
  Two findings routed via plan_reconciler (prediction tranche, 2026-08-09), parked per its own recommendation (neither
  is provable/auto-fixable from the documented record alone; both need an explicit codex-touching ruling). (1)
  /codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md documents
  {VENUE}:{MARKET_TYPE}:{EVENT_SLUG}@{OUTCOME} (self-flagged as an unresolved codification gap, G2), while
  /codex/02-data/prediction-schema-paths.md documents a structurally different
  POLYMARKET::UP_DOWN::{ASSET}::{TF}::{WINDOW_END_TS} format as canonical — and neither matches live
  canonical_instrument_id samples cited in prediction_phase_ab_residuals_2026_07_24.md (e.g.
  PRICE::BNB::UP_DOWN::2026-07-17::DIR). (2) Both codex docs' Kalshi framing (BLOCKED-CREDENTIALS, last_reviewed
  2026-05-22) reads stale — live capture has been running through day=2026-07-27 per prediction_phase_ab_residuals, and
  the actual residual gate is an operator ruling on live-order verification, not a credentials absence.
status: resolved
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, codex-alignment, instrument-id, canonicalisation, kalshi, ssot-contradiction]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md,
    /codex/02-data/prediction-schema-paths.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
  ]
created: 2026-08-13
author: main-agent (blocked-question BLK-8f289fba, originally routed by plan_reconciler prediction tranche 2026-08-09)
source:
  "plan_reconciler prediction-tranche run, 2026-08-09 — 2 codex-alignment findings requiring an operator/codex-touching
  ruling before any SSOT edit (plan_reconciler never edits codex autonomously)."
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 1.0
drift_direction: advance-code
parent_epic: predictions_master
depends_on: []
resolved_by: /unified-trading-pm@98c5d710dc + interactive-session-2026-08-14-doc-rewrite
locked_by:
archived: "2026-08-14"
last_updated: 2026-08-13
context_scope:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md,
    /codex/02-data/prediction-schema-paths.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
  ]
---

> **ARCHIVED 2026-08-14** — both findings resolved via direct codex rewrite (interactive session): Finding 1
> (instrument-ID drift) was a false conflict between two different fields (`instrument_id` vs `canonical_event_id`), not
> a format to pick — both codex docs rewritten to describe the real single-dispatcher `instrument_id` and the separate
> `canonical_event_id` cross-venue/sports matching key; G2 deleted from the codification-gaps register. Finding 2 (stale
> Kalshi `BLOCKED-CREDENTIALS` framing) corrected on both docs, `last_reviewed` bumped to 2026-08-14. Shipped
> `unified-trading-pm@98c5d710dc` (Finding 2) + a follow-up commit (Finding 1 + this archival).

# Prediction-market codex alignment: two parked findings

## Finding 1 — instrument-ID convention drift ACROSS codex itself (3 incompatible formats)

Three different instrument-ID shapes exist for prediction markets, none of them reconciled against each other:

1. `/codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md` documents
   `{VENUE}:{MARKET_TYPE}:{EVENT_SLUG}@{OUTCOME}` — and self-flags this as an unresolved codification gap (its own G2
   marker), i.e. even this doc doesn't claim the format is settled.
2. `/codex/02-data/prediction-schema-paths.md` documents a structurally different canonical form:
   `POLYMARKET::UP_DOWN::{ASSET}::{TF}::{WINDOW_END_TS}`.
3. **Neither matches what's actually live.** `prediction_phase_ab_residuals_2026_07_24.md` cites real
   `canonical_instrument_id` samples, e.g. `PRICE::BNB::UP_DOWN::2026-07-17::DIR` — a third shape distinct from both
   codex docs (leads with `PRICE`, not a venue name; date positioned differently; a `DIR` outcome suffix neither doc
   describes).

This needs a ruling on which format is actually canonical (or that codex needs a real update to match live reality), not
a guess — a wrong pick risks codifying a format nothing actually writes.

## Finding 2 — both codex docs' Kalshi framing reads stale

Both `/codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md` and
`/codex/02-data/prediction-schema-paths.md` frame Kalshi as `BLOCKED-CREDENTIALS` (`last_reviewed: 2026-05-22`). Live
capture has been running through `day=2026-07-27` per `prediction_phase_ab_residuals_2026_07_24.md` — over two months
past that review date. The actual current residual gate (per the same doc) is an **operator ruling on live-order
verification**, not a credentials absence. The `BLOCKED-CREDENTIALS` framing misleads a reader into thinking Kalshi
capture is still not running at all.

## Why parked, not fixed here

Both are genuine scope/authority calls, not fact-checkable-and-fixable in place: which of the 3 instrument-ID formats is
canonical is a real design decision (not something derivable by reading further — a wrong pick propagates), and the
Kalshi framing needs someone to confirm the CURRENT actual gate state (live-order-verification ruling status) before
rewriting the codex text, not just delete the stale marker. Per `plan_reconciler`'s own operating rule: it never edits
codex autonomously.

## Todos

- [x] ✅ [OPERATOR] P2. **DONE 2026-08-14 (interactive session, operator confirmed).** Not a competing-format pick —
      `instrument_id` (VENUE:TYPE:SYMBOL, `build_canonical_instrument_id()`) and `canonical_event_id`
      (`PredictionMarketCrossVenueMapping`, cross-venue/cross-asset-group matching key incl. football via
      `api_football_fixture_id`) are two different fields that were never meant to be the same shape. Rewrote
      `prediction-markets.md`'s Instrument ID Convention section (deleted the fictional
      `{VENUE}:{MARKET_TYPE}:{EVENT_SLUG}@{OUTCOME}` pattern) and `prediction-schema-paths.md`'s Canonical Instrument ID
      Format table (added a DELTA banner marking the `POLYMARKET::...` formats as never-shipped/superseded). Deleted the
      now-resolved G2 row from `prediction-markets-codification-gaps.md` per its own "close a gap = delete its row" rule
      (G3 left open — not verified as fully resolved, only G2's exact claim was investigated).
- [x] ✅ [OPERATOR] P2. **DONE 2026-08-14 (interactive session, operator confirmed).** Updated both codex docs'
      `BLOCKED-CREDENTIALS` delta banners + venue table row to reflect actual state (live capture running past
      `day=2026-07-27`, dead-host bug fixed and regression-guarded `e2e-testing@371ac1b`, real `KALSHI:...` rows
      landing; actual gate = operator ruling on live-order verification, not credentials absence). `last_reviewed`
      bumped to 2026-08-14 on both `/codex/02-data/prediction-schema-paths.md` and
      `/codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md`.

## Progress Log

- 2026-08-14 (interactive session): investigated Finding 1 (instrument-ID drift) before ruling — found
  `build_canonical_instrument_id()`
  (`unified-api-contracts/unified_api_contracts/internal/reference/canonical_id_builder.py:1027`) is the
  ALREADY-OPERATOR-RULED (`instrument_id_format_canonicalization_2026_07_08.md`) single dispatch entry point: prediction
  → `VENUE:TYPE:SYMBOL` (matches the live `KALSHI:PREDICTION_MARKET:KXBNB15M-...` sample), sports →
  `LEAGUE:MATCHUP:DATE` (deliberately different, sports has no clean TYPE/SYMBOL concept). Separately, the
  `PRICE::{ASSET}::{BET_TYPE}::{SETTLEMENT_KEY}::{STRIKE_TOKEN}` shape is `canonical_event_id`, NOT `instrument_id` — a
  different field entirely, built by
  `unified-api-contracts/unified_api_contracts/canonical/domain/predictions/cross_venue_mapping.py` specifically to
  answer "is this Kalshi market the same individual contract as that Polymarket market", and it already supports sports
  matching via an optional `titles` map. So the doc's "3 incompatible formats" framing conflates two different fields
  (instrument_id vs. canonical_event_id) that were never meant to be the same shape. Fix-in-place: update
  `prediction-markets.md`'s G2 marker and `prediction-schema-paths.md`'s canonical-form section to (1) point
  `instrument_id` at the single dispatcher's real output shape, (2) document `canonical_event_id` as the separate
  cross-venue/cross-asset-group matching key. Operator instrument-ID todo left open pending that doc rewrite (not done
  in this entry — a real edit, not just a ruling restatement).

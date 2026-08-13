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
status: open
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
resolved_by:
locked_by:
last_updated: 2026-08-13
context_scope:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md,
    /codex/02-data/prediction-schema-paths.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
  ]
---

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

- [ ] [OPERATOR] P2. **Rule which instrument-ID format is canonical** for prediction markets — reconcile
      `prediction-markets.md`'s `{VENUE}:{MARKET_TYPE}:{EVENT_SLUG}@{OUTCOME}` (self-flagged G2, unresolved),
      `prediction-schema-paths.md`'s `POLYMARKET::UP_DOWN::{ASSET}::{TF}::{WINDOW_END_TS}`, and the live
      `PRICE::BNB::UP_DOWN::2026-07-17::DIR`-shaped samples into ONE documented canonical form (or confirm they
      legitimately coexist for a stated reason, e.g. schema versioning — and document that instead). Update both codex
      docs to match once ruled.
- [ ] [OPERATOR] P2. **Confirm Kalshi's current actual capture/gate state** and update both codex docs'
      `BLOCKED-CREDENTIALS` framing to reflect it (per `prediction_phase_ab_residuals_2026_07_24.md`, capture is running
      through `day=2026-07-27`; the real residual gate is an operator ruling on live-order verification). Bump
      `last_reviewed` on both docs once corrected.

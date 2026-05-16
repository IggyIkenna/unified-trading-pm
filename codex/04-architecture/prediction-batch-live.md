---
scope: [engineer, admin]
created: 2026-05-16
plan: plans/active/batch_live_symmetry_2026_05_10.md Tab 1 (P2 post-cutover placeholder)
status: placeholder
---

# Prediction Batch/Live Architecture

> Placeholder for the per-asset-group narrative for `asset_group=prediction`. Cross-cutting batch=live invariant lives
> in [`batch-live-architecture.md`](batch-live-architecture.md). Full content shipped post-cutover; this placeholder
> exists so `prediction-batch-live.md` is referenceable from the cross-asset-group meta section in
> `batch-live-architecture.md` without producing broken-link rot.

---

## §1 Prediction venues in scope (placeholder)

In-scope venues: **Polymarket** (CLOB API; primary), **Kalshi** (post-cutover). Polymarket is the May-23 cutover
target for the `arbitrage_event_markets` archetype. Kalshi + Polymarket cross-venue dispersion shipped post-cutover.

**Source of truth**: UAC `registry/capability_declarations/_prediction.py`.

## §2 Matcher pattern (placeholder)

Prediction-market matchers use the canonical L2 matcher with one prediction-specific layer: the
`prediction_canonical_question_group` axis groups synonymous markets across venues (e.g.
"will-X-event-happen-by-Y" on Polymarket vs Kalshi). The canonical-question-group registry lives in UAC
`canonical/domain/prediction/`; see
[`prediction_canonical_question_group_polymarket_migration_2026_05_06.md`](../../plans/active/prediction_canonical_question_group_polymarket_migration_2026_05_06.md)
for the cross-venue mapping rollout.

Detailed per-instrument-type matcher narrative ships post-cutover.

## §3 Shard atom + empty rules (placeholder)

Shard atom = `(asset_group=prediction, source, data_type, market_id, date)`. Market resolution events fire
`EXPECTED_MARKET_RESOLVED` empty reasons (closed-set per UAC
`canonical.crosscutting.honest_coverage.EmptyConfirmedReason`). Time-decay structure (binary-outcome markets vs
multi-outcome) governs the empty-vs-failed distinction.

Polymarket-specific rules:

* Pre-genesis-of-market dates → `EXPECTED_PRE_MARKET_GENESIS`.
* Resolved markets → `EXPECTED_MARKET_RESOLVED` (single timestamp; no further trades expected).
* Live-but-zero-volume slots → `SOURCE_RETURNED_ZERO` (not absence; market is open but quiet).

## §4 Integration with batch-vs-live equality (placeholder)

Same code-path principle as CeFi (see [`cefi-batch-live.md`](cefi-batch-live.md) § 5): there is ONE Prediction
pipeline. Mode-conditional logic is constrained to the CLI seam per
[`mode-axis-discipline.md`](../06-coding-standards/mode-axis-discipline.md) §4. The
`prediction_canonical_question_group` axis composes with `pipeline_mode` per the writegate plan's manifest schema —
batch + live runs produce identically-shaped parquets keyed by
`(market_id, canonical_question_group, pipeline_mode, day)`.

## §5 Cross-references

* [`batch-live-architecture.md`](batch-live-architecture.md) — cross-asset-group meta + L2/L3 matcher contract.
* [`cefi-batch-live.md`](cefi-batch-live.md) — sibling per-asset-group narrative (reference shape).
* [`tradfi-batch-live.md`](tradfi-batch-live.md) — sibling placeholder.
* [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) — partition-key contract.
* [`../06-coding-standards/mode-axis-discipline.md`](../06-coding-standards/mode-axis-discipline.md) — 4-axis cartesian
  rules + anti-pattern list.
* `unified-trading-pm/plans/epics/predictions_master_2026_05_07.md` — cutover-week prediction delivery plan.

## §6 Successor

Post-cutover follow-up: replace this placeholder with the full per-instrument-type narrative once Polymarket live
streaming + canonical-question-group cross-venue mapping fully land. Tracked in
`predictions_master_2026_05_07.md` "post-cutover follow-ups" section.

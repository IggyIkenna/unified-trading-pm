---
doc_type: issue
title: >-
  onchain feature manifest is dishonest (11 of 13 rows falsely `captured`), and the operator-authorized mark→recompute
  is blocked on two upstream defects: a frozen index/consolidator and missing MTDS chain-field collection
summary: >-
  Operator authorized (2026-07-21) marking the 6 false-captured + 5 feature-less onchain manifest rows to
  attempted_failed and then recomputing. Investigation found BOTH halves are blocked by deeper defects. MARK is blocked:
  the onchain availability_index has 13 rows all frozen at date=2026-01-25 all `captured`, despite GCS objects through
  2026-05-22 — the index-update/consolidator path is broken (measured no-op, shards_scanned=1/rows_in=0 against 723 live
  objects), so a proper ManifestWriter.record_failed cannot reach the index and a raw parquet edit is banned + fragile
  (a future consolidator run would clobber it). RECOMPUTE is blocked: the 5 feature-less calculators require input
  columns (ltv, liquidation_threshold, flash_loan_liquidity, health/collateral, reward_rate) that the upstream MTDS
  lending source does NOT collect — so rerunning produces the same empty shards. The producer-honesty fix already
  shipped (features-service@907e17b4) stops NEW runs from writing these as captured; the durable close is fix
  consolidator → mark via API → build the missing MTDS collectors → recompute.
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos: [features-service, market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest-honesty, consolidator, recompute-blocked, upstream-gap, defi, coverage-correctness]
related:
  [
    features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    silent_wrong_answer_audit_candidates_2026_07_20.md,
  ]
created: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "operator ruled mark→recompute 2026-07-21; investigating the mark mechanism + recompute feasibility found both
    blocked by a frozen consolidator and a missing MTDS collection gap",
  ]
resolved_by:
locked_by:
---

# onchain manifest dishonest + mark→recompute blocked

## The 13 index rows (onchain/\_index/availability_index.parquet), all `date=2026-01-25`, all `captured`

| feature_group           | instrument_count | GCS objects    | verdict                             |
| ----------------------- | ---------------- | -------------- | ----------------------------------- |
| lending_rates           | 14,630,914       | real (15 cols) | ✅ correct                          |
| lst_yields              | 1,602            | real (8 cols)  | ✅ correct                          |
| health_factor           | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| rewards                 | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| liquidation_events      | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| risk_params             | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| flash_loan_availability | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| perp_funding_rates      | 0                | none           | ❌ should be attempted_failed/empty |
| macro_sentiment         | 0                | none           | ❌ should be attempted_failed/empty |
| lst_native_rates        | 0                | none           | ❌ should be attempted_failed/empty |
| rate_impact             | 0                | none           | ❌ should be attempted_failed/empty |
| onchain_perps           | 0                | none           | ❌ should be attempted_failed/empty |
| utilization             | 0                | none           | ❌ should be attempted_failed/empty |

(The identical `instrument_count=14,630,914` across five different groups AND lending_rates is itself implausible as a
per-group count — a separate count-provenance bug, not chased here.)

## Blocker 1 — MARK cannot be applied cleanly (frozen index / broken consolidator)

The index is frozen at a single day (`2026-01-25`) while GCS objects exist through `2026-05-22` (118 day partitions).
The index-update/consolidator path is broken: measured `shards_scanned=1 / rows_in=0` against 723 live objects — it has
stopped scanning and stopped self-correcting. Consequences for the mark:

- `ManifestWriter.record_failed` (writes `capture_status="attempted_failed"`) writes to the per-run/per-shard manifest
  layer that must be CONSOLIDATED into the index. With the consolidator no-op, a fresh `record_failed` never reaches the
  13-row index — so marking via the supported API is inert here.
- A raw rewrite of the 11 rows in `availability_index.parquet` is banned (manifest writes go through the writer/shard
  discipline, never a raw parquet edit) AND fragile: if the consolidator is ever repaired and re-runs, it would clobber
  the hand-edit (or loud-fail on the shape mismatch). Band-aiding a broken manifest masks the real defect.

**So the honest mark requires fixing the onchain index-update/consolidator FIRST**, then re-deriving the index from the
producer-honest shards (the producer fix `features-service@907e17b4` already emits the correct `attempted_failed` /
`empty_confirmed` states going forward). Diagnosing why the consolidator went no-op (and why onchain writes stopped at
2026-05-22) is the prerequisite.

## Blocker 2 — RECOMPUTE cannot produce features (missing MTDS collection)

The 5 feature-less calculators read input columns that the upstream source does not carry (verified against
`orchestrator_calculators.py` + the live `lending_rates` parquet schema):

| feature_group           | calculator needs (input cols)                  | present in source? |
| ----------------------- | ---------------------------------------------- | ------------------ |
| risk_params             | `ltv`, `liquidation_threshold`                 | **no**             |
| flash_loan_availability | `flash_loan_liquidity` / `available_liquidity` | **no**             |
| health_factor           | health/collateral fields                       | **no**             |
| liquidation_events      | liquidation fields                             | **no**             |
| rewards                 | `reward_rate`                                  | **no**             |

The `lending_rates` source carries only `aave_supply_apy` / `aave_borrow_apy` / `aave_utilization` /
`aave_liquidity_index` / `aave_borrow_index` / `aave_reserve_factor` / `rate_spread` — none of the fields above. So the
calculators correctly produce nothing, and **rerunning them yields the same empty shards.** Recompute is not a rerun —
it is NEW upstream work: MTDS (or the onchain collectors) must capture `ltv` / `liquidation_threshold` / reserve
`reward_rate` / flash-loan liquidity / the health-factor inputs from chain before these five groups can be real.

## The fix chain (durable close, in order)

1. **Diagnose + fix the onchain index-update/consolidator** (why frozen at 2026-01-25, why no-op vs 723 objects, why
   writes stopped 2026-05-22). Prerequisite to any honest coverage number.
2. **Re-derive the index from producer-honest shards** — with `907e17b4` shipped, the 11 groups then render
   `attempted_failed` / `empty_confirmed` honestly (this IS the "mark", done correctly via the pipeline, not by hand).
3. **Build the missing MTDS chain-field collectors** (ltv / liquidation_threshold / reward_rate / flash_loan_liquidity /
   health-factor inputs) — the real unblock for the 5 feature-less groups.
4. **Recompute** the five groups once their inputs exist.

## Recommendation

Do NOT hand-edit the frozen prod index (fragile band-aid on a broken subsystem). Treat step 1 (consolidator) as the
gating fix; the producer honesty is already shipped. Steps 3–4 are genuinely new scope (upstream collection), not a
rerun — size them as their own work, not as part of "mark→recompute". This reframes the operator's "mark now" as "fix
the consolidator so the already-shipped producer honesty propagates." </content>

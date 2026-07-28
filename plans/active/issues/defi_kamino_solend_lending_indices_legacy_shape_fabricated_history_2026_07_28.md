---
doc_type: issue
title:
  KAMINO/SOLEND `lending_indices` legacy `instrument_type=lending` shape carries fabricated history — a single
  2026-05-04/05 snapshot duplicated across ~2 years of `day=` partitions
summary: >-
  Probing item 6 of defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md (reconcile Track 2's
  47-object KAMINO lending_indices finding) surfaced a NEW, much larger fabrication: the legacy
  `instrument_type=lending` (old pre-SOLANA_LENDING-split schema, `timestamp` epoch field, no `ts_event`) shape for BOTH
  KAMINO and SOLEND `lending_indices` carries a SINGLE frozen snapshot (KAMINO: epoch 1777937251 = 2026-05-04 23:27:31
  UTC; SOLEND: epoch 1777937437 = 2026-05-04 23:30:37 UTC) duplicated verbatim across every sampled `day=` partition
  from at least 2024-06-01 through 2026-03-23 (coarse monthly probe, all present) — every market's tvl_usd identical
  across days, a `_migrated_kamino_lending_SOLANA_20260504_232646.parquet` filename confirms migration-script origin.
  The CURRENT-schema `instrument_type=solana_lending` shape (uses `ts_event`) is CLEAN — verified genuine on
  day=2026-04-14 (6/6 samples exact match). This is the SAME fake-history-snapshot bug class as the parent dex_pools
  issue, but in a population that issue's own investigation (item 4) explicitly could not locate ("inconclusive, not a
  clean bill") and Track 2's 47-object finding (defi_consolidated_closeout_2026_07_18.md, corrected in
  defi_dex_pools_delete_order_stale_2026_07_20.md to `instrument_type=lending`, NOT `solana_amm_pool` as originally
  stated) never checked for the fabrication signature — it only verified existence/counts for a delete-safety decision,
  already resolved (folded 2026-07-21, that SPECIFIC day=2026-04-14 population is genuinely clean per this doc's own
  probe).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, solana, kamino, solend, lending-indices, fake-history, data-correctness, fabrication]
related:
  [
    /plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md,
    /plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
    /plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md,
    /plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-28"
source:
  defi_satellite_ao_dispatch_batch1_2026_07_25.md's "resolve Kamino/Solend lending_indices shape conflict" todo (slot-2,
  data_engineering)
resolved_by:
locked_by:
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

## What I found

Dispatched to resolve item 6 of `defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` (now archived):
reconcile Track 2's claim of "47 real KAMINO `lending_indices` objects under `instrument_type=solana_amm_pool`" against
the current `resolve_lending_instrument_type()` writer (which produces `instrument_type=solana_lending` for
KAMINO/SOLEND) and record a definitive verdict.

### Part 1 — the reconciliation (item 6's original ask): RESOLVED, no live bug in that specific population

Live GCS probe (`gs://market-data-tick-defi-prd-central-element-323112`, day=2026-04-14, the exact day Track 2
originally probed):

```
venue=KAMINO/chain=SOLANA/instrument_type=solana_vault/data_type=dex_pool_state/   (unrelated — vault data)
venue=KAMINO/chain=SOLANA/instrument_type=solana_lending/data_type=lending_indices/  53 objects
venue=KAMINO/chain=SOLANA/instrument_type=lending/data_type=lending_indices/         58 objects
venue=SOLEND/chain=SOLANA/instrument_type=solana_lending/data_type=lending_indices/  73 objects
venue=KAMINO/chain=SOLANA/instrument_type=solana_amm_pool/  — ZERO objects, any data_type, any pipeline_mode
```

`instrument_type=solana_amm_pool` does not exist for KAMINO `lending_indices` at all — Track 2's original prose
(`defi_consolidated_closeout_2026_07_18.md:345`) was corrected by its own successor doc
(`defi_dex_pools_delete_order_stale_2026_07_20.md`'s verification table): the real shape is `instrument_type=lending`
(47 objects on 2026-07-20's probe, 44 post-delete-verification 2026-07-21), not `solana_amm_pool`. That population is
the LEGACY-schema twin that was folded into the canonical `raw_tick_data/by_date/...` hive tree as part of the
2026-07-21 `dex_pools/`+`lending_indices/` legacy-prefix fold+delete (`mtds@13b9dac5`).

Sampled 6 objects across both `instrument_type=lending` and `instrument_type=solana_lending` for KAMINO+SOLEND on
day=2026-04-14 specifically — the `ts_event`/timestamp column matches `day=2026-04-14` in **6/6 samples** (exact match,
same pattern as item 5's clean 30/30 result). **This specific day's population, for both shapes, is genuine.**

### Part 2 — a NEW finding: the `instrument_type=lending` shape is fabricated on EVERY OTHER sampled day

While reconciling, sampled `instrument_type=lending` (the OLD, pre-SOLANA_LENDING-split schema — no `ts_event` column,
instead a `timestamp` UNIX-epoch integer field) on days OTHER than 2026-04-14, mirroring the parent issue's
"day=2025-01-08..2025-01-12" affected-window sample:

```python
day=2025-01-08: raw timestamp=1777937251 -> actual UTC date=2026-05-04 23:27:31  MATCH=False
day=2025-01-10: raw timestamp=1777938774 -> actual UTC date=2026-05-04 23:52:54  MATCH=False
day=2025-01-12: raw timestamp=1777939810 -> actual UTC date=2026-05-05 00:10:10  MATCH=False
```

**Every one of the 55 KAMINO market objects on `day=2025-01-08` carries the IDENTICAL `timestamp=1777937251`**
(2026-05-04 23:27:31 UTC) — a single frozen snapshot moment, not per-market real historical data. tvl_usd values are
frozen too (e.g. market `019b43fe-...` = 3,502,331.0 on 2025-01-08/10/12, vs. the GENUINE `ts_event`-tagged
day=2026-04-14 object for the same market = 3,705,939.0 — different values, confirming the fake-day objects are NOT
simply a copy of the 2026-04-14 real data either, but a distinct, separately-fabricated snapshot). One object is
literally named `_migrated_kamino_lending_SOLANA_20260504_232646.parquet` — the filename itself encodes the fabrication
timestamp (2026-05-04 23:26:46), confirming migration-script origin, not a genuine per-day capture.

**SOLEND is affected too, at LARGER scale**: `day=2025-01-08` has **595** `instrument_type=lending` objects, every one
sampled carrying the identical `timestamp=1777937437` (2026-05-04 23:30:37 UTC, ~3 min after KAMINO's — consistent with
one migration run processing KAMINO then SOLEND sequentially).

**Scope (coarse monthly probe, presence-only, NOT a full sweep — a proper scan is follow-up work, see Todos)**:
`instrument_type=lending` is PRESENT for KAMINO on every sampled day from **2024-06-01 through 2026-03-23** (~21
months). SOLEND is present 2024-06-01 through ~2025-06-26, then intermittently absent from 2025-07 onward (exact cutover
unconfirmed — needs the real scan). GCS object `time_created` for these fabricated-day objects clusters around
**2026-07-19 to 2026-07-21** — i.e. they were physically WRITTEN during the same window as the legacy-prefix fold
operation (`mtds@13b9dac5`, 2026-07-21) — but the ROW-LEVEL content (the frozen `timestamp` field) shows the underlying
fabrication happened earlier, around **2026-05-04/05** (per the embedded epoch + the `_migrated_...` filename), and the
fold operation faithfully relocated/replicated that already-fabricated content into the new canonical hive-shaped path
across many `day=` partitions without validating it.

## Why it matters

This is the SAME fake-history-snapshot bug class the parent
`defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` existed to fix for `dex_pools/` — a single
point-in-time snapshot masquerading as multi-year historical data. Any downstream consumer treating KAMINO/SOLEND
`lending_indices` under `instrument_type=lending` as real historical time-series (backtesting, feature computation,
historical APY/TVL analysis) is currently reading fabricated data for potentially ~21 months of "history" that never
actually existed at those dates. Unlike the CURRENT-schema `instrument_type=solana_lending` population (verified clean),
this legacy shape has NOT been through the parent issue's fabrication sweep — it was invisible to that investigation
(item 4 explicitly flagged it as an unresolved gap, "inconclusive, not a clean bill") because nobody had yet identified
`instrument_type=lending` as lending's real legacy path shape until this session's probe.

## Recommended decision

This needs the SAME disposition process as the parent dex_pools issue (operator ruling required, per that issue's own
todo-1 precedent: "OPTION B" — see `defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` todo 1 for
the decision framework to reuse). Do NOT delete or relabel unilaterally — this needs the same care (legacy data may be a
canonical twin's only copy for some cells, same as the dex_pools finding).

## Todos

- [ ] [OPERATOR] P0. **Rule on disposition** for the `instrument_type=lending` KAMINO/SOLEND fabricated population,
      mirroring `defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` todo 1's decision framework
      (relabel-forward vs. delete vs. retain-with-warning-flag). Key question: does ANY consumer currently read this
      shape as real historical data (grep `instrument_type=.lending.` read-sites across strategy-service/
      features-service, mirroring the parent issue's `solana_amm_depth_provider.py` read-site discovery)? (repo:
      unified-trading-pm — operator decision)
- [ ] [DATA] P1. **Full-scope scan** (VM-scale, per the heavy-I/O HARD RULE — this is NOT a local-session task) to
      determine the EXACT affected date range + total fabricated-object count for both KAMINO and SOLEND
      `instrument_type=lending` `data_type=lending_indices`, mirroring the parent issue's own full-scope sweep
      methodology (day-by-day or sharded date-range GCS walk, sampling each day's `timestamp` field against its `day=`
      partition). Confirm the exact boundary where SOLEND's presence becomes intermittent (2025-06-26 to 2025-07-26
      window, coarse probe only). (repo: market-tick-data-service)
- [ ] [DATA] P1. **Check whether other data_types under `instrument_type=lending`** (not just `lending_indices` — the
      legacy schema may also cover `liquidations`/`liquidation_events`/`position_data` per `_lending_grain.py`'s doc
      comment listing 6 lending-family handlers) carry the same fabrication signature. (repo: market-tick-data-service)
- [ ] [REVIEW] P2. Once the operator rules on disposition (todo 1) and the full scope is known (todo 2), execute the fix
      (relabel-forward migration mirroring `mtds` `dcbed674`-class todo-3 fix from the parent issue, or delete per the
      operator's ruling) + verify with a clean re-scan. (repo: market-tick-data-service)

## Lesson (do not re-learn)

**A "clean bill" claim from checking only ONE candidate instrument_type shape is not proof of absence — this
investigation itself is the third shape-mislabeling in this exact lending_indices data (the original issue said
`instrument_type=pool`, Track 2 said `solana_amm_pool`, the REAL affected shape was `instrument_type=lending`).** When a
fabrication-class bug is suspected in a dataset with multiple historical writer-generation shapes, enumerate EVERY
instrument_type folder actually present under the venue/chain prefix (a `delimiter="/"` listing, not a guess) before
concluding a shape doesn't exist — a guessed prefix returning 0 objects reads identically to "genuinely doesn't exist"
and "wrong guess," and only a live folder enumeration disambiguates the two.

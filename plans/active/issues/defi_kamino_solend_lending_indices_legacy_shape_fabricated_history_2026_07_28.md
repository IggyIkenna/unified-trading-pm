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

> **⚠️ SCOPE CORRECTION 2026-07-28 (slot-14, todo 2's full-scope scan)** — the frontmatter `title`/`summary` above
> ("duplicated verbatim across ~2 years of `day=` partitions") reflects the ORIGINAL coarse, presence-only probe and is
> now known to OVERSTATE the true scope. A full day-by-day scan (2023-01-01..2026-07-28, every present day individually
> classified, not sampled-monthly) found the fabrication is a SHARP, NARROW window — `2025-01-01` through `2025-01-16`
> (SOLEND) / `2025-01-17` (KAMINO), ~16-17 days, not ~21 months. See the "Full-scope scan" todo below for full
> evidence + methodology. Left the original title/summary text unchanged (historical record of what was known at
> creation time) rather than rewritten — read this correction alongside them, not instead of them.

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

**RESOLVED (2026-07-28 gate-cleanup pass) — this is NOT a fresh operator decision.** The parent dex_pools issue's todo 1
already litigated this exact decision framework for the SAME fabrication bug class and the operator already ruled option
(b) — relabel-forward, not wipe, not leave-in-place
(`defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` todo 1, operator verbatim: "OK YEAH WE need to
relabel to reality"). This population is structurally identical (a single frozen migration-script snapshot duplicated
across historical `day=` partitions) — there is no new fact here that would change that ruling, so it applies directly
rather than needing to be re-asked. Do NOT delete or relabel unilaterally without following the same
copy-forward-then-flag-old-for-human-delete mechanics the parent issue's fix already validated (legacy data may be a
canonical twin's only copy for some cells, same as the dex_pools finding).

## Todos

- [x] ✅ **RETAGGED from `[OPERATOR]` and RESOLVED (2026-07-28 gate-cleanup pass).** **Disposition**: no longer an open
      decision — cite the standing `defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` todo 1
      ruling (option b, relabel-forward) directly; it governs this population too (same fabrication mechanism, same
      remedy). The follow-on fix (todo 4 below) should apply the SAME validated migration pattern
      `market-tick-data-service@67524cbb`'s `scripts/relabel_solana_dex_pools_fake_history.py` already implements and
      proved end-to-end: for each affected object, derive `<true_date>` from the row's own `timestamp` column (NOT
      `available_at`/write-time), write a NEW object at the canonical path under that true date with the correct
      live-mode `pipeline_mode`, `record_captured` only the new path, and leave the OLD mislabeled object un-recorded
      (never delete-on-relabel) pending a later human delete decision. **Consumer-read investigation — done as separate,
      ordinary read-only AO work (not part of the disposition gate), concrete result found**: grepped `strategy-service`
      and `features-service` for `instrument_type=lending`-shaped read sites. `strategy-service`: zero hits (it consumes
      computed features, not raw MTDS `instrument_type=`-partitioned parquets, directly). `features-service`:
      `OnChainDataLoader._resolve_mtds_parquet_files()` / `_probe_mtds_blobs()`
      (`features_service/onchain/app/core/data_loader.py:138-159`) is the real read site for the `rate_indices` bypass
      data-type (on-disk `data_type=lending_indices`) — it matches blobs purely by
      `data_type_segment ("data_type=lending_indices/") in blob_name`, with **no `instrument_type` filter at all** (the
      method's own docstring even shows the glob as `instrument_type=*`). **This means the reader does NOT distinguish
      `instrument_type=lending` (fabricated legacy shape) from `instrument_type=solana_lending` (clean current shape) —
      it ingests whichever objects exist under the queried day, so YES, this consumer currently reads the fabricated
      population as real historical data whenever both shapes co-exist under the same `day=` prefix.** This makes the
      fix more urgent (real downstream pollution, not just latent risk) but does not change the already- ruled
      disposition. Original ask, preserved for context: **Rule on disposition** for the `instrument_type=lending`
      KAMINO/SOLEND fabricated population, mirroring
      `defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` todo 1's decision framework
      (relabel-forward vs. delete vs. retain-with-warning-flag). (repo: unified-trading-pm)
- [x] ✅ [DATA] P1. **Full-scope scan — DONE 2026-07-28 (slot-14), MAJOR CORRECTION to the presence-only coarse probe's
      implied scope.** Reassessed against the heavy-I/O HARD RULE before launching a VM: this is a BOUNDED, SAMPLED scan
      (one delimiter-bounded `list_blobs` + one small parquet read per (day, venue) cell, never a whole-corpus
      walk/materialization), so it qualifies for the CLAUDE.md bounded-work exemption and ran in-session — no VM needed.
      Script (committed, reusable):
      `market-tick-data-service/scripts/scan_kamino_solend_legacy_lending_fabrication_2026_07_28.py`. Validated first
      against the known-fabricated window (2025-01-06..2025-01-14, matched the doc's own 3 spot-checks 3/3) and the
      known-genuine day (2026-04-14, correctly GENUINE once the script was fixed to also accept the `ts_event` schema
      variant — the "genuine" day's object turned out to use `ts_event`/datetime64, not the legacy `timestamp`/epoch-int
      column the fabricated snapshot uses; both schemas coexist under this same legacy path).

      **Full scan 2023-01-01..2026-07-28** (1,305 days × 2 venues = 2,610 cells, 1 sample read per present cell, 0
                                  UNKNOWN/ambiguous cells):

                                  ```
                                  KAMINO: present 2023-01-01..2026-05-28 (1,231 present days) — 17 FABRICATED, 1,214 GENUINE
                                  SOLEND: present 2023-01-01..2026-05-28 (1,012 present days) — 16 FABRICATED,   996 GENUINE
                                  ```

                                  **The fabricated population is a SHARP, NARROW window: `2025-01-01` through `2025-01-16` (SOLEND) /
                                  `2025-01-17` (KAMINO) — 16-17 days, NOT the ~21-month range the coarse presence-only probe's phrasing implied.**
                                  Re-reading that probe's own words confirms it never claimed otherwise ("presence-only, NOT a full sweep" —
                                  it measured the SHAPE existing across ~21 months, not fabrication on every one of those days; the only actual
                                  fabrication evidence it had was the 3 spot-checked January-2025 days, which this scan now shows WAS the
                                  correct signal, just over-generalized in the summary framing). **Verified this isn't a same-day
                                  sampling blind-spot**: pulled EVERY object (not just 1 sample) for a GENUINE-classified day well inside the
                                  old presumed-fabricated window (`day=2024-06-15`, 45 KAMINO objects) — 45/45 genuine, 0 fabricated, confirming
                                  no intra-day mix the single-sample method could have missed. Verified the boundary is sharp via a dense
                                  2024-12-28..2025-01-25 re-scan: fabrication starts cleanly at `2025-01-01` and ends `2025-01-16/17`, no partial
                                  days.

                                  **Corrected object-count estimate**: at the doc's own measured per-day density (KAMINO ~55 objects/day,
                                  SOLEND ~595 objects/day), the TRUE fabricated population is roughly `17×55 + 16×595 ≈ 10,455` objects — an
                                  order of magnitude smaller than the ~21-month framing would have implied (which would have suggested tens of
                                  thousands more). This materially changes the disposition calculus for todo 1 (a 16-17 day gap is a much
                                  smaller/cheaper fix surface than ~21 months).

                                  **Absence note** (not fabrication, a separate observation): both venues are also fully ABSENT (no
                                  `instrument_type=lending` objects at all, not even fabricated ones) for `2023-03-31` through some point before
                                  `2023-05` (start of the scanned range's early gap) and again from `2026-05-29` onward through the scan's
                                  `2026-07-28` end — i.e. the legacy shape's total lifetime is `2023-01-01..2026-05-28`(ish) with this one
                                  narrow fabricated pocket inside it, not fabricated-then-clean-forever or clean-then-fabricated-forever.

                                  Full per-cell report (not committed — regenerable from the committed script + these exact date bounds, same
                                  pattern as the footystats/CF-11 migration reports in sibling sessions):
                                  `/tmp/kamino_solend_scan_report.json` (session-local, will not persist). (repo: market-tick-data-service)

- [x] ✅ [DATA] P1. **Check whether other data_types under `instrument_type=lending` — DONE 2026-07-28 (slot-5),
      VERDICT: NO other data_type exists for KAMINO/SOLEND under this shape; the fabrication is confined to
      `lending_indices` by construction, not just by absence.** Script (committed, reusable):
      `market-tick-data-service/scripts/scan_kamino_solend_lending_other_datatypes_2026_07_28.py`.

      **Live GCS enumeration (never guessed a data_type name — per this doc's own "Lesson")**
          across 91 scanned days: daily coverage of 2024-12-20..2025-02-05 (the confirmed
          lending_indices fabrication window with margin) + a monthly sweep of the shape's full
          measured lifetime (2023-01-01..2026-07-01, one day/month) + the 2 known control days
          (2026-04-14 genuine, 2024-06-15 genuine) — 610 (day, pipeline_mode) cells checked for
          KAMINO/SOLEND presence, 169 shard-atom sightings found, **zero** carrying any `data_type`
          other than `lending_indices` (`instrument_type=lending/data_type=lending_indices/` is the
          ONLY data_type folder ever present under
          `venue={KAMINO,SOLEND}/chain=SOLANA/instrument_type=lending/`, at any sampled point across
          the shape's entire lifetime). Of the 169 `lending_indices` sightings, 33 carried the known
          fabrication epoch signature (`timestamp`/`ts_event` decoding into the 2026-05-04/05
          migration-run neighborhood on a day it doesn't belong to) — consistent with, not a new
          finding beyond, the parent todo's 17/16-day fabricated-window result.

          **Root cause of the "zero elsewhere" result — a structural code guarantee, not just an
          absence in this scan's sample**: of the 6 lending-family handlers named in
          `_lending_grain.py`'s doc comment (`lending_indices`/`liquidations`/`liquidation_events`/
          `flash_loan_events`/`position_data`/`risk_params`), 4 (`liquidations`, `liquidation_events`,
          `flash_loan_events`, `position_data`) only ever fetch from EVM protocols (Aave V3/
          Compound V3/Morpho/Uniswap V3 per their own docstrings) — Kamino/Solend never appear in
          their source protocol lists at all, so they structurally cannot write under
          `venue=KAMINO|SOLEND`. The 5th, `risk_params_handler.py`, DOES include `kamino_lending` in
          its `_DEFAULT_PROTOCOLS` — but `resolve_lending_instrument_type()` (the SAME single
          shard-atom resolver every lending-family writer imports, `_lending_grain.py:45-60`) maps
          `kamino_lending`/`solend`/`marginfi` protocols to `InstrumentType.SOLANA_LENDING`, NEVER to
          the legacy `LENDING` type any writer would need to reach the
          `instrument_type=lending/` path this issue is scoped to. So even a future/backfilled
          `risk_params` capture for `kamino_lending` would land under `instrument_type=solana_lending`
          (the CURRENT, verified-clean schema — out of this issue's scope), not the legacy fabricated
          shape — by construction, not by luck. **The legacy `instrument_type=lending` shape for
          KAMINO/SOLEND is therefore closed/frozen to `lending_indices` only, both retrospectively
          (this scan) and going forward (no current writer can ever add to it).**

          This materially simplifies the fix surface for the todo below: it is `lending_indices`
          alone, not a multi-data_type sweep. (repo: market-tick-data-service)

- [ ] [REVIEW] P2. **Disposition already resolved (todo 1) — no operator wait needed here.** Full scope is now known
      (todo 2: `lending_indices` only, no other data_type affected). Execute the fix (relabel-forward migration
      mirroring `market-tick-data-service@67524cbb`'s `relabel_solana_dex_pools_fake_history.py` pattern, per the
      standing option-b ruling cited in todo 1) + verify with a clean re-scan. (repo: market-tick-data-service)

## Lesson (do not re-learn)

**A "clean bill" claim from checking only ONE candidate instrument_type shape is not proof of absence — this
investigation itself is the third shape-mislabeling in this exact lending_indices data (the original issue said
`instrument_type=pool`, Track 2 said `solana_amm_pool`, the REAL affected shape was `instrument_type=lending`).** When a
fabrication-class bug is suspected in a dataset with multiple historical writer-generation shapes, enumerate EVERY
instrument_type folder actually present under the venue/chain prefix (a `delimiter="/"` listing, not a guess) before
concluding a shape doesn't exist — a guessed prefix returning 0 objects reads identically to "genuinely doesn't exist"
and "wrong guess," and only a live folder enumeration disambiguates the two.

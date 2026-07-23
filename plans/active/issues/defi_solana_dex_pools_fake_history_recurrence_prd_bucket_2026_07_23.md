---
doc_type: issue
title:
  Solana DeFi dex_pools legacy shape in the -prd- bucket carries the SAME fake-history-snapshot bug
  solana_defi_fake_history_snapshot_2026_06_17.md already fixed once, in a scope that fix never scanned
summary: >-
  While monitoring the 2026-07-23 defi orphan-sweep + planning its backfill, sampled real
  raw_tick_data/by_date/day=2025-01-*/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=ORCA|RAYDIUM/
  chain=SOLANA/instrument_type=pool/data_type=dex_pools/ objects in market-data-tick-defi-prd-central-element-323112.
  Every sampled row's own timestamp column resolves to 2026-05-04/05-05 (a year+ after the day= partition it is filed
  under), and available_at is uniformly 2026-06-11T09-48-03 across every day= partition sampled -- the exact signature
  of the already-diagnosed "one live snapshot back-dated across every historical partition" bug. The prior fix (commit
  aa3b9f18, forward-only-honest write gate) plus its 6000-object cleanup targeted only the OLD flat prefix
  (dex_pools/PROTOCOL/SOLANA/date=star/) and a non-prd bucket variant (Gate 7,
  solana_defi_legacy_migration_2026_05_27.md, 2823 objects, fully migrated 2026-05-28) -- neither covers this
  hive-shaped, -prd- bucket population. Scanning the live sweep's own already-written checkpoint shards -- 241,281 of
  3,074,283 actionable rows found so far (7.8 pct) carry this exact data_type=dex_pools legacy shape, venues ORCA +
  RAYDIUM, days 2025-01-01 through 2025-01-17 (bounded so far; the sweep has not finished and may find more as it
  continues). MUST NOT be record_captured as genuine historical coverage until ruled on.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [defi, solana, orca, raydium, fake-history, data-correctness, orphan-sweep, canonical-migration]
related:
  [
    ../archive/issues/solana_defi_fake_history_snapshot_2026_06_17.md,
    ../archive/2026_07/solana_defi_legacy_migration_2026_05_27.md,
    estate_orphan_assessment_2026_07_21.md,
    defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-23
parent_epic: defi_master
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
assigned_vm: NA
execution_scope: local-only
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py,
    market-tick-data-service/scripts/migrate_legacy_solana_defi_to_canonical.py,
    unified-trading-library/unified_trading_library/availability_stamping.py,
  ]
depends_on: []
---

# defi Solana dex_pools fake-history recurrence in the -prd- bucket (2026-07-23)

## What I found

Investigating why the 2026-07-23 defi orphan-sweep was finding ~99% orphan rates in the Jan-2025 region (operator asked
"how do we know instruments captured match the catalogue and aren't fabricated"), sampled 10 real objects under:

```
gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2025-01-0{8,9}..2025-01-12/
  pipeline_mode=batch_onchain_rpc/asset_group=defi/venue={ORCA,RAYDIUM}/chain=SOLANA/instrument_type=pool/
  data_type=dex_pools/<pool_address>.parquet
```

**Every single sample** shows the identical pattern:

- The GCS partition key (`day=`) says January 2025.
- The row's own `timestamp` column (unix epoch) resolves to **2026-05-04 or 2026-05-05** — over a year AFTER the day=
  partition claims.
- `available_at` is **uniformly `2026-06-11T09:48:03`** across every sampled day= partition (2025-01-08 through
  2025-01-12) — a single write-time stamp smeared across 5 different logical dates.
- Where a file has 2 rows, they are byte-identical duplicates of each other.
- Nothing in the schema (`source=onchain_rpc`, no `note`/`evidence`/forward-fill flag) distinguishes this from genuine
  historical data — it is **silently indistinguishable** without checking `timestamp` against `day=` by hand.

This is the EXACT signature `solana_defi_fake_history_snapshot_2026_06_17.md` already diagnosed and marked **RESOLVED**:
Orca/Raydium/Kamino REST collectors have no historical endpoint, so a historical backfill loop wrote ONE live snapshot
into every requested historical `date=` partition. That fix (`solana_defi_handler.py:: _filter_rows_to_target_day`,
commit `aa3b9f18`) + its cleanup **only targeted the OLD flat prefix** (`dex_pools/<protocol>/SOLANA/date=*/`, 6000
objects deleted) — not the hive-shaped `raw_tick_data/by_date/...` structure. A SEPARATE remediation (Gate 7,
`solana_defi_legacy_migration_2026_05_27.md`) found 2823 objects in this same hive shape but in a bucket WITHOUT `-prd-`
(`market-data-tick-defi-central-element-323112`), fully migrated + deleted 2026-05-28. **Neither remediation's scope
includes the `-prd-` bucket's hive-shaped `dex_pools` objects** — this is a population no prior cleanup pass ever
re-scanned.

Corroborating evidence: this shape (`instrument_type=pool` lowercase, `data_type=dex_pools`) is confirmed via git blame
to be **pre-2026-06-05** code — commit `fbff8cf0` renamed Orca/Raydium/Kamino's data_type to `dex_pool_state` and their
`instrument_type` to Solana-specific types on that date. Everything in this shape predates that rename, i.e. predates
the current canonical vocabulary entirely.

## Scope — CONFIRMED FINAL 2026-07-23 (independent of the orphan-sweep; does not need to wait for ACCEPTANCE)

Rather than wait on the general orphan-sweep's full-corpus walk, ran a TARGETED, bounded existence-check walk
(read-only, `list_blobs(prefix=..., max_results=1)` per day×venue, 24-way concurrent) across the exact date range the
ORIGINAL fake-history bug's backfill loop covered per `solana_defi_fake_history_snapshot_2026_06_17.md:68`
(`--start 2023-01-01 --end 2026-04-15`) — 1,201 days × {ORCA, RAYDIUM} = 2,402 probes, ~2 minutes.

- **Exactly 34 day/venue combinations have this shape — 17 days × 2 venues, nothing more, nothing less.**
- Venues: `ORCA`, `RAYDIUM` only (confirmed — no hits for any other venue at any point in this session).
- Days: `2025-01-01` through `2025-01-17` inclusive, **every single day in that window, no gaps** — matches exactly what
  the orphan-sweep's partial walk had already found, confirming that partial sample WAS already the complete population
  (the sweep simply hadn't reached ACCEPTANCE yet to prove it independently).
- This makes todo 2 below DONE — no need to wait for the sweep or re-run
  `scope_defi_dex_pools_fake_history.py --source final`; the day/venue boundary is now proven, not merely
  observed-so-far. Row count (241,281 as of the 55-60 shard samples) is likewise final since the day/venue set it's
  derived from cannot grow.

## Why this blocks the backfill

`backfill_orphan_class_e.py --apply` would `record_captured` every orphan-E row in the sweep's report, INCLUDING this
population, stamping the manifest with **fabricated day=2025-01-XX coverage that is actually a copy of 2026-05-04/05
live state**. That is fabrication-by-construction — the exact class of harm the sports 2020-06-06 data floor rule exists
to prevent. **Do not run defi's backfill until this population is either excluded from the report or the report itself
is regenerated after a fix.**

## Todos

- [x] 1. [OPERATOR] P0. **Rule on disposition — DECIDED 2026-07-23, option (b)**. Operator ruling (verbatim): "OK YEAH
      WE need to relabel to reality." This is option (b) from the choices below: migrate-forward, re-stamp
      `available_at`/relabel each affected object as a `live`-mode snapshot under its TRUE date (2026-05-04/05, per the
      row's own `timestamp` column) instead of a fabricated historical `day=2025-01-XX`. NOT a wipe, NOT a
      leave-in-place exclusion. Implementation is a COPY-forward migration (GCS objects are immutable-by-path; per the
      delete-safety protocol, the OLD mislabeled object is left in place, unregistered, until a human confirms deletion
      — never delete-on-relabel): for each affected object, write a NEW object at the canonical path with
      `day=<true_date>` and `pipeline_mode=live_onchain_rpc` (or whatever the correct live-mode partition token is; the
      object's own row-level `timestamp` is the source of truth for `<true_date>`, NOT `available_at`, which is itself
      the uniform write-time artifact of the original bug), then `record_captured` the NEW path only. The OLD
      `day=2025-01-XX` path is left un-recorded (never `record_captured`) and flagged for a later human delete decision
      once the new copies are verified. See todo 3 for the concrete implementation. <br>Original options considered: (a)
      WIPE per the 2020-06-floor-style precedent — rejected, since Orca/Raydium pool STATE (unlike a genuinely-absent
      historical price series) has standalone present-tense value even mislabeled; (c) leave-in-place-and-exclude-only —
      rejected as a permanent non-fix, since it never produces the TRUE coverage the data actually represents.
- [x] 2. [DATA] P1. ~~**Get the TRUE final scope** once defi's orphan-sweep reaches ACCEPTANCE~~ — **DONE 2026-07-23,
      superseded by a faster independent method**: rather than wait on the sweep, ran a targeted bounded walk across the
      exact date range the original bug's backfill loop covered (2023-01-01..2026-04-15) — proved the population is
      EXACTLY 17 days × {ORCA, RAYDIUM}, 2025-01-01..17, no gaps, nothing beyond this window. See "Scope" section above.
- [ ] 3. [CODE] P1. **Build the relabel-forward migration per the todo-1 ruling** — a new script (sibling of
      `migrate_legacy_solana_defi_to_canonical.py`), scoped to `venue in (ORCA, RAYDIUM)`, `data_type=dex_pools`, the
      affected `day=2025-01-*` range: for each affected object, (1) read the row(s), derive `<true_date>` from the row's
      own `timestamp` column (NOT `available_at`), (2) compute the new canonical dest path with `day=<true_date>` and a
      `live_`-prefixed `pipeline_mode` (mirrors `_build_dest_path()`'s existing pure-computed-path pattern in
      `migration_orphan_sweep.py`/`backfill_orphan_class_e.py` — reuse it, don't reinvent), (3) **re-stamp the
      `available_at` COLUMN to match `<true_date>` before upload** (the row's OWN `timestamp` value, run through the
      same `stamp_available_at_onchain_tick` helper the live writer uses — NOT left as the old uniform
      `2026-06-11T09:48:03` bug artifact; path and row content must agree, or the relabel just moves the fabrication one
      level down), upload the new object, (4) `record_captured` the NEW path only, (5) leave the OLD `day=2025-01-XX`
      object un-recorded and log it to a "pending-human-delete" manifest for a later, separately-gated cleanup pass
      (never auto-delete). Must also independently exclude this population from `backfill_orphan_class_e.py`'s ordinary
      `--apply` path in the interim (route matching cells to `escalated`/`BLOCKED-OPERATOR-DECISION`) so a normal
      backfill run can't `record_captured` the OLD mislabeled path before the relabel migration runs.
- [x] 4. [REVIEW] P2. ~~Check whether the SAME bug shape exists for Kamino~~ — **PARTIALLY DONE 2026-07-23**:
      `venue=KAMINO/chain=SOLANA/instrument_type=pool/data_type=dex_pools/` has **zero objects** in the `-prd-` bucket
      across 6 sampled days (both inside and outside the affected window) — moot for the AMM-pool shape this issue
      covers (Kamino is primarily a lending protocol, not an AMM, so it likely never wrote this shape at all). **Still
      unconfirmed**: the original 2026-06-17 doc ALSO named a `lending_indices/{kamino,solend}` tree as affected — a
      quick exploratory check of `data_type=lending_indices` / `lending_rates` under `instrument_type=pool` came back
      empty too, but that's **inconclusive, not a clean bill** — I don't have confirmed knowledge of the real
      path/instrument_type shape lending data actually uses in this bucket (my guess may simply be wrong, not "no such
      data exists"). A real check needs someone to find lending's actual writer code + real path shape first, then
      re-probe.
- [ ] 5. [REVIEW] P3. **Audit whether other already-completed backfills this session (cefi, prediction) could have the
      same class of issue** — spot-check a sample of already-`record_captured`-ed cefi/prediction cells for a
      day=/timestamp mismatch before treating those backfills as fully clean. Not yet done; both were sampled for
      canonical-SHAPE correctness (confirmed clean) but NOT specifically for this timestamp-provenance check.

## Lesson (do not re-learn)

**A previously-RESOLVED data-fabrication bug's fix scope must be checked against ALL buckets/path-shapes the bug could
have written to, not just the one the fix's own cleanup happened to scan.** The 2026-06-17 fix covered the old flat
prefix; a SEPARATE 2026-05-27 migration covered a non-`-prd-` bucket's hive-shaped copy. Neither effort's "done"
checklist included "verify the `-prd-` bucket's hive-shaped copy too" — the exact population that turned out to still
have live fake data. When closing out a fabrication-class bug, enumerate every bucket × path-shape combination the buggy
writer could have touched, not just the one instance found first.

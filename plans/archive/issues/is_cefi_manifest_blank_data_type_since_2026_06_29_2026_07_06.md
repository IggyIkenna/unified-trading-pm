---
doc_type: issue
title:
  IS cefi availability index — captured rows land with data_type='' (blank) instead of 'instruments' since 2026-06-29
summary:
  Every cefi venue's IS captured shards since 2026-06-29 write `data_type=""` (blank) into the availability index
  instead of the canonical `data_type="instruments"`. Fleet-wide across all 26 cefi venues (EXTENDED-STARKNET,
  HYPERLIQUID, BINANCE-SPOT/FUTURES/DELIVERY, BYBIT/BYBIT-SPOT, KRAKEN-SPOT/FUTURES, OKX-SPOT/SWAP/FUTURES,
  COINBASE-SPOT/FUTURES, BITFINEX-SPOT/FUTURES, BITGET-SPOT/FUTURES, DERIBIT, DERIBIT-COMBO, KALSHI-PERP,
  POLYMARKET-PERP, UPBIT, ASTER, LIGHTER-ZKSYNC, PACIFICA-SOLANA). 2026-06-27→28 is the transition window (BOTH the old
  data_type='instruments' rows AND new blank rows coexist); 2026-06-29→2026-07-06 (today) only the blank-data_type rows
  are emitted. Any downstream consumer that filters by `capture_status=='captured' AND data_type=='instruments'` (the
  canonical honest-coverage query) will silently miss 10 days of cefi captures per venue (~260 shards), reading them as
  absent.
status: resolved
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [instruments, manifest, data-correctness, cefi, data_type, honest-coverage, regression]
related:
  [
    plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md,
    plans/archive/2026_07/is_catalogue_completion_2d_2026_07_06.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
source: [plans/archive/2026_07/is_catalogue_completion_2d_2026_07_06.md, is_catalogue_completion_2d-003]
priority: P1
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  instruments-service@46ba62b (writer fix) + @40bdfe1d (cefi backfill) + @523d427 (defi/tradfi backfill) + @9263c80 (QG
  regression guard)
---

> **Status-flip note (2026-07-10)**: all 4 todos confirmed `[x]` with cited evidence (writer fix + dry-run/apply
> backfills + regression guard, all runtime-verified); flipped `status: open` → `resolved`.

## What I found

Reading the cefi availability index (`instruments-store-cefi-prd/_index/availability_index.parquet`, 2026-07-06)
filtered to 2026-06-27+ dates shows every cefi venue has the same pattern:

| Venue                                                                                                                                                                                                   | Rows 2026-06-27+ with data_type='instruments' | Rows 2026-06-27+ with data_type='' (blank) |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------: | -----------------------------------------: |
| ASTER, BINANCE-_, BITFINEX-_, BITGET-_, BYBIT, BYBIT-SPOT, COINBASE-_, DERIBIT, DERIBIT-COMBO, EXTENDED-STARKNET, HYPERLIQUID, KRAKEN-\*, LIGHTER-ZKSYNC, OKX-SPOT/SWAP/FUTURES, PACIFICA-SOLANA, UPBIT |                    2 (2026-06-27, 2026-06-28) |         10 (2026-06-27 through 2026-07-06) |
| KALSHI-PERP                                                                                                                                                                                             |                                             0 |                                         12 |
| POLYMARKET-PERP                                                                                                                                                                                         |                                             0 |                                         10 |

Concrete EXTENDED-STARKNET dump for 2026-06-27:

```
row 86555: data_type='instruments' instrument_count=103 written_at=2026-06-28T13:41 available_at set
row 86554: data_type=''           instrument_count=101 written_at=2026-06-29T13:40 available_at NOT set
```

For 2026-06-29..2026-07-06 (10 days including today), only the blank-data_type row exists per (date, venue), and the
`available_at` column is missing.

Both rows carry `capture_status='captured'`, `pipeline_mode='batch_instruments_service'`,
`source='instruments_service'`, `schema_version=9`, `instrument_type='PERPETUAL'`. The only differences are:

1. `data_type`: 'instruments' vs ''
2. `available_at`: populated vs missing
3. `instrument_count`: 103 vs 101 (adapter's `/info/markets` returned different active-market lists at different times —
   expected variance, NOT part of the regression)

## Why it matters

**Data-correctness break for downstream consumers.** The canonical availability-manifest query for "IS instruments
coverage" is `capture_status == 'captured' AND data_type == 'instruments'` (matches the
`REFERENCE_DATA_TYPE = "instruments"` constant in `scripts/migrate_instruments_store_v9.py:126` — the migration-time
SSOT for the reference-data-type stamp). With `data_type=''`, 10 recent days of cefi captures per venue (26 venues × 10
days = 260 shards) are silently missing from the "instruments" filter. Any dashboard, coverage-check, or downstream
reader using the canonical filter reads them as absent, not captured.

Explicitly does NOT affect the current `is_catalogue_completion_2d_2026_07_06.md` line-105 gate flip because that gate
uses `capture_status == 'captured'` alone (per B0's classification in the plan progress log), which still counts the
blank-data_type rows as captured. But any consumer using the stricter canonical filter will miscount.

## Root-cause hypothesis (partial — needs a fix-worker to confirm)

Two candidate root causes surfaced during investigation (2026-07-06):

1. **Writer explicitly emits `data_type=""` (writers.py:239).** The current code path
   `record_captured(row_key=_rk, df=_stamped_venue_df, asset_group=_cat, ..., data_type="", venue=manifest_venue, chain=manifest_chain, pipeline_mode=BATCH_INSTRUMENTS_SERVICE, ...)`
   has been in place since the 2026-06-11 orchestrator split (`cb51c98a`). The `migrate_instruments_store_v9.py`
   migration is what promotes blank → 'instruments' (see `REFERENCE_DATA_TYPE` constant + CF-7 comment at line 343:
   "canonical data_type (blank → reference 'instruments'; typed values preserved, incl. pred)"). The pre-2026-06-29 rows
   carry data_type='instruments' because the migration script ran periodically to normalize. Post-2026-06-29 rows are
   un-migrated blanks.

2. **The 2026-06-29 UAC-producer consolidation (`4da6fe8`) may have changed the emission surface** — the commit
   "consolidate IS cefi/tradfi/prediction venue producers to UAC (named Tardis grain-adapter; delete \_CEFI/\_TRADFI
   mirrors)" landed 2026-06-29T08:46 UTC. The first blank-data_type row landed 2026-06-29T13:40 (5 hours later — the
   daily t1-recon fire). Correlated in time.

**Right fix (WRITER as SSOT — codex/02-data/availability-manifest-and-data-status.md):** the writer should stamp
`data_type="instruments"` directly at `record_captured` call time (writers.py:239), not rely on a post-hoc migration.
That makes the atom canonical from the first emission and eliminates the migration-lag correctness window.
`migrate_instruments_store_v9.py` remains a one-time backfill for the legacy blank rows.

## Recommended decision

Fix the writer to stamp `data_type="instruments"` at emission time (the same value the migration promotes to). Two
follow-ons:

- (a) code fix at writers.py:239 (change `data_type=""` → `data_type="instruments"` for the cefi/tradfi/defi non-sports
  emit path); add a regression test that asserts a fresh cefi captured shard lands with data_type='instruments'.
- (b) one-off patch script to promote the 260 blank cefi shards written 2026-06-29..today back to
  data_type='instruments' via the same code path as migrate_instruments_store_v9.py.

## Actionable todos (for the fix-worker)

- [x] ✅ [CODE] P1. writers.py:239 — change the record_captured `data_type=""` argument to `data_type="instruments"` for
      the cefi/tradfi/defi non-sports path (matches `REFERENCE_DATA_TYPE` in migrate_instruments_store_v9.py). Add a
      unit test that asserts a fresh cefi captured row lands with `data_type='instruments'` (repo: instruments-service).
      — instruments-service@46ba62b + regression tests at tests/unit/test_orchestrator_process.py:233 (cefi) & :275
      (defi)
- [x] ✅ [DATA] P1. One-off patch script shipped instruments-service@40bdfe1d as
      `scripts/backfill_cefi_blank_instruments_data_type_2026_07_06.py`. Contract: filter
      `date >= 2026-06-27 AND capture_status == 'captured' AND (data_type is null OR data_type == '') AND venue != ''`;
      rewrite `data_type = 'instruments'` (matches `REFERENCE_DATA_TYPE` in `migrate_instruments_store_v9.py:126`);
      dry-run by default; `--apply --confirm` mutates; captured-row-count safety gate; post-run 0-blank verify;
      idempotent. **Runtime verification 2026-07-06 dry-run against instruments-store-cefi-prd: manifest ALREADY CLEAN —
      297/297 cefi captured venue-grain rows on 2026-06-27+ carry `data_type='instruments'` (writer fix `@46ba62b` +
      periodic `migrate_instruments_store_v9` run already remediated the historical blanks)**. Script serves as a
      defensive idempotent safety-net for future recurrence. Gate met: 0 blank cefi captured rows post-verify.
- [x] ✅ [DATA] P2. Verify defi + tradfi are not affected. If the same regression exists there, extend the (a) fix to
      include their data_type stamp + (b) run the patch on their buckets too (`instruments-store-defi-prd`,
      `instruments-store-tradfi-prd`) (repo: instruments-service). — **DONE 2026-07-06 (Opus, slot-5)**. Regression
      confirmed on both stores; mirror-script `scripts/backfill_defi_tradfi_blank_instruments_data_type_2026_07_06.py`
      shipped `instruments-service@523d427` with same contract as the cefi oneoff (dry-run default; `--apply --confirm`
      mutates; captured-row-count safety gate; idempotent). Runtime results (2026-07-06 `--apply --confirm`): **defi 536
      blank captured rows → `data_type='instruments'` (28 venues, 10 dates)**; **tradfi 46 blank captured rows →
      `data_type='instruments'` (7 venues, 10 dates)**. Post-run verify: 0 blank captured rows on 2026-06-27+ for both
      buckets. Safety gate OK: captured row totals preserved (defi 170887; tradfi 11810). The writer fix `@46ba62b` +
      periodic `migrate_instruments_store_v9` run drove the ongoing writes clean; this oneoff cleared the historical
      tail.
- [x] ✅ [DATA] P2. Add a `quality-gates.sh` check (or extend an existing one) that asserts the writer's
      `record_captured` calls for non-sports paths always stamp `data_type='instruments'` — grep-level check on
      `writers.py` that catches a future regression at CI time (repo: instruments-service). —
      instruments-service@9263c80 + scripts/qg/no_blank_instruments_data_type.sh in PM; QG STEP 5.86 added; grep-P
      lookbehind catches data_type="" keyword arg, excludes manifest_data_type= variable assignments; QG green.

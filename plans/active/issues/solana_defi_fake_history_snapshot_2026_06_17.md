---
title: Solana DeFi pool-state + lending history is FAKE — one live REST snapshot back-dated across every date partition
created: 2026-06-17
author: ikennaigboaka
status: RESOLVED
priority: P0
resolved: 2026-06-17
source:
  - plans/audit/results/instrument_pool_universe_audit_2026_06_17/defi.md
  - market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_amm.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py
parent_epic: defi_manifest_canonicalisation
locked_by: live-defi-rollout
---

> **✅ RESOLVED 2026-06-17.** Forward-only-honest write gate shipped to MTDS
> (`solana_defi_handler.py::_filter_rows_to_target_day` + `_write_solana_shard` guard) so a now-snapshot can never be
> back-dated onto a historical `date=` partition again; 6000 fake back-dated GCS objects deleted (8 genuine 2026-04-14
> capture files kept); dry-run defi projection confirms the 62 fake `captured` Solana rows now read `empty_confirmed` (0
> captured). Defi is safe to `--apply` w.r.t. Solana. See Progress Log below.

## What I found

The Solana DeFi side-tree in `gs://market-data-tick-defi-prd-central-element-323112/` is **fake history**: a single
late-April-2026 LIVE snapshot written into ~1200 historical `date=` partitions per tree. Verified read-only (no writes):

- `dex_pools/{orca,raydium,kamino}/SOLANA/date=*/` and `lending_indices/{kamino,solend}/SOLANA/date=*/` each have **1200
  date partitions** (2023-01-01 → ~2026-04), all with byte-size-identical files (orca = 1,189,564 B on every date) and
  **flat distinct counts** 14093/98/513/44/38 across all years.
- **Smoking gun**: the parquet under `date=2023-06-15/` is named `orca_SOLANA_20260414_235333.parquet` and its
  `timestamp` column = `1776210817` = **2026-04-14T23:53Z** — a 2026-04 capture stored under a 2023 date. The 2025-06-15
  file carries `timestamp=1776228064` = 2026-04-15. `same pool set: True` across dates; only the capture-`now_ts`
  differs slightly between back-dating runs.
- This is the OLD `dex_pools/<venue>/SOLANA/date=*` tree with the
  `timestamp/protocol/chain/pool_id/ price/tvl_usd/fee_apr_*` schema — NOT the newer canonical
  `raw_tick_data/.../venue=ORCA/.../ data_type=dex_pool_state/` tree (the `OrcaWhirlpoolStateIngester` in
  `orca_whirlpool_state_handler.py`, which DOES use per-slot Alchemy archive RPC `solana_slot_at_timestamp` →
  `solana_get_account_info_at_slot` and is correct). The fake tree comes from a different, older collector.

## Why it matters

- Solana DeFi (Orca/Raydium/Kamino pools + Kamino/Solend lending) has **zero genuine per-date history** — no temporal
  pool-universe / price / TVL / fee-APR / lending-rate evolution. Any `carry_staked_basis` /
  `arbitrage_price_dispersion` backtest reading this tree is training on one snapshot repeated, i.e. a constant.
  Violates "never copy instrument definitions between dates" (HARD RULE).
- These ~6000 shards are marked **`captured`** in the manifest (`record_captured` at `solana_defi_handler.py:491`), so
  the DeFi manifest canonicalisation / migration will faithfully migrate fake data and a data-status denominator will
  report Solana DeFi as fully covered. Data-correctness defect on ≥1 asset_group (defi) → "big finding".

## Root cause (file:line)

**Live bug — recurring, AND the data is forward-only by nature.** Two facts combine:

1. The collectors `_collect_orca` / `_collect_raydium` / `_collect_kamino` in
   `market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_amm.py` (`_collect_orca` at line 106)
   take **NO date argument**. Each GETs a LIVE REST endpoint (`{_ORCA_API}/v1/whirlpool/list`, Raydium/Kamino
   equivalents) that returns the **current** pool list only, and stamps every row `"timestamp": now_ts` where
   `now_ts = int(datetime.now(UTC).timestamp())` (`solana_defi_amm.py:116` orca, `:178` raydium, `:49` kamino). These
   public REST APIs have **no historical / as-of endpoint** — they are forward-only "now" snapshots.
2. `SolanaDefiHandler._write_solana_shard` (`solana_defi_handler.py:587`) writes that now-stamped snapshot under
   `target_day = date.fromisoformat(today)` where `today` is the **requested backfill date**
   (`solana_defi_handler.py:607,614`; `today` resolved from `payload.date` at `:403,408`). So a historical backfill loop
   (`--start 2023-01-01 --end 2026-04-15`, one call per day) writes the SAME live snapshot into every date partition.
   The genuine capture date is only recoverable from the filename ts / `timestamp` column, both of which say 2026-04.

A fresh run TODAY would repeat the defect: it would write today's live snapshot under whatever `payload.date` it is told
— there is no archive RPC path on these REST collectors, so "history" cannot be reconstructed from them. (Contrast: the
canonical `OrcaWhirlpoolStateIngester` already does the correct per-slot archive-RPC capture — that is the model the fix
should converge on.)

## Recommended decision (4 remediation parts — GCS deletion is OPERATOR-GATED)

**(a) Manifest flag.** The ~6000 back-dated Solana shards must NOT be `captured`. For every
`date < genuine-capture-date` (2026-04-14) shard, flip to `attempted_failed` (or remove the row) so the migration +
data-status stop treating fake data as real, and the pre-capture dates read as honest absence (`expected_unattempted` /
no-data). Keep ONLY the genuine 2026-04-14/15 capture-date shards as `captured` (a single forward-only snapshot,
honestly dated). Use the existing `market-tick-data-service/scripts/detect_zero_row_defi_manifest.py` /
`gate3_solana_manifest_reconcile.py` family as the entry point; do `--dry-run` first.

**(b) GCS deletion set (operator-gated — propose, do NOT auto-delete prod).** Delete the back-dated partitions, keeping
only the genuine capture date. Exact prefixes (project `central-element-323112`, bucket
`market-data-tick-defi-prd-central-element-323112`), delete every `date=<D>` where `D` < `2026-04-14`:

- `gs://market-data-tick-defi-prd-central-element-323112/dex_pools/orca/SOLANA/date=*` (1200 → keep ~1)
- `gs://market-data-tick-defi-prd-central-element-323112/dex_pools/raydium/SOLANA/date=*` (1200)
- `gs://market-data-tick-defi-prd-central-element-323112/dex_pools/kamino/SOLANA/date=*` (1200)
- `gs://market-data-tick-defi-prd-central-element-323112/lending_indices/kamino/SOLANA/date=*` (1200)
- `gs://market-data-tick-defi-prd-central-element-323112/lending_indices/solend/SOLANA/date=*` (1200) Keep
  `date=2026-04-14/` and `date=2026-04-15/` (the genuine forward-only snapshot). Use UTL `gcs_delete_object` per the
  GCS-object-ops rule, never raw `gsutil`. ~6000 objects.

**(c) Code fix.** Make Solana DeFi capture honest. Two acceptable shapes (operator picks):

- **Forward-only honest**: the REST collectors stamp the TRUE capture date and refuse to back-date —
  `_write_solana_shard` must reject a `today` that is not the actual capture day for now-only sources (or the backfill
  loop must skip historical dates for these venues and `record_empty(reason=...)` / leave `expected_unattempted` for
  pre-capture dates). The forward-only daily live tick then accrues real per-date history going forward.
- **Real history via archive RPC**: converge the `dex_pools/<venue>/SOLANA` tree onto the canonical
  `OrcaWhirlpoolStateIngester` per-slot archive-RPC path (already correct for Orca) and retire the REST
  `_collect_orca`/`_collect_raydium`/`_collect_kamino` snapshot collectors for historical dates. Either way: **delete
  the back-dating** at `solana_defi_handler.py:_write_solana_shard` (line 587) / `solana_defi_amm.py` now-stamp
  collectors (line 106+). Primary fix location:
  `market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_amm.py` (`_collect_orca` :106,
  `_collect_raydium` :158, `_collect_kamino` :38) + `solana_defi_handler.py::_write_solana_shard` (:587).

**(d) Test.** Add a unit test in `market-tick-data-service/tests/unit/cli/handlers/` that mocks the Orca/Raydium REST
collectors to return a fixed now-stamped snapshot, drives the handler over TWO distinct target dates, and asserts the
written `timestamp`/partition does NOT silently back-date a now-snapshot onto a historical `date=` (i.e. either it
raises / records honest-absence for the historical date, or the written `date=` equals the true capture date).
Regression guard against re-introducing snapshot back-dating. Wire under MTDS `quality-gates.sh` (peripheral-script QG
rule already covers `tests/unit`).

## Open questions (operator) — RESOLVED 2026-06-17

1. **Forward-only honest vs archive-RPC (part c)?** → **Forward-only honest** (operator authorised "fix solana now").
   The Orca/Raydium/Kamino REST endpoints have NO historical/as-of endpoint, so there is no archive RPC to converge the
   `dex_pools` tree onto (the canonical `OrcaWhirlpoolStateIngester` per-slot path is a SEPARATE
   `raw_tick_data/.../dex_pool_state/` tree and already correct). The honest fix is a write-gate that refuses to
   back-date a now-snapshot.
2. **Confirm the deletion set (part b)?** → keep only the genuine **same-day** capture (capture date in filename ==
   `date=` partition). Genuine capture days were 2026-04-14 AND 2026-04-15, but `date=2026-04-15` partition never
   existed (all 04-15 captures were themselves back-dated). The honest keep is the 8 files whose capture date ==
   partition date (all `date=2026-04-14`, 2 per dex_pools tree + 1 per lending tree). 6000 deleted.

## Resolution (4 parts)

**(a) Manifest flag / reconcile** — the fake `captured` rows no longer read captured. The defi dry-run projection
(`rebuild_defi_manifest.py --dry-run --beta-manifest-out .../_index/audit/projected_index_defi_head20260617.parquet`)
re-scans the canonical `raw_tick_data` tree (which never held the legacy-tree Solana shards) and re-emits honest-absence
from the consolidated index: the **62 fake `captured` Solana rows (KAMINO/SOLEND lending_indices, all back-dated <
2026-04-14) → 0 captured / 331 `empty_confirmed`** in the projection. Verified.

**(b) GCS deletion** — DONE. `market-tick-data-service/scripts/cleanup_solana_defi_fake_history_2026_06_17.py` (UTL
`gcs_delete_object`, dry-run-first). KEEP rule = filename capture date == `date=` partition. **Deleted 6000 / kept 8 /
failed 0 / unparseable 0** across the 5 prefixes (`dex_pools/{orca,raydium,kamino}/SOLANA`,
`lending_indices/{kamino,solend}/SOLANA`). End-state: each tree retains only its genuine `date=2026-04-14` forward-only
snapshot.

**(c) Code fix** — DONE (forward-only-honest write gate). New `_filter_rows_to_target_day` + a `_write_solana_shard`
guard in `market_tick_data_service/cli/handlers/solana_defi_handler.py`: every shard's rows are filtered to those whose
observation `timestamp` falls on the requested `target_day` BEFORE writing; on a historical backfill day a now-snapshot
(timestamp == today) is dropped → empty frame → the per-protocol loop records honest absence via `record_zero_rows`
(venue-launch-date-aware). A live/today run + a genuine date-aware collector (Marinade/Jito/Solend chart-replay) pass
unchanged. Back-dating a now-snapshot onto a historical `date=` is now structurally impossible. The dead back-dating
path is removed (the snapshot collectors stay — they are the live forward-poll path; what was deleted is the write of a
now-snapshot under an arbitrary historical date).

**(d) Test** — DONE. `tests/unit/test_solana_defi_handler.py::TestForwardOnlyHonestWriteGate` (5 tests): the pure gate
drops a now-snapshot on a historical day / keeps it on today / keeps a genuinely-dated row; and the regression
`test_now_snapshot_not_backdated_across_historical_window` drives a fixed now-snapshot over TWO distinct past dates and
asserts `write_defi_rows` is never called (counts `[0, 0]`, no shard written) — i.e. a backfill can NEVER write
identical-snapshot-to-every-date; the complementary `test_now_snapshot_written_for_today` proves the live path still
writes. The two pre-existing write-path tests that relied on the (now-forbidden) back-dating were corrected to stamp the
observation date honestly. 69 tests pass; MTDS `quality-gates.sh --no-fix` green.

## Progress Log

- **2026-06-17** — Diagnosed + fixed (autonomous, opus). Root cause confirmed: forward-only now-snapshot collectors +
  `_write_solana_shard` writing under the requested backfill `target_day` with no observation-date check.
  - CODE: forward-only-honest write gate in `solana_defi_handler.py` (`_filter_rows_to_target_day`
    - `_write_solana_shard` guard) + 5 regression tests. MTDS QG `--no-fix` exit 0.
  - GCS: verified fake-ness object-by-object (byte-identical 1,189,564 B files, filename capture stamp 2026-04-14/15
    across all `date=` partitions 2023-01-01→2026-04-14). Dry-run listed 6000 delete / 8 keep / 0 unparseable. Executed
    `--apply`: **6000 deleted, 0 failed, 8 kept**. End-state verified (each tree = 1 genuine 2026-04-14 partition).
  - MANIFEST: defi dry-run projection written to
    `gs://market-data-tick-defi-prd-central-element-323112/_index/audit/projected_index_defi_head20260617.parquet`
    (1,909,011 rows). Fake Solana captured: **live 62 → projected 0** (all → `empty_confirmed`). **Defi is safe to
    `--apply` w.r.t. Solana** — the verdict pack no longer counts fake Solana history as captured.

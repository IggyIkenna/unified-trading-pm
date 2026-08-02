---
doc_type: issue
title: >-
  LIGHTER-ZKSYNC derivative_ticker batch writes 100% fail schema validation — Tardis's numeric market_id leaks into the
  `symbol` column/filename instead of the original ticker
summary: >-
  Discovered while attempting a real production backfill of (LIGHTER-ZKSYNC, derivative_ticker) for the
  2026-04-17..2026-07-29 window (the funding-rate data type this venue's own smoke-test doc claimed a working Tardis
  fetch for, but which had never actually been backfilled into the corpus — see the companion doc's todo 1 note). The
  backfill VM (`mtds-backfill-cefi-lighter-derivative-ticker-v2-20260729`) DID successfully stream real data from Tardis
  (`Tardis streaming success: N rows...` — confirms the venue+data_type+date range genuinely has real, fetchable
  funding-rate data) but 100% of writes then failed: `schema contract violated for
  cefi/LIGHTER-ZKSYNC/perpetual/derivative_ticker: 2 violation(s); first=column 'symbol' has dtype 'int64', expected
  'string'`. The resulting (would-be) parquet filenames were also malformed:
  `raw_tick_data/.../instrument_type=perpetual/data_type=derivative_ticker/LIGHTER-ZKSYNC:PERPETUAL:43.parquet` — using
  the raw Tardis numeric market_id (`43`) as the instrument identifier instead of the canonical ticker-based
  instrument_id (`LIGHTER-ZKSYNC:PERPETUAL:BTC-USDC@LIN`).
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, lighter-zksync, derivative-ticker, funding-rate, tardis, schema-contract, data-pipeline-correctness]
related:
  [
    /plans/archive/issues/lighter_zksync_trades_generic_tardis_path_bypasses_no_batch_source_2026_07_29.md,
    /plans/active/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
  ]
created: 2026-07-29
parent_epic: cefi_master
priority: P1
estimate_class: refactor
assigned_role: data_engineering
source: >-
  Surfaced while executing a real production backfill for (LIGHTER-ZKSYNC, derivative_ticker) as a follow-up to the
  funding-rate canonical-route audit (2026-07-29). VM launched, ran, and was deleted (self-completed, zero real
  captures) within ~10 minutes; root-caused by reading its GCS run.log directly.
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# LIGHTER-ZKSYNC derivative_ticker: Tardis numeric market_id leaks into the written `symbol` schema

> **🗄️ ARCHIVED 2026-07-30** — status=resolved, all 5 todos done: (1) symbol-remap fix
> (`market-tick-data-service@7a708284`/`@039cddb6`/`@6bf568ee`), (2) full production backfill (179 instruments × 105
> dates, ~1.10B rows, 0 schema violations), (3) the 4th-bug manifest-recording fix
> (`market-tick-data-service@064f872a`), (4) manifest reconciliation for the pre-fix backfill
> (`market-tick-data-service@67dd6422`, 15,639/15,639 cells recorded as captured, 0 skipped), (5) the
> Tardis-concurrency-guard exemption-list fix (`deployment-service@45e1cd1`). See each todo below for full evidence.

## What I found

`market_tick_data_service/adapters/umi_tick_provider.py::_route_lighter` (lines 343-369) handles LIGHTER-ZKSYNC's
`derivative_ticker` batch leg via Tardis. Because Tardis's `lighter` exchange indexes symbols by **numeric market_id**
(e.g. `"43"`), not by the venue's own bare ticker (e.g. `"BTC"`), the routing function translates before calling Tardis:

```python
# line 359
tardis_instrument_ids = await _resolve_lighter_tardis_instrument_ids(instrument_ids, max_instruments)
result = await tardis.download_batch(
    date=date,
    data_types=tardis_data_types,
    instrument_ids=tardis_instrument_ids,   # <-- now numeric strings, e.g. ["43", "104", "15", ...]
    exchange=exchange,
    writer=_w,
)
```

`_resolve_lighter_tardis_instrument_ids` (lines 282-317) does the ticker→market_id translation via `/orderBookDetails`
and returns **only** the numeric IDs — the original ticker is discarded at the call site, with no reverse map kept.

`TardisAdapter.download_batch` is venue-agnostic and treats whatever `instrument_ids` it receives as the canonical
symbol for both the written `symbol` column and the per-instrument parquet filename — correct for every OTHER
Tardis-CeFi venue (where `instrument_ids` IS already the real ticker), but wrong here: the numeric market_id string
flows straight through into the schema and filename, producing:

- `symbol` column with `dtype=int64` values like `43`, `104`, `15` instead of ticker strings — fails the cefi
  `derivative_ticker` schema contract (`'symbol'` must be `string`), so **every single write is rejected**:
  `schema contract violated for cefi/LIGHTER-ZKSYNC/perpetual/ derivative_ticker: 2 violation(s); first=column 'symbol' has dtype 'int64', expected 'string'`.
- Filenames like `LIGHTER-ZKSYNC:PERPETUAL:43.parquet` instead of the canonical
  `LIGHTER-ZKSYNC:PERPETUAL:BTC-USDC@LIN.parquet` — flagged by the pipeline's own Stage-0 observability check as
  "non-canonical instrument-id form... raw venue wire symbol / bare symbol or a double-wrapped catalogue-miss id"
  (confirms the pipeline itself already detects this shape as wrong, it just doesn't block on it).

**Live evidence (2026-07-29, VM `mtds-backfill-cefi-lighter-derivative-ticker-v2-20260729`,
`--start 2026-04-17 --end 2026-07-29`, 179 correctly-formatted bare-ticker `--instrument-ids`):** Tardis streaming
genuinely succeeded (`Tardis streaming success: 29899 rows, 1 batches...` and dozens of similar lines, confirming this
venue+data_type DOES have real, fetchable historical funding-rate data from 2026-04-17 onward) — but **100% of the
resulting writes failed** the schema contract, for every symbol, on every date attempted. The VM completed its date
range quickly (no real data ever got network-fetched for MOST dates before this failure mode was hit repeatedly) and
self-terminated (`--instance-termination-action=DELETE`) with **zero real rows captured**.

**Manifest impact — CORRECTED 2026-07-30, this claim was WRONG.** Originally assessed as benign (schema-validation
failures thought to leave the cell unwritten, neither false success nor false failure). A later, more complete manifest
query (2026-07-30, prompted by an operator question — "does manifest need purge") found this was incomplete: the VM DID
write 677 real `attempted_failed` rows for this exact combo,
`error_reason="schema contract violated for cefi/LIGHTER-ZKSYNC/perpetual/derivative_ticker"`, `written_at`
2026-07-29T16:02–22:36Z, keyed on the raw numeric Tardis market_id (not the real ticker) — these went through the
standalone handler's `_emit_per_symbol_manifest` exception branch (`record_failed`, which has always existed, unlike the
missing success-recording path this doc's own fix addresses). They were permanently dead (the manifest's
captured-outranks dedup rule can't retire a row whose key no real captured row shares) and have since been purged — see
the new P2 todo below for full evidence. The original `empty_confirmed` counts quoted above (18,616 + 50) were real but
not the whole picture.

## Why this matters

This is the reason `(LIGHTER-ZKSYNC, derivative_ticker)` shows **0 captured** rows in production despite the venue's own
smoke-test doc (`non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`) claiming a working Tardis fetch verified
via a one-off manual API probe (238,122 real rows, 2026-07-07). That manual probe likely used the ORIGINAL discovered
numeric-market_id values directly as ad-hoc verification (bypassing the normal `download_batch` schema-write path
entirely, e.g. inspecting the raw Tardis HTTP response), so it never hit this schema-contract failure — the bug is
specifically in the **production write path** (`_route_lighter` → `download_batch`), not in whether Tardis has the data
at all (confirmed it does).

## Fix shipped + verified live (2026-07-29/30) — 3 bugs, one feature path

Implemented approach 1 (ContextVar-scoped symbol-display override, safer than a wrapping writer given `writer=None` at
the LIGHTER call site — confirmed threading through `download_batch`'s internals was non-trivial: see bug 2 below):

1. **Numeric-symbol leak (this doc's original finding) — FIXED, `market-tick-data-service@7a708284`.** Added
   `symbol_display_map_var` (a module-level `ContextVar[dict[str, str] | None]` in `tardis_cefi_shards.py`, never a
   `TardisAdapter` instance attribute — the adapter is a pooled singleton shared by concurrent venues, so instance state
   would race). `_ensure_symbol_and_data_type_columns` now force-overwrites the `symbol` column when the resolved
   display value differs from the raw one (previously it silently no-op'd whenever a `symbol` column already existed,
   which was exactly the case here — Tardis's own `lighter` response already carries a `symbol` column, just the wrong
   (numeric) one). `download_batch` gained an optional `symbol_display_map` kwarg (default `None`, byte-identical for
   every other venue) that sets the ContextVar; `_route_lighter` builds the reverse (market_id → ticker) map alongside
   the existing forward translation. Same fix applied to the legacy (non-streaming) write path.
2. **ContextVar didn't propagate across the finalise executor thread — FIXED, `market-tick-data-service@039cddb6`.** The
   first version of fix 1 did NOT work on real infra: `_download_one_perp_symbol_streaming` offloads
   `_ensure_symbol_and_data_type_columns` to a `ThreadPoolExecutor` via `loop.run_in_executor(executor, func)` —
   `ContextVar`s do NOT auto-propagate into executor threads (each thread gets its own default `Context`), so
   `symbol_display_map_var.get()` returned `None` inside the thread even though `download_batch` had just set it in the
   calling coroutine. Confirmed via a real smoke-test VM showing identical `dtype int64` failures even with fix 1's
   tarball freshly deployed. Fixed via `contextvars.copy_context()` captured in the async caller, submitted as
   `ctx.run(...)` instead of calling the closure directly — the standard pattern for carrying `ContextVar` state across
   a `run_in_executor` boundary.
3. **Missing `ts_event` derivation for `derivative_ticker` — FIXED, `market-tick-data-service@6bf568ee`.** After fixes
   1+2 landed, a re-verification smoke-test VM surfaced a THIRD, separate gap:
   `schema contract violated: column 'ts_event' missing from dataframe`. `_WIRE_COLUMN_RENAMES` (`tardis_shared.py`)
   never had a `derivative_ticker` entry — this exact gap was already flagged in a 2026-07-28 code comment as "left as a
   separate, untriggered gap if a future caller starts writing derivative_ticker through this same
   finalise_rows_and_path route" — LIGHTER-ZKSYNC's backfill is that future caller. Added `"derivative_ticker": {}` (no
   renames needed; `funding_rate`/`open_interest`/`mark_price`/`index_price` already match the contract's wire names,
   only the generic `timestamp → ts_event` derivation was missing).

**Live verification (VM `mtds-smoke-lighter-dt-fix-v4-20260730`, 2 instruments × 3 days, all 3 fixes deployed):** zero
schema failures, zero `Stage-0 OBSERVE`-flagged write rejections — all 6 shards succeeded end-to-end
(`Tardis streaming success` → `StreamingParquetWriter: uploaded` → `StreamingShardFinalizer` →
`TardisAdapter (streaming): canonical shard`), ~987K real rows written to
`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=<D>/pipeline_mode=batch_tardis/ asset_group=cefi/venue=LIGHTER-ZKSYNC/instrument_type=perpetual/data_type=derivative_ticker/LIGHTER-ZKSYNC:PERPETUAL: {BTC,ETH}.parquet`
(confirmed via `gsutil ls`, real parquet objects present).

## NEW finding (4th bug, same feature path) — successful writes never reach the manifest as `captured`

The live verification above proves the DATA writes correctly, but a **separate, deeper gap** means it never shows up in
the honest-coverage manifest. Root cause, traced precisely:

- `_onchain_perp_batch_lighter.py:197` calls `fetch_tick_data_for_venue(..., writer=None)` — deliberately, per the
  module's own docstring, which claims "Tardis's own manifest rows are the source of truth for per-symbol capture
  status" once delegated to `download_batch`. **This claim is empirically wrong for the success case.**
- `download_batch`'s bookkeeping-replay block (`tardis_cefi_shards.py:446`, `if partition_writer is not None:`) is the
  ONLY place a per-symbol `record_shard_count`/`record_instrument` call happens — entirely skipped when `writer=None`.
- `_emit_per_symbol_manifest` (`tardis_batch_download.py:387`) — the function that DOES construct a real
  `ManifestWriter` unconditionally — only handles the failure/empty branches (`isinstance(_val, BaseException)`); for a
  successful `int` result it only accumulates `total_rows`, never calls a captured-row write.
- For every OTHER Tardis-CeFi venue, `record_captured` ultimately happens via a COMPLETELY different, day-level
  mechanism: `venue_fetch.py::_process_venue` constructs a real `PartitionedTickWriter` and passes it as `writer=writer`
  (non-`None`) — so the bookkeeping-replay block above DOES fire, accumulating into
  `writer._row_counts`/`writer.underlying_counts`. Later, `venue_fetch.py:421` (`_record_venue_shard_counts`) reads
  `writer.underlying_counts` and merges it into a SHARED, per-day, multi-venue `_DateRunState` accumulator, which is
  flushed to real `ManifestWriter.record_captured(...)` calls at the end of the whole day's venue loop — NOT per-venue,
  NOT something `_onchain_perp_batch_lighter.py`'s standalone handler has any access to (its signature has no
  `_DateRunState` parameter at all).

**Verified this is genuinely benign for data integrity, not for observability**: `gsutil ls` on the exact GCS paths
above confirms the real parquet objects exist with correct schema — the funding-rate data itself is 100% real and
usable. The gap is purely that the honest-coverage manifest will keep reading 0% captured for this cell even after a
fully successful backfill, until this is fixed.

**Why not fixed here**: properly wiring this handler into the day-level `_DateRunState` accumulator (or building an
equivalent narrower path) touches the SAME shared state machine every other cefi venue's manifest accounting depends on
— a wrong merge could double-count or corrupt concurrent venues' shard counts. This needs its own careful, tested
change, not a rushed addition alongside 3 already-shipped fixes in one session. A NARROWER, lower-risk alternative for
THIS specific already-known scope (LIGHTER-ZKSYNC derivative_ticker, precise instrument + date list) is a targeted
post-hoc reconciliation script that verifies each expected GCS object exists via `gcs_describe_object` (not a corpus
walk — the exact path set is fully known) and calls `ManifestWriter.record_captured(...)` directly per confirmed object
— see todo below.

## Todos

- [x] [FIX] P1. Implement the symbol-remap fix (approach 1 from the original proposal) in
      `market_tick_data_service/adapters/umi_tick_provider.py` (`_route_lighter` + `TardisAdapter.download_batch`), add
      regression tests for both LIGHTER-ZKSYNC and existing Tardis-CeFi venue coverage, `quality-gates.sh` green,
      commit + push. **DONE** — `market-tick-data-service@7a708284` (symbol fix) + `@039cddb6` (ContextVar
      thread-propagation fix, discovered live) + `@6bf568ee` (ts_event derivation fix, discovered live). 7 new
      regression tests total across 3 commits. Full `quality-gates.sh` green each time (358-360 Tardis-scoped tests, no
      regressions for any other venue).
- [x] [DATA] P2. Once fixed, re-launch the `(LIGHTER-ZKSYNC, derivative_ticker)` backfill for 2026-04-17..today (179
      instruments, bare-ticker `--instrument-ids`, SPOT, single Tardis-VM cap respected) and verify real `captured` rows
      land with non-null `funding_rate`. **DONE — full production backfill completed 2026-07-30.** VM
      `mtds-backfill-cefi-lighter-derivative-ticker-full-20260730` (179 instruments, 2026-04-17..2026-07-30, SPOT,
      e2-highmem-4, single Tardis-VM cap respected — verified 0 other Tardis VMs running both pre-launch and throughout
      via the fixed guard below) ran to `DEPLOYMENT_COMPLETED exit_code=0` in ~25 minutes wall-clock (00:39–01:04 UTC).
      Full-run log verification: **0** `schema contract violated` occurrences (down from 100% of writes before the 3
      fixes), 15,639 successful shard uploads across the 105-date range, **~1.10 billion real funding-rate rows
      written** (`funding_rate`/`open_interest`/`mark_price`/`index_price` columns all populated). 16,058
      `Stage-0 OBSERVE` lines are the known cosmetic filename-shape warning (bare-ticker filenames, e.g.
      `LIGHTER-ZKSYNC:PERPETUAL:APEX.parquet`, instead of the fully `-USDC@LIN`-suffixed canonical form) — informational
      only, not a write failure. Manifest visibility for this real data is the separate 4th finding below, tracked as
      its own todo, not a blocker on this todo's completion (the GCS data itself is the deliverable here).
- [x] [FIX] P1. **NEW finding.** Wire manifest `record_captured` recording for the LIGHTER-ZKSYNC (and by extension any
      future) delegated-to-`download_batch` onchain-perp-batch path — either (a) properly integrate with the day-level
      `_DateRunState`/`_record_venue_shard_counts` accumulator `venue_fetch.py` uses for every other venue, or (b)
      design a narrower, self-contained manifest-recording call inside `_onchain_perp_batch_lighter.py` itself once
      `download_batch` returns, using the per-symbol row counts it currently discards. Needs careful design + regression
      tests against the shared day-level state machine (option a) before shipping. Deliberately left open — a rushed
      write against the shared manifest-accounting state machine is a worse outcome than a documented, correctly-scoped
      follow-up. Repo: market-tick-data-service. **DONE — `market-tick-data-service@064f872a`.** Shipped option (b):
      `_emit_per_symbol_manifest` (`tardis_batch_download.py` → relocated to `tardis_cefi_shards.py`, which already owns
      `symbol_display_map_var`, per the 900-line codex ratchet) gained a `record_success` kwarg — self-records via
      `manifest.add(row_count=...)` for successful `int` results ONLY when `partition_writer is None` (today exclusively
      this LIGHTER-ZKSYNC standalone path), so every other Tardis-CeFi venue (which relies on the day-level flow) is
      provably unaffected — no double manifest write. Reuses the existing `symbol_display_map_var` ContextVar to resolve
      the numeric Tardis `market_id` back to the real ticker for `instrument_id`/`underlying`, so the manifest can never
      re-leak the numeric id this whole investigation started from. Both `_run_per_symbol_batch` call sites updated to
      pass `record_success=partition_writer is None`. 7 new regression tests (5 in
      `test_tardis_batch_download_fetch_evidence.py`: default `False` is a no-op, `True` self-records via
      `manifest.add`, numeric-symbol resolution via the display map, failures still route normally; 2 in
      `test_tardis_batch_download_failure_instrument_type.py` proving the `partition_writer`-gated wiring end-to-end at
      the `_run_per_symbol_batch` level). Full test suite for every touched Tardis/lighter file green (85 passed).
      `quality-gates.sh` green for all 4 changed files (the one QG failure present in the tree,
      `scripts/verify_kamino_solend_lending_relabel_2026_07_30.py` STEP 5.101, is foreign — committed by `slot-11` at
      2026-07-30 04:08 UTC, unrelated to and not touched by this fix). Pushed, `ahead=0`.
- [x] [DATA] P2. Once the manifest-recording gap is fixed (or as an interim narrower fix), run a targeted reconciliation
      pass for the ALREADY-WRITTEN real GCS data (the full 179-instrument × 105-date backfill completed above, ~15,639
      shards, ~1.10B rows): for each known (instrument, date) cell, `gcs_describe_object` the expected canonical path
      (fully enumerable, NOT a corpus walk — the exact scope is known and fixed) and
      `ManifestWriter.record_captured(...)` (or `record_captured_from_counts`, whichever fits the plain per-instrument
      shard shape — needs checking, the bundled-shard-oriented signature seen in `manifest_finalize.py` may not directly
      apply) directly for each confirmed-existing object. Repo: market-tick-data-service. **DONE —
      `market-tick-data-service@67dd6422`.** Resolved the open `record_captured` vs `record_captured_from_counts`
      question in favor of a THIRD option: `ManifestWriter.add()` (the same v9-compliant per-instrument API the shipped
      4th-bug fix now uses going forward — see `067dd6422`'s sibling `@064f872a`) — `record_captured` needs a real `df`
      for schema validation and `record_captured_from_counts` is bundled-shard-oriented (neither fits a plain
      per-instrument cell cleanly). New one-off script
      `scripts/reconcile_lighter_derivative_ticker_manifest_2026_07_30.py`: one `list_blobs` call per day (105 total,
      not a corpus walk) against the known canonical prefix, row counts read via a lazy range-reading wrapper so pyarrow
      reads ONLY the parquet footer (a few KB, not the several-MB-per-shard full file — downloading full bytes for
      ~15,000+ shards would have been an unbounded bulk transfer, genuinely unsuitable for a laptop). Hardened with
      retries (4 attempts + backoff) and per-cell skip-and-continue after a live dry-run hit real transient network
      failures (read timeouts, SSL EOF, even a transient local DNS resolution failure) partway through — a naive first
      pass let ONE bad read kill the whole 105-day sweep; the hardened version completed cleanly. **Verified via
      `--apply` on real prod data**: 105/105 dates scanned, **15,639 (ticker, date) cells recorded as captured, 0
      skipped** — an EXACT match to the original backfill's ~15,639 shards. Spot-checked the written per-VM manifest
      shard directly (`market-data-tick-cefi-prd-central-element-323112/_index/per_vm/local-20288-3b12.parquet`, 15,639
      rows): every row shows `venue=LIGHTER-ZKSYNC`, `data_type=derivative_ticker`, `instrument_type=PERPETUAL`,
      `source=tardis`, `pipeline_mode=batch_tardis`, `capture_status=captured`, clean bare `instrument_id`/`underlying`
      (no numeric market_id leak — reused the same `KNOWN_INSTRUMENTS` ticker list the backfill VM was launched with,
      not the raw Tardis wire filenames), plausible `row_count` values (tens of thousands per shard, consistent with the
      ~1.10B total rows / 15,639 shards ≈ 70k rows/shard average). Per-VM shard merges into the canonical index via the
      consolidator daemon within ~60s (never a direct index rewrite).
- [x] [PROCESS] P3. The Tardis-concurrency-guard's `TARDIS_VM_NAME_PATTERN`-based venue exemption list treats
      LIGHTER-ZKSYNC as blanket "non-Tardis" (`deployment-service/scripts/vm/tardis-concurrency-guard.sh`), but its
      `trades`/`book_snapshot_5`/`derivative_ticker` DO route through Tardis (confirmed throughout this and the
      companion doc's investigation, `pipeline_mode=batch_tardis`) — the guard's exemption is coarser than reality.
      **DONE — `deployment-service@45e1cd1`.** Removed LIGHTER-ZKSYNC from `TARDIS_CAP_EXEMPT_VENUES`; verified
      HYPERLIQUID (own `hyperliquid_s3.py` REST funding fetch), ASTER, EXTENDED-STARKNET (own distinct
      `pipeline_mode=batch_extended`, confirmed via manifest read — never `batch_tardis`), and COINBASE-CDE remain
      genuinely non-Tardis and correctly stay exempt. Manually verified `tardis_venue_list_needs_guard()`'s behavior for
      all 5 cases (LIGHTER-ZKSYNC alone, mixed with an exempt venue, EXTENDED-STARKNET alone, HYPERLIQUID+ASTER, a real
      Tardis venue) matches the intended fix exactly. This was live-relevant, not just a future-incident risk — the full
      179-instrument backfill above was actively consuming the single Tardis IP slot while this gap existed; confirmed
      the launcher's `VM_TARDIS_CONSUMER=1` metadata stamp is unconditional (not gated on the buggy pre-flight check),
      so the live blast radius was narrower than a fully-blind gap, but a second concurrent LIGHTER-ZKSYNC-only launch
      would have also skipped its own pre-flight check.
- [x] [DATA] P2. **NEW finding (post-archival, 2026-07-30).** 677 `attempted_failed` manifest rows from the ORIGINAL
      pre-fix backfill attempt (2026-07-29) were confirmed permanently dead: keyed on the raw numeric Tardis market_id
      (e.g. `"0"`, `"102"`) rather than the real ticker, so the manifest's "captured outranks any status" dedup rule
      (`unified_trading_library/manifest_writer/_read_index.py::_merge_shard_frames`) can never retire them — the real
      captured rows use a different key entirely, so these sit as permanent noise. Confirmed via code
      (`finalise_rows_and_path` raises `ValueError` BEFORE returning a `FinalisedShard` on schema violation — no
      partial/malformed GCS write ever happens) and empirically (0 GCS objects match a bare-numeric filename under this
      venue/data_type prefix) that this is a PURE manifest-metadata cleanup, no data migration needed. **DONE —
      `market-tick-data-service@3d38b7bf`** (new script
      `scripts/purge_lighter_derivative_ticker_prefix_schema_violation_rows_2026_07_30.py`, dry-run default + `--apply`
      snapshot-then-write, modeled on the `reclass_cefi_no_batch_source_phantom_rows_2026_07_29.py` precedent). **Per
      the heavy-I/O HARD RULE** (a full `_index/availability_index.parquet` rewrite — confirmed 9.5M rows
      workspace-wide, not a "known enumerable scope" like the P2 reconciliation above), the `--apply` write did NOT run
      locally (a local dry-run measured 7.5 minutes just to download the index over a flaky home connection — real
      evidence for exactly why this rule exists) — dispatched via AWS SSM to the human-planning VM
      (`i-0dd9812a96cdda5dc`, already-cloud-hosted, exempt) instead: same download there took **13 seconds**. Verified
      post-apply from the VM: `attempted_failed` fully gone for this combo (0 rows), `captured` unchanged at 15,639,
      `empty_confirmed`/`expected_unattempted` unchanged (33,323 / 25,249), pre-purge snapshot confirmed on GCS
      (`_index/snapshots/pre_lighter_derivative_ticker_schema_violation_purge_20260730T112932Z.parquet`, 195MB, fully
      reversible).

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the P1 manifest-recording fix is an
  explicit (a)-or-(b) design choice touching the shared day-level `_DateRunState` accumulator every cefi venue depends
  on; the P2 reconciliation is gated on it.

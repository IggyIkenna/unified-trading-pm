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
status: open
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

> Investigation-only record (this doc). No code was changed while authoring this doc — `assigned_vm: NA`, a human
> decides when to pick this up.

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

**Manifest impact — confirmed benign, no cleanup needed.** The schema-validation failures did NOT produce false
`attempted_failed` or false `captured` manifest rows — a fresh read shows the VM's ~10-minute run only wrote legitimate
`empty_confirmed` rows (18,616 `EXPECTED_PRE_SOURCE_COVERAGE_START` for genuinely pre-2026-04-17 dates the enumeration
pass touched, + 50 `SOURCE_RETURNED_ZERO`) — the schema-rejected cells were simply never written at all (neither as a
false success nor a false failure), leaving them in their prior state. No manifest-row cleanup is needed as a result of
this VM's activity.

## Why this matters

This is the reason `(LIGHTER-ZKSYNC, derivative_ticker)` shows **0 captured** rows in production despite the venue's own
smoke-test doc (`non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`) claiming a working Tardis fetch verified
via a one-off manual API probe (238,122 real rows, 2026-07-07). That manual probe likely used the ORIGINAL discovered
numeric-market_id values directly as ad-hoc verification (bypassing the normal `download_batch` schema-write path
entirely, e.g. inspecting the raw Tardis HTTP response), so it never hit this schema-contract failure — the bug is
specifically in the **production write path** (`_route_lighter` → `download_batch`), not in whether Tardis has the data
at all (confirmed it does).

## Proposed fix (not implemented — scoped for a future session)

`TardisAdapter.download_batch` is shared, widely-used infrastructure (every Tardis-CeFi venue routes through it) — a
blind edit here risks regressing every other venue's symbol handling, so this needs a careful, tested change, not a
quick patch. Two candidate approaches:

1. **Add an optional `symbol_remap: dict[str, str] | None` parameter to `download_batch`** (or to its
   writer/schema-normalization step) that translates the outgoing `symbol` column / filename-instrument-id AFTER fetch
   but BEFORE schema validation/write. `_route_lighter` would build this map (numeric market_id string → original
   ticker) at the same time it currently builds the forward map in `_resolve_lighter_tardis_instrument_ids`, and pass it
   through.
2. **A wrapping writer**, mirroring the existing `_ChainAnnotatingWriter` pattern (same file, lines 70-81) — a
   `_LighterSymbolRemappingWriter` that intercepts `write_chunk(df)` and remaps `symbol` before delegating. This only
   works cleanly if `download_batch` is called with an EXPLICIT writer; the current LIGHTER call site passes
   `writer=None` upstream (`_onchain_perp_batch_lighter.py:197`, `fetch_tick_data_for_venue(..., writer=None)`), so
   whether `download_batch`'s own default internal writer path can be intercepted this way needs checking first — if
   `writer=None` bypasses external hooks entirely, approach 1 is simpler and safer.

Either approach needs new unit tests confirming: (a) LIGHTER-ZKSYNC's written `symbol` values are tickers not numeric
IDs, (b) every OTHER Tardis-CeFi venue's behavior is byte-identical (regression guard), (c) a real (or VCR-cassette)
Tardis fetch produces a schema-valid parquet.

## Todos

- [ ] [FIX] P1. Implement one of the two approaches above in `market_tick_data_service/adapters/umi_tick_provider.py`
      (`_route_lighter` + `TardisAdapter.download_batch`), add regression tests for both LIGHTER-ZKSYNC and at least one
      other Tardis-CeFi venue, `quality-gates.sh` green, commit + push. Repo: market-tick-data-service.
- [ ] [DATA] P2. Once fixed, re-launch the `(LIGHTER-ZKSYNC, derivative_ticker)` backfill for 2026-04-17..today (179
      instruments, bare-ticker `--instrument-ids`, SPOT, single Tardis-VM cap respected) and verify real `captured` rows
      land with non-null `funding_rate`. Repo: market-tick-data-service / deployment-service launcher.
- [ ] [PROCESS] P3. The Tardis-concurrency-guard's `TARDIS_VM_NAME_PATTERN`-based venue exemption list treats
      LIGHTER-ZKSYNC as blanket "non-Tardis" (`deployment-service/scripts/vm/     tardis-concurrency-guard.sh`), but its
      `trades`/`book_snapshot_5`/`derivative_ticker` DO route through Tardis (confirmed throughout this and the
      companion doc's investigation, `pipeline_mode=batch_tardis`) — the guard's exemption is coarser than reality. Not
      a live problem today (no other Tardis VM was running during either launch in this session), but worth tightening
      the exemption to be per-(venue, data_type) rather than per-venue before it causes a real concurrent-IP-lockout
      incident. Repo: deployment-service.

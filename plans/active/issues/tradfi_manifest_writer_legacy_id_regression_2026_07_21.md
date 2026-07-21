---
doc_type: issue
title: TradFi equity/ETF manifest writer emits legacy bare-symbol ids LIVE — actively growing, not just historical debt
summary:
  The currently-running TradFi equity/ETF backfill fleet writes canonical GCS object paths/filenames but NON-canonical
  manifest rows (lowercase instrument_type, bare-symbol instrument_id) for the same capture — a live writer/manifest
  divergence, not a one-time historical migration gap. Measured 856,872 bad rows written on 2026-07-21 alone, growing
  continuously while backfill VMs run.
status: open
nature: record
asset_group: tradfi
created: 2026-07-21
tags: [tradfi, manifest, canonical, writer-bug, data-correctness, backfill]
related:
  [
    tradfi_consolidated_closeout_2026_07_18,
    data_pipeline_reconciliation_tradfi_2026_07_21,
    tradfi_manifest_row_loss_regression_2026_07_12,
  ]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
drift_direction: fix-code
depends_on: []
source:
  main session direct GCS/manifest read, 2026-07-21T16:04Z, cross-checked against a parallel content-migration
  root-cause investigation agent
locked_by:
resolved_by:
---

# TradFi manifest writer — live legacy-id regression (not historical debt)

## What's actually true (measured live, 2026-07-21T16:00-16:04Z)

Read the live TradFi manifest (`_index/availability_index.parquet` in
`market-data-tick-tradfi-prd-central-element-323112`) directly, filtered to `asset_group=tradfi`,
`capture_status=captured`, single-instrument rows (`underlying` null), `instrument_type` in `{equity, etf, spot_pair}`
case-insensitive:

| Population | Count   | `instrument_type`                      | `instrument_id` shape                                    | `written_at`                                                        |
| ---------- | ------- | -------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------- |
| Canonical  | 352,423 | UPPERCASE (`EQUITY`/`ETF`/`SPOT_PAIR`) | colon-shaped (`NASDAQ:EQUITY:AAPL-USD`)                  | **ALL exactly 2026-07-18**                                          |
| Legacy     | 858,165 | lowercase (`equity`/`etf`/`spot_pair`) | bare ticker (`IDXX`, `HON`, `ISRG`, `GOOG`, `META`, ...) | **856,872 written TODAY (2026-07-21)**, 1,258 on 07-19, 35 on 07-20 |

The canonical population is frozen at a single timestamp — it is entirely the one-time output of
`market-tick-data-service/scripts/migrate_tradfi_manifest_usd_lin_2026_07_18.py --apply --in-place-cas` (a historical
repair script). **Nothing new has been written in canonical form since.** The legacy population is overwhelmingly fresh
— written TODAY by the currently-running TradFi equity/ETF backfill fleet (`tradfi-bf-nasdaq-*` / `tradfi-bf-nyse-*`
VMs, part of this session's MVP backfill drive).

**Cross-check — the GCS object path/filename for the SAME live capture IS canonical**: sampled
`NASDAQ:EQUITY:AAPL-USD.parquet`, GCS creation time `2026-07-21T00:55Z` (written by today's active backfill). So **the
same writer, same capture event, produces a canonical file path but a non-canonical manifest row** — two code paths for
one event are out of sync, violating the shard-atom-identity invariant (path / manifest / content must agree —
`codex/02-data/availability-manifest-and-data-status.md`).

## Why this matters more than a normal migration gap

This was initially assumed (by an earlier `/data-pipeline-reconciliation` run on 2026-07-21 and this session's own prior
claims) to be **historical debt** — legacy 2020-2022 data that a content-migration pass needs to clean up once. It is
not (or not only) that. **The writer itself is currently emitting non-canonical manifest rows for BRAND NEW captures,
right now, continuously, at a rate of ~850K rows/day while the backfill fleet runs.** Any content-migration/cleanup pass
run before this writer bug is fixed will be immediately re-polluted by the next backfill cycle — exactly what happened
to the 2026-07-18 fix, whose output has sat frozen and un-repeated for 3 days while ~858K fresh bad rows piled up around
it.

This also means the tradfi id-form canonical percentage (measured 30.8% on 2026-07-21 morning) is **not stable** — it
will continue to fall as the backfill fleet keeps running, not just stay flat pending cleanup.

## Root cause (CONFIRMED + fixed for equity/etf/index)

`market_tick_data_service/engine/orchestrator/venue_fetch.py`'s `_canonicalize_manifest_instrument_id()` /
`_record_venue_shard_counts()` fed the raw bare ticker + the DataFrame's lowercase HIVE PARTITION `instrument_type`
token straight into the manifest `record_captured` call (`manifest_finalize.py:360-375`), instead of the SAME canonical
value `tradfi_shared.py`'s file-path derivation already computes. Two independent divergences, same root cause (raw
pre-derivation values reused instead of the canonical derived ones).

**Fixed**: `mtds@56d39325` — new whitelist-gated resolver `_tradfi_manifest_canon.py::resolve_tradfi_manifest_shard()`,
wired into both call sites. **Scoped to `equity`/`etf`/`index` only** (the 3 exhaustively-audited single-instrument hive
tokens); everything else returns `None` (byte-identical prior behavior) — deliberately narrow, not a full tradfi-wide
rewrite. 12 new regression tests. Full quality-gates green. Shipped via quickmerge.

**Confirmed NOT affected** (verified live, 2026-07-21T16:2xZ): `futures_chain`/`options_chain` CME bundle rows —
`instrument_id=null` is correct BY DESIGN for bundle grain (not a bug), and `underlying=SP500` (not raw `ES`) is already
the correct product-root translation. The `future`/`FUTURE` lowercase/uppercase split visible in an axis census is a
small (2,023-row), STATIC legacy population (all `written_at=2026-07-16`, nothing written since) — not something the
active CME backfill is writing into. So the CME futures/options backfill fleet was never in scope for this bug.

**Deliberately left unscoped by the fix** (flagged by the fixing agent, not guessed): FX `spot_pair` and other tradfi
cash types (`currency`/`bond`/`commodity`/`cds`) share the identical mechanism but route through a different UAC builder
branch (`_build_tradfi_cash` vs `_build_cefi_simple`) that wasn't verified — left untouched rather than risk a wrong
mapping on a live writer. Population size TBD — check before considering this closed.

**⚠️ Fix propagation gap (found post-ship, 2026-07-21T16:40Z)**: shipping the code fix does NOT retroactively patch
already-running VM processes (tarball-deployment model — a VM fetches its code tarball once at boot, never re-fetches).
Confirmed live: NASDAQ equity rows written AFTER the fix landed (`written_at > 16:20Z`) were still bare-ticker legacy
form. The published tarball (`gs://deployment-scripts-central-element-323112/code/mtds-code.tar.gz`) was also confirmed
STALE (didn't contain the new module) as of the fix landing — refreshed via `create-code-tarballs.sh` (so any NEW VM
launch from this point picks up the fix), but **every currently-running backfill VM will keep writing legacy-form rows
for equity/etf/index until it finishes naturally** — they are not being killed/restarted for this (would lose in-flight
capture progress). The historical content-migration pass therefore needs to cover everything written up through fleet
drain, not just the pre-2026-07-21 backlog.

## Recommended sequencing (do not skip ahead)

1. **Fix the writer** (root-cause code fix, not a data migration) — the manifest record call must use the same canonical
   `instrument_id` + UPPERCASE `instrument_type` enum that the file-path derivation already computes.
2. Only THEN does a historical content-migration/cleanup pass (the parallel root-cause investigation's proposed
   two-track design — manifest track via a corrected/extended
   `migrate_tradfi_manifest_usd_lin_2026_07_18.py --in-place-cas`, and a new parquet-content read-modify-write track for
   the raw tick objects) make sense to run and actually hold.
3. Re-measure the canonical % after both the writer fix AND the backfill fleet has drained, not before — an in-flight
   measurement will keep moving.

## Safety precedent to respect when touching the manifest

`tradfi_manifest_row_loss_regression_2026_07_12.md` (RESOLVED but real): a 1,017,024-row silent manifest loss from an
unguarded read-modify-write racing the manifest consolidator. Any manifest write here MUST use the CAS
(`if_generation_match`) pattern already shipped in `migrate_tradfi_manifest_usd_lin_2026_07_18.py` — never a naive
download-rewrite-upload. The writer-code fix itself (append-only `record_captured` calls, not a bulk rewrite) does not
carry this risk; the follow-up historical cleanup pass does.

## Progress Log

- **2026-07-21T16:04Z (main session)** — finding measured + written up; dispatched a background agent to locate the
  exact `record_captured` call site, diagnose the divergence, and ship a scoped fix if safe (agent authorized to ship
  directly if the fix is small/well-tested; told to stop and report a design instead if it's not confident). Also
  flagged to the operator in-chat per the workspace's big-finding rule.
- **2026-07-21T16:33Z (sub-agent)** — root cause confirmed + fix shipped `mtds@56d39325` (equity/etf/index only; 12 new
  tests; full quality-gates green). FX cash types + CME derivatives deliberately left unverified/out of scope.
- **2026-07-21T16:40Z (main session)** — operator asked an unrelated sanity-check question ("only 12 tradfi shards
  across instrument_type/data_type — sure?") which prompted a live axis census; that surfaced (a) the real captured
  landscape is 34 `(instrument_type,data_type)` pairs / 51 with venue — "12" was an undercount from an unknown source —
  and (b) confirmed CME `futures_chain`/`options_chain` are NOT affected by this bug (null id is by-design; underlying
  already correctly translated) — the earlier worry that CME derivatives shared this bug is RESOLVED, false alarm. Also
  found the fix hadn't reached the running fleet or the published tarball yet (tarball deploy model — VMs fetch code
  once at boot); refreshed the tarball (`create-code-tarballs.sh`) so new VM launches pick it up, but currently-running
  VMs will keep writing legacy-form equity/etf/index rows until they finish naturally (not killed — would lose in-flight
  capture progress). Separately found the tradfi MVP rule's `data_types` is still `{ohlcv_1m}` only (never extended to
  `ohlcv_1s` despite this session's backfill capturing both) — filed as a follow-up question for the operator, not yet
  resolved.

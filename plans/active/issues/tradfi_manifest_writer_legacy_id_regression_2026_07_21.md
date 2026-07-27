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
    tradfi_yahoo_venue_vendor_conflation_2026_07_27,
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
`/codex/02-data/availability-manifest-and-data-status.md`).

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
mapping on a live writer. **Checked live (2026-07-21T17:05Z): small, low-priority, DIFFERENT bug.** Only 3,126 total
rows (3,115 UPPERCASE `SPOT_PAIR` from the 2026-07-18 fix + 11 lowercase written today — negligible ongoing volume, not
a live-regression driver like equity/etf). But the "canonical" 3,115 rows are themselves broken a different way:
`instrument_id` is either the literal string `"ticks"` or blank, not a real derived id (`FX:SPOT_PAIR:KRW-USD`-shape) —
looks like a bundle-style `ticks.parquet` filename leaking into the id field rather than a per-pair id ever being
derived. Low priority given the tiny volume; needs its own small fix when convenient, not urgent.

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

## Post-drain re-measurement (2026-07-27, tradfi_satellite_ao_dispatch_batch4 todo)

**Method**: single-object read of the live `market-data-tick-tradfi-prd-central-element-323112`
`_index/availability_index.parquet` via `unified_trading_library`'s `get_storage_client().download_bytes(...)` +
`pandas.read_parquet` (NOT a bucket walk — same method the legacy-bucket/07-24 censuses used), 5,873,616 total manifest
rows scanned, filtered to `asset_group=tradfi`, `capture_status=captured`. Drain precondition independently re-confirmed
live: `gcloud compute instances list --project=central-element-323112` shows **zero** `tradfi-bf-*` instances in any
state (only unrelated `af-backfill-*`/`cefi-*`/`canonical-migration-*`/etc. VMs are running).

### Part 1 — equity/etf/index canonicality, split by `written_at` vs. the 2026-07-21T16:20Z fix landing

Single-instrument rows (`underlying` null), `is_canonical` = UPPERCASE `instrument_type` AND colon-shaped
`instrument_id`:

| `instrument_type` | cohort                      | canonical | total   | % canonical |
| ----------------- | --------------------------- | --------- | ------- | ----------- |
| equity            | pre-fix (written < 16:20Z)  | 29,330    | 29,330  | 100.00%     |
| equity            | post-fix (written ≥ 16:20Z) | 749,538   | 753,096 | 99.53%      |
| etf               | pre-fix                     | 294       | 294     | 100.00%     |
| etf               | post-fix                    | 114,238   | 114,292 | 99.95%      |
| index             | post-fix (no pre-fix rows)  | 5         | 105     | 4.76%       |
| **all three**     | post-fix combined           | 863,781   | 867,493 | **99.57%**  |

This is a dramatic improvement over the 30.8% pre-fix baseline cited at the top of this doc — the writer fix + fleet
drain worked as intended for the overwhelming majority of volume. **But there is a real, non-zero residual — see "New
residuals" below; this population is not simply the drain-window tail (0 of the residual rows fall inside the
2026-07-21T16:20Z–17:34:04Z fix-to-drain window — all of it is freshly-written, see below).**

### Part 2 — FX cash types verdict (settles the doc's explicitly-unverified scope)

Only `SPOT_PAIR` rows exist in tradfi for the cash-type set (`currency`/`bond`/`commodity`/`cds` = 0 rows found). 3,168
total `SPOT_PAIR` rows, **100% now UPPERCASE** (0 lowercase remain — confirms the casing half of
`tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`'s write-path fix, shipped
`market-tick-data-service@020b703e`/`b0fedf91` per that doc's batch4 resolution). **However, the `instrument_id`
POPULATION half of that same claimed fix does NOT hold on live data**: rows written _after_ the casing fix (venue=`FX`,
2026-07-22 n=22 and 2026-07-25 n=25) still carry bare `BASE-QUOTE` ids (e.g. `AUD-USD`, `EUR-USD` — no colon, not the
`FX:SPOT_PAIR:AUD-USD` form `test_fx_spot_pair_now_resolves_canonical` asserts), and the most recent rows (venue=
`YAHOO_FINANCE`, 2026-07-27, n=6, written literally during this measurement) carry **null** `instrument_id` — a
regression, not just incomplete. The 3,115 rows frozen at 2026-07-18 keep their known historical shapes (13
colon-shaped, 458 other-bare, 664 literal-string `"ticks"`). **Verdict: the FX write-path defect is NOT fully resolved**
— see "New residuals" below.

### Part 3 — CME derivatives verdict (settles the doc's other explicitly-unverified scope)

`futures_chain`/`options_chain` bundle rows (267,982 total, spanning 2026-06-22 through 2026-07-27, i.e. still being
actively written): `underlying` is confirmed correctly translated to product roots (`SP500`, `NASDAQ100`, `GOLD`,
`PLATINUM`, `SILVER`, `COPPER`, `NATGAS`, `AUD`, `CRUDE`, `BTC`, …), consistent with the doc's original by-design claim;
a null `instrument_id` remains the dominant shape for the bundle grain (151,136/155,485 `futures_chain`, 111,776/112,496
`options_chain`), with a smaller populated-id subset for per-leg rows. **Verdict: CONFIRMED, still not affected — no
regression detected here.**

**Stale sub-claim found and corrected**: the doc's "small (2,023-row), STATIC legacy population (all
`written_at=2026-07-16`), nothing written since" characterization of the separate `future`/`FUTURE` (singular)
instrument_type is now **wrong** — re-measured live, this population has grown to **9,126 rows** (`FUTURE`=8,927,
`future`=199; venues CME/ICE/CBOE), with `written_at` spanning 2026-06-22 through **2026-07-27** (today) — it is being
actively written into, not static. This is a separate, currently-uncharacterized population that needs its own follow-up
(not urgent — flagged as a residual below, not investigated further here per this todo's measure-only scope).

### New residuals found this pass (did not exist / were not characterized at the 2026-07-21 measurement)

1. **Equity/ETF live-path null-`instrument_id` writes (NASDAQ/NYSE, `ohlcv_1m`+`trades`) — 3,612 rows, ALL written
   2026-07-27T16:46:40–48Z (i.e. during this very measurement), with canonical UPPERCASE `instrument_type` (`EQUITY`/
   `ETF`) but `instrument_id=None`.** This is a **different failure shape** than the original bug (null, not
   bare-ticker) and provably NOT the drain-window tail (0 of these rows fall in the 16:20Z–17:34:04Z fix-to-drain
   window; 100% are freshly written days later, and the VM census above confirms zero `tradfi-bf-*` backfill instances
   are running). Something OTHER than the (already-fixed) backfill-fleet code path is writing these — most likely a
   live/scheduled capture path for NASDAQ/NYSE that was never in scope for `mtds@56d39325`'s fix. **Data-correctness
   regression, currently active.**
2. **CBOE `ohlcv_15m` `INDEX`/`OPTION` null-`instrument_id` writes — 103 rows (100 INDEX + 3 OPTION), ALL written
   2026-07-27T16:46:40–48Z** (same few-second window as finding 1, above) — this is what drives the "index" 4.76%
   canonical figure in Part 1. Brand-new, tiny volume, needs root-cause (is a CBOE 15-minute intraday capture even
   in-MVP-scope? if so its writer needs the same canonical-id treatment equity/etf/index got).
3. **FX `SPOT_PAIR` write-path is not actually fixed for new captures** (Part 2, above) — contradicts
   `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md`'s own todo-4 "(b) Write-path fix — ALREADY SHIPPED" claim.
   `test_fx_spot_pair_now_resolves_canonical` proves
   `_canonicalize_manifest_instrument_id("FX", "spot_pair", "EUR-USD")` returns the canonical form in isolation, but the
   live venue=`FX`/`YAHOO_FINANCE` capture path (`market_tick_data_service/adapters/_umi_yahoo.py::fetch_yahoo_fx`) is
   evidently not reaching (or not correctly using) that canonicalizer for the MANIFEST row's `instrument_id` field —
   only the file-path `instrument_id` (via `derive_tradfi_row_instrument_id`) is confirmed canonical; the manifest-row
   value is a separate derivation (`venue_fetch.py`'s
   `_canonicalize_manifest_instrument_id`/`resolve_tradfi_manifest_shard`) that live data shows is NOT landing the
   canonical form for this venue, and has regressed to null for the very latest (2026-07-27) rows. **Likely root cause,
   found while cross-checking this finding (not yet proven live)**: `resolve_tradfi_manifest_shard`
   (`_tradfi_manifest_canon.py:129`) short-circuits to `None` (no canonicalization at all) whenever
   `VENUE_TO_ASSET_GROUP.get(venue) != "tradfi"`. `unified_api_contracts`'s `VENUES_BY_ASSET_GROUP` registers `"FX"` and
   `"CBOE"` as real tradfi venues, but does **NOT** register `"YAHOO_FINANCE"` or `"YAHOO"` — so any row whose writer
   stamps a VENDOR name (Yahoo) into the `venue` field instead of the registered venue token silently gets NO
   canonicalization, of either the itype or the id. This would explain both this finding and finding 2 (CBOE rows) in
   one root cause, and is structurally the SAME class of bug as a sibling finding that landed in this same corpus today:
   `/plans/active/issues/tradfi_yahoo_venue_vendor_conflation_2026_07_27.md` documents
   `market_tick_data_service/market_interface/adapters/tradfi/yahoo_finance_adapter.py::write_canonical_shard`
   unconditionally stamping `venue="YAHOO"` (a DIFFERENT Yahoo adapter than `_umi_yahoo.py`, note — two separate Yahoo
   code paths exist) for every row it writes. **Not confirmed as the same bug** (that doc explicitly did not trace the
   manifest write path or check `VENUE_TO_ASSET_GROUP`), but the two findings should be investigated TOGETHER, not
   separately, given the shared shape (Yahoo-vendor-string-as-venue → asset_group lookup miss → canonicalization
   silently skipped).

### Recommendation

**Do NOT close this doc.** The writer fix + drain resolved the overwhelming bulk of the original bug (99.57%
equity/etf/index canonical, up from 30.8%), and the doc's two explicitly-unverified scopes are now settled (FX casing:
fixed; FX id-population: NOT fixed; CME derivatives: confirmed unaffected). But three live, currently-active residuals
were found this pass (none present/characterized as of 2026-07-21) that are small in volume (~3.7K rows total, <0.5% of
the equity/etf/index population) but **actively growing on the LIVE (non-backfill) write path** — small enough that they
do NOT warrant handing to the heavyweight historical content-recovery plan
(`tradfi_manifest_content_recovery_ completion_2026_07_24.md`, which is explicitly for the frozen historical backlog,
not a live regression), but real enough to need their own scoped root-cause-and-fix pass. See the follow-up todos below.

## Follow-up (unchecked, added 2026-07-27 by this re-measurement — NOT auto-dispatched, `assigned_vm: NA` on this doc)

- [ ] [DATA] P1. Root-cause + fix the live-path null-`instrument_id` write for tradfi equity/ETF (NASDAQ/NYSE,
      `ohlcv_1m`+`trades`) — find the call site writing these manifest rows (confirmed NOT the `tradfi-bf-*` backfill
      fleet, confirmed NOT within the 2026-07-21 fix-to-drain window) and apply the same canonical-id derivation
      `mtds@56d39325` gave the backfill path. Repo: market-tick-data-service. Source: this doc's 2026-07-27
      re-measurement, finding 1.
- [ ] [DATA] P2. Investigate the CBOE `ohlcv_15m` `INDEX`/`OPTION` null-`instrument_id` writes (103 rows, all
      2026-07-27) — confirm whether CBOE 15-minute intraday capture is in-MVP-scope, and if so give it the same
      canonical-id treatment. Repo: market-tick-data-service. Source: this doc's 2026-07-27 re-measurement, finding 2.
- [ ] [DATA] P1. Root-cause why the FX `SPOT_PAIR` manifest-row `instrument_id` is still bare (`BASE-QUOTE`, no colon)
      for post-2026-07-25 captures on venue=`FX`, and NULL for venue=`YAHOO_FINANCE` captures — this contradicts
      `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` todo-4's "already shipped" claim for the manifest write path.
      Start at `market_tick_data_service/adapters/_umi_yahoo.py::fetch_yahoo_fx` and trace how its record reaches
      `venue_fetch.py`'s `_canonicalize_manifest_instrument_id`/`resolve_tradfi_manifest_shard` (or bypasses it) for
      this venue. **Check the leading hypothesis first**: `resolve_tradfi_manifest_shard` no-ops whenever
      `VENUE_TO_ASSET_GROUP.get(venue) != "tradfi"`, and `"YAHOO_FINANCE"`/`"YAHOO"` are not registered tradfi venues
      (only `"FX"`/`"CBOE"`/etc. are) — if the writer is stamping a vendor name into `venue` for some rows, that alone
      would explain the silent no-canonicalization. Investigate TOGETHER with
      `/plans/active/issues/tradfi_yahoo_venue_vendor_conflation_2026_07_27.md` (same-day sibling finding: a DIFFERENT
      Yahoo adapter, `market_interface/adapters/tradfi/yahoo_finance_adapter.py`, unconditionally stamps `venue="YAHOO"`
      — not confirmed as the same bug, but the same shape). Repo: market-tick-data-service. Source: this doc's
      2026-07-27 re-measurement, finding 3.
- [ ] [DOC] P3. Re-verify and update the `future`/`FUTURE` (singular instrument_type) characterization — this doc
      previously called it a small (2,023-row) static legacy population; re-measured 2026-07-27 it is 9,126 rows and
      growing (written through today). Confirm whether this population needs the same canonical-id fix, or is a
      different, intentionally-uncanonicalized case. Source: this doc's 2026-07-27 re-measurement.

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
- **2026-07-27T~16:50Z (data_engineering worker, slot 4, `tradfi_satellite_ao_dispatch_batch4` todo)** — post-drain
  re-measurement per this doc's own "Recommended sequencing" step 3: read the live availability index as a single object
  (5,873,616 rows scanned), confirmed the backfill fleet drain live (zero `tradfi-bf-*` VMs running), and measured
  equity/etf/index canonicality split pre/post the 2026-07-21T16:20Z fix landing (99.57% post-fix, up from 30.8%).
  Settled both of the doc's explicitly-unverified scopes: FX cash-type casing is fixed (0 lowercase remain) but the FX
  `instrument_id` POPULATION is NOT fixed for live captures (contradicts batch4 todo-4's "already shipped" claim —
  flagged as finding 3); CME derivatives confirmed still unaffected. Found and recorded three new residuals not present
  at the 2026-07-21 measurement, all on the LIVE (non-backfill) write path: (1) 3,612 NASDAQ/NYSE equity/ETF rows with
  canonical type but NULL id, all written today; (2) 103 CBOE `ohlcv_15m` INDEX/OPTION rows with NULL id, all written
  today; (3) the FX write-path gap above. Also found the `future`/`FUTURE` population characterization is stale (was
  "static 2,023 rows", now 9,126 and growing). Verdict: doc stays OPEN (not closeable) — residual is small in volume but
  real and actively growing, warrants its own scoped fix pass, not the heavyweight historical content-recovery plan.
  Four follow-up todos added above. Full working scripts (not committed — scratch analysis) used
  `unified_trading_library.get_storage_client().download_bytes()` +
  `resolve_bucket_name(kind="market-data", asset_group="tradfi")`, single-object reads only, no GCS walk.

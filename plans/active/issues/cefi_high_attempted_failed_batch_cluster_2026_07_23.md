---
doc_type: issue
title:
  "6 CeFi DP_RUN_MOSTLY_EMPTY CRITICAL alerts (2026-07-22T23:16Z-2026-07-23T00:02Z) are a STATIC, already-diagnosed
  backlog re-firing, not a new incident -- 93-100% of the options_chain/futures_chain failures and 53-91% of the other 4
  data_types trace to the already-open Tardis concurrent-IP-lock 403 storm (tardis_concurrent_ip_lockout_2026_07_12.md)
  and the already-open DERIBIT chain-bundle capture gap (deribit_options_chain_af_g4_blocker_2026_07_03.md); a smaller,
  previously-uncatalogued 'FUTURE/OPTION row requires expiry_date' writer-validation tail is newly surfaced"
summary: >-
  Investigated a cluster of 6 `data-pipeline-alerts` CRITICAL `DP_RUN_MOSTLY_EMPTY` alerts for asset_group=cefi
  (derivative_ticker 16.9%, trades 28.7%, book_snapshot_5 34.4%, options_chain 100.0%, liquidations 7.3%, futures_chain
  99.8% attempted_failed). A live read of
  `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (10.5M rows) reproduces the
  alert's counts almost exactly and shows: (1) the alert is `alerting-service`'s `DP_RUN_MOSTLY_EMPTY` "static
  manifest-cell signal" (30-min re-fire cooldown, router.py:86) evaluating a CUMULATIVE manifest total, not a delta --
  no manifest write for ANY of the 6 data_types falls inside the stated alert window (newest `attempted_at` across all 6
  is 2026-07-21T11:47Z, and for 4 of the 6 it is 2026-07-13 to 2026-07-16, i.e. 6-30 days stale); (2) for options_chain
  (99.1%) and futures_chain (93.3%), the dominant failure signature is 112,600 identical `UNCLASSIFIED:Tardis HTTP 403`
  rows on venue=DERIBIT, `attempted_at` clustered 2026-07-03/07-04 -- the exact wave-1 reprobe already documented in
  `deribit_options_chain_af_g4_blocker_2026_07_03.md` (open, unresolved 18+ days) and root-caused workspace-wide in
  `tardis_concurrent_ip_lockout_2026_07_12.md` (open P0, Tardis academic key allows only 1 concurrent IP); (3) the same
  403-family (explicit "403" in `error_reason`) is 53-91% of the other 4 data_types' failures too, spread across many
  more venues (BITGET-FUTURES dominates liquidations); (4) a ~76,000-row-workspace-wide `VENUE_FETCH_FAILED` bucket
  (30-40% of derivative_ticker/trades/book_snapshot_5) is a NORMALIZED label applied post-hoc by
  `scripts/flip_cefi_bug_x2_leaked_text.py` over originally-distinct leaked-text causes (aiohttp payload-incomplete,
  CSV-decode errors, StreamingParquetWriter validation, and the "FUTURE/OPTION row requires 'expiry_date'" writer bug)
  -- NOT confirmed to share the 403-lock mechanism, and the original per-row cause is unrecoverable post-normalization;
  (5) a smaller, currently-live (2026-07-21, not yet normalized) recurrence of the same "FUTURE/OPTION row requires
  'expiry_date'" writer-validation error hits ~4,655 book_snapshot_5/trades rows, mostly DERIBIT -- not previously
  tracked in any open issue doc found in this investigation, flagged as a new, smaller finding. No GCS object, manifest
  row, or code was modified -- read-only.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, alerting-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, attempted-failed, cefi, tardis, concurrency-lock, options_chain, futures_chain, alerting]
related:
  [
    /plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md,
    /plans/archive/issues/tardis_concurrent_ip_lockout_2026_07_12.md,
    /plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md,
    /plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-07-23
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "6 CRITICAL DP_RUN_MOSTLY_EMPTY alerts, `data-pipeline-alerts` Slack channel, fired
  2026-07-22T23:16Z-2026-07-23T00:02Z, asset_group=cefi, bucket=market-data-tick-cefi-prd-central-element-323112"
last_updated: 2026-07-29
---

# CeFi `DP_RUN_MOSTLY_EMPTY` alert cluster (2026-07-22/23) -- root-cause + why it's not a new incident

## Alert as received

```
Event: DP_RUN_MOSTLY_EMPTY (severity CRITICAL), asset_group=cefi, bucket=market-data-tick-cefi-prd-central-element-323112
Window: 2026-07-22T23:16Z - 2026-07-23T00:02Z

data_type            attempted_failed   attempted     ratio
derivative_ticker    239,095            1,412,176     16.9%
trades               308,113            1,071,844     28.7%
book_snapshot_5      378,817            1,100,809     34.4%
options_chain        113,593            113,595       100.0%
liquidations          55,392              757,996      7.3%
futures_chain        120,646              120,868     99.8%
```

Alert description: "high attempted_failed batch -- a backfill exited 0 / captured climbed but failed this batch
invisibly."

## What happened (VERIFIED)

**Method**: read-only.
`gcloud storage cp gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` to local
scratch (10,523,348 rows, 178 MB), then `pandas`/`pyarrow` analysis of `capture_status`, `error_reason`, `venue`,
`attempted_at`, `date` per data_type. No GCS object, manifest row, or code was written, moved, or deleted at any point
in this investigation.

### The manifest reproduces the alert almost exactly (confirms this is the live manifest, not a stale/different copy)

| data_type         | manifest `captured` | manifest `attempted_failed` | `captured+af` | alert `attempted` |  delta |
| ----------------- | ------------------: | --------------------------: | ------------: | ----------------: | -----: |
| derivative_ticker |           1,174,923 |                     239,095 |     1,414,018 |         1,412,176 | +0.13% |
| trades            |             770,211 |                     308,113 |     1,078,324 |         1,071,844 | +0.60% |
| book_snapshot_5   |             726,416 |                     378,817 |     1,105,233 |         1,100,809 | +0.40% |
| options_chain     |                   2 |                     113,593 |       113,595 |           113,595 |  exact |
| liquidations      |             703,658 |                      55,392 |       759,050 |           757,996 | +0.14% |
| futures_chain     |                 222 |                     120,646 |       120,868 |           120,868 |  exact |

`attempted_failed` counts match the alert EXACTLY in all 6 rows; `attempted` (= `captured + attempted_failed`, excluding
`empty_confirmed`/`expected_unattempted`) matches within 0.6% (consistent with a few minutes of consolidator-merge drift
between when the alert evaluated and when this investigation read the index, not a different dataset).

### The alert is a static/cumulative signal, not a "this batch" delta -- confirmed from `alerting-service` source

```
alerting-service/alerting_service/notifiers/router.py:86:
    "DP_RUN_MOSTLY_EMPTY": 1800.0,  # 30 min; CRITICAL, static manifest-cell signal, >= 900s meta-sweep cadence
```

This is coded as a **static manifest-cell signal** re-evaluated on a periodic sweep (>=900s) and re-fired on a 1800s (30
min) cooldown if the condition is still true -- it is NOT a "just-ran-batch" delta check, despite the alert's own prose
description ("failed this batch invisibly"). The 46-minute alert window (23:16Z-00:02Z, 6 data_types) is consistent with
1-2 cooldown-gated re-fires across that period, not 6 independent fresh batches.

**Corroborating evidence — no manifest write falls inside the alert window, for any of the 6 data_types:**

| data_type         | newest `attempted_failed` `attempted_at` | newest `written_at`  | age vs alert (23:16Z 07-22) |
| ----------------- | ---------------------------------------- | -------------------- | --------------------------- |
| derivative_ticker | 2026-07-16T06:08:27Z                     | 2026-07-16T06:08:27Z | 6.7 days stale              |
| trades            | 2026-07-21T11:46:35Z                     | 2026-07-21T11:46:35Z | 1.5 days stale              |
| book_snapshot_5   | 2026-07-21T11:47:18Z                     | 2026-07-21T11:47:19Z | 1.5 days stale              |
| options_chain     | 2026-07-13T08:59:59Z                     | 2026-07-13T08:59:59Z | 9.6 days stale              |
| liquidations      | 2026-07-16T06:04:43Z                     | 2026-07-16T06:04:43Z | 6.7 days stale              |
| futures_chain     | 2026-07-16T06:08:27Z                     | 2026-07-16T06:08:27Z | 6.7 days stale              |

**This cluster is the sweep re-detecting an already-known, unremediated backlog, not a live regression that occurred
around 2026-07-22 23:16.**

## Root cause -- per data_type, explicit confidence

### options_chain: HIGH confidence -- Tardis concurrent-IP-lock 403 storm, wave-1 (2026-07-03/04)

`error_reason` breakdown of the 113,593 `attempted_failed` rows:

| error_reason                                               |    rows |     % |
| ---------------------------------------------------------- | ------: | ----: |
| `UNCLASSIFIED:Tardis HTTP 403`                             | 112,600 | 99.1% |
| `VENUE_FETCH_FAILED`                                       |     887 |  0.8% |
| `UNCLASSIFIED:HTTPSConnectionPool(...)`                    |     100 |  0.1% |
| `UNCLASSIFIED:Tardis HTTP 403 code=274 concurrent-IP-lock` |       6 |  0.0% |

`venue`: DERIBIT=113,587, DERIBIT-COMBO=6. `attempted_at` for the dominant 403 rows clusters exactly 2026-07-03 (76,050
rows) and 2026-07-04 (36,650 rows) -- microsecond-apart timestamps within each day, i.e. one fast automated sweep, not
organic drip. `row_count`/`instrument_count` are 0 for every one of these rows (genuine zero-byte fetch failures, not
partial captures). `pipeline_mode=batch_tardis` for 100%.

This is the **same population** already documented in `deribit_options_chain_af_g4_blocker_2026_07_03.md` (filed
2026-07-03 at af=10,114/captured=1; corroborated 2026-07-15 at af=113,595/113,596, 99.999% -- i.e. this doc's numbers
today, 113,593/113,595, are within 2 rows of that reading 8 days ago) and root-caused in
`tardis_concurrent_ip_lockout_2026_07_12.md`: the shared academic-tier Tardis API key permits only ONE concurrently
active IP; every VM in a multi-VM wave beyond the first gets `HTTP 403` for its entire overlapping runtime. The
`UNCLASSIFIED:` prefix (vs the later `Tardis HTTP 403 code=274 concurrent-IP-lock` tag) is expected: these rows'
`attempted_at` (07-03/07-04) predate the 403-body-parsing/code=274-tagging fix (`market-tick-data-service@31934527`,
shipped 2026-07-12).

### futures_chain: HIGH confidence -- same 403 core (93.3%), plus a smaller, more recent 404 wave (6.6%)

| error_reason                            |    rows |     % |
| --------------------------------------- | ------: | ----: |
| `UNCLASSIFIED:Tardis HTTP 403`          | 112,600 | 93.3% |
| `UNCLASSIFIED:404 GET https`            |   7,918 |  6.6% |
| `UNCLASSIFIED:HTTPSConnectionPool(...)` |     100 |  0.1% |
| `In CSV column #5`/`#7`                 |      28 |  0.0% |

`venue`: DERIBIT=112,700 (the 403 core, `attempted_at` 07-03/07-04 -- identical wave to options_chain), BYBIT=5,250 +
BINANCE-FUTURES=2,696 (the 404 tail, `attempted_at` 2026-07-15/07-16 -- a distinct, smaller, later wave).

`deribit_options_chain_af_g4_blocker_2026_07_03.md`'s 2026-07-18 correction banner is directly on point:
`options_chain`/`futures_chain` are **our own per-underlying shard bundles** (MTDS fetches per-symbol
trades/book_snapshot_5/derivative_ticker/options_chain via Tardis and aggregates by underlying), not a Tardis-side
channel -- so this is a genuine capture gap on our side, not a source-absence to reclassify. Per
`cefi_consolidated_closeout_2026_07_18.md` Track-2, the fix is to CAPTURE the underlying per-symbol data (viable since
the throughput-collapse fix, ~14 MB/s) and let the bundle build -- a dedicated DERIBIT-light backfill wave ("Wave-3
DERIBIT LIGHT, options_chain") is designed in that plan but, per its own 2026-07-20 snapshot, the single Tardis cap-1
slot was held by a different wave (`cefi-queue-heavy-binancefutu-x17-...`); DERIBIT specifically was called out there as
"8.6% (af 114k -- worst)". This investigation found no options_chain/futures_chain manifest write since 2026-07-13/07-16
respectively, consistent with that DERIBIT-specific wave still not having run as of this alert.

### derivative_ticker / trades / book_snapshot_5: MEDIUM-HIGH confidence for the majority; residual tail not

individually root-caused here

Splitting each data_type's `attempted_failed` rows by whether `error_reason` contains the literal substring `"403"`:

| data_type         | 403-family rows | % of af | `VENUE_FETCH_FAILED` | % of af | remainder | % of af |
| ----------------- | --------------: | ------: | -------------------: | ------: | --------: | ------: |
| derivative_ticker |         127,722 |   53.4% |               95,805 |   40.1% |    15,568 |    6.5% |
| trades            |         197,979 |   64.3% |               98,158 |   31.9% |    11,976 |    3.9% |
| book_snapshot_5   |         254,013 |   67.1% |               97,444 |   25.7% |    27,360 |    7.2% |

**403-family (53-67%): same mechanism as options_chain/futures_chain**, but spread across many more venues than just
DERIBIT (derivative_ticker's 403 rows: DERIBIT 112,663, BINANCE-FUTURES/BYBIT/KRAKEN-FUTURES/BITFINEX-FUTURES/
BITGET-FUTURES the rest) and multiple historical waves, not only 2026-07-03/04 -- e.g. the
`tardis_concurrent_ip_lockout_2026_07_12.md` doc's own "RECURRENCE" section documents a 2026-07-14 6-VM BITGET-FUTURES
wave that ran WITHOUT the lease and 403'd completely. This is the same already-tracked, still-open P0 issue, not a new
mechanism.

**`VENUE_FETCH_FAILED` (26-40%): NOT confirmed to share the 403-lock mechanism -- do not assume it does.** Read directly
from source: this label is a **post-hoc normalization**, not a live capture-time classification.
`market-tick-data-service/scripts/flip_cefi_bug_x2_leaked_text.py` (docstring + `_LEAKED_TEXT_PATTERNS`) bulk-rewrites
`attempted_failed` rows whose ORIGINAL `error_reason` matched one of 5 "leaked text" patterns --
`"Response payload is not completed"` (aiohttp), `"FUTURE row requires 'expiry_date'"` /
`"OPTION row requires 'expiry_date'"` (writer pre-write validation, see below), `"In CSV column #..."` (Tardis CSV
decode), or `"StreamingParquetWriter pre-write validation failed"` -- to the single canonical label
`VENUE_FETCH_FAILED`, to make downstream dashboard grouping work. **The original per-row cause is unrecoverable from the
current manifest** (the rewrite is destructive/in-place). All `VENUE_FETCH_FAILED` rows in this manifest carry
`attempted_at` 2026-06-23/06-24 -- an EARLIER, separate wave than the 07-03/04 403 storm. Their true sub-cause mix (how
much is genuinely the expiry_date writer bug vs. a transient aiohttp truncation vs. a CSV decode issue) was not
re-diagnosed in this pass -- flagged as an open question, not claimed to be either the 403-lock issue or something new.

**Remainder (4-7%)**: small tails of `Tardis HTTP 400/500/503`, `UNCLASSIFIED:404 GET https`, individual
`In CSV column #N` errors, `Connection timeout to host`, and (book_snapshot_5/trades only) a **currently-live,
NOT-yet-normalized** recurrence of `"FUTURE row requires 'expiry_date'"` -- see the dedicated subsection below.

### liquidations: MEDIUM-HIGH confidence -- same 403-family mechanism, concentrated on BITGET-FUTURES not DERIBIT

`venue` breakdown of the 55,392 `attempted_failed` rows: BITGET-FUTURES=40,273 (72.7%), BYBIT=8,797, DERIBIT=2,243,
OKX-SWAP=1,104, BINANCE-FUTURES=1,097, KRAKEN-FUTURES=949, BITFINEX-FUTURES=928.

403-family (`Tardis HTTP 403` + `Tardis HTTP 403 code=274 concurrent-IP-lock`, both ALREADY classified -- these
`attempted_at` postdate the 2026-07-12 tagging fix) = 50,373 of 55,392 = **90.9%**. Per-venue: BITGET-FUTURES 403-share
= 34,181/40,273 = 84.9%; KRAKEN-FUTURES/BITFINEX-FUTURES/OKX-SWAP are almost entirely `code=274`-tagged (899/928/1,003
of their small totals). `attempted_at` spans 2026-06-23, 2026-07-03/04, 2026-07-12, 2026-07-14, 2026-07-15/16 -- i.e.
liquidations was hit by essentially every wave the lockout issue's Progress Log documents (2026-06-23 pre-fix wave,
07-03/04 storm, 07-12 corroboration, 07-14 BITGET no-lease recurrence, 07-15/16 tail). Same root cause as the others,
just concentrated on a different venue because BITGET-FUTURES liquidations happened to be in-flight during more of those
waves.

### New, smaller finding: recurring "FUTURE/OPTION row requires 'expiry_date'" writer-validation bug, live as recently

as 2026-07-21 -- not found tracked in any existing open issue doc

`market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:544` (FUTURE) and `:516-518` (OPTION) raise
`ValueError("FUTURE row requires 'expiry_date'")` /
`"OPTION row requires 'expiry_date', 'strike', and 'option_right' ..."` when none of the venue-specific expiry-parsing
helpers (`parse_deribit_future_symbol`, `_parse_numeric_futures_expiry`, `_parse_month_code_futures_expiry`) can extract
an expiry from the raw symbol. A code comment at line 356 documents ONE prior instance of exactly this error class
already root-caused and fixed (`market-tick-data-service@55ec86ac`, 2026-07-14: BITGET-FUTURES/legacy-BYBIT no-dash
CME-month-code dated-quarterly symbols, e.g. `BTCUSDH25`).

A FRESH, un-normalized recurrence exists in the live manifest with `attempted_at` **2026-07-21** (i.e. only ~1.5 days
before this alert cluster, the most recent write activity found anywhere in this investigation for these 6 data_types):

| data_type       | rows (attempted_at >= 07-20) | venue breakdown                                                                                                                                                       |
| --------------- | ---------------------------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| book_snapshot_5 |   3,947 of 4,666 recent rows | DERIBIT 4,183, COINBASE-FUTURES 189, COINBASE-SPOT 185, BITFINEX-FUTURES 104, OKX-FUTURES 5 (venue counts are for the whole 4,666-row recent slice, both error types) |
| trades          |       108 of 145 recent rows | DERIBIT 144, OKX-FUTURES 1                                                                                                                                            |

This is DERIBIT-dominant but NOT the already-fixed BITGET-FUTURES shape (BITGET-FUTURES does not appear in the venue
breakdown of these recent rows at all). Given the concurrent, actively-tracked
`deribit_combo_perpetual_partition_move_2026_07_21.md` finding (DERIBIT combo/multi-leg symbols like
`BTC-FS-25SEP26_27FEB26` routinely defeat the standard FUTURE/OPTION symbol regexes), a combo-shaped symbol reaching
this expiry-parsing fallback and failing is a **plausible but NOT confirmed** explanation -- this investigation did not
trace which exact symbols triggered these 4,655 rows (out of scope for a read-only manifest-level pass; would need the
run.log or a live symbol-level replay). No existing open issue doc found in this workspace (`plans/active/issues/`,
`codex/`) tracks this specific DERIBIT/COINBASE-FUTURES/BITFINEX-FUTURES/OKX-FUTURES recurrence -- flagged as a
genuinely new, smaller finding, not a duplicate of anything read.

## Is this one root cause or several? (honest answer, per the investigation task)

**Not one root cause -- a dominant shared cause plus at least two smaller, distinct tails:**

1. **Dominant (53-99% depending on data_type)**: the Tardis concurrent-IP-lock 403 storm -- ONE mechanism, already
   root-caused, already has an open P0 issue doc (`tardis_concurrent_ip_lockout_2026_07_12.md`) and a partial mitigation
   shipped (opt-in GCS-lease serialization + a `tardis-concurrency-guard.sh` cap-1 launcher guard, per CLAUDE.md's
   2026-07-16 "HARD cap 1 concurrent" ruling) -- but the HISTORICAL poisoned rows from before that mitigation have never
   been retried/cleared, so they sit permanently in the denominator until the specific shards are re-attempted.
2. **`VENUE_FETCH_FAILED` (26-40% of derivative_ticker/trades/book_snapshot_5)**: a normalized label over multiple
   DIFFERENT original leaked-text causes; not confirmed to share cause #1's mechanism; not re-diagnosed to the sub-cause
   level in this pass.
3. **`FUTURE/OPTION row requires 'expiry_date'` (small, <1.5% overall, but the ONLY genuinely-recent/live signature
   found)**: a writer-side symbol-parsing gap, ONE instance of which was already fixed for BITGET-FUTURES; a fresh,
   un-fixed recurrence exists for DERIBIT/COINBASE-FUTURES/BITFINEX-FUTURES/OKX-FUTURES as of 2026-07-21.
4. **Small residual tails** (CSV column parse errors, connection timeouts, HTTP 400/500/503, 404s) -- not individually
   investigated; consistent with ordinary transient venue/network noise, not sized or attributed further.

## Why 6 alerts fired together in a 46-minute window

Per the `alerting-service` code evidence above: `DP_RUN_MOSTLY_EMPTY` is a static-condition CRITICAL alert with a 30-min
cooldown against a >=900s (15-min) sweep. All 6 data_types have been sitting at a critically-high `attempted_failed`
ratio continuously for days (their newest write is 1.5-9.6 days before this alert window); the sweep simply re-evaluated
all 6 cefi data_type cells in the same pass and re-fired each independently once its own 30-min cooldown allowed. This
is expected re-fire behavior for a genuinely-still-bad, unremediated condition -- not evidence of a fresh regression at
23:16Z on 2026-07-22.

## Prior/related open work (do not duplicate -- cross-link)

- `deribit_options_chain_af_g4_blocker_2026_07_03.md` -- **open**, unresolved 18+ days ("Open actions" all unchecked).
  This doc's numbers (113,593/113,595) are within 2 rows of that doc's 2026-07-15 corroboration entry (113,595/113,596).
  Same population, same blocker.
- `tardis_concurrent_ip_lockout_2026_07_12.md` -- **open** P0. Root-caused the 403 mechanism; shipped the opt-in
  GCS-lease mutex + CAS hardening + 403-code-274 tagging; the final `[DATA] P1` "post-fix G4 re-run" todo is still
  unchecked, gated on production waves accumulating enough post-fix history. CLAUDE.md now documents the stricter
  2026-07-16 "hard cap 1 concurrent" operator ruling that supersedes this doc's 2026-07-14 "2-3 VMs is workable" interim
  guidance.
- `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md` -- **open** P0, separate denominator-
  corruption mechanism (HTTP 400 "impossible combination" symbol/date pairs recorded as `attempted_failed` instead of
  excluded). Not directly measured as a contributor to THIS cluster's numbers (no `error_reason` in this manifest read
  showed the `code=300`/`code=140` signature this doc describes), but the same denominator-honesty class of bug.
- `deribit_combo_perpetual_partition_move_2026_07_21.md` -- **open**, design-only. Cross-referenced above as a plausible
  (not confirmed) explanation for the fresh `expiry_date` recurrence.
- `cefi_consolidated_closeout_2026_07_18.md` Track-2 -- the coverage-backfill plan that owns the actual remediation
  (capture the underlying per-symbol data so the options_chain/futures_chain bundles build); DERIBIT-specific Wave-3 was
  designed but, per that plan's 2026-07-20 snapshot, not yet run (cap-1 slot held by another wave).

## Recommendation

1. **Do not open new root-cause investigation for options_chain/futures_chain or the 403-family majority of the other 4
   data_types** -- it is the already-diagnosed, already-P0-tracked Tardis concurrent-IP-lock issue. The actionable
   unblock is operational, not diagnostic: run `cefi_consolidated_closeout_2026_07_18.md`'s already-designed Track-2
   "Wave-3 DERIBIT LIGHT" backfill (cap-1, `tardis-concurrency-guard.sh`-gated) once the single Tardis slot is free, and
   more broadly work through that plan's queued waves for the other venues carrying 403-family debt (BITGET-FUTURES,
   BYBIT, KRAKEN-FUTURES, BITFINEX-FUTURES, BINANCE-FUTURES).
2. **Close the loop on `tardis_concurrent_ip_lockout_2026_07_12.md`'s open `[DATA] P1` todo** (post-fix G4
   re-measurement) once a genuine post-cap-1 production wave has run long enough to accumulate fresh history -- this
   alert cluster is itself evidence that hasn't happened yet for cefi as a whole.
3. **`VENUE_FETCH_FAILED` needs its own targeted follow-up** if anyone wants to close the gap on
   derivative_ticker/trades/book_snapshot_5 beyond the 403-family majority -- the original leaked-text sub-causes are
   gone from the manifest (normalized away), so this would need either historical run.log archaeology or accepting the
   ~26-40% as an un-attributed but already-corralled bucket.
4. **File (or fold into an existing plan) a dedicated follow-up for the fresh `expiry_date` recurrence** -- it is the
   only genuinely LIVE (2026-07-21) signature found in this investigation, it is small (~4,655 rows) but growing, it is
   NOT the already-fixed BITGET-FUTURES shape, and no existing open issue doc names it. Worth a symbol-level trace (pull
   the real run.log for the 2026-07-21 DERIBIT writes) before assuming the combo-symbol hypothesis above.
5. **Alerting-hygiene question for whoever owns `alerting-service` (process recommendation, not a data bug)**: consider
   whether `DP_RUN_MOSTLY_EMPTY` should suppress re-paging CRITICAL on a condition with zero new manifest activity for
   multiple days (i.e. distinguish "actively failing right now" from "known-bad backlog, already tracked, not moving")
   -- as currently coded it will keep CRITICAL-paging every 30 minutes indefinitely until the backlog is actually
   cleared, which may be intended (keep visible pressure on an open P0) or may be alert fatigue; not asserting either
   way, flagging for an operator/owner decision.

## What is NOT claimed

- Did not verify whether the Track-2 DERIBIT Wave-3 backfill has been launched or completed between the plan's
  2026-07-20 snapshot and now (2026-07-23) -- the manifest shows no new options_chain/futures_chain capture activity
  since 07-13/07-16, which is consistent with it not having run yet, but this investigation did not check live VM fleet
  status (`gcloud compute instances list`) or the plan's Progress Log for a more recent entry -- read-only manifest
  analysis only, per this task's scope.
- Did not individually root-cause the ~26-40% `VENUE_FETCH_FAILED` bucket in derivative_ticker/trades/book_snapshot_5 to
  the sub-cause level -- the original per-row error text was destructively normalized away by
  `flip_cefi_bug_x2_leaked_text.py` before this investigation; only the script's own docstring's declared pattern list
  is available, not a per-row breakdown.
- Did not trace which exact symbols triggered the 4,655 fresh `expiry_date` rows, nor confirm the combo-symbol
  hypothesis -- flagged as plausible, not verified.
- Did not measure whether `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`'s `code=300`/
  `code=140` signature contributes to this specific manifest snapshot -- no `error_reason` value observed in this read
  matched that signature, but a full search for it was not the primary focus of this pass.
- Did not touch, modify, re-run, retry, or delete anything -- one `gcloud storage cp` read of the availability index to
  local scratch, followed by local `pandas` analysis, and source-code `grep`/`Read` only. No manifest write, no GCS
  write, no VM launch, no backfill triggered.
- Did not verify the alert-evaluation service itself (whatever computed the exact ratios in the Slack message) beyond
  reading `alerting-service`'s static cooldown/threshold constant -- the underlying sweep/query code that produces the
  per-data_type ratios was not located or read in this pass.

## Todos

- [x] ✅ [OPS] P0. **DONE 2026-07-26 (slot-4, `data_engineering`) — confirmed NOT running, and confirmed it should NOT
      be launched right now (design has changed since this todo was written).** `gcloud compute instances list` (project
      `central-element-323112`, all zones): no VM matching `deribit`/`wave`/`tardis` in name — nothing running. Fresh
      manifest read (`gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`): DERIBIT
      `options_chain` is still 113,615 `attempted_failed` / 10,096 `empty_confirmed` / 1 `captured`; `futures_chain` is
      112,728 `attempted_failed` / 10,983 `empty_confirmed` — essentially unchanged from this doc's own numbers. The
      only 2026-07-25 activity is a small unrelated 56-row (`28+28`) `404 GET https` tail, not a Wave-3 run (a real wave
      would touch tens of thousands of rows). **Root cause this todo missed (written 2026-07-23, superseded
      2026-07-25):** `cefi_consolidated_closeout_2026_07_18.md`'s Track 2 was **forked** 2026-07-25 to
      `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`, which subsumes the old per-venue "Wave-3 DERIBIT LIGHT"
      concept into one consolidated resume-backfill todo — and that forked plan is `status: draft` with
      `depends_on: [cefi_migration_cutover_and_track8_completion_2026_07_25]` + `gate_on_depends: true`, explicitly
      because "launching before the Track-1 drain re-enables would fight the consolidator." Checked the gating plan
      (`/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`): also `status: draft`, all 5
      of its own todos unchecked, **no Progress Log section at all** — Track 1 has not started. So launching DERIBIT
      Wave-3 (or any Track-2 backfill) right now would violate the plan authors' own explicit sequencing gate, not just
      be premature. **Correct action: do not launch.** This is now tracked as a machine-gated dependency
      (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`'s first todo, "Resume the cefi Tardis COVERAGE
      backfill") that will dispatch automatically once Track 1 completes — no separate DERIBIT-specific launch is needed
      or correct to force now.
- [x] ✅ [REVIEW] P1. **RESOLVED-AS-SUPERSEDED 2026-07-27 (slot-4)** — traced the reference chain and found there is no
      live checkbox to close: `tardis_concurrent_ip_lockout_2026_07_12.md` itself has ZERO open `- [ ]` todos (every
      item already `[x]`), and the doc its 2026-07-14 entry names as owning the actual re-measurement
      (`mvp_backfill_cefi_tick_v10_2026_06_27.md` G4) is ARCHIVED with `status: complete`/"zero open todos" since
      2026-07-15. More importantly, the tardis doc's OWN 2026-07-25 SUPERSEDED banner already reconciles this: the G4
      re-measurement this todo asks for was scoped to compare pre/post the **lease** mechanism
      (`TARDIS_CONCURRENCY_LEASE`, N=3-concurrent-with-lease model) that doc built and measured through 2026-07-14 — but
      the operator's 2026-07-16 ruling replaced that whole approach with a hard **N=1-concurrent-VM cap**
      (`tardis-concurrency-guard.sh`), which the lease-era measurement never covered. So there is no valid "close the
      old G4 re-measurement" action left to take — the thing it would have measured no longer exists in the current
      architecture. Attempted a live manifest read for a fresh post-cap-1 attempted_failed/403 census anyway
      (`read_availability_index` on `market-data-tick-cefi-prd-central-element-323112`) but got 0 rows both total and
      post-2026-07-16 — inconclusive (likely a wrong call signature on my part, not proof of genuine absence at
      ~7.5M-row scale) — NOT reporting this as a real finding. **Recommendation**: if a fresh post-N=1-cap
      attempted_failed/403 census is still wanted, scope it as a NEW todo against the current architecture (not a
      "close" of this now-moot lease-era one).
- [x] [DATA] P1. **DONE 2026-07-27 (slot-15)** — Traced the fresh (2026-07-21) `"FUTURE row requires 'expiry_date'"`
      recurrence to specific symbols via a bounded, column-projected manifest read (no VM, no corpus walk; `venue`,
      `instrument_type`, `data_type`, `instrument_id`, `capture_status`, `error_reason`, `attempted_at` columns only).
      **Two corrections to the finding above, plus the hypothesis CONFIRMED (not just plausible):** 1. **Venue-breakdown
      correction.** The `error_reason` column IS the specific per-row cause — filtering the whole
      `book_snapshot_5`+`trades` manifest for `error_reason` literally containing `"expiry_date"` returns **4,812 rows,
      100% `venue=DERIBIT`, 100% `instrument_type=FUTURE`, 0 rows on any other venue and 0 rows with the `OPTION`
      variant of the message, ever.** The earlier finding's venue table
      (`COINBASE-FUTURES 189, COINBASE-SPOT 185, BITFINEX-FUTURES 104, OKX-FUTURES 5`) was **not** the expiry_date bug's
      venue distribution — its own caveat said so ("venue counts are for the whole 4,666-row recent slice, both error
      types") but the surrounding prose read as if those venues shared this specific defect. They do not: those venues'
      rows in the same time window carry unrelated causes (measured separately: `Resolver requires aiodns library` 791,
      `UNCLASSIFIED:404 GET https` 368, `Tardis HTTP 500` 344, `Tardis HTTP 403 code=274 concurrent-IP-lock` 200,
      `UNCLASSIFIED:UpstreamTimestampBiasError` 150 — a different, already-covered mix, not this todo's scope). 2.
      **Symbol-level trace — the manifest's own `instrument_id` column IS the failing raw symbol.** For an
      `attempted_failed` row, `instrument_id` carries the raw wire symbol (id-resolution never completed), e.g.
      `BTC-CS-25DEC26-110000_120000`, `BTC-FS-25DEC26_13FEB26`, `BTC-CBUT-26JUN26-75000_90000_100000` — read directly,
      no run.log needed. **786 distinct failing symbols. Ran the real `is_deribit_combo_symbol_shape()` classifier (not
      a re-implemented regex) against all 786: 786/786 = 100% combo-shaped.** The DERIBIT-combo hypothesis in the
      finding above is CONFIRMED, not merely plausible. 3. **Already fixed, zero recurrence since.** Max `attempted_at`
      across all 4,812 expiry_date rows is `2026-07-21T11:47:18Z` — the day BEFORE `market-tick-data-service@2ddc6d4a`
      (2026-07-22T18:28:09Z, the `deribit_combo_perpetual_partition_move_2026_07_21.md` §9 `[WRITER] P1` guard-widen,
      independently re-verified earlier this same session) shipped. Zero rows with `attempted_at` on or after the fix.
      This is the SAME mechanism and SAME fix as that doc's root cause (a combo-shaped bare-`DERIBIT` symbol falling
      through to the `FUTURE`-branch's expiry-parsing helpers, all of which structurally cannot extract a single expiry
      from a multi-leg combo id) — the guard-widen hoists `is_deribit_combo_symbol_shape` above that branch, so a combo
      symbol is now classified `COMBO` before ever reaching the code that raised. **No new issue doc needed** —
      extending `deribit_combo_perpetual_partition_move_2026_07_21.md` with a cross-link is sufficient (added there);
      this is not a new mechanism, it is the same one's OTHER symptom (a hard write failure via `ValueError`, vs that
      doc's silent mispartition via a passthrough). 4. **Residual, unfixed by the guard-widen**: this HISTORICAL backlog
      of 786 symbols × up to ~35 days each (4,812 `attempted_failed` rows) is still sitting in the manifest as permanent
      capture gaps — the guard-widen only stops the bug from recurring going forward; it does not retry the historical
      failures. Retrying them is a normal backfill re-attempt (idempotent, no code change needed) — not filed as a
      separate todo here since it is the same "historical poisoned rows never retried" class already named in this doc's
      own § "Is this one root cause or several?" item 1, not a new gap.
- [x] ✅ [DATA] P2. **Labeling half DONE + SHIPPED 2026-07-28 (slot-8) — `deployment-service@6f464325`** (rebased from
      the earlier local `cf895170` once `RB-18e1c305`'s cross-repo fastapi-cap conflict cleared; verified
      `git merge-base --is-ancestor 6f464325 origin/live-defi-rollout` = true). Surfaces `max_attempted_at`/`stale_days`
      per `attempted_failed` cell and labels the `DP_RUN_MOSTLY_EMPTY` alert body/details "STATIC BACKLOG" vs "Fresh".
      This closes the determinable half of the original todo (can an on-call reader tell static-backlog from
      fresh-failure at a glance) — split into its own checkbox since it is a normal shippable-unit fix, distinct from
      the judgment call below.
- [x] ✅ [BACKEND] P2. **SHIPPED 2026-07-29 (slot-9, `alerting-service@bb76cae`) — verified 2026-07-29 (slot-13,
      `backend_engineer`).** RULED 2026-07-28 (previously gated on an operator decision, retagged 2026-07-28 slot-10 →
      then retagged again with a ruling applied) — stop the 30-min CRITICAL re-page once a cell is labeled "STATIC
      BACKLOG"; downgrade to a lower-severity periodic reminder, do NOT go fully silent.** Ruling + reasoning: none of
      the operator's 8 general-theme bullets (backfill/migration completion, full-functionality-no-shortcuts, cost,
      Databento, manifest version, pause/unpause, auto-recovery, live-probing-scope, adaptor completion) speaks to
      alerting/paging cadence directly, but the workspace already has a codified, applicable precedent for exactly this
      class of decision: CLAUDE.md's own "AO alerts / Slack notifications" rule — "standing conditions dedup by
      state-transition (fire on change / RESOLVED / re-remind), never every tick." A `DP_RUN_MOSTLY_EMPTY` cell that has
      sat unmoving for days (this doc's own finding: 1.5-9.6 days stale at alert time) re-paging CRITICAL every 30
      minutes is exactly the "every tick" anti-pattern that principle already rejects elsewhere in this workspace, and
      applying it here is the closest thing to a determinable, non-arbitrary answer available. Concrete spec for the
      implementer: once `attempted_failed_staleness.py`'s STATIC BACKLOG label fires for a cell (already shipped,
      `deployment-service@6f464325`), suppress the 30-min CRITICAL re-page for that SPECIFIC cell and instead emit a
      single lower-severity (WARNING/INFO) reminder on a much longer cadence (e.g. daily, or on next state-transition —
      matching the "fire on change" half of the precedent) so the open P0 stays visible without the fatigue-inducing
      30-min drumbeat; the moment the cell's `error_reason`/`attempted_at` shows genuinely fresh activity (state
      transitions back to non-static), CRITICAL paging resumes immediately, unsuppressed. This is a normal
      alerting-service code change (repo: alerting-service), not a judgment call requiring further sign-off — the
      precedent above is the sign-off.
- [ ] [DATA] P3. If pursued, a targeted historical run.log pull to attribute the `VENUE_FETCH_FAILED` bucket's original
      leaked-text sub-causes (aiohttp/CSV-decode/streaming-writer/expiry_date) proportionally, rather than leaving it as
      one un-attributed bucket.

## Progress Log

- **2026-07-29 (data_pipeline_failure escalation worker, agt-79063c):** A DP-FETCH-009 re-page for
  `(cefi, futures_chain)` dispatched this worker with no issue doc pre-linked; it initially mis-fixed the finding
  (removed `futures_chain` from the cefi Tardis launchers + re-ran the banned
  `reclass_cefi_futures_chain_no_tardis_source.py` against prod) before finding this doc +
  `deribit_options_chain_af_g4_blocker_2026_07_03.md`'s 2026-07-18 correction banner, which rules that exact fix out.
  Reverted both actions same session (full account in that doc's 2026-07-29 entry) — net effect on this cluster is zero,
  the backlog is exactly as this doc already describes it (still gated on Track-2). Also corroborates: `futures_chain`'s
  DERIBIT population is still ~112,700+ attempted_failed (403-storm core) plus small ~2,442-row 404 tail plus a
  newly-observed small daily trickle (2026-07-26 through 07-29, ~124 rows/day across
  BINANCE-DELIVERY/BINANCE-FUTURES/BYBIT/DERIBIT) — i.e. the launcher IS still periodically retrying and re-failing
  futures_chain daily, consistent with Track-2 not having run yet. Cross-linked from
  `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md`.
- **2026-07-28 (gated-decision retag sweep)** — Applied a ruling to the outstanding `[OPERATOR]` paging-cadence
  decision: stop the 30-min `DP_RUN_MOSTLY_EMPTY` CRITICAL re-page once a cell is labeled STATIC BACKLOG, downgrading to
  a lower-severity periodic reminder rather than full silence — reasoning drawn from the workspace's own existing "dedup
  by state-transition, never every tick" alerting precedent (CLAUDE.md § AO alerts), since none of the 8 general-theme
  bullets speaks to paging cadence directly. Retagged the todo from `[OPERATOR]` to `[BACKEND]` (normal alerting-service
  code change) with the full ruling + concrete implementation spec written into the todo. Docs-only, no code changed.
- **2026-07-26 (slot-4, `data_engineering`, task `cefi_satellite_ao_dispatch_batch2-008`):** Investigated the OPS P0
  todo above. No DERIBIT/Wave-3 VM is running (`gcloud compute instances list`, all zones, project
  `central-element-323112`). Fresh manifest read confirms the options_chain/futures_chain backlog is essentially
  unchanged from this doc's original 2026-07-23 numbers (113,615/112,728 `attempted_failed`), with only a small 56-row
  unrelated 404 tail from 2026-07-25 — no Wave-3 run has happened. Traced why:
  `cefi_consolidated_closeout _2026_07_18.md`'s Track 2 was forked 2026-07-25 into
  `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`, which is machine-gated
  (`depends_on`/`gate_on_depends: true`) on `cefi_migration_cutover_and_track8_completion _2026_07_25.md` — and that
  gating plan hasn't started (draft, all 5 todos unchecked, no Progress Log). Launching DERIBIT Wave-3 (or any Track-2
  backfill) right now would violate the plan authors' own explicit anti-race sequencing ("would fight the
  consolidator"), so the correct action is NOT to launch — this todo's original "launch it if not running" instruction
  is stale relative to the 2026-07-25 fork+gate redesign. No VM launched, no manifest/GCS write. Todo flipped with this
  finding.
- **2026-07-28 (slot-8, `backend_engineer`, task `cefi_high_attempted_failed_batch_cluster-003`):** Worked the P2
  `[REVIEW]` alerting-hygiene todo. The todo as written ("Decide (operator/alerting-service owner) whether...") is a
  process/policy judgment call, not a determinable fact — per CLAUDE.md's dispatch-scope-eligibility rule, that decision
  isn't mine to make unilaterally. Split it: implemented the SAFE, non-decision half — surfaced
  `max_attempted_at`/`stale_days` per `attempted_failed` cell in `deployment-service`'s `check_high_attempted_failed`
  (new sibling module `attempted_failed_staleness.py`, mirrors `renag_tracker.py`/`known_dead_cells_registry.py` to stay
  under the 920-line file cap) and annotated the `DP_RUN_MOSTLY_EMPTY` alert body/details "STATIC BACKLOG — no new
  attempted_failed activity in Nd" vs "Fresh" once a cell has gone ≥1 day with no new activity. This answers the "can an
  on-call reader tell static-backlog from fresh-failure" half WITHOUT touching paging/suppression behavior — that policy
  call (should it also stop re-paging) stays explicitly open for the operator/alerting-service owner, unchanged by this
  commit. Code: `deployment-service@cf895170` — full `quality-gates.sh` green (2903 passed, 71.25% coverage), new
  regression tests for the staleness computation + the annotation reaching the finding details/summary. **NOT yet
  shipped**: quickmerge's ancestor cascade hit a genuine, pre-existing, unrelated cross-repo blocker —
  `unified-trading-library@3b99d19d` bumped `fastapi>=0.137.0` while `canonical-dependency-manifest.json` +
  `deployment-service`'s own pyproject.toml still cap `<0.137.0` (SSOT contradiction, already filed as P0
  `plans/archive/issues/fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md` by another agent; I added one
  corroborating finding there re: `deployment-api`'s route-ordering test). Verified this is NOT my diff's fault
  (reproduced on a clean tree) and did NOT attempt a unilateral partial fix (tried it, found it silently drops 140 test
  items via `deployment-api`'s broken peer install, reverted). Declared repo-blocker `RB-18e1c305` on
  `deployment-service` so the fleet backend tracks the wait; will resume shipping once that clears. This todo stays
  `- [ ]` (not done) — done_definition requires shipped code, which is blocked, and the underlying paging-suppression
  question is separately still open for the operator.
- **2026-07-28 (slot-10, `review`, task `cefi_high_attempted_failed_batch_cluster-003`):** Re-dispatched the same task
  id slot-8 worked. Verified the labeling code slot-8 left blocked (local `cf895170`) has since shipped as
  `deployment-service@6f464325` (`git merge-base --is-ancestor 6f464325 origin/live-defi-rollout` = true; repo-blocker
  `RB-18e1c305` is resolved, `GET /api/repo-blockers` returns `open: []`) — no code change needed from this session.
  Split the todo: flipped the labeling half `[x]` with the shipped SHA as evidence, and retagged the remaining
  paging-suppression policy question `[OPERATOR]` (was `[REVIEW]`) so it stops auto-redispatching to workers who have no
  standing to decide it — this is the second worker in a row (slot-8, then this session) to correctly decline the
  unilateral call per CLAUDE.md's dispatch-scope-eligibility rule. No GCS/manifest write, no VM launch, no code shipped
  this session (PM plan-doc edit only).
- **2026-07-29 (slot-13, `backend_engineer`, task `cefi_high_attempted_failed_batch_cluster-009`):** Dispatched onto the
  final `[BACKEND]` P2 paging-cadence todo; found it already implemented and shipped moments earlier by a concurrent
  session (`alerting-service@bb76cae`, slot-9, `git merge-base --is-ancestor bb76cae origin/live-defi-rollout` = true)
  but the checkbox was not yet flipped. Verified the implementation end-to-end rather than re-doing the work: (1) new
  sibling module `alerting_service/notifiers/dp_run_mostly_empty_static_backlog.py` implements `effective_severity()`
  (downgrades `CRITICAL`→`WARN` for a `DP_RUN_MOSTLY_EMPTY` cell carrying `details["is_static_backlog"] is True`) and
  `dedup_window_override()` (widens the dedup cooldown from 1800s to 86400s for the same condition, `default`
  passthrough otherwise); (2) `router.py`'s `_route_data_pipeline_event` applies `effective_severity` BEFORE the
  `severity is AlertSeverity.CRITICAL` paging-channel check, so a STATIC BACKLOG cell still mirrors to
  `#data-pipeline-alerts` (per the "never fully silent" requirement) but skips the PagerDuty/Telegram page; (3)
  confirmed the field-name contract end-to-end — `deployment-service`'s `meta_watchers.py:651` stamps
  `"is_static_backlog": is_static_backlog` (from `attempted_failed_staleness.py`'s `stale_backlog_annotation()`) onto
  the same details payload `router.py` reads; (4) the shipped
  `tests/unit/notifiers/test_router_dp_run_mostly_empty_static_backlog.py` covers all four required cases (static cell
  suppresses PagerDuty but still Slack-mirrors at WARN severity; fresh cell pages CRITICAL unchanged; missing
  `is_static_backlog` field back-compat defaults to paging, not silent suppression). Implementation matches the ruling's
  concrete spec exactly. No code change needed this session — flipped the checkbox with the shipped SHA as evidence.
  Both remaining todos in this doc (`[DATA] P3` and the always-open Progress Log) are unaffected. No GCS/manifest write,
  no VM launch; PM plan-doc edit only.

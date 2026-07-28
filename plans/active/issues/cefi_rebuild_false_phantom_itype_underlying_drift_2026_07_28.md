---
doc_type: issue
title:
  cefi rebuild_cefi_manifest false-phantom rate is ~8.6% (490,639/5.68M rows) — itype/underlying column drift, NOT
  DERIBIT-chain-only
summary: >-
  Re-ran rebuild_cefi_manifest --dry-run over the full corpus (2019-01-01..2026-07-28); phantom_to_failed=490,639 (~8.6%
  of prior index) failed the "small + DERIBIT-chain-style only" gate — itype/underlying column drift, fixed
  (market-tick-data-service@dcbed674). Post-fix re-run (2026-07-28) confirms the fix works (phantom_to_failed
  490,639→50,615, 89.7% reduction) BUT the gate is STILL not met: DERIBIT is only 5.0% of the residual. A SECOND,
  distinct root cause found (also confirmed live via 3 GCS spot-checks) — the prior manifest's instrument_id used an
  older fully-qualified format (VENUE:TYPE:SYM@MARGIN) that differs from the current live GCS filename stem for the same
  physical object. Needs a venue-aware instrument_id normalizer (new todo), NOT a blanket ignore (unlike
  itype/underlying, instrument_id disambiguates distinct instruments — over-suppressing would hide TRUE phantoms).
  Blocks the "NEXT SESSION — execute the migration" P0 todo in data_completion_cefi_2026_07_15.md (and Phase D of its
  successor plan cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md) until fixed + re-validated.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, manifest, honest-coverage, false-phantom, cf-11, data-correctness]
related: [../data_completion_cefi_2026_07_15.md]
created: "2026-07-28"
source: data_completion_cefi_2026_07_15.md todo re-run (slot-12, data_engineering)
resolved_by:
locked_by:
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

## What I found

Re-ran `market_tick_data_service.scripts.rebuild_cefi_manifest --dry-run` over the FULL corpus
(`--start-date 2019-01-01 --end-date 2026-07-28`, per the plan's "multi-year dry-run phantom spot-check" todo) against
`gs://market-data-tick-cefi-prd-central-element-323112`. First attempt required an env fix: `GCP_PROJECT_ID` must be
exported for the CF-11 pass's direct-consolidated-index read to succeed — without it, `get_project_id()` raises and the
pass silently falls back to `read_availability_index`, which itself found nothing and logged "prior _index is
empty/missing" (a **false-negative** result: it looked clean only because the CF-11 pass never actually ran against real
data). Re-ran with `GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp` exported.

Final summary (elapsed 753.2s):

```
total_shards: 4,545,458   unparseable: 0   distinct_venues: 26   distinct_dates: 2,675
reemit_attempted_failed: 942,674
reemit_empty_confirmed: 755,445
reclassified_to_failed: 218,705
phantom_to_failed: 490,639          <-- the gate this todo exists to check
dropped_malformed_captured: 25,413
reemit_skipped_covered: 3,244,340
reemit_out_of_range: 0
```

Prior-index total ≈ 5,677,228 rows. **`phantom_to_failed` = 490,639 = ~8.6% of the entire historical manifest** — the
plan's acceptance criterion ("`phantom_to_failed` stays small + well-formed, DERIBIT-chain-style true phantoms only") is
**NOT met**. Per-venue phantom volume is spread across nearly every major venue, not concentrated in DERIBIT
options/futures chains: OKX-FUTURES, HYPERLIQUID, ASTER, BYBIT-SPOT, OKX-SWAP, BINANCE-FUTURES, COINBASE-FUTURES,
BITFINEX-FUTURES, BITGET-FUTURES, KRAKEN-FUTURES all show large counts (partial sample before completion: OKX-FUTURES
113,750 / HYPERLIQUID 95,577 / ASTER 77,230 / BYBIT-SPOT 52,388 phantom lines — the DERIBIT count in the same partial
sample was only 5,429, i.e. DERIBIT is a small minority of the total, not the dominant class the acceptance criterion
anticipated).

**Root cause confirmed live (not a hypothesis) — 3 independent spot-checks, 100% false-phantom hit rate:**

The CF-11 covered-keys dedup (`_rebuild_cefi_cf11.py:311-336`) builds the prior-row key as
`(day_str, venue_str, itype_str, dtype_str, iid_str, underlying_str)` where `itype_str` and `underlying_str` are read
**directly from the prior manifest's stored columns** (`row.get("instrument_type")`, `row.get("underlying")`), then
compared for exact-tuple membership in `covered_keys` (built from the live object scan's parsed path). When the prior
manifest's stored `instrument_type`/`underlying` values don't match what the CURRENT GCS path structure encodes for the
identical physical object, the row is falsely declared phantom (`PHANTOM_CAPTURED_NO_OBJECT`) even though the parquet is
sitting right there. Confirmed via live `bucket.list_blobs()`:

1. **OKX-FUTURES, date=2022-08-15, `derivative_ticker`, `OKX-FUTURES:FUTURE:ETH-USDT@LIN-20220930`** — flagged phantom.
   Object EXISTS at
   `raw_tick_data/by_date/day=2022-08-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=OKX-FUTURES/instrument_type=perpetual/data_type=derivative_ticker/OKX-FUTURES:FUTURE:ETH-USDT@LIN-20220930.parquet`.
   The instrument_id embeds the literal token `FUTURE`, and the prior manifest apparently stamped
   `instrument_type=future` from this (or from an earlier writer generation) — but the CURRENT GCS path segment is
   `instrument_type=perpetual`. Exact-tuple compare fails on `itype`.
2. **ASTER, date=2024-01-10, `trades`, `ASTER:PERPETUAL:ARB-USDT@LIN`** — flagged phantom (prior row's `underlying`
   column = `ARBUSDT`). Object EXISTS at
   `raw_tick_data/by_date/day=2024-01-10/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/instrument_type=perpetual/data_type=trades/ASTER:PERPETUAL:ARB-USDT@LIN.parquet`
   — a per-instrument (non-bundled) path, so the object scan derives `underlying=""` for this cell (per
   `rebuild_cefi_manifest.py`'s per-instrument branch), but the prior manifest recorded a non-blank `underlying` value
   for the same physical row. Exact-tuple compare fails on `underlying`.
3. **BYBIT-SPOT, date=2022-01-02, `book_snapshot_5`, `BYBIT-SPOT:SPOT_PAIR:BOBA-USDT`** — flagged phantom. Object EXISTS
   at
   `raw_tick_data/by_date/day=2022-01-02/pipeline_mode=batch_tardis/asset_group=cefi/venue=BYBIT-SPOT/instrument_type=perpetual/data_type=book_snapshot_5/BYBIT-SPOT:SPOT_PAIR:BOBA-USDT.parquet`
   — same pattern as (1): instrument_id embeds `SPOT_PAIR`, prior manifest likely stamped `instrument_type=spot_pair`,
   current GCS path is `instrument_type=perpetual`. Exact-tuple compare fails on `itype`.

This is the SAME BUG CLASS as the already-fixed `spot`→`spot_pair` `_ITYPE_SYNONYMS` entry (2026-06-11) and the
already-fixed slash-symbol stem regex (2026-06-04, "1187 false phantoms") — but it is **not covered** by either existing
fix. It looks like most/all non-bundled CeFi venues' actual GCS folder structure has settled on
`instrument_type=perpetual` regardless of what the instrument_id token or an older manifest-writer generation recorded,
and the CF-11 exact-tuple key match never accounts for this drift.

`unparseable=0` (criterion met) and `dropped_malformed_captured=25,413` (~0.45% of the prior index; the malformed
predicate — blank venue/dtype, literal `"ticks"` id, or fully-blank id+underlying — reads as junk-only, consistent with
the plan's expectation) look fine. **`phantom_to_failed` is the criterion that fails, and by a wide margin.**

## Re-run confirmation (2026-07-28, post-fix @dcbed674) — fix WORKED but gate still NOT met, second distinct root cause found

Re-ran the identical full-corpus `rebuild_cefi_manifest --dry-run` (`--start-date 2019-01-01 --end-date 2026-07-28`,
`GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp`) against the SAME bucket, on top of the shipped fix
(market-tick-data-service@dcbed674). Elapsed 2089.6s. Final summary:

```
total_shards: 4,558,590   unparseable: 0   distinct_venues: 26   distinct_dates: 2,676
reemit_attempted_failed: 942,542
reemit_empty_confirmed: 770,802
reclassified_to_failed: 233,074
phantom_to_failed: 50,615           <-- down from 490,639 pre-fix (89.7% reduction)
dropped_malformed_captured: 22,793
captured_processed_passthrough: 12
reemit_skipped_covered: 3,263,234
reemit_skipped_shadow: 468,555      <-- NEW field: the itype/underlying-drift shadow-suppression firing, confirms the fix is live
dropped_legacy_drift_recon: 0
reemit_out_of_range: 0
```

The shipped fix is confirmed WORKING — `reemit_skipped_shadow=468,555` accounts almost exactly for the prior
`phantom_to_failed` drop (490,639 → 50,615 ≈ 440K fewer phantoms, consistent with most of the 468,555 shadow-suppressed
rows previously would have been phantom-demoted). **However the acceptance gate ("small DERIBIT-chain-style residual
only") is still NOT met** — per-venue breakdown of the remaining 50,615 phantom rows:

```
OKX-SWAP: 12,921   BINANCE-FUTURES: 9,427   COINBASE-FUTURES: 8,442   BYBIT: 5,608
OKX-FUTURES: 4,329  BITGET-FUTURES: 3,198   BITFINEX-FUTURES: 2,610  DERIBIT: 2,545
KRAKEN-FUTURES: 812  COINBASE-CDE: 388      HYPERLIQUID: 309         ASTER: 26
```

DERIBIT is only 2,545/50,615 (5.0%) — still a small minority, NOT the dominant class. (DERIBIT's own residual sampled as
expected — bundled-chain `instrument_id=BTC`/`ETH` rows, consistent with the genuine true-phantom class the acceptance
criterion anticipated.)

**Root cause of the residual, confirmed live (not a hypothesis) — 3 independent spot-checks via `bucket.list_blobs()`,
100% false-phantom hit rate, same methodology as the original diagnosis:**

1. **OKX-SWAP, date=2021-03-18, `liquidations`, prior iid=`OKX-SWAP:PERPETUAL:LTC-USD@INV`** — flagged phantom. The
   physical object EXISTS at
   `raw_tick_data/by_date/day=2021-03-18/pipeline_mode=batch_tardis/asset_group=cefi/venue=OKX-SWAP/instrument_type=perpetual/data_type=liquidations/LTC-USD-SWAP.parquet`
   — filename `LTC-USD-SWAP.parquet` (bare legacy stem), not the fully-qualified `OKX-SWAP:PERPETUAL:LTC-USD@INV` the
   prior manifest recorded. Exact-tuple + shadow compare both fail on `instrument_id` itself (the shadow key still
   requires exact iid match — it only ignores itype/underlying).
2. **BINANCE-FUTURES, date=2020-08-11, `book_snapshot_5`, prior iid=`BINANCE-FUTURES:PERPETUAL:OMG-USDT@LIN`** — flagged
   phantom. Object EXISTS at
   `.../venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=book_snapshot_5/BINANCE-FUTURES:PERPETUAL:OMG-USDT.parquet`
   — same qualified prefix but MISSING the `@LIN` margin-type suffix.
3. **COINBASE-FUTURES, date=2025-01-25, `book_snapshot_5`, prior iid=`COINBASE-FUTURES:PERPETUAL:FLOW-USD@INV`** —
   flagged phantom. Object EXISTS at
   `.../venue=COINBASE-FUTURES/instrument_type=perpetual/data_type=book_snapshot_5/COINBASE-FUTURES:PERPETUAL:FLOW-USD.parquet`
   — same pattern, missing `@INV`.

**This is a DIFFERENT bug class than todo 1's fix**: todo 1 generalized the shadow key to ignore `instrument_type` and
`underlying` DRIFT between the prior manifest's stored columns and the live scan — but it still requires an EXACT
`instrument_id` string match. Here the drift is IN `instrument_id` itself: the prior manifest recorded an
older/alternate fully-qualified format (`VENUE:TYPE:SYM@MARGIN`) while the CURRENT live GCS filename for these (venue,
instrument) pairs is either the bare stem without the `@MARGIN` suffix, or (OKX-SWAP specifically) an entirely different
legacy token (`-SWAP` instead of `@INV`). Per `rebuild_cefi_manifest.py`'s `parse_hive_path`, the live-scan
`instrument_id` for a per-instrument Tardis-canonical shard IS the raw filename stem verbatim — there is no
margin-type-suffix stripping/normalization on the SCAN side either, so this is a genuine instrument_id FORMAT mismatch,
not a parser bug.

**Why this fix is NOT a mechanical repeat of todo 1's**: ignoring `instrument_type`/`underlying` was safe because
`instrument_id` alone already uniquely identified the physical object for a given (date, venue, data_type) — so widening
the shadow key to ignore those two columns could only ever correctly de-duplicate, never wrongly suppress a distinct
instrument. Ignoring `instrument_id` drift is NOT safe the same way: `instrument_id` is the ONLY field that
disambiguates between multiple genuinely-different instruments captured under the same (date, venue, data_type) —
naively dropping `iid` from the shadow key (matching on `(day, venue, dtype)` alone) would suppress TRUE phantoms too (a
real missing instrument on a busy multi-instrument day would be falsely shadowed by ANY other instrument object present
that day/venue/dtype). This needs a **venue-aware/format-aware instrument_id normalizer** (e.g. strip a trailing
`@LIN`/`@INV`/`@SWAP`-style margin-type token from the prior manifest's iid before compare, and special-case OKX-SWAP's
`-SWAP` suffix token), not a blanket ignore — and it needs enough per-venue format enumeration to be confident it does
not collapse two genuinely different instruments into one shadow key. This is genuinely a design-and-verify task, not a
mechanical generalization — flagged as a NEW todo below rather than attempted inline.

## Why it matters

The next plan todo ("NEXT SESSION — execute the migration") is explicitly gated on this dry-run "validating perf" before
running the REAL (non-dry-run) rebuild, which would `record_failed(error="PHANTOM_CAPTURED_NO_OBJECT")` on every one of
these ~490K rows for real. That would corrupt ~8.6% of the historical manifest — silently downgrading genuinely
captured, present data to `attempted_failed`, which would then (a) misreport historical coverage as incomplete when it
is not, and (b) likely trigger unnecessary re-fetch/backfill attempts against venues that already have the data, wasting
real compute/API-quota cost for no data gain. This is a data-pipeline-correctness HARD RULE matter — the fix must land
and a clean re-run must confirm before the migration proceeds.

## Recommended decision

1. **BLOCK** `data_completion_cefi_2026_07_15.md`'s "NEXT SESSION — execute the migration" P0 todo from running until
   this is fixed and re-validated (added as a blocking note on that todo in the same commit as this issue doc).
2. **Fix** (AO-eligible, scoped, data_engineering craft, repo `market-tick-data-service`): extend the CF-11 covered-keys
   comparison in `_rebuild_cefi_cf11.py` (`reemit_cefi_honest_absence_rows`, lines ~311-336) so a prior captured row is
   NOT treated as phantom purely because its stored `instrument_type`/`underlying` columns differ from the live path's
   encoding, when a matching object genuinely exists under the SAME (date, venue, data_type, instrument_id) ignoring
   `instrument_type`/`underlying` — mirroring the existing N1/F3-shadow suppression already used for blank-itype rows
   (`covered_keys_no_itype`, lines 270-272, 340-342), generalized to also ignore `underlying`. A worker taking this
   should NOT simply widen `_ITYPE_SYNONYMS` per-venue (that only chases one venue at a time and this spans ~9+ venues)
   — the shadow-suppression generalization is the systemic fix.
3. **Re-run** this same full-corpus `--dry-run` after the fix lands; `phantom_to_failed` should drop by roughly the 490K
   false-phantom volume, leaving a small DERIBIT-chain-style residual (true phantoms — a captured row genuinely missing
   its backing parquet, e.g. deleted/moved objects). Re-flip this issue + the plan todo once confirmed.
4. **(2026-07-28 update)** The re-run in the section above CONFIRMS step 3's fix landed correctly (490,639 → 50,615,
   `reemit_skipped_shadow=468,555` proves it's firing) but the gate is STILL not met — a SECOND, distinct root cause
   (instrument_id format drift, not itype/underlying drift) accounts for the residual. **The migration stays BLOCKED.**
   Do NOT flip `data_completion_cefi_2026_07_15.md`'s "NEXT SESSION — execute the migration" todo. See new todo 3 below.

## Todos

- [x] ✅ [DATA] P0. Generalize the CF-11 covered-keys shadow-suppression in
      `market-tick-data-service/market_tick_data_service/scripts/_rebuild_cefi_cf11.py`
      (`reemit_cefi_honest_absence_rows`) to also ignore `instrument_type`/`underlying` drift between the prior
      manifest's stored columns and the live object scan's parsed path — confirmed false-phantom repro: OKX-FUTURES
      `future`→`perpetual`, BYBIT-SPOT `spot_pair`→`perpetual` (itype drift), ASTER non-blank `underlying` column vs
      live path's blank `underlying` for a per-instrument shard (underlying drift). Add regression tests mirroring
      `test_wellformed_captured_no_object_still_phantom` (must still catch a TRUE phantom) alongside new tests for each
      drift case (must NOT phantom-demote when the object genuinely exists). (repo: market-tick-data-service) —
      market-tick-data-service@dcbed674
- [x] ✅ [DATA] P1. After the fix lands, re-run the full-corpus `rebuild_cefi_manifest --dry-run` (2019-01-01..present)
      and confirm `phantom_to_failed`'s new value + update this issue doc. **Re-run DONE and documented above (elapsed
      2089.6s, phantom_to_failed 490,639→50,615) — the fix is confirmed working, but the "drops to a small
      DERIBIT-chain-style residual" acceptance condition is NOT met** (DERIBIT is only 5.0% of the residual; a second,
      distinct instrument_id-format-drift root cause dominates — see the "Re-run confirmation" section above). Per the
      todo's own conditional wording, the migration-unblock action correctly did NOT happen — it stays gated on the new
      todo below, not on this one. (repo: market-tick-data-service) — issue doc updated this commit.
- [x] ✅ [DATA] P0. **Sequencing gate (2026-07-28, re-sequenced ahead of the normalizer todo below per main-agent
      review):** the DERIBIT-residual diagnosis in the "Re-run confirmation" section above was measured against
      market-tick-data-service@dcbed674 on LDR, which was MISSING a follow-up fix
      (`fix(cefi): gate CF-11 itype/underlying-drift shadow on non-blank instrument_id`, orig SHA `89112f89`) — that fix
      gates the itype/underlying-drift shadow-suppression (todo 1 above) on a non-blank `instrument_id`, closing a real
      over-suppression gap (a blank-iid bundled-chain row, e.g. DERIBIT `futures_chain`/`options_chain`, could
      cross-match a DIFFERENT underlying's chain cell on the same date/venue/data_type and get wrongly shadow-suppressed
      — exactly the DERIBIT-chain-style residual this issue's acceptance gate expects to still catch). Landed on LDR
      this commit: market-tick-data-service@42a2fd9f (cherry-picked from
      `origin/wip-preserve/orchestrator-slot-2-89112f89`, QG green, 40 CF-11 unit tests passing). **The instrument_id
      -format-normalizer todo below was designed/drafted BEFORE this gate landed and its premise (the residual's true
      root cause) is therefore unverified until the full-corpus dry-run is re-run on this gated code** — see the
      re-diagnosis note on that todo. (repo: market-tick-data-service) — market-tick-data-service@42a2fd9f
- [ ] [DATA] P0. Re-run the full-corpus `rebuild_cefi_manifest --dry-run` (2019-01-01..present) on the NOW-GATED code
      (market-tick-data-service@42a2fd9f, includes both the itype/underlying-drift shadow AND its non-blank-iid gate)
      and re-diagnose the residual `phantom_to_failed` per-venue breakdown. **This determines whether the
      instrument_id-format-normalizer todo below is still needed at all** — if the DERIBIT-chain-style residual now
      meets the acceptance gate on its own (the missing `89112f89` gate was the true root cause), the normalizer todo is
      MOOT: close it as not-needed, restore nothing from the stashed WIP, and unblock
      `data_completion_cefi_2026_07_15.md`'s migration todo directly from here. Only if a genuine instrument_id-FORMAT
      residual (OKX-SWAP raw-stem, BINANCE-FUTURES/COINBASE-FUTURES missing `@LIN`/`@INV`) still survives this gated
      re-run does the normalizer todo proceed — a stashed WIP normalizer implementation + 8 regression tests already
      exist (git stash on the slot-2 worktree, `_normalize_instrument_id_for_venue` in `_rebuild_cefi_cf11.py`,
      confirmed correct against all 3 live repros) and can be restored + finished quickly once re-validated against this
      gated re-run's actual residual. **Background this run via a properly harness-tracked bg task** (same orphan-reaper
      caveat as todo 4 below). (repo: market-tick-data-service)

      **🟡 2026-07-28 (slot-12) — triple-dispatch found, do NOT launch another copy of this re-run.** Landed here via
          `data_completion_cefi_2026_07_15.md`'s blocked todo (whose own note points to this issue doc as the real
          predecessor). On arrival, `ps aux` showed this EXACT full-corpus dry-run (same start/end dates, same gated
          `market-tick-data-service@42a2fd9f`) already running concurrently in **two** other slot worktrees: slot-2
          (`.tabs/2`, started 10:49, holds the stashed WIP normalizer referenced above — likely this todo's true owner) and
          slot-15 (`.tabs/15`, started 10:57, log explicitly named `rebuild_cefi_dryrun_42a2fd9f_run2.log`). I had already
          launched a third copy before checking; killed it immediately (PID 3023906, reached only `date=2023-07-22` of
          2019-01-01..2026-07-28, no output written) to avoid a third full-corpus GCS scan for identical work. **Whichever
          of slot-2/slot-15 finishes first should update this todo with the re-diagnosed per-venue breakdown** — do not
          dispatch a fourth run. If both stall or die without updating this doc within a few hours, the next session should
          check `ps aux` for a live `rebuild_cefi_manifest` process before re-launching, not just check this doc's checkbox
          state.

- [ ] [DATA] P0. Design + implement a venue-aware instrument_id-format normalizer for the CF-11 shadow-suppression in
      `market-tick-data-service/market_tick_data_service/scripts/_rebuild_cefi_cf11.py`
      (`_build_shadow_keys_ignoring_itype_and_underlying`, `reemit_cefi_honest_absence_rows` lines ~227-357) so a prior
      captured row is not treated as phantom purely because the prior manifest's `instrument_id` used an older/alternate
      fully-qualified format (`VENUE:TYPE:SYM@MARGIN`, e.g. `OKX-SWAP:PERPETUAL:LTC-USD@INV`) that differs from the
      CURRENT live GCS filename stem for the SAME physical object (`LTC-USD-SWAP`, `OMG-USDT` w/o `@LIN`, `FLOW-USD` w/o
      `@INV` — see confirmed repros in the "Re-run confirmation" section above). **GATED on the todo above** — only
      proceed if the gated re-run still shows a genuine instrument_id-format residual; a stashed WIP already implements
      this (see prior todo). **This is NOT a blanket ignore-instrument_id fix** (unlike itype/underlying, instrument_id
      is the only field disambiguating distinct instruments on the same date/venue/data_type — a naive
      `(day, venue, dtype)`-only shadow key would wrongly suppress TRUE phantoms too, which this codebase's own CF-11
      doc-comment calls "the WORSE error"). Needs: (a) enumerate the actual historical instrument_id formats per venue
      (git-blame/read the OLD manifest-writer's instrument_id derivation, plus the confirmed live cases: bare stem,
      stem-minus-margin-suffix, OKX-SWAP's `-SWAP`-suffix token), (b) a normalizer/synonym table (mirroring
      `_ITYPE_SYNONYMS`'s pattern) that strips/maps the prior iid to what the CURRENT scan would produce for the same
      instrument, verified NOT to collapse two distinct instruments into one key, (c) regression tests mirroring
      `test_wellformed_captured_no_object_still_phantom` (must still catch a TRUE phantom — e.g. two DIFFERENT symbols
      must never shadow each other) alongside new tests for each confirmed drift case (OKX-SWAP `-SWAP` token,
      BINANCE-FUTURES/COINBASE-FUTURES missing `@LIN`/`@INV`). Largest residual contributors to prioritize: OKX-SWAP
      (12,921), BINANCE-FUTURES (9,427), COINBASE-FUTURES (8,442), BYBIT (5,608), OKX-FUTURES (4,329). (repo:
      market-tick-data-service)
- [ ] [DATA] P1. After the todo above lands, re-run the full-corpus `rebuild_cefi_manifest --dry-run`
      (2019-01-01..present) a third time and confirm `phantom_to_failed` finally drops to a small DERIBIT-chain-style
      residual (DERIBIT-dominant, well-formed bundled `instrument_id=BTC`/`ETH`-style rows only); update this issue
      doc + unblock `data_completion_cefi_2026_07_15.md`'s "NEXT SESSION — execute the migration" todo. **When launching
      this re-run interactively: background it via a properly harness-tracked bg task (Bash `run_in_background: true`
      with NO manual `&`/`disown`/`setsid` inside the command) — the agent-orchestrator runs a per-slot orphan-process
      reaper that silently kills any manually-detached/reparented (PPID→1) background process at ~345s elapsed,
      confirmed via 2 failed attempts this session (kern.log: `orphan_reap sweep: slot 14 pid <N> age=34[25]s KILLED`);
      a plain harness-tracked background Bash call survives the full ~35min run.** (repo: market-tick-data-service)

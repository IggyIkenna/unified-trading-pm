---
doc_type: issue
title:
  Bug C's existence-window denominator collapses to a handful of buckets for OPTIONS/dated-FUTURES — `@`-suffix
  normalization strips real identity, not just a settlement tag
summary: >-
  Found while live-data-verifying Bug C's fix (mtds_data_status_page_parity_2026_07_21.md's "Verify Bug C's fix against
  live data" P1 todo). `per_instrument_coverage()`'s new per-instrument existence-window denominator
  (`deployment-api@89e31a0`, deployment_api/services/data_status/instrument_coverage.py) keys its
  `per_instrument_expected` dict by `_normalize_instrument_id_for_match(iid)`, which strips EVERYTHING after the first
  `@` in an instrument_id. That normalization was designed for the settlement/chain-suffix divergence case
  (`@LIN`/`@INV`/`@ETHEREUM` — a fixed, low-cardinality tag both catalogue and manifest carry). For CEFI OPTIONS and
  dated FUTURES, the `@`-suffix is NOT a fixed tag — it embeds the expiry date (+ strike + call/put for options), i.e.
  it IS the instrument's actual distinguishing identity beyond `VENUE:TYPE:UNDERLYING`. Stripping it collapses thousands
  of genuinely distinct instruments onto one dict key. Measured live against the real
  `instruments-store-cefi-prd-central-element-323112` catalogue (`prod/catalog.parquet`, 2026-07-22): DERIBIT OPTION
  264,550 raw instrument_ids normalize to only 4 distinct keys (66,137x collision); DERIBIT FUTURE 1,631 raw ids
  normalize to 12 keys (135.9x collision). Because the dict-comprehension's later entries silently overwrite earlier
  ones for a colliding key, this corrupts BOTH the fixed denominator (`instrument_windows` populated) AND — more
  seriously — the function's own "exact pre-fix-behavior parity when `instrument_windows=None`" guarantee (asserted by
  Bug C's shipped commit message + its own new unit tests): `instrument_windows=None` no longer reproduces
  `n_instruments * n_dates`, it reproduces `n_distinct_normalized_keys * n_dates`, silently under-counting by orders of
  magnitude for these instrument_types. Live-measured production consequence: `per_instrument_coverage(DERIBIT,
  options_chain)` today reports `completion_pct=100.0%` (`expected_shards=210`, clamped) despite only 10,172 real
  captured/empty_confirmed shards existing against a true universe of 264,550 options — a false "fully clean" signal
  that MASKS real coverage gaps, the mirror-image failure mode of the operator's original "0% shown when actually fine"
  complaint. Confirmed this is a pre-existing property of `_normalize_instrument_id_for_match` (predates Bug C, already
  affected `missing_instruments`/the `per_instrument` breakdown display), but Bug C's refactor is the first place it
  corrupts the actual `expected_shards`/`completion_pct` headline numbers rather than just a secondary display field.
  `is_per_instrument_shard_data_type` currently live+unseeded for DERIBIT `options_chain` and `futures_chain` (confirmed
  via the real manifest — F4's `expected_unattempted` seed-guard does NOT cover these two dt's for DERIBIT today), so
  this is an ACTIVE production code path, not dormant.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-api]
scope: [engineer]
tags: [data-correctness, mtds, honest-coverage, per-instrument, normalization, options, futures, regression, bug-c]
related: [../mtds_data_status_page_parity_2026_07_21.md]
created: "2026-07-22"
last_updated: "2026-07-22"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  side-discovery during mtds_data_status_page_parity_2026_07_21.md's "Verify Bug C's fix against live data" P1 todo — a
  dedicated read-only verification pass calling deployment-api's real per_instrument_coverage() against the live CEFI
  manifest + IS catalogue, 2026-07-22. Not caused by that verification task; a pre-existing property of
  _normalize_instrument_id_for_match newly exposed by Bug C's `89e31a0` refactor.
resolved_by:
---

# Bug C's existence-window fix has a real `@`-suffix normalization collision for OPTIONS/dated-FUTURES

## How this was found

Assigned task: verify `deployment-api@89e31a0` (Bug C, `mtds_data_status_page_parity_2026_07_21.md`) against real CEFI
manifest + IS catalogue data — read-only, no code changes intended. While selecting a clean repro venue/dt/ instrument,
found the mechanism works correctly and dramatically as designed for PERPETUAL/SPOT_PAIR instrument_types (see the
parent plan's todo flip for that clean before/after). While cross-checking a second candidate (DERIBIT `options_chain`,
chosen because it is genuinely NOT F4-seeded — i.e. actually exercises the derived `per_instrument_coverage` path in
production, unlike most CEFI trades/book_snapshot dt's which ARE seeded and bypass this function entirely today), the
numbers didn't match a flat cross-product OR a sane clipped total — investigation traced it to a dict-key collision in
`_normalize_instrument_id_for_match`.

## Root cause

`deployment_api/services/data_status/instrument_coverage.py:37-64`, `_normalize_instrument_id_for_match`:

```python
normalized = "".join(instrument_id.split()).upper()  # strip/collapse ALL whitespace
if "@" in normalized:
    normalized = normalized.split("@", 1)[0]
return normalized
```

Designed (per its own docstring) for the cross-service surface-divergence case: `@LIN`/`@INV`/`@ETHEREUM` settlement or
chain tags that both instruments-service's catalogue and MTDS's manifest carry inconsistently for the SAME instrument.
For PERPETUAL/SPOT_PAIR/COMBO instrument_ids this holds — the `@`-suffix (if present at all) is a static,
low-cardinality tag, not part of the instrument's distinguishing identity (measured: DERIBIT PERPETUAL 26 raw ids -> 26
normalized keys, ratio 1.00; BINANCE-FUTURES PERPETUAL 854 -> 854, ratio 1.00; COINBASE-FUTURES PERPETUAL+ SPOT_PAIR 277
-> 277, ratio 1.00).

For OPTIONS and dated FUTURES, the instrument_id format is `VENUE:TYPE:UNDERLYING@MARGIN-YYYYMMDD[-STRIKE-C|P]` — e.g.
`DERIBIT:OPTION:BTC-USD@INV-20190405-3250-C` / `DERIBIT:FUTURE:AVAX-USDC@LIN-20260401`. Everything after `@` here is NOT
a formatting-divergence tag — it's the expiry date (+ strike + side for options) that makes each instrument unique
within its underlying. Splitting on `@` and keeping only `[0]` collapses `DERIBIT:OPTION:BTC-USD@INV-...` for every
expiry/strike/side of every BTC option into the single key `DERIBIT:OPTION:BTC-USD`.

**Measured live** (`instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`, 2026-07-22):

| venue            | instrument_type     | raw unique ids | normalized unique keys | collision ratio |
| ---------------- | ------------------- | -------------: | ---------------------: | --------------: |
| DERIBIT          | OPTION              |        264,550 |                      4 |         66,137x |
| DERIBIT          | FUTURE              |          1,631 |                     12 |          135.9x |
| OKX-FUTURES      | FUTURE              |          5,604 |                    123 |           45.6x |
| DERIBIT          | PERPETUAL           |             26 |                     26 |    1.00x (safe) |
| DERIBIT          | COMBO               |         69,466 |                 69,466 |    1.00x (safe) |
| BINANCE-FUTURES  | PERPETUAL           |            854 |                    854 |    1.00x (safe) |
| COINBASE-FUTURES | PERPETUAL+SPOT_PAIR |            277 |                    277 |    1.00x (safe) |

Because `per_instrument_coverage`'s denominator build (`instrument_coverage.py:493-499`) is a Python dict comprehension
keyed by the normalized id, colliding entries silently overwrite each other (last-iterated wins, no error, no log) —
this is NOT limited to the new `instrument_windows`-populated (fixed) path. It ALSO fires when `instrument_windows=None`
(the fallback every pre-existing MTDS caller uses), because `_clip_dates_to_window` is called unconditionally regardless
of whether a window is supplied:

```python
per_instrument_expected: dict[str, frozenset[str]] = {
    _normalize_instrument_id_for_match(iid): _clip_dates_to_window(
        expected_dates, (instrument_windows or {}).get(iid)
    )
    for iid in expected_instruments
}
expected_count = sum(len(dates) for dates in per_instrument_expected.values()) * tf_multiplier
```

With `instrument_windows=None`, every `iid` maps to the SAME unclipped `expected_dates` value — so the collision is
invisible to a spot-check that only compares total row COUNT before vs after against a hand-computed
`n_instruments * n_dates` for a small, non-colliding sample (which is what Bug C's own new unit tests do — none of the 8
new tests use an OPTION or dated-FUTURE instrument_id). But `n_distinct_normalized_keys` is what actually drives
`expected_count`, not `len(expected_instruments)` — so for DERIBIT OPTION, `instrument_windows=None` now computes
`4 * n_dates`, not `264,550 * n_dates`. This directly contradicts the shipped commit's own documented claim ("exact
pre-fix-behavior parity when `instrument_windows=None` is not passed at all") for any instrument_type where the
normalization collides.

## Live-measured production consequence (2026-07-22, read-only)

Called the real `per_instrument_coverage()` against real DERIBIT `options_chain` data (`prod/catalog.parquet` for the
264,550-option universe + `_read_cefi_catalogue_metadata()` for the real windows + the real
`market-data-tick-cefi-prd-central-element-323112` manifest for `venue_df_ok`, real `mtds_expected_dates_for_venue_dt()`
for the 2,672-date calendar 2019-03-30..2026-07-22):

- `expected_shards=210` (should be a number reflecting ~264,550 options each clipped to their real ~5-10 day existence
  window — i.e. plausibly in the hundreds of thousands to low millions, not 210)
- `found_shards=10,172` (the real count of captured/empty_confirmed manifest shards)
- `completion_pct=100.0` (clamped — `found > expected` because the denominator is corrupted down to 4 keys × the clipped
  window sizes of whichever 4 instruments happened to be last-iterated per key)

**This is a live, currently-active false-clean signal**: DERIBIT options coverage is being reported as 100% complete
today when the true picture (264,550 real option instruments, only 10,172 real captured/confirmed shards) is nowhere
near complete. Confirmed `options_chain` and `futures_chain` are NOT F4-seeded for DERIBIT (no `expected_unattempted`
rows in the live manifest for these two dt's), so `per_instrument_coverage`'s derived branch — not the seeded 4-state
fallback — is the branch actually serving these numbers in production today.

## Blast radius

- Confirmed affected: DERIBIT `options_chain` (264,550 instruments), DERIBIT `futures_chain` (1,631), OKX-FUTURES
  `futures_chain`/other dated-FUTURE dt's (5,604) — any CEFI venue/dt combination whose `instruments_provider`- resolved
  universe includes OPTION or dated-FUTURE instrument_ids AND is not F4-seeded.
- NOT affected: PERPETUAL/SPOT_PAIR/COMBO-only venues (measured collision-free) — this is the majority of MTDS's
  documented use case (the module's own docstring cites BINANCE-FUTURES's 50-perp board as the canonical example), which
  is presumably why this wasn't caught by the 8 new unit tests, none of which used an OPTION/dated-FUTURE id.
- Direction of error is "hides gaps" (false 100%/near-100% completion), not "shows phantom gaps" — the OPPOSITE
  direction from the original Bug C symptom (0% shown when actually clean). Both are real, live, and distinct.

## Recommended fix (not attempted here — out of this verification task's scope, real design work)

`_normalize_instrument_id_for_match` needs to stop blanket-stripping everything after `@` for instrument_types whose
`@`-suffix carries real distinguishing content (OPTION, dated FUTURE). Two directions, needs an owner to pick:

- (a) Only strip a KNOWN, enumerated set of pure settlement/chain tags (`@LIN`, `@INV`, `@ETHEREUM`, ...) via an exact
  suffix match, not "everything after the first `@`" — instruments whose `@`-content doesn't match a known tag keep
  their full raw id for normalization purposes.
- (b) Make the normalization instrument_type-aware: only apply `@`-stripping for instrument_types confirmed
  suffix-divergent (PERPETUAL/SPOT_PAIR today), pass through raw (uppercased/whitespace-collapsed only) ids for
  OPTION/FUTURE.

Either way needs new unit tests using real OPTION/dated-FUTURE ids (the current 8 don't), and a targeted live
re-verification of DERIBIT `options_chain`/`futures_chain` completion_pct before/after to confirm the false-100% signal
clears.

## Todos

- [ ] [BACKEND] P1. Fix `_normalize_instrument_id_for_match` so OPTION/dated-FUTURE instrument_ids don't collide
      (direction (a) or (b) above) — re-verify DERIBIT `options_chain` completion_pct moves off the false 100.0% clamp
      against real data.
- [ ] [BACKEND] P2. Add unit test coverage for `per_instrument_coverage`/`_normalize_instrument_id_for_match` using at
      least one real OPTION and one real dated-FUTURE instrument_id shape — the 8 tests added in `89e31a0` all use
      PERPETUAL/SPOT-shaped ids, which is why this collision wasn't caught pre-ship.
- [ ] [REVIEW] P2. Audit other `_normalize_instrument_id_for_match` call sites (`missing_instruments`,
      `normalized_iid_counts`, the `per_instrument` breakdown block) for the same collision on OPTION/dated-FUTURE
      venues — this issue only traced the `expected_shards`/`completion_pct` headline numbers Bug C's fix touches; the
      pre-existing display-only call sites may already have a milder version of the same problem.

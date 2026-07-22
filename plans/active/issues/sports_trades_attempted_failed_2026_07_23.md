---
doc_type: issue
title:
  "sports/trades DP_RUN_MOSTLY_EMPTY (2026-07-22 23:46-48Z, 58,016/66,545 = 87.2%) — NOT a new venue outage or a
  mislabeled axis; the exact same dead 2026-07-13-frozen BETFAIR/MATCHBOOK/PINNACLE residue already diagnosed
  2026-07-15, with its ratio spiked by TODAY's own K1/K2 canonical-casing manifest-swap relocating the surviving
  `captured` rows out of the literal lowercase `data_type=trades` string this alert measures"
summary: >-
  Investigated a `#data-pipeline-alerts` `DP_RUN_MOSTLY_EMPTY` CRITICAL alert (window 2026-07-22 23:46-48Z) against
  `market-data-tick-sports-prd-central-element-323112`, `sports/trades`: 58,016/66,545 attempted_failed (87.2%).
  Live-queried the manifest index directly (single-file read, 1,830,258 rows, not a corpus walk) and the count
  reproduces the alert EXACTLY. Two things checked per this task's brief: (1) is `trades` even a real sports data_type,
  or a wrong-axis/mislabeled value? UAC `market_data_categories.py:223` registers it deliberately — "Matched bets /
  trade-level acceptance events (aligned with CeFi/prediction)" — a real, intentional axis (the order-matched-fill side
  of a betting exchange, distinct from `odds`, the quote/orderbook side). NOT mislabeled. (2) Is this a fresh/live
  regression? No. 100% of the 58,016 rows share `pipeline_mode=batch_api_football`, 100% `venue` in `{BETFAIR,
  MATCHBOOK, PINNACLE}`, and — critically — 100% share `attempted_at` inside the IDENTICAL 2026-07-13T23:56:41-48Z
  8-second window already root-caused in `sports_trades_venue_fetch_failed_2026_07_15.md`: a
  `rebuild_sports_manifest_v9.py` E4 re-emit pass silently re-stamped years-old dead rows (originals span
  2020-08-24..2026-05-31) with the REBUILD's own runtime instead of preserving their true `attempted_at` (a genuine bug,
  code-fixed 2026-07-15 `market-tick-data-service@6fad6565` to prevent recurrence; the ALREADY-corrupted rows'
  timestamps were explicitly left un-restored as a deferred follow-up, still open). What's NEW today is only the RATIO:
  87.2% vs the 07-15 investigation's 21.5% (112,277/522,276), even though the raw attempted_failed count roughly HALVED
  (112,277 -> 58,016). Root cause of the ratio spike: the SAME session's
  `plans/active/sports_master_closeout_2026_07_21.md` ran a K1/K2 canonical-casing manifest-swap (`--confirm-prod-write`
  EXECUTE, ~2026-07-22T19:45Z, hours before this alert) plus a phantom-row prune against this EXACT
  `(instrument_type=odds, data_type=trades)` axis, relocating the vast majority of genuinely-successful `captured` rows
  out of the literal lowercase `data_type=="trades"` string this alert's denominator measures (live `captured` for this
  string collapsed from 409,999 on 07-15 to just 8,529 today) while the frozen dead-residue `attempted_failed`
  population (unaffected by the casing relocation; partly thinned by the unrelated phantom-prune) mostly survived —
  shrinking the denominator far faster than the numerator and swinging the ratio up. Not a new incident; a metric
  artifact of routine, already-tracked manifest-canonicalization work landing on top of an already-open,
  already-deferred stale-residue cell.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    sports,
    trades,
    odds,
    dp_run_mostly_empty,
    data-pipeline-alerts,
    manifest,
    attempted-at,
    v9-rebuild,
    canonical-casing,
    k1-k2-migration,
    venue-fetch-failed,
    honest-coverage,
  ]
related:
  [
    sports_trades_venue_fetch_failed_2026_07_15.md,
    ../sports_master_closeout_2026_07_21.md,
    ../sports_consolidated_closeout_2026_07_19.md,
    ../data_pipeline_alerts_batch_remediation_2026_07_15.md,
    ../../archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    ../../../codex/02-data/sports-2020-06-data-floor.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-23
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
locked_by:
locked_since:
resolved_by:
source: >-
  operator-reported #data-pipeline-alerts DP_RUN_MOSTLY_EMPTY CRITICAL alert, window 2026-07-22 23:46-48Z, triaged
  2026-07-23 (read-only investigation, no changes made).
---

# sports/trades DP_RUN_MOSTLY_EMPTY — dead 2026-07-13 residue, ratio inflated by today's own K1/K2 casing migration

## Ground truth (live-queried 2026-07-23)

Downloaded `gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet` directly (a
single 42 MiB targeted read of the already-consolidated index — NOT a corpus walk; 1,830,258 total rows). Filtered to
`data_type == "trades"` (1,287,618 rows):

```
capture_status
empty_confirmed     1,221,073
attempted_failed        58,016
captured                  8,529
```

`captured + attempted_failed = 66,545`, `attempted_failed / 66,545 = 87.18%` — **reproduces the alert's 58,016/66,545
(87.2%) exactly.**

## Finding 1 — `trades` is a real, intentional sports data_type, NOT a mislabeled axis

Per this task's brief, checked whether "trades" for a sports asset_group might be a wrong-axis/mislabeled value (sports
data is normally odds/H2H, not "trades"). It is not: UAC `unified_api_contracts/registry/market_data_categories.py` line
223 registers `"trades"` for sports explicitly with the comment _"Matched bets / trade-level acceptance events (aligned
with CeFi/prediction)"_ — the order-matched-fill side of a betting-exchange feed (Betfair/Matchbook/Pinnacle are all
real betting exchanges where a "trade" = an actual matched bet), distinct from `"odds"` (the quote/orderbook side). This
is deliberate, cross-asset-group-consistent modeling (mirrors CeFi/prediction's own `trades` data_type), not a
copy-paste error or a wrong axis.

## Finding 2 — this IS the already-diagnosed 2026-07-13-frozen residue, not a fresh outage

`attempted_failed` breakdown for `data_type=trades` (all 58,016 rows are `pipeline_mode=batch_api_football` — the
api-football odds/exchange ingestion pipeline, NOT the canonical `batch_odds_api` axis):

| venue     | attempted_failed rows |
| --------- | --------------------: |
| BETFAIR   |                37,426 |
| MATCHBOOK |                11,352 |
| PINNACLE  |                 9,238 |

`error_reason`: **49,202** rows carry the literal string `VENUE_FETCH_FAILED`; the remaining **8,814** rows carry the
`EmptyFromLiveInstrumentError`-guard message
(`record_empty(reason=SOURCE_RETURNED_ZERO) rejected: ... catalog says 'trades' was ALIVE on <VENUE>/<DATE> ... Use record_failed(EmptyFromLiveInstrumentError(...)) instead`),
spread across hundreds of distinct historical dates (e.g. `BETFAIR/2022-02-26`, `BETFAIR/2024-01-13`,
`BETFAIR/2026-01-31`, ...). **Every single one of the 58,016 rows shares `attempted_at` inside the exact
`2026-07-13T23:56:41.328635Z` – `2026-07-13T23:56:48.805133Z`** window — an 8-second burst, not independent live fetch
attempts.

This is the **identical fingerprint** already fully root-caused in `sports_trades_venue_fetch_failed_2026_07_15.md`
(status: open, priority P2, resolved_by lists the code fix only): on 2026-07-15 that investigation found 112,277 rows in
this same 8-second window (94,127 `VENUE_FETCH_FAILED` + 18,150 `EmptyFromLiveInstrumentError`-guard) and proved via
`git log -S` that `VENUE_FETCH_FAILED` is DEAD classification vocabulary — removed from live sentinel code 2026-06-28
(`market-tick-data-service@b989284c` decomposed it into `UNCLASSIFIED:{code}`), so no row written by current code can
carry that string. The actual mechanism: `rebuild_sports_manifest_v9.py`'s 2026-07-13 E4 apply-pass
(`_rebuild_sports_write.py::_write_attempted_failed_rows`) re-emits PRE-EXISTING historical rows (true original dates
span 2020-08-24..2026-05-31) via `record_failed()`/`record_empty()` **without an explicit `attempted_at=`**, so UTL's
`ManifestWriter` defaulted it to the rebuild's OWN runtime — silently overwriting the real last-attempt timestamp and
making years-old, already-known failures look like the freshest cell in the whole alert batch. **Code fix shipped
2026-07-15** (`market-tick-data-service@6fad6565`, adds `_attempted_at_from_row()` and wires it into all 3 re-emit call
sites) — prevents recurrence going forward, but explicitly does **not** retroactively fix the already-corrupted rows;
that historical-`attempted_at` restore was investigated further (2026-07-20 addendum: the naive soft-delete restore plan
was abandoned after discovering the target generation was itself already clobbered by 3 later rebuild passes, and a
clean, un-clobbered copy of the true values survives in
`_index/snapshots/pre_migration_v9_2026-07-12_availability_index.parquet` with no deadline) — **still open, not yet
executed.**

That same doc's Part B also confirmed (re-derived against the live `is_bookmaker_league_covered()` oracle) that **100%
of these rows are genuinely-covered (bookmaker, league) pairs** — not a coverage-scope gap, but historical fixtures that
genuinely need a real re-fetch to determine whether the underlying data is recoverable. So there IS a real underlying
data question here (can BETFAIR/MATCHBOOK/PINNACLE historical trade data for these ~1,579 dates actually be recovered),
but it is the SAME open question already on record since 2026-07-15, not a new finding.

## Finding 3 — why the RATIO spiked (21.5% -> 87.2%) even though the raw count roughly HALVED (112,277 -> 58,016)

This is the genuinely new piece of this investigation. Two numbers moved in the same direction but by very different
amounts:

- `attempted_failed`: 112,277 (07-15) -> 58,016 (today) — **-48%**.
- `captured` (same literal lowercase `data_type=="trades"` string): 409,999 (07-15) -> 8,529 (today) — **-98%**.
- Denominator (`captured+attempted_failed`): 522,276 -> 66,545 — **-87%**, which is why the ratio rose even though the
  failure count fell.

The `captured` collapse is explained directly by work in the SAME session, on the SAME asset_group, on the SAME
`(instrument_type=odds, data_type=trades)` axis, executed **hours before** this alert fired (per
`plans/active/sports_master_closeout_2026_07_21.md`'s own Progress Log, "2026-07-22 fifth/sixth wave"):

1. **Phantom `soccer_*` prune** (`prune_phantom_soccer_manifest_rows_2026_07_22.py`, executed ~19:12Z): removed 6,110
   rows matching `league_id startswith soccer_` AND `data_type=trades` AND `instrument_type=odds` AND no `fixture_id` —
   verified genuinely phantom (0 still-live in GCS) before removal.
2. **K1/K2 canonical-casing manifest-swap** (`--confirm-prod-write` EXECUTE, ~19:45Z): this is the K1/K2 casing
   relocation for exactly the `instrument_type=odds/data_type=trades` (lowercase) -> canonical-cased axis (per
   `market_data_categories.py`'s own comment: _"odds writer never had its `instrument_type=odds/data_type=trades` casing
   fixed... Location:
   gs://market-data-tick-sports-prd-{pid}/raw_tick_data/.../instrument_type=odds/data_type=trades/..."_). REMOVE dropped
   320,469 rows / ADD wrote 373,296 canonical-keyed rows against the live index (base 1,777,431 -> 1,830,258 after) —
   i.e. a large fraction of the population previously readable under the literal lowercase `data_type=="trades"` string
   (including real `captured` rows) was RELOCATED to its canonical-cased identity by this swap.

Live-queried today's `captured` rows for `data_type=="trades"` fell to 8,529 — consistent with the great majority of
real successful captures having moved out of this exact string as a direct, intended effect of the K1/K2 swap. The
frozen `attempted_failed` residue from Finding 2 is dead terminal data (not part of what K1/K2 relocates — it isn't a
live capture output), so it wasn't relocated the same way; it shrank only via the unrelated phantom-prune's partial
overlap (soccer_*/no-fixture-id rows). Net effect: the SAME already-known dead-residue population, now measured against
a MUCH smaller surviving denominator, produces a dramatically higher ratio. **This is a metric artifact of routine,
already-tracked, correctly-executed manifest-canonicalization work — not a new venue outage, not a growing failure
population, and not evidence anything broke.**

## Verdict

- `trades` is a real, intentional sports data_type (Finding 1) — not filed as a mislabeled-axis issue.
- The underlying `attempted_failed` population is the SAME dead, 2026-07-13-frozen residue already open and tracked
  since 2026-07-15 (Finding 2) — no new investigation needed on that half; it is exactly as resolved/unresolved as the
  linked doc already states (code fix shipped, historical `attempted_at` restore + the covered-but-unrecovered
  BETFAIR/MATCHBOOK/PINNACLE re-fetch question both still open).
- Today's alert fired because a same-day, unrelated, already-planned manifest-canonicalization pass (K1/K2 casing
  migration + phantom prune, both already tracked to completion in `sports_master_closeout_2026_07_21.md`) shrank the
  denominator this specific alert measures, inflating the ratio well past the alert threshold on a cell that was already
  known-broken at a lower ratio (Finding 3). **Filed P2**: real underlying question exists (can the
  BETFAIR/MATCHBOOK/PINNACLE historical data be recovered) but it is not new, not urgent beyond its existing P2, and
  today's specific alert firing does not indicate a fresh regression.

## Todos

- [ ] [DATA] P2. Execute the still-open historical `attempted_at` restore for the sports/trades dead residue, now
      unblocked and low-risk per `sports_trades_venue_fetch_failed_2026_07_15.md`'s 2026-07-20 correction (the true
      values survive in a plain, non-soft-deleted snapshot,
      `_index/snapshots/pre_migration_v9_2026-07-12_availability_index.parquet`, no deadline, no risky live restore
      needed) — restoring the true dates would make this cell stop looking like the freshest failure in every future
      alert batch. Repo: `market-tick-data-service`.
- [ ] [DESIGN] P3. Flag to whoever owns `check_high_attempted_failed` (deployment-service): a same-day manifest
      canonicalization swap that relocates `captured` rows to a new casing/key can inflate an UNRELATED still-open
      cell's `DP_RUN_MOSTLY_EMPTY` ratio purely as a denominator side-effect. Not urgent (the underlying cell being
      dead/already-tracked means no action was actually needed here), but worth a one-line runbook note so a future
      on-call doesn't re-diagnose this from scratch. Repo: `deployment-service`.
- [ ] [VERIFY] P3. Once `sports_master_closeout_2026_07_21.md`'s K1/K2 work is fully flipped to done and the DELETE of
      old non-canonical objects eventually executes (operator-gated), re-check this cell's ratio settles back down as
      expected once the legacy lowercase `data_type=="trades"` population's dead-residue rows are themselves
      migrated/purged rather than left as an orphaned denominator-shrunk remnant.

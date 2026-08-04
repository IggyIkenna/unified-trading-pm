---
doc_type: issue
title:
  TradFi FX manifest instrument_id backfill (tradfi_fx_provenance_and_manifest_id_defects-002) — 1,983 of 3,795 affected
  rows blocked by TWO newly-discovered defect classes, not the id-blankness itself
summary: >-
  Executing the operator-confirmed FX SPOT_PAIR manifest instrument_id historical backfill
  (issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md todo, "execute now, no further sign-off needed"), a
  content-verified (GCS-read-per-shard, never guessed) restamp script found the live census has moved since the
  2026-07-26 snapshot (bare-pair shape already self-healed to 0 via ordinary daily-cron operation) and, of the remaining
  3,795 captured-but-non-canonical FX rows, only 25 are safely restampable. The other 3,770 split into: (1) 1,812 rows
  with NO backing GCS object at all under any known path/pipeline_mode shape (a phantom-capture defect, same class as
  the sibling tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md finding but a DIFFERENT
  batch/writer/signature — FX/ohlcv_24h/market-tick-data-service, written_at clustered 2026-07-16/2026-07-18, not MDPS's
  2026-07-27 CME/ohlcv_1m batch); (2) 1,958 rows that would collide post-restamp with another row for the SAME shard-day
  (up to 4 redundant manifest bookkeeping rows per date, spanning both pipeline_mode values and both blank/SPOT_PAIR
  instrument_type variants — a duplicate-manifest-row defect, not an id-labeling one). Neither can be resolved by an
  instrument_id-only repair; both need their own scoped investigation/decision. The 25 safe rows were applied (see
  Progress Log for the SHA/verification).
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags:
  [tradfi, fx, data-correctness, manifest, phantom-rows, duplicate-rows, instrument-id, capture-status, reconciliation]
related:
  [
    /plans/archive/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /plans/active/issues/tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md,
    /plans/archive/issues/tradfi_fx_phantom_row_premise_contradicted_2026_08_04.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-03
last_updated: 2026-08-04
parent_epic: tradfi_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by: market-tick-data-service@c86016f6
locked_by:
locked_since:
supersedes:
superseded_by:
source: "Found while executing tradfi_fx_provenance_and_manifest_id_defects-002, 2026-08-03, slot 8."
context_scope:
  [
    /plans/archive/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/scripts/restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py,
  ]
---

# TradFi FX manifest: phantom-captured rows + duplicate bookkeeping rows block full instrument_id coverage

## What I found

Building `restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py` (manifest-only, content-verified re-stamp — see the
parent issue doc's operator-confirmed 6-step plan), a live dry-run against
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (2026-08-03) found:

**The live census has moved since the parent doc's 2026-07-26 snapshot.** `bare-pair` (`XXX-YYY`, no prefix) rows are
now **0** (was 501) and well-formed `FX:SPOT_PAIR:...` rows are now **562** (was 13) — the ordinary daily forward-poll
cron, re-running its rolling recent-day window under the already-shipped write-path fix
(`market-tick-data-service@020b703e`, 2026-07-25), naturally superseded every 2026-dated bare-pair row with a
correctly-stamped capture. No agent action was needed for that shape. The genuinely remaining population is exactly **2
shapes, 3,795 rows**: blank `instrument_id` (2,812) + literal `"ticks"` (983), both scoped to `capture_status=captured`,
`venue=FX`, `data_type=ohlcv_24h`.

**Every affected row's date is `< 2026-06-26`** —
`unified_api_contracts.registry.tradfi_instrument_universe .FX_SPOT_PAIRS` states the G10 majors were added exactly
`2026-06-26`; before that the registry held only `KRW-USD`. So the collision mechanism in `PartitionedTickWriter`'s
symbol-less `ticks.parquet` fallback (no per-pair path segment for non-derivative tradfi shards — every pair on the same
day would physically collide at one object path) was structurally present but **never actually triggered for FX**: there
was never more than one pair fetched per day in the affected window. No real FX market data was lost to this mechanism.

### Defect 1 — 1,812 rows with NO backing GCS object at all (a phantom-capture, not a mislabel)

All 1,812 are the `blank instrument_id` shape (never the `"ticks"` shape — every `"ticks"`-shaped row DID resolve to a
real object). `row_count` is `NaN` for all of them (the `"ticks"`-shaped rows carry `row_count=0.0` instead — a
different signature). Checked directly: `gs://.../raw_tick_data/by_date/day=2020-01-16/` (one sampled affected date)
lists 191 real objects that day, **zero of which are under `venue=FX`** — confirmed absent, not a path-template miss on
this script's part (tried both known path shapes × both known `pipeline_mode` values, 4 candidates per date, none exist
for any of the 1,812).

`instrument_count` for these rows clusters heavily on two exact values (`5820.0` and small integers `1`/`2`) across MANY
unrelated dates, and `written_at` clusters on just 3 distinct timestamps across all 1,812 rows
(`2026-07-16T07:04:10.308211Z` — 804 rows, `2026-07-18T15:04:25.190281Z` — 1,980 rows [across both shapes, un-scoped to
just the 1,812], `2026-04-06T08:43:54.282523Z` — 16 rows, + a handful of singletons around `2026-05-05`) — a small
number of bulk-seed/backfill write batches stamping `capture_status=captured` across MANY historical dates at once, not
organic per-day capture traffic. `service_name` is 97.9% `market-tick-data-service`, with 13 `instruments-service` and
12 `market-data-processing-service` rows also present in the broader blank-id population.

**This is the SAME general defect class as `tradfi_bare_instrument_type_phantom_manifest_rows_2026_08_03.md`'s finding
(a `capture_status=captured` manifest row with zero backing GCS data) but a DIFFERENT batch/writer/signature** — that
doc's population is `instrument_type∈{UD,OPTION,FUTURE,COMBO,EQUITY,ETF,INDEX}`, `venue∈{CME,ICE,NASDAQ,NYSE,CBOE}` (no
FX), written in a single ~9-second window on `2026-07-27T16:46:31-40Z` by `market-data-processing-service`/`databento`.
This FX population is `venue=FX` only, spans 3 different bulk-write timestamps on 2026-04-06/07-16/07-18, and is
`service_name=market-tick-data-service` (mostly) — a separate incident, not a mislabeled/duplicate report of the same
one. Root cause NOT investigated this pass (out of scope — this todo is an instrument_id repair, not a
capture_status/phantom-row investigation).

### Defect 2 — 1,958 rows that would collide post-restamp with a redundant row for the same shard-day

`resolve_pair_for_shard` successfully resolved a real pair (content-verified via the shard's actual GCS object) for
1,983 of the 3,795 affected rows, but the collision-safe classifier (mirroring
`restamp_lending_instrument_type_2026_07_24.py`'s pattern, checked against the FULL `venue=FX` population, not just the
affected subset) found 1,958 of those would land on an IDENTICAL manifest key
(`date`+`venue`+`data_type`+`service_name`+`instrument_type`+`instrument_id`, post-normalization) as another existing
row for that same date. **Only 15 of 664 affected dates already have an existing well-formed twin** — the other 649
dates' collisions are entirely BETWEEN the affected candidates themselves. A representative date (`2020-01-24`) has
exactly 4 manifest rows for the one real KRW-USD capture that day:

```
instrument_type=''        blank id   pipeline_mode=batch_yahoo      instrument_count=5820.0
instrument_type=SPOT_PAIR blank id   pipeline_mode=batch_yahoo      instrument_count=1.0
instrument_type=SPOT_PAIR 'ticks'    pipeline_mode=batch_databento  instrument_count=0.0
instrument_type=None      'ticks'    pipeline_mode=batch_databento  instrument_count=0.0
```

All 4 represent the SAME real shard (one KRW-USD bar for that day) tracked under 2 `pipeline_mode` values × 2
`instrument_type`-blankness variants — redundant bookkeeping, not 4 real captures. Restamping all 4 to their "correct"
id would legitimately make them identical rows (not a bug in the restamp — a pre-existing duplication the restamp would
just make visible/exact). **1,958 rows / 664 distinct dates ≈ 2.9 redundant rows per affected date.** This is a
manifest-hygiene defect (duplicate/redundant capture bookkeeping across pipeline_mode/instrument_type-blank variants for
the same shard), separate from the instrument_id-blankness defect this todo targets, and needs its own design decision
(which row is canonical per shard-day? merge, or delete the redundant ones — delete-safety protocol applies since
`capture_status=captured` rows would be removed).

## Why it matters

The parent issue doc's todo mandated "verify ... a post-apply `FX:SPOT_PAIR:` prefix on 100% of FX captured rows" — that
outcome is **not achievable via an instrument_id-only manifest repair**. 100% coverage depends on two separate, unscoped
defects (phantom captures with no real data to attribute an id to; duplicate rows that need a merge/dedup decision)
being resolved first. This is a genuine scope-invalidating finding for that todo's stated Done-when criteria, not a
partial-fix shortcut — flagging per the workspace's "audit's issues are fixed in FULL, no partial deferral" rule: the
FULL fix for Finding 2 now spans 3 scoped pieces of work (this todo's 25-row mechanical piece, done; + the 2 below).

## Root-cause diagnosis (2026-08-03, slot 5)

**Provenance correlation (live re-query, not the doc's original snapshot)**: a bounded, column-pruned read of
`_index/availability_index.parquet` filtered to `venue=FX`, `data_type=ohlcv_24h`, `capture_status=captured`,
`instrument_id==""` (confirmed live: "blank" is stored as an empty string, not a parquet NULL — an `is_null()` filter
silently returns 0 rows) returns **2,787 rows** (2,812 minus the 25 already restamped by this doc's own parent todo —
exact match). **100%** of these 2,787 rows share `service_name=market-tick-data-service`, `source=yahoo`,
`pipeline_mode=batch_yahoo`, `row_count=None` — a cleaner, more precise result than the sibling doc's 97.9% figure (that
population mixed in some non-FX rows). They split into exactly the 3 documented `written_at` clusters, and inside each
cluster EVERY row shares the identical microsecond-precision timestamp (not just a tight window — a literal single
shared value): batch 1 (804 rows, `2026-07-16T07:04:10.308211Z`, `instrument_type=''`), batch 2 (1,967 rows,
`2026-07-18T15:04:25.190281Z`, `instrument_type='SPOT_PAIR'`), batch 3 (16 rows, `2026-04-06T08:43:54.282523Z`,
`instrument_type=''`). No rows exist outside these 3 windows — the 3-timestamp characterization is exhaustive.
Independently re-verified GCS-absence (not just trusting the parent doc) at 2 sample dates via direct `list_blobs()`:
`raw_tick_data/by_date/day=2020-01-01/pipeline_mode=batch_yahoo/asset_group=tradfi/venue=FX/` and
`.../day=2022-12-09/.../venue=FX/` both return **0 objects**, while the identical path shape at a real KRW-USD-backed
date (`day=2020-04-24`) returns 1 real object — confirms the path template is correct and these dates are genuinely
phantom, not a path-miss on this investigation's part. Script:
`market-tick-data-service/scripts/investigate_fx_phantom_manifest_rows_provenance_2026_08_03.py`.

**Writer MECHANISM confirmed (code-level, not just provenance-column inference)** — a genuinely different signature from
the sibling MDPS finding (that one was a per-row write loop, distinct `written_at` per row; this one shares ONE
timestamp across hundreds/thousands of rows, pointing to a single bulk-write call rather than a loop):

`market-tick-data-service/scripts/rebuild_mtds_manifest.py`'s `--from-canonical` mode (a **permanent**, still-live
production maintenance tool, not a one-off migration script) calls
`unified_trading_library.manifest_writer._maintenance.rebuild_manifest_from_canonical_paths()` (pre-2026-07-27) or its
07-27 additive replacement `merge_manifest_from_canonical_paths()` (post-`market-tick-data-service@de0ed32f`,
`"fix(mtds): route rebuild_mtds_manifest.py --from-canonical through the safe additive merge helper"`) — **both share
the identical bug**, confirmed by direct read of
`unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py`:

1. Each function computes `now_iso = datetime.now(UTC).isoformat()` **once**, OUTSIDE the per-shard loop (lines 620 and
   831 respectively), then stamps every discovered row's `"written_at": now_iso` inside the loop (lines 642, 851) — this
   is exactly the "one shared timestamp across a whole batch" signature observed, as opposed to a per-row
   `record_captured()` call which would naturally produce distinct timestamps.
2. Both functions **hardcode `"instrument_id": ""`** in the row dict (lines 639, 848) — there is no `instrument_id`
   derivation anywhere in either function. The row-key grain these helpers reconstruct is
   `(date, venue, chain, instrument_type, data_type)` — genuinely correct for an aggregated/candle-shard rebuild, but FX
   is a **per-instrument-pair** venue (each real object embeds the pair in the filename stem, e.g.
   `FX:SPOT_PAIR:KRW-USD.parquet`) — confirmed by reading the path-parsing regexes directly
   (`day_pat`/`venue_pat`/`chain_pat`/`itype_pat`/`dtype_pat` in `_maintenance.py:547-551`): none of them capture the
   filename stem at all, so the per-pair id is silently dropped during rebuild. This is the SAME blind-spot class as the
   already-tracked `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` finding (a different oracle, same
   "path-structure readers ignore the filename stem where tradfi/FX encodes the real id" root defect shape) — worth
   flagging as a recurring pattern, not a one-off coincidence.
3. Neither record sets `row_count`/`capture_status`/`pipeline_mode`/`source` — `row_count` therefore reads back as
   `None` (matches observed), and `capture_status=captured` is a **read-time coercion**, not a write-time claim:
   `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:451-464` (`_backfill()`) — "Legacy
   rows (no `capture_status` column) are coerced to `CAPTURED`: under pre-v5 schemas, presence of a row implied a
   successful capture" — directly confirmed by reading this function. This is the exact mechanism that turns these thin
   rebuild-placeholder rows into false `capture_status=captured` phantoms downstream.
4. **Not fully traced** (same honest-boundary pattern as the sibling doc): exactly how `pipeline_mode=batch_yahoo` /
   `source=yahoo` get attached to these rows — neither `_maintenance.py` function sets those fields, so they likely come
   from a downstream consolidator-side derive/backfill keyed on `venue=FX`, not from the rebuild call itself. Not pinned
   to an exact line this pass.
5. **Batch 3's date (2026-04-06) predates `rebuild_manifest_from_canonical_paths`'s earliest confirmed appearance** in
   UTL git history (`8249dfa5`, 2026-04-18) by ~12 days — most likely an earlier/local predecessor rebuild with the same
   bug pattern (not pinned to an exact commit). Batches 1/2's `instrument_type` split (`''` vs `'SPOT_PAIR'`) matches
   FX's legacy pre-hive path shape (no `instrument_type=` segment) vs the later canonical hive-path shape, consistent
   with two separate rebuild runs against the corpus at different points in its own path-migration history.

**Verdict**: a genuine, still-live **writer-mechanism bug** in a permanent production tool, not a deliberate seed script
and not "this venue/data_type should never have been captured" — `rebuild_mtds_manifest.py --from-canonical` will
reproduce this exact phantom-row shape again on any future run against FX (or any other per-instrument-grain tradfi
venue) until the underlying UTL helper is fixed to actually recover the per-instrument id from the filename stem (or
refuses to emit a blank-id row for a venue it can't resolve, rather than silently emitting one). Recommending BOTH a fix
(prevent recurrence, todo below) and a quarantine/cleanup of the 1,812 existing rows (todo below) — same
disjoint-defect-classes reasoning the parent doc already applied to Defect 1 vs Defect 2, and matching the "quarantine

- fix code" combination the sibling MDPS finding's own todos 2+3 landed.

## Recommended next steps

- [x] ✅ [DATA] P2. **ROOT-CAUSED 2026-08-03 (slot 5)** — writer mechanism confirmed:
      `rebuild_mtds_manifest.py     --from-canonical`'s UTL helpers
      (`rebuild_manifest_from_canonical_paths`/`merge_manifest_from_canonical_paths` in
      `unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py`) hardcode a blank
      `instrument_id` and stamp one shared `written_at` per rebuild run, structurally unable to recover FX's
      per-instrument-pair filename-stem id. Full diagnosis in § "Root-cause diagnosis" above; exact upstream trigger for
      `source=yahoo`/`pipeline_mode=batch_yahoo` not fully traced (honest boundary, see caveat 4 above).
      market-tick-data-service@84abe868 (investigation script; no writer-code change this todo — see the 2 follow-up
      todos below).
- [x] ✅ [DATA] P2. **Fix the underlying writer bug** — `rebuild_manifest_from_canonical_paths()` /
      `merge_manifest_from_canonical_paths()` in
      `unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py` no longer silently hardcode
      `instrument_id=""` for a per-instrument-grain venue's canonical-path rebuild. Implemented option (a): both writer
      lanes that feed a candle/tick rebuild (MTDS `PartitionedTickWriter`, MDPS's `candle_leaf_filename`) already share
      one convention — a per-instrument write names its GCS leaf file `{instrument_id}.parquet` verbatim (the FULL
      canonical id, e.g. `FX:SPOT_PAIR:EUR-USD.parquet`), while a genuinely symbol-less bundle write always uses the
      literal leaf `ticks.parquet`. New `_instrument_id_from_leaf()` reads that back (no parsing/guessing — the id was
      already embedded by the writer) instead of hardcoding blank; `instrument_id` joined the shard-grouping key
      (`_candle_shard_key_of` / `_walk_canonical_candle_shards`, now shared by BOTH rebuild and merge — closes a latent
      drift risk where rebuild carried its own near-duplicate copy of the parse loop) so distinct per-instrument
      captures on the same day no longer collapse into one phantom blank-id row with an inflated `instrument_count` (the
      exact `instrument_count=5820.0` symptom this issue doc's own evidence section documented). Regression test
      `test_rebuild_from_canonical_paths_recovers_per_instrument_id_no_blank_rows` proves two distinct FX pairs on the
      same day get two distinct non-blank-id rows (rebuild + idempotent re-run), while a genuine symbol-less bundle
      write still correctly stays blank. `unified-trading-library@64701222` (verified on origin; full `quality-gates.sh`
      green, sentinel-verified quickmerge). (repo: unified-trading-library)
- [x] ✅ [DATA] P2. **INVESTIGATED 2026-08-04 (slot 13) — "1,812 confirmed phantom, zero backing" premise CONTRADICTED,
      disposition changed from DELETE to RE-STAMP.** Built the delete script per this todo's own instruction and
      pre-apply-verified it against the live corpus (per the delete-safety protocol's spirit — confirm before executing
      an irreversible manifest mutation); found every one of the 1,967 candidate dates resolves to a REAL backing GCS
      object once a second, previously-unprobed prefix (`pipeline_mode=batch_databento`) is also checked — content is
      genuine Yahoo-sourced KRW-USD data, not a placeholder. **No delete was executed.** Full evidence + the corrected
      re-stamp todo: `/plans/archive/issues/tradfi_fx_phantom_row_premise_contradicted_2026_08_04.md`. This finding
      FOLDS Defect 1 into Defect 2 below — see that doc's own re-stamp todo, which now supersedes both this todo and the
      dedup todo immediately below. market-tick-data-service@e1b75315 (diagnostic script + tests, verified on origin).
      (repo: market-tick-data-service)
- [x] ✅ [DATA] P2. **DONE 2026-08-04 (slot-12 applied, slot-10 verified) via the superseding doc.** Design + execute a
      de-duplication pass for the 1,958 FX rows spanning 664 dates with redundant per-shard-day manifest bookkeeping —
      **SUPERSEDED 2026-08-04 by the wider re-stamp todo in
      `/plans/archive/issues/tradfi_fx_phantom_row_premise_contradicted_2026_08_04.md`**, which folded Defect 1's former
      1,812 rows into this same population and designed the re-stamp + dedup together against the FULL ~2,787-row
      population. That todo is now DONE: `market-tick-data-service@c86016f6` re-stamped every resolvable row and
      globally deduped `(date, instrument_id)` (keeping the latest `written_at` row), applied + CAS-verified — manifest
      row count 6,601,216 → 6,600,032 (−1,184, matching the predicted dedup count). Re-verified independently 2026-08-04
      (slot-10): `quarantine_tradfi_fx_phantom_manifest_rows_2026_08_04.py` dry-run shows **0** remaining
      blank-`instrument_id` FX candidates. (repo: market-tick-data-service)
- [x] ✅ [DATA] P3. **MOOT 2026-08-04 (slot-10)** — `restamp_tradfi_fx_spot_pair_instrument_id_2026_08_03.py` no longer
      exists in the repo (never actually committed despite being referenced here — confirmed via `git log --all` on the
      path, zero hits) and its whole population is now covered by the completed re-stamp above (0 remaining candidates).
      Nothing left to re-run. (repo: market-tick-data-service)

## Progress Log

- **2026-08-03 (slot 8, data_engineering)**: filed while executing `tradfi_fx_provenance_and_manifest_id_defects-002`.
  Full evidence above; 25 safely-resolvable rows applied under the parent todo (see its own Progress Log for the apply
  SHA/verification).
- **2026-08-03/04 (slot 5, data_engineering)**: closed todo 1 (root-cause investigation) —
  `market-tick-data-service/scripts/rebuild_mtds_manifest.py --from-canonical`'s UTL helpers confirmed as the writer
  mechanism (hardcoded blank `instrument_id` + one shared `written_at` per rebuild run, structurally blind to FX's
  per-instrument filename-stem id). Full diagnosis in § "Root-cause diagnosis" above. Added 2 scoped follow-up todos
  (fix the writer, quarantine/delete the 1,812 existing phantom rows) — both left open, this todo's own scope was
  investigation + decision, not execution, matching the sibling doc's own todo 2/3 split.
  market-tick-data-service@84abe868 (verified on origin). Session note: an earlier attempt's commit (`e31cf8d1`) was
  discarded by the crash-recovery reset when this slot's session died mid-task (waiting on a shared
  `market-tick-data-service` repo-blocker, `RB-e7d79260`, unrelated `cryptography` CVE) — recovered via
  `git cherry-pick` after resume, content verified byte-identical before re-shipping.
- **2026-08-04 (slot 10, data_engineering)**: closed todo 2 (fix the underlying writer bug) — implemented option (a):
  `_instrument_id_from_leaf()` reads the per-instrument id the writer already embeds in the GCS leaf filename (both MTDS
  and MDPS writer lanes share the `{instrument_id}.parquet` vs. symbol-less-bundle `ticks.parquet` convention), and both
  `rebuild_manifest_from_canonical_paths()`/`merge_manifest_from_canonical_paths()` now key discovered shards on it
  instead of hardcoding blank. Added a regression test proving no blank-`instrument_id` row survives a rebuild (or
  re-run) of a per-instrument-grain corpus, while a genuine symbol-less bundle still stays blank.
  `unified-trading-library@64701222` (verified on origin). Follow-up todos 3 (quarantine the 1,812 phantom rows) and 4
  (dedup the 1,958 collision rows) remain open — this todo's own scope was the writer fix only.
- **2026-08-04 (slot 13, data_engineering)**: picked up todo 3 ("quarantine or delete the 1,812 phantom rows"). Built
  the delete script per the todo's instruction, then pre-apply-verified against the live corpus before running `--apply`
  (no delete is ever safe to trust blind) and found the "1,812 confirmed phantom, zero backing" premise CONTRADICTED —
  every one of the 1,967 candidate dates has a real backing GCS object once a second, previously-unprobed
  `pipeline_mode=batch_databento` prefix is also checked; content is genuine Yahoo-sourced KRW-USD data. No delete
  executed. Filed `/plans/archive/issues/tradfi_fx_phantom_row_premise_contradicted_2026_08_04.md` with full evidence +
  a corrected re-stamp (not delete) todo that now supersedes both todo 3 and todo 4 above.
  market-tick-data-service@e1b75315 (diagnostic script + tests, verified on origin).
- **2026-08-04 (slot-10, data_engineering, dispatched via `tradfi_fx_manifest_phantom_and_duplicate_rows-002`)**: closed
  out this doc — the superseding doc's unified re-stamp+dedup landed and was independently verified (0 remaining
  blank-`instrument_id` FX candidates, down from 2,787; manifest row count 6,601,216 → 6,600,032 matching the predicted
  −1,184 dedup exactly). Flipped both remaining todos + `status: resolved`. Full detail + evidence in
  `/plans/archive/issues/tradfi_fx_phantom_row_premise_contradicted_2026_08_04.md`'s own Progress Log.

---
doc_type: issue
title:
  understat XG_SHOTS producer writes inconsistently populate `instrument_type` ("shot" vs unset), which — because
  `instrument_type` is an `_OPTIONAL_DEDUP_COLS` member — splits genuinely-identical (date, league, data_type) cells
  into two coexisting dedup-key groups in the canonical index
summary:
  "Surfaced while re-running plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md's item
  #3 reproduction after the P0 CAS-retry fix (unified-trading-library@75e59a89) shipped and a `--force` full-rebuild
  consolidation ran against instrument-store-sports-prd-central-element-323112 (rows_in=4,981,844 → rows_out=4,899,088,
  dedup_dropped=82,756 — confirming the CAS-race duplicates collapsed as expected). Post-rebuild, 5 duplicate dedup-key
  groups remained in understat XG_SHOTS (big-5 leagues), ALL on date=2024-12-14, ALL with IDENTICAL capture_status=
  captured/error_reason=''/source=understat/row_count=126 — i.e. NOT the CAS-retry lost-update pattern (that pattern
  pairs an old expected_unattempted/blank-source seed with a newer typed row; these pairs are both fully-resolved
  'captured' rows). The only differing field is `instrument_type`: one row (written 2026-06-29T16:09:49Z) sets
  instrument_type='shot'; the other (written 2026-07-08T20:48:15Z, ~9 days newer) leaves it unset (None/NaN).
  `_OPTIONAL_DEDUP_COLS` includes `instrument_type`, and per the module comment on `_resolve_dedup_cols`, ANY optional
  dimension carrying a non-empty value anywhere in the merged frame becomes a REQUIRED dedup-key component for the whole
  cycle — so the 'shot'-tagged row and the unset row land in DIFFERENT dedup-key partitions and both survive the
  window-dedup, even though they represent the same underlying fact (XG_SHOTS EPL/BUNDESLIGA/LA_LIGA/LIGUE_1/SERIE_A
  2024-12-14, 126 rows captured)."
status: open
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [manifest, manifest-consolidator, data-correctness, dedup, understat, sports, instrument_type]
related: [plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md]
created: 2026-07-09
parent_epic: sports_master
priority: P3
source: [plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-09
---

## What I found

While closing item #3 of `manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md` (re-run the reproduction
post-P0-fix), ran
`python -m unified_trading_library.manifest_consolidator --bucket instruments-store-sports-prd-central-element-323112 --force`
to trigger the retroactive full-rebuild needed to actually collapse the pre-fix CAS-race duplicates (the P0 fix only
prevents _future_ races — it does not retroactively re-merge rows a stale pre-fix write already duplicated; routine
incremental cycles only anti-join on _changed_ shard keys, so they leave pre-existing duplicate rows untouched until a
full window-dedup runs). The rebuild succeeded: `rows_in=4,981,844 rows_out=4,899,088 dedup_dropped=82,756`, and a
direct raw-blob re-read confirmed the specific understat XG/XG_SHOTS duplicate-key-group count dropped from 7,565 to 5
(all 15 originally-sampled-style cells now single-row) — the CAS-retry race duplicates are confirmed collapsed.

The remaining 5 groups are a DIFFERENT bug, not this doc's race:

```
(date=2024-12-14, data_type=XG_SHOTS, league_id=BUNDESLIGA|EPL|LA_LIGA|LIGUE_1|SERIE_A):
  row A: capture_status=captured error_reason='' source=understat instrument_type='shot'  written_at=2026-06-29T16:09:49Z
  row B: capture_status=captured error_reason='' source=understat instrument_type=None     written_at=2026-07-08T20:48:15Z
```

Both rows are fully-resolved `captured` states with identical `row_count=126` — this is two producer runs writing the
SAME logical fact with different schema completeness, not a stale-vs-fresh race. Root cause: `instrument_type` is a
member of `_OPTIONAL_DEDUP_COLS` (`unified_trading_library/manifest_consolidator.py:279-290`), and `_resolve_dedup_cols`
promotes ANY optional column with a non-empty value ANYWHERE in the merged frame to a required dedup-key component for
that cycle — so as soon as ONE understat write started tagging XG_SHOTS rows `instrument_type='shot'`, every historical
row from writers that never set it (None/NaN, not the empty-string sentinel `_DEDUP_NULL_SENTINEL` normalizes) stopped
deduping against the newly-tagged rows.

## Why it matters

- Currently narrow (5 cells, 1 date, big-5 leagues, XG_SHOTS only) but the mechanism is general: ANY future understat
  (or other sports producer) write that starts/stops populating `instrument_type` for a data_type that previously never
  set it will silently double-count that data_type's rows in the canonical going forward — a slow-growing duplicate
  count, not a one-time artifact, unless the underlying producer inconsistency is fixed.
- Double-counts in any downstream `COUNT(*)`/coverage-% gate reading the raw canonical directly (same class of
  understatement risk documented in the parent race doc's item #4 tradfi finding, just far smaller scale here).

## Recommended decision

- [ ] [DATA] P3. Decide + fix at the PRODUCER level (repo: unified-trading-library or the sports enumerator/writer that
      emits XG_SHOTS `record_captured` calls): either (a) make instrument_type population consistent across all XG_SHOTS
      writers (always set `'shot'` or always omit), or (b) if instrument_type genuinely doesn't belong in XG_SHOTS's
      identity (the data_type is inherently match/league/date-grained, not per-shot), exclude it from that data_type's
      resolved dedup key. Then re-run `manifest_consolidator --force` against
      `instruments-store-sports-prd-central-element-323112` to collapse the 5 existing duplicate cells once the
      producer-side fix (or key exclusion) lands.

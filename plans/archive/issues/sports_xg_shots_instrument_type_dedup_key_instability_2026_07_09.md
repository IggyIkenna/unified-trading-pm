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
status: resolved
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, instruments-service]
scope: [engineer]
tags: [manifest, manifest-consolidator, data-correctness, dedup, understat, sports, instrument_type]
related: [plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md]
created: 2026-07-09
parent_epic: sports_master
priority: P1
source: [plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md]
assigned_vm: planning
resolved_by: slot-3 (data_engineering), 2026-07-09, instruments-service@f136eec0
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
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

- [x] ✅ [DATA] P3. Decide + fix at the PRODUCER level (repo: unified-trading-library or the sports enumerator/writer
      that emits XG_SHOTS `record_captured` calls): either (a) make instrument_type population consistent across all
      XG_SHOTS writers (always set `'shot'` or always omit), or (b) if instrument_type genuinely doesn't belong in
      XG_SHOTS's identity (the data_type is inherently match/league/date-grained, not per-shot), exclude it from that
      data_type's resolved dedup key. Then re-run `manifest_consolidator --force` against
      `instruments-store-sports-prd-central-element-323112` to collapse the 5 existing duplicate cells once the
      producer-side fix (or key exclusion) lands. — 2026-07-09 slot-3 (data_engineering): instruments-service@f136eec0
      (+57d8b937). Producer-level fix (option (a), always omit — matches the sports-wide blank-`instrument_type`
      convention) was ALREADY shipped at `instruments-service@4281a01d` (2026-07-06); this pass closed the retroactive
      half. Root-caused why a plain `--force` rebuild does NOT collapse pre-existing `instrument_type='shot'` rows:
      `instrument_type` is part of the resolved dedup KEY (`_OPTIONAL_DEDUP_COLS`/`_resolve_dedup_cols` in
      `manifest_consolidator.py`), so window-dedup only merges rows that already share an IDENTICAL key — relabeling a
      row's `instrument_type` creates a NEW key-partition rather than superseding the old one (confirmed by direct
      repro: wrote a corrective per-VM shard relabeling the 5 rows to `''`, ran `--force`, and the 5 stale `'shot'` rows
      survived unchanged). Fix required a direct, verified canonical rewrite dropping the 5 stale rows (only after
      confirming each had a valid captured blank-`instrument_type` sibling covering the same cell) — both one-off
      scripts checked in (`scripts/fix_xg_shots_instrument_type_dedup_2026_07_09.py`,
      `scripts/drop_stale_xg_shots_shot_rows_2026_07_09.py`). Verified directly against
      `instruments-store-sports-prd-central-element-323112`: 0 `instrument_type='shot'` XG_SHOTS rows remain, 0
      duplicate `(date, league_id)` XG_SHOTS groups remain system-wide. Also fixed 3 unrelated pre-existing quality-gate
      blockers hit while shipping (tree was red at HEAD before this commit, independently verified): STEP 5
      codex-compliance ratchet (deep `unified_api_contracts` imports in 6 orchestrator files; 2 test files' hardcoded
      prod project ID) and STEP 5.101 empty-string-fallback baseline (`scripts/reconcile_phantom_manifest_rows_all.py` —
      genuinely optional cross-asset-group columns, matching the file's own existing noqa precedent).

## Progress Log

- **2026-07-13 (slot-3, interactive session) — REOPENED, the 2026-07-09 fix did not stick.** A fresh live-manifest read
  (`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, updated
  2026-07-13T12:01:14Z) found the EXACT same pattern this doc claimed resolved: 2024-12-14, big-5 leagues, XG_SHOTS
  `instrument_type='shot'` vs `''`/`None` twins (10 rows / 5 groups) — the 2026-07-09 "0 remain system-wide"
  verification no longer holds. Additionally found a related-but-new instance on **XG** itself (not XG_SHOTS): 2
  duplicate `captured` rows per big-5 league on the same 2024-12-14 date, both `instrument_type=None`, one from
  2026-07-08 and a fresh twin written 2026-07-13T06:21Z. Flipped `status` back to `open`. **Prime suspect (not yet
  confirmed): a lingering/zombie corrective shard.** This doc's own fix mechanism writes a per-VM corrective shard at
  `_index/per_vm/{VM_NAME}.parquet` rather than touching the canonical blob directly, relying on the consolidator's next
  merge cycle to pick it up and then (implicitly) retire it. If that shard is never cleaned up post-merge, or if the
  consolidator's incremental anti-join re-applies a stale corrective shard against an already-current canonical row,
  that would explain a "resolved" fix producing a fresh duplicate days later without any new buggy write actually
  happening. This is also plausibly the SAME standing, never-root-caused gap flagged in
  `sports_manifest_null_vs_empty_dedup_double_count_2026_06_21.md` ("Update 2026-07-08": the deployed consolidator's
  incremental cycles were not reliably applying the NULL/`''` dedup fix in production). **Next steps** (tracked as a
  todo in `plans/archive/2026_07/understat_local_backfill_completion_2026_07_06.md`, 2026-07-13 entry): (1) re-run
  `fix_xg_shots_instrument_type_dedup_2026_07_09.py --apply` + `manifest_consolidator --force` to collapse the current
  residual; (2) list `_index/per_vm/` on the sports bucket for stale/uncleaned corrective shards and check whether the
  consolidator retires a per-VM shard after merging it or leaves it to be re-applied indefinitely; (3) do not re-close
  this doc until the recurrence mechanism is actually identified — another one-off relabel without understanding WHY it
  recurred will likely just recur again.
- **2026-07-13 (same session, later) — RE-CLOSED. Root cause was NOT a recurrence of this doc's own bug — it was
  collateral damage from an unrelated migration bug in a different repo.** Full root-cause: today's 16-VM
  `sports_manifest_canonicalisation_2026_06_01.md` E4 apply-pass ran `market-tick-data-service`'s
  `rebuild_sports_manifest_v9.py --surface instruments` against instruments-service's own manifest, and that script had
  a real bug (hardcoded `service_name`, no `asset_group` threading) that re-emitted 684,158 rows fleet-wide (understat
  XG/XG_SHOTS included) under `service_name="market-tick-data-service"` at `2026-07-13T06:16:51Z`– `06:23:04Z` — exactly
  matching the "fresh 06:21Z twin" observed above. This was never a lingering-shard/consolidator issue and this doc's
  2026-07-09 fix DID stick (verified: 0 `instrument_type='shot'` rows remain) — the "recurrence" was a same-day,
  one-off, unrelated mass-write landing on top of it. Full detail, fix (`market-tick-data-service@55f9e961`), and
  cleanup (`instruments-service@2f56038e`, direct canonical rewrite dropping 683,592 confirmed duplicates) are tracked
  in `plans/active/sports_manifest_canonicalisation_2026_06_01.md` (E3/E4 entry) — that is now the durable home for this
  finding. Re-verified live: 0 duplicate groups remain for understat XG/XG_SHOTS big-5. Flipping `status` back to
  `resolved`.

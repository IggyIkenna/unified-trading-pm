---
doc_type: issue
title:
  reprocess_sports_odds.py --force cannot correct a false `captured` manifest row — the reader/consolidator
  captured-outranks-recency tie-break permanently masks the honest attempted_failed/empty_confirmed verdict
summary: |
  sports_closeout_batch1_ao_ready_2026_07_24.md todo 3 ([DATA] P0) asked to run
  `reprocess_sports_odds.py --force` for 2025-12-18/24/31 so the manifest's stale `captured` coarse row (a
  legacy-path capture leak) flips to an honest verdict. The real script DOES correctly reclassify all 3 dates
  as `attempted_failed` (ADAPTER_RETURNED_EMPTY_OUTPUT — raw odds exist but land in the T-12h/T-24h dead-zone,
  §B2) and DOES write that row via `ManifestWriter.record_failed()`. But the write never becomes visible at read
  time: `unified_trading_library.manifest_writer._read_index._merge_shard_frames`'s captured-outranks-recency
  tie-break (shipped `unified-trading-library@17ee38de`, 2026-07-14,
  `sports_index_recency_masked_captured_atoms_2026_07_13.md`) ranks ANY `capture_status='captured'` row above
  ANY non-captured row for the same dedup key, unconditionally, regardless of which one is newer. Since all 3
  dates already carry a `captured` row (dated 2026-07-14T04:1x, both at the coarse per-day key and at 9-11
  per-league T-0 shard keys), the new `attempted_failed` row loses every time. Measured directly: a fast-path
  `lookup()` read taken seconds after the 2025-12-31 write showed `attempted_failed` (fresh); a second read ~15
  minutes later (after the background consolidator's next cycle) showed `captured` again — confirming the flip
  reverts, it isn't just absent. `reprocess_sports_odds.py --force` is therefore NOT the "not a hand-edit"
  compliant mechanism the todo assumed; the codebase's own established precedent for this exact class of
  correction (`instruments-service/scripts/flip_phantom_to_attempted_failed.py`) is a bespoke, reviewed,
  backup-then-write script that edits `_index/availability_index.parquet` directly — a materially different,
  higher-privilege action than "run the real script," and out of this todo's stated scope without a decision.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, market-data-processing-service, instruments-service]
scope: [engineer]
tags: [manifest, honest-coverage, sports, dedup, captured-outranks, recency-masking]
related:
  - /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
  - /plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md
created: "2026-07-24"
parent_epic: sports_master
priority: P1
source: sports_closeout_batch1_ao_ready-003 execution (slot 5, 2026-07-24)
assigned_vm: planning
resolved_by: ""
locked_by: ""
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# reprocess_sports_odds.py --force cannot correct a false `captured` row (captured-outranks tie-break)

## What I found

Ran `reprocess_sports_odds.py --start-date <D> --end-date <D> --force` for real (no `--dry-run`) against PROD for
2025-12-18, 2025-12-24, and 2025-12-31 (`market-data-tick-sports-prd-central-element-323112` /
`instruments-store-sports-prd-central-element-323112`). All 3 dates read raw odds successfully (26.7k-28.8k rows,
654-702 parquet files) but the `SportsBucketAssignmentAdapter` returned an empty bucketed frame for all 3 — every
observation's `bm_minutes_to_kickoff` falls in the T-12h/T-24h 615-minute structural dead-zone the parent audit's §B2
already root-caused. The script correctly classified this as `ADAPTER_RETURNED_EMPTY_OUTPUT` →
`record_failed(capture_status="attempted_failed")` for all 3 (not the `empty_confirmed` the todo predicted for
2025-12-24 — see "Secondary finding" below) and each run logged a successful manifest write
(`ManifestWriter: updated availability index (... 1 new)`).

Verifying via `ManifestWriter.lookup()` (the exact API `reprocess_sports_odds.py`'s own pre-flight uses) immediately
after each write showed:

- 2025-12-18 → still `captured` (2026-07-14T04:17:31, unchanged)
- 2025-12-24 → still `captured` (2026-07-14T04:17:53, unchanged)
- 2025-12-31 → `attempted_failed` (2026-07-24T19:26:31, fresh) — briefly

A raw (un-deduped) read of the merged index for all 3 dates found the OLD `captured` rows still present at BOTH the
coarse per-day key (`league_id`/`timeframe` null, `row_count` 51/63/62) AND 9-11 per-league `T-0` shard keys (e.g.
`soccer_japan_j_league`, `soccer_usa_mls`, ...), all dated 2026-07-14T04:1x:xx — no trace of my new `attempted_failed`
rows appeared in that read at all.

Re-running the `lookup()` check ~15 minutes later showed **2025-12-31 had reverted to `captured`** too — all 3 dates now
read identically to their pre-run state. This rules out "just hasn't propagated yet": the fresh row existed, was read
once, and was then masked/lost, matching `_merge_shard_frames`'s documented behavior exactly ("within one dedup-key
group, `capture_status='captured'` always beats any non-captured row ... regardless of recency" —
`unified_trading_library/manifest_writer/_read_index.py:1184-1191`, shipped `unified-trading-library@17ee38de` per
`sports_index_recency_masked_captured_atoms_2026_07_13.md`).

## Why it matters

This todo's premise — "run the real script (not a hand-edit) so the stale `captured` state flips to the honest verdict"
— cannot succeed through `reprocess_sports_odds.py --force` alone, for ANY atom that already carries a `captured` row,
because the manifest's own reader-side (and, per the referenced issue doc, consolidator-side) dedup logic is DESIGNED to
make `captured` win unconditionally. That protection exists for a good reason (prevent a stray later empty/failure stamp
from masking a real capture — the 2026-07-13 oscillation), but it has no way to distinguish "this later attempt is a
deliberate correction of a KNOWN-false capture" from "this later attempt is routine noise." The effect: the legacy-path
capture leak this todo set out to fix is **structurally un-fixable** via the sanctioned "run the real script" path — the
same blocker would hit ANY future attempt to correct a false `captured` atom anywhere in the sports (or likely any)
manifest, not just these 3 dates.

The codebase already has a precedent for this exact correction direction —
`instruments-service/scripts/flip_phantom_to_attempted_failed.py` (backup-then-write directly against
`_index/availability_index.parquet`, used to re-flip 100,431 phantom-captured rows to `attempted_failed`) — but
building/running an equivalent one-off script is a materially different, higher-privilege action than what this todo
described ("not a hand-edit"), and touches a shared, deliberately-guarded mechanism, so it needs sign-off before a
data_engineering worker does it under this todo's scope.

## Secondary finding (lower priority)

The todo's predicted per-date verdict split (`attempted_failed` for 18/31, `empty_confirmed` for 24) does not match what
the real script actually determines: **all 3 dates classify as `attempted_failed`** (`ADAPTER_RETURNED_EMPTY_OUTPUT`),
including 2025-12-24. The parent audit's own §B2 root-cause called 2025-12-24 "genuine honest-absence (0 in-window)" — a
semantic judgment that the raw ticks exist but zero land in any Tier-1 horizon window — but `reprocess_date()`'s
honest-absence classification only awards `empty_confirmed` when `_read_raw_odds` returns a genuinely-empty DataFrame
(zero raw bytes anywhere for the date); a non-empty raw frame that the adapter filters to zero rows is always
`attempted_failed`/`ADAPTER_RETURNED_EMPTY_OUTPUT`, by design, per the 2026-06-22 honest-absence hardening rule (a real
fetch found data, so a clean-empty proof would be false). The code doesn't currently distinguish "the dead-zone ate
every observation" from any other adapter-empty cause. This overlaps the parent plan's own still-open Track O
`[DIAG] P2` todo ("corpus-wide scan for other low-fixture dates whose only in-window odds fall in the T-12h/T-24h
dead-zone ... consider adding a T-18h horizon") — no new todo needed here, just noting the discrepancy so whoever picks
up that DIAG item has this data point.

## Recommended decision

- **Option A (recommended)**: build a scoped, reviewed, backup-then-write correction script mirroring
  `flip_phantom_to_attempted_failed.py`'s pattern — read `_index/availability_index.parquet` from
  `instruments-store-sports-prd-{project}`, snapshot it, re-stamp the coarse + per-league/T-0 rows for these 3 dates
  (identified above) from `captured` to `attempted_failed`, write back. Small, targeted, precedented; single
  data_engineering todo.
- **Option B**: leave the manifest as-is for now (my correct `attempted_failed` writes remain in the raw per-VM shard
  data as evidence, even though currently masked at read time); file a new backlog todo for Option A's script rather
  than building it under this todo; this todo stays not-fully-completable as literally scoped.
- **Option C**: revisit `_merge_shard_frames`'s tie-break itself to support a marked, deliberate override (e.g. a
  `correction=True` flag that beats `captured` for a specific, human-reviewed re-stamp) — a bigger, cross-cutting design
  change affecting every asset_group's manifest, not sports-specific; too large for this todo, flagged for awareness
  only.

## Todos

- [ ] [DATA] P1. Implement Option A (or whichever the operator/main picks): a one-off backup-then-write script
      re-stamping the 2025-12-18/24/31 coarse + per-league T-0 `captured` rows in
      `instruments-store-sports-prd-{project}/_index/availability_index.parquet` to `attempted_failed`, mirroring
      `instruments-service/scripts/flip_phantom_to_attempted_failed.py`'s snapshot-then-write pattern. Verify via
      `ManifestWriter.lookup()` immediately AND after >=2 consolidator cycles (per the 2026-07-14 adjudication's own
      verification recipe) so a transient read isn't mistaken for a durable fix. Repo: instruments-service or
      unified-trading-library (whichever owns the correction-script home per
      `/codex/06-coding-standards/script-homes.md`).

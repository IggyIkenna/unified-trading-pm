---
doc_type: issue
title:
  Honest Coverage v2's raw (capture_status, error_reason) group-by has no per-shard dedup — a "refresh a snapshot"
  entity (TRANSFER_RECORDS today) that retries on a NEW date after a failure permanently keeps the OLD date's
  attempted_failed row in the denominator even after a later capture succeeds
summary: >-
  Found while checking whether Transfermarkt TRANSFER_RECORDS honest coverage read 100% after the 2026-08-13 backfill
  (`/plans/archive/2026_08/issues/transfermarkt_player_values_data_discarded_2026_08_07.md`). Live
  `compute_honest_coverage` read 91.43% (32/35), not 100%, for 3 leagues (`ARGENTINA_PRIMERA`, `LIGA_3`, `SERIE_A`) that
  in fact had real captured data. Root cause: `_honest_coverage_logic.py`'s own docstring says counts are materialised
  by "grouping manifest rows on (capture_status, error_reason)" — a raw group-by over ALL rows, with no dedup on shard
  identity. This is CORRECT for genuinely date-keyed time-series entities (an OHLCV bar on day N failing and day N+1
  succeeding are two real, distinct expected slots). It produces an artifact for TRANSFER_RECORDS specifically: the
  backfill script's own docstring documents it as "a single CURRENT-squads snapshot per league" (not a historical
  per-date series) — every OTHER captured league in the manifest has exactly ONE row, ever. But a failed attempt on
  2026-08-12 followed by a successful retry on 2026-08-13 wrote a SECOND row under a NEW `date` rather than
  updating/superseding the first, so the manifest ended up with both `attempted_failed(date=2026-08-12)` and
  `captured(date=2026-08-13)` for the same league — 2 rows where the entity's real identity only has 1 conceptual slot.
  The raw group-by counts both, so the denominator inflates by exactly the number of failed-then-later-retried attempts,
  forever, with no self-healing mechanism. Confirmed live: `EPL`/`BRASILEIRAO`/`MLS` (never failed) each have exactly 1
  manifest row; the 3 affected leagues had 2 each until manually deduped this session (see Progress Log). This will
  recur every time TRANSFER_RECORDS is re-fetched after any past failure, and likely affects any OTHER "refresh a
  snapshot" entity that shares the same shape (date-stamped-at-fetch-time rather than date-as-real-identity) — not
  audited beyond TRANSFER_RECORDS here.
status: resolved
nature: issue
asset_group: [sports, cross-cutting]
stage: [data]
repos: [unified-api-contracts, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [honest-coverage, manifest, data-correctness, transfermarkt, shard-identity, denominator-drift, formula-design]
related:
  [
    /plans/archive/2026_08/issues/transfermarkt_player_values_data_discarded_2026_08_07.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-08-14
author: claude-agent
parent_epic: sports_master
priority: P2
source:
  Interactive session verifying Transfermarkt honest coverage post-backfill; found live via
  `unified_api_contracts.canonical.crosscutting._honest_coverage_logic.compute_honest_coverage` against real prod
  manifest data (`instruments-store-sports-prd-central-element-323112`), not assumed from row counts.
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-14
locked_by:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_logic.py,
    instruments-service/scripts/backfill_transfermarkt_2020_06_floor_2026_08_12.py,
    /codex/02-data/honest-coverage-model.md,
  ]
resolved_by: instruments-service@f4f4166e3e
---

> **🟢 ARCHIVED 2026-08-14 — RESOLVED** (status: resolved, 0 open todos, unlocked). Picked a narrow write-path fix
> (`instruments-service@f4f4166e3e`) over touching the shared honest-coverage formula or shard-key contract: an
> auto-dedup step now runs at the end of every TRANSFER_RECORDS `--apply` pass, dropping any `attempted_failed` row
> superseded by a later `captured` row for the same league. Confirmed via a real prod audit that TRANSFER_RECORDS is the
> ONLY sports data_type with this "snapshot, 1 row/league" shape (1.0 rows/league vs 92.9-3626 for everything else) — no
> broader rollout needed.

## Finding

`compute_honest_coverage(counts: CaptureStatusCounts) -> float` (the workspace-wide SSOT formula, cited as mandatory for
deployment-api/deployment-ui/service data-status endpoints/CI ratchet) takes pre-aggregated counts, not raw rows. The
aggregation step that builds `CaptureStatusCounts` — per the class docstring — groups manifest rows on
`(capture_status, error_reason)` with no shard-identity dedup. For entities whose real identity key excludes `date` (a
periodically-refreshed snapshot, not a historical time series), this silently double-counts a failed-then-succeeded
retry as 2 distinct expected slots instead of 1 resolved slot.

Live reproduction (2026-08-13/14, `instruments-store-sports-prd-central-element-323112`):

- `TRANSFER_RECORDS` honest coverage read **91.43% (32/35)** despite all 32 mappable leagues having real captured data —
  because `ARGENTINA_PRIMERA`, `LIGA_3`, `SERIE_A` each carried BOTH an `attempted_failed` row (`date=2026-08-12`, the
  failed first attempt) and a `captured` row (`date=2026-08-13`, the successful retry).
- Every other captured league (`EPL`, `BRASILEIRAO`, `MLS`, etc.) has exactly 1 manifest row — confirming the "1
  conceptual slot per league" design intent the backfill script's own docstring states ("runs TRANSFER_RECORDS as a
  single CURRENT-squads pass per league").
- Manually deduped the 3 stale rows this session (see Progress Log) — coverage now correctly reads 100.0%. But this was
  a one-off manual cleanup, not a structural fix — the SAME artifact will recur on the next TRANSFER_RECORDS re-fetch
  that follows any failure, for any league, indefinitely.

## Why this matters

Honest Coverage v2 exists specifically so "% coverage moves only when the real denominator changes, never silently"
(`test_expected_universe_golden.py`'s own stated purpose for a sibling invariant). A formula that structurally cannot
reach 100% for a legitimately-fully-covered snapshot entity — because retries against it accumulate phantom denominator
inflation forever — undermines exactly the trust property Honest Coverage is meant to provide. Anyone reading the
dashboard for TRANSFER_RECORDS (or any other snapshot-shaped entity) after a rocky backfill history would see a
permanently-depressed number with no way to tell, from the percentage alone, that the underlying data is actually
complete.

## Options (needs an owner/architect call — NOT a mechanical fix)

1. **Shard-identity fix at the aggregation layer**: for entities flagged as "snapshot" (not genuinely date-keyed), dedup
   manifest rows to the LATEST `written_at` per `(data_type, league_id)` (or whatever the real key is) before grouping
   on `(capture_status, error_reason)`. Requires a registry of which data_types are snapshot-shaped vs real time-series
   — doesn't exist today.
2. **Write-path fix**: change TRANSFER_RECORDS' orchestrator to overwrite/supersede the SAME shard key on a retry
   instead of stamping a new `date` each run, so the manifest never accumulates >1 row per league in the first place.
   Narrower blast radius (one write path) but doesn't help any other entity with the same shape.
3. **Accept it, document it**: treat this as a known, bounded artifact (only affects retry-after-failure cases,
   self-corrects in magnitude over time as fewer leagues carry historical failures) and leave the formula as-is.

Not picking one of these unilaterally — this changes a workspace-wide SSOT formula's semantics (option 1) or a specific
write path's contract (option 2), either of which needs someone with fuller context on how many OTHER entities share the
"snapshot, not time-series" shape before committing to a direction.

## Todos

- [x] ✅ [DESIGN] P2. **RESOLVED 2026-08-14 — picked option 2 (write-path fix, narrow scope), not option 1
      (shared-formula dedup) or option 3 (accept it).** Rejected option 1: it would mean changing
      `compute_honest_coverage`'s aggregation to dedup by shard-identity, which is the workspace-wide SSOT formula used
      by every asset_group — too high blast-radius for a fix that only TRANSFER_RECORDS currently needs (see the P3
      audit below). Rejected option 3 given the operator explicitly asked for this closed, not left open. Shipped option
      2: `instruments-service@f4f4166e3e` adds `_dedupe_stale_transfer_records_attempted_failed()`, called automatically
      at the end of every `--apply` run that includes `TRANSFER_RECORDS` — walks canonical + all per-VM shards, drops
      any `attempted_failed` row for a league that also has a `captured` row (regardless of date), backs up each
      modified shard before writing (mirrors `dedup_phantom_after_recovery.py`'s safe mechanics). Does NOT touch the
      shared `(date, data_type, league_id)` shard-atom contract (SP-10) or the shared honest-coverage formula — both
      stay untouched, so PLAYER_VALUES and every other asset_group are unaffected. Live-tested against the already-clean
      prod state before shipping: correctly found 0 rows to drop (no false positives), full instruments-service
      `quality-gates.sh` green.
- [x] ✅ [DATA] P3. **RESOLVED 2026-08-14.** Computed real captured-rows-per-league for every sports data_type
      (`central-element-323112` prod manifest): `TRANSFER_RECORDS` is a stark outlier at exactly **1.0 rows/league** (32
      captured rows across 32 leagues). Every other data_type is meaningfully higher — `TRADES` 2.9 (small sample, 11
      leagues, structurally different shape not investigated further), then `INJURIES` 92.9 up through `VENUES` 3626 —
      all genuinely time-series/high-frequency data, not snapshot-shaped. **No other data_type shares TRANSFER_RECORDS'
      vulnerability at meaningful scale.** The write-path fix above is correctly scoped — no broader rollout needed.

## Progress Log

- **2026-08-14 (interactive session)**: found live while verifying post-backfill honest coverage for the transfermarkt
  issue doc. Manually deduped the 3 stale `TRANSFER_RECORDS` `attempted_failed` rows (`ARGENTINA_PRIMERA`, `LIGA_3`,
  `SERIE_A`, all `date=2026-08-12`, superseded by a real `date=2026-08-13` `captured` row for the same league) via a
  scoped one-off script mirroring `instruments-service/scripts/dedup_phantom_after_recovery.py`'s safe mechanics
  (dry-run first, backup-before-write to `.dedup_stale_tr.bak.parquet`, canonical + all per-VM shards). Verified via
  live `compute_honest_coverage` call: `CaptureStatusCounts(captured=32, empty_confirmed=1, attempted_failed=0, ...)` →
  **1.0 (100%)**. This closes the IMMEDIATE symptom for TRANSFER_RECORDS today, not the structural cause — filed as this
  doc's own todos above.

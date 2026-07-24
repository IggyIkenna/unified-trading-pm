---
doc_type: issue
title:
  55,233 legacy FIXTURES sports manifest rows are exact duplicates of an already-migrated FIXTURES_SCHEDULE row —
  restamp-blocked, DELETE policy decision needed
summary: >-
  sports_closeout_batch1_ao_ready_2026_07_24.md's [DATA] P0 backfill todo restamped 282,231 of 337,464 legacy
  data_type="FIXTURES" sports manifest rows to FIXTURES_SCHEDULE (instruments-service@e92efc78, verified). The remaining
  55,233 rows could NOT be safely restamped: their post-restamp dedup key (date, venue, service_name, league_id, ...)
  already exists as a FIXTURES_SCHEDULE row today — a genuine dual-write duplicate from the
  sports_fixture_status_refresh.py leak (fixed instruments-service@47c1ffb3). Sampled rows confirm these are
  BYTE-IDENTICAL duplicates (same capture_status, same error_reason, same every dedup dim) spanning 2020-06-06 through
  2026-12-06 — not a "which side is correct" question, purely redundant rows. A resolution decision is needed before
  these can be closed out; DELETE is the natural fix but is a workspace-wide banned pattern for this manifest family
  pending verification it's safe here specifically.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [sports, fixtures, manifest, data_type-atom, duplicate, backfill, honest-coverage]
related:
  [
    /plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/issues/fixtures_manifest_legacy_backfill_2026_07_24.md,
    /plans/archive/issues/legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  found while running sports_closeout_batch1_ao_ready_2026_07_24.md's [DATA] P0 restamp todo, 2026-07-24 (escalation
  agt-2a122f follow-up)
---

## What I found

The restamp script (`instruments-service/scripts/restamp_fixtures_manifest_legacy_atom_2026_07_24.py`) ran `--apply`
against the real prod manifest (`instruments-store-sports-prd-central-element-323112`, generation `1784932654620334` →
`1784932868619431`), backed up first
(`gs://instruments-store-sports-prd-central-element-323112/_index/backups/availability_index.pre_fixtures_legacy_restamp_apply_20260724T224019Z.parquet`).
Result, fully verified post-write:

- `FIXTURES` → `FIXTURES_SCHEDULE`: **282,231 rows restamped** (safe, no collision).
- **55,233 rows ESCALATED** (left as legacy `FIXTURES`, untouched) — their post-restamp dedup key
  `(date, venue, service_name, league_id, ...)` already exists as an EXISTING `FIXTURES_SCHEDULE` row.
- 0 internal collisions, 0 duplicate keys post-write, `FIXTURES_OUTCOMES` (57,039) untouched.

**Sampled 3 of the 55,233 rows** (arbitrary, first-N by row order) and diffed each against its colliding
`FIXTURES_SCHEDULE` sibling on every dedup dimension PLUS `capture_status`/`error_reason`: all 3 are **byte-identical**
on every checked column. The 55,233 population's `capture_status` breakdown: `captured` (42,755), `empty_confirmed`
(12,180), `expected_unattempted` (298); `error_reason` breakdown shows a mix of blank (43,053), `EXPECTED_NO_FIXTURE`
(7,982), `SOURCE_RETURNED_ZERO` (1,204), and several `EXPECTED_*` lifecycle reasons. **Date range: 2020-06-06 through
2026-12-06** — spans well past the 2026-07-14 writer-migration cutover, confirming the
`sports_fixture_status_refresh.py` leak (fixed today, `instruments-service@47c1ffb3`) was continuously re-writing
legacy-atom rows for a wide date range, including CURRENT/recent dates, right up until the fix landed.

## Why it matters

These 55,233 rows are pure redundant noise — the correct data already exists under the canonical `FIXTURES_SCHEDULE`
atom. They don't currently cause a coverage-math error (the additive `SCHEDULE_DEFINING_DATA_TYPES` fix,
`unified-api-contracts@c2b303f7`, still resolves legacy-atom `SOURCE_RETURNED_ZERO` rows correctly), but:

1. They inflate row counts / storage cost for zero informational value.
2. They keep `SCHEDULE_DEFINING_DATA_TYPES` permanently additive (can never narrow back to
   `frozenset({FIXTURES_SCHEDULE})`, sports_closeout_batch1_ao_ready_2026_07_24.md todo 1's original Done-when) — a
   live, uncleared TODO item accumulates as tech debt.
3. Any future census/audit re-discovers this exact 55,233 number and re-asks the same question unless it's closed here.

## The blocker: row DELETE is a workspace-wide banned pattern for this manifest family

`plans/archive/issues/legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md` established that a row DELETE is
UNSAFE for sports/cefi manifest families in general — a stale `_legacy_seed.parquet` can resurrect deleted rows on the
next consolidator merge (fixed for the GENERAL case in `unified-trading-library@f14b13ae`/`@8e783d70`, but the precedent
restamp scripts (`restamp_sports_odds_horizon_bucket_2026_07_22.py`, this todo's own script) both deliberately chose
re-stamp over delete for exactly this reason). This population is different in kind, though: these rows are PROVABLY
exact duplicates of an already-migrated, already-correct row — deleting them doesn't lose any information the surviving
`FIXTURES_SCHEDULE` row doesn't already carry, unlike a general-purpose delete. Whether that distinction is enough to
justify a scoped, verified delete here (vs. leaving them as permanent harmless noise) is a genuine design call, not
something to decide unilaterally.

## Recommended decision

1. **Leave them as permanent noise** (do nothing further) — simplest, zero risk, but `SCHEDULE_DEFINING_DATA_TYPES`
   stays additive forever and the row-count/storage cost is permanent. [Recommended if delete-safety can't be
   re-verified for this specific case quickly.]
2. **Scoped, verified DELETE** — extend the `_legacy_seed.parquet` resurrection fix's verification method
   (`unified-trading-library@f14b13ae`/`@8e783d70`) to confirm it also covers this bucket/consolidator before deleting
   these 55,233 rows; requires the same paused-cron + snapshot + CAS pattern as the restamp itself. Would let
   `SCHEDULE_DEFINING_DATA_TYPES` narrow back to `frozenset({FIXTURES_SCHEDULE})` (closing
   sports_closeout_batch1_ao_ready_2026_07_24.md todo 1's original Done-when) once done.
3. **Investigate a tombstone/supersede mechanism** instead of a hard delete, if one already exists elsewhere in the
   manifest consolidator (mentioned as a concept in the odds_horizon_bucket precedent's docstring but not verified to
   exist as working code) — avoids re-deriving the delete-safety proof from scratch.

## Todos

- [ ] [DIAG] P2. Decide + execute the resolution for the 55,233 duplicate legacy `FIXTURES` rows in
      `instruments-store-sports-prd-central-element-323112` (options above). **Done when**: either (a) the rows are gone
      via a verified-safe delete AND `SCHEDULE_DEFINING_DATA_TYPES` (`unified-api-contracts`) is narrowed back to
      `frozenset({FIXTURES_SCHEDULE})`, sentinel-verified, OR (b) an explicit operator/main decision to leave them
      permanently is recorded here with rationale. (repo: instruments-service + unified-api-contracts)

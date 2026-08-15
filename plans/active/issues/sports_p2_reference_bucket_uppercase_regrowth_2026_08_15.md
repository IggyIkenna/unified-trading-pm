---
doc_type: issue
title: Sports reference-bucket 19-token lowercase restamp — a live writer is still emitting uppercase post-migration
summary: >-
  Four-surface reconciliation (sports_taxonomy_p2_migration_2026_08_08.md's "Four-surface reconciliation after the
  migration" REVIEW todo) found `instruments-store-sports-prd`'s manifest carries 8,078 rows across 9 of the 19
  reference-vocabulary tokens (INJURIES 3,847 / STANDINGS 1,911 / TEAMS 1,010 / FIXTURE_STATS 600 / FIXTURE_LINEUPS 596
  / PLAYER_STATS 76 / FIXTURE_EVENTS 20 / FIXTURES_OUTCOMES 12 / PLAYER_VALUES 6) that STILL carry the retired uppercase
  form. Every one of these rows has `attempted_at` between 2026-08-14T04:55Z and 2026-08-15T06:01Z — i.e. AFTER the
  plan's own "0 uppercase-token rows remaining" closing verification (also dated 2026-08-14) — so this is not
  un-migrated historical residue the restamp missed; it is a live writer somewhere in the fleet that keeps emitting
  uppercase tokens on every new fetch, unaffected by the registry flip (`instruments-service@3637252f81`/`f2586ada09`).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, migration, canonicalisation, manifest, live-writer, regression, data-correctness, casing]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-15
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
source:
  [
    "sports_taxonomy_p2_migration_2026_08_08.md 'Four-surface reconciliation' REVIEW todo, live census 2026-08-15
    (slot-9)",
  ]
resolved_by:
locked_by:
locked_since:
---

# Sports reference-bucket 19-token restamp — live regrowth after the closing verification

## What I found

Four-surface reconciliation (S3 manifest census, `read_availability_index_safe` against
`instruments-store-sports-prd-central-element-323112`, columns-only, no filter — bucket confirmed medium-scale, ~15.7M
rows):

- 8,078 rows still carry one of the 19 target tokens in UPPERCASE:
  `{INJURIES: 3847, STANDINGS: 1911, TEAMS: 1010, FIXTURE_STATS: 600, FIXTURE_LINEUPS: 596, PLAYER_STATS: 76, FIXTURE_EVENTS: 20, FIXTURES_OUTCOMES: 12, PLAYER_VALUES: 6}`.
- `capture_status`: 8,072 `empty_confirmed`, 3 `attempted_failed`, 3 `captured` — mostly honest-absence bookkeeping, not
  a large real-data loss, but still a live-vocabulary violation.
- `attempted_at` range: **2026-08-14T04:55:40Z → 2026-08-15T06:01:27Z** — entirely AFTER the parent plan's own "step 1
  (manifest re-stamp)... EXECUTED 2026-08-14 (slot-26)" + its dedicated closing-verification todo (also 2026-08-14, "0
  remaining, independently verified" via `census_sports_19token_lowercase_scope_2026_08_14.py` re-run). Sample rows
  (`date=2024-08-01/2025-01-31`, `data_type=PLAYER_VALUES`, `venue=""`, `attempted_at=2026-08-14T04:55:40Z`) show
  historical DATES being re-attempted on a RECENT `attempted_at` — this is a live fetch/enumeration job re-touching old
  date ranges, not a one-time backfill replaying old writes.

**Root cause NOT yet pinned** (bounded investigation this session, ruled OUT rather than confirmed): grepped + read the
two most obvious instruments-service sports write sites —
`instruments_service/engine/orchestrator/process_zero_records.py` and `.../process_fetch.py` — both already route their
`record_captured`/`record_empty` calls' `data_type` through `canonical_sports_is_data_type(...)`, so neither is the
source. The parent plan's own 2026-08-14 correction note admits its 8-site classification of manifest-boundary call
sites was not fully exhaustive ("not yet traced to the same rigor this session":
`sports_reference_fixtures_write.py::_ENTITY_DT_BY_SHORT`'s full consumer set, `_ENRICHMENT_ENTITY_VENUES`'s full
consumer set). Candidate untranslated sites, not yet individually confirmed or ruled out:
`instruments_service/engine/orchestrator/process_preflight.py` (sites other than the 592-598 one already covered),
`process_enrichment.py`, `transfermarkt.py` (both the reference_data/adapters copy and the orchestrator copy), and
`instruments_service/engine/orchestrator/__init__.py`.

## Why it matters

The plan's closing-verification claim ("0 uppercase-token rows remaining… confirmed twice") is now STALE — a live writer
has re-populated 8,078 rows since. If left unfixed this keeps growing indefinitely and any consumer trusting the
"restamp complete" claim (dashboards, the accepted-exception-shrinkage REVIEW todo two lines below this one in the
parent plan) will silently re-admit uppercase tokens as a permanent baseline instead of a closed migration.

## Recommended decision

Find the still-untranslated writer (grep every `record_captured`/`record_empty`/`record_failed` call site in
instruments-service's sports orchestrator modules for a `data_type=` kwarg NOT wrapped in
`canonical_sports_is_data_type(...)`), fix it the same way the already-covered 5 sites were fixed, ship, then re-stamp
the 8,078 residual rows (manifest-only relabel, no GCS object involved for `empty_confirmed`/ `attempted_failed` rows;
the 3 `captured` rows need the standard four-surface re-stamp). Re-run the census with a fresh `attempted_at` filter to
confirm the writer stopped.

## Todos

- [ ] [DATA] P0. Grep every sports `record_captured`/`record_empty`/`record_failed` call site in
      `instruments-service/instruments_service/engine/orchestrator/` for a `data_type=` argument not routed through
      `canonical_sports_is_data_type(...)`; fix the untranslated site(s); ship + QG green.
- [ ] [DATA] P1. Re-stamp the 8,078 residual uppercase reference-bucket rows (manifest-only relabel) once the writer fix
      is confirmed live; re-run `census_sports_19token_lowercase_scope_2026_08_14.py` (or its successor) filtered on
      `attempted_at` after the fix deploy time to confirm 0 new uppercase rows.

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
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-08-15"
last_updated: 2026-08-17
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
drift_direction: advance-code
depends_on: []
context_scope: [/plans/active/sports_taxonomy_p2_migration_2026_08_08.md, /codex/02-data/four-surface-reconciliation-procedure.md, /codex/02-data/gcs-and-manifest-delete-safety-protocol.md, instruments-service/instruments_service/engine/orchestrator/, /plans/active/sports_consolidated_closeout_2026_07_19.md]
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

**Root cause CONFIRMED (2026-08-15, slot-10)** — a full sweep of every `record_captured`/`record_empty`/`record_failed`/
`record_captured_from_counts` call site's `data_type=` argument in
`instruments-service/instruments_service/engine/ orchestrator/` (not just the two previously-checked files) found 4
untranslated sites, matching all 9 regrown tokens:

1. `sports_reference_core.py::_emit_empty_gap_for_league` — the `EXPECTED_NO_PROVIDER_COVERAGE` early-return branch used
   the raw uppercase `data_type` param; `_dt_lower` was computed AFTER that branch's `return`, so it never reached it
   (accounts for INJURIES/STANDINGS/TEAMS/FIXTURE_STATS/FIXTURE_LINEUPS/PLAYER_STATS/FIXTURE_EVENTS — 7,930 of 8,078
   rows, mostly `empty_confirmed`).
2. `process_preflight.py::_enrichment_only_fast_path` — the per-fixture-entity `record_empty` loop (freshness-preflight
   fast path, a second code path onto the same 4 per-fixture entities as #1) used
   `pf_entity.replace("API_FOOTBALL_", "").upper()` directly, uncanonicalised.
3. `sports_fixtures.py::_write_fixtures_per_league` — the FIXTURES_OUTCOMES honest-absence gate (2026-08-14 writer fix,
   itself dated the same day the regrowth window starts) emitted the raw `_orch.FIXTURES_OUTCOMES` constant; this is the
   ONLY manifest touchpoint for FIXTURES_OUTCOMES (12 rows).
4. `process_enrichment.py::_run_sports_enrichment` — the blanket `record_captured_from_counts` fallback for entities not
   in `_self_manifested` used `entity_name.upper()` directly (covers any residual entity not self-manifesting, incl. the
   PLAYER_VALUES path — 6 rows).

Fixed in `instruments-service@b872799efa` — all 4 now route through `canonical_sports_is_data_type(...) or <original>`.

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

- [x] ✅ [DATA] P0. Grep every sports `record_captured`/`record_empty`/`record_failed` call site in
      `instruments-service/instruments_service/engine/orchestrator/` for a `data_type=` argument not routed through
      `canonical_sports_is_data_type(...)`; fix the untranslated site(s); ship + QG green. —
      instruments-service@b872799efa. 4 untranslated sites found + fixed (see "What I found" above); QG green
      (`.qg_last_passed_sha=b872799efaa861280460f5930b0792416f75aa14`); landed on live-defi-rollout, verified ancestor
      of origin.
- [ ] [DATA] P1. Re-stamp the 8,078 residual uppercase reference-bucket rows (manifest-only relabel) once the writer fix
      is confirmed live; re-run `census_sports_19token_lowercase_scope_2026_08_14.py` (or its successor) filtered on
      `attempted_at` after the fix deploy time to confirm 0 new uppercase rows.

## Progress Log

- 2026-08-15 (slot-16): Dispatched the P1 todo above. Independently root-caused P0 in parallel with slot-16 — same 3 of
  their 4 sites (`sports_reference_core.py::_emit_empty_gap_for_league`'s early-return branch = 8,060 rows;
  `sports_fixtures.py`'s bare `_orch.FIXTURES_OUTCOMES` constant = 12 rows; `process_enrichment.py`'s blanket
  `entity_name.upper()` fallback, not yet observed in the regrowth but a real gap) — confirms slot-10's
  `instruments-service@b872799efa` is correct; did not find their 4th site
  (`process_preflight.py::_enrichment_only_fast_path`) myself. Discarded my duplicate local edits and fast-forwarded
  onto their commit rather than shipping a conflicting version. P1 itself is NOT started: "confirmed live" is the
  load-bearing phrase here — the 2026-08-14 restamp was undone because it followed the code fix onto LDR by only ~2
  minutes, before the running service had actually picked it up. Restamping again on the same premature timing would
  reproduce that exact mistake. `instruments-service@b872799efa` needs to (a) promote LDR→main, (b) actually redeploy
  the live service, and (c) complete at least one subsequent write cycle, before a re-run of
  `census_sports_19token_lowercase_scope_2026_08_14.py` can honestly confirm 0 new uppercase rows. None of that is
  verifiable synchronously in one agent turn. Releasing P1 back to the queue (`GATED`, ~180 min) rather than restamping
  now.
- 2026-08-15 (slot-32, data_engineering): Re-checked live-deploy status — `b872799efa` is CONFIRMED still not on `main`
  (`git merge-base --is-ancestor` false against a freshly-fetched `origin/main`). The LDR→main promote pipeline is
  actively running (a promote batch landed ~12:01-12:06Z, `main` advanced from 1261→1183 commits behind LDR) but hasn't
  reached this commit's position in the backlog yet — genuinely still gated, not a stall. No Cloud Run service named
  `instruments-service` exists (it runs as scheduled Cloud Run Jobs, e.g.
  `uts-prod-instruments-service-sports-fixtures`, image tag `:latest`); deploy-liveness for the actual fix therefore
  requires promote→image-build-gate→a fresh job execution, none of which has happened yet. GATED-skipping again (~150
  min) — no restamp attempted.
- 2026-08-15T15:03Z (slot-8, data_engineering): Re-checked live-deploy status ~3h after the slot-32 check — `b872799efa`
  (2026-08-15T09:09:54Z) is STILL not on `origin/main` (`git merge-base --is-ancestor` false, freshly fetched). `main`
  is now 1192 commits behind LDR overall, and `b872799efa` itself sits only 24 commits behind LDR's tip — i.e. it's near
  the FRONT of the queue once the batched promote pipeline catches up, but the backlog is deep enough (observed ~78
  commits/batch in the slot-32 window) that it hasn't reached it yet. Same conclusion as the two prior checks —
  genuinely still gated, not stalled. GATED-skipping again (180 min cap) — no restamp attempted.
- 2026-08-16 (slot-2, data_engineering, "docs only, no writes" session): Re-checked ~14h after the slot-8 check —
  `b872799efa` (2026-08-15T09:09:54Z) is STILL not on `origin/main` (`git merge-base --is-ancestor` false, freshly
  fetched both `main` and `live-defi-rollout`). It IS confirmed an ancestor of `live-defi-rollout` (never fell off
  LDR), but now sits 63 commits behind LDR's tip (up from 24 at the slot-8 check — LDR kept advancing faster than the
  promote pipeline consumed this position) and `main` is now 1219 commits behind LDR overall (up from 1192) — the
  backlog is deepening, not shrinking, but this reads as sustained promote-pipeline lag under continuous LDR growth,
  not a stall (no error signal, no stuck PR found). Same conclusion as all three prior checks: genuinely still gated.
  P1 (the manifest restamp) also remains outside this session's own authorization regardless of deploy state — this
  session is scoped to "docs only, no writes" (no manifest CAS writes permitted even once the fix is confirmed live).
  GATED-skipping again — next check should also verify actual redeploy + one post-deploy write cycle before anyone
  attempts the restamp, not just the promote-to-main landing.
- 2026-08-16 (slot-2, data_engineering, "docs only, no writes" session, second check same session): Re-checked again —
  `b872799efa` STILL not an ancestor of `origin/main` (fresh fetch). Now 71 commits behind LDR's tip (up from 63 at the
  prior check a few hours earlier) and `main` now 1225 commits behind LDR overall (up from 1219) — backlog continuing
  to widen, not narrow, but still reads as sustained promote-pipeline lag under continuous LDR growth, not a stall (no
  error signal, no stuck PR). Same conclusion as every prior check: genuinely still gated. P1 restamp remains outside
  this session's authorization regardless. GATED-skipping again.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).

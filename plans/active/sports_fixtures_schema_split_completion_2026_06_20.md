---
title: "Sports FIXTURES → SCHEDULE + OUTCOMES schema-split completion + announcement-floor + migration"
parent_epic: sports_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/sports_master.md
  - ../active/writegate_honest_coverage_endtoend_2026_05_06.md
---

> **Provenance**: extracted 2026-06-20 from the inline `sports_master` epic body during the asset-group-umbrella
> restructure (the L0 umbrellas carried stale May-08 inline todos the backlog regen never scanned because it only reads
> `plans/active/*.md`). This plan is the **open remainder** of the FIXTURES schema split (lookahead-bias fix): the UAC
> schema additions + UTL reader-join helper already SHIPPED (uac@c4058c68 / utl@b2f60f31, see § "Already shipped" below)
> — what stays OPEN is the per-league announcement-floor empirical audit, the cross-source `announced_at` backfill, the
> one-shot manifest split migration, the writegate same-day coordination, the HT/ET/PEN + score-distinction write-path
> population, and the deferred pre-features-extractor follow-up.
>
> Migrated from the epic's "FIXTURES schema split — SCHEDULE + OUTCOMES" + "Match HT/ET/PEN timestamps +
> score-distinction columns + pre-features extractor" sections (originally migrated from issues
> `fixtures_lookahead_bias_post_match_scores_2026_05_08` +
> `instruments_lifecycle_and_fixtures_endtime_cascade_2026_05_08`).

## Context

Today, post-match scores ride the same FIXTURES row as the schedule, and `available_at` uses an arbitrary `kickoff − 7d`
heuristic instead of real announcement time. Every sports feature compute that joins FIXTURES on schedule fields can
silently leak post-match scores into pre-match feature windows. The fix splits FIXTURES into `FIXTURES_SCHEDULE`
(`available_at = announced_at`) and `FIXTURES_OUTCOMES` (`available_at = match_end_time`, from the C.6 cascade already
shipped in the epic), with a reader-side join helper hiding the split from consumers.

**Cross-plan banner — writegate strict-mode**: writegate Phase 2.D `available_at` strict-mode enforcement (already
shipped) flips this to a hard-fail once the new entity-split lands. The entity-folder split + migration + writegate
same-day flip MUST ship in a single coordinated unit so writegate doesn't break sports parquets mid-migration.
Coordinate with [`writegate_honest_coverage_endtoend_2026_05_06`](./writegate_honest_coverage_endtoend_2026_05_06.md).
This is also a **single-walk** migration (CLAUDE.md HARD RULE) — bundle the entity-folder split into the gated
walk-after step; do NOT open an independent whole-corpus GCS walk.

## P0 — announcement-floor + manifest split migration + writegate coordination

- [x] [SCRIPT] P0. Per-league announcement-floor empirical audit (Phase 2 of source issue): 2-week observation window
      per league; record api_football fixture-publication-time vs `kickoff_time`. Output: per-league
      `ANNOUNCEMENT_FLOOR_HOURS` table in UAC `unified_api_contracts.canonical.crosscutting.availability_semantics`
      (replacing the `kickoff−7d` heuristic). Default 14d for unobserved leagues; per-league override once observed.
      Repo: unified-api-contracts. <!-- unified-api-contracts@723e3b3 2026-06-16 -->
- [ ] [SCRIPT] P1. Cross-source backfill for historical `announced_at` where api_football didn't capture it (Phase 3
      optional): footystats + SFI publication-time as fallback; stamp at write-time during the migration. Repo:
      instruments-service.
- [x] ✅ [SCRIPT] P0. One-shot manifest migration: existing `entity=fixtures` rows split into `entity=fixtures_schedule` +
      `entity=fixtures_outcomes`. Script `instruments-service/scripts/migrate_fixtures_split.py` mirroring the existing
      `migrate_sports_available_at_column.py` pattern (idempotent, per-blob CAS, dry-run + apply). Repo:
      instruments-service.
      — instruments-service@3f8b6a9 | CAS-idempotent split, schedule/outcomes column partition per OUTCOME_COLUMNS, dry-run+apply, --overwrite flag
- [x] [QG] P0. Coordinate with writegate Phase 2.D — the schema-split (writer-emit + entity-folder split) commit must
      ship same-day as the writegate strict-mode-flip-on-FIXTURES (avoid mid-migration hard-fail). Single coordinated
      unit with the migration above.
      — coordination analysis 2026-06-16: `_WRITE_GATE = InstrumentsWriteGate(mode="warn")` at
        `instruments_service/engine/orchestrator/__init__.py:204` — global scope, no entity-level granularity needed.
        Strict-mode flip = single-line change at that site. Protocol confirmed: (1) UAC announcement-floor ships first
        (independent); (2) SINGLE instruments-service quickmerge batch: writer entity-split (entity=fixtures →
        entity=fixtures_schedule + entity=fixtures_outcomes) + `mode="warn"` → `mode="strict"` + migration script run
        = no mid-migration window where writegate rejects old entity=fixtures writes. **Blocked pending**: upstream
        `[SCRIPT] P0` announcement-floor audit + `[SCRIPT] P0` migrate_fixtures_split.py (must ship before this flip
        can activate — the quickmerge batch for the flip is gated on those tasks completing).

## P0 — HT/ET/PEN phase-timestamp + score-distinction write-path population

> The UAC schema fields are already additive on `CanonicalFixtureSchedule` (Q5: HT/ET/PEN phase timestamps) +
> `CanonicalFixtureOutcomes` (Q6: regulation/ET/PEN score-distinction + match_result) — shipped uac@c4058c68. The open
> piece is populating them from api_football at instruments-service write-time (the IS Phase-3 piece).

- [ ] [VERIFY] P0. After the writer populates Q5/Q6 columns + the entity-split lands, confirm `FIXTURES_SCHEDULE`
      carries the 9 HT/ET/PEN phase-timestamp columns and `FIXTURES_OUTCOMES` carries the 11 score-distinction columns
      populated for completed fixtures (regulation / ET-only / ET+PEN cases; NEVER collapse pen-shootout score into a
      single field). Spot-check on real GCS rows for a completed matchweek across the Top-5 EU leagues. **[VERIFY][UI]**
      the deployment-ui schema modal renders both entity schemas — this touches a UI repo, so any tick requires
      `pw:L2 ✓` (`npx playwright test --project=chromium tests/smoke/`) + a cited regression spec per CLAUDE.md UI
      playwright-gate HARD RULE; on a fleet VM with no dev server, keep `[BLOCKED-PLAYWRIGHT]`.
- [ ] [SCRIPT] P1. **DEFERRED** follow-up: if features-sports HT-feature work grows past 3 calculators, extract
      `match_lifecycle_extractor` into a dedicated pre-features service stage (Q7 option (b)). Not scoped now per
      operator direction 2026-05-08 (operator chose Option (a) — UTL helper at instruments-service write-time). Named
      successor for the deferral = this plan line; revisit when the 3-calculator threshold is crossed.

## Already shipped (flipped in the epic — listed for context, NOT re-opened)

- UAC schema additions (additive, NOT a rename): `CanonicalFixtureSchedule` + `CanonicalFixtureOutcomes` + `MatchResult`
  - `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` constants + `MatchLifecycle` — uac@c4058c68.
- UTL reader-side join: `read_fixtures_joined(day, league_id)` + `read_fixtures_outcomes_pit_safe` (per-row
  LookaheadBiasError on outcome-column read before `outcomes_available_at`) — utl@b2f60f31.
- UTL `extract_match_lifecycle(af_response) -> MatchLifecycle` + IS write-time call (Q5/Q6 columns additive on
  entity=fixtures rows) — utl@b2f60f31 / is@9de5ac87; 16 UTL + IS column tests.
- The full `match_end_time` cascade (C.6) feeding `FIXTURES_OUTCOMES.available_at` — shipped in the epic 2026-05-23.

## Success criteria

- Per-league `ANNOUNCEMENT_FLOOR_HOURS` table replaces the `kickoff−7d` heuristic in UAC; historical `announced_at`
  backfilled where capturable.
- `migrate_fixtures_split.py` splits every `entity=fixtures` row into `entity=fixtures_schedule` +
  `entity=fixtures_outcomes` (idempotent, per-blob CAS, dry-run-then-apply), shipped same-day as the writegate
  strict-mode flip so no mid-migration hard-fail.
- HT/ET/PEN phase timestamps + score-distinction columns populated at write-time for completed fixtures and verified on
  real GCS rows (and in the deployment-ui schema modal behind the playwright gate).
- `bash scripts/quality-gates.sh` green on `unified-api-contracts` + `instruments-service` before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the announcement-floor audit runs on real
api_football publication-time data; `migrate_fixtures_split.py` runs to completion on the real sports buckets (base +
PRD) with manifest-verified split-entity row counts and a sample-inspected parquet; the writegate strict-mode flip is
confirmed green on a post-migration sports backfill smoke.

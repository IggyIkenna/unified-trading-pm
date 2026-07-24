---
doc_type: issue
title: sports_closeout_batch1_ao_ready-018 (CLEANUP P3) — 2 of 3 sub-parts SHIPPED, 1 (GCS scaffolding purge) still open
summary:
  "Compound [CLEANUP] P3 todo (drop frozen 2018-2020 markets/outcomes/settlements/arbitrage_opportunity GCS scaffolding
  + correct SPORTS_INSTRUMENTS.md's stale lineups-strip claim + add a non-ASCII junk-symbol guard for fixture names). 2
  of 3 sub-parts SHIPPED: SPORTS_INSTRUMENTS.md doc correction (instruments-service@97fbea22) and the junk-symbol guard
  + tests (unified-api-contracts@a6346f95). The 3rd sub-part (locating + purging the frozen 2018-2020 GCS scaffolding)
  remains open — the exact bucket/path was not quickly locatable via grep and a live-bucket delete needs real
  confirmation, not a guess under time pressure."
status: open
nature: record
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, instruments-service, unified-trading-pm]
scope: [engineer]
tags: [sports, cleanup, partial-progress, qg-red, handoff]
related: [/plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md]
created: 2026-07-24
parent_epic: sports_master
assigned_vm: planning
resolved_by:
source: [sports_closeout_batch1_ao_ready_2026_07_24.md todo 18 (dispatched to slot 10)]
priority: P3
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

# sports_closeout_batch1_ao_ready-018 — partial progress + handoff

## What I found / did

Working the compound `[CLEANUP] P3` todo (`sports_closeout_batch1_ao_ready_2026_07_24.md` line ~404), 3 sub-parts:

1. **Correct `SPORTS_INSTRUMENTS.md`'s stale "lineups player-id strip" claim** — DONE, staged uncommitted in
   `instruments-service` (`docs/SPORTS_INSTRUMENTS.md`, +16/-8 lines). Verified false at the code level: the
   API-Football adapter's `get_fixture_lineups()`
   (`instruments_service/reference_data/adapters/sports/adapters/api_football.py:918`) already calls
   `normalize_api_football_lineup()` to flatten each team's raw lineup block into ONE FLAT dict per (fixture, team,
   player) — `player_id` lands as a plain scalar column — BEFORE rows ever reach `_prepare_fixture_entity_df`'s
   nested-column-drop guard (`sports_reference_fixtures.py:596-615`). That guard only drops columns still holding raw
   `dict`/`list` values; by the time lineup rows reach it there is nothing nested left to strip, so `player_id` was
   never actually at risk from this code path — the doc's claimed MECHANISM was wrong. Confirmed
   `entity=fixture_lineups` genuinely has 0 objects across 5 sampled recent dates (2026-04-15, 2026-06-13, 2026-06-20,
   2026-07-16, 2026-07-18) in
   `instruments-store-sports-prd-central-element-323112/sports_reference/by_date/day={date}/entity=fixture_lineups/` —
   the entity is dormant, not stripped; the doc now says so accurately.
2. **Add a junk-symbol guard rejecting non-ASCII characters in fixture names** — DONE, staged uncommitted in
   `unified-api-contracts` (`unified_api_contracts/canonical/domain/sports/canonical_ids.py` +36/-1,
   `tests/unit/sports/test_canonical_ids_junk_guard.py` new, 5 tests, all pass locally
   `uv run pytest tests/unit/sports/test_canonical_ids_junk_guard.py -q` → 5 passed). "Fixture names" is not a distinct
   concept in the codebase — team/league/player/venue names all funnel through the shared `_slug()` helper, which is
   where the guard was added (`_reject_junk_symbols`, called at the top of `_slug`). It rejects the Unicode replacement
   character (U+FFFD, the canonical mojibake/decode-failure marker) and C0 control characters — genuine corruption, not
   legitimate non-ASCII — while still letting real accented names (e.g. "México", "São Paulo") pass through to `_slug`'s
   existing diacritic-stripping unchanged (verified by a dedicated test, `test_slug_allows_legitimate_diacritics`). A
   blanket "reject all non-ASCII" would have broken real international team/league names, so the guard is deliberately
   narrower than the todo's literal wording.
3. **Drop the frozen 2018-2020 `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` GCS scaffolding** — NOT
   STARTED. Grepped for `entity=markets`/`entity=outcomes`/`entity=settlements`/`data_type=markets` etc. across
   `instruments-service`, `market-tick-data-service`, `market-data-processing-service` — no exact-literal hits (a
   plain-English grep for `"markets"`/`"outcomes"`/`"settlements"` matches dozens of unrelated prediction-market /
   DeFi-lending-market call sites, not useful for narrowing). The parent audit
   (`sports_consolidated_audit_2026_07_19.md:206`) names the finding but not a bucket/path. This needs a
   reconciliation-style bounded GCS listing (per `/data-pipeline-reconciliation` conventions — snapshot before any
   delete, never a corpus-wide walk) to actually locate the scaffolding before anything is deleted; not something to
   guess at under time pressure on a prod bucket.

## Why staged, not shipped

QG did not confirm green for either repo before this session had to checkpoint on high context usage (`/pre-compact`):

- **unified-api-contracts**: the first QG run failed on a trivial lint issue (import order in the new test file), fixed
  with `uv run ruff check --fix` (confirmed 1 fixed, 0 remaining). The re-run was still in progress (last seen at the
  `[3/6] TESTS` stage) when the harness killed the background task at session checkpoint. Not a known failure —
  genuinely unconfirmed, needs a fresh full run.
- **instruments-service**: QG genuinely FAILED, but on `[6/6] PRODUCTION READINESS VALIDATORS`, NOT on anything touching
  `docs/SPORTS_INSTRUMENTS.md`. Reproduced standalone:
  `python3 unified-trading-pm/scripts/run_validators.py --scope all` →
  `BROKEN: active/active_plan_inventory_dashboard_2026_07_24.md -> ./data_pipeline_alerts_batch_remediation_closeout_2026_07_24.md`
  — a stale auto-generated inventory-table row pointing at a plan that shows 14/14 (100%) done, most likely just
  archived by a concurrent slot with the dashboard not yet regenerated. Confirmed pre-existing and unrelated to this
  diff (the touched file is in a different repo entirely). Did NOT attempt to fix it myself:
  `active_plan_inventory_dashboard_2026_07_24.md` is an auto-generated file that many slots touch concurrently (observed
  several other slots' plan-flip commits landing during this session) — editing it blind under compaction time-pressure
  risked colliding with in-flight work from another slot, which the multi-agent-safety rules explicitly warn against.

## Recommended decision / next steps

- [x] [CODE] P3. ✅ Re-ran `bash scripts/quality-gates.sh` fresh in `unified-api-contracts` for the junk-symbol guard +
      test file — first attempt hit a trivial import-order lint (fixed via `uv run ruff check --fix`), re-run passed
      clean (428s; the `partition_paths.py` 900-line flag seen mid-run is warn-only, does not gate exit code — confirmed
      pre-existing, untouched by this diff). Shipped `unified-api-contracts@a6346f95`.
- [x] [CODE] P3. ✅ Confirmed already fixed: `python3 scripts/run_validators.py --scope all` now reports "OK: No broken
      links in plans/active/*.md" clean (the stale row referencing
      `data_pipeline_alerts_batch_remediation_closeout_2026_07_24.md` is gone — a subsequent inventory regen by another
      slot resolved it; that target plan file no longer exists anywhere, active or archived, confirming the archival
      completed). Recreated the staged `docs/SPORTS_INSTRUMENTS.md` diff (slot 10's fix lived only in its own `.tabs/10`
      worktree, not visible to this slot) verbatim in this slot's worktree (diffed byte-identical against slot 10's
      staged content before shipping), QG green, shipped `instruments-service@97fbea22`.
- [ ] [DATA] P3. Locate the actual GCS bucket/path for the frozen 2018-2020 `markets`/`outcomes`/`settlements`/
      `arbitrage_opportunity` scaffolding (bounded listing, not a corpus walk), confirm no live reader/writer (mirror
      the diligence already done for the dead dimension-groups purge in `sports_closeout_batch1_ao_ready_2026_07_24.md`
      todo 12's sibling), snapshot first, then purge. **Done when**: a listing for the scaffolding prefix returns 0
      objects post-purge, with the pre-purge snapshot location cited.
- [ ] [DOC] P3. Once all 3 sub-parts above are shipped, flip `sports_closeout_batch1_ao_ready_2026_07_24.md`'s
      `[CLEANUP] P3` todo (currently still `[ ]`) to `[x]` citing all 3 SHAs, and close this issue doc.

## Progress Log

- 2026-07-24 (slot 10): staged both code changes (sub-parts 1+2 of 3), QG unconfirmed on both for the reasons above;
  filed this doc rather than leave the state undocumented at session checkpoint.
- 2026-07-24 (slot-6): worked the recommended-next-steps item 2 (validator + SPORTS_INSTRUMENTS.md sub-part 1) — see the
  flipped checkbox above. Sub-part 2 (the junk-symbol guard in unified-api-contracts) and sub-part 3 (locating the
  2018-2020 GCS scaffolding) remain open for whoever picks this up next.
- 2026-07-24 (slot 10, same session, continued past the checkpoint): shipped sub-part 2 —
  `unified-api-contracts@a6346f95`. Only sub-part 3 (the GCS scaffolding purge) remains open.

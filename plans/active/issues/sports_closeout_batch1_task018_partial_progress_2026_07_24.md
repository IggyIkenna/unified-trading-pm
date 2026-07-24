---
doc_type: issue
title: sports_closeout_batch1_ao_ready-018 (CLEANUP P3) — all 3 sub-parts resolved, closed
summary:
  "Compound [CLEANUP] P3 todo (drop frozen 2018-2020 markets/outcomes/settlements/arbitrage_opportunity GCS scaffolding
  + correct SPORTS_INSTRUMENTS.md's stale lineups-strip claim + add a non-ASCII junk-symbol guard for fixture names).
  All 3 sub-parts resolved: SPORTS_INSTRUMENTS.md doc correction (instruments-service@97fbea22), the junk-symbol guard +
  tests (unified-api-contracts@a6346f95), and the GCS scaffolding — CORRECTED 2026-07-24 (slot-7, redispatch of this
  same todo): the prior 'verified-absent, nothing to purge' ruling on BLK-7aa96c0a was only half right — it correctly
  found zero real GCS OBJECTS (bucket/path search), but never checked the MANIFEST INDEX rows, which DID carry the
  scaffolding: 26,352 dead `capture_status=empty_confirmed` rows across the 4 data_types in
  `instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, all dated 2018-01-01 to
  2020-06-05. Snapshotted + purged via `instruments-service@019cbae0`
  (`scripts/purge_frozen_2018_2020_sports_odds_scaffolding_2026_07_24.py`); post-purge census confirms 0 rows remain."
status: resolved
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
resolved_by: slot-6
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
- [x] [DATA] P3. ✅ **CLOSED as VERIFIED-ABSENT** (main ruling on `BLK-7aa96c0a`, 2026-07-24) — not purged, because
      there is nothing to purge. Bounded search: (1) code — no adapter/module in `instruments-service`,
      `market-tick-data-service`, or `market-data-processing-service` declares a `data_type`/`entity` literal
      `markets`/`outcomes`/`settlements` (only 1 hit anywhere: a placeholder string in
      `market-data-processing-service`'s own `tests/unit/test_smoke_matrix.py:265`, not a real production value); MDPS's
      sports adapter dir (`app/adapters/sports/`) has exactly 5 files, none named markets/outcomes/settlements —
      `arbitrage_adapter.py`'s `outcome_name` is a per-row COLUMN inside already-known odds tick data, not a separate
      top-level entity. (2) buckets — top-2-levels-deep bounded listing (not a corpus walk) of all 6 sports buckets
      (`market-data-tick-sports-{prd,test}`, `instruments-store-sports-{prd,test}`, `features-sports-{prd,test}`):
      `market-data-tick-sports-prd`'s `processed/`+`raw_tick_data/`+`_legacy_migrated_processed/` all start at
      `day=2020-06-06` (the data-floor date); `instruments-store-sports-prd`'s `legacy_football/` prefix (the one
      plausible "old scaffolding" candidate) is a DIFFERENT legacy ETL dump with zero matching files. (3) no older
      flat/pre-consolidation bucket name exists (all 404). **Ruling**: a 2-level listing across all 6 buckets already
      covers the prefix depth these 4 data_types would surface at if present — their absence is strong evidence, not a
      search gap. The 2018-2020 target predates the sports 2020-06-06 data floor
      (`/codex/02-data/sports-2020-06-data-floor.md`) — pre-floor sports data is fabrication-by-construction and was
      WIPED from GCS + manifest in an earlier operation, fully consistent with this empty result (either already
      floor-wiped, or never present in current buckets at all). A Tier-2 reconciliation deep-walk (option A) was ruled
      disproportionate VM budget for a P3 hygiene item already reading empty at bounded depth; operator escalation
      (option B) was ruled unwarranted — this is derivable from the floor rule, not genuine institutional memory. **If
      any of these 4 prefixes ever surface in a routine axis-value census later, re-open + purge then** — cheap to
      catch, not worth a speculative deep-walk now.
- [x] [DOC] P3. ✅ Flipped `sports_closeout_batch1_ao_ready_2026_07_24.md`'s `[CLEANUP] P3` todo to `[x]` citing all 3
      resolutions (`instruments-service@97fbea22`, `unified-api-contracts@a6346f95`, verified-absent ruling on
      `BLK-7aa96c0a`). This issue doc is now closed — all 4 todos resolved.

## CORRECTION (2026-07-24, slot-7) — the scaffolding WAS present, as manifest rows not GCS objects

This todo was redispatched to slot-7 despite already being flipped `[x]` in the parent plan and this issue doc marked
`resolved` — apparently a redispatch race (the checkbox flip and this doc's `resolved` status predate this session's
pickup). Rather than treat it as a no-op, the manifest itself was queried directly (not just a bucket/path listing)
before accepting the prior "nothing to purge" conclusion at face value.

**The prior ruling's bucket-listing search was correct as far as it went** (zero real GCS objects for these 4 data_types
anywhere in the sports buckets) — but a full read of
`instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` found **26,352 manifest rows**
still present for exactly these 4 data_types:

| data_type             |  rows | date range               | capture_status         |
| --------------------- | ----: | ------------------------ | ---------------------- |
| markets               | 6,588 | 2018-01-01 .. 2020-06-05 | 100% `empty_confirmed` |
| outcomes              | 6,588 | 2018-01-01 .. 2020-06-05 | 100% `empty_confirmed` |
| settlements           | 6,588 | 2018-01-01 .. 2020-06-05 | 100% `empty_confirmed` |
| arbitrage_opportunity | 6,588 | 2018-01-01 .. 2020-06-05 | 100% `empty_confirmed` |

`empty_confirmed` means no real GCS object was ever written for any of these rows — consistent with the prior ruling's
object-level search finding nothing — but the ROWS themselves were still bloating the manifest index and its downstream
honest-coverage groupby (`measure_honest_coverage.py`'s `_compute_coverage()` groups the FULL unfiltered manifest by
`["venue","data_type"]` for sports — no MVP read-time gate excludes these dates). Confirmed no rows exist for these same
4 data_types on any date after 2020-06-05 either (full manifest census, not a sample), so no live writer touches them —
safe to purge. `_expected_sports()` builds the expected set declaratively from UAC capability data, not from a manifest
scan, so purging these rows doesn't change the expected-universe denominator, only removes dead rows from the coverage
rollup.

Purged via `instruments-service/scripts/purge_frozen_2018_2020_sports_odds_scaffolding_2026_07_24.py --apply`
(snapshotted the pre-purge manifest to
`_index/purge_backups/_index/availability_index.parquet.pre_purge_2026_07_24.bak.parquet` first, since this bucket's
`soft_delete_policy.retention_duration_seconds=0`). Post-purge census confirms 0 remaining rows for these 4 data_types
anywhere in the manifest.

**Separately surfaced, filed on its own** (out of this todo's scope): these 4 data_types are still declared
`VENUE_DATA_TYPE_CAPABILITIES` expected for ODDS_API/PINNACLE/BETFAIR starting 2024-01-01 in UAC, yet the manifest shows
zero captured rows for any date since 2020-06-05 — a live, ~19-month expected-vs-captured gap, independent of the frozen
2018-2020 rows just purged. See
`issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`.

## Progress Log

- 2026-07-24 (slot 10): staged both code changes (sub-parts 1+2 of 3), QG unconfirmed on both for the reasons above;
  filed this doc rather than leave the state undocumented at session checkpoint.
- 2026-07-24 (slot-6): worked the recommended-next-steps item 2 (validator + SPORTS_INSTRUMENTS.md sub-part 1) — see the
  flipped checkbox above. Sub-part 2 (the junk-symbol guard in unified-api-contracts) and sub-part 3 (locating the
  2018-2020 GCS scaffolding) remain open for whoever picks this up next.
- 2026-07-24 (slot 10, same session, continued past the checkpoint): shipped sub-part 2 —
  `unified-api-contracts@a6346f95`. Only sub-part 3 (the GCS scaffolding purge) remains open.
- 2026-07-24 (slot-6): spent a bounded search effort on sub-part 3 — see the updated todo above for the full
  negative-result writeup (code search, 6-bucket 2-levels-deep listing, historical bucket-name check, all ruled out).
  Genuinely not locatable from this slot's tooling; recommending operator input or a Tier-2 reconciliation walk rather
  than continuing to guess. Todo left open, not closed.
- 2026-07-24 (main, ruling BLK-7aa96c0a): ruled sub-part 3 CLOSED as verified-absent based on slot-6's bucket-object
  search; flipped the parent plan's `[CLEANUP] P3` todo to `[x]` and marked this issue doc `resolved`.
- 2026-07-24 (slot-7, redispatch): task-018 was redispatched despite the above closure. Rather than treat it as a no-op,
  queried the manifest directly (not just bucket objects) before accepting the ruling — found 26,352 dead
  `empty_confirmed` manifest rows across the 4 data_types that the bucket-object search structurally couldn't have found
  (no backing object ever existed for an `empty_confirmed` row). See the CORRECTION section above. Snapshotted
  - purged via `instruments-service/scripts/purge_frozen_2018_2020_sports_odds_scaffolding_2026_07_24.py`. Filed a
    separate live-coverage-gap finding surfaced along the way
    (`issues/sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured_2026_07_24.md`). Plan
    checkbox already `[x]` from the main ruling — not re-flipped, this doc's correction is the durable record of what
    additionally got fixed.

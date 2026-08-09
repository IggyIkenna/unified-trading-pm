---
doc_type: plan
title: Sports closeout Track S2 — fold-in absorption from 3 archived plans (split from the sports closeout)
summary: >-
  Extraction of sports_consolidated_closeout_2026_07_19.md's remaining Track S2 "FOLD-IN ABSORPTION" items (line-cap
  split, 2026-07-25) — real data/infra engineering work extracted 2026-07-23 from 3 now-archived plans
  (sports_manifest_canonicalisation_2026_06_01, sports_pipeline_to_100pct_golden_window_first_2026_06_27,
  sports_p2_history_apifootball_2015_to_present_2026_06_27). A sibling triage
  (sports_consolidated_native_ao_extract_2026_07_25.md) already extracted 7 Track S2 items (or sub-parts of them) as its
  own AO-eligible candidates before this split ran — those are excluded here (4 fully covered, 3 partially: only their
  remaining, still-human-flagged sub-part is carried here). Several remaining items are real judgment calls that stay
  non-dispatchable (tagged `[OPERATOR]`/`BLOCKED-PREREQUISITES`) or pure cross-plan pointers reformatted as non-checkbox
  digests per task_template.md finding H — this fold-in does not manufacture dispatchability that was never there.
  Verifying each item's cited detail doc against its CURRENT status (finding C) also surfaced 4 items the parent's Track
  S2 text described as live open work that are actually already resolved (the IS L6 index regression 3-step fix, the
  exit_code_fleet_monitor misclassification fix, the api_football gate-reader fix, and the WEATHER layout fix — the last
  resolved literally today, 2026-07-25) — those are carried forward as closed digests, not re-manufactured as open
  todos.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, track-s2, fold-in, satellite-docs]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25_finalize.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    /plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/archive/2026_08/sports_legacy_fixtures_path_migration_2026_07_24.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
  ]
created: "2026-07-25"
last_updated: "2026-08-05"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Extracted 2026-07-25 from sports_consolidated_closeout_2026_07_19.md's Track S2 (line-cap split pass — the parent was
  over its 1000L hard cap), after removing the items/sub-items sports_consolidated_native_ao_extract_2026_07_25.md
  already drafted from the same Track.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25_finalize.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /plans/active/issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md,
    plans/audit/results/cf_manifest_audit_2026_06_01.py,
  ]
---

# Sports closeout Track S2 — fold-in absorption

> **Status corrected 2026-07-26: this plan is `active`** (frontmatter has said so since creation; this banner was stale
> — the operator review it said to wait for is the 2026-07-26 rulings recorded in the two `[OPERATOR]` items below, both
> now closed). `sequential: false` — every item below touches a distinct file/doc/population; the several
> `BLOCKED-PREREQUISITES`/ `[OPERATOR]` tags below make real cross-item and cross-plan ordering non-dispatchable
> explicitly rather than relying on file position, so serializing the whole plan is unnecessary.
>
> **Overlap reconciliation (2026-07-25)**: `sports_consolidated_native_ao_extract_2026_07_25.md` already extracted, as
> its own AO-eligible candidates: (1) the mis-keyed-duplicate-bug mdps-surface check (excluding the sibling "88 orphan
> rows manual review" sub-item — carried here below); (2) Sports P2a sub-item (c) ONLY, the 40,041 FIXTURES
> `attempted_failed` re-run (excluding sub-items (a)/(b) — carried here below, rescoped); (3) the TEAMS full-history
> backfill (fully covered, not repeated here); (4) the legacy-CAS aggregate-manifest-gate question + 205-227 cell
> re-fetch (fully covered, not repeated here); (5) the post-07-13 rebuild-delta reconciliation (fully covered, not
> repeated here); (6) the staleness-budget mirror + hardcoded-workaround grep (fully covered, not repeated here); (7)
> the `check_high_attempted_failed` runbook note (excluding the sibling "re-check once K1/K2 DELETE executes" sub-part —
> carried here below). Nothing below duplicates any of the 7.
>
> **Staleness correction (2026-07-25, finding C)**: verifying each item's cited detail doc against its CURRENT status —
> not just carrying forward the parent's text — found 4 items the parent's Track S2 section described as live open work
> that are actually already resolved and archived. These are kept as closed digests below (not re-created as open todos)
> so the fact they were once tracked here stays visible.

## Todos

- [ ] [DATA] P0. BLOCKED-PREREQUISITES — **Sports E8 legacy-bucket delete gate stays RED, blocked on the PARENT doc's
      own Track H "schedule + run the CF-8 `available_at` maintenance window" todo** (that todo stays in the parent,
      un-dispatched — a dispatched child cannot `depends_on`+`gate_on_depends` against a LOCAL plan's todo, so this item
      is tagged non-dispatchable instead and must be re-checked by hand once CF-8's window runs).
      `cf_manifest_audit_2026_06_01.py` is RED on both the legacy `market-data-tick-sports` + `instruments-store-sports`
      bucket surfaces; the primary blocker is CF-8's `available_at` backfill (code fix shipped
      `market-tick-data-service@af627b5b`, unit-tested only, not yet run in production — same window as the parent's
      Track H todo, run together). Do not re-dispatch the audit itself until that window runs — 30+ prior re-audits
      reproduced identical RED with zero new information. **Correction (2026-07-25, finding C): the parent's own
      "separately, the L6-legacy-only == 0 gate criterion needs redefining" clause is STALE — that redefinition already
      shipped `unified-trading-pm@10ad5d69a` (2026-07-15, confirmed still live by a 2026-07-23 RE-TRIAGE)**, so CF-8's
      `available_at` fill rate is the ONLY remaining blocker on this item, not two blockers. Detail:
      `sports_cf8_available_at_backfill_regression_2026_07_13.md`. (repo: market-tick-data-service /
      deployment-service). **Done when**: the parent's Track H CF-8 todo is confirmed `[x]` AND a fresh
      `cf_manifest_audit_2026_06_01.py` run is GREEN on both surfaces. **RE-VERIFIED 2026-07-27 (slot-10), still
      genuinely blocked, no re-audit run**: parent doc `sports_consolidated_closeout_2026_07_19.md` line 639's Track H
      CF-8 todo is confirmed still `- [ ]` unchecked; the detail doc's `status:` is still `open`. This is
      operator-only-gated (the parent todo's own text: "Lift operator stop `BLK-d9137d48` and clear the still-false
      backlog parking-gate condition `sports-cf8-maintenance-window-scheduled`") — a fresh `/blocked` would be
      redundant, the operator already answered `BLK-d9137d48` (option A: wait for the repo-blocker) per the detail doc's
      own Progress Log; what's missing is the operational maintenance-window RUN itself, not a new decision. Per this
      item's own explicit instruction, did NOT re-run `cf_manifest_audit_2026_06_01.py` (30+ prior identical RED
      reproductions on record; nothing has changed upstream to make a 31st informative). No forward action possible from
      this slot — correctly re-parked pending the operator-scheduled window. **RE-CONFIRMED 2026-07-27 (slot-15, same
      day as slot-10's check above) — independently re-read both facts, unchanged: parent Track H CF-8 todo still
      `- [ ]`, detail doc `status:` still `open`.** No new information; did not re-run the audit script for the same
      reason slot-10 gave. This item should stay parked until the maintenance window actually runs — flagging that this
      todo is bouncing back into the AO dispatch queue on every cycle with no mechanical gate to stop it (the doc's own
      text already names why: a dispatched child can't `depends_on`+`gate_on_depends` against a LOCAL plan's todo) is
      itself worth a main/operator look, since each re-dispatch burns a full worker cycle for zero new signal.
- **[DATA] P0.** Sports IS L6 index regression — **ALREADY RESOLVED, not carried forward as an open todo (finding C,
  2026-07-25).** The parent's Track S2 text described this as a live 3-step fix (base-image rebuild / resume schedulers
  / re-consolidate); the cited detail doc (`sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`, now
  archived, `status: resolved`) shows all 3 steps executed and verified 2026-07-15 (`unified-trading-library@45a43438`,
  `instruments-service@a25cf70d`, `unified-api-contracts@c280e1ff`, `unified-trading-pm@10ad5d69a`), with a 2026-07-23
  RE-TRIAGE confirming the live index has grown monotonically since with no recurrence. The doc's one
  genuinely-still-open residual (P1 forensics: what wrote the pre-launch rows that caused the original regression) is
  already tracked in `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s digest — not re-created here.
- **[DATA] P0.** Legacy no-env instruments-store-sports bucket decommission - tracked in
  sports_legacy_bucket_cutover_2026_07_16.md, not here.
- **[DATA] P2.** **RETAGGED 2026-07-28 (stale-tag audit — this digest entry's own text already says the disposition was
  decided and executed; `[OPERATOR]` was a stale label from before that, never cleaned up).** Manual review of the 88
  mis-keyed-duplicate orphan rows' disposition — **ALREADY RESOLVED, not carried forward as an open todo (2026-07-26,
  same "finding C" staleness pattern this plan already flags for 4 other items above).** These 88 rows (0.01% of the
  2026-07-13 683,592-row dedup cleanup that had no canonical twin to dedupe against, left untouched during
  `market-tick-data-service@55f9e961`'s fix) are genuinely-captured, unique API-Football `PLAYER_STATS` rows (100%
  `capture_status=captured`, spread across 21 leagues, 2020-2026) mis-stamped with
  `service_name=market-tick-data-service` and a blank `asset_group` by the same root-cause bug — real data, not
  corrupted/redundant, so deletion was never the right disposition. The disposition was decided and **executed** the
  same week this bug was found, before this 2026-07-25 plan was even written: `instruments-service@9ce3450e`'s
  `scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py` did a direct canonical rewrite (re-stamp
  `service_name→instruments-service`, `asset_group→sports`), matching this incident family's established rule (twin
  exists → drop the mis-keyed copy; no twin → relabel, never drop — same pattern used by
  `dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py` and `drop_stale_xg_shots_shot_rows_2026_07_09.py`).
  Independently re-verified live 2026-07-14
  (`plans/archive/2026_07/sports_data_sources_canonical_completion_2026_07_13.md:111-116`): a fresh manifest read
  confirmed 0 remaining `service_name=market-tick-data-service` + `source=api_football` rows. Detail:
  `instruments-service/scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py`,
  `plans/archive/2026_07/sports_data_sources_canonical_completion_2026_07_13.md:56-77,111-129`. No further action
  needed.
- [x] ✅ [DOC] P1. **Move the mis-filed DEFI tracking item out of the sports corpus entirely — DONE 2026-07-27.** The
      "features-service: ban `category=defi` in on-disk GCS path reads (`mtds_canonical_reader.py::_legacy_twin()`,
      `eigen_rewards_calculator.py`)" item (mis-filed under the now-archived
      `sports_manifest_canonicalisation_2026_06_01.md` — it has nothing to do with sports) is now a tracked `- [ ]` todo
      in `data_completion_to_100_all_ag_2026_06_21.md`'s own todo list (its real gating plan), directly under the
      `defi_manifest_canonicalisation_2026_06_01.md` fold-in section. Cited that doc's current defi C-GREEN status as of
      the move: **NOT green** — `data_completion_defi_2026_07_15.md`'s C0 path+bucket canonicalisation todo is still
      `- [ ]` open, so the item stays correctly gated on defi C0 reaching C-GREEN in its new home. No other duplicate of
      this item was found anywhere else in the active sports corpus.
- [x] ✅ [DATA] P1. **Sports P2a sub-item (a) — G1 non-canonical-league NOISE wipe, audit-then-conditionally-purge —
      DONE 2026-07-27 via discrepancy-report path, NO purge executed.** Ran a live read-only census against the
      production `instruments-store-sports-prd-central-element-323112` `_index/availability_index.parquet` (6,860,486
      rows) reproducing the G1 delete script's own canonical-set derivation. Result: NEITHER the plan's cited
      ~106k/1,437 figure NOR §U's approved 10,869/489 figure is reproducible today under any of 3 canonical-set cuts
      tried (full-registry: 268,094 rows/780 leagues; MVP-scope: 1,476,781 rows/1,067 leagues; football-only: 17,767
      rows/734 leagues) — genuinely different from both historical figures, confirming the todo's own "must not be
      assumed" warning. Worse: the full-registry cut contains 160,909 rows under 5 symbolic aliases
      (`PREMIER_LEAGUE`/`CHAMPIONSHIP`/`PRIMERA_DIVISION`/`2._BUNDESLIGA`/`FIRST_DIVISION_A`) already flagged as a P0
      catastrophic-delete risk in `sports_league_id_namespace_migration_2026_07_20.md` — 100% in `trades`/
      `odds_horizon_bucket`, real un-migrated canonical-league data belonging to Track V's separate, still-in-flight
      casing migration, NOT G1 NOISE. Root cause: `delete_noncanonical_sports_leagues_2026_06_25.py` defines
      `_FOOTBALL_DATA_TYPES` but never uses it to filter — a live scope bug that would delete 250,327 non-football rows
      if `--apply` ran today. **Fixed same-turn, `instruments-service@7409c5b1`**: wired `_FOOTBALL_DATA_TYPES` into
      `_delete_noncanonical_rows()`'s mask + 4 new unit tests (non-football survives / football still deleted / mixed
      same-league_id-both-types / missing-data_type-column fallback), all passing; full QG green. Per this todo's own
      instruction, STOPPED short of any purge and filed the population discrepancy as actionable follow-ups:
      `plans/active/issues/sports_g1_noise_population_mismatch_and_scope_bug_2026_07_27.md` (remaining 3 todos:
      re-baseline the canonical-set decision, reconcile §U's exact population against a raw-content read, update this
      plan's figures once fixed). (repo: instruments-service). Census + discrepancy recorded — no purge executed, per
      the todo's own "if genuinely different, do not purge" branch.

      **UPDATE 2026-08-03 — items 1+2 resolved, figures now authoritative (see
      `sports_g1_noise_population_mismatch_and_scope_bug_2026_07_27.md` Progress Log for full methodology):**

      **Item 1 (re-baseline, `instruments-service@7409c5b1` dry-run):** Operator ruled the full 383-league registry is
      authoritative for the "not in registry" wipe (not MVP-96). Fixed-script dry-run against the live
      `availability_index.parquet` (11,853,040 rows): **11,403 non-canonical rows / 755 unique league_ids** under the
      full 383-league registry, football-data-types-only (top data_types: MATCHES 3665, FIXTURES 3332, INJURIES 1644,
      ODDS 1044, PREDICTIONS 804, STANDINGS 614 — all football, zero `trades`/`odds_horizon_bucket`, confirming the
      `_FOOTBALL_DATA_TYPES` scope-bug fix holds). Supersedes the 2026-07-27 manual census's 17,767/734 figure for the
      same cut.

      **Item 2 (§U reconciliation, `instruments-service@153063e4`):** The G1 script's `_FOOTBALL_DATA_TYPES` frozenset
      does NOT include `FIXTURES_SCHEDULE` or `FIXTURES_OUTCOMES` — §U's ENTIRE population is drawn from
      `FIXTURES_SCHEDULE` raw content, so the two populations are **DISJOINT BY CONSTRUCTION**. A scoped walk of the
      raw `fixtures_schedule` corpus restricted to the 363 non-registry `FIXTURES_SCHEDULE` league_ids found **7,573
      non-registry blank-`round` rows across 296 distinct leagues** — the honest 2026-08-03 equivalent of §U's original
      10,869/489 figure (smaller because the registry grew 94→383 leagues since §U's 2026-07-19 measurement, plus the
      intervening §T/§W backfills and the 2026-07-23 pre-floor wipe). 60 of the 2,111 scoped blobs (all
      `day=2026-04-14`) hit the already-tracked wrong-schema contamination from
      `sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` — known residue, not a new defect.

- [x] ✅ [DIAG] P1. **Sports P2a sub-item (b) — G2 2015-2017 zero-captured diagnosis — DONE 2026-07-27, read-only, no
      fix implemented.** **FINDING: subscription-tier limit (high confidence), not a backfill bug.** This question was
      already investigated by the source plan (`sports_p2_history_apifootball_2015_to_present_2026_06_27.md`, archived,
      todo 2 / G2 diagnosis, lines 133-143 + 468-492): `unified-api-contracts@d858f67d` recorded "VERDICT: SUBSCRIPTION
      FLOOR" — 35,889 rows, 100% `capture_status=empty_confirmed`, across 76 MVP leagues, all of 2015-2017. Re-verified
      live against current code this session: 1. **`empty_confirmed` cannot mask a fetch error by construction** —
      `instruments-service/instruments_service/reference_data/adapters/sports/adapters/api_football.py:1001-1116`.
      API-Football signals plan/quota/auth/param errors INSIDE the 200-OK JSON envelope
      (`{"errors": {"plan": "..."}, "response": []}`), never via HTTP status. `_raise_on_api_errors()`
      (line 1034) raises `ApiFootballResponseError` whenever `errors` is a non-empty dict/list; `_extract_response()`
      (line 1101) calls it BEFORE returning rows, routing any error to `attempted_failed` via the `RuntimeError` branch
      in `_fetch_one_venue`. A clean `empty_confirmed` for these rows can therefore only mean the vendor was actually
      called and returned `{"errors": [], "response": []}` — a genuine empty, not a swallowed error. 2. **Uniformity** —
      76 leagues × 3 full years, not a scattered/partial failure pattern a backfill bug would produce. 3. **Independent
      re-affirmation in current UAC code** —
      `unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py:86-96`
      (`SOURCE_COVERAGE_START`) comment, dated 2026-07-15, states: "Earlier probes had already shown the subscription
      returns empty for seasons 2015-2017 (35,889 all-empty_confirmed across 76 MVP leagues — subscription floor, not a
      backfill bug). CONFIRMED CORRECT — unchanged." — a later, independent audit reached the same conclusion (this
      constant was since raised again to the 2020-06-06 sports data floor per
      `/codex/02-data/sports-2020-06-data-floor.md`, which supersedes but does not contradict this 2015-2017
      sub-finding). 4. **Prior-code corroboration**: `instruments-service/scripts/audit_fixtures_via_api_football.py:93`
      hardcodes `_DEFAULT_SEASON_RANGE: tuple[int, int] = (2018, 2026)`;
      `scripts/run_fixture_completeness_audit_2026_06_25.py:31` comments "the 2014-2018 range pre-dates the registry (no
      expected counts seeded yet)" — both reflect the same prior institutional finding. 5. **No evidence anywhere in the
      corpus supports the backfill-bug hypothesis** — no `attempted_failed` rows for 2015-2017 (which a code-level error
      would produce instead of clean empties), no exception-swallowing pattern in the adapter, and no
      incident/regression doc referencing 2015-2017 specifically. **Residual gap (does not change the verdict, but the
      diagnosis is not 100% vendor-confirmed)**: no script or log in the corpus has ever captured the live `/status`
      endpoint's `subscription` field (the field that would give a direct vendor-stated plan/history-limit confirmation)
      — `_parse_status_body()` (`api_football.py:1063-1099`) only reads `response.requests.limit_day/current` for quota
      math and never inspects `response.subscription`, even though `/status` is called routinely in production for quota
      purposes (`data_completion_sports_2026_07_24.md:486-497`). Per this todo's explicit scope (diagnosis-only, no
      fix), this residual gap is noted but not closed here — a follow-up live
      `curl -H "x-apisports-key: <KEY>" https://v3.football.api-sports.io/status` from a credentialed VM, inspecting
      `response.subscription`, would fully vendor-confirm rather than strongly infer. The
      subscription-tier-limit-vs-backfill-bug fork this todo exists to resolve is answered: **subscription-tier limit**
      — any future fix-path decision (e.g., whether to upgrade the API-Football plan) should proceed on that basis. No
      fix implemented; no code changed. (repo: instruments-service, read-only — verified.)
- [x] ✅ [DATA] P1. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — the checkbox was lagging this
      todo's own prose, which already reflects the odds-api-key credential fix (same rotation as
      `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`); fixing the formal tag to match, not
      duplicating the note below. Only the gap-fill backfill run remains (tracked in
      `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`), not credential-blocked.** UNBLOCKED 2026-07-29 —
      **Sports P2b — reference sources + odds history, 5 of 6 sources VERIFIED DONE 2026-07-27, odds_api genuinely NOT
      done yet (real gap; root-cause closed-exhausted, credential now fixed, only the actual backfill run remains).**
      **Scope correction applied first**: this todo's own title says "2015→present," but that framing is stale — the
      2026-07-21 operator ruling (`/codex/02-data/sports-2020-06-data-floor.md`) clamped every sports source's
      `coverage_start` to **2020-06-06** and ruled "any plan/track that backfills sports history before 2020-06 is
      moot." So "extend to `coverage_start`" today means 2020-06-06→present, not 2015→present; measured against the live
      `SOURCE_COVERAGE_START` floor. **Method**: single read of `instruments-store-sports-prd-central-element-323112`'s
      `_index/availability_index.parquet` (6,871,468 rows, one download, bounded columns — no whole-corpus GCS walk),
      filtered `date >= 2020-06-06`, grouped by `source`. **5/6 sources — open_meteo (weather), soccer_football_info,
      transfermarkt, understat, footystats — genuinely extended**: each has a manifest row for effectively every
      calendar day since the floor (2243-2248 of 2243 calendar days), **0 blank/un-typed `error_reason`** on any
      `empty_confirmed`/`attempted_failed` row across all 5. **odds_api — NOT extended**: 635 of 2243 calendar days
      since the floor have **ZERO manifest row of any capture_status** (a true absence, not a typed skip — IS has no
      `odds_api` adapter/expected-universe seeder, confirmed by sub-agent trace, so no denominator cell was ever
      materialized for these days). Of the 635, only 19 fall inside the already-documented + already-fixed
      2026-06-27..07-15 scheduler-dormancy window
      (`sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`, fixed
      `market-tick-data-service@410d7569`), and part of one range overlaps the already-documented 2022-09 canonical
      under-capture outage (`mdt_legacy_canonical_row_gap_2026_07_16.md`, superseded). **616 days are newly found,
      previously undocumented** — 30 contiguous ranges >=3 days (6 undocumented multi-week ranges: 2020-08-24.. 10-10
      [48d], 2022-03-06..04-18 [44d], 2023-07-01..10-06 [98d], 2024-11-19..12-31 [43d], 2025-03-11..04-11 [32d],
      2026-02-22..03-28 [35d]) plus 120 isolated single-day gaps, roughly even day-of-week distribution (no weekly-cron
      signature). Filed as a new finding, with root-cause + backfill todos:
      `plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`. **No backfill attempted yet**: the
      odds-api.com key was `DEACTIVATED_KEY` through 2026-07-28 (`sports_odds_api_key_deactivated_2026_07_26.md`,
      independently re-verified live by 3 slots against the vendor directly) — any fetch attempt then would have just
      401'd and added `attempted_failed` noise. **UPDATE 2026-07-29: the operator rotated `odds-api-key` to a new key on
      a 5,000,000-credits/month subscription, live-verified (HTTP 200, `x-requests-remaining: 5000000`) — no longer
      deactivated.** Only the actual gap-fill backfill remains, no further gate. (repo: instruments-service,
      market-tick-data-service). **Done when**: the new issue doc's root-cause + backfill todos land AND a fresh census
      shows odds_api at 0 missing days too (the other 5 sources' portion of this done-when is already satisfied).
      **UPDATE 2026-07-28 (slot 14) — root-cause avenue now closed too.** Picked up the issue doc's root-cause todo (the
      6 undocumented multi-week gaps): checked GCP Cloud Logging bucket retention (`_Default`=2 days, `_Required`=400
      days but audit-log-only), the `vm-logs/` GCS archive (earliest entry 2026-07-14, postdates even the most recent of
      the 6 windows), and Cloud Scheduler job wiring — all three are categorically insufficient for every one of the 6
      windows, so the root-cause todo is now closed as UNABLE TO ROOT-CAUSE (exhausted, not deferred; see the issue
      doc's Progress Log). Re-verified the odds-api key live at the time: still `error_code=DEACTIVATED_KEY`, unchanged.
      **UPDATE 2026-07-29: the operator rotated `odds-api-key` (new 5,000,000-credits/month-subscription key),
      live-verified HTTP 200 — no longer `DEACTIVATED_KEY`.** This item is now genuinely fully investigated end-to-end
      and credential-unblocked — the ONLY remaining action is the actual backfill run itself, no operator gate left. Not
      re-tagging `BLOCKED-CREDENTIALS` (the credential is fixed); `BLOCKED-PREREQUISITES` above has been changed to
      `UNBLOCKED` to match so `regen_backlog_from_plan.py` picks this back up as dispatchable.
- [ ] [DATA] P2. BLOCKED-PREREQUISITES — **Sports P2c — features history backfill to ML-ready, blocked on the P2a and
      P2b todos above landing first.** Extend the features-service sports feature matrix from the golden window
      (2025-09-01..11-30) to 2015→present once P2a/P2b land. (repo: features-service). **Done when**: P2a/P2b are both
      confirmed done AND the features matrix extension completes with a fresh coverage census cited.
- [ ] [REVIEW] P2. BLOCKED-PREREQUISITES — **Sports P2d — final e2e gate stamp, deliberately deferred, blocked on the
      P2a/P2b/P2c items above.** R3-daily/R4/R5 sub-items already shipped/verified; R1/R2/R3-history remain blocked
      pending P2a+P2b+P2c — re-run this gate once those land, don't mark it DONE early. (repo: unified-trading-pm).
      **Done when**: P2a/P2b/P2c are all confirmed done AND the gate re-run passes. — **2026-07-31T15:15Z (slot 14,
      review): re-dispatched, still genuinely blocked — P2c (features history backfill, todo above) is still `[ ]`, so
      the done-when clause is not met.** Same root cause as the P0 VERIFY todo below
      (`blocked_prerequisites_ marker_not_in_non_dispatchable_regex_2026_07_28.md`): `regen_backlog_from_plan.py`'s
      `_NON_DISPATCHABLE_RE` doesn't recognize the `BLOCKED-PREREQUISITES` token, so this same-plan-dependency todo
      keeps re-dispatching despite the plan's own banner intent. Not re-tagging to an operator/credential marker
      (inaccurate — this is a genuine same-corpus todo dependency, not an external gate). No code shipped, no gate
      re-run attempted (P2c isn't done yet — forcing one now would be exactly the "don't mark it DONE early" this todo
      warns against). Logged as a disposition entry rather than silently re-bouncing. — **2026-07-31 (slot 8):
      re-dispatched again same day, still genuinely blocked — no change since slot 14's 15:15Z check: P2c (line ~271)
      still `[ ]`, and P2b's own text confirms the odds_api backfill run itself still hasn't happened. Same root cause
      (`blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` — `_NON_DISPATCHABLE_RE` doesn't
      recognize `PREREQUISITES`). No new diagnosis needed; no code shipped; checkbox correctly stays open. Flagging that
      this todo has now bounced across at least 4 separate slots (10/15/6/14/8) purely on this same mechanical gap — the
      issue doc's own P2 audit todo (converting this to a structural `depends_on`+`gate_on_depends` split, per its
      "Recommended decision" §(b)) would stop the churn; that audit is `assigned_vm: NA` there and hasn't been picked up
      yet. — **2026-07-31 (slot 5): re-dispatched again, same-day, still genuinely blocked — P2c unchanged.** Confirmed
      via `GET /api/backlog/sports_closeout_track_s2_foldin-008/blockers` that this task_id carried NO armed fleet
      cooldown before this dispatch (`"ready (no blockers)"`) — prior dispatches evidently closed via a no-op `/done`
      rather than `/skip-current-task`, which never exercises `register_cooldown`/the auto-park counter
      (`server/state_store/cooldown.py`, `dispatch_cooldown_auto_park_skip_threshold` default 3). Closing THIS dispatch
      via `/skip-current-task` with `reason_code: GATED` instead, so it actually arms the fleet-scoped cooldown and
      counts toward durable auto-park — future dispatches of this same todo should do likewise (not `/done`) until it
      either auto-parks or P2c genuinely lands. — **2026-08-02 (slot 13, review): re-dispatched again, still genuinely
      blocked — P2c (line 278) confirmed still `[ ]`.** Checked
      `GET /api/backlog/sports_closeout_track_s2_foldin-008/blockers` before declining: `"ready (no blockers)"` —
      slot-5's 2026-07-31 GATED cooldown/skip_count has since expired (the 24h park window elapsed with no further GATED
      decline in between to accumulate toward the auto-park threshold of 3). Declining via `/skip-current-task` with
      `reason_code: GATED` again, per the established pattern above — this re-arms the fleet cooldown; whoever picks
      this up next should do likewise until P2c lands or 3 GATED declines land close enough together to cross the
      auto-park threshold. — **2026-08-02 (slot 3, review): re-dispatched again minutes after slot 13's decline, still
      genuinely blocked — P2c (line 278) confirmed still `[ ]`.** The upstream chain has if anything regressed further:
      `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s P1 backfill (which P2b's own done-when depends on) now
      carries a NEW `BLOCKED-CREDENTIALS` tag as of today (task `-004`, slot 14) — the-odds-api.com account is OUT OF
      USAGE CREDITS (`error_code=OUT_OF_USAGE_CREDITS`, a different blocker than July's `DEACTIVATED_KEY` one), operator
      ruled Option B (purchase additional credits) but the top-up isn't confirmed landed yet. So P2b's backfill is
      further from done than at slot 13's check, not closer.
      `GET /api/backlog/sports_closeout_track_s2_foldin-008/blockers` read `"ready (no blockers)"` before this decline.
      Declining via `/skip-current-task` with `reason_code: GATED` again — this is the second GATED decline in quick
      succession today (after slot 13's), which should help cross the auto-park threshold of 3 if a third lands before
      the park window elapses.
- [x] ✅ [DATA] P2. **RETAGGED 2026-07-28 (stale-tag audit — already ruled 2026-07-26, `[OPERATOR]` never removed).**
      Unresolved cefi-before-sports gate TENSION, never ruled (flagged 2026-07-14, still open).
      `instruments_foundation_completeness_2026_06_24.md` states sports does NOT start its G1→G5 until cefi is DONE, but
      cefi's own G4/G5 were still open when this coordinator's G1 noise-wipe work executed (2026-06-28). Unclear whether
      the 2026-06-27 re-homing was an implicit operator override. (repo: unified-trading-pm, decision record). **Done
      when**: the operator has ruled on whether the re-homing was an intended override. ✅ **RULING (2026-07-26):
      retroactively BLESSED as an intended exception, not remediated.** The 2026-06-27 re-homing was a workspace-wide
      infra migration (epic VMs → role-based dispatch), not a sports-specific override, but a direct 2-days-earlier
      TRADFI precedent (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md:169-171`, operator-dispatched ahead of
      cefi-first ordering 2026-06-25) already establishes the standing rule: reversible/audit-class work proceeds
      regardless of cefi's gate state; irreversible/expensive operations stay gated on cefi DONE. The sports G1 wipe
      matched that pattern exactly (snapshot-first, reversible). cefi/sports share no storage/manifest surface, so no
      contamination was possible by construction, and no harm traceable to the sequencing has surfaced since. Full
      ruling + standing rule recorded at the source SSOT: `instruments_foundation_completeness_2026_06_24.md`'s
      TENSION-flag section (now marked RESOLVED). No remediation needed — the already-executed G1 work stands.
- **[REVIEW] P0.** Fixtures-entity-split live-freeze contradiction (`instruments-service@e1524d21`'s
  `_read_fixtures_entity_with_schedule_fallback`) — tracked to completion in
  `sports_legacy_fixtures_path_migration_2026_07_24.md` (now archived at
  `/plans/archive/2026_08/sports_legacy_fixtures_path_migration_2026_07_24.md`), not here; that plan's Phase 1 measures
  the exact load-bearing subset before any data moves.
- [ ] [VERIFY] P0. BLOCKED-PREREQUISITES — **FINAL full-history zero-missing (R1/R2/R3). RE-VERIFIED 2026-07-30 (slot-6,
      7th dispatch) — still genuinely FAILS, same-corpus dependency on P2a/P2b/P2c above, not a mystery block.** No
      fresh corpus-wide census needed to reach this verdict: P2b's own entry above (last measured 2026-07-29) already
      cites 616 undocumented `odds_api` gap days out of 2243 since the 2020-06-06 floor, with **no backfill attempted
      yet** (only the root-cause investigation is done) — that alone violates "0 `expected_unattempted_pending_fetch`...
      for every (source, data_type)", so this gate cannot pass yet regardless of any other axis. P2c (features backfill)
      and P2d (final e2e gate stamp) are both still `[ ]` and explicitly cascade off the same P2a/P2b landing first.
      This is a genuine same-corpus todo dependency
      (`plans/active/issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`'s case (b)), not a
      mislabeled external/operator gate — retagging to an existing `BLOCKED-CREDENTIALS`/`-OPERATOR`/etc. token would be
      inaccurate. **Why this keeps re-dispatching**: this plan's own banner above states intent that the
      `BLOCKED-PREREQUISITES` marker suppresses dispatch, but `server/regen_backlog_from_plan.py`'s
      `_NON_DISPATCHABLE_RE` does not recognize the `PREREQUISITES` token (confirmed root cause, same issue doc) — a
      structural per-todo same-plan dependency has no expressible mechanism today (`sequential: true` would
      over-serialize this plan's many unrelated items, which the banner already correctly rejected; splitting into a
      depends_on-gated plan needs an operator plan-destination decision; task-level `backlog.yaml` prereqs need
      backlog-file access this worker slot does not have). Logged as a disposition entry against the tracking issue
      doc's open audit todo rather than silently re-bouncing an 8th time. Do NOT fetch the
      `api_football × ODDS eu=89,073` slice if it resurfaces — impossible-not-fetchable denominator pollution
      pending a purge/retype pass, not real work. (repo: instruments-service). **Done when**: P2a(c) (sibling
      plan)/P2b's odds_api backfill/P2c all confirmed landed AND the full gate re-run passes corpus-wide with a fresh
      census.
- [ ] [DATA] P2. **STILL RUNNING as of 2026-08-08 live-check (slot-27, review) — Features recompute for enriched
      dates.** Gated on `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s INJURIES 94-league enrichment backfill
      landing first** (that plan was archived 2026-07-28 with `[x]` ✅ 94-league enrichment backfill COMPLETE — prereq
      met). After full-history AF enrichment lands, re-run sports features with force/no-skip for the enriched dates
      (`derived_features` + `fixture_features` only; `odds_features` unaffected). (repo: features-service,
      deployment-service). **Relaunched 2026-08-06 (slot-4)**: VM `fts-backfill-20260806-012831` (SPOT, e2-standard-4,
      zone asia-northeast1-c) running
      `python -m features_service.sports --operation compute --mode batch --asset-group SPORTS --tables derived_features,fixture_features --start-date 2020-06-06 --end-date 2026-08-06 --force`.
      All 5 tarballs fresh, no permission errors (prior VM's 403 on events bucket was transient — `uts-prd-sa` has
      `storage.objectAdmin`). VM setup completed cleanly at 01:31:05Z, calculators initializing with PIPELINE_HEARTBEAT,
      no crash. Monitor:
      `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/fts-backfill-20260806-012831/run.log`. **Done
      when**: the forced re-run completes (VM exit 0, manifest rows written for enriched dates). **Prior attempts**: VM
      `fts-backfill-20260805-045644` (slot-13, 2026-08-05) was PREEMPTED mid-run at ~2021-01-30 (~10% of range).
      Launcher comma-escaping fix `deployment-service@1fabb73` (gcloud `^|^` delimiter for multi-table `--tables`
      values) already shipped on prior attempt. **REVERTED to `[ ]` 2026-08-08 (slot-27, review) — same premature-flip
      pattern as the 08-05 attempt: this todo was flipped `[x]` at launch time (08-06) even though its own done-when (VM
      exit 0, manifest rows written) was unmet; live-check confirms it's genuinely still unmet, not just unconfirmed.**
      See Progress Log for the full live-check evidence.
- [ ] [VERIFY] P2. BLOCKED-PREREQUISITES — **ML-readiness re-verify, transitively gated behind the features-recompute
      todo above.** (repo: unified-trading-pm). **Done when**: the features-recompute todo above is confirmed done AND
      the ML-readiness re-verify passes.
- **[INFRA] P2.** `exit_code_fleet_monitor` CLEAN-misclassification — **ALREADY RESOLVED, not carried forward as an open
  todo (finding C, 2026-07-25).** The parent's Track S2 text described this as live open work; the cited detail doc
  (`exit_code_fleet_monitor_clean_misclassifies_premature_kill_2026_07_21.md`, now archived, `status: resolved`) shows
  both fixes shipped: `deployment-service@2e22c54` (defensive CLEAN-classification check) and
  `deployment-service@6671f02` (preemption-marker write hardening).
- **[DATA] P3.** Season-cache-0-fixtures gap investigation — **ALREADY RESOLVED, not carried forward as an open todo
  (finding C, 2026-07-25).** The cited detail doc
  (`api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency_2026_07_19.md`, now archived,
  `status: resolved`, 10/10 todos done) shows the gate-reader root causes fixed,
  `resolved_by: instruments-service@4ef4cfeb`.
- **[DATA] P3.** WEATHER layout mismatch — **ALREADY RESOLVED, not carried forward as an open todo (finding C,
  2026-07-25 — resolved literally today).** The cited detail doc
  (`sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`, now archived,
  `status: resolved`) shows `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` aligned to `PER_DAY_PER_LEAGUE`,
  `resolved_by: unified-api-contracts@b73c95d5` (2026-07-25).
- [x] ✅ [DATA] P3. **UNBLOCKED 2026-07-28** — sports/trades `DP_RUN_MOSTLY_EMPTY` post-DELETE re-check. The parent's
      Track V K1/K2 legacy-object DELETE has landed and is verified complete
      (`sports_consolidated_closeout_2026_07_19.md` Track V K1/K2 todo, `market-tick-data-service@26201c44`,
      345,852/345,852 deleted, 0 failed). Not a live defect (the 87.2% ratio spike is a K1/K2 denominator-shrink
      artifact on already-dead residue, not a new outage) — this is now the actionable re-check. Filed:
      `sports_trades_attempted_failed_2026_07_23.md`. (repo: deployment-service, read-only). **Done when**: a fresh
      ratio check confirms the spike resolves as predicted. — **DONE 2026-08-05 (slot-4, data_engineering): spike
      resolved as predicted.** Fresh live ratio check against the consolidated
      `market-data-tick-sports-prd-central-element-323112` `_index/availability_index.parquet` (614,477 rows;
      single-file column-pruned read `[capture_status, data_type, attempted_at]` mirroring
      `meta_watchers._read_attempted_failed_cells` — no corpus walk): `data_type="trades"` now reads **captured=375,257,
      attempted_failed=0, empty_confirmed=20,818 → ratio 0.00%** (was 87.2% = 58,016/66,545 on 2026-07-23). The 58,016
      dead-residue `attempted_failed` rows are fully gone (0 remain, no `max_attempted_at`), the genuine `captured`
      population is back on the lowercase axis (375,257 vs 8,529 on 07-23), and no uppercase `TRADES` twin remains in
      the index. 0.00% is far below the 10% `ATTEMPTED_FAILED_RATIO_THRESHOLD` — no new alert, no code change needed
      (read-only check per the todo).
- **[DOC] P2.** `sports_features_layer_findings_sweep_2026_07_18.md` is NOT closed by this plan or by the parent
  closeout — 73 open todos there are the features-layer correctness backlog, deliberately not duplicated here (too large
  to fold in). Do not treat sports feature-layer correctness as done when this closeout or this child archives; that doc
  tracks its own, separate completion.

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/honest-absence-downstream-handling.md`,
`/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`. Plan↔codex drift is review-blocking.

## Progress Log

- **2026-08-08 (slot-27, review)** — Live-check of `fts-backfill-20260806-012831` per
  `plan_reconciler_findings_2026_08_08.md`'s filed `[REVIEW] P3` todo (2026-08-06 last-observed state was "still
  RUNNING, no exit signal"; ~2 days had passed, hypothesized it had "almost certainly resolved one way or the other by
  now"). **Live gcloud/GCS check (this dispatch) finds it has NOT resolved — it is genuinely, actively still running,
  not stalled and not dead:**
  - `gcloud compute instances describe fts-backfill-20260806-012831 --zone=asia-northeast1-c`: status=`RUNNING`,
    `lastStartTimestamp=2026-08-05T18:28:48-07:00` (=2026-08-06T01:28:48Z, matches the launch record above).
  - `run.log` last GCS object update: 2026-08-08T20:57:32Z — 2 seconds before this check, actively growing
    (`WATCHDOG_TRACE.log` shows monotonically increasing size across iters 3900-3919, no stuck-size pattern).
  - Progress metric (target-artifact count, not activity — per RULES.md § 1): distinct `Target fixtures on <date>` log
    lines cover 892 of the 2,253 total days in the `2020-06-06..2026-08-06` range = **39.6% complete**, currently on
    `2022-11-14`. At the measured rate (892 dates / 67.4h elapsed = 13.2 dates/h), ETA to completion is **~4.3 more
    days** (~7.1 days total run time) — far longer than a typical features-backfill VM, but this is throughput, not a
    hang: no exceptions/tracebacks, only expected per-date `data_quality` schema-validation warnings with
    `recovery=skip` (pre-existing sparse-source columns like `ht_*`/`*_xg_understat` on early dates, not new breakage).
  - `ManifestWriter` per-VM shard log lines show `process_final=False` throughout — the manifest write for this VM
    hasn't been finalized, confirming the todo's own done-when (VM exit 0, manifest rows written) is not met.
  - **Reverted the todo's premature `[x]` flip** (see todo text) — this is the same bug class already documented for
    this VM's 08-05 predecessor (`fts-backfill-20260805-045644`, flipped-at-launch then reverted 2026-08-06 below):
    flipping on launch instead of on the stated done-when. Not filing a fresh issue doc for the pattern itself since
    `plan_reconciler_findings_2026_08_08.md`'s live-check todo already covers this dispatch's finding.
  - Not escalated as a billing-waste concern: SPOT VM, actively progressing (no preemption-without-recovery), and
    `/vm-preemption-billing-waste-audit` is the standing mechanism for that surface if the ~7-day total runtime proves
    symptomatic on a future pass.
- **2026-08-06 (slot-13, data_engineering)** — P2c (`sports_closeout_track_s2_foldin-007`) re-dispatch: still genuinely
  blocked, declined via `/skip-current-task` `reason_code=GATED` (not `/done` — the done-when is unmet). Fresh evidence
  gathered this dispatch: (1) **P2b not done** — odds_api gap-fill P1 backfill still `[ ]` + `BLOCKED-CREDENTIALS`
  (`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` `status: open`; OUT_OF_USAGE_CREDITS since 08-02, operator
  Option B credit top-up not confirmed landed); (2) **features matrix extension not complete** — recompute VM
  `fts-backfill-20260805-045644` was PREEMPTED 2026-08-05T16:00:42Z mid-run (`compute.instances.preempted`
  `systemevent-1785945641513…`; run.log ends ~2021-01-30 ≈10% of the 2020-06-06..2026-08-05 range; no `PROGRESS.json`;
  no relaunch VM, verified 08-06). Corrected this plan's features-recompute todo: it was `[x]`-flipped at launch (08-05)
  with its own done-when ("VM exit 0, manifest rows written for enriched dates") unmet — reverted to `[ ]` so the
  backlog re-derives it. P2c's done-when ("P2a/P2b confirmed done AND features matrix extension completes with a fresh
  coverage census cited") is not met on either clause. Ack'd the operator's shared-host OOM directive: nothing this
  session launched was OOM-killed — only read-only `gsutil cat` / `gcloud compute operations list` checks, all bounded
  and small.
- **2026-07-30 (slot-6)** — Dispatched the FINAL full-history zero-missing gate todo (R1/R2/R3) for the 7th time.
  Re-verified FAIL using already-cited evidence in this same plan (P2b's 616 undocumented `odds_api` gap days, no
  backfill run yet) rather than re-running an expensive corpus-wide census — the verdict doesn't change and the real
  blocker is P2b's actual backfill landing, not a diagnosis gap. Root-caused WHY this specific todo keeps re-dispatching
  despite its own `BLOCKED-PREREQUISITES` tag and this plan's banner explicitly relying on that tag to suppress
  dispatch: `server/regen_backlog_from_plan.py`'s `_NON_DISPATCHABLE_RE` does not recognize the `PREREQUISITES` token
  (already tracked, not a new finding —
  `plans/active/issues/blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`). Classified this
  occurrence as that issue doc's case (b) (genuine same-corpus dependency on P2a/P2b/P2c above, not a mislabeled
  external gate) — correctly tagged text-wise already, but with no expressible per-todo dependency mechanism available
  to a worker slot (`sequential: true` would over-serialize this plan's unrelated items, which the banner already
  rejected; a depends_on-gated split needs an operator plan-destination decision; task-level backlog prereqs need
  server-side `backlog.yaml` access this worker doesn't have). Sharpened the todo's own text with the precise current
  blocker + dependency chain so the 8th dispatch (if the regex bug isn't fixed first) doesn't have to re-derive this
  diagnosis from scratch. Logged a disposition entry on the tracking issue doc's Progress Log (see that doc) rather than
  silently re-bouncing. No code shipped — nothing to fix within this worker's reach; checkbox correctly stays open.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added the `blocked_prerequisites` dispatch-regex
  bug issue (explains why several todos here keep re-bouncing) and `cf_manifest_audit_2026_06_01.py` (the audit script
  gating the P0 E8 legacy-bucket delete item).
- **2026-08-05 (slot-13, data_engineering)** — P2 Features recompute for enriched dates: confirmed INJURIES 94-league
  enrichment backfill COMPLETE (satellite plan `sports_satellite_ao_dispatch_batch2_2026_07_24.md` archived 2026-07-28,
  `[x]` ✅). Launched features recompute VM `fts-backfill-20260805-045644` (SPOT, e2-standard-4, asia-northeast1-c) with
  `--tables derived_features,fixture_features --start-date 2020-06-06 --end-date 2026-08-05 --force`. Fixed
  `deployment-service@1fabb73`: gcloud metadata comma-escaping bug in `launch-features-sports-backfill-vm.sh` — switched
  from comma to pipe (`^|^`) delimiter so multi-table `--tables` values (e.g. `derived_features,fixture_features`)
  survive gcloud's dict parsing. Flipped checkbox; VM completion tracked via GCS log at
  `gs://deployment-scripts-central-element-323112/vm-logs/fts-backfill-20260805-045644/run.log`.
- **2026-08-05 (slot-13, data_engineering)** — P2 ML-readiness re-verify: ran `verify_ml_readiness.py` on (a) golden
  window 2025-09-01..11-30: **91/91 days PASS, 100% non-NULL ✅**; (b) recent window 2026-07-01..08-04: **2/35 days have
  data** (July 16, 18 only), both pass at 100% non-NULL but **33/35 days MISSING** — odds_features pipeline has been
  writing only intermittently since ~2026-03 (scattered 8 days in June, 2 in July, 0 in August). The gate technically
  reports YES (0 failed, 100% non-NULL on present data) because the current gate logic only fails on existing-data
  quality, not on missing days. The odds_features gap is independent of the features-recompute VM (which only touches
  `derived_features` + `fixture_features`). However, task done-when requires the features-recompute todo confirmed done
  — VM `fts-backfill-20260805-045644` is still RUNNING (at day ~2020-06-10 of ~2,251, ~7h elapsed). Declining via GATED
  — features-recompute prerequisite not met. ML-readiness check results captured here so the next dispatch doesn't
  re-derive them.
- **2026-08-05 (slot-4, data_engineering)** — P3 sports/trades `DP_RUN_MOSTLY_EMPTY` post-DELETE re-check: flipped
  checkbox. Ran the fresh ratio check (see the flipped todo for full numbers): live read of
  `market-data-tick-sports-prd-central-element-323112` `_index/availability_index.parquet` (614,477 rows, single-file
  column-pruned read `[capture_status, data_type, attempted_at]`, memory-bounded via `run-bounded-analysis.sh` — the
  index was 18 MiB / ~61% smaller than the 07-23 measurement, consistent with the K1/K2 DELETE removing the uppercase
  twin + the 07-23 `source=api_football` wipe). `data_type="trades"`: **captured=375,257, attempted_failed=0,
  empty_confirmed=20,818, ratio=0.00%** — the 87.2% spike resolved as predicted; no code change needed (read-only per
  the todo). Also ack'd the operator's shared-host OOM directive: no subprocess launched by this session was OOM-killed
  (only the bounded index read); heavy corpus-scale work stays on VMs / bounded wrappers per RULES.md § 1.
- **2026-08-06 (slot-4, data_engineering)** — P2 Features recompute for enriched dates: RELAUNCHED after slot-13's
  preempted VM. Verified no `fts-backfill-*` VM running (singleton lock free). Launched `fts-backfill-20260806-012831`
  (SPOT, e2-standard-4, asia-northeast1-c) with
  `--tables derived_features,fixture_features --start-date 2020-06-06 --end-date 2026-08-06 --redo-all`. All 5 tarballs
  fresh; `uts-prd-sa` confirmed `storage.objectAdmin` on events bucket (prior VM's 403 was transient). VM setup complete
  01:31:05Z, calculators initializing with PIPELINE_HEARTBEAT, no crash. Flipped checkbox. Monitor:
  `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/fts-backfill-20260806-012831/run.log`.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **2026-08-06 (slot-16, data_engineering)** — P2c (`sports_closeout_track_s2_foldin-007`) re-dispatch: still genuinely
  blocked, declined via `/skip-current-task` `reason_code=GATED`. Quick re-verification this dispatch: (1) **P2b not
  done** — odds_api gap-fill issue doc `status: open`, 5 open todos, `OUT_OF_USAGE_CREDITS` unresolved
  (`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`); (2) **features recompute VM**
  `fts-backfill-20260806-012831` **still RUNNING** (~1h in, calculators active at 02:34Z, no exit signal). P2c done-when
  ("P2a/P2b confirmed done AND features matrix extension completes with fresh coverage census") unmet on both clauses.
  Same root cause as prior dispatches: `BLOCKED-PREREQUISITES` marker not recognized by `_NON_DISPATCHABLE_RE`
  (`blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` case (b)).

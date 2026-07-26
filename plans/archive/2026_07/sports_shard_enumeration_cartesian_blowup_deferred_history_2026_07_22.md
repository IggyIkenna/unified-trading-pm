---
doc_type: issue
title: Extracted history — Deferred work after 2026-07-22 (sports_shard_enumeration_cartesian_blowup_2026_07_20.md)
summary: >-
  Extracted from sports_shard_enumeration_cartesian_blowup_2026_07_20.md (2026-07-26, slot-2) to bring the parent doc
  back under the 1000-line hard cap per task_template.md finding J: (1) the "Deferred work after 2026-07-22" section,
  (2) the "What adversarial verification REFUTED" writeup, (3) the "NOT-TO-DO" premises checklist. Every item here is
  either `- [x]` (done/resolved/ruled) or an explicit "do NOT act on this" finding — a fully-closed historical record,
  not open work. The parent doc's own RE-TRIAGE (2026-07-23) section + its 2026-07-26 progress entries independently
  summarize the current state; this file preserves the original derivation reasoning (why 1,066,231 not 1,136,624, the
  3.3 predicate independent-derivation writeup, the soft-delete-vs-backup investigation, and every REFUTED claim's full
  evidence) for anyone who needs the "why", not just the "what".
status: complete
nature: record
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [sports, history, extracted, archive]
related: [sports_shard_enumeration_cartesian_blowup_2026_07_20]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
locked_by:
---

# Extracted history: Deferred work after 2026-07-22

> Extracted verbatim from `plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` — see that doc's
> RE-TRIAGE (2026-07-23) section and its 2026-07-26 Part 2/Part 3 progress entries for the current, authoritative state.
> This file is the historical derivation record only.

## Deferred work after 2026-07-22 (superseded table below — see the 2026-07-22-later-same-day correction banner)

> **⚠️ Correction (2026-07-22, later same day)**: the table below said Phase 3 was "Operator-owned, pending
> re-authorization" — **stale**. Phase 3 shipped the same day (`unified-api-contracts@7338fa65`) after the operator
> reviewed the exact measured table and said to continue. A dedicated Phase 5 scoping workflow (spec-extraction +
> CAS-mechanism + Phase 6d deploy-status investigation) also found this doc's own §4.4 header claimed "IMPLEMENTED, ship
> pending" while this table (and the Progress Log) said the opposite — a real self-contradiction, now corrected in §4.4
> above. The row-by-row corrections are below; do not trust the "Phase 3" / "Phase 4/4.4" rows' original wording, only
> the states as now written.

| Item                                                                                                                                                                                                                   | State                                                                         | Blocked on                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Phase 3** — ✅ DONE, shipped `unified-api-contracts@7338fa65`                                                                                                                                                        | Done                                                                          | Operator reviewed the exact measured table (CEFI -11.50pp, TRADFI -8.96pp, SPORTS -10.19pp, PREDICTION -5.19pp, DEFI -0.05pp) and explicitly authorized shipping it same-day; formula re-verified via a fresh same-day re-measurement immediately before the ship.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Phase 4 / 4.4** — ✅ DONE, live in prod (see §4.4)                                                                                                                                                                   | Done                                                                          | N/A — `deployment-api@6d20724` → squash-merged to main as `f8abbae` → deployed to `uts-shared-deployment-api` at 17:51:37Z, content-verified via `gcloud run services describe`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Phase 5 / Part 3** — execute manifest remediation (3.1/3.2/3.3/3.4) — **3.0 prereq MET; all scoping/ordering/procedure/mechanism DECISIONs now RULED 2026-07-22/23; only safety tooling + the human trigger remain** | Not done (all decisions closed, real engineering work + human trigger remain) | 3.0's prerequisite (Phase 6d) is satisfied — `deployment-api@6d20724` confirmed live via `gcloud run services describe`. All operator decisions RULED: (1) human-only triggers the write; (2) row-count scope = **1,066,231**; (3) 3.3 destination = `empty_confirmed` + one of 3.1's new codes; (4) execution order = strict sequential 3.1→3.2→3.3 (3.4 separately blocked on 2.1); (5) 3.4 gets a lighter procedure (phantom rows, no live GCS object); (6) cross-object write mechanism = sequential per-object CAS + partial-apply alarm, matching the existing `purge_pre_launch_manifest_rows.py` precedent. **What's left is NOT a decision** — genuine unbuilt safety tooling (row-identity assertions, the CAS+alarm implementation itself, a consolidator-paused pre-flight check, a `coverage_drift.py` pre-notify mechanism, default-on dry-run mode) — plus the human-only trigger, which applies regardless of how complete the tooling is. Note also 3.2 itself is independently marked NOT-TO-DO (§3.2, four grounds) regardless of scope. Full runbook + every open question: see the `- [x]`/`- [ ]` todos below. |
| **4.5** — issue-doc corrections (strike the false "no per-(venue,league) coverage declaration" line; fix the reason-split figures to the measured `606,772 / 459,459 / 200,864 / 94,127 / 385,402` values)             | Not done                                                                      | Nobody — small, safe doc fix, pick up any time.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

**Recommended order**: (1) retry the `deployment-api` + `instruments-service` pushes opportunistically as the foreign
UAC dependency clears (external contention, not a design/implementation gap); (2) once Phase 6d is pushed, watch the
LDR→main→Cloud-Build pipeline to a read-only-verified deploy
(`gcloud run services describe uts-shared-deployment-api --region asia-northeast1 --project central-element-323112 --format='value(spec.template.spec.containers[0].image)'`);
(3) **separately and in parallel**, get the operator's answers to the 3 Phase 5 decisions below — Part 3 cannot start
without them regardless of how fast (1)-(2) resolve.

- [x] [DECISION] P0. ✅ **RULED 2026-07-22 (operator, chat, this session) — Human-only.** Who triggers the actual
      sports-manifest prod-bucket write (3.2 purge, and possibly 3.4): the operator (or another human) runs the write
      script by hand after review; no agent executes `--apply` autonomously. Confirms
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`'s existing hard stop applies here with no
      agent-with-signoff carve-out — 4.2's "combined A+B" decision is now reconciled against it.
- [x] [DECISION] P0. ✅ **RE-RULED 2026-07-22 (operator, chat, this session, superseding the same-day earlier answer) —
      1,066,231.** Which population scopes 3.1/3.2's predicate. The operator's first answer to this question was
      "1,136,624" (the 3rd of 3 options offered, whose own description already flagged it as "possibly a typo").
      Investigation before acting on it traced 1,136,624's provenance: it first appears in this doc's very first commit
      (`435356187f3`, 2026-07-20, the 7-agent adversarial-verify pass) in the same sentence that introduced **Option C**
      ("reclassify to `expected_unattempted`", §4.2's options table, listed only as "~1.1M mod" and never given an exact
      figure anywhere else) — not as a second measurement of Option B's (3.2) dead-pair population. No script or doc
      anywhere computes 1,136,624 as 3.1/3.2's population, and it exceeds both 923,952 and 1,066,231 (consistent with C
      being a broader/different-filter population, not a stricter one). Since §4.2 already DECIDED **combined A+B**, not
      C, using 1,136,624 to scope 3.1/3.2 would have silently substituted an un-chosen option's population into the
      chosen mechanism. Surfaced to the operator as a probable SSOT contradiction (not silently resolved); the operator
      confirmed it should be re-picked and chose **1,066,231** — 3.1's own already-shipped, already-measured
      frozenset-addition effect (`unified-api-contracts@7338fa65`). **This closes the reconciliation with no further
      derivation needed**: 3.1's shipped predicate
      (`capture_status=empty_confirmed AND error_reason IN     {EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE, EXPECTED_PAUSED_LEAGUE}`)
      already produces exactly the ruled population — 3.2/3.3, if and when authorized, target that same 1,066,231-row
      set, not 3.2's originally-drafted narrower LIVE_PAIRS/`row_count`-filtered subset (923,952). 1,136,624 (Option C)
      is preserved here only as a pointer in case Option C is ever revisited — it is not part of the executed mechanism.
- [x] [DECISION] P0. ✅ **RULED 2026-07-22 (operator, chat, this session) — `empty_confirmed` + new code.** 3.3's
      destination classification: write `capture_status=empty_confirmed` paired with one of 3.1's two newly-introduced
      `error_reason` codes (`EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` / `EXPECTED_PAUSED_LEAGUE`), not a distinct new
      code. Which of the two codes applies per-row still needs the predicate work in the P1 item below.
- [x] [SCRIPT] P0. ✅ **RESOLVED 2026-07-22 — no predicate derivation needed.** Superseded by the re-ruling above: the
      operator re-picked 1,066,231 (3.1's already-shipped scope) instead of 1,136,624, so 3.2/3.3's target predicate is
      simply 3.1's own
      `capture_status=empty_confirmed AND error_reason IN {EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE,     EXPECTED_PAUSED_LEAGUE}`
      — no new query to write, no widening of 923,952's narrower LIVE_PAIRS-scoped predicate. §3.2's SQL sketch
      (`LIVE_PAIRS` / `row_count IN (0, NULL)` narrowing) is now superseded for scoping purposes; retained in place
      below for its documented failure-mode reasoning (UNION requirement, `SOURCE_RETURNED_ZERO` carve-out), not as the
      operative predicate.
- [x] [SCRIPT] P1. ✅ **RESOLVED 2026-07-23 — predicate derived + independently verified against real prod data, exact
      match.** Two independent agents (blind to each other's approach) both derived: `LIVE_PAIRS` = distinct
      `(venue, league_id)` pairs with `capture_status=='captured'`, over the sports manifest read via
      `instruments-service/scripts/measure_honest_coverage.py`'s `_read_manifest("sports", merge=True)` (loaded via
      `importlib`, never edited on disk);
      `never_captured = capture_status=='attempted_failed' AND (venue,league_id)     NOT IN LIVE_PAIRS`. **Both agents
      got exactly 37,426 on the first straightforward run, no filter-tuning.** Schema note for whoever writes the
      relabel code: `league_id` IS a real, first-class manifest column
      (`unified-trading-library/unified_trading_library/manifest_writer/_rows.py:64`, `_read_index.py`,
      `_queries.py:69`) — it is just absent from `measure_honest_coverage.py`'s own narrower `_READ_COLUMNS*` lists,
      which must be monkeypatched in-process (same pattern
      `unified-api-contracts/scripts/measure_honest_coverage_formula_delta.py` already uses for `error_reason`) to
      include it; do not re-derive league_id from `instrument_id` parsing, read it directly. See the full derivation
      write-up + the 67,206 cross-check discrepancy (explained, not a bug) in §3.3 below.
- [x] [DECISION] P2. ✅ **RULED 2026-07-23 (operator, chat, this session) — strict sequential 3.1 → 3.2 → 3.3.** 3.1 is
      already shipped. Each of 3.2/3.3 is fully verified (manifest re-read, coverage re-measured) before the next
      starts, even though 3.3's population is disjoint from 3.2's and nothing data-dependent forces serialization —
      chosen to keep each write's blast radius isolated and attributable. 3.4 remains separately hard-blocked on 2.1
      regardless of this ordering.
- [x] [DECISION] P2. ✅ **RULED 2026-07-23 (operator, chat, this session) — lighter procedure for 3.4.** Since 3.4's
      22,145 rows are confirmed-phantom (no backing GCS object), the full 5-step procedure (consolidator pause,
      per-VM-shard snapshot, CAS write, pre-notify, T+1/T+24h verify) is safety overhead built for a live-data purge,
      not a phantom-row cleanup. 3.4 keeps: a plain backup of the affected manifest rows before the write, and the
      `coverage_drift.py` pre-notify (since it still moves the coverage number).
- [x] [SCRIPT] P1. ✅ **RULED 2026-07-23 (operator, chat, this session) — sequential per-object CAS + partial-apply
      alarm, confirmed as the mechanism.** Matches the doc's own proposal and the existing precedent script
      (`instruments-service/scripts/purge_pre_launch_manifest_rows.py`, true generation-match CAS, fails loud,
      live-verified 2026-07-15 against 612 real sports rows) — build from that template, no new design pass needed.
- [x] [SCRIPT] P1. ✅ **NARROWED 2026-07-23 — the backup/restore sub-item is resolved; the rest still needs building.**
      A dedicated investigation (live `gcloud`/`gsutil` check against
      `market-data-tick-sports-prd-central-element-323112`, cross-checked against Google's current Cloud Storage docs)
      confirmed: **GCS soft-delete is enabled on this bucket, 7-day retention, and covers OVERWRITES, not just explicit
      deletes** — Google's own docs state soft-delete "preserves objects and buckets that get deleted or overwritten."
      Object Versioning is separately OFF (`gsutil versioning get` → `Suspended`) but isn't needed for this. Restore is
      `gcloud storage restore     gs://BUCKET/OBJECT[#GENERATION]` (generation optional — defaults to latest). This
      workspace's own `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` never mentions soft-delete/versioning
      at all and does NOT mandate an explicit backup step — its safety model is proof-before-delete (5-part
      verification) + human-only hard stops, not backup-then-restore. **However**, soft-delete would NOT have helped the
      actual precedent incident this section warns about
      (`plans/archive/issues/reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12.md` — path corrected, doc
      has moved to `archive/`): that was a stale-read blind full-overwrite with no write-time staleness/CAS guard, and
      soft-delete is purely retroactive (no write-time gate) — plus during that incident the consolidator was
      crash-looping erratically, so it's unclear a clean prior generation even existed to restore to. The actual fix
      shipped there was a write-time merge-with-outstanding-shards guard, not a restore path. **Net:** drop the
      hand-rolled `_index/purge_backups/<date>/` backup requirement (soft-delete already gives a 7-day undo window for
      free) — still to build: row-IDENTITY assertions for the untouched populations (3.3's 12,945 genuine current
      failures — re-measure at execution time, not the doc's stale 67,206; 3.4's 20,331 lowercase twins), the per-object
      CAS + partial-apply alarm itself (see the ruled mechanism above), an automated pre-flight consolidator-paused
      check (fail closed if unverifiable), and a concrete mechanism for the `coverage_drift.py` pre-notify step (still
      unspecified anywhere). Default-on dry-run mode (predicate-matching row count vs. expected figures, refuse
      `--apply` on mismatch) also still needs building.
- [x] [SCRIPT] P3. ✅ **Already self-answered in this todo's own text — no further decision needed.** Best-fit existing
      template for the bulk delete/reclassify shape: `instruments-service/scripts/purge_pre_launch_manifest_rows.py`
      (true generation-match CAS, fails loud, live-verified 2026-07-15 against 612 real sports rows) — build from this,
      not from scratch. Explicitly do NOT use
      `unified_trading_library/manifest_migrations/purger.py::LegacyRowPurger.apply` or the deprecated
      `reconcile_phantom_manifest_rows.py` as templates — the latter caused the real 2026-07-12 production incident
      (`plans/active/issues/reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12.md`), silently reverting
      ~2.5 hours of completed backfill by re-uploading a stale 4.9M-row dataframe.

## What adversarial verification REFUTED (do NOT act on these)

- REFUTED -- THE HEADLINE CLAIM THAT empty_confirmed IS FABRICATED ACROSS THE BOARD ('no per-bookmaker fetch is ever
  performed', 'roughly 1.06M rows assert honest absence for cells never fetched'). This is materially wrong about how
  the Odds API works. venue_fetch.py:695 issues ONE provider call whose response carries a bookmaker_key column, and
  captures are produced by records_df.groupby(['bookmaker_key','league_id','fixture_id']). The aggregator returns ALL
  requested bookmakers in that single response. So for any bookmaker actually in the request, its absence from the
  response IS a genuine observation of absence -- exactly the operator's alternative hypothesis ('we asked the
  aggregator for this league-date and it returned nothing'). The per-bookmaker fan-out is a legitimate pattern, not a
  fabrication. What matters is not whether each book was individually requested (none are, by design) but whether it was
  in the request list at all.
- REFUTED -- 'FABRICATED HONEST-ABSENCE PROOF affects all 200,864 SOURCE_RETURNED_ZERO rows'. Scope is overstated and
  the wrong path is cited. In the v2 fixture-level path (the dominant one), SOURCE_RETURNED_ZERO is emitted via
  `writer_manifest.record_zero_rows(..., was_expected=True)` at sentinels.py:325 with NO fetch_evidence at all -- the
  code comment at :321-324 explicitly notes this routes to attempted_failed and requires no proving evidence. The
  `_reached_empty_fetch_evidence` synthesis (sentinels.py:97-104) appears only on the v1 season-calendar fallback path
  at :443. The claim conflated two different branches.
- REFUTED -- 'ONEXBET is an INTENTIONAL mechanism, honestly reason-coded, so this is not a false-absence bug; it is only
  a denominator-inflation question.' This is wrong, and the adapter proves it. `onexbet` is NOT in
  `_HISTORICAL_BOOKMAKERS` (odds_api_adapter.py:114-147), the explicit 23-key `bookmakers=` list actually sent to the
  API. 1xBet is never requested, so it can never appear in a response. Its 139,620 empty_confirmed rows assert the
  aggregator returned nothing for a bookmaker that was never asked for. That is a FALSE honest-absence claim, identical
  in kind to bare BETFAIR -- not a defensible reason-coded absence.
- REFUTED (NEW ROOT CAUSE, sharper than either sub-report reached) -- the defect is NOT 'the coverage oracle is
  circular' nor 'league-alias vocabulary mismatch'. It is that the expectation axis is disconnected from the
  `bookmakers=` request list, and it is wrong in BOTH directions. Measured set comparison of the 23 requested keys
  against the 5-key sentinel scope and against the manifest: (a) IN SCOPE BUT NEVER REQUESTED =
  ['BETFAIR','ODDS_API','ONEXBET'] -> 418,860 structurally-impossible rows, 0 captured, ever; (b) REQUESTED BUT NEVER
  EXPECTATION-TRACKED = 21 books
  ['BETFAIR_EX_EU','BETFAIR_EX_UK','BETFAIR_SB_UK','BETONLINEAG','BETRIVERS','BETSSON','BETVICTOR','CASUMO','CORAL','DRAFTKINGS','FANDUEL','LADBROKES_UK','LIVESCOREBET','PADDYPOWER','SKYBET','SMARKETS','SPORT888','UNIBET','UNIBET_UK','VIRGINBET','WILLIAMHILL']
  -> these are fetched on every single call yet can never be recorded as missing. Only PINNACLE and MATCHBOOK are both
  requested AND enumerated. Decisively: REQUESTED venues with ZERO captures = NONE (empty set). Every book that is
  actually asked for does capture. So the entire 'dead venue' phenomenon is explained by non-requested keys, NOT by
  bookmakers declining to price leagues.
- REFUTED -- 'PINNACLE 16/93 and MATCHBOOK 16/79 dead leagues are false honest-absence claims from alias misses.' Partly
  right about the alias mismatch, but the conclusion does not follow: pinnacle and matchbook ARE in the `bookmakers=`
  request list, so their zero-row cells reflect a real probe of a real book. Their 188,041 empty_confirmed rows are
  DEFENSIBLE honest absence -- the operator's alternative hypothesis (a) holds for exactly these two venues. Any
  remediation must not sweep them in with the 1.1M structurally-false rows.
- REFUTED -- 'the case duplicates are a LIVE bug.' They are FROZEN legacy. Measured per-data_type date ranges: ODDS and
  odds both span 2020-06-01..2026-04-14 and STOP there, while `trades` runs to 2026-06-27. written_at for both cohorts
  occurs on only three dates (2026-04-08: 23 rows, 2026-04-13: 526, 2026-07-13: 21,596/19,782 = the manifest rebuild
  restamp). Every live-code reference to an uppercase 'ODDS' data_type is in a migration/rebuild script
  (migrate_sports_canonical_v9.py, rebuild_sports_manifest_v9.py, normalize_sports_mtds_data_type_case_2026_06_25.py,
  migrate_sports_instruments_legacy_gap_2026_07_13.py) -- none in the live writer. This is a live DATA defect in the
  served index (the duplicate rows still double-count any data_type-grouped denominator), but NOT an actively-writing
  bug. The distinction changes the fix from 'stop the writer' to 'one-off dedupe'.
- REFUTED (NEW) -- the prior report treated the ODDS/odds split as duplicated physical shards and left canonical
  direction contested. Measured against GCS: on day=2020-07-21, day=2023-05-10 and day=2026-04-14 the bucket contains
  ONLY `data_type=odds` (5, 5 and 2 objects respectively) and ZERO `data_type=ODDS` directories, while the manifest
  carries BOTH spellings for those same days (2020-07-21: 6 uppercase + 5 lowercase). So uppercase ODDS is a
  MANIFEST-ONLY PHANTOM with no backing objects; lowercase matches disk. This inverts the practical conclusion:
  /codex/02-data/sports-data-types-catalog.md:32-41 K0-DECISION(b) 2026-07-18 declares UPPER canonical for sports, which
  contradicts the physical estate. The phantom rows should be dropped, not the lowercase ones -- and the K0 decision
  needs operator re-confirmation before any normalizer is re-pointed.
- REFUTED -- 'written_at differs by ~41 microseconds (ODDS 2026-04-13T02:10:21.383459 vs odds ...383500), proving the
  twins were emitted microseconds apart in the same pass and are therefore not benign legacy.' The maximum written_at
  for both cohorts is 2026-07-13T23:56:41 (the rebuild), not 2026-04-13. The microsecond-adjacency describes rows
  written by a bulk rebuild pass iterating a data_type list, which is evidence FOR the rebuild-artifact explanation, not
  against the legacy explanation.
- REFUTED -- internal numerical contradiction between the sub-reports, resolved by my measurement. The 'dead' section
  reported EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE 538,098 / EXPECTED_PAUSED_LEAGUE 369,272; the 'writer' and 'applic'
  sections reported 606,772 / 459,459. My groupby over the odds slice gives 606,772 / 459,459 (plus SOURCE_RETURNED_ZERO
  200,864, VENUE_FETCH_FAILED 94,127, and 385,402 blank). The 'dead' figures are wrong and should not be carried
  forward.
- WEAKENED -- 'prediction-venue rows are provably stale because their date range stops at 2026-06-20 while in-scope
  venues run to 2026-06-27.' The cited evidence does not prove it: PADDYPOWER, UNIBET, DRAFTKINGS, SKYBET, FANDUEL,
  CORAL and most other captured-only venues ALSO stop at 2026-06-20. The 2026-06-27 tail is unique to the five
  enumerated scope keys precisely because sentinels keep emitting past the last capture. The conclusion (stale residue
  predating the 2026-06-21 exclusion) is still probably correct -- the venues are verifiably out of the live scope today
  -- but it rests on the code filter, not on the date gap.
- NEW FINDING NEITHER REPORT FLAGGED -- FREE-TEXT REASON TAXONOMY VIOLATIONS in the odds slice. The error_reason column
  contains full English sentences as values, e.g. "record_empty(reason=SOURCE_RETURNED_ZERO) rejected:
  instruments-service catalog says 'trades' was ALIVE on MATCHBOOK/2024-02-08. Use
  record_failed(EmptyFromLiveInstrumentError(...)) instead -- this is a real fetch failure, not honest absence." A
  rejection diagnostic has been persisted as the reason code itself. This is the class tracked by
  plans/active/issues/sports_rebuild_v9_free_text_reason_taxonomy_rejection_2026_07_13.md, still present in the live
  index and breaking any closed-set reason consumer.
- NEW FINDING NEITHER REPORT FLAGGED -- FOUR VENUES CAPTURE DESPITE NOT BEING REQUESTED: BETMGM (988), BETWAY (1,226),
  BOVADA (1,419), UNIBET_EU (34), all dated 2025-07-31..2025-12-31. None is in the `bookmakers=` list. `betway` is
  EXPLICITLY EXCLUDED at odds_api_adapter.py:105 for corrupt data ('4-6% price diff vs OddsPapi', validated 2026-03-28),
  yet 1,226 captured rows exist. Either a second ingest path bypasses the audited bookmaker list or the exclusion
  post-dates the data. Worth its own check before these rows feed features.
- ANSWER TO THE OPERATOR'S QUESTION, corrected: YES we record shards per bookmaker, and yes a per-(bookmaker,league)
  applicability gate already exists and is consulted -- so the premise 'not all bookmakers exist for all odds' is
  already handled and is NOT the failure. NO it does not work, but for a different reason than either sub-report gave:
  the expectation universe is a 5-key static list that shares only 2 keys with the 23-key list actually sent to the API.
  Three enumerated keys can never be captured (418,860 false rows) and twenty-one requested books are never
  expectation-tracked (their gaps are invisible). Fix = derive the sentinel scope FROM the adapter's `bookmakers=` list
  (odds_api_adapter.py:114) rather than from UAC venue categories, so the expected universe equals the requested
  universe by construction. That single change removes the phantom axes and makes the 21 unmeasured books measurable,
  without touching the league gate that already works.

## ⛔ NOT-TO-DO — premises that did not survive verification

Do not spend engineering time on any of these.

1. **"`empty_confirmed` is fabricated across the board — no per-bookmaker fetch is ever performed."** — **REFUTED.**
   `venue_fetch.py:695` issues one provider call whose response carries a `bookmaker_key` column; captures come from
   `records_df.groupby(["bookmaker_key","league_id","fixture_id"])`. The aggregator returns **all requested bookmakers**
   in that single response, so for a book that **is** in the request list, its absence from the response _is_ a genuine
   observation of absence. The per-bookmaker fan-out is a legitimate pattern. The defect is not "was each book
   individually requested" (none are, by design) — it is "was it in the request list at all."
2. **"Fabricated honest-absence proof affects all 200,864 `SOURCE_RETURNED_ZERO` rows."** — **REFUTED, scope overstated
   and wrong path cited.** The dominant v2 path emits via `record_zero_rows(..., was_expected=True)` at
   `sentinels.py:325` with **no** `fetch_evidence` — the comment at `:321-324` explicitly notes no proving evidence is
   required. `_reached_empty_fetch_evidence` appears **only** on the v1 fallback at `:443`. Fix is step 1.4, narrowly
   scoped.
3. **"The root cause is the circular coverage oracle."** — **REFUTED as the root cause.** The oracle _is_
   self-referential (`sports_bookmaker_league_coverage.py:3-7`: covered iff ≥1 captured row exists) and that is a real
   known floor worth documenting — but it is not what produces the dead venues. **Every book actually in the
   `bookmakers=` list captures; the set of requested-venues-with-zero-captures is EMPTY.** Do not rebuild the league
   gate; it works.
4. **"The league-alias vocabulary mismatch (16/33 leagues) is the root cause of MATCHBOOK 16 / PINNACLE 16 dead."** —
   **REFUTED as a defect.** `pinnacle` and `matchbook` ARE in the request list (`odds_api_adapter.py:132,133`), so their
   zero-row cells reflect a real probe of a real book. Their 188,041 `empty_confirmed` rows are **defensible honest
   absence**. The alias mismatch is real but cosmetic here; **do not sweep these two venues into any remediation** aimed
   at the structurally-false rows.
5. **"ONEXBET is intentional and honestly reason-coded — only a denominator-inflation question."** — **REFUTED, and
   inverted.** `onexbet` is **not** in `_HISTORICAL_BOOKMAKERS` (`odds_api_adapter.py:114-149`). It is never requested,
   so it can never appear in a response. Its 139,620 `empty_confirmed` rows assert the aggregator returned nothing for a
   book that was never asked for — a **false** honest-absence claim, identical in kind to bare BETFAIR. Step 1.2 removes
   it; it is not a "leave it, just note the denominator" case.
6. **"The case-duplicate rows are a LIVE writer bug — fix the writer."** — **REFUTED.** Frozen legacy: both cohorts stop
   at 2026-04-14 while `trades` runs to 2026-06-27; every uppercase-`ODDS` reference in live code is in a
   migration/rebuild script. **Do not go hunting for a writer to stop.** It is a one-off data dedupe (3.4), gated on
   4.3.
7. **"The 41-microsecond `written_at` gap proves the twins were emitted in the same live pass and are not legacy."** —
   **REFUTED.** Max `written_at` for both cohorts is `2026-07-13T23:56:41` (the rebuild), not 2026-04-13. Microsecond
   adjacency is evidence **for** the bulk-rebuild-artifact explanation, iterating a data_type list — not against it.
8. **"ODDS_API is a 100%-dead venue."** — **REFUTED.** It has **165,677 captured rows across 94 leagues** (306,416
   total). It is dead only on the bookmaker axis. It must be **excluded from every purge scope** — this is the same
   class of error as the original "impossible order-book trades" conclusion: a subset read as a total. Its legitimate
   provider axis (`_LEAGUE_PARTITIONED_VENUES`, `venue_fetch.py:101`) must not be touched by step 1.2.
9. **"Prediction-venue rows are provably stale because their dates stop at 2026-06-20 while in-scope venues run to
   2026-06-27."** — **WEAKENED, do not cite this evidence.** PADDYPOWER, UNIBET, DRAFTKINGS, SKYBET, FANDUEL and CORAL
   **also** stop at 2026-06-20; the 2026-06-27 tail is unique to the enumerated scope keys precisely because sentinels
   keep emitting past the last capture. The conclusion (stale residue predating the 2026-06-21 exclusion) is still
   probably right, but it rests on the code filter at `venue_fetch.py:144`, not on the date gap.
10. **Adding a `first_capture_date` third gate axis (`EXPECTED_BOOKMAKER_NOT_YET_ONBOARDED`).** — **DEPRIORITIZED, do
    not build yet.** The payoff was measured at 7,645 `attempted_failed` rows (6.8%), and it was scoped against the
    wrong root cause. After steps 1.2 + 3.3 remove the phantom axes, re-measure — most of that 7,645 lives on bare
    BETFAIR, which will no longer exist. Revisit only if the residual is still material. If it is, the derivation is
    cheap: `refresh_sports_bookmaker_league_coverage_2026_06_21.py:54-63` already groups by `(venue, league)` over
    captured rows and only needs `.min()` on date — no new corpus walk.

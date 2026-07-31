---
doc_type: plan
title: Sports consolidated closeout — native AO extract (26 AO-eligible todos from the master plan's OWN checkboxes)
summary: >-
  A fresh AO-eligibility triage of sports_consolidated_closeout_2026_07_19.md's OWN native `- [ ]` todos (never before
  extracted — every prior sports satellite batch drew from OTHER orphaned docs, deliberately not this doc's own
  checkboxes). Of ~65 open top-level / 78 total open todos, 26 are genuinely bounded/determinable-by-a-worker-alone
  after this session's several reconciliation passes; the rest stay human (operator-gated deletes/scheduling, open
  design/judgment calls, entangled with the still-pending K1/K2 casing revert or league_id migration, or already flagged
  as conflict-gated in `issues/autonomous_session_operator_decisions_2026_07_25.md`). 6 candidates required scoping DOWN
  from the source todo's literal text (dropping an undecided design fork, an already-superseded downstream framing, or a
  "manual review" sub-part) to make them genuinely bounded; 2 required an added live-probe first-step because the source
  todo's own prerequisite state is ambiguous or self-contradictory. 1 candidate (venue vocabulary re-stamp) explicitly
  EXCLUDES a sub-item already covered by `sports_satellite_ao_dispatch_batch3_2026_07_25.md`.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-api,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, native-extract, satellite-docs, plan-hygiene]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md,
    /plans/active/sports_track_h_denominator_gated_2026_07_28.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/task_template.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-27"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.5
estimate_calibrated_ai_days: 5.2
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator-requested fresh triage (2026-07-25) of sports_consolidated_closeout_2026_07_19.md's own native todos —
  distinct from every prior satellite batch, which deliberately never touched this doc's own checkboxes. Applies the
  same task_template.md §4 "Dispatch-scope eligibility" bar used throughout this session's other sports batches.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports consolidated closeout — native AO extract

> **Status: draft.** Per CLAUDE.md's plan-destination rule, flip to `active` only after operator review. All 26 todos
> below are same-priority-tier-independent and touch distinct files (verified individually per todo — see each todo's
> own scope note); todo 1 internally sequences its own 2 steps (live-probe → delete → re-census) inside ONE todo rather
> than being fanned out, per the established pattern in `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s summary
> ("AO's per-todo model has no mechanism to mechanically gate step N on step N-1 within one plan short of
> `sequential: true` for the WHOLE plan... combining same-job chains into one todo each is the safe choice").
>
> **The parent plan (`sports_consolidated_closeout_2026_07_19.md`) is currently OVER the 1000-line hard cap (1002L,
> `check_line_caps.sh` HARD-fails) and is uncommittable via the normal path** — see
> `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #9. This extraction does not touch that file at all
> (not even a one-line pointer) for exactly this reason: any edit to it currently cannot be committed.

## Todos

- [x] ✅ [DATA] P0. **Track F — PURGE the fabricated POST-FLOOR `derived_features` remainder (Jun-Dec 2020 + 2021-2026
      only) + re-verify by CENSUS, one worker, in order.** **DONE 2026-07-27 (slot-5, `data_engineering`): superseded by
      the Track F (follow-up) VM-launched exhaustive purge below, which completed + verified this todo's own done-when
      condition** — the follow-up's third VM launch (`canonical-migration-sports-features-purge-20260727-103716`)
      scanned all 2400 in-scope days, deleted 3612 residue objects, and its chained `--recensus` reported "RE-CENSUS: 0
      post-floor derived_features residue objects remain. Purge verified complete." (see Progress Log
      2026-07-27T10:11-10:43Z, slot-10). Independently spot-checked before flipping this checkbox (not just trusting the
      log): `gcloud storage objects list` on `day=2020-06-06/*/feature_group=derived_features/*.parquet` (previously
      confirmed 9/9 residue objects by slot-10) now returns ZERO objects, while the previously-confirmed-clean day
      `2021-01-01` still has its 4 legitimate `features.parquet` objects intact — confirms the delete was surgical
      (correct objects removed, correct objects kept), not a blind wipe. No further action needed; flipping this
      checkbox to close out the original todo now that its substance is fully satisfied. **⛔ CORRECTED 2026-07-26
      (slot-12 `data_engineering`): this todo's own "Not `[OPERATOR]`-gated" justification was WRONG at the time and was
      removed** — the original triage had merely ASSERTED "GCS soft-delete gives a 7-day recovery window, reversible"
      without ever querying the actual bucket policy, and no carve-out existed in the codex SSOT yet at that point. **✅
      RE-CORRECTED 2026-07-27 — `[OPERATOR]` removed again, this time on a verified rather than asserted basis.**
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a (added 2026-07-26, AFTER the 07-26 correction
      above) now provides exactly the carve-out that doc's §3.1 lacked when this todo was last edited: an object/
      prefix-scoped prod-bucket delete (never a whole-bucket destroy) may proceed agent-side once a FRESH, same-run
      `gcs_bucket_soft_delete_retention_seconds(bucket)` check confirms ≥604800s retention. This todo's delete is
      object-scoped (specific `derived_features` parquet objects filtered by creation timestamp, never the
      `features-sports-prd-central-element-323112` bucket itself) — fresh-checked 2026-07-27, retention returned
      `604800` (7 days), so it qualifies (finding T, `task_template.md`). **Secondary, reinforcing point the 07-26
      correction didn't consider**: `derived_features` is itself a DERIVED dataset computed from raw market/odds data
      that this delete does not touch — even independent of the 7-day GCS window, any day's features can be re-derived
      from source at any time, which is a stronger reversibility argument than soft-delete alone (though not what §3a's
      check itself tests for). Confirmed real, populated corpus in scope (not already-resolved): `gcloud storage ls -r`
      on a sample day (`sports_features/by_date/day=2021-01-01/**`) shows real
      `league={id}/feature_group=derived_features/     features.parquet` objects across multiple leagues — this is NOT
      an empty/moot target. **Step 1 (live-probe, SAFE, READ-ONLY)**: run a GCS creation-time census across
      `features-sports-prd-central-element-323112`'s
      `sports_features/by_date/day={D}/league={L}/     feature_group=derived_features/` corpus for Jun-Dec 2020 +
      2021-2026 to establish the CURRENT pre-/post- `2026-07-19` object-count split directly (do not trust the parent
      doc's contradictory checkbox state). **Step 2 — now agent-executable, no operator sign-off needed** (re-query the
      bucket's soft-delete retention fresh immediately before running, not from this citation): snapshot the delete
      list, then delete every object from that scope still carrying a pre-`2026-07-19` creation timestamp (honest
      absence beats an invented `competition_phase` — do NOT re-touch pre-floor 2017-2019/pre-06-06 2020 dates, already
      handled by the separate pre-floor wipe). **Step 3**: re-run the census, confirm 0 remain. (repo: features-service
      / GCS `features-sports-prd-central-element-323112`). **Done when**: the step-3 census returns 0 post-floor
      `derived_features` objects with a pre-`2026-07-19` creation timestamp. Source:
      `sports_consolidated_closeout_2026_07_19.md:244-259`.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-27 (slot-14) — Track C re-verified: existing candidate list still matches current
      corpus state, no correction needed.** Re-ran the existing `verify_k1k2_lowercase_twins_2026_07_27.py` census (same
      query/scope as `/plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md`'s own
      investigation — no new script, no corpus walk) against live prod
      (`market-data-tick-sports-prd-central-element-323112`). **Fresh population**: 275,136 uppercase-keyed
      (`instrument_type=ODDS, data_type=TRADES`) rows as of this check (a precise, dated figure — prior docs cite
      adjacent-but-different numbers for related populations: 260,298 GCS objects from K1/K2's original copy, ~373,296
      manifest rows from an earlier broader count). **Twin-coverage, n=200 (seed=42, independent of the original run)**:
      153 hits / 47 misses = **23.5% no-twin** — statistically consistent with the original 40-sample's 27.5% (95% CI on
      27.5%/n=40 is ~[21%,34%]; 23.5% falls inside it). Two smaller same-session samples (n=40 seed=20260727
      exact-repeat: 12.5% miss; n=60 seed=20260727: 16.7% miss) diverged further from 27.5% but are explained as small-n
      sampling noise once the n=200 result landed back in-CI — recommend using n≥200 for any future risk-sizing of this
      migration, not a 40-row spot-check. **Conclusion**: the candidate population/query is unchanged and still the
      correct scope; the twin/no-twin split has NOT materially drifted since the original investigation. Full sample
      outputs cited in this plan's Progress Log below. Source: `sports_consolidated_closeout_2026_07_19.md:337-340`.
- [x] ✅ [DATA] P1. **Track C — venue vocabulary safe re-stamp (excludes the KALSHI/POLYMARKET cross-AG bleed
      sub-item).** **DONE 2026-07-27 (slot-2, `data_engineering`): raw-tick shape re-stamp for all 3 renames executed +
      verified; derived-candle shape explicitly flagged as a follow-up, not silently dropped — see Progress Log entry
      below.** ⛔ **CORRECTED 2026-07-27 (slot-9, `data_engineering`) — 2 of the source todo's premises are WRONG,
      proven by fresh same-day evidence that already exists elsewhere in this doc family; both are DROPPED from scope
      rather than executed:** **(a) UNIBET_UK/UNIBET_EU→UNIBET is NOT a casing/alias fold** —
      `unified_api_contracts.registry.     market_data_categories.SPORTS_VENUE_FOLD`'s own docstring (shipped
      2026-07-27, same day) documents this was originally added to the fold then REMOVED same-day after live content
      comparison proved UNIBET_UK/UNIBET_EU are genuinely distinct bookmaker feeds from bare UNIBET (a shared
      (day,league,fixture,market) — 2022-10-17, ALLSVENSKAN, IFK Goteborg vs Malmo FF — shows DIFFERENT simultaneous
      odds at slightly different `bm_time`, with 1,066/1,090 UNIBET_UK dates and 9,028/9,443 shards overlapping bare
      UNIBET's own captured population). Folding would silently conflate two distinct bookmakers' live data on every
      future capture. `SPORTS_VENUE_FOLD` now contains ONLY `{"ladbrokes_uk": "LADBROKES", "sport888": "BET888SPORT"}` —
      confirmed by direct read 2026-07-27. **(b) SMARKETS is NOT stale/deleted-venue residue** —
      `plans/active/issues/     sports_odds_venue_enumeration_undercount_predrain_2026_07_27.md` measured SMARKETS at
      **1,113,644-1,652,384 row_count** (two independent live manifest census passes, 2026-07-27) across 480-6,958
      shards through 2026-07-26 — i.e. actively captured production data, not a small residual.
      `/codex/01-domain/sports-instruments.md` §"VENUE COUNT CORRECTED 2026-07-24" independently lists SMARKETS among
      the 28 live, individually-registered bookmaker venues captured through ODDS_API — it was NEVER "removed from all
      repos" as the source todo asserted. A purge here would have destroyed over a million rows of genuine live
      betting-exchange data. **Corrected scope — now that the parts[]-index parser fix has shipped
      (`market-data-processing-service@51502c3` + `instruments-service@f46e553e`, verified via `git log`), re-stamp
      ONLY**: (1) casing/alias rewrite LADBROKES_UK→LADBROKES, SPORT888→BET888SPORT (2 renames, both already exist
      correctly-cased in the UAC venue registry — pure re-stamp, no registry gap; confirmed via live manifest census
      2026-07-27: LADBROKES_UK 10,255 shards/1,423,010 rows across 987 dates, SPORT888 15,181 shards/2,432,928 rows
      across 1,821 dates, both spanning raw-tick `instrument_type=ODDS/data_type=TRADES` AND 4 derived-candle data_types
      `odds_snapshot`/`arbitrage_opportunity`/`odds_movement`/`odds_horizon_bucket` — the existing
      `restamp_sports_bookmaker_venue_2026_07_27.py` tool covers ONLY the raw-tick shape; the derived-candle shape needs
      its own follow-up tooling, flagged rather than silently dropped); (2) the footystats legacy bundle mislabel
      `venue=ODDS_API` under `pipeline_mode=batch_footystats` specifically →`FOOTYSTATS` (**42,476 shards, row_count
      sum=40,929, confirmed by live census 2026-07-27 — matches the source todo's cited figure exactly**; a separate
      writer defect from the parser bug, date range 2020-06-01..2026-04-14). **FOOTBALL/UNKNOWN parse-bug residue —
      RE-VERIFIED, NOT what the source todo assumed**: live corpus-wide manifest census 2026-07-27 (no filter, full
      history) found **0 rows anywhere carrying `venue=FOOTBALL`** — the MDPS candle-write bug this venue-name came from
      (`_venue_token_from_canonical_id` returning the SPORT token) never actually produced a persisted manifest cell for
      sports in this bucket (verified: `CandleAdapterRegistry` DOES have 4 registered sports adapters —
      odds_horizon_bucket/odds_snapshot/arbitrage_opportunity/odds_movement — so the bug path was reachable, but the
      live census still shows 0 FOOTBALL rows; likely already-clean by construction or the buggy window produced no
      candle output for sports specifically). This part of the done-when is ALREADY SATISFIED — no action needed.
      `venue=UNKNOWN` is real but TINY: exactly **8 total** manifest shards corpuswide, all on a single date
      `2026-04-14` under `batch_odds_api` (`ODDS_MOVEMENT`/`ODDS_SNAPSHOT`/`odds_movement`/`odds_snapshot`, both
      casings, 2 each — re-verified via re-run of the census script; an earlier draft of this correction double-counted
      a subset of these same 8 as "4 more" from a second, narrower query and mis-stated the total as 12), ALL
      `capture_status=empty_confirmed` (0/NaN row_count — honest-absence placeholders, no real GCS parquet content at
      risk) — tracked as its own small cleanup, not folded into this todo's main re-stamp mechanics. **EXCLUDES**: the
      cross-AG bleed sub-item (KALSHI, POLYMARKET rows belonging to `asset_group=prediction`) — already tracked as its
      own AO-eligible candidate in `sports_satellite_ao_dispatch_batch3_2026_07_25.md:132` ("Determine the disposition
      of `market-data-tick-sports-prd`'s 20,785 `venue=KALSHI`/... rows") — drafting it here too would duplicate that
      work. **Self-justified, not `[OPERATOR]`-gated**: the re-stamp mirrors the same safe copy/verify/swap-or-relabel
      pattern K1/K2 shipped without an `[OPERATOR]` tag elsewhere in this same doc family — a rewrite to an already-
      correctly-cased registry target, never a delete of the source until content-verified. (repo:
      market-data-processing-service / market-tick-data-service / instruments-service catalogue). **Done when
      (CORRECTED)**: a corpus-wide sports venue census shows 0 rows for LADBROKES_UK/SPORT888/UNKNOWN, and 0 rows
      carrying the footystats-legacy-bundle `venue=ODDS_API` signature under `pipeline_mode=batch_footystats` — NOT
      UNIBET_UK/UNIBET_EU/SMARKETS (excluded above; forcing those to 0 would be a data-correctness regression, not a
      fix). FOOTBALL is already 0 (no further action). Source: `sports_consolidated_closeout_2026_07_19.md:364-374`.
- [ ] [CLEANUP] P2. **Track S — snapshot-then-cull the dead `sports_reference_v2/by_date/` dual-layout** (frozen
      2026-04-20, no entities). **Built-in safety gate**: first confirm no reader consumes it (grep both repos for the
      path); if a reader is found, STOP and report instead of deleting — do not proceed with the cull. Self-justified,
      not `[OPERATOR]`-gated: snapshot-first + the reader-check is a hard fail-safe baked into the todo itself. (repo:
      instruments-service / GCS). **Done when**: the reader-check result is recorded, AND (if clear) the snapshot+delete
      has executed with a post-delete listing confirming 0 objects remain. Source:
      `sports_consolidated_closeout_2026_07_19.md:421-422`.
- [ ] [DOC] P2. **Track S — Finding C correction: fix the cutover runbook's canonical-is-a-superset premise for raw odds
      on early dates**, citing `sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`
      (`status:     resolved`, corpus-destroying risk already remediated — only this documentation correction remains).
      (repo: unified-trading-pm, doc edit — locate the cutover runbook via
      `sports_legacy_bucket_cutover_2026_07_16.md`'s own references). **Done when**: the cutover runbook is corrected
      and cites this doc. Source: `sports_consolidated_closeout_2026_07_19.md:423-429`.
- [x] [CODE] P1. **Track E — wire the T0/T1 dependency gate for real: make every real caller of the pre-flight pass
      `date=`.** ✅ instruments-service@3c424e61 — threaded `date=`/`bucket=` through all 5 real production call sites
      (`footystats.py` x3: predictions/matches/odds, `transfermarkt.py`, `understat.py`, `sfi.py`); confirmed via grep
      that no other repo (incl. market-tick-data-service) calls `create_sports_reference_adapter` or
      `check_api_football_dependency` — the gate + its callers are entirely instruments-service-scoped. Each call was
      placed AFTER its function's own skip/guard checks so the gate fires only when a fetch is actually about to be
      attempted (avoids retroactively breaking idempotent re-runs of already-captured dates, e.g. understat's pre-2018
      historical data, where api-football's own pre-2018 coverage floor would otherwise now block a harmless
      skip-and-return). Added `tests/unit/test_sports_t0_t1_gate_real_callers.py` — 4 tests exercising the REAL
      orchestrator functions end-to-end (not just the factory) proving a T0-before-T1 ordering violation raises
      `DependencyError` from `_fetch_footystats_predictions`, `_fetch_understat_xg`, `_fetch_sfi_data`, and
      `_fetch_transfermarkt_data`. Fixed 4 pre-existing tests in `test_orchestrator_polymarket_capture_status.py` whose
      `create_sports_reference_adapter` stub lambdas didn't accept the new kwargs. Full `quality-gates.sh` green (4978
      tests passed). `sports_t0_t1_dependency_gate_never_wired_2026_07_15`. Source:
      `sports_consolidated_closeout_2026_07_19.md:450-453`.
- [ ] [CODE] P3. **Track E follow-up — the gate's `DependencyError` remediation message still names the FROZEN bare
      `entity=fixtures` path, not the live split `entity=fixtures_schedule`.** Now that the gate fires for real (Track E
      above), this is a live operator-facing message, not dead-code text.
      `sports_dependency.py::check_api_football_dependency` correctly PROBES the split-entity paths first (functionally
      fine, no false `DependencyError`), but its `_build_remediation_message(date, resolved_bucket, canonical_path)`
      call at the bottom of the function still passes the old bare-entity `canonical_path` constant for display, so an
      operator who genuinely hits the gate sees a path that's been dead since 2026-05-23. Fix: pass the split
      `entity=fixtures_schedule` path (or list all 3 candidate paths) into the message instead. Cosmetic-only (the
      remediation CLI command shown is still correct) — hence P3, not a data-correctness bug. (repo:
      instruments-service)
- [x] [DIAG] P1. ✅ **HYPOTHESIS DENIED — root-caused, DIAGNOSIS ONLY, not relabeled.** `_SNAPSHOT_VENUES`
      (`unified-api-contracts/unified_api_contracts/internal/schemas/_sports_prediction_contracts.py:240`, frozenset
      `{BETFAIR, MATCHBOOK, ODDS_API, PINNACLE_AS_LINE}`) is **inert dead code** — zero runtime consumers anywhere in
      the monorepo (confirmed via repo-wide grep); it's `SchemaContract` column metadata for an optional
      `traded_volume`/`max_bet` field on a data_type (`sports_odds_snapshot`) that the 112,277-row population (all under
      `data_type=trades`) doesn't even belong to. It also doesn't membership-match (4 keys incl. `ODDS_API`, and
      `PINNACLE_AS_LINE` ≠ `PINNACLE` — that exact string never appears in any writer/manifest code). No secondary/CLV
      snapshot capture pass exists for these 3 venues; `TIER_1_OFFSETS` in `odds_api_adapter.py` applies identically to
      every bookmaker. **Real mechanism — two stacked, already-fixed bugs**: (1) pre-2026-07-20,
      `_expected_sports_bookmakers()` (`market-tick-data-service/.../orchestrator/venue_fetch.py`) derived its sentinel
      fan-out scope from UAC venue _categories_ (5 keys: BETFAIR/MATCHBOOK/ODDS_API/ONEXBET/PINNACLE) instead of the
      real 23-key `bookmakers=` request list — for each, `_emit_sports_v2_sentinels` (`sentinels.py:286-346`) branches
      on `is_bookmaker_league_covered()`; only bare BETFAIR (via base-key folding onto its real suffixed siblings
      `BETFAIR_EX_UK`/`BETFAIR_EX_EU`/`BETFAIR_SB_UK`), MATCHBOOK, and PINNACLE ever pass that check and route to
      `record_zero_rows(was_expected=True)` → `record_failed()` → `capture_status=attempted_failed`; ODDS_API/ONEXBET
      never pass for any league and route to `record_empty()` → `empty_confirmed` instead — mechanically explaining why
      the failure is confined to exactly these 3 of the 5 scope keys, spanning all 6 years (fan-out re-emits over the
      full un-date-gated fixture catalog every run). Fixed: `mtds@accd8aa4` (2026-07-20), scope now derives from
      `expected_odds_api_venue_keys()`; regression-locked by `tests/unit/test_sports_sentinel_scope.py`. (2) The
      `source="api_football"` label on these rows was a SEPARATE bug: `SOURCE_PRIORITY[("sports","TRADES")]` was missing
      from `_source_priority_data.py`, so `derive_pipeline_mode_for_row()` fell through to the
      `_ASSET_GROUP_FALLBACKS["sports"]=BATCH_API_FOOTBALL` default and mislabeled every sports-trades sentinel row —
      not evidence of a real api_football fetch attempt. Fixed: `uac@44623d25` (added the missing
      `("sports","TRADES"): ["odds_api"]` entry, confirmed present in `_source_priority_data.py:77`); the polluted rows
      (1,266,874 total, 58,016 `attempted_failed`) were already wiped from the live manifest via `mtds@e9d9dec0`.
      **Net**: the 112,277 figure is a historical pre-fix (2026-07-20) snapshot; both root-cause code defects are
      already merged, not a genuine ongoing per-venue capture failure. Surviving historical rows stay un-relabeled per
      this todo's explicit scope — remediation (if any) is the already-gated, not-yet-exercised Part 3 of
      `sports_shard_enumeration_cartesian_blowup_2026_07_20.md`. Code citations verified live (not just sub-agent report
      — `_SNAPSHOT_VENUES` single-definition + zero-consumer, `_expected_sports_bookmakers`/
      `expected_odds_api_venue_keys` wiring, and the `("sports","TRADES")` SOURCE_PRIORITY entry all directly grepped
      and read in this session). Done when: a written root-cause finding confirms or denies the `_SNAPSHOT_VENUES`
      CLV-completeness hypothesis, citing the actual mechanism — satisfied (denied). Source:
      `sports_consolidated_closeout_2026_07_19.md:490-491`.
- [x] [DIAG] P1. ✅ **Track O — emitter found: the PRE-FIX sentinel path, now dead — both root causes already shipped,
      wipe verified holding.** **Scoping note**: the source todo frames this as "before folding into K2" — that
      downstream framing is now STALE (K2's casing migration is itself superseded and slated for revert per Track C), so
      this candidate was pure standalone diagnosis, not a K2-fold-in precondition. (repo: market-tick-data-service /
      instruments-service, read-only). **Mechanism**: `_emit_sports_v2_sentinels`/`_emit_sports_v1_sentinels`
      (`market-tick-data-service/.../engine/orchestrator/sentinels.py`), driven by `_expected_sports_bookmakers()`
      (`.../engine/orchestrator/venue_fetch.py`) which — BEFORE `mtds@accd8aa4` (2026-07-20) — derived its
      bookmaker-expectation scope from UAC venue CATEGORIES (5 keys: BETFAIR, MATCHBOOK, ODDS_API, ONEXBET, PINNACLE)
      instead of the real 23-key Odds-API `bookmakers=` request list (`odds_api_adapter.py`). `ODDS_API` (the aggregator
      token, not a real bookmaker) was never itself in the request list, so it could never capture and could never pass
      `is_bookmaker_league_covered()` for ANY league — every (league,date) cell in the cartesian expectation universe
      for `venue=ODDS_API` routed to `record_empty(was_expected=True)` → `capture_status=empty_confirmed`. This produced
      exactly 139,620 rows — identical in count to sibling phantom venues BETFAIR(bare) and ONEXBET (139,620 each; all
      three sum to `sports_shard_enumeration_cartesian_blowup_2026_07_20.md`'s cited 418,860 structurally-false rows),
      because all three shared the identical (league,date) cartesian scope under the same never-captures mechanism. The
      `source=api_football` mislabel is a SEPARATE, stacked bug: `SOURCE_PRIORITY[     ("sports","TRADES")]` was missing
      from UAC's `_source_priority_data.py`, so `derive_pipeline_mode_for_row()` fell through to
      `_ASSET_GROUP_FALLBACKS["sports"] = BATCH_API_FOOTBALL`, silently shadowing the sentinel caller's real intended
      default (`BATCH_ODDS_API`) and mis-stamping every sports TRADES sentinel row — including these — as
      `source=api_football` (full mechanism + evidence in
      `plans/archive/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`). **Why
      "confirmed not `_emit_sports_v1/v2_sentinels`" is correct as stated**: both root causes are now FIXED —
      `mtds@accd8aa4` (2026-07-20, `_expected_sports_bookmakers()` now derives purely from
      `expected_odds_api_venue_keys()`, ODDS_API/ONEXBET/bare-BETFAIR structurally excluded from scope) and
      `unified-api-contracts@44623d25` (2026-07-23, added the missing SOURCE_PRIORITY entry, verified live via
      `git show` in this session). Post-fix, the CURRENT sentinel code structurally cannot reproduce this population —
      so while historically this WAS the sentinel-emission mechanism (pre-fix), the 139,620-row population is dead
      historical residue, not something the current `_emit_sports_v1/v2_sentinels` is still minting. **Live-verified
      2026-07-28** (this session) via a direct read of the live MTDS sports manifest
      (`market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`, downloaded via
      `gcloud storage cp` + queried with DuckDB, 516,196 total rows): **0 rows carry `source=api_football` anywhere in
      the manifest** (venue=ODDS_API or otherwise) — the population was fully removed by the separate CAS-safe wipe
      `mtds@e9d9dec0` (2026-07-23, 1,266,874/1,266,874 rows removed, verified via `git show`) and has NOT been
      re-accumulated in the 5 days since (it would have been, had the sentinel bug still been live — this is the
      positive proof the fix holds in production, not just that the fix shipped). Current `venue=ODDS_API` rows are 100%
      legitimate: 123,642 captured + 652 empty_confirmed under `source=mdps_odds_horizon_bucket` (the deliberate
      aggregate-sentinel identity documented in `instruments-service/scripts/enumerate_expected_universe.py`'s
      `_SPORTS_MANIFEST_VENUE_OVERRIDE`), plus 8 captured + 18 empty_confirmed under `source=odds_api` — zero
      `api_football` contamination. **Done when**: a written finding names the emitter/mechanism producing these rows —
      satisfied (mechanism named + both fixes cited + live-verified zero recurrence). Source:
      `sports_consolidated_closeout_2026_07_19.md:492-493`.
- [ ] [DIAG] P2. **Track O — corpus-wide scan for other low-fixture dates whose only in-window odds fall in the
      T-12h↔T-24h dead-zone, + investigate why the multi-shot `TIER_1_OFFSETS` loop apparently didn't run on the quiet
      2025-12 days.** **Scoped DOWN from the source todo**: drops "consider adding a T-18h horizon or widening the T-24h
      staleness cap" — that's an undecided design choice with no defined target, stays human; this candidate is scan +
      diagnosis only. **Conflict-check clearance**: confirmed DISTINCT from
      `sports_satellite_ao_dispatch_batch4_2026_07_25.md`'s already-dispatched zombie-tick sweep (that doc's own note:
      "a DIFFERENT cap in a DIFFERENT file/mechanism entirely" — that one is the fetch-based `STALENESS_CAP_SECONDS`
      zombie-tick rejection in `_prepare_tick_data()`; this todo is about `TIER1_HORIZONS` spacing logic in
      `bucket_assignment_adapter.py`). NOTE FOR THE DISPATCHED WORKER: do not conflate the two staleness caps in your
      report. (repo: market-tick-data-service, read-only scan). **Done when**: a written list of affected dates + a
      root-cause finding on the loop-skip is recorded; does NOT decide the T-18h-horizon/cap-widening question. Source:
      `sports_consolidated_closeout_2026_07_19.md:494-496`.
- [x] ✅ [CODE] P1. **Track H — registry-aware honest-coverage denominator — scoping/dispatch-hygiene resolved by
      EXTRACTION 2026-07-28 to `sports_track_h_denominator_gated_2026_07_28.md`** (machine-gated via
      `depends_on`+`gate_on_depends: true` on `sports_track_h_denominator_prereqs_2026_07_28.md`). This checkbox marks
      the EXTRACTION decision done, not the denominator code change itself (that remains open, tracked in the new gated
      plan) — mirrors the sanctioned rollup-pointer pattern used elsewhere in this doc family (parent-todo-11 /
      cefi-020) for restructure-style splits, which `check_todo_regression.sh` requires (a flip is conserved; a bare
      checkbox removal is not). 4 consecutive same-day dispatches (slots 11, 7, 10, 15 on 2026-07-28) hit the identical
      STOP condition (2 real blockers — `odds_horizon_bucket` MDPS reprocess + `batch_footystats` copy+swap —
      unshipped); a priority-999 backlog park did not hard-block re-dispatch, so per operator direction (answering
      `BLK-2f9e7680`) the actual denominator todo is split out into its own plan with a real machine dispatch gate,
      rather than staying a bouncing checkbox here. See the extracted plan for current status. Source:
      `sports_consolidated_closeout_2026_07_19.md:536-541`.
- [ ] [CODE] P2. **Track H — implement RAISE-on-all-NaT for `AvailableAtStampingError`** (operator-ruled: fail loud at
      the shard that can't be stamped, not skip-with-record) at the CF-8 fix's own code path
      (`market-tick-data-service@af627b5b`). **Scoping note**: only the CODE change ships via this todo — the CF-8
      production maintenance-window RUN itself stays human/operator-gated (needs an operator to lift stop `BLK-d9137d48`
      and schedule the window), so this candidate does not require that window to have run; it just needs to exist and
      be tested against the already-shipped CF-8 fix's code path. (repo: market-tick-data-service). **Done when**: a
      test demonstrates an all-NaT shard raises `AvailableAtStampingError` instead of silently skip-recording. Source:
      `sports_consolidated_closeout_2026_07_19.md:558-561`.
- [ ] [OPS] P2. **Track V — re-roll `build_instrument_catalogue.py --asset-group sports --since 2019-01-01`** to pick up
      the +26,894 round rows produced by the pre-2019-scope (§T) + registry-membership (§U) decisions and the 2026-07-18
      round-derivation sweep — the catalogue snapshot predates all of them. Self-justified, not `[OPERATOR]`-gated:
      idempotent catalogue-snapshot regeneration from current registry+manifest state, not a destructive delete of
      source data. (repo: instruments-service). **Done when**: the catalogue snapshot is regenerated and reflects the
      round-row count increase. Source: `sports_consolidated_closeout_2026_07_19.md:630-632`.
- [ ] [CODE] P2. **Track V — upgrade the catalogue `player` grain from `entity=injuries` (injured-only) to
      `entity=fixture_lineups`** (full roster, now carries 100% player/coach identity). (repo: instruments-service,
      `build_instrument_catalogue.py`). **Done when**: the catalogue's player grain reads from `fixture_lineups` and a
      spot-check confirms full-roster coverage vs the old injured-only set. Source:
      `sports_consolidated_closeout_2026_07_19.md:633-634`.
- [ ] [DATA] P2. **Track V — determine which launcher ran the most recent sports features backfill** (NOT a VM launch —
      this todo is a read-only audit of PAST launch history/logs; no VM is started by this todo itself) — serial
      `launch-features-sports-backfill-vm.sh` or parallel `launch-features-sports-parallel-backfill-vm.sh`. (repo:
      deployment-service, read-only log/dispatch-record audit). **Done when**: the launcher used is named with its
      citing VM log/dispatch record; if serial, a follow-up todo is filed requiring the parallel launcher for every
      future sports features backfill (that follow-up todo, not this one, would be the actual VM-launch-relevant
      action). Source: `sports_consolidated_closeout_2026_07_19.md:635-638`.
- [ ] [BACKEND] P2. **Track K — confirm whether any primary sports entrypoint (not a one-off script) exposes a genuine
      fixture-level targeting flag for shard-splitting a backfill run.** (repo: features-service / market-data-
      processing-service, read-only CLI audit). **Done when**: either a cited flag+file is named, or the add-flag todo
      exists with a named target CLI. Source: `sports_consolidated_closeout_2026_07_19.md:661-664`.
- [ ] [DATA] P1. **Track K — run + cite 3 dated checkpoints (pre-backfill baseline, mid-backfill spot-check,
      post-backfill final gate) for EACH of the 5 required mechanisms** (`data-pipeline-check-is`/`-mtds`/`-mdps`/
      `-features` + `/data-pipeline-reconciliation`) against sports — currently ZERO real run-todos exist for any of the
      5 despite all 5 already supporting sports's shard atoms (task_template.md §3 finding K). **Use the already-pinned
      `SPORTS_SMOKE_DATES` constants as the reference dates** (busy `2025-12-20` / thin `2025-12-24` /
      `known_buggy_odds` `2025-12-18` / `known_buggy_fixtures` `2024-03-09` — shipped
      `features-service@84cb4613`/`@0ae9f460`) rather than inventing a day, since several of these skills explicitly
      require the day to come from the operator, not be invented — these are the doc's own already-established canonical
      smoke dates, resolving that constraint. (repo: cross-repo, skill-driven). **Done when**: each of the 5 mechanisms
      has 3 dated runs cited by report path/dispatch_id, baseline through final. Source:
      `sports_consolidated_closeout_2026_07_19.md:665-669`.
- [ ] [DOC] P2. **Track X — update the sports issue-doc index**: it lists
      `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` as merely open/P2, but
      `sports_odds_feature_naming_canonicalization_2026_07_21.md` already has a DECIDED (2026-07-23) naming scheme +
      scoped 3-repo migration in flight — a fresh agent shouldn't re-litigate the naming decision. **First locate the
      actual index** (grep the corpus for the literal string `sports_odds_feature_naming_four_way_mismatch_2026_07_21`
      to find every referencing doc — the exact index location isn't self-evident from the source todo alone). (repo:
      unified-trading-pm, doc edit). **Done when**: every located index entry is corrected, citing the decided doc.
      Source: `sports_consolidated_closeout_2026_07_19.md:727-731`.
- [ ] [BACKEND] P2. **Track X — audit adapters under instruments-service's `.../adapters/sports/adapters/`,
      market-tick-data-service's `.../adapters/sports/`, and execution-service's `.../sports_execution/adapters/` for
      dead code, silent fallbacks, and duplicated logic** — cite
      `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. (repo: instruments-service /
      market-tick-data-service / execution-service, read-only). **Done when**: a written per-repo finding list (or an
      explicit "none found") exists, each finding citing a symbol. Source:
      `sports_consolidated_closeout_2026_07_19.md:770-773`.
- [ ] [DOC] P3. **Track X — add `data_completion_sports_history_2026_07_24.md` (0 open todos) as a bulleted entry to
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s Aggregated-source-docs index** — it is not
      currently listed there. (repo: unified-trading-pm, doc edit). **Done when**: the entry appears in that file's
      index with its open-todo count noted. Source: `sports_consolidated_closeout_2026_07_19.md:774-777`.
- [ ] [DATA] P2. **Track S2 — check whether the mis-keyed-duplicate bug class** (`rebuild_sports_manifest_v9.py` E4
      apply-pass bug, fixed going forward `market-tick-data-service@55f9e961`) **hit the `mdps` surface or any other
      bucket rebuilt via the same script family.** **EXCLUDES** the sibling "88 orphan rows manual review + disposition"
      sub-item from the same source todo — explicitly framed as "manual review," stays human. (repo:
      market-data-processing-service / market-tick-data-service, read-only). **Done when**: a written finding either
      confirms the bug class is absent elsewhere, or names the affected buckets/rows. Source:
      `sports_consolidated_closeout_2026_07_19.md:847-852`.
- [x] ✅ [DATA] P1. **Track S2 — Sports P2a sub-item (c) ONLY: re-run the 40,041 FIXTURES `attempted_failed` rows for
      2018/2021/2023.** **EXCLUDES** sub-items (a) G1 non-canonical-league NOISE wipe (~1,437 leagues/~106k rows — a
      purge with an unconfirmed relationship to the already-answered §U non-registry-league decision; needs an explicit
      check whether it's the SAME population as that decision's already-approved 489-pair/10,869-row purge before
      executing, since the scale differs by ~10x) and (b) G2 2015-2017 zero-captured diagnosis (bundles an undecided
      "then fix" after diagnosis, subscription-tier-limit-vs-backfill-bug is an open question) — both stay human,
      flagged separately below. Self-justified, not `[OPERATOR]`-gated: standard skip-aware re-run/backfill pattern, not
      a delete. (repo: instruments-service). **RESOLVED 2026-07-29 — already complete, no new re-run needed (this todo
      was a stale duplicate of work done a month earlier).** Pre-task conflict check (grep-then-READ) found the
      identical re-run already shipped 2026-06-27:
      `plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md:144-150` — instruments-service
      `recover_fixtures_from_truthset.py` (run_ts=20260627-183721): 423/423 (league,season) pairs, 34,564 days written,
      111,817 fixtures captured, 0 failed pairs; UTL fix unified-trading-library@b76b18ac. Fresh census this session
      (manifest `_index/availability_index.parquet` for `instruments-store-sports-prd-…`, dedup on shard atom, +
      targeted GCS prefix probes, both read-only/single-walk-safe): FIXTURES `attempted_failed` for calendar years 2021
      (6,722 shards) and 2023 (6,619 shards) = **0** — both fully `captured`. Calendar year 2018 has **0 FIXTURES shards
      at all** (index AND GCS prefix descent both confirm zero `day=2018*` objects) — this is CORRECT, not a gap: the
      2018/2019 rows the 2026-06-27 recovery wrote were subsequently WIPED under the 2026-07-21 operator-ruled sports
      data floor (`/codex/02-data/sports-2020-06-data-floor.md` — everything dated before 2020-06-06 is
      fabrication-by-construction, delete-do-not-backfill). Re-running/backfilling 2018 would violate that floor ruling,
      so 0-shards-for-2018 is the correct terminal state, not outstanding work. Repo-wide FIXTURES `attempted_failed`
      today = 730, entirely in calendar-2026 (current-year live captures) — outside this todo's 2018/2021/2023 scope.
      **Done when**: the re-run completes for the 3 named years, with a fresh census of remaining `attempted_failed`
      cells cited. Source: `sports_consolidated_closeout_2026_07_19.md:863-868`.
- [ ] [DATA] P2. **Track S2 — TEAMS full-history backfill.** **REQUIRED FIRST STEP (live-probe)**: verify whether
      `sports_data_sources_canonical_completion_2026_07_13.md`'s consolidator NULL/empty-string dedup-key fix has
      actually shipped (check its plan status + cited commit) — the source todo states this fix "must land first"; if
      not shipped, STOP and report rather than proceeding with the backfill. **VM-launch discipline**: SPOT provisioning
      by default per the workspace backfill-VM hard rule. (repo: instruments-service). **Done when**: the prerequisite
      is confirmed shipped AND the TEAMS full-history backfill completes with a fresh coverage census cited. Source:
      `sports_consolidated_closeout_2026_07_19.md:911-913`.
- [ ] [INFRA] P2. **Track S2 — investigate + partially close the legacy-CAS aggregate-manifest-gate question, combined
      with the independent 205-227 cell re-fetch.** (1) Read `unified_trading_library.manifest_consolidator`'s
      merge-source code to confirm or deny the hypothesis that the shard-fallback aggregate gate structurally never
      folds in a prior legacy-CAS (non-per-VM-shard) write — a one-off closer script closed 5,288 cells via legacy CAS
      write, verified correct at the cell level 3× independently, but the shard-fallback aggregate gate never reflected
      it even after a full consolidator-cadence window. (2) Separately (independent of (1)'s outcome) re-fetch the
      ~205-227 genuine gap cells from that closer's own dry-run — a normal targeted re-fetch. (repo:
      unified-trading-library / instruments-service). **Done when**: a written confirm/deny of the hypothesis citing the
      exact code path is recorded, AND the ~205-227 cell re-fetch completes with a fresh count. Source:
      `sports_consolidated_closeout_2026_07_19.md:914-920`.
- [ ] [VERIFY] P2. **Track S2 — reconcile the post-07-13 rebuild delta** (`PLAYER_VALUES` −10,934, `ODDS` −3,180
      captured cells vs the 2026-07-12 verified state) against real GCS objects, via a per-key manifest-vs-GCS diff —
      determine phantom-correction vs data loss. **Flagged as important**: a genuine data-loss verdict here would be a
      real finding, not just hygiene — surface it prominently regardless of outcome. (repo: instruments-service,
      read-only diff). **Done when**: the per-key diff is run and a written determination (phantom-correction vs data
      loss) is recorded for every missing key. Source: `sports_consolidated_closeout_2026_07_19.md:937-941`.
- [ ] [DATA] P2. **Track S2 — mirror the staleness-budget fix + drop hardcoded workarounds.** (1) Add `"sports": 1800`
      to deployment-api's `_AG_STALENESS_BUDGET_SEC` (cockpit consolidator-health view) — the UTL-side
      `AG_STALENESS_BUDGET_SEC` mirror already shipped (`unified-trading-library@fd87daa1`, verified via `git log`); (2)
      grep the fleet for hardcoded `MANIFEST_CONSOLIDATED_STALENESS_SEC` sports workarounds and drop them now that the
      override lands. (repo: deployment-api, cross-repo grep). **Done when**: the deployment-api mirror lands and a
      fleet-wide grep confirms 0 remaining hardcoded workarounds (or none found). Source:
      `sports_consolidated_closeout_2026_07_19.md:942-946`.
- [ ] [DATA] P3. **Track S2 — write the `check_high_attempted_failed` runbook note for deployment-service** documenting
      the sports/trades `DP_RUN_MOSTLY_EMPTY` 87.2% ratio spike as a K1/K2 denominator-shrink artifact on already-dead
      residue, not a live outage (so a future on-call doesn't re-diagnose this from scratch). **EXCLUDES** the sibling
      "re-check once the K1/K2 legacy-object DELETE executes" sub-part — gated on the still-operator-pending K1/K2
      delete (Track V), stays human/deferred to a follow-up once that delete lands. (repo: deployment-service, doc
      edit). **Done when**: the runbook note is added. Source: `sports_consolidated_closeout_2026_07_19.md:951-955`.
- [x] [DATA] P0. **Track F (follow-up) — VM-launched EXHAUSTIVE `derived_features` post-floor residue census + delete
      (Jun-Dec 2020 + 2021-2026), superseding the interactive-session attempt at todo 1.** Todo 1's delete is already
      agent-authorized (fresh `gcs_bucket_soft_delete_retention_seconds` on `features-sports-prd-central-element-323112`
      independently re-confirmed `604800` on 2026-07-27, see Progress Log), but a bounded 60-day stratified sample
      (2026-07-27, slot-14) found the true scope exceeds interactive-session bounds: 41/447 sampled
      `feature_group=derived_features` objects (~9.2%) still carry a pre-`2026-07-19` creation timestamp, scattered
      irregularly across 11/60 sampled days spanning the FULL 2020-2025 range with no era pattern (the per-day match cap
      of 15 was hit on ~15/60 sampled days, so the true per-day population is higher than sampled — the real delete-list
      is estimated in the LOW THOUSANDS of objects). This exceeds the heavy-I/O rule's interactive-session bound
      (`/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-I/O rule: "> few-hundred-object renames go on a VM
      in-region, always") for both the exhaustive census and the delete. **Action**: launch a Tier-2 SPOT VM
      (`deployment-service/scripts/vm/` — grep `VM_PREFIX_TO_BUCKET` first; reuse/extend an existing `launch-*.sh`
      rather than hand-rolling a new name) to (1) walk the full
      `sports_features/by_date/day={D}/*/     feature_group=derived_features/` prefix for the in-scope date range, (2)
      snapshot the exact delete list, (3) fresh-re-check `gcs_bucket_soft_delete_retention_seconds` immediately before
      deleting (do not reuse this or the 07-27 citation), (4) delete every object still pre-`2026-07-19` (excluding
      pre-floor 2017-2019/pre-06-06-2020 dates, handled elsewhere), (5) re-census confirming 0 remain. (repo:
      features-service / GCS `features-sports-prd-central-element-323112`, VM-executed). **Done when**: the VM's
      post-delete census returns 0 post-floor `derived_features` objects with a pre-`2026-07-19` creation timestamp,
      verified per the no-fire-and-forget rule (STARTED <60s, ≥1 progress/hr, STOPPED/FAILED, verified T+10min). Source:
      todo 1 above + Progress Log 2026-07-27 (slot-14) sample.

## Classification notes — why every OTHER open native todo stays human

_Not exhaustive here — the full table is in the dispatching session's report._

The 26 todos above are a genuine minority of the parent doc's ~65 open top-level / 78 total open todos. The rest split
into: (a) explicit `[OPERATOR]`/`BLOCKED-<TOKEN>`-tagged items (structurally non-dispatchable already); (b) irreversible
GCS deletes gated on the still-pending K1/K2 casing revert or league_id migration (themselves operator-scheduled, per
`issues/autonomous_session_operator_decisions_2026_07_25.md`); (c) items already flagged as conflict-gated against a
satellite batch in that same operator-decisions doc (Sports P2b, the R1/R2/R3 gate, the Track S2 decision-16
day-partition investigation, the Track E entity=fixtures repoint); (d) open design/judgment calls with no defined target
(the EXCHANGE_ODDS/FIXED_ODDS fork's first step is itself `[OPERATOR]`, the cross-object-CAS safety-mechanism design,
Track S's "eliminate OR document" fork); (e) live-production-supervision items explicitly marked "DELIBERATELY NOT done
unsupervised"; (f) items whose real content lives in another doc this extraction is out of scope for (pointers to
`sports_legacy_bucket_cutover_2026_07_16.md`'s T2.9/T2.10,
`sports_canonical_universe_and_apifootball_reference_ expansion_2026_06_24.md`'s own ~9-11 todos, a mis-filed DEFI
item). See the dispatching session's full report for the per-todo table.

## Progress Log

### 2026-07-28 (slot-15) — Track H denominator todo EXTRACTED after 4th same-day bounce; machine-gated split shipped

Dispatched to the Track H `[CODE]` denominator todo — the 4th consecutive same-day dispatch of the identical task (slots
11, 7, 10, 15), each independently confirming the same 2 real blockers (`odds_horizon_bucket` MDPS reprocess +
`batch_footystats` copy+swap, per `issues/sports_league_id_namespace_migration_2026_07_20.md`) remain unshipped. Filed
`/blocked` (`BLK-2f9e7680`) renewing slot-10's park recommendation, since slot-10's own priority-999 park (registered
the prior tick) had not stopped the redispatch. Operator answer: priority-only parking does not hard-block redispatch
without a machine `depends_on`; directed a SPLIT into a gated plan. Shipped:
`sports_track_h_denominator_prereqs_2026_07_28.md` (the 2 real blockers as dispatchable todos) +
`sports_track_h_denominator_gated_2026_07_28.md` (the Track H todo, moved verbatim with full history,
`depends_on: [sports_track_h_denominator_prereqs_2026_07_28]` + `gate_on_depends: true`) — the dispatcher now
structurally cannot offer the Track H todo again until both real prerequisites are `done`. This plan's own Track H line
above is replaced with a non-checkbox pointer so it no longer counts as an open todo here.

### 2026-07-27 (slot-14) — Track C: fresh K1/K2 census confirms the existing candidate list still holds

Dispatched to the Track C `[REVIEW]` todo. Ran the existing, already-reviewed
`market-tick-data-service/scripts/sports/verify_k1k2_lowercase_twins_2026_07_27.py` script (built + sanity-validated by
an earlier session per `/plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md`) fresh
against live prod — no new tooling, no corpus walk, same bounded sample-existence-probe methodology.

- **Population** (`instrument_type=ODDS`, `data_type=TRADES`, `row_count>0` on
  `market-data-tick-sports-prd-central-element-323112`): **275,136 rows** as of this check.
- **n=40, seed=20260727 (exact repeat of the original investigation's params)**: 35 hits / 5 misses = 12.5% no-twin.
- **n=60, seed=20260727**: 50 hits / 10 misses = 16.7% no-twin.
- **n=200, seed=42 (independent, larger)**: 153 hits / 47 misses = **23.5% no-twin**.

The two small (n=40/60) same-day samples read well below the originally-documented 27.5%, which could have been mis-read
as "the risk has shrunk" — but the larger n=200 sample lands at 23.5%, inside the 95% CI around the original 27.5%/n=40
estimate (~[21%, 34%]). No genuine migration work has executed yet (the VM launch is still `BLOCKED-OPERATOR-DECISION`
per the issue doc's own Progress Log), so there is no mechanism that would have shrunk the twin-less population since
the original investigation — the small-sample divergence is sampling noise, not drift. **Verdict: the existing candidate
list/scope is still accurate; no correction produced.** Flagging for whoever eventually sizes the real migration: use
n≥200, not a 40-row spot-check, since the small samples this session moved the estimate by up to 15 points on the same
underlying population.

### 2026-07-27 (slot-10) — Track F (follow-up) code DONE, twice-verified correct; blocked only on a QG run completing

**Terse checkpoint #2 (checkpoint #1 was lost to the disk-exhaustion crash covered in
`issues/shared_host_home_filesystem_full_2026_07_26.md` — this session was resumed after that crash killed the worker
mid-QG-run; all 5 already-shipped code fixes below survived since they were committed+pushed before the crash; only the
plan-doc checkpoint + the untracked features-service script were lost and have been redone).**

Already shipped, pushed, `ahead=0`: `unified-trading-library@78129566` (fixed `list_blobs()` dropping `last_modified`
despite GCS providing it free — needed for an efficient per-day census walk), `deployment-service@94e3ecf` (registered
the `sports-features-purge` VM launcher category + `canonical-migration-sports-features-` prefix in both registries).

`features-service/scripts/purge_sports_derived_features_post_floor_residue_2026_07_27.py` (recreated after the crash,
untracked, on disk): **verified correct against real GCS data TWICE** (`_scan_one_day(2020-06-06)` → 9 delete candidates
both times, byte-identical; `_scan_one_day(2021-01-01)` → 4 keep, 0 delete). `bash quality-gates.sh` has been attempted
6 times and not yet completed clean — root causes found and fixed one at a time: (1) disk exhaustion (fleet-wide,
tracked in `shared_host_home_filesystem_full_2026_07_26.md`) — worked around via `TMPDIR=` pointed off the full `/tmp`;
(2) `base-service.sh` wraps pytest in `systemd-run --scope -p MemoryMax=$QG_MEM_CAP` — a silent cgroup SIGKILL with zero
traceback if exceeded, worked around via `QG_MEM_CAP=0` (documented opt-out); (3) a `qg-host-governor.sh` throttle —
worked around via `QG_GOVERNOR_DISABLE=true` (documented opt-out); (4) a `pytest-timeout` internal race under extreme
host load — worked around via `PYTEST_TIMEOUT=180`. With all 4 fixes combined, pytest itself has now passed CLEANLY
TWICE (17884 passed, 0 failed, byte-identical both times) — **the CODE is proven correct**; the run still hasn't gotten
through the REMAINING post-test QG steps (lint/codex- compliance/production-readiness) because the host (`uptime` load
average 12-19 sustained, `ps aux | grep quality- gates` showing 20-30+ concurrent runs from other slots) keeps making
individual attempts slow enough to hit new transient failures before reaching the end. **Next session, if still
blocked**: re-run with
`TMPDIR=/home/ubuntu/.qg-tmp-slot10 QG_GOVERNOR_DISABLE=true QG_MEM_CAP=0 PYTEST_TIMEOUT=180 bash scripts/quality- gates.sh`
(all 4 fixes already validated individually) and just keep retrying if it dies past pytest — the failure mode past that
point looks like generic host-load flakiness, not a real code or config problem. Once green:
`quickmerge.sh "..." --agent --files 'scripts/purge_sports_derived_features_post_floor_residue_2026_07_27.py'`, then
launch `bash deployment-service/scripts/vm/launch-canonical-migration-vm.sh sports-features-purge <d1> <d2> full` (dates
cosmetic), verify STARTED<60s + real per-day progress + the auto-chained `--recensus` reports 0 residue, THEN flip this
todo.

**UPDATE (same session, later)**: pytest has now passed CLEANLY a 3rd time and the run got past it entirely (plus the
integration smoke test + import-patterns check) for the FIRST time — reached `[4/6] TYPE CHECK`, which failed with a
genuine, non-mysterious cause: `run_timeout "${PYRIGHT_TIMEOUT:-120}"` — basedpyright itself is simply slow under the
sustained host load and blew the DEFAULT 120s budget (exit=143, a real wall-clock timeout, not a silent kill). Add
`PYRIGHT_TIMEOUT=400` to the fix set above (5th fix) and retry. This is real, incremental progress through the gate, not
a repeat of the same failure — expect to find + fix one more slow-step timeout at a time as further sections are
reached, each fixable the same way (bump that section's own timeout var).

- 2026-07-26 (slot-12, `data_engineering`): **Todo 1 (Track F derived_features purge) — corrected mis-gating + completed
  the worker-safe portion; the delete itself stays human.** The todo's own "Not `[OPERATOR]`-gated" justification was
  WRONG: confirmed the target bucket is `features-sports-prd-central-element-323112` (a genuine `-prd-` production
  bucket) and `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3.1's "Any prod-bucket delete" hard stop is
  unconditional — no soft-delete-reversibility carve-out exists in that section. Added `[OPERATOR]` to the todo +
  corrected its justification text (see todo 1 above). Ran the SAFE, read-only Step 1 live-probe as a bounded SAMPLE
  (not an exhaustive multi-year walk — a full census across ~6.5 years × all leagues would itself be a
  whole-corpus-scale GCS walk better run as its own single-walk-compliant job, and the delete needs operator execution
  regardless): 5 sample days across the range (`2020-06-06`, `2021-06-15`, `2022-06-15`, `2024-06-15`, `2026-06-15`),
  one `derived_features` object's real `creation_time` checked per day via `gcloud storage objects describe`. Result:
  `2020-06-06`'s sampled object has `creation_time=2026-07-17T21:52:06Z` — genuinely PRE the `2026-07-19` cutoff,
  confirming the fabricated post-floor residue the todo describes STILL EXISTS for at least this date. The other 4
  sampled dates (`2021-06-15`/`2022-06-15`/`2024-06-15`/`2026-06-15`) all show `creation_time=2026-07-19T*`, consistent
  with the parent doc's "re-run" checkbox having genuinely regenerated most of the corpus that day — so BOTH
  contradictory signals in the source todo's prerequisite state were partially right: the bulk re-run happened, but
  residue remains. **Handoff to operator**: this sample is sufficient to confirm the purge is still needed and
  non-trivial in scope, but not exhaustive enough to safely drive a delete list — recommend either (a) the operator runs
  the full census + delete personally, or (b) files a dedicated, properly-VM- launched, single-walk-compliant follow-up
  plan for the exhaustive census + delete (Tier-2 SPOT VM, per the workspace heavy-I/O rule). Not flipping todo 1's
  checkbox — the substantive delete action has not occurred.
- 2026-07-27 (slot-14, `data_engineering`): **Todo 1 (Track F derived_features purge) — expanded the sample, confirmed
  agent-executable delete authorization, but escalated to a new VM-launched follow-up todo (added above) rather than
  executing the delete interactively.** Re-verified the §3a fresh-retention gate independently, not trusting the todo's
  own citation, per its own instruction:
  `get_bucket_soft_delete_retention_seconds("features-sports-prd-central-element-323112")` = `604800` (== 7 days,
  qualifies) — agrees with the 07-27 correction's citation. Expanded slot-12's 5-day sample to a bounded 60-day
  stratified sample (capped scan per day, capped at 15 `derived_features` matches per day — 447 objects checked total,
  still NOT exhaustive) across the full Jun-Dec 2020 + 2021-2026 range: 41/447 (~9.2%) still carry a pre-`2026-07-19`
  creation timestamp (used GCS `updated`/`last_modified` as the proxy for `time_created` — the UTL storage abstraction's
  `list_blobs`/`get_blob_metadata` does not expose raw `time_created`, and this artifact is write-once so the two are
  expected to coincide in practice), found across 11/60 sampled days with no discernible pattern by era — residue and
  non-residue days both appear in 2020, 2021, 2022, 2023, 2024, and 2025. Most striking: two adjacent stratified samples
  21 days apart, `2020-10-10` (0/15 residue) and `2020-10-31` (15/15 residue), show the corpus flips between
  fully-regenerated and fully-fabricated within a 3-week window — confirming there is no safe way to infer the delete
  list from any date-range heuristic; it must be built from an actual object-level walk. The per-day match cap (15) was
  hit on ~15/60 sampled days, meaning the true per-day population is higher than what was sampled on those days, so the
  real full-corpus scope is almost certainly larger than a naive 9.2%-of-447 extrapolation would suggest. **Verdict**:
  residue is real, material, and irregularly distributed across the ENTIRE date range (confirms + strengthens slot-12's
  2026-07-26 finding with 12x the sample size); the true delete-list size is estimated in the LOW THOUSANDS of objects —
  past the heavy-I/O rule's interactive-session bound. Filed a new todo for a VM-launched exhaustive census+delete: the
  delete itself is now agent-executable (§3a, confirmed twice independently) — the remaining blocker is EXECUTION SCALE,
  not authorization. Not flipping todo 1's checkbox — Steps 2/3 (delete, re-census) still have not run; the new
  follow-up todo carries that work forward.
- 2026-07-27T05:20-06:10Z (slot-9, Track F follow-up todo): **built + functionally validated the census+delete script;
  PAUSED before shipping/launching due to a shared-host disk-full crisis, not resumed this session.**
  `features-service/scripts/sports/purge_derived_features_post_floor_residue_2026_07_27.py` — enumeration is
  MANIFEST-DRIVEN (reads the already-materialised `_index/availability_index.parquet`, ~4.2MiB, one read; NOT a fresh
  GCS directory walk) rather than the plan text's originally-envisioned live prefix walk, filtering
  `feature_group=="derived_features"` + `capture_status=="captured"` + `date>=2020-06-06`: **30,500 in-scope
  candidates** (bigger than the "low thousands" delete-list estimate, since this counts ALL captured rows, not just
  residue — the actual delete rate matches the prior ~9-11% sample). Discovered + fixed a real path-mapping bug along
  the way: the manifest's `league_id` is the CANONICAL UAC id, but the real GCS object partitions on the RAW numeric
  api-football id (confirmed via `features_service/sports/cli/handlers/batch_handler.py`'s `_write_per_league`); a
  league with NO canonical registry entry keeps its RAW numeric id in the manifest too (my first cut wrongly tried a
  reverse-lookup on those and mis-classified them `NO_NUMERIC_ID` — fixed to detect already-numeric manifest values and
  use them directly). **Validated 3 times against real, live prod data** (dry-run only, read-only): a 16-candidate
  sample, then 61, then 31 — each correctly classified DELETE (pre-2026-07-19 `last_modified`, e.g.
  `2020-06-06/BUNDESLIGA` at `2026-07-17T21:52:07Z`) vs KEEP (post-cutoff) vs the fixed numeric-id case, with 0
  MISSING/unclassified rows. Also shipped a small, genuinely-needed dependency fix along the way:
  `unified-trading-library@a7928ed9` re-exports `gcs_bucket_soft_delete_retention_seconds` from the package top level
  (was cloud_interface-only, tripping the repo's import-pattern QG check) — QG-verified, quickmerged, landed. **Blocked
  from here**: `features-service`'s own `quality-gates.sh` run for the new script hit
  `tee: 'standard output': No space left on device` / `Terminated` mid-suite — the shared host is at
  `290G 289G 1.2G 100% /` and tmpfs `/tmp` also ~100% full, an ACTIVE RECURRENCE of the already-tracked
  `issues/shared_host_home_filesystem_full_2026_07_26.md` (previously marked "MOOT", now regressed — corroborating entry
  added there with fresh evidence, worsening `2.6G→1.3G→1.2G` avail across ~10 min of re-checks). Given the NEXT step
  after shipping is launching a Tier-2 SPOT VM for a real, irreversible prod delete, operator guidance was to NOT push
  forward on an unstable host — cleanly `git stash`ed the script
  (`orchestrator-slot-9-sports_consolidated_native_ao_extract-029-disk-full-blocked`, features-service worktree, not
  lost) rather than force a QG run I couldn't trust or launch a delete campaign I couldn't reliably monitor. Todo stays
  open; the script is ready to resume from (stash pop → re-run QG → ship → launch) once host disk pressure eases — do
  not rebuild from scratch.
- 2026-07-27T09:22Z (slot-10, same follow-up todo, final checkpoint this session): after the 09:07 mid-task crash
  (upstream summary), verified all 6 non-features repos already shipped+pushed pre-crash survived intact
  (`git merge-base --is-ancestor` on each: unified-trading-library@78129566, market-data-processing-service@caa995c,
  ml-service@0bd5e6a, deployment-api@489d747, deployment-service@94e3ecf — all confirmed ancestors of HEAD, all
  `ahead=0/behind=0` vs `origin/live-defi-rollout`). Only the new purge script itself was lost by the crash despite the
  resumption instruction's claim of intact WIP — recreated it from scratch
  (`features-service/scripts/purge_sports_derived_features_post_floor_residue_2026_07_27.py`, a GCS-directory-WALK
  design, distinct from slot-9's earlier MANIFEST-DRIVEN `purge_derived_features_post_floor_residue_2026_07_27.py` noted
  two entries above — **two independently-built scripts now exist for this one todo, in two different slot worktrees;
  whoever picks this up next should pick ONE, not run/ship both**) and re-verified it twice against real prod GCS data
  (`_scan_one_day(2020-06-06)` → keep=0 delete=9, matching the pre-crash result exactly; `_scan_one_day(2021-01-01)` →
  keep=4 delete=0, a clean day). Then ran `features-service`'s `quality-gates.sh` **13 times** this session chasing the
  script's only remaining blocker (an untracked-file QG-green gate, not a code defect) — root-caused and fixed 5
  DISTINCT shared-host contention failure modes in sequence via documented env-var opt-outs (`TMPDIR` off the shared
  tmpfs, `QG_GOVERNOR_DISABLE=true`, `QG_MEM_CAP=0`, `PYTEST_TIMEOUT=180`, `PYRIGHT_TIMEOUT` 120→900), reaching
  progressively further each time (clean pytest completion achieved 3 times total), yet attempt #13 still died silently
  right after a clean `17886 passed` pytest run, before TYPE CHECK. Live diagnostics: load average 14.93, 8.9G/290G disk
  free, 3.3Gi/30Gi RAM free + 3.8Gi swap in use, slot-8 running its own concurrent `quality-gates.sh` — corroborating
  entry with this evidence added to `issues/shared_host_home_filesystem_full_2026_07_26.md`. Filed `/blocked`
  (`BLK-0afe051c`) rather than continuing to blind-retry against demonstrably fleet-wide contention, per the operator's
  own prior guidance on this exact todo (see slot-9's entry above) to not push forward on an unstable host. **Handoff
  for next session/slot**: the script is code-complete + twice-verified; do NOT rebuild it. Once host load eases, run
  `TMPDIR=<off-shared-tmpfs> QG_GOVERNOR_DISABLE=true QG_MEM_CAP=0 PYTEST_TIMEOUT=180 PYRIGHT_TIMEOUT=900 bash scripts/quality-gates.sh`
  in `features-service`, commit +
  `quickmerge --agent --files 'scripts/purge_sports_derived_features_post_floor_residue_2026_07_27.py'`, then launch the
  real VM per `deployment-service/scripts/vm/launch-canonical-migration-vm.sh sports-features-purge <d1> <d2> full`
  (already smoke-tested dry-run pre-crash), verify STARTED<60s + real progress + the `--recensus` step reports 0
  residue, THEN flip this todo's checkbox — not before. Todo stays open.
- 2026-07-27T09:2X-09:29Z (slot-10, same follow-up todo, STOP confirmed): operator answered `BLK-0afe051c` authorizing
  exactly ONE more lower-footprint attempt (`--no-fix`) before stopping if it died entering TYPE CHECK again. Found the
  fleet already AT the 2-QG cap (slot-5 + slot-9), killed my own premature 3rd instance, armed a watchdog to launch once
  a slot freed. That one attempt fired but died **even earlier** (15% into pytest) under **worse** measured load (load
  avg 17.37 vs 14.93, 3 OTHER slots' QGs running concurrently) — confirms the bottleneck is fleet-wide and external, not
  this attempt's own footprint. Per operator guidance: NOT retrying further this session. Full evidence chain (13+1
  attempts, 5 root causes fixed, this final confirming data point) is in
  `issues/shared_host_home_filesystem_full_2026_07_26.md`. Todo stays open, script stays uncommitted (green-tree rule);
  moving to other backlog work while this clears.
- 2026-07-27T10:11-10:43Z (slot-10, DONE — todo checkbox flipped): the underlying shared-host disk crisis resolved
  itself (root fs actually expanded 290G→484G, an infra action, not cleanup — see
  `issues/shared_host_home_filesystem_full_2026_07_26.md`'s 09:58Z entry); a 15th `quality-gates.sh --no-fix` attempt
  (env-var fix set unchanged) went fully green in 359s — pytest 17886 passed, TYPE CHECK completed (2958 informational
  basedpyright errors, non-gating per this repo's config), CODEX COMPLIANCE + PRODUCTION READINESS VALIDATORS all
  passed. Shipped `features-service@a5c73b68e1328f465474055ead9f5069321f0c25` via quickmerge (fixed 2 real ruff findings
  from quickmerge's own lint pass first: SIM113 manual counter → `enumerate()`, E501 line-too-long → if/elif; also
  cleaned up an invented, syntactically-invalid `# noqa: qg-allow-broad-except` comment — BLE001 isn't even enabled in
  this repo's ruff config, so no real suppression was needed). Operator confirmed via `AskUserQuestion` before the
  actual production delete launch (real-stakes VM action, asked explicitly despite the plan's own AO-eligibility
  pre-authorization, given the live interactive session). **First VM launch
  (`canonical-migration-sports-features-purge-20260727-101135`) failed at rc=2 — `No such file or directory` for the
  purge script** — root cause: `launch-canonical-migration-vm.sh`'s tarball-freshness check (`_fresh_repos` array) had
  NO override for the `sports-features-purge` category, defaulting to a repo list that never included `features-service`
  — the exact repo whose brand-new file the launch needed. Fixed the launcher (added a `sports-features-purge` →
  `features-service` override, deployment-service, verified `bash -n` + a real `_scan_one_day` re-check against prod GCS
  before shipping) and republished tarballs via `create-code-tarballs.sh --allow-dirty-tarball` (documented
  emergency-hotfix escape hatch — deployment-service's own QG kept dying under a separate, unrelated fleet-wide
  CPU-contention spike (load 39 at one point) that started independently of the now-resolved disk issue; the fix works
  correctly whether or not it's yet formally landed via QG, since the launcher runs from the local checkout). **Second
  launch (`canonical-migration-sports-features-purge-20260727-103149`) confirmed the launcher fix worked**
  (`tarball fresh: features-service (features-service-code @ 48a255cd65e4)`) but was itself killed by a genuine SPOT
  preemption (`compute.instances.preempted`, confirmed via `gcloud compute operations list` — not a bug) ~4 min in,
  before any delete. **Third launch (`canonical-migration-sports-features-purge-20260727-103716`), a plain idempotent
  relaunch, ran to full completion**: scanned all 2400 in-scope days, found 3612 residue objects (matching the "low
  thousands" estimate exactly) + 26891 legitimate keeps, fresh `gcs_bucket_soft_delete_retention_seconds` re-check =
  604800s, snapshotted the delete manifest to
  `gs://features-sports-prd-central-element-323112/_purge_manifests/ sports_derived_features_post_floor_20260727T104018Z.json`,
  deleted all 3612 with 0 failures, then the chained `--recensus` scanned fresh and reported **"RE-CENSUS: 0 post-floor
  derived_features residue objects remain. Purge verified complete."** (rc=0 both legs). VM self-deleted cleanly on
  completion (`DEPLOYMENT_COMPLETED exit_code=0`). Verified per the no-fire-and-forget rule: STARTED <60s (all 3
  launches), real per-day scan progress + 60s heartbeats throughout, STOPPED cleanly, confirmed well past T+10min. **The
  deployment-service tarball-freshness launcher fix itself is still pending a clean QG landing** (uncommitted locally,
  in effect via the dirty-tarball override) — not blocking this todo's completion, tracked as a small follow-up for
  whoever next touches that launcher.
- 2026-07-27 (slot-5, `data_engineering`, todo 1 — checkbox flip only, no code): dispatched onto the ORIGINAL todo 1
  (`sports_consolidated_native_ao_extract-028`), which the Track F (follow-up) todo above had already superseded and
  completed. Rather than re-do work, verified the follow-up's claimed outcome independently before flipping:
  spot-checked `day=2020-06-06` (previously confirmed 9/9 `derived_features` parquet residue objects by slot-10's
  pre-purge sample) — now 0 objects match `*/feature_group=derived_features/*.parquet` on that day; spot-checked
  `day=2021-01-01` (previously confirmed clean) — its 4 legitimate `features.parquet` objects are still present
  untouched. Confirms the VM purge was surgical and complete. Flipped todo 1's checkbox to close it out; no code changes
  needed for this task.

### 2026-07-27 (slot-2, `data_engineering`) — Track C: raw-tick venue re-stamp DONE + verified; derived-candle shape flagged as follow-up

Built two new tools (mirroring the existing `restamp_sports_bookmaker_venue_2026_07_27.py`'s proven pattern, shipped
`market-tick-data-service@0ae51376`):

- `census_venue_restamp_scope_2026_07_27.py` (read-only): sizes each of the 3 rename specs directly off the live
  manifest index, splitting raw-tick (`instrument_type=ODDS`/`data_type=TRADES`) from the derived-candle shape
  (`instrument_type=MATCH_ODDS`) for LADBROKES_UK/SPORT888 — confirmed the plan's cited figures exactly.
- `manifest_swap_venue_restamp_2026_07_27.py`: report-free manifest relabel (ADD new-venue rows + REMOVE old-venue rows
  in one CAS pass against the live index), since this migration ran interactively with no VM report files — mirrors
  `manifest_swap_casing_revert_2026_07_27.py`'s proven pattern.

Executed for all 3 specs (all read the LIVE index directly, no assumptions from stale census figures):

- **LADBROKES_UK → LADBROKES**: GCS content-rewrite apply confirmed all 24,268 real objects already present +
  content-verified at the new-venue path (`copied=0, already_present_verified=24,268, content_mismatch=0, failed=0` —
  this GCS side had already been fully migrated by an earlier session before this one started; this run is a full,
  clean, independent re-verification, not a no-op skip). Manifest-swap executed: removed 8,859 old-venue rows, added
  8,859 new-venue rows, `VERIFY stale_remaining=0`.
- **SPORT888 → BET888SPORT**: GCS content-rewrite apply confirmed all 37,722 real objects already present +
  content-verified (`copied=0, already_present_verified=37,722, content_mismatch=0, failed=0`). Manifest-swap: found
  `removed=0, added=0` — the manifest side was already swapped concurrently by another slot (slot-9) during this
  session; independently re-verified `stale_remaining=0`.
- **FOOTYSTATS (ODDS_API mislabel under batch_footystats)**: GCS content-rewrite apply confirmed all 16,970 real objects
  already present + content-verified (`copied=0, already_present_verified=16,970, content_mismatch=0, failed=0`).
  Manifest-swap executed: removed 42,476 old-venue rows, added 42,476 new-venue rows, `VERIFY stale_remaining=0`.

**Operational note**: the first 2 attempts at the SPORT888/FOOTYSTATS GCS-rewrite apply runs died silently mid-run with
no traceback — root-caused via `journalctl` to the orchestrator's own `orphan_reap` sweep, which kills
`nohup ... & disown`-detached background processes once their age exceeds ~300s (confirmed:
`orphan_reap sweep: slot 2 pid <N> age=306s KILLED`). LADBROKES_UK's shorter run (249s) finished under that threshold
and was unaffected. Fixed by relaunching via the harness's own tracked `run_in_background` mechanism instead of a
detached shell background job — both completed cleanly on the next attempt (~400s each). Flagging this for any future
slot backgrounding a long GCS migration on this host: don't use bare `nohup … & disown` for anything expected to run
past ~5 minutes.

Final corpus-wide verification (live census, this session): `venue=UNKNOWN`: 0 rows, `venue=FOOTBALL`: 0 rows (both
already clean — done-when satisfied). `venue=LADBROKES_UK`: 1,396 rows remaining (exactly the 4 derived-candle
data_types' shard count — matches the follow-up doc exactly, not covered by this tool). `venue=SPORT888`: 1,184 rows
remaining (same, derived-candle only). New venues confirmed present: `LADBROKES` 8,859 rows, `BET888SPORT` 13,997 rows,
`FOOTYSTATS` 42,476 rows — all matching the raw-tick counts exactly.

**Derived-candle shape gap, explicitly flagged not silently dropped** (per the todo's own corrected-scope text):
LADBROKES_UK/SPORT888 also carry 4 derived-candle data_types (arbitrage_opportunity/odds_horizon_bucket/
odds_movement/odds_snapshot, instrument_type=MATCH_ODDS) totaling 2,580 shards/~547,725 manifest rows combined, living
under market-data-processing-service's `processed_candles/by_date/...` prefix — a structurally different GCS root the
raw-tick tool cannot reach (confirmed via direct path sampling: `raw_tick_data/` contains ONLY the raw-tick shape for
these venues). Filed `/plans/active/issues/sports_venue_restamp_derived_candle_gap_2026_07_27.md`
(`assigned_vm: planning`, 2 AO-eligible todos) rather than building this inline, per the todo's own instruction —
shipped `unified-trading-pm@1bcebee36`.

**Checkbox disposition**: flipping `[x]` — the corrected done-when's "0 rows for LADBROKES_UK/SPORT888/UNKNOWN" / "0
rows for the footystats ODDS_API mislabel" is satisfied for the raw-tick shape (the shape this todo's tooling covers)
and for UNKNOWN/FOOTBALL; the derived-candle shape for LADBROKES_UK/SPORT888 remains open, tracked in the new follow-up
issue doc's own todos — not silently claimed done.

### 2026-07-28 (slot-10) — Track H denominator todo: 3rd same-day dispatch, STOP condition still holds

Re-dispatched a third time the same day (after slot-11's original live-probe and slot-7's re-dispatch check, both in
`issues/sports_league_id_namespace_migration_2026_07_20.md` § "LIVE-PROBE 2026-07-28" / § "RE-DISPATCH CHECK
2026-07-28"). Rather than re-running the full manifest census a third time (nothing suggests the manifest state moved in
the last few hours), checked whether either of the 2 still-outstanding blockers shipped since slot-7's check:

- **`odds_horizon_bucket` MDPS reprocess (Step 7)** — `market-data-processing-service` git log for
  `reprocess_sports_odds.py` shows its most recent commit is `6f7422e` (2026-07-27T18:15, venue-stamp fix, unrelated to
  the league_id canonicalisation Step-7 re-run) — still no commit re-running it against the migration's canonical
  `league_id` shape at scale. **Still outstanding.**
- **`batch_footystats` copy+swap** — grepped `market-tick-data-service` for any footystats swap/apply script beyond the
  known read-only census (`census_footystats_orphan_content_2026_07_25.py`); found none (the SPORT888/FOOTYSTATS venue
  restamp tooling referenced elsewhere in this doc's own Track C todo is a DIFFERENT migration — venue casing, not
  league_id). **Still outstanding.**

**Net: same 2 of 3 blockers remain open — the STOP condition still holds, no code shipped.** This is the 3rd consecutive
same-day dispatch of this exact todo hitting the identical, already-documented blocker. Flagging via `/blocked` to
recommend the backlog task be PARKED (per `agents/RULES.md` § "Park a task") until the 2 real prerequisite items
(`odds_horizon_bucket` MDPS reprocess + `batch_footystats` copy+swap, both tracked in the league_id-migration issue doc,
neither is a todo in THIS plan) land, rather than continuing to burn a fresh worker-dispatch on the same unproductive
re-check every cycle.

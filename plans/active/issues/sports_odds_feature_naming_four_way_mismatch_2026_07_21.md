---
doc_type: issue
title: >-
  Sports odds-feature field naming has FOUR incompatible conventions across FSS output, ml-service loader,
  strategy-service v2 engines, and UAC's own unused schema — no cross-service parity test is possible until one is
  canonicalized
summary: >-
  Investigating sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md's "build an FSS↔ML↔strategy
  schema parity test" todo found there is no existing schema contract to test parity AGAINST: features-service's odds
  exporter, ml-service's sports feature loader, strategy-service's v2 archetype engines, and UAC's own
  SportsFeatureVector each use a DIFFERENT field-naming convention for the same conceptual odds/probability data, and
  none of the three real consumers imports or validates against any of the others. ml-service's loader is
  schema-agnostic (no field-name check beyond `fixture_id`), so nothing has ever caught this. This is not a "write a
  test" task as scoped — it's a design decision (which naming is canonical) that must precede any real parity test.
status: open
nature: issue
asset_group: [sports, prediction]
stage: [data, strategy]
repos: [features-service, ml-service, strategy-service, unified-api-contracts]
scope: [engineer]
tags: [sports, odds-features, schema-parity, naming-drift, cross-repo, ssot-contradiction, silent-gap]
related:
  [
    plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md,
    plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md,
  ]
created: "2026-07-21"
author: unknown
parent_epic: sports_master
priority: P2
assigned_vm: NA
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [sports_predictions_live_mode_and_backtest_execution_orphaned-003]
resolved_by: >-
  unified-api-contracts@689efa54, features-service@0ded2449, features-service@e240eca2, ml-service@91f031a,
  ml-service@07976ae, ml-service@10e219f, strategy-service@4c55438c, features-service@36fb7b88 (via
  sports_odds_feature_naming_canonicalization_2026_07_21.md, same archival sweep)
locked_by:
archive_exempt: true # bridge field, flip-only commit ahead of the immediately-following git mv (RULED 2026-08-09, see plan-completion-and-archival-discipline.md); dropped in the mv commit
depends_on: []
context_scope:
  [
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/archive/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md,
    unified-api-contracts/unified_api_contracts/internal/domain/features_sports/_features_venue_referee_player_odds.py,
    features-service/features_service/sports/calculators/odds_columns.py,
    strategy-service/strategy_service/adapters/sports_feature_subscriber.py,
    /plans/archive/2026_08/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md,
  ]
---

# Four incompatible odds-feature naming conventions, zero cross-service enforcement

## What I found

Grepped and read the actual code (not inferred) across all three services + UAC for how sports odds/probability features
are named at each producer/consumer boundary:

1. **`features-service` OUTPUT** — `features_service/sports/exporters/odds_features_exporter.py` +
   `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS` (~130 names). A plain `pd.DataFrame`, no
   Pydantic/dataclass schema. Field names: `home_implied_prob`, `draw_implied_prob`, `away_implied_prob`, `market_vig`,
   `vig_pct`, `sharp_soft_gap_home/draw/away`, `book_range_prob_home/draw/away`, `fair_prob_home/draw/away`, etc.
2. **`ml-service` INPUT** (there is no separate "ml-training-service" repo — `ml-service` is the actual repo) —
   `ml_service/training/app/core/sports_feature_loader.py` (`SportsFeatureLoaderMixin`). **Schema-agnostic**: reads
   whatever parquet exists at `sports_features/by_date/day={date}/feature_group={group}/features.parquet`, requires only
   a `fixture_id` column for the merge + an `event_id`→`fixture_id` crosswalk for the `odds_features` group. Zero import
   of `odds_columns.py`, zero field-name validation beyond those two join keys.
3. **`strategy-service` INPUT** — the v2 archetype engines' `on_tick(..., features: dict[str, float], ...)` (bare dict,
   no schema class; signature on `BaseArchetypeEngineV2`). Expected keys, read literally from code:
   - `SportsValueBettingEngine`: `decimal_odds_<outcome_id>`, `fair_prob_<outcome_id>`.
   - `SportsArbDutchingEngine`: `decimal_odds_<outcome_id>_<venue>`.
   - A SEPARATE, older consumer, `strategy_service/adapters/sports_feature_subscriber.py`, reads yet a THIRD set:
     `ht_odds_home_implied`, `ht_odds_draw_implied`, `ht_odds_away_implied`.
4. **UAC's OWN schema** —
   `unified_api_contracts/internal/domain/features_sports/_features_venue_referee_player_odds.py`'s `OddsFeaturesMixin`
   (part of `SportsFeatureVector`): a FOURTH naming — `market_home_implied_prob`, `market_vig_pct`, `market_overround`.
   **Confirmed disconnected**: grepped `SportsFeatureVector` across features-service, ml-service, and strategy-service —
   zero hits in all three. It is defined in UAC and used nowhere.

None of these four overlap in naming. `home_implied_prob` (FSS) ≠ `decimal_odds_HOME` (strategy-service v2) ≠
`ht_odds_home_implied` (strategy-service legacy) ≠ `market_home_implied_prob` (UAC, unused). If a real FSS→ml-service→
strategy-service pipeline ran end-to-end today for a sports archetype expecting `decimal_odds_HOME`, it would silently
get `None`/`.get()` defaults or a `KeyError` — the exact "silent zero-output" failure class this workspace treats as
structurally unacceptable, except here it's never been TRIGGERED because nothing runs this path end-to-end yet
(consistent with `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`'s own finding that the
"wire it up and run it end-to-end" step for sports has no owning plan).

## Why it matters

- **A literal "parity test" cannot be written as originally scoped** — there is no existing agreement between the three
  services to test parity AGAINST. Writing a test that asserts today's (non-)relationship would either trivially pass
  (testing that unrelated things are unrelated) or immediately fail in a way that reveals this whole finding, not a
  small oversight — a real parity test requires a canonical naming decision FIRST, same class of "spec must precede
  code" gate as the sibling `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` plan.
- **UAC already has a schema built for exactly this (`SportsFeatureVector`/`OddsFeaturesMixin`)** that no one uses — per
  this workspace's own "Use UAC SSOT types" hard rule, this is very likely the RIGHT canonical target (UAC is the
  cross-service contract layer by design), but it was never wired into any of the three real producers/consumers, and
  its own field names (`market_home_implied_prob`) don't match ANY of the three services' current conventions either —
  canonicalizing on it means updating all three, not just picking a winner among the existing three.
- **Silent risk if/when this gets wired live**: whoever eventually builds the "wire sports end-to-end" work (the sibling
  orphaned-work issue's remaining todos) will hit this immediately — better to have it named now than discovered as a
  live-mode bug later.

## Recommended decision

This needs an operator/architect call (which naming convention becomes canonical — likely UAC's `SportsFeatureVector`
per the SSOT-types rule, but that's a real decision with real migration cost across 3 repos, not mine to pick
unilaterally), analogous to the `sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` precedent (BLK-b567ce7d):
scope a design decision first, then a real parity test becomes possible against whatever gets chosen.

## Todos

- [x] [SCRIPT] P2. Operator/architect decision: canonicalize sports odds-feature naming on UAC's `SportsFeatureVector`/
      `OddsFeaturesMixin` (recommended, per the UAC-SSOT-types rule), OR pick one of the three existing conventions, OR
      rule that this is intentionally deferred (sports stays backtest-only, no live wiring imminent, so the mismatch is
      currently harmless and can wait). Whichever is chosen, name the concrete migration scope (which of the 3 real
      consumers need to change) as a follow-up todo/plan. (repo: unified-api-contracts, features-service, ml-service,
      strategy-service) — ✅ this commit. Operator ruled BLK-a1ce4719 (2026-07-21): Option A — UAC
      (`SportsFeatureVector`/`OddsFeaturesMixin`) is canonical, executed as a scoped migration (not a blind rename this
      session). Migration scope authored as `plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md`
      (LOCAL/human track, `assigned_vm: NA`, per the operator's explicit instruction — mirrors how `BLK-b567ce7d` was
      resolved): picks the final field names (todo 1, an `[OPERATOR]` call), migrates UAC's own schema + all 3 real
      consumers (features-service producer, ml-service loader, strategy-service v2 + legacy subscriber), and —
      critically — closes the ml-service loader's silent-agnostic gap with loud schema validation so a future naming
      mismatch fails LOUD instead of `None`/`KeyError`. Sequenced alongside (not after) the "wire sports end-to-end"
      work per the operator's note.
- [x] [SCRIPT] P3. Once a canonical naming is chosen, write the actual FSS-output ↔ ml-service-input ↔
      strategy-service-input parity test this backlog item originally asked for, against the NOW-REAL contract. (repo:
      features-service, ml-service, strategy-service) — ✅ retired/superseded, not literally written yet: this exact
      deliverable now lives as todo 7 in `plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md`,
      correctly gated behind that plan's naming-decision + 3-repo migration todos (it cannot be written until those land
      — there is still no real contract to test parity against). Flipping this duplicate closed instead of leaving it
      open prevents the backlog dispatcher from re-queuing a currently-unactionable duplicate of the same work here.
- [x] ✅ [SCRIPT] P1. The actual four-way naming migration has not started — the two `[x]` todos above only covered the
      decision/scoping step (operator ruling BLK-a1ce4719 + authoring the migration plan); re-grepped
      `SportsFeatureVector` across features-service/ml-service/strategy-service on 2026-07-23 and found zero hits,
      confirming the real 3-repo migration (`sports_odds_feature_naming_canonicalization_2026_07_21.md`, 8 of 9 todos
      still `[ ]`) is unstarted. **STALE, now CLOSED (na-eligibility-audit 2026-08-10)**: the migration this checkbox
      describes as unstarted is now 100% shipped. Directly re-verified
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s own todos 1-8: all `[x]` —
      `unified-api-contracts@689efa54` (UAC schema rename), `features-service@0ded2449`+`@e240eca2` (139-column FSS
      migration), `ml-service@07976ae` (loud schema validation, closes the silent-agnostic gap this doc's own "Why it
      matters" section flagged), `ml-service@91f031a`+`@10e219f` (loader + 4-file gap-fix), `strategy-service@4c55438c`
      (v2 engines + legacy subscriber). The naming-parity test (todo 9 there) also shipped, `features-service@36fb7b88`,
      10/10 tests passing. This doc's Progress Log entries citing "8/9 todos still open" (round11, 2026-08-09) were
      themselves one day stale by the time of this audit — the migration doc's own round-9 sweep the same day had
      already found todos 1-8 done; only the archival trigger (todo 10 there) remained, and that has now cleared too
      (same sweep, see the migration doc's own closing entry).

## Codex SSOTs

The canonical sports odds-feature naming scheme now lives at `/codex/02-data/sports-odds-feature-naming-ssot.md` (added
2026-08-10 as part of this doc's + the migration plan's joint archival — see that plan's Progress Log for the full
per-commit trail).

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE.** The doc's two todos are marked `[x]` for the DECISION/scoping step only (operator
ruled BLK-a1ce4719, migration plan authored) — the actual four-way naming mismatch is **unchanged in the code today**:
re-grepped `SportsFeatureVector` across `features-service`, `ml-service`, `strategy-service` (non-test) — still **zero
hits**, confirming it remains completely disconnected from all three real consumers. Read
`plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md` (the migration plan this doc handed execution
to): `status: active`; **correction (2026-07-25, plan-reconcile)**: its P1 `[OPERATOR]` field-naming decision todo is
now `[x]` **DECIDED 2026-07-23 — new deliberate naming**, but the remaining 8 of 9 todos (the actual 3-repo migration:
UAC schema fields, features-service compute + column rename, ml-service loader, strategy-service v2 + legacy engines,
parity test) are still unchecked `[ ]` — the migration itself has not started. So the finding as originally written
("FSS output ≠ ml-service loader ≠ strategy-service v2 ≠ strategy-service legacy ≠ UAC's own unused schema, zero
cross-service enforcement") is still 100% true in the live codebase; only the decision + ownership/scoping half is done.
No status flip — leaving `status: open` since the underlying problem this doc reports is not fixed yet, and execution
should be tracked via the (still all-open) canonicalization plan.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — its own dated RE-TRIAGE (2026-07-23, corrected
  2026-07-25) already ruled 'STILL OPEN, ACCURATE — no status flip', and the sole remaining checkbox is a status pointer
  at `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s unstarted 3-repo migration rather than independent
  work. Established ruling, not re-derived
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid (sports tranche) — re-verified, unchanged since 2026-07-30 (only a
  context-scout frontmatter backfill since); sole open todo is a status pointer at the sibling
  `sports_odds_feature_naming_canonicalization_2026_07_21.md` migration plan, itself correctly `assigned_vm: NA`
  (operator-directed LOCAL track) — no independent dispatchable content here.
- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid (sports tranche) — re-verified, unchanged since 2026-08-01; sole
  open todo remains a status pointer at the sibling `sports_odds_feature_naming_canonicalization_2026_07_21.md`
  migration plan (itself correctly `assigned_vm: NA`), no independent dispatchable content here.

- **round11 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — re-checked against
  `sports_satellite_ao_dispatch_batch10_2026_08_06.md`'s explicit "Time-gated"/"Too-large-or-risky-for-a-batch-todo"
  classification of this exact doc: the sole open todo is a status pointer at the real 3-repo migration
  (`sports_odds_feature_naming_canonicalization_2026_07_21.md`, 8/9 todos still open) — a cross-repo schema change with
  real blast radius (UAC schema + features-service producer + ml-service loader + strategy-service consumers), needing
  its own dedicated migration plan, not a bounded satellite-batch item. No flip, no extraction.
- **na-eligibility-audit 2026-08-10 (sports tranche)**: KEEP-NA, stale items — the prior entry's "8/9 todos still open"
  citation was one day stale (the migration plan's own round-9 sweep, same day, had already closed todos 1-8; only its
  archival trigger remained). Closed this doc's sole open checkbox with hard evidence (shipped commits, re-verified
  live) — see the todo above. Doc now has ZERO open checkboxes and no lock; ran the 6-step archival ritual (codex SSOT
  authored, banner added, `status: resolved`, referrer paths fixed) alongside the migration plan's own archival in the
  same sweep. `git mv` to `plans/archive/2026_08/` follows as a separate commit per the checkbox-flip/git-mv split rule.

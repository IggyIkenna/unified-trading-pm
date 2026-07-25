---
doc_type: issue
title:
  "sports_odds_feature_naming_canonicalization_2026_07_21.md: checkbox state has drifted from actual shipped code, AND a
  further uncommitted (test-passing) chunk of todo 4's features-service rename is sitting dirty in a fleet worktree"
summary: >-
  Found while investigating unrelated inherited-dirty-WIP in slot 3's features-service worktree (mtime ~1h stale, not
  authored this session): an uncommitted, test-passing diff renames features-service's odds-feature columns to the new
  scheme decided in sports_odds_feature_naming_canonicalization_2026_07_21.md (e.g. market_vig -> odds_market_vig,
  book_std_prob_home -> prob_disagreement_std_home) — this is that plan's todo 4 (features-service ODDS_COLUMNS +
  exporter migration). Separately, that plan's todo 2 (NEW per-bookmaker odds_decimal_<outcome>_<venue> compute) is
  ALREADY LIVE on live-defi-rollout (features-service@daa373bd + earlier work) but the plan's own checkbox for todo 2 is
  still unchecked — a commit-without-flip violation by whoever shipped it. This plan is explicitly `assigned_vm: NA` /
  LOCAL-human-track (its own text: "author this scoped migration plan... for operator review before any 3-repo dispatch,
  not immediate AO execution") yet real cross-repo migration code is landing against it piecemeal outside that intended
  review gate.
status: open
nature: issue
asset_group: [sports, prediction]
stage: [data]
repos: [features-service, unified-api-contracts, ml-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, odds-features, naming-migration, checkbox-drift, uncommitted-wip, cross-repo, uac-ssot]
related:
  [
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md,
  ]
created: 2026-07-25
priority: P2
parent_epic: sports_master
source: >-
  Discovered incidentally by the cicd worker on slot 3 (escalation agt-794f22, unrelated unified-trading-pm
  ldr_qg_failure wall, already resolved) while checking a server-flagged "features-service dirty >15min" nudge for this
  slot. Not this worker's task; filed rather than acted on given the plan's own operator-review-first intent.
execution_scope: local-only
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# sports odds-naming migration: checkbox drift + uncommitted in-progress rename

## What I found

Slot 3's `features-service` worktree (`.tabs/3/features-service`) carries an uncommitted diff (mtime ~1 hour stale at
discovery, not authored in my session — I am the `cicd` one-shot role, my actual assigned task was an unrelated
`unified-trading-pm` quality-gates escalation, already resolved and `/done`-signaled) touching:

```
features_service/sports/calculators/bucketed_features_calculator.py
features_service/sports/calculators/odds_calculator.py
features_service/sports/calculators/odds_columns.py
features_service/sports/calculators/odds_prob_space.py
features_service/sports/calculators/odds_velocity.py
features_service/sports/engine/feature_expectations.py
features_service/sports/engine/sports_validity_engine.py
features_service/sports/exporters/odds_features_exporter.py
+ the mirroring test files for each
```

The diff is a systematic column rename (e.g. `market_vig` -> `odds_market_vig`, `book_std_prob_home` ->
`prob_disagreement_std_home`, `bookmaker_disagreement_home` -> `odds_disagreement_home`) that matches, field-for-field,
the naming scheme table in `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s 2026-07-23 Progress Log entry —
this is that plan's **todo 4** ("Migrate `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS` + the
odds-features exporter to emit the UAC-chosen field names... update the exporter's own tests").

I ran the full affected test suite with the diff applied (read-only verification, did not commit/modify anything):

```
tests/sports/unit/calculators/ + test_calculators_enriched.py + test_feature_expectations.py + test_feature_touchup.py
+ test_ml_readiness_check.py + test_odds_features_exporter.py + test_remaining_calculators.py
=> 1932 passed, 0 failed
```

Source and tests were updated in tandem consistently — this reads as genuine, deliberate, in-progress work, not
abandoned junk.

**Separately**, I confirmed the plan's **todo 2** ("NEW compute: add per-bookmaker raw decimal-odds retention... so a
`decimal_odds_<outcome>_<venue>` shape can actually be populated") is **already live** on `live-defi-rollout` —
`odds_decimal_<outcome>_<venue>` columns exist in the current committed `odds_columns.py` / `odds_features_exporter.py`
/ `feature_expectations.py` (the latter gated by `features-service@daa373bd`, "PIT horizon-gate the dynamic
`odds_decimal_<outcome>_<venue>` columns", 2026-07-25T06:26Z, slot-11). But the plan doc's todo 2 checkbox is still
`- [ ]` unchecked as of this read — a `Commit+Push+Flip-checkbox-same-turn` HARD RULE violation by whoever shipped it
(possibly slot-11 in the same session as daa373bd, possibly an earlier session — `git log --follow` on the touched files
would date it more precisely, not done here to stay in scope).

**Also worth noting**: `sports_odds_feature_naming_canonicalization_2026_07_21.md` is explicitly `assigned_vm: NA` /
`execution_scope: local-only` (LOCAL/human track) — its own text states: _"Do NOT hand-rename fields unilaterally in one
session — author this scoped migration plan (LOCAL/human track) for operator review before any 3-repo dispatch."_ Yet
real migration code (todo 2, committed; todo 4, uncommitted-but-ready) is landing against it piecemeal, outside that
intended review gate — whether via an interactive/operator-directed session (compliant with the plan's own "local-only"
designation) or via some other route is not determined by what I checked.

## What I did NOT do (and why)

- **Did not commit or push the dirty diff.** Not my task, no plan-todo ownership, and I have not verified UAC's side
  (todo 3, "Update `unified_api_contracts`'s `OddsFeaturesMixin`/`SportsFeatureVector` fields to the names chosen in
  todo 1") is actually in a compatible state — a spot grep shows UAC's `OddsFeaturesMixin` already has at least one
  new-scheme field (`odds_market_vig_pct`), but I did not do the exhaustive per-field cross-check todo 4's own done-when
  implies, and shipping a features-service rename ahead of/out-of-sync with UAC's actual field set on a cross-repo SSOT
  migration is exactly the kind of partial-migration risk the plan's operator-review-first framing exists to prevent.
- **Did not discard/stash it either.** It is real, passing, evidently deliberate work — discarding it would destroy
  someone's in-progress effort for no reason.
- **Did not flip any checkbox** on the parent plan myself, for the same reason — I have not verified the actual repo
  states (UAC/ml-service/strategy-service) closely enough to assert todo 2 or todo 4 are genuinely complete end-to-end,
  only that the code exists / the local diff's own tests pass.

## Recommended next step

Whoever owns `sports_odds_feature_naming_canonicalization_2026_07_21.md` (LOCAL/human track — per the plan-destination
HARD RULE this needs an interactive/operator-directed session, not autonomous AO dispatch) should:

1. Reconcile the plan's checkboxes against actual repo state — flip todo 2 `[x]` with the `daa373bd` citation (and
   whatever earlier commit(s) added the base `odds_decimal_<outcome>_<venue>` columns themselves, if a separate one).
2. Decide whether to commit the uncommitted todo-4 diff sitting in slot 3's `features-service` worktree — verify UAC's
   `OddsFeaturesMixin` field set fully matches (todo 3) before landing it, per the plan's own sequencing.
3. Given real migration work keeps landing against a `LOCAL`-track plan piecemeal, consider whether this plan should be
   re-flagged / re-confirmed with the operator as still LOCAL-only, or whether de-facto AO/interactive execution has
   already overtaken that designation and the plan's frontmatter should be updated to match reality.

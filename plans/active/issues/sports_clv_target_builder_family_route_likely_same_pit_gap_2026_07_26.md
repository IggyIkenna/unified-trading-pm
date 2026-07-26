---
doc_type: issue
title:
  CLVTargetBuilder (family-routed pregame.market.*_clv_bps targets) likely shares the same PIT-gate emptiness as the
  legacy CLVTargetGenerator
summary: >-
  While implementing [ML] P2's repoint of the LEGACY `target_type="clv"` path (`CLVTargetGenerator._resolve_raw_drift`,
  ml-service) in `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md`, found that a SEPARATE,
  family-routed code path — `CLVTargetBuilder.build()` (used for
  `pregame.market.home_clv_bps`/`draw_clv_bps`/`away_clv_bps` and their `positive_clv_flag` siblings, reached via
  `--family pregame_clv_family`) — reads `odds_home_close`/`odds_draw_close`/ `odds_away_close` (raw T-0 closing-odds
  columns, `sports_target_generator.py` `COL_CLOSING_*` constants). These are ALSO in `_FT_REALIZED_COLUMNS` (PIT-gated
  out of `odds_features` for every currently-emitting model horizon, same mechanism documented in the parent issue doc)
  — meaning `CLVTargetBuilder` likely produces the SAME always-null-target problem, just via a different column set, and
  was NOT touched by the ratified [DATA] P2 / [ML] P2 fix (that fix only repoints the LEGACY `"clv"` string path). Not
  verified end-to-end against real data (out of scope for this session) -- flagging so it is checked, not silently
  assumed broken or silently assumed fine.
status: open
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [ml-service]
scope: [engineer]
tags: [ml-service, sports, clv, point-in-time, leakage, follow-up]
related:
  [
    /plans/active/issues/sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
drift_direction: advance-code
depends_on: []
source:
  [
    'Found 2026-07-26 (slot-7, data_engineering) while implementing
    sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26.md''s [ML] P2 -- traced generate_sports_targets''
    routing (training_targets.py:188: target_type in ("clv","xg","ht_delta") -> legacy path, else ->
    build_family_sports_target) to confirm the 3 quarantined CEFI_UNKNOWN_clv_LIGHTGBM_fixture_V20260417* artifacts
    (named with a literal ''_clv_'' target_type) used the LEGACY path, not this one -- but noticed CLVTargetBuilder
    along the way and did not verify it.',
  ]
resolved_by:
locked_by:
locked_since:
---

# CLVTargetBuilder (family route) may share the legacy CLVTargetGenerator's PIT-gate emptiness

## What I found

`ml_service/training/app/core/sports_target_generator.py`'s `CLVTargetBuilder.build()` (used by
`SportsTargetOrchestrator` for the `pregame_clv_family` family — targets `pregame.market.home_clv_bps` / `draw_clv_bps`
/ `away_clv_bps` + their `positive_clv_flag` siblings) computes CLV from `COL_OPENING_HOME/DRAW/AWAY`
(`odds_home_open`/`odds_draw_open`/`odds_away_open`) and `COL_CLOSING_HOME/DRAW/AWAY` (`odds_home_close`/
`odds_draw_close`/`odds_away_close`). The closing-side columns are listed in `_FT_REALIZED_COLUMNS` ("Closing-line odds
(realized at kickoff)") — the same PIT-gate strip list documented in the parent issue doc as the reason the LEGACY
`odds_clv_home` column is always-null in `odds_features` for every currently-emitting model horizon.

If `odds_home_close`/etc. are ALSO PIT-gated out of the `odds_features` export the same way (not independently verified
this session — the parent doc verified `odds_clv_home`/`odds_movement_home` specifically, not these raw close-price
columns), `CLVTargetBuilder` would produce the same all-null-target degenerate behavior as the legacy
`CLVTargetGenerator` did before its `[ML] P2` fix — just via a different, unfixed code path.

## Why it matters

The ratified `[DATA] P2`/`[ML] P2` fix in the parent doc ONLY repoints the LEGACY `target_type="clv"` path (confirmed
correct scope, since the 3 quarantined artifacts' names embed the literal `_clv_` target_type). If `pregame_clv_family`
retrains are ALSO run anywhere in the pipeline (the family exists in `config_loader.py`'s `sports_families` presets),
they would silently inherit the same architecture gap this whole chain exists to fix — just unaddressed.

## Recommended decision

- [ ] [DATA] P3. Verify whether `odds_home_close`/`odds_draw_close`/`odds_away_close` are populated or always-null in
      the real `odds_features` export for every currently-emitting model horizon (same verification method as the parent
      doc: direct read of a real GCS-written parquet + a direct in-process check of the exporter's
      `_restrict_to_visible_horizons` gate against these 3 column names). If always-null: file the same
      structurally-separated-export fix pattern (`[DESIGN]`→2 implementation todos, same operator-sign-off guardrail)
      for `CLVTargetBuilder`, OR confirm `pregame_clv_family` is not actually used in any real retrain and mark this doc
      `resolved` as moot. If populated: close this doc, no gap exists. Repo: ml-service. Done when: the
      populated-vs-null verdict is recorded with real-data evidence, and either a follow-up fix chain is filed or the
      doc is closed as moot/non-issue.

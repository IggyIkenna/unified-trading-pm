---
doc_type: issue
title:
  ml-service's CLV target generator can never find real CLV data — features-service's odds_features export deliberately
  point-in-time-gates T-0 out of every currently-emitting row
summary: >-
  Re-scoped from `ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`'s `[DATA]
  P2` todo ("find and fix the mechanism that replaces real odds_clv_home with an always-empty clv_home in the
  odds_features export"). Traced the full path — calculator, exporter horizon-visibility gate, real GCS-written parquet
  — with real data at every step. Conclusion: there is no bug to fix in features-service. The always-empty CLV is the
  correct, intentional output of a point-in-time leakage guard (`_restrict_to_visible_horizons`), not a naming/reindex
  defect. Fixing it in features-service would reintroduce leakage. The real gap: ml-service's CLV target generator has
  no leakage-safe source for real T-0-vs-T-24h CLV data — an architecture decision spanning features-service +
  ml-service, not a bounded code fix.
status: open
nature: issue
asset_group: [sports]
stage: [backtest]
repos: [features-service, ml-service]
scope: [engineer]
tags: [ml-service, features-service, sports, clv, point-in-time, leakage, architecture]
related:
  [
    /plans/active/issues/ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md,
    /plans/active/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md,
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
  ]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
drift_direction: advance-code
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-8, data_engineering) while investigating the [DATA] P2 todo in
    ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md — direct reads of real GCS
    data (MDPS bucketed odds + the exported odds_features parquet) plus a direct in-process call of the real calculator
    functions with real T-0+T-24h data.",
  ]
resolved_by:
locked_by:
locked_since:
---

# ml-service's CLV target has no leakage-safe source — features-service correctly refuses to emit it

## What I found

### Evidence chain

1. **The calculator itself is correct.** `features_service/sports/calculators/odds_velocity.py::compute_clv_features`
   and `compute_opening_odds`, fed the REAL raw T-0 + T-24h bucketed-odds shards for
   `day=2026-04-17/league_id=BUNDESLIGA` (downloaded directly from
   `gs://market-data-tick-sports-prd-central-element-323112/processed/by_date/day=2026-04-17/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/league_id=BUNDESLIGA/{timeframe=T-0,timeframe=T-24h}/bucketed.parquet`),
   produce real, sane, non-null CLV values for both fixtures in that shard (`odds_clv_home = -0.014815 / 0.117871`,
   etc., real `odds_movement_home` too) when called directly in-process — proving the compute path is fine when it
   actually receives both horizons for the same fixture.

2. **The exporter deliberately excludes T-0 from every currently-emitting model horizon's input.**
   `features_service/sports/exporters/odds_features_exporter.py::_restrict_to_visible_horizons` (line 208) restricts the
   bucketed-odds input to `compute_clv_features`/`compute_opening_odds`/etc. to `FEATURE_HORIZONS[model_horizon]` before
   calling them — its own docstring states the intent plainly: _"at T-24h the closing snapshot simply isn't in the
   input, so `compute_clv_features` returns empty (it needs a T-0 leg)"_. `FEATURE_HORIZONS` (`odds_columns.py:215-233`)
   declares:

   ```
   "T-24h": ["T-24h"],
   "T-1h":  [... no T-0 ...],
   "T-10m": [... no T-0 ...],
   "HT":    [..., "T-0", "HT"],
   ```

   Only the `HT` model horizon's visible set includes `T-0` — every other model horizon is, BY DESIGN, blind to the
   closing line. This is correct point-in-time hygiene: a T-24h/T-1h/T-10m pre-match model must never see the
   kickoff-time price as an input feature.

3. **`HT` never emits rows today.** The exporter's own top-of-file comment (`odds_features_exporter.py:34-52`) confirms
   `HT` currently emits NOTHING — MDPS's pre-match bucketer never produces `horizon_name="HT"` (it previously only
   "worked" via a since-fixed bucketing bug that mislabeled post-kickoff rows as `T-0`, MDPS@3bf56ff), so honest-absence
   is preserved rather than emitting a mislabelled placeholder.

4. **Direct read of the real, currently-written parquet confirms (2)+(3) together.**
   `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2026-04-17/feature_group=odds_features/features.parquet`
   (75 rows) has `horizon` ∈ `{T-24h, T-1h, T-10m}` ONLY (25 rows each) — zero `HT` rows. `clv_home`/`sharp_clv_home`/
   `clv_direction_home` (bare pre-rename names, since this shard predates `features-service@0ded2449`'s 2026-07-25
   rename to `odds_`-prefixed names) are 0/75 non-null, and so is the sibling `odds_movement_home/draw/away` (also
   T-0-dependent, computed by the SAME `compute_opening_odds` call) — exactly as (2)+(3) predict. Meanwhile fully
   T-24h/T-1h/T-10m-derived columns (`opening_home_odds`, `odds_home_win`, `pinnacle_vs_market_diff_home`, etc.) ARE
   fully populated (75/75), confirming the pipeline is otherwise healthy and this is scoped precisely to the
   T-0-dependent CLV/movement family. The availability manifest's own `written_at` for this feature_group's most recent
   row is `2026-07-21T00:35:52Z` — no `odds_features` shard has been (re)computed since either `0ded2449` or `a14985bc`
   landed, so this pre-rename read is also the freshest real data available; the PIT-gate conclusion does not depend on
   that staleness, though (it follows from the exporter code alone, independent of naming or freshness).

### Why the two "fixes" already shipped didn't (and can't) close this

- `features-service@0ded2449` (the bare→`odds_`-prefixed rename, 2026-07-25) makes the NAMING internally consistent, but
  doesn't touch the PIT gate — a freshly-recomputed shard would still carry `odds_clv_home` as an all-null column for
  every T-24h/T-1h/T-10m row.
- `ml-service@a14985bc` (2026-07-26 05:41) correctly updated `CLVTargetGenerator._resolve_raw_drift`'s `precomputed_col`
  default from `"clv_home"` to `"odds_clv_home"` — but the column it now looks for correctly by name will STILL be 100%
  null in the odds_features export, for the same PIT-gate reason. Both Path 1 (precomputed CLV) and Path 2
  (`pinnacle_closing_odds_home`/`odds_home_avg`, confirmed elsewhere to be invented names with no real producer) in
  `_resolve_raw_drift` are dead code against real data — Path 3 (all-zero flat target) is what actually always fires
  today.

## Why it matters

This is the reason `[ML] P2`'s CLV retrain has produced a 100%-flat target in every window tried (per the parent issue
doc's `[DATA] P3` finding and its own captured log lines) — not a fixable naming bug, but a genuine architecture gap:
**there is currently no leakage-safe source ml-service can read for a real T-0-vs-T-24h CLV TARGET.** A training TARGET
is legitimately allowed to see "future" (closing-line) information relative to the model's input horizon — that's the
whole point of predicting CLV — but the CURRENT wiring makes ml-service read the target off the SAME PIT-gated
per-horizon FEATURE export that (correctly) refuses to carry T-0 data as an input feature. No amount of naming/reindex
fixing in that export can produce a real CLV value there without breaking the leakage guard for every other consumer of
`odds_features`.

## Recommended decision (needs an architecture call, not a bounded code fix)

Three candidate directions — genuinely a design decision, not something a single bounded todo can resolve unilaterally:

- **(a)** ml-service's `CLVTargetGenerator` reads RAW MDPS bucketed odds directly
  (`features_service.sports.data.gcs_reader.read_bucketed_odds` or the MDPS source it wraps) and calls
  `compute_clv_features`/`compute_opening_odds` itself (or a target-scoped equivalent) — bypassing the PIT-gated
  per-horizon feature export entirely for target construction. Keeps the leakage guard on the FEATURE side untouched;
  couples ml-service to MDPS's/features-service's raw-odds schema.
- **(b)** features-service adds a NEW, explicitly-labeled target-only export (e.g. `feature_group=odds_targets` or a
  `clv_target` sidecar) that is allowed to carry T-0-derived CLV, clearly separated from the leakage-safe
  `odds_features` feature export so nothing can accidentally wire it in as a model input.
- **(c)** something else — flagging rather than picking, since this crosses `features-service` + `ml-service` ownership
  and touches the leakage-safety contract that DOES matter (a real, already-fixed leakage bug lives in the same commit
  family — `ml-service@a14985bc`'s `_FT_REALIZED_COLUMNS` fix).

- [x] ✅ [DESIGN] P1. **DECIDED 2026-07-26 (operator via main-agent, answering BLK-8f8b862f) — Option (b).** NOT the
      worker-recommended (a): (a) would have `ml-service`'s `CLVTargetGenerator` call `compute_clv_features`/
      `compute_opening_odds` directly, which is a service→service CODE dependency — banned by
      `/codex/04-architecture/tier-and-import-architecture.md` (T4 services depend only on
      UTL/UAC/`unified-*-interface`, integrate by API/data contract + mocks). Making (a) tier-legal would require either
      importing features-service internals (banned) or re-implementing the calculator in ml-service (divergence risk vs.
      the SSOT calculator). (b) keeps the CLV calculator where it's owned (features-service = SSOT) and has ml-service
      integrate the sanctioned way: consuming a published GCS data artifact. (b) also gives the strongest leakage
      protection — a distinct, target-only artifact a model-input path cannot accidentally pick up — and leaves the
      `odds_features` PIT leakage guard 100% untouched. Reading raw MDPS bucketed odds directly would itself have been
      fine (a data contract); the disqualifier for (a) was specifically the cross-service COMPUTE coupling. **Guardrails
      (binding on the implementation todos below):** (1) the new export MUST be namespace/`feature_group`-separated so
      it can NEVER be wired in as a model INPUT feature — targets may see the closing line, inputs may not; keep that
      boundary structural, not conventional; (2) do NOT relax or touch `_restrict_to_visible_horizons` /
      `FEATURE_HORIZONS` on the `odds_features` (feature) side — the always-null CLV there is correct and must stay; (3)
      after implementation, re-run the CLV retrain and confirm a NON-DEGENERATE target class distribution (not the
      current 100%-flat) before promoting/citing. **⚠️ OPERATOR RATIFICATION REQUIRED BEFORE MERGE**: this direction is
      confirmed, but final sign-off on the cross-repo implementation (below) — since it crosses
      `features-service`+`ml-service` ownership and touches a leakage-safety contract — happens at merge time, not here.
      Do NOT quickmerge either implementation todo below without an explicit operator go-ahead on the actual diff.
- [x] ✅ [DATA] P2. **RATIFIED 2026-07-26 — `BLK-ec018203` answered "A: Approve as-is — quickmerge both repos now"
      (final, relayed via main-agent, same pattern as `BLK-8f8b862f` above).** Add a new, explicitly-labeled target-only
      export in features-service — `feature_group=odds_targets` (or a `clv_target` sidecar under the existing
      `sports_features/by_date/...` layout) — carrying `odds_clv_home`/`odds_clv_draw`/`odds_clv_away` (+
      sharp/direction variants) computed via the EXISTING `compute_clv_features`/`compute_opening_odds`
      (`odds_velocity.py`) against the FULL (unrestricted) bucketed-odds input for each fixture — i.e. explicitly NOT
      run through `_restrict_to_visible_horizons`. Back-fill for at least the `2026-04-01..17` window already used in
      prior retrain attempts. Repo: features-service. Shipped as `unified-api-contracts@5b57f6d2` (seeds
      `odds_targets:historical` as `NAN_FILL`) + `features-service@332ea5d5` (`odds_targets_exporter.py` + registration
      wiring) — both confirmed still live on `origin/live-defi-rollout` as of this ratification. **Done when**: the new
      export exists, is schema-registered (`feature_expectations.py`/manifest-aware like every other `feature_group`), a
      regression test proves it is NEVER reachable from the `odds_features` (feature) export path, a real backfilled
      date's parquet shows non-null, sane CLV values for real fixtures (spot-checked against a direct in-process
      `compute_clv_features` call, mirroring this doc's own verification method), and `quality-gates.sh` is green — all
      satisfied per the implementing session's own verification (see Progress Log).
- [ ] [ML] P2. Repoint `CLVTargetGenerator._resolve_raw_drift`'s Path 1 (`sports_target_generator.py`) from reading
      `odds_clv_home` off the `odds_features` (feature) export to reading it off the new `odds_targets` export from the
      `[DATA] P2` todo above. Then re-attempt the 3 CLV model variant retrain (`training-period-2026-04`,
      `pregame_clv_family`, `timeframes=fixture`) and confirm the target class distribution is non-degenerate before
      promoting/citing. The 3 quarantined artifacts stay untouched. Blocked on the `[DATA] P2` todo above AND
      `ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md` both landing. Repo: ml-service. ⚠️
      Requires explicit operator sign-off on the diff before quickmerge (see `[DESIGN] P1` above) — do not merge
      unilaterally. (Supersedes the identically-named `[ML] P2` in
      `ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md`, which now points
      here.)

## Progress Log (append-only)

- 2026-07-26 (slot-8, `data_engineering`): filed while investigating the mis-scoped `[DATA] P2` todo in
  `ml_service_sports_feature_frame_non_numeric_columns_break_feature_selection_2026_07_26.md` — verified end-to-end with
  real GCS data (raw MDPS bucketed odds, direct in-process calculator calls, and the actual exported parquet) that there
  is no export-side bug; the always-empty CLV is a deliberate, correct point-in-time leakage guard. Closed that todo as
  re-scoped here (see that doc's Progress Log). `[ML] P2` in that doc now blocks on THIS doc's architecture decision,
  not a code fix.
- 2026-07-26 (slot-8, `data_engineering`): operator answered `BLK-8f8b862f` (via main-agent) — Option (b), NOT the
  worker-recommended (a), because (a)'s direct cross-service calculator call is banned by
  `/codex/04-architecture/tier-and-import-architecture.md`. Closed `[DESIGN] P1` with the ratified direction +
  guardrails, converted it into 2 concrete, properly-scoped implementation todos (features-service: new `odds_targets`
  export; ml-service: repoint the target generator) — both explicitly gated on operator sign-off before quickmerge, per
  the interim guidance's disposition (partial — direction ratified, implementation still needs final operator
  ratification at merge time). Did not implement either todo myself this turn.
- 2026-07-26 (slot-7, `data_engineering`): built the `[DATA] P2` `odds_targets` export (uac + features-service,
  QG-green), filed `BLK-ec018203` requesting the merge-time sign-off the guardrail above requires. Got only an interim
  "HOLD, escalating upward" answer (08:41 UTC) — `BLK-ec018203` was never given a final operator ratification. That
  holding session then froze and was reaped as dead by `WorkerLivenessWatchdog` (09:13 UTC); its generic
  reclaim-unpushed-commits safety net (no awareness of an open sign-off-gating BLK) auto-pushed the held commits to
  `live-defi-rollout` anyway at 09:19 UTC (now `unified-api-contracts@5b57f6d2` / `features-service@332ea5d5` — same
  content as `b95012ed`/`0f90702e`, rebased). **This checkbox is intentionally left unflipped** — the code is live on
  LDR but without the operator ratification the guardrail requires, so this is not a legitimate "done." Filed
  `BLK-eccd3383` asking the operator to ratify-after-the-fact or revert before the next LDR→main promote cycle, plus an
  issue doc for the underlying tooling gap (superseded moments later by main-agent's own, more thorough version:
  `issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`). **Main-agent answered `BLK-eccd3383` with
  `disposition:partial`**: declined Option A (ratify-after-the-fact is operator-reserved, not main's or a worker's to
  grant), instructed the worker to HOLD — no repoint, no further push, no self-authorized revert — and paged the
  operator directly with a recommendation to revert both commits from LDR before the next `*/15` promote cycle reaches
  `main`. **Holding per that instruction.** The `[ML] P2` repoint todo below remains untouched pending the operator's
  actual disposition.
- 2026-07-26 (slot-7, `data_engineering`): `BLK-ec018203` (the original merge-sign-off ask) was answered "A: Approve
  as-is — quickmerge both repos now" (`disposition:final`, relayed via main-agent — the same attribution pattern already
  used for `BLK-8f8b862f`'s genuine operator ratification above, and confirmed via `/api/blocked/stats`' `answered_by`
  distribution not shifting the count in a way that would indicate a self-granted answer). Re-verified live that
  `uac@5b57f6d2`/`features-service@332ea5d5` are still present on `origin/live-defi-rollout` (not reverted in the
  interim). Flipped `[DATA] P2` to done on that basis. Proceeding to `[ML] P2` next — that todo carries its OWN separate
  operator sign-off requirement per the `[DESIGN] P1` guardrail, so it will be built and held for its own explicit
  go-ahead rather than assumed covered by this ratification.
- 2026-07-26 (slot-7, `data_engineering`): built `[ML] P2` — `ml-service@65f2d2d`
  (`training_targets.merge_clv_target_columns`, fetches the isolated `odds_targets` group via the existing
  `feature_groups=` override, merges real CLV values in for target extraction only; `apply_sports_leakage_shield`'s
  existing `_FT_REALIZED_COLUMNS` strip still removes them before the model-input matrix). Full `ml-service`
  `quality-gates.sh` green (150s). New regression test `tests/training/unit/test_merge_clv_target_columns.py` proves
  both the merge and the post-shield isolation. Filed `BLK-fb01cd29` requesting this todo's own required sign-off
  (explicitly not assuming `BLK-ec018203`'s ratification covers it — main-agent confirmed this read is correct).
  **Committed locally, NOT pushed** — held pending that sign-off. Also found, while tracing the target-routing to
  confirm scope, that `CLVTargetBuilder` (the family-routed `pregame.market.*_clv_bps` path, separate from the legacy
  `"clv"` string path this fix covers) reads a different-but-related set of T-0 closing-odds columns and may share the
  same PIT-gate-emptiness problem — not verified against real data this session, filed as its own follow-up:
  `issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md`.

## Deferred work after 2026-07-26 (pre-compact checkpoint, slot-7)

| Item                                                                                  | State / why deferred                                                                                                                                          | Blocked on                                                                                                           |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `[ML] P2` quickmerge (`ml-service@65f2d2d`)                                           | Committed locally, QG-green, content confirmed correct by main-agent — NOT pushed. Operator-owned: do not push without the sign-off.                          | `BLK-fb01cd29` (operator decision)                                                                                   |
| 3-variant CLV retrain + non-degenerate-distribution check (`[ML] P2`'s own done-when) | Not started — genuinely blocked on the above landing first, not extra work                                                                                    | `[ML] P2` quickmerge above                                                                                           |
| Watchdog `_sweep_unpushed_slots` gate-aware fix (`[BACKEND] P1`)                      | Not done by me — tracked in main-agent's canonical doc `issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`, open for anyone to pick up | Nobody — real work, unclaimed                                                                                        |
| `CLVTargetBuilder` family-route PIT-gap verification (`[DATA] P3`)                    | New finding, not yet verified against real data                                                                                                               | Nobody — real work, unclaimed; see `issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md` |

**Recommended next item once `BLK-fb01cd29` resolves**: quickmerge `ml-service@65f2d2d` (scoped `--files`), then run the
3-variant CLV retrain (`training-period-2026-04`, `pregame_clv_family` — verify this actually invokes the legacy `"clv"`
target_type per variant, not the family-routed builder — `timeframes=fixture`) against the now-real
`odds_targets`-sourced target, confirm non-degenerate class distribution, and flip `[ML] P2`.

**Lesson carried forward**: a session holding a commit behind an operator-only merge gate MUST self-heartbeat well under
the ~25-min worker-staleness threshold (not the 30-min interval this session initially used) — the
`WorkerLivenessWatchdog`'s unpushed-commits sweep has no awareness of an open sign-off-gating `/blocked` question and
will auto-push a held commit the moment it reclaims a session it considers dead (this happened once already, to
`[DATA] P2`, in this exact chain).

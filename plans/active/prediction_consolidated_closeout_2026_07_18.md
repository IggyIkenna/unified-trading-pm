---
doc_type: plan
title:
  Prediction consolidated close-out — one-pass code→migrations→coverage→smoke-test to MVP-backfill-ready (+ football
  cross-venue arb enablement)
summary:
  Single coordination plan that AGGREGATES (references, does not duplicate) every open prediction + prediction-touching
  IS/MTDS plan and issue into ONE ordered pass, mirroring cefi_consolidated_closeout_2026_07_18.md and
  tradfi_consolidated_closeout_2026_07_18.md — Phase A get ALL the code ready (writers live+batch, migration scripts,
  adapters, fixture-attribute writers), Phase B run the migrations (manifest/catalogue/CQG canonicalisation + backfill),
  Phase C data-status + honest-coverage (RE-ADD the removed dimensions-enumeration view + enumeration-driven canonical
  dedupe audit), Phase D re-smoke-test the backfills with data-pipeline-check-mtds and data-pipeline-check-is ADAPTED to
  prediction against -test- buckets — so prediction is verified complete and ready for the MVP backfills. Adds Phase E —
  the originating operator ask — football (soccer) cross-venue arb enablement — thread the canonical API-Football
  fixture id (af_fixture_id / build_fixture_id string) onto Polymarket AND Kalshi soccer markets as additive attributes,
  drive the join off the fixtures parquet OR name-parsing with robust alias resolution to a ~0% team-name gap (close the
  South-American alias hole + build a Kalshi soccer team registry), and unify the two currently-disconnected arb paths
  (features-service Kalshi↔Polymarket kernel + the e2e bookmaker/Betfair scanner) onto that shared fixture identity so
  live-odds-vs-Polymarket-vs-Kalshi arb becomes possible on a canonical basis.
status: active
nature: process
umbrella: true
asset_group: [prediction]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    features-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    prediction,
    close-out,
    consolidation,
    canonicalisation,
    instrument-id,
    manifest,
    honest-coverage,
    backfill,
    mvp,
    cross-venue-arb,
    sports-fixtures,
  ]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/data_completion_prediction_2026_07_15.md,
    /plans/archive/2026_07/prediction_canonical_identity_migration_2026_07_08.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md,
    /plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md,
    /plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/archive/2026_07/prediction_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/2026_07/prediction_consolidated_native_ao_extract_2026_07_25_finalize.md,
    /plans/archive/2026_07/prediction_cross_cutting_debt_index_2026_07_25.md,
  ]
created: 2026-07-18
last_updated: 2026-07-31 # was 2026-07-26 — /ag-closeout-audit prediction (scheduled) Finding-3 fix: added 6 previously-unindexed docs (2 kalshi issues, features_delta_one, prediction_trades_migration_concurrent_dispatch, 2 fresh 2026-07-31 adapter dead-code findings) to the Aggregated source docs index, and corrected the stale kalshi_live_capture_regression_and_drift entry (was "3 prose follow-ups", live-verified now 1 checkbox)
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
assigned_role: data_engineering
drift_direction: none
archive_exempt: true # gate_on_depends:false coordination hub — 0 native todos by design, 4 child Phase A-E plans still open (see frontmatter comment + Progress Log)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
  [
    prediction_phase_ab_residuals_2026_07_24,
    prediction_phase_c_data_status_ui_2026_07_24,
    prediction_phase_d_formal_smoke_and_backfill_2026_07_24,
    prediction_phase_e_football_arb_live_2026_07_24,
  ]
gate_on_depends: false # documents ordering only — this parent has 0 remaining native todos of its own after this pass (documentation + archival-gating only), so there is nothing left here to machine-hold
source:
  Operator, 2026-07-18 — asked whether we have canonical football fixture ids linking sports→prediction such that we can
  arb football live-odds-API vs Polymarket vs Kalshi, and whether the question groups are canonical. Finding — the
  fixture side is canonical (af_fixture_id / build_fixture_id) and joined to live bookmaker odds (~66% match); the
  question groups are canonical as a cross-venue THEMATIC label (canonical_question_group) but NOT keyed to the fixture
  id — Polymarket soccer computes the build_fixture_id string, Kalshi carries nothing, and the two arb code paths are
  disconnected. Operator then directed a single consolidated prediction close-out mirroring the cefi + tradfi ones that
  aggregates ALL prediction IS/MTDS plans+issues into one pass, ADDS the fixture-id threading + ~0% alias matching +
  arb-path unification, RE-ADDS the removed data-status dimensions-enumeration view and bakes an enumeration-driven
  canonical/dedupe audit into the migration (single source of truth), and re-smoke-tests prediction the same way cefi +
  tradfi are, using -test- buckets via data-pipeline-check-is / data-pipeline-check-mtds scoped to prediction shards for
  IS and MTDS. Authored slot-2 from a 6-agent read-only research pass; tab-2 unified-trading-pm was first synced from a
  stale June-12 HEAD up to origin/live-defi-rollout 6c4787972 so this is authored against the current corpus.
context_scope:
  [
    /plans/epics/predictions_master.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/04-architecture/prediction-batch-live.md,
    /codex/02-data/prediction-data-types-catalog.md,
  ]
---

# Prediction consolidated close-out — one pass to MVP-backfill-ready (+ football arb)

> **Purpose.** ONE place that aggregates every open prediction + prediction-touching IS/MTDS plan/issue into a single
> ordered pass. This plan **references** the source docs; it does not duplicate them. Close a track by closing its
> source doc(s), then tick it here. Mirrors `cefi_consolidated_closeout_2026_07_18.md` and
> `tradfi_consolidated_closeout_2026_07_18.md`; ordered per the operator's directive: **Phase A code → Phase B
> migrations → Phase C data-status/honest-coverage → Phase D re-smoke-test → MVP-backfill-ready**, then **Phase E** the
> originating football cross-venue arb enablement (gated on B+D). Two identity systems must be kept straight throughout:
> **`canonical_question_group` (CQG)** = a venue-agnostic THEMATIC family label (`SPORTS_EPL_MATCH`,
> `BTC_UP_DOWN_DAILY`) shared across Polymarket+Kalshi by design; **`af_fixture_id` / `build_fixture_id`** = the
> canonical API-Football fixture identity. They are separate today; Phase E is where a prediction soccer market gains a
> fixture link.

## Split notice (2026-07-24 — plan-hygiene line-cap remediation)

> **This plan was trimmed from 1488 lines and forked 5 ways**, per the operator-approved split in
> `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` (row 22: "4-way split along the plan's own Phase A-E
> boundaries"). Every todo and every Progress Log line was moved **verbatim** to its destination — nothing was
> summarized, rewritten, or silently dropped.
>
> | Child doc                                                                                                                                                                | Carries                                                                                      |
> | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
> | [`prediction_phase_ab_residuals_2026_07_24.md`](/plans/active/prediction_phase_ab_residuals_2026_07_24.md)                                                               | Phase A (writers/adapters/migration-scripts) + Phase B (run the migrations) residual todos   |
> | [`prediction_phase_c_data_status_ui_2026_07_24.md`](/plans/active/prediction_phase_c_data_status_ui_2026_07_24.md)                                                       | Phase C — data-status + honest-coverage                                                      |
> | [`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`](/plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md)                                 | Phase D — re-smoke-test the backfills, all shards                                            |
> | [`prediction_phase_e_football_arb_live_2026_07_24.md`](/plans/active/prediction_phase_e_football_arb_live_2026_07_24.md)                                                 | Phase E — football cross-venue arb enablement (depends_on-gated on B+D per the original ask) |
> | [`prediction_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/prediction_consolidated_closeout_history_2026_07_18.md) (archived, `status: complete`) | The full chronological Progress Log (autonomous ticks 1-31, ~917 lines, verbatim)            |
>
> **Retained here**: the Ground-truth verdict + MVP universe (foundational context every Phase depends on), the Codex
> SSOTs + aggregated source-doc index, the still-genuinely-open "Deferred work after 2026-07-18" items (blocked on
> shared-file drain windows, not stale), and a condensed pointer replacing the full tick-by-tick Progress Log.

**Per-child open-todo snapshot (2026-07-24 — so the split itself is AO-legible without opening each child):**

- [`prediction_phase_ab_residuals_2026_07_24.md`](/plans/active/prediction_phase_ab_residuals_2026_07_24.md) — **13
  open** (verified via `grep -c` 2026-07-25 consolidated-closeout split — was 11, +2 relocated in from this parent's
  former "Queued audits + reviews"/"Distinct Values" P3 sections: the adapter dead-code audit (new Phase-A "A5"
  subsection) and the merged `/data-pipeline-reconciliation` cadence + duplicate-note todo (Phase B); the POLYMARKET
  schema-extension item also relocated here but folded into the EXISTING A2 dual-write-trees todo, so it added no new
  checkbox). Top: [BACKEND] P0. Finish the prediction capture-incident remediation — harden the capture path; [BACKEND]
  P0. Kill the dead Kalshi `trading-api.kalshi.com` host reintroduced into the smoke matrix.
- [`prediction_phase_c_data_status_ui_2026_07_24.md`](/plans/active/prediction_phase_c_data_status_ui_2026_07_24.md) —
  **4 open**. Top P0: [UI] P0. RE-ADD the data-status "dimensions enumeration" view to deployment-ui/api.
- [`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`](/plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md)
  — **6 open** (verified via `grep -c` 2026-07-25 consolidated-closeout split — was 3, +3 relocated in from this
  parent's former "Queued audits + reviews" section: the `-is`/`-mtds` 3x-cadence top-ups and the adversarial
  AO-dispatch-readiness pass). Top (still the same 2 P0s): [DATA] P0. Run `data-pipeline-check-is` for prediction-only,
  all shards, post-migration; [DATA] P0. Run `data-pipeline-check-mtds` for prediction-only, all shards, post-migration.
- [`prediction_phase_e_football_arb_live_2026_07_24.md`](/plans/active/prediction_phase_e_football_arb_live_2026_07_24.md)
  — **3 open** (2 P1 + 1 P2, no P0 yet). Top: [BACKEND] P1. Verified end-to-end fixture link on Polymarket + Kalshi
  soccer; [BACKEND] P1. Wire the arb engine to CONSUME `af_fixture_id`.
- [`prediction_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/prediction_consolidated_closeout_history_2026_07_18.md)
  (archived) — **0 open** — VERIFIED: `status: complete`, 995 lines, zero unchecked checkboxes; pure verbatim record.

## Ground-truth verdict (from the folded issues — RE-VERIFY live before migrating, per Phase A0)

Authored from the folded plans/issues; **A0 (autonomous tick 1, 2026-07-18) has since re-measured prod live** — rows
marked "A0 live read" carry the measured correction (see Progress Log § A0). What the docs + A0 establish:

| Surface                                   | Canonical / linked?                                                          | Reality (cited source doc)                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CQG cluster atom in the live manifest     | **present at `captured`: 17,352 rows** — CORRECTED 2026-07-18 (A0 live read) | A0 measured 80,068 CQG bundle rows (captured 17,352 / empty_confirmed 60,286 / expected_unattempted 2,421 / attempted_failed 9), 81 distinct canonical CQG values — this SUPERSEDES the folded issue's "ZERO at captured" claim; the phantom wipe is fixed or intermittent. **Re-check** `issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` status before assuming a wipe (Phase-B item downgraded to verify-not-fix) |
| Prediction capture liveness               | **was dead 07-01→07-06**                                                     | capture-outage remediation in flight; KALSHI/POLYMARKET-PERP adapters hit the wrong Kalshi host → **fake PERPETUAL contaminated cefi (25,473 rows)** (`prediction_capture_incident_remediation_2026_07_06.md`)                                                                                                                                                                                                                            |
| MTDS prediction `-test-` bucket isolation | **MISSING (writes to PROD)**                                                 | `_test_bucket("prediction")` has no `-test-` sibling and falls back to the PROD `market-data-tick-prediction` bucket (`market-tick-data-service/scripts/pipeline_e2e_check.py:434-450`) — a prediction force/skip leg would write to PROD, breaking the test-bucket-only invariant cefi/tradfi enjoy                                                                                                                                      |
| Instrument-id canonical shape             | **partial**                                                                  | adapter `underlying` from `classify_*_to_canonical_group` + `canonical_instrument_id` from cross_venue_mapping are 4/8 done (`prediction_canonical_identity_migration_2026_07_08.md`)                                                                                                                                                                                                                                                     |
| Football fixture ↔ live bookmaker odds    | **joined, ~66%**                                                             | odds ticks carry `af_fixture_id` + `af_fixture_match_status`; ~66% fixture-level match, gap = South-American team-alias hole, not a join bug (`instruments-service/docs/SPORTS_INSTRUMENTS.md`)                                                                                                                                                                                                                                           |
| Football fixture ↔ Polymarket market      | **string bridge only**                                                       | Polymarket soccer computes the same `build_fixture_id()` string (`LEAGUE:HOME_v_AWAY:YYYYMMDD`) as the sports asset group (`instruments-service/.../reference_data/adapters/prediction/polymarket/parsing.py::_build_sports_id`) — the STRING, not the numeric `af_fixture_id`                                                                                                                                                            |
| Football fixture ↔ Kalshi market          | **NONE**                                                                     | Kalshi titles are city-level ("Seattle vs Cleveland") with no team registry → no fixture id at all; per-venue Kalshi↔Polymarket sports pairing needs a title-map the schema doesn't persist → honestly absent                                                                                                                                                                                                                             |
| Cross-venue arb code                      | **two disconnected paths**                                                   | features-service `cross_venue_arb_detector` (Kalshi↔Polymarket, crypto-oriented in practice) + e2e `live_arb_scanner.py` (bookmakers+Betfair+Polymarket, NO Kalshi, prototype); neither keys on `af_fixture_id`                                                                                                                                                                                                                           |

**Conclusion**: prediction is NOT YET MVP-backfill-ready, but two of the four blockers above are RESOLVED, not open —
the CQG cluster atom is no longer being wiped (A0 live-read corrected the row above: 17,352 `captured` rows; the
phantom-wipe issue is downgraded to verify-not-fix) and MTDS prediction `-test-` bucket isolation is FIXED end-to-end
(`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`, 2026-07-18: `market-tick-data-service@b06d1e6b` /
`@2e50851d` / `@86d70de9`). What remains genuinely open: capture only just recovered and its hardening is still in
flight (`prediction_phase_ab_residuals_2026_07_24.md`), the formal post-migration smoke-green + MVP backfill gate itself
has not yet run (Phase D's remaining P0 todos), and the football fixture identity that would enable
live-odds-vs-Polymarket-vs-Kalshi arb is still threaded onto Polymarket-as-a-string only and onto Kalshi not at all
(`prediction_phase_e_football_arb_live_2026_07_24.md`, all 3 items open). This plan scopes the full end-to-end.

### Shard atom for prediction (SSOT-canonical — key is `canonical_question_group`, NOT `(instrument_id OR underlying)`)

The cross-AG shard-atom frame
(`pipeline_mode · date · asset_group · venue · [chain] · instrument_type · data_type · (instrument_id OR underlying) · [quote · margin] · source`)
applies to prediction on every axis EXCEPT the key column. Per the SSOT
(`/codex/02-data/availability-manifest-and-data-status.md:57-60`) the prediction atom is
`(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` — keyed
on **`canonical_question_group`**, which is neither a per-market `instrument_id` nor `underlying`. Two grains, kept
straight:

- **Manifest/shard grain** = a MANIFEST-ONLY bundle (`data_type=prediction_canonical_question_group`) keyed on
  `canonical_question_group` (`BTC_UP_DOWN_DAILY`, `SPORTS_EPL_MATCH`), re-computed at rebuild. `underlying` is a
  ROW-LEVEL display column here, NOT the key — drop `underlying` as a key axis for prediction.
- **Raw object grain** = per-CID: raw `trades` / `book_snapshot_5` objects stay per-market (`instrument_id` = Polymarket
  condition_id / Kalshi ticker) — the per-market rows INSIDE the bundle.

Corollaries the generic frame misses for prediction: `[chain]` absent; `[quote · margin]` present only for KALSHI-PERP /
POLYMARKET-PERP; **IS side collapses to `venue → dates`** (no data_type axis — the instruments parquet IS the metadata);
MTDS drilldown is **CQG-led** — `venue → canonical_question_group → data_type → date`
(`/codex/02-data/data-status-drilldown-hierarchy.md:42`), i.e. CQG sits ABOVE data_type (opposite ordering to the flat
atom). Representative rows:

| shard (venue · data_type · type)                                       | key                                                  | notes                                                                                                        |
| ---------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| POLYMARKET · `prediction_canonical_question_group` · prediction_market | `canonical_question_group` (e.g. `SPORTS_EPL_MATCH`) | manifest-only bundle; per-market rows carry CID `instrument_id` + `underlying` + `build_fixture_id` (soccer) |
| KALSHI · `trades` · prediction_market                                  | per-CID `instrument_id` (market ticker)              | flat per-market raw object                                                                                   |

**This is the root of the Phase-B CQG-wipe**: the phantom reconciler treats prediction as if keyed on a per-object
`instrument_id` instead of the `(canonical_question_group, day)` bundle, so it wipes the bundle rows. A0/A2/B and the
Phase-D verify gate MUST assert the atom key is `canonical_question_group` (bundle) / per-CID `instrument_id` (raw),
never `underlying`.

## Distinct Values / axis-value census (2026-07-20 measured)

The corpus-wide SSOT tracker is `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md` — its
2026-07-20 ground-truth table already shows prediction clean on every axis (non-canonical/total distinct:
`venues 0/2, instrument_types 0/1, data_types 0/4, chains 0/1`). This section adds a second, independent corroborating
source: the same-day `/data-pipeline-reconciliation` four-surface pass against `asset_group=prediction`, full doc at
`/plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_20.md`.

- **Prediction's own `instrument_type` axis** (745,136-row manifest census): `PREDICTION_MARKET` 741,029 (99.46%,
  canonical-cased) · `prediction_market` (lower) 4,001 (0.54%, **C2a RULED** UPPERCASE-target, `migration_pending` —
  operator D1, 2026-07-20; compared case-insensitively, no casing finding emitted during the migration_pending window;
  see `/codex/02-data/reconciliation-finding-taxonomy.md` §5.1 — NOT refused/unruled) · `prediction` 76 + `None` 30 (F2
  — malformed VALUE, not casing — **106/745,136 = 0.014%**).
- **Cross-AG comparison, each AG's own 2026-07-20 reconciliation result doc (not a joint census — categories aren't
  always the same measurement)**:
  - cefi: C2a `PERPETUAL` 7,220,102 vs `perpetual` 9,146 (0.127% lower-case tail); separately, 130,130 rows (1.27% of
    10,282,640) carry a BLANK `instrument_type` (the malformed-VALUE-not-casing analogue of prediction's F2).
  - tradfi: C2a `EQUITY` 1,685,476 vs `equity` 81,145 (**4.59%** lower-case tail — the largest measured casing tail of
    the AGs compared here).
  - defi: both `LENDING`/`lending`, `POOL`/`pool`, `PERPETUAL`/`perpetual` forms present same sampled day — no
    corpus-wide % measured (single-day sample scope only).
  - sports: `instrument_type` is not the sports axis of record (keyed on `entity`/`league`/`day` instead) — its own
    report does not carry a comparable corpus-wide `instrument_type` casing %.
- **Reading**: on the two axes that WERE measured corpus-wide for more than one AG (malformed-value rate: prediction
  0.014% vs cefi 1.27%; casing-tail rate: tradfi 4.59% vs cefi 0.127% vs prediction 0.54%), prediction's malformed-VALUE
  rate is the lowest measured — this is the "prediction already measures cleanest" fact referenced elsewhere in this
  plan's gap analysis, now cited with its actual numbers rather than left undocumented. This is NOT an unqualified
  "prediction is cleanest on every axis" claim — the casing-tail axis alone would rank cefi below prediction.
- **Reconciliation-cadence tracking relocated (2026-07-25 consolidated-closeout split)**: the post-Phase-B-migration
  `/data-pipeline-reconciliation` re-run (previously a P3 "Duplicate note" checkbox here, which was itself already a
  duplicate of the Queued-Audits P2 reconciliation-cadence todo) is now ONE combined todo in
  [`prediction_phase_ab_residuals_2026_07_24.md`](/plans/active/prediction_phase_ab_residuals_2026_07_24.md)'s Phase B
  section — see that doc for the live checkbox and the current cadence state (2 of 3 dated passes already cited: the
  confirmed 2026-07-20 baseline above, plus a 2026-07-24 pass —
  `/plans/audit/results/data_pipeline_reconciliation_prediction_2026_07_24.md`; only the post-Phase-B final gate
  remains). **Predating-run search (2026-08-04, `prediction_consolidated_native_ao_extract_2026_07_25.md` todo 4)**:
  confirmed-absent — no `/data-pipeline-reconciliation prediction` report dated before 2026-07-20 exists anywhere in
  `plans/audit/results/`, `plans/active/`, or `plans/archive/`; the 2026-07-20 file above is the earliest.

## MVP universe (the Phase-D / Phase-E readiness target)

- **Venues**: POLYMARKET + KALSHI (`VENUES_BY_ASSET_GROUP["prediction"]`).
- **Data-types (MVP)**: `trades` + `book_snapshot_5` (the depth/orderbook grain — top-5 CLOB ladder; there is no
  separate `quotes`/`orderbook` type) at the market grain; `prediction_canonical_question_group` at the cluster grain;
  `market_lifecycle` at the market-id grain. Market groups: crypto, politics, sports.
- **Football-arb slice (Phase E)**: the Kalshi × Polymarket football-league overlap — Polymarket
  `POLYMARKET_PREDICTION_LEAGUES` (23 football leagues) ∩ Kalshi `KALSHI_SPORTS_TICKER_PREFIXES` (6 football: EPL,
  Bundesliga, La Liga, Serie A, Ligue 1, Champions League) against the 33 API-Football Prediction leagues + ~20
  bookmakers via the Odds API. Start where all three overlap (EPL, top-5 European leagues).
- **Codex SSOTs (MVP-readiness, batch=live=paper)**: `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`
  (batch=live determinism spine — paper(W) must equal batch-rerun(W) trade-for-trade, ε=0 PROOF — applies to
  prediction's MVP backfill the same as every other AG) plus `/codex/04-architecture/prediction-batch-live.md` (already
  cited in the main Codex SSOTs section above; repeated here because this MVP-universe section previously had no Codex
  SSOTs list of its own).

Everything below is scoped so these cells are captured, canonical, honestly-covered, smoke-tested green, and (Phase E)
fixture-linked before MVP backfill.

---

## Phases A-E — forked out (see Split notice above)

> All 5 phase bodies (writers/adapters/migrations/data-status/smoke-test/football-arb) now live in the 4 child plans
> listed above. This parent keeps only the ground-truth context, the aggregated index, and still-open
> cross-phase-blocked items (below) that don't cleanly belong to one child.

## Codex SSOTs (read before touching a phase)

`/codex/02-data/prediction-data-types-catalog.md`, `/codex/02-data/prediction-schema-paths.md`,
`/codex/02-data/prediction-perps-sourcing.md`, `/codex/02-data/prediction-settlement-availability-convention.md`,
`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/data-status-drilldown.md`,
`/codex/02-data/data-status-drilldown-hierarchy.md`, `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`,
`/codex/02-data/venue-availability.md`, `/codex/02-data/honest-absence-downstream-handling.md`,
`/codex/04-architecture/prediction-batch-live.md`, `/codex/04-architecture/cross-venue-prediction-arb-detection.md`,
`/codex/09-strategy/architecture-v2/cross-cutting/prediction-markets.md`,
`/codex/09-strategy/operational/prediction-markets-codification-gaps.md`, `/codex/01-domain/sports-instruments.md`,
`/codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md`. Plus (Phase E odds/fixture side, out-of-repo):
`instruments-service/docs/SPORTS_INSTRUMENTS.md`.

## Aggregated source docs (referenced, not duplicated)

> Format: path (real repo-root link) → its currently-OPEN todos only, one line each (`[TAG] P<N>.` prefix preserved,
> evidence/prose dropped). Docs with 0 open todos say so explicitly. >8-open docs list every P0/P1 in full and cap P2/P3
> with a `+N more` marker — nothing is silently dropped. Re-verified 2026-07-24 against the live corpus.

- **`prediction_cqg_residual_2026_07_24.md`** — ARCHIVED 2026-07-29 (0 open todos:
  [`/plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md`](/plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md)),
  via `prediction_satellite_ao_dispatch_batch5_2026_07_26_finalize.md`'s reconciliation + the MTDS CODE_QUICK backlog
  pass — cqg grain wired (`unified-api-contracts@283d7449` + `instruments-service@38e393de`), dead-code cleanup shipped
  (`market-tick-data-service@5bf8a3c7`).

- **This plan's own Phase A-E children (2026-07-24 fork — were listed in the Split-notice table above but not repeated
  here; added so this index is the single place every source doc lives, including this plan's own forks)**:
  - **[BACKEND] P0.**
    [`prediction_phase_ab_residuals_2026_07_24.md`](/plans/active/prediction_phase_ab_residuals_2026_07_24.md) — 13 open
    (2026-07-25 consolidated-closeout split, was 11; +2 relocated in from this parent's former "Queued audits +
    reviews"/"Distinct Values" sections). Top: finish the prediction capture-incident remediation; kill the dead Kalshi
    `trading-api.kalshi.com` host.
  - **[UI] P0.**
    [`prediction_phase_c_data_status_ui_2026_07_24.md`](/plans/active/prediction_phase_c_data_status_ui_2026_07_24.md) —
    4 open. Top: RE-ADD the data-status "dimensions enumeration" view to deployment-ui/api.
  - **[DATA] P0.**
    [`prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`](/plans/active/prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md)
    — 6 open (2026-07-25 consolidated-closeout split, was 3; +3 relocated in from this parent's former "Queued audits +
    reviews" section). Top: run `data-pipeline-check-is` for prediction-only, all shards, post-migration; run
    `data-pipeline-check-mtds` for prediction-only, all shards, post-migration.
  - **[BACKEND] P1.**
    [`prediction_phase_e_football_arb_live_2026_07_24.md`](/plans/active/prediction_phase_e_football_arb_live_2026_07_24.md)
    — 3 open (2 P1 + 1 P2). Top: verify the end-to-end fixture link on Polymarket + Kalshi soccer; wire the arb engine
    to CONSUME `af_fixture_id`.
- **Capture / correctness**:
  - [`plans/active/prediction_capture_incident_remediation_2026_07_06.md`](/plans/active/prediction_capture_incident_remediation_2026_07_06.md)
    (9 open total)
    - **[VERIFY] P0.** Demo dry-run: returned tickers are genuine perps (`BTC-PERPETUAL` shape, `contract_type` present)
    - **[CODE] P1.** Make the perp base URL config-driven — `KALSHI_PERP_ENV=demo|prod` (via `UnifiedCloudConfig`)
    - **[CODE] P1.** Extract the RSA-PSS signing that ALREADY EXISTS in `adapters/prediction/kalshi.py`
    - **[CODE] P1.** Rewrite `KalshiPerpReferenceDataAdapter.get_instruments` to hit `…/trade-api/v2/markets/margin`
    - **[RESEARCH] P1.** `docs.polymarket.com` perps API — find the markets-listing endpoint + auth (beta-gated)
    - **[CODE] P1.** Repoint `polymarket_perp` against Polymarket's perps API (demo/testnet if available)
    - **[VERIFY] P1.** Pin the prediction-store event-capture gap (the real question the purge-vs-move decision needs)
    - +2 more (P2/P3, one DESCOPED-NOT-MVP) — see file for the rest
  - [`/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`](/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md)
    - **[VERIFY] P2.** Post-fix: re-measure prediction attempted/captured trajectory on a sampled window
    - **[INFRA] P1.** Launch the historical prediction re-backfill under the widened catalogue — **RULED 2026-07-28, GO
      (sharded SPOT VMs, full 2025-03-14→today range, no partial-window shortcut)**, retagged away from
      `[BLOCKED-OPERATOR-DECISION]`; see that doc's Todos section for the full mandate
  - [`plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md`](/plans/active/issues/kalshi_live_capture_regression_and_drift_2026_07_13.md)
    — **1 open** (corrected 2026-07-31, `/ag-closeout-audit prediction` — was stale "3 prose follow-ups", all 3 resolved
    since; live-verified via direct checkbox read). **[DATA] P2.** Verify the Kalshi execution-service paper-order flow
    end-to-end — the same deliverable as `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 6's second leg,
    itself currently `BLOCKED-OPERATOR-DECISION` (gated on the same credential/host question, see that plan).
  - [`plans/active/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md`](/plans/archive/2026_08/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md)
    — **added to this index 2026-07-31** (`/ag-closeout-audit prediction` Finding 3 fix). **RESOLVED + archived
    2026-08-09** (0 open) — covered by `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 5
    (`execution-service@577b9a884`; both secret reshape and non-live paper-order verify shipped).
  - [`plans/active/issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md`](/plans/archive/issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md)
    — **added to this index 2026-07-31** (Finding 3 fix). 3 open, covered by
    `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo 7 (recurrence check + reclassification + contingent
    fix, not yet dispatched).
  - [`plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`](/plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md)
    — **added to this index 2026-07-31** (Finding 3 fix). 3 open P3, self-dispatching (`assigned_vm: planning`); its
    higher-value item is already substantively closed via `data_pipeline_check_mdps_features_2026_07_20.md`, only a
    small currently-unreachable volatility-module echo remains.
  - [`plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md`](/plans/archive/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md)
    — **added to this index 2026-07-31** (Finding 3 fix). 2 prose-only recommended fixes, no checkboxes; dual-tagged
    `[prediction, ao]`, `parent_epic: orchestrator_master` — genuinely owned by the `ao` tranche's own closeout
    (dispatcher/checkpoint architecture, not prediction data work), not re-drafted here per the primary-owner rule for
    multi-tranche docs.
  - [`plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md`](/plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md)
    — **new 2026-07-31** (filed by `prediction_consolidated_native_ao_extract_2026_07_25.md` todo 1's adapter dead-code
    audit). **RESOLVED 2026-08-09** — operator ruled DELETE (option A) 2026-08-07, executed + archived
    (instruments-service@4b55c57b) via batch10's todo; the doc is now 0-open-todos and archived.
  - [`plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`](/plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md)
    — **new 2026-07-31** (same audit). 1 open `[BACKEND] P2` — same shape (A) delete vs (B) keep-and-document,
    operator-gated.
  - [`plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`](/plans/archive/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md)
    (resolved, 1 residual — cross-link; note: archived location, not `plans/active/issues/`)
    - **[CODE] P2.** Durable fix: bound memory in the prediction CLOB universe scan (chunked pagination → incremental)
- **Manifest / CQG / phantom**:
  - [`plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md`](/plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md)
    — 0 open todos (ARCHIVED 2026-07-29; both re-based via decision 338 and shipped — `unified-api-contracts@283d7449` +
    `instruments-service@38e393de` + `market-tick-data-service@5bf8a3c7`).
  - [`plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`](/plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md)
    — **1 open** (corrected 2026-07-30, batch2 finalize re-triage; was wrongly marked 0 open — `status: open` on the doc
    itself). **[DATA] P2.** market-tick-data-service — investigate the KALSHI-venue scaffold-row provenance mislabel
    (129,227 rows carrying `venue=KALSHI` with `pipeline_mode`/`source` stamped
    `polymarket_clob`/`polymarket_gamma_api`, spanning dates back to 2018; NOT the already-fixed captured-row defect).
    The doc's own bundle-atom root-cause remediation (items 1-6) and its combined residual close-out (a/b/c/d) are all
    done/superseded — only this one residual todo remains open.
  - [`plans/active/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md`](/plans/archive/issues/mtds_prediction_rebuild_instrument_type_mismatch_2026_08_01.md)
    — **added to this index 2026-08-06** (`/ag-closeout-audit prediction`, closing a `check_ag_closeout_linkage.py`
    graph-disconnection gap — see
    [`ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md`](/plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md)).
    Self-dispatched (`assigned_vm: planning`, `status: open`), so not orphaned in the ag-closeout-audit sense — but was
    graph-disconnected from this closeout family (no `related:`/mention link), which is now fixed by this citation. Code
    fix (writer `instrument_type` stale-literal) + root-cause fix + prod deploy all DONE 2026-08-01/03 per the doc's own
    todos 1 and 3; **[OPERATOR] P2** (todo 2) — decide whether to lift
    `canonicalize_prediction_manifest_2026_07_18.py`'s HELD prod-run status — reads `[ ]` at the top level but its own
    body text describes steps 2-6 (dry-run + 2 full apply/verify rounds) as DONE 2026-08-03; not independently
    re-verified or flipped by this run (self-dispatched doc, outside this audit's remit to edit) — flagging the apparent
    stale-checkbox for whoever next touches this doc or a future `/na-eligibility-audit`/`/plan-reconcile` pass.
  - [`plans/archive/issues/phantom_captures_prediction_2026_06_28.md`](/plans/archive/issues/phantom_captures_prediction_2026_06_28.md)
    — 0 open todos (writer-fix done; final re-fetch/backfill todo SUPERSEDED 2026-07-29 into Phase-D MVP-backfill gate +
    data_completion_prediction; archived)
  - [`plans/archive/issues/mtds_prediction_migration_connection_pool_hardening_2026_07_10.md`](/plans/archive/issues/mtds_prediction_migration_connection_pool_hardening_2026_07_10.md)
    (resolved residual; archived location) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/mdps_prediction_tick_bucket_uac_ssot_404_2026_07_14.md`](/plans/archive/issues/mdps_prediction_tick_bucket_uac_ssot_404_2026_07_14.md)
    (done-evidence; archived location) — 0 open todos (closed/archived/record-only)
  - [`plans/archive/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md`](/plans/archive/issues/polymarket_book_snapshot_5_dead_stream_2026_06_26.md)
    (done-evidence; archived location) — 0 open todos (closed/archived/record-only)
- **Canonicalisation / data-completion**:
  - [`plans/active/data_completion_prediction_2026_07_15.md`](/plans/active/data_completion_prediction_2026_07_15.md)
    (primary open data track; 23 open total)
    - **[DATA] P0.** C0 ONE bundled walk: copy legacy `raw_tick_data/` + `processed_candles/` objects → canonical
      `pred-prd`
    - **[DATA] P0.** C-pipeline_mode RIDER: the `pipeline_mode=` partition for prediction lands in THIS walk
    - **[DATA] P0.** Post-walk: re-run the `(date,venue,data_type)` comparison → legacy-only CELLS = 0
    - **[CODE] P0.** Ship the MTDS+UAC live-writer bundle change (spec above) TOGETHER WITH the MDPS companion change
    - **[DATA] P0.** Per-AG (cefi/tradfi/prediction): Phase-0 layout audit → re-tarball+pin SHAs → G1 full-corpus
    - **[DATA] P1.** C-source RIDER: stamp `source` = the data-source API (`polymarket_clob` / `polymarket_gamma_api`)
    - **[DATA] P1.** E6 CF-7 relabel — CF-7 NOW BAKED INTO THE MIGRATOR (mtds@4b311c93)
    - **[DATA] P1.** Build the historical rollup migration script (reuse `rebuild_prediction_manifest.py` logic)
    - **[DATA] P1.** Pre-migration drain (stop prediction writers/crons per the HARD RULE) → snapshot `_index`
    - **[DATA] P1.** Post-verify: CF-audit the pred surface (row-parity per (day,venue,cqg) sampled; manifest
      cross-check)
    - **[CODE] P1.** FLAG-3 (deployment-api) — DECIDED (operator 2026-06-02): env-tier the `*-store` buckets
    - **[DATA] P1.** Downstream service C-walks (MDPS rides the AG tick walk; features/strategy/execution)
    - **[CODE] P1.** FLAG 3 (bucket-SSOT, deployment-api) — DECIDED (operator 2026-06-02): env-tier the `*-store`
      buckets
    - **[DATA] P1.** MDPS C-walk: bundle any `processed_candles/` debt into the SAME AG tick-bucket walk
    - **[DATA] P1.** features C-walk: ONE bundled walk per `features-*-{ag}` index for any P0 debt
    - **[DATA] P1.** strategy C-walk: ONE bundled walk for strategy output `_index` debt
    - **[DATA] P1.** execution C-walk: ONE bundled walk for execution-record/ledger `_index` debt
    - **[DATA] P1.** Post-walk per service: re-run the P0 CF audit → all applicable CF GREEN (data-state)
    - +5 more (3×P2, 2×P3) — see file for the rest
  - [`plans/archive/2026_07/prediction_canonical_identity_migration_2026_07_08.md`](/plans/archive/2026_07/prediction_canonical_identity_migration_2026_07_08.md)
    (archived location, `status: active` retained on the doc itself)
    - **[DATA] P1.** Regenerate/backfill `prod/catalog.parquet` for Prediction after the `raw_symbol`/`base_asset` fix
- **Venue-perps / CLOB depth**: split + archived 2026-07-24 (was
  `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`) into:
  - [`plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md`](/plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md)
    - **[SCRIPT] P1.** Polymarket-perp enumerator — BLOCKED-UPSTREAM (no public perps API exists yet — CONFIRMED)
  - [`plans/active/prediction_live_clob_depth_capture_2026_07_24.md`](/plans/active/prediction_live_clob_depth_capture_2026_07_24.md)
    - **[DATA] P2.** Verify END-TO-END depth-history retention — the RAW live book store is rolling-latest-window
  - [`plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md`](/plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md)
    (9 open + 2 in-progress — listed in full, not over the >8 cap threshold)
    - **[SCRIPT] P0.** Populate POLYMARKET instrument lifecycle start/end + bound manifest empty-emission to it
    - **[DESIGN] P1.** Fixture-pairing RESIDUAL — registry-resolution + mapping-population + arb wiring (nested under
      the in-progress fixture-pairing parent; parser itself already shipped UAC@3effe2fc)
    - **[SCRIPT] P1.** e2e-testing/instruments-service — series-scoped historical backfill — DEEP CORPUS DONE
    - **[OPS] P2.** Tarball-overwrite race: a concurrent fleet `create-code-tarballs` (from a clone behind LDR) clobbers
    - **[UAC] P2.** Politics/geo cross-venue canonicalization — Kalshi Politics (2049 series: electoral-college)
    - **[DESIGN] P2.** Per-instrument same-game/same-settlement arb PAIRING within a shared cqg group
    - **[DATA] P2.** Residual lowercase `venue=kalshi` + blank/UNKNOWN venue rows in the prediction `_index` manifest
    - **[SCRIPT] P2.** cqg partition-completeness — recent-window catalogue re-enumeration
    - **[DATA] P3.** 1,454 prediction `_index` rows still at schema v4 (vs 192,713 at v9; DISCOVERED 2026-06-23)
- **UI / bucket**:
  - [`plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md`](/plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md)
    - [VERIFY]**[UI] P0.** After the writer + UI ship: re-walk the deployment-ui prediction panel; POLYMARKET drill-down
    - **[SCRIPT] P1.** Phase 5 — canonical-groups backfill (30+ groups beyond the initial 9). Full list in the archived
    - **[SCRIPT] P2.** Prediction sentinel fan-out for `prediction_canonical_question_group` empty rows
- **ML / arb (downstream, gated)**:
  - [`plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md`](/plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md)
    - **[SCRIPT] P0.** Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix (BLOCKED-ON)
    - **[ANALYSIS] P0.** Run the acceptance-metrics computation above against the real walk-forward output (BLOCKED-ON)
    - **[GATE] P0.** Block Group F until walk-forward AUC ≥ 0.55 AND calibration error ≤ 5% (ACTIVE GATE)
    - **[ANALYSIS] P1.** Persist model + metrics to the ml-models registry; tag `model_family=sports_arb_v1`
    - **[AGENT] P1.** Predictions MTDS completion-% slice — per-(canonical_question_group, day) completion %
- **Cross-cutting (shared w/ sports)**:
  - [`plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`](/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md)
    (resolved)
    - **[OPS] P2.** Verify the next scheduled `lifecycle-catalogue-regen-sports` run (next `0 1 * * *` UTC)
    - **[INFRA] P3.** Grant `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com`
  - sports feeder side lives in `sports_master` (fixtures/odds that Phase E consumes) — cross-link, not owned here.
- **Cross-asset arb (separate, archived/tradfi)**:
  - [`plans/archive/2026_05/cme_polymarket_arb_2026_05_08.md`](/plans/archive/2026_05/cme_polymarket_arb_2026_05_08.md)
    (CME↔Polymarket, `status: complete`) — 0 open todos (closed/archived/record-only)
- **Skills / engine**:
  - [`plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md`](/plans/archive/2026_07/data_pipeline_e2e_check_2026_07_10.md)
    (archived location, `status: active` retained on the doc itself) — 0 open todos (closed/archived/record-only)
  - - the `data-pipeline-check-mtds` / `data-pipeline-check-is` skills (skill definitions, not plan files — no todos to
      track here).
- **Parent epic (stale — see Progress Log)**:
  - [`plans/epics/predictions_master.md`](/plans/epics/predictions_master.md) (41 open total — 24 P0 + 5 P1 + 12
    untagged success-criteria checkboxes; **re-counted 2026-07-26, `/plan-reconcile` prediction shard** — was "38 …+ 9
    untagged", the P0/P1 splits were right and the untagged tail was undercounted by 3. 40 of the 41 sit under that
    epic's own explicitly SUPERSEDED history-only sections — "Consolidated todos (P0 only)" 29, "May-23 deliverable" 9,
    "`available_at` adapter stamping" 2 — so this doc's "functionally SUPERSEDED" characterisation agrees with the
    epic's own banners rather than contradicting them; the 1 genuinely-live remainder is the `[SCRIPT] P1` predictions
    `feature_groups` → UAC `FEATURE_REQUIRED_INPUTS` item under "Folded-in scope 2026-07-15". The items below are
    UNVERIFIED against current reality, listed here only per the completeness rule)
    - **[SCRIPT] P0.** Replace POLYMARKET writer (`orchestrator.py:1990–1995`): old `data_type = <base_asset>` → new
    - **[SCRIPT] P0.** Reader migration: every callsite with `data_type=BTC|ETH|...` →
    - **[SCRIPT] P0.** Per-market lifecycle gating in feature compute: `LookaheadBiasError` extension
    - **[SCRIPT] P0.** Strategy-service prediction archetypes: archetype configs reference `canonical_question_group`
    - **[TEST] P0.** End-to-end smoke: 1 canonical_group (`BTC_UP_DOWN_HOURLY`) × 1 day; run feature compute + verify
    - **[SCRIPT] P0.** New script `mtds_migrate_polymarket_per_base_asset_to_canonical_group.py` (in scripts/)
    - **[SCRIPT] P0.** Manifest reflip script `mtds_reflip_polymarket_per_base_asset.py`
    - **[SCRIPT] P0.** Old parquet deletion — only AFTER new parquets verified by hand-inspection (sample 10 random)
    - **[SCRIPT] P0.** Backfill any missing canonical_groups — markets in `conditionid_universe.csv` that classifier
      maps
    - **[SCRIPT] P0.** Confirm `migrate_polymarket_canonical.py` (MTDS) ran for all targets; afterwards delete legacy
    - **[SCRIPT] P0.** Every reconciler wraps work in `unified_trading_library.run_lifecycle.run_lifecycle(...)`
    - **[SCRIPT] P0.** Each reconciler supports `--max-flips-per-run=10000` halt safety; operator confirms first 10k
    - **[SCRIPT] P0.** CSV audit at `gs://{pid}-reconciler-audit/{run_id}/`
    - **[SCRIPT] P0.** Predictions asset_group panel — drill-down shape: `(venue, canonical_question_group, day)`
    - **[SCRIPT] P0.** Run ml-training Model 2A walk-forward against the Group-D-validated feature matrix (gated on
      sports)
    - **[ANALYSIS] P0.** Acceptance metrics — log-loss, calibration, AUC for win/draw/loss; threshold per consolidated
      plan
    - **[SCRIPT] P0.** Training-config sanity check: feature columns match FSS schema, label leakage absent
    - **[GATE] P0.** Block Group F until walk-forward AUC ≥ 0.55 and calibration error ≤ 5% (ACTIVE GATE)
    - **[SCRIPT] P0.** Synthetic `OTHER` canonical-question-group bucket — the classifier MUST map every Polymarket
    - **[VERIFY] P0.** Phase 1 timeline check against 2026-05-23 master deadline: 14/37 done (38%) as of 2026-05-07
    - **[VERIFY] P0.** After Phase 1 ships: re-walk deployment-ui prediction panel; POLYMARKET drill-down renders
    - **[SCRIPT] P0.** features per-market LookaheadBiasError check — per CLAUDE.md prediction-lifecycle rule
    - **[SCRIPT] P0.** deployment-ui 3-level hierarchy + per-shard parquet download — today MARKETS list is flat
    - **[SCRIPT] P0.** Lifecycle-bounded `available_at` stamping for Polymarket + Kalshi adapters
    - **[ANALYSIS] P1.** Persist model + metrics to ml-models registry; tag `model_family=sports_arb_v1`
    - **[AGENT] P1.** Per-(canonical_question_group, day) completion %: HOURLY = 24 expected/day, DAILY = 1, ELECTION =
      1
    - **[SCRIPT] P1.** Phase 5 — canonical-groups backfill (30+ groups beyond initial 9). Full list in archived issue
    - **[SCRIPT] P1.** Predictions feature_groups → UAC `FEATURE_REQUIRED_INPUTS`. Per-canonical_question_group
      (line 818)
    - **[SCRIPT] P1.** Predictions feature_groups → UAC `FEATURE_REQUIRED_INPUTS`. Per-canonical_question_group (line
      1000, duplicate of the 818 entry)
    - +9 more (untagged success-criteria checklist items, e.g. "Polymarket backtest runs end-to-end") — see file for the
      rest

**Additional cross-cutting / issue-doc coverage** — forked out 2026-07-25 (consolidated-closeout split pass) to
[`prediction_cross_cutting_debt_index_2026_07_25.md`](/plans/archive/2026_07/prediction_cross_cutting_debt_index_2026_07_25.md),
moved verbatim (~20 docs cataloged: canonical-id-builder retrofit, candle-canonical-path migration execution,
MDPS/features pipeline-check debt, is-daily-enum capture-heal, cross-asset backfill maintenance windows, and a dozen
more issue-doc digests whose open work is genuinely cross-AG — defi/cefi/tradfi/sports-scoped, not prediction-owned
dispatch surface). See that doc for the full digest; nothing here was prediction-specific work, so nothing was lost by
the move.

**Sports-tagged, prediction-relevant (shared infra/scope with sports_master)** — primary tracking: `sports_master` /
sports's own consolidated closeout plan; short digest only:

- [`plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`](/plans/archive/2026_08/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md)
  (8 open, all `[DESIGN] P3`) — top: define the decay-window STATISTIC precisely; define the WINDOW boundaries
  (signal-time → first-leg fill vs last-leg). +6 more — see file for the rest.
- [`plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md`](/plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md)
  (5 open, all `[BACKEND]/[DESIGN]/[SCRIPT] P3`) — top: add `run_sports_backtest(args, config, config_path) -> int`;
  wire a data source (reuse the Group-B fixture dataset). +3 more — see file for the rest.
- [`plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md`](/plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md)
  (8 open total — listed in full, not over the >8 cap threshold)
  - **[DATA] P1.** NEW compute, not a rename: add per-bookmaker raw decimal-odds retention
  - **[DATA] P1.** Update `unified_api_contracts`'s `OddsFeaturesMixin`/`SportsFeatureVector` fields to the names chosen
  - **[DATA] P2.** Migrate `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS`
  - **[BACKEND] P2.** Close the silent-agnostic gap in `SportsFeatureLoaderMixin`
  - **[BACKEND] P2.** Migrate `SportsValueBettingEngine` + `SportsArbDutchingEngine` (`on_tick`'s)
  - **[BACKEND] P2.** Migrate the legacy `strategy_service/adapters/sports_feature_subscriber.py`
  - **[REVIEW] P3.** Once todos 2–6 land, write the FSS-output ↔ ml-service-input ↔ strategy-service-input parity test
  - **[REVIEW] P3.** Cross-reference this migration against whichever plan ends up doing the "wire sports end-to-end"
- [`plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md`](/plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md)
  (6 open, all `[OPERATOR]/[INFRA]/[DATA]/[REVIEW] P3`) — top: decide whether to pursue a live sports-odds ingestion
  path at all (the structural blocker); once that's a yes, scope the MTDS live-odds connector. +4 more — see file.
- [`plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`](/plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md)
  — 0 open todos. **DECIDED 2026-07-23**: naming scheme canonicalized per
  [`sports_odds_feature_naming_canonicalization_2026_07_21.md`](/plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md)
  (Option A, UAC-as-SSOT); scoped 3-repo migration in flight — do not re-litigate.
- [`plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`](/plans/archive/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md)
  (resolved) — 0 open todos (closed/archived/record-only)

**Newly discovered (2026-07-24 completeness check via `grep -l '^asset_group:.*prediction'` — not previously named in
this section)**:

- [`plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md`](/plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md)
  — **1 open** (corrected 2026-07-30, batch2 finalize re-triage; was wrongly marked 0 open — `status: open` on the doc
  itself). **[BACKEND] P1.** Build the paper-LIVE routing seam for `AtomicInstruction` → `AtomicLegExecutor` via the UTL
  `EventTransport` facade — the architecture question is **RULED (operator, 2026-07-28)**, so this is now build-ready
  work, not an open operator decision; the doc's separate paper-vs-live promotion + Betfair account/credential/
  jurisdiction sign-off items remain OPERATOR-GATED (per the doc's own "OPERATOR DECISIONS" list) but do not block
  building this specific routing plumbing.

## Queued audits + reviews — forked out (2026-07-25 consolidated-closeout split)

> All 6 todos previously tracked here (5 triaged into an AO-dispatchable batch, 1 an operator-ruled schema-extension
> migration) relocated to their thematically-correct Phase child below — this parent's native todo count is now 0,
> documentation + archival-gating only (see the frontmatter `depends_on` on all 4 Phase children).

| Item (was tracked here)                                                   | New home                                                                                                                                  |
| ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Adapter dead-code/fallback audit (`[BACKEND] P2`)                         | `prediction_phase_ab_residuals_2026_07_24.md`, new "A5 — Adapter code-quality audit" subsection                                           |
| `data-pipeline-check-is` 3x cadence top-up (`[DATA] P2`)                  | `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`, Phase D section                                                             |
| `data-pipeline-check-mtds` 3x cadence top-up (`[DATA] P2`)                | `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`, Phase D section                                                             |
| `/data-pipeline-reconciliation` verify + 3x cadence (`[DATA] P2`)         | `prediction_phase_ab_residuals_2026_07_24.md`, Phase B section (merged with the former "Distinct Values" P3 duplicate note above)         |
| Adversarial AO-dispatch-readiness pass (`[REVIEW] P2`)                    | `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`, Phase D section                                                             |
| POLYMARKET `prediction_trades` schema-extension migration (`[DESIGN] P1`) | `prediction_phase_ab_residuals_2026_07_24.md`, Phase B section (folded into the existing A2 dual-write-trees todo, same source issue doc) |

**AO-dispatch status**:
[`prediction_consolidated_native_ao_extract_2026_07_25.md`](/plans/archive/2026_07/prediction_consolidated_native_ao_extract_2026_07_25.md)
(`status: draft`) already carries an AO-dispatchable execution copy of the first 5 rows above (its own todos 1-5,
drafted before this relocation). Its own text and its finalize plan's text were corrected in this same pass to reconcile
evidence into the NEW homes above rather than into this now-relocated section — see that plan for the currently-drafted
AO-dispatch path; the table above + the phase-child docs are the durable-tracking side of record.

## Deferred work after 2026-07-18 (HELD — unblock when the concurrent tradfi/cefi migrations free the shared files / a drain window opens)

The autonomous slot-2 pass (operator: "prediction-specific files only") shipped every prediction-specific-file-safe
unit; the items below each require a SHARED file another slot is actively migrating, an irreversible prod-migration
drain window, or an operator decision. They are ordered, not abandoned — each names its exact blocker.

- [x] ✅ [DATA] P2. **STALE — CLOSED 2026-07-31 (na-eligibility-audit, prediction tranche).** A4 column materialization
      (shared): add the 6 fixture-match fields to UAC `InstrumentRecord`; IS `process_write._records_to_dataframe` join
      (~6-line extension of the `clob_token_ids` block reading `fixture_match_for_instrument_key`); MTDS prediction-tick
      schema. **Already shipped, this checkbox was never flipped**: per
      [`prediction_phase_ab_residuals_2026_07_24.md`](/plans/active/prediction_phase_ab_residuals_2026_07_24.md)'s own
      A4 section (`[x]` DONE 2026-07-18) — UAC `InstrumentRecord` + `INSTRUMENTS_PARQUET_SCHEMA` shipped
      `unified-api-contracts@e7ed754e`; IS `process_write._records_to_dataframe` join shipped
      `instruments-service@e3ffc613`. MTDS prediction-tick schema is explicitly **OPTIONAL/DEFERRED** there ("catalogue
      carries the attrs; tick-grain only if the arb path needs it") — a deliberate scope decision, not open blocked
      work. The separate historical BACKFILL of these columns remains tracked as its own live Phase-B checkbox
      ("Backfill the fixture-match attributes (A4 columns) across historical Polymarket + Kalshi soccer") — not
      superseded by this close.
- **E2 alias additions** (shared): add the missing Kalshi soccer team aliases (E2's worklist) to
  `unified_api_contracts.external.api_football.team_mappings`, plus the South-American club aliases for the odds-side
  ~66%→~100% — to reach the operator's ~0% gap.
- **A2 residual** (shared / other repo): identity-migration todo 2 only (`prod/catalog.parquet` regen — prod-GCS run,
  gated on the shared canonical migration so it doesn't bake transitional ids) — corrected 2026-07-21, plan-reconcile:
  todos 7 (`gcs_paths.py` bucket-abbreviation flip) and 8 (MDPS UAC-pin verify) were resolved 2026-07-19 (see the A2
  todo above), this residual list was never trimmed to match.
- **CQG residual §5** (shared + operator decision): add `pipeline_mode=live_*` prefix shapes to UAC `possible_manifest`
  — needs the BATCH-satisfied-by-LIVE-evidence semantics call (A: union batch+live [REC]; B: batch-only).
- **Phase-B prod migration** (drain window): the enumeration-driven manifest canonicalisation (`prediction_trades`→
  `trades`, empty `source`, `base_asset` whitespace) + the fixture-attr backfill — needs a pre-migration VM drain the
  concurrent tradfi/cefi migrations currently occupy. **`instrument_type`→`PREDICTION_MARKET` is effectively DONE**
  (99.46% per the 2026-07-20 census in "Distinct Values / axis-value census" above, up from the stale 11.70% dry-run
  baseline this bullet previously cited) — only the 0.54% C2a lowercase tail (RULED UPPERCASE-target,
  `migration_pending` — operator D1, 2026-07-20; the harness case-robustness gate is resolved/archived, see
  `/codex/02-data/reconciliation-finding-taxonomy.md` §5.1) and the 0.014% malformed-value residual remain, neither
  gated on this drain window.
- **Phase C/D/E remainders** gated on the above (data-status dimensions view is partly already-served by
  `catalogue-filter-options`; smoke-test needs the MTDS prediction `-test-` bucket; arb-path unification needs the
  materialized columns + E2 resolution).
- **instruments-store CF-2/CF-3 path-scheme gap** (operator decision): live re-audit 2026-07-26 found prediction is the
  one non-sports AG where the instruments-store object path never got the `asset_group=`/`pipeline_mode=` retrofit
  cefi/defi/tradfi already have — needs an architect pick (A/B/C) on whether/how to fold the segment into prediction's
  two existing path shapes. See
  [`instruments_store_prediction_path_scheme_not_asset_group_pipeline_mode_2026_07_26.md`](/plans/archive/issues/instruments_store_prediction_path_scheme_not_asset_group_pipeline_mode_2026_07_26.md).

## Progress Log — condensed (2026-07-24, replaces the pre-split ~917-line tick-by-tick log)

- **na-eligibility-audit 2026-07-31 (prediction tranche)**: KEEP-NA, stale item closed — the "A4 column materialization
  (shared)" Deferred-work checkbox was superseded (UAC + IS legs shipped `unified-api-contracts@e7ed754e` /
  `instruments-service@e3ffc613` per `prediction_phase_ab_residuals_2026_07_24.md`'s own A4 section; MTDS leg explicitly
  OPTIONAL/DEFERRED, not blocked open work) — closed with citation, doc stays NA. Separately archived
  `issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md` (0 open todos, terminal) and
  fixed this doc's own aggregated-source-docs link to its new `plans/archive/issues/` path in the same pass. No other
  open item changed; this doc's role as the live Phase A-E coordination hub (0 native todos by design per its own
  `gate_on_depends: false` note) is unaffected — not archived, still the live index.

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 1 open ([DATA] P2, A4 fixture-match column
  materialization), which is the shared cross-repo half of work whose prediction-side legs are tracked in the Phase A-B
  residuals fork. Note for whoever picks up `issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md`
  Finding 3: that finding proposes adding 4 docs to THIS doc's aggregated-sources index, and
  `prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md` todo 2 separately edits the same index section —
  same-file adjacency, sequence them rather than running both blind.
- **2026-07-31 — `/ag-closeout-audit prediction` scheduled run (ag_closeout_auditor, slot 4, dispatch agt-592e74).**
  Phase 0: re-discovered the covering-plan set via `generate_ag_closeout_audit_candidates.py` (7 auto-detected covering
  docs) — confirmed a real, not-yet-fixed instance of the script's known `depends_on`-resolution gap (previously noted
  for `native_ao_extract`-shaped forks): the script only resolves `depends_on` from discovered `_finalize` docs, never
  from the closeout hub's OWN `depends_on` — so this doc's 4 Phase A-E children
  (`prediction_phase_ab_residuals`/`_c_data_status_ui`/`_d_formal_smoke_and_backfill`/`_e_football_arb_live`, none of
  which have their own `_finalize` sibling) are not structurally recognized as covering docs, only accidentally caught
  by prose-text citation matching. Not fixed here (out of this run's authorized scope — the script is
  `ao`/tooling-owned, `parent_epic: agent_operating_framework_master`); flagged for that tranche via this run's own
  parked-findings doc. Phase 0.3: 52 raw `asset_group:[prediction]` candidates; of the 12 the script reported "never
  cited," 11 are genuinely cross-cutting multi-AG docs (tagged with 3+ peer AG markers, e.g. "bugs found across
  CeFi/DeFi/TradFi/Sports/Prediction") correctly excluded by the skill's orthogonality filter (which the script itself
  does not implement), and 1 (`mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`) was a citation
  false-positive — its basename WAS already cited in `prediction_consolidated_native_ao_extract_2026_07_25.md`'s
  Progress Log, just broken by a prettier line-wrap inserting a stray space mid-filename (fixed same commit — the exact
  "prettier can wrap a long bare filename" trap the skill's own Phase 0.3 notes warn about, confirmed live). Net: 0
  genuinely-never-triaged prediction-primary candidates from the mechanical pre-filter after correction. Phase 1:
  Workflow-classified the 2 docs with real fresh ground — both 2026-07-31-filed adapter dead-code findings
  (`is_polymarket_dead_fixture_cross_reference`, `mtds_prediction_adapters_dead_rest_polling_interface`) — both
  `orphaned_never_touched` but correctly non-batchable (each doc's own text already says its A-delete-vs-B-document
  choice is "not adjudicated," a genuine operator/plan-owner judgment call, and `prediction_phase_ab_residuals`'s A5
  subsection already acknowledges both without fixing them inline, per the same reasoning). Applied 2 mechanical fixes
  from yesterday's parked findings (`issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md`): Finding 2
  (batch4/batch6 duplicate cqg-reenumeration todo — checked off batch6's copy in place, citing batch4 todo 3 as sole
  owner, without reordering any other todo given the fleet's live positional-task-ID-instability warning) and Finding 3
  (added the 4 named docs + the 2 new dead-code docs to this index, corrected the stale
  `kalshi_live_capture_regression_and_drift` entry). Findings 1 (inherited `cefi` tag on 2 forks) and 4
  (`prediction_trades_migration_concurrent_dispatch` needs `ao`-tranche adoption) remain open — both still genuinely
  operator/cross-tranche-gated, re-confirmed not stale. Phase 3: no new batch drafted — every orphaned doc found is
  either non-batchable (operator-gated) or already covered; batch4 and batch6 remain the live dispatch surface. Full
  report + remaining-open findings in this run's own parked-findings doc
  (`issues/ag_closeout_audit_prediction_parked_2026_07_31.md`).

> **The full tick-by-tick history was NOT deleted** — it lives verbatim in
> [`prediction_consolidated_closeout_history_2026_07_18.md`](/plans/archive/2026_07/prediction_consolidated_closeout_history_2026_07_18.md)
> (autonomous ticks 1-31, 2026-07-18 through 2026-07-20). Every genuinely-open item that log surfaced was cross-checked
> against the 4 Phase children and the "Deferred work after 2026-07-18" section above — nothing was silently dropped.

- **2026-07-18** — Plan authored, folding prior prediction plans/issues; Phase A-E structure set; football arb (Phase E)
  added as the originating operator ask.
- **2026-07-18/19** — Phase A writers/adapters shipped incrementally (autonomous ticks); fixture-attribute resolver +
  side-table stamping shipped (`is@85988ade`).
- **2026-07-19/20** — 3-venue paper arb proof landed end-to-end (Kalshi/Polymarket/Betfair, `execution@5ed8a029`);
  cross-repo seam e2e proof shipped (`e2e@7665a027`); the autonomous slot-2 pass shipped every prediction-specific-
  file-safe unit, leaving only shared-file/drain-window/operator-decision items open (the "Deferred work after
  2026-07-18" section above).
- **2026-07-24** — Plan line-cap remediation: 4 Phase children extracted (A+B, C, D, E), full Progress Log archived
  verbatim to `prediction_consolidated_closeout_history_2026_07_18.md`, this parent condensed to a lean coordination
  index with an enriched Aggregated source docs index covering every active prediction + prediction-touching plan/issue.
- **2026-07-24 (later same day)** — Distributed 6 gate-doc todos from `data_pipeline_e2e_milestones_gate_2026_07_24.md`
  into this file: added a "Distinct Values / axis-value census" section (cites the corpus-wide SSOT tracker
  `/plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md`, whose ground-truth table already shows
  prediction clean on every axis, plus the corroborating same-day `/data-pipeline-reconciliation` run; **correction
  2026-07-24 same-session**: an earlier draft of this entry wrongly claimed no such tracker doc existed — it does, this
  entry now cites it directly); added the 4 Phase A-E children to the Aggregated source docs index (previously only in
  the Split-notice table); added a Codex SSOTs bullet to "MVP universe" citing
  `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`; and added a new "Queued audits + reviews" section
  with 5 bounded todos (adapter dead-code audit, -is/-mtds/reconciliation 3x-checkpoint top-up, and an adversarial
  AO-dispatch-readiness pass mirroring sports's Track Y) for a future dispatched worker — none executed in this pass,
  per the distributing task's scope (documentation placement only).
- **2026-07-25 — Consolidated-closeout split pass (reconciled against the same-day `native_ao_extract` sibling pass).**
  Reconciliation first: `prediction_consolidated_native_ao_extract_2026_07_25.md` (+ its gated finalize, both
  `status: draft`) had already triaged this parent's 7 native todos and added the "AO-eligibility triage" pointer-note
  to "Queued audits + reviews", but had NOT relocated any content — the 7 native checkboxes were still live here. This
  pass completed the relocation: (1) `depends_on` set to all 4 Phase children (`gate_on_depends: false` —
  documentation/archival-gating only, nothing left to machine-hold); (2) `related:` extended with the 2 satellite
  AO-dispatch batches + `native_ao_extract` + its finalize + the new cross-cutting-debt-index child; (3) the "Distinct
  Values" P3 duplicate-note todo and all 6 "Queued audits + reviews" todos relocated verbatim (with reconciling edits,
  not blind copies) into `prediction_phase_ab_residuals_2026_07_24.md` (adapter dead-code audit as a new "A5"
  subsection; the reconciliation-cadence + duplicate-note merged into one Phase-B todo; the POLYMARKET schema-extension
  folded into the existing A2 dual-write-trees todo) and `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`
  (the `-is`/`-mtds` 3x-cadence top-ups + the adversarial AO-dispatch-readiness pass, all 3 into the Phase D section) —
  both former sections left as short stub + pointer-table (heading text preserved so existing corpus references still
  resolve by name); (4) the "Additional cross-cutting / issue-doc coverage" subsection (~20 non-prediction-specific
  cross-AG docs, ~171 lines) forked verbatim to the new `prediction_cross_cutting_debt_index_2026_07_25.md` (LOCAL plan,
  pure digest, no AO-dispatch surface of its own); (5) `prediction_consolidated_native_ao_extract_2026_07_25.md` + its
  finalize + `prediction_satellite_ao_dispatch_batch2_2026_07_25.md` corrected (corpus-wide referrer fixup) to point
  their reconciliation targets at the NEW phase-child locations instead of this now-relocated section; (6) phase_ab's
  and phase_d's open-todo counts corrected corpus-wide (11→13, 3→6, verified via `grep -c` — the design brief's own
  estimate of 7 for phase_d didn't reconcile against the actual 3 items named for relocation; used the verified count).
  Net: parent trimmed from 764 to 611 lines (`wc -l`, post-prettier) with 0 remaining native todos; zero engineering
  work was done or lost — pure reorganisation, every action still a real, live checkbox somewhere in the corpus.
- **2026-07-26 — `/plan-reconcile` prediction shard (autonomous).** Re-measured every countable digest claim in the
  Aggregated-source-docs index against real `- [ ]` counts. Result: all 6
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` todos targeted at this file are confirmed genuinely landed (§1
  adapter dead-code audit, §2 Distinct-Values census section, §11 the 3 checkpoint top-ups, §12 the 4 Phase A-E digest
  bullets, §13 the adversarial-pass todo, §14 the MVP-universe Codex SSOTs bullet) — several now living in the
  2026-07-25 phase children, which is the split working as intended, not drift. Every child-plan open-count in the index
  re-measured exact (cqg=2, phase_ab=13, phase_c=4, phase_d=6, phase_e=3, capture-incident=9). One count was provably
  wrong and is corrected above: the `predictions_master.md` epic entry said "38 open total — 24 P0 + 5 P1 + 9 untagged";
  measured 41 = 24 P0 + 5 P1 + **12** untagged. Also recorded there: 40 of those 41 sit under that epic's own
  explicitly-SUPERSEDED history-only sections, so this doc's "functionally SUPERSEDED" wording agrees with the epic's
  own banners — an earlier read of this as a live contradiction between two active docs was refuted by counting the
  todos per section.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) -- coordination-hub doc (0 native todos,
  archive_exempt), codex-only list is correct/minimal; child-phase plans already machine-linked via depends_on.
- **na-eligibility-audit 2026-08-04 (prediction tranche)**: KEEP-NA, valid — 0 native open todos (coordination hub by
  design, `archive_exempt: true`, `gate_on_depends: false`; confirmed live via `grep -cE '^- \[ \]'` = 0). Only content
  change since the 2026-07-31 marker is today's 07:48 commit adding an explicit report-path citation + a predating-run
  confirmed-absent note to the Distinct Values section (a `prediction_phase_ab_residuals` todo-4 partial-slice
  side-effect) — non-substantive to this doc's own classification. Still the live index for its 4 Phase A-E children
  (all still open); not archived. Doc stays NA.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (prediction tranche, autonomous)**: KEEP-NA, valid — 0 native open checkboxes
  (coordination hub by design, `archive_exempt: true`, 4 Phase A-E children still open under it), agrees with the
  07-30/07-31/08-04 markers. The 6-bullet prose-only "Deferred work after 2026-07-18" section (confirmed-trap checked —
  no `- [ ]` markup, so it doesn't surface in the grep count) is genuine operator/shared-file-gated work, correctly
  KEEP-NA, not stale. Doc stays NA, not archive-eligible.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — 0 native open checkboxes, re-confirmed
  (`archive_exempt: true`, `gate_on_depends: false` coordination hub; `depends_on` lists the 4 Phase A-E children, all
  still open under their own docs — this parent has nothing of its own to reclassify). Nothing to reclassify.

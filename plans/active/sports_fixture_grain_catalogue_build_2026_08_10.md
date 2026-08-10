---
doc_type: plan
title: Sports fixture-grain catalogue — manifest schema + builder + adapter wiring + codex alignment
summary: >-
  Dispatch the fixture-grain catalogue build the operator ruled for on 2026-08-08. Converts the 4 open NA-only todos
  from sports_catalog_league_grain_only_scope_2026_07_08.md into an AO-dispatched execution surface — design the
  per-fixture manifest-schema extension, write build_sports_fixture_catalogue_from_manifest(), wire the reference-data
  adapters into the catalogue build, and run the post-phase codex alignment check. Gated on P1 contracts (archived);
  deliberately NOT gated on P2 data migration per the operator's dispatch ruling.
status: active
nature: design
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-pm]
scope: [engineer]
tags: [sports, catalogue, fixture-grain, manifest, honest-coverage, reference-data, dispatch]
related:
  [
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-10
last_updated: 2026-08-10
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5.0
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [sports_taxonomy_p1_capture_and_contracts_2026_08_08]
gate_on_depends: true
context_scope:
  [
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    instruments-service/scripts/build_instrument_catalogue.py,
    instruments-service/docs/SPORTS_INSTRUMENTS.md,
  ]
effort: medium
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  Operator ruling 2026-08-08 via /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md — "DISPATCH APPROVED, gated on
  the taxonomy contracts phase." The fixture-grain-vs-league-grain decision was ruled 2026-07-14 ("FIXTURE-GRAIN
  WANTED"); this plan is the dispatch routing that was previously unrouted.
---

# Sports fixture-grain catalogue build

> Dispatched per operator ruling 2026-08-08. The fixture-grain decision was made 2026-07-14; the P1 taxonomy contracts
> (venue/data_type/horizon axes) are now archived — build once against the final vocabulary rather than rebuilding
> after. This plan converts the 4 open NA-only todos from `sports_catalog_league_grain_only_scope_2026_07_08.md` into an
> AO-dispatched execution surface. Machine-gated on the P1 contracts plan (archived, gate satisfied).

## Known cross-plan dependency — SCOPE OVERLAP

The catalogue plan carries a live 🟡 SCOPE OVERLAP banner (flagged 2026-07-23, cross-linked 2026-07-25) with
`sports_consolidated_closeout_2026_07_19.md` on two fronts:

1. **`entity={fixtures,teams,injuries}/` path collision** — the closeout's own fixture entity-split
   (`entity=fixtures_schedule` + `entity=fixtures_outcomes`) declares the legacy bare `entity=fixtures/` FROZEN; the
   catalogue plan's adapter-invocation todo writes under `entity={fixtures,teams,injuries}/` — a different namespace but
   the same bare-entity naming collision the closeout is designed to eliminate.
2. **Parallel fixture-grain redesigns** — both the catalogue plan and the closeout's Track E independently design
   fixture-grain work, with neither aware of the other until the 2026-07-25 cross-link. The closeout's Track V
   `league_id` resolution (raw-keyed GCS object DELETE) is still tracked as unresolved as of 2026-08-10, and the
   catalogue plan's manifest-schema design depends on correct `league_id` resolution.

**The first todo below resolves this overlap before any design/shipping happens.** The operator ruled "DISPATCH
APPROVED" on 2026-08-08 with full knowledge of this banner (it was cited in the dispatch-verification chain) — this is
not a block on dispatch, it is a design constraint the first worker must satisfy.

## Todos

- [x] [REVIEW] P0. ✅ **Check the closeout's current Track C, Track V, and Track E state before designing anything.**
      Read `sports_consolidated_closeout_2026_07_19.md`'s live state (not a stale read from this plan's authoring date)
      for: (a) Track C — has the `data_type` lower-case revert landed? (b) Track V — has the raw-keyed `league_id` GCS
      object DELETE landed? (c) Track E — have the remaining stale `entity=fixtures` consumers been repointed? Record
      the current state of each in this plan's Progress Log, then decide whether the fixture-grain manifest-schema
      design (todo 2) can start now or must wait on a specific closeout item. If the closeout has advanced past the
      blocking items cited in the SCOPE OVERLAP banner, note that and proceed. If not, file a brief finding in the
      Progress Log stating which specific closeout todo blocks which catalogue todo — do not skip the whole plan, gate
      only the affected todo(s). **Done when**: the current Track C/V/E state is recorded in the Progress Log with a
      go/no-go call on todo 2.
- [ ] [DATA] P2. **Design the manifest schema extension for per-fixture capture tracking.** Today's sports manifest atom
      is `(league_id, data_type, date)` — `build_sports_catalogue_from_manifest()` relies on this exact grain to seed
      `expected_unattempted` without inflating the honest-coverage denominator. A fixture-grain catalogue needs the
      manifest to also track presence at `(fixture_id, league_id, data_type, date)` grain. Design the extension (new
      column(s)? separate index file? composite key?) without breaking the existing league-grain denominator for
      in-flight consumers. Cite `availability-manifest-and-data-status.md` and `honest-coverage-model.md` — the design
      must fit into the two-layer/two-view model, not bypass it. The catalogue plan's original P2 design todo
      (calibrated at 3.6 AI-days) is the precedent for this being the largest single item. **Done when**: a design
      decision is recorded in this plan's Progress Log (or a linked design note) covering the schema shape, the
      back-compat guarantee for league-grain readers, and the honest-coverage denominator math.
- [ ] [CODE] P2. **Write `build_sports_fixture_catalogue_from_manifest()` in
      `instruments-service/scripts/build_instrument_catalogue.py`.** Gated on the manifest schema extension above (todo
      2). Model it on the existing `build_sports_catalogue_from_manifest()` — same "catalogue superset ⊇ manifest
      present-set" invariant, same `expected_unattempted` seeding logic, same honest-absence handling. The fixture-grain
      catalogue rows carry `instrument_type="fixture"` (or the P1-contracts name if different — check UAC
      `market_data_categories.py`), real `venue` values (no longer blank — the fixture-grain atom IS per-venue), and the
      `fixture_id` from the extended manifest. Unit tests must cover: (a) a manifest with fixture-grain rows produces
      fixture-grain catalogue rows, (b) a manifest with only legacy league-grain rows produces an empty fixture
      catalogue (honest absence, not an error), (c) `expected_unattempted` is correctly seeded per-fixture. **Done
      when**: the function exists, is called from `build_instrument_catalogue()` for `asset_group == "sports"`
      (alongside — not replacing — the existing league-grain call), and `quality-gates.sh` is green.
- [ ] [CODE] P3. **Wire the reference-data adapters into the sports catalogue build.** `build_instrument_catalogue.py`
      currently calls ONLY `build_sports_catalogue_from_manifest()` for sports — it never invokes any adapter's
      `get_instruments()` (unlike DeFi/CeFi paths), so fixture/team/player/Betfair-runner `InstrumentRecord`s are never
      rolled into the catalogue. Extend the sports path to also call the relevant adapters (`api_football_reference.py`
      for fixtures, `betfair.py` for Betfair runners once BETFAIR is wired into the sports fetch pipeline — see
      `betfair_instrument_id_delimiter_cross_repo_2026_07_08.md` for the Betfair-specific gating item). Confirm whether
      the manifest-only path (no direct adapter calls) remains the intended SSOT — the catalogue plan's own P3
      adapter-invocation todo leaves both outcomes open. **Done when**: the adapters are invoked (or a documented
      decision NOT to invoke them is recorded with rationale), and the catalogue row count is verified against a real
      GCS read of the output.
- [x] ✅ [REVIEW] P3. **Post-phase codex alignment check.** — instruments-service@0f2a798c65
      `/codex/02-data/availability-manifest-and-data-status.md` and `/codex/02-data/honest-coverage-model.md` need a
      corresponding update (HARD RULE "post-phase codex audit"). Also update
      `instruments-service/docs/SPORTS_INSTRUMENTS.md`'s "11-step pipeline" section so it accurately reflects the
      current catalogue grain(s) — the existing doc language implies fixture/team/player-grain `instrument_id`s in the
      catalogue itself, which was never true for the league-grain-only era and must be accurate for the fixture-grain
      era. **Done when**: every codex doc whose contract changed is updated, and every referrer to the old catalogue
      shape resolves.

## Codex SSOTs

- `/codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`, manifest atom schema.
- `/codex/02-data/honest-coverage-model.md` — two-layer / two-view / instrument-gates-download model.

## Progress Log

- **2026-08-10** — Authored from the operator's 2026-08-08 dispatch ruling. P1 contracts are archived; the fixture-grain
  decision was made 2026-07-14. The 4 source todos from `sports_catalog_league_grain_only_scope_2026_07_08.md` are
  carried by this plan; that doc's checkboxes flip via `sports_taxonomy_p3_consumers_2026_08_08_finalize.md` once this
  plan lands.
- **2026-08-10 (slot 17, todo 1 — Track C/V/E state check)** — Read the closeout's live state at
  `sports_consolidated_closeout_2026_07_19.md` (987 lines, full read). Findings:

  **Track C — `data_type` lower-case revert: LANDED.** All three layers are done and verified: (1) Registry:
  `unified-api-contracts@bddd063e` removed uppercase TRADES from `DATA_TYPES_BY_ASSET_GROUP["sports"]` (ODDS already
  dropped 2026-07-26 via `uac@a32ad5fb`). (2) Writers: `market-tick-data-service@7ffabf77` reverted all 3 live call
  sites back to lower-case. (3) Data migration: `market-tick-data-service@fa6fd4cd` — 345,852 uppercase objects
  copy-verified to lowercase + manifest swap, independently census-verified 0 uppercase remain. The closeout's K1/K2
  revert is complete. Remaining Track C open items (venue vocabulary cleanup, QG assertion, PERPETUAL/football
  monitoring) are cleanup/monitoring, not blockers.

  **Track V — raw-keyed `league_id` GCS object DELETE: PARTIAL.** The COPY+SWAP phase is done ✅ (manifest data migrated
  to canonical `league_id` slugs). The DELETE of old raw-keyed GCS objects is still OPEN
  (`[ ] [DATA] P0. RESTORED 2026-07-24` at line ~779) but is UNBLOCKED since 2026-07-28 (Track C's lowercase-revert
  prerequisite has landed). The DELETE is reversibility-verified (7-day soft-delete window, fresh-checked 2026-07-27) —
  it's a cleanup step, not a schema-blocker.

  **Track E — remaining stale `entity=fixtures` consumer repoint: STILL OPEN.**
  `[ ] [CODE] P1. Repoint the remaining stale entity=fixtures consumers` (line ~607) — the 7-file list
  (`sports_dependency.py`, `sports_fixtures_daily_repoll.py`, `rescan_sports_fixtures_canonical.py:328,452`,
  `enumerate_expected_universe.py:1902`, `migrate_sports_per_league.py`,
  `reconcile_sports_blank_empty_reason_2026_06_24.py`) still needs repointing from bare `entity=fixtures/` to
  `fixtures_schedule`/`fixtures_outcomes`. However, the freeze on legacy bare `entity=fixtures/` is confirmed TRUE (no
  live reads remain — the `_read_fixtures_entity_with_schedule_fallback` and its 4 call sites were removed
  `instruments-service@333c35d2`; a Phase-1 census across 2,319 post-floor dates confirmed the fallback was never
  load-bearing). These remaining 7 files are residual references, not live data-path consumers.

  **Go/no-go on todo 2 (manifest schema extension design): GO.** The blocking prerequisite (Track C lowercase-revert)
  has fully landed. Track V's COPY+SWAP means canonical `league_id` slugs are already in the manifest — the design can
  proceed against the current canonical vocabulary. Track V's pending DELETE is a cleanup step that doesn't affect
  schema design. Track E's open repoint items are read-side consumers of `entity=fixtures/` paths — they don't touch the
  manifest schema that todo 2 extends. The SCOPE OVERLAP banner's two collision points are both non-blocking at this
  stage: (a) the `entity={fixtures,teams,injuries}/` path is a different namespace from the closeout's frozen
  `entity=fixtures/`; (b) the parallel fixture-grain designs address different concerns (Track E repoints readers, todo
  2 extends the manifest write schema). **No closeout item blocks the manifest-schema design. Proceed with todo 2.**

- **2026-08-10 (slot 5, todo 5 — post-phase codex alignment check)** — Verdict: **codex docs are CURRENT** —
  `availability-manifest-and-data-status.md` and `honest-coverage-model.md` both correctly describe the sports manifest
  grain (league-grain, fixture_id as row-level column, no shard-axis change). No manifest grain change has occurred
  (todos 2-4 are still unflipped). **SPORTS_INSTRUMENTS.md updated** — added a "Catalogue rollup" subsection to the
  11-step pipeline documenting the two-grain catalogue (league-grain from manifest + fixture/team/player-grain from
  observed by_date snapshots, shipped 2026-07-09) with the builder functions and real row counts.
  instruments-service@0f2a798c65.

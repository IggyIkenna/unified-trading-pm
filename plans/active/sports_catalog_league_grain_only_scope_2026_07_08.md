---
doc_type: plan
title:
  Sports reference catalog is intentionally league-grain-only today — decide + scope fixture/team/player-grain catalog &
  coverage tracking
summary: |
  `prod/catalog.parquet` for sports has 116 rows, all `venue=""` and `instrument_type="league"` — confirmed via a
  real GCS read (2026-07-08). This is NOT a silently-broken write path (unlike the earlier weather stale-GCS-path
  bug): `build_sports_catalogue_from_manifest()` in `scripts/build_instrument_catalogue.py` is a documented,
  deliberate 2026-06-07 design decision to scope the sports "could-exist" catalog to LEAGUE grain only, because the
  captured manifest atom itself is per-(league_id, data_type, date) with no fixture/team/player grain — a
  fixture-grain catalogue would inflate `expected_unattempted` against a manifest that can never match it. The
  11-step pipeline in SPORTS_INSTRUMENTS.md describes fixture/team/player reference DATA flowing through
  instruments-service to GCS, which is real and separate from this catalog — but nothing today rolls that data up
  into fixture/team/player-grain catalog ("could-exist") rows or coverage tracking. This plan scopes the decision +
  follow-on work, it does not force an immediate fix.
status: active
nature: design
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags:
  [sports, catalog, reference-data, coverage, manifest, league-grain, fixture-grain, honest-coverage, data-completeness]
related:
  [
    instruments-service/docs/SPORTS_INSTRUMENTS.md,
    plans/audit/results/canonical_instrument_id_audit_2026_07_08.md,
    plans/active/issues/sports_manifest_unknown_league_id_2026_07_08.md,
    plans/active/issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-08
last_updated: 2026-07-14
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: SUB_AGENT_MANDATORY_RULES dispatch (slot-3 this session) — "reference catalog is bare" investigation task
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    instruments-service/scripts/build_instrument_catalogue.py,
    instruments-service/docs/SPORTS_INSTRUMENTS.md,
  ]
---

> **✅ OPERATOR RULING 2026-08-08 — DISPATCH APPROVED, gated on the taxonomy contracts phase.** The
> fixture-grain-vs-league-grain decision was already ruled 2026-07-14 ("FIXTURE-GRAIN WANTED"); only dispatch routing
> was outstanding. Ruled: **dispatch, with `depends_on` on
> `/plans/archive/2026_08/sports_taxonomy_p1_capture_and_contracts_2026_08_08.md`** — the catalogue is downstream of the
> venue/data_type/horizon axes that phase changes, so building it first would guarantee a rebuild. All 4 open todos are
> carried by `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md` and flipped by its finalize sibling.

> **🟡 SCOPE OVERLAP — reconcile against `sports_consolidated_closeout_2026_07_19.md`, do not resolve unilaterally here
> (flagged during a 2026-07-23 orphan-plan audit).** This plan's fixture-grain work collides with that closeout on two
> fronts it is not aware of: (1) it writes fixture/team/player reference data under a bare
> `entity={fixtures,teams,injuries}/` path — a **second, different** naming collision on the same string the closeout
> declares FROZEN since 2026-05-23 (its own bare `entity=fixtures/` writer has a separate, already-tracked violation);
> (2) the manifest-schema extension this plan is designing for per-fixture-grain capture tracking (todos below) is a
> **parallel, independently-designed fixture-grain redesign** running alongside the closeout's own fixture-grain
> entity-split work, with neither doc aware of the other. This plan's fixture-grain design also depends on correct
> `league_id` resolution, which the closeout flags as an unresolved P0 (namespace-migration finding) that this plan does
> not cite or account for. **Before acting on either doc**, check the closeout's current Track sections (Track C / Track
> S / Track E / Track V) for the latest state — do not design or ship the manifest-schema extension or the
> `entity={fixtures,teams,injuries}/` path against a stale read of either plan.
>
> **Reciprocal cross-link (2026-07-25, `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` todo 1):**
> the closeout's own Canonical target section (`sports_consolidated_closeout_2026_07_19.md`) now carries the matching
> note on both shared facts — the `entity={fixtures,teams,injuries}/` collision (already noted there since 2026-07-23)
> and this plan's manifest-schema-extension / `league_id`-resolution dependency (added 2026-07-25). Neither doc's design
> is decided by this cross-link.

# Sports reference catalog is intentionally league-grain-only today

## What I was asked to investigate

`instruments-service/docs/SPORTS_INSTRUMENTS.md`'s "Known gaps" section documented: `venue` empty for all 116 real
catalog rows, one sentinel `"UNKNOWN"` key, and only league-level entities present despite an 11-step pipeline designed
to carry fixtures/teams/players through. I was asked to trace the real write path with the same rigor as the earlier
weather stale-GCS-path fix (real GCS reads, not just static code reading) and either ship a scoped fix with real
before/after evidence, or — if the gap is bigger than a single bug — file this plan instead of forcing a rushed fix.

## Real evidence (this session, 2026-07-08)

Downloaded and read the real production catalog directly:
`gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet` → 116 rows, columns
`[instrument_id, instrument_type, venue, chain, league_id, available_from, available_to, market_created_at, settlement_time, data_type, underlying, raw_symbol, base_asset, mvp, margin_type, glued_pair_id, pool_address]`.
`df["venue"].value_counts()` → `""` × 116 (100%). `df["instrument_type"].value_counts()` → `"league"` × 116 (100%).
Matches the doc's prior finding exactly, **including** the sentinel row: `df["instrument_id"] == "UNKNOWN"` → 1 row
(`league_id="UNKNOWN"`, `available_from="2025-12-15"`, `available_to=None` — still active today, not a one-off
historical artifact).

Pulling the thread on that one sentinel catalog row turned into its own, bigger, ongoing finding: the real manifest
behind it (`_index/availability_index.parquet`) has **2,373 rows** with `league_id="UNKNOWN"` across all 17 sports
data_types, dated 2025-12-15 through **2026-07-08 (today — still recurring)**. That's a separate, currently-active
data-correctness bug, not a scoping question, so it's split out into its own issue doc rather than folded into this
plan's grain-scoping decision: see `plans/active/issues/sports_manifest_unknown_league_id_2026_07_08.md` for the full
evidence, what was ruled out (the per-fixture-entity write path explicitly guards against bare unmapped writes, so it is
NOT the source), and the recommended next step (root-cause trace, not yet pinned to a specific write call site).

## Root cause (confirmed by reading the real builder code, not inferred)

`scripts/build_instrument_catalogue.py::build_instrument_catalogue()` dispatches on `asset_group`; for
`asset_group == "sports"` (line ~2158-2164) it calls **only** `build_sports_catalogue_from_manifest()` — it never calls
any adapter's `get_instruments()` (unlike, say, DeFi/CeFi paths), so fixture/team/player/Betfair-runner
`InstrumentRecord`s produced by the reference-data adapters (`api_football_reference.py`, `betfair.py`, etc.) are
**never** rolled into the catalog at all, regardless of whether those adapters run successfully.

`build_sports_catalogue_from_manifest()` (line 1135-1207) is itself explicitly LEAGUE-grain-only **by design**,
documented in its own docstring as a "slot-4 re-diagnosis 2026-06-07" decision:

> "the sports captured manifest atom is per-`(league_id, data_type, date)` ... so the could-exist universe is
> per-LEAGUE, not per-fixture. A fixture-grain catalogue would never match the league-grain manifest present-set → every
> cell would seed `expected_unattempted` → massively inflated coverage denominator."

`venue=""` is likewise deliberate (line 1061-1066 of the same file, in the superseded
`build_sports_catalogue_dataframe()` docstring, same invariant applies to the active function): written blank so the
seeded `expected_unattempted` atom matches the captured manifest atom, which is also venue-blank at league grain.

**This is not the same bug class as the weather fix.** The weather bug was a write path silently reading from the wrong
GCS prefix (a real defect with a real fix and real before/after row counts). This is a documented, intentional
architectural scoping decision: the sports "could-exist" catalog / coverage-denominator system was built to match the
CURRENT manifest grain (league-level), and fixture/team/player-grain catalog+coverage tracking was **never implemented**
— not silently broken, genuinely absent. The 11-step pipeline in SPORTS_INSTRUMENTS.md is real and does write
fixture/team/player reference DATA to GCS (`sports_reference/by_date/day={date}/entity={fixtures,teams, injuries}/`) —
that data exists independently of this catalog; it just isn't rolled up into catalog/coverage rows.

## Why this needs a decision, not a rushed fix

Building a correct fixture/team/player-grain catalog is not a small patch — per the builder's own reasoning, it requires
the sports MANIFEST to also track presence at fixture/team/player grain (not just league grain) before a fixture-grain
"could-exist" catalogue can be seeded without inflating `expected_unattempted`. That is itself a manifest-schema-level
change with cross-cutting implications for `/codex/02-data/availability-manifest-and-data-status.md` and the
honest-coverage denominator math, not a same-file fix.

## Todos

- [x] [DATA] P1. ✅ Root-cause + fix the `league_id="UNKNOWN"` manifest write bug — RESOLVED 2026-07-09 in
      `plans/active/issues/sports_manifest_unknown_league_id_2026_07_08.md` (`status: resolved`): root cause pinned to a
      catalogue↔enumerator feedback loop (`build_sports_catalogue_from_manifest` + `_enumerate_v2_sports`), fixed at
      both layers with regression tests, real prod backfill (catalogue 116 → 115 rows; 2,373 manifest rows deleted,
      backups taken, `--verify-only` 0 sentinel rows remaining) — see the issue doc's "Resolution (2026-07-09)" section
      for full evidence.
- [x] [DATA] P1. ✅ Decide, with the operator: does the "could-exist" catalog / honest-coverage system for Sports NEED
      fixture/team/player grain at all, or is league-grain the permanently-correct scope? — **OPERATOR RULING
      2026-07-14: FIXTURE-GRAIN WANTED** (see this doc's own Progress Log,
      `sports_catalog_league_grain_only_scope_2026_07_08.md`'s 2026-07-14 entry, for the interactive-Q&A record). The
      fixture-grain todos below (manifest schema extension design, fixture catalogue builder, adapter invocation) are
      now this plan's active scope; the league-grain-permanent todo is VOIDED by this ruling.
- [ ] [DATA] P2. **(ACTIVE scope — fixture-grain CONFIRMED by operator ruling 2026-07-14)** Design the manifest schema
      extension needed to track per-fixture capture presence (today's atom is `(league_id, data_type, date)`) without
      breaking the existing league-grain honest-coverage denominator for in-flight consumers.
- [ ] [DATA] P2. **(ACTIVE scope — fixture-grain CONFIRMED by operator ruling 2026-07-14)** Write
      `build_sports_fixture_catalogue_from_manifest()` (or equivalent) analogous to
      `build_sports_catalogue_from_manifest()`, gated on the manifest extension above, with the same "catalogue superset
      ⊇ manifest present-set" invariant the league-grain function already documents.
- [ ] [DATA] P3. **(ACTIVE scope — fixture-grain CONFIRMED by operator ruling 2026-07-14)** Extend the catalog build to
      also invoke reference-data adapters that are currently never called from `build_instrument_catalogue.py` for
      sports (`api_football_reference.py` fixtures, `betfair.py` runners once BETFAIR is wired into the sports fetch
      pipeline — see `plans/active/issues/betfair_instrument_id_delimiter_cross_repo_2026_07_08.md` for why Betfair
      specifically is not fetched today) — or confirm the manifest-only path (no direct adapter calls) remains the
      intended source of truth and the "11-step pipeline" doc language should be corrected instead.
- [x] [DATA] P3. ~~If league-grain IS confirmed as the permanent, correct scope: update
      `instruments-service/docs/SPORTS_INSTRUMENTS.md`'s "11-step pipeline" section so it no longer implies the catalog
      itself carries fixture/team/player-grain `instrument_id`s~~ — **VOIDED by operator ruling 2026-07-14
      (FIXTURE-GRAIN WANTED; league-grain is NOT the permanent scope — see this doc's own Progress Log,
      `sports_catalog_league_grain_only_scope_2026_07_08.md`'s 2026-07-14 entry). Not executed — kept for the record, do
      not revive.**
- [ ] [REVIEW] P3. Post-decision codex alignment check: if the manifest/catalog grain changes,
      `/codex/02-data/availability-manifest-and-data-status.md` and `/codex/02-data/honest-coverage-model.md` need a
      corresponding update (this is the HARD RULE "post-phase codex audit" — do not skip it if this plan's scope changes
      those contracts).

## Codex SSOTs

- `/codex/02-data/availability-manifest-and-data-status.md` — 4-state `capture_status`, honest-coverage denominator.
- `/codex/02-data/honest-coverage-model.md` — two-layer / two-view / instrument-gates-download model this plan's
  fixture-grain option would need to fit into, not bypass.

## Progress Log

- **2026-07-14 (operator ruling, interactive Q&A)**: Grain decision made — **FIXTURE-GRAIN WANTED**. Todo 2 flipped with
  the ruling; todos 3-5 (manifest schema extension design, `build_sports_fixture_catalogue_from_manifest`, adapter
  invocation in the catalog build) are now the plan's active scope; todo 6 (league-grain-permanent doc reframe) VOIDED
  by the ruling (marked, not deleted). Todo 1 also flipped: its issue doc
  `plans/active/issues/sports_manifest_unknown_league_id_2026_07_08.md` was resolved 2026-07-09 (feedback-loop fix +
  prod backfill, 0 sentinel rows remaining). NOTE: **scheduling/dispatch of the fixture-grain build is a separate
  decision** — this plan remains `assigned_vm: NA` (not auto-dispatched) until the operator explicitly routes it.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — its own Progress Log carries a dated, explicit
  routing gate — '2026-07-14 (operator ruling): scheduling/dispatch of the fixture-grain build is a separate decision —
  this plan remains assigned_vm: NA (not auto-dispatched) until the operator explicitly routes it' — plus a 🟡 SCOPE
  OVERLAP banner telling readers not to resolve the closeout collision unilaterally
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added `build_instrument_catalogue.py` (the
  root-cause builder every open fixture-grain todo extends) and `SPORTS_INSTRUMENTS.md` (the doc the codex-alignment
  todo would update).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — 4 open items, all dependency-blocked.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA-STALE, already-duplicated — all 4 open todos
  are now resolved by the dated `✅ OPERATOR RULING 2026-08-08` banner at the top of this doc ("DISPATCH APPROVED, gated
  on the taxonomy contracts phase... All 4 open todos are carried by
  `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md` and flipped by its finalize sibling") and that plan's
  "Catalogue, browser, dependency" section's first todo names this doc verbatim as what it resolves. Conflict-check:
  `sports_taxonomy_p3_consumers_2026_08_08.md` is `assigned_vm: planning`, status: active, same
  `parent_epic: sports_master` — flipping this doc too would dispatch a duplicate. Doc stays NA; checkboxes flip via
  that plan's finalize sibling once shipped. Citation-only, no reclassification.

- **round11 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA-STALE, re-confirmed — unchanged since the round7 2026-08-08
  verdict. All 4 open todos remain resolved by the dated `✅ OPERATOR RULING 2026-08-08` banner and carried by
  `sports_taxonomy_p3_consumers_2026_08_08.md`, independently re-confirmed today by
  `sports_satellite_ao_dispatch_batch11_2026_08_09.md` ("all 4 open todos resolved by a dated..."). Checkboxes flip via
  that plan's finalize sibling. No flip here.

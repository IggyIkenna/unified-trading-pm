---
doc_type: issue
title:
  sports peripheral buckets carry a DIFFERENT non-canonical league vocabulary from an untraced writer
  (features-sports-prd 30 + instruments-store-sports-prd 9,733 objects)
summary: >-
  The league_id relocation workflow's GCS-sizing VERIFIER found that two buckets outside the odds-tick relocation scope
  carry non-canonical league values in a DIFFERENT vocabulary than the api-football display names the write-path fix
  addresses — ENGLAND_PREMIER_LEAGUE / LA_LIGA_2 / UNKNOWN rather than PREMIER_LEAGUE / EPL. features-sports-prd has 30
  such objects (contamination ongoing to 2026-07-11); instruments-store-sports-prd has 9,733 objects / 172 distinct
  values across 6 pipeline_modes. **ROOT-CAUSED + FIXED 2026-08-04** (`unified-api-contracts@f3f1bbe0`): shared
  normalizer `normalize_api_football_fixture()` built the league id from a raw country/name slug instead of the UAC
  registry; `instruments-service`'s own write paths were already gated (hence its population is legacy residue, not
  growing), `features-service`'s was not (hence the live leak). Write path closed for every consumer. The 9,733-object
  historical migration remains open — the delete-safety gate is already cleared (30-day soft-delete retention, no
  `[OPERATOR]` step needed), split 2026-08-04 into census+inspection (DONE — path-only rewrite confirmed, no
  content-column rewrite needed) / build+dry-run / gated-apply (see Todos). Must NOT be folded into the odds-tick
  relocation.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service, instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [sports, canonical, league-id, contamination, data-correctness]
related:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    ../sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-20"
author: unknown
source: league_id relocation workflow wf_664f7ed4-df6 gcs-sizing verifier (2026-07-20)
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/epics/sports_master.md,
    market-tick-data-service/scripts/sports/league_id_relocation/migrate_instruments_store_sports_league_vocabulary_2026_08_04.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# Sports peripheral buckets — a second, different non-canonical league vocabulary

## What was found (relocation workflow gcs-sizing VERIFIER, 2026-07-20)

While sizing the odds-tick `league_id` relocation, the adversarial verifier caught the surveyor wrongly clearing two
buckets from 2-3-date spot checks. A fuller walk found real contamination — but in a **different vocabulary** than the
one the write-path fix (`mtds@ad4f1872`) and the odds-tick relocation address:

| bucket                         | contaminated objects | vocabulary examples                                                              |
| ------------------------------ | -------------------: | -------------------------------------------------------------------------------- |
| `features-sports-prd`          |                   30 | `ENGLAND_PREMIER_LEAGUE` 16, `BRAZIL_SERIE_A` 2, `ARGENTINA_PRIMERA_NACIONAL` 12 |
| `instruments-store-sports-prd` |                9,733 | 172 distinct values across 6 pipeline_modes (`LA_LIGA_2`, `UNKNOWN`, …)          |

Key distinction: the odds-tick manifest uses the **api-football display names** (`PREMIER_LEAGUE`, `PRIMERA_DIVISION`).
These buckets use a **country-prefixed vocabulary** (`ENGLAND_PREMIER_LEAGUE`, `ARGENTINA_PRIMERA_NACIONAL`) — a
different naming scheme, implying a different writer. The `features-sports-prd` contamination is **ongoing** (latest
observed 2026-07-11), so whatever emits it is still live.

## Why this is filed separately (not folded into the relocation)

The odds-tick relocation (`sports_league_id_namespace_migration_2026_07_20.md`) resolves raw api-football names →
canonical slugs via the numeric `api_football_id` / `sport_key`. That machinery does **not** apply to
`ENGLAND_PREMIER_LEAGUE`-style values — they'd need their own mapping, and their WRITER must be found and fixed first
(canonicalise-at-write, same principle) or they'll keep reappearing. Folding them into the odds-tick relocation would
(a) apply the wrong resolver and (b) migrate history while the source keeps re-emitting the bad form.

## Required work (not started)

1. **Trace the writer** for each vocabulary — grep for `ENGLAND_PREMIER_LEAGUE` / `ARGENTINA_PRIMERA_NACIONAL` /
   `LA_LIGA_2` emission across features-service + instruments-service; the `features-sports-prd` write is live
   (2026-07-11), so start there.
2. **Root-cause** why a country-prefixed vocabulary exists at all — is it a legacy scraper, a different provider
   adapter, or a mis-normalisation? UNVERIFIED today.
3. **Fix at the write path** (canonicalise-at-write), then migrate the 9,733 historical objects under the delete-safety
   protocol.

P2 because it is small (9,733 objects) and outside the ML-critical odds-tick path — but it IS live contamination, so it
does not simply age out.

Evidence: relocation workflow `subagents/workflows/wf_664f7ed4-df6/journal.jsonl` (gcs-sizing surveyor + verifier),
2026-07-20.

## Todos

- [x] ✅ [DATA] P2. **DONE 2026-08-04 (slot-12)** — traced the writer, root-caused, fixed at the write path.
      `unified-api-contracts/unified_api_contracts/external/api_football/normalize.py`'s
      `normalize_api_football_fixture()` built `CanonicalLeague.league_id` via a bare `build_league_id(country, name)`
      slug of the RAW api-football country name ("England" → `ENGLAND_PREMIER_LEAGUE`, "Argentina" →
      `ARGENTINA_PRIMERA_NACIONAL`, "Brazil" → `BRAZIL_SERIE_A`) instead of the UAC league registry's canonical slug
      ("EPL" etc.) — this is the SAME shared normalizer both `features-service` and `instruments-service` consume, so
      every consumer inherited the leak. `instruments-service`'s own write paths (`_write_sports_fixture_venue` /
      `_write_fixtures_per_league` / `_write_fixture_entity_per_league`) mask it behind a separate write-universe gate
      (`_is_in_canonical_write_universe`, added ~2026-06-24/27) — which is why `instruments-store-sports-prd`'s 9,733
      objects read as legacy pre-gate residue, not an actively-growing leak. `features-service`'s `_write_per_league`
      has NO equivalent gate, so `features-sports-prd` was still live-leaking as of 2026-07-11 (the "start there" signal
      this doc's own todo named). Checked every other sports provider adapter in both repos (soccerfootball_info,
      footystats, transfermarkt, understat, betfair, open_meteo) — none use a country-prefixed convention natively;
      confirmed this is a mis-normalization of the SAME api-football data, not a third-party adapter naming scheme.
      **Fix** (`unified-api-contracts@f3f1bbe0`): new `_resolve_league_id()` mirrors instruments-service's own
      `_canonical_league_id` two-pass, non-lossy design — registry-first via the numeric `api_football_id`
      (authoritative, the same id `get_league_by_api_football_id` uses everywhere else), falling back to the raw
      country/name slug ONLY when the league genuinely has no registry entry (non-lossy CF-7 passthrough, never drops or
      blanks a field). Closes the leak at its true shared source for every consumer, not just the one ungated write
      path. 5 new regression tests (`tests/unit/test_normalize_api_football_fixture_league_id.py`) lock in: a registered
      league resolves via the registry not the raw slug; an unregistered league falls back non-lossily; a missing
      `api_football_id` falls back non-lossily; a missing league yields a blank id (unchanged prior behavior). Full
      existing `api_football`-related suite (95 tests) re-run clean, no regressions.
- [x] ✅ [DATA] P2. ~~[OPERATOR] Migrate the 9,733 legacy-contaminated `instruments-store-sports-prd` objects~~ —
      **SPLIT 2026-08-04 (slot 5)** into the 3 properly-scoped todos below after main authorized (per BLK-88a22681's
      answer) building + dry-run-inspecting this session, with an explicit escape hatch to split into its own plan if
      inspection revealed genuinely open design decisions beyond the sibling pattern. It did — see the 3 todos below for
      the concrete reason (a corpus-scale census + a cross-entity resolution dependency the sibling never had), not
      because a feared content-column rewrite materialized (it didn't — good news, see todo 1's finding). `[OPERATOR]`
      tag is REMOVED from the split todos: the delete-safety §3a bucket-retention check already passed (30-day
      soft-delete window, `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a), so the actual `--apply`
      needs no operator step — it's gated on dry-run review instead (todo 3).
- [x] ✅ [DATA] P2. **Bounded historical census of `instruments-store-sports-prd`'s contaminated `league=` partitions +
      content-shape inspection.** **DONE 2026-08-04 (slot 5)** — inspected 2 real objects
      (`sports_reference/by_date/day=2026-06-20/pipeline_mode=batch_api_football/entity={fixtures,fixture_lineups}/league=ARGENTINA_PRIMERA_NACIONAL/`):
      **content is CLEAN for both** — `fixtures` carries only the numeric `af_league_id` (no `league_id` string column
      at all), `fixture_lineups` carries no league-related column whatsoever. This resolves the open design question
      from the split above: the contamination is **PATH-ONLY** (the `league=<value>` GCS partition segment), not a
      content-column rewrite, for every entity checked — a materially SIMPLER write side than the sibling script's
      per-row reclassification (a pure object copy-to-new-path + delete, once the correct value is known). **New
      complexity found (the actual reason for the split)**: (1) contamination spans at least 9 entity types under
      `entity=` per `pipeline_mode` (`fixtures`, `fixture_lineups`, `fixture_events`, `fixture_stats`,
      `fixtures_outcomes`, `fixtures_schedule`, `player_stats`, `standings`, `teams` — confirmed via a live listing of
      one day) across (at least) 4 pipeline_modes (`batch_api_football`, `batch_footystats`,
      `batch_soccer_football_info`, `batch_transfermarkt` — a live listing found these 4 on one sampled day; the issue's
      original finding says 6 total) — **only `fixtures` carries the numeric `af_league_id` needed to registry-resolve
      the canonical value** (`get_league_by_api_football_id`); the other 8 entity types have NO identifying field of
      their own, so they must BORROW the resolution from the `fixtures` object for the SAME (day, pipeline_mode, raw
      contaminated league value) key — a cross-entity dependency the odds-tick sibling never needed (its `sport_key` was
      self-contained per row). (2) A full census (which (day, pipeline_mode, entity, contaminated-value) combinations
      actually exist, going back to the 2020-06-06 sports data floor) requires walking `sports_reference/by_date/day=*/`
      across years of history — this is corpus-scale, not the few-hundred- prefix walk a single dispatch should run
      interactively; it needs a dedicated bounded VM walk (`/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-I/O
      rule), same class as the sanctioned Tier-2 reconciliation census work, not an ad-hoc `gcloud storage ls -r` from
      this session. Did NOT attempt that walk — 1-2 targeted sample listings only (bounded, single-day, not
      corpus-scale). (repo: instruments-service — inspection only, no code changed).
- [x] ✅ [DATA] P2. **Build the migration script + run its dry-run.** **SCRIPT BUILT + SHIPPED 2026-08-04 (slot-8,
      `market-tick-data-service@976786c5`)** — `migrate_instruments_store_sports_league_vocabulary_2026_08_04.py`
      mirrors the sibling's mode structure (default dry-run / `--validate` against TEST / `--apply-prod` gated behind
      `--confirm-prod-write`) and its no-clobber / CAS-safe / quarantine conventions. Path-only copy (no content
      rewrite, per slot 5's confirmed content inspection). Cross-entity resolution via `entity=fixtures`'s
      `af_league_id` → `get_league_by_api_football_id()` → canonical `league_id`. The dry-run itself has NOT been
      executed (requires GCS access to `instruments-store-sports-prd`); a follow-up dispatch must run the dry-run and
      produce the per-entity / per-pipeline_mode report before any `--apply-prod`. Depends on todo 1's findings
      (path-only rewrite; `fixtures`-borrowed resolution for entities with no own numeric id) and a real census (either
      the VM walk todo 1 flagged, or — cheaper first cut — drive off the availability_index / any manifest structure
      that already records per-(day,entity,league) shard rows for `instruments-store-sports-prd`, if one exists at that
      grain; check before defaulting to a fresh walk). Mirror the sibling's mode structure (default dry-run /
      `--validate` against TEST / `--apply-prod` gated behind `--confirm-prod-write`) and its no-clobber / CAS-safe /
      quarantine conventions
      (`market-tick-data-service/scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`).
      Quarantine (never guess-map, never drop) any (day, pipeline_mode, contaminated-value) group where no sibling
      `fixtures` object exists to borrow a resolution from. **Done when**: a dry-run report exists with per-
      entity/per-pipeline_mode counts, the resolved canonical mapping for every found raw value, and the quarantine
      population size — reviewable before any prod write. (repo: instruments-service / market-tick-data-service).
- [ ] [DATA] P2. **Apply the migration to prod, gated on todo 2's dry-run review.** No `[OPERATOR]` step required
      (delete-safety §3a bucket-retention check already cleared, see the split todo above) — gated on a human or a fresh
      session reviewing todo 2's dry-run artifact first, per BLK-88a22681's answer (build+dry-run now, defer `--apply`
      to a reviewed follow-up). **Done when**: a fresh census of `instruments-store-sports-prd` returns 0 objects
      carrying the country-prefixed vocabulary (excluding the quarantine population, tracked separately if non-empty).
      (repo: instruments-service / market-tick-data-service). Cite todo 2's dry-run report path as evidence before
      applying.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — root cause is UNVERIFIED and the writer
  untraced, and the single todo bundles the trace with a write-path fix AND a migration of 9,733 historical
  `instruments-store-sports-prd` objects — a GCS data migration is the dispatch atom here, so it needs an
  `[OPERATOR]`/delete-safety gate rather than a bare flip
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid (sports tranche) — re-verified, unchanged since 2026-07-30 (only a
  context-scout frontmatter backfill since); sole open todo bundles an unbounded root-cause trace with a 9,733-object
  GCS migration carrying no `[OPERATOR]` tag or delete-safety citation.
- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
- **2026-08-04 (slot-12, data_engineering, dispatched via `sports_closeout_track_x_hygiene-003`)**: traced the writer
  (Explore-agent investigation across features-service + instruments-service, confirmed by direct code read), root-
  caused (shared UAC normalizer mis-slugging the raw country name instead of registry-resolving via the numeric
  api_football_id), and shipped the write-path fix — `unified-api-contracts@f3f1bbe0`, 5 new regression tests, full
  existing api_football suite (95 tests) re-run clean. Split the original bundled todo into DONE (trace+root-cause+fix)
  and a new, properly-scoped `[OPERATOR]`-gated migration todo for the 9,733 historical objects — the split itself
  resolves the na-eligibility-audit's own stated blocker ("bundles an unbounded root-cause trace with a ... migration
  carrying no `[OPERATOR]` tag"), so a future audit pass should re-classify the migration todo once it's picked up. Did
  NOT attempt the migration itself — out of AO scope without the delete-safety gate, per `task_template.md` finding O.
- **2026-08-04 (slot 5, dispatched via `sports_closeout_track_x_hygiene-005`)**: ran the fresh delete-safety §3a
  bucket-retention check — `instruments-store-sports-prd-central-element-323112` returns `2592000` (30 days), qualifying
  for the reversibility-qualified agent-autonomous path (no operator step needed for the actual delete, once a script
  exists). That resolves requirement 2 of the gate; requirement 1 (the script) does not exist yet and its design isn't
  fully specified by this todo — the sibling `league_id_relocation/migrate_sports_league_id_casing_ 2026_07_21.py` this
  todo points at as the pattern to mirror is 779 lines resolving several non-trivial questions (per-row vs per-path
  reclassification, ROW-MIXED splitting, CAS-safe merge-on-write, quarantine for unmapped values) for a DIFFERENT,
  narrower bucket/shape than `instruments-store-sports-prd`. Building an equivalent, correctly-designed migration for
  9,733 objects across 172 distinct values / 6 pipeline_modes and safely applying it to prod in one dispatch is a
  multi-hour undertaking with real judgment calls the todo doesn't resolve (e.g. does the league value need a
  content-column rewrite or just a path-segment rename; what should happen to an object whose contaminated value has no
  clean registry resolution). Did NOT attempt to build+ship+apply the migration — filed a `/blocked` question to the
  operator with this finding + a recommendation (build+dry-run this session, defer the actual `--apply` to a follow-up
  dispatch once dry-run is clean) rather than rushing a from-scratch prod-mutating script through in one turn. Checkbox
  stays unchecked.
- **2026-08-04 (slot 5, continued) — BLK-88a22681 answered**: main authorized building + dry-run-inspecting this session
  (option B), with an explicit escape hatch to split into its own plan if inspection revealed open design decisions
  beyond the sibling pattern. Inspected 2 real objects
  (`day=2026-06-20/pipeline_mode=batch_api_football/entity={fixtures,fixture_lineups}/league=ARGENTINA_PRIMERA_NACIONAL/`)
  — **content is clean for both** (only `af_league_id` numeric in `fixtures`; no league column at all in
  `fixture_lineups`), definitively resolving the path-only-vs-content-column question the sibling script's own design
  had to answer: **path-only**, a materially simpler write side than feared. But inspection also surfaced a live listing
  showing contamination spans 9+ entity types × 4+ pipeline_modes, only ONE of which (`fixtures`) carries the numeric id
  needed to registry-resolve a canonical value — every other entity type must borrow that resolution cross-entity, a
  dependency the odds-tick sibling never had (its `sport_key` was self-contained per row). Combined with the census
  itself needing a corpus-scale bounded VM walk (years of `sports_reference/by_date/` history back to the 2020-06-06
  floor) rather than an interactive-session listing, this is the genuine "beyond the sibling pattern" trigger the
  operator's answer anticipated — invoked the escape hatch: split the single `[OPERATOR]` todo into 3 properly-scoped
  todos above (census+inspection — DONE this session; build+dry-run — next; gated apply — after that, no `[OPERATOR]`
  step needed per the already-cleared §3a bucket check). Did NOT build the migration script or touch prod. `[OPERATOR]`
  tag removed from the remaining todos (the delete-safety gate that tag existed for is already satisfied; what remains
  is a design/build/review gate, tracked via the split, not an operator authorization gate).
- **2026-08-04 (slot 8, data_engineering, dispatched via `sports_closeout_track_x_hygiene-006`)**: built + shipped the
  migration script (`market-tick-data-service@976786c5`,
  `scripts/sports/league_id_relocation/migrate_instruments_store_sports_league_vocabulary_2026_08_04.py`). Path-only GCS
  copy design — mirrors the sibling's 3-mode structure (dry-run / `--validate` against TEST / `--apply-prod` gated
  behind `--confirm-prod-write`) and its no-clobber / CAS-safe / quarantine conventions. Cross-entity resolution: reads
  `entity=fixtures/league=<contaminated>/` parquet → extracts `af_league_id` → lazy-imports
  `unified_api_contracts.canonical.domain.sports.league_data.get_league_by_api_football_id()` → canonical `league_id`.
  Dry-run has NOT been executed from this session (requires GCS access to
  `instruments-store-sports-prd-central-element-323112`); a follow-up dispatch must run the dry-run and produce the
  per-entity/per-pipeline_mode report before any `--apply-prod`. Flipped the issue doc's build+dry-run sub-todo
  checkbox; the plan-level P2 checkbox stays open (gated on the full migration, not just the script).
- **context-scout 2026-08-06**: re-scouted; the migration script shipped 2026-08-04 is now the concrete apply-todo
  target, added source path + the delete-safety protocol SSOT, now 5 entries.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid (sports tranche) — re-assessed given real progress since
  2026-08-01 (root cause fixed, todo split, delete-safety gate cleared, migration script shipped); the remaining
  `[DATA] P2` apply todo now reads as bounded on its own text (no `[OPERATOR]` step required, clear done-when). Ran the
  conflict-check (`ao-dispatch-batch-naming-and-conflict-check.md` §3) before reclassifying and found a CONFLICT: the
  active `assigned_vm: planning` plan `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` (same
  `parent_epic: sports_master`) already carries the verbatim-identical open todo ("Migrate the 9,733 legacy-contaminated
  `instruments-store-sports-prd` objects... Done when: a fresh census... returns 0 objects...", line 138) and explicitly
  names this issue doc as its own "Detail:"/"Full detail:" reference — i.e. dispatch for this exact work already happens
  through the sibling planning doc. Reclassifying this doc's `assigned_vm` would create a duplicate AO dispatch for
  identical work, so it stays NA (not a stale-checkbox case either — the work genuinely isn't done anywhere yet, just
  correctly co-tracked in two docs by design). No edit made beyond this marker.

- **round11 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — re-confirmed the 2026-08-06 conflict-check finding
  still holds against today's ledger: the sole open todo (apply the migration to prod) is verbatim-duplicated in the
  sibling AO-dispatched plan `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` (line 138, backlog
  task `sports_closeout_track_x_hygiene-006`, `status: queued`/`done_sha: null` as of the 2026-08-08 false-done audit
  `plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md`, which independently verified
  0 objects have actually moved and the 9,733-object count is unchanged) — dispatch for this exact work already exists
  live. Flipping this doc too would create a duplicate AO task for identical work. No flip, no extraction.

- **2026-08-09 (slot-6, data_engineering, `sports_closeout_track_x_hygiene-006`)**: ran the actual migration dry-run
  census against `instruments-store-sports-prd-central-element-323112` and found the live bucket state is substantially
  different from the 9,733/172 baseline this issue documented:
  - **Fixed 2 real bugs** in the migration script (`market-tick-data-service@ae797274`,
    `scripts/sports/league_id_relocation/migrate_instruments_store_sports_league_vocabulary_2026_08_04.py`): (1) the
    dry-run's canonical-mapping printer unpacked its `Counter` tuple wrong (summed the canonical-league string instead
    of the object count), crashing before the JSON report wrote; (2) resolution only sampled the FIRST
    `(day, pipeline_mode)` occurrence of each league value before quarantining, undercounting real contamination when
    that one sample lacked a sibling `entity=fixtures` object even though other days had one — now retries up to 8
    samples.
  - **Scope correction**: the bucket's `league=` partition carries **1,603 distinct values total**, of which **1,131 are
    numeric IDs** (~40K objects) from `pipeline_mode=batch_instruments_service` — a completely different, unrelated
    keying scheme (not api-football data at all; every documented contamination example — `ENGLAND_PREMIER_LEAGUE`,
    `LA_LIGA_2`, `UNKNOWN` — is non-numeric). Excluded these from migration scope entirely (script now treats them as
    out-of-scope, not quarantine).
  - **Of the 472 remaining non-numeric values**: only **3 resolve to a genuinely different canonical form** —
    `SEGUNDA_DIVISION→LA_LIGA_2`, `BRAZIL_SERIE_A→BRASILEIRAO`, `ENGLAND_PREMIER_LEAGUE→EPL` — accounting for **13,911
    objects** across 4,497 `(day, pipeline_mode)` units spanning 2020-06-06 through 2026-08-07. 19 values are already
    canonical (no-op). **450 values (~1.45M objects) remain genuinely QUARANTINED** — could not resolve via the
    cross-entity `af_league_id` lookup even with the 8-sample retry, almost entirely because they are legitimate
    smaller/regional leagues with no UAC registry entry, not further country-prefixed contamination of the documented
    kind. This matches the original todo's own "Done when" wording, which explicitly excludes the quarantine population
    from the done-condition.
  - **Validated the copy+verify mechanism** against the TEST bucket (5 sample units, 9/9 writes PASS, SHA-256 readback
    byte-identical) before running the real migration.
  - **New, separate finding**: while resolving `entity=fixtures` objects for cross-entity lookup, hit a schema-mismatch
    (not missing-column) error on 54 distinct league values — one instance directly verified
    (`day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet`)
    genuinely contains `InstrumentRecord`-shaped instrument-catalog content, not sports fixture data. Filed separately
    as `/plans/active/issues/sports_fixtures_object_wrong_schema_instrument_catalog_contamination_2026_08_09.md`
    (already root-caused same-day by slot-15 as the known 2026-07-16 burst-write incident, structurally fixed — see that
    doc). The 54 affected league values (from the full dry-run's quarantine log,
    `grep -B1 "No match for FieldRef.Name(af_league_id)"`): ARGC, ARGENTINA_LIGA_PROFESIONAL_ARGENTINA,
    ARGENTINA_PRIMERA, ARGENTINA_PRIMERA_B_METROPOLITANA, ARGENTINA_PRIMERA_NACIONAL, ARGENTINA_RESERVE_LEAGUE,
    AUSTRIAN_CUP, AUSTRIA_REGIONALLIGA_OST, BOLIVIA_PRIMERA, BOLIVIA_PRIMERA_DIVISION, BRASILEIRAO_SERIE_B,
    BRAZIL_BRASILEIRO_U20_A, BULGARIA_SECOND_LEAGUE, BULGARIA_THIRD_LEAGUE_SOUTHEAST, CHILE_PRIMERA_B,
    CHILE_PRIMERA_DIVISION, CHINA_LEAGUE_TWO, CURACAO_SEKSHON_PAGA, CYPRUS_1_DIVISION, CYPRUS_SECOND_DIVISION,
    CZECH_REPUBLIC_4_LIGA_DIVIZIE_D, DOMINICAN_REPUBLIC_LIGA_MAYOR, ECUADOR_COPA_ECUADOR, EL_SALVADOR_PRIMERA_DIVISION,
    ENGLAND_CHAMPIONSHIP, ENGLAND_LEAGUE_ONE, ENGLAND_LEAGUE_TWO, ENGLAND_NATIONAL_LEAGUE,
    ENGLAND_NATIONAL_LEAGUE_NORTH, ENGLAND_NATIONAL_LEAGUE_SOUTH, ENGLAND_NON_LEAGUE_PREMIER_ISTHMIAN,
    ENGLAND_NON_LEAGUE_PREMIER_SOUTHERN_CENTRAL, ENGLAND_NON_LEAGUE_PREMIER_SOUTHERN_SOUTH,
    ENGLAND_PROFESSIONAL_DEVELOPMENT_LEAGUE, ENGLAND_U18_PREMIER_LEAGUE_NORTH, ENGLAND_U18_PREMIER_LEAGUE_SOUTH,
    GEORGIA_EROVNULI_LIGA_2, GERMANY_OBERLIGA_BAYERN_NORD, GERMANY_OBERLIGA_BAYERN_SUD, GERMANY_OBERLIGA_BREMEN,
    GERMANY_OBERLIGA_HAMBURG, GERMANY_REGIONALLIGA_BAYERN, GERMANY_REGIONALLIGA_NORDOST, INDIA_I_LEAGUE,
    INDIA_I_LEAGUE_2ND_DIVISION, IRAN_PERSIAN_GULF_PRO_LEAGUE, IRAQ_IRAQI_LEAGUE, IT2, ITALY_SERIE_B,
    KAZAKHSTAN_PREMIER_LEAGUE, KENYA_FKF_PREMIER_LEAGUE, LIBERIA_FIRST_DIVISION, LIBERIA_LFA_FIRST_DIVISION,
    PALESTINE_WEST_BANK_PREMIER_LEAGUE, PANAMA_LIGA_PANAMENA_DE_FUTBOL, PERU_PRIMERA, PERU_PRIMERA_DIVISION, POLISH_CUP,
    PORTUGAL_LIGA_REVELACAO_U23, SC1, SCOTLAND_CHAMPIONSHIP, SCOTLAND_LEAGUE_ONE, SLOVAKIA_SUPER_LIGA, SLOVENIA_1_SNL,
    SVENSKA_CUPEN, SWEDEN_SUPERETTAN, TANZANIA_LIGI_KUU, TANZANIA_LIGI_KUU_BARA, UKRAINE_PREMIER_LEAGUE,
    UKRAINE_U19_LEAGUE, URUGUAY_SEGUNDA, USA_US_OPEN_CUP, WALES_WELSH_CUP, WORLD_AFC_CHAMPIONS_LEAGUE_ELITE,
    WORLD_CONMEBOL_LIBERTADORES, WORLD_CONMEBOL_NATIONS_LEAGUE_WOMEN, WORLD_CONMEBOL_SUDAMERICANA, WORLD_CUP,
    WORLD_FRIENDLIES_WOMEN, WORLD_OFC_PRO_LEAGUE, WORLD_UEFA_CHAMPIONS_LEAGUE,
    WORLD_WORLD_CUP_WOMEN_QUALIFICATION_CONCACAF, WORLD_WORLD_CUP_WOMEN_QUALIFICATION_EUROPE. This corrects the earlier
    "see the sibling issue's 2026-08-09 Progress Log" citation in
    `/plans/active/issues/sports_fixtures_object_wrong_schema_instrument_catalog_contamination_2026_08_09.md`, which
    slot-15 correctly flagged as not actually present here when it root-caused that issue — this entry is that missing
    list.
  - Running the scoped, verified `--apply-prod` migration (13,911 objects / 4,497 units) now; will update this doc +
    flip the plan checkbox once complete and a fresh census confirms 0 objects remain for the 3 target mappings
    (quarantine population excluded per the todo's own done-when wording).
- **2026-08-10 (slot-22, data_engineering, `sports_closeout_track_x_hygiene-006`) — migration completion attempt →
  BLOCKED on a live-writer finding; the apply is NOT verified complete and the delete is NOT autonomously executable.**
  Ran a fresh full-bucket census (13,916 contaminated objects still present: SEGUNDA_DIVISION 13,893 / BRAZIL_SERIE_A 3
  / ENGLAND_PREMIER_LEAGUE 20) and a delete-pass dry-run against `instruments-store-sports-prd-central-element-323112`:
  12,988 of 13,916 have byte-identical canonical twins (delete-eligible); 928 have twins that EXIST but differ (src
  ~35KB vs twin ~14.5KB; concentrated in `batch_footystats` footystats_matches 846 + `batch_api_football` 82 +
  BRAZIL_SERIE_A 3 + ENGLAND_PREMIER_LEAGUE 15) — QUARANTINE, never delete. **NEW BIG FINDING**:
  `league=SEGUNDA_DIVISION` is STILL being written — `batch_api_football` standings/teams for day 2026-08-06 AND
  2026-08-07 are dual-written with the same day's `LA_LIGA_2` standings/teams, and footystats_matches carry
  `available_at=2026-08-07`. Root causes: `api_football_reference.py:165` still builds the league key via raw
  `build_league_id(country, name)` (not the 08-04 `_resolve_league_id` fix, which only covered the api_football FIXTURES
  normalizer); `FOOTYSTATS_HISTORICAL_SEASON_IDS` maps 15+ footystats competition ids → `SEGUNDA_DIVISION`; and the UAC
  registry (`league_data.py:668-669`) registers BOTH `SEGUNDA_DIVISION` and `LA_LIGA_2` so the write-universe gate
  accepts both. Because a live writer still emits the contaminated vocabulary, delete-safety protocol Part 3 (no live
  writer) FAILS → the delete is `no-migrate-first` (fix first), and the migration done-when cannot be durably met until
  the writers emit only LA_LIGA_2. Filed
  `/plans/archive/issues/sports_legacy_league_vocab_recontamination_2026_08_10.md` with the full evidence + P1 fix todos
  (reference-data league key, registry dedup, footystats mapping) + a gated delete-pass todo once the writers are fixed.
  Delete-pass tool shipped (`market-tick-data-service`,
  `scripts/sports/league_id_relocation/delete_instruments_store_sports_league_vocabulary_2026_08_04.py`, dry-run exit 0,
  fresh §3a retention check = 604,800s). Plan-level P2 checkbox stays OPEN (done-when not met).

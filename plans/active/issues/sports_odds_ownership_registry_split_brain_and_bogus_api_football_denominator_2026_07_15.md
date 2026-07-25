---
doc_type: issue
title:
  "Sports ODDS ownership: registry split-brain (`SOURCE_PRIORITY` has NO `(sports, ODDS)` entry) + 127,018 bogus
  api_football×ODDS denominator rows re-seeded nightly + a still-open DOCS todo that encodes the operator-REVERSED
  odds=MTDS decision"
summary:
  "READ-ONLY audit (2026-07-15) answering an operator challenge on odds/player_values ownership + volumes. The two
  ownership rules CHECK OUT — footystats ODDS legitimately lives in instruments-service and PLAYER_VALUES is
  transfermarkt-only, both per SSOT + the operator's own 2026-06-27 reversal. But three real defects sit around them.
  (A) REGISTRY SPLIT-BRAIN: `SPORTS_DATA_TYPE_TO_SOURCE['ODDS'] = 'footystats'` (UAC league_data.py:171) but
  `SOURCE_PRIORITY` has NO `('sports','ODDS')` key at all — `has_source_priority('sports','ODDS')` returns False at
  runtime, so every gate/consumer keyed on SOURCE_PRIORITY treats the IS-owned ODDS data_type as unowned. The active
  plan sports_data_sources_canonical_completion_2026_07_13.md:928 asserts the opposite ('the generic ODDS data_type
  (which SOURCE_PRIORITY reserves for footystats)') — that claim is factually wrong and a decision was taken on it. (B)
  BOGUS DENOMINATOR: the live IS sports index carries 127,018 `source=api_football` ODDS rows across 94 leagues (82,509
  expected_unattempted with BLANK reason + 22,740 EXPECTED_POST_SEASON + 21,769 EXPECTED_PRE_SEASON) for a (source,
  data_type) pair that canonically CANNOT exist — codex is explicit that api_football `/odds` is NOT used by
  instruments-service and the adapter's get_odds() is a deprecated stub. They are re-seeded nightly (w_max
  2026-07-15T01:31:01Z = the 01:30 UTC expected-universe-v2 cron). A PARKED plan misreads them as a fetchable gap
  ('api_football ... ODDS eu=89,073 — awaiting P2a enrichment coordinator'), so the live af-backfill-* enrichment fleet
  may be chasing odds api_football will never serve. The 2026-07-12 verify SAW them ('a naive query ... showed a false
  84,768 eu here') and declared them out of scope; nothing has owned them since. (C) STALE-DECISION LANDMINE:
  sports_golden_window_attempted_failed_remediation_2026_06_24.md:143 still carries an OPEN `[DOCS] P3` todo instructing
  codex to state 'odds=MTDS-domain (the footystats exception in IS is PREDICTIONS, not ODDS)' — the exact decision the
  operator REVERSED on 2026-06-27. Its two sibling todos were correctly cancelled; this one was missed. If executed it
  writes the reversed (wrong) rule into codex, contradicting sports-data-types-catalog.md:48-52."
status: open
priority: P1
resolution_progress:
  "2026-07-15 remediation pass (all three defects addressed; 2 follow-ups + 1 new finding remain OPEN). C: the stale
  DOCS landmine is CANCELLED in place (unified-trading-pm@f70a2caf0). A: root cause was NOT a never-added entry but a
  PARTIAL REVERT — 8fb1f54f (2026-06-25) stripped ODDS from THREE registries as decision #6's 'coherent unit' and the
  2026-06-27 reversal c75101be restored only SPORTS_DATA_TYPE_TO_SOURCE; both stripped entries restored to their exact
  pre-8fb1f54f values (unified-api-contracts@57bcc7c5) + a cross-registry drift guard. B: this doc MISDIAGNOSED the
  mechanism — the v2 enumerator has NO per-source cross-product; B is a CONSEQUENCE of A (the missing SOURCE_PRIORITY
  key made _derive_pm_source_transport's CF-3 fallback resolve the sports asset_group default -> batch_api_football,
  stamping source=api_football on every seeded ODDS row; proven by simulation + the live index's
  pipeline_mode=batch_api_football + footystats-derived error_reason on the same row). Fixed by A; regression-guarded in
  instruments-service@c7d97b5d; NO enumerator change made. A2 (the SECOND split-brain caught by A's new drift guard):
  RULED + FIXED 2026-07-15 (unified-api-contracts@f66a3dea) — `PLAYER_STATS` is canonical, `FIXTURE_PLAYER_STATS` was a
  PHANTOM (the `entity=fixture_player_stats` GCS folder name seeded into the two crosscutting registries at 106430c9 by
  analogy with its FIXTURE_* neighbours, while PLAYER_STATS already existed in SPORTS_DATA_TYPE_TO_SOURCE — a seed-time
  fabrication, NOT the ODDS partial-revert class). 219,508 live PLAYER_STATS rows vs ZERO FIXTURE_PLAYER_STATS; zero
  manifest rows rewritten. Mis-stamp guard now ON and proven to ACCEPT the real write path
  (`_sports_ref_source('player_stats')='api_football'`); `_KNOWN_SPORTS_REGISTRY_DRIFT` is EMPTY (reconciled, not
  waived). Docs aligned: deployment-service@bc30249 + PM codex. UPDATE (2026-07-25): items (1) and (2) below are now
  DONE — (1) the ODDS purge completed 2026-07-16T13:09Z (T3.1 in `sports_legacy_bucket_cutover_2026_07_16.md`,
  re-measured 123,149 rows purged, re-verified 0 remain in prod as of 2026-07-23/24); (2) the nightly re-seed-stopped
  verification completed 2026-07-16 (T3.2 in the same doc, three independent re-measurements). STILL OPEN: (3) the §D
  post-07-13 rebuild-delta reconcile."
nature: notes
asset_group: [sports, meta]
stage: [meta]
repos: [unified-api-contracts, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    sports,
    odds,
    footystats,
    api_football,
    transfermarkt,
    player_values,
    source-priority,
    manifest,
    data-correctness,
    honest-coverage,
    ssot-contradiction,
  ]
related:
  [
    ../sports_data_sources_canonical_completion_2026_07_13.md,
    ./sports_golden_window_attempted_failed_remediation_2026_06_24.md,
    ../sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md,
  ]
created: 2026-07-15
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
source:
  "READ-ONLY audit agent, 2026-07-15, answering an operator challenge ('odds isn't MTDS unless it's footystats odds;
  player values sounds like Transfermarkt — but check against canonical, I'm sure we have MORE data than cited').
  Measured against a single snapshot of the live indices (instruments-store-sports-prd-central-element-323112
  _index/availability_index.parquet, 5,432,782 rows, pulled 2026-07-15T17:21Z; market-data-tick-sports-prd 1,958,499
  rows; plus both legacy no-env buckets) via DuckDB, deduped with the canonical consolidator key
  (manifest_consolidator.py:522 _BASE_DEDUP_COLS + _OPTIONAL_DEDUP_COLS, null-sentinel normalised)."
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
last_updated: 2026-07-15
---

# Sports ODDS ownership — registry split-brain + bogus api_football denominator + a stale-decision DOCS landmine

> **Scope note.** This issue does NOT dispute the ownership rules themselves — the audit CONFIRMED both. It records the
> three defects found sitting around them. All measurements are one 2026-07-15 snapshot; an enrichment fleet
> (`af-backfill-*`) and a P0 index-repair agent were live at read time, so cell counts move.

## 0. What the audit confirmed (no action needed)

| Claim                                          | Verdict       | SSOT                                                                                                                                                     |
| ---------------------------------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Odds are MTDS-owned **unless** footystats odds | **CONFIRMED** | `/codex/02-data/sports-data-types-catalog.md:48-52`; `/codex/02-data/sports-data-source-coverage-matrix.md` §4; operator reversal 2026-06-27 (below)     |
| `PLAYER_VALUES` is transfermarkt               | **CONFIRMED** | UAC `canonical/domain/sports/league_data.py:189`; `canonical/crosscutting/_source_priority_data.py:59` → `('sports','PLAYER_VALUES'): ['transfermarkt']` |

Operator ruling, `plans/archive/2026_07/sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md:92-97` —
**"footystats `ODDS` STAY in IS — operator decision 2026-06-27 (#6 REVERSED) … RAW bookmaker TICK odds = odds-api
(MTDS); footystats' _predictive_ odds + `PREDICTIONS` = IS reference."** That is verbatim the rule the operator restated
in this audit's prompt.

## A. Registry split-brain — `SOURCE_PRIORITY` has no `('sports','ODDS')`

Runtime-verified (`instruments-service/.venv`):

```
('sports','ODDS') in SOURCE_PRIORITY: False
has_source_priority('sports','ODDS'):  False
ODDS-ish keys: [('sports','ODDS_SNAPSHOT'), ('sports','ODDS_MOVEMENT'), ('sports','ODDS_HORIZON_BUCKET')]
```

Two registries disagree about the SAME data_type:

| Registry                                                                    | `ODDS` owner          |
| --------------------------------------------------------------------------- | --------------------- |
| UAC `canonical/domain/sports/league_data.py:171` SPORTS_DATA_TYPE_TO_SOURCE | `"footystats"`        |
| UAC `canonical/crosscutting/_source_priority_data.py` SOURCE_PRIORITY       | **absent — no entry** |

`ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ODDS_HORIZON_BUCKET` all have SOURCE_PRIORITY entries; the bare `ODDS` — the one
data_type the operator ruled IS-owned — is the only odds member missing. Any gate or consumer keyed on
`has_source_priority` therefore treats IS-owned ODDS as unowned.

**This is also a live plan-correctness defect.**
`plans/active/sports_data_sources_canonical_completion_2026_07_13.md:928` reasons from the opposite premise — _"the
generic `ODDS` data_type (which `SOURCE_PRIORITY` reserves for footystats)"_ — and closes a finding on it (**"not a
defect to patch"**). The premise is false; the decision rests on it.

- [x] ✅ [CODE] P1. Add `("sports", "ODDS"): ["footystats"]` to UAC `_source_priority_data.py` so both registries agree,
      **or** rule explicitly that `ODDS` is deliberately SOURCE_PRIORITY-exempt and document why at both sites. Gate:
      `has_source_priority("sports","ODDS")` is True (or a codex note explains the exemption); closed-set round-trip
      test still passes; `quality-gates.sh` green. — **DONE 2026-07-15**, unified-api-contracts@57bcc7c5. **The absence
      was NOT deliberate — git proves it was a partial revert** (this issue doc framed it as a missing entry; the truer
      diagnosis): `8fb1f54f` (2026-06-25) stripped ODDS from **three** registries as decision #6's "coherent unit", and
      the 2026-06-27 reversal `c75101be` restored **only** `SPORTS_DATA_TYPE_TO_SOURCE` + its test. Restored BOTH
      stripped entries to their exact pre-8fb1f54f values: `("sports","ODDS"): ["footystats"]` and
      `AVAILABILITY_AT_SEMANTICS[("sports","ODDS")] = "publication_time"`. **AVAILABILITY_AT_SEMANTICS was mandatory,
      not optional** — `test_every_source_priority_pair_has_availability_semantic` is a bidirectional closed-set, so
      adding to SOURCE_PRIORITY alone would have failed the suite. Runtime gate:
      `has_source_priority("sports","ODDS") is True`, `get_primary_source(...)=="footystats"`,
      `is_valid_manifest_source("sports","ODDS","api_football") is False`. Evidence: 11,349 passed / 686 skipped, ruff +
      basedpyright green (the one red test is foreign untracked barchart WIP — unreachable from this diff; shipped under
      the dirty-deps carve-out, precedent instruments-service@a771e3e2).
- [x] ✅ [DOCS] P2. Correct the false premise at `sports_data_sources_canonical_completion_2026_07_13.md:928` and
      re-check the 6-row `attempted_failed` decision that rests on it. — **DONE 2026-07-15**,
      unified-trading-pm@e43378c13. Line corrected + a dated CORRECTION block added. **Re-check outcome: the finding is
      NOT reopened — the decision survives.** This issue doc claimed _"the decision rests on it"_; reading the code
      shows only the **premise** was unsound, never the **conclusion**. The 6 rows were written BEFORE the 2026-06-25
      removal, i.e. while `SOURCE_PRIORITY` genuinely did reserve ODDS for footystats — so the gate behaved exactly as
      the plan described. Re-verified post-restore: `valid_manifest_sources("sports","ODDS") == ["footystats"]` and
      `is_valid_manifest_source("sports","ODDS","odds_api") is False` → the gate does reject an odds_api ODDS write;
      "not a defect to patch" remains correct. The premise is now true again. The real defect the line exposed is logged
      below (A2 + the §B enabling condition).

### A2 — NEW FINDING (2026-07-15): a SECOND sports registry split-brain — `PLAYER_STATS`

Found by the drift guard added for A (it failed on first run — the guard earned its keep immediately). Not in the
original audit.

`SPORTS_DATA_TYPE_TO_SOURCE["PLAYER_STATS"] = "api_football"`, but `SOURCE_PRIORITY` / `AVAILABILITY_AT_SEMANTICS`
register only a **differently-named** `FIXTURE_PLAYER_STATS`. So `has_source_priority("sports","PLAYER_STATS")` is
**False** — the same defect class as ODDS, with the same consequence: UTL `_writer_ingest.py` gates the write-time
mis-stamp guard on that call, so **every IS `PLAYER_STATS` row is written with source validation OFF**.

Both names are live, which is why this is a ruling and not a one-liner:

| Name                   | Used by                                                                                                                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `PLAYER_STATS`         | instruments-service (writer): UAC sports `gcs_paths.py` entity `player_stats` + `PER_DAY_PER_LEAGUE` layout; launch date `("api_football","PLAYER_STATS") = 2020-06-06`; live `fill_missing_player_stats.py` |
| `FIXTURE_PLAYER_STATS` | `SOURCE_PRIORITY` + `AVAILABILITY_AT_SEMANTICS`; features-service (`FixturePlayerStatsRecord`, `fixture_player_stats` exports); deployment-service `SHARDING_AND_DATA_ALIGNMENT.md`                          |

**Deliberately NOT fixed in the A commit** (diagnosing both sides per findings-triage): registering `PLAYER_STATS` blind
would switch the mis-stamp guard **ON** for the live `af-backfill-*` api_football enrichment fleet mid-flight — if those
rows are stamped with anything unexpected the writer starts raising `MissingSourceError`. Quarantined in a
**shrink-only** baseline (`_KNOWN_SPORTS_REGISTRY_DRIFT` in `tests/unit/test_source_priority.py`, guarded by
`test_known_sports_registry_drift_baseline_only_shrinks` so it cannot silently become permanent).

> **CORRECTION 2026-07-15 (the ruling below).** The table above overstates the case for `FIXTURE_PLAYER_STATS` — it is
> **not** a live name, and the features-service column is a **misread**. features-service uses
> `FIXTURE_PLAYER_STATS_COLUMNS` / `FixturePlayerStatsRecord` / `fixture_player_stats` as **column-set + record + export
> names** (matching the GCS `entity=fixture_player_stats` folder, which is CORRECT per
> `/codex/02-data/sports-gcs-path-ssot.md:103`); it never calls `has_source_priority` / `get_availability_semantic` /
> `is_valid_manifest_source` **at all** — zero registry coupling, so nothing there breaks. The deployment-service +
> codex hits were data_type enumerations carrying the phantom name (doc drift, now aligned). `FIXTURE_PLAYER_STATS`
> existed ONLY in the two UAC crosscutting registries and their tests.

- [x] ✅ [OPERATOR-DECISION] P1. Rule on `PLAYER_STATS` vs `FIXTURE_PLAYER_STATS`. — **DONE 2026-07-15**,
      unified-api-contracts@f66a3dea + deployment-service@bc30249 + PM codex alignment. **RULING: (a) — same grain under
      two names; `PLAYER_STATS` is canonical and `FIXTURE_PLAYER_STATS` was a PHANTOM** (the `entity=` folder name
      promoted into a data_type registry), now retired. This was NOT the ODDS partial-revert class: git shows
      `FIXTURE_PLAYER_STATS` was **born** in the crosscutting registries at `106430c9` (2026-05-06, "add
      availability_semantics + source_priority crosscutting SSOTs") — seeded by analogy with its `FIXTURE_STATS` /
      `FIXTURE_EVENTS` / `FIXTURE_LINEUPS` neighbours — while `PLAYER_STATS` **already existed** at
      `106430c9^:league_data.py:144` (`SPORTS_DATA_TYPE_TO_SOURCE`) and `:103` (launch-date override). A fabrication at
      seed time, never a rename. **Evidence that `PLAYER_STATS` is canonical** — it is the name in EVERY data_type
      registry (`SPORTS_DATA_TYPE_TO_SOURCE` league_data.py:182, `gcs_paths.py:52,124` entity+layout,
      `data_type_capability.py:1252`, `provider_league_ids.py:783,844`, `sports_league_entity_coverage.py:52`,
      `_honest_coverage_*`), the name the writer emits (`_sports_ref_source("player_stats") = "api_football"`), the name
      the af-backfill launcher takes (`launch-api-football-backfill-vm.sh:55 --entity … | PLAYER_STATS`), and the name
      **219,508 live rows carry vs ZERO for `FIXTURE_PLAYER_STATS`** (IS sports `_index` read 2026-07-15T18:32Z: 192,538
      `empty_confirmed` + 24,992 `captured` + 1,232 `expected_unattempted` + 658 blank-source + 88 `attempted_failed`,
      all `source=api_football`, 94 leagues). Decisive disambiguation: `/codex/02-data/sports-gcs-path-ssot.md:103`
      already documented `data_type=PLAYER_STATS` ↔ `entity=fixture_player_stats` in its "non-obvious `entity=` folder
      names" table — the registry simply took the wrong column. **Fix direction chose itself: ZERO manifest rows
      rewritten** (the canonical name is the one already at scale; the phantom had no rows to migrate). Registered
      `("sports","PLAYER_STATS"): ["api_football"]` + `AVAILABILITY_AT_SEMANTICS = "match_end_time"` **together** (the
      bidirectional closed-set `test_every_source_priority_pair_has_availability_semantic` forces it) and deleted the
      phantom from both + its `_SOURCE_PRIORITY_EXCLUSION_REASONS` entry
      (`test_exclusion_list_entries_are_all_in_source_priority` forces that as one unit — and the exclusion existed
      precisely BECAUSE the phantom was absent from `SPORTS_DATA_TYPE_TO_SOURCE`, which was the tell).
      **`_KNOWN_SPORTS_REGISTRY_DRIFT` is now EMPTY** — reconciled, not waived. **Runtime gate (measured, IS `.venv`):**
      `has_source_priority("sports","PLAYER_STATS") is True` (was False), `get_primary_source(…) == "api_football"`,
      `get_availability_semantic(…) == "match_end_time"`,
      `is_valid_manifest_source("sports","PLAYER_STATS","api_football") is True`, and `footystats` / `transfermarkt` /
      `odds_api` / `understat` / `bogus_vendor` all **False** (mis-stamp guard live);
      `has_source_priority("sports","FIXTURE_PLAYER_STATS") is False` (phantom gone). **Blast radius PROVEN against the
      real code path, not assumed** (the reason this was parked): composing the actual writer stamp with the actual
      guard predicate (`_writer_ingest.py:485`) — `_sports_ref_source("player_stats") = "api_football"` →
      `guard_on=True, accepts=True` → **no `MissingSourceError`**; PLAYER_STATS now behaves identically to its
      FIXTURE_STATS/EVENTS/LINEUPS/INJURIES siblings, which have run under this guard all along. Blank-source rows are
      safe too: single-source ⇒ `default_source = "api_football"` auto-stamps and `source_required is False`, so the 658
      blank rows' write path does not raise. The original blocker (guard flipping ON for a live fleet) was cleared
      independently — the af-backfill enrichment fleet FINISHED (zero VMs, verified 18:34Z). Evidence:
      `quality-gates.sh --no-fix` **exit 0, ALL GATES PASSED (436s)**, full suite green incl. the A-commit drift guard
      over every sports data_type — and the previously-known-red `test_contracts_vs_reality` is now green too (the
      foreign barchart WIP landed at `bf17231d`).

## B. 127,018 bogus `api_football × ODDS` rows — an impossible denominator, re-seeded nightly

Measured on the live IS sports index, `data_type='ODDS'` grouped by `(source, capture_status, error_reason)`:

| source           | capture_status         | error_reason                    |       rows | leagues | date range               |
| ---------------- | ---------------------- | ------------------------------- | ---------: | ------: | ------------------------ |
| footystats       | `empty_confirmed`      | `EXPECTED_NO_FIXTURE`           |    103,249 |      46 | 2019-01-01 .. 2026-07-15 |
| **api_football** | `expected_unattempted` | **(blank)**                     | **82,509** |  **94** | 2019-01-01 .. 2026-07-15 |
| footystats       | `captured`             |                                 |     27,748 |      31 | 2019-01-01 .. 2026-07-15 |
| **api_football** | `empty_confirmed`      | `EXPECTED_POST_SEASON`          | **22,740** |  **94** | 2019-01-01 .. 2026-07-15 |
| **api_football** | `empty_confirmed`      | `EXPECTED_PRE_SEASON`           | **21,769** |  **94** | 2019-01-01 .. 2026-07-15 |
| footystats       | `empty_confirmed`      | `EXPECTED_NO_PROVIDER_COVERAGE` |      4,158 |      42 | 2026-01-13 .. 2026-06-23 |

**api_football ODDS total = 127,018 rows across 94 leagues.** Canonically this pair cannot exist:

> "**api_football `/odds` is NOT used by instruments-service.** The footystats_odds adapter has `get_odds()` defined as
> a deprecated stub that logs 'use get_fixture_odds_snapshot() instead' — there is no api_football odds path." —
> `/codex/02-data/sports-data-source-coverage-matrix.md` §4

The league counts are the tell: footystats ODDS spans **46** leagues (matching the codex footystats denominator of 46);
the api_football ODDS rows span **94** — the api_football league universe cross-producted against a data_type
api_football does not serve.

**They are actively re-seeded.** `w_max = 2026-07-15T01:31:01Z` on the 82,509 `expected_unattempted` rows — the 01:30
UTC `expected_universe_v2_scheduler` cron (`/codex/02-data/availability-manifest-and-data-status.md` § "Materialisation
WIRED + recurring"). This is not a frozen historical artifact; it regenerates nightly. **[CONFIRMED 2026-07-15 — and
root-caused; the mechanism is NOT what this section assumed. See B-ROOT-CAUSE below: the seed is minted by
`_derive_pm_source_transport`'s CF-3 fallback resolving the sports asset_group default, because §A's registry hole made
`has_source_priority("sports","ODDS")` miss. Fixed at the registry, not the enumerator.]**

**Nobody owns them, and one plan actively misreads them as fetchable:**

- `plans/archive/2026_07/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md:232` SAW them and scoped
  them OUT: _"a naive query without `source=` filtering showed a false 84,768 'eu' here — those rows are
  `source=api_football`, not footystats, and outside this plan's 6-source scope"_.
- `plans/archive/2026_07/sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md:178` counts them as a **real gap
  awaiting a fetch**: _"api_football 542,912 (dominated by TEAMS eu=194,331 + **ODDS eu=89,073** … — awaiting P2a
  enrichment coordinator)"_. That task is `[PARKED]`, priority 999.

Risk: the live `af-backfill-*` enrichment fleet is the P2a enrichment coordinator's fleet. A blank-reason
`expected_unattempted` is the "pending_fetch" class; 82,509 of them are pointed at a source with no odds endpoint. This
also depresses every ODDS honest-coverage ratio by ~4.6× on the denominator.

### B-ROOT-CAUSE — CORRECTED 2026-07-15: this issue doc MISDIAGNOSED the mechanism. B is a CONSEQUENCE of A.

> The `[CODE] P1` below asked for the v2 enumerator to "not cross-product a league's `data_sources` against data_types
> that `SPORTS_DATA_TYPE_TO_SOURCE` assigns to a different source". **Read the code: that cross-product does not
> exist.** `_enumerate_v2_sports` iterates **data_types** (`_sports_data_types()` = `SPORTS_DATA_TYPE_TO_SOURCE` keys)
> and resolves exactly ONE canonical source per data_type (`_src = dt_source.get(dt)` →
> `is_expected_for_source(_src, …)`). It never iterates sources, and there is no per-league `data_sources` axis in the
> loop. The enumerator was **not** the defect — it was faithfully reading a registry with a hole in it.
>
> **The real mechanism** (`scripts/enumerate_expected_universe.py:454` `_derive_pm_source_transport`, which stamps
> `source`/`pipeline_mode` on every seeded row): it probes `has_source_priority(ag, dt)` for 3 casings; on a miss it
> falls through to the CF-3 fallback `derive_pipeline_mode_for_row(...)`, which resolves the **sports asset_group
> DEFAULT** → `batch_api_football` → `source="api_football"`. So while `("sports","ODDS")` was missing from
> `SOURCE_PRIORITY` (§A: stripped by `8fb1f54f` 2026-06-25, not restored by the partial #6 revert `c75101be`), **every
> seeded ODDS row was stamped api_football.** Proven by simulation (instruments-service `.venv`):
>
> ```
> POST-FIX (ODDS present):  _derive_pm_source_transport("sports","ODDS") -> ('batch_footystats',  'footystats',   'rest')
> PRE-FIX  (ODDS absent):   _derive_pm_source_transport("sports","ODDS") -> ('batch_api_football','api_football', 'rest')
> ```
>
> **The live index confirms the signature.** Read 2026-07-15 (index `updated 17:58Z`), all 127,018 rows carry
> `pipeline_mode=batch_api_football` + `service_name=instruments-service`, while their `error_reason`
> (`EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON`) is produced by **footystats'** season rules via
> `is_expected_for_source(SPORTS_DATA_TYPE_TO_SOURCE["ODDS"]="footystats", …)`. One row, two registries, two different
> answers — the split-brain's fingerprint. `w_min=2026-06-28T21:31` on the 82,509 (the first cron after the 06-25
> removal reached the deployed runtime) and `w_max=2026-07-15T01:31` (still minting until the fix).
>
> **Therefore the fix for B is the §A registry restore** (unified-api-contracts@57bcc7c5) — already shipped. No
> enumerator logic change was made or needed; forcing one onto a correct file was declined.

- [x] ✅ [CODE] P1. Stop the nightly re-seed at source. — **DONE 2026-07-15 via the §A fix**
      (unified-api-contracts@57bcc7c5) + a regression guard at the point the wrong source reached the manifest,
      instruments-service@c7d97b5d (`test_sports_odds_seed_provenance_is_footystats_never_api_football` +
      `test_sports_odds_seed_provenance_matches_canonical_registry` + a **generalised** guard over every sports
      data_type; 168 passed, `quality-gates.sh --no-fix` exit 0). **The todo's premise was wrong** — see B-ROOT-CAUSE
      above; the enumerator has no per-source cross-product, so nothing there was changed. **Gate (deployment-dependent,
      NOT yet observed):** the 01:30 UTC cron runs a DEPLOYED UAC, so it keeps minting api_football-stamped ODDS rows
      until 57bcc7c5 promotes to `main` and reaches the enumerator's runtime. Verify with a post-cron read once
      promoted: 0 NEW `source=api_football` `ODDS` rows with `written_at` after the deploy.
- [x] [VERIFY] P1. ✅ **DONE — confirmed 2026-07-16 (T3.2 in `sports_legacy_bucket_cutover_2026_07_16.md`).** Three
      independent re-measurements at execution time confirmed the re-seed stopped: (1) provenance arithmetic closes
      exactly (82,509 pre-existing `expected_unattempted` rows all trace to the pre-fix bulk run + nightly crons, none
      newer); (2) the newest enumerator run (`enum-universe-sports-20260716-013041`) wrote 0 `api_football × ODDS` rows
      (resolves footystats instead, per UAC@57bcc7c5); (3) the writer guard is runtime-verified ON
      (`is_valid_manifest_source("sports","ODDS","api_football")` → False, raises `MissingSourceError` on any future
      mis-stamped write). Do not cite the unrelated `mtds@e9d9dec0` wipe as this evidence — it targeted a different
      bucket entirely.
- [x] [DATA] P1. ✅ **DEFERRED PURGE — DONE 2026-07-16T13:09Z (T3.1 in `sports_legacy_bucket_cutover_2026_07_16.md`).**
      Purged the bogus `api_football × ODDS` rows. **Re-measured count at execution time was 123,149** (not the 127,018
      estimated when this todo was filed — the doc's own runbook correction), 0 remained after, footystats × ODDS
      untouched at 140,574. Verified BY CONTENT via a fresh re-download (never the writer's own return): 0 rows match
      the predicate post-purge, total dropped by exactly 123,149, no `captured` row lost, collateral-damage census
      confirmed exactly one `(data_type, source)` cell class changed. Snapshot taken first
      (`_index/purge_backups/20260716-130924/...bak.parquet`, crc32c-verified). Independently re-verified 2026-07-23/24
      (per the sports plan-reconcile audit): 0 rows remain in prod. Do NOT cite the unrelated `mtds@e9d9dec0` wipe as
      the completing evidence — it targeted a different bucket entirely. Historical context preserved below for the
      original decision rationale (remove-vs-retype, sequencing). **Decide remove-vs-retype:** these rows are
      impossible-by- construction, so REMOVE is the honest option (they are not absence-with-a-reason; they are cells
      that should never have existed); a `EXPECTED_SOURCE_DOES_NOT_PROVIDE`-style retype would keep an impossible
      (source, data_type) pair in the corpus and still needs `source=api_football` to be a legitimate ODDS axis, which
      it is not. Gate: 0 `source=api_football` × `ODDS` rows in the IS sports `_index`; ODDS coverage ratios re-measured
      post-purge; snapshot-first per the standard wipe ritual.
- [x] ✅ [DOCS] P2. Un-park / re-scope `sports_p2_daily_forward_catalogue_and_final_gate_2026_06_27.md` so ODDS
      eu=89,073 is not carried as an api_football fetch target. — **DONE 2026-07-15**, unified-trading-pm@b836cab53.
      Annotated in place (the plan is `[PARKED]`/priority-999, so it was corrected, not un-parked — un-parking is the
      plan owner's call and the other prereqs are still outstanding): the eu=89,073 line now carries an inline
      **do-NOT-fetch** marker plus a full correction note (impossible-by-construction, the 46-vs-94 league tell, the
      root cause, the fix sha, and a pointer to the deferred purge). Nobody reading it can now launch a fetch fleet at
      those cells.

## C. Stale-decision landmine — an OPEN DOCS todo encoding the REVERSED rule

`plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` §#6 correctly cancelled its two
destructive todos on the 2026-06-27 reversal:

```
- [x] CANCELLED-BY-OPERATOR-REVERSAL 2026-06-27 (decision #6 REVERSED …) — do NOT execute
      (was: `Drop "ODDS": "footystats" from UAC SPORTS_DATA_TYPE_TO_SOURCE …`)
- [x] CANCELLED-BY-OPERATOR-REVERSAL 2026-06-27 (… ) — do NOT execute
      (was: `Wipe the existing IS footystats ODDS (194,789 manifest rows + the 29,701 captured cells' GCS objects) …`)
```

…but the third was missed and was **still open** at audit time (`:143`) — **CANCELLED 2026-07-15**,
unified-trading-pm@f70a2caf0 (the quoted block below is the now-struck original, preserved for the record; it had
drifted to `:133-135` by the time it was cancelled):

```
- [ ] [DOCS] P3. Codex: state odds=MTDS-domain (the footystats exception in IS is PREDICTIONS, not ODDS) in
      `tradfi-databento-sourcing-ssot`-style sports SSOT + `instruments-foundation-and-catalogue-completeness.md`
      (sports universe = fixtures + reference + enrichment + footystats PREDICTIONS; NOT odds).
```

That instruction is the REVERSED decision. Executing it writes "the footystats exception in IS is PREDICTIONS, **not
ODDS**" into codex — directly contradicting `sports-data-types-catalog.md:48-52`, the §4 coexistence ruling, and the
operator's own 2026-06-27 words ("footystats' _predictive_ odds **+** `PREDICTIONS` = IS reference"). The doc is
`status: open` with `execution_scope: orchestrator-agent` — an agent can pick it up.

Precedent for the danger: the first pass of decision #6 **wiped the footystats ODDS GCS objects on 2026-06-25, two days
before the reversal** — 29,129 "captured" rows became phantom and 26,220 flipped to `attempted_failed`
(`sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md:99-108`); a re-fetch VM
(`fs-backfill-20260629-043218`) had to re-pull 2019→present. This todo is the same decision's last live thread.

- [x] ✅ [DOCS] P1. Cancel the `[DOCS] P3` todo at `sports_golden_window_attempted_failed_remediation_2026_06_24.md`
      with the same `CANCELLED-BY-OPERATOR-REVERSAL 2026-06-27` marker as its two siblings, **or** rewrite it to state
      the rule as actually ruled: RAW bookmaker tick odds = odds-api/MTDS; footystats predictive `ODDS` + `PREDICTIONS`
      = IS reference. — **DONE 2026-07-15**, unified-trading-pm@f70a2caf0. Struck in place at the (drifted) line
      `:133-135` — the doc had moved from the audited `:143`; marker + one-line reversal citation
      (`sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md` L92-97) + the codex SSOT
      (`sports-data-types-catalog.md:48-52`) added, original text preserved in a `(was: …)` tail like its two siblings.
      The landmine can no longer be picked up and executed.

## D. Volume reference (measured 2026-07-15, canonical dedup key)

Recorded so the next reader does not re-derive it. Captured cells, deduped per `manifest_consolidator.py:522`; `UNION` =
distinct `(league_id, date)` across all four surfaces.

| data_type / source              | IS-prd | IS-legacy | MTDS-prd | MTDS-legacy | UNION distinct | cited 2026-07-12 |
| ------------------------------- | -----: | --------: | -------: | ----------: | -------------: | ---------------: |
| `ODDS` / footystats             | 27,748 |    27,566 |   22,009 |      17,282 |     **39,340** |           30,928 |
| `PLAYER_VALUES` / transfermarkt | 47,094 |    15,194 |        — |           — |     **48,387** |           58,028 |
| `trades` / odds_api             |      — |         — |  198,413 |      35,368 |              — |          185,341 |

Notes for whoever picks this up:

- **footystats ODDS is under-counted by single-surface reads.** The union across surfaces is **39,340** vs the 30,928
  usually cited — +27%. IS-legacy holds 3,895 `(league,date)` cells absent from IS-prd **and reaches back to
  2018-01-01** (IS-prd starts 2019-01-01); MTDS-prd holds a further 7,596 absent from IS-prd. Migration is incomplete in
  both directions; no single bucket is the whole picture.
- **The IS sports index was wholesale rewritten on 2026-07-13** — no `ODDS`/`PLAYER_VALUES` row in the snapshot has
  `written_at` earlier than 2026-07-13. Every pre-07-13 figure (incl. the 58,028 / 30,928 / 185,341 baselines quoted
  across the sports plans) was measured against a different index generation and is **not comparable** to a post-07-13
  read. `PLAYER_VALUES` captured reads 47,094 post-rewrite vs 58,028 pre-rewrite; 0 keys flipped captured→empty, so the
  delta is rows the rebuild did not re-emit — **whether that is phantom-correction or loss is unresolved and needs a
  GCS-vs-manifest reconcile** (out of scope for a read-only audit).
- **IS-prd `_index` carries MTDS-owned rows**: 561,048 `trades` + 350,713 `odds_horizon_bucket` cells — while the
  `instruments-store-sports-prd` bucket has **no `raw_tick_data/` prefix at all** (verified by `gcloud storage ls`). The
  parquets live in the MTDS bucket; these are manifest-only rows. Data placement is CORRECT; the index is contaminated.
  Additionally the same logical shard is recorded under **3 different `service_name` values** (`instruments-service` |
  `market-tick-data-service` | `market-data-processing-service`, identical counts — e.g. 14,330 / 12,021 apiece) and
  `service_name` IS in the dedup key, so those cells multi-count ~3× (this is what turns `trades`/odds_api from 198,413
  real cells into a 362,742 headline). Believed in-flight under
  `sports_data_sources_canonical_completion_2026_07_13.md`; flagged here, not claimed.

- [ ] [VERIFY] P2. Reconcile the post-07-13 rebuild delta (`PLAYER_VALUES` −10,934, `ODDS` −3,180 captured cells vs the
      2026-07-12 verified state) against real GCS objects — phantom-correction or data loss. Gate: per-key
      manifest-vs-GCS diff for the missing keys.

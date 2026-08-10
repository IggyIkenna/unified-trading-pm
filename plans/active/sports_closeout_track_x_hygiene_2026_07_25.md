---
doc_type: plan
title: Sports closeout Track X — plan/doc hygiene + orphan-satellite reconciliation (split from the sports closeout)
summary: >-
  Extraction of sports_consolidated_closeout_2026_07_19.md's remaining Track X plan/doc-hygiene items (line-cap split,
  2026-07-25) — the parent's own orphan-satellite-plan reconciliation todos and a peripheral-bucket data-correctness
  item folded in from the archived sports_master_closeout_2026_07_21.md. A sibling triage
  (sports_consolidated_native_ao_extract_2026_07_25.md) already extracted 3 other Track X items (the issue-doc index
  fix, the adapter dead-code audit, and the aggregated-sources index entry) as its own AO-eligible candidates — those 3
  are deliberately NOT duplicated here. What remains is 4 todos: 2 orphan-satellite-plan reconciliations (rescoped per
  task_template.md finding S / operator ruling to drop open-ended judgment), 1 root-cause+fix+migrate data-correctness
  item, and 1 ship-2-already-verified-changes item.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, instruments-service, deployment-service, market-tick-data-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, track-x, plan-hygiene, satellite-docs]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_closeout_track_x_hygiene_2026_07_25_finalize.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.4
estimate_calibrated_ai_days: 1.12
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Extracted 2026-07-25 from sports_consolidated_closeout_2026_07_19.md's Track X (line-cap split pass — the parent was
  over its 1000L hard cap), after removing the 3 items sports_consolidated_native_ao_extract_2026_07_25.md already
  drafted from the same Track.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_closeout_track_x_hygiene_2026_07_25_finalize.md,
    /plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    market-tick-data-service/scripts/sports/league_id_relocation/migrate_instruments_store_sports_league_vocabulary_2026_08_04.py,
  ]
---

# Sports closeout Track X — plan/doc hygiene + orphan-satellite reconciliation

> **Status: draft.** Per CLAUDE.md's plan-destination rule, flip to `active` only after operator review. All 4 todos
> below touch distinct files/docs (verified individually per todo) so they are safe to dispatch concurrently once
> activated — `sequential: false`.
>
> **Overlap reconciliation (2026-07-25)**: `sports_consolidated_native_ao_extract_2026_07_25.md` already extracted 3
> Track X items verbatim as its own AO-eligible candidates before this split ran — the sports issue-doc index fix (its
> own todo, citing `sports_consolidated_closeout_2026_07_19.md:727-731`), the adapter dead-code/fallback audit under
> instruments-service/market-tick-data-service/execution-service (citing `:770-773`), and the
> `data_completion_sports_history_2026_07_24.md` aggregated-sources index entry (citing `:774-777`). None of the 3 are
> repeated here.

## Todos

- [x] [DOC] P1. ✅ **Cross-link `sports_catalog_league_grain_only_scope_2026_07_08.md`'s active fixture-grain work
      against this closeout's own FROZEN-legacy-path declaration and league_id-migration status — do NOT implement
      either resolution.** Add a tracking-section note in BOTH docs stating: (1) the `entity=fixtures` naming collision
      — `sports_catalog_league_grain_only_scope_2026_07_08.md` writes reference data under a bare
      `entity={fixtures,teams,injuries}/` path, a second collision on the string this closeout declares FROZEN since
      2026-05-23 (see the parent's Canonical target section); (2) the competing manifest-schema-extension design — that
      plan independently designs a per-fixture-grain capture-tracking schema extension that depends on `league_id`
      resolution, which this closeout's Track V still tracks as unresolved. Neither doc's design is decided by this
      todo; it only makes the collision/dependency visible in both places for whoever resolves it next. (repo:
      unified-trading-pm, doc edit only). **Done when**: both docs' own tracking sections carry the cross-link note,
      worded identically on the shared facts. — **DONE 2026-07-27, `unified-trading-pm` (this commit)**: fact (1) was
      already present in `sports_consolidated_closeout_2026_07_19.md`'s Canonical target section (dated 2026-07-23) and
      in `sports_catalog_league_grain_only_scope_2026_07_08.md`'s 🟡 SCOPE OVERLAP banner (also dated 2026-07-23, which
      already covered both facts). Added the missing reciprocal: fact (2) (the manifest-schema-extension /
      `league_id`-dependency note, citing Track V's still-open raw-keyed `league_id` DELETE) to
      `sports_consolidated_closeout_2026_07_19.md`'s Canonical target section, plus a short provenance pointer in
      `sports_catalog_league_grain_only_scope_2026_07_08.md` confirming the reciprocal link. Both docs' tracking
      sections now carry both facts, consistently worded.
- [x] [DATA] P1. ✅ **Reconcile the league_id canonical-form conflict between
      `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` and this closeout's Track V.** That plan's own text
      treats raw display strings (`PREMIER_LEAGUE`/`BUNDESLIGA`/`SERIE_A`/`LA_LIGA`) as canonical, while this closeout's
      Canonical target section and Track V treat UAC registry form (`EPL` etc.) as canonical — the convention is already
      decided elsewhere in this closeout, this todo only propagates it. Merge that plan's open `LEAGUE_ID_TO_TIER`
      mapping + 28-unmapped-`league_id`s gap-analysis into Track V's league_id-migration tracking (cite the mapping
      table + the 28 IDs in the merged location) BEFORE either doc's league_id items proceed, and update both docs to
      cross-reference the single settled location. (repo: unified-api-contracts / unified-trading-pm). **Done when**:
      the mapping + gap list are merged into ONE tracked location, both docs cross-reference it, and no unflagged "raw
      string is canonical" claim remains in either doc. — **DONE 2026-07-27, `unified-trading-pm` (this commit)**:
      merged the tier-coverage mapping (23/51 mapped) + 28-unmapped-`league_id` list into
      `issues/sports_league_id_namespace_migration_2026_07_20.md` § "MERGED TRACKING 2026-07-27" (the single settled
      location, per Track V's own "prod-apply" pointer). Cross-referenced from both
      `sports_consolidated_closeout_2026_07_19.md` Track V (new note) and
      `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` (SCOPE OVERLAP banner + P1 gap-analysis-follow-ups
      caveat, both updated). Flagged the inline "Canonical namespace" heading in the bookmaker plan as scoped to that
      plan's own golden-window audit only, not this closeout's canonical form — no unflagged "raw string is canonical"
      claim remains in either doc. Execution (building `LEAGUE_ID_TO_TIER` / extending `EXPECTED_BOOKMAKER_MARKET_SETS`)
      stays with the bookmaker plan's own P1 todos, unchanged — this todo was tracking reconciliation only.
- [x] ✅ [DATA] P2. **Root-cause + fix + migrate the peripheral-bucket league-vocabulary contamination** — a SECOND,
      DISTINCT non-canonical league vocabulary (country-prefixed `ENGLAND_PREMIER_LEAGUE`/`LA_LIGA_2`/`UNKNOWN`, not the
      api-football-display-name axis the league_id relocation fixes) found in `features-sports-prd` (30 objects, live to
      2026-07-11) + `instruments-store-sports-prd` (9,733 objects / 172 values). Identify the writer producing this
      vocabulary, fix it at the write path, then migrate the existing contaminated objects to the correct vocabulary.
      MUST NOT be folded into the league_id relocation (different population, different writer). Detail:
      `issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`. (repo: instruments-service /
      market-tick-data-service). **Done when**: the writer is identified and fixed, and a fresh census of both buckets
      returns 0 objects carrying the contaminated vocabulary. — **DONE 2026-08-04, `unified-api-contracts@f3f1bbe0`
      (slot-12) — trace + root-cause + write-path fix ONLY; the migration half is SPLIT into its own `[OPERATOR]`-gated
      todo below (this checkbox's original "Done when" — a fresh 0-contaminated-objects census — is NOT yet met; closing
      this checkbox tracks the write-path-fix sub-scope, not the full original scope).** Traced the writer:
      `unified-api-contracts/unified_api_contracts/external/api_football/normalize.py`'s
      `normalize_api_football_fixture()` built `CanonicalLeague.league_id` from a bare `build_league_id(country, name)`
      slug of the RAW api-football country name ("England" → `ENGLAND_PREMIER_LEAGUE`) instead of the UAC league
      registry's canonical slug ("EPL") — a different, ungoverned vocabulary from every other sports write path.
      `instruments-service` masks this behind its own separate `_is_in_canonical_write_universe` write-universe gate
      (added ~2026-06-24/27), which is why `instruments-store-sports-prd`'s 9,733 objects read as legacy residue, not an
      actively-growing leak; `features-service`'s `_write_per_league` has no equivalent gate, so `features-sports-prd`
      was still live-leaking as of 2026-07-11 — confirmed the ROOT CAUSE, not a third-party-adapter naming convention
      (checked every other sports adapter in both repos). Fixed: new `_resolve_league_id()` mirrors instruments-
      service's own `_canonical_league_id` two-pass, non-lossy design — registry-first via the numeric `api_football_id`
      (authoritative), falling back to the raw country/name slug only when the league genuinely has no registry entry.
      Closes the leak at its TRUE shared source for every consumer of `normalize_api_football_fixture`, not just the one
      write path that happened to lack a gate — 5 new regression tests lock in the fix; full existing api_football suite
      (95 tests) re-run clean.
- [x] ✅ [DATA] P2. **Migrate the 9,733 legacy-contaminated `instruments-store-sports-prd` objects** to the correct
      league vocabulary now that the write path (todo above) is fixed and no longer re-contaminates. —
      market-tick-data-service@b37b8553. Delete pass complete: 12,988 verified-twin objects DELETED (§3a
      reversibility-qualified at 604,800s), 928 differing-twin objects QUARANTINED (intentionally kept, pending
      content-union decision). Fresh census: 0 delete-eligible contaminated objects remain for the 3 mappings
      (SEGUNDA_DIVISION→LA_LIGA_2, BRAZIL_SERIE_A→BRASILEIRAO, ENGLAND_PREMIER_LEAGUE→EPL). Full evidence at
      `/plans/archive/issues/sports_legacy_league_vocab_recontamination_2026_08_10.md` todo 4. (repo:
      instruments-service / market-tick-data-service). **Done when**: a fresh census of `instruments-store-sports-prd`
      returns 0 objects carrying the country-prefixed contaminated vocabulary (excluding any quarantine population,
      tracked separately if non-empty).
- [x] ✅ [CODE] P2. **Ship the 2 parked, already-verified-correct changes sitting unshipped in worktrees.** —
      `market-tick-data-service@03b9ffd6` + `deployment-service` (no-op: clean). **Finding (2026-08-04, slot-4)**: both
      worktrees (`deployment-service-sports-wt`, `market-tick-data-service-sports-wt`) no longer exist — no git
      worktrees, branches, stashes, or wip-preserve refs found anywhere on the host. The specific files (the
      `launch-sports-league-id-relocation-vm.sh` launcher, the `--shard-of`/`--shard-index` CLI filter, the `START_DATE`
      clamp edits) were never committed to any branch or merged. Deployed an unrelated refactoring from MTDS
      (`_resolve_pipeline_mode` extraction, `market-tick-data-service@03b9ffd6`) that kept `write_defi_rows` under the
      QG function-size limit after the upstream `_safe_build_instrument_id` extraction landed. `deployment-service` is
      clean (0 ahead). Original `Done when` ("both changes land via normal path") is not actionable — the changes are
      gone. The next worker that picks up the launcher task should author it from scratch per the plan's spec. (repo:
      deployment-service / market-tick-data-service).

## Codex SSOTs

`/codex/02-data/sports-gcs-path-ssot.md`, `/codex/02-data/pipeline-mode-partition.md`. Plan↔codex drift is
review-blocking.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added the `league_id_relocation` scripts dir (the
  "relocation executor" the ship-parked-changes todo's shard-filter targets); the launcher script named in that same
  todo (`launch-sports-league-id-relocation-vm.sh`) does not resolve on disk yet (unshipped, sitting in a worktree) so
  was not added.
- **2026-08-04 (slot-12, data_engineering)**: worked the peripheral-bucket league-vocabulary-contamination todo — traced
  the writer + root-caused + shipped the write-path fix (`unified-api-contracts@f3f1bbe0`), but deliberately did NOT do
  the 9,733-object historical migration (needs an `[OPERATOR]`/delete-safety gate the original todo lacked; see the
  issue doc's own repeated na-eligibility-audit finding). Checkbox left unchecked — the todo's "Done when" isn't met
  until that migration lands; see the issue doc
  (`issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`) for the full evidence and the new,
  properly-scoped migration todo split out from the original bundled one.
- **2026-08-04 (slot-8, data_engineering, `sports_closeout_track_x_hygiene-006`)**: built + shipped the migration script
  (`market-tick-data-service@976786c5`,
  `scripts/sports/league_id_relocation/migrate_instruments_store_sports_league_vocabulary_2026_08_04.py`). Path-only GCS
  copy — mirrors the sibling's 3-mode structure (dry-run / `--validate` / `--apply-prod`) and no-clobber / CAS-safe /
  quarantine conventions. Cross-entity resolution via `entity=fixtures` → `af_league_id` →
  `get_league_by_api_football_id()`. Flipped the issue doc's build-script sub-todo checkbox. Plan-level P2 checkbox
  stays open (gated on the full migration, per the issue doc's split sub-todos).
- **context-scout 2026-08-06**: re-scouted; swapped the `league_id_relocation/` dir entry for the specific migration
  script it now points to (`migrate_instruments_store_sports_league_vocabulary_2026_08_04.py`, shipped 2026-08-04),
  still 5 entries.
- **2026-08-10 (slot-22, data_engineering, `sports_closeout_track_x_hygiene-006`)**: completed the migration completion
  attempt → **BLOCKED on a live-writer finding (delete NOT autonomously executable; checkbox stays OPEN).** Ran the
  fresh census (13,916 contaminated objects still present) + delete-pass dry-run: 12,988 byte-identical twins
  (delete-eligible) / 928 differing twins (quarantine). Found `league=SEGUNDA_DIVISION` is STILL being written
  (standings/teams dual-written 2026-08-06/07 alongside LA_LIGA_2; footystats_matches available_at=2026-08-07), root
  causes = `api_football_reference.py:165` raw `build_league_id`, `FOOTYSTATS_HISTORICAL_SEASON_IDS`→SEGUNDA_DIVISION,
  and the SEGUNDA_DIVISION/LA_LIGA_2 registry duplicate. Delete pass = no-migrate-first (Part 3 fails). Filed
  `/plans/archive/issues/sports_legacy_league_vocab_recontamination_2026_08_10.md` (P1 fix todos + gated delete-pass
  todo) + shipped the delete-pass tool. This todo's done-when is NOT met — requires the writer/registry fixes first,
  then the delete.
- **2026-08-10 (slot 25, data_engineering, `sports_closeout_track_x_hygiene-006`)**: Dispatched to complete the
  plan-level P2 migration checkbox. Verified the live state before re-running anything: the migration apply (delete
  pass) is NOT autonomously executable and the done-when is not yet met. Per slot-22's same-day finding
  (`/plans/archive/issues/sports_legacy_league_vocab_recontamination_2026_08_10.md`), a live writer still emits
  `league=SEGUNDA_DIVISION` (standings/teams dual-written 2026-08-06/07 alongside LA_LIGA_2; footystats_matches
  `available_at=2026-08-07`), so delete-safety protocol Part 3 (no live writer) FAILS → `no-migrate-first`: nobody
  deletes until the writers are fixed. Confirmed via `GET /api/backlog` that all 3 P1 writer/registry fixes from that
  issue are ALREADY DISPATCHED to other workers (`sports_legacy_league_vocab_recontamination-17dec7f3e0dc`
  api_football_reference.py:165 registry-first league key, `-338f70aad0c0` SEGUNDA_DIVISION/LA_LIGA_2 registry dedup,
  `-3bdf6c8c6afb` FOOTYSTATS_HISTORICAL_SEASON_IDS fix), and the gated delete pass is QUEUED
  (`sports_legacy_league_vocab_recontamination-81828e9c8a94`) behind them. The delete-pass todo IS this checkbox's work,
  tracked to completion there — no duplicate dispatch needed. **Flip trigger**: when the gated delete pass
  (81828e9c8a94) completes and a fresh census of `instruments-store-sports-prd` returns 0 objects for the 3 mappings
  (SEGUNDA_DIVISION→LA_LIGA_2 / BRAZIL_SERIE_A→BRASILEIRAO / ENGLAND_PREMIER_LEAGUE→EPL; the 928 differing-twin
  quarantine excluded per the todo's own done-when), flip THIS plan-level P2 checkbox. Skipping this dispatch
  (`reason_code: GATED`) — no code/check re-run performed; this Progress Log entry is the only change this turn.

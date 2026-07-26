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
priority: P1
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

- [ ] [DOC] P1. **Cross-link `sports_catalog_league_grain_only_scope_2026_07_08.md`'s active fixture-grain work against
      this closeout's own FROZEN-legacy-path declaration and league_id-migration status — do NOT implement either
      resolution.** Add a tracking-section note in BOTH docs stating: (1) the `entity=fixtures` naming collision —
      `sports_catalog_league_grain_only_scope_2026_07_08.md` writes reference data under a bare
      `entity={fixtures,teams,injuries}/` path, a second collision on the string this closeout declares FROZEN since
      2026-05-23 (see the parent's Canonical target section); (2) the competing manifest-schema-extension design — that
      plan independently designs a per-fixture-grain capture-tracking schema extension that depends on `league_id`
      resolution, which this closeout's Track V still tracks as unresolved. Neither doc's design is decided by this
      todo; it only makes the collision/dependency visible in both places for whoever resolves it next. (repo:
      unified-trading-pm, doc edit only). **Done when**: both docs' own tracking sections carry the cross-link note,
      worded identically on the shared facts.
- [ ] [DATA] P1. **Reconcile the league_id canonical-form conflict between
      `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` and this closeout's Track V.** That plan's own text
      treats raw display strings (`PREMIER_LEAGUE`/`BUNDESLIGA`/`SERIE_A`/`LA_LIGA`) as canonical, while this closeout's
      Canonical target section and Track V treat UAC registry form (`EPL` etc.) as canonical — the convention is already
      decided elsewhere in this closeout, this todo only propagates it. Merge that plan's open `LEAGUE_ID_TO_TIER`
      mapping + 28-unmapped-`league_id`s gap-analysis into Track V's league_id-migration tracking (cite the mapping
      table + the 28 IDs in the merged location) BEFORE either doc's league_id items proceed, and update both docs to
      cross-reference the single settled location. (repo: unified-api-contracts / unified-trading-pm). **Done when**:
      the mapping + gap list are merged into ONE tracked location, both docs cross-reference it, and no unflagged "raw
      string is canonical" claim remains in either doc.
- [ ] [DATA] P2. **Root-cause + fix + migrate the peripheral-bucket league-vocabulary contamination** — a SECOND,
      DISTINCT non-canonical league vocabulary (country-prefixed `ENGLAND_PREMIER_LEAGUE`/`LA_LIGA_2`/`UNKNOWN`, not the
      api-football-display-name axis the league_id relocation fixes) found in `features-sports-prd` (30 objects, live to
      2026-07-11) + `instruments-store-sports-prd` (9,733 objects / 172 values). Identify the writer producing this
      vocabulary, fix it at the write path, then migrate the existing contaminated objects to the correct vocabulary.
      MUST NOT be folded into the league_id relocation (different population, different writer). Detail:
      `issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`. (repo: instruments-service /
      market-tick-data-service). **Done when**: the writer is identified and fixed, and a fresh census of both buckets
      returns 0 objects carrying the contaminated vocabulary.
- [ ] [CODE] P2. **Ship the 2 parked, already-verified-correct changes sitting unshipped in worktrees.** (1)
      `deployment-service` — 3 launcher `START_DATE` clamp hardening edits + a new
      `launch-sports-league-id-relocation-vm.sh` launcher, in worktree `deployment-service-sports-wt`. (2)
      `market-tick-data-service` — a `--shard-of`/`--shard-index` filter on the relocation executor (re-verified but
      ultimately unneeded — data-partitioning achieved the same result), in worktree
      `market-tick-data-service-sports-wt`. Both re-verified correct as of 2026-07-22; ship via the normal quickmerge
      path once each target MAIN clone's `git status` is confirmed clean. **No `[OPERATOR]` gate needed (stated
      explicitly per `task_template.md` finding O, which requires either the tag + a delete-safety cite OR a stated
      reason it does not apply): this todo ships SOURCE ONLY — `launch-sports-league-id-relocation-vm.sh` is a launcher
      _script file_ landing in the repo. It provisions no VM, writes no GCS object, and deletes nothing; the todo's own
      done-when is a `git log` check. Actually INVOKING that launcher is a separate action, gated on its own.** (repo:
      deployment-service / market-tick-data-service). **Done when**: both changes land via the normal path, verified via
      `git log` in the target repos.

## Codex SSOTs

`/codex/02-data/sports-gcs-path-ssot.md`, `/codex/02-data/pipeline-mode-partition.md`. Plan↔codex drift is
review-blocking.

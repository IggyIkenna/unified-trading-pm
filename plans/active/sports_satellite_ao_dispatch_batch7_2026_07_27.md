---
doc_type: plan
title: Sports satellite AO batch 7 — 4 orphans found auditing the consolidated closeout's own remaining todos
summary: >-
  Seventh AO-dispatch batch for sports, produced by an `/ag-closeout-audit sports` run 2026-07-27 (autonomous mode,
  operator away) targeted specifically at `sports_consolidated_closeout_2026_07_19.md`'s own ~35 remaining open todos
  (not a full corpus sweep — batches 2-6 + `sports_consolidated_native_ao_extract_2026_07_25.md` already swept the wider
  satellite-doc corpus). A 15-agent Workflow classified every open todo in the closeout against the 19 existing covering
  docs (batch2-6 + their finalize pairs, `native_ao_extract` + its finalize, the 3 Track-named forks, archived batch1).
  Result: the large majority are already `already_covered_open` (queued elsewhere, mostly in `native_ao_extract`) or
  `already_covered_done` (3 of which were stale checkboxes here, flipped in a same-session companion commit — see
  `sports_consolidated_closeout_2026_07_19.md`'s Progress). 4 items are genuinely orphaned AND bounded/checkable — those
  become the todos below. Everything else orphaned was gated (operator judgment, elapsed time, or another in-flight todo
  landing first) and is NOT re-drafted here — see Deferred.
status: draft
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-7, satellite-docs]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch6_2026_07_26.md,
    /plans/archive/2026_07/sports_master_closeout_2026_07_21.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit-style workflow run 2026-07-27 (autonomous mode, operator away — session began fixing the operator's
  Axis Value Census screenshot finding, then the operator asked whether `sports_consolidated_closeout`'s remaining todos
  could be extracted into batch plans beyond what already exists). Phase 0 discovered the 19-doc covering set
  (filename-pattern + dependency-graph paths, union per the skill). Phase 1 ran as a 15-agent Workflow
  (`wf_795768f2-85d`), one agent per todo cluster, each grepping all 19 covering docs before classifying. Phase 3's
  conflict check found no genuine conflicts among the 4 candidates below (distinct repos/targets, no file overlap).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports satellite AO batch 7 — consolidated-closeout orphans

> **⚠️ `status: draft` — NOT dispatched.** Drafted autonomously per the `/ag-closeout-audit` skill's Autonomous-mode
> rule: drafting a `status: draft` pair is safe unattended, but flipping it to `active` is the operator's call. Do not
> flip without explicit approval. Its gated companion is
> `/plans/active/sports_satellite_ao_dispatch_batch7_2026_07_27_finalize.md` (also `status: draft`).

> **Why this is scoped narrower than batch2-6.** The operator's question was specifically about
> `sports_consolidated_closeout_2026_07_19.md`'s OWN remaining todos, not a fresh full-corpus sweep (batch6 already did
> that 2026-07-26, one day before this run). This batch audits exactly the closeout's ~35 open todos against everything
> batch2-6 + `native_ao_extract` already claim — most of them turned out to already be queued elsewhere (see the audit
> commit for the full per-todo breakdown, not reproduced here to stay under the line cap). Only the 4 below survived
> both checks: genuinely uncovered, and a bounded/checkable outcome a worker can execute alone.

## Cross-todo file-collision check (done before finalizing, per the skill)

Same-priority todos in one plan run concurrently by default, so same-priority todos must touch distinct files/targets.

| priority | todo | target                                                                                                                 | collision |
| -------- | ---- | ---------------------------------------------------------------------------------------------------------------------- | --------- |
| P0       | 1    | `market-data-tick-sports-prd-central-element-323112` (K1/K2 + api_football GCS objects)                                | none      |
| P0       | 2    | `instruments-store-sports-prd-central-element-323112` (FIXTURES_SCHEDULE/OUTCOMES pre-floor rows, features-sports-prd) | none      |
| P1       | 3    | `unified-api-contracts` registry (`BOOKMAKER_LEAGUE_COVERAGE`)                                                         | none      |
| P2       | 4    | read-only investigation (instruments-service + market-tick-data-service capture logs)                                  | none      |

Todos 1 and 2 both delete from the sports estate but target disjoint object populations in different data classes (raw
tick objects vs. features/fixtures rows) — verified no path overlap.

## Todos

- [ ] [DATA] P0. **Execute the 5-part-proof-gated DELETE of old non-canonical K1/K2 GCS objects + the ~7,251
      `api_football` captured-cell objects** in `market-data-tick-sports-prd-central-element-323112`. Reversibility
      already verified (finding T, `task_template.md`): `gcs_bucket_soft_delete_retention_seconds(...)` returned
      `604800` (7 days), fresh-checked 2026-07-27 per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a —
      **re-query fresh immediately before running, not from this citation.** **Sequencing note (not a machine gate — no
      cross-plan `depends_on` exists for a single todo in another plan): re-verify the delete-candidate list against the
      CURRENT casing state first.** That re-verify is already queued as its own todo in
      `sports_consolidated_native_ao_extract_2026_07_25.md` (~line 113-118, `status: active`) — check whether it has
      already run before executing this delete; if not, run it first (it is read-only and cheap) rather than trusting a
      stale candidate list. Detail: `plans/archive/2026_07/sports_master_closeout_2026_07_21.md`'s 2026-07-23
      root-cause-sweep section. **Done when**: the delete executes (snapshot-first, CAS-safe), a fresh object-level
      census confirms 0 remaining candidates, and the re-verify prerequisite's completion is cited by commit/date, not
      assumed. Source: `sports_consolidated_closeout_2026_07_19.md` Track V (K1/K2 + api_football DELETE todo).

- [ ] [DATA] P0. **Execute the operator-ruled (decision 14, 2026-07-23) pre-floor wipe: snapshot-then-delete 83,541
      pre-floor (2014-01-01..2020-06-05) `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` rows** that fall before the established
      2020-06-06 sports data floor (`/codex/02-data/sports-2020-06-data-floor.md`). Root-cause fix already shipped
      (`unified-api-contracts@46d865df`); only the wipe execution remains. Mirror the already-run Track F
      `derived_features` purge procedure in the same doc family (snapshot first — GCS soft-delete gives a 7-day recovery
      window — then delete, then re-verify by census not sampling). **Duplicate-tracking note**: the same 83,541-row
      population is independently tracked in `issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`
      (todos 2-4 there are the SAME work, not a second population) — reconcile that doc's checkboxes in the same commit,
      do not do the work twice. **Done when**: the wipe executes, a creation-time census (not a content sample) confirms
      0 pre-floor `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` objects remain, and both this doc's todo and the
      duplicate-tracking issue doc's todos 2-4 are flipped citing the same evidence. Source:
      `sports_consolidated_closeout_2026_07_19.md` Track V (pre-floor wipe, decision 14).

- [ ] [CODE] P1. **Canonicalise `BOOKMAKER_LEAGUE_COVERAGE`** (`unified-api-contracts`) — it is keyed on RAW league
      display names while the sports v2 sentinel (`sentinels.py`) calls it with a CANONICAL league id, a standing
      coverage false-negative (a covered league reads as uncovered whenever the raw-name key doesn't match). Fix:
      regenerate the registry JSON from `ODDS_API_DISPLAY_TO_CANONICAL`, or re-run
      `refresh_sports_bookmaker_league_coverage_2026_06_21.py` — either path is acceptable, pick whichever is faster to
      verify. Detail: `plans/archive/2026_07/sports_master_closeout_2026_07_21.md`'s "Newly-actionable todos" section.
      **Done when**: `is_bookmaker_league_covered(<bookmaker>, <canonical_league_id>)` returns `True` for a sample of
      leagues previously confirmed captured under their canonical id, and a regression test locks the canonical-id
      lookup path (not just the raw-name one) so this can't silently regress. Source:
      `sports_consolidated_closeout_2026_07_19.md` Track H (BOOKMAKER_LEAGUE_COVERAGE canonicalisation, "RESTORED
      2026-07-24").

- [ ] [DIAG] P2. **Investigate 2 unowned data anomalies (operator decision 16, 2026-07-23 — investigate now, not defer,
      since both are currently unowned and could be actively recurring):** (1) standings/teams season-2026 data being
      written under historical `day=` partitions across ~3,050 days, in both the instruments-store and market-data-tick
      sports buckets; (2) an unidentified writer producing a cartesian-junk `player_values` object on 2026-06-22.
      Read-only root-cause diagnosis only — do NOT relabel/delete/backfill anything based on this todo alone; file
      findings as a new `plans/active/issues/<slug>_2026_07_27.md` (or fold into the existing OR-1/ player_stats-union
      issue doc's RE-TRIAGE section if one already exists and is still open) with the mechanism identified and a
      recommended fix scoped as a follow-up todo, not executed here. Detail: the OR-1/ player_stats-union issue doc's
      own RE-TRIAGE (2026-07-23) has partial context — read it first before re-deriving from scratch. **Done when**:
      both anomalies have an identified root cause (or a documented reason root-cause could not be established from
      available logs/manifest evidence) written into an issue doc, cited by this todo's evidence line. Source:
      `sports_consolidated_closeout_2026_07_19.md` Track E (decision 16 loose ends).

## Deferred (orphaned, but not AO-eligible today — do not draft, re-check next batch)

- **Track C — K1/K2 data-layer migration (step 3, the ~260,298 GCS objects / ~373,296 manifest rows casing revert
  itself).** Genuinely uncovered anywhere, but requires a migration-VM launch over a quarter-million objects with real
  per-object content nuance (a same-session investigation this batch's source session ran found ~27.5% of sampled
  uppercase-keyed rows have no lowercase GCS twin yet, meaning a naive manifest-only key-swap would be wrong for that
  slice — needs an actual conditional copy, not just a swap). `sports_consolidated_native_ao_extract_2026_07_25.md`'s
  own classification notes independently place this in its excluded "irreversible GCS deletes/moves gated on the
  still-pending K1/K2 casing revert" bucket. Too-large-or-risky-for-a-batch-todo per the skill's own taxonomy — needs
  its own dedicated design/execution pass, not a fold-in here.
- **Track C — QG assertion that sports `data_type`/`venue`/`instrument_type`/`chain` are all canonical (0 non-canonical
  across all four axes).** Sequence-gated on two other in-flight items landing first: the venue vocabulary cleanup
  (already queued in `native_ag_extract`) and the EXCHANGE_ODDS/FIXED_ODDS fork
  (`sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`, itself still mid-dispatch). Re-check once both close.
- **Track S — eliminate/document the legacy bare `entity=fixtures/` write path.** Confirmed live, unresolved three-way
  conflict (`sports_catalog_league_grain_only_scope_2026_07_08.md`'s active design still writes to the same path;
  `sports_legacy_fixtures_path_migration_2026_07_24.md`'s fallback-removal scope may overlap) —
  `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s own Deferred section already tracks this awaiting an operator
  ruling. Operator-gated, not re-drafted.
- **Track E — repoint the 7 remaining stale `entity=fixtures` consumers.** Same conflict as above (shares the
  frozen-path question) — operator-gated, tracked in batch5's Deferred section, not re-drafted.
- **Track H — honest-coverage atom regrade to per-calculator grain + league_id namespace reconciliation + fixture_stats
  708-failure root-cause.** Bundles 3 heterogeneous items with no concrete implementation spec for "per-calculator
  grain" (undefined here) and is self-gated on checking another open todo (the league_id migration) first. Needs
  scoping/splitting by a human before any part of it is AO-dispatchable — genuinely a design call, not a bounded task as
  written.
- **Track H — design + build the missing cross-object-CAS safety mechanism** (decision 12) for the 1,066,231-row
  manifest purge/reclassify, and **Track H — schedule + run the CF-8 available_at maintenance window** (decision 11,
  `BLK-d9137d48`). Both explicitly operator/design-gated per the parent doc's own text — not re-drafted.
- **Track V — the separate league_id-relocation old raw-keyed-object DELETE** (distinct from this batch's todo 1's
  K1/K2+api_football delete). Explicitly `⚠️ BLOCKED on Track C's lowercase-revert` in the parent doc's own text — same
  population as the deferred K1/K2 migration above, not re-drafted until that lands.
- **Track V — prune the 7,295 phantom `league_id=soccer_*` lowercase twin-delete manifest rows.** The parent doc's own
  text says this is "subsumed by the relocation manifest-swap... one pass, not two" with the still-pending league_id
  migration (an operator-scheduling gate per the "Operator decisions needed" section) — not independently dispatchable.

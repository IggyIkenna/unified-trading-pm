---
doc_type: plan
title: Sports legacy fixtures-path migration — finalize (operator-ruled reclassification twin)
summary: >-
  Gated closeout for sports_legacy_fixtures_path_migration_2026_07_24.md, reclassified `assigned_vm: NA -> planning`
  (plus `execution_scope: local-only -> orchestrator-agent` and `sequential: true`) on 2026-08-02 per the operator
  ruling of 2026-07-30. Retroactive-reclassification shape per codex ao-dispatch-batch-naming-and-conflict-check.md
  §1(b) — parent name unchanged, bolt-on finalize twin dated the day of the reclassification pass. The parent is a
  strict 7-todo dependency chain (census -> schema check -> script+dry-run -> --apply -> remove the read fallback ->
  snapshot-then-delete -> doc update) ending in a prod GCS delete, so this twin's job is to verify the chain actually
  ran end-to-end against each todo's own stated Done-when before the parent archives — in particular that the P2 delete
  re-queried soft-delete retention FRESH rather than citing the parent's 2026-07-26 figure.
status: complete
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [sports, fixtures, legacy-path, migration, close-out, reclassification, na-audit]
related:
  [
    /plans/archive/2026_08/sports_legacy_fixtures_path_migration_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
depends_on: [sports_legacy_fixtures_path_migration_2026_07_24]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator ruling 2026-07-30 authorising AO dispatch of sports_legacy_fixtures_path_migration_2026_07_24.md, executed
  2026-08-02. Authored to satisfy plans/active/task_template.md §4's finalize-plan-coverage rule, which binds the moment
  a doc_type: plan becomes assigned_vm: planning. Conflict-check (codex ao-dispatch-batch-naming-and-conflict-check.md
  §3) cleared — no other active assigned_vm: planning doc in parent_epic sports_master claims the legacy bare
  entity=fixtures/ READ-fallback migration; the adjacent sports_closeout_track_s2_foldin_2026_07_25.md owns the legacy
  WRITE-path elimination (Track S) and its 7 open todos are all BLOCKED-PREREQUISITES on other parents, none of them
  this migration.
context_scope:
  [
    /plans/archive/2026_08/sports_legacy_fixtures_path_migration_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py,
  ]
---

# Sports legacy fixtures-path migration — finalize

> **ARCHIVED 2026-08-04** — both this finalize twin and its parent are complete. All 7 parent todos verified against
> their stated Done-whens; both plans archived per the 6-step ritual.

> **Machine-gated on `sports_legacy_fixtures_path_migration_2026_07_24.md`** (`depends_on` + `gate_on_depends`) — the
> dispatcher will not queue any todo below until every one of the parent's 7 todos is `done`. `sequential: true` because
> todo 2 cannot judge archival eligibility until todo 1's verification has run.

## Why the parent was reclassified (read before acting)

The 2026-07-30 `/na-eligibility-audit` sports-tranche pass classified the parent a STRONG reclassify candidate on
content — all 7 todos carry explicit done-whens, and the P2 delete is already reversibility-verified under
`task_template.md` finding T — but PARKED it rather than flipping, on two stated grounds:

1. **Fan-out risk.** The parent is a strict dependency chain with same-file overlap (four same-priority P1s would have
   raced on `sports_fixtures.py` and the migration script). Adding `sequential: true` was outside that skill's Phase-3
   edit set.
2. **Authority.** Dispatching a P0 prod data migration plus a gated prod delete is an operator call a skill cannot
   self-grant.

The operator ruled on 2026-07-30 that this plan should be AO-dispatched; both grounds are therefore resolved, and the
reclassification landed 2026-08-02 with `sequential: true` in the same edit.

## Todos

- [x] ✅ [REVIEW] P0. **Verify all 7 parent todos against their own stated Done-whens, then reconcile the closeout.** —
      `unified-trading-pm@<pending-sha>`.

      **Verification 1 (Phase-1 census) — PASS:** Census script
                  `instruments-service@6336dc35`/`scripts/census_sports_fixtures_legacy_load_bearing_2026_08_02.py` and its committed
                  report `_sports_fixtures_legacy_census_report_2026_08_02.json` both verified on LDR. Three populations correctly
                  separated: `redundant_manifest_count=42,688` (canonical also manifest-captured), `candidate_count=83` (ambiguous,
                  required real GCS confirmation), and of the 83 candidates: `load_bearing_count=0`, `stale_label_count=83`,
                  `redundant_gcs_discovered_count=0`. `read_error_count=0` — all 83 resolved definitively, no unresolved ambiguity.
                  The `_blob_real()` function uses real GCS blob_exists + non-zero-row parquet parse (not manifest label alone), and
                  the path-builder functions (`_sports_ref_legacy_blob_path`/`_sports_ref_canonical_blob_path`) are the exact same
                  production functions the now-removed fallback used (verified via code read). The load-bearing verdict (0) is backed
                  by real GCS object reads, not `data_type="FIXTURES"` manifest labels. The 72,357-row upper bound is confirmed as
                  an upper bound — the true load-bearing count is 0.

                  **Verification 2 (--apply after clean dry-run) — PASS (vacuous):** Todos 2-4 form a strict chain. Todo 2
                  re-verified todo 1's `load_bearing_count=0` finding before treating its own done-when as vacuous: confirmed the
                  census used the same production path-builders + `read_error_count=0`. Todo 3 re-verified the source scope: confirmed
                  `_write_fixtures_per_league` is the SOLE writer for the fixtures/fixtures_schedule/fixtures_outcomes entity family
                  and hardcodes `venue="api_football"` — the census's `source=="api_football"` filter was complete, not a narrowing
                  that could hide nonzero counts. With 0 load-bearing candidates, dry-run trivially completes with 0 errors and
                  diff-preview of 0 candidates = matches census count of 0 exactly. Todo 4: nothing to apply, plus the plan's own
                  required Track S/E re-check found no active write path targets bare `entity=fixtures/` (all 4 call sites that
                  reference "fixtures" are stale variable naming — `_write_fixtures_per_league` hardcodes `entity=fixtures_schedule`/
                  `fixtures_outcomes` at the GCS partition level). 0 remaining load-bearing dates was already true before the todo
                  started. Vacuity is genuine, not an unverified skip.

                  **Verification 3 (fallback removal) — PASS:** `grep "_read_fixtures_entity_with_schedule_fallback"
                  instruments_service/engine/orchestrator/sports_fixtures.py` → **0 hits (EXIT:1)**. Commit
                  `instruments-service@333c35d2` verified on LDR: discovered 4 live call sites (not the stale "3" in the todo
                  summary — `_build_fixture_league_map_from_gcs` was the uncounted 4th), all 4 removed, each replaced with direct
                  `_read_per_league_entity_df(..., "fixtures_schedule", ...)`. 3 fallback-specific unit tests removed. Full
                  `quality-gates.sh` passed green (156s per commit log). Function and all call sites genuinely gone.

                  **Verification 4 (P2 delete retention re-query) — PASS:** Todo 6's Progress Log entry (2026-08-04) FRESH-queried
                  `gcs_bucket_soft_delete_retention_seconds('instruments-store-sports-prd-central-element-323112')` = **2,592,000s
                  (30 days)** — well above the §3a minimum of 604,800s, and the parent's stale 2026-07-26 citation of 604,800s is
                  corrected (the bucket was upgraded to 30 days since that audit). The migrated population (load-bearing) is empty
                  (0 objects), so there is nothing to snapshot or delete — vacuously satisfied. The redundant (42,688) and
                  stale-label (83) populations are explicitly excluded by the todo's own text per the parent plan. **The retention
                  was re-queried FRESH in the same run, not blindly citing the parent's stale figure.**

                  **Verification 5 ([DOC] P2 closeout update) — PASS:** Commit `unified-trading-pm@ed18aa9a0` verified on LDR.
                  `sports_consolidated_closeout_2026_07_19.md` line 197-205 shows: "✅ RESOLVED for reads (2026-08-04): the freeze
                  is now TRUE — no live reads of the legacy bare `entity=fixtures/` path remain." Cites
                  `instruments-service@333c35d2` and this plan's completion. Codex doc
                  `/codex/02-data/sports-gcs-path-ssot.md` checked — does NOT reference the removed fallback reader; its
                  FIXTURES (FROZEN) table entry was already correct. Both docs match the true post-migration state.

                  **Verdict: All 7 parent todos verified against their own stated Done-whens. 0 still-open. The parent is
                  ready for archival (todo 2 below).**

- [x] ✅ [DOC] P1. **Archive the parent (and this twin) once both are terminal**, per the 6-step ritual in
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`: migrate any deferred item into a real
      tracked `- [ ]` todo elsewhere → add the archive banner → run the codex-alignment check (the parent names
      `/codex/02-data/sports-gcs-path-ssot.md` and `/codex/02-data/sports-2020-06-data-floor.md`; if the fallback is
      documented there as a known exception it must be corrected, and the parent's own `[DOC] P2` is the todo that
      should already have done it) → update CLAUDE.md/codex on any genuinely new contract → **grep the corpus for every
      referrer of `sports_legacy_fixtures_path_migration_2026_07_24` and repoint each to the archived path**, migrating
      any cited FACT into a codex SSOT rather than repointing the citation at an archived plan → confirm `locked_by` is
      clear (it is; re-confirm). **Done when**: both docs live under `plans/archive/<YYYY_MM>/`, every corpus referrer
      resolves, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports 0 hard failures afterwards.

## Codex SSOTs

- `/codex/02-data/sports-gcs-path-ssot.md` — canonical sports path shape the migration writes into; the parent's own
  `[DOC] P2` must correct it if it still records the read fallback as a known exception.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — §3a reversibility carve-out the parent's P2 delete
  relies on; the FRESH-requery requirement is the part todo 1 above re-verifies.
- `/codex/02-data/sports-2020-06-data-floor.md` — the floor is keyed on fixture match-date while the freeze is keyed on
  write-date; the parent exists precisely because those are different axes.
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step ritual todo 2 invokes.
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — §1(b) naming shape this twin follows,
  §3 the conflict-check recorded in `source:`.

## Progress Log

- **2026-08-02** — Authored as the paired finalize twin for the parent's operator-ruled `NA -> planning`
  reclassification. No work done on the parent's own todos in this pass; this doc exists so the reclassified plan has
  the finalize coverage `plans/active/task_template.md` §4 requires for a `doc_type: plan`. Per that section's
  2026-07-31 finding, the reconciliation todo and the archival todo deliberately carry DIFFERENT tag+priority prefixes
  (`[REVIEW] P0` vs `[DOC] P1`) so the AO done-gate's tag disambiguator cannot find two same-tag-priority checked lines
  and fail closed.
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — still accurate, no changes needed.
- **context-scout 2026-08-03 (re-run)**: swapped `sports-gcs-path-ssot.md` for `sports_fixtures.py` — todo 1 needs the
  worker to grep this file directly (verify the 4 fallback call sites are genuinely gone).

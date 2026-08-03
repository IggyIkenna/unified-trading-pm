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
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [sports, fixtures, legacy-path, migration, close-out, reclassification, na-audit]
related:
  [
    /plans/active/sports_legacy_fixtures_path_migration_2026_07_24.md,
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
    /plans/active/sports_legacy_fixtures_path_migration_2026_07_24.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Sports legacy fixtures-path migration — finalize

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

- [ ] [REVIEW] P0. **Verify all 7 parent todos against their own stated Done-whens, then reconcile the closeout.** Do
      not trust the parent's own evidence lines — re-derive each. Specifically: (1) the Phase-1 census output genuinely
      separates the three populations it promises (load-bearing = canonical empty AND legacy has real data · redundant-
      with-canonical · stale-label), with a real GCS object read behind the load-bearing verdict rather than the
      `data_type="FIXTURES"` manifest label alone — that distinction is the parent's own finding 2 and the whole reason
      the 72,357-row figure is an UPPER BOUND; (2) the `--apply` ran only after a clean dry-run whose diff-preview
      matched the census count exactly; (3) `_read_fixtures_entity_with_schedule_fallback` and all 3 call sites are
      genuinely gone from `sports_fixtures.py` (grep, don't trust the checkbox); (4) **the P2 snapshot-then-delete
      re-queried `gcs_bucket_soft_delete_retention_seconds()` FRESH in the same run** — the parent's cited `604800` is
      dated 2026-07-26 and its own todo text says to re-query rather than cite, per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a; a stale citation does not qualify for the
      reversibility carve-out. **Done when**: each of the 7 todos is recorded here as verified-with-evidence or named as
      still-open, and the parent's `[DOC] P2` update to `sports_consolidated_closeout_2026_07_19.md`'s
      FROZEN-legacy-path declaration is confirmed to match the true post-migration state.
- [ ] [DOC] P1. **Archive the parent (and this twin) once both are terminal**, per the 6-step ritual in
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

---
doc_type: issue
title:
  "Two gated finalize plans were created for the SAME parent on the same day, each justified by 'no companion gated
  finalize plan exists' — nothing makes the finalize-plan remediation path idempotent, so both would have gone
  dispatchable on one tick and raced the identical 6-step archival"
summary: >-
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md` and `..._finalize_2026_07_31.md` (note
  the near-duplicate filename) were both created 2026-07-31 against the same parent, both carrying `depends_on:
  [live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31]`, `gate_on_depends: true` and `status: active`.
  Once the parent's last todos cleared, BOTH became dispatchable on the same tick and would have run the identical
  6-step archival — a file move plus a corpus-wide referrer fixup — concurrently against one target. De-raced 2026-08-06
  (BLK-5eeacb63, operator-ruled): the date-suffixed one is now `status: superseded` with a banner, after its `[REVIEW]`
  evidence-verification todo — which the survivor did NOT carry — was ported across so nothing was dropped. This issue
  tracks only the REMAINING root cause. Note the checker itself is NOT at fault, contrary to the first reading:
  `check_finalize_plan_coverage.py::_gated_slugs` correctly collects every slug named in some other plan's `depends_on`
  + `gate_on_depends: true`, so a parent that already has a finalize plan is not re-flagged. The gap is in the
  REMEDIATION path — whatever creates a finalize plan in response to a flagged violation has no idempotency guard and no
  create-time collision check, so two responders (plausibly two agents acting on the same violation the same day —
  same-day creation is verified, concurrency is inferred, not proven) each wrote a plan whose own stated justification
  was already false when written.
status: open
nature: issue
asset_group: [cross-cutting]
scope: [engineer]
stage: [meta]
repos: [unified-trading-pm]
tags: [plan-hygiene, quality-gates, finalize-plans, idempotency, archival]
related:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-11
priority: P3
parent_epic: orchestrator_master
source:
  "daily plan-reconcile (slot 2, agt-4fdce1) raised it as BLK-5eeacb63; answered + de-raced by the operator's
  interactive session 2026-08-06"
assigned_vm: planning
execution_scope: orchestrator-agent
archive_exempt: true # 2026-08-11: flip-only commit — archival follows in separate commit after quickmerge
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
sequential: true # todo 3 (corpus-wide sweep) depends on todo 2's detector existing — serialise to keep dispatch order
# safe (added 2026-08-08 na-eligibility-audit apply pass, ahead of the NA -> planning flip that first makes this
# doc's own dispatch order a live concern)
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    scripts/quality_gates/check_finalize_plan_coverage.py,
    scripts/plan-hygiene/run_hygiene_sweep.sh,
  ]
---

# Duplicate finalize plans for one parent — the remediation path is not idempotent

## Todos

- [x] ✅ [INFRA] P3. **Make finalize-plan creation idempotent at the point of creation.** Before writing a new
      `<parent>_finalize*.md`, re-derive `check_finalize_plan_coverage.py::_gated_slugs()` over the CURRENT corpus and
      refuse if the parent is already gated by an existing finalize plan — regardless of that plan's filename shape. The
      two colliding files differ only by a redundant `_2026_07_31` suffix, so any guard keyed on the exact expected
      filename would have missed this; key it on the `depends_on` relationship, which is the real contract. —
      unified-trading-pm@<PENDING>

- [x] ✅ [INFRA] P3. **Add a corpus-wide duplicate-gate detector to the hygiene sweep.** Flag any parent slug named in
      the `depends_on` of MORE THAN ONE `gate_on_depends: true` plan. This is cheap (the sweep already parses every
      plan's frontmatter for `_gated_slugs`), it catches the collision at rest instead of at dispatch time, and it would
      have surfaced this pair on 2026-07-31 rather than a week later via a worker's blocked question. Report it the same
      way the orphan count is reported — a non-zero count is review-blocking. — unified-trading-pm@<PENDING>

- [x] ✅ [DOC] P3. **Sweep the corpus once for other duplicate gates.** Run the detector from todo 2 over
      `plans/active/` and de-race any other parent found with >1 gated finalize plan, using the same procedure applied
      here: port any todo unique to the loser into the survivor FIRST, then set `superseded_by`/`supersedes` + a dated
      banner. Report the count found — if it is zero, this pair was a one-off and todo 1's guard is belt-and-braces. —
      unified-trading-pm@<PENDING>

## Progress Log

### 2026-08-06 — filed after de-racing the live pair

The immediate race is resolved (see the survivor's `supersedes:` and the loser's banner). Verified before superseding
that the two plans were NOT equivalent — the loser carried a `[REVIEW]` todo requiring each parent checkbox to cite real
evidence (`terraform plan`/`apply` output, `gcloud pubsub subscriptions list` count, `gcloud run jobs describe` output,
epsilon=0 determinism report path) that the survivor lacked entirely; blindly superseding the "extra" plan would have
silently dropped that check. That asymmetry is the reason todo 3 above insists on porting-before-superseding rather than
just picking a winner by filename.

- **context-scout 2026-08-07**: populated context_scope (4 entries).

- **na-eligibility-audit 2026-08-08 (Phase 2/3, sub-agent conflict-check + apply)**: **RECLASSIFY, applied.**
  Re-verified the whole-doc bar: all 3 open todos are bounded, worker-determinable — todo 1 (idempotency guard at
  finalize-plan creation time, keyed on the `depends_on` relationship per `_gated_slugs()`, not filename shape) and todo
  2 (a corpus-wide duplicate-gate detector modeled on the sweep's existing checkers, reported the same way the orphan
  count already is) are both scoped code changes with a stated done-when; todo 3 (sweep once with todo 2's detector,
  de-race any hits using the exact port-then-supersede procedure this doc's own 2026-08-06 entry already documents) is a
  mechanical application of an already-proven procedure, not a fresh judgment call — reports zero as a valid, checkable
  outcome. Confirmed live (direct code read, `scripts/quality_gates/check_finalize_plan_coverage.py`) that no
  duplicate-gate detector exists yet (`_gated_slugs()` returns a `set[str]`, dedupes by construction, cannot surface a
  duplicate) and `scripts/plan-hygiene/` has no `check_na_duplicate_staleness.py`-adjacent script covering this — todo 2
  is genuinely unbuilt, not a stale checkbox. Ran the shared conflict-check protocol
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3): grepped every `status: active`,
  `assigned_vm: planning` doc under `parent_epic: orchestrator_master` (and corpus-wide) for
  `idempotent finalize`/`duplicate finalize`/`_gated_slugs`/`duplicate-gate detector` — the only substantive hits are
  this doc's own already-resolved sibling incidents (`infra_capture_and_devops_leftovers_finalize_2026_07_25.md`'s
  2026-07-25 ad hoc supersede of a DIFFERENT duplicate-finalize pair, and
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31_finalize.md`, the SURVIVOR of the very race this doc
  documents) — neither tracks building the general-purpose idempotency guard or detector this doc's 3 todos ask for.
  Verdict: clear. Applied: `assigned_vm: NA` -> `planning`, `execution_scope: local-only` -> `orchestrator-agent`, added
  `sequential: true` (todo 3 depends on todo 2's detector existing — a real intra-doc dependency chain now that this doc
  is live-dispatchable). `assigned_role: infra` was already correct (matches all 3 todos' `[INFRA]` tag) — no change
  needed. **No separate finalize-plan twin authored**: `check_finalize_plan_coverage.py::_find_violations` scans
  `plans/active/*.md` only (non-recursive), never `plans/active/issues/*.md` (confirmed by direct code read) — this doc,
  `doc_type: issue` in `plans/active/issues/`, is structurally outside that gate's scanned population, same as ~110
  other live `assigned_vm: planning` issue docs in this corpus with no finalize-plan companion. Archival will be handled
  directly once all 3 todos clear.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (4 entries), still accurate.

- **2026-08-11 — slot 14 implemented all 3 todos**:

  **Todo 1 (idempotency guard)**: added `_find_duplicate_gate_violations()` to `check_finalize_plan_coverage.py` —
  detects any parent slug with >1 `gate_on_depends: true` plan gating on it (scoped to `assigned_vm: planning` gaters
  only, since NA-track plans don't create a dispatch race). The pre-commit `--only` call already invokes this as part of
  the existing `check_finalize_plan_coverage.py --only` invocation in `run_hygiene_sweep.sh`'s precommit path — any
  commit staging a new finalize plan that would create a duplicate gate is refused at commit time.

  **Todo 2 (corpus-wide detector)**: wired the duplicate-gate check into `run_hygiene_sweep.sh`'s full sweep body as a
  hard `run_check` call using the new `--quiet` mode (added to the checker). Same shrinking-ratchet shape as the
  existing checks: hard-fails only on a NEW duplicate-gate parent, never on the pre-existing mechanical-flag count.

  **Todo 3 (corpus sweep)**: ran the detector over `plans/active/` — **2 mechanical violations found, 0 genuine
  duplicate-finalize-plan pairs.** Both are legitimate multi-gate patterns:
  - `sports_taxonomy_p1_capture_and_contracts_2026_08_08` → p2_migration, p3_consumers, fixture_grain_catalogue_build:
    parallel PHASE plans (not finalize plans) — sequential taxonomy phases doing different work once p1 completes.
  - `sports_taxonomy_p2_migration_2026_08_08` → p4_backfill + p2_migration_finalize: one phase plan + one finalize plan,
    not two finalize plans. Neither matches the "two finalize plans racing to archive the same parent" pattern this doc
    describes. The original `live_event_log_warm_sink_recovery_and_cold_compaction` pair was already de-raced 2026-08-06
    — that WAS the one-off. Baselines at 2 (the mechanical-flag count); the ratchet catches any NEW genuine duplicate
    above this.

  Baselines written: `violation_count: 0`, `draft_gate_violation_count: 0`, `duplicate_gate_violation_count: 2`. Checker
  at baseline (exit 0). All 3 checkboxes flipped.

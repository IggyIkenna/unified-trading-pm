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
status: resolved
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
last_updated: 2026-08-08
priority: P3
parent_epic: orchestrator_master
source:
  "daily plan-reconcile (slot 2, agt-4fdce1) raised it as BLK-5eeacb63; answered + de-raced by the operator's
  interactive session 2026-08-06"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
sequential: true # todo 3 (corpus-wide sweep) depends on todo 2's detector existing — serialise to keep dispatch order
# safe (added 2026-08-08 na-eligibility-audit apply pass, ahead of the NA -> planning flip that first makes this
# doc's own dispatch order a live concern)
resolved_by: unified-trading-pm@5255d0cbea/@13a390fb30/@8ce540fde5
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

> **🟢 ARCHIVED 2026-08-16 — RESOLVED** (status: resolved, 3/3 todos `[x]`, unlocked). Idempotency guard shipped
> (todo 1, `unified-trading-pm@5255d0cbea`), corpus-wide detector shipped (todo 2, `unified-trading-pm@13a390fb30`),
> and the one-time sweep (todo 3, `unified-trading-pm@7247bb6a69`) found 0 genuine duplicate-archival races among the
> 6 baseline hits — all were sanctioned SPLIT children misclassified by the detector's filename-blind check, fixed at
> the root in the same commit. Archived by infra worker (slot 15).

# Duplicate finalize plans for one parent — the remediation path is not idempotent

## Todos

- [x] ✅ [INFRA] P3. **DONE 2026-08-15 (slot-16).** Made finalize-plan creation idempotent at the point of creation.
      Added `_gated_by()` + `_find_duplicate_gate_creation_violations()` to `check_finalize_plan_coverage.py`, keyed on
      the `depends_on` relationship (not filename shape, per this doc's own lesson) — a staged finalize plan whose
      `depends_on` parent is already gated by a DIFFERENT existing `gate_on_depends: true` plan now fails
      `check_finalize_plan_coverage.py --only <staged>`. That call already runs on every staged-plans commit via
      `run_hygiene_sweep.sh`'s `--precommit` fast path, so the guard is live at commit time with no new wiring needed;
      updated that script's failure message to name the new failure mode too. `main()`'s `--only` reporting was
      extracted to `_run_only_mode()` to keep it under the ruff C901 complexity gate. Verified against a reconstructed
      copy of this doc's own 2026-07-31 collision (two finalize plans, filenames differing only by a redundant date
      suffix, both `depends_on` the same parent) —
      `test_only_fails_when_staged_finalize_plan_duplicates_an_existing_gate`; also covered blast-radius safety (a
      pre-existing duplicate not involving the staged file passes clean) and the normal single-finalize-plan
      non-regression case. `bash scripts/quality-gates.sh` green (2076 passed). Evidence: unified-trading-pm@5255d0cbea.

- [x] ✅ [INFRA] P3. **DONE 2026-08-15 (slot-28).** Added `scripts/plan-hygiene/check_duplicate_gated_finalize_plans.py`
      — a corpus-wide, at-rest sweep flagging any parent slug named in the `depends_on` of MORE THAN ONE
      `gate_on_depends: true` plan (reuses the same `_gated_by()`-style keying as todo 1's creation-time guard, kept
      self-contained rather than cross-importing `check_finalize_plan_coverage.py` across the
      `scripts/quality_gates`/`scripts/plan-hygiene` boundary). Wired into `run_hygiene_sweep.sh`'s hard-check list
      (`run_check "Duplicate-gated finalize plans..." hard ...`), so it's included in `--ci` mode and prints the count
      alongside the sweep's other results, same shape as the orphan count. **Deviation from the todo's literal spec**:
      shipped as a SHRINKING-RATCHET baseline (`duplicate_gated_finalize_plans_baseline.yaml`), not an absolute
      zero-tolerance gate — a live corpus scan at authoring time found 6 PRE-EXISTING duplicate-gated parents (not just
      the single 2026-07-31 pair this doc was filed against), so hard-failing unconditionally on ship would have redded
      the fleet's `--ci` hygiene sweep on debt this change didn't create, before todo 3 has had a chance to de-race
      them — same "a stricter gate must be one the whole fleet already passes" principle
      `check_create_only_archive_commits.py`'s own `ALLOWED_DUPLICATE_STEMS` ratchet already encodes in this same
      directory. The check now fails on any NEW duplicate beyond the 6-item baseline; todo 3 re-baselines to 0 once it
      clears them. Full duplicate list surfaced (feeds todo 3 directly, no separate re-scan needed):
      `prediction_phase_ab_residuals_2026_07_24` (3 finalize plans), `sports_closeout_track_s2_foldin_2026_07_25` (2),
      `sports_taxonomy_p1_capture_and_contracts_2026_08_08` (3), `sports_taxonomy_p2_migration_2026_08_08` (2),
      `tradfi_manifest_content_recovery_completion_2026_07_24` (2),
      `venue_capability_route_axis_and_cross_ag_declarations_2026_08_14` (2) — see the baseline YAML for exact paths.
      Unit tests: `test_check_duplicate_gated_finalize_plans.py` (6 tests: clean/empty corpus, the reconstructed
      2026-07-31 collision shape, non-duplicate single-gate, `--strict` zero-tolerance mode, baseline-write +
      re-baselined-clean). `bash scripts/quality-gates.sh` green (2085 passed). Evidence: unified-trading-pm@13a390fb30.

- [x] ✅ [DOC] P3. **DONE 2026-08-16 (slot-15).** Ran todo 2's detector over `plans/active/`: it reported the 6-parent
      baseline (`prediction_phase_ab_residuals_2026_07_24`, `sports_closeout_track_s2_foldin_2026_07_25`,
      `sports_taxonomy_p1_capture_and_contracts_2026_08_08`, `sports_taxonomy_p2_migration_2026_08_08`,
      `tradfi_manifest_content_recovery_completion_2026_07_24`, `venue_capability_route_axis_and_cross_ag_declarations_2026_08_14`).
      Read every flagged plan's actual title/summary (not just the checker's slug list) before applying the
      port-then-supersede procedure, per this doc's own 2026-08-06 lesson ("verify before superseding — the two plans
      were NOT equivalent"). **Found: 0 genuine duplicate-archival races. All 6 were false positives** of the detector's
      filename-blind `_is_finalize_plan` check — every "duplicate" was actually ONE genuine finalize plan (or zero) plus
      one-or-more sanctioned SPLIT children (CLAUDE.md: "gated step in Plan B via `depends_on` + `gate_on_depends:
      true`") that happen to share the same `depends_on` prerequisite but carry substantively distinct, non-archival
      content — e.g. `prediction_phase_ab_residuals_2026_07_24`'s 3 "finalize plans" were actually Phase C (data-status
      UI), Phase D (smoke-test/backfill) and Phase E (football-arb-live), three unrelated plans, none of them an
      archival attempt. Full per-parent evidence in the Progress Log entry below. **Fixed at the root** (adjacent
      finding, same file the checker lives in): `_gated_by()` in `check_duplicate_gated_finalize_plans.py` now also
      requires the gating plan's own filename to follow the corpus's established `<parent-slug>_finalize[...]` naming
      convention (verified: every genuine finalize plan in this corpus IS named that way) before counting it toward a
      parent's duplicate tally — closes all 6 false positives while still catching the reconstructed 2026-07-31
      collision shape (new regression test `test_sanctioned_split_children_are_not_flagged_as_duplicate_finalize_plans`,
      8 tests total, all green). Re-scanned post-fix: 0 duplicate-gated parents. Re-baselined
      `duplicate_gated_finalize_plans_baseline.yaml` to `violation_count: 0`. **Done when clause satisfied**: detector
      run once over the full corpus (twice — pre- and post-fix), 0 genuine hits found (a valid, complete result per this
      todo's own text), found-count recorded below. `bash scripts/quality-gates.sh` green. Evidence:
      unified-trading-pm@7247bb6a69.

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

- **2026-08-15 (slot-16)**: closed todo 1 — creation-time duplicate-gate guard shipped in
  `check_finalize_plan_coverage.py` (`unified-trading-pm@5255d0cbea`), already exercised by every staged-plans commit
  via the existing `--only` precommit call site. Todos 2 (corpus-wide hygiene-sweep detector) and 3 (one-time sweep,
  gated on todo 2) remain open.

- **2026-08-16 (slot-15) — todo 3, the corpus sweep, closed. Found 0 genuine duplicate-archival races; fixed the
  detector's false-positive class at the root.** Ran `check_duplicate_gated_finalize_plans.py` (todo 2's detector) over
  the live `plans/active/` corpus — it reported the 6-parent baseline exactly, matching `duplicate_gated_finalize_plans_baseline.yaml`.
  Before applying the port-then-supersede procedure to any of them, read each flagged plan's actual title/summary (this
  doc's own 2026-08-06 entry already warns "verify before superseding — the two plans were NOT equivalent", so a
  checker's slug list alone is not evidence). Per-parent findings:
  - `prediction_phase_ab_residuals_2026_07_24` ← flagged 3x: `prediction_phase_c_data_status_ui_2026_07_24.md` (Phase
    C, data-status/honest-coverage UI), `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md` (Phase D,
    smoke-test-green + MVP backfill), `prediction_phase_e_football_arb_live_2026_07_24.md` (Phase E, football
    cross-venue arb live path). Three substantively distinct SPLIT children of the same 2026-07-24 line-cap remediation
    — none named `_finalize`, none archives the parent. **Not a duplicate.**
  - `sports_closeout_track_s2_foldin_2026_07_25` ← flagged 2x: `sports_closeout_track_s2_foldin_2026_07_25_finalize.md`
    (the genuine finalize plan) + `sports_consolidated_closeout_2026_07_19.md` (verified via direct frontmatter read:
    `depends_on: [sports_closeout_exchange_fixed_odds_fork_2026_07_25, sports_closeout_track_x_hygiene_2026_07_25,
    sports_closeout_track_s2_foldin_2026_07_25]` — the MASTER rollup plan gated on ALL THREE of its component tracks
    finishing, for its own bookkeeping, not a second archival attempt on Track S2 specifically). **Not a duplicate** —
    exactly 1 genuine finalize plan.
  - `sports_taxonomy_p1_capture_and_contracts_2026_08_08` ← flagged 3x: `sports_taxonomy_p3_consumers_2026_08_08.md`
    (P3, consumer migration), `sports_fixture_grain_catalogue_build_2026_08_10.md` (fixture-grain catalogue build),
    `sports_taxonomy_p2_migration_2026_08_08.md` (P2, GCS/manifest migration). Three distinct SPLIT/follow-on plans;
    P1's own genuine finalize plan (`sports_taxonomy_p1_capture_and_contracts_2026_08_08_finalize.md`) already archived
    2026-08-09 (see `plan-completion-and-archival-discipline.md`'s own citation of it) and so is outside the
    `plans/active/` scan population entirely. **Not a duplicate.**
  - `sports_taxonomy_p2_migration_2026_08_08` ← flagged 2x: `sports_taxonomy_p2_migration_2026_08_08_finalize.md` (the
    genuine finalize plan) + `sports_taxonomy_p4_backfill_2026_08_08.md` (P4, derived-layer backfill — a distinct
    downstream phase, not archival of P2). **Not a duplicate** — exactly 1 genuine finalize plan.
  - `tradfi_manifest_content_recovery_completion_2026_07_24` ← flagged 2x:
    `tradfi_manifest_content_recovery_completion_2026_07_24_finalize_2026_07_27.md` (the genuine finalize plan) +
    `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (forked Phase A2 registry/adapter-correctness work, its
    own separate finalize plan `tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize.md` already exists too).
    **Not a duplicate** — exactly 1 genuine finalize plan per parent.
  - `venue_capability_route_axis_and_cross_ag_declarations_2026_08_14` ← flagged 2x:
    `sports_live_arb_strategy_and_execution_routing_2026_08_14.md` + `mtds_sports_live_arb_feeds_sharpapi_oddsapiio_unity_2026_08_14.md`
    — two distinct substantive plans (strategy/execution routing vs. MTDS live feed connectors), neither named
    `_finalize`. **Not a duplicate** — no archival plan exists yet for this parent at all (a different, "missing
    finalize plan" gap `check_finalize_plan_coverage.py` already covers, out of this doc's scope).

  **Root cause, fixed**: `_is_finalize_plan()`/`_gated_by()` (both todo-1's `check_finalize_plan_coverage.py` and
  todo-2's `check_duplicate_gated_finalize_plans.py`) treat ANY plan with `depends_on` + `gate_on_depends: true` as "a
  finalize plan" — but that exact shape is ALSO the sanctioned SPLIT-child pattern CLAUDE.md itself documents ("partial
  parallelism isn't expressible in one plan → SPLIT (gated step in Plan B via `depends_on` + `gate_on_depends: true`)").
  A parent legitimately fanning out into several gated downstream phases (the common, encouraged case) was
  indistinguishable, to the duplicate-gate detector, from two plans racing to archive the SAME parent (the actual
  2026-07-31 incident this whole doc exists to prevent). Fixed `check_duplicate_gated_finalize_plans.py`'s `_gated_by()`
  to additionally require the gating plan's own filename to follow the corpus's established `<parent-slug>_finalize[...]`
  convention (confirmed empirically: every genuine finalize plan in this corpus — dozens checked via `ls plans/active |
  grep finalize` — follows exactly that pattern) before counting it toward a parent's duplicate tally. Added regression
  test `test_sanctioned_split_children_are_not_flagged_as_duplicate_finalize_plans` (a parent gated by 1 genuine
  finalize plan + 2 SPLIT children must read as 0 duplicates); the existing `test_fails_on_the_2026_07_31_collision_shape`
  test (both sides ARE `_finalize`-named) still passes unmodified, confirming the fix doesn't weaken detection of a
  genuine collision. Full corpus re-scan post-fix: 0 duplicate-gated parents. Re-baselined
  `duplicate_gated_finalize_plans_baseline.yaml` to `violation_count: 0` (was 6). `check_finalize_plan_coverage.py`
  (todo 1's creation-time guard) was NOT touched — it correctly scopes to "does THIS parent already have a
  `_finalize`-shaped companion" per its own separate `_gated_slugs()` logic and was not exhibiting this false-positive
  class.

  **Found-count for this todo's done-when clause: 0** (genuine duplicate-gated-finalize-plan pairs requiring
  port-then-supersede) — a valid, complete result per the todo's own text. All 3 todos in this doc are now `[x]`;
  archiving per the standard 6-step ritual in this same session.

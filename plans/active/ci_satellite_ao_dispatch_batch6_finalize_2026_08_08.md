---
doc_type: plan
title: CI satellite AO batch 6 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch6_2026_08_08.md — machine-held via depends_on + gate_on_depends: true
  until all 12 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D6-1 through D6-29) for whether their blocker has cleared, flips the 2 confirmed
  stale-checkbox items in github_actions_operator_gated_followups_2026_07_17.md and
  post_cutover_silent_assumption_sweep_2026_07_23.md that batch6's own Phase 1 audit found already-done-but-unflipped,
  and archives batch 6 via the standard 6-step ritual.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.9
estimate_calibrated_ai_days: 0.7
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch6_2026_08_08]
gate_on_depends: true
source: >-
  Authored alongside `ci_satellite_ao_dispatch_batch6_2026_08_08.md` per `plans/active/task_template.md` §4's
  finalize-plan-coverage rule. Authored `status: active` (not `draft`) per the established 2026-07-30 no-double-gate
  finding (batch4/batch5's finalize plans record the same): `gate_on_depends: true` already machine-holds every task
  here until the batch's own todos are `done`, including while the batch is still `draft` (via the derived
  `gate-upstream-open:<stem>` condition).
assigned_role: cicd
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 6 — finalize

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch6_2026_08_08]` + `gate_on_depends: true` holds
> every todo below until all 12 of batch6's own todos are `done` — this applies whether batch6 is still `status: draft`
> or has been flipped `active`. No separate flip is needed for THIS doc. `sequential: true` because todo 2's
> reconciliation needs todo 1's verification current, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 12 batch-6 todos' source docs.** Each batch-6 todo ends with `Source:` naming a
      doc. For each: flip the corresponding checkbox or annotate the corresponding prose section, citing the batch-6
      commit that shipped it — **verify the cited commit exists and is an ancestor of `origin/live-defi-rollout` before
      citing it** (`git merge-base --is-ancestor`). **Also flip the 2 confirmed-already-done-but-unflipped stale
      checkboxes batch6's own Phase 1 audit surfaced** (see D6-8, D6-9 in batch6's Deferred table): the
      ldr-docs-gate-firing verification + the codex staging-re-entry item in
      `github_actions_operator_gated_followups_2026_07_17.md` (both closed by `unified-trading-pm@97970974e` and a
      batch1 [VERIFY] P2 todo, 2026-07-26 — verify the ancestor relationship before flipping, do not trust the citation
      blind), and the F3 `cascade-qg-ordering.yml`/`sit-gate.yml` success-reporting item in
      `post_cutover_silent_assumption_sweep_2026_07_23.md` (closed by batch5's `[INFRA] P2` todo, 2026-08-07 — same
      ancestor-verify-first rule). Then, per doc, re-check whether it now has zero open work **in checkbox AND prose
      form**; only set `status: resolved` on a doc that genuinely reaches zero. **Done when**: every cited doc (batch-6
      sources plus the 2 stale-checkbox docs above) is flipped/annotated with verified evidence, and each doc that
      genuinely reaches zero open work is `status: resolved`. **DONE 2026-08-09, slot 31** — see this doc's own Progress
      Log for the full per-doc breakdown.
- [ ] [REVIEW] P1. **Re-check the Deferred items D6-1 through D6-29 for whether their blocker has cleared.** D6-1/D6-2
      (the two parked `scripts/workflow-templates/` claims) — has todo 9 landed, freeing the mechanism? If so both are
      ready-for-batch-7 extraction; note it, do NOT draft it here. D6-3 — has batch4's todo 1 landed
      (`scripts/quickmerge.sh` freed)? D6-4 through D6-14 (operator-gated) — has any received a ruling since 2026-08-08?
      D6-15 through D6-19 (time-gated/live-incident) — has the incident's own Progress Log shown resolution, or has the
      stated elapsed-time gate passed? D6-20 through D6-22 (needs-re-scoping) — has anyone supplied the missing scope
      decision? D6-23 through D6-29 (too-large/human-only) — unchanged confirmation only. **Done when**: each of D6-1
      through D6-29 has either (a) a note that it is ready for batch-7 extraction because its blocker cleared, or (b) a
      re-verified confirmation the blocker is still open. Do NOT draft follow-up todos here — this plan's scope is
      reconciliation, not fresh drafting.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch6_2026_08_08.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked follow-up (todo 2 above should have
      re-confirmed D6-1 through D6-29 — verify none silently vanishes) → add the archive banner → run the
      codex-alignment check (confirm `/codex/08-workflows/ci-cd-flow.md` and `/codex/04-architecture/ci-alerting.md`
      reflect any new contract this batch's todos established, e.g. the escalation-dispatch cooldown guard in todo 6) →
      update CLAUDE.md/codex if warranted → grep the corpus for every referrer of
      `ci_satellite_ao_dispatch_batch6_2026_08_08` and repoint each to the archived path → clear `locked_by` (already
      empty; confirm). **Done when**: the plan is in `plans/archive/2026_08/`, every corpus referrer resolves,
      `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contracts several batch-6 todos touch
- `/codex/04-architecture/ci-alerting.md` — the dedup/recovery-bookend contract todos 3, 4, 6 establish or extend
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-08** — Drafted alongside `ci_satellite_ao_dispatch_batch6_2026_08_08.md`. Authored `status: active` per the
  established no-double-gate precedent (batch4/batch5's finalize plans record the same reasoning); batch6 itself remains
  `status: draft` pending the operator's flip.
- **2026-08-09 (todo 1, slot 31)** — Reconciled all 12 batch-6 source docs plus the 2 D6-8/D6-9 stale-checkbox docs, one
  by one, verifying every cited commit is an ancestor of `origin/live-defi-rollout` (`git merge-base --is-ancestor`)
  before citing it:
  1. `issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` (todo 1) — already correctly reconciled
     (checkbox flipped + Progress Log entry present); no action needed.
  2. `issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (todo 2) — already correctly reconciled,
     `features-service@7c86a6b1` verified ancestor; no action needed.
  3. `issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (todo 3) — flipped 2 stale `[ ]` checkboxes
     (`[REVIEW] P2` allowlist-removal item citing `unified-trading-pm@917fc626a`; `[SCRIPT] P1` automation-gap item
     citing `unified-trading-pm@b073c47f9`), both verified ancestors. Doc still carries genuine open prose work
     (redeploy-to-live-VM + operator-gated throughput decision) — `status` correctly stays `open`.
  4. `issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md` (todo 4) — corrected a STALE
     citation: `c717af0fd` does not resolve to a commit in this repo (`git cat-file -e` fails — a pre-rebase SHA);
     replaced with the actual work commit `unified-trading-pm@4bd8a11d0b` (verified ancestor), matching the correction
     batch6's own plan already made for its todo 4. Doc genuinely reaches zero open checkbox+prose work but a prior
     session already documented why it deliberately stays `status: open` + `archive_exempt: true` (a line-cap/link-gate
     archival deadlock) — respected that existing reasoning rather than overriding it.
  5. `issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` (todo 5) — replaced the vague
     "unified-trading-pm@(this commit)" placeholder citation with the actual flip commit `unified-trading-pm@39e71f811`
     (found via `git log --follow`, verified ancestor). Doc still has 1 open `[INFRA] P3` item (D6-2's parked scope);
     status unchanged.
  6. `issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` (todo 6) — already correctly reconciled,
     `agent-orchestrator@a351d0d` verified ancestor; no action needed.
  7. `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (todo 7) — flipped the unchecked `[ ]`
     lag-alert-cause-per-line item, citing `unified-trading-pm@66ba7feda` (verified ancestor). Doc's other 3 open items
     stay correctly parked per batch1 D14/D15/D33 precedent; status unchanged.
  8. - 9. `plans/archive/2026_08/issues/unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md` (todos 8, 9) —
          already `status: resolved` and archived; no action needed.
  9. `ui_build_warm_cache_2026_06_17.md` (todo 10) — flipped the pnpm hardlink-store checkbox, verified
     `deployment-ui@33c6a02`, `unified-trading-system-ui@e70aeeb8`, `unified-trading-pm@e9e344a66` are all ancestors.
     This was the doc's LAST open item (sub-parts 1-2 already shipped) — zero open checkbox/prose work remains, so
     `status: active` → `complete` (`resolved` isn't a valid `doc_type: plan` status; `complete` is the plan schema's
     terminal value). Not archived (`locked_by: live-defi-rollout` is non-empty, blocking archival without an
     `[unlock-plan]` decision — out of this todo's scope).
  10. - 12. `quality_gates_quickmerge_timing_baseline_2026_07_31.md` (todos 11, 12) — todo 11's item had been converted
            to a non-checkbox digest pointer ("do the work via batch6, not here"); converted it back to a real `[x]`
            checkbox with the actual evidence + citation (`unified-trading-pm@ec01e4167`, verified ancestor) now that
            batch6 shipped it. Todo 12's item was already an `[x]` checkbox with full evidence but no commit citation;
            added one (`unified-trading-pm@7f41c4488`, verified ancestor). Doc still has 3 other open items; status
            unchanged.
  - **D6-8**: `github_actions_operator_gated_followups_2026_07_17.md` — flipped 2 stale table rows: row 14
    (`ldr-docs-gate` firing verification, citing batch1's 2026-07-26 `[VERIFY] P2` live-check evidence — no code commit,
    a pure observation) and row 5 (codex staging re-entry procedure, citing `unified-trading-pm@97970974e`, verified
    ancestor, from batch1's combined `[DOC] P2` todo). Doc has many other genuinely open rows; status unchanged.
  - **D6-9**: `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` — the F3 item is a composite (3 slices); the
    `service-deployed→deployment-service` slice was already done, and I added evidence that the
    `cascade-qg-ordering.yml`/`sit-gate.yml` slice is ALSO done (`unified-trading-pm@ead69c37d` from batch5 todo 6,
    verified ancestor). Left the outer checkbox `[ ]` — the 24-repo `semver-agent.yml schema-changed` slice remains
    genuinely open (D5-2, conflict-gated, not claimed by batch6 either). Status unchanged (doc has substantial other
    open work).
  - Net: 8 files edited (1 doc archived+resolved already, 3 docs already correctly reconciled with no edits needed). 1
    doc (`ui_build_warm_cache_2026_06_17.md`) reached zero open work and was flipped to `status: resolved`; every other
    doc retains its existing status because real open work remains, matching the todo's "only set status: resolved on a
    doc that genuinely reaches zero" instruction.

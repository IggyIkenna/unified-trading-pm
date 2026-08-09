---
doc_type: plan
title: CI satellite AO batch 5 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch5_2026_08_02.md — machine-held via depends_on + gate_on_depends: true
  until all 6 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D5-1 through D5-7) for whether their blocker has cleared, and archives batch 5 via the
  standard 6-step ritual. Carries one batch-specific check the batch itself cannot contain: confirming the cloudbuild
  drift baseline was ratcheted DOWN (never up) by todo 1's two-step rollout.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch5_2026_08_02]
gate_on_depends: true
source: >-
  Authored alongside `ci_satellite_ao_dispatch_batch5_2026_08_02.md` per `plans/active/task_template.md` §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the
  batch1/batch2/batch4 precedent. Authored `status: active` (not `draft`) per the same 2026-07-30 no-double-gate finding
  batch4's finalize records: `gate_on_depends: true` already machine-holds every task here until the batch's own todos
  are `done`, including while the batch is still `draft` (via the derived `gate-upstream-open:<stem>` condition).
assigned_role: cicd
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 5 — finalize

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch5_2026_08_02]` + `gate_on_depends: true` holds
> every todo below until all 6 of batch5's own todos are `done` — this applies whether batch5 is still `status: draft`
> (via the derived `gate-upstream-open:` condition) or has been flipped `active`. No separate flip is needed for THIS
> doc. `sequential: true` because todo 2's reconciliation cites todo 1's verification, todo 3 needs both, and todo 4
> (archival) must run last.

## Todos

- [x] ✅ [VERIFY] P1. **DONE 2026-08-09 (slot 32, cicd)** — re-ran `check_cloudbuild_template_drift.py` live against
      `origin/live-defi-rollout`: found + fixed ONE genuine post-ratchet regression (`client-reporting-api`, 3→4, an
      unclassified marker that slipped in 20 min after the 2026-08-06 ratchet). Checker now GREEN (exit 0), all 19
      consumers at-or-below baseline, all 17 image-building consumers guard-present. Full evidence below. **Confirm todo
      1's cloudbuild rollout ratcheted the drift baseline DOWN, never up, and left no consumer un-guarded.** This is the
      one check the batch itself structurally cannot make: todo 1 touches 15 repos across two ordered steps, so only a
      post-hoc pass can see the whole result. Re-run
      `.venv/bin/python scripts/quality_gates/check_cloudbuild_template_drift.py --show` and diff it against
      `scripts/quality_gates/cloudbuild_template_drift_baseline.yaml`: every count must be ≤ its 2026-07-28 seed, the
      residual non-zero counts must each map to a category-(b) "intentional permanent divergence" entry recorded in todo
      1's classification, and no repo may have been added at a NEW non-zero count. Then grep every one of the 19
      consumers' committed `cloudbuild.yaml` for the empty-tag guard and list any that lack it. **Done when**: the
      baseline diff is recorded with a per-repo before/after table, every residual is justified, and either all 19
      consumers carry the guard or the exceptions are named with reasons.
- [ ] [REVIEW] P1. **Reconcile all 6 batch-5 todos' source docs.** Each batch-5 todo ends with `Source:` naming one or
      more docs (todos 3 and 4 cite two distinct items in the SAME doc — flip them independently, not as one). For each:
      flip the corresponding checkbox or annotate the corresponding prose section in EVERY cited doc, citing the batch-5
      commit that shipped it — **verify the cited commit exists and is an ancestor of `origin/live-defi-rollout` before
      citing it** (`git merge-base --is-ancestor`). Then, per doc, re-check whether it now has zero open work **in
      checkbox AND prose form**; only set `status: resolved` on a doc that genuinely reaches zero. Note that
      `post_cutover_silent_assumption_sweep_2026_07_23.md` will NOT reach zero (its superseded/time-gated set stays open
      by design) and that `github_actions_operator_gated_followups_2026_07_17.md` may be concurrently edited by batch4's
      todo 9 — re-pull before writing. **Done when**: every cited doc is flipped/annotated with verified evidence, and
      each doc that genuinely reaches zero open work is `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the Deferred items D5-1 through D5-7 for whether their blocker has cleared.** D5-1
      (quickmerge.sh branch-check broadening) — have BOTH batch4 todo 1 and batch4 todo 2 landed? If so it is
      ready-for-batch-6 extraction; note it, do NOT draft it here. D5-2/D5-3 (F3's semver-agent and cloudbuild halves) —
      are the workflow-template rollout mechanism and the consumer `cloudbuild.yaml` files free again (batch-5 todos 4
      and 1 landed)? If so both are ready-for-batch-6. D5-4 — has the operator ruled on the billing-token fork? D5-5 —
      confirm batch4 is still the live home for D4-5..D4-18 and none has silently vanished. D5-6 — has
      `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` left `status: open`? D5-7 — has the pnpm migration
      been given its own plan? **Done when**: each of D5-1 through D5-7 has either (a) a note that it is ready for
      batch-6 extraction because its blocker cleared, or (b) a re-verified confirmation the blocker is still open. Do
      NOT draft follow-up todos here — this plan's scope is reconciliation, not fresh drafting.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch5_2026_08_02.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked follow-up (todo 3 above should have
      re-confirmed D5-1 through D5-7 — verify none silently vanishes) → add the archive banner → run the codex-alignment
      check (todo 1 changes the cloudbuild template contract and todo 4 changes the `quality-gates-v2` CI-status
      dispatch contract; confirm `/codex/08-workflows/ci-cd-flow.md` reflects both, and that the two-step "resolve
      drift, then roll out" procedure is captured as a durable contract rather than living only in this batch) → update
      CLAUDE.md/codex if any batch-5 todo established a new contract → grep the corpus for every referrer of
      `ci_satellite_ao_dispatch_batch5_2026_08_02` and repoint each to the archived path → clear `locked_by` (already
      empty; confirm). **Done when**: the plan is in `plans/archive/2026_08/`, every corpus referrer resolves,
      `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes; the shrinking-ratchet baseline convention todo
  1 above verifies
- `/codex/08-workflows/ci-cd-flow.md` — the pipeline contracts batch-5 todos 1 and 4 touch
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-02** — Drafted alongside `ci_satellite_ao_dispatch_batch5_2026_08_02.md`. Authored `status: active` per the
  no-double-gate precedent batch4's finalize records; batch5 itself remains `status: draft` pending the operator's flip.
  Todo 1 exists because batch-5's todo 1 spans 15 repos in two ordered steps, so whether the drift baseline actually
  ratcheted DOWN is only observable after the whole batch lands — the same partial-parallelism remedy batch1's finalize
  used for its three-checker registration commit.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **2026-08-09 (todo 1, slot 32 — cicd) — TODO 1 COMPLETE, ONE REGRESSION FOUND + FIXED.** Batch5's own 6 todos were
  already all `[x]` at pickup, so the `depends_on`/`gate_on_depends` gate was open. Ran
  `python3 scripts/quality_gates/check_cloudbuild_template_drift.py` (system python3 — no repo `.venv` present in this
  slot; `--show` isn't a real flag, the script's actual CLI has no such option, ran without it) against live
  `origin/live-defi-rollout` state, workspace-root pointed at this slot:
  - **Initial run: EXIT 1 (RED).** `client-reporting-api` reported 4 drift markers > baseline 3 — an over-baseline
    regression, not a baseline violation (the YAML baseline value itself was never raised). Root-caused via
    `git log -S _RUN_INIMAGE_QG` + `git show`: commit `client-reporting-api@99171ca` (2026-08-06 18:06:56Z, "fix(ci):
    tag built image
    :$$SAFE_SHA...") landed **20 minutes after** the batch5-todo-1 baseline ratchet commit
    (`unified-trading-pm@46ecaded`, 17:47:08Z) and, while legitimately re-pointing the build tag to `$$SAFE_SHA`(matches`cloudbuild-api-template.yaml`, correct), ALSO accidentally carried over an unrelated SERVICE-template-only `_RUN_INIMAGE_QG`skip-guard into this API-template consumer's`quality-gates`step — 4 lines of guard logic + a substitution declaration + a tag/script-invocation change, none of which exist in`configs/cloudbuild-api-template.yaml`. Confirmed via corpus-wide grep that nothing ever sets `_RUN_INIMAGE_QG=true`for this repo (no trigger config references it) — the guard was dead code, safe to remove with zero behavior change (falls back to the pre-existing unconditional QG invocation the template still specifies). **Fixed**: reverted the`quality-gates`step in`client-reporting-api/cloudbuild.yaml`to match`cloudbuild-api-template.yaml`exactly (unconditional`docker
    run`, `:$SHORT_SHA`tag,`bash scripts/quality-gates.sh --no-fix
    --quick`), keeping the legitimate `:$$SAFE_SHA`build-tag fix untouched. Verified: valid YAML,`check_cloudbuild_substitutions.py
    --repo
    client-reporting-api`clean, repo`quality-gates.sh`green (sentinel matches committed HEAD). Shipped`client-reporting-api@b75b798`(QG Pass-1 green, quickmerge Pass-2 landed,`git
    merge-base --is-ancestor`verified on`origin/live-defi-rollout`).
  - **Re-run after fix: EXIT 0 (GREEN).**
  - **Per-repo before/after table** (2026-07-28 seed → 2026-08-06 ratcheted baseline → this session's live re-measure):

    | Repo                              | 07-28 seed | baseline (post-ratchet) | live before fix | live after fix | verdict                                                                  |
    | --------------------------------- | ---------: | ----------------------: | --------------: | -------------: | ------------------------------------------------------------------------ |
    | alerting-service                  |         10 |                       8 |               8 |              8 | OK (== baseline)                                                         |
    | batch-live-reconciliation-service |          9 |                       9 |               9 |              9 | OK (== baseline)                                                         |
    | client-reporting-api              |          5 |                       3 |           **4** |              3 | **FIXED** (was over-baseline, unclassified `_RUN_INIMAGE_QG` regression) |
    | deployment-api                    |         26 |                      16 |              16 |             16 | OK (== baseline)                                                         |
    | deployment-ui                     |          0 |                       0 |               0 |              0 | OK (== baseline)                                                         |
    | e2e-testing                       |          0 |                       0 |               0 |              0 | OK (== baseline)                                                         |
    | execution-service                 |         10 |                      10 |              10 |             10 | OK (== baseline)                                                         |
    | features-service                  |         12 |                      12 |              12 |             12 | OK (== baseline)                                                         |
    | fund-administration-service       |          6 |                       5 |               5 |              5 | OK (== baseline)                                                         |
    | greeks-service                    |         10 |                       5 |               5 |              5 | OK (== baseline)                                                         |
    | ibkr-gateway-infra                |          4 |                       0 |               0 |              0 | OK (== baseline)                                                         |
    | instruments-service               |          7 |                       7 |               7 |              7 | OK (== baseline)                                                         |
    | market-data-processing-service    |          6 |                       5 |               5 |              5 | OK (== baseline)                                                         |
    | market-tick-data-service          |          8 |                       8 |               8 |              8 | OK (== baseline)                                                         |
    | ml-service                        |          9 |                       8 |               8 |              8 | OK (== baseline)                                                         |
    | strategy-service                  |         13 |                       8 |               8 |              8 | OK (== baseline)                                                         |
    | system-integration-tests          |          0 |                       0 |               0 |              0 | OK (== baseline)                                                         |
    | trading-agent-service             |          9 |                       8 |               8 |              8 | OK (== baseline)                                                         |
    | unified-trading-system-ui         |          0 |                       0 |               0 |              0 | OK (== baseline)                                                         |

    Every current baseline value is ≤ its 2026-07-28 seed (confirmed the ratchet moved DOWN or stayed, never up) and,
    after the client-reporting-api fix, every live count matches its baseline exactly — no repo silently drifted past
    what the baseline already records, and no repo's baseline was itself ever raised in the YAML (verified via `git log`
    on `cloudbuild_template_drift_baseline.yaml` — its only two edits are the 2026-07-28 seed and the 2026-08-06
    ratchet-down). Residual non-zero counts (14 repos) all map to the category-(b) intentional-divergence set recorded
    in the baseline file's own `note:` field and in batch5 todo 1's 2026-08-06 Progress Log entries (operability-probe /
    gar_token BuildKit-secret variant / deployment-api's bespoke deploy steps / per-repo dep-skew gates / SCM-arg form
    variants) — no new unclassified residual beyond the one found+fixed above.

  - **Empty-tag guard presence** — grepped all 19 consumers' committed `cloudbuild.yaml` for `SAFE_SHA`: **17/17
    image-building consumers carry it** (alerting-service, batch-live-reconciliation-service, client-reporting-api,
    deployment-api, deployment-ui, execution-service, features-service, fund-administration-service, greeks-service,
    ibkr-gateway-infra, instruments-service, market-data-processing-service, market-tick-data-service, ml-service,
    strategy-service, trading-agent-service, unified-trading-system-ui). **2 exceptions, both legitimate N/A**:
    `e2e-testing` and `system-integration-tests` are lint+smoke test-harness repos with no Docker image / no push step
    (confirmed by reading both `cloudbuild.yaml` files — "Test-harness repo: lint + smoke tests only. No Docker image,
    no push." — matches the 2026-08-06 slot-15 Progress Log note that sit repos are N/A for this guard). So: all
    applicable consumers are guarded; the two non-applicable ones are named with reasons, per the todo's done-when.
  - **Done-when met**: baseline diff recorded with the per-repo before/after table above; every residual justified; all
    17 image-building consumers carry the guard, the 2 non-applicable ones are named with reasons. Evidence:
    `client-reporting-api@b75b798` (fix, verified ancestor of origin), drift checker EXIT 0 post-fix.

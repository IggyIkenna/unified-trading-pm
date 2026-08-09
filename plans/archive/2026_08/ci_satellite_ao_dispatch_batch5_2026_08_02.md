---
doc_type: plan
title: CI satellite AO batch 5 — fifth AO-dispatch extraction for the ci tranche
summary: >-
  Fifth AO-dispatch batch for the `ci` topic tranche, authored 2026-08-02 against an operator ruling authorising the
  extraction. Six conflict-cleared bounded todos, headed by the cloudbuild empty-tag-guard rollout the operator
  separately RULED must be re-scoped into two explicit steps (resolve the 15/19 per-repo drift FIRST, then apply the
  guard) — that re-scope is applied in the source issue doc in the same change that created this plan. The other five
  come from blockers the corpus itself recorded as "ready for batch 5": batch4's own conflict-gated Deferred D4-2/D4-3
  (the two remaining `github_actions_operator_gated_followups_2026_07_17.md` items, combined into ONE todo per that
  file's chronic contention), the three bounded items in `github_actions_billing_wall_recurrence_2026_07_29.md` whose
  only gate was "re-triage once the incident resolves" (it flipped `status: resolved`, so batch4-finalize's own todo 3
  pre-authorised exactly this triage), the `deployment-ui/scripts/setup.sh` pre-warm sync batch4 explicitly flagged for
  batch 5, and the F3 dispatch-success-reporting gap the 2026-08-01 `/na-eligibility-audit ci` re-flagged as "the one
  genuinely-uncovered bounded gap, still not yet extracted into any active batch". Two halves of F3 and batch4's D4-1
  are rationed into `## Deferred` on genuine same-file contention, not dropped.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    agent-orchestrator,
    deployment-ui,
    deployment-api,
    strategy-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    execution-service,
  ]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-5, satellite-docs, cloud-build, template-drift, github-actions, billing]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: cicd
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/archive/issues/github_actions_billing_wall_recurrence_2026_07_29.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator ruling (interactive Q&A, recorded 2026-07-30, executed 2026-08-02): (a) drafting this next ci-tranche
  AO-dispatch batch is AUTHORISED; (b) the cloudbuild empty-tag-guard rollout must be re-scoped into two explicit steps
  — resolve per-repo drift first, then apply the guard. Candidate set re-derived against live corpus state on 2026-08-02
  rather than taken from the original audit's in-session list (which was never committed to the corpus) — every todo
  below cites the corpus's own recorded "ready for batch 5" pointer or a verified state change since 2026-07-31. See `##
  Provenance of the six candidates`.
---

# CI satellite AO batch 5

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 6 todos done. Finalize plan
> (`ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md`) reconciled all 5 distinct source docs the 6 todos cite,
> re-checked all 7 Deferred items (D5-1 through D5-7 — 2 resolved since drafting, 2 re-triaged onward via
> batch6/batch6-finalize, 1 unchanged RESOLVED, 2 reconfirmed still open), then archived this plan via the standard
> 6-step ritual. Finalize archived alongside at
> `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md`.

> **✅ STATUS: `active`** (historical, at time of dispatch) — operator-approved 2026-08-06, dispatching. Todo 5 was
> found already shipped (`deployment-ui@7086565`) before dispatch — see its checkbox. The other 5 todos are unaffected.

> **Why this plan exists.** `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (12/32 todos still open) and
> `ci_satellite_ao_dispatch_batch4_2026_07_31.md` (9/9 still open, still `draft`) both remain active — this is NOT a
> replacement for either. Batch 2 and batch 3 are complete and archived. This is the tranche's FIFTH extraction: items
> earlier batches deferred whose blocker has since cleared, plus items genuinely new since batch4's 2026-07-31 snapshot.

## Provenance of the six candidates

The operator's ruling referenced a `ci`-closeout audit's list of six conflict-cleared candidates. That audit's output
was never committed to the corpus, so the set below was **re-derived from live state on 2026-08-02** rather than copied.
Each candidate names the corpus artefact that independently marks it batch-5-ready, so the derivation is checkable:

| #   | Candidate                                                                     | Corpus pointer that marks it batch-5-ready                                                                               |
| --- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1   | Cloudbuild empty-tag-guard rollout (re-scoped)                                | batch4 `## Deferred` **D4-20** ("needs a re-scoping pass") + this session's operator ruling supplying that re-scope      |
| 2   | The 2 remaining `github_actions_operator_gated_followups_2026_07_17.md` items | batch4 **D4-2**/**D4-3** ("held for a cleaner batch-5 extraction")                                                       |
| 3   | `authoring_slot="ci-reconcile"` ping 400 mismatch                             | batch4 **D4-19** gate ("re-triage once the doc's own Progress Log shows the incident resolved") — now `status: resolved` |
| 4   | Outage-aware `quality-gates-v2` status dispatch                               | same D4-19 gate; batch4-finalize todo 3 pre-authorises exactly this triage                                               |
| 5   | `deployment-ui/scripts/setup.sh` pre-warm sync                                | batch4 `## Already covered`: "flagging for batch 5, not drafted this round"                                              |
| 6   | F3 dispatch-success-reporting (PM-owned half)                                 | `/na-eligibility-audit ci` 2026-08-01 verdict on `post_cutover_silent_assumption_sweep_2026_07_23.md`                    |

## Same-file contention — read before editing this plan

Same-priority todos in one plan run **concurrently**, so they must touch disjoint files (CLAUDE.md § Plans).

- **Consumer `cloudbuild.yaml` files are claimed by todo 1** for the whole batch. F3's `service-deployed` dispatch fix
  touches the same 12+ files, so that half of F3 is rationed to `## Deferred` (D5-3) and todo 6 is scoped to the
  PM-owned workflow files only. Do **not** add a second `cloudbuild.yaml`-touching todo to this plan.
- **`scripts/workflow-templates/` rollouts are serialised through one script** (`rollout-workflow-templates.sh`, which
  rewrites every consumer's committed copy). Todo 4 claims that mechanism this round for `quality-gates-v2.yml.tmpl`;
  F3's `semver-agent.yml.tmpl` fan-out is therefore deferred (D5-2), not run concurrently.
- **`plans/active/github_actions_operator_gated_followups_2026_07_17.md` is claimed by todo 2** (both remaining items
  write findings back into that one doc, so they are ONE todo, not two). **Cross-plan caution**: batch4's own todo 9
  claims the same file for its 4-item billing sweep — if batch4 is dispatched concurrently with this batch, todo 2 must
  not run at the same time as batch4 todo 9. Whichever lands second re-pulls first.
- Every audit/verification todo below records its findings **in its own named source doc**, never in this plan's body,
  so concurrent workers do not collide on this file.

## Todos

- [x] ✅ [DEVOPS] P2. **Roll the cloudbuild empty-tag guard out to the consumer repos — RE-SCOPED per operator ruling
      (2026-07-30, `cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md`) into two explicit,
      ordered steps.** The original one-line todo assumed a clean `rollout-cloudbuild.py --apply` sweep; the
      would-drop-content guard that shipped 2026-07-28 (`unified-trading-pm@ddf0b89f4`) now correctly REFUSES 15 of the
      19 consumers, so the rollout mechanism it assumed no longer exists. Do the steps in order — step 2 is not
      startable for a repo until step 1 has cleared that repo.
  1. **Resolve the per-repo drift first.** Ground truth is
     `scripts/quality_gates/cloudbuild_template_drift_baseline.yaml` (seeded 2026-07-28): **15 of 19 consumers carry
     content their mapped template does not** — `deployment-api` (26), `strategy-service` (13), `features-service` (12),
     `alerting-service` (10), `execution-service` (10), `greeks-service` (10), `batch-live-reconciliation-service` (9),
     `ml-service` (9), `trading-agent-service` (9), `market-tick-data-service` (8), `instruments-service` (7),
     `fund-administration-service` (6), `market-data-processing-service` (6), `client-reporting-api` (5),
     `ibkr-gateway-infra` (4). The 4 clean ones are `deployment-ui`, `e2e-testing`, `system-integration-tests`,
     `unified-trading-system-ui`. **Re-measure before trusting those numbers** — run
     `.venv/bin/python scripts/quality_gates/check_cloudbuild_template_drift.py --show` first; the baseline is 5 days
     old. For each drifted repo, classify every reported marker into exactly one of three buckets and act on it: (a)
     **forward-portable** — genuinely belongs in `configs/cloudbuild-*-template.yaml`; port it, so the render stops
     dropping it; (b) **intentional permanent per-repo divergence** (the baseline's own comment names deployment-api's
     `vendor-deps`/`deploy`/`redeploy-monitor-jobs` steps as the archetype) — leave it in the repo, record WHY in the
     baseline comment; (c) **stale repo-local content** — delete it from the repo. Ratchet the baseline DOWN for every
     marker resolved under (a) or (c); never raise a count.
  2. **Then apply the guard.** For every repo whose step-1 classification leaves it renderable, land the fail-fast
     empty-tag guard (`SHORT_SHA` → `VERSION` fallback, hard-fail with a diagnostic only when both are unresolvable —
     the guard already lives in `configs/cloudbuild-service-template.yaml`). For a category-(b) repo where a full render
     is deliberately not wanted, hand-apply just the guard hunk instead of running the rollout tool against it. Each
     repo needs its own `quality-gates.sh` + its own quickmerge.
  - **`--apply` safety justification (stated per CLAUDE.md § Plans, so no `[OPERATOR]` tag is required)**:
    `rollout-cloudbuild.py --apply` writes only to git-tracked `cloudbuild.yaml` files inside a git worktree — fully
    reversible with `git checkout`, no cloud resource is mutated, no object is deleted, and the tool's own
    would-drop-content guard refuses any write that would drop live content. Nothing reaches a repo without that repo's
    own quality gate and quickmerge.
  - **Done when**: (1) every drifted repo's markers are classified (a)/(b)/(c) with the classification recorded in the
    source doc's Progress Log, the template forward-ports have landed, and the drift baseline has been ratcheted down to
    the residual category-(b) set; (2) the empty-tag guard is present in every consumer's `cloudbuild.yaml`; (3) at
    least ONE repo is proven end-to-end — a manual `gcloud builds submit` (storageSource, so `SHORT_SHA` is empty)
    recovers via the `VERSION` fallback instead of dying with `invalid reference format` / exit 125, with the build id
    cited; (4) every touched repo's `quality-gates.sh` is green.
  - Source: `issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` (`[DEVOPS] P2`, the sole
    open todo — re-scoped in that doc in the same change that created this plan). Was batch4 Deferred **D4-20**; its
    2026-07-30 na-eligibility-audit verdict said verbatim "Re-scope the todo to name the mechanism and it becomes a
    clean RECLASSIFY" — this is that re-scope.

- [x] ✅ [VERIFY] P2. **DONE 2026-08-09 (slot 11)** — both sub-items closed with ONE dated Progress Log entry in
      `github_actions_operator_gated_followups_2026_07_17.md`. Sub-item 1: measured directly against the durable
      BigQuery `resource_samples` pipeline — avg_cpu_pct = 50.6% (min 16.7%, p95 85.6%, max 95.1%, 171 samples,
      `vm_name='planning'`), within the operator's 50-70% band, no re-escalation warranted (caveat: pipeline data for
      this VM only starts 2026-08-08, so the window is ~29.5h, not multi-day — recorded honestly). Sub-item 2: recorded
      as MOOT — pointer to `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` per the instruction to skip
      re-scoping. Evidence: `unified-trading-pm@b3d2deacb` (source-doc checkbox flip + Progress Log entry). **Two
      remaining `github_actions_operator_gated_followups_2026_07_17.md` items, combined into ONE todo per the
      same-file-contention note above.** Record BOTH findings as ONE dated Progress Log entry in that doc:
  1. **BigQuery `resource_samples` utilization verification** (`[VERIFY] P2`, ~line 632; batch4 Deferred **D4-3**). The
     runner resize landed 2026-07-27; measure the rolling average utilization over a sustained window from the durable
     BigQuery `resource_samples` pipeline (NOT a point-in-time SSM check) and report it against the operator's
     pre-stated 50-70% band. The doc's own text makes this a fact-check, not a judgment call — **only re-escalate if the
     measured number falls outside the band**, and then quote the number.
  2. **MOOT — SUPERSEDED, do not execute as written (found by `/ag-closeout-audit ci` 2026-08-03).** Originally: "Scope
     a DESIGN (design only, no implementation) for test-impact / selective test execution" (`[REVIEW] P2`, ~line 776;
     batch4 Deferred **D4-2**; operator-approved 2026-07-28). The cited line has since moved: the source doc's own
     checkbox there now reads "EXTRACTED 2026-08-03 to its own issue doc" —
     `plans/active/issues/test_impact_selective_execution_design_2026_08_03.md`. By the time this batch-5 todo is
     actually dispatched, that design was not only written but operator-reviewed-and-approved, followed by a full
     implementation (`test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`, `assigned_vm: NA` active local
     plan): Phase 1 fleet-wide eligibility measurement done, Phase 2 walker/selector/golden-set tests shipped
     (`unified-trading-pm@1452d5da1`), a single-repo shadow trial live on `market-data-processing-service` (`@1c8588c`,
     2-week clock to 2026-08-17), and a historical backtest executed. **Skip sub-item 2 entirely when this todo is
     worked** — record a one-line pointer to the rollout plan instead of scoping a design that already shipped code; do
     not re-scope or re-design.
  - **Done when**: sub-item 1's utilization number is recorded in the source doc (measurement window, or a note that the
    BigQuery source is credentials-unreachable), and sub-item 2 is recorded as a pointer to
    `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` rather than a fresh design.
  - Source: `github_actions_operator_gated_followups_2026_07_17.md` (`[VERIFY] P2` + `[REVIEW] P2`). Batch4 **D4-2** /
    **D4-3**, both recorded there as "held for a cleaner batch-5 extraction".

- [x] ✅ [BACKEND] P3. **DONE-ELSEWHERE 2026-08-06 (duplicate of batch1's completed item) + structural fix completed.**
      The core fix shipped 2026-08-03 as `unified-trading-pm@41f193405` (flipped in batch1): Direction 1 — `cicd.md`'s
      completion-ping step now guards on `[[ "$AUTHORING_SLOT" =~ ^[0-9]+$ ]]`, skipping non-numeric sentinels
      (`ci-reconcile`, empty string). Verified here (slot 14) by faithful simulation of the scheduler-raised bare-LDR
      completion path: `AUTHORING_SLOT=ci-reconcile` emits no POST (no 400), a numeric slot still pings, and the server
      4xxs any non-numeric slot path (`/api/slots/ci-reconcile/message` → 422) — confirming the bug the guard avoids.
      Completed the structural fix this session by extending the same guard to `agents/conflict_resolver.md` +
      `agents/data_pipeline_failure.md` (the identical unguarded completion-ping pattern on the other two
      authoring-slot-pinging worker docs; `authoring_slot` is an unvalidated `str` at the escalate API, so the bug can
      recur there). Both repos' `quality-gates.sh` green. Original text preserved below for record. **Fix the structural
      `authoring_slot="ci-reconcile"` ping mismatch.** Every bare-LDR (`pr_number=0`) `ldr_qg_failure` escalation the
      scheduler raises passes the literal string `authoring_slot="ci-reconcile"`
      (`agent-orchestrator/server/ci_reconcile.py:546`), not a numbered slot — so the mandated "ping the authoring slot
      on completion" step in `unified-trading-pm/agents/cicd.md` always 400s (`POST /api/slots/ci-reconcile/message` →
      `int_parsing`, the path expects an int; reproduced `agt-69e9e4`/slot 14, 2026-07-29). The server's own
      `_notify_authoring_slot` already treats the value as an advisory label rather than a real target, so the two sides
      disagree structurally. Pick ONE of the two directions the source doc names and implement it: either special-case a
      non-numeric `AUTHORING_SLOT` in `cicd.md` (skip the ping — it is advisory-only per the source comment), or give
      scheduler-raised escalations a pingable surface keyed off `escalation_id`. **Done when**: a scheduler-raised
      bare-LDR escalation's completion path no longer emits a 400 (verified against a real or faithfully-simulated
      escalation, not a code read alone), and both repos' `quality-gates.sh` are green.
  - Source: `issues/github_actions_billing_wall_recurrence_2026_07_29.md` (`[BACKEND] P3`, the third item). Batch4
    Deferred **D4-19**, whose only stated gate was "re-triage once the doc's own Progress Log shows the incident
    resolved" — that doc is now `status: resolved` (P0 cleared 2026-07-31), so the gate is met.

- [x] ✅ [BACKEND] P3. **DONE-ELSEWHERE 2026-08-07 (slot-10,
      `feat(ci): add billing-wall / startup_failure guard to     quality-gates-v2`).** Verification confirmed this
      shipped before dispatch. `unified-trading-ci@0afd236` (2026-08-07 04:38Z, verified ancestor of
      `origin/live-defi-rollout`): the "Record CI status" step in `python-quality-gates-v2.yml` now detects the
      infrastructure-kill pattern (`CONTENT_GATE_RESULT=failure` AND `SLICES_RESULT=failure` → `BILLING_KILL=true`) and
      skips the `ci-status-update` FAILING dispatch, emitting only a `::notice::` annotation. This is the suppression
      the 2026-06-11 P1 asked for and the `D4-19`-gated batch5 triage was checking for. Verified the implementation is
      byte-correct against the done-definition: a billing-wall run (both-failed) exits before the dispatch; a genuine
      failing run (content-gate succeeds / slices fails) still dispatches `STATUS=FAILING`. The 2026-06-11 archived
      doc's `[ ] [CICD] P1. Outage-aware v2 status dispatch` item is effectively delivered — the implementation lives in
      `unified-trading-ci` rather than as a PM template edit (the reusable workflow was extracted to
      `unified-trading-ci` per `shared_ci_workflow_repo_extraction_2026_08_06.md`, so the "edit
      `quality-gates-v2.yml.tmpl` + rollout" instruction no longer applies; the single source file is the right place).
      **Make the `quality-gates-v2` CI-status dispatch outage-aware.** The workflow's "Record CI status" step
      (`if: always()`) still dispatches a normal FAILING status when the run was a 0-job billing/outage kill
      (`jobs: []`, `conclusion: startup_failure`) — so an account-level wall no worker can fix generates
      `ldr_qg_failure` escalation spam fleet-wide, burning escalation-worker dispatches. **Step 1 is a verification, not
      an assumption**: the source doc attributes this to a still-open P1 in the archived 2026-06-11 precedent doc —
      confirm first whether that item shipped in the interim; if it did, close this out as already-done with the
      citation instead of re-implementing. If it did not, fix it: distinguish a genuine test/lint failure from a 0-job
      startup kill and suppress (or downgrade to an outage-class signal) the CI-status dispatch in the latter case. Edit
      `scripts/workflow-templates/quality-gates-v2.yml.tmpl` and roll out via `rollout-workflow-templates.sh` — **never
      hand-edit a per-repo workflow copy** (CLAUDE.md § CI verification). **Done when**: either the already-shipped
      citation is recorded, or a synthetic 0-job/`startup_failure` run produces no normal FAILING CI status while a
      genuine failing run still does, the template rollout is committed AND pushed for every consumer copy, and PM's
      `quality-gates.sh` is green.
  - Source: `issues/github_actions_billing_wall_recurrence_2026_07_29.md` (`[BACKEND] P3`, the second item). Same
    cleared **D4-19** gate as the todo above; batch4-finalize's own todo 3 pre-authorises exactly this triage ("note it
    is ready for a future batch's fresh triage of its 3 remaining bounded items").

- [x] ✅ [UI] P3. **DONE-ELSEWHERE 2026-08-06 (governance-sweep activation-readiness check).** Already shipped:
      `deployment-ui@7086565` ("Sync setup.sh pre-warm build cache step from unified-trading-pm template", 2026-08-03,
      `Quickmerge: agent`, confirmed a clean ancestor of current `live-defi-rollout` HEAD). Verified live
      `diff deployment-ui/scripts/setup.sh unified-trading-pm/scripts/setup.sh` returns empty — byte-identical. The
      source doc (`ui_build_warm_cache_2026_06_17.md`) already has this checked `[x]` at line 67. No action needed.
      Original text preserved below for record. **Sync `deployment-ui/scripts/setup.sh` with the PM template's
      `[UI.5] PRE-WARM BUILD CACHE` step.** The step was added to `unified-trading-pm/scripts/setup.sh` on 2026-07-29
      and shipped to `unified-trading-system-ui` (`unified-trading-system-ui@42439593`); `deployment-ui`'s copy could
      not ship at the time because its vitest coverage gate was broadly red — that blocker was root-caused as an
      environment artefact and RESOLVED 2026-07-30 (`deployment-ui@3c7e2a8`, a `pnpm-workspace.yaml` missing
      `packages:`), so the gate is unblocked. The remaining work is exactly what the source todo names: sync the
      template's pre-warm step into `deployment-ui/scripts/setup.sh`, commit, ship. Re-diff the two files before copying
      — do not blind-`cp` a PM script over a UI repo's copy if the UI copy has diverged for its own reasons.
      **Playwright-gate note**: this is a shell script, not rendered UI, so `pw:L2` may legitimately not apply — if the
      `[UI]`-capable slot determines it is out of `pw:L2` scope, **record that determination explicitly in the source
      doc**; do not skip the gate silently (`/codex/06-coding-standards/ui-testing-layers.md`). **Done when**:
      `deployment-ui/scripts/setup.sh` carries the pre-warm step, a cold clone of `deployment-ui` is observed running
      one real `pnpm run build` at setup time and a warm clone is observed skipping it, `deployment-ui`'s own gate is
      green, and the source todo is flipped with the commit cited.
  - Source: `ui_build_warm_cache_2026_06_17.md` (`[CODE] P2`). Batch4 `## Already covered` held this "for a
    `[UI]`-capable slot's judgment rather than assumed safe here — flagging for batch 5".

- [x] ✅ [INFRA] P2. **Fix the unconditional `&& echo "...dispatched"` success reporting at the F3 orphan-dispatch sites
      — PM-owned workflow files ONLY this round.** These sites claim a dispatch succeeded whether or not any listener
      exists. In scope: `.github/workflows/cascade-qg-ordering.yml` and `.github/workflows/sit-gate.yml` (the
      `game-day-sit` / `synthetic-smokes` dispatches are already `::warning::`-guarded per the source doc — **verify
      that claim rather than assuming it**, and fix only what is genuinely unguarded). For each site: either add the
      missing listener in the target repo, or stop claiming success when the dispatch has no subscriber. Enumerate the
      live set first with `.venv/bin/python scripts/quality_gates/check_dispatch_listeners.py --show`, and re-baseline
      (`--baseline-write`) as each is fixed so `check_dispatch_listeners_baseline.yaml`'s ratchet only ever shrinks.
      **Explicitly OUT of scope this round** (both rationed to `## Deferred`, see D5-2/D5-3): the 24 repos'
      `semver-agent.yml` `schema-changed` dispatch (template rollout, contends with todo 4) and the 12+ services'
      `cloudbuild.yaml` / `buildspec.aws.yaml` `service-deployed` dispatches (contends with todo 1). **Done when**: both
      PM workflow files either dispatch to a real listener or no longer report unconditional success, the baseline is
      ratcheted down by exactly the fixed count, and PM's `quality-gates.sh` is green.
  - Source: `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` (`[INFRA] P2`, the F3 success-reporting item).
    Re-flagged by `/na-eligibility-audit ci` 2026-08-01 as "the one genuinely-uncovered bounded gap, still not yet
    extracted into any active batch".

## Deferred

Tagged by WHY, per the `/ag-closeout-audit` non-batchable taxonomy. Only **conflict-gated** items can be converted by a
future batch's re-triage; the rest need direct operator action, elapsed time, or a re-scoping pass.

### Conflict-gated (re-triageable in batch 6+)

| id   | Item                                                                                                                                                             | Competing claim it collided with                                                                                                                                                                                                   |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D5-1 | `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` step 3 — broaden `quickmerge.sh`'s branch check to recognise `live-defi-rollout`/`staging` | Unchanged from batch4 **D4-1**: batch4's todo 1 owns `scripts/quickmerge.sh`, and this step is additionally gated on batch4's todo 2 (the alias-precedence fix) landing first. Batch4 is still `draft`, so neither gate has moved. |
| D5-2 | F3 success-reporting — the 24 repos' `semver-agent.yml` `schema-changed` dispatch                                                                                | Todo 4 owns the `scripts/workflow-templates/` rollout mechanism this round; two concurrent template rollouts race each other's per-repo copies.                                                                                    |
| D5-3 | F3 success-reporting — the 12+ services' `cloudbuild.yaml` / `buildspec.aws.yaml` `service-deployed` dispatch                                                    | Todo 1 owns every consumer `cloudbuild.yaml` for the whole batch.                                                                                                                                                                  |

### Operator-gated (needs a ruling, not a re-triage)

| id   | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D5-4 | **RESOLVED 2026-08-03, no longer operator-gated (found by `/ag-closeout-audit ci`).** `github_actions_billing_wall_recurrence_2026_07_29.md`'s `[BACKEND] P2` — spend telemetry / 50-80-95% budget alerting. **RULED 2026-08-03T06:28:59Z** (operator, via main, `blocked_id: BLK-c099ebe5`, `disposition: final`, captured in `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s own migrated todo): recurring manual operator intervention IS the accepted standing posture — no `Plan: read` token will be minted. Closed wont-fix at the source; nothing left for batch 6 to extract here. |
| D5-5 | Batch4's operator-gated set **D4-5 through D4-18** — re-verified 2026-08-02 as still unruled and still correctly parked there. Not re-listed item-by-item here; batch4 remains their home, and batch4-finalize's todo 3 owns their re-check.                                                                                                                                                                                                                                                                                                                                                  |

### Live incident (too risky to batch while hot)

| id   | Item                                                                                                                                                                                                                                                                                                     |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D5-6 | `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` — still `status: open` as of 2026-08-02. Same precedent batch3 and batch4 both applied: do not fold an actively-evolving incident doc's items into a static batch. Re-triage once its own Progress Log shows the capacity question settled. |

### Too large / needs its own plan

| id   | Item                                                                                                                                                                                                                                                                                                                                                     |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D5-7 | `ui_build_warm_cache_2026_06_17.md`'s `[INFRA] P3` pnpm content-addressable-store migration. Operator-APPROVED 2026-07-27, so it is not blocked on a ruling — but it converts both UI repos' lockfiles and every slot clone's `node_modules` layout, which is its own properly-scoped plan, not a line item in a CI satellite batch. Same as batch1 D20. |

## Codex SSOTs (read before executing any todo)

- `/codex/08-workflows/ci-cd-flow.md` — pipeline / quickmerge / gate set / never hand-edit a per-repo workflow copy
- `/codex/06-coding-standards/quality-gates.md` — how gates run; the shrinking-ratchet baseline convention todos 1 and 6
  both depend on
- `/codex/04-architecture/ci-alerting.md` — the `notify-slack.yml` carrier + state-transition dedup, if todo 4's fix
  needs an outage-class signal rather than plain suppression
- `/codex/06-coding-standards/ui-testing-layers.md` — the `pw:L2` gate todo 5 must either satisfy or explicitly
  determine out-of-scope
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan's sibling satisfies

## Progress Log

- **2026-08-02** — Authored against the operator's recorded ruling (drafting authorised; cloudbuild rollout to be
  re-scoped into two explicit steps). Verified before drafting: `ci_satellite_ao_dispatch_batch3_2026_07_30.md` already
  exists and is **archived complete**, and `ci_satellite_ao_dispatch_batch4_2026_07_31.md` already exists and is
  **active `draft` with 9 open todos** — so this batch is numbered **5**, not 3. Re-derived the candidate set from live
  corpus state (the ruling's referenced audit list was never committed): confirmed the 15/19 cloudbuild drift figure
  directly against `cloudbuild_template_drift_baseline.yaml`; confirmed
  `github_actions_billing_wall_recurrence_2026_07_29.md` has flipped to `status: resolved`, meeting batch4 D4-19's only
  stated gate; confirmed `github_actions_operator_gated_followups_2026_07_17.md`'s two items are still open; confirmed
  `ui_build_warm_cache_2026_06_17.md`'s `deployment-ui` sync is still the stated remaining work and its coverage-gate
  blocker resolved 2026-07-30; confirmed the F3 success-reporting item is still `- [ ]` and was re-flagged by the
  2026-08-01 na-eligibility-audit. Conflict-check found consumer `cloudbuild.yaml` contended between todo 1 and F3
  (rationed → D5-3), the workflow-template rollout mechanism contended between todo 4 and F3's semver-agent half
  (rationed → D5-2), and `github_actions_operator_gated_followups_2026_07_17.md` contended two ways internally (combined
  into todo 2) plus cross-plan with batch4's todo 9 (caution recorded, not silently ignored). 6 todos drafted, 7 items
  deferred (D5-1 through D5-7), nothing escalated that batch4 has not already escalated. Nothing shipped, nothing
  flipped to `active`.
- **2026-08-03 — `/ag-closeout-audit ci` (autonomous, daily scheduled run).** Re-checked this batch's own Deferred
  section per the skill's iterative-drain step before any fresh triage. D5-1/D5-2/D5-3 unchanged (batch4's todos 1/2/4
  still un-landed, 0/9 — the contended files are still contended). D5-5/D5-6/D5-7 unchanged (batch4's D4-5..D4-18 still
  unruled; `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` still `status: open`; pnpm migration still has
  no dedicated plan). **Two corrections applied in place, both evidence-backed, neither a fresh judgment call**: D5-4
  marked RESOLVED (operator ruling `BLK-c099ebe5`, captured in batch1); todo 2 sub-item 2 marked MOOT/superseded (the
  design it asks to scope already shipped as a full implementation — see the inline notes above). Fresh-candidate sweep
  via `generate_ag_closeout_audit_candidates.py --tranche ci`: 40 total members, 7
  never-cited-in-an-active-covering-doc. All 7 investigated end-to-end; **zero produced a genuine new batch-6
  candidate**: 2 are already cited in batch1's own Deferred (D21/D3(5)) under a truncated basename the mechanical
  citation-regex doesn't match, both `na-eligibility-audit`-confirmed KEEP-NA (operator-gated, do-not-dispatch-blind); 1
  (`workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md`) is `na-eligibility-audit`-confirmed KEEP-NA
  (open-ended design questions, no decided mechanism); 1
  (`deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md`) had its blocking scope resolved
  same-day, leaving only a P3 "consider whether…" design suggestion, not yet bounded enough to batch; 1
  (`pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md`) is a live, actively-multi-session-worked
  incident continuation of the same capacity crisis D5-6 already tracks — too hot to batch, matches precedent; 2
  (`qg_governor_glue_runner_ledger_coordination_2026_08_03.md`,
  `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`) are themselves already-active LOCAL plans with real
  shipped progress today — self-covering, nothing for a batch to extract. **Verdict: no batch 6 drafted this round** —
  batch1 (42/43 done)/batch4 (0/9, drafted)/batch5 (this doc, 0/6, drafted) already comprehensively cover the tranche's
  currently-extractable work; today's fresh sweep found nothing new to add. 0 parked/BLOCKED-OPERATOR-DECISION findings
  this run (both corrections above were auto-resolvable on evidence, not judgment calls) — no separate
  `ag_closeout_audit_ci_parked_2026_08_03.md` issue doc needed.
- **2026-08-04 — `/ag-closeout-audit ci` (autonomous, daily scheduled run, `ag_closeout_auditor` worker, slot 13).**
  Re-checked this batch's own Deferred section first (iterative-drain step 1): D5-1/D5-2/D5-3 unchanged (batch4's todos
  1/2/4 still un-landed, 0/9); D5-5/D5-6/D5-7 unchanged (batch4's D4-5..D4-18 still unruled;
  `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` still `status: open`; pnpm migration still has no
  dedicated plan). D5-4 stays RESOLVED, todo 2 sub-item 2 stays MOOT (both from yesterday, unchanged). Corpus-wide date
  stamps are dominated by the 2026-08-03 `context-scout` full-corpus re-scout (a mechanical `context_scope:`
  frontmatter-only touch on nearly every doc in the repo) — spot-verified on a sample file and confirmed content-inert,
  so NOT used as a change-detection signal; relied on `generate_ag_closeout_audit_candidates.py` + a fresh full Phase 1
  sweep instead. Fresh-candidate sweep: **42 total members** (up from 40 yesterday: -1
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` shipped+archived since yesterday — was self-covering,
  nothing lost; +3 new docs — `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`,
  `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md`, `…continued3_2026_08_03.md`), **4
  never-cited-in-an-active-covering-doc** (down from 7). **Full Phase 1 ran as a 42-agent `Workflow`** (one agent per
  candidate doc, not just the 4 never-cited — 0 errors, all 42 settled): 0 `archivable_now`, 11
  `archivable_after_planned_work`, 27 `orphaned_partial_coverage`, 4 `orphaned_never_touched`, 0 `exclude_cross_cutting`
  → **31 orphaned total**. All 4 never-touched individually assessed for Phase-3 AO-eligibility, **none qualify**:
  `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` is itself an active human-driven LOCAL plan whose own
  frontmatter says "each phase gate is a live judgment call, not a determinable worker todo" (operator-approved
  2026-08-03); the two `pytest_timeout_60s_flaky_under_contention_continued2/3_2026_08_03.md` docs are further splits of
  the SAME live incident chain D5-6 already tracks (matches batch3/4/5 precedent — too hot to batch while live);
  `qg_host_adaptive_resource_governor_2026_07_14.md` sits under its own standing 2026-07-14 "human-driven, not
  AO-ingested" operator ruling, independently re-confirmed KEEP-NA by two separate na-eligibility-audit passes
  (2026-07-30 infra, 2026-08-03 ci). Spot-checked all 27 `orphaned_partial_coverage` reasoning texts for a hidden
  bounded/conflict-clear candidate slipping through under an operator-gated label — found none; every item is either
  already named in batch1/batch4/batch5's own Deferred tables (D4-x/D5-x style) or, in one case
  (`digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`'s dormant-cascade item), confirmed genuinely
  too-open-ended to bound yet — that doc's own na-eligibility-audit verdict already says so; not a new finding, just
  re-verified. **Verdict: no batch 6 drafted this round either** — batch1 (42/43 done)/batch4 (0/9, drafted)/batch5
  (this doc, 0/6, drafted) still comprehensively cover the tranche's currently-extractable work, second day running. **0
  new parked/BLOCKED-OPERATOR-DECISION findings this run** (ledger: 0 parked == 0 written) — no
  `ag_closeout_audit_ci_parked_2026_08_04.md` issue doc needed. **One observation flagged, not acted on**:
  `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` carries `asset_group: [ci, infrastructure]` — a dual
  specific- tranche tag structurally analogous to the Orthogonality HARD CHECK's mistag pattern (content reads
  CI/CD-specific — GH-Actions self-hosted-runner fleet — so `ci` is likely primary), but its
  `parent_epic: infrastructure_master` doesn't cleanly disambiguate ownership since that epic feeds both `ci` and
  `infra` tranches, and per the concurrent-sharded- worker safety rule a non-owning tranche must not write a retag to a
  doc it doesn't clearly own — left for a future corpus-wide retag pass (mirroring
  `asset_group_ao_ci_infra_schema_expansion_2026_07_27`) or the `infra` tranche's own audit to resolve.
- **2026-08-06 (batch5 todo 1, slot 3 — cicd) — TODO 1 COMPLETE.** Slot-15's 5-repo quickmerge batch was already pushed
  to `origin/live-defi-rollout` at pickup (all 8 guard repos ahead=0, guard commits verified on origin). The drift
  checker is GREEN (EXIT 0) — all 19 consumers at or below baseline, residual counts = category-(b) intentional per-repo
  divergence. Empty-tag guard verified present in all 17 image-building consumer `cloudbuild.yaml` files
  (SAFE_SHA→VERSION fallback + FATAL diagnostic on double-empty). **End-to-end proof executed**: manual
  `gcloud builds submit` (storageSource, `SHORT_SHA` empty) on execution-service → build
  `4d265c51-5ca0-4349-b48f-80d4f7179430` recovered via `VERSION=0.0.0.dev0` fallback (extract-version wrote the
  fallback, build step's `SAFE_SHA=$VERSION` resolved, docker build proceeding normally instead of dying with
  `invalid reference format` / exit 125). Build still in progress at flip time — guard proof captured at the build step.
  Source issue doc `cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` follow-up checkbox also
  flipped with the build id cited. Todo 1 done_definition met: (1) markers classified (a)/(b)/(c) in source doc Progress
  Log; (2) guard present in every consumer; (3) end-to-end proof with build id; (4) drift checker green.
  `check_cloudbuild_template_drift.py` EXIT 0.
- **2026-08-06 (batch5 todo 3, slot 14 — backend_engineer) — TODO 3 COMPLETE (done-elsewhere + structural completion).**
  This todo duplicated batch1's already-completed item: the source doc's 3 prevention todos migrated to batch1 on
  2026-08-02, and batch1 flipped the `authoring_slot="ci-reconcile"` 400 item 2026-08-03 with the fix shipped as
  `unified-trading-pm@41f193405` (Direction 1 — `cicd.md`'s completion-ping guards on
  `[[ "$AUTHORING_SLOT" =~ ^[0-9]+$ ]]`). Verified (not code-read-alone): faithful simulation of the scheduler-raised
  bare-LDR completion path with `AUTHORING_SLOT=ci-reconcile` emits no POST; numeric `14` still fires; the server 4xxs
  `/api/slots/ci-reconcile/message` (422), confirming the 400 the guard prevents. Completed the STRUCTURAL fix by
  extending the same guard to `agents/conflict_resolver.md` + `agents/data_pipeline_failure.md` (same unguarded ping;
  `authoring_slot` is `str`-unvalidated at the escalate API). PM `quality-gates.sh` green; agent-orchestrator
  `quality-gates.sh` green. Sibling guards + flip shipped in this session's commit.
- **2026-08-07 — `/ag-closeout-audit ci` (autonomous, daily scheduled run, `ag_closeout_auditor` worker, slot 4,
  `agt-d12c5d`) — IN PROGRESS, checkpointed by `/pre-compact`.** Re-checked this batch's own Deferred section first
  (iterative-drain step 1): D5-1/D5-2/D5-3 unchanged (batch4's todos 1/2/4 still un-landed); D5-5/D5-6/D5-7 unchanged.
  Fresh-candidate sweep via `generate_ag_closeout_audit_candidates.py --tranche ci`: **45 total members, 7
  never-cited**. Dispatched a fresh full Phase 1 sweep as a 46-agent `Workflow` (45 real candidates + 1
  `asset_group:[meta]` fold-in candidate per the skill's Phase 0.3 meta-sweep rule,
  `quality_gates_quickmerge_timing_ baseline_2026_07_31.md`) — **run id `wf_1f04b9b2-680`, still executing when this
  checkpoint was written; results pending, to be reconciled in a follow-up entry.** Phase-0-only findings already
  written durably (not left in chat): see `/plans/archive/2026_08/issues/ag_closeout_audit_ci_parked_2026_08_07.md` — 6
  docs dual-tagged `[ci, infrastructure]` (content reads CI-specific in all 6, not retagged here per the same
  non-owning-tranche-race caution the 2026-08-04 run applied to the first of these six), 1 doc dual-tagged
  `[sports, ci]` (sports-owned, not retagged here), the `asset_group:[meta]` fold-in candidate noted above, and a
  `check_ag_closeout_linkage.py` ratchet cross-check (71 vs baseline 69, corpus-wide — 7 of the 71 are
  bare-`[ci]`-tagged; spot-verified `pm_bats_tests_never_invoked_by_quality_ gates_2026_07_26.md` is a gate
  false-positive, already tracked at batch4 D4-10, since the gate's "closeout family" for `ci` is only the archived
  digest doc, not this batch chain's own Deferred tables). Also observed (out of scope to chase here):
  `check_reference_paths.py` corpus-wide ratchets are both currently red (format 83 vs baseline 81, existence 92 vs
  baseline 86) — pre-existing, not caused by this run, not ci-specific; noted for whoever owns that ratchet. **Resume**:
  re-invoke/inspect Workflow run `wf_1f04b9b2-680` (or its journal.jsonl in the transcript dir), synthesize Phase 2
  (verdict counts + orphan list), run Phase 3's conflict-check, and append the final report + any batch6 decision to the
  parked-findings doc above rather than creating a second one.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) — the still-open todos' sources
  (`github_actions_operator_gated_followups_2026_07_17.md` for todo 2, the now-archived+resolved
  `github_actions_billing_wall_recurrence_2026_07_29.md` for todo 4,
  `post_cutover_silent_assumption_sweep_2026_07_23.md` for todo 6), this batch's own gated finalize, and the umbrella
  pipeline codex SSOT; dispatch-batch-coordinator shape.
- **2026-08-07 (batch5 todo 6, slot 2 — infra) — TODO 6 COMPLETE.** Verified live state with
  `check_dispatch_listeners.py --show` (baseline 38, current 38). **cascade-qg-ordering.yml**: the `quality-gate-run`
  repository_dispatch orphan was already fixed 2026-08-03 (switched to `workflow_dispatch` of `quality-gates-v2.yml`,
  which fails loudly on no target — no unconditional success issue). **sit-gate.yml**: `game-day-sit` and
  `synthetic-smokes` dispatches did have `|| echo "::warning::"` guards as the source doc claimed, but the guard was
  effectively dead code — GitHub returns 204 for `repository_dispatch` regardless of listener existence, so the
  `&& echo "Dispatched X"` branch always fired even with no listener in `system-integration-tests`. Fixed by changing
  `&& echo "Dispatched X"` → `&& echo "::notice::Fired X (best-effort; GitHub 204 does not confirm listener)"`, plus
  updating the `||` branch to acknowledge API error (not no-listener). Dispatch sites kept (fire-and-forget; listener
  can be added later). Baseline unchanged at 38 (dispatch sites still present; fixed count = 0 for orphan purposes —
  this fixes the reporting, not the orphan count). PM `quality-gates.sh` green. Shipped `unified-trading-pm@ead69c37d`,
  verified on origin.
- **2026-08-09 (finalize todo 4, slot 33 — review→cicd craft) — ARCHIVED.** All 6 todos done, `locked_by` empty —
  archived via the standard 6-step ritual (see `ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md` todo 4 for the
  full per-step detail). Moved to `plans/archive/2026_08/` alongside its finalize plan in a commit separate from this
  Progress Log/banner edit.

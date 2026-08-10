---
doc_type: plan
title: CI satellite AO batch 5 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch5_2026_08_02.md — machine-held via depends_on + gate_on_depends: true
  until all 6 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D5-1 through D5-7) for whether their blocker has cleared, and archives batch 5 via the
  standard 6-step ritual. Carries one batch-specific check the batch itself cannot contain: confirming the cloudbuild
  drift baseline was ratcheted DOWN (never up) by todo 1's two-step rollout.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
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
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 5 — finalize

> **🟢 ARCHIVED 2026-08-09** — all 4 todos done: reconciled all 5 distinct source docs the 6 batch-5 todos cite,
> re-checked/re-verified all 7 Deferred items (D5-1 through D5-7; 2 resolved since drafting, 2 re-triaged onward via
> batch6/batch6-finalize, 1 unchanged RESOLVED, 2 reconfirmed still open), then archived the parent via the standard
> 6-step ritual in this same commit. Parent archived to
> `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_2026_08_02.md`.

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
- [x] ✅ [REVIEW] P1. **DONE 2026-08-09 (slot 23, review→backend_engineer craft)** — reconciled all 5 distinct source
      docs cited by batch5's 6 todos (todos 3 and 4 cite two distinct items in the SAME doc). Per-doc findings + fixes:
  - `cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` (todo 1) — already `plans/archive/`,
    every todo + Follow-up `[x]`, genuinely zero open work. **Found + fixed a stale frontmatter mismatch**: `status:`
    had stayed `open` despite the 2026-08-07 archive banner claiming RESOLVED — flipped to `resolved`, populated
    `resolved_by` with the end-to-end proof citation. Progress Log entry added.
  - `github_actions_operator_gated_followups_2026_07_17.md` (todo 2) — both sub-items already correctly flipped `[x]`
    2026-08-09 by the batch5 todo 2 worker (slot 11), citing `unified-trading-pm@b3d2deacb` — verified ancestor of
    `origin/live-defi-rollout` ✅. Doc carries many unrelated still-open items (P0/P2/P3 across other sections) so it
    correctly stays `status: active` — does NOT reach zero. No batch4-todo-9 concurrent-edit collision found on re-pull.
  - `github_actions_billing_wall_recurrence_2026_07_29.md` (todos 3 + 4) — already `plans/archive/`, `status: resolved`
    since 2026-07-31; its 3 prevention todos were migrated to `ci_satellite_ao_dispatch_batch1_2026_07_26.md` on
    2026-08-02, so no live checkbox remained here to flip. **Batch5 todos 3/4 shipped work genuinely beyond what
    batch1's migrated items covered** — annotated a new Progress Log entry citing both, verified as ancestors:
    `unified-trading-pm@ba675a148` (todo 3's guard extension to `conflict_resolver.md`/`data_pipeline_failure.md`) and
    `unified-trading-ci@0afd236` (todo 4's actual outage-aware `quality-gates-v2` suppression — a different mechanism
    from batch1's `ci_reconcile.py` fix). Doc's own Todos/status unaffected (already zero/resolved).
  - `ui_build_warm_cache_2026_06_17.md` (todo 5) — already `status: complete`, every todo `[x]`, genuinely zero open
    work. No action needed.
  - `post_cutover_silent_assumption_sweep_2026_07_23.md` (todo 6) — **confirmed does NOT reach zero, as this todo's own
    text predicted.** The F3 item was already annotated by a prior na-eligibility-audit pass (2026-08-07) with the exact
    batch5 commit (`unified-trading-pm@ead69c37d`, re-verified ancestor of origin ✅); its checkbox correctly stays
    `- [ ]` because the 24-repo `semver-agent.yml` `schema-changed` dispatch slice (D5-2, conflict-gated on the
    workflow-template rollout mechanism) remains genuinely open. No hygiene fix needed — reconciliation was already
    correct on arrival.
  - **Net result**: 1 doc's frontmatter status corrected (cloudbuild), 1 doc got a new traceability annotation
    (billing-wall, for genuinely-new batch5 work its migrated copy didn't capture), 3 docs required no change (already
    correctly reconciled or correctly still-open by design). Zero commits were fabricated or cited without verifying
    ancestry. ~~[REVIEW] P1. **Reconcile all 6 batch-5 todos' source docs.**~~ (original text preserved below for
    record) Each batch-5 todo ends with `Source:` naming one or more docs (todos 3 and 4 cite two distinct items in the
    SAME doc — flip them independently, not as one). For each: flip the corresponding checkbox or annotate the
    corresponding prose section in EVERY cited doc, citing the batch-5 commit that shipped it — **verify the cited
    commit exists and is an ancestor of `origin/live-defi-rollout` before citing it** (`git merge-base --is-ancestor`).
    Then, per doc, re-check whether it now has zero open work **in checkbox AND prose form**; only set
    `status: resolved` on a doc that genuinely reaches zero. Note that
    `post_cutover_silent_assumption_sweep_2026_07_23.md` will NOT reach zero (its superseded/time-gated set stays open
    by design) and that `github_actions_operator_gated_followups_2026_07_17.md` may be concurrently edited by batch4's
    todo 9 — re-pull before writing. **Done when**: every cited doc is flipped/annotated with verified evidence, and
    each doc that genuinely reaches zero open work is `status: resolved`.
- [x] ✅ [REVIEW] P1. **DONE 2026-08-09 (slot 33, review→cicd craft).** Re-checked all 7 Deferred items D5-1 through
      D5-7 against live corpus state. Note-only per this todo's scope — nothing drafted here.
  - **D5-1** (quickmerge.sh branch-check broadening, step 3 of
    `issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`) — **blocker cleared.** Both
    preconditions landed: batch4 todo 1 (`unified-trading-pm@b02ba28c7`, verified ancestor) and batch4 todo 2 step 2
    (`unified-trading-library@dc1dc7df`, verified ancestor); batch4 itself is now fully done (all 9 todos `[x]`).
    Already independently re-confirmed by `ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md` todo 2 (also this
    slot, same session). **Superseded, not a fresh batch-6 candidate**: batch6 (drafted 2026-08-08, before batch4
    finished) re-deferred this exact item as its own **D6-3** using stale info ("batch4 todo 1 still draft, un-landed").
    `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md` todo 2 (2026-08-09) has since
    independently re-cleared D6-3 too, flagging it ready for **batch-7** consideration (with the caveat, per the source
    doc's own latest note, that step 3 is a genuine design/judgment call, not a rubber-stamp extraction). No action
    needed here.
  - **D5-2** (F3 success-reporting — 24 repos' `semver-agent.yml` `schema-changed` dispatch) — **file-contention gate
    cleared, underlying work still genuinely open.** Batch-5 todo 4 landed done-elsewhere (never touched
    `scripts/workflow-templates/`) and batch6 todo 9 separately freed the same mechanism (`unified-trading-pm@ec01e4167`
    per batch6-finalize D6-1/D6-2) — so the contention this item was rationed against no longer exists. But nobody has
    implemented the actual fix: `post_cutover_silent_assumption_sweep_2026_07_23.md`'s own F3 checkbox still explicitly
    states "the 24 repos' `semver-agent.yml` `schema-changed` dispatch (D5-2 ... not claimed by batch6 either; still
    genuinely open)", independently reconfirmed 2026-08-09 by
    `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md` todo 2's D6-9 entry. Ready for
    **batch-7** extraction (batch6 had the mechanism free too and still didn't claim it).
  - **D5-3** (F3 success-reporting — 12+ services' `cloudbuild.yaml`/`buildspec.aws.yaml` `service-deployed` dispatch) —
    **RESOLVED, no longer a batch-6 candidate.** The fix shipped 2026-08-06 via a different mechanism than the one D5-3
    was deferred over: a `deployment-service` listener (`deployment-service@5599bda8`) + an explicit-allowlist
    `deployment-api` override (`deployment-api@7110d2d`), both verified ancestors — it never touched the contended
    consumer `cloudbuild.yaml`/`buildspec.aws.yaml` files batch-5 todo 1 owned, so the file-contention framing that
    deferred it never actually applied. Confirmed directly in the source doc
    (`post_cutover_silent_assumption_sweep_2026_07_23.md`'s F3 checkbox: "`service-deployed → deployment-service` SLICE:
    DONE 2026-08-06"). Nothing left to extract.
  - **D5-4** — unchanged, stays RESOLVED (operator ruling `BLK-c099ebe5`, 2026-08-03, captured in batch1's migrated
    todo). Re-confirmed still `RESOLVED` in batch5's own Deferred table; no new ruling needed or issued.
  - **D5-5** — confirmed: batch4 (`ci_satellite_ao_dispatch_batch4_2026_07_31.md`) remains the live home for **D4-5
    through D4-18** — grepped its Deferred table directly, all 14 rows present, none silently vanished. Detailed
    per-item re-verification (has any individual D4-x's own blocker since cleared) is
    `ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md` todo 3's own scope (still open `[ ]` there) — not
    duplicated here.
  - **D5-6** — confirmed still open: `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` frontmatter reads
    `status: open` (3 open checkboxes remain), matching the live-incident precedent this item was deferred under.
    Blocker not cleared.
  - **D5-7** (pnpm content-addressable-store migration, `ui_build_warm_cache_2026_06_17.md`) — **RESOLVED, no longer
    needs "its own plan."** The sole remaining sub-part (cross-clone hardlink-dedup verification) shipped via
    `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md` todo 1 (2026-08-09, slot 31):
    `deployment-ui@33c6a02`, `unified-trading-system-ui@e70aeeb8`, `unified-trading-pm@e9e344a66`, all verified
    ancestors. Source doc flipped `status: active` → `complete` (zero open checkboxes/prose). Not yet archived
    (`locked_by: live-defi-rollout` blocks it pending an `[unlock-plan]` decision — out of this todo's scope).
  - **Net result**: 2 of 7 (D5-3, D5-7) fully RESOLVED since batch5 was drafted — no longer extraction candidates at
    all. 2 of 7 (D5-1, D5-2) had their batch5-specific gate clear but were already independently re-triaged by
    batch6/batch6-finalize, landing as ready-for-**batch-7** (not batch-6, which already came and mostly went). 1 of 7
    (D5-4) stays RESOLVED, unchanged. 2 of 7 (D5-5, D5-6) reconfirmed still in their recorded state, unchanged. Zero
    follow-up todos drafted here, per this todo's scope. ~~[REVIEW] P1. **Re-check the Deferred items D5-1 through D5-7
    for whether their blocker has cleared.**~~ (original text preserved below for record) D5-1 (quickmerge.sh
    branch-check broadening) — have BOTH batch4 todo 1 and batch4 todo 2 landed? If so it is ready-for-batch-6
    extraction; note it, do NOT draft it here. D5-2/D5-3 (F3's semver-agent and cloudbuild halves) — are the
    workflow-template rollout mechanism and the consumer `cloudbuild.yaml` files free again (batch-5 todos 4 and 1
    landed)? If so both are ready-for-batch-6. D5-4 — has the operator ruled on the billing-token fork? D5-5 — confirm
    batch4 is still the live home for D4-5..D4-18 and none has silently vanished. D5-6 — has
    `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` left `status: open`? D5-7 — has the pnpm migration been
    given its own plan? **Done when**: each of D5-1 through D5-7 has either (a) a note that it is ready for batch-6
    extraction because its blocker cleared, or (b) a re-verified confirmation the blocker is still open. Do NOT draft
    follow-up todos here — this plan's scope is reconciliation, not fresh drafting.
- [x] ✅ [DOC] P1. **DONE 2026-08-09 (slot 33, review→cicd craft).** Archived
      `ci_satellite_ao_dispatch_batch5_2026_08_02.md` via the standard 6-step ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`).
  - **Step 1 (migrate Deferred items)**: none needed migrating — every D5-1 through D5-7 item's real work already lives
    in its own independent source doc (`quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`,
    `post_cutover_silent_assumption_sweep_2026_07_23.md`, batch4's own Deferred table, the capacity-crisis doc), none of
    which are being archived here — todo 3's re-check confirmed nothing evaporates with batch5.
  - **Step 2 (archive banner)**: added to both `ci_satellite_ao_dispatch_batch5_2026_08_02.md` and this finalize doc,
    `status: complete` on both.
  - **Step 3 (codex-alignment check)**: confirmed `/codex/08-workflows/ci-cd-flow.md` did NOT yet reflect either
    contract batch5 shipped — added two new subsections: "Empty-tag / `$SHORT_SHA` guard" (todo 1's SAFE_SHA fallback
    - the two-step "resolve drift, then roll out" procedure) and "`quality-gates-v2` CI-status dispatch must be
      outage-aware" (todo 4's billing-kill-detection, done-elsewhere in `unified-trading-ci`). Shipped
      `unified-trading-pm@<this commit>`.
  - **Step 4 (CLAUDE.md)**: no CLAUDE.md-level change needed — both new contracts are codex-doc detail, not
    always-on-every-task rules; the existing `/codex/08-workflows/ci-cd-flow.md` pointer in CLAUDE.md already covers the
    domain.
  - **Step 5 (referrer sweep)**: grepped the whole corpus for `ci_satellite_ao_dispatch_batch5_2026_08_02` and
    `…_finalize_2026_08_02` — 8 leading-slash `/plans/active/...` references found (2 mutual between batch5/finalize, 2
    in active issue docs `ag_closeout_audit_ci_parked_2026_08_08.md`/`…_09.md`, 4 in already-archived docs —
    `batch6`/`batch6_finalize`/`ag_closeout_audit_ci_parked_2026_08_07.md`/
    `cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md`), all repointed to
    `/plans/archive/2026_08/...`. Bare-filename prose citations (historical "X was shipped by batch5 todo N" facts) left
    as-is per this doc's own convention — `check_reference_paths.py` only scopes leading-slash tokens; a historical fact
    citation doesn't need a live path.
  - **Step 6 (move + clear lock)**: `locked_by` confirmed empty on both docs (no unlock needed). Both files `git mv`d to
    `plans/archive/2026_08/` as a separate commit from this checkbox flip (per the "never combine flip + mv in one
    commit" rule). `INDEX.md`/`active_plan_inventory` regenerated via their own scripts, not hand-edited.
  - **Done-when met**: both docs live in `plans/archive/2026_08/`; every corpus referrer using the leading-slash form
    resolves; `check_reference_paths.py` re-run clean (not regressed) before shipping.

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
- **2026-08-09 (todo 2, slot 23 — review/backend_engineer craft) — TODO 2 COMPLETE.** Reconciled all 5 distinct source
  docs cited by batch5's 6 todos (Source: lines). Every cited commit verified via
  `git merge-base --is-ancestor <sha> origin/live-defi-rollout` before citing: `unified-trading-pm@b3d2deacb` (todo 2,
  pre-existing, re-verified), `unified-trading-pm@ba675a148` + `unified-trading-ci@0afd236` (todos 3/4, newly cited),
  `unified-trading-pm@ead69c37d` (todo 6, pre-existing, re-verified). Findings:
  `cloudbuild_template_behind_repos_ rollout_would_regress_fleet_2026_07_20.md` had a stale `status: open` frontmatter
  despite its 2026-08-07 archive banner claiming RESOLVED — corrected to `resolved` + populated `resolved_by`.
  `github_actions_billing_wall_recurrence_2026_07_29.md` had its 3 original prevention todos already migrated to batch1
  2026-08-02, but batch5 todos 3/4 shipped genuinely additional work (the authoring-slot guard extended to 2 more worker
  docs; a real outage-aware `quality-gates-v2` suppression, a different mechanism from batch1's `ci_reconcile.py` fix) —
  annotated a new Progress Log entry there for traceability. `github_actions_operator_gated_followups_2026_07_17.md`,
  `ui_build_warm_cache_2026_06_17.md`, and `post_cutover_silent_assumption_sweep_2026_07_23.md` were all already
  correctly reconciled by prior sessions/audits — no changes needed. Zero docs incorrectly marked `resolved`:
  `post_cutover_silent_assumption_sweep_2026_07_23.md` correctly stays open (D5-2's semver-agent slice genuinely
  unresolved, as this todo's own text predicted); `github_actions_operator_gated_followups_2026_07_17.md` correctly
  stays open (many unrelated open items). Full per-doc detail recorded on the todo checkbox itself above. Evidence:
  `unified-trading-pm@<this commit>` (this session's edits to the 3 touched docs + this plan).
- **2026-08-09 (todo 3, slot 33 — review→cicd craft) — TODO 3 COMPLETE.** Re-checked D5-1 through D5-7 against live
  corpus state, cross-referencing the sibling `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_2026_08_08.md` /
  `…batch6_finalize_2026_08_08.md` docs (drafted after batch5, so authoritative for what's changed since). Every cited
  commit verified via `git merge-base --is-ancestor <sha> origin/live-defi-rollout` before citing. **2 items fully
  RESOLVED since batch5 was drafted** (D5-3 — service-deployed dispatch fixed via a listener, never touched the
  contended files; D5-7 — pnpm hardlink-dedup shipped via batch6-finalize todo 1). **2 items had their batch5-specific
  gate clear but are best picked up in batch-7, not batch-6** (D5-1 — already independently re-cleared by
  batch6-finalize as its own D6-3; D5-2 — mechanism freed twice over (batch5 todo 4 + batch6 todo 9) but the actual
  24-repo fix remains unclaimed by both batch5 and batch6). **1 item unchanged, stays RESOLVED** (D5-4, prior operator
  ruling). **2 items reconfirmed still open, unchanged** (D5-5 — batch4 confirmed still home to D4-5..D4-18, all 14
  present; D5-6 — capacity-crisis doc confirmed still `status: open`). Zero follow-up todos drafted, per this todo's
  scope. Full per-item detail + citations on the todo checkbox itself above. Evidence:
  `unified-trading-pm@<this commit>` (this session's edit to this plan only — no code repos touched).
- **2026-08-09 (todo 4, slot 33 — review→cicd craft) — TODO 4 COMPLETE, PLAN ARCHIVED.** Ran the standard 6-step
  archival ritual against `ci_satellite_ao_dispatch_batch5_2026_08_02.md` (all 6 todos done, `locked_by` empty —
  genuinely archival-eligible). Codex-alignment check found `/codex/08-workflows/ci-cd-flow.md` did not yet reflect
  either contract batch5 shipped — added two new subsections (empty-tag/`SAFE_SHA` guard + the two-step
  drift-then-rollout procedure; outage-aware `quality-gates-v2` CI-status dispatch). Referrer sweep: 8 leading-slash
  `/plans/active/...` citations repointed to `/plans/archive/2026_08/...` across active + already-archived docs;
  bare-filename prose citations left untouched (out of `check_reference_paths.py`'s scope, and correct per this corpus's
  own historical-fact-citation convention). Both docs `git mv`d to `plans/archive/2026_08/` in a commit separate from
  this checkbox flip (never combine flip + move, per the archival discipline SSOT's 2026-07-30 incident rule).
  `INDEX.md` + the active-plan inventory regenerated via their own scripts (never hand-edited).
  `check_reference_paths.py` re-run clean before shipping — zero new dangling/malformed leading-slash references. Full
  per-step detail on the todo checkbox itself above. Evidence: `unified-trading-pm@<this commit>` (archival move +
  referrer-repoint commit(s), this session).

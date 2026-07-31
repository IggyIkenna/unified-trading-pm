---
doc_type: plan
title: CI satellite AO batch 1 — first AO-dispatch extraction for the ci tranche (which had ZERO dispatch coverage)
summary: >-
  First AO-dispatch batch for the `ci` topic tranche, produced by `/ag-closeout-audit ci` (autonomous mode, 2026-07-26)
  after `/plan-reconcile ci` had just cleaned the same corpus. Phase 0 found the tranche has NO dispatch vehicle at all
  — `ci_consolidated_closeout_2026_07_25.md` carries ZERO todos (it is a pure reachability digest, `assigned_vm: NA`),
  no `ci_satellite_ao_dispatch_batch*` plan has ever existed (active or archived), and all 30 of its Source docs are
  `assigned_vm: NA`/unset. Phase 1 read all 34 tranche-primary docs end-to-end (30 Sources + 4 newly-discovered unlisted
  members) and classified 30 as orphaned. Phase 3's conflict-check cleared 29 bounded items into the todos below; the
  same check found `scripts/quickmerge.sh` claimed by SIX different docs and PM `scripts/quality-gates.sh` by THREE, so
  exactly one quickmerge.sh todo is dispatched here and all new-QG-checker wire-ins are pushed to the gated finalize
  plan. 33 items stayed Deferred (conflict-gated / operator-gated / time-gated / human-only) and 8 went to the operator
  as parked questions.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    deployment-api,
    deployment-service,
    deployment-ui,
    unified-trading-system-ui,
    system-integration-tests,
    instruments-service,
  ]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-1, satellite-docs, quickmerge, github-actions, cloud-build]
related:
  [
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit ci` run 2026-07-26 (autonomous / AO-dispatched mode, operator away). Phase 0 discovery: the ci
  tranche's covering-plan set is EMPTY. Phase 1: all 34 tranche-primary docs read directly (no Workflow/Task tool was
  available in this environment, so the per-doc fan-out was executed as direct reads — same coverage, better adversarial
  fidelity on the supersession chains). Phase 3: conflict-check run BEFORE drafting, against the closeout's own content
  and every ci-primary doc's own todos.
assigned_role: cicd
sequential: false
drift_direction: advance-code
---

# CI satellite AO batch 1

> **⚠️ STATUS: `draft` — NOT dispatched, NOT ingested.** Flipping this (and its finalize sibling) to `status: active` is
> the operator's call per CLAUDE.md § "Plan destination — ASK BEFORE CREATING" and the `/ag-closeout-audit` skill's
> autonomous-mode rule. Drafted while the operator was unreachable; nothing here has been shipped.

> **Why this plan exists at all.** Unlike the 5 asset groups, `ci` has never had an AO-dispatch batch, and its
> consolidated closeout is a **digest with no todos** — being listed in its Track Sources is not dispatch. So every
> remaining open item in the tranche's 30 orphaned docs is, today, tracked-but-unworked. This batch extracts only the
> conflict-cleared, bounded, worker-determinable slice.

## Same-file contention — read before editing this plan

Same-priority todos in one plan run **concurrently**, so they must touch disjoint files (CLAUDE.md § Plans). Two files
are heavily over-claimed in this tranche and were deliberately rationed:

- **`scripts/quickmerge.sh` — claimed by 6 ci docs.** Only todo 1 touches it. The other five claims are in `## Deferred`
  (D3) for batch 2+; do **not** add a second quickmerge.sh todo here.
- **PM `scripts/quality-gates.sh` — claimed by 3 new checkers** (todos 2, 6, 7). Each todo delivers its checker as a
  **new standalone file plus a proven red/green run**, and the single `quality-gates.sh` registration commit is a todo
  in the gated finalize plan. Do not wire in from a batch todo.
- **`.github/workflows/digest-drift-sweep.yml`** — todo 3 owns it; `post_cutover_silent_assumption_sweep`'s F4
  non-convergence claim on the same file is parked (see `## Deferred` D2), not dispatched.

Every audit/verification todo records its findings **in its own named source doc**, never in this plan's body, so
concurrent workers do not collide on this file.

## Todos

- [x] [INFRA] P1. ✅ **quickmerge silently no-ops a new-file-only ship.** Fix already landed same-day at
      `unified-trading-pm@04c0eef0e` (guard now ALSO checks `git status --porcelain -- $FILES_ARG`, consistent with the
      clean-tree guard). This todo closes the remaining gap: added the regression test the source doc called for —
      `scripts/quality-gates-base/tests/test-quickmerge-untracked-new-file-guard.sh` (extracts the real guard from
      quickmerge.sh; verified it fails 2/4 against the pre-fix commit and passes 4/4 against the fix) —
      `unified-trading-pm@3ddd1a4f2`, PM `quality-gates.sh` green. Also flipped the tracking-home P0 in
      `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` and closed
      `/plans/archive/issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md` (`status: resolved`) so both stop
      duplicate- tracking this bug.
- [x] ✅ [INFRA] P1. **DONE 2026-07-26 (slot-5, `infra`)** — Delivered
      `scripts/quality_gates/check_dispatch_listeners.py` + `tests/unit/test_check_dispatch_listeners.py` (9 regression
      cases). Walks every repo's `.github/workflows/*.yml` / `cloudbuild*.yaml` / `buildspec*.yaml` / `scripts/**/*.sh`
      for `repos/{o}/{r}/dispatches` calls + each repo's own `on: repository_dispatch: types: [...]` listeners; resolves
      owner/repo/event_type via literals, known single-owner aliases, file-scope shell vars, and (for
      `trading-kill-switch.sh`'s exact shape) a shell-function-wrapper pass. **Reproduces F1 exactly**
      (`halt-order-flow`/`resume-order-flow` → execution-service, no listener) **and F3 exactly** (`quality-gate-run`
      dynamic-target zero-listeners-anywhere; `game-day-sit`/`synthetic-smokes` → system-integration-tests, no listener;
      12+ services' `cloudbuild.yaml`/`buildspec.aws.yaml` `service-deployed` → deployment-service, no listener) — plus
      additional real orphans not previously enumerated (`schema-changed` across all 24 repos, `library-published`,
      `tier-ab-green`, the dormant `staging-locked`/`staging-unlocked` pair). **63 orphans / 344 dispatch sites scanned
      / 13 unresolved** (2 of the 13 confirmed zero-call-site generic utilities, nothing to resolve). Baselined at 63
      (shrinking ratchet). NOT wired into `scripts/quality-gates.sh` (per § Same-file contention — registration is the
      finalize plan's todo). Regression tests prove: F1-shaped orphan detection, matching-listener NOT flagged, wildcard
      listener coverage, the cloudbuild/buildspec escaped-JSON-quote parsing (the exact bug that silently dropped every
      cloudbuild.yaml hit before the fix), the dynamic-target zero-vs-some-listeners distinction, the shell-wrapper
      per-call-site resolution, and the baseline ratchet exiting 0 at-baseline / 1 on a synthetic new orphan. Full
      findings + evidence recorded in the source doc's Resolution checklist (split the remaining "fix the unconditional
      success-reporting" work into its own new follow-up todo there, since that's a separate remediation this todo's own
      scope — "make it observable" — doesn't cover). Full PM `quality-gates.sh` green (1356 passed, 16 skipped). Source:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` (Resolution checklist, [INFRA] P1 "Make dispatch
      delivery observable").
- [x] ✅ [INFRA] P1. **DONE 2026-07-26 (slot-5, infra)** — digest-drift-sweep silent-failure hardening, the 3 of 4
      recommendations that were still open. Shipped `unified-trading-pm@6cb21eca3`: (2b) the Dockerfile fetch now
      captures the HTTP status via `-o "$BODY_FILE" -w '%{http_code}'` instead of `curl -sf … || echo ""` — `404` on
      both `live-defi-rollout` and `main` is a genuine benign skip (still counted in `SKIPPED_NO_ARG`), `401`/`403`/any
      other status `exit 1`s the step loudly instead of being folded into the benign-skip branch; (2c) the summary is
      now self-auditing — `Dispatched + Already fresh + Capped == 0` over a non-empty `IMAGE_REPOS` exits non-zero
      (`CAPPED` counts as "found and would have dispatched", so a cap-bound run is never mistaken for the failure); (3)
      added a `workflow_dispatch.inputs.max_dispatches` (default 5) that bounds real `/dispatches` POSTs per run,
      deferring the rest to the next tick and counting them separately. Proven via
      `scripts/quality-gates-base/tests/test-digest-drift-sweep-silent-failure-hardening.sh` — extracts the live
      workflow's embedded bash (not a replica) via PyYAML and exercises all 8 cases: the negative test
      (genuinely-absent-Dockerfile benign skip), 401/403 loud-failure, dispatch-cap bounding, and the self-audit
      assertion's positive/negative cases; all 8 pass against the fix, and the structural anchor fails against the
      pre-fix commit. The loud-failure path was proven via this extracted-block test rather than a live
      `workflow_dispatch` run — forcing a real 401/403 would require deliberately de-scoping the shared `GH_PAT` secret
      other production dispatches also depend on, an unacceptable side effect for a routine hardening change. Full PM
      `quality-gates.sh` green. Source doc's own status table updated to match:
      `issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` (now 3-of-4 done; recommendation 1, the
      dormant-cascade investigation, remains open and out of this todo's scope).
- [x] ✅ [INFRA] P1. **`check_strict_quickmerge.py` fails OPEN on a bad range, and `_backmerge` exemption is
      unconfirmed.** — unified-trading-pm@fd52877f6. (a) `main()` now runs `git rev-list` via a checked `_run_git()` and
      fails CLOSED (exit 1, unconditional of `--block`/`STRICT_QUICKMERGE_BLOCK`) when the range is unresolvable,
      instead of silently falling through to "✅ no bypassed code commits". (b) Confirmed `_backmerge` merge commits are
      ALREADY carve-out-exempt via the existing generic 2-parent "merge/reconcile commit" rule — no code change needed
      there, just proof: `test_backmerge_merge_commit_is_exempt` builds a real 2-parent `_backmerge`-style merge in a
      throwaway repo and asserts `commit_violates` returns exempt. Evidence: 3 new tests
      (`test_main_fails_closed_on_unresolvable_range`,
      `test_main_fails_closed_on_unresolvable_range_even_without_block`, `test_backmerge_merge_commit_is_exempt`) —
      16/16 pass in `tests/unit/test_check_strict_quickmerge.py`; full PM `quality-gates.sh` green (1359+6 passed, 16
      skipped; sentinel matched committed HEAD). Sources:
      `issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` ([DEVOPS] P2) +
      `issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md` (Fix direction 3).
- [x] ✅ [INFRA] P2. **DONE 2026-07-28 (slot-9, infra)** — `rollout-cloudbuild.py` can no longer regress a repo. —
      unified-trading-pm@ddf0b89f4. Added `find_dropped_markers()`: parses both the live cloudbuild.yaml and the
      freshly-rendered template (structural, not a raw line diff — a purely cosmetic YAML reflow like a one-line vs.
      two-line `args: [...]` parses identically either way, so it never false-positives) and diffs top-level keys, step
      ids, `secretEnv`/`availableSecrets` entries, and per-step arg content (list items compared as a set; heredoc/bash
      script content compared line-wise, since YAML block scalars preserve those breaks verbatim — this is what catches
      an in-place fallback change like the 2026-07-20 `VERSION="0.0.0.dev0"` case, not just whole-step drops). Any
      marker present live but absent from the render refuses the write with a diagnostic naming it (`main()` in
      `scripts/propagation/rollout-cloudbuild.py`). Default flipped write→dry-run; writing now requires an explicit
      `--apply` (`--dry-run` still accepted, forces dry-run even if `--apply` is also passed). Verified nothing
      programmatic invokes the old write-by-default path (grepped the corpus — only manual/docstring usage; not wired
      into `scripts/quality-gates.sh`, confirmed pre-existing exclude). Full PM `quality-gates.sh` green (sentinel
      matched committed HEAD before the rebase-recovery push; the pre-existing bare `except Exception:` lint hit was
      fixed by narrowing to `except yaml.YAMLError:`, not bypass-documented). **Finding surfaced while proving "done
      when" #3** ("a dry run over all 19 consumers is clean"): a real `--dry-run` today correctly REFUSES 15/19
      consumers — the template has drifted far past the single 2026-07-20 near-miss (secretEnv/`--unshallow`/VERSION
      fallback, since forward-ported and clean) to include entire steps the template still lacks (MTDS's
      `stage-workspace-deps`/`image-import-smoke` dep-skew guard, deployment-api's
      `vendor-deps`/`deploy`/`redeploy-monitor-jobs`, and a `fetch-tags`/`operability-probe` pair now present on most
      service repos). Only `deployment-ui`, `e2e-testing`, `system-integration-tests`, `unified-trading-system-ui` are
      currently write-clean. This is real and current, not a detector bug (spot-verified several diffs by hand); it is
      squarely the scope of this same plan's next todo (drift checker) and the source issue doc's P3 (all-templates
      reconciliation) — out of scope for this todo, which only had to make the tool incapable of silently regressing a
      repo, and it now measurably cannot: every one of those 15 repos would have been overwritten pre-fix. Recorded in
      the source issue doc's Progress Log for visibility. Source:
      `issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` ([DEVOPS] P2).
- [x] ✅ [INFRA] P2. **Deliver a cloudbuild template-vs-consumer drift checker.** — unified-trading-pm@8f15ff124.
      Delivered standalone `scripts/quality_gates/check_cloudbuild_template_drift.py`, reusing `rollout-cloudbuild.py`'s
      own `generate_cloudbuild()`/`find_dropped_markers()` (never re-implemented) to render every
      `configs/cloudbuild-*-template.yaml` and diff it against every consumer's committed `cloudbuild.yaml`. Covers ALL
      FIVE templates, not just `-service-` (measured: service 12/12 drifted, api 2/2, infra 1/1, ui 0/2 clean, sit 0/2
      clean — matches the earlier 15/19 fleet-wide figure exactly). Shrinking-ratchet baseline
      (`cloudbuild_template_drift_baseline.yaml`, seeded 2026-07-28 at today's real per-repo counts) bakes in the
      intentional per-repo drift (e.g. deployment-api's `vendor-deps`/`deploy`/`redeploy-monitor-jobs` steps) rather
      than "fixing" it. **NOT wired into `scripts/quality-gates.sh`** per the finalize-plan gate.
      `tests/unit/test_check_cloudbuild_template_drift.py` (14 cases) proves a synthetic template-lags-repo case fails
      at a seeded baseline, plus the API-template path. Per-template measurements recorded in the source doc's Progress
      Log. Source: `issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` ([DEVOPS] P1 +
      P3, both closed).
- [x] ✅ [INFRA] P1. **Deliver a checker banning the swallowed-credential-fetch idiom.** — unified-trading-pm@c91844b09.
      Delivered `scripts/quality_gates/check_no_swallowed_credential_fetch.py` (standalone, NOT wired into
      `scripts/quality-gates.sh` per the finalize-plan gate; `glue-runner-run.sh` untouched) + a shrinking-ratchet
      baseline (`no_swallowed_credential_fetch_baseline.yaml`, seeded at 18 real hits across 3 repos) +
      `tests/unit/test_check_no_swallowed_credential_fetch.py` (22 cases incl. a synthetic-new-hit failure case). Hit
      list recorded in `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`.
- [x] ✅ [INFRA] P1. **Self-hosted glue pool with 0 runners listening must page on its OWN cause.** Nothing watches
      runner liveness — a total pool collapse surfaced only as a generic `PROMOTION LAG > 60m` WARNING and was mis-read
      as "normal SIT latency" for 16 hours. Implement the source doc's own cheapest-honest-signal design as a NEW
      workflow: alert when a `glue`-labelled job has been `queued` longer than N minutes while `in_progress == 0` —
      unambiguous, and it needs no VM access (a naive "is the host up" check would have said GREEN, since the
      `glue-writer` pool stayed healthy). Route through the reusable `notify-slack.yml` carrier with a state-transition
      `dedup_key` per `/codex/04-architecture/ci-alerting.md` (fire on change / RESOLVED / re-remind, never every tick).
      **Done when**: the workflow exists, a synthetic starved-queue case fires exactly one alert, and a healthy pool
      fires none. Source: `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` ([DEVOPS] P1). —
      unified-trading-pm@80f397278: new `.github/workflows/glue-pool-starvation-monitor.yml` (hosted runner, per
      classify-glue-workflows.sh's failure-independence rule — never runs on `glue` itself) cron `*/15`, calling
      `scripts/cicd/glue_pool_starvation_monitor.py` (pure decision logic + `gh api` queued/in_progress job scan, `glue`
      vs `glue-writer` exact-label match) then `notify-slack.yml` with `dedup_key: glue-pool-starved`,
      `cooldown_min: 60`. `tests/unit/test_glue_pool_starvation_monitor.py` (16 cases) proves the synthetic
      starved-queue case (queued > threshold + 0 in-progress) fires and a healthy/busy/under-threshold pool fires none.
      Full `bash scripts/quality-gates.sh` green.
- [x] ✅ [INFRA] P2. **`workspace-quickmerge-validation` logs `❌ Dependency alignment FAILED` yet concludes
      `success`.** Make the workflow exit non-zero when it emits a failure line. **Done when**: a run that logs the
      failure concludes `failure`, and a genuinely-aligned run still concludes `success`. —
      unified-trading-pm@6f898f930: removed the blanket `|| true` on the validation step
      (`.github/workflows/workspace-quickmerge-validation.yml`) so the job's exit code is the script's real exit code,
      added `if: always()` to the artifact-upload + summary steps so they still run on a failing validation; also fixed
      a latent `set -e` early-exit bug in `scripts/validate-workspace-quickmerge.sh` where a failing repo's subshell
      terminated the script before `ec=$?` was ever read, skipping the dependent-skip cascade + matrix write for every
      repo after the first failure. Verified via a local harness (fake manifest + 3 fake repos, one made to fail):
      failure path now exits 1 with a full PASS/FAIL/SKIPPED matrix (dependent correctly marked SKIPPED); all-pass path
      exits 0. Source: `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` § F4.
- [x] ✅ [INFRA] P2. **The `sit_retry_cap` escalation can never succeed.** — unified-trading-pm@2e5a42479 +
      agent-orchestrator@dbdccb6. `escalation.WALL_TYPES` + the GHA case-statement already accepted `sit_retry_cap`
      (fixed 2026-07-27 by `agent-orchestrator@63f5cbd`), but a live `workflow_dispatch` proof exposed TWO further gaps
      the earlier fix missed: (1) `escalate-to-orchestrator.yml`'s `workflow_dispatch` input was `type: choice` with a
      stale `options:` list that never included `stuck_promotion_pr`/`ldr_main_qg_failure`/`sit_retry_cap` — dispatch
      itself 422'd with "not in the list of allowed values" (unified-trading-pm@2e5a42479 fixes the choice list + both
      wall_type descriptions). (2) After that, the live POST to `/api/escalate` STILL 422'd —
      `server/models/escalation.py`'s `EscalateRequest.wall_type` is a THIRD, separately-hardcoded `Literal` that was
      ALSO missing both new wall types (agent-orchestrator@dbdccb6 fixes it + adds a regression test cross-checking
      `EscalateRequest`'s Literal args against `escalation.WALL_TYPES` so the two sets can't drift apart silently
      again). **Evidenced by a real run**: after deploying `dbdccb6` to the live orchestrator VM (`git pull --ff-only`,
      verified non-destructive — untracked runtime files in `data/config/` were unrelated and untouched), re-dispatched
      `escalate-to-orchestrator.yml` via `workflow_dispatch` —
      https://github.com/IggyIkenna/unified-trading-pm/actions/runs/30342653568 — `POST /api/escalate` returned
      `HTTP 200 {"ok":true,"escalation_id":"agt-d37ed9","status":"queued","wall_type":"sit_retry_cap","prompt_template":"cicd"}`.
      `status:"queued"` (no free slot at dispatch time) means the proof landed with zero synthetic worker spawned.
      Local: `pytest tests/test_escalation.py` 79/79 passed incl. the new cross-check test. Source:
      `issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` ([DEVOPS] P2). **Full round-trip CONFIRMED
      2026-07-28**: `agt-d37ed9` above was later dispatched to a live worker (slot 1, `cicd` role) — its boot carried
      `WALL_TYPE=sit_retry_cap` + the same escalation id, which is itself proof the request cleared both the GHA
      case-statement AND the `EscalateRequest` pydantic Literal with no 422. The worker confirmed the fix in code
      (`server/models/escalation.py:44` carries `sit_retry_cap`), pinged the authoring slot, and closed via `/done`.
      This closes the gap the `status:"queued"` proof above left open (zero synthetic worker spawned at that time) — the
      chain emit → validate → queue → **dispatch → worker execute → complete** is now proven end-to-end, not just
      accept/queue.
- [x] ✅ [INFRA] P2. **DONE 2026-07-28 (slot-11, infra)** — Guard the latent self-dispatch repeat.
      `.github/workflows/agent-runner.yml:91` and `.github/workflows/sit-gate.yml:357` self-dispatched via
      `${{ github.repository }}`, correct only because both files exist solely in PM. Hardcoded the PM target in both —
      `repos/${{ github.repository_owner }}/unified-trading-pm/dispatches`, the GHA-expression-syntax equivalent of the
      already-shipped `repos/${GITHUB_REPOSITORY_OWNER}/unified-trading-pm/dispatches` bash pattern in
      `main-backmerge-to-ldr.yml` — with an inline comment on each site explaining why (agent-runner.yml is additionally
      a `workflow_call` reusable workflow invoked via a local `uses: ./.github/workflows/agent-runner.yml`, so a copy
      rolled into another repo would previously have silently self-dispatched there). Verified both edits are clean YAML
      (`python3 -c "import yaml; yaml.safe_load(...)"`) and prettier-clean. Full PM `quality-gates.sh` green, shipped
      via `quickmerge --agent --files` — `unified-trading-pm@cb5e944f0`. Source:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([REVIEW] P3).
- [x] ✅ [INFRA] P3. **`check_dispatch_listeners.py`'s dispatch-URL regex cannot resolve inline GHA `${{ }}`
      expressions, silently excluding those dispatch sites from the scan.** — unified-trading-pm@cbd511a. **Fixed
      2026-07-29.** `_DISPATCH_URL_RE` now accepts `${{ }}` expressions as an alternative to literal tokens within
      owner/repo capture groups via `_GHA_EXPR_PAT`. `_resolve_token` returns GHA expressions as-is so the dispatch site
      is tracked as unresolved rather than silently excluded. Added `_GHA_EXPR_RE` for token classification. 3 new test
      cases: GHA expression capture, mixed GHA+literal, literal regression. Result: 350 sites scanned (was 344), 17
      unresolved (was 13), orphans unchanged at 63 (at baseline). segment (either by resolving the GHA context
      expression the same way `_OWNER_ALIASES` resolves shell vars, or by stripping `${{ ... }}` whitespace before
      matching), a regression test proves both `agent-runner.yml` shapes are now scanned, and the baseline is
      re-measured (expected to rise, since previously-invisible sites become visible — a one-time step up in the
      ratchet, not a new orphan). Source: this plan's own todo 2 (`check_dispatch_listeners.py`, delivered
      `unified-trading-pm@613f79960`) + `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([REVIEW] P3,
      discovered while closing it).
- [x] [INFRA] P2. **F5 vacuous manifest readers render GREEN where they should render "unknown".** Fix the enumerated
      sites so a permanently-empty input renders as unknown/not-applicable, never as a pass — starting with the two the
      doc names first: `_repo_ci_manifest.py:285-289`'s `deployed_versions.get(repo)` shape mismatch (the writer at
      `cloud-build-router.yml:853` writes `[env][repo]`, so the column is permanently blank) and the
      `_repo_ci_stuck.py:148,155` `stuck_in_sit` / `repo_ci.py:643-670` promotion-blocked panels. Also correct the
      now-false in-file comment at `ldr-to-main-promote-fleet.yml:422-434` claiming "BOTH stay live for ldr_main repos".
      Copy the correct dormancy-checking pattern the doc already identifies (`promotion_lag_monitor.py:190-199`,
      `_repo_ci_manifest.py:251-258`). **Done when**: each fixed reader renders unknown on empty input, covered by a
      test, and the false comment is corrected. Source: `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` §
      F5 + its [INFRA] P2. — **DONE 2026-07-29, of the 4 sub-items 3 are closed and 1 is a genuinely-scoped-larger
      residual, split out below rather than force-fit here:** 1. ✅ **`deployed_version_for` shape mismatch — FIXED.**
      Now reads `deployed_versions["prod"][repo]["version"]` (the real writer shape) instead of a flat
      `deployed_versions.get(repo)`. The pre-existing test fixture used the WRONG flat shape too (so it validated a
      contract that never matched production) — corrected + added 2 regression tests proving the flat/wrong-env cases
      correctly resolve to `None`, not silently succeed by accident. `deployment-api@6885fc3`, `quality-gates.sh` full
      green. 2. ✅ **`repo_ci.py`'s "Promotion blocked" panel — ALREADY FIXED, verified not re-fixed.** Live code at
      (now) `repo_ci.py:639-667` (`_build_promotion_blocked`) reads real `view.promotion_failures()` +
      `view.promotion_quarantine()` state, not the vacuous pattern the source issue described — this drifted to a real
      fix sometime between the issue's 2026-07-23 filing and today, independently of this todo. No code change needed;
      confirmed via direct read, not assumed. 3. ✅ **False `ldr-to-main-promote-fleet.yml` comment — FIXED.** Corrected
      to state the true reason `breaking_pending` is currently empty (staging_dormant_mode suppresses the writer
      fleet-wide, not an ldr_main-specific carve-out) and names the actual load-bearing signal (`sit-gate/fleet-green`
      required check, Firestore `sit_validated_tree`). `unified-trading-pm@b7605db21`. Comment-only, no behavior
      change. 4. ⚠️ **`stuck_in_sit` — confirmed still vacuous, but NOT tri-stated here; split into its own todo.**
      `derive_sit_state`'s `in_pending = repo in breaking_pending` is structurally always `False` while
      `staging_dormant_mode` is on (same root cause as item 3), so `stuck_in_sit` can never fire — genuinely matches the
      issue's description. BUT: traced its only consumer (`deployment-ui/src/lib/repoCi.ts:172`,
      `if (hasGenuineStuck || row.sit.stuck_in_sit) return 2`) and confirmed it is OR'd with other real signals, never
      gates/suppresses one — so today it can only ever be a false-negative (never contributes a spurious "stuck"), not a
      false-positive masking a real failure, unlike the promotion-blocked bug this todo's sibling item fixed. Making it
      a real tri-state (unknown vs. true/false) needs `SitStateDict.stuck_in_sit: bool` → `bool | None` in
      `deployment-api`'s `_repo_ci_types.py` PLUS the matching `deployment-ui` consumer change — a real type-contract
      change across 2 repos, not a same-shape reader fix like items 1-3. Per the workspace's dispatch-scope rule this is
      bigger than a single AO todo; tracked as its own properly-scoped follow-up:
      `issues/repo_ci_stuck_in_sit_tristate_2026_07_29.md`.
- [x] ✅ [INFRA] P2. **DONE 2026-07-29 (slot-2, infra)** — `full-workspace-sit.yml`: a cancelled run's status clobbers a
      real success, and `SIT_VALIDATED` over-claims. **The live-measured incident's actual clobber path was
      `sit-gate/fleet-green` in `unified-trading-pm/.github/workflows/ldr-to-main-promote-fleet.yml`** (its
      `SIT_FLEET_LINE` derivation reads `gh run list` — ordered by run CREATION time, newest first — and picked
      `completed[0]`, which is also true for `conclusion=cancelled`; a run created after a real success but cancelled
      almost immediately could outrank it, exactly reproducing the cited 30158515857/30158518796 incident). Fixed both
      real instances of the same bug class, in scope per this plan's own repo list: (a1) `ldr-to-main-promote-fleet.yml`
      — `unified-trading-pm@2f9646585` + `@466c7621e` (the actual edit landed in a companion commit after prek's
      stash/restore dropped it from the first) — filters cancelled runs out of the informative candidate set before
      selecting `[0]`. (a2) `full-workspace-sit.yml`'s own "Report SIT result to PM" step had the identical defect
      (`job.status != success` → `sit-failed`, so a cancelled job dispatched a false failure to `sit-unlock`) —
      `system-integration-tests@33cf6f0` — now no-ops on `job.status=cancelled`. (b) Corrected the
      `full-workspace-sit.yml` header comment (same commit) so `SIT_VALIDATED` cannot be read as "the resolved
      cross-repo combination was executed" — states plainly it's an API-surface check (installs only UAC, never collects
      a dependent's tests; a value-only config change can pass while breaking a consumer at runtime). **Evidence**: both
      fixes proven via regression tests extracting the REAL shipped code (not replicas) —
      `unified-trading-pm/scripts/quality-gates-base/tests/test-sit-fleet-green-cancelled-run-clobber.sh` (5/5 pass
      post-fix, 2/5 pass pre-fix — reproduces the exact incident JSON) and
      `system-integration-tests/tests/abbreviated/test_full_workspace_sit_cancelled_run_noop.py` (cancelled→no-op,
      success→sit-passed, failure→sit-failed; confirmed dispatching `sit-failed` pre-fix). Full `quality-gates.sh` green
      on both repos, shipped via `quickmerge --agent --files`. Sources:
      `issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` ([DEVOPS] P2 sub-finding,
      2026-07-25) + `issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` ([DEVOPS] P2 messaging).
- [ ] [INFRA] P3. **A repo SIT-BLOCKED for N consecutive promoter ticks must be visible as a stuck gate, not as
      slowness.** The treadmill is currently only observable as a promotion-lag alert, which reads as latency. Add a
      regression test / monitor that fires on N consecutive `SIT GATE BLOCK <repo>` verdicts for the same repo.
      **Constraint**: implement as a NEW detector file — do **not** edit `ldr-to-main-promote-fleet.yml` (todo 12 owns a
      comment there, and this doc's other promote-fleet todo is gated on an unmade direction ruling, `## Deferred` D12).
      **Done when**: the detector fires on a synthetic N-tick block and stays silent on a block→revalidate→pass cycle.
      Source: `issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` ([DEVOPS] P3).
- [x] ✅ [INFRA] P2. **Apply the shipped sha-tag-guard to deployment-api's two unguarded secondary cloudbuild configs.**
      Applied the identical first-push-wins guard from `cloudbuild.yaml` to both `cloudbuild-tier3.yaml` and
      `cloudbuild-dashboard.yaml`: a `sha-tag-guard` step writing `/workspace/.sha_tag_preexists`, a conditional push
      (immutable `:$SHORT_SHA` kept, `:latest` re-pushed), and dropped the sha entry from `images:` on both.
      `scripts/validation/validate-cloudbuild.py` + `scripts/quality_gates/check_cloudbuild_substitutions.py` both clean
      on both files; full `quality-gates.sh` green. — deployment-api@a3f5822 Source:
      `/plans/archive/issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md` (archived 2026-07-30) ([INFRA] P3,
      third item).
- [ ] [INFRA] P2. **Sync `deployment-service/configs/gcp_service_accounts.yaml` against live IAM.** The per-service
      SA/IAM registry has NO entry at all for `unified-trading-sa@central-element-323112` (deployment-api's actual
      runtime SA) and its own footer admits `last_executed: NEVER` — an aspirational registry is worse than none,
      because it reads as coverage. Reconcile it against a live `gcloud projects get-iam-policy` /
      `gcloud iam service-accounts list` read and set the runbook fields (`owner`/`cadence`/`verifier`/`last_executed`)
      that `check_runbook_fields.py` expects. **Read-only on GCP — do not add, remove, or modify any IAM binding** (the
      SA-scoping work in the same source doc is operator-credential-gated, `## Deferred` D10). **Done when**: every live
      SA the workspace actually uses has an entry, each entry's roles match the live policy, `last_executed` is dated,
      and the diff between registry and reality is recorded in the source doc. Source:
      `issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md` ([BACKEND] P3).
- [x] ✅ [DOC] P2. **`/codex/08-workflows/ci-cd-flow.md` — retire the stale staging-as-canonical narrative, add the
      staging re-entry procedure, and fix the WARN-default line.** FOUR docs independently claim this one file, so it is
      one combined todo. (a) L75-109 still shows `ldr-to-staging-promote` draining every service repo on a 15-min cron
      and labels direct-to-main as "PM only"; L763, L777-786, L1183 still describe `quickmerge → staging → main` as
      canonical — bring all four sites to the current LDR→main-direct model. (b) Add the staging **re-entry** procedure
      INCLUDING "uncomment the disabled triggers" — verified 2026-07-23 that `grep -rn -i "uncomment" codex/` returns
      one unrelated hit, so this fact currently lives only in inline YAML comments and a plan (plans archive; codex is
      the SSOT). (c) L702 still calls the strict-quickmerge guard "WARN-default" — stale since it now BLOCKS. **Done
      when**: all four narrative sites match the shipped model, the re-entry procedure is in codex, L702 is corrected,
      and prettier + `check_reference_paths.py` are clean. Sources:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([DOC] P2 + § Docs) ·
      `github_actions_staging_machinery_shutdown_2026_07_24.md` (its single open [DOC] P2) ·
      `github_actions_operator_gated_followups_2026_07_17.md` (Deferred-after-07-23 row 5, "Blocked on: Nobody") ·
      `issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` ([DEVOPS] P3). **DONE 2026-07-26
      (slot-5, cicd)** — `unified-trading-pm@97970974e`. (a) verified via broad grep this session that the four
      staging-as-canonical narrative sites were already corrected by prior work (no stale hits remain for
      `ldr-to-staging-promote`/"15-min cron"/"PM only"/"quickmerge → staging → main" outside the now-current
      LDR→main-direct model). (b) added the "Staging re-entry procedure" section (manifest flip + the 6 disabled
      triggers table + default-branch schedule gotcha + measure-don't-assume verification). (c) corrected the
      strict-quickmerge line from "WARN-default" to "BLOCKS by default" (operator policy 2026-06-26). prettier +
      `check_reference_paths.py` both clean (at baseline); shipped via `quality-gates.sh` → `quickmerge --agent`.
- [ ] [INFRA] P3. **The two husky UI repos carry no strict-quickmerge guard.** The pre-push self-heal skips them
      (`case "${_hooks_dir}" in */.husky/*) continue`), so `deployment-ui` and `unified-trading-system-ui` are the only
      clones with no provenance guard at all. Wire the strict guard into each repo's husky `pre-push`. This touches
      `.husky/` hooks only — **no UI source, so the playwright gate does not apply**; do not touch any `src/`/`app/`
      file. **Done when**: a synthetic non-quickmerge code push is blocked in both repos, a quickmerged range passes,
      and the self-heal recognises the husky installs. Source:
      `issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` ([DEVOPS] P3).
- [ ] [INFRA] P2. **D13 orphan-reader census + remediate `sync-manifest-versions.py`.** D13 (2026-06-27) made the git
      tag the version SSOT and deleted the static `version = "X.Y.Z"` pyproject line, but only migrated ONE reader.
      `scripts/manifest/sync-manifest-versions.py` still has 28 pyproject refs / 0 git-tag-aware branches and a
      docstring that still says "Sync manifest versions section with pyproject.toml versions" — and because it is a
      manual tool wired to no workflow, it fails only when someone reaches for it, i.e. exactly when it is trusted. Two
      steps, one unit: (i) run the census the source doc explicitly says is owed ("this table is a sample, not a
      census") — sweep for every remaining reader of a static `version =` and check each against its repo's
      `version_source`; (ii) make `sync-manifest-versions.py` D13-correct, or delete it and repoint referrers per
      "delete deprecated code (no shims)" — state which and why. **Done when**: the census is recorded in the source
      doc, and the script either no longer parses a deleted field or is gone with zero dangling referrers. Source:
      `issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` (steps 3 + 7).
- [ ] [INFRA] P2. **Fleet version/tag-state census (read-only, NO tag minting).** Three docs each ask for a slice of the
      same measurement; do it once. (a) Re-derive manifest `versions{}` vs the highest real `vX.Y.Z` tag across all 24
      repos (last measured 2026-07-17: 13 in sync / 9 LAGGING / 1 AHEAD — worst `e2e-testing` 0.6.0 vs v0.40.0). (b)
      Determine why the versions-consolidator is not closing that gap, and confirm it runs at all. (c) Confirm each of
      the 22 repos the stall alarm reported STALLED on 2026-07-23 has since minted ONE post-fix tag capturing current
      `main`, and list those that have not. **HARD CONSTRAINT: audit only — do NOT mint, move, or delete any git tag**
      (CLAUDE.md: never bump manually; the minter is semver-agent; hand-minting and the deliberate no-backfill decision
      are operator territory, `## Deferred` D16/D31). **Done when**: one dated table covering (a)/(b)/(c) is recorded in
      `d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` and cross-linked from
      `post_cutover_silent_assumption_sweep_2026_07_23.md`, with zero write operations performed. Sources:
      `issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` (step 2) +
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([INFRA] P2 "Reconcile the ~4 weeks of missing tags").
- [ ] [INFRA] P2. **The repurposed release-STALL alarm emits a `::warning::` nobody reads.** `reconcile_release_tags.py`
      is now the fleet's release-stall detector (codex ruling, `/codex/08-workflows/ci-cd-flow.md:1004`), and it
      correctly measured a 4-week, 22-repo, ~2,490-commit outage — but by default it only emits a `::warning::` unless a
      caller passes `--fail-on-stall`, so the finding lands nowhere a human sees. Route the STALL verdict to a channel
      someone reads: fire it through the reusable `notify-slack.yml` carrier with a state-transition `dedup_key` per
      `/codex/04-architecture/ci-alerting.md`, so a NEW stall pages once and a RESOLVED stall all-clears — without
      making the `*/30` schedule fail 48×/day. Also apply the source doc's silent-failure lesson if it still holds
      post-repurpose: `_main_version()` returning `None` conflates "no pyproject" / "fetch failed" / "field absent" —
      distinguish them, or record why the repurpose made it moot. **Done when**: a synthetic stall produces exactly one
      alert with the repo names and staleness, a no-stall run produces none, and the `*/30` cron does not fail. Source:
      `issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md` § "Also fix the silent-failure
      class". **Note**: the separate question of what happens to the three dead `DELETE     reconcile-release-tags` todo
      lines is parked with the operator; this todo stands under every option.
- [ ] [SCRIPT] P3. **`base-ui.sh`: one automatic retry on the build-timeout class.** A cold-cache UI build trips the 90s
      QG budget and passes on retry; a genuine hang fails twice. Add exactly one automatic retry on the timeout class in
      `scripts/quality-gates-base/base-ui.sh` — removes the human re-run without weakening the budget. Exercise it
      against a real UI repo build before shipping (the source doc requires this). PM shell script only; **no UI source
      change, so the playwright gate does not apply**. **Done when**: a cold-cache trip self-recovers on the single
      retry, a deliberately-hung build still fails, and the budget is unchanged. Source:
      `ui_build_warm_cache_2026_06_17.md` ([SCRIPT] P3).
- [ ] [INFRA] P2. **cassette-drift-check: the negative test its own fix requires is unevidenced.** All three prescribed
      fixes shipped 2026-07-17 (`unified-trading-pm@f339ce5e8`: repointed to
      `-m unified_api_contracts.testing.detect_cassette_drift`, `RUNNER_TEMP` venv install, `0)`/`1)`/`*)` exit-code
      split) and the workflow was flipped to `[self-hosted, glue]` (`@e9d02e5d6`) — but the doc's own "Negative test
      that must pass after the fix" was never run: a genuine drift must still open the issue, a genuinely-absent-drift
      run must exit 0, and a BROKEN invocation (bad path / unimportable module) must FAIL the job rather than report
      drift. Add that negative test and prove all three states are now distinguishable. **Explicitly OUT of scope**:
      closing the 52 false `[Cassette Drift]` issues and the detector's cassette→model matching lottery — both
      operator-owned, and Ikenna owns the count verification (`## Deferred` D23). **Done when**: the three exit states
      are covered by a test/dispatch and the source doc's banner records the evidence. Source:
      `issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md`.
- [ ] [INFRA] P2. **Verify the released Docker version tag is no longer re-pointed at new content.** The F2 blast-radius
      probe found the UTL base image rebuilt daily and re-tagged the SAME frozen `0.55.0`/`latest`, so `0.55.0` named a
      different tree every day and rollback-by-version was undefined. A fix shipped (`:{version}-{sha12}` always applied
      and never re-pointed; bare `:{version}` only when HEAD is exactly the release commit) but the open item's own
      verification was never done: **confirm two builds never share a version tag**. Probe Artifact Registry read-only,
      and record whether pinning service `FROM` lines by digest only is still needed. Read-only on AR — do not delete or
      re-tag any image. **Done when**: a dated AR probe shows every version tag maps to exactly one digest across at
      least two consecutive rebuilds, recorded in the source doc. Source:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([INFRA] P1 "Stop re-pointing a released Docker tag at
      new content").
- [ ] [INFRA] P2. **Confirm `instruments-service`'s publish path can no longer emit `0.0.0.dev0`.** It published
      `0.0.0.dev0` to AR `unified-libraries` on 2026-07-03 — hatch-vcs's no-git-history fallback, a wheel carrying
      neither a version nor a sha. The generic fix shipped in PM's `publish-package.yml` (`fetch-depth: 0` + fail-closed
      on the BUILT wheel's version), and the propagation template `scripts/propagation/templates/publish-package.yml`
      was corrected — but this repo's INSTALLED copy was never confirmed. Read its live copy; if it lacks
      `fetch-depth: 0` or the built-wheel assertion, install the corrected template copy. **Done when**:
      instruments-service's publish workflow has both, evidenced by reading the file on `origin/live-defi-rollout`, and
      the bad 2026-07-03 wheel's disposition is recorded (do NOT delete it — an AR delete is operator-gated). Source:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([INFRA] P2).
- [ ] [VERIFY] P1. **Re-measure the billed notify/glue cost — the 3-5 day window has long passed.** The mover flip
      landed 2026-07-17; the source doc's own table says the earliest useful measurement was ~2026-07-20/22, and it is
      now 2026-07-26, so this is actionable, not calendar-blocked. Run `scripts/cicd/measure-billed-notify-cost.sh`
      (promoted out of a scratchpad precisely so this is repeatable) and confirm the moved workflows bill ~$0 and the VM
      absorbed the load (slice `MemoryCurrent` < 8G, orchestrator load unaffected). Honour the doc's own measurement
      traps: skipped jobs are not billed, a throttled API call silently counts as 0, `/timing.billable.total_ms`
      UNDER-reports (`billable: {}` with no `UBUNTU` key is the real zero) — so COUNT JOBS, never ms. If the billing
      token is unavailable, record `BLOCKED-CREDENTIALS` rather than estimating. **Done when**: a dated per-workflow
      billed-job-count table is recorded in the source doc, or the credential block is recorded. **Explicitly NOT the
      two-week Phase-5 re-pull** (still calendar-gated, `## Deferred` D29). Source:
      `github_actions_operator_gated_followups_2026_07_17.md` ([VERIFY] P0, `measure-billed-notify-cost.sh`).
- [x] ✅ [VERIFY] P2. DONE 2026-07-26 (slot 6) — **CONFIRMED FIRING.**
      `gh run list -R IggyIkenna/unified-trading-pm     --workflow=ldr-docs-gate.yml --limit 20` shows 20 consecutive
      `event=schedule` runs, ALL `conclusion=success`, spanning `2026-07-26T03:02:59Z` through `2026-07-26T23:19:47Z`
      (most recent: run id `30225007924`) — roughly hourly cadence with the documented ~80-90% GH `schedule:` delivery
      slippage (e.g. `03:02→05:07` is a ~2h gap, consistent with known throttling, not a real miss). The
      `push`→`schedule: "0 * * * *"` retarget from 2026-07-22 is genuinely live and healthy; no root-cause investigation
      needed. Source: `github_actions_operator_gated_followups_2026_07_17.md` (Deferred row 14).
- [ ] [INFRA] P2. **Find the CI/CD event-ledger CONSUMER — the one blocking question behind decision D2.** The
      `persist-cicd-event` ledger is written with an unlocked read-modify-write on ONE object per repo per day, so
      overlapping writers silently discard each other's rows while every writer logs success. The operator's
      fix-vs-accept ruling is explicitly blocked on ONE determinable fact the doc names: **who reads this ledger?** The
      schema claims `GitHubWorkflowEvent` from `unified_api_contracts.internal`, implying a real consumer. Grep the
      whole workspace (all repos, incl. UIs and deployment-api) for every reader of the `unified-trading-cicd-events`
      bucket and of that type, then read each candidate consumer — **grep-then-READ, 0 hits ≠ missing.** Audit only: do
      NOT change `persist-cicd-event` or the ledger's write path. **Done when**: the consumer set (possibly empty,
      stated as a measured fact) is recorded in the source doc so the operator's D2 ruling is unblocked. **Do not
      re-derive the loss analysis** — the doc says it is complete. Source:
      `github_actions_operator_gated_followups_2026_07_17.md` ([REVIEW] P0 / D2).
- [x] ✅ [INFRA] P2. **Is the AWS CodeBuild cosmetic `failure` status still posted at all?** This doc's noise may
      already be moot: all native GitHub webhooks on the 18 CodeBuild projects in `427895769566`/ap-northeast-1 were
      deleted 2026-07-03 (`f22fde880` + `d93388305`, `AWS_BUILDS_ENABLED` switch OFF since), so CodeBuild should no
      longer fire on PR events. Check a recent automated promote PR's commit statuses for
      `AWS CodeBuild ap-northeast-1 (<repo>)`. If absent, the issue is empirically moot and the doc's remaining prose
      recommendation should be recorded as no-longer-needed; if present, capture the current live webhook config so the
      TF↔live drift can be reconciled later. **Read-only: no `terraform apply`, no `aws codebuild update-webhook`** —
      both are operator/AWS-perms-gated and the module itself warns a blind apply reverts live config (`## Deferred`
      D27). **Done when**: a dated status check on a named recent promote PR is recorded in the source doc with a
      keep-open-or-resolve recommendation. Source:
      `/plans/archive/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md`. — **CONFIRMED RESOLVED 2026-07-27**
      (operator interactive session, `plans/active/june_2026_vintage_audit_findings_2026_07_27.md` §5#21): live-verified
      via `gh pr view` — the "AWS CodeBuild" status check shows `SKIPPED`, not the red `FAILURE` the finding described,
      on `unified-api-contracts#776` and `deployment-service#571` — posted but non-failing (not literally absent, but
      empirically moot for the noise this finding tracked: no more red `failure` on promote PRs). Source doc archived:
      `plans/archive/issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md`.

## Deferred

Tagged by WHY, per the `/ag-closeout-audit` non-batchable taxonomy. Only **conflict-gated** items can be converted by a
future batch's re-triage; the rest need direct operator/human action or elapsed time.

### Conflict-gated (re-triageable in batch 2+)

| id  | Item                                                                                                                                                  | Competing claim it collided with                                                                                                           |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| D1  | Wire the 3 new QG checkers into PM `scripts/quality-gates.sh`                                                                                         | Todos 2, 6, 7 all need the same registration line → moved to the finalize plan's todo 2                                                    |
| D2  | `digest-drift-sweep` non-convergence + `ubuntu-latest` fan-out (the part costing money)                                                               | Same file as todo 3; `post_cutover` § F4 claims it while `digest_drift_sweep_…` owns the mechanism analysis — **PARKED with the operator** |
| D3  | 5 further `scripts/quickmerge.sh` claims (see below)                                                                                                  | Todo 1 owns the file this batch; concurrent same-file todos are forbidden                                                                  |
| D4  | Delete redundant `scripts/dev/hooks/pre-push-strict-quickmerge.sh` + repoint referrers                                                                | Referrers include `quickmerge.sh` (todo 1) and `/codex/08-workflows/ci-cd-flow.md` (todo 17)                                               |
| D5  | `check_strict_quickmerge.py` dirty-deps carve-out trailer                                                                                             | Same file as todo 4 **and** operator-gated: it changes the provenance gate's trust model, its own doc requires sign-off                    |
| D6  | Disable/fix the 4 F4 vacuous crons (`sit-debounce-trigger`, `freeze-deferred-build-replay`, `fix-approval-timeout`, `supersede-stale-dep-update-prs`) | `sit-debounce-trigger.yml` is todo 10's file; and "disable OR fix" needs a per-cron ruling                                                 |

**D3 detail** — the five held `scripts/quickmerge.sh` claims, in the order this audit would re-extract them: (1) bind
`ENVIRONMENT`/gate-affecting config INTO the QG sentinel hash so a dev-verified sentinel cannot satisfy a prod-context
run (`qg_sentinel_environment_blind_2026_07_23.md` [INFRA] P1 — the doc's own "fix this regardless" item); (2) STAGE 1.6
dormancy-aware dep gate (`stale_staging_versions_manifest_2026_07_23.md`, gated on the operator's option 1/2/3 pick —
parked); (3) instrument STAGE 0's cascade step for the MTDS `DEPLOYMENT_ENV` leak
(`mtds_deployment_env_race_survives_single_worker_2026_07_23.md` — also parked, see the reproducer question); (4)
broaden the branch check to recognise `live-defi-rollout` (`quickmerge_environment_autodetect_…` step 3, itself gated on
its step 2); (5) the content-hash green-tree fast-path (`quickmerge_sentinel_race_retry_storm_…` fix 1 — explicitly "do
NOT dispatch blind", operator sign-off).

### Operator-gated (needs a ruling, not a re-triage)

| id  | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| D7  | `qg_sentinel_environment_blind` — **RESOLVED, no longer operator-gated (2026-07-28 gate-cleanup)**: no specific answer was on file, so the general design-choice theme was applied — ruled **BOTH** (fix the env-coupled tests properly AND align quickmerge's/standalone's resolved `ENVIRONMENT` so the two paths can never silently diverge again); full reasoning + the two retagged todos live in the source doc's § "Which side is actually wrong?" and Resolution checklist. Retag `[OPERATOR]` → `[DOCS]`/`[INFRA]` already done there — out of this batch's file scope to retag directly here.                                                                                                                                                      |
| D8  | `stale_staging_versions_manifest` — **RESOLVED, no longer operator-gated**: `autonomous_session_operator_decisions_2026_07_25.md` entry #33 ruled option 1 (dormancy-aware gate) confirmed — "the doc's own pre-committed gate (versions advancing since 2026-07-23) is now measured satisfied; queued as a `quickmerge.sh`-touching todo for ci's batch 2" (`unified-trading-pm@36c5433eb`). Drop the `[OPERATOR]` framing on this tracking row; the source doc's todo is queued for batch 2 as an ordinary `scripts/quickmerge.sh`-touching todo, same file-contention rules as D3.                                                                                                                                                                        |
| D9  | `orchestrator_gcloud_active_account_wif_poisoning` [OPERATOR-DECISION] P1 — direction (a)/(b)/(c)/(d), + its gated P2                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| D10 | `github_actions_deploy_sa_overbroad_secret_access` — the 2 secret-scoped bindings need `ikenna@…`'s `secretmanager.admin` ⇒ BLOCKED-CREDENTIALS                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| D11 | `uac_value_only_config_change_breaks_utl_untested` [A] dependency-content-aware v2 sentinel — explicitly "operator sign-off required, not an autonomous ship"; [B] blocked on [A]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| D12 | `sit_validated_tree_treadmill` — the direction ruling (lease vs SIT-sha-pin + gate-side change vs accept-and-monitor) and the retarget's gated POST move                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| D13 | `post_cutover` F1 — trading kill-switch no-op. Operator ruling 2026-07-23: KEEP TRACKED, DO NOT FIX YET; re-entry gate before execution-service handles live order flow                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| D14 | `silent_failures` [DEVOPS] P0 — re-do the `\|\| true` fix in `glue-runner-run.sh`. Root cause found (an apostrophe inside a `${VAR:-…}` default word) but the first attempt crash-looped all 5 live runners; needs a `--selfcheck` mode + a staged one-unit roll on the live glue pool                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| D15 | `silent_failures` [DEVOPS] P3 — runner-unit `StartLimitBurst`/`StartLimitIntervalSec`; same live-runner-infra roll risk as D14                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| D16 | `d13_orphaned_version_readers` steps 5-6 — delete the vestigial `repositories{}.version` manifest scalar + make `assert_version_coherence.py` gate. Manifest schema change every slot rebases on; fleet blast radius                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| D17 | `mutable_git_sha_tag_restamping` [INFRA] P3 — `scan-check` semantics on a pre-existing sha tag; the doc says a deliberate ruling was never sought                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| D18 | `promotion_lag_alert_hides_provenance_block` — **no longer operator-gated (2026-07-28 gate-cleanup)**: clearing the 2 provenance blocks at source is an ordinary re-ship, not an operator sign-off decision — re-ship the 2 named commits via `quickmerge --agent --files` (or revert on LDR if abandoned). Retag `[OPERATOR]` → `[DEVOPS]` P2 in the source doc and dispatch it there as a normal AO todo (out of this batch's file scope to retag directly here).                                                                                                                                                                                                                                                                                          |
| D19 | `capability_wizard_client_lite_and_ci_regen_followup` — both residuals; the plan itself says "neither should be auto-queued to a worker" (residual 1 blocked on `.venv-workspace` on a CI runner = operator action)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| D20 | `ui_build_warm_cache` [INFRA] P3 — pnpm content-addressable store. **UPDATED 2026-07-27**: operator decision `june_2026_vintage_audit_findings_2026_07_27.md` §5#33 APPROVED the migrate-to-pnpm call — no longer an open decision. Still not dispatchable HERE though: it's real implementation scope (lockfile format change + CI install steps across UI repos), so it needs `[UI]` + `pw:L2 ✓` + a UI-capable role same as D28 — this batch's `assigned_role` is `cicd`. Kept in the source doc as a real `- [ ]` todo pending a UI-capable slot.                                                                                                                                                                                                        |
| D21 | `quickmerge_sentinel_race_retry_storm` fixes 1 and 3 — see D3(5)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| D22 | `github_actions_operator_gated_followups` [INFRA] P0 — STEP 2d assert-not-decorative. HELD on decision D3, whose three subjects have all since changed state (**parked**)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| D23 | Cassette D4 — close the 52 false `[Cassette Drift]` issues + the detector's cassette→model matching lottery. Ikenna owns the count verification; do not duplicate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| D24 | `operator_gated_followups` D2 — the event-ledger fix-vs-accept ruling itself (todo 28 only unblocks it by finding the consumer)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| D25 | `operator_gated_followups` Deferred row 13 — the 91 broken doc references in `doc_reference_baseline.yaml`. Cross-tranche plan-hygiene work that collides with concurrent `/plan-reconcile` shards; belongs to a hygiene plan, not `ci`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| D26 | `build_deploy_pipeline_provenance_and_aws_deferred_gaps` — all 4 items. Explicit operator instruction: "Page-first, do NOT fix here… loop Ikenna in before touching any of them; every open item lives in a file in his active CI area"; #4/#7 are AWS-lane                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| D27 | `aws_codebuild_terraform_import_pending` — needs AWS CodeBuild write perms (`ikenna-worker` has none: `ListProjects`/`BatchGetProjects`/`UpdateWebhook` all `AccessDenied`) plus standing up a new S3 TF state backend; AWS is intentionally parked (no credits)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| D28 | `ui_build_warm_cache` [CODE] P2 ×2 (tsc `incremental` + `setup.sh` pre-warm). **CORRECTED 2026-07-27**: the `tsc incremental` half was NOT fresh dispatch — verified already implemented (`"incremental": true` present in both `deployment-ui/tsconfig.json` and `unified-trading-system-ui/tsconfig.json`, gitignored tsbuildinfo paths) and flipped `[x]` in the source doc. Only the `setup.sh` pre-warm half is genuinely still open, confirmed still touching UI source only insofar as the setup script change is PM-owned (`scripts/setup.sh`) — no UI repo source change required for that half, so it may not need the full `[UI]`+`pw:L2` gate on re-triage; still deferred here since this batch's `assigned_role` is `cicd` not `ui_developer`. |

### Time-gated

| id  | Item                                                                                                                          |
| --- | ----------------------------------------------------------------------------------------------------------------------------- |
| D29 | Two-week billing-ledger re-pull vs the Phase-0 baseline — earliest ~2026-07-31. Method + exact commands are in the source doc |
| D30 | Re-observe the 27-consecutive-loss quickmerge retry storm under similarly heavy multi-slot contention before closing that doc |

### Too-large-or-risky / genuinely human-only

| id  | Item                                                                                                                                                                                             |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| D31 | `d13_orphaned_version_readers` step 1 — decide the cache-repair direction and build a `versions{}`←tags reconciler. A design pass, not a todo                                                    |
| D32 | `post_cutover` — close the `sit_validated_workspace_digest` written-but-unread gap **or** document why it is safe to drop; the "or" is the design call                                           |
| D33 | `silent_failures` [DEVOPS] P2 — `detect_breaking_change.py` is Python-only, so every TS repo is permanently "unknown-delta". The doc itself calls this "a structural promotion tax, not a fault" |

## Escalated to the operator (parked, not guessed)

Eight questions went back with quotes, locations, options and a marked recommendation rather than being resolved
autonomously. In summary: (1) should this batch + finalize pair be flipped `active`, and should the ci closeout itself
gain dispatchable todos or stay a pure digest; (2) the `scripts/quickmerge.sh` extraction order (6 competing claims);
(3) who owns `digest-drift-sweep.yml` edits (3 docs); (4) MTDS `DEPLOYMENT_ENV` — fix the 2 tests or preserve them as
the only reproducer; (5) is STEP 2d unblocked now that decision D3's three subjects have changed state; (6) two ci docs
are already AO-dispatched but listed in no closeout, and one of their live todos asks a worker to move a published git
tag; (7) the tranche-membership rule misses every `asset_group: [meta]`/`[infrastructure]` doc; (8) confirm
`stale_staging_versions` option 1 now that its own gate is satisfied.

## Codex SSOTs (read before executing any todo)

- `/codex/08-workflows/ci-cd-flow.md` — pipeline / quickmerge / strict-quickmerge / gate set / release + wheel
- `/codex/06-coding-standards/quality-gates.md` — how gates run; never `pytest` directly
- `/codex/04-architecture/ci-alerting.md` — `notify-slack.yml` carrier, `dedup_key` + cooldown, recovery-gated
  all-clears
- `/codex/02-data/honest-absence-downstream-handling.md` — the "absent must not be indistinguishable from unreadable"
  principle every silent-failure todo here generalises from data to automation
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-07-26** — Drafted by `/ag-closeout-audit ci` in autonomous mode, immediately after `/plan-reconcile ci` (whose
  14 auto-fixes shipped as `unified-trading-pm@29dda2bfd`, so frontmatter/checkbox state was trustworthy going in).
  Phase 0: covering-plan set EMPTY — closeout has 0 todos, no batch plan has ever existed, all 30 Sources are
  `assigned_vm: NA`. Phase 1: all 34 tranche-primary docs read end-to-end (per-doc reads, not checkbox counts — the
  documented traps bit repeatedly: 12 of the 30 orphans express ALL their remaining work as numbered prose with zero
  checkboxes). Phase 3: conflict-check run first; it is what produced the same-file rationing above and the 6
  conflict-gated deferrals. Nothing shipped, nothing flipped to `active`.
- **2026-07-26** — Flipped `status: active` per resolution of
  `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #26 (option A: leave the closeout hub a pure digest
  — matches the documented digest/dispatch split architecture). Flipped batch1 only, not the finalize sibling: the
  finalize plan already carries `gate_on_depends: true` (task_template.md's draft-gated pattern), so it self-activates
  once this batch's todos land — flipping it now, ahead of that, would be premature (nothing to reconcile yet). Same
  reasoning applied consistently to entries #22 (ao) and #38 (infra).

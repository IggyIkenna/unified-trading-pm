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
status: complete
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
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
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
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# CI satellite AO batch 1

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 43 todos shipped. Finalize plan
> `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` (source-doc reconciliation, the 8-item
> Deferred re-check, and this archival) completed and archived alongside in the same commit set. Every Deferred item
> (D1-D33) remains tracked in its own live source doc (none was uniquely resident in this plan), so archiving it strands
> no open work — see the finalize plan's todos 3-4 for the full per-item re-verification. Successor: none drafted here;
> D2/D3(4 sub-items)/D6(bounded sub-part)/D30 are still-open items ready for a future `ci_satellite_ao_dispatch_batchN`
> to extract.

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
      expressions, silently excluding those dispatch sites from the scan.** —
      unified-trading-pm@5913352467b7215e8cc7d58ae5a632c5aebd5658. **Fixed 2026-07-29.** `_DISPATCH_URL_RE` now accepts
      `${{ }}` expressions as an alternative to literal tokens within owner/repo capture groups via `_GHA_EXPR_PAT`.
      `_resolve_token` returns GHA expressions as-is so the dispatch site is tracked as unresolved rather than silently
      excluded. Added `_GHA_EXPR_RE` for token classification. 3 new test cases: GHA expression capture, mixed
      GHA+literal, literal regression. Result: 350 sites scanned (was 344), 17 unresolved (was 13), orphans unchanged at
      63 (at baseline). segment (either by resolving the GHA context expression the same way `_OWNER_ALIASES` resolves
      shell vars, or by stripping `${{ ... }}` whitespace before matching), a regression test proves both
      `agent-runner.yml` shapes are now scanned, and the baseline is re-measured (expected to rise, since
      previously-invisible sites become visible — a one-time step up in the ratchet, not a new orphan). Source: this
      plan's own todo 2 (`check_dispatch_listeners.py`, delivered `unified-trading-pm@613f79960`) +
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([REVIEW] P3, discovered while closing it).
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
      — `unified-trading-pm@ab22e725b6141e4ccd7b11018134e7e8bbb90961` + `@18a55dd49c12dbf71241696b1fbfd5e8aa2ee37d` (the
      actual edit landed in a companion commit after prek's stash/restore dropped it from the first) — filters cancelled
      runs out of the informative candidate set before selecting `[0]`. (a2) `full-workspace-sit.yml`'s own "Report SIT
      result to PM" step had the identical defect (`job.status != success` → `sit-failed`, so a cancelled job dispatched
      a false failure to `sit-unlock`) — `system-integration-tests@33cf6f0` — now no-ops on `job.status=cancelled`. (b)
      Corrected the `full-workspace-sit.yml` header comment (same commit) so `SIT_VALIDATED` cannot be read as "the
      resolved cross-repo combination was executed" — states plainly it's an API-surface check (installs only UAC, never
      collects a dependent's tests; a value-only config change can pass while breaking a consumer at runtime).
      **Evidence**: both fixes proven via regression tests extracting the REAL shipped code (not replicas) —
      `unified-trading-pm/scripts/quality-gates-base/tests/test-sit-fleet-green-cancelled-run-clobber.sh` (5/5 pass
      post-fix, 2/5 pass pre-fix — reproduces the exact incident JSON) and
      `system-integration-tests/tests/abbreviated/test_full_workspace_sit_cancelled_run_noop.py` (cancelled→no-op,
      success→sit-passed, failure→sit-failed; confirmed dispatching `sit-failed` pre-fix). Full `quality-gates.sh` green
      on both repos, shipped via `quickmerge --agent --files`. Sources:
      `issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` ([DEVOPS] P2 sub-finding,
      2026-07-25) + `issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` ([DEVOPS] P2 messaging).
- [x] ✅ [CI] P1. **Mirror the batch1-036 auto-merge-arm-failure fix to the sibling standalone
      `ldr-to-main-promote.yml`.** batch1-036 (`unified-trading-pm@4bf65b67c`) fixed the silent-swallow of
      auto-merge-arm failures in `.github/workflows/ldr-to-main-promote-fleet.yml`, but the PM-own standalone
      `.github/workflows/ldr-to-main-promote.yml` has the IDENTICAL silent-swallow bug and is failing LIVE (review
      agt-39a53d confirmed via `gh run view 30774619258`, 00:30-00:31Z: "WARN: auto-merge unavailable"; PR #2061 OPEN,
      mergeStateStatus=UNSTABLE, autoMergeRequest=null; zero ARM_FAILED-equivalent tally/Slack). Apply the same
      arm-failure tally + alerting as `4bf65b67c`. **Done when**: the standalone workflow surfaces an arm-failure
      non-silently (+ alert), regression-tested, QG green, shipped via quickmerge. Source: review batch chat msg 3383,
      2026-08-03; same failure class as the original ~10h-silent promote incident this plan traces to. Fixed all 4
      `gh pr merge --auto` arm-call sites (new-PR arm, routine per-tick re-arm, close+reopen recovery re-arm,
      post-dirty-reconcile re-arm) to branch on the arm call's own exit status, wiring a new `arm_failed` step/job
      output through GITHUB_OUTPUT at every exit point + a dedicated `notify-arm-failed` Slack job (single boolean flag
      tracking the last arm attempt's outcome this run, vs. the fleet's per-repo count — this workflow is
      single-repo/per-tick). Added `scripts/quality-gates-base/tests/test-ldr-promote-standalone-arm-failed-tally.sh`
      (structural + a functional extraction of a real if/else arm-site block evaluated against a stubbed `gh`, 8/8
      pass). Full `quality-gates.sh` green. — unified-trading-pm@5047141d0
- [x] ✅ [INFRA] P3. **A repo SIT-BLOCKED for N consecutive promoter ticks must be visible as a stuck gate, not as
      slowness.** Added `scripts/cicd/sit_gate_stuck_detector.py` — a standalone detector (does NOT edit
      `ldr-to-main-promote-fleet.yml`) that fetches the workflow's recent run LOGS via `gh run view --log` (the run's
      own `conclusion` stays `success` on a SIT-gate block, so run-level status can't distinguish it — only the log text
      can), extracts every `SIT GATE BLOCK <repo>: ...` line per tick, and pages once the SAME repo has been blocked on
      the `--threshold` (default 3) most-recent CONSECUTIVE ticks — always counted from the newest tick backward, so a
      block→revalidate→PASS cycle self-silences the moment the newest tick is clean, regardless of the prior streak
      length. Wired a new `.github/workflows/sit-gate-stuck-detector.yml` (every 30 min, mirrors
      `promote-fleet-startup-failure-monitor.yml`'s shape) posting via the `notify-slack.yml` carrier with its own
      `dedup_key: sit-gate-stuck` / `cooldown_min: 60` (distinct from promotion-lag's / startup-failure's, no shared
      cooldown). **Done when, verified**: `tests/unit/test_sit_gate_stuck_detector.py` (22/22 pass) proves both
      acceptance cases directly on synthetic tick histories — `test_stuck_repos_fires_on_exact_threshold_streak` (fires
      on a synthetic 3-tick block) and `test_stuck_repos_silent_on_block_revalidate_pass_cycle` (silent once a
      block→revalidate→PASS cycle completes), plus insufficient-history / multi-repo-independent-streak /
      report-formatting coverage. Full `quality-gates.sh` green. — unified-trading-pm@409c35437 Source:
      `issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` ([DEVOPS] P3).
- [x] ✅ [INFRA] P2. **Apply the shipped sha-tag-guard to deployment-api's two unguarded secondary cloudbuild configs.**
      Applied the identical first-push-wins guard from `cloudbuild.yaml` to both `cloudbuild-tier3.yaml` and
      `cloudbuild-dashboard.yaml`: a `sha-tag-guard` step writing `/workspace/.sha_tag_preexists`, a conditional push
      (immutable `:$SHORT_SHA` kept, `:latest` re-pushed), and dropped the sha entry from `images:` on both.
      `scripts/validation/validate-cloudbuild.py` + `scripts/quality_gates/check_cloudbuild_substitutions.py` both clean
      on both files; full `quality-gates.sh` green. — deployment-api@a3f5822 Source:
      `/plans/archive/issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md` (archived 2026-07-30) ([INFRA] P3,
      third item).
- [x] ✅ [INFRA] P2. **Sync `deployment-service/configs/gcp_service_accounts.yaml` against live IAM.** Read-only audit
      (`gcloud iam service-accounts list` / `get-iam-policy` / `storage buckets list` / `run services describe` per live
      Cloud Run service — no IAM binding added/removed/modified) confirmed the specifically-flagged gap: added the
      missing `unified-trading-sa` entry (deployment-api's + client-reporting-api's confirmed live runtime SA) with its
      live project-level roles, plus `deployment-api` to `service_short_names`. The audit also surfaced a much larger
      finding beyond this todo's bounded scope: 17/19 other declared `*-prod` SAs (and all their declared buckets) have
      no live counterpart at all, and most live Cloud Run services actually run on the GCP default compute SA rather
      than any per-service SA — i.e. the registry's whole per-service isolation model was never provisioned. Recorded
      the full diff in the YAML's header comment + `execution.last_diff` (dated `last_executed: 2026-07-31`) rather than
      silently absorbing or dropping it, and filed the larger architecture-decision-gated finding as a separate issue
      doc (its own scope — migrate live services to match the plan, or rewrite the plan to match live reality — is a
      judgment call, not a bounded fact-check). — deployment-service@0b7d03c Source:
      `issues/github_actions_deploy_sa_overbroad_secret_access_2026_07_24.md` ([BACKEND] P3), follow-up:
      `issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`.
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
- [x] ✅ [INFRA] P3. **DONE 2026-08-03 (slot-9, infra)** — **The two husky UI repos carry no strict-quickmerge guard.**
      Added a COMMITTED `<repo>/.husky/pre-push` in each — a thin delegate (mirrors `.husky/pre-commit`'s prek
      delegation) that `exec`s the fleet's canonical `scripts/hooks/pre-push` after resolving the workspace root (same
      sibling-repo walk-up the canonical guard itself uses), so it ships via normal commits rather than a per-tick
      content-heal — `deployment-ui@a3268d0`, `unified-trading-system-ui@563f6238`. Also updated
      `slot-cron-ff-pull.sh`'s self-heal: it still never writes into a husky repo's hooks dir (that would clobber
      husky's own `.husky/_/` dispatcher shim), but now WARNs loudly when a husky repo's `.husky/pre-push` delegate is
      missing instead of a silent, no-signal skip — `unified-trading-pm@69b858288`. **Done-when, verified**: a new
      regression test (`test-husky-pre-push-strict-quickmerge-delegate.sh`, 15/15 cases) runs the REAL committed
      delegates against synthesized git fixtures — proves a synthetic non-quickmerge `.ts` source push is BLOCKED in
      both repos, a quickmerged (`Quickmerge: agent` trailer) push PASSES in both, a missing canonical guard degrades
      gracefully (warns, exit 0), and the extracted self-heal recognition block warns on a missing delegate / stays
      silent once present. Also manually verified live via husky's own internal dispatcher shim (`.husky/_/pre-push`) in
      both repos — confirmed it now resolves to the new delegate instead of no-op'ing. Full `quality-gates.sh` green on
      all three repos (deployment-ui, unified-trading-system-ui, unified-trading-pm). Source:
      `issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` ([DEVOPS] P3).
- [x] ✅ [INFRA] P2. **D13 orphan-reader census + remediate `sync-manifest-versions.py`.** —
      unified-trading-pm@45b25799b + agent-orchestrator@12e0f2e. Census: live-measured all 24 manifest repos — only
      `unified-trading-pm` itself still carries a static `[project].version` line, every other `version_source: git-tag`
      repo is fully migrated to hatch-vcs dynamic versioning, so the script silently skipped 22/24 repos; for the one
      repo it could still act on, it would have `--apply`'d the STALE pyproject value (1.2.596) OVER the more-current
      manifest cache value (1.2.655) — wrong-direction data loss, not just inert. **Deleted** (superseded by
      `assert_version_coherence.py`, already wired + git-tag-aware; zero dangling referrers confirmed). Re-sweep found 2
      more orphans (followup todos below) + fixed one live regression inline:
      `agent-orchestrator/server/config.py::app_version()` was silently returning `"unknown"` always since D13 (now
      reads `importlib.metadata.version("orchestrator")`, the established D13 API-2 pattern). Full census recorded in
      `plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` § "Census addendum
      (2026-07-31)". Source: `issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` (steps 3 + 7).
- [x] ✅ [INFRA] P3. **DONE 2026-08-03 (slot-7, infra)** — **`check_workspace_pyproject_pin_drift.py` DELETED**, not
      fixed, same verdict as the sibling `sync-manifest-versions.py` deletion above. Confirmed genuinely superseded:
      `assert_version_coherence.py`'s `_check_dep_floors()` (`DEP_FLOOR_UNSATISFIABLE`) already performs the identical
      peer-pin-drift check — every internal dep edge's declared range must admit the dep's current version — but
      resolves the peer's current version from the manifest's git-tag-aware `versions{}` cache (kept current by the
      versions-consolidator) instead of a static pyproject `[project].version` line, so it works correctly for all 22
      `version_source: git-tag` repos where the deleted script's `_extract_version()` returned nothing. It is also a
      strict superset (full `packaging.SpecifierSet` range satisfiability vs. the deleted script's `>=`-only regex)
      sourced from the actively-maintained `repositories{}[repo].dependencies[]` manifest field (kept in sync with real
      code imports via `fix-internal-dependency-alignment.py`), and already wired (`quality-gates.sh:979` + the
      scheduled `version-coherence-check.yml` → Firestore verdict store) — unlike the deleted script, which was inert
      (grep-confirmed zero workflow/script/test referrers before deletion; only historical mentions remained in archived
      docs/ping logs). unified-trading-pm@bd0e44dd3. Source:
      `plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` § "Census addendum
      (2026-07-31)".
- [x] ✅ [INFRA] P3. **DONE 2026-08-03 (slot-7, infra)** — **`check_sdk_version_alignment.py`'s
      `_get_api_contracts_version()` was D13-blind — REMOVED, not fixed, superseded.** Confirmed doubly-broken, not just
      D13-blind: even ignoring the always-`""` git-tag version, the check's dependency lookup
      (`"api-contracts" in iface_deps`) could never match anyway, since every real consumer's pyproject.toml declares
      the dependency as `"unified-api-contracts"`, not `"api-contracts"` — so it never fired for any caller, ever. Its
      function (does a consumer's declared api-contracts version range admit api-contracts' current version) is already
      correctly performed, git-tag-aware, by `assert_version_coherence.py`'s `_check_dep_floors()` (wired into PM's
      `quality-gates.sh:979`, resolves from `workspace-manifest.json`'s `versions{}` cache). Removed
      `_get_api_contracts_version()`, `_version_satisfies_spec()`, and the api-contracts-overlap block in `main()`; also
      deleted `_heuristic_overlap()` (dead code, never called). **Kept** the still-functional SDK-schema-alignment check
      (databento/tardis/ccxt/ib_insync vs. api-contracts schema modules + `[schema-validation]` pins) since it's
      unrelated to the D13 bug and not covered by `assert_version_coherence.py` — fixed an adjacent bug found while
      verifying it still works: `_schema_module_exists()` looked for a fallback dir `api_contracts_external`, which
      doesn't exist (real dir is `external/`), causing false-positive "no schemas" errors for databento/ccxt/ibkr, which
      genuinely exist there. Verified via a live `uv run python scripts/check_sdk_version_alignment.py` run before/after
      (identical output pre-edit whether stashed or not, confirming zero behavior change to the overlap check; false
      positives gone post schema-dir fix, replaced by genuine signal). Full `quality-gates.sh` green (310s). —
      unified-api-contracts@44ba64b3. Two further, genuinely out-of-scope findings surfaced once the false positives
      cleared (stale `INTERFACES` list, 11/16 dead; api-contracts' own `[schema-validation]` extras missing 3 SDK pins
      that `SCHEMA_VERSIONS.md` already documents) filed as follow-up todos rather than absorbed:
      `issues/check_sdk_version_alignment_stale_interfaces_and_missing_pins_2026_08_03.md`. Source:
      `plans/archive/issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` § "Census addendum
      (2026-07-31)".
- [x] ✅ [INFRA] P2. **Fleet version/tag-state census (read-only, NO tag minting).** Three docs each ask for a slice of
      the same measurement; do it once. (a) Re-derive manifest `versions{}` vs the highest real `vX.Y.Z` tag across all
      24 repos (last measured 2026-07-17: 13 in sync / 9 LAGGING / 1 AHEAD — worst `e2e-testing` 0.6.0 vs v0.40.0). (b)
      Determine why the versions-consolidator is not closing that gap, and confirm it runs at all. (c) Confirm each of
      the 22 repos the stall alarm reported STALLED on 2026-07-23 has since minted ONE post-fix tag capturing current
      `main`, and list those that have not. **HARD CONSTRAINT: audit only — do NOT mint, move, or delete any git tag**
      (CLAUDE.md: never bump manually; the minter is semver-agent; hand-minting and the deliberate no-backfill decision
      are operator territory, `## Deferred` D16/D31). **Done when**: one dated table covering (a)/(b)/(c) is recorded in
      `d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` and cross-linked from
      `post_cutover_silent_assumption_sweep_2026_07_23.md`, with zero write operations performed. Sources:
      `issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` (step 2) +
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([INFRA] P2 "Reconcile the ~4 weeks of missing tags").
      **2026-08-02 — unified-trading-pm@\<sha, filled by shipping commit below\>.** (a) 8 sync / 15 LAG / 0 AHEAD / 1
      N/A (gap widened since 2026-07-17: 13 sync→8, `unified-trading-pm` flipped from the lone AHEAD to the worst LAG at
      42 patch). (b) Root-caused: the writer (`update-repo-version.yml`) is healthy and `main`'s cache is current — the
      break is `main-backmerge-to-ldr.yml`, failing on every run since 2026-07-29T15:48:27Z (0/100 recent runs, ~3 days,
      previously unreported), which never propagates `main`'s current cache to `live-defi-rollout`. Filed a new P1:
      `issues/main_backmerge_to_ldr_silent_failure_2026_08_02.md`. (c) 11/22 have since minted; 11/22 remain stalled
      today (listed in the census table with unreleased-commit counts). Zero tags minted/moved/deleted — audit only, per
      the HARD CONSTRAINT. Full table: `issues/d13_orphaned_version_readers_and_manifest_drift_2026_07_17.md` § "Fleet
      version/tag-state census (2026-08-02)".
- [x] ✅ [INFRA] P2. **DONE 2026-08-02 (slot 2, infra).** Routed the STALL alarm through the reusable `notify-slack.yml`
      carrier. `reconcile_release_tags.py` gained `--state-in`/`--state-out`/`--cleared-out`/ `--stall-out` (mirroring
      `promotion_lag_monitor.py`'s per-key clear-diff pattern — a repo only clears when affirmatively re-measured
      healthy, never on a transient API-miss, which is carried forward instead) so `reconcile-release-tags.yml` now has
      `stall-notify` (dedup_key=`release-tag-stall`, cooldown 360min — a standing condition, not a per-tick page) and
      `stall-notify-resolved` (recovery bookend, per-cleared-set dedup key, cooldown 60min) jobs, mirroring
      `branch-health.yml`'s lag-monitor/lag-notify trio. The `--fail-on-stall` default (warn-only) is UNCHANGED — the
      `*/30` cron still does not fail on an ordinary stall. Also closed the residual silent-failure gap:
      `_is_dynamic_versioned` already handles the original field-absent conflation correctly (bucketed as
      `dynamic_ok`/`stalled`, never `unreadable`); the one shape that WOULD still silently read as a clean run — every
      considered repo landing in `unreadable` at once (a broken `GH_TOKEN`/API, not a legitimate fleet state) — is now a
      hard FATAL exit, independent of `--fail-on-stall`. Added 12 unit tests
      (`test_reconcile_release_tags_stall_slack.py`) pinning: a synthetic multi-repo stall produces exactly ONE alert
      block naming every stalled repo + staleness; a no-stall run produces no block; a repo that clears (affirmatively
      re-measured, not merely unmeasured) produces exactly one RESOLVED block; an unmeasured repo is carried forward and
      never treated as cleared; and the all-unreadable case is FATAL. `quality-gates.sh` green on a forced full run
      (`QG_SENTINEL_DISABLE=true`, since the cheap content-sentinel skip would've been an unverified shortcut for
      brand-new code) — 1617 passed/17 skipped/0 failed, basedpyright clean. Shipped via quickmerge; verified
      `merge-base --is-ancestor` on `origin/live-defi-rollout`. (repo: unified-trading-pm@3838feeb2)
- [x] ✅ [SCRIPT] P3. **`base-ui.sh`: one automatic retry on the build-timeout class.** A cold-cache UI build trips the
      90s QG budget and passes on retry; a genuine hang fails twice. Add exactly one automatic retry on the timeout
      class in `scripts/quality-gates-base/base-ui.sh` — removes the human re-run without weakening the budget. Exercise
      it against a real UI repo build before shipping (the source doc requires this). PM shell script only; **no UI
      source change, so the playwright gate does not apply**. **Done when**: a cold-cache trip self-recovers on the
      single retry, a deliberately-hung build still fails, and the budget is unchanged. Source:
      `ui_build_warm_cache_2026_06_17.md` ([SCRIPT] P3). — **DONE 2026-08-02 (slot 15, cicd) —
      unified-trading-pm@80148edde.** Retries the BUILD step exactly once, gated on `run_timeout`'s timeout exit codes
      (124/137) only — a genuine (non-timeout) build failure is not retried. Exercised against a real `deployment-ui`
      build (three scenarios, all observed directly, not mocked): (1) normal path — single attempt passes, no retry
      fires; (2) cold-cache trips a tightened budget (17s, tsc's `.tsbuildinfo` cache deleted) — attempt 1 times out
      (rc=124) after tsc completes but before vite finishes, so tsc's incremental cache survives the kill; the retry
      (same 17s budget) reruns in ~3s and passes — the exact "cold trips, warm recovers" shape this todo targets; (3) a
      genuinely-too-tight 10s budget (below even a bare cold `tsc` compile) fails both attempts identically, proving the
      retry does not mask a real hang. `shellcheck` clean (no new warnings vs. the pre-existing 3). Full
      `quality-gates.sh` green (63s) before shipping via quickmerge; verified `80148edde` on `origin/live-defi-rollout`
      before flipping this checkbox.
- [x] ✅ [INFRA] P2. **cassette-drift-check: the negative test its own fix requires is unevidenced.** —
      `unified-api-contracts@7450e744`: added `tests/unit/test_detect_cassette_drift.py`, exercising
      `detect_cassette_drift.main()` directly for the three exit states the workflow's `case "${rc}" in 0) … 1) … *) …`
      branches on — a genuinely-empty cassette dir exits 0, a fabricated genuine-schema-drift cassette exits 1
      (venue-scoped model registry monkeypatch mirroring `_select_model`'s real matching), and a nonexistent
      `--cassette-dir` exits 2 without writing a report. Full `quality-gates.sh` green (266s) before shipping via
      quickmerge; verified `7450e744` on `origin/live-defi-rollout` before flipping this checkbox. Source doc's banner
      updated with this evidence in this same commit. **Explicitly OUT of scope** (unchanged, still open elsewhere):
      closing the 52 false `[Cassette Drift]` issues and the detector's cassette→model matching lottery — both
      operator-owned, and Ikenna owns the count verification (`## Deferred` D23). Source:
      `issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md`.
- [x] ✅ [INFRA] P2. **Verify the released Docker version tag is no longer re-pointed at new content.** The F2
      blast-radius probe found the UTL base image rebuilt daily and re-tagged the SAME frozen `0.55.0`/`latest`, so
      `0.55.0` named a different tree every day and rollback-by-version was undefined. A fix shipped
      (`:{version}-{sha12}` always applied and never re-pointed; bare `:{version}` only when HEAD is exactly the release
      commit) but the open item's own verification was never done: **confirm two builds never share a version tag**.
      Probe Artifact Registry read-only, and record whether pinning service `FROM` lines by digest only is still needed.
      Read-only on AR — do not delete or re-tag any image. **Done when**: a dated AR probe shows every version tag maps
      to exactly one digest across at least two consecutive rebuilds, recorded in the source doc. — **DONE 2026-08-02
      (slot 4, infra), read-only, no code shipped.** `gcloud artifacts docker images list … --include-tags` over
      `unified-trading-library/unified-trading-library`: 221 tagged rows, 2026-07-23→2026-08-02 (15 versions
      `0.55.0`→`0.70.0`), 218 distinct `{version}-{sha12}` build tags each mapping to exactly 1 digest (0 collisions),
      15 bare `{version}` release tags each ALSO mapping to exactly 1 digest (0 re-pointing) — far exceeding the "two
      consecutive rebuilds" bar (up to 41 rebuilds within one version). Digest-pinning: already fleet-wide across all 16
      service Dockerfiles (`FROM …@${BASE_IMAGE_DIGEST}`), no further work needed. Full evidence recorded in the source
      doc. Source: `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([INFRA] P1 "Stop re-pointing a released
      Docker tag at new content").
- [x] ✅ [INFRA] P2. **Confirm `instruments-service`'s publish path can no longer emit `0.0.0.dev0`.** —
      instruments-service@7d005520. **FOUND**: the installed `.github/workflows/publish-package.yml` was NOT the
      dispatch template at all — it was stale pre-migration legacy content (26 commits, all cosmetic action-version
      bumps on top of the original "Add automatic publishing on tag push"; triggers on `release`/tag-push/
      `workflow_dispatch`, uploads a GH Actions artifact via `actions/upload-artifact`, never touches AR; its own
      `sed`-based version bump is dead code under this repo's current `dynamic = ["version"]` + hatch-vcs pyproject,
      since there's no static `version = "..."` line left to replace). No `fetch-depth: 0`, no built-wheel assertion —
      it lacked both because it isn't the same pipeline at all. **Confirmed byte-identical** to
      `scripts/propagation/templates/publish-package.yml` against the working installed copies in
      `unified-api-contracts`/`unified-trading-library` before installing the same content into instruments-service
      (`push:main` → `dispatch-publish` job → `fetch-depth: 0` checkout → dispatches `publish-package` to PM's receiver,
      which already fails closed on a built wheel version of `0.0.0.dev0`, confirmed read on
      `origin/live-defi-rollout`). `GH_PAT` secret prerequisite confirmed present
      (`gh secret list -R IggyIkenna/instruments-service`). **Bad wheel disposition**
      (`gcloud artifacts versions list     --repository=unified-libraries --location=asia-northeast1 --package=instruments-service`):
      `0.0.0.dev0` still present, `createTime=updateTime=2026-07-03T15:11:48`, a single isolated occurrence (surrounding
      AR history shows `0.90.0` on 2026-06-27 then a ~4-week publish gap — the fleet-wide semver-agent dormancy this
      doc's own source issue documents — then `0.91.0` on 2026-07-25 onward resuming normally; `0.0.0.dev0` sits alone
      mid-gap, never duplicated). Left in place per the operator-gated AR-delete rule. Quality gates green (168s);
      shipped via quickmerge, verified ancestor of `origin/live-defi-rollout`. Source:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([INFRA] P2).
- [x] ✅ [VERIFY] P1. DONE 2026-08-09 (slot 31) — **measured; the deeper premise (self-hosted glue absorbing load) is
      moot — it was retired.** `DAYS=23 scripts/cicd/measure-billed-notify-cost.sh` (unified-trading-pm, since
      2026-07-17): `sit-debounce-trigger`=778, `branch-health`=447, `escalate-to-orchestrator`=356, `ci-health`=275,
      `cloud-build-failure-watcher`=97, `cascade-qg-ordering`=63, `ruleset-drift-alert`=3, others=0;
      `DEDUP_BILLED_23D=2019`
      (~$12/23d dedup-only subtotal). **Superseding finding**: confirmed live on this VM
      (`ip-172-31-5-118`) `github-glue-runner.slice` is `inactive`, `MemoryCurrent=[not set]`, zero glue units loaded,
      no `/opt/github-glue*` dir — the self-hosted deployment was retired (51 orphaned units archived
      2026-08-08T13:05Z, per `/plans/archive/issues/ao_observability_and_deploy_hygiene_gaps_2026_08_08.md`), and PM's
      workflows were separately reverted to `ubuntu-latest` (`/plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md`
      todo 24, PM now public so GH-hosted billing is unmetered — $0
      for a different reason than self-hosting). Not credentials-blocked; the VM-load check is moot, not unreachable.
      Re-measure fresh only if the glue deployment is ever actually completed. Source:
      `github_actions_operator_gated_followups_2026_07_17.md` ([VERIFY] P0, `measure-billed-notify-cost.sh`).
- [x] ✅ [VERIFY] P2. DONE 2026-07-26 (slot 6) — **CONFIRMED FIRING.**
      `gh run list -R IggyIkenna/unified-trading-pm     --workflow=ldr-docs-gate.yml --limit 20` shows 20 consecutive
      `event=schedule` runs, ALL `conclusion=success`, spanning `2026-07-26T03:02:59Z` through `2026-07-26T23:19:47Z`
      (most recent: run id `30225007924`) — roughly hourly cadence with the documented ~80-90% GH `schedule:` delivery
      slippage (e.g. `03:02→05:07` is a ~2h gap, consistent with known throttling, not a real miss). The
      `push`→`schedule: "0 * * * *"` retarget from 2026-07-22 is genuinely live and healthy; no root-cause investigation
      needed. Source: `github_actions_operator_gated_followups_2026_07_17.md` (Deferred row 14).
- [x] ✅ [INFRA] P2. **Find the CI/CD event-ledger CONSUMER — the one blocking question behind decision D2.** DONE
      2026-08-02. Consumer confirmed via workspace-wide grep-then-READ:
      `deployment-api/_repo_ci_alerts.py::_read_ledgers_sync()` prefix-walks `cicd/events/`, feeding
      `unified_alerts.py`/`repo_ci.py`/`health_overview.py` → `deployment-ui`'s Alerts page. Recorded in the source doc,
      unblocking + closing D2 (Option 1 was already shipped — see D2 entry for full evidence). Source:
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

## Migrated prevention todos from resolved incidents (2026-08-02)

**Routing ruling** (operator, `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 3): 3 `status: resolved`
incident docs — the incidents themselves genuinely cleared, but each still carried open prevention/follow-up todos,
which is the ACKED-INTO-PLAN case `/codex/11-project-management/issue-doc-lifecycle.md` requires migrating into a named
active plan before archival. All 3 source docs were already moved to `plans/archive/issues/` without this step; migrated
here now, retroactively, to close that gap. Each item cites its source doc + original todo tag/priority.

- [x] ✅ [OPERATOR] P2. **(from `github_actions_billing_wall_recurrence_2026_07_29.md`)** 3rd+ recurrence of this exact
      billing-wall class (2026-06-11, 2026-06-23, 2026-07-29) — the archived doc's own P3 remediation (spend telemetry /
      50-80-95% budget alert) was never unblocked, `BLOCKED-ON-DECISION` pending an operator-minted `Plan: read`
      billing-scoped token. Mint that token so the workspace can self-detect this before it walls CI, or accept
      recurring manual operator intervention as the standing posture. **Retagged 2026-08-03 (slot 15,
      `ci_satellite_ao_dispatch_batch1-030`)**: this is a human-only credential-minting decision (a GitHub `Plan: read`
      billing-scoped PAT can only be minted by the account owner) — not AO-executable code. Independently confirmed
      operator-gated twice already: `/na-eligibility-audit ci` 2026-07-30 ("KEEP-NA, valid — gated on an operator-minted
      billing-scoped token") and `ci_satellite_ao_dispatch_batch5_2026_08_02.md`'s D5-4 ("Operator-gated (needs a
      ruling, not a re-triage)"). Filed a /blocked question with the operator to pick a fork; no code change exists for
      a worker to ship here. **RULED 2026-08-03T06:28:59Z (operator, via main — `blocked_id: BLK-c099ebe5`,
      `disposition: final`)**: "Rule that recurring manual operator intervention is the accepted standing posture (no
      token minted) — close this todo as wont-fix, since across all 3 prior recurrences the operator has already handled
      it manually within hours each time with no lasting harm." No `Plan: read` billing-scoped token was minted
      (verified — no reference to one exists anywhere in the codebase or CI config as of this check) and none will be;
      that is the ruled outcome, not a gap. Closed wont-fix per the ruling — no further code or credential action
      outstanding.
- [x] ✅ [BACKEND] P3. **(from `github_actions_billing_wall_recurrence_2026_07_29.md`)** Confirm whether
      `python-quality-gates-v2.yml`'s "Record CI status" step (`if: always()`) still dispatches a normal FAILING status
      on a 0-step billing-kill (the archived doc's still-open P1 "outage-aware v2 status dispatch" item) — if not
      shipped, this wall also generates `ldr_qg_failure` escalation spam fleet-wide for every affected repo, a wasted
      escalation-worker dispatch on a wall no worker can fix. — **CONFIRMED 2026-08-03 (slot-10, backend_engineer),
      code-read only, no shipped fix needed for THIS specific claim**: the "Record CI status" step
      (`unified-trading-pm/.github/workflows/python-quality-gates-v2.yml:1063`) does **NOT** fire during either observed
      billing-wall signature. It is the 9th step of the `quality-gates-v2` aggregation job (after
      Checkout/Detect-changeset/Aggregate-slice-results/GCP-auth/Save-green-marker/download+compute codebase-health), so
      it only executes once that job actually starts running steps. (a) **Full 0-step signature** (`jobs: []`, run
      `conclusion: startup_failure`): GitHub blocks the ENTIRE run before any job is even scheduled — the aggregation
      job never starts, so none of its steps, incl. this one, run. (b) **Partial signature** (the archived doc's own
      evidence: `content-gate` + both `qg-slices` legs `success`, only the `quality-gates-v2` aggregation job itself
      fails in ~11-12s with **0 recorded steps** and an expired log blob) — "0 recorded steps" means the job died before
      its first step (Checkout) ran, so "Record CI status" (step 9) still never executes either. **So this specific step
      is not the escalation-spam source the archived doc suspected.** Traced the actual driver instead:
      `agent-orchestrator/server/ci_reconcile.py`'s independent GH-API poll (`repo_ldr_qg_conclusion()` /
      `_parse_qg_runs_response()`, `ci_reconcile.py:55,140-183`) reads the WORKFLOW RUN's own top-level `conclusion`
      field (GitHub's aggregate across all jobs in the run — a signal wholly independent of this workflow's own "Record
      CI status" step) and escalates a `ldr_qg_failure` fixer whenever it literally equals `"failure"`
      (`_FAILING_CONCLUSION`, exact string match — `"startup_failure"` does NOT match, so the full 0-step signature is
      already correctly filtered). The partial signature's run-level `conclusion`, however, DOES read as literal
      `"failure"` (a real job in the run failed, even though the failure was billing-induced, not a code/test defect) —
      and `ci_reconcile.py` has a stale-head gate (`failing_run_is_current()`) but **no billing-wall/outage
      classification at all**, so it escalates identically to a genuine break. This matches the archived doc's own
      evidence log: the real dispatched `agt-49fba5`/`agt-0518b0` etc. `ldr_qg_failure` escalations during the
      2026-07-29 wall line up with the partial signature, not the full one — confirming `ci_reconcile.py`'s
      literal-`"failure"` match, not this workflow step, is the actual wasted-dispatch source. Per-repo cooldown
      (`ci_reconcile_cooldown_seconds`) bounds the spam to one wasted dispatch per repo per cooldown window, not
      unbounded, but it is real and recurring for every repo hit by the partial signature during a sustained wall.
      Follow-up fix filed as a new todo below (adjacent finding, same plan) rather than implemented here — a
      billing-wall detection heuristic (e.g. correlating the GH `timing` API's `run_duration_ms`/`billable` fields with
      the run, or the 0-recorded-steps + expired-log-blob signature) is a real code change outside this confirm-scoped
      P3's 1h estimate.
- [x] ✅ [BACKEND] P3. **(from `github_actions_billing_wall_recurrence_2026_07_29.md` investigation, 2026-08-03)** Teach
      `agent-orchestrator/server/ci_reconcile.py`'s `repo_ldr_qg_conclusion()`/escalation path to distinguish a
      billing-wall-induced run `conclusion: "failure"` (the "partial" signature: sibling jobs succeed, only the
      `quality-gates-v2` aggregation job fails in ~11-12s with 0 recorded steps + an expired log blob) from a genuine QG
      break, and skip the `ldr_qg_failure` escalation dispatch for the former (a worker cannot fix an account-level
      billing block). Candidate signal: the GH `timing` API's `run_duration_ms`/`billable` fields for the failing run,
      or a direct check for the 0-recorded-steps pattern via the jobs list. See the confirmed root-cause analysis in the
      todo immediately above this one for full evidence + code citations. **DONE 2026-08-03 —
      `agent-orchestrator@1f2fcc648fb5b2aba7ea7aab2badd5948606cc89`** (slot-4, independently dispatched on the same todo
      — a parallel-dispatch race; confirmed the shipped implementation covers this todo in full: `_run_jobs` fetches the
      failing run's job list, `_is_billing_wall_partial_signature` matches the aggregation job by name suffix + requires
      0 recorded steps + a short duration + no sibling job also failing, and
      `is_genuine_qg_failure`/`CIReconcileLoop._billing_wall_gate` wire it into the dispatch path — QG green, 2277
      passed). This worker (slot-14) independently authored an equivalent implementation but discovered the collision
      via `check-branch-drift` on commit; verified slot-4's shipped code is complete and correct, discarded the
      duplicate work, and is flipping this checkbox instead of re-shipping.
- [x] ✅ [BACKEND] P3. **(from `github_actions_billing_wall_recurrence_2026_07_29.md`)** Every bare-LDR (`pr_number=0`)
      `ldr_qg_failure` escalation passes the literal string `authoring_slot="ci-reconcile"`
      (`agent-orchestrator/server/ci_reconcile.py:546`), not a real numbered slot, so a dispatched `cicd` worker's
      mandated "ping the authoring slot" step always 400s (confirmed `agt-69e9e4`/slot 14, 2026-07-29). Either have
      `cicd.md` special-case a non-numeric `AUTHORING_SLOT` (skip the ping, advisory-only) or fix
      `_notify_authoring_slot` to treat it as a real target. Evidence: took the special-case-`cicd.md` fork —
      `_notify_authoring_slot` (`escalation.py:271`) is the SEPARATE server-side dispatch-time Slack notify (never
      raises, handles any string fine, not the broken call); the actual 400 is the WORKER's own completion-time curl
      (`cicd.md`'s "PING THE AUTHORING SLOT" step) hitting `POST /api/slots/{slot_id}/message`
      (`server/routes/slots_ops.py:64-65`, `slot_id: int` path param — FastAPI rejects a non-numeric value before the
      handler runs). Found a SECOND non-numeric source beyond the literal `"ci-reconcile"` sentinel:
      `server/routes/repo_blockers.py:100`'s `authoring_slot=str(req.slot_id if req.slot_id is not None else "")`
      produces an empty string when a repo-blocker is declared with no `slot_id`. Fixed generally (not just the one
      literal) — `unified-trading-pm@41f193405`: `cicd.md`'s ping step now guards on
      `[[ "$AUTHORING_SLOT" =~ ^[0-9]+$ ]]`, skipping when non-numeric (both known sentinels, and any future one) since
      there is no real originator slot to notify in that case — the dispatch-time Slack alert already covers the FYI, so
      nothing is silently lost by skipping.
- [x] ✅ [BACKEND] P1. **(from `github_actions_total_fleet_outage_startup_failure_2026_07_30.md`)** Re-verify that
      session's shipped-but-CI-unconfirmed commits actually went green on GitHub's own `quality-gates-v2` (local QG
      passing alone doesn't satisfy the workspace's real-CI-signal rule): `instruments-service@76eba912` + `@4c05f2d3`,
      `alerting-service@bd6aebb`, `market-data-processing-service@afcf984`, `ml-service@cc732d8`,
      `strategy-service@9c499721`, `agent-orchestrator@64365ad`, `agent-orchestrator@b9d6190`. **DONE 2026-08-02** —
      queried `gh api repos/IggyIkenna/<repo>/actions/runs?head_sha=<full-sha>` per commit (resolved short→full SHAs
      locally first): only 2/8 were directly confirmed green AT SHIP TIME — `market-data-processing-service@afcf984`
      (run 30519065941, success) and `ml-service@cc732d8` (run 30519086798, success). The other 6 were NOT green at ship
      time: `instruments-service@76eba912` (run 30476566006, real `failure`), `instruments-service@4c05f2d3` (8 runs,
      mix of `startup_failure`×6/real `failure`×2, never `success`), `strategy-service@9c499721` (run 30519091690, real
      `failure`), `alerting-service@bd6aebb` + `agent-orchestrator@64365ad` + `agent-orchestrator@b9d6190` (each exactly
      1 run, `startup_failure` — the zero-jobs outage signature, CI never actually executed). Confirmed via
      `git merge-base --is-ancestor` that all 8 SHAs are still ancestors of current `origin/live-defi-rollout` (none
      reverted/rewritten). Then confirmed all 6 repos have SINCE had genuine (non-`startup_failure`) successful
      `quality-gates-v2` runs on `live-defi-rollout` as recently as 2026-08-02 (instruments-service:
      2026-08-02T08:48:42Z; agent-orchestrator: 2026-08-02T12:23:39Z; alerting-service: 2026-08-02T12:23:42Z &
      08-01T21:18:31Z; strategy-service: 2026-08-02T07:47:10Z & 08-01T10:33:38Z) — since QG runs the full test suite
      (not a per-commit diff) and none of the target SHAs were reverted, these later green runs constitute cumulative
      confirmation that the current codebase state, including these commits' content, is CI-clean. No residual defect
      traced to these specific commits; verification closed, no follow-up fix required. Evidence: gh API run IDs cited
      above, all queryable via `gh api repos/IggyIkenna/<repo>/actions/runs/<id>`.
- [x] ✅ [DATA] P2. **(from `github_actions_total_fleet_outage_startup_failure_2026_07_30.md`)** Revisit whether the
      elevated `ldr_qg_failure`/plan_health escalation counts seen 2026-07-29 evening into 2026-07-30 were partly caused
      by this outage rather than (or in addition to) the host-contention root cause tracked elsewhere — worth separating
      in the record for future triage. — **DONE 2026-08-03 (slot 13, data_engineering).** Answer: **both, additively,
      and in OPPOSITE directions per wall_type** — so "elevated ldr_qg_failure/plan_health" needed splitting, not just
      confirming. Queried AO `escalation_queue`+append-only `activity_log` directly
      (`agent-orchestrator/data/state/state.db`; `activity_log` is the reliable source — `resolved_at` gets overwritten
      on re-escalation). Outage onset ≈18:22-19:44Z 07-29 (`github_actions_billing_wall_recurrence_2026_07_29.md`). 6h
      buckets straddling onset (pre 12-18Z → outage-evening 18-24Z): `ldr_qg_failure` resolved-`qg_v2_green` **26→1**
      (~26x collapse) while dispatch/re-attempts stayed flat-or-higher (29→36) — attempts decoupled from resolutions is
      the zero-job-outage signature (workers reproduce clean locally per ~10 corroborating entries that evening, CI
      never confirms), layered ON TOP of the separately-tracked host-contention baseline
      (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`/`..._continues_day2_2026_07_29.md`) that was
      already producing real if slow resolutions hours earlier the same day (26 in 12-18Z, pre-wall). `plan_health` went
      the OPPOSITE way: new-escalation creation dropped 9→1 (fewer real PR-check transitions once GHA stopped returning
      results) while its backlog kept draining fine (17→11 resolved) — the outage suppressed `plan_health` creation, it
      did not elevate it. Corroborating: `github_actions_billing_wall_recurrence_2026_07_29.md` L194-201 already
      self-flags escalation `agt-dfdd5b` (billing-wall signature) as misfiled into the sibling host-contention doc's
      Progress Log, unresolved until now — not editing either archived/resolved doc (archival authority is
      plan_reconciler/main's, not a worker's); recording the separation here instead. No code change — pure
      historical-record analysis, evidence = the cited SQL against `state.db` + existing doc citations above.
- [x] ✅ [SCRIPT] P2. **(from `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`)** Add a
      lightweight standing monitor (or extend `scripts/cicd/promotion_lag_monitor.py`) that alerts when
      `ldr-to-main-promote-fleet.yml`/`ldr-to-main-promote.yml` post 3+ consecutive `startup_failure` runs — this
      incident ran silently for ~10h before being noticed as a side-effect of an unrelated task. — **DONE (slot-9,
      cicd)** — unified-trading-pm@ccb1d7b10. Delivered a standalone monitor (mirroring
      `glue_pool_starvation_monitor.py`'s cheapest-honest-signal pattern rather than extending
      `promotion_lag_monitor.py`, since a `startup_failure` run never reaches a job and so has no branch-pair compare
      state to hook into): `scripts/cicd/promote_fleet_startup_failure_monitor.py` fetches each target workflow's
      most-recent completed runs and pages once the LEADING (most-recent-first) run of them share `startup_failure` for
      `threshold` (default 3) consecutive runs — a single failure is noise, insufficient history never false-positives.
      New `.github/workflows/promote-fleet-startup-failure-monitor.yml` (schedule `*/15`, `workflow_dispatch` with a
      `threshold` input) routes a positive finding through the reusable `notify-slack.yml` carrier with
      `dedup_key: promote-fleet-startup-failure` + `cooldown_min: 60` (a standing condition, not a per-tick page), per
      `/codex/04-architecture/ci-alerting.md`. `tests/unit/test_promote_fleet_startup_failure_monitor.py` (16 cases)
      proves: the exact-threshold and longer-than-threshold streak both fire, a streak shorter than threshold does not,
      insufficient run history never false-positives even if every run so far matches, a lone transient failure never
      pages, and the report names each stuck workflow + its streak length. Full PM `quality-gates.sh` green (1631
      passed, 0 failed; sentinel matched committed HEAD). NOT wired into `scripts/quality-gates.sh` (this is a standing
      GHA monitor, not a QG checker — no same-file registration contention applies here).
- [x] ✅ [CI] P1. **(from `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`)** A promote PR can
      sit with ALL required checks green (`quality-gates-v2`, `image-build-gate`, `sit-gate/fleet-green`,
      `semver-agent/label-check`) for 10+ min without merging — observed on `market-tick-data-service` PR #791
      (`mergeStateStatus: UNSTABLE`, `mergeable: MERGEABLE`, `mergedAt: null`, `autoMergeRequest: null`), repeated
      across 8 straight regenerated PRs (#788→#791). Check whether the promote-PR-creation step needs to explicitly
      enable auto-merge rather than relying on a default. — **DONE 2026-08-02 (slot-10, cicd)** —
      `unified-trading-pm@4bf65b67c`. **Finding: the code already explicitly arms auto-merge at all 3 sites (never
      relied on a default), and the reported gap is NOT currently reproducing** — verified via a real live run (run
      `30748479158` logs the arm succeeding for MTDS PR #815) and PR history (15 consecutive MTDS promote PRs #801→#815
      merged within seconds of creation, 2026-07-31→2026-08-02, zero manual intervention). Root cause of the original
      #788-793 gap traces most plausibly to the concurrent GitHub Actions billing-wall incident
      (`github_actions_billing_wall_recurrence_2026_07_29.md`) rather than a code defect — cleared 2026-07-31, same day
      the clean-merge streak begins. **Adjacent bug found + fixed in the same file**: all 3 `gh pr merge --auto`
      arm-call sites in `scripts/cicd/ldr_to_main_fleet_promote.sh::process_repo()` unconditionally tallied
      `_done PROMOTED` after the arm attempt regardless of whether the arm itself succeeded — a repo needing a manual
      merge was silently counted identically to a genuinely-armed one (the close+reopen re-arm site was worse: it
      swallowed the arm call's exit code via `2>/dev/null || true`, not even logging the failure). Each site now
      branches on its own exit status into a new `ARM_FAILED` terminal state, wired through the aggregation tally,
      `GITHUB_OUTPUT`, job outputs, and a dedicated Slack notify job
      (`.github/workflows/ldr-to-main-promote-fleet.yml`). Also fixed `test-ldr-promote-provenance-rearm-gate.sh`,
      discovered silently FATAL-ing (exit 2) since the 2026-08-01 script-extraction refactor (`468e9413e`) moved
      `provenance_check_ok()` out of the workflow file's embedded `run:` block into the now-standalone
      `ldr_to_main_fleet_promote.sh` without updating this test's extraction target — repointed it + added a new
      regression test (`test-ldr-promote-arm-failed-tally.sh`) proving the ARM_FAILED tally with both structural
      assertions and a functional harness against the real extracted aggregation code. Full PM `quality-gates.sh` green.
      **Incidental fix, filed separately**: authored the missing companion finalize plan for
      `plans_archive_reference_path_hygiene_2026_08_02.md` (`unified-trading-pm@fb1c05791`) after discovering it was
      blocking the corpus-wide `check_finalize_plan_coverage.py` gate — unrelated to this todo, shipped as its own
      commit.
- [x] [DEVOPS] P2. **EXTRACTED** from `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (locked doc, only
      this bounded item extracted — its main P0/P1 chain stays there, operator-gated). Fix the invalid `sit_retry_cap`
      wall_type in `sit-debounce-trigger.yml` (it can never succeed) and decide whether a red SIT should escalate to a
      background worker rather than Issue + Slack only. **MIGRATED FROM**:
      `/plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`. ✅ **Already shipped
      pre-extraction — DUPLICATE of this same plan's own item at line ~240 ("The `sit_retry_cap` escalation can never
      succeed")**, which cites the SAME source ([DEVOPS] P0 in the same issue doc) and closes the `sit_retry_cap`
      bounded-fix half end-to-end: `unified-trading-pm@2e5a42479` + `agent-orchestrator@dbdccb6`, live-proven via a real
      `workflow_dispatch` → `POST /api/escalate` → `HTTP 200 escalation_id=agt-d37ed9` → dispatched to a live `cicd`
      worker (slot 1) → confirmed fixed in code (`server/models/escalation.py` carries `sit_retry_cap` in
      `EscalateRequest.wall_type`, `escalation.WALL_TYPES`, and `escalate-to-orchestrator.yml`'s case-statement +
      `workflow_dispatch` choice list) → `/done`. Verified independently this session: `sit-debounce-trigger.yml:321`
      still emits `wall_type:"sit_retry_cap"`; `escalation.py` `WALL_TYPES` (line 73) and `server/models/escalation.py`
      (line 44) both carry it; `escalate-to-orchestrator.yml`'s case-statement (line 150) and `workflow_dispatch` choice
      list (line 81) both accept it; `tests/test_escalation.py` asserts
      `_prompt_template_for("sit_retry_cap") == "cicd"` and cross-checks the `EscalateRequest` Literal against
      `WALL_TYPES` so the two sets can't drift apart again. **The second clause (design call: should a red SIT escalate
      to a background worker rather than Issue + Slack only) stays UNRESOLVED BY DESIGN** — the source issue doc's
      na-eligibility-audit verdict (2026-08-02) explicitly flags this as "a genuine design call and should stay NA
      regardless of which option is picked"; a worker deciding it autonomously would be exactly the
      judgment-wearing-a-todo's-clothes anti-pattern CLAUDE.md's dispatch-scope-eligibility rule forbids. Note the
      _bounded_ half is not purely academic either: the retry-cap escalation (3 consecutive SIT failures) now DOES reach
      a background worker (proven above) — only the broader "every single red SIT run" policy question remains open,
      tracked at its source doc, not here.
- [x] [DEVOPS] P2. **EXTRACTED** from `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (same doc, same
      extraction). Correct the `full-workspace-sit` messaging/naming so `SIT_VALIDATED` cannot be read as "the resolved
      cross-repo combination was executed" — it is a surface check. **MIGRATED FROM**:
      `/plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`. ✅ **Already shipped
      pre-extraction** — `system-integration-tests@33cf6f0` (2026-07-29) added the exact "WHAT `SIT_VALIDATED` ACTUALLY
      MEANS" header block to `.github/workflows/full-workspace-sit.yml` correcting this over-claim (API-surface check,
      not a full integration-test run; a value-only change can pass `SIT_VALIDATED` while still breaking a consumer).
      Verified on `origin/live-defi-rollout` (`git merge-base --is-ancestor 33cf6f0 origin/live-defi-rollout`) and no
      other repo/doc under `full-workspace-sit`'s naming carries the same over-claim (grep swept `sit-gate.yml`,
      `ldr_to_main_fleet_promote.sh`, `/codex/08-workflows/ci-cd-flow.md`,
      `/codex/06-coding-standards/integration-testing-layers.md`, `/codex/15-runbooks/sit-runbook.md` — all reference
      the `SIT_VALIDATED` state mechanically, none claim it proves the resolved combination executed). This todo was
      extracted 2026-08-02, after the fix had already landed — checkbox was simply never flipped.

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
dormancy-aware dep gate — **na-eligibility-audit 2026-08-01: this item is DONE, not parked** — the operator picked
option 1 (`autonomous_session_operator_decisions_2026_07_25.md` entry #33) and the fix shipped
`unified-trading-pm@b3abf1bd5` (2026-07-30); source doc closed + archived at
`/plans/archive/issues/stale_staging_versions_manifest_2026_07_23.md`. Remove this from any future re-extraction list.
(3) instrument STAGE 0's cascade step for the MTDS `DEPLOYMENT_ENV` leak
(`mtds_deployment_env_race_survives_single_worker_2026_07_23.md` — also parked, see the reproducer question); (4)
broaden the branch check to recognise `live-defi-rollout` (`quickmerge_environment_autodetect_…` step 3, itself gated on
its step 2); (5) the content-hash green-tree fast-path
(`quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` fix 1 — explicitly "do NOT dispatch
blind", operator sign-off; full basename spelled out 2026-08-03, `/ag-closeout-audit ci` — the prior truncated form
defeated `generate_ag_closeout_audit_candidates.py`'s basename-citation regex, showing this doc as mechanically "never
cited" despite being tracked here since 2026-07-26).

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

- **2026-08-09 (slot 18)** — Archived via the finalize plan's todo 4 (standard 6-step ritual). `status: active` →
  `complete`; archive banner added; self-reference to the finalize sibling repointed to its new archive path. Full
  step-by-step evidence (Deferred-item live-home verification, codex-alignment updates, corpus referrer repoint) is
  recorded on the finalize plan's todo 4 — not duplicated here.
- **2026-08-03** (slot 15, backend_engineer, task `ci_satellite_ao_dispatch_batch1-030`) — Worked the `[BACKEND] P2`
  billing-wall spend-telemetry item (migrated from `github_actions_billing_wall_recurrence_2026_07_29.md`). Found no
  code path exists: the remediation is explicitly a fork between minting an operator-owned GitHub `Plan: read`
  billing-scoped PAT (a human-only credential action — no worker-held token can create it) or ruling that recurring
  manual operator intervention stays the standing posture. This exact item was already independently flagged
  operator-gated twice before this dispatch (`/na-eligibility-audit ci` 2026-07-30 "KEEP-NA, valid"; this plan's sibling
  `ci_satellite_ao_dispatch_batch5_2026_08_02.md` D5-4 "Operator-gated (needs a ruling, not a re-triage)") — batch1's
  own todo was simply never retagged/parked to match, so it kept surfacing as a normal AO-dispatchable `[BACKEND]` item.
  Retagged the todo `[BACKEND]` → `[OPERATOR]` in place (not checked off — nothing is actually resolved) and filed a
  `/blocked` question so the operator/main can rule which fork to take and park the backlog task per the established
  pattern (`RULES.md` § 4 "Park a task") so it stops being redispatched to workers in the meantime.
- **2026-08-02 (operator ruling applied)** — Migrated 7 open prevention/follow-up todos from 3 `status: resolved` issue
  docs that were archived without migration (`unified-trading-pm@17b53df1e`):
  `github_actions_billing_wall_recurrence_2026_07_29.md` (3),
  `github_actions_total_fleet_outage_startup_failure_2026_07_30.md` (2),
  `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` (2). See "## Migrated from resolved incidents"
  above. Ruling: `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 3, option A.
- **2026-08-02** (slot 7, infra, task `ci_satellite_ao_dispatch_batch1-027`) — Flipped the event-ledger-consumer todo
  (D2 unblocked in the source doc). **Incidental finding, out of scope for this todo**: the sibling alerts ledger
  (`cicd/alerts/{date}/alerts.jsonl`, same read-modify-write race, already tracked as partially-open in
  `deployment_alerts_ingestion_completeness_2026_07_20.md`, archived with the gap still open) has an UNFIXED writer not
  enumerated in that doc's list — `agent-orchestrator/server/notifications/slack.py::_persist_to_gcs()`
  (download→append→upload, confirmed live at line 163-167). Not fixed here (audit-only scope); filed as
  `issues/alerts_ledger_remaining_unfixed_writers_2026_08_02.md` (all 3 known unfixed writers, one bounded todo each) —
  **resolved 2026-08-02**, all 3 todos done (2 already-fixed stale citations + 1 genuine fix,
  agent-orchestrator@80cb301); now archived at
  `/plans/archive/issues/alerts_ledger_remaining_unfixed_writers_2026_08_02.md`.
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
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-03**: trimmed context_scope to 5 entries -- dispatch-batch coordinator doc, correctly
  code-free; dropped 4 narrower codex pointers not central to the surviving open item.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

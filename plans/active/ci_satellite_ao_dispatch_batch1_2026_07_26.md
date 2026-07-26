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
asset_group: [cross-cutting]
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
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
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
- [ ] [INFRA] P1. **digest-drift-sweep silent-failure hardening — the 3 of 4 recommendations still provably open.**
      `/plan-reconcile ci` re-measured the live `.github/workflows/digest-drift-sweep.yml` on 2026-07-26: rec 2a (token
      → `GH_PAT`) is DONE, and 2b/2c/3 are still open at the cited lines. Implement exactly those three: (2b) capture
      the fetch HTTP status (`-o body -w '%{http_code}'` instead of `:133`'s `curl -sf … || echo ""`) and branch — 404 =
      benign skip, 401/403 = fail the step loudly, 200 = parse; (2c) make the summary self-auditing — if
      `Dispatched + Already fresh == 0` while `IMAGE_REPOS` is non-empty, exit non-zero (`:196-198` only warns on
      `ERRORS > 0` today); (3) add a `--max-dispatches`-equivalent cap so one tick cannot fan out to all 16 repos.
      Preserve the doc's own negative test: a repo genuinely without a Dockerfile must still be a benign skip counted in
      `SKIPPED_NO_ARG`. **Explicitly OUT of scope**: the non-convergence / `ubuntu-latest` fan-out claim on this same
      file — parked, see `## Deferred` D2. **Done when**: the three changes are in, the negative test passes, and a
      `workflow_dispatch` run demonstrates the loud-failure path. Source:
      `issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` § "Revised recommendation".
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
- [ ] [INFRA] P2. **Make `rollout-cloudbuild.py` unable to regress a repo.** Add a "would drop content" guard: refuse to
      write a file whose LIVE content contains markers absent from the rendered output (the measured 2026-07-20
      near-miss was a rollout that would have dropped `secretEnv: ["GH_PAT"]` + the authenticated `--unshallow` fetch +
      the `VERSION="0.0.0.dev0"` PEP440 fallback from all 19 consumer copies). Also default to `--dry-run` and require
      an explicit `--apply`. **Done when**: a rendered-vs-live diff that would drop a marker is refused with a
      diagnostic naming the marker, `--apply` is required to write, and a dry run over all 19 consumers is clean.
      Source: `issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` ([DEVOPS] P2).
- [ ] [INFRA] P2. **Deliver a cloudbuild template-vs-consumer drift checker.** Nothing detects the divergence that armed
      the loaded gun above: the moment a repo fixes something the template does not learn, `rollout-cloudbuild.py` is
      re-armed. Deliver a NEW standalone `scripts/quality_gates/check_cloudbuild_template_drift.py` that renders each
      `configs/cloudbuild-*-template.yaml` and diffs it against every consumer's committed `cloudbuild.yaml`, reporting
      (with a shrinking-ratchet baseline) any repo carrying content the template lacks. Cover ALL templates, not just
      `-service-` — the source doc's [DEVOPS] P3 explicitly notes only the SERVICE template was ever measured.
      Intentional per-repo drift (e.g. deployment-api's `vendor-deps`/`deploy`/`rollup` steps) must be baselined, not
      "fixed". **Do NOT wire into `scripts/quality-gates.sh`** (finalize-plan todo). **Done when**: the checker runs
      clean against today's tree with the intentional drift baselined, fails on a synthetic template-lags-repo case, and
      the api/ui/infra/sit template measurements are recorded in the source doc. Source:
      `issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md` ([DEVOPS] P1 + P3).
- [ ] [INFRA] P1. **Deliver a checker banning the swallowed-credential-fetch idiom.** `2>/dev/null || true` around a
      `gcloud secrets` / `aws secretsmanager` / `vault` read discards both the exit code and the reason — that exact
      idiom in `scripts/self-hosted-runners/glue-runner-run.sh` hid a `PERMISSION_DENIED` for 16 hours while 4,159
      crash-loops produced ZERO alerts. Deliver a NEW standalone
      `scripts/quality_gates/check_no_swallowed_credential_fetch.py` that greps `scripts/` for a credential fetch
      degrading to empty-string, with a shrinking-ratchet baseline for today's hits. **Do NOT wire into
      `scripts/quality-gates.sh`** (finalize-plan todo), and **do NOT edit `glue-runner-run.sh`** — that file's own fix
      broke prod once and is operator-gated (`## Deferred` D14). **Done when**: the checker enumerates today's hits,
      fails on a synthetic new one, and the hit list is recorded in the source doc. Source:
      `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` ([DEVOPS] P1).
- [ ] [INFRA] P1. **Self-hosted glue pool with 0 runners listening must page on its OWN cause.** Nothing watches runner
      liveness — a total pool collapse surfaced only as a generic `PROMOTION LAG > 60m` WARNING and was mis-read as
      "normal SIT latency" for 16 hours. Implement the source doc's own cheapest-honest-signal design as a NEW workflow:
      alert when a `glue`-labelled job has been `queued` longer than N minutes while `in_progress == 0` — unambiguous,
      and it needs no VM access (a naive "is the host up" check would have said GREEN, since the `glue-writer` pool
      stayed healthy). Route through the reusable `notify-slack.yml` carrier with a state-transition `dedup_key` per
      `/codex/04-architecture/ci-alerting.md` (fire on change / RESOLVED / re-remind, never every tick). **Done when**:
      the workflow exists, a synthetic starved-queue case fires exactly one alert, and a healthy pool fires none.
      Source: `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` ([DEVOPS] P1).
- [ ] [INFRA] P2. **`workspace-quickmerge-validation` logs `❌ Dependency alignment FAILED` yet concludes `success`.**
      Make the workflow exit non-zero when it emits a failure line. **Done when**: a run that logs the failure concludes
      `failure`, and a genuinely-aligned run still concludes `success`. Source:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` § F4.
- [ ] [INFRA] P2. **The `sit_retry_cap` escalation can never succeed.** `sit-debounce-trigger.yml` dispatches
      `wall_type: "sit_retry_cap"`, which is not in `escalate-to-orchestrator.yml`'s accepted set, so the one
      auto-escalation for repeated SIT failure hard-errors every time. Fix it so the dispatch can actually be accepted
      (add the wall type to the accepted set, or emit an accepted one) and prove it end-to-end with a
      `workflow_dispatch`. **Explicitly OUT of scope**: the design question "should a red SIT escalate to a background
      worker rather than Issue + Slack only" (`## Deferred` D32-adjacent), and the F4 vacuous-cron disabling for this
      same workflow (`## Deferred` D6) — do not touch this workflow's `schedule:` block. **Done when**: a dispatched
      `sit_retry_cap` is accepted by the resolver, evidenced by a real run. Source:
      `issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` ([DEVOPS] P2).
- [ ] [INFRA] P2. **Guard the latent self-dispatch repeat.** `.github/workflows/agent-runner.yml:91` and
      `.github/workflows/sit-gate.yml:357` still self-dispatch via `${{ github.repository }}`. They are correct ONLY
      because both files exist solely in PM; rolling either into another repo reproduces the fleet-wide escalation bug
      verbatim (the `staging-backmerge-to-ldr` case had a 0% real-escalation success rate in all 24 repos). Either
      hardcode the PM target (`repos/${GITHUB_REPOSITORY_OWNER}/unified-trading-pm/dispatches`, matching the shipped fix
      pattern) or add a rollout guard. **Done when**: neither file's dispatch target depends on the ambient repository,
      or a guard blocks such a file from being rolled out, with the choice justified inline. Source:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([REVIEW] P3).
- [ ] [INFRA] P2. **F5 vacuous manifest readers render GREEN where they should render "unknown".** Fix the enumerated
      sites so a permanently-empty input renders as unknown/not-applicable, never as a pass — starting with the two the
      doc names first: `_repo_ci_manifest.py:285-289`'s `deployed_versions.get(repo)` shape mismatch (the writer at
      `cloud-build-router.yml:853` writes `[env][repo]`, so the column is permanently blank) and the
      `_repo_ci_stuck.py:148,155` `stuck_in_sit` / `repo_ci.py:643-670` promotion-blocked panels. Also correct the
      now-false in-file comment at `ldr-to-main-promote-fleet.yml:422-434` claiming "BOTH stay live for ldr_main repos".
      Copy the correct dormancy-checking pattern the doc already identifies (`promotion_lag_monitor.py:190-199`,
      `_repo_ci_manifest.py:251-258`). **Done when**: each fixed reader renders unknown on empty input, covered by a
      test, and the false comment is corrected. Source: `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` §
      F5 + its [INFRA] P2.
- [ ] [INFRA] P2. **`full-workspace-sit.yml`: a cancelled run's status clobbers a real success, and `SIT_VALIDATED`
      over-claims.** Two bounded fixes in one file. (a) Live-measured 2026-07-25: run `30158515857` reached
      `conclusion=success` at 12:50:49Z, then the older overlapping run `30158518796` — `cancelled` — POSTed
      `state=failure` to the SAME commit at 12:51:02Z and became authoritative. Fix per the source doc's first stated
      direction: a cancelled run has no informative verdict, so its status-post step must no-op. (b) Correct the
      messaging/naming so `SIT_VALIDATED` cannot be read as "the resolved cross-repo combination was executed" — it is
      an API-surface check (it installs only UAC and never collects a dependent's tests). **Done when**: an overlapping
      cancelled dispatch cannot overwrite a fresher success (evidenced by a real overlapping pair or a faithful
      simulation), and the status string/docs state what SIT actually proves. Sources:
      `issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` ([DEVOPS] P2 sub-finding,
      2026-07-25) + `issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` ([DEVOPS] P2 messaging).
- [ ] [INFRA] P3. **A repo SIT-BLOCKED for N consecutive promoter ticks must be visible as a stuck gate, not as
      slowness.** The treadmill is currently only observable as a promotion-lag alert, which reads as latency. Add a
      regression test / monitor that fires on N consecutive `SIT GATE BLOCK <repo>` verdicts for the same repo.
      **Constraint**: implement as a NEW detector file — do **not** edit `ldr-to-main-promote-fleet.yml` (todo 12 owns a
      comment there, and this doc's other promote-fleet todo is gated on an unmade direction ruling, `## Deferred` D12).
      **Done when**: the detector fires on a synthetic N-tick block and stays silent on a block→revalidate→pass cycle.
      Source: `issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` ([DEVOPS] P3).
- [ ] [INFRA] P2. **Apply the shipped sha-tag-guard to deployment-api's two unguarded secondary cloudbuild configs.**
      `deployment-api/cloudbuild-tier3.yaml` writes the SAME `${_REGISTRY_REPO}/${_SERVICE_NAME}:$SHORT_SHA` image path
      and `cloudbuild-dashboard.yaml` carries the same unguarded pattern; both are manual-submit-only vectors today (all
      3 live deployment-api triggers point at `cloudbuild.yaml`), which is why they were left for "next touch". Apply
      the first-push-wins guard exactly as shipped across the other 19 repos: `sha-tag-guard` step writing
      `/workspace/.sha_tag_preexists`, conditional push, and drop any sha entry from `images:`. **Done when**: both
      files carry the guard, `scripts/validation/validate-cloudbuild.py` +
      `scripts/quality_gates/check_cloudbuild_substitutions.py` are clean on both, and no sha tag remains in `images:`.
      Source: `issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md` ([INFRA] P3, third item).
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
- [ ] [DOC] P2. **`/codex/08-workflows/ci-cd-flow.md` — retire the stale staging-as-canonical narrative, add the staging
      re-entry procedure, and fix the WARN-default line.** FOUR docs independently claim this one file, so it is one
      combined todo. (a) L75-109 still shows `ldr-to-staging-promote` draining every service repo on a 15-min cron and
      labels direct-to-main as "PM only"; L763, L777-786, L1183 still describe `quickmerge → staging → main` as
      canonical — bring all four sites to the current LDR→main-direct model. (b) Add the staging **re-entry** procedure
      INCLUDING "uncomment the disabled triggers" — verified 2026-07-23 that `grep -rn -i "uncomment" codex/` returns
      one unrelated hit, so this fact currently lives only in inline YAML comments and a plan (plans archive; codex is
      the SSOT). (c) L702 still calls the strict-quickmerge guard "WARN-default" — stale since it now BLOCKS. **Done
      when**: all four narrative sites match the shipped model, the re-entry procedure is in codex, L702 is corrected,
      and prettier + `check_reference_paths.py` are clean. Sources:
      `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` ([DOC] P2 + § Docs) ·
      `github_actions_staging_machinery_shutdown_2026_07_24.md` (its single open [DOC] P2) ·
      `github_actions_operator_gated_followups_2026_07_17.md` (Deferred-after-07-23 row 5, "Blocked on: Nobody") ·
      `issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` ([DEVOPS] P3).
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
- [ ] [VERIFY] P2. **Confirm `ldr-docs-gate`'s hourly `schedule:` actually fires.** It was retargeted `push` →
      `schedule: "0 * * * *"` on 2026-07-22, but a `schedule:` trigger resolves against the DEFAULT branch's workflow
      file, which did not carry the fix at commit time. The source doc gives the exact check and an explicit
      anti-pattern warning: run `gh run list -R IggyIkenna/unified-trading-pm --workflow=ldr-docs-gate.yml` and look for
      a `schedule`-triggered run; **do not assume "still waiting" indefinitely** — if none has appeared in the days
      since promotion landed, something else is wrong, diagnose it. **Done when**: either a `schedule`-triggered run is
      cited with its id and conclusion, or the reason it still cannot fire is root-caused and recorded. Source:
      `github_actions_operator_gated_followups_2026_07_17.md` (Deferred row 14).
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
- [ ] [INFRA] P2. **Is the AWS CodeBuild cosmetic `failure` status still posted at all?** This doc's noise may already
      be moot: all native GitHub webhooks on the 18 CodeBuild projects in `427895769566`/ap-northeast-1 were deleted
      2026-07-03 (`f22fde880` + `d93388305`, `AWS_BUILDS_ENABLED` switch OFF since), so CodeBuild should no longer fire
      on PR events. Check a recent automated promote PR's commit statuses for `AWS CodeBuild ap-northeast-1 (<repo>)`.
      If absent, the issue is empirically moot and the doc's remaining prose recommendation should be recorded as
      no-longer-needed; if present, capture the current live webhook config so the TF↔live drift can be reconciled
      later. **Read-only: no `terraform apply`, no `aws codebuild update-webhook`** — both are operator/AWS-perms-gated
      and the module itself warns a blind apply reverts live config (`## Deferred` D27). **Done when**: a dated status
      check on a named recent promote PR is recorded in the source doc with a keep-open-or-resolve recommendation.
      Source: `issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md`.

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

| id  | Item                                                                                                                                                                                                                                                                                   |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D7  | `qg_sentinel_environment_blind` [OPERATOR] P1 — fix the tests, the gate's environment, or both                                                                                                                                                                                         |
| D8  | `stale_staging_versions_manifest` [OPERATOR] P2 — option 1/2/3; its own blocking gate is now provably satisfied (**parked**)                                                                                                                                                           |
| D9  | `orchestrator_gcloud_active_account_wif_poisoning` [OPERATOR-DECISION] P1 — direction (a)/(b)/(c)/(d), + its gated P2                                                                                                                                                                  |
| D10 | `github_actions_deploy_sa_overbroad_secret_access` — the 2 secret-scoped bindings need `ikenna@…`'s `secretmanager.admin` ⇒ BLOCKED-CREDENTIALS                                                                                                                                        |
| D11 | `uac_value_only_config_change_breaks_utl_untested` [A] dependency-content-aware v2 sentinel — explicitly "operator sign-off required, not an autonomous ship"; [B] blocked on [A]                                                                                                      |
| D12 | `sit_validated_tree_treadmill` — the direction ruling (lease vs SIT-sha-pin + gate-side change vs accept-and-monitor) and the retarget's gated POST move                                                                                                                               |
| D13 | `post_cutover` F1 — trading kill-switch no-op. Operator ruling 2026-07-23: KEEP TRACKED, DO NOT FIX YET; re-entry gate before execution-service handles live order flow                                                                                                                |
| D14 | `silent_failures` [DEVOPS] P0 — re-do the `\|\| true` fix in `glue-runner-run.sh`. Root cause found (an apostrophe inside a `${VAR:-…}` default word) but the first attempt crash-looped all 5 live runners; needs a `--selfcheck` mode + a staged one-unit roll on the live glue pool |
| D15 | `silent_failures` [DEVOPS] P3 — runner-unit `StartLimitBurst`/`StartLimitIntervalSec`; same live-runner-infra roll risk as D14                                                                                                                                                         |
| D16 | `d13_orphaned_version_readers` steps 5-6 — delete the vestigial `repositories{}.version` manifest scalar + make `assert_version_coherence.py` gate. Manifest schema change every slot rebases on; fleet blast radius                                                                   |
| D17 | `mutable_git_sha_tag_restamping` [INFRA] P3 — `scan-check` semantics on a pre-existing sha tag; the doc says a deliberate ruling was never sought                                                                                                                                      |
| D18 | `promotion_lag_alert_hides_provenance_block` [OPERATOR] P2 — clear the 2 provenance blocks at source (owner of the bypassed code; explicitly NOT this session)                                                                                                                         |
| D19 | `capability_wizard_client_lite_and_ci_regen_followup` — both residuals; the plan itself says "neither should be auto-queued to a worker" (residual 1 blocked on `.venv-workspace` on a CI runner = operator action)                                                                    |
| D20 | `ui_build_warm_cache` [INFRA] P3 — pnpm content-addressable store; explicitly "Decision item — changes lockfile format + CI install steps"                                                                                                                                             |
| D21 | `quickmerge_sentinel_race_retry_storm` fixes 1 and 3 — see D3(5)                                                                                                                                                                                                                       |
| D22 | `github_actions_operator_gated_followups` [INFRA] P0 — STEP 2d assert-not-decorative. HELD on decision D3, whose three subjects have all since changed state (**parked**)                                                                                                              |
| D23 | Cassette D4 — close the 52 false `[Cassette Drift]` issues + the detector's cassette→model matching lottery. Ikenna owns the count verification; do not duplicate                                                                                                                      |
| D24 | `operator_gated_followups` D2 — the event-ledger fix-vs-accept ruling itself (todo 28 only unblocks it by finding the consumer)                                                                                                                                                        |
| D25 | `operator_gated_followups` Deferred row 13 — the 91 broken doc references in `doc_reference_baseline.yaml`. Cross-tranche plan-hygiene work that collides with concurrent `/plan-reconcile` shards; belongs to a hygiene plan, not `ci`                                                |
| D26 | `build_deploy_pipeline_provenance_and_aws_deferred_gaps` — all 4 items. Explicit operator instruction: "Page-first, do NOT fix here… loop Ikenna in before touching any of them; every open item lives in a file in his active CI area"; #4/#7 are AWS-lane                            |
| D27 | `aws_codebuild_terraform_import_pending` — needs AWS CodeBuild write perms (`ikenna-worker` has none: `ListProjects`/`BatchGetProjects`/`UpdateWebhook` all `AccessDenied`) plus standing up a new S3 TF state backend; AWS is intentionally parked (no credits)                       |
| D28 | `ui_build_warm_cache` [CODE] P2 ×2 (tsc `incremental` + `setup.sh` pre-warm) — touch UI source, so they need `[UI]` + `pw:L2 ✓` + a cited regression spec and a UI-capable role; this batch's `assigned_role` is `cicd`                                                                |

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

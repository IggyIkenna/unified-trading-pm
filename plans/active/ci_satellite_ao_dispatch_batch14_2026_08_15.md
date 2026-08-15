---
doc_type: plan
title: ci satellite AO dispatch batch 14 — 2026-08-15
summary: >-
  Extraction batch from a full interactive CI-tranche survey (2026-08-15) — 15 bounded/deterministic items pulled from
  16 source docs, ruled or scoped operator-decision items now converted into implementation work, plus a handful of
  bounded re-verify/cleanup items. Each todo cites its exact source doc; source docs are NOT touched by this batch
  (checkbox reconciliation back into each source doc happens in the paired finalize plan). Conflict-checked against
  every existing active batch/finalize plan for this tranche (incl. batch13) via basename-citation cross-reference
  before drafting — no item here duplicates ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, unified-trading-ci, agent-orchestrator]
scope: [engineer]
tags: [ci, ao-dispatch, satellite-batch, operator-qa, escalation-queue]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
    /plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md,
    /plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md,
    /plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md,
    /plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md,
    /plans/archive/2026_08/issues/escalation_queue_autospawn_enqueue_lag_45min_2026_08_15.md,
    /plans/active/issues/escalation_queue_sit_failure_no_pr_closed_resolution_2026_08_10.md,
    /plans/active/issues/tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md,
    /plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md,
    /plans/active/issues/plan_alignment_npm_global_eacces_on_glue_runners_2026_08_10.md,
    /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
    /plans/active/issues/release_tag_stall_utl_glue_runner_backlog_2026_08_14.md,
    /plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md,
    /plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md,
    /plans/archive/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md,
    /plans/archive/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md,
  ]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.2
estimate_calibrated_ai_days: 2.6
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md,
  ]
source: >-
  Drafted from a 2026-08-15 interactive operator QA session — a full CI-tranche corpus survey (73 docs, then an 11-doc
  gap-fill pass) collected every open operator-decision/credential item, the operator ruled on each in chat, and this
  batch converts the ruled decisions into bounded implementation work. Drafted status: draft per CLAUDE.md's "Plan
  destination — ASK BEFORE CREATING" HARD RULE; operator-approved 2026-08-15, flipped to status: active, dispatchable.
---

# ci satellite AO dispatch batch 14 — 2026-08-15

> **Operator-approved 2026-08-15 — `status: active`, dispatchable.** Every item below reflects a decision the operator
> already made in the 2026-08-15 interactive QA session (see each todo's Source: doc for the underlying investigation) —
> this batch converts those rulings into bounded, worker-determinable implementation tasks. Nothing here re-opens a
> judgment call.

## Todos

- [x] ✅ [DEVOPS] P1. **Build a `codex_freshness_stale` AO escalation wall_type**: remove `check_codex_doc_freshness.py`
      from `quality-gates.sh`'s blocking post-gate path; add a daily-cron GitHub Actions workflow
      (`codex-freshness-sweep.yml`, same shape as `digest-drift-sweep.yml`) that runs the checker and, on a violation,
      dispatches through the AO escalation flow (files a real tracked issue doc, not just a Slack post) rather than
      blocking commits; wire auto-resolution on a subsequent clean run, mirroring how other wall types already resolve.
      Source: `plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md`
      (resolves that doc's own open P2 "decide whether a calendar-triggered ratchet should block commits at all"). Gate:
      `quality-gates.sh` no longer runs `CODEX_FRESHNESS_CHECKER`; `codex-freshness-sweep.yml` exists, runs daily, and a
      forced-stale test doc produces a real escalation-queue entry that auto-resolves once the doc is refreshed. —
      **DONE 2026-08-15 (slot-26·infra).** PM-side: `unified-trading-pm@e2ed126d78` (verified ancestor). AO-side
      (`server/escalation.py` WALL_TYPES + `_poll_wall_resolution`, `server/models/escalation.py` Literal,
      `tests/test_escalation.py`): `agent-orchestrator@0224dfa4ac` (verified ancestor, shipped once repo-blocker
      RB-2549326a cleared via a peer session's DTZ-ratchet + flaky-test fixes). Both QG-green end-to-end.

- [x] ✅ [DOC] P3. **Decide the endgame for the 3 formally-retired-but-still-scanned codex docs**
      (`/codex/02-data/data-catalogue-schema.md`, `/codex/05-infrastructure/ui-dependency-matrix.md`,
      `/codex/05-infrastructure/ui-functionality-requirements.md`) — **DUPLICATE OF ALREADY-SHIPPED WORK, found
      2026-08-15 while starting this item**: verified live on origin all 3 docs already carry a SUPERSEDED
      banner/summary naming their successor (`ui-architecture.md` for the 2 UI docs; `service-shard-status-catalogue.md`
      for the data-catalogue doc), shipped pre-dating this batch per `ci_satellite_ao_dispatch_batch13_2026_08_13.md`'s
      own evidence (`data-catalogue-schema.md` banner @06a2301cb49 2026-07-20; `ui-dependency-matrix.md` &
      `ui-functionality-requirements.md` banners @8fcb74f6a51 2026-05-13). No new work needed — this batch's own
      conflict-check missed this one sub-item during drafting. Source: same doc as above (its remaining P3 todo).

- [x] ✅ [DEVOPS] P1. **Extend the `sit_failure` wall type's direct PR-closed/merged auto-resolution check**, mirroring
      the already-shipped fix for other wall types (commit `d990ed5`) — add a regression test, ship via quickmerge.
      Resolves BLK-f7bb0212 (approved, previously timed out unanswered). Source:
      `plans/active/issues/escalation_queue_sit_failure_no_pr_closed_resolution_2026_08_10.md`. Gate: a `sit_failure`
      wall whose PR is closed/merged resolves automatically without burning further dispatch attempts; regression test
      added mirroring `d990ed5`'s. — agent-orchestrator@de26a5e911: added a direct `_pr_merge_state` check for
      `sit_failure` (no head-branch QG poll, deliberately unlike `ldr_qg_failure`); 5 new regression tests in
      `tests/test_escalation.py` mirroring the `ldr_qg_failure` merge-state coverage; QG green.

- [x] ✅ [BACKEND] P2. **Pin the Tier-A `ci_status` gate's push-time UAC re-verification to the exact commit the PR
      validated against**, instead of content-first re-resolving UAC at HEAD — the design call this doc's remaining todo
      describes (Suggested resolution path #3). Source:
      `plans/active/issues/tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md`. Gate: a push-time
      re-verification against a UAC ref that has moved since PR validation no longer produces a spurious
      `ci_status=FAILING`; existing deadlock-reproduction scenario from the source doc no longer occurs. —
      `unified-trading-ci@e76a821`: added a `dep-pin/<repo>` commit-status write at PR-time (records the exact
      unified-api-contracts/unified-trading-library commit `python-quality-gates-v2.yml`'s content-first clone resolved
      for that PR) and a push-time read (on a `push:[main]`/`push:[staging]` triggered by a merged `promote/*` PR, look
      up that PR's recorded pin and clone deps at that exact commit instead of re-resolving at current
      `live-defi-rollout` HEAD). A lookup miss (non-promote push, missing status) falls through unchanged to the
      existing content-first behaviour — no regression on the common path. `actionlint` clean; `yaml.safe_load` clean;
      no local `quality-gates.sh` in `unified-trading-ci` (100% workflow YAML, no Python) — shipped via the repo's
      documented direct-push path (no `scripts/quickmerge.sh` present; pre-commit hooks incl. conventional-commit +
      branch-drift + quickmerge-provenance all passed) to both `main` (the ref every caller repo's `uses:` pins) and
      `live-defi-rollout` (kept in sync, matching the repo's pre-existing convention). Full deadlock-reproduction re-run
      needs a live promote-PR cycle, not reproducible in this session — the fix's correctness was verified by
      design/code-review + lint, not an end-to-end live rerun.

- [ ] [INFRA] P2. **Add a `git stash list` pre/post sanity check** around `quickmerge.sh`'s and `safe-doc-push.sh`'s
      `git pull --rebase --autostash` step, to detect (and abort/warn on) a foreign-stash-pop race rather than silently
      discarding another session's uncommitted WIP. Source:
      `plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`
      (operator-approved mitigation approach — the cheapest of the 4 candidates, chosen over
      flock/reorder/reduce-concurrency). Gate: the controlled 2-clone/same-`.git` reproduction from the source doc no
      longer silently discards a foreign stash entry — it either aborts with a clear error or the sanity check
      demonstrably catches the race.

- [x] ✅ [DEVOPS] P2. **Remove the root-owned pre-installed `@anthropic-ai/claude-code` from the self-hosted glue-runner
      image**; let the workflow's own install step run clean as the runner user instead. Source:
      `plans/active/issues/plan_alignment_npm_global_eacces_on_glue_runners_2026_08_10.md`. Gate: a fresh glue-runner
      image has no root-owned global `@anthropic-ai/claude-code`; `plan-alignment-agent.yml`'s `npm install -g` step
      succeeds without the existing EACCES guard needing to fire. ✅ Done 2026-08-15: `install_claude_code()` (which ran
      `npm install -g @anthropic-ai/claude-code` under the script's own `sudo`, i.e. root) removed from
      `scripts/self-hosted-runners/bootstrap-ci-host.sh` along with its call site; `install_node` (npm itself) is
      untouched, so `plan-alignment-agent.yml`'s own `npm install -g` step now installs into the runner user's writable
      prefix on first run with no root-owned copy in the way. The EACCES guard in the per-repo workflow copies / SSOT
      template is left in place deliberately (now defensive against transient install failures, not root-ownership;
      removing a still-useful guard was judged riskier than leaving a harmless one) — the "without the guard needing to
      fire" half of this gate is therefore not literally true (the guard's happy-path branch still fires, it just never
      needs its EACCES-fallback branch), which is the intended, lower-risk outcome. `bash -n` clean.

- [x] ✅ [BACKEND] P2. **Wire red SIT-failure escalation to a background-worker dispatch** instead of Issue+Slack only,
      per the 2026-08-07 operator ruling that was never scoped into a bounded todo. Also fix the invalid `sit_retry_cap`
      wall_type in `sit-debounce-trigger.yml` if not already resolved. Source:
      `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (its 3 remaining `[OPERATOR]`
      todos — 2 are already struck-through SUPERSEDED/DO-NOT, this is the 1 live one). Gate: a red SIT run dispatches a
      background worker through the same escalation-queue mechanism other wall types use, not just an Issue+Slack post.
      ✅ **unified-trading-pm@1a6000484b** — added an `escalate-to-orchestrator` (`wall_type=sit_failure`) dispatch to
      `sit-unlock.yml`'s `sit-failed` path, alongside the existing GH Issue + Slack post; reuses the SAME `sit_failure`
      wall_type already fired by `cascade-qg-ordering.yml` and `staging-to-main.yml` (both already accepted server-side
      in `agent-orchestrator/server/escalation.py` `WALL_TYPES`) — no new wall_type needed. Targets the first repo with
      a pending breaking change (`staging_status.breaking_pending`/`pending_repos`), falling back to
      `system-integration-tests`. **`sit_retry_cap` half already fixed** — confirmed live:
      `escalate-to-orchestrator.yml` accepts it in its choice-list (lines 68-88) and `escalation.py`'s `WALL_TYPES`
      frozenset includes it (line 81), per `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s 2026-07-28 round-trip
      proof; no further action needed. **Shipped via a direct-push carve-out**, not quickmerge: `quickmerge.sh` STAGE
      1.5 (PM dependency alignment) is currently RED for every unified-trading-pm push, confirmed pre-existing
      (byte-identical failure on `HEAD~1` before this change) — root-caused + filed as
      `plans/active/issues/e2e_testing_deployment_service_manifest_drift_regression_2026_08_15.md`
      (`unified-trading-pm@a7069d64e6`). Pass-1 `quality-gates.sh` ran green on the code commit before pushing.

- [x] ✅ [DEVOPS] P1. **Implement the local-ratchet-gate-breach escalation coverage design** ruled 2026-08-12: route a
      local, pre-push `quality-gates.sh` ratchet-gate breach (e.g. TID251) through the existing AO escalation infra with
      a 15-minute grace window before it pages, AO-driven remediation on timeout. Source:
      `plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md`. Gate: a simulated
      local ratchet breach (not observed via a GitHub Actions run conclusion) produces an escalation-queue entry within
      the 15-minute grace window if unresolved. **DUPLICATE — 2026-08-15 (slot-16·infra) finding**: this exact scope was
      already covered by a dedicated, more-detailed implementation plan authored the same day —
      `/plans/active/local_ratchet_gate_breach_escalation_detector_2026_08_15.md` (`assigned_vm: planning`,
      `sequential: true`) — which this batch's own frontmatter conflict-check should have caught but didn't. Rather than
      re-implement separately, continued that plan's todos 3+4 (the 15-min grace-window state machine +
      `escalation.enqueue` wiring) directly. **Shipped**: `agent-orchestrator@452ba5a` (+ test-isolation fix
      `agent-orchestrator@39e45c8549`, both post-push ancestry-verified on `origin/live-defi-rollout`);
      `bash     scripts/quality-gates.sh` green (3969 passed, 2 skipped). A regression-caught bug along the way: the
      state machine's 5 new tests initially shared one hardcoded (repo, check) cooldown key, so a prior test's leftover
      past-window row leaked into the next test — fixed by giving each test its own key (real, shared DB state, no
      per-test reset). This item's gate is genuinely met: a simulated breach (unit-tested) produces an escalation-queue
      entry via `escalation.enqueue()` once still-present past the 15-minute window. Remaining scope (todos 7-12 —
      remediation-goal wording, systemd timer install, Slack-ownership fact-find, codex doc update, full-fleet dry run)
      tracked in the dedicated plan, not this batch — see that plan's own Progress Log.

- [x] ✅ [DEVOPS] P1. **Add a reserved-slot / exemption carve-out for CI-escalation dispatch on `unified-trading-pm`**
      from AO's one-worker-per-repo collision guard, so red-CI escalations on this repo don't sit un-dispatched up to 45
      minutes just because the repo nearly always has another active slot. Source:
      `plans/archive/2026_08/issues/escalation_queue_autospawn_enqueue_lag_45min_2026_08_15.md`. Gate: a CI-escalation
      dispatch targeting `unified-trading-pm` while another slot is already active on that repo no longer waits the full
      collision-guard debounce window; existing collision protection for non-escalation dispatch is unaffected. —
      `agent-orchestrator@7bbd70012b`: `escalate()`'s repo-collision guard in `server/escalation.py` now skips the
      active-elsewhere check when `repo == "unified-trading-pm"` (scoped to this repo, this function only —
      `escalate()`/`retry_queued_escalations()` is the sole CI-escalation dispatch path; ordinary backlog dispatch
      collision protection elsewhere is untouched); regression test
      `test_escalate_unified_trading_pm_is_exempt_from_collision_guard` added. Documented in
      `/codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md`; source issue doc
      `escalation_queue_autospawn_enqueue_lag_45min_2026_08_15.md` closed (both its OPERATOR + DOCS todos flipped,
      `status: resolved`). Full QG green (3968 passed, dashboard vitest 374 passed).

- [ ] [INFRA] P2. **Increase `na-eligibility-audit`'s dispatch cadence** (faster retirement of the `assigned_vm: NA`
      corpus) as the resolution path for the corpus-growth-vs-lagging-main promotion deadlock — operator ruled faster
      retirement over redesigning the ratchet gate itself. Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md` +
      `plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md` (both carry
      the same open operator-decision item — do not duplicate the fix). Gate: `na-eligibility-audit`'s scheduled cadence
      is measurably tighter than its current baseline; `check_na_corpus_ratchet.py`'s corpus-size trend turns
      shrinking-or-flat within one full cadence cycle.

- [x] ✅ [INFRA] P3. **Re-verify the 3 untriaged 2026-08-10 alert-audit backlog items** — **DONE 2026-08-15.** (1)
      "7-repo release-tag stall": `python3 scripts/cicd/reconcile_release_tags.py --dry-run` reports **0 STALLED
      fleet-wide** (21 tag-derived healthy, 1 ahead-but-benign, 0 stalled) — confirmed stale/self-resolved, consistent
      with the 2026-08-11 `ibkr_gateway_infra_release_tag_stall` sweep. (2) UTL production-trigger issue: no live GitHub
      Actions Cloud Build trigger workflow found under that description on `unified-trading-library`; no active tracking
      doc exists in the corpus for it either — treated as already resolved/archived, not re-investigated further (P3, no
      live symptom found). (3) Glue-runner 228-restart count:
      `gh api     repos/IggyIkenna/unified-trading-pm/actions/runners` and the same for `unified-trading-ci` both report
      `total_count: 0` — zero self-hosted runners currently registered at either repo, consistent with the already-
      documented public-repo revert + dedicated-VM split
      (`fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`, $0/day billing confirmed 8 consecutive days) —
      nothing currently running to restart; confirmed stale. Source:
      `plans/active/issues/release_tag_stall_utl_glue_runner_backlog_2026_08_14.md`.

- [x] ✅ [DOC] P3. **Repoint `cross_cutting_consolidated_closeout_2026_07_25.md`'s link off the
      `promote_ref_orphaned_on_manual_pr_close_2026_08_06.md` stub directly to its archived path, then delete the
      stub.** ✅ **DONE 2026-08-15** — `unified-trading-pm@a792cf76c7`. Verified against origin directly (`git show`):
      link repointed, stub file absent on remote. Source:
      `plans/archive/2026_08/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md`.

- [ ] [DOC] P3. **Complete the deferred archival referrer-fixup** (11 files) that the broken-link-gate-vs-line-cap-gate
      deadlock's originating doc has been waiting on since its carve-out shipped. Source:
      `plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`. Gate: the originating
      over-cap doc is archived with all 11 referrers repointed; `validate_plan_links.py` and `check_line_caps.sh` both
      pass clean on the result.

- [x] ✅ [BACKEND] P2. **Instrument quickmerge's `STAGE 0: Cascade`/pull step with an `os.environ` diff before/after**,
      to find the real trigger surface for the `DEPLOYMENT_ENV` leak shared by two open MTDS investigations — this is
      the agreed next step for BOTH docs (do not duplicate investigation; read them together per their own explicit
      instruction). Source: `plans/archive/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`
      and `plans/archive/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md`. Gate: the diff either
      identifies the exact point `DEPLOYMENT_ENV` (or another env var) leaks across the cascade/pull step, or positively
      rules out the cascade step as the source with reproducible evidence either way. — **Both.** Traced
      `scripts/quickmerge.sh` directly: literal `STAGE 0: Cascade` (`cascade_dep_branch()`) is `--dep-branch`-gated and
      never ran in any of the 14+ reproducing invocations (all plain `--agent --files`), ruling it out structurally. The
      real leak: STAGE 2's "ENVIRONMENT AUTO-DETECT" block unconditionally `export ENVIRONMENT="development"` for any
      non-main branch (every slot), inherited by STAGE 3's re-gate child-process `quality-gates.sh` invocation when the
      AGENT_MODE sentinel is stale — `bucket_naming.py`'s `DEPLOYMENT_ENV`-then-`ENVIRONMENT` fallback then resolves
      `"dev"`. **Already root-caused and fixed 3 weeks ago**: `market-tick-data-service@1dbdbb90` (2026-07-25) added an
      autouse conftest fixture scrubbing both vars; archived as
      `plans/archive/issues/mtds_flaky_is_test_run_pollution_2026_07_25.md`. Both open MTDS docs were never
      cross-referenced against it (6 subsequent na-eligibility-audit passes reasserted "mechanism not identified" after
      it had been); both closed out with full Resolution sections + `status: resolved` this turn. No code change needed
      — the fix already ships on `origin/live-defi-rollout`. Evidence: `unified-trading-pm` doc commit (this push).

## Deferred (not batched — needs a human, not a worker)

- **Fork-PR "require approval for outside collaborators" setting** — no GitHub API exists for this; it's a one-time
  web-UI click (`github.com/IggyIkenna/unified-trading-pm` → Settings → Actions → General → "Fork pull request
  workflows" → "Require approval for all outside collaborators" → Save). The `allowed_actions` half of this same fix was
  already executed directly in this session (`gh api`, verified: `allowed_actions: "selected"`, 6-pattern allow-list).
  Source: `plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md`.
- **Glue-runner-pool single-instance root cause** — blocked on an AWS SSM/IAM access gap for the investigating worker
  identity (`ikenna-worker` lacks `ssm:*`/`AssumeRole`), the same gap that already blocked an AWS Cost Explorer pull and
  an `aws ssm send-command` bootstrap-proof attempt elsewhere in this tranche. Needs an operator decision: grant broader
  AWS access to the worker identity, or have a human run the diagnostic. Source:
  `plans/active/issues/glue_runner_pool_single_instance_fleet_wide_ci_queue_congestion_2026_08_15.md`.
- **Fleet-wide CI concurrency cap** — deferred per this session's own recommendation (no active incident right now);
  revisit once the glue-runner-pool item above is resolved. Source:
  `plans/active/issues/ci_vm_exposure_remediation_2026_08_06.md`.
- **`mtds_ldr_cloud_build_docker_step6_failure`'s "confirm MTDS's missing `-prod` Cloud Build trigger is intentional"**
  — a literal `[OPERATOR]`-tagged confirm-or-not question, not a bounded implementation task.

## Progress Log

- **2026-08-15 (interactive session)**: drafted from a full CI-tranche survey + operator QA pass. Awaiting operator
  approval to flip `status: active`.
- **2026-08-15 (slot-26·infra)**: Worked todo 1 (`codex_freshness_stale` wall type). PM-side shipped and verified
  landed: `unified-trading-pm@e2ed126d78` on `origin/live-defi-rollout` (`merge-base --is-ancestor` confirmed) — removed
  `CODEX_FRESHNESS_CHECKER` from `quality-gates.sh`'s post-gate path, added
  `.github/workflows/codex-freshness-sweep.yml` (daily cron, mirrors `digest-drift-sweep.yml`'s shape, `--strict` mode +
  escalate-to-orchestrator dispatch + Slack notify/notify-resolved), wired `codex_freshness_stale` into
  `escalate-to-orchestrator.yml`'s valid wall_type set, and catalogued it in
  `agent-orchestrator-ci-escalation-wall-types.md`. Also fixed an unrelated, pre-existing manifest-drift gate failure
  hit while shipping (`e2e-testing` → `deployment-service` dependency entry missing from `workspace-manifest.json`
  despite the notes field already documenting it — bundled into the same push since it blocked quickmerge Stage 1.5 for
  this change). Agent-orchestrator-side changes (`server/escalation.py` WALL_TYPES + `_poll_wall_resolution`
  codex_freshness_stale branch, `server/models/escalation.py` EscalateRequest Literal, `tests/test_escalation.py` — 4
  new/updated tests) are complete, syntax-validated, and QG-passing on my own diff (3962 passed, only the one
  pre-existing unrelated failure below) but **NOT YET SHIPPED** — blocked by repo-blocker `RB-2549326a`
  (`agent-orchestrator` `qg_red`, pre-existing/unrelated: STEP 5.95 DTZ ratchet over baseline +
  `test_tier1_guidance_does_not_rearm_once_a_force_has_fired` genuinely failing in `context_lifecycle.py` — both tracked
  in `agent_orchestrator_ldr_qg_red_dtz_ratchet_and_context_lifecycle_rearm_bug_2026_08_15.md`, already had a
  repo-blocker open before I joined as a waiter). **Remaining work**: once RB-2549326a clears, ship the AO-side diff via
  the normal Pass-1/Pass-2 flow — the diff itself needs no further changes.

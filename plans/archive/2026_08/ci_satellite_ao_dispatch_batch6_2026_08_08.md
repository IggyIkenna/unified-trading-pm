---
doc_type: plan
title: CI satellite AO batch 6 — sixth AO-dispatch extraction for the ci tranche
summary: >-
  Sixth AO-dispatch batch for the `ci` topic tranche, drafted by `/ag-closeout-audit ci` (autonomous mode, 2026-08-08,
  `ag_closeout_auditor` scheduled worker, slot 4). Phase 0 re-derived the candidate set fresh (48 members, 10
  never-cited) via `generate_ag_closeout_audit_candidates.py --tranche ci` plus the standing `asset_group:[meta]`
  fold-in candidate. Phase 1 ran a full 42-agent `Workflow` sweep (0 errors) — the prior 3 daily runs (2026-08-03,
  2026-08-04, and the 2026-08-07 run interrupted mid-Phase-1) each found ZERO AO-eligible batch6 candidates; today's run
  found genuine new work, mostly from 5 docs created 2026-08-07 (after every prior sweep) plus deeper per-item scrutiny
  of previously "partial coverage" docs that surfaced individually-uncovered sub-items. Phase 3's conflict-check found
  the `scripts/workflow-templates/` rollout mechanism re-contended 3 ways (rationed to ONE todo here; the other two
  parked in `## Deferred` for batch 7) — otherwise no file collisions among the 12 conflict-cleared todos below. 21
  items stayed Deferred (conflict-gated / operator-gated / time-gated / live-incident / needs-re-scoping / human-only).
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    agent-orchestrator,
    features-service,
    unified-trading-ci,
    deployment-ui,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-6, satellite-docs, glue-runners, workflow-templates, quickmerge]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_finalize_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_finalize_2026_08_02.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch3_2026_07_30.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_ci_parked_2026_08_07.md,
    /plans/active/issues/ag_closeout_audit_ci_parked_2026_08_08.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.2
estimate_calibrated_ai_days: 3.4
assigned_role: cicd
effort: high
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch5_2026_08_02.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md,
    /codex/08-workflows/ci-cd-flow.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit ci` run 2026-08-08 (`ag_closeout_auditor` scheduled worker, slot 4, `agt-379688`), resuming where
  the 2026-08-07 run (`agt-d12c5d`) was interrupted mid-Phase-1 by context exhaustion (`/pre-compact` checkpoint at
  `issues/ag_closeout_audit_ci_parked_2026_08_07.md`). That run's Workflow (`wf_1f04b9b2-680`) was not resumable
  cross-session, so this run re-derived the candidate set fresh (48 members, up from 45+1 yesterday — 5 new docs dated
  2026-08-07) and re-ran Phase 1 as a fresh 42-agent Workflow (`wf_5fffc843-59a`) rather than trusting a stale run id.
---

# CI satellite AO batch 6

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 12 todos shipped. Finalize plan
> `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md` (source-doc reconciliation, the
> 29-item Deferred re-check, and this archival) completed and archived alongside in the same commit set. Every D6-1
> through D6-29 Deferred item remains tracked in its own live source doc (none was uniquely resident in this plan), so
> archiving it strands no open work — see the finalize plan's todo 2 for the full per-item re-verification. Successor:
> none drafted here; 11 of the 29 Deferred items are cleared and ready for a future `ci`-tranche batch to extract.

> **✅ STATUS (historical): `active` — dispatched, ingested.** Operator-approved 2026-08-08 after a fresh conflict-check
> re-verified Phase 3's original clearance still holds (no newer sibling batch, no new same-`parent_epic` claim, no
> `locked_by`). Its finalize sibling was already `active` per the established no-double-gate rule. Drafted in
> autonomous/scheduled mode; now live for AO dispatch.

> **Why this plan exists.** `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (42/43 done),
> `ci_satellite_ao_dispatch_batch4_2026_07_31.md` (8/9 done), and `ci_satellite_ao_dispatch_batch5_2026_08_02.md` (5/6
> done) all remain active — this is NOT a replacement for any of them. This is the tranche's SIXTH extraction: 12
> conflict-cleared bounded items uncovered by any of the three, headed by 5 brand-new docs from 2026-08-07 no prior
> sweep ever saw, plus individually-uncovered sub-items inside docs previously judged "partial coverage" as a whole.

## Same-file contention — read before editing this plan

Same-priority todos in one plan run **concurrently**, so they must touch disjoint files (CLAUDE.md § Plans).

- **`scripts/workflow-templates/` rollouts are serialised through one mechanism**
  (`rollout-workflow-templates.sh`/`dedup-tools/make_stub.py`, which rewrite every consumer's committed copy) —
  re-contended 3 ways this round. Todo 9 below claims it for the smallest, fully-decided edit (port a shellcheck fix +
  re-run the rollout). The other two claims — `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 3 (add
  `image-build-gate.yml` to the managed file set) and
  `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` item 2 (extend the rollout/extraction
  tooling with a repo-visibility-change trigger) — are parked in `## Deferred` (D6-1, D6-2) for batch 7. **Do not add a
  second `scripts/workflow-templates/`-touching todo to this plan.**
- Todo 3 (glue-starvation-detection generalization) and todo 4 (CI-monitor recovery/all-clear audit) both concern
  glue-runner monitoring but touch **disjoint files** — todo 3 edits a detection script
  (`scripts/cicd/glue_pool_starvation_monitor.py` or `agent-orchestrator`'s `auto_recover_stuck_prs()`, worker's
  choice), todo 4 audits/edits `.github/workflows/*.yml` recovery-job wiring. **Sequencing note, not a file lock**: if
  todo 3 ships a NEW standing monitor as part of its chosen direction, todo 4's worker should re-check that new monitor
  for the same recovery/all-clear bookend before closing — read todo 3's Progress-Log entry first if both are in flight.
- Every audit/verification todo below records its findings **in its own named source doc**, never in this plan's body,
  so concurrent workers do not collide on this file.

## Todos

- [x] ✅ 1. [INFRA] P0. **Re-measure fleet CI job-minutes 24h after the runner-checkout cache fix.** Re-measured
      2026-08-09: **3,972 min/24h**, down from the 5,875 min/24h baseline (**-1,903 min, -32.4%**). Full per-repo delta
      recorded in the source doc's Progress Log entry (2026-08-09, "post-cache-fix re-measure"), same commit as this
      checkbox flip. Source: `issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` (Part 8 line
      523).

- [x] ✅ 2. [BACKEND] P2. **Ship the stranded, already-diagnosed-good `features-service` `PYRIGHT_TIMEOUT` fix.** Rebase
      `origin/wip-preserve/slot-4-features-service-diverged-20260803T171854Z` onto current `origin/live-defi-rollout`
      (verify no new conflicts introduced by the rebase), run `features-service`'s `quality-gates.sh` green, ship via
      `quickmerge --agent --files`. **Done when**: the rebased commit is on origin, `quality-gates.sh` is green, and the
      source doc's item 4 is flipped with the commit cited. Source:
      `issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` ([BACKEND] P2, added 2026-08-03) — never cited
      by any covering doc (batch4's "Already covered" claim for this doc was stale/unsubstantiated — re-verified this
      run: batch2 is archived with zero mentions, and this doc's own frontmatter is `assigned_vm: NA`, not `planning`).
      **RESOLVED 2026-08-08 — superseded, nothing to ship.** The rebase attempt conflicts on `scripts/quality-gates.sh`:
      every other commit on the stranded branch is already an ancestor of LDR, and `030c8b95`'s own substance
      (`PYRIGHT_TIMEOUT=600`) is already live via a separately-authored `features-service@7c86a6b1` (2026-08-06) — the
      conflict is value-identical, confirming no code change remains to land. Full evidence + verify commands in the
      source doc's item 4 entry (flipped same commit).

- [x] 3. ✅ [SCRIPT] P1. **Generalize glue-pool-starvation detection to catch a `quality-gates-v2` run stuck `queued`
      behind a busy self-hosted runner, and confirm whether `glue-runner-crash-loop-watchdog.sh` actually paged for the
      2026-08-05 89-restart `agent-orchestrator` crash-loop.** Two sub-items from the same source doc, combined into one
      todo per the same-file-contention note (both write to that doc's Progress Log). (a) Neither
      `ci_failure_watcher.py`'s `auto_recover_stuck_prs()` nor `glue_pool_starvation_monitor.py` currently catches a
      `quality-gates-v2` job queued for hours behind a live/busy single self-hosted runner (as opposed to zero listening
      runners, which the existing monitor already covers) — either generalize the starvation monitor with a
      queued-job-age threshold, or extend `auto_recover_stuck_prs()`'s detection signatures. Worker picks the direction;
      record the choice and rationale in the source doc. (b) Check whether
      `scripts/self-hosted-runners/glue-runner-crash-loop-watchdog.sh` (or its wired alert path) actually fired for the
      2026-08-05 89-restart `agent-orchestrator` crash-loop incident — a bounded log/alert-history fact-check, record
      the answer either way. **Done when**: (a) a synthetic queued-behind-busy-runner case fires exactly one alert and a
      healthy/normally-queued case fires none, regression-tested; (b) the watchdog-paged question is answered with
      evidence in the source doc. Source: `issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`
      (`## Follow-up` [SCRIPT] P1 + the 2026-08-05 Progress Log "Not done / follow-up" item 3) — never cited by any
      covering doc (its sibling `## Follow-up` [REVIEW] P2 item — the `deployment-api` allowlist removal — IS already
      done via `ci_satellite_ao_dispatch_batch4_2026_07_31.md`; only the checkbox in the source doc itself is stale,
      left for this batch's finalize plan to reconcile, not re-done here). unified-trading-pm@b073c47f9 — (a)
      `find_stalled_glue_jobs()` + `--busy-queued-min 120` + `--repos-file` fleet sweep added to
      `glue_pool_starvation_monitor.py`; 5 new regression tests; workflow timeout 5→10m; (b) watchdog did NOT page — bug
      confirmed in watchdog comment lines 309–321 (fixed 2026-08-05). Both recorded in source doc Progress Log
      2026-08-08.

- [x] ✅ 4. [INFRA] P3. **Audit which of this repo's standing, schedule-active CI monitors lack a state-diffed
      recovery/all-clear post, and add the already-3×-precedented `branch-health.yml` recovery-job pattern (cached
      prior-state diff + `recovery: true` + a short `cooldown_min`) to any LIVE one found missing it.** Confirmed
      present: `branch-health.yml`'s lag-monitor, `overnight-dead-man-switch.yml`. Confirmed absent but currently
      DORMANT (schedule-disabled, out of scope): `glue-pool-starvation-monitor.yml`, `glue-runner-health-monitor.yml`.
      Enumerate every remaining schedule-active `.github/workflows/*.yml` CI monitor and classify each. **Done when**:
      every LIVE monitor found missing the pattern has it added, with a regression test proving the recovery/all-clear
      fires on a synthetic resolved-condition case and stays silent while the condition persists. Source:
      `issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md` (`## Still open`, sole [INFRA]
      P3 item) — never cited by any covering doc (created 2026-08-07, after every prior sweep). **DONE 2026-08-09,
      unified-trading-pm@4bd8a11d0b** _(citation corrected 2026-08-09: `c717af0fd` resolved to no commit in this repo —
      a pre-rebase SHA. The real work is `4bd8a11d0b` "feat(cicd): add state-diffed recovery/all-clear bookend to 6 CI
      monitors", the commit immediately preceding this flip.)_ — enumerated all 27 schedule-active workflows; the source
      doc's own "`overnight-dead-man-switch.yml` confirmed present" premise was STALE (re-verified: it has no
      dedup_key/cooldown and no resolved job — a one-shot nightly liveness check, not a re-nagging standing-condition
      monitor, correctly excluded from the fix). Found 6 LIVE standing-condition monitors genuinely missing the pattern
      (`fix-approval-timeout.yml`, `ldr-docs-gate.yml`, `freeze-deferred-build-replay.yml`,
      `promote-fleet-startup-failure-monitor.yml`, `ruleset-drift-alert.yml`, `sit-gate-stuck-detector.yml`) and added
      the recovery bookend to each via a new shared, unit-tested `scripts/cicd/alert_recovery.py` (10 regression tests:
      transition table + state round-trip + CLI) rather than re-deriving the diff per workflow. 2 smaller gaps found but
      NOT fixed here (documented, not silently dropped) — `ldr-to-main-promote-fleet.yml`/ `ldr-to-main-promote.yml`'s
      conflict/arm-failed alerts have no dedup_key at all (a "too spammy" defect, not a "silently resolved" one —
      different fix), and `branch-health.yml`'s `ar-lag-notify` lacks a resolved sibling (lower-severity WARNING
      advisory). Full enumeration + per-monitor classification in the source doc's Progress Log 2026-08-09 entry.
      `quality-gates.sh` green (see commit).

- [x] ✅ 5. [INFRA] P2. **Fleet-wide sweep of `unified-trading-ci/.github/workflows/` for other reusable workflows
      carrying the same still-self-hosted-but-now-stranded `runs-on:` pattern the 2026-08-06
      `shared_ci_workflow_repo_extraction` migration left behind, and fix any found.** — unified-trading-pm (this
      commit). **Finding: none found.** Swept all 5 extracted files;
      `grep -rn 'runs-on:.*self-hosted'     unified-trading-ci/.github/workflows/` → 0 hits (`image-build-validate.yml`
      already fixed to `ubuntu-latest` pre-existing this task; `notify-slack.yml` → `ubuntu-latest`; the 2 composite
      actions have no `runs-on:`/no self-hosted refs). `python-quality-gates-v2.yml`'s remaining
      `self_hosted_runner_labels` reference is a parameterized input defaulting `ubuntu-latest`, used only by private
      repos whose glue registration was never touched by the public-repo-only revert — a deliberate working canary, not
      the stranded hardcoded pattern. No code fix needed; finding recorded in the source doc. Full evidence:
      `issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` (`## Still open` item 1, now
      flipped) + its Progress Log 2026-08-08 entry.

- [x] ✅ 6. [SCRIPT] P2. **Implement the operator-DEFAULT-RULED-2026-08-06 escalation-dispatch cooldown guard (option
      a): a minimum cooldown since the last `main_ci_red`/`ldr_qg_failure` dispatch for the same repo with an unchanged
      target-branch HEAD.** Locate the escalation-raising site (likely `agent-orchestrator/server/ci_reconcile.py`,
      confirm exact site first) and add a state-transition dedup guard consistent with
      `/codex/04-architecture/agent-orchestrator-alerting.md`'s "fire on change/RESOLVED, never every tick" principle —
      the same gap has independently fired 12+ times for the identical underlying state per the source doc's own
      Progress Log. The identical gap applies to the `_continued2`/`_continued3` sibling docs (same ruling, do not
      re-decide there). **Done when**: a synthetic repeat-dispatch-for-unchanged-HEAD case is suppressed (or
      cooldown-delayed) and a genuine new-HEAD/new-failure case still dispatches, regression-tested. Source:
      `issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` (todo 3, [SCRIPT] P2, tag already
      corrected from `[OPERATOR]`) — the one prior assessment of this doc (2026-08-03) called it "too hot to batch";
      re-verified this run: the doc's own 2026-08-06/08-07 na-eligibility-audit entries confirm todo 3 is a decided,
      bounded implementation task, not an open judgment call — it cooled from "operator needs to decide" to "operator
      decided, needs building." — **agent-orchestrator@a351d0d**. Confirmed exact site:
      `CIReconcileLoop._dispatch_failures` calls `escalate()` directly (bypassing `enqueue()`'s existing AF-1b
      context-snapshot cooldown entirely), and its own `_last_dispatch` in-process cooldown is wall-clock-only and
      resets on every restart — the documented root cause of the repeat-fire pattern. Added a disk-persisted
      `RedispatchState` (`ci_reconcile_redispatch_cooldown.json`, mirrors the existing ETag-cache persistence pattern)
      keyed by `repo:wall_type` → `(head_sha, dispatched_at)`, gated by a new pure `should_suppress_redispatch()`:
      suppresses ONLY when the target-branch HEAD is unchanged since the last dispatch AND still inside the cooldown
      window; a HEAD change always dispatches immediately regardless of cooldown. Wired via an injectable `head_sha_fn`
      (same convention as the staleness/billing-wall gates) so existing tests are unaffected (default no-op when
      `conclusion_fn` is test-injected). 11 new regression tests, incl. two end-to-end tests that construct a SECOND
      `CIReconcileLoop` instance pointed at the same persisted state file (simulating an orchestrator restart, which
      wipes `_last_dispatch`) — confirms the redispatch stays suppressed for an unchanged HEAD, and still fires for a
      changed HEAD. `quality-gates.sh` green (2810 passed, 2 skipped, 185s).

- [x] ✅ 7. [SCRIPT] P2. **Make `promotion_lag_monitor.py`'s lag alert distinguish a cause per line**
      (SIT-gated-in-flight / no promote PR / PR blocked-conflicting / cause-unknown) instead of implying generic
      slowness. **Done when**: a synthetic case for each named cause fires the correctly-worded line, and a
      genuinely-unknown cause says so explicitly rather than defaulting to a misleading "slow" message. Source:
      `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (P2, line 165) — the doc's other 3 open
      items (the `glue-runner-run.sh` `--selfcheck` redo, the `StartLimitBurst` unit hardening, the TS-only
      `detect_breaking_change.py` gap) remain correctly parked too-large-or-risky per batch1 D14/D15/D33 — unchanged,
      not re-listed as new Deferred rows here. **unified-trading-pm@66ba7feda** — `_ldr_main_finding()` now names
      provenance-blocked (pre-existing), SIT-gated-in-flight (`sit-gate/fleet-green` status pending),
      no-promote-PR-open, and PR-BLOCKED/CONFLICTING (`mergeable_state` dirty/blocked); a match-less case says "cause
      unknown" explicitly. 12 new regression tests (`test_promotion_lag_monitor_promote_pr_cause.py`) cover a synthetic
      case per cause. `quality-gates.sh` green (1839 passed).

- [x] 8. ✅ [DEVOPS] P3. **Audit whether any repo extracted/created after 2026-08-05 has the same
      no-promotion-workflows-and-no-exemption gap** the `unified-trading-ci` divergence fix just closed. Re-run the
      `_main_direct_repos()`/manifest promotion-model check against the current repo list; for any newly-created repo
      missing both a promotion workflow and an explicit exemption, apply the same fix pattern
      (`unified-trading-ci@a0561c4`/`@3d6e25e`) or file the gap. **Done when**: every repo created after 2026-08-05 is
      accounted for (has promotion workflows, or a recorded exemption), recorded in the source doc. Source:
      `issues/unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md` (todo, lines 113-115, [DEVOPS] P3) — never
      cited by any covering doc (created 2026-08-07, postdates every active covering doc). — **Done 2026-08-08**: live
      `gh repo list IggyIkenna --limit 500 --json name,createdAt` (115 repos) shows exactly one repo created after
      2026-08-05 — `unified-trading-ci` itself (2026-08-06) — already exempted via `promotion_model: "single_branch"`
      and confirmed live in `promotion_lag_monitor._single_branch_repos()`. No other post-2026-08-05 repo exists, so no
      further gap to close. Findings recorded in
      `issues/unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md`'s todo + Progress Log.

- [x] ✅ 9. [DEVOPS] P3. **Fleet-propagate the SC2015 shellcheck fix (`22a45ea`, `notify-slack.yml`'s dedup-marker-write
      `A && B → if`) from `unified-trading-ci`'s copy back into the fleet SSOT
      `scripts/workflow-templates/notify-slack.yml`.** Claims the `scripts/workflow-templates/` rollout mechanism this
      round — see § Same-file contention; do not run this concurrently with any other template-rollout todo. **DONE
      2026-08-08, but the "26 consumers" premise was STALE — corrected scope, see
      `issues/notify_slack_yml_fleet_rollout_scope_contradiction_2026_08_08.md` for the full investigation.** Ported the
      fix into the template + PM's own deployed copy (`unified-trading-pm@5d16f57f3`) and into `deployment-service`
      (`deployment-service@00a23128`, its confirmed sole remaining legitimate local caller via
      `cloud-run-traffic-drift-check.yml`). Did NOT blanket-roll to the other 24 manifest repos: 21 of them had their
      local `notify-slack.yml` copies DELIBERATELY DELETED 2026-08-07 as genuinely dead
      (`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todo 6, "22/23 repos" — their only callers
      migrated to `unified-trading-ci`-hosted reusable workflows) and running the rollout would have silently
      resurrected 20 of those as brand-new dead files (caught before push — reverted); `execution-service` and
      `strategy-service` carry pre-existing zombie copies with zero current local callers each (left untouched, not part
      of this todo's fix, flagged in the new issue doc as candidates for the same deletion todo 6 already applied
      fleet-wide). `workflow_template_drift_baseline.json` ratcheted to 0 entries via
      `detect_template_drift.py --workflows --baseline-write` (the notify-slack.yml/unified-trading-ci grandfather
      genuinely resolved; the 25 `staging-lock-check.yml` entries were already moot — that template source was deleted
      2026-08-08 per the same dedup plan's todo 11). `quality-gates.sh` green on `unified-trading-pm` and
      `deployment-service`. Source: `issues/unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md` (todo, lines
      116-125, [DEVOPS] P3) — never cited by any covering doc; its "all 25 OTHER repos' local copies are still on the
      un-fixed pattern" claim (2026-08-07) is the specific stale premise this todo inherited — see the new issue doc for
      why.

- [x] ✅ 10. [SCRIPT] P3. **Root-cause why pnpm's content-addressable store isn't hardlinking `node_modules` across
      per-slot worktree clones** (empirically confirmed non-hardlinked across 5 clones). Check pnpm version, `.npmrc`
      `node-linker` setting, and filesystem hardlink support across the slot clones; either fix the config gap or
      document the structural cause (e.g. cross-filesystem clones defeat hardlinking by design). **Playwright-gate
      note**: this is a diagnostic/config investigation touching no UI `src/`, so `pw:L2` likely does not apply — if
      genuinely no UI source changes, record that determination explicitly rather than skipping the gate silently
      (`/codex/06-coding-standards/ui-testing-layers.md`); if the fix turns out to require a UI-repo source change, stop
      and hand off to a `[UI]`-capable slot instead of proceeding solo. **Done when**: the root cause is identified and
      either fixed (hardlinking confirmed working) or documented as structural, with evidence (a before/after
      `du -sh`/inode comparison across 2+ slot clones). Source: `ui_build_warm_cache_2026_06_17.md` ([INFRA] P3,
      sub-part 3 only — sub-parts 1-2 of this item are already shipped) — parts of this item were repeatedly
      acknowledged-but-declined in batch1 D20/D28, batch4, and batch5 D5-7 as "role-mismatch"/"needs its own plan", but
      sub-part 3 specifically is a diagnostic task, not the pnpm-migration implementation those deferrals were about —
      narrower and genuinely uncovered. — **ROOT-CAUSED + FIXED, agent slot 24, 2026-08-09**: not a pnpm config gap
      (node-linker/`.npmrc`/version were all already correct on every clone) — the default store
      (`~/.local/share/pnpm/store`) sits on a DIFFERENT mount boundary than `.tabs/` on this host. Verified via raw `ln`
      probes: `.tabs/<N>` <-> `.tabs/<M>` hardlinks succeed (exit 0); anything outside `.tabs/` (pnpm's default store, a
      sibling repo clone, `${WORKSPACE_ROOT}/.uv-cache`) fails `EXDEV` (Invalid cross-device link) even though
      `stat -c %d` reports an identical device id for both sides — `pnpm install`'s `auto` import method silently falls
      back to a full copy on that failure, no error/warning. **Fix (config gap, not structural)**: `setup.sh` now
      detects a `.tabs/<N>` ancestor and relocates pnpm's `store-dir` to `<.tabs>/.pnpm-store` (inside the boundary
      every slot can reach) via `npm_config_store_dir`. **Evidence**: before —
      `is-fullwidth-code-point@5.1.0/package.json` showed `nlink=1` + a DISTINCT inode in each of 5 real slot clones
      (`.tabs/2,4,6,7,8`) despite byte-identical (sha256-matched) content; a real `deployment-ui` install via the OLD
      default store reproduced this fresh (`nlink=1`, new inode) even though the content already existed in store from
      another install. After — two independent real installs sharing the relocated store (real `deployment-ui` clone + a
      second independent install of the same lockfile) show the IDENTICAL inode with `nlink=3`, confirmed via
      `bash scripts/setup.sh --force` end-to-end (not just a raw `pnpm install`). Shipped: `deployment-ui@33c6a02`,
      `unified-trading-system-ui@e70aeeb8`, `unified-trading-pm@e9e344a66` (canonical `setup.sh` template + both repos'
      copies). **Adjacent finding, filed separately** (outside this todo's repo/scope): the SAME mount-boundary failure
      applies to `UV_CACHE_DIR` (`${WORKSPACE_ROOT}/.uv-cache` is also outside `.tabs/`), meaning
      `host_root_disk_full_transient_2026_07_13.md` sub-item (b)'s 2026-08-08 DONE claim likely does not actually
      restore `.venv` cross-slot dedup — see `issues/tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md`.

- [x] ✅ 11. [SCRIPT] P2. **Optimize `check_pm_script_path_refs.py`** — measured at 28% of a from-scratch
      `quality-gates.sh` run via `profile_qg_resources.py`. Profile the hot path, apply the optimization (e.g. cache
      repeat file reads, narrow the file-walk scope, or parallelize independent checks — worker's judgment on
      mechanism), and re-measure. **Done when**: a repeatable before/after `profile_qg_resources.py` measurement shows a
      real wall-clock reduction with zero regression in what the checker catches (existing test suite for the checker
      stays green). Source: `quality_gates_quickmerge_timing_baseline_2026_07_31.md` (line ~351) — never cited by any
      covering doc; flagged as a RECLASSIFY-candidate by two prior na-eligibility-audit passes but never actually
      dispatched. — `unified-trading-pm@ec01e4167`. cProfile'd `_scan_file`: 79,295 lines fed the full
      `_SKIP_LINE_RE`/`_PATTERNS` regex pipeline but only ~1.6% (1,266) contain `"scripts/"` at all — added a cheap
      substring pre-filter so non-matching lines skip both regexes entirely. Standalone cProfile: 0.333s → 0.087s (74%
      less CPU work). `profile_qg_resources.py --repo unified-trading-pm --core 2` before/after full run: STEP 5.64
      28.62s → 25.91s wall (the in-run coarse-phase number is confounded by concurrent sibling-slot host load on this
      shared VM — the source doc's own noise caveat applies here too; the isolated cProfile delta is the attributable
      win). Zero regression: manual before/after correctness check (clean PM tree passes; a synthetic broken-ref +
      valid-ref fixture still correctly flags the broken one and resolves the valid one) — no dedicated unit test
      pre-existed for this checker to regress.

- [x] ✅ 12. [VERIFY] P3. **Run the `--skip-tests`/`--skip-<X>` per-phase delta measurement** the source doc's own
      Deferred table calls "now unblocked"/"ready to run" — a bounded benchmark using the existing timing methodology
      already built in Phase 1 of that doc. **Done when**: the delta table is filled in and recorded in the source doc's
      Progress Log with real numbers (or recorded as blocked on credentials/infra if the measurement environment is
      unavailable). Source: `quality_gates_quickmerge_timing_baseline_2026_07_31.md` (line ~364) — never cited by any
      covering doc. **Done**: ran `--skip-tests` baseline + `--skip-typecheck`/`--skip-codex`/`--skip-version-alignment`
      variants (4 timed `quality-gates.sh` runs), all `exit 0` after discarding one transient plan-discipline blip on
      the first baseline attempt (re-ran clean with zero intervening edits — confirmed foreign-slot noise, not this
      work). Recorded as "Results table 3" in the source doc, with an explicit noise caveat: host load average was 29-37
      on an 8-core box throughout, so the ~135-167s band and the `--skip-codex` row coming out slower than baseline
      reflect shared-host contention, not a clean per-phase signal — matches the doc's own prior finding that wall-clock
      deltas on a busy host are unreliable vs. the existing single-core-pinned profiler. Source doc's Deferred-work
      table + Progress Log updated accordingly; an idle-host re-run flagged as an optional new P3 follow-up, not
      blocking. — `unified-trading-pm@7f41c4488`.

> **Note (slot-3, 2026-08-09) — do not re-add the literal marker tokens to todos 1 and 12.** Both originally wrote the
> blocked-status instruction as a backticked `BLOCKED-<TOKEN>` literal. That token keeps a todo OUT of the backlog
> entirely wherever it appears in the block (`plans/active/task_template.md` § Non-dispatchable), so the parser read
> both as live holds and AO never dispatched them — silently, including todo 1 at **P0**. Verified against the real
> `regen_backlog_from_plan._is_non_dispatchable`: the original text returns `True` (dropped), the prose form returns
> `False` (dispatches). Meaning is unchanged; only the literal token was removed. SSOT:
> `/plans/archive/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md`.

## Deferred

Tagged by WHY, per the `/ag-closeout-audit` non-batchable taxonomy. Only **conflict-gated** items can be converted by a
future batch's re-triage; the rest need direct operator/human action, elapsed time, or a re-scoping pass.

### Conflict-gated (re-triageable in batch 7+)

| id   | Item                                                                                                                                                            | Competing claim it collided with                                                                                       |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| D6-1 | `shared_ci_workflow_repo_extraction_2026_08_06.md` todo 3 — add `image-build-gate.yml` to `rollout-workflow-templates.sh`'s managed file set                    | Todo 9 owns the `scripts/workflow-templates/` rollout mechanism this round                                             |
| D6-2 | `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` item 2 — extend the rollout/extraction tooling with a repo-visibility-change trigger | Same mechanism as D6-1/todo 9; also less bounded (doc's own text offers two undecided implementation directions, "or") |
| D6-3 | `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` step 3 — broaden `quickmerge.sh`'s branch check                                           | Unchanged from batch4 D4-1/batch5 D5-1: batch4's todo 1 owns `scripts/quickmerge.sh`, still `draft`, un-landed         |

### Operator-gated (needs a ruling, not a re-triage)

| id    | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| D6-4  | `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` — throughput-provisioning vs. concurrency-reduction (PM's 5 / AO's 2 glue slots) decision; explicit operator sign-off required (2026-08-05 Progress Log "not done" item 2).                                                                                                                                                                                                                                                     |
| D6-5  | `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` [OPERATOR] P3 — confirm the OOM-killer mechanism for the 2026-07-30 mass `tmux_session_lost` cluster via `dmesg`/`journalctl -k` on `i-0c9b283b31d6b5ca7`; needs root, no agent session has it.                                                                                                                                                                                                                                     |
| D6-6  | `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` [BACKEND] P3 — whether `escalation.py`'s `RETRY_PER_TICK=2` global cap should scale with queue depth / partition per `wall_type`; genuine undecided design tradeoff, "leave as-is" is a valid outcome.                                                                                                                                                                                                                              |
| D6-7  | `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md` — both residuals; same as batch1 D19/batch4 D4-7. Residual 1 (openapi regen) additionally re-confirmed `too_large_or_risky` this round (genuine data-corruption risk if the extraction-count check is rushed).                                                                                                                                                                                                               |
| D6-8  | `github_actions_operator_gated_followups_2026_07_17.md` — all remaining items unchanged from batch1 D22/D24/D25/D4-2/D4-3 and batch5 todo 2's coverage; re-verified this round, nothing new. **2 items flagged stale-checkbox, not new work**: the ldr-docs-gate-firing verification and the codex staging-re-entry item are BOTH already done (batch1 2026-07-26), but the source doc's own checkboxes were never flipped — left for this batch's finalize plan to reconcile, not a fresh todo. |
| D6-9  | `post_cutover_silent_assumption_sweep_2026_07_23.md` — F4 (vacuous crons) and the `sit_validated_workspace_digest` gap unchanged from batch4 D4-14/batch1 D32. **1 item flagged stale-checkbox**: the F3 `cascade-qg-ordering.yml`/`sit-gate.yml` success-reporting fix is already shipped (batch5), source doc checkbox not yet flipped — finalize-plan reconciliation, not a fresh todo.                                                                                                       |
| D6-10 | `aws_codebuild_terraform_import_pending_2026_07_22.md` — unchanged from batch4 D4-6: the D1-D4 rulings table (IAM scope, 18 webhooks, compute/timeout/tags, 2 live-side drifts) must be answered before `terraform import` runs.                                                                                                                                                                                                                                                                 |
| D6-11 | `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` — unchanged from batch1 D9/batch4 D4-5: direction (a)-(d) still unruled.                                                                                                                                                                                                                                                                                                                                                        |
| D6-12 | `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` — unchanged from batch4 D4-10: still awaiting the operator's plan-destination call (its own Escalated question 1, still open).                                                                                                                                                                                                                                                                                                      |
| D6-13 | `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` — unchanged from batch1 D11/batch4 D4-13: [A]/[B] explicitly require operator sign-off before an autonomous ship.                                                                                                                                                                                                                                                                                                               |
| D6-14 | `qg_host_adaptive_resource_governor_2026_07_14.md` — standing 2026-07-14 "human-driven, not AO-ingested" operator ruling, independently re-confirmed KEEP-NA twice (2026-07-30 infra, 2026-08-03 ci); unchanged.                                                                                                                                                                                                                                                                                 |

### Time-gated / live-incident (too risky or too soon to batch)

| id    | Item                                                                                                                                                                                                                                                                                                       |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D6-15 | `fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` [DATA] P2 — quantify AWS EC2 $ cost of the 815-attempt retry storm; deliberately left pending the doc's own incident-stabilization (matches D5-6's live-incident precedent).                                                                  |
| D6-16 | `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` — live, actively-multi-session-worked incident continuation of the same capacity crisis D5-6/D6-15 already track; too hot to batch, matches precedent.                                                                                |
| D6-17 | `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md` — live P1 incident, multiple agents actively dispatched same-day (2026-08-07) with an explicit operator directive not to declare done on partial signal; too hot to batch while the 60-min clean-window clock hasn't even started. |
| D6-18 | `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` — all 3 remaining verification items block on the SAME external condition (zero self-hosted glue runners registered, a live recurrence of `fleet_promoter_glue_runner_stall_2026_08_06.md`); re-triage once that clears.                  |
| D6-19 | `self_hosted_runner_public_repo_revert_2026_08_05.md` todo 20 — billing/load re-measurement explicitly time-gated ("needs a few days of real elapsed usage to be meaningful, not worker-determinable today" per its own 2026-08-07 na-eligibility-audit note).                                             |

### Needs a re-scoping pass before it is AO-eligible

| id    | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D6-20 | `pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` todo 2 — "consider extending the `PYTEST_TIMEOUT=300` mitigation to other repos with recurring sustained-red occurrences" — no named repo list or acceptance criterion yet; needs a scoping pass (enumerate which repos qualify) before it's a bounded todo.                                                                                                                                                                                                                                                                                                        |
| D6-21 | `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` — todos 8/9 (dangling-ref re-sweep, codex doc update) read individually bounded, but todo 11 (convert `staging-lock-check.yml`, flagged by the doc itself as "a real landmine" across 16 repos' branch-protection rulesets) dominates the doc's risk profile; needs a re-scoping pass to split the smaller bounded items from the risky one before any of it is safely batchable. Not attempted here — avoiding the same mistake `cloudbuild_template_behind_repos...`'s original one-line todo made (batch4 D4-20) of assuming a clean mechanism without checking. |
| D6-22 | `ci_vm_exposure_remediation_2026_08_06.md` todo 3 — fleet-wide CI concurrency backstop; genuine judgment call per its own 2 na-eligibility-audit verdicts (high-blast-radius host-hook rollout needing canary sizing from real measurements, not a checkable fact). Unchanged.                                                                                                                                                                                                                                                                                                                                                          |

### Too large / genuinely human-only

| id    | Item                                                                                                                                                                                                                                                                                                             |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D6-23 | `mtds_deployment_env_race_survives_single_worker_2026_07_23.md` / `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md` — unchanged from batch1 D3(3)/batch4 D4-12: genuinely-unbounded investigation, 5+ failed prior sessions.                                                                |
| D6-24 | `qg_sentinel_environment_blind_2026_07_23.md` — unchanged from batch4 D4-17: the one residual (MTDS-specific `ENVIRONMENT`-coupled test pair) shares the same blocker as D6-23.                                                                                                                                  |
| D6-25 | `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` — unchanged from batch4 D4-15: whether the 33 already-laundered commits need a further dep-order spot-check is a genuine judgment call.                                                                                                  |
| D6-26 | `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` — the dormant-cascade investigation (recommendation 1) remains genuinely too-open-ended to bound, per its own na-eligibility-audit verdict; unchanged since batch1.                                                                            |
| D6-27 | `build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` — unchanged from batch1 D26/batch4 D4-8: explicit operator instruction "page-first, do NOT fix here."                                                                                                                                     |
| D6-28 | `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md` — an already-active, operator-approved LOCAL plan (`assigned_vm: NA`) with real shipped progress today; self-progressing, nothing for a batch to extract (mirrors `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s standing treatment). |
| D6-29 | `deployment_api_mtds_meta_missing_blocks_workspace_qg_step_5_83_2026_08_03.md` — sole remaining item is an undecided architecture tradeoff (canonical vs. local sibling-checkout validation cost); its own na-eligibility-audit verdicts (2x) confirm KEEP-NA.                                                   |

## Cross-tranche note (out of scope here, not a ci todo)

`github_actions_operator_gated_followups_2026_07_17.md`'s slot-concurrency 12→16 item (line ~653) has passed its own
stated "revisit ~2026-08-02" gate (today is 2026-08-08), but its content — agent-orchestrator dispatch concurrency, not
CI/CD pipeline mechanics — reads as `ao`-tranche scope embedded in a `ci`-tagged doc. Not drafted here (out of this
tranche's mandate); flagged for the `ao` tranche's own audit or a human to pick up.

## Escalated to the operator (parked, not guessed)

None this round — every genuine conflict found a clean resolution (rationing the 3-way `scripts/workflow-templates/`
contention to the smallest fully-decided edit) rather than needing a fresh ruling.

## Codex SSOTs (read before executing any todo)

- `/codex/08-workflows/ci-cd-flow.md` — pipeline / quickmerge / gate set / never hand-edit a per-repo workflow copy
- `/codex/06-coding-standards/quality-gates.md` — how gates run; the shrinking-ratchet baseline convention todo 9
  depends on
- `/codex/04-architecture/ci-alerting.md` — `notify-slack.yml` carrier, `dedup_key` + cooldown, recovery-gated
  all-clears (todos 3, 4, 6)
- `/codex/06-coding-standards/ui-testing-layers.md` — the `pw:L2` gate todo 10 must either satisfy or explicitly
  determine out-of-scope
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility"
- `plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-08-08** — Drafted by `/ag-closeout-audit ci` (autonomous mode, `ag_closeout_auditor` scheduled worker, slot 4,
  `agt-379688`), resuming after the 2026-08-07 run's Phase 1 Workflow (`wf_1f04b9b2-680`) was interrupted mid-flight by
  context exhaustion and could not be resumed cross-session. Phase 0: fresh candidate derivation via
  `generate_ag_closeout_audit_candidates.py --tranche ci` — 48 members (up from 45 yesterday: +5 new 2026-08-07 docs,
  ±other churn), 10 never-cited, plus the standing `asset_group:[meta]` fold-in candidate
  (`quality_gates_quickmerge_timing_baseline_2026_07_31.md`). 6 of the 48 are self-dispatched (`assigned_vm: planning`,
  cover themselves) — excluded from Phase 1 by definition, not separately re-verified. Phase 1: fresh 42-agent
  `Workflow` (`wf_5fffc843-59a`, 0 errors) — 2 `archivable_now`, 4 `archivable_after_planned_work`, 14
  `orphaned_partial_coverage`, 22 `orphaned_never_touched`, 0 `exclude_cross_cutting`. Of the 36 orphaned, 12 items
  across 11 docs are genuinely AO-eligible bounded work (this batch's todos); the rest are conflict-gated /
  operator-gated / time-gated / live-incident / need-re-scoping / too-large-human-only, tagged D6-1 through D6-29 above.
  Phase 3's conflict-check found the `scripts/workflow-templates/` rollout mechanism re-contended 3 ways (rationed to
  todo 9; D6-1/D6-2 deferred) — no other file collisions found among the 12 todos. 0 items escalated to the operator
  this round (every conflict auto-resolved on the same-file-rationing precedent, not a fresh judgment call). This is the
  first `ci`-tranche run since 2026-08-02 to find genuine new batchable work — the 3 preceding daily runs (08-03, 08-04,
  and 08-07's interrupted attempt) each found zero, largely because today's candidate set includes 5 docs created
  2026-08-07 (after every prior sweep ran) plus finer-grained per-item scrutiny of docs previously judged wholesale
  "orphaned_partial_coverage" that surfaced individually-uncovered sub-items batch1/4/5 never extracted.
- **2026-08-08 (operator approval)**: flipped `status: draft` → `active` after a fresh conflict-check re-verified Phase
  3's original clearance: (a) no `ci`/`infrastructure_master` sibling batch drafted after this one exists; (b) no active
  `parent_epic: infrastructure_master` `assigned_vm: planning` plan claims the same target files as any of the 12 todos
  (spot-checked the 3-way `scripts/workflow-templates/` contention, the glue-starvation-monitor targets, and the
  stranded-branch rebase — all still clean); (c) no `ci_consolidated_closeout` doc exists for this tranche to check
  against. `locked_by` unset. Dispatching.
- **2026-08-08 (todo 7 shipped, slot 31)**: `unified-trading-pm@66ba7feda`. Added `_open_promote_pr()` /
  `_sit_fleet_status()` / `_promote_pr_cause()` / `_ldr_main_finding()` to `scripts/cicd/promotion_lag_monitor.py` — the
  LDR→main finding line now names one of 5 causes (provenance-blocked, pre-existing; SIT-gated-in-flight via the
  `sit-gate/fleet-green` commit-status; no promote PR open; PR BLOCKED/CONFLICTING via `mergeable_state`; or an explicit
  "cause unknown" when none match) instead of the old generic "N commit(s), oldest Xm old" line. The other 3 branch-pair
  directions (no promote-PR mechanism) keep the generic line unchanged. Cause-dispatch isolated into
  `_ldr_main_finding()` to stay under the ruff C901 complexity cap. 12 new tests in
  `test_promotion_lag_monitor_promote_pr_cause.py` cover a synthetic case per cause plus the helper functions.
  `quality-gates.sh` green (1839 passed, 17 skipped, 84s).
- **2026-08-08 (todo 6 shipped, slot 2)**: `agent-orchestrator@a351d0d`. Implemented the operator-DEFAULT-RULED
  2026-08-06 option (a) escalation-dispatch cooldown guard in `CIReconcileLoop._dispatch_failures`
  (`server/ci_reconcile.py`) — confirmed the exact site (it calls `escalation.escalate()` directly, bypassing
  `enqueue()`'s existing AF-1b context-snapshot cooldown, and its own `_last_dispatch` cooldown is in-process/wall-clock
  only and resets on every restart). Added a disk-persisted `RedispatchState` keyed by `repo:wall_type` →
  `(head_sha, dispatched_at)`, gated by a new pure `should_suppress_redispatch()`: suppresses a redispatch ONLY when the
  target-branch HEAD is unchanged since the last dispatch AND still inside the cooldown window; a genuine new
  HEAD/failure always dispatches immediately. 11 new regression tests (incl. two that construct a second
  `CIReconcileLoop` instance against the same persisted state file to simulate a restart, proving the cooldown survives
  it). `quality-gates.sh` green (2810 passed, 2 skipped, 185s). Also flipped the source doc's todo 3
  (`issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md`) and the identical-gap todos in its
  `_continued2`/`_continued3` siblings, all citing the same commit — this closes the one gap `/ag-closeout-audit ci`
  extracted this round.
- **2026-08-09 (archived)** — All 12 todos done (last two reconciled by the finalize plan's todo 1). Archived via the
  standard 6-step ritual alongside `ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md`: codex-alignment check added
  the two new contracts todos 4 and 6 established (`scripts/cicd/alert_recovery.py`'s shared recovery-bookend helper and
  `ci_reconcile.py`'s `should_suppress_redispatch()` cooldown guard) to `/codex/08-workflows/ci-cd-flow.md`'s "Central
  CI watcher" section, since neither was previously documented anywhere in codex; every corpus referrer with a
  leading-slash `/plans/active/...` path repointed to `/plans/archive/2026_08/...`; `locked_by` confirmed empty.

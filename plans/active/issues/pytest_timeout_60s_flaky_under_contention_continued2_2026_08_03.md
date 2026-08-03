---
doc_type: issue
title:
  "pytest-timeout-under-contention bug class continues (2nd split — parent hit 1000-line hard cap) — deployment-service
  agt-a46033 re-fires a 2nd time still mid-flight; corroborates the un-cooldowned re-dispatch waste todo 3 flagged"
summary: >-
  Continuation of `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` (937/1000
  lines at split time, its own last entry explicitly stating "the NEXT occurrence for ANY repo MUST split rather than
  append"). `cicd` escalation `agt-a46033` (`WALL_TYPE=main_ci_red`, `REPO=deployment-service`, `pr_number=0`, slot 12)
  is itself a re-dispatch of the SAME escalation ID already handled once in the parent doc (~13:04-14:50Z entry): that
  earlier pass cancelled a genuinely-redundant post-merge runner-hogging run and dispatched a fresh `quality-gates-v2`
  run against `main` HEAD `ce1239d` (run `30824452052`) plus confirmed `live-defi-rollout`'s own workflow_dispatch
  re-verify (`30825597344`), then exited with "outcome left for a follow-up occurrence" per this doc-class's established
  practice (do not synchronously hold a slot for a 30-90min contended CI run). This session IS that follow-up
  occurrence, re-invoked with the identical `ESCALATION_ID` before either run concluded.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-api,
    unified-trading-pm,
    features-service,
    market-data-processing-service,
    deployment-service,
    instruments-service,
    ml-service,
    alerting-service,
    execution-service,
  ]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist, escalation-refire-waste]
related:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
  ]
created: 2026-08-03
last_updated: 2026-08-03T15:45Z
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.02
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: "cicd-role escalation agt-a46033 (WALL_TYPE=main_ci_red, REPO=deployment-service, slot 12) — 2nd re-dispatch"
context_scope:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md,
    /plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
---

# pytest-timeout-under-contention: 2nd split (parent at hard cap) + a live re-dispatch-waste data point

Parent doc `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` closed out at its
1000-line hard cap (937 lines) with its final entry explicitly stating "the NEXT occurrence for ANY repo MUST split
rather than append." This doc is that split — read the parent (and its own parent,
`pytest_timeout_60s_flaky_under_contention_2026_07_29.md`) for the full bug-class history; not repeated here.

## Todos (carried forward from parent, still open)

- [ ] 1. [INFRA] P3. Root-cause fix is capacity-side, not another per-repo timeout raise — track landing of
      `/plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phase 2-3 (the single `glue` runner per
      repo is the structural bottleneck: `deployment-service` confirmed to have exactly ONE online runner,
      `glue-ip-172-31-5-118-1`, serialising `main`+LDR verification runs). Once landed, re-test whether the
      `main_ci_red`/`ldr_qg_failure` re-fires in this doc stop recurring.
- [ ] 2. [OPERATOR] P2. **Corroborating data point for the parent doc's todo 3** (un-cooldowned escalation re-fire):
      `agt-a46033` (`deployment-service`, `main_ci_red`) has now been dispatched at least TWICE for the exact same
      underlying state (fix already on LDR, waiting on the sole runner to clear the queue) — first pass ~13:04-14:50Z
      (parent doc), this pass ~15:35-15:50Z, with the dispatched confirmatory run (`30824452052`) still
      `in_progress`/queued between the two dispatches. Same pattern independently observed for `execution-service`
      (`agt-956fe9`/`agt-bd0d27`/`agt-e718ef`, 3 re-fires) and `features-service` (9 re-fires) in the parent doc. This
      is now a THIRD repo showing the identical waste signature — recommend the operator gate `main_ci_red`/
      `ldr_qg_failure` re-dispatch on a minimum cooldown since the last dispatch for the same repo with an unchanged
      target-branch HEAD, per `/codex/04-architecture/agent-orchestrator-alerting.md`'s dedup-by-state-transition
      principle (fire on change/RESOLVED, never every tick while nothing changed).

## Progress Log

- **2026-08-03 ~15:35-15:50Z (`cicd` escalation `agt-a46033`, slot 12, `deployment-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — 2nd dispatch of the SAME escalation, re-verified from scratch, still no code action warranted, split
  this doc per the parent's mandate**: re-confirmed the diagnosis from scratch (independent of the parent doc's own
  entry for this exact escalation ID, found only after investigating): main push run `30813934094` (started `12:31:37Z`,
  right after PR#677 merged `e7d17f2`/`ce1239d`) failed `tests` slice on
  `TestApiFootballLauncherHardenedPreemptionSignal::test_launcher_writes_launch_params_with_replayable_scope`,
  `Failed: Timeout (>300.0s)`, 2866 passed/17 skipped, 29m45s runtime — the exact class + the exact already-raised
  ceiling (`deployment-service@eb131cd`, `PYTEST_TIMEOUT=300`, confirmed still intact and unchanged on
  `live-defi- rollout` HEAD `87d9d17`). Cross-referenced 5 prior LDR failures the same day (07-29 through 03:07-10:56Z)
  at the PRE-raise `150.0s` ceiling — confirmed the failing test is NOT specific to the api-football launcher: different
  runs hit timeouts on `test_log_service.py`, `test_manifest_reader_column_projection.py`,
  `test_backends_vm_services.py` — a random subset each time, proving host contention (not a launcher-specific hang)
  exactly as the parent doc's diagnosis pattern establishes. `gh api .../actions/runners` confirms exactly ONE online
  runner for this repo (`glue-ip-172-31-5-118-1`, `busy=true`), which is why the LDR re-verify run (`30825597344`,
  dispatched by the PRIOR pass of this same escalation) sat `queued` behind `main`'s run rather than running
  concurrently — the single-runner-per-repo structural bottleneck todo 1 above tracks. Checked for a redundant
  runner-hogging job to cancel (this bug class's one sanctioned non-pure-wait mitigation) — found none this time (only
  the two legitimate in-flight runs). Did NOT raise `PYTEST_TIMEOUT` a third time, consistent with the parent doc's
  `execution-service` precedent (`agt-e718ef`) and this doc's own todo 1: a repo already at the sanctioned 300s ceiling
  timing out under contention is the capacity-side case, not a per-repo-timeout case. **Disposition: no code or workflow
  change made or needed this pass** — both confirmatory runs (`30824452052` main, `30825597344` LDR) were still
  genuinely progressing at investigation end (main `tests` slice ~17min into its run, LDR still queued behind it); did
  not cancel/redispatch (would lose real elapsed queue position for zero benefit). `GET /api/repo-blockers` → checked,
  `open: []`. Split this doc per the parent's explicit mandate (937/1000 lines) rather than appending. Slot left clean
  (`deployment-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this
  doc's own commit; no branch changes in either repo). `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real numbered
  slot) — per `cicd.md`, skipped the authoring-slot ping. Outcome of `30824452052`/`30825597344` left for the NEXT
  occurrence, per this bug class's established practice — flagging in todo 2 above that this is now the THIRD repo to
  show wasteful un-cooldowned re-dispatch for the identical unresolved-but-progressing state, which the operator should
  address at the escalation-dispatch level rather than each pass re-diagnosing the same wait.

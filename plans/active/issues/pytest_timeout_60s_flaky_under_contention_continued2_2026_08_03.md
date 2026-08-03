---
doc_type: issue
title:
  "pytest-timeout-under-contention bug class continues (2nd split — parent hit its 1000-line hard cap) — two concurrent
  cicd sessions (deployment-service agt-a46033, features-service agt-c6ccfb) independently split the same parent within
  minutes of each other; merged here"
summary: >-
  Continuation of `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` (937-938/1000
  lines at split time, its own last entry explicitly stating "the NEXT occurrence for ANY repo MUST split rather than
  append"). Two `cicd` escalations landed on this split within minutes of each other and are merged into this single doc
  rather than left as a duplicate pair: (1) `agt-a46033` (`WALL_TYPE=main_ci_red`, `REPO=deployment-service`,
  `pr_number=0`, slot 12) — a re-dispatch of an escalation already handled once in the parent doc (~13:04-14:50Z entry);
  re-confirmed no code gap, both confirmatory runs (`30824452052` main, `30825597344` LDR) still genuinely
  progressing/queued behind the repo's sole self-hosted runner. (2) `agt-c6ccfb` (`WALL_TYPE=main_ci_red`,
  `REPO=features-service`, slot 7) — the ~15th same-day re-fire for this repo; confirmed `main`'s failing run had
  changed since the parent doc's cited runs (a fresh direct-`main` dispatch, run `30825589070`, failed the same
  established scheduler-starvation signature on a new random hang site,
  `test_trendline.py::test_convergence_acceleration_column`); LDR's own true current head (`87942ac0`) had no run
  in-flight, so dispatched a fresh one (`30829019397`). Both sessions independently confirm: all sanctioned per-repo
  timeout mitigations remain intact, the single shared self-hosted `glue-ip-172-31-5-118-1` runner is the structural
  bottleneck (confirmed `busy=true` fleet-wide across every repo spot-checked), and the root-cause fix remains correctly
  out of scope for a one-shot wall-clearing task
  (`/plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`, `status: active`, Phase 2-3 open). Both
  sessions independently flag the SAME operator-level gap: `main_ci_red`/`ldr_qg_failure` escalations for an unchanged
  underlying state are re-firing with no cooldown/dedup guard (now a 3rd+ repo showing this waste pattern, on top of the
  9+ already logged for `features-service` alone in the parent doc).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-api,
    features-service,
    market-data-processing-service,
    deployment-service,
    instruments-service,
    ml-service,
    alerting-service,
    execution-service,
    market-tick-data-service,
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
last_updated: 2026-08-03T16:35Z
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "cicd-role escalations agt-a46033 (WALL_TYPE=main_ci_red, REPO=deployment-service, slot 12, 2nd re-dispatch) +
  agt-c6ccfb (WALL_TYPE=main_ci_red, REPO=features-service, slot 7) — merged, concurrent splits of the same parent doc"
context_scope:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md,
    /plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
    deployment-service/scripts/quality-gates.sh,
    features-service/scripts/quality-gates.sh,
  ]
---

# pytest-timeout-under-contention: 2nd split (parent at hard cap) — two concurrent occurrences merged

Parent doc `/plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` closed out at its
1000-line hard cap (937-938 lines) with its final entry explicitly stating "the NEXT occurrence for ANY repo MUST split
rather than append." Two independent `cicd` sessions split it within minutes of each other (a genuine concurrent-write
race, not a duplicate filing) — merged into this single doc rather than kept as two competing files. Read the parent
(and its own parent, `pytest_timeout_60s_flaky_under_contention_2026_07_29.md`) for the full bug-class history; not
repeated here.

## Todos

- [ ] 1. [INFRA] P3. Root-cause fix is capacity-side, not another per-repo timeout raise — track landing of
      `/plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phase 2-3 (the single `glue` runner per
      repo is the structural bottleneck: both `deployment-service` and `features-service` confirmed to have exactly ONE
      online runner, `glue-ip-172-31-5-118-1`, serialising `main`+LDR verification runs). Once landed, re-test whether
      the `main_ci_red`/`ldr_qg_failure` re-fires in this doc-chain stop recurring.
- [ ] 2. [OPERATOR] P2. **Corroborating data point for the parent doc's todo 3** (un-cooldowned escalation re-fire), now
      observed across at least THREE repos: `deployment-service` (`agt-a46033`, 2 dispatches for the same state),
      `execution-service` (`agt-956fe9`/`agt-bd0d27`/`agt-e718ef`, 3 re-fires, logged in the parent doc), and
      `features-service` (~15 re-fires, logged across the parent doc and this one). No cooldown/state-transition dedup
      guard exists on the `main_ci_red`/`ldr_qg_failure` escalation trigger — recommend gating re-fire on either (a) a
      minimum cooldown since the last dispatch for the same repo with an unchanged target-branch HEAD, or (b)
      suppressing re-dispatch while `ldr-to-main-promote-fleet`'s own GATE BLOCK reason is unchanged from the prior
      escalation's, per `/codex/04-architecture/agent-orchestrator-alerting.md`'s dedup-by-state-transition principle
      (fire on change/RESOLVED, never every tick while nothing changed). Operator decision, not something a one-shot
      wall-clearing session should self-implement.
- [ ] 3. [INFRA] P3. Once `/plans/active/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phases 2-3 land,
      re-check whether this entire doc-chain (3 docs, ~30+ occurrences across 7+ repos) self-resolves — if the ledger
      coordination fix genuinely closes the class, archive all three docs together rather than leaving them open
      indefinitely as "still waiting."

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

- **2026-08-03 ~15:35-15:50Z (`cicd` escalation `agt-c6ccfb`, slot 7, `features-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — ~15th escalation for this repo's wall, no new code gap, one forward-progress action taken**: read
  `main`'s current failing run directly rather than assuming the stale cached run from the parent doc's entries still
  applied — it had genuinely changed: run `30825589070` (created 15:02:36Z, a fresh direct-`main` dispatch from an
  earlier session per the `ml-service`-established "only main can speak for main" pattern) had superseded the long-stale
  `30780455914` (02:55Z) the parent doc's entries all cited. This new run failed via the same established signature:
  `tests` slice hung inside `test_trendline.py::test_convergence_acceleration_column` (`_add_lagged_features`→pandas
  `Series.name` setter→`validate_all_hashable`) for ~4.3min before timing out — a DIFFERENT random hang site than every
  previously-logged occurrence (no test-content overlap), matching the established scheduler-starvation signature, not a
  per-test defect. `main` itself lacks the `PYTEST_TIMEOUT=300` mitigation (it hasn't been promoted since
  2026-08-02T13:01Z, 28+ commits behind LDR), so a direct main-dispatch is, if anything, MORE likely to hit this shape
  than an LDR run — consistent with what was observed.

  Checked LDR: confirmed all three sanctioned mitigations (`PYTEST_TIMEOUT=300`, `PYRIGHT_TIMEOUT=300`,
  `FORMULA_DRIFT_TIMEOUT=240`) intact and unchanged in `scripts/quality-gates.sh` — no regression. LDR HEAD had moved
  twice since the parent doc's last features-service entry (`8265205c`→`63e97f6a`→`87942ac0`, none touching test-timeout
  config or `delta_one`/typecheck-relevant paths per `git log --oneline`). The only queued run (`30825603740`,
  dispatched by an earlier session) targeted a 3-commits-stale head (`fa18180b`) and had been stuck `status=queued` for
  40+ minutes with no run in-flight against the true current head — unlike most parent-doc entries (which withhold a
  fresh dispatch to avoid discarding an in-flight run's elapsed contention-survival progress), this was a genuine "no
  one has tested the current head" case. Dispatched
  `gh workflow run quality-gates-v2.yml --repo IggyIkenna/features-service --ref live-defi-rollout` → run `30829019397`,
  confirmed queued against the true current head `87942ac0` within seconds (the previously-stuck `30825603740` also
  happened to claim the runner and start `in_progress` at the same moment — coincidental, not caused by this dispatch).
  Confirmed via 6-repo spot-check (`features-service`, `strategy-service`, `market-tick-data-service`,
  `market-data-processing-service`, `instruments-service`, `execution-service`) that all report the identical single
  self-hosted runner name/IP (`glue-ip-172-31-5-118-1`) `status=online busy=true` simultaneously — reconfirms this is
  genuinely fleet-wide, not features-service-specific. `GET /api/repo-blockers` → `open: []`.
  `ldr-to-main-promote-fleet`'s latest tick (`30828957778`, 15:45:08Z) unchanged:
  `GATE BLOCK features-service: ci_status=FAILING (cached='FAILING', live='FAILING')` — will auto-promote the instant
  either in-flight LDR run (`30825603740` or `30829019397`) reports green; no manual promotion action needed or taken.

  **Disposition: no code or workflow change made or needed** — every candidate fix already exists on
  `live-defi-rollout`; the remaining wall is pure runner-queue-depth wait, identical in kind to ~14 prior same-repo
  entries in the parent doc-chain. `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real numbered slot) — per `cicd.md`,
  skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left clean
  (`features-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this doc).
  This entry and the `agt-a46033` entry above were independently written as concurrent splits of the same at-cap parent
  doc within minutes of each other and have been merged here (not left as two competing files). Todo 2 (operator-flagged
  dedup/cooldown gap) remains open and unaddressed by this entry — now ~15 same-day fires for `features-service` alone,
  plus corroborating counts for `deployment-service`/`execution-service`.

- **2026-08-03 ~15:56Z (`cicd` escalation `agt-5b13b5`, slot 8, `alerting-service`, `wall_type=ldr_qg_failure`,
  `pr_number=0`) — a 4th repo added to the corroboration list, no code gap, one supporting data point on the
  same-tree-different-outcome signature**: escalation cited run `30808107879` (started `11:05:12Z`, commit `21bd8bc0`)
  which failed the `tests` slice on two unrelated, independently-mocked tests —
  `test_router_deployment_enrichment.py::TestDataPipelineDeepLinks::test_empty_base_url_omits_links` and
  `test_incident_persister.py::TestPersistActionEvent::test_upload_called_once` — both
  `Failed: Timeout (>150.0s) from pytest-timeout`, 2 failed/908 passed/972.22s actual pytest runtime. Read both test
  files + the code paths they exercise
  (`alerting_service/notifiers/router.py::route_event`/`_mirror_to_data_pipeline_slack`,
  `alerting_service/gateway/incident_persister.py::IncidentPersister`): every external sink (`AlertingSystemConfig`,
  `send_data_pipeline_alert`, `get_paging_credentials`, `_persist_*`, `send_uts_live_alert`) is patched in the router
  test, and the persister test injects a `MagicMock` `storage_client` directly — no un-mocked network/GCS call on either
  path. Specifically checked for the `_get_cloud_config` lru_cache-poisoning bug class documented elsewhere in this
  repo's own history: `tests/conftest.py` already carries an autouse `_clear_notifier_config_caches` fixture that
  cache-clears `router`/`pagerduty`/`slack`/`storage_store`'s `_get_cloud_config` before every test — ruled out. Two
  unrelated tests timing out at exactly the shared 150s ceiling, on properly-mocked code, is the established
  scheduler-starvation signature, not a per-test defect. Confirmed `gh api .../actions/runners`: `alerting-service` has
  exactly ONE online runner, `glue-ip-172-31-5-118-1` (same name/IP as every other repo in this doc-chain), `busy=true`
  — the fleet-wide single-runner bottleneck, not repo-specific. **Direct corroborating evidence for the
  same-tree-different-outcome signature**: a `main`-branch `quality-gates-v2` run (`30813349842`, `workflow_dispatch`,
  started `12:23:01Z`, overlapping the failing LDR run's own `12:14-12:58Z` window) completed `success` on
  content-equivalent code — same test suite, same approximate wall-clock window, opposite outcome, purely a function of
  which runner-contention lottery each run drew. `ldr-to-main-promote-fleet`'s latest tick (`30828957778`, `15:45:08Z`)
  already reads `alerting-service` `ci_status cached='MAIN_GREEN' live='MAIN_GREEN'`,
  `SKIP: main tree == LDR tree (content-identical)` — the promotion gate is UNAFFECTED by the earlier LDR-run failure (a
  later `main` success already overwrote the Firestore `ci_status` projection).
  `alerting-service/scripts/quality-gates.sh` carries no `PYTEST_TIMEOUT` override (stays at `base-service.sh`'s shared
  150s default) and pins `PYTEST_WORKERS=2` (fixed, not `auto`) — consistent with, not a cause of, the contention
  signature. Per this doc-chain's established practice (todo 1: root-cause is capacity-side, another per-repo timeout
  raise is discouraged), did NOT bump `PYTEST_TIMEOUT` for this repo. A fresh re-verify run (`30816220716`, dispatched
  by an earlier pass before this escalation) was still genuinely `in_progress` at investigation end —
  `QG slice (checks)` alone took `44m26s` (itself evidence of the same runner contention outside the `tests` slice), and
  the `tests` slice's own `Run quality gates (leg tests)` step had been running ~51min with no completion — did not
  cancel/redispatch (would lose real elapsed queue survival for zero benefit, per this doc-chain's established
  precedent). `GET /api/repo-blockers` → `open: []`; no redundant runner-hogging job found to cancel. **Disposition: no
  code or workflow change made or needed** — outcome of `30816220716` left for the next occurrence, consistent with
  practice. `AUTHORING_SLOT=ldr-ci-monitor` (a workflow-dispatch sentinel, not a real numbered slot per `cicd.md`'s
  `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left
  clean (`alerting-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this
  doc's own commit; no branch changes in either repo). Now a 4th repo (`alerting-service`, alongside
  `deployment-service`/`features-service`/ `execution-service`) showing this identical bug-class signature.

- **2026-08-03 ~15:20-16:00Z (`cicd` escalation `agt-3fb529`, slot 4, `deployment-service`, `wall_type=ldr_qg_failure`,
  `pr_number=676`) — 3rd occurrence for this exact repo, same already-diagnosed test, no new code gap**: escalation
  cited run `30812894587` (`promote/deployment-service/84bd8a0ea0e0`, created `12:16:14Z`) failing `tests` slice on the
  identical already-mitigated test —
  `TestApiFootballLauncherHardenedPreemptionSignal::test_launcher_writes_launch_params_with_replayable_scope`,
  `Failed: Timeout (>300.0s)` — same class + same already-raised `PYTEST_TIMEOUT=300` ceiling
  (`deployment-service@eb131cd`, confirmed still intact and unchanged on `live-defi-rollout` HEAD `bd47dd8`) that
  `agt-771546`/`agt-a46033` already diagnosed twice above. Reproduced the exact failing test in isolation first:
  **17.2s, passed clean, zero timeout** — decisive confirmation of no code/test defect. PR #676 had **already
  self-merged** (`mergedAt: 2026-08-03T12:16:15Z`, 1s after creation — the same
  self-merge-before-confirmatory-check-completes pattern this doc-chain documents repeatedly) —
  `gh pr list --state open` for `deployment-service` → 0 open PRs, confirms nothing is actually blocked; the failing run
  is a moot post-merge artifact. Did NOT raise `PYTEST_TIMEOUT` a third time (todo 1: capacity-side root cause,
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` still `status: active` / Phase 2-3 open — re-confirmed
  unchanged). Current LDR HEAD (`bd47dd8`) had NO run in-flight (the only queued run, `30825597344`, targeted a
  2-commits-stale head, `e72fe30`) — dispatched
  `gh workflow run quality-gates-v2.yml --repo IggyIkenna/deployment-service --ref live-defi-rollout` → run
  `30830046052`, confirmed queued against the true current head within seconds. `GET /api/repo-blockers` → `open: []`.
  **Disposition: no code or workflow change made or needed** — promotion already complete, fix already correctly shipped
  and intact, remaining wall is pure runner-queue-depth/host-contention wait; outcome of `30830046052` left for a
  follow-up occurrence per this doc-chain's established practice. `AUTHORING_SLOT=ci` is not a real numbered slot (fails
  cicd.md's `^[0-9]+$` check) — skipped the authoring-slot ping per the same carve-out as the `ci-reconcile`/
  `ldr-ci-monitor` sentinels above. Slot left clean (`deployment-service` and `unified-trading-pm` both on
  `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch changes in either repo). Now a
  3rd same-day escalation for this exact repo/test — corroborates todo 2's operator-flagged dedup/cooldown gap further.

- **2026-08-03 ~16:05-16:20Z (`cicd` escalation `agt-0a8231`, slot 13, `features-service`, `wall_type=ldr_qg_failure`,
  `pr_number=0`) — same signature confirmed independently, no new code gap, fresh dispatch for the true current head**:
  escalation cited run `30818407385` (created `13:32:16Z`, headSha `abff85a3`) failing the `tests` slice on
  `test_momentum.py::test_volume_momentum_columns_present` — read the full failed-job log directly rather than trusting
  the cached diagnosis: captured stderr shows `_calculate_features`/`_enrich_features` completed normally at `14:04:29`
  (`Added 147 time-since event features`, `Added 882 event-horizon binary features` — 147×6 horizons matches UTL's
  current `EVENT_HORIZONS` default `[1,3,5,10,20,50]` exactly, not an inflated horizon count), then hung inside
  `_add_lagged_features`'s single `pd.concat` call for ~7m57s before `pytest-timeout` dumped + killed at `14:12:26`.
  Independently re-derived why this is NOT an algorithmic hang before accepting the doc-chain's conclusion: read
  `_select_lag_candidates` (`features_service/delta_one/app/calculators/base.py:416-423`) — it dtype-filters to
  `float64/float32/int64/int32/float/int`, which excludes the 882 just-added horizon-binary columns (stored `int8` via
  `.astype(np.int8)` at `base.py:409`) from the lag pass entirely, so the final concat is bounded (~1176 existing cols +
  ~441 freshly-lagged Series for a 50-row frame) — genuinely trivial at this scale, consistent with the parent commit's
  own local-repro claim (`c092df50`: "338s, zero timeouts" at this exact code path). Confirmed all three sanctioned
  mitigations intact + unchanged on current HEAD (`0f894013`): `PYTEST_TIMEOUT=300`, `PYRIGHT_TIMEOUT=300`
  (`features-service/scripts/quality-gates.sh:40-41`). Confirmed `gh api .../actions/runners`: `features-service` has
  exactly ONE online runner, `glue-ip-172-31-5-118-1`, `busy=true` — the same fleet-wide single-runner bottleneck this
  doc-chain has now confirmed across 5 repos. `GET /api/repo-blockers` → `open: []`. The only run testing near-current
  HEAD was `30829019397` (`queued`, headSha `87942ac0` — one commit behind true HEAD `0f894013`, and that one commit,
  `test(multi_timeframe): port subprocess --help exit-code regression test`, is test-only/inert w.r.t. this failure) —
  left it queued rather than cancel/redispatch (would lose ~20min of accumulated queue position for zero benefit, per
  this doc-chain's established practice); did NOT dispatch an additional redundant run since one already targets a
  content-equivalent tree. Did NOT raise `PYTEST_TIMEOUT` a third time (todo 1: capacity-side root cause,
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` still `status: active`, Phase 2-3 open — re-confirmed
  unchanged). **Disposition: no code or workflow change made or needed** — every sanctioned mitigation already exists on
  `live-defi-rollout`, the remaining wall is pure runner-queue-depth/host-contention wait; outcome of `30829019397` left
  for a follow-up occurrence per established practice. `AUTHORING_SLOT=ldr-ci-monitor` is a workflow-dispatch sentinel,
  not a real numbered slot (fails `cicd.md`'s `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time
  Slack alert already covers the FYI). Slot left clean (`features-service` and `unified-trading-pm` both on
  `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch changes in either repo). Now a
  5th repo's worth of same-day corroboration for the fleet-wide signature (`deployment-service` ×3, `features-service`
  ×2 in this doc alone (~17 total across the doc-chain), `alerting-service`, `execution-service`).

- **2026-08-03 ~15:31-16:05Z (`cicd` escalation `agt-72552a`, slot 11, `market-tick-data-service`,
  `wall_type=main_ci_red`, `pr_number=0`) — 6th repo added to the corroboration list; checked this repo's own base rate
  before concluding "same signature, no action" and confirmed it does NOT meet the sustained-red mitigation bar**:
  `main` HEAD at dispatch time (`efcd8980`) had failed `quality-gates-v2` on 2026-08-02 via
  `❌ Type check FAILED/timeout (exit=124)` (checks leg, `[4/6] TYPE CHECK` step) — a `timeout`-wrapped basedpyright
  invocation blowing its wall-clock ceiling under host contention, not a real type error (workflow-yaml/actionlint/ruff
  steps immediately before it all passed clean in seconds). By investigation time LDR had already advanced and
  auto-promoted forward (PR #816, `mergedAt=2026-08-03T06:38:55Z`, the same
  self-merge-before-confirmatory-check-completes pattern this doc-chain documents repeatedly) to new `main` HEAD
  `ef78e52b`, whose own `quality-gates-v2` run (`30790885949`) was already `in_progress` with its `checks` leg PASSED
  (no repeat of the typecheck timeout) — watched it to completion via a bounded background poll (180s interval, ~35min)
  rather than re-dispatching. Outcome: the run was `cancelled`, NOT failed — a yet-newer LDR→main promotion landed mid-
  watch (main HEAD advanced again to `17502351`), and the branch-scoped concurrency group correctly superseded the stale
  run with a fresh one (`30830062679`, confirmed `queued` against the true current head) — pure forward-progress churn,
  not a stall. Before accepting "same bug class, no action" by default, pulled this repo's own last 40 LDR
  `quality-gates-v2` runs: 18 success / 8 failure / 13 cancelled, most recent success `2026-08-02T12:24:14Z` — a healthy
  self-clearing ratio, NOT the "100% failure, no green for 13.5-36h+" bar that justified the repo-local
  `PYTEST_TIMEOUT`/`PYRIGHT_TIMEOUT` mitigation on `unified-trading-api`/`features-service`/`deployment-service`/
  `execution-service` elsewhere in this doc-chain (mirrors the `instruments-service` precedent above, which similarly
  found only 2/25 genuine failures and correctly withheld the mitigation). Confirmed `scripts/quality-gates.sh` here
  carries no `PYTEST_TIMEOUT`/`PYRIGHT_TIMEOUT` override — deliberately NOT adding one, per that precedent.
  `GET /api/repo-blockers` → `open: []`. **Disposition: no code or workflow change made or needed** — every candidate
  fix already exists on `live-defi-rollout`, the newly-queued run (`30830062679`) is the correct in-flight state to
  leave this for the next occurrence, and this repo's base rate argues against pre-emptively adding a timeout override
  it doesn't yet need. `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real numbered slot) — per `cicd.md`, skipped the
  authoring-slot ping. Slot left clean (`market-tick-data-service` and `unified-trading-pm` both on `live-defi-rollout`,
  0 commits ahead of origin beyond this doc's own commit; no branch changes in either repo). Added
  `market-tick-data-service` to this doc's `repos:` frontmatter (1st occurrence for this repo in the doc-chain).

- **2026-08-03 ~15:48-16:30Z (`cicd` escalation `agt-d12ed0`, slot 3, `instruments-service`, `wall_type=ldr_qg_failure`,
  `pr_number=0`) — this repo's own first full write-up in this doc (previously cited only by reference, in the
  `market-tick-data-service` entry above, as an earlier low-base-rate precedent), no code gap, two-run comparison
  confirms the same-tree-different-outcome signature**: reproduced locally first per the wall brief — backgrounded
  `bash scripts/quality-gates.sh` on current LDR HEAD (`2f46deecbc49`) came back
  **`✅ ALL QUALITY GATES PASSED (234s)`**, tests phase `5179 passed, 6 skipped, 10 warnings in 80.36s`. Cross-checked
  live CI: most recent completed-failure run `30816252648` (`live-defi-rollout`, `workflow_dispatch`, started
  `13:04:24Z`) failed the `tests` slice via an xdist worker crash —
  `AssertionError: ('tests/unit/test_sports_adapters_boost.py::TestFootystatsGetTeamsEdgeCases:: test_canonical_team_exception_continues', <WorkerController gw1>)`,
  underlying cause `Failed: Timeout (>150.0s) from pytest-timeout` —
  `1 failed, 4300 passed, 6 skipped, 5 warnings in 1022.14s`. Read the test + the code it exercises
  (`FootystatsAdapter.get_teams`, fully mocked `_make_session`/`_get_with_retry`/ `_extract_data`/`CanonicalTeam`, no
  un-mocked I/O) and ran it in isolation: `1 passed, 1 warning in 0.93s` — decisive, zero hang in the test's own logic.
  A second, older completed-failure run (`30774745528`, started `00:33:18Z`) crashed with
  `RuntimeError: Unexpectedly no active workers available` after only `1270 passed` in `3571.90s` (0:59:31) — no single
  test named (all xdist workers died), a different random failure shape entirely — the same same-tree-different-outcome
  / random-hang-site signature this doc-chain's diagnosis pattern establishes, not a per-test defect. Confirmed
  `gh api .../actions/runners`: `instruments-service` has exactly ONE online runner, `glue-ip-172-31-5-118-1` (identical
  name/IP to every other repo in this doc-chain), `busy=true` — the fleet-wide single-runner bottleneck, not
  repo-specific. **Direct same-tree-different-outcome corroboration**: a THIRD run against the same LDR HEAD, still
  `in_progress` at investigation end (`30823202578`, `workflow_dispatch`, started `14:32:44Z`) — its `tests` slice this
  time **succeeded**, but took `14:33:12Z→15:58:20Z` (~85 minutes wall-clock vs. the local 80-second run), itself hard
  evidence of severe scheduler contention rather than any code/test defect; `checks` slice began `15:59:29Z` and was
  still running at investigation end. `instruments-service/scripts/quality-gates.sh` carries no `PYTEST_TIMEOUT`
  override (stays at the shared 150s default) and pins `PYTEST_WORKERS=2` — consistent with, not a cause of, the
  contention signature; per this doc-chain's established practice (todo 1: root-cause is capacity-side,
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` still `status: active` / Phase 2-3 open, re-confirmed
  unchanged), did NOT bump `PYTEST_TIMEOUT` for this repo. `GET /api/repo-blockers` → `open: []`; no redundant
  runner-hogging job found to cancel. Did NOT cancel/redispatch the in-flight `30823202578` (would lose its real elapsed
  queue-survival progress — its `tests` slice had already cleared the hardest part — for zero benefit), per this
  doc-chain's established precedent. **Disposition: no code or workflow change made or needed** — outcome of
  `30823202578` left for the next occurrence, consistent with practice. `AUTHORING_SLOT=ci-reconcile` (sentinel, not a
  real numbered slot per `cicd.md`'s `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time Slack alert
  already covers the FYI). Slot left clean (`instruments-service` and `unified-trading-pm` both on `live-defi-rollout`,
  0 commits ahead of origin beyond this doc's own commit; no branch changes in either repo). Another repo
  (`instruments-service`, alongside `deployment-service`/`features-service`/`execution-service`/`alerting-service`/
  `market-tick-data-service`) showing this identical bug-class signature.

- **2026-08-03 ~16:00-16:20Z (`cicd` escalation `agt-2482ca`, slot 7, `features-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — ~16th same-day fire for this repo, re-confirms `agt-c6ccfb`'s disposition + adds one new clarifying
  detail on the `checks` leg**: re-verified from scratch rather than trusting the cached diagnosis. `main` run
  `30825589070` (the same run `agt-c6ccfb` already read) — confirmed BOTH slices failed, not just `tests`: the `checks`
  leg's actual failing selector is `typecheck` (`##[error]QG selector 'typecheck' FAILED (leg=checks, exit=1)`, preceded
  by `❌ Type check FAILED/timeout (exit=124)` after a ~121s hang in the `[4/6] TYPE CHECK` section) — i.e. the **same
  exit-124 wall-clock-timeout signature as the `tests` leg**, not a distinct bug. Flagging this because the run's log is
  easy to misread: the peripheral-consumer basedpyright scan over `e2e-testing/scripts/{delta_one, commodity,...}/` that
  runs later in the same job prints 96+ genuine `reportAny` errors against
  `e2e-testing/scripts/features/snapshot_instrument_universe.py` and several `smoke_matrix.py` files — but every one of
  those is wrapped in `run_timeout 120 basedpyright ... || log_warn "..."` (`features-service/scripts/quality-gates.sh`
  ~L145), i.e. WARN not FAIL by design (catches cross-repo import-rot without gating on a sibling repo's own type
  hygiene) — confirmed this is not new/blocking by checking `e2e-testing`'s own `quality-gates-v2` (green, 5 most recent
  runs all `success`) and by confirming the primary `features_service`-source typecheck itself reported
  `✅ STEP 5.21/5.22` clean in this exact run. 121s is consistent with `main` still lacking the `PYRIGHT_TIMEOUT=300`
  raise (`c092df50`, LDR-only, unpromoted — same 28+-commits-behind gap `agt-c6ccfb` already diagnosed for the `tests`
  leg's missing `PYTEST_TIMEOUT=300`). Re-confirmed promotion state unchanged: `ldr-to-main-promote-fleet` still emits
  `GATE BLOCK features-service: ci_status=FAILING` every ~15min tick; single runner `glue-ip-172-31-5-118-1`
  `status=online busy=true`; the LDR re-verify run `agt-c6ccfb` dispatched (`30829019397`) was still genuinely
  progressing (`checks` leg `in_progress`, `tests` leg `queued` behind it) at investigation end — did not cancel or
  redispatch. **Disposition: no code or workflow change made or needed** — this pass's only incremental value is
  confirming the `checks` leg is the identical timeout class (not a second bug) and ruling out the loud-but-non-blocking
  peripheral warn as a distraction for the next reader. This is now corroboration #4 for todo 2 (features-service alone
  is ~16 same-state re-fires) — no dedup/cooldown guard exists yet on `main_ci_red` re-dispatch for an unchanged
  in-flight state. `GET /api/repo-blockers` → `open: []`. `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real numbered
  slot) — per `cicd.md`, skipped the authoring-slot ping. Slot left clean (`features-service` and `unified-trading-pm`
  both on `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch changes in either
  repo).

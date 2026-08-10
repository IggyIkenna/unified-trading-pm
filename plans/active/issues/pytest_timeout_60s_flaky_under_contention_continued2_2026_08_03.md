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
  (`/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`, `status: active`, Phase 2-3
  open). Both sessions independently flag the SAME operator-level gap: `main_ci_red`/`ldr_qg_failure` escalations for an
  unchanged underlying state are re-firing with no cooldown/dedup guard (now a 3rd+ repo showing this waste pattern, on
  top of the 9+ already logged for `features-service` alone in the parent doc).
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    unified-trading-api,
    unified-api-contracts,
    features-service,
    market-data-processing-service,
    deployment-service,
    instruments-service,
    ml-service,
    alerting-service,
    execution-service,
    market-tick-data-service,
    batch-live-reconciliation-service,
    agent-orchestrator,
  ]
scope: [engineer, admin]
tags: [quality-gates, flaky-gate, timeout, pytest-timeout, ci, shared-host-contention, xdist, escalation-refire-waste]
related:
  [
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
  ]
created: 2026-08-03
author: unknown
last_updated: 2026-08-03T22:50Z
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
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued3_2026_08_03.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md,
    /plans/active/issues/pytest_timeout_60s_flaky_under_contention_2026_07_29.md,
    /plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
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
      `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phase 2-3 (the single `glue`
      runner per repo is the structural bottleneck: both `deployment-service` and `features-service` confirmed to have
      exactly ONE online runner, `glue-ip-172-31-5-118-1`, serialising `main`+LDR verification runs). Once landed,
      re-test whether the `main_ci_red`/`ldr_qg_failure` re-fires in this doc-chain stop recurring.
- [x] ✅ 2. [SCRIPT] P2. **RULED 2026-08-06: option (a) cooldown, same as parent doc todo 3 — not duplicated here.**
      **Corroborating data point for the parent doc's todo 3** (un-cooldowned escalation re-fire), now observed across
      at least THREE repos: `deployment-service` (`agt-a46033`, 2 dispatches for the same state), `execution-service`
      (`agt-956fe9`/`agt-bd0d27`/`agt-e718ef`, 3 re-fires, logged in the parent doc), and `features-service` (~15
      re-fires, logged across the parent doc and this one). No cooldown/state-transition dedup guard exists on the
      `main_ci_red`/`ldr_qg_failure` escalation trigger — recommend gating re-fire on either (a) a minimum cooldown
      since the last dispatch for the same repo with an unchanged target-branch HEAD, or (b) suppressing re-dispatch
      while `ldr-to-main-promote-fleet`'s own GATE BLOCK reason is unchanged from the prior escalation's, per
      `/codex/04-architecture/agent-orchestrator-alerting.md`'s dedup-by-state-transition principle (fire on
      change/RESOLVED, never every tick while nothing changed). Operator decision, not something a one-shot
      wall-clearing session should self-implement. — **DONE 2026-08-08, `a351d0d`** — same fix as parent doc todo 3.
- [ ] 3. [INFRA] P3. Once `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phases 2-3
      land, re-check whether this entire doc-chain (3 docs, ~30+ occurrences across 7+ repos) self-resolves — if the
      ledger coordination fix genuinely closes the class, archive all three docs together rather than leaving them open
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

- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — added the grandparent issue doc
  (`pytest_timeout_60s_flaky_under_contention_2026_07_29.md`), which this doc's own body explicitly instructs readers to
  consult ("Read the parent (and its own parent, ...) for the full bug-class history; not repeated here") but which the
  prior context_scope omitted.
- **context-scout 2026-08-06**: restored the grandparent doc + added `continued3` (this doc's own successor since 08-04)
  -- both silently missing despite the 08-03 marker above. 5 entries.

- **2026-08-03 ~16:46-17:05Z (`cicd` escalation `agt-7bcb7c`, slot 12, `deployment-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — yet another same-day re-dispatch of this repo's identical wall (now the 4th deployment-service entry
  in this doc-chain alone: `agt-a46033` ×2, `agt-3fb529`, this one), re-confirms the disposition from scratch, no new
  code gap**: classified per the `main_ci_red` boot brief's A/B split first — checked `gh pr list --base main` (0 open
  PRs, rules out (A) promotion-stuck) and confirmed `main` HEAD (`ce1239d`, PR #677's merge commit) has no stale
  workflow-definition issue — the required check DID run and report, twice (`30813934094` push @12:31:37Z, `30824452052`
  workflow_dispatch @14:48:17Z), both genuinely FAILED the `tests` slice on `pytest-timeout`, ruling out (B)'s
  missing-check/stale-workflow shape too. Read both failing logs directly rather than trusting the cached parent-doc
  diagnosis: `30813934094` timed out on `test_launcher_writes_launch_params_with_replayable_scope` (already logged by
  `agt-a46033`'s first pass), but `30824452052` hit a **different, previously-unlogged-for-this-repo hang site**:
  `test_turbo_data_validation.py::TestDataTypeValidation::test_expected_instrument_types_cefi_deribit`,
  `Failed: Timeout (>300.0s)`, `1 failed, 2866 passed, 17 skipped, 8 warnings in 2312.15s (0:38:32)` — a third distinct
  random test for this repo's occurrence-set, reinforcing (not just repeating) the scheduler-starvation signature over a
  launcher-hang theory. Confirmed `PYTEST_TIMEOUT=300`/`PYRIGHT_TIMEOUT=300` still intact and unchanged on current LDR
  HEAD (`f55b16c`, itself 2 commits ahead of the `bd47dd8` cited by `agt-3fb529`) — did NOT raise a third time, per this
  doc-chain's established todo-1 practice. `gh api .../actions/runners`: exactly ONE online runner for this repo,
  `glue-ip-172-31-5-118-1`, confirmed `busy` at investigation time — same fleet-wide bottleneck. Checked
  `ldr-to-main-promote-fleet`'s freshest tick (`30833585017`, 16:45:56Z):
  `GATE BLOCK deployment-service: ci_status=FAILING (cached='FAILING', live='FAILING')` — auto-promotion is correctly
  withheld pending a genuine green LDR re-verify, not stuck on anything a human/agent needs to unblock. The only
  in-flight LDR run (`30833902590`, `queued`) targets headSha `3c5acfba` — 2 commits behind the true current HEAD
  `f55b16c`, but both intervening commits are VM-launcher/terraform-only and orthogonal to the failing test class, so
  left it queued rather than cancel+redispatch (would forfeit real elapsed queue position for negligible freshness
  gain), consistent with this doc-chain's established precedent. `GET /api/repo-blockers` → `open: []`; no redundant
  runner-hogging job found to cancel. **Disposition: no code or workflow change made or needed** — every sanctioned
  mitigation already exists on `live-defi-rollout`, remaining wall is pure runner-queue-depth/host-contention wait;
  outcome of `30833902590` left for the next occurrence per established practice. `AUTHORING_SLOT=ci-reconcile`
  (sentinel, not a real numbered slot per `cicd.md`'s `^[0-9]+$` check) — skipped the authoring-slot ping (dispatch-time
  Slack alert already covers the FYI). Slot left clean (`deployment-service` and `unified-trading-pm` both on
  `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch changes in either repo). This
  is now the **5th same-day escalation dispatch for this exact repo/wall** across the doc-chain (`agt-771546` implied by
  `agt-3fb529`'s reference, `agt-a46033` ×2, `agt-3fb529`, this one) — further corroborates todo 2's operator-flagged
  missing cooldown/dedup guard on `main_ci_red`/`ldr_qg_failure` re-dispatch for an unchanged in-flight state.

- **2026-08-03 ~16:50-17:10Z (`cicd` escalation `agt-e718ef`, slot 4, `execution-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — SAME escalation ID re-dispatched a 4th time (the parent doc's `agt-956fe9`→`agt-bd0d27`→`agt-e718ef`
  chain already covered 3 passes at ~15:05-15:35Z from slot 3; this is a fresh dispatch of the identical ID from slot 4,
  ~75min later), re-verified from scratch, still no code action warranted, two new corroborating failure signatures
  found**: classified per the `main_ci_red` boot brief's A/B split first — `gh pr list --base main` → 0 open PRs (rules
  out (A) promotion-stuck); `main` HEAD (`9ad9265f`) unchanged since the prior pass, still the pre-fix commit (279
  commits behind LDR at the time, now confirmed via `git log origin/main..origin/live-defi-rollout` — dozens of commits
  ahead including the already-landed `7803a634` `PYTEST_TIMEOUT=300` fix); `ldr-to-main-promote-fleet`'s freshest tick
  (`30834730331`, 17:00:03Z) confirms
  `GATE BLOCK execution-service: ci_status=FAILING (cached='SIT_VALIDATED', live='FAILING')` — auto-promotion correctly
  withheld pending a genuine LDR green, not stuck on anything actionable. Read the two most recent LDR runs directly
  rather than trusting the cached diagnosis: (1) `30822100465` (the same run the prior `agt-e718ef` pass had left
  `in_progress` — now `completed`/`failure`): `tests` slice this time crashed via the xdist
  `INTERNALERROR`/`RuntimeError: Unexpectedly no active workers available` shape (NOT a plain timeout) after
  `3306 passed, 4 skipped, 1 xfailed` in `1961.13s` — a pytest-timeout SIGALRM firing mid-flush of the xdist report
  channel killed the whole session on an otherwise-clean run, the same channel-corruption variant already logged for
  `instruments-service` above (2nd run, `30774745528`); `checks` slice on this same run ALSO failed independently via
  `❌ Type check FAILED/timeout (exit=124)` even with `PYRIGHT_TIMEOUT=300` in effect — both failures on the SAME
  commit, different random shapes, consistent with host contention not a code defect. (2) A fresh run dispatched by the
  fleet/watcher machinery since the prior pass, `30833908386` (started `16:49:22Z`, same HEAD `7803a634`): `checks` leg
  failed via the identical `[4/6] TYPE CHECK` → `❌ Type check FAILED/timeout (exit=124)` signature (`[4/6] TYPE CHECK`
  header at `16:51:18.526Z`, verdict at `16:56:18.937Z` — ~5min hang before the 300s-class ceiling fired, confirmed via
  the GHA-level `##[error]QG selector 'typecheck' FAILED (leg=checks, exit=1)` annotation, not a silent script bug —
  traced the job's raw log line-by-line to rule out a false read of the "✅ ALL QUALITY GATES PASSED (104s)" banner
  appearing to precede the failure: that banner belongs to the SAME loop's second selector, `lint-codex`, which ran and
  passed cleanly AFTER `typecheck` had already failed — `QG_SLICE=typecheck ── ... FAILED` at `16:56:22Z` precedes
  `QG_SLICE=lint-codex ── ... ALL QUALITY GATES PASSED` at `16:58:05Z` in the same job's log, an ordering easy to
  misread if only the tail of the log is inspected); the sibling `tests` leg of this same run was cancelled (superseded
  by a newer run, not a genuine failure). Confirmed both sanctioned mitigations still intact and unchanged on current
  LDR HEAD (`7803a634`): `PYTEST_TIMEOUT="${PYTEST_TIMEOUT:-300}"` (`scripts/quality-gates.sh:161`),
  `PYRIGHT_TIMEOUT="${PYRIGHT_TIMEOUT:-300}"` (`scripts/quality-gates.sh:153`) — did NOT raise either a further time,
  per this doc-chain's established todo-1 practice (re-confirmed
  `qg_governor_glue_runner_ledger_coordination_2026_08_03` still `status: active`, Phases 2-3 `[ ]` open, unchanged).
  `gh api .../actions/runners`: this repo actually has TWO online runners (`glue-ip-172-31-3-59-1`,
  `glue-ip-172-31-5-118-1`), both `busy=true` at investigation time — the first repo in this doc-chain observed with 2
  runners rather than the usual single-runner bottleneck, yet still showing the identical contention signature,
  reinforcing that the bottleneck is host-level (shared physical capacity/load), not simply runner-count-per-repo; host
  `uptime` load average **33.89, 28.55, 27.75** on this same shared host, consistent with (not worse than) the prior
  pass's 36.21/35.14/39.94 reading. `GET /api/repo-blockers` → `open: []`. A THIRD LDR run was already dispatched by the
  fleet/watcher machinery before this investigation concluded (`30835276766`, started `17:06:57Z`, same HEAD `7803a634`,
  `in_progress` at investigation end) — left it running rather than cancel/redispatch (would lose real elapsed queue/run
  position for zero benefit), consistent with this doc-chain's established practice. **Disposition: no code or workflow
  change made or needed** — every sanctioned mitigation already exists and is intact on `live-defi-rollout`; the
  remaining wall is pure runner-queue-depth/host- contention wait; outcome of `30835276766` left for the next
  occurrence. `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real numbered slot per `cicd.md`'s `^[0-9]+$` check) —
  skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left clean
  (`execution-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this doc's
  own commit; no branch changes in either repo). This is now the **4th same-day escalation dispatch for this exact
  repo/wall's identical escalation ID** (`agt-956fe9`→ `agt-bd0d27`→`agt-e718ef` ×2) — the SAME escalation ID re-firing
  (not just the same repo/wall) is new evidence for todo 2's operator-flagged missing cooldown/dedup guard: this is not
  merely "no state-transition dedup on the trigger" but the identical `escalation_id` being re-dispatched to a fresh
  slot without the prior pass's disposition ever being consulted by the dispatcher.

- **2026-08-03 ~17:35-17:45Z (`cicd` escalation `agt-3fb529`, slot 2, `deployment-service`, `wall_type=ldr_qg_failure`,
  `pr_number=676`) — SAME escalation ID re-dispatched a 2nd time (this doc's own `agt-3fb529` entry above,
  ~15:20-16:00Z, already fully diagnosed + closed this exact escalation), re-verified from scratch, disposition
  unchanged**: confirmed `gh pr list --state open` for `deployment-service` → still 0 open PRs; PR #676 still `MERGED`
  at `2026-08-03T12:16:15Z` — nothing is actually blocked. `GET /api/repo-blockers` → `open: []`. The follow-up run the
  prior pass dispatched (`30830046052`) is now `completed`/`cancelled` (NOT a genuine failure) — superseded by the
  branch-scoped concurrency group as newer commits kept landing on LDR, exactly the "same-tree-different-outcome" churn
  this doc-chain documents; same for the two runs after it (`30833902590`, `30816236026`, both `cancelled`). LDR HEAD
  has advanced twice since (`bd47dd8`→`28c8d5f`) and a fresh run (`30837367180`) is already `queued` against the true
  current head — did not cancel/redispatch (would forfeit queue position for zero benefit), per established practice.
  Confirmed `PYTEST_TIMEOUT=300`/`PYRIGHT_TIMEOUT` mitigations still intact and unchanged in `scripts/quality-gates.sh`.
  Did NOT raise `PYTEST_TIMEOUT` a third time (todo 1: capacity-side root cause,
  `qg_governor_glue_runner_ledger_coordination_ 2026_08_03.md` still `status: active`, Phase 2-3 open — re-confirmed
  unchanged). **Disposition: no code or workflow change made or needed** — identical to the prior pass's conclusion;
  this is now the **2nd same-day dispatch of this exact escalation ID**, another direct data point for todo 2's
  operator-flagged missing cooldown/dedup guard (the dispatcher re-fired the same ID without consulting the prior pass's
  already-recorded disposition). `AUTHORING_SLOT=ci` is not a real numbered slot (fails `cicd.md`'s `^[0-9]+$` check) —
  skipped the authoring-slot ping. Slot left clean (`deployment-service` and `unified-trading-pm` both on
  `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch changes in either repo).

- **2026-08-03 ~17:35-17:50Z (`cicd` escalation `agt-83db42`, slot 9, `ml-service`, `wall_type=ldr_qg_failure`,
  `pr_number=333`) — this repo's 2nd occurrence in the doc-chain (1st: `agt-2336b3`, `main_ci_red`,
  `pytest_timeout_60s_flaky_under_contention_continued_2026_08_02.md` ~11:15-11:38Z), first occurrence via the
  `typecheck`/basedpyright exit-124 signature rather than a pytest timeout, no code gap**: read the cited failing run
  (`30825406243`, `checks` job `91725696087`) directly — `qg-governor` queued the job `WAIT_CPU`/`WAIT_HOST_PRESSURE`
  for 1582s (`15:34:29Z`→`16:01:23Z`) before admission, then `[4/6] TYPE CHECK` ran `16:01:23Z`→`16:03:23Z` (~120s) and
  hit `❌ Type check FAILED/timeout (exit=124)` — the identical exit-124 wall-clock-timeout shape already established
  fleet-wide in this doc-chain (`features-service`, `market-tick-data-service`, `execution-service` above), just
  ml-service's first manifestation via `typecheck` instead of `tests`. Confirmed `ml-service/scripts/quality-gates.sh`
  carries NO `PYRIGHT_TIMEOUT`/`PYTEST_TIMEOUT` override — stays at `base-service.sh`'s shared defaults (120s pyright /
  150s pytest), the LOWEST ceiling of any repo in this doc-chain, consistent with (not a cause of) the contention
  signature. Confirmed `gh api .../actions/runners`: exactly ONE online runner, `glue-ip-172-31-5-118-1` (identical
  name/IP to every other repo in this doc-chain), `busy=true` — same fleet-wide bottleneck. Per this doc-chain's
  established practice (todo 1: capacity-side root cause; `alerting-service`/`market-tick-data-service`/
  `instruments-service` precedent of NOT bumping a still-at-default repo's timeout), did NOT add a
  `PYRIGHT_TIMEOUT`/`PYTEST_TIMEOUT` override for ml-service — a single non-sustained occurrence (2nd total, 1st of this
  specific sub-signature) does not meet the sustained-red bar that justified the one-time raises elsewhere. Separately
  noted: PR#333 (the promotion PR this escalation cited) had **already self-merged** (`mergedAt: 2026-08-03T15:00:22Z`,
  6s after `createdAt: 15:00:16Z` — the same self-merge-before-confirmatory-check-completes pattern this doc-chain
  documents repeatedly for `deployment-service`/`market-tick-data-service`) — `gh pr list --state open` for `ml-service`
  → 0 open PRs, confirms nothing is actually blocked. Checked current state rather than assuming the cited run still
  applies: both LDR's and `main`'s most recent COMPLETED `quality-gates-v2` runs are already `success` (LDR
  `30833929143` @`16:49:38Z`, `main` `30829050842` @`15:46:20Z`) — the gate had already self-cleared via a later
  re-verify before this investigation started. `GET /api/repo-blockers` → `open: []`. The only queued LDR run
  (`30837391154`) targeted headSha `1b3df5a2` — one commit behind true current HEAD `48843e56`
  (`chore(deps): re-pin unified-trading-library to 0.72.0`, a dep-pin bump, not inert but unrelated to the
  typecheck-timeout failure class) — dispatched a fresh run against the true current head
  (`gh workflow run quality-gates-v2.yml --repo IggyIkenna/ml-service --ref live-defi-rollout` → run `30838304919`,
  confirmed `queued` against `48843e56` within seconds) rather than relying solely on the one-behind run, per this
  doc-chain's established practice of preferring a true-current-head verification when the cost is low. **Disposition:
  no code or workflow change made or needed** — every sanctioned mitigation already exists at its correct (default)
  level, the cited failure was a one-off host-contention timeout that already self-cleared on a later run, and the
  promotion PR is not actually blocked (already merged); outcome of `30838304919` left for the next occurrence per
  established practice. `AUTHORING_SLOT=planning` is not a real numbered slot (fails `cicd.md`'s `^[0-9]+$` check) —
  skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left clean (`ml-service`
  and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no
  branch changes in either repo).

- **2026-08-03 ~17:50Z (`cicd` escalation `agt-684220`, slot 10, `deployment-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — 6th same-day dispatch for this exact repo/wall in this doc alone, unchanged state, no code action**:
  re-verified from scratch per the A/B classification: `gh pr list --base main` → 0 open PRs (rules out A,
  promotion-stuck). `main` HEAD (`ce1239d`) and its latest `quality-gates-v2` run (`30824452052`, workflow_dispatch
  14:48:17Z, failed `tests` on
  `test_turbo_data_validation.py::TestDataTypeValidation::test_expected_instrument_types_cefi_deribit`,
  `Failed: Timeout (>300.0s)`) are byte-identical to what `agt-7bcb7c` already diagnosed above — no newer main run
  exists, ruling out B too (the check DID run and report; not a stale-workflow/missing-check shape).
  `PYTEST_TIMEOUT=300` confirmed intact on LDR HEAD (`28c8d5f4`). `gh api .../actions/runners`: still exactly ONE online
  runner (`glue-ip-172-31-5-118-1`), `busy=true`. `ldr-to-main-promote-fleet`'s freshest tick (`30838152842`, 17:47:27Z)
  unchanged: `GATE BLOCK deployment-service: ci_status=FAILING` — the only in-flight LDR run (`30837367180`, queued
  against the true current HEAD `28c8d5f4`) is the correct state to leave for the next occurrence; did not
  cancel/redispatch. `GET /api/repo-blockers` → `open: []`. **Disposition: no code or workflow change made or needed** —
  identical to every prior pass for this repo today; pure runner-queue-depth wait. `AUTHORING_SLOT=ci-reconcile`
  (sentinel) — skipped the authoring-slot ping per established carve-out. Slot left clean (`deployment-service` and
  `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit). Adding no
  new todo — todo 2 (missing cooldown/dedup guard) already fully covers this; this is simply another same-day data point
  for it.

- **2026-08-03 ~17:49-17:55Z (`cicd` escalation `agt-2482ca` re-dispatched to slot 11, `features-service`,
  `wall_type=main_ci_red`, `pr_number=0`) — SAME escalation ID already fully diagnosed by the earlier slot-7 pass above
  (~16:00-16:20Z), re-verified from scratch, disposition unchanged but state has moved forward**: the LDR→main promotion
  PR (`#933`, `promote/features-service/7eca96acc75d`) has since **MERGED** (`mergedAt=2026-08-03T17:31:15Z`,
  `ci_status=SIT_VALIDATED` at merge time, v2-gated auto-merge armed) — the push-triggered `quality-gates-v2` run this
  produced on `main` (`30837128315`) was still `queued` (both `tests`/`checks` job slices, `content sentinel` slice
  already `success`) at investigation end, ~23min after dispatch, with zero progress — confirmed via
  `gh api .../actions/runners`: still exactly ONE online runner (`glue-ip-172-31-5-118-1`), `busy=true`, serialising
  behind 3 other queued quality-gates-v2 workflow runs for this repo (`30837377996` LDR workflow_dispatch, `30837121191`
  the now-closed promote-PR's own pull_request run, `30837126930` Semver Agent) — the same fleet-wide single-runner
  bottleneck this doc-chain has established across 8+ repos, not a stall. `gh pr list --base main` → 0 open PRs
  (promotion already landed, not stuck). Independently re-read the last real (non-cancelled) completed failure on both
  branches before accepting "no code gap": `main`'s `30825589070` (15:02:36Z) and LDR's `30818407385` (13:32:16Z) both
  failed via the established scheduler-starvation signature on different random hang sites
  (`test_trendline.py::test_convergence_acceleration_column` vs `test_momentum.py::test_volume_momentum_columns_present`
  for `tests`; both also hit the `[4/6] TYPE CHECK` exit-124 wall-clock timeout on `checks`, already ruled non-blocking
  cross-repo-warn noise by the earlier slot-7 pass's entry above) — no new failure shape, no code regression. Confirmed
  `PYTEST_TIMEOUT=300`/`PYRIGHT_TIMEOUT=300` intact and unchanged on current LDR HEAD. `GET /api/repo-blockers` →
  `open: []`. Did NOT cancel/redispatch the in-flight `30837128315` (would forfeit its ~23min of accumulated queue
  position for zero benefit), consistent with this doc-chain's established practice. **Disposition: no code or workflow
  change made or needed** — every sanctioned mitigation already exists on `live-defi-rollout`; the promotion has already
  landed and its confirmatory `main` run is progressing normally through the single-runner queue; remaining wall is pure
  runner-queue-depth wait. This is now the **3rd same-day dispatch of this exact escalation ID** (`agt-2482ca`: slot 7
  ~16:00-16:20Z, this slot-11 pass) — another direct data point for todo 2's operator-flagged missing cooldown/dedup
  guard (the dispatcher re-fired the same ID to a fresh slot ~90min later without the state having meaningfully changed
  beyond the promotion PR itself merging, which was already expected/in-flight, not a new gap needing agent action).
  `AUTHORING_SLOT=ci-reconcile` (sentinel, not a real numbered slot per `cicd.md`'s `^[0-9]+$` check) — skipped the
  authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left clean (`features-service` and
  `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch
  changes in either repo). Adding no new todo — todo 2 already fully covers this.

- **2026-08-03 ~18:00-18:40Z (`cicd` escalation `agt-01e4dd`, slot 9, `batch-live-reconciliation-service`,
  `wall_type=ldr_qg_failure`, `pr_number=296`) — 7th repo added to the corroboration list, `checks` leg exit-124
  signature, no code gap**: escalation cited the `checks` job of run `30837616904`
  (`promote/batch-live- reconciliation-service/b974adb29349`, PR #296). Read the job log directly: `qg-governor` queued
  the job `WAIT_CPU` for 2056s (`17:47:01Z`→`18:22:49Z`, in 30s increments) before admission, then `[4/6] TYPE CHECK`
  ran exactly 120s (`18:22:49.3Z`→`18:24:49.7Z`) and hit `❌ Type check FAILED/timeout (exit=124)` with 0 errors/0
  warnings extracted from `$PYRIGHT_OUT` (base-service.sh's own disambiguation for a genuine wall-clock timeout vs. a
  real type-error verdict) — the identical exit-124 signature already established fleet-wide in this doc-chain
  (`features-service`/`market-tick-data-service`/`execution-service`/`ml-service` above). Confirmed the `lint-codex`
  selector that ran immediately after in the SAME job (same log, same "✅ ALL QUALITY GATES PASSED (104s)" banner the
  `agt-2482ca` entry above already flagged as easy to misread) passed 104s later, clean — ruling out a systemic break in
  this repo's codex-compliance surface; the job's overall failure is `typecheck`-only. Confirmed
  `batch-live-reconciliation-service/scripts/quality-gates.sh` carries NO `PYRIGHT_TIMEOUT`/`PYTEST_TIMEOUT` override —
  stays at `base-service.sh`'s shared defaults (120s pyright / 150s pytest), matching `ml-service`'s
  lowest-ceiling-in-the-doc-chain precedent. Checked this repo's own base rate before accepting "same class, no action"
  (per the `market-tick-data-service`/`instruments-service` precedent of NOT pre-emptively raising a timeout a repo
  doesn't yet need): last 8 LDR `quality-gates-v2` runs = 5 success / 2 cancelled (superseded-by-newer-commit churn, not
  genuine failures) / 1 failure (this one) — a healthy self-clearing ratio, NOT the sustained-red bar that justified the
  repo-local timeout raises elsewhere. Did NOT add a `PYRIGHT_TIMEOUT` override. `gh api .../actions/ runners`: exactly
  ONE online runner, `glue-ip-172-31-5-118-1` (identical name/IP to every other repo in this doc-chain), `busy=true` —
  same fleet-wide bottleneck; this VM's own `uptime` also reads `load average: 34.20, 37.71, 35.67`, consistent with the
  contention level already logged for `execution-service` above — skipped a local `quality-gates.sh` reproduction (no
  `.venv` yet provisioned in this slot's clone; spinning one up would itself add load to an already-contended shared
  host for a confirmation the log evidence — 0 errors/0 warnings, a hard 120s wall-clock cutoff — already makes
  unambiguous). PR #296 had **already self-merged** (`mergedAt: 2026-08-03T17:37:45Z`, 5s after `createdAt: 17:37:40Z` —
  the same self-merge-before-confirmatory-check- completes pattern this doc-chain documents repeatedly);
  `gh pr list --state open` for this repo → 0 open PRs, confirms nothing is actually blocked. Fresh confirmatory runs
  were already queued against BOTH true current heads at investigation end — LDR (`423c95f0`, run `30841991289`) and
  `main` (`b187b331`, run `30837624393`, itself already 59+ min queued behind the single busy runner) — did not
  cancel/redispatch either (would forfeit real elapsed queue position for zero benefit), per this doc-chain's
  established practice. `GET /api/repo-blockers` → `open: []`. **Disposition: no code or workflow change made or
  needed** — every sanctioned mitigation is already at its correct (default, not-yet-warranted-to-raise) level, the
  cited failure is the established host-contention exit-124 class, and the promotion PR is not actually blocked (already
  merged); outcome of `30841991289`/`30837624393` left for the next occurrence per established practice.
  `AUTHORING_SLOT=ci` fails `cicd.md`'s `^[0-9]+$` check (not a real numbered slot) — skipped the authoring-slot ping
  per the established carve-out. Slot left clean (`batch-live-reconciliation-service` and `unified-trading-pm` both on
  `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch changes in either repo). Added
  `batch-live-reconciliation-service` to this doc's `repos:` frontmatter (1st occurrence for this repo in the
  doc-chain).

- **2026-08-03 ~19:00-19:25Z (`cicd` escalation `agt-684220`, slot 5, `deployment-service`, `wall_type=main_ci_red`,
  `pr_number=0`) — re-dispatch of the same repo's earlier entry, promotion not stuck, no code gap**: classified per this
  doc-chain's standard first check — `gh pr list --base main --state open` → 0 open PRs (the latest promotion PR, #679,
  already merged `19:02:20Z`); this is NOT a promotion-stuck wall. Confirmed no code/test diff between `origin/main` and
  `origin/live-defi-rollout` for the file behind the last genuine (non-cancelled) main failure —
  `tests/unit/test_turbo_data_validation.py` (failing selector
  `TestDataTypeValidation::test_expected_instrument_types_cefi_deribit`, `Failed: Timeout (>300.0s)` in run
  `30824452052`, a `workflow_dispatch` re-run, 1/2867 tests failed) — the code is identical on both branches, so this is
  the same host-contention-timeout class already established fleet-wide in this doc, not a regression to fix.
  `origin/main`'s own fresh push-triggered run (`30843993487`, from #679's merge commit) is genuinely progressing:
  `content sentinel` completed success, `tests`/`checks` slices `queued` since `19:04:05Z` (~21min at check time) behind
  the single online runner (`gh api .../actions/runners` → exactly one, `glue-ip-172-31-5-118-1`, `busy=true` — same
  runner name/bottleneck as every other repo in this doc-chain). Cross-checked sibling repos at the same moment
  (`market-tick-data-service` run in-progress 3h23m elapsed but its jobs ARE advancing serially — `checks` completed
  failure, `tests` in-progress since `19:10:00Z`; `instruments-service` 1h21m; `agent-orchestrator` 1h;
  `execution-service` 20m; `unified-api-contracts` 2 concurrent in-progress) — confirms the ONE shared runner is
  serializing the entire fleet's queue, exactly the structural bottleneck this doc-chain's todo 1 already tracks
  (`/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`). Did NOT cancel/redispatch the
  queued `30843993487` (would forfeit its accumulated queue position for zero benefit), per established practice.
  `GET /api/repo-blockers` → `open: []`. **Disposition: no code or workflow change made or needed** — the promotion has
  already landed, the confirmatory `main` run is genuinely queued (not stuck/hung) behind the fleet-wide single-runner
  bottleneck, and the underlying code is unchanged/correct on both branches; the "RED" ci_status is stale, dating to the
  earlier flaky-timeout workflow_dispatch run, and will self-clear once `30843993487` completes.
  `AUTHORING_SLOT=ci-reconcile` fails `cicd.md`'s `^[0-9]+$` check (not a real numbered slot —
  `server/ci_reconcile.py`'s self-detected bare-LDR wall path) — skipped the authoring-slot ping per the established
  carve-out. Slot left clean (`deployment-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead
  of origin beyond this doc's own commit; no branch changes in either repo). `deployment-service` already present in
  this doc's `repos:` frontmatter — no frontmatter change needed.

- **2026-08-03 ~19:35-20:10Z (`cicd` escalation `agt-f91096`, slot 3, `ml-service`, `wall_type=ldr_qg_failure`,
  `pr_number=335`) — this repo's 3rd occurrence in the doc-chain (1st: `agt-2336b3` `main_ci_red`, parent doc; 2nd:
  `agt-83db42` above, `typecheck` exit-124), and the FIRST occurrence of a genuinely new failure shape**: the cited run
  (`30835989289`, `checks` job) reproduced the already-established `typecheck` exit-124 wall-clock-timeout signature
  (`qg-governor` admitted the job after 880s `WAIT_CPU`, `[4/6] TYPE CHECK` ran `17:35:34Z`→`17:37:34Z`, exactly the
  120s ceiling, 0 errors/0 warnings extracted) — no new diagnosis needed there. Confirmed PR#335 had **already
  self-merged** (`mergedAt: 2026-08-03T17:16:15Z`, 5s after `createdAt`, the same
  self-merge-before-confirmatory-check-completes pattern this doc-chain documents repeatedly); `gh pr list --state open`
  for `ml-service` → 0 open PRs, nothing actually blocked. Checked current state rather than stopping at the cited run:
  `ldr-to-main-promote-fleet`'s freshest tick (`30848223829`, `20:00:06Z`) still reads
  `GATE BLOCK ml-service: ci_status=FAILING (cached='FAILING', live='FAILING')` — genuinely still red, not stale. The
  most-current LDR run against true current HEAD (`37d59f1`, run `30846230098`, dispatched by an earlier pass) had
  **already failed its `checks` job** by investigation time — but via a **different,
  previously-unlogged-for-this-doc-chain failure shape**:
  `error: Failed to install: basedpyright-1.38.2-py3-none-any.whl (basedpyright==1.38.2) — Caused by: The wheel is invalid: Missing .dist-info directory`,
  a hard `uv sync`/`uv pip install` failure (exit 2) during environment setup, well before `base-service.sh`'s own
  `[4/6] TYPE CHECK` step ever ran — i.e. NOT the typecheck-timeout class, a distinct infra failure mode. Being
  co-located with the shared self-hosted `glue-ip-172-31-5-118-1` runner (this session's shell runs on the same host),
  inspected the actual on-disk `uv` cache directly rather than reasoning from the log alone:
  `~/.cache/uv/wheels-v6/pypi/basedpyright/1.38.2-py3-none-any/` currently contains BOTH `basedpyright/` and
  `basedpyright-1.38.2.dist-info/` intact — the cache entry is NOT corrupted now, consistent with a transient corruption
  (a concurrent-write race under the extreme fleet-wide disk-I/O contention this doc-chain already establishes —
  `uptime` read `load average: 24.50, 29.64, 32.26` at investigation time) that self-healed on a later `uv`
  fetch/repair, not a persistent defect requiring a code/script fix. `df -h`: root filesystem 173G available (75% used,
  not full) — rules out the disk-full failure class (`shared_host_home_filesystem_full_ 2026_07_26.md`) as the direct
  cause. Per this doc-chain's established scope (todo 1: root-cause is capacity-side, tracked by
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md`, still `status: active`/Phase 2-3 open — did NOT attempt a
  broader infra fix such as isolating `UV_CACHE_DIR` per-runner), dispatched a fresh LDR re-verify run against the true
  current head (`gh workflow run quality-gates-v2.yml --repo IggyIkenna/ml-service --ref live-defi-rollout` → run
  `30848928130`, confirmed queued against `37d59f1`) rather than relying on the already-failed `30846230098`. Watched it
  for several minutes (background-polled, heartbeated) — still `queued` behind the single busy runner at investigation
  end, consistent with this doc-chain's established queue-depth pattern (not stuck/hung). `GET /api/repo-blockers` →
  `open: []`; no redundant runner-hogging job found to cancel. **Disposition: no code or workflow change made or
  needed** — `ml-service/scripts/quality-gates.sh` still carries no `PYRIGHT_TIMEOUT`/`PYTEST_TIMEOUT` override and this
  single non-sustained wheel-corruption occurrence does not meet the sustained-red bar that justified repo-local timeout
  raises elsewhere (same precedent `agt-83db42` already applied for this repo); the promotion PR is not actually blocked
  (already merged); outcome of `30848928130` left for the next occurrence per established practice. **New data point for
  todo 1**: this is the first occurrence in the doc-chain of a `uv`-wheel-install corruption (as opposed to a
  `pytest`/`basedpyright` wall-clock timeout) — same root cause class (shared-host resource contention), different
  failure mechanism (cache-write race vs. CPU-starved wall-clock), worth the ledger-coordination fix's authors being
  aware the contention surfaces in more than one failure shape. `AUTHORING_SLOT=ci` fails `cicd.md`'s `^[0-9]+$` check
  (not a real numbered slot) — skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI).
  Slot left clean (`ml-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond
  this doc's own commit; no branch changes in either repo). `ml-service` already present in this doc's `repos:`
  frontmatter — no frontmatter change needed.

- **2026-08-03 ~20:26-20:40Z (`cicd` escalation `agt-48c16d`, slot 12, `market-data-processing-service`,
  `wall_type=ldr_qg_failure`, `pr_number=0`) — MDPS's 1st occurrence in this doc-chain, both established failure shapes
  reproduced back-to-back, no code gap**: escalation cited run `30833923988` (commit `363b62b1`, since superseded — 5
  commits behind the true current LDR HEAD `28ffed1` at investigation time). Read both failed slices' full job logs
  directly via `gh api .../actions/jobs/<id>/logs` (`--log-failed`'s 50KB truncation cut off before the real failure, so
  fetched raw logs instead): (1) `checks` slice — `qg-governor` `WAIT_CPU`'d 862s before admission, then
  `[4/6] TYPE CHECK` hit the plain 120s `PYRIGHT_TIMEOUT` default (0 errors/0 warnings extracted, `exit=124`) — the
  established typecheck wall-clock-timeout signature. (2) `tests` slice — ran to ~100% of the suite (dots visible up to
  the final batch) then crashed during `pytest_sessionfinish` teardown with `OSError: cannot send (already closed?)` (an
  xdist worker-pipe-closed race), never reaching a `FAILURES`/summary section — consistent with this doc-chain's
  scheduler-starvation class, a distinct crash mechanism from the wall-clock-timeout shape but the same root cause.
  Checked the very next run (`30842024762`, ~2h later): `checks` passed this time (34m36s wall, sanctioned mitigations
  unaffected) but `tests` failed again — this time silently, zero pytest output at all between "Coverage floor" passing
  and the selector's `FAILED (exit=1)` 31s later (narrowed by the test-impact selector to a single file,
  `test_backfill_defi_dex_pool_swaps_source_correction.py`), after another 764s `WAIT_CPU` — same signature class,
  different specific manifestation (silent kill vs. teardown `OSError` vs. wall-clock timeout), all three now attested
  for this repo alone within ~2 hours. Checked `scripts/quality-gates.sh`: `PYTEST_TIMEOUT=300` already sanctioned-set,
  but **`PYRIGHT_TIMEOUT` has no override — still the bare 120s `base-service.sh` default** (unlike
  `features-service`/`deployment-service`, both at `PYRIGHT_TIMEOUT=300`, or `execution-service` at `900`). Per this
  doc-chain's established practice (todo 1: root-cause is capacity-side; `alerting-service`'s and `ml-service`'s prior
  entries both explicitly declined a same-shape timeout-raise for a single non-sustained occurrence), did **not** bump
  `PYRIGHT_TIMEOUT` here either — noting the gap as a candidate for the _next_ occurrence to weigh, not actioning it
  now. Confirmed `gh api .../actions/runners`: `market-data-processing-service` reports the identical single
  `glue-ip-172-31-5-118-1` runner, `status=online busy=true` — the same fleet-wide bottleneck, not repo-specific.
  `GET /api/repo-blockers` → `open: []`. A fresh run (`30850649487`) was already queued against the true current LDR
  HEAD (`28ffed1`) by an earlier tick before this session started — left it alone rather than dispatching a duplicate
  (would only discard its already-elapsed queue-position progress). `ldr-to-main-promote-fleet`'s latest tick
  (`30850478435`, `20:30Z`) confirms
  `GATE BLOCK market-data-processing-service: ci_status=FAILING (cached= 'SIT_VALIDATED', live='FAILING')` — will
  auto-promote the instant the in-flight run (`30850649487`) reports green; no manual promotion action taken or needed.
  **Disposition: no code or workflow change made or needed** — every candidate fix already exists or is deliberately
  withheld per established precedent; outcome of `30850649487` left for the next occurrence. **Timely note for todo
  1/3**: mid-investigation, `qg_governor_glue_runner_ledger_ coordination_2026_08_03.md`'s glue-runner-topology fix
  landed on LDR (`4247e957f`, `20:36Z` — pulled in via this session's own pre-commit rebase) and is documented as
  live-validated the same day (≥6 real concurrent repos correctly sharing one ledger, admission gating actually binding,
  up from the zero-shared-admission state that produced this doc-chain's whole failure class). Both of my cited MDPS
  runs (`16:49Z`, `18:36Z`) predate the fix, so they are NOT evidence against it landing successfully — the still-queued
  `30850649487` (dispatched `20:32Z`, 4 min before the fix commit, but each CI job self-clones
  `unified-trading-pm@live-defi-rollout` fresh at job-start rather than at dispatch-time) is the first real chance to
  observe whether MDPS's `WAIT_CPU` pileup shape actually disappears — worth the next occurrence (or a deliberate
  re-check of `30850649487`'s outcome) confirming this, before archiving todo 1/3 as closed.
  `AUTHORING_SLOT=ldr-ci-monitor` fails `cicd.md`'s `^[0-9]+$` check (not a real numbered slot) — skipped the
  authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left clean
  (`market-data-processing-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin
  beyond this doc's own commit; no branch changes in either repo). `market-data-processing-service` already present in
  this doc's `repos:` frontmatter — no frontmatter change needed.

- **2026-08-03 ~20:52-21:05Z (`cicd` escalation `agt-9c7994`, slot 9, `instruments-service`, `wall_type=ldr_qg_failure`,
  `pr_number=1068`) — instruments-service's 2nd occurrence in this doc-chain (1st: `agt-d12ed0` above), a fresh
  same-shape xdist-crash on a different random test, no code gap, PR already moot**: escalation cited failing run
  `30839360878` (`promote/instruments-service/710bcbf7b036`, triggered by pull_request, started `19:35:24Z`) — the
  `tests` slice crashed via the identical xdist `INTERNALERROR`/`AssertionError` shape already logged for this repo on
  `tests/unit/test_sports_comprehensive.py::TestCompetitionPhaseAdditional::test_whitespace_handling` (a
  `Failed: Timeout (>150.0s) from pytest-timeout` firing mid-flush of the xdist report-channel write, corrupting the
  worker rather than cleanly failing the test), `1 failed, 4420 passed, 6 skipped, 3 warnings in 728.53s`. Read the
  named test + the function it exercises (`classify_competition_phase`,
  `instruments_service/reference_data/adapters/sports/competition_phase.py`) before accepting the doc-chain's
  conclusion: pure string ops (`.lower().strip()`, `in`/`startswith` checks) with zero I/O, no loops, no regex — cannot
  itself hang for 150s under any input, ruling out an algorithmic-hang theory for this specific test. Confirmed PR #1068
  was **already MERGED** (`mergedAt: 2026-08-03T18:01:13Z`, ~94min before the failing run even started) — the same
  self-merge-before-confirmatory-check-completes pattern this doc-chain documents repeatedly;
  `gh pr list --state open --repo IggyIkenna/instruments-service` → 0 open PRs, confirms nothing is actually blocked by
  this failure. Reproduced fresh on current LDR HEAD (`d79b9d74`, 2 commits ahead of the failing run's `710bcbf7`) via a
  backgrounded `bash scripts/quality-gates.sh` (heartbeat loop posted every 180s while it ran):
  **`✅ ALL QUALITY GATES PASSED (114s)`**, tests phase `5195 passed, 6 skipped, 10 warnings in 54.90s` — zero timeouts,
  decisive confirmation of no code/test defect (the named test passed clean as part of the full suite). Confirmed
  `gh api .../actions/runners`: `instruments-service` still reports exactly ONE online runner, `glue-ip-172-31-5-118-1`,
  `busy=true` — the same fleet-wide bottleneck. `instruments-service/scripts/quality-gates.sh` carries no
  `PYTEST_TIMEOUT` override (stays at the shared 150s default) — per this doc-chain's established practice (todo 1:
  root-cause is capacity-side), did NOT add one for a single non-sustained occurrence. `GET /api/repo-blockers` →
  `open: []`. Checked in-flight runs on `live-defi-rollout`: a run was already `queued` (`30851282295`, dispatched by an
  earlier tick, headSha `47a631ff` — 1 commit behind the true current HEAD `d79b9d74`); the one intervening commit
  (`fix(tradfi): canonicalize present-set rollup's re-keyed combo instrument_type`) is orthogonal to the sports/
  competition-phase test class that failed, so left the queued run alone rather than cancel+redispatch (would forfeit
  its elapsed queue position for negligible freshness gain), consistent with established precedent. Noted (not actioned,
  informational only): the prior entry in this doc (`agt-48c16d`, MDPS) reports the
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` topology fix landed on LDR at `20:36Z` — this repro ran at
  `~20:57-20:59Z`, after that fix, though a single 114s local run is too fast/uncontended to itself evidence anything
  about shared-runner topology (it never touches the shared `glue` runner at all); the fix's effect on THIS repo's own
  CI-side contention remains for the next occurrence to observe. **Disposition: no code or workflow change made or
  needed** — PR already merged and moot, local reproduction clean, every sanctioned mitigation already in place; outcome
  of `30851282295` left for the next occurrence. `AUTHORING_SLOT=ci` is not a real numbered slot (fails `cicd.md`'s
  `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left
  clean (`instruments-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond
  this doc's own commit; no branch changes in either repo). `instruments-service` already present in this doc's `repos:`
  frontmatter — no frontmatter change needed.

- **2026-08-03 ~20:52-21:35Z (`cicd` escalation `agt-892a1c`, slot 2, `market-tick-data-service`,
  `wall_type=ldr_qg_failure`, `pr_number=817`) — 2nd occurrence for this repo (1st: `agt-72552a` above), PR already
  moot, one genuine code regression found+already-resolved by others, both remaining failures are this doc-chain's
  established signature, plus a NEW direct root-cause exclusion (ruled out cgroup-OOM and session/pgid-kill as the
  local-repro-death mechanism via cgroup inspection, not just inferred from CI-run patterns)**: escalation cited failing
  run `30830057533` (`promote/market-tick-data-service/fa991f12a6c1`) with BOTH `checks` and `tests` slices red.
  Confirmed PR #817 was **already MERGED** (`mergedAt: 2026-08-03T15:59:21Z`, ~3.5h before this escalation was worked) —
  the same self-merge-before-confirmatory-check-completes pattern this doc-chain documents repeatedly; 0 open PRs for
  this repo, nothing actually blocked. `checks` slice had TWO distinct failures: (a) **STEP 5.95 type:ignore ratchet
  regression** (live count 659 vs frozen baseline 658) — this is NOT the capacity-side class, a genuine code-adjacent
  gate; bisected independently via `git grep -c` across the commit range (no checkout, avoided a destructive-command
  mistake mid-bisect) and found the HEAD commit `06cd3ca5` (unrelated sports work) tipped a then-exactly-658 parent to
  659 via one new `# type: ignore[import-not-found]` in a fresh test file's `sys.path.insert`+bare-import — wrote a fix
  using this repo's own established pattern (`test_drop_sports_odds_phantom_uppercase.py`'s
  `importlib.util.spec_from_file_location` dynamic-load, which basedpyright never statically resolves, needing no
  suppression at all) to remove the ignore rather than raise the baseline. Mid-ship, discovered **slot-10 had
  independently already landed a different, equally valid fix 40min earlier** (`840c816d`, bumped
  `_MTDS_TYPE_IGNORE_BASELINE` 658→659 after a broader 9-commit bisection showing genuine cumulative drift, not a single
  bad add — see `plans/archive/issues/mtds_type_ignore_ratchet_regression_2026_08_03.md`, already `status: resolved`) —
  since their fix already fully resolves the gate (0 bare/broad ignores, all exact-rule-coded), abandoned my own
  competing fix as redundant rather than spend another full contended QG cycle re-shipping equivalent value; reset my
  local branch to match origin exactly (no force-flags, non-destructive `reset --soft`+`restore` since the commit was my
  own, never pushed/shared). (b) **typecheck timeout** (`exit=124`, ~121s hang matching the repo's bare 120s
  `PYRIGHT_TIMEOUT` default — confirmed via `grep` this repo has NEITHER `PYRIGHT_TIMEOUT` nor `PYTEST_TIMEOUT`
  overridden, unlike `features-service`/`deployment-service`/`execution-service` elsewhere in this doc-chain) — the
  established wall-clock-timeout signature, noted as a candidate gap for the next occurrence to weigh, not actioned for
  a single non-sustained occurrence per established practice. `tests` slice: xdist `INTERNALERROR`
  (`RuntimeError: Unexpectedly no active workers available`, a `pytest-timeout` SIGALRM firing mid-flush of the xdist
  report channel) after `2949 passed, 7 skipped, 1 xpassed` — the identical channel-corruption variant already logged
  for `instruments-service`/`execution-service` above. **New direct evidence for this doc-chain's capacity-side
  diagnosis**: attempted 3 local reproduction passes via backgrounded `quickmerge.sh` (a real ship attempt, not just a
  read-only repro), each progressively more isolated — (1) plain `nohup ... &` monitored from a separate tool call, (2)
  launch+monitor combined in one atomic backgrounded call, (3) full `setsid`+`disown` session detachment (confirmed via
  `ps -o ... state` showing `Ss`, a genuine new session leader) — all three died `Terminated` at ~6-10min wall-clock, at
  wildly different test-progress points (53%/22%/68%), ruling out a fixed test-count boundary. Before concluding
  "generic host contention" by default, checked TWO specific alternative mechanisms directly rather than assuming: (i)
  cgroup OOM — `/proc/self/cgroup` shows this whole slot's session lives in `system.slice/orchestrator.service`'s shared
  cgroup; `memory.events` read `oom 0, oom_kill 0` and `memory.current` (13.2GB) was well under both `memory.high`
  (49.4GB) and `memory.max` (58GB) — definitively ruled out; (ii) a session/pgid-level watchdog kill — the `setsid`
  attempt (fully detached into its own session/pgid) died on the same ~6-10min schedule as the non-detached attempts,
  ruling this out too. Neither of the two mechanisms I could directly test explains the kills; genuine host-wide CPU
  contention (load avg 25-35 sustained on 16 cores across the observation window, 10-15+ concurrent
  `quality-gates.sh`/`pytest` processes visible host-wide at every check) remains the only fitting explanation, but this
  entry narrows what it ISN'T for the next investigator. `gh api .../actions/runners`: 2 online runners
  (`glue-ip-172-31-3-59-1`, `glue-ip-172-31-5-118-1`), both `busy=true` — same fleet-wide bottleneck. A fresh run
  (`30854610738`) was already `queued` against the true current LDR HEAD (`840c816d`) at investigation end — left it
  alone. `GET /api/repo-blockers` → found ONE open: `RB-9732d071` (filed by slot-8, `created_at` 21:04:47Z — 16min AFTER
  `840c816d` had already landed at 20:48:42Z, apparently checked against a stale/uncached tree) — resolved it via
  `POST /api/repo-blockers/RB-9732d071/resolve` (1 waiter notified) since the underlying condition was already fixed.
  **Disposition: no code change shipped** (the genuine regression was already fixed by another agent before I could land
  my own equivalent fix; the two remaining failures are this doc-chain's established capacity-side class) — outcome of
  `30854610738` left for the next occurrence. `AUTHORING_SLOT=ci` is not a real numbered slot (fails `cicd.md`'s
  `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left
  clean (`market-tick-data-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin in
  either repo; no branch changes; no orphaned processes remaining under the slot's working directory, confirmed via
  `ps`). `market-tick-data-service` already present in this doc's `repos:` frontmatter — no frontmatter change needed.

- **2026-08-03 ~21:37-21:50Z (`cicd` escalation `agt-5ea4c7`, slot 14, `features-service`, `wall_type=ldr_qg_failure`,
  `pr_number=934`) — PR already self-merged before the failing run even started, moot post-merge artifact, identical
  doc-chain signature on a new random hang site**: escalation cited failing run `30840835293`
  (`promote/features-service/b0be030bd8e2`, `pull_request`, `createdAt: 18:20:35Z` — 3s AFTER PR#934's own
  `mergedAt: 18:20:32Z`) — the same self-merge-before-confirmatory-check-completes pattern this doc-chain documents
  repeatedly. Confirmed `main` == the merge commit (`compare/main...e6dfb41f` → `identical`, 0 ahead/behind); 0 open PRs
  for this repo (`gh pr list --base main`) — nothing actually blocked. Read the failing job's raw log directly rather
  than trusting the summary: the `tests` slice hung inside `tests/delta_one/unit/test_cli_parser.py` — a pure-`argparse`
  unit-test file (18 tests, zero I/O/mocks/fixtures that could genuinely hang; read the full file to confirm) — for
  ~10min (`21:10:53Z`→`21:21:06Z`) before `pytest-timeout` fired mid `pytest_runtest_call`→ `evaluate_xfail_marks` on
  MainThread, with collection stalled at only 12% (item ~2266/18450+1skipped) despite ~28min of real elapsed session
  time — the established scheduler-starvation signature (random hang site, no code-content overlap with any prior-logged
  occurrence), not a per-test defect. Confirmed both sanctioned mitigations intact + unchanged on current LDR HEAD
  (`5275fef1`): `PYTEST_TIMEOUT=300`/`PYRIGHT_TIMEOUT=300` (`features-service/scripts/quality-gates.sh:40-41`) — did NOT
  raise either further, per this doc-chain's established todo-1 practice (root cause is capacity-side;
  `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` still `status: active`, Phase 2-3 open, re-confirmed
  unchanged). `gh api .../actions/runners`: `features-service` has 2 online runners (`glue-ip-172-31-3-59-1` idle,
  `glue-ip-172-31-5-118-1` `busy=true`) — consistent with the fleet-wide bottleneck; host `uptime` load average **23.68,
  26.65, 27.50** on 16 cores at investigation time, corroborating the contention diagnosis. `GET /api/repo-blockers` →
  `open: []`. A fresh run (`30854599037`) was already `in_progress` against the true current LDR HEAD (`5275fef1`,
  confirmed matches local `git log`) at investigation end — left it running rather than cancel/redispatch (would forfeit
  real elapsed queue/run position for zero benefit), per established practice. **Disposition: no code or workflow change
  made or needed** — the specific PR#934 wall is fully moot (already merged, main identical), every sanctioned
  mitigation already exists and is intact, remaining state is a genuinely in-flight LDR re-verify; outcome of
  `30854599037` left for the next occurrence. `AUTHORING_SLOT=ci` is not a real numbered slot (fails `cicd.md`'s
  `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time Slack alert already covers the FYI). Slot left
  clean (`features-service` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this
  doc's own commit; no branch changes in either repo). `features-service` already present in this doc's `repos:`
  frontmatter — no frontmatter change needed. Now the ~17th+ same-day escalation for `features-service` alone across
  this doc-chain — further corroborates todo 2's operator-flagged missing cooldown/dedup guard on `ldr_qg_failure`
  re-dispatch for an already-resolved/moot state.

- **2026-08-03 ~21:50Z (interactive session, `/autonomous` on the ledger-coordination fork)** — the root-cause fix this
  doc-chain's todo 1 has been tracking has now LANDED and is archived:
  `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`
  (`unified-trading-pm@fada7dc20`/`4247e957f`), live-validated (6+ real repos sharing one ledger, admission gating
  binding) and soaked (~73min, 0 OOM, 0 ghost reservations). **Not yet verified**: whether this specific doc-chain's
  `main_ci_red`/`ldr_qg_failure` re-fires actually stop recurring now that it's live — todo 1's own "once landed,
  re-test" step still needs real elapsed time post-fix + a fresh escalation-history pull to answer, not assumed from the
  ledger fix's own soak alone (different observable: this doc tracks ESCALATION recurrence, the fork's soak tracked
  ADMISSION correctness — related but not the same metric). Leaving todos 1 and 3 open for whoever next checks this
  doc-chain to make that call with real post-fix escalation data.

- **2026-08-03 ~22:04-22:15Z (`cicd` escalation `agt-0499f8`, slot 6, `features-service`, `wall_type=ldr_qg_failure`,
  `pr_number=0`) — the SAME run `agt-5ea4c7` (above) left in-flight has since completed FAILED; re-verified from scratch
  with a full local reproduction (not just log-reading), disposition unchanged, one direct new data point for todo 1**:
  `agt-5ea4c7`'s in-flight run `30854599037` (headSha `5275fef1`, matches current LDR HEAD) completed `failure` at
  `21:50Z` on `tests/delta_one/unit/test_feature_groups/test_anomaly.py::test_volume_zscore_columns` — hung ~7m42s
  inside `_add_lagged_features`'s `features[feature].shift(lag)` before `pytest-timeout` fired, yet ANOTHER
  previously-unlogged random hang site for this repo (18th+ distinct test in the doc-chain), reinforcing the
  scheduler-starvation signature over any single-test theory. Rather than trust the log alone, ran a full LOCAL
  `bash scripts/quality-gates.sh` reproduction (backgrounded, heartbeated every 180s per `cicd.md`'s mandatory pattern):
  **tests slice — 18244 passed, 209 skipped, 0 failures, 0 timeouts, in 262.79s (4m22s)** — decisive,
  `test_volume_zscore_columns` included and green, ruling out any code/test defect. The SAME local run then hit the
  **identical timeout-class failure itself**, on `checks`/`[4/6] TYPE CHECK`: `run_timeout` SIGTERM'd basedpyright at
  the `PYRIGHT_TIMEOUT=300` ceiling (`exit=143`) — direct first-hand confirmation, on this exact shared host, that the
  contention is real and ongoing right now (not just inferred from CI logs): `uptime` read `load average: 24-27` at
  dispatch time, still `17-23` minutes later with 10+ concurrent `quality-gates.sh` processes visible host-wide via
  `ps aux` (matching every prior entry's host-state reading). Confirmed both sanctioned mitigations
  (`PYTEST_TIMEOUT=300`/`PYRIGHT_TIMEOUT=300`) intact and unchanged in `features-service/scripts/quality-gates.sh` — did
  NOT raise either further, per this doc-chain's established todo-1 practice. `gh pr list --base main --state open` → 0
  open PRs (nothing blocked). `GET /api/repo-blockers` → `open: []`. `ldr-to-main-promote-fleet`'s freshest tick
  (`30856940815`, `22:00Z`) reads `GATE BLOCK features-service: ci_status=FAILING (cached='FAILING', live='MAIN_GREEN')`
  — live already reads green (content-equivalent tree), cached just hasn't caught up; no manual promotion action needed.
  `gh api .../actions/runners`: both online runners (`glue-ip-172-31-3-59-1`, `glue-ip-172-31-5-118-1`) were
  `busy=false` at investigation start (first time this doc-chain has observed an idle fleet for this repo — consistent
  with `agt-48c16d`'s note that the `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` topology fix had just
  landed) but both flipped back to `busy=true` within ~10min as fleet-wide activity resumed — the idle window was
  transient, not a sustained fix-confirmed calm. No run was in flight against the true current HEAD (`5275fef1`) at
  investigation start (the completed-failure `30854599037` was the latest) — dispatched a fresh one
  (`gh workflow run quality-gates-v2.yml --repo IggyIkenna/features-service --ref live-defi-rollout` → run
  `30857768146`, confirmed queued against `5275fef1` within seconds); at entry time it is `in_progress`
  (`content sentinel` succeeded, `checks`/`tests` both still running) — left it running rather than cancel/redispatch,
  per established practice. **Disposition: no code or workflow change made or needed** — full local reproduction is the
  strongest evidence yet for this repo that the calculator/test code itself is correct; the wall is purely
  runner-queue-depth/host-contention, now also directly reproduced on this investigating session's own shared host, not
  just inferred from CI logs. Outcome of `30857768146` left for the next occurrence. **New data point for todo 1**: the
  ledger-coordination fix's brief idle window (both runners momentarily `busy=false`) did not hold — re-confirms todo
  1's "re-test once landed" step is not yet answerable from a single observation; needs a sustained idle/low-contention
  period, not a momentary one, before concluding the fix closed this class. `AUTHORING_SLOT=ci-reconcile` (sentinel, not
  a real numbered slot per `cicd.md`'s `^[0-9]+$` check) — skipped the authoring-slot ping (the dispatch-time Slack
  alert already covers the FYI). Slot left clean (`features-service` and `unified-trading-pm` both on
  `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch changes in either repo).
  `features-service` already present in this doc's `repos:` frontmatter — no frontmatter change needed. Now the ~18th+
  same-day escalation for `features-service` alone across this doc-chain — further corroborates todo 2's
  operator-flagged missing cooldown/dedup guard on `ldr_qg_failure` re-dispatch for an already-in-flight-verification
  state.

- **2026-08-03 ~22:15-22:25Z (`cicd` escalation `agt-63a88d`, slot 9, `unified-api-contracts`,
  `wall_type=ldr_qg_failure`, `pr_number=837`) — this repo's own founding case
  (`pytest_timeout_60s_flaky_under_contention_2026_07_29.md`) recurs in the xdist-channel-corruption variant, no code
  gap, promotion already moot**: escalation cited run `30849457988` (created `20:18:06Z`, headSha `862ff5a6`) failing
  the `tests` slice — read the full job log directly rather than trusting the cached summary:
  `6205 passed, 686 skipped, 4 xfailed, 1 warning in 464.77s` with **zero named test failures**, then
  `INTERNALERROR> RuntimeError: Unexpectedly no active workers available` — `pytest-timeout`'s SIGALRM handler fired
  mid-`execnet` channel send (`xdist/remote.py:289`→`gateway_base.py::dumps_internal`), corrupting the worker/master
  protocol and killing the session — the identical xdist-channel-corruption shape already logged for
  `instruments-service` (`30774745528`) and `execution-service` (`30822100465`) above, not a per-test defect (no test
  node was ever named as failing). Checked PR state first: `gh pr view 837` → **already `MERGED` at `20:16:22Z`**, ~2
  minutes BEFORE this confirmatory run even started — the same self-merge-before-confirmatory-check-completes pattern
  this doc-chain documents repeatedly (`agt-3fb529`/deployment-service#676 precedent); `gh pr list --state open` → 0
  open PRs, confirms nothing is actually blocked by this run's outcome. Checked whether a repo-specific `PYTEST_TIMEOUT`
  override was warranted before considering one: `unified-api-contracts/scripts/quality-gates.sh` has no override (stays
  at `base-service.sh`'s shared 150s default); pulled the last 40 LDR `quality-gates-v2` runs — **28 success / 10
  cancelled / 2 failure**, a healthy base rate (matches the `market-tick-data-service` precedent for withholding the
  mitigation, not the ~100%-red bar that justified `PYTEST_TIMEOUT=300` elsewhere) — did NOT add an override.
  `gh api .../actions/runners`: exactly ONE online runner (`glue-ip-172-31-3-59-1`), `busy=true` — same fleet-wide
  single-runner bottleneck. `GET /api/repo-blockers` → `open: []`. LDR HEAD had already advanced twice since the failing
  run (`862ff5a6`→`cec272e9`→`6806fd50`, both intervening commits promotion-backmerge-only) and an intervening run
  against `cec272e9` had already gone `success` (`30850665921`) — no run yet targeted the true current HEAD, so
  dispatched `gh workflow run quality-gates-v2.yml --repo IggyIkenna/unified-api-contracts --ref live-defi-rollout` →
  run `30858497649`, confirmed queued against `6806fd50` within seconds (a second, independently fleet-dispatched run,
  `30858491949`, landed on the same headSha ~5s earlier — coincidental, not caused by this dispatch). **Disposition: no
  code or workflow change made or needed** — the promotion already completed before this run even started, every
  sanctioned mitigation elsewhere in this doc-chain remains correctly withheld here given the healthy base rate,
  remaining wall was pure runner-queue-depth/host-contention on an already-moot post-merge artifact; outcome of
  `30858497649` left for the next occurrence. `AUTHORING_SLOT=ci` is not a real numbered slot (fails `cicd.md`'s
  `^[0-9]+$` check) — skipped the authoring-slot ping. Slot left clean (`unified-api-contracts` and `unified-trading-pm`
  both on `live-defi-rollout`, 0 commits ahead of origin beyond this doc's own commit; no branch changes in either
  repo). Added `unified-api-contracts` to this doc's `repos:` frontmatter (1st full write-up for this repo in this
  specific split, though it is the doc-chain's founding case per the 2026-07-29 parent).

- **2026-08-03 ~22:30-22:50Z (`cicd` escalation `agt-5467b9`, slot 5, `agent-orchestrator`, `wall_type=ldr_qg_failure`,
  `pr_number=766`) — `chore(promote): LDR → main` PR gate reported red on an already-fully-landed promotion, this
  doc-chain's self-merge-before-confirmatory-check-completes pattern one more time, this time on the doc-chain's own
  home repo**: escalation cited run `30843984596` (`event=pull_request`, headSha `57e38956`, PR #766) failing the
  `QG slice (checks)` job's `Install dependencies` step with the identical `uv`-cache-corruption-under-contention
  signature already tracked repeatedly above —
  `error: Failed to install: typing_inspection-0.4.2-py3-none-any.whl ... Caused by: failed to read directory /home/ubuntu/.cache/uv/archive-v0/FmTx4U7lXPejS46mFkrlp: No such file or directory (os error 2)`
  — a shared-runner concurrent-`uv`-cache race (the same `archive-v0` hardlink/directory-vanish shape as the
  `pytz`/`vcrpy`/`basedpyright` entries elsewhere in this doc-chain), not a code or dependency-lock defect.
  `gh run view --json createdAt`: this run was created `2026-08-03T19:02:25Z` — the EXACT same instant `gh pr view 766`
  shows the PR `mergedAt` — confirming the now-familiar race (required check kicks off at merge time, then queues for
  ~2h behind the sole shared runner before finally failing well after the PR is already gone).
  `gh pr list --state all --limit 5`: PR #766 `MERGED`, and the fleet has since promoted TWICE more past it — PR #767
  (`headRefOid` = current local LDR HEAD `d71f1d9`) also already `MERGED` (`22:41:59Z`), `main` HEAD now `48f839e5` (PR
  #767's squash commit). Decisive external evidence in lieu of a fresh local reproduce (per this doc-chain's established
  practice of trusting a corroborating real CI run over a redundant local one when one already exists):
  `gh run list --branch live-defi-rollout --limit 5` shows a **`success`** `quality-gates-v2` run (`30854583572`,
  56m10s, completed `2026-08-03T22:21:50Z`) landed AFTER this failing run's own conclusion (`21:01:36Z`) and BEFORE PR
  #767 merged — LDR has been proven green since, ruling out a code regression definitively. `main`'s own post-PR#767
  required check (`30859629406`) was `queued`/`in_progress` at check time, not red. `GET /api/repo-blockers` →
  `open: []`. **Disposition: no code or workflow change made or needed** — the promotion business-outcome (LDR→main,
  twice over) completed cleanly before and independent of this stale check's eventual failure; root cause remains the
  fleet-wide shared self-hosted-runner `uv`-cache contention already tracked as out-of-scope-for-one-shot-wall-clearing
  (`/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md`). `AUTHORING_SLOT=ci` is not a
  real numbered slot (fails `cicd.md`'s `^[0-9]+$` check) — skipped the authoring-slot ping. Slot left clean
  (`agent-orchestrator` and `unified-trading-pm` both on `live-defi-rollout`, 0 commits ahead of origin beyond this
  doc's own commit; no branch changes in either repo). Added `agent-orchestrator` to this doc's `repos:` frontmatter
  (1st occurrence for this repo in this doc-chain, though the doc-chain itself lives in the PM repo that ships via this
  same repo's orchestrator).

- **2026-08-09 (plan_reconciler ci-tranche, agt-04cb0e)** — re-tested todo 1's gate: ledger-coordination fix landed
  (`status: complete`, Phase 2+3 `[x]`) but recurrence did NOT stop — `continued3` logs a fresh occurrence 2026-08-09
  ~02:20-03:15Z. Todo 3's archive condition unmet; both stay open.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:b3a968bf485c1cf8]: KEEP-NA,
valid — 2 open checkboxes (matches phase0=2 and my grep; todo 2 is already [x] DONE 2026-08-08, a cooldown/dedup fix,
not open). Todo 1 (P3, track capacity-side root-cause fix + re-test) and todo 3 (P3, gated
archive-all-four-docs-together condition) both hinge on qg_governor_glue_runner_ledger_coordination_2026_08_03.md Phase
2-3 'landing AND holding (sustained)'. Independently verified (direct grep of the archived doc's frontmatter, not just
trusted the claim): that doc is genuinely at plans/archive/2026_08/, status: complete -- Phase 2-3 landed.

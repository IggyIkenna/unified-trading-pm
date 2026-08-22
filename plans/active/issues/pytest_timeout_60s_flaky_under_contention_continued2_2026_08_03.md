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
    /plans/archive/2026_08/pytest_timeout_60s_flaky_under_contention_continued2_progress_log_history_2026_08_16.md,
    /plans/archive/2026_08/operator_ruling_record_ci_line_cap_splits_2026_08_16.md,
  ]
created: 2026-08-03
author: unknown
last_updated: 2026-08-21 # line-cap remediation split (Trust Mode) -- extracted the bulk 2026-08-03 Progress Log to the archive doc above; was 1013L, flagged unresolved since 2026-08-15
parent_epic: security_and_cross_cutting_master
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

- [ ] [INFRA] P3. 1. Root-cause fix is capacity-side, not another per-repo timeout raise — track landing of
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
- [ ] [INFRA] P3. 3. Once `/plans/archive/2026_08/qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phases 2-3
      land, re-check whether this entire doc-chain (3 docs, ~30+ occurrences across 7+ repos) self-resolves — if the
      ledger coordination fix genuinely closes the class, archive all three docs together rather than leaving them open
      indefinitely as "still waiting."

## Progress Log

> **Progress-Log history (2026-08-16)**: this doc's bulk 2026-08-03 Progress Log — ~20 individual `cicd`-escalation
> investigation entries across 7+ repos (deployment-service, features-service, alerting-service,
> market-tick-data-service, instruments-service, ml-service, market-data-processing-service,
> batch-live-reconciliation-service, unified-api-contracts, agent-orchestrator, execution-service), every single one
> disposition "no code or workflow change made or needed" — pure fleet-wide single-self-hosted-runner queue-depth
> contention, the bug class this doc-chain tracks — was extracted verbatim to
> [`/plans/archive/2026_08/pytest_timeout_60s_flaky_under_contention_continued2_progress_log_history_2026_08_16.md`](/plans/archive/2026_08/pytest_timeout_60s_flaky_under_contention_continued2_progress_log_history_2026_08_16.md)
> to bring this doc back under the 1000-line hard cap. Nothing was summarized or altered — read the linked doc for the
> full narrative. The 2026-08-09 status update below (post-ledger-coordination-fix recurrence check) and the
> na-eligibility-audit verdict are kept here since they directly inform this doc's own still-open todos 1/3.

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

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-20**: refreshed context_scope (5 entries).

**na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid -- 2 open P3 todos, both tracking/gating on qg_governor_glue_runner_ledger_coordination_2026_08_03.md's capacity-side fix. That fix has technically landed (archived, status:complete, Phase 2-3 both [x]) but this doc's own Progress Log (2026-08-09, plan_reconciler) and embedded na-eligibility-audit verdict (2026-08-10) both independently confirm recurrence continued PAST the fix landing -- a fresh corroborating occurrence on 2026-08-09 (market-tick-data-service, under measured heavy host...

- **2026-08-21 — ruling D1 (Stale meta-doc disposition)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Approve all — repeated audits agree these are churn, not live tasks; the two
  keep-open items and the one split are the only exceptions. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger. Applied: this doc is one of the two named
  "keep-open" exceptions — its own 2026-08-21 na-eligibility-audit verdict (below) independently found 2 fresh
  post-fix recurrences (`deployment_api_qg_pre_existing_red_inventory_classification_2026_08_19.md`,
  `utl_qg_host_pressure_perf_and_fd_failures_2026_08_20.md`) and explicitly ruled "both open todos correctly stay
  open — do NOT close or archive on the Phase 2-3 landing alone." No todo changed by this ruling; recorded here for
  the ledger.

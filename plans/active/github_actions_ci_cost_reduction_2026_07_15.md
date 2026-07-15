---
doc_type: plan
title:
  GitHub Actions CI/CD cost reduction — self-host the glue, kill the minute-minimum tax, fix cron cadence (DRAFT /
  suggestions)
summary: >-
  PM is ~48% of a ~$1,000/mo GitHub Actions bill despite a code freeze because it is the fleet CI/CD control tower —
  ~79% of its runs are automation (status routing, deploy dispatch, promotion/health crons), only ~8% are doc commits.
  All repos are private (every minute billed) and there are ZERO self-hosted runners, so the biggest untapped lever is
  moving lightweight glue off $0.008/min GitHub-hosted runners onto compute we already run 24/7. This plan proposes a
  tiered fix — self-host the switchboard+crons, collapse the quality-gates job fan-out that pays a 1-min minimum per
  sub-second job, retire a duplicate promote bot + slow crons, and (later) move ci-status-update to a serverless write.
  THESE ARE SUGGESTIONS FOR REVIEW, NOT FINAL DECISIONS — nothing here is approved to execute yet.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, self-hosted-runner, workflows, spend-reduction, draft, suggestions]
related:
  - github_billing_dashboard_access_2026_07_09.md
  - cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  - "operator ask 2026-07-15 (spend investigation): GitHub bill ~$50-82/day during code freeze; why is PM so expensive"
  - "live Enhanced-Billing usage report (users/IggyIkenna/settings/billing/usage) via github-billing-token, Jun+Jul 2026"
  - "PM Actions run-mix sample: 1000 runs / 13.5h window ending 2026-07-15T06:53Z"
drift_direction: advance-code
---

# GitHub Actions CI/CD cost reduction — proposal (DRAFT)

> **⚠️ THESE ARE SUGGESTIONS, NOT FINAL DECISIONS.** This plan is `status: draft` and **human-only** (`assigned_vm: NA`,
> `execution_scope: local-only`) — it will **not** be ingested or dispatched to any agent. It exists to lay out the
> options and evidence so the operator can decide **which, if any,** of these changes to make and in what order. No
> workflow, runner, or infra change below is approved to execute. Flip individual items to real todos (and the plan to
> `active`) only after an explicit operator ruling on the open questions in § "Decisions needed".

---

## Why we are spending the money (evidence)

Pulled from the **live GitHub Enhanced-Billing ledger** (not estimates) via the existing `github-billing-token`:

- **100% of spend is Actions Linux compute minutes** — not storage, not packages, not Copilot.
- **June net $1,441 · July (1–15) net $485**
  (~$1,000/mo run-rate). Daily figures matched the operator's memory exactly
  (Jul 13 = $82, Jul 14 = $77).
- **PM is the single biggest repo — 35% of spend in June, rising to ~48% in July.**
- PM produced **1,000 workflow runs in a 13.5-hour window (~1,778/day)** during a code freeze. Trigger mix by billed
  share: **repository_dispatch 55% · schedule 18% · pull_request 13% · push 8% · workflow_dispatch 6%.** → **~79%
  automation, ~21% code, and only ~8% is PM's own commits.**
- All repos are **private** (every minute billed; public would be free) and there are **zero self-hosted runners**
  registered — the cheapest lever is completely untapped.

**Root cause:** PM is not expensive because it is a docs repo. It is the **CI/CD control tower** — every repo's CI
dispatches status/build/deploy jobs _into_ PM, and PM runs the fleet's promotion/health cron machinery. The cost is the
switchboard traffic + the timer-driven bots, both of which boot a full `ubuntu-latest` VM for lightweight glue.

### Top cost drivers in PM (13.5h sample, by est. billed-minute share)

| Workflow                      | Share | Trigger              | What it does                                                                                                                        | Assessment                                   |
| ----------------------------- | ----- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `ci-status-update`            | ~33%  | repository_dispatch  | Boots a 2-job VM every ~2.5 min to write ONE Firestore CI-status row for whichever repo just finished CI                            | Purpose right, mechanism ~100× too heavy     |
| `cloud-build-router` + `-aws` | ~20%  | repository_dispatch  | Routes a "QG passed → go build/deploy" dispatch to GCP + AWS, 3 jobs each, both fire on every green                                 | Fires even in freeze when nothing deploys    |
| `quality-gates-v2`            | ~18%  | pull_request         | The real tests/lint/typecheck — but splits into 5–7 jobs, each billed a 1-min minimum (9s "content sentinel" = 1 full min)          | Legit compute, inflated ~3× by fan-out       |
| promotion + health crons      | ~18%  | schedule (_/15–_/30) | `ldr-to-main-promote`, `-fleet`, `staging-to-main`, `branch-health`, `ci-health` — poll "anything to ship/any failures?" on a clock | Real safety nets; over-frequent + duplicated |

---

## Guiding principle

**GitHub-hosted runners are for running _tests_ in a clean throwaway box. Stop using them as the always-on _plumbing_
for status-writing, dispatch-routing, PR-opening, and health-polling.** That glue should run on compute we already pay
for 24/7 (self-hosted runner minutes are free from GitHub's side), or not boot a VM at all. Because every repo is
**private, there are no untrusted fork PRs**, so self-hosted runners are safe here even for PR-triggered workflows —
though we still keep heavy test jobs on hosted runners to avoid loading our own VMs.

---

## Proposed work (SUGGESTIONS — each is a decision, not a commitment)

### Phase 0 — Make the case airtight (do this first, low-risk, read-only)

- [ ] [MEASURE] P1. Pull the **full 30-day** per-workflow billed-minute attribution (not the 13.5h sample) so every %
      and $ below is exact before we change anything. Script against `settings/billing/usage` + the Actions runs/jobs
      API; store the breakdown table as evidence in this plan's Progress Log.
- [ ] [MEASURE] P1. Confirm fleet-wide there are **zero self-hosted runners** and record the current baseline: $/mo per
      repo and per top workflow (the number we measure the fix against).

### Phase 1 — Self-host the switchboard + cron glue (biggest win, ~70% of PM)

- [ ] [OPERATOR-DECISION] P1. **Decide the runner host** — reuse the always-on orchestrator VM (near-zero marginal cost,
      but shares capacity with AO) vs a small dedicated runner VM (~$30–60/mo, isolated). Recommendation: orchestrator
      VM to start, split out later if capacity contends.
- [ ] [INFRA] P1. Register **3–4 self-hosted runner processes** on the chosen host with label `glue` (parallel so
      concurrent dispatches don't serialize into a backlog), under systemd with auto-restart; verify toolchain
      (gcloud/python/gh) present.
- [ ] [REVIEW] P1. **Security gate:** confirm every workflow moved to `glue` is triggered ONLY by `repository_dispatch`
      / `schedule` / `push` (no untrusted fork-PR code ever runs on our VM). Any `pull_request`-triggered job stays on
      GitHub-hosted for this phase.
- [ ] [INFRA] P1. Flip `runs-on: ubuntu-latest` → `runs-on: [self-hosted, glue]` for the glue workflows
      (`ci-status-update`, `cloud-build-router`, `cloud-build-router-aws`, `ldr-to-main-promote`, `-fleet`,
      `staging-to-main`, `branch-health`, `ci-health`, and the small reconcile/conflict/plan-health bots) — via the
      workflow-template SSOT + `rollout-workflow-templates.sh`, never hand-editing per-repo copies.
- [ ] [VERIFY] P1. After 3–5 days, re-measure PM's billed minutes; confirm the glue workflows now bill ~$0 and the VM
      absorbed the load without contention.

### Phase 2 — Kill the 1-minute-minimum tax on quality-gates-v2 (~18%)

- [ ] [INFRA] P2. In the `quality-gates-v2` / `python-quality-gates-v2` templates, **collapse the sub-minute jobs**
      (content-sentinel, Slack-notify, dispatch) into the main/slice jobs. Rule: keep a job split out ONLY when it
      genuinely runs >1 min AND parallelism speeds developer feedback; otherwise merge to stop paying a 1-min minimum
      per boot.
- [ ] [VERIFY] P2. Re-measure a representative QG run's billed job-minutes before/after; target ~30–40% fewer billed
      minutes per run with no loss of gate coverage.

### Phase 3 — Cadence + de-duplication (cheap wins)

- [ ] [OPERATOR-DECISION] P2. **Retire the duplicate promote bot** — `ldr-to-main-promote` and
      `ldr-to-main-promote-fleet` do near-identical work (mid-migration overlap). Decide which survives, finish the
      migration, delete the other (no shim).
- [ ] [INFRA] P2. Slow promotion/health crons from `*/15` toward **hourly** (or purely event-driven off the promotion PR
      event) during freeze; keep the event path for real-time needs. Lower priority once these are on self-hosted, but
      fewer idle boots is cleaner regardless.
- [ ] [INFRA] P3. **Debounce `ci-status-update`** — coalesce multiple repo reports arriving within a short window into
      one write instead of N runner boots (careful to preserve the CAS + stale-write ordering the Firestore store relies
      on).

### Phase 4 — (Later / optional) Move ci-status-update off Actions entirely

- [ ] [OPERATOR-DECISION] P3. Decide whether to go further than self-hosting for the busiest workflow: wrap the existing
      `scripts/cicd/ci_status_store.py` write logic in a small **Cloud Run / Cloud Function** endpoint and have each
      repo's CI POST directly, removing the Actions run (and its checkout) entirely. Folds into Phase 1's savings but
      removes VM load + cuts latency ~30s→~1s. Medium effort — only if we want the elegant end-state.

### Phase 5 — Prove the savings

- [ ] [VERIFY] P3. Two weeks after rollout, re-pull the billing ledger and compare to the Phase-0 baseline; record
      actual $/mo saved per repo. Target landing: **fleet ~$1,000/mo → ~$300–400/mo**, and structurally flat when
      activity grows (glue cost stays on our VM; only real test minutes scale).

---

## Expected impact (rough — Phase-0 will make exact)

| Step                                         | Effort | Est. monthly saving            |
| -------------------------------------------- | ------ | ------------------------------ |
| 1. Self-host switchboard + cron glue         | Low    | ~$400–500 fleet                |
| 2. Collapse `quality-gates-v2` fan-out       | Low    | ~$50–80                        |
| 3. Retire duplicate promote bot + slow crons | Low    | ~$30–50                        |
| 4. (Later) Serverless `ci-status-update`     | Medium | folds into #1, removes VM load |

## The honest tradeoff

Self-hosted runners are infrastructure **we** now maintain (patching, disk, capacity, auto-restart). For lightweight
glue on a VM we already run 24/7 that is nearly free. For heavy test fleets it is real work — which is exactly why the
proposal keeps heavy test jobs on GitHub-hosted and only moves the glue.

## Decisions needed (operator) before any of this becomes `active`

1. Approve the direction at all? (self-host glue vs leave as-is vs a different approach)
2. Runner host: shared orchestrator VM vs dedicated small runner VM?
3. Which promote bot survives (`ldr-to-main-promote` vs `-fleet`)?
4. Do we want Phase 4 (serverless ci-status-update), or is self-hosting enough?
5. Acceptable cron cadence during freeze (hourly? event-only?).

## Codex SSOTs (read before executing any item)

- `codex/08-workflows/ci-cd-flow.md` — quickmerge / LDR-is-SSOT / promotion flow / branch protection
- `codex/05-infrastructure/` — runner + VM infra conventions; workflow-template rollout
- `codex/04-architecture/ci-alerting.md` — notify-slack carrier (touched if cron cadence changes)
- Related: `plans/active/issues/github_billing_dashboard_access_2026_07_09.md` (the billing-token that made this
  measurable), `plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` (the LDR→main promotion refactor this
  overlaps)

## Progress Log

- 2026-07-15 — Plan drafted from the live billing investigation (this session). Evidence: Enhanced-Billing ledger
  Jun/Jul 2026 + PM 1000-run/13.5h Actions run-mix sample. Status draft, human-only, suggestions-not-final. Awaiting
  operator ruling on § "Decisions needed".

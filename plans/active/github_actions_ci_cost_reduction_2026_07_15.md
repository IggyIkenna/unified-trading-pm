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
  sub-second job, and fix cron cadence. Decisions closed 2026-07-15 (B1 on the planning-VM; ci-status-update trimmed to
  use the VM's warm state; serverless B2 dropped; promote bots kept). Execution in progress.
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

## Execution pre-flight & runbook (READ FIRST — context not obvious from the todos)

**State 2026-07-15:** decisions closed; runner infra authored + pushed (`scripts/self-hosted-runners/`); **NOTHING
deployed, no `runs-on` flipped.** Work continues from **slot 1** (`.tabs/1/`), root left to the AO worker.

### The flip set — CRITICAL split (`bash scripts/self-hosted-runners/classify-glue-workflows.sh`)

- **46 = MOVE (PM-local DIRECT `.github/workflows/*.yml`)** → edit `runs-on` directly in PM. Safe — only PM, which has
  the runners.
- **10 = KEEP hosted**, of which two special classes you must NOT naively flip:
  - **`KEEP-T` (4): `main-backmerge-to-ldr`, `semver-agent`, `major-bump-issue-handler`, `request-major-bump`** — these
    are **fleet templates** (`scripts/workflow-templates/`) rolled to EVERY repo. **DO NOT flip the template** (only PM
    has runners → hangs the other ~24 repos) and **DO NOT hand-edit PM's copy** (banned rule). Leave hosted (low value).
  - **`KEEP*` (2): `build-smoke-all-repos` (docker buildx), `publish-package` (wheel)** — build locally, too heavy for
    the light VM.
  - Plus `quality-gates-v2` + `python-quality-gates-v2` (heavy tests) + 2 `pull_request` bots.

### Deploy mechanism (Track 1 step 1)

- The planning-VM `i-0c9b283b31d6b5ca7` has **no inbound SSH/:8765** → drive it via **AWS SSM**
  (`aws ssm send-command --region ap-northeast-1 --instance-ids i-0c9b283b31d6b5ca7 …`), the same channel as
  `/check-agent-orchestrator`. Then `bash scripts/self-hosted-runners/setup-glue-runners.sh install`.
- Registration token = an **admin PAT with `Administration:write` on unified-trading-pm**. The fleet `GH_PAT` (loaded by
  `load-gh-token.sh`; Secret Manager `github-token`) was **verified** to register runners (JIT `generate-jitconfig`
  returned ok=true 2026-07-15). Prefer the Secret-Manager path (`GH_TOKEN_SECRET`) so no PAT sits on disk.
- Runner pinned **v2.335.1** + sha256 `4ef2f25285f0…` (in `setup-glue-runners.sh`). Then flip ONE canary
  (`branch-health`) → verify green → phased groups.

### Implementation specifics (so A1/A2/A5/2b aren't rediscovered)

- **A2 dedup** keys off fingerprints `ci_status_store.py` **already stores** — `sit_validated_tree` /
  `sit_validated_workspace_digest`; skip ONLY on an exact match to a GREEN record.
- **A1 regex** = `\.(md|mdc|rst|txt|svg|png|jpe?g|gif|ico)$` (from `base-service.sh:596`); extend the committed-diff
  check at `python-quality-gates-v2.yml` L170-202 / L585-607; `plans/**`+`codex/**` IN, lockfiles/YAML OUT.
- **A2 dead cache** at `python-quality-gates-v2.yml:90-137` (probe) + `:647-653` (`if:false` save), hardcoded
  `cache-hit=false` at L124.
- **STEP 2b trim** — `ci-status-update.yml` does `google-github-actions/auth` (~L82) + runtime
  `pip install google-cloud-firestore` (~L104) + `python3 scripts/cicd/ci_status_store.py …` (~L117). Trim: pre-install
  the lib in the `ubuntu` runner's python env, drop the auth step (VM ADC), shallow `git fetch` not a fresh checkout.
- **Re-measure (VERIFY)**: token via
  `gcloud secrets versions access latest --secret=github-billing-token --project=central-element-323112`;
  `curl …/users/IggyIkenna/settings/billing/usage?year=&month=`; per-workflow via
  `/repos/…/actions/workflows/{id}/runs?created=>DATE` `total_count` × billable-jobs (the timing endpoint returns 0 on
  this account — use the proxy). GitHub purges run history at ~90 days.

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

- [x] ✅ [MEASURE] P1. Pull the **full 4-month (Apr–Jul 2026)** billed attribution + a 30-day per-workflow breakdown —
      DONE 2026-07-15. Results written to the companion doc §"Audit results — April–July 2026" (fleet monthly totals,
      per-repo 4-mo matrix, PM per-workflow + per-cluster). Key: fleet ~$1,000/mo steady-state (Jun peak $1,441, Apr
      ~$0
      pre-machinery); PM $808/4mo = 39% (share climbing to 47.7% in Jul); PM clusters ci-status-update 32% /
      promotion-health-bots 28% / quality-gates-v2 20% / agent-plan bots 13.5% / routers 5% (router **corrected DOWN**
      from the 13.5h sample's ~20%).
- [x] ✅ [MEASURE] P1. Confirm fleet-wide **zero self-hosted runners** + baseline — DONE 2026-07-15: `actions/runners`
      total_count = 0; rate $0.006/min; baseline = ~$1,000/mo fleet / ~$480–510/mo PM (the number the fixes are measured
      against). Evidence in the companion doc §"Audit results".

### Phase 1 — Self-host the switchboard + cron glue (biggest win, ~70% of PM)

- [x] ✅ [OPERATOR-DECISION] P1. **Runner host DECIDED (operator 2026-07-15): the planning-VM** (central orchestrator,
      `i-0c9b283b31d6b5ca7`, m8i.2xlarge 8vCPU/32GB). Capacity verified: glue ~1.7 cores avg vs ~7 idle; fits with a CPU
      cap. See companion doc §"Capacity assessment".
- [x] ✅ [INFRA] P1. **Runner infra files AUTHORED 2026-07-15** (created locally, NOT yet deployed) —
      `scripts/self-hosted-runners/`: `setup-glue-runners.sh` (install/status/teardown/prune), `glue-runner-run.sh`
      (JIT-ephemeral wrapper), `github-glue-runner@.service` + `.slice` (CPUQuota≤400% / MemoryMax 8G to protect AO),
      `classify-glue-workflows.sh`, `README.md` (runbook). Runner pinned **v2.335.1** + sha256; PAT can register (JIT
      verified); all glue is in PM so **repo-scoped runners**, no per-repo fan-out. shellcheck-clean. **Deploy step
      pending operator go** (run `setup-glue-runners.sh install` on the VM with an admin PAT).
- [ ] [REVIEW] P1. **Security gate:** the `classify-glue-workflows.sh` split is **46 MOVE / 10 KEEP** — KEEP =
      `quality-gates-v2` + `python-quality-gates-v2` + 2 `pull_request` bots, **`KEEP*` builders**
      `build-smoke-all-repos`/`publish-package`, and **`KEEP-T` fleet templates** `main-backmerge-to-ldr` /
      `semver-agent` / `major-bump-issue-handler` / `request-major-bump` (see pre-flight §). Confirm the MOVE set
      carries no untrusted fork-PR code (private repo → none) before flipping.
- [ ] [INFRA] P1. **STEP 2 — flip `runs-on`** on the **46 MOVE (PM-local direct) workflows only** (`ubuntu-latest` →
      `[self-hosted, glue]`), editing PM's `.github/workflows/*.yml` **directly** (these are NOT templated — do NOT
      touch `scripts/workflow-templates/`; the `KEEP-T` templates stay hosted). **Pace = canary → phased groups
      (operator 2026-07-15):** flip ONE low-risk workflow first (`branch-health` or `reconcile-release-tags`), confirm a
      green self-hosted run, then roll the remaining ~45 out in **small batches** (not all at once). (Takes effect on
      push — do NOT push until the runners are live on the VM, else those workflows queue with no runner.)
- [ ] [INFRA] P2. **STEP 2b — `ci-status-update` warm-VM trim (do it PROPERLY, operator 2026-07-15).** A plain `runs-on`
      flip keeps the job's pointless per-run setup (fresh `actions/checkout` into `_work`, `google-github-actions/auth`,
      runtime `pip install google-cloud-firestore`) — ~15s on a warm VM for a 1-row write. Trim it so it uses the VM's
      warm state: **(1)** pre-install `google-cloud-firestore` in the runner's Python env; **(2)** drop the `auth` step
      — the Firestore client picks up the VM's ADC; **(3)** reuse a warm checkout (shallow `git fetch` on the existing
      clone, not a fresh clone). Result: `fetch + write` ≈ **~2-5s, near-zero boot churn**. Guard the trimmed steps to
      self-hosted only (they'd fail on GitHub-hosted). Highest-frequency workflow (~13k/mo) so the trim matters most
      here; apply the same pattern to any other high-freq mover that does redundant setup.
- [ ] [VERIFY] P1. After 3–5 days, re-measure PM's billed minutes (ledger); confirm the moved workflows bill ~$0 and the
      VM absorbed the load without contention (slice `MemoryCurrent` < 8G, orchestrator load unaffected).

### Phase 2 — Shrink the fleet-wide hosted QG (the real $ that stays on GitHub-hosted: A1 + A2 + A5)

> These three touch the shared reusable `python-quality-gates-v2.yml` (44 callers, all ~25 repos) → fleet-wide savings.
> QG is the ADR-sensitive gate — no coverage loss, green-only guards.

- [ ] [INFRA] P1. **A1 — docs-only fast-path (operator: do it).** Extend the committed-diff check
      (`python-quality-gates-v2.yml` L170-202 / L585-607) to the `base-service.sh:596` docs regex so a pure
      docs/plans/codex change skips the ~12-min pytest+typecheck legs (keep lint-codex). Scope: `plans/**`+`codex/**`
      IN, lockfiles/workflow-YAML OUT. Also gate `dispatch-cloud-build` on `docs_only!='true'`.
- [ ] [INFRA] P1. **A2 — FIX the content-gate dedup properly (operator: fix now).** Rebuild the byte-identical-tree skip
      on the **Firestore tree-fingerprints** (replace the broken `actions/cache` at L90-137 / L647-653). **Correctness
      guard: skip ONLY when that exact tree previously passed GREEN** (never off a failed/unknown run); relies on QG
      determinism. Fleet-wide (does NOT touch SIT; never skips a changed tree).
- [ ] [INFRA] P2. **A5 — collapse the fan-out (operator: measure-then-collapse).** Confirm the merged
      `typecheck`+`lint-codex` leg stays under the pytest leg on the slowest repo, then merge + fold the sub-minute jobs
      (content-sentinel/Slack/dispatch). Target ~30–40% fewer billed job-minutes/run, no coverage loss.
- [ ] [VERIFY] P2. Re-measure a representative QG run's billed job-minutes + the docs-PR / identical-tree skip rates
      before/after (ledger + run counts).

### Phase 3 — Cadence + de-duplication (cheap wins)

- [x] ✅ [OPERATOR-DECISION] P2. **Promote bots — KEEP BOTH (operator 2026-07-15; "retire duplicate" WITHDRAWN).**
      Re-inspection: `ldr-to-main-promote` is **PM-only** and `ldr-to-main-promote-fleet` serves the **23 `ldr_main`
      repos** (PM excluded, `promotion_model` unset) — disjoint scopes, complementary, NOT duplicates. Optional future
      consolidation only (moot once self-hosted at $0).
- [ ] [INFRA] P2. Slow promotion/health crons from `*/15` toward **hourly** (or purely event-driven off the promotion PR
      event) during freeze; keep the event path for real-time needs. Lower priority once these are on self-hosted, but
      fewer idle boots is cleaner regardless.
- [ ] [INFRA] P3. **Debounce `ci-status-update`** — coalesce multiple repo reports arriving within a short window into
      one write instead of N runner boots (careful to preserve the CAS + stale-write ordering the Firestore store relies
      on).

### Phase 4 — Serverless (B2) — DROPPED (operator 2026-07-15)

- [x] ✅ [OPERATOR-DECISION] P3. **B2 DROPPED.** ci-status-update runs on the VM (B1) with its setup trimmed (STEP 2b) →
      ~2-5s at $0; the only thing serverless would add (~1s + zero boot churn) is irrelevant at the promotion crons'
      15-min read cadence. The `deployment-api` endpoint stays a cheap **fallback** to revisit ONLY if VM churn/latency
      ever bites — not planned now.

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

## Decisions — RESOLVED (operator 2026-07-15)

All closed; full ledger in the companion doc §"Decisions — MADE". In short: (1) direction approved; (2) runner host =
the shared orchestrator/planning-VM; (3) promote bots — **keep both** (not duplicates, disjoint scopes); (4) **B2
serverless DROPPED** — ci-status-update runs on the VM with its setup trimmed to use warm state; (5) cron cadence —
disable dead staging crons, **leave promotion crons at `*/15`** (they're $0 self-hosted; the SLA was deliberate).

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
- 2026-07-15 — **Superset options analysis added**:
  [`github_actions_cost_reduction_options_analysis_2026_07_15.md`](github_actions_cost_reduction_options_analysis_2026_07_15.md)
  (4 parallel investigations). This plan is the execution vehicle for the **self-host** path; the companion doc is the
  wider decision menu (self-host vs fold-into-deployment-api vs RunsOn; the no-infra GitHub-native fixes incl. two
  latent bugs; and why Cloud Build / monorepo / merge-queue were rejected). Baseline rate corrected to **$0.006/min**.
- 2026-07-15 — **Phase 1 STEP 1 cracked** (operator: B1 on the planning-VM). Authored the runner infra under
  `scripts/self-hosted-runners/` (setup/wrapper/systemd template+slice/classifier/runbook) — pinned runner v2.335.1 +
  sha256, JIT-ephemeral, repo-scoped to PM (all glue lives here), CPU-capped to protect the orchestrator, shellcheck
  clean. `classify-glue-workflows.sh` → 46 MOVE / 10 KEEP (refined 2026-07-15). Files pushed; deploy on the VM + the
  runs-on flip are the next steps, gated on operator go.
- 2026-07-15 — **Captured execution-critical context** (operator: don't lose it in compaction). Added a
  pre-flight/runbook §. Key catch: 4 MOVE workflows are FLEET TEMPLATES
  (`main-backmerge-to-ldr`/`semver-agent`/`major-bump-issue-handler`/`request-major-bump`) — flipping the template would
  hang the other ~24 repos (no runner there) and hand-editing per-repo copies is banned → they stay hosted (`KEEP-T`).
  Split corrected to **46 MOVE (PM-local direct) / 10 KEEP**; classifier now flags `KEEP-T`/`KEEP*`. Also recorded: SSM
  deploy channel + verified admin PAT, A1/A2/2b code locations, A2 Firestore fingerprint fields, and the billing re-pull
  command for VERIFY.

---
doc_type: plan
title: GitHub Actions cost reduction — full options analysis & decision record
summary: >-
  Companion decision-menu to github_actions_ci_cost_reduction_2026_07_15.md. Four parallel investigations (service
  fold-in, GitHub-native YAML levers, runner infrastructure, drastic redesigns) evaluated every realistic way to cut the
  ~$1,000/mo GitHub Actions bill. Verdict: the truly drastic options (Cloud Build as CI runner, monorepo, merge queue)
  are the WORST on savings-per-risk; the real money is in (A) no-new-infra GitHub-native fixes — two of which are latent
  BUGS already half-built and silently disabled — and (B) choosing where the fleet glue executes (self-hosted runner vs
  fold into the existing deployment-api service vs a third-party runner in our own AWS). deployment-api already has most
  building blocks. ALL DECISIONS ARE NOW CLOSED (2026-07-15/16) — this doc is the DECISION RECORD + evidence base;
  execution lives in the sibling plan, which is ACTIVE.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-api]
scope: [engineer, admin]
tags:
  [
    ci-cd,
    github-actions,
    cost,
    self-hosted-runner,
    deployment-api,
    workflows,
    spend-reduction,
    options-analysis,
    decision-record,
  ]
related:
  - /plans/active/github_actions_ci_cost_reduction_2026_07_15.md
  - /plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
  - /plans/archive/issues/github_billing_dashboard_access_2026_07_09.md
created: 2026-07-15
last_updated: 2026-07-16
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2
assigned_role: infra
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  - "operator ask 2026-07-15: thorough analysis, explore best options incl. drastic ones, write as a new doc to decide"
  - "4 parallel research agents (service-fold-in / github-native-levers / runner-infra / drastic-redesigns), 2026-07-15"
  - "live Enhanced-Billing ledger — billed rate confirmed $0.006/min (Jan-2026 cut), not $0.008"
drift_direction: advance-code
---

# GitHub Actions cost reduction — full options analysis & decision record

> **🟢 DECISION RECORD — all decisions CLOSED (2026-07-15/16).** The earlier "suggestions, not decisions" framing is
> withdrawn; see § "Decisions — MADE". This doc is the **evidence base + the record of what we chose and why** (incl.
> the options we rejected and the audit numbers). **It is NOT the execution vehicle** — every actionable item lives in
> the sibling plan [`github_actions_ci_cost_reduction_2026_07_15.md`](github_actions_ci_cost_reduction_2026_07_15.md),
> which is **ACTIVE**. `assigned_vm: NA` → never auto-dispatched. Read this for _why_; execute from the sibling.

## Corrected baseline (measured this session)

- Bill is **100% Actions Linux compute minutes**, billed at
  **$0.006/min** (confirmed from the ledger — GitHub cut the
  rate ~39% on 2026-01-01; earlier $0.008 references are
  stale). June net **$1,441**, July 1–15 net **$485** (~$1,000/mo run-rate). PM is **~48%**, ~79% of its runs are
  automation glue, ~8% its own doc commits.
- All ~25 repos are **private** (every minute billed) → **no untrusted fork PRs exist**, which makes self-hosted runners
  safe here even for PR-triggered jobs.
- **Zero self-hosted runners** fleet-wide — the cheapest lever is untapped.
- GitHub's proposed
  **$0.002/min self-hosted platform fee was postponed indefinitely** (Dec 2025) — not guaranteed gone;
  even if it returns it is ~+$250/mo
  at this volume and does not change any recommendation.

---

## Audit results — April–July 2026 (measured, replaces the 13.5h sample)

> Ran the two Phase-0 audit todos for the full 4 months (operator ask 2026-07-15). **Method:** dollar figures are exact
> from the GitHub Enhanced-Billing ledger (`settings/billing/usage`, per repo × day × SKU). Per-workflow attribution is
> a **proxy** — GitHub's per-run timing endpoint returns 0 on this account, so we distribute PM's real ledger dollars
> across workflows by `run_count × billable_jobs_per_run` (the 1-min-per-job minimum dominates, so this tracks billed
> cost well). Per-workflow counts use a 30-day window (2026-06-15→07-15; GitHub purges run history at ~90 days, so
> earlier per-workflow detail is unavailable — but the ledger dollars go back the full 4 months).

### Fleet monthly totals (net, 100% Actions Linux — no storage/packages/Copilot)

| Month             | Net $      | Gross $ | Actions Linux min | Notes                                                 |
| ----------------- | ---------- | ------- | ----------------- | ----------------------------------------------------- |
| Apr 2026          | **$2**     | $22     | 3,605             | CI/CD machinery barely on yet                         |
| May 2026          | **$146**   | $165    | 27,472            | machinery ramping                                     |
| Jun 2026          | **$1,441** | $1,541  | 256,753           | **peak / incident-heavy** (Jun 11 alone ≈ $248 fleet) |
| Jul 2026 (1–15)   | **$485**   | $518    | 86,327            | ~$1,000/mo run-rate                                   |
| **4-month total** | **$2,074** | $2,246  | 374,157           | avg $518/mo (skewed low by near-zero April)           |

**Read the trend, not the 4-mo average:** April was pre-machinery (~$0); the real steady-state is **~$1,000/mo** (June
actual, July annualized), with June inflated by an incident. Rate confirmed **$0.006/min**.

### Per-repo, 4-month (Actions Linux net $) — PM dominates and its share is climbing

| Repo                       | Apr | May | Jun | Jul | 4-mo     | %         |
| -------------------------- | --- | --- | --- | --- | -------- | --------- |
| **unified-trading-pm**     | 0   | 72  | 504 | 231 | **$808** | **39.0%** |
| features-service           | 0   | 0   | 80  | 11  | $92      | 4.4%      |
| unified-api-contracts      | 0   | 9   | 63  | 17  | $89      | 4.3%      |
| unified-trading-library    | 0   | 12  | 51  | 21  | $84      | 4.1%      |
| market-tick-data-service   | 0   | 5   | 52  | 26  | $83      | 4.0%      |
| instruments-service        | 0   | 7   | 50  | 23  | $81      | 3.9%      |
| execution-service          | 0   | 10  | 48  | 9   | $67      | 3.2%      |
| deployment-service         | 0   | 5   | 43  | 17  | $65      | 3.1%      |
| deployment-api             | 0   | 3   | 48  | 14  | $64      | 3.1%      |
| _(≈15 more service repos)_ | —   | —   | —   | —   | ~2–3% ea | —         |

PM share by month: Apr 18% · **May 49.5% · Jun 35% · Jul 47.7%**. Every _other_ repo is a near-uniform ~2–4% — that flat
tail is the per-repo CI baseline; PM is the outlier because it's the control tower. (Self-hosted runner audit: **0
registered fleet-wide** — confirmed.)

### PM per-workflow attribution (30-day window, anchored to PM's real $510 net for Jun15–Jul15)

| Workflow                          | runs/30d | jobs/run | ~$/mo | % of PM   |
| --------------------------------- | -------- | -------- | ----- | --------- |
| **ci-status-update**              | 13,022   | 2        | ~$165 | **32.4%** |
| **quality-gates-v2**              | 3,215    | 5        | ~$102 | **20.0%** |
| SIT Debounce Trigger              | 1,426    | 4        | ~$36  | 7.1%      |
| update-repo-version               | 1,142    | 3        | ~$22  | 4.3%      |
| staging-to-main                   | 1,050    | 3        | ~$20  | 3.9%      |
| cloud-build-router                | 912      | 3        | ~$17  | 3.4%      |
| Plan Health Agent                 | 2,214    | 1        | ~$14  | 2.8%      |
| Conflict Resolution Agent         | 1,037    | 2        | ~$13  | 2.6%      |
| Rules Alignment Agent             | 644      | 3        | ~$12  | 2.4%      |
| main-backmerge-to-ldr             | 1,922    | 1        | ~$12  | 2.4%      |
| branch-health                     | 465      | 4        | ~$12  | 2.3%      |
| Plan Notification & Approval Gate | 613      | 3        | ~$12  | 2.3%      |
| ldr-to-staging-promote            | 1,620    | 1        | ~$10  | 2.0%      |
| cloud-build-router-aws            | 635      | 2        | ~$8   | 1.6%      |
| _(tail: promote/reconcile/etc.)_  | —        | —        | ~$45  | ~9%       |

### PM by cluster (the shape that drives the Set B decision)

| Cluster                                 | ~$/mo | % of PM   | Where it goes under Set B                            |
| --------------------------------------- | ----- | --------- | ---------------------------------------------------- |
| **ci-status-update**                    | ~$165 | **32.4%** | → self-host (B1), trim setup steps → ~$0             |
| **promotion / health / reconcile bots** | ~$144 | **28.2%** | → self-host (B1) → ~$0 (git+PR bots stay on Actions) |
| **quality-gates-v2** (real tests)       | ~$102 | **20.0%** | Set A shrinks it (docs-skip + fan-out collapse)      |
| **agent / plan / misc bots**            | ~$69  | **13.5%** | → self-host (B1) → ~$0                               |
| **cloud-build-router(+aws)**            | ~$25  | **5.0%**  | → self-host (B1) or B2                               |

### Corrections vs the earlier 13.5h sample (why the 4-month audit mattered)

- **`cloud-build-router` is ~5%, NOT ~20%** — the small sample caught a deploy burst. It fires ~900×/30d, and the AWS
  mirror is disabled. This meaningfully **de-prioritizes A4** (merging router jobs saves ~$8–15/mo, not ~$25–30).
- **The promotion/health/reconcile-bot cluster is ~~28% (~~$144/mo)** — bigger than the earlier "~18% crons" framing,
  and spread across many bots (SIT Debounce alone is 7%, `update-repo-version` 4.3%, `staging-to-main` 3.9%). These are
  the fat middle that **self-hosting (B1) zeroes** — reinforcing B1 as the highest-value move after the Set-A bug-fixes.
- **`ci-status-update` (32%) and `quality-gates-v2` (20%) hold** as the top two — the plan's spine is unchanged.
- **~79% of PM is glue** (everything except quality-gates-v2) — consistent with the run-mix finding.

---

## Capacity assessment — planning-VM as the glue runner host (B1, operator-chosen 2026-07-15)

> Operator decision 2026-07-15: **glue → the planning-VM (central orchestrator VM) for now** (B1). This section sizes
> the CI-side load against the VM's live headroom. **Bottom line: it fits comfortably — glue is IO-bound and light; the
> VM is ~90% idle on CPU with 27 GB RAM free.**

### The host — `i-0c9b283b31d6b5ca7` (EIP 13.113.200.22, AWS Tokyo)

| Resource | Spec                                                                                          | Live usage (2026-07-15, measured via SSM) | Headroom              |
| -------- | --------------------------------------------------------------------------------------------- | ----------------------------------------- | --------------------- |
| CPU      | **8 vCPU** (m8i.2xlarge)                                                                      | load avg **0.73 / 0.84 / 0.89** (~10%)    | **~7 cores idle**     |
| RAM      | **32 GiB**                                                                                    | 4.8 GB used, 16 GB buff/cache             | **~27 GB available**  |
| Disk     | 300 GB gp3                                                                                    | 232 GB used (**80%**)                     | 59 GB free ← tightest |
| Running  | ~10 orchestrator Claude slots (`orch-agent-main` + `orch-slot-*`) — IO/network-bound, low CPU |                                           |                       |

### The glue workload (moving PM's 39 glue workflows off GitHub-hosted; QG + the health watchers + notify-slack STAY hosted)

Measured from real run timings (1,000-run/13.4h sample + 30-day counts):

- **~3,100 glue job-executions/day**, average **~47s each** — short, IO-bound (a checkout + a Python/`gcloud`/Firestore
  call), not CPU-bound.
- **Average concurrency ≈ 1.7 jobs → ~1.7 cores continuous** (~41 CPU-hours/day).
- **Peak burst ≈ 26 concurrent runs** (~40–50 job-slots momentarily) when the fleet's CI completes together — but jobs
  are seconds-long, so bursts drain in minutes.
- **RAM:** ~0.5–1.5 GB per active job → a few GB at peak.
- **Disk per runner:** a PM checkout is only **~120 MB tracked tree / ~290 MB with shallow `.git`**; 6–8 runners +
  shared tool caches ≈ **~3–5 GB** total.

### Fit verdict

|      | Glue needs (steady / peak) | VM headroom               | Verdict                                          |
| ---- | -------------------------- | ------------------------- | ------------------------------------------------ |
| CPU  | ~1.7 cores avg / bursts    | ~7 idle cores             | ✅ trivial                                       |
| RAM  | a few GB                   | ~27 GB                    | ✅ trivial                                       |
| Disk | ~3–5 GB                    | 59 GB free (but 80% used) | ✅ fits, but disk is the pre-existing watch-item |

The glue's **steady draw (~1.7 cores, a few GB RAM, ~5 GB disk) disappears into the VM's idle headroom.** It does not
meaningfully compete with the orchestrator slots (both are IO/network-bound, not CPU-bound). Key framing: these are
**background glue jobs, not developer-facing CI**, so a short queue during a burst is acceptable — we size runners for
throughput + tolerable latency, **not** zero-queue at peak.

### Sizing + guardrails

- **6–8 ephemeral runner processes**, label `glue`, systemd-managed with auto-restart. At 8 slots a worst-case ~50-job
  burst drains in ~5 min; typical bursts far less.
- **Hard-cap CPU** so a CI burst can never starve the orchestrator: systemd `CPUQuota` on the runner slice (e.g. total
  glue ≤ 400% = 4 cores), leaving ≥4 cores always free for AO. RAM cap via `MemoryMax` (e.g. 8 GB slice).
- **Ephemeral runners (`--ephemeral`) + periodic `_work` cleanup** so disk doesn't creep — disk is already at 80% (from
  AO worktrees, not the glue). Optional: online-resize the gp3 300→400 GB (~$8/mo) if the 80% becomes a standing
  concern; that's a pre-existing AO issue, not caused by this move.
- **KEEP on GitHub-hosted:** `quality-gates-v2` (pytest is CPU-bound ~12 min — moving it would actually load the VM),
  and any `pull_request`-triggered test job. Shrink QG via Set A instead. **MOVE:** the `repository_dispatch` / schedule
  / push glue (ci-status-update, cloud-build-router(+aws), promotion/health/reconcile crons, agent/plan bots).
- **Realized saving:** this zeroes GitHub cost on ~~79% of PM (~~$400/mo) → PM from ~$480–510/mo to
  ~$100/mo (QG only,
  which Set A further trims); fleet ~$1,000 → ~$550–650, before Set A's docs-skip lands across the
  other repos.

**Net: the planning-VM absorbs the entire CI-glue load with room to spare — the things to actively manage are memory
(the QG interaction below) and disk; a CPU cap protects the orchestrator.**

**B2 DROPPED (operator 2026-07-15):** `ci-status-update` runs on the VM at
$0 like the rest of the glue — no serverless
build. **Key mechanism (correcting an earlier muddled framing):** a GitHub Actions job runs the _steps the workflow YAML
lists_, in a fresh isolated `_work/` dir — it does NOT auto-reuse the host VM's state. So a **plain `runs-on` flip would
still** `actions/checkout` (fresh clone into `_work`, not the VM's `pm` clone) + `google-github-actions/auth` (ignoring
the VM's ADC) + `pip install google-cloud-firestore` (ignoring the pre-installed lib) — ~15s of pointless setup on a
warm VM. **That setup is not inherent — the YAML tells it to.** Because it's OUR long-running VM, we TRIM those steps
(see the migration todo): pre-install the lib, drop the auth step (use the VM's ADC), reuse a warm checkout
(`git fetch`, not a fresh clone) → the run is just `fetch + write Firestore` ≈ **~2-5s, $0,
near-zero boot churn**. Only a pure warm daemon/Cloud Run endpoint would shave the last couple seconds to ~1s, and the
promotion crons read this on a **15-min cadence** so that's irrelevant. So B2 is **not planned**; revisit only if
churn/latency ever bites (then a `deployment-api` endpoint is the cheap option).

### Reconciliation with the QG-offload ADR (2026-06-02) — complementary, not contradictory

`/codex/06-coding-standards/adr-qg-offload-self-hosted-runners-2026-06-02.md` (accepted, Option A) **rejected a central
self-hosted runner pool — but for the _heavy QG gate_**, because moving the authoritative pass/fail off the worker
breaks the local feedback loop (which SHA is tested; async failure-routing back to the agent). It kept heavy
`quality-gates.sh` **local on the worker VMs**, governed by `qg-host-governor.sh` (K = `floor(vCPU/4)` concurrent).

B1 here does **not** re-open that decision:

- **We move GLUE, not QG.** ci-status-update / routers / promotion bots are fire-and-forget automation — no agent blocks
  on their pass/fail, so the feedback-loop objection does not apply. `quality-gates-v2` **stays off** the self-hosted
  runners (label `glue`, distinct from the ADR's rejected `qg` pool).
- **Security patterns match the ADR:** ephemeral + single-job (JIT), private-repo-only, never on fork PRs.
- **Memory interaction (the ADR's real concern) — accounted for:** the orchestrator VM's slots ARE workers, so local QG
  bursts already land here (governor K = `floor(8/4)` = **2** concurrent × ~5.3 GB ≈ ~10 GB). Budget: ~5 GB base + ~10
  GB QG burst + the glue slice's **8 GB `MemoryMax`** ≈ **~23 GB of 32 GB** (~9 GB headroom). The 8 GB glue cap is sized
  precisely so glue + local-QG + orchestrator never exceeds RAM — this is why memory is a managed watch-item, and why
  the heavy CPU/RAM QG must NOT be added to the glue pool.

---

## The big picture: what's worth doing vs not

Four investigations converged on the same shape. **The most "drastic-sounding" ideas are the least worth doing**, and
there is unexpected free money in fixing two latent bugs. Options are grouped by decision, cheapest-and-safest first.

### OPTION SET A — GitHub-native fixes (NO new infrastructure) — do these regardless of everything else

These are pure workflow-YAML/bash edits to existing files. Two of them are **latent bugs**: machinery that was built to
save money and is silently disabled today.

| #     | Lever                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Where                                               | Est. saving                                                                     | Risk                                                                                         |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| A1 🐛 | **Docs-only fast-path is CI-blind.** `scripts/quality-gates-base/base-service.sh:580-602` already skips pytest+typecheck for docs-only changes — but it keys off the working-tree diff, which is always empty on a clean CI checkout, so it **never fires server-side**. PM is majority-docs. Extend the existing committed-diff check (`python-quality-gates-v2.yml` L170-202 / L585-607) to the same docs regex → skip the ~12-min pytest leg on every docs/plans/codex-only PR + promotion, fleet-wide. Also gate `dispatch-cloud-build` on `docs_only!='true'`.                                                                                                                                                                                                                                                                   | `python-quality-gates-v2.yml`, `base-service.sh`    | **Large** (removes the long-pole test leg from the majority-docs change stream) | Low — mirrors the already-shipped `metadata_only` fast-path                                  |
| A2 🐛 | **The redundant-rerun cache is silently disabled.** `content-gate` (`python-quality-gates-v2.yml:90-137`) was built to skip byte-identical reruns (push+PR × main+staging = up to 4×); the cache probe/save were ripped out ~2026-06-26 and hardcoded to `cache-hit=false` / `if: false`. Every QG run now pays a full job-minute for a probe that **can never hit**. Fix it, or delete the dead job.                                                                                                                                                                                                                                                                                                                                                                                                                                 | `python-quality-gates-v2.yml:90-137, 647-653`       | Medium–Large if fixed (restores 4× dedup); ~1 job-min/run if just removed       | Low to remove; Medium to properly fix (GHA cache-in-reusable-workflow is a known rough edge) |
| A3 ✅ | **SUPERSEDED 2026-07-16 by the option-C composite-action conversion — see sibling plan STEP 2c.** A3 was "fold the `persist` job into `ci-status-update`" (`ci-status-update.yml:326` → reusable `persist-cicd-event.yml`, a separate `workflow_call` job firing ~every invocation; ~13k runs × 1 job-min × $0.006 ≈ **~$78/mo standalone, NOT ~$140/mo** — and the SAME dollars as ci-status-update, so never additive to B1). The **better, fleet-wide** version the operator chose: convert `persist-cicd-event` to a **composite action** so it runs as a STEP inside each caller's own job → (a) removes the separate 1-min-minimum job for **all 22 callers**, not just ci-status-update, and (b) resolves the hosted-vs-moved straddle (each caller's persist runs on its own runner). Do this instead of the per-caller fold. | `.github/actions/persist-event/` (new) + 22 callers | **~$78/mo+ fleet-wide via STEP 2c (not additive to B1)**                        | Low                                                                                          |
| A4    | **Merge trivial jobs in `cloud-build-router`(+aws)** — `freeze-check` and `persist` are separate 1-min-minimum `workflow_call` jobs wrapping the real `route-build`; inline them as steps.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | `cloud-build-router*.yml`                           | ~$20–30/mo                                                                      | Low                                                                                          |
| A5    | **Collapse the QG job fan-out** — merge `typecheck`+`lint-codex` into one job (both finish well inside the pytest leg). Base case drops from ~5 jobs/run to ~3 (~40% job-count cut), killing per-job 1-min minimums.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `python-quality-gates-v2.yml:149-152`               | Medium, fleet-wide                                                              | Medium (verify combined leg stays under the pytest leg)                                      |
| A6    | **Kill the dead `staging-to-main` cron.** Staging is bypassed fleet-wide, yet its `*/15` cron still fires 96×/day doing real fleet API queries before finding nothing — the sibling `ldr-to-staging-promote.yml` already got exactly this fix (schedule commented out, dispatch/manual kept). Apply the proven pattern.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | `staging-to-main.yml:16-30`                         | ~$15–25/mo                                                                      | Medium (keep `repository_dispatch` escape hatch)                                             |
| A7    | **Relax leftover staging-family + backstop crons** — `reconcile-staging-versions`, `staging-conflict-ldr-main-fallback` (hourly, low-urgency), `ci-health` (`*/15`, event path is already primary — same relax precedent as `ldr-ci-monitor`).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | various                                             | Small, compounding                                                              | Low                                                                                          |
| A8    | **Runaway cap** — `qg-slices` has `timeout-minutes: 135` (~11× the ~12-min real cost). Tighten to ~30–45 to bound a hung run.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | `python-quality-gates-v2.yml:156`                   | Tail-risk insurance                                                             | Low                                                                                          |

**Already good — do NOT "fix":** `quality-gates-v2` already cancels superseded `push` runs; `ci-status-update`
deliberately has no concurrency group (Firestore CAS makes unbounded concurrency safe — a shared group previously
dropped transitions); the routers already never fire on feature branches and already have a freeze guard. Some crons
(`ldr-ci-monitor`, `reconcile-release-tags`, `cloud-build-failure-watcher`) were already throttled 2026-06-11.

### OPTION SET B — Where the fleet glue executes (the ~53% that is dispatch traffic) — CHOOSE ONE

`ci-status-update` (~33%) + `cloud-build-router`(+aws) (~20%) are the bulk. They boot a full VM to do sub-second work.
Three mutually-comparable ways to stop that — pick the target architecture:

- **B1 — Self-host GitHub runners on the existing 24/7 orchestrator VM** (the sibling plan's Phase 1). Flip
  `runs-on: ubuntu-latest` → `runs-on: [self-hosted, glue]` for the glue/cron workflows. GitHub-side cost →
  $0; marginal
  VM cost ≈ $0 (already running). **Lowest effort, no new services.** Caveat: static pool (run 3–4 runner
  processes), we own patching/capacity.

- **B2 — Fold the glue into the existing `deployment-api` service (serverless, on Cloud Run).** ⭐ **Bigger structural
  win than expected** — deployment-api **already has almost every building block**: native GCP Cloud Build trigger-run
  (`_cloud_builds_trigger.py:231`), native AWS CodeBuild start-build via keyless WIF (`_code_builds_aws.py:326`), a
  Firestore `ci_status` client (`_ci_status_firestore_store.py`, currently read-only), `GH_PAT` from Secret Manager,
  server-to-server API-key auth (`firebase_auth.py::verify_any_auth`), and it's **already a public Cloud Run service**.
  The status logic (`scripts/cicd/ci_status_store.py`) is already GHA-free and portable. The cheapest first cut:
  **redirect the `curl`/`gh api dispatches` POST that each repo's CI already sends** from GitHub's dispatch API to a new
  deployment-api endpoint — PM's runner boot for `ci-status-update` **disappears entirely** (not just moves). Then reuse
  the existing build-trigger functions for `cloud-build-router`. New work: a GitHub-webhook/HMAC endpoint (~50 lines,
  scaffolding exists) + porting the write path + making the long build/health polls background tasks with a
  crash-recovery story. Est. ~3–5 days for status, ~5–8 days for the router.

- **B3 — Third-party runner in OUR OWN AWS account (RunsOn).** Drop-in `runs-on:` swap, but runners run ephemerally
  **inside AWS account 427895769566** (code never leaves our infra — best compliance fit of the vendor options). Flat
  license (~$330/yr Starter tier, verify job-count tier) + raw AWS spot compute → plausibly **< $300/mo all-in** with
  native autoscaling and near-zero ops. Good if we want autoscaling without running our own runner fleet.

  _(Managed vendors that run on THEIR hardware — Blacksmith ~$0.004/min, BuildJet — are cheaper drop-ins but execute
  trading code on shared third-party infra; noted, not recommended for this codebase. **Avoid ARC-on-Kubernetes** — we
  don't run k8s; highest ops burden of all.)_

**B1 vs B2 vs B3 is the core architectural decision.** B1 is fastest to savings. B2 is the "proper" end-state (glue
becomes service code, not Actions plumbing) and is unusually cheap here because the plumbing already exists in
deployment-api — but it concentrates the deploy pipeline into one service (single-point-of-failure; keep the manual
`gcloud builds triggers run` escape hatch). B3 buys managed autoscaling for a small license. **DECISION (2026-07-15): B1
for everything, B2 DROPPED** — even `ci-status-update` runs on the VM, with its redundant setup steps trimmed to use the
VM's warm state (see §"Capacity assessment" → B2 DROPPED note). B2/B3 are not planned; revisit only if churn ever bites.

### OPTION SET C — Drastic redesigns we EVALUATED and do NOT recommend (with why)

| Option                                         | Verdict               | Why                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---------------------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Move CI to Cloud Build / CodeBuild**         | ❌ Not worth it       | Cloud Build `e2-highcpu-8` is **$0.0156/min** — _more expensive per minute_ than the GitHub runners you're fleeing ($0.006), and far more than free self-hosted. HIGH effort (rebuild required-checks + promoter-bot logic for 25 repos), HIGH risk (branch-protection rulesets hard-require `quality-gates-v2`/`sit-gate` contexts). The one good idea inside it — "run on compute we own" — is just B1. |
| **GitHub merge queue** instead of promote bots | ❌ Doesn't fit        | Merge queue solves many-parallel-human-PRs contention. This pipeline has **one standing bot-owned promote PR per repo** whose head is a branch ref — structurally at odds with merge queue. It also only handles the merge step, not content-discovery/provenance/SIT-fingerprint. Touches ~$0 of the actual cost drivers.                                                                                |
| **Monorepo / repo consolidation**              | ❌ Not for cost       | Fights the load-bearing no-service-deps tier rule (`/codex/04-architecture/tier-and-import-architecture.md`); every tool is per-repo (quickmerge, promoter fleet, Path-B worktrees, branch protection, secrets). Multi-month re-architecture; savings are mostly maintenance, not dollars — and the dollar driver is fixed far more cheaply by Set A + B.                                                 |
| **Hard Actions spending cap**                  | ⚠️ Caution, not a fix | A hard cap already **caused a fleet-wide CI outage on 2026-06-22** (cap exhausted → all promotion halted). Use **soft budget alerts** (email thresholds), never a hard stop.                                                                                                                                                                                                                              |

---

## Engineering notes & refinements (from the walkthrough — review these)

> Added 2026-07-15 after going over the items live. These are the "how I'd actually do it" nuances beyond the option
> tables above — read alongside each lettered item.

### Cross-cutting: Cluster A splits into UNCONDITIONAL vs B-DEPENDENT

Set A is not one bucket. **Unconditional** items (A1, A2, A5, A6, A7, A8) are worth doing no matter which Set B path we
pick. But **A3 and A4 are B-dependent** — they optimize `ci-status-update` and `cloud-build-router`, the exact workflows
Set B (B1/B2) may move OFF Actions. Polishing a workflow we are about to delete is wasted work. → **Do the unconditional
A items now; hold A3/A4 until the Set B decision.** This also means the Set B decision does not block the biggest,
safest wins.

### Per-item refinements

- **A1 (docs-only fast-path).** Biggest beneficiary is NOT feature PRs — it is the **LDR→main promotion PRs during the
  freeze**, which are almost always pure docs/plans/codex yet run the full ~12-min pytest leg for nothing. Safe by
  construction: the regex skips only when EVERY changed file is a doc extension, so any `.py`/`.yml`/lockfile in the
  diff forces the full gate. Get the scope right: `plans/**` + `codex/**` (both `.md`) IN; `uv.lock` / `requirements*` /
  workflow YAML OUT. High confidence — just do it.
- **A2 (dead rerun cache) — a cleaner fix than resurrecting `actions/cache`.** The cache broke specifically in the
  reusable-workflow / PR-dispatch context and may re-break. Better: we **already store the state to dedup** — the
  `ci_status` Firestore store records SIT-validated **tree fingerprints** (`sit_validated_tree` /
  `sit_validated_workspace_digest`). A cheap "has this exact tree already passed?" check against that is more durable
  than a GH cache blob. Cheapest interim: **delete the dead job now** (stop paying for a probe that can never hit), then
  revisit the Firestore-based dedup once the 30-day data shows how large the redundant-rerun class actually is.
- **A5 (collapse QG fan-out).** A1 already removes the expensive pytest leg from MOST PM changes, so A5's remaining
  value is mostly on the **code repos**. Merging `typecheck`+`lint-codex` is safe only if the combined leg stays under
  the pytest leg (pytest ~12 min dominates, so it should) — **measure per-repo before blanket-merging.**
- **A6/A7 (staging crons) — verified safe.** Measured 2026-07-15: **23 repos `ldr_main`, 2 unset, ZERO repos with any
  staging activity** (no locks, no queued `staging_commits`). Use the proven `ldr-to-staging-promote` pattern: comment
  the `schedule:`, keep `repository_dispatch` + `workflow_dispatch` as the escape hatch. One open thread: confirm the
  **2 unset repos** are not intended to route through staging before treating the whole staging path as dormant.
- **A8 (runaway cap).** Set a sane fleet-wide default (`timeout-minutes` ~30–45) via the workflow TEMPLATE, not
  per-repo.
- **A3/A4 (B-dependent).** Real wins (~$78/mo + ~$20–30/mo) IF those workflows stay on Actions; **$0 / moot once B1
  self-hosts them** (A3 is the same dollars as ci-status-update, not additive) — wasted if B2 moves them into
  deployment-api. Hold for the Set B decision.

### Sequencing implication

The safe order is: **(1) unconditional Set A now** (A1, A2-delete, A5, A6/A7, A8) → **(2) decide Set B** → **(3)
B-conditional work** (A3/A4 only if staying on Actions; the chosen B path otherwise). Re-measure Set A alone against the
30-day baseline before committing to how far Set B needs to go.

## Recommended sequencing — ⛔ SUPERSEDED (2026-07-16), do NOT execute from here

> This section was the pre-decision proposal. **It is superseded by the sibling plan's todos**
> ([`github_actions_ci_cost_reduction_2026_07_15.md`](github_actions_ci_cost_reduction_2026_07_15.md), now ACTIVE) —
> execute from there, not here. It is kept only as a record of the original proposal. Specifically, three items here are
> now **factually wrong** and must not be followed:
>
> - _"Choose the Set B target architecture"_ → **decided: B1** (self-host on the planning-VM); B2 dropped, B3 parked.
> - _"Execute the chosen Set B path via the workflow-template SSOT + `rollout-workflow-templates.sh`"_ → **WRONG.** The
>   flip edits PM's `.github/workflows/*.yml` **directly**; the 4 fleet **templates stay hosted (`KEEP-T`)** — flipping
>   a template would hang the other ~24 repos. Never roll this out via templates.
> - _"A3 fold-persist"_ → **superseded by option C** (convert `persist-cicd-event` to a composite action — sibling STEP
>   2c).
>
> Phase-0 measurement is **done** (see § "Audit results"); the ledger re-pull lives in the sibling's VERIFY todos.

## Decisions — MADE (operator, 2026-07-15)

All decisions are now closed. Execution follows in the sibling plan.

1. ✅ **Direction approved** — Set A + Set B = B1.
2. ✅ **Set B = B1 for everything; B2 DROPPED, B3/RunsOn parked** (self-hosted glue runners on the planning-VM; 8
   ephemeral runners, CPU/RAM-capped). Even `ci-status-update` runs on the VM — with its redundant per-run setup
   (`pip install` / `google-github-actions/auth` / fresh clone) **trimmed** so it uses the VM's warm state (~2-5s). B2
   (serverless) not planned; revisit only if churn/latency ever bites.
3. ✅ **A2 = FIX PROPERLY NOW** — rebuild the content-gate dedup on the Firestore tree-fingerprints, **fleet-wide** (it
   lives in the shared reusable `python-quality-gates-v2.yml`, called by 44 workflows across ~25 repos). **Correctness
   guard:** skip ONLY when that exact tree previously passed GREEN (never dedup off a failed/unknown run); relies on QG
   determinism (same tree → same result). Does NOT touch SIT (cross-repo integration) and never skips a changed tree.
4. ✅ **A6 + A7 = disable the staging crons** — staging-in-flight verified zero; the 2 unset repos are
   `unified-trading-pm` (Option-B main-direct, own PM-only bot) + `system-integration-tests` (test harness) — **neither
   routes through staging**. (Now a VM-load tidy-up, since these go self-hosted at $0.)
5. ✅ **Spending cap = LEAVE AS-IS** — a hard cap already exists; operator: do not touch it. (No soft-alert change
   made.)
6. ✅ **Migration pace = canary → phased groups** — flip one low-risk workflow, verify green on `[self-hosted, glue]`,
   then roll the 39 MOVE set out in small batches, not all at once (**39 MOVE / 17 KEEP** — see the sibling plan's
   §"MOVE / STAY manifest"; 52/50 → 44/12 → 40/16 → 39/17 after the 2026-07-16 review reclassified
   `image-build-validate` as a cross-repo reusable, the operator kept the 4 CI-health watchers hosted, and the final
   review caught the shared alert carrier `notify-slack` (`KEEP-D`, ~$1/mo)). Canary = `reconcile-release-tags`
   (`branch-health` is now hosted).
7. ✅ **A5 = measure per-repo, then collapse** the QG fan-out.
8. ✅ **A1 = do it** (docs-only fast-path, fleet QG). **A8 = do it** (template timeout cap). **A3/A4 = deprioritized**
   ($0 once self-hosted; VM-load micro-optimisation for later).
9. ✅ **Promote bots = keep both** — `ldr-to-main-promote` (PM-only) and `-fleet` (the 23 `ldr_main` repos) are
   complementary, NOT duplicates. Earlier "retire the duplicate" framing withdrawn.

---

# Appendix — full investigation findings (complete record, for later decisions)

Everything the four parallel investigations surfaced, captured verbatim-in-substance so no detail is lost when we
revisit this. Nothing here is approved; it is the evidence base for the § "Decisions needed" above.

## Appendix 1 — Runner-infrastructure: every option compared

Volume assumption: ~$1,000/mo ÷ $0.006/min ≈ **~86k–125k billed min/mo** fleet-wide (per-job 1-min-minimum inflates this
above raw wall-clock).

| Option                                             | $/min or model                                  | Est. monthly @ volume          | Setup                           | Ops burden                                        | Security fit (private trading code)                            | Autoscaling                       |
| -------------------------------------------------- | ----------------------------------------------- | ------------------------------ | ------------------------------- | ------------------------------------------------- | -------------------------------------------------------------- | --------------------------------- |
| Status quo (GitHub-hosted x64)                     | $0.006/min (was $0.008 pre-Jan-2026)            | ~$1,000                        | none                            | none                                              | N/A (GitHub infra)                                             | native                            |
| ARM64 GitHub-hosted (partial)                      | $0.005/min                                      | ~$625 if fully portable (rare) | low                             | low                                               | same as above                                                  | native                            |
| **Raw self-hosted on existing VM (B1)**            | GitHub side $0 (fee postponed)                  | **~$0–250** (VM only)          | low-med                         | med (patch/capacity, no autoscale)                | **Best** — never leaves our infra; fork-PR risk moot           | none (static pool)                |
| ARC on Kubernetes (GKE/EKS)                        | $0 GitHub + pod compute                         | ~$100–300                      | **high**                        | **high** (own k8s)                                | Best (our infra)                                               | good; GKE node-autoscale immature |
| terraform-aws-github-runner (community) on our AWS | $0 GitHub + EC2 spot                            | ~$50–150                       | med-high                        | med (Terraform/AMI, no vendor support)            | Best (our AWS)                                                 | good (spot fleet)                 |
| **RunsOn (B3)**                                    | flat license (~$330–3,600/yr tiered) + our spot | **~$60–300 all-in**            | **low** (1 CFN stack + relabel) | **low** (vendor-managed orchestration, our infra) | **Best of vendor options** — compute stays in our AWS          | native, ephemeral per-job         |
| Blacksmith                                         | $0.004/min x64, $0.0025 ARM, 3k free/mo         | ~$500 (x64) / ~$312 (ARM)      | lowest                          | lowest                                            | Good — SOC2 Type 2, Firecracker isolation — but on THEIR fleet | native                            |
| BuildJet                                           | ~$0.004–0.048/min, 3k free/mo                   | ~$500                          | lowest                          | lowest                                            | Unverified — check SOC2/DPA                                    | native                            |
| Depot                                              | tiered + $0.004/min overage                     | likely >$500, needs quote      | low                             | low                                               | Docker-build-focused, not ideal for general CI at this size    | native                            |
| Cirun                                              | flat SaaS + your cloud compute                  | needs quote                    | med                             | low-med                                           | Good (your cloud) but **tier caps ~20 private repos < our 25** | native                            |
| Namespace                                          | unlisted, needs quote                           | unknown                        | low                             | low                                               | Unverified                                                     | native                            |

**Runner top-2:** (1) **RunsOn** if we want managed autoscaling with code staying in our AWS; (2) **static self-hosted
on the existing VM** as the zero-new-vendor baseline. **Avoid:** DIY ARC-on-k8s (we run no k8s; highest ops), Cirun
(repo-count cap below our 25), Depot (Docker-build-optimized, overage-heavy at our volume), and assuming self-hosted
stays $0 forever (GitHub's $0.002/min self-hosted platform fee is postponed, not killed — worst case ~+$250/mo, doesn't
change the recommendation).

## Appendix 2 — B2 deployment-api fold-in: deep dive

**Why deployment-api, not agent-orchestrator:** deployment-api is a public Cloud Run service by design;
agent-orchestrator binds `127.0.0.1:8765` with no public inbound rule
(`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md:117`), so GitHub can't reach it without new
networking. deployment-api also already holds the cloud/Firestore/GH plumbing.

**Building blocks that ALREADY exist (this is why B2 is cheap here):**

| Capability                                            | Where in deployment-api                                                                                                                                   |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GCP Cloud Build trigger-run, native (no `gcloud` CLI) | `_cloud_builds_trigger.py:231` `_run_trigger_operation_sync()` → `CloudBuildClient().run_build_trigger(...)`, exposed at `POST /api/cloud-builds/trigger` |
| AWS CodeBuild start-build, keyless via GCP→AWS WIF    | `_code_builds_aws.py:326` `start_codebuild_sync()` → `boto3 start_build(...)`                                                                             |
| Firestore `ci_status` client (read-only today)        | `_ci_status_firestore_store.py` (same collection/lazy-import as the PM store)                                                                             |
| GitHub API + `GH_PAT` from Secret Manager             | `resolve_gh_token()`, read wrappers in `_repo_ci_github.py`                                                                                               |
| Server-to-server auth (X-API-Key) OR Firebase bearer  | `firebase_auth.py::verify_any_auth`                                                                                                                       |
| Public HTTPS ingress                                  | Cloud Run service `uts-shared-deployment-api` (`cloudbuild.yaml:382`)                                                                                     |

**New work required:** (1) a GitHub-webhook endpoint with `X-Hub-Signature-256` HMAC verify (~50-line pattern; neither
service has real GitHub webhook signature verification today) OR simply an API-key-guarded endpoint the caller `curl`s;
(2) port `resolve_status`/`is_stale_write`/`set_status` from `scripts/cicd/ci_status_store.py` into the (currently
read-only) `_ci_status_firestore_store.py` — mechanical, the source has zero GHA deps; (3) make the long build poll (30
min) + health poll (5 min) **background tasks** with a crash-recovery story (Cloud Run can recycle mid-poll → needs
Cloud Tasks or equivalent, not a blocking request); (4) port the bash Slack message-building to Python.

**Honest risks / blockers:** single-point-of-failure vs Actions' per-run isolation (a deployment-api bug can black out
CI-status + deploy-routing fleet-wide — needs per-repo async isolation + health checks); secrets concentration into one
Cloud Run SA; the **`manifest.json` git-commit step stays on Actions** (deployment-api has no git-push capability
today); **promotion/backmerge bots (`ldr-to-*-promote`, `main-backmerge-to-ldr`) are a separate, larger effort** — they
need full checkouts + rebase/conflict handling + `gh pr create`, which neither service has — recommend leaving them on
Actions for now; and a bootstrapping/circularity risk (the service that fixes CI ships via its own CI — keep the manual
`gcloud builds triggers run` escape hatch, which already exists).

**Effort (infra 0.8× calibrated):** ci_status write-path port + authenticated endpoint + swap 25 repos' QG-workflow
`curl` target + HMAC/API-key hardening ≈ **3–5 days**; cloud-build-router port (reuse existing trigger fns + async poll
design + Slack port, minus the git-manifest step) ≈ **5–8 days**. Promotion-bot migration: **not in this scope.**

## Appendix 3 — GitHub-native levers: full detail + cron inventory

**The two bugs, precisely:**

- **A1 (docs-only fast-path CI-blind):** `scripts/quality-gates-base/base-service.sh:580-602` (mirrored in
  `base-library.sh:305-325`, `base-ui.sh:150-165`) has an "AUTO DOCS-ONLY TIER" that skips tests+typecheck (keeps
  lint/doc-validators) when every changed file matches `\.(md|mdc|rst|txt|svg|png|jpe?g|gif|ico)$` — but it reads the
  **working-tree** diff (`git diff HEAD`), always empty on a clean CI checkout, so it never fires server-side (the code
  comment admits it: "the server v2 … always runs the FULL gate"). `python-quality-gates-v2.yml` L170-202 / L585-607
  already compute a **committed** diff (`git diff BEFORE HEAD`) but only for `chore(release)`/`chore(deps)` — generalize
  that committed-diff check to the docs regex.
- **A2 (dead rerun cache):** `content-gate` job (`python-quality-gates-v2.yml:90-137`) was built to skip byte-identical
  reruns via `actions/cache`; probe/save were removed ~2026-06-26 ("broken for PR/dispatch in reusable-workflow
  context") → hardcoded `cache-hit=false` (L124), `if: false` on save (L651). The whole 4×-dedup mechanism from
  `cicd_v2_latency_reduction_2026_06_10.md` Phase 3 currently delivers zero savings.

**A5 detail:** base scripts already partition by `QG_SLICE` (`tests`|`typecheck`|`lint-codex`,
`base-service.sh:220-268`) with zero overlap; `tests` (pytest ~715s) is the long pole; `typecheck`+`lint-codex` combined
run well inside it → matrix `[tests, typecheck+lint-codex]` drops a whole job/run.

**Full PM cron inventory (reference):** `*/5` sit-debounce-trigger (GH floors ~5min) · `*/15` ldr-to-main-promote,
ldr-to-main-promote-fleet (offset), staging-to-main, ci-health · `*/30` branch-health, cloud-build-failure-watcher
(already relaxed from _/15), reconcile-release-tags (already relaxed), freeze-deferred-build-replay · hourly
ldr-ci-monitor (already relaxed from _/30), ci-status-consolidator, reconcile-staging-versions,
staging-conflict-ldr-main-fallback · 2h fix-approval-timeout, supersede-stale-dep-update-prs · 6h digest-drift-sweep,
workspace-quickmerge-validation · daily cassette-drift-check, plan-health-agent, overnight-agent-orchestrator,
overnight-dead-man-switch, readiness-verifier, removed-symbols-workspace-sweep · weekly ruleset-drift-alert,
secret-health-check, cold-storage-cleanup, build-smoke-all-repos. (`ldr-to-staging-promote` schedule already commented
out — the precedent for A6.)

**Confirmed-good — do NOT touch:** `quality-gates-v2` push-cancel (`quality-gates-v2.yml:20-22`) is correct; the
no-concurrency-group on `ci-status-update`/`version-registry-update` is deliberate (Firestore CAS); routers already
never fire on feature branches + already freeze-guard; tool caching (`ripgrep`/`shellcheck`/`bats`/`actionlint`,
`python-quality-gates-v2.yml:218-224`) already works; only `plan-notification.yml:12` + `rules-alignment-agent.yml:14`
have `paths:` filters today (both correct).

## Appendix 4 — Must re-verify before committing to a path

_(Reference checklist, not dispatch todos — `☐` open, `✅` done.)_

- ✅ Billed rate — **confirmed $0.006/min** from the ledger this session (was assumed $0.008).
- ☐ Full **30-day** per-workflow billed-minute attribution (sibling plan Phase 0) — the 13.5h sample is directional.
- ☐ RunsOn exact tier pricing vs our **monthly job count** (not minutes) — Starter <50k jobs/mo; Growth/Scale € figures
  not fully public.
- ☐ Whether any repo is mid-flight through **staging** before disabling staging crons (A6/A7).
- ☐ BuildJet / Namespace SOC2/DPA status **if** either is ever seriously considered (not recommended).
- ☐ GitHub self-hosted **$0.002/min platform fee** status (postponed indefinitely; re-check the changelog periodically).

---

## Codex SSOTs (read before executing any item)

- `/codex/08-workflows/ci-cd-flow.md` — pipeline / promotion / branch protection
- `/codex/06-coding-standards/adr-qg-offload-self-hosted-runners-2026-06-02.md` — the QG-offload ADR (Option A: heavy QG
  stays LOCAL, rejected central `qg` pool). B1 here is complementary (moves GLUE, keeps QG off self-hosted) — see
  §"Reconciliation with the QG-offload ADR" above; **do not** add QG to the `glue` pool.
- `/codex/04-architecture/tier-and-import-architecture.md` — the no-service-deps rule (why monorepo is rejected)
- `/codex/04-architecture/runtime-deployment-topology.md` +
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — why deployment-api (public Cloud Run) is the
  fold-in host, not agent-orchestrator (:8765, no inbound rule)
- `codex/05-infrastructure/` — runner/VM conventions; workflow-template rollout
- Sibling execution plan:
  [`github_actions_ci_cost_reduction_2026_07_15.md`](github_actions_ci_cost_reduction_2026_07_15.md)

## Progress Log

- 2026-07-15 — Options analysis authored from 4 parallel investigations. Key surprises: (1) two latent money-saving bugs
  (docs-only fast-path CI-blind; content-gate cache disabled since ~2026-06-26); (2) deployment-api already holds the
  building blocks to absorb the glue as a service; (3) the drastic options (Cloud Build, monorepo, merge queue) are the
  worst on savings-per-risk — Cloud Build is priced HIGHER per minute than GitHub-hosted. Baseline rate corrected to
  $0.006/min. Awaiting operator ruling on § "Decisions needed".
- 2026-07-15 — Per operator ("write every finding in the plan, decide later"), added the **full Appendix** (runner
  comparison matrix incl. all vendors + verify-items; B2 deployment-api fold-in deep-dive with existing building blocks
  / new work / risks / effort; complete GitHub-native lever detail incl. the two bugs' exact file:line, full cron
  inventory, and the do-NOT-touch list; and a re-verify checklist). Decisions deferred by the operator — no path chosen
  yet.
- 2026-07-15 — Added **"Engineering notes & refinements"** section from the live walkthrough: the
  UNCONDITIONAL-vs-B-DEPENDENT split of Cluster A (hold A3/A4 until Set B is chosen), per-item refinements (A1 biggest
  win = freeze-time promotion PRs; A2 cleaner Firestore tree-fingerprint dedup vs resurrecting `actions/cache`; A5
  measure-per-repo; A8 template-level default), and the safe sequencing. **Verified staging-in-flight = zero** (23
  `ldr_main`, 2 unset) → decision #4 closed bar the 2-unset-repos sub-check. Still awaiting operator ruling on the
  remaining § "Decisions needed".
- 2026-07-15 — Ran the **4-month audit** (Apr–Jul) → §"Audit results"; **flipped both Phase-0 todos done** in the
  sibling plan. Ledger-exact fleet/per-repo dollars + a 30-day per-workflow proxy. Correction: `cloud-build-router` ~5%
  (not ~20%); promotion/health/reconcile bot cluster ~28%.
- 2026-07-15 — **Operator decision: Set B = B1 on the planning-VM (for now).** Added §"Capacity assessment" — measured
  the host live (m8i.2xlarge, 8 vCPU / 32 GB / 300 GB, load 0.8, 27 GB RAM free, disk 80%) vs the glue footprint (~3,100
  job-execs/day, ~1.7 cores avg, peak ~26 concurrent runs, ~5 GB disk). Verdict: **fits comfortably**; size 6–8
  ephemeral runners with a systemd CPU cap to protect the orchestrator; keep `quality-gates-v2` on GitHub-hosted; disk
  is the only watch-item. Everything LOCAL/uncommitted per operator ("no push").
- 2026-07-15 — Runner infra files pushed (PM@a8696bb48). **Reconciled with the QG-offload ADR (2026-06-02)**: found via
  grep-then-READ; it rejected a central self-hosted pool for the _heavy QG_ (feedback-loop), kept QG local. B1 here is
  complementary (moves GLUE not QG; QG stays off `glue`). Refined the capacity note — local QG bursts (governor K=2 ≈
  ~10 GB) already land on this VM, so **memory is a managed watch-item** and the 8 GB glue `MemoryMax` is sized so
  glue+QG+orchestrator ≈ ~23 GB of 32 GB. Added the ADR to Codex SSOTs. Work now continues from **slot 1** (root left to
  the AO worker).
- 2026-07-15 — **All decisions closed** (operator): B1/planning-VM; A1 do; A2 **fix properly** (fleet-wide Firestore
  tree-fingerprint dedup, green-only guard — it lives in the shared reusable QG, 44 callers); A5 measure-then-collapse;
  A6/A7 disable staging crons; A8 do; A3/A4 deprioritized; spend cap left as-is; migration = canary→phased groups;
  promote bots kept (not duplicates). Recorded in §"Decisions — MADE". Next: execute the changes.
- 2026-07-15 — **B2 DROPPED + ci-status-update handled properly** (operator). Corrected a muddled latency framing: a
  plain `runs-on` flip keeps the Actions job's per-run setup (fresh checkout / `google-github-actions/auth` / runtime
  `pip install`) even on a warm VM (~15s) because the runner executes the YAML steps in an isolated `_work` dir — the
  VM's warm state isn't auto-reused. Fix = **trim those steps** (pre-installed lib + VM ADC + reused shallow checkout) →
  ~2-5s at $0, near-zero boot churn. Added sibling STEP 2b for the trim; Phase 4 (serverless) marked DROPPED; counts
  corrected to 50 MOVE / 6 KEEP.
- 2026-07-16 — **Review pass (operator: "grill the plan").** Caught a fleet-breaker: `image-build-validate` was labeled
  MOVE but is a **cross-repo reusable called by 24 repos** — flipping it hangs their staging→main promote gate
  everywhere. Reclassified `KEEP-R`; added `KEEP-M` for `overnight-dead-man-switch` (failure-independence). **Final
  split 44 MOVE / 12 KEEP** (the classifier now emits `KEEP-R`/`KEEP-M`; explicit list in the sibling plan's §"MOVE /
  STAY manifest"). Also: corrected A3's inflated/double-counted
  ~$140/mo (it's the *same* dollars as self-hosting
  ci-status-update → $0 once moved; the standalone saving is ~$78/mo,
  and moot post-B1); added A1/A2 correctness guards (skip must still post the required check GREEN; A2 key must include
  the gate version); recorded the runner-slot isolation + long-lived-writer + ambient-creds security posture; flagged
  the 4 CI-health watchers as a deferred failure-independence follow-up. Canary caveat: dispatch-only movers
  (`ci-status-update` etc.) can't be canaried via `gh workflow run` (no `workflow_dispatch`).
- 2026-07-16 (later) — **Operator closed the two review threads.** (1) The 4 CI-health watchers (`ci-health`,
  `cloud-build-failure-watcher`, `ldr-ci-monitor`, `branch-health`) **STAY HOSTED** (`KEEP-M`, alongside
  `overnight-dead-man-switch`) — light monitors whose value is independence from our infra; GitHub-hosted is their right
  home. (2) `image-build-validate` **stays hosted** (`KEEP-R`) for now — the blocker is personal-account runner scoping
  (self-hosted runners are repo-scoped; no org pool), so serving its 24 callers would need per-repo registrations for
  ~no money; revisit only if we convert to a GitHub Org. Split → 40 MOVE / 16 KEEP; canary switched to
  `reconcile-release-tags` (branch-health now hosted).
- 2026-07-16 (final review) — **`notify-slack` → `KEEP-D`; final split 39 MOVE / 17 KEEP.** The shared alert carrier the
  `KEEP-M` monitors call must stay hosted or a VM outage would let them detect-but-not-page (a reusable's `runs-on` is
  independent of its caller). It's hosted **for the watchers, not the movers** (a mover on a down VM isn't running →
  nothing to alert; movers call the hosted carrier unchanged — GitHub runs that job on a hosted runner inside a
  self-hosted workflow). Cost **measured first** (no per-workflow billing + nested reusable → counted the alert ledger +
  billed `send-notification` jobs):
  **~$1/mo** (117 posts/30d + a small deduped-but-billed tail); two intermediate
  figures ($4/$22) were skipped-job +
  rate-limit artifacts, corrected. `persist-cicd-event` remains the one open straddle (left MOVE — secondary
  event-ledger, not the alert path).
- 2026-07-16 (final review) — **Last straddle closed: `persist-cicd-event` → option C (operator), convert to a composite
  action.** It fires on ~~every run (5 KEEP + 17 MOVE callers incl. the 13k/mo `ci-status-update`), so unlike
  `notify-slack`
  (~~$1/mo) where it runs is real money — but one reusable can't be hosted-for-KEEP and on-VM-for-movers,
  and flipping it would hang the hosted callers during a VM outage. Converting it to `.github/actions/persist-event`
  makes it run as steps inside each caller's own job → caller's runner (movers → VM/$0,
  KEEP → hosted, no hang) AND drops the separate 1-min billed job for all 22 callers. **This SUPERSEDES A3** (the
  per-caller fold) and covers the persist half of A4. Classifier tags it `MOVE-C` (convert, do NOT flip); sibling plan
  gets **STEP 2c**. **No open straddles or classification questions remain — the flip set is final at 39 MOVE (38 flip +
  1 convert) / 17 KEEP.**
- 2026-07-16 — **Flipped `status: draft` → `active` (operator: "make this plan active and start working on it").** This
  doc is now the **DECISION RECORD** (all decisions closed; the "suggestions, not decisions" banner withdrawn);
  execution lives in the sibling plan, also ACTIVE. Marked § "Recommended sequencing" **⛔ SUPERSEDED** — it was the
  pre-decision proposal and three of its items are now factually wrong (Set-B choice is decided = B1; the "roll out via
  `rollout-workflow-templates.sh`" instruction is WRONG — the flip edits PM's workflows directly and the templates STAY
  hosted; A3 is superseded by option C). Both plans keep `assigned_vm: NA` → operator-driven, never auto-dispatched.

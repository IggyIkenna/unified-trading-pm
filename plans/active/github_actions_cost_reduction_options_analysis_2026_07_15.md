---
doc_type: plan
title: GitHub Actions cost reduction — full options analysis & decision menu (DRAFT / suggestions)
summary: >-
  Companion decision-menu to github_actions_ci_cost_reduction_2026_07_15.md. Four parallel investigations (service
  fold-in, GitHub-native YAML levers, runner infrastructure, drastic redesigns) evaluated every realistic way to cut the
  ~$1,000/mo GitHub Actions bill. Verdict: the truly drastic options (Cloud Build as CI runner, monorepo, merge queue)
  are the WORST on savings-per-risk; the real money is in (A) no-new-infra GitHub-native fixes — two of which are latent
  BUGS already half-built and silently disabled — and (B) choosing where the fleet glue executes (self-hosted runner vs
  fold into the existing deployment-api service vs a third-party runner in our own AWS). deployment-api already has most
  building blocks. THESE ARE SUGGESTIONS FOR REVIEW, NOT FINAL DECISIONS.
status: draft
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
    draft,
    suggestions,
    options-analysis,
  ]
related:
  - github_actions_ci_cost_reduction_2026_07_15.md
  - cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
  - github_billing_dashboard_access_2026_07_09.md
created: 2026-07-15
last_updated: 2026-07-15
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

# GitHub Actions cost reduction — full options analysis (DRAFT)

> **⚠️ THESE ARE SUGGESTIONS, NOT FINAL DECISIONS.** `status: draft`, **human-only** (`assigned_vm: NA`) — not ingested,
> not dispatched. This is the **decision menu**: it lays out every option we evaluated so the operator can choose the
> path. The chosen path's execution items live in the sibling plan
> [`github_actions_ci_cost_reduction_2026_07_15.md`](github_actions_ci_cost_reduction_2026_07_15.md) — this doc does not
> duplicate them; it frames the wider set of choices around them. Nothing here is approved to execute.

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

## The big picture: what's worth doing vs not

Four investigations converged on the same shape. **The most "drastic-sounding" ideas are the least worth doing**, and
there is unexpected free money in fixing two latent bugs. Options are grouped by decision, cheapest-and-safest first.

### OPTION SET A — GitHub-native fixes (NO new infrastructure) — do these regardless of everything else

These are pure workflow-YAML/bash edits to existing files. Two of them are **latent bugs**: machinery that was built to
save money and is silently disabled today.

| #     | Lever                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Where                                            | Est. saving                                                                     | Risk                                                                                         |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| A1 🐛 | **Docs-only fast-path is CI-blind.** `scripts/quality-gates-base/base-service.sh:580-602` already skips pytest+typecheck for docs-only changes — but it keys off the working-tree diff, which is always empty on a clean CI checkout, so it **never fires server-side**. PM is majority-docs. Extend the existing committed-diff check (`python-quality-gates-v2.yml` L170-202 / L585-607) to the same docs regex → skip the ~12-min pytest leg on every docs/plans/codex-only PR + promotion, fleet-wide. Also gate `dispatch-cloud-build` on `docs_only!='true'`. | `python-quality-gates-v2.yml`, `base-service.sh` | **Large** (removes the long-pole test leg from the majority-docs change stream) | Low — mirrors the already-shipped `metadata_only` fast-path                                  |
| A2 🐛 | **The redundant-rerun cache is silently disabled.** `content-gate` (`python-quality-gates-v2.yml:90-137`) was built to skip byte-identical reruns (push+PR × main+staging = up to 4×); the cache probe/save were ripped out ~2026-06-26 and hardcoded to `cache-hit=false` / `if: false`. Every QG run now pays a full job-minute for a probe that **can never hit**. Fix it, or delete the dead job.                                                                                                                                                               | `python-quality-gates-v2.yml:90-137, 647-653`    | Medium–Large if fixed (restores 4× dedup); ~1 job-min/run if just removed       | Low to remove; Medium to properly fix (GHA cache-in-reusable-workflow is a known rough edge) |
| A3    | **Fold the `persist` job into `ci-status-update`.** `persist` is a separate `workflow_call` job firing ~every invocation (~576 runs/day). Folding it to a final step removes 1 job-min per run.                                                                                                                                                                                                                                                                                                                                                                     | `ci-status-update.yml:326-339`                   | **~$140/mo**                                                                    | Low                                                                                          |
| A4    | **Merge trivial jobs in `cloud-build-router`(+aws)** — `freeze-check` and `persist` are separate 1-min-minimum `workflow_call` jobs wrapping the real `route-build`; inline them as steps.                                                                                                                                                                                                                                                                                                                                                                          | `cloud-build-router*.yml`                        | ~$20–30/mo                                                                      | Low                                                                                          |
| A5    | **Collapse the QG job fan-out** — merge `typecheck`+`lint-codex` into one job (both finish well inside the pytest leg). Base case drops from ~5 jobs/run to ~3 (~40% job-count cut), killing per-job 1-min minimums.                                                                                                                                                                                                                                                                                                                                                | `python-quality-gates-v2.yml:149-152`            | Medium, fleet-wide                                                              | Medium (verify combined leg stays under the pytest leg)                                      |
| A6    | **Kill the dead `staging-to-main` cron.** Staging is bypassed fleet-wide, yet its `*/15` cron still fires 96×/day doing real fleet API queries before finding nothing — the sibling `ldr-to-staging-promote.yml` already got exactly this fix (schedule commented out, dispatch/manual kept). Apply the proven pattern.                                                                                                                                                                                                                                             | `staging-to-main.yml:16-30`                      | ~$15–25/mo                                                                      | Medium (keep `repository_dispatch` escape hatch)                                             |
| A7    | **Relax leftover staging-family + backstop crons** — `reconcile-staging-versions`, `staging-conflict-ldr-main-fallback` (hourly, low-urgency), `ci-health` (`*/15`, event path is already primary — same relax precedent as `ldr-ci-monitor`).                                                                                                                                                                                                                                                                                                                      | various                                          | Small, compounding                                                              | Low                                                                                          |
| A8    | **Runaway cap** — `qg-slices` has `timeout-minutes: 135` (~11× the ~12-min real cost). Tighten to ~30–45 to bound a hung run.                                                                                                                                                                                                                                                                                                                                                                                                                                       | `python-quality-gates-v2.yml:156`                | Tail-risk insurance                                                             | Low                                                                                          |

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
`gcloud builds triggers run` escape hatch). B3 buys managed autoscaling for a small license. They're not exclusive: B1
now, B2 for the highest-frequency `ci-status-update` later, is a sensible sequence.

### OPTION SET C — Drastic redesigns we EVALUATED and do NOT recommend (with why)

| Option                                         | Verdict               | Why                                                                                                                                                                                                                                                                                                                                                                                                       |
| ---------------------------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Move CI to Cloud Build / CodeBuild**         | ❌ Not worth it       | Cloud Build `e2-highcpu-8` is **$0.0156/min** — _more expensive per minute_ than the GitHub runners you're fleeing ($0.006), and far more than free self-hosted. HIGH effort (rebuild required-checks + promoter-bot logic for 25 repos), HIGH risk (branch-protection rulesets hard-require `quality-gates-v2`/`sit-gate` contexts). The one good idea inside it — "run on compute we own" — is just B1. |
| **GitHub merge queue** instead of promote bots | ❌ Doesn't fit        | Merge queue solves many-parallel-human-PRs contention. This pipeline has **one standing bot-owned promote PR per repo** whose head is a branch ref — structurally at odds with merge queue. It also only handles the merge step, not content-discovery/provenance/SIT-fingerprint. Touches ~$0 of the actual cost drivers.                                                                                |
| **Monorepo / repo consolidation**              | ❌ Not for cost       | Fights the load-bearing no-service-deps tier rule (`codex/04-architecture/tier-and-import-architecture.md`); every tool is per-repo (quickmerge, promoter fleet, Path-B worktrees, branch protection, secrets). Multi-month re-architecture; savings are mostly maintenance, not dollars — and the dollar driver is fixed far more cheaply by Set A + B.                                                  |
| **Hard Actions spending cap**                  | ⚠️ Caution, not a fix | A hard cap already **caused a fleet-wide CI outage on 2026-06-22** (cap exhausted → all promotion halted). Use **soft budget alerts** (email thresholds), never a hard stop.                                                                                                                                                                                                                              |

---

## Recommended sequencing (proposal — not approved)

- [ ] [MEASURE] P1. Phase 0 of the sibling plan: pull the full 30-day per-workflow attribution so every $ below is
      exact.
- [ ] [INFRA] P1. **Set A quick wins first** — they need no infra and include the two bug-fixes (A1 docs-only fast-path,
      A2 dead cache) + A3 fold-persist (~$140/mo) + A6 dead `staging-to-main` cron. Highest bang-for-buck, low risk.
- [ ] [OPERATOR-DECISION] P1. **Choose the Set B target architecture** — B1 (self-host on the VM) vs B2 (fold into
      deployment-api) vs B3 (RunsOn in our AWS). Recommendation: **B1 now** for speed, **B2 for `ci-status-update`
      next** (building blocks already exist), revisit B3 only if autoscaling contention shows up.
- [ ] [INFRA] P2. Execute the chosen Set B path via the workflow-template SSOT + `rollout-workflow-templates.sh` (never
      hand-edit per-repo copies); keep promotion/backmerge bots (git+PR ops) on Actions for now — moving those is a
      separate, larger effort.
- [ ] [INFRA] P2. Set A cleanup tail (A4, A5 job consolidation; A7 cron relax; A8 runaway cap) + turn on **soft** budget
      alerts.
- [ ] [VERIFY] P3. Re-pull the ledger 2 weeks post-rollout; compare to baseline. Target: **fleet
      ~$1,000/mo →
      ~$250–400/mo**, structurally flat as activity grows.

## Decisions needed (operator)

1. Approve the direction? (Set A + one Set B path)
2. **Set B: B1 self-host / B2 deployment-api service / B3 RunsOn?** (rec: B1 now → B2 for ci-status-update later)
3. A2: fix the content-gate cache properly, or just delete the dead job?
4. A6 + A7: confirm no repo is mid-flight through staging before disabling staging crons?
5. Confirm **no hard spending cap** (soft alerts only), given the 2026-06-22 outage?

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
(`codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md:117`), so GitHub can't reach it without new
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

- `codex/08-workflows/ci-cd-flow.md` — pipeline / promotion / branch protection
- `codex/04-architecture/tier-and-import-architecture.md` — the no-service-deps rule (why monorepo is rejected)
- `codex/04-architecture/runtime-deployment-topology.md` +
  `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — why deployment-api (public Cloud Run) is the
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

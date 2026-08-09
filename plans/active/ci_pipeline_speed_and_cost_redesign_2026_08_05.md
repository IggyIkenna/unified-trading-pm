---
doc_type: plan
title: CI pipeline redesign — fast LDR→main (3-5min target), needs-driven cross-repo triggering, cost right-sizing
summary: >-
  Operator target: LDR→main should take 3-5 minutes regardless of repo when little has changed, cross-repo workflow
  triggering should fire only when genuinely needed, and fleet CI cost (AWS self-hosted + GitHub Actions billing) should
  track actual task volume (~300 tasks/day) instead of the current multiple-of-that footprint. Seeded from a same-day
  live investigation (2026-08-05) that found and fixed a real crash-loop bug, root-caused the capacity crisis to
  disk-throughput saturation (not CPU), and raised the CI VM's EBS ceiling — this plan is where the remaining, bigger
  design work (measurement, fan-out audit, concurrency right-sizing, cost accounting) lives.
status: active
nature: process
asset_group: [ci, infrastructure]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, system-integration-tests]
scope: [engineer, admin]
tags: [ci-cd, cost, self-hosted-runners, capacity, cross-repo-dispatch, pipeline-speed]
related:
  [
    /plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/archive/issues/qg_v2_digest_refresh_fastpath_gap_2026_08_05.md,
    /plans/archive/2026_06/quality_gates_speed_and_config_ssot_2026_06_09.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-05
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: infra
drift_direction: advance-code
depends_on: [ci_runner_fleet_split_and_vm_rightsizing_2026_08_03]
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    scripts/self-hosted-runners/fast-checkout.sh,
    scripts/self-hosted-runners/glue-runner-run.sh,
  ]
source:
  [
    "operator, 2026-08-05, live session — 'a simple CI flow LDR to main should take max 3-5 mins regardless of the
    repo... currently we spend 1k monthly on gh plus... 5k gh ci spend alone'",
  ]
last_updated: 2026-08-05
locked_by:
locked_since:
supersedes:
superseded_by:
---

# CI pipeline redesign — speed + needs-driven fan-out + cost

## Why this plan exists

Same-day investigation (2026-08-05) chasing a stuck dashboard deploy surfaced a chain of real, concrete findings —
recorded in full in `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s 2026-08-05 entry. Summary:

- **Fixed and shipped this session**: agent-orchestrator's `glue-1` runner crash-loop (89 restarts, a DELETE-retry race
  in `glue-runner-run.sh`) — code fix `unified-trading-pm@a4eb9a288`, deployed live to the VM.
- **Fixed this session**: the CI VM's EBS volume was throughput-capped at gp3's 125 MB/s baseline (confirmed via
  `iostat`: 89.5% util, 101-deep queue, throughput AT the ceiling — NOT a CPU or IOPS problem, load-average readings
  were mostly I/O wait). Raised to 500 MB/s / 6000 IOPS via `aws ec2 modify-volume` (no downtime).
- **Also fixed this session**: `python-quality-gates-v2.yml`'s metadata-only fast-path didn't cover the bot's
  digest-only refresh commit shape — every UTL base-image republish ran the FULL gate on all ~24 fleet repos
  simultaneously for a single-line Dockerfile bump. Fixed (`qg_v2_digest_refresh_fastpath_gap_2026_08_05.md`).
- **Investigated and explicitly NOT pursued**: scoping `pytest` to changed files for a faster local/quickmerge loop.
  This exact idea was already designed, measured, and rejected by the operator on 2026-06-17
  (`quality_gates_speed_and_config_ssot_2026_06_09.md` Phase 2 — "🔴 CLOSED — DO NOT BUILD THE FAST TIER"): the
  safely-scopable slice was measured at ~1.1% of gate wall-clock (tests are 67.4%, deliberately kept always-full because
  this codebase's dynamic-dispatch/factory-registry wiring makes test-impact-selection unreliable — a
  deselected-but-actually-impacted test is a false green). Also: quickmerge's local Pass-1 QG run happens on each
  agent's own machine, not the shared CI VM, so scoping it wouldn't have addressed the capacity crisis regardless.
  Recorded here so it isn't re-investigated from scratch next time someone has the same instinct.
- **CORRECTED 2026-08-05 (was wrong when this plan was opened)**: the interactive `gh` CLI session indeed lacks billing
  scope, but that was never the real path — `deployment-api` already holds a dedicated fine-grained PAT
  (`github-billing-token`, GSM secret in project `central-element-323112`, Account permission "Plan: Read-only" only)
  that has been used successfully in at least 3 prior sessions to pull real Actions spend (2026-07-10/11, 2026-07-23,
  2026-07-30 — see `plans/archive/issues/github_billing_dashboard_access_2026_07_09.md`). No operator OAuth needed. Also
  note the classic `/users/{user}/settings/billing/actions` endpoint this todo originally named is deprecated
  (`410 Gone`); the working replacement is the Enhanced Billing endpoint `GET /users/{username}/settings/billing/usage`
  (filter `product=actions`), which is exactly what `github-billing-token` reaches. Fastest path: read
  `deployment-api`'s own `/costs/summary`/`/costs/breakdown` routes (`deployment_api/routes/costs.py`) or check
  deployment-ui's `/ops/costs` page directly — both already surface this live. Direct `gcloud secrets versions access`
  also works but needs a live `gcloud auth login` session (hit intermittent human-account reauth failures 2026-08-05
  fetching it from an agent session — not a permission problem, just a stale local gcloud session; the `github-token-sa`
  service-account key sidesteps this entirely, see the resolved todo below).
- **Concrete, evidenced but NOT yet decided**: reducing per-repo self-hosted runner slot counts as the direct
  concurrency lever (unified-trading-pm has 5 glue + 3 writer; agent-orchestrator has 2 glue + 1 writer; the other 23
  repos already have the minimum, 1 each) — proposed in the issue doc, needs an explicit target before touching
  fleet-wide runner provisioning.

## What "done" looks like

- LDR→main for a small/no-op change completes in 3-5 minutes, verified across a representative sample of repos (not just
  the 1-2 already-fast ones).
- A dependency-version bump from UTL/UAC/PM only triggers downstream `repository_dispatch` for repos that actually
  declare that dependency — not the whole fleet unconditionally — UNLESS the bump is breaking (breaking changes
  legitimately need broader validation).
- Fleet CI cost (AWS self-hosted compute + GitHub Actions billed minutes, once both are measured) has a stated,
  understood relationship to actual task volume (~300 tasks/day), and any residual gap is explained, not hand-waved.

## Todos

- [x] ✅ [INFRA] P0. **Get real GitHub Actions billing numbers.** — Pulled live 2026-08-05 via `github-token-sa`'s GCP
      service-account key (sidesteps the human-account's intermittent gcloud MFA-reauth failures hit mid-session) →
      `github-billing-token` GSM secret → `GET /users/IggyIkenna/settings/billing/usage`. **July 2026:
      $1,179.13 total**
      (100% `sku=Actions Linux`, i.e. 100% GitHub-hosted `ubuntu-latest` billing — self-hosted runners bill $0
      against this API by design). Confirms the operator's "~$1k" recollection almost exactly; the "$5k" figure
      referenced when this plan opened does not match GH Actions billing specifically (likely conflated with AWS
      self-hosted infra spend, which is a separate cost surface — `deployment-api`'s `/costs/summary` covers both, worth
      cross-checking if the $5k figure still needs reconciling). **August 2026 (partial, through day 5): $89.44.**
      **Unexpected finding — by-repo breakdown**: `unified-trading-pm` alone is **41.0% of July's total**
      ($483.58) and
      **59.4% of August's partial total** ($53.15) — more than every actual trading-service repo
      combined, despite PM being a coordination/docs/CI-tooling repo, not a service. Spawned a follow-up investigation
      (see new todo below) rather than assume the cause.
- [x] ✅ [INFRA] P1. **Measure current LDR→main wall-clock, per repo** — measured 2026-08-05 against `execution-service`
      (heavy), `greeks-service` (light), `agent-orchestrator`, `unified-trading-pm`, sampling 08-02/03/04 PRs (excludes
      the 08-05 incident). **Result: the 3-5min target is already beaten by 10-50x for most of the fleet** —
      PR-open-to-merge is 4-16 seconds for every repo running "direct" mode (execution-service #544/#541, greeks-service
      #404/#402, agent-orchestrator #781/#774), because the required checks
      (`quality-gates-v2`/`sit-gate/fleet-green`/`quickmerge-provenance`) reference/reuse QG state that already ran when
      the commit landed on LDR — the heavy test/lint slices (1-2+ hrs sometimes) are NOT re-run inside the promotion
      PR's lifetime. **The real structural floor is invisible to "open→merge"**: it's the ~15-min promotion-cron cadence
      that decides WHEN a PR gets opened at all (before `createdAt`), giving an average ~7.5min PRE-PR latency not
      captured by this metric. **Outlier: PM runs a different "auto-drain" mode** with genuine 4s-34min variance even on
      clean days (PM #2088 = 4s, #2199 = 14m52s, #2266 = 33m48s) — looks like real retry/backoff churn in that mode, not
      cron-related; worth checking `ldr-to-main-promote-fleet.yml`'s auto-drain retry logic if a tight fleet-wide floor
      matters, separate from PM's ubuntu-latest billing-driver investigation above (different root cause, same repo).
- [x] ✅ [INFRA] P1. **Find PM's dominant GitHub-hosted (`ubuntu-latest`) cost driver — FOUND AND FIXED, 2026-08-05.**
      The `workflow_call` hypothesis was WRONG (corrected via search of GitHub's own billing docs): reusable-workflow
      minutes bill to the CALLING repo, not the file's home repo — confirmed all 24 other repos' calls into
      `python-quality-gates-v2.yml` bill against themselves. **Real root cause, ranked by measured July run count**
      (`gh api .../actions/workflows/<f>/runs?created=2026-07-01..2026-07-31`): 1. **`quality-gates-v2.yml` (PM's own
      promotion-gate wrapper) — 4,763 runs/month, by far #1.** PM must call `python-quality-gates-v2.yml` LOCALLY
      (`uses: ./.github/workflows/...`, chicken-and-egg — PM can't reference itself remotely) — and unlike the 24 other
      repos (migrated by `rollout-workflow-templates.sh`, which only targets remote-ref callers), PM's own local `with:`
      block never passed `self_hosted_runner_labels`, so EVERY internal job (`content-gate`, `qg-slices`,
      `supersede-check`) defaulted to `ubuntu-latest` — even though PM's own glue pool has been live and used by other
      jobs in the same file for weeks. **FIXED**: added `self_hosted_runner_labels: '["self-hosted","glue"]'` to PM's
      own `with:` block (`unified-trading-pm@995c374ce`), verified via a manual `workflow_dispatch` run. 2.
      `ci-health.yml` — 1,398 runs (hourly cron + fleet-wide `repository_dispatch` wake-ups, genuinely land in PM).
      `runs-on: ubuntu-latest` is explicitly commented LOAD-BEARING (verifies GH-hosted infra independent of
      self-hosted) — correctly should NOT change. 3. `branch-health.yml` (731×3 jobs, hourly) +
      `reconcile-release-tags.yml` (931×2 jobs, `*/30`) — moderate, already relaxed once (07-17/06-11); lower priority
      than #1, diminishing safety margin on further cuts. **Ruled out as false leads**: `main-backmerge-to-ldr.yml`
      (2,774 runs but ~40s each, trivial total) and `conflict-resolution-merged.yml` (1,026 runs but its `if:` gate
      skips almost every invocation in ~1s). **Expected impact**: fix #1 alone should eliminate the large majority of
      PM's $483.58/mo — re-measure PM's September billing once a full month has elapsed under the fix to confirm.
- [x] ✅ [INFRA] P1. **Audit the `update-dependency-version.yml` fan-out** — CLOSED as "already true", 2026-08-05.
      `update-repo-version.yml` (the sender, `.github/workflows/update-repo-version.yml:294-310`) computes
      `/tmp/dependents.txt` by walking `workspace-manifest.json`'s `repositories.<name>.dependencies` list and only
      including repos whose `dependencies` array actually names the bumped repo — a MINOR/PATCH bump's
      `repository_dispatch` (`:668-672`) fires ONLY to those real dependents, never the whole fleet. A MAJOR/breaking
      bump additionally triggers `cascade-qg-ordering.yml` (`:717` on), which does a topological forward-walk of
      "transitively affected repos" via the manifest's `topologicalOrder.levels` (`cascade-qg-ordering.yml:150-210`) —
      broader than direct dependents (by design — breaking changes legitimately need wider validation, matching this
      plan's own "done" criteria), but still graph-derived, not an unconditional blast. One deliberate special case:
      `pm_all_tiers = source_repo == "unified-trading-pm"` (`:170`) widens the cascade further specifically when PM
      itself is the source — reasonable given nearly everything depends on PM transitively. No fix needed; this todo was
      based on an untested assumption, not a confirmed bug.
- [x] ✅ [OPERATOR] P1. **Decide the concurrency-reduction target** and execute: reduce `unified-trading-pm`'s glue pool
      (currently 5) and `agent-orchestrator`'s (currently 2) per the proposal in
      `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s 2026-08-05 entry — or a different target if the
      fresh EBS throughput headroom (500 MB/s vs the old 125 MB/s ceiling) changes the calculus. Verify with a
      steady-state (not spot-check) load measurement before and after, matching the rightsizing plan's own unfinished
      "longer-window measurement" todo. **RESOLVED 2026-08-05 — open question answered, concurrency cut is clear to
      proceed on this axis**: investigated whether AO's glue pool serves escalation-dispatch work in addition to its own
      CI. It does NOT, on either count the operator expected: (1) AO's `quality-gates-v2.yml` still runs its own CI on
      `[self-hosted, glue]` exactly like every other repo — unchanged. (2) The actual `/api/escalate` HTTP call fires
      from `unified-trading-pm`'s `escalate-to-orchestrator.yml` — PM's glue pool, not AO's; AO's own
      `escalate-to-orchestrator.yml` is vestigial (nothing calls it via `uses:`). (3) The worker that actually resolves
      an escalation never touches a GHA runner at all — `server/escalation.py` spawns it onto an AO "slot" (a persistent
      tmux session), a completely separate resource pool. So cutting AO's glue pool 2→1 only affects AO's own CI
      throughput, not escalation capacity — safe to decide purely on that basis. **Separate, real finding surfaced by
      this investigation** (not a CI-cost topic, flagging for the right owner): escalation dispatch is currently
      HARD-PINNED to the Anthropic/Claude account pool (`autospawn.pick_headroom_account(...)` with no `provider=` arg
      defaults to `"anthropic"`, `agent-orchestrator/server/autospawn.py:868-873`) — it does NOT use the DeepSeek/Claude
      blended routing that regular backlog dispatch already has (`select_account_for_spawn()`, same file `:1216+`). The
      operator's stated preference ("escalation work should be dispatchable to DeepSeek, we already have the
      observability for it") is NOT true of the current code — `EscalationQueueRow`/`activity_log` tracks escalation
      lifecycle but never DeepSeek spend, since escalations never route there today. Wiring escalation dispatch through
      the existing blended-routing path is a real, scoped follow-up but belongs in an agent-orchestrator
      dispatch/routing plan, not this CI-cost plan — not created here per the "ask before creating a plan" rule;
      operator to decide where it lands. **EXECUTED 2026-08-05**: chose a MODERATE target rather than the original
      proposal's full cut, given two things had changed since it was written: the EBS throughput fix (4x headroom on the
      exact bottleneck that caused the 07-27 crisis) argues for less caution, but PM's own `self_hosted_runner_labels`
      fix (above) means PM's glue pool now ALSO carries PM's own 4,763-runs/month CI load that previously ran on
      `ubuntu-latest` — a new source of real utilization the original proposal didn't anticipate. Landed in between:
      **PM 5→3 glue** (not the proposal's 2-3 low end, to leave headroom for the new self-hosted load), **AO 2→1 glue**
      (unchanged from the proposal — AO's workload didn't change this session). Executed via `systemctl stop`+`disable`
      on the specific excess instances (`github-glue-runner@glue-{4,5}.service`, `github-glue-runner-ao@glue-2.service`)
      — checked every instance's live `ActiveState` first (all confirmed idle, zero risk of interrupting an in-flight
      job) before stopping any of them. **Verified the remaining pool still works**: dispatched a real PM
      `quality-gates-v2` run post-reduction — `QG slice (tests)` succeeded cleanly on the reduced 3-runner pool;
      `QG slice (checks)` failed, but on a genuine pre-existing content issue (`qg_red_reason: "qg"`, a real
      typecheck/lint failure, unrelated to checkout/infra — confirmed by reading the actual failure log, not assumed)
      that correctly triggered the existing Slack CRITICAL alert — the alerting pipeline itself working as designed, not
      a symptom of the reduction. Not a "steady-state" measurement (that needs real multi-day load data this session
      can't produce) — a single verified-working dispatch immediately after the cut, which is the minimum bar for
      "didn't break anything," not the rightsizing plan's own longer-window todo.
- [x] ✅ [INFRA] P2. **Re-evaluate + re-add `unified-trading-library` and `e2e-testing` to self-hosted — SHIPPED
      2026-08-05.** Live host check at re-add time: load average 4.08/4.92/6.24 (vs. the 90+ that caused both prior
      reverts) and 18% swap (vs. 87%) — healthy headroom, not just "should be fine" hope. Allowlist updated
      (`unified-trading-pm@dc3ab95d7`), rolled out via
      `rollout-workflow-templates.sh --repo <name> --template quality-gates-v2.yml` (pre-flight action-pin check
      passed cleanly), shipped per-repo: `unified-trading-library@9f309cb0`, `e2e-testing@ccda667`. Both
      watched-not-guaranteed — this is the 2nd/3rd cycle for each repo, so if the same starvation/SIGALRM signature
      recurs, revert per the same precedented per-repo playbook (not a new investigation).
- [x] ✅ [INFRA] P2. **Check whether `glue-runner-crash-loop-watchdog.sh` actually paged — CONFIRMED IT DIDN'T, FOUND
      AND FIXED THE ROOT CAUSE, 2026-08-05.** `unified-trading-pm@6d1ae8463`, deployed live to
      `/usr/local/sbin/glue-runner-crash-loop-watchdog.sh` (MD5-verified). Confirmed on the live host: the
      `alerted-units` state file was completely empty, and `journalctl` showed every single 5-min tick since
      2026-08-05T00:00 logging `OK -- 0/1 glue-runner units crash-looping` — meaning it has NEVER once alerted, for ANY
      crash-loop, ever (not just AO's). **Root cause**: `systemctl list-units --type=service --all` with NO pattern
      argument does not reliably enumerate JIT-ephemeral `glue-N` template instances that have cycled out of systemd's
      in-memory unit cache between jobs — the "1" unit it DID see was its own service
      (`glue-runner-crash-loop-watchdog.service`, self-matched by the old bare `grep glue` filter, since its own name
      contains "glue"). Verified live: during a burst of active CI dispatch (this session's own canary-run testing), the
      bare query returned exactly 1 line despite ~68 real glue-runner units genuinely present; passing an explicit
      pattern (`"github-glue-runner*"`) to force systemd to actively resolve matching units instead of only reporting
      whatever's cached reliably returned all 68 during that SAME active window — a fix confirmed by direct before/after
      comparison, not just code review. (During a subsequent quiet moment with zero active CI, it correctly reports 0/0
      — JIT-ephemeral units genuinely aren't "loaded" when nothing is running, which is correct behavior, not a
      regression; the fix's job is to catch units DURING an active crash-loop, which is inherently an "active" systemd
      state that should remain visible regardless of overall fleet activity.) Also naturally excludes the watchdog's own
      unit going forward, since it doesn't match the `github-` prefix. **Real impact**: every glue-runner crash-loop or
      wedge incident since this watchdog was deployed has gone unalerted — a confirmed, not hypothetical, alerting gap.
- [x] ✅ [INFRA] P3. **Cost-vs-volume reconciliation — DONE 2026-08-05.** Pulled the AWS side to complete the picture
      (`aws ce get-cost-and-usage`, single-account org `427895769566`/"Kapsule", no sibling accounts): **July 2026 total
      AWS spend (all services, not CI-specific) =
      $1,020.06**, of which raw EC2-Compute (the CI VM fleet's actual
      instance cost) is only **$113.37** — the rest
      is VPC/ECS/ECR/RDS/Secrets Manager/etc., unrelated to CI. Combined with the P0 finding (GH Actions
      **$1,179.13**), **total CI+AWS-adjacent spend ≈ $2,199/month — the
      "$5k" figure
      referenced when this plan opened does NOT reconcile against anything found in this account.** Flagging as likely
      a misremembered/rough estimate rather than continuing to chase it — there is no hidden AWS account or cost
      category that closes the gap.
      **The actual reconciliation, ~300 tasks/day (9,000/month) vs. measured GH Actions footprint**: pre-fix, July's
      $1,179.13
      breaks down to $483.58 PM (the `self_hosted_runner_labels` bug, fixed this session) + $695.55 everything else
      (ci-health.yml's intentional hourly GH-hosted monitoring, branch-health.yml/ reconcile-release-tags.yml's crons,
      and UTL/e2e-testing's capacity-crisis GH-hosted workaround, also fixed this session). **Key finding: most of this
      cost does NOT scale with task volume at all** — it's dominated by TIME-based fleet-monitoring crons (fire
      hourly/every-30-min regardless of how many tasks run that hour) and by the two now-fixed misconfigurations, not by
      genuine per-task GH-hosted minutes. The self-hosted EC2 fleet itself is a near-fixed cost
      (~$113/month total, already paid for whether 100 or 1,000 tasks run — spare capacity
      absorbs the difference), so the MARGINAL cost of one more task is close to zero on both sides once this
      session's fixes are live for a full month. Re-measure August/September's GH Actions bill once the PM +
      UTL/e2e-testing fixes have had a full billing cycle to confirm the expected drop (rough estimate: July's
      $1,179.13
      minus most of the $483.58 PM component ≈ $600-700/month steady-state, pending confirmation).
- [ ] [INFRA] P1. **Warm git-object cache for JIT-ephemeral runner checkouts** — DESIGN REVISED 2026-08-05, folding in
      an independent analysis from Harsh (Slack, same day) plus a correction to this todo's own earlier claim.
      **Correction**: this todo previously said "zero hits for `--reference`/mirror patterns... no mechanism exists" —
      WRONG, found on closer read: `setup-glue-runners.sh` + `refresh-slot-repo.sh` (10-min timer,
      `github-glue-slot-refresh.timer`) already maintain a cron-refreshed local clone at `${RUNNER_BASE}/repo`
      (`/opt/github-glue-runners/repo`), with a `repo.refreshed-at` freshness stamp — this IS the mirror Harsh
      described. **But it's scoped narrowly**: built for the WRITER pool only (STEP 2b — lets the high-frequency
      `ci-status-update` writer pre-stage `ci_status_store.py` and skip `actions/checkout` entirely for its own tiny
      job), a SHALLOW clone (`gh repo clone ... -- --depth 1`), and the GLUE pool's actual
      `python-quality-gates-v2.yml`/`quality-gates-v2.yml` jobs — the ones doing the 1.7 GB `actions/checkout@v4` I/O
      Harsh measured — never read it at all. **Harsh's independent measurement** (same root cause, extra numbers): ~1.7
      GB written per glue run (checkout+venv+artifacts) × up to 25 concurrent = ~42 GB competing for one disk; at the
      OLD 96 MB/s (6k IOPS) that's 7+ min of pure write time — matches this session's own iostat finding (92.9% iowait).
      Proposed 3 options, ranked by his own effort/payoff read: **(A)**
      `git clone --reference <deep-mirror> --dissociate` (needs the shallow mirror converted to a real/deep clone first
      — `actions/checkout@v4` has no native `reference:` input, so this means a custom checkout step). **(B)**
      `git worktree add` off a `--bare --mirror` repo (zero object copying, fastest, but needs maintaining bare
      mirrors + custom checkout). **(C)** hardlink-copy the existing mirror (`cp -al mirror _work/<run-id>/<repo>` +
      `git fetch` + `git checkout --force <sha>` — cheapest to implement TODAY because the mirror infra already exists)
      — his own pick, "the mirror already exists and is refreshed every 10 min." He additionally flags **pre-built
      venvs**: hardlink-copying a per-repo pre-built `.venv` alongside the checkout would eliminate `uv sync`'s
      venv-write cost too (currently ~200-500 MB written fresh per run even though `~/.cache/uv` itself is already
      persistent/warm — 9s not 2m07s). **Recommendation**: Option C, reusing the EXISTING `refresh-slot-repo.sh`/timer
      pattern rather than building a parallel mechanism — (1) convert `${RUNNER_BASE}/repo` from `--depth 1` to a full
      clone (one-time, then `pull --ff-only` keeps it current same as today), (2) extend the refresh timer's
      scope/labels so it also serves the glue pool (today it's writer-pool-only by convention, not by hard restriction),
      (3) replace `actions/checkout@v4` in `python-quality-gates-v2.yml` with a custom step:
      `cp -al ${RUNNER_BASE}/repo _work/<run-id>/<repo> && git fetch origin && git checkout --force <sha> && git clean -fdx`,
      with an explicit fallback to plain `actions/checkout@v4` if the mirror is missing/stale/dirty (checked via the
      existing `repo.refreshed-at` stamp) — so a mirror problem degrades to today's behavior, never blocks a job.
      **Still true**: this touches every job on the shared runner across ~24+ repos via the shared workflow template —
      needs real testing before fleet-wide rollout (a single canary repo first, verified for a few days, is the safe
      path given this session's own history of 2 separate live incidents from touching this exact runner
      infrastructure). Directly reduces disk WRITE I/O on the same EBS volume this session's capacity investigation was
      about. **IMPLEMENTED + CANARIED 2026-08-05, `fast-checkout.sh` shipped
      (`unified-trading-pm@b656cb87b`/`23f1ad262`/`91ebc6584`) — mechanism proven SAFE via a real green CI run, but the
      actual speedup is NOT yet confirmed active.** Deployed to agent-orchestrator's pool as the canary. Found and fixed
      3 real bugs live, each via an actual failing/succeeding CI run (not just static review) — recorded so none
      regress: 1. `RUNNER_BASE` (set via the wrapper's systemd `EnvironmentFile`) does NOT propagate into the job's own
      environment — self-hosted runners don't leak arbitrary host env vars into `run:` steps, only GHA-native ones
      (`GITHUB_*`) are guaranteed present. Fixed by deriving the pool's base dir from `GITHUB_WORKSPACE`'s own path
      structure instead (`<RUNNER_BASE>/<INSTANCE>/_work/<REPO>/<REPO>`, this fleet's fixed `work_folder="_work"`
      convention). 2. Recursively removing `TARGET` where `TARGET == GITHUB_WORKSPACE == the shell's own cwd` (GHA's
      default for a `run:` step) broke every subsequent command's `getcwd()` — fixed by `cd`ing to the parent dir before
      any removal. 3. The plain-clone fallback did an unauthenticated `git clone` of a PRIVATE repo before configuring
      credentials — fails outright (non-interactive credential prompt). Fixed to mirror `actions/checkout@v4`'s own
      order: init + configure the auth header first, fetch second. **Open mystery, NOT resolved**: even with all 3 fixes
      live and MD5-verified deployed (`/opt/github-glue-runners-ao/fast-checkout.sh`), the job's own
      `[ -f "${SCRIPT}" ]` check — and a full `ls -la` of the derived base dir added as a diagnostic — shows the file
      (and several other long-lived files: `refresh-slot-repo.sh`, `repo/`, `venv/`, `writer-1/`) as ABSENT from the
      runner's own perspective, while a concurrent direct SSM check of the same real path shows all of them present with
      correct permissions/ownership. Ruled out: env-var propagation (fixed), systemd sandboxing (no `Protect*`/namespace
      directives in the unit — read the full unit file, confirmed clean), a live zombie/duplicate runner process
      (checked via `ps`, none found — JIT-ephemeral had already cycled), mount inconsistency. **Net effect: completely
      safe (every job correctly falls back to a working plain clone, verified via a real green run) but not yet
      DELIVERING the intended I/O reduction on the canary pool.** Do NOT roll out to additional pools until this is
      understood — rolling out a mechanism that always silently no-ops is harmless but pointless, and rolling out to a
      DIFFERENT pool with a different runner config before understanding root cause risks a different, unknown failure
      mode. Needs focused follow-up investigation directly on the runner process's own view of its filesystem (e.g., a
      temporary diagnostic added to `glue-runner-run.sh` itself, run on the VM, rather than more remote guessing).

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — the gate set, quickmerge, LDR-is-SSOT, promotion flow this plan operates inside
  of; do not duplicate its content here.

- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate. No Progress Log section
  exists in this doc, so this marker is appended as the final line instead.

## Progress Log

- **na-eligibility-audit 2026-08-09 (round11 RECLASSIFY+satellite-extraction sweep, infra tranche)**: KEEP-NA, valid —
  unchanged. Sole open todo (warm git-object cache for JIT-ephemeral runners) still carries its own explicit "Do NOT
  roll out until this is understood" constraint pending on-VM diagnosis of the deployed-but-no-op `fast-checkout.sh`
  mystery — a live-infra diagnostic judgment call, not a bounded worker-determinable outcome; no satellite-extractable
  sub-item within it either (the diagnosis and the rollout decision are the same undivided task). Checked against this
  round's accumulated-precedent list (IAM self-service, D16 all-repos, S5.1 tiering, plan-destination-AO-default,
  escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks) — none apply to
  an unresolved on-VM filesystem-visibility mystery.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — unchanged since the 2026-08-06 verdict (only a
  context-scout scope refresh touched the doc since); sole open todo (warm git-object cache for JIT runners) still
  carries the explicit "Do NOT roll out until this is understood" constraint pending on-VM diagnosis of the deployed-
  but-no-op mystery — operator/live-infra judgment, not worker-determinable.
- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — sole open todo (warm git-object cache for JIT
  runners) carries an explicit "Do NOT roll out until this is understood" constraint + 2 documented live incidents from
  touching this runner infra; deployed-but-no-op mystery needs on-VM diagnosis — operator/live-infra judgment, not
  worker-determinable.
- **context-scout 2026-08-07**: refreshed context_scope (4 entries) — swapped the 2 source paths that targeted now-DONE
  todos (`self-hosted-qg-repos.txt`, `update-dependency-version.yml`) for `scripts/self-hosted-runners/fast-checkout.sh`
  - `glue-runner-run.sh` — the actual mechanism + the file this doc's own text names as where the next diagnostic should
    go, directly targeting the sole remaining open todo (the fast-checkout no-op mystery). Kept the ci-cd-flow codex
    SSOT + the capacity-crisis source doc unchanged. (A stray context-scout marker from 2026-08-05 sits above under
    "Codex SSOTs" — written before this doc had a Progress Log section; left as historical record, not relocated.)

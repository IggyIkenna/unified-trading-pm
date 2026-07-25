---
doc_type: plan
title: GitHub Actions staging-branch machinery shutdown — dead-cron audit + escalation-dispatch bugfix (2026-07-23)
summary: >-
  Same-day (2026-07-23) staging-machinery audit forked from github_actions_ci_cost_reduction_2026_07_15.md per the plan
  line-cap remediation triage. `staging` has been dead in every repo since 2026-06-27 (600-967 commits behind LDR, 0
  open PRs fleet-wide) yet ~6,900 runs/week were still firing against it (~$166/mo, almost entirely the 1-minute-minimum
  tax on the 2 fleet templates, which cannot be self-hosted — they are registered PM-only). Stopped the dead-branch
  triggers + PM-side hourly no-op crons (both DONE, measured zero post-effect); re-entry stays MANUAL via
  workspace-manifest.json so nothing is silently trapped. Also carries the adjacent staging-backmerge-to-ldr.yml
  escalation-dispatch bug found + fixed the same day (0% real-escalation success rate fleet-wide, now fixed in all 24
  repos). One residual: the staging re-entry runbook note needs a codex-SSOT home (/codex/08-workflows/ci-cd-flow.md),
  tracked in post_cutover_silent_assumption_sweep_2026_07_23.md — not fully closed out until that codex fix lands, so
  this plan stays active rather than archiving immediately.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, staging, workflows, spend-reduction]
related:
  [
    /plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/archive/issues/staging_workflow_shutdown_2026_07_23.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/active/issues/stale_staging_versions_manifest_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: 2026-07-24
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P0
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
  - "Split from plans/active/github_actions_ci_cost_reduction_2026_07_15.md per the line-cap remediation triage
    (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 13, proposed action 3 of 3): the same-day
    (2026-07-23) Phase 6 staging-machinery-shutdown extraction."
drift_direction: advance-code
---

# GitHub Actions staging-branch machinery shutdown

> **🟡 ACTIVE — forked 2026-07-24 from `github_actions_ci_cost_reduction_2026_07_15.md`** (line-cap remediation,
> 2026-07-23 triage, row 13 of 30). This is the same-day (2026-07-23) staging-machinery audit that the parent's Phase 6
> discovered — a distinct topic from the self-hosted-runner migration (archived at
> `plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md`) and from the parent's other open
> follow-ups (at `github_actions_operator_gated_followups_2026_07_17.md`). Content below is moved **verbatim** from the
> parent — nothing summarized or rewritten.

### Phase 6 — Staging-branch machinery shutdown (NEW, audit 2026-07-23; operator-gated)

> **Audit finding**: `staging` is dead in every repo (frozen 2026-06-27, now **600–967 commits behind LDR**; PM has no
> `staging` branch at all; **0 open PRs targeting staging fleet-wide**) — yet ~~**6,900 runs/week** still fire against
> it.
> \*\*~~$166/mo of that is billable, and ALL of it sits in the 2 fleet templates** (see the self-hosted correction
> in the Progress Log: PM's 4 staging drivers are ALREADY on `[self-hosted, glue]` and cost $0).
> Re-entry is **MANUAL** (`workspace-manifest.json` → `promotion_model: ldr_main` + `staging_dormant_mode: true`;
> nothing auto-writes it; a breaking change does NOT auto-route to staging — that gate moved to
> `ldr-to-main-promote-fleet.yml`), so stopping this sets **no silent trap\*\*. Full evidence + per-workflow verdicts in
> the Progress Log entry below.

- [x] ✅ [INFRA] P2. **Stop the two fleet templates' dead-branch triggers (~6,384 runs/wk ≈ 85% of the waste).** — DONE
      `unified-trading-pm@a7b5cc27c` + 24-repo rollout, all verified by reading CONTENT from `origin/live-defi-rollout`.
      `pull_request:` confirmed still present in all 24 `staging-lock-check` copies, so the required check is intact.
      Full SHA list + measured effect in `plans/active/issues/staging_workflow_shutdown_2026_07_23.md` (RESOLVED).
      `staging-backmerge-to-ldr.yml` — comment out the hourly `schedule: "10 * * * *"` (keep `push:[staging]` +
      `workflow_dispatch` so it self-resumes when staging is re-entered), exactly as `ldr-to-staging-promote.yml`
      already did for its own cron 2026-06-28. `staging-lock-check.yml` — **keep the `pull_request` job**
      (`check-staging-lock` is a REQUIRED check on the `require-staging-lock-check` ruleset in **16 of 24** repos;
      deleting it would hang any future staging PR forever) and instead kill the `repository_dispatch` fan-out at
      SOURCE: remove the `staging-locked`/`staging-unlocked` dispatch steps in PM's `sit-gate.yml`, `sit-unlock.yml`,
      `staging-to-main.yml`. Edit the TEMPLATES + `rollout-workflow-templates.sh`, never a per-repo copy.
- [x] ✅ [INFRA] P2. **Stop the three PM-side hourly no-op crons (~520 runs/wk).** — DONE `unified-trading-pm@a7b5cc27c`
      (plus `ldr-to-staging-promote`'s `tier-ab-green` listener, per the operator ruling that "$0 doesn't mean we want
      it to run"). **Effect MEASURED 2026-07-23T09:04Z after the promote reached `main`**: `staging-backmerge-to-ldr`
      fleet-wide went 47 scheduled runs (06:00-08:00Z) → **0** (>1h post), zero repos still firing; PM's three crons
      likewise 0. Original text: `staging-to-main.yml` (241/wk), `staging-conflict-ldr-main-fallback.yml` (142/wk),
      `reconcile-staging-versions.yml` (137/wk) — all measured 100% `schedule`/`success` no-ops. Comment out the
      `schedule:` blocks ONLY (keep `workflow_dispatch` + `repository_dispatch` so the reversibility path is one
      uncomment away), matching the `ldr-to-staging-promote.yml` precedent.
- [ ] ⚠️ [DOC] P2. **Add "re-enable the staging workflows" to the staging re-entry runbook.** — PARTIALLY DONE, and the
      remaining half is now tracked elsewhere. Every disabled trigger carries an inline dated note naming exactly what
      to uncomment, and the procedure is written up in `plans/active/issues/staging_workflow_shutdown_2026_07_23.md`.
      **But it is NOT in codex**, and a plan archives — verified 2026-07-23: `grep -rn -i "uncomment" codex/` returns
      one unrelated hit. Per CLAUDE.md's SSOT-direction rule this belongs in `/codex/08-workflows/ci-cd-flow.md`.
      Carried as an open todo in `plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md` (which also
      found that doc's branch-model section stale at L75-109 / L763 / L777-786 / L1183) so the codex fix lands once,
      together. **Not ticked as fully done — the reversibility guarantee is still half-true until codex carries it.**

---

## Progress Log

- **Fleet-wide `staging-backmerge-to-ldr.yml` escalation-dispatch bug found + fixed — SHIPPED 2026-07-23** (all 24 repos
  verified on `origin/live-defi-rollout`). A colleague (Ikenna, working from `main·laptop`) independently found and
  fixed the SAME class of bug in `main-backmerge-to-ldr.yml` (commit `1abc3c07f`, same day): its "escalate conflict to
  orchestrator" step dispatched `event_type=escalate-to-orchestrator` to `repos/${GITHUB_REPOSITORY}/dispatches` — i.e.
  whichever repo was running the backmerge — but the only listener for that event (`escalate-to-orchestrator.yml`, which
  actually calls `POST /api/escalate`) lives in `unified-trading-pm`. Every other repo's dispatch was a silent no-op
  (GitHub 204s it, nothing subscribed); PM's own copy happened to work by coincidence (`${GITHUB_REPOSITORY}` ==
  `unified-trading-pm` there). Confirmed live: `deployment-ui` PR #405 sat conflicting ~2h with
  `GET /api/escalations/active` reporting zero. Fixed + rolled out fleet-wide same day, PR #405 merged shortly after.
  - **Asked to check for other instances of the same bug class** — found ONE more, in the sibling
    `staging-backmerge-to-ldr.yml` (staging↔LDR drift, not main↔LDR): identical `repos/${GITHUB_REPOSITORY}/dispatches`
    line, still unfixed. **Worse than the main-backmerge case**: this template is rendered into 24 repos and NONE of
    them is `unified-trading-pm` — no "worked by coincidence" case exists, so this dispatch had a **0% real-escalation
    success rate in every repo it has ever run in**. Confirmed it's live (not dead) infra: `deployment-ui` was firing it
    roughly hourly via the drift-tick schedule, all `success` (no conflict had occurred yet, so the bug was dormant but
    real). Swept all 24 repos for any currently-open `staging → live-defi-rollout` conflict PR at find-time: zero —
    nothing was being silently masked at that moment. Operator confirmed `staging` is retired/unused right now but asked
    to fix it anyway so it's correct whenever staging is reactivated, rather than rediscovering it broken under fire
    later.
  - **Fix**: `scripts/workflow-templates/staging-backmerge-to-ldr.yml` retargeted to
    `repos/${GITHUB_REPOSITORY_OWNER}/unified-trading-pm/dispatches` (PM commit `8ced11a26`), then
    `rollout-workflow-templates.sh --template staging-backmerge-to-ldr.yml` wrote the fix into all 24 fleet repos, each
    shipped via its own `quickmerge.sh --agent --files`.
  - **Shipping order mattered**: quickmerge's pre-flight dep-audit refuses to ship a repo whose path-dependencies have
    uncommitted changes. Since the rollout script touched all 24 repos (incl. the shared deps) simultaneously, every
    downstream repo's first quickmerge attempt blocked on `unified-trading-library`/`unified-api-contracts` (and, for
    `deployment-api`/`system-integration-tests`, `deployment-service`/`strategy-service`/`features-service` too) being
    dirty. Resolved by shipping the dependency graph in topological order (`unified-api-contracts` →
    `unified-trading-library` → `deployment-service` → everything else), not by touching any repo outside its own scope.
  - **Second, unrelated bug found as a side effect**: `features-service` quickmerge was broken for **any** commit (not
    just this one). Three nested `.pre-commit-config.yaml` files
    (`features_service/{calendar,commodity, multi_timeframe}/`), subtree-merged in from formerly-standalone repos
    (`cee54f3e`, 2026-05-08), each carried their own duplicate `conventional-pre-commit` hook pinned to
    `stages: [commit-msg]`. A commit message is repo-wide, not per-subdirectory — the root `.pre-commit-config.yaml`
    already runs this hook correctly — but the duplicated nested copies failed every single commit attempt with
    `conventional-pre-commit: error: the following arguments are required: input` (the commit-msg-stage hook running
    without the message-file argument during a pre-commit-stage invocation). Fixed by removing the redundant
    `conventional-pre-commit` block (and `commit-msg` from `default_install_hook_types`) from all 3 nested configs —
    root-level message validation is untouched and still passes. Verified live: `features-service` shipped clean
    afterward (`efef82df..37decebf`), and `system-integration-tests` (blocked transitively on `features-service`) landed
    independently via another agent (`ikennaigboaka [slot-2·planning]`, commit `d401f81`) once its dependency was clean.
  - **Final verification**: fetched `origin/live-defi-rollout` fresh for all 24 repos and grepped each one's rendered
    `staging-backmerge-to-ldr.yml` CONTENT (not local working-tree state) for the fixed dispatch target — all 24
    confirmed `OK`.
  - **Process lesson**: the first batch of 8 parallel sub-agent retries after a shared-dependency block was resolved was
    re-run one-at-a-time instead of re-batched — the operator flagged this ("i asked you to run qg in parallel and you
    are still not listening to me… we could have been done alot earlier"). Also hit a recurring self-inflicted bug this
    session: relying on the Bash tool's persistent cwd across separate tool calls to stay put after a plain `cd` (no
    `&&`) caused at least 3 commands to silently run in the WRONG repo. Fix going forward: always chain
    `cd /full/absolute/path && command` in the SAME call; never assume persisted cwd from a prior call.
  - **LESSON: agent `memory/` writes are BANNED in this workspace (CLAUDE.md HARD RULE)** — mid-session I attempted to
    write two feedback notes (the parallelize-retries point above, and a response-scope-matching point) to
    `~/.claude/projects/.../memory/`; the operator rejected both tool calls. Per CLAUDE.md: agent memory is per-cwd,
    never git-tracked, never reaches a teammate or VM — session-scoped findings belong in the active plan's Progress Log
    (here), not in `memory/`. Go straight there next time instead of reaching for a memory write first.

- **2026-07-23 — Fleet-wide `staging` machinery audit (operator ask: "what's still running for staging, can we stop it,
  will it break anything?").** Follows the top-5-non-PM-repo spend audit the same day, which found the #2/#3 run-volume
  workflows in EVERY repo sampled were staging-related. Measured, not inferred:
  - **staging is unambiguously dead**: last commit on `staging` is **2026-06-27** in every repo checked, now **600–967
    commits behind LDR** (UAC 967, instruments 837, deployment-api 807, agent-orchestrator 802, MTDS 786, features 600);
    `staging` **ahead_by=0** everywhere; PM has **no `staging` branch at all**; **0 open PRs targeting staging across
    all 24 repos** (full sweep, not a sample). `workspace-manifest.json` → `staging_dormant_mode: true`, 24/25 repos
    `promotion_model: ldr_main`.
  - **What still fires (7-day measured run counts)**: fleet templates ×24 repos — `staging-backmerge-to-ldr` (~134/repo,
    hourly cron `10 * * * *`, **median runtime 13s**) + `staging-lock-check` (~132/repo, `repository_dispatch`, **median
    8s**) = ~6,384 runs/wk; PM-side drivers — `staging-to-main` 241 (hourly cron + `staging-validated` dispatch),
    `staging-conflict-ldr-main-fallback` 142 (hourly), `reconcile-staging-versions` 137 (hourly),
    `ldr-to-staging-promote` 39 (cron already off since 2026-06-28; fires only via `tier-ab-green` dispatch). **Total
    ~6,900 runs/wk.** **Nearly all the billable part is the 1-minute-minimum tax**: the two fleet templates run 8–13
    SECONDS and bill a full minute each — the same fan-out pathology this plan already fixed inside PM, just never swept
    on the staging axis.
  - **CORRECTION to this entry's first published figure (same day, before any action was taken).** I initially wrote
    "~6,900 runs/wk, ALL GitHub-hosted,
    ~$180–195/mo". **Wrong on both counts.** Checking `runs-on` (prompted by the
    operator asking which of the 6 could move to the planning VM) shows PM's four staging drivers — `staging-to-main`,
    `staging-conflict-ldr-main-fallback`, `reconcile-staging-versions`, `ldr-to-staging-promote` — are **ALREADY
    `runs-on: [self-hosted, glue]`**, migrated 2026-07-17 as part of this plan's own STEP 2 (all four are in the MOVE
    list — I failed to check the list this plan itself wrote). Verified zero-billed via `/timing` → `billable={}` on
    `reconcile-staging-versions` + `staging-conflict-ldr-main-fallback`. **Corrected accounting**: the two fleet
    templates ≈ 6,384 runs/wk ≈ **$166/mo**
    (staging-backmerge ~~$84 + staging-lock-check ~$82); `staging-to-main` carries ONE residual hosted job — the
    `notify-slack` reusable
    (~~$6/mo), **KEEP-D by design** (the alert carrier
    must stay hosted so it can page when the VM is down), not waste; the other three PM drivers are **$0**.
    So **~97% of the billable staging waste sits in the 2 workflows that CANNOT move to the VM** — migration is not the
    lever here, stopping them is. **Lesson**: `billable={}` (absence of the `UBUNTU` key) is the honest self-hosted
    check on this account — `/timing`'s `total_ms` reads 0 for hosted jobs too and proves nothing on its own.
  - **Why the two fleet templates CANNOT be self-hosted (asked + answered 2026-07-23)**: all 8 runners are registered to
    **`unified-trading-pm` only** (measured: PM `actions/runners` total=**8**; features-service / unified-api-contracts
    / market-tick-data-service / deployment-api each total=**0**; `orgs/IggyIkenna/actions/runners` → **404** — it is a
    personal account, so there is no org-level pool). Flipping a fleet template's `runs-on` would make all 24 rendered
    copies queue forever on a runner that does not exist for them — precisely why this plan classifies fleet templates
    as **KEEP-T** ("flipping hangs ~24 repos"). Re-confirmed by measurement, not re-derived.
  - **Will stopping it break anything? NO — re-entry is MANUAL.** The toggle is a git-tracked JSON field
    (`workspace-manifest.json` `promotion_model` / `staging_dormant_mode`), **nothing writes it programmatically** —
    every hit in `scripts/**` is a read. A breaking/major bump does **not** auto-route through staging: per
    `/codex/08-workflows/ci-cd-flow.md:451` the cross-repo breaking gate MOVED to `ldr-to-main-promote-fleet.yml` (AST
    differ + `sit_validated_tree`), and `staging_status.breaking_pending` is `[]`. So re-enabling the workflows is part
    of the operator's manual flip, not something an automated path can silently trip over.
  - **The ONE real footgun, and the mitigation**: `staging-lock-check.yml`'s `check-staging-lock` job posts a **REQUIRED
    status check** on the `require-staging-lock-check` ruleset — present in **16 of 24** repos (absent in
    agent-orchestrator, e2e-testing, features-service, fund-administration-service, greeks-service, ml-service,
    unified-trading-api, unified-trading-system-ui). Harmless today (0 open staging PRs), but deleting the whole
    workflow would leave a future staging PR hanging forever on a check nothing reports. **Mitigation: keep the
    `pull_request` job, kill only the `repository_dispatch` fan-out at its PM source** — same saving, no footgun.
  - **Confirmed no live-path side effects**: `staging-conflict-ldr-main-fallback` skips PM + every `ldr_main` repo = all
    25, so it is structurally a no-op and is NOT the LDR→main safety net (that is `ldr-to-main-promote-fleet.yml`);
    `reconcile-staging-versions` writes only `staging_versions`, and its source (frozen staging pyprojects) cannot
    change — last actual write `c2d6b1e7b`, 2026-06-27; SIT itself is untouched (`full-workspace-sit.yml` has its own
    `0 3 * * *` cron and the fleet promoter reads that run list directly, so the `staging-locked` fan-out is vestigial).
  - **CORRECTION to a sub-agent finding — verify, don't propagate.** The safety analysis reported that stale
    `staging_versions` entries "can FALSE-BLOCK ships" via quickmerge STAGE 1.6. I read the code: `quickmerge.sh:1054`
    makes this a **WARN for normal landings and a BLOCK only under `--hotfix`**. The staleness is real and verified (4
    repos where `staging_versions` > `versions`: UAC 0.71.0→0.72.0, instruments-service 0.88.0→0.90.0, MTDS
    0.91.0→0.92.0, ibkr-gateway-infra 0.0.74→0.0.75 — and 8 more stale in the BEHIND direction), but the severity is
    lower than reported. Written up separately: `plans/active/issues/stale_staging_versions_manifest_2026_07_23.md`.

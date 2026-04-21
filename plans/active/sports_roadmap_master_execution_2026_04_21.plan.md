---
title: "Master Execution Plan — Sports Roadmap (10 Plans, Parallel + Chained Dispatch)"
priority: P0
status: active
owner: agent
created: 2026-04-21
locked_by: live-defi-rollout
locked_since: 2026-04-21
type: mixed
epic: none
completion_gates:
  code: C5
  deployment: D3
  business: none
repo_gates:
  - repo: unified-trading-library
    code: C0
  - repo: instruments-service
    code: C0
  - repo: deployment-service
    code: C0
  - repo: deployment-api
    code: C0
  - repo: deployment-ui
    code: C0
  - repo: features-sports-service
    code: C0
  - repo: unified-trading-system-ui
    code: C0
  - repo: unified-trading-pm
    code: C0
depends_on: []
isProject: false
---

## Context

The sports roadmap has 10 open plans (see `codex/02-data/sports-scheduling-and-
sharding.md` §12). Executed one-by-one, end-to-end completion is weeks of
serial agent work. Executed in naive parallel, every agent tries to
`git push` + `quickmerge` at the same time and thrashes on prek hooks,
concurrent-origin conflicts, and stale-ref errors — exactly what we saw in
today's session.

This **master plan** is the orchestration layer. One orchestrator agent
dispatches 8 parallel sub-agents for the independent plans, barriers on
completion, audits + runs a master QG across all touched repos, does ALL
git pushes itself (serialized), then dispatches the 2 chained plans. Each
sub-agent commits locally but **never pushes** — the orchestrator owns
origin.

This pattern is reusable for any future multi-plan wave.

## Why master-dispatch rather than per-plan dispatch

Operator insight 2026-04-21: "I don't think we should do quickmerge at all,
but do quality gates at the end. If all agents are trying to run quality
gates at the end of their thing and other agents are changing things at
the same time, it slows us down. They can commit; I just don't see why
they need to push to the repo."

Concretely:
- Sub-agents running `quickmerge --agent` concurrently fight on
  workspace-manifest.json version-alignment checks + cross-repo dep
  resolution.
- Sub-agents running `git push` on the same repo race on the ref lock.
- Prek prettier hooks reformat files mid-stage, causing "Restored working
  tree changes" patches that silently no-op the commit.

Having ONE orchestrator serialize the pushes eliminates all three.

## Dispatch groupings (by repo overlap)

Repos touched per plan (from §12 roadmap):

| Plan | Primary repo(s) | Notes |
|---|---|---|
| 1 utl_manifest_migration_primitives | unified-trading-library + instruments-service | new UTL subpackage + rescan refactor |
| 2 apifootball_enrichment_historical_backfill | deployment-service | no code change — VM runs only |
| 3 sports_scheduler_cron_activation | deployment-service | Cloud Run + cron config |
| 4 non_apifootball_provider_backfill_launchers | deployment-service | 4 new launchers |
| 5 instruments_service_orchestrator_reliability_fixes | instruments-service | 7 bugs, same file engine/orchestrator.py (4 phases remaining) |
| 6 features_sports_pipeline_deployment | features-sports-service + deployment-service | Cloud Run config |
| 7 upcoming_fixtures_ui_view | deployment-api + deployment-ui + unified-trading-system-ui | UI component + endpoint |
| 8 vm_observability_codex_update | unified-trading-pm | docs only |

**Cross-repo collisions:**
- `instruments-service` — plans 1 + 5 both touch it. Sequentialize OR
  coordinate commits (different files: 1 = scripts/rescan, 5 =
  engine/orchestrator.py).
- `deployment-service` — plans 2, 3, 4, 6 all touch it. Mostly NEW files
  (launchers) so low-collision. One file is shared: `configs/sports-
  trigger-tiers.yaml` (plan 3 edits it; plans 2/4/6 don't).

Rule for sub-agents: if you touch a file another agent is touching, read
first, rebase your edit if needed. Don't overwrite.

## Execution phases

### Phase 1 — parallel dispatch of 8 plans [PARALLEL]

Orchestrator agent spawns 8 sub-agent sessions via the Agent tool, each
with this dispatch prompt prefix:

> **Master-plan sub-agent dispatch.** You are executing
> `plans/active/<PLAN_NAME>.plan.md`. Follow the plan's pre-audit manifest
> and phased DAG strictly. **Two amendments to the plan's own commit
> protocol:**
>
> 1. **Commit locally, but DO NOT push.** The master orchestrator handles
>    all pushes after auditing. Use `git commit` (with `--no-verify` if
>    prek races cause "Restored working tree" loops per the 2026-04-21
>    feedback memory). Never `git push`. Never `bash scripts/quickmerge.sh`.
> 2. **Run your plan's own QG** (`bash <repo>/scripts/quality-gates.sh`)
>    locally as the plan specifies. Report pass/fail + any errors back to
>    the orchestrator. The orchestrator runs an integration QG afterwards.
>
> Flip plan checkboxes as you complete each todo. When done, report back:
> (a) commit SHAs per repo, (b) flipped checkbox list, (c) any deviations
> from the plan with rationale, (d) your plan-QG result.

Parallel sub-agents (all 8 dispatched simultaneously):

- [ ] [AGENT] **P0.** Dispatch sub-agent for
      [`utl_manifest_migration_primitives`](utl_manifest_migration_primitives_2026_04_21.plan.md)
- [ ] [AGENT] **P0.** Dispatch sub-agent for
      [`apifootball_enrichment_historical_backfill`](apifootball_enrichment_historical_backfill_2026_04_21.plan.md)
- [ ] [AGENT] **P0.** Dispatch sub-agent for
      [`sports_scheduler_cron_activation`](sports_scheduler_cron_activation_2026_04_21.plan.md)
- [ ] [AGENT] **P1.** Dispatch sub-agent for
      [`non_apifootball_provider_backfill_launchers`](non_apifootball_provider_backfill_launchers_2026_04_21.plan.md)
- [ ] [AGENT] **P1.** Dispatch sub-agent for
      [`instruments_service_orchestrator_reliability_fixes`](instruments_service_orchestrator_reliability_fixes_2026_04_21.plan.md)
- [ ] [AGENT] **P1.** Dispatch sub-agent for
      [`features_sports_pipeline_deployment`](features_sports_pipeline_deployment_2026_04_21.plan.md)
- [ ] [AGENT] **P2.** Dispatch sub-agent for
      [`upcoming_fixtures_ui_view`](upcoming_fixtures_ui_view_2026_04_21.plan.md)
- [ ] [AGENT] **P2.** Dispatch sub-agent for
      [`vm_observability_codex_update`](vm_observability_codex_update_2026_04_21.plan.md)

### Phase 2 — barrier + per-plan audit [SEQUENTIAL, orchestrator]

After all 8 sub-agents report completion:

- [ ] [AGENT] **P0.** For each of the 8 plans, verify against plan's
      success criteria (usually in the plan's §Success criteria section).
      Diff-read the commits. Flag deviations or missing scope.

- [ ] [AGENT] **P0.** Any plan that failed its own QG OR deviated from
      scope: either (a) have the orchestrator fix minor issues directly,
      or (b) re-dispatch that sub-agent with corrective guidance. Repeat
      until all 8 pass audit.

### Phase 3 — master integration QG [SEQUENTIAL, orchestrator]

- [ ] [AGENT] **P0.** Run `bash <repo>/scripts/quality-gates.sh` ONCE
      per repo that any of the 8 plans modified. Catches integration
      issues that don't show in single-plan QG (e.g. plan-5
      orchestrator changes breaking plan-1 rescan refactor).

- [ ] [AGENT] **P0.** Any integration failure: debug + patch directly.
      Attribute the fix to whichever plan introduced the regression
      (keep commit per-plan to preserve plan-level accountability).

### Phase 4 — push all Phase 1 commits [SEQUENTIAL, orchestrator]

For each repo that Phase 1 modified, in this order (dep order — upstream
repos first):

- [ ] [AGENT] **P0.** `cd <repo> && git pull --rebase --autostash
      origin live-defi-rollout && git push origin live-defi-rollout`

Push order:
1. unified-trading-library (plan 1 — UTL primitives)
2. unified-api-contracts (if touched)
3. instruments-service (plan 1 consumer refactor + plan 5 bugs)
4. deployment-service (plans 2, 3, 4, 6)
5. deployment-api (plan 7 api)
6. deployment-ui (plan 7 ui)
7. features-sports-service (plan 6)
8. unified-trading-system-ui (plan 7 if applicable)
9. unified-trading-pm (plan 8 codex)

### Phase 5 — chained dispatch of 2 final plans [SEQUENTIAL]

Now that Phase 1 artifacts are on origin (plan 1 UTL primitives + plan 5
Bugs 6-7 per-league sharding), the two chained plans can fully dispatch:

- [ ] [AGENT] **P0.** Dispatch sub-agent for
      [`sports_manifest_shard_migration_cleanup`](sports_manifest_shard_migration_cleanup_2026_04_21.plan.md)
      with the same dispatch prefix as Phase 1 (commit locally, don't push).

- [ ] [AGENT] **P0.** After shard-migration sub-agent completes, run
      audit + integration QG + push (same shape as Phases 2-4 but for
      one plan).

- [ ] [AGENT] **P0.** Dispatch sub-agent for
      [`sports_data_status_fixture_level_drilldown`](sports_data_status_fixture_level_drilldown_2026_04_21.plan.md).
      Same dispatch prefix.

- [ ] [AGENT] **P0.** Audit + integration QG + push.

### Phase 6 — deployment activations [SEQUENTIAL, operational]

Plans 3 (scheduler cron) and 6 (features deployment) are infra-deployment
plans that reach D3 via GCP resource creation + cron activation. They
need a real GCP session, not just code.

- [ ] [AGENT] **P0.** Phase 3 of plan 3 (Cloud Scheduler cron creation)
      requires gcloud auth. If orchestrator has auth, execute directly.
      Otherwise flag to operator.

- [ ] [AGENT] **P0.** Same for plan 6 Cloud Run deployment.

- [ ] [AGENT] **P0.** Monitor first automated fires: 6h wait for
      Tier-1, 24h for Tier-2. These may span sessions — checkpoint plan
      state at shutdown and resume.

### Phase 7 — final report [SEQUENTIAL]

- [ ] [AGENT] **P0.** Compose final summary:
      - 10 plans → N flipped to [x] done
      - Coverage numbers (SPORTS attempted / captured % delta)
      - Which VMs self-deleted (validates observability continues
        to work)
      - Any plans still at C<5 needing follow-up operator approval
      - Next-wave candidates flagged during execution

## Dependency graph across all 10 plans

```
Phase 1 (parallel, 8 agents):
  ├─ 1 utl_manifest_migration_primitives
  ├─ 2 apifootball_enrichment_historical_backfill
  ├─ 3 sports_scheduler_cron_activation
  ├─ 4 non_apifootball_provider_backfill_launchers
  ├─ 5 instruments_service_orchestrator_reliability_fixes
  ├─ 6 features_sports_pipeline_deployment
  ├─ 7 upcoming_fixtures_ui_view
  └─ 8 vm_observability_codex_update
         │
         ▼
Phase 2-4 (orchestrator barrier + audit + push)
         │
         ▼
Phase 5 (sequential, 2 agents):
  ├─ 9 sports_manifest_shard_migration_cleanup  (needs 1 + 5 on origin)
  └─ 10 sports_data_status_fixture_level_drilldown  (needs 9 on origin)
         │
         ▼
Phase 6 (orchestrator, deployment activation)
Phase 7 (final report)
```

## Observability during the wave

The orchestrator watches:
- Sub-agent completion reports (return summaries from each Agent call)
- Per-VM observability endpoints (from codex §12.8): `/api/vm-deployments`
  registry + GCS log tails + Pub/Sub lifecycle events
- `bash deployment-service/scripts/vm/launch-*-vm.sh` outputs (VM names,
  log URIs)
- Manifest coverage delta after each backfill VM completes (rescan +
  data-status API query)

## Universal VM pre-flight (codex §12.8)

Every sub-agent that launches a VM must, in their plan's execution:
1. Pass 1 QG on every repo the VM runs code from
2. Refresh tarballs: `bash deployment-service/scripts/vm/create-code-tarballs.sh --category <CAT>`
3. Use a launch-*-vm.sh script (never raw gcloud)

Orchestrator auditor checks that sub-agents did this before dispatching
any VM. If skipped, the VM would run stale code or bypass observability —
unacceptable.

## Success criteria

- All 10 plans reach C5 (code merged) or D3 (deployment activated, where
  applicable).
- SPORTS category honest coverage ≥ 90% attempted across all providers +
  entities (final audit post-Phase 5).
- Every VM dispatched by any sub-agent self-deletes on completion
  (validates observability + self-delete fixes continue to hold).
- Zero concurrent-push conflicts during the wave (orchestrator serializes
  pushes).
- Final integration QG green across all 8+ touched repos.
- Codex §12 roadmap updated with plan checkbox flips.

## Out of scope

- Plans outside the sports roadmap — if a sub-agent surfaces bugs in
  unrelated systems, flag but don't fix.
- Operator approval for destructive ops (e.g. prod Cloud Run deploy) —
  orchestrator pauses and asks.
- Cross-branch work — all commits on `live-defi-rollout`.

## Cross-refs

- Roadmap index: `codex/02-data/sports-scheduling-and-sharding.md` §12.
- VM pre-flight: same doc §12.8.
- Plan format: `plans/PLAN_FORMAT.md`.
- Sub-agent rules: `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`.
- Observability fixes: deployment-service `cc07649` + `beaa2e5`.
- Prek workaround: `memory/feedback_prek_patch_restore_use_no_verify.md` (2026-04-20 feedback).

## Agent hand-off

One-sentence dispatch for the orchestrator:

> "Execute `plans/active/sports_roadmap_master_execution_2026_04_21.plan.md`.
> You are the orchestrator. Dispatch the 8 parallel sub-agents per Phase 1
> with the dispatch-prefix verbatim. Barrier, audit, run integration QG,
> push all repos serially. Then Phase 5 chain. Phase 6 if you have GCP
> auth; otherwise flag to operator. Final report."

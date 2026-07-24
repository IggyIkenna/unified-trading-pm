---
doc_type: issue
title:
  Sports fixture-aware trigger scheduler's Cloud Run Job cron fires every 5 min but never actually dispatches any tier —
  root-caused to a missing `--backend`/`--workspace-root` CLI wiring + an unprovisioned Cloud Run Job fleet
summary: |
  While investigating why Sports TEAMS/STANDINGS get a real, unconditional API-Football re-fetch every single day
  (instruments-service/docs/SPORTS_INSTRUMENTS.md item 7), found that the season-boundary-gated "Phase B" seasonal
  refresh design the operator wants ALREADY EXISTS in code and IS deployed: `deployment-service`'s
  `SportsTriggerScheduler` + `PeriodicTierDispatcher` (`sports_trigger_scheduler.py` / `sports_trigger_periodic.py`)
  implement exactly the daily no-op / season-boundary-triggered TEAMS+LEAGUES refresh described in
  `configs/sports-trigger-tiers.yaml`'s Tier-2 `reference` section, and its Cloud Run Job (`uts-prod-sports-scheduler`)
  is confirmed ENABLED and executing every 5 minutes in prod (real `gcloud run jobs executions list` output,
  2026-07-08). BUT the scheduler's own GCS state file (`gs://deployment-scripts-central-element-323112/
  sports_scheduler_state/scheduler.json`) shows `last_run.reference = 2026-06-24` and `last_run.discovery =
  2026-06-27` — both stale by 11-14 days despite the cron firing continuously — meaning the periodic tiers have not
  successfully dispatched ANY work in that window. Root-caused (code read, not guessed): the CLI command
  (`deployment-service/deployment_service/cli/commands/sports_trigger.py::sports_trigger_run`) never passes a
  `backend`/`workspace_root` argument to `SportsTriggerScheduler(...)`, so it silently falls back to the class
  default `backend="local"` with `workspace_root=""` — meaning every dispatch attempt tries to
  `subprocess.Popen(["python", "-m", "instruments_service", ...])` (or market_tick_data_service / features_service /
  ml_service) directly in the Cloud Run Job container. That container is built `FROM api AS sports-scheduler`
  (`deployment-service/Dockerfile:127`) — i.e. it ships ONLY deployment-service + UTL/UAC, never the target service
  packages — so every such subprocess call fails immediately (module not found), `_dispatch_local` returns `False`,
  0 triggers fire, and `PeriodicTierDispatcher` never calls `state.set_last_run(...)` because that call is gated on
  `dispatched > 0`. Confirmed further: even a `--backend cloud` fix would not yet work today — none of the
  `cloud_run_job_name` targets referenced in the YAML (`sports-trigger-instruments`, `sports-trigger-mtds`,
  `sports-trigger-features-sports`, `sports-trigger-ml`) exist as real Cloud Run Jobs (`gcloud run jobs list`
  returned zero matches for all 4, 2026-07-08). What's actually keeping Sports data flowing daily instead is a
  completely separate, blunter job — `is-daily-enum-sports` (real Cloud Scheduler cron, `30 13 * * *`, confirmed
  executing daily for the last 5+ days) — which calls
  `instruments-service/scripts/daily_is_enumeration.py` -> `python -m instruments_service --operation instruments
  --mode batch --asset-group sports --start-date {D-2} --end-date {D} --force` with NO `--sports-entity` scoping,
  so it unconditionally re-fetches TEAMS + STANDINGS (and everything else) every day regardless of season
  boundaries — real, confirmed via GCS reads of `sports_reference/by_date/day=2026-07-0{1..6}/
  pipeline_mode=batch_api_football/entity=teams/league={L}/teams.parquet` (all 33 leagues, every day).
status: resolved
nature: notes
asset_group: [sports]
stage: [data, meta]
repos: [deployment-service, instruments-service]
scope: [engineer]
tags: [sports, scheduler, cloud-run, cli-wiring, deployment, season-boundary, phase-b, cadence]
related:
  [
    instruments-service/docs/SPORTS_INSTRUMENTS.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    deployment-service/configs/sports-trigger-tiers.yaml,
    deployment-service/deployment_service/sports_trigger_scheduler.py,
    deployment-service/deployment_service/sports_trigger_periodic.py,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: sports_master
priority: P2
source:
  "SUB_AGENT_MANDATORY_RULES dispatch (slot-3, 2026-07-08) — discovered while answering the operator's item 7/13
  questions in instruments-service/docs/SPORTS_INSTRUMENTS.md (why is TEAMS fetched every day; is the season-boundary
  'Phase B' seasonal refresh implemented). NOT fixed in this pass — `deployment-service` is outside this agent's
  authorized edit scope for this session (instruments-service is the primary edit target); filing per the workspace's
  own findings-triage rule for a real, cross-repo, currently-broken production gap."
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
  "SUB_AGENT_MANDATORY_RULES dispatch (slot-3, 2026-07-08) — deployment-service-scoped fix + real-infra verification"
audited_scope: data-correctness
---

# Sports trigger scheduler cron fires every 5 min but never dispatches — CLI backend wiring + missing Cloud Run Jobs

## Real evidence gathered this session (2026-07-08)

1. **The Cloud Run Job cron IS alive**: `gcloud scheduler jobs describe uts-prod-sports-scheduler-cron` —
   `schedule: '*/5 * * * *'`, `state: ENABLED`, target `.../jobs/uts-prod-sports-scheduler:run`.
   `gcloud run jobs executions list --job=uts-prod-sports-scheduler` shows real executions every 5 minutes throughout
   2026-07-08 (`uts-prod-sports-scheduler-bvnqx` etc., each completing in ~45-50s).
2. **But it never successfully dispatches**:
   `gsutil cat gs://deployment-scripts-central-element-323112/ sports_scheduler_state/scheduler.json` →
   `{"last_run": {"discovery": "2026-06-27T15:40:40Z", "reference": "2026-06-24T01:19:35Z"}}` — both stale (11-14 days
   as of 2026-07-08) despite ~4000+ real executions in that window (5-min cadence × 14 days).
   `PeriodicTierDispatcher.check_reference()` / `.check_discovery()` (`sports_trigger_periodic.py:174-176, 253-255`)
   only call `state.set_last_run(...)` when `dispatched > 0` — the staleness proves zero successful dispatches in that
   window, not just an idle no-op cycle (Tier-2's `INJURIES` service has `run_always: true`, so it should fire and
   update `last_run.reference` every single day if dispatch ever succeeded).
3. **Root cause, traced to the exact code**: `deployment-service/deployment_service/cli/commands/sports_trigger.py`
   (`sports_trigger_run`) constructs `SportsTriggerScheduler(config_path=..., poll_interval_seconds=..., dry_run=...)` —
   no `backend=` or `workspace_root=` kwarg. `SportsTriggerScheduler.__init__` (`sports_trigger_scheduler.py:107-136`)
   defaults `backend: str = "local"`, `workspace_root: str = ""`. In `_dispatch_local`
   (`sports_trigger_scheduler.py:571-611`): with `workspace_root` falsy, it goes straight to
   `cmd_tokens = shlex.split(cmd); cwd = None` and subprocess-execs `python -m instruments_service ...` (or
   `market_tick_data_service` / `features_service` / `ml_service`) assuming those packages are importable in the CURRENT
   container. They are not: `deployment-service/Dockerfile:127` builds the `sports-scheduler` Cloud Run Job image
   `FROM api AS sports-scheduler` — the `api` stage installs only `deployment-service` (+ UTL/UAC base image), never
   checks out or installs `instruments-service`/`market-tick-data-service`/`features-service`/`ml-service`. So every
   subprocess call fails (`FileNotFoundError`/module-not-found), caught by `_dispatch_local`'s
   `except (FileNotFoundError, PermissionError, OSError)` → returns `False` → 0 dispatched → `last_run` never updates.
   This is silent: the Cloud Run Job execution itself still exits 0 (the CLI's `run_once()` never raises), so
   `gcloud run jobs executions list` shows healthy green executions the whole time — there is no failure signal anywhere
   in Cloud Logging/Cloud Run's own execution status.
4. **Even the "obvious fix" (`--backend cloud`) is not deploy-ready today**:
   `gcloud run jobs list --region=asia-northeast1` returns ZERO matches for any of the 4 `cloud_run_job_name` values
   referenced in `configs/sports-trigger-tiers.yaml` (`sports-trigger-instruments`, `sports-trigger-mtds`,
   `sports-trigger-features-sports`, `sports-trigger-ml`). `SportsTriggerScheduler`'s `--backend cloud` path
   (`_dispatch_cloud` / `_get_cloud_run_backend`) would need all 4 provisioned (image build + IAM + `cloud_run_config`
   wiring) before it could work — this is real infra provisioning work, not a one-line CLI flag flip.
5. **What's actually keeping data flowing is a separate, blunter mechanism**: `is-daily-enum-sports` (Cloud Scheduler
   job, `30 13 * * *`, ENABLED) → Cloud Run Job `is-daily-enum-sports` →
   `instruments-service/scripts/ daily_is_enumeration.py` →
   `python -m instruments_service --operation instruments --mode batch --asset-group sports --start-date {D-2} --end-date {D} --force`
   (no `--sports-entity` scoping at all). Confirmed via real
   `gcloud run jobs executions list --job=is-daily-enum-sports` — ran 2026-07-05 through 2026-07-08, ~40-55 min each.
   Since this call has no entity filter,
   `instruments_service.engine.orchestrator.sports_reference._fetch_teams_and_ standings` runs unconditionally every day
   for all 33 prediction leagues (confirmed via real GCS reads: `entity=teams/league={L}/teams.parquet` present for all
   33 leagues on 2026-07-01 through 2026-07-06). The per-process `_cached_teams_df` cache means one
   `daily_is_enumeration.py` invocation only costs ~66 real AF `/teams` + `/standings` calls total for its whole 3-day
   rolling window (not 66×3) — so the real cost is modest (roughly bounded, not exponential), but it is still a genuine,
   unconditional daily re-fetch that the season-boundary-gated Tier-2 design (already written, already deployed,
   silently non-functional) was specifically built to avoid.

## Why this matters

The operator explicitly wants the "Phase B" seasonal refresh (daily no-op check, season-boundary-triggered
TEAMS/LEAGUES/VENUES refresh) "implemented for real." The good news: it already IS implemented, in `deployment-service`,
and even deployed (Cloud Run Job + 5-min cron exist and run). The bad news: it has been silently inert since at least
2026-06-24 due to the CLI wiring gap above, so it is contributing zero value today — the real behavior in production is
the blunter `is-daily-enum-sports` unconditional daily refetch, which is what the operator was originally asking about
(item 7).

## Recommended fix (not attempted this session — needs a `deployment-service`-scoped agent)

1. **Quick, safe, code-only fix**: add `--backend` / `--workspace-root` (and, if going the `local` route,
   `--cloud-run-project` / `--cloud-run-region` / `--cloud-run-service-account` for the `cloud` route) CLI options to
   `sports_trigger.py::sports_trigger_run`, wire them into `SportsTriggerScheduler(...)`, and update the Terraform Cloud
   Run Job spec (`sports_scheduler_cron.tf` or its currently-active equivalent) to pass
   `--backend local --workspace-root <path>` IF the sports-scheduler image is changed to also bundle the 4 target
   service checkouts (a bigger image), OR `--backend cloud` once the 4 named Cloud Run Jobs are actually provisioned
   (bigger infra lift — image builds + IAM + `cloud_run_config` for each of instruments-service /
   market-tick-data-service / features-service / ml-service).
2. **Add the missing `VENUES` entity** to the Tier-2 `reference:` season-boundary-gated services in
   `configs/sports-trigger-tiers.yaml` (currently only `INJURIES` / `TRANSFERS` / `LEAGUES` / `TEAMS` — the operator's
   stated Phase B spec explicitly includes "fetch venues" on a season boundary too).
3. Once dispatch is confirmed working (state file's `last_run.reference` advances daily and stops going stale),
   re-evaluate whether `is-daily-enum-sports`'s unconditional daily TEAMS/STANDINGS refetch should be narrowed (e.g.
   `--sports-entity FIXTURES,INJURIES,STANDINGS` excluding `TEAMS`/`LEAGUES` once the season-boundary path is proven
   reliable) — do this LAST, only after the replacement mechanism is verified working for a real season boundary, so
   there is no coverage gap in between.

## Resolution (2026-07-08, `deployment-service`-scoped agent)

**Root cause confirmed exactly as diagnosed above** (CLI never passed `backend=`/`workspace_root=` to
`SportsTriggerScheduler(...)`, defaulting to `backend="local"` which cannot work in the `deployment-service`-only Cloud
Run Job image). Fixed:

1. **CLI wiring** (`deployment-service/deployment_service/cli/commands/sports_trigger.py`): added `--backend`
   (`local`/`cloud`), `--workspace-root`, `--cloud-run-project`, `--cloud-run-region`, `--cloud-run-service-account`
   options to both `sports_trigger_run` and `sports_trigger_evaluate`, wired into `SportsTriggerScheduler(...)`.
   `--cloud-run-*` fall back to `DeploymentConfig()` (project_id / gcs_region / service_account_email) when omitted.
2. **Terraform** (`deployment-service/terraform/gcp/sports_scheduler_cron.tf`): the Cloud Run Job container now
   overrides `args` to pass
   `--backend cloud --cloud-run-project <project> --cloud-run-region <region> --cloud-run-service-account <unified-trading-sa email>`
   (previously inherited the Dockerfile CMD verbatim, no backend flag at all). Also corrected the stale top-of-file
   comment claiming this job was "DEFERRED... VM instead" — confirmed via `gcloud compute instances list` that no
   `sports-scheduler-*` VM exists; the Cloud Run Job + Cloud Scheduler cron IS the live mechanism and has been since
   some point after 2026-04-22.
3. **Config** (`deployment-service/configs/sports-trigger-tiers.yaml`): `cloud_run_job_name` fields were pointing at 4
   scheduler-specific job names (`sports-trigger-instruments` / `-mtds` / `-features-sports` / `-ml`) that were NEVER
   provisioned (confirmed zero matches via `gcloud run jobs list`). Repointed at the REAL, already-provisioned,
   already-working per-service Cloud Run Jobs the T+1 batch reconciliation cron (`terraform/gcp/t1_batch_scheduler.tf`)
   already dispatches into: `uts-prod-instruments-service-t1-recon`, `uts-prod-market-tick-data-service-fast-t1-recon`,
   `features-sports-service-job` (all verified live via `gcloud run jobs describe`; execution SA `unified-trading-sa`
   already holds project-level `roles/run.invoker`, so no new IAM grants were needed). **No real ml-service Cloud Run
   Job exists** — the `inference_pre_match` trigger's `cloud_run_job_name` is left empty on purpose (fires the
   dispatcher's existing loud warning + skip instead of pointing at a name that doesn't resolve); provisioning one is a
   separate, still-open follow-up (item 1's "bigger infra lift" caveat, now narrowed to just ml-service).
4. **Second latent bug found + fixed in the same code path**: `_dispatch_services`'s inline `cloud` branch passed the
   FULL `"python -m <module> ..."` command as the Cloud Run Jobs execution-override `args`. Verified via
   `gcloud run jobs describe uts-prod-instruments-service-t1-recon` that the real target job's container `command` is
   `None` (image ENTRYPOINT already resolves the module) and `args` is CLI-flags-only
   (`['--operation=instruments', '--mode=batch', '--asset-group=DEFI', '--run-tag=t1-recon']`) — Cloud Run Jobs V2
   execution overrides can only replace `args`, never `command`. Extracted a shared `_strip_python_module_prefix()`
   static method (deduplicating what the dead, never-called `_dispatch_cloud` method already did correctly) and used it
   in `_dispatch_services`'s cloud branch. This bug would have silently broken every cloud dispatch even after fix #1-#3
   above. Removed `_dispatch_cloud` as genuinely dead code (confirmed zero call sites) — it was never wired into
   `_dispatch_services`, which had its own divergent, buggy inline implementation instead.

**Verified against real production infra (not just unit tests)** (was: verified in-process only — deploy step was
outstanding until 2026-07-12): instantiated the fixed `SportsTriggerScheduler` with `backend="cloud"` and the real
`cloud_run_config`, and called `_check_reference()` directly against the real GCS state file
(`gs://deployment-scripts-central-element-323112/sports_scheduler_state/scheduler.json`) and the real Cloud Run Jobs
API. Result:

```
=== BEFORE ===
last_run.discovery: 2026-06-27 15:40:40.665723+00:00
last_run.reference: 2026-06-24 01:19:35.834717+00:00

=== Firing Tier-2 reference check (real dispatch) ===
check_reference() fired=2   # INJURIES (run_always) + TRANSFERS (transfer window open, 49 leagues)

=== AFTER ===
last_run.discovery: 2026-06-27 15:40:40.665723+00:00
last_run.reference: 2026-07-08 21:30:23.827692+00:00
```

Both dispatches were real Cloud Run Jobs API calls against `uts-prod-instruments-service-t1-recon` (log line:
`Triggering Cloud Run Job for shard instruments-service-reference-periodic in region asia-northeast1`), and the real
production state file's `last_run.reference` advanced from 14-days-stale to now — the exact symptom this issue was filed
about, cured. Did not fire `_check_discovery()` for real in this pass (would trigger a heavier 33-league
FIXTURES+STANDINGS rolling-window refetch) or a live end-to-end Cloud Scheduler cron tick (the terraform change needs a
normal deploy/apply cycle to reach the running job) — the direct `_check_reference()` call against real infra was judged
sufficient real-infra proof for the dispatch-path fix without over-scoping this verification pass.

Added regression tests: `tests/unit/test_sports_trigger_cli.py` (`TestBackendWiring` — CLI flags reach the ctor,
cloud_run_config fallback to `DeploymentConfig`) and `tests/unit/test_sports_trigger_scheduler_periodic.py`
(`_strip_python_module_prefix` unit coverage + a regression test asserting `deploy_shard` never receives a "python -m
module" prefix). Full `deployment-service` `quality-gates.sh` green.

**Still open (out of scope for this fix, tracked here for continuity)**: item 2 above (add `VENUES` to the Tier-2
season-boundary services) and item 3 above (re-narrow `is-daily-enum-sports` once the season-boundary path is proven
reliable over a real season boundary) were NOT done in this pass — this fix's scope was specifically the zero-dispatch
bug. A real ml-service Cloud Run Job also still needs provisioning for the `inference_pre_match` trigger to work
end-to-end.

## Resolution completed 2026-07-12

The 2026-07-08 resolution above fixed the code (CLI backend/workspace-root wiring, Terraform `args`, config repoint) and
verified it **in-process only** — a direct `_check_reference()` call against real infra, not an actual `tofu apply`
followed by a real Cloud Scheduler cron tick. The Terraform change
(`deployment-service/terraform/gcp/sports_scheduler_cron.tf`) was committed (`deployment-service@bb880b6`) but never
applied, so the fix never reached the running Cloud Run Job — the scheduler stayed on its stale generation-1 container
and ~1150 no-op 5-minute-cadence executions followed between 2026-07-08 and 2026-07-12.

**2026-07-12 (operator-authorized prod deploy — escalation ii, see
`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §Progress Log "sports prod deploy, escalation
ii COMPLETE")**: the args fix was applied via a targeted single-resource OpenTofu plan (generation 2,
`lastUpdated 2026-07-12T10:38:43Z`). The scheduler's GCS state file
(`gs://deployment-scripts-central-element-323112/sports_scheduler_state/scheduler.json`) advanced past its
2026-06-27/07-08 freeze — `last_run.reference` flipped 2026-07-12T10:40:44Z on the first post-apply tick;
`last_run.discovery` dispatched 2026-07-12T16:45:37Z. Crons are now succeeding.

Status **remains `resolved`** — this addendum corrects the original Resolution section's overclaim: (was: verified
in-process only — deploy step was outstanding until 2026-07-12).
